# ai-agent-bench

Measures which local model should sit in the Developer seat of a real, supervised `project-manager` (PM) Mode B run on production scientific code — by running a completely normal, unmodified PM session against a frozen plan, then grading what the Developer seat produced from PM's own artifact trail.

Full design: `docs/MODE2-REWRITE-PLAN.md`. Contributor rules: `AGENTS.md`. Current state and next steps: `HANDOFF.md`.

## How it works

The PM session is never instrumented, wrapped, or told anything about this bench — the operator launches it exactly as they always do, with `project-manager`'s own unmodified launcher prompt. `pm.py` already writes a rich, structured artifact trail (`run.json`, `events.jsonl`, per-slice diffs, reviewer reports); this repo's tools read that trail from outside, strictly read-only — no run token, no writes to PM state, `pm.py` is never invoked as a subprocess, and nothing is ever added to the launcher prompt. That boundary is deliberate: the premise is a normal supervised run, so anything that made measurement easier by changing PM's behavior would contaminate the thing being measured.

What gets scored is a *trajectory*, not just an end state: how many attempts a slice took, and what correctness, quality, scope discipline, and reviewer findings looked like for every attempt a git-log walk can recover (falling back to just the final attempt where it can't — see `docs/MODE2-REWRITE-PLAN.md` §5).

## Steps to run a cohort member

This bench tests exactly one frozen plan (`docs/MERGER_RATE_PLAN-2SLICE.md`, vendored from `relative-velocity` at a pinned commit — see `docs/MERGER_RATE_PLAN-2SLICE.provenance.md`), so a trial's `Repo:`/`Plan file:` never need hand-typing: `tools/cohort_run.py` (Tool 6 — see below; it invents no measurement of its own, only sequencing and preparation) derives them for you. The whole flow:

1. **Create a trial worktree and print the launcher prompt for it** — a fresh git worktree of `policy.yaml`'s `relative_velocity_repo`, checked out from this bench's pinned plan commit (parsed live, never duplicated), on its own branch (`pm-eval-v2/<label>`, auto-numbered from `trial` unless `--label` names it yourself):

   ```bash
   python tools/cohort_run.py setup
   ```

   Copy the printed prompt into a brand-new PM-capable session (not this one) — `Repo:`/`Plan file:` are already filled in — fill in the `Developer:`/`Reviewer:` harness and model by hand, and send it. Who plays either seat is entirely your own choice made in the pasted prompt; this tool has no flag for it. Already have a prepared repo you'd rather use instead? Pass `--repo <path>` to skip worktree creation entirely.
2. **Let PM supervise the run to completion.** It handles Developer sessions, commissions whatever reviewers it judges right per slice (often a panel of several models), and makes every accept/steer/stop decision on its own. Nothing here launches PM for you, and never will.
3. **Once the run is finished** — `run.json["status"]` is `complete`, or `stopped` with PM's own closing event on record (`needs-human` is a pause, not a finish) — grade it, build its per-model report, and refold the cross-model leaderboard in one command (`setup` already printed the exact one to run, pointed at the trial worktree it created):

   ```bash
   python tools/cohort_run.py analyze --dev-repo <dev-repo>
   ```

   `<dev-repo>` resolves to PM's one run directory under that repo's git state automatically (refusing by name if more than one exists there — pass `--run-dir <pm-run-dir>` explicitly to pick one then). `analyze` refuses to grade a run still in progress, and is always safe to re-run.
4. Check `results/leaderboard.json`. Once you're done with a trial's worktree, `python tools/cohort_run.py cleanup --label <label>` removes it (dry run by default; `--yes` to actually remove; an ungraded trial is flagged with a warning, not refused). Its branch is left in place either way. Separately, `python tools/cohort_run.py reset-leaderboard` archives (never deletes) `results/` itself, for starting a whole cohort pass over clean.

You can run step 3 yourself, or separately tell the same or a fresh PM/agent session, once the plan is finished, to read this repo's instructions and run it — the tool doesn't care who invokes it, only that the run is actually over. Either way, nothing about grading is ever added to PM's own prompt.

`cohort_run.py analyze` is exactly the same as running the three scoring tools by hand, in order, and either path is fine:

```bash
python tools/grade_run.py --run-dir <pm-run-dir>
python tools/model_report.py --run-id <run-id>
python tools/leaderboard.py
```

## The tools

| Tool | What it does |
|---|---|
| `tools/grade_run.py` | Grades one **finished** run in a single pass: resolves each slice's final gradeable attempt, calls `dev_check.py` on it, then harvests every commissioned review via `review_score.py`. This is what you run. |
| `tools/dev_check.py` | Grades one specific attempt: checks its commit out into a disposable worktree, runs that slice's held-out hidden tests and scores them by acceptance obligation, independently invokes `lint`/`code-health` (never trusting PM's own prose about them), and recomputes scope discipline via `pm_lib`'s own `effective_authorized_files` helper. Callable directly for a manual/ad-hoc grade. |
| `tools/review_score.py --skill drift-audit\|code-review` | Harvests one commissioned reviewer's report into the matching attempt: findings by severity, per-section item counts, the verdict, and how many findings survive into the next reviewed attempt. |
| `tools/bench_lib.py` | Shared helpers (attempt numbering, event-log reading, atomic JSON writes) — not a CLI tool. |
| `tools/model_report.py` | Gathers one model's full run (every `slice-<N>.json` sheet under `results/runs/<run_id>/`) into one report: final correctness/quality/scope and attempt count per slice, the review-finding trend across attempts, and PM's own `model-performance.md` rating — read back verbatim and kept in its own field, never blended into the deterministic scores. Invents no composite score; writes `results/runs/<run_id>/model-report.json`. |
| `tools/leaderboard.py` | Folds every `model-report.json` on disk into one cross-model leaderboard: groups by model (a model can have several runs — `policy.yaml`'s `repeats`), reduces every graded slice to four deterministic sub-scores (correctness, quality, scope, iterations) and blends them into a `composite_score` weighted by `policy.yaml`'s `leaderboard` section. PM's own subjective rating is carried through per run, verbatim, never blended into the composite. Writes `results/leaderboard.json`. |
| `tools/cohort_run.py` | Operator convenience wrapper, not a scoring tool: `setup` creates a fresh trial worktree of `relative_velocity_repo` (unless `--repo` given) and prints project-manager's own launcher prompt (extracted live from `SKILL.md`, never a stale copy) for it, plus the steps to follow; `analyze` runs `grade_run.py` → `model_report.py` → `leaderboard.py` for one finished run in a single command; `cleanup` removes a trial's worktree (never its branch); `reset-leaderboard` archives (never deletes) old `results/` output. Never launches PM, never writes into a Developer/PM directory. |

`dev_check.py` and `review_score.py` are both pure, one-shot, idempotent commands — the same inputs always produce the same measurement, and re-running one for an already-graded attempt refreshes only its own fields, never disturbing anything the other tool wrote. Both write into one cumulative scoring sheet per run and slice, `results/runs/<run_id>/slice-<N>.json`.

**Known scope limit:** every attempt of a slice gets a deterministic grade when a git-log walk recovers exactly one commit per attempt between the slice's own before_head and its final commit; a slice whose history doesn't satisfy that (most commonly a multi-epoch first slice with no review recorded from its earliest epoch) falls back to grading only its *final* attempt, reported as a named problem, not silently. A review commissioned against an attempt with no sheet row is likewise reported as a named, loud problem when harvested — never silently dropped. The attempt count and PM's per-attempt decision (steer/accept/stop) are unaffected either way, since both come from `events.jsonl` directly for every attempt. See `docs/MODE2-REWRITE-PLAN.md` for the full reasoning.

## Setup

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

python -m pytest tests/ -q
```

`policy.yaml` holds every path, threshold, and tunable this repo uses — nothing is hardcoded in the tools. Set `python_interpreter` to one with the Developer repo's own dependencies installed (numpy, scipy, h5py for `relative-velocity`); this repo's own `requirements.txt` deliberately doesn't duplicate them. `relative_velocity_repo` defaults to `substrate/relative-velocity` — a local clone vendored under this repo (gitignored) so `cohort_run.py setup` is self-contained and immune to your own working checkout of `relative-velocity` moving, being on the wrong branch, or having uncommitted changes. If it's ever missing (a fresh clone of this bench, or after deleting it), repopulate it once with `git clone git@github.com:darrencroton/relative-velocity.git substrate/relative-velocity` (`dev_branch_prefix`/`dev_worktree_root` control where and how trial worktrees/branches are named). There's no reviewer-seat key: PM commissions whichever reviewer tool/model it judges right per slice, and that composition is recorded per-review (`run.json`'s `reviews[].tool`/`.model`) rather than pinned in policy ahead of time. There's also no one-shot pre-filter key — that idea was considered and dropped (see `docs/MODE2-REWRITE-PLAN.md`).

## Repo layout

```text
docs/
  MODE2-REWRITE-PLAN.md            the design, and the authority for it
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
results/runs/<run_id>/slice-<N>.json   the cumulative scoring sheet (gitignored, generated)
```

## Before you touch the hidden tests

**The obligation partition is the rubric weight.** A slice's correctness score is the equally weighted mean of its obligation groups. There is no other weighting, so how the tests are grouped *is* how they are weighted — a group holding one decisive assertion counts exactly as much as one holding twenty type checks. Balance by importance, never by test count, and read `docs/OBLIGATION-GROUPS.md` before regrouping anything.

**Never run both slices' hidden tests in one pytest invocation.** `slice1/` and `slice2/` each contain a `test_hA.py` and a `test_hB.py`, so a combined run fails module collection. This never arises operationally — slice 2 is not graded until slice 1 is accepted — and `dev_check.py` grades one slice per invocation by construction.
