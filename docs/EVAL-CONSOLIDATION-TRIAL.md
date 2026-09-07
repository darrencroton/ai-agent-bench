# The consolidated evaluation: what was built, and what it was checked against

**Date:** 2026-09-07
**Status:** steps 1-4 of the trial implemented and validated on branch `eval-consolidation-trial`. Step 5's fresh Mode 2 model run is outstanding and is the operator's call; step 5's *grading path* is validated. Replacing `main` remains a decision for the operator alone, per the proposal.
**Design it implements:** [`EVAL-CONSOLIDATION-PROPOSAL.md`](EVAL-CONSOLIDATION-PROPOSAL.md).
**Evidence it rests on:** [`PM-BRANCH-TRANSPLANT-FINDINGS.md`](PM-BRANCH-TRANSPLANT-FINDINGS.md), and the 219 graded v2 trials in `eval/results/runs/`.

This document is the durable specification of the profile view's semantics and the frozen structural formula, and the record of every number the implementation was checked against. It is the reference the harness code points at.

---

## What the change is, in one paragraph

The weighted composite is deleted, not re-tuned. `eval/harness/profile_view.py` reads the same graded records `aggregate.py` reads and reports each signal as its own column: **mutation kill rate is the score**, **correctness is a pass/fail gate carrying no weight**, a new deterministic **structural score is a second, independent score** replacing the AI-judged `maintainability`, **lint and scope discipline are flags**, and **reliability is a record**. Nothing is combined into a total. `eval/harness/branch_check.py` makes the Mode 2 (PM-branch) grading path first-class over the same kernel. `relative-velocity`'s plan drops from three slices to two.

## Why the composite had to go, measured on this repo's own data

Ranking 16 models by each candidate signal, macro-averaged across tasks. `gpt-5.6-terra`'s rank differs by cohort for one signal only (composite score), so that row states both denominators explicitly; the other rows are the same rank whether the cohort is all 16 models or the 14 with complete task coverage:

| ranking signal | spread across models | `gpt-5.6-terra`'s rank |
|---|---|---|
| composite score | 75.6 - 93.1 (**17.5 pts**) | 6th of 16 (88.2), 5th of the 14 complete-coverage models |
| mutation kill rate | 33.8 - 90.3 (**56.5 pts**) | **13th of 16** (68.2) |
| correctness | 92.6 - 99.9 (**7.4 pts**) | 1st (99.9) |
| scope discipline | 218 of 219 trials perfect | -- |

Per-task, the same picture holds. Range of per-model means within each task:

| task | mutation kill | correctness | hygiene | scope discipline |
|---|---|---|---|---|
| 001-merger-rate-feature | **87.7** | 16.0 | 50.9 | **0.0** |
| 002-pair-binning-convention | **79.0** | 6.5 | 52.1 | **0.0** |
| 003-pair-finder-validation | **99.3** | 0.5 | 20.4 | **0.0** |
| 004-catalog-loader-test-adequacy | 33.3 | 33.3 | 33.3 | 33.3 |
| 005-scope-temptation | **42.4** | **0.0** | 11.6 | **0.0** |

Mutation kill rate is the only column with real spread on every task. Correctness contributes **0.0 pts of range on Task 005** and 0.5 on Task 003. Scope discipline contributes **0.0 pts on four of five tasks** -- including Task 005, which is *named* `scope-temptation` and was built specifically to catch scope violations; every model scores 100%. Task 004's uniform 33.3 across all four columns is one archived-pending technical failure (`ornith`'s SIGTERM'd trial), not signal.

Averaging one 56-point signal with several 0-to-6-point signals is what produced the compression. There is nothing to reweight once the average is gone.

## Is the primary score good enough to be *the* score?

**Signal-to-noise.** Over the 71 (task, model) groups with n>=3 trials:

| | mutation kill rate |
|---|---|
| within-model, run-to-run spread | median **6.1 pts**, mean 10.5, p90 19.2 |
| between-model spread, per task | median **79.0 pts** |

