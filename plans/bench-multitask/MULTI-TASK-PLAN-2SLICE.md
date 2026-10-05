# Implementation Plan: Multi-Task Support for ai-agent-bench

## Purpose and scope

Today this bench is hardwired to exactly one scientific task: one target repo (`relative-velocity`), one frozen plan (`docs/MERGER_RATE_PLAN-2SLICE.md`), one hidden-test suite (`hidden_tests/slice1|2` + `hidden_tests/obligations.yaml`). This plan makes the harness's grading path able to grade a **second** scientific task (a different target repo, plan, and hidden-test suite) side by side with the first, without any risk of the two tasks' scores silently blending at grading time. Propagating the task onto `model-report.json`, partitioning the leaderboard by task, making `cohort_run.py` task-aware, and any cross-task ranking are deliberately outside this plan (see Non-goals).

This plan does **not** onboard an actual second task — no second repo, plan, or hidden-test suite is created here. It builds the mechanism; picking and vending a second scientific target is deliberate future work, done once this lands. It also does not touch anything about how the *current* task (`relative-velocity`) is graded, scientifically speaking: `hidden_tests/`, `docs/MERGER_RATE_PLAN-2SLICE.md`, and `docs/OBLIGATION-GROUPS.md` are not edited anywhere in this plan — only the code that currently hardcodes their paths changes, to read them from policy instead.

### Non-goals (explicit, for every slice below)

- No second real task is added. Multi-task behavior is validated with synthetic fixtures (fabricated `model-report.json`/`policy.yaml` test data with two distinct `task_id`s), never a live second PM run.
- No change to the frozen plan document, hidden-test bodies, or `hidden_tests/obligations.yaml`'s existing content for `relative-velocity`.
- The PM (supervisor) seat stays unranked and unvaried — out of scope, per the investigation that produced this plan.
- No change to `review_score.py` — it harvests purely from `run.json` + `policy.yaml`'s `review_identity.corrections` and has no task-specific logic to generalize.
- No renaming or removal of any *existing* CLI flag's current behavior. Every new `--task` flag is additive and optional, defaulting to the resolved `default_task`, so every command an operator runs today keeps working unchanged with zero policy.yaml edits.
- No change to `tools/model_report.py`. Propagating `task_id` onto `model-report.json` and backfilling it for historical sheets are out of scope; the `task_id` Slice 2 stamps into each attempt's provenance therefore has no reader within this plan, deliberately — it is the structural fact later work consumes.
- No change to `tools/cohort_run.py` beyond Slice 1's `parse_pinned_plan_commit` relocation. Task-aware `cohort_run.py` (a `--task` flag on its subcommands, inferring a run's task from worktree membership, discovery across several tasks, a task-aware `_PLAN_NOTE`) is out of scope; it keeps reading `relative_velocity_repo`/`dev_branch_prefix`/`dev_worktree_root` exactly as today.
- No change to `tools/leaderboard.py`. Partitioning reports by `task_id`, per-task `expected_slices`, per-task reviewer scoring and any cross-task standing table are out of scope; it keeps reading `leaderboard.expected_slices` and pooling globally, which is correct while exactly one task is populated.
- No documentation slice: `README.md` and `AGENTS.md` are not edited by this plan.

## Design overview

- **`policy.yaml` gets a `tasks:` map**, keyed by an operator-chosen task id string (e.g. `relative-velocity`), plus a top-level `default_task:` scalar. Each task entry carries what is today's single set of flat scalars/hardcoded constants: target repo path, branch prefix, plan/provenance file paths, hidden-tests directory, obligations file, expected slice count, and production/test/doc path globs. The `relative-velocity` entry's values are set to make every existing tool behave identically to today, byte for byte. **The old flat keys are removed incrementally, not all at once**: a slice that finishes migrating a given key's last remaining reader removes that key in the same commit, so every slice's own end state leaves the full tool suite working and fully tested (see "Migration approach" below). Within this plan only the top-level `measurement.production_paths`/`test_paths`/`doc_paths` keys reach that point (Slice 2); `relative_velocity_repo`, `dev_branch_prefix`, `dev_worktree_root` and `leaderboard.expected_slices` keep their readers (`cohort_run.py`, `leaderboard.py`, both out of scope) and stay, read exactly as today, alongside the new `tasks:` block.
- **`bench_lib.resolve_task(policy, task_id)`** is the one place that resolves and validates a task id into a fully-checked dict (fails loudly, names the task id and the missing/malformed key — never guesses). Every tool this plan makes task-aware calls this instead of reading flat policy keys.
- **`task_id` becomes a first-class field**: stamped by `dev_check.py` into each attempt's provenance at grading time (the only place task configuration is actually resolved against a real grading worktree). Propagating it through `model_report.py` and consuming it in `leaderboard.py` are out of scope for this plan.
- **A run is cross-checked against its resolved task at grading time**, not just resolved: `dev_check.py` already reads the run's own recorded target repository from `run.json`; it compares that against the resolved task's configured repo and refuses loudly on a mismatch. This closes the gap an operator-supplied but wrong `--task` would otherwise leave open — the exact score-blending boundary this plan exists to close cannot depend on the operator never mistyping a flag.
- **Where a resolution choice must be made once, it is made once and threaded explicitly downstream** rather than re-derived independently in each tool. Concretely: within this plan nothing *infers* which task a run belongs to — `grade_run.py` takes an explicit `--task` and hands it to `dev_check.py`, which cross-checks it against the run's own recorded repository rather than re-inferring it. Inference from worktree membership (a future `cohort_run.py` change) is out of scope here.

