# Task-bank and scoring-redesign assessment

**Date:** 2026-09-05

**Status:** recommendation for team decision and fresh implementation

**Scope:** the five-task assessment bank, grading rubric, grader, aggregation, and diagnostic weak-tier evidence

## Decision question

Is the current five-task benchmark fit to compare LLM-and-harness combinations for scientific coding, from weak local models to strong frontier models, and what—if anything—should change before more model trials are run?

## Executive summary

The benchmark is a strong foundation and should not be broadly redesigned. Its one-shot protocol, task contracts, hidden-test isolation, reference solutions, mutation banks, and adversarial controls are unusually rigorous. Tasks 001–003 should remain unchanged, Task 004's mutation instrument should be retained, and Task 005 should be tested against genuinely weak local models before its value is judged.

The main risk is not inadequate test construction. It is that several scoring rules do not faithfully represent the acceptance obligations those tests encode. The recommended response is a targeted rubric v2 before any new official batch:

1. Make Task 004 correctness a compatibility gate rather than 40 points.
2. Weight hidden-test correctness by named acceptance obligation rather than raw pytest node count.
3. Replace diff-size-relative scope scoring with fixed, classed consequences and protect mutation-credit attribution.
4. Pin and explicitly define the hygiene evaluator; remove the unsupported warning-free claim.
5. Report deterministic and judged evidence separately, retaining any composite only as a secondary summary.
6. Preserve incomplete submissions in primary aggregates while exposing completion rate.
7. Record sufficient rubric, task, grader, judge, and environment provenance in every result.
8. Keep operational telemetry outside the quality score and label cross-harness comparability limits.

This is a recommendation for **some material changes, not many**. The task bank is fit for its current role as a focused scientific-Python benchmark, but it does not yet cover all scientific-coding work. Root-cause debugging is the highest-value next task; performance-at-scale and multi-module architecture follow. Adding those tasks should wait until rubric v2 and a small three-tier calibration have established what the present five tasks actually discriminate.

There are no valid leaderboard results to migrate. The archived 30-run weak-tier batch is useful diagnostic evidence only: Tasks 001–003 subsequently received mutation-bank repairs, so its totals and adequacy denominators are superseded. This makes the current moment the least costly opportunity to replace the claimed “same fixed rubric forever” policy with explicit rubric versioning.

## Purpose and evaluation criteria

The repository evaluates a model **and its coding harness together** on a real scientific-code substrate, unattended, in one shot, without a review/fix loop. A useful benchmark for that purpose should:

- reward correct scientific behaviour, including numerical and rejection semantics;
- distinguish whether model-authored tests detect plausible defects;
- expose incomplete work, scope failures, and operational failures rather than filtering them away;
- remain fair across tasks whose tests use different parameterization styles;
- retain enough granularity to compare weak local, weak frontier, and strong frontier systems;
- be reproducible across time and evaluator environments;
- separate deterministic evidence from subjective model judgment;
- avoid changing tasks merely to manufacture a preferred score distribution.

The conclusions below were evaluated against those criteria, not against a presumption that every observed limitation must be fixed.

## Evidence base and confidence

### Primary repository evidence

- [`README.md`](../README.md) and [`docs/DESIGN.md`](DESIGN.md), including the full task and harness history.
- [`eval/rubric.yaml`](../eval/rubric.yaml), [`eval/harness/grade_trial.py`](../eval/harness/grade_trial.py), [`eval/harness/aggregate.py`](../eval/harness/aggregate.py), and [`eval/harness/judge_prompt.md`](../eval/harness/judge_prompt.md).
- All five task specifications, metadata files, hidden-test layouts, mutation registries, reference-solution documentation, and control descriptions under [`eval/tasks/`](../eval/tasks/).
- The 30 records in `archive/2026-09-04-weak-tier-r3-pre-mutation-fix/runs/`, treated as diagnostic and not leaderboard-valid.
- The current handoff record and the mutation-bank validation completed before this assessment.

Current validated mutation counts are 73, 111, 145, 53, and 33 for Tasks 001–005. Current hidden-test node counts are 61, 140, 315, 38, and 117. Reference solutions and task-specific controls have been used to validate mutation reachability and reject false or free kills; Tasks 001–003 were repaired after the archived batch.

### Independent review