Roughly **13:1** on the median. The two worst within-model spreads (100 and 78.8 pts) are both already-documented technical failures, not model variance. Report 03's "run every configuration at least twice and report the spread" still stands -- 6.1 pts is not zero -- and the profile view prints the min-max range beside every mutation mean for exactly that reason.

## The correctness gate

```text
gate_pass  <=>  category_scores.correctness >= 0.70
```

Chosen because the observed distribution over 219 records is **one 0.0 and then nothing until 0.834**. The threshold sits in an empty band, so its exact value cannot change any verdict -- it is not a tuned parameter. Applied to the transplant cohort it fails both negative controls (the byte-identical-to-`main` branch at 0%, and the backend-outage branch at 47%) and passes every genuine submission.

A record whose `correctness` is `None` -- grading stopped before correctness was measured, e.g. a no-submission -- is a gate **FAIL**, never a skip. That is the case the gate exists to catch, not exempt.

## The structural score

### The formula, frozen

Per task, over the AST of the scored deliverables (see *Measurement scope* below), pooling functions across files **before** computing any statistic:

```text
function_count       top-level FunctionDef / AsyncFunctionDef in the module body
median_function_loc  median of (end_lineno - lineno + 1) over those functions
mean_cyclomatic      mean over those functions of 1
                       + one per {If, For, AsyncFor, While, ExceptHandler, Assert, IfExp}
                         in the function's ast.walk() subtree
                       + (len(values) - 1) per BoolOp
                       + len(ifs) per comprehension clause

decomposition = clamp01((function_count      -   3) / (18 -   3))
length        = clamp01((100 - median_function_loc) / (100 - 15))
complexity    = clamp01(( 15 -    mean_cyclomatic ) / ( 15 -  2))

structural_score = 100 * (decomposition + length + complexity) / 3
```

Every constant lives in `eval/profile.yaml`'s `structure:` block and is read at run time; none is hardcoded. The block's canonical sha256 is recorded in `eval/results/structure.json`'s `_meta.policy_sha256`, and `profile_view.py` warns if the two have drifted.

### Why these three metrics

`PM-BRANCH-TRANSPLANT-FINDINGS.md` finding 5, Spearman rho against report 04's hand-assigned `maintainability` over 13 labelled PM branches:

| metric | rho | verdict |
|---|---|---|
| function count | **+0.65** | scored |
| helper count | +0.65 | redundant with function count; not scored |
| median function LOC | **-0.54** | scored |
| mean cyclomatic | **-0.51** | scored |
| max cyclomatic | -0.39 | dominated by the mean |
| module LOC | -0.15 | rejected |
| comment density | -0.13 | rejected |
| test LOC / test count | -0.11 / -0.12 | rejected -- test volume is a vanity metric |
| `code-health` duplication | **-0.21** | rejected, see below |

**`code-health`'s `health.py` was dropped deliberately, against the proposal's own text.** The proposal names it as a source. The evidence does not support it: 12 of the 13 branches have *zero* detected duplication, and the duplication columns correlate at -0.21 versus +0.65 for pure AST function count. Depending on it would also mean hardcoding an absolute path to a personal skill directory into a grader that `AGENTS.md` requires to run identically inside an `agent-sbx` clone. Dropping it costs nothing measurable and removes an external dependency.

### Validation

| check | target | result |
|---|---|---|
| rho vs report 04 `maintainability`, n=13 | beat +0.69 | **+0.7246** |
| for calibration: report 04's own /30 total vs its own `maintainability` | -- | +0.73 |
| components clipping at either bound on that cohort | few | **0 of 39** |
| agreement at the extremes | -- | ranks the 5/5 branch 1st and the 2/5 branch last |

The deterministic proxy tracks the judge's maintainability call about as well as the judge's own headline number does, and it destroys no information via the clamps on the validation cohort. It is computed by feeding the branches' raw AST metrics through the shipped `structure.structural_score()`, so the number validates the code path rather than a reimplementation.

