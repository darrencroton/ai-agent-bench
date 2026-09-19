# Implementation Plan: Multi-Task Support for ai-agent-bench

## Purpose and scope

Today this bench is hardwired to exactly one scientific task: one target repo (`relative-velocity`), one frozen plan (`docs/MERGER_RATE_PLAN-2SLICE.md`), one hidden-test suite (`hidden_tests/slice1|2` + `hidden_tests/obligations.yaml`). This plan makes the harness able to run a **second** scientific task (a different target repo, plan, and hidden-test suite) side by side with the first, without any risk of the two tasks' scores silently blending, and with a normalized cross-task ranking for the Developer seat and the reviewer seats.

This plan does **not** onboard an actual second task — no second repo, plan, or hidden-test suite is created here. It builds the mechanism; picking and vending a second scientific target is deliberate future work, done once this lands. It also does not touch anything about how the *current* task (`relative-velocity`) is graded, scientifically speaking: `hidden_tests/`, `docs/MERGER_RATE_PLAN-2SLICE.md`, and `docs/OBLIGATION-GROUPS.md` are not edited anywhere in this plan — only the code that currently hardcodes their paths changes, to read them from policy instead.

### Non-goals (explicit, for every slice below)

- No second real task is added. Multi-task behavior is validated with synthetic fixtures (fabricated `model-report.json`/`policy.yaml` test data with two distinct `task_id`s), never a live second PM run.
- No change to the frozen plan document, hidden-test bodies, or `hidden_tests/obligations.yaml`'s existing content for `relative-velocity`.
- The PM (supervisor) seat stays unranked and unvaried — out of scope, per the investigation that produced this plan.
- No change to `review_score.py` — it harvests purely from `run.json` + `policy.yaml`'s `review_identity.corrections` and has no task-specific logic to generalize.
- No renaming or removal of any *existing* CLI flag's current behavior. Every new `--task` flag is additive and optional, defaulting to the resolved `default_task`, so every command an operator runs today keeps working unchanged with zero policy.yaml edits.

## Design overview

- **`policy.yaml` gets a `tasks:` map**, keyed by an operator-chosen task id string (e.g. `relative-velocity`), plus a top-level `default_task:` scalar. Each task entry carries what is today's single set of flat scalars/hardcoded constants: target repo path, branch prefix, plan/provenance file paths, hidden-tests directory, obligations file, expected slice count, and production/test/doc path globs. The `relative-velocity` entry's values are set to make every existing tool behave identically to today, byte for byte. **The old flat keys are removed incrementally, not all at once**: each slice that finishes migrating a given key's last remaining reader removes that key in the same commit, so every slice's own end state leaves the full tool suite working and fully tested (see "Migration approach" below).
- **`bench_lib.resolve_task(policy, task_id)`** is the one place that resolves and validates a task id into a fully-checked dict (fails loudly, names the task id and the missing/malformed key — never guesses). Every tool that needs task configuration calls this instead of reading flat policy keys.
- **`task_id` becomes a first-class field**: stamped by `dev_check.py` into each attempt's provenance at grading time (the only place task configuration is actually resolved against a real grading worktree), propagated by `model_report.py` onto `model-report.json`'s top level (backfilling it for sheets graded before this plan landed — see "Migration approach"), and used by `leaderboard.py` to **partition reports by task before running any aggregation**, rather than trying to make the aggregation functions themselves task-aware. Each task's tables are computed by the exact aggregation pipeline that exists today, just invoked once per partition.
- **A run is cross-checked against its resolved task at grading time**, not just resolved: `dev_check.py` already reads the run's own recorded target repository from `run.json`; it compares that against the resolved task's configured repo and refuses loudly on a mismatch. This closes the gap an operator-supplied but wrong `--task` would otherwise leave open — the exact score-blending boundary this plan exists to close cannot depend on the operator never mistyping a flag.
- **Cross-task ranking** is a new, clearly-separate derived table: per-task percentile rank of a configuration's first-attempt correctness (and, separately, of reviewer comparative-rank scores), averaged equally across the tasks a configuration appears in. It is computed *from* each task's already-final, independently-correct table and never feeds back into or replaces any task's own correctness number — consistent with this repo's existing "deterministic first, subjective/derived numbers surfaced but never blended" discipline.
- **Where a resolution choice must be made once, it is made once and threaded explicitly downstream** rather than re-derived independently in each tool. Concretely: `cohort_run.py analyze`/`analyze-all` are the only place that *infers* which task a run belongs to (from which task's configured repo the run's worktree structurally belongs to, via `git worktree list` — the same kind of ground-truth check `cleanup` already performs); everything downstream (`grade_run.py`, `dev_check.py`) takes an explicit `--task` it was handed, never re-inferring it.

### Migration approach

Two distinct migration concerns, handled differently, both load-bearing:

