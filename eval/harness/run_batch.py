#!/usr/bin/env python3
"""Run a batch of independent trials across tasks and (harness, model, effort) combos.

This is a thin driver over run_trial.py + grade_trial.py -- it adds no
grading logic of its own. Each (task, combo, trial index) is one fully
independent `run_trial.py` invocation followed immediately by
`grade_trial.py` against the manifest it produced; trials never depend on
each other (aggregate.py rescans eval/results/runs/ from scratch regardless
of how records got there). A failure in one trial is logged and the batch
continues -- this file must never silently skip a trial without recording
why, and must never retry a trial (that would violate the one-shot rule
this repo exists to enforce).

Distinct (harness, model, effort) combos run concurrently (one OS process
each at a time, via a thread per combo); trials within a single combo run
strictly sequentially, in task order, matching how every prior batch in
this repo's history was run. Each git worktree gets its own path (run_id
includes a uuid), so concurrent `git worktree add`/`remove` across combos
relies only on git's own locking, not on anything in this script.

Usage:
    python eval/harness/run_batch.py \\
        --combo codex:gpt-5.6-luna:low \\
        --combo claude:claude-haiku-4-5-20251001:low \\
        --trials 3 --label weak-tier-r3

    # restrict to specific tasks (default: every directory under eval/tasks/)
    python eval/harness/run_batch.py --combo codex:gpt-5.6-luna:low \\
        --task 001-merger-rate-feature --task 002-pair-binning-convention \\
        --trials 1 --label smoke-test

Writes a running JSONL summary to
eval/results/tmp/batches/<label>-<timestamp>.jsonl (one line per completed
or failed trial, flushed immediately) so a partial batch is never lost, plus
a final summary table on stdout.
"""
import argparse
import concurrent.futures
import datetime
import json
import os
import re
import subprocess
import sys
import threading

MANIFEST_RE = re.compile(r"\[run_trial\] manifest: (\S+)")
RECORD_RE = re.compile(r"\[grade_trial\] record: (\S+)")
SCORE_RE = re.compile(r"\[grade_trial\] total_score=(\S+)")


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


def parse_combo(spec):
    parts = spec.split(":")
    if len(parts) != 3:
        raise ValueError(f"--combo must be harness:model:effort, got {spec!r}")
    harness, model, effort = parts
    return harness, model, (effort or None)


def run_one_trial(root, python, task, harness, model, effort, label):
    cmd = [python, os.path.join(root, "eval", "harness", "run_trial.py"),
           "--task", task, "--model", model, "--harness", harness, "--label", label]
    if effort:
        cmd += ["--effort", effort]
    result = {"task": task, "harness": harness, "model": model, "effort": effort,
              "label": label, "stage": "run_trial", "ok": False}
    proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    result["run_trial_returncode"] = proc.returncode
    m = MANIFEST_RE.search(proc.stdout)
    if not m:
        result["error"] = "no manifest path found in run_trial.py output"
        result["stdout_tail"] = proc.stdout[-2000:]
        result["stderr_tail"] = proc.stderr[-2000:]
        return result
    manifest_path = m.group(1)
    result["manifest_path"] = manifest_path

    grade_cmd = [python, os.path.join(root, "eval", "harness", "grade_trial.py"),
                 "--manifest", manifest_path]
    gproc = subprocess.run(grade_cmd, cwd=root, capture_output=True, text=True)
    result["stage"] = "grade_trial"
    result["grade_trial_returncode"] = gproc.returncode
    rm = RECORD_RE.search(gproc.stdout)
    sm = SCORE_RE.search(gproc.stdout)
    if not rm:
        result["error"] = "grade_trial.py did not produce a record (see stderr_tail)"
        result["stdout_tail"] = gproc.stdout[-2000:]
        result["stderr_tail"] = gproc.stderr[-2000:]
        return result
    result["record_path"] = rm.group(1)
    result["total_score"] = float(sm.group(1)) if sm and sm.group(1) != "None" else None

    try:
        with open(manifest_path) as f:
            manifest = json.load(f)
        result["run_id"] = manifest.get("run_id")
        result["duration_seconds"] = manifest["duration_seconds"]
        result["venv_setup_seconds"] = manifest["venv_setup_seconds"]
        result["timed_out"] = manifest["timed_out"]
        result["token_usage"] = manifest.get("token_usage")
    except OSError:
        pass

    result["ok"] = True
    return result


