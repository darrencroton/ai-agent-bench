#!/usr/bin/env python3
"""Deterministic structural-quality score: library + sweep CLI.

Retires the AI-judged `maintainability` category (see
docs/EVAL-CONSOLIDATION-PROPOSAL.md) with a formula fixed and frozen BEFORE
this file existed -- see docs/EVAL-CONSOLIDATION-TRIAL.md for its derivation
and validation, and docs/PM-BRANCH-TRANSPLANT-FINDINGS.md finding 5 for the
evidence a deterministic proxy tracks a human-judged maintainability call
about as well as an AI judge's own score does. Every constant the formula
uses is read from eval/profile.yaml's `structure:` block (see
`load_policy()`), never hardcoded here.

Two roles in one file: a library (`module_metrics`, `aggregate_metrics`,
`structural_score`, `load_policy`, `policy_sha256`) that profile_view.py and
branch_check.py (sibling scripts over the same grading kernel) import
directly; and
a `sweep` CLI that walks every graded record in eval/results/runs/*.json,
reconstructs each task's non-test `required_deliverables` post-image from
the archived submission.patch (the graded worktrees themselves are pruned),
and writes one structural score per record to eval/results/structure.json.

This computes a NEW score over EXISTING graded trials -- no re-grading, no
new model calls, no touching eval/rubric.yaml or eval/tasks/*/meta.yaml
(read-only over both eval/results/runs/ and archive/, per AGENTS.md's "Hard
invariants"; writes only its own output file).
"""
import argparse
import ast
import glob
import hashlib
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
from collections import Counter

import yaml


def repo_root():
    out = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True, check=True)
    return out.stdout.strip()


# ---------------------------------------------------------------------------
# Policy
# ---------------------------------------------------------------------------

_REQUIRED_COMPONENTS = ("decomposition", "length", "complexity")
_REQUIRED_COMPONENT_KEYS = ("metric", "zero_at", "one_at")
# Which of a task's scored deliverables the formula is allowed to measure.
# See eval/profile.yaml's `structure:` block for the measured evidence behind
# the `new_files_only` default -- in short, a deliverable that already existed
# at the trial's baseline makes the AST metrics describe the frozen substrate
# rather than the submission (Task 005 scored an identical 68.9 for all 42 of
# its trials before this existed).
_VALID_SCOPES = {"new_files_only", "all_deliverables"}


def load_policy(root, path=None):
    """Read eval/profile.yaml. Fails loud (raises) rather than silently
    defaulting if the `structure:` block is missing or incomplete -- a
    silently-defaulted policy would compute a score nobody actually chose,
    and it would do so quietly across every one of the 219 records."""
    p = path or os.path.join(root, "eval", "profile.yaml")
    with open(p) as f:
        policy = yaml.safe_load(f) or {}
    struct = policy.get("structure")
    if not isinstance(struct, dict):
        raise ValueError(f"{p}: missing or empty 'structure:' block")
    scope = struct.get("scope")
    if scope not in _VALID_SCOPES:
        raise ValueError(f"{p}: structure.scope must be one of {sorted(_VALID_SCOPES)}, "
                          f"got {scope!r}")
    for name in _REQUIRED_COMPONENTS:
        cfg = struct.get(name)
        if not isinstance(cfg, dict):
            raise ValueError(f"{p}: structure.{name} is missing")
        missing = [k for k in _REQUIRED_COMPONENT_KEYS if k not in cfg]
        if missing:
            raise ValueError(f"{p}: structure.{name} missing key(s) {missing}")
    return policy


