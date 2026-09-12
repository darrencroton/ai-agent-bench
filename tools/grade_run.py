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

**G16, resolved:** a *superseded* (steered-away) attempt's own intermediate
commit is not named anywhere in `run.json`'s structure directly, but git
itself never discards it and never rewrites history across a PM-level
"epoch" boundary (a `finalize --stop` followed by a later restart) -- so it
is recoverable by walking the linear commit chain between a slice's own
`before_head` and its final accepted commit (`resolve_attempt_commits`,
below) and matching commits to attempts in file order, one each. This
relies on the Developer contract's one-commit-per-attempt convention, not a
mechanical guarantee `pm_lib` enforces, so every attempt is graded this way
only when the walked commit count matches the attempt count exactly;
otherwise this module falls back, per-slice, to exactly its prior
behavior -- grading only that slice's final attempt -- and reports the
mismatch as a named problem rather than guessing a partial or misaligned
mapping. Per-attempt review findings and the per-attempt `pm_decision`
(steer/accept/stop) were already fully recoverable regardless, from the
permanent event log and `run.json["slices"][i]["reviews"]` -- this closes
the remaining gap, the deterministic correctness/quality/scope grade for
every attempt, not just the accepted one.

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
import subprocess
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


def _find_slice_entry(run_state: dict[str, Any], slice_id: str) -> dict[str, Any] | None:
    """`slice_id`'s own entry from `run_state["slices"]`, or None if absent.

    Shared by `_resolve_grading_commit` and `_resolve_attempt_grading_plan`,
    which both need to locate the same entry -- one implementation, not two
    near-identical scans (AGENTS.md).
    """
    for entry in run_state.get("slices", []) or []:
        if isinstance(entry, dict) and entry.get("id") == slice_id:
            return entry
    return None


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
    entry = _find_slice_entry(run_state, slice_id)
    if entry is None:
        return None, f"slice {slice_id!r} not found in run.json's 'slices' list"
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


def resolve_attempt_commits(
    repo: Path, before_head: str, final_commit: str, expected_count: int
) -> tuple[list[str] | None, str | None]:
    """Walk the linear git history between a slice's own `before_head` and its
    final commit, recovering one ending commit per attempt, oldest first
    (G16, docs/MODE2-REWRITE-PLAN.md §8).

    Git history itself is permanent and continuous across any PM-level
    "epoch" boundary (a `finalize --stop` followed by a later restart) --
    nothing about a stop/relaunch cycle rewrites or discards a commit
    already made -- so this walk needs no notion of epoch boundaries at
    all; only the commit *count* can disagree with the attempt count. That
    disagreement is real to plan for: this relies on the Developer
    contract's one-commit-per-attempt convention, not a mechanical
    guarantee `pm_lib` enforces (an attempt abandoned via a top-level
    `pm stop` with uncommitted work leaves zero commits of its own; nothing
    stops more than one). Every check below is a named refusal, never a
    raise -- the caller falls back to grading only the final attempt when
    this returns a problem, so one slice's non-conforming history must
    never abort grading of any other slice.

    Returns:
        (commits, None): exactly `expected_count` commits, oldest first --
            commits[0] is attempt 0's ending commit, commits[-1] ==
            final_commit.
        (None, problem): `before_head` is not an ancestor of `final_commit`,
            the range contains a merge commit (breaks the strict 1:1
            ordering this walk assumes), the commit count doesn't match
            `expected_count`, or either `git log`/`git rev-list` call itself
            failed.
    """
    # Every git invocation below is wrapped so a failure -- a nonzero exit
    # (dev_check.run_git's DevCheckError) or the subprocess never starting
    # at all (OSError, e.g. git missing from PATH) -- is returned as a named
    # problem, never raised: this function's contract is the opposite of
    # dev_check.run_git's own (correct for its one-shot CLI use), because a
    # git failure here must never abort grading of every OTHER slice still
    # to be graded in this run (grade_finished_run's "never raises for a
    # single slice's own failure" promise).
    try:
        ancestor_check = subprocess.run(
            ["git", "-C", str(repo), "merge-base", "--is-ancestor", before_head, final_commit],
            check=False, capture_output=True, text=True,
        )
    except OSError as exc:
        return None, f"'git merge-base --is-ancestor {before_head} {final_commit}' could not be run in {repo}: {exc}"
    if ancestor_check.returncode not in (0, 1):
        return None, (
            f"'git merge-base --is-ancestor {before_head} {final_commit}' failed in {repo}: "
            f"{ancestor_check.stderr.strip()}"
        )
    if ancestor_check.returncode == 1:
        return None, f"before_head {before_head} is not an ancestor of {final_commit} in {repo}"

    commit_range = f"{before_head}..{final_commit}"
    try:
        has_merge_commit = dev_check.run_git(repo, "rev-list", "--min-parents=2", commit_range)
        commits = [line for line in dev_check.run_git(repo, "log", "--reverse", "--format=%H", commit_range).splitlines() if line]
    except (dev_check.DevCheckError, OSError) as exc:
        return None, f"could not walk commit range {commit_range} in {repo}: {exc}"

    if has_merge_commit:
        return None, f"commit range {commit_range} in {repo} contains a merge commit; not a linear chain"
    if len(commits) != expected_count:
        return None, (
            f"commit range {commit_range} in {repo} has {len(commits)} commit(s), expected {expected_count} "
            "(one per attempt) -- the Developer's one-commit-per-attempt convention doesn't hold here"
        )
    return commits, None


