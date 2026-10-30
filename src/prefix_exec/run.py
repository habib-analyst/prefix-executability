"""Experiment driver: arms x tasks, paired metrics, paired bootstrap CIs."""

from __future__ import annotations

import random

from .agents import inject_defects, run_checked, run_policy
from .scorer import aggregate, score_trajectory
from .stats import paired_ci
from .tasks import generate_tasks, make_goal
from .world import new_world

DEFECT_RATES = {"p_stale": 0.20, "p_skip": 0.15, "p_type": 0.10}

ARMS = ["baseline", "plan", "check_drop", "check_repair"]


def run_arm(task, arm, defect_rates, defect_seed):
    """Return (executed_trajectory, planned_trajectory_or_None)."""
    world = new_world(task["world_seed"])
    if arm == "baseline":
        return run_policy(task, world, coordinated=False), None
    plan = run_policy(task, world, coordinated=True)
    if defect_rates is None:
        defective, _ = plan, []
    else:
        rng = random.Random(defect_seed)
        defective, _ = inject_defects(plan, rng, defect_rates["p_stale"],
                                      defect_rates["p_skip"], defect_rates["p_type"])
    if arm == "plan":
        return defective, plan
    if arm == "check_drop":
        return run_checked(task, world, defective, repair=False), plan
    if arm == "check_repair":
        return run_checked(task, world, defective, repair=True), plan
    raise ValueError(arm)


def run_experiment(n_tasks, seed, defect_rates=DEFECT_RATES):
    """Run all arms on the same task list. Returns nested results dict."""
    tasks = generate_tasks(n_tasks, seed)
    per_arm_rows = {a: [] for a in ARMS}
    per_arm_per_task = {a: [] for a in ARMS}  # (success, ter1, auc1) per task
    planned_ter = []
    for task in tasks:
        world = new_world(task["world_seed"])
        goal = make_goal(task)
        for arm in ARMS:
            traj, planned = run_arm(task, arm, defect_rates,
                                    defect_seed=seed * 1000003 + task["id"])
            row = score_trajectory(world, traj, goal)
            per_arm_rows[arm].append(row)
            per_arm_per_task[arm].append(
                (1.0 if row["success"] else 0.0,
                 1.0 if row["fed"] == row["T"] + 1 else 0.0,
                 (row["fed"] - 1) / row["T"] if row["T"] > 0 else 0.0))
        if planned is not None:
            prow = score_trajectory(world, planned, goal)
            planned_ter.append(1.0 if prow["fed"] == prow["T"] + 1 else 0.0)
    out = {"n_tasks": n_tasks, "seed": seed,
           "defect_rates": defect_rates,
           "arms": {a: aggregate(per_arm_rows[a]) for a in ARMS},
           "per_family": {},
           "contrasts": {}}
    for fam in ("oneway", "roundtrip", "single", "bundle", "modify"):
        idx = [i for i, t in enumerate(tasks) if t["family"] == fam]
        out["per_family"][fam] = {
            a: aggregate([per_arm_rows[a][i] for i in idx]) for a in ARMS}
    # Paired contrasts: (delta, lo, hi) for b - a.
    def contrast(a, b, metric_idx):
        va = [r[metric_idx] for r in per_arm_per_task[a]]
        vb = [r[metric_idx] for r in per_arm_per_task[b]]
        return paired_ci(va, vb)
    for name, a, b in [("plan_minus_baseline", "baseline", "plan"),
                       ("repair_minus_plan", "plan", "check_repair"),
                       ("repair_minus_drop", "check_drop", "check_repair"),
                       ("drop_minus_plan", "plan", "check_drop")]:
        out["contrasts"][name] = {
            "success": contrast(a, b, 0),
            "TER": contrast(a, b, 1),
            "AUC_PEC": contrast(a, b, 2),
        }
    if planned_ter:
        out["planned_TER_mean"] = sum(planned_ter) / len(planned_ter)
    return out