def policy_sha256(policy):
    """sha256 over a canonical rendering of `version` plus the `structure:`
    block -- the values that actually determine a structural score -- so
    eval/results/structure.json can record which formula produced it without
    hashing the whole (heavily commented, freely rewordable) profile.yaml.

    `version` is included deliberately: eval/profile.yaml's own header tells a
    maintainer to bump it whenever a value changes, and if the bump did not
    move this hash that instruction would be theatre -- profile_view's
    freshness check would stay silent on a policy the operator had explicitly
    declared different. `score:` and `flags:` are NOT hashed; they are
    declarative documentation that no code reads."""
    canonical = json.dumps({"version": policy.get("version"),
                            "structure": policy["structure"]}, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# AST metrics
# ---------------------------------------------------------------------------

# Exactly docs/EVAL-CONSOLIDATION-TRIAL.md's frozen list. IfExp is the ternary `a if c else b`;
# BoolOp and comprehension `if`s are handled separately below since each one
# contributes a variable amount (not a flat +1).
_BRANCH_NODE_TYPES = (ast.If, ast.For, ast.AsyncFor, ast.While,
                      ast.ExceptHandler, ast.Assert, ast.IfExp)


def _function_cyclomatic(fn_node):
    """1 + one per branch node in the function's ast.walk() subtree (this
    naturally includes a NESTED function's own branches -- a nested def's
    control flow belongs to its enclosing function's complexity, not to a
    function_count entry of its own) + (len(values)-1) per BoolOp (an N-way
    `and`/`or` is N-1 extra paths) + len(ifs) per comprehension clause (each
    `if` is a filtering branch)."""
    complexity = 1
    for node in ast.walk(fn_node):
        if isinstance(node, _BRANCH_NODE_TYPES):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1
        elif isinstance(node, ast.comprehension):
            complexity += len(node.ifs)
    return complexity


def module_metrics(source_text):
    """AST metrics for one module. Raises SyntaxError (from ast.parse) on
    unparsable source -- the sweep's `parse_error` status catches it.

    Returns {"functions": [{"loc": int, "cyclomatic": int}, ...],
             "module_loc": int, "total_lines": int}. `functions` covers only
    TOP-LEVEL FunctionDef/AsyncFunctionDef in the module body (a class
    method lives in the ClassDef's body, not the module's, so it's excluded
    by construction). `module_loc`/`total_lines` are recorded for context
    only -- finding 5 measured module LOC as a near-zero predictor
    (rho -0.15), which is why it is NOT one of the three scored metrics."""
    tree = ast.parse(source_text)
    functions = [
        {"loc": node.end_lineno - node.lineno + 1, "cyclomatic": _function_cyclomatic(node)}
        for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    lines = source_text.splitlines()
    code_lines = [ln for ln in lines if ln.strip() and not ln.strip().startswith("#")]
    return {"functions": functions, "module_loc": len(code_lines), "total_lines": len(lines)}


def summarize_functions(functions):
    """function_count / median_function_loc / mean_cyclomatic over ONE list
    of {"loc", "cyclomatic"} records -- shared by the per-file display stats
    and `aggregate_metrics` (the pooled cross-file list) so both compute the
    three numbers identically."""
    n = len(functions)
    if n == 0:
        return {"function_count": 0, "median_function_loc": None, "mean_cyclomatic": None}
    return {
        "function_count": n,
        "median_function_loc": statistics.median(f["loc"] for f in functions),
        "mean_cyclomatic": statistics.mean(f["cyclomatic"] for f in functions),
    }


def aggregate_metrics(per_file_function_lists):
    """Pool functions across files FIRST, then compute the three metrics
    ONCE over the pooled list -- "never average per-file scores." Averaging
    per-file medians/means instead would silently misweight a task whose
    deliverables have very different function counts (a 1-function
    config.py pulled equal weight to a 10-function merger_rate.py).
    `per_file_function_lists` is a list of `module_metrics()`'s `functions`
    lists (one per file), not the module_metrics dicts themselves."""
    pooled = [f for file_functions in per_file_function_lists for f in file_functions]
    return summarize_functions(pooled)


def clamp01(x):
    return max(0.0, min(1.0, x))


def structural_score(metrics, policy):
    """(score_or_None, components_dict). None when there are no functions to
    measure at all (function_count == 0) -- nothing for the formula to
    score, and 0 would misleadingly read as "measured, and bad" rather than
    "not measurable".

    Each component is a clamped linear ramp between the policy's `zero_at`
    (metric value scoring 0) and `one_at` (metric value scoring 1):
        component = clamp01((metric - zero_at) / (one_at - zero_at))
    One formula handles both "more is better" (decomposition: zero_at <
    one_at) and "less is better" (length, complexity: zero_at > one_at) --
    the sign of (one_at - zero_at) supplies the direction, driven entirely
    by profile.yaml."""
    if not metrics.get("function_count"):
        # `not` rather than `== 0`: a None function_count (a caller handing in
        # an all-null metrics row, as the archived mixed-glm-5.2-1 branch has)
        # otherwise fell through to the arithmetic below and raised TypeError.
        # This is one of the library entry points AGENTS.md advertises for
        # direct import, so it has to be safe for a caller we do not control.
        return None, {}
    struct_policy = policy["structure"]
    values = {
        "decomposition": metrics["function_count"],
        "length": metrics["median_function_loc"],
        "complexity": metrics["mean_cyclomatic"],
    }
    components = {}
    for name, value in values.items():
        cfg = struct_policy[name]
        components[name] = clamp01((value - cfg["zero_at"]) / (cfg["one_at"] - cfg["zero_at"]))
    score = 100.0 * sum(components.values()) / len(components)
    return score, components


# ---------------------------------------------------------------------------
# Sweep: reconstruct each graded record's scored deliverables from its
# archived submission.patch, without needing the (pruned) worktree.
# ---------------------------------------------------------------------------

_DIFF_HEADER_RE = re.compile(r"^diff --git a/(.+) b/(.+)$")
_INDEX_LINE_RE = re.compile(r"^index ([0-9a-fA-F]+)\.\.([0-9a-fA-F]+)(?: \d+)?$")


def parse_patch_index(patch_text):
    """path -> {"new_blob": <hex sha or None>, "is_new_file": bool} for every
    file the patch touches, keyed by the post-image (b/) path. `new_blob`
    (possibly abbreviated; matched by prefix, see `_score_record`) verifies
    a reconstruction is byte-exact without needing the repo's object db."""
    files = {}
    current_path = None
    for line in patch_text.splitlines():
        header = _DIFF_HEADER_RE.match(line)
        if header:
            current_path = header.group(2)
            files[current_path] = {"new_blob": None, "is_new_file": False}
            continue
        if current_path is None:
            continue
        if line.startswith("new file mode"):
            files[current_path]["is_new_file"] = True
            continue
        index = _INDEX_LINE_RE.match(line)
        if index:
            files[current_path]["new_blob"] = index.group(2)
    return files


def reconstruct_file(root, before_head, patch_path, rel_path, dest_dir):
    """Reconstruct one path's post-image under dest_dir/rel_path: write its
    pre-image (`git show <before_head>:<rel_path>`, if it existed at
    baseline) then `git apply --include=<rel_path>` the patch on top.
    `git apply` works against a plain directory with no .git present, so
    `dest_dir` need not be a repo -- this is what lets the sweep reconstruct
    a file without the pruned worktree.

    Returns {"dest_path": <abs path, or None if the file doesn't exist>,
    "existed_at_baseline": bool, "applied": bool (True if the patch doesn't
    touch this path -- nothing needed applying), "apply_stderr": str/None}."""
    dest_path = os.path.join(dest_dir, rel_path)
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    existed_at_baseline = False
    if before_head:
        show = subprocess.run(["git", "show", f"{before_head}:{rel_path}"],
                               cwd=root, capture_output=True, check=False)
        if show.returncode == 0:
            with open(dest_path, "wb") as f:
                f.write(show.stdout)
            existed_at_baseline = True

    apply_result = subprocess.run(
        ["git", "apply", "-p1", f"--include={rel_path}", os.path.abspath(patch_path)],
        cwd=dest_dir, capture_output=True, text=True, check=False)
    applied_ok = apply_result.returncode == 0

    return {
        "dest_path": dest_path if os.path.isfile(dest_path) else None,
        "existed_at_baseline": existed_at_baseline,
        "applied": applied_ok,
        "apply_stderr": None if applied_ok else apply_result.stderr.strip(),
    }


def _is_scored_deliverable(path):
    """A required deliverable is scored if it's a non-test .py file. Checked
    by path COMPONENT rather than a bare prefix so a nested tests/
    directory is caught the same way a top-level one is."""
    return path.endswith(".py") and "tests" not in path.split("/")


def _resolve_before_head(root, record, manifest):
    """manifest.json's `before_head` is the reliable source (present for
    every record but one, which is already stopped earlier by a missing
    patch). Fallback: the record's own `baseline_ref` resolved with
    `git rev-parse` -- not exercised by any current record, but keeps the
    sweep from crashing on a future one that lacks a manifest."""
    if manifest and manifest.get("before_head"):
        return manifest["before_head"]
    ref = (manifest or {}).get("baseline_ref") or record.get("baseline_ref")
    if not ref:
        return None
    out = subprocess.run(["git", "rev-parse", ref], cwd=root,
                          capture_output=True, text=True, check=False)
    return out.stdout.strip() if out.returncode == 0 else None


# Where a submission's post-image is read from. `auto` is the only value the
# sweep uses by default: live worktree first, archived patch as the fallback
# (see find_worktree). The two explicit values exist so the paths can be
# AUDITED against each other -- sweeping the same records `--source worktree`
# and `--source patch` must produce identical scores, which is the check that
# proves the fallback equivalent rather than merely assumed. Pinning a source
# is also the honest way to re-derive a cohort purely from archived evidence.
SOURCE_AUTO = "auto"
SOURCE_WORKTREE = "worktree"
SOURCE_PATCH = "patch"
SOURCES = (SOURCE_AUTO, SOURCE_WORKTREE, SOURCE_PATCH)


def _existed_at_baseline(root, before_head, rel_path):
    """Whether `rel_path` was already present at the trial's baseline commit.

    This is what `structure.scope: new_files_only` keys off, and it is
    deliberately resolved from the BASELINE COMMIT rather than from the
    submission source, so the answer is identical whether the post-image came
    from a live worktree or a reconstructed patch."""
    if not before_head:
        return False
    show = subprocess.run(["git", "cat-file", "-e", f"{before_head}:{rel_path}"],
                           cwd=root, capture_output=True, check=False)
    return show.returncode == 0


def find_worktree(root, record, manifest):
    """The trial's live worktree, or None.

    A freshly graded trial has a worktree on disk and NO archived patch:
    neither run_trial.py nor run_batch.py archives anything, and this repo's
    standing policy is to leave trial worktrees in place until an operator
    runs worktree_lifecycle.py explicitly. Reading the worktree directly is
    therefore the primary source -- without it the structural column would be
    blank for every new trial until someone remembered to archive it, which
    is a silent gap rather than a loud one. The archived patch is the fallback
    for a trial whose worktree has since been pruned (the case for most of the
    existing cohort).

    Reading the worktree is also strictly safer than reconstructing: it is the
    graded artifact itself, so there is nothing to verify. The mutation gate
    cannot have disturbed it -- mutations monkey-patch already-imported
    modules at run time via sitecustomize.py and never rewrite source (see
    AGENTS.md)."""
    candidates = []
    if manifest and manifest.get("worktree_path"):
        candidates.append(manifest["worktree_path"])
    candidates.append(os.path.join(root, "eval", "results", "tmp", "worktrees",
                                    record["run_id"]))
    for path in candidates:
        if path and os.path.isdir(path):
            return path
    return None


def _load_manifest(root, record, archive_dir):
    """The trial's manifest, from the archive if present, else from the live
    manifests directory run_trial.py wrote it to."""
    for path in (os.path.join(archive_dir, record["run_id"], "manifest.json"),
                 os.path.join(root, "eval", "results", "tmp", "manifests",
                              f"{record['run_id']}.json")):
        if os.path.isfile(path):
            with open(path) as f:
                return json.load(f)
    return None


def _score_record(root, record, archive_dir, tmp_root, policy, manifest=None,
                   prefer=SOURCE_AUTO):
    """Returns the eval/results/structure.json entry for one graded record
    (everything except the top-level `task_id` the caller already has).

    `manifest` overrides the on-disk lookup; the sweep never passes it, tests
    use it to point at a synthetic worktree. `prefer` pins the post-image
    source -- see SOURCE_* and the `--source` flag."""
    run_id = record["run_id"]
    task_id = record["task_id"]
    with open(os.path.join(root, "eval", "tasks", task_id, "meta.yaml")) as f:
        meta = yaml.safe_load(f)
    # set() before sorted(): a deliverable listed twice would otherwise be
    # pooled twice and double-count its functions. No task does today.
    scored_paths = sorted({p for p in meta.get("required_deliverables", [])
                           if _is_scored_deliverable(p)})
    if not scored_paths:
        return {"status": "not_applicable",
                "note": "task has no non-test .py required_deliverable"}

    if manifest is None:
        manifest = _load_manifest(root, record, archive_dir)
    before_head = _resolve_before_head(root, record, manifest)
    new_files_only = policy["structure"]["scope"] == "new_files_only"

    # Source resolution: live worktree first, archived patch as the fallback.
    # See find_worktree() for why that order matters -- a freshly graded trial
    # has only the worktree, and most of the existing cohort has only a patch.
    worktree = None if prefer == SOURCE_PATCH else find_worktree(root, record, manifest)
    run_archive_dir = os.path.join(archive_dir, run_id)
    patch_path = os.path.join(run_archive_dir, "submission.patch")
    have_patch = os.path.isfile(patch_path)

    # P1 (external review, 2026-09-07): a leftover or partial worktree
    # directory must not shadow a perfectly good archived patch. find_worktree
    # only proves a DIRECTORY exists; it cannot know the submission is still in
    # it. Partial worktree directories demonstrably occur here -- see
    # archive/2026-09-07-pm-branch-transplant/orphan-worktree-*/ -- and
    # worktree_lifecycle.py reports "FAILED to prune" without removing the
    # directory when `git worktree remove` fails. Before this check such a
    # directory produced not_applicable with the note "no scored deliverable
    # was authored from scratch by this submission", which is simply false,
    # and the patch that would have scored it was never read.
    #
    # This runs BEFORE the source branch below, not after: demoting later would
    # leave patch_index empty on the patch path, silently forfeiting both blob
    # verification and apply-failure detection for exactly the records that
    # most need them. Only applies under `auto` -- an explicit
    # --source worktree must never silently become a patch read.
    if (worktree is not None and prefer == SOURCE_AUTO and have_patch
            and not any(os.path.isfile(os.path.join(worktree, path))
                        for path in scored_paths)):
        worktree = None

    patch_index, patch_text = {}, None
    if worktree is None:
        if prefer == SOURCE_WORKTREE:
            return {"status": "missing_submission",
                    "note": "no live worktree, and --source worktree forbids the "
                            "archived-patch fallback"}
        if not have_patch:
            # Repo-relative, never absolute: this note is copied verbatim into
            # the tracked eval/results/structure.json and from there into
            # eval/profile.md, and an absolute path would bake one machine's
            # home directory into project history (AGENTS.md forbids hardcoded
            # absolute paths for the same "must run identically in an
            # agent-sbx clone" reason).
            rel = os.path.relpath(run_archive_dir, root)
            return {"status": "missing_submission",
                    "note": f"no live worktree and no submission.patch under {rel}"}
        with open(patch_path, "r", errors="replace") as f:
            patch_text = f.read()
        if not patch_text.strip() or "diff --git" not in patch_text:
            return {"status": "not_applicable", "note": "empty patch (no-submission trial)"}
        patch_index = parse_patch_index(patch_text)
        touched = set(patch_index)
    else:
        # The graded record already states what the submission changed; no
        # need to re-derive it from a diff we are not reading.
        touched = set(record.get("changed_files") or [])
        if not touched:
            return {"status": "not_applicable", "note": "no changed files (no-submission trial)"}

    if not touched.intersection(scored_paths):
        return {"status": "not_applicable",
                "note": "submission touches none of the task's scored deliverables"}

    source = "worktree" if worktree else "patch"
    tempdir = tempfile.mkdtemp(dir=tmp_root, prefix=f"{run_id[:40]}-") if worktree is None else None
    try:
        files_out = {}
        per_file_functions = []
        missing_from_source = []
        for path in scored_paths:
            if new_files_only and _existed_at_baseline(root, before_head, path):
                # Recorded, not scored: the metrics would describe the frozen
                # substrate this file already had, not what the model wrote.
                files_out[path] = {
                    "note": "existed at baseline; excluded by structure.scope="
                            "new_files_only (measures the substrate, not the submission)"}
                continue

            blob_verified = None
            if worktree is not None:
                src_path = os.path.join(worktree, path)
                if not os.path.isfile(src_path):
                    files_out[path] = {"note": "not present in the trial worktree"}
                    missing_from_source.append(path)
                    continue
            else:
                recon = reconstruct_file(root, before_head, patch_path, path, tempdir)
                if path in patch_index and not recon["applied"]:
                    return {"status": "apply_failed", "note": f"{path}: {recon['apply_stderr']}"}
                if recon["dest_path"] is None:
                    files_out[path] = {"note": "not present in reconstructed submission"}
                    missing_from_source.append(path)
                    continue
                src_path = recon["dest_path"]
                # Only the reconstructed path needs verifying: a worktree file
                # IS the graded artifact, so there is nothing to check it
                # against. The patch's `index <old>..<new>` header carries the
                # post-image blob sha (possibly abbreviated, hence the prefix
                # compare), which proves the reconstruction byte-exact.
                declared_blob = patch_index.get(path, {}).get("new_blob")
                if declared_blob:
                    hashed = subprocess.run(["git", "hash-object", src_path],
                                            capture_output=True, text=True, check=True)
                    actual = hashed.stdout.strip()
                    n = min(len(actual), len(declared_blob))
                    blob_verified = actual[:n] == declared_blob[:n]

            with open(src_path, "r", errors="replace") as f:
                source_text = f.read()
            try:
                mm = module_metrics(source_text)
            except SyntaxError as e:
                return {"status": "parse_error", "note": f"{path}: {e}"}
            files_out[path] = {
                **summarize_functions(mm["functions"]),
                "module_loc": mm["module_loc"],
                "total_lines": mm["total_lines"],
                "blob_verified": blob_verified,
            }
            per_file_functions.append(mm["functions"])
    finally:
        if tempdir is not None:
            shutil.rmtree(tempdir, ignore_errors=True)

    if not per_file_functions:
        # Every scored deliverable was excluded above. `not_applicable` with a
        # null score, never a 0 -- 0 reads as "measured, and bad". The note
        # must say WHICH exclusion applied: "excluded by scope" and "the file
        # wasn't there" are different facts, and conflating them produced a
        # false explanation before the external review caught it.
        if missing_from_source:
            note = (f"scored deliverable(s) absent from the {source} source: "
                    f"{sorted(missing_from_source)}")
        else:
            note = ("no scored deliverable was authored from scratch by this "
                    "submission (see structure.scope in eval/profile.yaml)")
        return {"status": "not_applicable", "files": files_out, "source": source,
                "note": note}
    metrics = aggregate_metrics(per_file_functions)
    score, components = structural_score(metrics, policy)
    if score is None:
        # Parsed fine, but pooled to zero top-level functions -- e.g. a
        # submission that factors everything into a class. There is nothing for
        # the formula to measure, so this is not_applicable; returning "ok"
        # with a null score would over-count _meta.n_scored and let
        # profile.md's header claim it as scored.
        return {"status": "not_applicable", "source": source, "files": files_out,
                "metrics": metrics,
                "note": "scored deliverable(s) define no module-level function, so the "
                        "decomposition/length/complexity metrics have nothing to measure"}
    return {"status": "ok", "source": source, "files": files_out, "metrics": metrics,
            "components": components, "structural_score": score}


def sweep(root, out_path, runs_dir, archive_dir, prefer=SOURCE_AUTO):
    """Score every record in runs_dir. A record whose own scoring raises is
    caught here, not left to crash the whole sweep -- one bad archive entry
    must never cost the other 218."""
    policy = load_policy(root)
    records_glob = sorted(glob.glob(os.path.join(runs_dir, "*.json")))

    results = {}
    status_tally = Counter()
    source_tally = Counter()   # which post-image source each record used
    blob_tally = Counter()     # True / False / None (not checked)
    scores = []

    tmp_root = tempfile.mkdtemp(prefix="structure-sweep-")
    try:
        for path in records_glob:
            with open(path) as f:
                record = json.load(f)
            if record.get("harness") == "none":
                # Same defense-in-depth backstop aggregate.load_records applies:
                # a reference_check.py or branch_check.py record left behind by
                # mistake is not a trial. It matters here beyond tidiness --
                # profile_view.structure_eligible_tasks reads this sidecar, so a
                # stray PM-branch record on a task no real model has authored
                # from scratch would mark that task eligible and withhold every
                # real model's structural mean.
                continue
            run_id = record.get("run_id", os.path.basename(path))
            try:
                entry = _score_record(root, record, archive_dir, tmp_root, policy,
                                       prefer=prefer)
            except Exception as e:  # noqa: BLE001 -- see docstring
                entry = {"status": "apply_failed", "note": f"sweep error: {e}"}
            entry["task_id"] = record.get("task_id")
            results[run_id] = entry
            status_tally[entry["status"]] += 1
            if entry.get("source"):
                source_tally[entry["source"]] += 1
            for f in (entry.get("files") or {}).values():
                if "note" not in f:
                    blob_tally[f.get("blob_verified")] += 1
            if entry.get("structural_score") is not None:
                scores.append(entry["structural_score"])
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)

    meta = {
        "generated_from": dict(sorted(source_tally.items())) or None,
        "policy_sha256": policy_sha256(policy),
        "scope": policy["structure"]["scope"],
        "source_preference": prefer,
        "n_records": len(records_glob),
        "n_scored": status_tally.get("ok", 0),
        "n_not_applicable": status_tally.get("not_applicable", 0),
        "n_failed": sum(v for k, v in status_tally.items()
                        if k in ("missing_submission", "apply_failed", "parse_error")),
    }
    out = {"_meta": meta, **results}
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2, sort_keys=True)
        f.write("\n")

    print(f"[structure] wrote {out_path}")
    print(f"[structure] status tally: {dict(status_tally)}")
    print(f"[structure] blob verification: {blob_tally[True]} verified, "
          f"{blob_tally[False]} MISMATCH, {blob_tally[None]} not checked")
    if scores:
        print(f"[structure] structural_score: min={min(scores):.1f} "
              f"median={statistics.median(scores):.1f} max={max(scores):.1f} "
              f"n={len(scores)} (nulls={meta['n_records'] - len(scores)})")
    print(f"[structure] policy_sha256={meta['policy_sha256']}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sweep_p = sub.add_parser("sweep", help="Score every record in eval/results/runs/")
    sweep_p.add_argument("--out", default=None)
    sweep_p.add_argument("--runs-dir", default=None)
    sweep_p.add_argument("--archive-dir", default=None)
    sweep_p.add_argument("--source", choices=SOURCES, default=SOURCE_AUTO,
                          help="where to read each submission's post-image from: "
                               "'auto' (default) prefers a live trial worktree and falls "
                               "back to the archived patch; 'worktree' and 'patch' pin one "
                               "source, which is how the two are audited against each other")
    args = parser.parse_args(argv)

    root = repo_root()
    if args.command == "sweep":
        out_path = args.out or os.path.join(root, "eval", "results", "structure.json")
        runs_dir = args.runs_dir or os.path.join(root, "eval", "results", "runs")
        archive_dir = args.archive_dir or os.path.join(root, "archive", "worktrees")
        return sweep(root, out_path, runs_dir, archive_dir, prefer=args.source)
    return 1


if __name__ == "__main__":
    sys.exit(main())
