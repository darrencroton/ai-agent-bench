# Grading PM-workflow branches with the one-shot bench's instruments

**Date:** 2026-09-07
**Status:** completed experiment. Every number below is mechanically reproducible from the artifacts in `archive/2026-09-07-pm-branch-transplant/`; nothing here rests on a model's judgement.
**Proposal that follows from it:** [`EVAL-CONSOLIDATION-PROPOSAL.md`](EVAL-CONSOLIDATION-PROPOSAL.md).

---

## The question

This repo grades one-shot trials — no PM, no reviewers, no correction round — with hidden tests, a mutation gate and deterministic scope/lint checks. `relative-velocity` grades real `project-manager` Mode B branches with hand-written conformance harnesses and an AI-judged 6x5 rubric. Across 207 trials here and 32 supervised runs there, the two have never been placed on one ruler, so three things were unmeasured:

1. Can this repo's instruments grade a PM branch at all?
2. What is the PM loop actually worth, per model, on a common scale?
3. Can deterministic structural metrics replace the AI-judged maintainability score?

## Method

The transplant is `reference_check.py` with one substitution: instead of installing `reference_solution/*.py` onto the task's authorized surface, install the four authorized files as they exist on a named PM branch. Everything downstream — worktree from `frozen-substrate`, isolated venv, hidden tests, the 73-mutation gate, scope discipline, pinned-ruff lint — is `grade_trial.py`, unmodified.

Records are written with `harness="none"`, which `aggregate.py` already excludes from every leaderboard cohort, and `model="pmbranch/<branch>"`. They are experiment evidence, not leaderboard results.

**Scope:** the 14 branches of `relative-velocity` report 04 (2026-08-26), retrieved from the `rv` sandbox's private clone by `git bundle`. Reports 02/03's branches were deliberately skipped — their Developer models (`qwen3.6-27b-bf16`, `qwen3.5-397b`, `qwen3-235b`) have no counterpart in this repo's 207 trials, so they could not contribute to question 2.

### Two feasibility checks, both passed before anything was graded

- **Substrate identity.** This repo's `frozen-substrate` (`5118620`) and `relative-velocity`'s branch point (`5d21ff9`) are byte-identical across all 12 files they share — every `src/` module, every baseline test, `requirements.txt`. Verified by SHA-256 per file.
- **Interface identity.** Every PM branch changes exactly the four paths in Task 001's `authorized_surface` (`src/config.py`, `src/calc.py`, `src/merger_rate.py`, `tests/test_merger_rate.py`), and every branch's `merger_rate.py` exposes the same ten public and private functions the task's `reference_solution` declares, plus its own extra helpers. The mutation bank's post-import monkey-patching therefore applies unchanged.

Grading cost ~4m40s per branch solo, ~5-11m under three-way parallelism.

---

## Findings

### 1. The transplant works

All 14 branches graded without a single change to `grade_trial.py`, `meta.yaml`, the hidden tests or the mutation bank. This is the enabling result: **the two projects can share one grading kernel**, and the expensive half of `relative-velocity`'s method — writing a conformance harness by hand from the plan text, per report — does not have to be repeated.

### 2. Correctness does not transfer between modes — and the reason is worth knowing

Every completed PM branch scores the *same* correctness, and it is not 100%. The failures are not model defects; they are places where Task 001's `spec.md` pins a literal string the plan never demanded. Two examples from the top-ranked branch, which report 04 scored 30/30 with zero confirmed defects:

- `test_B14_docstring_wording` requires the exact sentence *"Uncertainty follows Task 001's plug-in Poisson-error convention; it is not a confidence interval."* The branch's docstring says the same thing in its own words.
- `test_B15_rejection_messages_name_the_reason` requires the literal token `non-negative` in a rejection message. The branch says `n_pairs contains negative counts`.

**Correctness is therefore a within-mode signal only.** This is an independent argument for the conclusion the leaderboard already suggested from saturation (88-100% for every model on every task): correctness should be a gate that catches the model which cannot do the physics, not a weighted score. Here it does exactly that — it correctly zeroes the branch that produced nothing while sitting flat for everyone who produced something.

### 3. The mutation gate saturating in report 04 was a property of its bank, not of the PM loop

This is the finding that most changes the picture.

Report 04 ran a 19-mutation gate over each branch's own suite, recorded **18 of 19 killed by 12 of 12** completed branches, and concluded that the dominant defect class of reports 01-03 was "essentially closed" and that the instrument had saturated.