def _resolve_repo_path(run_state: dict[str, Any]) -> Path | None:
    repo = run_state.get("repo")
    return Path(repo).expanduser().resolve() if repo else None


def _resolve_slice_before_head_for_walk(
    run_state: dict[str, Any], slice_id: str, entry: dict[str, Any]
) -> tuple[str | None, str | None]:
    """The before_head to start the multi-attempt walk from: this slice's
    ORIGINAL before_head, as of its very first attempt -- not necessarily
    what `dev_check.resolve_before_head` would return.

    `resolve_before_head` is written to correctly grade one already-decided
    attempt, so for a slice that went through a stop/restart it deliberately
    prefers the MOST RECENT review's before_head -- the value correct for
    the epoch that actually got accepted. That is the wrong value to start
    a full-history walk from: it would silently truncate the walk to only
    the last epoch's commits, understating how many commits exist and
    causing a spurious count mismatch even though every attempt's commit is
    still sitting right there in git history.

    For any slice after the first, the previous slice's own recorded
    `commit` (`resolve_before_head`'s rule 4(a)) sidesteps this entirely: it
    is fixed the moment THIS slice was first launched and is completely
    independent of how many epochs this slice itself later went through --
    so it is preferred here directly, before ever consulting
    `resolve_before_head`. Only the first slice, with no predecessor to fall
    back on, defers to `resolve_before_head`'s own resolution -- which, for
    an accepted slice, is rule 4(b): the most recent review whose `head`
    matches the FINAL accepted commit. **A genuinely multi-epoch first
    slice always falls back to final-attempt-only grading here, regardless
    of whether an early (pre-restart) epoch's own review was ever recorded**
    -- rule 4(b)'s `head`-match filter can only ever select a review from
    the epoch that was actually accepted, never an earlier one, so an early
    epoch's before_head is not recovered by this path even when a review
    exists for it. Reviewing every one of a first slice's own epochs to
    recover its true earliest before_head is possible in principle but adds
    real machinery for a narrow case (this bench's own frozen plan
    mechanically elevates risk on both its slices, so this shows up only if
    Slice 1 itself both restarts AND still gets accepted) -- left as a
    named, graceful fallback rather than built, matching G16's own
    "moderate, well-scoped" mandate (docs/MODE2-REWRITE-PLAN.md §8).

    Returns:
        (before_head, None), or (None, problem) if `resolve_before_head`
        itself could not resolve one at all.
    """
    slices = run_state.get("slices") or []
    index = next((i for i, s in enumerate(slices) if isinstance(s, dict) and s.get("id") == slice_id), None)
    if index is not None and index > 0:
        previous_commit = slices[index - 1].get("commit")
        if previous_commit:
            return str(previous_commit), None

    try:
        return dev_check.resolve_before_head(run_state, slice_id, None, 0, entry), None
    except dev_check.DevCheckError as exc:
        return None, f"could not resolve {slice_id!r}'s own before_head: {exc}"


