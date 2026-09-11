#!/usr/bin/env python3
"""The driver: watches one PM run and calls Tools 1-3 at the right checkpoints
(docs/MODE2-REWRITE-PLAN.md §7a).

**Never launches or manages the outer PM harness session.** The operator does
that themselves, interactively, with `project-manager`'s own unmodified
`SKILL.md` launcher prompt (§7a, resolved empirically against a real
classifier-block finding, not a simplification of convenience). This module's
only job is external: poll `events.jsonl`/`run.json` under a PM run directory
and, as the events this bench cares about appear, call `tools/dev_check.py`
(Tool 1) and `tools/review_score.py` (Tools 2/3) -- both of which are already
pure, one-shot, idempotent grading commands (their own module docstrings).
This driver adds no grading logic of its own; it only decides *when* to call
what already exists.

This module has been through three independent codex reviews (2026-09-11,
medium effort, each verified directly against `pm_lib` source, not this
repo's own comments). The first found four defects in the initial build; the
second, verifying that fix round, found the fix for one of those four was
incomplete in two further ways and the terminal-status fix was a heuristic
rather than an actual synchronization; the third, verifying that round,
found the terminal-status fix could still stall behind an unrelated later
event, pushed back on "grading failures are never retried" as too extreme,
and found a malformed-state edge case falling through to an unsafe default.
All three rounds' corrections are load-bearing:

- **Grading resolves an explicit commit, and groups by (slice, attempt), not
  slice alone.** `dev_check.py` has no way to check out anything but the
  Developer repo's current HEAD unless told otherwise -- and PM's own
  `finalize --accept` clears `current_slice` and appends `floor` and `accept`
  back-to-back in one command, so a driver polling normally (not just
  recovering from a backlog) routinely sees both in the same batch. If a
  batch contains grading events for more than one *attempt* of the same
  slice, only the latest attempt's events are dispatched -- an earlier
  attempt's own ending commit cannot be recovered from anything PM persists
  (a `floor` event records only its artifact directory, never a commit sha),
  so grading it would silently attribute the wrong commit's diff/tests/lint.
  Within the kept (latest) attempt's own events, every one is still
  dispatched, in file order: once a slice is recorded `accepted` in
  `run.json` (`pm_lib.slice_ops.finalize_accept` sets `entry["commit"]` at
  acceptance), that commit is passed explicitly (`--commit`), which remains
  correct no matter how much a *later* slice has since moved the repo's
  global HEAD -- this is what actually fixes grading a backlogged,
  already-accepted slice, which a per-slice "latest event" rule alone does
  not (HEAD is a repository-wide concept, not a per-slice one). A malformed
  state (a slice recorded `accepted` with no `commit` at all, which a
  well-formed `run.json` never produces) is a named, logged problem, never a
  silent fall-through to an unsafe HEAD default.
- **A residual, honest gap remains, and is not hidden**: if a slice's OWN
  first-ever grade attempt is dispatched only after its `accept`/`slice-stop`
  event has already cleared `current_slice` -- e.g. floor and accept landing
  in the very same poll for an attempt that was never separately graded by
  an earlier bare `finalize` check -- `dev_check.py`'s `resolve_before_head`
  has neither a live `current_slice` nor an existing sheet row to recover the
  diff base from, and grading fails loudly (a logged, named problem, not
  silent corruption). This is not limited to a driver that starts watching
  late: it also bites a driver that was watching promptly if that earlier
  bare-`finalize` grade was itself attempted and failed -- the one bounded
  retry (below) narrows this, since a retried success would still create the
  row in time, but does not eliminate it if the retry also fails. Not fixed
  further here -- doing so would mean either giving `dev_check.py` a way to
  accept an explicit `before_head` override or having this driver track and
  cache `before_head` itself the first time it observes a slice live, neither
  of which is a light-touch change worth making speculatively.
- **The terminal-status check confirms PM's own closing event, not merely a
  repeated status read -- and specifically the most recent *relevant*
  event, not simply the log's last line.** PM saves `run.json`'s terminal
  status (`complete`/`stopped`) *before* appending the event that reflects it
  (`finalize_accept`/`stop` both save state, then append their event) -- and
  that event is always the same, fixed kind for its status (`"complete"` for
  a run reaching `complete`; `"stop"` for the top-level `stop()` path that
  sets `status="stopped"`). An earlier fix required only the same status on
  two consecutive polls, which is a fixed delay, not real synchronization --
  it does not survive PM being slow, descheduled, or crashed for longer than
  one poll interval right after saving that state. This driver instead
  checks for that specific closing kind and keeps polling for however long
  it takes to appear -- but PM permits other event-producing commands with no
  terminal-status guard (e.g. `approve()`) to be appended *after* a run's own
  closing event, so a bare "is the log's last line the closing kind" check
  would then never confirm again. The check instead looks at the most recent
  event that is itself a run/slice-state transition this driver already
  tracks (`_RELEVANT_FOR_TERMINAL_CONFIRMATION`), skipping past anything else.
- **Review harvesting is re-attempted every poll over every known
  (slice, skill) target from the FULL event log, not triggered once per new
  `review` event.** `pm_lib.review.run_review` requires only the slice's
  current, advanced HEAD and a clean worktree -- nothing ties commissioning a
  review to a prior `finalize`/`floor` call, so a review can legitimately
  land before dev_check.py has ever created that attempt's row in the sheet.
  `review_score.upsert_sheet` refuses to write onto a missing row. Retrying
  every known target every poll (cheap: `run_review_score` is fully
  idempotent and re-derives its own canonical set from the log each time) is
  what lets a review that raced ahead of its own floor event succeed on a
  LATER poll, instead of being silently and permanently lost.
- **A failed grading dispatch gets exactly one bounded retry, on the NEXT
  poll -- not zero, and not an unconditional retry every poll like review
  harvesting.** Unlike a review-report re-parse, a grading dispatch runs the
  full hidden-test suite plus lint and code-health in a fresh worktree --
  genuinely expensive, not cheap -- so retrying it unconditionally forever
  would trade a data gap for continuous, unbounded work; but never retrying
  at all throws away exactly the purely transient failures (a worktree
  hiccup, a momentary git lock) this driver's own design already expects to
  happen. `_retry_pending_grades` tracks one pending retry per (slice,
  attempt) across polls, dropping it (as permanently superseded, logged) if
  a newer attempt appears before the retry runs, and giving up for good
  (also logged) if the retry itself fails again. Two ordering details make
  "on the next poll" actually true rather than aspirational, both caught by
  this driver's own final self-review rather than an external one:
  `watch_once` retries anything already pending *before* dispatching this
  poll's own new events, so a fresh failure is queued for the poll after
  next, never retried moments later in the very same call (which would
  give a transient condition no real time to clear); and `watch()` will not
  stop on a confirmed terminal status while a retry is still pending -- PM
  can append `floor`, `accept` and `complete` all before this driver ever
  polls, so a grading failure and a confirmed terminal status can coincide
  on the very first poll, and that queued retry still deserves its one
  chance to run before this driver gives up watching.
- **A `stop` event's "slice" field reflects whether a slice happened to be
  current at that moment, nothing else** (`pm_lib.slice_ops.stop`:
  `slice_id=current.get("id") if current else None`) -- an operator's
  top-level `pm stop` carries the same slice id as an attempt-budget
  exhaustion stop whenever a slice is active; there is no way, and no need,
  to tell the two apart from the event's shape. A further, accepted
  limitation here: top-level `stop()` performs no floor or clean-worktree
  check of its own, so it can fire while the Developer session has
  uncommitted work in progress -- grading it then measures whatever was last
  *committed* (possibly an earlier attempt's own ending state), attributed to
  the newer attempt number that never itself committed anything. This is not
  silent corruption -- the row's own `commit_sha` field still discloses
  exactly what was measured -- but it can look, at a glance, like an attempt
  "achieved" a result it never actually produced. Not fixed here: detecting
  "this attempt never committed anything of its own" would need its own
  small design (e.g. comparing `commit_sha` against the previous attempt's),
  not a hasty addition to this fix round.
- **`run.json["status"] == "stopped"` is this bench's *operating assumption*
  of finality, matching the documented operator workflow (`SKILL.md`: the
  operator does not resume a stopped run) -- it is not a guarantee
  `pm_lib` itself enforces.** `stop()` does not clear `current_slice`, and
  `start_slice()` has no guard against the run's own top-level status, so a
  `stopped` run *can* be reactivated via `start-slice` if an operator chooses
  to. This driver, having already exited on `stopped`, would need to be
  relaunched by the operator to pick back up in that case.

Dispatch rules for the events this driver acts on, all following from the
above:

- `floor`, `accept`, `slice-stop`, or a slice-scoped `stop` -- (re)grade that
  slice via Tool 1, but only for the batch's latest attempt per slice (see
  above); every other one is a named, logged, permanently skipped problem.
- `review` with recorded evidence -- not dispatched per-event at all; see
  `known_review_targets` and `watch_once`.
- Anything else (`launch`/`relaunch`/`steer`/`grant`/`observe`/`send`/
  `risk-raise`/`complete`) needs no action from this driver: launch-family
  events only open an attempt (Tool 1 note 2), and `complete` is reflected in
  `run.json["status"]`, which this driver's own loop already polls.

A grading or harvesting failure for one event is a named, logged problem --
never a reason to stop watching a run that may still be producing more
attempts (dev_check.py's own hidden-test/lint/health worktree failures, or a
transient filesystem error, are exactly the kind of thing a long unattended
run can hit once and not again -- `OSError` is caught alongside each tool's
own named exception type for this reason). A corrupt `events.jsonl` line is
the opposite: fatal immediately, via `bench_lib.read_events`'s own contract,
and is allowed to propagate and stop this driver outright.

**No persistent watermark across restarts.** This driver tracks which event
indices it has already dispatched only in memory, for the lifetime of one
`watch()` call. A restarted driver re-dispatches from event index 0 -- correct
for review harvesting (fully idempotent) and for the latest attempt of
whichever slice(s) still need grading, but NOT a full guarantee of complete
historical data (see the backlog-skip design point above).

**Known, deliberately deferred gap: `infrastructure_failure_suspected` is
never computed by this driver.** §6 assigns this heuristic to the driver
(PM persists no such state itself), but detecting it -- e.g. a dead Developer
tmux session with no terminal event ever following -- is a genuinely new
capability this build does not attempt, rather than a hasty, undertested
guess. `dev_check.py` only defaults the field to false on a first grade or
preserves whatever a prior grade recorded; nothing in this driver ever sets
it true. Recorded here as a named gap, not silently absent.

**Tools 4/5 do not exist yet.** Once the run reaches a confirmed terminal
`run.json` status (`complete` or `stopped` -- see above), this driver stops
watching and prints that Tool 4 (`model_report.py`) and Tool 5
(`leaderboard.py`) are future work, rather than calling scripts that are not
built (docs/MODE2-REWRITE-PLAN.md §10 step 9).
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable

import bench_lib
import dev_check
import review_score

# `needs-human` is deliberately excluded: it is a pause (attempt-budget
# exhaustion or a PM-initiated slice stop), not necessarily the run's end --
# the operator may resume with another `start-slice` (references/run-state.md's
# Attempts semantics). `complete` and `stopped` are treated as terminal --
# `stopped` is this bench's own operating assumption of finality, not a
# guarantee `pm_lib` enforces (see module docstring).
_TERMINAL_PM_STATUSES = frozenset({"complete", "stopped"})

# The specific events.jsonl event kind PM always appends immediately after
# saving each terminal status -- see _terminal_status_confirmed.
_CLOSING_EVENT_KIND_FOR_STATUS = {"complete": "complete", "stopped": "stop"}

# Event kinds that close out gradeable work for a slice (see module docstring).
# A "stop" event's own "slice" field simply reflects whether a slice was
# current at that moment -- true for both an operator's top-level `pm stop`
# and an attempt-budget-exhaustion stop alike (pm_lib.slice_ops.stop); there
# is no need to tell them apart here.
_SLICE_GRADE_KINDS = frozenset({"floor", "accept", "slice-stop", "stop"})

_SLICE_ID_RE = re.compile(r"^Slice (\d+)$")

# Exceptions caught at each dispatch boundary as "this one event's operation
# failed, log it and move on" -- each tool's own named exception type, plus
# OSError for a transient filesystem/subprocess failure that isn't itself a
# defect in dev_check.py/review_score.py (disk full, a permission blip, a
# git/pytest process that couldn't be spawned). Never widened to bare
# Exception: an unexpected exception type is a bug worth a loud crash, not a
# silently swallowed "problem".
_GRADE_EXCEPTIONS = (dev_check.DevCheckError, OSError)
_HARVEST_EXCEPTIONS = (review_score.ReviewScoreError, OSError)


class RunSeatError(bench_lib.BenchLibError):
    """Raised for every condition this driver must fail loudly on.

    main() catches exactly this exception type, prints it, and exits 1 --
    matching dev_check.py's and review_score.py's own __main__ pattern, so a
    bench_lib helper's failure surfaces under this tool's own name once
    re-raised (see bench_root()), never as an unfamiliar third type.
    """


def bench_root() -> Path:
    """Absolute path to this repo's root -- see bench_lib.repo_root()."""
    try:
        return bench_lib.repo_root()
    except bench_lib.BenchLibError as exc:
        raise RunSeatError(str(exc)) from exc


