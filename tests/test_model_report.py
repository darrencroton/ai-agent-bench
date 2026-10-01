"""Tests for tools/model_report.py (one model's full run, reshaped into a report).

Fixtures are hand-written scoring sheets under `tmp_path`, matching the real
shape `dev_check.py`/`review_score.py` write.
No git, no subprocess: this tool only reads already-graded JSON/Markdown
already on disk.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Callable

import pytest
import yaml

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
    identity_correction: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """A `reviews` list record shaped like review_score.py's real
    `build_record` output (tools/review_score.py) -- including every field
    it carries (`review_id`/`skill`/`tool`/`model`/`effort`/`head`/
    `before_head`/`at`/`event_index`/`report_ref`/`report_sha256`/
    `superseded_by`, and `identity_correction` when given). No `commissioned`
    key at all -- every record in a `reviews` list is unconditionally a
    commission.
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
    if identity_correction is not None:
        record["identity_correction"] = identity_correction
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
    real output -- just the fields model_report.py's own tests exercise
    (baseline_commit, metric_version, and each bucket's `net`/`available`),
    not the full binary_files/function_count/coverage_note shape
    dev_check.py's own tests already cover."""
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
    provenance: dict[str, Any] | None = None,
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
    if provenance is not None:
        entry["provenance"] = provenance
    return entry


def _provenance(*, task_id: str | None = "relative-velocity") -> dict[str, Any]:
    """An attempt's provenance block shaped like dev_check.build_provenance's
    real output; pass task_id=None for a sheet graded without task
    stamping -- no task_id key at all."""
    block: dict[str, Any] = {}
    if task_id is not None:
        block["task_id"] = task_id
    block.update(
        {
            "plan_hash": "plan-hash",
            "policy_hash": "policy-hash",
            "obligations_hash": "obligations-hash",
            "hidden_tests_hash": "hidden-tests-hash",
            "base_commit": "before-head",
            "pm_skill_version": None,
        }
    )
    return block


def _task_entry(**overrides: Any) -> dict[str, Any]:
    """One complete tasks: registry entry -- every key bench_lib.resolve_task
    validates -- mirroring this repo's own relative-velocity entry in
    policy.yaml (the values are irrelevant to model_report.py, which only
    ever reads obligations_file out of a resolved entry)."""
    entry = {
        "repo": "substrate/relative-velocity",
        "branch_prefix": "pm-eval-v2",
        "worktree_root": None,
        "plan_file": "docs/MERGER_RATE_PLAN-2SLICE.md",
        "provenance_file": "docs/MERGER_RATE_PLAN-2SLICE.provenance.md",
        "hidden_tests_dir": "hidden_tests",
        "obligations_file": "hidden_tests/obligations.yaml",
        "mutations_dir": "hidden_tests/mutations",
        "expected_slices": 2,
        "measurement": {
            "production_paths": ["src/**/*.py"],
            "test_paths": ["tests/**/*.py"],
            "doc_paths": ["docs/**/*.md", "*.md"],
        },
    }
    entry.update(overrides)
    return entry


def _policy(*, default_task: str = "relative-velocity", tasks: dict[str, Any] | None = None) -> dict[str, Any]:
    """A minimal-but-complete parsed policy mapping for build_report's task
    resolution -- the same shape main() hands it after load_policy."""
    if tasks is None:
        tasks = {"relative-velocity": _task_entry()}
    return {"default_task": default_task, "tasks": tasks}


def _developer(
    *,
    model: str = "opencode/some-model",
    harness: str = "opencode",
    effort: str | None = "low",
    attributed: bool = True,
) -> dict[str, Any]:
    """The structured identity block dev_check.py writes onto a sheet, in
    place of a flat `model` string."""
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
        report, problems = mr.build_report(sheets, "run-1", policy=_policy())

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
        # Every `reviews` entry carries a `pm_rating` field -- "unjudged"
        # here, since this report was built with no `run_dir` (so no
        # run.json to harvest a real PM judgment from).
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
        report, _problems = mr.build_report(sheets, "run-1", policy=_policy())
        assert report["slices"][0]["accepted_at_attempt"] is None
        assert report["slices"][0]["first_attempt"]["attempt"] == 0
        assert report["slices"][0]["final_attempt"]["attempt"] == 1

    def test_attempts_total_uses_final_ordinal_not_row_count_under_walk_fallback(self, tmp_path: Path) -> None:
        # When the per-attempt commit walk falls back to grading only a
        # slice's final attempt, the sheet can
        # hold just one row -- its true final attempt -- even though PM ran
        # 5 attempts; grade_run.py still records that row's real ordinal
        # (4), so attempts_total must read 5, not 1.
        attempts = [_attempt(4, pm_decision="accept")]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=4))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1", policy=_policy())
        assert report["slices"][0]["attempts_total"] == 5
        # No attempt-0 row survived the walk's fallback -- first_attempt is
        # an honest None, never substituted with whatever row IS present.
        assert report["slices"][0]["first_attempt"] is None

    def test_review_trend_preserves_parse_error_verbatim(self, tmp_path: Path) -> None:
        attempts = [_attempt(0, reviews=[_review_record(parse_error="unrecognised report header")])]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=0))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1", policy=_policy())
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
        # review_score.py harvests review_id/effort/event_index for real --
        # this must pass them through, not read them as None.
        attempts = [_attempt(0, reviews=[_review_record(review_id="review-2", effort="low", event_index=15)])]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=0))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1", policy=_policy())
        drift_entry = report["slices"][0]["reviews"][0]
        assert drift_entry["review_id"] == "review-2"
        assert drift_entry["effort"] == "low"
        assert drift_entry["event_index"] == 15

    def test_review_entry_carries_identity_correction_when_present(self, tmp_path: Path) -> None:
        correction = {"model": "opencode-go/mimo-v2.5", "effort": "default", "reason": "r", "evidence": "e"}
        attempts = [_attempt(0, reviews=[_review_record(event_index=9, identity_correction=correction)])]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=0))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1", policy=_policy())
        assert report["slices"][0]["reviews"][0]["identity_correction"] == correction

    def test_review_entry_omits_identity_correction_when_absent(self, tmp_path: Path) -> None:
        attempts = [_attempt(0, reviews=[_review_record(event_index=9)])]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=0))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1", policy=_policy())
        assert "identity_correction" not in report["slices"][0]["reviews"][0]

    def test_review_entry_carries_superseded_by(self, tmp_path: Path) -> None:
        attempts = [_attempt(0, reviews=[_review_record(event_index=14, superseded_by=15, parse_error="no report")])]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=0))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1", policy=_policy())
        assert report["slices"][0]["reviews"][0]["superseded_by"] == 15

    def test_reviews_are_sorted_by_attempt_regardless_of_sheet_file_order(self, tmp_path: Path) -> None:
        attempts = [
            _attempt(1, reviews=[_review_record(event_index=1, verdict="PASS", open_after_this_attempt=0)]),
            _attempt(0, reviews=[_review_record(event_index=0, verdict="FAIL", open_after_this_attempt=1)]),
        ]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=1))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1", policy=_policy())
        assert [entry["attempt"] for entry in report["slices"][0]["reviews"]] == [0, 1]

    def test_two_reviewers_on_one_attempt_both_appear_in_the_flat_list(self, tmp_path: Path) -> None:
        """A panel: two reviewers commissioned on one attempt both stand as
        their own record, neither superseded."""
        attempts = [
            _attempt(0, reviews=[
                _review_record(event_index=0, tool="claude", model="model-a"),
                _review_record(event_index=1, tool="opencode", model="model-b"),
            ]),
        ]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=0))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1", policy=_policy())
        reviews = report["slices"][0]["reviews"]
        assert len(reviews) == 2
        assert {r["model"] for r in reviews} == {"model-a", "model-b"}
        assert all(r["superseded_by"] is None for r in reviews)

    def test_disagreeing_developer_block_across_sheets_is_a_named_error(self, tmp_path: Path) -> None:
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, model="model-a"))
        _write_sheet(tmp_path, 2, _sheet("run-1", 2, model="model-b"))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        with pytest.raises(mr.ModelReportError, match="disagree on 'developer'"):
            mr.build_report(sheets, "run-1", policy=_policy())

    def test_none_vs_non_null_stop_reason_across_sheets_is_a_named_error(self, tmp_path: Path) -> None:
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, stop_reason=None))
        _write_sheet(tmp_path, 2, _sheet("run-1", 2, stop_reason="done"))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        with pytest.raises(mr.ModelReportError, match="disagree on 'run_status.stop_reason'"):
            mr.build_report(sheets, "run-1", policy=_policy())

    def test_disagreeing_performance_ref_across_sheets_is_a_named_error(self, tmp_path: Path) -> None:
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, pm_model_performance_ref="/path/a.md"))
        _write_sheet(tmp_path, 2, _sheet("run-1", 2, pm_model_performance_ref="/path/b.md"))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        with pytest.raises(mr.ModelReportError, match="pm_model_performance_ref"):
            mr.build_report(sheets, "run-1", policy=_policy())

    def test_never_recorded_rating_is_not_a_problem(self, tmp_path: Path) -> None:
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, pm_model_performance_ref=None))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, problems = mr.build_report(sheets, "run-1", policy=_policy())
        assert report["pm_subjective_rating"] == {"available": False, "ref": None, "text": None}
        assert problems == []

    def test_missing_referenced_rating_file_is_a_named_problem(self, tmp_path: Path) -> None:
        missing = tmp_path / "gone.md"
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, pm_model_performance_ref=str(missing)))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, problems = mr.build_report(sheets, "run-1", policy=_policy())
        assert report["pm_subjective_rating"] == {"available": False, "ref": str(missing), "text": None}
        assert len(problems) == 1
        assert "does not exist on disk" in problems[0]
        assert report["problems"] == problems


