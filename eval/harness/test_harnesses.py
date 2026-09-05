"""Regression tests for eval/harness/harnesses.py: command-shape builders and
usage parsers.

Run from eval/harness/:
    cd eval/harness && ../../venv/bin/python -m pytest test_harnesses.py -v

build_command() is pure, so its shapes are asserted directly. The usage
parsers are exercised against realistic captured-line fixtures rather than a
live CLI call; the opencode/qwen/copilot fixtures below are trimmed from real
invocations run during this repo's 2026-09-05 harness verification (see
docs/DESIGN.md's History) -- not invented shapes.
"""
import json

import pytest

import harnesses


# ---- build_command: command shapes ----

def test_build_command_unsupported_harness_raises():
    with pytest.raises(ValueError):
        harnesses.build_command("nonexistent", "prompt", None, None, "/wt")


def test_claude_command_shape():
    cmd, env, cwd = harnesses.build_command("claude", "do X", "claude-opus-5", "high", "/wt")
    assert cmd[:3] == ["claude", "-p", "do X"]
    assert cmd[cmd.index("--model") + 1] == "claude-opus-5"
    assert cmd[cmd.index("--effort") + 1] == "high"
    assert cmd[cmd.index("--permission-mode") + 1] == "bypassPermissions"
    assert cmd[cmd.index("--output-format") + 1] == "stream-json"
    assert cwd == "/wt" and env == {}


def test_codex_command_shape():
    cmd, env, cwd = harnesses.build_command("codex", "do X", "gpt-5.6-luna", "high", "/wt")
    assert cmd[:2] == ["codex", "exec"]
    assert cmd[cmd.index("-m") + 1] == "gpt-5.6-luna"
    assert 'model_reasoning_effort="high"' in cmd
    assert 'approval_policy="never"' in cmd
    assert cmd[cmd.index("-C") + 1] == "/wt"


def test_copilot_command_shape():
    cmd, env, cwd = harnesses.build_command("copilot", "do X", "gpt-5.6-luna", "high", "/wt")
    assert cmd[0] == "copilot"
    assert cmd[cmd.index("-p") + 1] == "do X"
    assert "--allow-all-tools" in cmd and "--autopilot" in cmd
    assert cmd[cmd.index("--add-dir") + 1] == "/wt"
    # --add-dir only grants permission; cwd (not an argv flag) is what
    # actually places copilot in the worktree -- confirmed the hard way
    # (2026-09-05: a manual invocation without a matching cwd wrote outside
    # the intended directory).
    assert cwd == "/wt"


def test_opencode_command_shape():
    cmd, env, cwd = harnesses.build_command("opencode", "do X", "opencode-go/hy3", "high", "/wt")
    assert cmd[:2] == ["opencode", "run"]
    assert cmd[cmd.index("-m") + 1] == "opencode-go/hy3"
    assert cmd[cmd.index("--variant") + 1] == "high"
    assert cmd[cmd.index("--agent") + 1] == "build"
    assert "--auto" in cmd
    assert cmd[cmd.index("--dir") + 1] == "/wt"


def test_qwen_command_shape():
    cmd, env, cwd = harnesses.build_command("qwen", "do X", "qwen3-max", None, "/wt")
    assert cmd[0] == "qwen"
    assert cmd[cmd.index("--prompt") + 1] == "do X"
    assert cmd[cmd.index("--approval-mode") + 1] == "yolo"
    assert "--sandbox" in cmd
    # qwen has no repository-directory flag -- cwd is the only placement.
    assert cwd == "/wt"


def test_qwen_rejects_an_effort_request():
    with pytest.raises(harnesses.UnsupportedEffort):
        harnesses.build_command("qwen", "do X", "qwen3-max", "high", "/wt")


# ---- parse_usage: claude / codex (documented final-event schemas) ----

def test_usage_claude_parses_final_result_event(tmp_path):
    line = json.dumps({"type": "result", "total_cost_usd": 0.02,
                        "usage": {"input_tokens": 100, "output_tokens": 50,
                                  "cache_creation_input_tokens": 10,
                                  "cache_read_input_tokens": 5}})
    log = tmp_path / "log.txt"
    log.write_text("some preamble line\n" + line + "\n")
    assert harnesses.parse_usage("claude", str(log)) == {
        "source": "claude_result_json", "input_tokens": 100, "output_tokens": 50,
        "cache_creation_input_tokens": 10, "cache_read_input_tokens": 5,
        "total_cost_usd": 0.02}


def test_usage_codex_parses_turn_completed_event(tmp_path):
    line = json.dumps({"type": "turn.completed",
                        "usage": {"input_tokens": 200, "output_tokens": 80,
                                  "cached_input_tokens": 20, "reasoning_output_tokens": 15}})
    log = tmp_path / "log.txt"
    log.write_text(line + "\n")
    usage = harnesses.parse_usage("codex", str(log))
    assert usage["input_tokens"] == 200 and usage["reasoning_output_tokens"] == 15
    assert usage["total_cost_usd"] is None


