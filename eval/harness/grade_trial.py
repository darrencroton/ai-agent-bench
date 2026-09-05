#!/usr/bin/env python3
"""Grade one trial produced by run_trial.py.

Everything here is automated and mechanical except the two `judged`
categories in rubric.yaml, which call a fixed judge model if one is
configured. No step in this file re-prompts the Developer model or gives it
a chance to fix anything -- grading happens once, after the fact, exactly
like a real benchmark run.

Usage:
    python eval/harness/grade_trial.py --manifest <path-to-manifest.json>
"""
import argparse
import fnmatch
import hashlib
import importlib.metadata
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harnesses import build_command  # noqa: E402


def repo_root():
    out = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True, check=True)
    return out.stdout.strip()


def _decode(x):
    """CPython quirk: subprocess.run's TimeoutExpired.stdout/.stderr carry
    raw bytes from the partial read even when text=True was passed -- the
    text decoding only applies on the successful, non-timeout completion
    path. Every caller of run() below treats out/err as str."""
    if isinstance(x, bytes):
        return x.decode(errors="replace")
    return x or ""


def run(cmd, cwd=None, env=None, timeout=None):
    try:
        p = subprocess.run(cmd, cwd=cwd, env=env, timeout=timeout,
                            capture_output=True, text=True)
        return p.returncode, p.stdout, p.stderr, False
    except subprocess.TimeoutExpired as e:
        return None, _decode(e.stdout), _decode(e.stderr), True


# Fallback only (see parse_pytest_verbose): anchored on the trailing
# "VERDICT [ NN%]" pytest -v always appends, not on "no spaces in the node
# id" -- a parametrize id can contain spaces, which \S+::\S+ would fail to
# match. No greedy/non-greedy choice here is actually safe on its own: a
# parametrize id can contain a verdict word as a substring (greedy id-group
# needed to resolve that correctly), but a SKIPPED/XFAIL reason can *also*
# contain a verdict word as a substring (which a greedy id-group then
# mis-resolves the other way -- both directions confirmed by real review
# rounds). parse_pytest_verbose()'s known_ids path avoids this regex
# ambiguity entirely by matching against real, already-known node ids
# instead of guessing where id ends and verdict begins.
PYTEST_LINE = re.compile(r"^(.+?)\s+(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)\b.*?\s+\[\s*\d+%\]\s*$")
# \S+::.+ , not \S+::\S+: everything up to the first "::" is a path/dotted
# name (never contains a space), but a parametrize suffix after it can.
COLLECT_ONLY_LINE = re.compile(r"^(\S+::.+)$")
_VERDICT_ONLY = re.compile(r"^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)\b")


# XPASS (non-strict) means the assertion actually held -- treat it as PASSED.
# Strict XPASS already reports as literal FAILED and needs no mapping. XFAIL
# is an accepted, expected non-pass outcome like SKIPPED, not a suite defect.
_VERDICT_NORMALIZE = {"XPASS": "PASSED", "XFAIL": "SKIPPED"}


def parse_pytest_verbose(stdout, known_ids=None):
    """Parse pytest -v output into {node_id: status}.

    known_ids, when given, is matched as an exact line prefix instead of
    split out by PYTEST_LINE's regex heuristic -- a SKIPPED/XFAIL reason or
    a parametrize id can itself contain a real verdict word as a substring
    (e.g. a skip reason of "prior phase PASSED unexpectedly"), which no
    single greedy/non-greedy regex choice can reliably tell apart from the
    true trailing verdict in every case. Matching against the real,
    already-known node ids sidesteps the ambiguity entirely: every caller
    already has an id universe available (collect-only's expected_ids, or
    own_suite_baseline's passed_nodes) before it ever needs to parse a
    verdict line. Falls back to the regex heuristic only when no id
    universe is available at all (e.g. collection itself failed)."""
    results = {}
    if known_ids:
        # Longest first, in case one node id is a literal prefix of
        # another (e.g. differing only by an appended parametrize case).
        ordered = sorted(known_ids, key=len, reverse=True)
        for line in stdout.splitlines():
            stripped = line.strip()
            if "::" not in stripped:
                continue
            for node_id in ordered:
                # The whitespace-boundary test is what stops a node id from
                # claiming a longer sibling's line ("::test_a" vs
                # "::test_a2", "::test_a[case]") -- a bare startswith()
                # would mis-attribute both.
                if not (stripped.startswith(node_id) and (
                        len(stripped) == len(node_id) or stripped[len(node_id)].isspace())):
                    continue
                m = _VERDICT_ONLY.match(stripped[len(node_id):].strip())
                if not m:
                    # Prefix-matched but no verdict follows: this candidate
                    # isn't what the line is reporting (a bare node id in the
                    # warnings summary, or -- since a parametrize id may
                    # contain spaces -- a longer id that happens to span the
                    # shorter one's verdict word). Keep trying shorter
                    # candidates instead of dropping the line, or the id the
                    # line really belongs to reads as MISSING, which the
                    # mutation gate would score as a kill it never earned.
                    continue
                verdict = m.group(1)
                results[node_id] = _VERDICT_NORMALIZE.get(verdict, verdict)
                break
        return results
    for line in stdout.splitlines():
        m = PYTEST_LINE.match(line.strip())
        if m:
            verdict = m.group(2)
            results[m.group(1)] = _VERDICT_NORMALIZE.get(verdict, verdict)
    return results


def _pytest_base_args(py):
    return [py, "-m", "pytest", "--color=no", "-p", "no:cacheprovider"]


def _pytest_verbose_args():
    """Wins over whatever a submission's own pytest.ini/pyproject.toml/
    conftest.py sets via addopts. --verbosity=N (not -v/-q) SETS verbosity
    rather than adding to it -- verified empirically that addopts=-q
    silently cancels a plain -v, since verbosity is additive across every
    source, not just repeated CLI flags. --capture=fd similarly overrides
    an addopts=-s: -o console_output_style=progress alone still loses the
    "[ NN%]" suffix PYTEST_LINE needs when capture is disabled. The second
    -o closes the same hole for a config-file verbosity_test_cases
    override."""
    return ["--verbosity=1", "--capture=fd", "-o", "console_output_style=progress",
            "-o", "verbosity_test_cases=1", "--tb=short"]


def _collect_node_ids(py, installed, worktree, timeout=120):
    """Enumerate hidden-test node IDs independently of running them, so a
    node that never gets a verdict line (the run hangs, or the process dies
    partway through) can be told apart from a node that was never supposed
    to exist. --collect-only --verbosity=-1 prints one bare "path::test" per
    line and doesn't execute any test body, so it isn't subject to the same
    hang/crash risk as the real run -- guarded against anyway with its own
    shorter timeout. --verbosity=-1 (not -q) for the same non-additive
    reason _pytest_verbose_args() uses --verbosity=1."""
    rc, out, err, timed_out = run(
        _pytest_base_args(py) + ["--collect-only", "--verbosity=-1",
         "--continue-on-collection-errors"] + installed,
        cwd=worktree, timeout=timeout)
    ids = {line.strip() for line in out.splitlines()
           if COLLECT_ONLY_LINE.match(line.strip())}
    return ids, timed_out


