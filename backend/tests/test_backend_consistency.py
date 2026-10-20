"""The same tenant/graph/scientific scenarios execute against both real ORM adapters."""
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace
import pytest

sys.path.insert(0, str(Path(__file__).parents[2] / 'backend_fastapi'))
os.environ['ENVIRONMENT'] = 'test'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'


@pytest.fixture(params=['django', 'fastapi'])
def case(request, db):
    if request.param == 'django':
        from apps.organizations.models import Organization, Service
        from apps.processes.models import Asset, BusinessProcess, Dependency
        from apps.bia.models import BIAAssessment, BIAImpact
        from apps.plans.models import ContinuityPlan
        from apps.risks.models import Risk
        from apps.simulation.models import Scenario
        from apps.simulation.simulator import ScenarioSimulator
        from apps.engine.calculator import PriorityEngine
        session = None
    else:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session
        from app.models import Base
        from app.models.organization import Organization, Service
        from app.models.process import Asset, BusinessProcess, Dependency
        from app.models.bia import BIAAssessment, BIAImpact
        from app.models.plan import ContinuityPlan
        from app.models.risk import Risk
        from app.models.simulation import Scenario
        from app.services.simulation import run_cascade_simulation
        from app.services.engine import compute_priority_scores
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        session = Session(engine)
    def create(cls, **values):
        if session is None:
            return cls.objects.create(**values)
        row = cls(**values); session.add(row); session.flush(); return row
    org = create(Organization, name='Reference tenant', sector='Test', max_acceptable_loss=1000)
    foreign = create(Organization, name='Foreign tenant', sector='Test')
    service = create(Service, organization_id=org.id, name='Reference service')
    procs = [create(BusinessProcess, organization_id=org.id, service_id=service.id, name=f'P{i}', criticality='HIGH') for i in range(4)]
    asset = create(Asset, organization_id=org.id, name='Server', type='SERVER')
    isolated = create(Asset, organization_id=org.id, name='Isolated', type='SERVER')
    foreign_asset = create(Asset, organization_id=foreign.id, name='Foreign secret asset', type='SERVER')
    def dep(source, target, *, source_type='PROCESS', target_type='ASSET', tenant=org, deleted=False):
        return create(Dependency, organization_id=tenant.id, from_type=source_type, from_id=source.id, to_type=target_type, to_id=target.id, is_deleted=deleted)
    def simulate(ids):
        scenario = create(Scenario, organization_id=org.id, title='Failure', disrupted_asset_ids=ids, estimated_outage_hours=8)
        return ScenarioSimulator.simulate(scenario) if session is None else run_cascade_simulation(session, scenario, org.id).model_dump()
    def priority():
        if session is None:
            return PriorityEngine.calculate_priority(procs[0])
        return next(p.model_dump() for p in compute_priority_scores(session, org.id).ranked_processes if p.process_id == procs[0].id)
    def delete(row):
        row.is_deleted = True
        if session is None: row.save()
        else: session.flush()
    yield SimpleNamespace(**locals())
    if session is not None:
        session.close(); engine.dispose()


def ids(result):
    return [p['process_id'] for p in result['affected_processes']]


def test_sim01_direct_three_and_sim03_unrelated(case):
    for proc in case.procs[:3]: case.dep(proc, case.asset)
    result = case.simulate([case.asset.id])
    assert ids(result) == sorted(p.id for p in case.procs[:3])
    assert result['affected_processes_count'] == 3
    assert case.procs[3].id not in ids(result)


def test_sim02_isolated_and_sim07_empty_graph(case):
    empty = case.simulate([case.isolated.id])
    assert ids(empty) == []
    assert any('EMPTY_DEPENDENCY_GRAPH' in w for w in empty['warnings'])
    case.dep(case.procs[0], case.asset)
    isolated = case.simulate([case.isolated.id])
    assert ids(isolated) == []
    assert any('NO_REGISTERED_DEPENDENTS' in w for w in isolated['warnings'])
    assert isolated['simulation_status'] == 'NO_CONFIRMED_IMPACT'


