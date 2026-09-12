# Design: PM-Only Evaluation

**Status:** All five scoring tools are built, tested, and validated against a real completed PM run: Tools 1-3 (`tools/dev_check.py`, `tools/review_score.py`), the grader (`tools/grade_run.py`), Tool 4 (`tools/model_report.py`), and Tool 5 (`tools/leaderboard.py`). G16 (§8) — grading every attempt, not just each slice's final one — is resolved via the git-log walk. A sixth, operator-convenience tool, `tools/cohort_run.py` (§6), wraps `setup`/`analyze`/`cleanup`/`reset-leaderboard` around the five scoring tools without adding any new measurement — it never launches PM. The tool suite is complete; see `HANDOFF.md` for exactly where a fresh session should pick up (running real cohort members through it).

This document describes what the system is and how it works. For how it got this way, see the History appendix at the end — read it only if you need the reasoning behind a specific decision.

## 1. What this measures

Which local model should sit in the Developer seat of a real, supervised `project-manager` Mode B run on production scientific code? Local models tend to converge on scientifically equivalent code but differ sharply in final quality and in how many review/fix iterations it takes to get there. That variance is the thing worth measuring, repeatably and offline — not by using a model "in the wild" and hoping.

The method: run a real, **completely normal, unmodified** `project-manager` Mode B session against a frozen two-slice plan (`docs/MERGER_RATE_PLAN-2SLICE.md`, vendored from `relative-velocity` at a pinned commit), with the candidate model in the Developer seat. Once the run is finished, grade it from PM's own artifact trail — correctness against held-out hidden tests, independently measured code quality, scope discipline, and every commissioned reviewer's findings — for every attempt of every slice that a git-log walk can recover (§5), falling back to just the final attempt only where it can't. This is a *trajectory*, not just an end state: how many attempts a slice took, and what each reviewer found, are as much the measurement as the final code's quality.

## 2. Design principles