class TestAttemptTrajectory:
    def test_includes_an_attempt_steered_with_no_commissioned_review(self, tmp_path: Path) -> None:
        # An attempt steered with no review commissioned at all must still
        # appear in the trajectory -- `reviews` alone would omit it
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
        report, _problems = mr.build_report(sheets, "run-1", policy=_policy())

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
        report, _problems = mr.build_report(sheets, "run-1", policy=_policy())

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
        report, _problems = mr.build_report(sheets, "run-1", policy=_policy())
        assert [e["attempt"] for e in report["slices"][0]["attempt_trajectory"]] == [0, 1]

    def test_size_complexity_summary_is_a_compact_row_not_the_full_block(self, tmp_path: Path) -> None:
        attempts = [_attempt(0, size_complexity=_size_complexity(production_loc_net=7, production_cc_net=-2))]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=0))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1", policy=_policy())

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
        report, _problems = mr.build_report(sheets, "run-1", policy=_policy())

        entry = report["slices"][0]["attempt_trajectory"][0]
        assert entry["size_complexity"] == {
            "loc_available": False,
            "production_loc_net": None,
            "cc_available": False,
            "production_cc_net": None,
        }

    def test_an_attempt_with_no_size_complexity_block_at_all_reads_unavailable(self, tmp_path: Path) -> None:
        # A sheet with no size_complexity block recorded -- absent, not a
        # KeyError.
        attempts = [_attempt(0)]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=0))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1", policy=_policy())
        entry = report["slices"][0]["attempt_trajectory"][0]
        assert entry["size_complexity"]["loc_available"] is False
        assert entry["size_complexity"]["cc_available"] is False


