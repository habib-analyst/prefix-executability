#!/usr/bin/env python3
"""Run the prefix-executability experiment.

Usage:
  python3 run_experiment.py --seed 101 --n-tasks 400 --out pilot_results.json
  python3 run_experiment.py --seed 20261031 --n-tasks 1000 --out results.json
  python3 run_experiment.py --seed 20261031 --n-tasks 1000 --clean --out results_clean.json
With --clean, defect rates are zero (benign/utility bound arm comparison).
Output JSON is deterministic: same seed + same code -> byte-identical file.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from prefix_exec.run import run_experiment  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--n-tasks", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--clean", action="store_true")
    args = ap.parse_args()
    from prefix_exec.run import DEFECT_RATES
    rates = {"p_stale": 0.0, "p_skip": 0.0, "p_type": 0.0} if args.clean else DEFECT_RATES
    res = run_experiment(args.n_tasks, args.seed, defect_rates=rates)
    # JSON with sorted keys + fixed float rendering for byte determinism.
    text = json.dumps(res, indent=2, sort_keys=True)
    Path(args.out).write_text(text + "\n")
    for arm, m in res["arms"].items():
        print(f"{arm:12s} success={m['success']:.4f} TER={m['TER']:.4f} "
              f"AUC_PEC={m['AUC_PEC']:.4f} RR={m['RR']} "
              f"(elig={m['RR_eligible']})")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
