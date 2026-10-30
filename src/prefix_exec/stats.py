"""Paired bootstrap CIs over tasks (same task list across arms)."""

from __future__ import annotations

import random


def paired_ci(values_a, values_b, n_resamples=2000, seed=424242):
    """values_* are per-task metric lists of equal length.

    Returns (delta_mean, ci_low, ci_high) for mean(b) - mean(a), using
    percentile bootstrap resampling task indices with replacement.
    """
    assert len(values_a) == len(values_b)
    n = len(values_a)
    rng = random.Random(seed)
    deltas = []
    for _ in range(n_resamples):
        idx = [rng.randrange(n) for _ in range(n)]
        ma = sum(values_a[i] for i in idx) / n
        mb = sum(values_b[i] for i in idx) / n
        deltas.append(mb - ma)
    deltas.sort()
    lo = deltas[int(0.025 * n_resamples)]
    hi = deltas[int(0.975 * n_resamples) - 1]
    return (sum(values_b) / n - sum(values_a) / n, lo, hi)
