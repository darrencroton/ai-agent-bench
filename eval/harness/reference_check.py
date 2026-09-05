#!/usr/bin/env python3
"""Grade a task's reference_solution/ (or a named control variant under it,
e.g. weak_baseline/) through the real trial pipeline -- same worktree setup,
same venv provisioning, same grade_trial.py -- without invoking a harness or
a model.

This exists because a task's mutation gate, obligation mapping, and rubric
profile are otherwise only ever exercised by real trials, and a broken one
reads as a permanently low ceiling across many trials, much later (exactly
the "test_hB.py bug during initial validation" failure mode AGENTS.md warns
about). Run this against reference_solution/ once before trusting a task's
scores, and again whenever its hidden tests, mutations, or obligation map
change.

Unlike validate_obligations.py (no worktree, no venv, --collect-only only,
checks the obligation mapping in isolation), this runs the FULL grade:
hidden tests, own-suite baseline, the mutation gate, scope discipline,
hygiene, and (if eval/rubric.yaml configures one) the judge. It is slow by
the same amount a real trial's grading is slow.

No --baseline-ref flag, deliberately: unlike run_trial.py, this never hands
the worktree to a model, so there is no leak surface to guard against --
the ref always comes from the task's own meta.yaml (default
'frozen-substrate'), never from a caller-supplied string.

A reference-check grade is evaluator-validation evidence, never a leaderboard
result -- aggregate.py refuses to fold a harness="none" record into any
cohort (see its loader). Move the graded record and report out of
eval/results/runs/ and eval/results/reports/ into archive/ once you're done
with it, the same way this repo's own validation sessions have always done;
see docs/DESIGN.md's History for the convention.

Usage:
    python eval/harness/reference_check.py --task 004-catalog-loader-test-adequacy
    python eval/harness/reference_check.py --task 004-catalog-loader-test-adequacy \\
        --variant weak_baseline
    # then, as run_trial.py would print:
    python eval/harness/grade_trial.py --manifest eval/results/tmp/manifests/<run_id>.json
"""
import argparse
import datetime
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_trial import repo_root, load_meta, provision_trial_venv, remove_worktree  # noqa: E402
from validate_obligations import install_reference_solution  # noqa: E402


# A single path component, never a separator or a ".."/"." traversal --
# --variant and --label both flow into a directory lookup under
# reference_solution/ and into run_id, which in turn becomes a worktree path
# passed to `git worktree add`/`remove --force`. An unsanitized value
# reaching either is a path-traversal / accidental-deletion risk, not just a
# cosmetic one (codex/gpt-5.6-sol review, 2026-09-05).
_SAFE_COMPONENT = re.compile(r"^[A-Za-z0-9_.-]+$")


def _validate_component(value, flag):
    if value is None:
        return
    if not _SAFE_COMPONENT.fullmatch(value) or value in (".", ".."):
        raise SystemExit(f"{flag} must be a single path-safe component "
                          f"(letters, digits, '_', '-', '.') -- got {value!r}")


def _check_no_basename_collisions(authorized):
    """Both install_reference_solution() and this module's own variant
    overlay resolve an authorized_surface path by basename alone. Two
    authorized entries sharing a basename (e.g. src/config.py and
    tests/config.py) would make that resolution ambiguous and silently
    install a reference_solution/*.py file at whichever path happened to
    win the dict collision -- fail loudly instead (codex/gpt-5.6-sol
    review, 2026-09-05). No current task's authorized_surface collides;
    this only guards a task added later."""
    seen = {}
    collisions = {}
    for p in authorized:
        base = os.path.basename(p)
        seen.setdefault(base, []).append(p)
    for base, paths in seen.items():
        if len(paths) > 1:
            collisions[base] = paths
    if collisions:
        raise SystemExit(
            f"authorized_surface has ambiguous basenames, which "
            f"reference_solution/ file installation cannot resolve: {collisions}")


def install_variant(task_dir, meta, dest, variant):
    """Install the reference solution onto `dest`'s authorized_surface, then
    (if `variant` is given) layer reference_solution/<variant>/*.py on top of
    it by matching basename. Mirrors how this repo's own weak_baseline/
    controls are documented to be used (see Task 005's reference_solution/
    README.md's "Weak baseline" entry): the variant replaces only the
    authorized file(s) it ships, and the base reference solution still
    supplies everything else -- so a variant that only ships a weaker test
    file still runs against the reference's own correct implementation, and
    a variant that ships nothing usable is a task-authoring mistake, not a
    silent no-op.
    """
    authorized = meta.get("authorized_surface", [])
    _check_no_basename_collisions(authorized)
    install_reference_solution(task_dir, meta, dest)
    if variant is None:
        return

    variant_dir = os.path.join(task_dir, "reference_solution", variant)
    if not os.path.isdir(variant_dir):
        raise SystemExit(f"reference_solution/{variant}/ does not exist for task "
                          f"{os.path.basename(task_dir)!r}")

    by_basename = {os.path.basename(p): p for p in authorized}
    installed_any = False
    for py in sorted(glob.glob(os.path.join(variant_dir, "*.py"))):
        base = os.path.basename(py)
        target_rel = by_basename.get(base)
        if target_rel is None:
            raise SystemExit(
                f"reference_solution/{variant}/{base} has no authorized_surface entry "
                f"with matching basename -- authorized_surface: {authorized}")
        target = os.path.join(dest, target_rel)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy(py, target)
        installed_any = True

    if not installed_any:
        raise SystemExit(f"reference_solution/{variant}/ has no .py files to install")


