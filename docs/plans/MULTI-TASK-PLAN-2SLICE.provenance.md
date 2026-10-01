# Provenance: `MULTI-TASK-PLAN-2SLICE.md`

Vendored verbatim (byte-identical) from the `bench-multitask-2slice` task's substrate — a dedicated clone of this repository, not this checkout — a pinned copy rather than a live reference, so a later edit there can never silently change what this bench is scoring mid-cohort.

- Source repo: `ai-agent-bench` itself, as the clone at `substrate/ai-agent-bench-task` (branch `bench-multitask-substrate` of `git@github.com:darrencroton/ai-agent-bench.git`; the local clone is single-branch with its remote removed — see `policy.yaml`'s comment on these entries for why, and for the exact repopulation commands)
- Source path: `docs/plans/MULTI-TASK-PLAN-2SLICE.md`
- Pinned commit: `54a6242bae89b634d2bfe062126a8cb9694e2a13` ("Remove the last evaluation-context phrasing from the pinned plans")
- History of that commit: `77b24c4b4eae3ad0ae7f44ae5177a84989c1ebcf` (the last commit before any multi-task implementation) plus three commits that add only the two re-cut plans and a `setup.sh` (venv + `requirements.txt`, so `cohort_run.py setup` can pre-build a trial's venv); the second and third are the review-fix rounds recorded below.
- Plan sha256: `663fc43aa17ee963c0e320ff509b3e01e65a573a16d4cadf23abf1b894f7b196`
- Vendored: 2026-10-01

## What this plan is, and what was cut

The plan is a cut of the retired eight-slice multi-task plan, `docs/plans/multi-task-support-plan.md` at `77b24c4` (archived locally at `archive/2026-09-30-plan-retired/multi-task-support-plan.md`). Slices 1 and 2 of that plan are kept with their Acceptance Criteria unchanged in substance; Slices 3–8 (`model_report.py` task-id propagation and backfill, then the same five as the 3-slice cut) are dropped and declared plan-level non-goals, and every cross-reference to them is rewritten. The cut follows `docs/SECOND-TASK-PROPOSAL.md` §5.3 and §10. The PM-amended Slice 9 of the nine-slice variant (a `leaderboard.py` provenance-comparison fix) is not folded in, because this cut has no leaderboard slice. Its Migration approach item 2 is rewritten to say the historical-data backfill belongs to a later, out-of-scope `model_report.py` slice, and the Mode A launcher no longer mentions a historical-data step.

Substantive changes beyond the cut, all made before the plan was first run under this task, so no cohort is affected:

- Slice 2's Authorized Surface names the `obligations.yaml` `plan`/`plan_pin` load-time check its own Intended Change already required, and permits, without requiring, two further checks the first run of the original plan added under a recorded surface gap (the run's recorded plan being content-identical to the task's `plan_file`, and a regrade resolving the same `task_id` its captured provenance recorded).
- Slice 1 states that `branch_prefix`, `worktree_root` and `expected_slices` are deliberately reader-less within this plan (their consumers are the out-of-scope tools), so a drift audit does not read them as dead configuration.
- Slice 3's Validation Plan (3-slice only) makes the step that re-runs `model_report.py` against a real `results/runs/` tree conditional on such a tree existing, since a fresh trial worktree has none. Slice 2's equivalent step was already conditional.
- Blank lines were normalised after `###` headings for lint; no prose changed for that.
- Slice 2's Intended Change no longer says the run/task cross-check closes "a gap plan review flagged" (plan-authoring history), and the Mode B launcher's `Repo:` placeholder no longer calls the checkout a trial worktree: the plan must not tell its readers they are inside an evaluation.

The plan text itself carries none of this history: a PM-run plan must read as a stand-alone plan for its repository (`AGENTS.md`, "The vendored plans are frozen").

If the plan is ever revised, this vendored copy is deliberately left unchanged — re-vendor explicitly (new commit hash recorded here) rather than editing in place, so every run's `provenance.plan_hash` stays meaningful across the cohort. A defect found in the plan's text after a cohort has started is recorded in the task's reference README (`hidden_tests/bench-multitask/README.md`, written with the hidden tests), never patched.
