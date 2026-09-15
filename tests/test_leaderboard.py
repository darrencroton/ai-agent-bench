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


def _size_complexity(
    *,
    production_loc_net: int | None = 10,
    production_cc_net: int | None = 2,
    loc_available: bool = True,
    cc_available: bool = True,
    baseline_commit: str = "before-head",
) -> dict[str, Any]:
    """A `size_complexity` block shaped like dev_check.compute_size_complexity's
    real output (Stage 3, docs/LEADERBOARD-REBUILD-PLAN.md) -- only the
    fields leaderboard.py's own aggregation/rendering reads."""
    loc: dict[str, Any] = {"available": loc_available}
    if loc_available:
        loc["buckets"] = {"production": {"added": max(production_loc_net or 0, 0), "deleted": 0, "net": production_loc_net}}
    else:
        loc["error"] = "endpoint: health.py exited 2"
    complexity: dict[str, Any] = {"available": cc_available}
    if cc_available:
        complexity["production"] = {"baseline_total": 10, "endpoint_total": 10 + (production_cc_net or 0), "net": production_cc_net}
        complexity["coverage_note"] = None
    else:
        complexity["error"] = "baseline: health.py exited 2"
    return {
        "metric_version": 1,
        "baseline_commit": baseline_commit,
        "endpoint_commit": "endpoint-head",
        "loc": loc,
        "complexity": complexity,
    }


_ATTEMPT_SIZE_COMPLEXITY_UNSET = object()


