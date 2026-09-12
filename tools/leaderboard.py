#!/usr/bin/env python3
"""Tool 5: the cross-model leaderboard, folded from every Tool 4 report on
disk (docs/MODE2-REWRITE-PLAN.md §6, "Tool 5").

Reads every `model-report.json` under `results/runs/*/` (Tool 4's own
output), groups them by model (a model can have several runs -- see
policy.yaml's `repeats`), and reduces each model's flattened slice-records
into four deterministic sub-scores -- correctness, quality, scope,
iterations -- then a single weighted composite driven by `policy.yaml`'s
`leaderboard` section. This module invents no new *measurement*: every
sub-score is a direct, documented reduction of fields `dev_check.py`/
`review_score.py` already computed and Tool 4 already reshaped; only the
weighting is new, and every weight lives in policy.yaml (AGENTS.md: "every
path, threshold and tunable lives in policy.yaml").

PM's own subjective rating is carried through per run, verbatim, in its own
`pm_subjective_ratings` list -- never blended into `composite_score` (same
separation this repo's design applies everywhere: deterministic scores are
comparable across runs, PM's judgement is a within-run call, and averaging
the two would destroy that distinction silently).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import yaml

import bench_lib

# The four sub-scores this tool computes, and the exact policy.yaml weight
# keys that drive their composite blend -- one name used throughout so a
# missing/None sub-score and its matching weight are always found the same
# way (see aggregate_model's renormalization).
_SUB_SCORES = ("correctness", "quality", "scope", "iterations")

# Tool 4's own two quality-tool fields on an attempt's `quality` block
# (dev_check.py's run_lint/run_code_health, reshaped verbatim by
# model_report.py) -- reused by name here rather than imported, same as
# model_report.py's own _REVIEW_TREND_FIELDS convention.
_QUALITY_FIELDS = ("lint_findings_by_tool", "code_health_findings_by_category")

_REQUIRED_REPORT_KEYS = ("run_id", "model", "run_status", "slices", "pm_subjective_rating")

_WEIGHT_SUM_TOLERANCE = 1e-6


class LeaderboardError(bench_lib.BenchLibError):
    """Raised for every condition this tool must fail loudly on.

    main() catches exactly this exception type, prints it, and exits 1 --
    matching model_report.py's/dev_check.py's own __main__ pattern.
    """


def bench_root() -> Path:
    """Absolute path to this repo's root -- see bench_lib.repo_root()."""
    try:
        return bench_lib.repo_root()
    except bench_lib.BenchLibError as exc:
        raise LeaderboardError(str(exc)) from exc


# --- policy --------------------------------------------------------------