- **The PM session is never instrumented, wrapped, or told anything about this bench.** The operator launches it exactly as they always do (`project-manager`'s own `SKILL.md` launcher prompt, unmodified, every field filled in normally). Anything that made measurement easier by changing what PM does would contaminate the thing being measured.
- **Everything this repo does to a PM run is read-only.** No run token, no writes to PM state, `pm.py` is never invoked as a subprocess — `pm_lib` is imported as a library for its plan/git helpers only.
- **Deterministic first.** Correctness and quality are measured by tools, not by asking a model to judge a model. An LLM judge is a fallback for if a deterministic proxy proves insufficient, never a default.
- **Externalize policy as data.** Every path, threshold, and tunable lives in `policy.yaml`. A policy change must never require a code change.
- **Fail loudly, never guess.** An unavailable linter is recorded as unavailable, never as a clean pass. A base commit that cannot be safely resolved is a named, refused grading target, never a silent default to whatever HEAD happens to be. A stale sheet, a mismatched run, a partial review report — every one of these is a named error, never a quiet zero.
- **Minimum, no dead code.** Every file is load-bearing. A prior repo's useful *pattern* (fail-closed scope checks, provenance hashing) is reimplemented fresh and small, never carried over wholesale from code written for a different purpose.
- **Grading is isolated from the PM/Developer run.** Every grading pass checks out the commit under test into a fresh, disposable git worktree — never PM's or the Developer's own working directory.

## 3. Repo layout

```text
docs/
  MODE2-REWRITE-PLAN.md            this file
  MERGER_RATE_PLAN-2SLICE.md       the frozen plan PM runs against, vendored
                                    from relative-velocity at a pinned commit
  MERGER_RATE_PLAN-2SLICE.provenance.md   that pin
  OBLIGATION-GROUPS.md             how the hidden tests are partitioned, and why
  reference-impl/README.md         evidence the hidden tests are correct and
                                    discriminating, plus how to reproduce it
hidden_tests/
  slice1/, slice2/                 held-out tests, one directory per slice
  obligations.yaml                 the acceptance-obligation partition
policy.yaml                        every weight, threshold and tool path
requirements.txt                   this repo's own dependencies (pyyaml, pytest)
tools/
  dev_check.py                     correctness, quality, scope for one attempt
  review_score.py                  drift-audit / code-review harvesting
  grade_run.py                     grades one FINISHED run in a single pass
  model_report.py                  Tool 4: one model's full run, reshaped
  leaderboard.py                   Tool 5: the cross-model composite
  cohort_run.py                    Tool 6: setup / analyze / cleanup / reset-leaderboard wrapper
  bench_lib.py                     helpers shared by the scoring tools above
tests/                             this repo's own test suite
results/runs/<run_id>/slice-<N>.json   the cumulative scoring sheet (gitignored, generated)
results/runs/<run_id>/model-report.json   Tool 4's output (gitignored, generated)
results/leaderboard.json          Tool 5's output (gitignored, generated)
```

`results/` is gitignored: a single scoring sheet's raw code-health payload can run to over a thousand lines, and this is regenerable per-run evidence, not project source (same rationale as `.orchestrator/`/`archive/`).

## 4. How a run works, end to end

1. **The operator launches PM** — a normal Mode B session, `SKILL.md`'s unmodified launcher prompt, with the candidate model in the Developer seat. This repo never launches it, and never adds anything to that prompt. `python tools/cohort_run.py setup --harness <...> --model <candidate>` creates a fresh trial worktree of `policy.yaml`'s `relative_velocity_repo` (checked out from this bench's one pinned plan commit, on its own `pm-eval-v2/<label>` branch) and prints that exact prompt (extracted live from project-manager's own `SKILL.md`, never a hardcoded copy — see §6's Tool 6) with `Harness:`/`Plan file:`/`Repo:` already filled in, plus these same steps, so there is nothing to hand-assemble or hand-type. `--repo <path>` skips worktree creation and uses an already-prepared repo instead.
2. **PM supervises the run to completion**: Developer sessions per slice, reviews it commissions on its own judgment (often a panel of several reviewer models, harvested per-review by Tools 2/3 — §6), and accept/steer/stop decisions, exactly as an ordinary Mode B run.
3. **Once the run is finished** — `run.json["status"]` is `complete`, or `stopped` with PM's own closing event on record; `needs-human` is a pause, not a finish — grade it, build its per-model report, and refold the cross-model leaderboard in one command:

   ```bash
   python tools/cohort_run.py analyze --run-dir <pm-run-dir>
   ```

   `<pm-run-dir>` is PM's authoritative run directory, `<worktree-git-dir>/pm/<run-id>/` (find it with `git rev-parse --absolute-git-dir` in the Developer's repo — the in-worktree `.pm/` copy is a mirror, not the authority; `--dev-repo <dev-repo>` does that resolution for you when exactly one run exists under it). `analyze` is `grade_run.py` → `model_report.py` → `leaderboard.py`, run as three in-process calls, in that order; each step's own refusal is reported without aborting a later step that can still proceed. Equivalently, the same three tools can still be run by hand, one at a time (below) — `cohort_run.py` adds no new measurement, only sequencing. `grade_run.py` refuses to run against anything that isn't confirmed finished.

   ```bash
   python tools/grade_run.py --run-dir <pm-run-dir>
   python tools/model_report.py --run-id <run-id>
   python tools/leaderboard.py
   ```

4. **Who runs step 3, and when, is the operator's call** — not fixed by this design. The operator can run it themselves the moment PM reports done, or separately tell the same or a fresh PM/agent session, once the plan is finished, to read this repo's instructions and run it. Both are fine: the tool doesn't care who invokes it, only that the run is actually over. (This is a different question from "should PM invoke bench tooling *while* supervising" — that stays rejected, for the same reason PM's prompt is never modified: it risks contaminating the judgment being measured. Running a read-only report *after* every decision is already locked into `run.json` carries no such risk.)
5. Check `results/leaderboard.json`. Once a trial's worktree is no longer needed, `python tools/cohort_run.py cleanup` removes it (never its branch; dry run by default, `--yes` to actually remove, an ungraded trial flagged with a warning rather than refused). Separately, `python tools/cohort_run.py reset-leaderboard` archives (never deletes) `results/` itself, for starting a whole cohort pass over clean.

## 5. Grading design: a single pass over a finished run