def build_manifest(run_id, task_id, variant, baseline_ref, before_head,
                    venv_setup_seconds, changed_files, worktree):
    """The subset of run_trial.py's manifest schema grade_trial.py actually
    reads (see grade_trial.py's main(), which indexes run_id/task_id/model/
    harness/effort/baseline_ref/before_head/duration_seconds/
    venv_setup_seconds/timed_out/committed/changed_files/token_usage, plus
    worktree_path for locating the checkout). harness="none" and
    model="reference-solution"[+variant] make a reference-check record
    unmistakable in any listing or leaderboard row next to real trials, and
    are exactly what aggregate.py's loader keys off of to exclude one from
    every cohort."""
    model = "reference-solution" if variant is None else f"reference-solution+{variant}"
    return {
        "run_id": run_id, "task_id": task_id, "model": model, "harness": "none",
        "effort": None, "baseline_ref": baseline_ref, "before_head": before_head,
        "duration_seconds": 0.0, "venv_setup_seconds": round(venv_setup_seconds, 1),
        "timed_out": False, "committed": False, "changed_files": changed_files,
        "worktree_path": worktree, "token_usage": None,
    }


def make_run_id(task_id, variant, label):
    """Timestamp + short uuid, exactly like run_trial.py's make_run_id --
    NOT a deterministic function of (task, variant, label) alone. A
    deterministic id let a second run silently overwrite an earlier
    canonical eval/results/runs/ record whenever the rubric hash happened
    to match (grade_trial.py's own overwrite guard only checks the rubric
    hash, not whether the underlying task contract changed in between) --
    codex/gpt-5.6-sol review, 2026-09-05."""
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{ts}-REFCHECK-{task_id}"
    if variant:
        run_id += f"-{variant}"
    if label:
        run_id += f"-{label}"
    return f"{run_id}-{uuid.uuid4().hex[:6]}"


def _remove_worktree_or_warn(root, worktree):
    cleanup_rc = remove_worktree(root, worktree)
    if cleanup_rc:
        print(f"[reference_check] WARNING: failed to remove worktree {worktree} "
              f"(exit {cleanup_rc}) -- clean it up by hand with "
              f"'git worktree remove --force {worktree}'.", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task", required=True, help="task directory name under eval/tasks/")
    ap.add_argument("--variant", default=None,
                     help="subdirectory under reference_solution/ to layer on top of the "
                          "reference solution (e.g. weak_baseline); omit to grade the plain "
                          "reference solution")
    ap.add_argument("--label", default=None, help="free-text label folded into the run id")
    args = ap.parse_args()

    _validate_component(args.variant, "--variant")
    _validate_component(args.label, "--label")

    root = repo_root()
    task_dir, meta = load_meta(root, args.task)
    baseline_ref = meta.get("baseline_ref", "frozen-substrate")

    run_id = make_run_id(args.task, args.variant, args.label)
    runs_tmp = os.path.join(root, "eval", "results", "tmp", "worktrees")
    os.makedirs(runs_tmp, exist_ok=True)
    worktree = os.path.join(runs_tmp, run_id)

    print(f"[reference_check] run_id={run_id}")
    print(f"[reference_check] creating worktree at {worktree} from {baseline_ref}")
    subprocess.run(["git", "worktree", "add", "--detach", worktree, baseline_ref],
                    cwd=root, check=True)

    try:
        before_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=worktree,
                                      capture_output=True, text=True, check=True).stdout.strip()
        install_variant(task_dir, meta, worktree, args.variant)
        print("[reference_check] provisioning venv...")
        _, venv_setup_seconds = provision_trial_venv(worktree)
        print(f"[reference_check] venv ready in {venv_setup_seconds:.0f}s")
    except (SystemExit, RuntimeError, OSError, subprocess.CalledProcessError) as exc:
        # One cleanup path for every failure mode between worktree creation
        # and a gradeable checkout: a task-authoring mistake (SystemExit from
        # install_variant, RuntimeError from install_reference_solution's own
        # basename-mismatch check), or an environment failure (OSError/
        # CalledProcessError from git or venv provisioning). None of these
        # should leave a half-built worktree behind.
        detail = f"exit {exc.returncode}" if isinstance(exc, subprocess.CalledProcessError) else str(exc)
        _remove_worktree_or_warn(root, worktree)
        raise SystemExit(detail) from exc

    # Same convention as run_trial.py: stage everything so a brand-new file
    # (e.g. pair_binning.py itself) is visible to every subsequent diff-based
    # check, whether or not grade_trial.py's own defensive `git add -A` would
    # have caught it anyway. Unlike run_trial.py, both commands are checked
    # here: a real trial's failure here is vanishingly rare and already
    # covered by grade_trial.py's own defensive re-add, but a reference
    # check exists specifically to be trusted evidence, so a silently
    # incomplete `changed_files` (understating what's really on disk, and
    # therefore what scope/lint/judge see) must fail loudly instead of
    # grading a misleadingly small diff.
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

    manifest = build_manifest(run_id, args.task, args.variant, baseline_ref, before_head,
                               venv_setup_seconds, changed_files, worktree)
    manifest_dir = os.path.join(root, "eval", "results", "tmp", "manifests")
    os.makedirs(manifest_dir, exist_ok=True)
    manifest_path = os.path.join(manifest_dir, f"{run_id}.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"[reference_check] changed_files={len(changed_files)}")
    print(f"[reference_check] manifest: {manifest_path}")
    print(f"[reference_check] next: python eval/harness/grade_trial.py --manifest {manifest_path}")


if __name__ == "__main__":
    sys.exit(main())