This repo's 73-mutation bank, run over the same suites, does not saturate. It spreads the same branches across a real range and **reorders them against report 04's own ranking** — the branch report 04 placed first on quality is not the branch with the strongest tests under the larger bank.

The operational conclusion: **mutation kill rate remains the primary discriminator in both modes, provided the bank is large and behaviourally diverse.** A 19-mutation bank is too coarse to separate competent suites; a 73-mutation bank separates them. Report 04's "the plan no longer discriminates" needs re-reading as "that instrument no longer discriminated".

### 4. Lint is laundered only against the ruleset the agent was told to satisfy

Report 04 found `pyflakes` clean on all 14 branches and concluded the lint floor "eliminated a defect class and therefore stopped finding anything". That is correct, and it is a property of the workflow, not of the models: the PM chain runs the `lint` skill before every commit, so any post-hoc pass over PM output sees a cleaned tree.

But grading the same branches under this repo's pinned `ruff_eval.toml` — a stricter ruleset the agent was never asked to satisfy — still produces findings, and they differ between branches. The top branch carries three `E702` findings (multiple statements on one line) that `pyflakes` does not check for at all.

**The generalisable principle: grade under a policy the agent does not hold.** Lint keeps real signal in both modes as long as the grading ruleset is external to, and stricter than, the one the workflow enforces. It is worth a flag, not a weighted category.

### 5. Deterministic structure predicts the AI judge's maintainability call about as well as the judge's own total does

Structural metrics were measured from the AST of each branch's `merger_rate.py`, plus `code-health`'s exact-window duplication detector, with no reference to any report. Spearman rank correlation against report 04's hand-assigned scores, n=13:

| metric | vs. maintainability | vs. readability | vs. total /30 |
|---|---|---|---|
| function count | **+0.65** | **+0.69** | +0.64 |
| helper count | **+0.65** | +0.65 | +0.56 |
| median function LOC | **-0.54** | -0.12 | -0.39 |
| mean cyclomatic | **-0.51** | -0.28 | -0.40 |
| max cyclomatic | -0.39 | -0.27 | -0.14 |
| comment density | -0.13 | +0.44 | -0.18 |
| module LOC | -0.15 | +0.23 | -0.09 |
| test LOC | -0.11 | -0.04 | -0.05 |
| test count | -0.12 | -0.06 | +0.10 |

A three-component proxy (function count, negated median function LOC, negated mean cyclomatic, averaged as ranks) reaches **rho = +0.69** against the judged maintainability score. For calibration, **report 04's own 30-point total correlates with its own maintainability sub-score at +0.73.** The deterministic proxy tracks the judge nearly as well as the judge's own headline number does.

It agrees exactly at both ends — it ranks the 5/5 branch first and the 2/5 branch last — and disagrees in the middle, which is precisely the band report 04 §9 already disowns as "indicative".

Three secondary results fall out:

- **Helper count alone reaches +0.65**, independently reproducing report 04's claim that it is "the cheapest single predictor of code quality in the dataset". The AST sweep also independently reproduced its "median function 27 lines" figure for the top branch.
- **Test volume predicts nothing** (test LOC -0.11, test count -0.12), confirming across a fourth instrument what reports 02, 03 and 04 each found separately.
- **Module LOC is not a predictor** (-0.15). This *corrects* report 04, which recorded the relationship as "negative — bigger is not more careful". That claim rested on a single 726-line branch ranking 10th.

### 6. The measured value of the PM loop

Question 2's answer, on a common bank, for the models that appear in both datasets.

#### Table 1 — every report-04 PM branch, graded by Task 001's instruments