Grading happens once, after the run is over — not by watching PM live. This is correct, not just simpler, because the two facts that matter are both permanent and structural, recoverable from `run.json`/`events.jsonl` alone with no live state needed:

- **A slice's `before_head`** (the commit correctness/quality/scope are measured against) is set once, at `start_slice`, and preserved unchanged across every relaunch/steer within one uninterrupted in-flight epoch (`pm_lib/prompts.py`; verified against `pm_lib/slice_ops.py`'s `start_slice`). It is not permanent across a stop-then-restart of the same slice, which captures a fresh value — `dev_check.resolve_before_head` (below) accounts for this.
- **A slice's ending commit**, once accepted, is permanently recorded (`run.json`'s `entry["commit"]`, set by `finalize_accept`). Mode B processes slices strictly in plan order and gates progression on acceptance (or an operator's `--attest`), so at most one slice in a finished run can be non-accepted, and only if it's the last one PM ever touched.

`tools/dev_check.py`'s `resolve_before_head` resolves the base commit in this order, each one cheaper/more authoritative than the next:

1. An explicit `--before-head` override, if the caller supplied one.
2. `current_slice.before_head`, if this slice is still live (only relevant when grading manually, mid-run).
3. This attempt's own previously recorded `provenance.base_commit`, if it was graded before.
4. Structurally, from `run.json` alone: the immediately preceding slice's recorded `commit` (for any slice past the first, if that predecessor was actually run through PM and accepted — an `attested`, operator-approved predecessor never records a commit and falls through to the next option); or, for any slice including the first, the most recent review commissioned against it whose `head` matches this slice's own recorded accepted commit — a guarantee, not a heuristic, because reviews record the exact commit they ran against and this bench's plan mandates a fresh review before acceptance. (Recency by list position alone is *not* used for an accepted slice: reviews commission concurrently, and a slow, earlier-epoch review's report can be parsed and appended after a faster, current-epoch one — filtering by exact `head` match avoids that race entirely.)

`tools/grade_run.py` uses this to grade every slice in one pass:

- Refuses to run unless `run.json["status"]` is `complete` or `stopped` *and* PM's own closing event for that status exists anywhere in `events.jsonl` (not merely as the most recent tracked event — PM saves status before appending the matching event, and an unrelated trailing event, like a routine `stop` issued after a run already completed, must not mask an earlier real closing event).
- For each slice, resolves its final attempt's ordinal from `events.jsonl` and its ending commit: an accepted slice's recorded `commit`; a non-accepted slice is always refused (never defaulted to the repo's current HEAD) — a top-level `pm stop` can end an in-progress attempt with no commit recorded and no clean-worktree guarantee, and a stopped run can be reactivated later, so nothing about "current HEAD" is safe to assume for that case. Grade a stopped, non-accepted slice by hand with `dev_check.py --commit <sha>` once you've independently confirmed the right commit.
- **G16, resolved — grades every attempt, not just the final one**, via `_resolve_attempt_grading_plan`/`resolve_attempt_commits` (`tools/grade_run.py`): git history is permanent and continuous across any PM-level "epoch" boundary (a `finalize --stop` followed by a later restart), so walking `git log --reverse` between a slice's own before_head and its final commit recovers one ending commit per attempt, in order, one commit per attempt-family event recorded in `events.jsonl`. That before_head is this slice's *original* one — the previous slice's own recorded commit, when one exists, not whatever `resolve_before_head` would return for grading a single already-decided attempt (which deliberately favors the most recent epoch, and would silently truncate a multi-epoch slice's walk to just its last epoch). This relies on the Developer contract's one-commit-per-attempt convention, not a mechanical guarantee `pm_lib` enforces, so the walk is a named refusal whenever it doesn't hold exactly (a merge commit in range, a `before_head` that isn't an ancestor of the final commit, or a commit count that doesn't match the attempt count) — never a partial or guessed mapping. A slice whose walk refuses falls back, on its own, to grading only its final attempt (the pre-G16 behavior), with the refusal reported as a named problem, never silently.
- Harvests every commissioned review for every attempt found in the event log — every one of which now typically has a sheet row to attach to, not just the final attempt's.
- Is fully idempotent — safe to re-run any time, including immediately, if in doubt about a narrow timing edge in the terminal-status check above.

