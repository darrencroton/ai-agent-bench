# Eval consolidation branch: holistic code review

Date: 2026-09-08

Branch: `eval-consolidation-trial`

Reviewed commit: `04af7b843e54a35586f60b47ba08cd109f3ea573` (`Replace the composite score with an independent-columns profile view`)

Comparison base: `4bae2f5`

Verdict: **FAIL for merge or promotion as the benchmark's primary reporting and Mode 2 path.** The implementation is well tested and reproduces most of the frozen trial measurements, but three P1 findings can make the benchmark rank unlike evidence or report a score for evidence other than the artifact actually delivered. The branch should remain a trial until those are fixed and the end-to-end operator step is completed or explicitly waived.

**Status: addressed (2026-09-08).** All 3 P1s and every substantive P2/P3 below were fixed the same day this review was written -- see `docs/DESIGN.md`'s "Tenth session" History entry for what changed and how it was verified. The end-to-end Mode 2 operator step (this review's step 10) remains outstanding and is tracked in `HANDOFF.md`. Kept here as the audit trail; do not re-derive these findings from a fresh review of the same commit.

## Review scope and authorization

This review covered all 17 changed files (10 added, 7 modified; 7,621 insertions and 44 deletions), the full `4bae2f5..04af7b8` diff, `HANDOFF.md`, `README.md`, `AGENTS.md`, the consolidation proposal and trial record, the design history, the Mode 2 transplant findings, relevant task metadata, the grading and reference-check call paths, the worktree lifecycle, all three new test modules, and the tracked generated outputs.

The user explicitly requested a combined plan/goal-conformance review, code review, simplification review, code-health assessment, style audit, unused-surface audit, and final fresh-eyes review. No separate drift-audit receipt exists. This report therefore assesses both implementation quality and conformance to the accepted consolidation intent, but it does not certify formal authorization drift.

The external `relative-velocity` plan-rewrite commit named by `HANDOFF.md` (`043b13c477b8164466060a129fb5b33fd0a81c22`) was not available in the local `relative-velocity` checkout (`git show` returned exit 128, `bad object`). The local consolidation proposal and documentation were reviewed, but that external commit was not independently inspected.

Backward compatibility is not treated as a reason to retain unused branch-local code, policy, fields, or tests. Removal recommendations below prefer the smallest current design.

## Intended problem and proposed solution

The existing v2 benchmark combines one strongly discriminating signal with several saturated signals and two AI-judged categories. The composite compresses meaningful mutation-kill differences, adds model cost and variance through an AI judge, and can rank models with weaker tests above models whose tests kill more seeded faults. The accepted consolidation proposal replaces that output with a profile: correctness as a gate, mutation kill rate as the primary score, deterministic structural quality as an independent secondary score, lint and scope as flags, and reliability/cost as records. Mode 1 is intended to be a cheap Task-001 screen. Mode 2 is intended to qualify a screened model by grading the actual result of a supervised `project-manager` Mode B workflow through the same unchanged grading kernel. No composite is supposed to remain in the primary decision path.

The branch implements that shape with `profile_view.py`, `structure.py`, `branch_check.py`, `eval/profile.yaml`, and tracked generated profile/structure artifacts. It correctly keeps grading policy and reporting policy separate, leaves the existing graded records and leaderboard bytes unchanged, and shares cohort grouping with `aggregate.py`. The central defects are not ordinary syntax or test failures; they are mismatches between the evidence shown and the claims the benchmark intends that evidence to support.

## Findings

### P1 — The headline profile ranks models measured on different task sets

Locations: `eval/harness/profile_view.py:324-369`, especially lines 334-356; `eval/harness/profile_view.py:409-430`; `eval/harness/profile_view.py:489-504`; `README.md:20-28`.

`build_model_row()` averages every task a model happens to have run, and `main()` sorts all such means together. The accepted routine workflow, however, runs a new model only on Task 001. The generated table already demonstrates the problem: `glm-5.3-flash` has three tasks and `minimax-m3` has two, yet both are ranked directly alongside models with all five tasks. The task means are not exchangeable: the independently verified cohort-wide mutation means for Tasks 001–005 are 55.2%, 53.8%, 77.4%, 94.7%, and 81.2%. A Task-001-only mean and a five-task mean therefore answer different questions.