Claude Opus 5 at high effort performed an independent read-only review through the orchestrator. Its overall verdict was “pass with risks”: retain the instruments and task contracts, but correct a small set of scoring-policy problems before further trials. The raw review remains in the local, gitignored `.orchestrator/runs/task3-opus-assessment-20260905-115948-62636/` directory and is not required to use this report; its material conclusions and disagreements are incorporated here so they survive a fresh clone.

The present report does not accept that review uncritically. In particular, it rejects the suggestion to exclude incomplete submissions from the primary quality mean because doing so would hide reliability failures and introduce survivorship bias.

### Confidence limits

- No genuinely weak local model or strong frontier anchor has yet run the finalized task bank.
- The archived weak-tier data predates the repaired Tasks 001–003 mutation denominators.
- Task 005 produced no scope violation in the archived tier; this is an unresolved calibration result, not proof that the task is defective.
- Judge repeatability is documented only coarsely, at roughly 1.5–3 total-score points for the same input.
- An Opus judge may also become a strong-frontier trial subject. Same-model judging is a stronger bias risk than the currently accepted same-family harness risk and needs explicit handling.

These limits argue for retaining uncertain tasks through calibration, not for prematurely redesigning them.

## Current task-bank assessment

| Task | Primary capability | Current instrument | Assessment | Recommendation |
|---|---|---:|---|---|
| 001 — merger-rate feature | Cross-file scientific implementation: counts, pair fractions, rates, fitting, persistence, configuration, and tests | 61 hidden nodes; 73 mutations | Broad, realistic, and demanding. Its long specification is justified by the need to remove scientific ambiguity in a one-shot trial. Archived runs show meaningful correctness and test-adequacy variation. | Keep unchanged. |
| 002 — pair-binning convention | Scientific reasoning under alternative conventions, invariant preservation, implementation, and explanation | 140 hidden nodes; 111 mutations | The strongest discriminator in the archived diagnostic tier. It combines conceptual choice with concrete scientific implementation and testing. | Keep unchanged. |
| 003 — pair-finder validation | Defensive numerical programming, malformed-input handling, dtype/shape semantics, and preserved behaviour | 315 hidden nodes; 145 mutations | A valuable task with deep boundary coverage. Its 315 nodes are generated by only 25 test functions and include large Cartesian case matrices, so raw-node correctness overweights some obligations. That is a grader-policy issue, not a reason to weaken the suite. | Keep the task and tests; change correctness aggregation. |
| 004 — loader test adequacy | Designing tests that detect plausible defects in correct, frozen scientific code | 38 hidden nodes; 53 mutations | The mutation instrument is excellent: the reference suite kills all mutations while weak and degenerate controls kill none or very few. Correctness is explicitly a compatibility floor, yet currently supplies 40 points. | Keep the task; make correctness a gate/N/A category and make mutation adequacy the primary measurement. Do not change difficulty before three-tier calibration. |
| 005 — provenance scope | Requirement fidelity and resistance to a nearby, real maintenance temptation | 117 hidden nodes; 33 mutations | Scientifically relevant and inexpensive. All archived trials passed correctness and scope, but no genuinely weak local model has been tried. The absence of observed scope failures is insufficient evidence to discard it. | Keep unchanged for calibration. If scope remains flat across tiers, replace it with debugging rather than making the temptation obvious. |

### Diagnostic archived results

The following figures are not valid leaderboard scores, but they show which dimensions produced variation before the Tasks 001–003 mutation repair. The repair changed only the mutation banks: the archived correctness and scope columns remain valid diagnostic evidence, while Tasks 001–003 test-adequacy fractions use superseded denominators and are included only to show coarse behavioural variation.

| Task | Trials | Total-score range | Correctness range | Test-adequacy range | Scope |
|---|---:|---:|---:|---:|---:|
| 001 | 6 | 60.1–73.0 | 0.787–0.984 | 0.000–0.706 | 1.0 in all trials |
| 002 | 6 | 64.8–88.6 | 0.879–0.993 | 0.000–0.912 | 1.0 in all trials |
| 003 | 6 | 72.0–87.1 | 0.975–1.000 | 0.000–0.763 | 1.0 in all trials |
| 004 | 6 | 92.1–97.0 | 1.000 | 0.925–1.000 | 1.0 in all trials |
| 005 | 6 | 86.4–92.5 | 1.000 | 0.667–0.818 | 1.0 in all trials |

The observed saturation in Tasks 004 and 005 establishes the need for broader-tier calibration; it does not establish that either task lacks value. A task need not discriminate every model tier to contribute useful evidence.

## Test coverage: verdict

### What is already strong

