# Evaluation consolidation: one instrument set, two modes

**Date:** 2026-09-07
**Status:** **accepted for trial.** This document is the entry point for that work — `HANDOFF.md` points a fresh session here. The trial runs on its own branch, against the existing data, and only replaces `main` if it measurably improves on it; if it does not, this document is the record of why it was tried.

**How to start:** read this document, then [`PM-BRANCH-TRANSPLANT-FINDINGS.md`](PM-BRANCH-TRANSPLANT-FINDINGS.md) for the evidence behind every claim in it, then `HANDOFF.md`'s "Next Session" for the branch name and first action. Do not begin by re-deriving the evidence — it is already reproducible from `archive/2026-09-07-pm-branch-transplant/`.
**Evidence:** [`PM-BRANCH-TRANSPLANT-FINDINGS.md`](PM-BRANCH-TRANSPLANT-FINDINGS.md), this repo's `eval/leaderboard.md` (207 one-shot trials), and `relative-velocity`'s model-evaluation series (reports 01-04, 32 supervised PM runs).
**Supersedes in direction, not yet in fact:** [`V3-DISCRIMINATION-ASSESSMENT.md`](V3-DISCRIMINATION-ASSESSMENT.md). That document proposes fixing score compression by reweighting a composite. This proposal argues the composite is itself the problem and should be deleted rather than re-tuned. If this is accepted, most of v3's open items stop being work that needs doing.

---

## The problem, stated once

Two projects have been trying to answer the same question with different machinery.

`relative-velocity` runs the real `project-manager` Mode B workflow and grades the resulting branch with hand-written conformance harnesses plus an AI-judged 6x5 rubric. It produces *seat verdicts* — which model belongs in the Developer, drift-audit and code-review seats — which is exactly what the operator needs. It costs 1h13m to 20h21m of supervised wall-clock per run plus scarce PM attention, its rubric changed between reports so cross-report comparison is disclaimed, and its top-9 ordering is explicitly described by its own author as "indicative".

`ai-agent-bench` runs the same substrate one-shot with no loop, and grades it mechanically. It produces repeatable numbers cheaply. But it averages seven categories into a composite, five of which saturate, so the distribution compresses and a strong frontier anchor (`gpt-5.6-terra`, composite 88.2) lands below a cloud model (`deepseek-v4-flash`, 91.7) and barely above a local one.

Neither is wrong. They measure different things and have never been put on one ruler.

## What the experiment changed

Five results from [`PM-BRANCH-TRANSPLANT-FINDINGS.md`](PM-BRANCH-TRANSPLANT-FINDINGS.md) drive this proposal. Only the first was expected.

1. **The transplant works.** This repo's `frozen-substrate` and `relative-velocity`'s branch point are byte-identical across all 12 files, every PM branch changes exactly Task 001's four authorized files, and every branch exposes the same public API the task's `reference_solution` declares. `grade_trial.py` grades a PM branch unmodified, in ~5 minutes.

2. **Correctness does not transfer between the two modes, for a reason worth knowing.** Task 001's `spec.md` pins literal strings the plan never demanded — an exact docstring sentence, and the literal word "non-negative" in a rejection message where a branch wrote "contains negative counts". Semantically identical code fails. Correctness is therefore a *within-mode* signal only. This confirms "correctness is a gate, not a score" on a firmer basis than saturation alone.

3. **The mutation gate saturating in report 04 was a property of its 19-mutation bank, not of the PM loop.** Report 04 recorded 18/19 kills for 12 of 12 branches and concluded the defect class was closed. This repo's 73-mutation bank, run over the same suites, spreads them **0-93%**. Bank size and behavioural diversity are the load-bearing variable — so mutation kill rate remains the primary discriminator in *both* modes, and report 04's "the instrument has saturated" needs re-reading as "that instrument had saturated".

   Two corollaries. The larger bank **reorders the cohort against the AI rubric** — report 04's top branch (30/30) ranks 6th on test power and its second (29/30) ranks 12th of 13. And **within-model variance has not collapsed**: the same two `ornith-1.5-397b-q6` runs score 64% and 78%, against report 04's 2-point spread, so report 03's "run every configuration at least twice" stands.

4. **Lint is laundered only against the ruleset the agent was told to satisfy.** The operator is right that a post-hoc lint pass over PM output measures the commit chain, not the model — report 04 found `pyflakes` clean on all 14 branches. But grading the same branches under this repo's stricter pinned `ruff_eval.toml` spreads them **0-100%**, and scores the one branch that ships a red suite at 0%. The generalisable principle: **grade under a policy the agent does not hold.**

5. **Deterministic structure predicts the AI judge's maintainability call about as well as the judge's own total score does.** Across 13 branches, a three-component structural proxy (function count, median function length, mean cyclomatic complexity) correlates with report 04's hand-assigned maintainability at rho = +0.69; report 04's own 30-point total correlates with its own maintainability sub-score at +0.73. Helper count alone reaches +0.65, independently reproducing report 04's "cheapest single predictor" claim. Test LOC and test count correlate with nothing (~0.0), confirming three reports' worth of "test volume is a vanity metric".

   One correction to report 04 falls out: **module LOC is not a good predictor** (rho = -0.15 against maintainability, not the "negative" relationship report 04 claims). That claim rested on a single 726-line branch ranking 10th.

