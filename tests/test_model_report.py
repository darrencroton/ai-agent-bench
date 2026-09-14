"""Tests for tools/model_report.py (Tool 4: one model's full run, reshaped).

Fixtures are hand-written scoring sheets under `tmp_path`, matching the real
shape `dev_check.py`/`review_score.py` write (docs/MODE2-REWRITE-PLAN.md §7).
No git, no subprocess: this tool only reads already-graded JSON/Markdown
already on disk.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import model_report as mr  # noqa: E402


def _review_record(
    *,
    skill: str = "drift-audit",
    tool: str = "opencode",
    model: str = "github-copilot/gpt-5.6-luna",
    head: str = "deadbeef",
    at: str = "2026-09-12T11:21:03Z",
    verdict: str | None = "PASS",
    findings_by_severity: dict[str, int] | None = None,
    open_after_this_attempt: int | None = None,
    parse_error: str | None = None,
) -> dict[str, Any]:
    """A drift_review/code_review record shaped like review_score.py's real
    `build_record` output (tools/review_score.py) -- including the fields
    it already carries (`skill`/`tool`/`model`/`head`/`at`/`report_ref`/
    `report_sha256`) that model_report.py's old `_review_trend_entry` used
    to silently drop (docs/LEADERBOARD-REBUILD-PLAN.md Stage 2). Deliberately
    has no `review_id`/`effort` key at all -- review_score.py does not
    harvest those onto the record yet (Stage 4's job); `_review_trend_entry`
    must read them as None, not KeyError, until then.
    """
    record: dict[str, Any] = {
        "commissioned": True,
        "report_ref": f"/fake/{skill}.md",
        "report_sha256": "abc123",
        "skill": skill,
        "tool": tool,
        "model": model,
        "head": head,
        "grants_seen": 0,
        "at": at,
    }
    if parse_error is not None:
        record["parse_error"] = parse_error
        return record
    record["verdict"] = verdict
    record["findings_by_severity"] = findings_by_severity if findings_by_severity is not None else {}
    record["open_after_this_attempt"] = open_after_this_attempt
    return record


def _attempt(
    attempt: int,
    *,
    pm_decision: str | None = "steer",
    pm_attempts_counter: int | None = None,
    drift_review: dict[str, Any] | None = None,
    code_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "attempt": attempt,
        "pm_attempts_counter": pm_attempts_counter if pm_attempts_counter is not None else attempt,
        "commit_sha": f"sha-{attempt}",
        "correctness": {"hidden_tests_passed": 40, "hidden_tests_total": 44},
        "quality": {"lint_findings_by_tool": {}, "code_health_findings_by_category": {}},
        "scope": {"violations": []},
        "pm_decision": pm_decision,
        "drift_review": drift_review,
        "code_review": code_review,
    }


def _developer(
    *,
    model: str = "opencode/some-model",
    harness: str = "opencode",
    effort: str | None = "low",
    attributed: bool = True,
) -> dict[str, Any]:
    """Stage 1's structured identity block (docs/LEADERBOARD-REBUILD-PLAN.md)
    -- what dev_check.py now writes onto a sheet in place of the flat
    `model` string this module's tests used to hand-write directly."""
    return {
        "harness": harness if attributed else None,
        "model": model if attributed else None,
        "effort": effort,
        "configuration_key": f"{model} · {harness} · {effort or 'effort unknown'}"
        if attributed
        else "model unknown · harness unknown · effort unknown",
        "sources": {"harness": "run_harness", "model": "run_harness", "effort": "run_harness"},
        "attributed": attributed,
        "attestation": None,
    }


def _sheet(
    run_id: str,
    slice_number: int,
    *,
    model: str = "opencode/some-model",
    developer: dict[str, Any] | None = None,
    pm_status: str = "complete",
    stop_reason: str | None = "done",
    attempts: list[dict[str, Any]] | None = None,
    accepted_at_attempt: int | None = 0,
    pm_model_performance_ref: str | None = None,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "developer": developer if developer is not None else _developer(model=model),
        "slice": slice_number,
        "run_status": {
            "pm_status": pm_status,
            "slice_status": "accepted" if accepted_at_attempt is not None else "stopped",
            "stop_reason": stop_reason,
            "infrastructure_failure_suspected": False,
        },
        "attempts": attempts if attempts is not None else [_attempt(0, pm_decision="accept")],
        "accepted_at_attempt": accepted_at_attempt,
        "pm_model_performance_ref": pm_model_performance_ref,
    }


def _write_sheet(sheets_dir: Path, slice_number: int, sheet: dict[str, Any]) -> Path:
    sheets_dir.mkdir(parents=True, exist_ok=True)
    path = sheets_dir / f"slice-{slice_number}.json"
    path.write_text(json.dumps(sheet), encoding="utf-8")
    return path


class TestDiscoverSheets:
    def test_no_sheets_directory_is_a_named_error(self, tmp_path: Path) -> None:
        with pytest.raises(mr.ModelReportError, match="no scoring sheets directory"):
            mr.discover_sheets(tmp_path / "missing", "run-1")

    def test_empty_sheets_directory_is_a_named_error(self, tmp_path: Path) -> None:
        (tmp_path / "empty").mkdir()
        with pytest.raises(mr.ModelReportError, match="no slice-<N>.json"):
            mr.discover_sheets(tmp_path / "empty", "run-1")

    def test_finds_and_sorts_every_slice_sheet(self, tmp_path: Path) -> None:
        _write_sheet(tmp_path, 2, _sheet("run-1", 2))
        _write_sheet(tmp_path, 1, _sheet("run-1", 1))
        found = mr.discover_sheets(tmp_path, "run-1")
        assert [n for n, _p, _s in found] == [1, 2]

    def test_sheet_identity_mismatch_is_a_named_error_not_a_raw_bench_lib_error(self, tmp_path: Path) -> None:
        _write_sheet(tmp_path, 1, _sheet("wrong-run-id", 1))
        with pytest.raises(mr.ModelReportError, match="wrong-run-id"):
            mr.discover_sheets(tmp_path, "run-1")

    def test_duplicate_parsed_slice_number_across_filenames_is_a_named_error(self, tmp_path: Path) -> None:
        _write_sheet(tmp_path, 1, _sheet("run-1", 1))
        (tmp_path / "slice-01.json").write_text(json.dumps(_sheet("run-1", 1)), encoding="utf-8")
        with pytest.raises(mr.ModelReportError, match="same slice number"):
            mr.discover_sheets(tmp_path, "run-1")


class TestBuildReport:
    def test_happy_path_aggregates_two_slices(self, tmp_path: Path) -> None:
        ref = tmp_path / "model-performance.md"
        ref.write_text("Developer (opencode):\nProcess discipline: 5/5 -- none.\n", encoding="utf-8")
        slice1_attempts = [
            _attempt(
                0,
                pm_decision="steer",
                drift_review=_review_record(verdict="FAIL", findings_by_severity={"P2": 1}, open_after_this_attempt=1, at="2026-09-12T11:21:03Z"),
            ),
            _attempt(
                1,
                pm_decision="accept",
                drift_review=_review_record(verdict="PASS", findings_by_severity={"P2": 0}, open_after_this_attempt=0, at="2026-09-12T11:22:51Z"),
            ),
        ]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=slice1_attempts, accepted_at_attempt=1, pm_model_performance_ref=str(ref)))
        _write_sheet(tmp_path, 2, _sheet("run-1", 2, accepted_at_attempt=0, pm_model_performance_ref=str(ref)))

        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, problems = mr.build_report(sheets, "run-1")

        assert problems == []
        assert report["run_id"] == "run-1"
        assert report["developer"]["model"] == "opencode/some-model"
        assert report["run_status"] == {"pm_status": "complete", "stop_reason": "done"}
        assert report["timing"] == {"available": False, "reason": "no --run-dir given; events.jsonl was not read"}
        assert [s["slice"] for s in report["slices"]] == [1, 2]

        slice1 = report["slices"][0]
        assert slice1["attempts_total"] == 2
        assert slice1["accepted_at_attempt"] == 1
        assert slice1["first_attempt"]["attempt"] == 0
        assert slice1["final_attempt"]["attempt"] == 1
        assert slice1["review_trends"]["drift_review"] == [
            {
                "attempt": 0,
                "review_id": None,
                "skill": "drift-audit",
                "tool": "opencode",
                "model": "github-copilot/gpt-5.6-luna",
                "effort": None,
                "head": "deadbeef",
                "at": "2026-09-12T11:21:03Z",
                "event_index": None,
                "report_ref": "/fake/drift-audit.md",
                "report_sha256": "abc123",
                "verdict": "FAIL",
                "findings_by_severity": {"P2": 1},
                "open_after_this_attempt": 1,
            },
            {
                "attempt": 1,
                "review_id": None,
                "skill": "drift-audit",
                "tool": "opencode",
                "model": "github-copilot/gpt-5.6-luna",
                "effort": None,
                "head": "deadbeef",
                "at": "2026-09-12T11:22:51Z",
                "event_index": None,
                "report_ref": "/fake/drift-audit.md",
                "report_sha256": "abc123",
                "verdict": "PASS",
                "findings_by_severity": {"P2": 0},
                "open_after_this_attempt": 0,
            },
        ]
        assert "code_review" not in slice1["review_trends"]

        assert report["pm_subjective_rating"] == {
            "available": True,
            "ref": str(ref),
            "text": ref.read_text(encoding="utf-8"),
        }

    def test_non_accepted_slice_falls_back_to_highest_attempt_present(self, tmp_path: Path) -> None:
        attempts = [_attempt(0, pm_decision="steer"), _attempt(1, pm_decision=None)]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=None))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1")
        assert report["slices"][0]["accepted_at_attempt"] is None
        assert report["slices"][0]["first_attempt"]["attempt"] == 0
        assert report["slices"][0]["final_attempt"]["attempt"] == 1

    def test_attempts_total_uses_final_ordinal_not_row_count_under_g16_fallback(self, tmp_path: Path) -> None:
        # G16's fallback (docs/MODE2-REWRITE-PLAN.md SS5/SS8) can leave a
        # sheet with just one row -- its true final attempt -- even though
        # PM ran 5 attempts; grade_run.py still records that row's real
        # ordinal (4), so attempts_total must read 5, not 1.
        attempts = [_attempt(4, pm_decision="accept")]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=4))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1")
        assert report["slices"][0]["attempts_total"] == 5
        # No attempt-0 row survived the walk's fallback -- first_attempt is
        # an honest None, never substituted with whatever row IS present.
        assert report["slices"][0]["first_attempt"] is None

    def test_review_trend_preserves_parse_error_verbatim(self, tmp_path: Path) -> None:
        attempts = [_attempt(0, drift_review=_review_record(parse_error="unrecognised report header"))]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=0))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1")
        drift_entry = report["slices"][0]["review_trends"]["drift_review"][0]
        assert drift_entry["attempt"] == 0
        assert drift_entry["parse_error"] == "unrecognised report header"
        assert "verdict" not in drift_entry
        # Attribution fields survive even a parse failure -- knowing WHICH
        # reviewer's report failed to parse matters just as much as a
        # successfully-parsed one's.
        assert drift_entry["skill"] == "drift-audit"
        assert drift_entry["tool"] == "opencode"

    def test_review_trend_entry_reads_review_id_and_effort_as_none_when_absent(self, tmp_path: Path) -> None:
        # review_score.py does not harvest review_id/effort onto the record
        # yet (Stage 4's job, docs/LEADERBOARD-REBUILD-PLAN.md) -- this must
        # read None, not KeyError, for every real sheet on disk today.
        attempts = [_attempt(0, drift_review=_review_record())]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=0))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1")
        drift_entry = report["slices"][0]["review_trends"]["drift_review"][0]
        assert drift_entry["review_id"] is None
        assert drift_entry["effort"] is None
        assert drift_entry["event_index"] is None

    def test_review_trends_are_sorted_by_attempt_regardless_of_sheet_file_order(self, tmp_path: Path) -> None:
        attempts = [
            _attempt(1, drift_review=_review_record(verdict="PASS", open_after_this_attempt=0)),
            _attempt(0, drift_review=_review_record(verdict="FAIL", open_after_this_attempt=1)),
        ]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=1))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1")
        assert [entry["attempt"] for entry in report["slices"][0]["review_trends"]["drift_review"]] == [0, 1]

    def test_disagreeing_developer_block_across_sheets_is_a_named_error(self, tmp_path: Path) -> None:
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, model="model-a"))
        _write_sheet(tmp_path, 2, _sheet("run-1", 2, model="model-b"))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        with pytest.raises(mr.ModelReportError, match="disagree on 'developer'"):
            mr.build_report(sheets, "run-1")

    def test_none_vs_non_null_stop_reason_across_sheets_is_a_named_error(self, tmp_path: Path) -> None:
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, stop_reason=None))
        _write_sheet(tmp_path, 2, _sheet("run-1", 2, stop_reason="done"))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        with pytest.raises(mr.ModelReportError, match="disagree on 'run_status.stop_reason'"):
            mr.build_report(sheets, "run-1")

    def test_disagreeing_performance_ref_across_sheets_is_a_named_error(self, tmp_path: Path) -> None:
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, pm_model_performance_ref="/path/a.md"))
        _write_sheet(tmp_path, 2, _sheet("run-1", 2, pm_model_performance_ref="/path/b.md"))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        with pytest.raises(mr.ModelReportError, match="pm_model_performance_ref"):
            mr.build_report(sheets, "run-1")

    def test_never_recorded_rating_is_not_a_problem(self, tmp_path: Path) -> None:
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, pm_model_performance_ref=None))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, problems = mr.build_report(sheets, "run-1")
        assert report["pm_subjective_rating"] == {"available": False, "ref": None, "text": None}
        assert problems == []

    def test_missing_referenced_rating_file_is_a_named_problem(self, tmp_path: Path) -> None:
        missing = tmp_path / "gone.md"
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, pm_model_performance_ref=str(missing)))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, problems = mr.build_report(sheets, "run-1")
        assert report["pm_subjective_rating"] == {"available": False, "ref": str(missing), "text": None}
        assert len(problems) == 1
        assert "no longer exists" in problems[0]
        assert report["problems"] == problems