def load_policy(policy_path: Path) -> dict[str, Any]:
    """dev_check.py's own policy validation, plus this driver's own key.

    Reuses dev_check.load_policy for every key Tool 1's grading calls
    themselves need (backend, pm_scripts_dir, lint/health scripts,
    python_interpreter, subprocess_timeout_seconds) so a bad policy file
    fails loudly here, once, at driver startup -- not hours into an
    unattended watch, on whichever grading call happens to hit the missing
    key first.

    Raises:
        RunSeatError: dev_check.py's own validation failed, or
            driver_poll_interval_seconds is missing or not a positive number.
    """
    try:
        policy = dev_check.load_policy(policy_path)
    except dev_check.DevCheckError as exc:
        raise RunSeatError(str(exc)) from exc

    interval = policy.get("driver_poll_interval_seconds")
    if not isinstance(interval, (int, float)) or isinstance(interval, bool) or interval <= 0:
        raise RunSeatError(
            f"policy file {policy_path} must set driver_poll_interval_seconds to a positive number "
            f"(never a hardcoded fallback in this tool); got {interval!r}"
        )
    return policy


def parse_slice_number(slice_id: str) -> int | None:
    """"Slice 1" -> 1, or None if `slice_id` doesn't match that exact shape."""
    match = _SLICE_ID_RE.match(slice_id)
    return int(match.group(1)) if match else None