### Migration approach

Two distinct migration concerns, handled differently, both load-bearing:

1. **Policy schema migration (code-level)**: rather than Slice 1 deleting the old flat keys in one shot (which would leave every other tool broken until later slices individually catch up — a real defect an earlier draft of this plan had), the old flat keys are removed incrementally. Slice 1 only *adds* `tasks:`/`default_task:` alongside the existing flat keys, changing no consumer's behavior. Each later slice, when it finishes switching its own tool over to `resolve_task`, deletes the specific flat key(s) it was the last reader of, in the same commit. Every slice's own end state is therefore fully working with a green test suite — there is no "broken until N slices later" window at any commit boundary.
2. **Historical data (no step in this plan)**: the real `results/runs/` tree already holds many graded `relative-velocity` runs from before this plan existed. Their `slice-<N>.json` sheets will never retroactively gain a `provenance.task_id` field — `dev_check.py` deliberately preserves an already-graded attempt's captured provenance on a later regrade (never silently rewriting what rubric an attempt was graded under), so simply re-running `grade_run.py` against an old attempt does not backfill it. Backfilling at report time (treating a sheet with no `provenance.task_id` as `default_task`, visibly marked as backfilled) is the job of a later `model_report.py` slice, out of scope here.

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

- **Slice 2**: High difficulty, `Independent audit required: yes`. This is the grading-correctness critical path, largest blast radius if subtly wrong. Recommend a frontier/senior-profile implementer, full attention, no batching.
- **Slice 1**: Low difficulty — recommend any capable model; safe to run solo.

## Slice Batches

Batching is a Mode A (assisted-session) convenience only — `project-manager` (Mode B) executes atomic slices in plan order regardless of any batch grouping stated here.

- No batches are recommended by default given the strict dependency chain (each slice's authorized surface assumes the previous slice's schema/field additions already exist) and the mixed difficulty levels. If a single strong implementer runs this end to end in one session, running slices individually in order — with the `Independent audit required: yes` slice (Slice 2) genuinely reviewed by a separate pass, not self-graded — is the recommended path over any batching.

---

## Slice 1: `tasks:` policy schema + `bench_lib.resolve_task`

### Intended Change