6. **The PM loop is worth +6 to +20 points of mutation kill rate, and once -3** — measured per model on a common bank for the first time. The weakest one-shot model gains most (`kat-coder`, 57% alone, +12/+20); the strongest gains least (`deepseek-v4-flash`, 79% alone, +6/+8). **Supervision compresses toward a ceiling and buys the most for the weakest Developer.** That quantifies `relative-velocity`'s founding observation and explains why 32 supervised runs looked alike — and it is the number that makes a two-mode design worth having, because the gap is the thing worth reporting.

7. **The three-slice plan can become two, but not by dropping the obvious slice.** Slices 1 and 2 substantially duplicate each other (rho +0.68; both are dominated by input-validation guard-writing — 40 of their 57 mutations), while Slice 3 is statistically independent of both (rho +0.03) and is the only slice carrying scientific reasoning. Because the plan is a dependency chain, the rewrite is a **merge of Slices 1 and 2 into one slice, keeping Slice 3 intact** — removing one full PM cycle per Mode 2 run without losing either capability axis.

---

## The proposal

**One task. Two modes. One grading kernel. No composite.**

### Shape

| | **Mode 1 — screen** | **Mode 2 — qualify** |
|---|---|---|
| Input | `spec.md`, one shot, no loop | the same content as a **2-slice** PM Mode B plan (see evidence item 7) |
| Question | what can this model do alone? | what does it deliver in the workflow I actually run? |
| Cost | ~1.5h local x 3 attempts | 1h13m-20h + PM attention |
| Run it | on every new model | only on models that clear Mode 1 |
| Grader | `grade_trial.py` | `grade_trial.py`, via `branch_check.py` |

Task 001's `spec.md` already *is* `MERGER_RATE_PLAN-REVISED.md` reframed. These are not two tasks; they are one substrate in two modes. Keeping them as one artifact is the central DRY move — the hidden tests, the mutation bank, the authorized surface, the frozen substrate and the grader are written once and serve both.

### What is scored, what is a gate, what is a flag

The single most consequential change: **delete `composite_score` and the weighted rubric.** Report a profile of independent columns.

| Signal | Role | Source | Notes |
|---|---|---|---|
| **Mutation kill rate** | **the score** | existing 73-mutation bank | The only category spanning 0-100% in 207 one-shot trials. Requires a large, behaviourally diverse bank (finding 3). |
| **Correctness** | **gate** (pass/fail, no weight) | hidden tests | Saturates at 88-100% for every model; within-mode only (finding 2). Its job is catching the model that cannot do the physics at all. |
| **Structural quality** | **second score** | `code-health`'s `health.py` + AST metrics | Retires judged `maintainability` (finding 5). Not laundered by the commit chain. |
| **Lint** | **flag** | pinned `ruff_eval.toml` | Live in both modes *provided* it is a ruleset the agent was not optimising against (finding 4). |
| **Scope discipline** | **flag** | existing check | 100% for every model on every Task 001 trial. Zero information as a score; still worth failing loudly on. |
| **Reliability** | **record** | manifest + transcript | completed / no-submission / looped / faked / timed-out / confirmed-technical-failure, plus wall-clock. Report 04 lost 14% of runs to non-cognitive failure; this is a first-order result, not noise. |
| **Readability, maintainability (judged)** | **retired** | — | See "What is retired". |

### What is retired, and why

- **`composite_score` and the category weights.** Averaging five saturated signals with one discriminating signal is what produced the compression. There is nothing to reweight once the average is gone. This also dissolves most of the v3 agenda: no rubric version bump, no cohort archival, no `code_quality` weight formula, no anti-gaming validation of that formula.
- **The judged categories.** Their measured contribution is small (readability/maintainability move in 10-point steps and mostly track harness family), they carry a disclosed same-family bias, and a deterministic proxy now reproduces the maintainability signal at rho +0.69. Retiring them also removes a model call from the grading path, which is the operator's stated reason for building this repo.
- **The 5-task bank as a mandatory screen.** Task 001's mutation column alone reproduces the top four and bottom three of the full five-task composite ordering, at one fifth the Mac Studio time. Tasks 002-005 stay in the repo; they stop being required for a routine model check.

### Why the axes then extend cheaply

With a weighted composite, adding an axis forces a re-weight, a rubric version bump and a cohort archival — which is exactly why extending the bench has felt expensive. With independent columns, a new axis is a new column and every existing column stays valid:

- **debugging / root-cause** — found the fault: yes/no, plus time-to-find
- **code review** — precision and recall against a seeded-defect corpus
- **paper comprehension** — fraction of equations, units and parameters correctly extracted, and ambiguities flagged rather than silently resolved
- **performance at scale** — pass/fail against an enforced wall-clock or memory ceiling

None of these needs the scoring policy to change. That is the property worth buying.