def score_hidden_tests(worktree, task_dir, meta):
    """Copy hidden tests into the worktree, run them, then remove them
    again. Returns (results, detail): results is the per-node verdict map
    (contract §3 splits obligation scoring out of this function -- see
    score_obligations below); detail carries the fixed-denominator
    bookkeeping that used to live alongside a single fraction here.

    The removal matters: every check that runs after this one (own-suite
    baseline, the outside-root suite-health check, the mutation gate) runs
    `pytest tests/` against whatever is sitting in the worktree's tests/
    directory. Leaving the hidden tests there would make those checks score
    the hidden tests' ability to catch a mutation instead of the model's
    own tests' -- silently inflating test_adequacy on every trial, since
    the hidden tests are comprehensive by construction. Caught in this
    repo's own harness-validation smoke test: the mutation kill rate read
    19/19 with the hidden tests still present and 17/19 once this cleanup
    was added, against the same reference submission.
    """
    hidden_paths = [os.path.join(task_dir, p) for p in meta["hidden_tests"]]
    installed = []
    installed_rel = []
    for hp in hidden_paths:
        dest = os.path.join(worktree, "tests", os.path.basename(hp))
        shutil.copy(hp, dest)
        installed.append(dest)
        # Relative to worktree, not the absolute dest: both pytest calls
        # below run with cwd=worktree already, and an absolute argument
        # risks pytest resolving node ids against a different rootdir than
        # a relative one would (observed directly under a symlinked path
        # like macOS's /tmp -> /private/tmp; real trial worktrees live
        # inside the repo tree so this never triggers there, but a relative
        # argument removes the dependency on that entirely).
        installed_rel.append(os.path.join("tests", os.path.basename(hp)))

    try:
        py = sys.executable
        # A fixed, submission-independent expected node count: without
        # this, a submission whose own code hangs or crashes pytest
        # partway through the hidden suite would have the tests it never
        # reached silently excluded from the denominator (results only
        # ever contains nodes that produced a verdict line) rather than
        # scored as failed -- so dying early could outscore running to
        # completion and failing honestly.
        expected_ids, collect_timed_out = _collect_node_ids(py, installed_rel, worktree)
        # Without this flag, a collection error in ANY one hidden-test file
        # (e.g. a broken import in test_hB.py) aborts the whole pytest
        # session by default, silently zeroing out an unrelated file's
        # already-correct results (e.g. test_hA.py) too.
        rc, out, err, timed_out = run(
            _pytest_base_args(py) + _pytest_verbose_args() +
            ["--continue-on-collection-errors"] + installed_rel,
            cwd=worktree, timeout=600)
    finally:
        for dest in installed:
            if os.path.exists(dest):
                os.remove(dest)

    results = parse_pytest_verbose(out, expected_ids)
    # Fall back to what actually produced a verdict only if collection
    # itself didn't yield a usable expected set (e.g. it also timed out) --
    # the previous, weaker behavior, not a new failure mode.
    missing = sorted(expected_ids - set(results)) if expected_ids else []
    for node_id in missing:
        results[node_id] = "MISSING"
    passed = sum(1 for v in results.values() if v == "PASSED")
    total = len(expected_ids) if expected_ids else len(results)
    return results, {
        "total": total, "passed": passed,
        "failed": [k for k, v in results.items() if v != "PASSED"],
        "missing": missing, "collect_timed_out": collect_timed_out,
        "timed_out": timed_out, "raw_tail": out[-4000:], "stderr_tail": err[-2000:],
    }


def score_obligations(results, obligations, weighting):
    """Contract §3: correctness is the equally-weighted mean over the task's
    declared acceptance-obligation groups, each scored as the fraction of its
    own hidden-test nodes that pass -- 0.0, never skipped, when a group
    collected no nodes at all (an import failure must not shrink the
    denominator -- the same principle as score_hidden_tests' fixed
    denominator above).

    Mapping rule for a collected node N against an obligation's declared
    entry E: N == E or N.startswith(E + "["); entries never carry
    parametrize suffixes themselves. A collected node that maps to zero or
    more than one obligation is a loud grading failure (contract §2) --
    raised here as ValueError, which main() turns into a diagnostic dump and
    a return 1. A declared entry that never matches any collected node is
    NOT a failure here: that's a legitimate submission failure (its import
    broke) and the affected group just scores 0.0. The bidirectional check
    (every declared entry also matches something) belongs to
    validate_obligations.py, not to per-trial grading.
    """
    if weighting != "equal":
        raise ValueError(f"unsupported correctness.obligation_weighting: {weighting!r}")

    membership = {ob["id"]: [] for ob in obligations}
    for node_id in results:
        matches = [ob["id"] for ob in obligations
                   if any(node_id == entry or node_id.startswith(entry + "[")
                          for entry in ob["tests"])]
        if len(matches) != 1:
            raise ValueError(f"hidden-test node {node_id!r} maps to {len(matches)} acceptance "
                              f"obligations (expected exactly 1): {matches}")
        membership[matches[0]].append(node_id)

    detail = []
    fractions = []
    for ob in obligations:
        nodes = membership[ob["id"]]
        collected = len(nodes)
        passed = sum(1 for n in nodes if results[n] == "PASSED")
        fraction = (passed / collected) if collected else 0.0
        detail.append({"id": ob["id"], "passed": passed, "collected": collected,
                        "fraction": fraction, "uncollected": collected == 0,
                        "failed_nodes": sorted(n for n in nodes if results[n] != "PASSED")})
        fractions.append(fraction)

    correctness = sum(fractions) / len(fractions) if fractions else 0.0
    return correctness, detail


def _suite_args(py):
    """Shared by the baseline and every mutation run, so both see the same
    node universe. Hardcoded, not meta.yaml's `own_suite_command` -- see
    _pytest_verbose_args() for why. --continue-on-collection-errors must
    apply to mutation runs too: without it, one broken test file would
    abort every mutation run into zero verdict lines, i.e. every
    baseline-passing node reads as killed -- a free perfect score for a
    broken submission."""
    return (_pytest_base_args(py) + _pytest_verbose_args() +
            ["tests/", "--continue-on-collection-errors"])


def own_suite_baseline(worktree):
    py = sys.executable
    expected_ids, collect_timed_out = _collect_node_ids(py, ["tests/"], worktree)
    rc, out, err, timed_out = run(_suite_args(py), cwd=worktree, timeout=900)
    parsed = parse_pytest_verbose(out, expected_ids)
    # Tests were collected but nothing parsed (and it didn't time out) means
    # PYTEST_LINE stopped matching pytest's real output -- main() fails the
    # grade loudly on this rather than silently record a zeroed baseline.
    unparsable = bool(expected_ids) and not parsed and not timed_out
    missing = sorted(expected_ids - set(parsed)) if expected_ids else []
    for node_id in missing:
        parsed[node_id] = "MISSING"
    # SKIPPED is neither: it gives mutation_gate no kill signal (excluded
    # from passed_nodes) but isn't a hygiene defect either (pytest itself
    # returns 0 for a skip-only suite), so it's excluded from failed_nodes.
    passed_nodes = sorted(k for k, v in parsed.items() if v == "PASSED")
    failed_nodes = sorted(k for k, v in parsed.items() if v not in ("PASSED", "SKIPPED"))
    return {"returncode": rc, "timed_out": timed_out, "passed_clean": rc == 0,
            "passed_nodes": passed_nodes, "failed_nodes": failed_nodes,
            "unparsable": unparsable, "collect_timed_out": collect_timed_out,
            "tail": out[-3000:]}