**Residual scope limit (G16's honest edge):** a slice whose commit history doesn't satisfy the walk's one-commit-per-attempt convention exactly still gets only its final attempt deterministically graded (hidden tests, lint, code-health, scope) — most commonly a multi-epoch *first* slice (no predecessor's commit to fall back on for its walk-start, and `resolve_before_head`'s own rule for an accepted slice only ever returns the most recently-accepted epoch's before_head, never an earlier one, *even when a review from that earlier epoch was recorded* — a first slice that itself restarted always falls back here, not just when its earliest epoch went unreviewed), or any slice where the Developer's own commit-per-attempt convention didn't hold. A review commissioned against an attempt with no sheet row is still reported as a named, loud problem when harvested, never silently dropped. The attempt *count* and PM's per-attempt *decision* (steer/accept/stop) are unaffected by any of this — both come from `events.jsonl` directly, for every attempt, regardless of which ones got a deterministic grade.

**Per-attempt fidelity within a slice:** `before_head` is constant across every attempt sharing one PM "epoch" (a `launch` through the `relaunch`/`steer`s that follow it, before the next `launch`), resetting only at the next epoch's own start — not, as an earlier draft of this walk incorrectly assumed, advancing to the immediately preceding attempt's own commit on every attempt uniformly. That incremental assumption was caught (by an independent review round, then verified against the real completed run's own regenerated sheet before this was written) as a real bug: it would silently miss a scope violation or quality finding introduced early in a slice and left untouched by a later attempt, since nothing changed in that specific incremental diff. PM's own `pm_attempts_counter` is not constant within an epoch — it increments by 1 on every attempt, same as before — but it resets to 0 at exactly the same epoch boundary `before_head` does, so both are governed by the one `bench_lib.epoch_start_ordinals` helper, which derives each attempt's epoch boundary directly from `events.jsonl` (PM's own counter resets/increments in exact lockstep with the same launch-family events, verified against `pm_lib.slice_ops.start_slice`/`steer`). `tools/grade_run.py`'s per-attempt `before_head` and `tools/dev_check.py`'s `resolve_pm_attempts_counter` are both built on it.

## 6. The tools

### Tool 1 — `dev_check.py`: correctness, quality, scope for one attempt

A pure, one-shot grading command: given a run directory, a slice number, and (optionally) an explicit attempt/commit, it checks that attempt's commit out into a disposable worktree, copies in that slice's held-out hidden tests, runs them, and scores them per acceptance-obligation group (`hidden_tests/obligations.yaml` — the partition *is* the correctness rubric; see `docs/OBLIGATION-GROUPS.md`). It then measures quality independently — invoking the `lint` and `code-health` skills directly, never trusting whatever PM's own prose assessment happened to mention — and recomputes scope discipline by calling `pm_lib.plan.effective_authorized_files` directly, the same function PM's own floor check uses. Quality tools run *before* the hidden tests are copied in (both use differential `--base` mode, which would otherwise attribute this bench's own test files to the Developer).

Output: upserts one entry into that slice's cumulative scoring sheet (§7), keyed by the monotonic event-derived attempt ordinal (`bench_lib.attempt_ordinal` — never PM's own `attempts` counter, which resets to 0 whenever a stopped slice is restarted and so cannot be a stable key).

### Tools 2/3 — `review_score.py --skill drift-audit|code-review`: harvest, not invoke

One script, parameterized by which report it's reading (drift-audit and code-review harvesting are identical logic against two report shapes). It extracts deterministic structure from a commissioned reviewer's report — findings by severity, per-section item counts, the verdict, how many findings survive into the next *reviewed* attempt — never a holistic "how good was this review" score, which has no ground truth to check against. Reads the report only after verifying its recorded sha256 against `run.json`'s entry (the in-worktree mirror copy is written non-atomically, so file-existence alone isn't a safe read signal).

Fully idempotent and re-derives its canonical review set from the full event log every call, so it is always safe to re-run: it processes every attempt's canonical review independently, skipping (and reporting, not raising for) an attempt with no sheet row to attach to rather than aborting the whole harvest at the first one found.

### Tool 4 — `model_report.py`