def review_skill_for_note(note: str) -> str | None:
    """Which of review_score.REVIEW_SKILLS a "review" event's note names, or
    None if it names neither (not a skill this bench harvests).

    Mirrors review_score.find_review_events's own note-prefix match
    ("<skill> via <tool>") rather than reimplementing it differently.
    """
    for skill in review_score.REVIEW_SKILLS:
        if note.startswith(f"{skill} via "):
            return skill
    return None


def _resolve_grading_commit(run_state: dict[str, Any], slice_id: str) -> tuple[str | None, str | None]:
    """The explicit commit to pass dev_check.py for this slice, or a named
    problem if none can be safely resolved.

    Returns:
        (commit, None): the slice is recorded `accepted` in run.json with its
            own commit (`pm_lib.slice_ops.finalize_accept` sets
            `entry["commit"]` at acceptance) -- this remains correct
            regardless of how much a *later* slice has since moved the
            repo's global HEAD, which a bare reliance on "current HEAD"
            cannot guarantee (finding 1's "repository-global, not per-slice,
            latest" defect).
        (None, None): dev_check.py should resolve its own default (current
            HEAD) -- safe when this slice is still run.json's live
            current_slice (nothing else could have moved HEAD), or when NO
            slice is currently live at all (a paused/stopped run with
            nothing else able to commit).
        (None, problem): neither holds -- e.g. a different slice is now
            current, and this one was stopped without ever being accepted;
            or (a malformed-state case, not expected from a well-formed
            run.json) this slice is recorded accepted but with no commit at
            all -- reported as a named problem rather than silently falling
            through to a HEAD default that could be entirely wrong.
    """
    for entry in run_state.get("slices", []) or []:
        if isinstance(entry, dict) and entry.get("id") == slice_id and entry.get("status") == "accepted":
            commit = entry.get("commit")
            if not commit:
                return None, (
                    f"slice {slice_id!r} is recorded accepted in run.json but has no recorded commit "
                    "(malformed state); this driver refuses to guess a commit for it"
                )
            return str(commit), None

    current_slice = run_state.get("current_slice") or {}
    current_id = current_slice.get("id")
    if current_id is None or current_id == slice_id:
        return None, None
    return None, (
        f"slice {slice_id!r} is neither accepted (with a recorded commit) nor run.json's current_slice "
        f"(currently {current_id!r}); this driver has no way to determine which commit to grade and is skipping it"
    )


