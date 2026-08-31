"""Command-builders for every supported invocation harness.

This repo's whole point is "point a harness+model at it and it tests" --
opencode is the fixed default (it is how local models are actually run day
to day), but the trial runner is not opencode-specific. The read-write
launch shapes below are taken directly from the `orchestrator` skill's
per-harness references (skills/orchestrator/references/*.md), which already
did the work of finding the unattended, auto-approving, write-enabled
invocation for each of these five CLIs. This module only reuses that
knowledge for a single synchronous one-shot call; it does not reimplement
orchestrator's session tracking, health polling, or resume machinery --
run_trial.py owns the whole lifecycle of one subprocess call directly, so
none of that is needed here.

Each builder returns (argv, extra_env, cwd) for subprocess.run. All five are
unattended and auto-approving: there is no human present to approve a
permission prompt in a benchmark trial, so every builder picks the
documented auto/yolo/accept-edits equivalent.
"""


class UnsupportedEffort(ValueError):
    pass


def _claude(prompt, model, effort, worktree):
    cmd = ["claude", "-p", prompt]
    if model:
        cmd += ["--model", model]
    if effort:
        cmd += ["--effort", effort]
    cmd += ["--permission-mode", "acceptEdits", "--output-format", "text",
            "--add-dir", worktree]
    return cmd, {}, worktree


def _codex(prompt, model, effort, worktree):
    cmd = ["codex", "exec", prompt]
    if model:
        cmd += ["-m", model]
    if effort:
        cmd += ["-c", f'model_reasoning_effort="{effort}"']
    cmd += ["-c", 'sandbox_mode="workspace-write"', "-c", 'approval_policy="never"',
            "--skip-git-repo-check", "-C", worktree]
    return cmd, {}, worktree


def _copilot(prompt, model, effort, worktree):
    cmd = ["copilot"]
    if model:
        cmd += ["--model", model]
    if effort:
        cmd += ["--effort", effort]
    cmd += ["-p", prompt, "--allow-all-tools", "--autopilot", "--silent",
            "--add-dir", worktree]
    return cmd, {}, worktree


def _opencode(prompt, model, effort, worktree):
    cmd = ["opencode", "run", prompt]
    if model:
        cmd += ["-m", model]
    if effort:
        cmd += ["--variant", effort]
    cmd += ["--agent", "build", "--auto", "--dir", worktree, "--format", "json"]
    return cmd, {}, worktree


def _qwen(prompt, model, effort, worktree):
    if effort:
        raise UnsupportedEffort(
            "qwen's tested CLI has no effort/variant flag -- fails closed "
            "rather than silently dropping the requested effort")
    cmd = ["qwen", "--prompt", prompt]
    if model:
        cmd += ["--model", model]
    cmd += ["--approval-mode", "yolo", "--sandbox", "--output-format", "text"]
    # qwen has no repository-directory flag; the child cwd IS the repo.
    return cmd, {}, worktree


BUILDERS = {
    "claude": _claude,
    "codex": _codex,
    "copilot": _copilot,
    "opencode": _opencode,
    "qwen": _qwen,
}


def build_command(harness, prompt, model, effort, worktree):
    if harness not in BUILDERS:
        raise ValueError(f"unsupported harness {harness!r}; choose from {sorted(BUILDERS)}")
    return BUILDERS[harness](prompt, model, effort, worktree)
