#!/usr/bin/env python3
"""Tool 1: correctness, independent quality, and scope-discipline grading
for one PM slice attempt (docs/MODE2-REWRITE-PLAN.md §7, "Tool 1").

Design note -- refinement of §7's prose (deliberate, not a redesign):
§7 describes this tool as something that "watches events.jsonl". That watch
loop is the driver's job (tools/run_seat.py, §7a), a later work item this
module does not build. This module is a pure, one-shot grading command:
given a PM run directory and a slice number, it grades exactly one attempt
(the current one, by default) and upserts one entry into that slice's
cumulative scoring sheet (§6). It never polls, never daemonizes, and never
re-invokes itself. **The driver is expected to call it once per `floor`
event, and once more after `accept` lands** (§7's Tool 1 notes 2 and 3) --
never at `launch`/`relaunch`/`steer` itself, which only opens an attempt
before the Developer has committed anything gradeable, and an accepted
slice's `before_head` can only be recovered from a sheet an earlier grade of
that same attempt already wrote (see resolve_before_head). Re-running this
tool for an attempt already graded replaces that attempt's row and refreshes
its timestamp -- not byte-identical (the timestamp always advances), but it
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
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
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

    # G12: "local" is the only implemented backend. An unimplemented backend
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
    return policy


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


def resolve_pm_attempts_counter(run_state: dict[str, Any], slice_id: str, entry: dict[str, Any]) -> int:
    """PM's own `attempts` counter: current_slice.attempts when this slice is
    current, else the slice entry's own attempts (run-state.md's "Attempts"
    semantics).

    Recorded on the attempt entry as `pm_attempts_counter` -- what a human
    reading PM's own output sees -- but never used as the sheet's key.
    `pm_lib.slice_ops.start_slice` resets this counter to 0 whenever a
    stopped slice is relaunched (finding 2), so keying on it would silently
    overwrite the earlier attempt-0 row the moment the slice restarts. See
    resolve_attempt() for the actual key.

    This function always reads the *current* run.json state, so calling it
    again to regrade a historical `--attempt` returns whatever PM's counter
    is now, not what it was when that attempt was first opened -- exactly
    the same staleness risk `provenance` has. `upsert_attempt` is what
    actually protects the recorded value on a regrade, by preserving the
    existing attempt's `pm_attempts_counter` rather than accepting whatever
    this function returns a second time (finding 2).
    """
    current_slice = run_state.get("current_slice") or {}
    attempts = current_slice.get("attempts") if current_slice.get("id") == slice_id else entry.get("attempts")
    if attempts is None:
        raise DevCheckError(f"could not resolve PM's attempts counter for {slice_id!r} from run.json")
    return int(attempts)


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
    run_state: dict[str, Any], slice_id: str, existing_sheet: dict[str, Any] | None, attempt: int
) -> str:
    """current_slice.before_head, the base commit correctness/quality/scope
    are all measured against -- falling back to this same attempt's own
    previously recorded provenance once this slice is no longer current.

    Only the currently active slice carries a recorded before_head
    (run-state.md's schema has no such field on a completed slice entry).
    That collides with A1: `finalize_accept` sets `entry["status"]="accepted"`
    and `state["current_slice"]=None` in the *same* state write (verified
    against pm_lib/slice_ops.py), so the moment a slice is accepted this
    branch would always raise and the accepted attempt could never be graded
    -- accepted_at_attempt would stay permanently null. The sheet this tool
    itself wrote earlier already recorded this attempt's provenance.base_commit
    == the same before_head (finding 4: provenance moved to per-attempt), so
    once current_slice no longer names this slice, that recorded value is
    reused instead of insisting on a live one.

    Note for the driver (§7's "closing out an accepted slice" case): grading
    an accepted slice therefore requires a sheet already on disk from an
    earlier grade of the same attempt -- the driver is expected to call
    dev_check.py once more after the `accept` event lands, not for the first
    time.

    Raises:
        DevCheckError: naming both places looked (current_slice and this
            attempt's own recorded provenance), if neither carries a
            before_head.
    """
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

    raise DevCheckError(
        f"slice {slice_id!r} is not run.json's current_slice (current is "
        f"{current_slice.get('id')!r}), and no existing scoring sheet entry for attempt {attempt} with a "
        "recorded provenance.base_commit was found to fall back to; before_head cannot be resolved"
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
    way out, success or failure, per docs/MODE2-REWRITE-PLAN.md §7 Tool 1
    step 3.
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


def run_hidden_tests(worktree: Path, slice_number: int, root: Path, policy: dict[str, Any]) -> dict[str, str]:
    """Copy this slice's hidden tests into the worktree and run pytest once.

    Never points pytest at both hidden_tests/slice1/ and hidden_tests/slice2/
    in the same invocation -- they share filenames and collection would fail
    (docs/MODE2-REWRITE-PLAN.md §8, G4's resolution note).

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
    single "0 means available" assumption can be shared between them
    (finding 1: a shared "any nonzero exit is unavailable" rule previously
    misrecorded lint.py's exit 1, "new findings were found", as unavailable
    coverage instead of the findings themselves).

    Never reinterprets or invents a composite score (§6 is explicit that
    none exists at the per-attempt level); a genuinely unavailable or
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
    silently count every pre-existing finding as new (finding 1). The
    payload's own `verdict` and its `uncovered`/`missing_binaries` lists are
    surfaced too, so a coverage gap reads as one in the sheet rather than
    looking like a clean pass. The full raw payload is kept verbatim
    alongside all of it.

    `--require-coverage` (finding 7) makes lint.py exit 3 ("coverage-gap",
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

    `--require-coverage` (finding 7) makes health.py exit 3 ("coverage-gap",
    already scoreable per `_HEALTH_SCOREABLE_EXIT_CODES`/`_HEALTH_EXIT_COVERAGE`)
    when a required language in scope has unavailable metric coverage,
    rather than silently reporting whatever partial measurement it managed
    -- the same honesty requirement as lint.py's flag above.
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
    result["verdict"] = "coverage-gap" if result["exit_code"] == _HEALTH_EXIT_COVERAGE else "pass"
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


def build_provenance(run_state: dict[str, Any], policy_path: Path, obligations_path: Path, before_head: str) -> dict[str, Any]:
    """plan_hash, policy_hash, obligations_hash, base_commit, pm_skill_version
    -- §6's provenance block, recorded per attempt (finding 4).

    A sheet-level provenance field, overwritten on every upsert, made an
    earlier attempt look like it was graded under whatever policy.yaml or
    obligations.yaml happen to read at the moment of a *later* attempt's
    grade -- exactly the "rules changed silently" case §3 requires this
    field to detect. So this is captured once, at an attempt's first grade,
    and upsert_attempt() never rewrites it on a regrade of that same
    attempt. `obligations_hash` is the sha256 of the obligation map --
    docs/OBLIGATION-GROUPS.md establishes that the partition *is* the
    correctness rubric, so a later change to it must be as detectable as a
    policy or plan change. `pm_skill_version` is null (not a guess):
    project-manager carries no version marker anywhere in SKILL.md,
    README.md, or scripts/.
    """
    return {
        "plan_hash": run_state.get("plan", {}).get("sha256"),
        "policy_hash": hashlib.sha256(policy_path.read_bytes()).hexdigest(),
        "obligations_hash": hashlib.sha256(obligations_path.read_bytes()).hexdigest(),
        "base_commit": before_head,
        "pm_skill_version": None,
    }


def upsert_attempt(
    existing_sheet: dict[str, Any] | None,
    *,
    run_id: str,
    model: str | None,
    slice_number: int,
    run_status: dict[str, Any],
    attempt_entry: dict[str, Any],
    accepted_at_attempt: int | None,
    pm_model_performance_ref: str | None,
) -> dict[str, Any]:
    """Upsert one attempt into the cumulative scoring sheet, by attempt number.

    Every other attempt is preserved untouched, in place, along with any
    `drift_review`/`code_review` fields already recorded on the attempt
    being replaced (Tool 2/3's job, not this tool's -- this upsert must
    never clobber them); that attempt's own `provenance` if it was already
    graded once (finding 4: captured at an attempt's first grade and never
    rewritten, so a later policy.yaml/obligations.yaml edit cannot silently
    make an earlier attempt look graded under new rules); and that attempt's
    own `pm_attempts_counter` if it was already graded once (finding 2, the
    same preservation rule as provenance: `--attempt` can regrade any
    existing historical attempt, and PM's own `attempts` counter on
    `run.json` reflects only the *current* state, not what it was when this
    attempt was first opened -- a stopped-then-restarted slice resets it to
    0, so re-grading attempt 0 after a later restart would otherwise silently
    overwrite its recorded counter with a value that now points at the
    wrong `attempt-<n>/` artifacts on disk, defeating the field's only
    purpose).

    Raises:
        DevCheckError: an existing sheet at the same path is for a
            different run_id or slice -- writing into it would silently mix
            two runs' data.
    """
    if existing_sheet is None:
        sheet: dict[str, Any] = {
            "run_id": run_id,
            "model": model,
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
        sheet["model"] = model
        sheet["run_status"] = run_status
        sheet["accepted_at_attempt"] = accepted_at_attempt
        sheet["pm_model_performance_ref"] = pm_model_performance_ref

    attempts = sheet.setdefault("attempts", [])
    for index, existing_attempt in enumerate(attempts):
        if existing_attempt.get("attempt") == attempt_entry["attempt"]:
            for key in ("drift_review", "code_review"):
                if key not in attempt_entry and key in existing_attempt:
                    attempt_entry[key] = existing_attempt[key]
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
        description="Grade one PM slice attempt: correctness, independent quality, scope discipline (docs/MODE2-REWRITE-PLAN.md §7, Tool 1)."
    )
    parser.add_argument("--run-dir", required=True, type=Path, help="PM run state directory containing run.json and events.jsonl")
    parser.add_argument("--slice", required=True, type=int, help="slice number (1 or 2), matching hidden_tests/obligations.yaml")
    parser.add_argument(
        "--attempt", type=int, default=None,
        help="the monotonic event-derived attempt ordinal to grade (defaults to the latest recorded for the slice)"
    )
    parser.add_argument("--commit", default=None, help="defaults to the Developer repo's current HEAD")
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
    # finding 2: the sheet's key is the monotonic event-derived ordinal, not
    # PM's own `attempts` counter (which resets on a stopped-then-restarted
    # slice) -- PM's counter is still resolved below, but only to record it
    # on the attempt entry, never to key the sheet.
    attempt = resolve_attempt(events, slice_id, args.attempt)
    pm_attempts_counter = resolve_pm_attempts_counter(run_state, slice_id, entry)

    # A1: the existing sheet must be loaded *before* resolving before_head --
    # once a slice is accepted, run.json's current_slice no longer names it
    # (finalize_accept clears current_slice in the same write that marks the
    # slice accepted), so before_head can only be recovered from a sheet this
    # tool wrote on an earlier grade of the same attempt. See
    # resolve_before_head's docstring.
    out_path = (args.out or (root / "results" / "runs" / run_state["run_id"] / f"slice-{args.slice}.json")).expanduser().resolve()
    existing_sheet = load_existing_sheet(out_path, run_state["run_id"], args.slice)
    before_head = resolve_before_head(run_state, slice_id, existing_sheet, attempt)

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
        # A2: lint/code-health MUST run before run_hidden_tests copies this
        # slice's held-out test files into worktree/tests/ -- both quality
        # tools run in --base differential mode, which includes untracked
        # files, so measuring after the copy silently attributes the bench's
        # own hidden tests to the Developer (empirically confirmed: lint and
        # code-health both flagged tests/test_hA.py when run in the wrong
        # order). Never reorder this back.
        lint_result = run_lint(worktree, before_head, policy)
        health_result = run_code_health(worktree, before_head, policy)
        outcomes = run_hidden_tests(worktree, args.slice, root, policy)
        correctness = score_correctness(outcomes, groups, args.slice)
        scope = compute_scope(pm_plan, pm_git_ops, repo, before_head, commit, plan_slice, run_state)

    # A5: infrastructure_failure_suspected is a driver-computed heuristic
    # (§6) this tool has no basis to set -- if the driver already recorded it
    # true on an earlier grade, a regrade must not silently reset it to
    # false. Only a first-time sheet defaults it to false.
    existing_run_status = (existing_sheet or {}).get("run_status") or {}
    run_status = {
        "pm_status": run_state.get("status"),
        "slice_status": entry.get("status"),
        "stop_reason": run_state.get("stop_reason"),
        "infrastructure_failure_suspected": existing_run_status.get("infrastructure_failure_suspected", False),
    }
    provenance = build_provenance(run_state, policy_path, root / OBLIGATIONS_RELATIVE_PATH, before_head)
    accepted_at_attempt = resolve_accepted_at_attempt(existing_sheet, entry.get("status"), attempt)
    pm_model_performance_ref = resolve_model_performance_ref(run_dir, existing_sheet)

    attempt_entry = {
        "attempt": attempt,
        # PM's own counter, for a human cross-referencing PM's output --
        # never the sheet's key (finding 2; see resolve_pm_attempts_counter).
        "pm_attempts_counter": pm_attempts_counter,
        "commit_sha": commit,
        "timestamp": utc_now_iso(),
        # Captured fresh here but never rewritten on a regrade of this same
        # attempt -- see build_provenance/upsert_attempt (finding 4).
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
        # Read per-attempt from the event log, not from run.json's one
        # decision-per-slice field -- see resolve_pm_decision. None means the
        # attempt is not yet decided.
        "pm_decision": resolve_pm_decision(events, slice_id, attempt),
    }

    sheet = upsert_attempt(
        existing_sheet,
        run_id=run_state["run_id"],
        model=run_state.get("harness", {}).get("model"),
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
