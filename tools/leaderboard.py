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
(Stage 3) and PM's own judgments (Stage 4b: reviewer PM-ratings/comparisons
and the Developer PM-rating column, `aggregate_reviewers`/
`_reviewer_utility_table`/`_reviewer_acceptability_table` below) are
supporting columns/tables, never folded into a score. Every remaining
number here is a direct, documented
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
from typing import Any, Callable

import yaml

import bench_lib

# Tool 4's own two quality-tool fields on an attempt's `quality` block
# (dev_check.py's run_lint/run_code_health, reshaped verbatim by
# model_report.py) -- used only by compute_run_coverage's per-run
# availability report (Stage 1), never by any ranking computation (quality
# is no longer scored at all -- see this module's own docstring).
_QUALITY_FIELDS = ("lint_findings_by_tool", "code_health_findings_by_category")

_REQUIRED_REPORT_KEYS = ("run_id", "developer", "run_status", "timing", "provenance", "slices", "pm_subjective_rating")

# The rubric a slice's correctness was graded under, as model_report.py's
# resolve_correctness_provenance writes it onto each slice entry. Ranked
# reports must agree on all three per slice number, or their correctness
# scores are not comparable and must not be averaged together.
_CORRECTNESS_PROVENANCE_KEYS = ("plan_hash", "obligations_hash", "hidden_tests_hash")

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


def _production_loc_net(attempt: dict[str, Any] | None) -> float | None:
    """The production bucket's net ΔLOC from one attempt's own
    `size_complexity` block (docs/LEADERBOARD-REBUILD-PLAN.md Stage 3), or
    None when the attempt is absent or the measurement itself is recorded
    unavailable -- never a fabricated 0 (a slice with no available
    measurement renders as unavailable, never as 0, throughout Stage 3's
    tables)."""
    if not attempt:
        return None
    loc = (attempt.get("size_complexity") or {}).get("loc") or {}
    if not loc.get("available"):
        return None
    return ((loc.get("buckets") or {}).get("production") or {}).get("net")


def _production_code_loc_net(attempt: dict[str, Any] | None) -> float | None:
    """The production bucket's net ΔLOC restricted to the `code` category
    of `size_complexity.loc.production_categories` -- physical ΔLOC minus
    docstring/comment/blank churn (C1: the fitness review found physical
    ΔLOC alone misleading as the headline production-size figure, since it
    is inflated by documentation the code/docstring/comment/blank split
    already decomposes). Same availability contract as
    `_production_loc_net`: None when the attempt or the category split is
    absent or recorded unavailable, never a fabricated 0."""
    if not attempt:
        return None
    categories = ((attempt.get("size_complexity") or {}).get("loc") or {}).get("production_categories") or {}
    if not categories.get("available"):
        return None
    return (categories.get("net") or {}).get("code")


def _production_cc_net(attempt: dict[str, Any] | None) -> float | None:
    """The production bucket's net ΔCC from one attempt's own
    `size_complexity` block -- same availability contract as
    _production_loc_net above. Descriptive only, never scored (see
    dev_check.compute_complexity_delta's own docstring)."""
    if not attempt:
        return None
    complexity = (attempt.get("size_complexity") or {}).get("complexity") or {}
    if not complexity.get("available"):
        return None
    return (complexity.get("production") or {}).get("net")


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


# --- rank-support diagnostic (F1, docs/LEADERBOARD-FITNESS-REVIEW-2026-09-15.md) ---
#
# Two separately-named categorical facts about one adjacent pair in the
# final ranking, never combined into a score, confidence grade or
# stability number (the review's own proposal to collapse near-equal rows
# into shared ranks is explicitly rejected -- see the module docstring
# addendum in render_markdown's Table 1 prose for why):
#
# - Rubric robustness: does the strict ordering survive removing every
#   single hidden-test node, one at a time (leave-one-node-out)?
# - Run-range overlap: do the two configurations' observed first-attempt
#   min-max ranges overlap?


def _slice_mean_from_node_outcomes(node_outcomes: dict[str, dict[str, str]], *, exclude_node: str | None = None) -> float:
    """The equally-weighted mean of one slice's obligation-group pass
    fractions, recomputed directly from its per-node outcome map --
    `exclude_node` removes one node from its own group's denominator
    first. A group emptied by the exclusion is dropped from the mean
    rather than dividing by zero (docs/LEADERBOARD-FITNESS-REVIEW-2026-09-15.md
    F1: "If removing a node would empty a group, drop that group from the
    slice mean rather than dividing by zero").

    Raises:
        LeaderboardError: excluding `exclude_node` empties every group in
            this slice, leaving no group left to average -- named rather
            than silently returning some placeholder value.
    """
    fractions: list[float] = []
    for nodes in node_outcomes.values():
        if exclude_node is not None and exclude_node in nodes:
            remaining = {node_id: outcome for node_id, outcome in nodes.items() if node_id != exclude_node}
            if not remaining:
                continue
            fractions.append(sum(1 for outcome in remaining.values() if outcome == "passed") / len(remaining))
        else:
            fractions.append(sum(1 for outcome in nodes.values() if outcome == "passed") / len(nodes))
    if not fractions:
        raise LeaderboardError(
            f"leave-one-node-out: excluding node {exclude_node!r} emptied every obligation group in this "
            "slice, leaving nothing to average"
        )
    return sum(fractions) / len(fractions)


def _config_mean_excluding_node(
    eligible_node_outcomes_by_run: dict[str, dict[int, dict[str, Any] | None]],
    *,
    exclude_slice: int,
    exclude_node: str,
) -> float:
    """One configuration's mean first-attempt correctness with one
    (slice, node) pair excised from its own slice's own denominator --
    the full scoring hierarchy repeated per run and per slice (never a
    nominal-weight subtraction from an already-aggregated mean): recompute
    the affected slice's group-fraction mean, average equally across the
    run's slices, then average equally across the configuration's eligible
    runs (docs/LEADERBOARD-FITNESS-REVIEW-2026-09-15.md F1's "implementation
    trap").

    Raises:
        LeaderboardError: an eligible run has no stored
            `first_attempt_node_outcomes` for some slice -- eligibility
            already guarantees a first-attempt row exists, so a missing
            node map here means the per-node map was never persisted for
            this run, which must stop this computation rather than being
            silently skipped (docs/LEADERBOARD-FITNESS-REVIEW-2026-09-15.md
            F1: "a null map on an eligible run is a loud, named error").
    """
    run_means: list[float] = []
    for run_id, by_slice in eligible_node_outcomes_by_run.items():
        slice_means: list[float] = []
        for slice_number, node_outcomes in by_slice.items():
            if node_outcomes is None:
                raise LeaderboardError(
                    f"leave-one-node-out: eligible run {run_id!r} slice {slice_number} has no "
                    "first_attempt_node_outcomes recorded -- eligibility requires a first-attempt row, so "
                    "this map must not be null"
                )
            if slice_number == exclude_slice:
                slice_means.append(_slice_mean_from_node_outcomes(node_outcomes, exclude_node=exclude_node))
            else:
                slice_means.append(_slice_mean_from_node_outcomes(node_outcomes))
        run_means.append(sum(slice_means) / len(slice_means))
    return sum(run_means) / len(run_means)


def _node_universe(*node_outcome_maps: dict[str, dict[int, dict[str, Any] | None]]) -> set[tuple[int, str]]:
    """Every `(slice_number, node_id)` pair appearing in any of the given
    configurations' eligible-run node-outcome maps -- node ids collide
    across slices (both slices carry a `test_hA.py`/`test_hB.py`), so a
    node is only ever addressed keyed on the pair, never the bare id.

    Raises:
        LeaderboardError: an eligible run's slice has a null
            `first_attempt_node_outcomes` map (docs/MODE2-REWRITE-PLAN.md
            §8 G21: eligibility for first-submission ranking requires a
            first-attempt row, so a null map on an eligible run is a named
            bug, never silently skipped -- skipping it here let a universe
            built from *no* eligible evidence be reported `robust: true`
            further up in `_rank_support`, a fabricated-looking verdict
            from zero comparisons).
    """
    universe: set[tuple[int, str]] = set()
    for by_run in node_outcome_maps:
        for run_id, by_slice in by_run.items():
            for slice_number, node_outcomes in by_slice.items():
                if node_outcomes is None:
                    raise LeaderboardError(
                        f"leave-one-node-out: eligible run {run_id!r} slice {slice_number} has no "
                        "first_attempt_node_outcomes recorded -- eligibility requires a first-attempt row, so "
                        "this map must not be null"
                    )
                for nodes in node_outcomes.values():
                    for node_id in nodes:
                        universe.add((slice_number, node_id))
    return universe


