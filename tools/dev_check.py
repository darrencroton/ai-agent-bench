#!/usr/bin/env python3
"""Correctness, independent quality, test-suite kill rate, and
scope-discipline grading for one PM slice attempt.

This module is a pure, one-shot grading command: given a PM run directory
and a slice number, it grades exactly one attempt (the latest one, by
default) and upserts one entry into that slice's cumulative scoring sheet.
It never polls, never daemonizes, and never re-invokes itself.

Grading is a single post-hoc pass over a finished run (`tools/grade_run.py`
calls this module once per attempt): a slice's `before_head` is recoverable
from `run.json` after the fact (see `resolve_before_head`), so nothing needs
to happen while PM is still working. Re-running this tool for an attempt
already graded replaces that attempt's row and refreshes its timestamp --
not byte-identical (the timestamp always advances), but it never disturbs
any other attempt or `review_score.py`'s fields on the same one.

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
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterator

import yaml

import bench_lib

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

    # The four machine-specific paths this tool runs or imports from. A `~`
    # prefix is expanded here, once, so one policy.yaml can be shared across
    # an operator's machines; every later use reads the expanded string.
    machine_path_keys = ("pm_scripts_dir", "lint_script", "health_script", "python_interpreter")
    missing = [key for key in machine_path_keys if not policy.get(key)]
    if missing:
        raise DevCheckError(f"policy file {policy_path} is missing required keys: {', '.join(missing)}")
    for key in machine_path_keys:
        if not isinstance(policy[key], str):
            raise DevCheckError(f"policy file {policy_path}: {key} must be a path string, got {policy[key]!r}")
        policy[key] = os.path.expanduser(policy[key])

    # subprocess_timeout_seconds gets its own check, not the blanket one
    # above: every tunable lives in policy.yaml, never hardcoded (AGENTS.md),
    # so this tool must refuse to fall back to an inline default when it is
    # absent, and must refuse a value that could never be a real timeout.
    timeout = policy.get("subprocess_timeout_seconds")
    if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or timeout <= 0:
        raise DevCheckError(
            f"policy file {policy_path} must set subprocess_timeout_seconds to a positive number; "
            f"got {timeout!r}"
        )

    _validate_measurement_policy(policy, policy_path)
    _validate_mutation_gate_policy(policy, policy_path)
    _validate_hygiene_policy(policy, policy_path)
    return policy


_HYGIENE_PATTERN_LIST_KEYS = ("narration_tokens", "commit_process_labels")


def _validate_hygiene_policy(policy: dict[str, Any], policy_path: Path) -> None:
    """Validate the `hygiene` section measure_hygiene reads.

    Raises:
        DevCheckError: the section is missing or not a mapping; a pattern
            list is missing, empty, or holds a non-string or a regex that
            does not compile (naming the key and the offending pattern); or
            `commit_subject_max_length` is not a positive integer.
    """
    hygiene = policy.get("hygiene")
    if not isinstance(hygiene, dict):
        raise DevCheckError(f"policy file {policy_path} is missing its required 'hygiene' section")
    for key in _HYGIENE_PATTERN_LIST_KEYS:
        patterns = hygiene.get(key)
        if not isinstance(patterns, list) or not patterns:
            raise DevCheckError(
                f"policy file {policy_path}'s hygiene.{key} must be a non-empty list of regexes, got {patterns!r}"
            )
        for pattern in patterns:
            if not isinstance(pattern, str):
                raise DevCheckError(f"policy file {policy_path}'s hygiene.{key} entry {pattern!r} is not a string")
            try:
                re.compile(pattern, re.IGNORECASE)
            except re.error as exc:
                raise DevCheckError(
                    f"policy file {policy_path}'s hygiene.{key} pattern {pattern!r} does not compile: {exc}"
                ) from exc
    max_length = hygiene.get("commit_subject_max_length")
    if not isinstance(max_length, int) or isinstance(max_length, bool) or max_length <= 0:
        raise DevCheckError(
            f"policy file {policy_path}'s hygiene.commit_subject_max_length must be a positive integer, "
            f"got {max_length!r}"
        )


def _validate_mutation_gate_policy(policy: dict[str, Any], policy_path: Path) -> None:
    """Validate the `mutation_gate` section measure_test_kill_rate reads.

    Raises:
        DevCheckError: the section is missing or not a mapping, or
            `parallel_workers` is not a positive integer (naming it).
    """
    gate = policy.get("mutation_gate")
    if not isinstance(gate, dict):
        raise DevCheckError(f"policy file {policy_path} is missing its required 'mutation_gate' section")
    workers = gate.get("parallel_workers")
    if not isinstance(workers, int) or isinstance(workers, bool) or workers <= 0:
        raise DevCheckError(
            f"policy file {policy_path}'s mutation_gate.parallel_workers must be a positive integer, got {workers!r}"
        )


# Only the methodology keys are validated here, globally: the three path-glob
# buckets (production_paths/test_paths/doc_paths) describe one task's target
# repo layout, so they live per-task under tasks:<id>:measurement and are
# validated by bench_lib.resolve_task, the single source for that contract.
_MEASUREMENT_REQUIRED_KEYS = ("loc_definition", "loc_category_definition", "metric_version")

# The only ΔLOC definition dev_check.py implements -- an unimplemented
# alternative (e.g. SLOC-excluding-comments) must fail loudly here, exactly
# like load_policy's own "backend" check above, never be silently treated
# as this one.
_LOC_DEFINITION_NET_PHYSICAL_LINES = "net_physical_lines"


def _validate_measurement_policy(policy: dict[str, Any], policy_path: Path) -> None:
    """Validate the global part of the `measurement` section.

    Checks the LOC definition, the line-category definition, and
    `metric_version` -- each a methodology choice applied uniformly to any
    task, hence top-level rather than per-task (see policy.yaml's comment on
    both blocks). The per-task path globs are checked by
    bench_lib.resolve_task, which main() calls on every invocation.

    Raises:
        DevCheckError: naming the missing or malformed key.
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
    metric_version = measurement["metric_version"]
    if not isinstance(metric_version, int) or isinstance(metric_version, bool):
        raise DevCheckError(
            f"policy file {policy_path}'s measurement.metric_version must be an integer, got {metric_version!r}"
        )
    if measurement["loc_definition"] != _LOC_DEFINITION_NET_PHYSICAL_LINES:
        raise DevCheckError(
            f"policy file {policy_path}'s measurement.loc_definition must be "
            f"{_LOC_DEFINITION_NET_PHYSICAL_LINES!r}, the only definition dev_check.py implements; got "
            f"{measurement['loc_definition']!r}"
        )
    if measurement["loc_category_definition"] != _LOC_CATEGORY_DEFINITION_AST_TOKENIZE:
        raise DevCheckError(
            f"policy file {policy_path}'s measurement.loc_category_definition must be "
            f"{_LOC_CATEGORY_DEFINITION_AST_TOKENIZE!r}, the only code/docstring/comment/blank line "
            f"classification dev_check.py implements; got {measurement['loc_category_definition']!r}"
        )


# --- run.json (read-only) -----------------------------------------------