This invalidates the profile's headline comparative ranking in exactly the documented normal workflow. The visible `Tasks` column discloses the mismatch but does not make the sorted ranking valid.

Required fix: make the headline screen compare a common task set. The lightest design is a Task-001-only screening table for every model, because that is the accepted Mode 1 contract. If a full-bank summary remains useful, render it separately and include only complete-bank models. Do not macro-average whichever subset happens to exist. Add a regression test with deliberately different task distributions and partial model coverage; assert that unlike coverage can never enter one ranked column.

### P1 — Mode 2 grades a sanitized authorized-surface transplant, not the source branch

Locations: `eval/harness/branch_check.py:110-135`, `eval/harness/branch_check.py:138-165`, `eval/harness/branch_check.py:290-321`, `eval/harness/branch_check.py:339-361`, and `eval/harness/grade_trial.py:1073-1083`.

`branch_check.py` copies only the task's `authorized_surface` into a clean baseline worktree. It checks only paths listed in `frozen_unchanged`, and a mismatch merely emits a warning before grading continues. Any other unauthorized source-branch change is absent from the transplanted worktree, so `grade_trial.py`'s scope and integrity checks cannot see it. A changed or missing frozen path is also replaced by the local clean baseline. The output can consequently report clean scope and successful correctness for a source branch that violated the task or did not share its substrate.

The 14-branch experiment was credible because a separate manual audit established that every source branch changed exactly the four authorized paths. Promoting the script to an arbitrary `--repo`/`--branch` CLI makes that one-time prerequisite part of the tool's correctness contract. The current docstring explicitly says interface identity is still left for a human to eyeball, which is inconsistent with a first-class qualifier intended to produce trusted, repeatable evidence.

The manifest does record `source_repo`, `source_branch`, `source_commit`, missing deliverables, and the frozen-file check, but `grade_trial.py` drops those fields from the durable graded record. The temporary manifest therefore contains the only link from a Mode 2 grade to its source evidence.

Required fix: fail closed unless the source branch is proven to start from an explicitly identified compatible baseline, and validate the complete source diff before constructing the grading worktree. Either reproduce the complete diff so the existing scope checker sees unauthorized changes, or reject any source diff outside the authorized surface before grading. Treat every substrate mismatch as invalid, not warning-only. Preserve a compact Mode 2 provenance block in the durable record/report, including source commit, verified baseline identity, full changed-path set, and verification result. Add an end-to-end negative test in which a source branch changes one authorized and one unauthorized path and assert that no normal grade can be produced.

### P1 — Structural scores are not bound to the graded post-image

Locations: `eval/harness/structure.py:382-469`, especially lines 407-434 and 458-463; `eval/harness/structure.py:606-621`; `eval/harness/worktree_lifecycle.py:194-216`.

In automatic mode, `structure.py` prefers any discoverable live worktree and reads current file bytes from it. It trusts the old graded record's `changed_files` list but does not verify that the worktree still matches the state graded by `grade_trial.py`. If an archived patch also exists, automatic mode still prefers the worktree unless all scored files are absent. The worktree lifecycle explicitly acknowledges that a worktree can change or become corrupted after archiving and refuses to prune when its current diff differs from the patch. Running the ordinary structural sweep during that state silently scores the newer worktree while the correctness, mutation, scope, and lint values still describe the earlier grade.

Neither the graded record nor `structure.json` stores a content identity for the scored post-image. The current six worktree/patch pairs happen to match, but that audit is a point-in-time observation rather than an enforced invariant.

Required fix: bind the derived score to immutable submission evidence. For new grades, record a canonical staged-diff or post-image hash in the graded record. When a patch exists, prefer it as the archived source or require the live diff to match it byte-for-byte before using the worktree. For a fresh unarchived worktree, verify it against a hash captured during grading. Record the input evidence hash in each structural entry and make mismatches a failed sweep entry. Add a negative test that mutates a graded worktree after a patch or recorded hash exists and assert that automatic mode refuses to emit an `ok` score.