The five tasks have sufficient depth against their written contracts:

- hidden tests cover pinned numerical values, rejection behaviour, integration paths, persistence, and preserved behaviour;
- expected node IDs are collected before execution so a crash cannot shrink the correctness denominator;
- hidden tests are copied only at grading time and removed afterward;
- mutation gates credit only test nodes that passed at baseline;
- mutations are designed as one defect predicate each and are checked against reference and degenerate controls;
- frozen surfaces protect the substrate and prevent a model from rewriting the problem it was asked to solve;
- the tasks deliberately vary implementation, scientific judgment, defensive validation, test authorship, and scope discipline.

Adding more tests to the existing contracts would mostly increase density, cost, and maintenance burden. It would not address the most important coverage gaps.

### What is missing at task level

The largest missing capability is root-cause debugging: locating and repairing an existing scientific defect from symptoms and failing evidence. The current tasks primarily ask models to build or harden specified behaviour.

The next gaps are:

1. Performance and memory behaviour at scientifically realistic scale while preserving numerical equivalence.
2. A larger multi-module architectural change with more consequential dependency decisions.
3. Independent algorithm selection under accuracy, stability, and computational-cost trade-offs.

Reproducibility and scientific communication are only incidentally measured, but they are lower priority than debugging and performance for the current repository purpose. They should not become new rubric categories until a concrete task can measure them reliably.

## Recommended rubric v2

### 1. Version and provenance every result

The rubric declares `version: 1`, but graded records do not persist that version. A version that is absent from the result cannot prevent incompatible records from being aggregated.

Every graded record should persist at least:

- rubric version and rubric content hash;
- task identifier plus specification/metadata content hash or explicit contract version;
- grader and aggregator Git revision;
- baseline revision;
- judge model, harness, effort, prompt version/hash, and judge status;
- Python version, resolved evaluator dependency versions, and exact Ruff policy/version.

Aggregation should refuse or visibly partition incompatible rubric and task-contract versions. Pinning only the model name is insufficient when the evaluator dependencies remain open-ended.

**Alternative:** record only `rubric.version`. This is cheap but cannot distinguish task, grader, prompt, or dependency drift and is therefore inadequate for long-lived comparisons.

### 2. Make Task 004 correctness a gate

Recommended semantics:

- If any compatibility-floor condition fails, mark the Task 004 attempt failed and give it no successful task score.
- If the floor passes, report correctness as `N/A (gate passed)`, not `1.0` worth 40 points.
- Treat mutation adequacy as the task's primary continuous result.
- Continue to report scope, hygiene, completion, and judge evidence separately.

“Failed” has explicit score semantics here: retain the trial in aggregates with a zero Task 004 score and a failed-gate flag. Do not exclude it. This matches the existing no-submission policy and prevents unreliable systems from benefiting through survivorship bias.

Do not obtain a Task 004 score by automatically renormalizing the generic remaining categories. The grader currently skips `None` categories and renormalizes over the remaining weight, so merely setting correctness to `None` would produce this prohibited result. Removing 40 points and renormalizing the remaining 60 would make the 15 judged points worth 25% of a test-writing task. If an overall scalar is required, define an explicit test-task scoring profile in `rubric.yaml`; the profile must make mutation adequacy dominant by design rather than by accident.

**Alternative:** retain the current 40-point floor. This is mechanically simple but communicates a high score before measuring the skill the task exists to evaluate.

**Alternative:** make the entire task pass/fail. This discards the high-resolution 53-mutation instrument and is not recommended.

### 3. Score correctness by acceptance obligation

The grader currently computes correctness as passed hidden-test nodes divided by collected nodes. Pytest authoring style therefore determines rubric weight: one obligation expressed through many parameter combinations counts more than a separately bundled obligation.

Recommended hierarchical proportional method:

1. Each task declares named acceptance-obligation groups and the node patterns belonging to them.
2. Every collected hidden node must map to exactly one group; missing or duplicate mappings are grading errors.
3. Each group receives the fraction of its own nodes that pass.
4. Groups have equal weight unless a different frozen weight is explicitly justified in the rubric.
5. Correctness is the weighted mean of group fractions.

This preserves partial credit and the value of boundary matrices while ensuring that adding another parameter combination does not silently rewrite the rubric.

**Alternative:** retain raw node fractions. Simple, granular, and currently implemented, but structurally unfair across test styles.

**Alternative:** make each obligation all-or-nothing. Clear but brittle: a single boundary miss erases all partial evidence for a broad obligation.