# ---- parse_usage: qwen / copilot via _usage_generic, real captured shapes ----

QWEN_RESULT_LINE = json.dumps({
    "type": "result", "subtype": "success",
    "usage": {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0}})


def test_usage_generic_parses_real_qwen_result_shape(tmp_path):
    log = tmp_path / "log.txt"
    log.write_text(QWEN_RESULT_LINE + "\n")
    usage = harnesses.parse_usage("qwen", str(log))
    assert usage["source"] == "qwen_generic"
    assert usage["raw"] == {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0}
    assert usage["total_cost_usd"] is None  # qwen reports no dollar figure


COPILOT_RESULT_LINE = json.dumps({
    "type": "result", "exitCode": 0,
    "usage": {"premiumRequests": 1, "totalApiDurationMs": 4139, "sessionDurationMs": 8223,
              "codeChanges": {"linesAdded": 1, "linesRemoved": 0, "filesModified": ["x.txt"]}}})


def test_usage_generic_parses_real_copilot_result_shape(tmp_path):
    log = tmp_path / "log.txt"
    log.write_text(COPILOT_RESULT_LINE + "\n")
    usage = harnesses.parse_usage("copilot", str(log))
    assert usage["source"] == "copilot_generic"
    assert usage["raw"]["premiumRequests"] == 1
    assert usage["total_cost_usd"] is None  # copilot reports no dollar figure either


# ---- parse_usage: opencode's dedicated per-step-sum parser ----

# A real tool-call step followed by a text-reply step: the second step's own
# "input" is small because most of its context came back via cache.read
# instead -- proof these are per-step deltas, not a running cumulative total.
OPENCODE_STEP_1 = json.dumps({
    "type": "step_finish",
    "part": {"tokens": {"total": 10818, "input": 10729, "output": 89, "reasoning": 0,
                         "cache": {"write": 0, "read": 0}},
              "cost": 0.00155368}})
OPENCODE_STEP_2 = json.dumps({
    "type": "step_finish",
    "part": {"tokens": {"total": 10846, "input": 208, "output": 14, "reasoning": 0,
                         "cache": {"write": 0, "read": 10624}},
              "cost": 0.00040908}})


def test_usage_opencode_sums_every_step_finish_event(tmp_path):
    log = tmp_path / "log.txt"
    log.write_text(OPENCODE_STEP_1 + "\n" + OPENCODE_STEP_2 + "\n")
    usage = harnesses.parse_usage("opencode", str(log))
    assert usage["input_tokens"] == 10729 + 208
    assert usage["output_tokens"] == 89 + 14
    assert usage["cache_read_tokens"] == 10624
    assert usage["total_cost_usd"] == pytest.approx(0.00155368 + 0.00040908)


def test_usage_opencode_reports_no_cost_as_none_not_zero(tmp_path):
    """A step_finish with tokens but no "cost" key at all must report
    total_cost_usd as None ("not asked"), never 0.0 ("free") -- caught in
    code review (2026-09-05) against the same accounting-legibility bug this
    parser exists to fix."""
    step_no_cost = json.dumps({
        "type": "step_finish",
        "part": {"tokens": {"total": 10, "input": 8, "output": 2, "reasoning": 0,
                             "cache": {"write": 0, "read": 0}}}})
    log = tmp_path / "log.txt"
    log.write_text(step_no_cost + "\n")
    usage = harnesses.parse_usage("opencode", str(log))
    assert usage["input_tokens"] == 8
    assert usage["total_cost_usd"] is None


def test_usage_opencode_has_no_top_level_usage_key_by_design():
    """Regression guard for the real bug found and fixed 2026-09-05: opencode's
    --format json never emits a top-level "usage" key, so a generic
    "last object with a usage dict" parser silently returns None for every
    opencode trial. This is exactly why opencode gets its own parser instead
    of _usage_generic()."""
    assert harnesses._usage_generic("opencode")([OPENCODE_STEP_1]) is None


def test_usage_opencode_returns_none_with_no_step_finish_events(tmp_path):
    log = tmp_path / "log.txt"
    log.write_text(json.dumps({"type": "text", "part": {"text": "hi"}}) + "\n")
    assert harnesses.parse_usage("opencode", str(log)) is None


# ---- parse_usage: shared failure modes ----

def test_parse_usage_missing_log_returns_none(tmp_path):
    assert harnesses.parse_usage("claude", str(tmp_path / "nope.txt")) is None


def test_parse_usage_unknown_harness_returns_none(tmp_path):
    log = tmp_path / "log.txt"
    log.write_text("{}\n")
    assert harnesses.parse_usage("nope", str(log)) is None