def _attempt(
    *,
    attempt: int = 0,
    by_obligation: dict[str, dict[str, float]] | None = None,
    lint: dict[str, Any] | None = None,
    health: dict[str, Any] | None = None,
    violations: list[str] | None = None,
    pm_decision: str = "accept",
    size_complexity: dict[str, Any] | None | object = _ATTEMPT_SIZE_COMPLEXITY_UNSET,
) -> dict[str, Any]:
    entry = {
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
    # Default: no size_complexity data at all (a sheet graded before Stage
    # 3, or a test that doesn't care) -- distinct from `size_complexity=None`,
    # which a caller can still pass explicitly if that distinction ever
    # matters; both read as "unavailable" downstream.
    if size_complexity is not _ATTEMPT_SIZE_COMPLEXITY_UNSET:
        entry["size_complexity"] = size_complexity
    return entry


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
    reviews: list[dict[str, Any]] | None = None,
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
        "reviews": reviews if reviews is not None else [],
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


def _pm_rating(*, status: str = "rated", score: int | None = 2, reason: str | None = "r") -> dict[str, Any]:
    """A `reviews` entry's `pm_rating` field (Stage 4b,
    docs/LEADERBOARD-REBUILD-PLAN.md) -- the shape
    `model_report.resolve_pm_judgments` stamps onto every entry."""
    if status == "unjudged":
        return {"status": "unjudged", "score": None, "reason": None, "at": None, "judgment_id": None}
    return {"status": status, "score": score if status == "rated" else None, "reason": reason, "at": None, "judgment_id": "j"}


def _judged_review(
    *,
    skill: str = "code-review",
    tool: str = "claude",
    model: str = "m",
    effort: str | None = None,
    rating_status: str = "rated",
    score: int | None = 2,
) -> dict[str, Any]:
    """A minimal `reviews` entry (Stage 4b) -- only the keys
    `aggregate_reviewers` itself reads."""
    return {
        "skill": skill,
        "tool": tool,
        "model": model,
        "effort": effort,
        "pm_rating": _pm_rating(status=rating_status, score=score),
    }


def _comparison(
    *, skill: str = "code-review", judgment_id: str = "j", rank_groups: list[list[dict[str, Any]]]
) -> dict[str, Any]:
    """A resolved run-level comparison judgment (Stage 4b) -- the shape
    `model_report.resolve_pm_judgments` appends onto `pm_judgments.comparisons`."""
    return {"slice": "Slice 1", "skill": skill, "judgment_id": judgment_id, "at": None, "reason": None, "rank_groups": rank_groups}


def _reviewer_ref(review_id: str, *, tool: str = "claude", model: str, effort: str | None = None) -> dict[str, Any]:
    return {"review_id": review_id, "tool": tool, "model": model, "effort": effort}


def _report_with_reviews(
    run_id: str, reviews: list[dict[str, Any]], *, comparisons: list[dict[str, Any]] | None = None, **kwargs: Any
) -> dict[str, Any]:
    """A `_report()` whose first slice carries `reviews` and whose
    run-level `pm_judgments.comparisons` carries `comparisons` -- the two
    inputs `aggregate_reviewers` (Stage 4b) reads."""
    report = _report(run_id, **kwargs)
    report["slices"][0]["reviews"] = reviews
    report["pm_judgments"] = {
        "available": True,
        "reason": None,
        "review_judgments_recorded": bool(reviews),
        "developer_judgments_recorded": False,
        "comparisons": comparisons or [],
    }
    return report


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
        reviews = [
            {"attempt": 0, "skill": "drift-audit", "tool": "opencode", "model": "gpt-5.6-luna",
             "at": "2026-09-12T11:21:03Z", "event_index": 11, "verdict": "PASS", "findings_by_severity": {},
             "superseded_by": None},
            {"attempt": 0, "skill": "code-review", "tool": "opencode", "model": "gpt-5.6-luna",
             "at": "2026-09-12T11:22:51Z", "event_index": 17, "parse_error": "malformed finding line",
             "superseded_by": None},
        ]
        report = _report("run-1", slices=[_slice(1, reviews=reviews), _slice(2)])
        _write_report(tmp_path, "run-1", report)
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)

        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert "Reviews of each attempt -- multiple rows can refer to the same submission." in markdown
        # event_index order: drift (11) before code (17) -- the exact
        # trial-6-slice-1 case the plan names, and the Role column holds the
        # record's own skill, never the old sheet field name.
        drift_idx = markdown.index("drift-audit | opencode / gpt-5.6-luna")
        code_idx = markdown.index("code-review | opencode / gpt-5.6-luna")
        assert drift_idx < code_idx
        assert "parse error: malformed finding line" in markdown

    def test_review_history_table_marks_a_superseded_retry(self, tmp_path: Path) -> None:
        """Trial 11 slice 1's real shape: a retry must never read as a
        second, independent vote (docs/LEADERBOARD-REBUILD-PLAN.md Stage 4a)."""
        reviews = [
            {"attempt": 1, "skill": "drift-audit", "tool": "claude", "model": "claude-haiku-4-5",
             "at": "2026-09-14T06:23:22Z", "event_index": 14, "parse_error": "report missing required section(s)",
             "superseded_by": 15},
            {"attempt": 1, "skill": "drift-audit", "tool": "claude", "model": "claude-haiku-4-5",
             "at": "2026-09-14T06:25:55Z", "event_index": 15, "verdict": "PASS", "findings_by_severity": {},
             "superseded_by": None},
        ]
        report = _report("run-1", slices=[_slice(1, reviews=reviews), _slice(2)])
        _write_report(tmp_path, "run-1", report)
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)

        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert "superseded by review at event 15" in markdown

    def test_review_history_table_is_order_unavailable_with_no_time_or_index(self, tmp_path: Path) -> None:
        reviews = [
            {"attempt": 0, "skill": "drift-audit", "tool": "opencode", "model": "m", "at": None,
             "event_index": None, "verdict": "PASS", "superseded_by": None},
        ]
        report = _report("run-1", slices=[_slice(1, reviews=reviews), _slice(2)])
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


# --- Stage 3 (docs/LEADERBOARD-REBUILD-PLAN.md): production size and ------
# --- complexity -------------------------------------------------------------


