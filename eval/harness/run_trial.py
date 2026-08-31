#!/usr/bin/env python3
"""Run one (task, model) trial: one shot, no review loop, no correction round.

Creates an isolated git worktree from a baseline ref, drops the task's
spec.md into it as TASK.md, invokes the harness (opencode by default) with a
fixed instruction and a fixed budget, and records everything needed for
grade_trial.py to score it afterward. The model gets exactly one attempt --
this script never re-prompts, never shows it review feedback, and never
retries on its behalf. That is the whole point of this repo: measure what a
model does unsupervised, not what a review/fix loop launders it into.

Usage:
    # opencode is the default harness -- this is the everyday local-model case
    python eval/harness/run_trial.py --task 001-merger-rate-feature \\
        --model macstudio/qwen/qwen3.8-27b-bf16

    # but any harness+model combination works -- point it at this repo and it tests
    python eval/harness/run_trial.py --task 001-merger-rate-feature \\
        --harness claude --model claude-sonnet-5 --effort low

    [--baseline-ref frozen-substrate] [--timeout SECONDS] [--label anything]
    also apply to every harness. See eval/harness/harnesses.py for the full
    supported set (opencode, claude, codex, copilot, qwen) and their exact
    command shapes, sourced from the orchestrator skill's per-harness
    references.

Portable by design: every path is resolved relative to the repo root via
`git rev-parse --show-toplevel`, so this runs the same whether invoked
directly on a host checkout or inside an agent-sbx sandbox clone.
"""
import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
import time
import uuid

import yaml  # PyYAML; add to requirements.txt if not already present

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harnesses import build_command, BUILDERS  # noqa: E402


def repo_root():
    out = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True, check=True)
    return out.stdout.strip()


def load_meta(root, task_id):
    task_dir = os.path.join(root, "eval", "tasks", task_id)
    with open(os.path.join(task_dir, "meta.yaml")) as f:
        meta = yaml.safe_load(f)
    return task_dir, meta


