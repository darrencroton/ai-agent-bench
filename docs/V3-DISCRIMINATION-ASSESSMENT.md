# Discrimination assessment: does the v2 rubric spread models the way we need it to?

**Superseded (2026-09-07):** largely superseded in direction by `docs/EVAL-CONSOLIDATION-PROPOSAL.md` and `docs/EVAL-CONSOLIDATION-TRIAL.md`. This document's diagnosis -- correctness saturates and the composite compresses as a result -- was correct and is now independently confirmed on the full 219-trial dataset. Its proposed remedy, reweighting the composite, is superseded by deleting the composite outright: there is nothing to reweight once averaging five saturated signals against one discriminating one stops happening at all. Every number below was computed against 90 trials; the dataset is now 219. One item survives independently of all of this: the systematic technical-failure classification rule this document first called for remains open and is not addressed by the consolidation work. Nothing below has been rewritten or removed -- it stands as the historical record of the diagnosis.

**Date:** 2026-09-06

**Status:** exploratory -- nothing here is decided or implemented. This captures a discussion, and the evidence gathered during it, from the first real multi-tier trial batch under rubric v2 (weak-tier frontier models plus a local and a subscription model). It exists so a fresh session can pick up v3 planning with full context instead of re-deriving it. Do not treat any weight number below as final -- they are illustrative candidates computed against a partial, still-growing dataset.