### P2 — Patch blob-integrity failure is counted as a successful score

Location: `eval/harness/structure.py:491-523` and `eval/harness/structure.py:556-615`.

When reconstructed bytes do not match the patch header's declared post-image blob, the file receives `"blob_verified": false`, but `_score_record()` still returns `status: "ok"`. `sweep()` therefore counts the entry as scored, excludes it from `n_failed`, exits successfully, and writes a structural score over evidence its own integrity check rejected.

Required fix: return an explicit integrity-failure status, omit the score, count it in `n_failed`, and make the CLI exit nonzero when any integrity failure occurs. Add a negative test by corrupting the declared blob or reconstruction and assert fail-loud behavior.

### P2 — Reporting policy contains ignored behavior, and one hashed metric selector does nothing

Locations: `eval/profile.yaml:22-25`, `eval/profile.yaml:49-81`, `eval/profile.yaml:198-202`, `eval/harness/profile_view.py:235-252`, and `eval/harness/structure.py:188-216`.

`eval/profile.yaml` explicitly says its `score:` and `flags:` sections are declarative documentation read by no code. `profile_view.py` hardcodes `test_adequacy`, `hygiene`, and `scope_discipline`. These policy sections are duplicate prose masquerading as configuration and are unused under the requested no-backward-compatibility standard.

The `structure` component mappings are worse: `load_policy()` requires and hashes each `metric` value, but `structural_score()` ignores it and hardcodes its own mapping. A direct check changed `structure.decomposition.metric` from `function_count` to `mean_cyclomatic`; the policy hash changed, but the computed score remained exactly `53.11211664152841`. A policy change can therefore appear provenance-distinct while having no behavioral effect.

`profile_view.load_gate_threshold()` rejects booleans and nonnumeric values but accepts YAML `.nan` and infinities. A NaN threshold makes every `correctness >= threshold` comparison false, silently converting the whole cohort to gate failures; non-finite reporting policy must fail during loading.

Required fix: choose one minimal source of truth. Because project guidance says reporting policy lives in `profile.yaml`, make the category identifiers and component metric selectors drive the implementation and validate the supported schema strictly. If dynamic score/flag categories are not genuinely required, delete the unused `score:` and `flags:` sections and revise the guidance rather than retaining decorative configuration. For component metrics, the simplest correct implementation is `metrics[cfg["metric"]]` plus validation that the referenced metric exists. Reject booleans and nonnumeric/nonfinite gate thresholds and structural endpoints, and reject `zero_at == one_at` during policy loading. Replace shape-only tests with behavior tests that mutate each policy value and assert a changed result or a loud validation failure.

### P2 — Partial and stale structural sidecars can still produce authoritative-looking headline values

Locations: `eval/harness/profile_view.py:215-258`, `eval/harness/profile_view.py:305-321`, `eval/harness/profile_view.py:334-362`, and `eval/harness/profile_view.py:454-504`.

Per-task cells receive `*` when one or more run IDs are missing from `structure.json`, but the model headline averages the remaining values and carries no partial marker. Its withholding rule checks only whether each eligible task has at least one numeric mean, not whether every contributing trial is present and valid. This is the normal state immediately after a new grade because grading does not regenerate the sidecar.

The inverse stale state is also unchecked: extra sidecar run IDs are not rejected or ignored before `structure_eligible_tasks()` derives the global eligible-task set. Archiving a run record can leave an old task in that set and incorrectly withhold otherwise complete model rows. `structure.py` also reports `_meta.n_records` from every JSON file found even though it omits `harness == "none"` entries from results, so the metadata can disagree with the emitted record set once a Mode 2 record is present.

`check_policy_freshness()` detects a mismatch between the current structural policy hash and the sidecar hash, but `main()` only prints a warning and continues to render all numeric Structure values. Those values are known to have different semantics and should not remain authoritative-looking under the new policy.