def dispatch_grade(run_dir: Path, slice_number: int, attempt: int, policy_path: Path, commit: str | None = None) -> None:
    """Grade one specific attempt of one slice via Tool 1.

    `commit`, when given, is passed as an explicit `--commit` -- see
    _resolve_grading_commit for when and why this matters. None lets
    dev_check.py default to the Developer repo's current HEAD, which
    _resolve_grading_commit only ever permits when that is actually safe.

    Calls dev_check.main() directly (not a subprocess) -- it returns 0 or
    raises dev_check.DevCheckError, never sys.exit()s itself, so this driver
    can catch that exception type (plus OSError, see _GRADE_EXCEPTIONS)
    without a subprocess boundary.
    """
    argv = [
        "--run-dir",
        str(run_dir),
        "--slice",
        str(slice_number),
        "--attempt",
        str(attempt),
        "--policy",
        str(policy_path),
    ]
    if commit is not None:
        argv += ["--commit", commit]
    dev_check.main(argv)


def dispatch_review_harvest(run_dir: Path, slice_number: int, skill: str, root: Path) -> None:
    """Harvest one skill's canonical reviews for one slice via Tools 2/3.

    Calls review_score.run_review_score() directly, not review_score.main():
    main() parses sys.argv and calls sys.exit(1) on its own ReviewScoreError,
    which would kill this driver's whole watch loop over one bad review
    report. run_review_score() only raises, so this driver can catch it the
    same way dispatch_grade() catches dev_check.DevCheckError.

    Raises:
        review_score.ReviewScoreError: including when run.json has no
            'run_id' yet -- deliberately this type, not RunSeatError, so
            every caller of this function can catch one exception type
            (plus OSError, see _HARVEST_EXCEPTIONS) for every way this call
            can fail.
    """
    run_state = review_score.read_json(run_dir / "run.json")
    run_id = run_state.get("run_id")
    if not run_id:
        raise review_score.ReviewScoreError(f"run.json at {run_dir} has no 'run_id'")
    sheet_path = review_score.default_sheet_path(root, run_id, slice_number)
    review_score.run_review_score(run_dir, slice_number, skill, sheet_path)


