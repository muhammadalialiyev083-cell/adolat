import pytest
from bcms_domain.scientific import evaluate_strategies


@pytest.mark.parametrize('field,value', [('likelihood',0),('impact',6),('rto_hours',-1),('rpo_minutes',-1)])
def test_risk_payload_validation(auth_client, field, value):
    payload = dict(process_id=1, likelihood=4, impact=5, rto_hours=4, rpo_minutes=60, backup_interval_minutes=360)
    payload[field] = value
    assert auth_client.post('/api/v1/analyses/evaluate-risk', json=payload).status_code == 422


def test_strategy_shared_contract_and_missing_cost(auth_client):
    strategies = [dict(name='b', cost=20, estimated_rto_hours=2, estimated_rpo_minutes=30), dict(name='a', cost=10, estimated_rto_hours=2, estimated_rpo_minutes=30)]
    payload = dict(target_rto_hours=4, target_rpo_minutes=60, strategies=strategies)
    response = auth_client.post('/api/v1/analyses/evaluate-strategy', json=payload)
    assert response.status_code == 200
    assert response.json() == evaluate_strategies(4, 60, strategies)
    del strategies[0]['cost']
    assert auth_client.post('/api/v1/analyses/evaluate-strategy', json=payload).status_code == 422


def test_simulation_api_rejects_foreign_and_deleted_scenarios(auth_client):
    from conftest import TestingSessionLocal
    from app.models.simulation import Scenario
    db = TestingSessionLocal()
    scenario = Scenario(organization_id=1, title='Invalid asset', disrupted_asset_ids=[987654], estimated_outage_hours=1)
    db.add(scenario); db.commit(); pk=scenario.id
    try:
        response = auth_client.post(f'/api/v1/scenarios/{pk}/simulate/')
        assert response.status_code == 400
        scenario.is_deleted = True; db.commit()
        assert auth_client.post(f'/api/v1/scenarios/{pk}/simulate/').status_code == 404
    finally:
        db.delete(scenario); db.commit(); db.close()


def test_stored_strategy_contract_scoped_and_feasible(auth_client):
    from conftest import TestingSessionLocal
    from app.models.plan import Strategy
    db = TestingSessionLocal()
    rows = [Strategy(organization_id=1, process_id=1, name='Stored cheapest', estimated_cost=10, estimated_rto_hours=2, estimated_rpo_minutes=30),
            Strategy(organization_id=1, process_id=1, name='Stored infeasible', estimated_cost=1, estimated_rto_hours=8, estimated_rpo_minutes=30)]
    db.add_all(rows); db.commit()
    try:
        response = auth_client.post('/api/v1/analyses/evaluate-strategy', json=dict(process_id=1, target_rto_hours=4, target_rpo_minutes=60))
        assert response.status_code == 200
        data = response.json()
        assert len(data['strategies']) == 2
        assert data['recommended_strategy']['name'] == 'Stored cheapest'
        assert data['rejected_candidates'][0]['reasons'] == ['RTO_EXCEEDED']
        rows[0].estimated_cost=0; db.commit()
        assert auth_client.post('/api/v1/analyses/evaluate-strategy', json=dict(process_id=1)).status_code == 422
    finally:
        for row in rows: db.delete(row)
        db.commit(); db.close()
