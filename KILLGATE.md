# KILLGATE — project #103 `prefix-executability`

Source paper: arXiv 2610.40444, "Prefix Executability: Evaluating Tool-Using
Agents Beyond Final Success" (Rezaeian, Sun, Benajiba, Roth; Oracle AI;
submitted 29 Oct 2026). Context figures ONLY, never reproduced: 6,768
rollouts across BFCL-v3, ToolSandbox, tau^3-bench; the paper's
plan-conditioned divergence and Dual-Loop restoration. All numbers below
are from the scripted analog (synthetic airline/retail tool suite).

## G0 harness — PASS
Deterministic, CPU-only, $0, pure-stdlib Python, no LLMs/APIs/GPUs.
Scripted agents over a synthetic tool suite (14 tools, schemas,
preconditions, cross-step references) mirroring tau^3-bench Airline/Retail
workflows. 11/11 tests green.

## G1 author-code recheck — PASS (fresh, 2026-10-30)
- Abs page (arxiv.org/abs/2610.40444, fetched fresh): NO author code link.
  "Code, Data and Media" section holds only third-party finder toggles
  (alphaXiv, CatalyzeX, DagsHub, GotitPub, Hugging Face, ScienceCast,
  Replicate, Spaces, TXYZ.AI).
- Full-text HTML (arxiv.org/html/2610.40444v1, 1544 lines): exactly ONE
  "github" match — a trustagenticai.github.io workshop PDF in the
  references (not author code). ZERO "zenodo", ZERO "4open", ZERO
  "replication", ZERO "open source", ZERO "code is available".
- No author replication/data package exists in the paper text. Contrast
  #100 (host-cited anonymous 4open package) and #102's adjudicated
  caveat (unlocatable supplement reference): here there is not even a
  supplement reference. Nothing retrievable to duplicate.

## Differentiation gate — PASS (load-bearing, vs #56 and #85)
- #56 tool-trace-audit: POST-HOC trace truth — which tool's result leaks
  the answer (per-tool TF-IDF localization + counterfactual redaction).
  Object = the completed trace, judged after the fact.
- #85 harness-vcr: harness×agent blame attribution (VCR, pairing
  interaction). Object = which component to blame for failure.
- #103: PREFIX survival — a deterministic scorer walks the trajectory
  step by step and records First-Error Depth, the PEC survival curve,
  TER, AUC-PEC, and Recovery Rate; the intervention is PRE-execution
  plan checking that changes what gets emitted. Different object
  (survival to first invalid call + recovery), different metric family,
  different intervention, different failure taxonomy (schema /
  unknown-ref / precondition). Not a re-skin: no TF-IDF, no redaction,
  no harness pairing, no VCR anywhere in this build.

## Pilot gate — PASS (after disclosed world-design fixes; see PREREG.md)
Pilot v3 (N=400, seed 101): plan−baseline success +0.110
[+0.043, +0.175], TER −0.365 [−0.413, −0.318], AUC-PEC −0.163
[−0.189, −0.139] — the paper's headline divergence, in the analog.
Repair−plan: TER +0.365, AUC-PEC +0.163, success +0.275.
Plan Recovery Rate 0.123 (18/146 invalid-prefix trajectories still
succeeded — invalid informational/optional calls that do not block the goal).

## G2 / G3 — PASS, all bars, head-to-head N=1000 seed 20261031 (verified programmatically)
- D1 success plan−baseline +0.091 [0.052, 0.130] (bar >=0.05, CI excl 0).
- D2 TER plan−baseline −0.391 [−0.422, −0.361] (bar <=−0.10).
- D3 AUC-PEC plan−baseline −0.177 [−0.193, −0.162] (bar <=−0.05).
- M1/M2/M3 repair−plan: TER +0.391, AUC-PEC +0.177, success +0.270
  [0.244, 0.298] (all CIs excl 0).
- A1 drop−plan TER +0.391; A2 drop−plan success 0.000 exactly
  (|delta| <= 0.005); A3 repair−drop success +0.270 [0.244, 0.298].
- B1/B2 clean (defect rates 0): repair success 0.987 = plan 0.987
  (bar >= plan−0.02); repair TER 1.000 (bar >=0.99).
- Plan RR 0.151 (59/391 invalid-prefix trajectories still succeeded).
- Determinism: rerun byte-identical; results.json SHA-256
  0d2ec86b641a4c50046d3dfc44cbefe45bd8464aefc16d76f84d53659199c875.
- Zero PREREG amendments; no bar moved (the #97 rule, applied literally).

## Scope honesty (mandatory, everywhere)
- Scripted-analog numbers only. The paper's BFCL/ToolSandbox/tau^3-bench
  figures (6,768 rollouts) are context, never claimed reproduced.
- The paper's Dual-Loop verifier is LLM-based; the analog's checker is
  a deterministic rule-based validator implementing the same
  pre-execution validation function (schema + precondition + reference
  checks + repair). Stated in PAPER.md and README.md.
- Baseline TER = 1.0 is by construction (validate-before-act policy);
  the claim is the success/TER tradeoff across arms, not that real
  agents have TER 1.0.
- check_drop success is IDENTICAL to plan success by construction:
  invalid calls are no-ops under blind execution too, so dropping them
  changes neither state nor outcome. The ablation claim is therefore
  "checking alone restores TER; only repair adds success" — not that
  dropping improves success.