**Update (end of fifth session, 2026-09-06):** all batches referenced below have now finished, plus two more added specifically to widen the tier spread -- a strong frontier anchor (`gpt-5.6-terra`, `codex`, effort `high`) and an additional cloud model (`opencode-go/hy3`, `opencode`). `eval/leaderboard.md` now holds 90 graded trials (not the 50 this document's numbers were computed against) across all 6 models. Skimming the regenerated leaderboard: the compression problem persists with real strong-frontier data in hand -- `gpt-5.6-terra` composite 88.2 sits close to the subscription/local tier (88.7-91.7) and only modestly above weak frontier (75.6-79.3), which is consistent with this document's saturation diagnosis rather than contradicting it, but every specific number and simulation below (the 15.6 range, the four-model table, `ornith`'s n=7) still needs recomputing against the full 90-trial dataset before being trusted -- that recomputation was not done as part of this closeout and is the fresh session's first task, per `HANDOFF.md`.

**Scope:** whether the current five-task bank and v2 rubric produce enough score spread to usefully rank models from weak to strong, what's causing the compression actually observed, and what (rubric reweighting, a new deterministic code-quality category, new task types) would fix it.

## Decision question

The user's framing, verbatim in spirit: *weak frontier models are scoring 70-80 and a strong local model is scoring ~85-87. That's too compressed -- weak frontier should read closer to 60, strong frontier closer to 80, with room below and around that for local and subscription models of varying quality. Is this a rubric-weighting problem we can fix by reweighting/ renormalizing, or have we built tasks that saturate for any competent model regardless of real ability?*

## Executive summary

**It's a task/rubric ceiling problem, not a normalization problem, and the evidence is unusually direct: `correctness` is 88-100% for every model tested so far, on every task, including Task 002 -- the one task in the bank explicitly built to require a genuine design decision rather than formula transcription.** Since `correctness` carries 40 of the rubric's 100 points (the `default` profile's largest single category), an almost-constant ~36-40 points land in every model's composite regardless of real ability differences at this tier, which mechanically compresses the whole distribution upward and narrow. `test_adequacy` (25 points) is the one category currently doing real discriminating work, spanning 0-100%.

Population-relative renormalization (z-scores/percentiles against whichever models happen to be in the cohort) was considered and rejected as the primary fix: it doesn't touch the actual cause, makes a graded record's score depend on who else is in the population at aggregation time (breaking this repo's "every record is self-contained and reproducible" principle), and at n=3 trials/cell would amplify small, possibly-noisy real differences into large rank swings.

Recommended direction instead, both retroactively testable against data already collected:

1. **Reweight**, shifting points off saturated `correctness` onto `test_adequacy` (already discriminating). A simulated candidate widened the observed model range from 15.6 to ~23 points on the exact same 50 trials -- see "Reweighting simulation" below.
2. **Add a deterministic code-quality category**, sourced from the `code-health` skill's underlying analyzer script (not its judgment workflow -- see "Code-health integration" below), to give KISS/DRY a real measured signal instead of riding entirely on a subjective, same-family- biased judge call.
3. **Prioritize task types that can't saturate the way Task 002 did** -- debugging/root-cause first, performance-at-scale second -- because the evidence now shows that "add another somewhat-open design-decision task" (which is what Task 002 already was) did not fix the ceiling. The fix needs categorically different difficulty, not just less pinning.

A second, unrelated but consequential finding surfaced during this same session: **two trials were confirmed technical failures (a provider-side output-token ceiling truncating the model's response mid-turn, not a model capability failure) and were incorrectly averaged in as zero-quality attempts.** They've been archived out of the primary results (`archive/2026-09-06-deepseek-truncation-technical-failures/`) and replaced with fresh trials. This exposed a real gap in the v2 scoring philosophy that should be closed systematically in v3 -- see "Technical failures vs genuine model failures" below.

---

## Evidence: correctness is saturated across every model tested so far

Every trial that produced a genuine submission (i.e. excluding the two confirmed technical failures discussed below), across all four model/harness combinations run in this session's weak-tier and local/cloud batches:

| Task | `claude-haiku-4-5` (weak frontier) | `gpt-5.6-luna` (weak frontier) | `ornith-1.5-397b-q6` (local) | `deepseek-v4-flash` (subscription) |
|---|---|---|---|---|
| 001 (feature) | 88% | 96% | 97% | 96-100%* |
| 002 (design decision) | 95% | 98% | 100% | 98% |
| 003 (validation) | 100% | 100% | 100% | 100%* |
| 004 (test-authoring, gated) | 100% | 100% | -- | 100% |
| 005 (scope temptation) | 100% | 100% | -- | 100% |

*Task 001 and 003 deepseek figures shown are from genuine (non-truncated) trials only; see the technical-failures section for why the raw leaderboard average looked much lower (65-67%) before that correction.

No model, on any task, scored below 88% correctness. **Task 002 -- built specifically per `docs/DESIGN.md` backlog item 1 to require a genuine design decision (deriving the pair-fraction denominator from three stated invariant properties, rather than being handed a formula) -- saturates exactly like the heavily-pinned Task 001.** That is the single most important data point in this assessment: the bank's one deliberate attempt to fix formula-transcription-driven saturation did not fix it. The difficulty needs to come from somewhere categorically different (diagnosis under ambiguity with no location hint, or a hard performance constraint), not from "less pinning in the spec."

By contrast, `test_adequacy` (mutation-kill rate) spans the full range observed across these same trials: 0% (`gpt-5.6-luna`, which consistently never writes the required test file on Tasks 001-003 -- confirmed as genuine, consistent model behavior via clean `turn.completed` transcripts, not a harness fault) up to 97-100% (`ornith-1.5-397b-q6` on Task 003, `deepseek-v4-flash` on Task 004). This is the category actually telling models apart today.

## Technical failures vs genuine model failures

During this session's local/cloud batch, one `deepseek-v4-flash` trial scored 0.0 with `no_submission: true`. Transcript inspection showed the model behaving normally throughout (read `TASK.md`, explored the repo, confirmed the baseline suite passed), then beginning to write its implementation -- at which point the `opencode-go` provider's response was cut off mid-turn: the final `step_finish` event recorded `"reason": "length"` at exactly 32000 output tokens, `exit_code: 0`, zero changed files. A second, independent occurrence of the identical pattern was found on a different task in the same batch. Both trials' sibling attempts (same task, same model, different trial index) completed normally and scored 87-100%.

This is a provider-side per-turn output-token ceiling, not evidence about the model's coding ability. Both trials were archived (`archive/2026-09-06-deepseek-truncation-technical-failures/`, with a full writeup of the evidence and reasoning in that directory's `README.md`) and replaced with fresh trials (new run ids -- **not** a re-prompt of the same trial, which would have violated the one-shot rule) to restore n=3 genuine attempts per cell.

**This is a real tension in the v2 philosophy, not just an isolated fix.** `README.md` states: *"A trial that timed out or produced no diff at all scores 0 in every category rather than being silently dropped -- an unsupervised model that can't finish is a real result, not a data-collection failure."* That principle was written to stop a **model's own** inability to finish from being laundered out of the aggregate, and it should stay exactly as strict for that case. It was not written with a **harness/provider** fault in mind, and conflating the two punishes a model for its infrastructure rather than its ability -- which is precisely what happened here before the archival correction (it dragged `deepseek-v4-flash`'s measured Task 001/003 correctness down to 65-67% when its real correctness, every time it actually got to submit, was 96-100%).

**Recommended forward work for v3 (not yet implemented):** make the distinction systematic in `grade_trial.py` rather than requiring an operator to notice it by hand each time. A concrete rule that preserves both principles: a `no_submission` trial is scored zero and retained by default (the existing behavior, unchanged); it is only reclassified as a technical failure -- archived, and replaced with a fresh trial -- when there is **positive transcript evidence** of a harness/provider fault (a truncation `step_finish` reason, a non-2xx/5xx transport error, a harness-level crash with a nonzero `run_trial_returncode` that isn't attributable to the model's own output) rather than merely a suspicion. A trial where the model itself gave up, looped, or ran out of its own budget must still score zero and stay in the aggregate -- that is a real result. The bar is **confirmed** technical fault, never **inconclusive** ones (a genuinely ambiguous case stays scored as-is, since the burden of proof for excluding data must sit higher than the burden for including it).

## Reweighting simulation (against data already collected -- no rubric.yaml changes made)

Ran three weight schemes against the 50 genuine graded trials (after archiving the two technical failures), macro-averaged per model exactly as `aggregate.py`'s own "Model summary" table does:

| Scheme | correctness | test_adequacy | scope | hygiene | readability | maintainability | code_quality |
|---|---|---|---|---|---|---|---|
| v2 (current, `default` profile) | 40 | 25 | 10 | 10 | 8 | 7 | -- |
| Candidate A | 25 | 40 | 10 | 10 | 8 | 7 | -- |
| Candidate B (illustrative only -- see caveat) | 20 | 35 | 10 | 8 | 7 | 5 | 15 |

| Model | n | v2 (current) | Candidate A | Candidate B |
|---|---|---|---|---|
| `gpt-5.6-luna` (weak frontier, codex) | 15 | 75.6 | 66.1 | 65.7 |
| `claude-haiku-4-5-20251001` (weak frontier, claude) | 15 | 79.3 | 74.5 | 75.0 |
| `opencode-go/deepseek-v4-flash` (subscription) | 13 | 91.2 | 88.9 | 89.1 |
| `macstudio/ornith/ornith-1.5-397b-q6` (local) | 7 | 87.0 | 82.8 | 82.8 |

| | v2 current | Candidate A | Candidate B |
|---|---|---|---|
| Range (max - min) across models | 15.6 | 22.8 | 23.4 |

**Caveats, both material:**

- `ornith-1.5-397b-q6`'s n=7 is incomplete (Tasks 004/005 hadn't finished running as of this simulation) -- its mean will move once the batch completes, and should not yet be treated as a settled number.
- **Candidate B's `code_quality` column carries no real per-trial score yet** -- none of the 50 records has a measured code-quality signal, so the simulator silently renormalized over the other six categories for every trial. Candidate B's near-identical numbers to Candidate A are an artifact of that gap, not evidence that adding code_quality is a no-op. See the next section for what integrating it for real would take.

The clear, trustworthy finding from this simulation: shifting weight from saturated `correctness` to discriminating `test_adequacy` widens the observed range by roughly 50% (15.6 -> ~23 points) using only data already in hand, and correctly demotes `gpt-5.6-luna` (which reliably skips writing tests) below `claude-haiku` -- a reordering that better reflects a real, confirmed behavioral gap rather than being drowned out by near-ceiling correctness.

## Code-health integration: use the fact engine, not the judgment workflow

The `code-health` skill (`~/.claude/skills/code-health`, symlinked from `ai-agent-coder`) was evaluated as the source for a deterministic KISS/DRY signal, as an alternative to writing a duplication/complexity detector from scratch.

**Its own design explicitly refuses to produce a score:** *"No score or universal target... never emits an `unhealthy` verdict"* -- it hands an agent raw facts (exact-window duplication with occurrence counts, Python-AST cyclomatic complexity distributions, LOC composition) and requires human/agent judgment to turn those into a verdict. That's incompatible with this repo's requirement that grading be fully automated and repeatable with no interpretive step in the loop.

**Recommendation: call its underlying script directly, skip its skill workflow.** `scripts/health.py analyze --base <ref> --json` is a genuine, reusable fact engine -- deterministic exact-window duplication detection and stdlib-AST cyclomatic complexity, with disclosed limits, no external dependency needed for a pure-Python repo like this one (Lizard is only needed for multi-language coverage). Reuse that; write our own thin, versioned scoring formula on top of its facts (which is exactly the judgment layer the skill deliberately does not provide).

### Real spot-check data (Task 001, one trial per model, plus the reference solution)

`src/merger_rate.py` specifically (the one substantial file every submission actually wrote, so comparable apples-to-apples -- unlike a whole-diff LOC comparison, which is confounded whenever a model skipped a required deliverable):

| Submission | code lines | vs. reference ratio | functions | mean cyclomatic | max cyclomatic |
|---|---|---|---|---|---|
| `reference_solution/` | 236 | 1.00x | 11 | 4.09 | 8 |
| `ornith-1.5-397b-q6` (local, best composite) | 391 | 1.66x | 11 | 3.73 | 8 |
| `claude-haiku-4-5` (weak frontier) | 458 | 1.94x | 10 | 3.10 | 5 |
| `gpt-5.6-luna` (weak frontier) | 101 | 0.43x | 11 | 4.36 | 9 |
| `deepseek-v4-flash` (subscription) | 348 | 1.47x | 11 | 2.73 | 6 |

This one-task, one-trial-per-model spot check (not yet a full-population measurement) already shows real, meaningful spread that correctness and test_adequacy don't capture on their own:

- `gpt-5.6-luna` is by far the shortest (0.43x reference) **and** has the highest complexity per function (mean 4.36, max 9, both above the reference's own numbers) -- a compact-but-dense signature, not a genuinely simple one. LOC alone would have called this the "leanest" submission; complexity-per-function correctly flags it as cramped rather than clean.
- `claude-haiku` is the longest (1.94x reference) but has the *lowest* complexity (mean 3.10, max 5) of any submission -- verbose/boilerplate- heavy rather than logically tangled. A pure complexity metric would have missed this; LOC-ratio catches it.
- `deepseek-v4-flash` has both a reasonable LOC ratio (1.47x) and the lowest mean complexity of all four (2.73, below even the reference's 4.09) -- the cleanest structural profile in this sample, consistent with its strong composite scores elsewhere.

**This confirms the earlier conceptual conclusion: LOC alone is not a sufficient KISS signal** (it would have rewarded `gpt-5.6-luna`'s dense, high-complexity code as "most concise"). **A code-quality category needs both signals** -- LOC-ratio-vs-reference and complexity-ratio-vs-reference -- not either alone, and both must be normalized against `reference_solution` (which exists for all 5 tasks already) rather than an absolute threshold, since different tasks legitimately need different amounts of code (Task 003's rejection matrix needs real line count; a shorter reference doesn't).

### Recommended weight allocation (illustrative, not final)

A draft v3 `default`-profile weight table that funds a new `code_quality` category primarily from saturated `correctness` (which can afford to lose weight without losing real discriminating power) and partly from judged `maintainability` (whose job code_quality would partly subsume):

| Category | v2 (current) | v3 draft |
|---|---|---|
| `correctness` | 40 | 25 |
| `test_adequacy` | 25 | 35 |
| `code_quality` (new, deterministic) | -- | 10 |
| `scope_discipline` | 10 | 10 |
| `hygiene` | 10 | 8 |
| `readability` (judged) | 8 | 7 |
| `maintainability` (judged) | 7 | 5 |

This keeps `correctness` + `test_adequacy` dominant (60 of 100 points, still clearly primary, matching the user's own framing that KISS/DRY should be a **secondary/tie-breaking signal for equivalently-correct code**, never a way to let a broken-but-terse submission outscore a correct one) while giving deterministic quality signal real weight (18 points across `code_quality` + `hygiene`) and trimming the judged share to 12 points, appropriately reduced now that part of what judged `maintainability` was guessing at (DRY, function size) has a measured alternative.

The `test_authoring` profile (Task 004 only) would need an analogous, smaller adjustment since it has no `correctness` weight to draw from -- likely funding a smaller `code_quality` slot from its own `maintainability`/ `hygiene` share instead. Not worked out in detail here; flagged as an open item.

**Not yet done, and required before this can become a real v3 proposal:** run `health.py` across every surviving trial worktree (all ~50+, all 5 tasks) to get population-scale code_quality numbers, not a four-model, one-task spot check; then define the exact scoring formula (how LOC-ratio and complexity-ratio combine into one 0-100 value) and validate it doesn't produce perverse incentives (e.g. confirm it can't be gamed by artificially padding or shrinking code without changing real structure).

## Task-gap analysis: which proposed extension actually fixes this?

Three task extensions are already proposed (`docs/DESIGN.md` backlog items 6-8, `HANDOFF.md`'s Forward Work List has the fuller sketch of each): debugging/root-cause, performance-at-scale, and a larger multi-module task (already deprioritized for an unrelated reason -- this repo's expected real usage is `scoped-implementation`-shaped, narrow bounded slices, where a cross-module task matters less by construction).

Assessed against **this session's specific finding** (correctness saturates even on the bank's one deliberate "harder, less-pinned" task):

1. **Debugging/root-cause -- highest priority, and now for a stronger reason than before.** Given a real, reproducible wrong-output or crash bug with no location hint, a model must diagnose from symptom to cause. There is no formula to transcribe and no invariant properties handed to it the way Task 002 hands D1-D3 -- the difficulty is categorically different from every current task, which is exactly what's needed since "less pinning within the same spec-driven shape" (Task 002's approach) already proved insufficient. A weak model can genuinely fail to find the fault at all; correctness would not be pre-saturated the way it is today.
2. **Performance-at-scale -- second priority, complementary rather than redundant.** Adds a wholly new axis (efficiency under an enforced wall-clock/memory budget) that nothing today measures at all, separate from "does it produce the right answer." A model can pass every hidden test today with an accidentally-quadratic implementation and lose nothing for it. Real value, but adds harness complexity of its own (host- independent, reproducible timing).
3. **Multi-module -- still lowest priority, now for two independent reasons.** The original scoped-implementation-framing rationale still stands, and this session's evidence adds a second: a multi-module task built in the same spec-driven style as Tasks 001/002 would likely saturate correctness the same way unless deliberately built to require genuine cross-file design tension -- which is a much harder task to design well than debugging or performance, and lower expected value per unit of authoring effort.

**No new task type beyond these three is recommended by this analysis.** The temptation to instead build "another Task 002" (a further design-decision task, just less pinned) is explicitly not recommended -- that is the approach already tried, and the data now shows it did not solve the saturation problem. The fix needs categorically different task shape (diagnosis under ambiguity, or a hard performance constraint), not merely a softer specification of the same shape.

## Open items for whoever picks this up next

1. Finish running the local/cloud batch (`ornith-1.5-397b-q6`'s Tasks 004/005 were still pending as of this writeup) and fold the two replacement `deepseek-v4-flash` trials in once graded, before treating any of the numbers above as settled.
2. Run the planned wider model-tier sweep (a genuinely weak local model, and eventually a strong frontier anchor) -- this whole assessment is built on four models clustered in a fairly narrow real-ability band; the reweight and code-quality proposals need validating against a wider spread before being trusted.
3. Run `health.py` at population scale (every surviving trial worktree, all 5 tasks) to replace the four-model, one-task spot check with real coverage, and define the exact `code_quality` scoring formula.
4. Decide and implement the systematic technical-failure-vs-genuine-failure rule in `grade_trial.py` (see that section above) rather than relying on an operator noticing by hand each time.
5. Work out the `test_authoring` profile's analogous weight adjustment for Task 004.
6. Only after 1-5: draft the actual v3 `rubric.yaml` diff, bump `version`, and follow the existing archival convention for any batch that becomes incomparable under it -- per this repo's own rule, rubric changes are versioned data, never silently applied retroactively to already-graded records.
7. Author the debugging/root-cause task first (see priority ranking above), then performance-at-scale, before revisiting whether a v3 rubric change alone was sufficient or whether new task types were the load-bearing fix.