- Add a `tasks:` mapping to `policy.yaml`, keyed by task id (string), and a top-level `default_task:` scalar naming which entry applies when no `--task` is given anywhere downstream.
- Populate exactly one entry, `relative-velocity`, whose values reproduce today's hardcoded/flat-scalar behavior: target repo path (today's `relative_velocity_repo`), branch prefix (today's `dev_branch_prefix`), worktree root (today's `dev_worktree_root`), the plan file's path relative to the *target repo* (today's `cohort_run._FROZEN_PLAN_RELATIVE_PATH`), the provenance file's path relative to *this bench's own root* (today's `cohort_run._PROVENANCE_RELATIVE_PATH`), the hidden-tests directory and obligations file paths relative to *this bench's own root* (today's `hidden_tests/` and `dev_check.OBLIGATIONS_RELATIVE_PATH`), the expected slice count (today's `leaderboard.expected_slices`), and a required `measurement` sub-block (`production_paths`/`test_paths`/`doc_paths`, today's flat top-level `measurement.production_paths` etc.) carrying today's exact glob values — these describe the *target repo's* layout, so they belong per-task, not global; only `loc_definition`/`loc_category_definition`/`metric_version` stay in a global top-level `measurement:` block, since they're a methodology choice applied uniformly to any task, never a layout fact.
- **This slice does not remove any existing flat policy key.** `relative_velocity_repo`, `dev_branch_prefix`, `dev_worktree_root`, `leaderboard.expected_slices`, and the top-level `measurement.production_paths`/`test_paths`/`doc_paths` all stay exactly as they are, still read by `cohort_run.py`/`dev_check.py`/`leaderboard.py` exactly as today, alongside the new `tasks:` block. See "Migration approach" above: each later slice deletes the specific key(s) it finishes migrating away from, in its own commit — this slice's job is only to add the new schema without changing any existing tool's behavior at all.
- Add `bench_lib.resolve_task(policy: dict, task_id: str | None) -> dict`: resolves `task_id` (falling back to `policy["default_task"]` when `None`), validates every required key is present with the right type, and returns one self-describing dict including the resolved `task_id` itself. Raises `bench_lib.BenchLibError` naming the task id and the specific missing or malformed key — mirroring the validation rigor `dev_check.load_policy` and `leaderboard.load_leaderboard_policy` already apply to today's flat keys. Concretely: `expected_slices` must be a positive integer (`0` or a negative value is malformed, not just a wrong type); `worktree_root` may be a string or `null` (today's `dev_worktree_root` is `null`, and `null` must be accepted and preserved); each `measurement` bucket must be a non-empty list of strings; and a `tasks:` key that is not a string (e.g. an unquoted YAML number) is a named `BenchLibError`, never a raw `TypeError` — including when an unknown-id error lists the configured ids. The returned dict is a fresh copy — mutating it must never alter the loaded policy. The registry's own shape (a non-empty mapping with string keys) may be checked up front, but of the entries only the requested one is validated: resolving one task never fails because a *different* entry's contents are malformed.
- This slice does not wire `resolve_task` into any CLI tool's live behavior yet — that's every following slice's job. It is exercised directly by this slice's own unit tests, which is enough for it not to be dead code (AGENTS.md's "every function must be load-bearing" is satisfied by its tests plus its planned, documented consumers in Slice 2, not by having a CLI caller today). Within this plan, `branch_prefix`, `worktree_root` and `expected_slices` have no reader beyond `resolve_task`'s own validation and tests: they are carried so each entry is complete for the out-of-scope `cohort_run.py`/`leaderboard.py` consumers, deliberately, and are not dead configuration to remove.
- **Narrow, surgical exception to the above**: relocate `cohort_run.parse_pinned_plan_commit` (today's only implementation of "read the pinned commit out of a provenance file") from `tools/cohort_run.py` to `tools/bench_lib.py`, unchanged in behavior except its raised exception type, and update `cohort_run.py`'s own call site accordingly. This is needed because Slice 2 (`dev_check.py`) must validate `obligations.yaml`'s `plan_pin` against the same pinned-commit logic, and `dev_check.py` cannot import `cohort_run.py` for it — `cohort_run.py` already does `import dev_check`, so the reverse import would be circular. `bench_lib.py` is the correct home regardless of this slice's chronological ordering: it is the shared-helpers module every other tool imports, and this function has never been CLI-specific. The relocated function raises `bench_lib.BenchLibError` (not `CohortRunError`, since it no longer lives in that module); `cohort_run.py`'s call site must catch `bench_lib.BenchLibError` there and re-raise it as `CohortRunError` with the same message, preserving today's exact error-handling contract at the CLI boundary (today's top-level handler catches `CohortRunError` specifically, not its `BenchLibError` parent). This relocation, and the matching call-site/exception-handling update, is the *only* change permitted in `tools/cohort_run.py`/`tests/test_cohort_run.py` in this slice — every other flat-key read in `cohort_run.py` (the actual `tasks:`-schema wiring) stays untouched; making `cohort_run.py` task-aware is out of scope for this plan (see Non-goals).
- **Second shared helper, needed for the same reason**: add `bench_lib.repo_belongs_to_task(candidate_repo_path: Path, configured_repo_path: Path) -> bool`, a pure, testable check for whether `candidate_repo_path` is the same repository as `configured_repo_path` — either literally the same path, or a `git worktree` of it (checked the same structural way `cohort_run.resolve_ungraded_run_dirs`/`cleanup` already enumerate worktrees of a configured repo today, e.g. via `git worktree list`). A worktree of a *bare* configured repository counts the same way. When `configured_repo_path` does not exist or is not a git repository, membership cannot be determined, so the function raises `BenchLibError` naming that path rather than answering `False`; `False` is reserved for a configured repo that git can enumerate and whose worktrees do not include the candidate. This exists because Slice 2 must verify a graded run's own recorded target-repo path (a trial *worktree*, not the substrate repo path configured in `policy.yaml`) genuinely belongs to the resolved task, and a later, out-of-scope `cohort_run.py` change will need the identical check to resolve `--task` from a worktree's membership. Putting it in `bench_lib.py` now keeps that check in one shared place rather than having two tools independently invent two slightly different implementations of it.

### Acceptance Criteria

- Inputs: `policy.yaml` after this slice; `resolve_task(policy, task_id)` with `task_id` a known key of `tasks:`, `None`, or an unknown string.
- Outputs:
  - [ ] `resolve_task(policy, None)` resolves to the `default_task` entry.
  - [ ] `resolve_task(policy, "relative-velocity")` returns a dict whose resolved values are equivalent to today's hardcoded constants and flat policy keys (same repo path, same branch prefix, same plan/provenance/hidden-tests/obligations paths, same expected slice count, same `measurement.production_paths`/`test_paths`/`doc_paths` glob lists) — this is checked by a test that asserts those exact values, not just that resolution succeeds. The test writes the expected values out as literals; it must not read them back from the flat policy keys, because Slice 2 deletes the flat `measurement.production_paths`/`test_paths`/`doc_paths` keys and a test that reads them would break there.
  - [ ] `resolve_task(policy, "does-not-exist")` raises `BenchLibError` naming `"does-not-exist"` and the configured task ids available.
  - [ ] A `tasks:` entry missing a required key, or with a key of the wrong type, raises `BenchLibError` naming the task id and the specific key — never silently defaults or coerces. This includes a non-positive `expected_slices` and a measurement bucket that is not a non-empty list of strings; a non-string task key is likewise a named `BenchLibError`, not a raw crash; `worktree_root: null` is accepted and preserved.
  - [ ] `bench_lib.parse_pinned_plan_commit` exists, raises `bench_lib.BenchLibError` on the same error conditions its `cohort_run.py` predecessor raised `CohortRunError` for, and `cohort_run.py` no longer defines its own copy — its call site catches `BenchLibError` and re-raises `CohortRunError` with the same message.
  - [ ] `bench_lib.repo_belongs_to_task(candidate, configured)` returns `True` for the configured path itself, `True` for a path that is a registered `git worktree` of the configured repo (including a worktree of a bare configured repo), and `False` for an unrelated repository; a configured path that does not exist or is not a git repository raises `BenchLibError` naming it — verified against a real or fixture git repo with at least one worktree, not just path-string comparison (a trial worktree's path is never literally equal to `policy["tasks"][id]["repo"]`, so this must check actual git worktree membership, not path equality).
  - [ ] Every existing test in `tests/test_cohort_run.py`, `tests/test_dev_check.py`, `tests/test_grade_run.py`, `tests/test_model_report.py`, and `tests/test_leaderboard.py` still passes unchanged after this slice — this is the slice's core regression guarantee: adding the new schema changes no existing tool's behavior at all.
- User-visible behaviour: none — every existing `cohort_run.py`/`dev_check.py`/`grade_run.py`/`model_report.py`/`leaderboard.py` invocation is completely unaffected by this slice, because none of them read `tasks:`/`resolve_task` yet, and every flat key they do read is untouched.
- Behaviour that must not change: every existing tool's behavior against today's single-task `policy.yaml`, in full — this slice is purely additive.

### Authorized Surface

- Files allowed to change:
  - `policy.yaml`
  - `tools/bench_lib.py`
  - `tools/cohort_run.py` (only for the `parse_pinned_plan_commit` relocation and its call-site exception handling described above — no other change in this file)
  - `tests/test_bench_lib.py`
  - `tests/test_cohort_run.py` (only for the relocated function's tests moving/being re-pointed at `bench_lib`, and for one test that the call site re-raises `BenchLibError` as `CohortRunError` with the same message — no other change)
- Functions/classes/components allowed to change: `bench_lib.resolve_task` (new), `bench_lib.parse_pinned_plan_commit` (relocated, new in this module), `bench_lib.repo_belongs_to_task` (new), the `tasks:`/`default_task:` addition to `policy.yaml` (additive only — no existing key removed), `cohort_run.py`'s call site for `parse_pinned_plan_commit` and its own now-removed local definition of that function.
- Tests allowed or expected to change: `tests/test_bench_lib.py` (new), `tests/test_cohort_run.py` (only the tests covering `parse_pinned_plan_commit`, relocated to `tests/test_bench_lib.py` or kept as a thin re-export test — implementer's choice — plus one test of the call site's `BenchLibError` → `CohortRunError` re-raise).

### Explicit Non-Goals

- Do not touch `tools/dev_check.py`, `tools/grade_run.py`, `tools/model_report.py`, or `tools/leaderboard.py` in this slice — none of them change behavior, and none of them call `resolve_task` yet; Slice 2 is the first real consumer.
- Do not remove any existing flat policy key in this slice — see "Migration approach" above.
- Do not change anything else in `tools/cohort_run.py` beyond the `parse_pinned_plan_commit` relocation and its exception handling — its own `tasks:`-schema wiring is out of scope for this plan.

### Risk Flags

- Risky surfaces touched: none (no auth/billing/persistence/migration/shared-external-contract surface — `policy.yaml` and `model-report.json` are operator-local tooling config, not a public API).
- Difficulty: **Low** — new, well-isolated code with direct unit tests; no existing call site's behavior changes within this slice itself.
- Approval needed before implementation: no
- Independent audit required: no

### Validation Plan

- Tests to add/update: `tests/test_bench_lib.py` — new tests for `resolve_task` covering: default resolution, explicit task id, unknown task id, missing key, wrong-typed key, non-positive `expected_slices`, a non-list measurement bucket, a non-string task key, `worktree_root: null` accepted, the returned dict being a fresh copy, and exact literal-value equivalence to today's constants for the `relative-velocity` entry; `repo_belongs_to_task` against real git repositories (the configured repo itself, a registered worktree, a worktree of a bare configured repo, an unrelated repository, and the raise for a missing or non-git configured path); plus `parse_pinned_plan_commit`'s relocated tests and its exception type.
- Commands to run: `python -m pytest tests/ -q` — the **full** suite, and it must pass in full, since this slice changes no existing tool's behavior.
- Lint (differential, via the `lint` skill): required — `policy.yaml`, `tools/bench_lib.py`, `tools/cohort_run.py`, `tests/test_bench_lib.py`, `tests/test_cohort_run.py`.
- Manual checks: read the new `tasks:` block's comments against the still-present flat keys' own comments and confirm the new block's rationale is consistent with, not contradicting, what the flat keys' comments still say (they coexist in this slice, so both must read as true simultaneously).

### Rollback Path

- Revert this slice's commit. The full test suite passes before and after this commit, so revert is clean, total, and leaves the tool suite exactly as it was.

---

## Slice 2: `dev_check.py` and `grade_run.py` become task-aware

### Intended Change

- `dev_check.py` gains a `--task <id>` CLI flag (default: `policy["default_task"]` when omitted), resolves it via `bench_lib.resolve_task`, and uses the resolved task's `hidden_tests_dir`/`obligations_file`/`plan_file` in place of the current hardcoded `hidden_tests/slice{N}` path convention and `OBLIGATIONS_RELATIVE_PATH` constant.
- Replace the hardcoded `HIDDEN_TEST_FILENAMES = ("test_hA.py", "test_hB.py")` module constant with filenames **derived from the resolved task's `obligations.yaml` for that slice** — its obligation groups' `tests:` entries already carry `tests/test_hA.py::test_name`-shaped node ids; the set of distinct filenames referenced by a slice's obligation groups *is* the set of hidden test files for that slice. This removes a duplicated, task-specific constant in favor of information the obligations file already, uniquely holds — consistent with this repo's "recompute rather than duplicate" principle. **Three** current call sites move to this derivation, not two — check for more before assuming this list is exhaustive: `hidden_tests_manifest_hash`'s file-copy loop, `run_hidden_tests`'s own file-copy loop (both currently iterate `HIDDEN_TEST_FILENAMES` directly), *and* `run_hidden_tests`'s pytest subprocess argv, which today hardcodes the literal strings `"tests/test_hA.py"`/`"tests/test_hB.py"` directly rather than reading the constant — easy to miss by grepping for `HIDDEN_TEST_FILENAMES` alone, since that grep won't find it. The obligations map is the single authority on which hidden-test files a slice runs: a slice whose groups name no test file at all is refused with a `DevCheckError` naming the obligations file, before any grading worktree is created; a `test_*.py` file in the slice directory that no group names is simply not run, and a runtime stray-file check in `dev_check.py` is not part of this plan. The existing test-time guard `tests/test_dev_check.py::TestObligationMapAgainstRealFiles` (today it iterates `HIDDEN_TEST_FILENAMES`) must keep checking the repository's own obligations map against the `test_*.py` files actually present in each slice directory — never against the map-derived names, which would make it circular.
- Add a load-time consistency check: the resolved task's `obligations.yaml` top-level `plan:` field must match the resolved task's `plan_file` (repo-relative path), and `plan_pin:` must match the pinned commit resolvable from the task's `provenance_file` via `bench_lib.parse_pinned_plan_commit` (relocated there in Slice 1 specifically so `dev_check.py` can call it without a circular import on `cohort_run.py`) — a mismatch is a loud, named-file-and-value `DevCheckError`, not a silent grade. This wires up `obligations.yaml`'s existing-but-previously-unread `plan`/`plan_pin` fields rather than inventing a new schema for the same fact.
- `dev_check.py`'s own grading path loads the resolved task's `obligations_file`. Keep `dev_check.load_obligations(root)` and `OBLIGATIONS_RELATIVE_PATH` working exactly as today for their other callers — `model_report.py` and `tests/test_model_report.py` call `load_obligations(root)` and are outside this slice's surface — by adding a separate path-taking helper, or an optional parameter whose default preserves today's behavior.
- Add a second, distinct consistency check: the run actually being graded must belong to the resolved task, not just have a validly-configured task id passed for it. `dev_check.py` already reads the run's own recorded target repository (a trial *worktree* path, e.g. `relative-velocity-trial-1` — never literally equal to `policy["tasks"][id]["repo"]`, which points at the vendored substrate repo itself) from `run.json` at its existing attempt-resolution call sites. Membership is proven by either of two facts, checked in this order: (a) Slice 1's `bench_lib.repo_belongs_to_task(recorded, configured)` returns `True` — the recorded repository is the task's configured `repo` or a registered `git worktree` of it (never literal path-string equality, which would reject every real, valid run); or (b) the recorded repository's history contains the task's pinned plan commit — the commit `bench_lib.parse_pinned_plan_commit` reads from the task's `provenance_file`, the same value the `plan_pin` check above uses — for example `git -C <recorded repo> merge-base --is-ancestor <pinned commit> <commit being graded>` exits 0. Proof (b) exists because `cohort_run.py setup --repo <path>`, documented in today's `README.md`, runs a trial in an already-prepared repository that may be a plain clone rather than a worktree; grading uses the recorded repository only as a git source, so such a run is equally gradeable. If (a) answers `True`, (b) is not consulted; if (a) answers `False` or cannot be evaluated (`repo_belongs_to_task` raises, e.g. because the configured repo is absent), (b) decides. Any non-zero exit from (b)'s git check — including the pinned commit being unknown to that repository — means "not proven", never "accepted". When neither proof holds, the run is refused with a loud `DevCheckError` naming both the run's recorded repository and the resolved task's configured one (and carrying (a)'s own error text when (a) could not be evaluated), and no sheet is written. A clone of some other repository, whose history does not contain this task's pinned commit, is still refused. Two tasks whose repositories share one history are not told apart by (b); that is accepted here. This is what actually prevents an operator's mistyped-but-valid `--task` from silently grading a run under the wrong task's rubric; the `plan`/`plan_pin` check above only validates a task's own internal configuration, not its association with the specific run being graded.
- Move `measurement.production_paths`/`test_paths`/`doc_paths` (today a single global policy block, read by `dev_check.classify_path` and validated at load time by `dev_check.load_policy`'s own measurement-keys validation helper) to being read from the resolved task's own `measurement` sub-block (already defined by Slice 1) instead of the flat top-level block. Once this is done, delete the old top-level `measurement.production_paths`/`test_paths`/`doc_paths` keys from `policy.yaml` — this slice is their last reader, and the load-time validation helper that currently requires those keys globally must move to validating them per-task instead (via `resolve_task`, which Slice 1 already requires the sub-block for). `loc_definition`/`loc_category_definition`/`metric_version` stay in the top-level `measurement:` block unchanged, since they're a methodology choice applied uniformly to any task, not a layout fact, and must still reach the LOC computation alongside the task's own globs. `dev_check.load_policy` therefore stops requiring the three flat glob keys, but must not start requiring a `tasks:` block or rejecting leftover flat glob keys: `cohort_run.py` and `review_score.py` load their policy through it, and their existing test fixtures (outside this slice's surface) build policies with flat `measurement` globs and no `tasks:`.
- Stamp the resolved `task_id` into `dev_check.build_provenance`'s returned block, alongside the existing `plan_hash`/`obligations_hash`/`hidden_tests_hash`.
- `grade_run.py` gains its own `--task <id>` CLI flag (default: `policy["default_task"]` when omitted — grading a run without specifying a task keeps working exactly as today for the existing single-task cohort) and threads it into `dispatch_grade`'s `argv` it builds for `dev_check.main(argv)`, as `["--task", task_id]`.
- Update the `--slice` help text (currently "slice number (1 or 2), matching hidden_tests/obligations.yaml") to not bake in the current task's slice count.

### Acceptance Criteria

- Inputs: an attempt commit graded via `dev_check.py`/`grade_run.py`, with or without `--task` given; `policy.yaml` from Slice 1.
- Outputs:
  - [ ] Grading the existing `relative-velocity` task, with `--task` omitted or `--task relative-velocity` given explicitly, produces a sheet whose grading-outcome fields — per-node pass/fail results, obligation-group fractions, the overall correctness score, ΔLOC/ΔCC/size-complexity figures, scope-discipline results, and the attempt's resolved ordinal — are identical to what today's `dev_check.py` produces for the same commit. Fields expected to differ, and excluded from this comparison: the grading timestamp (always refreshed on any regrade, with or without this slice), `provenance.task_id` (new in this slice), and `provenance.policy_hash` (changes because Slices 1 and 2 both edit `policy.yaml`'s content, independent of anything task-relevant to the graded commit). This is the slice's core regression guarantee and must be checked against a real or fixture-recorded prior sheet with this explicit field-exclusion list applied, not just "grading succeeds."
  - [ ] The derived hidden-test filename set for slice 1 and slice 2 of `relative-velocity` equals `{"test_hA.py", "test_hB.py"}` exactly, by derivation, not by a remaining hardcoded fallback.
  - [ ] A slice whose obligation groups name no hidden-test file is refused with a `DevCheckError` naming the obligations file, before any grading worktree is created and without writing a sheet.
  - [ ] `obligations.yaml`'s `plan`/`plan_pin` mismatched against the resolved task raises `DevCheckError` naming both the expected and found value, and no sheet is written.
  - [ ] Grading a run whose own recorded repository is not the explicitly-passed `--task`'s configured repo, nor a registered `git worktree` of it (per `bench_lib.repo_belongs_to_task`), nor a repository whose history contains that task's pinned plan commit, fails loudly with a `DevCheckError` naming both repositories and writes no sheet, even though the passed task id is itself validly configured. Grading a run whose recorded worktree genuinely *is* a worktree of the resolved task's configured repo succeeds — this must not reject ordinary valid runs by comparing paths for literal equality — and so does a run recorded in a plain clone whose history contains the pinned plan commit (the `cohort_run.py setup --repo` case).
  - [ ] Every attempt's `provenance` block carries `task_id` alongside the existing hash triple.
  - [ ] `grade_run.py --task does-not-exist ...` fails loudly before attempting to grade anything, and `dev_check.py --task does-not-exist ...` raises `DevCheckError` naming the id and the configured ids.
  - [ ] `dev_check.classify_path` classifies paths using the resolved task's `measurement.production_paths`/`test_paths`/`doc_paths` (not a global flat read, which no longer exists after this slice), and for `relative-velocity` this produces identical classification to today's behavior for every path in a real `relative-velocity` diff.
  - [ ] All three hardcoded-filename call sites identified in Intended Change (not just the two obviously named by the constant) now derive filenames from the resolved task's obligations, verified by a fixture task whose slice references a filename other than `test_hA.py`/`test_hB.py` and confirming the pytest subprocess argv actually targets it.
- User-visible behaviour: `dev_check.py`/`grade_run.py` invocations exactly as documented in today's `README.md` keep working unchanged, including grading a run made with `cohort_run.py setup --repo <path>` in a plain clone (proof (b) of the run/task cross-check).
- Behaviour that must not change: the actual pass/fail outcome and obligation-group scoring of every existing hidden test for `relative-velocity` — this slice changes *how* file paths and filenames are resolved, never what gets graded or how it's scored.

### Authorized Surface

- Files allowed to change:
  - `policy.yaml` (only to delete the now-fully-migrated top-level `measurement.production_paths`/`test_paths`/`doc_paths` keys and to update the comments that describe or reference them, including the `tasks:` block's note that they coexist — no other change)
  - `tools/dev_check.py`
  - `tools/grade_run.py`
  - `tests/test_dev_check.py`
  - `tests/test_grade_run.py`
  - `tests/test_tool_contract.py` (only if it enumerates these two tools' CLI flags)
  - `tests/test_bench_lib.py` (only to re-point a Slice 1 test that still reads the deleted flat `measurement` glob keys at the literal values those keys held — no other change)
- Functions/classes/components allowed to change: `dev_check.HIDDEN_TEST_FILENAMES` (removed), `dev_check.classify_path` and its `measurement` argument's source, `dev_check.hidden_tests_manifest_hash`, `dev_check.run_hidden_tests` (including its pytest subprocess argv construction — see Intended Change's third call site), `dev_check.build_provenance`, the run/task repository cross-check (new, calling `bench_lib.repo_belongs_to_task`), the `obligations.yaml` `plan`/`plan_pin` load-time consistency check (new, calling `bench_lib.parse_pinned_plan_commit`), `dev_check.load_policy`'s measurement-keys validation helper (today validates the flat top-level keys; must move to validating each task's own `measurement` sub-block instead — whatever this helper is actually named in the current code, it is in scope), `dev_check.main`'s new `--task` argument, `grade_run.dispatch_grade`, `grade_run.main`'s new `--task` argument, the path-taking obligations loader or `load_obligations` parameter described in Intended Change, `dev_check`'s argument parsing (`--task`, the `--slice` help text), and `grade_run`'s internal functions that carry the task id from `main` to `dispatch_grade` on every grading path. Additionally, at the implementer's discretion, two further checks that close the same score-blending boundary are in surface if added though never required: that the run's own recorded plan file (run.json `plan.path`) is content-identical to the resolved task's `plan_file`, and that a regrade of an already-graded attempt resolves the same `task_id` its captured provenance recorded.
- Tests allowed or expected to change: `tests/test_dev_check.py`, `tests/test_grade_run.py`, `tests/test_tool_contract.py` (only if it enumerates these two tools' CLI flags), `tests/test_bench_lib.py` (only as stated in the files list above).

### Explicit Non-Goals

- Do not change `hidden_tests/slice1/`, `hidden_tests/slice2/`, or `hidden_tests/obligations.yaml`'s content — only how `dev_check.py` locates and reads them.
- Do not touch `tools/bench_lib.py` or `tools/cohort_run.py` in this slice — both `resolve_task` and `parse_pinned_plan_commit` already exist from Slice 1; this slice only calls them.
- Do not add task-awareness to `model_report.py` or `cohort_run.py` — both are out of scope for this plan — this slice's own tests should exercise `dev_check.py`/`grade_run.py` directly, not through the full CLI chain.

### Risk Flags

- Risky surfaces touched: none in the classic sense, but this is the grading-correctness core of the entire bench — a subtle mistake here (e.g. a filename-derivation edge case, or a path resolved against the wrong root) produces a grade that looks plausible but is wrong, which is exactly the failure mode this repo's "fail loudly, never silently degrade" principle exists to prevent. Treat any ambiguity in this slice as a stop-and-ask, not a judgment call.
- Difficulty: **High** — touches the grading-critical path; the filename-derivation change in particular replaces a previously-explicit constant with computed behavior and needs careful edge-case testing (e.g., a slice whose obligation groups reference more than two files, or a node id with a `[param]` suffix per `obligations.yaml`'s own documented-but-never-exercised parametrize caveat); the new run/task cross-check also needs careful testing since it's genuinely new logic, not a refactor.
- Approval needed before implementation: no
- Independent audit required: yes

### Validation Plan

- Tests to add/update: `tests/test_dev_check.py` (task resolution, filename derivation from a fixture obligations block, the zero-file refusal, plan/plan_pin consistency check, run/task repository cross-check including both proofs and a clone of an unrelated repository, provenance `task_id` field); `tests/test_grade_run.py` (`--task` threading into `dispatch_grade`'s argv); `tests/test_tool_contract.py` if it enumerates `dev_check.py`/`grade_run.py`'s CLI flags.
- Commands to run: `python -m pytest tests/ -q` — the full suite, expected to pass in full (this slice's own regression criterion requires it).
- If a real or recorded `relative-velocity` attempt commit is available, re-grade it before and after this slice and diff the resulting sheet JSON using this slice's explicit field-exclusion list — this is the strongest available regression check and should be run even though it's not a unit test.
- Lint (differential, via the `lint` skill): required.
- Manual checks: read through `dev_check.py`'s full diff against the pre-slice version specifically looking for any remaining hardcoded `hidden_tests`/`slice{N}`/`test_hA.py`/`test_hB.py` reference that should have moved to task resolution.

### Rollback Path

- Revert this slice's commit. `dev_check.py`/`grade_run.py` return to reading their pre-slice flat keys, and this slice's `policy.yaml` edit (deleting the now-redundant `measurement` block) reverts together with it in the same commit, restoring the flat block. Since the full suite passed before and after this slice, revert is clean and total.

---

## Next Chat Prompts

### Mode A — Assisted run (default, checkpointed)

```md
Plan file: docs/plans/MULTI-TASK-PLAN-2SLICE.md
Slices or batch this session: Slice 1

Read the full plan file first. If a selected slice or batch receipt is incomplete or the plan state is unclear, stop and tell me before coding.

Work on the current feature branch for this plan; if none exists, create one and tell me the name.

Use orchestrator as the controlling skill. Act as the Developer: keep implementation, validation, Git operations, and commits local. Use a read-only Reviewer only for investigation, evidence gathering, the hostile drift-audit skill, and an independent code-review skill pass. If no Reviewer is configured or available, perform Developer self-audit and record that provenance explicitly. Slice 2 is marked `Independent audit required: yes` in the plan -- for it, a genuinely independent Reviewer (not Developer self-audit) is required, not optional.

For each selected slice or batch, in plan order:
1. Restate the frozen contract (authorized surface + non-goals) from the plan, and re-read the plan's "How rigid this plan is meant to be" and "Migration approach" sections so you apply its flexibility rules correctly rather than treating every prose detail as frozen.
2. If any included slice's Risk Flags mark approval-needed, stop and get my approval before coding.
3. apply the scoped-implementation skill against the selected contract.
4. apply the drift-audit skill using a read-only Reviewer when available; otherwise perform Developer self-audit. Report the authorization gate result and who performed it before any quality review.
5. If the gate passes: for a broad or structural change, first run the code-health skill differentially against the slice's starting commit and supply its report as review evidence. Then apply the code-review skill using a read-only Reviewer when available (mandatory, not optional, for a slice marked `Independent audit required: yes`); otherwise perform Developer self-audit through the code-review skill. Record who performed it. If the drift gate fails, fix the drift and re-audit.
6. Surface drift and review findings to me, fix them, then re-run the relevant gate. If consecutive reviews return only minor findings and have clearly converged record residuals in the slice summary and proceed.
7. Ask me before committing. On my approval, commit the selected slice or batch with the commit skill.

After the selected slice(s) or batch are committed, use the handoff skill to record state, audit provenance (Reviewer tool/label or Developer self-audit and fallback context), and the next slice to resume from (this plan has a strict dependency chain -- Slice 1 before 2). Do not continue past the selected scope.

Confirm before starting: plan file read, selected slice(s), branch, and the first slice. Then begin.
```

### Mode B — Supervised autonomy (alternative)

```md
Plan file: docs/plans/MULTI-TASK-PLAN-2SLICE.md
Repo: <path to the repository>
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
