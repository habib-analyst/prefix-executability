# PREREG — project #103 `prefix-executability`

Locked 2026-10-30, BEFORE the head-to-head run, after pilot only.
Pilot: N=400, seed 101. Head-to-head: N=1000, fresh seed 20261031.
Decision rule (standing, #97 lesson): ANY locked bar fails -> KILL.
No amendments, no bar-moving, no bar-shrinking, ever.

## Arms (same task list, paired)
- `baseline`: reactive validate-before-act greedy first-choice policy.
- `plan`: globally coordinated plan, defect-injected (p_stale=0.20,
  p_skip=0.15, p_type=0.10), executed blindly.
- `check_drop`: plan + pre-execution checking, invalid calls dropped.
- `check_repair`: plan + pre-execution checking with repair (Dual-Loop analog).

## G2 — disease: final-success rankings diverge from prefix-executability rankings
- D1: success(plan) − success(baseline) >= 0.05, paired bootstrap 95% CI excludes 0.
- D2: TER(plan) − TER(baseline) <= −0.10, paired bootstrap 95% CI excludes 0.
- D3: AUC_PEC(plan) − AUC_PEC(baseline) <= −0.05, paired bootstrap 95% CI excludes 0.
- Pilot values (for reference, NOT bars): +0.110 [+0.043, +0.175];
  −0.365 [−0.413, −0.318]; −0.163 [−0.189, −0.139].

## G3 — load-bearing mechanism: Dual-Loop pre-execution plan checking
- M1: TER(repair) − TER(plan) >= 0.10, paired bootstrap 95% CI excludes 0.
- M2: AUC_PEC(repair) − AUC_PEC(plan) >= 0.05, paired bootstrap 95% CI excludes 0.
- M3: success(repair) − success(plan) >= 0.0 point estimate AND paired
  bootstrap 95% CI excludes 0 (checking restores executability while
  preserving — here, improving — terminal success).
- Ablations (which component carries the gain):
- A1: TER(drop) − TER(plan) >= 0.10, CI excludes 0 (checking alone restores TER).
- A2: |success(drop) − success(plan)| <= 0.005 (dropping alone changes
  nothing on success: invalid calls are no-ops under blind execution too,
  so the executed valid calls are identical).
- A3: success(repair) − success(drop) >= 0.05, CI excludes 0
  (REPAIR, not dropping, carries the success gain).
- Pilot values: M1 +0.365, M2 +0.163, M3 +0.275, A1 +0.365, A2 0.000, A3 +0.275.

## Benign / utility bound (clean trajectories, defect rates all 0, same seed)
- B1: success(repair_clean) >= success(plan_clean) − 0.02.
- B2: TER(repair_clean) >= 0.99.
- Pilot clean check (N=200, seed 101): plan_clean success 0.985,
  repair_clean success 0.985, TER both 1.0 (bundle 0.94 is a stock
  shortage, not a checker effect — identical across arms).

## Statistics
Paired bootstrap over tasks, 2000 resamples, seed 424242, percentile CIs.
All four arms see identical task lists and identical world seeds.

## Pilot calibration history (disclosed, pre-lock)
- Pilot v1 (rates 0.25/0.20/0.15): plan success 0.445 < baseline 0.615.
  Diagnosis: world-construction artifacts, not a missing phenomenon —
  (a) product category and warehouse were perfectly confounded
  (all gadgets W1, all widgets W2, all tools W3), so coordinated
  bundles were impossible unless q1==q2; (b) flight ids were assigned
  in fixed airline order, so baseline first-choice outbound/return
  airlines always matched; (c) BOS→MIA lacked a reverse route.
  Fixes: decoupled category×warehouse (all 9 combos present), shuffled
  airline order per route/date, symmetric routes.
- Pilot v2: bundle baseline still 0.90 — within-category id order put
  the W1 product first for every category. Fix: shuffled combo→id order.
- Pilot v3 (rates 0.20/0.15/0.10): divergence on all three axes (above).
  Defect rates and world fixes are frozen at pilot-v3 values for the
  head-to-head; no further tuning after this lock.
