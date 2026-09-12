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


def _attempt(
    attempt: int,
    *,
    pm_decision: str | None = "steer",
    drift_review: dict[str, Any] | None = None,
    code_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "attempt": attempt,
        "commit_sha": f"sha-{attempt}",
        "correctness": {"hidden_tests_passed": 40, "hidden_tests_total": 44},
        "quality": {"lint_findings_by_tool": {}, "code_health_findings_by_category": {}},
        "scope": {"violations": []},
        "pm_decision": pm_decision,
        "drift_review": drift_review,
        "code_review": code_review,
    }


def _sheet(
    run_id: str,
    slice_number: int,
    *,
    model: str = "opencode/some-model",
    pm_status: str = "complete",
    stop_reason: str | None = "done",
    attempts: list[dict[str, Any]] | None = None,
    accepted_at_attempt: int | None = 0,
    pm_model_performance_ref: str | None = None,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "model": model,
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
            _attempt(0, pm_decision="steer", drift_review={"verdict": "FAIL", "findings_by_severity": {"P2": 1}, "open_after_this_attempt": 1}),
            _attempt(1, pm_decision="accept", drift_review={"verdict": "PASS", "findings_by_severity": {"P2": 0}, "open_after_this_attempt": 0}),
        ]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=slice1_attempts, accepted_at_attempt=1, pm_model_performance_ref=str(ref)))
        _write_sheet(tmp_path, 2, _sheet("run-1", 2, accepted_at_attempt=0, pm_model_performance_ref=str(ref)))

        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, problems = mr.build_report(sheets, "run-1")

        assert problems == []
        assert report["run_id"] == "run-1"
        assert report["model"] == "opencode/some-model"
        assert report["run_status"] == {"pm_status": "complete", "stop_reason": "done"}
        assert [s["slice"] for s in report["slices"]] == [1, 2]

        slice1 = report["slices"][0]
        assert slice1["attempts_total"] == 2
        assert slice1["accepted_at_attempt"] == 1
        assert slice1["final_attempt"]["attempt"] == 1
        assert slice1["review_trends"]["drift_review"] == [
            {"attempt": 0, "verdict": "FAIL", "findings_by_severity": {"P2": 1}, "open_after_this_attempt": 1},
            {"attempt": 1, "verdict": "PASS", "findings_by_severity": {"P2": 0}, "open_after_this_attempt": 0},
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

    def test_review_trend_preserves_parse_error_verbatim(self, tmp_path: Path) -> None:
        attempts = [_attempt(0, drift_review={"parse_error": "unrecognised report header"})]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=0))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1")
        assert report["slices"][0]["review_trends"]["drift_review"] == [
            {"attempt": 0, "parse_error": "unrecognised report header"}
        ]

    def test_review_trends_are_sorted_by_attempt_regardless_of_sheet_file_order(self, tmp_path: Path) -> None:
        attempts = [
            _attempt(1, drift_review={"verdict": "PASS", "findings_by_severity": {}, "open_after_this_attempt": 0}),
            _attempt(0, drift_review={"verdict": "FAIL", "findings_by_severity": {}, "open_after_this_attempt": 1}),
        ]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=1))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1")
        assert [entry["attempt"] for entry in report["slices"][0]["review_trends"]["drift_review"]] == [0, 1]

    def test_disagreeing_model_across_sheets_is_a_named_error(self, tmp_path: Path) -> None:
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, model="model-a"))
        _write_sheet(tmp_path, 2, _sheet("run-1", 2, model="model-b"))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        with pytest.raises(mr.ModelReportError, match="disagree on 'model'"):
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