Required fix: join sidecar entries to the currently loaded, leaderboard-eligible records and require exact membership for an authoritative headline. Withhold or visibly mark a model structural value whenever any expected trial is absent, failed, or policy-stale; withhold the whole structural column when the policy hash is missing or mismatched. Derive eligible tasks from the joined current records/current cohorts, warn on both missing and extra IDs, and make metadata counts describe the emitted set. Tests should cover missing entries, extra entries from an archived task, failed entries, policy mismatch, missing policy hash, and `harness == "none"` records.

### P2 — The durable implementation record contains false central claims

Locations: `docs/EVAL-CONSOLIDATION-TRIAL.md:181`, `docs/EVAL-CONSOLIDATION-TRIAL.md:251`, `docs/DESIGN.md:136-139`, `docs/DESIGN.md:213`, and `eval/profile.yaml:163-175`.

The trial and design records say the change adds nine files, modifies no tracked file, and leaves `aggregate.py` untouched. The actual commit adds 10 files and modifies 7, including `aggregate.py`. The documents also report 157 harness tests while the fresh suite has 159. The trial record also needs to distinguish the model-free profile generation path from the unchanged grader, which still invokes an AI judge. `profile.yaml` correctly labels Task 001's 23.3-point range as pre-`new_files_only` evidence, but adding the resulting 57.7-point post-scope range would make the transition easier to audit; the omission is clarity debt, not a false claim.

These are auditability defects, not cosmetic typos: the documents present themselves as the durable evidence that existing cohorts were not invalidated and that the new measurement does what it claims.

Required fix: update all counts and scope statements from the actual commit; state precisely that no grading-policy input, task contract, grader behavior, or existing graded record changed; state separately that the new reporting/structure path makes no model call while legacy grading still does; add the post-scope structural range for clarity; and update the validation count to 159.

### P3 — Remove unused result fields and avoid retaining tests that only bless dead declarations

Locations: `eval/harness/profile_view.py:235-258` and `eval/harness/profile_view.py:350-369`; related tests in `eval/harness/test_structure.py:154-213`.

`group_stats_profile()` returns `structure_n_scored`, and `build_model_row()` returns `structure_n_covered` and `structure_n_eligible`; no production code or test consumes any of the three fields. Remove them. Do not keep speculative return-schema compatibility on this new branch.

The test suite contains no orphaned test file—pytest collects and runs all three new modules—but some tests validate that the YAML contains keys or that its hash changes without demonstrating that those keys affect behavior. Once the ignored policy is removed or wired in, replace those shape-only assertions with behavioral contract tests. In particular, a test that merely approves sidecar-derived eligible tasks should not preserve the stale-global-sidecar behavior described above.

### P3 — Extract the duplicated strict staging/diff helper, but do not broadly split the orchestration functions

Locations: `eval/harness/branch_check.py:339-357` and `eval/harness/reference_check.py:229-249`.

The 11-line normalized `git add -A` plus checked `git diff --name-only` block is duplicated exactly across the two trusted-evidence entry points, including cleanup-sensitive error semantics. Extract one narrowly named helper that stages, returns changed paths, and raises with stderr on failure; let each caller retain its own cleanup. Do not unify this with `run_trial.py` without a separate decision, because the comments document intentionally different failure handling there.

The differential code-health evidence shows large orchestration functions (`profile_view.main`, cyclomatic complexity 37; `structure._score_record`, 34), but their branches map to real CLI phases and failure states. Splitting them merely to lower a metric would increase indirection. Apart from the exact duplicated block and the dead fields above, the current module boundaries and dependencies are reasonable.

### P3 — Style and generated-artifact presentation need a cleanup pass

Locations include `eval/harness/aggregate.py:134`, `eval/harness/profile_view.py:245`, `eval/harness/profile_view.py:293`, `eval/harness/profile_view.py:454`, `eval/harness/structure.py:415`, `eval/harness/test_structure.py:445`, and `eval/harness/profile_view.py:580-599`.

