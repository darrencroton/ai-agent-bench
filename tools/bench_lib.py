#!/usr/bin/env python3
"""Shared helpers for tools/dev_check.py (Tool 1) and tools/review_score.py
(Tools 2/3): the three pieces of state each tool otherwise reimplemented
independently, with subtly different semantics (docs/MODE2-REWRITE-PLAN.md
§2, "minimum, no dead code"; AGENTS.md: "prefer one parameterised
implementation over two near-identical ones").

This is a shared-helpers module, not a framework: nothing goes in here that
both tools do not already need.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


class BenchLibError(RuntimeError):
    """Base for both tools' own error types.

    Each tool subclasses this (DevCheckError, ReviewScoreError) and lets its
    own subclass reach the user, never this base type directly -- a shared
    helper failing loudly should still read as "dev_check.py: error: ..." or
    "review_score: error: ...", not as an unfamiliar third name.
    """


# An attempt "opens" at one of these event kinds (references/run-state.md's
# Attempts semantics). Shared by attempt_ordinal() below and by
# dev_check.resolve_pm_decision(), which walks the same family to find what
# closed an attempt rather than what opened it.
LAUNCH_KINDS = ("launch", "relaunch", "steer")


def read_events(run_dir: Path) -> list[dict[str, Any]]:
    """Read `events.jsonl` into an ordered list (file order is time order).

    Contract (deliberately tolerant of a missing file, not accidentally so):
    a run whose first event has not landed yet has no decisions and no
    reviews to report, which is different from a corrupt log and must not be
    conflated with one -- so a missing events.jsonl returns `[]`, exactly
    like dev_check.py always assumed. review_score.py's callers need real
    events to do anything useful (a review harvest cannot proceed without a
    review event), so it is `find_review_events`'s and
    `run_review_score`'s job to fail loudly on an empty result themselves --
    this function has no opinion on whether "no events yet" is an error for
    its caller.

    Raises:
        BenchLibError: a line exists but is not valid JSON, naming the file
            and line number -- always an error, tolerant-missing-file or not.
    """
    events_path = run_dir / "events.jsonl"
    if not events_path.is_file():
        return []
    events: list[dict[str, Any]] = []
    for lineno, line in enumerate(events_path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            events.append(json.loads(stripped))
        except json.JSONDecodeError as exc:
            raise BenchLibError(f"invalid JSON on {events_path}:{lineno}: {exc}") from exc
    return events


def launch_family_indices(events: list[dict[str, Any]], slice_id: str) -> list[int]:
    """Indices of `launch`/`relaunch`/`steer` events for one slice, in file order.

    The count of these events -- never `run.json`'s own `attempts` counter --
    is the monotonic per-slice attempt key both tools use (see
    attempt_ordinal()). `pm_lib.slice_ops.start_slice` resets that counter to
    0 whenever a stopped slice is relaunched (a `finalize --stop` clears
    `current_slice`, so the next `start-slice` takes the non-relaunch branch
    and re-zeroes it) even though the slice may already carry several
    attempts from before the stop. The event log has no such reset: a
    restarted slice's next launch is still one more `launch` event for the
    same slice id, so counting them monotonically survives a stop/restart
    cycle intact.
    """
    return [i for i, e in enumerate(events) if e.get("kind") in LAUNCH_KINDS and e.get("slice") == slice_id]


def attempt_ordinal(events: list[dict[str, Any]], slice_id: str, *, before_index: int | None = None) -> int:
    """The monotonic 0-based attempt ordinal open at `before_index` (or, by
    default, the latest one recorded for the slice) -- the sheet's real key
    (docs/MODE2-REWRITE-PLAN.md §7; see launch_family_indices for why this,
    not PM's own `attempts` counter, is used). Both dev_check.py (the
    current/latest attempt, or an explicitly requested one) and
    review_score.py (the attempt live when a given review event ran) derive
    their attempt number from this single function so they cannot disagree
    by construction.

    Args:
        before_index: an event index; only launch-family events strictly
            before it are counted (review_score's use: attribute a review to
            the attempt that was open when it ran). None counts every
            launch-family event recorded so far for the slice.

    Returns:
        The 0-based ordinal: (count of qualifying launch-family events) - 1.

    Raises:
        BenchLibError: no qualifying launch-family event exists -- there is
            no attempt to number.
    """
    opens = launch_family_indices(events, slice_id)
    if before_index is not None:
        opens = [i for i in opens if i < before_index]
    if not opens:
        where = f" before event index {before_index}" if before_index is not None else ""
        raise BenchLibError(f"no launch/relaunch/steer event found for slice {slice_id!r}{where}")
    return len(opens) - 1


def epoch_start_ordinals(events: list[dict[str, Any]], slice_id: str) -> list[int]:
    """For each attempt ordinal (index into `launch_family_indices`'s own
    order), the ordinal of the first attempt in the same PM "epoch" -- the
    run of `relaunch`/`steer` attempts that share one `launch`, resetting
    only at the next `launch` (a fresh restart after a `finalize --stop`
    cleared `current_slice`; every OTHER launch-family event is a
    `relaunch` or `steer`, which never resets it).

    This is not a heuristic: `pm_lib.slice_ops.start_slice`'s relaunch
    branch and its `steer()` both set PM's own per-slice `attempts` counter
    to `entry["attempts"] + 1` unconditionally, and `start_slice`'s
    non-relaunch (fresh `launch`) branch sets it to 0 -- the exact same
    reset/increment rule this function applies to the event log. So
    `attempt - epoch_start_ordinals(events, slice_id)[attempt]` IS PM's own
    attempts counter at that historical moment (dev_check.py's
    `resolve_pm_attempts_counter`), and each epoch's first attempt's
    before_head is this slice's before_head as of exactly that restart
    (tools/grade_run.py's G16 walk, docs/MODE2-REWRITE-PLAN.md §8) --
    constant for every attempt sharing the same epoch start, since neither
    fact changes again until the next `launch`.
    """
    opens = launch_family_indices(events, slice_id)
    starts: list[int] = []
    current_epoch_start = 0
    for ordinal, event_index in enumerate(opens):
        if events[event_index].get("kind") == "launch":
            current_epoch_start = ordinal
        starts.append(current_epoch_start)
    return starts


def validate_sheet_identity(sheet: dict[str, Any], run_id: str, slice_number: int, path: Path) -> None:
    """Refuse a scoring sheet that belongs to a different run or slice (finding 5).

    Both dev_check.py's `--out` and review_score.py's `--sheet` accept an
    explicit path; without this check, pointing either at another run's or
    slice's sheet would silently read or write into the wrong cohort's data.

    Raises:
        BenchLibError: `sheet`'s own `run_id`/`slice` fields do not match.
    """
    if sheet.get("run_id") != run_id or sheet.get("slice") != slice_number:
        raise BenchLibError(
            f"scoring sheet {path} is for run_id={sheet.get('run_id')!r} slice={sheet.get('slice')!r}, "
            f"not run_id={run_id!r} slice={slice_number!r}"
        )


def write_text_atomically(path: Path, text: str, *, suffix: str = ".tmp") -> None:
    """Write `text` via mkstemp + os.replace.

    Never leaves a torn file: either the old content stays (write failed and
    the temp file is cleaned up) or the new content lands whole (os.replace
    is atomic on the same filesystem, which mkstemp's `dir=` guarantees).
    Shared by write_json_atomically (below) and leaderboard.py's own
    Markdown render -- both need the identical torn-write guarantee, not
    just the JSON-shaped one.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".bench-lib-", suffix=suffix)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
        os.replace(tmp_name, path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def write_json_atomically(path: Path, data: Any) -> None:
    """Write `data` as indent=2 JSON, torn-write-safe (see write_text_atomically)."""
    write_text_atomically(path, json.dumps(data, indent=2) + "\n", suffix=".json.tmp")


def report_problems(tool_name: str, problems: list[str], *, kind: str = "problem(s)") -> int:
    """Print every named problem to stderr and return the tool's exit code.

    Shared by grade_run.py and model_report.py, whose `main()`s both collect
    a flat list of named problems (never raising for any single one) and
    need the identical count-then-list-then-exit-code shape at the end --
    review_score.py's own tail differs (no summary count line, calls
    sys.exit() itself) and is left as its own, since its shape is genuinely
    not the same.

    Returns:
        1 if `problems` is non-empty, else 0.
    """
    if not problems:
        return 0
    print(f"{tool_name}: {len(problems)} {kind} occurred:", file=sys.stderr)
    for problem in problems:
        print(f"  - {problem}", file=sys.stderr)
    return 1


def repo_root() -> Path:
    """Absolute path to this repo's root, via `git rev-parse --show-toplevel`.

    Resolved relative to *this module's own location* (tools/, shared by
    both callers) rather than the caller's cwd -- dev_check.py's original
    rationale, now the one implementation both tools use. Without this, a
    tool invoked from the Developer's own repo (the natural place to run
    review_score.py from) would resolve its default --sheet/--out path into
    the wrong repository entirely.

    Raises:
        BenchLibError: cwd is not inside a git repo, or git is not on PATH --
            never lets a raw CalledProcessError/OSError escape to the caller.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=Path(__file__).resolve().parent,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise BenchLibError(f"could not run git to resolve this repo's root: {exc}") from exc
    if result.returncode != 0:
        raise BenchLibError(
            f"could not resolve this repo's root via 'git rev-parse --show-toplevel' "
            f"(cwd {Path(__file__).resolve().parent} is not inside a git repo?): {result.stderr.strip()}"
        )
    return Path(result.stdout.strip()).resolve()
