"""Shared scientific specification, strategy and independent statistical reference tests."""
import json
from pathlib import Path
import math
import pytest
from bcms_domain import scientific as m
from apps.engine.sensitivity import kendall_tau, kendall_tau_b, sweep_weights, ablate_operands

REFERENCE = json.loads((Path(__file__).parents[2] / 'tests/scientific_reference.json').read_text())


def test_reference_equation_and_bounds():
    inputs = {k: v for k, v in REFERENCE.items() if not k.startswith('expected')}
    result = m.priority(**inputs)
    assert result['operands'] == REFERENCE['expected_operands']
    assert result['priority_score'] == REFERENCE['expected_score']
    assert result == m.priority(**inputs)
    assert all(0 <= v <= 1 for v in result['operands'].values())
    assert sum(m.WEIGHTS.values()) == 1
    assert m.risk_score(4, 5) == 20
    assert result['parameters']['has_rpo_gap']


@pytest.mark.parametrize('likelihood,impact', [(0, 5), (6, 1), (-1, 4), (1.1, 3), (True, 3), ('NaN', 4)])
def test_risk_range_validation(likelihood, impact):
    with pytest.raises(ValueError): m.risk_score(likelihood, impact)


def test_recovery_targets_and_missing_data():
    assert m.recovery_constraints(4, 12, 60, 360)
    with pytest.raises(ValueError): m.recovery_constraints(18, 12, 60, 360)
    r = m.priority(criticality='HIGH', bia=None, impacts=[], max_loss=1000, risks=[], dependency_norm=0)
    assert r['operands']['impact_norm'] == 0.5
    assert len(r['warnings']) == 2
    assert r['parameters']['rto_hours'] == 24


def candidate(name='a', cost=10, rto=2, rpo=30):
    return dict(name=name, cost=cost, estimated_rto_hours=rto, estimated_rpo_minutes=rpo)


def test_strategy_cost_constraints_ties_and_order():
    rows = [candidate('b', 20), candidate('a', 10), candidate('rto', 1, 8), candidate('rpo', 1, 2, 90)]
    r = m.evaluate_strategies(4, 60, rows)
    assert r['recommended_strategy']['name'] == 'a'
    assert len(r['feasible_candidates']) == 2
    assert {tuple(x['reasons']) for x in r['rejected_candidates']} == {('RTO_EXCEEDED',), ('RPO_EXCEEDED',)}
    assert m.evaluate_strategies(4, 60, list(reversed(rows))) == r
    assert m.evaluate_strategies(1, 10, rows)['status'] == 'NO_FEASIBLE_OPTION'
    assert m.evaluate_strategies(4, 60, [candidate('b'), candidate('a')])['recommended_strategy']['name'] == 'a'


@pytest.mark.parametrize('field,value', [('cost', None), ('cost', -1), ('cost', 'NaN'), ('cost', 'Infinity'), ('estimated_rto_hours', -1), ('estimated_rpo_minutes', -1)])
def test_invalid_candidates_fail_validation(field, value):
    row = candidate(); row[field] = value
    with pytest.raises(ValueError): m.evaluate_strategies(4, 60, [row])


@pytest.mark.parametrize('x,y', [([1, 1, 2, 3], [1, 2, 2, 3]), ([1, 2, 3], [3, 2, 1]), ([1, 1, 2, 2], [2, 2, 1, 3])])
def test_tau_b_independent_scipy_reference(x, y):
    from scipy.stats import kendalltau
    assert kendall_tau_b(x, y) == pytest.approx(kendalltau(x, y).statistic)


def test_tau_b_undefined_and_rank_compatibility():
    assert kendall_tau_b([1, 1], [2, 2]) is None
    assert kendall_tau_b([1], [2]) is None
    assert kendall_tau([1, 2, 3], [1, 2, 3]) == 1
    assert kendall_tau([1, 2, 3], [3, 2, 1]) == -1
    with pytest.raises(ValueError): kendall_tau([1, 1], [1, 1])
    with pytest.raises(ValueError): kendall_tau_b([1, math.nan], [1, 2])


def test_sensitivity_normalization_ablation_and_ties():
    data = [dict(id=i, operands=dict(impact_norm=0.5, urgency_norm=0.5, risk_norm=0.5, dependency_norm=0.5)) for i in [3, 1, 2]]
    results = sweep_weights(data, m.WEIGHTS)
    assert results['base_rank'] == [1, 2, 3]
    assert results == sweep_weights(data, m.WEIGHTS)
    for value in results['per_weight'].values():
        for variant in value['variants']:
            assert sum(variant['weights'].values()) == pytest.approx(1, abs=1e-12)
            assert variant['tau_b_scores'] is None
    for key, value in ablate_operands(data, m.WEIGHTS)['per_operand'].items():
        assert value['weights'][key.removesuffix('_norm')] == 0
        assert sum(w == 0 for w in value['weights'].values()) == 1
        assert sum(value['weights'].values()) == pytest.approx(1, abs=1e-12)


def test_decimal_cost_comparison_does_not_round_before_selection():
    rows = [candidate('a', '9999999999999999.99'), candidate('z', '9999999999999999.98')]
    result = m.evaluate_strategies(4, 60, rows)
    assert result['recommended_strategy']['name'] == 'z'
    assert result['recommended_strategy']['estimated_cost_exact'] == '9999999999999999.98'