Gathers one model's full run into a per-model report: reads every `slice-<N>.json` sheet under `results/runs/<run_id>/` and reshapes them into one document — final correctness/quality/scope and attempt count per slice, and the review-finding trend across attempts (`drift_review`/`code_review`, one entry per attempt that commissioned it). It invents no new scoring math and no composite score (that is Tool 5's job, driven by `policy.yaml`); every field is a direct pass-through or reshape of data `dev_check.py`/`review_score.py` already computed.

It also folds in PM's own `rate --text` comparative rating (`model-performance.md`, referenced by each sheet's `pm_model_performance_ref`), read back verbatim into a `pm_subjective_rating` block — kept **strictly separate** from the deterministic scores, never parsed into structured numbers, and never blended into them. The two signals differ in repeatability (the deterministic scores are comparable across runs; PM's rating is a within-run judgment call) and averaging them would destroy that distinction silently. A rating never recorded is an honest `available: false`, not an error; a rating recorded but since vanished from disk is a named problem.

Writes `results/runs/<run_id>/model-report.json`. Sheets that disagree on `model`, `run_status.pm_status`/`.stop_reason`, or a non-null `pm_model_performance_ref` are refused outright — these all come from the same run.json, so disagreement is corruption, never something to average or guess past.

### Tool 5 — `leaderboard.py`

Rebuilds the cross-model summary from every Tool 4 report on disk (`results/runs/*/model-report.json`), grouped by each report's own `model` field — a model can have several runs on disk (`policy.yaml`'s `repeats` documents this). It flattens every graded slice from every one of a model's runs into one list of slice-records (equal weight per slice-record, no per-run or per-slice-number weighting) and reduces each record to four deterministic sub-scores:

- **correctness** — the equally-weighted mean of a final attempt's own obligation-group `fraction`s (never the raw `hidden_tests_passed/total`, which would double-count a large group; the obligation partition *is* the rubric weight, per `AGENTS.md`).
- **quality** — the mean of whichever of the two quality tools (`lint_findings_by_tool`, `code_health_findings_by_category`) were `available` on the final attempt, each contributing 1.0 for a `pass` verdict else 0.0; an unavailable tool is excluded from the mean, never scored as a pass.
- **scope** — 1.0 with no scope violations on the final attempt, else penalized per violation and floored at 0.0.
- **iterations** — defined only for an accepted slice (an unaccepted one is counted separately, as `unaccepted_slices`, never scored here); the reference-attempts count over the actual attempt count, capped at 1.0.

A slice-record missing the data a sub-score needs is excluded from that sub-score's mean (never scored as 0) and named in `problems`. Per model, the four sub-score means blend into one `composite_score`, renormalized over whichever weights have data when one sub-score mean is `None` for that model (never treating the gap as a 0) — and `composite_score` itself is `None`, never a fabricated number, if literally none of the four have any data. Every weight and threshold (`weights.correctness/quality/scope/iterations`, `scope_violation_penalty`, `iteration_reference_attempts`) lives in `policy.yaml`'s `leaderboard` section — Tool 5 hardcodes no fallback default, and fails loudly if the weights don't sum to 1.0 or any required key is missing.

PM's own subjective rating is carried through per run, verbatim, in `pm_subjective_ratings` — never blended into `composite_score`, same separation principle as Tool 4. PM-run data only — there is no one-shot pre-filter screen feeding into this (§8).

Writes `results/leaderboard.json`, sorted by `composite_score` descending (`None` last, ties broken by `model` name ascending).

### Tool 6 — `cohort_run.py`: operator convenience wrapper

Not a scoring tool — it invents no measurement of its own, reads no `run.json`/`events.jsonl`, and computes nothing Tools 1-5 don't already compute. It exists only to remove hand-assembly and hand-sequencing around them, and it must never grow a code path that crosses the boundaries §2 states: it never launches PM, never writes into a Developer/PM directory, and never touches a run in progress.