class TestFirstAttemptNodeOutcomes:
    """The one per-slice node map model-report.json carries -- the first
    attempt's `by_node`, nested `{group_id: {node_id: outcome}}`. The full
    per-attempt `by_node` map itself never appears in this report."""

    def test_by_node_absent_from_first_attempt_final_attempt_and_every_trajectory_row(self, tmp_path: Path) -> None:
        attempts = [_attempt(0), _attempt(1, pm_decision="accept")]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=1))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, problems = mr.build_report(sheets, "run-1", policy=_policy())
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
        report, problems = mr.build_report(sheets, "run-1", policy=_policy())
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
        report, problems = mr.build_report(sheets, "run-1", policy=_policy())
        assert problems == []

        slice_entry = report["slices"][0]
        assert slice_entry["has_attempt_zero"] is False
        assert slice_entry["first_attempt_node_outcomes"] is None

    def test_malformed_by_node_shape_is_a_named_model_report_error(self, tmp_path: Path) -> None:
        # by_node recorded as a list, not a {node_id: outcome} mapping, must
        # raise a named ModelReportError naming the concrete sheet, never a
        # bare AttributeError from deep inside the reconstruction.
        correctness = _correctness_for_slice(1)
        correctness["by_node"] = ["passed"]
        attempts = [_attempt(0, correctness=correctness)]
        sheet_path = _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=0))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        with pytest.raises(mr.ModelReportError, match=re.escape(str(sheet_path))):
            mr.build_report(sheets, "run-1", policy=_policy())

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
            mr.build_report(sheets, "run-1", policy=_policy())

    def test_malformed_by_node_outcome_value_is_a_named_model_report_error(self, tmp_path: Path) -> None:
        correctness = _correctness_for_slice(1)
        first_node = next(iter(correctness["by_node"]))
        correctness["by_node"][first_node] = "not-a-real-outcome"
        attempts = [_attempt(0, correctness=correctness)]
        sheet_path = _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=0))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        with pytest.raises(mr.ModelReportError, match=re.escape(str(sheet_path))):
            mr.build_report(sheets, "run-1", policy=_policy())

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
            mr.build_report(sheets, "run-1", policy=_policy())


class TestBaselineResetLabelling:
    """In a stop/restart case the stored grading baseline may have reset;
    that case is labelled, never quietly reused as an apparent
    first-to-final improvement."""

    def test_same_baseline_across_first_and_final_attempt_is_not_flagged(self, tmp_path: Path) -> None:
        attempts = [
            _attempt(0, size_complexity=_size_complexity(baseline_commit="base-x")),
            _attempt(1, pm_decision="accept", size_complexity=_size_complexity(baseline_commit="base-x")),
        ]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=1))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, problems = mr.build_report(sheets, "run-1", policy=_policy())
        assert report["slices"][0]["size_complexity_baseline_reset"] is False
        assert problems == []

    def test_a_differing_baseline_between_first_and_final_attempt_is_flagged_and_named(self, tmp_path: Path) -> None:
        attempts = [
            _attempt(0, size_complexity=_size_complexity(baseline_commit="base-BEFORE-restart")),
            _attempt(1, pm_decision="accept", size_complexity=_size_complexity(baseline_commit="base-AFTER-restart")),
        ]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=1))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, problems = mr.build_report(sheets, "run-1", policy=_policy())

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
        report, problems = mr.build_report(sheets, "run-1", policy=_policy())
        assert report["slices"][0]["size_complexity_baseline_reset"] is False
        assert problems == []


class TestMeasurementMetricVersion:
    def test_a_single_agreed_metric_version_is_carried_through(self, tmp_path: Path) -> None:
        attempts = [_attempt(0, size_complexity=_size_complexity(metric_version=1))]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=0))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, problems = mr.build_report(sheets, "run-1", policy=_policy())
        assert report["measurement_metric_version"] == 1
        assert problems == []

    def test_no_size_complexity_data_anywhere_is_none_not_an_error(self, tmp_path: Path) -> None:
        attempts = [_attempt(0)]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=0))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, problems = mr.build_report(sheets, "run-1", policy=_policy())
        assert report["measurement_metric_version"] is None
        assert problems == []

    def test_disagreeing_metric_versions_across_the_run_are_a_named_problem(self, tmp_path: Path) -> None:
        attempts = [
            _attempt(0, size_complexity=_size_complexity(metric_version=1)),
            _attempt(1, pm_decision="accept", size_complexity=_size_complexity(metric_version=2)),
        ]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=1))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, problems = mr.build_report(sheets, "run-1", policy=_policy())
        assert report["measurement_metric_version"] is None
        assert any("metric_version" in p and "run-1" in p for p in problems)