def ships_red_outside_root(worktree):
    """report 04's §7.4 gate #1: run the own suite once from outside the repo
    root. Catches CWD-relative subprocess/path assumptions in the model's
    own tests that a run from the repository root would never expose.

    Only rc == 0 counts as green. run() reports a timeout as rc None, and a
    suite that passes at the root but hangs from outside it is exactly the
    defect this check exists to find -- treating that as "not red" handed the
    submission full hygiene credit for a real portability failure."""
    py = sys.executable
    outside = tempfile.mkdtemp(prefix="ai-agent-bench-outside-")
    tests_dir = os.path.join(worktree, "tests")
    rc, out, err, timed_out = run([py, "-m", "pytest", "-q", tests_dir],
                                   cwd=outside, timeout=900)
    shutil.rmtree(outside, ignore_errors=True)
    return {"ships_red_outside_root": rc != 0, "returncode": rc,
            "timed_out": timed_out, "tail": out[-2000:]}


def load_mutations(task_dir, meta):
    mut_list_path = os.path.join(task_dir, meta["mutations_file"])
    with open(mut_list_path) as f:
        return [line.strip() for line in f if line.strip()]


def mutation_gate(worktree, task_dir, meta, baseline_passed_nodes):
    """A mutation is "killed" only by a node in `baseline_passed_nodes`
    (own_suite_baseline()'s passed set, restricted by main() to the task's
    authorized test path before this is called -- contract §6) that stops
    being PASSED under it -- FAILED, ERROR, or missing entirely. A node
    already broken at baseline gives no signal either way, and SKIPPED must
    never count as a kill."""
    mut_dir = os.path.join(task_dir, "mutations")
    mutations = load_mutations(task_dir, meta)

    py = sys.executable
    pytest_args = _suite_args(py)

    results = {}
    for mut in mutations:
        env = dict(os.environ)
        env["PYTHONPATH"] = mut_dir + os.pathsep + env.get("PYTHONPATH", "")
        env["MUTATION"] = mut
        rc, out, err, timed_out = run(pytest_args, cwd=worktree, env=env, timeout=180)
        if timed_out:
            results[mut] = "timeout"
        elif rc is None:
            results[mut] = "error"
        else:
            nodes = parse_pytest_verbose(out, baseline_passed_nodes)
            flipped = {n for n in baseline_passed_nodes if nodes.get(n) not in ("PASSED", "SKIPPED")}
            results[mut] = "kill" if flipped else "survive"

    killed = sum(1 for v in results.values() if v == "kill")
    # Divide by every configured mutation, not just the resolved kill/survive
    # ones -- a timeout/error must count as a non-kill, not shrink the
    # denominator (mirrors this file's own correctness-denominator fix).
    fraction = (killed / len(mutations)) if mutations else 0.0
    return fraction, {"per_mutation": results, "killed": killed, "total": len(mutations),
                       "baseline_passed_count": len(baseline_passed_nodes)}


# Dropped into every worktree by run_trial.py so the model can read its
# task; never part of the model's own submission. Left in, it reads as a
# scope violation and crowds out the real diff from the judge's truncated
# prompt budget.
HARNESS_ARTIFACTS_PATHSPEC = ["--", ".", ":(exclude)TASK.md"]


def scope_discipline(worktree, before_head, meta, rubric):
    """Contract §5: fixed per-file penalties, independent of authorized diff
    size, plus an "integrity" class for changes to something the grading
    process itself depends on (grader inputs, hidden-test mechanisms, and
    every frozen_unchanged path under tests/) -- distinct from an ordinary
    unauthorized file, and zeroing the whole category outright."""
    # --no-renames: git's default rename detection would otherwise report only
    # the destination path for an exact rename, hiding that a frozen source
    # file was deleted (e.g. renaming a frozen test onto an authorized name).
    # Forcing the delete+add pair keeps both endpoints visible to the checks
    # below.
    rc, out, err, _ = run(["git", "diff", "--name-only", "--no-renames", before_head]
                           + HARNESS_ARTIFACTS_PATHSPEC, cwd=worktree)
    changed = [line for line in out.splitlines() if line.strip()]
    authorized = set(meta.get("authorized_surface", []))
    frozen = set(meta.get("frozen_unchanged", []))
    cfg = rubric["scope"]
    frozen_tests = {p for p in frozen if p.startswith("tests/")} if cfg["integrity_includes_frozen_tests"] else set()
    integrity_paths = cfg["integrity_paths"]

    violations = []
    for p in changed:
        if p in authorized:
            continue
        if p in frozen_tests or any(fnmatch.fnmatch(p, pat) for pat in integrity_paths):
            violations.append({"path": p, "class": "integrity"})
        else:
            # Includes frozen *source* files: only grader inputs, hidden-test
            # mechanisms, and frozen tests are integrity paths -- a frozen
            # source file touched outside authorized_surface is an ordinary
            # unauthorized-file violation, not an integrity one.
            violations.append({"path": p, "class": "unauthorized"})
    violations.sort(key=lambda v: v["path"])

    integrity_violations = [v["path"] for v in violations if v["class"] == "integrity"]
    out_of_scope = [v["path"] for v in violations if v["class"] == "unauthorized"]
    frozen_touched = [f for f in changed if f in frozen]

    if not changed:
        fraction = 1.0  # unreachable in practice: no_submission fires first
    elif integrity_violations:
        fraction = 0.0
    else:
        fraction = max(0.0, 1.0 - cfg["unauthorized_file_penalty"] * len(out_of_scope))

    return fraction, {"changed_files": changed, "violations": violations,
                       "integrity_violations": integrity_violations, "out_of_scope": out_of_scope,
                       "frozen_touched": frozen_touched, "penalty_per_file": cfg["unauthorized_file_penalty"]}


_HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def _changed_line_ranges(worktree, before_head, path):
    """New-file line numbers added or modified by the diff for `path`, read
    from a -U0 unified diff's hunk headers (no surrounding context lines to
    mistake for real changes)."""
    rc, out, err, _ = run(["git", "diff", "--no-renames", "-U0", before_head, "--", path],
                           cwd=worktree)
    lines = set()
    for line in out.splitlines():
        m = _HUNK_HEADER.match(line)
        if not m:
            continue
        start = int(m.group(1))
        count = int(m.group(2)) if m.group(2) is not None else 1
        if count:  # count == 0 is a pure deletion hunk -- no new-file lines
            lines.update(range(start, start + count))
    return lines


def resolve_ruff(rubric):
    """Contract §7: resolve the ruff binary actually on PATH and its real
    version, so a mismatch against rubric.yaml's pinned version can be
    reported loudly rather than silently scoring under a different ruleset.
    An unpinned evaluator would lint every future submission under whatever
    ruleset happened to be installed that day."""
    pinned = rubric["hygiene"]["ruff"]["version"]
    # The interpreter's own bin/ first, PATH only as a fallback: this script
    # runs under the evaluator venv's python, but that venv is not necessarily
    # *activated*, so a bare `which ruff` can resolve a system-wide ruff of a
    # different version than requirements.txt pinned. Caught for real the
    # first time this check ran (venv 0.16.5 vs a homebrew 0.16.0 on PATH).
    beside = os.path.join(os.path.dirname(sys.executable), "ruff")
    path = beside if os.path.exists(beside) else shutil.which("ruff")
    if path is None:
        return None, None, pinned
    rc, out, err, _ = run([path, "--version"])
    m = re.match(r"ruff (\S+)", out.strip())
    return path, (m.group(1) if m else None), pinned


