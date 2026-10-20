from typing import Dict, Any
from apps.simulation.models import Scenario
from apps.processes.models import BusinessProcess
from apps.engine.calculator import DependencyAnalyzer


class ScenarioSimulator:
    """
    FR-10: Ssenariy simulyatsiyasi va zanjirsimon ta'sir tahlili (T-06).
    Aktivlar ishdan chiqqanda ularga bog'liq barcha jarayonlarni aniqlaydi va
    RTO/MTPD buzilishlarini bashorat qiladi.
    """
    @classmethod
    def simulate(cls, scenario: Scenario) -> Dict[str, Any]:
        org = scenario.organization
        g = DependencyAnalyzer.build_graph(org)
        
        from bcms_domain.graph import cascade
        from bcms_domain.scientific import number
        from rest_framework.exceptions import ValidationError
        disrupted_asset_ids = scenario.disrupted_asset_ids if scenario.disrupted_asset_ids is not None else []
        try:
            outage_hours = float(number(scenario.estimated_outage_hours, 'estimated_outage_hours'))
            affected_processes_ids, warnings = cascade(g, disrupted_asset_ids)
        except ValueError as exc:
            raise ValidationError({'simulation': str(exc)}) from None

        affected_processes_data = []
        rto_breaches = 0
        mtpd_breaches = 0
        missing_plans = 0


        for pid in affected_processes_ids:
            try:
                proc = BusinessProcess.objects.get(id=pid, organization=org, is_deleted=False)
            except BusinessProcess.DoesNotExist:
                continue

            latest_bia = proc.bia_assessments.filter(organization=org, is_deleted=False).order_by('-revision', '-id').first()
            if not latest_bia:
                warnings.append(f'MISSING_BIA: process {pid}; breach targets use legacy 24h/48h priors')
            rto_h = float(latest_bia.rto_hours) if latest_bia else 24.0
            mtpd_h = float(latest_bia.mtpd_hours) if latest_bia else 48.0

            rto_breached = outage_hours > rto_h
            mtpd_breached = outage_hours > mtpd_h

            if rto_breached:
                rto_breaches += 1
            if mtpd_breached:
                mtpd_breaches += 1

            has_published_plan = proc.continuity_plans.filter(organization=org, is_deleted=False, status='PUBLISHED').exists()
            if not has_published_plan:
                missing_plans += 1

            affected_processes_data.append({
                'process_id': proc.id,
                'process_name': proc.name,
                'service_name': proc.service.name if proc.service.organization_id == org.id else '',
                'criticality': proc.criticality,
                'target_rto_hours': rto_h,
                'target_mtpd_hours': mtpd_h,
                'rto_breached': rto_breached,
                'mtpd_breached': mtpd_breached,
                'has_published_plan': has_published_plan
            })

        return {
            'warnings': sorted(set(warnings)),
            'data_quality_status': 'INCOMPLETE' if warnings else 'REGISTERED_GRAPH_ONLY',
            'simulation_status': 'CONFIRMED_IMPACT' if affected_processes_data else 'NO_CONFIRMED_IMPACT',
            'scenario_id': scenario.id,
            'scenario_title': scenario.title,
            'estimated_outage_hours': outage_hours,
            'disrupted_assets_count': len(disrupted_asset_ids),
            'affected_processes_count': len(affected_processes_data),
            'rto_breaches_count': rto_breaches,
            'mtpd_breaches_count': mtpd_breaches,
            'missing_plans_count': missing_plans,
            'affected_processes': affected_processes_data
        }
