#!/usr/bin/env python3
"""Grade an EXISTING project-manager Mode B branch through this repo's
one-shot grading kernel, without invoking a harness or a model.

This is the Mode 2 entry point of the two-mode design in
docs/EVAL-CONSOLIDATION-PROPOSAL.md: Mode 1 (`run_trial.py`) screens a model
one-shot from `spec.md`; Mode 2 qualifies a model that cleared Mode 1 by
grading a real `project-manager` Mode-B branch it produced in
`relative-velocity`, which runs the same task substrate as a supervised PM
plan instead of a single unattended shot. The two modes share one grading
kernel deliberately -- `grade_trial.py`, unmodified -- so a policy change
(the mutation bank, scope discipline, lint ruleset) never has to be kept in
sync between two graders.

Grading a branch from a foreign checkout through instruments built for this
repo's own worktrees is only valid under two conditions, both established by
hand in docs/PM-BRANCH-TRANSPLANT-FINDINGS.md before any branch was trusted:

  1. Substrate identity: the branch's un-touched files are the same bytes as
     this repo's own `frozen-substrate` baseline, so grading the branch here
     measures the same starting point the task assumes.
  2. Interface identity: the branch changes exactly the task's
     `authorized_surface` and exposes the same public API the task's
     reference solution declares, so the mutation bank's post-import
     monkey-patching (see mutations/sitecustomize.py) still applies.

The findings doc verified both once, by hand, over 14 branches with a
SHA-256-per-file comparison. This script checks (1) on every run instead --
see `check_frozen_unchanged()` -- because "verified once during an
experiment" is exactly the kind of assumption that goes stale silently: a
task's `frozen_unchanged` list can grow, and a caller can point `--repo` at
any checkout, not just the one that was hand-verified. Condition (2) is not
re-derived here; it is a property of a specific branch's diff, worth eyeballing
once per model family the way the findings doc did, not worth automating a
heavyweight cross-repo API diff for every run (see the "cheap, not
heavyweight" note on `check_frozen_unchanged()` below for why the same
reasoning kept this check cheap too).

Method: this is `reference_check.py` with one substitution -- instead of
installing `reference_solution/*.py` onto the task's authorized surface, it
installs the four authorized files as they exist on a named branch of
another checkout (`--repo`). Everything downstream -- worktree from
`frozen-substrate`, isolated venv, `git add -A` before the diff, the manifest
handed to `grade_trial.py` -- is unchanged from that sibling.

Records are written with harness="none" and model="pmbranch/<slug>". This is
not decorative: aggregate.py's `load_records` and profile_view.py both
exclude any harness=="none" record from every leaderboard cohort, which is
what keeps a PM-branch grade from silently inflating a one-shot model's
score. Treat a branch_check.py record as experiment evidence, never a
leaderboard result, and archive its run/report/worktree out of
eval/results/ into archive/ once you are done with it -- the same
harness="none" / archive-it-out convention reference_check.py documents, and
the one this script's own graded records (see
archive/2026-09-07-pm-branch-transplant/runs/) already followed.

Usage:
    python eval/harness/branch_check.py --task 001-merger-rate-feature \\
        --repo /path/to/relative-velocity-clone \\
        --branch merger-rate-revised/mixed-ornith-1.5-397b-q6-2
    # then, as run_trial.py would print:
    python eval/harness/grade_trial.py --manifest <printed path>
"""
import argparse
import ast
import datetime
import json
import os
import re
import subprocess
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_trial import repo_root, load_meta, provision_trial_venv, remove_worktree  # noqa: E402


# A single path component, never a separator or a ".."/"." traversal -- both
# --label and the branch-derived slug flow into run_id, which becomes a
# worktree path passed to `git worktree add`/`remove --force`. Mirrors
# reference_check.py's _SAFE_COMPONENT/_validate_component exactly (same
# path-traversal / accidental-deletion risk, same fix).
_SAFE_COMPONENT = re.compile(r"^[A-Za-z0-9_.-]+$")


def _validate_component(value, flag):
    if value is None:
        return
    if not _SAFE_COMPONENT.fullmatch(value) or value in (".", ".."):
        raise SystemExit(f"{flag} must be a single path-safe component "
                          f"(letters, digits, '_', '-', '.') -- got {value!r}")