def lint_diff(worktree, before_head, root, rubric, ruff_path):
    """Only findings on lines the diff actually touched -- a pre-existing
    finding in a file the model merely edited elsewhere must not count
    against it. Returns (findings_count, detail).

    Lint is never "unavailable but still scored": main() refuses to grade at
    all unless the pinned ruff is on PATH (contract §7), and a ruff that then
    misbehaves raises here rather than handing back a free 10 points under an
    unknown ruleset."""
    rc, out, err, _ = run(["git", "diff", "--name-only", "--no-renames", before_head], cwd=worktree)
    py_files = [line for line in out.splitlines() if line.strip().endswith(".py")]
    if not py_files:
        return 0, {"note": "no changed .py files", "findings_count": 0,
                    "findings": [], "all_findings_count": 0}

    config_abs = os.path.join(root, rubric["hygiene"]["ruff"]["config"])
    # --config is what stops a submission's own pyproject.toml/ruff.toml from
    # changing the policy it is graded under -- do NOT add --isolated, it
    # would ignore --config too.
    rc, out, err, _ = run([ruff_path, "check", "--quiet", "--no-cache", "--config", config_abs,
                           "--output-format=json"] + py_files, cwd=worktree)
    # ruff's own documented exit codes: 0 = clean, 1 = findings reported --
    # both are real results. Anything else (bad config, crash) is a tool
    # failure and must not silently read as "0 findings, perfect hygiene".
    if rc not in (0, 1):
        raise ValueError(f"ruff exited {rc} under the pinned config {config_abs} "
                          f"(stderr tail: {err[-500:]!r})")
    try:
        all_findings = json.loads(out) if out.strip() else []
    except Exception:
        raise ValueError(f"ruff produced unparsable JSON under the pinned config "
                          f"{config_abs} (stdout tail: {out[-500:]!r})") from None

    changed_ranges = {f: _changed_line_ranges(worktree, before_head, f) for f in py_files}
    real_worktree = os.path.realpath(worktree)

    def _touches_diff(f):
        # realpath both sides: ruff resolves symlinks in its reported
        # filename (e.g. macOS /tmp -> /private/tmp), worktree may not be.
        rel = os.path.relpath(os.path.realpath(f.get("filename", "")), real_worktree)
        rows = changed_ranges.get(rel)
        row = (f.get("location") or {}).get("row")
        # Start-line attribution only (contract §7): no end_location span
        # scan any more -- that re-admitted a pre-existing multiline finding
        # whenever a later line inside the same span was touched.
        return bool(rows) and row is not None and row in rows

    findings = [f for f in all_findings if _touches_diff(f)]
    lines = [f"{os.path.relpath(os.path.realpath(f['filename']), real_worktree)}:"
             f"{f['location']['row']}:{f['location']['column']}: {f['code']} {f['message']}"
             for f in findings]
    return len(findings), {"findings_count": len(findings), "findings": lines[:50],
                            "all_findings_count": len(all_findings)}


def hygiene(root, worktree, before_head, rubric, ruff_path, baseline, outside):
    """Contract §7's suite-health composition: differential lint findings and
    whether the own suite runs green, both at the repository root and from
    outside it."""
    findings_count, lint_detail = lint_diff(worktree, before_head, root, rubric, ruff_path)
    # A file that fails during collection contributes no node to
    # failed_nodes at all (collect-only and -v both just never see it),
    # so a suite that's red purely from a collection error would
    # otherwise charge nothing here -- floor it at one defect.
    baseline_failing = max(len(baseline["failed_nodes"]), 0 if baseline["passed_clean"] else 1)
    if baseline["passed_clean"] and outside["ships_red_outside_root"]:
        # Only charge hygiene for ships_red_outside_root when the baseline was
        # otherwise clean -- a baseline already red at the root makes the
        # outside-root run red too and confirms nothing new, so charging
        # hygiene as well as test_adequacy would double-penalize one defect.
        fraction = 0.0
        detail = dict(lint_detail, ships_red_outside_root=True, baseline_failing_nodes=baseline_failing)
    else:
        # test_adequacy now gives partial mutation credit even with a red
        # own suite, so "the suite runs clean" needs its own consequence
        # somewhere -- charge it here, on the same decay curve as lint
        # findings, proportional rather than all-or-nothing.
        k = rubric["hygiene"]["penalty_per_defect"]
        fraction = 1.0 / (1.0 + k * (findings_count + baseline_failing))
        detail = dict(lint_detail, baseline_failing_nodes=baseline_failing)
    return fraction, detail


def _extract_json_object(text):
    """Find and parse the first {...} object in free-form model output."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return {}
    try:
        return json.loads(text[start:end + 1])
    except Exception:
        return {}


MAX_JUDGE_ATTEMPTS = 3


def _validate_judge_score(v, valid_scores):
    """Contract §8: accept a value only when it is an int/float (never a
    bool -- isinstance(True, int) is True in Python, so a stray true/false
    must be excluded explicitly or it would silently parse as 1/0),
    integral, and inside rubric.yaml's valid_scores. Anything else is an
    unparsed category and triggers the retry, exactly like a missing key."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    if isinstance(v, float) and not v.is_integer():
        return None
    v_int = int(v)
    return v_int if v_int in valid_scores else None


def _map_judge_score(v_int, valid_scores, score_map):
    """Contract §8: shifted maps the worst observable score to zero credit
    instead of a silent floor; linear is the only other accepted mapping.
    Anything else is a rubric misconfiguration -- validate_judge_config()
    already rejects it before any trial work starts, so this function should
    never actually see a third value in practice."""
    lo, hi = min(valid_scores), max(valid_scores)
    if score_map == "shifted":
        return (v_int - lo) / (hi - lo)
    if score_map == "linear":
        return v_int / hi
    raise ValueError(f"unsupported judge.score_map: {score_map!r}")


def render_judge_diff(worktree, before_head, max_chars):
    """Contract §8: deterministic per-file diff rendering, replacing a flat
    diff[:N] truncation that could drop an entire late-sorting file's diff
    without a trace. No file is ever dropped, and the same diff always
    produces the same prompt."""
    rc, out, err, _ = run(["git", "diff", "--name-only", "--no-renames", before_head]
                           + HARNESS_ARTIFACTS_PATHSPEC, cwd=worktree)
    paths = sorted(line for line in out.splitlines() if line.strip())
    per_file = {}
    for p in paths:
        _, d, _, _ = run(["git", "diff", "--no-renames", before_head, "--", p], cwd=worktree)
        per_file[p] = d

    total = sum(len(d) for d in per_file.values())
    if total <= max_chars:
        return "".join(per_file[p] for p in paths)

    # Fair allocation: repeatedly shrink the per-file budget to what's left
    # over unsettled files, letting any file that already fits inside that
    # budget keep its full text and release its unused share to the rest.
    # Repeat until nothing new settles at the current budget.
    settled = {}
    unsettled = set(paths)
    remaining_chars = max_chars
    budget = 0
    while unsettled:
        budget = remaining_chars // len(unsettled)
        newly_settled = [p for p in unsettled if len(per_file[p]) <= budget]
        if not newly_settled:
            break
        for p in newly_settled:
            settled[p] = per_file[p]
            remaining_chars -= len(per_file[p])
            unsettled.discard(p)

    parts = []
    for p in paths:
        if p in settled:
            parts.append(settled[p])
        else:
            full = per_file[p]
            kept = full[:budget]
            truncated_chars = len(full) - len(kept)
            parts.append(kept + f"\n[... truncated {truncated_chars} of {len(full)} "
                                 f"characters from {p} ...]\n")
    return "".join(parts)


