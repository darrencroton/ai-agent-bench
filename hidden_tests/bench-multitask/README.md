# bench-multitask hidden tests -- validation record

This directory holds the hidden tests for the `bench-multitask-3slice` task and its fallback `bench-multitask-2slice` (both registered in `policy.yaml`'s `tasks:` map), the two obligations maps that partition them, and this record of how they were calibrated. The plans they grade are the pinned `docs/plans/MULTI-TASK-PLAN-3SLICE.md` and `docs/plans/MULTI-TASK-PLAN-2SLICE.md`. Both tasks share this directory as their `hidden_tests_dir`: Slices 1 and 2 are the same contract in both plans, so `obligations-2slice.yaml` is `obligations-3slice.yaml`'s slices 1-2 verbatim, and `slice3/` is graded only for the 3-slice task. `docs/OBLIGATION-GROUPS.md` records why the groups are shaped and weighted as they are. Nothing here is shown to a Developer model.

| Path | Contents |
|---|---|
| `slice1/test_hA.py` | 19 nodes: the `tasks:` registry, `resolve_task`, `repo_belongs_to_task`, `parse_pinned_plan_commit` |
| `slice1/test_hB.py` | 1 node: the existing suite still present and passing (the one expensive node, about 55 s measured on the reference) |
| `slice2/test_hA.py` | 12 nodes: `dev_check.py`/`grade_run.py` task-awareness, end to end |
| `slice3/test_hA.py` | 14 nodes: `model_report.py` task_id propagation and backfill, end to end |
| `obligations-3slice.yaml` | 5 + 6 + 6 groups over 20 + 12 + 14 nodes |
| `obligations-2slice.yaml` | slices 1-2 of the above, byte for byte |

## Provenance

- **Substrate pin**: `54a6242bae89b634d2bfe062126a8cb9694e2a13`, the commit every trial branches from (see `docs/plans/MULTI-TASK-PLAN-3SLICE.provenance.md`). It is `77b24c4b4eae3ad0ae7f44ae5177a84989c1ebcf` plus three commits that add only the two plans and `setup.sh`; `tools/`, `tests/` and `policy.yaml` are identical between the two (checked with `git diff --quiet 77b24c4 54a6242 -- tools tests policy.yaml` in `substrate/ai-agent-bench-task`), so `77b24c4` stands in for the pin in calibration.
- **Reference**: this repository's `main` at `310ab63`. Its history passes through the qwen implementation (`3838855`), then `c7ec6b3` (the fix-up the two-model comparative review recommended), `4fb64e5` (stand-alone cleanup) and `310ab63`.
- **Red check A (qwen)**: branch `multi-task-support` at `3838855`, the qwen3.8-27b-q8 implementation of the retired eight-slice plan.
- **Red check B (ornith)**: branch `multi-task-support-2` at `f3ff079`, the ornith-1.5-397b-q6 implementation of the same plan.
- **Per-slice states** (supplementary evidence, because real grading runs each slice's tests against that slice's own commit, not a final tree): qwen/reference lineage Slice 1 first attempt `6ef5eb3`, accepted `9871787`; Slice 2 first `d037a53`, accepted `1c19d55`; Slice 3 first `83c40c5`, accepted `4c312d5`. Ornith Slice 1 first `0267ac0`, accepted `fa656f5`; Slice 2 first `2b76021`, accepted `8121850`; Slice 3 first `f2d65a5`, accepted `3daae25`.

## Reproduction recipe

1. Create detached worktrees of this repository at `310ab63`, `3838855`, `f3ff079` and `77b24c4` (and at the per-slice commits above if re-checking those), outside this checkout.
2. For each worktree and each slice N: copy `hidden_tests/bench-multitask/sliceN/*.py` into the worktree's `tests/`, run `<python> -m pytest tests/<file>.py ... -q -p no:cacheprovider` from the worktree root with `PYTHONDONTWRITEBYTECODE=1`, then delete the copied files. **One slice per invocation**: every slice has a `test_hA.py`, so two slices in one run fail collection on duplicate basenames. `<python>` is `policy.yaml`'s `python_interpreter` (a Python with pyyaml and pytest).
3. Confirm the worktree is clean afterwards (`git status --short` empty). The tests create and remove their own fixture directories (`.hidden-fixture-<uuid>/` at the worktree root, `results/runs/hidden-mt-<id>/`); `results/` is gitignored.
4. To confirm the node ids map through the grading path itself, add `--junitxml` and score the result with `dev_check._parse_junit_outcomes` + `dev_check.score_correctness` against the slice's groups; this was done on the reference for all three slices and every node mapped.

The tests stub nothing inside the tools. Where a grade needs project-manager's `pm_lib`, a stub package is written under a fixture `pm_scripts_dir`; `lint_script`/`health_script` point at files that do not exist, which `dev_check.py` records as unavailable (non-fatal). Every repository and worktree is a real `git init`/`git worktree add`/`git clone --bare` under pytest's `tmp_path`.

## Measured results

Final trees, as instructed for calibration (2026-10-01):

| Worktree | Slice 1 (20 nodes) | Slice 2 (12) | Slice 3 (14) | Matches expectation? |
|---|---|---|---|---|
| reference `310ab63` | 19/20; fails `existing_suite_unchanged` | 12/12 | 14/14 | yes, with the `existing_suite_unchanged` decision below |
| red A qwen `3838855` | 19/20; fails `existing_suite_unchanged` | 12/12 | 11/14; fails `every_attempt_inspected` 2/2, `broken_sibling_entry_not_blocking` 1/2 | `every_attempt_inspected` as expected; `broken_sibling_entry_not_blocking` is an unlisted, confirmed defect (below) |
| red B ornith `f3ff079` | 15/20; fails `entry_validation_fail_loud` 1/6 (`expected_slices: 0` accepted), `repo_membership_real_git` 3/6 (bare repo's worktree False; non-git and missing configured paths return False instead of raising), `existing_suite_unchanged` | 12/12 | 10/14; fails `malformed_provenance_refused` 2/2, `broken_sibling_entry_not_blocking` 1/2, `every_attempt_inspected` 1/2 | yes, plus one unlisted, confirmed defect in `every_attempt_inspected` (below) |
| pin `77b24c4` | 1/20; only `existing_suite_unchanged` passes | 0/12 | 0/14 | yes: every node asserting new behaviour fails; the one "existing behaviour unchanged" node passes |

Each slice graded at its own accepted commit, which is what real grading does:

| Lineage | Slice 1 | Slice 2 | Slice 3 |
|---|---|---|---|
| qwen/reference (`9871787`, `1c19d55`, `4c312d5`) | 20/20 | 12/12 | 11/14 (same failures as the final tree) |
| ornith (`fa656f5`, `8121850`, `3daae25`) | 16/20 (`entry_validation_fail_loud` 1, `repo_membership_real_git` 3) | 12/12 | 10/14 (same failures as the final tree) |

Each slice graded at its first attempt, which is what the leaderboard ranks on:

| Lineage | Slice 1 | Slice 2 | Slice 3 |
|---|---|---|---|
| qwen (`6ef5eb3`, `d037a53`, `83c40c5`) | 19/20: a non-string task key crashes with a raw `TypeError` | 11/12: a slice whose obligations name no test file is refused, but without naming the obligations file | 9/14: middle attempt and stamped/unstamped mix not inspected; explicit-null `task_id` and non-mapping provenance not refused; broken default entry blocks a sibling |
| ornith (`0267ac0`, `2b76021`, `f2d65a5`) | 16/20: `expected_slices: 0` accepted, non-string key crashes, non-git and missing configured paths return False | 5/12: `grade_run.py` did not forward `--task` (the run is graded under `default_task` and refused); the per-task measurement block lost `loc_definition` (`KeyError`); a zero-file slice runs pytest instead of refusing | 9/14: same five failures as qwen's first attempt |

Every first-attempt failure in Slice 2, and qwen's in Slice 1, is gone by that lineage's accepted commit for the slice, i.e. it was fixed under steer. Ornith's Slice 1 defects survived to acceptance, and its bare-repo failure was introduced by a steer: the first attempt passed that node, and `fa656f5` added the `.git`-exists shortcut that broke it. In Slice 3, qwen's lineage fixed explicit-null and non-mapping provenance under steer (`be45658`, `4c312d5`), and the reference fixed the rest in `c7ec6b3`; ornith's fixed every-attempt disagreement (`d6b1c32`).

## Decisions

- **`existing_suite_unchanged` is calibrated on Slice-1 states, not final trees.** Its contract is the plan's "every existing test in the five files still passes unchanged after this slice". It checks that every test function those files defined at `77b24c4` still exists somewhere under `tests/` and that the five files pass. Every final tree fails the name check by construction. The reference and both red checks implemented the retired eight-slice plan, whose later slices (task-aware `cohort_run.py`, leaderboard partitioning) legitimately removed or renamed tests in `test_cohort_run.py`/`test_leaderboard.py`. The reference's `4fb64e5` cleanup also renamed four `test_dev_check.py` tests. A 3-slice trial can contain none of that when its Slice 1 is graded, because Slice 1 is graded at its own commit and these plans forbid touching those files. At each lineage's own Slice-1 commit the node passes (qwen/reference `9871787`, ornith `fa656f5`, and both first attempts), and it passes at the pin. The node exempts only the pinned tests of `cohort_run.parse_pinned_plan_commit`, which the plan explicitly allows to be relocated and re-pointed at `bench_lib` (ornith renamed them when moving them to `test_bench_lib.py`).
- **Red A (qwen) fails `broken_sibling_entry_not_blocking`, which section 5.5 of the proposal lists for ornith only.** This is a real defect, not a wrong test. qwen's `model_report.build_report` calls `bench_lib.resolve_task(policy, None)` before deriving the run's task, which fully validates the default entry. The run under test is natively stamped `task-b`, and the report still fails with `task 'task-a' is missing required key(s): expected_slices`. The reference fixed exactly this in `c7ec6b3` ("a broken default entry no longer blocks a natively stamped sibling run's report"), on the qwen lineage. The proposal's list was incomplete; the test stays.
- **Red B (ornith) fails the stamped/unstamped-mix node of `every_attempt_inspected`, which section 5.5 does not list.** This is also a real defect. Ornith treats a slice as native when *any* attempt carries a `task_id` and ignores the unstamped ones, so a slice whose middle attempt is unstamped is reported `"graded"` and the inference is hidden. The plan says `"graded"` applies only when every contributing sheet carried `task_id` natively, and a mixture is refused. The comparative review recorded the same behaviour as its probes P4, P8 and P9 (`archive/2026-09-30-multi-task-model-comparison/appendices/R3-slice3-model_report.md`, local). Ornith still passes the middle-attempt *disagreement* node, because it does inspect every attempt; that half of the group discriminates qwen alone.
- **The `CohortRunError` re-raise at `cohort_run.py`'s call site is not asserted.** No plan-named surface can provoke it without side effects. `cohort_run.py`'s only caller reads the provenance file from a constant path (Slice 1 makes `cohort_run.py` no more task-aware), so provoking a parse failure would mean deleting a tracked file in the grading worktree or driving `setup` through its worktree side effects. The call site also differs legitimately between a 3-slice trial and the eight-slice reference. The relocation is asserted through `bench_lib` alone: `bench_lib.parse_pinned_plan_commit` exists, reads the pinned line, and raises `BenchLibError` naming the file for each of its two error conditions. An earlier node also asserted that `cohort_run` has no attribute of that name other than `bench_lib`'s function. The external review removed it, because a same-named thin wrapper in `cohort_run` that delegates to `bench_lib` and re-raises `CohortRunError` is a legitimate, minimal way to keep the pinned tests passing, and it is not a copy of the logic. Every red check and per-slice state passed that node and only the pin failed it, so removing it lowered each red-check and reference Slice 1 count by exactly one passing node (e.g. 20/21 became 19/20). The pin went from 1/21 to 1/20. The reference and pin numbers above were re-measured after the removal; the red-check numbers were adjusted arithmetically.
- **`broken_sibling_entry_not_blocking`'s first node pins lazy per-entry validation, an accepted residual risk.** The node requires that only the run's own task entry be validated in full, so a broken `default_task` entry cannot block a run natively stamped under another, valid task. The plan does not say this in so many words. Two plan-consistent implementations fail it: one that validates every registry entry eagerly, and one that derives the backfill id via `resolve_task(policy, None)`. The plan's text supports the node only indirectly. `resolve_task` must fail loudly "naming the task id and the specific missing or malformed key", and that wording is about the task actually resolved. The substrate's own `AGENTS.md`, at the pin, adds the rule "One failure must never silently discard another attempt's data", which is about review harvesting, extended here by analogy. Both red checks fail the node. It stays because §5.4/§5.5 of the proposal name the group and the reference fix-up `c7ec6b3` made the behaviour a confirmed defect. A candidate that validates eagerly loses half of one Slice 3 group for a reading the plan does not forbid.
- **Slice 2 does not separate the two final trees: both pass 12/12, as expected.** Both lineages converged on Slice 2 after five steers each. The group still earns its weight on first attempts (qwen 11/12, ornith 5/12 above), which is what the leaderboard ranks. Most negative-space nodes in Slices 1 and 3 likewise pass both red checks; each still asserts a refusal the plan states, and the first-attempt table shows several of them catching real first-attempt defects.
- **Policy key names are the plan's own.** The plan leaves "the literal string used for a policy key" to the implementer, yet every fixture policy has to spell the keys. The tests use the names the plan text itself writes in prose (`tasks`, `default_task`, `repo`, `branch_prefix`, `worktree_root`, `plan_file`, `provenance_file`, `hidden_tests_dir`, `obligations_file`, `expected_slices`, `measurement.production_paths`/`test_paths`/`doc_paths`). The reference and both red checks chose exactly these. A candidate that renamed one would fail several nodes for a reason the plan nominally permits. This residual risk is accepted, because no key-agnostic black-box fixture exists.
- **Error assertions accept a `str` or a `Path` and any wording.** The tests assert the error *type* the plan names (`BenchLibError`, `DevCheckError`, `ModelReportError`) and that the message contains the concrete id, key, value or path, comparing paths both as given and resolved. They never assert exact wording, which the plan leaves to the implementer. `grade_run.py`'s refusal is asserted through its CLI (nonzero exit, stderr naming the unknown id *and* a configured id), because the plan names no exception type for it. Naming a configured id also rules out an argument parser that simply does not know `--task`.
- **Prior-sheet equivalence and historical backfill are covered by fixtures, not the operator's tree. This is a recorded design decision, not a plan defect.** Slice 2's prior-sheet regrade equivalence and Slice 3's historical-run backfill acceptance criteria read the operator's real `results/runs/` tree. A trial worktree has no such tree, since `results/` is gitignored. The plan makes both steps conditional on such a tree existing, so they are not a plan defect to patch. Here they are covered by fixtures: Slice 2's `measurement_per_task` and `provenance_task_id` pin the grade's fields on a real diff; Slice 3's `task_id_propagation` and `task_resolved_obligations` pin the backfilled report.

## Mutation bank

`mutations/` holds the bank behind `dev_check.py`'s `test_kill_rate` for both bench-multitask tasks: `sitecustomize.py` (the hook module, sha256 `b8bc84d3ed50d49a9f1d8131917a7ab31a1b5d097d35fee4773b4dcb1747d7de`) and one `slice<N>.txt` per slice. Both tasks share the directory, and the 2-slice task never reads `slice3.txt`.

### Provenance

The bank was seeded from the confirmed defect classes: the fix-up contract (`.orchestrator/review-input/multi-task-fixup/fixup-contract.md`), the two-model comparison's Findings §1 (`archive/2026-09-30-multi-task-model-comparison/qwen-vs-ornith-developer-assessment.md`, local), and the red checks recorded above. It uses the same mechanism as relative-velocity's vendored bank but was written fresh for these modules. Each mutant wraps one plan-named public function of `bench_lib`, `dev_check`, `grade_run` or `model_report` after import. Modules are matched by basename, and the hooks cover `builtins.__import__`, `importlib.import_module` and `importlib.reload`. A module lacking the wrapped attribute leaves that mutant uninstalled, and transform or install failures propagate. With `MUTATION` unset nothing is installed. The module's own docstring states the full contract.

### Mutants

| Slice | Id | Wraps | Obligation broken |
|---|---|---|---|
| 1 | `S1_resolve_unknown_falls_back_to_default` | `bench_lib.resolve_task` | an unknown task id raises, naming it (here it resolves to `default_task`) |
| 1 | `S1_resolve_fills_missing_key` | `bench_lib.resolve_task` | a missing required key raises (here it is filled from another entry when one has it) |
| 1 | `S1_resolve_accepts_nonpositive_slices` | `bench_lib.resolve_task` | `expected_slices <= 0` is refused |
| 1 | `S1_resolve_none_takes_first_entry` | `bench_lib.resolve_task` | `task_id=None` resolves `default_task` (here the registry's first entry) |
| 1 | `S1_resolve_rejects_null_worktree_root` | `bench_lib.resolve_task` | `worktree_root: null` is legal |
| 1 | `S1_resolve_aliases_policy_entry` | `bench_lib.resolve_task` | the result never aliases the policy (here it is the policy's own entry) |
| 1 | `S1_membership_by_path_equality` | `bench_lib.repo_belongs_to_task` | a registered worktree is a member (here only path equality is) |
| 1 | `S1_membership_false_instead_of_raising` | `bench_lib.repo_belongs_to_task` | a missing or non-git configured path raises (here it returns False) |
| 1 | `S1_pin_parse_returns_empty` | `bench_lib.parse_pinned_plan_commit` | a missing file or pin line raises (here it returns `""`) |
| 2 | `S2_dev_check_ignores_task` | `dev_check.main` | `--task` selects the rubric (here it is dropped, so `default_task` is graded) |
| 2 | `S2_provenance_omits_task_id` | `dev_check.build_provenance` | provenance carries `task_id` |
| 2 | `S2_grade_run_ignores_task` | `grade_run.main` | `--task` is threaded into every grade (here it is dropped, so the default applies) |
| 3 | `S3_task_id_source_always_graded` | `model_report.build_report` | a backfilled run reports `task_id_source: "backfilled"` |
| 3 | `S3_explicit_null_task_id_backfilled` | `model_report.build_report` | an explicit `task_id: null` is refused (here it is removed before the report sees it) |
| 3 | `S3_middle_attempts_not_inspected` | `model_report.build_report` | every attempt is inspected (here each middle attempt mirrors the first attempt's `task_id` state) |
| 3 | `S3_obligations_from_bench_root_default` | `bench_lib.resolve_task`, as `model_report` sees it | model_report loads the task's own obligations file (here its resolution reports the bench-root default `hidden_tests/obligations.yaml`) |
| 3 | `S3_model_report_ignores_policy` | `model_report.main` | `--policy` selects the registry (here it is dropped) |
| 3 | `S3_correctness_provenance_drops_task_id` | `model_report.resolve_correctness_provenance` | the per-slice `task_id` echo is present |

### Recipe

In each detached calibration worktree (`310ab63` reference, `77b24c4` pin, `3838855` red A, `f3ff079` red B), for each slice N, run `dev_check.load_mutation_bank(<bench root>, resolve_task(policy, "bench-multitask-3slice"), N)` and then `dev_check.measure_test_kill_rate(<worktree>, <bank>, policy, task["measurement"])`, using the real `policy.yaml` (its `python_interpreter` and `mutation_gate`). The suite measured is every tracked file under `tests/**/*.py`. For the weak baseline, copy the pin's `tests/` over the reference worktree's tracked test files (the two tracked sets are identical), run the gate, then restore with `git checkout -- tests/` in that worktree. Confirm `git status --short` is empty in every worktree afterwards.

### Results

Interpreter `~/.conda/envs/work/bin/python3` (Python 3.12.9, pytest 9.1.1), `subprocess_timeout_seconds: 600`. Times are the wall clock of `measure_test_kill_rate` per slice, which includes the probe, the baseline and the control run. Slices 1 and 2 were measured on 2026-10-01 with `mutation_gate.parallel_workers: 4`. Slice 3 was re-measured on 2026-10-01 after `S3_obligations_from_bench_root_default` was retargeted, serially (`parallel_workers: 1`, the policy default), in a gate worktree of its own. Its kill counts are unchanged from the first, parallel measurement.

| Own suite (tools) | Passing at baseline | Slice 1 | Slice 2 | Slice 3 | Total | Errored | Wall clock S1 / S2 (4 workers) | S3 (serial) |
|---|---|---|---|---|---|---|---|---|
| reference `310ab63` | 783 | 9/9 | 3/3 | 6/6 | 18/18 | 0 | 108 s / 137 s | 343 s |
| weak: pin's tests on reference tools | 441 (178 not passing) | 1/9 | 0/3 | 0/6 | 1/18 | 0 | 93 s / 66 s | 168 s |
| frozen: pin `77b24c4` as is | 619 | 0/9 | 0/3 | 0/6 | 0/18 | 0 | 173 s / 105 s | 310 s |
| red A qwen `3838855` | 762 | 7/9 | 3/3 | 5/6 | 15/18 | 0 | 143 s / 132 s | 308 s |
| red B ornith `f3ff079` | 754 | 6/9 | 2/3 | 5/6 | 13/18 | 0 | 179 s / 185 s | 473 s |

- **Every mutant is detectable.** The reference suite kills all 18, each under the slice that lists it, so no mutant is mis-slotted or equivalent and no reference-suite gap was found.
- **The bank discriminates.** The pin's tests running against the reference tools kill 1 of 18: `S1_resolve_rejects_null_worktree_root`, because those tests drive the reference tools with the real policy, whose entries all carry `worktree_root: null`.
- **The frozen suite kills nothing.** At the pin, most target functions do not exist, so those mutants stay uninstalled. The rest (`dev_check.main`, `build_provenance`, `grade_run.main`, `model_report.main`/`build_report`/`resolve_correctness_provenance`) install but are no-ops, because the pin's code and tests never produce `--task`, `--policy` or `task_id`.
- **Inert when unset.** The gate's control run executes the baseline-passing tests with the bank on `PYTHONPATH` and `MUTATION` unset, and it passed in every measurement above; `tests/test_mutation_banks.py` also checks that loading the module installs no hook.
- **The red checks.** Each red check's survivors are its own confirmed defects or the coverage gaps the fix-up recorded:
  - qwen (15/18) misses `S1_resolve_accepts_nonpositive_slices`, the `expected_slices <= 0` test coverage the fix-up added (item 5). It also misses `S3_middle_attempts_not_inspected`, its own first/final-only defect (item 3), and `S1_resolve_fills_missing_key`: its missing-key tests use a single-entry registry, so there is no other entry to fill from.
  - ornith (13/18) misses `S1_resolve_accepts_nonpositive_slices` and `S1_membership_false_instead_of_raising`, which are behaviours its own code has, and `S3_explicit_null_task_id_backfilled`, likewise. It also misses `S1_resolve_fills_missing_key` and `S2_dev_check_ignores_task`.
  - The separation is two mutants, with qwen's suite the stronger.

### Decisions

- **Fewer, sharper mutants: 9 + 3 + 6.** Every listed defect class has exactly one mutant. No mutant was added for Slice 2's plan/plan_pin check or its run-repository cross-check. Both are internal to `dev_check.main`, and both reach `bench_lib` through functions that Slice 1's mutants already wrap. A mutant there would have to patch `bench_lib` as seen from `dev_check` only, which depends on the candidate's import style. The Slice 2 group's hidden tests cover both checks.
- **CLI flags are dropped in both invocation styles.** A tool run as `python tools/<tool>.py` executes as `__main__`, which no import hook sees. For the three flag mutants the module also removes the flag from `sys.argv` at startup when the script's basename matches. Slice 2's hidden tests run `tools/grade_run.py` as a subprocess, which inherits `PYTHONPATH` and `MUTATION`. The residual gap: the other mutants do not reach functions defined in a tool that is running as `__main__` (for example `build_provenance` inside `python tools/dev_check.py`). They do reach every module that script imports.
- **The `build_report` pre-processing mutants work on deep copies.** They find every sheet dict (any dict carrying an `attempts` list) inside the arguments, however the candidate shapes them, and rewrite copies, so a test's own fixture objects are never altered.
- **`S1_membership_by_path_equality` calls the real function first.** Its refusals therefore stay intact, and the mutant breaks only worktree membership, leaving `S1_membership_false_instead_of_raising` as the sole owner of the raise-versus-False obligation.
- **`S3_obligations_from_bench_root_default` wraps `bench_lib.resolve_task`, and fires only for calls from `model_report`.** The plan makes widening `dev_check.load_obligations` optional and leaves its call shape free, so a mutant there would sit inert in a candidate that took the plan's preferred route and survive regardless of suite strength. `resolve_task` is the surface the plan fixes for this obligation (Slice 3 resolves the run's task through it). The mutant checks the immediate caller's module basename, so `dev_check`'s own grading path, a Slice 2 surface, is untouched.
