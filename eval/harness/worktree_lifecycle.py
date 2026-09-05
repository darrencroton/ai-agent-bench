#!/usr/bin/env python3
"""Inventory, archive, and prune trial worktrees under eval/results/tmp/worktrees/.

A trial worktree (git worktree + per-trial venv + caches) is reproducible
from its manifest's `before_head` plus the model's submission -- but the
submission itself only exists as uncommitted changes in that worktree.
Archived graded reports/records do NOT contain a patch of those changes, so
deleting a worktree without capturing one first destroys evidence that
can't be reconstructed. This script exists to do that capture safely,
before any pruning.

The captured patch covers tracked and untracked files, same as every other
diff-based check in this harness (`git add -A` first, same convention as
run_trial.py/grade_trial.py) -- it does NOT capture a file a model wrote
under a gitignored path (e.g. `/data/`, `/results/`, `/figures/`), since
those are pipeline-generated outputs, not submission source, everywhere
else in this repo too.

`archive/worktrees/<run_id>/` is a standing evidence store keyed by run_id,
distinct from AGENTS.md's `archive/<dated-reason>/` convention for
superseded *graded* batches -- this is raw per-trial evidence, not a
dated snapshot of a result set.

Usage:
    python eval/harness/worktree_lifecycle.py list
    python eval/harness/worktree_lifecycle.py archive --run-id <id> [--run-id <id> ...]
    python eval/harness/worktree_lifecycle.py archive --all
    python eval/harness/worktree_lifecycle.py prune --run-id <id> [...]   # requires prior archive
    python eval/harness/worktree_lifecycle.py prune --all
    python eval/harness/worktree_lifecycle.py prune --all --force        # skip the archive check
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_trial  # reuse remove_worktree, same convention as test_run_trial.py

ARCHIVE_SUBDIR = "worktrees"


def repo_root():
    out = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True, check=True)
    return out.stdout.strip()


def registered_trial_worktrees(root):
    """{run_id: path} for every registered worktree under
    eval/results/tmp/worktrees/ (excludes the main repo worktree).

    Excludes an entry whose directory no longer exists on disk (git still
    lists it as "prunable" once its worktree dir is gone by other means) --
    otherwise a later `git ... cwd=path` on it raises FileNotFoundError and
    aborts the rest of an --all batch instead of just skipping that one."""
    out = subprocess.run(["git", "worktree", "list", "--porcelain"],
                          cwd=root, capture_output=True, text=True, check=True).stdout
    prefix = os.path.join(root, "eval", "results", "tmp", "worktrees") + os.sep
    result = {}
    for line in out.splitlines():
        if line.startswith("worktree "):
            path = line[len("worktree "):]
            if path.startswith(prefix) and os.path.isdir(path):
                result[os.path.basename(path)] = path
    return result


def dir_size_bytes(path):
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for name in filenames:
            fp = os.path.join(dirpath, name)
            if not os.path.islink(fp):
                try:
                    total += os.path.getsize(fp)
                except OSError:
                    pass
    return total


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def archive_dir(root, run_id):
    return os.path.join(root, "archive", ARCHIVE_SUBDIR, run_id)


def _load_manifest(root, run_id):
    path = os.path.join(root, "eval", "results", "tmp", "manifests", f"{run_id}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def _capture_diff(wt, before_head):
    """Stage + diff the worktree against before_head. Returns the patch text,
    or None if either git command failed (caller must not treat that as an
    empty-but-valid diff). --binary/--full-index so a binary submission file
    round-trips through `git apply`, not just text files."""
    add_rc = subprocess.run(["git", "add", "-A"], cwd=wt, check=False).returncode
    diff = subprocess.run(
        ["git", "diff", "--binary", "--full-index", before_head, "--", ".", ":(exclude)TASK.md"],
        cwd=wt, capture_output=True, text=True, check=False)
    if add_rc != 0 or diff.returncode != 0:
        return None
    return diff.stdout


def cmd_list(root, args):
    worktrees = registered_trial_worktrees(root)
    rows = []
    for run_id, path in sorted(worktrees.items()):
        manifest = _load_manifest(root, run_id)
        end = manifest.get("end") if manifest else None
        archived = os.path.exists(os.path.join(archive_dir(root, run_id), "submission.patch"))
        graded = os.path.exists(os.path.join(root, "eval", "results", "runs", f"{run_id}.json"))
        rows.append((run_id, dir_size_bytes(path), end, archived, graded))

    print(f"{'run_id':<95} {'size':>8}  {'end (UTC)':<26} {'archived':<9} {'graded'}")
    for run_id, size, end, archived, graded in rows:
        print(f"{run_id:<95} {human(size):>8}  {end or '(no manifest)':<26} "
              f"{archived!s:<9} {graded}")
    total = sum(r[1] for r in rows)
    print(f"\n{len(rows)} registered trial worktrees, {human(total)} total")
    return True


def cmd_archive(root, args):
    worktrees = registered_trial_worktrees(root)
    targets = sorted(worktrees) if args.all else args.run_id
    ok = True
    for run_id in targets:
        if run_id not in worktrees:
            print(f"[worktree_lifecycle] SKIP {run_id}: not a registered worktree", file=sys.stderr)
            ok = False
            continue
        wt = worktrees[run_id]
        dest = archive_dir(root, run_id)
        os.makedirs(dest, exist_ok=True)

        manifest = _load_manifest(root, run_id)
        before_head = manifest.get("before_head") if manifest else None
        if manifest:
            shutil.copy(os.path.join(root, "eval", "results", "tmp", "manifests", f"{run_id}.json"),
                        os.path.join(dest, "manifest.json"))
            log_path = manifest.get("transcript_log")
            if log_path and os.path.exists(log_path):
                shutil.copy(log_path, os.path.join(dest, os.path.basename(log_path)))
        else:
            print(f"[worktree_lifecycle] WARNING {run_id}: no manifest -- cannot resolve "
                  f"before_head, submission.patch will not be written", file=sys.stderr)
            ok = False

        if before_head:
            patch_text = _capture_diff(wt, before_head)
            if patch_text is None:
                print(f"[worktree_lifecycle] ERROR {run_id}: `git add`/`git diff` failed -- "
                      f"submission.patch NOT written, this run is NOT safely prunable",
                      file=sys.stderr)
                ok = False
            else:
                with open(os.path.join(dest, "submission.patch"), "w") as f:
                    f.write(patch_text)

        for src, name in (
            (os.path.join(root, "eval", "results", "runs", f"{run_id}.json"), "run.json"),
            (os.path.join(root, "eval", "results", "reports", f"{run_id}.md"), "report.md"),
        ):
            if os.path.exists(src):
                shutil.copy(src, os.path.join(dest, name))

        print(f"[worktree_lifecycle] archived {run_id} -> {dest}")
    return ok


def cmd_prune(root, args):
    worktrees = registered_trial_worktrees(root)
    targets = sorted(worktrees) if args.all else args.run_id
    ok = True
    for run_id in targets:
        if run_id not in worktrees:
            print(f"[worktree_lifecycle] SKIP {run_id}: not a registered worktree", file=sys.stderr)
            ok = False
            continue
        patch = os.path.join(archive_dir(root, run_id), "submission.patch")
        if not args.force:
            if not os.path.exists(patch):
                print(f"[worktree_lifecycle] REFUSING to prune {run_id}: no archived evidence "
                      f"at {patch} -- run `archive` first, or pass --force to prune anyway",
                      file=sys.stderr)
                ok = False
                continue
            # Evidence existing isn't evidence it's still CURRENT -- the
            # worktree could have changed (or the file could have been
            # corrupted/truncated) since it was archived. Recompute the diff
            # fresh and require it to match byte-for-byte before removing
            # the only place that diff exists.
            manifest = _load_manifest(root, run_id)
            before_head = manifest.get("before_head") if manifest else None
            current = _capture_diff(worktrees[run_id], before_head) if before_head else None
            with open(patch) as f:
                archived = f.read()
            if current is None or current != archived:
                print(f"[worktree_lifecycle] REFUSING to prune {run_id}: archived evidence at "
                      f"{patch} is stale or unverifiable relative to the worktree's current "
                      f"state -- re-run `archive`, or pass --force to prune anyway",
                      file=sys.stderr)
                ok = False
                continue
        rc = run_trial.remove_worktree(root, worktrees[run_id])
        if rc == 0:
            print(f"[worktree_lifecycle] pruned {run_id}")
        else:
            print(f"[worktree_lifecycle] FAILED to prune {run_id} "
                  f"(git worktree remove rc={rc})", file=sys.stderr)
            ok = False
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="inventory registered trial worktrees: size, age, "
                                 "archived/graded status")

    ap_archive = sub.add_parser(
        "archive", help="preserve evidence (submission patch, manifest, transcript, any "
                         "graded record) into archive/worktrees/<run_id>/")
    g1 = ap_archive.add_mutually_exclusive_group(required=True)
    g1.add_argument("--run-id", action="append", default=[])
    g1.add_argument("--all", action="store_true")

    ap_prune = sub.add_parser("prune", help="remove a worktree after its evidence is archived")
    g2 = ap_prune.add_mutually_exclusive_group(required=True)
    g2.add_argument("--run-id", action="append", default=[])
    g2.add_argument("--all", action="store_true")
    ap_prune.add_argument("--force", action="store_true",
                           help="prune even without archived evidence (destructive -- "
                                "confirms nothing was preserved first)")

    args = ap.parse_args()
    root = repo_root()
    ok = {"list": cmd_list, "archive": cmd_archive, "prune": cmd_prune}[args.cmd](root, args)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