1. **Policy schema migration (code-level)**: rather than Slice 1 deleting the old flat keys in one shot (which would leave every other tool broken until Slices 2–5 individually catch up — a real defect an earlier draft of this plan had), the old flat keys are removed incrementally. Slice 1 only *adds* `tasks:`/`default_task:` alongside the existing flat keys, changing no consumer's behavior. Each later slice, when it finishes switching its own tool over to `resolve_task`, deletes the specific flat key(s) it was the last reader of, in the same commit. Every slice's own end state is therefore fully working with a green test suite — there is no "broken until N slices later" window at any commit boundary.
2. **Historical data migration (no new code needed beyond Slice 3's own changes, one operational step)**: the real `results/runs/` tree already holds many graded `relative-velocity` runs from before this plan existed. Their `slice-<N>.json` sheets will never retroactively gain a `provenance.task_id` field — `dev_check.py` deliberately preserves an already-graded attempt's captured provenance on a later regrade (never silently rewriting what rubric an attempt was graded under), so simply re-running `grade_run.py` against an old attempt does not backfill it. Instead, `model_report.py` (Slice 3) treats a sheet with no `provenance.task_id` as belonging to `policy["default_task"]` — a sound inference, not a guess, because before this plan landed `default_task` was structurally the *only* task any sheet in this repository could have been graded under — and marks the report's `task_id_source` as `"backfilled"` rather than `"graded"` so this is always visible, never silent. Because `model_report.py` fully rebuilds `model-report.json` from scratch on every invocation (it is not incremental), the one-time operational step is: after Slice 3 lands and before relying on Slice 5's leaderboard for the historical cohort, re-run `model_report.py` once for every already-graded run. For a run whose original PM run directory (`--run-dir`) still exists on disk, pass it again, along with the same non-default `--policy` if one was used for grading, so timing/provenance/PM-judgment fields stay fully populated — never assume a bare `--run-id` alone is equivalent, since `model_report.py` genuinely uses run-directory access for those fields. **For a run whose trial worktree/PM run directory has already been cleaned up** (`cohort_run.py cleanup`), do not pass its now-nonexistent `--run-dir` — `model_report.py` hard-fails on an explicitly-given but missing `--run-dir`, it does not degrade gracefully for that case; omit the flag entirely instead, exactly as the tool's own standard `--run-id`-only invocation already does, and let its existing, already-documented behavior for a run with no `--run-dir` supplied report those specific fields as unavailable the normal way. In short: **prefer running this migration step before cleaning up any trial worktree**, so every field stays resolvable; for a worktree already gone, use the flag-omitted form, never a stale path. `cohort_run.py analyze-all` does not do this on its own (it only discovers runs that have no `model-report.json` yet), so this is a deliberate, documented, one-time manual step, not a new tool.

## How rigid this plan is meant to be

The **Acceptance Criteria** in each slice below are the frozen contract: what must be observably true when the slice is done. They are what a reviewer checks the diff against.

They are deliberately **not** a frozen implementation. In particular, treat the following as the implementer's judgment call, not something to stop and ask about:

- Exact internal helper/function names and how logic is split between them.
- The literal string used for a policy key, as long as it is used consistently everywhere that slice's authorized surface touches it, and the slice's stated behavior holds.
- Minor `policy.yaml` schema adjustments *within a slice's own authorized surface* if implementation surfaces a genuine gap this plan's authors didn't anticipate (for example: a value some tool reads from the bench root that should have been per-task all along). Add it, document why in a `policy.yaml` comment the same way the existing file already documents every key's rationale, and note it in that slice's summary — don't stop the whole plan over it.
- Exact wording of error messages, as long as they name the concrete file, path, task id, or key involved (this repo's own "fail loudly and specifically" rule, not a plan invention).

What is **not** the implementer's call, and should be a stop-and-ask (or, if run under `project-manager` Mode B, a recorded surface-grant / steer) rather than a silent reinterpretation:

- Anything that would change what a slice's Acceptance Criteria mean, not just how they're satisfied.
- Touching a file outside a slice's authorized surface for anything other than a genuinely mechanical, same-slice consequence (e.g., updating a test fixture in a file already in-surface). A path discovered to be necessary but out of surface is exactly what `project-manager`'s surface-grant mechanism (Mode B) or a plain pause-and-ask (Mode A) exists for.
- Any change to `hidden_tests/`, `docs/MERGER_RATE_PLAN-2SLICE.md`, or `docs/MERGER_RATE_PLAN-2SLICE.provenance.md` content. These stay frozen in every slice, full stop — if a slice's contract seems to require touching them, that's a planning defect, stop and flag it rather than editing them.
- Skipping or weakening the "existing task behaves identically" acceptance criterion that opens most slices below. That criterion exists precisely so a fresh-eyes reviewer doesn't have to re-derive whether a refactor changed real behavior — it's the regression backstop for the whole plan.

If a later slice's assumption about an earlier slice's exact output turns out to be wrong once that earlier slice is actually implemented (e.g. a different key name was chosen), the implementer reconciles it against this plan's stated *behavior*, not its literal prose — and notes the deviation in that slice's handoff/summary so the next slice's implementer (possibly a different session) isn't surprised.

## Implementation Profiles

- **Slices 2, 5**: High difficulty. **Slices 2, 5, 6**: all three marked `Independent audit required: yes` (Slice 6 is Medium difficulty but still carries the mandatory-independent-review flag — don't let the difficulty grouping cause it to be under-reviewed). Together these are the grading-correctness and ranking-logic critical paths, largest blast radius if subtly wrong. Recommend a frontier/senior-profile implementer for 2 and 5, full attention, no batching; 6 can go to a standard-profile implementer but must still get a genuinely independent review pass, not self-audit.
- **Slices 4, 7**: Medium difficulty, no mandatory independent audit — recommend a standard strong-model profile, run individually.
- **Slices 1, 3, 8**: Low-to-Medium difficulty (Slice 3 carries the historical-backfill logic, which raises it above trivial) — recommend any capable model; safe to run each solo without much risk.

## Slice Batches

Batching is a Mode A (assisted-session) convenience only — `project-manager` (Mode B) executes atomic slices in plan order regardless of any batch grouping stated here.

- No batches are recommended by default given the strict dependency chain (each slice's authorized surface assumes the previous slice's schema/field additions already exist) and the mixed difficulty levels. If a single strong implementer runs this end to end in one session, running slices individually in order — with the three `Independent audit required: yes` slices (2, 5, 6) genuinely reviewed by a separate pass, not self-graded — is the recommended path over any batching.

---

## Slice 1: `tasks:` policy schema + `bench_lib.resolve_task`

### Intended Change
- Add a `tasks:` mapping to `policy.yaml`, keyed by task id (string), and a top-level `default_task:` scalar naming which entry applies when no `--task` is given anywhere downstream.
- Populate exactly one entry, `relative-velocity`, whose values reproduce today's hardcoded/flat-scalar behavior: target repo path (today's `relative_velocity_repo`), branch prefix (today's `dev_branch_prefix`), worktree root (today's `dev_worktree_root`), the plan file's path relative to the *target repo* (today's `cohort_run._FROZEN_PLAN_RELATIVE_PATH`), the provenance file's path relative to *this bench's own root* (today's `cohort_run._PROVENANCE_RELATIVE_PATH`), the hidden-tests directory and obligations file paths relative to *this bench's own root* (today's `hidden_tests/` and `dev_check.OBLIGATIONS_RELATIVE_PATH`), the expected slice count (today's `leaderboard.expected_slices`), and a required `measurement` sub-block (`production_paths`/`test_paths`/`doc_paths`, today's flat top-level `measurement.production_paths` etc.) carrying today's exact glob values — these describe the *target repo's* layout, so they belong per-task, not global; only `loc_definition`/`loc_category_definition`/`metric_version` stay in a global top-level `measurement:` block, since they're a methodology choice applied uniformly to any task, never a layout fact.
- **This slice does not remove any existing flat policy key.** `relative_velocity_repo`, `dev_branch_prefix`, `dev_worktree_root`, `leaderboard.expected_slices`, and the top-level `measurement.production_paths`/`test_paths`/`doc_paths` all stay exactly as they are, still read by `cohort_run.py`/`dev_check.py`/`leaderboard.py` exactly as today, alongside the new `tasks:` block. See "Migration approach" above: each later slice deletes the specific key(s) it finishes migrating away from, in its own commit — this slice's job is only to add the new schema without changing any existing tool's behavior at all.
- Add `bench_lib.resolve_task(policy: dict, task_id: str | None) -> dict`: resolves `task_id` (falling back to `policy["default_task"]` when `None`), validates every required key is present with the right type, and returns one self-describing dict including the resolved `task_id` itself. Raises `bench_lib.BenchLibError` naming the task id and the specific missing or malformed key — mirroring the validation rigor `dev_check.load_policy` and `leaderboard.load_leaderboard_policy` already apply to today's flat keys.
- This slice does not wire `resolve_task` into any CLI tool's live behavior yet — that's every following slice's job. It is exercised directly by this slice's own unit tests, which is enough for it not to be dead code (AGENTS.md's "every function must be load-bearing" is satisfied by its tests plus its planned, documented consumers in Slices 2–5, not by having a CLI caller today).
- **Narrow, surgical exception to the above**: relocate `cohort_run.parse_pinned_plan_commit` (today's only implementation of "read the pinned commit out of a provenance file") from `tools/cohort_run.py` to `tools/bench_lib.py`, unchanged in behavior except its raised exception type, and update `cohort_run.py`'s own call site accordingly. This is needed because Slice 2 (`dev_check.py`) must validate `obligations.yaml`'s `plan_pin` against the same pinned-commit logic, and `dev_check.py` cannot import `cohort_run.py` for it — `cohort_run.py` already does `import dev_check`, so the reverse import would be circular. `bench_lib.py` is the correct home regardless of this slice's chronological ordering: it is the shared-helpers module every other tool imports, and this function has never been CLI-specific. The relocated function raises `bench_lib.BenchLibError` (not `CohortRunError`, since it no longer lives in that module); `cohort_run.py`'s call site must catch `bench_lib.BenchLibError` there and re-raise it as `CohortRunError` with the same message, preserving today's exact error-handling contract at the CLI boundary (today's top-level handler catches `CohortRunError` specifically, not its `BenchLibError` parent). This relocation, and the matching call-site/exception-handling update, is the *only* change permitted in `tools/cohort_run.py`/`tests/test_cohort_run.py` in this slice — every other flat-key read in `cohort_run.py` (the actual `tasks:`-schema wiring) stays untouched until Slice 4.
- **Second shared helper, needed for the same reason**: add `bench_lib.repo_belongs_to_task(candidate_repo_path: Path, configured_repo_path: Path) -> bool`, a pure, testable check for whether `candidate_repo_path` is the same repository as `configured_repo_path` — either literally the same path, or a `git worktree` of it (checked the same structural way `cohort_run.resolve_ungraded_run_dirs`/`cleanup` already enumerate worktrees of a configured repo today, e.g. via `git worktree list`). This exists because **two different slices need the identical check**: Slice 2 must verify a graded run's own recorded target-repo path (a trial *worktree*, not the substrate repo path configured in `policy.yaml`) genuinely belongs to the resolved task, and Slice 4 must resolve `--task` from `--dev-repo`'s worktree membership the same way. Putting it in `bench_lib.py` now avoids Slice 2 depending on logic Slice 4 hasn't written yet, and avoids the two slices independently inventing two slightly different implementations of the same check.

### Acceptance Criteria
- Inputs: `policy.yaml` after this slice; `resolve_task(policy, task_id)` with `task_id` a known key of `tasks:`, `None`, or an unknown string.
- Outputs:
  - [ ] `resolve_task(policy, None)` resolves to the `default_task` entry.
  - [ ] `resolve_task(policy, "relative-velocity")` returns a dict whose resolved values are equivalent to today's hardcoded constants and flat policy keys (same repo path, same branch prefix, same plan/provenance/hidden-tests/obligations paths, same expected slice count, same `measurement.production_paths`/`test_paths`/`doc_paths` glob lists) — this is checked by a test that asserts those exact values, not just that resolution succeeds.
  - [ ] `resolve_task(policy, "does-not-exist")` raises `BenchLibError` naming `"does-not-exist"` and the configured task ids available.
  - [ ] A `tasks:` entry missing a required key, or with a key of the wrong type, raises `BenchLibError` naming the task id and the specific key — never silently defaults or coerces.
  - [ ] `bench_lib.parse_pinned_plan_commit` exists, raises `bench_lib.BenchLibError` on the same error conditions its `cohort_run.py` predecessor raised `CohortRunError` for, and `cohort_run.py` no longer defines its own copy — its call site catches `BenchLibError` and re-raises `CohortRunError` with the same message.
  - [ ] `bench_lib.repo_belongs_to_task(candidate, configured)` returns `True` for the configured path itself, `True` for a path that is a registered `git worktree` of the configured repo, and `False` for an unrelated path — verified against a real or fixture git repo with at least one worktree, not just path-string comparison (a trial worktree's path is never literally equal to `policy["tasks"][id]["repo"]`, so this must check actual git worktree membership, not path equality).
  - [ ] Every existing test in `tests/test_cohort_run.py`, `tests/test_dev_check.py`, `tests/test_grade_run.py`, `tests/test_model_report.py`, and `tests/test_leaderboard.py` still passes unchanged after this slice — this is the slice's core regression guarantee: adding the new schema changes no existing tool's behavior at all.
- User-visible behaviour: none — every existing `cohort_run.py`/`dev_check.py`/`grade_run.py`/`model_report.py`/`leaderboard.py` invocation is completely unaffected by this slice, because none of them read `tasks:`/`resolve_task` yet, and every flat key they do read is untouched.
- Behaviour that must not change: every existing tool's behavior against today's single-task `policy.yaml`, in full — this slice is purely additive.

### Authorized Surface
- Files allowed to change:
  - `policy.yaml`
  - `tools/bench_lib.py`
  - `tools/cohort_run.py` (only for the `parse_pinned_plan_commit` relocation and its call-site exception handling described above — no other change in this file)
  - `tests/test_bench_lib.py`
  - `tests/test_cohort_run.py` (only for the relocated function's tests moving/being re-pointed at `bench_lib` — no other change)
- Functions/classes/components allowed to change: `bench_lib.resolve_task` (new), `bench_lib.parse_pinned_plan_commit` (relocated, new in this module), `bench_lib.repo_belongs_to_task` (new), the `tasks:`/`default_task:` addition to `policy.yaml` (additive only — no existing key removed), `cohort_run.py`'s call site for `parse_pinned_plan_commit` and its own now-removed local definition of that function.
- Tests allowed or expected to change: `tests/test_bench_lib.py` (new), `tests/test_cohort_run.py` (only the tests covering `parse_pinned_plan_commit`, relocated to `tests/test_bench_lib.py` or kept as a thin re-export test — implementer's choice).

### Explicit Non-Goals
- Do not touch `tools/dev_check.py`, `tools/grade_run.py`, `tools/model_report.py`, or `tools/leaderboard.py` in this slice — none of them change behavior, and none of them call `resolve_task` yet; Slice 2 is the first real consumer.
- Do not remove any existing flat policy key in this slice — see "Migration approach" above.
- Do not change anything else in `tools/cohort_run.py` beyond the `parse_pinned_plan_commit` relocation and its exception handling — its own `tasks:`-schema wiring is Slice 4's job, not this one's.

### Risk Flags
- Risky surfaces touched: none (no auth/billing/persistence/migration/shared-external-contract surface — `policy.yaml` and `model-report.json` are operator-local tooling config, not a public API).
- Difficulty: **Low** — new, well-isolated code with direct unit tests; no existing call site's behavior changes within this slice itself.
- Approval needed before implementation: no
- Independent audit required: no

### Validation Plan
- Tests to add/update: `tests/test_bench_lib.py` — new tests for `resolve_task` covering: default resolution, explicit task id, unknown task id, missing key, wrong-typed key, and exact value equivalence to today's constants for the `relative-velocity` entry; plus `parse_pinned_plan_commit`'s relocated tests and its exception type.
- Commands to run: `python -m pytest tests/ -q` — the **full** suite, and it must pass in full, since this slice changes no existing tool's behavior.
- Lint (differential, via the `lint` skill): required — `policy.yaml`, `tools/bench_lib.py`, `tools/cohort_run.py`, `tests/test_bench_lib.py`, `tests/test_cohort_run.py`.
- Manual checks: read the new `tasks:` block's comments against the still-present flat keys' own comments and confirm the new block's rationale is consistent with, not contradicting, what the flat keys' comments still say (they coexist in this slice, so both must read as true simultaneously).

### Rollback Path
- Revert this slice's commit. The full test suite passes before and after this commit, so revert is clean, total, and leaves the tool suite exactly as it was.

---

## Slice 2: `dev_check.py` and `grade_run.py` become task-aware

### Intended Change
- `dev_check.py` gains a `--task <id>` CLI flag (default: `policy["default_task"]` when omitted), resolves it via `bench_lib.resolve_task`, and uses the resolved task's `hidden_tests_dir`/`obligations_file`/`plan_file` in place of the current hardcoded `hidden_tests/slice{N}` path convention and `OBLIGATIONS_RELATIVE_PATH` constant.
- Replace the hardcoded `HIDDEN_TEST_FILENAMES = ("test_hA.py", "test_hB.py")` module constant with filenames **derived from the resolved task's `obligations.yaml` for that slice** — its obligation groups' `tests:` entries already carry `tests/test_hA.py::test_name`-shaped node ids; the set of distinct filenames referenced by a slice's obligation groups *is* the set of hidden test files for that slice. This removes a duplicated, task-specific constant in favor of information the obligations file already, uniquely holds — consistent with this repo's "recompute rather than duplicate" principle. **Three** current call sites move to this derivation, not two — check for more before assuming this list is exhaustive: `hidden_tests_manifest_hash`'s file-copy loop, `run_hidden_tests`'s own file-copy loop (both currently iterate `HIDDEN_TEST_FILENAMES` directly), *and* `run_hidden_tests`'s pytest subprocess argv, which today hardcodes the literal strings `"tests/test_hA.py"`/`"tests/test_hB.py"` directly rather than reading the constant — easy to miss by grepping for `HIDDEN_TEST_FILENAMES` alone, since that grep won't find it.
- Add a load-time consistency check: the resolved task's `obligations.yaml` top-level `plan:` field must match the resolved task's `plan_file` (repo-relative path), and `plan_pin:` must match the pinned commit resolvable from the task's `provenance_file` via `bench_lib.parse_pinned_plan_commit` (relocated there in Slice 1 specifically so `dev_check.py` can call it without a circular import on `cohort_run.py`) — a mismatch is a loud, named-file-and-value `DevCheckError`, not a silent grade. This wires up `obligations.yaml`'s existing-but-previously-unread `plan`/`plan_pin` fields rather than inventing a new schema for the same fact.
- Add a second, distinct consistency check, closing a gap plan review flagged: the run actually being graded must belong to the resolved task, not just have a validly-configured task id passed for it. `dev_check.py` already reads the run's own recorded target repository (a trial *worktree* path, e.g. `relative-velocity-trial-1` — never literally equal to `policy["tasks"][id]["repo"]`, which points at the vendored substrate repo itself) from `run.json` at its existing attempt-resolution call sites; pass that recorded path and the resolved task's configured `repo` to Slice 1's `bench_lib.repo_belongs_to_task` — never literal path-string equality, which would reject every real, valid run. A mismatch is a loud `DevCheckError` naming both the run's recorded repository and the resolved task's configured one. This is what actually prevents an operator's mistyped-but-valid `--task` from silently grading a run under the wrong task's rubric; the `plan`/`plan_pin` check above only validates a task's own internal configuration, not its association with the specific run being graded.
- Move `measurement.production_paths`/`test_paths`/`doc_paths` (today a single global policy block, read by `dev_check.classify_path` and validated at load time by `dev_check.load_policy`'s own measurement-keys validation helper) to being read from the resolved task's own `measurement` sub-block (already defined by Slice 1) instead of the flat top-level block. Once this is done, delete the old top-level `measurement.production_paths`/`test_paths`/`doc_paths` keys from `policy.yaml` — this slice is their last reader, and the load-time validation helper that currently requires those keys globally must move to validating them per-task instead (via `resolve_task`, which Slice 1 already requires the sub-block for). `loc_definition`/`loc_category_definition`/`metric_version` stay in the top-level `measurement:` block unchanged, since they're a methodology choice applied uniformly to any task, not a layout fact.
- Stamp the resolved `task_id` into `dev_check.build_provenance`'s returned block, alongside the existing `plan_hash`/`obligations_hash`/`hidden_tests_hash`.
- `grade_run.py` gains its own `--task <id>` CLI flag (default: `policy["default_task"]` when omitted — grading a run without specifying a task keeps working exactly as today for the existing single-task cohort) and threads it into `dispatch_grade`'s `argv` it builds for `dev_check.main(argv)`, as `["--task", task_id]`.
- Update the `--slice` help text (currently "slice number (1 or 2), matching hidden_tests/obligations.yaml") to not bake in the current task's slice count.

### Acceptance Criteria
- Inputs: an attempt commit graded via `dev_check.py`/`grade_run.py`, with or without `--task` given; `policy.yaml` from Slice 1.
- Outputs:
  - [ ] Grading the existing `relative-velocity` task, with `--task` omitted or `--task relative-velocity` given explicitly, produces a sheet whose grading-outcome fields — per-node pass/fail results, obligation-group fractions, the overall correctness score, ΔLOC/ΔCC/size-complexity figures, scope-discipline results, and the attempt's resolved ordinal — are identical to what today's `dev_check.py` produces for the same commit. Fields expected to differ, and excluded from this comparison: the grading timestamp (always refreshed on any regrade, with or without this slice), `provenance.task_id` (new in this slice), and `provenance.policy_hash` (changes because Slices 1 and 2 both edit `policy.yaml`'s content, independent of anything task-relevant to the graded commit). This is the slice's core regression guarantee and must be checked against a real or fixture-recorded prior sheet with this explicit field-exclusion list applied, not just "grading succeeds."
  - [ ] The derived hidden-test filename set for slice 1 and slice 2 of `relative-velocity` equals `{"test_hA.py", "test_hB.py"}` exactly, by derivation, not by a remaining hardcoded fallback.
  - [ ] `obligations.yaml`'s `plan`/`plan_pin` mismatched against the resolved task raises `DevCheckError` naming both the expected and found value.
  - [ ] Grading a run whose own recorded repository (a trial worktree) is not a `git worktree` of the explicitly-passed `--task`'s configured repo, per `bench_lib.repo_belongs_to_task`, fails loudly with a `DevCheckError` naming both, even though the passed task id is itself validly configured. Grading a run whose recorded worktree genuinely *is* a worktree of the resolved task's configured repo succeeds — this must not reject ordinary valid runs by comparing paths for literal equality.
  - [ ] Every attempt's `provenance` block carries `task_id` alongside the existing hash triple.
  - [ ] `grade_run.py --task does-not-exist ...` fails loudly before attempting to grade anything.
  - [ ] `dev_check.classify_path` classifies paths using the resolved task's `measurement.production_paths`/`test_paths`/`doc_paths` (not a global flat read, which no longer exists after this slice), and for `relative-velocity` this produces identical classification to today's behavior for every path in a real `relative-velocity` diff.
  - [ ] All three hardcoded-filename call sites identified in Intended Change (not just the two obviously named by the constant) now derive filenames from the resolved task's obligations, verified by a fixture task whose slice references a filename other than `test_hA.py`/`test_hB.py` and confirming the pytest subprocess argv actually targets it.
- User-visible behaviour: `dev_check.py`/`grade_run.py` invocations exactly as documented in today's `README.md` keep working unchanged.
- Behaviour that must not change: the actual pass/fail outcome and obligation-group scoring of every existing hidden test for `relative-velocity` — this slice changes *how* file paths and filenames are resolved, never what gets graded or how it's scored.

### Authorized Surface
- Files allowed to change:
  - `policy.yaml` (only to delete the now-fully-migrated top-level `measurement.production_paths`/`test_paths`/`doc_paths` keys — no other change)
  - `tools/dev_check.py`
  - `tools/grade_run.py`
  - `tests/test_dev_check.py`
  - `tests/test_grade_run.py`
  - `tests/test_tool_contract.py`
- Functions/classes/components allowed to change: `dev_check.HIDDEN_TEST_FILENAMES` (removed), `dev_check.classify_path` and its `measurement` argument's source, `dev_check.hidden_tests_manifest_hash`, `dev_check.run_hidden_tests` (including its pytest subprocess argv construction — see Intended Change's third call site), `dev_check.build_provenance`, the run/task repository cross-check (new, calling `bench_lib.repo_belongs_to_task`), `dev_check.load_policy`'s measurement-keys validation helper (today validates the flat top-level keys; must move to validating each task's own `measurement` sub-block instead — whatever this helper is actually named in the current code, it is in scope), `dev_check.main`'s new `--task` argument, `grade_run.dispatch_grade`, `grade_run.main`'s new `--task` argument.
- Tests allowed or expected to change: `tests/test_dev_check.py`, `tests/test_grade_run.py`, `tests/test_tool_contract.py` (only if it enumerates these two tools' CLI flags).

### Explicit Non-Goals
- Do not change `hidden_tests/slice1/`, `hidden_tests/slice2/`, or `hidden_tests/obligations.yaml`'s content — only how `dev_check.py` locates and reads them.
- Do not touch `tools/bench_lib.py` or `tools/cohort_run.py` in this slice — both `resolve_task` and `parse_pinned_plan_commit` already exist from Slice 1; this slice only calls them.
- Do not add task-awareness to `cohort_run.py` yet (Slice 4) or `model_report.py` yet (Slice 3) — this slice's own tests should exercise `dev_check.py`/`grade_run.py` directly, not through the full CLI chain.

### Risk Flags
- Risky surfaces touched: none in the classic sense, but this is the grading-correctness core of the entire bench — a subtle mistake here (e.g. a filename-derivation edge case, or a path resolved against the wrong root) produces a grade that looks plausible but is wrong, which is exactly the failure mode this repo's "fail loudly, never silently degrade" principle exists to prevent. Treat any ambiguity in this slice as a stop-and-ask, not a judgment call.
- Difficulty: **High** — touches the grading-critical path; the filename-derivation change in particular replaces a previously-explicit constant with computed behavior and needs careful edge-case testing (e.g., a slice whose obligation groups reference more than two files, or a node id with a `[param]` suffix per `obligations.yaml`'s own documented-but-never-exercised parametrize caveat); the new run/task cross-check also needs careful testing since it's genuinely new logic, not a refactor.
- Approval needed before implementation: no
- Independent audit required: yes

### Validation Plan
- Tests to add/update: `tests/test_dev_check.py` (task resolution, filename derivation from a fixture obligations block, plan/plan_pin consistency check, run/task repository cross-check, provenance `task_id` field); `tests/test_grade_run.py` (`--task` threading into `dispatch_grade`'s argv); `tests/test_tool_contract.py` if it enumerates `dev_check.py`/`grade_run.py`'s CLI flags.
- Commands to run: `python -m pytest tests/ -q` — the full suite, expected to pass in full (this slice's own regression criterion requires it).
- If a real or recorded `relative-velocity` attempt commit is available, re-grade it before and after this slice and diff the resulting sheet JSON using this slice's explicit field-exclusion list — this is the strongest available regression check and should be run even though it's not a unit test.
- Lint (differential, via the `lint` skill): required.
- Manual checks: read through `dev_check.py`'s full diff against the pre-slice version specifically looking for any remaining hardcoded `hidden_tests`/`slice{N}`/`test_hA.py`/`test_hB.py` reference that should have moved to task resolution.

### Rollback Path
- Revert this slice's commit. `dev_check.py`/`grade_run.py` return to reading their pre-slice flat keys, and this slice's `policy.yaml` edit (deleting the now-redundant `measurement` block) reverts together with it in the same commit, restoring the flat block. Since the full suite passed before and after this slice, revert is clean and total.

---

## Slice 3: `model_report.py` propagates and backfills `task_id`

### Intended Change
- `model_report.py`'s report schema gains a top-level `task_id` field, derived from the run's own graded slice sheets — read, never re-resolved independently against a grading worktree, and validated for internal consistency: every slice of one run must agree on `task_id`, since a run cannot span two tasks. A disagreement is a named `ModelReportError` (the same shape as the existing `resolve_correctness_provenance` disagreement check just above it).
- **Historical backfill** (see the plan's own "Migration approach" section above for why this is needed and why it's sound): a slice sheet whose `provenance` block has no `task_id` (graded before Slice 2 landed) is treated as belonging to `policy["default_task"]`. The report additionally carries `task_id_source: "backfilled"` for this case, versus `"graded"` when every contributing sheet's provenance actually carried `task_id`. A run whose sheets mix backfilled and graded task attribution, or whose sheets disagree even after backfilling, is the same named `ModelReportError` as any other cross-slice disagreement.
- `model_report.py`'s own obligations-loading call site (used to reconstruct first-attempt node outcomes) currently always loads `hidden_tests/obligations.yaml` relative to the bench root, regardless of which task actually graded the run. This must instead resolve the run's own `task_id` (backfilled or graded, per above) via `bench_lib.resolve_task` and load *that* task's `obligations_file` — otherwise a second task's reports would have their node outcomes reconstructed against the wrong rubric even after `task_id` itself is correctly stamped. This may require widening `dev_check.load_obligations`'s signature to accept an explicit path (implementer's choice per "internal helper" discretion in "How rigid this plan is meant to be") — the observable requirement is that `model_report.py` never loads obligations from a fixed bench-root default once a task can be anything other than `relative-velocity`.
- `model_report.py` currently has no `--policy` flag at all (unlike `dev_check.py`/`grade_run.py`/`cohort_run.py`, which all accept one), which becomes a real gap once resolving a task requires reading `policy.yaml`: an operator who graded a run with `--policy custom.yaml` (a supported override today) would otherwise have `model_report.py` silently resolve the task registry from the *default* `policy.yaml` instead, a genuine mismatch risk if the two files define tasks differently. Add `--policy <path>` to `model_report.py`, defaulting to `policy.yaml` at the bench root exactly like the other tools, and use it for the `resolve_task` call this slice adds.
- `resolve_correctness_provenance`'s returned triple gains `task_id` as a sibling field (documented as informational/redundant with the top-level field — the authoritative value lives at `report["task_id"]`, this is a per-slice echo for anything that reads `correctness_provenance` in isolation).

### Acceptance Criteria
- Inputs: a run's set of graded slice sheets, some carrying `provenance.task_id` (graded under Slice 2), some not (pre-migration).
- Outputs:
  - [ ] `model-report.json`'s top level carries `task_id` matching what every graded slice's provenance recorded, or `policy["default_task"]` when backfilled.
  - [ ] `task_id_source` is `"graded"` when every contributing sheet carried `task_id` natively, `"backfilled"` when it was inferred for a pre-migration sheet.
  - [ ] A run whose slices disagree on `task_id` (after backfilling) raises `ModelReportError` naming the run id and the differing values.
  - [ ] A run graded entirely under Slice 2's `relative-velocity` default produces `task_id: "relative-velocity"`, `task_id_source: "graded"`, and is otherwise unchanged from today's `model-report.json` shape.
  - [ ] `model_report.py`'s reconstructed first-attempt node outcomes are built from the resolved task's own `obligations_file`, not always `hidden_tests/obligations.yaml` at the bench root — verified by a fixture task whose obligations file lives at a different path and confirming that path is actually read.
  - [ ] Re-running `model_report.py` for an already-existing `relative-velocity` run graded entirely before this slice landed, using its original `--run-dir` (only if that path still exists on disk — an explicitly-given but missing `--run-dir` is a hard failure today, per `model_report.py`'s own existing `--run-dir` validation, and must never be passed once stale) and original `--policy` if one was used, produces `task_id: "relative-velocity"`, `task_id_source: "backfilled"`, with every other field the tool can still resolve unchanged from what it produced before this slice. For a run whose `--run-dir` no longer exists, re-running with the flag omitted entirely (the tool's own standard `--run-id`-only form) must still succeed, backfilling `task_id` correctly while any `--run-dir`-dependent field is reported the way `model_report.py` already reports an unavailable input when `--run-dir` is omitted today — named and explicit, never silently blanked or fabricated; this slice does not need to invent new fallback behavior for that case, only preserve whatever `model_report.py` already does when `--run-dir` isn't supplied.
  - [ ] `model_report.py --policy <path>` resolves the task registry from the given policy file, not the bench-root default, verified by a fixture where the two files define the `relative-velocity` task's `obligations_file` differently and confirming the explicitly-passed one is the one actually read.
- User-visible behaviour: every existing `model_report.py` invocation with no `--policy` flag keeps working unchanged, since `--policy` defaults to today's implicit bench-root `policy.yaml` — the only new user-facing surface is the flag itself.
- Behaviour that must not change: every other field of `model-report.json`.

### Authorized Surface
- Files allowed to change:
  - `tools/model_report.py`
  - `tools/dev_check.py` (only to widen `load_obligations`'s signature to accept an explicit path if the implementer chooses that approach — no other change; if a different approach avoids touching `dev_check.py`, prefer that and leave this file untouched)
  - `tests/test_model_report.py`
- Functions/classes/components allowed to change: `model_report.resolve_correctness_provenance` (gains `task_id`), `model_report.build_report` (gains top-level `task_id`, `task_id_source`, and its cross-slice consistency/backfill logic), the obligations-loading call site used for first-attempt node-outcome reconstruction, `model_report.parse_args`'s new `--policy` argument and `model_report.main`'s use of it, optionally `dev_check.load_obligations`'s signature (see above).
- Tests allowed or expected to change: `tests/test_model_report.py`, `tests/test_dev_check.py` only if `load_obligations`'s signature changed.

### Explicit Non-Goals
- Do not touch `leaderboard.py` in this slice — it does not yet read `task_id` (that's Slice 5). This slice only makes the field exist, be correct, and be backfillable.
- Do not write a standalone migration script or a new CLI flag for the historical backfill — it happens automatically through `model_report.py`'s existing full-rebuild-on-every-run behavior, triggered by a plain re-run of the existing command, once per historical run id, as documented in this plan's own "Migration approach" section.
- Do not mutate any existing `slice-<N>.json` sheet file — the backfill is read-side only, in `model_report.py`, never a rewrite of `dev_check.py`'s already-captured provenance.

### Risk Flags
- Risky surfaces touched: none.
- Difficulty: **Medium** — the `task_id` propagation itself follows the exact pattern `plan_hash`/`obligations_hash`/`hidden_tests_hash` already use one function above it in the same file, but the backfill logic and the obligations-loading fix are genuinely new behavior that needs its own careful tests, not a pure refactor.
- Approval needed before implementation: no
- Independent audit required: no

### Validation Plan
- Tests to add/update: `tests/test_model_report.py` — `task_id` propagation, the cross-slice-disagreement error case, the default-task passthrough case, the backfill case (missing `provenance.task_id` → `default_task` + `task_id_source: "backfilled"`), and the task-resolved obligations-loading fix.
- Commands to run: `python -m pytest tests/test_model_report.py -q`; then, against the real `results/runs/` tree, re-run `model_report.py` (with the same `--run-dir`/`--policy` its original invocation used, per this plan's "Migration approach") for at least one real pre-existing run and confirm the backfill fields appear correctly and every other field the tool can resolve is unchanged.
- Lint (differential, via the `lint` skill): required.
- Manual checks: confirm the one-time historical-regeneration step is documented somewhere the operator will actually see it before running Slice 5's leaderboard build (this plan's own README update in Slice 8 is the durable home for it; note it here too so it isn't lost between slices).

### Rollback Path
- Revert this slice's commit; `model_report.py` returns to not emitting `task_id`/`task_id_source`, which is safe since nothing yet consumes them.

---

## Slice 4: `cohort_run.py` becomes task-aware

### Intended Change
- Add `--task <id>` to the `setup`, `analyze`, `analyze-all`, and `cleanup` subcommands, resolved via `bench_lib.resolve_task` and used in place of the flat `relative_velocity_repo`/`dev_branch_prefix`/`dev_worktree_root` reads and the hardcoded `_FROZEN_PLAN_RELATIVE_PATH`/`_PROVENANCE_RELATIVE_PATH` module constants. Once every use of these flat keys/constants in `cohort_run.py` is switched to task resolution, delete `relative_velocity_repo`, `dev_branch_prefix`, and `dev_worktree_root` from `policy.yaml` — this slice is their last reader.
- For `analyze`/`analyze-all`, when `--task` is omitted: resolve it by checking, for each configured task, whether the run's worktree (`--dev-repo`, or each worktree `analyze-all` discovers) satisfies `bench_lib.repo_belongs_to_task` against that task's configured repo — the same helper Slice 2 already uses for `dev_check.py`'s own run/task cross-check, not a second, independently-written implementation of the same worktree-membership logic. Zero or more than one matching task is a named `CohortRunError` telling the operator to pass `--task` explicitly — never a silent guess. When exactly one task is configured (today's starting state), this resolves unambiguously by construction and is a no-op change in practice.
- `analyze`/`analyze-all` pass the resolved `--task` down to `grade_run.py`.
- `analyze`'s own pipeline (`run_analyze`, which today already forwards an explicit `--policy` override to grading and to `leaderboard.py`) must also forward that same `--policy` to the `model_report.py` call it makes internally, now that Slice 3 gives `model_report.py` its own `--policy` flag — otherwise an operator's `--policy` override would apply to grading and the leaderboard but silently not to report generation in between, a real gap plan review flagged. This closes the loop for the normal `cohort_run.py analyze`/`analyze-all` path; a bare, direct `model_report.py --policy ...` invocation (e.g. during the Slice 3 historical-migration step) already works from Slice 3 alone.
- `analyze-all`'s discovery (today scoped to one `relative_velocity_repo`/`dev_branch_prefix` pair) iterates every configured task's repo/branch-prefix pair, tagging each discovered ungraded run with its owning task id.
- `_PLAN_NOTE`'s hardcoded "this bench has exactly one frozen plan" string becomes task-aware (a function of the resolved task rather than a fixed constant): it should name the resolved task and its plan file, and, when more than one task is configured, say so accurately rather than claiming exclusivity.

### Acceptance Criteria
- Inputs: `policy.yaml` with one configured task (`relative-velocity`, as after Slices 1–3) and, for new-behavior tests, a fixture `policy.yaml` with two.
- Outputs:
  - [ ] `cohort_run.py setup` (no `--task`) behaves identically to today against the single-task `policy.yaml` — same worktree/branch naming, same printed prompt, same plan-file resolution.
  - [ ] `cohort_run.py setup --task relative-velocity` behaves identically to the no-flag case.
  - [ ] Against a two-task fixture policy, `analyze --dev-repo <path unambiguously under task A's repo>` resolves task A without `--task`; `analyze --dev-repo <path under neither task's repo>` raises `CohortRunError` naming the ambiguity/absence.
  - [ ] `analyze-all` against a two-task fixture discovers ungraded runs under both tasks' worktrees and grades each against its own task.
  - [ ] The printed `_PLAN_NOTE` names the actually-resolved task and its actual plan file path, and does not claim there's only ever one plan once more than one task is configured.
  - [ ] `cohort_run.py analyze --policy custom.yaml ...` passes that same `custom.yaml` to the `model_report.py` call it makes internally, not just to grading and `leaderboard.py` — verified by a fixture where the default and custom policy files define the resolved task's `obligations_file` differently, confirming the report is built against the custom one.
- User-visible behaviour: every documented `README.md` invocation (all of which omit `--task` today) keeps working unchanged for the existing single-task cohort.
- Behaviour that must not change: worktree/branch creation, cleanup semantics, and the printed launcher-prompt substitution logic for the existing task.

### Authorized Surface
- Files allowed to change:
  - `policy.yaml` (only to delete the now-fully-migrated `relative_velocity_repo`/`dev_branch_prefix`/`dev_worktree_root` keys — no other change)
  - `tools/cohort_run.py`
  - `tests/test_cohort_run.py`
- Functions/classes/components allowed to change: `cohort_run.run_setup`, `cohort_run.resolve_ungraded_run_dirs`, the `analyze`/`analyze-all`/`cleanup` command handlers (including `run_analyze`'s existing `--policy`-forwarding call sites, which must add the `model_report.py` call to the set they already forward to for grading and `leaderboard.py`), `cohort_run._PLAN_NOTE` (becomes a function, not a constant, since it needs the resolved task to render), `cohort_run.parse_args`'s subcommand argument definitions.
- Tests allowed or expected to change: `tests/test_cohort_run.py`.

### Explicit Non-Goals
- Do not implement the cross-machine iCloud-sync locking/coordination this investigation flagged — that's a documentation-only concern, handled in Slice 8.
- Do not change branch-naming convention to embed the task id (`pm-eval-v2/<task>/<label>`) — task ownership is derived structurally from git worktree membership instead (see Intended Change), which needs no naming convention change and keeps existing branch names stable.

### Risk Flags
- Risky surfaces touched: none (operator-local CLI tooling, no external consumers of its flags).
- Difficulty: **Medium** — mechanical flag threading across four subcommands in a large file, plus one genuinely new piece of logic (the worktree-membership task resolution) that needs its own dedicated tests, not just "does it still work with one task."
- Approval needed before implementation: no
- Independent audit required: no

### Validation Plan
- Tests to add/update: `tests/test_cohort_run.py` — task resolution via worktree membership (unambiguous, ambiguous, absent cases), `--task` threading into each subcommand, `_PLAN_NOTE` rendering for one- and two-task fixtures, and full regression of every existing single-task test.
- Commands to run: `python -m pytest tests/test_cohort_run.py -q`.
- Lint (differential, via the `lint` skill): required.
- Manual checks: run `cohort_run.py setup --harness claude` (or whichever harness is available) once against the real `relative-velocity` substrate and confirm the printed prompt/worktree exactly match pre-slice output (aside from `_PLAN_NOTE`'s wording).

### Rollback Path
- Revert this slice's commit; `cohort_run.py` returns to reading the flat keys this slice deleted, and the `policy.yaml` edit reverts in the same commit, restoring them together. Clean and total.

---

## Slice 5: `leaderboard.py` partitions Developer tables by task

### Intended Change
- `discover_reports` requires `task_id` as a new top-level required key (added to `_REQUIRED_REPORT_KEYS`) — a report missing it is a named, loud `LeaderboardError`, never silently defaulted to the existing task. (See this plan's "Migration approach": every real historical report needs one re-run of `model_report.py`, per Slice 3, before it will satisfy this check — that re-run is what actually backfills the field, not this slice.)
- Add a partitioning step (new function, e.g. `partition_reports_by_task`) that groups discovered reports by `task_id` before any of today's aggregation runs.
- `build_leaderboard` runs the existing pipeline — `group_reports_by_model`, `aggregate_model`, `_check_correctness_provenance_consistency` — once per task partition, unchanged internally, and assembles one full Developer "first submission" / "supervised outcome" table pair **per task** in the output, each clearly labelled with its task id, rather than one global table.
- `load_leaderboard_policy`'s single `expected_slices` read is replaced by reading each task's own `expected_slices` (via `bench_lib.resolve_task`) and threading it into that task's own `compute_run_coverage` calls. Once this is done, delete the top-level `leaderboard.expected_slices` key from `policy.yaml` — this slice is its last reader, and once it's gone the now-empty `leaderboard:` section is removed too.
- `results/leaderboard.md`'s rendering gains a per-task section header (e.g. `## Task: relative-velocity`) wrapping that task's existing table structure, so a reader can never mistake one task's rows for another's — this generalizes today's single, unlabelled `# Leaderboard` structure without changing its content for a single-task cohort beyond adding the section header itself.
- `results/leaderboard.json`'s top-level shape changes to hold a mapping keyed by task id (exact shape is this slice's implementation choice, per "How rigid this plan is meant to be" above) rather than one flat structure — nothing outside this repo's own tools/tests reads this file today (per `AGENTS.md`), so this is a controlled, internal schema evolution.

### Acceptance Criteria
- Inputs: the existing `results/runs/` tree (all `relative-velocity`; every report must already have been regenerated per Slice 3's one-time backfill step, or this slice's own missing-`task_id` check will correctly refuse them — do that regeneration first if it hasn't happened yet), plus a synthetic two-task fixture (fabricated `model-report.json` pairs with two distinct `task_id`s) for new-behavior tests.
- Outputs:
  - [ ] Rebuilding the leaderboard from the real, single-task `results/runs/` tree (after the Slice 3 regeneration step) produces a Developer ranking table for `relative-velocity` whose ranking, correctness figures, and supporting columns are unchanged from the pre-slice `leaderboard.json`/`.md` (aside from the new task-partitioned structure/section header) — this is checked by comparing against a saved pre-slice `leaderboard.json` for every numeric field.
  - [ ] A two-task fixture produces two independent, correctly-scoped Developer tables — no configuration's correctness number from task A appears mixed into task B's table or vice versa.
  - [ ] A report missing `task_id` fails `discover_reports` loudly, naming the file (and, in the real tree, this is the expected/correct outcome for any report not yet regenerated per Slice 3 — not a bug in this slice).
  - [ ] `_check_correctness_provenance_consistency`'s existing per-slice-number hash check still runs, now scoped within each task partition (never across partitions) — verified by a fixture where two tasks happen to reuse the same slice *number* with different hashes and the build succeeds (rather than today's accidental cross-task collision-refusal behavior, which this slice supersedes with real partitioning).
  - [ ] The `reviewers` block (built by `aggregate_reviewers`, not yet touched by this slice — see Explicit Non-Goals) stays exactly as it is today: a single, non-task-partitioned top-level structure, unchanged in shape or content by this slice's restructuring of the Developer tables. This is a deliberate, temporary asymmetry — Slice 6 partitions it next — not an oversight; a reviewer whose findings span two tasks will still be pooled globally until Slice 6 lands, and that is expected and acceptable for this slice alone.
- User-visible behaviour: `leaderboard.py`'s CLI flags are unchanged (it still discovers everything under `--results-dir`/`results/runs` and needs no new flag — task partitioning happens automatically from the data).
- Behaviour that must not change: `aggregate_model`'s own internal correctness/coverage/attempt-trajectory computation logic — this slice changes *when and how many times* it's invoked, not what it computes.

### Authorized Surface
- Files allowed to change:
  - `policy.yaml` (only to delete the now-fully-migrated top-level `leaderboard.expected_slices` key and the resulting empty `leaderboard:` section — no other change)
  - `tools/leaderboard.py`
  - `tests/test_leaderboard.py`
- Functions/classes/components allowed to change: `leaderboard.discover_reports` (`task_id` added to `_REQUIRED_REPORT_KEYS`), a new `partition_reports_by_task` (or equivalently named) function, `leaderboard.build_leaderboard`, `leaderboard.load_leaderboard_policy` (now reads per-task `expected_slices` via `bench_lib.resolve_task` rather than a flat `leaderboard.expected_slices`), `leaderboard.compute_run_coverage`'s `expected_slices` parameter source, the markdown/JSON rendering functions for the Developer tables. Not `aggregate_reviewers`/`_UnionFind` (see Explicit Non-Goals) — those stay exactly as they are today in this slice.
- Tests allowed or expected to change: `tests/test_leaderboard.py`.

### Explicit Non-Goals
- Do not touch `aggregate_reviewers`/`_UnionFind` in this slice — that's Slice 6, kept separate because it's a distinct code region with its own risk profile.
- Do not implement the cross-task standing table yet — that's Slice 7 and depends on this slice's per-task partitioning existing first.

### Risk Flags
- Risky surfaces touched: none in the classic sense, but this is the highest-blast-radius slice in the plan — it changes the core ranking output every other slice and the operator's own trust in the tool depend on. Any silent mis-partitioning here (e.g. a task boundary leaking) is exactly the failure mode this whole plan exists to prevent, so treat it with the same care as Slice 2.
- Difficulty: **High** — largest file in the repo, most existing tests and README-documented output shape to preserve, and the partition-then-aggregate restructuring touches the top-level control flow of `build_leaderboard` directly.
- Approval needed before implementation: no
- Independent audit required: yes

### Validation Plan
- Tests to add/update: `tests/test_leaderboard.py` — the full existing test suite must keep passing unchanged in spirit (single-task behavior preserved), plus new tests for: two-task partitioning correctness, the missing-`task_id` refusal, and the scoped provenance-consistency check.
- Commands to run: `python -m pytest tests/test_leaderboard.py -q`; then, after regenerating every real run's `model-report.json` per Slice 3's step, `python tools/leaderboard.py` against the real `results/` tree and diff the resulting `leaderboard.json` against a saved pre-slice copy (every numeric field must match; structural/labelling differences are expected and should be reviewed by eye against `results/leaderboard.md`).
- Lint (differential, via the `lint` skill): required.
- Manual checks: read the regenerated `results/leaderboard.md` in full and confirm it reads cleanly as "one task, clearly labelled" rather than losing any of today's detail sections.

### Rollback Path
- Revert this slice's commit; its `policy.yaml` edit (restoring `leaderboard.expected_slices`) reverts together with it. Before doing so, restore `results/leaderboard.json`/`.md` from the pre-slice saved copy if this slice's rebuild already overwrote them on disk (they're gitignored generated output, so git revert alone won't restore them) — re-running `tools/leaderboard.py` from the pre-slice code against the still-intact `results/runs/` tree is the actual recovery path.

---

## Slice 6: `leaderboard.py` reviewer scoring scoped per task

### Intended Change
- `aggregate_reviewers` is called once per task partition (reusing Slice 5's partitioning), so its PM-rating pool and `_UnionFind` opponent-group connectivity are computed **within one task's reports only** — closing the live gap this plan's originating investigation flagged: a reviewer identity that reviews both tasks currently would (once two tasks exist) bridge two otherwise-disconnected opponent groups and falsely report cross-task "global comparability," and PM ratings from two tasks would pool into one mean with no check at all.
- No change to `_rank_points`'s per-round math or `_UnionFind`'s own algorithm — only the scope of what's fed into one `_UnionFind` instance and one accumulator set.

### Acceptance Criteria
- Inputs: the same real single-task tree plus a synthetic two-task fixture where the *same* reviewer identity (tool/model/effort) appears in panel rounds for both tasks.
- Outputs:
  - [ ] Rebuilding against the real, single-task tree produces reviewer tables (`Code reviewer`, `Drift reviewer`) numerically unchanged from pre-slice output.
  - [ ] In the two-task fixture, that shared reviewer identity gets an **independent** PM-rating mean and comparative-rank score per task — never one pooled mean across both.
  - [ ] In the two-task fixture, that shared identity's `comparative_globally_comparable` flag is evaluated per task (true/false independently for task A and task B), never bridging the two tasks' otherwise-disconnected opponent groups into one falsely-comparable component.
- User-visible behaviour: reviewer tables in `results/leaderboard.md` are now sectioned per task, matching Slice 5's Developer-table sectioning.
- Behaviour that must not change: `_rank_points`'s normalized-rank-point computation for any single round.

### Authorized Surface
- Files allowed to change:
  - `tools/leaderboard.py`
  - `tests/test_leaderboard.py`
- Functions/classes/components allowed to change: `leaderboard.aggregate_reviewers`, `leaderboard._UnionFind`'s call sites (not its own algorithm — see Explicit Non-Goals), `leaderboard.build_leaderboard`'s invocation of `aggregate_reviewers` (moves from once-globally to once-per-task-partition), the reviewer-table markdown/JSON rendering to add per-task sectioning.
- Tests allowed or expected to change: `tests/test_leaderboard.py`.

### Explicit Non-Goals
- Do not change how a single review round's rank points are computed — only what pool of reports/rounds is fed into the accumulation.

### Risk Flags
- Risky surfaces touched: none.
- Difficulty: **Medium** — the change itself is a scoping change to an already-well-isolated function (`aggregate_reviewers`), but the test fixture needed to actually exercise the cross-task-bridge bug requires careful construction to be a real regression test rather than a vacuous one.
- Approval needed before implementation: no
- Independent audit required: yes

### Validation Plan
- Tests to add/update: `tests/test_leaderboard.py` — the shared-reviewer-across-two-tasks fixture described above is the load-bearing new test; without it this slice's actual fix is unverified.
- Commands to run: `python -m pytest tests/test_leaderboard.py -q`.
- Lint (differential, via the `lint` skill): required.
- Manual checks: none beyond the above.

### Rollback Path
- Revert this slice's commit; reviewer scoring returns to Slice 5's per-task Developer-table partitioning with reviewer tables still pooled globally (safe for a single-task cohort, latent for a future second one).

---

## Slice 7: Cross-task standing table

### Intended Change
- Add a new, clearly-separate derived table (e.g. `Cross-task standing`) to `leaderboard.py`'s output: for each Developer configuration, compute its percentile rank of first-attempt correctness *within* each task's own field, then average those percentile ranks equally across every task the configuration appears in. Do the same, separately, for reviewer comparative-rank scores once Slice 6's task-scoped `_UnionFind` components exist — the exact rule, stated once here and nowhere else, so it is never restated ambiguously elsewhere in this slice: a reviewer identity's comparative score for a given task contributes to that identity's cross-task average **only when that task's own `comparative_globally_comparable` flag (Slice 6) is `True` for that identity** (i.e. exactly one connected component in that task's reviewer field, or this identity's component is the only one). A task where that flag is `False` for this identity, or where the identity has no comparative score at all, is excluded from this identity's cross-task average exactly as if the identity hadn't participated in that task — never averaged in as a lower or default value.
- **Percentile-rank formula, pinned exactly** to match this codebase's own existing tie convention (`_rank_points`) rather than inventing a new one: for a task's field of N eligible configurations (N = the count eligible for that task's first-submission ranking, per Slice 5's own eligibility rule), sort descending by first-attempt correctness, assign each tied group the mean of its occupied 1-based rank positions, then `percentile_rank = (N - mean_rank) / (N - 1)` for N > 1 — exactly `_rank_points`'s own `(total - mean_rank) / (total - 1)`, reapplied here to Developer correctness instead of reviewer panel rank. For `N == 1` (the task's field has exactly one eligible configuration), define percentile rank as `1.0` for that sole configuration, labelled `"n=1 field"` in the rendered table — distinct from the `"n=1 task"` label for a configuration appearing in only one task; both facts can co-occur and both must be visible when they do.
- A configuration ineligible for a given task's first-submission ranking (per Slice 5's coverage rule) is excluded from that task's field entirely — both from the percentile-rank computation for other configurations, and from its own cross-task average's set of contributing tasks. It is never scored as 0 for that task and never silently dropped from the rendered table; render its row for that task as `"not eligible for task <id>"`.
- This table is additive: it must never alter any task's own correctness number, ranking, or coverage/eligibility logic. It is computed strictly *after* every task's own tables are final, reading from them, never the reverse.
- A configuration appearing in only one task gets a cross-task standing equal to that one task's percentile rank, clearly labelled `"n=1 task"` so a reader doesn't mistake it for a genuinely cross-task-validated number.

### Acceptance Criteria
- Inputs: Slice 5/6's per-task tables, real (single-task) and a synthetic two-task fixture.
- Outputs:
  - [ ] Against the real single-task tree, the cross-task standing table's values equal each configuration's within-task percentile rank exactly (`"n=1 task"` everywhere), and every existing table/number is byte-for-byte unchanged.
  - [ ] Against a two-task fixture with known, hand-computed percentile ranks (including a tied pair), the cross-task standing table's averaged values match the hand computation exactly, using the formula pinned in Intended Change.
  - [ ] A task field of size N=1 reports percentile rank `1.0`, labelled `"n=1 field"`.
  - [ ] A configuration ineligible for one task's first-submission ranking is visibly excluded from that task's contribution to its own cross-task average, rendered as `"not eligible for task <id>"`, never silently as 0 or as a dropped row.
  - [ ] Reviewer cross-task standing (for `code-review` and `drift-audit` separately) is verified against its own hand-computed two-task fixture, applying exactly the rule stated in Intended Change: a reviewer identity whose `comparative_globally_comparable` flag is `False` for a given task (or who has no comparative score in it) contributes only its remaining, comparable task(s) to its own cross-task average, and a reviewer with zero comparable tasks anywhere gets no cross-task standing at all, never a fabricated one.
  - [ ] No task's own `Developer -- first submission`/`-- supervised outcome` table, or its ranking order, changes as a result of this slice existing.
- User-visible behaviour: one new table/section appears in `results/leaderboard.md`, clearly separated from and after every task's own tables, with a glossary entry explaining it is a derived, never-authoritative-on-its-own standing measure.
- Behaviour that must not change: every existing table's content and ranking order.

### Authorized Surface
- Files allowed to change:
  - `tools/leaderboard.py`
  - `tests/test_leaderboard.py`
- Functions/classes/components allowed to change: a new cross-task standing computation (e.g. `compute_cross_task_standing`) reading Slice 5/6's finished per-task tables, plus its markdown/JSON rendering and glossary entry. Must not modify any function Slices 5/6 already finalized except to call the new one.
- Tests allowed or expected to change: `tests/test_leaderboard.py`.

### Explicit Non-Goals
- Do not implement Bradley-Terry/pairwise win-rate or any scheme that fabricates a head-to-head comparison between configurations that never ran the same task — rejected explicitly by this plan's originating investigation as inventing evidence that doesn't exist.
- Do not blend this table's numbers into any task's own correctness score, ranking order, or eligibility computation.
- Do not attempt z-score normalization in this slice — percentile rank was chosen specifically because this bench's typical run counts (`policy.yaml` `repeats`) are too small to trust a standard deviation; revisit only if a future policy change substantially raises typical repeat counts, and treat that as a new slice, not a silent substitution here.

### Risk Flags
- Risky surfaces touched: none.
- Difficulty: **Medium** — new, additive, well-isolated logic with a precisely pinned mathematical contract that's straightforward to unit-test against hand-computed fixtures, but easy to get subtly wrong (tie handling, configurations present in only one task, empty-task edge cases, the reviewer-side opponent-component interaction) if rushed.
- Approval needed before implementation: no
- Independent audit required: no

### Validation Plan
- Tests to add/update: `tests/test_leaderboard.py` — hand-computed two-task percentile-rank fixture (including a tie case, an N=1 field case, an ineligible-configuration case, and a single-task-only configuration case) for the Developer side, plus a separate hand-computed fixture for reviewer cross-task standing exercising the disconnected-opponent-component case, plus a regression check that no existing table changes.
- Commands to run: `python -m pytest tests/test_leaderboard.py -q`.
- Lint (differential, via the `lint` skill): required.
- Manual checks: read the rendered cross-task table in `results/leaderboard.md` for legibility — this is a UX-motivated feature, so a table a human can't parse at a glance is a real defect even if the numbers are correct.

### Rollback Path
- Revert this slice's commit; the new table/section disappears, every other table is unaffected (it was never a dependency of anything else).

---

## Slice 8: Documentation

### Intended Change
- `README.md`: document the `tasks:` policy schema, the `--task` flag on every tool that now accepts one, how task resolution/auto-detection works in `cohort_run.py analyze`/`analyze-all`, the per-task leaderboard sectioning, the new cross-task standing table (with its own glossary entry, matching the existing glossary's style), and **the one-time historical-backfill step** from Slice 3's "Migration approach" (re-run `model_report.py` once per pre-existing run, before trusting Slice 5's leaderboard for the historical cohort: pass the run's original `--run-dir`/`--policy` if that trial worktree still exists — ideally by doing this before running `cohort_run.py cleanup` on it — and omit `--run-dir` entirely, never a stale path, for a run whose worktree is already gone) — this is an operational step a real operator must actually perform once, so it needs a durable, easy-to-find home, not just this plan document. Also add a short, explicit section documenting the multi-machine iCloud-synced `results/` dir assumptions this plan's originating investigation flagged: rebuilds are idempotent/regenerable and safe to re-run on failure; avoid running `leaderboard.py`/`analyze-all` literally simultaneously from both machines (last-write-wins on the shared files); a `model-report.json` read mid-iCloud-sync fails loudly (named `JSONDecodeError`/refusal) rather than silently corrupting anything, so a build failure immediately after a sync is worth a simple retry before treating it as a real bug.
- `AGENTS.md`: fold in the task-registry design decision (per its own stated rule: "Fold a design decision into this file... not only into HANDOFF.md") — a short paragraph stating that task configuration lives in `policy.yaml`'s `tasks:` map, resolved via `bench_lib.resolve_task`, that `task_id` is stamped at grading time (or backfilled to `default_task` for pre-migration data, explicitly marked `task_id_source: "backfilled"`) and never re-derived downstream, and that grading/leaderboard partitioning is scoped per task by construction, not by convention.

### Acceptance Criteria
- Inputs: the finished behavior of Slices 1–7.
- Outputs:
  - [ ] `README.md` accurately describes every new flag and behavior added by this plan, with no remaining reference to "this bench tests exactly one frozen plan" as a structural claim (it may still note that only one task is populated today, as a fact, distinct from a structural limitation), and includes the historical-backfill operational step.
  - [ ] `AGENTS.md` records the task-registry design decision per its own documented convention.
- User-visible behaviour: none (docs only).
- Behaviour that must not change: nothing code-facing.

### Authorized Surface
- Files allowed to change:
  - `README.md`
  - `AGENTS.md`
- Functions/classes/components allowed to change: none (prose only).
- Tests allowed or expected to change: none.

### Explicit Non-Goals
- Do not edit `docs/OBLIGATION-GROUPS.md`, `docs/MERGER_RATE_PLAN-2SLICE.md`, or its provenance file — unrelated to this plan's scope.

### Risk Flags
- Risky surfaces touched: none.
- Difficulty: **Low**.
- Approval needed before implementation: no
- Independent audit required: no

### Validation Plan
- Tests to add/update: none (docs-only slice).
- Commands to run: none beyond lint.
- Lint (differential, via the `lint` skill): required (`markdownlint`/`codespell` per this repo's `lint` skill).
- Manual checks: read `README.md` end to end as a brand-new operator would, confirming the 4-step flow (now task-aware) is still followable without needing this plan document as context.

### Rollback Path
- Revert this slice's commit; no functional impact either way.

---

## Next Chat Prompts

### Mode A — Assisted run (default, checkpointed)

```md
Plan file: docs/plans/multi-task-support-plan.md
Slices or batch this session: Slice 1

Read the full plan file first. If a selected slice or batch receipt is incomplete or the plan state is unclear, stop and tell me before coding.

Work on the current feature branch for this plan; if none exists, create one and tell me the name.

Use orchestrator as the controlling skill. Act as the Developer: keep implementation, validation, Git operations, and commits local. Use a read-only Reviewer only for investigation, evidence gathering, the hostile drift-audit skill, and an independent code-review skill pass. If no Reviewer is configured or available, perform Developer self-audit and record that provenance explicitly. Slices 2, 5, and 6 are marked `Independent audit required: yes` in the plan -- for those, a genuinely independent Reviewer (not Developer self-audit) is required, not optional.

For each selected slice or batch, in plan order:
1. Restate the frozen contract (authorized surface + non-goals) from the plan, and re-read the plan's "How rigid this plan is meant to be" and "Migration approach" sections so you apply its flexibility and backfill rules correctly rather than treating every prose detail as frozen or missing the historical-data step.
2. If any included slice's Risk Flags mark approval-needed, stop and get my approval before coding.
3. apply the scoped-implementation skill against the selected contract.
4. apply the drift-audit skill using a read-only Reviewer when available; otherwise perform Developer self-audit. Report the authorization gate result and who performed it before any quality review.
5. If the gate passes: for a broad or structural change, first run the code-health skill differentially against the slice's starting commit and supply its report as review evidence. Then apply the code-review skill using a read-only Reviewer when available (mandatory, not optional, for a slice marked `Independent audit required: yes`); otherwise perform Developer self-audit through the code-review skill. Record who performed it. If the drift gate fails, fix the drift and re-audit.
6. Surface drift and review findings to me, fix them, then re-run the relevant gate. If consecutive reviews return only minor findings and have clearly converged record residuals in the slice summary and proceed.
7. Ask me before committing. On my approval, commit the selected slice or batch with the commit skill.

After the selected slice(s) or batch are committed, use the handoff skill to record state, audit provenance (Reviewer tool/label or Developer self-audit and fallback context), and the next slice to resume from (this plan has a strict dependency chain -- Slice 1 before 2, 2 before 3, 3 before 4 (Slice 4 forwards `--policy` to the `model_report.py` flag Slice 3 adds), 5 before 6 before 7, all before 8; and before Slice 5's leaderboard build is trusted for the real historical cohort, Slice 3's one-time `model_report.py` regeneration step must have been run for every existing run). Do not continue past the selected scope.

Confirm before starting: plan file read, selected slice(s), branch, and the first slice. Then begin.
```

### Mode B — Supervised autonomy (alternative)

```md
Plan file: docs/plans/multi-task-support-plan.md
Repo: /Users/dcroton/Local/git-repos/ai-agent-bench
Developer: harness <codex|claude|copilot|opencode|qwen> model <model name>
Reviewer: harness <codex|claude|copilot|opencode|qwen> model <model name>

Use the project-manager skill. You are the PM: the accountable supervisor of this run — you never write slice code yourself.

Start the run for this plan and repo on the Developer harness above, with the Reviewer harness/model as your default for commissioned reviews — turn it into a wider review panel yourself, per slice, if the risk warrants it. Keep the run token the toolkit gives you to yourself; never pass it to a Developer or Reviewer session.

Then, slice by slice, in plan order:
1. Launch a fresh Developer session scoped to that slice's frozen contract.
2. Wait on it with a single long `observe --wait` rather than repeated checks; nudge it only if it genuinely stalls, and otherwise let the session's own signal — result, death, or a dialog marker — end the wait.
3. Assess what it produced against the plan, the diff, and the validation evidence; run lint, investigate differential code-health when structure materially changed, and commission an independent review when risk warrants it. A review blocks until it returns or its timeout kills it; leave it to run rather than watching it.
4. Record your decision: accept, send it back for correction, or stop for a human — whichever the evidence and the plan's gates call for.

Stop the run and tell me whenever the plan or the mechanical floor requires a human decision, rather than making that call yourself.

Confirm before starting: plan file read, Developer and Reviewer harness/model, and the first slice. Then begin.

When every slice is decided, report from the run record: total run time (double check this), what was accepted and on what evidence, what stopped and why, and any residual risk I should know about.
```
