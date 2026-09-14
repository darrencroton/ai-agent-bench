"""Tests for tools/leaderboard.py (Tool 5: the cross-model leaderboard).

Fixtures are hand-written model-report.json documents under `tmp_path`,
matching the real shape Tool 4 (model_report.py) writes
(docs/MODE2-REWRITE-PLAN.md §6; Stage 2's `first_attempt`/`attempt_trajectory`/
`timing`/`provenance` additions, docs/LEADERBOARD-REBUILD-PLAN.md). No git,
no subprocess: this tool only reads already-graded JSON already on disk.

Stage 2 deletes the old four-term weighted composite entirely (correctness/
quality/scope/iterations sub-scores, policy.yaml's `weights`/
`scope_violation_penalty`/`iteration_reference_attempts`) and ranks on mean
first-attempt correctness instead -- every test that exercised the composite
is replaced here, not merely patched, since the behaviour it encoded no
longer exists.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import leaderboard as lb  # noqa: E402


def _policy(**overrides: Any) -> dict[str, Any]:
    return {"expected_slices": overrides.get("expected_slices", 2)}


def _quality_tool(*, available: bool = True, verdict: str = "pass") -> dict[str, Any]:
    return {"available": available, "verdict": verdict}


def _attempt(
    *,
    attempt: int = 0,
    by_obligation: dict[str, dict[str, float]] | None = None,
    lint: dict[str, Any] | None = None,
    health: dict[str, Any] | None = None,
    violations: list[str] | None = None,
    pm_decision: str = "accept",
) -> dict[str, Any]:
    return {
        "attempt": attempt,
        "pm_attempts_counter": attempt,
        "commit_sha": f"sha-{attempt}",
        "correctness": {
            "hidden_tests_passed": 4,
            "hidden_tests_total": 4,
            "by_obligation": by_obligation if by_obligation is not None else {"g1": {"fraction": 1.0}},
        },
        "quality": {
            "lint_findings_by_tool": lint if lint is not None else _quality_tool(),
            "code_health_findings_by_category": health if health is not None else _quality_tool(),
        },
        "scope": {"violations": violations or []},
        "pm_decision": pm_decision,
    }


# Kept as a thin alias so fixtures reading like "the final attempt scored
# X" stay readable -- _attempt()'s shape works identically as a
# first_attempt or final_attempt block.
_final_attempt = _attempt


_UNSET = object()


def _slice(
    slice_number: int,
    *,
    final_attempt: dict[str, Any] | None | object = _UNSET,
    first_attempt: dict[str, Any] | None | object = _UNSET,
    accepted_at_attempt: int | None = 0,
    attempts_total: int = 1,
    has_attempt_zero: bool | object = _UNSET,
    slice_status: str = "accepted",
    infrastructure_failure_suspected: bool = False,
    review_trends: dict[str, Any] | None = None,
    attempt_trajectory: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    resolved_final = _attempt() if final_attempt is _UNSET else final_attempt
    # Most fixtures describe a one-attempt slice, where "first" and "final"
    # are the same submission -- callers testing first-vs-final divergence
    # pass both explicitly.
    resolved_first = resolved_final if first_attempt is _UNSET else first_attempt
    # has_attempt_zero must stay consistent with whether a first_attempt
    # row actually exists (model_report.py guarantees this on every real
    # report) -- a caller not overriding it explicitly gets it inferred
    # from resolved_first, rather than silently defaulting True and letting
    # compute_run_coverage mark a first-attempt-less slice eligible anyway.
    resolved_has_attempt_zero = (resolved_first is not None) if has_attempt_zero is _UNSET else has_attempt_zero
    default_trajectory = (
        [
            {
                "attempt": 0,
                "pm_attempts_counter": 0,
                "commit_sha": "sha-0",
                "correctness": (resolved_final or {}).get("correctness"),
                "pm_decision": (resolved_final or {}).get("pm_decision", "accept"),
                "commissioned_reviews": [],
            }
        ]
        if resolved_final
        else []
    )
    return {
        "slice": slice_number,
        "slice_status": slice_status,
        "infrastructure_failure_suspected": infrastructure_failure_suspected,
        "first_attempt": resolved_first,
        "final_attempt": resolved_final,
        "accepted_at_attempt": accepted_at_attempt,
        "attempts_total": attempts_total,
        "has_attempt_zero": resolved_has_attempt_zero,
        "attempt_trajectory": attempt_trajectory if attempt_trajectory is not None else default_trajectory,
        "review_trends": review_trends if review_trends is not None else {},
    }


# Fixed harness/effort for every test report, so the `model=` parameter
# already used throughout this file's fixtures stays the one varying
# identity dimension -- configuration_key still includes all three (Stage
# 1: an unrecorded field must stay distinct, never merged away), so the
# grouping/display value most tests compare against is `f"{model} · "
# f"{_HARNESS} · {_EFFORT}"`, produced by `_configuration_key` below.
_HARNESS = "opencode"
_EFFORT = "low"


def _configuration_key(model: str) -> str:
    return f"{model} · {_HARNESS} · {_EFFORT}"


def _developer(*, model: str = "opencode/some-model", attributed: bool = True) -> dict[str, Any]:
    """Stage 1's structured identity block (docs/LEADERBOARD-REBUILD-PLAN.md),
    what a real model-report.json now carries in place of a flat `model`
    string."""
    if not attributed:
        return {
            "harness": None,
            "model": None,
            "effort": None,
            "configuration_key": "model unknown · harness unknown · effort unknown",
            "sources": {},
            "attributed": False,
            "attestation": None,
        }
    return {
        "harness": _HARNESS,
        "model": model,
        "effort": _EFFORT,
        "configuration_key": _configuration_key(model),
        "sources": {"harness": "run_harness", "model": "run_harness", "effort": "run_harness"},
        "attributed": True,
        "attestation": None,
    }


def _timing(*, available: bool = True, elapsed_seconds: float = 3195.0) -> dict[str, Any]:
    if not available:
        return {"available": False, "reason": "no --run-dir given; events.jsonl was not read"}
    return {
        "available": True,
        "init_at": "2026-09-12T06:56:34Z",
        "terminal_at": "2026-09-12T07:49:49Z",
        "terminal_kind": "complete",
        "elapsed_seconds": elapsed_seconds,
    }


def _provenance() -> dict[str, Any]:
    return {"available": False, "reason": "no --run-dir given; run.json was not read", "pm_run_dir": None}


def _report(
    run_id: str,
    *,
    model: str = "opencode/some-model",
    developer: dict[str, Any] | None = None,
    pm_status: str = "complete",
    slices: list[dict[str, Any]] | None = None,
    rating_available: bool = False,
    rating_text: str | None = None,
    timing_available: bool = True,
    elapsed_seconds: float = 3195.0,
    problems: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "developer": developer if developer is not None else _developer(model=model),
        "run_status": {"pm_status": pm_status, "stop_reason": "done"},
        "timing": _timing(available=timing_available, elapsed_seconds=elapsed_seconds),
        "provenance": _provenance(),
        "slices": slices if slices is not None else [_slice(1), _slice(2)],
        "pm_subjective_rating": {"available": rating_available, "ref": None, "text": rating_text},
        "problems": problems if problems is not None else [],
    }


def _write_report(runs_root: Path, run_id: str, report: dict[str, Any]) -> Path:
    run_dir = runs_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "model-report.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    return path


def _eligible_coverage(*run_ids: str) -> dict[str, dict[str, Any]]:
    return {run_id: {"eligible_for_first_submission": True, "ineligibility_reasons": []} for run_id in run_ids}


def _ineligible_coverage(run_id: str, reason: str = "not eligible for this test") -> dict[str, dict[str, Any]]:
    return {run_id: {"eligible_for_first_submission": False, "ineligibility_reasons": [reason]}}


class TestLoadLeaderboardPolicy:
    def test_missing_leaderboard_section_is_a_named_error(self, tmp_path: Path) -> None:
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text(yaml.safe_dump({"backend": "local"}), encoding="utf-8")
        with pytest.raises(lb.LeaderboardError, match="leaderboard"):
            lb.load_leaderboard_policy(policy_path)

    def test_missing_expected_slices_is_a_named_error(self, tmp_path: Path) -> None:
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text(yaml.safe_dump({"leaderboard": {}}), encoding="utf-8")
        with pytest.raises(lb.LeaderboardError, match="expected_slices"):
            lb.load_leaderboard_policy(policy_path)

    def test_non_positive_expected_slices_is_a_named_error(self, tmp_path: Path) -> None:
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text(yaml.safe_dump({"leaderboard": {"expected_slices": 0}}), encoding="utf-8")
        with pytest.raises(lb.LeaderboardError, match="expected_slices"):
            lb.load_leaderboard_policy(policy_path)

    def test_boolean_expected_slices_is_a_named_error(self, tmp_path: Path) -> None:
        # bool subclasses int in Python -- `True` must not silently become
        # expected_slices=1 by passing an `isinstance(x, int)` check.
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text(yaml.safe_dump({"leaderboard": {"expected_slices": True}}), encoding="utf-8")
        with pytest.raises(lb.LeaderboardError, match="expected_slices"):
            lb.load_leaderboard_policy(policy_path)

    def test_valid_policy_loads(self, tmp_path: Path) -> None:
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text(yaml.safe_dump({"leaderboard": {"expected_slices": 2}}), encoding="utf-8")
        leaderboard_policy = lb.load_leaderboard_policy(policy_path)
        assert leaderboard_policy["expected_slices"] == 2

    def test_no_dead_weights_key_is_read(self, tmp_path: Path) -> None:
        # Stage 2 deletes weights/scope_violation_penalty/
        # iteration_reference_attempts entirely -- a policy that no longer
        # carries them must still load cleanly.
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text(yaml.safe_dump({"leaderboard": {"expected_slices": 2}}), encoding="utf-8")
        leaderboard_policy = lb.load_leaderboard_policy(policy_path)
        assert "weights" not in leaderboard_policy
        assert "scope_violation_penalty" not in leaderboard_policy


class TestMeanObligationFraction:
    def test_equally_weights_groups_not_raw_test_count(self) -> None:
        # An asymmetric partition: one group of 1 test, one of 19 tests --
        # the mean must weight the groups equally (0.5), never the raw
        # pass fraction (18/20 = 0.9 would disagree).
        by_obligation = {
            "small_group": {"passed": 0, "total": 1, "fraction": 0.0},
            "large_group": {"passed": 18, "total": 19, "fraction": 18 / 19},
        }
        result = lb._mean_obligation_fraction(by_obligation, context="test")
        assert result == pytest.approx((0.0 + 18 / 19) / 2)

    def test_malformed_by_obligation_raises_named_error(self) -> None:
        with pytest.raises(lb.LeaderboardError, match="malformed by_obligation for model X"):
            lb._mean_obligation_fraction({"g": {"no_fraction_key": True}}, context="model X")

    def test_empty_by_obligation_raises_named_error(self) -> None:
        with pytest.raises(lb.LeaderboardError, match="empty by_obligation for model X"):
            lb._mean_obligation_fraction({}, context="model X")


class TestSpread:
    def test_empty_is_none(self) -> None:
        assert lb._spread([]) is None

    def test_single_value_shows_n_one_not_a_fabricated_spread(self) -> None:
        spread = lb._spread([0.75])
        assert spread == {"mean": 0.75, "min": 0.75, "max": 0.75, "n": 1}

    def test_multiple_values_mean_min_max_n(self) -> None:
        spread = lb._spread([0.5, 1.0, 0.75])
        assert spread == {"mean": pytest.approx(0.75), "min": 0.5, "max": 1.0, "n": 3}


class TestDiscoverReports:
    def test_no_reports_found_is_a_named_error(self, tmp_path: Path) -> None:
        with pytest.raises(lb.LeaderboardError, match="no model-report.json"):
            lb.discover_reports(tmp_path / "runs")

    def test_unparsable_json_is_a_named_error(self, tmp_path: Path) -> None:
        run_dir = tmp_path / "run-1"
        run_dir.mkdir(parents=True)
        (run_dir / "model-report.json").write_text("{not json", encoding="utf-8")
        with pytest.raises(lb.LeaderboardError, match="invalid JSON"):
            lb.discover_reports(tmp_path)

    def test_missing_required_key_is_a_named_error(self, tmp_path: Path) -> None:
        report = _report("run-1")
        del report["pm_subjective_rating"]
        _write_report(tmp_path, "run-1", report)
        with pytest.raises(lb.LeaderboardError, match="pm_subjective_rating"):
            lb.discover_reports(tmp_path)

    def test_missing_timing_key_is_a_named_error(self, tmp_path: Path) -> None:
        # Stage 2 adds `timing`/`provenance` to every report -- a report
        # missing either is malformed, not just missing an optional extra.
        report = _report("run-1")
        del report["timing"]
        _write_report(tmp_path, "run-1", report)
        with pytest.raises(lb.LeaderboardError, match="timing"):
            lb.discover_reports(tmp_path)

    def test_finds_every_report(self, tmp_path: Path) -> None:
        _write_report(tmp_path, "run-1", _report("run-1"))
        _write_report(tmp_path, "run-2", _report("run-2", model="other/model"))
        found = lb.discover_reports(tmp_path)
        assert len(found) == 2

    def test_non_mapping_developer_block_is_a_named_error(self, tmp_path: Path) -> None:
        report = _report("run-1")
        report["developer"] = "not-a-mapping"
        _write_report(tmp_path, "run-1", report)
        with pytest.raises(lb.LeaderboardError, match="'developer' block is not a mapping"):
            lb.discover_reports(tmp_path)

    def test_developer_block_missing_a_required_subkey_is_a_named_error(self, tmp_path: Path) -> None:
        report = _report("run-1")
        del report["developer"]["configuration_key"]
        _write_report(tmp_path, "run-1", report)
        with pytest.raises(lb.LeaderboardError, match="configuration_key"):
            lb.discover_reports(tmp_path)

    def test_developer_attributed_must_be_a_bool(self, tmp_path: Path) -> None:
        report = _report("run-1")
        report["developer"]["attributed"] = "yes"
        _write_report(tmp_path, "run-1", report)
        with pytest.raises(lb.LeaderboardError, match="attributed must be true/false"):
            lb.discover_reports(tmp_path)

    def test_developer_configuration_key_must_be_a_non_empty_string(self, tmp_path: Path) -> None:
        report = _report("run-1")
        report["developer"]["configuration_key"] = ""
        _write_report(tmp_path, "run-1", report)
        with pytest.raises(lb.LeaderboardError, match="configuration_key must be a non-empty string"):
            lb.discover_reports(tmp_path)

    def test_duplicate_run_id_across_reports_is_a_named_error(self, tmp_path: Path) -> None:
        runs_root = tmp_path / "runs"
        _write_report(runs_root, "run-dupe", _report("run-dupe"))
        # A second, differently-named run directory whose report still
        # claims run_id "run-dupe" -- must not silently collapse into one
        # entry (and undercount run_count) in aggregate_model's grouping.
        _write_report(runs_root, "run-dupe-2", _report("run-dupe"))
        with pytest.raises(lb.LeaderboardError, match="run-dupe"):
            lb.discover_reports(runs_root)


class TestAggregateModel:
    def test_first_attempt_correctness_uses_ordinal_zero_only(self) -> None:
        first = _attempt(attempt=0, by_obligation={"g": {"fraction": 0.5}})
        final = _attempt(attempt=1, by_obligation={"g": {"fraction": 1.0}})
        report = _report("run-1", slices=[_slice(1, first_attempt=first, final_attempt=final), _slice(2)])
        entry, problems = lb.aggregate_model("m", [(Path("x"), report)], _eligible_coverage("run-1"))
        # Slice 1 contributes its FIRST attempt's 0.5, slice 2 (default,
        # first==final) contributes 1.0 -- mean 0.75, never final's 1.0.
        assert entry["first_attempt_correctness"]["mean"] == pytest.approx(0.75)
        assert problems == []

    def test_ineligible_run_excluded_from_first_attempt_correctness(self) -> None:
        report = _report("run-1")
        entry, _problems = lb.aggregate_model("m", [(Path("x"), report)], _ineligible_coverage("run-1"))
        assert entry["first_attempt_correctness"] is None
        assert entry["eligible_run_ids"] == []
        # Final correctness and other columns don't need attempt-0 data --
        # an ineligible run still contributes to them.
        assert entry["final_attempt_correctness"]["mean"] == pytest.approx(1.0)

    def test_no_final_attempt_excludes_correctness_and_is_named(self) -> None:
        report = _report("run-1", slices=[_slice(1, final_attempt=None, first_attempt=None, accepted_at_attempt=None)])
        entry, problems = lb.aggregate_model("m", [(Path("x"), report)], _ineligible_coverage("run-1"))
        assert entry["final_attempt_correctness"] is None
        assert any("no final attempt to grade correctness from" in p for p in problems)

    def test_eligible_run_missing_first_attempt_data_is_an_invariant_violation(self) -> None:
        # run_coverage says eligible, but the sheet has no first_attempt --
        # that combination should never occur; this tool must raise loudly
        # rather than silently produce a wrong mean.
        report = _report("run-1", slices=[_slice(1, first_attempt=None)])
        with pytest.raises(lb.LeaderboardError, match="eligible_for_first_submission"):
            lb.aggregate_model("m", [(Path("x"), report)], _eligible_coverage("run-1"))

    def test_gain_pp_computed_within_run_before_averaging(self) -> None:
        # Unequal slice counts per run (2 in run A, 1 in run B) so that
        # per-run averaging (the documented rule: mean each run's own
        # final-minus-first, THEN average across runs) and a naive
        # flatten-every-slice-then-diff-the-means approach disagree.
        #
        # Run A (2 slices): first [0.0, 1.0] -> final [1.0, 1.0].
        #   Per-run means: first 0.5, final 1.0 -> gain_A = 50pp.
        # Run B (1 slice): first 0.0 -> final 0.0 -> gain_B = 0pp.
        #
        # Correct (per-run-paired-then-averaged): mean(50, 0) = 25pp.
        # Naive (flatten all 3 slice-records, diff the two means):
        #   mean(final)=[1,1,0]->0.667*100; mean(first)=[0,1,0]->0.333*100;
        #   diff = 33.3pp -- a different, wrong number.
        report_a = _report(
            "run-a",
            slices=[
                _slice(1, first_attempt=_attempt(by_obligation={"g": {"fraction": 0.0}}), final_attempt=_attempt(by_obligation={"g": {"fraction": 1.0}})),
                _slice(2, first_attempt=_attempt(by_obligation={"g": {"fraction": 1.0}}), final_attempt=_attempt(by_obligation={"g": {"fraction": 1.0}})),
            ],
        )
        report_b = _report(
            "run-b",
            slices=[_slice(1, first_attempt=_attempt(by_obligation={"g": {"fraction": 0.0}}), final_attempt=_attempt(by_obligation={"g": {"fraction": 0.0}}))],
        )
        entry, _problems = lb.aggregate_model(
            "m", [(Path("a"), report_a), (Path("b"), report_b)], _eligible_coverage("run-a", "run-b")
        )
        assert entry["gain_pp"]["mean"] == pytest.approx(25.0)
        naive_wrong_answer = (100 * (2 / 3)) - (100 * (1 / 3))
        assert entry["gain_pp"]["mean"] != pytest.approx(naive_wrong_answer)

    def test_gain_pp_excludes_runs_ineligible_for_first_submission(self) -> None:
        report = _report("run-1")
        entry, _problems = lb.aggregate_model("m", [(Path("x"), report)], _ineligible_coverage("run-1"))
        assert entry["gain_pp"] is None

    def test_attempts_by_slice_spread(self) -> None:
        report = _report("run-1", slices=[_slice(1, attempts_total=3), _slice(2, attempts_total=5)])
        entry, _problems = lb.aggregate_model("m", [(Path("x"), report)], _eligible_coverage("run-1"))
        assert entry["attempts_by_slice"][1] == {"mean": 3.0, "min": 3, "max": 3, "n": 1}
        assert entry["attempts_by_slice"][2] == {"mean": 5.0, "min": 5, "max": 5, "n": 1}

    def test_steers_counted_from_attempt_trajectory_pm_decision(self) -> None:
        trajectory = [
            {"attempt": 0, "pm_attempts_counter": 0, "commit_sha": "a", "correctness": {}, "pm_decision": "steer", "commissioned_reviews": []},
            {"attempt": 1, "pm_attempts_counter": 1, "commit_sha": "b", "correctness": {}, "pm_decision": "accept", "commissioned_reviews": []},
        ]
        report = _report("run-1", slices=[_slice(1, attempt_trajectory=trajectory)])
        entry, _problems = lb.aggregate_model("m", [(Path("x"), report)], _eligible_coverage("run-1"))
        assert entry["steers"] == {"mean": 1.0, "min": 1.0, "max": 1.0, "n": 1}

    def test_pm_elapsed_seconds_excludes_unavailable_timing(self) -> None:
        report = _report("run-1", timing_available=False)
        entry, _problems = lb.aggregate_model("m", [(Path("x"), report)], _eligible_coverage("run-1"))
        assert entry["pm_elapsed_seconds"] is None

    def test_pm_elapsed_seconds_recorded_when_available(self) -> None:
        report = _report("run-1", timing_available=True, elapsed_seconds=1234.0)
        entry, _problems = lb.aggregate_model("m", [(Path("x"), report)], _eligible_coverage("run-1"))
        assert entry["pm_elapsed_seconds"] == {"mean": 1234.0, "min": 1234.0, "max": 1234.0, "n": 1}

    def test_run_metadata_recorded_per_model(self) -> None:
        r1 = _report("run-1", pm_status="complete", rating_available=True, rating_text="great")
        r2 = _report("run-2", pm_status="stopped")
        entry, _problems = lb.aggregate_model(
            "m", [(Path("a"), r1), (Path("b"), r2)], {**_eligible_coverage("run-1"), **_ineligible_coverage("run-2")}
        )
        assert entry["run_count"] == 2
        assert entry["run_ids"] == ["run-1", "run-2"]
        assert entry["eligible_run_ids"] == ["run-1"]
        assert entry["pm_status_counts"] == {"complete": 1, "stopped": 1}
        assert entry["completed_runs"] == 1
        assert entry["pm_subjective_ratings"] == [
            {"run_id": "run-1", "available": True, "ref": None, "text": "great"},
            {"run_id": "run-2", "available": False, "ref": None, "text": None},
        ]

    def test_report_level_problems_are_propagated_with_run_context(self) -> None:
        # Tool 4 names its own problems (e.g. a vanished rating file, or a
        # malformed timing log) in the report's own `problems` list --
        # dropping them here would make that indistinguishable from "never
        # recorded" (AGENTS.md: never silently discard another tool's named
        # problem).
        report = _report("run-1", problems=["pm_model_performance_ref foo.md is recorded but no longer exists on disk"])
        entry, problems = lb.aggregate_model("m", [(Path("a"), report)], _eligible_coverage("run-1"))
        assert any("run-1: pm_model_performance_ref foo.md is recorded but no longer exists" in p for p in problems)
        assert problems == entry["problems"]


class TestBuildLeaderboard:
    def test_one_model_one_run(self, tmp_path: Path) -> None:
        _write_report(tmp_path, "run-1", _report("run-1"))
        reports = lb.discover_reports(tmp_path)
        leaderboard, problems = lb.build_leaderboard(reports, _policy())
        assert [m["model"] for m in leaderboard["models"]] == [_configuration_key("opencode/some-model")]
        assert problems == []

    def test_one_model_multiple_runs_folds_into_one_entry(self, tmp_path: Path) -> None:
        _write_report(tmp_path, "run-1", _report("run-1"))
        _write_report(tmp_path, "run-2", _report("run-2"))
        reports = lb.discover_reports(tmp_path)
        leaderboard, _problems = lb.build_leaderboard(reports, _policy())
        assert len(leaderboard["models"]) == 1
        assert leaderboard["models"][0]["run_count"] == 2

    def test_two_distinct_configs_ranked_by_first_attempt_correctness(self, tmp_path: Path) -> None:
        strong = [_slice(1, first_attempt=_attempt(by_obligation={"g": {"fraction": 1.0}})), _slice(2, first_attempt=_attempt(by_obligation={"g": {"fraction": 1.0}}))]
        weak = [_slice(1, first_attempt=_attempt(by_obligation={"g": {"fraction": 0.1}})), _slice(2, first_attempt=_attempt(by_obligation={"g": {"fraction": 0.1}}))]
        _write_report(tmp_path, "run-1", _report("run-1", model="strong/model", slices=strong))
        _write_report(tmp_path, "run-2", _report("run-2", model="weak/model", slices=weak))
        reports = lb.discover_reports(tmp_path)
        leaderboard, _problems = lb.build_leaderboard(reports, _policy())
        assert [m["model"] for m in leaderboard["models"]] == [
            _configuration_key("strong/model"),
            _configuration_key("weak/model"),
        ]

    def test_run_with_no_eligible_slices_sorts_last(self, tmp_path: Path) -> None:
        ineligible = _report("run-1", model="ineligible/model", pm_status="stopped")
        eligible = _report("run-2", model="eligible/model")
        _write_report(tmp_path, "run-1", ineligible)
        _write_report(tmp_path, "run-2", eligible)
        reports = lb.discover_reports(tmp_path)
        leaderboard, _problems = lb.build_leaderboard(reports, _policy())
        assert [m["model"] for m in leaderboard["models"]] == [
            _configuration_key("eligible/model"),
            _configuration_key("ineligible/model"),
        ]
        assert leaderboard["models"][1]["first_attempt_correctness"] is None

    def test_ties_are_labelled_and_broken_by_name(self, tmp_path: Path) -> None:
        _write_report(tmp_path, "run-1", _report("run-1", model="zeta/model"))
        _write_report(tmp_path, "run-2", _report("run-2", model="alpha/model"))
        reports = lb.discover_reports(tmp_path)
        leaderboard, _problems = lb.build_leaderboard(reports, _policy())
        assert [m["model"] for m in leaderboard["models"]] == [
            _configuration_key("alpha/model"),
            _configuration_key("zeta/model"),
        ]
        assert leaderboard["models"][0]["tied_with_previous"] is False
        assert leaderboard["models"][1]["tied_with_previous"] is True


class TestUnattributedRuns:
    """Stage 1's own goal (docs/LEADERBOARD-REBUILD-PLAN.md): a run is
    attributed to a Developer configuration, or it is conspicuously
    unattributed and excluded from ranking -- never discarded, and never a
    model literally named `None`."""

    def test_unattributed_run_is_excluded_from_models_but_not_discarded(self, tmp_path: Path) -> None:
        _write_report(tmp_path, "run-1", _report("run-1", developer=_developer(attributed=False)))
        reports = lb.discover_reports(tmp_path)
        leaderboard, problems = lb.build_leaderboard(reports, _policy())

        assert leaderboard["models"] == []
        assert [r["run_id"] for r in leaderboard["unattributed_runs"]] == ["run-1"]
        assert leaderboard["unattributed_runs"][0]["developer"]["attributed"] is False
        assert any("unattributed" in p and "run-1" in p for p in problems)

    def test_a_run_named_none_never_appears_as_a_ranked_model(self, tmp_path: Path) -> None:
        # The literal defect this stage exists to fix: a run with no
        # recorded identity must never rank as a model named "None".
        _write_report(tmp_path, "run-1", _report("run-1", developer=_developer(attributed=False)))
        reports = lb.discover_reports(tmp_path)
        leaderboard, _problems = lb.build_leaderboard(reports, _policy())
        assert None not in [m["model"] for m in leaderboard["models"]]
        assert "None" not in [m["model"] for m in leaderboard["models"]]

    def test_attributed_and_unattributed_runs_coexist(self, tmp_path: Path) -> None:
        _write_report(tmp_path, "run-1", _report("run-1", model="known/model"))
        _write_report(tmp_path, "run-2", _report("run-2", developer=_developer(attributed=False)))
        reports = lb.discover_reports(tmp_path)
        leaderboard, _problems = lb.build_leaderboard(reports, _policy())
        assert [m["model"] for m in leaderboard["models"]] == [_configuration_key("known/model")]
        assert [r["run_id"] for r in leaderboard["unattributed_runs"]] == ["run-2"]

    def test_run_coverage_is_recorded_for_every_run_attributed_or_not(self, tmp_path: Path) -> None:
        _write_report(tmp_path, "run-1", _report("run-1"))
        _write_report(tmp_path, "run-2", _report("run-2", developer=_developer(attributed=False)))
        reports = lb.discover_reports(tmp_path)
        leaderboard, _problems = lb.build_leaderboard(reports, _policy())
        assert set(leaderboard["run_coverage"]) == {"run-1", "run-2"}


class TestRunCoverage:
    """compute_run_coverage's own unit tests -- the eligibility rule
    (docs/LEADERBOARD-REBUILD-PLAN.md Stage 1): attributed identity, PM
    status complete, every expected slice graded, each with a real
    attempt-0 row."""

    def test_fully_covered_run_is_eligible(self) -> None:
        report = _report("run-1", slices=[_slice(1), _slice(2)])
        coverage = lb.compute_run_coverage(report, _policy())
        assert coverage["eligible_for_first_submission"] is True
        assert coverage["ineligibility_reasons"] == []
        assert coverage["graded_slices"] == [1, 2]

    def test_missing_a_slice_is_ineligible_and_named(self) -> None:
        report = _report("run-1", slices=[_slice(1)])
        coverage = lb.compute_run_coverage(report, _policy())
        assert coverage["eligible_for_first_submission"] is False
        assert any("graded 1 of 2" in reason for reason in coverage["ineligibility_reasons"])

    def test_missing_attempt_zero_is_ineligible_and_never_substituted(self) -> None:
        # Under G16's fallback a slice can hold only its final attempt's
        # row -- attempt 0 is genuinely absent and must never be treated as
        # present just because *some* attempt was graded.
        report = _report("run-1", slices=[_slice(1, has_attempt_zero=False), _slice(2)])
        coverage = lb.compute_run_coverage(report, _policy())
        assert coverage["eligible_for_first_submission"] is False
        assert coverage["slices_missing_attempt_zero"] == [1]
        assert any("no attempt-0 row" in reason for reason in coverage["ineligibility_reasons"])

    def test_unattributed_identity_is_ineligible_and_named(self) -> None:
        report = _report("run-1", developer=_developer(attributed=False), slices=[_slice(1), _slice(2)])
        coverage = lb.compute_run_coverage(report, _policy())
        assert coverage["eligible_for_first_submission"] is False
        assert any("unattributed" in reason for reason in coverage["ineligibility_reasons"])

    def test_incomplete_pm_status_is_ineligible_and_named(self) -> None:
        report = _report("run-1", pm_status="active", slices=[_slice(1), _slice(2)])
        coverage = lb.compute_run_coverage(report, _policy())
        assert coverage["eligible_for_first_submission"] is False
        assert any("pm_status='active'" in reason for reason in coverage["ineligibility_reasons"])

    def test_a_complete_stopped_followed_by_stop_is_still_judged_on_recorded_pm_status(self) -> None:
        # run_status.pm_status is read verbatim from the report -- this
        # tool recomputes nothing PM already recorded (AGENTS.md).
        report = _report("run-1", pm_status="stopped", slices=[_slice(1), _slice(2)])
        coverage = lb.compute_run_coverage(report, _policy())
        assert coverage["pm_status"] == "stopped"
        assert coverage["eligible_for_first_submission"] is False


class TestRenderMarkdown:
    def test_opening_sentence_and_glossary_present(self, tmp_path: Path) -> None:
        _write_report(tmp_path, "run-1", _report("run-1"))
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)
        markdown = lb.render_markdown(leaderboard, reports, policy)
        assert (
            "First-submission ability and supervised outcomes for the frozen two-slice task. Higher "
            "correctness is better; smaller edits and shorter elapsed time are supporting measures."
        ) in markdown
        assert "## Glossary" in markdown
        assert "## Developer -- first submission" in markdown
        assert "## Developer -- supervised outcome" in markdown

    def test_first_submission_table_lists_rank_and_correctness(self, tmp_path: Path) -> None:
        strong = [_slice(1, first_attempt=_attempt(by_obligation={"g": {"passed": 4, "total": 4, "fraction": 1.0}}))]
        _write_report(tmp_path, "run-1", _report("run-1", model="strong/model", slices=strong))
        reports = lb.discover_reports(tmp_path)
        policy = _policy(expected_slices=1)
        leaderboard, _problems = lb.build_leaderboard(reports, policy)

        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert f"[`{_configuration_key('strong/model')}`](#{lb._config_anchor(_configuration_key('strong/model'))})" in markdown
        assert "100.0% (n=1)" in markdown

    def test_supervised_outcome_table_uses_same_row_order(self, tmp_path: Path) -> None:
        strong = [_slice(1, first_attempt=_attempt(by_obligation={"g": {"fraction": 1.0}}))]
        weak = [_slice(1, first_attempt=_attempt(by_obligation={"g": {"fraction": 0.1}}))]
        _write_report(tmp_path, "run-1", _report("run-1", model="strong/model", slices=strong))
        _write_report(tmp_path, "run-2", _report("run-2", model="weak/model", slices=weak))
        reports = lb.discover_reports(tmp_path)
        policy = _policy(expected_slices=1)
        leaderboard, _problems = lb.build_leaderboard(reports, policy)

        markdown = lb.render_markdown(leaderboard, reports, policy)
        first_table = markdown.index("## Developer -- first submission")
        second_table = markdown.index("## Developer -- supervised outcome")
        first_section = markdown[first_table:second_table]
        second_section = markdown[second_table:]
        assert first_section.index("strong/model") < first_section.index("weak/model")
        assert second_section.index("strong/model") < second_section.index("weak/model")

    def test_ordinal_fix_shows_accepted_on_attempt_2_of_2(self, tmp_path: Path) -> None:
        # The literal defect this stage fixes (docs/LEADERBOARD-EVALUATION-
        # 2026-09-13.md): a slice accepted on its SECOND of two attempts
        # must read "attempt 2 of 2", not "attempt 1 of 2" (the 0-based
        # ordinal interpolated raw beside the 1-based total).
        attempt = _attempt(by_obligation={"g": {"passed": 5, "total": 5, "fraction": 1.0}})
        _write_report(
            tmp_path,
            "run-1",
            _report("run-1", slices=[_slice(1, final_attempt=attempt, attempts_total=2, accepted_at_attempt=1), _slice(2)]),
        )
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)

        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert "#### Slice 1 -- accepted on attempt 2 of 2" in markdown
        assert "accepted on attempt 1 of 2" not in markdown

    def test_unaccepted_slice_heading_names_its_status_not_an_attempt_number(self, tmp_path: Path) -> None:
        report = _report(
            "run-1",
            slices=[_slice(1, final_attempt=None, first_attempt=None, accepted_at_attempt=None, attempts_total=4, slice_status="abandoned"), _slice(2)],
        )
        _write_report(tmp_path, "run-1", report)
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)

        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert "#### Slice 1 -- abandoned after 4 attempt(s)" in markdown
        assert "_No final attempt graded._" in markdown

    def test_attempt_history_table_includes_an_attempt_with_no_commissioned_review(self, tmp_path: Path) -> None:
        trajectory = [
            {"attempt": 0, "pm_attempts_counter": 0, "commit_sha": "sha-a", "correctness": {"hidden_tests_passed": 3, "hidden_tests_total": 4}, "pm_decision": "steer", "commissioned_reviews": []},
            {"attempt": 1, "pm_attempts_counter": 1, "commit_sha": "sha-b", "correctness": {"hidden_tests_passed": 4, "hidden_tests_total": 4}, "pm_decision": "accept", "commissioned_reviews": [{"skill": "drift-audit", "review_id": None}]},
        ]
        report = _report("run-1", slices=[_slice(1, attempts_total=2, accepted_at_attempt=1, attempt_trajectory=trajectory), _slice(2)])
        _write_report(tmp_path, "run-1", report)
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)

        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert "| 1 | `sha-a` | 3/4 | steer | none |" in markdown
        assert "| 2 | `sha-b` | 4/4 | accept | drift-audit |" in markdown

    def test_review_history_table_shows_two_reviews_of_one_attempt(self, tmp_path: Path) -> None:
        review_trends = {
            "drift_review": [{"attempt": 0, "skill": "drift-audit", "tool": "opencode", "model": "gpt-5.6-luna", "at": "2026-09-12T11:21:03Z", "event_index": None, "verdict": "PASS", "findings_by_severity": {}}],
            "code_review": [{"attempt": 0, "skill": "code-review", "tool": "opencode", "model": "gpt-5.6-luna", "at": "2026-09-12T11:22:51Z", "event_index": None, "parse_error": "malformed finding line"}],
        }
        report = _report("run-1", slices=[_slice(1, review_trends=review_trends), _slice(2)])
        _write_report(tmp_path, "run-1", report)
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)

        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert "Reviews of each attempt -- multiple rows can refer to the same submission." in markdown
        # Recorded-time order: drift (11:21:03) before code (11:22:51) --
        # the exact trial-6-slice-1 case the plan names.
        drift_idx = markdown.index("drift_review | opencode / gpt-5.6-luna")
        code_idx = markdown.index("code_review | opencode / gpt-5.6-luna")
        assert drift_idx < code_idx
        assert "parse error: malformed finding line" in markdown
        assert "not yet captured for these reviews (Stage 4)" in markdown

    def test_review_history_table_is_order_unavailable_with_no_time_or_index(self, tmp_path: Path) -> None:
        review_trends = {
            "drift_review": [{"attempt": 0, "skill": "drift-audit", "tool": "opencode", "model": "m", "at": None, "event_index": None, "verdict": "PASS"}],
        }
        report = _report("run-1", slices=[_slice(1, review_trends=review_trends), _slice(2)])
        _write_report(tmp_path, "run-1", report)
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)

        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert "Order-unavailable" in markdown

    def test_run_anchor_is_stable_independent_of_rank_and_model_name(self) -> None:
        assert lb._run_anchor("20260912T105700Z-c207d3") == "run-20260912t105700z-c207d3"

    def test_unattributed_run_section_is_rendered(self, tmp_path: Path) -> None:
        _write_report(tmp_path, "run-1", _report("run-1", developer=_developer(attributed=False)))
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)

        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert "## Unattributed runs" in markdown
        assert "run-1" in markdown[markdown.index("## Unattributed runs") :]

    def test_run_index_lists_every_discovered_run(self, tmp_path: Path) -> None:
        _write_report(tmp_path, "run-1", _report("run-1"))
        _write_report(tmp_path, "run-2", _report("run-2", developer=_developer(attributed=False)))
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)

        markdown = lb.render_markdown(leaderboard, reports, policy)
        run_index = markdown[markdown.index("## Run index") :]
        assert "run-1" in run_index
        assert "run-2" in run_index

    def test_problems_are_stored_once_not_repeated_per_model(self, tmp_path: Path) -> None:
        report = _report("run-1", slices=[_slice(1, final_attempt=None, first_attempt=None, accepted_at_attempt=None), _slice(2)])
        _write_report(tmp_path, "run-1", report)
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)

        markdown = lb.render_markdown(leaderboard, reports, policy)

        problem_text = "no final attempt to grade correctness from"
        assert markdown.count(problem_text) == 1
        assert "problem(s) attributed to this configuration -- see Problems below" in markdown

    def test_pm_subjective_rating_is_quoted_verbatim_and_labeled_never_blended(self, tmp_path: Path) -> None:
        report = _report("run-1", rating_available=True, rating_text="Process discipline: 5/5\nOutput quality: 4/5")
        _write_report(tmp_path, "run-1", report)
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)

        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert "never blended into any score" in markdown
        assert "> Process discipline: 5/5" in markdown
        assert "> Output quality: 4/5" in markdown

    def test_unavailable_rating_is_not_rendered(self, tmp_path: Path) -> None:
        report = _report("run-1", rating_available=False, rating_text=None)
        _write_report(tmp_path, "run-1", report)
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)

        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert "PM's subjective rating" not in markdown

    def test_obligation_table_falls_back_to_question_mark_for_missing_counts(self, tmp_path: Path) -> None:
        attempt = _attempt(by_obligation={"g": {"fraction": 0.5}})  # no passed/total keys
        _write_report(tmp_path, "run-1", _report("run-1", slices=[_slice(1, final_attempt=attempt), _slice(2)]))
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)

        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert "| `g` | ?/? | 0.500 |" in markdown

    def test_pipe_and_backtick_in_model_name_render_through_the_full_pipeline(self, tmp_path: Path) -> None:
        # One end-to-end check that render_markdown() actually calls
        # _code_span/_md_cell where it should -- their own escaping rules
        # are covered directly by TestCodeSpan/TestMdCell below.
        _write_report(tmp_path, "run-1", _report("run-1", model="weird`model|name"))
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)

        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert lb._code_span(_configuration_key("weird`model|name")) in markdown

    def test_model_report_missing_from_disk_is_named_not_crashed(self, tmp_path: Path) -> None:
        # aggregate_model() folds a run's data into leaderboard.json from
        # whatever model-report.json files existed at build time; if one is
        # since deleted before render_markdown() re-reads it (passed
        # `reports` no longer has an entry for that run_id), it must be
        # named, not KeyError.
        _write_report(tmp_path, "run-1", _report("run-1"))
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)

        markdown = lb.render_markdown(leaderboard, [], policy)

        assert "model-report.json no longer on disk" in markdown


class TestCodeSpan:
    def test_widens_the_fence_past_embedded_backticks_without_altering_content(self) -> None:
        assert lb._code_span("foo") == "`foo`"
        # Content is never substituted -- two names differing only by a
        # backtick must stay distinguishable in the rendered output.
        assert lb._code_span("vendor`model") == "``vendor`model``"
        assert lb._code_span("vendor'model") == "`vendor'model`"
        assert lb._code_span("`leading") == "`` `leading ``"

    def test_pipe_is_escaped_but_a_pre_existing_backslash_is_not_doubled(self) -> None:
        # Pipe is escaped defensively, same as _md_cell (whether GFM's
        # table-cell splitter honours a code span's own boundary around an
        # embedded pipe isn't worth gambling on). But unlike _md_cell, a
        # pre-existing backslash is never doubled: a code span's content is
        # taken completely literally for backslash, so doubling would
        # visibly show two characters where the source had one.
        assert lb._code_span("a|b\\c") == "`a\\|b\\c`"

    def test_newline_becomes_a_space(self) -> None:
        assert lb._code_span("weird\nmodel") == "`weird model`"


class TestMdCell:
    def test_escapes_pipe_and_pre_existing_backslash_and_normalizes_newlines(self) -> None:
        assert lb._md_cell("a|b") == "a\\|b"
        # A naive `"|" -> "\|"` replacement over text that already contains
        # a literal backslash right before a pipe would produce `\\|`,
        # which GFM reads as an escaped backslash followed by an unescaped,
        # row-breaking pipe. Escaping every backslash first avoids that.
        assert lb._md_cell("weird\\|model") == "weird" + "\\" * 3 + "|model"
        assert lb._md_cell("a\nb") == "a b"

    def test_no_problems_renders_none(self, tmp_path: Path) -> None:
        _write_report(tmp_path, "run-1", _report("run-1"))
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)

        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert "## Problems" in markdown
        assert "None." in markdown


class TestSlug:
    def test_lowercases_and_collapses_non_alphanumerics(self) -> None:
        assert lb._slug("github-copilot/gpt-5.6-luna · opencode · low") == "github-copilot-gpt-5-6-luna-opencode-low"

    def test_stable_for_the_same_input(self) -> None:
        assert lb._slug("Some Run-ID_123") == lb._slug("Some Run-ID_123")


class TestMain:
    def test_writes_leaderboard_and_returns_0_on_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        root = tmp_path / "bench-root"
        _write_report(root / "results" / "runs", "run-1", _report("run-1"))
        policy_path = root / "policy.yaml"
        policy_path.parent.mkdir(parents=True, exist_ok=True)
        policy_path.write_text(yaml.safe_dump({"leaderboard": {"expected_slices": 2}}), encoding="utf-8")
        monkeypatch.setattr(lb, "bench_root", lambda: root)

        exit_code = lb.main([])

        assert exit_code == 0
        out_path = root / "results" / "leaderboard.json"
        assert out_path.is_file()
        written = json.loads(out_path.read_text(encoding="utf-8"))
        assert written["models"][0]["model"] == _configuration_key("opencode/some-model")
        md_path = root / "results" / "leaderboard.md"
        assert md_path.is_file()
        assert "opencode/some-model" in md_path.read_text(encoding="utf-8")

    def test_markdown_out_override_writes_to_the_given_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        root = tmp_path / "bench-root"
        _write_report(root / "results" / "runs", "run-1", _report("run-1"))
        policy_path = root / "policy.yaml"
        policy_path.parent.mkdir(parents=True, exist_ok=True)
        policy_path.write_text(yaml.safe_dump({"leaderboard": {"expected_slices": 2}}), encoding="utf-8")
        monkeypatch.setattr(lb, "bench_root", lambda: root)
        custom_md = tmp_path / "elsewhere" / "custom-leaderboard.md"

        exit_code = lb.main(["--markdown-out", str(custom_md)])

        assert exit_code == 0
        assert custom_md.is_file()
        assert not (root / "results" / "leaderboard.md").exists()

    def test_a_render_markdown_failure_writes_neither_output_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        # render_markdown() runs before either file is written, so a bug in
        # it can never leave leaderboard.json updated to a new generation
        # while leaderboard.md is still stale (or missing).
        root = tmp_path / "bench-root"
        _write_report(root / "results" / "runs", "run-1", _report("run-1"))
        policy_path = root / "policy.yaml"
        policy_path.parent.mkdir(parents=True, exist_ok=True)
        policy_path.write_text(yaml.safe_dump({"leaderboard": {"expected_slices": 2}}), encoding="utf-8")
        monkeypatch.setattr(lb, "bench_root", lambda: root)
        monkeypatch.setattr(lb, "render_markdown", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("boom")))

        with pytest.raises(RuntimeError, match="boom"):
            lb.main([])

        assert not (root / "results" / "leaderboard.json").exists()
        assert not (root / "results" / "leaderboard.md").exists()

    def test_returns_1_when_problems_are_reported(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        root = tmp_path / "bench-root"
        report = _report("run-1", slices=[_slice(1, final_attempt=None, first_attempt=None, accepted_at_attempt=None), _slice(2)])
        _write_report(root / "results" / "runs", "run-1", report)
        policy_path = root / "policy.yaml"
        policy_path.parent.mkdir(parents=True, exist_ok=True)
        policy_path.write_text(yaml.safe_dump({"leaderboard": {"expected_slices": 2}}), encoding="utf-8")
        monkeypatch.setattr(lb, "bench_root", lambda: root)

        assert lb.main([]) == 1