Several source comments embed dated review history such as `P1 (external review, 2026-09-07)`. The rationale belongs in present-tense invariant comments, while review history belongs in `docs/DESIGN.md` or commit history. Remove the review labels and retain only the technical reason.

`eval/harness/structure.py:13-16` says both `profile_view.py` and `branch_check.py` import its library directly; `branch_check.py` does not. Correct the module documentation rather than preserving a nonexistent dependency.

The generated profile's grouped provenance footnote still produces an approximately 3,759-character line for the current data, undercutting the legibility rationale in the adjacent comment. Render one group per sub-bullet or otherwise keep generated lines reviewable. Explicitly label both `eval/profile.md` and `eval/results/structure.json` as generated/do-not-hand-edit at the artifact top level or in the closest unavoidable documentation.

New prose in `README.md`, `AGENTS.md`, `docs/DESIGN.md`, and `docs/V3-DISCRIMINATION-ASSESSMENT.md` is manually hard-wrapped despite the repository instruction that Markdown prose must not be hard-wrapped. Reflow changed paragraphs only; do not churn unrelated history.

## Contract and design assessment

No task contract, rubric, hidden test, mutation bank, or grading implementation changed in this commit. The tracked `eval/leaderboard.md` is byte-identical to the base version. This supports the claim that the 219 existing graded records remain valid under their original policy.

The implementation deliberately narrowed structural measurement to new Python deliverables and excluded code-health duplication after the evidence showed that whole-file metrics on modified substrate files and duplication did not predict the target construct. That is a reasonable evidence-backed refinement, not itself a defect. The residual construct limitations remain material: structural scoring applies to only two of five tasks, ignores class methods, rewards raw top-level function count up to saturation, and was calibrated against 13 labeled PM branches. It should continue to be described as an experimental independent signal, not a general maintainability score.

The proposal's Step 5, a fresh real two-slice Mode 2 run, remains an operator decision rather than completed acceptance evidence. Given the Mode 2 integrity finding above, it should not be run for a trusted comparison until `branch_check.py` fails closed and persists source provenance.

## Removal audit

Keep, with the correctness fixes above:

- `eval/harness/profile_view.py`: it is the new primary reporting entry point and is linked from operator documentation.
- `eval/harness/structure.py`: it is the deterministic secondary-score library and sweep CLI.
- `eval/harness/branch_check.py`: it is required for Mode 2, but must not be promoted as trustworthy until the P1 source-diff/substrate issue is fixed.
- `eval/profile.md`: it is the tracked human-readable generated profile; retain if the repository intentionally tracks generated reporting beside `leaderboard.md`.
- `eval/results/structure.json`: it must remain tracked because most reconstruction inputs are local/gitignored and unavailable in a fresh clone; add stronger evidence identity rather than deleting it.
- The three new test modules: all are collected and cover live behavior. Replace weak or incorrect tests rather than removing the modules.
- `aggregate.group_and_order()`: both reporting paths consume it, and centralizing cohort partition/order removes a real divergence risk.
- The `run_batch.py` and `run_trial.py` post-run messages: they are live operator guidance, though they should be reconsidered after deciding whether automatic profile regeneration belongs in the workflow.

Remove or replace:

- Remove the unused `structure_n_scored`, `structure_n_covered`, and `structure_n_eligible` return fields.
- Remove `eval/profile.yaml`'s unused `score:` and `flags:` blocks unless they are made authoritative runtime inputs.
- Replace policy shape/hash-only tests with behavior tests; do not retain tests whose only function is to bless unused declarations.
- Remove dated external-review labels from code comments after preserving their present-tense invariant.
- Replace the duplicated strict staging/diff block with one helper.

No other new production function, CLI, generated artifact, or test file was found without a current consumer or a documented reproducibility role. Automated dead-code and coverage scanners were unavailable in the environment (`vulture` and `coverage` were not installed), so this conclusion comes from symbol/reference tracing, CLI/documentation entry points, pytest collection, and generated-artifact readers rather than those optional tools.

## Code-health evidence

