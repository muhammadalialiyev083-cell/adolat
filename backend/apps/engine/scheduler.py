"""Deterministic list scheduling. Minutes, UZS; heuristic, no optimality claim."""

from copy import deepcopy
from decimal import Decimal
from math import ceil
from time import perf_counter

import networkx as nx

from apps.engine.calculator import PriorityEngine
from apps.engine.models import RecoveryResource
from apps.processes.models import BusinessProcess, Dependency

VERSION = "deterministic-list-v1"


def make_snapshot(organization, budget=None, staff_capacity=1):
    tasks = []
    for process in BusinessProcess.objects.filter(
        organization=organization, is_deleted=False, status="ACTIVE"
    ).order_by("id"):
        bia = process.bia_assessments.filter(is_deleted=False).order_by("-revision", "-id").first()
        priority = PriorityEngine.calculate_priority(process)
        options = []
        for strategy in process.strategies.filter(is_deleted=False).order_by(
            "estimated_cost", "id"
        ):
            options.append(
                {
                    "id": strategy.id,
                    "name": strategy.name,
                    "cost": str(strategy.estimated_cost),
                    "duration": ceil(strategy.recovery_seconds / 60),
                    "preparation": strategy.preparation_minutes,
                    "rpo": strategy.estimated_rpo_minutes,
                    "staff": max(strategy.staff_required, process.required_staff),
                    "resources": strategy.resource_requirements,
                    "conditions": strategy.conditions,
                }
            )
        selected_ids = set(
            process.strategies.filter(is_deleted=False, is_selected=True).values_list(
                "id", flat=True
            )
        )
        if selected_ids:
            options = [option for option in options if option["id"] in selected_ids]
        tasks.append(
            {
                "id": process.pk,
                "name": process.name,
                "criticality": process.criticality,
                "priority": priority["priority_score"],
                "target": bia.rto_seconds // 60 if bia else None,
                "rpo": bia.rpo_minutes if bia and process.data_recovery_applicable else None,
                "data_recovery_applicable": process.data_recovery_applicable,
                "options": options,
            }
        )
    resources = {
        str(r.pk): {
            "name": r.name,
            "capacity": r.capacity,
            "available": max(r.available_from_minutes, r.unavailable_until_minutes),
        }
        for r in RecoveryResource.objects.filter(organization=organization, is_deleted=False)
    }
    resources["staff"] = {"name": "Mutaxassislar", "capacity": staff_capacity, "available": 0}
    deps = list(
        Dependency.objects.filter(
            organization=organization, is_deleted=False, dependency_criticality="MANDATORY"
        ).values("from_type", "from_id", "to_type", "to_id")
    )
    return {
        "tasks": tasks,
        "resources": resources,
        "dependencies": deps,
        "budget": str(budget) if budget is not None else None,
        "units": {"time": "minute", "cost": "UZS"},
        "algorithm_version": VERSION,
    }


def compare_schedules(snapshot):
    return {method: schedule(deepcopy(snapshot), method) for method in ["baseline", "constrained"]}