def load_leaderboard_policy(policy_path: Path) -> dict[str, Any]:
    """Load policy.yaml and validate the `leaderboard` section this tool
    needs: `weights` (all four of `_SUB_SCORES`, summing to 1.0),
    `scope_violation_penalty`, `iteration_reference_attempts`.

    No fallback default is ever hardcoded here (AGENTS.md: "do not invent
    scoring weights outside [policy.yaml]") -- every one of these being
    absent is a named LeaderboardError, never a silent default.
    """
    if not policy_path.is_file():
        raise LeaderboardError(f"policy file not found: {policy_path}")
    with policy_path.open("r", encoding="utf-8") as handle:
        policy = yaml.safe_load(handle)
    if not isinstance(policy, dict):
        raise LeaderboardError(f"policy file {policy_path} did not parse to a mapping")

    leaderboard = policy.get("leaderboard")
    if not isinstance(leaderboard, dict):
        raise LeaderboardError(f"policy file {policy_path} is missing its required 'leaderboard' section")

    weights = leaderboard.get("weights")
    if not isinstance(weights, dict):
        raise LeaderboardError(f"policy file {policy_path}'s leaderboard section is missing 'weights'")
    missing_weights = [key for key in _SUB_SCORES if key not in weights]
    if missing_weights:
        raise LeaderboardError(
            f"policy file {policy_path}'s leaderboard.weights is missing: {', '.join(missing_weights)}"
        )
    for key in _SUB_SCORES:
        _require_finite_nonnegative(weights[key], f"leaderboard.weights.{key}", policy_path)
    weight_sum = sum(weights[key] for key in _SUB_SCORES)
    if abs(weight_sum - 1.0) > _WEIGHT_SUM_TOLERANCE:
        raise LeaderboardError(
            f"policy file {policy_path}'s leaderboard.weights must sum to 1.0, got {weight_sum}"
        )

    for key in ("scope_violation_penalty", "iteration_reference_attempts"):
        if leaderboard.get(key) is None:
            raise LeaderboardError(f"policy file {policy_path}'s leaderboard section is missing '{key}'")
    _require_finite_nonnegative(
        leaderboard["scope_violation_penalty"], "leaderboard.scope_violation_penalty", policy_path
    )
    _require_finite_nonnegative(
        leaderboard["iteration_reference_attempts"], "leaderboard.iteration_reference_attempts", policy_path
    )
    if leaderboard["iteration_reference_attempts"] <= 0:
        raise LeaderboardError(
            f"policy file {policy_path}'s leaderboard.iteration_reference_attempts must be positive, "
            f"got {leaderboard['iteration_reference_attempts']!r}"
        )

    return leaderboard


def _require_finite_nonnegative(value: Any, field_name: str, policy_path: Path) -> None:
    """A weight/penalty value must be a finite, non-negative number -- guards
    against a policy typo (a negative weight, or YAML's `.nan`/`.inf`
    literals) silently propagating into `composite_score` instead of being
    named here. A NaN weight is the sharpest case: `sum()` over it produces
    NaN, and NaN's comparisons are always False, so the weights-sum-to-1.0
    check below would otherwise silently pass instead of catching it.
    """
    is_number = isinstance(value, (int, float)) and not isinstance(value, bool)
    if not is_number or (isinstance(value, float) and not math.isfinite(value)) or value < 0:
        raise LeaderboardError(f"policy file {policy_path}'s {field_name} must be a finite, non-negative number, got {value!r}")


# --- discovery -------------------------------------------------------------


def default_runs_root(root: Path) -> Path:
    """Where model_report.py writes every run's report -- see its own
    default_sheets_dir, which likewise hardcodes `results/runs/` rather
    than reading it from policy.yaml (this tool has no path tunable of its
    own, matching that choice)."""
    return root / "results" / "runs"


def default_out_path(root: Path) -> Path:
    return root / "results" / "leaderboard.json"