class TestAggregateModelSizeComplexity:
    def test_first_attempt_loc_and_cc_are_collected_per_slice(self) -> None:
        report = _report(
            "run-1",
            slices=[
                _slice(1, first_attempt=_attempt(size_complexity=_size_complexity(production_loc_net=10, production_cc_net=2))),
                _slice(2, first_attempt=_attempt(size_complexity=_size_complexity(production_loc_net=-3, production_cc_net=-1))),
            ],
        )
        entry, _problems = lb.aggregate_model("m", [(Path("x"), report)], _eligible_coverage("run-1"))
        assert entry["first_loc_by_slice"][1] == {"mean": 10.0, "min": 10, "max": 10, "n": 1}
        assert entry["first_cc_by_slice"][1] == {"mean": 2.0, "min": 2, "max": 2, "n": 1}
        assert entry["first_loc_by_slice"][2] == {"mean": -3.0, "min": -3, "max": -3, "n": 1}

    def test_final_attempt_loc_and_cc_do_not_require_first_submission_eligibility(self) -> None:
        # Same guard as final_attempt_correctness: an ineligible run still
        # contributes a final-attempt measurement.
        report = _report("run-1", slices=[_slice(1, final_attempt=_attempt(size_complexity=_size_complexity(production_loc_net=7)))])
        entry, _problems = lb.aggregate_model("m", [(Path("x"), report)], _ineligible_coverage("run-1"))
        assert entry["final_loc_by_slice"][1]["mean"] == 7.0
        assert entry["first_loc_by_slice"][1] is None

    def test_unavailable_measurement_is_none_not_a_fabricated_zero(self) -> None:
        report = _report(
            "run-1",
            slices=[_slice(1, first_attempt=_attempt(size_complexity=_size_complexity(loc_available=False, cc_available=False)))],
        )
        entry, _problems = lb.aggregate_model("m", [(Path("x"), report)], _eligible_coverage("run-1"))
        assert entry["first_loc_by_slice"][1] is None
        assert entry["first_cc_by_slice"][1] is None

    def test_a_slice_with_no_size_complexity_block_at_all_is_none(self) -> None:
        # The default _attempt() fixture -- a legacy/unmeasured sheet.
        report = _report("run-1", slices=[_slice(1, first_attempt=_attempt())])
        entry, _problems = lb.aggregate_model("m", [(Path("x"), report)], _eligible_coverage("run-1"))
        assert entry["first_loc_by_slice"][1] is None

    def test_first_attempt_production_loc_total_sums_across_slices(self) -> None:
        report = _report(
            "run-1",
            slices=[
                _slice(1, first_attempt=_attempt(size_complexity=_size_complexity(production_loc_net=10))),
                _slice(2, first_attempt=_attempt(size_complexity=_size_complexity(production_loc_net=5))),
            ],
        )
        entry, _problems = lb.aggregate_model("m", [(Path("x"), report)], _eligible_coverage("run-1"))
        assert entry["first_attempt_production_loc_total"] == pytest.approx(15.0)

    def test_first_attempt_production_loc_total_is_none_with_no_data(self) -> None:
        report = _report("run-1", slices=[_slice(1, first_attempt=_attempt())])
        entry, _problems = lb.aggregate_model("m", [(Path("x"), report)], _eligible_coverage("run-1"))
        assert entry["first_attempt_production_loc_total"] is None


class TestBuildLeaderboardSizeComplexityTiebreak:
    def test_ties_on_correctness_break_by_smaller_first_attempt_production_loc(self, tmp_path: Path) -> None:
        # Both configurations score identical correctness (1.0) -- the
        # smaller-edit configuration ("small/model", net +2) must rank
        # ahead of the larger one ("big/model", net +50), even though
        # "big/model" would sort first alphabetically.
        big = _report(
            "run-1", model="big/model",
            slices=[_slice(1, first_attempt=_attempt(size_complexity=_size_complexity(production_loc_net=50)))],
        )
        small = _report(
            "run-2", model="small/model",
            slices=[_slice(1, first_attempt=_attempt(size_complexity=_size_complexity(production_loc_net=2)))],
        )
        _write_report(tmp_path, "run-1", big)
        _write_report(tmp_path, "run-2", small)
        reports = lb.discover_reports(tmp_path)
        leaderboard, _problems = lb.build_leaderboard(reports, _policy(expected_slices=1))

        assert [m["model"] for m in leaderboard["models"]] == [
            _configuration_key("small/model"),
            _configuration_key("big/model"),
        ]
        # Still labelled tied -- the tie-break is not evidence of a better
        # correctness score.
        assert leaderboard["models"][1]["tied_with_previous"] is True

    def test_no_loc_data_on_either_side_falls_back_to_name(self, tmp_path: Path) -> None:
        _write_report(tmp_path, "run-1", _report("run-1", model="zeta/model"))
        _write_report(tmp_path, "run-2", _report("run-2", model="alpha/model"))
        reports = lb.discover_reports(tmp_path)
        leaderboard, _problems = lb.build_leaderboard(reports, _policy())
        assert [m["model"] for m in leaderboard["models"]] == [
            _configuration_key("alpha/model"),
            _configuration_key("zeta/model"),
        ]


