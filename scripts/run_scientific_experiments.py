"""Reproduce synthetic sensitivity experiments without a database or web framework."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
from bcms_domain.scientific import WEIGHTS
from apps.engine.sensitivity import sweep_weights, ablate_operands, sweep_tmax, sweep_thresholds


def run():
    data = json.loads((ROOT / 'tests/sensitivity_reference.json').read_text())
    return dict(dataset='synthetic reference; not empirical pilot data',
                weights=sweep_weights(data, WEIGHTS, delta=0.05),
                ablation=ablate_operands(data, WEIGHTS),
                tmax=sweep_tmax([0, 4, 12, 24, 48, 72, 96]),
                thresholds=sweep_thresholds([1, 4, 6, 7, 14, 15, 20, 25]))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    content = json.dumps(run(), indent=2, sort_keys=True, allow_nan=False) + '\n'
    if args.output:
        args.output.write_text(content)
    else:
        print(content, end='')