Mutation adequacy should remain a per-mutation fraction for now. The mutation banks were deliberately repaired so that each mutation represents a distinct defect predicate; their cardinality is therefore more meaningful than pytest node cardinality.

### 4. Replace relative scope penalties and protect mutation attribution

The current scope formula is `1 - violations / changed_files`. The same unauthorized change therefore costs less in a larger authorized diff. This has no principled relationship to the severity of the violation.

Recommended policy:

- modifying protected grader inputs, hidden-test mechanisms, or frozen tests is an integrity violation that zeroes and retains the affected trial with an integrity-failure flag;
- each ordinary unauthorized file incurs a fixed penalty independent of the number of authorized files changed;
- known harness-created artifacts may be excluded only through explicit, narrow patterns, extending rather than replacing the existing `HARNESS_ARTIFACTS_PATHSPEC` mechanism;
- details must list every violating path and its class.

A starting policy of losing 0.5 scope fraction per ordinary unauthorized file is simple and auditable, although the team should freeze the exact value before implementation. A binary clean/not-clean score is also defensible and simpler, but treats a stray file and a substantive unauthorized refactor identically.

Mutation credit should be attributable only to the task-authorized model-authored test path or paths. The complete frozen suite should continue to run as a regression check, but a frozen or unrelated test must not earn mutation credit. This generalizes the task-specific freebie controls into an enforceable grader invariant.

### 5. Make hygiene deterministic and accurately described

The current rubric says hygiene covers a warning-free model suite, but ordinary pytest warnings do not change `passed_clean`. The evaluator also invokes whichever compatible Ruff version and default configuration happen to be installed, and the differential overlap logic can re-admit a pre-existing multiline finding when only a later line is changed.

Recommended changes:

- pin the exact Ruff version used for official grading;
- run an explicit isolated ruleset owned by the repository;
- define differential attribution by the finding's primary/start location or another stable rule, not any span overlap;
- remove the warning-free claim from rubric v2;
- retain own-suite baseline status and outside-root portability as separately reported deterministic evidence.

Do not score ordinary warnings yet. Scientific Python environments often emit third-party and version-dependent warnings, and a reliable submission-attribution mechanism would cost more complexity than current evidence justifies.

### 6. Preserve incomplete submissions in the evidence

When a task requires model-authored tests and none are written, the result should say so prominently. It should not erase otherwise useful evidence about implementation ability.

Recommended reporting:

- add a structured `complete_submission` or `incomplete_submission` field based on task-declared required deliverables;
- show complete attempts over total attempts for every leaderboard group;
- retain the all-trial mean as the primary quality aggregate;
- optionally show a complete-only mean as a secondary diagnostic, clearly labelled.

The current 25-point test-adequacy loss is already material. Zeroing or capping the whole trial would conflate implementation and test-writing ability; excluding incomplete trials from the mean would reward unreliable systems through survivorship bias.

### 7. Separate deterministic and judged evidence

The current 100-point composite contains an 85-point deterministic subtotal and 15 judged points. Readability and maintainability each use only five bins, and one bin changes the total by 1.6 or 1.4 points—comparable to documented same-input rejudge movement.

Recommended leaderboard fields:

- **Deterministic:** normalized applicable automated score, with each component retained.
- **Judge:** readability and maintainability shown separately, with judge identity and status.
- **Composite v2:** optional secondary summary, never the only ranking signal.
- **Completion:** complete attempts over total attempts.

Use deterministic evidence as the primary ordering unless the comparison question explicitly needs judged quality. Treat small composite differences inside the known judge-noise band as ties rather than precise ranks.

Claude Opus 5 at high effort is the preferred long-term judge, but the judge choice is not settled merely by choosing its exact identifier. If Opus is also used as a strong-frontier trial subject, it would judge its own submissions on 15 points. That same-model exposure is stronger than the currently disclosed same-family harness risk. The team must therefore choose both the judge and the treatment of judge-equals-trial-model results: exclude those judged dimensions from comparison, flag and separate them, or deliberately accept and document the bias. Do not silently include them in an ordinary composite.

Any judge-prompt change must preserve the task-level `judge_context` mechanism and the current empty-context rendering invariant. Endpoint anchors must not contain generic DRY guidance or similar language that would disarm Task 005's intentional tension between maintainability and authorized scope. Also:

- anchor the observable meanings of scores 1 and 5;
- reject non-integer, out-of-range, missing, or malformed category values;
- decide explicitly whether judge score 1 means zero credit: if it does, use `(score - 1) / 4`; the current `score / 5` produces a 20% floor;
- supply the complete relevant diff or a deterministic per-file representation rather than truncating the first 40,000 characters in file order;
- preserve retry/fail-loud behaviour for malformed judge output.

A single judge remains proportionate. Do not multiply cost with three-judge sampling unless calibration demonstrates that judge variance changes material conclusions.

**Alternative:** retain the pinned Sonnet judge to reduce cost. This is defensible operationally, but the no-valid-results boundary makes now the cleanest time to adopt the intended Opus default.

### 8. Report operational telemetry without scoring it

The aggregator already reports `n`, mean, best, and worst, so run range is present. With three runs per configuration, standard deviation would imply more statistical precision than the sample supports; retain mean and range.

Add or retain separate operational fields for:

- median and range of model execution time;
- virtual-environment setup time separately from model time;
- token counts with parser source and verification status;
- cost only as optional metadata, not a headline comparison;
- unavailable or non-comparable telemetry explicitly marked.

Claude and Codex expose different cache and reasoning token fields, so a cross-harness token total must not be presented as directly comparable without a documented normalization. Do not add lint or code-health as duplicate headline metrics: lint already contributes deterministic hygiene, while repository-level code-health is poorly scaled to tiny authorized task diffs and overlaps judged maintainability. Either can remain in detailed trial evidence.

## Recommended reporting model

No single number fully answers “which model is best for scientific coding.” The leaderboard should retain task-level components and provide a compact model summary:

| Field | Role |
|---|---|
| Deterministic quality | Primary repeatable outcome over applicable automated obligations |
| Judge dimensions | Secondary evidence about readability and maintainability |
| Composite v2 | Optional convenience summary, labelled with rubric version |
| Completion rate | Reliability and compliance signal |
| Per-task mean and range | Capability and run-to-run variability |
| Duration | Operational efficiency, separate from quality |
| Tokens | Efficiency diagnostic within comparable harness accounting |

Overall model summaries should macro-average task results so a task with more pytest nodes, mutations, or trials does not receive accidental extra weight. Task-specific gates and N/A categories must remain visible rather than being silently converted into generic zeros or passes.

## Task-bank evolution

### Immediate position

Retain all five tasks through the next calibration. Change only grader/rubric mechanics and the metadata necessary to express Task 004's gate and acceptance-obligation groups. Do not rewrite task specifications to force greater score spread.

### Calibration population

After rubric v2 passes reference and control validation, run a small calibration grid across all five tasks:

- at least one genuinely weak local model;
- the established weak-frontier tier;
- one strong frontier anchor;
- repeated trials sufficient to expose gross variance without treating a three-run sample as a population estimate.

Use the calibration to decide:

- whether Task 004's mutation adequacy has useful spread below and above the prior weak-frontier tier;
- whether Task 005 ever exposes scope behaviour;
- whether judged dimensions change material conclusions relative to deterministic evidence;
- whether operational telemetry is sufficiently comparable to publish.

### Next task priority

Add a debugging/root-cause task first if the bank expands to six. If the bank must remain at five and Task 005 is flat across tiers, replace Task 005 with debugging.

Do not strengthen Task 005 by naming the attractive nuisance in its specification. That would reveal the intended trap and convert a judgment test into reading comprehension. If a stronger stimulus is eventually required, change the substrate or task situation and repeat the same reference, control, and adversarial-review process used for the current tasks.

Performance-at-scale is the next addition after debugging. A larger architectural task should follow only when the cost and timeout implications for weak local models are understood.

## Implementation constraints

These are constraints for the team, not a frozen implementation plan:

- Preserve the one-shot trial rule and hidden-test isolation.
- Keep rubric weights, category definitions, applicability profiles, and gate policy in versioned data rather than hardcoding them in grader or aggregator branches.
- Stage worktree changes before every diff-based check so new files are visible.
- Treat unmapped hidden nodes, unresolved rubric profiles, malformed judge output, and incompatible aggregation versions as loud evaluator failures.
- Do not silently regrade or mix existing records after v2. Archive superseded evidence and use new run IDs.
- Validate every task profile against its reference solution, frozen-only mutation control, and deliberately broken fixtures. Checked-in weak/degenerate controls currently exist only for Tasks 004 and 005; add targeted low-signal correctness fixtures for Tasks 001–003 as part of obligation-group validation rather than treating their coverage as already present.
- Add focused harness tests for scoring arithmetic, N/A categories, gates, integrity violations, version partitioning, malformed metadata, and aggregation of incomplete attempts.
- Recheck both callers of shared harness command builders when changing judge behaviour.
- Update `README.md`, `docs/DESIGN.md`, rubric commentary, task metadata, and `HANDOFF.md` alongside the implementation.