- **`setup`** creates a fresh trial worktree of `policy.yaml`'s `relative_velocity_repo` (unless `--repo` is given) and prints project-manager's own launcher prompt for it (§4 step 1), ready to paste. Creating/removing a worktree of the substrate repo is not "launching PM" or "adding to its prompt" (§2) — it is ordinary git housekeeping the operator would otherwise do by hand before pasting the prompt into their own harness. The worktree is created on branch `<dev_branch_prefix>/<label>` (default `pm-eval-v2`), checked out from this bench's one pinned plan commit — parsed live from `docs/MERGER_RATE_PLAN-2SLICE.provenance.md`'s own "Pinned commit" line, never a second, driftable copy of that hash — under `dev_worktree_root` (default: a sibling directory of `relative_velocity_repo`). `--label` names the trial explicitly (refusing, by name, a collision with an existing branch or worktree directory); omitted, it's derived from `--model`/`--harness` and auto-numbered so repeats never collide. The prompt text itself is extracted live from `SKILL.md`'s own `## Launcher` fenced block (via `policy.yaml`'s existing `pm_scripts_dir`) every time this runs, never a copy kept in this repo — the launcher's *wording* isn't something this bench scores (unlike the frozen plan, G8), so a stale local copy could only mislead an operator about what project-manager currently asks for. `--harness`/`--model` fill in the template's `Harness:` line (harness always first, matching `SKILL.md`'s own field order); `Repo:`/`Plan file:` are derived from the created worktree unless `--repo`/`--plan-file` override them. There is deliberately no reviewer-seat flag: PM commissions whichever reviewer tool/model it judges right per slice (policy.yaml carries no reviewer-seat key for the same reason), and `setup`'s own printed output says so.
- **`analyze`** runs `grade_run.py` → `model_report.py` → `leaderboard.py` against one finished run (§4 step 3), in-process (each tool's own `main(argv)`, the same in-process-call pattern `grade_run.py` already uses for `dev_check.main()`), never as subprocesses. `--run-dir` names the run directly; `--dev-repo` resolves it via `git rev-parse --absolute-git-dir` + `/pm/` (§4's own resolution recipe), refusing by name, never guessing, if more than one run directory exists there. A step's own refusal (its `bench_lib.BenchLibError` subclass) is caught, reported, and does not stop a later step from running — `model_report.py`/`leaderboard.py` still operate correctly on whatever other data already exists on disk even when this run's own grading failed. The command's exit code is the max across every step it ran.
- **`cleanup`** removes a trial's worktree (never its branch — cheap, recoverable history left in place, per `AGENTS.md`'s "archive, never delete" spirit) via `git worktree remove`. `--label` scopes to one trial; omitted, every worktree under `dev_branch_prefix/*` is targeted. Dry-run by default; `--yes` actually removes; `--force` passes through to `git worktree remove` for a dirty worktree. An ungraded trial (no `model-report.json` recorded for any PM run found in it) is flagged with a warning, never refused outright — the operator may deliberately not want to grade every trial, an explicit operator decision this tool does not second-guess.
- **`reset-leaderboard`** archives (`AGENTS.md`: "archive, never delete") this repo's own regenerable `results/` output into a dated `archive/results-<UTC timestamp>/` directory (or one scoped to a single `--run-id`), so a fresh cohort pass can start clean without losing any prior run's evidence. Dry-run by default — nothing moves until `--yes` is given.

## 7. The scoring sheet

One JSON document per `(run_id, slice)`, upserted across attempts, never overwritten:

```json
{
  "run_id": "...",
  "model": "opencode-go/mimo-v2.5-pro",
  "slice": 1,
  "run_status": {
    "pm_status": "active | needs-human | complete | stopped",
    "slice_status": "null | accepted | attested | stopped",
    "stop_reason": "... | null",
    "infrastructure_failure_suspected": false
  },
  "attempts": [
    {
      "attempt": 0,
      "pm_attempts_counter": 0,
      "commit_sha": "...",
      "timestamp": "...",
      "provenance": {"plan_hash": "...", "policy_hash": "...", "obligations_hash": "...", "base_commit": "...", "pm_skill_version": "..."},
      "correctness": {"hidden_tests_passed": 41, "hidden_tests_total": 46, "by_obligation": {"...": {}}},
      "quality": {"lint_findings_by_tool": {"...": {}}, "code_health_findings_by_category": {"...": {}}},
      "scope": {"violations": []},
      "drift_review": {"commissioned": true, "report_ref": "...", "report_sha256": "...", "findings_by_severity": {"...": 0}, "open_after_this_attempt": 2},
      "code_review": {"commissioned": true, "report_ref": "...", "report_sha256": "...", "findings_by_severity": {"...": 0}, "open_after_this_attempt": 1},
      "pm_decision": "steer"
    }
  ],
  "accepted_at_attempt": 3,
  "pm_model_performance_ref": ".pm/runs/.../model-performance.md"
}
```

Field notes:

- **Key**: `(run_id, slice_id, attempt)`. `attempt` is `bench_lib.attempt_ordinal`'s value — the count of `launch`/`relaunch`/`steer` events recorded for the slice, minus one; 0-based, and monotonic across a stop/restart cycle (a restart's plain `launch` event counts the same as a `relaunch` would have). `pm_attempts_counter` is PM's own, separately-tracked, non-monotonic counter, recorded for cross-referencing PM's own output — never the key.
- **`provenance`** is captured once, at an attempt's first grade, and never rewritten on a regrade — so a `policy.yaml`/`obligations.yaml` edit made between two attempts cannot silently make an earlier attempt look graded under different rules.
- **`pm_decision`** is read per attempt from `events.jsonl`, never from `run.json`'s one decision-per-*slice* field (which would flatten a steered first attempt and an accepted third attempt to the same value). `null` means undecided, never "nothing happened."
- **`run_status`** matches `pm.py`'s actual state machine: `run.json["status"]` has exactly four values, a slice's own `status` has exactly four. There is no distinct `attempt_budget_exhausted` state (it's `needs-human` + a `stop_reason` string) and no structured `infrastructure_failure` state in `pm_lib` at all — `infrastructure_failure_suspected` here is a heuristic this repo's own tooling would have to compute (not yet built), never a value read from PM.
- **No invented composite score** at the per-attempt level. Per-attempt data is raw and diagnostic; weighting into one number happens only in Tool 5, driven by `policy.yaml`.
- The number of `attempts` entries before `accepted_at_attempt` **is** the iteration-count metric. The sequence of `correctness`/`quality` values across the attempts that got graded **is** the trajectory — see §5 for which attempts that includes.

## 8. Known limitations and open questions

- **G1 — Review-quality scoring has no ground truth.** Resolved: a deterministic coverage proxy (Tools 2/3, above) plus PM's own comparative judgment (Tool 4), kept strictly separate, never blended.
- **G2 — PM's own acceptance judgment is unscored.** Accepted as a scope boundary: PM is presumably a strong frontier model, and this study is about the Developer seat. A future "which model makes the best PM" study would need different instrumentation.
- **G3 — Deterministic quality (lint/code-health) is an imperfect proxy for real code quality.** Accepted as the right starting point (see design principles); watch for cases where it obviously disagrees with a human reader's judgment.
- **G6/G7 — One-shot pre-filter screen. Dropped, not built.** A cheap pre-screen before committing a model to a full PM run was considered and rejected: a candidate model is only ever run through PM because the operator already cares about it, so the screen would never change that decision.
- **G9 — Grading-worktree discoverability by a live Developer session.** Not a live concern: grading strictly follows a run's end, so there is never a live Developer session left to discover a grading worktree, under any containment choice.
- **G12 — Containment/state-access backend.** `policy.yaml`'s `backend` key supports `local` (direct filesystem/subprocess) today; `sbx` (for an `ai-agent-sbx`-contained PM run) is reserved but not implemented — selecting it fails loudly rather than silently falling back.
- **G16 — Superseded-attempt grading (§5's scope limit). Resolved, via approach 1 (the git-log walk).** Every attempt of a slice now gets a deterministic grade (hidden tests/lint/code-health/scope) whenever `resolve_attempt_commits` recovers exactly one commit per attempt between the slice's own before_head and its final commit — no change to `project-manager`/`pm_lib` needed, and retroactive: it works on any already-recorded run, not just future ones. Validated against the real completed run on disk (`results/runs/20260911T112036Z-cd15fe/`: Slice 1's 5 attempts and Slice 2's 2 attempts both fully recovered, commit-for-commit, with correct per-attempt review harvesting) and against a synthetic stop/restart case built in a throwaway repo (a `finalize --stop` followed by a later plain `launch`, spanning two epochs, still recovers all 3 attempts intact).

  This relies on the Developer contract's one-commit-per-attempt convention, not a mechanical guarantee `pm_lib` enforces, so `resolve_attempt_commits` is a named refusal whenever it doesn't hold exactly (a merge commit in the range, a before_head that isn't an ancestor of the final commit, or a commit count that disagrees with the attempt count) — never a partial or guessed mapping. A subtlety the restart validation surfaced directly: the walk must start from the slice's *original* before_head (the previous slice's own recorded commit, when one exists), not from whatever `dev_check.resolve_before_head` would return for grading a single already-decided attempt — that function deliberately prefers the *most recent* epoch's before_head, which would silently truncate a multi-epoch slice's walk to only its last epoch. `_resolve_slice_before_head_for_walk` (`tools/grade_run.py`) makes this correct for any slice after the first, regardless of how many epochs it went through. A genuinely multi-epoch *first* slice still falls back to grading only its final attempt, with the refusal reported as a named problem, not a bug — regardless of whether an early (pre-restart) epoch's own review was ever recorded: `resolve_before_head`'s rule 4(b) can only ever select the review whose `head` matches the slice's *final accepted* commit, never an earlier epoch's, so there is no predecessor's commit to fall back on and no other structural source for the first slice's true earliest before_head.

  Approach 2 (extending `pm_lib` to persist each attempt's own commit/before_head directly) remains a fallback option if the git-log walk's convention-reliance ever proves too fragile in practice, but was not needed.

## 9. Reused vs. freshly written

| Component | Disposition |
|---|---|
| `relative-velocity`'s frozen `src/`/`tests/` substrate | Reused as-is — the frozen baseline pipeline, not eval infrastructure |
| `MERGER_RATE_PLAN-2SLICE.md` | Vendored copy, pinned commit (see its `.provenance.md`) |
| Task 001's original hidden tests | Reused as a content starting point (pinned fixtures/values), re-partitioned by slice and validated fresh against a reference solution of this plan |
| The `lint` and `code-health` skills | Invoked directly by Tool 1 on every attempt, never scraped from PM's own prose |
| `project-manager`'s own `.pm/runs/<run-id>/` and `<git-dir>/pm/<run-id>/` trail | The primary data source for every tool — harvested, never independently re-derived except where noted as a fallback |
| An LLM judge for readability/maintainability | Not built — see design principles and G3 |
| A one-shot pre-filter screen | Considered and dropped — see G6/G7 |

## Appendix: design history

Kept for context; not required reading to work on this repo. See `HANDOFF.md` for session-by-session detail and `git log` for the full trail.

This repo replaced two prior attempts at the same question: five one-shot tasks that tested a proxy (cheap one-shot quality predicts iteration-need) but never validated it against a real PM run, and a "Mode 1 + Mode 2" design that never reached a single real data point and, on inspection, measured nothing about iteration count or per-attempt trajectory — it scored a finished diff once, same as Mode 1. This branch (`pm-eval-v2`) started from an orphan root, carrying forward only the frozen plan, the pinned substrate, and the hidden-test content.

The grading design itself was rebuilt once, after real use. The original design had a driver (`tools/run_seat.py`) watch a PM run *live*, on the theory that a slice's base commit and a superseded attempt's own commit would become unrecoverable once PM moved past them. Running that driver against an already-completed real PM run exposed two bugs — an infinite loop in its terminal-status check, and a `before_head` that could never be resolved for either slice's final attempt — and the investigation into the second one showed the underlying theory was wrong: both facts are permanent and structurally recoverable from `run.json` alone, verified directly against `pm_lib` source, not merely reasoned about. The live-watching driver was retired and replaced by the single-pass `tools/grade_run.py` design in §5. Two independent reviews of that redesign then found (and fixes closed) a real data-loss bug in review harvesting — an earlier attempt's missing sheet row was silently discarding a *later*, gradeable attempt's own review data too — plus several narrower correctness edges in the structural `before_head` resolution. The one-shot pre-filter screen (G6/G7) was dropped in the same session, on the operator's direct judgment that it never changed which models got a full run.