class TestTaskIdPropagation:
    """Top-level task_id/task_id_source derivation from the sheets' own
    attempt provenance, including the backfill to the policy's default_task
    for sheets with no stamped task_id."""

    def test_graded_sheets_carry_their_recorded_task_id_with_source_graded(self, tmp_path: Path) -> None:
        attempts = [
            _attempt(0, pm_decision="steer", provenance=_provenance()),
            _attempt(1, pm_decision="accept", provenance=_provenance()),
        ]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=1))
        _write_sheet(
            tmp_path,
            2,
            _sheet(
                "run-1",
                2,
                attempts=[_attempt(0, pm_decision="accept", slice_number=2, provenance=_provenance())],
            ),
        )
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, problems = mr.build_report(sheets, "run-1", policy=_policy())
        assert problems == []
        assert report["task_id"] == "relative-velocity"
        assert report["task_id_source"] == "graded"
        # The per-slice echo lands on every correctness_provenance block.
        assert all(s["correctness_provenance"]["task_id"] == "relative-velocity" for s in report["slices"])

    def test_unstamped_sheets_backfill_to_default_task_with_source_backfilled(self, tmp_path: Path) -> None:
        # No provenance at all.
        _write_sheet(tmp_path, 1, _sheet("run-1", 1))
        # Provenance present but carrying no task_id key.
        attempts = [_attempt(0, slice_number=2, provenance=_provenance(task_id=None))]
        _write_sheet(tmp_path, 2, _sheet("run-1", 2, attempts=attempts))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, problems = mr.build_report(sheets, "run-1", policy=_policy())
        assert problems == []
        assert report["task_id"] == "relative-velocity"
        assert report["task_id_source"] == "backfilled"

    def test_backfill_follows_the_policys_own_default_task_not_a_hardcoded_one(self, tmp_path: Path) -> None:
        tasks = {
            "relative-velocity": _task_entry(),
            "second-task": _task_entry(repo="substrate/other-repo"),
        }
        _write_sheet(tmp_path, 1, _sheet("run-1", 1))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, problems = mr.build_report(
            sheets, "run-1", policy=_policy(default_task="second-task", tasks=tasks)
        )
        assert problems == []
        assert report["task_id"] == "second-task"
        assert report["task_id_source"] == "backfilled"

    def test_broken_default_entry_does_not_block_a_run_stamped_under_another_task(self, tmp_path: Path) -> None:
        # Only the run's own task entry is resolved in full; the default entry
        # is validated only when an unstamped sheet actually backfills to it.
        broken_default = _task_entry()
        del broken_default["plan_file"]
        tasks = {"relative-velocity": broken_default, "second-task": _task_entry(repo="substrate/other-repo")}
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=[_attempt(0, provenance=_provenance(task_id="second-task"))]))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1", policy=_policy(tasks=tasks))
        assert report["task_id"] == "second-task"
        assert report["task_id_source"] == "graded"

        _write_sheet(tmp_path, 1, _sheet("run-1", 1))  # unstamped: backfills to the broken default
        with pytest.raises(mr.ModelReportError, match="'relative-velocity'.*plan_file"):
            mr.build_report(mr.discover_sheets(tmp_path, "run-1"), "run-1", policy=_policy(tasks=tasks))

    def test_cross_slice_disagreement_is_a_named_error_naming_run_and_values(self, tmp_path: Path) -> None:
        tasks = {"relative-velocity": _task_entry(), "second-task": _task_entry()}
        _write_sheet(
            tmp_path, 1, _sheet("run-1", 1, attempts=[_attempt(0, provenance=_provenance(task_id="relative-velocity"))])
        )
        _write_sheet(
            tmp_path,
            2,
            _sheet(
                "run-1",
                2,
                attempts=[_attempt(0, slice_number=2, provenance=_provenance(task_id="second-task"))],
            ),
        )
        sheets = mr.discover_sheets(tmp_path, "run-1")
        with pytest.raises(mr.ModelReportError) as excinfo:
            mr.build_report(sheets, "run-1", policy=_policy(tasks=tasks))
        message = str(excinfo.value)
        assert "run-1" in message
        assert "'relative-velocity'" in message
        assert "'second-task'" in message

    def test_mixed_graded_and_backfilled_attribution_is_a_named_error(self, tmp_path: Path) -> None:
        # Even though both slices resolve to the SAME id here (the native one
        # happens to equal default_task), mixed attribution is still refused:
        # the report carries ONE run-level source, and a silent mix would
        # make it impossible to say which sheets were actually re-graded.
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=[_attempt(0, provenance=_provenance())]))
        _write_sheet(tmp_path, 2, _sheet("run-1", 2))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        with pytest.raises(mr.ModelReportError) as excinfo:
            mr.build_report(sheets, "run-1", policy=_policy())
        message = str(excinfo.value)
        assert "run-1" in message
        assert "mix" in message

    def test_stamped_and_unstamped_attempts_in_one_slice_is_a_named_error(self, tmp_path: Path) -> None:
        # Attempt 0 was natively graded under second-task; attempt 1's
        # unstamped provenance would backfill to
        # relative-velocity -- two possible rubrics inside one slice, named
        # rather than averaged away.
        attempts = [
            _attempt(0, pm_decision="steer", provenance=_provenance(task_id="second-task")),
            _attempt(1, pm_decision="accept", provenance=_provenance(task_id=None)),
        ]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=1))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        with pytest.raises(mr.ModelReportError) as excinfo:
            mr.build_report(sheets, "run-1", policy=_policy())
        message = str(excinfo.value)
        assert "run-1" in message
        assert "slice 1" in message
        assert "'second-task'" in message
        assert "'relative-velocity'" in message

    def test_middle_attempt_under_another_task_is_a_named_error_naming_the_attempt(self, tmp_path: Path) -> None:
        tasks = {"relative-velocity": _task_entry(), "second-task": _task_entry()}
        attempts = [
            _attempt(0, provenance=_provenance(task_id="relative-velocity")),
            _attempt(1, provenance=_provenance(task_id="second-task")),
            _attempt(2, pm_decision="accept", provenance=_provenance(task_id="relative-velocity")),
        ]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=2))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        with pytest.raises(mr.ModelReportError) as excinfo:
            mr.build_report(sheets, "run-1", policy=_policy(tasks=tasks))
        message = str(excinfo.value)
        assert "run-1" in message
        assert "slice 1" in message
        assert "attempt 1='second-task'" in message
        assert "attempt 0='relative-velocity'" in message

    def test_unstamped_middle_attempt_among_stamped_ones_is_a_named_mixed_error(self, tmp_path: Path) -> None:
        attempts = [
            _attempt(0, provenance=_provenance()),
            _attempt(1, provenance=_provenance(task_id=None)),
            _attempt(2, pm_decision="accept", provenance=_provenance()),
        ]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=2))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        with pytest.raises(mr.ModelReportError) as excinfo:
            mr.build_report(sheets, "run-1", policy=_policy())
        message = str(excinfo.value)
        assert "run-1" in message
        assert "slice 1" in message
        assert "mix" in message
        assert "attempts [1]" in message

    def test_every_attempt_stamped_is_graded_and_every_attempt_unstamped_is_backfilled(self, tmp_path: Path) -> None:
        for task_id, expected_source in (("relative-velocity", "graded"), (None, "backfilled")):
            attempts = [
                _attempt(0, provenance=_provenance(task_id=task_id)),
                _attempt(1, provenance=_provenance(task_id=task_id)),
                _attempt(2, pm_decision="accept", provenance=_provenance(task_id=task_id)),
            ]
            _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=2))
            sheets = mr.discover_sheets(tmp_path, "run-1")
            report, _problems = mr.build_report(sheets, "run-1", policy=_policy())
            assert report["task_id"] == "relative-velocity"
            assert report["task_id_source"] == expected_source

    def test_non_string_recorded_task_id_is_a_named_error(self, tmp_path: Path) -> None:
        attempts = [_attempt(0, provenance={**_provenance(), "task_id": 7})]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        with pytest.raises(mr.ModelReportError, match=r"must be a non-empty string"):
            mr.build_report(sheets, "run-1", policy=_policy())

    def test_explicit_null_recorded_task_id_is_malformed_not_unstamped(self, tmp_path: Path) -> None:
        # Key PRESENT with an explicit JSON null is syntactically valid but
        # malformed: an unstamped provenance omits the key entirely
        # (the backfill case covered by
        # test_unstamped_sheets_backfill_to_default_task_with_source_
        # backfilled), so an explicit null must be refused by name, never
        # silently read as "no id recorded yet".
        attempts = [_attempt(0, provenance={**_provenance(), "task_id": None})]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        with pytest.raises(mr.ModelReportError) as excinfo:
            mr.build_report(sheets, "run-1", policy=_policy())
        message = str(excinfo.value)
        assert "run-1" in message
        assert "slice 1" in message
        assert "attempt 0" in message
        assert "None" in message
        # The contrast on the same sheet minus the key: genuinely absent
        # backfills instead of erroring.
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=[_attempt(0, provenance=_provenance(task_id=None))]))
        report, problems = mr.build_report(mr.discover_sheets(tmp_path, "run-1"), "run-1", policy=_policy())
        assert problems == []
        assert report["task_id"] == "relative-velocity"
        assert report["task_id_source"] == "backfilled"

    def test_non_mapping_provenance_is_a_named_error_not_a_raw_attribute_error(self, tmp_path: Path) -> None:
        # A hand-corrupted sheet whose attempt carries a truthy non-mapping
        # provenance must fail loudly by name -- never escape as the bare
        # AttributeError that reading .get() off the corrupted value would raise.
        attempts = [
            _attempt(0, pm_decision="steer"),
            _attempt(1, pm_decision="accept"),
        ]
        attempts[0]["provenance"] = "corrupted"
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=1))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        with pytest.raises(mr.ModelReportError) as excinfo:
            mr.build_report(sheets, "run-1", policy=_policy())
        message = str(excinfo.value)
        assert "run-1" in message
        assert "slice 1" in message
        assert "attempt 0" in message
        assert "not a mapping" in message
        assert "'corrupted'" in message

    def test_unknown_task_id_in_provenance_fails_loudly_via_resolve_task(self, tmp_path: Path) -> None:
        # A sheet stamped with a task id the registry does not configure must
        # fail through bench_lib.resolve_task's own named error, never fall
        # back to the default or guess.
        _write_sheet(
            tmp_path, 1, _sheet("run-1", 1, attempts=[_attempt(0, provenance=_provenance(task_id="ghost-task"))])
        )
        sheets = mr.discover_sheets(tmp_path, "run-1")
        with pytest.raises(mr.ModelReportError, match=r"unknown task 'ghost-task'"):
            mr.build_report(sheets, "run-1", policy=_policy())

    def test_no_graded_attempts_anywhere_is_a_named_error_not_a_guess(self, tmp_path: Path) -> None:
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=[]))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        with pytest.raises(mr.ModelReportError, match=r"cannot be determined"):
            mr.build_report(sheets, "run-1", policy=_policy())


