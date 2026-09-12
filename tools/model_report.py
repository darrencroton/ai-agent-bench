#!/usr/bin/env python3
"""Tool 4: one model's full PM run, reshaped into a per-model report
(docs/MODE2-REWRITE-PLAN.md §6, "Tool 4").

This module invents no scoring math and no composite score -- weighting
belongs to Tool 5 (`leaderboard.py`), driven by `policy.yaml`. It only reads
what `dev_check.py`/`review_score.py` already computed into each slice's
scoring sheet (`results/runs/<run_id>/slice-<N>.json`) and reshapes it into
one run-level document: final correctness/quality/scope per slice, attempt
counts, and the review-finding trend across attempts. It also folds in PM's
own `model-performance.md` rating (referenced by each sheet's
`pm_model_performance_ref`), read back verbatim and kept in its own
`pm_subjective_rating` block -- that rating is PM's judgement on a fixed
scale, "not a mechanical measurement, and never presented as one"
(project-manager's `references/model-performance-rubric.md`), so it is never
parsed into structured scores here.

Everything this module reads is already-graded, already-on-disk data; it
touches neither PM's own state nor git.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import bench_lib

_SHEET_FILENAME_RE = re.compile(r"^slice-(\d+)\.json$")

# Attempt-entry fields review_score.py populates per commissioned review skill
# (tools/review_score.py's own REVIEW_SKILLS -> sheet_field mapping) --
# reused by name here rather than imported, since this module has no other
# reason to import review_score.py at all.
_REVIEW_TREND_FIELDS = ("drift_review", "code_review")


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
    `("model",)` or `("run_status", "pm_status")`), or a loud error naming
    which slices disagreed -- these fields all come from the same run.json,
    so disagreement across sheets is corruption, never something to average
    or pick around.

    `ignore_none` treats a sheet with no value for this field as "not yet
    recorded" rather than a disagreement -- correct only for
    `pm_model_performance_ref`, which is legitimately null on a sheet graded
    before PM wrote `model-performance.md` (dev_check.py's
    resolve_model_performance_ref). Every other field this tool checks
    (`model`, `run_status.pm_status`/`.stop_reason`) is always present on a
    valid sheet and comes from the same run.json for every slice, so a None
    there is itself a disagreement worth raising on, not something to treat
    as a wildcard.
    """
    values: dict[int, Any] = {}
    for slice_number, _path, sheet in sheets:
        value: Any = sheet
        for key in field_path:
            value = value.get(key) if isinstance(value, dict) else None
        values[slice_number] = value
    candidates = [v for v in values.values() if not ignore_none or v is not None]
    distinct = set(candidates)
    if len(distinct) > 1:
        field_name = ".".join(field_path)
        detail = ", ".join(f"slice {n}={v!r}" for n, v in sorted(values.items()))
        raise ModelReportError(f"sheets for this run disagree on {field_name!r}: {detail}")
    return next(iter(distinct), None)


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


def _review_trend_entry(attempt_number: int, record: dict[str, Any]) -> dict[str, Any]:
    """One `review_trends` entry for a single commissioned review record.

    A report that failed to parse carries only `parse_error`
    (review_score.py's own `build_record`), never `verdict`/
    `findings_by_severity`/`open_after_this_attempt` -- preserved verbatim
    here rather than defaulting those fields to None, which would silently
    read as "commissioned, nothing to report" instead of a named parse
    failure (AGENTS.md: "an unparsable review report is a named parse
    error, never zero findings").
    """
    if "parse_error" in record:
        return {"attempt": attempt_number, "parse_error": record["parse_error"]}
    return {
        "attempt": attempt_number,
        "verdict": record.get("verdict"),
        "findings_by_severity": record.get("findings_by_severity"),
        "open_after_this_attempt": record.get("open_after_this_attempt"),
    }


def resolve_attempts_total(sheet: dict[str, Any]) -> int:
    """The true PM attempt count for this slice: the highest attempt
    ordinal recorded, plus one -- NOT the number of graded rows.

    Under G16's fallback (docs/MODE2-REWRITE-PLAN.md §5/§8), a slice's sheet
    can hold only its final attempt's row even though PM actually ran many
    more attempts; `grade_run.py`'s fallback path still grades that row
    under its correct, true final ordinal
    (`bench_lib.attempt_ordinal`/`gradeable_slice_targets`), so the highest
    `attempt` value present is always the true attempt count regardless of
    how many rows the walk recovered -- exactly the invariant
    docs/MODE2-REWRITE-PLAN.md's §5/§8 promise ("the attempt count ... [is]
    unaffected ... both come from events.jsonl directly, for every
    attempt"). Counting rows instead would silently undercount every
    slice that fell back.
    """
    attempts = sheet.get("attempts") or []
    if not attempts:
        return 0
    return max(a["attempt"] for a in attempts) + 1


