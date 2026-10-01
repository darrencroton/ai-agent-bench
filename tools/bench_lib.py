#!/usr/bin/env python3
"""Shared helpers for this bench's scoring tools: the pieces of state several
tools otherwise reimplemented independently, with subtly different semantics
(AGENTS.md: "minimum, no dead code"; "prefer one parameterised script to two
near-identical ones"): attempt numbering, event-log reading, judgment and
Developer-identity resolution, atomic writes, the multi-task registry
resolver (resolve_task), the pinned-plan-commit parse
(parse_pinned_plan_commit, kept here so dev_check.py can use it without a
circular import on cohort_run.py), and the git-worktree membership check
(repo_belongs_to_task).

This is a shared-helpers module, not a framework: nothing goes in here that
more than one tool does not need.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


class BenchLibError(RuntimeError):
    """The shared error type: raised directly by every bench_lib helper, and
    subclassed by each CLI tool (DevCheckError, CohortRunError, GradeRunError,
    LeaderboardError, ModelReportError, ReviewScoreError).

    Convention: a bench_lib helper failing loudly raises THIS base type; each
    tool re-raises it under its own subclass at its own call sites, so the
    failure still reads as "dev_check.py: error: ..." rather than an
    unfamiliar third name, and the tool's top-level handler -- which catches
    its own subclass specifically, not this parent -- keeps working unchanged.
    Catching this base type anywhere in the chain sees every condition below.
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

    The count of these events, never `run.json`'s own `attempts` counter, is
    the monotonic per-slice attempt key (see attempt_ordinal()).
    `pm_lib.slice_ops.start_slice` resets that counter to 0 whenever a stopped
    slice is relaunched (a `finalize --stop` clears `current_slice`, so the
    next `start-slice` takes the non-relaunch branch), even though the slice
    may already carry several attempts. The event log has no such reset, so
    counting its launch events survives a stop/restart cycle intact.
    """
    return [i for i, e in enumerate(events) if e.get("kind") in LAUNCH_KINDS and e.get("slice") == slice_id]


def attempt_ordinal(events: list[dict[str, Any]], slice_id: str, *, before_index: int | None = None) -> int:
    """The monotonic 0-based attempt ordinal open at `before_index` (or, by
    default, the latest one recorded for the slice) -- the sheet's real key
    (see launch_family_indices for why this, not PM's own `attempts`
    counter, is used). dev_check.py (the latest or an explicitly requested
    attempt) and review_score.py (the attempt live when a review ran) both
    derive their attempt number from this function, so they cannot disagree.

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
    `attempt - epoch_start_ordinals(events, slice_id)[attempt]` is PM's own
    attempts counter at that historical moment (dev_check.py's
    `resolve_pm_attempts_counter`), and each epoch's before_head (used by
    grade_run.py's attempt-commit walk) is constant for every attempt sharing
    the same epoch start, since neither fact changes until the next `launch`.
    """
    opens = launch_family_indices(events, slice_id)
    starts: list[int] = []
    current_epoch_start = 0
    for ordinal, event_index in enumerate(opens):
        if events[event_index].get("kind") == "launch":
            current_epoch_start = ordinal
        starts.append(current_epoch_start)
    return starts


def active_judgments(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Judgment records still in force, from one slice's own
    `developer_judgments`/`review_judgments` list.

    project-manager re-judges a submission or review by appending a NEW
    record whose own `supersedes` names the earlier record's `judgment_id`
    -- it never edits or removes the earlier one in place. A record is
    superseded exactly when some other record in THIS SAME collection names
    its `judgment_id` in `supersedes` -- list position and timestamp play no
    role, so this needs no sorting and no "most recent wins" heuristic of
    its own.

    Shared by `resolve_developer_identity` (for `developer_judgments`) and
    `review_score.py`'s reviewer-judgment harvest (`review_judgments`).

    Args:
        records: one slice's own judgment list, in file order (order does
            not matter to this function, but callers should pass it as
            recorded).

    Returns:
        `records`, minus any whose own `judgment_id` is named by another
        record's `supersedes`. A record with no `judgment_id` at all can
        never be superseded (nothing could ever name it), so it always
        survives -- this function raises on nothing; a malformed judgment
        record is its caller's problem to name, not this shared filter's.
    """
    superseded_ids = {record["supersedes"] for record in records if record.get("supersedes")}
    return [record for record in records if record.get("judgment_id") not in superseded_ids]