Differential analysis used base `4bae2f5` and covered the full changed Python surface with no parser fallback, analysis limits, dependency cycles, unrecognized files, or vendor exclusions. New production code is concentrated in `structure.py` (494 code lines), `profile_view.py` (507), and `branch_check.py` (300). The dependency additions are acyclic and justified. The only exact production duplication worth extracting is the strict 11-line staging/diff block. Large orchestration-function complexity is visible, but a broad decomposition pass is not recommended without a specific responsibility seam.

## Style-guide audit

Standard: repository `AGENTS.md` plus the default Python/Markdown baseline from the `style-guide` skill.

Scope: all changed source, tests, Markdown, YAML policy, and generated artifacts in `4bae2f5..04af7b8`.

Result: naming, imports, test discovery, and most docstrings are clear; `git diff --check` passes. The main style defects are inaccurate documentation, dated review-history comments, hard-wrapped new Markdown prose, the oversized generated provenance line, and insufficient do-not-hand-edit signaling for generated artifacts. Style verdict: **FAIL pending cleanup**, primarily because inaccurate audit documentation is functional project metadata in this repository.

## Validation and evidence

- `venv/bin/python -m pytest tests/ -q`: exit 0, **80 passed** in 5.17 seconds.
- From `eval/harness`, `../../venv/bin/python -m pytest -q`: exit 0, **159 passed** in 12.66 seconds.
- `venv/bin/python eval/harness/validate_obligations.py`: exit 0, all **5 tasks passed** in 22.64 seconds.
- Focused new-code tests independently rerun: exit 0, **68 passed**.
- `git diff --check 4bae2f5..HEAD`: exit 0.
- Differential code-health analysis: complete Python metric coverage; no dependency cycles or analysis exclusions.
- Tracked sidecar invariant check: 219 records, 91 scored, 128 not applicable, 0 currently failed; policy hash matches the tracked profile policy.
- Current worktree-versus-patch audit: all 6 jointly scoreable records produced identical metrics and scores. This is useful current-state evidence but does not remove the missing binding identified in P1.
- Generated-artifact portability check: no machine-specific absolute paths found.
- Existing leaderboard compared with the base commit: byte-identical.
- Optional removal-audit scanners: `vulture` unavailable (exit 1, module not installed); `coverage` unavailable (exit 1, module not installed). These are unavailable coverage, not passes.
- Context-clean fresh-eyes review: all three P1 findings and the removal audit were independently upheld; one range-description overstatement was corrected, and the policy-staleness/non-finite-gate paths were added.

## Recommended repair order for a fresh session

1. Fix the Mode 1 comparison semantics: make the primary screen a common Task-001 comparison and separate or withhold full-bank summaries with incomplete coverage.
2. Make Mode 2 fail closed on substrate and complete-diff identity, and persist source provenance through grading.
3. Bind structural scores to immutable graded evidence; fail on live/archived/hash divergence.
4. Turn blob mismatch and every evidence-integrity failure into a failed/nonzero sweep result.
5. Make `profile.yaml` genuinely authoritative or delete its unused sections; reject non-finite gate and structural calibration values; add behavioral policy tests.
6. Make sidecar/current-record membership exact and propagate any partial/failure state to headline values.
7. Remove dead fields, extract only the strict duplicated staging/diff helper, and keep the larger orchestration structure unless a real seam emerges.
8. Correct the durable documentation and generated-artifact presentation.
9. Re-run the focused tests, both full suites, obligation validation, a patch/worktree equivalence audit, `structure.py sweep`, and `profile_view.py`; verify `leaderboard.md` remains byte-identical.
10. Only then run or explicitly waive the proposal's fresh Mode 2 operator trial.

## Final assessment

The branch is a strong experimental prototype: it preserves the old cohort, removes the composite from the new view, shares cohort logic correctly, produces deterministic current results, and has substantial focused test coverage. It is not yet fit to be the benchmark's trusted primary profile or Mode 2 qualification path. The current failures are evidence-integrity and comparability failures, which matter more here than the green unit suites. Fix the three P1 issues first; the P2/P3 work is then a contained cleanup rather than a redesign.
