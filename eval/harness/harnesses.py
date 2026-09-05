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
    # reasoning as _claude() above. Command shape and usage capture (final
    # "result" event's top-level "usage" dict, parsed by _usage_generic())
    # confirmed against a real unattended read-write invocation (2026-09-05).
    # --add-dir only grants copilot read/write permission on worktree -- it
    # does NOT change its cwd; run_trial.py's subprocess.run(cwd=worktree)
    # (the third element this returns) is what actually places it there.
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
    # verbose-by-default change to the other harnesses). Command shape and
    # --dir's cwd behavior confirmed against a real unattended read-write
    # invocation (2026-09-05); its usage capture has its own dedicated parser
    # below (_usage_opencode()) rather than _usage_generic() -- see there for
    # why.
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
    # reasoning as _claude() above. Command shape confirmed unattended
    # (2026-09-05): --approval-mode yolo is accepted and avoids a headless
    # hang even though it doesn't appear in `qwen --help`, and the final
    # stream-json "result" event does carry a top-level "usage" dict that
    # _usage_generic() parses -- but the one live invocation tried hit a
    # backend-side 502 (this installation's model routing, not a CLI-shape
    # issue), so a real completed turn is still unconfirmed end-to-end.
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
    # copilot and qwen both confirmed (2026-09-05, real invocations) to emit
    # exactly one final JSON object carrying a top-level "usage" dict --
    # copilot's "result" event ({"premiumRequests", "totalApiDurationMs",
    # "sessionDurationMs", "codeChanges": {...}}, no dollar figure) and
    # qwen's stream-json "result" event ({"input_tokens", "output_tokens",
    # "cache_read_input_tokens", ...}, also no dollar figure). Kept generic
    # (not given claude/codex-style named fields) because neither schema is
    # contractually documented upstream the way claude's/codex's is -- a
    # caller should still treat "raw"'s exact keys as best-effort. opencode
    # does NOT go through this: its `--format json` output has no top-level
    # "usage" key at all (see _usage_opencode() below), so this would always
    # return None for it.
    def parse(lines):
        for obj in _json_objects(lines, reverse=True):
            if isinstance(obj.get("usage"), dict):
                return {"source": f"{harness}_generic", "raw": obj["usage"],
                        "total_cost_usd": obj.get("total_cost_usd") or obj.get("cost_usd")}
        return None
    return parse


def _usage_opencode(lines):
    # --format json never emits a top-level "usage" event -- confirmed
    # against a real invocation (2026-09-05). Instead every step emits its
    # own "step_finish" event carrying that step's own token/cost delta at
    # part.tokens.{input,output,reasoning,cache.{read,write}} and part.cost
    # (a real trial with a tool call followed by a final text reply produced
    # two such events, with the second step's "input" dropping sharply
    # because most of its context came back as cache.read instead -- proof
    # these are per-step deltas, not a running cumulative total). Summed
    # across every step_finish in the transcript to get the run's total.
    input_t = output_t = reasoning_t = cache_write = cache_read = 0
    cost = 0.0
    found = saw_cost = False
    for obj in _json_objects(lines):
        if obj.get("type") != "step_finish":
            continue
        part = obj.get("part") or {}
        tokens = part.get("tokens")
        if tokens:
            found = True
            input_t += tokens.get("input") or 0
            output_t += tokens.get("output") or 0
            reasoning_t += tokens.get("reasoning") or 0
            cache = tokens.get("cache") or {}
            cache_write += cache.get("write") or 0
            cache_read += cache.get("read") or 0
        # Tracked separately from `found`/`tokens` so a step_finish with a
        # cost but no tokens (or vice versa) doesn't lose either figure, and
        # so a transcript with no cost key anywhere reports total_cost_usd
        # as None ("not asked") rather than a misleading 0.0 ("free") --
        # same reasoning as claude's/codex's parsers never inventing a cost.
        if "cost" in part:
            saw_cost = True
            cost += part.get("cost") or 0.0
    if not found:
        return None
    return {
        "source": "opencode_step_finish_sum",
        "input_tokens": input_t,
        "output_tokens": output_t,
        "reasoning_tokens": reasoning_t,
        "cache_write_tokens": cache_write,
        "cache_read_tokens": cache_read,
        "total_cost_usd": cost if saw_cost else None,
    }


USAGE_PARSERS = {
    "claude": _usage_claude,
    "codex": _usage_codex,
    "copilot": _usage_generic("copilot"),
    "qwen": _usage_generic("qwen"),
    "opencode": _usage_opencode,
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