# The three Developer-identity fields resolve_developer_identity merges, and
# the sentinel each renders as in configuration_key when unresolved -- an
# unrecorded field stays visibly distinct from any recorded value, never
# dropped or blended into the model/harness position.
_IDENTITY_FIELDS = ("harness", "model", "effort")
_UNKNOWN_SENTINELS = {"harness": "harness unknown", "model": "model unknown", "effort": "effort unknown"}

# Source names, in priority order for *display* only (which source's name
# is recorded in the returned block's `sources` mapping when more than one
# source agrees on a value). Priority carries no weight in conflict
# detection itself -- any two non-null values that disagree are a named
# error regardless of which sources produced them (see
# resolve_developer_identity's docstring).
_IDENTITY_SOURCE_PRIORITY = ("pm_developer_judgment", "run_harness", "operator_attestation")


def resolve_developer_identity(
    run_state: dict[str, Any], *, run_id: str, corrections: dict[str, Any]
) -> tuple[dict[str, Any], list[str]]:
    """The Developer configuration this run measured, with its provenance.

    Merges three sources, in this priority order for display attribution
    only (see below for why priority does not decide conflicts):

    1. `slices[].developer_judgments[].developer` snapshots, across every
       slice, taken through `active_judgments` -- PM's own immutable record
       of what it launched (`{tool, model, effort}`; `tool` is this
       function's `harness` field -- the two sources genuinely disagree on
       the field's own name).
    2. `run_state["harness"]` -- `{name, model, effort, command_override}`;
       `name` is this function's `harness` field, matching the judgment
       snapshot's `tool` for the same underlying concept.
    3. `corrections[run_id]` -- `policy.yaml`'s `identity.corrections`, an
       operator attestation used only to fill a field neither structural
       source above recorded.

    Merge rule, applied uniformly across all three sources for each field
    independently: **null means "not recorded," never a conflicting
    value.** Zero non-null values leaves the field unresolved (None, no
    named problem -- an honest gap). Exactly one distinct non-null value
    (however many sources agree on it) resolves the field, attributed to
    the highest-priority source that supplied it. **Two or more distinct
    non-null values for the same field is a named problem, naming every
    source and value in conflict -- the field is never averaged and never
    silently picked from one side**, so it resolves to None with the
    conflict recorded in the returned problems list, exactly as an
    unrecorded field would, but with the reason stated. This is what lets a
    run resolve `effort: "low"` when the harness block recorded null but
    PM's judgment recorded low, without any special-casing: a null and a
    non-null are never "two differing values."

    `command_override` needs no special case: a `command_override` run
    records its `model` when given, and an omitted `effort` as the literal
    string "default", both ordinary values. A run whose override named no
    model at all (or an older run recorded before pm_lib did this) carries a
    genuine null and resolves unattributed by the general rule above, unless
    an operator attestation fills that gap (`identity.corrections` exists for
    exactly this).

    Args:
        run_state: the parsed run.json.
        run_id: this run's id, used only to look up `corrections[run_id]`
            and to name this run in any conflict problem.
        corrections: `policy.yaml`'s `identity.corrections` mapping (run id
            -> `{harness, model, effort, reason, evidence}`); an empty dict
            when the policy carries none.

    Returns:
        (block, problems). `block` always has the shape:
        `{"harness": ..., "model": ..., "effort": ..., "configuration_key":
        ..., "sources": {...}, "attributed": bool, "attestation": dict |
        None}`. `configuration_key` joins the three fields (rendering an
        unresolved one as its own distinct "<field> unknown" sentinel, per
        the module-level docstring) -- the grouping and display identity,
        never merged across runs by spelling similarity. `attributed` is
        true only when both `harness` and `model` resolved to a value.
        `attestation` is the correction dict itself when it was actually
        used to fill a gap, else None (an attestation that only echoed an
        already-resolved value used nothing and is not recorded here).
        `problems` names every field conflict found; an empty list means
        every field agreed (or was simply unrecorded) everywhere it was
        looked for.
    """
    harness_block = run_state.get("harness") or {}
    correction = (corrections or {}).get(run_id)
    if correction is not None and not isinstance(correction, dict):
        # policy.yaml is hand-edited by the operator, so a malformed
        # attestation is a realistic typo -- name the run and what was
        # found rather than letting a bare AttributeError escape from the
        # `.get(field)` below (AGENTS.md: every error names the concrete
        # file, path or parameter).
        raise BenchLibError(
            f"policy.yaml's identity.corrections[{run_id!r}] must be a mapping of "
            f"{{harness, model, effort, reason, evidence}}, got {correction!r}"
        )
    for field in _IDENTITY_FIELDS if correction else ():
        value = correction.get(field)
        if value is not None and not isinstance(value, str):
            raise BenchLibError(
                f"policy.yaml's identity.corrections[{run_id!r}].{field} must be a string or null, got {value!r}"
            )

    judgment_snapshots: list[dict[str, Any]] = []
    for slice_entry in run_state.get("slices") or []:
        if not isinstance(slice_entry, dict):
            continue
        for judgment in active_judgments(slice_entry.get("developer_judgments") or []):
            judgment_snapshots.append(judgment.get("developer") or {})

    # run.json's harness block names the same three concepts by different
    # keys than a judgment snapshot does (see docstring) -- normalise both
    # structural sources to this function's own field names once, here.
    harness_values = {
        "harness": harness_block.get("name"),
        "model": harness_block.get("model"),
        "effort": harness_block.get("effort"),
    }
    judgment_values_by_field: dict[str, list[Any]] = {field: [] for field in _IDENTITY_FIELDS}
    for snapshot in judgment_snapshots:
        judgment_values_by_field["harness"].append(snapshot.get("tool"))
        judgment_values_by_field["model"].append(snapshot.get("model"))
        judgment_values_by_field["effort"].append(snapshot.get("effort"))

    resolved: dict[str, Any] = {}
    sources: dict[str, str] = {}
    attestation_applied = False
    problems: list[str] = []

    for field in _IDENTITY_FIELDS:
        candidates: list[tuple[str, Any]] = []
        for value in judgment_values_by_field[field]:
            if value is not None:
                candidates.append(("pm_developer_judgment", value))
        if harness_values[field] is not None:
            candidates.append(("run_harness", harness_values[field]))
        if correction is not None and correction.get(field) is not None:
            candidates.append(("operator_attestation", correction[field]))

        distinct_values = {value for _source, value in candidates}
        if not distinct_values:
            continue  # unresolved: no source recorded this field at all.
        if len(distinct_values) > 1:
            detail = ", ".join(f"{source}={value!r}" for source, value in candidates)
            problems.append(f"run {run_id}: developer.{field} conflict across sources: {detail}")
            continue  # never average or pick between disagreeing sources.

        value = next(iter(distinct_values))
        source = next(s for s in _IDENTITY_SOURCE_PRIORITY if any(cs == s and cv == value for cs, cv in candidates))
        resolved[field] = value
        sources[field] = source
        if source == "operator_attestation":
            attestation_applied = True

    harness = resolved.get("harness")
    model = resolved.get("model")
    effort = resolved.get("effort")
    attributed = harness is not None and model is not None

    configuration_key = " · ".join(
        resolved.get(field, _UNKNOWN_SENTINELS[field]) for field in ("model", "harness", "effort")
    )

    block = {
        "harness": harness,
        "model": model,
        "effort": effort,
        "configuration_key": configuration_key,
        "sources": sources,
        "attributed": attributed,
        "attestation": correction if attestation_applied else None,
    }
    return block, problems