class TestAttemptTrajectory:
    def test_includes_an_attempt_steered_with_no_commissioned_review(self, tmp_path: Path) -> None:
        # Trial 6 slice 1's real shape (docs/LEADERBOARD-REBUILD-PLAN.md
        # Stage 2): attempt 0 was steered with no review commissioned at
        # all, and must still appear -- review_trends alone would omit it
        # entirely, since it only ever lists attempts that DID commission
        # one.
        attempts = [
            _attempt(0, pm_decision="steer"),
            _attempt(1, pm_decision="accept", drift_review=_review_record(), code_review=_review_record(skill="code-review")),
        ]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=1))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1")

        trajectory = report["slices"][0]["attempt_trajectory"]
        assert [entry["attempt"] for entry in trajectory] == [0, 1]
        assert trajectory[0]["pm_decision"] == "steer"
        assert trajectory[0]["commissioned_reviews"] == []
        assert trajectory[1]["commissioned_reviews"] == [
            {"skill": "drift-audit", "review_id": None},
            {"skill": "code-review", "review_id": None},
        ]

    def test_carries_pm_attempts_counter_commit_and_correctness_verbatim(self, tmp_path: Path) -> None:
        attempts = [_attempt(0, pm_attempts_counter=0)]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=0))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1")

        entry = report["slices"][0]["attempt_trajectory"][0]
        assert entry["pm_attempts_counter"] == 0
        assert entry["commit_sha"] == "sha-0"
        assert entry["correctness"] == {"hidden_tests_passed": 40, "hidden_tests_total": 44}
        # No scoring math invented here -- correctness is the raw sheet
        # block, never reduced to a fraction (that is leaderboard.py's job).
        assert "quality" not in entry
        assert "scope" not in entry

    def test_sorted_by_attempt_regardless_of_sheet_file_order(self, tmp_path: Path) -> None:
        attempts = [_attempt(1), _attempt(0)]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=1))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1")
        assert [e["attempt"] for e in report["slices"][0]["attempt_trajectory"]] == [0, 1]