def _resolve_batch_grading_targets(
    events: list[dict[str, Any]], start_index: int, log: Callable[[str], None]
) -> tuple[list[tuple[int, dict[str, Any], int, int]], list[str]]:
    """For events[start_index:], resolve (index, event, slice_number,
    attempt) for every `_SLICE_GRADE_KINDS` event whose slice id parses and
    whose attempt number resolves -- grouped by slice, keeping only the
    events that belong to that slice's LATEST attempt in this batch.

    An earlier, now-superseded attempt's own events are a named, logged,
    permanently skipped problem instead: its ending commit cannot be
    recovered once a newer attempt exists for the same slice (a `floor`
    event records only its artifact directory, never a commit sha).

    Returns:
        (targets, problems) -- targets holds only the safe-to-dispatch
        entries, in file order (so e.g. a `floor` event is attempted before
        the `accept`/`slice-stop` that immediately follows it for the same
        attempt, giving dev_check.py's live-`current_slice` before_head
        route its best chance before falling back to an existing sheet row).
    """
    problems: list[str] = []
    resolved: list[tuple[int, dict[str, Any], str, int, int]] = []

    for index, event in enumerate(events[start_index:], start=start_index):
        kind = event.get("kind")
        slice_id = event.get("slice")
        if kind not in _SLICE_GRADE_KINDS or not slice_id:
            continue

        slice_number = parse_slice_number(slice_id)
        if slice_number is None:
            problems.append(f"event kind={kind!r} has unrecognised slice id {slice_id!r}; skipped")
            log(f"run_seat.py: warning: {problems[-1]}")
            continue

        try:
            attempt = bench_lib.attempt_ordinal(events, slice_id, before_index=index)
        except bench_lib.BenchLibError as exc:
            problems.append(
                f"could not resolve the attempt number for slice {slice_number} at event index {index} "
                f"(kind={kind!r}): {exc}"
            )
            log(f"run_seat.py: warning: {problems[-1]}")
            continue

        resolved.append((index, event, slice_id, slice_number, attempt))

    latest_attempt_per_slice: dict[str, int] = {}
    for _, _, slice_id, _, attempt in resolved:
        latest_attempt_per_slice[slice_id] = max(attempt, latest_attempt_per_slice.get(slice_id, attempt))

    targets: list[tuple[int, dict[str, Any], int, int]] = []
    for index, event, slice_id, slice_number, attempt in resolved:
        latest = latest_attempt_per_slice[slice_id]
        if attempt != latest:
            problems.append(
                f"slice {slice_number}: attempt {attempt}'s event at index {index} (kind={event.get('kind')!r}) is "
                f"superseded by attempt {latest} in this same poll -- dev_check.py can only check out the repo's "
                "current HEAD, never a superseded attempt's historical commit; grade it manually with an explicit "
                "--commit if the data matters"
            )
            log(f"run_seat.py: warning: {problems[-1]}")
            continue
        targets.append((index, event, slice_number, attempt))

    return targets, problems