class TestTaskResolvedObligationsLoading:
    """first_attempt_node_outcomes must be reconstructed from the RESOLVED
    TASK'S OWN obligations_file, never a fixed bench-root location."""

    def test_node_outcomes_are_built_from_the_resolved_tasks_own_obligations_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = tmp_path / "bench-root"
        # A synthetic rubric at a NON-default path, with its own group ids
        # and node ids -- nothing like this repo's real partition. Nothing is
        # vendored at the default hidden_tests/obligations.yaml location
        # under this fake root, so loading that instead of the resolved
        # task's file would fail loudly on a missing file.
        fixture_rubric = {
            "slices": {
                1: {
                    "obligations": [
                        {"id": "fixture-group-a", "tests": ["tests/test_fx.py::test_one", "tests/test_fx.py::test_two"]},
                        {"id": "fixture-group-b", "tests": ["tests/test_gx.py::test_three"]},
                    ]
                }
            }
        }
        rubric_dir = root / "fixture-rubric"
        rubric_dir.mkdir(parents=True)
        (rubric_dir / "obligations.yaml").write_text(yaml.safe_dump(fixture_rubric), encoding="utf-8")
        monkeypatch.setattr(mr, "bench_root", lambda: root)

        groups = dev_check.obligation_groups_for_slice(fixture_rubric, 1)
        outcomes = {node: "passed" for group in groups for node in group["tests"]}
        correctness = dev_check.score_correctness(outcomes, groups, 1)
        attempts = [_attempt(0, correctness=correctness, provenance=_provenance(task_id="fixture-task"))]
        sheets_dir = root / "results" / "runs" / "run-1"
        _write_sheet(sheets_dir, 1, _sheet("run-1", 1, attempts=attempts))

        policy = _policy(
            default_task="fixture-task",
            tasks={"fixture-task": _task_entry(obligations_file="fixture-rubric/obligations.yaml")},
        )
        report, problems = mr.build_report(mr.discover_sheets(sheets_dir, "run-1"), "run-1", policy=policy)
        assert problems == []
        assert report["task_id"] == "fixture-task"
        assert report["task_id_source"] == "graded"
        # The nested map is keyed by the FIXTURE rubric's own group ids --
        # proof that file was actually read.
        assert set(report["slices"][0]["first_attempt_node_outcomes"]) == {"fixture-group-a", "fixture-group-b"}


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
        # A routine `stop` event can land AFTER `complete`. pm_status is
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
    """Harvest PM's own `review_judgments`/`developer_judgments` and join
    them onto an already-built `slices` list. Fixtures here are deliberately
    minimal (only the keys `resolve_pm_judgments` itself reads) rather than
    full `_review_record`/`attempt_trajectory` shapes -- unit-level,
    matching `TestResolveRunTiming`/`TestResolveRunProvenance`'s own style
    above. Fixtures cover: a steer-joined judgment, a superseded judgment,
    an unavailable-status record, and a slice whose only launch-family
    event requires the `+1` ordinal conversion.
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
        # run.json can exist and have slices, but carry no
        # review_judgments/developer_judgments key anywhere -- a labelled
        # absence, never an error.
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
        # run.json DOES carry the named review, but the per-attempt commit
        # walk only graded the slice's final attempt (the Developer did not
        # hold one commit per attempt) -- so the attempt this review was
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
        # inferred (a refused commit walk is usual, but not the only way an
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
        # When a slice's attempt-commit walk is refused, an earlier round's
        # reviews can have no scoring-sheet rows and so never reach this
        # report's own harvested `reviews`. A comparison needs only the
        # reviewer's IDENTITY, which run.json records for every commission
        # -- so the round must survive intact. Resolving through harvested
        # records alone would drop every member of such a round, scoring
        # those reviewers over fewer comparisons than PM actually made and
        # letting a Developer property (commit habits) contaminate a
        # reviewer metric.
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

    def test_comparison_member_prefers_the_harvested_identity_over_a_null_recorded_one(self, tmp_path: Path) -> None:
        # run.json's own reviews[] entry is what a --reviewer-command
        # override left null (policy.yaml's review_identity.corrections
        # fixes this only at HARVEST time, in review_score.py) -- this
        # report's own already-harvested entry carries the corrected
        # identity and must win over the stale recorded null, not the
        # other way around.
        run_state_slices = [
            {
                "id": "Slice 1",
                "reviews": [
                    {"review_id": "review-a", "skill": "code-review", "tool": "opencode", "model": None, "effort": None}
                ],
                "review_judgments": [
                    {"assessment": "comparison", "judgment_id": "judgment-1", "skill": "code-review", "rank_groups": [["review-a"]]}
                ],
            }
        ]
        run_dir = self._run_dir(tmp_path, slices=run_state_slices, events=[])
        slices = [
            {
                "slice": 1,
                "reviews": [
                    self._review(
                        review_id="review-a", skill="code-review", tool="opencode",
                        model="opencode-go/mimo-v2.5", effort="default",
                    )
                ],
                "attempt_trajectory": [],
            }
        ]
        block, problems = mr.resolve_pm_judgments(run_dir, "run-1", slices)
        assert problems == []
        member = block["comparisons"][0]["rank_groups"][0][0]
        assert member["model"] == "opencode-go/mimo-v2.5"
        assert member["effort"] == "default"

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
        # origin_event.index is the slice's ONLY launch-family event -- the
        # strict (no +1) form raises BenchLibError here; the +1 form
        # correctly resolves to attempt ordinal 0.
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
        # origin_event is a `steer` (index 4), the SECOND launch-family
        # event for the slice -- must resolve to attempt ordinal 1, never 0
        # (the strict, no-+1 form would give 0).
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
        # developer-judgment-2 supersedes developer-judgment-1, judging the
        # SAME submission -- only the successor's score must land on the
        # attempt.
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
    `tmp_path` for every other purpose, but `build_report` also loads
    obligations from it (`dev_check.load_obligations`), so that fake root
    needs the real rubric map too."""
    real = REPO_ROOT / "hidden_tests" / "obligations.yaml"
    fake = root / "hidden_tests" / "obligations.yaml"
    fake.parent.mkdir(parents=True, exist_ok=True)
    fake.write_text(real.read_text(encoding="utf-8"), encoding="utf-8")