| branch | correctness (gate) | mutation kill | scope | lint | det. score | report 04 /30 | report 04 kills /19 |
|---|---|---|---|---|---|---|---|
| `mixed-qwen3.8-27b-1` | 93% | **93%** | 100% | 67% | 90.6 | 27 | 18 |
| `mixed-deepseek-v4-flash-2` | 92% | **86%** | 100% | 100% | 92.1 | 26 | 18 |
| `mixed-deepseek-v4-flash-1` | 92% | **85%** | 100% | 100% | 91.9 | 27 | 18 |
| `mixed-qwen3.8-27b-2` | 91% | **81%** | 100% | 71% | 86.9 | 25 | 18 |
| `mixed-minimax-m2.7-1` | 87% | **79%** | 100% | 45% | 81.3 | 21 | 19 |
| `mixed-ornith-1.5-397b-q6-2` | 92% | **78%** | 100% | 77% | 87.2 | 30 | 19 |
| `mixed-ornith-1.5-35b-a3b-bf16-2` | 87% | **78%** | 100% | 83% | 85.3 | 26 | 18 |
| `mixed-kat-coder-v2.5-dev-bf16-2` | 84% | **77%** | 100% | 0% | 73.9 | 22 | 18 |
| `mixed-ornith-1.5-35b-a3b-bf16-1` | 91% | **70%** | 100% | 83% | 84.8 | 24 | 18 |
| `mixed-kat-coder-v2.5-dev-bf16-1` | 90% | **68%** | 100% | 100% | 85.9 | 23 | 17 |
| `mixed-hy3-1` | 87% | **67%** | 100% | 91% | 83.0 | 26 | 18 |
| `mixed-ornith-1.5-397b-q6-1` | 88% | **64%** | 100% | 100% | 84.1 | 29 | 18 |
| `mixed-kimi-k2.7-code-1` | 47% | **18%** | 100% | 100% | 51.0 | 18 | 7 |
| `mixed-glm-5.2-1` | 0% | **0%** | 0% | 0% | 0.0 | 0 | — |

Three things to read off it.

**The 73-mutation bank spans 0-93% where the 19-mutation bank spanned 89-100%.** Same branches, same suites, same day. The saturation report 04 reported was the instrument, not the models.

**The ordering disagrees materially with the AI rubric.** Report 04's top branch (30/30, 55/55 conformance, zero confirmed defects) ranks 6th on test power. Its second-ranked branch (29/30) ranks **12th of 13**. The best test suite in the cohort belongs to `qwen3.8-27b-1`, which report 04 placed 4th. These are not the same measurement, and the deterministic one is measuring the property three reports named as the dominant escape class.

**Within-model variance has not collapsed.** Report 04 §6.6 recorded the first reversal in the series — "the largest spread across six twice-run models is 2 points on a 30-point scale" — and used it to argue n=2 is now nearly sufficient. Under the larger bank, the same two `ornith-1.5-397b-q6` runs score **64% and 78%**, and the same two `kat-coder` runs score 68% and 77%. Report 03's conclusion stands after all: **run every configuration at least twice, and report the spread.**

Two negative controls behaved correctly without being told about them: `glm-5.2-1` (byte-identical to `main`) scores 0 in every category and is flagged rather than dropped, and `kat-coder-v2.5-dev-bf16-2` — the one branch report 04 found ships a red suite in a clean checkout — scores **0% lint** here, the worst in the cohort.

#### Table 2 — capability (one-shot) vs delivered (PM loop), on the same 73-mutation bank

| model | match | one-shot correctness | one-shot mutation | PM correctness | PM mutation | mutation delta |
|---|---|---|---|---|---|---|
| `kat-coder-v2.5-dev` | near (bf16 vs q8) | 90% | 57% | 90% | 68% | **+12** |
| `kat-coder-v2.5-dev` (run 2) | near (bf16 vs q8) | 90% | 57% | 84% | 77% | **+20** |
| `ornith-1.5-397b-q6` | exact | 97% | 67% | 88% | 64% | **-3** |
| `ornith-1.5-397b-q6` (run 2) | exact | 97% | 67% | 92% | 78% | **+11** |
| `deepseek-v4-flash` | exact | 97% | 79% | 92% | 85% | **+6** |
| `deepseek-v4-flash` (run 2) | exact | 97% | 79% | 92% | 86% | **+8** |
| `hy3` | exact | 98% | 59% | 87% | 67% | **+8** |

**This is the number neither project had.** The PM loop is worth roughly **+6 to +20 points of mutation kill rate**, and once **-3**.

The shape is more informative than the mean. The weakest one-shot model in the set gains the most (`kat-coder`, 57% alone, +12 and +20 supervised); the strongest gains the least (`deepseek-v4-flash`, 79% alone, +6 and +8). **Supervision compresses toward a ceiling and buys the most for the weakest Developer** — which is `relative-velocity`'s founding observation, now quantified rather than inferred, and the direct explanation for why the loop made 32 runs look alike.

The single negative delta matters too: a PM run is not guaranteed to beat the same model unsupervised on test power. `ornith-1.5-397b-q6`'s two supervised runs straddle its unsupervised mean.

### 7. How many plan slices are actually needed: two, but not the obvious two

`MERGER_RATE_PLAN-REVISED.md` runs three slices — (1) galaxy-count denominator and pair fraction, (2) merger timescale, rate conversion and persistence, (3) weighted redshift-evolution fit and validation. Each of this repo's 73 mutations maps unambiguously onto one of them (18 / 39 / 16), so the graded `per_mutation` records answer directly whether all three carry independent information.

