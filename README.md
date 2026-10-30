# prefix-executability

A deterministic, CPU-only, $0 open analog of arXiv 2610.40444
(Rezaeian et al., Oracle AI), "Prefix Executability: Evaluating
Tool-Using Agents Beyond Final Success".

The paper's protocol: every prefix of a tool-call sequence must stay
executable under schemas, preconditions, and data dependencies. We
implement its metric family exactly (paper §2.2) — FED, PEC survival
curve, TER, AUC-PEC, Recovery Rate — over scripted agents on a synthetic
airline/retail tool suite (14 tools, tau^3-bench shape), and test the
paper's two headline claims in the analog: (1) plan-conditioned agents
reach higher final success while lowering executability; (2) Dual-Loop
pre-execution plan checking restores executability while preserving
terminal success.

## Headline (head-to-head, N=1000 tasks, seed 20261031, paired bootstrap)

| arm | final success | TER | AUC-PEC | Recovery Rate |
|---|---|---|---|---|
| baseline (reactive, validate-before-act) | 0.569 | 1.000 | 1.000 | — (0 invalid prefixes) |
| plan (coordinated, unverified, defect-injected) | 0.660 | 0.609 | 0.823 | 0.151 (59/391) |
| plan + check-drop | 0.660 | 1.000 | 1.000 | — |
| plan + check-repair (Dual-Loop analog) | 0.930 | 1.000 | 1.000 | — |

- Disease: plan−baseline success **+0.091** [0.052, 0.130], TER **−0.391**
  [−0.422, −0.361], AUC-PEC **−0.177** [−0.193, −0.162] — final-success
  rankings and prefix-executability rankings diverge, as in the paper.
- Mechanism: repair−plan TER **+0.391**, AUC-PEC **+0.177**, success
  **+0.270** [0.244, 0.298] — checking restores executability and
  improves terminal success.
- Ablation: checking alone (drop) restores TER/AUC-PEC with success
  IDENTICAL to plan (0.000 delta — invalid calls are no-ops under blind
  execution too); only repair adds success (+0.270 over drop). So
  checking carries executability, repair carries success.
- Benign bound (clean trajectories, no defects): repair success 0.987 =
  plan success 0.987, TER 1.000 — checking costs nothing when plans
  are already valid.
- Plan PEC: 1.000 at k=1 (first calls are searches, always valid),
  0.966 at k=2, 0.920 at k=3, 0.759 at k=5; baseline PEC is 1.000
  throughout (validate-before-act, by construction).

All PREREG bars passed (see PREREG.md); zero amendments. Determinism:
re-running the head-to-head command reproduces `results.json`
byte-identically; SHA-256
`0d2ec86b641a4c50046d3dfc44cbefe45bd8464aefc16d76f84d53659199c875`.

## What this is — and is not

Scripted-analog numbers only. The paper's BFCL-v3 / ToolSandbox /
tau^3-bench figures (6,768 rollouts, frontier LLMs) are context, never
claimed reproduced. The paper's Dual-Loop verifier is LLM-based; the
analog's checker is a deterministic rule-based validator implementing
the same pre-execution validation function. Baseline TER = 1.0 is by
construction (it validates before acting); the claim is the
success/TER tradeoff across arms.

## Run it

```bash
python3 run_experiment.py --seed 20261031 --n-tasks 1000 --out results.json
python3 run_experiment.py --seed 20261031 --n-tasks 1000 --clean --out results_clean.json
python3 -m pytest tests/ -q   # 11/11
```

## Layout

- `src/prefix_exec/world.py` — synthetic airline/retail world
- `src/prefix_exec/tools.py` — tool schemas, validation, execution
- `src/prefix_exec/scorer.py` — prefix replay, FED/PEC/TER/AUC-PEC/RR
- `src/prefix_exec/tasks.py` — task families + goal predicates
- `src/prefix_exec/agents.py` — baseline / plan / defect injection / checker
- `src/prefix_exec/stats.py` — paired bootstrap CIs
- `src/prefix_exec/run.py` — experiment driver
- `KILLGATE.md` — per-gate verdicts incl. G1 author-code recheck
- `PREREG.md` — locked bars, pilot calibration history