def _resolve_attempt_grading_plan(
    run_state: dict[str, Any], events: list[dict[str, Any]], slice_id: str, final_commit: str, final_attempt: int
) -> tuple[list[tuple[int, str, str]] | None, str | None]:
    """Every attempt's own (attempt, commit, before_head) for one slice, via
    `resolve_attempt_commits`, or (None, problem) for the caller to fall back
    to grading only the final attempt.

    `before_head` is constant across every attempt in the same PM "epoch"
    (`pm_lib/prompts.py`: "before_head is correct on every attempt" --
    within one epoch, not globally) and resets only at that epoch's own
    start: this slice's ORIGINAL before_head
    (`_resolve_slice_before_head_for_walk`) for the first epoch, or the
    commit the PREVIOUS epoch ended on for any later one. **Not** the
    immediately preceding attempt's own commit for every attempt uniformly
    -- a real bug this repo's own review round caught before commit,
    verified against the real completed run: Slice 1's five attempts are
    all one epoch (a `launch` then four `steer`s, no restart), so every one
    of them was reviewed and floor-checked against the SAME original
    before_head throughout: an incremental attempt-to-attempt base would
    silently miss a scope violation or lint finding introduced in an early
    attempt and left untouched by a later one, since nothing changed in
    THAT specific diff -- exactly the undercounting this function exists to
    avoid. `bench_lib.epoch_start_ordinals` gives each attempt's epoch-start
    ordinal directly from the event log (no git needed for this part): a
    strict, non-decreasing partition of `commits` into consecutive epochs.
    """
    repo = _resolve_repo_path(run_state)
    if repo is None:
        return None, "run.json has no 'repo' path recorded; cannot walk its git history"
    if not repo.is_dir():
        return None, f"recorded repo path {repo} does not exist; cannot walk its git history"

    entry = _find_slice_entry(run_state, slice_id)
    if entry is None:
        return None, f"slice {slice_id!r} not found in run.json's 'slices' list"

    slice_before_head, before_head_problem = _resolve_slice_before_head_for_walk(run_state, slice_id, entry)
    if slice_before_head is None:
        return None, before_head_problem

    commits, walk_problem = resolve_attempt_commits(repo, slice_before_head, final_commit, final_attempt + 1)
    if commits is None:
        return None, walk_problem

    epoch_starts = bench_lib.epoch_start_ordinals(events, slice_id)
    plan: list[tuple[int, str, str]] = []
    for attempt_number, attempt_commit in enumerate(commits):
        epoch_start = epoch_starts[attempt_number]
        attempt_before_head = slice_before_head if epoch_start == 0 else commits[epoch_start - 1]
        plan.append((attempt_number, attempt_commit, attempt_before_head))
    return plan, None


def dispatch_grade(
    run_dir: Path,
    slice_number: int,
    attempt: int,
    policy_path: Path,
    commit: str | None = None,
    before_head: str | None = None,
) -> None:
    """Grade one specific attempt of one slice via Tool 1.

    Calls dev_check.main() directly (not a subprocess) -- it returns 0 or
    raises dev_check.DevCheckError, never sys.exit()s itself.

    `before_head` is only ever passed explicitly for a multi-attempt walk
    (`_resolve_attempt_grading_plan`) -- the single-final-attempt fallback
    leaves it None and lets dev_check.py's own `resolve_before_head` derive
    it structurally, unchanged from before G16.
    """
    argv = [
        "--run-dir", str(run_dir),
        "--slice", str(slice_number),
        "--attempt", str(attempt),
        "--policy", str(policy_path),
    ]
    if commit is not None:
        argv += ["--commit", commit]
    if before_head is not None:
        argv += ["--before-head", before_head]
    dev_check.main(argv)


