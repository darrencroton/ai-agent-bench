#!/usr/bin/env python3
"""Grades one FINISHED PM run in a single pass (docs/MODE2-REWRITE-PLAN.md §5).

**Replaces `tools/run_seat.py` (retired 2026-09-11).** That module watched a
PM run live -- polling `events.jsonl`/`run.json`, batching events per poll,
retrying a failed grade once on the next poll, and confirming a terminal
status by checking whether the most recent tracked event matched PM's own
closing-event kind. All of that existed to serve one assumption: that a
slice's `before_head` (the diff base every grade is measured against) and a
superseded attempt's own ending commit evaporate once PM moves on, so
grading had to happen while the data was still "live."

**That assumption was never actually verified against `pm_lib` source until
this session, and it is false for the data this bench actually needs:**

- A slice's `before_head` is set exactly once, at `start_slice`, and is
  preserved unchanged across every relaunch/steer within that slice
  (`pm_lib/prompts.py`: "The slice's before_head is correct on every
  attempt" -- verified directly against `pm_lib/slice_ops.py`'s
  `start_slice`, not inferred). It is a permanent, structural fact.
- Mode B processes slices strictly in plan order and gates progression on
  acceptance (`current_slice` is a single field; nothing in `pm_lib` allows
  two slices in flight), so at most one slice in a finished run can be
  non-accepted, and only if it is the LAST slice PM ever touched -- every
  earlier slice's ending commit is necessarily recorded in `run.json`
  (`entry["commit"]`, set by `finalize_accept`).
- `dev_check.resolve_before_head` now derives `before_head` structurally
  from `run.json["slices"]` and, when available, any review's recorded
  `before_head` (a per-slice constant PM writes onto every commissioned
  review) -- see that function's own docstring for the full four-path
  resolution order. This closes the exact gap that broke grading a real,
  already-finished run the first time this bench tried it (2026-09-11):
  neither of Slice 1's or Slice 2's final attempts could be graded because
  `resolve_before_head` only ever checked a live pointer or a previously
  cached sheet row -- an implementation gap, not missing data.

**What this means for this module:** grading a slice's FINAL attempt -- the
one whose iteration count and pm_decision *is* the trajectory this bench
exists to measure (docs/MODE2-REWRITE-PLAN.md §7) -- needs no live watching
at all. A single pass over a finished run's `events.jsonl`/`run.json`
recovers it completely. This module refuses to run against anything but a
confirmed-terminal run (see `_terminal_status_confirmed`) rather than trying
to grade a run still in progress.

**What is deliberately still out of scope, same as before:** a *superseded*
(steered-away) attempt's own intermediate commit is not named anywhere in
`run.json`'s structure. It is often still recoverable in practice --
`run.json["slices"][i]["reviews"][*]["head"]` pins it whenever a review was
commissioned on that exact attempt, and git itself never discards the
commit -- but nothing guarantees a review on every steer for a slice PM
judged standard risk (only elevated-risk slices mandate one). Recovering
that trajectory fully is a real, bounded future enhancement (walk the linear
commit chain between two structurally-known before_head/commit endpoints,
correlating with `reviews[].head` where present), deliberately not built
here: per-attempt review findings and the per-attempt `pm_decision`
(steer/accept/stop) are already fully recoverable regardless, from the
permanent event log and `run.json["slices"][i]["reviews"]`, which covers
most of "what it took to get there" without needing to re-run pytest/lint/
health against every intermediate commit.

**Design consequence: no watch loop, no polling, no retries.** A stateless,
single-pass script has no "next poll" for a retry to wait for and no
batching-across-time question to get wrong -- the entire class of bug that
took three independent review rounds to shake out of the retired
`run_seat.py`, and still left two more (a genuine infinite loop on a normal
trailing top-level `stop` after `complete`; the before_head gap above) that
only a real completed run ever exposed. If grading fails here, it fails
loudly once and this module exits nonzero; re-running it is always safe
(dev_check.py/review_score.py are both idempotent upserts).

Everything this module does is read-only with respect to PM's own state and
never launches or manages the PM harness session -- the operator runs PM
exactly as they always have, and separately, whenever they judge the run
finished, invokes this module themselves (or points a later PM/agent session
at it) to grade it. Nothing about invoking this module is baked into PM's
own launcher prompt.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import bench_lib
import dev_check
import review_score

# `needs-human` is deliberately excluded: it is a pause (attempt-budget
# exhaustion or a PM-initiated slice stop), not necessarily the run's end --
# the operator may resume with another `start-slice`. `complete` and
# `stopped` are the only two this module treats as finished; `stopped` is
# this bench's own operating assumption of finality, not a guarantee
# `pm_lib` enforces (`stop()` doesn't clear `current_slice` and
# `start_slice()` has no guard against a stopped run being reactivated).
_TERMINAL_PM_STATUSES = frozenset({"complete", "stopped"})

# The specific events.jsonl event kind PM always appends immediately after
# saving each terminal status -- see _terminal_status_confirmed.
_CLOSING_EVENT_KIND_FOR_STATUS = {"complete": "complete", "stopped": "stop"}

_SLICE_ID_RE = re.compile(r"^Slice (\d+)$")


class GradeRunError(bench_lib.BenchLibError):
    """Raised for every condition this module must fail loudly on.

    main() catches exactly this exception type, prints it, and exits 1 --
    matching dev_check.py's and review_score.py's own __main__ pattern.
    """


def bench_root() -> Path:
    """Absolute path to this repo's root -- see bench_lib.repo_root()."""
    try:
        return bench_lib.repo_root()
    except bench_lib.BenchLibError as exc:
        raise GradeRunError(str(exc)) from exc