def judge_prompt_path(root, rubric):
    cfg = rubric.get("judge", {})
    return os.path.join(root, "eval", "harness", cfg.get("prompt_template", "judge_prompt.md"))


def run_judge(root, worktree, before_head, rubric, categories, meta):
    """Returns (scores, detail, status).

    status: "no_judge_configured" (rubric.yaml has no judge.model -- a
    static, report-wide condition, safe to renormalize over) vs "ok" (every
    category parsed) vs "failed" (judge ran but never parsed after retrying
    -- looks identical to "no_judge_configured" in the scores dict alone, but
    must NOT be renormalized: a trial silently missing rubric weight isn't
    comparable to a fully-scored one, and needs investigation, not a
    quietly smaller total). Partial success across attempts (e.g. one
    category parses on attempt 1, another only on attempt 2) still counts as
    "failed" if no single attempt scored every category -- a category's
    score should come from one coherent judgement, not be stitched together.
    """
    judge_cfg = rubric.get("judge", {})
    model = judge_cfg.get("model")
    if not model:
        return ({c: None for c in categories},
                {"note": "no judge model configured in rubric.yaml"}, "no_judge_configured")
    harness = judge_cfg["harness"]
    effort = judge_cfg.get("effort")
    valid_scores = judge_cfg["valid_scores"]
    score_map = judge_cfg["score_map"]

    diff = render_judge_diff(worktree, before_head, judge_cfg["max_diff_chars"])
    prompt_path = judge_prompt_path(root, rubric)
    # No embedded fallback: silently judging under a different, unversioned
    # prompt would change the scoring instrument without changing the prompt
    # hash recorded in provenance, so those scores would then be mixed with
    # real ones.
    if not os.path.exists(prompt_path):
        raise ValueError(f"judge.prompt_template does not exist: {prompt_path}")
    with open(prompt_path) as f:
        template = f.read()
    judge_context = meta.get("judge_context", "").strip()
    # {{JUDGE_CONTEXT}} sits directly against "DIFF:" in the template (no
    # blank line of its own) so an empty judge_context renders byte-identical
    # to a prompt with no context block at all.
    context_block = f"Task-specific context (read before scoring):\n{judge_context}\n\n" if judge_context else ""
    prompt = template.replace("{{JUDGE_CONTEXT}}", context_block).replace("{{DIFF}}", diff)

    attempts = []
    for attempt in range(1, MAX_JUDGE_ATTEMPTS + 1):
        cmd, extra_env, cwd = build_command(harness, prompt, model, effort, worktree)
        env = {**os.environ, **extra_env} if extra_env else None
        rc, out, err, timed_out = run(cmd, cwd=cwd, env=env, timeout=600)
        if harness == "opencode":
            # opencode --format json emits a stream of JSON events; take the
            # last text payload and parse a JSON object out of it.
            try:
                text = out.strip().splitlines()[-1] if out.strip() else "{}"
                obj = json.loads(text)
                parsed = _extract_json_object(obj.get("text", "") if isinstance(obj, dict) else "")
            except Exception:
                parsed = {}
        elif harness == "claude":
            # claude's stream-json output (harnesses.py) ends with a
            # "result" event wrapping the actual reply alongside usage/cost
            # metadata -- unwrap it first, or _extract_json_object grabs
            # that whole envelope instead of the judge's {..} score object
            # (it has no "readability"/"maintainability" keys of its own, so
            # every attempt would silently fail to parse).
            try:
                text = out.strip().splitlines()[-1] if out.strip() else "{}"
                obj = json.loads(text)
                parsed = _extract_json_object(obj.get("result", "") if isinstance(obj, dict) else "")
            except Exception:
                parsed = {}
        else:
            # Every other supported harness prints its final response as
            # plain text on stdout -- pull the JSON object out of that
            # directly.
            parsed = _extract_json_object(out)

        scores = {}
        for c in categories:
            v = _validate_judge_score(parsed.get(c), valid_scores)
            scores[c] = _map_judge_score(v, valid_scores, score_map) if v is not None else None
        # rc/stderr distinguish a parse hiccup (stdout has content) from a
        # hard invocation failure (bad model id, auth, rate limit).
        attempts.append({"attempt": attempt, "returncode": rc, "raw": out[-2000:],
                          "stderr_tail": err[-2000:], "parsed": parsed, "timed_out": timed_out})
        if all(scores[c] is not None for c in categories):
            return scores, {"attempts": attempts, "judge_context": judge_context}, "ok"

    return ({c: None for c in categories},
            {"attempts": attempts, "judge_context": judge_context}, "failed")


def validate_profile(rubric, profile_name):
    """Contract §2: a missing/unknown profile, an unknown category id in
    weights/gates, a category in both weights and gates, or a non-gated
    category missing from weights are all loud grading failures rather than
    a silent fallback or renormalization. Returns the resolved profile dict;
    raises ValueError otherwise (caught by main() as a loud grading
    failure)."""
    profiles = rubric.get("profiles", {})
    if profile_name is None or profile_name not in profiles:
        raise ValueError(f"meta.yaml names an unknown or missing rubric_profile: {profile_name!r}")
    profile = profiles[profile_name]
    category_ids = {c["id"] for c in rubric["categories"]}
    weights = profile.get("weights", {})
    gates = profile.get("gates", {})

    unknown = (set(weights) | set(gates)) - category_ids
    if unknown:
        raise ValueError(f"profile {profile_name!r} references unknown category ids: {sorted(unknown)}")
    both = set(weights) & set(gates)
    if both:
        raise ValueError(f"profile {profile_name!r} has categories in both weights and gates: {sorted(both)}")
    missing = category_ids - set(weights) - set(gates)
    if missing:
        raise ValueError(f"profile {profile_name!r} is missing weights for non-gated categories: {sorted(missing)}")
    return profile


# The categories this grader knows how to compute, and the one it evaluates
# before the gate point. Category ids are the grader's contract with the
# rubric: evidence (hidden tests, mutations, the diff, lint) has to bind to
# a specific id somewhere. That binding is checked rather than assumed, so
# renaming a category in YAML fails loudly instead of silently deleting its
# weight from every future score.
_COMPUTED_CATEGORIES = {"correctness", "test_adequacy", "scope_discipline",
                        "hygiene", "readability", "maintainability"}
_PRE_GATE_CATEGORIES = {"correctness"}


def validate_categories(rubric, gates):
    declared = {c["id"] for c in rubric["categories"]}
    if declared != _COMPUTED_CATEGORIES:
        raise ValueError(
            f"rubric.yaml declares categories {sorted(declared)} but this grader computes "
            f"{sorted(_COMPUTED_CATEGORIES)}; adding or renaming a category needs a grader "
            f"change, not only a rubric change")
    ungateable = set(gates) - _PRE_GATE_CATEGORIES
    if ungateable:
        raise ValueError(
            f"profile gates {sorted(ungateable)}, but gates are evaluated straight after "
            f"correctness and before any other category is computed; only "
            f"{sorted(_PRE_GATE_CATEGORIES)} can be gated")


