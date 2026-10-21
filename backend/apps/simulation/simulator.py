from typing import Any

import networkx as nx

from apps.engine.calculator import DependencyAnalyzer
from apps.engine.scheduler import compare_schedules, make_snapshot
from apps.processes.models import BusinessProcess, Dependency
from apps.simulation.models import Scenario


class ScenarioSimulator:
    """
    FR-10: Ssenariy simulyatsiyasi va zanjirsimon ta'sir tahlili (T-06).
    Aktivlar ishdan chiqqanda ularga bog'liq barcha jarayonlarni aniqlaydi va
    RTO/MTPD buzilishlarini bashorat qiladi.
    """

    @classmethod
    def simulate(cls, scenario: Scenario) -> dict[str, Any]:
        org = scenario.organization
        g = DependencyAnalyzer.build_graph(org)

        disrupted_asset_ids = scenario.disrupted_asset_ids or []
        affected_processes_ids = set()

        # Har bir nosoz aktiv uchun unga qaram bo'lgan tugunlarni topish
        for asset_id in disrupted_asset_ids:
            asset_node = f"ASSET:{asset_id}"
            if asset_node in g:
                # In-edges or ancestors: kim ushbu aktivga bog'langan
                dependents = nx.ancestors(g, asset_node)
                for dep in dependents:
                    if dep.startswith("PROCESS:"):
                        proc_id = int(dep.split(":")[1])
                        affected_processes_ids.add(proc_id)

            # Shuningdek, to'g'ridan-to'g'ri bog'liqliklar
            direct_deps = Dependency.objects.filter(
                organization=org,
                to_type="ASSET",
                to_id=asset_id,
                dependency_criticality="MANDATORY",
                is_deleted=False,
                from_type="PROCESS",
            )
            for d in direct_deps:
                affected_processes_ids.add(d.from_id)

        affected_processes_data = []
        rto_breaches = 0
        mtpd_breaches = 0
        missing_plans = 0

        outage_hours = float(scenario.estimated_outage_hours)

        for pid in sorted(affected_processes_ids):
            try:
                proc = BusinessProcess.objects.get(id=pid, organization=org, is_deleted=False)
            except BusinessProcess.DoesNotExist:
                continue

            latest_bia = (
                proc.bia_assessments.filter(is_deleted=False).order_by("-revision", "-id").first()
            )
            rto_h = float(latest_bia.rto_hours) if latest_bia else None
            mtpd_h = float(latest_bia.mtpd_hours) if latest_bia else None

            rto_breached = outage_hours > rto_h if rto_h is not None else None
            mtpd_breached = outage_hours > mtpd_h if mtpd_h is not None else None

            if rto_breached:
                rto_breaches += 1
            if mtpd_breached:
                mtpd_breaches += 1

            has_published_plan = proc.continuity_plans.filter(
                status="PUBLISHED", is_deleted=False
            ).exists()
            if not has_published_plan:
                missing_plans += 1

            affected_processes_data.append(
                {
                    "process_id": proc.id,
                    "process_name": proc.name,
                    "service_name": proc.service.name,
                    "criticality": proc.criticality,
                    "target_rto_hours": rto_h,
                    "target_mtpd_hours": mtpd_h,
                    "rto_breached": rto_breached,
                    "mtpd_breached": mtpd_breached,
                    "has_published_plan": has_published_plan,
                }
            )

        snapshot = make_snapshot(org, org.recovery_budget, 1)
        snapshot["tasks"] = [
            task for task in snapshot["tasks"] if task["id"] in affected_processes_ids
        ]
        affected_nodes = {f"PROCESS:{pid}" for pid in affected_processes_ids}
        snapshot["dependencies"] = [
            dep
            for dep in snapshot["dependencies"]
            if f"{dep['from_type']}:{dep['from_id']}" in affected_nodes
            and f"{dep['to_type']}:{dep['to_id']}" in affected_nodes
        ]
        if scenario.recovery_options:
            for task in snapshot["tasks"]:
                task["options"] = [
                    option
                    for option in task["options"]
                    if option["id"] in scenario.recovery_options
                ]
        for resource_id, capacity in scenario.available_resources.items():
            if str(resource_id) in snapshot["resources"]:
                snapshot["resources"][str(resource_id)]["capacity"] = capacity
        snapshot["scenario"] = {
            "id": scenario.pk,
            "title": scenario.title,
            "is_synthetic": scenario.is_synthetic,
            "disrupted_asset_ids": scenario.disrupted_asset_ids,
            "estimated_outage_hours": str(scenario.estimated_outage_hours),
            "event_time": scenario.event_time.isoformat() if scenario.event_time else None,
        }
        return {
            "input_snapshot": snapshot,
            "recovery_comparison": compare_schedules(snapshot),
            "simulation_notice": "Sun’iy hisoblash; real infratuzilmaga hech qanday buyruq yuborilmaydi. Bir vaqtda bitta umumiy mutaxassis taxmini.",
            "scenario_id": scenario.id,
            "scenario_title": scenario.title,
            "estimated_outage_hours": outage_hours,
            "disrupted_assets_count": len(disrupted_asset_ids),
            "affected_processes_count": len(affected_processes_data),
            "rto_breaches_count": rto_breaches,
            "mtpd_breaches_count": mtpd_breaches,
            "missing_plans_count": missing_plans,
            "affected_processes": affected_processes_data,
        }