class TestQualityAndScopeSummaries:
    def test_quality_summary_shows_measured_not_pass_with_a_finding_count(self) -> None:
        quality = {
            "lint_findings_by_tool": {"available": True, "verdict": "findings", "counts": {"ruff": 2}},
            "code_health_findings_by_category": {"available": True, "verdict": "measured", "counts": {"cyclomatic": 1}},
        }
        summary = lb._quality_summary(quality)
        assert "measured" in summary
        assert "pass" not in summary
        assert "1 finding(s)" in summary
        assert "2 finding(s)" in summary

    def test_scope_summary_lists_the_violating_paths(self) -> None:
        summary = lb._scope_summary({"violations": ["src/a.py", "src/b.py"]})
        assert "src/a.py" in summary
        assert "src/b.py" in summary
        assert "2 violation(s)" in summary

    def test_scope_summary_no_violations(self) -> None:
        assert lb._scope_summary({"violations": []}) == "no violations"


class TestSizeComplexitySummary:
    def test_available_measurements_are_summarised(self) -> None:
        summary = lb._size_complexity_summary(_size_complexity(production_loc_net=8, production_cc_net=-3))
        assert "ΔLOC" in summary
        assert "+8" in summary
        assert "ΔCC" in summary
        assert "-3" in summary
        assert "never scored" in summary

    def test_unavailable_measurements_are_named_not_a_silent_zero(self) -> None:
        summary = lb._size_complexity_summary(_size_complexity(loc_available=False, cc_available=False))
        assert "ΔLOC unavailable" in summary
        assert "ΔCC unavailable" in summary


class TestFmtNetSpread:
    def test_none_is_unavailable(self) -> None:
        assert lb._fmt_net_spread(None) == "unavailable"

    def test_single_value_shows_sign_and_n_one(self) -> None:
        assert lb._fmt_net_spread({"mean": 5.0, "min": 5, "max": 5, "n": 1}) == "+5 (n=1)"

    def test_negative_mean_keeps_its_sign(self) -> None:
        assert lb._fmt_net_spread({"mean": -5.0, "min": -5, "max": -5, "n": 1}) == "-5 (n=1)"


class TestRenderMarkdownSizeComplexity:
    def test_first_submission_table_has_loc_and_cc_columns(self, tmp_path: Path) -> None:
        _write_report(
            tmp_path, "run-1",
            _report("run-1", slices=[_slice(1, first_attempt=_attempt(size_complexity=_size_complexity(production_loc_net=12)))]),
        )
        reports = lb.discover_reports(tmp_path)
        policy = _policy(expected_slices=1)
        leaderboard, _problems = lb.build_leaderboard(reports, policy)
        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert "ΔLOC S1/S2" in markdown
        assert "ΔCC S1/S2" in markdown
        assert "+12" in markdown

    def test_supervised_outcome_table_has_final_loc_and_cc_columns(self, tmp_path: Path) -> None:
        _write_report(
            tmp_path, "run-1",
            _report("run-1", slices=[_slice(1, final_attempt=_attempt(size_complexity=_size_complexity(production_loc_net=-4)))]),
        )
        reports = lb.discover_reports(tmp_path)
        policy = _policy(expected_slices=1)
        leaderboard, _problems = lb.build_leaderboard(reports, policy)
        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert "Final ΔLOC S1/S2" in markdown
        assert "Final ΔCC S1/S2" in markdown
        assert "-4" in markdown

    def test_a_slice_with_no_measurement_renders_unavailable_not_zero(self, tmp_path: Path) -> None:
        _write_report(tmp_path, "run-1", _report("run-1", slices=[_slice(1, first_attempt=_attempt())]))
        reports = lb.discover_reports(tmp_path)
        policy = _policy(expected_slices=1)
        leaderboard, _problems = lb.build_leaderboard(reports, policy)
        markdown = lb.render_markdown(leaderboard, reports, policy)

        first_table = markdown.index("## Developer -- first submission")
        second_table = markdown.index("## Developer -- supervised outcome")
        row = [line for line in markdown[first_table:second_table].splitlines() if line.startswith("| 1")][0]
        assert "unavailable" in row

    def test_glossary_defines_loc_as_net_physical_lines_and_cc_as_descriptive(self, tmp_path: Path) -> None:
        _write_report(tmp_path, "run-1", _report("run-1"))
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)
        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert "net physical lines" in markdown
        assert "never scored" in markdown
        # Stage 4b: the old "Code/drift reviewer ... Stage 4's job" glossary
        # placeholder is gone, replaced by real glossary entries for the
        # new PM-judgment metrics.
        assert "Comparative rank score" in markdown
        assert "PM rating (mean /2, n)" in markdown

    def test_scope_alert_appears_when_a_run_has_violations(self, tmp_path: Path) -> None:
        _write_report(
            tmp_path, "run-1",
            _report("run-1", slices=[_slice(1, final_attempt=_attempt(violations=["src/unauthorized.py"]))]),
        )
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)
        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert "Scope alert" in markdown
        assert "src/unauthorized.py" in markdown

    def test_no_scope_alert_when_no_run_has_violations(self, tmp_path: Path) -> None:
        _write_report(tmp_path, "run-1", _report("run-1"))
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)
        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert "Scope alert" not in markdown


