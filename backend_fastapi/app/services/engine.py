"""SQLAlchemy adapters for the canonical BCMS research calculation model."""
from fastapi import HTTPException
from bcms_domain import scientific as model
from bcms_domain.graph import dependency_norm
from app.models.process import BusinessProcess
from app.models.bia import BIAAssessment
from app.models.risk import Risk
from app.models.plan import Strategy
from app.models.organization import Organization
from app.services.graph import tenant_graph
from app.schemas.engine import EvaluateRiskResponse, PriorityResponse, RankedProcess


def evaluate_risk_algorithm(data):
    score = model.risk_score(data.likelihood, data.impact)
    gap = data.backup_interval_minutes > data.rpo_minutes
    return EvaluateRiskResponse(risk_score=score, risk_class=model.classify_risk(score), rpo_gap=gap,
                                observations=['Zaxiralash intervali RPO talabidan katta'] if gap else [])


def compute_priority_scores(db, organization_id):
    procs = db.query(BusinessProcess).filter(BusinessProcess.organization_id == organization_id, BusinessProcess.is_deleted == False).all()
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    graph = tenant_graph(db, organization_id)
    ranked = []
    for proc in procs:
        bia = db.query(BIAAssessment).filter(BIAAssessment.organization_id == organization_id, BIAAssessment.process_id == proc.id, BIAAssessment.is_deleted == False).order_by(BIAAssessment.revision.desc(), BIAAssessment.id.desc()).first()
        risks = db.query(Risk).filter(Risk.organization_id == organization_id, Risk.process_id == proc.id, Risk.is_deleted == False).all()
        fields = ('rto_hours', 'mtpd_hours', 'rpo_minutes', 'backup_interval_minutes')
        result = model.priority(criticality=proc.criticality, bia={k: getattr(bia, k) for k in fields} if bia else None,
            impacts=[{k: getattr(i, k) for k in ('horizon_hours', 'financial_loss', 'operational_score', 'legal_score', 'reputational_score')} for i in bia.impacts] if bia else [],
            max_loss=org.max_acceptable_loss, risks=[(r.likelihood, r.impact) for r in risks],
            dependency_norm=dependency_norm(graph, proc.id, len(procs)))
        result['warnings'].extend(graph.graph['warnings'])
        ranked.append(RankedProcess(process_id=proc.id, process_name=proc.name, **result))
    ranked.sort(key=lambda p: (-p.priority_score, p.process_id))
    return PriorityResponse(ranked_processes=ranked)


def evaluate_strategy_algorithm(db, data, organization_id):
    # New supplied-candidate contract also works without a stored process, like Django.
    if data.strategies is not None:
        if data.target_rto_hours is None or data.target_rpo_minutes is None:
            raise ValueError('Supplied candidates require target_rto_hours and target_rpo_minutes')
        return model.evaluate_strategies(data.target_rto_hours, data.target_rpo_minutes, data.strategies)
    proc = db.query(BusinessProcess).filter(BusinessProcess.id == data.process_id, BusinessProcess.organization_id == organization_id, BusinessProcess.is_deleted == False).first()
    if not proc:
        raise HTTPException(status_code=404, detail='Jarayon topilmadi.')
    rows = db.query(Strategy).filter(Strategy.process_id == proc.id, Strategy.organization_id == organization_id, Strategy.is_deleted == False)
    if data.strategy_id is not None:
        rows = rows.filter(Strategy.id == data.strategy_id)
    result = [dict(strategy_id=s.id, name=s.name, estimated_rto_hours=float(s.estimated_rto_hours), estimated_rpo_minutes=s.estimated_rpo_minutes, cost=str(s.estimated_cost), estimated_cost=float(s.estimated_cost), is_selected=s.is_selected) for s in rows]
    if any(model.number(row['cost'], 'cost') == 0 for row in result):
        raise ValueError('Stored zero costs require explicit confirmation through supplied candidates')
    bia = db.query(BIAAssessment).filter(BIAAssessment.process_id == proc.id, BIAAssessment.organization_id == organization_id, BIAAssessment.is_deleted == False).order_by(BIAAssessment.revision.desc(), BIAAssessment.id.desc()).first()
    rto = data.target_rto_hours if data.target_rto_hours is not None else bia.rto_hours if bia else None
    rpo = data.target_rpo_minutes if data.target_rpo_minutes is not None else bia.rpo_minutes if bia else None
    if rto is None or rpo is None:
        raise ValueError('A current BIA or explicit recovery targets is required')
    return dict(process_id=proc.id, strategies=result, **model.evaluate_strategies(rto, rpo, result))