def schedule(snapshot, method):
    started = perf_counter()
    graph = nx.DiGraph()
    for dep in snapshot["dependencies"]:
        graph.add_edge(f"{dep['from_type']}:{dep['from_id']}", f"{dep['to_type']}:{dep['to_id']}")
    cycles = [
        sorted(c)
        for c in nx.strongly_connected_components(graph)
        if len(c) > 1 or any(graph.has_edge(n, n) for n in c)
    ]
    tasks = snapshot["tasks"]
    rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    tasks.sort(
        key=lambda t: (
            rank[t["criticality"]],
            -(t["priority"] if t["priority"] is not None else -1),
            t["id"],
        )
    )
    by_id = {t["id"]: t for t in tasks}
    prerequisites = {
        t["id"]: {
            int(n.split(":")[1])
            for n in nx.descendants(graph, f"PROCESS:{t['id']}")
            if n.startswith("PROCESS:")
        }
        if f"PROCESS:{t['id']}" in graph
        else set()
        for t in tasks
    }
    constraints = []
    chosen = {}
    resources = snapshot["resources"]
    remaining_budget = Decimal(snapshot["budget"]) if snapshot["budget"] is not None else None
    for task in tasks:
        if task["target"] is None:
            constraints.append(
                {
                    "process_id": task["id"],
                    "code": "MISSING_BIA",
                    "detail": "Tiklash maqsadi baholanmagan.",
                }
            )
            continue
        for option in task["options"]:
            requirements = {str(k): v for k, v in option["resources"].items()}
            requirements["staff"] = option["staff"]
            cost = Decimal(option["cost"])
            if (
                option["duration"] + option["preparation"] > task["target"]
                or task["rpo"] is not None
                and option["rpo"] > task["rpo"]
            ):
                continue
            if any(
                key not in resources or amount > resources[key]["capacity"]
                for key, amount in requirements.items()
            ):
                continue
            if remaining_budget is not None and cost > remaining_budget:
                continue
            chosen[task["id"]] = {**option, "requirements": requirements}
            if remaining_budget is not None:
                remaining_budget -= cost
            break
        if task["id"] not in chosen:
            constraints.append(
                {
                    "process_id": task["id"],
                    "code": "NO_FEASIBLE_STRATEGY",
                    "detail": "RTO/RPO, budjet yoki resurs quvvatiga mos variant yo‘q.",
                    "options": task["options"],
                }
            )
    if cycles:
        constraints.append(
            {
                "code": "DEPENDENCY_CYCLE",
                "detail": "Majburiy bog‘liqlik sikli mavjud; siklni bartaraf eting.",
                "cycles": sorted(cycles),
            }
        )
        # No fabricated recovery order for a cyclic prerequisite graph.
        return {
            "method": method,
            "feasible": False,
            "rows": [],
            "constraints": constraints,
            "rto_breaches": 0,
            "total_cost": "0",
            "makespan_minutes": 0,
            "utilization": {},
            "runtime_ms": round((perf_counter() - started) * 1000, 3),
            "algorithm_version": VERSION,
        }
    rows = []
    bookings = {key: [] for key in resources}
    finished = {}
    pending = [t["id"] for t in tasks if t["id"] in chosen]
    cursor = 0
    while pending:
        ready = (
            [pid for pid in pending if prerequisites[pid].issubset(finished)]
            if method == "constrained"
            else pending[:1]
        )
        if not ready:
            for pid in pending:
                constraints.append(
                    {
                        "process_id": pid,
                        "code": "BLOCKED_DEPENDENCY",
                        "detail": "Tiklanmagan yoki rejalashtirilmagan zarur jarayon mavjud.",
                        "prerequisites": sorted(prerequisites[pid] - finished.keys()),
                    }
                )
            break
        pid = ready[0]
        pending.remove(pid)
        option = chosen[pid]
        duration = max(1, option["duration"] + option["preparation"])
        earliest = max([0] + [resources[k]["available"] for k in option["requirements"]])
        if method == "baseline":
            earliest = max(earliest, cursor)
        else:
            earliest = max([earliest] + [finished[d] for d in prerequisites[pid]])
        candidates = sorted(
            {earliest}
            | {end for entries in bookings.values() for _, end, _ in entries if end >= earliest}
        )
        start = None
        for candidate in candidates:
            end = candidate + duration
            fits = True
            for key, amount in option["requirements"].items():
                intervals = bookings[key]
                checkpoints = (
                    {candidate}
                    | {a for a, b, _ in intervals if candidate <= a < end}
                    | {b for a, b, _ in intervals if candidate <= b < end}
                )
                if any(
                    amount + sum(n for a, b, n in intervals if a <= point < b)
                    > resources[key]["capacity"]
                    for point in checkpoints
                ):
                    fits = False
                    break
            if fits:
                start = candidate
                break
        if start is None:
            constraints.append(
                {
                    "process_id": pid,
                    "code": "RESOURCE_UNAVAILABLE",
                    "detail": "Resurs uchun vaqt topilmadi.",
                }
            )
            continue
        end = start + duration
        for key, amount in option["requirements"].items():
            bookings[key].append((start, end, amount))
        cursor = end
        finished[pid] = end
        task = by_id[pid]
        late = end > task["target"]
        if late:
            constraints.append(
                {
                    "process_id": pid,
                    "code": "RTO_BREACH",
                    "detail": f"Tugash {end} daqiqa > RTO {task['target']} daqiqa.",
                }
            )
        rows.append(
            {
                "process_id": pid,
                "process_name": task["name"],
                "strategy_id": option["id"],
                "strategy_name": option["name"],
                "start_minutes": start,
                "end_minutes": end,
                "target_rto_minutes": task["target"],
                "rto_breached": late,
                "assigned_resources": option["requirements"],
                "cost": option["cost"],
                "explanation": "Muhimlik navbati; ketma-ket."
                if method == "baseline"
                else "Zarur jarayonlar tiklangach, resurslar bo‘sh bo‘lgan eng erta vaqt.",
                "conditions": option["conditions"],
            }
        )
    for row in rows:
        for prerequisite in prerequisites[row["process_id"]]:
            if prerequisite not in finished or finished[prerequisite] > row["start_minutes"]:
                constraints.append(
                    {
                        "process_id": row["process_id"],
                        "code": "DEPENDENCY_ORDER",
                        "detail": f"Zarur {prerequisite}-jarayon oldin tiklanmagan.",
                    }
                )
    makespan = max(finished.values(), default=0)
    utilization = {
        key: round(
            sum((end - start) * n for start, end, n in values)
            / (makespan * resources[key]["capacity"]),
            4,
        )
        if makespan and resources[key]["capacity"]
        else 0
        for key, values in bookings.items()
    }
    return {
        "method": method,
        "feasible": bool(tasks) and len(rows) == len(tasks) and not constraints,
        "rows": rows,
        "constraints": constraints
        or ([] if tasks else [{"code": "NO_DATA", "detail": "Faol jarayonlar kiritilmagan."}]),
        "rto_breaches": sum(r["rto_breached"] for r in rows),
        "total_cost": str(sum(Decimal(r["cost"]) for r in rows)),
        "makespan_minutes": makespan,
        "utilization": utilization,
        "runtime_ms": round((perf_counter() - started) * 1000, 3),
        "algorithm_version": VERSION,
    }
