#!/usr/bin/env python3
"""Tool 4: one model's full PM run, reshaped into a per-model report
(docs/MODE2-REWRITE-PLAN.md §6, "Tool 4").

This module invents no scoring math and no composite score -- weighting
belongs to Tool 5 (`leaderboard.py`), driven by `policy.yaml`. It only reads
what `dev_check.py`/`review_score.py` already computed into each slice's
scoring sheet (`results/runs/<run_id>/slice-<N>.json`) and reshapes it into
one run-level document: first/final-attempt correctness/quality/scope per
slice, a compact per-attempt trajectory, attempt counts, and the
review-finding trend across attempts. It also folds in PM's own
`model-performance.md` rating (referenced by each sheet's
`pm_model_performance_ref`), read back verbatim and kept in its own
`pm_subjective_rating` block -- that rating is PM's judgement on a fixed
scale, "not a mechanical measurement, and never presented as one"
(project-manager's `references/model-performance-rubric.md`), so it is never
parsed into structured scores here.

Everything this module reads is already-graded, already-on-disk data --
except the run's own `timing` block (docs/LEADERBOARD-REBUILD-PLAN.md Stage
2), which is derived from `events.jsonl`'s `init`/`complete`/`stop`
timestamps and requires read access to the originating PM run directory
(`--run-dir`, optional). That read is still strictly read-only against PM
state (no run token, no write, matching every other tool in this suite) --
it is simply not "already-on-disk sheet data" the way everything else here
is. Omitting `--run-dir` degrades gracefully: `timing` reads `available:
false` with a named reason, never a guess.
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
    `("developer",)` or `("run_status", "pm_status")`), or a loud error
    naming which slices disagreed -- these fields all come from the same
    run.json, so disagreement across sheets is corruption, never something
    to average or pick around.

    Compares candidates by equality, not by collecting them into a `set`
    (`("developer",)` is a dict -- Stage 1's structured identity block,
    docs/LEADERBOARD-REBUILD-PLAN.md -- and dicts are not hashable), so this
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


def resolve_first_attempt(sheet: dict[str, Any]) -> dict[str, Any] | None:
    """The ordinal-0 attempt entry -- the Developer's first submission for
    this slice, which is what Stage 2's ranking basis (mean first-attempt
    correctness, docs/LEADERBOARD-REBUILD-PLAN.md) is computed from.

    Returns:
        The attempt dict, or None when the sheet has no attempt-0 row at
        all -- G16's fallback (docs/MODE2-REWRITE-PLAN.md §5/§8) can leave a
        slice with only its final attempt's row, and Stage 1's
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


