"""Tests for tools/grade_run.py (grades one FINISHED PM run in a single pass).

Run with plain pytest from the repo root: `pytest tests/test_grade_run.py`.
These tests use synthetic fixtures only (a hand-written run.json/events.jsonl
under tmp_path) and monkeypatch every point where grade_run.py would
otherwise call into dev_check.py/review_score.py's own subprocess-invoking
internals -- they never invoke a real subprocess, a real git worktree, or the
real project-manager toolkit, matching test_dev_check.py's own stated
approach.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import dev_check  # noqa: E402
import grade_run  # noqa: E402
import review_score  # noqa: E402

REAL_POLICY_PATH = REPO_ROOT / "policy.yaml"


# --- helpers -----------------------------------------------------------


def _write_run_dir(tmp_path: Path, run_state: dict[str, Any], events: list[dict[str, Any]]) -> Path:
    run_dir = tmp_path / "pm-run"
    run_dir.mkdir()
    (run_dir / "run.json").write_text(json.dumps(run_state), encoding="utf-8")
    (run_dir / "events.jsonl").write_text(
        "\n".join(json.dumps(e) for e in events) + ("\n" if events else ""), encoding="utf-8"
    )
    return run_dir


# --- parse_slice_number --------------------------------------------------


class TestParseSliceNumber:
    def test_well_formed_slice_id_extracts_the_number(self) -> None:
        assert grade_run.parse_slice_number("Slice 1") == 1
        assert grade_run.parse_slice_number("Slice 12") == 12

    def test_non_matching_string_is_none(self) -> None:
        assert grade_run.parse_slice_number("slice 1") is None
        assert grade_run.parse_slice_number("Slice one") is None
        assert grade_run.parse_slice_number("") is None


# --- review_skill_for_note ------------------------------------------------


class TestReviewSkillForNote:
    def test_matches_each_real_skill_by_its_note_prefix(self) -> None:
        # Confirm against the real review_score.REVIEW_SKILLS rather than
        # hardcoding a name this module might drift away from.
        assert "drift-audit" in review_score.REVIEW_SKILLS
        assert "code-review" in review_score.REVIEW_SKILLS
        assert grade_run.review_skill_for_note("drift-audit via opencode") == "drift-audit"
        assert grade_run.review_skill_for_note("code-review via claude") == "code-review"

    def test_note_matching_neither_prefix_is_none(self) -> None:
        assert grade_run.review_skill_for_note("some-other-skill via claude") is None
        assert grade_run.review_skill_for_note("") is None


# --- _terminal_status_confirmed -------------------------------------------


class TestTerminalStatusConfirmed:
    def test_complete_status_confirmed_by_a_complete_event_anywhere(self) -> None:
        events = [
            {"kind": "launch", "slice": "Slice 1"},
            {"kind": "complete"},
            {"kind": "floor", "slice": "Slice 1"},
        ]
        assert grade_run._terminal_status_confirmed(events, "complete") is True

    def test_a_trailing_stop_after_complete_does_not_mask_the_earlier_complete(self) -> None:
        # This is the exact real bug fixed in this module: the retired
        # run_seat.py used a "most recent tracked event" check, and an
        # ordinary trailing top-level `stop` issued after a run had already
        # reached `complete` became the "most recent relevant event",
        # permanently masking the earlier, real `complete` event and
        # polling forever (confirmed against a real run, 2026-09-11).
        # _terminal_status_confirmed checks existence anywhere in the log,
        # not recency, so it must not regress into the same bug.
        events = [
            {"kind": "launch", "slice": "Slice 1"},
            {"kind": "complete"},
            {"kind": "stop", "slice": None},  # unrelated trailing event, AFTER complete
        ]
        assert grade_run._terminal_status_confirmed(events, "complete") is True

    def test_stopped_status_confirmed_by_a_stop_event_anywhere(self) -> None:
        events = [{"kind": "launch", "slice": "Slice 1"}, {"kind": "stop", "slice": None}]
        assert grade_run._terminal_status_confirmed(events, "stopped") is True

    def test_non_terminal_statuses_are_always_false_regardless_of_events(self) -> None:
        events = [{"kind": "complete"}, {"kind": "stop", "slice": None}]
        assert grade_run._terminal_status_confirmed(events, "needs-human") is False
        assert grade_run._terminal_status_confirmed(events, "active") is False
        assert grade_run._terminal_status_confirmed(events, None) is False

    def test_empty_events_with_complete_status_is_false(self) -> None:
        assert grade_run._terminal_status_confirmed([], "complete") is False


# --- _resolve_grading_commit ----------------------------------------------


class TestResolveGradingCommit:
    def test_accepted_slice_with_a_recorded_commit(self) -> None:
        run_state = {"slices": [{"id": "Slice 1", "status": "accepted", "commit": "abc123"}]}
        assert grade_run._resolve_grading_commit(run_state, "Slice 1") == ("abc123", None)

    def test_accepted_slice_with_no_commit_is_a_named_problem(self) -> None:
        run_state = {"slices": [{"id": "Slice 1", "status": "accepted", "commit": None}]}
        commit, problem = grade_run._resolve_grading_commit(run_state, "Slice 1")
        assert commit is None
        assert problem is not None
        assert "malformed" in problem

    def test_accepted_slice_with_missing_commit_key_is_a_named_problem(self) -> None:
        run_state = {"slices": [{"id": "Slice 1", "status": "accepted"}]}
        commit, problem = grade_run._resolve_grading_commit(run_state, "Slice 1")
        assert commit is None
        assert problem is not None
        assert "malformed" in problem

    def test_slice_not_present_at_all_is_a_named_problem(self) -> None:
        # 2026-09-11: a non-accepted slice is now always refused, never
        # silently defaulted to the repo's current HEAD -- an independent
        # review found that default unsafe (a top-level `pm stop` can end
        # an in-progress attempt with no commit recorded and no guarantee
        # HEAD hasn't moved by grading time).
        run_state = {"slices": [{"id": "Slice 2", "status": "accepted", "commit": "xyz"}]}
        commit, problem = grade_run._resolve_grading_commit(run_state, "Slice 1")
        assert commit is None
        assert problem is not None and "Slice 1" in problem

    def test_slice_present_but_not_accepted_is_a_named_problem(self) -> None:
        run_state = {"slices": [{"id": "Slice 1", "status": "active", "commit": "abc123"}]}
        commit, problem = grade_run._resolve_grading_commit(run_state, "Slice 1")
        assert commit is None
        assert problem is not None and "not recorded accepted" in problem


# --- gradeable_slice_targets ------------------------------------------------


class TestGradeableSliceTargets:
    def test_two_slices_resolve_their_own_final_attempt_ordinal(self) -> None:
        run_state = {"slices": [{"id": "Slice 1"}, {"id": "Slice 2"}]}
        events = [
            {"kind": "launch", "slice": "Slice 1"},
            {"kind": "steer", "slice": "Slice 1"},  # Slice 1: 2 launch-family events -> ordinal 1
            {"kind": "launch", "slice": "Slice 2"},  # Slice 2: 1 launch-family event -> ordinal 0
        ]
        assert grade_run.gradeable_slice_targets(run_state, events) == [
            (1, "Slice 1", 1),
            (2, "Slice 2", 0),
        ]

    def test_a_slice_never_launched_is_silently_excluded(self) -> None:
        # A slice the plan defines but PM never reached before the run
        # ended -- zero launch-family events is a normal shape, not an
        # error, so it must not appear in the result at all.
        run_state = {"slices": [{"id": "Slice 1"}, {"id": "Slice 2"}]}
        events = [{"kind": "launch", "slice": "Slice 1"}]
        assert grade_run.gradeable_slice_targets(run_state, events) == [(1, "Slice 1", 0)]


# --- known_review_targets ---------------------------------------------------


class TestKnownReviewTargets:
    def test_a_review_event_with_evidence_is_a_known_target(self) -> None:
        events = [
            {
                "kind": "review",
                "slice": "Slice 1",
                "note": "drift-audit via opencode",
                "evidence": "/tmp/report.md",
            }
        ]
        assert (1, "drift-audit") in grade_run.known_review_targets(events)

    def test_a_review_event_with_no_evidence_is_excluded(self) -> None:
        # Mirrors review_score.find_review_events's own discriminator: PM's
        # reviewer-timeout path appends a review event with the same note
        # prefix and no evidence at all -- that must never be harvested.
        events = [
            {"kind": "review", "slice": "Slice 1", "note": "drift-audit via opencode", "evidence": None},
            {"kind": "review", "slice": "Slice 1", "note": "drift-audit via opencode timed out after 60s"},
        ]
        assert grade_run.known_review_targets(events) == set()

    def test_duplicate_slice_skill_pairs_collapse_to_one_set_entry(self) -> None:
        events = [
            {"kind": "review", "slice": "Slice 1", "note": "drift-audit via opencode", "evidence": "/a.md"},
            {"kind": "review", "slice": "Slice 1", "note": "drift-audit via claude", "evidence": "/b.md"},
        ]
        targets = grade_run.known_review_targets(events)
        assert targets == {(1, "drift-audit")}


# --- dispatch_grade ---------------------------------------------------------


class TestDispatchGrade:
    def test_commit_is_appended_only_when_not_none(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        captured: dict[str, list[str]] = {}

        def fake_main(argv: list[str]) -> int:
            captured["argv"] = argv
            return 0

        monkeypatch.setattr(dev_check, "main", fake_main)
        run_dir = tmp_path / "run"
        policy_path = tmp_path / "policy.yaml"

        grade_run.dispatch_grade(run_dir, 1, 0, policy_path, commit="deadbeef")
        assert captured["argv"] == [
            "--run-dir", str(run_dir),
            "--slice", "1",
            "--attempt", "0",
            "--policy", str(policy_path),
            "--commit", "deadbeef",
        ]

    def test_no_commit_flag_when_commit_is_none(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        captured: dict[str, list[str]] = {}

        def fake_main(argv: list[str]) -> int:
            captured["argv"] = argv
            return 0

        monkeypatch.setattr(dev_check, "main", fake_main)
        run_dir = tmp_path / "run"
        policy_path = tmp_path / "policy.yaml"

        grade_run.dispatch_grade(run_dir, 2, 3, policy_path, commit=None)
        assert captured["argv"] == [
            "--run-dir", str(run_dir),
            "--slice", "2",
            "--attempt", "3",
            "--policy", str(policy_path),
        ]
        assert "--commit" not in captured["argv"]


# --- dispatch_review_harvest -------------------------------------------------


class TestDispatchReviewHarvest:
    def test_calls_run_review_score_with_the_resolved_sheet_path(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        captured: dict[str, tuple] = {}
        run_dir = tmp_path / "run"
        root = tmp_path / "root"
        sheet_path = tmp_path / "sheet.json"

        monkeypatch.setattr(review_score, "read_json", lambda path: {"run_id": "run-1"})
        monkeypatch.setattr(
            review_score, "default_sheet_path", lambda root_, run_id, slice_num: sheet_path
        )

        def fake_run_review_score(run_dir_, slice_num, skill, sheet_path_) -> None:
            captured["args"] = (run_dir_, slice_num, skill, sheet_path_)

        monkeypatch.setattr(review_score, "run_review_score", fake_run_review_score)

        grade_run.dispatch_review_harvest(run_dir, 1, "drift-audit", root)
        assert captured["args"] == (run_dir, 1, "drift-audit", sheet_path)

    def test_missing_run_id_raises_review_score_error(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        monkeypatch.setattr(review_score, "read_json", lambda path: {})
        with pytest.raises(review_score.ReviewScoreError, match="run_id"):
            grade_run.dispatch_review_harvest(tmp_path / "run", 1, "drift-audit", tmp_path / "root")


# --- grade_finished_run (orchestration) --------------------------------------


class TestGradeFinishedRun:
    def _run_state_with_one_slice(self) -> dict[str, Any]:
        return {
            "run_id": "run-1",
            "status": "complete",
            "slices": [{"id": "Slice 1", "status": "accepted", "commit": "deadbeef"}],
        }

    def _events_with_one_attempt_and_one_review(self) -> list[dict[str, Any]]:
        return [
            {"kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
            {
                "kind": "review",
                "slice": "Slice 1",
                "note": "drift-audit via opencode",
                "evidence": "/tmp/report.md",
            },
        ]

    def test_grading_runs_before_review_harvesting(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        run_state = self._run_state_with_one_slice()
        events = self._events_with_one_attempt_and_one_review()
        run_dir = _write_run_dir(tmp_path, run_state, events)
        call_order: list[str] = []

        def fake_dispatch_grade(run_dir_, slice_number, attempt, policy_path, commit=None) -> None:
            call_order.append(f"grade:{slice_number}:{attempt}")

        def fake_dispatch_review_harvest(run_dir_, slice_number, skill, root) -> list[str]:
            call_order.append(f"harvest:{slice_number}:{skill}")
            return []

        monkeypatch.setattr(grade_run, "dispatch_grade", fake_dispatch_grade)
        monkeypatch.setattr(grade_run, "dispatch_review_harvest", fake_dispatch_review_harvest)

        problems = grade_run.grade_finished_run(run_dir, tmp_path / "root", tmp_path / "policy.yaml", run_state, events)
        assert problems == []
        assert call_order == ["grade:1:0", "harvest:1:drift-audit"]

    def test_a_grading_failure_is_caught_and_does_not_block_harvesting(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        run_state = self._run_state_with_one_slice()
        events = self._events_with_one_attempt_and_one_review()
        run_dir = _write_run_dir(tmp_path, run_state, events)
        harvest_calls: list[str] = []

        def failing_dispatch_grade(run_dir_, slice_number, attempt, policy_path, commit=None) -> None:
            raise dev_check.DevCheckError("boom")

        def fake_dispatch_review_harvest(run_dir_, slice_number, skill, root) -> list[str]:
            harvest_calls.append(f"{slice_number}:{skill}")
            return []

        monkeypatch.setattr(grade_run, "dispatch_grade", failing_dispatch_grade)
        monkeypatch.setattr(grade_run, "dispatch_review_harvest", fake_dispatch_review_harvest)

        problems = grade_run.grade_finished_run(run_dir, tmp_path / "root", tmp_path / "policy.yaml", run_state, events)
        assert len(problems) == 1
        assert "slice 1" in problems[0] and "attempt 0" in problems[0]
        # Grading one slice's failure must not block review harvesting for
        # the run -- harvesting for the known review target still happened.
        assert harvest_calls == ["1:drift-audit"]

    def test_a_harvest_failure_is_caught_and_recorded(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        run_state = self._run_state_with_one_slice()
        events = self._events_with_one_attempt_and_one_review()
        run_dir = _write_run_dir(tmp_path, run_state, events)

        def fake_dispatch_grade(run_dir_, slice_number, attempt, policy_path, commit=None) -> None:
            pass

        def failing_dispatch_review_harvest(run_dir_, slice_number, skill, root) -> list[str]:
            raise review_score.ReviewScoreError("boom2")

        monkeypatch.setattr(grade_run, "dispatch_grade", fake_dispatch_grade)
        monkeypatch.setattr(grade_run, "dispatch_review_harvest", failing_dispatch_review_harvest)

        problems = grade_run.grade_finished_run(run_dir, tmp_path / "root", tmp_path / "policy.yaml", run_state, events)
        assert len(problems) == 1
        assert "slice 1" in problems[0]
        assert "drift-audit" in problems[0]

    def test_a_review_score_reported_problem_is_included_without_being_an_exception(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # 2026-09-11: run_review_score() now RETURNS per-attempt problems
        # (a missing sheet row for a superseded attempt) rather than always
        # raising -- this must surface in grade_finished_run's own problems
        # list, not be silently dropped.
        run_state = self._run_state_with_one_slice()
        events = self._events_with_one_attempt_and_one_review()
        run_dir = _write_run_dir(tmp_path, run_state, events)

        monkeypatch.setattr(grade_run, "dispatch_grade", lambda *a, **k: None)
        monkeypatch.setattr(
            grade_run, "dispatch_review_harvest", lambda *a, **k: ["slice 1 attempt 0: no scoring-sheet row"]
        )

        problems = grade_run.grade_finished_run(run_dir, tmp_path / "root", tmp_path / "policy.yaml", run_state, events)
        assert problems == ["slice 1 attempt 0: no scoring-sheet row"]

    def test_no_failures_returns_an_empty_list(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        run_state = self._run_state_with_one_slice()
        events = self._events_with_one_attempt_and_one_review()
        run_dir = _write_run_dir(tmp_path, run_state, events)
        monkeypatch.setattr(grade_run, "dispatch_grade", lambda *a, **k: None)
        monkeypatch.setattr(grade_run, "dispatch_review_harvest", lambda *a, **k: [])

        problems = grade_run.grade_finished_run(run_dir, tmp_path / "root", tmp_path / "policy.yaml", run_state, events)
        assert problems == []


# --- main() end-to-end -------------------------------------------------------


class TestMain:
    def _run_state_with_one_slice(self, status: str) -> dict[str, Any]:
        return {
            "run_id": "run-1",
            "status": status,
            "slices": [{"id": "Slice 1", "status": "accepted", "commit": "deadbeef"}],
        }

    def _events_with_complete(self) -> list[dict[str, Any]]:
        return [
            {"kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
            {
                "kind": "review",
                "slice": "Slice 1",
                "note": "drift-audit via opencode",
                "evidence": "/tmp/report.md",
            },
            {"kind": "complete"},
        ]

    def _stub_dispatch(self, monkeypatch: pytest.MonkeyPatch, *, grade_raises: bool = False) -> None:
        def fake_dispatch_grade(run_dir_, slice_number, attempt, policy_path, commit=None) -> None:
            if grade_raises:
                raise dev_check.DevCheckError("boom")

        monkeypatch.setattr(grade_run, "dispatch_grade", fake_dispatch_grade)
        monkeypatch.setattr(grade_run, "dispatch_review_harvest", lambda *a, **k: [])

    def test_non_terminal_status_active_refuses_to_grade(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        run_dir = _write_run_dir(
            tmp_path, self._run_state_with_one_slice("active"), [{"kind": "launch", "slice": "Slice 1"}]
        )
        self._stub_dispatch(monkeypatch)
        with pytest.raises(grade_run.GradeRunError, match="not a confirmed-finished run"):
            grade_run.main(["--run-dir", str(run_dir), "--policy", str(REAL_POLICY_PATH)])

    def test_needs_human_status_is_a_pause_not_a_finish(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        run_dir = _write_run_dir(
            tmp_path, self._run_state_with_one_slice("needs-human"), [{"kind": "launch", "slice": "Slice 1"}]
        )
        self._stub_dispatch(monkeypatch)
        with pytest.raises(grade_run.GradeRunError, match="not a confirmed-finished run"):
            grade_run.main(["--run-dir", str(run_dir), "--policy", str(REAL_POLICY_PATH)])

    def test_complete_status_without_a_complete_event_is_refused(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # status alone isn't enough -- PM's own closing event must be on
        # record too.
        run_dir = _write_run_dir(
            tmp_path, self._run_state_with_one_slice("complete"), [{"kind": "launch", "slice": "Slice 1"}]
        )
        self._stub_dispatch(monkeypatch)
        with pytest.raises(grade_run.GradeRunError, match="not a confirmed-finished run"):
            grade_run.main(["--run-dir", str(run_dir), "--policy", str(REAL_POLICY_PATH)])

    def test_confirmed_complete_run_with_successful_grading_returns_0(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        run_dir = _write_run_dir(tmp_path, self._run_state_with_one_slice("complete"), self._events_with_complete())
        self._stub_dispatch(monkeypatch)
        rc = grade_run.main(["--run-dir", str(run_dir), "--policy", str(REAL_POLICY_PATH)])
        assert rc == 0

    def test_a_grading_failure_yields_exit_code_1_not_an_exception(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        # Matches the module's own documented contract: "if grading fails
        # here, it fails loudly once and this module exits nonzero" -- a
        # partial-failure exit code, not a raised exception.
        run_dir = _write_run_dir(tmp_path, self._run_state_with_one_slice("complete"), self._events_with_complete())
        self._stub_dispatch(monkeypatch, grade_raises=True)
        rc = grade_run.main(["--run-dir", str(run_dir), "--policy", str(REAL_POLICY_PATH)])
        assert rc == 1

    def test_run_dir_with_neither_file_is_refused_by_name(self, tmp_path: Path) -> None:
        empty_dir = tmp_path / "not-a-run-dir"
        empty_dir.mkdir()
        with pytest.raises(grade_run.GradeRunError, match=str(empty_dir)):
            grade_run.main(["--run-dir", str(empty_dir), "--policy", str(REAL_POLICY_PATH)])