def validate_judge_config(rubric):
    """Contract §8: score_map is a fixed, closed vocabulary (shifted or
    linear). A third value is a rubric misconfiguration, not a per-attempt
    judge parse failure, so it fails the grade immediately rather than
    after a slow trial run."""
    judge_cfg = rubric.get("judge", {})
    if not judge_cfg.get("model"):
        return
    score_map = judge_cfg.get("score_map")
    if score_map not in ("shifted", "linear"):
        raise ValueError(f"unsupported judge.score_map: {score_map!r}")
    policy = judge_cfg.get("same_model_policy")
    if policy != "flag_and_separate":
        raise ValueError(
            f"unsupported judge.same_model_policy: {policy!r}. Only 'flag_and_separate' is "
            f"implemented (record the flag, withhold the judged and composite columns from "
            f"comparison); a different policy needs a grader and aggregator change.")


def _same_model(judge_model, trial_model):
    """Is the judge scoring its own submission? Compared on the bare model id:
    every harness spells the same model differently (`--model` is passed in
    whatever form that CLI expects), so opencode's "anthropic/claude-opus-5"
    and the rubric's "claude-opus-5" are the same model and must not escape
    the withholding policy on a raw string mismatch."""
    if not judge_model or not trial_model:
        return False
    return judge_model.rsplit("/", 1)[-1].strip().lower() == \
        trial_model.rsplit("/", 1)[-1].strip().lower()


def evaluate_gates(gates, category_scores):
    """Contract §4: no gates -> not_applicable. Every gated category's score
    must meet its threshold to pass; a missing score counts as a failure
    rather than a silent pass."""
    if not gates:
        return "not_applicable", []
    failed = []
    for cid, threshold in gates.items():
        score = category_scores.get(cid)
        if score is None or score < threshold:
            failed.append({"category": cid, "score": score, "threshold": threshold})
    return ("failed" if failed else "passed"), failed


def weighted_score(category_ids, weights, category_scores):
    """Contract §4 arithmetic: weighted mean over `category_ids`, rescaled to
    the rubric's 0-100 scale, using only categories that carry both a weight
    (gated categories are absent from `weights` by construction) and a
    score. Returns (score_or_None, ws) so callers can also derive
    scored_weight_fraction from ws."""
    ws = sum(weights[c] for c in category_ids
             if weights.get(c) is not None and category_scores.get(c) is not None)
    if not ws:
        return None, 0.0
    total = sum(weights[c] * category_scores[c] for c in category_ids
                if weights.get(c) is not None and category_scores.get(c) is not None)
    return round(100.0 * total / ws, 1), ws


def _sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


# Distribution names as published to PyPI (case matters to some
# importlib.metadata versions -- PyYAML is not "pyyaml").
_DEP_DIST_NAMES = {"numpy": "numpy", "scipy": "scipy", "h5py": "h5py",
                   "pytest": "pytest", "pyyaml": "PyYAML"}


def _dependency_versions():
    out = {}
    for key, dist in _DEP_DIST_NAMES.items():
        try:
            out[key] = importlib.metadata.version(dist)
        except importlib.metadata.PackageNotFoundError:
            out[key] = None
    return out


def build_provenance(root, rubric, rubric_bytes, manifest, meta, task_dir,
                      ruff_version, ruff_pinned, judge_status, judge_same_model):
    """Contract §1/§9: everything needed to tell whether two run records are
    even comparable (same rubric bytes, same task contract bytes, same
    grader code) before any score is compared."""
    judge_cfg = rubric.get("judge", {})
    prompt_path = judge_prompt_path(root, rubric)
    prompt_sha = None
    if os.path.exists(prompt_path):
        with open(prompt_path, "rb") as f:
            prompt_sha = _sha256_bytes(f.read())

    # task_contract_sha256: sha256 over spec.md bytes then meta.yaml bytes,
    # concatenated -- either file changing (an ambiguity fix to spec.md, a
    # reweighted acceptance_obligations entry) must change the cohort a
    # record belongs to.
    spec_path = os.path.join(task_dir, meta.get("spec", "spec.md"))
    meta_path = os.path.join(task_dir, "meta.yaml")
    contract_bytes = b""
    if os.path.exists(spec_path):
        with open(spec_path, "rb") as f:
            contract_bytes += f.read()
    with open(meta_path, "rb") as f:
        contract_bytes += f.read()

    rc, out, err, _ = run(["git", "rev-parse", "HEAD"], cwd=root)
    grader_git_rev = out.strip() if rc == 0 else None
    rc2, out2, err2, _ = run(["git", "status", "--porcelain"], cwd=root)
    grader_git_dirty = bool(out2.strip()) if rc2 == 0 else None

    return {
        "rubric_version": rubric.get("version"),
        "rubric_sha256": _sha256_bytes(rubric_bytes),
        "rubric_profile": meta.get("rubric_profile"),
        "task_contract_sha256": _sha256_bytes(contract_bytes),
        "grader_git_rev": grader_git_rev,
        "grader_git_dirty": grader_git_dirty,
        "baseline_ref": manifest.get("baseline_ref"),
        # The resolved commit, not just the symbolic ref: `frozen-substrate`
        # could be re-cut, and two trials from different substrates must not
        # aggregate together. This is part of aggregate.py's cohort key.
        "baseline_commit": manifest.get("before_head"),
        "python_version": platform.python_version(),
        "ruff_version": ruff_version,
        "ruff_version_pinned": ruff_pinned,
        "ruff_config": rubric["hygiene"]["ruff"]["config"],
        "dependency_versions": _dependency_versions(),
        "judge": {"model": judge_cfg.get("model"), "harness": judge_cfg.get("harness"),
                  "effort": judge_cfg.get("effort"), "prompt_sha256": prompt_sha,
                  "status": judge_status, "same_model": judge_same_model},
    }


def _fail_loud(root, run_id, reason, diagnostic=None):
    """Contract §2: write a diagnostic JSON, print a loud ERROR to stderr
    saying no record was written, and return 1. Reused by every loud
    grading failure (profile/gate misconfiguration, judge score_map
    misconfiguration, an unmapped or multiply-mapped hidden-test node) as
    well as the pre-existing unparsable own-suite-baseline case -- same
    convention throughout, one place that writes it."""
    diag_dir = os.path.join(root, "eval", "results", "tmp", "grading_failures")
    os.makedirs(diag_dir, exist_ok=True)
    diag_path = os.path.join(diag_dir, f"{run_id}.json")
    with open(diag_path, "w") as f:
        json.dump({"run_id": run_id, "reason": reason, **(diagnostic or {})}, f, indent=2, default=str)
    print(f"[grade_trial] ERROR: {reason}. No run record was written. "
          f"Diagnostic: {diag_path}", file=sys.stderr)
    return 1