def _rank_support(entry_above: dict[str, Any], entry_below: dict[str, Any]) -> dict[str, Any]:
    """The two-fact rank-support diagnostic for one adjacent pair in the
    final ranking (`entry_above` currently ranked ahead of `entry_below`
    on mean first-attempt correctness).

    Returns a dict with `available: False` and a `reason` when either side
    has no eligible run to compare (nothing to leave-one-out or to range
    against) -- an honest structural gap, not a computed verdict.
    """
    above_runs = entry_above["eligible_node_outcomes_by_run"]
    below_runs = entry_below["eligible_node_outcomes_by_run"]
    above_spread = entry_above["first_attempt_correctness"]
    below_spread = entry_below["first_attempt_correctness"]
    if not above_runs or not below_runs or above_spread is None or below_spread is None:
        return {
            "available": False,
            "reason": f"{entry_above['model']!r} or {entry_below['model']!r} has no eligible run to compare",
        }

    universe = sorted(_node_universe(above_runs, below_runs))
    robust = True
    witness_slice: int | None = None
    witness_node: str | None = None
    witness_tied: bool | None = None
    for slice_number, node_id in universe:
        above_excl = _config_mean_excluding_node(above_runs, exclude_slice=slice_number, exclude_node=node_id)
        below_excl = _config_mean_excluding_node(below_runs, exclude_slice=slice_number, exclude_node=node_id)
        if not (above_excl > below_excl):
            robust = False
            witness_slice, witness_node = slice_number, node_id
            witness_tied = above_excl == below_excl
            break

    ranges_overlap = above_spread["min"] <= below_spread["max"] and below_spread["min"] <= above_spread["max"]

    return {
        "available": True,
        "robust": robust,
        "witness_slice": witness_slice,
        "witness_node": witness_node,
        "witness_tied": witness_tied,
        "ranges_overlap": ranges_overlap,
    }


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
    # Stage 4b (docs/LEADERBOARD-REBUILD-PLAN.md): PM's own 0-2 rating of
    # each Developer SUBMISSION (`attempt_trajectory`'s `pm_developer_judgment`,
    # model_report.resolve_pm_judgments), flattened across every attempt of
    # every run for this configuration -- like `steers`/`pm_elapsed_seconds`
    # above, this is a supervised-outcome measure and is collected for every
    # discovered run, not gated on first-submission eligibility. An attempt
    # PM never rated contributes nothing (status != "rated"), never a
    # fabricated 0 -- an honest gap, not inferred (see that function's own
    # docstring: pm_lib refuses historical backfill by construction).
    pm_developer_rating_scores: list[float] = []
    # Stage 3 (docs/LEADERBOARD-REBUILD-PLAN.md): production ΔLOC/ΔCC, per
    # slice, first-attempt (eligible runs only, same guard as correctness
    # above) and final-attempt (every run, like final correctness). A slice
    # with no available measurement for a given run contributes nothing to
    # that slice's list -- _spread renders an empty list as unavailable,
    # never a fabricated 0.
    first_loc_by_slice: dict[int, list[float]] = {}
    first_code_loc_by_slice: dict[int, list[float]] = {}
    first_cc_by_slice: dict[int, list[float]] = {}
    final_loc_by_slice: dict[int, list[float]] = {}
    final_code_loc_by_slice: dict[int, list[float]] = {}
    final_cc_by_slice: dict[int, list[float]] = {}

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
            # setdefault unconditionally, even when nothing is appended below
            # (matching attempts_by_slice's own pattern above), so every
            # model's per-slice dict carries the same key set for rendering
            # to iterate, and a slice with zero available measurements still
            # renders as an explicit "unavailable" cell, never a missing one.
            final_loc_by_slice.setdefault(slice_number, [])
            final_code_loc_by_slice.setdefault(slice_number, [])
            final_cc_by_slice.setdefault(slice_number, [])
            first_loc_by_slice.setdefault(slice_number, [])
            first_code_loc_by_slice.setdefault(slice_number, [])
            first_cc_by_slice.setdefault(slice_number, [])

            for trajectory_entry in slice_entry.get("attempt_trajectory") or []:
                if trajectory_entry.get("pm_decision") == "steer":
                    run_steers += 1
                pm_developer_judgment = trajectory_entry.get("pm_developer_judgment") or {}
                if pm_developer_judgment.get("status") == "rated":
                    pm_developer_rating_scores.append(pm_developer_judgment["score"])

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
            final_loc_net = _production_loc_net(final_attempt)
            if final_loc_net is not None:
                final_loc_by_slice[slice_number].append(final_loc_net)
            final_code_loc_net = _production_code_loc_net(final_attempt)
            if final_code_loc_net is not None:
                final_code_loc_by_slice[slice_number].append(final_code_loc_net)
            final_cc_net = _production_cc_net(final_attempt)
            if final_cc_net is not None:
                final_cc_by_slice[slice_number].append(final_cc_net)

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
                first_loc_net = _production_loc_net(first_attempt)
                if first_loc_net is not None:
                    first_loc_by_slice[slice_number].append(first_loc_net)
                first_code_loc_net = _production_code_loc_net(first_attempt)
                if first_code_loc_net is not None:
                    first_code_loc_by_slice[slice_number].append(first_code_loc_net)
                first_cc_net = _production_cc_net(first_attempt)
                if first_cc_net is not None:
                    first_cc_by_slice[slice_number].append(first_cc_net)

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
    first_loc_by_slice_spread = {slice_number: _spread(values) for slice_number, values in first_loc_by_slice.items()}
    first_code_loc_by_slice_spread = {
        slice_number: _spread(values) for slice_number, values in first_code_loc_by_slice.items()
    }
    first_cc_by_slice_spread = {slice_number: _spread(values) for slice_number, values in first_cc_by_slice.items()}
    final_loc_by_slice_spread = {slice_number: _spread(values) for slice_number, values in final_loc_by_slice.items()}
    final_code_loc_by_slice_spread = {
        slice_number: _spread(values) for slice_number, values in final_code_loc_by_slice.items()
    }
    final_cc_by_slice_spread = {slice_number: _spread(values) for slice_number, values in final_cc_by_slice.items()}

    # docs/LEADERBOARD-FITNESS-REVIEW-2026-09-15.md F1/F3: the ΔLOC
    # tie-break is deleted -- an unvalidated proxy must never resolve a
    # near-tie that the rubric itself cannot separate. Ordering now falls
    # back to `configuration_key` ascending only (see build_leaderboard's
    # `_sort_key`).

    # F1's rank-support diagnostic (leave-one-node-out robustness and
    # run-range overlap) needs every eligible run's own first-attempt
    # per-node outcome map, nested by slice -- kept here so
    # build_leaderboard's adjacent-pair computation (after the whole
    # `models` list is sorted) does not have to re-walk every report a
    # second time.
    eligible_node_outcomes_by_run: dict[str, dict[int, dict[str, Any]]] = {}
    for run_id in eligible_run_ids:
        report = reports_by_run_id[run_id]
        eligible_node_outcomes_by_run[run_id] = {
            slice_entry["slice"]: slice_entry.get("first_attempt_node_outcomes")
            for slice_entry in report.get("slices") or []
        }

    entry = {
        "model": configuration_key,
        "first_attempt_correctness": _spread(first_attempt_run_means),
        "final_attempt_correctness": _spread(final_attempt_run_means),
        "gain_pp": _spread(gain_values_pp),
        "attempts_by_slice": attempts_by_slice_spread,
        "first_loc_by_slice": first_loc_by_slice_spread,
        "first_code_loc_by_slice": first_code_loc_by_slice_spread,
        "first_cc_by_slice": first_cc_by_slice_spread,
        "final_loc_by_slice": final_loc_by_slice_spread,
        "final_code_loc_by_slice": final_code_loc_by_slice_spread,
        "final_cc_by_slice": final_cc_by_slice_spread,
        "eligible_node_outcomes_by_run": eligible_node_outcomes_by_run,
        "steers": _spread([float(s) for s in steers_per_run]),
        "pm_elapsed_seconds": _spread(elapsed_seconds_values),
        "run_count": len(run_ids),
        "run_ids": run_ids,
        "eligible_run_ids": eligible_run_ids,
        "pm_status_counts": pm_status_counts,
        "completed_runs": pm_status_counts.get("complete", 0),
        "pm_subjective_ratings": pm_subjective_ratings,
        # Stage 4b: Table 2's "PM Developer rating (mean /2, n)" column --
        # PM's own judgement, shown alongside the deterministic columns but
        # never blended into any of them (the same separation
        # pm_subjective_rating already gets).
        "pm_developer_rating": _spread(pm_developer_rating_scores),
        # Kept per-model, not just folded into the repo-wide flat list --
        # render_markdown() needs exact attribution, and a model name could
        # otherwise defeat a string-prefix recovery of it (e.g. `foo` vs.
        # `foo bar`).
        "problems": list(problems),
    }
    return entry, problems


# --- reviewer aggregation (Stage 4b, docs/LEADERBOARD-REBUILD-PLAN.md) -----
#
# PM assesses BOTH reviewer skills, from the same two judgment shapes
# harvested onto each report by model_report.resolve_pm_judgments: a 0-2
# rating per review report (`pm_rating` on each `reviews` entry) and,
# separately, a best-first panel comparison (`pm_judgments.comparisons`).
# Grouped by reviewer CONFIGURATION (tool, model, effort) -- never by run or
# by skill+run -- because the question these tables answer is "how good IS
# this reviewer", across every submission it ever reviewed.


def _reviewer_identity(review: dict[str, Any]) -> tuple[Any, Any, Any]:
    return (review.get("tool"), review.get("model"), review.get("effort"))