def load_run_state(run_dir: Path) -> dict[str, Any]:
    """Read run.json read-only: no run token, no HMAC verification, no writes.

    This tool never authenticates as PM's controller and never mutates PM
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


def check_run_belongs_to_task(run_state: dict[str, Any], task: dict[str, Any], root: Path) -> Path:
    """Cross-check the RUN being graded against the resolved TASK, returning
    the run's own recorded target repository (resolved).

    run.json records the run's target repo as a trial *worktree* path (e.g.
    relative-velocity-trial-1), never literally equal to
    policy.yaml's tasks:<id>:repo, which points at the vendored substrate
    repo itself -- so membership goes through bench_lib.repo_belongs_to_task's
    structural git-worktree check, NEVER literal path-string equality, which
    would reject every real, valid run. This is what stops an operator's
    mistyped-but-valid --task from silently grading this run under the wrong
    task's rubric: validate_obligations_against_task only checks a task's
    internal configuration, not its association with this specific run.

    Returns:
        The run's recorded repository, resolved -- main() reuses it instead
        of re-resolving run_state["repo"] a second time.

    Raises:
        DevCheckError: run.json records no repository at all, or records one
            that is not a usable string (naming the offending value); the
            recorded repository is neither the configured repo nor a registered
            worktree of it (naming both paths); or the membership cannot be
            determined structurally because git failed on the configured side
            (bench_lib wraps a missing or unexecutable git binary into
            BenchLibError; OSError is caught here too because resolving the
            paths themselves can raise it -- either way a loud failure, never
            a guessed False).
    """
    # A syntactically valid run.json can still carry a non-string repo value
    # (e.g. an integer); refuse it by name rather than letting
    # Path(recorded_raw) below escape as a raw, unnamed TypeError -- the same
    # pattern check_plan_matches_task applies to plan.path.
    recorded_raw = run_state.get("repo")
    if not isinstance(recorded_raw, str) or not recorded_raw:
        raise DevCheckError(
            f"run.json's 'repo' value is missing or not a string (got {recorded_raw!r}); cannot cross-check "
            f"this run against task {task['task_id']!r}'s configured repository"
        )
    recorded = Path(recorded_raw).expanduser().resolve()
    configured = (root / task["repo"]).expanduser().resolve()
    try:
        belongs = bench_lib.repo_belongs_to_task(recorded, configured)
    except (bench_lib.BenchLibError, OSError) as exc:
        raise DevCheckError(
            f"could not determine whether the run's recorded repository {recorded} belongs to task "
            f"{task['task_id']!r}'s configured repo {configured}: {exc}"
        ) from exc
    if not belongs:
        raise DevCheckError(
            f"the run's recorded repository {recorded} is neither task {task['task_id']!r}'s configured repo "
            f"{configured} nor a registered git worktree of it; refusing to grade this run under that "
            "task's rubric"
        )
    return recorded


def check_plan_matches_task(run_state: dict[str, Any], task: dict[str, Any], repo: Path) -> None:
    """Require the run's recorded plan to be content-identical to the task's plan_file.

    Scope discipline is computed from the plan the run itself was initialized
    with (run.json `plan.path`), independently of --task, so without this
    check a task's hidden-test rubric could be scored against scope
    authorization parsed from an unrelated plan. Content, not path, is
    compared: `setup --plan-file` may point a run at a byte-identical copy
    elsewhere, which must grade normally.

    Args:
        run_state: the run's parsed run.json.
        task: the resolved task entry.
        repo: the run's recorded repository (from check_run_belongs_to_task),
            against which the task's plan_file is anchored.

    Raises:
        DevCheckError: run.json records no usable `plan.path` string; either
            plan file cannot be read (naming the unreadable path and the other
            side of the comparison); or the two files differ in content
            (naming both paths and both sha256 digests).
    """
    plan_record = run_state.get("plan")
    recorded_raw = plan_record.get("path") if isinstance(plan_record, dict) else None
    if not isinstance(recorded_raw, str) or not recorded_raw:
        raise DevCheckError(
            f"run.json has no usable 'plan.path' string recorded (got {recorded_raw!r}); cannot verify "
            f"this run was initialized under task {task['task_id']!r}'s configured plan"
        )
    recorded = Path(recorded_raw).expanduser().resolve()
    expected = (repo / task["plan_file"]).expanduser().resolve()
    try:
        recorded_digest = hashlib.sha256(recorded.read_bytes()).hexdigest()
    except OSError as exc:
        raise DevCheckError(
            f"cannot read the run's recorded plan file {recorded} (run.json plan.path={recorded_raw!r}): "
            f"{exc}; cannot verify whether it matches the resolved task {task['task_id']!r}'s configured "
            f"plan_file {task['plan_file']!r} ({expected})"
        ) from exc
    try:
        expected_digest = hashlib.sha256(expected.read_bytes()).hexdigest()
    except OSError as exc:
        raise DevCheckError(
            f"cannot read the resolved task {task['task_id']!r}'s configured plan file {expected} "
            f"(task plan_file={task['plan_file']!r}): {exc}; cannot verify whether the run's recorded plan "
            f"{recorded} (run.json plan.path={recorded_raw!r}) matches it"
        ) from exc
    if recorded_digest != expected_digest:
        raise DevCheckError(
            f"the run's recorded plan file {recorded} (run.json plan.path={recorded_raw!r}, sha256 "
            f"{recorded_digest}) differs in content from the resolved task {task['task_id']!r}'s "
            f"configured plan_file {task['plan_file']!r} ({expected}, sha256 {expected_digest}); refusing "
            "to grade scope discipline against a plan the selected task did not configure for this "
            "repository"
        )


def resolve_pm_attempts_counter(events: list[dict[str, Any]], slice_id: str, attempt: int) -> int:
    """PM's own `attempts` counter as it read while `attempt` was open.

    `attempt` is the monotonic event-derived ordinal (see resolve_attempt).
    The result is recorded on the attempt entry as `pm_attempts_counter`, for
    a human cross-referencing PM's own output, but never keys the sheet: PM's
    counter resets to 0 whenever a stopped slice is restarted
    (`pm_lib.slice_ops.start_slice`).

    Derived from the event log via `bench_lib.epoch_start_ordinals`, never
    from run.json: run.json holds only PM's counter *now*, which is wrong for
    any earlier attempt. PM's counter resets and increments on exactly the
    launch-family events this repo parses, so `attempt -
    epoch_start_ordinals(...)[attempt]` reproduces it for any attempt.
    `upsert_attempt` preserves an already-graded attempt's recorded value on
    a regrade.

    Raises:
        DevCheckError: no launch/relaunch/steer event opens `attempt`.
    """
    starts = bench_lib.epoch_start_ordinals(events, slice_id)
    if attempt < 0 or attempt >= len(starts):
        raise DevCheckError(
            f"could not resolve PM's attempts counter for {slice_id!r} attempt {attempt}: no matching "
            "launch/relaunch/steer event found in events.jsonl"
        )
    return attempt - starts[attempt]


def resolve_attempt(events: list[dict[str, Any]], slice_id: str, requested_attempt: int | None) -> int:
    """The sheet's key: the monotonic event-derived attempt ordinal
    (bench_lib.attempt_ordinal), never PM's own `attempts` counter (see
    resolve_pm_attempts_counter for why that counter cannot be the key).

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

    A slice's `before_head` is HEAD at the moment `start_slice` ran, and is
    unchanged across every relaunch/steer within one uninterrupted epoch
    (`pm_lib/slice_ops.py`'s `start_slice`). A `finalize --stop` followed by
    a later `start-slice` on the same unaccepted slice opens a new epoch
    with a new `before_head`. Resolution order, most authoritative first:

    1. `explicit_before_head` (`--before-head`), the escape hatch for the one
       case nothing below recovers: a first slice that is no longer current,
       was never graded, and was never reviewed.
    2. `current_slice.before_head`, when this slice is still live.
    3. This attempt's own `provenance.base_commit` from an earlier grade.
    4. Structural, from run.json alone. Mode B runs slices strictly in plan
       order and only advances past an `accepted` or `attested` slice
       (`pm_lib.plan.next_slice`); `run_state["slices"]` is in plan order
       from `init` onward, so list-index arithmetic on it is safe.
       (a) For a later slice, the preceding slice's recorded `commit` is this
           slice's before_head. An `attested` predecessor (operator
           pre-approval, never launched, so no commit) or one with no
           recorded commit falls through to (b).
       (b) For any slice, the most recent review's recorded
           `before_head` (`entry["reviews"][*]`, written by
           `pm_lib/review.py`). The most recent, not the first: an earlier
           epoch's review carries a stale value. For this bench's plan every
           slice is elevated-risk, so `finalize_accept` requires a fresh
           review against the accepted head (`_fresh_reviews_for_head`) --
           the latest review of an accepted slice is therefore from its
           accepted epoch. List position alone is not a guarantee, because
           concurrently commissioned reviews can be appended out of order;
           for an accepted slice, reviews are first filtered to those whose
           `head` equals `entry["commit"]`, which is exact. For any other
           slice (graded manually with an explicit `--commit`), list-position
           recency is the best available signal.

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
        # List position alone could pick a slow, earlier-epoch review appended
        # after a current-epoch one; matching `head` to the accepted commit
        # cannot (see the docstring's step 4(b)).
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


# Default obligations location under the bench root, used only when
# load_obligations is called without a path. main() and model_report.py
# always pass the resolved task's own `obligations_file`; the tests use this
# default to load the bench's own obligations map.
OBLIGATIONS_RELATIVE_PATH = Path("hidden_tests") / "obligations.yaml"


def load_obligations(root: Path, relative_path: Path | None = None) -> dict[str, Any]:
    """Load and shape-check one obligations file under `root`.

    Args:
        root: the directory the file lives under (the bench root).
        relative_path: the file's path relative to `root`; defaults to
            OBLIGATIONS_RELATIVE_PATH. main() and model_report.py pass the
            resolved task's own `obligations_file`, so one task's rubric is
            never graded against another's.

    Raises:
        DevCheckError: the file is missing, or does not parse to the
            expected top-level `slices` mapping.
    """
    path = root / (relative_path or OBLIGATIONS_RELATIVE_PATH)
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
    # load_obligations guarantees only that top-level `slices` is a mapping;
    # a hand-edited file can still carry a non-mapping slice entry or a
    # non-list `obligations` value there, which would otherwise escape as a
    # raw AttributeError/TypeError further down this same parsing path.
    if not isinstance(slice_map, dict):
        raise DevCheckError(
            f"obligations.yaml's entry for slice {slice_number} is {type(slice_map).__name__}, not a mapping"
        )
    groups = slice_map.get("obligations", [])
    if not isinstance(groups, list):
        raise DevCheckError(
            f"obligations.yaml's slice {slice_number} 'obligations' field is {type(groups).__name__}, not a list"
        )
    return groups


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