def process_new_events(
    events: list[dict[str, Any]],
    start_index: int,
    run_dir: Path,
    run_state: dict[str, Any],
    policy_path: Path,
    pending_retries: dict[tuple[str, int], None],
    log: Callable[[str], None],
) -> list[str]:
    """Dispatch every safely-gradeable event from `start_index` onward --
    see `_resolve_batch_grading_targets` for which events those are, and
    `_resolve_grading_commit` for the explicit `--commit` each dispatch is
    given.

    Never raises for a single event's own grading failure -- each is caught,
    logged via `log`, and recorded in the returned list. A failure also
    queues one bounded retry for the next poll, in `pending_retries` (see
    `_retry_pending_grades`) -- a success removes any stale entry for the
    same (slice, attempt), though normally there would be at most one to
    remove. Review harvesting is not triggered here at all -- see
    `watch_once`, which re-attempts it every poll over the full set of known
    (slice, skill) targets, not just newly-seen events.

    Returns:
        Every problem encountered, as human-readable strings (empty if none).
    """
    targets, problems = _resolve_batch_grading_targets(events, start_index, log)

    for _, event, slice_number, attempt in targets:
        kind = event.get("kind")
        slice_id = event.get("slice")
        commit, commit_problem = _resolve_grading_commit(run_state, slice_id)
        if commit_problem is not None:
            problems.append(f"slice {slice_number} attempt {attempt}: {commit_problem}")
            log(f"run_seat.py: warning: {problems[-1]}")
            continue

        log(f"run_seat.py: grading slice {slice_number} attempt {attempt} (event kind={kind!r})")
        try:
            dispatch_grade(run_dir, slice_number, attempt, policy_path, commit)
            pending_retries.pop((slice_id, attempt), None)
        except _GRADE_EXCEPTIONS as exc:
            problems.append(
                f"dev_check.py failed grading slice {slice_number} attempt {attempt} on {kind!r} event: {exc} "
                "(will retry once on the next poll)"
            )
            log(f"run_seat.py: warning: {problems[-1]}")
            pending_retries[(slice_id, attempt)] = None

    return problems


def _retry_pending_grades(
    pending_retries: dict[tuple[str, int], None],
    events: list[dict[str, Any]],
    run_dir: Path,
    run_state: dict[str, Any],
    policy_path: Path,
    log: Callable[[str], None],
) -> list[str]:
    """Retry each (slice_id, attempt) pair in `pending_retries` exactly once
    more -- a single bounded retry for a grading dispatch that failed once
    already, covering a purely transient failure (a worktree hiccup, a
    momentary git lock) without unconditionally re-running dev_check.py's
    genuinely expensive work (a full hidden-test suite plus lint and
    code-health) forever the way review harvesting's cheap full-rescan retry
    can (see known_review_targets' docstring for that contrast).

    Every entry is removed from `pending_retries` by the time this returns --
    whether it succeeds, fails again (and this driver gives up on it), or is
    abandoned because a newer attempt has since superseded it -- so there is
    only ever one retry per failure, never an unbounded loop.
    """
    problems: list[str] = []
    for slice_id, attempt in list(pending_retries):
        del pending_retries[(slice_id, attempt)]
        slice_number = parse_slice_number(slice_id)
        if slice_number is None:
            continue

        try:
            latest = bench_lib.attempt_ordinal(events, slice_id)
        except bench_lib.BenchLibError:
            continue

        if attempt != latest:
            problems.append(
                f"slice {slice_number} attempt {attempt}: abandoning its one retry -- a newer attempt "
                f"({latest}) now exists for this slice, so its historical commit can no longer be recovered"
            )
            log(f"run_seat.py: warning: {problems[-1]}")
            continue

        commit, commit_problem = _resolve_grading_commit(run_state, slice_id)
        if commit_problem is not None:
            problems.append(f"slice {slice_number} attempt {attempt}: retry abandoned -- {commit_problem}")
            log(f"run_seat.py: warning: {problems[-1]}")
            continue

        log(f"run_seat.py: retrying grade for slice {slice_number} attempt {attempt} (one bounded retry)")
        try:
            dispatch_grade(run_dir, slice_number, attempt, policy_path, commit)
        except _GRADE_EXCEPTIONS as exc:
            problems.append(
                f"dev_check.py failed grading slice {slice_number} attempt {attempt} again on retry; giving up: {exc}"
            )
            log(f"run_seat.py: warning: {problems[-1]}")

    return problems