class TestMeasurementMetricVersionInLeaderboard:
    def test_metric_version_is_collected_from_reports(self, tmp_path: Path) -> None:
        report = _report("run-1")
        report["measurement_metric_version"] = 1
        _write_report(tmp_path, "run-1", report)
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)
        assert leaderboard["measurement_metric_versions"] == [1]
        markdown = lb.render_markdown(leaderboard, reports, policy)
        assert "Measurement metric_version: 1" in markdown

    def test_no_metric_version_anywhere_renders_honestly(self, tmp_path: Path) -> None:
        _write_report(tmp_path, "run-1", _report("run-1"))
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)
        assert leaderboard["measurement_metric_versions"] == []
        markdown = lb.render_markdown(leaderboard, reports, policy)
        assert "none recorded" in markdown


class TestRankPoints:
    """`lb._rank_points` (Stage 4b, docs/LEADERBOARD-REBUILD-PLAN.md):
    normalized `(N-r)/(N-1)` rank points from a best-first `rank_groups`
    list, with a tied group sharing the mean occupied rank. Synthetic
    fixtures throughout: the cohort's real panels (trials 12-14, four
    code-review models per submission) are all size 4, so panel sizes 2 and
    3, disconnected groups, and the degenerate cases only ever get
    exercised here."""

    def test_singleton_panel_has_no_comparative_score(self) -> None:
        assert lb._rank_points([[{"review_id": "r1"}]]) == []

    def test_panel_of_two_gives_full_points_to_the_winner(self) -> None:
        rank_groups = [[{"review_id": "a"}], [{"review_id": "b"}]]
        points = {review["review_id"]: p for review, p in lb._rank_points(rank_groups)}
        assert points == {"a": 1.0, "b": 0.0}

    def test_panel_of_three_with_a_tied_group_shares_the_mean_rank(self) -> None:
        rank_groups = [[{"review_id": "a"}], [{"review_id": "b"}, {"review_id": "c"}]]
        points = {review["review_id"]: p for review, p in lb._rank_points(rank_groups)}
        assert points["a"] == pytest.approx(1.0)
        assert points["b"] == pytest.approx(0.25)
        assert points["c"] == pytest.approx(0.25)

    def test_a_three_way_tie_for_first_gives_every_member_the_same_points(self) -> None:
        rank_groups = [[{"review_id": "a"}, {"review_id": "b"}, {"review_id": "c"}]]
        points = {review["review_id"]: p for review, p in lb._rank_points(rank_groups)}
        # Mean occupied rank for a 3-way tie spanning ranks 1-3 is 2, so
        # every member gets the SAME points -- an entirely-tied panel is,
        # correctly, indistinguishable from a coin flip.
        assert points["a"] == points["b"] == points["c"] == pytest.approx(0.5)


