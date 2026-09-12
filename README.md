# ai-agent-bench

Measures which local model should sit in the Developer seat of a real, supervised `project-manager` (PM) Mode B run on production scientific code — by running a completely normal, unmodified PM session against a frozen plan, then grading what the Developer seat produced from PM's own artifact trail.

Full design: `docs/MODE2-REWRITE-PLAN.md`. Contributor rules: `AGENTS.md`. Current state and next steps: `HANDOFF.md`.

## How it works

The PM session is never instrumented, wrapped, or told anything about this bench — the operator launches it exactly as they always do, with `project-manager`'s own unmodified launcher prompt. `pm.py` already writes a rich, structured artifact trail (`run.json`, `events.jsonl`, per-slice diffs, reviewer reports); this repo's tools read that trail from outside, strictly read-only — no run token, no writes to PM state, `pm.py` is never invoked as a subprocess, and nothing is ever added to the launcher prompt. That boundary is deliberate: the premise is a normal supervised run, so anything that made measurement easier by changing PM's behavior would contaminate the thing being measured.

What gets scored is a *trajectory*, not just an end state: how many attempts a slice took, and what correctness, quality, scope discipline, and reviewer findings looked like for every attempt a git-log walk can recover (falling back to just the final attempt where it can't — see `docs/MODE2-REWRITE-PLAN.md` §5).

## Steps to run a cohort member

1. **Launch PM yourself**, in your own interactive session, with `project-manager`'s `SKILL.md` launcher prompt — fill in the candidate model as the Developer seat, exactly as normal. Nothing here launches PM for you.
2. **Let PM supervise the run to completion.** It handles Developer sessions, commissions whatever reviewers it judges right per slice (often a panel of several models), and makes every accept/steer/stop decision on its own.
3. **Once the run is finished** — `run.json["status"]` is `complete`, or `stopped` with PM's own closing event on record (`needs-human` is a pause, not a finish) — grade it in one command:

   ```bash
   python tools/grade_run.py --run-dir <pm-run-dir>
   ```

   `<pm-run-dir>` is PM's authoritative run directory, `<worktree-git-dir>/pm/<run-id>/` (find it with `git rev-parse --absolute-git-dir` in the Developer's repo — the in-worktree `.pm/` copy is a mirror, not the authority). `grade_run.py` refuses to run against a run still in progress, and is always safe to re-run.
4. Fold the graded run into a per-model report:

   ```bash
   python tools/model_report.py --run-id <run-id>
   ```

   Once Tool 5 exists (not yet built — see `HANDOFF.md`), run `leaderboard.py` to fold every model report on disk into the cross-model summary.

You can run step 3 yourself, or separately tell the same or a fresh PM/agent session, once the plan is finished, to read this repo's instructions and run it — the tool doesn't care who invokes it, only that the run is actually over. Either way, nothing about grading is ever added to PM's own prompt.

## The tools

| Tool | What it does |
|---|---|
| `tools/grade_run.py` | Grades one **finished** run in a single pass: resolves each slice's final gradeable attempt, calls `dev_check.py` on it, then harvests every commissioned review via `review_score.py`. This is what you run. |
| `tools/dev_check.py` | Grades one specific attempt: checks its commit out into a disposable worktree, runs that slice's held-out hidden tests and scores them by acceptance obligation, independently invokes `lint`/`code-health` (never trusting PM's own prose about them), and recomputes scope discipline via `pm_lib`'s own `effective_authorized_files` helper. Callable directly for a manual/ad-hoc grade. |
| `tools/review_score.py --skill drift-audit\|code-review` | Harvests one commissioned reviewer's report into the matching attempt: findings by severity, per-section item counts, the verdict, and how many findings survive into the next reviewed attempt. |
| `tools/bench_lib.py` | Shared helpers (attempt numbering, event-log reading, atomic JSON writes) — not a CLI tool. |
| `tools/model_report.py` | Gathers one model's full run (every `slice-<N>.json` sheet under `results/runs/<run_id>/`) into one report: final correctness/quality/scope and attempt count per slice, the review-finding trend across attempts, and PM's own `model-performance.md` rating — read back verbatim and kept in its own field, never blended into the deterministic scores. Invents no composite score; writes `results/runs/<run_id>/model-report.json`. |
| `tools/leaderboard.py` | **Not yet built.** Cross-model summary from every model report on disk. |

`dev_check.py` and `review_score.py` are both pure, one-shot, idempotent commands — the same inputs always produce the same measurement, and re-running one for an already-graded attempt refreshes only its own fields, never disturbing anything the other tool wrote. Both write into one cumulative scoring sheet per run and slice, `results/runs/<run_id>/slice-<N>.json`.

**Known scope limit:** every attempt of a slice gets a deterministic grade when a git-log walk recovers exactly one commit per attempt between the slice's own before_head and its final commit; a slice whose history doesn't satisfy that (most commonly a multi-epoch first slice with no review recorded from its earliest epoch) falls back to grading only its *final* attempt, reported as a named problem, not silently. A review commissioned against an attempt with no sheet row is likewise reported as a named, loud problem when harvested — never silently dropped. The attempt count and PM's per-attempt decision (steer/accept/stop) are unaffected either way, since both come from `events.jsonl` directly for every attempt. See `docs/MODE2-REWRITE-PLAN.md` for the full reasoning.

## Setup

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

python -m pytest tests/ -q
```

`policy.yaml` holds every path, threshold, and tunable this repo uses — nothing is hardcoded in the tools. Set `python_interpreter` to one with the Developer repo's own dependencies installed (numpy, scipy, h5py for `relative-velocity`); this repo's own `requirements.txt` deliberately doesn't duplicate them. There's no reviewer-seat key: PM commissions whichever reviewer tool/model it judges right per slice, and that composition is recorded per-review (`run.json`'s `reviews[].tool`/`.model`) rather than pinned in policy ahead of time. There's also no one-shot pre-filter key — that idea was considered and dropped (see `docs/MODE2-REWRITE-PLAN.md`).

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