def known_review_targets(events: list[dict[str, Any]]) -> set[tuple[int, str]]:
    """Every (slice_number, skill) pair with at least one successful `review`
    event (recorded evidence) anywhere in the FULL event log -- not just
    newly-seen events.

    Recomputed from the whole log and re-attempted every poll (see
    watch_once), not triggered by a single new `review` event: PM's review
    command has no precondition tying it to a prior `finalize`/`floor` call
    (`pm_lib.review.run_review` only requires the slice's current, advanced
    HEAD and a clean worktree), so a review event for an attempt can
    legitimately arrive before that attempt's own scoring-sheet row exists yet
    (dev_check.py creates that row; `review_score.upsert_sheet` refuses to
    write onto a missing one). Retrying every known target every poll --
    cheap, since `run_review_score()` is fully idempotent and re-derives its
    own canonical set from the log each time -- is what lets a review that
    raced ahead of its own floor event get picked up on a LATER poll once
    that row exists, instead of being silently and permanently lost because
    its own triggering event was seen too early and never revisited.
    """
    targets: set[tuple[int, str]] = set()
    for event in events:
        if event.get("kind") != "review" or not event.get("evidence"):
            continue
        slice_number = parse_slice_number(str(event.get("slice", "")))
        skill = review_skill_for_note(str(event.get("note", "")))
        if slice_number is not None and skill is not None:
            targets.add((slice_number, skill))
    return targets


def read_events(run_dir: Path) -> list[dict[str, Any]]:
    """Read events.jsonl -- see bench_lib.read_events() for the missing-file
    contract (empty list, an unwatched run has nothing to dispatch yet); an
    invalid JSON line is a corrupt log and is re-raised as RunSeatError, fatal
    to this driver rather than caught per-event like a grading failure."""
    try:
        return bench_lib.read_events(run_dir)
    except bench_lib.BenchLibError as exc:
        raise RunSeatError(str(exc)) from exc


# Event kinds this driver treats as meaningful run/slice-state transitions
# for terminal-status confirmation -- see _terminal_status_confirmed. Not
# every events.jsonl kind belongs here: `approve`, `grant`, `observe`,
# `send`, `risk-raise` and the like can legitimately be appended after a
# run's own closing event (nothing in pm_lib ties them to run completion)
# without representing a NEW state transition this driver cares about.
_RELEVANT_FOR_TERMINAL_CONFIRMATION = _SLICE_GRADE_KINDS | {"complete"}


def _terminal_status_confirmed(events: list[dict[str, Any]], status: str | None) -> bool:
    """Whether the most recent event.jsonl entry that is actually a
    run/slice-state transition (see `_RELEVANT_FOR_TERMINAL_CONFIRMATION`)
    is the specific kind PM always appends immediately after saving this
    terminal status.

    `pm_lib.slice_ops`: a run reaching `complete` always ends with a
    `"complete"`-kind event; the top-level `stop()` path that sets
    `status="stopped"` always ends with a `"stop"`-kind event. Checking the
    actual closing event, rather than merely observing the same status on
    two consecutive polls, is what survives PM saving that status and then
    being slow, descheduled, or crashed for an ARBITRARY delay before
    appending the event that reflects it -- not just one extra poll interval.

    Looking at the most recent *relevant* event, not simply `events[-1]`,
    matters because PM permits other event-producing commands with no
    terminal-status guard (e.g. `approve()`) to be called after a run has
    already reached `complete`/`stopped` -- a bare "last event" check would
    then never confirm again, and this driver would poll forever despite the
    real closing event already being on record.
    """
    expected_kind = _CLOSING_EVENT_KIND_FOR_STATUS.get(status or "")
    if not expected_kind:
        return False
    for event in reversed(events):
        if event.get("kind") in _RELEVANT_FOR_TERMINAL_CONFIRMATION:
            return event.get("kind") == expected_kind
    return False


def watch_once(
    run_dir: Path,
    root: Path,
    policy_path: Path,
    seen_index: int,
    pending_retries: dict[tuple[str, int], None],
    log: Callable[[str], None],
) -> tuple[int, list[str], str | None, bool]:
    """One poll iteration: retry anything queued in `pending_retries` from an
    EARLIER poll's failure first (see `_retry_pending_grades`), THEN dispatch
    any new gradeable events beyond `seen_index` -- in that order, so a
    failure from THIS poll's own new events is queued for the NEXT poll, not
    retried moments later in this same call (which would defeat the point of
    a retry: giving a transient condition a full poll interval to clear, not
    a back-to-back re-attempt). Also re-attempts every known review-harvest
    target regardless of whether anything is new (see known_review_targets),
    then reads run.json once (missing entirely only before `init` completes
    -- read as an empty mapping, so `status` is None, not an error, and the
    caller keeps waiting).

    Returns:
        (new seen_index, problems from this iteration's dispatches, pm_status
        or None, whether that status's own closing event has already
        appeared in events.jsonl -- see _terminal_status_confirmed).
    """
    events = read_events(run_dir)
    run_json_path = run_dir / "run.json"
    run_state = review_score.read_json(run_json_path) if run_json_path.is_file() else {}
    status = run_state.get("status")

    problems: list[str] = _retry_pending_grades(pending_retries, events, run_dir, run_state, policy_path, log)

    if len(events) > seen_index:
        problems += process_new_events(events, seen_index, run_dir, run_state, policy_path, pending_retries, log)
        seen_index = len(events)

    for slice_number, skill in sorted(known_review_targets(events)):
        try:
            dispatch_review_harvest(run_dir, slice_number, skill, root)
        except _HARVEST_EXCEPTIONS as exc:
            problem = f"review_score.py failed harvesting {skill} for slice {slice_number}: {exc}"
            problems.append(problem)
            log(f"run_seat.py: warning: {problem}")

    confirmed = _terminal_status_confirmed(events, status)
    return seen_index, problems, status, confirmed