def branch_slug(branch):
    """Derive a path-safe slug from a (possibly namespaced) branch name, for
    use in run_id and the model field. Takes the last path component (a
    branch like 'merger-rate-revised/mixed-ornith-1.5-397b-q6-2' should read
    as the model, not the plan namespace it sits under) and replaces
    anything unsafe with '-'. Raises rather than silently mangling a branch
    name into an empty or colliding slug -- e.g. a branch that is entirely
    punctuation, or one ending in '/' with nothing after it.
    """
    slug = branch.rsplit("/", 1)[-1]
    slug = re.sub(r"[^A-Za-z0-9_.-]", "-", slug)
    if not _SAFE_COMPONENT.fullmatch(slug) or slug in (".", ".."):
        raise SystemExit(f"cannot derive a path-safe slug from branch {branch!r}")
    return slug


def install_branch_files(src_repo, branch, meta, dest):
    """Copy each authorized_surface path out of `branch` into `dest`.

    A path absent on the branch is left at its frozen-substrate state and
    reported, exactly as a real trial that never created the file would be --
    grade_trial.py then records it as an incomplete submission rather than
    failing. Never silently skipped.
    """
    authorized = meta.get("authorized_surface", [])
    installed, missing = [], []
    for rel in authorized:
        show = subprocess.run(["git", "show", f"{branch}:{rel}"], cwd=src_repo,
                               capture_output=True, check=False)
        if show.returncode != 0:
            missing.append(rel)
            continue
        target = os.path.join(dest, rel)
        # dirname is "" for a root-level authorized path (no task declares one
        # today, but a future task could) -- os.makedirs("") raises, so skip.
        parent = os.path.dirname(target)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(target, "wb") as f:
            f.write(show.stdout)
        installed.append(rel)
    return installed, missing


def check_frozen_unchanged(src_repo, branch, root, baseline_ref, frozen_paths):
    """Cheap, per-run substrate-identity check.

    docs/PM-BRANCH-TRANSPLANT-FINDINGS.md established substrate identity once,
    by hand, with a SHA-256-per-file comparison between this repo's
    frozen-substrate and relative-velocity's branch point -- but that was
    verified for one pairing of checkouts at one point in time, and this
    script accepts an arbitrary --repo. A real merge-base lookup across two
    unrelated repos' histories would need a shared remote or a bundle import
    to even resolve, which is exactly the kind of heavyweight, easy-to-get-
    wrong machinery the task explicitly warned off inventing here. This
    check gets the same evidence more cheaply by comparing content directly:
    for each path this task declares `frozen_unchanged`, `git show` it off
    the branch tip itself and compare bytes against the same path at this
    repo's own baseline_ref. If a branch legitimately left every
    frozen_unchanged file untouched (which it must, or grade_trial.py's own
    scope_discipline check would already flag it once graded), this equals
    the merge-base comparison in outcome without needing one to exist. It
    also, as a side effect, re-derives the "byte-identical across all shared
    files" half of the findings doc's substrate-identity check on every run
    instead of once.

    Returns {"matched": [...], "mismatched": [...], "missing_on_branch": [...]}.
    Never raises on a branch-side difference -- a real content mismatch
    (scope creep on a frozen file, or a genuinely divergent substrate in
    --repo) is exactly the kind of thing an operator needs to see and weigh
    before trusting the grade, not something this script should paper over
    by aborting a run that might otherwise be perfectly gradeable.
    """
    matched, mismatched, missing_on_branch = [], [], []
    for rel in frozen_paths:
        branch_show = subprocess.run(["git", "show", f"{branch}:{rel}"], cwd=src_repo,
                                      capture_output=True, check=False)
        if branch_show.returncode != 0:
            missing_on_branch.append(rel)
            continue
        # This repo's own baseline_ref must contain every path its own
        # meta.yaml declares frozen_unchanged -- a failure here is a bug in
        # this repo's task metadata, not a property of the branch being
        # graded, so it is allowed to raise loudly (check=True) rather than
        # being folded into "mismatched".
        baseline_show = subprocess.run(["git", "show", f"{baseline_ref}:{rel}"], cwd=root,
                                        capture_output=True, check=True)
        if branch_show.stdout == baseline_show.stdout:
            matched.append(rel)
        else:
            mismatched.append(rel)
    return {"matched": matched, "mismatched": mismatched, "missing_on_branch": missing_on_branch}