def _derive_hidden_test_filename(node: Any, group_id: Any, obligations_path: Path) -> str:
    """One obligations node id -> the bare `<file>.py` under tests/ it names.

    Node ids are worktree-relative pytest ids (see obligations.yaml's header
    comment): `tests/<filename>.py::<test name>`, where the test-name part may
    itself contain further `::` (class methods) and a @pytest.mark.parametrize
    `[param]` suffix -- including spaces inside the brackets. Only the file
    part locates a hidden test file on disk, so it is derived by validating
    the `tests/` prefix and splitting at the FIRST `::`; the remainder is
    checked only to be non-empty, never against an exact shape, so a legal
    future pytest id convention is never spuriously rejected.

    Raises:
        DevCheckError: naming the obligations file, the offending group id,
            and the offending value whenever the node is not a string or does
            not carry a valid `tests/<file>.py::` prefix.
    """
    if not isinstance(node, str):
        raise DevCheckError(
            f"{obligations_path}: obligation group {group_id!r} lists a non-string node id {node!r}; "
            "cannot derive this slice's hidden test filenames from it"
        )
    if not node.startswith("tests/") or "::" not in node[len("tests/"):]:
        raise DevCheckError(
            f"{obligations_path}: obligation group {group_id!r} lists node id {node!r}, which is not shaped "
            "like a worktree-relative 'tests/<file>.py::<test>' node id; cannot derive this slice's "
            "hidden test filenames from it"
        )
    file_part, _, test_name = node.partition("::")
    filename = file_part[len("tests/"):]
    if not filename or "/" in filename or not filename.endswith(".py"):
        raise DevCheckError(
            f"{obligations_path}: obligation group {group_id!r} lists node id {node!r}, whose file part "
            f"'{filename}' is not a bare '<file>.py' directly under tests/; cannot derive this slice's "
            "hidden test filenames from it"
        )
    if not test_name:
        raise DevCheckError(
            f"{obligations_path}: obligation group {group_id!r} lists node id {node!r} with no test name "
            "after '::'; cannot derive this slice's hidden test filenames from it"
        )
    return filename


def hidden_test_filenames(groups: list[Any], obligations_path: Path) -> set[str]:
    """The distinct hidden-test filenames one slice's obligation groups reference.

    The obligations file is the single source for which test files a slice
    runs: every group's `tests:` entries are worktree-relative node ids
    shaped like `tests/test_hA.py::test_name`, so the file set is derived
    from them rather than configured separately. Nothing about the number of
    files is assumed.

    Every structural assumption is validated before use: each group must be a
    mapping with a string `id`, its `tests` field a list, and each entry a
    well-shaped node id.

    Args:
        groups: one slice's obligation groups (from obligation_groups_for_slice).
        obligations_path: the obligations file these groups came from, named
            in every error this function raises.

    Raises:
        DevCheckError: a group is not a mapping or has no usable `id`, a
            `tests` field is not a list, a listed node id is malformed
            (naming the offender and its group), or the slice references no
            hidden test files at all.
    """
    filenames: set[str] = set()
    for index, group in enumerate(groups):
        if not isinstance(group, dict):
            raise DevCheckError(
                f"{obligations_path}: obligation group #{index} is {type(group).__name__}, not a mapping; "
                "cannot derive this slice's hidden test filenames from it"
            )
        group_id = group.get("id")
        # Checked here because node_to_group_map/score_correctness index
        # group["id"] directly and would otherwise fail with a raw KeyError.
        if not isinstance(group_id, str) or not group_id:
            raise DevCheckError(
                f"{obligations_path}: obligation group #{index} has no usable string 'id' field "
                f"(got {group_id!r}); cannot derive this slice's hidden test filenames from it"
            )
        tests = group.get("tests")
        if not isinstance(tests, list):
            raise DevCheckError(
                f"{obligations_path}: obligation group {group_id!r}'s 'tests' field is "
                f"{type(tests).__name__}, not a list of node ids; cannot derive this slice's hidden "
                "test filenames from it"
            )
        for node in tests:
            filenames.add(_derive_hidden_test_filename(node, group_id, obligations_path))
    if not filenames:
        raise DevCheckError(
            f"{obligations_path}: no obligation group references any hidden test file; refusing to grade "
            "a slice with an empty hidden-test set rather than score it vacuously"
        )
    return filenames


def validate_obligations_against_task(
    obligations: dict[str, Any], task: dict[str, Any], root: Path, obligations_path: Path
) -> None:
    """The resolved task's own configuration must agree with its obligations file.

    obligations.yaml carries top-level `plan:`/`plan_pin:` fields that pin the
    same facts the task entry records independently -- the frozen plan's
    repo-relative path and the exact commit it was vendored from (parsed from
    the task's provenance file by bench_lib.parse_pinned_plan_commit). A
    disagreement means one source drifted, and grading under either would be
    wrong. This validates a task's internal consistency only; whether the run
    being graded belongs to this task is check_run_belongs_to_task's job.

    Raises:
        DevCheckError: naming both the expected and the found value whenever
            either field disagrees (a missing field counts as disagreeing --
            never guessed), or the provenance file itself yields no pinned
            commit.
    """
    expected_plan = task["plan_file"]
    found_plan = obligations.get("plan")
    if found_plan != expected_plan:
        raise DevCheckError(
            f"{obligations_path}'s plan={found_plan!r} does not match task {task['task_id']!r}'s configured "
            f"plan_file={expected_plan!r}; refusing to grade against a rubric whose pinned plan disagrees "
            "with the task's own configuration"
        )
    provenance_path = root / task["provenance_file"]
    try:
        pinned_commit = bench_lib.parse_pinned_plan_commit(provenance_path)
    except bench_lib.BenchLibError as exc:
        raise DevCheckError(str(exc)) from exc
    found_pin = obligations.get("plan_pin")
    if found_pin != pinned_commit:
        raise DevCheckError(
            f"{obligations_path}'s plan_pin={found_pin!r} does not match the pinned commit {pinned_commit!r} "
            f"parsed from {provenance_path}; refusing to grade against a rubric pinned to a different "
            "commit than the task's provenance file records"
        )


# --- correctness -----------------------------------------------------------


def _manifest_hash(paths: list[Path]) -> str:
    """Sha256 of a canonical manifest of `paths`: sorted
    `<filename>:<sha256-of-bytes>` entries joined by newlines, hashed again.
    Hashing the manifest rather than concatenating raw bytes means a rename
    or a content shift between two files can never produce the same digest
    as leaving them all alone; sorting makes it independent of input order."""
    entries = sorted(f"{path.name}:{hashlib.sha256(path.read_bytes()).hexdigest()}" for path in paths)
    return hashlib.sha256("\n".join(entries).encode("utf-8")).hexdigest()


def hidden_tests_manifest_hash(root: Path, task: dict[str, Any], slice_number: int, filenames: set[str]) -> str:
    """Sha256 of a canonical manifest of this slice's hidden test files.

    Covers exactly the files `run_hidden_tests` copies into the grading
    worktree -- same derived `filenames`, same source directory (the resolved
    task's `hidden_tests_dir`) -- so this can never drift from what actually
    gets executed. The digest is `_manifest_hash` over those files.

    Raises:
        DevCheckError: an expected hidden test file is missing -- never a
            hash computed over whatever happened to be present.
    """
    source_dir = root / task["hidden_tests_dir"] / f"slice{slice_number}"
    paths = [source_dir / filename for filename in sorted(filenames)]
    for file_path in paths:
        if not file_path.is_file():
            raise DevCheckError(f"hidden test file not found: {file_path}")
    return _manifest_hash(paths)