def watch(
    run_dir: Path,
    root: Path,
    policy_path: Path,
    poll_interval_seconds: float,
    *,
    log: Callable[[str], None] = print,
    sleep: Callable[[float], None] = time.sleep,
) -> int:
    """Poll `run_dir` until the PM run reaches a terminal status (`complete`
    or `stopped` -- `needs-human` is a pause, not necessarily an end, see
    `_TERMINAL_PM_STATUSES`) AND its own closing event has actually appeared
    in `events.jsonl` (see `_terminal_status_confirmed` for why a status read
    alone is not trusted), dispatching Tools 1-3 at every event this bench
    cares about along the way.

    Returns:
        0 if every dispatch this call made succeeded, 1 if any failed (the
        run itself may still be fully graded up to the point of failure --
        this is a summary exit code, not a claim that nothing was recorded).
    """
    seen_index = 0
    all_problems: list[str] = []
    pending_retries: dict[tuple[str, int], None] = {}
    warned_unconfirmed = False
    while True:
        seen_index, problems, status, confirmed = watch_once(
            run_dir, root, policy_path, seen_index, pending_retries, log
        )
        all_problems.extend(problems)

        if status in _TERMINAL_PM_STATUSES:
            if confirmed and not pending_retries:
                log(f"run_seat.py: run reached terminal status {status!r}; stopping watch")
                log(
                    "run_seat.py: Tool 4 (model_report.py) and Tool 5 (leaderboard.py) are not yet built "
                    "(docs/MODE2-REWRITE-PLAN.md §10 step 9) -- run them manually once they exist"
                )
                break
            if confirmed and pending_retries:
                # A grading failure from this very poll queued a retry --
                # give it the one more poll it's owed (see watch_once's
                # ordering note) before this driver is allowed to stop,
                # even though the run itself is already done.
                log(
                    f"run_seat.py: run reached terminal status {status!r}, but "
                    f"{len(pending_retries)} grading retry(ies) are still pending; giving them one more poll"
                )
            elif not warned_unconfirmed:
                log(
                    f"run_seat.py: run.json reports status={status!r} but its closing event has not appeared in "
                    "events.jsonl yet; continuing to poll until it does"
                )
                warned_unconfirmed = True
        else:
            warned_unconfirmed = False

        sleep(poll_interval_seconds)

    if all_problems:
        log(f"run_seat.py: {len(all_problems)} grading/harvest problem(s) occurred during this watch:")
        for problem in all_problems:
            log(f"  - {problem}")
        return 1
    return 0


# --- CLI ---------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Watch one PM run and grade every attempt as it becomes gradeable, purely externally -- "
            "never launches PM itself (docs/MODE2-REWRITE-PLAN.md §7a)."
        )
    )
    parser.add_argument("--run-dir", required=True, type=Path, help="PM run state directory containing run.json and events.jsonl")
    parser.add_argument("--policy", type=Path, default=None, help="defaults to policy.yaml at this repo's root")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = bench_root()
    policy_path = (args.policy or (root / "policy.yaml")).expanduser().resolve()
    policy = load_policy(policy_path)

    run_dir = args.run_dir.expanduser().resolve()
    if not (run_dir / "run.json").is_file() and not (run_dir / "events.jsonl").is_file():
        raise RunSeatError(f"--run-dir {run_dir} has neither run.json nor events.jsonl; is this a real PM run directory?")

    return watch(run_dir, root, policy_path, policy["driver_poll_interval_seconds"])


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RunSeatError as exc:
        print(f"run_seat.py: error: {exc}", file=sys.stderr)
        sys.exit(1)