## Validation gates before new model trials

Rubric v2 should not be considered ready until all of the following hold:

1. Every current hidden node maps to exactly one acceptance obligation.
2. All five reference solutions reach their intended ceiling under the applicable profile.
3. Existing Task 004/005 weak and degenerate controls retain their intended low signals, and new targeted Tasks 001–003 correctness controls demonstrate that each obligation group affects the score as intended.
4. Frozen-only tests earn zero mutation credit on every task.
5. A deliberately unauthorized edit receives the same scope consequence regardless of authorized diff size.
6. A protected grading edit produces the intended integrity failure.
7. Task 004's compatibility failure produces a retained zero-scored failed attempt; a passing floor contributes no free correctness points, and the configured task profile—not generic N/A renormalization—determines the exact test-adequacy and judged shares.
8. Missing required tests remain visible in both trial records and aggregate completion rates.
9. Judge boundary, malformed-output, retry, range-validation, complete-diff/fallback, `judge_context`, empty-context-rendering, Task 005 non-disarmament, and same-model-treatment tests pass.
10. Mixed rubric or task-contract versions cannot appear as one leaderboard cohort.
11. All grader, aggregator, focused harness, reference-solution, and control tests pass in isolated environments.
12. A pre-existing multiline Ruff finding whose start line is unchanged is excluded, a finding starting on a changed line is retained, and the pinned repository ruleset is demonstrably the one invoked.
13. Differential lint and an independent high-effort code review find no unresolved material issue.

## Alternatives and recommendation

### Minimal correction

Change only Task 004 correctness, scope normalization, and the inaccurate warning wording.

**Advantages:** smallest implementation and validation cost.

**Disadvantages:** leaves node-count weighting, evaluator drift, mutation attribution, provenance, and mixed subjective/deterministic ranking unresolved.

### Targeted rubric v2 — recommended

Implement the eight policy changes in this report, retain the five tasks, revalidate all references and controls, then calibrate across three model tiers.

**Advantages:** corrects the material validity risks without discarding strong instruments or manufacturing difficulty. Produces interpretable evidence for both capability and reliability.

**Disadvantages:** obligation mappings and version-aware aggregation require careful implementation and full revalidation.

### Broad task-bank redesign

Replace apparently saturated tasks, add several dimensions, and rebuild the benchmark around a new composite.

**Advantages:** could eventually broaden scientific-coding coverage.

**Disadvantages:** confuses missing calibration with defective task design, multiplies adversarial-review cost, delays trustworthy results, and risks optimizing tasks to a desired score distribution.

## Team decisions required before implementation

The recommended direction is clear, but the following policy values should be frozen by the team before code is written:

1. Whether Task 004 is represented solely by mutation adequacy after its gate, or by an explicit test-task weighted profile.
2. The fixed consequence for an ordinary unauthorized file and the exact classes that constitute an integrity violation.
3. Whether acceptance obligations are equal-weighted by default or may carry explicit task-specific weights.
4. Whether judge score 1 maps to zero credit or a deliberate 20% floor.
5. Whether deterministic score or composite v2 is the default leaderboard ordering.
6. Which judge model to pin and how to treat judged scores when the judge is also the trial model; if Opus remains preferred, its exact model identifier.
7. The exact isolated Ruff ruleset, not only the Ruff version.
8. The maximum judge-input size and deterministic fallback when a complete diff exceeds it.

Acceptance-obligation membership should live in task metadata, while every default or task-specific weight should live in `eval/rubric.yaml`, preserving the repository rule that grading weights have one source of truth.

The proposed completeness flag supplements rather than replaces `no_submission`: every no-submission trial is incomplete and retains the existing all-zero treatment, while `incomplete_submission` additionally covers non-empty diffs missing task-declared deliverables. Both remain in the primary aggregate.

## Recommended next action

Approve or amend those eight policy choices, then implement rubric v2 as a fresh, bounded harness change. Do not run another benchmark batch until the validation gates above pass and the changed scoring system receives independent Claude Opus 5 high-effort review.