def run_combo(root, python, tasks, harness, model, effort, n_trials, label_prefix, summary_path, lock):
    combo_tag = f"{harness}-{model}".replace("/", "_")
    out = []
    for task in tasks:
        for i in range(1, n_trials + 1):
            label = f"{label_prefix}-{combo_tag}-{i}" if label_prefix else f"{combo_tag}-{i}"
            print(f"[run_batch] starting task={task} harness={harness} model={model} "
                  f"effort={effort} trial={i}/{n_trials}", flush=True)
            result = run_one_trial(root, python, task, harness, model, effort, label)
            result["trial_index"] = i
            with lock:
                with open(summary_path, "a") as f:
                    f.write(json.dumps(result) + "\n")
            status = "OK" if result["ok"] else "FAILED"
            score = result.get("total_score")
            setup = (f" venv_setup={result['venv_setup_seconds']}s" if result["ok"] else "")
            print(f"[run_batch] {status} task={task} harness={harness} model={model} "
                  f"trial={i}/{n_trials} score={score}"
                  f"{setup}"
                  f" {'error=' + result['error'] if not result['ok'] else ''}", flush=True)
            out.append(result)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--combo", action="append", required=True,
                     help="harness:model:effort, repeatable. effort may be empty (harness:model:)")
    ap.add_argument("--task", action="append", default=None,
                     help="task directory name under eval/tasks/, repeatable. "
                          "Default: every task directory.")
    ap.add_argument("--trials", type=int, default=3, help="trials per (task, combo)")
    ap.add_argument("--label", default=None, help="prefix folded into every run's --label")
    args = ap.parse_args()

    root = repo_root()
    python = sys.executable
    tasks = args.task or default_tasks(root)
    combos = [parse_combo(c) for c in args.combo]

    batch_dir = os.path.join(root, "eval", "results", "tmp", "batches")
    os.makedirs(batch_dir, exist_ok=True)
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    tag = args.label or "batch"
    summary_path = os.path.join(batch_dir, f"{ts}-{tag}.jsonl")

    total = len(tasks) * len(combos) * args.trials
    print(f"[run_batch] {len(combos)} combo(s) x {len(tasks)} task(s) x {args.trials} trial(s) "
          f"= {total} trials")
    print(f"[run_batch] combos: {combos}")
    print(f"[run_batch] tasks: {tasks}")
    print(f"[run_batch] summary: {summary_path}")

    lock = threading.Lock()
    all_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(combos)) as ex:
        futures = [
            ex.submit(run_combo, root, python, tasks, harness, model, effort,
                      args.trials, args.label, summary_path, lock)
            for harness, model, effort in combos
        ]
        for fut in concurrent.futures.as_completed(futures):
            all_results.extend(fut.result())

    n_ok = sum(1 for r in all_results if r["ok"])
    n_fail = len(all_results) - n_ok
    print(f"\n[run_batch] done: {n_ok}/{len(all_results)} trials graded, {n_fail} failed")
    if n_fail:
        print("[run_batch] FAILED trials:")
        for r in all_results:
            if not r["ok"]:
                print(f"  - {r['task']} {r['harness']} {r['model']} trial {r['trial_index']}: "
                      f"{r.get('error')}")
    print(f"[run_batch] full per-trial log: {summary_path}")
    print("[run_batch] next: python eval/harness/aggregate.py")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
