"""Tests for tools/model_report.py (Tool 4: one model's full run, reshaped).

Fixtures are hand-written scoring sheets under `tmp_path`, matching the real
shape `dev_check.py`/`review_score.py` write (docs/MODE2-REWRITE-PLAN.md §7).
No git, no subprocess: this tool only reads already-graded JSON/Markdown
already on disk.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import dev_check  # noqa: E402
import model_report as mr  # noqa: E402


def _real_obligation_groups(slice_number: int) -> list[dict[str, Any]]:
    """The real obligation groups for one slice, straight from this repo's
    own `hidden_tests/obligations.yaml` -- fixtures below build `by_node`/
    `by_obligation` against these rather than an invented parallel map, so
    `model_report.first_attempt_node_outcomes`'s reconstruction-vs-
    `by_obligation` cross-check (exercised for real in `TestBuildReport`)
    has a genuine rubric to check against, matching how `dev_check.py`
    itself derives it.
    """
    obligations = dev_check.load_obligations(REPO_ROOT)
    return dev_check.obligation_groups_for_slice(obligations, slice_number)


def _correctness_for_slice(slice_number: int, *, failing_nodes: frozenset[str] = frozenset()) -> dict[str, Any]:
    """A `correctness` block shaped like `dev_check.score_correctness`'s
    real output for one slice, with every node passing except
    `failing_nodes`."""
    groups = _real_obligation_groups(slice_number)
    outcomes = {node: ("failed" if node in failing_nodes else "passed") for group in groups for node in group["tests"]}
    return dev_check.score_correctness(outcomes, groups, slice_number)


def _review_record(
    *,
    skill: str = "drift-audit",
    tool: str = "opencode",
    model: str = "github-copilot/gpt-5.6-luna",
    effort: str | None = None,
    review_id: str | None = None,
    event_index: int | None = 0,
    head: str = "deadbeef",
    before_head: str = "beforedeadbeef",
    at: str = "2026-09-12T11:21:03Z",
    verdict: str | None = "PASS",
    findings_by_severity: dict[str, int] | None = None,
    open_after_this_attempt: int | None = None,
    parse_error: str | None = None,
    superseded_by: int | None = None,
) -> dict[str, Any]:
    """A `reviews` list record shaped like review_score.py's real
    `build_record` output (tools/review_score.py) -- including every field
    it carries (`review_id`/`skill`/`tool`/`model`/`effort`/`head`/
    `before_head`/`at`/`event_index`/`report_ref`/`report_sha256`/
    `superseded_by`) that model_report.py's old `_review_entry` used
    to silently drop (docs/LEADERBOARD-REBUILD-PLAN.md Stage 2, then Stage
    4a for the fields Stage 2 itself couldn't populate yet). No
    `commissioned` key at all -- that field was deleted as dead weight once
    every record in a `reviews` list is unconditionally a commission
    (Stage 4a).
    """
    record: dict[str, Any] = {
        "review_id": review_id,
        "event_index": event_index,
        "report_ref": f"/fake/{skill}.md",
        "report_sha256": "abc123",
        "skill": skill,
        "tool": tool,
        "model": model,
        "effort": effort,
        "head": head,
        "before_head": before_head,
        "grants_seen": 0,
        "at": at,
        "superseded_by": superseded_by,
    }
    if parse_error is not None:
        record["parse_error"] = parse_error
        return record
    record["verdict"] = verdict
    record["findings_by_severity"] = findings_by_severity if findings_by_severity is not None else {}
    record["open_after_this_attempt"] = open_after_this_attempt
    return record


def _size_complexity(
    *,
    baseline_commit: str = "before-head",
    metric_version: int | None = 1,
    production_loc_net: int | None = 12,
    production_cc_net: int | None = 3,
    loc_available: bool = True,
    cc_available: bool = True,
) -> dict[str, Any]:
    """A `size_complexity` block shaped like dev_check.compute_size_complexity's
    real output (Stage 3, docs/LEADERBOARD-REBUILD-PLAN.md) -- just the
    fields model_report.py's own tests exercise (baseline_commit,
    metric_version, and each bucket's `net`/`available`), not the full
    binary_files/function_count/coverage_note shape dev_check.py's own
    tests already cover."""
    loc: dict[str, Any] = {"available": loc_available}
    if loc_available:
        loc["buckets"] = {"production": {"added": max(production_loc_net, 0), "deleted": 0, "net": production_loc_net}}
    complexity: dict[str, Any] = {"available": cc_available}
    if cc_available:
        complexity["production"] = {"baseline_total": 10, "endpoint_total": 10 + production_cc_net, "net": production_cc_net}
    return {
        "metric_version": metric_version,
        "baseline_commit": baseline_commit,
        "endpoint_commit": "endpoint-head",
        "loc": loc,
        "complexity": complexity,
    }


def _attempt(
    attempt: int,
    *,
    pm_decision: str | None = "steer",
    pm_attempts_counter: int | None = None,
    reviews: list[dict[str, Any]] | None = None,
    size_complexity: dict[str, Any] | None = None,
    slice_number: int = 1,
    correctness: dict[str, Any] | None = None,
) -> dict[str, Any]:
    entry = {
        "attempt": attempt,
        "pm_attempts_counter": pm_attempts_counter if pm_attempts_counter is not None else attempt,
        "commit_sha": f"sha-{attempt}",
        "correctness": correctness if correctness is not None else _correctness_for_slice(slice_number),
        "quality": {"lint_findings_by_tool": {}, "code_health_findings_by_category": {}},
        "scope": {"violations": []},
        "pm_decision": pm_decision,
        "reviews": reviews if reviews is not None else [],
    }
    if size_complexity is not None:
        entry["size_complexity"] = size_complexity
    return entry


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
        "attempts": attempts if attempts is not None else [_attempt(0, pm_decision="accept", slice_number=slice_number)],
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
                reviews=[_review_record(
                    event_index=11, verdict="FAIL", findings_by_severity={"P2": 1},
                    open_after_this_attempt=1, at="2026-09-12T11:21:03Z",
                )],
            ),
            _attempt(
                1,
                pm_decision="accept",
                reviews=[_review_record(
                    event_index=17, verdict="PASS", findings_by_severity={"P2": 0},
                    open_after_this_attempt=0, at="2026-09-12T11:22:51Z",
                )],
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
        # Stage 4b: every `reviews` entry now also carries a `pm_rating`
        # field -- "unjudged" here, since this report was built with no
        # `run_dir` (so no run.json to harvest a real PM judgment from).
        unjudged = {"status": "unjudged", "score": None, "reason": None, "at": None, "judgment_id": None}
        assert slice1["reviews"] == [
            {
                "attempt": 0,
                "review_id": None,
                "skill": "drift-audit",
                "tool": "opencode",
                "model": "github-copilot/gpt-5.6-luna",
                "effort": None,
                "head": "deadbeef",
                "before_head": "beforedeadbeef",
                "at": "2026-09-12T11:21:03Z",
                "event_index": 11,
                "report_ref": "/fake/drift-audit.md",
                "report_sha256": "abc123",
                "superseded_by": None,
                "verdict": "FAIL",
                "findings_by_severity": {"P2": 1},
                "open_after_this_attempt": 1,
                "pm_rating": unjudged,
            },
            {
                "attempt": 1,
                "review_id": None,
                "skill": "drift-audit",
                "tool": "opencode",
                "model": "github-copilot/gpt-5.6-luna",
                "effort": None,
                "head": "deadbeef",
                "before_head": "beforedeadbeef",
                "at": "2026-09-12T11:22:51Z",
                "event_index": 17,
                "report_ref": "/fake/drift-audit.md",
                "report_sha256": "abc123",
                "superseded_by": None,
                "verdict": "PASS",
                "findings_by_severity": {"P2": 0},
                "open_after_this_attempt": 0,
                "pm_rating": unjudged,
            },
        ]

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
        attempts = [_attempt(0, reviews=[_review_record(parse_error="unrecognised report header")])]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=0))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1")
        drift_entry = report["slices"][0]["reviews"][0]
        assert drift_entry["attempt"] == 0
        assert drift_entry["parse_error"] == "unrecognised report header"
        assert "verdict" not in drift_entry
        # Attribution fields survive even a parse failure -- knowing WHICH
        # reviewer's report failed to parse matters just as much as a
        # successfully-parsed one's.
        assert drift_entry["skill"] == "drift-audit"
        assert drift_entry["tool"] == "opencode"

    def test_review_entry_reads_review_id_and_effort_verbatim(self, tmp_path: Path) -> None:
        # Stage 4a: review_score.py now harvests review_id/effort/event_index
        # for real -- this must pass them through, not read them as None.
        attempts = [_attempt(0, reviews=[_review_record(review_id="review-2", effort="low", event_index=15)])]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=0))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1")
        drift_entry = report["slices"][0]["reviews"][0]
        assert drift_entry["review_id"] == "review-2"
        assert drift_entry["effort"] == "low"
        assert drift_entry["event_index"] == 15

    def test_review_entry_carries_superseded_by(self, tmp_path: Path) -> None:
        attempts = [_attempt(0, reviews=[_review_record(event_index=14, superseded_by=15, parse_error="no report")])]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=0))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1")
        assert report["slices"][0]["reviews"][0]["superseded_by"] == 15

    def test_reviews_are_sorted_by_attempt_regardless_of_sheet_file_order(self, tmp_path: Path) -> None:
        attempts = [
            _attempt(1, reviews=[_review_record(event_index=1, verdict="PASS", open_after_this_attempt=0)]),
            _attempt(0, reviews=[_review_record(event_index=0, verdict="FAIL", open_after_this_attempt=1)]),
        ]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=1))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1")
        assert [entry["attempt"] for entry in report["slices"][0]["reviews"]] == [0, 1]

    def test_two_reviewers_on_one_attempt_both_appear_in_the_flat_list(self, tmp_path: Path) -> None:
        """A panel (hypothetical -- docs/LEADERBOARD-REBUILD-PLAN.md is
        explicit no real one exists in the cohort): two records on one
        attempt, neither superseded, both present."""
        attempts = [
            _attempt(0, reviews=[
                _review_record(event_index=0, tool="claude", model="model-a"),
                _review_record(event_index=1, tool="opencode", model="model-b"),
            ]),
        ]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=0))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1")
        reviews = report["slices"][0]["reviews"]
        assert len(reviews) == 2
        assert {r["model"] for r in reviews} == {"model-a", "model-b"}
        assert all(r["superseded_by"] is None for r in reviews)

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
        # all, and must still appear -- `reviews` alone would omit it
        # entirely, since it only ever lists attempts that DID commission
        # one.
        attempts = [
            _attempt(0, pm_decision="steer"),
            _attempt(1, pm_decision="accept", reviews=[
                _review_record(event_index=5, review_id="review-1"),
                _review_record(event_index=6, skill="code-review", review_id="review-2"),
            ]),
        ]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=1))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1")

        trajectory = report["slices"][0]["attempt_trajectory"]
        assert [entry["attempt"] for entry in trajectory] == [0, 1]
        assert trajectory[0]["pm_decision"] == "steer"
        assert trajectory[0]["commissioned_reviews"] == []
        assert trajectory[1]["commissioned_reviews"] == [
            {"skill": "drift-audit", "review_id": "review-1", "event_index": 5},
            {"skill": "code-review", "review_id": "review-2", "event_index": 6},
        ]

    def test_carries_pm_attempts_counter_commit_and_correctness_verbatim(self, tmp_path: Path) -> None:
        attempts = [_attempt(0, pm_attempts_counter=0)]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=0))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1")

        entry = report["slices"][0]["attempt_trajectory"][0]
        assert entry["pm_attempts_counter"] == 0
        assert entry["commit_sha"] == "sha-0"
        # No scoring math invented here -- correctness is the raw sheet
        # block, never reduced to a fraction (that is leaderboard.py's job) --
        # except its bulky by_node map, which is dropped (it stays sheet-only).
        assert entry["correctness"]["hidden_tests_passed"] == attempts[0]["correctness"]["hidden_tests_passed"]
        assert entry["correctness"]["hidden_tests_total"] == attempts[0]["correctness"]["hidden_tests_total"]
        assert entry["correctness"]["by_obligation"] == attempts[0]["correctness"]["by_obligation"]
        assert "by_node" not in entry["correctness"]
        assert "quality" not in entry
        assert "scope" not in entry

    def test_sorted_by_attempt_regardless_of_sheet_file_order(self, tmp_path: Path) -> None:
        attempts = [_attempt(1), _attempt(0)]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=1))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1")
        assert [e["attempt"] for e in report["slices"][0]["attempt_trajectory"]] == [0, 1]

    def test_size_complexity_summary_is_a_compact_row_not_the_full_block(self, tmp_path: Path) -> None:
        attempts = [_attempt(0, size_complexity=_size_complexity(production_loc_net=7, production_cc_net=-2))]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=0))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1")

        entry = report["slices"][0]["attempt_trajectory"][0]
        assert entry["size_complexity"] == {
            "loc_available": True,
            "production_loc_net": 7,
            "cc_available": True,
            "production_cc_net": -2,
        }
        # A summary, not a second copy: baseline_commit/endpoint_commit/full
        # bucket detail stay out of the trajectory row.
        assert "baseline_commit" not in entry["size_complexity"]

    def test_size_complexity_summary_is_honest_about_unavailable_measurements(self, tmp_path: Path) -> None:
        attempts = [_attempt(0, size_complexity=_size_complexity(loc_available=False, cc_available=False))]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=0))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1")

        entry = report["slices"][0]["attempt_trajectory"][0]
        assert entry["size_complexity"] == {
            "loc_available": False,
            "production_loc_net": None,
            "cc_available": False,
            "production_cc_net": None,
        }

    def test_an_attempt_with_no_size_complexity_block_at_all_reads_unavailable(self, tmp_path: Path) -> None:
        # A sheet graded before Stage 3 landed -- size_complexity is simply
        # absent, not a KeyError.
        attempts = [_attempt(0)]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=0))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1")
        entry = report["slices"][0]["attempt_trajectory"][0]
        assert entry["size_complexity"]["loc_available"] is False
        assert entry["size_complexity"]["cc_available"] is False


class TestFirstAttemptNodeOutcomes:
    """The one per-slice node map model-report.json now carries -- the
    first attempt's `by_node`, nested `{group_id: {node_id: outcome}}` --
    and the by_node stripping this replaces the old flat leak with."""

    def test_by_node_absent_from_first_attempt_final_attempt_and_every_trajectory_row(self, tmp_path: Path) -> None:
        attempts = [_attempt(0), _attempt(1, pm_decision="accept")]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=1))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, problems = mr.build_report(sheets, "run-1")
        assert problems == []

        slice_entry = report["slices"][0]
        assert "by_node" not in slice_entry["first_attempt"]["correctness"]
        assert "by_node" not in slice_entry["final_attempt"]["correctness"]
        for row in slice_entry["attempt_trajectory"]:
            assert "by_node" not in row["correctness"]
        # The full per-attempt map is untouched on the sheet dict itself --
        # stripping must copy, never mutate, since the same sheet is read
        # again elsewhere in the same process.
        assert "by_node" in attempts[0]["correctness"]

    def test_nested_by_group_matches_the_real_obligation_partition(self, tmp_path: Path) -> None:
        attempts = [_attempt(0, slice_number=2)]
        _write_sheet(tmp_path, 2, _sheet("run-1", 2, attempts=attempts, accepted_at_attempt=0))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, problems = mr.build_report(sheets, "run-1")
        assert problems == []

        outcomes = report["slices"][0]["first_attempt_node_outcomes"]
        groups = _real_obligation_groups(2)
        assert set(outcomes) == {g["id"] for g in groups}
        for group in groups:
            assert set(outcomes[group["id"]]) == set(group["tests"])
            assert all(outcome == "passed" for outcome in outcomes[group["id"]].values())

    def test_null_when_slice_has_no_attempt_zero_row(self, tmp_path: Path) -> None:
        attempts = [_attempt(3, pm_decision="accept")]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=3))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, problems = mr.build_report(sheets, "run-1")
        assert problems == []

        slice_entry = report["slices"][0]
        assert slice_entry["has_attempt_zero"] is False
        assert slice_entry["first_attempt_node_outcomes"] is None

    def test_malformed_by_node_shape_is_a_named_model_report_error(self, tmp_path: Path) -> None:
        # A9: by_node recorded as a list, not a {node_id: outcome} mapping,
        # used to raise a bare AttributeError from deep inside the
        # reconstruction instead of a named ModelReportError naming the
        # concrete sheet.
        correctness = _correctness_for_slice(1)
        correctness["by_node"] = ["passed"]
        attempts = [_attempt(0, correctness=correctness)]
        sheet_path = _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=0))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        with pytest.raises(mr.ModelReportError, match=re.escape(str(sheet_path))):
            mr.build_report(sheets, "run-1")

    def test_empty_malformed_by_node_is_a_named_model_report_error(self, tmp_path: Path) -> None:
        # An empty list is falsy, so reading it through `or {}` coerced it
        # into a valid-looking empty mapping and skipped the shape check
        # entirely -- the validator must see the raw recorded value.
        correctness = _correctness_for_slice(1)
        correctness["by_node"] = []
        attempts = [_attempt(0, correctness=correctness)]
        sheet_path = _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=0))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        with pytest.raises(mr.ModelReportError, match=re.escape(str(sheet_path))):
            mr.build_report(sheets, "run-1")

    def test_malformed_by_node_outcome_value_is_a_named_model_report_error(self, tmp_path: Path) -> None:
        correctness = _correctness_for_slice(1)
        first_node = next(iter(correctness["by_node"]))
        correctness["by_node"][first_node] = "not-a-real-outcome"
        attempts = [_attempt(0, correctness=correctness)]
        sheet_path = _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=0))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        with pytest.raises(mr.ModelReportError, match=re.escape(str(sheet_path))):
            mr.build_report(sheets, "run-1")

    def test_reconstruction_disagreeing_with_by_obligation_is_a_named_error(self, tmp_path: Path) -> None:
        correctness = _correctness_for_slice(1)
        # Corrupt the recorded by_obligation count for one group without
        # touching by_node -- the two are supposed to agree, since both
        # came from the same score_correctness call; this fakes the sheet
        # having gone stale in only one of them.
        correctness["by_obligation"]["mass_bin_denominator"]["passed"] = 0
        attempts = [_attempt(0, correctness=correctness)]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=0))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        with pytest.raises(mr.ModelReportError, match="mass_bin_denominator"):
            mr.build_report(sheets, "run-1")


class TestBaselineResetLabelling:
    """Stage 3 (docs/LEADERBOARD-REBUILD-PLAN.md): 'In a stop/restart case
    the stored grading baseline may have reset; that case is refused or
    labelled, never quietly reused as an apparent first-to-final
    improvement.'"""

    def test_same_baseline_across_first_and_final_attempt_is_not_flagged(self, tmp_path: Path) -> None:
        attempts = [
            _attempt(0, size_complexity=_size_complexity(baseline_commit="base-x")),
            _attempt(1, pm_decision="accept", size_complexity=_size_complexity(baseline_commit="base-x")),
        ]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=1))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, problems = mr.build_report(sheets, "run-1")
        assert report["slices"][0]["size_complexity_baseline_reset"] is False
        assert problems == []

    def test_a_differing_baseline_between_first_and_final_attempt_is_flagged_and_named(self, tmp_path: Path) -> None:
        attempts = [
            _attempt(0, size_complexity=_size_complexity(baseline_commit="base-BEFORE-restart")),
            _attempt(1, pm_decision="accept", size_complexity=_size_complexity(baseline_commit="base-AFTER-restart")),
        ]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=1))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, problems = mr.build_report(sheets, "run-1")

        slice_entry = report["slices"][0]
        assert slice_entry["size_complexity_baseline_reset"] is True
        assert any("baseline reset" in p and "run-1" in p and "slice 1" in p for p in problems)
        # Correctness is unaffected and must not be suppressed by the reset.
        assert slice_entry["first_attempt"]["correctness"]["hidden_tests_passed"] == 44
        assert slice_entry["final_attempt"]["correctness"]["hidden_tests_passed"] == 44

    def test_missing_size_complexity_on_either_attempt_is_not_flagged(self, tmp_path: Path) -> None:
        # No baseline_commit recorded at all on one side -- nothing to
        # compare, so this must read as "not reset", not a false positive.
        attempts = [
            _attempt(0),
            _attempt(1, pm_decision="accept", size_complexity=_size_complexity(baseline_commit="base-x")),
        ]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=1))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, problems = mr.build_report(sheets, "run-1")
        assert report["slices"][0]["size_complexity_baseline_reset"] is False
        assert problems == []