class TestAggregateReviewers:
    """`lb.aggregate_reviewers` (Stage 4b) -- PM rating and comparative
    aggregation per reviewer configuration, per skill."""

    def test_rated_reviews_produce_a_rating_spread(self) -> None:
        report = _report_with_reviews("run-1", [_judged_review(score=2), _judged_review(score=0)])
        rows = lb.aggregate_reviewers([(Path("x"), report)])["code-review"]
        assert len(rows) == 1
        row = rows[0]
        assert row["rating"]["mean"] == 1.0
        assert row["rated_count"] == 2
        assert row["unacceptable_count"] == 1

    def test_unavailable_reviews_are_counted_separately_never_blended_as_zero(self) -> None:
        report = _report_with_reviews("run-1", [_judged_review(score=2), _judged_review(rating_status="unavailable")])
        row = lb.aggregate_reviewers([(Path("x"), report)])["code-review"][0]
        assert row["rating"]["mean"] == 2.0
        assert row["rated_count"] == 1
        assert row["unavailable_count"] == 1

    def test_unjudged_reviews_do_not_affect_the_rating(self) -> None:
        report = _report_with_reviews("run-1", [_judged_review(rating_status="unjudged")])
        row = lb.aggregate_reviewers([(Path("x"), report)])["code-review"][0]
        assert row["rating"] is None
        assert row["rated_count"] == 0

    def test_singleton_panel_comparison_has_no_comparative_score(self) -> None:
        report = _report_with_reviews(
            "run-1",
            [_judged_review()],
            comparisons=[_comparison(rank_groups=[[_reviewer_ref("r1", model="m")]])],
        )
        row = lb.aggregate_reviewers([(Path("x"), report)])["code-review"][0]
        assert row["comparative_score"] is None
        assert row["rounds"] == 1
        assert row["panel_sizes"] == [1]

    def test_panel_of_two_produces_a_comparative_score(self) -> None:
        report = _report_with_reviews(
            "run-1",
            [_judged_review(model="a"), _judged_review(model="b")],
            comparisons=[_comparison(rank_groups=[[_reviewer_ref("r1", model="a")], [_reviewer_ref("r2", model="b")]])],
        )
        rows = {row["identity"]["model"]: row for row in lb.aggregate_reviewers([(Path("x"), report)])["code-review"]}
        assert rows["a"]["comparative_score"]["mean"] == 1.0
        assert rows["b"]["comparative_score"]["mean"] == 0.0
        assert rows["a"]["comparative_globally_comparable"] is True
        assert rows["b"]["comparative_globally_comparable"] is True

    def test_disconnected_comparison_groups_are_marked_not_globally_comparable(self) -> None:
        # Two 2-reviewer panels that never share a reviewer -- a's/b's
        # points come from an entirely different opponent pool than c's/d's.
        report = _report_with_reviews(
            "run-1",
            [_judged_review(model=m) for m in ("a", "b", "c", "d")],
            comparisons=[
                _comparison(judgment_id="j1", rank_groups=[[_reviewer_ref("r1", model="a")], [_reviewer_ref("r2", model="b")]]),
                _comparison(judgment_id="j2", rank_groups=[[_reviewer_ref("r3", model="c")], [_reviewer_ref("r4", model="d")]]),
            ],
        )
        rows = lb.aggregate_reviewers([(Path("x"), report)])["code-review"]
        scored = [row for row in rows if row["comparative_score"] is not None]
        assert len(scored) == 4
        assert all(row["comparative_globally_comparable"] is False for row in scored)

    def test_drift_audit_and_code_review_are_kept_separate(self) -> None:
        report = _report_with_reviews("run-1", [_judged_review(skill="drift-audit", score=1)])
        reviewers = lb.aggregate_reviewers([(Path("x"), report)])
        assert reviewers["code-review"] == []
        assert len(reviewers["drift-audit"]) == 1

    def test_no_reviews_or_comparisons_produces_empty_rows_for_both_skills(self) -> None:
        reviewers = lb.aggregate_reviewers([(Path("x"), _report("run-1"))])
        assert reviewers == {"code-review": [], "drift-audit": []}


