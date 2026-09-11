# ai-agent-bench

Answers one operational question: **which local model should sit in the Developer seat of a real, supervised `project-manager` run on production scientific code?**

Real use of the `relative-velocity` pipeline showed local models converge on scientifically equivalent code but differ sharply in final code quality and in how many review/fix rounds it takes to get there. That variance is the thing worth measuring, and measuring it in the wild is expensive and unrepeatable. This repo is the repeatable offline stand-in: run a completely normal, unmodified `project-manager` Mode B session against a frozen two-slice plan, and grade what the Developer seat actually produced at every attempt along the way.

## The design in one paragraph

The PM session is not instrumented, wrapped, or told anything about this bench. The operator launches it exactly as they always do. `pm.py` already writes a rich, structured artifact trail — `run.json`, `events.jsonl`, per-slice diffs, reviewer reports — and this repo's tools read that trail from outside, strictly read-only: no run token, no writes to PM state, no `pm.py` subprocess, nothing added to the launcher prompt. That boundary is deliberate. The bench's premise is a normal supervised run, so anything this repo did to make measurement easier would contaminate the thing being measured.

What gets scored is a *trajectory*, not an end state: how many attempts a slice took, and what correctness, quality, scope discipline and review findings looked like at each one. The previous generation of this repo graded only the finished branch, which is why it never measured the iteration cost that motivated the whole exercise.

## How a run works

1. **Screen (optional, on by default).** The one-shot Task 001 screen on `main` ranks a candidate model cheaply before committing it to a full supervised run. Skippable per model via `policy.yaml`.
2. **The operator launches PM** — a normal Mode B session, unmodified launcher prompt, with the candidate model in the Developer seat. This repo never launches it. An agent spawning that session programmatically is refused by Claude Code's own permission classifier, and rightly so; an operator launching it personally has no friction at all.
3. **`tools/dev_check.py` grades one attempt.** It checks the attempt's commit out into a disposable worktree (never PM's, the Developer's, or a reviewer's directory), copies in that slice's held-out hidden tests, runs them, and scores them by acceptance obligation. It then measures quality independently — invoking `lint` and `code-health` directly rather than trusting whatever PM's prose assessment happened to mention — and recomputes scope discipline by calling `pm_lib`'s own `effective_authorized_files` helper directly, the same function PM's floor check calls, rather than reimplementing surface matching. This is not identical to floor's own check: floor passes the real `git status` text and folds in more evidence than surface matching alone (floor fact 5), where this tool passes an empty status text and looks only at the changed-file surface.
4. **`tools/review_score.py` harvests each commissioned review** (`--skill drift-audit` or `--skill code-review`) into the same attempt entry: findings by severity, per-section item counts, the verdict, and how many findings survive into the next attempt.
5. Both write to one cumulative scoring sheet per run and slice, `results/runs/<run_id>/slice-<N>.json`. Attempts accumulate; nothing is overwritten.
6. **`tools/run_seat.py` is the driver**: it does steps 3–4 automatically, so the operator doesn't have to. It polls `events.jsonl`/`run.json` externally — never launching or managing PM itself — and calls `dev_check.py`/`review_score.py` at every event this bench cares about (a `floor` from any `finalize`, an `accept` or `slice-stop` closing a slice out, a commissioned `review` landing), until the run reaches `complete` or `stopped` (`needs-human` is a pause the operator may resume from, not an end) and that status's own closing event has actually appeared in `events.jsonl`. `stopped` is this bench's own operating assumption of finality, matching the documented operator workflow — `project-manager` itself does not mechanically prevent a stopped run from being reactivated. It never invents grading logic of its own; it only decides when to call what steps 3–4 already do.

Still to build: the per-model report and the cross-model leaderboard. See `docs/MODE2-REWRITE-PLAN.md` §10.

## Usage

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Watch a live run and grade/harvest automatically until it finishes.
python tools/run_seat.py --run-dir <pm-run-dir>

# Or drive the same two steps by hand, one attempt/review at a time:
python tools/dev_check.py --run-dir <pm-run-dir> --slice 1
python tools/review_score.py --run-dir <pm-run-dir> --slice 1 --skill drift-audit
python tools/review_score.py --run-dir <pm-run-dir> --slice 1 --skill code-review

python -m pytest tests/ -q
```

`<pm-run-dir>` is PM's authoritative run directory, `<worktree-git-dir>/pm/<run-id>/` — find it with `git rev-parse --absolute-git-dir` in the Developer's repo. The in-worktree `.pm/` copy is a mirror for the Developer session to read, not the authority.

Both tools are pure, one-shot commands: given the same inputs, they measure the same correctness/quality/scope/review facts every time. Re-running one for the same attempt replaces that attempt's own row and refreshes its timestamp — not byte-identical (grading time is itself useful evidence, so it is kept, not suppressed), but every other attempt and every field the other tool wrote are left untouched. `dev_check.py` grades the current slice against the base commit PM records for it. Once a slice is accepted, PM clears that record, so the tool reuses the base commit an earlier grade of the same attempt already wrote into that attempt's own provenance — which means **a slice must be graded at least once while it is still current before its accepted attempt can be graded.** With no sheet to fall back on it refuses rather than guessing a base commit.

`policy.yaml` holds every path, threshold and tunable — prefilter and repeat defaults, the state-access backend, the interpreter used inside grading worktrees, and how often the driver polls (`driver_poll_interval_seconds`). Set `python_interpreter` to one with the Developer repo's own dependencies (numpy, scipy, h5py) installed; this repo's `requirements.txt` deliberately does not duplicate them. There is deliberately no reviewer-seat key: PM commissions whichever reviewer tool/model it judges right per slice, often a panel of several, so reviewer composition is recorded per-review (in `run.json`'s `reviews[].tool`/`.model`, harvested by `review_score.py`) rather than pinned in policy ahead of time.

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
tools/
  dev_check.py                     correctness, quality, scope for one attempt
  review_score.py                  drift-audit / code-review harvesting
  run_seat.py                      the driver -- watches a run, calls the two above
  bench_lib.py                     the few helpers all three tools share
tests/                             this repo's own test suite
results/runs/<run_id>/slice-<N>.json   the cumulative scoring sheet (generated)
```

## Two things worth knowing before you touch the hidden tests

**The obligation partition is the rubric weight.** A slice's correctness score is the equally weighted mean of its obligation groups. There is no other weighting, so how the tests are grouped *is* how they are weighted — a group holding one decisive assertion counts exactly as much as one holding twenty type checks. Balance by importance, never by test count, and read `docs/OBLIGATION-GROUPS.md` before regrouping anything.

**Never run both slices' hidden tests in one pytest invocation.** `slice1/` and `slice2/` each contain a `test_hA.py` and a `test_hB.py`, so a combined run fails module collection. This never arises operationally — slice 2 is not graded until slice 1 is accepted — and `dev_check.py` grades one slice per invocation by construction.