class TestResolveRunTiming:
    def _events_dir(self, tmp_path: Path, events: list[dict[str, Any]]) -> Path:
        run_dir = tmp_path / "pm-run"
        run_dir.mkdir()
        text = "\n".join(json.dumps(e) for e in events) + "\n"
        (run_dir / "events.jsonl").write_text(text, encoding="utf-8")
        return run_dir

    def test_no_run_dir_is_unavailable_not_an_error(self) -> None:
        timing, problems = mr.resolve_run_timing(None, "complete")
        assert timing == {"available": False, "reason": "no --run-dir given; events.jsonl was not read"}
        assert problems == []

    def test_run_not_finished_is_unavailable_not_an_error(self, tmp_path: Path) -> None:
        run_dir = self._events_dir(tmp_path, [{"kind": "init", "ts": "2026-09-12T06:56:34Z"}])
        timing, problems = mr.resolve_run_timing(run_dir, "active")
        assert timing["available"] is False
        assert "not finished" in timing["reason"]
        assert problems == []

    def test_complete_run_elapsed_seconds_from_init_to_complete(self, tmp_path: Path) -> None:
        run_dir = self._events_dir(
            tmp_path,
            [
                {"kind": "init", "ts": "2026-09-12T06:56:34Z"},
                {"kind": "launch", "ts": "2026-09-12T06:57:00Z"},
                {"kind": "complete", "ts": "2026-09-12T07:49:49Z"},
            ],
        )
        timing, problems = mr.resolve_run_timing(run_dir, "complete")
        assert problems == []
        assert timing == {
            "available": True,
            "init_at": "2026-09-12T06:56:34Z",
            "terminal_at": "2026-09-12T07:49:49Z",
            "terminal_kind": "complete",
            "elapsed_seconds": 3195.0,
        }

    def test_a_stop_event_after_complete_does_not_extend_a_complete_runs_span(self, tmp_path: Path) -> None:
        # Trial 5's real shape (docs/LEADERBOARD-REBUILD-PLAN.md Stage 2):
        # a routine `stop` event lands AFTER `complete`. pm_status is
        # "complete", so the terminal event looked up is `complete`, and
        # the later `stop` must never extend the measured span.
        run_dir = self._events_dir(
            tmp_path,
            [
                {"kind": "init", "ts": "2026-09-12T08:54:27Z"},
                {"kind": "complete", "ts": "2026-09-12T09:47:12Z"},
                {"kind": "stop", "ts": "2026-09-12T09:48:18Z"},
            ],
        )
        timing, problems = mr.resolve_run_timing(run_dir, "complete")
        assert problems == []
        assert timing["terminal_kind"] == "complete"
        assert timing["terminal_at"] == "2026-09-12T09:47:12Z"
        assert timing["elapsed_seconds"] == 3165.0

    def test_stopped_run_uses_the_stop_event_as_terminal(self, tmp_path: Path) -> None:
        run_dir = self._events_dir(
            tmp_path,
            [
                {"kind": "init", "ts": "2026-09-12T06:56:34Z"},
                {"kind": "stop", "ts": "2026-09-12T07:00:34Z"},
            ],
        )
        timing, problems = mr.resolve_run_timing(run_dir, "stopped")
        assert problems == []
        assert timing["terminal_kind"] == "stop"
        assert timing["elapsed_seconds"] == 240.0

    def test_missing_init_event_is_a_named_problem(self, tmp_path: Path) -> None:
        run_dir = self._events_dir(tmp_path, [{"kind": "complete", "ts": "2026-09-12T07:49:49Z"}])
        timing, problems = mr.resolve_run_timing(run_dir, "complete")
        assert timing["available"] is False
        assert len(problems) == 1
        assert "expected exactly one" in problems[0]

    def test_duplicate_terminal_event_is_a_named_problem(self, tmp_path: Path) -> None:
        run_dir = self._events_dir(
            tmp_path,
            [
                {"kind": "init", "ts": "2026-09-12T06:56:34Z"},
                {"kind": "complete", "ts": "2026-09-12T07:49:49Z"},
                {"kind": "complete", "ts": "2026-09-12T07:50:00Z"},
            ],
        )
        timing, problems = mr.resolve_run_timing(run_dir, "complete")
        assert timing["available"] is False
        assert len(problems) == 1

    def test_offset_naive_timestamp_is_unavailable_never_guessed(self, tmp_path: Path) -> None:
        run_dir = self._events_dir(
            tmp_path,
            [
                {"kind": "init", "ts": "2026-09-12T06:56:34"},  # no trailing Z/offset
                {"kind": "complete", "ts": "2026-09-12T07:49:49Z"},
            ],
        )
        timing, problems = mr.resolve_run_timing(run_dir, "complete")
        assert timing["available"] is False
        assert len(problems) == 1
        assert "unparsable or offset-naive" in problems[0]

    def test_terminal_before_init_is_a_named_problem_not_a_negative_duration(self, tmp_path: Path) -> None:
        run_dir = self._events_dir(
            tmp_path,
            [
                {"kind": "init", "ts": "2026-09-12T07:49:49Z"},
                {"kind": "complete", "ts": "2026-09-12T06:56:34Z"},
            ],
        )
        timing, problems = mr.resolve_run_timing(run_dir, "complete")
        assert timing["available"] is False
        assert len(problems) == 1
        assert "negative elapsed duration" in problems[0]

    def test_missing_events_file_is_a_named_problem_when_run_dir_given(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "pm-run-empty"
        run_dir.mkdir()
        timing, problems = mr.resolve_run_timing(run_dir, "complete")
        assert timing["available"] is False
        assert len(problems) == 1
        assert "no events found" in problems[0]


class TestResolveRunProvenance:
    def test_no_run_dir_is_unavailable_not_an_error(self) -> None:
        provenance, problems = mr.resolve_run_provenance(None)
        assert provenance == {"available": False, "reason": "no --run-dir given; run.json was not read", "pm_run_dir": None}
        assert problems == []

    def test_reads_repo_and_branch_and_checks_presence(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "pm-run"
        run_dir.mkdir()
        present_repo = tmp_path / "present-repo"
        present_repo.mkdir()
        (run_dir / "run.json").write_text(json.dumps({"repo": str(present_repo), "branch": "pm-eval-v2/trial-9"}), encoding="utf-8")

        provenance, problems = mr.resolve_run_provenance(run_dir)

        assert problems == []
        assert provenance == {
            "available": True,
            "repo": str(present_repo),
            "branch": "pm-eval-v2/trial-9",
            "repo_present_as_of_generation": True,
            "pm_run_dir": str(run_dir),
        }

    def test_missing_worktree_is_recorded_false_not_an_error(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "pm-run"
        run_dir.mkdir()
        (run_dir / "run.json").write_text(json.dumps({"repo": str(tmp_path / "gone"), "branch": "b"}), encoding="utf-8")

        provenance, problems = mr.resolve_run_provenance(run_dir)

        assert problems == []
        assert provenance["repo_present_as_of_generation"] is False

    def test_missing_run_json_is_a_named_problem_when_run_dir_given(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "pm-run-empty"
        run_dir.mkdir()
        provenance, problems = mr.resolve_run_provenance(run_dir)
        assert provenance["available"] is False
        assert len(problems) == 1
        assert "no run.json found" in problems[0]


class TestMain:
    def test_writes_report_and_returns_0_on_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        root = tmp_path / "bench-root"
        sheets_dir = root / "results" / "runs" / "run-1"
        _write_sheet(sheets_dir, 1, _sheet("run-1", 1))
        monkeypatch.setattr(mr, "bench_root", lambda: root)

        exit_code = mr.main(["--run-id", "run-1"])

        assert exit_code == 0
        out_path = sheets_dir / "model-report.json"
        assert out_path.is_file()
        written = json.loads(out_path.read_text(encoding="utf-8"))
        assert written["run_id"] == "run-1"

    def test_returns_1_when_problems_are_reported(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        root = tmp_path / "bench-root"
        sheets_dir = root / "results" / "runs" / "run-1"
        _write_sheet(sheets_dir, 1, _sheet("run-1", 1, pm_model_performance_ref=str(tmp_path / "gone.md")))
        monkeypatch.setattr(mr, "bench_root", lambda: root)

        assert mr.main(["--run-id", "run-1"]) == 1

    def test_run_dir_flag_populates_the_timing_block(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        root = tmp_path / "bench-root"
        sheets_dir = root / "results" / "runs" / "run-1"
        _write_sheet(sheets_dir, 1, _sheet("run-1", 1))
        monkeypatch.setattr(mr, "bench_root", lambda: root)

        run_dir = tmp_path / "pm-run"
        run_dir.mkdir()
        events = [
            {"kind": "init", "ts": "2026-09-12T06:56:34Z"},
            {"kind": "complete", "ts": "2026-09-12T07:49:49Z"},
        ]
        (run_dir / "events.jsonl").write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
        (run_dir / "run.json").write_text(
            json.dumps({"repo": str(tmp_path / "dev-repo"), "branch": "pm-eval-v2/trial-1"}), encoding="utf-8"
        )

        exit_code = mr.main(["--run-id", "run-1", "--run-dir", str(run_dir)])

        assert exit_code == 0
        written = json.loads((sheets_dir / "model-report.json").read_text(encoding="utf-8"))
        assert written["timing"] == {
            "available": True,
            "init_at": "2026-09-12T06:56:34Z",
            "terminal_at": "2026-09-12T07:49:49Z",
            "terminal_kind": "complete",
            "elapsed_seconds": 3195.0,
        }
        assert written["provenance"] == {
            "available": True,
            "repo": str(tmp_path / "dev-repo"),
            "branch": "pm-eval-v2/trial-1",
            "repo_present_as_of_generation": False,
            "pm_run_dir": str(run_dir),
        }
