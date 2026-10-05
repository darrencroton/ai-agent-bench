#!/usr/bin/env python3
"""The cross-model leaderboard, folded from every model_report.py report on
disk.

Reads every `model-report.json` under `results/runs/*/`, partitions them by
their own top-level `task_id` -- a structural fact stamped at grading time,
or backfilled to `untagged_sheet_task` by model_report.py for sheets graded without
one and marked `task_id_source: "backfilled"` there -- then, WITHIN each
task partition, groups reports by
Developer configuration (`developer.configuration_key` -- a configuration
can have several runs on disk; see policy.yaml's `repeats`) and ranks
configurations by **mean first-attempt correctness**: the equally-weighted
mean of a slice's obligation-group `fraction`s on its FIRST (ordinal-0)
attempt, averaged equally across a run's slices, then averaged equally
across a configuration's *eligible* runs
(`run_coverage`/`eligible_for_first_submission`, below). Each task gets its
own complete Developer "first submission"/"supervised outcome" table pair,
labelled with its task id; one task's numbers never enter another task's
tables anywhere in this tool. The reviewer tables (`aggregate_reviewers`,
below) are scoped the same way: built once per task partition from that
partition's reports only, so a reviewer identity reviewing under two tasks
gets an independent PM-rating mean and comparative-rank score per task, and
its opponent-group connectivity is computed within one task's rounds only,
and within one skill's rounds only, never bridging two tasks' or two roles'
otherwise-disconnected groups into one falsely-comparable component.

The document also carries ONE derived cross-task section
(`compute_cross_task_standing`, below): each Developer configuration's
percentile rank of first-attempt correctness WITHIN each task's own field,
averaged equally across the contributing tasks -- and the same, separately,
for reviewer comparative-rank-score means (`code-review` and `drift-audit`
in their own tables), restricted to the tasks where the identity's own
`comparative_globally_comparable` flag is true. It is computed strictly
after every task's own tables are final, reads only from them, and feeds
back into none of them: a derived, never-authoritative-on-its-own standing
measure.

There is no composite score. Correctness is the primary ranking; mean
first-attempt test kill rate (dev_check.py's mutation gate over the
Developer's own test suite) is a second, independent ranking column
(`kill_rate_rank`) with its own parallel cross-task standing, never combined
with correctness; ΔLOC/ΔCC and PM's own judgments (reviewer PM-ratings/comparisons and the
Developer PM-rating column, `aggregate_reviewers`/`_reviewer_utility_table`/
`_reviewer_acceptability_table` below) are supporting columns/tables, never
folded into a score. Every remaining number here is a direct, documented
reduction of fields `dev_check.py`/`review_score.py`/`model_report.py`
already computed; the only arithmetic this tool adds is the mean/min/max/n
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
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, Callable

import yaml

import bench_lib
import quality_panel

# The two quality-tool fields on an attempt's `quality` block
# (dev_check.py's run_lint/run_code_health, reshaped verbatim by
# model_report.py) -- used only by compute_run_coverage's per-run
# availability report, never by any ranking computation (quality is not
# scored at all).
_QUALITY_FIELDS = ("lint_findings_by_tool", "code_health_findings_by_category")

# `task_id` is required, never defaulted: a report without it cannot be
# partitioned, and silently assigning it to some existing task would blend
# unknown data into that task's ranking. model_report.py stamps it on every
# report it writes (backfilling sheets graded without one to `untagged_sheet_task`,
# marked `task_id_source: "backfilled"`), so a missing value means a stale or
# hand-edited report, which must be regenerated, not guessed around.
_REQUIRED_REPORT_KEYS = ("run_id", "task_id", "developer", "run_status", "timing", "provenance", "slices", "pm_subjective_rating")

# The rubric a slice's correctness was graded under, as model_report.py's
# resolve_correctness_provenance writes it onto each slice entry. Ranked
# reports must agree on all three per slice number, or their correctness
# scores are not comparable and must not be averaged together.
_CORRECTNESS_PROVENANCE_KEYS = ("plan_hash", "obligations_hash", "hidden_tests_hash")

# The structured identity block (bench_lib.resolve_developer_identity,
# reshaped through unchanged by model_report.build_report) -- discover_reports
# validates the block's own shape, not merely that a `model` key exists, so
# a report with no real identity cannot parse as valid without a `developer`
# block naming one.
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
    """Load policy.yaml as a mapping, checking only that it parses to one.

    This tool reads no flat tunable of its own: build_leaderboard resolves
    each report's task through `bench_lib.resolve_task`, which validates the
    task registry and supplies that task's `expected_slices`.

    Raises:
        LeaderboardError: the file is missing or does not parse to a mapping.
    """
    if not policy_path.is_file():
        raise LeaderboardError(f"policy file not found: {policy_path}")
    with policy_path.open("r", encoding="utf-8") as handle:
        policy = yaml.safe_load(handle)
    if not isinstance(policy, dict):
        raise LeaderboardError(f"policy file {policy_path} did not parse to a mapping")
    return policy


# --- discovery -------------------------------------------------------------


def default_runs_root(root: Path) -> Path:
    """Where model_report.py writes every run's report. Hardcoded rather than
    read from policy.yaml, matching model_report.py's own default_sheets_dir."""
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
    """Every `model-report.json` one level under `runs_root` (the
    `results/runs/<run_id>/` layout model_report.py writes), sorted by path
    for determinism.

    Raises:
        LeaderboardError: no report found anywhere; one found fails to parse,
            is missing a required top-level key, or carries a malformed
            `task_id`/`developer` block; or two reports carry the same
            `run_id` (they would otherwise collapse silently into one entry in
            aggregate_model's per-run grouping).
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
        task_id = report.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            raise LeaderboardError(
                f"model-report.json at {path}'s task_id must be a non-empty string, got {task_id!r}"
            )
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
    """The given reports, grouped by their own `developer.configuration_key`
    -- a configuration can have several runs on disk (policy.yaml's
    `repeats`). Does not filter on `attributed`: build_leaderboard passes
    attributed reports only."""
    groups: dict[str, list[tuple[Path, dict[str, Any]]]] = {}
    for path, report in reports:
        groups.setdefault(report["developer"]["configuration_key"], []).append((path, report))
    return groups


def partition_reports_by_task(reports: list[tuple[Path, dict[str, Any]]]) -> dict[str, list[tuple[Path, dict[str, Any]]]]:
    """Every discovered report, grouped by its own top-level `task_id` --
    the single boundary between tasks in this tool.

    build_leaderboard runs the entire aggregation pipeline
    (group_reports_by_model / aggregate_model /
    _check_correctness_provenance_consistency) once per returned partition,
    never across partitions, so one task's numbers can never be averaged
    into another's. The task_id is read as recorded, never re-derived."""
    partitions: dict[str, list[tuple[Path, dict[str, Any]]]] = {}
    for path, report in reports:
        partitions.setdefault(report["task_id"], []).append((path, report))
    return partitions


# --- coverage/eligibility ------------------------------------------------


