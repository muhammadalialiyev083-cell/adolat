"""FR-10: Cascade disruption simulation using dependency graph."""

from sqlalchemy.orm import Session

from app.models.process import BusinessProcess
from app.models.bia import BIAAssessment
from app.models.plan import ContinuityPlan
from app.models.simulation import Scenario
from app.schemas.simulation import SimulationResult, AffectedProcess


def run_cascade_simulation(
    db: Session, scenario: Scenario, organization_id: int
) -> SimulationResult:
    """Run cascade disruption analysis.
    
    1. Build dependency graph from Dependencies table.
    2. Mark disrupted assets as failed.
    3. Traverse graph to find all affected processes.
    4. Check RTO breaches and missing BCP plans.
    """
    disrupted_ids = scenario.disrupted_asset_ids if scenario.disrupted_asset_ids is not None else []

    from fastapi import HTTPException
    from app.services.graph import tenant_graph
    from bcms_domain.graph import cascade
    from bcms_domain.scientific import number
    if scenario.organization_id != organization_id or scenario.is_deleted:
        raise HTTPException(status_code=404, detail='Ssenariy topilmadi.')
    try:
        outage_hours = float(number(scenario.estimated_outage_hours, 'estimated_outage_hours'))
        affected_process_ids, warnings = cascade(tenant_graph(db, organization_id), disrupted_ids)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None

    # Build affected process details
    affected_processes = []
    rto_breaches = 0
    missing_plans = 0

    for pid in affected_process_ids:
        proc = db.query(BusinessProcess).filter(BusinessProcess.id == pid, BusinessProcess.organization_id == organization_id, BusinessProcess.is_deleted == False).first()
        if not proc:
            continue

        bia = (
            db.query(BIAAssessment)
            .filter(BIAAssessment.process_id == pid, BIAAssessment.organization_id == organization_id, BIAAssessment.is_deleted == False)
            .order_by(BIAAssessment.revision.desc(), BIAAssessment.id.desc())
            .first()
        )
        if not bia:
            warnings.append(f'MISSING_BIA: process {pid}; breach target uses legacy 24h prior')
        target_rto = float(bia.rto_hours) if bia else 24.0
        rto_breached = outage_hours > target_rto
        if rto_breached:
            rto_breaches += 1

        has_plan = (
            db.query(ContinuityPlan)
            .filter(
                ContinuityPlan.process_id == pid,
                ContinuityPlan.organization_id == organization_id,
                ContinuityPlan.status == "PUBLISHED",
                ContinuityPlan.is_deleted == False,
            )
            .first()
        ) is not None
        if not has_plan:
            missing_plans += 1

        affected_processes.append(AffectedProcess(
            process_id=proc.id,
            process_name=proc.name,
            service_name=proc.service.name if proc.service and proc.service.organization_id == organization_id else "",
            target_rto_hours=target_rto,
            rto_breached=rto_breached,
            has_published_plan=has_plan,
        ))

    return SimulationResult(
        warnings=sorted(set(warnings)),
        data_quality_status='INCOMPLETE' if warnings else 'REGISTERED_GRAPH_ONLY',
        simulation_status='CONFIRMED_IMPACT' if affected_processes else 'NO_CONFIRMED_IMPACT',
        scenario_id=scenario.id,
        estimated_outage_hours=outage_hours,
        affected_processes_count=len(affected_processes),
        rto_breaches_count=rto_breaches,
        missing_plans_count=missing_plans,
        affected_processes=affected_processes,
    )
