"""Small, fully synthetic comparisons. No claim about real organization outcomes."""

from copy import deepcopy
from hashlib import sha256
import json
from statistics import median
from apps.engine.scheduler import compare_schedules, VERSION


def dataset():
    base = {
        "tasks": [
            {
                "id": i,
                "name": f"O‘quv jarayoni {i}",
                "criticality": "CRITICAL" if i == 1 else "LOW",
                "priority": 0.8 if i == 1 else 0.2,
                "target": 180,
                "rpo": 30,
                "options": [
                    {
                        "id": i,
                        "name": "Zaxira server",
                        "duration": 60,
                        "preparation": 0,
                        "staff": 1,
                        "resources": {"server": 1},
                        "rpo": 15,
                        "cost": "100",
                        "conditions": "Sun’iy misol",
                    }
                ],
            }
            for i in [1, 2]
        ],
        "resources": {
            "server": {"name": "Server", "capacity": 2, "available": 0},
            "staff": {"name": "Mutaxassis", "capacity": 2, "available": 0},
        },
        "dependencies": [],
        "budget": "200",
        "units": {"time": "minute", "cost": "UZS"},
        "algorithm_version": VERSION,
    }
    dependency = deepcopy(base)
    dependency["dependencies"] = [
        {"from_type": "PROCESS", "from_id": 1, "to_type": "PROCESS", "to_id": 2}
    ]
    shortage = deepcopy(base)
    shortage["resources"]["server"]["capacity"] = 0
    return {"parallel": base, "prerequisite": dependency, "shortage": shortage}


def run_experiment(repeats=10):
    results = []
    for name, inputs in dataset().items():
        runs = [compare_schedules(inputs) for _ in range(repeats)]
        record = {
            "case": name,
            "input_hash": sha256(
                json.dumps(inputs, sort_keys=True, ensure_ascii=False).encode()
            ).hexdigest(),
            "input_snapshot": inputs,
            "methods": {},
        }
        for method in ["baseline", "constrained"]:
            example = runs[0][method]
            record["methods"][method] = {
                key: example[key]
                for key in [
                    "feasible",
                    "rto_breaches",
                    "total_cost",
                    "makespan_minutes",
                    "utilization",
                    "constraints",
                    "rows",
                ]
            }
            record["methods"][method]["median_runtime_ms"] = median(
                r[method]["runtime_ms"] for r in runs
            )
        results.append(record)
    return {
        "synthetic": True,
        "algorithm_version": VERSION,
        "repeats": repeats,
        "plan_preparation_time_measured": False,
        "cases": results,
    }