class TestReviewerTables:
    """Render-level tests for Table 3 ('Code reviewer -- PM-assessed
    utility') and Table 4 ('Drift reviewer -- PM-assessed acceptability'),
    docs/LEADERBOARD-REBUILD-PLAN.md Stage 4b -- these replace the old
    placeholder paragraph that deferred both tables to "Stage 4's job"."""

    def test_code_reviewer_table_shows_rating_and_explains_an_all_singleton_role(self, tmp_path: Path) -> None:
        report = _report_with_reviews(
            "run-1",
            [_judged_review(score=2)],
            comparisons=[_comparison(rank_groups=[[_reviewer_ref("r1", model="m")]])],
        )
        _write_report(tmp_path, "run-1", report)
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)
        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert "## Code reviewer -- PM-assessed utility" in markdown
        assert "single reviewer -- no comparative score" in markdown
        assert "2.0/2 (n=1)" in markdown
        # The table's own prose must say reviews DID happen -- never read as
        # an empty or broken table. This is a DERIVED statement (no row has
        # an eligible round), not a hardcoded cohort fact -- see the mixed
        # fixture below, which renders different prose from the same table.
        assert "Every code-review panel in this cohort is a singleton" in markdown
        assert "the role's real shape today" in markdown

    def test_code_reviewer_table_reports_a_real_multi_model_panel_when_one_exists(self, tmp_path: Path) -> None:
        # A genuine N=2 panel (a vs b) alongside b's own separate singleton
        # commission -- exercises the "some eligible rounds" branch of the
        # panel-shape derivation, and checks a singleton row's cell still
        # reads the same "no comparative score" text within a mixed table.
        report = _report_with_reviews(
            "run-1",
            [_judged_review(model="a", score=2), _judged_review(model="b", score=1), _judged_review(model="c", score=2)],
            comparisons=[
                _comparison(judgment_id="j1", rank_groups=[[_reviewer_ref("r1", model="a")], [_reviewer_ref("r2", model="b")]]),
                _comparison(judgment_id="j2", rank_groups=[[_reviewer_ref("r3", model="c")]]),
            ],
        )
        _write_report(tmp_path, "run-1", report)
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)
        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert "## Code reviewer -- PM-assessed utility" in markdown
        assert "This cohort includes real multi-model code-review panels" in markdown
        assert "Observed multi-model panel sizes: 2." in markdown
        # c never appeared in an eligible round -- its row still reads the
        # ordinary singleton cell, called out as a real property, not a gap.
        assert "single reviewer -- no comparative score" in markdown
        # It must not also claim every panel is a singleton -- that would
        # contradict the real panel just rendered above.
        assert "Every code-review panel in this cohort is a singleton" not in markdown

    def test_drift_reviewer_table_shows_unacceptable_over_assessed(self, tmp_path: Path) -> None:
        report = _report_with_reviews("run-1", [_judged_review(skill="drift-audit", score=0), _judged_review(skill="drift-audit", score=2)])
        _write_report(tmp_path, "run-1", report)
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)
        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert "## Drift reviewer -- PM-assessed acceptability" in markdown
        assert "| 1/2 |" in markdown
        # The table's own prose must tell a reader that blocking is good
        # reviewing, so a low-rated drift reviewer is never read as "it
        # failed the Developer too often" (docs/LEADERBOARD-REBUILD-PLAN.md
        # Stage 4: "finding a real violation is good reviewing").
        assert "finding a real violation is good reviewing" in markdown
        assert "Nothing in this table enters any Developer number." in markdown
        # Drift-audit is never ranked against other reviewers, so this table
        # has no comparative column and carries no panel-shape note either:
        # panel shape has no bearing on anything rendered here, and saying
        # it would send a reader looking for a column that does not exist.
        assert "drift-audit panel" not in markdown

    def test_a_reliability_outcome_is_shown_separately_never_as_a_poor_rating(self, tmp_path: Path) -> None:
        report = _report_with_reviews("run-1", [_judged_review(skill="drift-audit", score=2), _judged_review(skill="drift-audit", rating_status="unavailable")])
        _write_report(tmp_path, "run-1", report)
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)
        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert "2.0/2 (n=1) (+1 unavailable)" in markdown

    def test_no_commissions_at_all_reads_as_an_explicit_absence(self, tmp_path: Path) -> None:
        _write_report(tmp_path, "run-1", _report("run-1"))
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)
        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert "No `code-review` commissions recorded" in markdown
        assert "No `drift-audit` commissions recorded" in markdown

    def test_pm_developer_rating_column_appears_in_supervised_outcome_table(self, tmp_path: Path) -> None:
        trajectory = [
            {
                "attempt": 0,
                "pm_attempts_counter": 0,
                "commit_sha": "sha-0",
                "correctness": {"hidden_tests_passed": 4, "hidden_tests_total": 4},
                "pm_decision": "accept",
                "commissioned_reviews": [],
                "pm_developer_judgment": {"status": "rated", "score": 2, "reason": "r", "at": None, "judgment_id": "j"},
            }
        ]
        report = _report("run-1", slices=[_slice(1, attempt_trajectory=trajectory), _slice(2)])
        _write_report(tmp_path, "run-1", report)
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)
        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert "PM Developer rating (mean /2, n)" in markdown
        assert "2.0/2 (n=1)" in markdown

    def test_no_pm_developer_judgment_at_all_renders_the_no_ratings_label(self, tmp_path: Path) -> None:
        _write_report(tmp_path, "run-1", _report("run-1"))
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)
        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert "no PM ratings recorded" in markdown
