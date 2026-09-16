# ai-agent-bench

Measures which local model should sit in the Developer seat of a real, supervised `project-manager` (PM) Mode B run on production scientific code — by running a completely normal, unmodified PM session against a frozen plan, then grading what the Developer seat produced from PM's own artifact trail.

Contributor rules: `AGENTS.md`. A local, gitignored `HANDOFF.md` (not part of the repo) carries session-to-session working notes when one is in use.

## How it works

The PM session is never instrumented, wrapped, or told anything about this bench — the operator launches it exactly as they always do, with `project-manager`'s own unmodified launcher prompt. `pm.py` already writes a rich, structured artifact trail (`run.json`, `events.jsonl`, per-slice diffs, reviewer reports); this repo's tools read that trail from outside, strictly read-only — no run token, no writes to PM state, `pm.py` is never invoked as a subprocess, and nothing is ever added to the launcher prompt. That boundary is deliberate: the premise is a normal supervised run, so anything that made measurement easier by changing PM's behavior would contaminate the thing being measured.

What gets scored is a *trajectory*, not just an end state: how many attempts a slice took, and what correctness, quality, scope discipline, and reviewer findings looked like for every attempt a git-log walk can recover (falling back to just the final attempt where it can't — see "Known scope limit" below).

## Setup

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

python -m pytest tests/ -q
```

Every path, threshold, and tunable this repo uses lives in `policy.yaml` — nothing is hardcoded in the tools:

- **`python_interpreter`** — point this at an interpreter with the Developer repo's own dependencies installed (numpy, scipy, h5py for `relative-velocity`); this repo's own `requirements.txt` deliberately doesn't duplicate them.
- **`relative_velocity_repo`** — defaults to `substrate/relative-velocity`, a local clone vendored under this repo (gitignored) so `cohort_run.py setup` is self-contained and immune to your own `relative-velocity` checkout moving, being on the wrong branch, or having uncommitted changes. If it's ever missing (a fresh clone of this bench, or after deleting it), repopulate it with `git clone git@github.com:darrencroton/relative-velocity.git substrate/relative-velocity`.
- **`dev_branch_prefix`/`dev_worktree_root`** — control where and how trial worktrees/branches are named.

There's no reviewer-seat key: PM commissions whichever reviewer tool/model it judges right per slice, and that composition is recorded per-review (`run.json`'s `reviews[].tool`/`.model`) rather than pinned in policy ahead of time. There's also no one-shot pre-filter key: a cheap pre-screen before committing a model to a full PM run was considered and dropped, since a candidate model is only ever run through PM because the operator already cares about it — the screen would never change that decision.

## Steps to run a cohort member

This bench tests exactly one frozen plan (`docs/MERGER_RATE_PLAN-2SLICE.md`, vendored from `relative-velocity` at a pinned commit — see `docs/MERGER_RATE_PLAN-2SLICE.provenance.md`), so a trial's `Repo:`/`Plan file:` never need hand-typing: `tools/cohort_run.py` derives them for you (see "The tools" below; it invents no measurement of its own, only sequencing and preparation).

1. **Create a trial worktree and print the launcher prompt for it:**

   ```bash
   python tools/cohort_run.py setup
   ```

   This creates a fresh git worktree of `policy.yaml`'s `relative_velocity_repo`, checked out from this bench's pinned plan commit, on its own branch (`pm-eval-v2/<label>`, auto-numbered from `trial` unless `--label` names it yourself), and prints project-manager's own launcher prompt — extracted live from `SKILL.md`, never a hardcoded copy that could drift stale. Copy that prompt into a brand-new PM-capable session (not this one) — `Repo:`/`Plan file:` are already filled in — fill in the `Developer:`/`Reviewer:` harness and model by hand, and send it. Who plays either seat is entirely your own choice made in the pasted prompt; this tool has no flag for it.

   Already have a prepared repo you'd rather use instead? Pass `--repo <path>` to skip worktree creation entirely. Since a trial's directory is brand new, whichever harness you paste the prompt into may prompt once to trust/permit it before it will work there — pass `--harness <codex|claude|copilot|opencode|qwen>` to pre-register the new directory as trusted for that harness ahead of time (claude/codex/copilot are supported directly; opencode/qwen have no known safe way to do this externally, and `setup` says so rather than pretending to). This is the only thing `--harness` does — it is never filled into the printed `Developer:`/`Reviewer:` lines.

2. **Let PM supervise the run to completion.** It handles Developer sessions, commissions whatever reviewers it judges right per slice (often a panel of several models), and makes every accept/steer/stop decision on its own. Nothing here launches PM for you, and never will.

3. **Once the run is finished** — `run.json["status"]` is `complete`, or `stopped` with PM's own closing event on record (`needs-human` is a pause, not a finish) — grade it, build its per-model report, and refold the cross-model leaderboard in one command (`setup` already printed the exact one to run, pointed at the trial worktree it created):

   ```bash
   python tools/cohort_run.py analyze --dev-repo <dev-repo>
   ```

   `<dev-repo>` resolves to PM's one run directory under that repo's git state automatically (refusing by name if more than one exists there — pass `--run-dir <pm-run-dir>` explicitly to pick one then). `analyze` refuses to grade a run still in progress, and is always safe to re-run.

   **Grading several runs at once, or lost track of which trial directories they landed in?**

   ```bash
   python tools/cohort_run.py analyze-all
   ```

   Finds every ungraded run across every `pm-eval-v2/*` trial worktree of `relative_velocity_repo` on its own (no `--dev-repo`/`--run-dir` needed), keyed on each run's own authoritative `run_id` rather than a directory name, grades each one, then refolds the leaderboard once at the end regardless of whether anything new was found. One run's grading failure is reported and never stops the rest of the batch. It does *not* durably remove a deleted run on its own: delete `results/runs/<run_id>/` while that run's trial worktree is still checked out, and the next `analyze-all` will simply rediscover and grade it right back. To actually drop a run from the leaderboard, delete its results *and* remove its worktree (`cleanup`, step 4).

   You can also run `cohort_run.py analyze` yourself as three separate commands, in order — this is exactly what it does under the hood, and either path is fine:

   ```bash
   python tools/grade_run.py --run-dir <pm-run-dir>
   python tools/model_report.py --run-id <run-id>
   python tools/leaderboard.py
   ```

   Or run just `python tools/leaderboard.py` on its own to refold the leaderboard from whatever's already on disk, without grading or discovering anything new.

   Grading doesn't have to happen in this session: tell the same or a fresh PM/agent session, once the plan is finished, to read this repo's instructions and run it — the tool doesn't care who invokes it, only that the run is actually over. Nothing about grading is ever added to PM's own prompt.

4. **Check the results.** `results/leaderboard.md` is the human-readable ranking (first submission, then supervised outcome in the same row order) plus a per-configuration, per-slice breakdown (obligation-group fractions, ΔLOC/ΔCC, lint and code-health as a hygiene badge, scope exceptions, review-finding trend, PM's own subjective rating verbatim) and a run index. `results/leaderboard.json` carries the same ranking for machine use (the per-slice detail is read fresh from each run's own `model-report.json`, not duplicated into it).

   Once you're done with a trial's worktree, `python tools/cohort_run.py cleanup --label <label>` removes it (dry run by default; `--yes` to actually remove; an ungraded trial is flagged with a warning, not refused). Its branch is left in place either way. Separately, `python tools/cohort_run.py reset-leaderboard` archives (never deletes) `results/` itself, for starting a whole cohort pass over clean.

## The tools

| Tool | What it does |
|---|---|
| `tools/grade_run.py` | Grades one **finished** run in a single pass: resolves every attempt of every slice it can (falling back to just the final attempt per slice when it can't — see "Known scope limit" below), calls `dev_check.py` on each, then harvests every commissioned review via `review_score.py`. This is what you run. |
| `tools/dev_check.py` | Grades one specific attempt: checks its commit out into a disposable worktree, runs that slice's held-out hidden tests and scores them by acceptance obligation, independently invokes lint/code-health (never trusting PM's own prose about them), and recomputes scope discipline via `pm_lib`'s own `effective_authorized_files` helper. Callable directly for a manual/ad-hoc grade. |
| `tools/review_score.py --skill drift-audit\|code-review` | Harvests each commissioned reviewer's report onto its attempt's `reviews` list — one record per commission, so two reviewers on one submission are a panel and a re-commission of the same reviewer is a retry marked `superseded_by`, never an overwrite. Records findings by severity, per-section item counts, the verdict, and how many findings survive into that same reviewer's next review. |
| `tools/bench_lib.py` | Shared helpers (attempt numbering, event-log reading, atomic JSON writes) — not a CLI tool. |
| `tools/model_report.py` | Gathers one model's full run (every `slice-<N>.json` sheet under `results/runs/<run_id>/`) into one report: first- and final-attempt correctness, quality, size/complexity and scope, attempt count and trajectory per slice, every review commission with its full attribution, and PM's own structured judgments and subjective rating — all read back verbatim, never blended into the deterministic scores. Invents no composite score; writes `results/runs/<run_id>/model-report.json`. |
| `tools/leaderboard.py` | Folds every `model-report.json` on disk into one cross-model leaderboard: groups runs by their resolved Developer configuration (model · harness · effort), ranks on **mean first-attempt correctness** — there is no composite score; the old weighted blend was deleted because two of its four terms were saturated — and shows ΔLOC, ΔCC, final correctness, gain, attempts, steers and PM elapsed beside it as supporting columns, never blended in. Two further tables rate the code and drift reviewers from PM's own judgments, and PM's subjective rating is carried through per run, verbatim. Writes `results/leaderboard.json` and `results/leaderboard.md` (ranking tables plus each configuration's per-slice detail and a stably anchored run index, read fresh from `model-report.json` rather than duplicated into the JSON). Refuses outright — never writing an empty leaderboard — when zero `model-report.json` files exist, leaving the previous `leaderboard.json`/`.md` on disk untouched. |
| `tools/cohort_run.py` | Operator convenience wrapper, not a scoring tool — see "Steps to run a cohort member" above for the full flow. Subcommands: `setup` (create a trial worktree, print PM's launcher prompt), `analyze` (grade one finished run and refold the leaderboard), `analyze-all` (same, batched across every ungraded run this bench can find), `cleanup` (remove a trial worktree), `reset-leaderboard` (archive old `results/`). Never launches PM, never writes into a Developer/PM directory. |

`dev_check.py` and `review_score.py` are both pure, one-shot, idempotent commands — the same inputs always produce the same measurement, and re-running one for an already-graded attempt refreshes only its own fields, never disturbing anything the other tool wrote. Both write into one cumulative scoring sheet per run and slice, `results/runs/<run_id>/slice-<N>.json`.

**Known scope limit:** every attempt of a slice gets a deterministic grade when a git-log walk recovers exactly one commit per attempt between the slice's own before_head and its final commit; a slice whose history doesn't satisfy that (most commonly a multi-epoch first slice with no review recorded from its earliest epoch) falls back to grading only its *final* attempt, reported as a named problem, not silently. A review commissioned against an attempt with no sheet row is likewise reported as a named, loud problem when harvested — never silently dropped. The attempt count and PM's per-attempt decision (steer/accept/stop) are unaffected either way, since both come from `events.jsonl` directly for every attempt.

## Repo layout

```text
docs/
  MERGER_RATE_PLAN-2SLICE.md       the frozen two-slice plan PM runs against,
                                   vendored from relative-velocity at a pinned
                                   commit so a later edit there cannot silently
                                   change what is being scored mid-cohort
  MERGER_RATE_PLAN-2SLICE.provenance.md   that pin
  OBLIGATION-GROUPS.md             how the hidden tests are partitioned, and why
  reference-impl/README.md         evidence the hidden tests are correct and
                                   discriminating, plus how to reproduce it
hidden_tests/
  slice1/, slice2/                 held-out tests, one directory per slice
  obligations.yaml                 the acceptance-obligation partition
policy.yaml                        all weights, thresholds and tool paths
requirements.txt                   this repo's own dependencies (pyyaml, pytest)
tools/                             see "The tools" above
tests/                             this repo's own test suite
substrate/relative-velocity/       vendored local clone of the substrate repo
                                   (gitignored); trial worktrees from
                                   `cohort_run.py setup` are its siblings
results/runs/<run_id>/
  slice-<N>.json                   the cumulative scoring sheet (gitignored, generated)
  model-report.json                one model's full run, reshaped (gitignored, generated)
results/leaderboard.json          the cross-model ranking, machine-readable (gitignored, generated)
results/leaderboard.md            the same ranking plus per-slice detail, for a human (gitignored, generated)
```

## Before you touch the hidden tests

**The obligation partition is the rubric weight.** A slice's correctness score is the equally weighted mean of its obligation groups. There is no other weighting, so how the tests are grouped *is* how they are weighted — a group holding one decisive assertion counts exactly as much as one holding twenty type checks. Balance by importance, never by test count, and read `docs/OBLIGATION-GROUPS.md` before regrouping anything.

**Never run both slices' hidden tests in one pytest invocation.** `slice1/` and `slice2/` each contain a `test_hA.py` and a `test_hB.py`, so a combined run fails module collection. This never arises operationally — slice 2 is not graded until slice 1 is accepted — and `dev_check.py` grades one slice per invocation by construction.