That "destroys no information" result is scoped to the 13-branch validation cohort; it does not carry over to the live data. On the 219-record live cohort, 35 of 273 scored components clip at either bound -- roughly 20% of scored records saturate at least one component. That is a property of the design, not a defect discovered late: the `decomposition` ramp's ceiling at 18 functions is a deliberate anti-gaming choice (see the structural-gaming limitation below), not an oversight, so some saturation at that bound is expected on a large, varied cohort. It simply means the 0-of-39 validation-cohort result above should not be read as "the clamps never bind in practice."

The calibration points are round **external** norms -- 100-line functions and cyclomatic 15 are the conventional "refactor this" thresholds in common linter defaults; 3 top-level functions reads as monolithic and 18 as generously decomposed. They were not fitted to the validation set; fitting them would make +0.72 a property of curve-fitting rather than of the metrics.

### Measurement scope: `new_files_only`

**This was wrong in the first implementation and was caught by measuring it.** The formula was validated on Task 001's `merger_rate.py` -- a module the model wrote in full. Applied to a task whose deliverable is a small additive change to a large frozen module, the AST metrics describe the substrate, not the submission:

Ranges below are per-trial (min-max) ranges, measured over all 219 records -- not per-model means. The two "modified" rows are necessarily measured under the original `all_deliverables` scope, since that is the scope being rejected; the two "new" rows are quoted under the `new_files_only` scope now in force. For reference, the per-model-mean ranges are **45.3 pts** (Task 001) and **56.9 pts** (Task 002).

| task | scored deliverable | per-trial structural range |
|---|---|---|
| 001-merger-rate-feature | `src/merger_rate.py` -- **new** | 57.7 pts |
| 002-pair-binning-convention | `src/pair_binning.py` -- **new** | 65.8 pts |
| 003-pair-finder-validation | `src/pair_finder.py` -- modified | 45.6 pts per-trial; uniformly depressed on a per-model-mean basis (45-72) |
| 005-scope-temptation | `src/calc.py` -- modified | **0.0 pts -- an identical 68.9 for all 42 trials across all 16 models** |

Task 005 contributed a pure constant. Worse, because the per-task baselines differ so much, any model with partial task coverage got an inflated mean: `opencode-go/minimax-m3` held the cohort's **highest** structural score purely because it had never run the two low-baseline tasks.

`structure.scope: new_files_only` restricts scoring to deliverables that did not exist at the trial's baseline commit -- determined mechanically by comparing against that baseline commit (independent of which source the post-image itself comes from -- see below), so a new task needs no policy edit. Three consequences worth stating:

1. It is *exactly* the footing the +0.72 validation was measured on. For a brand-new module, "new files only" and "whole post-image" are the same measurement, so the frozen formula's validation carries over unchanged.
2. It **improved** Task 001's discrimination from 23.3 to **57.7 pts**, because the score is no longer diluted by a barely-changed `config.py` and `calc.py`.
3. The cost is stated honestly: structural quality is measured only where a model authored a whole module. Tasks 003, 004 and 005 return `not_applicable` with a **null** score, never a fabricated 0 -- 0 would read as "measured, and bad".

As a safety net for future partial batches, `profile_view.py` withholds a model's structural mean unless the model covers *every* structure-eligible task, mirroring the rule `aggregate.py`'s `full_pass_duration_and_tokens` already applies to incomplete task coverage. Nothing is withheld today: all 16 models cover both eligible tasks.

### The second score earns its column

Structure vs mutation kill rate across 16 models: **rho +0.215**. Near-independent -- had they correlated strongly the column would be redundant. The disagreements are the argument for the whole design:

| model | structure rank | mutation rank | reading |
|---|---|---|---|
| `gpt-5.6-terra` | **1st** (90.5) | **13th** (68%) | best-structured code in the cohort, near-weakest tests; 15/15 gate, 15/15 lint-clean |
| `gpt-5.6-luna` | 3rd (83.2) | **16th** (34%) | well-structured, and 9 of 15 submissions incomplete |
| `opencode-go/mimo-v2.5-pro` | 15th (48.2) | 6th (76%) | the converse |

The composite averaged `gpt-5.6-terra` into "5th, unremarkable". The profile says what it actually is.

## Reliability

Derived only from fields that exist on a graded record -- no classification is invented that cannot be computed:

```text
timed_out                      -> timed_out
else no diff / no_submission   -> no_submission
else gate_status == "failed"   -> gate_failed
else missing_deliverables      -> incomplete
else                           -> completed
```

The proposal's `looped` / `faked` / `confirmed-technical-failure` states are **not** implemented: they are not derivable from the record, and `HANDOFF.md`'s long-standing systematic-technical-failure rule remains the open item that would supply them. This column immediately earns its place anyway: `gpt-5.6-luna` passes the correctness gate 15/15 while completing only **6 of 15** submissions, a fact the composite reported as nothing more than a low score.

## Mode 2 becomes first-class

`eval/harness/branch_check.py` is promoted from `archive/2026-09-07-pm-branch-transplant/` with its import bootstrap removed, a full account of the two-mode design in its docstring, and two checks the experiment performed once by hand now performed on every run:

- `check_frozen_unchanged()` compares every path the task declares `frozen_unchanged` between the named branch tip and this repo's own baseline, byte for byte. Substrate identity was verified once, by hand, for one pairing of checkouts; `--repo` accepts any checkout, and a task's `frozen_unchanged` list can grow. A mismatch is a loud warning recorded in the manifest, not an abort -- an operator needs to see and weigh it, not have a gradeable run refused.
- `check_installed_python_parses()` surfaces a garbled or truncated `git show` at install time rather than as a wall of pytest collection errors minutes into grading.

Records keep `harness="none"` and `model="pmbranch/<slug>"`, which is what `aggregate.py`'s `load_records` and `profile_view.py` both filter on to keep a PM-branch grade out of every leaderboard cohort.

## Cost, checked rather than asserted

**The screen can be one task.** Ranking models by Task 001's mutation kill rate alone versus by all five tasks: **rho +0.927** over the 14 complete-coverage models (+0.895 over all 16), with every disagreement confined to adjacent ranks. That substantiates the proposal's ~5x reduction in Mac Studio time per local model (≈4.5h for one task x 3 attempts, versus 15-25h for five) on this repo's own data, rather than on the composite comparison the proposal used. No new code is needed for it: `run_batch.py --task 001-merger-rate-feature --trials 3` already *is* the Mode 1 screen.