def _write_and_report(root, manifest, rubric, record):
    results_dir = os.path.join(root, "eval", "results", "runs")
    os.makedirs(results_dir, exist_ok=True)
    out_path = os.path.join(results_dir, f"{manifest['run_id']}.json")
    with open(out_path, "w") as f:
        json.dump(record, f, indent=2, default=str)

    report_dir = os.path.join(root, "eval", "results", "reports")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f"{manifest['run_id']}.md")
    write_report(report_path, record, rubric)

    print(f"[grade_trial] deterministic_score={record['deterministic_score']} "
          f"composite_score={record['composite_score']} "
          f"(scored {record['scored_weight_fraction']*100:.0f}% of profile weight)")
    print(f"[grade_trial] record: {out_path}")
    print(f"[grade_trial] report: {report_path}")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", required=True)
    args = ap.parse_args()

    root = repo_root()
    with open(args.manifest) as f:
        manifest = json.load(f)
    task_dir = os.path.join(root, "eval", "tasks", manifest["task_id"])
    with open(os.path.join(task_dir, "meta.yaml"), "rb") as f:
        meta_bytes = f.read()
    meta = yaml.safe_load(meta_bytes)
    with open(os.path.join(root, "eval", "rubric.yaml"), "rb") as f:
        rubric_bytes = f.read()
    rubric = yaml.safe_load(rubric_bytes)

    ruff_path, ruff_version, ruff_pinned = resolve_ruff(rubric)
    try:
        profile = validate_profile(rubric, meta.get("rubric_profile"))
        validate_categories(rubric, profile.get("gates", {}))
        validate_judge_config(rubric)
        # Checked up front, before the mutation gate burns minutes: grading a
        # submission under a ruff other than the pinned one silently changes
        # what hygiene means, and scoring it anyway would hand out the
        # category's full weight with no lint coverage behind it.
        if ruff_path is None or ruff_version != ruff_pinned:
            raise ValueError(
                f"graded lint requires ruff {ruff_pinned} (rubric.yaml's "
                f"hygiene.ruff.version) but found "
                f"{ruff_version or 'no ruff on PATH'} -- install the pinned version, "
                f"or change the pin deliberately and treat it as a rubric change")
    except ValueError as e:
        return _fail_loud(root, manifest["run_id"], str(e))

    weights = profile.get("weights", {})
    gates = profile.get("gates", {})
    automated_ids = [c["id"] for c in rubric["categories"] if c["kind"] == "automated"]
    judged_ids = [c["id"] for c in rubric["categories"] if c["kind"] == "judged"]

    worktree = manifest["worktree_path"]
    before_head = manifest["before_head"]

    # Defensive: run_trial.py already stages everything so untracked new
    # files (e.g. merger_rate.py itself) are visible to `git diff`, but this
    # script must be safe to run standalone against a hand-built manifest too.
    run(["git", "add", "-A"], cwd=worktree)

    record = {"run_id": manifest["run_id"], "task_id": manifest["task_id"],
              "model": manifest["model"], "harness": manifest["harness"],
              "effort": manifest.get("effort"), "baseline_ref": manifest.get("baseline_ref"),
              "duration_seconds": manifest["duration_seconds"],
              "venv_setup_seconds": manifest["venv_setup_seconds"],
              "timed_out": manifest["timed_out"], "committed": manifest["committed"],
              "changed_files": manifest["changed_files"],
              "token_usage": manifest.get("token_usage"),
              "rubric_profile": meta["rubric_profile"]}

    judge_cfg = rubric.get("judge", {})
    judge_same_model = _same_model(judge_cfg.get("model"), manifest.get("model"))
    record["judge_same_model"] = judge_same_model

    no_submission = manifest["timed_out"] or not manifest["changed_files"]
    missing_deliverables = [p for p in meta.get("required_deliverables", [])
                            if p not in manifest["changed_files"]]
    record["missing_deliverables"] = missing_deliverables
    # A no_submission trial is always incomplete, regardless of deliverables.
    record["complete_submission"] = (not no_submission) and not missing_deliverables

    category_scores = {}
    category_detail = {}

    if no_submission:
        record["no_submission"] = True
        no_sub = rubric["scoring"]["no_submission_score"]
        for cat in rubric["categories"]:
            category_scores[cat["id"]] = float(no_sub)
        category_detail["reason"] = "no diff produced (timeout, crash, or empty run)"
    else:
        print("[grade_trial] scoring correctness (hidden tests)...")
        results, ht_detail = score_hidden_tests(worktree, task_dir, meta)
        try:
            correctness, obligations_detail = score_obligations(
                results, meta.get("acceptance_obligations", []),
                rubric["correctness"]["obligation_weighting"])
        except ValueError as e:
            return _fail_loud(root, manifest["run_id"], str(e), {"hidden_test_detail": ht_detail})
        category_scores["correctness"] = correctness
        category_detail["correctness"] = dict(ht_detail, obligations=obligations_detail)

    # Gate evaluated immediately after correctness (contract §4), before any
    # of the more expensive checks below run.
    gate_status, failed_gates = evaluate_gates(gates, category_scores)
    record["gate_status"] = gate_status
    record["failed_gates"] = failed_gates

    if no_submission or gate_status == "failed":
        if not no_submission:
            # The gated category's score is kept for evidence; every other
            # (weighted) category is null -- it was never computed, because
            # the mutation gate and judge are the expensive steps and the
            # composite is already fixed at 0 regardless of what they'd say.
            for cid in weights:
                category_scores[cid] = None
            failed_names = ", ".join(g["category"] for g in failed_gates)
            category_detail["reason"] = (f"gate failed ({failed_names}): mutation gate, scope, "
                                          f"hygiene, and judge skipped (score is already fixed at 0)")
            print(f"[grade_trial] gate failed ({failed_names}) -- skipping mutation gate, "
                  f"scope, hygiene, and judge")
        record["integrity_violation"] = False
        record["judge_status"] = "not_run"
        record["judged_scores"] = {c: category_scores.get(c) for c in judged_ids}
        record["deterministic_score"] = 0.0
        record["composite_score"] = 0.0
        record["scored_weight_fraction"] = 0.0
        record["category_scores"] = category_scores
        record["category_detail"] = category_detail
        record["provenance"] = build_provenance(root, rubric, rubric_bytes, manifest, meta, task_dir,
                                                 ruff_version, ruff_pinned,
                                                 "not_run", judge_same_model)
        return _write_and_report(root, manifest, rubric, record)

    print("[grade_trial] running own-suite baseline...")
    baseline = own_suite_baseline(worktree)
    category_detail["own_suite_baseline"] = baseline
    if baseline.get("unparsable"):
        return _fail_loud(root, manifest["run_id"],
                           "own-suite baseline collected tests but parsed no verdict lines -- "
                           "grading cannot proceed",
                           {"own_suite_baseline": baseline})

    print("[grade_trial] checking suite health from outside repo root...")
    outside = ships_red_outside_root(worktree)
    category_detail["ships_red_outside_root"] = outside

    baseline_passed = set(baseline["passed_nodes"])
    scope_cfg = rubric["scope"]
    if scope_cfg["mutation_credit_from_authorized_tests_only"]:
        # Mutation credit is only ever earned by a test file the task
        # authorized the model to write -- the full suite still ran above as
        # the regression check, but a frozen or unrelated test must not earn
        # test_adequacy credit (contract §6).
        credit_paths = [p for p in meta.get("authorized_surface", []) if p.startswith("tests/")]
        eligible_passed = {n for n in baseline_passed if n.split("::")[0] in credit_paths}
    else:
        credit_paths = sorted({n.split("::")[0] for n in baseline_passed})
        eligible_passed = baseline_passed
    mutation_count = len(load_mutations(task_dir, meta))
    if eligible_passed:
        print(f"[grade_trial] running {mutation_count}-mutation test-adequacy gate "
              f"(this takes a while)...")
        frac, detail = mutation_gate(worktree, task_dir, meta, eligible_passed)
    else:
        # No baseline-passing test in the authorized test path can ever be
        # flipped, so no mutation can earn credit -- skip the (expensive)
        # mutation runs rather than pay for len(mutations) trivially-
        # "survive" verdicts.
        frac, detail = 0.0, {"note": "no baseline-passing test in the authorized test path; no "
                              "mutation can earn credit", "total": mutation_count, "killed": 0,
                              "baseline_passed_count": 0}
    detail["credit_paths"] = credit_paths
    detail["baseline_passed_eligible"] = len(eligible_passed)
    detail["baseline_passed_total"] = len(baseline_passed)
    category_scores["test_adequacy"] = frac
    category_detail["test_adequacy"] = detail

    print("[grade_trial] checking scope discipline...")
    frac, detail = scope_discipline(worktree, before_head, meta, rubric)
    category_scores["scope_discipline"] = frac
    category_detail["scope_discipline"] = detail
    record["integrity_violation"] = bool(detail["integrity_violations"])

    print("[grade_trial] running differential lint...")
    try:
        frac, detail = hygiene(root, worktree, before_head, rubric, ruff_path, baseline, outside)
    except ValueError as e:
        return _fail_loud(root, manifest["run_id"], str(e),
                          {"automated_category_scores": category_scores,
                           "automated_category_detail": category_detail})
    category_scores["hygiene"] = frac
    category_detail["hygiene"] = detail

    print(f"[grade_trial] judged categories {judged_ids}: "
          f"{'calling judge model' if judge_cfg.get('model') else 'skipped (no judge configured)'}...")
    try:
        jscores, jdetail, judge_status = run_judge(root, worktree, before_head, rubric,
                                                    judged_ids, meta)
    except ValueError as e:
        return _fail_loud(root, manifest["run_id"], str(e),
                          {"automated_category_scores": category_scores,
                           "automated_category_detail": category_detail})
    if judge_status == "failed":
        unparsed = [c for c in judged_ids if jscores.get(c) is None]
        diag_dir = os.path.join(root, "eval", "results", "tmp", "judge_failures")
        os.makedirs(diag_dir, exist_ok=True)
        diag_path = os.path.join(diag_dir, f"{manifest['run_id']}.json")
        with open(diag_path, "w") as f:
            # Save the automated categories too -- already computed above,
            # otherwise lost on failure and only recoverable via a full
            # re-grade (the mutation gate is the slow step).
            json.dump({"run_id": manifest["run_id"], "unparsed_categories": unparsed,
                       "automated_category_scores": category_scores,
                       "automated_category_detail": category_detail,
                       "detail": jdetail}, f, indent=2, default=str)
        print(f"[grade_trial] ERROR: judge ran {MAX_JUDGE_ATTEMPTS} times but never "
              f"returned a parseable score for {unparsed}. No run record was written -- "
              f"this trial is NOT graded and must not be compared to others until "
              f"investigated. Diagnostic: {diag_path}", file=sys.stderr)
        return 1
    for c in judged_ids:
        category_scores[c] = jscores.get(c)
    category_detail["judge"] = jdetail
    record["judge_status"] = judge_status

    det_score, _ = weighted_score(automated_ids, weights, category_scores)
    comp_score, ws_all = weighted_score(automated_ids + judged_ids, weights, category_scores)
    record["deterministic_score"] = det_score
    record["composite_score"] = comp_score
    record["scored_weight_fraction"] = round(ws_all / sum(weights.values()), 2) if weights else 0.0
    record["judged_scores"] = {c: category_scores.get(c) for c in judged_ids}
    record["category_scores"] = category_scores
    record["category_detail"] = category_detail
    record["provenance"] = build_provenance(root, rubric, rubric_bytes, manifest, meta, task_dir,
                                             ruff_version, ruff_pinned,
                                             judge_status, judge_same_model)

    return _write_and_report(root, manifest, rubric, record)