def review_trends(sheet: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Per commissioned review field, one entry per attempt that actually
    commissioned it, in attempt order -- a straight reshape of data
    dev_check.py/review_score.py already computed, no new derivation.

    A field with no commissioned attempt at all is omitted from the result
    entirely (not emitted as an empty list) -- absence of the key means
    "never commissioned this slice", distinct from "commissioned, zero
    findings", which the per-entry dicts already represent explicitly.

    Sorted by `attempt` explicitly rather than trusting sheet-file order:
    dev_check.py's upsert appends new entries rather than inserting them in
    sorted position, so a slice graded out of order (e.g. an ad hoc regrade
    per README's "callable directly for a manual/ad-hoc grade") would
    otherwise emit an out-of-sequence trend.
    """
    trends: dict[str, list[dict[str, Any]]] = {}
    ordered_attempts = sorted(sheet.get("attempts") or [], key=lambda a: a.get("attempt"))
    for field in _REVIEW_TREND_FIELDS:
        entries = []
        for attempt in ordered_attempts:
            record = attempt.get(field)
            if record is None:
                continue
            entries.append(_review_trend_entry(attempt.get("attempt"), record))
        if entries:
            trends[field] = entries
    return trends


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


def build_report(sheets: list[tuple[int, Path, dict[str, Any]]], run_id: str) -> tuple[dict[str, Any], list[str]]:
    """Assemble the full per-model report from every discovered sheet.

    Returns:
        (report, problems) -- `problems` is empty unless the subjective
        rating's referenced file has gone missing (see
        resolve_subjective_rating); everything else here either succeeds or
        raises ModelReportError, since a sheet already on disk is either
        internally consistent or a bug this tool must not paper over.
    """
    model = _require_consistent(sheets, ("model",))
    pm_status = _require_consistent(sheets, ("run_status", "pm_status"))
    stop_reason = _require_consistent(sheets, ("run_status", "stop_reason"))
    rating, problems = resolve_subjective_rating(sheets)

    slices = []
    for slice_number, path, sheet in sheets:
        final_attempt = resolve_final_attempt(sheet)
        if final_attempt is None:
            problems.append(f"slice {slice_number} sheet {path} has no attempts recorded")
        run_status = sheet.get("run_status") or {}
        slices.append(
            {
                "slice": slice_number,
                "slice_status": run_status.get("slice_status"),
                "infrastructure_failure_suspected": run_status.get("infrastructure_failure_suspected"),
                "attempts_total": resolve_attempts_total(sheet),
                "accepted_at_attempt": sheet.get("accepted_at_attempt"),
                "final_attempt": final_attempt,
                "review_trends": review_trends(sheet),
            }
        )

    report = {
        "run_id": run_id,
        "model": model,
        "run_status": {"pm_status": pm_status, "stop_reason": stop_reason},
        "slices": slices,
        "pm_subjective_rating": rating,
        "problems": problems,
    }
    return report, problems


# --- CLI -----------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Gather one model's full PM run into a per-model report: final correctness/quality/scope and "
            "attempt count per slice, the review-finding trend across attempts, and PM's own subjective "
            "model-performance rating kept strictly separate (docs/MODE2-REWRITE-PLAN.md §6, Tool 4). No "
            "invented composite score -- that is Tool 5's job."
        )
    )
    parser.add_argument("--run-id", required=True, help="the PM run id, e.g. 20260911T112036Z-cd15fe")
    parser.add_argument("--out", type=Path, default=None, help="defaults to results/runs/<run_id>/model-report.json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = bench_root()
    sheets_dir = default_sheets_dir(root, args.run_id)
    out_path = (args.out or default_out_path(root, args.run_id)).expanduser().resolve()

    sheets = discover_sheets(sheets_dir, args.run_id)
    report, problems = build_report(sheets, args.run_id)
    bench_lib.write_json_atomically(out_path, report)
    print(f"wrote {out_path} ({len(sheets)} slice(s))")
    return bench_lib.report_problems("model_report.py", problems)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ModelReportError as exc:
        print(f"model_report.py: error: {exc}", file=sys.stderr)
        sys.exit(1)