The first cut looks like an easy yes to dropping Slice 3:

| subset | rank agreement with the full 3-slice result |
|---|---|
| Slices 1+2 | rho = +0.96 |
| Slice 1 alone | rho = +0.87 |
| Slice 3 alone | rho = +0.38 |

**That reading is wrong, and it is wrong for an arithmetic reason:** Slices 1+2 are 57 of the 73 mutations, so they correlate with the total largely by construction. The honest question is whether the slices measure the *same* thing. Across the 12 completed branches:

| pair | rho |
|---|---|
| Slice 1 vs Slice 2 | **+0.68** |
| Slice 1 vs Slice 3 | -0.07 |
| Slice 2 vs Slice 3 | -0.02 |
| **Slices 1+2 vs Slice 3** | **+0.03** |

**Slices 1 and 2 substantially duplicate each other; Slice 3 is statistically independent of both.** The mechanism is visible in the mutation inventory: 10 of Slice 1's 18 and 30 of Slice 2's 39 mutations are input-validation guards, so both slices are dominated by the same capability — writing and testing form-validation. Slice 3 is the only one carrying the scientific reasoning (weighted least squares, numerical stability, the centring amendment, the config-derived expected slope).

All three produce comparable spread, so none is a dead axis:

| slice | min | max | range | sd |
|---|---|---|---|---|
| Slice 1 | 61% | 100% | 39 pts | 15.1 |
| Slice 2 | 64% | 97% | 33 pts | 9.7 |
| Slice 3 | 56% | 88% | 31 pts | 8.4 |

**Conclusion: two slices are enough, and they must be a validation slice plus Slice 3 — never Slices 1+2.** Because the plan is a dependency chain (Slice 2 consumes Slice 1's loader; Slice 3 fits the rates Slice 2 produces), the rewrite is not a deletion but a **merge of Slices 1 and 2 into one slice, with Slice 3 kept intact as the second.** That preserves both independent capability axes and the execution dependency, while removing one full PM cycle — one session, one review panel, one steer budget — from every Mode 2 run.

---

## Caveats

- **The delta in Table 2 is not a clean single-variable manipulation.** It compares one-shot-under-`spec.md` against PM-multi-slice-under-the-plan. That bundles the loop itself (steers, reviewers, per-slice commits) with a different contract document, a different time budget, and a plan amended three times to remove ambiguity. It measures "what the workflow delivers", not "what steering alone adds".
- **n is small and unbalanced.** One-shot figures are means of n=3; PM figures are n=1 or 2 per model. `kat-coder` is a quantisation mismatch (bf16 vs q8) and is marked `near`, not `exact`.
- **Correctness is not comparable across the two columns of Table 2** for the reason in finding 2. It is shown for completeness, not for comparison.
- **The structural correlation is n=13** against labels assigned by a single AI reader, and report 04 §9 states plainly that its harnesses and score mapping are its author's judgement. A +0.69 rank correlation on 13 points is suggestive, not settled.
- **`minimax-m2.7-1` was graded against a different plan digest** (`dae3fe5a`, amended mid-run by a human), as report 04 §4.4 records. Its row carries that confound.
- **These records are excluded from every leaderboard cohort** by `harness="none"`, and were archived out of `eval/results/runs/` after tabulation, per this repo's convention.

## Reproducing this

Everything is in `archive/2026-09-07-pm-branch-transplant/`:

| file | what it is |
|---|---|
| `branch_check.py` | the transplant driver — installs a PM branch onto Task 001's authorized surface and emits a `grade_trial.py` manifest |
| `run_batch.sh` | batch driver, takes a file of branch names |
| `structural_metrics.py` | AST + `code-health` structural sweep |
| `emit_tables.py`, `tabulate.py` | table generation from the graded records |
| `oneshot_task001.json` | this repo's 46 Task 001 trials, aggregated per model |
| `report04_labels.json` | report 04's rubric scores, conformance and mutation kills, transcribed by hand |
| `structural_metrics.{json,md}` | the structural sweep's output |
| `pm_branch_results.json`, `tables.md` | the graded PM-branch results |
| `runs/`, `reports/`, `manifests/` | the 14 archived graded records, reports and manifests |
| `logs/` | per-branch and per-batch run logs |

The PM branches themselves live in the `rv` sandbox's private clone; retrieve them with `sbx exec rv bash -lc 'cd <repo> && git bundle create /tmp/rv04.bundle --branches'` followed by `sbx cp`.
