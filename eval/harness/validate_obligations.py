#!/usr/bin/env python3
"""Evaluator-integrity check: does grade_trial.py's obligation-to-node
mapping actually agree with the reference solution?

Validation gate #1 from docs/SCORING-REDESIGN-ASSESSMENT.md. For each task,
this substitutes the reference_solution/ files onto the frozen baseline,
installs the hidden tests, and collects node ids -- no model, no worktree,
no venv. It then asserts the same bidirectional mapping grade_trial.py
depends on at grading time: every collected node maps to exactly one
acceptance-obligation entry, and every declared entry matches at least one
collected node. A hidden test that maps to zero or two+ obligation groups
would fail every model's grade identically regardless of what the model
wrote -- exactly the kind of evaluator bug that a single trial's score can't
surface (it just looks like an oddly low ceiling, much later). Run this
whenever meta.yaml's acceptance_obligations, hidden_tests, or a task's
reference_solution/ changes.

Cheap by design: `git archive <ref> | tar -x` into a plain temp dir is
sufficient, since all this needs is running the reference solution's own
files under the operator's Python interpreter and asking pytest to enumerate
node ids -- no per-trial venv, no git worktree.

Usage:
    python eval/harness/validate_obligations.py            # every task
    python eval/harness/validate_obligations.py --task 001-merger-rate-feature
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grade_trial import _collect_node_ids  # noqa: E402


def repo_root():
    out = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True, check=True)
    return out.stdout.strip()


def default_tasks(root):
    tasks_dir = os.path.join(root, "eval", "tasks")
    return sorted(
        d for d in os.listdir(tasks_dir)
        if os.path.isdir(os.path.join(tasks_dir, d)) and not d.startswith(".")
    )


def load_meta(task_dir):
    with open(os.path.join(task_dir, "meta.yaml")) as f:
        return yaml.safe_load(f)


def load_rubric(root):
    with open(os.path.join(root, "eval", "rubric.yaml")) as f:
        return yaml.safe_load(f)


def archive_baseline(root, ref, dest):
    """`git archive <ref> | tar -x` into dest. No worktree, no venv: the only
    thing this ever runs against the result is `pytest --collect-only` under
    the operator's own interpreter, so a full worktree checkout would just be
    slower for the same answer."""
    archive = subprocess.Popen(["git", "archive", ref], cwd=root, stdout=subprocess.PIPE)
    try:
        with tarfile.open(fileobj=archive.stdout, mode="r|") as tf:
            tf.extractall(dest)  # ref is this repo's own frozen tag, not model input
    finally:
        archive.stdout.close()
        rc = archive.wait()
    if rc != 0:
        raise RuntimeError(f"git archive {ref!r} exited {rc}")


def install_reference_solution(task_dir, meta, dest):
    """Copy each top-level reference_solution/*.py over the authorized_surface
    entry with the same basename. Subdirectories (weak_baseline/,
    degenerate_controls/) are the task author's own freebie/regression
    controls, not part of the reference implementation, and are ignored."""
    ref_dir = os.path.join(task_dir, "reference_solution")
    authorized = meta.get("authorized_surface", [])
    by_basename = {os.path.basename(p): p for p in authorized}
    for py in sorted(glob.glob(os.path.join(ref_dir, "*.py"))):
        base = os.path.basename(py)
        target_rel = by_basename.get(base)
        if target_rel is None:
            raise RuntimeError(
                f"reference_solution/{base} has no authorized_surface entry with "
                f"matching basename -- authorized_surface: {authorized}")
        target = os.path.join(dest, target_rel)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy(py, target)


def install_hidden_tests(task_dir, meta, dest):
    """Same layout grade_trial.py's score_hidden_tests() uses: each hidden
    test file lands in tests/ under its own basename."""
    installed_rel = []
    for rel in meta.get("hidden_tests", []):
        src = os.path.join(task_dir, rel)
        target_rel = os.path.join("tests", os.path.basename(rel))
        target = os.path.join(dest, target_rel)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy(src, target)
        installed_rel.append(target_rel)
    return sorted(installed_rel)


def map_nodes_to_obligations(node_ids, obligations):
    """Same mapping rule as grade_trial.py: N == E or N.startswith(E + "["),
    since a declared entry never carries its own parametrize suffix.
    Returns (per_obligation: {id: [nodes]}, unmapped_nodes, multiply_mapped:
    {node: [obligation ids]}, dead_entries: [(obligation id, entry)])."""
    per_obl = {o["id"]: [] for o in obligations}
    entries_by_id = {o["id"]: o.get("tests", []) for o in obligations}
    unmapped = []
    multi = {}
    matched_entries = set()
    for n in sorted(node_ids):
        hits = []
        for oid, entries in entries_by_id.items():
            for e in entries:
                if n == e or n.startswith(e + "["):
                    hits.append(oid)
                    matched_entries.add((oid, e))
        if not hits:
            unmapped.append(n)
        elif len(set(hits)) > 1:
            multi[n] = sorted(set(hits))
        else:
            per_obl[hits[0]].append(n)
    # Per declared ENTRY, not per obligation: a group whose other tests still
    # collect would otherwise hide a deleted or renamed one, and that group
    # would quietly score out of a smaller denominator from then on.
    dead_entries = sorted((oid, e) for oid, entries in entries_by_id.items()
                          for e in entries if (oid, e) not in matched_entries)
    return per_obl, unmapped, multi, dead_entries


def validate_task(root, task_id, rubric):
    """Returns (errors: list[str], rows: list[(obligation_id, declared,
    collected)])."""
    task_dir = os.path.join(root, "eval", "tasks", task_id)
    meta = load_meta(task_dir)
    errors = []

    profile_name = meta.get("rubric_profile")
    profiles = rubric.get("profiles", {})
    if profile_name not in profiles:
        errors.append(f"rubric_profile {profile_name!r} not found in rubric.yaml's "
                       f"profiles ({sorted(profiles)})")

    authorized = set(meta.get("authorized_surface", []))
    required = set(meta.get("required_deliverables", []))
    missing_req = sorted(required - authorized)
    if missing_req:
        errors.append(f"required_deliverables not in authorized_surface: {missing_req}")

    obligations = meta.get("acceptance_obligations", [])
    if not obligations:
        errors.append("meta.yaml has no acceptance_obligations")

    baseline_ref = meta.get("baseline_ref", "frozen-substrate")

    node_ids = set()
    tmp = tempfile.mkdtemp(prefix=f"validate-obligations-{task_id}-")
    try:
        archive_baseline(root, baseline_ref, tmp)
        install_reference_solution(task_dir, meta, tmp)
        installed_rel = install_hidden_tests(task_dir, meta, tmp)
        node_ids, timed_out = _collect_node_ids(sys.executable, installed_rel, tmp)
        if timed_out:
            errors.append("pytest --collect-only timed out against the reference solution")
        elif not node_ids:
            errors.append("pytest --collect-only found zero nodes against the reference "
                           "solution -- collection itself is broken")
    except Exception as exc:  # noqa: BLE001 -- report as a task failure, not a crash
        errors.append(f"archive/collect failed: {exc}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    per_obl, unmapped, multi, dead_entries = map_nodes_to_obligations(node_ids, obligations)
    if dead_entries:
        errors.append(
            f"{len(dead_entries)} declared obligation entr"
            f"{'y' if len(dead_entries) == 1 else 'ies'} matched no collected node "
            f"(renamed or deleted hidden test?): "
            + ", ".join(f"{oid}:{e}" for oid, e in dead_entries))
    if unmapped:
        errors.append(f"{len(unmapped)} collected node(s) map to zero obligation entries: "
                       f"{unmapped}")
    if multi:
        errors.append(f"{len(multi)} collected node(s) map to more than one obligation "
                       f"entry: {multi}")

    n = len(obligations)
    rows = []
    for o in obligations:
        declared = len(o.get("tests", []))
        collected = len(per_obl.get(o["id"], []))
        rows.append((o["id"], declared, collected))
        if collected == 0:
            errors.append(f"obligation {o['id']!r} declares {declared} test entr"
                           f"{'y' if declared == 1 else 'ies'} but matched zero collected nodes")
    return errors, rows, n


def print_task_report(task_id, errors, rows, n):
    print(f"\n=== {task_id} ===")
    weight = f"1/{n} ({1.0 / n:.4f})" if n else "--"
    # Widen to the longest id present -- these names are deliberately verbose.
    w = max([len(r[0]) for r in rows] + [len("Obligation")])
    print(f"{'Obligation':<{w}} {'Declared':>8} {'Collected':>9}   Equal weight")
    for oid, declared, collected in rows:
        print(f"{oid:<{w}} {declared:>8} {collected:>9}   {weight}")
    if errors:
        print(f"[validate_obligations] FAILED ({len(errors)} issue(s)):")
        for e in errors:
            print(f"  - {e}")
    else:
        print("[validate_obligations] OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task", default=None,
                     help="task directory name under eval/tasks/ (default: every task)")
    args = ap.parse_args()

    root = repo_root()
    rubric = load_rubric(root)
    tasks = [args.task] if args.task else default_tasks(root)

    any_failed = False
    for task_id in tasks:
        errors, rows, n = validate_task(root, task_id, rubric)
        print_task_report(task_id, errors, rows, n)
        any_failed = any_failed or bool(errors)

    print(f"\n[validate_obligations] {len(tasks)} task(s) checked, "
          f"{'FAILURES PRESENT' if any_failed else 'all passed'}")
    return 1 if any_failed else 0


if __name__ == "__main__":
    sys.exit(main())
