# Provenance: `MULTI-TASK-PLAN-3SLICE.md`

Vendored verbatim (byte-identical) from the `bench-multitask-3slice` task's substrate — a dedicated clone of this repository, not this checkout — a pinned copy rather than a live reference, so a later edit there can never silently change what this bench is scoring mid-cohort.

- Source repo: `ai-agent-bench` itself, as the clone at `substrate/ai-agent-bench-task` (branch `bench-multitask-substrate` of `git@github.com:darrencroton/ai-agent-bench.git`; the local clone is single-branch with its remote removed — see `policy.yaml`'s comment on these entries for why, and for the exact repopulation commands)
- Source path: `docs/plans/MULTI-TASK-PLAN-3SLICE.md`
- Pinned commit: `ea2106e8b3f357e2e3d02b8617723b3e3e63f208` ("Remove the retired eight-slice multi-task plan from the substrate")
- History of that commit: `77b24c4b4eae3ad0ae7f44ae5177a84989c1ebcf` (the last commit before any multi-task implementation) plus five commits that add or revise only the two re-cut plans and a `setup.sh` (venv + `requirements.txt`, so `cohort_run.py setup` can pre-build a trial's venv), and finally delete the retired plan; the second and third are the review-fix rounds recorded below, the fourth is the post-first-run revision recorded at the end (`438c13e`), and the fifth is the removal recorded after it. `tools/`, `tests/` and `policy.yaml` are identical to `77b24c4`.
- Plan sha256: `29b44429a9d9f333df7fcfae10c607b5ac742fde5d034daa49eff7f1e92d9905`
- Vendored: 2026-10-01; re-vendored 2026-10-06 at `438c13e`, re-pinned 2026-10-06 at the pin above (plan bytes unchanged)

## What this plan is, and what was cut

The plan is a cut of the retired eight-slice multi-task plan, `docs/plans/multi-task-support-plan.md` at `77b24c4` (archived locally at `archive/2026-09-30-plan-retired/multi-task-support-plan.md`). Slices 1, 2 and 3 of that plan are kept with their Acceptance Criteria unchanged in substance; Slices 4–8 (task-aware `cohort_run.py`, leaderboard partitioning by task, per-task reviewer scoring, cross-task standing, documentation) are dropped and declared plan-level non-goals, and every cross-reference to them is rewritten. The cut follows `docs/SECOND-TASK-PROPOSAL.md` §5.3 and §10. The PM-amended Slice 9 of the nine-slice variant (a `leaderboard.py` provenance-comparison fix) is not folded in, because this cut has no leaderboard slice.

Substantive changes beyond the cut, all made before the plan was first run under this task, so no cohort is affected:

- Slice 2's Authorized Surface names the `obligations.yaml` `plan`/`plan_pin` load-time check its own Intended Change already required, and permits, without requiring, two further checks the first run of the original plan added under a recorded surface gap (the run's recorded plan being content-identical to the task's `plan_file`, and a regrade resolving the same `task_id` its captured provenance recorded).
- Slice 1 states that `branch_prefix`, `worktree_root` and `expected_slices` are deliberately reader-less within this plan (their consumers are the out-of-scope tools), so a drift audit does not read them as dead configuration.
- Slice 3's Validation Plan (3-slice only) makes the step that re-runs `model_report.py` against a real `results/runs/` tree conditional on such a tree existing, since a fresh trial worktree has none. Slice 2's equivalent step was already conditional.
- Blank lines were normalised after `###` headings for lint; no prose changed for that.
- Slice 2's Intended Change no longer says the run/task cross-check closes "a gap plan review flagged" (plan-authoring history), and the Mode B launcher's `Repo:` placeholder and Slice 3's validation aside no longer call the checkout a trial worktree: the plan must not tell its readers they are inside an evaluation.

The plan text itself carries none of this history: a PM-run plan must read as a stand-alone plan for its repository (`AGENTS.md`, "The vendored plans are frozen").

## Revision after the first run (2026-10-06)

The first run of the 3-slice plan (trial-1, since discarded with its branch, worktree and PM state; no sheet was graded) surfaced plan defects, so both plans were revised at `438c13e` and re-vendored before any cohort was graded under either. The 2-slice plan takes every change to Slices 1–2; the Slice 3 items apply to the 3-slice plan only. An independent review (Opus 5.5, two rounds) confirmed that no revised sentence contradicts a hidden-test node and that no plan-compliant implementation is forced outside a slice's surface.

- **Surface gaps that each cost an attempt.** Slice 1's equivalence test must pin literal values (Slice 2 deletes the flat `measurement` globs it read), and Slice 2's surface gains `tests/test_bench_lib.py` conditionally; Slice 3's files list gains `tests/test_dev_check.py` under the condition its tests line already stated; Slice 1's `tests/test_cohort_run.py` allowance now covers the call-site re-raise test its own criterion requires; Slice 2's `policy.yaml` allowance covers the comments describing the deleted keys.
- **Run/task membership (operator ruling).** Slice 2's cross-check accepts a run recorded in a registered worktree *or* in a repository whose history contains the task's pinned plan commit, so a `cohort_run.py setup --repo` plain clone stays gradeable as `README.md` documents. The second proof lives in `dev_check.py`; `repo_belongs_to_task` keeps its two-argument contract.
- **Traps for out-of-surface callers named.** `dev_check.load_policy` must not start requiring `tasks:` or rejecting flat globs (`cohort_run.py`/`review_score.py` fixtures load through it), and `load_obligations(root)` keeps working for `model_report.py`.
- **Scope settled where reviewers re-raised it.** A runtime stray-hidden-test-file check and `cohort_run.py` forwarding `--policy` to `model_report.py` are stated out of scope; the real-files guard test must stay non-circular.
- **Criteria the hidden tests assert, now stated.** `resolve_task`'s validation rules (positive `expected_slices`, `null` `worktree_root`, string keys, a fresh copy, only the requested entry validated); `repo_belongs_to_task`'s bare-repo case and its raise for a missing or non-git configured repo; the zero-file slice refusal; `DevCheckError`/`ModelReportError` as the refusal types; Slice 3's every-attempt inspection, malformed-provenance refusal, lazy resolution of only the run's own entry, missing `--policy` refusal, the per-slice `task_id` echo (always the resolved id) and the empty-run case. The hidden tests and mutation bank are unchanged; their calibration stands.

If the plan is ever revised, this vendored copy is deliberately left unchanged — re-vendor explicitly (new commit hash recorded here) rather than editing in place, so every run's `provenance.plan_hash` stays meaningful across the cohort. A defect found in the plan's text after a cohort has started is recorded in the task's reference README (`hidden_tests/bench-multitask/README.md`, written with the hidden tests), never patched.

## Re-pin after the first run (2026-10-06)

The substrate still carried the retired eight-slice plan at `docs/plans/multi-task-support-plan.md`, beside the plan a trial is given, where a weak model could mistake it for its own. `ea2106e` deletes that one file and nothing else: `tools/`, `tests/`, `policy.yaml` and both vendored plans are byte-identical to `438c13e`, so the plan sha256 above is unchanged and no hidden-test calibration is affected. The substrate's other `docs/` files (the relative-velocity plan, its provenance, `OBLIGATION-GROUPS.md`, `reference-impl/README.md`) are kept deliberately: `tools/cohort_run.py` and its tests depend on the first two, and the plans' own text names them as frozen. The pin moved only because the pin is a commit; `obligations-*.yaml`'s `plan_pin` follows it.