def load_policy(policy_path: Path) -> dict[str, Any]:
    """dev_check.py's own policy validation -- this module needs no key of
    its own (unlike the retired driver's `driver_poll_interval_seconds`,
    which existed only to pace a poll loop this module no longer has)."""
    try:
        return dev_check.load_policy(policy_path)
    except dev_check.DevCheckError as exc:
        raise GradeRunError(str(exc)) from exc


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


def read_events(run_dir: Path) -> list[dict[str, Any]]:
    """Read events.jsonl -- see bench_lib.read_events() for the missing-file
    contract. A corrupt line is fatal immediately, per that contract."""
    try:
        return bench_lib.read_events(run_dir)
    except bench_lib.BenchLibError as exc:
        raise GradeRunError(str(exc)) from exc


def _terminal_status_confirmed(events: list[dict[str, Any]], status: str | None) -> bool:
    """Whether PM's own closing event for `status` has appeared anywhere in
    the log -- checked by existence, not by being the MOST RECENT tracked
    event.

    The retired `run_seat.py` used a stricter "most recent relevant event"
    check, reasoned to survive a trailing *irrelevant* event (e.g.
    `approve()`, which PM permits after a run is already done). It did not
    survive a trailing top-level `stop` issued after a run had already
    reached `complete` -- ordinary, unremarkable operator/PM behavior, not
    an edge case -- because `stop` was itself one of the tracked kinds:
    that trailing `stop` became the "most recent relevant event" and
    permanently masked the earlier, real `complete` event, so the driver
    polled forever. Confirmed against a real run, 2026-09-11, not merely
    reasoned about.

    Existence anywhere in the log is sufficient and correct for `complete`,
    which can only ever be written once for a run's whole lifetime. It is
    very slightly weaker for `stopped`, which `stop()` can in principle be
    called more than once for (a run stopped, reactivated, then stopped
    again): an EARLIER `stop` event could satisfy this check during the
    narrow window where a second `stop()` call has already saved
    `status="stopped"` but not yet appended its own fresh `stop` event
    (`pm_lib` saves state before appending the matching event, the same
    ordering that motivates this whole check). This window is a handful of
    statements wide inside one synchronous function call, not a real span
    of time an operator manually invoking this tool once "the run looks
    done" is likely to land in -- and unlike the retired live-watching
    driver, this module is always safe to simply re-run if in doubt
    (`dev_check.py`/`review_score.py` are both idempotent upserts).
    """
    expected_kind = _CLOSING_EVENT_KIND_FOR_STATUS.get(status or "")
    if not expected_kind:
        return False
    return any(event.get("kind") == expected_kind for event in events)


