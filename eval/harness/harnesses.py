"""Command-builders and usage parsers for every supported invocation harness.

This repo's whole point is "point a harness+model at it and it tests" --
opencode is the fixed default (it is how local models are actually run day
to day), but the trial runner is not opencode-specific. The read-write
launch shapes below started from the `orchestrator` skill's per-harness
references (skills/orchestrator/references/*.md) -- a starting point, not a
guarantee: verify each shape is actually fully auto-approving for this
repo's unattended, no-human-present use before trusting it (see the next
paragraph for the one that wasn't). This module only reuses orchestrator's
per-harness knowledge for a single synchronous one-shot call; it does not
reimplement orchestrator's session tracking, health polling, or resume
machinery -- run_trial.py owns the whole lifecycle of one subprocess call
directly, so none of that is needed here.

Each builder returns (argv, extra_env, cwd) for subprocess.run. All five are
unattended and fully auto-approving -- the documented auto/yolo/bypass-
permissions equivalent, never a partial mode. `claude`'s `acceptEdits` looked
like that equivalent but isn't: it only auto-approves file edits and still
denies Bash calls with no one present to grant them (probe-confirmed: a
headless `acceptEdits` session cannot `git commit`). See docs/DESIGN.md's
History for the real trial evidence this was caught from.
"""
import json


class UnsupportedEffort(ValueError):
    pass


def _claude(prompt, model, effort, worktree):
    cmd = ["claude", "-p", prompt]
    if model:
        cmd += ["--model", model]
    if effort:
        cmd += ["--effort", effort]
    # stream-json (--verbose is mandatory for it in print mode) gives the
    # full turn-by-turn transcript, ending with the same usage/cost "result"
    # event plain `json` mode returns -- a strict superset, at the cost of a
    # bigger log file. The transcript matters on its own: a trial's score
    # alone can't distinguish real work from a model fighting its own
    # environment (see docs/DESIGN.md's History). Doesn't touch
    # permission-mode, so the bypassPermissions verification above holds.
    cmd += ["--permission-mode", "bypassPermissions", "--output-format", "stream-json",
            "--verbose", "--add-dir", worktree]
    return cmd, {}, worktree


def _codex(prompt, model, effort, worktree):
    cmd = ["codex", "exec", prompt]
    if model:
        cmd += ["-m", model]
    if effort:
        cmd += ["-c", f'model_reasoning_effort="{effort}"']
    # --json: full transcript, same reasoning as _claude()'s stream-json
    # above. Doesn't touch sandbox/approval, so the auto-approving
    # verification is unaffected.
    cmd += ["-c", 'sandbox_mode="workspace-write"', "-c", 'approval_policy="never"',
            "--skip-git-repo-check", "--json", "-C", worktree]
    return cmd, {}, worktree


def _copilot(prompt, model, effort, worktree):
    cmd = ["copilot"]
    if model:
        cmd += ["--model", model]
    if effort:
        cmd += ["--effort", effort]
    # --output-format json (not the default "text"): full transcript, same
    # reasoning as _claude() above. Unverified against a real copilot run
    # (not in active use) -- treat parse_usage()'s copilot handling as
    # best-effort until confirmed.
    cmd += ["-p", prompt, "--allow-all-tools", "--autopilot", "--silent",
            "--output-format", "json", "--add-dir", worktree]
    return cmd, {}, worktree


def _opencode(prompt, model, effort, worktree):
    cmd = ["opencode", "run", prompt]
    if model:
        cmd += ["-m", model]
    if effort:
        cmd += ["--variant", effort]
    # --format json: already a full transcript (predates this session's
    # verbose-by-default change to the other harnesses). Its usage capture
    # in parse_usage() is unverified, same as copilot/qwen -- see
    # _usage_generic() below.
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
    # --output-format stream-json (not "text"): full transcript, same
    # reasoning as _claude() above. Unverified against a real qwen run (not
    # in active use) -- treat parse_usage()'s qwen handling as best-effort
    # until confirmed.
    cmd += ["--approval-mode", "yolo", "--sandbox", "--output-format", "stream-json"]
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


def _json_objects(lines, reverse=False):
    """Yield each line of `lines` that parses as a JSON object, skipping the rest."""
    for line in reversed(lines) if reverse else lines:
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            yield json.loads(line)
        except ValueError:
            continue


def _usage_claude(lines):
    # --output-format stream-json ends with one "result" event carrying the
    # whole session's usage/cost; scan from the end in case of stray output
    # after it.
    for obj in _json_objects(lines, reverse=True):
        if obj.get("type") == "result" and "usage" in obj:
            u = obj["usage"]
            return {
                "source": "claude_result_json",
                "input_tokens": u.get("input_tokens"),
                "output_tokens": u.get("output_tokens"),
                "cache_creation_input_tokens": u.get("cache_creation_input_tokens"),
                "cache_read_input_tokens": u.get("cache_read_input_tokens"),
                "total_cost_usd": obj.get("total_cost_usd"),
            }
    return None


def _usage_codex(lines):
    # --json emits one turn.completed event per exec invocation in every
    # real trial seen so far; scan from the end and take the first match
    # regardless, so a future multi-turn shape still returns the final one.
    for obj in _json_objects(lines, reverse=True):
        if obj.get("type") == "turn.completed" and "usage" in obj:
            u = obj["usage"]
            return {
                "source": "codex_turn_completed",
                "input_tokens": u.get("input_tokens"),
                "output_tokens": u.get("output_tokens"),
                "cached_input_tokens": u.get("cached_input_tokens"),
                "reasoning_output_tokens": u.get("reasoning_output_tokens"),
                # codex reports no cost figure -- left None rather than
                # computed here from published per-token pricing.
                "total_cost_usd": None,
            }
    return None


def _usage_generic(harness):
    # copilot/qwen/opencode have no confirmed final-event schema (none has
    # been exercised for usage capture in a real trial yet). Best effort:
    # the last JSON object carrying a top-level "usage" dict, whatever else
    # it's called. A caller must treat a hit's "raw" shape as unverified,
    # and a miss (None) as "no data", never as zero usage.
    def parse(lines):
        for obj in _json_objects(lines, reverse=True):
            if isinstance(obj.get("usage"), dict):
                return {"source": f"{harness}_generic_unverified", "raw": obj["usage"],
                        "total_cost_usd": obj.get("total_cost_usd") or obj.get("cost_usd")}
        return None
    return parse


USAGE_PARSERS = {
    "claude": _usage_claude,
    "codex": _usage_codex,
    "copilot": _usage_generic("copilot"),
    "qwen": _usage_generic("qwen"),
    "opencode": _usage_generic("opencode"),
}


def parse_usage(harness, log_path):
    """Best-effort token/cost extraction from a harness's captured stdout.

    Never raises -- an unparsable or missing log means "no usage data", not
    a trial failure.
    """
    try:
        with open(log_path) as f:
            lines = f.readlines()
    except OSError:
        return None
    parser = USAGE_PARSERS.get(harness)
    return parser(lines) if parser else None