**No re-grading.** The original commit added 10 files and modified 7 (including `aggregate.py`, for the shared `group_and_order()` extraction) -- a subsequent code-review fix pass touched `grade_trial.py` and `run_trial.py` too (see docs/DESIGN.md's History), and none of that touches grading policy: `eval/rubric.yaml`, every `eval/tasks/*/meta.yaml`, the hidden tests, and the mutation banks remain byte-unchanged throughout, and `eval/leaderboard.md` regenerates byte-identically after every change. All 219 existing records stay in-cohort and valid, which is the proposal's headline cost claim, verified rather than assumed. Put precisely: no task contract, grader *behavior*, or existing graded record has changed -- `grade_trial.py` gained two new fields (`staged_tree_sha`, an optional `mode2_provenance` block) that a Mode 1 trial's score does not depend on.

**No model calls in the new reporting path -- distinct from the unchanged grader, which still does.** `structure.py sweep` and `profile_view.py` replace a judge invocation with an AST walk and make zero model calls; the full sweep over all 219 records takes ~26s. `grade_trial.py` itself is unmodified in this respect: it still invokes the configured judge model for the two judged categories on every trial it grades, in both Mode 1 and Mode 2. The profile view simply does not read those two categories into any of its columns.

### Why the profile policy is not in `rubric.yaml`

`grade_trial.py` hashes `rubric.yaml`'s bytes into `provenance.rubric_sha256`, and `aggregate.py`'s `cohort_key()` partitions on it. A byte change there -- even a comment -- would fork every future cohort away from the existing 219 records, destroying exactly the property above. The profile policy therefore lives in a **new** `eval/profile.yaml` that `grade_trial.py` never reads. This is the same reasoning that moved per-task leaderboard prose out of `meta.yaml` into `eval/leaderboard_summaries.yaml` after that mistake was made for real on 2026-09-07.

## Resolving a submission's post-image: live worktree first, archived patch as fallback

The structural sweep needs each submission's post-image. The first implementation read it only from `archive/worktrees/<run_id>/submission.patch` -- which was a real gap for a fresh end-to-end run: neither `run_trial.py` nor `run_batch.py` archives anything (archiving is a separate `worktree_lifecycle.py archive` step, and this repo deliberately leaves trial worktrees on disk afterwards so a completed run can be re-graded under a different scoring scheme). So a freshly graded trial had a live worktree and no archived patch, and got `missing_patch` with a blank Structure column -- silently.

`structure.py` now resolves the post-image in this order:

1. **Live trial worktree** -- `manifest.worktree_path` if it exists, else the conventional `eval/results/tmp/worktrees/<run_id>`; the file is read directly. This is strictly safer than reconstructing, because the worktree IS the graded artifact -- nothing to verify against. The mutation gate cannot have disturbed it: mutations monkey-patch already-imported modules at run time via `sitecustomize.py` and never rewrite source.
2. **Archived `submission.patch`** -- reconstructed as before (pre-image from the baseline commit into a temporary directory, then `git apply --include=<path>` on top -- `git apply` works against a plain directory tree, so no repo is needed), and blob-verified against the patch's `index <old>..<new>` post-image sha via `git hash-object` of the reconstructed file.

So the structural score is now computable at every point in a worktree's lifecycle: fresh trial (worktree only), archived-but-kept (both -- the operator's current re-evaluation workflow), and pruned (patch only -- and `worktree_lifecycle.py prune` already refuses to run without archived evidence, so the patch is guaranteed to exist by then).

A new `--source {auto,worktree,patch}` flag on `structure.py sweep` selects which of these `auto` uses. `auto` is the default and the only value normal use needs. The two pinned values exist so the paths can be **audited against each other**, and so a cohort can be re-derived purely from archived evidence. Each record in `eval/results/structure.json` now carries a `source` field (`"worktree"` or `"patch"`), and `_meta` carries `source_preference`. The failure status was renamed `missing_patch` -> `missing_submission`, since a patch is no longer the only source.

Current `auto` sweep over the 219 records:

| sweep result | value |
|---|---|
| records processed | 219 |
| scored (`ok`) | 91 |
| `not_applicable` | 128 |
| `missing_submission` / `apply_failed` / `parse_error` | **0** |
| sourced from live worktree | 12 |
| sourced from archived patch | 165 |
| blob verification | 85 verified / 0 mismatch / 6 not-checked |

