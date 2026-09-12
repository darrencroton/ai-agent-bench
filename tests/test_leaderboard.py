"""Tests for tools/leaderboard.py (Tool 5: the cross-model leaderboard).

Fixtures are hand-written model-report.json documents under `tmp_path`,
matching the real shape Tool 4 (model_report.py) writes
(docs/MODE2-REWRITE-PLAN.md §6). No git, no subprocess: this tool only
reads already-graded JSON already on disk.
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

_DEFAULT_WEIGHTS = {"correctness": 0.5, "quality": 0.25, "scope": 0.15, "iterations": 0.10}


def _policy(weights: dict[str, float] | None = None, **overrides: Any) -> dict[str, Any]:
    return {
        "weights": weights if weights is not None else dict(_DEFAULT_WEIGHTS),
        "scope_violation_penalty": overrides.get("scope_violation_penalty", 0.2),
        "iteration_reference_attempts": overrides.get("iteration_reference_attempts", 3),
    }


def _quality_tool(*, available: bool = True, verdict: str = "pass") -> dict[str, Any]:
    return {"available": available, "verdict": verdict}


def _final_attempt(
    *,
    by_obligation: dict[str, dict[str, float]] | None = None,
    lint: dict[str, Any] | None = None,
    health: dict[str, Any] | None = None,
    violations: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "attempt": 0,
        "correctness": {"by_obligation": by_obligation if by_obligation is not None else {"g1": {"fraction": 1.0}}},
        "quality": {
            "lint_findings_by_tool": lint if lint is not None else _quality_tool(),
            "code_health_findings_by_category": health if health is not None else _quality_tool(),
        },
        "scope": {"violations": violations or []},
    }


_UNSET = object()


def _slice(
    slice_number: int,
    *,
    final_attempt: dict[str, Any] | None | object = _UNSET,
    accepted_at_attempt: int | None = 0,
    attempts_total: int = 1,
    slice_status: str = "accepted",
    infrastructure_failure_suspected: bool = False,
    review_trends: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "slice": slice_number,
        "slice_status": slice_status,
        "infrastructure_failure_suspected": infrastructure_failure_suspected,
        "final_attempt": _final_attempt() if final_attempt is _UNSET else final_attempt,
        "accepted_at_attempt": accepted_at_attempt,
        "attempts_total": attempts_total,
        "review_trends": review_trends if review_trends is not None else {},
    }


def _report(
    run_id: str,
    *,
    model: str = "opencode/some-model",
    pm_status: str = "complete",
    slices: list[dict[str, Any]] | None = None,
    rating_available: bool = False,
    rating_text: str | None = None,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "model": model,
        "run_status": {"pm_status": pm_status, "stop_reason": "done"},
        "slices": slices if slices is not None else [_slice(1)],
        "pm_subjective_rating": {"available": rating_available, "ref": None, "text": rating_text},
    }


def _write_report(runs_root: Path, run_id: str, report: dict[str, Any]) -> Path:
    run_dir = runs_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "model-report.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    return path


class TestLoadLeaderboardPolicy:
    def test_missing_leaderboard_section_is_a_named_error(self, tmp_path: Path) -> None:
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text(yaml.safe_dump({"backend": "local"}), encoding="utf-8")
        with pytest.raises(lb.LeaderboardError, match="leaderboard"):
            lb.load_leaderboard_policy(policy_path)

    def test_weights_not_summing_to_one_is_a_named_error(self, tmp_path: Path) -> None:
        policy_path = tmp_path / "policy.yaml"
        bad_weights = {"correctness": 0.5, "quality": 0.25, "scope": 0.15, "iterations": 0.20}
        policy_path.write_text(
            yaml.safe_dump({"leaderboard": {"weights": bad_weights, "scope_violation_penalty": 0.2, "iteration_reference_attempts": 3}}),
            encoding="utf-8",
        )
        with pytest.raises(lb.LeaderboardError, match="must sum to 1.0"):
            lb.load_leaderboard_policy(policy_path)

    def test_missing_weight_subkey_is_a_named_error(self, tmp_path: Path) -> None:
        policy_path = tmp_path / "policy.yaml"
        incomplete_weights = {"correctness": 0.5, "quality": 0.25, "scope": 0.25}
        policy_path.write_text(
            yaml.safe_dump({"leaderboard": {"weights": incomplete_weights, "scope_violation_penalty": 0.2, "iteration_reference_attempts": 3}}),
            encoding="utf-8",
        )
        with pytest.raises(lb.LeaderboardError, match="iterations"):
            lb.load_leaderboard_policy(policy_path)

    def test_missing_scope_violation_penalty_is_a_named_error(self, tmp_path: Path) -> None:
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text(
            yaml.safe_dump({"leaderboard": {"weights": dict(_DEFAULT_WEIGHTS), "iteration_reference_attempts": 3}}),
            encoding="utf-8",
        )
        with pytest.raises(lb.LeaderboardError, match="scope_violation_penalty"):
            lb.load_leaderboard_policy(policy_path)

    def test_valid_policy_loads(self, tmp_path: Path) -> None:
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text(
            yaml.safe_dump(
                {"leaderboard": {"weights": dict(_DEFAULT_WEIGHTS), "scope_violation_penalty": 0.2, "iteration_reference_attempts": 3}}
            ),
            encoding="utf-8",
        )
        leaderboard_policy = lb.load_leaderboard_policy(policy_path)
        assert leaderboard_policy["weights"] == _DEFAULT_WEIGHTS

    def test_nan_weight_is_a_named_error_not_a_silent_pass(self, tmp_path: Path) -> None:
        # A YAML `.nan` weight makes the naive weight_sum a NaN, and NaN
        # comparisons are always False -- `abs(nan - 1.0) > tolerance` would
        # otherwise silently evaluate False and let it through.
        policy_path = tmp_path / "policy.yaml"
        bad_weights = {"correctness": float("nan"), "quality": 0.25, "scope": 0.15, "iterations": 0.10}
        policy_path.write_text(
            yaml.safe_dump({"leaderboard": {"weights": bad_weights, "scope_violation_penalty": 0.2, "iteration_reference_attempts": 3}}),
            encoding="utf-8",
        )
        with pytest.raises(lb.LeaderboardError, match="finite, non-negative"):
            lb.load_leaderboard_policy(policy_path)

    def test_negative_weight_is_a_named_error(self, tmp_path: Path) -> None:
        policy_path = tmp_path / "policy.yaml"
        bad_weights = {"correctness": -0.5, "quality": 0.65, "scope": 0.75, "iterations": 0.10}
        policy_path.write_text(
            yaml.safe_dump({"leaderboard": {"weights": bad_weights, "scope_violation_penalty": 0.2, "iteration_reference_attempts": 3}}),
            encoding="utf-8",
        )
        with pytest.raises(lb.LeaderboardError, match="finite, non-negative"):
            lb.load_leaderboard_policy(policy_path)

    def test_boolean_iteration_reference_attempts_is_a_named_error(self, tmp_path: Path) -> None:
        # bool subclasses int in Python -- `True` must not silently become
        # reference value 1 by passing an `isinstance(x, (int, float))` check.
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text(
            yaml.safe_dump(
                {"leaderboard": {"weights": dict(_DEFAULT_WEIGHTS), "scope_violation_penalty": 0.2, "iteration_reference_attempts": True}}
            ),
            encoding="utf-8",
        )
        with pytest.raises(lb.LeaderboardError, match="finite, non-negative"):
            lb.load_leaderboard_policy(policy_path)

    def test_non_positive_iteration_reference_attempts_is_a_named_error(self, tmp_path: Path) -> None:
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text(
            yaml.safe_dump(
                {"leaderboard": {"weights": dict(_DEFAULT_WEIGHTS), "scope_violation_penalty": 0.2, "iteration_reference_attempts": 0}}
            ),
            encoding="utf-8",
        )
        with pytest.raises(lb.LeaderboardError, match="must be positive"):
            lb.load_leaderboard_policy(policy_path)


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

    def test_finds_every_report(self, tmp_path: Path) -> None:
        _write_report(tmp_path, "run-1", _report("run-1"))
        _write_report(tmp_path, "run-2", _report("run-2", model="other/model"))
        found = lb.discover_reports(tmp_path)
        assert len(found) == 2


class TestAggregateModel:
    def test_correctness_is_obligation_mean_not_raw_test_count(self) -> None:
        # An asymmetric partition: one group of 1 test, one of 19 tests --
        # the mean must weight the groups equally (0.5), never the raw
        # pass fraction (10/20 = 0.5 would coincidentally match here, so
        # deliberately make raw and group-mean counts disagree).
        by_obligation = {
            "small_group": {"passed": 0, "total": 1, "fraction": 0.0},
            "large_group": {"passed": 18, "total": 19, "fraction": 18 / 19},
        }
        raw_fraction = 18 / 20  # what a naive hidden_tests_passed/total would give
        group_mean = (0.0 + 18 / 19) / 2
        assert abs(raw_fraction - group_mean) > 0.05  # sanity: the two really disagree
        report = _report("run-1", slices=[_slice(1, final_attempt=_final_attempt(by_obligation=by_obligation))])
        entry, problems = lb.aggregate_model("m", [(Path("x"), report)], _policy())
        assert entry["sub_scores"]["correctness"] == pytest.approx(group_mean)
        assert problems == []

    def test_no_final_attempt_excludes_correctness_and_is_named(self) -> None:
        report = _report("run-1", slices=[_slice(1, final_attempt=None, accepted_at_attempt=None)])
        entry, problems = lb.aggregate_model("m", [(Path("x"), report)], _policy())
        assert entry["sub_scores"]["correctness"] is None
        assert any("no final attempt to grade correctness from" in p for p in problems)

    def test_unavailable_quality_tool_is_excluded_not_zeroed(self) -> None:
        final = _final_attempt(lint=_quality_tool(available=False), health=_quality_tool(available=True, verdict="pass"))
        report = _report("run-1", slices=[_slice(1, final_attempt=final)])
        entry, problems = lb.aggregate_model("m", [(Path("x"), report)], _policy())
        # Only the available tool (pass -> 1.0) contributes; the unavailable
        # one must not be scored as a 0.0, which would instead give 0.5.
        assert entry["sub_scores"]["quality"] == pytest.approx(1.0)
        assert any("lint_findings_by_tool unavailable" in p for p in problems)

    def test_both_quality_tools_unavailable_excludes_quality_entirely(self) -> None:
        final = _final_attempt(lint=_quality_tool(available=False), health=_quality_tool(available=False))
        report = _report("run-1", slices=[_slice(1, final_attempt=final)])
        entry, _problems = lb.aggregate_model("m", [(Path("x"), report)], _policy())
        assert entry["sub_scores"]["quality"] is None

    def test_scope_penalizes_per_violation_and_floors_at_zero(self) -> None:
        final = _final_attempt(violations=["v1", "v2", "v3", "v4", "v5", "v6"])
        report = _report("run-1", slices=[_slice(1, final_attempt=final)])
        entry, _problems = lb.aggregate_model("m", [(Path("x"), report)], _policy(scope_violation_penalty=0.2))
        assert entry["sub_scores"]["scope"] == pytest.approx(0.0)  # 1 - 6*0.2 = -0.2, floored

    def test_unaccepted_slice_excluded_from_iterations_and_counted_separately(self) -> None:
        report = _report(
            "run-1",
            slices=[
                _slice(1, accepted_at_attempt=None, attempts_total=3),
                _slice(2, accepted_at_attempt=1, attempts_total=2),
            ],
        )
        entry, problems = lb.aggregate_model("m", [(Path("x"), report)], _policy(iteration_reference_attempts=3))
        # Only slice 2 contributes: 3 / max(2, 3) = 1.0.
        assert entry["sub_scores"]["iterations"] == pytest.approx(1.0)
        assert entry["unaccepted_slices"] == 1
        assert not any("iterations" in p and "unaccepted" not in p for p in problems)

    def test_accepted_slice_missing_attempts_total_is_a_named_error(self) -> None:
        # A corrupted/hand-edited report claiming acceptance with no
        # attempts_total must raise a named LeaderboardError, not an
        # unhandled TypeError from max(None, ...).
        broken_slice = _slice(1, accepted_at_attempt=0)
        del broken_slice["attempts_total"]
        report = _report("run-1", slices=[broken_slice])
        with pytest.raises(lb.LeaderboardError, match="attempts_total"):
            lb.aggregate_model("m", [(Path("x"), report)], _policy())

    def test_iterations_scales_down_smoothly_past_the_reference(self) -> None:
        report = _report("run-1", slices=[_slice(1, accepted_at_attempt=5, attempts_total=6)])
        entry, _problems = lb.aggregate_model("m", [(Path("x"), report)], _policy(iteration_reference_attempts=3))
        assert entry["sub_scores"]["iterations"] == pytest.approx(3 / 6)

    def test_composite_renormalizes_over_available_weights_when_a_subscore_is_missing(self) -> None:
        # Quality entirely unavailable -> composite renormalizes over the
        # remaining correctness/scope/iterations weights (0.5+0.15+0.10=0.75).
        final = _final_attempt(lint=_quality_tool(available=False), health=_quality_tool(available=False))
        report = _report("run-1", slices=[_slice(1, final_attempt=final, accepted_at_attempt=0, attempts_total=1)])
        policy = _policy(iteration_reference_attempts=3)
        entry, problems = lb.aggregate_model("m", [(Path("x"), report)], policy)
        assert entry["sub_scores"]["quality"] is None
        correctness = entry["sub_scores"]["correctness"]
        scope = entry["sub_scores"]["scope"]
        iterations = entry["sub_scores"]["iterations"]
        remaining_weight = 0.5 + 0.15 + 0.10
        expected = (0.5 * correctness + 0.15 * scope + 0.10 * iterations) / remaining_weight
        assert entry["composite_score"] == pytest.approx(expected)
        assert any("no gradeable data for quality" in p for p in problems)

    def test_composite_is_none_when_no_subscore_has_any_data(self) -> None:
        report = _report("run-1", slices=[_slice(1, final_attempt=None, accepted_at_attempt=None)])
        entry, problems = lb.aggregate_model("m", [(Path("x"), report)], _policy())
        assert entry["composite_score"] is None
        # One "no gradeable data for" per sub-score, plus the one
        # slice-level "no final attempt" problem correctness names directly.
        assert sum("no gradeable data for" in p for p in problems) == 4
        assert sum("no final attempt to grade correctness from" in p for p in problems) == 1
        assert len(problems) == 5

    def test_composite_is_none_when_available_subscores_carry_zero_weight(self) -> None:
        # A policy that legitimately sums to 1.0 but assigns zero weight to
        # every sub-score this model actually has data for (iterations is
        # excluded outright since the slice was never accepted) must not
        # raise ZeroDivisionError -- it's an undefined composite, named as a
        # problem, same as "no data at all".
        policy = _policy(weights={"correctness": 0.0, "quality": 0.0, "scope": 0.0, "iterations": 1.0})
        report = _report("run-1", slices=[_slice(1, accepted_at_attempt=None)])
        entry, problems = lb.aggregate_model("m", [(Path("x"), report)], policy)
        assert entry["composite_score"] is None
        assert entry["sub_scores"]["iterations"] is None
        assert any("zero total weight" in p for p in problems)

    def test_duplicate_run_id_across_reports_is_a_named_error(self, tmp_path: Path) -> None:
        runs_root = tmp_path / "runs"
        _write_report(runs_root, "run-dupe", _report("run-dupe"))
        # A second, differently-named run directory whose report still
        # claims run_id "run-dupe" -- must not silently collapse into one
        # entry (and undercount run_count) in aggregate_model's grouping.
        _write_report(runs_root, "run-dupe-2", _report("run-dupe"))
        with pytest.raises(lb.LeaderboardError, match="run-dupe"):
            lb.discover_reports(runs_root)

    def test_run_metadata_recorded_per_model(self) -> None:
        r1 = _report("run-1", pm_status="complete", rating_available=True, rating_text="great")
        r2 = _report("run-2", pm_status="stopped")
        entry, _problems = lb.aggregate_model("m", [(Path("a"), r1), (Path("b"), r2)], _policy())
        assert entry["run_count"] == 2
        assert entry["run_ids"] == ["run-1", "run-2"]
        assert entry["pm_status_counts"] == {"complete": 1, "stopped": 1}
        assert entry["pm_subjective_ratings"] == [
            {"run_id": "run-1", "available": True, "ref": None, "text": "great"},
            {"run_id": "run-2", "available": False, "ref": None, "text": None},
        ]

    def test_sub_scores_flatten_slice_records_across_every_run_not_just_one(self) -> None:
        # Unequal slice counts per run (two in run-1, one in run-2) so that
        # per-slice-record averaging (the documented rule) and per-run
        # averaging (a plausible but wrong alternative) disagree: per-run
        # would average [1.0, 1.0] and [0.0] to 0.5; the correct flattened
        # mean over all three slice-records is 2/3.
        run_1 = _report(
            "run-1",
            slices=[
                _slice(1, final_attempt=_final_attempt(by_obligation={"g": {"fraction": 1.0}})),
                _slice(2, final_attempt=_final_attempt(by_obligation={"g": {"fraction": 1.0}})),
            ],
        )
        run_2 = _report("run-2", slices=[_slice(1, final_attempt=_final_attempt(by_obligation={"g": {"fraction": 0.0}}))])
        entry, _problems = lb.aggregate_model("m", [(Path("a"), run_1), (Path("b"), run_2)], _policy())
        assert entry["run_count"] == 2
        assert entry["sub_scores"]["correctness"] == pytest.approx(2 / 3)

    def test_report_level_problems_are_propagated_with_run_context(self) -> None:
        # Tool 4 names its own problems (e.g. a vanished rating file) in the
        # report's own `problems` list -- dropping them here would make that
        # indistinguishable from "never recorded" (AGENTS.md: never silently
        # discard another tool's named problem).
        report = _report("run-1")
        report["problems"] = ["pm_model_performance_ref foo.md is recorded but no longer exists on disk"]
        entry, problems = lb.aggregate_model("m", [(Path("a"), report)], _policy())
        assert any("run-1: pm_model_performance_ref foo.md is recorded but no longer exists" in p for p in problems)


class TestBuildLeaderboard:
    def test_one_model_one_run(self, tmp_path: Path) -> None:
        _write_report(tmp_path, "run-1", _report("run-1"))
        reports = lb.discover_reports(tmp_path)
        leaderboard, problems = lb.build_leaderboard(reports, _policy())
        assert [m["model"] for m in leaderboard["models"]] == ["opencode/some-model"]
        assert problems == []

    def test_one_model_multiple_runs_folds_into_one_entry(self, tmp_path: Path) -> None:
        _write_report(tmp_path, "run-1", _report("run-1"))
        _write_report(tmp_path, "run-2", _report("run-2"))
        reports = lb.discover_reports(tmp_path)
        leaderboard, _problems = lb.build_leaderboard(reports, _policy())
        assert len(leaderboard["models"]) == 1
        assert leaderboard["models"][0]["run_count"] == 2

    def test_two_distinct_models_both_appear_ranked_by_composite(self, tmp_path: Path) -> None:
        strong = _final_attempt(by_obligation={"g": {"fraction": 1.0}})
        weak = _final_attempt(by_obligation={"g": {"fraction": 0.1}})
        _write_report(tmp_path, "run-1", _report("run-1", model="strong/model", slices=[_slice(1, final_attempt=strong)]))
        _write_report(tmp_path, "run-2", _report("run-2", model="weak/model", slices=[_slice(1, final_attempt=weak)]))
        reports = lb.discover_reports(tmp_path)
        leaderboard, _problems = lb.build_leaderboard(reports, _policy())
        assert [m["model"] for m in leaderboard["models"]] == ["strong/model", "weak/model"]

    def test_none_composite_scores_sort_last(self, tmp_path: Path) -> None:
        ungraded = _report("run-1", model="ungraded/model", slices=[_slice(1, final_attempt=None, accepted_at_attempt=None)])
        graded = _report("run-2", model="graded/model")
        _write_report(tmp_path, "run-1", ungraded)
        _write_report(tmp_path, "run-2", graded)
        reports = lb.discover_reports(tmp_path)
        leaderboard, _problems = lb.build_leaderboard(reports, _policy())
        assert [m["model"] for m in leaderboard["models"]] == ["graded/model", "ungraded/model"]

    def test_ties_broken_by_model_name_ascending(self, tmp_path: Path) -> None:
        _write_report(tmp_path, "run-1", _report("run-1", model="zeta/model"))
        _write_report(tmp_path, "run-2", _report("run-2", model="alpha/model"))
        reports = lb.discover_reports(tmp_path)
        leaderboard, _problems = lb.build_leaderboard(reports, _policy())
        assert leaderboard["models"][0]["composite_score"] == pytest.approx(leaderboard["models"][1]["composite_score"])
        assert [m["model"] for m in leaderboard["models"]] == ["alpha/model", "zeta/model"]


class TestRenderMarkdown:
    def test_ranking_table_lists_every_model_with_its_sub_scores(self, tmp_path: Path) -> None:
        strong = _final_attempt(by_obligation={"g": {"passed": 4, "total": 4, "fraction": 1.0}})
        _write_report(tmp_path, "run-1", _report("run-1", model="strong/model", slices=[_slice(1, final_attempt=strong)]))
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)

        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert "# Leaderboard" in markdown
        assert "## Ranking" in markdown
        assert "| 1 | `strong/model` | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1 | 1 | 0 |" in markdown

    def test_composite_none_renders_as_dashes_not_a_crash(self, tmp_path: Path) -> None:
        ungraded = _report("run-1", model="ungraded/model", slices=[_slice(1, final_attempt=None, accepted_at_attempt=None)])
        _write_report(tmp_path, "run-1", ungraded)
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)

        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert "| 1 | `ungraded/model` | -- | -- | -- | -- | -- | 1 | 0 | 1 |" in markdown

    def test_slice_section_shows_obligation_table_and_hidden_test_count(self, tmp_path: Path) -> None:
        attempt = _final_attempt(by_obligation={"weighted_fit_core": {"passed": 5, "total": 5, "fraction": 1.0}})
        attempt["correctness"]["hidden_tests_passed"] = 5
        attempt["correctness"]["hidden_tests_total"] = 5
        _write_report(tmp_path, "run-1", _report("run-1", slices=[_slice(1, final_attempt=attempt, attempts_total=2, accepted_at_attempt=1)]))
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)

        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert "#### Slice 1 -- accepted at attempt 1 of 2" in markdown
        assert "Hidden tests: 5/5" in markdown
        assert "| `weighted_fit_core` | 5/5 | 1.000 |" in markdown

    def test_unaccepted_slice_heading_names_its_status_not_an_attempt_number(self, tmp_path: Path) -> None:
        report = _report(
            "run-1",
            slices=[_slice(1, final_attempt=None, accepted_at_attempt=None, attempts_total=4, slice_status="abandoned")],
        )
        _write_report(tmp_path, "run-1", report)
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)

        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert "#### Slice 1 -- abandoned after 4 attempt(s)" in markdown
        assert "_No final attempt graded._" in markdown

    def test_review_trend_table_renders_verdicts_and_a_parse_error_row(self, tmp_path: Path) -> None:
        review_trends = {
            "drift_review": [{"attempt": 1, "parse_error": "malformed finding line"}],
            "code_review": [{"attempt": 1, "verdict": "PASS", "findings_by_severity": {"P0": 0, "P1": 0, "P2": 0, "P3": 0}}],
        }
        _write_report(tmp_path, "run-1", _report("run-1", slices=[_slice(1, review_trends=review_trends)]))
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)

        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert "| 1 | drift_review | parse error: malformed finding line | -- | -- | -- | -- |" in markdown
        assert "| 1 | code_review | PASS | 0 | 0 | 0 | 0 |" in markdown

    def test_pm_subjective_rating_is_quoted_verbatim_and_labeled_never_blended(self, tmp_path: Path) -> None:
        report = _report("run-1", rating_available=True, rating_text="Process discipline: 5/5\nOutput quality: 4/5")
        _write_report(tmp_path, "run-1", report)
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)

        markdown = lb.render_markdown(leaderboard, reports, policy)

        assert "never blended into composite" in markdown
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

    def test_model_problems_are_attributed_only_to_that_model(self, tmp_path: Path) -> None:
        # "foo" is a string-prefix of "foo bar" -- a naive `problems`
        # string-prefix match (rather than entry["problems"], attributed
        # structurally in aggregate_model()) would leak "foo bar"'s own
        # problem into "foo"'s section too, since "model foo bar, ..."
        # starts with "model foo ". Give the problem to "foo bar" so this
        # actually exercises that leak direction, not the reverse.
        _write_report(tmp_path, "run-1", _report("run-1", model="foo"))
        _write_report(tmp_path, "run-2", _report("run-2", model="foo bar", slices=[_slice(1, final_attempt=None, accepted_at_attempt=None)]))
        reports = lb.discover_reports(tmp_path)
        policy = _policy()
        leaderboard, _problems = lb.build_leaderboard(reports, policy)

        markdown = lb.render_markdown(leaderboard, reports, policy)

        # `foo` (graded, composite 1.0) ranks 1st; `foo bar` (ungraded,
        # composite None) ranks 2nd and last -- so its own section runs to
        # the end of the document.
        foo_idx = markdown.index("`foo`", markdown.index("## 1."))
        bar_idx = markdown.index("`foo bar`", markdown.index("## 2."))
        foo_section, bar_section = markdown[foo_idx:bar_idx], markdown[bar_idx:]
        assert "no final attempt to grade correctness from" in bar_section
        assert "no final attempt to grade correctness from" not in foo_section

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

    def test_obligation_table_falls_back_to_question_mark_for_missing_counts(self, tmp_path: Path) -> None:
        attempt = _final_attempt(by_obligation={"g": {"fraction": 0.5}})  # no passed/total keys
        _write_report(tmp_path, "run-1", _report("run-1", slices=[_slice(1, final_attempt=attempt)]))
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

        assert lb._code_span("weird`model|name") in markdown


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

        assert "## All problems" in markdown
        assert "None." in markdown


class TestMain:
    def test_writes_leaderboard_and_returns_0_on_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        root = tmp_path / "bench-root"
        _write_report(root / "results" / "runs", "run-1", _report("run-1"))
        policy_path = root / "policy.yaml"
        policy_path.parent.mkdir(parents=True, exist_ok=True)
        policy_path.write_text(
            yaml.safe_dump(
                {"leaderboard": {"weights": dict(_DEFAULT_WEIGHTS), "scope_violation_penalty": 0.2, "iteration_reference_attempts": 3}}
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(lb, "bench_root", lambda: root)

        exit_code = lb.main([])

        assert exit_code == 0
        out_path = root / "results" / "leaderboard.json"
        assert out_path.is_file()
        written = json.loads(out_path.read_text(encoding="utf-8"))
        assert written["models"][0]["model"] == "opencode/some-model"
        md_path = root / "results" / "leaderboard.md"
        assert md_path.is_file()
        assert "opencode/some-model" in md_path.read_text(encoding="utf-8")

    def test_markdown_out_override_writes_to_the_given_path(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        root = tmp_path / "bench-root"
        _write_report(root / "results" / "runs", "run-1", _report("run-1"))
        policy_path = root / "policy.yaml"
        policy_path.parent.mkdir(parents=True, exist_ok=True)
        policy_path.write_text(
            yaml.safe_dump(
                {"leaderboard": {"weights": dict(_DEFAULT_WEIGHTS), "scope_violation_penalty": 0.2, "iteration_reference_attempts": 3}}
            ),
            encoding="utf-8",
        )
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
        policy_path.write_text(
            yaml.safe_dump(
                {"leaderboard": {"weights": dict(_DEFAULT_WEIGHTS), "scope_violation_penalty": 0.2, "iteration_reference_attempts": 3}}
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(lb, "bench_root", lambda: root)
        monkeypatch.setattr(lb, "render_markdown", lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("boom")))

        with pytest.raises(RuntimeError, match="boom"):
            lb.main([])

        assert not (root / "results" / "leaderboard.json").exists()
        assert not (root / "results" / "leaderboard.md").exists()

    def test_returns_1_when_problems_are_reported(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        root = tmp_path / "bench-root"
        report = _report("run-1", slices=[_slice(1, final_attempt=None, accepted_at_attempt=None)])
        _write_report(root / "results" / "runs", "run-1", report)
        policy_path = root / "policy.yaml"
        policy_path.parent.mkdir(parents=True, exist_ok=True)
        policy_path.write_text(
            yaml.safe_dump(
                {"leaderboard": {"weights": dict(_DEFAULT_WEIGHTS), "scope_violation_penalty": 0.2, "iteration_reference_attempts": 3}}
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(lb, "bench_root", lambda: root)

        assert lb.main([]) == 1