## Two things `relative-velocity` asked for that already exist here

Report 04's §7.8 names two mechanical gates "that no model provides". One is already implemented in this repo and the other is one line of task prose:

1. **"Run the suite once from outside the repository root."** `grade_trial.py` already does this — `ships_red_outside_root()`, run on every trial. It is the gate that would have caught report 04's only red-shipping branch, which had cleared the mechanical floor three times, nine code reviews and three drift audits.
2. **"Require one acceptance-criterion test to use a non-default config value."** Task 001 already has the hidden test (`test_E09_expected_slope_tracks_nondefault_alpha`) for the property whose mutation survived in 10 of 12 PM branches. Promoting the requirement into the plan's own acceptance criteria closes it at source.

## Cost

| | today | proposed |
|---|---|---|
| Mac Studio time per local model, screen | ~15-25h (5 tasks x 3) | **~4.5h** (1 task x 3) |
| Scoring policy surface | 7 categories, 2 profiles, weights, gates, penalties, judge settings | 2 scores, 1 gate, 3 flags |
| Model calls in the grading path | 1 judge invocation per trial | **0** |
| Adding an axis | reweight + version bump + archive cohort | add a column |
| Existing 207 records | valid | **still valid** — every field is already recorded per-trial |

The last row matters most. The proposed profile view needs no re-grading and no rubric change: correctness, mutation rate, scope, hygiene, completion and duration are already in every `eval/results/runs/*.json`. A new `aggregate.py` view is a day's work; v3 as currently scoped is weeks.

## The trial: what to build, in what order

The trial runs on its own branch and is designed so each step is independently checkable against data that already exists. Nothing here needs a new model run until step 5.

1. **The profile view.** A new `aggregate.py` output (or a sibling script) that reads the existing `eval/results/runs/*.json` and emits independent columns — correctness as a gate, mutation kill rate, scope and lint flags, completion and duration — with no composite and no weights. **Checkable immediately:** it must reproduce the per-category numbers already in the 207 records, and it must rank `gpt-5.6-terra` below the models whose tests actually kill mutations.
2. **The structural-quality score.** Fix and freeze a formula over `code-health`'s facts plus AST metrics — evidence item 5 supports function count, median function length and mean cyclomatic complexity, and rules out module LOC and test volume. **Checkable immediately:** against the 13 labelled branches in `archive/2026-09-07-pm-branch-transplant/` (target: beat rho +0.69), and then at population scale across the archived submission patches for all 207 trials.
3. **Promote `branch_check.py`** from `archive/2026-09-07-pm-branch-transplant/` into `eval/harness/`, with a test, so Mode 2 grading is a first-class path rather than experiment scaffolding.
4. **Rewrite the plan to two slices** (merge Slices 1 and 2, keep Slice 3), per evidence item 7. This is the only step that touches `relative-velocity`.
5. **Validate end to end**: one Mode 1 screen and one Mode 2 run of the same model on the rewritten plan, graded by the same kernel, and confirm the capability-vs-delivered delta reproduces.

Only after step 5 does the question of replacing `main` arise.

## Open decisions for the operator

Settled by the decision to trial this: the two-mode shape, deleting the composite, and the two-slice plan rewrite. Still genuinely open:

1. **Do the judged categories go, or stay pending more evidence?** n=13 for the structural proxy is small. A defensible middle path is to keep recording them for one more batch while scoring on the deterministic columns, then compare.
2. **Does Mode 2 stay in `relative-velocity`, or move here?** Keeping the plan where it is preserves the four-report history; moving it consolidates the substrate. This proposal assumes the former and links the two by the shared grader.
3. **Which structural metrics enter the second score, and with what formula?** Finding 5 supports function count, median function length and mean cyclomatic complexity, and rules out module LOC and test volume. The exact combination needs fixing and freezing before it is used to rank anything.
4. **Freeze `relative-velocity`'s 6x5 rubric, or drop it?** If Mode 2 keeps an AI-judged layer at all, it must stop changing between reports — the scale has already changed three times (01: /100, 02: /35, 03-04: /30), which is why the series disclaims cross-report comparison.
5. **The saturation problem is not solved by any of this.** Both instruments are at ceiling for the current local field on this substrate. The proposal makes the measurement cheaper, more honest and extensible; it does not create discrimination above the ceiling. That needs a categorically different task shape — debugging with no location hint, or an enforced performance budget — and neither exists in either repo.

## What not to do

- **Do not build "another Task 002."** A less-pinned design-decision task was already tried here and saturated on correctness exactly like the pinned one. Report 04 independently asks for "a genuinely harder plan with a design decision rather than pinned literals" — that experiment has already been run, and the answer is no.
- **Do not rescale scores to spread the distribution.** Compression is caused by averaging saturated signals, not by the scale.
- **Do not treat `relative-velocity`'s AI-judged ordering as ground truth.** Report 04 §9 disowns its own top-9 ordering. The deterministic layer — 55 conformance criteria, mutation kills, probes — is the part that separated real outcomes, and it separated failures cleanly while saying little about ranks 1-9.