def check_installed_python_parses(dest, installed):
    """ast.parse() every installed .py file and report which ones don't.

    Restricted to .py because every task's authorized_surface is Python-only
    today (checked across all five tasks' meta.yaml); a non-Python
    authorized file would have nothing meaningful to parse-check anyway. A
    branch that installs a file that doesn't even parse will fail the
    hidden tests regardless, so this isn't load-bearing for correctness --
    it exists to surface a garbled/binary/truncated `git show` result loudly
    at install time rather than as a confusing wall of collection errors
    several minutes into grading.

    Returns a list of (path, error_message) pairs for files that failed to
    parse; empty if every installed .py file parsed cleanly.
    """
    errors = []
    for rel in installed:
        if not rel.endswith(".py"):
            continue
        with open(os.path.join(dest, rel), "r", encoding="utf-8", errors="replace") as f:
            source = f.read()
        try:
            ast.parse(source, filename=rel)
        except (SyntaxError, ValueError) as exc:
            # ValueError, not just SyntaxError: a truncated or binary `git
            # show` result can carry a NUL byte, which ast.parse reports as
            # ValueError -- exactly the garbled-install case this exists for.
            errors.append((rel, str(exc)))
    return errors


def make_run_id(task_id, slug, label):
    """Timestamp + short uuid, exactly like run_trial.py's / reference_check.py's
    make_run_id -- NOT a deterministic function of (task, slug, label) alone,
    for the same overwrite-guard reason reference_check.py documents on its
    own make_run_id."""
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{ts}-PMBRANCH-{task_id}-{slug}"
    if label:
        run_id += f"-{label}"
    return f"{run_id}-{uuid.uuid4().hex[:6]}"


def build_manifest(run_id, task_id, slug, baseline_ref, before_head, venv_setup_seconds,
                    changed_files, worktree, src_repo, branch, branch_sha, missing,
                    frozen_check):
    """The subset of run_trial.py's manifest schema grade_trial.py actually
    reads (run_id/task_id/model/harness/effort/baseline_ref/before_head/
    duration_seconds/venv_setup_seconds/timed_out/committed/changed_files/
    token_usage, plus worktree_path for locating the checkout), plus extra
    provenance fields grade_trial.py ignores but an operator inspecting the
    manifest by hand needs: which branch/commit/repo this came from, which
    authorized paths were missing, and the frozen_unchanged substrate check.
    harness="none" and model="pmbranch/<slug>" make a branch-check record
    unmistakable in any listing next to real trials, and are exactly what
    aggregate.py's loader and profile_view.py key off of to exclude one from
    every cohort."""
    return {
        "run_id": run_id, "task_id": task_id, "model": f"pmbranch/{slug}", "harness": "none",
        "effort": None, "baseline_ref": baseline_ref, "before_head": before_head,
        "duration_seconds": 0.0, "venv_setup_seconds": round(venv_setup_seconds, 1),
        "timed_out": False, "committed": False, "changed_files": changed_files,
        "worktree_path": worktree, "token_usage": None,
        "source_repo": src_repo, "source_branch": branch, "source_commit": branch_sha,
        "missing_deliverables": missing, "frozen_unchanged_check": frozen_check,
    }