def compute_run_coverage(report: dict[str, Any], expected_slices: int) -> dict[str, Any]:
    """One run's coverage/eligibility summary.

    Recorded for **every** discovered run, attributed or not -- this is
    what lets an unattributed run stay fully visible (never discarded) even
    though it is excluded from model ranking.

    Eligibility for first-submission ranking requires all four of: identity
    attributed, PM status `complete`, every expected slice graded, and each
    graded slice carrying a real attempt-0 row. A slice whose commit history
    doesn't satisfy the grader's one-commit-per-attempt walk can
    legitimately hold only its final attempt's row -- its attempt-0 is
    genuinely absent, never substituted with whatever attempt is present, so
    such a run is marked ineligible with a named reason rather than ranked
    on the wrong attempt.

    Args:
        expected_slices: how many slices this report's own task expects
            (from its registry entry, never a global value -- two tasks may
            have different frozen plans).
    """
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
    (supervised-outcome) correctness.

    Raises:
        LeaderboardError: `by_obligation` is malformed (missing/wrong-typed
            `fraction`) or empty -- named with `context`, the caller's
            description of which configuration, run, slice and attempt this is.
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
    `size_complexity` block, or None when the attempt is absent or the
    measurement itself is recorded unavailable -- never a fabricated 0."""
    if not attempt:
        return None
    loc = (attempt.get("size_complexity") or {}).get("loc") or {}
    if not loc.get("available"):
        return None
    return ((loc.get("buckets") or {}).get("production") or {}).get("net")


def _production_code_loc_net(attempt: dict[str, Any] | None) -> float | None:
    """The production bucket's net ΔLOC restricted to the `code` category
    of `size_complexity.loc.production_categories` -- physical ΔLOC minus
    docstring/comment/blank churn, since physical ΔLOC alone is inflated by
    documentation and can misrepresent production size on its own. Same
    availability contract as `_production_loc_net`: None when the attempt
    or the category split is absent or recorded unavailable, never a
    fabricated 0."""
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


def _production_max_function_cc_endpoint(attempt: dict[str, Any] | None) -> float | None:
    """The largest single production function's cyclomatic complexity AT
    THIS ATTEMPT'S ENDPOINT (`size_complexity.complexity.production.
    max_function_cyclomatic.endpoint`) -- a LEVEL, not a delta: it
    identifies a pathological single function rather than diffuse growth
    across many functions (`_max_function_cc_clause` renders the
    baseline->endpoint pair in per-slice detail). Same availability contract
    as `_production_cc_net`: None when the attempt is absent,
    `complexity.available` is false, or the value itself is absent -- never
    a fabricated 0.

    `policy.yaml` defines no threshold for this figure, so it is descriptive
    only and nothing can pass or fail it.
    """
    if not attempt:
        return None
    complexity = (attempt.get("size_complexity") or {}).get("complexity") or {}
    if not complexity.get("available"):
        return None
    max_cc = (complexity.get("production") or {}).get("max_function_cyclomatic") or {}
    return max_cc.get("endpoint")


def _narration_lines(attempt: dict[str, Any] | None) -> float | None:
    """One attempt's `hygiene.production.narration_lines`
    (dev_check.measure_hygiene), or None when the block is unavailable or
    absent -- a sheet graded before the census existed has none, and that is
    never read as zero narration. Descriptive only, never scored."""
    block = (attempt or {}).get("hygiene") or {}
    if not block.get("available"):
        return None
    return (block.get("production") or {}).get("narration_lines")


# The per-slice measurement series `aggregate_model` accumulates, each as
# (series name, extractor) -- driving one shared accumulation loop instead of
# a hand-copied accumulator/setdefault/append/spread block per series
# (AGENTS.md: "prefer one parameterised script to two near-identical ones").
# First-attempt series are collected only for eligible runs; final-attempt
# series for every discovered run (see aggregate_model's own docstring for
# why). `max_fn_cc` and `narration` are FINAL-attempt only -- the
# first-submission table never renders them, so no first-attempt copy is
# collected.
_FIRST_ATTEMPT_SERIES: tuple[tuple[str, Callable[[dict[str, Any] | None], float | None]], ...] = (
    ("loc", _production_loc_net),
    ("code_loc", _production_code_loc_net),
    ("cc", _production_cc_net),
)
_FINAL_ATTEMPT_SERIES: tuple[tuple[str, Callable[[dict[str, Any] | None], float | None]], ...] = _FIRST_ATTEMPT_SERIES + (
    ("max_fn_cc", _production_max_function_cc_endpoint),
    ("narration", _narration_lines),
)


def _kill_rate(attempt: dict[str, Any] | None) -> float | None:
    """One attempt's `test_kill_rate.kill_rate` (dev_check.measure_test_kill_rate),
    or None when the block is unavailable or absent -- a sheet graded before
    the measurement existed has none, and that is never read as 0.0."""
    block = (attempt or {}).get("test_kill_rate") or {}
    return block["kill_rate"] if block.get("available") else None


def _spread(values: list[float]) -> dict[str, Any] | None:
    """The 'mean [min-max], n' convention used throughout this document's
    tables. No variance in squared units, no confidence intervals; at n=1,
    the value is shown with n=1, never a zero spread. Returns None for an
    empty population -- absence of data, which every caller renders as "no
    eligible/available data for this cell", never as 0.
    """
    if not values:
        return None
    return {"mean": sum(values) / len(values), "min": min(values), "max": max(values), "n": len(values)}


# --- rank-support diagnostic ----------------------------------------------
#
# Two separately-named categorical facts about one adjacent pair in the
# final ranking, never combined into a score, confidence grade or
# stability number. A shared-rank/tie-band scheme is deliberately not used:
# a fixed threshold on score difference is not an equivalence relation and
# can yield ambiguous, non-unique rank groupings (the first-submission
# table's prose in _developer_task_section gives the rendered explanation).
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
    rather than dividing by zero.

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
    (slice, node) pair excised from its own slice's own denominator.

    The full scoring hierarchy is repeated per run and per slice: recompute
    the affected slice's group-fraction mean, average equally across the
    run's slices, then average equally across the configuration's eligible
    runs. Subtracting a nominal node weight from the already-aggregated mean
    instead gives the wrong answer, silently, under non-uniform group sizes
    and unequal run counts.

    Raises:
        LeaderboardError: an eligible run has no stored
            `first_attempt_node_outcomes` for some slice -- eligibility
            guarantees a first-attempt row exists, so a missing map means it
            was never persisted, and must stop the computation rather than
            be skipped.
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
            `first_attempt_node_outcomes` map. Skipping it instead would let
            a universe built from *no* eligible evidence be reported
            `robust: true` by `_rank_support`, a verdict from zero
            comparisons.
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
    correctness, paired-run gain, attempts/steers/floor-failures/nudges/
    elapsed-time supporting columns, and PM's own subjective ratings carried
    through verbatim.

    Ranking basis: per slice, the equally-weighted mean of obligation-group
    fractions on the FIRST (ordinal-0) attempt; averaged equally across a
    run's slices; then averaged equally across the configuration's
    *eligible* runs only (`run_coverage[run_id]["eligible_for_first_submission"]`)
    -- `first_attempt_correctness["n"]` is therefore the eligible run count,
    never the discovered run count. A run ineligible for first-submission
    ranking (incomplete coverage, no attempt-0 row, etc.) contributes
    nothing to `first_attempt_correctness`/`gain_pp` but still contributes
    to every other column (final correctness, attempts, steers, elapsed
    time, PM ratings) -- those don't need an attempt-0 row to be
    meaningful.

    `first_attempt_kill_rate` is the same shape over the FIRST attempt's test
    kill rate (`test_kill_rate.kill_rate`): per run, the mean across slices,
    then `_spread` across runs -- but a run counts only when it is eligible
    for first-submission ranking AND every one of its slices has an available
    first-attempt kill rate, so its `n` can be smaller than correctness's. A
    run with any unavailable slice contributes nothing, never a 0.
    `final_attempt_kill_rate` is the same over every run's final attempts.
    Neither is ever combined with correctness.

    `gain_pp` (percentage points) is computed **within each paired run
    first, then summarised** -- never as a difference of two independently
    summarised endpoints. A run is "paired" when it is eligible for
    first-submission ranking AND has final-attempt correctness for every
    one of the same slices; an eligible run whose final attempt is missing
    for a slice (a genuine, named problem, see below) is excluded from
    `gain_pp` rather than silently paired against partial data.

    Raises:
        LeaderboardError: a run `run_coverage` marks
            `eligible_for_first_submission` has no first-attempt
            correctness data in its report for some slice -- eligibility
            guarantees it, so this is a bug in this tool, not a soft data
            gap to paper over.
    """
    problems: list[str] = []
    reports_by_run_id = {report["run_id"]: report for _path, report in model_reports}
    run_ids = sorted(reports_by_run_id)

    first_attempt_run_means: list[float] = []
    first_kill_rate_run_means: list[float] = []
    final_kill_rate_run_means: list[float] = []
    eligible_run_ids: list[str] = []
    final_attempt_run_means: list[float] = []
    gain_values_pp: list[float] = []
    attempts_by_slice: dict[int, list[int]] = {}
    steers_per_run: list[int] = []
    # model_report.resolve_run_process's per-run counts; a run whose report
    # has no available `process` block contributes nothing, never a 0.
    floor_failures_per_run: list[float] = []
    nudges_per_run: list[float] = []
    elapsed_seconds_values: list[float] = []
    pm_status_counts: dict[str, int] = {}
    pm_subjective_ratings: list[dict[str, Any]] = []
    # PM's own 0-2 rating of each Developer SUBMISSION (`attempt_trajectory`'s
    # `pm_developer_judgment`, model_report.resolve_pm_judgments), flattened
    # across every attempt of every run for this configuration -- a
    # supervised-outcome measure, collected for every discovered run, not
    # gated on first-submission eligibility. An attempt PM never rated
    # contributes nothing (status != "rated"), never a fabricated 0.
    pm_developer_rating_scores: list[float] = []
    # Production ΔLOC/ΔCC/max-function-CC, per slice, first-attempt
    # (eligible runs only, same guard as correctness above) and
    # final-attempt (every run, like final correctness) -- one accumulator
    # dict per series named in `_FIRST_ATTEMPT_SERIES`/`_FINAL_ATTEMPT_SERIES`.
    # A slice with no available measurement for a given run contributes
    # nothing to that slice's list -- _spread renders an empty list as
    # unavailable, never a fabricated 0.
    first_series: dict[str, dict[int, list[float]]] = {name: {} for name, _extractor in _FIRST_ATTEMPT_SERIES}
    final_series: dict[str, dict[int, list[float]]] = {name: {} for name, _extractor in _FINAL_ATTEMPT_SERIES}

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
        # model_report.py's own named problems (e.g. a pm_model_performance_ref
        # that vanished from disk, or a malformed run-timing log) are this
        # run's evidence too -- dropping them here would make that case
        # indistinguishable from data that was simply never recorded.
        for report_problem in report.get("problems") or []:
            problems.append(f"configuration {configuration_key}, run {run_id}: {report_problem}")

        timing = report.get("timing") or {}
        if timing.get("available"):
            elapsed_seconds_values.append(timing["elapsed_seconds"])
        process = report.get("process") or {}
        if process.get("available"):
            floor_failures_per_run.append(float(process["floor_failures"]))
            nudges_per_run.append(float(process["nudges"]))

        run_first_values: list[float] = []
        run_final_values: list[float] = []
        # One entry per slice, None where that slice's kill rate is
        # unavailable -- a single None disqualifies the run's mean.
        run_first_kill_rates: list[float | None] = []
        run_final_kill_rates: list[float | None] = []
        run_steers = 0
        for slice_entry in report.get("slices") or []:
            slice_number = slice_entry.get("slice")
            attempts_by_slice.setdefault(slice_number, []).append(slice_entry.get("attempts_total"))
            # setdefault unconditionally, even when nothing is appended below,
            # so a slice with zero available measurements still renders as an
            # explicit "unavailable" cell, never a missing one.
            for series in final_series.values():
                series.setdefault(slice_number, [])
            for series in first_series.values():
                series.setdefault(slice_number, [])

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
                        context=f"configuration {configuration_key}, run {run_id}, slice {slice_number} (final attempt)",
                    )
                )
            else:
                problems.append(
                    f"configuration {configuration_key}, run {run_id}, slice {slice_number}: no final attempt to grade correctness from"
                )
            for name, extractor in _FINAL_ATTEMPT_SERIES:
                value = extractor(final_attempt)
                if value is not None:
                    final_series[name][slice_number].append(value)
            run_final_kill_rates.append(_kill_rate(final_attempt))

            if coverage["eligible_for_first_submission"]:
                first_attempt = slice_entry.get("first_attempt")
                first_by_obligation = (first_attempt.get("correctness") or {}).get("by_obligation") if first_attempt else None
                if not first_by_obligation:
                    raise LeaderboardError(
                        f"configuration {configuration_key}, run {run_id}, slice {slice_number}: run_coverage marked "
                        "this run eligible_for_first_submission but its report has no first-attempt correctness "
                        "data -- eligibility computation is inconsistent with the report it examined"
                    )
                run_first_values.append(
                    _mean_obligation_fraction(
                        first_by_obligation,
                        context=f"configuration {configuration_key}, run {run_id}, slice {slice_number} (first attempt)",
                    )
                )
                for name, extractor in _FIRST_ATTEMPT_SERIES:
                    value = extractor(first_attempt)
                    if value is not None:
                        first_series[name][slice_number].append(value)
                run_first_kill_rates.append(_kill_rate(first_attempt))

        steers_per_run.append(run_steers)

        if run_final_values:
            final_attempt_run_means.append(sum(run_final_values) / len(run_final_values))
        if run_final_kill_rates and None not in run_final_kill_rates:
            final_kill_rate_run_means.append(sum(run_final_kill_rates) / len(run_final_kill_rates))
        if run_first_kill_rates and None not in run_first_kill_rates:
            first_kill_rate_run_means.append(sum(run_first_kill_rates) / len(run_first_kill_rates))

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
    first_series_spread = {
        name: {slice_number: _spread(values) for slice_number, values in by_slice.items()}
        for name, by_slice in first_series.items()
    }
    final_series_spread = {
        name: {slice_number: _spread(values) for slice_number, values in by_slice.items()}
        for name, by_slice in final_series.items()
    }

    # There is no ΔLOC tie-break: an unvalidated proxy must never resolve a
    # near-tie that the rubric itself cannot separate. Ordering falls back
    # to `configuration_key` ascending only (see build_leaderboard's
    # `_sort_key`).

    # The rank-support diagnostic (leave-one-node-out robustness and
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
        # The second, independent ranking basis (build_leaderboard's
        # `kill_rate_rank`) and its supervised-outcome companion; never
        # combined with correctness.
        "first_attempt_kill_rate": _spread(first_kill_rate_run_means),
        "final_attempt_kill_rate": _spread(final_kill_rate_run_means),
        "attempts_by_slice": attempts_by_slice_spread,
        "first_loc_by_slice": first_series_spread["loc"],
        "first_code_loc_by_slice": first_series_spread["code_loc"],
        "first_cc_by_slice": first_series_spread["cc"],
        "final_loc_by_slice": final_series_spread["loc"],
        "final_code_loc_by_slice": final_series_spread["code_loc"],
        "final_cc_by_slice": final_series_spread["cc"],
        "final_max_fn_cc_by_slice": final_series_spread["max_fn_cc"],
        "final_narration_lines_by_slice": final_series_spread["narration"],
        "eligible_node_outcomes_by_run": eligible_node_outcomes_by_run,
        "steers": _spread([float(s) for s in steers_per_run]),
        "floor_failures": _spread(floor_failures_per_run),
        "nudges": _spread(nudges_per_run),
        "pm_elapsed_seconds": _spread(elapsed_seconds_values),
        "run_count": len(run_ids),
        "run_ids": run_ids,
        "eligible_run_ids": eligible_run_ids,
        "pm_status_counts": pm_status_counts,
        "completed_runs": pm_status_counts.get("complete", 0),
        "pm_subjective_ratings": pm_subjective_ratings,
        # The supervised-outcome table's "PM Developer rating (mean /2, n)"
        # column -- PM's own judgement, shown alongside the deterministic
        # columns but never blended into any of them.
        "pm_developer_rating": _spread(pm_developer_rating_scores),
        # Kept per-model, not just folded into the repo-wide flat list --
        # render_markdown() needs exact attribution, and a model name could
        # otherwise defeat a string-prefix recovery of it (e.g. `foo` vs.
        # `foo bar`).
        "problems": list(problems),
    }
    return entry, problems


# --- reviewer aggregation -------------------------------------------------
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


def _panel_label(panel: dict[str, Any]) -> str:
    """Display identity `tool · model · effort` of a quality-panel reviewer
    (effort omitted when not recorded)."""
    return " · ".join(str(panel[key]) for key in ("tool", "model", "effort") if panel.get(key))


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
    """Normalized rank points for one resolved comparison round: for a
    panel of N and 1-based rank r, `(N-r)/(N-1)`; a tied group (more
    than one reviewer at the same best-first position) shares the MEAN
    occupied rank.

    `rank_groups` is best-first: group 0 is rank 1 (or ranks 1..k for a
    k-way tie), group 1 starts at rank k+1, and so on -- exactly
    `model_report.py`'s own resolved `pm_judgments.comparisons[].rank_groups`
    shape (a list of lists of `{review_id, tool, model, effort}`).

    Returns:
        `[]` when N <= 1 -- a singleton panel has no comparative score at
        all, never a fabricated 1.0. Otherwise one `(review, points)` pair
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
    """Minimal union-find for the "disconnected comparison groups" check:
    reviewers in disconnected groups are marked not globally comparable
    rather than silently ranked against each other. Two reviewer identities
    are connected exactly when they have ever appeared together in the same
    (N>1) comparison round of the same skill within the same task
    (aggregate_reviewers keeps one instance per skill and is called once per
    task) -- normalized rank points are only comparable within one connected
    component, since a point value earned against one set of opponents says
    nothing about a reviewer who never faced any of them.
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
    """One row per reviewer CONFIGURATION per skill, folded from the
    `reviews`/`pm_judgments` already carried on every report it is given
    (harvested by model_report.resolve_pm_judgments -- run.json is never
    re-read). build_leaderboard calls it once per task partition, so the
    PM-rating pool and the opponent-group connectivity are both computed
    within ONE task's reports only. Connectivity is also kept per skill (one
    _UnionFind per entry of `accumulators`): a reviewer identity carries no
    skill, so a shared instance would let a drift-audit round connect two
    disjoint code-review opponent groups and report them comparable.

    Two independent signals per row, never blended together:

    - **PM rating** -- the mean 0-2 rating (`pm_rating.status == "rated"`)
      across every review report this identity produced for this skill
      within the partition. A review PM marked `"unavailable"` (a timed-out
      or unreadable report -- a reliability outcome, never a substantive
      0) is counted separately in `unavailable_count`, never folded into
      the rating mean. `unacceptable_count` is the rated subset scoring
      exactly 0 -- the drift-reviewer table's "unacceptable / assessed"
      column; it is computed for code-review too, but not rendered there.
    - **Comparative rank score** -- PM's own panel comparisons, reduced via
      `_rank_points`: a reviewer's eligible round scores are averaged within
      each run, then the run means are averaged, so a run contributing
      several rounds cannot outweigh a run contributing one. A reviewer with
      zero eligible (N>1) rounds anywhere has `comparative_score: None`;
      whether that is every row or only some is derived at render time from
      the rows being rendered (`_has_eligible_comparison`).

    Returns:
        `{"code-review": [rows...], "drift-audit": [rows...]}`, each row
        sorted by PM rating mean descending (a row with no ratings at all
        sorts last) -- a presentational ordering only, never a ranking.
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
                # across runs.
                "points_by_run": {},
                "opponent_identities": set(),
            },
        )

    union_finds: dict[str, _UnionFind] = {skill: _UnionFind() for skill in accumulators}

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
                    union_finds[skill].union(identity, other_identity)

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
                root = union_finds[skill].find(identity)
                component_members.setdefault(root, len(component_members) + 1)

        component_count = len(component_members)
        for identity, row in zip(by_identity, rows, strict=True):
            if row["comparative_score"] is not None:
                root = union_finds[skill].find(identity)
                row["comparative_component"] = component_members[root]
                row["comparative_globally_comparable"] = component_count <= 1
            else:
                row["comparative_component"] = None
                row["comparative_globally_comparable"] = None

        # Presentational only: highest PM rating first, a row with no
        # ratings at all last, ties broken by label for determinism.
        rows.sort(
            key=lambda row: (
                row["rating"] is None,
                -(row["rating"]["mean"] if row["rating"] else 0.0),
                row["label"],
            )
        )
        reviewers[skill] = rows

    return reviewers


def aggregate_quality_panel(reports: list[tuple[Path, dict[str, Any]]]) -> list[dict[str, Any]]:
    """One row per (Developer configuration x panel identity), folded from
    the `quality_panel` records carried on each report's slices.
    build_leaderboard calls it once per task partition.

    A panel identity is (tool, model, effort, rubric_sha256): two reviewer
    configurations, or two versions of the rubric, are never pooled into one
    row. Per row: `n_records`/`n_runs` count the records (and distinct runs)
    on the slice's *accepted* attempt, and `scores` holds one `_spread` per
    dimension over exactly those records, so repeat commissions widen the
    range rather than being averaged away. A record on any other attempt (a
    `--attempt` commission) is counted in `n_records_on_unaccepted_attempts`
    and excluded from the spreads. A group with only such records has
    `n_records` 0 and every spread None. This is a model's judgement: it is
    never an input to any rank or any other number here.
    """
    groups: dict[tuple[Any, ...], dict[str, Any]] = {}
    for _path, report in reports:
        configuration = (report.get("developer") or {}).get("configuration_key")
        for slice_entry in report.get("slices") or []:
            accepted_at = slice_entry.get("accepted_at_attempt")
            for record in slice_entry.get("quality_panel") or []:
                panel = {key: record.get(key) for key in ("tool", "model", "effort", "rubric_sha256")}
                group = groups.setdefault(
                    (configuration, *panel.values()),
                    {
                        "configuration": configuration,
                        "panel": panel,
                        "n_records": 0,
                        "n_records_on_unaccepted_attempts": 0,
                        "runs": set(),
                        "values": {key: [] for key in quality_panel.SCORE_KEYS},
                    },
                )
                if accepted_at is None or record.get("attempt") != accepted_at:
                    group["n_records_on_unaccepted_attempts"] += 1
                    continue
                group["n_records"] += 1
                group["runs"].add(report["run_id"])
                for key in quality_panel.SCORE_KEYS:
                    group["values"][key].append(record["scores"][key])
    rows = [
        {
            "configuration": group["configuration"],
            "panel": group["panel"],
            "n_records": group["n_records"],
            "n_runs": len(group["runs"]),
            "n_records_on_unaccepted_attempts": group["n_records_on_unaccepted_attempts"],
            "scores": {key: _spread(group["values"][key]) for key in quality_panel.SCORE_KEYS},
        }
        for group in groups.values()
    ]
    rows.sort(key=lambda row: (str(row["configuration"]), _panel_label(row["panel"]), str(row["panel"]["rubric_sha256"])))
    return rows


def _check_correctness_provenance_consistency(
    reports: list[tuple[Path, dict[str, Any]]], run_coverage: dict[str, dict[str, Any]]
) -> None:
    """Refuse to build a leaderboard when eligible reports disagree, per
    slice number, on the `plan_hash`/`obligations_hash`/`hidden_tests_hash`
    triple they were graded under. `dev_check.build_provenance`'s
    `hidden_tests_hash` exists specifically to catch a stale report graded
    under a since-changed hidden-test body or obligation map being averaged
    and ranked as if comparable.

    Compared per slice **number**, never across slices: slice 1 and slice 2
    carry different hidden-test files by design, so their hashes legitimately
    differ from each other.

    Only `_CORRECTNESS_PROVENANCE_KEYS` define rubric identity. Any other
    field on the block (the per-slice `task_id` echo included) is ignored
    here, so it can neither mask a real disagreement nor manufacture one.

    Only reports eligible for first-submission ranking are compared -- an
    ineligible run never enters the ranked average, so a stale hash on one
    cannot silently corrupt it, but is also not a reason to refuse building
    the leaderboard for everyone else.

    Raises:
        LeaderboardError: naming the slice number and, grouped by distinct
            hash triple, the sorted run ids that carry each one -- when
            triples disagree there is no single "offending" run, so the
            informative rendering is the partition itself, not a per-run
            dump.
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
        # would pass this check and rank on unverifiable comparability.
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
        runs_by_triple: dict[tuple[tuple[str, Any], ...], list[str]] = {}
        for run_id, provenance in provenance_by_run.items():
            triple = tuple((key, provenance.get(key)) for key in _CORRECTNESS_PROVENANCE_KEYS)
            runs_by_triple.setdefault(triple, []).append(run_id)
        if len(runs_by_triple) > 1:
            detail = "; ".join(
                f"{dict(triple)}: {sorted(run_ids)}"
                for triple, run_ids in sorted(runs_by_triple.items(), key=lambda item: sorted(item[1]))
            )
            raise LeaderboardError(
                f"slice {slice_number}: eligible runs disagree on correctness provenance "
                f"(plan_hash/obligations_hash/hidden_tests_hash) -- ranked reports must be graded under "
                f"the same rubric to be averaged/ranked together: {detail}"
            )


def _check_mutation_bank_consistency(reports: list[tuple[Path, dict[str, Any]]]) -> None:
    """Refuse to build a leaderboard when one task partition's kill rates,
    per slice number, were measured against different mutation banks
    (`test_kill_rate.bank_hash` on any report's first or final attempt):
    rates graded under two bank versions must never share a table. The
    placement and the rendering of the refusal mirror
    `_check_correctness_provenance_consistency`.

    Compared per slice number, never across slices: each slice reads its own
    mutant list, so slice 1's and slice 2's hashes legitimately differ. Every
    report is compared, not only first-submission-eligible ones, because the
    final-attempt kill rate averages over every run. An attempt with no
    available kill rate carries no hash and is not compared.

    Raises:
        LeaderboardError: naming the slice number and, grouped by distinct
            bank_hash, the sorted run ids that carry each one.
    """
    runs_by_slice_and_hash: dict[int, dict[str, set[str]]] = {}
    for _path, report in reports:
        for slice_entry in report.get("slices") or []:
            for attempt in (slice_entry.get("first_attempt"), slice_entry.get("final_attempt")):
                block = (attempt or {}).get("test_kill_rate") or {}
                if block.get("available"):
                    runs_by_slice_and_hash.setdefault(slice_entry.get("slice"), {}).setdefault(
                        block["bank_hash"], set()
                    ).add(report["run_id"])
    for slice_number, runs_by_hash in sorted(runs_by_slice_and_hash.items()):
        if len(runs_by_hash) > 1:
            detail = "; ".join(
                f"{bank_hash}: {sorted(run_ids)}"
                for bank_hash, run_ids in sorted(runs_by_hash.items(), key=lambda item: sorted(item[1]))
            )
            raise LeaderboardError(
                f"slice {slice_number}: reports disagree on the mutation bank their test kill rates were measured "
                f"against (bank_hash) -- kill rates graded under two bank versions must never share a table: {detail}"
            )


# --- cross-task standing ---------------------------------------------------
#
# The one derived, cross-partition table in this tool. Everything above is
# scoped within a single task partition by construction; this section is the
# only place two tasks' numbers meet, and it meets them read-only: it runs
# strictly AFTER every task's own tables are final, reads only from those
# finished structures, and feeds back into none of them (a task's own
# correctness number, ranking order and eligibility logic never see it).


def _percentile_ranks(scored: dict[Any, float]) -> dict[Any, float]:
    """Each member's percentile rank within one task's own field.

    Uses the same tie convention as `_rank_points`: sort the field
    descending by value, give each tied group (exact-equal values) the MEAN
    of its occupied 1-based rank positions, then `(N - mean_rank) / (N - 1)`
    for N > 1. A field of exactly one member gets `1.0` (rendered with an
    `n=1 field` marker); an empty field returns `{}`.
    """
    n = len(scored)
    if n == 0:
        return {}
    if n == 1:
        return {member: 1.0 for member in scored}
    ordered = sorted(scored.items(), key=lambda item: -item[1])
    ranks: dict[Any, float] = {}
    position = 1
    i = 0
    while i < n:
        j = i
        while j + 1 < n and ordered[j + 1][1] == ordered[i][1]:
            j += 1
        size = j - i + 1
        mean_rank = position + (size - 1) / 2
        points = (n - mean_rank) / (n - 1)
        for k in range(i, j + 1):
            ranks[ordered[k][0]] = points
        position += size
        i = j + 1
    return ranks


def compute_cross_task_standing(tasks: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """The derived cross-task standing block: one row per Developer
    configuration and, separately per skill, one row per reviewer identity.

    Reads ONLY the finished per-task tables -- each task entry's
    ranked `models` rows and `reviewers` rows -- which must already be final
    when build_leaderboard calls this; nothing here ever flows back into any
    task's own correctness number, ranking order or eligibility.

    Developer side: a configuration's value in a task is its mean
    first-attempt correctness (`first_attempt_correctness["mean"]`); the
    separate `developer_kill_rate` block repeats the same mechanics over
    `first_attempt_kill_rate["mean"]`, where "ineligible" means no run with a
    kill rate on every slice. A
    configuration with no eligible run there has that spread as None and is
    ineligible for the task's field entirely -- excluded both from other
    configurations' percentile computation (it never counts toward N) and
    from its own set of contributing tasks, rendered downstream as "not
    eligible for task <id>", never scored as 0 and never silently dropped.
    Each task's field is ranked via _percentile_ranks; a configuration's
    standing averages those percentile ranks EQUALLY across its contributing
    tasks only.

    Reviewer side (code-review and drift-audit separately): an identity's
    value in a task is its comparative-rank-score mean, and that task
    contributes to the identity's average ONLY WHEN the task's own
    `comparative_globally_comparable` flag is True for that identity. A
    task where the flag is False, or where the identity has no
    comparative score at all, is excluded from BOTH that task's field (for
    everyone else's percentile computation) and the identity's own average,
    exactly as if the identity hadn't participated in that task -- never
    averaged in as a lower or default value. An identity with zero comparable
    tasks anywhere gets no standing at all (`standing: None`), never a
    fabricated one.

    Returns:
        `{"developer": [rows...], "developer_kill_rate": [rows...],
        "code-review": [rows...], "drift-audit": [rows...]}`. Each row carries `per_task` (one cell
        per task the subject appears in: either
        `{"percentile_rank", "field_size"}` or a named status),
        `contributing_tasks`, `standing` (equal-weighted mean of the
        contributing tasks' percentile ranks, or None) and `labels`
        (`"n=1 task"` whenever the average rests on a single contributing
        task, so it is never mistaken for a genuinely cross-task-validated
        number). Rows are sorted standing-descending, no-standing last, ties
        broken by name ascending -- deterministic, presentational only.
    """
    task_ids = sorted(tasks)

    def _developer_subjects(spread_key: str) -> dict[str, dict[str, dict[str, Any]]]:
        subjects: dict[str, dict[str, dict[str, Any]]] = {}
        for task_id in task_ids:
            # The task's field: exactly the configurations with a non-None
            # `spread_key` spread there -- for correctness, precisely the
            # configurations ELIGIBLE for first-submission ranking, per
            # aggregate_model's own contract. Everyone else stays out of
            # `field` entirely, so they count toward no one's percentile rank.
            field: dict[str, float] = {}
            for entry in tasks[task_id]["models"]:
                spread = entry[spread_key]
                if spread is not None:
                    field[entry["model"]] = spread["mean"]
            ranks = _percentile_ranks(field)
            for entry in tasks[task_id]["models"]:
                model = entry["model"]
                cell = (
                    {"percentile_rank": ranks[model], "field_size": len(field)}
                    if model in ranks
                    else {"status": "not_eligible"}
                )
                subjects.setdefault(model, {})[task_id] = cell
        return subjects

    reviewer_subjects: dict[str, dict[tuple[Any, Any, Any], dict[str, dict[str, Any]]]] = {
        skill: {} for skill in ("code-review", "drift-audit")
    }
    for task_id in task_ids:
        for skill, subjects in reviewer_subjects.items():
            rows_in_task = tasks[task_id]["reviewers"].get(skill) or []
            # The task's reviewer field: exactly the identities whose own
            # comparative_globally_comparable flag is True here (which
            # requires having a comparative score at all). Flag-False and
            # unscored identities stay out of `field`, so their scores never
            # enter anyone's percentile computation for this task.
            field: dict[tuple[Any, Any, Any], float] = {}
            for row in rows_in_task:
                score = row["comparative_score"]
                if score is not None and row.get("comparative_globally_comparable") is True:
                    identity = (row["identity"]["tool"], row["identity"]["model"], row["identity"]["effort"])
                    field[identity] = score["mean"]
            ranks = _percentile_ranks(field)
            for row in rows_in_task:
                identity = (row["identity"]["tool"], row["identity"]["model"], row["identity"]["effort"])
                if row["comparative_score"] is None:
                    cell = {"status": "no_comparative_score"}
                elif row.get("comparative_globally_comparable") is not True:
                    cell = {"status": "not_comparable"}
                else:
                    cell = {"percentile_rank": ranks[identity], "field_size": len(field)}
                subjects.setdefault(identity, {})[task_id] = cell

    def _standing_row(*, fields: dict[str, Any], cells: dict[str, dict[str, Any]], sort_name: str) -> dict[str, Any]:
        contributing = [t for t in task_ids if t in cells and "percentile_rank" in cells[t]]
        standing = (sum(cells[t]["percentile_rank"] for t in contributing) / len(contributing)) if contributing else None
        return {
            **fields,
            "per_task": cells,
            "contributing_tasks": contributing,
            "standing": standing,
            # A single-contributing-task average is NOT cross-task validated;
            # the label makes that visible whenever it occurs.
            "labels": ["n=1 task"] if len(contributing) == 1 else [],
            "_sort_name": sort_name,
        }

    def _sorted_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows.sort(key=lambda r: (r["standing"] is None, -(r["standing"] or 0.0), r["_sort_name"]))
        for row in rows:
            del row["_sort_name"]
        return rows

    developer_rows = {
        spread_key: [
            _standing_row(fields={"configuration": model}, cells=cells, sort_name=model)
            for model, cells in sorted(_developer_subjects(spread_key).items())
        ]
        for spread_key in ("first_attempt_correctness", "first_attempt_kill_rate")
    }
    reviewer_rows: dict[str, list[dict[str, Any]]] = {}
    for skill, subjects in reviewer_subjects.items():
        reviewer_rows[skill] = [
            _standing_row(
                fields={
                    "identity": {"tool": identity[0], "model": identity[1], "effort": identity[2]},
                    "label": _reviewer_label(identity),
                },
                cells=cells,
                sort_name=_reviewer_label(identity),
            )
            for identity, cells in sorted(subjects.items(), key=lambda item: _reviewer_label(item[0]))
        ]

    return {
        "developer": _sorted_rows(developer_rows["first_attempt_correctness"]),
        # The parallel, independent standing on first-attempt test kill
        # rate; never combined with the correctness standing above.
        "developer_kill_rate": _sorted_rows(developer_rows["first_attempt_kill_rate"]),
        "code-review": _sorted_rows(reviewer_rows["code-review"]),
        "drift-audit": _sorted_rows(reviewer_rows["drift-audit"]),
    }


def build_leaderboard(
    reports: list[tuple[Path, dict[str, Any]]], policy: dict[str, Any]
) -> tuple[dict[str, Any], list[str]]:
    """Assemble the full cross-model leaderboard, one Developer table pair
    per task partition.

    Reports are first partitioned by their own top-level `task_id`
    (`partition_reports_by_task`), then group_reports_by_model,
    aggregate_model and _check_correctness_provenance_consistency run once
    per partition, so no configuration's number from one task can enter
    another task's tables. Each task's entry carries its own ranked
    `models`, `unattributed_runs`, `run_coverage` (computed against that
    task's OWN `expected_slices`, resolved via bench_lib.resolve_task -- two
    tasks may have different frozen plans) and `problems`.

    Within a task: sorted by mean first-attempt correctness descending, a
    configuration with no eligible run sorted last; ties (including an exact
    tie on first-attempt correctness) break by `model`
    (`configuration_key`) name ascending -- a stable, disclosed order, never
    an unvalidated proxy like ΔLOC. No shared/tied ranks are ever emitted;
    see `_rank_support` for the two-fact diagnostic used instead. Each row
    also carries `kill_rate_rank`, an independent second ranking by mean
    first-attempt test kill rate (same tie-break, None without one); it
    never changes the row order, and the two are never combined.

    Grouping and ranking are computed only over **attributed** reports: a
    run is attributed to a Developer configuration, or it is conspicuously
    unattributed and excluded from ranking. An unattributed report is never
    dropped -- it is recorded in
    `unattributed_runs`, named in `problems`, and still gets a
    `run_coverage` entry -- it is simply never grouped into a `models` row,
    so it can never rank first (or at all) as a model literally named
    `None`.

    Each task entry also carries its OWN `reviewers` block: aggregate_reviewers
    runs once per partition over that partition's reports (attributed or not
    -- a reviewer's identity is a fact about the commission, not about
    whether the reviewed Developer could be identified), so a reviewer
    identity reviewing under two tasks gets an independent PM-rating mean
    and comparative-rank score per task, and its opponent-group connectivity
    is computed within one task's rounds only, never bridging two tasks'
    otherwise-disconnected groups into one falsely-comparable component.

    Raises:
        LeaderboardError: a report names a task id the policy does not
            configure (resolve_task's own named error, wrapped), or any
            per-partition check below refuses the build
            (`_check_correctness_provenance_consistency`,
            `_check_mutation_bank_consistency`).
    """
    def _first_attempt_mean(entry: dict[str, Any]) -> float | None:
        spread = entry["first_attempt_correctness"]
        return spread["mean"] if spread else None

    def _sort_key(entry: dict[str, Any]) -> tuple[Any, ...]:
        mean = _first_attempt_mean(entry)
        return (mean is None, -(mean or 0.0), entry["model"])

    problems: list[str] = []
    tasks_out: dict[str, dict[str, Any]] = {}
    for task_id, task_reports in sorted(partition_reports_by_task(reports).items()):
        try:
            task = bench_lib.resolve_task(policy, task_id)
        except bench_lib.BenchLibError as exc:
            raise LeaderboardError(str(exc)) from exc
        expected_slices = task["expected_slices"]

        task_problems: list[str] = []
        run_coverage = {
            report["run_id"]: compute_run_coverage(report, expected_slices) for _path, report in task_reports
        }
        _check_correctness_provenance_consistency(task_reports, run_coverage)
        _check_mutation_bank_consistency(task_reports)

        attributed_reports = [(path, report) for path, report in task_reports if report["developer"]["attributed"]]
        unattributed_reports = [
            (path, report) for path, report in task_reports if not report["developer"]["attributed"]
        ]

        models = []
        for configuration_key, model_reports in group_reports_by_model(attributed_reports).items():
            entry, model_problems = aggregate_model(configuration_key, model_reports, run_coverage)
            models.append(entry)
            task_problems.extend(model_problems)

        models.sort(key=_sort_key)

        # The second, independent ranking: by mean first-attempt test kill
        # rate, ties broken by configuration key ascending, None for a
        # configuration with no kill-rate-eligible run. It never reorders
        # `models`, whose order stays the correctness ranking.
        kill_rate_ranked = sorted(
            (entry for entry in models if entry["first_attempt_kill_rate"] is not None),
            key=lambda entry: (-entry["first_attempt_kill_rate"]["mean"], entry["model"]),
        )
        kill_rate_rank = {entry["model"]: rank for rank, entry in enumerate(kill_rate_ranked, start=1)}
        for entry in models:
            entry["kill_rate_rank"] = kill_rate_rank.get(entry["model"])

        # The rank-support diagnostic: computed once per adjacent pair, over
        # the FINAL sorted order -- never re-derived at render time. The
        # first row has no row above it to compare against.
        if models:
            models[0]["rank_support"] = None
        for i in range(1, len(models)):
            models[i]["rank_support"] = _rank_support(models[i - 1], models[i])

        # `eligible_node_outcomes_by_run` (the cohort's full per-node
        # evidence, once per eligible run) is only ever a local computation
        # value for `_rank_support` above -- serializing it into
        # leaderboard.json would duplicate evidence already on each
        # model-report.json, once per model row. The adjacent-pair
        # `rank_support` facts computed from it are what consumers actually
        # need, and those are kept.
        for entry in models:
            entry.pop("eligible_node_outcomes_by_run", None)

        unattributed_runs = []
        for _path, report in sorted(unattributed_reports, key=lambda item: item[1]["run_id"]):
            developer = report["developer"]
            unattributed_runs.append({"run_id": report["run_id"], "developer": developer})
            task_problems.append(
                f"run {report['run_id']}: Developer identity unattributed (harness={developer.get('harness')!r}, "
                f"model={developer.get('model')!r}) -- excluded from model ranking, never discarded "
                "(see unattributed_runs and run_coverage)"
            )

        # This task's OWN reviewer tables: aggregated over this partition's
        # reports alone, attributed or not.
        tasks_out[task_id] = {
            "models": models,
            "unattributed_runs": unattributed_runs,
            "run_coverage": run_coverage,
            "problems": task_problems,
            "reviewers": aggregate_reviewers(task_reports),
            "quality_panel": aggregate_quality_panel(task_reports),
        }
        problems.extend(task_problems)

    # Every distinct measurement.metric_version seen across every
    # discovered report (attributed or not, any task -- this is about the
    # measuring apparatus, not ranking), so a metric-version rebuild of
    # already-graded runs is distinguishable from a genuinely new trial. A
    # report with no size_complexity data at all contributes nothing here --
    # an honest absence, not an error.
    measurement_metric_versions = sorted(
        {
            report["measurement_metric_version"]
            for _path, report in reports
            if report.get("measurement_metric_version") is not None
        }
    )

    # Strictly AFTER every task's own tables are final: the derived
    # cross-task block reads only from them and feeds back into none of them.
    cross_task_standing = compute_cross_task_standing(tasks_out)

    leaderboard = {
        "tasks": tasks_out,
        "cross_task_standing": cross_task_standing,
        "measurement_metric_versions": measurement_metric_versions,
    }
    return leaderboard, problems


# --- Markdown rendering -----------------------------------------------------
#
# leaderboard.json is this tool's authoritative, machine-readable output;
# everything below only formats that same data (plus each model's own
# already-written model-report.json, read again here for per-slice detail)
# for a human -- no new number is computed anywhere in this section.


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
    backslash-escaped, same as `_md_cell`: GFM's table-cell splitter may
    not honour a code span's boundary around an embedded pipe, and a stray
    visible backslash before a pipe is a harmless cosmetic wrinkle next to
    a broken table. A pre-existing
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


def _raw_digest(value: str) -> str:
    """A short deterministic fingerprint of the RAW (unslugged) value.

    _slug is lossy by design (it normalizes case/punctuation/runs purely for
    human readability), so distinct raw inputs can slug identically -- e.g.
    'x/y' and 'x-y'. Appending this digest of the exact string that was
    slugged makes the resulting anchor id injective in practice: two
    different raw values essentially never share both their slug AND their
    digest, whatever the cause of the slug collision (separator characters,
    case, a slug that degenerates to empty)."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:8]


def _run_anchor(run_id: str) -> str:
    """The stable anchor id for one run's detail section -- stable and
    independent of rank and model name: a run_id never changes once
    recorded, so this anchor never breaks across a regeneration that
    reorders ranks or corrects an identity. Shape: readable slug first, then
    the raw-value digest (_raw_digest) joined with '--' (which _slug's output
    can never contain), so the id stays human-readable yet injective."""
    return f"run-{_slug(run_id)}--{_raw_digest(run_id)}"


def _config_anchor(task_id: str, configuration_key: str) -> str:
    # Task-qualified: the same configuration (model/tool/effort) can run under
    # two different tasks, and each partition renders its OWN detail block for
    # it -- without the task id both blocks would emit identical anchor ids and
    # every table link from both tasks would resolve to the FIRST block,
    # silently attributing one task's evidence to the other task's row.
    # Each slugged part carries its own raw-value digest right after it, all
    # joined with '--' (which _slug's output can never contain): the slugs
    # stay human-readable while the digests keep distinct
    # (task_id, configuration_key) pairs apart, which no join scheme over
    # lossy slugs alone could guarantee.
    return (
        f"config-{_slug(task_id)}--{_raw_digest(task_id)}"
        f"--{_slug(configuration_key)}--{_raw_digest(configuration_key)}"
    )


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


def _fmt_count_spread(spread: dict[str, Any] | None, *, no_data_label: str = "--") -> str:
    if not spread:
        return no_data_label
    if spread["n"] == 1:
        return f"{spread['mean']:.0f} (n=1)"
    return f"{spread['mean']:.1f} [{spread['min']:.0f}-{spread['max']:.0f}], n={spread['n']}"


def _fmt_rating_spread(spread: dict[str, Any] | None) -> str:
    """A PM 0-2 rating spread cell -- shared by the supervised-outcome
    table's Developer column and both reviewer tables. `None` (no rated
    attempt/review at all -- PM never judged one, or `--run-dir` was never
    given to model_report.py) renders as an explicit label, never a
    fabricated 0/2: a 0 mean is a real, terrible rating PM actually gave,
    and must stay visually distinct from "nothing to rate at all."
    """
    if not spread:
        return "no PM ratings recorded"
    if spread["n"] == 1:
        return f"{spread['mean']:.1f}/2 (n=1)"
    return f"{spread['mean']:.2f}/2 [{spread['min']:.0f}-{spread['max']:.0f}], n={spread['n']}"


def _fmt_score_spread(spread: dict[str, Any] | None) -> str:
    """A quality-panel 1-5 score spread cell, `mean/5 [min-max], n=N`; None
    (no accepted-attempt record) renders as an explicit label, never 0."""
    if not spread:
        return "no records"
    if spread["n"] == 1:
        return f"{spread['mean']:.1f}/5 (n=1)"
    return f"{spread['mean']:.1f}/5 [{spread['min']:.0f}-{spread['max']:.0f}], n={spread['n']}"


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
    """The first-submission table's `Rank support vs previous` cell -- the
    first row's `None` renders `—`; a real diagnostic renders its two facts
    as separate clauses, never merged into one score, confidence grade or
    stability number."""
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
    """Lint/code-health as a hygiene and tool-coverage badge, never a score.
    `run_code_health`'s own verdict is `"measured"`/`"coverage-gap"`, never
    `"pass"` -- health.py emits no quality verdict of its own, and exit 0
    only means the tool ran and produced a payload, not that the code is
    good. A finding/candidate count is shown so a reader can see there IS
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
    """Scope discipline as an exceptions list, not just a count. The
    document-level alert for a nonzero count is computed separately, once,
    in render_markdown (`_total_scope_violations`) -- this only formats one
    attempt's own list.
    """
    violations = scope.get("violations") or []
    if not violations:
        return "no violations"
    return f"{len(violations)} violation(s): " + ", ".join(_code_span(path) for path in violations)


_LOC_CATEGORY_NAMES = ("code", "docstring", "comment", "blank")


def _production_categories_clause(loc: dict[str, Any]) -> str:
    """The production code/docstring/comment/blank split stored at
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
    return f"category split (net): {parts}"


def _max_function_cc_clause(production_cc: dict[str, Any]) -> str:
    """The max-function-CC figure, beside ΔCC's total -- identifies a
    pathological single function rather than diffuse growth."""
    max_cc = production_cc.get("max_function_cyclomatic") or {}
    baseline, endpoint = max_cc.get("baseline"), max_cc.get("endpoint")
    if baseline is None or endpoint is None:
        return "max function CC unavailable"
    return f"max function CC {baseline}->{endpoint}"


def _production_function_counts_clause(production_cc: dict[str, Any]) -> str:
    """Function-count clause beside ΔCC's total and max-function-CC:
    `functions baseline->endpoint (+added/-removed)`.

    Surfaced beside `endpoint mean CC/function` because
    `function_count.removed > 0` is exactly the case that makes a "ΔCC per
    ADDED function" reading silently wrong (dividing net ΔCC by `added`
    alone ignores complexity that left with a removed function); the raw
    counts let a reader see whether removals happened at all. Absent counts
    render as a named unavailable clause, never a fabricated 0.
    """
    counts = production_cc.get("function_count") or {}
    baseline, endpoint = counts.get("baseline"), counts.get("endpoint")
    if baseline is None or endpoint is None:
        return "functions unavailable (not recorded)"
    added, removed = counts.get("added", 0), counts.get("removed", 0)
    return f"functions {baseline}->{endpoint} (+{added}/-{removed})"


def _endpoint_mean_cc_per_function_clause(production_cc: dict[str, Any]) -> str:
    """Endpoint mean CC per production function =
    `endpoint_total / function_count.endpoint` -- NOT ΔCC divided by added
    functions, which is only well defined when removals are zero.
    Descriptive only, never scored; division by zero (no endpoint functions
    at all) is a named unavailable, never a crash or a fabricated value.
    """
    endpoint_total = production_cc.get("endpoint_total")
    endpoint_function_count = (production_cc.get("function_count") or {}).get("endpoint")
    if endpoint_total is None or not endpoint_function_count:
        return "endpoint mean CC/function unavailable (no endpoint function count)"
    return f"endpoint mean CC/function {endpoint_total / endpoint_function_count:.2f}"


def _size_complexity_summary(size_complexity: dict[str, Any]) -> str:
    """One-line ΔLOC/ΔCC summary for a slice's detail section -- production
    bucket only (test/doc deltas and the full per-bucket detail stay in the
    sheet, not surfaced here); descriptive, never a score.

    Carries test ΔLOC beside production ΔLOC (never netted together), the
    production code/docstring/comment/blank split, max function CC beside
    ΔCC, ΔCC's own baseline->endpoint totals (beside its net), a
    function-count clause (baseline->endpoint, +added/-removed), and
    endpoint mean CC per production function.
    """
    loc = (size_complexity or {}).get("loc") or {}
    complexity = (size_complexity or {}).get("complexity") or {}

    if loc.get("available"):
        production = (loc.get("buckets") or {}).get("production") or {}
        test_bucket = (loc.get("buckets") or {}).get("test") or {}
        loc_part = (
            f"ΔLOC +{production.get('added', 0)}/-{production.get('deleted', 0)} "
            f"(net {production.get('net', 0):+d}); test ΔLOC "
            f"+{test_bucket.get('added', 0)}/-{test_bucket.get('deleted', 0)} "
            f"(net {test_bucket.get('net', 0):+d}). "
            f"{_production_categories_clause(loc)}"
        )
    else:
        # compute_loc_delta records no `error` of its own -- a git failure
        # there aborts grading outright rather than producing an unavailable
        # block -- so the only way to reach this arm is a sheet carrying no
        # size_complexity block at all.
        loc_part = "ΔLOC unavailable (not recorded)"

    if complexity.get("available"):
        production_cc = complexity.get("production") or {}
        baseline_total, endpoint_total = production_cc.get("baseline_total"), production_cc.get("endpoint_total")
        # Guard: `ΔCC None->None` would be a fabricated-looking pair -- fall
        # back to just the net when either total is absent.
        if baseline_total is None or endpoint_total is None:
            cc_delta = f"ΔCC net {production_cc.get('net', 0):+d}"
        else:
            cc_delta = f"ΔCC {baseline_total}->{endpoint_total} (net {production_cc.get('net', 0):+d})"
        cc_part = (
            f"{cc_delta}; {_max_function_cc_clause(production_cc)}; "
            f"{_production_function_counts_clause(production_cc)}; "
            f"{_endpoint_mean_cc_per_function_clause(production_cc)}"
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
    order, joined with "/" -- the shape the attempts column and the ΔLOC/ΔCC
    columns both need. `_slice_columns_suffix` labels the same slices in the
    column header.

    `empty_label` is used only when the configuration has no slices at all;
    an individual slice with no value is `formatter`'s own business, and
    every formatter here renders that as an explicit unavailable marker
    rather than a fabricated 0.
    """
    return "/".join(formatter(by_slice.get(slice_number)) for slice_number in sorted(by_slice)) or empty_label


def _slice_columns_suffix(task: dict[str, Any]) -> str:
    """The `S1/S2/.../SN` suffix for every per-slice column header of one
    task's Developer tables: the slice numbers the rows' cells render
    (`_per_slice_cells` iterates each row's per-slice keys, and
    aggregate_model gives every row the same key set), in slice order. With
    no ranked rows at all, falls back to the task's own `expected_slices`
    (identical across its runs' coverage entries; a task section exists only
    when at least one report does)."""
    slice_numbers = sorted({slice_number for entry in task["models"] for slice_number in entry["attempts_by_slice"]})
    if not slice_numbers:
        expected_slices = next(iter(task["run_coverage"].values()))["expected_slices"]
        slice_numbers = list(range(1, expected_slices + 1))
    return "/".join(f"S{slice_number}" for slice_number in slice_numbers)


def _fmt_net_spread(spread: dict[str, Any] | None) -> str:
    """A ΔLOC/ΔCC net spread cell -- explicit sign (net can be negative:
    the attempt shrank the bucket), unlike `_fmt_count_spread`'s unsigned
    convention (attempts/steers are never negative). None (no available
    measurement for this slice) renders as "unavailable", never a
    fabricated 0.
    """
    if not spread:
        return "unavailable"
    if spread["n"] == 1:
        return f"{spread['mean']:+.0f} (n=1)"
    return f"{spread['mean']:+.0f} [{spread['min']:+.0f}-{spread['max']:+.0f}], n={spread['n']}"


def _display_attempt(ordinal: Any) -> Any:
    """Convert a 0-based machine attempt ordinal to the 1-based number a
    human reads. Machine ordinals stay 0-based everywhere in the sheets and
    JSON; this is the one place the renderer converts them.
    """
    return ordinal + 1 if isinstance(ordinal, int) else "?"


def _attempt_obligation_mean(entry: dict[str, Any]) -> float | None:
    """One attempt-trajectory row's own obligation-group mean correctness
    -- the same `_mean_obligation_fraction` reduction used everywhere else
    in this tool, never the raw `hidden_tests_passed/total` the trajectory
    table already prints, which is not the rubric score. `None` when this
    row carries no `by_obligation` block at all."""
    by_obligation = (entry.get("correctness") or {}).get("by_obligation")
    if not by_obligation:
        return None
    return _mean_obligation_fraction(by_obligation, context="attempt trajectory row")


# A float-equality epsilon for comparing means of small rationals (obligation-
# group pass fractions), used only by `_moved_correctness_transitions` below.
# Deliberately NOT a policy.yaml tunable: it only absorbs float-comparison
# noise between two arithmetically identical means and expresses no scoring
# judgement.
_MOVED_CORRECTNESS_ABS_TOL = 1e-9


def _moved_correctness_transitions(trajectory: list[dict[str, Any]]) -> tuple[int, int] | None:
    """`(n, m)`: of this slice's `m` attempt-to-attempt transitions, how
    many `n` moved obligation-group mean correctness beyond float-comparison
    noise. `None` when there are fewer than two attempts to compare, or
    when any adjacent pair's mean is unavailable on either side (an honest
    gap, not a fabricated 0/0)."""
    if len(trajectory) < 2:
        return None
    means = [_attempt_obligation_mean(entry) for entry in trajectory]
    if any(mean is None for mean in means):
        return None
    moved = sum(
        1
        for earlier, later in zip(means, means[1:], strict=False)
        if not math.isclose(earlier, later, abs_tol=_MOVED_CORRECTNESS_ABS_TOL)
    )
    return moved, len(means) - 1


def _kill_rate_summary(block: dict[str, Any] | None) -> str:
    """One attempt's `test_kill_rate` block as `killed/total (rate)`, naming
    any errored mutants, or `unavailable: <reason>` -- the reason's first line
    only, since an output tail follows it (the full text stays in
    model-report.json). A sheet graded before the measurement existed has no
    block at all."""
    if not block:
        return "unavailable: not measured"
    if not block.get("available"):
        return f"unavailable: {_md_cell(str(block.get('reason') or 'no reason recorded').splitlines()[0])}"
    text = f"{block['killed']}/{block['total']} ({block['kill_rate'] * 100:.1f}%)"
    if block.get("errored"):
        text += f", {block['errored']} errored"
    return text


def _hygiene_summary(block: dict[str, Any] | None) -> str:
    """One attempt's `hygiene` block (dev_check.measure_hygiene) as one
    descriptive clause list, or `unavailable: <reason>`. A sheet graded
    before the census existed has no block at all. Files the census skipped
    are named, so a low count is never mistaken for full coverage."""
    if not block:
        return "unavailable: not measured"
    if not block.get("available"):
        return f"unavailable: {_md_cell(str(block.get('reason') or 'no reason recorded').splitlines()[0])}"
    production = block.get("production") or {}
    commits = block.get("commits") or {}
    ratio = production.get("comment_to_code_ratio")
    ratio_text = f"{ratio:.2f}" if ratio is not None else "unavailable (no added code)"
    by_token = production.get("narration_by_token") or {}
    token_text = ", ".join(f"{_code_span(pattern)}: {count}" for pattern, count in by_token.items())
    text = (
        f"code {production.get('added_code')}, docstring {production.get('added_docstring')}, "
        f"comment {production.get('added_comment')}; comment-to-code {ratio_text}; "
        f"narration lines {production.get('narration_lines')} ({token_text}); "
        f"commits {commits.get('count')}, subjects over {commits.get('subject_max_length')} chars "
        f"{commits.get('subjects_over_max')}, with process labels {commits.get('subjects_with_process_label')}"
    )
    skipped = block.get("skipped_files") or {}
    if skipped:
        text += f"; skipped {', '.join(_code_span(path) for path in sorted(skipped))}"
    return text


def _attempt_history_table(trajectory: list[dict[str, Any]]) -> list[str]:
    """One row per Developer attempt, including one steered with no review
    commissioned at all -- `attempt_trajectory` (model_report.py) already
    includes every such row; this only formats it.
    """
    if not trajectory:
        return []
    lines = [
        "Developer attempts:",
        "",
        "| Attempt | Commit | Hidden tests | Test kill rate | Narration lines | PM decision | Reviews commissioned |",
        "|---|---|---|---|---|---|---|",
    ]
    for entry in trajectory:
        correctness = entry.get("correctness") or {}
        hidden_tests = f"{correctness.get('hidden_tests_passed', '?')}/{correctness.get('hidden_tests_total', '?')}"
        commissioned = entry.get("commissioned_reviews") or []
        commissioned_cell = ", ".join(_md_cell(c.get("skill", "?")) for c in commissioned) if commissioned else "none"
        kill_rate = (entry.get("test_kill_rate") or {}).get("kill_rate")
        kill_rate_cell = f"{kill_rate * 100:.1f}%" if kill_rate is not None else "unavailable"
        narration = (entry.get("hygiene") or {}).get("narration_lines")
        narration_cell = str(narration) if narration is not None else "unavailable"
        lines.append(
            f"| {_display_attempt(entry.get('attempt'))} | {_code_span(entry.get('commit_sha') or '?')} | "
            f"{hidden_tests} | {kill_rate_cell} | {narration_cell} | "
            f"{_md_cell(entry.get('pm_decision') or '(undecided)')} | "
            f"{commissioned_cell} |"
        )
    return lines


def _review_order_key(entry: dict[str, Any]) -> tuple[Any, ...]:
    """Sort key for one review-history row: a known `event_index` (populated
    for every commission harvested by review_score.py -- see
    model_report.py's `_review_entry`) sorts first and numerically; failing
    that, a known `at` timestamp sorts next -- ISO-8601 `Z`-suffixed strings
    sort correctly as plain strings, so no datetime parsing is needed here.
    A row with neither sorts last, by its own skill, purely for a stable
    (not meaningful) position. The fallbacks are reachable: a review record
    on a sheet graded before review_score.py harvested `event_index` keeps
    it absent.
    """
    event_index = entry.get("event_index")
    at = entry.get("at")
    at_known = isinstance(at, str) and bool(at)
    skill = entry.get("skill") or ""
    return (event_index is None, event_index if event_index is not None else 0, not at_known, at if at_known else "", skill)


def _review_history_table(reviews: list[dict[str, Any]]) -> list[str]:
    """Reviews of each attempt -- multiple rows can refer to the same
    submission: one row per review *commission*, not per attempt -- an
    attempt with two reviews (a panel, or a retry) gets two rows here,
    distinct from the one row it gets in the attempt-history table above. A
    superseded commission (a retry's earlier record) is never omitted -- it
    is marked in its own Verdict/extraction-status cell instead, so a retry
    is never mistaken for a second, independent vote.

    Ordered by the authoritative `events.jsonl` position when known
    (`event_index`), falling back to the recorded `at` timestamp otherwise
    (see `_review_order_key`). A completion timestamp is not a start time,
    so a fallback-ordered table is explicitly labelled "recorded order",
    never presented as reconstructed execution order.
    """
    rows = list(reviews)
    if not rows:
        return []
    rows.sort(key=_review_order_key)
    any_event_index = any(entry.get("event_index") is not None for entry in rows)
    any_at = any(isinstance(entry.get("at"), str) and entry.get("at") for entry in rows)

    lines = ["Reviews of each attempt:", ""]
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
            "_A true `events.jsonl` position is not captured on this report's reviews; the rows above are "
            "ordered by their recorded time instead -- labelled as recorded order, not reconstructed "
            "execution order._",
        ]
    return lines


_QUALITY_PANEL_SUMMARY_CHARS = 160


def _quality_panel_table(records: list[dict[str, Any]]) -> list[str]:
    """One row per quality-panel record of a slice (attempt, then record
    order); empty when the slice has none."""
    if not records:
        return []
    lines = ["Quality panel:", "", "| Attempt | Panel | Rubric | Scores (c/d/r/t/cd) | Summary |", "|---|---|---|---|---|"]
    for record in records:
        summary = str(record.get("summary") or "")
        if len(summary) > _QUALITY_PANEL_SUMMARY_CHARS:
            summary = summary[: _QUALITY_PANEL_SUMMARY_CHARS - 1] + "…"
        scores = "/".join(str(record["scores"][key]) for key in quality_panel.SCORE_KEYS)
        lines.append(
            f"| {_display_attempt(record.get('attempt'))} | {_md_cell(_panel_label(record))} | "
            f"{_code_span(str(record.get('rubric_sha256'))[:12])} | {scores} | {_md_cell(summary)} |"
        )
    return lines


def _slice_section(slice_entry: dict[str, Any], level: int) -> list[str]:
    # `level` is the ATX level of THIS heading, passed down from the enclosing
    # run section so a task's detail content nests one level under its own
    # ## Task: header instead of sitting beside it as flat siblings.
    prefix = "#" * level
    slice_number = slice_entry.get("slice")
    attempts_total = slice_entry.get("attempts_total")
    accepted_at = slice_entry.get("accepted_at_attempt")
    heading = (
        f"{prefix} Slice {slice_number} -- accepted on attempt {_display_attempt(accepted_at)} of {attempts_total}"
        if accepted_at is not None
        else f"{prefix} Slice {slice_number} -- {slice_entry.get('slice_status', '?')} after {attempts_total} attempt(s)"
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
        f"Lint/code-health: {_quality_summary(quality)}. "
        f"Scope: {_scope_summary(scope)}.",
        f"Production size/complexity (final attempt, vs this slice's own baseline): "
        f"{_size_complexity_summary(size_complexity)}.",
        f"Test kill rate (final attempt, own test suite vs this slice's mutants): "
        f"{_kill_rate_summary(final_attempt.get('test_kill_rate'))}.",
        f"Hygiene (final attempt, added production lines vs this slice's baseline): "
        f"{_hygiene_summary(final_attempt.get('hygiene'))}.",
        "",
    ]

    trajectory = slice_entry.get("attempt_trajectory") or []
    moved = _moved_correctness_transitions(trajectory)
    if moved is not None:
        n, m = moved
        lines += [
            f"Attempts that moved measured (obligation-group mean) correctness: {n}/{m}.",
            "",
        ]

    attempt_lines = _attempt_history_table(trajectory)
    if attempt_lines:
        lines += attempt_lines + [""]

    review_lines = _review_history_table(slice_entry.get("reviews") or [])
    if review_lines:
        lines += review_lines + [""]

    panel_lines = _quality_panel_table(slice_entry.get("quality_panel") or [])
    if panel_lines:
        lines += panel_lines + [""]

    return lines


def _run_section(
    run_id: str,
    report: dict[str, Any] | None,
    run_coverage: dict[str, dict[str, Any]],
    level: int,
) -> list[str]:
    """One run's full detail -- anchored so a rank/name change never breaks
    a link to it. `level` is the ATX level of this run's own heading; the
    enclosing section passes one deeper than its own (see _model_section)."""
    prefix = "#" * level
    lines = [f'<a id="{_run_anchor(run_id)}"></a>', "", f"{prefix} Run {_code_span(run_id)}", ""]
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
        lines += _slice_section(slice_entry, level + 1)

    rating = report.get("pm_subjective_rating") or {}
    if rating.get("available"):
        lines += [f"{'#' * (level + 1)} PM's subjective rating (verbatim; never blended into any score)", ""]
        lines += [f"> {line}" if line else ">" for line in (rating.get("text") or "").splitlines()]
        lines.append("")

    return lines


def _model_section(
    task_id: str,
    rank: int,
    entry: dict[str, Any],
    reports_by_run_id: dict[str, dict[str, Any]],
    run_coverage: dict[str, dict[str, Any]],
    level: int,
) -> list[str]:
    # `level` is the ATX level of THIS config's own heading -- one deeper than
    # the enclosing ## Task: header, so a task's detail content nests under it
    # instead of sitting beside it as flat siblings.
    prefix = "#" * level
    model = entry["model"]
    lines = [
        f'<a id="{_config_anchor(task_id, model)}"></a>',
        "",
        f"{prefix} {rank}. {_code_span(model)}",
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
        lines += _run_section(run_id, reports_by_run_id.get(run_id), run_coverage, level + 1)

    return lines


def _total_scope_violations(reports: list[tuple[Path, dict[str, Any]]]) -> int:
    """Total authorized-surface violations across every discovered run's
    first AND final attempt (the only two full attempt blocks a
    model-report.json carries -- `attempt_trajectory` is a compact summary
    without a `scope` field) -- drives render_markdown's top-level scope
    alert when nonzero.
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
    unavailable linter is never reported as a clean pass).

    A single-attempt slice has `first_attempt` and `final_attempt` pointing
    at the same attempt ordinal, so naively summing both would double-count
    it -- each `(run_id, slice, attempt_number)` is counted at most once
    here.
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
    overlap, for every slice both sides have data on -- the between-model
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
    claim about the cohort's shape, which can change as new panels are
    commissioned.
    """
    return any(row["comparative_score"] is not None for row in rows)


def _panel_shape_note(rows: list[dict[str, Any]]) -> str:
    """The paragraph explaining what code-review's panels actually look
    like, derived from the rows being rendered via `_has_eligible_comparison`
    and never hardcoded -- so it cannot assert a cohort shape that a later
    trial silently falsifies.

    Code-review is the only role this applies to, so the role is named
    literally: the drift-reviewer table has no comparative column
    (drift-audit is never ranked against other reviewers), so panel shape
    has no bearing on anything a reader sees there.

    Two cases, both read off `rows` rather than assumed:

    - No row has an eligible (N>1) round: every code-review panel is a
      singleton. Said plainly as the role's real shape -- not a defect, not
      an empty table -- with the column's literal cell text quoted.
    - At least one row has an eligible round: real multi-model panels
      exist. A row without one of its own still reads "single reviewer",
      a true, unremarkable property of that row.
    """
    if not _has_eligible_comparison(rows):
        return (
            "**Every code-review panel for this task is a singleton** -- this is the role's real shape here, "
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
        "**Real multi-model code-review panels exist for this task**, so the comparative column below carries "
        f"genuine comparative rank scores for the rows that appeared in one.{sizes_clause} A row with no "
        'eligible round of its own still reads "single reviewer -- no comparative score" -- a real property '
        "of that row, not a gap; that reviews DID occur regardless is shown by the PM rating and round "
        "columns."
    )


def _comparative_score_cell(row: dict[str, Any]) -> str:
    """The code-reviewer table's comparative-rank-score cell (the
    drift-reviewer table has no such column -- drift-audit never ranks
    reviewers against each other, only against PM's 0-2 rating scale).

    `comparative_score is None` covers BOTH "this reviewer never appeared
    in any panel at all" and "every panel it appeared in was a singleton"
    -- both read *"single reviewer -- no comparative score"*, since neither
    produces a comparable number; the surrounding table's prose explains
    that reviews did occur.
    """
    if row["comparative_score"] is None:
        return "single reviewer -- no comparative score"
    spread = row["comparative_score"]
    if spread["n"] == 1:
        cell = f"{spread['mean']:.2f} (n=1 run)"
    else:
        cell = f"{spread['mean']:.2f} [{spread['min']:.2f}-{spread['max']:.2f}], n={spread['n']} runs"
    if row.get("comparative_globally_comparable") is False:
        # This reviewer's points were earned entirely against a different
        # set of opponents than at least one other reviewer's, so the two
        # numbers are not on the same scale.
        cell += " (comparable only within its own opponent group -- see note)"
    return cell


def _reviewer_utility_table(reviewers: dict[str, list[dict[str, Any]]]) -> list[str]:
    """The 'Code reviewer -- PM-assessed utility' table. One row per
    reviewer configuration that ran ANY `code-review` commission within ONE
    task partition -- PM's own rating, never blended with the comparative
    score (the two differ in repeatability the same way
    `pm_subjective_rating` differs from the deterministic scores).

    The heading sits at ###, one level below the enclosing ## Task: header,
    matching the Developer tables' nesting."""
    rows = reviewers.get("code-review") or []
    lines = ["### Code reviewer -- PM-assessed utility", ""]
    if not rows:
        lines += ["_No `code-review` commissions recorded for this task._", ""]
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


def _reviewer_acceptability_table(reviewers: dict[str, list[dict[str, Any]]]) -> list[str]:
    """The 'Drift reviewer -- PM-assessed acceptability' table. One row per
    reviewer configuration that ran ANY `drift-audit` commission within ONE
    task partition. No comparative column at all -- drift-audit's job is to
    catch real authorization violations, not to be ranked against other
    reviewers, and a FAIL verdict is never translated into a poor rating
    (finding a real violation is good reviewing; that translation would
    happen entirely inside PM's own rating, never here).

    `unacceptable / assessed` is shown alongside the mean specifically
    because a mean alone can conceal a catastrophic 0 among 2s.

    The heading sits at ###, one level below the enclosing ## Task: header,
    matching the Developer tables' nesting."""
    rows = reviewers.get("drift-audit") or []
    lines = ["### Drift reviewer -- PM-assessed acceptability", ""]
    if not rows:
        lines += ["_No `drift-audit` commissions recorded for this task._", ""]
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


def _quality_panel_section(rows: list[dict[str, Any]]) -> list[str]:
    """One task's quality-panel section: the framing paragraph and a
    spread table per (Developer configuration x panel identity), or one line
    when the task has no records. Never ranked."""
    lines = ["### Quality panel -- a model's judgement (never ranked)", ""]
    if not rows:
        return lines + ["_No quality-panel records for this task._", ""]
    lines += [
        (
            "_A single reviewer model's subjective 1-5 scores of an accepted submission against the "
            "frozen plan: not repeatable the way a test is, and one fixed reviewer configuration is "
            "used per cohort. Repeat commissions widen the range shown rather than being averaged "
            "away. Nothing here enters any rank._"
        ),
        "",
        "| Developer configuration | Panel (tool · model · effort) | Rubric | Correctness beyond tests | Design "
        "| Readability/docs | Tests | Contract discipline | Records (runs) |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        cells = " | ".join(_fmt_score_spread(row["scores"][key]) for key in quality_panel.SCORE_KEYS)
        records_cell = f"{row['n_records']} ({row['n_runs']})"
        if row["n_records_on_unaccepted_attempts"]:
            records_cell += f" (+{row['n_records_on_unaccepted_attempts']} on unaccepted attempts, not pooled)"
        lines.append(
            f"| {_code_span(row['configuration'])} | {_md_cell(_panel_label(row['panel']))} | "
            f"{_code_span(str(row['panel']['rubric_sha256'])[:12])} | {cells} | {records_cell} |"
        )
    lines.append("")
    return lines


def _run_index_table(
    reports: list[tuple[Path, dict[str, Any]]],
    run_coverage: dict[str, dict[str, Any]],
    configuration_by_run_id: dict[str, str],
) -> list[str]:
    """A flat index of EVERY discovered run across ALL tasks, attributed or
    not -- alongside the per-task detail sections above. The Task column
    names each run's own top-level task_id verbatim (this table spans all
    partitions, unlike the per-task sections). Both lookup dicts arrive
    merged over every task partition by render_markdown."""
    lines = [
        "| Run | Task | Developer configuration | PM status | Eligible for first-submission | Graded slices |",
        "|---|---|---|---|---|---|",
    ]
    for _path, report in sorted(reports, key=lambda item: item[1]["run_id"]):
        run_id = report["run_id"]
        coverage = run_coverage.get(run_id) or {}
        configuration = configuration_by_run_id.get(run_id, "unattributed")
        lines.append(
            f"| [{_code_span(run_id)}](#{_run_anchor(run_id)}) | {_code_span(report['task_id'])} | "
            f"{_code_span(configuration)} | "
            f"{coverage.get('pm_status', '?')} | {'yes' if coverage.get('eligible_for_first_submission') else 'no'} | "
            f"{coverage.get('graded_slices', [])} |"
        )
    return lines


def _cross_task_cell(cell: dict[str, Any] | None, task_id: str, status_texts: dict[str, Callable[[str], str]]) -> str:
    """One per-task column cell of a cross-task table. `cell` is None when
    the subject does not appear in this task at all (`--`, absence --
    distinct from being present-but-excluded, which carries its own named
    label); a ranked cell prints the percentile rank with the same 3-decimal
    convention as `_fmt_score`, plus an explicit `n=1 field` marker when the
    task's field held exactly one member."""
    if cell is None:
        return "--"
    if "percentile_rank" in cell:
        text = f"{cell['percentile_rank']:.3f}"
        if cell.get("field_size") == 1:
            text += " (n=1 field)"
        return text
    return status_texts[cell["status"]](task_id)


def _cross_task_standing_cell(row: dict[str, Any], *, no_contributing_text: str) -> str:
    """The right-hand 'Cross-task standing' cell: the equal-weighted average
    over the contributing tasks, carrying the explicit `n=1 task` marker
    whenever that average rests on a single task; a subject with zero
    contributing tasks gets an explicit named marker instead of a number --
    never a fabricated value."""
    if row["standing"] is None:
        return no_contributing_text
    text = f"{row['standing']:.3f}"
    if "n=1 task" in row["labels"]:
        text += " (n=1 task)"
    return text


def _cross_task_developer_table(
    rows: list[dict[str, Any]], task_ids: list[str], *, heading: str, not_eligible_text: str
) -> list[str]:
    """One Developer table of the cross-task section (called once for the
    correctness standing and once for the test kill rate standing): one row
    per attributed configuration appearing in ANY task, one column per
    discovered task. A present-but-ineligible configuration renders
    `<not_eligible_text> <id>` in that task's column (never 0, never a
    dropped row); a task the configuration never ran renders `--`."""
    lines = [heading, ""]
    if not rows:
        lines += ["_No attributed Developer configurations discovered._", ""]
        return lines
    header = "| Developer configuration | " + " | ".join(_code_span(t) for t in task_ids) + " | Cross-task standing |"
    lines += [header, "|" + "---|" * (len(task_ids) + 2)]
    status_texts = {"not_eligible": lambda t: f"{not_eligible_text} {_code_span(t)}"}
    for row in rows:
        cells = [_cross_task_cell(row["per_task"].get(t), t, status_texts) for t in task_ids]
        lines.append(
            f"| {_code_span(row['configuration'])} | " + " | ".join(cells) + " | "
            + _cross_task_standing_cell(row, no_contributing_text="no eligible tasks") + " |"
        )
    lines.append("")
    return lines


def _cross_task_reviewer_table(
    rows: list[dict[str, Any]], task_ids: list[str], *, skill: str, heading: str
) -> list[str]:
    """One reviewer-skill half of the cross-task section (called once for
    code-review and once for drift-audit). Exclusion labels distinguish the
    two ways a scored-or-not identity can sit outside a task's comparable
    field: `not comparable in task <id>` (a comparative score exists, but
    the task's own connectivity flag is false for this identity) versus
    `no comparative score in task <id>` (no eligible panel round at all)."""
    lines = [heading, ""]
    if not rows:
        lines += [f"_No `{skill}` reviewer identities discovered._", ""]
        return lines
    header = "| Reviewer configuration | " + " | ".join(_code_span(t) for t in task_ids) + " | Cross-task standing |"
    lines += [header, "|" + "---|" * (len(task_ids) + 2)]
    status_texts = {
        "not_comparable": lambda t: f"not comparable in task {_code_span(t)}",
        "no_comparative_score": lambda t: f"no comparative score in task {_code_span(t)}",
    }
    for row in rows:
        cells = [_cross_task_cell(row["per_task"].get(t), t, status_texts) for t in task_ids]
        lines.append(
            f"| {_code_span(row['label'])} | " + " | ".join(cells) + " | "
            + _cross_task_standing_cell(row, no_contributing_text="no comparable tasks") + " |"
        )
    lines.append("")
    return lines


def _cross_task_section(standing: dict[str, Any], task_ids: list[str]) -> list[str]:
    """The one derived cross-partition section of the document. Placed after
    every ## Task: section and before the Glossary so it reads as separate
    from -- never part of -- any task's own tables; the full definition lives
    in the glossary exactly once (this prose states only what the columns
    mean at a glance)."""
    lines = ["## Cross-task standing", ""]
    lines += [
        (
            "Derived strictly after every task's own tables above are final, reading from them and feeding "
            "back into none of them -- a derived, never-authoritative-on-its-own standing measure. Each task "
            "column shows the subject's percentile rank WITHIN that task's own field; the right-hand column "
            "averages those ranks equally across the contributing tasks only. Full definition: see the "
            "[Glossary](#glossary) below."
        ),
        "",
    ]
    lines += _cross_task_developer_table(
        standing["developer"],
        task_ids,
        heading="### Developer -- cross-task standing",
        not_eligible_text="not eligible for task",
    )
    lines += _cross_task_developer_table(
        standing["developer_kill_rate"],
        task_ids,
        heading="### Developer -- cross-task standing on test kill rate",
        not_eligible_text="no test kill rate for task",
    )
    lines += _cross_task_reviewer_table(
        standing["code-review"], task_ids, skill="code-review", heading="### Code reviewer -- cross-task standing"
    )
    lines += _cross_task_reviewer_table(
        standing["drift-audit"], task_ids, skill="drift-audit", heading="### Drift reviewer -- cross-task standing"
    )
    return lines


def _glossary_lines() -> list[str]:
    """The `## Glossary` section -- placed after every task section and the
    cross-task standing so the tables are not buried under it; every
    definitional caveat this document states lives here EXACTLY ONCE, and
    each use site states only the number and its label.
    """
    return [
        "## Glossary",
        "",
        (
            "- **Correctness** -- the equally-weighted mean of a slice's obligation-group `fraction`s "
            "(the task's `obligations_file` in `policy.yaml`), never the raw hidden-test pass count, which would "
            "double-count a large group."
        ),
        (
            "- **First-attempt correctness** -- correctness on a slice's ordinal-0 (first) Developer "
            "submission, averaged equally across a run's slices, then equally across a configuration's "
            "*eligible* runs (the coverage/eligibility check). This is what the first-submission table "
            "ranks on."
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
        "- **Attempts** -- the true PM attempt count per slice, not the number of graded rows.",
        "- **Steers** -- how many of a run's attempts PM steered rather than accepted or stopped.",
        (
            "- **Floor failures / Nudges** -- per-run counts from PM's own `events.jsonl`: `floor` events "
            "whose note records a failed mechanical floor, and `send` events, free messages PM sent into the "
            "live Developer session without relaunching it (a relaunch or steer is an attempt, never a "
            "nudge). Supervision-cost descriptors like Steers, averaged over runs whose report carries them "
            "(`unavailable` otherwise), and never ranked."
        ),
        "- **PM elapsed** -- wall-clock time from PM's `init` event to its terminal `complete`/`stop` event.",
        (
            "- **Runs (eligible/discovered)** -- a configuration's total runs on disk versus how many are "
            "eligible for first-submission ranking; every run stays visible in its own detail section "
            "regardless."
        ),
        (
            "- **Developer configuration** -- one Developer identity, `model · harness · effort`; its runs "
            "fold into one row. **Reviewer configuration** is the same for a reviewer, `model · tool · effort`."
        ),
        (
            "- **Rank by observed mean** -- position by mean first-attempt correctness, ties broken by "
            "configuration name. The supervised-outcome table's **Rank** repeats that order, never re-ranking."
        ),
        (
            "- **Test kill rate** -- the fraction of a task's seeded mutants, for that slice, that the "
            "Developer's OWN test suite kills: each mutant monkey-patches one plan-named function to break "
            "one obligation, and it is killed when a test that passed unmutated stops passing. An errored "
            "mutant (a crash or timeout) counts against the rate, never as a kill and never by shrinking the "
            "denominator. Measured on the candidate's own test files only, never the hidden tests. Averaged "
            "like correctness, across a run's slices and then its runs -- but only over runs with an "
            "available kill rate on every slice, so its n can be smaller than correctness's. The `Final` "
            "column is the same on final attempts, a descriptive companion."
        ),
        (
            "- **Rank by test kill rate** -- an independent second ranking by mean first-attempt test kill "
            "rate, ties broken by configuration name; `—` for a configuration without one. Correctness "
            "remains the primary rank and orders every table; the two are never combined."
        ),
        (
            "- **Rank support vs previous** -- two separate facts about a row versus the row above it: "
            "**Rubric** (does the row above still strictly win after removing any one hidden-test node?) and "
            "**Runs** (do the two rows' observed first-attempt ranges overlap?); never combined into a score."
        ),
        "- **Completed/total** -- a configuration's runs whose PM status is `complete`, over all its discovered runs.",
        (
            "- Spread convention throughout: **mean [min-max], n**. At n=1, the one value is shown with "
            "n=1, never a fabricated zero spread."
        ),
        (
            "- Column-name conventions: a `Final` prefix is the same measure on a slice's final attempt; a "
            "trailing `S1/S2/...` lists one value per slice, in slice order; `[min-max]` follows the spread "
            "convention."
        ),
        (
            "- **Physical ΔLOC** -- net physical lines added to production source (the task's "
            "`measurement.production_paths` in `policy.yaml`) between "
            "a slice's own baseline commit and the attempt's commit (`git diff --numstat --no-renames`, "
            "added minus deleted; physical lines, including docstrings and blanks, never "
            "SLOC-excluding-comments -- the two definitions are never mixed, `policy.yaml`'s "
            "`measurement.loc_definition`). Test ΔLOC is classified and counted separately and is never "
            "netted against production."
        ),
        (
            "- **Code ΔLOC** -- the `code` category of physical ΔLOC's own code/docstring/comment/blank "
            "decomposition (`policy.yaml`'s `measurement.loc_category_definition`): physical ΔLOC minus "
            "documentation and blank-line churn. The four categories (code, docstring, comment, blank) sum "
            "exactly to the physical net, by construction. Both figures are descriptive, never a ranking "
            "criterion and never framed as smaller-is-better -- a larger or smaller net change is not "
            "itself better or worse code. Physical ΔLOC alone is misleading as the headline "
            "production-size figure (it is inflated by documentation), which is why code ΔLOC is surfaced "
            "alongside it rather than left to per-run detail alone."
        ),
        (
            "- **ΔCC** -- total production function cyclomatic complexity, endpoint minus baseline (summed "
            "over every function `health.py`'s absolute `analyze --all` finds at each revision, never the "
            "capped, display-only `candidates` list). Descriptive only -- splitting one function into three "
            "raises it through added function-entry counts alone -- and never scored."
        ),
        (
            "- **Max function CC** (`max fn CC` in column headers) -- the largest single production function's "
            "cyclomatic complexity at "
            "the attempt's endpoint. A LEVEL, not a delta -- it identifies a pathological single function "
            "rather than diffuse growth spread across many. `policy.yaml` defines no threshold for it, so "
            "nothing here can pass or fail it."
        ),
        (
            "- **Endpoint mean CC/function** and **function counts** -- endpoint mean CC/function is "
            "`endpoint_total / function_count.endpoint`, NOT ΔCC divided by added functions, which is only "
            "well defined when `function_count.removed == 0`; the baseline->endpoint function counts "
            "(with added/removed) are shown alongside it so a reader can see whether removals happened at "
            "all."
        ),
        (
            "- A slice with no available ΔLOC/ΔCC measurement renders as `unavailable`, never as a "
            "fabricated `0`. A slice flagged with a grading-baseline reset (a stop/restart mid-run) has its "
            "first-to-final size/complexity comparison named as unreliable in that run's own Problems entry "
            "-- correctness is unaffected."
        ),
        (
            "- **Hygiene census** -- counts over the lines an attempt ADDED to production files against its "
            "slice's own baseline, each classified code/docstring/comment/blank exactly as the Code ΔLOC split "
            "does: **narration lines** are added comment or docstring lines matching at least one of "
            "`policy.yaml`'s `hygiene.narration_tokens` patterns (history narration such as steer, round or "
            "slice references, `TODO`, `legacy`), counted once per line and separately per pattern; "
            "**comment-to-code** is added docstring plus comment lines over added code lines; and the "
            "attempt's commit subjects are counted, with those longer than `hygiene.commit_subject_max_length` "
            "and those matching `hygiene.commit_process_labels`. A file unparsable at the attempt's commit is "
            "skipped and named. Descriptive only: never a score and never a ranking criterion. `Final narration "
            "lines` is the final attempt's count."
        ),
        (
            "- **Lint/code-health** -- a hygiene and tool-coverage badge, never a score: a 0 is a measured "
            "pass, an unavailable tool is reported as unavailable, never a clean pass."
        ),
        (
            "- **Attempts that moved measured correctness** -- of a slice's attempt-to-attempt transitions, "
            "how many moved obligation-group mean correctness beyond float-comparison noise. Not \"wasted "
            "attempts\" -- a steer that fixed a drift finding, contract detail, or review finding the "
            "hidden tests do not cover will not move this figure."
        ),
        (
            "- **PM Developer rating (mean /2, n)** -- PM's own 0-2 rating of individual Developer "
            "submissions (`developer_judgments`), flattened across every rated attempt of every "
            "discovered run for a configuration. PM's judgement, shown alongside the deterministic columns, "
            "never blended into any of them -- the same separation `pm_subjective_rating` already gets."
        ),
        (
            "- **PM rating (mean /2, n)** (both reviewer tables) -- PM's own 0-2 rating of individual review reports "
            "(`review_judgments`' rating shape), per reviewer configuration. A review PM could not "
            "rate at all (a timed-out or unreadable report) is an explicit reliability outcome, counted "
            "separately, never blended into this mean as a 0."
        ),
        (
            "- **Comparative rank score** (code-reviewer table only) -- PM's own panel comparisons (`review_judgments`' "
            "comparison shape), normalized to `(N-r)/(N-1)` for a panel of size N and 1-based rank r (ties "
            "share the mean occupied rank); N=1 has no comparative score at all, never a fabricated 1.0. "
            "Averaged within a run first, then across runs."
        ),
        (
            "- **Rounds / distinct runs** -- how many PM comparison rounds (of any panel size) a reviewer "
            "appeared in, over how many distinct runs it reviewed or was compared in. **Distinct runs** alone "
            "is the second figure."
        ),
        "- **Observed panel sizes** -- the distinct sizes of the comparison rounds a reviewer appeared in.",
        (
            "- **Unacceptable / assessed** -- how many of a drift reviewer's PM-rated reports scored 0, over "
            "how many were rated."
        ),
        (
            "- **Quality panel** -- one fixed reviewer model's subjective 1-5 scores of an accepted "
            "submission on five dimensions: correctness beyond tests (c), design (d), readability/docs "
            "(r), tests (t) and contract discipline (cd). Records come from `tools/quality_panel.py`; "
            "`Rubric` is the first 12 hex characters of the rubric file's sha256, so a changed rubric "
            "shows as a different value and is never pooled with the old one. Nothing here enters "
            "any ranking."
        ),
        (
            "- **Cross-task standing** -- a derived, never-authoritative-on-its-own standing measure, "
            "computed strictly after every task's own tables are final and reading only from them: each "
            "Developer configuration's within-task percentile rank of first-attempt correctness, and "
            "separately each reviewer identity's within-task percentile rank of its comparative-rank-score "
            "mean (`code-review` and `drift-audit` in their own tables). Percentile rank reuses this "
            "document's own tie convention: sort the task's field descending, tied values share the mean "
            "of their occupied 1-based ranks, `(N - mean_rank) / (N - 1)` for N > 1, and exactly `1.0`, "
            "labelled `n=1 field`, when the field holds a single member. A configuration ineligible for a "
            "task's first-submission ranking renders `not eligible for task <id>` and is excluded from that "
            "task's field entirely -- never given a 0 for that task, never silently dropped; a reviewer whose "
            "`comparative_globally_comparable` flag is false for a task, or who has no comparative score "
            "there, is likewise excluded from both that task's field and its own average, never averaged in "
            "as a lower or default value. An average resting on a single contributing task is labelled "
            "`n=1 task`, so it is never mistaken for a genuinely cross-task-validated number. A second, "
            "separate Developer table applies the same mechanics to first-attempt test kill rate, where a "
            "configuration without a kill rate in a task renders `no test kill rate for task <id>`; the two "
            "Developer standings are never combined. Nothing in this section feeds back into any task's own "
            "numbers."
        ),
        (
            "- Reviews tables (per-slice detail) can carry multiple rows referring to the same submission "
            "-- one row per review commission, not per attempt: an attempt reviewed by a panel or retried "
            "gets one row per commission."
        ),
        (
            "- Reviews table columns -- **Event order** is the review's position in PM's `events.jsonl` "
            "(`unavailable` when not captured), **Recorded time** its recorded timestamp, **Role** its "
            "skill, **Reviewer** its `tool / model`, and **Verdict / extraction status** its verdict or the "
            "reason its report could not be parsed."
        ),
        (
            "- Developer attempts table columns -- **Attempt** is 1-based, **Commit** the attempt's commit, "
            "**Hidden tests** the raw passed/total count (not the correctness score), **Test kill rate** that "
            "attempt's own-suite kill rate, **Narration lines** its hygiene-census narration count, "
            "**PM decision** PM's "
            "accept/steer/stop call, and **Reviews commissioned** the review skills PM commissioned on it."
        ),
        (
            "- Obligation table columns -- **Obligation group** names a group from "
            "the task's `obligations_file`; **Passed/Total** and **Fraction** are that group's hidden-test "
            "results on the final attempt."
        ),
        (
            "- Run index columns -- **PM status** is PM's recorded run status, **Eligible for "
            "first-submission** whether the run passes the coverage/eligibility check, and **Graded slices** "
            "the slice numbers graded for it."
        ),
        (
            "- **`model unknown`/`effort unknown`** (reviewer identity) -- a `--reviewer-command` review "
            "recorded before pm_lib's 2026-09-18 fix shows this UNLESS an operator attestation "
            "(`policy.yaml`'s `review_identity.corrections`) fills the gap for that specific commission; "
            "an attested run instead shows the reviewer's real model and `default` (or a requested effort), "
            "exactly as a post-fix run would. A run graded after the fix always shows the real identity "
            "structurally, with no attestation needed. Two distinct rows for what was physically the same "
            "reviewer -- an unattested pre-fix commission next to an attested or post-fix one -- is the "
            "correct rendering of two different recorded facts, not a bug."
        ),
        "",
    ]


def _developer_task_section(
    task_id: str,
    task: dict[str, Any],
    task_reports: list[tuple[Path, dict[str, Any]]],
    reports_by_run_id: dict[str, dict[str, Any]],
    run_coverage: dict[str, dict[str, Any]],
) -> list[str]:
    """One task's complete section: the `## Task:` header wrapping that
    task's OWN "first submission"/"supervised outcome" table pair,
    conformance paragraph, reviewer tables, AND per-configuration detail
    blocks. Every figure here comes from exactly one task's partition, and
    a configuration running under two tasks gets one detail block (with a
    task-qualified anchor) per task. Every heading below the `## Task:`
    header is emitted ONE LEVEL DEEPER than its enclosing heading
    (tables/configs at ###, runs at ####, slices and ratings at #####), so
    an outline/TOC view nests each task's content under its own header."""
    models = task["models"]
    slices = _slice_columns_suffix(task)
    lines = [f"## Task: {task_id}", ""]
    lines += [
        "### Developer -- first submission",
        "",
        (
            "**Rank orders the observed configuration means only and does not claim statistical "
            "separation.** `Rank support vs previous` carries two separately-named categorical facts "
            "about each row versus the row directly above it, never combined into a score, confidence "
            "grade or stability number: **Rubric** varies one hidden-test node at a time, holding every "
            "run fixed, and asks whether the row above still strictly beats this row after every such "
            "single-node removal (leave-one-node-out); **Runs** compares the two rows' observed "
            "first-attempt min-max ranges and is **not** a confidence interval. The two "
            "statements are never combined into one joint grade. `Rank by test kill rate` is a second, "
            "independent ranking of the same rows; it never reorders them and is never combined with "
            "correctness."
        ),
        "",
        (
            f"| Rank by observed mean | Developer configuration | Correctness [min-max] | Rank by test kill rate | "
            f"Test kill rate [min-max] | Code ΔLOC {slices} | Physical ΔLOC {slices} | ΔCC {slices} | "
            "Rank support vs previous | Runs (eligible/discovered) |"
        ),
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for rank, entry in enumerate(models, start=1):
        first_code_loc_cells = _per_slice_cells(
            entry["first_code_loc_by_slice"], _fmt_net_spread, empty_label="unavailable"
        )
        first_loc_cells = _per_slice_cells(entry["first_loc_by_slice"], _fmt_net_spread, empty_label="unavailable")
        first_cc_cells = _per_slice_cells(entry["first_cc_by_slice"], _fmt_net_spread, empty_label="unavailable")
        lines.append(
            f"| {rank} | [{_code_span(entry['model'])}](#{_config_anchor(task_id, entry['model'])}) | "
            f"{_fmt_pct_spread(entry['first_attempt_correctness'], no_data_label='no eligible runs')} | "
            f"{entry['kill_rate_rank'] if entry['kill_rate_rank'] is not None else '—'} | "
            f"{_fmt_pct_spread(entry['first_attempt_kill_rate'], no_data_label='unavailable')} | "
            f"{first_code_loc_cells} | {first_loc_cells} | {first_cc_cells} | "
            f"{_rank_support_cell(entry.get('rank_support'))} | {_runs_cell(entry)} |"
        )

    lines += [
        "",
        "### Developer -- supervised outcome",
        "",
        (
            "Same row order as the table above -- never re-ranked by this table's own numbers, so a "
            "reader cannot mistake supervised-outcome position for a second, competing ranking."
        ),
        "",
        (
            "**`Attempts` and `Steers` measure supervision cost, not the source of `Gain` -- gain is "
            "measured only by hidden tests, so a steer that fixed something the hidden tests do not cover "
            "will not appear in it.** See each run's own "
            "slice detail below for how many of its attempt-to-attempt transitions actually moved measured "
            "correctness."
        ),
        "",
        (
            "| Rank | Developer configuration | Final correctness [min-max] | Final test kill rate [min-max] | "
            "Gain (pp) | Final code ΔLOC "
            f"{slices} | Final physical ΔLOC {slices} | Final ΔCC {slices} | Final max fn CC {slices} | "
            f"Final narration lines {slices} | Attempts {slices} | Steers | Floor failures | Nudges | PM elapsed | "
            "PM Developer rating (mean /2, n) | Completed/total |"
        ),
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for rank, entry in enumerate(models, start=1):
        attempts_cells = _per_slice_cells(entry["attempts_by_slice"], _fmt_count_spread, empty_label="--")
        final_code_loc_cells = _per_slice_cells(
            entry["final_code_loc_by_slice"], _fmt_net_spread, empty_label="unavailable"
        )
        final_loc_cells = _per_slice_cells(entry["final_loc_by_slice"], _fmt_net_spread, empty_label="unavailable")
        final_cc_cells = _per_slice_cells(entry["final_cc_by_slice"], _fmt_net_spread, empty_label="unavailable")
        final_max_fn_cc_cells = _per_slice_cells(
            entry["final_max_fn_cc_by_slice"], _fmt_count_spread, empty_label="unavailable"
        )
        final_narration_cells = _per_slice_cells(
            entry["final_narration_lines_by_slice"],
            lambda spread: _fmt_count_spread(spread, no_data_label="unavailable"),
            empty_label="unavailable",
        )
        lines.append(
            f"| {rank} | {_code_span(entry['model'])} | "
            f"{_fmt_pct_spread(entry['final_attempt_correctness'], no_data_label='no data')} | "
            f"{_fmt_pct_spread(entry['final_attempt_kill_rate'], no_data_label='unavailable')} | "
            f"{_fmt_pp_spread(entry['gain_pp'])} | {final_code_loc_cells} | {final_loc_cells} | {final_cc_cells} | "
            f"{final_max_fn_cc_cells} | {final_narration_cells} | {attempts_cells} | "
            f"{_fmt_count_spread(entry['steers'])} | "
            f"{_fmt_count_spread(entry['floor_failures'], no_data_label='unavailable')} | "
            f"{_fmt_count_spread(entry['nudges'], no_data_label='unavailable')} | "
            f"{_fmt_elapsed_spread(entry['pm_elapsed_seconds'])} | "
            f"{_fmt_rating_spread(entry['pm_developer_rating'])} | {entry['completed_runs']}/{entry['run_count']} |"
        )

    # All three cohort-wide figures are computed over THIS task's own
    # reports/models only: lint/scope totals and between-model ΔCC range
    # overlap across tasks would mix two rubrics' measurements into one
    # statement, the same boundary leak the partitioning exists to prevent.
    lint_total = _total_lint_findings(task_reports)
    scope_total = _total_scope_violations(task_reports)
    cc_overlap = _cc_ranges_overlap_across_models(models)
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
        # No "ΔCC is descriptive and never scored" restatement here: the
        # glossary's own ΔCC bullet is that caveat's single definition.
        else "at least one pair of configurations' final-attempt ΔCC ranges does not overlap, so the ranges "
        "alone do not rule out a between-model difference for that pair -- see each row's own ΔCC spread"
        if cc_overlap is False
        else "too little ΔCC data in this cohort to compare configurations' ranges"
    )
    lines += [
        "",
        (
            "**Conformance: lint findings and scope violations are conformance checks, not "
            "comparisons -- a 0 there is a measured pass, not missing data. Max function CC is a "
            "descriptive maintainability signal only: policy.yaml defines no threshold for it, so "
            "nothing here can pass or fail it.** "
            f"Across this cohort's first and final attempts, {lint_clause} and {scope_total} scope "
            f"violation(s) were recorded; see each attempt's own quality/scope summary and "
            f"max-function-CC figure below for detail. Separately, {overlap_clause}."
        ),
        "",
    ]
    # This task's OWN reviewer tables: their rows come from this task's
    # partition alone, so a reviewer identity reviewing under two tasks
    # appears once per task with independently-scoped numbers.
    lines += _reviewer_utility_table(task["reviewers"])
    lines += _reviewer_acceptability_table(task["reviewers"])
    lines += _quality_panel_section(task["quality_panel"])
    # This task's OWN per-configuration detail blocks: rank restarts per
    # task, matching the tables above. Each block ends on a blank line,
    # so the next task's heading -- or the global sections when this is the
    # last task -- always follows exactly one blank.
    for rank, entry in enumerate(models, start=1):
        lines += _model_section(task_id, rank, entry, reports_by_run_id, run_coverage, level=3)
    return lines


def render_markdown(leaderboard: dict[str, Any], reports: list[tuple[Path, dict[str, Any]]]) -> str:
    """Render `leaderboard` (the exact structure written to leaderboard.json)
    plus each model's own model-report.json detail into one human-readable
    Markdown document -- the "for a human" counterpart to leaderboard.json's
    "for a machine" one. Invents no new number: every figure here already
    exists in leaderboard.json or a model-report.json on disk.

    Every task gets its own `## Task:` section wrapping that task's Developer
    table pair, conformance paragraph, reviewer tables, and per-configuration
    detail blocks (`_developer_task_section`), with every in-task heading
    nested one level below its enclosing heading, so a reader can never
    mistake one task's rows -- or evidence -- for another's; the reviewer
    tables are sectioned per task exactly like the Developer ones, reading
    each task's own partition-scoped `reviewers` block."""
    reports_by_run_id = _reports_by_run_id(reports)
    tasks = leaderboard["tasks"]
    merged_run_coverage = {
        run_id: coverage
        for task_id in sorted(tasks)
        for run_id, coverage in tasks[task_id]["run_coverage"].items()
    }
    configuration_by_run_id = {
        run_id: model["model"]
        for task_id in sorted(tasks)
        for model in tasks[task_id]["models"]
        for run_id in model["run_ids"]
    }
    problems = [problem for task_id in sorted(tasks) for problem in tasks[task_id]["problems"]]
    scope_violation_total = _total_scope_violations(reports)

    lines = [
        "# Leaderboard",
        "",
        (
            "First-submission ability and supervised outcomes, one section per task's frozen plan. Higher "
            "correctness is better; smaller edits and shorter elapsed time are supporting measures."
        ),
        "",
    ]
    if scope_violation_total:
        # Top-level alert for a nonzero scope-violation count -- the exact
        # paths live in each affected run's own slice detail
        # (_scope_summary), not repeated here.
        lines += [
            (
                f"**Scope alert: {scope_violation_total} authorized-surface violation(s) recorded across this "
                "cohort's runs -- see each affected run's slice detail below for the exact paths.**"
            ),
            "",
        ]
    lines += [
        "Definitions and conventions: see the [Glossary](#glossary) below.",
        "",
    ]
    for task_id in sorted(tasks):
        task_reports = [item for item in reports if item[1]["task_id"] == task_id]
        lines += _developer_task_section(
            task_id, tasks[task_id], task_reports, reports_by_run_id, merged_run_coverage
        )

    # The one derived cross-partition section: computed by build_leaderboard
    # strictly after every task's tables were final, rendered here AFTER all
    # of them and BEFORE the glossary so it can never be mistaken for part
    # of any task's own tables.
    lines += _cross_task_section(leaderboard["cross_task_standing"], sorted(tasks))

    lines += _glossary_lines()

    # No leading blank: the glossary (or, with no tasks at all, the
    # definitions line) already ends on one.
    lines += ["## Run index", ""]
    lines += _run_index_table(reports, merged_run_coverage, configuration_by_run_id)

    unattributed_runs = [run for task_id in sorted(tasks) for run in tasks[task_id]["unattributed_runs"]]
    if unattributed_runs:
        lines += ["", "## Unattributed runs", "", (
            "Developer identity could not be resolved for these runs -- excluded from every "
            "configuration's ranking above, never discarded."
        ), ""]
        for run in unattributed_runs:
            # Global section, not nested under any ## Task: header, so its
            # run sections sit at ### rather than the deeper in-task level.
            lines += _run_section(run["run_id"], reports_by_run_id.get(run["run_id"]), merged_run_coverage, 3)

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
            "No composite score exists -- correctness ranks configurations on its own, and test kill rate "
            "is a second, independent ranking that is never combined with it; ΔLOC/ΔCC are supporting "
            "columns, and PM's own judgments and the quality panel's model judgement are supporting "
            "columns/tables too -- none is ever blended into a score."
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
            "Rebuild the cross-model leaderboard from every model-report.json on disk, one section per "
            "task, ranked by mean first-attempt correctness."
        )
    )
    parser.add_argument(
        "--out", type=Path, default=None, help="where to write the JSON leaderboard (default: results/leaderboard.json)"
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=None,
        help="where to write the Markdown leaderboard (default: results/leaderboard.md)",
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=None,
        help="directory holding one <run_id>/model-report.json per run (default: results/runs)",
    )
    parser.add_argument(
        "--policy",
        type=Path,
        default=None,
        help="policy file whose tasks: registry resolves each report's task (default: policy.yaml at this repo's root)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = bench_root()
    policy_path = (args.policy or (root / "policy.yaml")).expanduser().resolve()
    policy = load_leaderboard_policy(policy_path)

    runs_root = (args.results_dir or default_runs_root(root)).expanduser().resolve()
    out_path = (args.out or default_out_path(root)).expanduser().resolve()
    markdown_path = (args.markdown_out or default_markdown_path(root)).expanduser().resolve()

    reports = discover_reports(runs_root)
    leaderboard, problems = build_leaderboard(reports, policy)
    # Rendered before either file is written: a render_markdown() bug must
    # leave both leaderboard.json and leaderboard.md at their prior
    # generation, never JSON updated with Markdown left stale behind it.
    markdown = render_markdown(leaderboard, reports)
    bench_lib.write_json_atomically(out_path, leaderboard)
    bench_lib.write_text_atomically(markdown_path, markdown, suffix=".md.tmp")
    total_models = sum(len(task["models"]) for task in leaderboard["tasks"].values())
    print(f"wrote {out_path} ({total_models} model(s) from {len(reports)} report(s))")
    print(f"wrote {markdown_path}")
    return bench_lib.report_problems("leaderboard.py", problems)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except LeaderboardError as exc:
        print(f"leaderboard.py: error: {exc}", file=sys.stderr)
        sys.exit(1)