class TestMeasurementMetricVersion:
    def test_a_single_agreed_metric_version_is_carried_through(self, tmp_path: Path) -> None:
        attempts = [_attempt(0, size_complexity=_size_complexity(metric_version=1))]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=0))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, problems = mr.build_report(sheets, "run-1")
        assert report["measurement_metric_version"] == 1
        assert problems == []

    def test_no_size_complexity_data_anywhere_is_none_not_an_error(self, tmp_path: Path) -> None:
        attempts = [_attempt(0)]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=0))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, problems = mr.build_report(sheets, "run-1")
        assert report["measurement_metric_version"] is None
        assert problems == []

    def test_disagreeing_metric_versions_across_the_run_are_a_named_problem(self, tmp_path: Path) -> None:
        attempts = [
            _attempt(0, size_complexity=_size_complexity(metric_version=1)),
            _attempt(1, pm_decision="accept", size_complexity=_size_complexity(metric_version=2)),
        ]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=1))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, problems = mr.build_report(sheets, "run-1")
        assert report["measurement_metric_version"] is None
        assert any("metric_version" in p and "run-1" in p for p in problems)


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


class TestResolvePmJudgments:
    """Stage 4b (docs/LEADERBOARD-REBUILD-PLAN.md): harvest PM's own
    `review_judgments`/`developer_judgments` and join them onto an
    already-built `slices` list. Fixtures here are deliberately minimal
    (only the keys `resolve_pm_judgments` itself reads) rather than full
    `_review_record`/`attempt_trajectory` shapes -- unit-level, matching
    `TestResolveRunTiming`/`TestResolveRunProvenance`'s own style above.

    Real-shape fixtures (trial 10 Slice 1's steer-joined and superseded
    judgments; trial 11 Slice 1's shape-C unavailable record and Slice 2's
    single-launch-event `+1` case) are called out by name -- every one of
    these was re-derived against the actual trial data before being turned
    into a fixture here, not invented.
    """

    def _run_dir(self, tmp_path: Path, *, slices: list[dict[str, Any]], events: list[dict[str, Any]]) -> Path:
        run_dir = tmp_path / "pm-run"
        run_dir.mkdir()
        (run_dir / "run.json").write_text(json.dumps({"slices": slices}), encoding="utf-8")
        (run_dir / "events.jsonl").write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
        return run_dir

    def _review(self, **overrides: Any) -> dict[str, Any]:
        base = {"review_id": None, "skill": "drift-audit", "tool": "claude", "model": "m", "effort": None}
        base.update(overrides)
        return base

    def test_no_run_dir_marks_every_entry_unjudged_and_is_available_false(self) -> None:
        slices = [{"slice": 1, "reviews": [self._review(review_id="review-1")], "attempt_trajectory": [{"attempt": 0}]}]
        block, problems = mr.resolve_pm_judgments(None, "run-1", slices)
        assert block == {
            "available": False,
            "reason": "no --run-dir given; run.json/events.jsonl were not read for PM judgments",
            "review_judgments_recorded": False,
            "developer_judgments_recorded": False,
            "comparisons": [],
        }
        assert problems == []
        assert slices[0]["reviews"][0]["pm_rating"]["status"] == "unjudged"
        assert slices[0]["attempt_trajectory"][0]["pm_developer_judgment"]["status"] == "unjudged"

    def test_run_with_no_judgments_anywhere_is_labelled_absence_not_error(self, tmp_path: Path) -> None:
        # Trials 4-7's real shape: run.json exists and has slices, but no
        # review_judgments/developer_judgments key anywhere (this feature
        # postdates them) -- a labelled absence, never an error.
        run_dir = self._run_dir(tmp_path, slices=[{"id": "Slice 1"}], events=[{"kind": "launch", "slice": "Slice 1"}])
        slices = [{"slice": 1, "reviews": [], "attempt_trajectory": [{"attempt": 0}]}]
        block, problems = mr.resolve_pm_judgments(run_dir, "run-1", slices)
        assert block["available"] is True
        assert block["review_judgments_recorded"] is False
        assert block["developer_judgments_recorded"] is False
        assert block["comparisons"] == []
        assert problems == []

    def test_rating_judgment_joins_onto_the_matching_review(self, tmp_path: Path) -> None:
        run_state_slices = [
            {
                "id": "Slice 1",
                "review_judgments": [
                    {
                        "assessment": "rating",
                        "judgment_id": "judgment-1",
                        "review_id": "review-1",
                        "skill": "drift-audit",
                        "score": 2,
                        "reason": "clean",
                        "at": "2026-09-14T00:00:00Z",
                    }
                ],
            }
        ]
        run_dir = self._run_dir(tmp_path, slices=run_state_slices, events=[])
        slices = [{"slice": 1, "reviews": [self._review(review_id="review-1")], "attempt_trajectory": []}]
        block, problems = mr.resolve_pm_judgments(run_dir, "run-1", slices)
        assert problems == []
        assert block["review_judgments_recorded"] is True
        assert slices[0]["reviews"][0]["pm_rating"] == {
            "status": "rated",
            "score": 2,
            "reason": "clean",
            "at": "2026-09-14T00:00:00Z",
            "judgment_id": "judgment-1",
        }

    def test_unknown_review_id_absent_from_run_json_is_a_named_case_3_problem(self, tmp_path: Path) -> None:
        # run.json's own reviews[] for this slice carries no record for
        # "review-ghost" at all: PM's judgment names a review its own
        # recorded state never produced (case 3, never guessed as case 1).
        run_state_slices = [
            {
                "id": "Slice 1",
                "review_judgments": [
                    {"assessment": "rating", "judgment_id": "judgment-1", "review_id": "review-ghost", "skill": "drift-audit", "score": 1}
                ],
            }
        ]
        run_dir = self._run_dir(tmp_path, slices=run_state_slices, events=[])
        slices = [{"slice": 1, "reviews": [self._review(review_id="review-1")], "attempt_trajectory": []}]
        block, problems = mr.resolve_pm_judgments(run_dir, "run-1", slices)
        assert len(problems) == 1
        assert "review-ghost" in problems[0]
        assert "does not appear anywhere in run.json's own reviews" in problems[0]
        assert slices[0]["reviews"][0]["pm_rating"]["status"] == "unjudged"

    def test_dangling_review_id_on_an_ungraded_attempt_is_a_named_coverage_consequence(self, tmp_path: Path) -> None:
        # Real cohort shape (trials 8 and 13, Slice 1, 20 occurrences total):
        # run.json DOES carry the named review, but grade_run.py's G16 walk
        # only graded the slice's final attempt (the Developer did not hold
        # one commit per attempt) -- so the attempt this review was
        # commissioned against has no scoring-sheet row, and this report's
        # own `reviews` never harvested it. This is the benign, expected
        # case and must say so, never the alarming generic wording.
        events = [
            {"kind": "init"},
            {"kind": "launch", "slice": "Slice 1"},
            {"kind": "steer", "slice": "Slice 1"},
        ]
        run_state_slices = [
            {
                "id": "Slice 1",
                "reviews": [
                    {"review_id": "review-1", "skill": "drift-audit", "origin_event": {"index": 2, "kind": "steer", "slice": "Slice 1"}}
                ],
                "review_judgments": [
                    {"assessment": "rating", "judgment_id": "judgment-1", "review_id": "review-1", "skill": "drift-audit", "score": 2}
                ],
            }
        ]
        run_dir = self._run_dir(tmp_path, slices=run_state_slices, events=events)
        # This report's own scoring-sheet coverage only reaches attempt 0
        # (the slice's final graded attempt) -- attempt 1, which is what
        # review-1 was commissioned against (origin_event.index=2, +1 ==
        # attempt ordinal 1), was never graded.
        slices = [{"slice": 1, "reviews": [], "attempt_trajectory": [{"attempt": 0}]}]
        block, problems = mr.resolve_pm_judgments(run_dir, "run-1", slices)
        assert len(problems) == 1
        assert "attempt 1" in problems[0]
        assert "no scoring-sheet row in this report" in problems[0]
        assert "coverage gap, not a harvest bug" in problems[0]
        # The message names the observable fact and points at grade_run.py's
        # own output for the cause -- it never asserts a cause it only
        # inferred (a refused G16 walk is usual, but not the only way an
        # attempt can end up ungraded).
        assert "grade_run.py's own output for the slice" in problems[0]

    def test_dangling_review_id_on_a_graded_attempt_is_a_named_harvest_anomaly(self, tmp_path: Path) -> None:
        # Same shape as the coverage-consequence case above, except the
        # attempt review-1 was commissioned against WAS graded (attempt 1
        # has its own scoring-sheet row) -- so the missing `reviews` entry
        # is a genuine review_score.py harvest bug, and must be reported as
        # alarming, distinct wording, never softened to case 1.
        events = [
            {"kind": "init"},
            {"kind": "launch", "slice": "Slice 1"},
            {"kind": "steer", "slice": "Slice 1"},
        ]
        run_state_slices = [
            {
                "id": "Slice 1",
                "reviews": [
                    {"review_id": "review-1", "skill": "drift-audit", "origin_event": {"index": 2, "kind": "steer", "slice": "Slice 1"}}
                ],
                "review_judgments": [
                    {"assessment": "rating", "judgment_id": "judgment-1", "review_id": "review-1", "skill": "drift-audit", "score": 2}
                ],
            }
        ]
        run_dir = self._run_dir(tmp_path, slices=run_state_slices, events=events)
        slices = [{"slice": 1, "reviews": [], "attempt_trajectory": [{"attempt": 0}, {"attempt": 1}]}]
        block, problems = mr.resolve_pm_judgments(run_dir, "run-1", slices)
        assert len(problems) == 1
        assert "attempt 1" in problems[0]
        assert "WAS graded" in problems[0]
        assert "should have produced a reviews entry" in problems[0]
        assert "coverage consequence" not in problems[0]

    def test_dangling_review_id_with_no_origin_event_index_falls_back_to_named_unresolvable(self, tmp_path: Path) -> None:
        # run.json's own record for "review-1" exists but carries no
        # origin_event.index -- the ordinal cannot be determined, so this
        # must never be guessed as the benign case 1.
        run_state_slices = [
            {
                "id": "Slice 1",
                "reviews": [{"review_id": "review-1", "skill": "drift-audit", "origin_event": {}}],
                "review_judgments": [
                    {"assessment": "rating", "judgment_id": "judgment-1", "review_id": "review-1", "skill": "drift-audit", "score": 2}
                ],
            }
        ]
        run_dir = self._run_dir(tmp_path, slices=run_state_slices, events=[])
        slices = [{"slice": 1, "reviews": [], "attempt_trajectory": []}]
        block, problems = mr.resolve_pm_judgments(run_dir, "run-1", slices)
        assert len(problems) == 1
        assert "no origin_event.index" in problems[0]
        assert "could not determine whether its attempt was graded" in problems[0]

    def test_dangling_review_id_with_unresolvable_ordinal_falls_back_to_named_unresolvable(self, tmp_path: Path) -> None:
        # origin_event.index names an event that is not itself, or does not
        # come after, any launch-family event for this slice --
        # bench_lib.attempt_ordinal raises, and that must surface as its own
        # named "could not resolve" problem, never a guessed case 1.
        events = [{"kind": "init"}, {"kind": "review", "slice": "Slice 1"}]
        run_state_slices = [
            {
                "id": "Slice 1",
                "reviews": [
                    {"review_id": "review-1", "skill": "drift-audit", "origin_event": {"index": 1, "kind": "review", "slice": "Slice 1"}}
                ],
                "review_judgments": [
                    {"assessment": "rating", "judgment_id": "judgment-1", "review_id": "review-1", "skill": "drift-audit", "score": 2}
                ],
            }
        ]
        run_dir = self._run_dir(tmp_path, slices=run_state_slices, events=events)
        slices = [{"slice": 1, "reviews": [], "attempt_trajectory": []}]
        block, problems = mr.resolve_pm_judgments(run_dir, "run-1", slices)
        assert len(problems) == 1
        assert "could not resolve" in problems[0]
        assert "no launch/relaunch/steer event found" in problems[0]

    def test_skill_mismatch_is_a_named_problem(self, tmp_path: Path) -> None:
        run_state_slices = [
            {
                "id": "Slice 1",
                "review_judgments": [
                    {"assessment": "rating", "judgment_id": "judgment-1", "review_id": "review-1", "skill": "code-review", "score": 1}
                ],
            }
        ]
        run_dir = self._run_dir(tmp_path, slices=run_state_slices, events=[])
        slices = [{"slice": 1, "reviews": [self._review(review_id="review-1", skill="drift-audit")], "attempt_trajectory": []}]
        block, problems = mr.resolve_pm_judgments(run_dir, "run-1", slices)
        assert len(problems) == 1
        assert "skill" in problems[0]
        assert slices[0]["reviews"][0]["pm_rating"]["status"] == "unjudged"

    def test_duplicate_rating_for_one_review_is_a_named_problem(self, tmp_path: Path) -> None:
        run_state_slices = [
            {
                "id": "Slice 1",
                "review_judgments": [
                    {"assessment": "rating", "judgment_id": "judgment-1", "review_id": "review-1", "skill": "drift-audit", "score": 2},
                    {"assessment": "rating", "judgment_id": "judgment-2", "review_id": "review-1", "skill": "drift-audit", "score": 0},
                ],
            }
        ]
        run_dir = self._run_dir(tmp_path, slices=run_state_slices, events=[])
        slices = [{"slice": 1, "reviews": [self._review(review_id="review-1")], "attempt_trajectory": []}]
        block, problems = mr.resolve_pm_judgments(run_dir, "run-1", slices)
        assert len(problems) == 1
        assert "duplicate" in problems[0]
        # First-processed judgment wins; never silently overwritten.
        assert slices[0]["reviews"][0]["pm_rating"]["score"] == 2

    def test_unavailable_shape_c_marks_the_review_unavailable_never_a_zero(self, tmp_path: Path) -> None:
        # Trial 11 Slice 1 judgment-4's real shape.
        run_state_slices = [
            {
                "id": "Slice 1",
                "review_judgments": [
                    {
                        "assessment": "rating",
                        "judgment_id": "judgment-4",
                        "review_ids": ["review-1"],
                        "skill": "drift-audit",
                        "status": "unavailable",
                        "reason": "Reviewer subprocess failed to read the pinned diff file.",
                        "at": "2026-09-14T06:29:33Z",
                    }
                ],
            }
        ]
        run_dir = self._run_dir(tmp_path, slices=run_state_slices, events=[])
        slices = [{"slice": 1, "reviews": [self._review(review_id="review-1")], "attempt_trajectory": []}]
        block, problems = mr.resolve_pm_judgments(run_dir, "run-1", slices)
        assert problems == []
        rating = slices[0]["reviews"][0]["pm_rating"]
        assert rating["status"] == "unavailable"
        assert rating["score"] is None
        assert "pinned diff file" in rating["reason"]

    def test_comparison_singleton_panel_is_resolved_with_reviewer_identity(self, tmp_path: Path) -> None:
        run_state_slices = [
            {
                "id": "Slice 1",
                "review_judgments": [
                    {
                        "assessment": "comparison",
                        "judgment_id": "judgment-6",
                        "skill": "code-review",
                        "rank_groups": [["review-5"]],
                        "reason": "Singleton panel.",
                        "at": "2026-09-14T04:48:38Z",
                    }
                ],
            }
        ]
        run_dir = self._run_dir(tmp_path, slices=run_state_slices, events=[])
        slices = [
            {
                "slice": 1,
                "reviews": [self._review(review_id="review-5", skill="code-review", tool="opencode", model="m1", effort="low")],
                "attempt_trajectory": [],
            }
        ]
        block, problems = mr.resolve_pm_judgments(run_dir, "run-1", slices)
        assert problems == []
        assert block["comparisons"] == [
            {
                "slice": "Slice 1",
                "skill": "code-review",
                "judgment_id": "judgment-6",
                "at": "2026-09-14T04:48:38Z",
                "reason": "Singleton panel.",
                "rank_groups": [[{"review_id": "review-5", "tool": "opencode", "model": "m1", "effort": "low"}]],
            }
        ]

    def test_comparison_member_resolves_from_run_json_when_its_attempt_was_never_graded(self, tmp_path: Path) -> None:
        # Trial 13 Slice 1's real shape. Its G16 walk was refused, so the
        # four reviews of the earlier round have no scoring-sheet rows and
        # never reach this report's own harvested `reviews`. A comparison
        # needs only the reviewer's IDENTITY, which run.json records for
        # every commission -- so the round must survive intact. Resolving
        # through harvested records alone dropped all four members and the
        # whole round vanished, scoring these reviewers over three of PM's
        # four comparisons and letting a Developer property (commit habits)
        # contaminate a reviewer metric.
        run_state_slices = [
            {
                "id": "Slice 1",
                "reviews": [
                    {"review_id": "review-a", "skill": "code-review", "tool": "opencode", "model": "a", "effort": "xhigh"},
                    {"review_id": "review-b", "skill": "code-review", "tool": "opencode", "model": "b", "effort": "xhigh"},
                ],
                "review_judgments": [
                    {"assessment": "comparison", "judgment_id": "judgment-1", "skill": "code-review", "rank_groups": [["review-a"], ["review-b"]]}
                ],
            }
        ]
        run_dir = self._run_dir(tmp_path, slices=run_state_slices, events=[])
        # Neither review was harvested -- the ungraded-attempt case.
        slices = [{"slice": 1, "reviews": [], "attempt_trajectory": []}]
        block, problems = mr.resolve_pm_judgments(run_dir, "run-1", slices)
        assert problems == []
        groups = block["comparisons"][0]["rank_groups"]
        assert [[m["review_id"] for m in g] for g in groups] == [["review-a"], ["review-b"]]
        assert [[m["model"] for m in g] for g in groups] == [["a"], ["b"]]

    def test_comparison_member_with_a_disagreeing_skill_is_a_named_problem(self, tmp_path: Path) -> None:
        run_state_slices = [
            {
                "id": "Slice 1",
                "reviews": [{"review_id": "review-a", "skill": "drift-audit", "tool": "opencode", "model": "a", "effort": None}],
                "review_judgments": [
                    {"assessment": "comparison", "judgment_id": "judgment-1", "skill": "code-review", "rank_groups": [["review-a"]]}
                ],
            }
        ]
        run_dir = self._run_dir(tmp_path, slices=run_state_slices, events=[])
        slices = [{"slice": 1, "reviews": [], "attempt_trajectory": []}]
        block, problems = mr.resolve_pm_judgments(run_dir, "run-1", slices)
        assert len(problems) == 1
        assert "disagrees with review 'review-a'" in problems[0]
        assert block["comparisons"][0]["rank_groups"] == [[]]

    def test_comparison_panel_of_two_resolves_both_groups(self, tmp_path: Path) -> None:
        run_state_slices = [
            {
                "id": "Slice 1",
                "review_judgments": [
                    {"assessment": "comparison", "judgment_id": "judgment-1", "skill": "code-review", "rank_groups": [["review-a"], ["review-b"]]}
                ],
            }
        ]
        run_dir = self._run_dir(tmp_path, slices=run_state_slices, events=[])
        slices = [
            {
                "slice": 1,
                "reviews": [
                    self._review(review_id="review-a", skill="code-review", model="a"),
                    self._review(review_id="review-b", skill="code-review", model="b"),
                ],
                "attempt_trajectory": [],
            }
        ]
        block, problems = mr.resolve_pm_judgments(run_dir, "run-1", slices)
        assert problems == []
        groups = block["comparisons"][0]["rank_groups"]
        assert len(groups) == 2
        assert [g[0]["review_id"] for g in groups] == ["review-a", "review-b"]

    def test_comparison_panel_of_three_with_a_tied_group_resolves_every_id(self, tmp_path: Path) -> None:
        run_state_slices = [
            {
                "id": "Slice 1",
                "review_judgments": [
                    {
                        "assessment": "comparison",
                        "judgment_id": "judgment-1",
                        "skill": "code-review",
                        "rank_groups": [["review-a"], ["review-b", "review-c"]],
                    }
                ],
            }
        ]
        run_dir = self._run_dir(tmp_path, slices=run_state_slices, events=[])
        slices = [
            {
                "slice": 1,
                "reviews": [
                    self._review(review_id="review-a", skill="code-review", model="a"),
                    self._review(review_id="review-b", skill="code-review", model="b"),
                    self._review(review_id="review-c", skill="code-review", model="c"),
                ],
                "attempt_trajectory": [],
            }
        ]
        block, problems = mr.resolve_pm_judgments(run_dir, "run-1", slices)
        assert problems == []
        groups = block["comparisons"][0]["rank_groups"]
        assert [g["review_id"] for g in groups[0]] == ["review-a"]
        assert {g["review_id"] for g in groups[1]} == {"review-b", "review-c"}

    def test_rank_groups_naming_an_unknown_review_is_a_named_problem(self, tmp_path: Path) -> None:
        run_state_slices = [
            {
                "id": "Slice 1",
                "review_judgments": [
                    {"assessment": "comparison", "judgment_id": "judgment-1", "skill": "code-review", "rank_groups": [["review-ghost"]]}
                ],
            }
        ]
        run_dir = self._run_dir(tmp_path, slices=run_state_slices, events=[])
        slices = [{"slice": 1, "reviews": [], "attempt_trajectory": []}]
        block, problems = mr.resolve_pm_judgments(run_dir, "run-1", slices)
        assert len(problems) == 1
        assert "review-ghost" in problems[0]
        assert block["comparisons"][0]["rank_groups"] == [[]]

    def test_developer_judgment_joins_via_the_plus_one_ordinal_single_launch_event(self, tmp_path: Path) -> None:
        # Trial 11 Slice 2's real shape: origin_event.index is the slice's
        # ONLY launch-family event -- the strict (no +1) form raises
        # BenchLibError here (re-derived directly against the real data);
        # the +1 form correctly resolves to attempt ordinal 0.
        events = [{"kind": "init"}, {"kind": "launch", "slice": "Slice 1"}, {"kind": "launch", "slice": "Slice 2"}]
        run_state_slices = [
            {
                "id": "Slice 2",
                "developer_judgments": [
                    {
                        "judgment_id": "developer-judgment-1",
                        "score": 2,
                        "reason": "correct",
                        "at": "2026-09-14T06:40:30Z",
                        "submission": {"origin_event": {"index": 2, "kind": "launch", "slice": "Slice 2"}},
                    }
                ],
            }
        ]
        run_dir = self._run_dir(tmp_path, slices=run_state_slices, events=events)
        slices = [{"slice": 2, "reviews": [], "attempt_trajectory": [{"attempt": 0}]}]
        block, problems = mr.resolve_pm_judgments(run_dir, "run-1", slices)
        assert problems == []
        assert block["developer_judgments_recorded"] is True
        assert slices[0]["attempt_trajectory"][0]["pm_developer_judgment"] == {
            "status": "rated",
            "score": 2,
            "reason": "correct",
            "at": "2026-09-14T06:40:30Z",
            "judgment_id": "developer-judgment-1",
        }

    def test_developer_judgment_at_a_steer_joins_the_steered_attempt_not_the_prior_one(self, tmp_path: Path) -> None:
        # Trial 10 Slice 1's real shape: origin_event is a `steer` (index 4),
        # the SECOND launch-family event for the slice -- must resolve to
        # attempt ordinal 1, never 0 (the strict, no-+1 form would give 0).
        events = [
            {"kind": "init"},
            {"kind": "launch", "slice": "Slice 1"},
            {"kind": "review", "slice": "Slice 1"},
            {"kind": "review", "slice": "Slice 1"},
            {"kind": "steer", "slice": "Slice 1"},
        ]
        run_state_slices = [
            {
                "id": "Slice 1",
                "developer_judgments": [
                    {
                        "judgment_id": "developer-judgment-1",
                        "score": 1,
                        "reason": "steered fix",
                        "submission": {"origin_event": {"index": 4, "kind": "steer", "slice": "Slice 1"}},
                    }
                ],
            }
        ]
        run_dir = self._run_dir(tmp_path, slices=run_state_slices, events=events)
        slices = [{"slice": 1, "reviews": [], "attempt_trajectory": [{"attempt": 0}, {"attempt": 1}]}]
        block, problems = mr.resolve_pm_judgments(run_dir, "run-1", slices)
        assert problems == []
        assert slices[0]["attempt_trajectory"][0]["pm_developer_judgment"]["status"] == "unjudged"
        assert slices[0]["attempt_trajectory"][1]["pm_developer_judgment"]["status"] == "rated"

    def test_superseded_developer_judgment_is_ignored_only_the_successor_counts(self, tmp_path: Path) -> None:
        # Trial 10 Slice 1's real shape: developer-judgment-2 supersedes
        # developer-judgment-1, judging the SAME submission -- only the
        # successor's score must land on the attempt.
        events = [{"kind": "init"}, {"kind": "launch", "slice": "Slice 1"}, {"kind": "steer", "slice": "Slice 1"}]
        run_state_slices = [
            {
                "id": "Slice 1",
                "developer_judgments": [
                    {
                        "judgment_id": "developer-judgment-1",
                        "score": 1,
                        "reason": "first pass",
                        "submission": {"origin_event": {"index": 2, "kind": "steer", "slice": "Slice 1"}},
                    },
                    {
                        "judgment_id": "developer-judgment-2",
                        "score": 2,
                        "reason": "corrected",
                        "supersedes": "developer-judgment-1",
                        "submission": {"origin_event": {"index": 2, "kind": "steer", "slice": "Slice 1"}},
                    },
                ],
            }
        ]
        run_dir = self._run_dir(tmp_path, slices=run_state_slices, events=events)
        slices = [{"slice": 1, "reviews": [], "attempt_trajectory": [{"attempt": 0}, {"attempt": 1}]}]
        block, problems = mr.resolve_pm_judgments(run_dir, "run-1", slices)
        assert problems == []
        rated = slices[0]["attempt_trajectory"][1]["pm_developer_judgment"]
        assert rated["score"] == 2
        assert rated["judgment_id"] == "developer-judgment-2"

    def test_origin_event_not_launch_family_is_a_named_problem(self, tmp_path: Path) -> None:
        events = [{"kind": "init"}, {"kind": "launch", "slice": "Slice 1"}, {"kind": "review", "slice": "Slice 1"}]
        run_state_slices = [
            {
                "id": "Slice 1",
                "developer_judgments": [
                    {
                        "judgment_id": "developer-judgment-1",
                        "score": 1,
                        "submission": {"origin_event": {"index": 2, "kind": "review", "slice": "Slice 1"}},
                    }
                ],
            }
        ]
        run_dir = self._run_dir(tmp_path, slices=run_state_slices, events=events)
        slices = [{"slice": 1, "reviews": [], "attempt_trajectory": [{"attempt": 0}]}]
        block, problems = mr.resolve_pm_judgments(run_dir, "run-1", slices)
        assert len(problems) == 1
        assert "not a launch/relaunch/steer event" in problems[0]
        assert slices[0]["attempt_trajectory"][0]["pm_developer_judgment"]["status"] == "unjudged"

    def test_attempt_never_rated_by_pm_stays_explicitly_unjudged(self, tmp_path: Path) -> None:
        run_dir = self._run_dir(tmp_path, slices=[{"id": "Slice 1"}], events=[{"kind": "launch", "slice": "Slice 1"}])
        slices = [{"slice": 1, "reviews": [], "attempt_trajectory": [{"attempt": 0}]}]
        block, problems = mr.resolve_pm_judgments(run_dir, "run-1", slices)
        assert problems == []
        assert slices[0]["attempt_trajectory"][0]["pm_developer_judgment"]["status"] == "unjudged"

    def test_judgments_for_a_slice_with_no_scoring_sheet_coverage_is_a_named_problem(self, tmp_path: Path) -> None:
        run_state_slices = [
            {
                "id": "Slice 9",
                "review_judgments": [
                    {"assessment": "rating", "judgment_id": "j-1", "review_id": "r-1", "skill": "drift-audit", "score": 1}
                ],
            }
        ]
        run_dir = self._run_dir(tmp_path, slices=run_state_slices, events=[])
        slices = [{"slice": 1, "reviews": [], "attempt_trajectory": []}]
        block, problems = mr.resolve_pm_judgments(run_dir, "run-1", slices)
        assert len(problems) == 1
        assert "Slice 9" in problems[0]
        assert "no scoring-sheet coverage" in problems[0]


