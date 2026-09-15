#!/usr/bin/env python3
"""Tool 4: one model's full PM run, reshaped into a per-model report.

This module invents no scoring math and no composite score -- weighting
belongs to Tool 5 (`leaderboard.py`), driven by `policy.yaml`. It only reads
what `dev_check.py`/`review_score.py` already computed into each slice's
scoring sheet (`results/runs/<run_id>/slice-<N>.json`) and reshapes it into
one run-level document: first/final-attempt correctness/quality/scope per
slice, a compact per-attempt trajectory, attempt counts, and every review
commission (`reviews`, one record per commission -- a panel or a retry both
represented, never collapsed). It also folds in PM's own
`model-performance.md` rating (referenced by each sheet's
`pm_model_performance_ref`), read back verbatim and kept in its own
`pm_subjective_rating` block -- that rating is PM's judgement on a fixed
scale, "not a mechanical measurement, and never presented as one"
(project-manager's `references/model-performance-rubric.md`), so it is never
parsed into structured scores here.

Everything this module reads is already-graded, already-on-disk data --
except the run's own `timing` block, which is derived from `events.jsonl`'s
`init`/`complete`/`stop` timestamps and requires read access to the
originating PM run directory (`--run-dir`, optional). That read is still
strictly read-only against PM state (no run token, no write, matching every
other tool in this suite) -- it is simply not "already-on-disk sheet data"
the way everything else here is. Omitting `--run-dir` degrades gracefully:
`timing` reads `available: false` with a named reason, never a guess.

**PM's own structured judgments** (`run.json`'s
`review_judgments[]`/`developer_judgments[]`) are harvested here, in
`resolve_pm_judgments`, from the same `--run-dir` this module already reads
for `timing`/`provenance`, and joined onto this report's own `reviews`
entries (a `pm_rating` field) and `attempt_trajectory` entries (a
`pm_developer_judgment` field). The harvest lives in this module rather than
in `review_score.py` because PM's judgments are per-SLICE, run-level data
covering BOTH reviewer skills and the Developer, while `review_score.py` is
invoked once per `(slice, skill)` and has no Developer-judgment concept at
all -- and this module already receives `run_dir` for exactly this kind of
derived, run-level fact that doesn't belong on any one skill's per-attempt
record (`resolve_run_timing`/`resolve_run_provenance` are the existing
precedent), and already assembles the one run-level document these
judgments belong on. Every judgment read is strictly read-only against
`run.json`/`events.jsonl` -- no PM state is ever written, matching every
other tool in this suite (and PM's judgments themselves are surfaced, never
blended into any deterministic number -- the same separation
`pm_subjective_rating` already gets, immediately above).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import bench_lib
import dev_check

_SHEET_FILENAME_RE = re.compile(r"^slice-(\d+)\.json$")


class ModelReportError(bench_lib.BenchLibError):
    """Raised for every condition this tool must fail loudly on.

    main() catches exactly this exception type, prints it, and exits 1 --
    matching dev_check.py's/grade_run.py's own __main__ pattern.
    """


def bench_root() -> Path:
    """Absolute path to this repo's root -- see bench_lib.repo_root()."""
    try:
        return bench_lib.repo_root()
    except bench_lib.BenchLibError as exc:
        raise ModelReportError(str(exc)) from exc


def default_sheets_dir(root: Path, run_id: str) -> Path:
    """Where grade_run.py/dev_check.py write this run's sheets -- see
    review_score.default_sheet_path, which hardcodes the same
    `results/runs/<run_id>/` convention rather than reading it from
    policy.yaml (this tool has no tunables of its own, matching that)."""
    return root / "results" / "runs" / run_id


def default_out_path(root: Path, run_id: str) -> Path:
    return default_sheets_dir(root, run_id) / "model-report.json"