def test_sim04_transitive_sim05_cycles_sim09_duplicate_sim10_deterministic(case):
    p1, p2, p3, _ = case.procs
    case.dep(p1, case.asset)
    case.dep(p2, p1, target_type='PROCESS')
    case.dep(p3, p2, target_type='PROCESS')
    case.dep(p1, p3, target_type='PROCESS')
    case.dep(p2, case.asset)
    case.dep(p1, case.asset)
    first = case.simulate([case.asset.id, case.asset.id])
    second = case.simulate([case.asset.id])
    assert ids(first) == ids(second) == sorted([p1.id, p2.id, p3.id])
    assert len(ids(first)) == len(set(ids(first)))


@pytest.mark.parametrize('invalid', ['foreign', 'unknown', 'negative', 'string'])
def test_sim06_invalid_assets_rejected_generically(case, invalid):
    from rest_framework.exceptions import ValidationError
    from fastapi import HTTPException
    value = {'foreign': case.foreign_asset.id, 'unknown': 987654, 'negative': -1, 'string': str(case.asset.id)}[invalid]
    with pytest.raises((ValidationError, HTTPException)) as error:
        case.simulate([value])
    assert 'Foreign secret' not in str(error.value)


def test_sim08_deleted_foreign_or_dangling_nodes_do_not_bridge_graph(case):
    p1, p2, p3, _ = case.procs
    case.dep(p1, case.asset)
    case.dep(p2, p1, target_type='PROCESS')
    case.delete(p1)
    case.dep(p3, case.asset, deleted=True)
    # Invalid cross-tenant intermediate node may never bridge active local nodes.
    case.dep(p3, case.foreign_asset)
    case.dep(case.foreign_asset, case.asset, source_type='ASSET')
    result = case.simulate([case.asset.id])
    assert ids(result) == []
    assert any('UNAVAILABLE_DEPENDENCY_ENDPOINTS' in w for w in result['warnings'])


def test_bia_and_plan_lookups_ignore_other_tenants(case):
    p = case.procs[0]; case.dep(p, case.asset)
    case.create(case.BIAAssessment, organization_id=case.org.id, process_id=p.id, revision=1, rto_hours=4, mtpd_hours=12)
    case.create(case.BIAAssessment, organization_id=case.foreign.id, process_id=p.id, revision=99, rto_hours=100, mtpd_hours=100)
    case.create(case.ContinuityPlan, organization_id=case.foreign.id, process_id=p.id, title='Foreign plan', status='PUBLISHED')
    result = case.simulate([case.asset.id])['affected_processes'][0]
    assert result['target_rto_hours'] == 4
    assert result['rto_breached']
    assert not result['has_published_plan']


def test_alg01_real_adapters_match_identical_reference_fixture(case):
    ref = json.loads((Path(__file__).parents[2] / 'tests/scientific_reference.json').read_text())
    p = case.procs[0]
    for dependent in case.procs[1:]: case.dep(dependent, p, target_type='PROCESS')
    case.create(case.BIAAssessment, organization_id=case.org.id, process_id=p.id, revision=1, rto_hours=1, mtpd_hours=12)
    bia = case.create(case.BIAAssessment, organization_id=case.org.id, process_id=p.id, revision=2, **ref['bia'])
    for impact in ref['impacts']: case.create(case.BIAImpact, bia_id=bia.id, **impact)
    case.create(case.Risk, organization_id=case.org.id, process_id=p.id, likelihood=4, impact=5, threat='Reference risk')
    # These corrupt cross-tenant rows must have no effect on calculations.
    case.create(case.Risk, organization_id=case.foreign.id, process_id=p.id, likelihood=5, impact=5, threat='Foreign risk')
    first = case.priority()
    assert first['operands'] == ref['expected_operands']
    assert first['priority_score'] == ref['expected_score']
    assert first == case.priority()