def run_hidden_tests(
    worktree: Path, slice_number: int, root: Path, policy: dict[str, Any], task: dict[str, Any], filenames: set[str]
) -> dict[str, str]:
    """Copy this slice's hidden tests into the worktree and run pytest once.

    The copied files and the pytest targets are both exactly `filenames`
    (from hidden_test_filenames), read from the resolved task's own
    `hidden_tests_dir`, so each task is graded against precisely its own
    suite.

    Never points pytest at two slices' directories in the same invocation --
    sibling slices may share filenames and collection would fail (see
    README.md/AGENTS.md's note on the hidden tests).

    Returns:
        Mapping of worktree-relative node id (e.g. "tests/test_hA.py::test_A01_...")
        to one of "passed", "failed", "error", "skipped".

    Raises:
        DevCheckError: pytest crashed, produced no junit XML, or reported a
            collection/setup error -- all loud failures, never a zero score.
    """
    source_dir = root / task["hidden_tests_dir"] / f"slice{slice_number}"
    for filename in sorted(filenames):
        if not (source_dir / filename).is_file():
            raise DevCheckError(f"hidden test file not found: {source_dir / filename}")

    tests_dir = worktree / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    for filename in sorted(filenames):
        shutil.copy2(source_dir / filename, tests_dir / filename)

    junit_fd, junit_name = tempfile.mkstemp(prefix="dev-check-junit-", suffix=".xml")
    os.close(junit_fd)
    junit_path = Path(junit_name)
    try:
        cmd = [
            policy["python_interpreter"],
            "-m",
            "pytest",
            *[f"tests/{filename}" for filename in sorted(filenames)],
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

    Returns a dict with the pass/total counts, `by_obligation` (the
    group-level {passed, total, fraction} the rubric weight is computed
    from), and `by_node`, the full node_id -> outcome map those counts were
    derived from. `by_node` is per-test evidence, so rubric questions (which
    test drove a difference, is a group saturated, what a different
    partition would score) are answerable from the scoring sheet without
    re-grading. Only the first attempt's outcomes are carried further, by
    model_report.py's `first_attempt_node_outcomes`.

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
        # Sorted so regenerated sheets diff cleanly across regrades.
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
    payload for this specific tool. lint.py and health.py use different
    exit-code vocabularies (see run_lint/run_code_health), so there is no
    shared "nonzero means unavailable" rule: lint.py's exit 1 means new
    findings, not a failure.

    Never reinterprets the payload or derives a score from it; an
    unavailable or failing tool is recorded as an explicit marker, never as
    a clean pass.
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

    `--require-coverage` makes lint.py exit 3 ("coverage-gap", scoreable per
    `_LINT_SCOREABLE_EXIT_CODES`) when a changed language in scope has no
    available linter; without it, a missing linter would read as a clean
    pass.
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
    lint.py's absolute per-tool counts, `candidates` is already differential
    in `--base` mode (health.py drops zero-delta rows itself).

    `--require-coverage` makes health.py exit 3 ("coverage-gap", scoreable
    per `_HEALTH_SCOREABLE_EXIT_CODES`) when a required language in scope
    has unavailable metric coverage, rather than silently reporting a
    partial measurement.

    `result["verdict"]` is `"measured"` on exit 0, deliberately not
    `"pass"`: health.py emits no quality verdict of its own
    (`candidate_selection.verdict` is literally `"none"`), so exit 0 means
    only that the tool ran and produced a payload, however many candidates
    it lists. The value is displayed as a hygiene/coverage badge
    (leaderboard.py's `_quality_summary`), never scored.
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


# --- test kill rate (mutation gate) -------------------------------------------
#
# How much the candidate's OWN test suite would notice a seeded defect. Each
# task's bank (policy.yaml tasks:<id>:mutations_dir) is a sitecustomize.py
# hook module that, when its directory is first on PYTHONPATH and
# MUTATION=<id> is set, monkey-patches one plan-named public function after
# import (so a candidate's internal naming and import style cannot dodge it),
# plus one slice<N>.txt per plan slice naming the mutants that slice owns.

_MUTATION_HOOK_FILENAME = "sitecustomize.py"

# Run in a fresh interpreter in the candidate's worktree, with the bank first
# on PYTHONPATH and MUTATION unset -- the mutant runs' exact startup: reports
# which sitecustomize was auto-imported and that module's registry. It imports
# only the builtin `sys` module and prints a literal, so no tracked file in
# the worktree can shadow anything it uses.
_BANK_PROBE_SOURCE = (
    "import sys\n"
    "module = sys.modules.get('sitecustomize')\n"
    "registry = getattr(module, 'all_mutation_ids', None)\n"
    "print(repr({'file': getattr(module, '__file__', None),\n"
    "            'ids': [str(i) for i in registry()] if callable(registry) else None}))\n"
)

_OUTPUT_TAIL_CHARS = 2000


def parse_mutation_list(path: Path) -> list[str]:
    """The mutant ids one `slice<N>.txt` lists, in file order.

    One id per line; everything from a `#` to the end of its line is a
    comment, and blank lines are ignored.

    Raises:
        DevCheckError: a line carries more than one token, an id is listed
            twice, or the file lists no id at all -- each naming the file
            (and the line or id). An empty list would make every kill rate
            0/0; a duplicate would count one mutant twice.
    """
    ids: list[str] = []
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        tokens = raw.split("#", 1)[0].split()
        if not tokens:
            continue
        if len(tokens) > 1:
            raise DevCheckError(f"{path}:{line_number}: expected one mutant id per line, got {raw.strip()!r}")
        ids.append(tokens[0])
    if not ids:
        raise DevCheckError(f"mutant list {path} names no mutant; refusing to measure a kill rate over nothing")
    duplicates = sorted(mutant for mutant, count in Counter(ids).items() if count > 1)
    if duplicates:
        raise DevCheckError(f"mutant list {path} lists the same mutant id more than once: {duplicates}")
    return ids


def _mutation_env(bank_dir: Path, mutation: str | None) -> dict[str, str]:
    """A copy of this process's environment with the bank first on PYTHONPATH
    and MUTATION set to `mutation`, or removed when it is None. The grader's
    own os.environ is never modified."""
    env = dict(os.environ)
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(bank_dir) + (os.pathsep + existing if existing else "")
    if mutation is None:
        env.pop("MUTATION", None)
    else:
        env["MUTATION"] = mutation
    return env


def load_mutation_bank(root: Path, task: dict[str, Any], slice_number: int) -> dict[str, Any]:
    """Resolve and check the task's mutation bank files for one slice.

    The interpreter-level checks (that the bank's own sitecustomize is the
    one auto-imported, and that every listed id is registered) need the
    candidate's worktree, so `measure_test_kill_rate` makes them.

    Returns:
        `{"dir": <absolute bank dir>, "hook": <sitecustomize.py>, "list":
        <slice<N>.txt>, "ids": [...listed ids...], "bank_hash":
        _manifest_hash([hook, list])}` -- the hash is per slice, because each
        slice reads its own list.

    Raises:
        DevCheckError: sitecustomize.py or `slice<N>.txt` is missing, or the
            list is malformed (see parse_mutation_list), naming the path.
    """
    bank_dir = (root / task["mutations_dir"]).resolve()
    hook_path = bank_dir / _MUTATION_HOOK_FILENAME
    list_path = bank_dir / f"slice{slice_number}.txt"
    if not hook_path.is_file():
        raise DevCheckError(f"task {task['task_id']!r}'s mutation hook module not found: {hook_path}")
    if not list_path.is_file():
        raise DevCheckError(f"task {task['task_id']!r} has no mutant list for slice {slice_number}: {list_path}")
    ids = parse_mutation_list(list_path)
    return {
        "dir": bank_dir,
        "hook": hook_path,
        "list": list_path,
        "ids": ids,
        "bank_hash": _manifest_hash([hook_path, list_path]),
    }


def _probe_bank(worktree: Path, bank: dict[str, Any], policy: dict[str, Any]) -> str | None:
    """Run _BANK_PROBE_SOURCE under the mutant runs' own startup (cwd the
    worktree, bank first on PYTHONPATH, MUTATION unset). Returns None when
    the bank's sitecustomize is the one auto-imported, else the reason it is
    not -- another sitecustomize ahead of it would leave every mutant
    unapplied and read as "survived".

    Raises:
        DevCheckError: the probe interpreter cannot run or reports nothing
            usable, the hook defines no registry, or the slice list names an
            id the hook does not register (an unknown id is a silent no-op)
            -- each a fault in the bench or its environment, not the
            candidate's.
    """
    python = policy["python_interpreter"]
    try:
        probe = subprocess.run(
            [python, "-c", _BANK_PROBE_SOURCE],
            cwd=worktree,
            env=_mutation_env(bank["dir"], None),
            capture_output=True,
            text=True,
            timeout=policy["subprocess_timeout_seconds"],
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DevCheckError(f"could not probe mutation bank {bank['dir']} with {python}: {exc}") from exc
    try:
        report = ast.literal_eval(probe.stdout.strip()) if probe.returncode == 0 else None
    except (ValueError, SyntaxError):
        report = None
    if not isinstance(report, dict):
        raise DevCheckError(
            f"probing mutation bank {bank['dir']} with {python} failed (exit {probe.returncode}); output "
            f"tail:\n{_output_tail(probe.stdout, probe.stderr)}"
        )
    loaded = report.get("file")
    if not loaded or Path(loaded).resolve() != bank["hook"]:
        return (
            f"{python} auto-imported sitecustomize from {loaded!r}, not the bank's own {bank['hook']}, when "
            "started in this worktree; no mutant would ever be applied"
        )
    registered = report.get("ids")
    if not isinstance(registered, list):
        raise DevCheckError(f"{bank['hook']} defines no callable all_mutation_ids() registry")
    unregistered = [mutant for mutant in bank["ids"] if mutant not in set(registered)]
    if unregistered:
        raise DevCheckError(f"{bank['list']} lists mutant id(s) {bank['hook']} does not register: {unregistered}")
    return None


def own_test_files(worktree: Path, measurement: dict[str, Any]) -> list[str]:
    """Every path tracked at the graded commit that the task's measurement
    globs classify as `test`, sorted -- the candidate's own suite as the
    commit records it, never anything the grader copied in afterwards."""
    tracked = run_git(worktree, "ls-files", "-z").split("\0")
    return sorted(path for path in tracked if path and classify_path(path, measurement) == "test")


def _junit_node_id(classname: str, name: str, files: list[str]) -> str | None:
    """Rebuild one junit testcase's pytest node id from its dotted classname.

    pytest writes `classname` as the node id's file part with `/` turned into
    `.` and `.py` dropped, followed by any enclosing class names, so the file
    is the one whose dotted form the classname equals or extends. Returns
    None when no file, or more than one, matches.
    """
    dotted_by_path = {path: path[:-3].replace("/", ".") for path in files if path.endswith(".py")}
    matches = [
        path for path, dotted in dotted_by_path.items() if classname == dotted or classname.startswith(dotted + ".")
    ]
    if len(matches) != 1:
        return None
    path = matches[0]
    dotted = dotted_by_path[path]
    classes = classname[len(dotted) + 1 :].split(".") if classname != dotted else []
    return "::".join([path, *classes, name])


def _parse_own_suite_junit(junit_path: Path, files: list[str]) -> tuple[list[str], int, list[str]]:
    """The candidate suite's baseline outcome, read leniently.

    A collection error, failure, error or skip is simply "did not pass" --
    never a grading failure, because the candidate's own suite is the thing
    being measured. A node reported more than once (e.g. a teardown error
    on a passing test) passed only if every report passed.

    Returns:
        (sorted passed node ids, count of distinct testcases that did not
        pass, passed testcases whose node id could not be rebuilt).
    """
    passed_by_case: dict[tuple[str, str], bool] = {}
    for testcase in ET.parse(junit_path).getroot().iter("testcase"):
        key = (testcase.get("classname") or "", testcase.get("name") or "")
        passed = all(testcase.find(tag) is None for tag in ("failure", "error", "skipped"))
        passed_by_case[key] = passed_by_case.get(key, True) and passed
    passed_nodes: list[str] = []
    unmappable: list[str] = []
    for (classname, name), passed in passed_by_case.items():
        if not passed:
            continue
        node = _junit_node_id(classname, name, files)
        if node is None:
            unmappable.append(f"{classname}::{name}")
        else:
            passed_nodes.append(node)
    not_passed = sum(1 for passed in passed_by_case.values() if not passed)
    return sorted(passed_nodes), not_passed, sorted(unmappable)


def _output_tail(stdout: Any, stderr: Any) -> str:
    """The last _OUTPUT_TAIL_CHARS of a subprocess's combined output.
    TimeoutExpired can carry bytes even under text=True, so both are
    decoded."""
    parts = [part.decode("utf-8", "replace") if isinstance(part, bytes) else (part or "") for part in (stdout, stderr)]
    return "".join(parts)[-_OUTPUT_TAIL_CHARS:]


def _run_selection(cmd: list[str], worktree: Path, env: dict[str, str], timeout: float) -> tuple[str, str | None]:
    """One run of the baseline-passing selection (the control, or one
    mutant): ("survived" | "killed" | "errored", error detail).

    Every selected node passed at baseline, so exit 1 (some test failed) is
    a flip and therefore a kill; any other exit, or a timeout, is errored --
    never a kill."""
    try:
        result = subprocess.run(cmd, cwd=worktree, env=env, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        return "errored", f"timed out after {timeout}s; output tail:\n{_output_tail(exc.stdout, exc.stderr)}"
    if result.returncode == 0:
        return "survived", None
    if result.returncode == 1:
        return "killed", None
    return "errored", f"pytest exited {result.returncode}; output tail:\n{_output_tail(result.stdout, result.stderr)}"


def measure_test_kill_rate(
    worktree: Path, bank: dict[str, Any], policy: dict[str, Any], measurement: dict[str, Any]
) -> dict[str, Any]:
    """The attempt entry's `test_kill_rate` block: the fraction of this
    slice's listed mutants the candidate's OWN test suite kills.

    Runs in its own disposable worktree, never the one run_hidden_tests
    copies the bench's hidden tests into: the suite measured is exactly
    `own_test_files`, and whatever a mutant run leaves behind (`-x` skips
    cleanup, a timeout kills the process) never reaches the hidden tests.

    0. Probe (`_probe_bank`): the bank's sitecustomize must be the one a
       Python started in this worktree auto-imports.

    1. Baseline: the suite once, unmutated (`--continue-on-collection-errors`,
       junit read leniently), in this process's environment minus any
       `MUTATION` -- a value exported in the operator's shell, with a bank on
       their PYTHONPATH, would otherwise mutate the baseline itself. Its
       PASSED nodes are the only ones that can kill: a node already failing,
       erroring or skipped gives no signal.
    2. Control: exactly those nodes, selected by node id, with the bank on
       PYTHONPATH and MUTATION unset. It must pass -- this proves the
       selection reproduces the baseline and the hook is inert when no
       mutant is chosen, so under serial execution (`parallel_workers: 1`) a
       later failure can only be the mutant's doing; with concurrent runs,
       interference between them can also flip a test.
       Nodes are selected positionally rather than by `--deselect`ing the
       rest, because pytest's `--deselect` is a node-id PREFIX match and
       would silently drop a passing `test_x2` alongside a failing `test_x`.
    3. One run per listed mutant (`-x`, MUTATION=<id>), up to
       `mutation_gate.parallel_workers` at a time: exit 0 survived, exit 1
       killed, anything else or a timeout errored, with its output tail in
       `errors`. Outcomes are keyed by id, independent of completion order.

    `kill_rate` is killed over EVERY listed mutant: an errored mutant is
    never a kill and never shrinks the denominator. A baseline that passes
    nothing can kill nothing, so every mutant is recorded survived (0.0)
    without running any, with a `note` saying so.

    Returns:
        `{"available": False, "reason": ...}` when the suite cannot be
        measured (no test files under the task's test globs, another
        sitecustomize shadowing the bank's, a baseline or
        control that times out, a baseline exit outside pytest's 0/1, a
        passed node whose id cannot be rebuilt, or a control that does not
        pass); otherwise `{"available": True, "bank_hash", "own_suite":
        {"files", "passed", "not_passed"}, "mutations": {id: outcome},
        "killed", "survived", "errored", "total", "kill_rate", "errors"}`.
    """
    files = own_test_files(worktree, measurement)
    if not files:
        return {
            "available": False,
            "reason": f"no tracked file matches the task's test globs {measurement['test_paths']}",
        }

    shadowed = _probe_bank(worktree, bank, policy)
    if shadowed:
        return {"available": False, "reason": shadowed}

    python = policy["python_interpreter"]
    timeout = policy["subprocess_timeout_seconds"]
    baseline_env = {key: value for key, value in os.environ.items() if key != "MUTATION"}
    # Pinned, and resolved, because node ids are relative to pytest's rootdir:
    # with no pytest config in the repo it would otherwise be the test files'
    # common ancestor, and a symlinked path would put them outside it.
    rootdir = f"--rootdir={worktree.resolve()}"
    junit_fd, junit_name = tempfile.mkstemp(prefix="dev-check-own-suite-", suffix=".xml")
    os.close(junit_fd)
    junit_path = Path(junit_name)
    try:
        baseline_cmd = [
            python, "-m", "pytest", *files, "-q", "-p", "no:cacheprovider", "--continue-on-collection-errors",
            rootdir, f"--junitxml={junit_path}",
        ]
        try:
            baseline = subprocess.run(
                baseline_cmd, cwd=worktree, env=baseline_env, capture_output=True, text=True, timeout=timeout
            )
        except subprocess.TimeoutExpired:
            return {"available": False, "reason": f"own-suite baseline timed out after {timeout}s"}
        if baseline.returncode not in _PYTEST_SCOREABLE_EXIT_CODES or junit_path.stat().st_size == 0:
            return {
                "available": False,
                "reason": f"own-suite baseline exited {baseline.returncode}; output tail:\n"
                f"{_output_tail(baseline.stdout, baseline.stderr)}",
            }
        passed_nodes, not_passed, unmappable = _parse_own_suite_junit(junit_path, files)
    finally:
        junit_path.unlink(missing_ok=True)
    if unmappable:
        return {
            "available": False,
            "reason": f"passed baseline test(s) whose node id could not be rebuilt from junit: {unmappable}",
        }

    ids = bank["ids"]
    record: dict[str, Any] = {
        "available": True,
        "bank_hash": bank["bank_hash"],
        "own_suite": {"files": files, "passed": len(passed_nodes), "not_passed": not_passed},
    }
    if not passed_nodes:
        outcomes = {mutant: "survived" for mutant in ids}
        record["note"] = "the own suite passed no test at baseline, so it can kill nothing; no mutant was run"
        errors: dict[str, str] = {}
    else:
        selected_cmd = [python, "-m", "pytest", *passed_nodes, "-q", "-x", "-p", "no:cacheprovider", rootdir]
        control, control_error = _run_selection(selected_cmd, worktree, _mutation_env(bank["dir"], None), timeout)
        if control != "survived":
            return {
                "available": False,
                "reason": "the baseline-passing tests did not all pass when re-run by node id with the bank on "
                f"PYTHONPATH and MUTATION unset ({control_error or 'a test failed'}); an order-dependent or flaky "
                "suite cannot be measured",
            }
        with ThreadPoolExecutor(max_workers=policy["mutation_gate"]["parallel_workers"]) as pool:
            futures = {
                mutant: pool.submit(_run_selection, selected_cmd, worktree, _mutation_env(bank["dir"], mutant), timeout)
                for mutant in ids
            }
            results = {mutant: future.result() for mutant, future in futures.items()}
        outcomes = {mutant: results[mutant][0] for mutant in ids}
        errors = {mutant: results[mutant][1] for mutant in ids if results[mutant][0] == "errored"}

    counts = Counter(outcomes.values())
    record.update(
        {
            "mutations": outcomes,
            "killed": counts["killed"],
            "survived": counts["survived"],
            "errored": counts["errored"],
            "total": len(ids),
            "kill_rate": counts["killed"] / len(ids),
            "errors": errors,
        }
    )
    return record


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
# function cyclomatic complexity), both measured against this slice's own
# before_head, never the preceding attempt -- a trajectory against a moving
# base would hide a regression introduced early and never touched again.


@lru_cache(maxsize=None)
def _compile_glob(pattern: str) -> re.Pattern[str]:
    """Compile one policy.yaml measurement glob into an anchored regex, with
    "**" given the standard zero-or-more-directories meaning.

    Neither `pathlib.PurePath.match` nor stdlib `fnmatch.translate` on the
    Python versions this repo runs under treat "**" this way: both require
    at least one intervening path separator, so `"src/**/*.py"` would not
    match `"src/merger_rate.py"` -- exactly how relative-velocity's
    production code is laid out (see TestClassifyPath in
    tests/test_dev_check.py) -- and every real production file would be
    silently sorted into "unclassified".

    Deliberately narrow: it understands only "**" (zero or more full path
    segments), "*" (any run of characters within one segment) and "?" (one
    character within one segment) -- the only wildcards policy.yaml's
    measurement globs use. Cached per distinct pattern string.
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
    "unclassified" (a path matching none of the task's measurement globs),
    checked in that fixed order.

    An unclassified path is its own named bucket, counted and reported,
    never folded into production or discarded.
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
    `None`, never coerced to 0. Callers must run `git diff` with
    `--no-renames` (see compute_loc_delta): with it, git never
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


def label_source_lines(source: str) -> dict[int, str]:
    """Label every physical line of one Python source (1-based line number
    -> category) as exactly one of code/docstring/comment/blank; the
    mapping has one entry per physical line.

    `classify_source_lines` is this mapping summed per category, and
    `measure_hygiene` reads it for just the lines an attempt added, so the
    two measurements can never disagree about what a line is.

    Precedence (fixed):
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

    return {line: labels.get(line, "blank") for line in range(1, physical_line_count + 1)}


def classify_source_lines(source: str) -> dict[str, int]:
    """Classify every physical line of one Python source into exactly one of
    code/docstring/comment/blank; the four counts always sum to the
    source's own physical line count. The per-category sum of
    `label_source_lines`, whose docstring states the precedence.

    Raises:
        LineClassificationError: as `label_source_lines`.
    """
    counts = {category: 0 for category in _LOC_CATEGORIES}
    for category in label_source_lines(source).values():
        counts[category] += 1
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

    Deliberately `--all`, not `--base`: `run_code_health`'s differential
    invocation narrows to changed files and cannot supply a complete
    baseline total, so this absolute run is needed at both ends. Reusing
    health.py keeps a single complexity implementation.

    `--require-coverage` is not passed (unlike run_code_health): that flag
    is the only thing that makes health.py exit 3, so without it health.py
    exits 0 or 2 (genuine failure). A coverage gap here (lizard unavailable
    for non-Python files) is recorded as the complexity block's
    `coverage_note` (via facts.lizard.error, see _extract_functions) rather
    than a hard failure that would prevent scoring the rest of the attempt.
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
    and silent about functions that were removed entirely, so counting it
    would turn a display cap into a scoring ceiling).

    Returns:
        (functions, coverage_note). `coverage_note` is a named string
        exactly when `facts.lizard.error` is set -- non-Python complexity
        coverage was unavailable for this revision (e.g. lizard not
        installed) -- so the gap is reported, never read as "zero
        non-Python functions".
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


# The baseline complexity measurement depends only on (repo, before_head),
# which is shared by every attempt in one epoch, so it is computed once per
# epoch rather than once per attempt. grade_run.py calls dev_check.main()
# in-process per attempt, so this module-level dict is shared across a whole
# grade_run.py invocation. Deliberately process-local, never a file on disk:
# a disk cache could go stale across a policy.yaml edit (a changed glob, a
# metric_version bump) with nothing to invalidate it.
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
            the path being genuinely absent at that revision (a bad repo,
            an I/O error, a corrupt object -- never folded into "file does
            not exist" and counted as zero lines). Names the revision, path,
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
    `loc_category_definition` (the only implementation: AST docstrings +
    tokenize, see `classify_source_lines`).

    Production only, deliberately: the decomposition exists to judge the
    economy of the implementation, not of tests or prose.

    Returns `{"available": False, "error": ...}` (never zeros) when any
    production file in this diff is binary, or when any production file
    fails to parse/tokenize at either revision it exists at -- a Developer
    attempt can legitimately commit syntactically broken code, so that must
    never abort the rest of grading.

    Reconciliation invariant: the four categories' nets must sum to
    `loc["buckets"]["production"]["net"]`, the number `compute_loc_delta`
    derived from `git diff --numstat`. A mismatch means an accounting bug in
    this function.

    Raises:
        DevCheckError: the reconciliation invariant does not hold, or a
            blob is missing at a revision where numstat says the file
            exists.
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

        # A missing blob is legitimate only when numstat shows the file was
        # purely added (missing at baseline) or purely deleted (missing at
        # endpoint) in this diff; any other missing blob is a named error,
        # never silently zeroed. `deleted == 0` alone establishes "absent at
        # baseline" (and `added == 0` "absent at endpoint"): there is no
        # positive-line-count requirement, because an empty added file has
        # added == deleted == 0 and is just as legitimately absent.
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
            `commit`, computed by the caller inside the attempt's own
            grading worktree before `run_hidden_tests` copies this slice's
            held-out tests in -- otherwise the bench's own hidden tests
            would be attributed to the Developer. This function never opens
            a worktree at `commit` itself; only the baseline (at
            `before_head`, via _baseline_complexity_payload) gets one here.
    """
    loc = compute_loc_delta(repo, before_head, commit, measurement)
    # Additive: never changes `loc["buckets"]` itself.
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


# --- hygiene census (descriptive, never scored) ------------------------------

# One `git diff -U0` hunk header: `@@ -a[,b] +c[,d] @@`. An omitted count
# means 1 (git's own convention); `d == 0` is a pure deletion hunk.
_HUNK_HEADER_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def added_line_numbers(diff_text: str) -> list[int]:
    """The new-file line numbers a `git diff -U0` patch adds, read from its
    hunk headers alone (`+c,d` covers lines c..c+d-1), in ascending order.

    With zero context lines every added line falls inside exactly one
    header's `+c,d` range, so the hunk bodies never need parsing.
    """
    numbers: list[int] = []
    for line in diff_text.splitlines():
        match = _HUNK_HEADER_RE.match(line)
        if match:
            start = int(match.group(1))
            count = 1 if match.group(2) is None else int(match.group(2))
            numbers.extend(range(start, start + count))
    return numbers


def measure_hygiene(
    repo: Path, before_head: str, commit: str, measurement: dict[str, Any], hygiene_policy: dict[str, Any]
) -> dict[str, Any]:
    """The `hygiene` attempt-entry block: a deterministic census of what this
    attempt added between this slice's own `before_head` and `commit` (the
    same baseline as `size_complexity`). Descriptive only, never scored.

    Production files only (`classify_path == "production"`): each one's
    ADDED lines (`added_line_numbers` over `git diff -U0 --no-renames`) are
    labelled at `commit` by `label_source_lines` -- the same precedence the
    size decomposition uses -- and counted per category. An added comment or
    docstring line is a narration line when at least one of
    `hygiene_policy["narration_tokens"]` matches it (case-insensitive
    `re.search`); `narration_by_token` counts, per pattern, the lines it
    matched, so one line can appear under several patterns but only once in
    `narration_lines`. A deleted file adds nothing. A binary file, a file
    that fails to parse at `commit` (LineClassificationError -- a Developer
    may commit broken code), or one whose hunk names a line beyond the file's
    own length is skipped and named in `skipped_files` with the reason,
    never counted as zero lines silently.

    Commit subjects come from `git log before_head..commit`: how many there
    are, how many exceed `commit_subject_max_length` characters, and how
    many match at least one of `commit_process_labels`.

    Both `git diff` calls pass `--no-color --no-ext-diff`, so a user's
    `color.ui=always` or `diff.external` cannot change what is parsed.

    Returns `{"available": False, "reason": ...}` when git itself fails or a
    production file numstat reports added lines for has no blob at `commit`
    (the reason names the file); everything else is `available: True`. No
    timestamps, so a regrade of the same commits produces the same block.
    """
    narration_patterns = {pattern: re.compile(pattern, re.IGNORECASE) for pattern in hygiene_policy["narration_tokens"]}
    label_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in hygiene_policy["commit_process_labels"]]
    max_length = hygiene_policy["commit_subject_max_length"]

    added = {category: 0 for category in _LOC_CATEGORIES}
    narration_lines = 0
    narration_by_token = {pattern: 0 for pattern in sorted(narration_patterns)}
    skipped_files: dict[str, str] = {}
    try:
        records = parse_numstat(
            run_git(repo, "diff", "--no-color", "--no-ext-diff", "--numstat", "--no-renames", before_head, commit)
        )
        for record in records:
            path = record["path"]
            if classify_path(path, measurement) != "production":
                continue
            if record["binary"]:
                skipped_files[path] = "binary file; added lines cannot be classified"
                continue
            if record["added"] == 0:
                continue
            source = _read_blob(repo, commit, path)
            if source is None:
                raise DevCheckError(
                    f"hygiene: {path!r} has {record['added']} added line(s) per numstat but no blob at {commit}"
                )
            try:
                labels = label_source_lines(source)
            except LineClassificationError as exc:
                skipped_files[path] = f"unparsable at {commit}: {exc}"
                continue
            numbers = added_line_numbers(
                run_git(repo, "diff", "--no-color", "--no-ext-diff", "-U0", "--no-renames", before_head, commit, "--", path)
            )
            beyond = [number for number in numbers if number not in labels]
            if beyond:
                skipped_files[path] = (
                    f"diff names added line {beyond[0]} but the file has {len(labels)} physical line(s) at {commit}"
                )
                continue
            source_lines = source.split("\n")
            for number in numbers:
                category = labels[number]
                added[category] += 1
                if category not in ("comment", "docstring"):
                    continue
                matched = [pattern for pattern, regex in narration_patterns.items() if regex.search(source_lines[number - 1])]
                if matched:
                    narration_lines += 1
                    for pattern in matched:
                        narration_by_token[pattern] += 1

        # `%H %s` keeps every row non-empty, so an empty subject is still
        # counted as a commit rather than vanishing in run_git's strip.
        log = run_git(repo, "log", "--format=%H %s", f"{before_head}..{commit}")
    except DevCheckError as exc:
        return {"available": False, "reason": str(exc)}

    subjects = [row.split(" ", 1)[1] if " " in row else "" for row in log.splitlines() if row]
    documentation = added["docstring"] + added["comment"]
    return {
        "available": True,
        "production": {
            "added_code": added["code"],
            "added_docstring": added["docstring"],
            "added_comment": added["comment"],
            "added_blank": added["blank"],
            "narration_lines": narration_lines,
            "narration_by_token": narration_by_token,
            "comment_to_code_ratio": documentation / added["code"] if added["code"] else None,
        },
        "commits": {
            "count": len(subjects),
            "subjects_over_max": sum(1 for subject in subjects if len(subject) > max_length),
            "subjects_with_process_label": sum(
                1 for subject in subjects if any(regex.search(subject) for regex in label_patterns)
            ),
            "subject_max_length": max_length,
        },
        "skipped_files": dict(sorted(skipped_files.items())),
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
    task: dict[str, Any],
    filenames: set[str],
    slice_number: int,
) -> dict[str, Any]:
    """task_id, plan_hash, policy_hash, obligations_hash, hidden_tests_hash,
    base_commit, pm_skill_version -- the scoring sheet's provenance block,
    recorded per attempt.

    `task_id` names which task's rubric this attempt was graded under; every
    hash below is only meaningful relative to that choice. An attempt whose
    provenance has no `task_id` (graded before it was recorded) is treated
    as belonging to policy.yaml's default_task, by check_regrade_task_identity
    here and by model_report.py.

    The block is per attempt, captured once at an attempt's first grade, and
    upsert_attempt() never rewrites it on a regrade: a later policy.yaml or
    obligations.yaml edit must never make an earlier attempt look graded
    under the new rules. `obligations_hash` covers the obligation partition,
    which is the rubric weight (docs/OBLIGATION-GROUPS.md);
    `hidden_tests_hash` (`hidden_tests_manifest_hash`) covers the hidden test
    bodies `run_hidden_tests` actually copies in, which are the rubric's
    content -- an edited assertion changes scores without changing the
    partition. Content hashes are used rather than a hand-maintained version
    key, which could be bumped for a comment-only edit or left stale across
    a material one. `pm_skill_version` is null (not a guess):
    project-manager carries no version marker anywhere.

    Because the block is never rewritten, a regrade in place leaves every
    already-graded attempt's provenance exactly as first recorded; a cohort
    regrade under changed rules archives `results/` via `cohort_run.py
    reset-leaderboard` and regrades into a clean tree.
    """
    return {
        "task_id": task["task_id"],
        "plan_hash": run_state.get("plan", {}).get("sha256"),
        "policy_hash": hashlib.sha256(policy_path.read_bytes()).hexdigest(),
        "obligations_hash": hashlib.sha256(obligations_path.read_bytes()).hexdigest(),
        "hidden_tests_hash": hidden_tests_manifest_hash(root, task, slice_number, filenames),
        "base_commit": before_head,
        "pm_skill_version": None,
    }


def check_regrade_task_identity(existing_sheet: dict[str, Any] | None, task_id: str, default_task_id: str) -> None:
    """Refuse a grade whose task differs from any attempt already on the sheet.

    One sheet must never mix results from two tasks' rubrics: its provenance
    would then name a task other than the one its numbers came from. Every
    existing attempt is checked, not just the row being replaced, because a
    new attempt has no row yet to compare. An attempt with no recorded
    `task_id` (graded before task_id was recorded) counts as graded under
    `default_task_id`; that inference holds only while `default_task` has not
    been changed since those attempts were graded. main() calls this before
    any worktree is created, so a doomed invocation fails fast.

    Args:
        existing_sheet: the loaded sheet at the target out path, or None.
        task_id: the resolved task this invocation grades under.
        default_task_id: policy["default_task"], standing in for a missing
            recorded task_id.

    Raises:
        DevCheckError: `attempts` is not a list, an entry is not a mapping, or
            an entry's `provenance` is present but not a mapping (naming the
            sheet or attempt and the offending value); or an existing
            attempt's task differs from `task_id` (naming the sheet, the
            attempt, both task ids and, for an attempt with no recorded
            task_id, the default).
    """
    if existing_sheet is None:
        return
    attempts = existing_sheet.get("attempts", [])
    if not isinstance(attempts, list):
        raise DevCheckError(
            f"existing scoring sheet (run_id={existing_sheet.get('run_id')!r} slice="
            f"{existing_sheet.get('slice')!r}) has an 'attempts' field that is not a list (got "
            f"{type(attempts).__name__}: {attempts!r}); refusing to guess task identities on a corrupted "
            "sheet"
        )
    for index, existing_attempt in enumerate(attempts):
        if not isinstance(existing_attempt, dict):
            raise DevCheckError(
                f"existing scoring sheet (run_id={existing_sheet.get('run_id')!r} slice="
                f"{existing_sheet.get('slice')!r}) has attempts[{index}] that is not a mapping (got "
                f"{type(existing_attempt).__name__}: {existing_attempt!r}); refusing to guess its task "
                "identity on a corrupted sheet"
            )
        old_provenance = existing_attempt.get("provenance")
        if old_provenance is not None and not isinstance(old_provenance, dict):
            raise DevCheckError(
                f"existing scoring sheet (run_id={existing_sheet.get('run_id')!r} slice="
                f"{existing_sheet.get('slice')!r}) has attempt {existing_attempt.get('attempt')!r} with a "
                f"'provenance' value that is not a mapping (got {old_provenance!r}); refusing to guess its "
                "task identity on a corrupted sheet"
            )
        old_task_id = old_provenance.get("task_id") if isinstance(old_provenance, dict) else None
        effective_old = old_task_id if old_task_id is not None else default_task_id
        if effective_old != task_id:
            legacy_note = (
                " (its provenance records no task_id, so it counts as the policy's default_task, "
                f"{default_task_id!r})"
                if old_task_id is None
                else ""
            )
            raise DevCheckError(
                f"existing scoring sheet (run_id={existing_sheet.get('run_id')!r} slice="
                f"{existing_sheet.get('slice')!r}) has attempt {existing_attempt.get('attempt')!r} already "
                f"graded under task {effective_old!r}{legacy_note}; refusing to grade this invocation under "
                f"task {task_id!r} rather than mix results from two tasks' rubrics into one sheet"
            )


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

    Every other attempt is preserved untouched, in place. On the attempt
    being replaced, four fields already recorded are carried over:

    - `reviews`, which review_score.py owns (one record per review
      commission, so a reviewer panel survives intact);
    - `quality_panel`, which quality_panel.py owns (one record per
      commission, so repeat commissions survive a regrade byte-identical);
    - `provenance`, captured at an attempt's first grade and never
      rewritten (see build_provenance);
    - `pm_attempts_counter`, the value first recorded for the attempt, so a
      regrade can never replace it with a differently derived one.

    A regrade under a different task than the attempt's recorded identity is
    refused by check_regrade_task_identity, which main() runs before any
    grading work, not here.

    `developer` is the structured identity block
    `bench_lib.resolve_developer_identity` returns, so an unattributed run
    is a named gap rather than a model literally named "None". It is
    sheet-level data, refreshed on every upsert like `run_status`, so a later
    `policy.yaml` identity correction is picked up on the next regrade.

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
            if "quality_panel" not in attempt_entry and "quality_panel" in existing_attempt:
                attempt_entry["quality_panel"] = existing_attempt["quality_panel"]
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
    parser.add_argument(
        "--slice", required=True, type=int,
        help="slice number N (PM's 'Slice N'); must have an entry in the resolved task's obligations file",
    )
    parser.add_argument(
        "--attempt", type=int, default=None,
        help="attempt to grade: 0 for the slice's first launch, +1 for each later launch/relaunch/steer in "
        "events.jsonl (default: the latest recorded for the slice)"
    )
    parser.add_argument(
        "--commit", default=None,
        help="commit to grade (default: current HEAD of the repository recorded in run.json)",
    )
    parser.add_argument(
        "--before-head", default=None,
        help="base commit to measure against; needed only when it cannot be recovered from run.json, an earlier "
        "grade in the scoring sheet, or a recorded review (e.g. a first slice that was never reviewed)"
    )
    parser.add_argument("--policy", type=Path, default=None, help="policy file (default: policy.yaml at this repo's root)")
    parser.add_argument(
        "--task", default=None,
        help="task id from the policy's tasks: registry to grade under (default: the policy's default_task)",
    )
    parser.add_argument(
        "--out", type=Path, default=None, help="scoring sheet to write (default: results/runs/<run_id>/slice-<N>.json)"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = bench_root()
    policy_path = (args.policy or (root / "policy.yaml")).expanduser().resolve()
    policy = load_policy(policy_path)

    try:
        task = bench_lib.resolve_task(policy, args.task)
    except bench_lib.BenchLibError as exc:
        raise DevCheckError(str(exc)) from exc

    run_dir = args.run_dir.expanduser().resolve()
    run_state = load_run_state(run_dir)
    events = read_events(run_dir)

    # BEFORE any grading work: the run being graded must actually belong to
    # the resolved task (see check_run_belongs_to_task). Also returns the
    # run's own recorded repository, reused below instead of re-resolving it.
    repo = check_run_belongs_to_task(run_state, task, root)
    # ...and the plan the RUN was initialized with must be the resolved task's
    # own configured plan (see check_plan_matches_task) -- scope discipline is
    # computed from that plan further down, independently of --task, so a
    # mismatch would blend one task's rubric with another task's authorization.
    check_plan_matches_task(run_state, task, repo)

    slice_id = f"Slice {args.slice}"
    entry = find_slice_entry(run_state, slice_id)
    # The sheet's key is the monotonic event-derived ordinal, not PM's own
    # `attempts` counter (which resets on a stopped-then-restarted slice) --
    # PM's counter is still resolved below, but only to record it on the
    # attempt entry, never to key the sheet.
    attempt = resolve_attempt(events, slice_id, args.attempt)
    pm_attempts_counter = resolve_pm_attempts_counter(events, slice_id, attempt)

    # The existing sheet is loaded before resolving before_head because an
    # earlier grade's provenance.base_commit is one of resolve_before_head's
    # fallbacks: once a slice is accepted, run.json's current_slice no longer
    # names it (finalize_accept clears it in the same write).
    out_path = (args.out or (root / "results" / "runs" / run_state["run_id"] / f"slice-{args.slice}.json")).expanduser().resolve()
    existing_sheet = load_existing_sheet(out_path, run_state["run_id"], args.slice)
    # Cross-task identity guard, BEFORE any grading work (see
    # check_regrade_task_identity): it validates the resolved task against
    # EVERY attempt already in the sheet, so a doomed invocation fails fast
    # instead of burning a full pipeline for output that would then be
    # discarded.
    check_regrade_task_identity(existing_sheet, task["task_id"], policy["default_task"])
    before_head = resolve_before_head(run_state, slice_id, existing_sheet, attempt, entry, args.before_head)

    commit = resolve_commit(repo, args.commit)

    pm_plan, pm_git_ops = import_pm_lib(policy)
    plan_path = Path(run_state["plan"]["path"]).expanduser().resolve()
    if not plan_path.is_file():
        raise DevCheckError(f"plan file recorded in run.json not found: {plan_path}")
    plan_slices = pm_plan.parse_plan(plan_path)
    plan_slice = pm_plan.plan_slice_by_id(plan_slices, slice_id)
    if plan_slice is None:
        raise DevCheckError(f"{slice_id!r} not found by parsing plan file {plan_path}")

    # The rubric comes from the resolved task: its obligations file names
    # this slice's hidden test files, and its plan:/plan_pin: fields are
    # checked against the task's configuration before anything is scored.
    obligations_path = root / task["obligations_file"]
    obligations = load_obligations(root, task["obligations_file"])
    groups = obligation_groups_for_slice(obligations, args.slice)
    validate_obligations_against_task(obligations, task, root, obligations_path)
    hidden_files = hidden_test_filenames(groups, obligations_path)
    mutation_bank = load_mutation_bank(root, task, args.slice)

    # The kill rate runs the candidate's own suite many times, under mutants
    # that can leave files behind, so it gets a disposable worktree of its
    # own: the hidden tests never enter it, and nothing it leaves reaches
    # the worktree they are run in.
    with grading_worktree(repo, commit, policy) as gate_worktree:
        test_kill_rate = measure_test_kill_rate(gate_worktree, mutation_bank, policy, task["measurement"])

    with grading_worktree(repo, commit, policy) as worktree:
        # All three quality measurements must run before run_hidden_tests
        # copies this slice's held-out tests into worktree/tests/: each one
        # inspects untracked files, so measuring after the copy would
        # attribute the bench's own hidden tests to the Developer.
        lint_result = run_lint(worktree, before_head, policy)
        health_result = run_code_health(worktree, before_head, policy)
        endpoint_complexity_payload = run_code_health_absolute(worktree, policy)
        outcomes = run_hidden_tests(worktree, args.slice, root, policy, task, hidden_files)
        correctness = score_correctness(outcomes, groups, args.slice)
        scope = compute_scope(pm_plan, pm_git_ops, repo, before_head, commit, plan_slice, run_state)

    # The layout globs are per task (they describe that task's target repo);
    # the methodology keys are global (policy.yaml's top-level measurement
    # block). Downstream functions take the merged view.
    measurement = {
        **task["measurement"],
        "loc_definition": policy["measurement"]["loc_definition"],
        "loc_category_definition": policy["measurement"]["loc_category_definition"],
        "metric_version": policy["measurement"]["metric_version"],
    }

    # Outside the endpoint worktree: the baseline complexity measurement
    # opens its own worktree at before_head, cached per (repo, before_head)
    # (see _BASELINE_COMPLEXITY_CACHE).
    size_complexity = compute_size_complexity(repo, before_head, commit, endpoint_complexity_payload, policy, measurement)
    hygiene = measure_hygiene(repo, before_head, commit, measurement, policy["hygiene"])

    # infrastructure_failure_suspected is a heuristic this tool has no basis
    # to compute, so a value already on the sheet is carried over rather than
    # reset; only a first-time sheet defaults it to false.
    existing_run_status = (existing_sheet or {}).get("run_status") or {}
    run_status = {
        "pm_status": run_state.get("status"),
        "slice_status": entry.get("status"),
        "stop_reason": run_state.get("stop_reason"),
        "infrastructure_failure_suspected": existing_run_status.get("infrastructure_failure_suspected", False),
    }
    provenance = build_provenance(
        run_state, policy_path, obligations_path, before_head, root, task, hidden_files, args.slice
    )
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
            # Grouped by tool, not severity: lint.py's findings carry no
            # severity.
            "lint_findings_by_tool": lint_result,
            "code_health_findings_by_category": health_result,
        },
        "scope": scope,
        # ΔLOC/ΔCC against this slice's own before_head -- descriptive
        # supporting measures, never scored (see
        # compute_size_complexity/compute_complexity_delta).
        "size_complexity": size_complexity,
        # Narration/comment/commit-subject census against the same
        # baseline -- descriptive, never scored (see measure_hygiene).
        "hygiene": hygiene,
        # The candidate's own suite against this slice's seeded mutants --
        # a second, independent measure, never blended into correctness.
        "test_kill_rate": test_kill_rate,
        # Read per-attempt from the event log, not from run.json's one
        # decision-per-slice field -- see resolve_pm_decision. None means the
        # attempt is not yet decided.
        "pm_decision": resolve_pm_decision(events, slice_id, attempt),
    }

    # The Developer identity is resolved fresh on every grade, never read as
    # a bare run.json["harness"]["model"] string, which can be null. A
    # genuine conflict between sources is refused; an unattributed run (no
    # conflict, just nothing recorded) is graded normally.
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