def _review_trend_entry(attempt_number: int, record: dict[str, Any]) -> dict[str, Any]:
    """One `review_trends` entry for a single commissioned review record.

    Stops dropping attribution (docs/LEADERBOARD-REBUILD-PLAN.md Stage 2):
    every identifying field the record carries -- `skill`, `tool`, `model`,
    `head`, `at`, `report_ref`, `report_sha256` -- is passed through, not
    just `verdict`/`findings_by_severity`/`open_after_this_attempt`. This is
    what let `leaderboard.py`'s old review-trend table's "Reviewer" column
    hold the sheet *field name* instead of the reviewer's actual model
    (the defect docs/LEADERBOARD-EVALUATION-2026-09-13.md names).

    `review_id`, `effort` and `event_index` are included for the same
    reason but read `None` today: `review_score.py`'s `build_record` does
    not yet harvest them from `run.json`'s `reviews[]` entries (verified
    against real trial-10/11 data, which *does* carry `review_id`/`effort`/
    `origin_event.index` there) -- that harvest is Stage 4's job
    (docs/LEADERBOARD-REBUILD-PLAN.md Stage 4, "panel-preserving review
    records"). Reading `None` here is an honest "not yet captured", not a
    guess, and this function needs no further change once Stage 4 lands --
    it already passes these fields through by name.

    A report that failed to parse carries only `parse_error`
    (review_score.py's own `build_record`), never `verdict`/
    `findings_by_severity`/`open_after_this_attempt` -- preserved verbatim
    here rather than defaulting those fields to None, which would silently
    read as "commissioned, nothing to report" instead of a named parse
    failure (AGENTS.md: "an unparsable review report is a named parse
    error, never zero findings").
    """
    entry = {
        "attempt": attempt_number,
        "review_id": record.get("review_id"),
        "skill": record.get("skill"),
        "tool": record.get("tool"),
        "model": record.get("model"),
        "effort": record.get("effort"),
        "head": record.get("head"),
        "at": record.get("at"),
        "event_index": record.get("event_index"),
        "report_ref": record.get("report_ref"),
        "report_sha256": record.get("report_sha256"),
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


def attempt_trajectory(sheet: dict[str, Any]) -> list[dict[str, Any]]:
    """A compact, one-row-per-attempt summary of every Developer attempt
    this sheet has a row for -- including an attempt that PM steered with
    no review commissioned at all (docs/LEADERBOARD-REBUILD-PLAN.md Stage
    2: "including attempts that were steered with no commissioned review").
    `review_trends` (above) only ever lists attempts that DID commission a
    review, so it cannot show this by itself.

    Deliberately not a second copy of the bulky per-attempt payload
    (AGENTS.md/Stage 2: "the trajectory is a summary, not a second copy") --
    `quality` (lint/code-health findings) and `scope` stay only in
    `first_attempt`/`final_attempt`'s full blocks (and in the sheet itself).
    `correctness` is carried through here as-is: it is already small, and
    reducing it to a fraction would be inventing scoring math, which this
    module's own docstring forbids -- that reduction is `leaderboard.py`'s
    job, driven by `policy.yaml`.

    Two fields the plan's own trajectory format names are deliberately
    omitted rather than stubbed:

    - size/complexity (ΔLOC/ΔCC) has no source data until Stage 3
      instruments `dev_check.py` for it.
    - `pm_developer_judgment` has no source data until Stage 4 harvests
      PM's `developer_judgments[]` (nothing on today's sheet resembles it
      at all).

    Per AGENTS.md ("never write a partial result as if it were complete"),
    an absent column is left out of every row instead of a fabricated
    `None` repeated everywhere -- the same principle Stage 2 applies to the
    leaderboard tables' ΔLOC/ΔCC columns.
    """
    ordered_attempts = sorted(sheet.get("attempts") or [], key=lambda a: a.get("attempt"))
    trajectory: list[dict[str, Any]] = []
    for attempt in ordered_attempts:
        commissioned_reviews = []
        for field in _REVIEW_TREND_FIELDS:
            record = attempt.get(field)
            if record is None:
                continue
            commissioned_reviews.append(
                {
                    "skill": record.get("skill", field),
                    # Not yet harvested onto the record (Stage 4's job --
                    # see _review_trend_entry's own docstring); None here
                    # is an honest "not yet captured", never a guess.
                    "review_id": record.get("review_id"),
                }
            )
        trajectory.append(
            {
                "attempt": attempt.get("attempt"),
                "pm_attempts_counter": attempt.get("pm_attempts_counter"),
                "commit_sha": attempt.get("commit_sha"),
                "correctness": attempt.get("correctness"),
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


# pm_status -> the events.jsonl event `kind` that marks this run's end, per
# docs/MODE2-REWRITE-PLAN.md §7's four-value run_status.pm_status enum. Only
# these two are ever a finished run's terminal state ("active"/"needs-human"
# have no terminal event yet -- timing is honestly unavailable, not an
# error, for either).
_TERMINAL_EVENT_KIND_BY_PM_STATUS = {"complete": "complete", "stopped": "stop"}


def resolve_run_timing(run_dir: Path | None, pm_status: str | None) -> tuple[dict[str, Any], list[str]]:
    """Elapsed wall-clock time for this PM run, in seconds, from `init` to
    the terminal event matching `pm_status` (docs/LEADERBOARD-REBUILD-PLAN.md
    Stage 2) -- never a sheet timestamp, which records grading time
    (`dev_check.py`'s `utc_now_iso()`), not when PM actually ran.

    Trial 5 (verified against real data) carries a `complete` event
    followed by a later, routine `stop` event -- its `pm_status` is
    `"complete"`, so the terminal event looked up is `complete`, and the
    trailing `stop` never extends the measured span. Looking terminal
    events up by matching `pm_status` (rather than "the last of
    complete/stop") is what makes this correct in general, not just for
    this one trial.

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
    generation* -- `leaderboard.py`'s run index needs all three
    (docs/LEADERBOARD-REBUILD-PLAN.md Stage 2: "each run shows ... recorded
    branch, original Developer worktree path, presence-as-of-generation ...
    and PM artifact location").

    Read straight from `run.json` in `run_dir` -- still read-only, no
    write, the same PM-directory access `resolve_run_timing` already makes
    for the `timing` block.

    "Presence-as-of-generation" is a plain, timestamped filesystem check at
    the moment this report is built -- absence here is a real observation,
    but is NOT proof `cohort_run.py cleanup` ran (the plan is explicit that
    these are separate claims): the worktree could just as easily have been
    removed by hand, or never existed at this path on this machine at all
    (a report regenerated somewhere other than where the run happened).

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
            used only to derive the run-level `timing` block
            (docs/LEADERBOARD-REBUILD-PLAN.md Stage 2). Optional -- see
            `resolve_run_timing`'s own docstring for what an omitted
            `run_dir` produces.

    Returns:
        (report, problems) -- `problems` collects the subjective rating's
        referenced file going missing (see resolve_subjective_rating) and
        any genuine `timing` data problem (see resolve_run_timing);
        everything else here either succeeds or raises ModelReportError,
        since a sheet already on disk is either internally consistent or a
        bug this tool must not paper over.

        `report["developer"]` is passed through exactly as every sheet
        recorded it (Stage 1's structured identity block from
        `bench_lib.resolve_developer_identity`) -- including
        `attributed: false`. This tool does not reject an unattributed run:
        it is Tool 5 (leaderboard.py)'s job to keep such a run out of the
        ranked path while still surfacing it, never this tool's job to
        refuse writing its otherwise-valid report.
    """
    developer = _require_consistent(sheets, ("developer",))
    pm_status = _require_consistent(sheets, ("run_status", "pm_status"))
    stop_reason = _require_consistent(sheets, ("run_status", "stop_reason"))
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
        run_status = sheet.get("run_status") or {}
        slices.append(
            {
                "slice": slice_number,
                "slice_status": run_status.get("slice_status"),
                "infrastructure_failure_suspected": run_status.get("infrastructure_failure_suspected"),
                "attempts_total": resolve_attempts_total(sheet),
                "accepted_at_attempt": sheet.get("accepted_at_attempt"),
                # Stage 1's coverage/eligibility computation (leaderboard.py,
                # docs/LEADERBOARD-REBUILD-PLAN.md) needs to know whether a
                # real attempt-0 row survived grading, which G16's fallback
                # (docs/MODE2-REWRITE-PLAN.md SS5/SS8) can leave absent even
                # though the slice has a final-attempt row. This is a plain
                # boolean, kept alongside the richer `first_attempt` below
                # (which is None in exactly the same case) since Stage 1's
                # eligibility check reads it directly and needn't unpack
                # `first_attempt` to do so.
                "has_attempt_zero": any(a.get("attempt") == 0 for a in sheet.get("attempts") or []),
                "first_attempt": first_attempt,
                "final_attempt": final_attempt,
                "attempt_trajectory": attempt_trajectory(sheet),
                "review_trends": review_trends(sheet),
            }
        )

    report = {
        "run_id": run_id,
        "developer": developer,
        "run_status": {"pm_status": pm_status, "stop_reason": stop_reason},
        "timing": timing,
        "provenance": provenance,
        "slices": slices,
        "pm_subjective_rating": rating,
        "problems": problems,
    }
    return report, problems


# --- CLI -----------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Gather one model's full PM run into a per-model report: first/final-attempt correctness/"
            "quality/scope and a per-attempt trajectory per slice, the review-finding trend across attempts, "
            "and PM's own subjective model-performance rating kept strictly separate "
            "(docs/MODE2-REWRITE-PLAN.md §6, Tool 4). No invented composite score -- that is Tool 5's job."
        )
    )
    parser.add_argument("--run-id", required=True, help="the PM run id, e.g. 20260911T112036Z-cd15fe")
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=None,
        help=(
            "PM's authoritative run directory (holding run.json/events.jsonl), used only to derive the "
            "run's elapsed-time 'timing' block (docs/LEADERBOARD-REBUILD-PLAN.md Stage 2). Optional -- "
            "omitted, 'timing' reads available:false with a named reason, never a guess."
        ),
    )
    parser.add_argument("--out", type=Path, default=None, help="defaults to results/runs/<run_id>/model-report.json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = bench_root()
    sheets_dir = default_sheets_dir(root, args.run_id)
    out_path = (args.out or default_out_path(root, args.run_id)).expanduser().resolve()
    run_dir = args.run_dir.expanduser().resolve() if args.run_dir else None

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