def _resolve_grading_commit(run_state: dict[str, Any], slice_id: str) -> tuple[str | None, str | None]:
    """The explicit commit to pass dev_check.py for this slice's final
    attempt, or a named problem if none can be safely resolved.

    **Only an accepted slice's commit is ever safe to resolve automatically
    (corrected 2026-09-11, a real defect an independent review caught).**
    An earlier version of this function fell through to `(None, None)` --
    "let dev_check.py default to the repo's current HEAD" -- for any
    non-accepted slice, reasoning that a finished run's `current_slice` is
    always cleared, so nothing could have moved HEAD since. That reasoning
    is wrong: a top-level `pm stop` (`pm_lib.slice_ops.stop()`) can end an
    in-progress attempt with NO floor check, NO clean-worktree requirement,
    and NO commit recorded anywhere -- the Developer's uncommitted work is
    simply abandoned, so current HEAD may belong to a *previous* attempt,
    not the stopped one. Worse, `start_slice()` has no guard against a
    `stopped` run being reactivated, so "HEAD hasn't moved since" is not
    even a durable property of the moment grading actually runs. There is
    no other structurally reliable source for a stopped, non-accepted
    slice's ending commit (a commissioned review's `head` pins a specific
    moment, but not necessarily the attempt's true final state, since more
    could have been committed after that review ran) -- so this function
    now refuses, by design, rather than guess. Grade a stopped, non-accepted
    slice by hand with `dev_check.py --commit <sha>` once the operator has
    independently confirmed which commit is the right one.

    Returns:
        (commit, None): the slice is recorded `accepted` in run.json with
            its own commit (`pm_lib.slice_ops.finalize_accept` sets
            `entry["commit"]` at acceptance) -- correct regardless of how
            far a *later* slice has since moved the repo's global HEAD,
            which a bare "current HEAD" default cannot guarantee.
        (None, problem): the slice is not recorded accepted (never reached,
            or stopped without acceptance -- reported by name, so it's
            clear the case is refused, not silently skipped as gradeable
            with nothing to grade), or is recorded accepted with no
            commit at all (a malformed state).
    """
    for entry in run_state.get("slices", []) or []:
        if isinstance(entry, dict) and entry.get("id") == slice_id:
            if entry.get("status") != "accepted":
                return None, (
                    f"slice {slice_id!r} is not recorded accepted (status={entry.get('status')!r}); its final "
                    "attempt's ending commit cannot be safely resolved automatically -- grade it by hand with "
                    "dev_check.py --commit <sha> once you've independently confirmed the right commit"
                )
            commit = entry.get("commit")
            if not commit:
                return None, (
                    f"slice {slice_id!r} is recorded accepted in run.json but has no recorded commit "
                    "(malformed state); this tool refuses to guess a commit for it"
                )
            return str(commit), None
    return None, f"slice {slice_id!r} not found in run.json's 'slices' list"


def dispatch_grade(run_dir: Path, slice_number: int, attempt: int, policy_path: Path, commit: str | None = None) -> None:
    """Grade one specific attempt of one slice via Tool 1.

    Calls dev_check.main() directly (not a subprocess) -- it returns 0 or
    raises dev_check.DevCheckError, never sys.exit()s itself.
    """
    argv = [
        "--run-dir", str(run_dir),
        "--slice", str(slice_number),
        "--attempt", str(attempt),
        "--policy", str(policy_path),
    ]
    if commit is not None:
        argv += ["--commit", commit]
    dev_check.main(argv)


def dispatch_review_harvest(run_dir: Path, slice_number: int, skill: str, root: Path) -> list[str]:
    """Harvest one skill's canonical reviews for one slice via Tools 2/3.

    Calls review_score.run_review_score() directly, not review_score.main():
    main() parses sys.argv and calls sys.exit() on its own error, which
    would kill this module's whole grading pass over one bad review report.

    Returns:
        Per-attempt problems `run_review_score` itself recovered from
        (missing sheet rows -- an expected shape under this module's
        final-attempt-only grading, not a fatal error); empty if every
        canonical review for this (slice, skill) harvested cleanly.
    """
    run_state = review_score.read_json(run_dir / "run.json")
    run_id = run_state.get("run_id")
    if not run_id:
        raise review_score.ReviewScoreError(f"run.json at {run_dir} has no 'run_id'")
    sheet_path = review_score.default_sheet_path(root, run_id, slice_number)
    return review_score.run_review_score(run_dir, slice_number, skill, sheet_path)