def _reviewer_label(identity: tuple[Any, Any, Any]) -> str:
    """Display identity for a reviewer configuration -- model first (this
    repo's own `configuration_key` convention: model is the thing a reader
    is actually comparing), then tool, then effort when recorded. Never
    merged across a null/non-null effort difference, same as
    bench_lib.resolve_developer_identity's `configuration_key`."""
    tool, model, effort = identity
    label = f"{model or 'model unknown'} · {tool or 'tool unknown'}"
    if effort:
        label += f" · {effort}"
    return label


def _rank_points(rank_groups: list[list[dict[str, Any]]]) -> list[tuple[dict[str, Any], float]]:
    """Normalized rank points for one resolved comparison round (Stage 4b):
    for a panel of N and 1-based rank r, `(N-r)/(N-1)`; a tied group (more
    than one reviewer at the same best-first position) shares the MEAN
    occupied rank, per the plan's own spec.

    `rank_groups` is best-first: group 0 is rank 1 (or ranks 1..k for a
    k-way tie), group 1 starts at rank k+1, and so on -- exactly
    `model_report.py`'s own resolved `pm_judgments.comparisons[].rank_groups`
    shape (a list of lists of `{review_id, tool, model, effort}`).

    Returns:
        `[]` when N <= 1 -- a singleton panel has no comparative score at
        all, never a fabricated 1.0 (the plan is explicit: "N = 1 has no
        comparative score, not 1.0"). Otherwise one `(review, points)` pair
        per reviewer entry across every group, in no particular order.
    """
    total = sum(len(group) for group in rank_groups)
    if total <= 1:
        return []
    results: list[tuple[dict[str, Any], float]] = []
    position = 1
    for group in rank_groups:
        size = len(group)
        if size == 0:
            continue
        mean_rank = position + (size - 1) / 2
        points = (total - mean_rank) / (total - 1)
        for review in group:
            results.append((review, points))
        position += size
    return results


class _UnionFind:
    """Minimal union-find for the "disconnected comparison groups" check
    (docs/LEADERBOARD-REBUILD-PLAN.md Stage 4b: "mark disconnected
    comparison groups as not globally comparable"). Two reviewer identities
    are connected exactly when they have ever appeared together in the same
    (N>1) comparison round, anywhere in the cohort -- normalized rank points
    are only comparable within one connected component, since a point value
    earned against one set of opponents says nothing about a reviewer who
    never faced any of them.
    """

    def __init__(self) -> None:
        self._parent: dict[Any, Any] = {}

    def find(self, item: Any) -> Any:
        self._parent.setdefault(item, item)
        while self._parent[item] != item:
            self._parent[item] = self._parent[self._parent[item]]
            item = self._parent[item]
        return item

    def union(self, a: Any, b: Any) -> None:
        root_a, root_b = self.find(a), self.find(b)
        if root_a != root_b:
            self._parent[root_a] = root_b


