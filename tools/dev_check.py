#!/usr/bin/env python3
"""Tool 1: correctness, independent quality, and scope-discipline grading
for one PM slice attempt.

This module is a pure, one-shot grading command: given a PM run directory
and a slice number, it grades exactly one attempt (the current/latest one,
by default) and upserts one entry into that slice's cumulative scoring
sheet. It never polls, never daemonizes, and never re-invokes itself.

**Grading is a single post-hoc pass over a finished run** (`tools/grade_run.py`),
not something that needs to happen while PM is still working -- a
slice's `before_head` is a permanent, structural fact (see
`resolve_before_head`), not something that evaporates once a slice stops
being `current_slice`. Re-running this tool for an
attempt already graded replaces that attempt's row and refreshes its
timestamp -- not byte-identical (the timestamp always advances), but it
never disturbs any other attempt or the other tool's (`review_score.py`'s)
fields on the same one.

Everything this module does is read-only with respect to project-manager's
own state: it reads run.json (no run token, no HMAC verification, never a
write), and it imports pm_lib's plan/git_ops helpers as a library, never
`pm.py` as a subprocess. Grading itself happens in a disposable git worktree
of the Developer's repo, never PM's own working directory.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tokenize
import xml.etree.ElementTree as ET
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterator

import yaml

import bench_lib

HIDDEN_TEST_FILENAMES = ("test_hA.py", "test_hB.py")
# pytest exit codes that still represent a trustworthy, scoreable run: 0 (all
# passed) and 1 (some failed). Anything else (2 interrupted/collection error,
# 3 internal error, 4 usage error, 5 no tests collected) means pytest never
# produced a result worth scoring.
_PYTEST_SCOREABLE_EXIT_CODES = frozenset({0, 1})


class DevCheckError(bench_lib.BenchLibError):
    """Raised for every condition this tool must fail loudly on.

    main() catches exactly this exception type, prints it, and exits 1 --
    every other exception is a bug in this tool, not an expected failure
    mode, and should surface as a traceback. Subclasses bench_lib's shared
    base so a bench_lib helper's failure surfaces under this tool's own name
    once re-raised (see bench_root()), never as an unfamiliar third type.
    """


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def bench_root() -> Path:
    """Absolute path to this repo's root -- see bench_lib.repo_root().

    Resolved relative to bench_lib.py's own location rather than the
    caller's cwd, so --out's and --policy's defaults are stable regardless
    of where dev_check.py is invoked from.
    """
    try:
        return bench_lib.repo_root()
    except bench_lib.BenchLibError as exc:
        raise DevCheckError(str(exc)) from exc


# --- policy ------------------------------------------------------------


def load_policy(policy_path: Path) -> dict[str, Any]:
    """Load and minimally validate policy.yaml.

    Args:
        policy_path: path to the policy file.

    Returns:
        The parsed policy mapping.

    Raises:
        DevCheckError: the file is missing, is not a mapping, names an
            unimplemented backend, or is missing a key this tool needs.
    """
    if not policy_path.is_file():
        raise DevCheckError(f"policy file not found: {policy_path}")
    with policy_path.open("r", encoding="utf-8") as handle:
        policy = yaml.safe_load(handle)
    if not isinstance(policy, dict):
        raise DevCheckError(f"policy file {policy_path} did not parse to a mapping")

    # "local" is the only implemented backend. An unimplemented backend
    # must fail loudly here, never silently fall back to local.
    backend = policy.get("backend")
    if backend != "local":
        raise DevCheckError(
            f"policy.yaml's backend={backend!r} is not implemented by dev_check.py; only 'local' is supported"
        )

    required_keys = ("pm_scripts_dir", "lint_script", "health_script", "python_interpreter")
    missing = [key for key in required_keys if not policy.get(key)]
    if missing:
        raise DevCheckError(f"policy file {policy_path} is missing required keys: {', '.join(missing)}")

    # subprocess_timeout_seconds gets its own check, not the blanket one
    # above: every tunable lives in policy.yaml, never hardcoded (AGENTS.md),
    # so this tool must refuse to fall back to an inline default when it is
    # absent, and must refuse a value that could never be a real timeout.
    timeout = policy.get("subprocess_timeout_seconds")
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or timeout <= 0:
        raise DevCheckError(
            f"policy file {policy_path} must set subprocess_timeout_seconds to a positive number "
            f"(never a hardcoded fallback in this tool); got {timeout!r}"
        )

    _validate_measurement_policy(policy, policy_path)
    return policy


_MEASUREMENT_PATH_BUCKETS = ("production_paths", "test_paths", "doc_paths")
_MEASUREMENT_REQUIRED_KEYS = (*_MEASUREMENT_PATH_BUCKETS, "loc_definition", "loc_category_definition", "metric_version")

# The only ΔLOC definition dev_check.py implements -- an unimplemented
# alternative (e.g. SLOC-excluding-comments) must fail loudly here, exactly
# like load_policy's own "backend" check above, never be silently treated
# as this one.
_LOC_DEFINITION_NET_PHYSICAL_LINES = "net_physical_lines"


def _validate_measurement_policy(policy: dict[str, Any], policy_path: Path) -> None:
    """Validate the `measurement` section: production/test/doc path globs, the
    LOC definition, and `metric_version` -- every one of them a tunable
    AGENTS.md requires to live in policy.yaml, never hardcoded here. Failure
    here names the concrete missing/malformed key, matching this function's
    caller's own style for `backend`/`subprocess_timeout_seconds`.
    """
    measurement = policy.get("measurement")
    if not isinstance(measurement, dict):
        raise DevCheckError(
            f"policy file {policy_path} is missing its required 'measurement' section"
        )
    missing = [key for key in _MEASUREMENT_REQUIRED_KEYS if key not in measurement]
    if missing:
        raise DevCheckError(
            f"policy file {policy_path}'s 'measurement' section is missing required keys: {', '.join(missing)}"
        )
    for bucket in _MEASUREMENT_PATH_BUCKETS:
        globs = measurement[bucket]
        if not isinstance(globs, list) or not globs or not all(isinstance(g, str) and g for g in globs):
            raise DevCheckError(
                f"policy file {policy_path}'s measurement.{bucket} must be a non-empty list of glob strings, "
                f"got {globs!r}"
            )
    metric_version = measurement["metric_version"]
    if not isinstance(metric_version, int) or isinstance(metric_version, bool):
        raise DevCheckError(
            f"policy file {policy_path}'s measurement.metric_version must be an integer, got {metric_version!r}"
        )
    if measurement["loc_definition"] != _LOC_DEFINITION_NET_PHYSICAL_LINES:
        raise DevCheckError(
            f"policy file {policy_path}'s measurement.loc_definition must be "
            f"{_LOC_DEFINITION_NET_PHYSICAL_LINES!r} (the only definition dev_check.py implements; an "
            "alternative like SLOC-excluding-comments is a reasonable later addition under one pinned "
            f"analyzer on both revisions, but is never silently treated as this one); got "
            f"{measurement['loc_definition']!r}"
        )
    if measurement["loc_category_definition"] != _LOC_CATEGORY_DEFINITION_AST_TOKENIZE:
        raise DevCheckError(
            f"policy file {policy_path}'s measurement.loc_category_definition must be "
            f"{_LOC_CATEGORY_DEFINITION_AST_TOKENIZE!r} (the only production code/docstring/comment/blank "
            "decomposition dev_check.py implements -- see classify_source_lines); got "
            f"{measurement['loc_category_definition']!r}"
        )


# --- run.json (read-only) -----------------------------------------------


def load_run_state(run_dir: Path) -> dict[str, Any]:
    """Read run.json read-only: no run token, no HMAC verification, no writes.

    Tool 1 never authenticates as PM's controller and never mutates PM
    state -- this is a plain, unverified read of the same authoritative file
    PM itself writes.
    """
    run_json_path = run_dir / "run.json"
    if not run_json_path.is_file():
        raise DevCheckError(f"run.json not found under --run-dir: {run_json_path}")
    with run_json_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def find_slice_entry(run_state: dict[str, Any], slice_id: str) -> dict[str, Any]:
    for entry in run_state.get("slices", []):
        if isinstance(entry, dict) and entry.get("id") == slice_id:
            return entry
    raise DevCheckError(f"slice {slice_id!r} not found in run.json's 'slices' list")


def resolve_pm_attempts_counter(events: list[dict[str, Any]], slice_id: str, attempt: int) -> int:
    """PM's own `attempts` counter, as it read at the historical moment
    `attempt` (the monotonic event-derived ordinal, see resolve_attempt())
    was open -- not whatever run.json's live/final snapshot holds now.

    Recorded on the attempt entry as `pm_attempts_counter` -- what a human
    reading PM's own output sees -- but never used as the sheet's key (that
    is `attempt` itself; see resolve_attempt() for why PM's own counter,
    which `pm_lib.slice_ops.start_slice` resets to 0 whenever a stopped
    slice is relaunched, cannot serve as one).

    Derived from the event log via `bench_lib.epoch_start_ordinals`, never
    from run.json's `current_slice`/entry snapshot: that snapshot only ever
    reflects PM's counter *now*, so it cannot correctly answer this question
    for a historical (non-latest) attempt -- which matters because every
    attempt of a slice is graded, not just the final one. The event log has
    no such staleness: PM's own counter resets/increments in lockstep with
    the exact same launch-family events this repo already parses, so
    `attempt - epoch_start_ordinals(...)[attempt]` reproduces it exactly,
    for any attempt, live or historical (verified directly against
    `pm_lib.slice_ops.start_slice`/`steer`, not inferred). `upsert_attempt`
    separately preserves an already-graded attempt's recorded value on a
    regrade -- this function only resolves the value on an attempt's *first*
    grade.
    """
    starts = bench_lib.epoch_start_ordinals(events, slice_id)
    if attempt < 0 or attempt >= len(starts):
        raise DevCheckError(
            f"could not resolve PM's attempts counter for {slice_id!r} attempt {attempt}: no matching "
            "launch/relaunch/steer event found in events.jsonl"
        )
    return attempt - starts[attempt]


def resolve_attempt(events: list[dict[str, Any]], slice_id: str, requested_attempt: int | None) -> int:
    """The sheet's real key: the monotonic event-derived attempt ordinal
    (bench_lib.attempt_ordinal), never PM's own `attempts` counter (finding
    2 -- see resolve_pm_attempts_counter for why that counter cannot be the
    key).

    Args:
        requested_attempt: an explicit `--attempt`, or None to grade the
            latest attempt recorded for the slice.

    Raises:
        DevCheckError: an explicitly requested attempt does not exist in the
            event log (never silently clamped or guessed).
    """
    try:
        latest = bench_lib.attempt_ordinal(events, slice_id)
    except bench_lib.BenchLibError as exc:
        raise DevCheckError(str(exc)) from exc
    if requested_attempt is None:
        return latest
    if requested_attempt < 0 or requested_attempt > latest:
        raise DevCheckError(
            f"--attempt {requested_attempt} not found in the event log for {slice_id!r} "
            f"(latest recorded attempt is {latest})"
        )
    return requested_attempt


# What PM did with an attempt once its work was finalized, keyed by the event
# kind that closed it. `slice-stop` and a top-level `stop` both end the attempt
# without acceptance; the distinction between them (who stopped it) lives in
# run_status, not here.
_DECISION_BY_EVENT_KIND = {
    "steer": "steer",
    "relaunch": "relaunch",
    "accept": "accept",
    "slice-stop": "stop",
    "stop": "stop",
}


def read_events(run_dir: Path) -> list[dict[str, Any]]:
    """Read `events.jsonl` -- see bench_lib.read_events() for the missing-file
    contract (empty list, not an error: an unstarted run has no decisions to
    report yet)."""
    try:
        return bench_lib.read_events(run_dir)
    except bench_lib.BenchLibError as exc:
        raise DevCheckError(str(exc)) from exc


def resolve_pm_decision(events: list[dict[str, Any]], slice_id: str, attempt: int) -> str | None:
    """What PM decided about this specific attempt, read from the event log.

    `run.json` records one `decision` string per *slice*, not one per attempt,
    so it cannot distinguish a first attempt that was steered from the third
    that was accepted -- and that per-attempt sequence is the iteration
    trajectory this bench exists to measure. The event log can: attempt `n`
    opens at the (n+1)-th `launch`/`relaunch`/`steer` event for the slice, and
    closes at the first event after it that decides its fate.

    Args:
        events: the run's events in file order.
        slice_id: PM's slice id, e.g. "Slice 1".
        attempt: the monotonic event-derived attempt ordinal (bench_lib.attempt_ordinal).

    Returns:
        One of "steer", "relaunch", "accept", "stop", or None when the attempt
        has not been decided yet (still running, or finalized but not yet
        acted on). None means undecided, never "nothing happened".
    """
    opens = bench_lib.launch_family_indices(events, slice_id)
    if attempt < 0 or attempt >= len(opens):
        return None
    for event in events[opens[attempt] + 1 :]:
        kind = event.get("kind")
        # A top-level `stop` carries no slice id but still ends the attempt.
        if kind == "stop" or (event.get("slice") == slice_id and kind in _DECISION_BY_EVENT_KIND):
            return _DECISION_BY_EVENT_KIND[kind]
    return None


def resolve_before_head(
    run_state: dict[str, Any],
    slice_id: str,
    existing_sheet: dict[str, Any] | None,
    attempt: int,
    entry: dict[str, Any],
    explicit_before_head: str | None = None,
) -> str:
    """The base commit correctness/quality/scope are all measured against.

    A slice's `before_head` is set at `start_slice`, to whatever HEAD was at
    that moment, and is preserved unchanged across every *relaunch/steer*
    within one uninterrupted in-flight epoch (`pm_lib/prompts.py`: "The
    slice's before_head is correct on every attempt" -- verified directly
    against `pm_lib/slice_ops.py`'s `start_slice`, not inferred). It is a
    structural fact recoverable from `run.json`, not something that
    evaporates once a slice stops being `current_slice` -- but it is NOT
    permanent across a `finalize --stop` followed by a later `start-slice`
    on the same still-unaccepted slice, which captures a brand-new value
    (see 4(b) below; this is exactly what makes 4(b) pick the most recent
    review, not just any review). This function tries four increasingly
    indirect ways to recover the right value before ever failing, in order
    from cheapest/most-authoritative to most-defensive:

    1. --before-head, if the caller supplied one explicitly (the honest
       escape hatch for the one case nothing below can recover: an
       ungraded, never-reviewed, no-longer-current first slice -- see 4).
    2. `current_slice.before_head`, when this slice is still live.
    3. This same attempt's own previously recorded `provenance.base_commit`,
       if an earlier grade of it wrote one into the sheet.
    4. **Structural, from run.json alone.** Mode B
       processes slices strictly in plan order and gates progression (via
       `pm_lib.plan.next_slice`, which skips only `accepted` or `attested`
       slices), so:
       (a) for any slice after the first, if the immediately preceding
           slice in `run_state["slices"]` was actually run through PM and
           accepted (not `attested` -- an operator pre-approval that skips
           PM launching it at all, and so never records a commit), its
           recorded `commit` IS this slice's before_head (`start_slice`
           sets before_head = git HEAD at the moment this slice began = the
           previous slice's ending commit). `run_state["slices"]` is
           populated once, at `init`, directly from `parse_plan()`'s own
           order (`pm_lib/slice_ops.py:init_run`) and never reordered
           afterward, so plain list-index arithmetic on it is safe -- no
           need to re-parse the plan here. An `attested` (commit-less)
           predecessor, or one with no recorded commit for any other
           reason, falls through to (b) below for THIS slice, not an error.
       (b) for ANY slice, including the first, the MOST RECENT review ever
           commissioned for it recorded before_head onto
           `entry["reviews"][*]["before_head"]` (`pm_lib/review.py`).
           **Not just any review, and not the first one found.**
           before_head is constant only *within one uninterrupted in-flight
           epoch* -- a `finalize --stop` followed by a later `start-slice`
           on the SAME still-unaccepted slice takes `start_slice`'s
           non-relaunch branch and captures a brand-new before_head at
           that moment (`pm_lib/slice_ops.py`'s `start_slice`), so an
           EARLIER review's before_head can be stale by the time a LATER
           (post-restart) attempt needs grading. The most recent review is
           the right choice, not merely a safer one: for this bench's own
           plan, both slices mechanically elevate risk at parse time, which
           makes a *fresh* review (commissioned against the exact attempt
           being decided) mandatory before `finalize --accept` will ever
           succeed (`finalize_accept`'s `_fresh_reviews_for_head` check) --
           so the most recent review recorded for an ACCEPTED slice is
           always the one that decided its final, accepted attempt, in the
           correct epoch. A restarted slice that was never re-reviewed in
           its new epoch (only reachable for a non-elevated-risk slice this
           plan doesn't have, or a non-accepted slice -- which `grade_run.py`
           now refuses to auto-grade at all, see its own `_resolve_grading_commit`)
           still falls through to 1. **List-position recency alone is a
           heuristic, not a guarantee:** reviews commission concurrently, and
           a reviewer's PID is cleared before its own report is parsed and
           appended, so
           two reviews' APPEND order to `entry["reviews"]` need not match
           the order their epochs opened in.** For an accepted slice this
           is made a guarantee rather than a heuristic: `entry["commit"]`
           is the exact accepted commit, and each review's own `head` is
           the exact commit it ran against, so filtering to reviews whose
           `head` matches `entry["commit"]` before taking the most recent
           is airtight. That filter is applied whenever the slice is
           recorded accepted; for any other case (a non-accepted slice
           graded manually with an explicit `--commit`), recency alone is
           still the best available signal.

    Raises:
        DevCheckError: naming every place looked, if none of the above
            resolves a before_head.
    """
    if explicit_before_head:
        return explicit_before_head

    current_slice = run_state.get("current_slice") or {}
    if current_slice.get("id") == slice_id:
        before_head = current_slice.get("before_head")
        if not before_head:
            raise DevCheckError(f"run.json's current_slice has no before_head recorded for {slice_id!r}")
        return str(before_head)

    for existing_attempt in (existing_sheet or {}).get("attempts", []):
        if existing_attempt.get("attempt") == attempt:
            # `or {}`, not a bare access: an attempt entry with an explicit
            # `"provenance": null` must fail loudly below like any other
            # attempt without a base commit, not raise AttributeError here.
            fallback = (existing_attempt.get("provenance") or {}).get("base_commit")
            if fallback:
                return str(fallback)
            break

    slices = run_state.get("slices") or []
    index = next((i for i, s in enumerate(slices) if isinstance(s, dict) and s.get("id") == slice_id), None)
    if index is not None and index > 0:
        previous_commit = slices[index - 1].get("commit")
        if previous_commit:
            return str(previous_commit)

    reviews = list(reversed(entry.get("reviews") or []))
    accepted_commit = entry.get("commit") if entry.get("status") == "accepted" else None
    if accepted_commit:
        # "Most recent by list position" is not airtight -- PM clears a
        # reviewer's PID before its (fallible) report parsing/appending, so two
        # concurrently commissioned reviews' *append* order to
        # entry["reviews"] need not match the order their epochs opened in;
        # a slow, earlier-epoch review could in principle land after a
        # faster, current-epoch one. For an ACCEPTED slice this is fully
        # avoidable rather than just unlikely: `head` on each review is the
        # exact commit it ran against, and `entry["commit"]` is the exact
        # commit that got accepted -- filtering to reviews whose `head`
        # matches it, before taking the most recent, is a guarantee, not a
        # heuristic.
        for review in reviews:
            recorded = review.get("before_head")
            if recorded and review.get("head") == accepted_commit:
                return str(recorded)

    for review in reviews:
        recorded = review.get("before_head")
        if recorded:
            return str(recorded)

    raise DevCheckError(
        f"before_head could not be resolved for {slice_id!r} attempt {attempt}: it is not run.json's "
        f"current_slice (current is {current_slice.get('id')!r}), no existing scoring sheet entry for this "
        "attempt has a recorded provenance.base_commit, the previous slice (if any) has no recorded commit, "
        "and no review was ever commissioned for this slice; pass --before-head explicitly"
    )


# --- git -----------------------------------------------------------------


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise DevCheckError(f"git {' '.join(args)} failed in {repo}: {result.stderr.strip()}")
    return result.stdout.strip()


def resolve_commit(repo: Path, commit_arg: str | None) -> str:
    return run_git(repo, "rev-parse", commit_arg or "HEAD")


@contextmanager
def grading_worktree(repo: Path, commit: str, policy: dict[str, Any]) -> Iterator[Path]:
    """A disposable, detached git worktree of `repo` at `commit`.

    Always outside `repo` (asserted, not assumed) and always removed on the
    way out, success or failure.
    """
    root = policy.get("grading_worktree_root")
    root_path = Path(root).expanduser().resolve() if root else None
    if root_path is not None:
        root_path.mkdir(parents=True, exist_ok=True)
    worktree_dir = Path(tempfile.mkdtemp(prefix="dev-check-", dir=str(root_path) if root_path else None)).resolve()

    if worktree_dir == repo or repo in worktree_dir.parents:
        worktree_dir.rmdir()
        raise DevCheckError(
            f"grading worktree {worktree_dir} would be inside the Developer's repo {repo}; "
            "set policy.yaml's grading_worktree_root outside the repo"
        )

    # `git worktree add` refuses to add into a non-empty existing directory;
    # mkdtemp already created worktree_dir, so remove it and let git recreate
    # the path atomically as part of the checkout.
    worktree_dir.rmdir()
    run_git(repo, "worktree", "add", "--detach", str(worktree_dir), commit)
    try:
        yield worktree_dir
    finally:
        removal = subprocess.run(
            ["git", "-C", str(repo), "worktree", "remove", "--force", str(worktree_dir)],
            check=False,
            capture_output=True,
            text=True,
        )
        if removal.returncode != 0:
            # A cleanup failure must never mask a real grading error already
            # propagating out of this context manager (hence a warning, not
            # a raise) -- but a stale worktree left registered in the
            # Developer's repo is worth naming loudly, not swallowing.
            print(
                f"dev_check.py: warning: failed to remove grading worktree {worktree_dir}: "
                f"{removal.stderr.strip()}",
                file=sys.stderr,
            )
        if worktree_dir.exists():
            shutil.rmtree(worktree_dir, ignore_errors=True)


# --- obligations -----------------------------------------------------------


OBLIGATIONS_RELATIVE_PATH = Path("hidden_tests") / "obligations.yaml"


def load_obligations(root: Path) -> dict[str, Any]:
    path = root / OBLIGATIONS_RELATIVE_PATH
    if not path.is_file():
        raise DevCheckError(f"obligations file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict) or not isinstance(data.get("slices"), dict):
        raise DevCheckError(f"obligations file {path} did not parse to the expected 'slices' mapping")
    return data


def obligation_groups_for_slice(obligations: dict[str, Any], slice_number: int) -> list[dict[str, Any]]:
    slices = obligations["slices"]
    slice_map = slices.get(slice_number)
    if slice_map is None:
        raise DevCheckError(f"obligations.yaml has no entry for slice {slice_number}; known slices: {sorted(slices)}")
    return slice_map.get("obligations", [])


def node_to_group_map(groups: list[dict[str, Any]]) -> dict[str, str]:
    """Node id -> group id, after checking no node is listed in two groups.

    This check is against obligations.yaml's own internal consistency; it
    does not require a pytest run.

    Raises:
        DevCheckError: naming every duplicated node and the groups it
            appears in, if any node is doubly-mapped.
    """
    node_to_groups: dict[str, list[str]] = {}
    for group in groups:
        for node in group.get("tests", []):
            node_to_groups.setdefault(node, []).append(group["id"])
    duplicates = {node: gs for node, gs in node_to_groups.items() if len(gs) > 1}
    if duplicates:
        detail = "; ".join(f"{node!r} in groups {gs}" for node, gs in sorted(duplicates.items()))
        raise DevCheckError(f"obligations.yaml lists the same node id in more than one group: {detail}")
    return {node: gs[0] for node, gs in node_to_groups.items()}


# --- correctness -----------------------------------------------------------


def hidden_tests_manifest_hash(root: Path, slice_number: int) -> str:
    """Sha256 of a canonical manifest of this slice's hidden test files.

    Covers exactly the files `run_hidden_tests` copies into the grading
    worktree -- same `HIDDEN_TEST_FILENAMES`, same source directory -- so
    this can never drift from what actually gets executed. The manifest is
    a deterministic text of sorted (filename, sha256-of-bytes) pairs, joined
    with explicit separators, which is then hashed itself; this is hashed
    rather than concatenating the raw file bytes so that a rename or a
    content shift between the two files can never produce the same digest
    as leaving both alone, and the filenames are sorted so the result does
    not depend on directory-walk order.

    Raises:
        DevCheckError: an expected hidden test file is missing -- never a
            hash computed over whatever happened to be present.
    """
    source_dir = root / "hidden_tests" / f"slice{slice_number}"
    entries = []
    for filename in sorted(HIDDEN_TEST_FILENAMES):
        file_path = source_dir / filename
        if not file_path.is_file():
            raise DevCheckError(f"hidden test file not found: {file_path}")
        entries.append(f"{filename}:{hashlib.sha256(file_path.read_bytes()).hexdigest()}")
    manifest = "\n".join(entries)
    return hashlib.sha256(manifest.encode("utf-8")).hexdigest()


def run_hidden_tests(worktree: Path, slice_number: int, root: Path, policy: dict[str, Any]) -> dict[str, str]:
    """Copy this slice's hidden tests into the worktree and run pytest once.

    Never points pytest at both hidden_tests/slice1/ and hidden_tests/slice2/
    in the same invocation -- they share filenames and collection would fail
    (see README.md/AGENTS.md's note on the hidden tests).

    Returns:
        Mapping of worktree-relative node id (e.g. "tests/test_hA.py::test_A01_...")
        to one of "passed", "failed", "error", "skipped".

    Raises:
        DevCheckError: pytest crashed, produced no junit XML, or reported a
            collection/setup error -- all loud failures, never a zero score.
    """
    source_dir = root / "hidden_tests" / f"slice{slice_number}"
    for filename in HIDDEN_TEST_FILENAMES:
        if not (source_dir / filename).is_file():
            raise DevCheckError(f"hidden test file not found: {source_dir / filename}")

    tests_dir = worktree / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    for filename in HIDDEN_TEST_FILENAMES:
        shutil.copy2(source_dir / filename, tests_dir / filename)

    junit_fd, junit_name = tempfile.mkstemp(prefix="dev-check-junit-", suffix=".xml")
    os.close(junit_fd)
    junit_path = Path(junit_name)
    try:
        cmd = [
            policy["python_interpreter"],
            "-m",
            "pytest",
            "tests/test_hA.py",
            "tests/test_hB.py",
            f"--junitxml={junit_path}",
            "-q",
        ]
        try:
            result = subprocess.run(
                cmd,
                cwd=worktree,
                capture_output=True,
                text=True,
                timeout=policy["subprocess_timeout_seconds"],
            )
        except subprocess.TimeoutExpired as exc:
            raise DevCheckError(f"pytest timed out grading slice {slice_number} in {worktree}: {exc}") from exc

        if result.returncode not in _PYTEST_SCOREABLE_EXIT_CODES:
            raise DevCheckError(
                f"pytest exited {result.returncode} grading slice {slice_number} in {worktree} "
                f"(not a normal pass/fail outcome); stdout tail:\n{result.stdout[-2000:]}\n"
                f"stderr tail:\n{result.stderr[-2000:]}"
            )
        if not junit_path.is_file() or junit_path.stat().st_size == 0:
            raise DevCheckError(
                f"pytest exited {result.returncode} but wrote no junit XML grading slice {slice_number}; "
                f"stdout tail:\n{result.stdout[-2000:]}"
            )
        return _parse_junit_outcomes(junit_path, slice_number)
    finally:
        junit_path.unlink(missing_ok=True)


def _parse_junit_outcomes(junit_path: Path, slice_number: int) -> dict[str, str]:
    tree = ET.parse(junit_path)
    suite = tree.getroot().find("testsuite")
    if suite is None:
        raise DevCheckError(f"junit XML at {junit_path} had no <testsuite> element")

    error_count = int(suite.get("errors", "0"))
    if error_count:
        messages = []
        for testcase in suite.findall("testcase"):
            error_elem = testcase.find("error")
            if error_elem is not None:
                messages.append(f"{testcase.get('classname')}.{testcase.get('name')}: {error_elem.get('message')}")
        raise DevCheckError(
            f"pytest reported {error_count} collection/setup error(s) grading slice {slice_number}, "
            "not a scoreable result: " + "; ".join(messages)
        )

    outcomes: dict[str, str] = {}
    for testcase in suite.findall("testcase"):
        classname = testcase.get("classname") or ""
        name = testcase.get("name") or ""
        module_path = classname.replace(".", "/") + ".py" if classname else ""
        node_id = f"{module_path}::{name}"
        if testcase.find("failure") is not None:
            outcomes[node_id] = "failed"
        elif testcase.find("error") is not None:
            outcomes[node_id] = "error"
        elif testcase.find("skipped") is not None:
            outcomes[node_id] = "skipped"
        else:
            outcomes[node_id] = "passed"
    return outcomes


def score_correctness(outcomes: dict[str, str], groups: list[dict[str, Any]], slice_number: int) -> dict[str, Any]:
    """Score each obligation group as the fraction of its own nodes that passed.

    Returns a dict with `by_obligation` (the group-level {passed, total,
    fraction} the rubric weight is computed from) and `by_node`, the full
    node_id -> outcome map the group counts were derived from, kept as
    per-test evidence so rubric questions (which test drove a difference,
    is a group saturated, what a different partition would score) are
    answerable straight from a scoring-sheet entry instead of by re-grading
    in a fresh worktree. The full per-attempt `by_node` map itself is
    deliberately NOT threaded into tools/model_report.py or
    tools/leaderboard.py -- it stays per-run evidence an analyst reads from
    results/runs/<run_id>/slice-<N>.json directly, since model-report.json
    is already thousands of lines per run. Only the first attempt's own
    outcomes travel onward from there, nested by obligation group rather
    than repeated per attempt (tools/model_report.py's
    `first_attempt_node_outcomes`, one per slice) -- for the rank-support
    diagnostic that needs to know which group's denominator a node counts
    against, not a second copy of this whole map.

    Raises:
        DevCheckError: any collected node is unmapped, or any mapped node
            was not collected -- a partial map is never scored, per
            docs/OBLIGATION-GROUPS.md.
    """
    node_to_group = node_to_group_map(groups)  # also raises on duplicated nodes
    expected_nodes = set(node_to_group)
    collected_nodes = set(outcomes)

    unmapped = sorted(collected_nodes - expected_nodes)
    missing = sorted(expected_nodes - collected_nodes)
    if unmapped or missing:
        problems = []
        if unmapped:
            problems.append(f"collected but not in obligations.yaml: {unmapped}")
        if missing:
            problems.append(f"in obligations.yaml but not collected: {missing}")
        raise DevCheckError(
            f"hidden test collection for slice {slice_number} does not match obligations.yaml exactly; "
            + "; ".join(problems)
        )

    by_obligation: dict[str, dict[str, Any]] = {}
    for group in groups:
        nodes = group.get("tests", [])
        passed = sum(1 for node in nodes if outcomes[node] == "passed")
        total = len(nodes)
        by_obligation[group["id"]] = {"passed": passed, "total": total, "fraction": (passed / total) if total else 0.0}

    return {
        "hidden_tests_passed": sum(v["passed"] for v in by_obligation.values()),
        "hidden_tests_total": sum(v["total"] for v in by_obligation.values()),
        "by_obligation": by_obligation,
        # Sorted so regenerated sheets diff cleanly rather than reordering on
        # every regrade; this is the raw per-test evidence by_obligation was
        # computed from (see docstring above for why it is kept and scoped).
        "by_node": dict(sorted(outcomes.items())),
    }


# --- quality (lint, code-health) --------------------------------------------


# lint.py's exit codes (skills/lint/scripts/lint.py:45-48): EXIT_PASS=0,
# EXIT_FINDINGS=1 (new findings -- a real, scoreable answer, not a failure),
# EXIT_COVERAGE=3 (a coverage gap -- also real data, distinct from a clean
# pass), EXIT_ERROR=2 (the tool itself failed -- genuinely unavailable).
_LINT_SCOREABLE_EXIT_CODES = frozenset({0, 1, 3})

# health.py's exit codes: EXIT_OK=0, EXIT_COVERAGE=3 (also real data);
# EXIT_ERROR=2 stays unavailable. health.py's payload carries no top-level
# verdict of its own (unlike lint.py's), so run_code_health synthesizes one
# from the exit code below.
_HEALTH_SCOREABLE_EXIT_CODES = frozenset({0, 3})
_HEALTH_EXIT_COVERAGE = 3


def _run_quality_tool(
    cmd: list[str], cwd: Path | None, policy: dict[str, Any], tool_name: str, scoreable_exit_codes: frozenset[int]
) -> dict[str, Any]:
    """Run one external quality tool and record its JSON faithfully.

    `scoreable_exit_codes` names the exit codes that carry a usable JSON
    payload for this specific tool -- lint.py and health.py use disjoint
    exit-code vocabularies (see run_lint/run_code_health below), so no
    single "0 means available" assumption can be shared between them -- a
    shared "any nonzero exit is unavailable" rule would misrecord lint.py's
    exit 1, "new findings were found", as unavailable coverage instead of
    the findings themselves.

    Never reinterprets or invents a composite score (no per-attempt
    composite score exists anywhere in the scoring sheet); a genuinely unavailable or
    failing tool is recorded as an explicit marker, never as a clean pass.
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=policy["subprocess_timeout_seconds"],
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"available": False, "error": f"{tool_name} could not be invoked: {exc}"}

    if result.returncode not in scoreable_exit_codes:
        detail = (result.stderr or result.stdout).strip()[-2000:]
        return {"available": False, "error": f"{tool_name} exited {result.returncode}: {detail}"}

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return {"available": False, "error": f"{tool_name} did not emit valid JSON: {exc}"}

    return {"available": True, "raw": payload, "exit_code": result.returncode}


def run_lint(worktree: Path, before_head: str, policy: dict[str, Any]) -> dict[str, Any]:
    """`lint.py check --json --base <before_head>` against the worktree.

    Counts are grouped by linter tool name, from `new_findings` -- the
    differential list lint.py's own `--base` mode computes -- never from
    `tools[].findings`, which is the absolute HEAD finding count and would
    silently count every pre-existing finding as new. The payload's own
    `verdict` and its `uncovered`/`missing_binaries` lists are surfaced too,
    so a coverage gap reads as one in the sheet rather than looking like a
    clean pass. The full raw payload is kept verbatim alongside all of it.

    `--require-coverage` makes lint.py exit 3 ("coverage-gap",
    already scoreable per `_LINT_SCOREABLE_EXIT_CODES`) when a changed
    language in scope has no available linter, instead of silently exiting
    0/1 over whatever partial set of tools happened to be installed --
    without it, an unavailable linter for a language actually present in the
    diff would read as a clean pass, which AGENTS.md forbids.
    """
    cmd = [
        policy["python_interpreter"],
        policy["lint_script"],
        "--repo",
        str(worktree),
        "check",
        "--json",
        "--base",
        before_head,
        "--require-coverage",
    ]
    result = _run_quality_tool(
        cmd, cwd=None, policy=policy, tool_name="lint", scoreable_exit_codes=_LINT_SCOREABLE_EXIT_CODES
    )
    if not result["available"]:
        return result
    payload = result["raw"]
    new_findings = payload.get("new_findings", [])
    result["dimension"] = "tool"
    result["counts"] = dict(Counter(finding["tool"] for finding in new_findings))
    result["verdict"] = payload.get("verdict")
    result["uncovered"] = payload.get("uncovered", [])
    result["missing_binaries"] = payload.get("missing_binaries", [])
    return result


def run_code_health(worktree: Path, before_head: str, policy: dict[str, Any]) -> dict[str, Any]:
    """`health.py analyze --json --base <before_head>` against the worktree.

    health.py has no --repo flag: it always measures its own working
    directory, so cwd is set to the grading worktree. Its `candidates` list
    carries a `kind` per finding (file_size, cyclomatic, duplication,
    dependency_cycle) -- the natural per-category axis for this tool. Unlike
    lint.py, `candidates` is already genuinely differential in `--base` mode
    (health.py drops zero-delta rows itself), so no separate absolute-count
    bug exists here to fix.

    `--require-coverage` makes health.py exit 3 ("coverage-gap",
    already scoreable per `_HEALTH_SCOREABLE_EXIT_CODES`/`_HEALTH_EXIT_COVERAGE`)
    when a required language in scope has unavailable metric coverage,
    rather than silently reporting whatever partial measurement it managed
    -- the same honesty requirement as lint.py's flag above.

    `result["verdict"]` is `"measured"` on a plain exit 0, deliberately not
    `"pass"`: "quality = 1.0" must never mean only "the measurement tool
    ran," since health.py emits no quality verdict of its own anywhere in
    its payload
    (`candidate_selection.verdict` is literally `"none"`); exit 0 here means
    only that the tool ran and produced a payload, however many candidates
    that payload lists -- reading it as "clean" was the defect. This value
    is displayed as a hygiene/coverage badge (leaderboard.py's
    `_quality_summary`), never scored.
    """
    cmd = [
        policy["python_interpreter"],
        policy["health_script"],
        "analyze",
        "--json",
        "--base",
        before_head,
        "--require-coverage",
    ]
    result = _run_quality_tool(
        cmd, cwd=worktree, policy=policy, tool_name="code-health", scoreable_exit_codes=_HEALTH_SCOREABLE_EXIT_CODES
    )
    if not result["available"]:
        return result
    result["dimension"] = "kind"
    result["counts"] = dict(Counter(candidate["kind"] for candidate in result["raw"].get("candidates", [])))
    result["verdict"] = "coverage-gap" if result["exit_code"] == _HEALTH_EXIT_COVERAGE else "measured"
    return result


# --- scope discipline --------------------------------------------------------


def import_pm_lib(policy: dict[str, Any]) -> tuple[Any, Any]:
    """Add PM's scripts/ directory to sys.path and import pm_lib.plan/git_ops.

    Raises:
        DevCheckError: naming the configured path, if pm_lib is not
            importable there.
    """
    pm_scripts_dir = Path(policy["pm_scripts_dir"]).expanduser().resolve()
    if not (pm_scripts_dir / "pm_lib" / "__init__.py").is_file():
        raise DevCheckError(f"project-manager's pm_lib is not importable at policy.yaml's pm_scripts_dir={pm_scripts_dir}")
    if str(pm_scripts_dir) not in sys.path:
        sys.path.insert(0, str(pm_scripts_dir))
    try:
        from pm_lib import git_ops as pm_git_ops  # noqa: PLC0415
        from pm_lib import plan as pm_plan  # noqa: PLC0415
    except ImportError as exc:
        raise DevCheckError(f"failed to import pm_lib from {pm_scripts_dir}: {exc}") from exc
    return pm_plan, pm_git_ops


def compute_scope(
    pm_plan: Any,
    pm_git_ops: Any,
    repo: Path,
    before_head: str,
    commit: str,
    plan_slice: Any,
    run_state: dict[str, Any],
) -> dict[str, Any]:
    """Changed files vs. the effective authorized surface, in the Developer's
    repo -- not the disposable worktree, and not reimplemented: this calls
    pm_lib's own `effective_authorized_files`/`changed_files_between`/
    `unauthorized_files`, the same functions floor.py's fact 5 uses.
    """
    # after_status="": we are scoring one fixed historical commit, not a live
    # dirty tree, so only the committed diff between before_head and commit
    # counts as "changed".
    changed = pm_git_ops.changed_files_between(repo, before_head, commit, "")
    authorized = pm_plan.effective_authorized_files(plan_slice, run_state)
    violations = pm_git_ops.unauthorized_files(changed, authorized)
    return {
        "violations": violations,
        "changed_files": sorted(changed),
        "effective_authorized_surface": authorized,
    }


# --- size/complexity ---------------------------------------------------
#
# ΔLOC (net physical production/test/doc lines) and ΔCC (total production
# function cyclomatic complexity), both measured against THIS SLICE'S OWN
# before_head, never the preceding attempt -- a trajectory against a moving
# base would hide a regression introduced early and never touched again.
# Existing correctness/quality/scope checks already use before_head this
# way; this section just adds two more measurements against the same base.


@lru_cache(maxsize=None)
def _compile_glob(pattern: str) -> re.Pattern[str]:
    """Compile one policy.yaml measurement glob into an anchored regex, with
    "**" given the standard zero-or-more-directories meaning.

    Neither `pathlib.PurePath.match` nor stdlib `fnmatch.translate` on the
    Python versions this repo runs under treat "**" this way: both require
    at least one intervening path separator around it, so policy.yaml's own
    literal `production_paths` glob `"src/**/*.py"` would fail to match
    `"src/merger_rate.py"` -- a file living directly under src/ with no
    subdirectory, which is exactly how relative-velocity's real production
    code is laid out (verified empirically against both stdlib functions
    before writing this; see TestClassifyPath in tests/test_dev_check.py).
    Using either off-the-shelf matcher unmodified would silently sort every
    real production file into "unclassified".

    This hand-rolled translator is deliberately narrow: it understands only
    "**" (zero or more full path segments), "*" (any run of characters
    within one segment) and "?" (one character within one segment) -- the
    only wildcards policy.yaml's measurement globs use. Cached per distinct
    pattern string (there are only ever a handful, one per policy.yaml path
    bucket) rather than recompiled per path classified.
    """
    parts = ["^"]
    i, n = 0, len(pattern)
    while i < n:
        if pattern[i : i + 3] == "**/":
            parts.append("(?:.*/)?")
            i += 3
        elif pattern[i:] == "**":
            parts.append(".*")
            i += 2
        elif pattern[i] == "*":
            parts.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            parts.append("[^/]")
            i += 1
        else:
            parts.append(re.escape(pattern[i]))
            i += 1
    parts.append("$")
    return re.compile("".join(parts))


_MEASUREMENT_BUCKET_ORDER = ("production", "test", "doc")


def classify_path(path: str, measurement: dict[str, Any]) -> str:
    """Classify one repo-relative path into "production", "test", "doc", or
    "unclassified" (a path matching none of policy.yaml's measurement
    globs) -- checked in that fixed order. relative-velocity's own src//
    tests//docs/ prefixes are disjoint, so order never actually decides a
    real classification, but a path is never silently dropped: an
    unclassified path is its own named bucket, counted and reported, never
    folded into production or discarded (AGENTS.md: never silently drop
    data).
    """
    for bucket in _MEASUREMENT_BUCKET_ORDER:
        globs = measurement[f"{bucket}_paths"]
        if any(_compile_glob(pattern).match(path) for pattern in globs):
            return bucket
    return "unclassified"


def parse_numstat(raw: str) -> list[dict[str, Any]]:
    """Parse one `git diff --numstat` invocation's stdout into one record
    per changed path: `{"path": str, "added": int | None, "deleted": int |
    None, "binary": bool}`.

    A binary file's numstat line carries "-" for both counts (git's own
    convention) -- recorded as `binary=True` with `added`/`deleted` left
    `None`, never coerced to 0 (AGENTS.md: an unavailable measurement is
    recorded unavailable, never as a clean pass or a zero -- the same
    principle applies to an unmeasurable line count). Callers must run this
    tool with `--no-renames` (see compute_loc_delta): with it, git never
    emits the `old => new`/`{old => new}` rename path syntax this parser
    does not attempt to understand -- a rename becomes a plain delete-line
    plus a plain add-line instead, which is the honest accounting for
    *physical* lines this measurement is defined as.

    Raises:
        DevCheckError: a line does not split into exactly three tab-separated
            fields -- naming the offending line, never silently skipped.
    """
    records: list[dict[str, Any]] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        fields = line.split("\t", 2)
        if len(fields) != 3:
            raise DevCheckError(f"unparsable 'git diff --numstat' line (expected 3 tab-separated fields): {line!r}")
        added_raw, deleted_raw, path = fields
        binary = added_raw == "-" or deleted_raw == "-"
        records.append(
            {
                "path": path,
                "added": None if binary else int(added_raw),
                "deleted": None if binary else int(deleted_raw),
                "binary": binary,
            }
        )
    return records


class LineClassificationError(DevCheckError):
    """One Python source could not be parsed or tokenized for the
    code/docstring/comment/blank decomposition below. Carries the reason;
    the caller (decompose_production_categories) decides whether that
    makes the whole `production_categories` block unavailable -- a
    Developer attempt can legitimately commit syntactically broken code,
    so this must never abort grading on its own.
    """


_LOC_CATEGORY_DEFINITION_AST_TOKENIZE = "ast_tokenize_line_classification"
_LOC_CATEGORIES = ("code", "docstring", "comment", "blank")

# Token types that carry no line-classification weight of their own: NL/
# NEWLINE/INDENT/DEDENT/ENCODING/ENDMARKER are structural noise the
# tokenizer emits regardless of content, and COMMENT is handled separately
# below (comment tokens only win a line not already claimed by code).
_NON_CODE_TOKEN_TYPES = frozenset(
    {
        tokenize.NL,
        tokenize.NEWLINE,
        tokenize.INDENT,
        tokenize.DEDENT,
        tokenize.ENCODING,
        tokenize.ENDMARKER,
        tokenize.COMMENT,
    }
)


def _char_col_from_byte_col(line: str, byte_col: int) -> int:
    """Convert one AST `col_offset`/`end_col_offset` (a UTF-8 **byte**
    offset from the start of `line`, per the `ast` module's documented
    convention) into the **character** offset `tokenize` reports for the
    same position.

    Comparing the two coordinate systems directly, uncorrected, is wrong
    whenever a line has a non-ASCII character before the column in
    question -- e.g. a non-ASCII identifier on the same line as a
    docstring's opening quote -- silently misclassifying that docstring's
    continuation lines as code. `ast`'s own offsets always land on a
    codepoint boundary, so slicing the line's UTF-8 encoding at the byte
    offset and decoding never raises `UnicodeDecodeError` on a well-formed
    ast.parse result.
    """
    return len(line.encode("utf-8")[:byte_col].decode("utf-8"))


def _docstring_token_spans(source: str) -> set[tuple[int, int, int, int]]:
    """Every AST-docstring expression's exact token span (start line, start
    col, end line, end col) in `source` -- the first statement of a
    Module/ClassDef/FunctionDef/AsyncFunctionDef body, when it is a bare
    string-constant Expr. A string expression anywhere else in a body is
    ordinary code, never a docstring, per this decomposition's fixed
    precedence (see classify_source_lines).

    The returned span's columns are in `tokenize`'s character-offset
    convention, not `ast`'s own UTF-8-byte convention -- see
    `_char_col_from_byte_col` -- since `_within_a_docstring_span` compares
    these spans directly against `tokenize.TokenInfo.start`/`.end`.

    Raises:
        LineClassificationError: `source` is not valid Python (ast.parse
            failure) -- named with the underlying SyntaxError.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise LineClassificationError(f"ast.parse failed: {exc}") from exc
    # Split on newlines ONLY. str.splitlines() also breaks on \f, \v and
    # other Unicode line boundaries that ast does not count as physical
    # lines, so a form feed (legal, and real in older Python source)
    # would shift every subsequent lineno and convert the wrong line's
    # columns.
    lines = source.split("\n")

    spans: set[tuple[int, int, int, int]] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = node.body
        if not body:
            continue
        first = body[0]
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            value = first.value
            start_col = _char_col_from_byte_col(lines[value.lineno - 1], value.col_offset)
            end_col = _char_col_from_byte_col(lines[value.end_lineno - 1], value.end_col_offset)
            spans.add((value.lineno, start_col, value.end_lineno, end_col))
    return spans


def _within_a_docstring_span(token: tokenize.TokenInfo, docstring_spans: set[tuple[int, int, int, int]]) -> bool:
    """Is this token wholly inside one AST-docstring expression's span?

    (line, column) pairs compare lexicographically, which is exactly the
    ordering needed: a token is contained when it starts no earlier than
    the span's start and ends no later than its end.
    """
    return any(
        (start_line, start_col) <= token.start and token.end <= (end_line, end_col)
        for start_line, start_col, end_line, end_col in docstring_spans
    )


def classify_source_lines(source: str) -> dict[str, int]:
    """Classify every physical line of one Python source into exactly one of
    code/docstring/comment/blank; the four counts always sum to the
    source's own physical line count.

    Precedence (fixed; see the implementation-plan brief this encodes):
      1. Every line touched by a non-structural, non-docstring token is
         `code` -- the FULL token span (start line through end line
         inclusive), not just its start line, so a multi-line non-docstring
         string constant or a bracketed/backslash continuation is not
         mistaken for blank.
      2. Every line in an AST-docstring token's span that is not already
         `code` is `docstring` (a docstring followed on the same physical
         line by a semicolon and a statement is legal Python, and that line
         is `code`, not `docstring` -- code wins).
      3. Every line carrying a COMMENT token that is not already `code` or
         `docstring` is `comment`.
      4. Everything left unmarked is `blank`.

    Raises:
        LineClassificationError: `source` fails `ast.parse` or
            `tokenize.generate_tokens` -- names the underlying error. The
            caller decides what an unparsable revision means for scoring;
            this function only classifies.
    """
    docstring_spans = _docstring_token_spans(source)

    physical_line_count = source.count("\n") + (1 if source and not source.endswith("\n") else 0)
    labels: dict[int, str] = {}

    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError) as exc:
        raise LineClassificationError(f"tokenize.generate_tokens failed: {exc}") from exc

    comment_lines: set[int] = set()
    for tok in tokens:
        start_line, _ = tok.start
        end_line, _ = tok.end
        if tok.type == tokenize.COMMENT:
            comment_lines.add(start_line)
            continue
        if tok.type in _NON_CODE_TOKEN_TYPES:
            continue
        if tok.type == tokenize.STRING and _within_a_docstring_span(tok, docstring_spans):
            # Skip only a STRING token lying wholly INSIDE a docstring
            # expression's own span. Containment, not a start-line match:
            # `"""doc"""; x = """a\nb"""` puts a non-docstring multi-line
            # string on the docstring's own start line, and a start-line
            # test would skip it and leave its interior lines looking
            # blank. Containment also keeps an implicitly concatenated
            # docstring (`"""a""" """b"""`, one ast.Constant but two STRING
            # tokens) classified as docstring rather than code.
            continue
        for line in range(start_line, end_line + 1):
            labels[line] = "code"

    for start, _, end, _ in docstring_spans:
        for line in range(start, end + 1):
            labels.setdefault(line, "docstring")

    for line in comment_lines:
        labels.setdefault(line, "comment")

    counts = {category: 0 for category in _LOC_CATEGORIES}
    for line in range(1, physical_line_count + 1):
        counts[labels.get(line, "blank")] += 1
    return counts


def compute_loc_delta(repo: Path, before_head: str, commit: str, measurement: dict[str, Any]) -> dict[str, Any]:
    """ΔLOC: net physical lines added to production/test/doc source between
    `before_head` and `commit`.

    `git diff --numstat --no-renames` over the WHOLE diff, with every
    changed path then classified in Python against policy.yaml's globs
    (classify_path) -- never a git pathspec (`**` pathspec semantics need
    `:(glob)` magic and are a silent-surprise risk this tool would rather
    not depend on). `--no-renames` is deliberate: a rename becomes a
    delete+add pair, the honest accounting for physical lines, and it keeps
    every path in numstat's plain `<path>` format (see parse_numstat).

    Test and doc deltas are recorded in their own buckets and never netted
    against production -- each bucket carries its own added/deleted/net.
    `binary_files` lists the paths whose line counts are genuinely
    unmeasurable (git's own "-"/"-" numstat convention) rather than folding
    them into 0.

    This block has no external-tool failure mode distinct from a
    fundamental git failure that already aborts grading elsewhere
    (compute_scope's pm_git_ops calls, run_git itself) -- `available` is
    always True here; the key exists only for shape symmetry with
    `complexity` below, which genuinely can be unavailable (an external
    health_script that failed to run).
    """
    raw = run_git(repo, "diff", "--numstat", "--no-renames", before_head, commit)
    records = parse_numstat(raw)
    buckets: dict[str, dict[str, Any]] = {
        bucket: {"added": 0, "deleted": 0, "net": 0, "files": [], "binary_files": []}
        for bucket in (*_MEASUREMENT_BUCKET_ORDER, "unclassified")
    }
    for record in records:
        bucket = buckets[classify_path(record["path"], measurement)]
        bucket["files"].append(record["path"])
        if record["binary"]:
            bucket["binary_files"].append(record["path"])
            continue
        bucket["added"] += record["added"]
        bucket["deleted"] += record["deleted"]
        bucket["net"] += record["added"] - record["deleted"]
    return {"available": True, "loc_definition": measurement["loc_definition"], "buckets": buckets}


def run_code_health_absolute(worktree: Path, policy: dict[str, Any]) -> dict[str, Any]:
    """`health.py analyze --all --json` against `worktree`'s current
    checkout -- the complete, non-differential function inventory ΔCC needs
    at both the baseline and endpoint revision.

    Deliberately `--all`, not `--base`: the differential invocation
    `run_code_health` above already makes narrows to changed files and
    cannot supply a complete baseline total, which is exactly why this
    absolute run is needed at both ends -- writing a second, parallel
    complexity implementation here instead would be exactly the "do not
    write a parallel complexity implementation" mistake the plan warns
    against.

    `--require-coverage` is NOT passed (unlike run_code_health): that flag
    only ever makes health.py exit 3 when requested coverage is missing
    (verified against health.py's own argument handling), so without it
    health.py exits 0 or 2 (genuine failure) -- a coverage gap here (lizard
    unavailable for non-Python files) is recorded as this block's own
    `coverage_note` (via facts.lizard.error, see _extract_functions), not
    surfaced as a hard failure that would prevent scoring anything else in
    this attempt.
    """
    cmd = [policy["python_interpreter"], policy["health_script"], "analyze", "--all", "--json"]
    return _run_quality_tool(
        cmd, cwd=worktree, policy=policy, tool_name="code-health(absolute)", scoreable_exit_codes=frozenset({0})
    )


def _extract_functions(health_payload: dict[str, Any]) -> tuple[list[dict[str, Any]], str | None]:
    """Every function health.py found at one revision, Python and non-Python
    together: `facts.python.functions[]` plus `facts.lizard.functions[]`
    (each entry carries `path`, `name`, `line`, `cyclomatic`) -- summed
    together, never derived from `candidates` (capped at `limit_per_family=5`
    and silent about
    functions that were removed entirely, so counting it would turn a
    display cap into a scoring ceiling).

    Returns:
        (functions, coverage_note). `coverage_note` is a named string
        exactly when `facts.lizard.error` is set -- non-Python complexity
        coverage was unavailable for this revision (e.g. lizard not
        installed). This is reported, never silently treated as "zero
        non-Python functions existed" (AGENTS.md: an unavailable
        measurement is recorded unavailable, never a clean pass or a zero).
    """
    facts = health_payload.get("facts") or {}
    python_functions = (facts.get("python") or {}).get("functions") or []
    lizard = facts.get("lizard") or {}
    lizard_functions = lizard.get("functions") or []
    coverage_note = None
    lizard_error = lizard.get("error")
    if lizard_error:
        coverage_note = f"non-Python complexity coverage unavailable: {lizard_error}"
    return [*python_functions, *lizard_functions], coverage_note


def _complexity_bucket_stats(
    functions: list[dict[str, Any]], bucket: str, measurement: dict[str, Any]
) -> dict[str, Any]:
    """One revision's, one bucket's complexity summary: total cyclomatic
    complexity, the single largest function, and the set of function
    identities present (`(path, name)` -- line numbers shift with unrelated
    edits above a function, so they play no part in identity).
    """
    matched = [f for f in functions if classify_path(f.get("path", ""), measurement) == bucket]
    identities = {(f.get("path"), f.get("name")) for f in matched}
    return {
        "total": sum(f.get("cyclomatic", 0) for f in matched),
        "max_function_cyclomatic": max((f.get("cyclomatic", 0) for f in matched), default=None),
        "identities": identities,
    }


def compute_complexity_delta(
    baseline_payload: dict[str, Any], endpoint_payload: dict[str, Any], measurement: dict[str, Any]
) -> dict[str, Any]:
    """ΔCC: total production (and, separately, test) function cyclomatic
    complexity, endpoint minus baseline.

    **ΔCC is descriptive, not a penalty.** Splitting one function into three
    raises the total through added function-entry counts alone, with no
    change in what the code does -- this is displayed in every report this
    repo generates, never scored or blended into any ranking number.

    Args:
        baseline_payload / endpoint_payload: the raw `analyze --all --json`
            payloads from run_code_health_absolute, at before_head and at
            the attempt's commit respectively.

    Returns:
        `{"available": True, "coverage_note": str | None, "production":
        {...}, "test": {...}}`, each bucket carrying `baseline_total`,
        `endpoint_total`, `net`, `max_function_cyclomatic` at both ends, and
        `function_count` (baseline/endpoint/added/removed) -- `added`/
        `removed` from a plain set difference of function identities, so a
        removed function is reflected even though it contributes nothing to
        either total.
    """
    baseline_functions, baseline_note = _extract_functions(baseline_payload)
    endpoint_functions, endpoint_note = _extract_functions(endpoint_payload)
    coverage_note = "; ".join(note for note in (baseline_note, endpoint_note) if note) or None

    result: dict[str, Any] = {"available": True, "coverage_note": coverage_note}
    for bucket in ("production", "test"):
        baseline_stats = _complexity_bucket_stats(baseline_functions, bucket, measurement)
        endpoint_stats = _complexity_bucket_stats(endpoint_functions, bucket, measurement)
        result[bucket] = {
            "baseline_total": baseline_stats["total"],
            "endpoint_total": endpoint_stats["total"],
            "net": endpoint_stats["total"] - baseline_stats["total"],
            "max_function_cyclomatic": {
                "baseline": baseline_stats["max_function_cyclomatic"],
                "endpoint": endpoint_stats["max_function_cyclomatic"],
            },
            "function_count": {
                "baseline": len(baseline_stats["identities"]),
                "endpoint": len(endpoint_stats["identities"]),
                "added": len(endpoint_stats["identities"] - baseline_stats["identities"]),
                "removed": len(baseline_stats["identities"] - endpoint_stats["identities"]),
            },
        }
    return result


# A slice's baseline complexity measurement is constant across its whole PM
# epoch (before_head doesn't change), so caching it here turns "one absolute
# analyzer run per attempt plus one per epoch" into "one per attempt plus
# one per epoch, ever" across a whole grade_run.py invocation --
# grade_run.py calls dev_check.main() in-process, per attempt, so a plain
# module-level dict is a real cache across every attempt graded in one run.
# Deliberately process-local, never a file on disk: a disk cache could go stale across a
# policy.yaml edit (a changed production_paths glob, a metric_version bump)
# with nothing to invalidate it, which this module-level dict sidesteps
# simply by not surviving past one process.
_BASELINE_COMPLEXITY_CACHE: dict[tuple[str, str], dict[str, Any]] = {}


def _baseline_complexity_payload(repo: Path, before_head: str, policy: dict[str, Any]) -> dict[str, Any]:
    """The cached (or freshly computed) `run_code_health_absolute` result at
    `before_head`, in its own disposable worktree -- distinct from, and
    torn down independently of, the attempt's own endpoint worktree (nesting
    two disposable worktrees under different temp dirs is fine).
    """
    cache_key = (str(repo), before_head)
    cached = _BASELINE_COMPLEXITY_CACHE.get(cache_key)
    if cached is not None:
        return cached
    with grading_worktree(repo, before_head, policy) as baseline_worktree:
        payload = run_code_health_absolute(baseline_worktree, policy)
    _BASELINE_COMPLEXITY_CACHE[cache_key] = payload
    return payload


_MISSING_BLOB_STDERR_MARKERS = ("does not exist", "exists on disk, but not in")


def _read_blob(repo: Path, revision: str, path: str) -> str | None:
    """`git show <revision>:<path>`'s text, or None when the blob genuinely
    does not exist at that revision (git's "path ... does not exist" /
    "exists on disk, but not in" stderr) -- the caller decides whether a
    missing blob is legitimate (file added/deleted in this diff) or a named
    error.

    Deliberately not `run_git`: that helper raises DevCheckError on ANY
    non-zero exit, including a missing-path exit this function must instead
    distinguish and return as None.

    Raises:
        DevCheckError: `git show` exits non-zero for a reason OTHER than
            the path being genuinely absent at that revision (A6: a bad
            repo, an I/O error, a corrupt object -- any such invocation
            failure must never be silently folded into "file does not
            exist" and counted as zero lines). Names the revision, path,
            exit code and stderr.
    """
    result = subprocess.run(
        ["git", "-C", str(repo), "show", f"{revision}:{path}"], check=False, capture_output=True, text=True
    )
    if result.returncode != 0:
        if any(marker in result.stderr for marker in _MISSING_BLOB_STDERR_MARKERS):
            return None
        raise DevCheckError(
            f"git show {revision}:{path} failed (exit {result.returncode}), and not with the expected "
            f"missing-path message -- refusing to treat this as an absent blob. stderr: {result.stderr.strip()!r}"
        )
    return result.stdout


def decompose_production_categories(
    repo: Path, before_head: str, commit: str, loc: dict[str, Any]
) -> dict[str, Any]:
    """Decompose the production bucket's net physical ΔLOC (already computed
    by `compute_loc_delta`, in `loc["buckets"]["production"]`) into
    code/docstring/comment/blank, per `policy.yaml`'s
    `loc_category_definition` (currently the only implementation: AST
    docstrings + tokenize, see `classify_source_lines`).

    Production only (scope fixed by the review this responds to -- see the
    module docstring's Stage-4 note): test and doc buckets are never
    decomposed here, deliberately, because the need this responds to is
    specifically about judging economy of *implementation*, not tests or
    prose.

    Returns `{"available": False, "error": ...}` (never zeros) when any
    production file in this diff is binary, or when any production file
    fails to parse/tokenize at either revision it exists at -- a Developer
    attempt can legitimately commit syntactically broken code, so this must
    never raise past its caller and abort the rest of grading.

    Reconciliation invariant (asserted, not merely hoped): the sum of the
    four categories' nets MUST equal `loc["buckets"]["production"]["net"]`,
    the same number `compute_loc_delta` already derived from `git diff
    --numstat`. A mismatch means a newline/decoding/path/token-span
    accounting bug in this function, and must be a loud, named failure --
    never a quietly published, silently-wrong number.
    """
    production = loc["buckets"]["production"]
    if production["binary_files"]:
        return {
            "available": False,
            "error": (
                "production bucket contains binary file(s), unmeasurable for line categories: "
                f"{', '.join(production['binary_files'])}"
            ),
        }

    baseline_totals = {category: 0 for category in _LOC_CATEGORIES}
    endpoint_totals = {category: 0 for category in _LOC_CATEGORIES}

    numstat_records = {
        record["path"]: record
        for record in parse_numstat(run_git(repo, "diff", "--numstat", "--no-renames", before_head, commit))
    }

    for path in production["files"]:
        record = numstat_records.get(path)
        baseline_source = _read_blob(repo, before_head, path)
        endpoint_source = _read_blob(repo, commit, path)

        # A missing blob is legitimate only when numstat itself shows the
        # file was purely added (missing at baseline) or purely deleted
        # (missing at endpoint) in this diff -- any other missing blob is a
        # named error, never silently zeroed (AGENTS.md: never guess a
        # missing value).
        # "Added" vs "deleted" only, from the diff record itself -- never a
        # positive-line-count requirement: an *empty* added file has
        # added == deleted == 0 too, and is exactly as legitimately absent
        # at baseline as a non-empty one. A path present at baseline can
        # never show deleted == 0 in a diff that also has it missing at
        # baseline (there would be nothing to delete from), so `deleted ==
        # 0` alone already establishes "this path did not exist before
        # this diff", and symmetrically for `added == 0` at the endpoint.
        baseline_add_only = record is not None and not record["binary"] and record["deleted"] == 0
        endpoint_delete_only = record is not None and not record["binary"] and record["added"] == 0

        if baseline_source is None and not baseline_add_only:
            raise DevCheckError(
                f"production_categories: {path!r} missing blob at baseline {before_head} but numstat "
                f"record {record!r} does not show a pure add -- refusing to treat this as zero"
            )
        if endpoint_source is None and not endpoint_delete_only:
            raise DevCheckError(
                f"production_categories: {path!r} missing blob at endpoint {commit} but numstat "
                f"record {record!r} does not show a pure delete -- refusing to treat this as zero"
            )

        try:
            baseline_counts = classify_source_lines(baseline_source) if baseline_source is not None else {
                category: 0 for category in _LOC_CATEGORIES
            }
            endpoint_counts = classify_source_lines(endpoint_source) if endpoint_source is not None else {
                category: 0 for category in _LOC_CATEGORIES
            }
        except LineClassificationError as exc:
            return {"available": False, "error": f"{path!r}: {exc}"}

        for category in _LOC_CATEGORIES:
            baseline_totals[category] += baseline_counts[category]
            endpoint_totals[category] += endpoint_counts[category]

    net_totals = {category: endpoint_totals[category] - baseline_totals[category] for category in _LOC_CATEGORIES}
    reconciled_sum = sum(net_totals.values())
    if reconciled_sum != production["net"]:
        raise DevCheckError(
            "production_categories: reconciliation invariant violated -- category nets sum to "
            f"{reconciled_sum} but compute_loc_delta's production net (git --numstat) is "
            f"{production['net']} for files {production['files']} between {before_head} and {commit}"
        )

    return {
        "available": True,
        "definition": _LOC_CATEGORY_DEFINITION_AST_TOKENIZE,
        "baseline": baseline_totals,
        "endpoint": endpoint_totals,
        "net": net_totals,
    }


def compute_size_complexity(
    repo: Path,
    before_head: str,
    commit: str,
    endpoint_health_payload: dict[str, Any],
    policy: dict[str, Any],
    measurement: dict[str, Any],
) -> dict[str, Any]:
    """The `size_complexity` attempt-entry block: ΔLOC and ΔCC, both measured
    against this slice's own before_head, never the preceding attempt.

    Args:
        endpoint_health_payload: `run_code_health_absolute`'s result at
            `commit`, computed by the caller INSIDE the attempt's own
            grading worktree, before `run_hidden_tests` copies this slice's
            held-out tests in (main()'s lint/code-health-before-copy ordering constraint -- both
            existing quality tools already obey this; the absolute health
            run needs to as well, or it silently attributes the bench's own
            hidden tests to the Developer). This function never opens a
            second worktree at `commit` itself -- only the baseline (at
            `before_head`, via _baseline_complexity_payload) gets one of its
            own here.
    """
    loc = compute_loc_delta(repo, before_head, commit, measurement)
    # Production-only code/docstring/comment/blank decomposition of the
    # physical net above -- additive, never changes `loc["buckets"]` itself
    # (see decompose_production_categories's own docstring for scope and
    # the reconciliation invariant it asserts).
    loc["production_categories"] = decompose_production_categories(repo, before_head, commit, loc)

    if not endpoint_health_payload.get("available"):
        complexity: dict[str, Any] = {"available": False, "error": f"endpoint: {endpoint_health_payload.get('error')}"}
    else:
        baseline_payload = _baseline_complexity_payload(repo, before_head, policy)
        if not baseline_payload.get("available"):
            complexity = {"available": False, "error": f"baseline: {baseline_payload.get('error')}"}
        else:
            complexity = compute_complexity_delta(baseline_payload["raw"], endpoint_health_payload["raw"], measurement)

    return {
        "metric_version": measurement["metric_version"],
        "baseline_commit": before_head,
        "endpoint_commit": commit,
        "loc": loc,
        "complexity": complexity,
    }


# --- scoring sheet (cumulative, upserted) -----------------------------------


def load_existing_sheet(out_path: Path, run_id: str, slice_number: int) -> dict[str, Any] | None:
    """Load the cumulative scoring sheet at `out_path`, if one exists.

    The identity check (bench_lib.validate_sheet_identity) happens here
    rather than only at write time because `resolve_before_head` reads this
    sheet's per-attempt `provenance.base_commit` as its fallback. A sheet
    belonging to a different run or slice -- reachable only by pointing
    `--out` at one deliberately, since the default path is keyed by both --
    would otherwise supply a foreign base commit that the whole grading pass
    is then measured against, before the write-time guard finally rejects
    it. Failing here costs nothing and names the real fault.

    Raises:
        DevCheckError: the sheet on disk is for a different run or slice.
    """
    if not out_path.is_file():
        return None
    with out_path.open("r", encoding="utf-8") as handle:
        sheet = json.load(handle)
    try:
        bench_lib.validate_sheet_identity(sheet, run_id, slice_number, out_path)
    except bench_lib.BenchLibError as exc:
        raise DevCheckError(str(exc)) from exc
    return sheet


def resolve_accepted_at_attempt(existing_sheet: dict[str, Any] | None, slice_status: str | None, attempt: int) -> int | None:
    if slice_status == "accepted":
        return attempt
    return existing_sheet.get("accepted_at_attempt") if existing_sheet else None


def resolve_model_performance_ref(run_dir: Path, existing_sheet: dict[str, Any] | None) -> str | None:
    candidate = run_dir / "model-performance.md"
    if candidate.is_file():
        return str(candidate)
    return existing_sheet.get("pm_model_performance_ref") if existing_sheet else None


def build_provenance(
    run_state: dict[str, Any],
    policy_path: Path,
    obligations_path: Path,
    before_head: str,
    root: Path,
    slice_number: int,
) -> dict[str, Any]:
    """plan_hash, policy_hash, obligations_hash, hidden_tests_hash, base_commit,
    pm_skill_version -- the scoring sheet's provenance block, recorded per attempt.

    A sheet-level provenance field, overwritten on every upsert, made an
    earlier attempt look like it was graded under whatever policy.yaml or
    obligations.yaml happen to read at the moment of a *later* attempt's
    grade -- exactly the "rules changed silently" case this field exists to
    detect. So this is captured once, at an attempt's first grade,
    and upsert_attempt() never rewrites it on a regrade of that same
    attempt. `obligations_hash` is the sha256 of the obligation map --
    docs/OBLIGATION-GROUPS.md establishes that the partition *is* the
    correctness rubric, so a later change to it must be as detectable as a
    policy or plan change. `obligations_hash` alone is not sufficient,
    though: it hashes only the *partition* -- the rubric weight -- not the
    hidden test bodies themselves, which are the rubric's actual content.
    An edit to a single assertion in a hidden test file changes every
    attempt's recorded correctness score without changing the partition at
    all, so `hidden_tests_hash` (`hidden_tests_manifest_hash`) hashes the
    test files that `run_hidden_tests` actually copies into the grading
    worktree for this slice, closing that gap. A hand-maintained
    "correctness metric version" was considered and rejected instead: a
    content hash cannot lie, whereas a version can be bumped for a
    comment-only edit or left stale across a material one, and since such a
    key would live in policy.yaml, bumping it would change `policy_hash`
    anyway -- it would add no detection capability, just a second source of
    truth and a config key nothing needs. `pm_skill_version` is null (not a
    guess): project-manager carries no version marker anywhere in
    SKILL.md, README.md, or scripts/.

    Lifecycle note: like the rest of this block, `hidden_tests_hash` is
    captured once at an attempt's first grade and `upsert_attempt()` never
    rewrites it later. That means it appears only on attempts graded into a
    *fresh* scoring sheet -- a regrade of an existing cohort in place leaves
    historical attempts without it. This is why a cohort regrade archives
    `results/` via `cohort_run.py reset-leaderboard` and regrades into a
    clean tree, rather than upserting in place.
    """
    return {
        "plan_hash": run_state.get("plan", {}).get("sha256"),
        "policy_hash": hashlib.sha256(policy_path.read_bytes()).hexdigest(),
        "obligations_hash": hashlib.sha256(obligations_path.read_bytes()).hexdigest(),
        "hidden_tests_hash": hidden_tests_manifest_hash(root, slice_number),
        "base_commit": before_head,
        "pm_skill_version": None,
    }


def upsert_attempt(
    existing_sheet: dict[str, Any] | None,
    *,
    run_id: str,
    developer: dict[str, Any],
    slice_number: int,
    run_status: dict[str, Any],
    attempt_entry: dict[str, Any],
    accepted_at_attempt: int | None,
    pm_model_performance_ref: str | None,
) -> dict[str, Any]:
    """Upsert one attempt into the cumulative scoring sheet, by attempt number.

    Every other attempt is preserved untouched, in place, along with any
    `reviews` list already recorded on the attempt being replaced (Tool 2/3's
    job, not this tool's -- this upsert must never clobber it; the list holds
    one record per review commission, never one slot per role, so a panel of
    reviewers survives intact); that attempt's own `provenance` if it was
    already graded once (captured at an attempt's first grade and never
    rewritten, so a later policy.yaml/obligations.yaml edit cannot silently
    make an earlier attempt look graded under new rules); and that attempt's
    own `pm_attempts_counter` if it was already graded once (the same
    preservation rule as provenance: `--attempt` can regrade any
    existing historical attempt, and PM's own `attempts` counter on
    `run.json` reflects only the *current* state, not what it was when this
    attempt was first opened -- a stopped-then-restarted slice resets it to
    0, so re-grading attempt 0 after a later restart would otherwise silently
    overwrite its recorded counter with a value that now points at the
    wrong `attempt-<n>/` artifacts on disk, defeating the field's only
    purpose).

    `developer` is the structured identity block `bench_lib
    .resolve_developer_identity` returns -- a structured `{tool, model,
    effort}` block rather than a flat `model` string, so an unattributed run
    is a named gap rather than a model literally named "None". Every attempt
    is graded against the same run, so this is
    sheet-level data, refreshed on every upsert exactly like `run_status`
    (a run's identity cannot itself change between attempts; recomputing it
    fresh each grade only means a later `policy.yaml` correction or a newly
    landed PM judgment is picked up on the next regrade rather than frozen
    at whatever it read the first time).

    Raises:
        DevCheckError: an existing sheet at the same path is for a
            different run_id or slice -- writing into it would silently mix
            two runs' data.
    """
    if existing_sheet is None:
        sheet: dict[str, Any] = {
            "run_id": run_id,
            "developer": developer,
            "slice": slice_number,
            "run_status": run_status,
            "attempts": [],
            "accepted_at_attempt": accepted_at_attempt,
            "pm_model_performance_ref": pm_model_performance_ref,
        }
    else:
        try:
            bench_lib.validate_sheet_identity(existing_sheet, run_id, slice_number, Path("<in-memory sheet>"))
        except bench_lib.BenchLibError as exc:
            raise DevCheckError(str(exc)) from exc
        sheet = existing_sheet
        sheet["developer"] = developer
        sheet["run_status"] = run_status
        sheet["accepted_at_attempt"] = accepted_at_attempt
        sheet["pm_model_performance_ref"] = pm_model_performance_ref

    attempts = sheet.setdefault("attempts", [])
    for index, existing_attempt in enumerate(attempts):
        if existing_attempt.get("attempt") == attempt_entry["attempt"]:
            if "reviews" not in attempt_entry and "reviews" in existing_attempt:
                attempt_entry["reviews"] = existing_attempt["reviews"]
            if "provenance" in existing_attempt:
                attempt_entry["provenance"] = existing_attempt["provenance"]
            if "pm_attempts_counter" in existing_attempt:
                attempt_entry["pm_attempts_counter"] = existing_attempt["pm_attempts_counter"]
            attempts[index] = attempt_entry
            break
    else:
        attempts.append(attempt_entry)
    return sheet


def write_sheet_atomically(out_path: Path, sheet: dict[str, Any]) -> None:
    """Write the sheet -- see bench_lib.write_json_atomically() (mkstemp +
    os.replace, temp file cleaned up on failure)."""
    bench_lib.write_json_atomically(out_path, sheet)


# --- CLI ---------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Grade one PM slice attempt: correctness, independent quality, scope discipline."
    )
    parser.add_argument("--run-dir", required=True, type=Path, help="PM run state directory containing run.json and events.jsonl")
    parser.add_argument("--slice", required=True, type=int, help="slice number (1 or 2), matching hidden_tests/obligations.yaml")
    parser.add_argument(
        "--attempt", type=int, default=None,
        help="the monotonic event-derived attempt ordinal to grade (defaults to the latest recorded for the slice)"
    )
    parser.add_argument("--commit", default=None, help="defaults to the Developer repo's current HEAD")
    parser.add_argument(
        "--before-head", default=None,
        help="explicit override for the diff base commit; only needed when resolve_before_head's structural "
        "fallbacks cannot recover it (a first slice that was never graded live and never reviewed)"
    )
    parser.add_argument("--policy", type=Path, default=None, help="defaults to policy.yaml at this repo's root")
    parser.add_argument("--out", type=Path, default=None, help="defaults to results/runs/<run_id>/slice-<N>.json")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = bench_root()
    policy_path = (args.policy or (root / "policy.yaml")).expanduser().resolve()
    policy = load_policy(policy_path)

    run_dir = args.run_dir.expanduser().resolve()
    run_state = load_run_state(run_dir)
    events = read_events(run_dir)

    slice_id = f"Slice {args.slice}"
    entry = find_slice_entry(run_state, slice_id)
    # The sheet's key is the monotonic event-derived ordinal, not PM's own
    # `attempts` counter (which resets on a stopped-then-restarted slice) --
    # PM's counter is still resolved below, but only to record it on the
    # attempt entry, never to key the sheet.
    attempt = resolve_attempt(events, slice_id, args.attempt)
    pm_attempts_counter = resolve_pm_attempts_counter(events, slice_id, attempt)

    # The existing sheet must be loaded *before* resolving before_head --
    # once a slice is accepted, run.json's current_slice no longer names it
    # (finalize_accept clears current_slice in the same write that marks the
    # slice accepted), so before_head can only be recovered from a sheet this
    # tool wrote on an earlier grade of the same attempt. See
    # resolve_before_head's docstring.
    out_path = (args.out or (root / "results" / "runs" / run_state["run_id"] / f"slice-{args.slice}.json")).expanduser().resolve()
    existing_sheet = load_existing_sheet(out_path, run_state["run_id"], args.slice)
    before_head = resolve_before_head(run_state, slice_id, existing_sheet, attempt, entry, args.before_head)

    repo = Path(run_state["repo"]).expanduser().resolve()
    commit = resolve_commit(repo, args.commit)

    pm_plan, pm_git_ops = import_pm_lib(policy)
    plan_path = Path(run_state["plan"]["path"]).expanduser().resolve()
    if not plan_path.is_file():
        raise DevCheckError(f"plan file recorded in run.json not found: {plan_path}")
    plan_slices = pm_plan.parse_plan(plan_path)
    plan_slice = pm_plan.plan_slice_by_id(plan_slices, slice_id)
    if plan_slice is None:
        raise DevCheckError(f"{slice_id!r} not found by parsing plan file {plan_path}")

    obligations = load_obligations(root)
    groups = obligation_groups_for_slice(obligations, args.slice)

    with grading_worktree(repo, commit, policy) as worktree:
        # lint/code-health MUST run before run_hidden_tests copies this
        # slice's held-out test files into worktree/tests/ -- both quality
        # tools run in --base differential mode, which includes untracked
        # files, so measuring after the copy silently attributes the bench's
        # own hidden tests to the Developer (empirically confirmed: lint and
        # code-health both flagged tests/test_hA.py when run in the wrong
        # order). Never reorder this back.
        lint_result = run_lint(worktree, before_head, policy)
        health_result = run_code_health(worktree, before_head, policy)
        # The endpoint complexity measurement follows the same ordering
        # constraint as lint/health above: `analyze --all` also inspects the
        # worktree's untracked files, so it must run before run_hidden_tests
        # copies this slice's held-out tests into worktree/tests/, or the
        # bench's own hidden tests would be counted as the Developer's
        # production/test function inventory.
        endpoint_complexity_payload = run_code_health_absolute(worktree, policy)
        outcomes = run_hidden_tests(worktree, args.slice, root, policy)
        correctness = score_correctness(outcomes, groups, args.slice)
        scope = compute_scope(pm_plan, pm_git_ops, repo, before_head, commit, plan_slice, run_state)

    # Outside the endpoint worktree above: the baseline complexity
    # measurement needs its own, separate disposable worktree at
    # before_head (nesting two is fine -- distinct temp dirs), and is
    # cached per (repo, before_head) across this whole grade_run.py
    # invocation (see _BASELINE_COMPLEXITY_CACHE).
    size_complexity = compute_size_complexity(
        repo, before_head, commit, endpoint_complexity_payload, policy, policy["measurement"]
    )

    # infrastructure_failure_suspected is a heuristic this tool has no basis
    # to compute or set on its own -- if an earlier grade already recorded
    # it true, a regrade must not silently reset it to false. Only a
    # first-time sheet defaults it to false.
    existing_run_status = (existing_sheet or {}).get("run_status") or {}
    run_status = {
        "pm_status": run_state.get("status"),
        "slice_status": entry.get("status"),
        "stop_reason": run_state.get("stop_reason"),
        "infrastructure_failure_suspected": existing_run_status.get("infrastructure_failure_suspected", False),
    }
    provenance = build_provenance(run_state, policy_path, root / OBLIGATIONS_RELATIVE_PATH, before_head, root, args.slice)
    accepted_at_attempt = resolve_accepted_at_attempt(existing_sheet, entry.get("status"), attempt)
    pm_model_performance_ref = resolve_model_performance_ref(run_dir, existing_sheet)

    attempt_entry = {
        "attempt": attempt,
        # PM's own counter, for a human cross-referencing PM's output --
        # never the sheet's key (see resolve_pm_attempts_counter).
        "pm_attempts_counter": pm_attempts_counter,
        "commit_sha": commit,
        "timestamp": utc_now_iso(),
        # Captured fresh here but never rewritten on a regrade of this same
        # attempt -- see build_provenance/upsert_attempt.
        "provenance": provenance,
        "correctness": correctness,
        "quality": {
            # lint.py's Finding record carries no severity dimension at all
            # (see run_lint's docstring) -- named by_tool, not by_severity,
            # to match what it actually groups by.
            "lint_findings_by_tool": lint_result,
            "code_health_findings_by_category": health_result,
        },
        "scope": scope,
        # ΔLOC/ΔCC against this slice's own before_head -- descriptive
        # supporting measures, never scored (see
        # compute_size_complexity/compute_complexity_delta).
        "size_complexity": size_complexity,
        # Read per-attempt from the event log, not from run.json's one
        # decision-per-slice field -- see resolve_pm_decision. None means the
        # attempt is not yet decided.
        "pm_decision": resolve_pm_decision(events, slice_id, attempt),
    }

    # The Developer identity is resolved fresh on every grade, never read as
    # a bare run.json["harness"]["model"] string -- that string alone can be
    # null, which would otherwise let a run with no recorded model rank as a
    # model literally named "None". A genuine conflict between sources is a
    # named problem this tool must
    # not paper over by grading anyway; an unattributed run (no conflict,
    # just nothing recorded) is not an error and is graded normally.
    identity_corrections = (policy.get("identity") or {}).get("corrections") or {}
    developer, identity_problems = bench_lib.resolve_developer_identity(
        run_state, run_id=run_state["run_id"], corrections=identity_corrections
    )
    if identity_problems:
        raise DevCheckError(
            f"Developer identity could not be resolved for run {run_state['run_id']!r}: "
            + "; ".join(identity_problems)
        )

    sheet = upsert_attempt(
        existing_sheet,
        run_id=run_state["run_id"],
        developer=developer,
        slice_number=args.slice,
        run_status=run_status,
        attempt_entry=attempt_entry,
        accepted_at_attempt=accepted_at_attempt,
        pm_model_performance_ref=pm_model_performance_ref,
    )
    write_sheet_atomically(out_path, sheet)
    print(f"wrote {out_path} (attempt {attempt} of {slice_id})")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except DevCheckError as exc:
        print(f"dev_check.py: error: {exc}", file=sys.stderr)
        sys.exit(1)
