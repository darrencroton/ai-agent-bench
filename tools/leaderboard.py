#!/usr/bin/env python3
"""Tool 5: the cross-model leaderboard, folded from every Tool 4 report on
disk (docs/MODE2-REWRITE-PLAN.md §6, "Tool 5"; ranking basis rebuilt per
docs/LEADERBOARD-REBUILD-PLAN.md Stage 2).

Reads every `model-report.json` under `results/runs/*/` (Tool 4's own
output), groups them by Developer configuration (`developer.configuration_key`
-- a configuration can have several runs on disk; see policy.yaml's
`repeats`), and ranks configurations by **mean first-attempt correctness**:
the equally-weighted mean of a slice's obligation-group `fraction`s on its
FIRST (ordinal-0) attempt, averaged equally across a run's two slices, then
averaged equally across a configuration's *eligible* runs (Stage 1's
`run_coverage`/`eligible_for_first_submission`).

Stage 2 (docs/LEADERBOARD-REBUILD-PLAN.md) deletes the old four-term
weighted composite (`_slice_quality`/`_slice_scope`/`_slice_iterations`,
`policy.yaml`'s `leaderboard.weights`/`scope_violation_penalty`/
`iteration_reference_attempts`) entirely -- it is not replaced by another
blended number. Correctness is the only thing this tool ranks on; ΔLOC/ΔCC
(Stage 3) and PM's own judgments (Stage 4) are supporting columns, never
folded into a score. Every remaining number here is a direct, documented
reduction of fields `dev_check.py`/`review_score.py`/`model_report.py`
already computed; the only new arithmetic Stage 2 adds is the mean/min/max/n
spread convention used throughout (`_spread`) and paired-run improvement
(`aggregate_model`'s `gain_pp`, computed per run before being summarised --
never as a difference of two independently summarised endpoints).

PM's own subjective rating is carried through per run, verbatim, in its own
`pm_subjective_ratings` list -- never blended into any ranking number (same
separation this repo's design applies everywhere: deterministic scores are
comparable across runs, PM's judgement is a within-run call, and averaging
the two would destroy that distinction silently).
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

import yaml

import bench_lib

# Tool 4's own two quality-tool fields on an attempt's `quality` block
# (dev_check.py's run_lint/run_code_health, reshaped verbatim by
# model_report.py) -- used only by compute_run_coverage's per-run
# availability report (Stage 1), never by any ranking computation (quality
# is no longer scored at all -- see this module's own docstring).
_QUALITY_FIELDS = ("lint_findings_by_tool", "code_health_findings_by_category")

_REQUIRED_REPORT_KEYS = ("run_id", "developer", "run_status", "timing", "provenance", "slices", "pm_subjective_rating")

# Stage 1's structured identity block (bench_lib.resolve_developer_identity,
# reshaped through unchanged by model_report.build_report) -- discover_reports
# validates the block's own shape, not merely that a `model` key exists
# (docs/LEADERBOARD-REBUILD-PLAN.md Stage 1, fixing the "model literally
# named None" defect at its root: a report with no real identity can no
# longer even parse as valid without a `developer` block naming that).
_REQUIRED_DEVELOPER_KEYS = ("harness", "model", "effort", "configuration_key", "sources", "attributed", "attestation")


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
    needs.

    Stage 2 (docs/LEADERBOARD-REBUILD-PLAN.md) deletes `weights`,
    `scope_violation_penalty` and `iteration_reference_attempts` -- the
    composite they drove no longer exists, and AGENTS.md forbids a config
    key nothing reads. `expected_slices` is the only tunable this tool still
    needs (Stage 1's coverage/eligibility computation); no fallback default
    is ever hardcoded here (AGENTS.md: "do not invent scoring weights
    outside [policy.yaml]") -- its absence is a named LeaderboardError, not
    a silent default.
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

    # Stage 1: how many slices a run's coverage block should expect (this
    # bench's frozen plan always has two -- never inferred from whichever
    # slices happen to already be on disk, which would make an early-stopped
    # run's own incompleteness invisible).
    expected_slices = leaderboard.get("expected_slices")
    is_positive_int = isinstance(expected_slices, int) and not isinstance(expected_slices, bool) and expected_slices > 0
    if not is_positive_int:
        raise LeaderboardError(
            f"policy file {policy_path}'s leaderboard.expected_slices must be a positive integer, "
            f"got {expected_slices!r}"
        )

    return leaderboard


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
        developer = report["developer"]
        if not isinstance(developer, dict):
            raise LeaderboardError(f"model-report.json at {path}'s 'developer' block is not a mapping: {developer!r}")
        missing_developer_keys = [key for key in _REQUIRED_DEVELOPER_KEYS if key not in developer]
        if missing_developer_keys:
            raise LeaderboardError(
                f"model-report.json at {path}'s 'developer' block is missing key(s): {', '.join(missing_developer_keys)}"
            )
        if not isinstance(developer.get("attributed"), bool):
            raise LeaderboardError(
                f"model-report.json at {path}'s developer.attributed must be true/false, got {developer.get('attributed')!r}"
            )
        if not isinstance(developer.get("configuration_key"), str) or not developer["configuration_key"]:
            raise LeaderboardError(
                f"model-report.json at {path}'s developer.configuration_key must be a non-empty string, "
                f"got {developer.get('configuration_key')!r}"
            )
        run_id = report["run_id"]
        if run_id in seen_run_ids:
            raise LeaderboardError(
                f"two model-report.json files carry the same run_id {run_id!r}: {seen_run_ids[run_id]} and {path}"
            )
        seen_run_ids[run_id] = path
        reports.append((path, report))
    return reports


def group_reports_by_model(reports: list[tuple[Path, dict[str, Any]]]) -> dict[str, list[tuple[Path, dict[str, Any]]]]:
    """Every discovered report, grouped by its own `developer.configuration_key`
    -- a configuration can have several runs on disk (policy.yaml's
    `repeats`). Callers decide which reports to pass in: build_leaderboard
    only ever calls this with attributed reports (see its own docstring) --
    this function itself does not filter on `attributed`, so a caller that
    passes an unattributed report gets it grouped by whatever sentinel-laden
    configuration_key it resolved to, same as any other."""
    groups: dict[str, list[tuple[Path, dict[str, Any]]]] = {}
    for path, report in reports:
        groups.setdefault(report["developer"]["configuration_key"], []).append((path, report))
    return groups


# --- coverage/eligibility (Stage 1, unchanged by Stage 2) -------------------


def compute_run_coverage(report: dict[str, Any], leaderboard_policy: dict[str, Any]) -> dict[str, Any]:
    """One run's coverage/eligibility summary (Stage 1,
    docs/LEADERBOARD-REBUILD-PLAN.md "Strict missing-data representation").

    Recorded for **every** discovered run, attributed or not -- this is
    what lets an unattributed run stay fully visible (never discarded) even
    though it is excluded from model ranking.

    Eligibility for first-submission ranking (the ranking Stage 2 builds)
    requires all four of: identity attributed, PM status `complete`, every
    `policy.yaml`-expected slice graded, and each graded slice carrying a
    real attempt-0 row. Under G16's fallback (docs/MODE2-REWRITE-PLAN.md
    SS5/SS8) a slice can legitimately hold only its final attempt's row --
    that slice's attempt-0 is genuinely absent, never substituted with
    whatever attempt happens to be present, so such a run is correctly
    marked ineligible with a named reason rather than silently ranked on
    the wrong attempt.
    """
    expected_slices = leaderboard_policy["expected_slices"]
    slices = report.get("slices") or []
    graded_slice_numbers = sorted(
        {s.get("slice") for s in slices if isinstance(s, dict) and s.get("slice") is not None}
    )
    slices_missing_attempt_zero = sorted(
        s.get("slice") for s in slices if isinstance(s, dict) and not s.get("has_attempt_zero")
    )
    quality_tools_available: dict[str, dict[int, bool]] = {field: {} for field in _QUALITY_FIELDS}
    for slice_entry in slices:
        slice_number = slice_entry.get("slice")
        quality = (slice_entry.get("final_attempt") or {}).get("quality") or {}
        for field in _QUALITY_FIELDS:
            tool = quality.get(field) or {}
            quality_tools_available[field][slice_number] = bool(tool.get("available"))

    developer = report.get("developer") or {}
    attributed = bool(developer.get("attributed"))
    pm_status = (report.get("run_status") or {}).get("pm_status")

    reasons: list[str] = []
    if not attributed:
        reasons.append("Developer identity unattributed")
    if pm_status != "complete":
        reasons.append(f"pm_status={pm_status!r}, not 'complete'")
    if len(graded_slice_numbers) != expected_slices:
        reasons.append(f"graded {len(graded_slice_numbers)} of {expected_slices} expected slice(s): {graded_slice_numbers}")
    if slices_missing_attempt_zero:
        reasons.append(f"slice(s) with no attempt-0 row: {slices_missing_attempt_zero}")

    return {
        "expected_slices": expected_slices,
        "graded_slices": graded_slice_numbers,
        "slices_missing_attempt_zero": slices_missing_attempt_zero,
        "quality_tools_available": quality_tools_available,
        "pm_status": pm_status,
        "identity_attributed": attributed,
        "eligible_for_first_submission": not reasons,
        "ineligibility_reasons": reasons,
    }


# --- arithmetic --------------------------------------------------------


def _mean_obligation_fraction(by_obligation: dict[str, Any], *, context: str) -> float:
    """Equally-weighted mean of each obligation group's own `fraction` --
    never `hidden_tests_passed/hidden_tests_total` directly, which is an
    unweighted raw test count (AGENTS.md: the obligation partition *is* the
    rubric weight, so summing raw pass/fail counts would double-count a
    large group). Shared by first-attempt (ranking) and final-attempt
    (supervised-outcome) correctness -- the same reduction, on two
    different attempts.

    Raises:
        LeaderboardError: `by_obligation` is malformed (missing/wrong-typed
            `fraction`) or empty -- named with `context` (the caller's own
            "model X, run Y, slice Z (first|final attempt)" string) so the
            concrete offender is always identifiable.
    """
    try:
        fractions = [group["fraction"] for group in by_obligation.values()]
    except (KeyError, TypeError) as exc:
        raise LeaderboardError(f"malformed by_obligation for {context}: {exc}") from exc
    if not fractions:
        raise LeaderboardError(f"empty by_obligation for {context}")
    return sum(fractions) / len(fractions)


def _spread(values: list[float]) -> dict[str, Any] | None:
    """The 'mean [min-max], n' convention used throughout Stage 2's tables
    (docs/LEADERBOARD-REBUILD-PLAN.md: "No variance in squared units, no
    confidence intervals. At n=1, show the value and n=1, never zero
    spread."). Returns None for an empty population -- absence of data, not
    a fabricated zero; every caller treats None as "no eligible/available
    data for this cell", never as 0.
    """
    if not values:
        return None
    return {"mean": sum(values) / len(values), "min": min(values), "max": max(values), "n": len(values)}


# --- per-configuration aggregation ---------------------------------------


def aggregate_model(
    configuration_key: str,
    model_reports: list[tuple[Path, dict[str, Any]]],
    run_coverage: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], list[str]]:
    """Fold every run of one Developer configuration into its leaderboard
    row: first-attempt correctness (the ranking basis), final-attempt
    correctness, paired-run gain, attempts/steers/elapsed-time supporting
    columns, and PM's own subjective ratings carried through verbatim.

    Ranking basis (docs/LEADERBOARD-REBUILD-PLAN.md Stage 2): per slice, the
    equally-weighted mean of obligation-group fractions on the FIRST
    (ordinal-0) attempt; averaged equally across a run's two slices; then
    averaged equally across the configuration's *eligible* runs only
    (`run_coverage[run_id]["eligible_for_first_submission"]`) --
    `first_attempt_correctness["n"]` is therefore the eligible run count,
    never the discovered run count. A run ineligible for first-submission
    ranking (Stage 1: incomplete coverage, no attempt-0 row, etc.)
    contributes nothing to `first_attempt_correctness`/`gain_pp` but still
    contributes to every other column (final correctness, attempts, steers,
    elapsed time, PM ratings) -- those don't need an attempt-0 row to be
    meaningful.

    `gain_pp` (percentage points) is computed **within each paired run
    first, then summarised** (docs/LEADERBOARD-REBUILD-PLAN.md's own
    "Arithmetic" convention) -- never as a difference of two independently
    summarised endpoints. A run is "paired" when it is eligible for
    first-submission ranking AND has final-attempt correctness for every
    one of the same slices; an eligible run whose final attempt is missing
    for a slice (a genuine, named problem, see below) is excluded from
    `gain_pp` rather than silently paired against partial data.

    Raises:
        LeaderboardError: a run `run_coverage` marks
            `eligible_for_first_submission` has no first-attempt
            correctness data on its sheet for some slice -- eligibility is
            supposed to guarantee this; if it doesn't, Stage 1's own
            eligibility computation is inconsistent with the sheet it
            examined, which is a bug in this tool, not a soft data gap to
            paper over.
    """
    problems: list[str] = []
    reports_by_run_id = {report["run_id"]: report for _path, report in model_reports}
    run_ids = sorted(reports_by_run_id)

    first_attempt_run_means: list[float] = []
    eligible_run_ids: list[str] = []
    final_attempt_run_means: list[float] = []
    gain_values_pp: list[float] = []
    attempts_by_slice: dict[int, list[int]] = {}
    steers_per_run: list[int] = []
    elapsed_seconds_values: list[float] = []
    pm_status_counts: dict[str, int] = {}
    pm_subjective_ratings: list[dict[str, Any]] = []

    for run_id in run_ids:
        report = reports_by_run_id[run_id]
        coverage = run_coverage[run_id]
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
        # vanished from disk, or a malformed run-timing log) are this run's
        # evidence too -- dropping them here would make that case
        # indistinguishable from data that was simply never recorded
        # (AGENTS.md: never silently discard).
        for report_problem in report.get("problems") or []:
            problems.append(f"model {configuration_key}, run {run_id}: {report_problem}")

        timing = report.get("timing") or {}
        if timing.get("available"):
            elapsed_seconds_values.append(timing["elapsed_seconds"])

        run_first_values: list[float] = []
        run_final_values: list[float] = []
        run_steers = 0
        for slice_entry in report.get("slices") or []:
            slice_number = slice_entry.get("slice")
            attempts_by_slice.setdefault(slice_number, []).append(slice_entry.get("attempts_total"))

            for trajectory_entry in slice_entry.get("attempt_trajectory") or []:
                if trajectory_entry.get("pm_decision") == "steer":
                    run_steers += 1

            final_attempt = slice_entry.get("final_attempt")
            final_by_obligation = (final_attempt.get("correctness") or {}).get("by_obligation") if final_attempt else None
            if final_by_obligation:
                run_final_values.append(
                    _mean_obligation_fraction(
                        final_by_obligation,
                        context=f"model {configuration_key}, run {run_id}, slice {slice_number} (final attempt)",
                    )
                )
            else:
                problems.append(
                    f"model {configuration_key}, run {run_id}, slice {slice_number}: no final attempt to grade correctness from"
                )

            if coverage["eligible_for_first_submission"]:
                first_attempt = slice_entry.get("first_attempt")
                first_by_obligation = (first_attempt.get("correctness") or {}).get("by_obligation") if first_attempt else None
                if not first_by_obligation:
                    raise LeaderboardError(
                        f"model {configuration_key}, run {run_id}, slice {slice_number}: run_coverage marked "
                        "this run eligible_for_first_submission but its sheet has no first-attempt correctness "
                        "data -- eligibility computation is inconsistent with the sheet it examined"
                    )
                run_first_values.append(
                    _mean_obligation_fraction(
                        first_by_obligation,
                        context=f"model {configuration_key}, run {run_id}, slice {slice_number} (first attempt)",
                    )
                )

        steers_per_run.append(run_steers)

        if run_final_values:
            final_attempt_run_means.append(sum(run_final_values) / len(run_final_values))

        if coverage["eligible_for_first_submission"]:
            # Eligibility guarantees a first-attempt value for every slice
            # in this report (or this function already raised above), so
            # this mean is over the same slice count for every eligible run.
            run_first_mean = sum(run_first_values) / len(run_first_values)
            first_attempt_run_means.append(run_first_mean)
            eligible_run_ids.append(run_id)
            if run_final_values and len(run_final_values) == len(run_first_values):
                run_final_mean = sum(run_final_values) / len(run_final_values)
                gain_values_pp.append((run_final_mean - run_first_mean) * 100.0)

    attempts_by_slice_spread = {
        slice_number: _spread([v for v in values if isinstance(v, (int, float))])
        for slice_number, values in attempts_by_slice.items()
    }

    entry = {
        "model": configuration_key,
        "first_attempt_correctness": _spread(first_attempt_run_means),
        "final_attempt_correctness": _spread(final_attempt_run_means),
        "gain_pp": _spread(gain_values_pp),
        "attempts_by_slice": attempts_by_slice_spread,
        "steers": _spread([float(s) for s in steers_per_run]),
        "pm_elapsed_seconds": _spread(elapsed_seconds_values),
        "run_count": len(run_ids),
        "run_ids": run_ids,
        "eligible_run_ids": eligible_run_ids,
        "pm_status_counts": pm_status_counts,
        "completed_runs": pm_status_counts.get("complete", 0),
        "pm_subjective_ratings": pm_subjective_ratings,
        # Kept per-model, not just folded into the repo-wide flat list --
        # render_markdown() needs exact attribution, and a model name could
        # otherwise defeat a string-prefix recovery of it (e.g. `foo` vs.
        # `foo bar`).
        "problems": list(problems),
    }
    return entry, problems


def build_leaderboard(
    reports: list[tuple[Path, dict[str, Any]]], leaderboard_policy: dict[str, Any]
) -> tuple[dict[str, Any], list[str]]:
    """Assemble the full cross-model leaderboard from every discovered report.

    Sorted by mean first-attempt correctness descending, a configuration
    with no eligible run sorted last, ties broken by `model`
    (`configuration_key`) name ascending -- docs/LEADERBOARD-REBUILD-PLAN.md
    Stage 2 also specifies breaking a tie by smaller first-attempt
    production ΔLOC before falling back to name; that measurement is Stage
    3's job and does not exist yet, so today's tie-break is name-only. Every
    tied pair is still labelled `tied_with_previous` so the name-ordering
    is never mistaken for evidence of one configuration being better.

    Grouping and ranking are computed only over **attributed** reports
    (Stage 1's goal: "a run is attributed to a Developer configuration, or
    it is conspicuously unattributed and excluded from ranking"). An
    unattributed report is never dropped -- it is recorded in
    `unattributed_runs`, named in `problems`, and still gets a
    `run_coverage` entry -- it is simply never grouped into a `models` row,
    so it can never rank first (or at all) as a model literally named
    `None`.
    """
    problems: list[str] = []
    run_coverage = {report["run_id"]: compute_run_coverage(report, leaderboard_policy) for _path, report in reports}

    attributed_reports = [(path, report) for path, report in reports if report["developer"]["attributed"]]
    unattributed_reports = [(path, report) for path, report in reports if not report["developer"]["attributed"]]

    models = []
    for configuration_key, model_reports in group_reports_by_model(attributed_reports).items():
        entry, model_problems = aggregate_model(configuration_key, model_reports, run_coverage)
        models.append(entry)
        problems.extend(model_problems)

    def _first_attempt_mean(entry: dict[str, Any]) -> float | None:
        spread = entry["first_attempt_correctness"]
        return spread["mean"] if spread else None

    models.sort(key=lambda m: (_first_attempt_mean(m) is None, -(_first_attempt_mean(m) or 0.0), m["model"]))

    # Tied correctness is labelled, not silently absorbed into the name-order
    # tie-break above (docs/LEADERBOARD-REBUILD-PLAN.md: "tied correctness
    # is labelled as tied so the tiebreak is not read as evidence").
    previous_mean: float | None = None
    for entry in models:
        mean = _first_attempt_mean(entry)
        entry["tied_with_previous"] = (
            mean is not None and previous_mean is not None and math.isclose(mean, previous_mean, abs_tol=1e-9)
        )
        previous_mean = mean

    unattributed_runs = []
    for _path, report in sorted(unattributed_reports, key=lambda item: item[1]["run_id"]):
        developer = report["developer"]
        unattributed_runs.append({"run_id": report["run_id"], "developer": developer})
        problems.append(
            f"run {report['run_id']}: Developer identity unattributed (harness={developer.get('harness')!r}, "
            f"model={developer.get('model')!r}) -- excluded from model ranking, never discarded "
            "(see unattributed_runs and run_coverage)"
        )

    leaderboard = {
        "models": models,
        "unattributed_runs": unattributed_runs,
        "run_coverage": run_coverage,
        "problems": problems,
    }
    return leaderboard, problems


# --- Markdown rendering -----------------------------------------------------
#
# leaderboard.json is this tool's authoritative, machine-readable output;
# everything below only formats that same data (plus each model's own
# already-written model-report.json, read again here for per-slice detail)
# for a human -- no new number is computed anywhere in this section
# (AGENTS.md: recompute nothing already persisted; this reads, never
# re-derives).


def default_markdown_path(root: Path) -> Path:
    return root / "results" / "leaderboard.md"


def _fmt_score(value: Any) -> str:
    return f"{value:.3f}" if isinstance(value, (int, float)) else "--"


def _md_cell(value: Any) -> str:
    """Escape free-form plain text (a reviewer name, verdict, or a review's
    raw parse_error message -- none of which this tool controls the content
    of) for safe interpolation inside a Markdown table cell: an un-escaped
    `|` would otherwise shift or break the row, and an embedded newline
    would otherwise end it early. GFM tables treat a backslash-escaped pipe
    (`\\|`) as a literal pipe without ending the cell -- but only if the
    backslash itself isn't already escaping something, so every
    pre-existing backslash is doubled first (GFM's own backslash-escape
    rule), or a value already containing `\\|` would resolve as an escaped
    backslash followed by an unescaped pipe.

    Never use this on text that will be wrapped in `_code_span` below --
    that helper's own escaping is different and this one would corrupt it.
    """
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("\r\n", " ")
        .replace("\n", " ")
        .replace("\r", " ")
    )


def _code_span(value: Any) -> str:
    """Render `value` as a Markdown inline code span (backtick-wrapped) that
    its own content can't break. The fence is widened past the longest
    backtick run already in the text (CommonMark's own code-span rule) and
    padded with a space on each side when the text touches a backtick,
    rather than substituting a backtick outright -- two names differing
    only by a backtick must stay distinguishable. `|` is still
    backslash-escaped, same as `_md_cell`: whether GFM's table-cell
    splitter honours a code span's boundary around an embedded pipe is not
    worth gambling this repo's rendering on, and a stray visible backslash
    before a pipe that almost never occurs in a real model/obligation name
    is a harmless cosmetic wrinkle next to a broken table. A pre-existing
    backslash is never doubled, unlike `_md_cell` -- a code span's content
    is taken completely literally for backslash (no escape processing
    happens inside one, per CommonMark), so doubling would visibly show two
    characters where the source had one.
    """
    safe = str(value).replace("|", "\\|").replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
    longest_run = 0
    current_run = 0
    for char in safe:
        current_run = current_run + 1 if char == "`" else 0
        longest_run = max(longest_run, current_run)
    fence = "`" * (longest_run + 1)
    pad = " " if safe.startswith("`") or safe.endswith("`") else ""
    return f"{fence}{pad}{safe}{pad}{fence}"


def _slug(text: str) -> str:
    """A stable, URL/anchor-safe slug for `text` (a configuration_key or
    run_id) -- lowercase, non-alphanumeric runs collapsed to one hyphen,
    leading/trailing hyphens trimmed. Used only for anchor ids, never
    displayed -- the display text stays the real value, `_code_span`-quoted.
    """
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _run_anchor(run_id: str) -> str:
    """The stable anchor id for one run's detail section
    (docs/LEADERBOARD-REBUILD-PLAN.md Stage 2: "Anchors are stable and
    independent of rank and model name") -- a run_id never changes once
    recorded, so this anchor never breaks across a regeneration that
    reorders ranks or corrects an identity.
    """
    return f"run-{_slug(run_id)}"


def _config_anchor(configuration_key: str) -> str:
    return f"config-{_slug(configuration_key)}"


def _reports_by_run_id(reports: list[tuple[Path, dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    return {report["run_id"]: report for _path, report in reports}


def _fmt_pct_spread(spread: dict[str, Any] | None, *, no_data_label: str) -> str:
    if not spread:
        return no_data_label
    mean_pct = spread["mean"] * 100
    if spread["n"] == 1:
        return f"{mean_pct:.1f}% (n=1)"
    return f"{mean_pct:.1f}% [{spread['min'] * 100:.1f}-{spread['max'] * 100:.1f}%], n={spread['n']}"


def _fmt_pp_spread(spread: dict[str, Any] | None) -> str:
    if not spread:
        return "no paired data"
    if spread["n"] == 1:
        return f"{spread['mean']:+.1f}pp (n=1)"
    return f"{spread['mean']:+.1f}pp [{spread['min']:+.1f}-{spread['max']:+.1f}pp], n={spread['n']}"


def _fmt_count_spread(spread: dict[str, Any] | None) -> str:
    if not spread:
        return "--"
    if spread["n"] == 1:
        return f"{spread['mean']:.0f} (n=1)"
    return f"{spread['mean']:.1f} [{spread['min']:.0f}-{spread['max']:.0f}], n={spread['n']}"


def _fmt_elapsed(seconds: float) -> str:
    total = int(round(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}h{minutes:02d}m{secs:02d}s" if hours else f"{minutes}m{secs:02d}s"


def _fmt_elapsed_spread(spread: dict[str, Any] | None) -> str:
    if not spread:
        return "unavailable"
    if spread["n"] == 1:
        return f"{_fmt_elapsed(spread['mean'])} (n=1)"
    return f"{_fmt_elapsed(spread['mean'])} [{_fmt_elapsed(spread['min'])}-{_fmt_elapsed(spread['max'])}], n={spread['n']}"


def _runs_cell(entry: dict[str, Any]) -> str:
    """'Runs (eligible/discovered, with numbered links)' -- each run gets a
    small linked ordinal (its position in this configuration's own run
    list, 1-based for display) pointing at that run's stable anchor; an
    ordinal marked `*` is one of the eligible runs counted in the leading
    fraction.
    """
    run_ids = entry["run_ids"]
    eligible = set(entry["eligible_run_ids"])
    links = [
        f"[{i}{'*' if run_id in eligible else ''}](#{_run_anchor(run_id)})" for i, run_id in enumerate(run_ids, start=1)
    ]
    return f"{len(eligible)}/{len(run_ids)} ({', '.join(links)})"


def _obligation_table(by_obligation: dict[str, Any]) -> list[str]:
    lines = ["| Obligation group | Passed/Total | Fraction |", "|---|---|---|"]
    for name in sorted(by_obligation):
        group = by_obligation[name]
        lines.append(f"| {_code_span(name)} | {group.get('passed', '?')}/{group.get('total', '?')} | {_fmt_score(group.get('fraction'))} |")
    return lines


def _quality_summary(quality: dict[str, Any]) -> str:
    parts = []
    for field, tool_label in (("lint_findings_by_tool", "lint"), ("code_health_findings_by_category", "code-health")):
        tool = quality.get(field) or {}
        if not tool.get("available"):
            parts.append(f"{tool_label} unavailable")
        else:
            parts.append(f"{tool_label} {tool.get('verdict', '?')}")
    return ", ".join(parts) if parts else "no quality data"


def _scope_summary(scope: dict[str, Any]) -> str:
    violations = scope.get("violations") or []
    return "no violations" if not violations else f"{len(violations)} violation(s)"


def _display_attempt(ordinal: Any) -> Any:
    """Convert a 0-based machine attempt ordinal to the 1-based number a
    human reads (docs/LEADERBOARD-REBUILD-PLAN.md Stage 2's ordinal fix:
    "Machine ordinals stay 0-based everywhere in the sheets and JSON ...
    Convert ordinal + 1 ONLY at the human-display boundary"). This function
    IS that one boundary for every attempt number this renderer prints --
    nothing upstream of it ever adds 1, and nothing here adds 1 twice.
    """
    return ordinal + 1 if isinstance(ordinal, int) else "?"


def _attempt_history_table(trajectory: list[dict[str, Any]]) -> list[str]:
    """One row per Developer attempt -- including one steered with no
    review commissioned at all (docs/LEADERBOARD-REBUILD-PLAN.md Stage 2).
    `attempt_trajectory` (model_report.py) already includes every such row;
    this only formats it.
    """
    if not trajectory:
        return []
    lines = [
        "Developer attempts:",
        "",
        "| Attempt | Commit | Hidden tests | PM decision | Reviews commissioned |",
        "|---|---|---|---|---|",
    ]
    for entry in trajectory:
        correctness = entry.get("correctness") or {}
        hidden_tests = f"{correctness.get('hidden_tests_passed', '?')}/{correctness.get('hidden_tests_total', '?')}"
        commissioned = entry.get("commissioned_reviews") or []
        commissioned_cell = ", ".join(_md_cell(c.get("skill", "?")) for c in commissioned) if commissioned else "none"
        lines.append(
            f"| {_display_attempt(entry.get('attempt'))} | {_code_span(entry.get('commit_sha') or '?')} | "
            f"{hidden_tests} | {_md_cell(entry.get('pm_decision') or '(undecided)')} | {commissioned_cell} |"
        )
    return lines


def _review_order_key(row: tuple[str, dict[str, Any]]) -> tuple[Any, ...]:
    """Sort key for one review-history row: a known `event_index` (Stage
    4's job to populate -- always None today, see model_report.py's
    `_review_trend_entry`) sorts first and numerically; failing that, a
    known `at` timestamp sorts next -- ISO-8601 `Z`-suffixed strings sort
    correctly as plain strings, so no datetime parsing is needed here. A
    row with neither sorts last, by its own skill name, purely for a stable
    (not meaningful) position.
    """
    _field, entry = row
    event_index = entry.get("event_index")
    at = entry.get("at")
    at_known = isinstance(at, str) and bool(at)
    return (event_index is None, event_index if event_index is not None else 0, not at_known, at if at_known else "", _field)


def _review_history_table(review_trends: dict[str, list[dict[str, Any]]]) -> list[str]:
    """'Reviews of each attempt -- multiple rows can refer to the same
    submission' (docs/LEADERBOARD-REBUILD-PLAN.md Stage 2): one row per
    review *commission*, not per attempt -- an attempt with two reviews
    gets two rows here, distinct from the one row it gets in the
    attempt-history table above.

    Ordered by the authoritative `events.jsonl` position when known
    (`event_index`, Stage 4's job -- always None in today's cohort, see
    model_report.py's `_review_trend_entry` docstring), falling back to the
    recorded `at` timestamp otherwise. A completion timestamp is not a
    start time, so a fallback-ordered table is explicitly labelled
    "recorded order", never presented as reconstructed execution order.
    """
    rows = [(field, entry) for field, entries in review_trends.items() for entry in entries]
    if not rows:
        return []
    rows.sort(key=_review_order_key)
    any_event_index = any(entry.get("event_index") is not None for _field, entry in rows)
    any_at = any(isinstance(entry.get("at"), str) and entry.get("at") for _field, entry in rows)

    lines = ["Reviews of each attempt -- multiple rows can refer to the same submission.", ""]
    if not any_event_index and not any_at:
        lines.append(
            "_Order-unavailable: none of these reviews carry a recorded time or an events.jsonl position, "
            "so the rows below are NOT sorted by role and must not be read as chronology._"
        )
        lines.append("")
    lines += ["| Event order | Attempt | Recorded time | Role | Reviewer | Verdict / extraction status |", "|---|---|---|---|---|---|"]
    for field, entry in rows:
        event_index = entry.get("event_index")
        order_cell = str(event_index) if event_index is not None else "unavailable"
        recorded_time = entry.get("at") if isinstance(entry.get("at"), str) and entry.get("at") else "unavailable"
        reviewer = " / ".join(part for part in (entry.get("tool"), entry.get("model")) if part) or "unknown"
        if entry.get("parse_error"):
            status = f"parse error: {_md_cell(entry['parse_error'])}"
        else:
            status = _md_cell(entry.get("verdict") or "?")
        lines.append(
            f"| {order_cell} | {_display_attempt(entry.get('attempt'))} | {_md_cell(recorded_time)} | "
            f"{_md_cell(field)} | {_md_cell(reviewer)} | {status} |"
        )
    if any_at and not any_event_index:
        lines += [
            "",
            "_A true `events.jsonl` position is not yet captured for these reviews (Stage 4); the rows above "
            "are ordered by their recorded time instead -- labelled as recorded order, not reconstructed "
            "execution order._",
        ]
    return lines


def _slice_section(slice_entry: dict[str, Any]) -> list[str]:
    slice_number = slice_entry.get("slice")
    attempts_total = slice_entry.get("attempts_total")
    accepted_at = slice_entry.get("accepted_at_attempt")
    heading = (
        f"#### Slice {slice_number} -- accepted on attempt {_display_attempt(accepted_at)} of {attempts_total}"
        if accepted_at is not None
        else f"#### Slice {slice_number} -- {slice_entry.get('slice_status', '?')} after {attempts_total} attempt(s)"
    )
    lines = [heading, ""]
    if slice_entry.get("infrastructure_failure_suspected"):
        lines += ["**Infrastructure failure suspected on this slice.**", ""]

    final_attempt = slice_entry.get("final_attempt")
    if not final_attempt:
        return lines + ["_No final attempt graded._", ""]

    correctness = final_attempt.get("correctness") or {}
    lines.append(f"Hidden tests (final attempt): {correctness.get('hidden_tests_passed', '?')}/{correctness.get('hidden_tests_total', '?')}")
    lines.append("")
    by_obligation = correctness.get("by_obligation") or {}
    if by_obligation:
        lines += _obligation_table(by_obligation) + [""]

    quality = final_attempt.get("quality") or {}
    scope = final_attempt.get("scope") or {}
    lines += [
        f"Quality (measured, not scored -- Stage 3 replaces this with ΔLOC/ΔCC): {_quality_summary(quality)}. "
        f"Scope: {_scope_summary(scope)}.",
        "",
    ]

    attempt_lines = _attempt_history_table(slice_entry.get("attempt_trajectory") or [])
    if attempt_lines:
        lines += attempt_lines + [""]

    review_lines = _review_history_table(slice_entry.get("review_trends") or {})
    if review_lines:
        lines += review_lines + [""]

    return lines


def _run_section(run_id: str, report: dict[str, Any] | None, run_coverage: dict[str, dict[str, Any]]) -> list[str]:
    """One run's full detail -- anchored so a rank/name change never breaks
    a link to it (docs/LEADERBOARD-REBUILD-PLAN.md Stage 2).
    """
    lines = [f'<a id="{_run_anchor(run_id)}"></a>', "", f"### Run {_code_span(run_id)}", ""]
    if report is None:
        # Only reachable if a caller's `reports` disagrees with its own
        # `leaderboard` (e.g. a report deleted between the two) -- never
        # true for main()'s own matched pair from one discover_reports().
        return lines + [f"_Run {_code_span(run_id)}: model-report.json no longer on disk._", ""]

    provenance = report.get("provenance") or {}
    if provenance.get("available"):
        presence = provenance.get("repo_present_as_of_generation")
        presence_label = (
            "present as of this report's generation"
            if presence
            else "NOT present as of this report's generation (not proof cleanup ran -- see measurement notes)"
        )
        lines += [
            f"- Recorded branch: {_code_span(provenance.get('branch') or 'unknown')}",
            f"- Original Developer worktree: {_code_span(provenance.get('repo') or 'unknown')} ({presence_label})",
            f"- PM artifact location: {_code_span(provenance.get('pm_run_dir') or 'unknown')}",
        ]
    else:
        lines.append(f"- Provenance unavailable: {provenance.get('reason', 'not recorded')}")
    lines += [f"- Results directory: {_code_span(f'results/runs/{run_id}/')}", ""]

    accepted_commits = [
        f"slice {s.get('slice')}: {_code_span(s['final_attempt']['commit_sha'])}"
        for s in report.get("slices") or []
        if s.get("accepted_at_attempt") is not None and s.get("final_attempt")
    ]
    if accepted_commits:
        lines += [f"Accepted commits -- {'; '.join(accepted_commits)}.", ""]

    coverage = run_coverage.get(run_id) or {}
    if not coverage.get("eligible_for_first_submission"):
        reasons = "; ".join(coverage.get("ineligibility_reasons") or ["not recorded"])
        lines += [f"_Not eligible for first-submission ranking: {reasons}._", ""]

    for slice_entry in sorted(report.get("slices") or [], key=lambda s: s.get("slice", 0)):
        lines += _slice_section(slice_entry)

    rating = report.get("pm_subjective_rating") or {}
    if rating.get("available"):
        lines += ["#### PM's subjective rating (verbatim; never blended into any score)", ""]
        lines += [f"> {line}" if line else ">" for line in (rating.get("text") or "").splitlines()]
        lines.append("")

    return lines


def _model_section(rank: int, entry: dict[str, Any], reports_by_run_id: dict[str, dict[str, Any]], run_coverage: dict[str, dict[str, Any]]) -> list[str]:
    model = entry["model"]
    tie_note = " (tied with the row above on first-attempt correctness)" if entry.get("tied_with_previous") else ""
    lines = [
        f'<a id="{_config_anchor(model)}"></a>',
        "",
        f"## {rank}. {_code_span(model)}{tie_note}",
        "",
        (
            f"First-attempt correctness: {_fmt_pct_spread(entry['first_attempt_correctness'], no_data_label='no eligible runs')}. "
            f"Final correctness: {_fmt_pct_spread(entry['final_attempt_correctness'], no_data_label='no data')}. "
            f"Gain: {_fmt_pp_spread(entry['gain_pp'])}."
        ),
        "",
        (
            f"Runs: {entry['run_count']} discovered, {len(entry['eligible_run_ids'])} eligible for first-submission "
            f"ranking. Completed: {entry['completed_runs']}/{entry['run_count']}. PM elapsed: "
            f"{_fmt_elapsed_spread(entry['pm_elapsed_seconds'])}. Steers: {_fmt_count_spread(entry['steers'])}."
        ),
        "",
    ]

    model_problems = entry.get("problems") or []
    if model_problems:
        lines += [f"_{len(model_problems)} problem(s) attributed to this configuration -- see Problems below._", ""]

    for run_id in entry["run_ids"]:
        lines += _run_section(run_id, reports_by_run_id.get(run_id), run_coverage)

    return lines


def _run_index_table(reports: list[tuple[Path, dict[str, Any]]], leaderboard: dict[str, Any]) -> list[str]:
    """A flat index of every discovered run, attributed or not -- the run
    index docs/LEADERBOARD-REBUILD-PLAN.md Stage 2 asks for alongside the
    per-configuration detail above.
    """
    run_coverage = leaderboard["run_coverage"]
    configuration_by_run_id = {
        run_id: model["model"] for model in leaderboard["models"] for run_id in model["run_ids"]
    }
    lines = ["| Run | Developer configuration | PM status | Eligible for first-submission | Graded slices |", "|---|---|---|---|---|"]
    for _path, report in sorted(reports, key=lambda item: item[1]["run_id"]):
        run_id = report["run_id"]
        coverage = run_coverage.get(run_id) or {}
        configuration = configuration_by_run_id.get(run_id, "unattributed")
        lines.append(
            f"| [{_code_span(run_id)}](#{_run_anchor(run_id)}) | {_code_span(configuration)} | "
            f"{coverage.get('pm_status', '?')} | {'yes' if coverage.get('eligible_for_first_submission') else 'no'} | "
            f"{coverage.get('graded_slices', [])} |"
        )
    return lines


def render_markdown(
    leaderboard: dict[str, Any],
    reports: list[tuple[Path, dict[str, Any]]],
    leaderboard_policy: dict[str, Any],
) -> str:
    """Render `leaderboard` (the exact structure written to leaderboard.json)
    plus each model's own model-report.json detail into one human-readable
    Markdown document -- the "for a human" counterpart to leaderboard.json's
    "for a machine" one. Invents no new number: every figure here already
    exists in leaderboard.json or a model-report.json on disk.
    """
    reports_by_run_id = _reports_by_run_id(reports)
    run_coverage = leaderboard["run_coverage"]
    problems = leaderboard.get("problems") or []

    lines = [
        "# Leaderboard",
        "",
        (
            "First-submission ability and supervised outcomes for the frozen two-slice task. Higher "
            "correctness is better; smaller edits and shorter elapsed time are supporting measures."
        ),
        "",
        "## Glossary",
        "",
        (
            "- **Correctness** -- the equally-weighted mean of a slice's obligation-group `fraction`s "
            "(`hidden_tests/obligations.yaml`), never the raw hidden-test pass count, which would "
            "double-count a large group."
        ),
        (
            "- **First-attempt correctness** -- correctness on a slice's ordinal-0 (first) Developer "
            "submission, averaged equally across a run's two slices, then equally across a configuration's "
            "*eligible* runs (Stage 1's coverage/eligibility check). This is what Table 1 ranks on."
        ),
        (
            "- **Final correctness** -- correctness on a slice's accepted (or last-graded) attempt, same "
            "averaging. Not the ranking basis -- shown as a supervised-outcome measure."
        ),
        (
            "- **Gain (pp)** -- final minus first-attempt correctness, in percentage points, computed "
            "*within each paired run first* and then averaged -- never as a difference of two "
            "independently-averaged endpoints."
        ),
        "- **Attempts** -- the true PM attempt count per slice (`resolve_attempts_total`), not the number of graded rows.",
        "- **Steers** -- how many of a run's attempts PM steered rather than accepted or stopped.",
        "- **PM elapsed** -- wall-clock time from PM's `init` event to its terminal `complete`/`stop` event.",
        (
            "- **Runs (eligible/discovered)** -- a configuration's total runs on disk versus how many are "
            "eligible for first-submission ranking; every run stays visible in its own detail section "
            "regardless."
        ),
        (
            "- Spread convention throughout: **mean [min-max], n**. At n=1, the one value is shown with "
            "n=1, never a fabricated zero spread."
        ),
        (
            "- ΔLOC and ΔCC (production size/complexity) are Stage 3's job and do not appear yet -- "
            "omitted rather than shown as a placeholder `--`. Code/drift reviewer utility tables and PM's "
            "own Developer-submission ratings are Stage 4's job, likewise omitted rather than stubbed."
        ),
        "",
        "## Developer -- first submission",
        "",
        "| Rank | Developer configuration | Correctness [min-max] | Runs (eligible/discovered) |",
        "|---|---|---|---|",
    ]
    for rank, entry in enumerate(leaderboard["models"], start=1):
        tie_marker = " (tied)" if entry.get("tied_with_previous") else ""
        lines.append(
            f"| {rank}{tie_marker} | [{_code_span(entry['model'])}](#{_config_anchor(entry['model'])}) | "
            f"{_fmt_pct_spread(entry['first_attempt_correctness'], no_data_label='no eligible runs')} | "
            f"{_runs_cell(entry)} |"
        )

    lines += [
        "",
        "## Developer -- supervised outcome",
        "",
        (
            "Same row order as the table above -- never re-ranked by this table's own numbers, so a "
            "reader cannot mistake supervised-outcome position for a second, competing ranking."
        ),
        "",
        "| Rank | Developer configuration | Final correctness [min-max] | Gain (pp) | Attempts S1/S2 | Steers | PM elapsed | Completed/total |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for rank, entry in enumerate(leaderboard["models"], start=1):
        attempts_by_slice = entry["attempts_by_slice"]
        attempts_cells = "/".join(
            _fmt_count_spread(attempts_by_slice.get(slice_number)) for slice_number in sorted(attempts_by_slice)
        ) or "--"
        lines.append(
            f"| {rank} | {_code_span(entry['model'])} | "
            f"{_fmt_pct_spread(entry['final_attempt_correctness'], no_data_label='no data')} | "
            f"{_fmt_pp_spread(entry['gain_pp'])} | {attempts_cells} | {_fmt_count_spread(entry['steers'])} | "
            f"{_fmt_elapsed_spread(entry['pm_elapsed_seconds'])} | {entry['completed_runs']}/{entry['run_count']} |"
        )

    lines += [
        "",
        (
            "Code reviewer (PM-assessed utility) and drift reviewer (PM-assessed acceptability) tables are "
            "Stage 4's job -- every reviewer in this cohort ran as a singleton panel, so those tables would "
            "read \"single reviewer, no comparative score\" for every row until a real multi-model panel "
            "runs; they are left out entirely rather than published half-built."
        ),
        "",
        "## Developer configurations",
        "",
    ]
    for rank, entry in enumerate(leaderboard["models"], start=1):
        lines.append("")
        lines += _model_section(rank, entry, reports_by_run_id, run_coverage)

    lines += ["", "## Run index", ""]
    lines += _run_index_table(reports, leaderboard)

    if leaderboard.get("unattributed_runs"):
        lines += ["", "## Unattributed runs", "", (
            "Developer identity could not be resolved for these runs (Stage 1) -- excluded from every "
            "configuration's ranking above, never discarded."
        ), ""]
        for run in leaderboard["unattributed_runs"]:
            lines += _run_section(run["run_id"], reports_by_run_id.get(run["run_id"]), run_coverage)

    lines += [
        "",
        "## Measurement notes",
        "",
        (
            "Generated by `tools/leaderboard.py` (the last step of `cohort_run.py analyze`) from every "
            "`model-report.json` under `results/runs/`. Do not hand-edit -- re-run instead: "
            "`python tools/leaderboard.py`."
        ),
        (
            "`results/leaderboard.json` carries the same ranking in machine-readable form; the per-slice "
            "detail below is read fresh from each run's own `model-report.json`, not duplicated into "
            "`leaderboard.json` itself."
        ),
        (
            "A run's worktree shown \"NOT present as of this report's generation\" is an observation at "
            "generation time only -- it is not proof `cohort_run.py cleanup` ran, since the worktree could "
            "equally have been removed by hand or never existed at that path on this machine."
        ),
        (
            "No composite score exists in this generation (docs/LEADERBOARD-REBUILD-PLAN.md Stage 2 removed "
            "it entirely) -- correctness ranks configurations on its own; ΔLOC/ΔCC (Stage 3) and PM's own "
            "judgments (Stage 4) will appear as further supporting columns, never blended into a score."
        ),
        "",
        "## Problems",
        "",
    ]
    if problems:
        lines.append(f"{len(problems)} problem(s) surfaced while building this leaderboard, listed once here:")
        lines.append("")
        lines += [f"- {problem}" for problem in problems]
    else:
        lines.append("None.")

    return "\n".join(lines) + "\n"


# --- CLI -----------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Rebuild the cross-model leaderboard from every model-report.json on disk, ranked by mean "
            "first-attempt correctness (docs/MODE2-REWRITE-PLAN.md §6, Tool 5; ranking basis rebuilt per "
            "docs/LEADERBOARD-REBUILD-PLAN.md Stage 2). PM-run data only."
        )
    )
    parser.add_argument("--out", type=Path, default=None, help="defaults to results/leaderboard.json")
    parser.add_argument("--markdown-out", type=Path, default=None, help="defaults to results/leaderboard.md")
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
    markdown_path = (args.markdown_out or default_markdown_path(root)).expanduser().resolve()

    reports = discover_reports(runs_root)
    leaderboard, problems = build_leaderboard(reports, leaderboard_policy)
    # Rendered before either file is written: a render_markdown() bug must
    # leave both leaderboard.json and leaderboard.md at their prior
    # generation, never JSON updated with Markdown left stale behind it.
    markdown = render_markdown(leaderboard, reports, leaderboard_policy)
    bench_lib.write_json_atomically(out_path, leaderboard)
    bench_lib.write_text_atomically(markdown_path, markdown, suffix=".md.tmp")
    print(f"wrote {out_path} ({len(leaderboard['models'])} model(s) from {len(reports)} report(s))")
    print(f"wrote {markdown_path}")
    return bench_lib.report_problems("leaderboard.py", problems)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except LeaderboardError as exc:
        print(f"leaderboard.py: error: {exc}", file=sys.stderr)
        sys.exit(1)