def known_review_targets(events: list[dict[str, Any]]) -> set[tuple[int, str]]:
    """Every (slice_number, skill) pair with at least one successful `review`
    event (recorded evidence) anywhere in the log.

    `run_review_score()` is fully idempotent and re-derives its own
    canonical (latest per skill) review from the log each time, so
    re-harvesting every known target on every run of this module is cheap
    and always safe -- there is no "already harvested" state to track.
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


def gradeable_slice_targets(run_state: dict[str, Any], events: list[dict[str, Any]]) -> list[tuple[int, str, int]]:
    """For every slice PM ever launched at least once, resolve
    (slice_number, slice_id, attempt) for its FINAL attempt -- the only one
    a finished run's structural facts can recover a diff base and ending
    commit for (see dev_check.resolve_before_head and
    _resolve_grading_commit).

    A slice with zero launch-family events (never reached before the run
    ended) is silently skipped, not an error -- a normal, expected shape
    for a run that stopped early.
    """
    targets: list[tuple[int, str, int]] = []
    for entry in run_state.get("slices", []) or []:
        slice_id = entry.get("id")
        slice_number = parse_slice_number(str(slice_id))
        if slice_number is None:
            continue
        try:
            attempt = bench_lib.attempt_ordinal(events, slice_id)
        except bench_lib.BenchLibError:
            continue
        targets.append((slice_number, slice_id, attempt))
    return targets


def grade_finished_run(
    run_dir: Path, root: Path, policy_path: Path, run_state: dict[str, Any], events: list[dict[str, Any]]
) -> list[str]:
    """Grade every gradeable slice's final attempt, then harvest every known
    review target. Never raises for a single slice/review's own failure --
    each is caught and returned as a human-readable problem string.

    `run_state`/`events` are passed in, already read and validated by
    `main()`, rather than re-read here -- avoids a second, redundant parse
    of the same files and a second place a malformed run.json could raise
    uncaught past this function's own documented "never raises" contract.

    Returns:
        Every problem encountered (empty if none). Grading runs before
        review harvesting because `review_score.upsert_sheet` refuses to
        write onto a scoring-sheet row that doesn't exist yet -- dev_check.py
        is what creates it.
    """
    problems: list[str] = []

    for slice_number, slice_id, attempt in gradeable_slice_targets(run_state, events):
        commit, commit_problem = _resolve_grading_commit(run_state, slice_id)
        if commit_problem is not None:
            problems.append(f"slice {slice_number} attempt {attempt}: {commit_problem}")
            print(f"grade_run.py: warning: {problems[-1]}", file=sys.stderr)
            continue
        print(f"grade_run.py: grading slice {slice_number} attempt {attempt} (its final attempt)")
        try:
            dispatch_grade(run_dir, slice_number, attempt, policy_path, commit)
        except (dev_check.DevCheckError, OSError) as exc:
            problems.append(f"dev_check.py failed grading slice {slice_number} attempt {attempt}: {exc}")
            print(f"grade_run.py: warning: {problems[-1]}", file=sys.stderr)

    for slice_number, skill in sorted(known_review_targets(events)):
        try:
            harvest_problems = dispatch_review_harvest(run_dir, slice_number, skill, root)
        except (review_score.ReviewScoreError, OSError) as exc:
            problems.append(f"review_score.py failed harvesting {skill} for slice {slice_number}: {exc}")
            print(f"grade_run.py: warning: {problems[-1]}", file=sys.stderr)
            continue
        for harvest_problem in harvest_problems:
            problems.append(harvest_problem)
            print(f"grade_run.py: warning: {harvest_problem}", file=sys.stderr)

    return problems


# --- CLI ---------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Grade one FINISHED PM run in a single pass: every slice's final attempt, plus every "
            "commissioned review (docs/MODE2-REWRITE-PLAN.md §5). Refuses to run against a run still "
            "in progress."
        )
    )
    parser.add_argument("--run-dir", required=True, type=Path, help="PM run state directory containing run.json and events.jsonl")
    parser.add_argument("--policy", type=Path, default=None, help="defaults to policy.yaml at this repo's root")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = bench_root()
    policy_path = (args.policy or (root / "policy.yaml")).expanduser().resolve()
    load_policy(policy_path)  # validated once, up front, before any grading work

    run_dir = args.run_dir.expanduser().resolve()
    if not (run_dir / "run.json").is_file() and not (run_dir / "events.jsonl").is_file():
        raise GradeRunError(f"--run-dir {run_dir} has neither run.json nor events.jsonl; is this a real PM run directory?")

    try:
        run_state = review_score.read_json(run_dir / "run.json") if (run_dir / "run.json").is_file() else {}
    except review_score.ReviewScoreError as exc:
        raise GradeRunError(str(exc)) from exc
    # read_json() returns whatever JSON parsed, with no shape check -- a
    # syntactically valid but non-object run.json (independent review,
    # 2026-09-11) must fail loudly by this module's own name, not with a
    # bare AttributeError from run_state.get(...) below.
    if not isinstance(run_state, dict):
        raise GradeRunError(f"run.json at {run_dir} did not parse to a JSON object (got {type(run_state).__name__})")
    events = read_events(run_dir)
    status = run_state.get("status")

    if status not in _TERMINAL_PM_STATUSES or not _terminal_status_confirmed(events, status):
        raise GradeRunError(
            f"run.json reports status={status!r}, not a confirmed-finished run (this tool requires "
            f"status in {sorted(_TERMINAL_PM_STATUSES)} AND PM's own closing event for it on record); "
            "wait for PM to reach one, or resume the run yourself if it is merely paused at needs-human"
        )

    problems = grade_finished_run(run_dir, root, policy_path, run_state, events)
    print(
        "grade_run.py: Tool 4 (model_report.py) and Tool 5 (leaderboard.py) are not yet built "
        "(see HANDOFF.md) -- run them manually once they exist"
    )

    if problems:
        print(f"grade_run.py: {len(problems)} grading/harvest problem(s) occurred:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except GradeRunError as exc:
        print(f"grade_run.py: error: {exc}", file=sys.stderr)
        sys.exit(1)