def read_json(path: Path) -> Any:
    """Read and parse one JSON file, failing loudly with the path on error."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise LeaderboardError(f"required file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise LeaderboardError(f"invalid JSON in {path}: {exc}") from exc


def discover_reports(runs_root: Path) -> list[tuple[Path, dict[str, Any]]]:
    """Every `model-report.json` found under `runs_root` (mirrors Tool 4's
    own `results/runs/<run_id>/` convention), sorted by path for determinism.

    Raises:
        LeaderboardError: no report found anywhere; one found fails to parse
            or is missing a required top-level key; or two reports carry the
            same `run_id` (a run directory is supposed to be unique -- two
            reports sharing one would otherwise silently collapse into a
            single entry downstream, in aggregate_model's per-run grouping,
            exactly the duplicate-identity corruption model_report.py's own
            discover_sheets already guards against for slice numbers).
    """
    found_paths = sorted(runs_root.glob("*/model-report.json"))
    if not found_paths:
        raise LeaderboardError(
            f"no model-report.json files found under {runs_root} -- run tools/model_report.py first"
        )
    reports = []
    seen_run_ids: dict[str, Path] = {}
    for path in found_paths:
        report = read_json(path)
        if not isinstance(report, dict):
            raise LeaderboardError(f"model-report.json at {path} did not parse to a mapping")
        missing = [key for key in _REQUIRED_REPORT_KEYS if key not in report]
        if missing:
            raise LeaderboardError(f"model-report.json at {path} is missing required key(s): {', '.join(missing)}")
        run_id = report["run_id"]
        if run_id in seen_run_ids:
            raise LeaderboardError(
                f"two model-report.json files carry the same run_id {run_id!r}: {seen_run_ids[run_id]} and {path}"
            )
        seen_run_ids[run_id] = path
        reports.append((path, report))
    return reports


def group_reports_by_model(reports: list[tuple[Path, dict[str, Any]]]) -> dict[str, list[tuple[Path, dict[str, Any]]]]:
    """Every discovered report, grouped by its own `model` field -- a model
    can have several runs on disk (policy.yaml's `repeats`)."""
    groups: dict[str, list[tuple[Path, dict[str, Any]]]] = {}
    for path, report in reports:
        groups.setdefault(report["model"], []).append((path, report))
    return groups


# --- per-slice-record sub-scores -------------------------------------------


def _slice_correctness(model: str, run_id: str, slice_entry: dict[str, Any], problems: list[str]) -> float | None:
    """Equally-weighted mean of each obligation group's own `fraction` --
    never `hidden_tests_passed/hidden_tests_total` directly, which is an
    unweighted raw test count (AGENTS.md: the obligation partition *is* the
    rubric weight, so summing raw pass/fail counts would double-count a
    large group).

    Returns None (excluded from the model's mean, not scored as 0) when
    there is no final attempt, or it has no `by_obligation` data -- named in
    `problems` either way.
    """
    slice_number = slice_entry.get("slice")
    final_attempt = slice_entry.get("final_attempt")
    by_obligation = (final_attempt.get("correctness") or {}).get("by_obligation") if final_attempt else None
    if not by_obligation:
        problems.append(f"model {model}, run {run_id}, slice {slice_number}: no final attempt to grade correctness from")
        return None
    try:
        fractions = [group["fraction"] for group in by_obligation.values()]
    except (KeyError, TypeError) as exc:
        raise LeaderboardError(
            f"malformed by_obligation for model {model}, run {run_id}, slice {slice_number}: {exc}"
        ) from exc
    return sum(fractions) / len(fractions)


def _slice_quality(model: str, run_id: str, slice_entry: dict[str, Any], problems: list[str]) -> float | None:
    """Mean of whichever of the two quality tools were `available` on the
    final attempt, each contributing 1.0 for a `pass` verdict else 0.0.

    An unavailable tool (or a missing tool dict) is excluded from the mean
    entirely, never scored as a pass (AGENTS.md: "An unavailable linter is
    recorded as unavailable, never as a clean pass"), and named in
    `problems`. Returns None (excluded from the model's mean) if neither
    tool was available, or there is no final attempt at all -- the latter
    is not separately reported here since _slice_correctness already names
    the missing final attempt once per slice-record.
    """
    slice_number = slice_entry.get("slice")
    final_attempt = slice_entry.get("final_attempt")
    if not final_attempt:
        return None
    quality = final_attempt.get("quality") or {}
    sub_scores = []
    for field in _QUALITY_FIELDS:
        tool = quality.get(field)
        if not tool or not tool.get("available"):
            problems.append(f"model {model}, run {run_id}, slice {slice_number}: quality tool {field} unavailable")
            continue
        sub_scores.append(1.0 if tool.get("verdict") == "pass" else 0.0)
    if not sub_scores:
        return None
    return sum(sub_scores) / len(sub_scores)


def _slice_scope(slice_entry: dict[str, Any], scope_violation_penalty: float) -> float | None:
    """1.0 with no violations, else penalized per violation (floored at
    0.0). Always defined when a final attempt exists -- an empty/missing
    `scope` dict just means zero violations, so no `problems` entry is
    needed here (unlike correctness/quality, which name an unavailable
    input)."""
    final_attempt = slice_entry.get("final_attempt")
    if not final_attempt:
        return None
    violations = (final_attempt.get("scope") or {}).get("violations") or []
    if not violations:
        return 1.0
    return max(0.0, 1.0 - len(violations) * scope_violation_penalty)


def _slice_iterations(
    model: str, run_id: str, slice_entry: dict[str, Any], iteration_reference_attempts: float
) -> float | None:
    """Defined only when the slice was actually accepted -- an unaccepted/
    abandoned slice has no meaningful "attempts to accept" (its own count is
    tracked separately, as `unaccepted_slices`, not scored here).

    Capped at 1.0, scaling down smoothly for more attempts than the
    reference (policy.yaml's `iteration_reference_attempts`).

    Raises:
        LeaderboardError: the slice is accepted but its report carries no
            `attempts_total` -- Tool 4 always writes one via
            resolve_attempts_total(), so this only fires against a
            corrupted/hand-edited report, but the alternative is an
            unnamed TypeError from `max(None, ...)`.
    """
    if slice_entry.get("accepted_at_attempt") is None:
        return None
    attempts_total = slice_entry.get("attempts_total")
    if not isinstance(attempts_total, (int, float)):
        slice_number = slice_entry.get("slice")
        raise LeaderboardError(
            f"model {model}, run {run_id}, slice {slice_number}: accepted but attempts_total is "
            f"missing or not numeric ({attempts_total!r})"
        )
    return iteration_reference_attempts / max(attempts_total, iteration_reference_attempts)


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


# --- per-model aggregation ---------------------------------------------


def aggregate_model(
    model: str, model_reports: list[tuple[Path, dict[str, Any]]], leaderboard_policy: dict[str, Any]
) -> tuple[dict[str, Any], list[str]]:
    """Flatten every graded slice from every run of `model` into one list of
    slice-records, score each of the four sub-scores per record, then mean
    each sub-score across every record where it was defined -- equal weight
    per slice-record, no per-run or per-slice-number weighting.
    """
    problems: list[str] = []
    correctness_values: list[float] = []
    quality_values: list[float] = []
    scope_values: list[float] = []
    iteration_values: list[float] = []
    unaccepted_slices = 0
    slices_graded = 0
    pm_status_counts: dict[str, int] = {}
    pm_subjective_ratings: list[dict[str, Any]] = []

    reports_by_run_id = {report["run_id"]: report for _path, report in model_reports}
    run_ids = sorted(reports_by_run_id)

    scope_penalty = leaderboard_policy["scope_violation_penalty"]
    iteration_reference = leaderboard_policy["iteration_reference_attempts"]

    for run_id in run_ids:
        report = reports_by_run_id[run_id]
        pm_status = (report.get("run_status") or {}).get("pm_status")
        pm_status_counts[pm_status] = pm_status_counts.get(pm_status, 0) + 1
        rating = report.get("pm_subjective_rating") or {}
        pm_subjective_ratings.append(
            {
                "run_id": run_id,
                "available": bool(rating.get("available")),
                "ref": rating.get("ref"),
                "text": rating.get("text"),
            }
        )
        # Tool 4's own named problems (e.g. a pm_model_performance_ref that
        # vanished from disk) are this run's evidence too -- dropping them
        # here would make that case indistinguishable from a rating that was
        # simply never recorded (AGENTS.md: never silently discard).
        for report_problem in report.get("problems") or []:
            problems.append(f"model {model}, run {run_id}: {report_problem}")

        for slice_entry in report.get("slices") or []:
            if slice_entry.get("final_attempt"):
                slices_graded += 1

            correctness = _slice_correctness(model, run_id, slice_entry, problems)
            if correctness is not None:
                correctness_values.append(correctness)

            quality = _slice_quality(model, run_id, slice_entry, problems)
            if quality is not None:
                quality_values.append(quality)

            scope = _slice_scope(slice_entry, scope_penalty)
            if scope is not None:
                scope_values.append(scope)

            if slice_entry.get("accepted_at_attempt") is None:
                unaccepted_slices += 1
            else:
                iterations = _slice_iterations(model, run_id, slice_entry, iteration_reference)
                if iterations is not None:
                    iteration_values.append(iterations)

    sub_score_means = {
        "correctness": _mean(correctness_values),
        "quality": _mean(quality_values),
        "scope": _mean(scope_values),
        "iterations": _mean(iteration_values),
    }
    missing_sub_scores = [key for key in _SUB_SCORES if sub_score_means[key] is None]
    for key in missing_sub_scores:
        problems.append(f"model {model} has no gradeable data for {key}; excluded from its composite")

    weights = leaderboard_policy["weights"]
    available = {key: value for key, value in sub_score_means.items() if value is not None}
    weight_sum = sum(weights[key] for key in available) if available else 0.0
    if not available or weight_sum == 0.0:
        composite_score = None
        if available:
            problems.append(
                f"model {model}: composite undefined -- available sub-scores "
                f"({', '.join(sorted(available))}) carry zero total weight in policy.yaml"
            )
    else:
        composite_score = sum(weights[key] * available[key] for key in available) / weight_sum

    entry = {
        "model": model,
        "composite_score": composite_score,
        "sub_scores": sub_score_means,
        "run_count": len(run_ids),
        "run_ids": run_ids,
        "pm_status_counts": pm_status_counts,
        "slices_graded": slices_graded,
        "unaccepted_slices": unaccepted_slices,
        "pm_subjective_ratings": pm_subjective_ratings,
    }
    return entry, problems


def build_leaderboard(
    reports: list[tuple[Path, dict[str, Any]]], leaderboard_policy: dict[str, Any]
) -> tuple[dict[str, Any], list[str]]:
    """Assemble the full cross-model leaderboard from every discovered report.

    Sorted by `composite_score` descending, `None` scores sorted last, ties
    broken by `model` name ascending for determinism.
    """
    problems: list[str] = []
    models = []
    for model, model_reports in group_reports_by_model(reports).items():
        entry, model_problems = aggregate_model(model, model_reports, leaderboard_policy)
        models.append(entry)
        problems.extend(model_problems)

    models.sort(key=lambda m: (m["composite_score"] is None, -(m["composite_score"] or 0.0), m["model"]))
    leaderboard = {"models": models, "problems": problems}
    return leaderboard, problems


# --- CLI -----------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Rebuild the cross-model leaderboard from every model-report.json on disk, weighted by "
            "policy.yaml's 'leaderboard' section (docs/MODE2-REWRITE-PLAN.md §6, Tool 5). PM-run data only."
        )
    )
    parser.add_argument("--out", type=Path, default=None, help="defaults to results/leaderboard.json")
    parser.add_argument(
        "--results-dir", type=Path, default=None, help="defaults to results/runs; glob root for */model-report.json"
    )
    parser.add_argument("--policy", type=Path, default=None, help="defaults to policy.yaml at this repo's root")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = bench_root()
    policy_path = (args.policy or (root / "policy.yaml")).expanduser().resolve()
    leaderboard_policy = load_leaderboard_policy(policy_path)

    runs_root = (args.results_dir or default_runs_root(root)).expanduser().resolve()
    out_path = (args.out or default_out_path(root)).expanduser().resolve()

    reports = discover_reports(runs_root)
    leaderboard, problems = build_leaderboard(reports, leaderboard_policy)
    bench_lib.write_json_atomically(out_path, leaderboard)
    print(f"wrote {out_path} ({len(leaderboard['models'])} model(s) from {len(reports)} report(s))")
    return bench_lib.report_problems("leaderboard.py", problems)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except LeaderboardError as exc:
        print(f"leaderboard.py: error: {exc}", file=sys.stderr)
        sys.exit(1)