(The one record that used to be `missing_patch` is now correctly `not_applicable`: that record's Task 003 deliverable existed at baseline. The 6 not-checked entries are the worktree-sourced ones, which have nothing to verify against -- the worktree IS the graded artifact.)

**The `--source` audit was run and passed.** Sweeping the same 219 records `--source patch` and `--source worktree` produces byte-identical metrics and scores for all 6 records both sources can reach (0 score differences, 0 metric differences). `--source patch` alone reproduces the original patch-only result exactly: 91 scored, 91/91 blob-verified, 0 mismatches.

Before the `new_files_only` scope narrowed what is measured, the same sweep verified **313 of 313** reconstructed files byte-exact. The reconstruction is proven, not believed.

## Step 4: the plan rewrite

`relative-velocity`'s `docs/MERGER_RATE_PLAN-2SLICE.md` is a **new file**; `MERGER_RATE_PLAN-REVISED.md` is byte-unchanged. That matters because reports 02, 03 and 04 cite the revised plan's digest (`e03093ed` / `9ce92e7c`) and `model-eval-00-index.md` states that rankings are only valid within a report precisely because plan versions differ. Editing it in place would have silently broken three reports' reproducibility. A new suffixed file also matches that repo's own convention.

| check | result |
|---|---|
| original acceptance criteria dropped | **0 of 39** |
| criteria added | exactly **1** |
| 2026-08-03 binding-note amendments | byte-identical; only the mandated "Slices 1-2" -> "Slice 1" renumbering |
| slices | 3 -> 2 (Slices 1+2 merged; Slice 3 kept intact as Slice 2) |

The merge follows finding 7: Slice 1 and Slice 2 rank-correlate at **rho +0.68** (both dominated by input-validation guard-writing -- 40 of their 57 mutations), while Slices 1+2 versus Slice 3 correlate at **rho +0.03**. Merging the duplicated pair removes one full PM cycle per Mode 2 run without losing either capability axis. The one added criterion closes the property whose mutation survived in 10 of 12 PM branches, which report 04 §7.8 asked for by name: `run_merger_rate_validation`'s `expected_slope` must provably track a **non-default** `merger_timescale_alpha`.

## What is *not* done, and what remains open

- **Step 5's fresh Mode 2 run.** A supervised PM run costs 1h13m to 20h of operator attention. The grading path is validated -- `branch_check.py` grades a PM branch through the same kernel, and finding 6's capability-vs-delivered delta is reproducible from `archive/2026-09-07-pm-branch-transplant/rv04-report04-branches.bundle` plus the one-shot records. A fresh run adds a data point on the rewritten 2-slice plan; it does not further validate the instrument. **Operator's call.**
- **`composite_score` and the judged categories are still computed by `grade_trial.py`.** Deliberately: the proposal reserves "replacing `main`" for after step 5, and its own open decision #1 endorses keeping the judged categories recorded for one more batch while scoring on the deterministic columns. The profile view is the new primary artifact; retiring the composite from the grader is a separate, operator-owned step.
- **Saturation above the ceiling is not solved**, and this work does not claim to solve it. It makes the measurement cheaper, more honest and extensible. Real discrimination above the current ceiling needs a categorically different task shape -- debugging with no location hint, or an enforced performance budget -- which is `docs/DESIGN.md`'s next task-backlog item.
- **The systematic technical-failure rule remains open** and is what the reliability column's unimplemented states depend on.
- **Structural gaming is a documented limitation**: `function_count` is inflatable by splitting one function into trivial wrappers. Saturating at 18 bounds the damage but does not detect it. No metric in the finding-5 sweep closed this gap.
- **The decomposition metric counts only module-level functions.** A submission that factors its work into a class instead of top-level functions scores `function_count` near zero, and is penalised or unmeasurable regardless of how well-decomposed its methods are. The exclusion is deliberate and documented in the code, but the n=13 validation cohort contained no class-based submission, so this path was never exercised. If it ever bites, the fix is to count methods of module-level classes toward `function_count` and re-derive the validation, not to patch around it ad hoc.
- **The structural validation is n=13** against labels assigned by a single AI reader, and report 04 §9 disowns its own middle ranks. +0.72 on 13 points is suggestive, not settled.

## Reproducing every number above

```bash
python eval/harness/structure.py sweep     # -> eval/results/structure.json  (~26s)
python eval/harness/structure.py sweep --source patch   # audit: pin the archived-patch path
python eval/harness/profile_view.py        # -> eval/profile.md
python eval/harness/aggregate.py           # -> eval/leaderboard.md (unchanged by this work)
python -m pytest tests/ -q                                  # 80 passed
cd eval/harness && python -m pytest -q                      # 177 passed (2026-09-08 code-review fix pass)
```