def read_json(path: Path) -> Any:
    """Read and parse one JSON file, failing loudly with the path on error."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ModelReportError(f"required file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ModelReportError(f"invalid JSON in {path}: {exc}") from exc


def discover_sheets(sheets_dir: Path, run_id: str) -> list[tuple[int, Path, dict[str, Any]]]:
    """Every `slice-<N>.json` sheet found for `run_id`, sorted by slice number.

    Raises:
        ModelReportError: the directory has no matching sheet at all --
            grade_run.py needs to run first.
    """
    if not sheets_dir.is_dir():
        raise ModelReportError(
            f"no scoring sheets directory found for run_id {run_id!r} at {sheets_dir} -- "
            "run tools/grade_run.py against this run first"
        )
    found: list[tuple[int, Path, dict[str, Any]]] = []
    seen_slice_numbers: dict[int, Path] = {}
    for path in sorted(sheets_dir.glob("slice-*.json")):
        match = _SHEET_FILENAME_RE.match(path.name)
        if not match:
            continue
        slice_number = int(match.group(1))
        if slice_number in seen_slice_numbers:
            raise ModelReportError(
                f"two sheet files parse to the same slice number {slice_number}: "
                f"{seen_slice_numbers[slice_number]} and {path}"
            )
        seen_slice_numbers[slice_number] = path
        sheet = read_json(path)
        try:
            bench_lib.validate_sheet_identity(sheet, run_id, slice_number, path)
        except bench_lib.BenchLibError as exc:
            raise ModelReportError(str(exc)) from exc
        found.append((slice_number, path, sheet))
    if not found:
        raise ModelReportError(
            f"no slice-<N>.json scoring sheets found for run_id {run_id!r} under {sheets_dir} -- "
            "run tools/grade_run.py against this run first"
        )
    found.sort(key=lambda item: item[0])
    return found


def _require_consistent(
    sheets: list[tuple[int, Path, dict[str, Any]]], field_path: tuple[str, ...], *, ignore_none: bool = False
) -> Any:
    """The one value every sheet agrees on for `field_path` (e.g.
    `("developer",)` or `("run_status", "pm_status")`), or a loud error
    naming which slices disagreed -- these fields all come from the same
    run.json, so disagreement across sheets is corruption, never something
    to average or pick around.

    Compares candidates by equality, not by collecting them into a `set`
    (`("developer",)` is a dict -- the structured identity block -- and
    dicts are not hashable), so this
    works identically for a scalar field and for a whole nested block.

    `ignore_none` treats a sheet with no value for this field as "not yet
    recorded" rather than a disagreement -- correct only for
    `pm_model_performance_ref`, which is legitimately null on a sheet graded
    before PM wrote `model-performance.md` (dev_check.py's
    resolve_model_performance_ref). Every other field this tool checks
    (`developer`, `run_status.pm_status`/`.stop_reason`) is always present
    on a valid sheet and comes from the same run.json for every slice, so a
    None there is itself a disagreement worth raising on, not something to
    treat as a wildcard.
    """
    values: dict[int, Any] = {}
    for slice_number, _path, sheet in sheets:
        value: Any = sheet
        for key in field_path:
            value = value.get(key) if isinstance(value, dict) else None
        values[slice_number] = value
    candidates = [v for v in values.values() if not ignore_none or v is not None]
    distinct: list[Any] = []
    for candidate in candidates:
        if not any(candidate == existing for existing in distinct):
            distinct.append(candidate)
    if len(distinct) > 1:
        field_name = ".".join(field_path)
        detail = ", ".join(f"slice {n}={v!r}" for n, v in sorted(values.items()))
        raise ModelReportError(f"sheets for this run disagree on {field_name!r}: {detail}")
    return distinct[0] if distinct else None


def _correctness_without_by_node(attempt: dict[str, Any] | None) -> dict[str, Any] | None:
    """A copy of `attempt["correctness"]` with `by_node` dropped.

    `by_node` (dev_check.score_correctness's full node_id -> outcome map)
    is deliberately per-run evidence kept only on the scoring sheet
    (results/runs/<run_id>/slice-<N>.json) -- model-report.json already
    runs to thousands of lines per run, and the sheet is already the
    documented place an analyst reads per-node evidence from. Copies
    rather than mutates: the same sheet dict this was read from is read
    again elsewhere in the same process (e.g. `resolve_attempts_total`),
    so popping the key in place would corrupt it for every later reader.
    """
    if attempt is None:
        return None
    correctness = attempt.get("correctness")
    if correctness is None:
        return None
    trimmed = dict(correctness)
    trimmed.pop("by_node", None)
    return trimmed


def _attempt_without_by_node(attempt: dict[str, Any] | None) -> dict[str, Any] | None:
    """A shallow copy of a whole attempt entry with its `correctness.by_node`
    dropped, for `first_attempt`/`final_attempt` -- see
    `_correctness_without_by_node` for why. Every other field (`quality`,
    `scope`, `size_complexity`, ...) passes through unchanged; only the
    `correctness` key is replaced, and only on the copy, so the sheet's own
    attempt dict (read again elsewhere in this process) is untouched.
    """
    if attempt is None:
        return None
    trimmed = dict(attempt)
    trimmed["correctness"] = _correctness_without_by_node(attempt)
    return trimmed


def first_attempt_node_outcomes(
    sheet: dict[str, Any], slice_number: int, obligations: dict[str, Any], sheet_path: Path | None = None
) -> dict[str, dict[str, str]] | None:
    """The first attempt's per-node hidden-test outcomes, nested by the
    obligation group each node belongs to: `{group_id: {node_id: outcome}}`.

    Nested by group, not flat, because the only consumer this exists for
    (a future rank-support diagnostic) needs, for each node, which group's
    denominator it counts against -- exactly what `by_obligation`'s counts
    already aggregate, just not down to the node.

    Returns:
        None when the slice has no attempt-0 row at all (the same case
        `has_attempt_zero` flags) -- never another attempt's map
        substituted for the missing one.

    Raises:
        ModelReportError: naming the run/slice/group, if the reconstructed
            per-group pass/total from `by_node` disagrees with the
            attempt's own recorded `by_obligation` counts, or if a node in
            one is unknown to the other -- see `_validate_node_outcomes`.
    """
    attempt = resolve_first_attempt(sheet)
    if attempt is None:
        return None
    correctness = attempt.get("correctness") or {}
    # Validate the RAW value: `or {}` would coerce a malformed empty list or
    # string into a dict and silently skip the shape check below.
    _validate_by_node_shape(correctness.get("by_node"), slice_number, sheet_path)
    by_node: dict[str, str] = correctness.get("by_node") or {}
    by_obligation: dict[str, Any] = correctness.get("by_obligation") or {}

    try:
        groups = dev_check.obligation_groups_for_slice(obligations, slice_number)
        node_to_group = dev_check.node_to_group_map(groups)
    except dev_check.DevCheckError as exc:
        raise ModelReportError(str(exc)) from exc

    nested: dict[str, dict[str, str]] = {group["id"]: {} for group in groups}
    unknown_nodes = []
    for node_id, outcome in by_node.items():
        group_id = node_to_group.get(node_id)
        if group_id is None:
            unknown_nodes.append(node_id)
            continue
        nested[group_id][node_id] = outcome
    if unknown_nodes:
        raise ModelReportError(
            f"slice {slice_number}'s first attempt by_node lists node(s) not in obligations.yaml's "
            f"group map: {sorted(unknown_nodes)}"
        )

    _validate_node_outcomes(nested, by_obligation, slice_number)
    return nested


_KNOWN_NODE_OUTCOMES = frozenset({"passed", "failed", "error", "skipped"})


def _validate_by_node_shape(by_node: Any, slice_number: int, sheet_path: Path | None) -> None:
    """Reject a `by_node` map that is not `{node_id: outcome}` with each
    outcome one of the four strings `score_correctness` ever emits.

    A malformed sheet -- `by_node` recorded as a list, or an outcome that
    is not one of the four known strings -- must stop this tool with a
    named error identifying the concrete sheet, never raise a bare
    `AttributeError`/`KeyError` from deeper inside the reconstruction.
    """
    where = f"sheet {sheet_path}" if sheet_path is not None else f"slice {slice_number}'s sheet"
    if not isinstance(by_node, dict):
        raise ModelReportError(
            f"{where}: correctness.by_node must be a mapping of node id to outcome, got {type(by_node).__name__}"
        )
    for node_id, outcome in by_node.items():
        if not isinstance(outcome, str) or outcome not in _KNOWN_NODE_OUTCOMES:
            raise ModelReportError(
                f"{where}: correctness.by_node[{node_id!r}] = {outcome!r} is not one of "
                f"{sorted(_KNOWN_NODE_OUTCOMES)}"
            )


def _validate_node_outcomes(
    nested: dict[str, dict[str, str]], by_obligation: dict[str, Any], slice_number: int
) -> None:
    """Cross-check the nested by_node reconstruction against the attempt's
    own recorded `by_obligation` passed/total counts, group by group.

    This is not defensive padding: `by_node` and `by_obligation` are both
    already-stored evidence from the same `score_correctness` call, so a
    disagreement between them means one of the two is stale, and that must
    stop this tool rather than silently emit whichever is wrong.
    """
    group_ids = set(nested) | set(by_obligation)
    for group_id in sorted(group_ids):
        if group_id not in by_obligation:
            raise ModelReportError(
                f"slice {slice_number}: group {group_id!r} appears in by_node's group mapping but not in "
                "this attempt's by_obligation"
            )
        if group_id not in nested:
            raise ModelReportError(
                f"slice {slice_number}: group {group_id!r} appears in by_obligation but has no nodes in "
                "this attempt's by_node"
            )
        nodes = nested[group_id]
        reconstructed_total = len(nodes)
        reconstructed_passed = sum(1 for outcome in nodes.values() if outcome == "passed")
        recorded = by_obligation[group_id]
        recorded_total = recorded.get("total")
        recorded_passed = recorded.get("passed")
        if reconstructed_total != recorded_total or reconstructed_passed != recorded_passed:
            raise ModelReportError(
                f"slice {slice_number}, group {group_id!r}: by_node reconstructs to "
                f"{reconstructed_passed}/{reconstructed_total} passed/total but by_obligation records "
                f"{recorded_passed}/{recorded_total}"
            )


def resolve_first_attempt(sheet: dict[str, Any]) -> dict[str, Any] | None:
    """The ordinal-0 attempt entry -- the Developer's first submission for
    this slice, which is what the leaderboard's ranking basis (mean
    first-attempt correctness) is computed from.

    Returns:
        The attempt dict, or None when the sheet has no attempt-0 row at
        all -- the git-log walk's fallback can leave a slice with only its
        final attempt's row, and
        `has_attempt_zero` already flags exactly this case for eligibility.
        This function never substitutes another attempt for the missing
        one; a caller wanting to know *why* it's absent reads
        `has_attempt_zero` alongside it.
    """
    for attempt in sheet.get("attempts") or []:
        if attempt.get("attempt") == 0:
            return attempt
    return None


def resolve_final_attempt(sheet: dict[str, Any]) -> dict[str, Any] | None:
    """The attempt entry to report as this slice's final state: the accepted
    attempt if one is recorded, else the most recently graded attempt present
    (the most recent graded state, not a claim that it was accepted).

    Returns:
        The attempt dict, or None if the sheet has no attempts at all
        (a slice PM never actually graded any attempt of, which grade_run.py
        would not itself produce a sheet for -- kept as a defensive None
        rather than an IndexError).
    """
    attempts = sheet.get("attempts") or []
    if not attempts:
        return None
    target = sheet.get("accepted_at_attempt")
    if target is None:
        target = max(a["attempt"] for a in attempts)
    for attempt in attempts:
        if attempt.get("attempt") == target:
            return attempt
    return None


def resolve_correctness_provenance(
    first_attempt: dict[str, Any] | None, final_attempt: dict[str, Any] | None, slice_number: int, run_id: str
) -> dict[str, Any] | None:
    """The `plan_hash`/`obligations_hash`/`hidden_tests_hash` triple this
    slice was graded under -- carried through so `leaderboard.py` can
    refuse to average/rank reports that disagree on the rubric they were
    graded against.

    Both the first and final attempt carry their own `provenance` (each
    captured once, at that attempt's own first grade, per
    `dev_check.build_provenance`'s docstring) -- ordinarily identical
    within one slice, since both attempts are graded from the same
    checkout of policy.yaml/obligations.yaml/hidden_tests/. They are
    compared here and any disagreement is a named error naming the run and
    slice, rather than silently preferring one attempt's hashes over the
    other's.

    Returns:
        None when this slice has no graded attempt at all (final_attempt
        is None) -- there is nothing to compare a rubric hash against.

    Raises:
        ModelReportError: the first and final attempt's own provenance
            triples disagree, naming the run, slice and the differing hash.
    """
    if final_attempt is None:
        return None
    final_provenance = final_attempt.get("provenance") or {}
    triple_keys = ("plan_hash", "obligations_hash", "hidden_tests_hash")
    final_triple = {key: final_provenance.get(key) for key in triple_keys}
    if first_attempt is not None:
        first_provenance = first_attempt.get("provenance") or {}
        first_triple = {key: first_provenance.get(key) for key in triple_keys}
        if first_triple != final_triple:
            raise ModelReportError(
                f"run {run_id!r}, slice {slice_number}: first attempt's correctness provenance "
                f"{first_triple} disagrees with the final attempt's {final_triple} -- this slice was "
                "graded under different rubric versions between its first and final attempt"
            )
    return final_triple


def _review_entry(attempt_number: int, record: dict[str, Any]) -> dict[str, Any]:
    """One `reviews` entry for a single commissioned review record.

    Every identifying field the record carries -- `review_id`, `skill`,
    `tool`, `model`, `effort`, `head`, `before_head`, `at`, `event_index`,
    `report_ref`, `report_sha256`, `superseded_by` -- is passed through, not
    just `verdict`/`findings_by_severity`/`open_after_this_attempt`. This is
    what lets `leaderboard.py`'s review-history table's "Reviewer" column
    hold the reviewer's actual model instead of the sheet *field name*, and
    its "Role" column hold the record's own `skill`.

    `review_id`, `effort`, `event_index` and `before_head` are real,
    harvested values: `review_score.py`'s commission-keyed selection reads
    them straight from `run.json`'s `reviews[]` entries. A sheet graded
    before that harvest existed can still show them absent, which the
    caller's own fallback (`event_index is None`) handles.

    `superseded_by` marks a retried commission's own record as no longer the
    attempt's active vote for its (skill, tool, model, effort) lineage
    (`review_score.py`'s `upsert_sheet`) -- carried through unconditionally
    so a renderer can mark it, never silently drop it.

    A report that failed to parse carries only `parse_error`
    (review_score.py's own `build_record`), never `verdict`/
    `findings_by_severity`/`open_after_this_attempt` -- preserved verbatim
    here rather than defaulting those fields to None, which would silently
    read as "commissioned, nothing to report" instead of a named parse
    failure (AGENTS.md: "an unparsable review report is a named parse
    error, never zero findings").

    `pm_rating` is NOT set here -- it starts absent and is stamped on by
    `resolve_pm_judgments` once every entry in the slice's `reviews` list
    exists (that join needs the full, already-built list to look up
    `review_id`s against). Every entry gets a `pm_rating` unconditionally,
    `build_report` always calls `resolve_pm_judgments`; see that function's
    own docstring for what "unjudged" versus "rated" versus "unavailable"
    mean.
    """
    entry = {
        "attempt": attempt_number,
        "review_id": record.get("review_id"),
        "skill": record.get("skill"),
        "tool": record.get("tool"),
        "model": record.get("model"),
        "effort": record.get("effort"),
        "head": record.get("head"),
        "before_head": record.get("before_head"),
        "at": record.get("at"),
        "event_index": record.get("event_index"),
        "report_ref": record.get("report_ref"),
        "report_sha256": record.get("report_sha256"),
        "superseded_by": record.get("superseded_by"),
    }
    if "parse_error" in record:
        entry["parse_error"] = record["parse_error"]
        return entry
    entry["verdict"] = record.get("verdict")
    entry["findings_by_severity"] = record.get("findings_by_severity")
    entry["open_after_this_attempt"] = record.get("open_after_this_attempt")
    return entry


def resolve_attempts_total(sheet: dict[str, Any]) -> int:
    """The true PM attempt count for this slice: the highest attempt
    ordinal recorded, plus one -- NOT the number of graded rows.

    When the git-log walk's fallback applies, a slice's sheet can hold only
    its final attempt's row even though
    PM actually ran many more attempts; `grade_run.py`'s fallback path still
    grades that row under its correct, true final ordinal
    (`bench_lib.attempt_ordinal`/`gradeable_slice_targets`), so the highest
    `attempt` value present is always the true attempt count regardless of
    how many rows the walk recovered. Counting rows instead would silently
    undercount every slice that fell back.
    """
    attempts = sheet.get("attempts") or []
    if not attempts:
        return 0
    return max(a["attempt"] for a in attempts) + 1


def slice_reviews(sheet: dict[str, Any]) -> list[dict[str, Any]]:
    """Every review commission recorded across this slice's attempts, as a
    flat list -- one entry per commission, a straight reshape of the
    sheet's own per-attempt `reviews` list with no new derivation.

    An attempt with no commissions at all contributes nothing (there is no
    per-field placeholder to omit any more -- `attempt_trajectory`'s own
    `commissioned_reviews` already represents "nothing commissioned" for
    every attempt, reviewed or not).

    Sorted by `attempt` explicitly rather than trusting sheet-file order:
    dev_check.py's upsert appends new entries rather than inserting them in
    sorted position, so a slice graded manually out of sequence (see
    README's "callable directly for a manual/ad-hoc grade") would otherwise
    emit an out-of-sequence list. Within one attempt, records are
    read in the order review_score.py's `upsert_sheet` already keeps them
    (sorted by `event_index`); the renderer (`leaderboard.py`'s
    `_review_history_table`) re-sorts by `event_index` across the whole
    slice for actual display order regardless.
    """
    entries: list[dict[str, Any]] = []
    ordered_attempts = sorted(sheet.get("attempts") or [], key=lambda a: a.get("attempt"))
    for attempt in ordered_attempts:
        for record in attempt.get("reviews") or []:
            entries.append(_review_entry(attempt.get("attempt"), record))
    return entries


def _size_complexity_trajectory_summary(attempt: dict[str, Any]) -> dict[str, Any]:
    """A compact per-attempt ΔLOC/ΔCC summary for `attempt_trajectory` below
    -- production net lines and net cyclomatic complexity plus each
    measurement's own availability, read straight from the attempt's own
    `size_complexity` block.

    Deliberately not a second copy of the whole block: the full buckets
    (test/doc deltas, binary-file lists, baseline/endpoint totals, function
    counts, coverage notes) stay only in `first_attempt`/`final_attempt`'s
    full attempt dicts (and in the sheet itself) -- this is a summary for a
    trajectory row, not a duplicate of what `dev_check.py` already computed.
    """
    size_complexity = attempt.get("size_complexity") or {}
    loc = size_complexity.get("loc") or {}
    complexity = size_complexity.get("complexity") or {}
    loc_available = bool(loc.get("available"))
    cc_available = bool(complexity.get("available"))
    production_loc = (loc.get("buckets") or {}).get("production") or {}
    production_cc = complexity.get("production") or {}
    return {
        "loc_available": loc_available,
        "production_loc_net": production_loc.get("net") if loc_available else None,
        "cc_available": cc_available,
        "production_cc_net": production_cc.get("net") if cc_available else None,
    }


def attempt_trajectory(sheet: dict[str, Any]) -> list[dict[str, Any]]:
    """A compact, one-row-per-attempt summary of every Developer attempt
    this sheet has a row for -- including an attempt that PM steered with
    no review commissioned at all. `slice_reviews` (above) only ever lists
    attempts that DID commission a review, so it cannot show this by itself.

    Deliberately not a second copy of the bulky per-attempt payload --
    `quality` (lint/code-health findings) and `scope` stay only in
    `first_attempt`/`final_attempt`'s full blocks (and in the sheet itself).
    `correctness` is carried through here with its `by_node` map dropped
    (`_correctness_without_by_node`): `by_node` is per-run evidence kept
    only on the scoring sheet, and this function has no attempt number to
    excuse repeating it once per trajectory row on top of `first_attempt`/
    `final_attempt`. `hidden_tests_passed`/`hidden_tests_total`/
    `by_obligation` are unaffected. Reducing correctness to a single
    fraction here would be inventing scoring math, which this module's own
    docstring forbids -- that reduction is `leaderboard.py`'s job, driven
    by `policy.yaml`. The one node map this report does carry is the
    per-slice `first_attempt_node_outcomes` (see `build_report`), nested by
    obligation group rather than repeated per attempt.

    `size_complexity` is a compact per-row ΔLOC/ΔCC summary (see
    `_size_complexity_trajectory_summary`), not the full block.

    `pm_developer_judgment` is NOT set here (this function has no
    `run_dir`/events access to do the join with) -- it is stamped onto
    every entry afterward, by `resolve_pm_judgments`, once `build_report`
    has this whole trajectory list to look up attempt ordinals against. An
    attempt PM never rated while it was current is
    `pm_developer_judgment: {"status": "unjudged", ...}` -- a REAL gap, not
    an inferred one: `pm_lib` refuses historical backfill by construction,
    so there is no way to retroactively rate an attempt PM didn't rate at
    the time.

    `commissioned_reviews` carries each commission's real `review_id` and
    `event_index`, alongside its `skill`, one entry per commission on this
    attempt (a panel or a retry both showing up here, exactly as they do in
    `slice_reviews`).

    Per AGENTS.md ("never write a partial result as if it were complete"),
    an absent column is left out of every row instead of a fabricated
    `None` repeated everywhere.
    """
    ordered_attempts = sorted(sheet.get("attempts") or [], key=lambda a: a.get("attempt"))
    trajectory: list[dict[str, Any]] = []
    for attempt in ordered_attempts:
        commissioned_reviews = [
            {
                "skill": record.get("skill"),
                "review_id": record.get("review_id"),
                "event_index": record.get("event_index"),
            }
            for record in attempt.get("reviews") or []
        ]
        trajectory.append(
            {
                "attempt": attempt.get("attempt"),
                "pm_attempts_counter": attempt.get("pm_attempts_counter"),
                "commit_sha": attempt.get("commit_sha"),
                "correctness": _correctness_without_by_node(attempt),
                "size_complexity": _size_complexity_trajectory_summary(attempt),
                "pm_decision": attempt.get("pm_decision"),
                "commissioned_reviews": commissioned_reviews,
            }
        )
    return trajectory


def _parse_event_timestamp(value: Any) -> datetime | None:
    """Parse one `events.jsonl` `ts` value into an offset-aware UTC
    `datetime`, or None if it cannot be trusted.

    Every real timestamp in this cohort is a bare `Z`-suffixed ISO-8601
    string (`datetime.fromisoformat` does not accept a literal trailing
    `Z` on the Python versions this repo has run under, hence the
    substitution). An offset-naive result (a malformed value missing its
    'Z'/offset entirely) is refused, not assumed to be UTC -- guessing a
    timezone for a corrupted timestamp is exactly the kind of silent guess
    AGENTS.md forbids.
    """
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


# pm_status -> the events.jsonl event `kind` that marks this run's end, one
# of run_status.pm_status's four values. Only these two are ever a
# finished run's terminal state ("active"/"needs-human"
# have no terminal event yet -- timing is honestly unavailable, not an
# error, for either).
_TERMINAL_EVENT_KIND_BY_PM_STATUS = {"complete": "complete", "stopped": "stop"}


def resolve_run_timing(run_dir: Path | None, pm_status: str | None) -> tuple[dict[str, Any], list[str]]:
    """Elapsed wall-clock time for this PM run, in seconds, from `init` to
    the terminal event matching `pm_status` -- never a sheet timestamp,
    which records grading time (`dev_check.py`'s `utc_now_iso()`), not when
    PM actually ran.

    A run can carry a `complete` event followed by a later, routine `stop`
    event (e.g. a top-level stop issued after the run had already
    finished); looking the terminal event up by matching `pm_status`
    (rather than "the last of complete/stop") is what keeps such a trailing
    event from extending the measured span.

    Returns:
        (timing, problems). `timing["available"]` is False with a named
        `reason` for every honest gap (no `run_dir` given, run not yet
        finished, missing/duplicate init or terminal events, an unparsable
        timestamp, or a negative span) -- `problems` is only ever non-empty
        for a *genuine* data problem (a finished run whose log is
        malformed), never for the ordinary "no --run-dir given" or
        "run not finished yet" cases, which are not errors.
    """
    if run_dir is None:
        return {"available": False, "reason": "no --run-dir given; events.jsonl was not read"}, []

    events_path = run_dir / "events.jsonl"
    try:
        events = bench_lib.read_events(run_dir)
    except bench_lib.BenchLibError as exc:
        problem = f"could not read {events_path} for run timing: {exc}"
        return {"available": False, "reason": problem}, [problem]
    if not events:
        problem = f"no events found at {events_path}; run timing cannot be computed"
        return {"available": False, "reason": problem}, [problem]

    terminal_kind = _TERMINAL_EVENT_KIND_BY_PM_STATUS.get(pm_status)
    if terminal_kind is None:
        return {"available": False, "reason": f"run not finished (pm_status={pm_status!r})"}, []

    init_events = [e for e in events if e.get("kind") == "init"]
    terminal_events = [e for e in events if e.get("kind") == terminal_kind]
    if len(init_events) != 1 or len(terminal_events) != 1:
        problem = (
            f"{events_path}: expected exactly one 'init' and one {terminal_kind!r} event for a "
            f"pm_status={pm_status!r} run, found {len(init_events)} init and {len(terminal_events)} {terminal_kind!r}"
        )
        return {"available": False, "reason": problem}, [problem]

    init_at = init_events[0].get("ts")
    terminal_at = terminal_events[0].get("ts")
    init_dt = _parse_event_timestamp(init_at)
    terminal_dt = _parse_event_timestamp(terminal_at)
    if init_dt is None or terminal_dt is None:
        problem = f"{events_path}: 'init' or {terminal_kind!r} event has an unparsable or offset-naive timestamp"
        return {"available": False, "reason": problem}, [problem]

    elapsed_seconds = (terminal_dt - init_dt).total_seconds()
    if elapsed_seconds < 0:
        problem = (
            f"{events_path}: {terminal_kind!r} event ({terminal_at}) precedes 'init' ({init_at}) -- "
            "refusing a negative elapsed duration"
        )
        return {"available": False, "reason": problem}, [problem]

    return {
        "available": True,
        "init_at": init_at,
        "terminal_at": terminal_at,
        "terminal_kind": terminal_kind,
        "elapsed_seconds": elapsed_seconds,
    }, []


def resolve_run_provenance(run_dir: Path | None) -> tuple[dict[str, Any], list[str]]:
    """This run's recorded branch and original Developer worktree path, plus
    whether that worktree is still present on disk *as of this report's own
    generation* -- `leaderboard.py`'s run index needs all three, alongside
    the PM artifact location.

    Read straight from `run.json` in `run_dir` -- still read-only, no
    write, the same PM-directory access `resolve_run_timing` already makes
    for the `timing` block.

    "Presence-as-of-generation" is a plain, timestamped filesystem check at
    the moment this report is built -- absence here is a real observation,
    but is NOT proof `cohort_run.py cleanup` ran: the worktree could just as
    easily have been removed by hand, or never existed at this path on this
    machine at all (a report regenerated somewhere other than where the run
    happened).

    Returns:
        (provenance, problems). `provenance["available"]` is False with a
        named `reason` when `run_dir` is None or `run.json` cannot be read
        -- the latter is a genuine problem (named in `problems`) since
        `run_dir` was explicitly given; the former is the ordinary,
        expected shape of an ad hoc `--run-id`-only invocation, not an
        error.
    """
    if run_dir is None:
        return {"available": False, "reason": "no --run-dir given; run.json was not read", "pm_run_dir": None}, []

    run_json_path = run_dir / "run.json"
    try:
        run_state = json.loads(run_json_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        problem = f"no run.json found at {run_json_path}; run provenance cannot be recorded"
        return {"available": False, "reason": problem, "pm_run_dir": str(run_dir)}, [problem]
    except json.JSONDecodeError as exc:
        problem = f"invalid JSON in {run_json_path}: {exc}"
        return {"available": False, "reason": problem, "pm_run_dir": str(run_dir)}, [problem]

    repo = run_state.get("repo")
    branch = run_state.get("branch")
    return {
        "available": True,
        "repo": repo,
        "branch": branch,
        "repo_present_as_of_generation": Path(repo).is_dir() if repo else None,
        "pm_run_dir": str(run_dir),
    }, []


def _unjudged_pm_judgment() -> dict[str, Any]:
    """The explicit 'PM never rated this' marker -- the one shape shared by a review's
    `pm_rating` and an attempt's `pm_developer_judgment` before (or absent)
    a real join: `{"status": "unjudged", "score": None, "reason": None,
    "at": None, "judgment_id": None}`.

    `resolve_pm_judgments` stamps a FRESH copy of this onto every review and
    every trajectory entry before it ever looks at run.json, so a read
    failure (or no `run_dir` at all) still leaves every entry explicitly
    labelled -- never merely absent (AGENTS.md: "never write a partial
    result as if it were complete"). A fresh dict per call matters: reusing
    one dict object across every entry would make writing a real judgment
    onto one entry silently overwrite every other entry's default too.
    """
    return {"status": "unjudged", "score": None, "reason": None, "at": None, "judgment_id": None}


def _pm_judgments_unavailable(reason: str) -> dict[str, Any]:
    """The run-level `pm_judgments` block's shape when it could not be read
    at all (no `run_dir`, or run.json/events.jsonl unreadable) -- distinct
    from a run.json that was read fine but simply carries no judgments
    anywhere (a run predating PM's judgment feature): that case is still
    `"available": True`, with both `..._recorded` flags False (see
    `resolve_pm_judgments`)."""
    return {
        "available": False,
        "reason": reason,
        "review_judgments_recorded": False,
        "developer_judgments_recorded": False,
        "comparisons": [],
    }


def _describe_dangling_review_id(
    rid: Any,
    *,
    run_id: str,
    slice_id: str,
    judgment_id: Any,
    run_slice_reviews: list[dict[str, Any]],
    events: list[dict[str, Any]],
    trajectory_by_slice_and_attempt: dict[tuple[str, Any], dict[str, Any]],
) -> str:
    """A `review_id` a judgment names that has no match in this report's own
    harvested `reviews` -- distinguish the three structurally distinct
    reasons that can happen, rather than one alarming catch-all, by naming
    exactly which of PM's own `run.json` facts explains it.

    1. **Coverage consequence (non-alarming).** `run_slice_reviews` (run.json's
       own `slices[].reviews[]` for this slice) DOES carry a record for
       `rid`, but the attempt it belongs to was never graded. `grade_run.py`
       only walks a slice's full attempt history when the Developer held one
       commit per attempt; when it doesn't, only the slice's FINAL attempt
       is graded, and every review commissioned against an earlier attempt
       has no scoring-sheet row to harvest a `reviews` entry from -- so it
       can never appear in `reviews_by_slice_and_id` no matter how
       faithfully this report reads `run.json`. This is expected, not a
       bug. (Comparison
       members on an ungraded attempt do NOT land here: they resolve
       through `_resolve_comparison_member`, which needs only the
       reviewer's identity and so reads run.json directly.)
    2. **Genuine harvest anomaly (alarming).** `run_slice_reviews` carries a
       record for `rid`, ITS attempt WAS graded, and yet no harvested
       `reviews` entry matches -- `review_score.py` should have produced one
       and, for some reason, did not.
    3. **Dangling reference in PM's own state (alarming).** `rid` does not
       appear in `run_slice_reviews` at all -- PM's judgment names a review
       id its own `run.json` never recorded.

    The `rid` -> attempt-ordinal conversion mirrors `_apply_developer_judgment`
    exactly: `bench_lib.attempt_ordinal(events, slice_id, before_index=
    origin_event["index"] + 1)`. The `+1` is load-bearing here for the same
    reason it is there (see `resolve_pm_judgments`'s docstring for the full
    proof) -- `origin_event` IS the launch-family event that OPENED the
    attempt the review ran against, and `attempt_ordinal`'s `before_index`
    counts events strictly BEFORE it, so the window must include the origin
    event itself or the ordinal resolves to the attempt before the one the
    review actually belongs to.

    "Was that attempt graded" is answered from `trajectory_by_slice_and_attempt`
    -- this report's own already-built `attempt_trajectory` rows -- never by
    re-reading a sheet from disk: a slice's scoring sheet holds exactly the
    attempts `grade_run.py`/`dev_check.py` graded, so an ordinal missing from
    that map IS an ungraded attempt, structurally.

    If the ordinal cannot be determined at all (no matching `run_slice_reviews`
    record's `origin_event.index`, or `attempt_ordinal` itself raises), this
    falls back to a named "could not determine" wording -- it never guesses
    case 1, per this task's own instruction not to assume the benign case
    without structural proof.
    """
    matching = [r for r in run_slice_reviews if r.get("review_id") == rid]
    if not matching:
        return (
            f"run {run_id} slice {slice_id!r} judgment {judgment_id!r}: names review_id {rid!r}, which does "
            "not appear anywhere in run.json's own reviews[] for this slice -- PM's judgment names a review "
            "its own recorded state never produced"
        )

    # `review_id` is unique within one slice, so `matching` normally holds
    # exactly one record; the last is taken so that a slice which somehow
    # recorded the id twice is read as its latest state rather than its
    # first, matching how every other supersession in this bench resolves.
    origin_event = matching[-1].get("origin_event") or {}
    origin_index = origin_event.get("index")
    if origin_index is None:
        return (
            f"run {run_id} slice {slice_id!r} judgment {judgment_id!r}: names review_id {rid!r}, recorded in "
            "run.json but with no origin_event.index -- could not determine whether its attempt was graded"
        )
    try:
        attempt_ordinal = bench_lib.attempt_ordinal(events, slice_id, before_index=origin_index + 1)
    except bench_lib.BenchLibError as exc:
        return (
            f"run {run_id} slice {slice_id!r} judgment {judgment_id!r}: names review_id {rid!r}; could not "
            f"resolve its recorded origin_event.index={origin_index} to an attempt ordinal: {exc}"
        )

    if (slice_id, attempt_ordinal) not in trajectory_by_slice_and_attempt:
        return (
            f"run {run_id} slice {slice_id!r} judgment {judgment_id!r}: names review_id {rid!r}, commissioned "
            f"against attempt {attempt_ordinal}, which has no scoring-sheet row in this report -- an ungraded "
            "attempt has nothing for this judgment to join to (a coverage gap, not a harvest bug; "
            "grade_run.py's own output for the slice says why the attempt went ungraded)"
        )

    return (
        f"run {run_id} slice {slice_id!r} judgment {judgment_id!r}: names review_id {rid!r}, commissioned "
        f"against attempt {attempt_ordinal}, which WAS graded, yet no harvested review matches it -- "
        "review_score.py should have produced a reviews entry for this attempt and did not"
    )


def _resolve_comparison_member(
    rid: Any,
    *,
    skill: Any,
    run_id: str,
    slice_id: str,
    judgment_id: Any,
    reviews_by_slice_and_id: dict[tuple[str, Any], dict[str, Any]],
    run_slice_reviews: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, str | None]:
    """Resolve one `rank_groups` member to the reviewer identity that earned
    its rank points, joining on `(run_id, slice.id, review_id)` exactly as a
    rating does -- never list position, model, or artifact content.

    A comparison needs something a rating does not: only the reviewer's
    IDENTITY, never a harvested record to hang a `pm_rating` on. So this
    deliberately reads `run_slice_reviews` (run.json's own `slices[].reviews[]`,
    which records `tool`/`model`/`effort` for every commission PM ever made)
    rather than requiring the report's own harvested `reviews` entry the way
    `_resolve_review_for_judgment` must.

    That distinction is load-bearing. When a slice's attempt history doesn't
    satisfy the git-log walk's one-commit-per-attempt convention, only its
    final attempt is graded, so an earlier comparison round's reviews can
    have no scoring-sheet rows at all. Resolving identity through harvested
    records alone would drop every member of that round, vanishing the
    round entirely -- scoring the panel over fewer than the comparisons PM
    actually made and letting a *Developer* property (commit habits)
    silently contaminate a *reviewer* metric. Identity is always
    recoverable from run.json directly, independent of grading coverage.

    Dropping members one at a time is worse than dropping the round: it
    renormalizes `(N-r)/(N-1)` over a panel size PM never compared at,
    fabricating rank points. Resolving identity structurally means a member
    is only ever unresolvable when PM's own state never recorded that
    review at all -- a real error, reported as one.

    Returns:
        (identity, None), or (None, problem) naming the run, slice, judgment
        and review id. Never raises.
    """
    harvested = reviews_by_slice_and_id.get((slice_id, rid))
    recorded = [r for r in run_slice_reviews if r.get("review_id") == rid]
    if not recorded and harvested is None:
        return None, (
            f"run {run_id} slice {slice_id!r} judgment {judgment_id!r}: comparison names review_id {rid!r}, "
            "which appears neither among this slice's harvested reviews nor anywhere in run.json's own "
            "reviews[] for this slice -- PM compared a review its own recorded state never produced"
        )
    source = recorded[-1] if recorded else harvested
    assert source is not None  # guaranteed by the guard above; narrows the type
    recorded_skill = source.get("skill")
    if recorded_skill != skill:
        return None, (
            f"run {run_id} slice {slice_id!r} judgment {judgment_id!r}: comparison recorded skill {skill!r} "
            f"disagrees with review {rid!r}'s own skill {recorded_skill!r}"
        )
    return (
        {"review_id": rid, "tool": source.get("tool"), "model": source.get("model"), "effort": source.get("effort")},
        None,
    )


def _resolve_review_for_judgment(
    rid: Any,
    *,
    skill: Any,
    run_id: str,
    slice_id: str,
    judgment_id: Any,
    reviews_by_slice_and_id: dict[tuple[str, Any], dict[str, Any]],
    run_slice_reviews: list[dict[str, Any]],
    events: list[dict[str, Any]],
    trajectory_by_slice_and_attempt: dict[tuple[str, Any], dict[str, Any]],
) -> tuple[dict[str, Any] | None, str | None]:
    """Look `rid` up among THIS report's own already-harvested `reviews`
    entries for `slice_id` (never run.json's own `reviews[]` list, and never
    list position/model/artifact content -- the join key is exactly
    `(run_id, slice.id, review_id)`). Also checks the judgment's own
    `skill` agrees with the joined review's recorded skill.

    A miss here is resolved to one of three structurally distinct reasons by
    `_describe_dangling_review_id` (never guessed) -- `run_slice_reviews`,
    `events` and `trajectory_by_slice_and_attempt` exist on this function
    purely to feed that resolution.

    Returns:
        (review, None) on a clean join, or (None, problem) naming the run,
        slice, judgment id and what was found -- never raises: a malformed
        or dangling judgment record is real cohort data to report on, not a
        reason to abort the whole harvest.
    """
    review = reviews_by_slice_and_id.get((slice_id, rid))
    if review is None:
        return None, _describe_dangling_review_id(
            rid,
            run_id=run_id,
            slice_id=slice_id,
            judgment_id=judgment_id,
            run_slice_reviews=run_slice_reviews,
            events=events,
            trajectory_by_slice_and_attempt=trajectory_by_slice_and_attempt,
        )
    if review.get("skill") != skill:
        return None, (
            f"run {run_id} slice {slice_id!r} judgment {judgment_id!r}: recorded skill {skill!r} disagrees "
            f"with review {rid!r}'s own skill {review.get('skill')!r}"
        )
    return review, None


def _apply_review_judgment(
    judgment: dict[str, Any],
    *,
    run_id: str,
    slice_id: str,
    reviews_by_slice_and_id: dict[tuple[str, Any], dict[str, Any]],
    comparisons: list[dict[str, Any]],
    run_slice_reviews: list[dict[str, Any]],
    events: list[dict[str, Any]],
    trajectory_by_slice_and_attempt: dict[tuple[str, Any], dict[str, Any]],
) -> list[str]:
    """Join one active `review_judgments` record: a rating (shape A) or an
    unavailable rating (shape C) mutates the matching review's `pm_rating`
    in place; a comparison (shape B) is appended, with every named reviewer
    identity resolved, onto `comparisons`. See `resolve_pm_judgments` for
    the three shapes' exact keys.

    `run_slice_reviews`, `events` and `trajectory_by_slice_and_attempt` are
    passed straight through to `_resolve_review_for_judgment` -- they exist
    only so a dangling `review_id` can be diagnosed against run.json's own
    state rather than reported with one generic message (see
    `_describe_dangling_review_id`).

    Returns a list of named problems (possibly empty) -- never raises.
    """
    problems: list[str] = []
    judgment_id = judgment.get("judgment_id")
    skill = judgment.get("skill")
    assessment = judgment.get("assessment")

    if assessment == "comparison":
        rank_groups = judgment.get("rank_groups")
        if not isinstance(rank_groups, list) or not rank_groups:
            problems.append(
                f"run {run_id} slice {slice_id!r} judgment {judgment_id!r}: comparison judgment has no "
                "rank_groups list"
            )
            return problems
        resolved_groups: list[list[dict[str, Any]]] = []
        for group in rank_groups:
            resolved_group: list[dict[str, Any]] = []
            for rid in group if isinstance(group, list) else []:
                identity, problem = _resolve_comparison_member(
                    rid, skill=skill, run_id=run_id, slice_id=slice_id, judgment_id=judgment_id,
                    reviews_by_slice_and_id=reviews_by_slice_and_id, run_slice_reviews=run_slice_reviews,
                )
                if problem is not None:
                    problems.append(problem)
                    continue
                resolved_group.append(identity)
            resolved_groups.append(resolved_group)
        comparisons.append(
            {
                "slice": slice_id,
                "skill": skill,
                "judgment_id": judgment_id,
                "at": judgment.get("at"),
                "reason": judgment.get("reason"),
                "rank_groups": resolved_groups,
            }
        )
        return problems

    if assessment != "rating":
        problems.append(
            f"run {run_id} slice {slice_id!r} judgment {judgment_id!r}: unrecognised review_judgments "
            f"assessment {assessment!r} (expected 'rating' or 'comparison')"
        )
        return problems

    if judgment.get("status") == "unavailable":
        # Shape C: PM could not rate this review at all (a real reliability
        # outcome, e.g. a reviewer subprocess that never produced a report)
        # -- `review_ids` (plural) names every review this single judgment
        # covers.
        rids = judgment.get("review_ids")
        if not isinstance(rids, list) or not rids:
            problems.append(
                f"run {run_id} slice {slice_id!r} judgment {judgment_id!r}: unavailable rating judgment has "
                "no review_ids list"
            )
            return problems
        for rid in rids:
            review, problem = _resolve_review_for_judgment(
                rid, skill=skill, run_id=run_id, slice_id=slice_id, judgment_id=judgment_id,
                reviews_by_slice_and_id=reviews_by_slice_and_id, run_slice_reviews=run_slice_reviews,
                events=events, trajectory_by_slice_and_attempt=trajectory_by_slice_and_attempt,
            )
            if problem is not None:
                problems.append(problem)
                continue
            if review["pm_rating"]["status"] != "unjudged":
                problems.append(
                    f"run {run_id} slice {slice_id!r} review {rid!r}: duplicate PM judgment "
                    f"({review['pm_rating'].get('judgment_id')!r} and {judgment_id!r})"
                )
                continue
            review["pm_rating"] = {
                "status": "unavailable",
                "score": None,
                "reason": judgment.get("reason"),
                "at": judgment.get("at"),
                "judgment_id": judgment_id,
            }
        return problems

    # Shape A: a real 0/1/2 rating of exactly one review.
    rid = judgment.get("review_id")
    if rid is None:
        problems.append(f"run {run_id} slice {slice_id!r} judgment {judgment_id!r}: rating judgment has no review_id")
        return problems
    if "score" not in judgment:
        problems.append(f"run {run_id} slice {slice_id!r} judgment {judgment_id!r}: rating judgment has no score")
        return problems
    review, problem = _resolve_review_for_judgment(
        rid, skill=skill, run_id=run_id, slice_id=slice_id, judgment_id=judgment_id,
        reviews_by_slice_and_id=reviews_by_slice_and_id, run_slice_reviews=run_slice_reviews,
        events=events, trajectory_by_slice_and_attempt=trajectory_by_slice_and_attempt,
    )
    if problem is not None:
        problems.append(problem)
        return problems
    if review["pm_rating"]["status"] != "unjudged":
        problems.append(
            f"run {run_id} slice {slice_id!r} review {rid!r}: duplicate PM rating "
            f"({review['pm_rating'].get('judgment_id')!r} and {judgment_id!r})"
        )
        return problems
    review["pm_rating"] = {
        "status": "rated",
        "score": judgment.get("score"),
        "reason": judgment.get("reason"),
        "at": judgment.get("at"),
        "judgment_id": judgment_id,
    }
    return problems


def _apply_developer_judgment(
    judgment: dict[str, Any],
    *,
    run_id: str,
    slice_id: str,
    events: list[dict[str, Any]],
    trajectory_by_slice_and_attempt: dict[tuple[str, Any], dict[str, Any]],
) -> list[str]:
    """Join one active `developer_judgments` record onto the
    `attempt_trajectory` entry for the attempt it judged (mutating that
    entry's `pm_developer_judgment` in place). See `resolve_pm_judgments`'s
    own docstring for the `+1` ordinal conversion this depends on -- and for
    why that is not the plan's literal wording.

    Returns a list of named problems (possibly empty) -- never raises.
    """
    problems: list[str] = []
    judgment_id = judgment.get("judgment_id")
    submission = judgment.get("submission") or {}
    origin_event = submission.get("origin_event") or {}
    origin_index = origin_event.get("index")
    if origin_index is None:
        problems.append(
            f"run {run_id} slice {slice_id!r} judgment {judgment_id!r}: developer judgment has no "
            "submission.origin_event.index"
        )
        return problems
    origin_slice = origin_event.get("slice")
    if origin_slice is not None and origin_slice != slice_id:
        problems.append(
            f"run {run_id} slice {slice_id!r} judgment {judgment_id!r}: submission.origin_event.slice="
            f"{origin_slice!r} disagrees with this judgment's own slice {slice_id!r}"
        )
        return problems

    if origin_index not in bench_lib.launch_family_indices(events, slice_id):
        problems.append(
            f"run {run_id} slice {slice_id!r} judgment {judgment_id!r}: submission.origin_event.index="
            f"{origin_index} is not a launch/relaunch/steer event for this slice -- refusing to guess an "
            "attempt ordinal from it"
        )
        return problems

    try:
        # The +1 (see resolve_pm_judgments's own docstring): origin_event IS
        # the launch-family event that OPENS the attempt being judged, and
        # attempt_ordinal's before_index counts events strictly BEFORE it --
        # so the window must be made inclusive of the origin event itself,
        # or the strict form would resolve to the attempt before the one PM
        # actually judged (or raise outright, when the origin event is a
        # slice's only launch-family event recorded so far).
        attempt_ordinal = bench_lib.attempt_ordinal(events, slice_id, before_index=origin_index + 1)
    except bench_lib.BenchLibError as exc:
        problems.append(f"run {run_id} slice {slice_id!r} judgment {judgment_id!r}: {exc}")
        return problems

    trajectory_entry = trajectory_by_slice_and_attempt.get((slice_id, attempt_ordinal))
    if trajectory_entry is None:
        problems.append(
            f"run {run_id} slice {slice_id!r} judgment {judgment_id!r}: resolves to attempt {attempt_ordinal}, "
            "which has no scoring-sheet row in this report"
        )
        return problems
    if "score" not in judgment:
        problems.append(
            f"run {run_id} slice {slice_id!r} judgment {judgment_id!r}: developer judgment has no score"
        )
        return problems
    if trajectory_entry["pm_developer_judgment"]["status"] != "unjudged":
        existing = trajectory_entry["pm_developer_judgment"]
        problems.append(
            f"run {run_id} slice {slice_id!r} attempt {attempt_ordinal}: duplicate PM developer judgment "
            f"({existing.get('judgment_id')!r} and {judgment_id!r})"
        )
        return problems
    trajectory_entry["pm_developer_judgment"] = {
        "status": "rated",
        "score": judgment.get("score"),
        "reason": judgment.get("reason"),
        "at": judgment.get("at"),
        "judgment_id": judgment_id,
    }
    return problems


def resolve_pm_judgments(
    run_dir: Path | None, run_id: str, slices: list[dict[str, Any]]
) -> tuple[dict[str, Any], list[str]]:
    """Harvest PM's own structured judgments and join them onto this
    report's own already-built `slices` -- mutating each `reviews` entry's
    `pm_rating` and each `attempt_trajectory` entry's `pm_developer_judgment`
    in place -- and returning a run-level block carrying PM's comparative
    judgments plus both collections' availability, so `leaderboard.py` can
    build its tables without re-reading `run.json` (see this module's own
    top-of-file docstring for why this harvest lives here rather than in
    review_score.py).

    Every read here is read-only against `run.json`/`events.jsonl` -- no PM
    state is ever written, matching `resolve_run_timing`/
    `resolve_run_provenance`'s identical access pattern immediately above.

    **Join keys:**

    - Reviewer: `(run_id, slice.id, review_id)`, matched against THIS
      report's own already-built `reviews` entries -- never run.json's own
      `reviews[]` list, list position, model, or artifact content. Every
      real `review_id` on a report `reviews` entry comes straight from
      review_score.py's harvest (null on a sheet graded before that harvest
      existed, in which case it simply never matches anything).
    - Developer: `(run_id, slice.id, submission.origin_event.index)`,
      converted to this bench's own attempt ordinal via
      `bench_lib.attempt_ordinal(events, slice_id, before_index=
      origin_event["index"] + 1)`.

      **The `+1` is load-bearing.** `submission.origin_event` IS the
      launch/relaunch/steer event that OPENED the attempt PM is judging;
      `attempt_ordinal`'s `before_index` counts events strictly BEFORE it.
      The strict (no `+1`) form therefore excludes the very event that
      opens the attempt being judged, which either resolves to the WRONG
      (previous) attempt or raises outright when that origin event is a
      slice's only launch-family event recorded so far.

      Before converting, `origin_event["index"]` is checked against
      `bench_lib.launch_family_indices` for that slice -- an index that
      isn't actually a launch-family event would otherwise silently resolve
      to a plausible-looking but wrong ordinal instead of a named error.

    **Validation is loud, per AGENTS.md ("fail loudly and specifically")**
    -- every case below is a named problem (naming this run's id, the
    slice, the judgment id, and what was found), never a silently dropped
    judgment and never a raised exception (a malformed judgment record is
    real cohort data this tool must still report on, not a reason to abort
    the whole harvest): an unknown `review_id`; a `rank_groups` entry
    naming a review that does not exist; a judgment's own `skill`
    disagreeing with the joined review's recorded skill; a duplicate rating
    for one review or one attempt; a malformed record missing a key its own
    shape requires; an `origin_event` that isn't a launch-family event; and
    a judgment recorded for a slice this report has no scoring-sheet
    coverage for at all (a coverage gap, kept distinct from "unknown
    review_id" -- that's a dangling reference on a KNOWN slice, this is
    judgments for a slice never graded here).

    Returns:
        (block, problems). `block["available"]` is False (with a named
        `reason`) only when `run_dir` is None or run.json/events.jsonl could
        not be read at all. A run.json that reads fine but simply carries no
        `review_judgments`/`developer_judgments` anywhere (a run predating
        PM's judgment feature) is still `"available": True`, with both
        `..._recorded` flags False -- an honest labelled absence, never an
        error.
        `block["comparisons"]` is every active comparison judgment, with
        each named reviewer identity resolved through the joined reviews,
        so a renderer never has to re-resolve a `review_id` itself.
    """
    # Stamped BEFORE run_dir is even looked at, so every entry carries an
    # explicit label regardless of whether judgments could be read at all
    # (AGENTS.md: "never write a partial result as if it were complete").
    # "A review PM never judged is explicitly unjudged, never inferred as
    # anything" applies just as much to a run with no run_dir at all as to
    # one that was read but simply named no judgment for this entry.
    for slice_entry in slices:
        for review in slice_entry.get("reviews") or []:
            review["pm_rating"] = _unjudged_pm_judgment()
        for attempt in slice_entry.get("attempt_trajectory") or []:
            attempt["pm_developer_judgment"] = _unjudged_pm_judgment()

    if run_dir is None:
        return (
            _pm_judgments_unavailable("no --run-dir given; run.json/events.jsonl were not read for PM judgments"),
            [],
        )

    run_json_path = run_dir / "run.json"
    try:
        run_state = json.loads(run_json_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        problem = f"no run.json found at {run_json_path}; PM judgments cannot be harvested"
        return _pm_judgments_unavailable(problem), [problem]
    except json.JSONDecodeError as exc:
        problem = f"invalid JSON in {run_json_path}: {exc}"
        return _pm_judgments_unavailable(problem), [problem]

    events_path = run_dir / "events.jsonl"
    try:
        events = bench_lib.read_events(run_dir)
    except bench_lib.BenchLibError as exc:
        problem = f"could not read {events_path} for PM judgments: {exc}"
        return _pm_judgments_unavailable(problem), [problem]

    problems: list[str] = []
    comparisons: list[dict[str, Any]] = []
    review_judgments_recorded = False
    developer_judgments_recorded = False

    known_slice_ids = {f"Slice {s['slice']}" for s in slices if s.get("slice") is not None}
    reviews_by_slice_and_id: dict[tuple[str, Any], dict[str, Any]] = {}
    trajectory_by_slice_and_attempt: dict[tuple[str, Any], dict[str, Any]] = {}
    for slice_entry in slices:
        slice_id = f"Slice {slice_entry['slice']}"
        for review in slice_entry.get("reviews") or []:
            rid = review.get("review_id")
            if rid is not None:
                reviews_by_slice_and_id[(slice_id, rid)] = review
        for attempt in slice_entry.get("attempt_trajectory") or []:
            trajectory_by_slice_and_attempt[(slice_id, attempt.get("attempt"))] = attempt

    for run_slice in run_state.get("slices") or []:
        if not isinstance(run_slice, dict):
            continue
        slice_id = run_slice.get("id")
        if slice_id is None:
            continue
        review_judgments = run_slice.get("review_judgments") or []
        developer_judgments = run_slice.get("developer_judgments") or []
        if not review_judgments and not developer_judgments:
            continue
        if slice_id not in known_slice_ids:
            # A real PM judgment for a slice this report never graded --
            # distinct from "unknown review_id" (a dangling reference on a
            # KNOWN slice): this is a coverage gap, not a corrupted
            # reference, so it gets its own message.
            problems.append(
                f"run {run_id}: PM judgments recorded for slice {slice_id!r}, which has no scoring-sheet "
                "coverage in this report -- those judgments could not be joined to anything"
            )
            continue

        if review_judgments:
            review_judgments_recorded = True
        run_slice_reviews = run_slice.get("reviews") or []
        for judgment in bench_lib.active_judgments(review_judgments):
            problems.extend(
                _apply_review_judgment(
                    judgment, run_id=run_id, slice_id=slice_id,
                    reviews_by_slice_and_id=reviews_by_slice_and_id, comparisons=comparisons,
                    run_slice_reviews=run_slice_reviews, events=events,
                    trajectory_by_slice_and_attempt=trajectory_by_slice_and_attempt,
                )
            )

        if developer_judgments:
            developer_judgments_recorded = True
        for judgment in bench_lib.active_judgments(developer_judgments):
            problems.extend(
                _apply_developer_judgment(
                    judgment, run_id=run_id, slice_id=slice_id, events=events,
                    trajectory_by_slice_and_attempt=trajectory_by_slice_and_attempt,
                )
            )

    return {
        "available": True,
        "reason": None,
        "review_judgments_recorded": review_judgments_recorded,
        "developer_judgments_recorded": developer_judgments_recorded,
        "comparisons": comparisons,
    }, problems


def resolve_subjective_rating(sheets: list[tuple[int, Path, dict[str, Any]]]) -> tuple[dict[str, Any], list[str]]:
    """PM's own `model-performance.md` rating, read back verbatim -- never
    parsed into structured scores (see this module's own docstring).

    Returns:
        (rating, problems): `rating` is always one of the three shapes
        below; `problems` names a referenced-but-missing file (real
        corruption -- something recorded as written has since vanished),
        never a rating that was simply never recorded (an honest absence,
        not an error).
    """
    ref = _require_consistent(sheets, ("pm_model_performance_ref",), ignore_none=True)
    if ref is None:
        return {"available": False, "ref": None, "text": None}, []
    ref_path = Path(ref)
    if not ref_path.is_file():
        problem = f"pm_model_performance_ref {ref} is recorded but no longer exists on disk"
        return {"available": False, "ref": ref, "text": None}, [problem]
    text = ref_path.read_text(encoding="utf-8")
    return {"available": True, "ref": ref, "text": text}, []


def build_report(
    sheets: list[tuple[int, Path, dict[str, Any]]], run_id: str, *, run_dir: Path | None = None
) -> tuple[dict[str, Any], list[str]]:
    """Assemble the full per-model report from every discovered sheet.

    Args:
        run_dir: PM's own run directory (holding `run.json`/`events.jsonl`),
            used to derive the run-level `timing` block and to harvest PM's
            own structured judgments (`resolve_pm_judgments`). Optional --
            see `resolve_run_timing`'s own docstring for what an omitted
            `run_dir` produces (PM judgments degrade the same way).

    Returns:
        (report, problems) -- `problems` collects the subjective rating's
        referenced file going missing (see resolve_subjective_rating), any
        genuine `timing` data problem (see resolve_run_timing), and any
        named PM-judgment validation problem (see resolve_pm_judgments);
        everything else here either succeeds or raises ModelReportError,
        since a sheet already on disk is either internally consistent or a
        bug this tool must not paper over.

        `report["developer"]` is passed through exactly as every sheet
        recorded it (the structured identity block from
        `bench_lib.resolve_developer_identity`) -- including
        `attributed: false`. This tool does not reject an unattributed run:
        it is Tool 5 (leaderboard.py)'s job to keep such a run out of the
        ranked path while still surfacing it, never this tool's job to
        refuse writing its otherwise-valid report.
    """
    developer = _require_consistent(sheets, ("developer",))
    pm_status = _require_consistent(sheets, ("run_status", "pm_status"))
    stop_reason = _require_consistent(sheets, ("run_status", "stop_reason"))
    try:
        obligations = dev_check.load_obligations(bench_root())
    except dev_check.DevCheckError as exc:
        raise ModelReportError(str(exc)) from exc
    rating, problems = resolve_subjective_rating(sheets)
    timing, timing_problems = resolve_run_timing(run_dir, pm_status)
    problems.extend(timing_problems)
    provenance, provenance_problems = resolve_run_provenance(run_dir)
    problems.extend(provenance_problems)

    slices = []
    for slice_number, path, sheet in sheets:
        first_attempt = resolve_first_attempt(sheet)
        final_attempt = resolve_final_attempt(sheet)
        if final_attempt is None:
            problems.append(f"slice {slice_number} sheet {path} has no attempts recorded")

        # In a stop/restart case the stored grading baseline may have reset;
        # that case is labelled, never quietly reused as an apparent
        # first-to-final improvement. `baseline_commit` is recorded on
        # every attempt's own size_complexity block precisely so this
        # comparison is possible here without re-deriving before_head.
        # Correctness is measured independently on each attempt and is
        # unaffected by a baseline reset -- only a first-vs-final
        # size/complexity comparison for this slice becomes meaningless, so
        # only that gets flagged.
        node_outcomes = first_attempt_node_outcomes(sheet, slice_number, obligations, sheet_path=path)

        first_baseline = ((first_attempt or {}).get("size_complexity") or {}).get("baseline_commit")
        final_baseline = ((final_attempt or {}).get("size_complexity") or {}).get("baseline_commit")
        size_complexity_baseline_reset = bool(first_baseline and final_baseline and first_baseline != final_baseline)
        if size_complexity_baseline_reset:
            problems.append(
                f"run {run_id}, slice {slice_number}: grading baseline reset between the first attempt "
                f"(baseline_commit={first_baseline!r}) and the final attempt (baseline_commit={final_baseline!r}) "
                "-- a first-to-final size/complexity comparison for this slice must not be read as improvement "
                "(correctness is measured per-attempt and is unaffected)"
            )

        correctness_provenance = resolve_correctness_provenance(first_attempt, final_attempt, slice_number, run_id)

        run_status = sheet.get("run_status") or {}
        slices.append(
            {
                "slice": slice_number,
                "correctness_provenance": correctness_provenance,
                "slice_status": run_status.get("slice_status"),
                "infrastructure_failure_suspected": run_status.get("infrastructure_failure_suspected"),
                "attempts_total": resolve_attempts_total(sheet),
                "accepted_at_attempt": sheet.get("accepted_at_attempt"),
                # leaderboard.py's coverage/eligibility computation needs to
                # know whether a real attempt-0 row survived grading, which
                # the git-log walk's fallback can leave absent even though
                # the slice has a final-attempt row. This is a plain boolean,
                # kept alongside the richer `first_attempt` below (which is
                # None in exactly the same case) since the eligibility check
                # reads it directly and needn't unpack `first_attempt` to do so.
                "has_attempt_zero": any(a.get("attempt") == 0 for a in sheet.get("attempts") or []),
                "first_attempt": _attempt_without_by_node(first_attempt),
                "final_attempt": _attempt_without_by_node(final_attempt),
                # The one per-node hidden-test map this report carries,
                # nested {group_id: {node_id: outcome}} rather than flat --
                # the only consumer needs, for each node, which obligation
                # group's denominator it counts against (see
                # `first_attempt_node_outcomes`'s own docstring). None when
                # this slice has no attempt-0 row (same case as
                # `has_attempt_zero: False`); the bulky per-attempt
                # `by_node` map itself stays sheet-only.
                "first_attempt_node_outcomes": node_outcomes,
                "attempt_trajectory": attempt_trajectory(sheet),
                "reviews": slice_reviews(sheet),
                "size_complexity_baseline_reset": size_complexity_baseline_reset,
            }
        )

    measurement_metric_version, metric_version_problems = _resolve_measurement_metric_version(slices, run_id)
    problems.extend(metric_version_problems)

    # Mutates every slice's `reviews` entries (`pm_rating`) and
    # `attempt_trajectory` entries (`pm_developer_judgment`) in place, and
    # returns the run-level comparison/availability block -- called last,
    # once `slices` is fully built, since the join needs the complete
    # `reviews`/`attempt_trajectory` lists to look `review_id`s and attempt
    # ordinals up against.
    pm_judgments, pm_judgment_problems = resolve_pm_judgments(run_dir, run_id, slices)
    problems.extend(pm_judgment_problems)

    report = {
        "run_id": run_id,
        "developer": developer,
        "run_status": {"pm_status": pm_status, "stop_reason": stop_reason},
        "timing": timing,
        "provenance": provenance,
        "slices": slices,
        "pm_subjective_rating": rating,
        "pm_judgments": pm_judgments,
        # Stamped by dev_check.py onto every attempt's size_complexity block
        # from policy.yaml's measurement.metric_version at grading time --
        # carried through here so a metric-version rebuild of already-graded
        # runs is distinguishable from a genuinely new trial.
        "measurement_metric_version": measurement_metric_version,
        "problems": problems,
    }
    return report, problems


def _resolve_measurement_metric_version(slices: list[dict[str, Any]], run_id: str) -> tuple[int | None, list[str]]:
    """The single `metric_version` every attempt's `size_complexity` block
    on this run agrees on, or None with a named problem if they disagree
    (a run re-graded mid-way through a metric-version rebuild) -- never
    picked from one attempt and silently applied to the whole run.

    Returns:
        (version, problems). `version` is None, with no problem, when no
        attempt on this run carries a size_complexity block yet (an honest
        "not yet measured", not an error).
    """
    versions: set[int] = set()
    for slice_entry in slices:
        for attempt in (slice_entry.get("first_attempt"), slice_entry.get("final_attempt")):
            version = ((attempt or {}).get("size_complexity") or {}).get("metric_version")
            if version is not None:
                versions.add(version)
    if len(versions) > 1:
        problem = (
            f"run {run_id}: attempts disagree on measurement.metric_version across slices: {sorted(versions)} "
            "-- this run was graded across a metric-version rebuild; size/complexity figures are not "
            "comparable across its own attempts"
        )
        return None, [problem]
    return (next(iter(versions)) if versions else None), []


# --- CLI -----------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Gather one model's full PM run into a per-model report: first/final-attempt correctness/"
            "quality/scope and a per-attempt trajectory per slice, the review-finding trend across attempts, "
            "and PM's own subjective model-performance rating kept strictly separate. "
            "No invented composite score -- that is Tool 5's job."
        )
    )
    parser.add_argument("--run-id", required=True, help="the PM run id, e.g. 20260911T112036Z-cd15fe")
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=None,
        help=(
            "PM's authoritative run directory (holding run.json/events.jsonl), used to derive the "
            "run's elapsed-time 'timing' block and to harvest PM's own judgments. Optional -- "
            "omitted, 'timing' reads available:false with a named reason, never a guess."
        ),
    )
    parser.add_argument("--out", type=Path, default=None, help="defaults to results/runs/<run_id>/model-report.json")
    return parser.parse_args(argv)


def _require_pm_run_dir(run_dir: Path) -> None:
    """Hard-stop a `--run-dir` that is not PM's own run directory, before
    anything is read or written.

    `resolve_run_timing`/`resolve_run_provenance` degrade a missing
    `run.json`/`events.jsonl` to an honest `available: false` block, which
    is the *right* behaviour for the ordinary, expected "no --run-dir
    given" case but the *wrong* one for an explicitly-given, mistyped or
    nonexistent path -- the caller asked this tool to read a specific PM
    run, and it must not silently read nothing instead. Per AGENTS.md
    ("never write a partial result as if it were complete"), that must be a
    hard error raised before `build_report`/`write_json_atomically` ever
    run, not a set of honest-looking `available: false` blocks overwriting
    a good prior report.

    Raises:
        ModelReportError: naming the resolved directory and each missing
            required file, when `run.json` and/or `events.jsonl` are not
            both present under it.
    """
    missing = [name for name in ("run.json", "events.jsonl") if not (run_dir / name).is_file()]
    if missing:
        raise ModelReportError(
            f"--run-dir {run_dir} is not a PM run directory -- missing {', '.join(missing)}; "
            "--run-dir must point at PM's own run directory (.../pm/<run_id>/)"
        )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = bench_root()
    sheets_dir = default_sheets_dir(root, args.run_id)
    out_path = (args.out or default_out_path(root, args.run_id)).expanduser().resolve()
    run_dir = args.run_dir.expanduser().resolve() if args.run_dir else None
    if run_dir is not None:
        _require_pm_run_dir(run_dir)

    sheets = discover_sheets(sheets_dir, args.run_id)
    report, problems = build_report(sheets, args.run_id, run_dir=run_dir)
    bench_lib.write_json_atomically(out_path, report)
    print(f"wrote {out_path} ({len(sheets)} slice(s))")
    return bench_lib.report_problems("model_report.py", problems)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ModelReportError as exc:
        print(f"model_report.py: error: {exc}", file=sys.stderr)
        sys.exit(1)