def _vendor_policy(
    root: Path, *, name: str = "policy.yaml", mutate: Callable[[dict[str, Any]], None] | None = None
) -> Path:
    """Copy this repo's real policy.yaml under a fake `bench_root()` --
    main() loads and validates it before anything else (defaulting to
    <root>/policy.yaml exactly like every other tool in the suite). `mutate`,
    when given, rewrites the parsed mapping first; `name` lets one test hold
    two policies side by side (the --policy fixture below)."""
    data = yaml.safe_load((REPO_ROOT / "policy.yaml").read_text(encoding="utf-8"))
    if mutate is not None:
        mutate(data)
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


class TestMain:
    def test_writes_report_and_returns_0_on_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        root = tmp_path / "bench-root"
        sheets_dir = root / "results" / "runs" / "run-1"
        _write_sheet(sheets_dir, 1, _sheet("run-1", 1))
        _vendor_obligations(root)
        _vendor_policy(root)
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
        _vendor_policy(root)
        monkeypatch.setattr(mr, "bench_root", lambda: root)

        assert mr.main(["--run-id", "run-1"]) == 1

    def test_run_dir_flag_populates_the_timing_block(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        root = tmp_path / "bench-root"
        sheets_dir = root / "results" / "runs" / "run-1"
        _write_sheet(sheets_dir, 1, _sheet("run-1", 1))
        _vendor_obligations(root)
        _vendor_policy(root)
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

    def test_run_dir_missing_run_json_and_events_is_a_hard_error_before_anything_is_written(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # An explicitly-given --run-dir that is not PM's own run directory
        # must stop main() before build_report/write_json_atomically ever
        # run -- never silently overwrite a good prior model-report.json
        # with honest-looking but wrong available:false blocks.
        root = tmp_path / "bench-root"
        sheets_dir = root / "results" / "runs" / "run-1"
        _write_sheet(sheets_dir, 1, _sheet("run-1", 1))
        _vendor_obligations(root)
        _vendor_policy(root)
        monkeypatch.setattr(mr, "bench_root", lambda: root)

        out_path = sheets_dir / "model-report.json"
        out_path.write_text('{"sentinel": "pre-existing report, must survive untouched"}', encoding="utf-8")

        not_a_run_dir = tmp_path / "mistyped-run-dir"
        not_a_run_dir.mkdir()

        with pytest.raises(mr.ModelReportError, match=r"run\.json.*events\.jsonl|events\.jsonl.*run\.json"):
            mr.main(["--run-id", "run-1", "--run-dir", str(not_a_run_dir)])

        assert out_path.read_text(encoding="utf-8") == '{"sentinel": "pre-existing report, must survive untouched"}'

    def test_missing_default_policy_is_a_named_error_before_anything_is_written(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # No policy.yaml anywhere under the fake root: the default location
        # (<root>/policy.yaml) must be consulted and its absence named, never
        # skipped or replaced by an inline fallback.
        root = tmp_path / "bench-root"
        sheets_dir = root / "results" / "runs" / "run-1"
        _write_sheet(sheets_dir, 1, _sheet("run-1", 1))
        _vendor_obligations(root)
        monkeypatch.setattr(mr, "bench_root", lambda: root)

        out_path = sheets_dir / "model-report.json"
        out_path.write_text('{"sentinel": "must survive"}', encoding="utf-8")

        with pytest.raises(mr.ModelReportError, match=r"policy file not found"):
            mr.main(["--run-id", "run-1"])

        assert out_path.read_text(encoding="utf-8") == '{"sentinel": "must survive"}'

    def test_without_the_flag_the_bench_root_default_policy_is_consulted(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Mirror of the --policy test below with NO flag: the DEFAULT policy's
        # own obligations location is the one required -- proving the flag
        # defaults to the implicit bench-root policy.yaml rather than
        # skipping task resolution altogether.
        root = tmp_path / "bench-root"
        sheets_dir = root / "results" / "runs" / "run-1"
        _write_sheet(sheets_dir, 1, _sheet("run-1", 1))
        _vendor_policy(root)  # points relative-velocity at hidden_tests/obligations.yaml
        monkeypatch.setattr(mr, "bench_root", lambda: root)
        # Deliberately NOT vendored: nothing at the default rubric location.

        with pytest.raises(mr.ModelReportError, match=r"hidden_tests/obligations\.yaml"):
            mr.main(["--run-id", "run-1"])

    def test_explicit_policy_flag_selects_its_own_registry_over_the_bench_root_default(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The bench-root DEFAULT policy points relative-velocity's
        # obligations_file at hidden_tests/obligations.yaml -- which is NOT
        # vendored under this fake root. The explicit --policy file points
        # the SAME task id at a different path, where the real rubric IS
        # vendored. Success proves the explicitly-passed file's registry was
        # the one actually consulted; ignoring --policy would fail loudly on
        # the missing default-location file instead.
        root = tmp_path / "bench-root"
        sheets_dir = root / "results" / "runs" / "run-1"
        _write_sheet(sheets_dir, 1, _sheet("run-1", 1))
        _vendor_policy(root)
        custom = _vendor_policy(
            root,
            name="custom-policy.yaml",
            mutate=lambda data: data["tasks"]["relative-velocity"].update(obligations_file="custom-rubric/obligations.yaml"),
        )
        custom_rubric = root / "custom-rubric" / "obligations.yaml"
        custom_rubric.parent.mkdir(parents=True)
        custom_rubric.write_text((REPO_ROOT / "hidden_tests" / "obligations.yaml").read_text(encoding="utf-8"), encoding="utf-8")
        monkeypatch.setattr(mr, "bench_root", lambda: root)

        exit_code = mr.main(["--run-id", "run-1", "--policy", str(custom)])

        assert exit_code == 0
        written = json.loads((sheets_dir / "model-report.json").read_text(encoding="utf-8"))
        assert written["task_id"] == "relative-velocity"
        assert written["task_id_source"] == "backfilled"


def _kill_rate_block(killed: int, total: int, *, bank_hash: str = "bank-1") -> dict[str, Any]:
    """An available `test_kill_rate` block shaped like
    dev_check.measure_test_kill_rate's output, reduced to what this tool reads."""
    return {"available": True, "bank_hash": bank_hash, "killed": killed, "total": total, "kill_rate": killed / total}


class TestTestKillRatePassthrough:
    def _report(self, tmp_path: Path, attempts: list[dict[str, Any]]) -> tuple[dict[str, Any], list[str]]:
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=len(attempts) - 1))
        return mr.build_report(mr.discover_sheets(tmp_path, "run-1"), "run-1", policy=_policy())

    def test_blocks_pass_through_on_first_and_final_and_compactly_on_the_trajectory(self, tmp_path: Path) -> None:
        first, final = _attempt(0), _attempt(1, pm_decision="accept")
        first["test_kill_rate"] = _kill_rate_block(1, 4)
        final["test_kill_rate"] = {"available": False, "reason": "own-suite baseline timed out after 600s"}
        report, problems = self._report(tmp_path, [first, final])
        slice_entry = report["slices"][0]
        assert slice_entry["first_attempt"]["test_kill_rate"] == _kill_rate_block(1, 4)
        assert slice_entry["final_attempt"]["test_kill_rate"]["available"] is False
        assert [row["test_kill_rate"] for row in slice_entry["attempt_trajectory"]] == [
            {"available": True, "kill_rate": 0.25},
            {"available": False, "kill_rate": None},
        ]
        assert problems == []

    def test_a_sheet_graded_before_the_measurement_reads_as_unavailable(self, tmp_path: Path) -> None:
        report, _problems = self._report(tmp_path, [_attempt(0, pm_decision="accept")])
        assert report["slices"][0]["attempt_trajectory"][0]["test_kill_rate"] == {"available": False, "kill_rate": None}

    def test_attempts_measured_against_different_banks_are_a_named_problem(self, tmp_path: Path) -> None:
        first, final = _attempt(0), _attempt(1, pm_decision="accept")
        first["test_kill_rate"] = _kill_rate_block(1, 4, bank_hash="bank-1")
        final["test_kill_rate"] = _kill_rate_block(2, 4, bank_hash="bank-2")
        _report, problems = self._report(tmp_path, [first, final])
        assert len(problems) == 1
        assert "run run-1, slice 1" in problems[0]
        assert "['bank-1', 'bank-2']" in problems[0]

    def test_an_available_block_without_a_bank_hash_is_a_named_problem_not_a_crash(self, tmp_path: Path) -> None:
        attempt = _attempt(0, pm_decision="accept")
        attempt["test_kill_rate"] = {"available": True, "killed": 1, "total": 4, "kill_rate": 0.25}
        _report, problems = self._report(tmp_path, [attempt])
        assert len(problems) == 1
        assert "run run-1, slice 1, attempt 0" in problems[0]
        assert "no bank_hash" in problems[0]


class TestResolveRunProcess:
    def _events_dir(self, tmp_path: Path, text: str) -> Path:
        run_dir = tmp_path / "pm-run"
        run_dir.mkdir()
        (run_dir / "events.jsonl").write_text(text, encoding="utf-8")
        return run_dir

    def test_counts_failed_floors_and_send_events_only(self, tmp_path: Path) -> None:
        events = [
            {"kind": "init"},
            {"kind": "launch", "slice": "Slice 1"},
            {"kind": "send", "slice": "Slice 1", "note": "keep going"},
            {"kind": "floor", "slice": "Slice 1", "note": "failed: tests_pass, scope"},
            {"kind": "steer", "slice": "Slice 1"},
            {"kind": "send", "slice": "Slice 1", "note": "check the docstring"},
            {"kind": "floor", "slice": "Slice 1", "note": "7/7 passed"},
            {"kind": "relaunch", "slice": "Slice 2"},
            {"kind": "floor", "slice": "Slice 2", "note": "failed: tests_pass"},
            {"kind": "floor", "slice": "Slice 2", "note": "7/7 passed"},
            {"kind": "send", "slice": "Slice 2", "note": "one more"},
            {"kind": "complete"},
        ]
        run_dir = self._events_dir(tmp_path, "\n".join(json.dumps(e) for e in events) + "\n")

        process, problems = mr.resolve_run_process(run_dir)

        assert process == {"available": True, "floor_failures": 2, "nudges": 3}
        assert problems == []

    def test_no_run_dir_is_unavailable_not_an_error(self) -> None:
        process, problems = mr.resolve_run_process(None)
        assert process == {"available": False, "reason": "no --run-dir given; events.jsonl was not read"}
        assert problems == []

    def test_unreadable_log_is_a_named_problem(self, tmp_path: Path) -> None:
        run_dir = self._events_dir(tmp_path, '{"kind": "init"}\nnot json\n')
        process, problems = mr.resolve_run_process(run_dir)
        assert process["available"] is False
        assert len(problems) == 1
        assert "events.jsonl" in problems[0]
        assert process["reason"] == problems[0]

    def test_build_report_carries_the_block_at_top_level(self, tmp_path: Path) -> None:
        sheets_dir = tmp_path / "sheets"
        sheets_dir.mkdir()
        _write_sheet(sheets_dir, 1, _sheet("run-1", 1, attempts=[_attempt(0, pm_decision="accept")], accepted_at_attempt=0))
        run_dir = self._events_dir(tmp_path, json.dumps({"kind": "send", "note": "hi"}) + "\n")

        report, _problems = mr.build_report(mr.discover_sheets(sheets_dir, "run-1"), "run-1", run_dir=run_dir, policy=_policy())

        assert report["process"] == {"available": True, "floor_failures": 0, "nudges": 1}


class TestHygienePassthrough:
    def test_trajectory_rows_carry_a_compact_narration_view(self, tmp_path: Path) -> None:
        first, final = _attempt(0), _attempt(1, pm_decision="accept")
        first["hygiene"] = {"available": True, "production": {"narration_lines": 4, "added_code": 10}}
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=[first, final], accepted_at_attempt=1))

        report, _problems = mr.build_report(mr.discover_sheets(tmp_path, "run-1"), "run-1", policy=_policy())

        slice_entry = report["slices"][0]
        assert slice_entry["first_attempt"]["hygiene"] == first["hygiene"]
        # The final attempt was graded before the census existed: unavailable, never 0.
        assert [row["hygiene"] for row in slice_entry["attempt_trajectory"]] == [
            {"available": True, "narration_lines": 4},
            {"available": False, "narration_lines": None},
        ]


class TestSliceQualityPanel:
    @staticmethod
    def _record(model: str, design: int) -> dict[str, Any]:
        return {
            "tool": "claude",
            "model": model,
            "effort": "high",
            "rubric_file": "docs/QUALITY-PANEL-RUBRIC.md",
            "rubric_sha256": "ab" * 32,
            "prompt_sha256": "cd" * 32,
            "delegate_run_dir": "/x/y",
            "label": "quality-panel",
            "at": "2026-01-01T00:00:00Z",
            "commit_sha": "c0ffee",
            "before_head": "badf00d",
            "scores": {"correctness_beyond_tests": 4, "design": design, "readability_docs": 3, "tests": 2, "contract_discipline": 5},
            "evidence": ["a.py:1 -- reason"],
            "summary": "fine",
        }

    def test_records_come_through_in_attempt_then_record_order_with_every_field(self, tmp_path: Path) -> None:
        first, second = self._record("m1", 4), self._record("m2", 2)
        attempts = [_attempt(1), _attempt(0)]
        attempts[0]["quality_panel"] = [second]
        attempts[1]["quality_panel"] = [first]
        _write_sheet(tmp_path, 1, _sheet("run-1", 1, attempts=attempts, accepted_at_attempt=1))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1", policy=_policy())
        assert report["slices"][0]["quality_panel"] == [{**first, "attempt": 0}, {**second, "attempt": 1}]

    def test_sheet_without_the_key_yields_an_empty_list(self, tmp_path: Path) -> None:
        _write_sheet(tmp_path, 1, _sheet("run-1", 1))
        sheets = mr.discover_sheets(tmp_path, "run-1")
        report, _problems = mr.build_report(sheets, "run-1", policy=_policy())
        assert report["slices"][0]["quality_panel"] == []
        assert mr.slice_quality_panel({}) == []
