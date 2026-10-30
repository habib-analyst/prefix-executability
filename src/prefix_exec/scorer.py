"""Deterministic prefix scorer + the paper's metric family (paper §2.2).

Replay a trajectory on a fresh world copy. FED = index (1-based) of the
first invalid call, or T+1 if every call is valid. Invalid calls are
no-ops; replay continues so final success Y and recovery stay defined.
Metrics over N rollouts, exactly per paper eqs. (4), (8), (9), (11):
  PEC(k)   = mean(1{FED > k})            (fixed-cohort survival curve)
  TER      = mean(1{FED == T+1})
  AUC-PEC  = mean((FED-1)/T)
  RR       = mean(Y | FED <= T), with RR-eligible count reported
"""

from __future__ import annotations

from .tools import execute, validate


def replay(world, trajectory):
    """Execute every call; return (fed, final_world, error_kinds).

    fed is 1-based; fed == len(trajectory)+1 means fully executable.
    """
    w = world.fork()
    fed = None
    kinds = []
    for i, call in enumerate(trajectory):
        ok, _out, err = execute(w, call["tool"], call.get("args", {}))
        kinds.append(err)
        if not ok and fed is None:
            fed = i + 1
    if fed is None:
        fed = len(trajectory) + 1
    return fed, w, kinds


def score_trajectory(world, trajectory, goal_fn):
    """Return dict(T, fed, success, recovered, error_kinds)."""
    fed, final, kinds = replay(world, trajectory)
    success = bool(goal_fn(final))
    return {"T": len(trajectory), "fed": fed, "success": success,
            "recovered": success and fed <= len(trajectory),
            "error_kinds": kinds}


def aggregate(rows):
    """rows: list of dicts with T, fed, success. Returns metric dict."""
    n = len(rows)
    if n == 0:
        return {"n": 0}
    ter = sum(1 for r in rows if r["fed"] == r["T"] + 1) / n
    auc = sum((r["fed"] - 1) / r["T"] for r in rows if r["T"] > 0) / n
    succ = sum(1 for r in rows if r["success"]) / n
    max_t = max(r["T"] for r in rows)
    pec = {k: sum(1 for r in rows if r["fed"] > k) / n for k in range(max_t + 1)}
    elig = [r for r in rows if r["fed"] <= r["T"]]
    rr = (sum(1 for r in elig if r["success"]) / len(elig)) if elig else None
    return {"n": n, "TER": ter, "AUC_PEC": auc, "success": succ,
            "PEC": pec, "RR": rr, "RR_eligible": len(elig),
            "mean_FED": sum(r["fed"] for r in rows) / n,
            "mean_T": sum(r["T"] for r in rows) / n}