def make_run_id(task_id, model, label):
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_model = model.replace("/", "_")
    tag = f"-{label}" if label else ""
    return f"{ts}-{task_id}-{safe_model}{tag}-{uuid.uuid4().hex[:6]}"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task", required=True, help="task directory name under eval/tasks/")
    ap.add_argument("--model", required=True, help="model identifier, in whatever form --harness expects")
    ap.add_argument("--harness", default="opencode", choices=sorted(BUILDERS),
                     help="invocation CLI; opencode is the fixed default for local models, "
                          "but any harness with a build/write-enabled unattended mode works -- "
                          "point a harness+model at this repo and it tests")
    ap.add_argument("--effort", default=None,
                     help="reasoning effort/variant, passed through in the harness's own flag form "
                          "(unsupported by qwen's tested CLI -- fails closed rather than silently dropped)")
    ap.add_argument("--baseline-ref", default="frozen-substrate",
                     help="git ref the worktree is created from (default: the "
                          "'frozen-substrate' tag, which contains only src/, tests/, "
                          "docs/BACKGROUND.md, .gitignore, requirements.txt -- no eval/ "
                          "content). Do NOT default this to HEAD or any ref that has "
                          "eval/ committed to it: every task's hidden_tests/, mutations/, "
                          "and reference_solution/ live under eval/tasks/ in this repo's "
                          "history, and the worktree built from --baseline-ref is handed "
                          "directly to the model under test as its working directory. A "
                          "leak check runs after worktree creation regardless, but the "
                          "default itself must stay safe.")
    ap.add_argument("--timeout", type=int, default=None,
                     help="override the task's developer_timeout_seconds")
    ap.add_argument("--label", default=None, help="free-text label folded into the run id")
    args = ap.parse_args()

    root = repo_root()
    task_dir, meta = load_meta(root, args.task)
    timeout = args.timeout or int(meta.get("developer_timeout_seconds", 21600))

    run_id = make_run_id(args.task, args.model, args.label)
    runs_tmp = os.path.join(root, "eval", "results", "tmp", "worktrees")
    os.makedirs(runs_tmp, exist_ok=True)
    worktree = os.path.join(runs_tmp, run_id)

    print(f"[run_trial] run_id={run_id}")
    print(f"[run_trial] creating worktree at {worktree} from {args.baseline_ref}")
    subprocess.run(["git", "worktree", "add", "--detach", worktree, args.baseline_ref],
                    cwd=root, check=True)

    # Defense-in-depth against the whole point of this fix: whatever ref was
    # requested, the resulting worktree must not carry any benchmark-internal
    # content into what becomes the model's own working directory. This must
    # hold regardless of --baseline-ref -- a wrong ref on the command line, or
    # a future doc/task file accidentally added to the frozen substrate later,
    # should fail loudly here rather than silently leak hidden_tests/,
    # mutations/, or reference_solution/ to the model under test.
    leak_paths = ["eval", ".orchestrator", "HANDOFF.md"]
    leaks = [p for p in leak_paths if os.path.exists(os.path.join(worktree, p))]
    git_entry = os.path.join(worktree, ".git")
    if os.path.isdir(git_entry):
        # A worktree's own `.git` is a *file* pointing at the main repo's
        # gitdir, not a directory -- a directory here means this checkout
        # somehow carries a nested real repo, which is its own kind of leak.
        leaks.append(".git (unexpectedly a directory, not a worktree gitfile)")
    if leaks:
        print(f"[run_trial] REFUSING TO PROCEED: worktree built from "
              f"--baseline-ref={args.baseline_ref!r} contains benchmark-internal "
              f"content ({', '.join(leaks)}). This ref must not be used for a real "
              f"trial -- it would hand the model under test direct filesystem access "
              f"to its own hidden tests, mutation-injection code, and/or reference "
              f"solution. Use a ref that contains only the frozen baseline pipeline "
              f"(the 'frozen-substrate' tag, by default).", file=sys.stderr)
        subprocess.run(["git", "worktree", "remove", "--force", worktree], cwd=root)
        sys.exit(1)

    before_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=worktree,
                                  capture_output=True, text=True, check=True).stdout.strip()

    spec_path = os.path.join(task_dir, meta["spec"])
    shutil.copy(spec_path, os.path.join(worktree, "TASK.md"))

    prompt = (
        "Read TASK.md in this repository's root directory and implement everything "
        "it describes. This is a one-shot task: there is no reviewer, no PM, and no "
        "second attempt -- decide your own validation, run it yourself, and commit "
        "your final work when you are satisfied. Stay strictly within the Authorized "
        "Surface stated in TASK.md."
    )

    log_dir = os.path.join(root, "eval", "results", "tmp", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"{run_id}.jsonl")

    cmd, extra_env, cwd = build_command(args.harness, prompt, args.model, args.effort, worktree)
    env = dict(os.environ, **extra_env)

    print(f"[run_trial] invoking ({args.harness}): {' '.join(cmd[:1])} ... (timeout={timeout}s)")
    start = time.time()
    start_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
    timed_out = False
    exit_code = None
    with open(log_path, "w") as logf:
        try:
            proc = subprocess.run(cmd, cwd=cwd, env=env, stdout=logf,
                                   stderr=subprocess.STDOUT, timeout=timeout)
            exit_code = proc.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            exit_code = None
    duration = time.time() - start
    end_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # `git diff <ref>` silently ignores untracked files -- and every new file
    # the task asks for (merger_rate.py itself) starts untracked. Stage
    # everything first so new files enter the index and become visible to
    # every subsequent diff-based check here and in grade_trial.py, whether
    # or not the model itself ran `git add` or committed.
    subprocess.run(["git", "add", "-A"], cwd=worktree)
    diff_names = subprocess.run(["git", "diff", "--name-only", before_head],
                                 cwd=worktree, capture_output=True, text=True).stdout
    changed_files = [l for l in diff_names.splitlines() if l.strip()]
    after_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=worktree,
                                 capture_output=True, text=True).stdout.strip()
    committed = after_head != before_head

    manifest = {
        "run_id": run_id,
        "task_id": args.task,
        "model": args.model,
        "harness": args.harness,
        "effort": args.effort,
        "baseline_ref": args.baseline_ref,
        "before_head": before_head,
        "after_head": after_head,
        "committed": committed,
        "start": start_iso,
        "end": end_iso,
        "duration_seconds": round(duration, 1),
        "timeout_seconds": timeout,
        "timed_out": timed_out,
        "exit_code": exit_code,
        "changed_files": changed_files,
        "worktree_path": worktree,
        "transcript_log": log_path,
    }
    manifest_dir = os.path.join(root, "eval", "results", "tmp", "manifests")
    os.makedirs(manifest_dir, exist_ok=True)
    manifest_path = os.path.join(manifest_dir, f"{run_id}.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"[run_trial] done in {duration:.0f}s, timed_out={timed_out}, "
          f"changed_files={len(changed_files)}, committed={committed}")
    print(f"[run_trial] manifest: {manifest_path}")
    print(f"[run_trial] next: python eval/harness/grade_trial.py --manifest {manifest_path}")


if __name__ == "__main__":
    sys.exit(main())