def dispatch_review_harvest(run_dir: Path, slice_number: int, skill: str, root: Path) -> list[str]:
    """Harvest one skill's canonical reviews for one slice via Tools 2/3.

    Calls review_score.run_review_score() directly, not review_score.main():
    main() parses sys.argv and calls sys.exit() on its own error, which
    would kill this module's whole grading pass over one bad review report.

    Returns:
        Per-attempt problems `run_review_score` itself recovered from
        (a missing sheet row -- expected whenever a slice's git-log walk
        failed and this module fell back to grading only its final
        attempt, see `_resolve_attempt_grading_plan`; not a fatal error);
        empty if every canonical review for this (slice, skill) harvested
        cleanly.
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
    (slice_number, slice_id, attempt) for its FINAL attempt.

    The final attempt's own ordinal anchors both grading paths in
    `grade_finished_run`: it is `_resolve_attempt_grading_plan`'s
    `expected_count - 1` (the git-log walk grades every attempt 0..final
    when the walk succeeds), and it is the sole attempt graded when that
    walk falls back (see `resolve_attempt_commits`).

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


def _grade_attempt_safely(
    run_dir: Path, slice_number: int, attempt: int, policy_path: Path, commit: str, before_head: str | None
) -> str | None:
    """dispatch_grade, catching dev_check's own failure modes into a named
    problem string -- shared by both grading paths below so neither has to
    duplicate the same try/except.

    Returns:
        None on success, else a human-readable problem string.
    """
    try:
        dispatch_grade(run_dir, slice_number, attempt, policy_path, commit, before_head)
        return None
    except (dev_check.DevCheckError, OSError) as exc:
        return f"dev_check.py failed grading slice {slice_number} attempt {attempt}: {exc}"


def _grade_slice(
    run_dir: Path,
    policy_path: Path,
    run_state: dict[str, Any],
    events: list[dict[str, Any]],
    slice_number: int,
    slice_id: str,
    attempt: int,
) -> list[str]:
    """Grade one slice's attempt(s) -- grade_finished_run's own per-slice
    unit, split out to keep that function's loop simple. Every attempt is
    graded when `_resolve_attempt_grading_plan`'s git-log walk recovers a
    clean one-commit-per-attempt mapping (G16); otherwise this falls back to
    grading only the final attempt, exactly as before G16, with the walk's
    own reason recorded as a problem.

    Returns:
        Every problem encountered grading this one slice (empty if none).
    """
    problems: list[str] = []
    commit, commit_problem = _resolve_grading_commit(run_state, slice_id)
    if commit_problem is not None:
        problems.append(f"slice {slice_number} attempt {attempt}: {commit_problem}")
        print(f"grade_run.py: warning: {problems[-1]}", file=sys.stderr)
        return problems

    plan, plan_problem = _resolve_attempt_grading_plan(run_state, events, slice_id, commit, attempt)
    if plan is None:
        if plan_problem is not None:
            problems.append(f"slice {slice_number}: {plan_problem}; grading only its final attempt {attempt}")
            print(f"grade_run.py: warning: {problems[-1]}", file=sys.stderr)
        print(f"grade_run.py: grading slice {slice_number} attempt {attempt} (its final attempt)")
        grade_problem = _grade_attempt_safely(run_dir, slice_number, attempt, policy_path, commit, None)
        if grade_problem is not None:
            problems.append(grade_problem)
            print(f"grade_run.py: warning: {grade_problem}", file=sys.stderr)
        return problems

    for attempt_number, attempt_commit, attempt_before_head in plan:
        print(f"grade_run.py: grading slice {slice_number} attempt {attempt_number} of {attempt}")
        grade_problem = _grade_attempt_safely(
            run_dir, slice_number, attempt_number, policy_path, attempt_commit, attempt_before_head
        )
        if grade_problem is not None:
            problems.append(grade_problem)
            print(f"grade_run.py: warning: {grade_problem}", file=sys.stderr)
    return problems


def grade_finished_run(
    run_dir: Path, root: Path, policy_path: Path, run_state: dict[str, Any], events: list[dict[str, Any]]
) -> list[str]:
    """Grade every gradeable slice's attempts (via `_grade_slice`), then
    harvest every known review target. Never raises for a single
    slice/review/attempt's own failure -- each is caught and returned as a
    human-readable problem string.

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
        problems.extend(_grade_slice(run_dir, policy_path, run_state, events, slice_number, slice_id, attempt))

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
            "Grade one FINISHED PM run in a single pass: every attempt of every slice recoverable via its "
            "git-log walk (falling back to just the final attempt per-slice when that walk doesn't resolve "
            "cleanly), plus every commissioned review (docs/MODE2-REWRITE-PLAN.md §5). Refuses to run "
            "against a run still in progress."
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
    return bench_lib.report_problems("grade_run.py", problems, kind="grading/harvest problem(s)")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except GradeRunError as exc:
        print(f"grade_run.py: error: {exc}", file=sys.stderr)
        sys.exit(1)