def _vendor_obligations(root: Path) -> None:
    """Copy this repo's real `hidden_tests/obligations.yaml` under a fake
    `bench_root()` -- `TestMain` monkeypatches `bench_root` to an isolated
    `tmp_path` for every other purpose, but `build_report` now also loads
    obligations from it (`dev_check.load_obligations`), so that fake root
    needs the real rubric map too."""
    real = REPO_ROOT / "hidden_tests" / "obligations.yaml"
    fake = root / "hidden_tests" / "obligations.yaml"
    fake.parent.mkdir(parents=True, exist_ok=True)
    fake.write_text(real.read_text(encoding="utf-8"), encoding="utf-8")


class TestMain:
    def test_writes_report_and_returns_0_on_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        root = tmp_path / "bench-root"
        sheets_dir = root / "results" / "runs" / "run-1"
        _write_sheet(sheets_dir, 1, _sheet("run-1", 1))
        _vendor_obligations(root)
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
        _vendor_obligations(root)
        monkeypatch.setattr(mr, "bench_root", lambda: root)

        assert mr.main(["--run-id", "run-1"]) == 1

    def test_run_dir_flag_populates_the_timing_block(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        root = tmp_path / "bench-root"
        sheets_dir = root / "results" / "runs" / "run-1"
        _write_sheet(sheets_dir, 1, _sheet("run-1", 1))
        _vendor_obligations(root)
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