def _remove_worktree_or_warn(root, worktree):
    cleanup_rc = remove_worktree(root, worktree)
    if cleanup_rc:
        print(f"[branch_check] WARNING: failed to remove worktree {worktree} "
              f"(exit {cleanup_rc}) -- clean it up by hand with "
              f"'git worktree remove --force {worktree}'.", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task", required=True, help="task directory name under eval/tasks/")
    ap.add_argument("--repo", required=True,
                     help="checkout holding the PM branches (a relative-velocity clone, "
                          "or any repo carrying the same branch point)")
    ap.add_argument("--branch", required=True,
                     help="branch name to grade, e.g. merger-rate-revised/<model>")
    ap.add_argument("--label", default=None, help="free-text label folded into the run id")
    args = ap.parse_args()

    _validate_component(args.label, "--label")

    root = repo_root()
    src_repo = os.path.abspath(args.repo)
    _, meta = load_meta(root, args.task)
    baseline_ref = meta.get("baseline_ref", "frozen-substrate")

    rev = subprocess.run(["git", "rev-parse", args.branch], cwd=src_repo,
                          capture_output=True, text=True, check=False)
    if rev.returncode != 0:
        raise SystemExit(f"branch {args.branch!r} not found in {src_repo}")
    branch_sha = rev.stdout.strip()
    slug = branch_slug(args.branch)

    print(f"[branch_check] checking frozen_unchanged substrate identity against {baseline_ref}...")
    frozen_check = check_frozen_unchanged(src_repo, args.branch, root, baseline_ref,
                                           meta.get("frozen_unchanged", []))
    if frozen_check["mismatched"] or frozen_check["missing_on_branch"]:
        print(f"[branch_check] WARNING: substrate identity check found problems -- "
              f"mismatched={frozen_check['mismatched']} "
              f"missing_on_branch={frozen_check['missing_on_branch']}. This branch's "
              f"frozen_unchanged files differ from this repo's {baseline_ref} baseline; "
              f"the branch may not be measuring the same substrate this task assumes. "
              f"Review before trusting the graded result.", file=sys.stderr)
    else:
        print(f"[branch_check] substrate OK: {len(frozen_check['matched'])} frozen_unchanged "
              f"file(s) byte-identical to {baseline_ref}")

    run_id = make_run_id(args.task, slug, args.label)
    worktree = os.path.join(root, "eval", "results", "tmp", "worktrees", run_id)
    os.makedirs(os.path.dirname(worktree), exist_ok=True)

    print(f"[branch_check] run_id={run_id}")
    print(f"[branch_check] branch={args.branch} ({branch_sha[:12]})")
    subprocess.run(["git", "worktree", "add", "--detach", worktree, baseline_ref],
                    cwd=root, check=True)

    try:
        before_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=worktree,
                                      capture_output=True, text=True, check=True).stdout.strip()
        installed, missing = install_branch_files(src_repo, args.branch, meta, worktree)
        print(f"[branch_check] installed={len(installed)} missing={missing}")
        if missing:
            print(f"[branch_check] WARNING: {len(missing)} authorized_surface path(s) not "
                  f"found on branch {args.branch!r}: {missing} -- left at frozen-substrate "
                  f"state; grade_trial.py will record this as an incomplete submission.",
                  file=sys.stderr)
        parse_errors = check_installed_python_parses(worktree, installed)
        if parse_errors:
            print(f"[branch_check] WARNING: {len(parse_errors)} installed file(s) failed to "
                  f"parse as Python: {parse_errors}", file=sys.stderr)
        print("[branch_check] provisioning venv...")
        _, venv_setup_seconds = provision_trial_venv(worktree)
        print(f"[branch_check] venv ready in {venv_setup_seconds:.0f}s")
    except (SystemExit, RuntimeError, OSError, subprocess.CalledProcessError) as exc:
        # One cleanup path for every failure mode between worktree creation
        # and a gradeable checkout -- mirrors reference_check.py's identical
        # try/except for the identical reason: none of these should leave a
        # half-built worktree behind.
        detail = f"exit {exc.returncode}" if isinstance(exc, subprocess.CalledProcessError) else str(exc)
        _remove_worktree_or_warn(root, worktree)
        raise SystemExit(detail) from exc

    # Same convention as run_trial.py/reference_check.py: stage everything so
    # a brand-new file is visible to every subsequent diff-based check.
    # `git diff` silently ignores untracked files -- AGENTS.md records this
    # as a bug that already happened once. Both commands are checked, and a
    # failure here also gets the worktree cleaned up: a branch-check exists
    # specifically to be trusted evidence, so a silently incomplete
    # `changed_files` must fail loudly instead of grading a misleadingly
    # small diff, and a failed run shouldn't leave debris behind either.
    add = subprocess.run(["git", "add", "-A"], cwd=worktree, capture_output=True, text=True)
    if add.returncode != 0:
        _remove_worktree_or_warn(root, worktree)
        raise SystemExit(f"'git add -A' failed in {worktree}: {add.stderr}")
    diff = subprocess.run(
        ["git", "diff", "--name-only", before_head, "--", ".", ":(exclude)TASK.md"],
        cwd=worktree, capture_output=True, text=True)
    if diff.returncode != 0:
        _remove_worktree_or_warn(root, worktree)
        raise SystemExit(f"'git diff --name-only' failed in {worktree}: {diff.stderr}")
    changed_files = [line for line in diff.stdout.splitlines() if line.strip()]

    manifest = build_manifest(run_id, args.task, slug, baseline_ref, before_head,
                               venv_setup_seconds, changed_files, worktree, src_repo,
                               args.branch, branch_sha, missing, frozen_check)
    manifest_dir = os.path.join(root, "eval", "results", "tmp", "manifests")
    os.makedirs(manifest_dir, exist_ok=True)
    manifest_path = os.path.join(manifest_dir, f"{run_id}.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"[branch_check] changed_files={len(changed_files)}")
    print(f"[branch_check] manifest: {manifest_path}")
    print(f"[branch_check] next: python eval/harness/grade_trial.py --manifest {manifest_path}")


if __name__ == "__main__":
    sys.exit(main())