def aggregate_reviewers(reports: list[tuple[Path, dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    """One row per reviewer CONFIGURATION per skill, folded from every
    discovered report's own `reviews`/`pm_judgments` (already harvested by
    model_report.resolve_pm_judgments -- this never re-reads run.json, per
    the plan's own "so Tool 5 can build its tables without re-reading
    run.json").

    Two independent signals per row, never blended together:

    - **PM rating** -- the mean 0-2 rating (`pm_rating.status == "rated"`)
      across every review report this identity produced for this skill, in
      every discovered run. A review PM marked `"unavailable"` (a timed-out
      or unreadable report -- a reliability outcome, never a substantive
      0) is counted separately in `unavailable_count`, never folded into
      the rating mean. `unacceptable_count` is the rated subset scoring
      exactly 0 -- drift-audit's own "unacceptable / assessed" column
      (Table 4); code-review computes it too, harmlessly unused by Table 3.
    - **Comparative rank score** -- PM's own panel comparisons, reduced via
      `_rank_points`. "Average a reviewer's eligible round scores within a
      run, then average run means" (the plan's own chosen estimator, not a
      straight round mean): a run contributing several rounds is not
      allowed to outweigh a run contributing one. A reviewer with zero
      eligible (N>1) rounds anywhere has `comparative_score: None` -- the
      rule, not a claim about any particular cohort's shape: whether that
      is every row (a wholly singleton role) or only some of them (a role
      with a mix of solo and panel commissions) is derived at render time
      from the rows actually being rendered (see `_has_eligible_comparison`
      and its two call sites), never hardcoded here.

    Returns:
        `{"code-review": [rows...], "drift-audit": [rows...]}`, each row
        sorted by PM rating mean descending (a row with no ratings at all
        sorts last) -- a presentational ordering only, never described as a
        ranking the way Table 1/2 are.
    """
    # identity -> accumulator, one dict per skill.
    accumulators: dict[str, dict[tuple[Any, Any, Any], dict[str, Any]]] = {"code-review": {}, "drift-audit": {}}

    def _acc(skill: str, identity: tuple[Any, Any, Any]) -> dict[str, Any]:
        return accumulators[skill].setdefault(
            identity,
            {
                "identity": identity,
                "run_ids": set(),
                "rated_scores": [],
                "unavailable_count": 0,
                "unacceptable_count": 0,
                "rounds": 0,
                "panel_sizes": set(),
                # {run_id: [points, ...]} for this identity's ELIGIBLE (N>1)
                # rounds only -- reduced to a per-run mean, then averaged
                # across runs, per this function's own docstring.
                "points_by_run": {},
                "opponent_identities": set(),
            },
        )

    union_find = _UnionFind()

    for _path, report in reports:
        run_id = report.get("run_id")
        for slice_entry in report.get("slices") or []:
            for review in slice_entry.get("reviews") or []:
                skill = review.get("skill")
                if skill not in accumulators:
                    continue  # a skill this repo doesn't build a reviewer table for at all.
                identity = _reviewer_identity(review)
                acc = _acc(skill, identity)
                acc["run_ids"].add(run_id)
                rating = review.get("pm_rating") or {}
                status = rating.get("status")
                if status == "rated":
                    acc["rated_scores"].append(rating["score"])
                    if rating["score"] == 0:
                        acc["unacceptable_count"] += 1
                elif status == "unavailable":
                    acc["unavailable_count"] += 1

        pm_judgments = report.get("pm_judgments") or {}
        for comparison in pm_judgments.get("comparisons") or []:
            skill = comparison.get("skill")
            if skill not in accumulators:
                continue
            rank_groups = comparison.get("rank_groups") or []
            all_members = [member for group in rank_groups for member in group]
            panel_size = len(all_members)
            for member in all_members:
                identity = _reviewer_identity(member)
                acc = _acc(skill, identity)
                acc["run_ids"].add(run_id)
                acc["rounds"] += 1
                if panel_size:
                    acc["panel_sizes"].add(panel_size)
            for member, points in _rank_points(rank_groups):
                identity = _reviewer_identity(member)
                acc = _acc(skill, identity)
                acc["points_by_run"].setdefault(run_id, []).append(points)
                for other in all_members:
                    other_identity = _reviewer_identity(other)
                    if other_identity == identity:
                        continue
                    acc["opponent_identities"].add(other_identity)
                    union_find.union(identity, other_identity)

    reviewers: dict[str, list[dict[str, Any]]] = {}
    for skill, by_identity in accumulators.items():
        # A component id only distinguishes rows that actually have a
        # comparative score at all -- a reviewer with none has nothing to
        # be "disconnected" from, and is never assigned one.
        component_members: dict[Any, int] = {}
        rows: list[dict[str, Any]] = []
        for identity, acc in by_identity.items():
            run_means = [sum(points) / len(points) for points in acc["points_by_run"].values()]
            comparative_score = _spread(run_means)
            rows.append(
                {
                    "identity": {"tool": identity[0], "model": identity[1], "effort": identity[2]},
                    "label": _reviewer_label(identity),
                    "rating": _spread(acc["rated_scores"]),
                    "rated_count": len(acc["rated_scores"]),
                    "unavailable_count": acc["unavailable_count"],
                    "unacceptable_count": acc["unacceptable_count"],
                    "rounds": acc["rounds"],
                    "distinct_runs": len(acc["run_ids"]),
                    "panel_sizes": sorted(acc["panel_sizes"]),
                    "comparative_score": comparative_score,
                    "opponent_count": len(acc["opponent_identities"]),
                }
            )
            if comparative_score is not None:
                root = union_find.find(identity)
                component_members.setdefault(root, len(component_members) + 1)

        component_count = len(component_members)
        for identity, row in zip(by_identity, rows, strict=True):
            if row["comparative_score"] is not None:
                root = union_find.find(identity)
                row["comparative_component"] = component_members[root]
                row["comparative_globally_comparable"] = component_count <= 1
            else:
                row["comparative_component"] = None
                row["comparative_globally_comparable"] = None

        # Presentational only (this function's own docstring): highest PM
        # rating first, a row with no ratings at all sorts last, tied rows
        # broken by label for determinism.
        rows.sort(
            key=lambda row: (
                row["rating"] is None,
                -(row["rating"]["mean"] if row["rating"] else 0.0),
                row["label"],
            )
        )
        reviewers[skill] = rows

    return reviewers


def _check_correctness_provenance_consistency(
    reports: list[tuple[Path, dict[str, Any]]], run_coverage: dict[str, dict[str, Any]]
) -> None:
    """Refuse to build a leaderboard when eligible reports disagree, per
    slice number, on the `plan_hash`/`obligations_hash`/`hidden_tests_hash`
    triple they were graded under (A1: `dev_check.build_provenance`'s
    `hidden_tests_hash` exists specifically to catch a stale report graded
    under a since-changed hidden-test body or obligation map being averaged
    and ranked as if comparable -- nothing consumed it before this check).

    Compared per slice **number**, never across slices: slice 1 and slice 2
    carry different hidden-test files by design, so their hashes legitimately
    differ from each other.

    Only reports eligible for first-submission ranking are compared -- an
    ineligible run never enters the ranked average, so a stale hash on one
    cannot silently corrupt it, but is also not a reason to refuse building
    the leaderboard for everyone else.

    Raises:
        LeaderboardError: naming every disagreeing run id, the slice
            number, and each run's differing hash triple.
    """
    by_slice: dict[int, dict[str, dict[str, Any] | None]] = {}
    for _path, report in reports:
        run_id = report["run_id"]
        if not (run_coverage.get(run_id) or {}).get("eligible_for_first_submission"):
            continue
        for slice_entry in report.get("slices") or []:
            slice_number = slice_entry.get("slice")
            by_slice.setdefault(slice_number, {})[run_id] = slice_entry.get("correctness_provenance")

    for slice_number, provenance_by_run in sorted(by_slice.items()):
        # A triple carrying a null hash is as unusable as an absent block:
        # every such report "agrees" with every other, so a cohort of them
        # would pass this check and rank on unverifiable comparability --
        # the same fabricated-agreement-from-no-evidence shape the
        # null-node-map check above exists to stop.
        missing = sorted(
            run_id
            for run_id, provenance in provenance_by_run.items()
            if not provenance or any(provenance.get(key) is None for key in _CORRECTNESS_PROVENANCE_KEYS)
        )
        if missing:
            raise LeaderboardError(
                f"slice {slice_number}: eligible run(s) {missing} for first-submission ranking have no "
                "complete correctness_provenance (plan_hash/obligations_hash/hidden_tests_hash) -- rubric "
                "comparability across ranked reports cannot be checked"
            )
        distinct_triples = {tuple(sorted(provenance.items())) for provenance in provenance_by_run.values()}
        if len(distinct_triples) > 1:
            detail = ", ".join(
                f"{run_id!r}={provenance}" for run_id, provenance in sorted(provenance_by_run.items())
            )
            raise LeaderboardError(
                f"slice {slice_number}: eligible runs disagree on correctness provenance "
                f"(plan_hash/obligations_hash/hidden_tests_hash) -- ranked reports must be graded under "
                f"the same rubric to be averaged/ranked together: {detail}"
            )


def build_leaderboard(
    reports: list[tuple[Path, dict[str, Any]]], leaderboard_policy: dict[str, Any]
) -> tuple[dict[str, Any], list[str]]:
    """Assemble the full cross-model leaderboard from every discovered report.

    Sorted by mean first-attempt correctness descending, a configuration
    with no eligible run sorted last; ties (including an exact tie on
    first-attempt correctness) break by `model` (`configuration_key`) name
    ascending -- a stable, disclosed order, never an unvalidated proxy like
    ΔLOC (docs/LEADERBOARD-FITNESS-REVIEW-2026-09-15.md F1/F3: the review's
    own band-collapse proposal is rejected, and no shared/tied ranks are
    ever emitted; see `_rank_support` for the two-fact diagnostic that
    replaces both the collapsed rank and the ΔLOC tie-break).

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
    _check_correctness_provenance_consistency(reports, run_coverage)

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

    def _sort_key(entry: dict[str, Any]) -> tuple[Any, ...]:
        mean = _first_attempt_mean(entry)
        return (mean is None, -(mean or 0.0), entry["model"])

    models.sort(key=_sort_key)

    # F1's rank-support diagnostic: computed once per adjacent pair, over
    # the FINAL sorted order -- never re-derived at render time (render_
    # markdown stays free of new arithmetic). The first row has no row
    # above it to compare against.
    if models:
        models[0]["rank_support"] = None
    for i in range(1, len(models)):
        models[i]["rank_support"] = _rank_support(models[i - 1], models[i])

    # `eligible_node_outcomes_by_run` (the cohort's full per-node evidence,
    # once per eligible run) was only ever a local computation value for
    # `_rank_support` above -- serializing it into leaderboard.json (B1)
    # duplicates evidence already on each model-report.json, once per
    # model row. The adjacent-pair `rank_support` facts computed from it
    # are what consumers actually need, and those are kept.
    for entry in models:
        entry.pop("eligible_node_outcomes_by_run", None)

    unattributed_runs = []
    for _path, report in sorted(unattributed_reports, key=lambda item: item[1]["run_id"]):
        developer = report["developer"]
        unattributed_runs.append({"run_id": report["run_id"], "developer": developer})
        problems.append(
            f"run {report['run_id']}: Developer identity unattributed (harness={developer.get('harness')!r}, "
            f"model={developer.get('model')!r}) -- excluded from model ranking, never discarded "
            "(see unattributed_runs and run_coverage)"
        )

    # Stage 3 (docs/LEADERBOARD-REBUILD-PLAN.md): every distinct
    # measurement.metric_version seen across every discovered report
    # (attributed or not -- this is about the measuring apparatus, not
    # ranking), so a metric-version rebuild of already-graded runs is
    # distinguishable from a genuinely new trial. A report with no
    # size_complexity data at all (graded before Stage 3, or never
    # re-graded since) contributes nothing here -- an honest absence, not an error.
    measurement_metric_versions = sorted(
        {
            report["measurement_metric_version"]
            for _path, report in reports
            if report.get("measurement_metric_version") is not None
        }
    )

    # Stage 4b: reviewer utility/acceptability tables (Tables 3/4) are
    # computed over EVERY discovered report, attributed or not -- a
    # reviewer's own identity is a fact about the reviewer commission, not
    # about whether the Developer it reviewed could be identified.
    reviewers = aggregate_reviewers(reports)

    leaderboard = {
        "models": models,
        "unattributed_runs": unattributed_runs,
        "run_coverage": run_coverage,
        "reviewers": reviewers,
        "measurement_metric_versions": measurement_metric_versions,
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


def _fmt_rating_spread(spread: dict[str, Any] | None) -> str:
    """A PM 0-2 rating spread cell (Stage 4b, docs/LEADERBOARD-REBUILD-PLAN.md)
    -- shared by Table 2's Developer column and Tables 3/4's reviewer
    columns. `None` (no rated attempt/review at all -- PM never judged one,
    or `--run-dir` was never given) renders as an explicit label, never a
    fabricated 0/2: a 0 mean is a real, terrible rating PM actually gave,
    and must stay visually distinct from "nothing to rate at all."
    """
    if not spread:
        return "no PM ratings recorded"
    if spread["n"] == 1:
        return f"{spread['mean']:.1f}/2 (n=1)"
    return f"{spread['mean']:.2f}/2 [{spread['min']:.0f}-{spread['max']:.0f}], n={spread['n']}"


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


def _rank_support_cell(rank_support: dict[str, Any] | None) -> str:
    """Table 1's `Rank support vs previous` cell -- the first row's `None`
    renders `—`; a real diagnostic renders its two facts on separate
    clauses, joined but never merged into one grade (F1's own constraint:
    "never combined into a score, confidence grade or stability number")."""
    if rank_support is None:
        return "—"
    if not rank_support.get("available"):
        return f"unavailable: {rank_support.get('reason', 'not recorded')}"
    if rank_support["robust"]:
        rubric = "Rubric: robust"
    else:
        verb = "ties" if rank_support.get("witness_tied") else "reverses"
        rubric = (
            f"Rubric: not robust (removing {_md_cell(rank_support['witness_node'])} in slice "
            f"{rank_support['witness_slice']} {verb})"
        )
    runs = "Runs: observed ranges overlap" if rank_support["ranges_overlap"] else "Runs: observed ranges do not overlap"
    return f"{rubric}; {runs}"


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
    """Lint/code-health as a hygiene and tool-coverage badge, never a score
    (docs/LEADERBOARD-REBUILD-PLAN.md Stage 3: "Lint survives as a
    hygiene/coverage badge, not a score"). `run_code_health`'s own verdict
    is `"measured"`/`"coverage-gap"` now, never `"pass"` -- health.py emits
    no quality verdict of its own, and exit 0 only means the tool ran and
    produced a payload (Stage 3 fixes the leaderboard evaluation's finding
    2: "'Quality = 1.0' means the measurement tool ran, not the code is
    good"). A finding/candidate count is shown so a reader can see there IS
    coverage, never so the count can be summed into a score.
    """
    parts = []
    for field, tool_label in (("lint_findings_by_tool", "lint"), ("code_health_findings_by_category", "code-health")):
        tool = quality.get(field) or {}
        if not tool.get("available"):
            parts.append(f"{tool_label} unavailable")
            continue
        count = sum((tool.get("counts") or {}).values())
        parts.append(f"{tool_label} {tool.get('verdict', '?')} ({count} finding(s))")
    return ", ".join(parts) if parts else "no quality data"


def _scope_summary(scope: dict[str, Any]) -> str:
    """Scope discipline as an exceptions list, not just a count
    (docs/LEADERBOARD-REBUILD-PLAN.md Stage 3: "Scope violations become an
    exceptions list in run details"). The document-level alert for a
    nonzero count is computed separately, once, in render_markdown
    (_scope_violation_total) -- this only formats one attempt's own list.
    """
    violations = scope.get("violations") or []
    if not violations:
        return "no violations"
    return f"{len(violations)} violation(s): " + ", ".join(_code_span(path) for path in violations)


_LOC_CATEGORY_NAMES = ("code", "docstring", "comment", "blank")


def _production_categories_clause(loc: dict[str, Any]) -> str:
    """F3/F7 (docs/LEADERBOARD-FITNESS-REVIEW-2026-09-15.md): the
    production code/docstring/comment/blank split now stored at
    `loc["production_categories"]`, alongside the physical ΔLOC figure --
    never netted into it, and the reconciliation formula is stated so a
    reader does not assume `physical - code == documentation`.
    `available: false` renders its own recorded reason, never a fabricated
    zero.
    """
    categories = loc.get("production_categories") or {}
    if not categories.get("available"):
        return f"category split unavailable ({categories.get('error', 'not recorded')})"
    net = categories.get("net") or {}
    parts = ", ".join(f"{name} {net.get(name, 0):+d}" for name in _LOC_CATEGORY_NAMES)
    return f"category split (net): {parts} (code + docstring + comment + blank == physical net, by construction)"


def _max_function_cc_clause(production_cc: dict[str, Any]) -> str:
    """F7's max-function-CC figure, beside ΔCC's total -- identifies a
    pathological single function rather than diffuse growth."""
    max_cc = production_cc.get("max_function_cyclomatic") or {}
    baseline, endpoint = max_cc.get("baseline"), max_cc.get("endpoint")
    if baseline is None or endpoint is None:
        return "max function CC unavailable"
    return f"max function CC {baseline}->{endpoint}"


def _endpoint_mean_cc_per_function_clause(production_cc: dict[str, Any]) -> str:
    """Item 4: endpoint mean CC per production function =
    `endpoint_total / function_count.endpoint` -- NOT ΔCC divided by added
    functions, which is only well defined when removals are zero
    (docs/LEADERBOARD-FITNESS-REVIEW-2026-09-15.md). Descriptive only,
    never scored; division by zero (no endpoint functions at all) is a
    named unavailable, never a crash or a fabricated value.
    """
    endpoint_total = production_cc.get("endpoint_total")
    endpoint_function_count = (production_cc.get("function_count") or {}).get("endpoint")
    if endpoint_total is None or not endpoint_function_count:
        return "endpoint mean CC/function unavailable (no endpoint function count)"
    return f"endpoint mean CC/function {endpoint_total / endpoint_function_count:.2f}"


def _size_complexity_summary(size_complexity: dict[str, Any]) -> str:
    """One-line ΔLOC/ΔCC summary for a slice's detail section -- production
    bucket only (test/doc deltas and the full per-bucket detail stay in the
    sheet, not surfaced here); descriptive, never a score
    (docs/LEADERBOARD-REBUILD-PLAN.md Stage 3).

    Extended per docs/LEADERBOARD-FITNESS-REVIEW-2026-09-15.md F7/item4:
    test ΔLOC beside production ΔLOC (never netted together), the
    production code/docstring/comment/blank split, max function CC beside
    ΔCC, and endpoint mean CC per production function.
    """
    loc = (size_complexity or {}).get("loc") or {}
    complexity = (size_complexity or {}).get("complexity") or {}

    if loc.get("available"):
        production = (loc.get("buckets") or {}).get("production") or {}
        test_bucket = (loc.get("buckets") or {}).get("test") or {}
        loc_part = (
            f"ΔLOC (physical lines, including docstrings and blanks) +{production.get('added', 0)}/"
            f"-{production.get('deleted', 0)} (net {production.get('net', 0):+d}); test ΔLOC "
            f"+{test_bucket.get('added', 0)}/-{test_bucket.get('deleted', 0)} "
            f"(net {test_bucket.get('net', 0):+d}, never netted against production). "
            f"{_production_categories_clause(loc)}"
        )
    else:
        # compute_loc_delta records no `error` of its own -- a git failure
        # there aborts grading outright rather than producing an unavailable
        # block -- so the only way to reach this arm is a sheet graded before
        # Stage 3 existed, carrying no size_complexity block at all.
        loc_part = "ΔLOC unavailable (not recorded)"

    if complexity.get("available"):
        production_cc = complexity.get("production") or {}
        cc_part = (
            f"ΔCC net {production_cc.get('net', 0):+d} (descriptive, never scored); "
            f"{_max_function_cc_clause(production_cc)}; {_endpoint_mean_cc_per_function_clause(production_cc)}"
        )
        note = complexity.get("coverage_note")
        if note:
            cc_part += f"; {note}"
    else:
        cc_part = f"ΔCC unavailable ({complexity.get('error', 'not recorded')})" if complexity else "ΔCC unavailable (not recorded)"

    return f"{loc_part}; {cc_part}"


def _per_slice_cells(
    by_slice: dict[int, dict[str, Any] | None],
    formatter: Callable[[dict[str, Any] | None], str],
    *,
    empty_label: str,
) -> str:
    """One table cell holding a per-slice value for every slice, in slice
    order, joined "S1/S2" -- the shape Stage 2's attempts column and Stage
    3's ΔLOC/ΔCC columns both need, parameterised once rather than
    repeated per column (AGENTS.md: "prefer one parameterised script to two
    near-identical ones").

    `empty_label` is used only when the configuration has no slices at all;
    an individual slice with no value is `formatter`'s own business, and
    every formatter here renders that as an explicit unavailable marker
    rather than a fabricated 0.
    """
    return "/".join(formatter(by_slice.get(slice_number)) for slice_number in sorted(by_slice)) or empty_label


def _fmt_net_spread(spread: dict[str, Any] | None) -> str:
    """A ΔLOC/ΔCC net spread cell -- explicit sign (net can be negative:
    the attempt shrank the bucket), unlike `_fmt_count_spread`'s unsigned
    convention (attempts/steers are never negative). None (no available
    measurement for this slice) renders as "unavailable", never a
    fabricated 0 (docs/LEADERBOARD-REBUILD-PLAN.md Stage 3: "A slice with
    no available measurement renders as unavailable, never as 0").
    """
    if not spread:
        return "unavailable"
    if spread["n"] == 1:
        return f"{spread['mean']:+.0f} (n=1)"
    return f"{spread['mean']:+.0f} [{spread['min']:+.0f}-{spread['max']:+.0f}], n={spread['n']}"


def _display_attempt(ordinal: Any) -> Any:
    """Convert a 0-based machine attempt ordinal to the 1-based number a
    human reads (docs/LEADERBOARD-REBUILD-PLAN.md Stage 2's ordinal fix:
    "Machine ordinals stay 0-based everywhere in the sheets and JSON ...
    Convert ordinal + 1 ONLY at the human-display boundary"). This function
    IS that one boundary for every attempt number this renderer prints --
    nothing upstream of it ever adds 1, and nothing here adds 1 twice.
    """
    return ordinal + 1 if isinstance(ordinal, int) else "?"


def _attempt_obligation_mean(entry: dict[str, Any]) -> float | None:
    """One attempt-trajectory row's own obligation-group mean correctness
    -- the same `_mean_obligation_fraction` reduction used everywhere else
    in this tool, never the raw `hidden_tests_passed/total` the trajectory
    table already prints (docs/LEADERBOARD-FITNESS-REVIEW-2026-09-15.md F6:
    "Compute it on the obligation-group mean correctness ... the raw count
    is not the rubric score"). `None` when this row carries no
    `by_obligation` block at all."""
    by_obligation = (entry.get("correctness") or {}).get("by_obligation")
    if not by_obligation:
        return None
    return _mean_obligation_fraction(by_obligation, context="attempt trajectory row")


def _moved_correctness_transitions(trajectory: list[dict[str, Any]]) -> tuple[int, int] | None:
    """`(n, m)`: of this slice's `m` attempt-to-attempt transitions, how
    many `n` moved obligation-group mean correctness at all (F6). `None`
    when there are fewer than two attempts to compare, or when any
    adjacent pair's mean is unavailable on either side (an honest gap, not
    a fabricated 0/0)."""
    if len(trajectory) < 2:
        return None
    means = [_attempt_obligation_mean(entry) for entry in trajectory]
    if any(mean is None for mean in means):
        return None
    moved = sum(1 for earlier, later in zip(means, means[1:], strict=False) if not math.isclose(earlier, later, abs_tol=1e-9))
    return moved, len(means) - 1


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


def _review_order_key(entry: dict[str, Any]) -> tuple[Any, ...]:
    """Sort key for one review-history row: a known `event_index` (now
    populated for every commission harvested under Stage 4a's schema, docs/
    LEADERBOARD-REBUILD-PLAN.md -- see model_report.py's `_review_entry`)
    sorts first and numerically; failing that, a known `at` timestamp sorts
    next -- ISO-8601 `Z`-suffixed strings sort correctly as plain strings,
    so no datetime parsing is needed here. A row with neither sorts last, by
    its own skill, purely for a stable (not meaningful) position. The
    fallback stays reachable, not dead code: a `model-report.json` generated
    before Stage 4a landed can still carry entries with no `event_index` at
    all, and this renderer must still order them sensibly.
    """
    event_index = entry.get("event_index")
    at = entry.get("at")
    at_known = isinstance(at, str) and bool(at)
    skill = entry.get("skill") or ""
    return (event_index is None, event_index if event_index is not None else 0, not at_known, at if at_known else "", skill)


def _review_history_table(reviews: list[dict[str, Any]]) -> list[str]:
    """'Reviews of each attempt -- multiple rows can refer to the same
    submission' (docs/LEADERBOARD-REBUILD-PLAN.md Stage 2): one row per
    review *commission*, not per attempt -- an attempt with two reviews
    (a panel, or a retry) gets two rows here, distinct from the one row it
    gets in the attempt-history table above. A superseded commission (a
    retry's earlier record) is never omitted -- it is marked in its own
    Verdict/extraction-status cell instead, so a retry is never mistaken for
    a second, independent vote (Stage 4a).

    Ordered by the authoritative `events.jsonl` position when known
    (`event_index`, now populated by review_score.py's commission-keyed
    harvest for every record -- Stage 4a), falling back to the recorded
    `at` timestamp otherwise. That fallback is kept reachable rather than
    removed: a `model-report.json` written before Stage 4a landed can still
    reach this renderer, and its entries genuinely have no `event_index`. A
    completion timestamp is not a start time, so a fallback-ordered table is
    explicitly labelled "recorded order", never presented as reconstructed
    execution order.
    """
    rows = list(reviews)
    if not rows:
        return []
    rows.sort(key=_review_order_key)
    any_event_index = any(entry.get("event_index") is not None for entry in rows)
    any_at = any(isinstance(entry.get("at"), str) and entry.get("at") for entry in rows)

    lines = ["Reviews of each attempt -- multiple rows can refer to the same submission.", ""]
    if not any_event_index and not any_at:
        lines.append(
            "_Order-unavailable: none of these reviews carry a recorded time or an events.jsonl position, "
            "so the rows below are NOT sorted by role and must not be read as chronology._"
        )
        lines.append("")
    lines += ["| Event order | Attempt | Recorded time | Role | Reviewer | Verdict / extraction status |", "|---|---|---|---|---|---|"]
    for entry in rows:
        event_index = entry.get("event_index")
        order_cell = str(event_index) if event_index is not None else "unavailable"
        recorded_time = entry.get("at") if isinstance(entry.get("at"), str) and entry.get("at") else "unavailable"
        reviewer = " / ".join(part for part in (entry.get("tool"), entry.get("model")) if part) or "unknown"
        role = entry.get("skill") or "unknown"
        if entry.get("parse_error"):
            status = f"parse error: {_md_cell(entry['parse_error'])}"
        else:
            status = _md_cell(entry.get("verdict") or "?")
        superseded_by = entry.get("superseded_by")
        if superseded_by is not None:
            status += f" (superseded by review at event {superseded_by})"
        lines.append(
            f"| {order_cell} | {_display_attempt(entry.get('attempt'))} | {_md_cell(recorded_time)} | "
            f"{_md_cell(role)} | {_md_cell(reviewer)} | {status} |"
        )
    if any_at and not any_event_index:
        lines += [
            "",
            "_A true `events.jsonl` position is not captured on this report's reviews (generated before Stage "
            "4a); the rows above are ordered by their recorded time instead -- labelled as recorded order, "
            "not reconstructed execution order._",
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
    size_complexity = final_attempt.get("size_complexity") or {}
    lines += [
        f"Lint/code-health (hygiene & tool-coverage badge, never scored): {_quality_summary(quality)}. "
        f"Scope: {_scope_summary(scope)}.",
        f"Production size/complexity (final attempt, vs this slice's own baseline): "
        f"{_size_complexity_summary(size_complexity)}.",
        "",
    ]

    trajectory = slice_entry.get("attempt_trajectory") or []
    moved = _moved_correctness_transitions(trajectory)
    if moved is not None:
        n, m = moved
        lines += [
            (
                f"Attempts that moved measured (obligation-group mean) correctness: {n}/{m}. Not "
                "\"wasted attempts\" -- a steer that fixed a drift finding, contract detail, or review "
                "finding the hidden tests do not cover will not move this figure."
            ),
            "",
        ]

    attempt_lines = _attempt_history_table(trajectory)
    if attempt_lines:
        lines += attempt_lines + [""]

    review_lines = _review_history_table(slice_entry.get("reviews") or [])
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
    lines = [
        f'<a id="{_config_anchor(model)}"></a>',
        "",
        f"## {rank}. {_code_span(model)}",
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


def _total_scope_violations(reports: list[tuple[Path, dict[str, Any]]]) -> int:
    """Total authorized-surface violations across every discovered run's
    first AND final attempt (the only two full attempt blocks a
    model-report.json carries -- `attempt_trajectory` is a compact summary
    without a `scope` field) -- drives render_markdown's top-level scope
    alert (docs/LEADERBOARD-REBUILD-PLAN.md Stage 3: "a top-level alert when
    nonzero").
    """
    total = 0
    for _path, report in reports:
        for slice_entry in report.get("slices") or []:
            for key in ("first_attempt", "final_attempt"):
                attempt = slice_entry.get(key)
                if attempt:
                    total += len((attempt.get("scope") or {}).get("violations") or [])
    return total


def _total_lint_findings(reports: list[tuple[Path, dict[str, Any]]]) -> int | None:
    """Total lint findings across every discovered run's own recorded
    attempts (first and final, model-report.json's only two full attempt
    blocks per slice -- `attempt_trajectory` carries no `quality` field) --
    `None` when the tool was unavailable on every one of those attempts (an
    unavailable linter is never reported as a clean pass,
    F8/docs/LEADERBOARD-FITNESS-REVIEW-2026-09-15.md).

    A single-attempt slice has `first_attempt` and `final_attempt` pointing
    at the same attempt ordinal (A7: naively summing both double-counts it),
    so each `(run_id, slice, attempt_number)` is counted at most once here.
    """
    seen: set[tuple[str, int, int]] = set()
    total = 0
    any_available = False
    for _path, report in reports:
        run_id = report["run_id"]
        for slice_entry in report.get("slices") or []:
            slice_number = slice_entry.get("slice")
            for key in ("first_attempt", "final_attempt"):
                attempt = slice_entry.get(key)
                if not attempt:
                    continue
                attempt_key = (run_id, slice_number, attempt.get("attempt"))
                if attempt_key in seen:
                    continue
                seen.add(attempt_key)
                tool = ((attempt.get("quality") or {}).get("lint_findings_by_tool")) or {}
                if tool.get("available"):
                    any_available = True
                    total += sum((tool.get("counts") or {}).values())
    return total if any_available else None


def _cc_ranges_overlap_across_models(models: list[dict[str, Any]]) -> bool | None:
    """Whether every pair of configurations' final-attempt ΔCC ranges
    overlap, for every slice both sides have data on -- F8's between-model
    ΔCC comparison caveat. `None` when fewer than two configurations carry
    any ΔCC data at all to compare."""
    spreads_by_model = [model["final_cc_by_slice"] for model in models]
    comparable_pairs = 0
    for i in range(len(spreads_by_model)):
        for j in range(i + 1, len(spreads_by_model)):
            for slice_number in set(spreads_by_model[i]) & set(spreads_by_model[j]):
                a, b = spreads_by_model[i].get(slice_number), spreads_by_model[j].get(slice_number)
                if not a or not b:
                    continue
                comparable_pairs += 1
                if not (a["min"] <= b["max"] and b["min"] <= a["max"]):
                    return False
    return True if comparable_pairs else None


def _has_eligible_comparison(rows: list[dict[str, Any]]) -> bool:
    """Whether ANY of the given reviewer rows has at least one eligible
    (N>1) comparison round. `comparative_score is None` is exactly
    "zero eligible rounds for this identity" (aggregate_reviewers' own
    docstring), so checking it across the rows a table or the glossary is
    about to render is a live fact about that render -- never a hardcoded
    claim about the cohort's shape that can go stale the way "every panel
    is a singleton" already did once, when a real multi-model panel was
    commissioned for the first time.
    """
    return any(row["comparative_score"] is not None for row in rows)


def _panel_shape_note(rows: list[dict[str, Any]]) -> str:
    """The paragraph explaining what code-review's panels actually look like,
    derived from the rows being rendered via `_has_eligible_comparison` and
    never hardcoded -- so it cannot again assert a cohort shape ("every
    panel is a singleton") that a later trial silently falsifies, which is
    exactly what happened the first time a real multi-model panel ran.

    Code-review is the only role this applies to, so the role is named
    literally rather than parameterised: Table 4 deliberately has no
    comparative column (drift-audit is never ranked against other
    reviewers, whatever its panel size -- see `_comparative_score_cell`),
    so panel shape has no bearing on anything a reader sees there and
    stating it would only invite them to look for a column that does not
    exist by design. Should drift-audit ever gain such a column, give this
    a `role` then -- not before.

    Two cases, both read off `rows` rather than assumed:

    - No row has an eligible (N>1) round: every code-review panel is a
      singleton today. Said plainly as the role's real shape -- not a
      defect, not an empty table -- with the column's literal cell text
      quoted so a reader never reads it as a bug.
    - At least one row has an eligible round: real multi-model panels
      exist. A row without one of its own still reads "single reviewer",
      and that stays a true, unremarkable property of that row.
    """
    if not _has_eligible_comparison(rows):
        return (
            "**Every code-review panel in this cohort is a singleton** -- this is the role's real shape today, "
            'never a defect or an artifact of an empty table, so the comparative column reads "single '
            'reviewer -- no comparative score" for every row below; that reviews DID occur is shown by the '
            "PM rating and round columns."
        )
    observed_sizes = sorted({size for row in rows for size in row["panel_sizes"] if size > 1})
    sizes_clause = (
        f" Observed multi-model panel sizes: {', '.join(str(size) for size in observed_sizes)}."
        if observed_sizes
        else ""
    )
    return (
        "**This cohort includes real multi-model code-review panels**, so the comparative column below carries "
        f"genuine comparative rank scores for the rows that appeared in one.{sizes_clause} A row with no "
        'eligible round of its own still reads "single reviewer -- no comparative score" -- a real property '
        "of that row, not a gap; that reviews DID occur regardless is shown by the PM rating and round "
        "columns."
    )


def _comparative_score_cell(row: dict[str, Any]) -> str:
    """The comparative-rank-score cell shared by Table 3's own column
    (Table 4 has no such column -- drift-audit's acceptability table never
    ranks reviewers against each other, only against PM's 0-2 rating scale).

    `comparative_score is None` covers BOTH "this reviewer never appeared
    in any panel at all" and "every panel it appeared in was a singleton"
    -- the plan is explicit these read identically: *"single reviewer -- no
    comparative score"*, with the surrounding table's own prose explaining
    that reviews did occur. This is deliberately not distinguished further
    (a reviewer with zero comparisons at all versus one with only singleton
    ones) since neither produces a comparable number either way.
    """
    if row["comparative_score"] is None:
        return "single reviewer -- no comparative score"
    spread = row["comparative_score"]
    if spread["n"] == 1:
        cell = f"{spread['mean']:.2f} (n=1 run)"
    else:
        cell = f"{spread['mean']:.2f} [{spread['min']:.2f}-{spread['max']:.2f}], n={spread['n']} runs"
    if row.get("comparative_globally_comparable") is False:
        # docs/LEADERBOARD-REBUILD-PLAN.md Stage 4b: "mark disconnected
        # comparison groups as not globally comparable" -- this reviewer's
        # points were earned entirely against a different set of opponents
        # than at least one other reviewer's, so the two numbers are not on
        # the same scale.
        cell += " (comparable only within its own opponent group -- see note)"
    return cell


def _reviewer_utility_table(reviewers: dict[str, list[dict[str, Any]]], skill: str) -> list[str]:
    """Table 3 -- 'Code reviewer -- PM-assessed utility' (docs/
    LEADERBOARD-REBUILD-PLAN.md Stage 4b). One row per reviewer
    configuration that ran ANY `code-review` commission -- PM's own rating
    (never blended with the comparative score; the two differ in
    repeatability the same way `pm_subjective_rating` differs from the
    deterministic scores elsewhere in this document).
    """
    rows = reviewers.get(skill) or []
    lines = ["## Code reviewer -- PM-assessed utility", ""]
    if not rows:
        lines += ["_No `code-review` commissions recorded in this cohort._", ""]
        return lines
    any_globally_comparable_false = any(row.get("comparative_globally_comparable") is False for row in rows)
    lines += [
        (
            "PM assesses every code-review report it reads, both a 0-2 rating of the report itself and, "
            "separately, a comparison against any other reviewer(s) commissioned for the same submission. "
            f"{_panel_shape_note(rows)}"
        ),
        "",
        (
            "| Reviewer configuration | PM rating (mean /2, n) | Comparative rank score | Rounds / distinct "
            "runs | Observed panel sizes |"
        ),
        "|---|---|---|---|---|",
    ]
    for row in rows:
        reliability_note = f" (+{row['unavailable_count']} unavailable)" if row["unavailable_count"] else ""
        panel_sizes = ", ".join(str(n) for n in row["panel_sizes"]) if row["panel_sizes"] else "none observed"
        lines.append(
            f"| {_code_span(row['label'])} | {_fmt_rating_spread(row['rating'])}{reliability_note} | "
            f"{_comparative_score_cell(row)} | {row['rounds']}/{row['distinct_runs']} | {panel_sizes} |"
        )
    if any_globally_comparable_false:
        lines += [
            "",
            (
                "_Some rows' comparative scores were earned entirely against a different set of opponents "
                "than other rows' -- normalized rank points are only comparable within the same connected "
                "group of reviewers who have actually faced each other, never across groups that never have._"
            ),
        ]
    lines.append("")
    return lines


def _reviewer_acceptability_table(reviewers: dict[str, list[dict[str, Any]]], skill: str) -> list[str]:
    """Table 4 -- 'Drift reviewer -- PM-assessed acceptability' (docs/
    LEADERBOARD-REBUILD-PLAN.md Stage 4b). No comparative column at all --
    drift-audit's job is to catch real authorization violations, not to be
    ranked against other reviewers, and a FAIL verdict is never translated
    into a poor rating (finding a real violation is good reviewing; that
    translation would happen entirely inside PM's own rating, never here).

    `unacceptable / assessed` is shown alongside the mean specifically
    because a mean alone can conceal a catastrophic 0 among 2s -- the
    plan's own stated reason this column exists.
    """
    rows = reviewers.get(skill) or []
    lines = ["## Drift reviewer -- PM-assessed acceptability", ""]
    if not rows:
        lines += ["_No `drift-audit` commissions recorded in this cohort._", ""]
        return lines
    lines += [
        (
            "PM rates each drift-audit report 0-2 on whether its authorization verdict was itself "
            "acceptable work. **A drift `FAIL` is never a poor rating -- finding a real violation is good "
            "reviewing**, so a reviewer that blocks often can still sit at 2.00 here. `Unacceptable / "
            "assessed` is shown beside the mean because a mean alone can conceal a single catastrophic 0 "
            "among 2s, and a report PM could not rate at all (timed out, or unreadable) is counted "
            "separately as `unavailable` rather than folded in as a 0. Nothing in this table enters any "
            "Developer number."
        ),
        "",
        (
            "| Reviewer configuration | PM rating (mean /2, n) | Unacceptable / assessed | Distinct runs |"
        ),
        "|---|---|---|---|",
    ]
    for row in rows:
        reliability_note = f" (+{row['unavailable_count']} unavailable)" if row["unavailable_count"] else ""
        lines.append(
            f"| {_code_span(row['label'])} | {_fmt_rating_spread(row['rating'])}{reliability_note} | "
            f"{row['unacceptable_count']}/{row['rated_count']} | {row['distinct_runs']} |"
        )
    lines.append("")
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
    scope_violation_total = _total_scope_violations(reports)
    reviewers = leaderboard["reviewers"]

    lines = [
        "# Leaderboard",
        "",
        (
            "First-submission ability and supervised outcomes for the frozen two-slice task. Higher "
            "correctness is better; smaller edits and shorter elapsed time are supporting measures."
        ),
        "",
    ]
    if scope_violation_total:
        # Top-level alert (docs/LEADERBOARD-REBUILD-PLAN.md Stage 3: "Scope
        # violations become an exceptions list in run details, with a
        # top-level alert when nonzero") -- the exact paths live in each
        # affected run's own slice detail (_scope_summary), not repeated
        # here.
        lines += [
            (
                f"**Scope alert: {scope_violation_total} authorized-surface violation(s) recorded across this "
                "cohort's runs -- see each affected run's slice detail below for the exact paths.**"
            ),
            "",
        ]
    lines += [
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
            "- **Physical ΔLOC** -- net physical lines added to production source (`src/**/*.py`) between "
            "a slice's own baseline commit and the attempt's commit (`git diff --numstat --no-renames`, "
            "added minus deleted; test/doc paths are classified and counted separately and never netted "
            "against production). Physical lines, never SLOC-excluding-comments -- the two definitions are "
            "never mixed (`policy.yaml`'s `measurement.loc_definition`)."
        ),
        (
            "- **Code ΔLOC** -- the `code` category of physical ΔLOC's own code/docstring/comment/blank "
            "decomposition (`policy.yaml`'s `measurement.loc_category_definition`): physical ΔLOC minus "
            "documentation and blank-line churn. Both figures are descriptive, never a ranking criterion "
            "and never framed as smaller-is-better -- a larger or smaller net change is not itself better "
            "or worse code (docs/LEADERBOARD-FITNESS-REVIEW-2026-09-15.md: physical ΔLOC alone is "
            "misleading as the headline production-size figure, which is why code ΔLOC is now surfaced "
            "alongside it rather than left to per-run detail alone)."
        ),
        (
            "- **ΔCC** -- total production function cyclomatic complexity, endpoint minus baseline (summed "
            "over every function `health.py`'s absolute `analyze --all` finds at each revision, never the "
            "capped, display-only `candidates` list). Descriptive only -- splitting one function into three "
            "raises it through added function-entry counts alone -- and never scored."
        ),
        (
            "- A slice with no available ΔLOC/ΔCC measurement renders as `unavailable`, never as a "
            "fabricated `0`. A slice flagged with a grading-baseline reset (a stop/restart mid-run) has its "
            "first-to-final size/complexity comparison named as unreliable in that run's own Problems entry "
            "-- correctness is unaffected."
        ),
        (
            "- **PM Developer rating (mean /2, n)** -- PM's own 0-2 rating of individual Developer "
            "submissions (`developer_judgments`, Stage 4b), flattened across every rated attempt of every "
            "discovered run for a configuration. PM's judgement, shown alongside the deterministic columns, "
            "never blended into any of them -- the same separation `pm_subjective_rating` already gets."
        ),
        (
            "- **PM rating (mean /2, n)** (Tables 3/4) -- PM's own 0-2 rating of individual review reports "
            "(`review_judgments`' rating shape, Stage 4b), per reviewer configuration. A review PM could not "
            "rate at all (a timed-out or unreadable report) is an explicit reliability outcome, counted "
            "separately, never blended into this mean as a 0."
        ),
        (
            "- **Comparative rank score** (Table 3 only) -- PM's own panel comparisons (`review_judgments`' "
            "comparison shape), normalized to `(N-r)/(N-1)` for a panel of size N and 1-based rank r (ties "
            "share the mean occupied rank); N=1 has no comparative score at all, never a fabricated 1.0. "
            "Averaged within a run first, then across runs. "
            f"{_panel_shape_note(reviewers.get('code-review') or [])}"
        ),
        "",
        "## Developer -- first submission",
        "",
        (
            "**Rank orders the observed configuration means only and does not claim statistical "
            "separation.** `Rank support vs previous` carries two separately-named categorical facts "
            "about each row versus the row directly above it, never combined into a score, confidence "
            "grade or stability number: **Rubric** varies one hidden-test node at a time, holding every "
            "run fixed, and asks whether the row above still strictly beats this row after every such "
            "single-node removal (leave-one-node-out); **Runs** compares the two rows' observed "
            "first-attempt min-max ranges at n=2-3 and is **not** a confidence interval. The two "
            "statements are never combined into one joint grade. (A proposal to collapse near-equal "
            "rows into shared ranks using the rubric's own single-heaviest-test resolution was "
            "considered and rejected -- see docs/LEADERBOARD-FITNESS-REVIEW-2026-09-15.md F1: it is a "
            "worst-case single-node bound, a heavy node both rows pass contributes no uncertainty yet "
            "would still suppress the ranking, and \"within the band\" is not an equivalence relation.)"
        ),
        "",
        (
            "| Rank by observed mean | Developer configuration | Correctness [min-max] | Code ΔLOC S1/S2 | "
            "Physical ΔLOC S1/S2 | ΔCC S1/S2 | Rank support vs previous | Runs (eligible/discovered) |"
        ),
        "|---|---|---|---|---|---|---|---|",
    ]
    for rank, entry in enumerate(leaderboard["models"], start=1):
        first_code_loc_cells = _per_slice_cells(
            entry["first_code_loc_by_slice"], _fmt_net_spread, empty_label="unavailable"
        )
        first_loc_cells = _per_slice_cells(entry["first_loc_by_slice"], _fmt_net_spread, empty_label="unavailable")
        first_cc_cells = _per_slice_cells(entry["first_cc_by_slice"], _fmt_net_spread, empty_label="unavailable")
        lines.append(
            f"| {rank} | [{_code_span(entry['model'])}](#{_config_anchor(entry['model'])}) | "
            f"{_fmt_pct_spread(entry['first_attempt_correctness'], no_data_label='no eligible runs')} | "
            f"{first_code_loc_cells} | {first_loc_cells} | {first_cc_cells} | "
            f"{_rank_support_cell(entry.get('rank_support'))} | {_runs_cell(entry)} |"
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
        (
            "**`Attempts` and `Steers` measure supervision cost, not the source of `Gain` -- gain is "
            "measured only by hidden tests, so a steer that fixed something the hidden tests do not cover "
            "will not appear in it** (docs/LEADERBOARD-FITNESS-REVIEW-2026-09-15.md F6). See each run's own "
            "slice detail below for how many of its attempt-to-attempt transitions actually moved measured "
            "correctness."
        ),
        "",
        (
            "| Rank | Developer configuration | Final correctness [min-max] | Gain (pp) | Final code ΔLOC "
            "S1/S2 | Final physical ΔLOC S1/S2 | Final ΔCC S1/S2 | Attempts S1/S2 | Steers | PM elapsed | "
            "PM Developer rating (mean /2, n) | Completed/total |"
        ),
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for rank, entry in enumerate(leaderboard["models"], start=1):
        attempts_cells = _per_slice_cells(entry["attempts_by_slice"], _fmt_count_spread, empty_label="--")
        final_code_loc_cells = _per_slice_cells(
            entry["final_code_loc_by_slice"], _fmt_net_spread, empty_label="unavailable"
        )
        final_loc_cells = _per_slice_cells(entry["final_loc_by_slice"], _fmt_net_spread, empty_label="unavailable")
        final_cc_cells = _per_slice_cells(entry["final_cc_by_slice"], _fmt_net_spread, empty_label="unavailable")
        lines.append(
            f"| {rank} | {_code_span(entry['model'])} | "
            f"{_fmt_pct_spread(entry['final_attempt_correctness'], no_data_label='no data')} | "
            f"{_fmt_pp_spread(entry['gain_pp'])} | {final_code_loc_cells} | {final_loc_cells} | {final_cc_cells} | "
            f"{attempts_cells} | {_fmt_count_spread(entry['steers'])} | "
            f"{_fmt_elapsed_spread(entry['pm_elapsed_seconds'])} | "
            f"{_fmt_rating_spread(entry['pm_developer_rating'])} | {entry['completed_runs']}/{entry['run_count']} |"
        )

    lint_total = _total_lint_findings(reports)
    scope_total = _total_scope_violations(reports)
    cc_overlap = _cc_ranges_overlap_across_models(leaderboard["models"])
    lint_clause = f"{lint_total} lint finding(s)" if lint_total is not None else "lint unavailable on every attempt"
    # _cc_ranges_overlap_across_models is True only when EVERY comparable pair
    # overlaps, so False means "at least one pair does not" -- never "no pair
    # does". The wording has to carry that asymmetry, or a reader takes the
    # negative branch as the much stronger claim that the ranges are cleanly
    # separated everywhere.
    overlap_clause = (
        "this cohort's final-attempt ΔCC ranges overlap between every pair of configurations that has data "
        "to compare, so between-model comparison is not supported at this n"
        if cc_overlap
        else "at least one pair of configurations' final-attempt ΔCC ranges does not overlap, so the ranges "
        "alone do not rule out a between-model difference for that pair -- see each row's own ΔCC spread, "
        "and note ΔCC is descriptive and never scored"
        if cc_overlap is False
        else "too little ΔCC data in this cohort to compare configurations' ranges"
    )
    lines += [
        "",
        (
            "**Conformance (F8): lint findings and scope violations are conformance checks, not "
            "comparisons -- a 0 there is a measured pass, not missing data. Max function CC is a "
            "descriptive maintainability signal only: policy.yaml defines no threshold for it, so "
            "nothing here can pass or fail it.** "
            f"Across this cohort's first and final attempts, {lint_clause} and {scope_total} scope "
            f"violation(s) were recorded; see each attempt's own quality/scope summary and "
            f"max-function-CC figure above for detail. Separately, {overlap_clause}."
        ),
        "",
    ]
    lines += _reviewer_utility_table(leaderboard["reviewers"], "code-review")
    lines += [""]
    lines += _reviewer_acceptability_table(leaderboard["reviewers"], "drift-audit")
    lines += [
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
            "it entirely) -- correctness ranks configurations on its own; ΔLOC/ΔCC (Stage 3) are supporting "
            "columns, and PM's own judgments (Stage 4b) are supporting columns/tables too -- neither is ever "
            "blended into a score."
        ),
        (
            f"Measurement metric_version: {', '.join(str(v) for v in leaderboard.get('measurement_metric_versions') or []) or 'none recorded'}"
            " -- a change here means production-size-and-complexity's own definition (policy.yaml's "
            "`measurement` section) was rebuilt, not that a new trial ran; more than one value listed means "
            "this generation mixes runs graded under different measurement definitions."
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