def validate_sheet_identity(sheet: dict[str, Any], run_id: str, slice_number: int, path: Path) -> None:
    """Refuse a scoring sheet that belongs to a different run or slice.

    dev_check.py's `--out` and review_score.py's `--sheet` accept an explicit
    path; without this check, pointing either at another run's or slice's
    sheet would silently read or write the wrong cohort's data.

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
    Shared by write_json_atomically and leaderboard.py's Markdown render.
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

    Shared by grade_run.py and model_report.py, whose `main()`s collect a flat
    list of named problems (never raising for any single one) and finish with
    the same count-then-list-then-exit-code shape.

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

    Resolved relative to *this module's own location* (tools/), not the
    caller's cwd. Otherwise a tool invoked from the Developer's own repo (the
    natural place to run review_score.py from) would resolve its default
    --sheet/--out path into the wrong repository.

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


# --- multi-task registry ------------------------------------------------------

# The one line a plan provenance file must carry naming its exact source
# commit, parsed live so it is never duplicated as a driftable second source.
_PINNED_PLAN_COMMIT_RE = re.compile(r"Pinned commit:\s*`([0-9a-f]{7,40})`")


def parse_pinned_plan_commit(provenance_path: Path) -> str:
    """The exact commit a task's frozen plan was vendored from, parsed live
    from its provenance file's "Pinned commit: `<hash>`" line. Every trial
    worktree of that task starts from this commit, the known-clean baseline
    its plan and hidden tests were validated against.

    Lives here because dev_check.py and cohort_run.py both need it and
    cohort_run.py imports dev_check.py, so importing it from cohort_run.py
    would be circular.

    Raises:
        BenchLibError: the provenance file is missing, or has no
            "Pinned commit: `...`" line to parse -- never a stale fallback.
    """
    if not provenance_path.is_file():
        raise BenchLibError(f"{provenance_path} not found; cannot determine this bench's pinned plan commit")
    match = _PINNED_PLAN_COMMIT_RE.search(provenance_path.read_text(encoding="utf-8"))
    if not match:
        raise BenchLibError(f'{provenance_path} has no "Pinned commit: `...`" line to parse')
    return match.group(1)


# Every key a policy.yaml `tasks:` entry must carry. The path keys are
# relative: `repo`/`worktree_root` against this bench's own root,
# `plan_file` against the *target repo*, and
# `provenance_file`/`hidden_tests_dir`/`obligations_file`/`mutations_dir`
# against *this bench's own root* -- see policy.yaml's comment on the block
# for why each lives where it does.
_TASK_ENTRY_PATH_KEYS = (
    "repo",
    "branch_prefix",
    "plan_file",
    "provenance_file",
    "hidden_tests_dir",
    "obligations_file",
    "mutations_dir",
)
_TASK_ENTRY_REQUIRED_KEYS = (*_TASK_ENTRY_PATH_KEYS, "worktree_root", "expected_slices", "measurement")
# The per-task measurement sub-block carries only the target repo's layout
# globs; the methodology keys stay in policy.yaml's global measurement block.
_TASK_MEASUREMENT_BUCKETS = ("production_paths", "test_paths", "doc_paths")


def validate_task_registry(policy: dict[str, Any]) -> dict[str, Any]:
    """Validate the shape of policy.yaml's `tasks:` registry, not any entry.

    Returns:
        The `tasks` mapping, unmodified.

    Raises:
        BenchLibError: `tasks` is missing, empty or not a mapping, carries a
            non-string or empty key, or `default_task` is not a non-empty
            string naming a configured entry. Entry contents are never
            inspected here, so one broken entry does not hide the others.
    """
    tasks = policy.get("tasks")
    if not isinstance(tasks, dict) or not tasks:
        raise BenchLibError("policy.yaml is missing its required non-empty 'tasks' mapping")
    # YAML parses unquoted numeric/boolean-looking keys as int/bool, so a
    # hand-edited policy can carry non-string task ids; refuse them here,
    # before ANY message path sorts or joins the key set (which would crash
    # with a raw TypeError instead of a named error).
    bad_keys = [key for key in tasks if not isinstance(key, str) or not key]
    if bad_keys:
        raise BenchLibError(
            f"policy.yaml's tasks: mapping must be keyed by non-empty task-id strings, got: {bad_keys!r}"
        )
    default_task = policy.get("default_task")
    if not isinstance(default_task, str) or not default_task:
        raise BenchLibError(
            f"policy.yaml's default_task must be a non-empty string naming a tasks: entry, got {default_task!r}"
        )
    # Checked before any entry is resolved, so a policy whose default_task
    # points nowhere is refused even when a caller explicitly requests some
    # other, validly-configured entry.
    if default_task not in tasks:
        raise BenchLibError(
            f"policy.yaml's default_task={default_task!r} does not name a configured task; "
            f"configured tasks: {', '.join(sorted(tasks))}"
        )
    return tasks


def resolve_task(policy: dict[str, Any], task_id: str | None) -> dict[str, Any]:
    """Resolve and validate one entry of policy.yaml's `tasks:` registry.

    The single place a task id becomes a fully-checked configuration:
    every tool that needs task configuration calls this, so validation rigor
    is applied once, identically, everywhere.

    Args:
        policy: the parsed policy mapping (any loader's output -- this
            function reads only `default_task` and `tasks`, nothing else).
        task_id: the task to resolve; None falls back to
            `policy["default_task"]`.

    Returns:
        A fresh, self-describing dict holding exactly the resolved `task_id`
        plus the entry's validated keys (any other key in the entry is
        dropped), with values exactly as written in policy.yaml -- relative
        paths stay relative, and each consumer resolves them against its own
        root. Never aliases the caller's policy mapping.

    Raises:
        BenchLibError: `tasks` is missing/malformed or carries a non-string
            key, `default_task` is missing/malformed or points at no
            configured entry (all checked even when an explicit `task_id` is
            given -- a broken policy file is refused regardless of which
            entry happens to be requested), `task_id` names no configured
            task (naming both it and the ids that ARE configured), or any
            required key is missing or of the wrong type (naming the task id
            and the specific key). Never defaults, coerces, or guesses.
    """
    tasks = validate_task_registry(policy)
    default_task = policy["default_task"]
    if task_id is None:
        task_id = default_task
    elif not isinstance(task_id, str) or not task_id:
        raise BenchLibError(f"task_id must be a non-empty string or None (to use default_task), got {task_id!r}")
    if task_id not in tasks:
        raise BenchLibError(f"unknown task {task_id!r}; configured tasks: {', '.join(sorted(tasks))}")
    entry = tasks[task_id]
    if not isinstance(entry, dict):
        raise BenchLibError(f"task {task_id!r}'s entry must be a mapping, got {entry!r}")
    _validate_task_entry(task_id, entry)
    # Only the validated keys are carried over, and the measurement
    # sub-block (with its glob lists) is copied, so a mutation through the
    # result can never rewrite the shared parsed policy object.
    resolved: dict[str, Any] = {"task_id": task_id}
    for key in _TASK_ENTRY_REQUIRED_KEYS:
        resolved[key] = entry[key]
    resolved["measurement"] = {bucket: list(entry["measurement"][bucket]) for bucket in _TASK_MEASUREMENT_BUCKETS}
    return resolved


def _validate_task_entry(task_id: str, entry: dict[str, Any]) -> None:
    """Validate one `tasks:` entry's presence-and-type contract, raising
    BenchLibError that names the task id and the specific offending key --
    the same fail-loudly-and-specifically rigor dev_check._validate_
    measurement_policy applies to the global measurement block."""
    missing = [key for key in _TASK_ENTRY_REQUIRED_KEYS if key not in entry]
    if missing:
        raise BenchLibError(f"task {task_id!r} is missing required key(s): {', '.join(missing)}")
    for key in _TASK_ENTRY_PATH_KEYS:
        value = entry[key]
        if not isinstance(value, str) or not value:
            raise BenchLibError(f"task {task_id!r}'s {key} must be a non-empty string, got {value!r}")
    worktree_root = entry["worktree_root"]
    # null is legal: trial worktrees are then created as siblings of the repo.
    if worktree_root is not None and (not isinstance(worktree_root, str) or not worktree_root):
        raise BenchLibError(f"task {task_id!r}'s worktree_root must be null or a non-empty string, got {worktree_root!r}")
    expected_slices = entry["expected_slices"]
    if not isinstance(expected_slices, int) or isinstance(expected_slices, bool) or expected_slices <= 0:
        raise BenchLibError(f"task {task_id!r}'s expected_slices must be a positive integer, got {expected_slices!r}")
    measurement = entry["measurement"]
    if not isinstance(measurement, dict):
        raise BenchLibError(f"task {task_id!r}'s measurement sub-block must be a mapping, got {measurement!r}")
    for bucket in _TASK_MEASUREMENT_BUCKETS:
        globs = measurement.get(bucket)
        if not isinstance(globs, list) or not globs or not all(isinstance(g, str) and g for g in globs):
            raise BenchLibError(
                f"task {task_id!r}'s measurement.{bucket} must be a non-empty list of glob strings, got {globs!r}"
            )


def repo_belongs_to_task(candidate_repo_path: Path, configured_repo_path: Path) -> bool:
    """Whether `candidate_repo_path` is the same repository as
    `configured_repo_path`: either literally the same path, or a registered
    `git worktree` of it.

    A graded run's recorded target-repo path is a *trial worktree* of the
    substrate repo policy.yaml configures (e.g. relative-velocity-trial-1),
    never literally equal to it, so this checks actual git worktree
    membership via `git -C <configured> worktree list --porcelain -z` (`-z`
    because a worktree path can legally contain a newline) rather than
    path-string equality. Both paths are resolved before comparing.

    Shared by dev_check.py's cross-check that a graded run's repository
    belongs to the resolved task, and cohort_run.py's inference of an omitted
    --task from --dev-repo.

    Raises:
        BenchLibError: the paths are not literally equal AND git cannot be
            run, `git worktree list` fails against `configured_repo_path`
            (not a usable git repository), or it lists a different repository
            than the one `configured_repo_path` names (possible when it sits
            inside another repo's tree). Membership cannot then be determined
            structurally, and guessing False would silently misattribute a
            run.
    """
    candidate = candidate_repo_path.resolve()
    configured = configured_repo_path.resolve()
    if candidate == configured:
        return True
    try:
        result = subprocess.run(
            ["git", "-C", str(configured), "worktree", "list", "--porcelain", "-z"],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise BenchLibError(f"could not run git to check whether {candidate} belongs to {configured}: {exc}") from exc
    if result.returncode != 0:
        raise BenchLibError(
            f"`git -C {configured} worktree list` failed while checking whether {candidate} belongs to it: "
            f"{result.stderr.strip() or result.returncode}"
        )
    worktrees = [
        Path(field.partition(" ")[2]).resolve()
        for field in result.stdout.split("\0")
        if field.startswith("worktree ")
    ]
    # The enumeration is only trustworthy if it is of the repository
    # `configured` actually names: when `configured` is not itself a
    # repository location, git resolves to whatever repository encloses it,
    # and answering from THAT repo's worktree list would be a silent guess.
    if configured not in worktrees:
        raise BenchLibError(
            f"`git -C {configured} worktree list` resolved to a different repository "
            f"(its worktrees are: {', '.join(str(w) for w in worktrees)}); refusing to guess "
            f"whether {candidate} belongs to {configured}"
        )
    return candidate in worktrees
