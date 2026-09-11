"""Tests for tools/run_seat.py (the driver: watches one PM run and dispatches
to Tools 1-3 at the right events -- docs/MODE2-REWRITE-PLAN.md §7a).

Fixtures are hand-written per test: synthetic event lists, a throwaway
`run.json`/`events.jsonl` pair under `tmp_path`. dev_check.main() and
review_score.run_review_score() are monkeypatched at their call boundaries
(dispatch_grade/dispatch_review_harvest) -- this module's job is the
driver's own dispatch/polling logic in isolation, never a real grading or
review-harvest subprocess (that integration is covered by
tests/test_dev_check.py, tests/test_review_score.py, and
tests/test_tool_contract.py).

Several tests here guard against real defects found across TWO independent
codex reviews (2026-09-11), each verified directly against `pm_lib` source:
grading a superseded attempt against the wrong (current, not historical)
commit; the SAME defect resurfacing for an accepted slice once a LATER
slice has moved the repository's global HEAD; floor and accept for one
attempt colliding in a single poll and silently losing the only usable
grade; a terminal-status race where PM saves run.json's status before
appending the event that reflects it (and a first fix for that race being
only a fixed-delay heuristic, not real synchronization); a review event
racing ahead of its own attempt's floor event and being permanently lost;
and a false assumption that an operator's top-level `pm stop` never carries
a "slice" field.

Run with plain pytest from the repo root: `pytest tests/test_run_seat.py`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import dev_check  # noqa: E402
import review_score  # noqa: E402
import run_seat  # noqa: E402


# --- helpers -------------------------------------------------------------


def _write_events_jsonl(run_dir: Path, events: list[dict]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "events.jsonl").write_text(
        "\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8"
    )


def _append_event(run_dir: Path, event: dict) -> None:
    with (run_dir / "events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event) + "\n")


def _write_run_json(run_dir: Path, status: str | None, **extra: object) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {"status": status, **extra}
    (run_dir / "run.json").write_text(json.dumps(payload), encoding="utf-8")


def _valid_policy_yaml(tmp_path: Path, **overrides: object) -> Path:
    """A minimal policy file with every key dev_check.load_policy and
    run_seat.load_policy both require, valid by default -- mirrors the
    fixture pattern tests/test_dev_check.py's TestLoadPolicy already uses.
    A value of None omits that key entirely, to test a missing key."""
    fields: dict[str, object] = {
        "backend": "local",
        "pm_scripts_dir": "/x",
        "lint_script": "/x",
        "health_script": "/x",
        "python_interpreter": "python3",
        "subprocess_timeout_seconds": 600,
        "driver_poll_interval_seconds": 15,
    }
    fields.update(overrides)
    lines = []
    for key, value in fields.items():
        if value is None:
            continue
        lines.append(f"{key}: {value!r}" if isinstance(value, str) else f"{key}: {value}")
    policy_path = tmp_path / "policy.yaml"
    policy_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return policy_path


# A run_state where no slice is current and nothing is accepted -- the
# common "safe to default to current HEAD" case most dispatch tests want,
# since they only care about grading dispatch, not commit resolution.
_NO_ACTIVE_SLICE_STATE: dict[str, object] = {"status": "active", "current_slice": None, "slices": []}


# --- parse_slice_number ----------------------------------------------------


def test_parse_slice_number_extracts_the_integer() -> None:
    assert run_seat.parse_slice_number("Slice 1") == 1
    assert run_seat.parse_slice_number("Slice 2") == 2


def test_parse_slice_number_malformed_ids_return_none_never_raise() -> None:
    """A malformed slice id in an event log must be a recoverable None, not a
    crash or a silently wrong integer -- process_new_events relies on this to
    record a named problem and keep going (see the skipped-floor-event test
    below), so parse_slice_number itself must never raise."""
    for bad_id in ["Slice 1a", "slice 1", "Slice", "Slice -1", "Slice", "", "Slice  1"]:
        assert run_seat.parse_slice_number(bad_id) is None


# --- review_skill_for_note ---------------------------------------------


def test_review_skill_for_note_matches_known_skill_prefixes() -> None:
    assert run_seat.review_skill_for_note("drift-audit via codex, PASS") == "drift-audit"
    assert run_seat.review_skill_for_note("code-review via claude") == "code-review"


def test_review_skill_for_note_returns_none_for_an_unmatched_note() -> None:
    assert run_seat.review_skill_for_note("some unrelated note") is None


def test_review_skill_for_note_rejects_a_prefix_substring_trap() -> None:
    """A note that starts with a skill's name but is not literally
    "<skill> via " must not false-match -- e.g. a hypothetical
    "code-reviewed via codex" note starts with the literal string
    "code-review" but is not a code-review commission. A naive
    `note.startswith(skill)` check (instead of the full "<skill> via "
    prefix) would wrongly match this."""
    assert run_seat.review_skill_for_note("code-reviewed via codex") is None
    assert run_seat.review_skill_for_note("drift-audited via codex") is None


# --- dispatch_review_harvest -----------------------------------------------


def test_dispatch_review_harvest_raises_review_score_error_for_missing_run_id(
    tmp_path: Path,
) -> None:
    """Regression test: this used to raise run_seat.RunSeatError, which
    watch_once's except clause does not catch -- an uncaught RunSeatError
    here would have killed the whole watch loop instead of being logged as a
    per-target harvest problem. It must raise review_score.ReviewScoreError,
    the same type run_review_score() itself raises for the identical
    condition, so every caller can catch one exception type."""
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "run.json").write_text(json.dumps({"status": "active"}), encoding="utf-8")

    with pytest.raises(review_score.ReviewScoreError, match="run_id"):
        run_seat.dispatch_review_harvest(run_dir, 1, "drift-audit", tmp_path)


# --- known_review_targets ---------------------------------------------------


def test_known_review_targets_collects_every_slice_skill_pair_from_the_full_log() -> None:
    events = [
        {"kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
        {"kind": "review", "slice": "Slice 1", "note": "drift-audit via codex", "evidence": "r1.md"},
        {"kind": "review", "slice": "Slice 1", "note": "code-review via claude", "evidence": "r2.md"},
        {"kind": "review", "slice": "Slice 2", "note": "drift-audit via codex", "evidence": "r3.md"},
    ]
    assert run_seat.known_review_targets(events) == {(1, "drift-audit"), (1, "code-review"), (2, "drift-audit")}


def test_known_review_targets_ignores_events_without_evidence_or_an_unmatched_note() -> None:
    """A timeout review event carries the same "<skill> via <tool>" note
    prefix as a successful commission but no `evidence` field at all (see
    review_score.find_review_events's own docstring) -- it must never be
    treated as a harvestable target."""
    events = [
        {"kind": "review", "slice": "Slice 1", "note": "drift-audit via codex timed out after 900s"},
        {"kind": "review", "slice": "Slice 1", "note": "an unrelated note", "evidence": "r.md"},
    ]
    assert run_seat.known_review_targets(events) == set()


def test_known_review_targets_is_recomputed_from_the_whole_log_not_just_new_events() -> None:
    """The whole point of this function: it is called with the FULL events
    list every poll (see watch_once), not a slice of newly-seen ones, so a
    review event from long before the current poll's start_index is still a
    target every time."""
    events = [
        {"kind": "review", "slice": "Slice 1", "note": "code-review via claude", "evidence": "r1.md"},
    ]
    assert run_seat.known_review_targets(events) == {(1, "code-review")}


# --- _resolve_grading_commit -------------------------------------------------


def test_resolve_grading_commit_uses_the_recorded_commit_for_an_accepted_slice() -> None:
    """Regression test: an independent codex review found that grading only
    the batch's latest event per slice does not mean grading the right
    commit, because HEAD is repository-wide, not per-slice -- a LATER
    slice's own work can advance HEAD past an EARLIER, already-accepted
    slice's ending commit, e.g. when a driver catches up on a backlog
    spanning both slices. pm_lib.slice_ops.finalize_accept records the
    accepted commit on the slice's own run.json entry, which remains correct
    no matter how much HEAD has since moved -- this must be used explicitly
    instead of ever defaulting to "whatever HEAD currently is"."""
    run_state = {
        "current_slice": {"id": "Slice 2"},  # a later slice is now live
        "slices": [
            {"id": "Slice 1", "status": "accepted", "commit": "abc123"},
            {"id": "Slice 2", "status": None},
        ],
    }
    commit, problem = run_seat._resolve_grading_commit(run_state, "Slice 1")
    assert commit == "abc123"
    assert problem is None


def test_resolve_grading_commit_defaults_to_head_when_the_slice_is_still_current() -> None:
    run_state = {"current_slice": {"id": "Slice 1"}, "slices": [{"id": "Slice 1", "status": None}]}
    commit, problem = run_seat._resolve_grading_commit(run_state, "Slice 1")
    assert commit is None
    assert problem is None


def test_resolve_grading_commit_defaults_to_head_when_no_slice_is_current_at_all() -> None:
    """A paused/stopped run with no live slice cannot have had its HEAD moved
    by anything else -- current HEAD is still safe to default to."""
    run_state = {"current_slice": None, "slices": [{"id": "Slice 1", "status": "stopped"}]}
    commit, problem = run_seat._resolve_grading_commit(run_state, "Slice 1")
    assert commit is None
    assert problem is None


def test_resolve_grading_commit_refuses_when_a_different_slice_is_now_current_and_this_one_was_not_accepted() -> None:
    run_state = {
        "current_slice": {"id": "Slice 2"},
        "slices": [{"id": "Slice 1", "status": "stopped"}, {"id": "Slice 2", "status": None}],
    }
    commit, problem = run_seat._resolve_grading_commit(run_state, "Slice 1")
    assert commit is None
    assert problem is not None
    assert "Slice 1" in problem and "Slice 2" in problem


def test_resolve_grading_commit_reports_malformed_state_instead_of_falling_through_to_head() -> None:
    """Regression test for a P2 defect an independent (third-round) codex
    review found: an entry recorded `status == "accepted"` but with no
    `commit` at all (never expected from a well-formed run.json) must be a
    named problem, not a silent fall-through past the accepted-slices loop
    into "no slice is current, default to HEAD" -- HEAD could be completely
    wrong for this slice by the time such corrupted state is ever observed."""
    run_state = {"current_slice": None, "slices": [{"id": "Slice 1", "status": "accepted", "commit": None}]}
    commit, problem = run_seat._resolve_grading_commit(run_state, "Slice 1")
    assert commit is None
    assert problem is not None
    assert "Slice 1" in problem and "no recorded commit" in problem


# --- process_new_events: dispatch logic ----------------------------------


def test_floor_event_triggers_exactly_one_grade_dispatch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls = []
    monkeypatch.setattr(
        run_seat,
        "dispatch_grade",
        lambda run_dir, slice_number, attempt, policy_path, commit=None: calls.append(
            (run_dir, slice_number, attempt, policy_path, commit)
        ),
    )
    events = [
        {"kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
        {"kind": "floor", "slice": "Slice 1", "note": "6/7"},
    ]
    policy_path = tmp_path / "policy.yaml"
    problems = run_seat.process_new_events(events, 0, tmp_path, _NO_ACTIVE_SLICE_STATE, policy_path, {}, print)
    assert calls == [(tmp_path, 1, 0, policy_path, None)]
    assert problems == []


def test_floor_and_accept_for_the_same_attempt_are_both_dispatched_not_collapsed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Regression test for a P1 defect an independent codex review found in
    the first fix round: dispatching only the batch's LAST grading event per
    slice silently discarded the `floor` event whenever `accept` (or
    `slice-stop`) for the SAME attempt landed in the same poll -- which is
    the NORMAL case for acceptance, not a rare backlog: pm_lib's
    finalize_accept appends `floor` and `accept` back-to-back inside one PM
    command, so a driver polling normally sees both together far more often
    than not. Both events belong to attempt 0 (no launch-family event
    between them), so both must be dispatched -- grouping by (slice,
    attempt), not slice alone, is what fixes this."""
    calls = []
    monkeypatch.setattr(
        run_seat,
        "dispatch_grade",
        lambda run_dir, slice_number, attempt, policy_path, commit=None: calls.append((slice_number, attempt)),
    )
    events = [
        {"kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
        {"kind": "floor", "slice": "Slice 1", "note": "7/7"},
        {"kind": "accept", "slice": "Slice 1", "note": "accepted"},
    ]
    problems = run_seat.process_new_events(events, 0, tmp_path, _NO_ACTIVE_SLICE_STATE, tmp_path / "policy.yaml", {}, print)
    assert calls == [(1, 0), (1, 0)]
    assert problems == []


def test_accept_and_slice_stop_events_also_trigger_grade_dispatch(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """_SLICE_GRADE_KINDS groups floor/accept/slice-stop/stop together --
    accept and slice-stop must dispatch a grade exactly like floor does. Two
    DIFFERENT slices, each with only one attempt, so nothing here is
    superseded."""
    calls = []
    monkeypatch.setattr(
        run_seat,
        "dispatch_grade",
        lambda run_dir, slice_number, attempt, policy_path, commit=None: calls.append((slice_number, attempt)),
    )
    events = [
        {"kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
        {"kind": "accept", "slice": "Slice 1", "note": "accepted"},
        {"kind": "launch", "slice": "Slice 2", "note": "attempt 0"},
        {"kind": "slice-stop", "slice": "Slice 2", "note": "floor fact 5 failed"},
    ]
    problems = run_seat.process_new_events(events, 0, tmp_path, _NO_ACTIVE_SLICE_STATE, tmp_path / "policy.yaml", {}, print)
    assert calls == [(1, 0), (2, 0)]
    assert problems == []


def test_stop_event_with_a_slice_grades_regardless_of_the_reason(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """pm_lib.slice_ops.stop() sets a "stop" event's "slice" field to
    whatever current_slice happened to be, whenever one is active --
    verified directly against PM source. This is true for BOTH an
    operator's own top-level `pm stop` and an attempt-budget-exhaustion stop
    alike; there is no way, and no need, to tell them apart from the event's
    shape."""
    calls = []
    monkeypatch.setattr(
        run_seat,
        "dispatch_grade",
        lambda run_dir, slice_number, attempt, policy_path, commit=None: calls.append(slice_number),
    )
    events = [
        {"kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
        {"kind": "stop", "slice": "Slice 1", "note": "attempt budget exhausted"},
    ]
    problems = run_seat.process_new_events(events, 0, tmp_path, _NO_ACTIVE_SLICE_STATE, tmp_path / "policy.yaml", {}, print)
    assert calls == [1]
    assert problems == []


def test_stop_event_with_no_slice_triggers_nothing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A "stop" event carries no "slice" field only when no slice was current
    at that moment -- e.g. between slices, or after a slice was already
    accepted/stopped."""
    calls = []
    monkeypatch.setattr(run_seat, "dispatch_grade", lambda *args, **kwargs: calls.append(args))
    events = [{"kind": "stop", "slice": None, "note": "operator stopped the run between slices"}]
    problems = run_seat.process_new_events(events, 0, tmp_path, _NO_ACTIVE_SLICE_STATE, tmp_path / "policy.yaml", {}, print)
    assert calls == []
    assert problems == []


def test_noop_event_kinds_trigger_no_dispatch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    grade_calls = []
    monkeypatch.setattr(run_seat, "dispatch_grade", lambda *args, **kwargs: grade_calls.append(args))
    events = [
        {"kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
        {"kind": "relaunch", "slice": "Slice 1", "note": "attempt 1"},
        {"kind": "steer", "slice": "Slice 1", "note": "fix it"},
        {"kind": "grant", "slice": "Slice 1", "note": "granted"},
        {"kind": "observe", "slice": "Slice 1", "note": "observed"},
        {"kind": "complete", "slice": None, "note": "done"},
        # "review" is also a no-op here -- harvesting is dispatched from
        # watch_once via known_review_targets, never from here.
        {"kind": "review", "slice": "Slice 1", "note": "drift-audit via codex", "evidence": "r.md"},
    ]
    problems = run_seat.process_new_events(events, 0, tmp_path, _NO_ACTIVE_SLICE_STATE, tmp_path / "policy.yaml", {}, print)
    assert grade_calls == []
    assert problems == []


def test_start_index_skips_events_before_it(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Simulates a driver that already processed a prefix of the log in an
    earlier watch_once() iteration -- events before start_index must never
    be re-dispatched, even when they are themselves gradeable."""
    calls = []
    monkeypatch.setattr(
        run_seat,
        "dispatch_grade",
        lambda run_dir, slice_number, attempt, policy_path, commit=None: calls.append((slice_number, attempt)),
    )
    events = [
        {"kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
        {"kind": "floor", "slice": "Slice 1", "note": "already handled in an earlier poll"},
        {"kind": "launch", "slice": "Slice 2", "note": "attempt 0"},
        {"kind": "floor", "slice": "Slice 2", "note": "new this poll"},
    ]
    problems = run_seat.process_new_events(events, 2, tmp_path, _NO_ACTIVE_SLICE_STATE, tmp_path / "policy.yaml", {}, print)
    assert calls == [(2, 0)]
    assert problems == []


def test_floor_event_with_unparsable_slice_id_is_skipped_and_recorded(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A malformed slice id in the event log (which this driver never wrote
    itself) must be a named, visible problem -- never a raised exception
    that kills the whole watch loop, and never a silent no-op that hides a
    corrupt log from the operator."""
    calls = []
    monkeypatch.setattr(run_seat, "dispatch_grade", lambda *args, **kwargs: calls.append(args))
    logged = []
    events = [{"kind": "floor", "slice": "Slice X", "note": "malformed"}]
    problems = run_seat.process_new_events(events, 0, tmp_path, _NO_ACTIVE_SLICE_STATE, tmp_path / "policy.yaml", {}, logged.append)
    assert calls == []
    assert len(problems) == 1
    assert "Slice X" in problems[0]
    assert any("Slice X" in message for message in logged)


def test_dispatch_grade_failure_is_caught_logged_and_remaining_events_still_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A grading failure for one attempt must never be a reason to stop
    watching a run that may still be producing more attempts. The second
    slice's floor event must still be graded even though the first raised
    dev_check.DevCheckError."""
    calls = []

    def fake_dispatch_grade(run_dir: Path, slice_number: int, attempt: int, policy_path: Path, commit: str | None = None) -> None:
        calls.append(slice_number)
        if slice_number == 1:
            raise dev_check.DevCheckError("boom: hidden tests worktree missing")

    monkeypatch.setattr(run_seat, "dispatch_grade", fake_dispatch_grade)
    logged = []
    events = [
        {"kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
        {"kind": "floor", "slice": "Slice 1", "note": "first"},
        {"kind": "launch", "slice": "Slice 2", "note": "attempt 0"},
        {"kind": "floor", "slice": "Slice 2", "note": "second"},
    ]
    problems = run_seat.process_new_events(events, 0, tmp_path, _NO_ACTIVE_SLICE_STATE, tmp_path / "policy.yaml", {}, logged.append)
    assert calls == [1, 2]
    assert len(problems) == 1
    assert "slice 1" in problems[0] and "attempt 0" in problems[0] and "boom" in problems[0]
    assert any("boom" in message for message in logged)


def test_dispatch_grade_oserror_is_also_caught(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A transient filesystem/subprocess failure (disk full, a git process
    that could not be spawned) is not itself a dev_check.py defect -- it
    must be caught the same way a DevCheckError is, per _GRADE_EXCEPTIONS,
    not left to crash the watch loop."""

    def fake_dispatch_grade(run_dir: Path, slice_number: int, attempt: int, policy_path: Path, commit: str | None = None) -> None:
        raise OSError("no space left on device")

    monkeypatch.setattr(run_seat, "dispatch_grade", fake_dispatch_grade)
    events = [
        {"kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
        {"kind": "floor", "slice": "Slice 1", "note": "6/7"},
    ]
    problems = run_seat.process_new_events(events, 0, tmp_path, _NO_ACTIVE_SLICE_STATE, tmp_path / "policy.yaml", {}, print)
    assert len(problems) == 1
    assert "no space left" in problems[0]


def test_backlog_spanning_two_attempts_grades_only_the_latest_and_skips_the_rest(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Regression test: dev_check.py can only check out the Developer repo's
    CURRENT HEAD -- a backlog spanning more than one attempt's floor event
    for the same slice (a driver restart, or simply starting late against an
    already-progressed run) would grade BOTH attempts' rows against the SAME
    (latest) commit if dispatched naively, silently mislabeling the earlier
    one's data. There is no way to recover an earlier attempt's own
    historical commit, so the fix is to refuse the earlier one outright."""
    calls = []
    monkeypatch.setattr(
        run_seat,
        "dispatch_grade",
        lambda run_dir, slice_number, attempt, policy_path, commit=None: calls.append((slice_number, attempt)),
    )
    events = [
        {"kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
        {"kind": "floor", "slice": "Slice 1", "note": "6/7"},
        {"kind": "relaunch", "slice": "Slice 1", "note": "attempt 1"},
        {"kind": "floor", "slice": "Slice 1", "note": "7/7"},
    ]
    logged = []
    problems = run_seat.process_new_events(events, 0, tmp_path, _NO_ACTIVE_SLICE_STATE, tmp_path / "policy.yaml", {}, logged.append)
    assert calls == [(1, 1)]
    assert len(problems) == 1
    assert "superseded" in problems[0] and "index 1" in problems[0]
    assert any("superseded" in message for message in logged)


def test_attempt_ordinal_failure_is_caught_logged_and_remaining_events_still_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A floor/accept/slice-stop/stop event with a recognised slice id but no
    launch-family event recorded before it at all should not occur in a
    well-formed log, but bench_lib.attempt_ordinal raises BenchLibError
    rather than guess in that case -- process_new_events must catch it and
    keep processing the rest of the events (here, a second, well-formed
    slice's floor event)."""
    calls = []
    monkeypatch.setattr(
        run_seat,
        "dispatch_grade",
        lambda run_dir, slice_number, attempt, policy_path, commit=None: calls.append((slice_number, attempt)),
    )
    logged = []
    events = [
        {"kind": "floor", "slice": "Slice 1", "note": "no launch ever recorded for this slice"},
        {"kind": "launch", "slice": "Slice 2", "note": "attempt 0"},
        {"kind": "floor", "slice": "Slice 2", "note": "6/7"},
    ]
    problems = run_seat.process_new_events(events, 0, tmp_path, _NO_ACTIVE_SLICE_STATE, tmp_path / "policy.yaml", {}, logged.append)
    assert calls == [(2, 0)]
    assert len(problems) == 1
    assert "slice 1" in problems[0]
    assert any("slice 1" in message for message in logged)


def test_backlogged_accept_uses_the_recorded_commit_not_the_repos_current_global_head(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Regression test for the second codex review's finding: "latest event
    per slice" is not the same as "HEAD reflects that slice's commit",
    because HEAD is repository-wide. If Slice 1 is already accepted (with
    its own recorded commit) and Slice 2 has since become current, grading
    Slice 1's backlogged accept event must pass that RECORDED commit
    explicitly, not rely on dev_check.py's own current-HEAD default (which
    would silently reflect Slice 2's ongoing work instead)."""
    calls = []
    monkeypatch.setattr(
        run_seat,
        "dispatch_grade",
        lambda run_dir, slice_number, attempt, policy_path, commit=None: calls.append((slice_number, attempt, commit)),
    )
    run_state = {
        "current_slice": {"id": "Slice 2"},
        "slices": [{"id": "Slice 1", "status": "accepted", "commit": "deadbeef"}],
    }
    events = [
        {"kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
        {"kind": "accept", "slice": "Slice 1", "note": "accepted"},
    ]
    problems = run_seat.process_new_events(events, 0, tmp_path, run_state, tmp_path / "policy.yaml", {}, print)
    assert calls == [(1, 0, "deadbeef")]
    assert problems == []


def test_grading_is_skipped_with_a_named_problem_when_no_commit_can_be_resolved(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A stopped-without-acceptance slice, once a different slice has since
    become current, has no structurally recorded commit of its own --
    grading it would have to guess; this driver refuses instead."""
    calls = []
    monkeypatch.setattr(run_seat, "dispatch_grade", lambda *args, **kwargs: calls.append(args))
    run_state = {
        "current_slice": {"id": "Slice 2"},
        "slices": [{"id": "Slice 1", "status": "stopped"}],
    }
    events = [
        {"kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
        {"kind": "slice-stop", "slice": "Slice 1", "note": "floor fact 5 failed"},
    ]
    logged = []
    problems = run_seat.process_new_events(events, 0, tmp_path, run_state, tmp_path / "policy.yaml", {}, logged.append)
    assert calls == []
    assert len(problems) == 1
    assert "Slice 1" in problems[0] and "Slice 2" in problems[0]


# --- watch_once: one poll iteration ---------------------------------------


def test_watch_once_returns_the_new_seen_index_and_status(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    events = [
        {"kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
        {"kind": "floor", "slice": "Slice 1", "note": "6/7"},
    ]
    _write_events_jsonl(run_dir, events)
    _write_run_json(run_dir, "active")
    monkeypatch.setattr(run_seat, "dispatch_grade", lambda *args, **kwargs: None)
    monkeypatch.setattr(run_seat, "dispatch_review_harvest", lambda *args, **kwargs: None)

    seen_index, problems, status, confirmed = run_seat.watch_once(run_dir, tmp_path, tmp_path / "policy.yaml", 0, {}, print)
    assert seen_index == len(events)
    assert problems == []
    assert status == "active"
    assert confirmed is False


def test_watch_once_dispatches_no_new_grading_with_no_new_events(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """What makes the real watch() loop poll-safe: calling watch_once again
    with the seen_index it just returned, and no new events appended, must
    not re-dispatch any grading already handled."""
    run_dir = tmp_path / "run"
    _write_events_jsonl(
        run_dir,
        [
            {"kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
            {"kind": "floor", "slice": "Slice 1", "note": "6/7"},
        ],
    )
    _write_run_json(run_dir, "active")
    calls = []
    monkeypatch.setattr(run_seat, "dispatch_grade", lambda *args, **kwargs: calls.append(args))
    monkeypatch.setattr(run_seat, "dispatch_review_harvest", lambda *args, **kwargs: None)

    seen_index, _, _, _ = run_seat.watch_once(run_dir, tmp_path, tmp_path / "policy.yaml", 0, {}, print)
    assert len(calls) == 1

    calls.clear()
    seen_index_again, problems_again, _, _ = run_seat.watch_once(
        run_dir, tmp_path, tmp_path / "policy.yaml", seen_index, {}, print
    )
    assert seen_index_again == seen_index
    assert problems_again == []
    assert calls == []


def test_watch_once_does_not_retry_a_failure_from_its_own_same_call(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Regression test for a bug introduced (and caught) while adding the
    bounded retry: _retry_pending_grades must run BEFORE process_new_events
    within one watch_once() call, so a failure that process_new_events just
    queued is not immediately retried moments later in that SAME call --
    only on the NEXT poll, after a full poll interval has actually passed,
    which is the entire point of retrying at all (giving a transient
    condition time to clear, not re-trying back-to-back)."""
    run_dir = tmp_path / "run"
    _write_events_jsonl(
        run_dir,
        [
            {"kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
            {"kind": "floor", "slice": "Slice 1", "note": "6/7"},
        ],
    )
    _write_run_json(run_dir, "active")
    calls = []

    def failing_once(run_dir_arg: Path, slice_number: int, attempt: int, policy_path: Path, commit=None) -> None:
        calls.append(1)
        raise dev_check.DevCheckError("boom")

    monkeypatch.setattr(run_seat, "dispatch_grade", failing_once)
    monkeypatch.setattr(run_seat, "dispatch_review_harvest", lambda *args, **kwargs: None)

    pending: dict[tuple[str, int], None] = {}
    run_seat.watch_once(run_dir, tmp_path, tmp_path / "policy.yaml", 0, pending, print)
    assert len(calls) == 1  # only the original attempt, not also an immediate retry
    assert pending == {("Slice 1", 0): None}  # queued for the NEXT poll instead


def test_watch_once_re_attempts_review_harvest_every_poll_even_with_no_new_events(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Regression test: PM's review command has no precondition requiring a
    prior finalize/floor call, so a review event can arrive before
    dev_check.py has ever created that attempt's scoring-sheet row --
    harvesting it then fails. The first build only retried harvesting when a
    NEW "review" event appeared, so a review that failed once was never
    retried once the row later existed. This asserts the fix: harvesting is
    attempted on EVERY poll for every known (slice, skill) target."""
    run_dir = tmp_path / "run"
    _write_events_jsonl(
        run_dir,
        [{"kind": "review", "slice": "Slice 1", "note": "drift-audit via codex", "evidence": "r.md"}],
    )
    _write_run_json(run_dir, "active")
    monkeypatch.setattr(run_seat, "dispatch_grade", lambda *args, **kwargs: None)
    calls = []
    monkeypatch.setattr(run_seat, "dispatch_review_harvest", lambda *args, **kwargs: calls.append(args))

    seen_index, _, _, _ = run_seat.watch_once(run_dir, tmp_path, tmp_path / "policy.yaml", 0, {}, print)
    assert len(calls) == 1

    # No new events between polls -- harvesting must still be re-attempted.
    calls.clear()
    run_seat.watch_once(run_dir, tmp_path, tmp_path / "policy.yaml", seen_index, {}, print)
    assert len(calls) == 1


def test_watch_once_harvest_failure_is_caught_logged_and_recorded(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    run_dir = tmp_path / "run"
    _write_events_jsonl(
        run_dir,
        [{"kind": "review", "slice": "Slice 1", "note": "drift-audit via codex", "evidence": "r.md"}],
    )
    _write_run_json(run_dir, "active")

    def fake_dispatch_review_harvest(run_dir_arg: Path, slice_number: int, skill: str, root: Path) -> None:
        raise review_score.ReviewScoreError("boom: sha256 mismatch")

    monkeypatch.setattr(run_seat, "dispatch_review_harvest", fake_dispatch_review_harvest)
    logged = []
    _, problems, _, _ = run_seat.watch_once(run_dir, tmp_path, tmp_path / "policy.yaml", 0, {}, logged.append)
    assert len(problems) == 1
    assert "boom" in problems[0]
    assert any("boom" in message for message in logged)


def test_watch_once_missing_run_json_reads_status_as_none_not_an_error(tmp_path: Path) -> None:
    """run.json does not exist until PM's own `init` completes -- watch_once
    must read this as "no status yet" and let the caller keep polling, not
    raise."""
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "events.jsonl").write_text("", encoding="utf-8")

    seen_index, problems, status, confirmed = run_seat.watch_once(run_dir, tmp_path, tmp_path / "policy.yaml", 0, {}, print)
    assert status is None
    assert confirmed is False
    assert problems == []
    assert seen_index == 0


# --- _terminal_status_confirmed ---------------------------------------------


def test_terminal_status_confirmed_requires_the_matching_closing_event_kind() -> None:
    assert run_seat._terminal_status_confirmed([{"kind": "accept"}, {"kind": "complete"}], "complete") is True
    assert run_seat._terminal_status_confirmed([{"kind": "accept"}], "complete") is False
    assert run_seat._terminal_status_confirmed([{"kind": "floor"}, {"kind": "stop"}], "stopped") is True
    assert run_seat._terminal_status_confirmed([{"kind": "floor"}], "stopped") is False


def test_terminal_status_confirmed_false_for_a_non_terminal_or_missing_status() -> None:
    assert run_seat._terminal_status_confirmed([{"kind": "complete"}], "active") is False
    assert run_seat._terminal_status_confirmed([{"kind": "complete"}], None) is False
    assert run_seat._terminal_status_confirmed([], "complete") is False


def test_terminal_status_confirmed_skips_past_a_trailing_unrelated_event() -> None:
    """Regression test for a P2 defect an independent (third-round) codex
    review found: PM permits event-producing commands with no
    terminal-status guard (e.g. `approve()`) to be appended AFTER a run's
    own closing event. A bare "is the log's last entry the closing kind"
    check would then never confirm again, and this driver would poll
    forever despite the real closing event already being on record. The fix
    looks at the most recent event that is itself a run/slice-state
    transition (_RELEVANT_FOR_TERMINAL_CONFIRMATION), skipping anything
    else."""
    events = [{"kind": "accept"}, {"kind": "complete"}, {"kind": "approve"}]
    assert run_seat._terminal_status_confirmed(events, "complete") is True


def test_terminal_status_confirmed_still_false_when_the_last_relevant_event_does_not_match() -> None:
    """A trailing irrelevant event must not mask a genuinely unconfirmed
    status either -- only skipping past it, never treating its mere
    presence as confirmation."""
    events = [{"kind": "floor"}, {"kind": "approve"}]
    assert run_seat._terminal_status_confirmed(events, "complete") is False


# --- _retry_pending_grades ---------------------------------------------------


def test_retry_pending_grades_succeeds_and_clears_the_entry(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls = []
    monkeypatch.setattr(
        run_seat,
        "dispatch_grade",
        lambda run_dir, slice_number, attempt, policy_path, commit=None: calls.append((slice_number, attempt)),
    )
    pending: dict[tuple[str, int], None] = {("Slice 1", 0): None}
    events = [{"kind": "launch", "slice": "Slice 1", "note": "attempt 0"}]
    problems = run_seat._retry_pending_grades(pending, events, tmp_path, _NO_ACTIVE_SLICE_STATE, tmp_path / "policy.yaml", print)
    assert calls == [(1, 0)]
    assert problems == []
    assert pending == {}


def test_retry_pending_grades_gives_up_after_the_one_retry_fails_again(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Exactly one retry -- a second failure is a final, logged loss, not
    another queued attempt (module docstring: an expensive dev_check.py
    call is not retried unconditionally forever the way cheap review
    harvesting is)."""

    def always_fails(run_dir: Path, slice_number: int, attempt: int, policy_path: Path, commit: str | None = None) -> None:
        raise dev_check.DevCheckError("still broken")

    monkeypatch.setattr(run_seat, "dispatch_grade", always_fails)
    pending: dict[tuple[str, int], None] = {("Slice 1", 0): None}
    events = [{"kind": "launch", "slice": "Slice 1", "note": "attempt 0"}]
    logged = []
    problems = run_seat._retry_pending_grades(pending, events, tmp_path, _NO_ACTIVE_SLICE_STATE, tmp_path / "policy.yaml", logged.append)
    assert len(problems) == 1
    assert "giving up" in problems[0]
    assert pending == {}


def test_retry_pending_grades_abandons_an_entry_superseded_by_a_newer_attempt(tmp_path: Path) -> None:
    """If a newer attempt has appeared for the same slice before the retry
    runs, the pending entry is abandoned (its historical commit is now just
    as unrecoverable as any other superseded attempt's), not retried."""
    pending: dict[tuple[str, int], None] = {("Slice 1", 0): None}
    events = [
        {"kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
        {"kind": "relaunch", "slice": "Slice 1", "note": "attempt 1"},
    ]
    problems = run_seat._retry_pending_grades(pending, events, tmp_path, _NO_ACTIVE_SLICE_STATE, tmp_path / "policy.yaml", print)
    assert len(problems) == 1
    assert "abandoning" in problems[0]
    assert pending == {}


def test_process_new_events_queues_a_pending_retry_on_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def always_fails(run_dir: Path, slice_number: int, attempt: int, policy_path: Path, commit: str | None = None) -> None:
        raise dev_check.DevCheckError("boom")

    monkeypatch.setattr(run_seat, "dispatch_grade", always_fails)
    pending: dict[tuple[str, int], None] = {}
    events = [
        {"kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
        {"kind": "floor", "slice": "Slice 1", "note": "6/7"},
    ]
    run_seat.process_new_events(events, 0, tmp_path, _NO_ACTIVE_SLICE_STATE, tmp_path / "policy.yaml", pending, print)
    assert pending == {("Slice 1", 0): None}


# --- watch: the polling loop, with sleep faked out -----------------------


def test_watch_waits_for_the_closing_event_no_matter_how_many_polls_it_takes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Regression test for a P1 defect an independent codex review found in
    the first fix round's own repair: requiring the SAME status on two
    consecutive polls is a fixed one-poll delay, not real synchronization --
    it does not survive PM being slow, descheduled, or crashed for LONGER
    than one poll interval right after saving a terminal status but before
    appending its closing event. This asserts the loop keeps polling for
    several iterations with status="complete" but no "complete" event yet,
    and only stops once that event actually lands -- proving it is not a
    fixed-count heuristic."""
    run_dir = tmp_path / "run"
    _write_events_jsonl(run_dir, [{"kind": "launch", "slice": "Slice 1", "note": "attempt 0"}])
    _write_run_json(run_dir, "active")
    monkeypatch.setattr(run_seat, "dispatch_grade", lambda *args, **kwargs: None)
    monkeypatch.setattr(run_seat, "dispatch_review_harvest", lambda *args, **kwargs: None)

    sleep_calls = []

    def fake_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)
        if len(sleep_calls) == 1:
            _write_run_json(run_dir, "complete")  # status saved...
        elif len(sleep_calls) == 4:
            _append_event(run_dir, {"kind": "complete", "slice": None, "note": "all slices accepted"})
        # ...but the closing event only lands on the 4th sleep -- three
        # extra polls beyond a fixed one-poll debounce.

    logged = []
    rc = run_seat.watch(run_dir, tmp_path, tmp_path / "policy.yaml", 15, log=logged.append, sleep=fake_sleep)
    assert rc == 0
    # sleep is called once per poll that does NOT confirm termination: polls
    # 1-4 all sleep (poll 4's sleep is what finally appends the closing
    # event); poll 5 then sees it and breaks without sleeping again.
    assert len(sleep_calls) == 4
    assert any("closing event has not appeared" in message for message in logged)
    assert any("Tool 4" in message and "Tool 5" in message for message in logged)


def test_watch_stops_on_stopped_status_once_its_own_stop_event_lands(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    run_dir = tmp_path / "run"
    _write_events_jsonl(run_dir, [{"kind": "launch", "slice": "Slice 1", "note": "attempt 0"}])
    _write_run_json(run_dir, "active")
    monkeypatch.setattr(run_seat, "dispatch_grade", lambda *args, **kwargs: None)
    monkeypatch.setattr(run_seat, "dispatch_review_harvest", lambda *args, **kwargs: None)

    def fake_sleep(seconds: float) -> None:
        _write_run_json(run_dir, "stopped")
        _append_event(run_dir, {"kind": "stop", "slice": None, "note": "operator stopped the run"})

    rc = run_seat.watch(run_dir, tmp_path, tmp_path / "policy.yaml", 1, log=print, sleep=fake_sleep)
    assert rc == 0


def test_watch_does_not_stop_on_needs_human_keeps_polling_until_complete(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """`needs-human` is a deliberate, documented non-terminal pause (attempt-
    budget exhaustion or a PM-initiated slice stop) -- only `complete` and
    `stopped` are terminal. The loop must keep polling through a
    needs-human status rather than treating it as the run's end."""
    run_dir = tmp_path / "run"
    _write_events_jsonl(run_dir, [{"kind": "launch", "slice": "Slice 1", "note": "attempt 0"}])
    _write_run_json(run_dir, "needs-human")
    monkeypatch.setattr(run_seat, "dispatch_grade", lambda *args, **kwargs: None)
    monkeypatch.setattr(run_seat, "dispatch_review_harvest", lambda *args, **kwargs: None)

    sleep_calls = []

    def fake_sleep(seconds: float) -> None:
        sleep_calls.append(seconds)
        if len(sleep_calls) < 3:
            _write_run_json(run_dir, "needs-human")
        else:
            _write_run_json(run_dir, "complete")
            _append_event(run_dir, {"kind": "complete", "slice": None, "note": "all slices accepted"})

    rc = run_seat.watch(run_dir, tmp_path, tmp_path / "policy.yaml", 1, log=print, sleep=fake_sleep)
    assert rc == 0
    assert len(sleep_calls) == 3


def test_watch_returns_1_when_a_dispatch_problem_occurred(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The exit code is a summary, not a claim nothing was recorded (module
    docstring on watch()'s Returns) -- a grading failure surfaces as rc=1
    even though the run itself reaches a clean, confirmed terminal status."""
    run_dir = tmp_path / "run"
    _write_events_jsonl(
        run_dir,
        [
            {"kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
            {"kind": "floor", "slice": "Slice 1", "note": "6/7"},
        ],
    )
    _write_run_json(run_dir, "active")

    def failing_dispatch_grade(run_dir_arg: Path, slice_number: int, attempt: int, policy_path: Path, commit=None) -> None:
        raise dev_check.DevCheckError("boom")

    monkeypatch.setattr(run_seat, "dispatch_grade", failing_dispatch_grade)
    monkeypatch.setattr(run_seat, "dispatch_review_harvest", lambda *args, **kwargs: None)

    def fake_sleep(seconds: float) -> None:
        _write_run_json(run_dir, "complete")
        _append_event(run_dir, {"kind": "complete", "slice": None, "note": "all slices accepted"})

    rc = run_seat.watch(run_dir, tmp_path, tmp_path / "policy.yaml", 1, log=print, sleep=fake_sleep)
    assert rc == 1


def test_watch_gives_a_pending_retry_one_more_poll_even_after_terminal_status_is_confirmed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Regression test for a bug caught while adding the bounded retry: if a
    grade fails on the very same poll where the run's terminal status is
    ALSO already confirmed (PM's finalize_accept can append `floor`,
    `accept` and `complete` all before this driver ever polls), the loop
    must not stop immediately -- that would mean a queued retry never gets
    its one chance to run at all. watch() must give it one more poll first."""
    run_dir = tmp_path / "run"
    _write_events_jsonl(
        run_dir,
        [
            {"kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
            {"kind": "floor", "slice": "Slice 1", "note": "6/7"},
        ],
    )
    # The closing "complete" event is ALREADY on record before this driver
    # ever polls -- confirmed=True from the very first watch_once() call.
    _append_event(run_dir, {"kind": "complete", "slice": None, "note": "all slices accepted"})
    _write_run_json(run_dir, "complete")

    call_count = []

    def fails_once_then_succeeds(run_dir_arg: Path, slice_number: int, attempt: int, policy_path: Path, commit=None) -> None:
        call_count.append(1)
        if len(call_count) == 1:
            raise dev_check.DevCheckError("transient")

    monkeypatch.setattr(run_seat, "dispatch_grade", fails_once_then_succeeds)
    monkeypatch.setattr(run_seat, "dispatch_review_harvest", lambda *args, **kwargs: None)

    sleep_calls = []
    logged = []
    rc = run_seat.watch(
        run_dir, tmp_path, tmp_path / "policy.yaml", 1, log=logged.append, sleep=sleep_calls.append
    )
    assert len(call_count) == 2  # the original attempt, plus its one retry
    assert len(sleep_calls) == 1  # did not stop on the first poll despite confirmed status
    assert any("grading retry" in message and "pending" in message for message in logged)
    assert rc == 1  # the original failure is still reported, even though the retry recovered


# --- load_policy -----------------------------------------------------------


def test_load_policy_missing_driver_poll_interval_seconds_fails_loudly(tmp_path: Path) -> None:
    policy_path = _valid_policy_yaml(tmp_path, driver_poll_interval_seconds=None)
    with pytest.raises(run_seat.RunSeatError, match="driver_poll_interval_seconds"):
        run_seat.load_policy(policy_path)


@pytest.mark.parametrize("bad_value", [0, -5, True, False])
def test_load_policy_rejects_non_positive_or_bool_poll_interval(tmp_path: Path, bad_value: object) -> None:
    """Python bools are ints (isinstance(True, int) is True) -- the sibling
    tools' own subprocess_timeout_seconds check already guards against a
    bool sneaking through a bare positive-number check, and this driver's
    own driver_poll_interval_seconds check must guard the same way."""
    policy_path = _valid_policy_yaml(tmp_path, driver_poll_interval_seconds=bad_value)
    with pytest.raises(run_seat.RunSeatError, match="driver_poll_interval_seconds"):
        run_seat.load_policy(policy_path)


def test_load_policy_valid_policy_returns_the_parsed_dict(tmp_path: Path) -> None:
    policy_path = _valid_policy_yaml(tmp_path)
    policy = run_seat.load_policy(policy_path)
    assert policy["driver_poll_interval_seconds"] == 15
    assert policy["backend"] == "local"


def test_load_policy_wraps_dev_checks_backend_validation_as_run_seat_error(tmp_path: Path) -> None:
    """load_policy delegates required-key/backend validation to
    dev_check.load_policy, but main()'s __main__ block only catches
    RunSeatError -- if a raw dev_check.DevCheckError escaped here it would
    crash the driver with an unfamiliar exception type instead of a clean,
    caught error message."""
    policy_path = tmp_path / "policy.yaml"
    policy_path.write_text("backend: sbx\ndriver_poll_interval_seconds: 15\n", encoding="utf-8")
    with pytest.raises(run_seat.RunSeatError, match="not implemented"):
        run_seat.load_policy(policy_path)


def test_load_policy_wraps_dev_checks_missing_key_validation_as_run_seat_error(tmp_path: Path) -> None:
    policy_path = _valid_policy_yaml(tmp_path, pm_scripts_dir=None)
    with pytest.raises(run_seat.RunSeatError, match="pm_scripts_dir"):
        run_seat.load_policy(policy_path)


# --- main() / parse_args ---------------------------------------------------


def test_main_rejects_a_run_dir_with_neither_state_file_before_watch_is_reached(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """main() must check --run-dir for a real PM run directory before ever
    calling watch() -- verified here by making watch() itself fail the test
    if it is ever invoked, not merely by checking the error message."""
    empty_run_dir = tmp_path / "not-a-run-dir"
    empty_run_dir.mkdir()

    def fail_if_called(*args: object, **kwargs: object) -> int:
        pytest.fail("watch() must not be called when --run-dir is not a real PM run directory")

    monkeypatch.setattr(run_seat, "watch", fail_if_called)
    argv = ["--run-dir", str(empty_run_dir), "--policy", str(REPO_ROOT / "policy.yaml")]
    with pytest.raises(run_seat.RunSeatError, match="neither run.json nor events.jsonl"):
        run_seat.main(argv)


def test_parse_args_requires_run_dir() -> None:
    with pytest.raises(SystemExit):
        run_seat.parse_args([])
