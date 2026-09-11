#!/usr/bin/env python3
"""Shared helpers for tools/dev_check.py (Tool 1) and tools/review_score.py
(Tools 2/3): the three pieces of state each tool otherwise reimplemented
independently, with subtly different semantics (docs/MODE2-REWRITE-PLAN.md
§3, "minimum, no dead code"; AGENTS.md: "prefer one parameterised
implementation over two near-identical ones").

This is a shared-helpers module, not a framework: nothing goes in here that
both tools do not already need.
"""

from __future__ import annotations

import json
import os
import subprocess
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


def read_events(run_dir: Path) -> list[dict[str, Any]]:
    """Read `events.jsonl` into an ordered list (file order is time order).

    Contract (deliberately tolerant of a missing file, not accidentally so):
    a run whose first event has not landed yet has no decisions and no
    reviews to report, which is different from a corrupt log and must not be
    conflated with one -- so a missing events.jsonl returns `[]`, exactly
    like dev_check.py always assumed. review_score.py's callers need real
    events to do anything useful (a review harvest cannot proceed without a
    review event), so it is `find_latest_review_event`'s and
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


def write_json_atomically(path: Path, data: Any) -> None:
    """Write `data` as indent=2 JSON via mkstemp + os.replace.

    Never leaves a torn file: either the old content stays (write failed and
    the temp file is cleaned up) or the new content lands whole (os.replace
    is atomic on the same filesystem, which mkstemp's `dir=` guarantees).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".bench-lib-", suffix=".json.tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
            handle.write("\n")
        os.replace(tmp_name, path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


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