def write_report(path, record, rubric):
    profiles = rubric.get("profiles", {})
    profile_name = record.get("rubric_profile")
    profile = profiles.get(profile_name, {})
    weights = profile.get("weights", {})
    gates = profile.get("gates", {})

    gate_line = f"- Gate status: {record.get('gate_status')}"
    failed_gates = record.get("failed_gates") or []
    if failed_gates:
        parts = [f"{g['category']} {g['score']}<{g['threshold']}" for g in failed_gates]
        gate_line += " (" + "; ".join(parts) + ")"
    gate_line += f" | Integrity violation: {record.get('integrity_violation')}"

    complete_line = f"- Profile: `{profile_name}` | Complete submission: {record.get('complete_submission')}"
    if record.get("missing_deliverables"):
        complete_line += f" (missing: {', '.join(record['missing_deliverables'])})"

    judged = record.get("judged_scores") or {}
    jmodel = ((record.get("provenance") or {}).get("judge") or {}).get("model")
    jstatus = record.get("judge_status")

    def _judged_str(v):
        # Percentage of the category's weight earned, not "N/5" -- under the
        # shifted scale a judge score of 1 earns 0%, so echoing a /5 number
        # here would misreport what the trial actually scored. The raw judge
        # response is in the Detail block below.
        return f"{v * 100:.0f}% of weight" if isinstance(v, (int, float)) else "not scored"

    judge_line = (f"## Judged: readability {_judged_str(judged.get('readability'))}, "
                  f"maintainability {_judged_str(judged.get('maintainability'))} "
                  f"(judge {jmodel}, status {jstatus})")
    if record.get("judge_same_model"):
        judge_line += " -- withheld from comparison: judge is the trial model"

    det = record.get("deterministic_score")
    comp = record.get("composite_score")

    lines = [
        f"# Trial report: {record['run_id']}",
        "",
        f"- Task: `{record['task_id']}`",
        f"- Model: `{record['model']}` (harness: {record['harness']})",
        f"- Model duration: {record['duration_seconds']}s | venv setup: {record['venv_setup_seconds']}s | timed out: {record['timed_out']} | committed: {record['committed']}",
        f"- Changed files: {', '.join(record['changed_files']) or '(none)'}",
        complete_line,
        gate_line,
        "",
        f"## Deterministic score: {det if det is not None else 'not scored'} / 100",
        "",
        judge_line,
        "",
        f"## Composite score: {comp if comp is not None else 'not scored'} / 100",
        "",
        f"(scored {record['scored_weight_fraction']*100:.0f}% of profile weight)",
        "",
        "## Category scores",
        "",
        "| Category | Kind | Weight | Score |",
        "|---|---|---|---|",
    ]
    for cat in rubric["categories"]:
        cid = cat["id"]
        s = (record.get("category_scores") or {}).get(cid)
        s_str = f"{s*100:.0f}%" if isinstance(s, (int, float)) else "not scored"
        w_str = "gate" if cid in gates else str(weights.get(cid, "--"))
        lines.append(f"| {cid} | {cat['kind']} | {w_str} | {s_str} |")

    lines += ["", "## Obligations", "", "| Obligation | Passed | Collected | Fraction |", "|---|---|---|---|"]
    obligations = ((record.get("category_detail") or {}).get("correctness") or {}).get("obligations", [])
    for ob in obligations:
        lines.append(f"| {ob['id']} | {ob['passed']} | {ob['collected']} | {ob['fraction']:.2f} |")
    if not obligations:
        lines.append("| (none -- not computed for this trial) | | | |")

    lines += ["", "## Provenance", "", "```json",
              json.dumps(record.get("provenance", {}), indent=2, default=str), "```"]

    lines += ["", "## Detail", "", "```json",
              json.dumps(record.get("category_detail", {}), indent=2, default=str)[:20000],
              "```"]
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    sys.exit(main())
