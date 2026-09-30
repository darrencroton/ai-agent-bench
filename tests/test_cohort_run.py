"""Tests for tools/cohort_run.py (the operator convenience wrapper: setup /
analyze / cleanup).

`setup` and `cleanup` are exercised with fabricated policy.yaml/results
fixtures under tmp_path so no real repo state is ever touched. `analyze`
monkeypatches grade_run.main/model_report.main/leaderboard.main directly --
the same in-process-call pattern grade_run.py itself uses for
dev_check.main()/review_score.run_review_score() -- so no real git worktree,
subprocess, or PM state is ever involved.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import bench_lib  # noqa: E402
import cohort_run as cr  # noqa: E402
import dev_check  # noqa: E402

_LAUNCHER_SKILL_MD = """\
---
name: project-manager
---

# Project Manager (Mode B)

## Some other section

Not the launcher.

## Launcher

Paste into a fresh PM-capable session (fill the bracketed values):

```md
Plan file: <absolute path>
Repo: <absolute path>
Developer: harness <codex|claude|copilot|opencode|qwen> model <model name>
Reviewer: harness <codex|claude|copilot|opencode|qwen> model <model name>

Use the project-manager skill.
```

Details the launcher relies on: see README.md.
"""

_EXPECTED_TEMPLATE = (
    "Plan file: <absolute path>\n"
    "Repo: <absolute path>\n"
    "Developer: harness <codex|claude|copilot|opencode|qwen> model <model name>\n"
    "Reviewer: harness <codex|claude|copilot|opencode|qwen> model <model name>\n"
    "\n"
    "Use the project-manager skill."
)


def _write_skill_md(tmp_path: Path, text: str = _LAUNCHER_SKILL_MD) -> Path:
    skill_dir = tmp_path / "project-manager"
    (skill_dir / "scripts").mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(text, encoding="utf-8")
    return skill_dir


def _make_prepared_repo(tmp_path: Path, name: str = "dev-repo") -> Path:
    """A plain directory (no git needed -- --repo's manual escape hatch
    doesn't touch git) carrying the frozen plan at its fixed relative path,
    standing in for an already-prepared Developer repo/worktree."""
    repo = tmp_path / name
    (repo / "docs").mkdir(parents=True)
    (repo / "docs" / "MERGER_RATE_PLAN-2SLICE.md").write_text("frozen plan\n", encoding="utf-8")
    return repo


# The task id every single-task fixture configures -- the same id the real
# policy.yaml uses, so fixture behavior mirrors production naming.
TASK_ID = "relative-velocity"


def _task_entry(
    repo: str | Path,
    *,
    branch_prefix: str = "pm-eval-v2",
    worktree_root: str | Path | None = None,
    plan_file: str = "docs/MERGER_RATE_PLAN-2SLICE.md",
    provenance_file: str = "docs/MERGER_RATE_PLAN-2SLICE.provenance.md",
    obligations_file: str = "hidden_tests/obligations.yaml",
) -> dict[str, Any]:
    """One complete tasks: registry entry -- every key bench_lib.resolve_task
    validates, mirroring the shape of this repo's own relative-velocity entry."""
    return {
        "repo": str(repo),
        "branch_prefix": branch_prefix,
        "worktree_root": str(worktree_root) if worktree_root is not None else None,
        "plan_file": plan_file,
        "provenance_file": provenance_file,
        "hidden_tests_dir": "hidden_tests",
        "obligations_file": obligations_file,
        "expected_slices": 2,
        "measurement": {
            "production_paths": ["src/**/*.py"],
            "test_paths": ["tests/**/*.py"],
            "doc_paths": ["docs/**/*.md", "*.md"],
        },
    }


def _resolved_task(task_id: str, entry: dict[str, Any]) -> dict[str, Any]:
    """bench_lib.resolve_task over a one-entry synthetic registry -- the exact
    dict shape create_dev_worktree/_task_worktree_layout consume."""
    return bench_lib.resolve_task({"default_task": task_id, "tasks": {task_id: entry}}, task_id)


def _write_policy(tmp_path: Path, skill_dir: Path, *, tasks: dict[str, Any], default_task: str, name: str = "policy.yaml", **extra: Any) -> Path:
    """A full policy file passing dev_check.load_policy (the stricter loader
    `setup` uses) plus the tasks: registry every path now resolves through."""
    policy = {
        "backend": "local",
        "pm_scripts_dir": str(skill_dir / "scripts"),
        "lint_script": str(tmp_path / "lint.py"),
        "health_script": str(tmp_path / "health.py"),
        "python_interpreter": str(tmp_path / "python3"),
        "subprocess_timeout_seconds": 600,
        # dev_check.load_policy (reused by cohort_run.load_policy, see its
        # own docstring) requires this global methodology block; the per-task
        # layout globs live inside each tasks: entry instead.
        "measurement": {
            "loc_definition": "net_physical_lines",
            "loc_category_definition": "ast_tokenize_line_classification",
            "metric_version": 2,
        },
        "default_task": default_task,
        "tasks": tasks,
        **extra,
    }
    policy_path = tmp_path / name
    policy_path.write_text(yaml.safe_dump(policy), encoding="utf-8")
    return policy_path


def _raw_policy_file(tmp_path: Path, *, tasks: dict[str, Any] | None = None, default_task: str = TASK_ID, name: str = "policy.yaml") -> Path:
    """A minimal raw-loadable policy (just default_task + tasks:) for the
    analyze/cleanup paths, which never need dev_check.py's keys."""
    if tasks is None:
        tasks = {TASK_ID: _task_entry(str(tmp_path / "substrate"))}
    policy_path = tmp_path / name
    policy_path.write_text(yaml.safe_dump({"default_task": default_task, "tasks": tasks}), encoding="utf-8")
    return policy_path


# --- extract_launcher_template ---------------------------------------------


class TestExtractLauncherTemplate:
    def test_extracts_fenced_block_under_heading(self, tmp_path: Path) -> None:
        skill_dir = _write_skill_md(tmp_path)
        template = cr.extract_launcher_template(skill_dir / "SKILL.md")
        assert template == _EXPECTED_TEMPLATE

    def test_missing_heading_is_a_named_error(self, tmp_path: Path) -> None:
        skill_dir = _write_skill_md(tmp_path, text="# Project Manager\n\nNo launcher here.\n")
        with pytest.raises(cr.CohortRunError, match="no '## Launcher' section"):
            cr.extract_launcher_template(skill_dir / "SKILL.md")

    def test_missing_fence_is_a_named_error(self, tmp_path: Path) -> None:
        skill_dir = _write_skill_md(tmp_path, text="# PM\n\n## Launcher\n\nNo fenced block here.\n")
        with pytest.raises(cr.CohortRunError, match="no fenced code block"):
            cr.extract_launcher_template(skill_dir / "SKILL.md")

    def test_fence_in_a_later_section_is_not_mistaken_for_the_launcher_block(self, tmp_path: Path) -> None:
        # A fenced block must be refused as missing, not silently borrowed
        # from a later, unrelated section just because it's the next fence
        # in the file.
        skill_dir = _write_skill_md(
            tmp_path,
            text="# PM\n\n## Launcher\n\nNo fenced block directly under this heading.\n\n## Appendix\n\n```\nunrelated content\n```\n",
        )
        with pytest.raises(cr.CohortRunError, match="no fenced code block"):
            cr.extract_launcher_template(skill_dir / "SKILL.md")


# --- render_launcher_prompt -------------------------------------------------


class TestRenderLauncherPrompt:
    def test_no_args_leaves_every_gap_untouched(self) -> None:
        prompt, substituted = cr.render_launcher_prompt(_EXPECTED_TEMPLATE)
        assert prompt == _EXPECTED_TEMPLATE
        assert substituted == set()

    def test_fills_plan_file_and_repo_leaves_developer_and_reviewer_untouched(self) -> None:
        prompt, substituted = cr.render_launcher_prompt(_EXPECTED_TEMPLATE, plan_file="/p/plan.md", repo="/p/repo")
        assert "Plan file: /p/plan.md" in prompt
        assert "Repo: /p/repo" in prompt
        assert "Developer: harness <codex|claude|copilot|opencode|qwen> model <model name>" in prompt
        assert "Reviewer: harness <codex|claude|copilot|opencode|qwen> model <model name>" in prompt
        assert substituted == {"plan_file", "repo"}


# --- pretrust_repo_for_harness ------------------------------------------------


class TestAtomicWriteText:
    def test_preserves_the_original_files_permission_bits(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.json"
        config_path.write_text("{}", encoding="utf-8")
        config_path.chmod(0o600)

        cr._atomic_write_text(config_path, '{"changed": true}')

        assert config_path.stat().st_mode & 0o777 == 0o600
        assert config_path.read_text(encoding="utf-8") == '{"changed": true}'

    def test_writes_through_a_symlink_leaving_the_symlink_itself_intact(self, tmp_path: Path) -> None:
        real_target = tmp_path / "real-config.json"
        real_target.write_text("{}", encoding="utf-8")
        link_path = tmp_path / "config.json"
        link_path.symlink_to(real_target)

        cr._atomic_write_text(link_path, '{"changed": true}')

        assert link_path.is_symlink()
        assert link_path.resolve() == real_target
        assert real_target.read_text(encoding="utf-8") == '{"changed": true}'

    def test_leaves_no_stray_temp_file_behind(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.json"
        config_path.write_text("{}", encoding="utf-8")

        cr._atomic_write_text(config_path, "{}")
        cr._atomic_write_text(config_path, "{}")  # a second call must not collide with the first

        assert [p.name for p in tmp_path.iterdir()] == ["config.json"]


class TestPretrustClaude:
    def test_missing_config_file_is_reported_not_raised(self, tmp_path: Path) -> None:
        message = cr._pretrust_claude("/repo/path", tmp_path / "does-not-exist.json")
        assert "installed/configured" in message

    def test_creates_a_fresh_entry_with_the_minimal_shape(self, tmp_path: Path) -> None:
        config_path = tmp_path / "claude.json"
        config_path.write_text(json.dumps({"numStartups": 3, "projects": {"/other/repo": {"hasTrustDialogAccepted": True}}}), encoding="utf-8")

        message = cr._pretrust_claude("/new/trial/repo", config_path)

        assert "pre-trusted" in message
        data = json.loads(config_path.read_text(encoding="utf-8"))
        assert data["numStartups"] == 3  # untouched sibling top-level key
        assert data["projects"]["/other/repo"] == {"hasTrustDialogAccepted": True}  # untouched sibling project
        new_entry = data["projects"]["/new/trial/repo"]
        assert new_entry["hasTrustDialogAccepted"] is True
        assert new_entry["allowedTools"] == []

    def test_existing_untrusted_entry_is_merged_not_replaced(self, tmp_path: Path) -> None:
        config_path = tmp_path / "claude.json"
        config_path.write_text(
            json.dumps({"projects": {"/repo": {"hasTrustDialogAccepted": False, "lastSessionId": "abc123"}}}),
            encoding="utf-8",
        )

        cr._pretrust_claude("/repo", config_path)

        entry = json.loads(config_path.read_text(encoding="utf-8"))["projects"]["/repo"]
        assert entry["hasTrustDialogAccepted"] is True
        assert entry["lastSessionId"] == "abc123"  # preserved, not wiped by a full replace

    def test_already_trusted_is_a_no_op(self, tmp_path: Path) -> None:
        config_path = tmp_path / "claude.json"
        original = json.dumps({"projects": {"/repo": {"hasTrustDialogAccepted": True, "lastSessionId": "abc123"}}})
        config_path.write_text(original, encoding="utf-8")

        message = cr._pretrust_claude("/repo", config_path)

        assert "already trusts" in message
        assert config_path.read_text(encoding="utf-8") == original


class TestPretrustCodex:
    def test_missing_config_file_is_reported_not_raised(self, tmp_path: Path) -> None:
        message = cr._pretrust_codex("/repo/path", tmp_path / "does-not-exist.toml")
        assert "installed/configured" in message

    def test_appends_a_trust_table_leaving_existing_content_untouched(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.toml"
        original = 'model = "some-model"\n\n[projects."/other/repo"]\ntrust_level = "trusted"\n'
        config_path.write_text(original, encoding="utf-8")

        message = cr._pretrust_codex("/new/trial/repo", config_path)

        assert "pre-trusted" in message
        text = config_path.read_text(encoding="utf-8")
        assert text.startswith(original)  # append-only: existing bytes preserved verbatim
        parsed = tomllib.loads(text)
        assert parsed["projects"]["/other/repo"]["trust_level"] == "trusted"
        assert parsed["projects"]["/new/trial/repo"]["trust_level"] == "trusted"

    def test_already_present_is_a_no_op(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.toml"
        original = '[projects."/repo"]\ntrust_level = "trusted"\n'
        config_path.write_text(original, encoding="utf-8")

        message = cr._pretrust_codex("/repo", config_path)

        assert "already trusts" in message
        assert config_path.read_text(encoding="utf-8") == original

    def test_a_path_containing_a_newline_is_escaped_into_valid_toml(self, tmp_path: Path) -> None:
        # A worktree path is an arbitrary filesystem path and can legally
        # contain a newline (this repo's own worktree-listing tests already
        # treat that as real, not hypothetical) -- a naive f-string
        # interpolation would embed a raw newline inside the TOML table
        # header and corrupt the whole document.
        config_path = tmp_path / "config.toml"
        config_path.write_text("", encoding="utf-8")
        odd_repo = "/repo/weird\nname"

        message = cr._pretrust_codex(odd_repo, config_path)

        assert "pre-trusted" in message
        parsed = tomllib.loads(config_path.read_text(encoding="utf-8"))
        assert parsed["projects"][odd_repo]["trust_level"] == "trusted"

    def test_existing_entry_with_a_different_trust_level_is_left_alone(self, tmp_path: Path) -> None:
        # A structural check (not a substring match) must recognize this as
        # "already has an entry, but not a trusted one" -- appending a
        # second [projects."/repo"] table would be invalid TOML (a
        # duplicate table), so this must refuse to touch the file rather
        # than corrupt it or falsely claim the directory is trusted.
        config_path = tmp_path / "config.toml"
        original = '[projects."/repo"]\ntrust_level = "untrusted"\n'
        config_path.write_text(original, encoding="utf-8")

        message = cr._pretrust_codex("/repo", config_path)

        assert "leaving it as-is" in message
        assert config_path.read_text(encoding="utf-8") == original
        assert config_path.read_text(encoding="utf-8").count('[projects."/repo"]') == 1


class TestPretrustCopilot:
    def test_missing_config_file_is_reported_not_raised(self, tmp_path: Path) -> None:
        message = cr._pretrust_copilot("/repo/path", tmp_path / "does-not-exist.json")
        assert "installed/configured" in message

    def test_appends_to_trusted_folders_preserving_leading_comments(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.json"
        config_path.write_text(
            '// User settings belong in settings.json.\n// This file is managed automatically.\n'
            '{\n  "trustedFolders": ["/other/repo"]\n}\n',
            encoding="utf-8",
        )

        message = cr._pretrust_copilot("/new/trial/repo", config_path)

        assert "pre-trusted" in message
        text = config_path.read_text(encoding="utf-8")
        assert text.startswith("// User settings belong in settings.json.\n// This file is managed automatically.\n")
        data = json.loads(text[text.index("{") :])
        assert set(data["trustedFolders"]) == {"/other/repo", "/new/trial/repo"}

    def test_missing_trusted_folders_key_is_created(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.json"
        config_path.write_text("{}\n", encoding="utf-8")

        cr._pretrust_copilot("/repo", config_path)

        assert json.loads(config_path.read_text(encoding="utf-8"))["trustedFolders"] == ["/repo"]

    def test_already_trusted_is_a_no_op(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.json"
        original = '{\n  "trustedFolders": [\n    "/repo"\n  ]\n}\n'
        config_path.write_text(original, encoding="utf-8")

        message = cr._pretrust_copilot("/repo", config_path)

        assert "already trusts" in message
        assert config_path.read_text(encoding="utf-8") == original

    def test_a_blank_line_between_leading_comments_is_tolerated(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.json"
        config_path.write_text(
            "// header one\n\n// header two\n{\n  \"trustedFolders\": []\n}\n",
            encoding="utf-8",
        )

        message = cr._pretrust_copilot("/repo", config_path)

        assert "pre-trusted" in message
        text = config_path.read_text(encoding="utf-8")
        assert text.startswith("// header one\n\n// header two\n")

    def test_a_comment_after_real_content_is_reported_not_guessed_at(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.json"
        original = '{\n  "trustedFolders": []\n}\n// a trailing comment, not a leading one\n'
        config_path.write_text(original, encoding="utf-8")

        message = cr._pretrust_copilot("/repo", config_path)

        assert "not modified" in message
        assert config_path.read_text(encoding="utf-8") == original


class TestPretrustOpencodeAndQwen:
    def test_opencode_names_why_it_is_not_automated(self) -> None:
        message = cr._pretrust_opencode("/repo")
        assert "SQLite" in message
        assert "/repo" in message

    def test_qwen_names_why_it_is_not_automated(self) -> None:
        message = cr._pretrust_qwen("/repo")
        assert "no persistent per-directory trust store" in message
        assert "/repo" in message


class TestPretrustRepoForHarness:
    def test_dispatches_to_claude(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        config_path = tmp_path / "claude.json"
        config_path.write_text("{}\n", encoding="utf-8")
        monkeypatch.setitem(cr._HARNESS_TRUST_CONFIG_PATHS, "claude", config_path)

        message = cr.pretrust_repo_for_harness("claude", "/repo")

        assert "pre-trusted" in message
        assert json.loads(config_path.read_text(encoding="utf-8"))["projects"]["/repo"]["hasTrustDialogAccepted"] is True

    def test_dispatches_to_codex(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        config_path = tmp_path / "config.toml"
        config_path.write_text("", encoding="utf-8")
        monkeypatch.setitem(cr._HARNESS_TRUST_CONFIG_PATHS, "codex", config_path)

        message = cr.pretrust_repo_for_harness("codex", "/repo")

        assert "pre-trusted" in message

    def test_dispatches_to_copilot(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        config_path = tmp_path / "config.json"
        config_path.write_text("{}\n", encoding="utf-8")
        monkeypatch.setitem(cr._HARNESS_TRUST_CONFIG_PATHS, "copilot", config_path)

        message = cr.pretrust_repo_for_harness("copilot", "/repo")

        assert "pre-trusted" in message

    def test_dispatches_to_opencode_and_qwen_without_needing_a_config_path(self) -> None:
        assert "not automated" in cr.pretrust_repo_for_harness("opencode", "/repo")
        assert "not automated" in cr.pretrust_repo_for_harness("qwen", "/repo")

    def test_an_unexpected_failure_is_caught_and_reported_not_raised(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        config_path = tmp_path / "claude.json"
        config_path.write_text("not valid json", encoding="utf-8")
        monkeypatch.setitem(cr._HARNESS_TRUST_CONFIG_PATHS, "claude", config_path)

        message = cr.pretrust_repo_for_harness("claude", "/repo")

        assert "could not pre-trust" in message


# --- prebuild_dev_venv --------------------------------------------------------


class TestPrebuildDevVenv:
    def test_no_setup_script_is_reported_and_skipped(self, tmp_path: Path) -> None:
        message = cr.prebuild_dev_venv(tmp_path, timeout_seconds=60)
        assert f"no {tmp_path / 'setup.sh'} found -- skipped venv pre-build" == message

    def test_successful_setup_script_is_reported(self, tmp_path: Path) -> None:
        (tmp_path / "setup.sh").write_text(
            "#!/usr/bin/env bash\nmkdir -p venv/bin\ntouch venv/bin/python\n", encoding="utf-8"
        )
        message = cr.prebuild_dev_venv(tmp_path, timeout_seconds=60)
        assert message == f"pre-built venv/ in {tmp_path} via {tmp_path / 'setup.sh'}"
        assert (tmp_path / "venv" / "bin" / "python").is_file()

    def test_failing_setup_script_is_reported_not_raised(self, tmp_path: Path) -> None:
        (tmp_path / "setup.sh").write_text(
            "#!/usr/bin/env bash\necho 'no network' >&2\nexit 1\n", encoding="utf-8"
        )
        message = cr.prebuild_dev_venv(tmp_path, timeout_seconds=60)
        assert "failed (exit 1)" in message
        assert "no network" in message
        assert "Developer will need to build it themselves" in message

    def test_timeout_is_reported_not_raised(self, tmp_path: Path) -> None:
        (tmp_path / "setup.sh").write_text("#!/usr/bin/env bash\nsleep 5\n", encoding="utf-8")
        message = cr.prebuild_dev_venv(tmp_path, timeout_seconds=1)
        assert "timed out after 1s" in message
        assert "Developer will need to build it themselves" in message


# --- setup (CLI) -------------------------------------------------------------


class TestRunSetup:
    def test_no_harness_given_prints_the_not_pretrusted_note(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        skill_dir = _write_skill_md(tmp_path)
        dev_repo = _make_prepared_repo(tmp_path)
        policy_path = _write_policy(tmp_path, skill_dir, tasks={TASK_ID: _task_entry(dev_repo)}, default_task=TASK_ID)
        rc = cr.main(["--policy", str(policy_path), "setup", "--repo", str(dev_repo)])
        assert rc == 0
        assert "no --harness given" in capsys.readouterr().out

    def test_explicit_task_flag_behaves_identically_to_omitting_it(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Acceptance criterion: `setup --task relative-velocity` behaves
        # identically to the no-flag case against the single-task policy --
        # compared byte for byte over the whole printed output, modulo the
        # two repos' own paths (which necessarily differ between invocations).
        skill_dir = _write_skill_md(tmp_path)
        repo_a = _make_prepared_repo(tmp_path, name="prepared-a")
        repo_b = _make_prepared_repo(tmp_path, name="prepared-b")
        policy_path = _write_policy(tmp_path, skill_dir, tasks={TASK_ID: _task_entry(repo_a)}, default_task=TASK_ID)

        rc_default = cr.main(["--policy", str(policy_path), "setup", "--repo", str(repo_a)])
        out_default = capsys.readouterr().out
        rc_explicit = cr.main(["--policy", str(policy_path), "setup", "--repo", str(repo_b), "--task", TASK_ID])
        out_explicit = capsys.readouterr().out

        assert rc_default == 0
        assert rc_explicit == 0

        def normalize(text: str, repo: Path) -> str:
            return text.replace(str(repo.resolve()), "<REPO>").replace(str(repo), "<REPO>")

        assert normalize(out_default, repo_a) == normalize(out_explicit, repo_b)

    def test_unknown_task_id_is_a_named_error_naming_configured_ids(self, tmp_path: Path) -> None:
        skill_dir = _write_skill_md(tmp_path)
        dev_repo = _make_prepared_repo(tmp_path)
        policy_path = _write_policy(tmp_path, skill_dir, tasks={TASK_ID: _task_entry(dev_repo)}, default_task=TASK_ID)
        with pytest.raises(cr.CohortRunError, match=r"unknown task 'ghost-task'; configured tasks: relative-velocity"):
            cr.main(["--policy", str(policy_path), "setup", "--repo", str(dev_repo), "--task", "ghost-task"])

    def test_harness_given_prints_the_pretrust_result(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        skill_dir = _write_skill_md(tmp_path)
        dev_repo = _make_prepared_repo(tmp_path)
        policy_path = _write_policy(tmp_path, skill_dir, tasks={TASK_ID: _task_entry(dev_repo)}, default_task=TASK_ID)
        claude_config = tmp_path / "claude.json"
        claude_config.write_text("{}\n", encoding="utf-8")
        monkeypatch.setitem(cr._HARNESS_TRUST_CONFIG_PATHS, "claude", claude_config)

        rc = cr.main(["--policy", str(policy_path), "setup", "--harness", "claude", "--repo", str(dev_repo)])

        assert rc == 0
        out = capsys.readouterr().out
        assert f"pre-trusted {dev_repo} in {claude_config}" in out
        assert json.loads(claude_config.read_text(encoding="utf-8"))["projects"][str(dev_repo)]["hasTrustDialogAccepted"] is True

    def test_unrecognized_harness_is_rejected_by_argparse(self, tmp_path: Path) -> None:
        with pytest.raises(SystemExit):
            cr.main(["setup", "--harness", "not-a-real-harness"])

    def test_venv_prebuild_status_is_printed(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        skill_dir = _write_skill_md(tmp_path)
        dev_repo = _make_prepared_repo(tmp_path)
        policy_path = _write_policy(
            tmp_path, skill_dir, tasks={TASK_ID: _task_entry(dev_repo)}, default_task=TASK_ID, subprocess_timeout_seconds=123
        )
        calls: list[tuple[Path, int]] = []
        monkeypatch.setattr(
            cr, "prebuild_dev_venv", lambda repo, timeout_seconds: calls.append((repo, timeout_seconds)) or "PREBUILD-STATUS"
        )

        rc = cr.main(["--policy", str(policy_path), "setup", "--repo", str(dev_repo)])

        assert rc == 0
        assert "cohort_run.py: PREBUILD-STATUS" in capsys.readouterr().out
        assert calls == [(dev_repo.resolve(), 123)]

    def test_prints_prompt_and_steps(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        # --repo given: the manual escape hatch, so no worktree creation is
        # attempted (create_dev_worktree is exercised separately, below).
        skill_dir = _write_skill_md(tmp_path)
        dev_repo = _make_prepared_repo(tmp_path)
        policy_path = _write_policy(tmp_path, skill_dir, tasks={TASK_ID: _task_entry(dev_repo)}, default_task=TASK_ID)
        rc = cr.main(["--policy", str(policy_path), "setup", "--repo", str(dev_repo)])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Developer: harness <codex|claude|copilot|opencode|qwen> model <model name>" in out
        assert "Reviewer: harness <codex|claude|copilot|opencode|qwen> model <model name>" in out
        assert f"Repo: {dev_repo}" in out
        assert f"Plan file: {dev_repo / 'docs' / 'MERGER_RATE_PLAN-2SLICE.md'}" in out
        assert "Steps to follow" in out
        assert f"python tools/cohort_run.py analyze --dev-repo {dev_repo}" in out
        # The plan note names the actually-resolved task and its actual plan
        # file path, and claims exclusivity only because exactly one task is
        # configured here.
        assert "exactly one frozen plan" in out
        assert f"(docs/MERGER_RATE_PLAN-2SLICE.md, vendored from {TASK_ID} at a pinned commit" in out
        # --repo given manually: this tool created no trial worktree of its
        # own for it, so there is nothing for `cleanup` to remove -- the
        # cleanup step must not be printed.
        assert "cohort_run.py cleanup" not in out

    def test_removed_model_flag_is_rejected(self, tmp_path: Path) -> None:
        # Who plays Developer/Reviewer is the operator's own choice made in
        # the pasted prompt -- setup carries no flag for either. A stray
        # reimplementation of --model must fail argparse's own
        # unrecognized-argument check, not silently start working again.
        # (--harness *is* a real flag again, but scoped to directory-trust
        # pre-registration only -- see test_harness_given_prints_the_pretrust_result
        # and test_unrecognized_harness_is_rejected_by_argparse, both of which
        # exercise it through a fully isolated fixture, never real machine state.)
        with pytest.raises(SystemExit):
            cr.main(["setup", "--model", "claude-sonnet-5"])

    def test_label_or_base_commit_with_repo_is_a_named_error(self, tmp_path: Path) -> None:
        # The refusal fires before any policy/SKILL.md read, so no fixture
        # beyond the raw policy file is needed here.
        policy_path = _raw_policy_file(tmp_path)
        with pytest.raises(cr.CohortRunError, match="only apply when creating a new worktree"):
            cr.main(["--policy", str(policy_path), "setup", "--repo", str(tmp_path), "--label", "x"])

    def test_nonexistent_repo_is_a_named_error(self, tmp_path: Path) -> None:
        skill_dir = _write_skill_md(tmp_path)
        policy_path = _write_policy(
            tmp_path, skill_dir, tasks={TASK_ID: _task_entry(str(tmp_path / "substrate"))}, default_task=TASK_ID
        )
        with pytest.raises(cr.CohortRunError, match="is not an existing directory"):
            cr.main(["--policy", str(policy_path), "setup", "--repo", str(tmp_path / "does-not-exist")])

    def test_repo_with_no_frozen_plan_at_the_fixed_path_is_a_named_error(self, tmp_path: Path) -> None:
        skill_dir = _write_skill_md(tmp_path)
        policy_path = _write_policy(
            tmp_path, skill_dir, tasks={TASK_ID: _task_entry(str(tmp_path / "substrate"))}, default_task=TASK_ID
        )
        empty_repo = tmp_path / "empty-repo"
        empty_repo.mkdir()
        with pytest.raises(cr.CohortRunError, match="has no docs/MERGER_RATE_PLAN-2SLICE.md"):
            cr.main(["--policy", str(policy_path), "setup", "--repo", str(empty_repo)])

    def test_nonexistent_plan_file_override_is_a_named_error(self, tmp_path: Path) -> None:
        skill_dir = _write_skill_md(tmp_path)
        policy_path = _write_policy(
            tmp_path, skill_dir, tasks={TASK_ID: _task_entry(str(tmp_path / "substrate"))}, default_task=TASK_ID
        )
        dev_repo = _make_prepared_repo(tmp_path)
        with pytest.raises(cr.CohortRunError, match="is not an existing file"):
            cr.main(
                [
                    "--policy",
                    str(policy_path),
                    "setup",
                    "--repo",
                    str(dev_repo),
                    "--plan-file",
                    str(tmp_path / "does-not-exist.md"),
                ]
            )

    def test_nonexistent_plan_file_override_is_a_named_error_without_repo_too(self, tmp_path: Path) -> None:
        # The same validation must apply when --repo is omitted (auto-create
        # a worktree) and only --plan-file is overridden -- not just the
        # manual --repo path.
        skill_dir = _write_skill_md(tmp_path)
        substrate_repo, commit = _make_substrate_repo(tmp_path)
        policy_path = _write_policy(
            tmp_path,
            skill_dir,
            tasks={TASK_ID: _task_entry(substrate_repo, worktree_root=tmp_path / "worktrees")},
            default_task=TASK_ID,
        )
        with pytest.raises(cr.CohortRunError, match="is not an existing file"):
            cr.main(
                [
                    "--policy",
                    str(policy_path),
                    "setup",
                    "--label",
                    "bad-plan-file",
                    "--base-commit",
                    commit,
                    "--plan-file",
                    str(tmp_path / "does-not-exist.md"),
                ]
            )
        # And it must fail before create_dev_worktree runs, leaving nothing
        # behind for this to be a real "nothing happened" refusal.
        assert cr.list_bench_worktrees(substrate_repo, "pm-eval-v2") == []

    def test_relative_repo_is_printed_as_an_absolute_path(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # A relative --repo must never be echoed back verbatim: Repo:/Plan
        # file: are promised "already correct" regardless of the cwd the
        # printed prompt is later read from.
        skill_dir = _write_skill_md(tmp_path)
        dev_repo = _make_prepared_repo(tmp_path, name="rel-dev-repo")
        policy_path = _write_policy(tmp_path, skill_dir, tasks={TASK_ID: _task_entry(dev_repo)}, default_task=TASK_ID)
        monkeypatch.chdir(tmp_path)

        rc = cr.main(["--policy", str(policy_path), "setup", "--repo", "rel-dev-repo"])

        assert rc == 0
        out = capsys.readouterr().out
        assert f"Repo: {dev_repo.resolve()}" in out
        assert "Repo: rel-dev-repo" not in out

    def test_no_repo_given_creates_a_worktree_and_points_the_prompt_at_it(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        skill_dir = _write_skill_md(tmp_path)
        substrate_repo, commit = _make_substrate_repo(tmp_path)
        worktree_root = tmp_path / "worktrees"
        policy_path = _write_policy(
            tmp_path,
            skill_dir,
            tasks={TASK_ID: _task_entry(substrate_repo, worktree_root=worktree_root)},
            default_task=TASK_ID,
        )

        rc = cr.main(
            ["--policy", str(policy_path), "setup", "--label", "trial-1", "--base-commit", commit]
        )

        assert rc == 0
        out = capsys.readouterr().out
        expected_worktree = worktree_root / f"{substrate_repo.name}-trial-1"
        assert f"created worktree {expected_worktree}" in out
        assert f"Repo: {expected_worktree}" in out
        assert f"Plan file: {expected_worktree / 'docs' / 'MERGER_RATE_PLAN-2SLICE.md'}" in out
        assert (expected_worktree / "docs" / "MERGER_RATE_PLAN-2SLICE.md").is_file()
        # setup created this trial: the concrete --dev-repo/--label go
        # straight into the printed steps, no <...> placeholder for either.
        assert f"python tools/cohort_run.py analyze --dev-repo {expected_worktree}" in out
        # The default task needs no --task on either follow-up command: the
        # printed steps are identical to those of a single-task bench.
        steps = out.split("Prompt to paste")[0]
        assert "python tools/cohort_run.py cleanup --label trial-1` removes its worktree" in steps
        assert "--task" not in steps

    def test_printed_followup_commands_name_the_resolved_non_default_task_explicitly(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Both printed follow-up commands (analyze AND cleanup) must carry the
        # resolved task id explicitly. Here two configured tasks SHARE one
        # repo, so a non-default trial whose printed commands omitted --task
        # could never be graded or cleaned up later at all: analyze's
        # inference would refuse as ambiguous and cleanup would silently act
        # under default_task's pair. The resolved id goes into each printed
        # command itself, always.
        skill_dir = _write_skill_md(tmp_path)
        substrate_repo, commit = _make_substrate_repo(tmp_path)
        worktree_root = tmp_path / "worktrees"
        policy_path = _write_policy(
            tmp_path,
            skill_dir,
            tasks={
                TASK_ID: _task_entry(substrate_repo, worktree_root=worktree_root),
                "other-task": _task_entry(substrate_repo, worktree_root=worktree_root),
            },
            default_task=TASK_ID,
        )

        rc = cr.main(
            [
                "--policy",
                str(policy_path),
                "setup",
                "--label",
                "trial-other",
                "--base-commit",
                commit,
                "--task",
                "other-task",
            ]
        )

        assert rc == 0
        out = capsys.readouterr().out
        expected_worktree = worktree_root / f"{substrate_repo.name}-trial-other"
        assert f"created worktree {expected_worktree}" in out
        assert f"python tools/cohort_run.py analyze --dev-repo {expected_worktree} --task other-task" in out
        assert "python tools/cohort_run.py cleanup --label trial-other --task other-task" in out

    def test_default_task_setup_names_task_explicitly_when_several_tasks_are_configured(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # With --task omitted, analyze infers the task from --dev-repo and
        # never falls back to default_task, so under a multi-task policy the
        # default task's printed commands need the flag too.
        skill_dir = _write_skill_md(tmp_path)
        substrate_repo, commit = _make_substrate_repo(tmp_path)
        worktree_root = tmp_path / "worktrees"
        policy_path = _write_policy(
            tmp_path,
            skill_dir,
            tasks={
                TASK_ID: _task_entry(substrate_repo, worktree_root=worktree_root),
                "other-task": _task_entry(substrate_repo, worktree_root=worktree_root),
            },
            default_task=TASK_ID,
        )

        rc = cr.main(["--policy", str(policy_path), "setup", "--label", "trial-default", "--base-commit", commit])

        assert rc == 0
        out = capsys.readouterr().out
        expected_worktree = worktree_root / f"{substrate_repo.name}-trial-default"
        assert f"python tools/cohort_run.py analyze --dev-repo {expected_worktree} --task {TASK_ID}" in out
        assert f"python tools/cohort_run.py cleanup --label trial-default --task {TASK_ID}" in out

    def test_invalid_policy_is_a_named_cohortrunerror_not_a_raw_devcheckerror(self, tmp_path: Path) -> None:
        # A policy.yaml missing dev_check.py's own required keys must still
        # fail as this tool's own named error, not an unhandled
        # dev_check.DevCheckError traceback escaping main().
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text(yaml.safe_dump({"backend": "local"}), encoding="utf-8")
        with pytest.raises(cr.CohortRunError, match="missing required keys"):
            cr.main(["--policy", str(policy_path), "setup"])

    def test_missing_skill_md_is_a_named_error(self, tmp_path: Path) -> None:
        skill_dir = tmp_path / "project-manager"
        (skill_dir / "scripts").mkdir(parents=True)
        policy_path = _write_policy(
            tmp_path, skill_dir, tasks={TASK_ID: _task_entry(str(tmp_path / "substrate"))}, default_task=TASK_ID
        )
        with pytest.raises(cr.CohortRunError, match="SKILL.md not found"):
            cr.main(["--policy", str(policy_path), "setup"])

    def test_plan_note_for_multiple_tasks_names_resolved_task_and_drops_exclusivity_claim(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Acceptance criterion: with more than one configured task, the note
        # names the actually-resolved task and its actual plan file path, and
        # does NOT claim there's only ever one plan. The second task carries
        # a DIFFERENT plan filename so a stale single-task constant could not
        # accidentally satisfy this.
        other_plan = "docs/OTHER_TASK_PLAN.md"
        prepared = _make_prepared_repo(tmp_path, name="other-dev-repo")
        (prepared / "docs" / "OTHER_TASK_PLAN.md").write_text("frozen plan\n", encoding="utf-8")
        skill_dir = _write_skill_md(tmp_path)
        policy_path = _write_policy(
            tmp_path,
            skill_dir,
            tasks={
                TASK_ID: _task_entry(prepared),
                "other-task": _task_entry(prepared, plan_file=other_plan),
            },
            default_task=TASK_ID,
        )

        rc = cr.main(["--policy", str(policy_path), "setup", "--repo", str(prepared), "--task", "other-task"])

        assert rc == 0
        out = capsys.readouterr().out
        assert "configures 2 tasks" in out
        assert f"task other-task's plan ({other_plan}" in out
        assert "exactly one frozen plan" not in out
        # ...and the prompt itself still derives Plan file: from the resolved
        # task's own plan_file, not any leftover hardcoded path.
        assert f"Plan file: {prepared / other_plan}" in out

    def test_warns_when_a_given_field_has_no_matching_template_line(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        skill_dir = _write_skill_md(tmp_path, text="# PM\n\n## Launcher\n\n```md\nNothing to fill here.\n```\n")
        dev_repo = _make_prepared_repo(tmp_path)
        policy_path = _write_policy(tmp_path, skill_dir, tasks={TASK_ID: _task_entry(dev_repo)}, default_task=TASK_ID)
        rc = cr.main(["--policy", str(policy_path), "setup", "--repo", str(dev_repo)])
        assert rc == 0
        err = capsys.readouterr().err
        assert "--repo was given but the launcher template has no matching 'repo' line" in err


# --- _read_run_id -------------------------------------------------------------


class TestReadRunId:
    def test_missing_run_json_is_a_named_error(self, tmp_path: Path) -> None:
        with pytest.raises(cr.CohortRunError, match="no run.json"):
            cr._read_run_id(tmp_path)

    def test_invalid_json_is_a_named_error(self, tmp_path: Path) -> None:
        (tmp_path / "run.json").write_text("{not json", encoding="utf-8")
        with pytest.raises(cr.CohortRunError, match="not valid JSON"):
            cr._read_run_id(tmp_path)

    def test_missing_run_id_field_is_a_named_error(self, tmp_path: Path) -> None:
        (tmp_path / "run.json").write_text(json.dumps({"status": "complete"}), encoding="utf-8")
        with pytest.raises(cr.CohortRunError, match="run_id"):
            cr._read_run_id(tmp_path)

    def test_non_string_run_id_is_a_named_error_not_a_typeerror(self, tmp_path: Path) -> None:
        # A truthy but non-string run_id (e.g. malformed JSON producing a
        # number) must be rejected here, not passed on to a caller that
        # builds a Path from it and hits an uncaught TypeError instead.
        (tmp_path / "run.json").write_text(json.dumps({"run_id": 20260101}), encoding="utf-8")
        with pytest.raises(cr.CohortRunError, match="non-empty string 'run_id'"):
            cr._read_run_id(tmp_path)

    def test_valid_run_json_returns_run_id(self, tmp_path: Path) -> None:
        (tmp_path / "run.json").write_text(json.dumps({"run_id": "20260101T000000Z-abc"}), encoding="utf-8")
        assert cr._read_run_id(tmp_path) == "20260101T000000Z-abc"


# --- resolve_run_dir_from_dev_repo -------------------------------------------


def _recording_main(label: str, calls: list[tuple[str, list[str]]]) -> Any:
    """A fake tool `main(argv)` that records its own label and argv rather
    than doing anything -- shared by every TestRunAnalyze test that needs to
    see what cohort_run.py actually called each tool with."""

    def fake(argv: list[str]) -> int:
        calls.append((label, argv))
        return 0

    return fake


def _make_git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "dev-repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    return repo


def _make_substrate_repo(tmp_path: Path, *, name: str = "relative-velocity", with_plan: bool = True) -> tuple[Path, str]:
    """A throwaway git repo standing in for relative-velocity: one commit,
    optionally carrying docs/MERGER_RATE_PLAN-2SLICE.md (the frozen plan
    every trial worktree must have). Returns (repo_path, commit_sha)."""
    repo = tmp_path / name
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    if with_plan:
        (repo / "docs").mkdir()
        (repo / "docs" / "MERGER_RATE_PLAN-2SLICE.md").write_text("frozen plan\n", encoding="utf-8")
    else:
        (repo / "README.md").write_text("no plan here\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=repo, check=True)
    commit = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()
    return repo, commit


class TestResolveTaskOrError:
    def test_broken_registry_fails_as_cohortrunerror_not_bare_benchliberror(self) -> None:
        # main() catches CohortRunError specifically, not its BenchLibError
        # parent -- a broken tasks: registry must surface under this tool's
        # own named error type, exactly like load_policy wraps DevCheckError.
        with pytest.raises(cr.CohortRunError, match="missing its required non-empty 'tasks' mapping"):
            cr._resolve_task_or_error({}, None)

    def test_unknown_task_id_names_it_and_the_configured_ids(self) -> None:
        policy = {"default_task": TASK_ID, "tasks": {TASK_ID: _task_entry("/some/repo")}}
        with pytest.raises(cr.CohortRunError, match=r"unknown task 'ghost'; configured tasks: relative-velocity"):
            cr._resolve_task_or_error(policy, "ghost")


class TestTaskWorktreeLayout:
    """The (repo, branch_prefix, worktree_root) resolution every
    worktree-creating/removing path shares, now driven by one RESOLVED task
    entry rather than flat policy keys."""

    def _resolved(
        self, repo: str | Path, *, prefix: str = "pm-eval-v2", worktree_root: str | Path | None = None
    ) -> dict[str, Any]:
        return _resolved_task(TASK_ID, _task_entry(repo, branch_prefix=prefix, worktree_root=worktree_root))

    def test_not_a_git_repo_is_a_named_error(self, tmp_path: Path) -> None:
        not_a_repo = tmp_path / "not-a-repo"
        not_a_repo.mkdir()
        with pytest.raises(cr.CohortRunError, match="does not look like a git repository"):
            cr._task_worktree_layout(self._resolved(not_a_repo), tmp_path)

    def test_worktree_root_defaults_to_repo_parent(self, tmp_path: Path) -> None:
        repo, _ = _make_substrate_repo(tmp_path)
        resolved_repo, prefix, worktree_root = cr._task_worktree_layout(self._resolved(repo), tmp_path)
        assert resolved_repo == repo.resolve()
        assert prefix == "pm-eval-v2"
        assert worktree_root == repo.resolve().parent

    def test_worktree_root_override_is_honored(self, tmp_path: Path) -> None:
        repo, _ = _make_substrate_repo(tmp_path)
        override = tmp_path / "custom-worktrees"
        _, _, worktree_root = cr._task_worktree_layout(self._resolved(repo, worktree_root=str(override)), tmp_path)
        assert worktree_root == override.resolve()

    def test_relative_repo_and_worktree_root_resolve_against_root_not_cwd(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # policy.yaml is checked-in, portable config -- a relative value in
        # it must resolve against this bench's own repo root, never whatever
        # directory the operator happened to run the command from.
        bench_root = tmp_path / "bench-root"
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        (bench_root / "substrate").mkdir(parents=True)
        repo, _ = _make_substrate_repo(bench_root / "substrate", name="relative-velocity")
        monkeypatch.chdir(elsewhere)

        resolved_repo, _, worktree_root = cr._task_worktree_layout(
            self._resolved("substrate/relative-velocity", worktree_root="substrate"),
            bench_root,
        )

        assert resolved_repo == repo.resolve()
        assert worktree_root == (bench_root / "substrate").resolve()


class TestCreateDevWorktree:
    def _task(self, repo: Path, worktree_root: Path, *, prefix: str = "pm-eval-v2") -> dict[str, Any]:
        return _resolved_task(TASK_ID, _task_entry(repo, branch_prefix=prefix, worktree_root=worktree_root))

    def test_creates_worktree_on_the_expected_branch_at_the_given_commit(self, tmp_path: Path) -> None:
        repo, commit = _make_substrate_repo(tmp_path)
        worktree_root = tmp_path / "worktrees"
        task = self._task(repo, worktree_root)

        worktree_path, branch_name, label = cr.create_dev_worktree(
            task, tmp_path, label="explicit-label", base_commit=commit
        )

        assert label == "explicit-label"
        assert branch_name == "pm-eval-v2/explicit-label"
        assert worktree_path == (worktree_root / f"{repo.name}-explicit-label").resolve()
        assert (worktree_path / "docs" / "MERGER_RATE_PLAN-2SLICE.md").is_file()
        assert label in cr.list_bench_branches(repo, "pm-eval-v2")

    def test_relative_task_paths_resolve_against_root_not_cwd(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Threading `root` through to _task_worktree_layout is only real if
        # this caller (not just that helper in isolation) actually creates
        # the worktree under bench_root, even when invoked from some other
        # cwd -- exactly how the checked-in relative task repo/worktree_root
        # values are used in practice.
        bench_root = tmp_path / "bench-root"
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        (bench_root / "substrate").mkdir(parents=True)
        repo, commit = _make_substrate_repo(bench_root / "substrate", name="relative-velocity")
        task = _resolved_task(TASK_ID, _task_entry("substrate/relative-velocity", worktree_root="substrate"))
        monkeypatch.chdir(elsewhere)

        worktree_path, _, label = cr.create_dev_worktree(task, bench_root, label="rel-trial", base_commit=commit)

        assert label == "rel-trial"
        assert worktree_path == (bench_root / "substrate" / "relative-velocity-rel-trial").resolve()
        assert worktree_path.is_dir()
        assert not (elsewhere / "substrate").exists()

    def test_auto_label_defaults_to_trial_and_auto_numbers(self, tmp_path: Path) -> None:
        repo, commit = _make_substrate_repo(tmp_path)
        worktree_root = tmp_path / "worktrees"
        task = self._task(repo, worktree_root)

        _, _, label1 = cr.create_dev_worktree(task, tmp_path, label=None, base_commit=commit)
        _, _, label2 = cr.create_dev_worktree(task, tmp_path, label=None, base_commit=commit)

        assert label1 == "trial-1"
        assert label2 == "trial-2"

    def test_explicit_label_colliding_with_existing_branch_is_a_named_error(self, tmp_path: Path) -> None:
        repo, commit = _make_substrate_repo(tmp_path)
        worktree_root = tmp_path / "worktrees"
        task = self._task(repo, worktree_root)
        cr.create_dev_worktree(task, tmp_path, label="dup", base_commit=commit)

        with pytest.raises(cr.CohortRunError, match="already has a branch"):
            cr.create_dev_worktree(task, tmp_path, label="dup", base_commit=commit)

    def test_missing_plan_file_at_base_commit_is_a_named_error_and_leaves_no_orphaned_worktree(
        self, tmp_path: Path
    ) -> None:
        repo, commit = _make_substrate_repo(tmp_path, with_plan=False)
        worktree_root = tmp_path / "worktrees"
        task = self._task(repo, worktree_root)

        with pytest.raises(cr.CohortRunError, match="has no docs/MERGER_RATE_PLAN-2SLICE.md"):
            cr.create_dev_worktree(task, tmp_path, label="no-plan", base_commit=commit)

        # The half-created worktree must not be left behind, registered or
        # on disk, for a later `setup`/`cleanup` to trip over.
        assert not (worktree_root / f"{repo.name}-no-plan").exists()
        assert cr.list_bench_worktrees(repo, "pm-eval-v2") == []
        # ... and the branch it was on must be gone too, or a retry with the
        # same --label would wrongly refuse as "already has a branch" even
        # though nothing usable was actually left behind.
        assert "no-plan" not in cr.list_bench_branches(repo, "pm-eval-v2")

    def test_worktree_add_failing_after_creation_is_rolled_back(self, tmp_path: Path) -> None:
        # `git worktree add` can exit nonzero (e.g. a failing post-checkout
        # hook) while still leaving the branch and worktree fully created --
        # verified for real against this machine's own git (2.50.1): the
        # worktree and branch are both registered despite the nonzero exit.
        repo, commit = _make_substrate_repo(tmp_path)
        hooks_dir = repo / ".git" / "hooks"
        hook = hooks_dir / "post-checkout"
        hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        hook.chmod(0o755)
        worktree_root = tmp_path / "worktrees"
        task = self._task(repo, worktree_root)

        with pytest.raises(cr.CohortRunError, match="worktree add"):
            cr.create_dev_worktree(task, tmp_path, label="hook-fail", base_commit=commit)

        assert not (worktree_root / f"{repo.name}-hook-fail").exists()
        assert cr.list_bench_worktrees(repo, "pm-eval-v2") == []
        assert "hook-fail" not in cr.list_bench_branches(repo, "pm-eval-v2")

    def test_base_commit_defaults_to_the_pinned_provenance_commit(self, tmp_path: Path) -> None:
        repo, commit = _make_substrate_repo(tmp_path)
        worktree_root = tmp_path / "worktrees"
        task = self._task(repo, worktree_root)
        (tmp_path / "docs").mkdir(exist_ok=True)
        (tmp_path / "docs" / "MERGER_RATE_PLAN-2SLICE.provenance.md").write_text(
            f"Pinned commit: `{commit}`\n", encoding="utf-8"
        )

        worktree_path, _, _ = cr.create_dev_worktree(task, tmp_path, label="pinned", base_commit=None)

        checked_out = subprocess.run(
            ["git", "-C", str(worktree_path), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
        assert checked_out == commit

    def test_missing_provenance_at_the_call_site_raises_cohortrunerror_not_bare_benchliberror(
        self, tmp_path: Path
    ) -> None:
        # The relocated function raises bench_lib.BenchLibError; this call
        # site must re-raise it as CohortRunError with the same message, so
        # main()'s own handler -- which catches CohortRunError specifically,
        # not its BenchLibError parent -- keeps the exact CLI-boundary
        # behavior for a missing/unparsable provenance file.
        repo, _commit = _make_substrate_repo(tmp_path)
        worktree_root = tmp_path / "worktrees"
        task = self._task(repo, worktree_root)

        with pytest.raises(cr.CohortRunError, match="not found"):
            cr.create_dev_worktree(task, tmp_path, label="no-prov", base_commit=None)


class TestListBenchWorktreesAndBranches:
    def test_filters_by_branch_prefix(self, tmp_path: Path) -> None:
        repo, commit = _make_substrate_repo(tmp_path)
        worktree_root = tmp_path / "worktrees"
        task = _resolved_task(TASK_ID, _task_entry(repo, worktree_root=worktree_root))
        cr.create_dev_worktree(task, tmp_path, label="a", base_commit=commit)
        subprocess.run(
            ["git", "-C", str(repo), "worktree", "add", "-b", "other-prefix/x", str(worktree_root / "other"), commit],
            check=True,
        )

        worktrees = cr.list_bench_worktrees(repo, "pm-eval-v2")
        assert len(worktrees) == 1
        assert worktrees[0]["branch"] == "refs/heads/pm-eval-v2/a"

        branches = cr.list_bench_branches(repo, "pm-eval-v2")
        assert branches == {"a"}

    def test_a_worktree_path_containing_a_newline_is_still_parsed_as_one_entry(self, tmp_path: Path) -> None:
        # A worktree path is an arbitrary filesystem path and can legally
        # contain a newline (unlike a branch name) -- a line-based parse of
        # plain `--porcelain` output would misread it as two entries or a
        # corrupted field; `-z` (NUL-delimited) must not.
        repo, commit = _make_substrate_repo(tmp_path)
        odd_path = tmp_path / "weird\nname"
        subprocess.run(
            ["git", "-C", str(repo), "worktree", "add", "-b", "pm-eval-v2/odd", str(odd_path), commit], check=True
        )

        worktrees = cr.list_bench_worktrees(repo, "pm-eval-v2")

        assert len(worktrees) == 1
        assert worktrees[0]["worktree"] == str(odd_path)
        assert worktrees[0]["branch"] == "refs/heads/pm-eval-v2/odd"


class TestResolveRunDirFromDevRepo:
    def test_no_pm_dir_is_a_named_error(self, tmp_path: Path) -> None:
        repo = _make_git_repo(tmp_path)
        with pytest.raises(cr.CohortRunError, match="has PM ever run"):
            cr.resolve_run_dir_from_dev_repo(repo)

    def test_empty_pm_dir_is_a_named_error(self, tmp_path: Path) -> None:
        repo = _make_git_repo(tmp_path)
        (repo / ".git" / "pm").mkdir()
        with pytest.raises(cr.CohortRunError, match="no run directories"):
            cr.resolve_run_dir_from_dev_repo(repo)

    def test_single_run_dir_is_returned(self, tmp_path: Path) -> None:
        repo = _make_git_repo(tmp_path)
        run_dir = repo / ".git" / "pm" / "20260101T000000Z-abc"
        run_dir.mkdir(parents=True)
        assert cr.resolve_run_dir_from_dev_repo(repo).resolve() == run_dir.resolve()

    def test_multiple_run_dirs_is_a_named_error_listing_both(self, tmp_path: Path) -> None:
        repo = _make_git_repo(tmp_path)
        (repo / ".git" / "pm" / "run-a").mkdir(parents=True)
        (repo / ".git" / "pm" / "run-b").mkdir(parents=True)
        with pytest.raises(cr.CohortRunError, match="2 run directories"):
            cr.resolve_run_dir_from_dev_repo(repo)

    def test_not_a_git_repo_is_a_named_error(self, tmp_path: Path) -> None:
        not_a_repo = tmp_path / "not-a-repo"
        not_a_repo.mkdir()
        with pytest.raises(cr.CohortRunError, match="rev-parse"):
            cr.resolve_run_dir_from_dev_repo(not_a_repo)


# --- _call_tool ---------------------------------------------------------------


class TestCallTool:
    def test_success_returns_the_tools_own_exit_code(self) -> None:
        assert cr._call_tool(lambda argv: 0, "fake.py", []) == 0

    def test_named_problems_exit_code_is_passed_through(self) -> None:
        assert cr._call_tool(lambda argv: 1, "fake.py", []) == 1

    def test_a_raised_benchliberror_is_caught_and_reported(self, capsys: pytest.CaptureFixture[str]) -> None:
        def raiser(argv: list[str]) -> int:
            raise bench_lib.BenchLibError("boom")

        rc = cr._call_tool(raiser, "fake.py", [])
        assert rc == 1
        assert "fake.py refused: boom" in capsys.readouterr().err


# --- analyze --------------------------------------------------------------


class TestRunAnalyze:
    RUN_ID = "20260101T000000Z-abc"

    def _fixture(self, tmp_path: Path) -> tuple[Path, Path]:
        """Returns (fake_bench_root, run_dir). The fake root carries a
        single-task policy.yaml so main()'s own bench_root()/default-policy
        resolution stays hermetic -- these tests must never read this repo's
        checked-in policy.yaml."""
        root = tmp_path / "bench-root"
        root.mkdir()
        _raw_policy_file(root, name="policy.yaml")
        run_dir = root / "pm-run"
        run_dir.mkdir()
        (run_dir / "run.json").write_text(json.dumps({"run_id": self.RUN_ID}), encoding="utf-8")
        return root, run_dir

    def test_runs_all_three_tools_in_order_with_expected_argv(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root, run_dir = self._fixture(tmp_path)
        monkeypatch.setattr(cr, "bench_root", lambda: root)
        calls: list[tuple[str, list[str]]] = []

        monkeypatch.setattr(cr.grade_run, "main", _recording_main("grade_run", calls))
        monkeypatch.setattr(cr.model_report, "main", _recording_main("model_report", calls))
        monkeypatch.setattr(cr.leaderboard, "main", _recording_main("leaderboard", calls))

        rc = cr.main(["analyze", "--run-dir", str(run_dir)])

        assert rc == 0
        assert [label for label, _ in calls] == ["grade_run", "model_report", "leaderboard"]
        # --task is ALWAYS forwarded to grade_run.py: it names the task this
        # analyze invocation resolved (here the sole configured one), so
        # grading can never silently fall back to default_task.
        assert calls[0][1] == ["--run-dir", str(run_dir.resolve()), "--task", TASK_ID]
        # --run-dir is forwarded to model_report.py too, so its `timing`
        # block can actually be computed under normal `analyze` usage.
        assert calls[1][1] == ["--run-id", self.RUN_ID, "--run-dir", str(run_dir.resolve())]
        assert calls[2][1] == []

    def test_exit_code_is_the_max_across_steps(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        root, run_dir = self._fixture(tmp_path)
        monkeypatch.setattr(cr, "bench_root", lambda: root)
        monkeypatch.setattr(cr.grade_run, "main", lambda argv: 0)
        monkeypatch.setattr(cr.model_report, "main", lambda argv: 1)
        monkeypatch.setattr(cr.leaderboard, "main", lambda argv: 0)
        rc = cr.main(["analyze", "--run-dir", str(run_dir)])
        assert rc == 1

    def test_skip_leaderboard_does_not_call_leaderboard(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        root, run_dir = self._fixture(tmp_path)
        monkeypatch.setattr(cr, "bench_root", lambda: root)
        monkeypatch.setattr(cr.grade_run, "main", lambda argv: 0)
        monkeypatch.setattr(cr.model_report, "main", lambda argv: 0)

        def fail_if_called(argv: list[str]) -> int:
            raise AssertionError("leaderboard.main should not have been called")

        monkeypatch.setattr(cr.leaderboard, "main", fail_if_called)
        rc = cr.main(["analyze", "--run-dir", str(run_dir), "--skip-leaderboard"])
        assert rc == 0

    def test_grade_run_refusal_still_runs_later_steps(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        # A hard refusal (e.g. the run isn't finished yet) is reported, not
        # fatal to the whole pipeline -- model_report.py/leaderboard.py still
        # run, exactly as they would for any other model's already-graded
        # data on disk (see cohort_run.py's own _call_tool docstring).
        root, run_dir = self._fixture(tmp_path)
        monkeypatch.setattr(cr, "bench_root", lambda: root)
        calls: list[str] = []

        def raiser(argv: list[str]) -> int:
            raise bench_lib.BenchLibError("run not finished")

        monkeypatch.setattr(cr.grade_run, "main", raiser)
        monkeypatch.setattr(cr.model_report, "main", lambda argv: calls.append("model_report") or 0)
        monkeypatch.setattr(cr.leaderboard, "main", lambda argv: calls.append("leaderboard") or 0)

        rc = cr.main(["analyze", "--run-dir", str(run_dir)])
        assert rc == 1
        assert calls == ["model_report", "leaderboard"]

    def test_dev_repo_resolves_run_dir_when_run_dir_not_given(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root, run_dir = self._fixture(tmp_path)
        monkeypatch.setattr(cr, "bench_root", lambda: root)
        dev_repo = tmp_path / "dev-repo"
        dev_repo.mkdir()
        monkeypatch.setattr(cr, "resolve_run_dir_from_dev_repo", lambda repo: run_dir)
        monkeypatch.setattr(cr.grade_run, "main", lambda argv: 0)
        monkeypatch.setattr(cr.model_report, "main", lambda argv: 0)
        monkeypatch.setattr(cr.leaderboard, "main", lambda argv: 0)

        rc = cr.main(["analyze", "--dev-repo", str(dev_repo)])
        assert rc == 0

    def test_run_dir_and_dev_repo_are_mutually_exclusive(self, tmp_path: Path) -> None:
        with pytest.raises(SystemExit):
            cr.main(["analyze", "--run-dir", str(tmp_path), "--dev-repo", str(tmp_path)])

    def test_policy_override_is_forwarded_to_every_tool_including_model_report(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Slice 4 criterion: an operator's custom --policy must reach ALL
        # three downstream tools, including model_report -- before this slice
        # the report built between grading and refolding silently resolved
        # its own task registry from the bench-root default instead.
        root, run_dir = self._fixture(tmp_path)
        monkeypatch.setattr(cr, "bench_root", lambda: root)
        policy_path = tmp_path / "custom-policy.yaml"
        _raw_policy_file(tmp_path, name="custom-policy.yaml")
        calls: list[tuple[str, list[str]]] = []

        monkeypatch.setattr(cr.grade_run, "main", _recording_main("grade_run", calls))
        monkeypatch.setattr(cr.model_report, "main", _recording_main("model_report", calls))
        monkeypatch.setattr(cr.leaderboard, "main", _recording_main("leaderboard", calls))

        cr.main(["--policy", str(policy_path), "analyze", "--run-dir", str(run_dir)])

        grade_argv = dict(calls)["grade_run"]
        report_argv = dict(calls)["model_report"]
        board_argv = dict(calls)["leaderboard"]
        assert grade_argv == ["--run-dir", str(run_dir.resolve()), "--task", TASK_ID, "--policy", str(policy_path)]
        assert report_argv == ["--run-id", self.RUN_ID, "--run-dir", str(run_dir.resolve()), "--policy", str(policy_path)]
        assert board_argv == ["--policy", str(policy_path)]


class TestAnalyzeTaskInference:
    """Slice 4 criterion: when --task is omitted, `analyze` resolves which
    task to grade under from the run's own worktree membership; an explicit
    --task always wins. The membership primitive itself
    (bench_lib.repo_belongs_to_task) has its own tests -- here we verify the
    wiring around it: every configured task is consulted, exactly one match
    wins, anything else is a named refusal telling the operator to pass
    --task explicitly, never a silent guess."""

    RUN_ID = "20260101T000000Z-abc"

    def _two_task_policy(self, tmp_path: Path) -> dict[str, Any]:
        return {
            "default_task": TASK_ID,
            "tasks": {
                TASK_ID: _task_entry(str(tmp_path / "substrate-a")),
                "other-task": _task_entry(str(tmp_path / "substrate-b")),
            },
        }

    def test_single_configured_task_is_taken_by_construction_without_any_membership_check(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Today's starting state: with exactly one configured task there is
        # nothing to disambiguate -- even `analyze --run-dir` alone (no
        # worktree path exists to infer from at all) must resolve it without
        # touching git.
        root = tmp_path / "bench-root"
        root.mkdir()
        policy = {"default_task": TASK_ID, "tasks": {TASK_ID: _task_entry(str(tmp_path / "substrate"))}}

        def fail_if_called(*_args: Any, **_kwargs: Any) -> bool:
            raise AssertionError("repo_belongs_to_task must not be consulted for a single task")

        monkeypatch.setattr(bench_lib, "repo_belongs_to_task", fail_if_called)

        task = cr._resolve_analyze_task(policy, root, task_id=None, dev_repo=None)
        assert task["task_id"] == TASK_ID

    def test_dev_repo_matching_exactly_one_task_resolves_that_task(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = tmp_path / "bench-root"
        root.mkdir()
        policy = self._two_task_policy(tmp_path)
        monkeypatch.setattr(
            bench_lib,
            "repo_belongs_to_task",
            lambda candidate, configured: Path(configured).name == "substrate-b",
        )

        task = cr._resolve_analyze_task(policy, root, task_id=None, dev_repo=tmp_path / "trial-wt")

        assert task["task_id"] == "other-task"

    def test_dev_repo_matching_several_tasks_is_a_named_error_naming_them(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = tmp_path / "bench-root"
        root.mkdir()
        policy = self._two_task_policy(tmp_path)
        monkeypatch.setattr(bench_lib, "repo_belongs_to_task", lambda candidate, configured: True)

        with pytest.raises(
            cr.CohortRunError,
            match=r"is a worktree of more than one configured task \(other-task, relative-velocity\).*pass --task explicitly",
        ):
            cr._resolve_analyze_task(policy, root, task_id=None, dev_repo=tmp_path / "shared-wt")

    def test_multiple_tasks_with_no_dev_repo_is_a_named_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # `analyze --run-dir` alone gives no worktree path to infer ownership
        # from -- with several tasks that must be a refusal, not a default.
        root = tmp_path / "bench-root"
        root.mkdir()
        policy = self._two_task_policy(tmp_path)

        def fail_if_called(*_args: Any, **_kwargs: Any) -> bool:
            raise AssertionError("inference must refuse before consulting any repo")

        monkeypatch.setattr(bench_lib, "repo_belongs_to_task", fail_if_called)

        with pytest.raises(
            cr.CohortRunError,
            match=r"2 tasks are configured \(other-task, relative-velocity\) but no --dev-repo was given.*pass --task explicitly",
        ):
            cr._resolve_analyze_task(policy, root, task_id=None, dev_repo=None)

    def test_explicit_task_flag_wins_over_inference_and_validates_the_id(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root = tmp_path / "bench-root"
        root.mkdir()
        policy = self._two_task_policy(tmp_path)

        def fail_if_called(*_args: Any, **_kwargs: Any) -> bool:
            raise AssertionError("an explicit --task must never fall through to inference")

        monkeypatch.setattr(bench_lib, "repo_belongs_to_task", fail_if_called)

        task = cr._resolve_analyze_task(policy, root, task_id="other-task", dev_repo=tmp_path / "trial-wt")
        assert task["task_id"] == "other-task"

        with pytest.raises(cr.CohortRunError, match=r"unknown task 'ghost'; configured tasks"):
            cr._resolve_analyze_task(policy, root, task_id="ghost", dev_repo=None)

    def test_git_failure_during_membership_check_is_a_named_error_naming_the_task(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # repo_belongs_to_task raises (never returns False) on git failure or
        # enclosing-repo ambiguity; this call site must surface it as a named
        # CohortRunError identifying which task's check failed -- here
        # 'other-task', the first one consulted in sorted order.
        root = tmp_path / "bench-root"
        root.mkdir()
        policy = self._two_task_policy(tmp_path)

        def boom(candidate: Path, configured: Path) -> bool:
            raise bench_lib.BenchLibError("git exploded")

        monkeypatch.setattr(bench_lib, "repo_belongs_to_task", boom)

        with pytest.raises(
            cr.CohortRunError,
            match=r"could not determine whether .* belongs to task 'other-task': git exploded",
        ):
            cr._resolve_analyze_task(policy, root, task_id=None, dev_repo=tmp_path / "trial-wt")

    def test_oserror_during_membership_check_is_a_named_error_not_a_raw_traceback(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Unlike its BenchLibError, an OSError here comes from OUTSIDE
        # bench_lib: repo_belongs_to_task's internal subprocess.run(['git',
        # ...]) raises FileNotFoundError when git is unavailable or
        # PermissionError when it cannot be executed. This call site catches
        # both (exactly like dev_check.py's identical call), so either must
        # surface as this tool's named CohortRunError naming the failing
        # task -- never escape as a raw traceback.
        root = tmp_path / "bench-root"
        root.mkdir()
        policy = self._two_task_policy(tmp_path)

        def boom(candidate: Path, configured: Path) -> bool:
            raise FileNotFoundError("git")

        monkeypatch.setattr(bench_lib, "repo_belongs_to_task", boom)

        # (OSError.__str__ renders a single-argument instance as that
        # argument alone, hence the bare 'git' suffix.)
        with pytest.raises(
            cr.CohortRunError,
            match=r"could not determine whether .* belongs to task 'other-task': git$",
        ):
            cr._resolve_analyze_task(policy, root, task_id=None, dev_repo=tmp_path / "trial-wt")

    def test_mixed_type_tasks_keys_are_a_named_error_not_a_raw_typeerror_on_both_inference_paths(
        self, tmp_path: Path
    ) -> None:
        # YAML parses unquoted numeric-looking keys as int, so a hand-edited
        # policy can mix string and non-string tasks: keys; the whole registry
        # must be validated BEFORE any sorted()/join() over that key set runs,
        # or the refusal message itself crashes with a raw TypeError instead
        # of resolve_task's named error -- from BOTH inference entry shapes
        # (--run-dir alone, and --dev-repo given).
        root = tmp_path / "bench-root"
        root.mkdir()
        policy = {
            "default_task": TASK_ID,
            "tasks": {
                TASK_ID: _task_entry(str(tmp_path / "substrate-a")),
                2: _task_entry(str(tmp_path / "substrate-b")),
            },
        }
        for dev_repo in (None, tmp_path / "trial-wt"):
            with pytest.raises(cr.CohortRunError, match=r"keyed by non-empty task-id strings"):
                cr._resolve_analyze_task(policy, root, task_id=None, dev_repo=dev_repo)

    def _real_two_task_bench(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path, Path]:
        """A bench root whose policy configures two REAL throwaway git repos
        (substrate-a, substrate-b), plus an unrelated third repo. Returns
        (root, substrate_b, stray_repo)."""
        root = tmp_path / "bench-root"
        root.mkdir()
        (root / "policy.yaml").write_text(yaml.safe_dump(self._two_task_policy(tmp_path)), encoding="utf-8")
        _make_substrate_repo(tmp_path, name="substrate-a")
        substrate_b, _ = _make_substrate_repo(tmp_path, name="substrate-b")
        stray, _ = _make_substrate_repo(tmp_path, name="stray")
        monkeypatch.setattr(cr, "bench_root", lambda: root)
        return root, substrate_b, stray

    def _add_worktree_with_run(self, repo: Path, name: str) -> tuple[Path, Path]:
        """A real `git worktree` of `repo` carrying one PM run directory;
        returns (worktree, run_dir)."""
        worktree = repo.parent / name
        subprocess.run(["git", "-C", str(repo), "worktree", "add", "-q", "-b", name, str(worktree)], check=True)
        run_dir = _worktree_gitdir(worktree) / "pm" / self.RUN_ID
        run_dir.mkdir(parents=True)
        (run_dir / "run.json").write_text(json.dumps({"run_id": self.RUN_ID}), encoding="utf-8")
        return worktree, run_dir

    def test_main_level_inference_reaches_grade_run_argv(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        # End-to-end through argparse with real git: two configured tasks,
        # --dev-repo a real worktree of task B's own repo, no --task flag →
        # grade_run.py receives --task other-task. (--dev-repo alone: --run-dir
        # is its documented alternative and mutually exclusive with it.)
        _root, substrate_b, _stray = self._real_two_task_bench(tmp_path, monkeypatch)
        worktree, run_dir = self._add_worktree_with_run(substrate_b, "trial-b")
        calls: list[tuple[str, list[str]]] = []
        monkeypatch.setattr(cr.grade_run, "main", _recording_main("grade_run", calls))
        monkeypatch.setattr(cr.model_report, "main", lambda argv: 0)
        monkeypatch.setattr(cr.leaderboard, "main", lambda argv: 0)

        rc = cr.main(["analyze", "--dev-repo", str(worktree)])

        assert rc == 0
        assert calls[0][1] == ["--run-dir", str(run_dir.resolve()), "--task", "other-task"]

    def test_main_level_dev_repo_matching_no_task_is_a_named_error_and_grades_nothing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Real git: --dev-repo is a worktree of a repo no configured task
        # names, so inference refuses by name and never reaches grading.
        _root, _substrate_b, stray = self._real_two_task_bench(tmp_path, monkeypatch)
        worktree, _run_dir = self._add_worktree_with_run(stray, "trial-stray")
        calls: list[tuple[str, list[str]]] = []
        monkeypatch.setattr(cr.grade_run, "main", _recording_main("grade_run", calls))

        with pytest.raises(
            cr.CohortRunError,
            match=r"belongs to none of the configured tasks \(other-task, relative-velocity\).*pass --task explicitly",
        ):
            cr.main(["analyze", "--dev-repo", str(worktree)])

        assert calls == []


class TestAnalyzePolicyForwardingEndToEnd:
    """Slice 4 criterion, verified by effect rather than argv alone: the
    report model_report.py writes between grading and refolding must be built
    against the SAME policy file analyze was told to use. The fixture gives
    the default and custom policies different `obligations_file`s whose rubrics
    name different node ids, so a sheet graded under one of them can only be
    reported successfully against that same one."""

    RUN_ID = "20260101T000000Z-abc"

    def _rubric(self, group_id: str, node_id: str) -> dict[str, Any]:
        return {"slices": {1: {"obligations": [{"id": group_id, "tests": [node_id]}]}}}

    def _full_policy_file(self, path: Path, *, obligations_file: str) -> Path:
        # A complete policy passing dev_check.load_policy (model_report.py's
        # loader) -- the same shape `_write_policy` builds for setup tests.
        # load_policy checks key presence, never referenced-file existence.
        base = path.parent
        policy = {
            "backend": "local",
            "pm_scripts_dir": str(base / "project-manager" / "scripts"),
            "lint_script": str(base / "lint.py"),
            "health_script": str(base / "health.py"),
            "python_interpreter": str(base / "python3"),
            "subprocess_timeout_seconds": 600,
            "measurement": {
                "loc_definition": "net_physical_lines",
                "loc_category_definition": "ast_tokenize_line_classification",
                "metric_version": 2,
            },
            "default_task": TASK_ID,
            "tasks": {TASK_ID: _task_entry(str(path.parent / "substrate"), obligations_file=obligations_file)},
        }
        path.write_text(yaml.safe_dump(policy), encoding="utf-8")
        return path

    def _fixture(self, tmp_path: Path) -> tuple[Path, Path, Path]:
        """Returns (fake_bench_root, run_dir, sheet_dir). The fake root holds
        BOTH rubrics plus a default policy pointing at the DEFAULT one; the
        custom policy (written next to it in tmp_path) points at the CUSTOM
        one. The single sheet is graded under the custom rubric."""
        root = tmp_path / "bench-root"
        hidden = root / "hidden_tests"
        hidden.mkdir(parents=True)
        default_rubric = self._rubric("G-DEFAULT", "tests/test_d.py::test_one")
        custom_rubric = self._rubric("G-CUSTOM", "tests/test_c.py::test_one")
        (hidden / "obligations-default.yaml").write_text(yaml.safe_dump(default_rubric), encoding="utf-8")
        (hidden / "obligations-custom.yaml").write_text(yaml.safe_dump(custom_rubric), encoding="utf-8")
        self._full_policy_file(root / "policy.yaml", obligations_file="hidden_tests/obligations-default.yaml")

        run_dir = root / "pm-run"
        run_dir.mkdir()
        (run_dir / "run.json").write_text(json.dumps({"run_id": self.RUN_ID}), encoding="utf-8")
        events = [
            {"kind": "init", "ts": "2026-01-01T00:00:00+00:00"},
            {"kind": "complete", "ts": "2026-01-01T01:00:00+00:00"},
        ]
        (run_dir / "events.jsonl").write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")

        groups = dev_check.obligation_groups_for_slice(custom_rubric, 1)
        outcomes = {node: "passed" for group in groups for node in group["tests"]}
        correctness = dev_check.score_correctness(outcomes, groups, 1)
        attempt = {
            "attempt": 0,
            "pm_attempts_counter": 0,
            "commit_sha": "sha-0",
            "correctness": correctness,
            "quality": {"lint_findings_by_tool": {}, "code_health_findings_by_category": {}},
            "scope": {"violations": []},
            "pm_decision": "accept",
            "reviews": [],
            "provenance": {
                "task_id": TASK_ID,
                "plan_hash": "plan-hash",
                "policy_hash": "policy-hash",
                "obligations_hash": "obligations-hash",
                "hidden_tests_hash": "hidden-tests-hash",
                "base_commit": "before-head",
                "pm_skill_version": None,
            },
        }
        sheet = {
            "run_id": self.RUN_ID,
            "developer": {
                "harness": "opencode",
                "model": "opencode/some-model",
                "effort": "low",
                "configuration_key": "opencode/some-model · opencode · low",
                "sources": {"harness": "run_harness", "model": "run_harness", "effort": "run_harness"},
                "attributed": True,
                "attestation": None,
            },
            "slice": 1,
            "run_status": {
                "pm_status": "complete",
                "slice_status": "accepted",
                "stop_reason": "done",
                "infrastructure_failure_suspected": False,
            },
            "attempts": [attempt],
            "accepted_at_attempt": 0,
            "pm_model_performance_ref": None,
        }
        sheet_dir = root / "results" / "runs" / self.RUN_ID
        sheet_dir.mkdir(parents=True)
        (sheet_dir / "slice-1.json").write_text(json.dumps(sheet), encoding="utf-8")
        return root, run_dir, sheet_dir

    def test_custom_policy_reaches_model_report_and_the_report_is_built_against_it(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        root, run_dir, _sheet_dir = self._fixture(tmp_path)
        custom_policy = self._full_policy_file(
            tmp_path / "custom-policy.yaml", obligations_file="hidden_tests/obligations-custom.yaml"
        )
        # Both cohort_run's and model_report's own bench_root must point at
        # the fixture -- model_report resolves its sheets, out path, AND its
        # obligations file against ITS OWN copy of that function.
        monkeypatch.setattr(cr, "bench_root", lambda: root)
        monkeypatch.setattr(cr.model_report, "bench_root", lambda: root)
        monkeypatch.setattr(cr.grade_run, "main", lambda argv: 0)
        monkeypatch.setattr(cr.leaderboard, "main", lambda argv: 0)

        rc = cr.main(["--policy", str(custom_policy), "analyze", "--run-dir", str(run_dir)])

        assert rc == 0
        report = json.loads((root / "results" / "runs" / self.RUN_ID / "model-report.json").read_text())
        # The nested map is keyed by the CUSTOM rubric's own group id -- proof
        # model_report.py read the custom policy's obligations_file, not the
        # bench-root default's.
        assert set(report["slices"][0]["first_attempt_node_outcomes"]) == {"G-CUSTOM"}

    def test_without_the_flag_the_default_policy_governs_and_the_mismatched_sheet_is_refused(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Control direction: the same sheet graded under the custom rubric,
        # reported with NO --policy override → model_report resolves its task
        # from the bench-root default policy (the DEFAULT rubric) and must
        # refuse loudly on the unknown node, never write a report, and fail
        # the pipeline -- proving the two policies are observably different
        # downstream, which is what makes the forwarding above load-bearing.
        root, run_dir, sheet_dir = self._fixture(tmp_path)
        monkeypatch.setattr(cr, "bench_root", lambda: root)
        monkeypatch.setattr(cr.model_report, "bench_root", lambda: root)
        monkeypatch.setattr(cr.grade_run, "main", lambda argv: 0)
        monkeypatch.setattr(cr.leaderboard, "main", lambda argv: 0)

        rc = cr.main(["analyze", "--run-dir", str(run_dir)])

        assert rc == 1
        err = capsys.readouterr().err
        assert "model_report.py refused" in err
        assert "tests/test_c.py::test_one" in err
        assert not (sheet_dir / "model-report.json").exists()


# --- cleanup (trial worktrees) ----------------------------------------------


def _worktree_gitdir(worktree_path: Path) -> Path:
    out = subprocess.run(
        ["git", "-C", str(worktree_path), "rev-parse", "--absolute-git-dir"], capture_output=True, text=True, check=True
    ).stdout.strip()
    return Path(out)


class TestRunCleanupWorktrees:
    def _fixture(self, tmp_path: Path) -> tuple[Path, Path, Path, str]:
        """Returns (bench_root, policy_path, substrate_repo, base_commit)."""
        substrate_repo, commit = _make_substrate_repo(tmp_path)
        worktree_root = tmp_path / "worktrees"
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text(
            yaml.safe_dump(
                {
                    "default_task": TASK_ID,
                    "tasks": {TASK_ID: _task_entry(substrate_repo, worktree_root=worktree_root)},
                }
            ),
            encoding="utf-8",
        )
        bench_root = tmp_path / "bench-root"
        bench_root.mkdir()
        return bench_root, policy_path, substrate_repo, commit

    def _args(
        self,
        policy_path: Path,
        *,
        label: str | None = None,
        yes: bool = False,
        force: bool = False,
        task: str | None = None,
    ) -> Any:
        return type("Args", (), {"policy": policy_path, "label": label, "yes": yes, "force": force, "task": task})()

    def _make_trial(self, bench_root: Path, policy_path: Path, commit: str, label: str = "trial-1") -> tuple[Path, str]:
        """Create one trial worktree from an already-written policy.yaml --
        returns (worktree_path, branch_name)."""
        policy = yaml.safe_load(policy_path.read_text())
        task = bench_lib.resolve_task(policy, None)
        worktree_path, branch_name, _ = cr.create_dev_worktree(task, bench_root, label=label, base_commit=commit)
        return worktree_path, branch_name

    def test_relative_task_paths_resolve_against_root_not_cwd(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The `_fixture` policy above always uses absolute paths, so it can
        # never catch `root` being silently ignored -- this exercises a
        # relative task repo/worktree_root end to end through run_cleanup
        # itself (not just _task_worktree_layout in isolation), from a cwd
        # that is neither bench_root nor the repo.
        bench_root = tmp_path / "bench-root"
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()
        (bench_root / "substrate").mkdir(parents=True)
        substrate_repo, commit = _make_substrate_repo(bench_root / "substrate", name="relative-velocity")
        policy_path = bench_root / "policy.yaml"
        policy_path.write_text(
            yaml.safe_dump(
                {
                    "default_task": TASK_ID,
                    "tasks": {TASK_ID: _task_entry("substrate/relative-velocity", worktree_root="substrate")},
                }
            ),
            encoding="utf-8",
        )
        worktree_path, _ = self._make_trial(bench_root, policy_path, commit, label="rel-trial")
        monkeypatch.chdir(elsewhere)

        rc = cr.run_cleanup(self._args(policy_path), bench_root)

        assert rc == 0
        out = capsys.readouterr().out
        assert str(worktree_path) in out
        assert not (elsewhere / "substrate").exists()

    def test_task_flag_scopes_discovery_to_that_tasks_own_worktrees(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Two configured tasks, one trial under EACH: --task must consider
        # only its own task's repo/branch-prefix pair, never the other's.
        # The flag names a GENUINELY non-default task id, so a regression
        # that ignored args.task and fell back to default_task would list
        # the wrong worktree and fail these assertions.
        repo_a, commit_a = _make_substrate_repo(tmp_path, name="substrate-a")
        repo_b, commit_b = _make_substrate_repo(tmp_path, name="substrate-b")
        worktree_root = tmp_path / "worktrees"
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text(
            yaml.safe_dump(
                {
                    "default_task": "task-a",
                    "tasks": {
                        "task-a": _task_entry(repo_a, worktree_root=worktree_root),
                        "task-b": _task_entry(repo_b, worktree_root=worktree_root),
                    },
                }
            ),
            encoding="utf-8",
        )
        bench_root = tmp_path / "bench-root"
        bench_root.mkdir()
        policy = yaml.safe_load(policy_path.read_text())
        wt_a, _, _ = cr.create_dev_worktree(
            bench_lib.resolve_task(policy, "task-a"), bench_root, label="trial-a", base_commit=commit_a
        )
        wt_b, _, _ = cr.create_dev_worktree(
            bench_lib.resolve_task(policy, "task-b"), bench_root, label="trial-b", base_commit=commit_b
        )

        rc = cr.run_cleanup(self._args(policy_path, task="task-b"), bench_root)

        assert rc == 0
        out = capsys.readouterr().out
        assert str(wt_b) in out
        assert str(wt_a) not in out
        assert "dry run only" in out

    def test_dry_run_lists_without_removing(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        bench_root, policy_path, substrate_repo, commit = self._fixture(tmp_path)
        worktree_path, branch_name = self._make_trial(bench_root, policy_path, commit)

        rc = cr.run_cleanup(self._args(policy_path), bench_root)

        assert rc == 0
        out = capsys.readouterr().out
        assert f"{worktree_path} (branch {branch_name})" in out
        assert "would remove" in out
        assert worktree_path.is_dir()
        assert "trial-1" in cr.list_bench_branches(substrate_repo, "pm-eval-v2")

    def test_yes_removes_worktree_but_keeps_branch(self, tmp_path: Path) -> None:
        bench_root, policy_path, substrate_repo, commit = self._fixture(tmp_path)
        worktree_path, _ = self._make_trial(bench_root, policy_path, commit)

        rc = cr.run_cleanup(self._args(policy_path, yes=True), bench_root)

        assert rc == 0
        assert not worktree_path.exists()
        assert "trial-1" in cr.list_bench_branches(substrate_repo, "pm-eval-v2")

    def test_label_scopes_to_one_worktree(self, tmp_path: Path) -> None:
        bench_root, policy_path, substrate_repo, commit = self._fixture(tmp_path)
        worktree_1, _ = self._make_trial(bench_root, policy_path, commit, label="trial-1")
        worktree_2, _ = self._make_trial(bench_root, policy_path, commit, label="trial-2")

        rc = cr.run_cleanup(self._args(policy_path, label="trial-1", yes=True), bench_root)

        assert rc == 0
        assert not worktree_1.exists()
        assert worktree_2.is_dir()

    def test_unknown_label_is_a_named_error(self, tmp_path: Path) -> None:
        bench_root, policy_path, _, _ = self._fixture(tmp_path)
        with pytest.raises(cr.CohortRunError, match="no worktree found for label"):
            cr.run_cleanup(self._args(policy_path, label="does-not-exist"), bench_root)

    def test_no_worktrees_found_prints_message_and_returns_0(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        bench_root, policy_path, _, _ = self._fixture(tmp_path)
        rc = cr.run_cleanup(self._args(policy_path), bench_root)
        assert rc == 0
        assert "no pm-eval-v2/* trial worktrees found" in capsys.readouterr().out

    def test_ungraded_run_is_flagged_with_a_warning_but_still_listed(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        bench_root, policy_path, substrate_repo, commit = self._fixture(tmp_path)
        worktree_path, _ = self._make_trial(bench_root, policy_path, commit)
        (_worktree_gitdir(worktree_path) / "pm" / "run-abc").mkdir(parents=True)

        rc = cr.run_cleanup(self._args(policy_path), bench_root)

        assert rc == 0
        out = capsys.readouterr().out
        assert "WARNING: ungraded run(s): run-abc" in out
        assert worktree_path.is_dir()  # still just a dry run

    def test_graded_run_has_no_warning(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        bench_root, policy_path, substrate_repo, commit = self._fixture(tmp_path)
        worktree_path, _ = self._make_trial(bench_root, policy_path, commit)
        (_worktree_gitdir(worktree_path) / "pm" / "run-abc").mkdir(parents=True)
        report_dir = bench_root / "results" / "runs" / "run-abc"
        report_dir.mkdir(parents=True)
        (report_dir / "model-report.json").write_text("{}", encoding="utf-8")

        rc = cr.run_cleanup(self._args(policy_path), bench_root)

        assert rc == 0
        assert "WARNING" not in capsys.readouterr().out

    def test_dirty_worktree_needs_force_to_remove(self, tmp_path: Path) -> None:
        bench_root, policy_path, substrate_repo, commit = self._fixture(tmp_path)
        worktree_path, _ = self._make_trial(bench_root, policy_path, commit)
        (worktree_path / "uncommitted.txt").write_text("dirty\n", encoding="utf-8")

        rc_without_force = cr.run_cleanup(self._args(policy_path, yes=True), bench_root)
        assert rc_without_force == 1
        assert worktree_path.is_dir()

        rc_with_force = cr.run_cleanup(self._args(policy_path, yes=True, force=True), bench_root)
        assert rc_with_force == 0
        assert not worktree_path.exists()


# --- analyze-all --------------------------------------------------------------


class TestResolveUngradedRunDirs:
    def _fixture(self, tmp_path: Path) -> tuple[Path, Path, Path, str]:
        """Returns (bench_root, policy_path, substrate_repo, base_commit)."""
        substrate_repo, commit = _make_substrate_repo(tmp_path)
        worktree_root = tmp_path / "worktrees"
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text(
            yaml.safe_dump(
                {
                    "default_task": TASK_ID,
                    "tasks": {TASK_ID: _task_entry(substrate_repo, worktree_root=worktree_root)},
                }
            ),
            encoding="utf-8",
        )
        bench_root = tmp_path / "bench-root"
        bench_root.mkdir()
        return bench_root, policy_path, substrate_repo, commit

    def _make_trial(self, bench_root: Path, policy_path: Path, commit: str, label: str = "trial-1") -> Path:
        policy = yaml.safe_load(policy_path.read_text())
        task = bench_lib.resolve_task(policy, None)
        worktree_path, _branch_name, _ = cr.create_dev_worktree(task, bench_root, label=label, base_commit=commit)
        return worktree_path

    def _make_pm_run(self, worktree_path: Path, run_id: str, *, dir_name: str | None = None) -> Path:
        """Creates `<gitdir>/pm/<dir_name or run_id>/run.json` naming `run_id`
        as its own `run_id` field -- `dir_name` lets a test deliberately
        mismatch the directory name from the authoritative run_id."""
        run_dir = _worktree_gitdir(worktree_path) / "pm" / (dir_name or run_id)
        run_dir.mkdir(parents=True)
        (run_dir / "run.json").write_text(json.dumps({"run_id": run_id}), encoding="utf-8")
        return run_dir

    def test_no_worktrees_is_empty(self, tmp_path: Path) -> None:
        _bench_root, _policy_path, substrate_repo, _commit = self._fixture(tmp_path)
        pairs, problems = cr.resolve_ungraded_run_dirs(substrate_repo, "pm-eval-v2", tmp_path / "bench-root")
        assert pairs == []
        assert problems == []

    def test_ungraded_run_is_returned_graded_run_is_not(self, tmp_path: Path) -> None:
        bench_root, policy_path, substrate_repo, commit = self._fixture(tmp_path)
        worktree_path = self._make_trial(bench_root, policy_path, commit)
        ungraded_dir = self._make_pm_run(worktree_path, "run-ungraded")
        self._make_pm_run(worktree_path, "run-graded")
        report_dir = bench_root / "results" / "runs" / "run-graded"
        report_dir.mkdir(parents=True)
        (report_dir / "model-report.json").write_text("{}", encoding="utf-8")

        pairs, problems = cr.resolve_ungraded_run_dirs(substrate_repo, "pm-eval-v2", bench_root)

        assert [(run_id, run_dir.resolve()) for run_id, run_dir in pairs] == [("run-ungraded", ungraded_dir.resolve())]
        assert problems == []

    def test_spans_every_worktree(self, tmp_path: Path) -> None:
        bench_root, policy_path, substrate_repo, commit = self._fixture(tmp_path)
        worktree_1 = self._make_trial(bench_root, policy_path, commit, label="trial-1")
        worktree_2 = self._make_trial(bench_root, policy_path, commit, label="trial-2")
        run_1 = self._make_pm_run(worktree_1, "run-1")
        run_2 = self._make_pm_run(worktree_2, "run-2")

        pairs, problems = cr.resolve_ungraded_run_dirs(substrate_repo, "pm-eval-v2", bench_root)

        assert {(run_id, run_dir.resolve()) for run_id, run_dir in pairs} == {
            ("run-1", run_1.resolve()),
            ("run-2", run_2.resolve()),
        }
        assert problems == []

    def test_grading_status_keys_on_run_json_id_not_directory_name(self, tmp_path: Path) -> None:
        # A pm/ directory's own name is documented convention, not something
        # this function is allowed to trust blindly: this run's directory is
        # named "some-dir-name" but its run.json says its real run_id is
        # "real-run-id" -- the graded/ungraded check must key on the latter.
        bench_root, policy_path, substrate_repo, commit = self._fixture(tmp_path)
        worktree_path = self._make_trial(bench_root, policy_path, commit)
        self._make_pm_run(worktree_path, "real-run-id", dir_name="some-dir-name")
        report_dir = bench_root / "results" / "runs" / "real-run-id"
        report_dir.mkdir(parents=True)
        (report_dir / "model-report.json").write_text("{}", encoding="utf-8")

        pairs, problems = cr.resolve_ungraded_run_dirs(substrate_repo, "pm-eval-v2", bench_root)

        # Already graded under its real run_id -- must not be rediscovered
        # as ungraded just because "results/runs/some-dir-name/" is empty.
        assert pairs == []
        assert problems == []

    def test_unreadable_run_json_is_a_problem_not_a_crash(self, tmp_path: Path) -> None:
        bench_root, policy_path, substrate_repo, commit = self._fixture(tmp_path)
        worktree_path = self._make_trial(bench_root, policy_path, commit)
        good_dir = self._make_pm_run(worktree_path, "run-good")
        bad_dir = _worktree_gitdir(worktree_path) / "pm" / "run-bad"
        bad_dir.mkdir(parents=True)  # no run.json at all

        pairs, problems = cr.resolve_ungraded_run_dirs(substrate_repo, "pm-eval-v2", bench_root)

        assert [(run_id, run_dir.resolve()) for run_id, run_dir in pairs] == [("run-good", good_dir.resolve())]
        assert len(problems) == 1
        assert str(bad_dir) in problems[0]

    def test_non_string_run_id_is_a_problem_not_a_crash(self, tmp_path: Path) -> None:
        bench_root, policy_path, substrate_repo, commit = self._fixture(tmp_path)
        worktree_path = self._make_trial(bench_root, policy_path, commit)
        good_dir = self._make_pm_run(worktree_path, "run-good")
        bad_dir = _worktree_gitdir(worktree_path) / "pm" / "run-bad"
        bad_dir.mkdir(parents=True)
        (bad_dir / "run.json").write_text(json.dumps({"run_id": 12345}), encoding="utf-8")

        # Must not raise TypeError building a results/runs/<run_id>/ Path
        # from a non-string run_id -- _read_run_id rejects it first.
        pairs, problems = cr.resolve_ungraded_run_dirs(substrate_repo, "pm-eval-v2", bench_root)

        assert [(run_id, run_dir.resolve()) for run_id, run_dir in pairs] == [("run-good", good_dir.resolve())]
        assert len(problems) == 1
        assert str(bad_dir) in problems[0]

    def test_unresolvable_worktree_is_a_problem_not_a_crash(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        bench_root, policy_path, substrate_repo, commit = self._fixture(tmp_path)
        worktree_1 = self._make_trial(bench_root, policy_path, commit, label="trial-1")
        worktree_2 = self._make_trial(bench_root, policy_path, commit, label="trial-2")
        run_2 = self._make_pm_run(worktree_2, "run-2")

        real_resolve = cr._resolve_git_dir

        def flaky_resolve(path: object) -> Path:
            if str(path) == str(worktree_1):
                raise cr.CohortRunError("simulated failure")
            return real_resolve(path)

        monkeypatch.setattr(cr, "_resolve_git_dir", flaky_resolve)

        pairs, problems = cr.resolve_ungraded_run_dirs(substrate_repo, "pm-eval-v2", bench_root)

        assert [(run_id, run_dir.resolve()) for run_id, run_dir in pairs] == [("run-2", run_2.resolve())]
        assert len(problems) == 1
        assert "simulated failure" in problems[0]


class TestRunAnalyzeAll:
    def _fixture(self, tmp_path: Path) -> tuple[Path, Path]:
        """Returns (bench_root, policy_path); no real worktree needed since
        most tests here monkeypatch resolve_ungraded_run_dirs directly."""
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text(
            yaml.safe_dump({"default_task": TASK_ID, "tasks": {TASK_ID: _task_entry(str(tmp_path / "repo"))}}),
            encoding="utf-8",
        )
        (tmp_path / "repo").mkdir()
        subprocess.run(["git", "init", "-q"], cwd=tmp_path / "repo", check=True)
        bench_root = tmp_path / "bench-root"
        bench_root.mkdir()
        return bench_root, policy_path

    def _args(self, policy_path: Path, *, skip_leaderboard: bool = False, task: str | None = None) -> Any:
        return type("Args", (), {"policy": policy_path, "skip_leaderboard": skip_leaderboard, "task": task})()

    def _run_dir(self, tmp_path: Path, run_id: str) -> Path:
        run_dir = tmp_path / run_id
        run_dir.mkdir()
        (run_dir / "run.json").write_text(json.dumps({"run_id": run_id}), encoding="utf-8")
        return run_dir

    def test_grades_every_discovered_run_then_refolds_once(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        bench_root, policy_path = self._fixture(tmp_path)
        run_dir_1 = self._run_dir(tmp_path, "run-1")
        run_dir_2 = self._run_dir(tmp_path, "run-2")
        monkeypatch.setattr(
            cr, "resolve_ungraded_run_dirs", lambda repo, prefix, root: ([("run-1", run_dir_1), ("run-2", run_dir_2)], [])
        )
        calls: list[tuple[str, list[str]]] = []
        monkeypatch.setattr(cr.grade_run, "main", _recording_main("grade_run", calls))
        monkeypatch.setattr(cr.model_report, "main", _recording_main("model_report", calls))
        monkeypatch.setattr(cr.leaderboard, "main", _recording_main("leaderboard", calls))

        rc = cr.run_analyze_all(self._args(policy_path), bench_root)

        assert rc == 0
        assert [label for label, _ in calls] == ["grade_run", "model_report", "grade_run", "model_report", "leaderboard"]
        # --task is ALWAYS forwarded: it names the task whose own worktrees
        # discovery found each run under, so grading can never silently fall
        # back to default_task. --policy is always forwarded here too since
        # run_analyze_all needs a real policy.yaml to enumerate its tasks in
        # the first place -- args.policy is never None in this fixture -- and
        # Slice 4 extends that forwarding to model_report as well, not just
        # grade_run/leaderboard.
        assert calls[0][1] == ["--run-dir", str(run_dir_1), "--task", TASK_ID, "--policy", str(policy_path)]
        assert calls[1][1] == ["--run-id", "run-1", "--run-dir", str(run_dir_1), "--policy", str(policy_path)]
        assert calls[2][1] == ["--run-dir", str(run_dir_2), "--task", TASK_ID, "--policy", str(policy_path)]
        assert calls[3][1] == ["--run-id", "run-2", "--run-dir", str(run_dir_2), "--policy", str(policy_path)]
        assert calls[4][1] == ["--policy", str(policy_path)]

    def test_no_ungraded_runs_still_refolds_leaderboard(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        bench_root, policy_path = self._fixture(tmp_path)
        monkeypatch.setattr(cr, "resolve_ungraded_run_dirs", lambda repo, prefix, root: ([], []))
        monkeypatch.setattr(cr.leaderboard, "main", lambda argv: 0)

        rc = cr.run_analyze_all(self._args(policy_path), bench_root)

        assert rc == 0
        assert "no ungraded runs found" in capsys.readouterr().out

    def test_skip_leaderboard_does_not_call_leaderboard(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        bench_root, policy_path = self._fixture(tmp_path)
        run_dir = self._run_dir(tmp_path, "run-1")
        monkeypatch.setattr(cr, "resolve_ungraded_run_dirs", lambda repo, prefix, root: ([("run-1", run_dir)], []))
        monkeypatch.setattr(cr.grade_run, "main", lambda argv: 0)
        monkeypatch.setattr(cr.model_report, "main", lambda argv: 0)

        def fail_if_called(argv: list[str]) -> int:
            raise AssertionError("leaderboard.main should not have been called")

        monkeypatch.setattr(cr.leaderboard, "main", fail_if_called)

        rc = cr.run_analyze_all(self._args(policy_path, skip_leaderboard=True), bench_root)
        assert rc == 0

    def test_one_runs_grading_failure_does_not_stop_the_others(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # A malformed run.json is now caught during discovery (see
        # TestResolveUngradedRunDirs.test_unreadable_run_json_is_a_problem_not_a_crash)
        # -- what run_analyze_all itself must still isolate is a later stage
        # (grade_run.py/model_report.py) refusing one already-discovered run.
        bad_run_dir = self._run_dir(tmp_path, "run-bad")
        good_run_dir = self._run_dir(tmp_path, "run-good")
        bench_root, policy_path = self._fixture(tmp_path)
        monkeypatch.setattr(
            cr,
            "resolve_ungraded_run_dirs",
            lambda repo, prefix, root: ([("run-bad", bad_run_dir), ("run-good", good_run_dir)], []),
        )
        calls: list[str] = []

        def raiser(argv: list[str]) -> int:
            if any("run-bad" in arg for arg in argv):
                raise bench_lib.BenchLibError("run not finished")
            return calls.append("grade_run") or 0

        monkeypatch.setattr(cr.grade_run, "main", raiser)
        monkeypatch.setattr(cr.model_report, "main", lambda argv: calls.append("model_report") or 0)
        monkeypatch.setattr(cr.leaderboard, "main", lambda argv: calls.append("leaderboard") or 0)

        rc = cr.run_analyze_all(self._args(policy_path), bench_root)

        assert rc == 1  # run-bad's refusal is reported as a failure
        # run-bad's model_report.py still ran (matching analyze's own
        # per-tool isolation), then run-good's full pipeline, then one
        # leaderboard refold at the very end.
        assert calls == ["model_report", "grade_run", "model_report", "leaderboard"]

    def test_discovery_problems_force_nonzero_exit_even_if_everything_else_succeeds(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        bench_root, policy_path = self._fixture(tmp_path)
        monkeypatch.setattr(
            cr, "resolve_ungraded_run_dirs", lambda repo, prefix, root: ([], ["some-worktree: could not resolve"])
        )
        monkeypatch.setattr(cr.leaderboard, "main", lambda argv: 0)

        rc = cr.run_analyze_all(self._args(policy_path), bench_root)
        assert rc == 1

    def test_policy_override_is_forwarded_to_every_tool_including_model_report(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Slice 4 criterion: an operator's custom --policy must reach ALL
        # three downstream tools, including model_report -- before this slice
        # the report built between grading and refolding silently resolved
        # its own task registry from the bench-root default instead.
        bench_root, policy_path = self._fixture(tmp_path)
        run_dir = self._run_dir(tmp_path, "run-1")
        monkeypatch.setattr(cr, "resolve_ungraded_run_dirs", lambda repo, prefix, root: ([("run-1", run_dir)], []))
        calls: list[tuple[str, list[str]]] = []
        monkeypatch.setattr(cr.grade_run, "main", _recording_main("grade_run", calls))
        monkeypatch.setattr(cr.model_report, "main", _recording_main("model_report", calls))
        monkeypatch.setattr(cr.leaderboard, "main", _recording_main("leaderboard", calls))

        rc = cr.run_analyze_all(self._args(policy_path), bench_root)

        assert rc == 0
        grade_argv = dict(calls)["grade_run"]
        board_argv = dict(calls)["leaderboard"]
        report_argv = dict(calls)["model_report"]
        assert grade_argv == ["--run-dir", str(run_dir), "--task", TASK_ID, "--policy", str(policy_path)]
        assert board_argv == ["--policy", str(policy_path)]
        assert report_argv == ["--run-id", "run-1", "--run-dir", str(run_dir), "--policy", str(policy_path)]

    def test_task_flag_restricts_discovery_to_that_tasks_own_worktrees(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Two configured tasks; --task names one of them. Discovery must
        # consult exactly that task's repo/branch-prefix pair -- never the
        # other task's -- and every discovered run is graded under the named
        # task id. The flag names a GENUINELY non-default task id, so a
        # regression that ignored args.task and fell back to default_task
        # would consult the wrong repo and fail these assertions.
        bench_root, policy_path = self._fixture(tmp_path)
        policy = yaml.safe_load(policy_path.read_text())
        policy["tasks"]["other-task"] = _task_entry(str(tmp_path / "other-repo"))
        (tmp_path / "other-repo").mkdir()
        subprocess.run(["git", "init", "-q"], cwd=tmp_path / "other-repo", check=True)
        policy_path.write_text(yaml.safe_dump(policy), encoding="utf-8")
        run_dir = self._run_dir(tmp_path, "run-1")
        consulted: list[Path] = []

        def recording_resolve(repo: Path, prefix: str, root: Path):
            consulted.append(repo)
            return ([("run-1", run_dir)], []) if repo.name == "other-repo" else ([], [])

        monkeypatch.setattr(cr, "resolve_ungraded_run_dirs", recording_resolve)
        calls: list[tuple[str, list[str]]] = []
        monkeypatch.setattr(cr.grade_run, "main", _recording_main("grade_run", calls))
        monkeypatch.setattr(cr.model_report, "main", _recording_main("model_report", calls))
        monkeypatch.setattr(cr.leaderboard, "main", _recording_main("leaderboard", calls))

        rc = cr.run_analyze_all(self._args(policy_path, task="other-task"), bench_root)

        assert rc == 0
        assert [str(p) for p in consulted] == [str(tmp_path / "other-repo")]
        assert dict(calls)["grade_run"] == [
            "--run-dir",
            str(run_dir),
            "--task",
            "other-task",
            "--policy",
            str(policy_path),
        ]

    def test_broken_task_repo_is_a_named_problem_and_other_tasks_runs_are_still_graded(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # other-task's repo is a plain directory (no .git): that task alone
        # is named as a problem and skipped; relative-velocity's run is still
        # handed to grading, and the command exits 1.
        bench_root, policy_path = self._fixture(tmp_path)
        policy = yaml.safe_load(policy_path.read_text())
        broken_repo = tmp_path / "broken-repo"
        broken_repo.mkdir()
        policy["tasks"]["other-task"] = _task_entry(broken_repo)
        policy_path.write_text(yaml.safe_dump(policy), encoding="utf-8")
        run_dir = self._run_dir(tmp_path, "run-1")
        monkeypatch.setattr(cr, "resolve_ungraded_run_dirs", lambda repo, prefix, root: ([("run-1", run_dir)], []))
        calls: list[tuple[str, list[str]]] = []
        monkeypatch.setattr(cr.grade_run, "main", _recording_main("grade_run", calls))
        monkeypatch.setattr(cr.model_report, "main", _recording_main("model_report", calls))
        monkeypatch.setattr(cr.leaderboard, "main", _recording_main("leaderboard", calls))

        rc = cr.run_analyze_all(self._args(policy_path), bench_root)

        assert rc == 1
        assert dict(calls)["grade_run"][:4] == ["--run-dir", str(run_dir), "--task", TASK_ID]
        warnings = [line for line in capsys.readouterr().err.splitlines() if "warning" in line]
        assert len(warnings) == 1
        assert "other-task" in warnings[0]
        assert str(broken_repo) in warnings[0]
        assert "does not look like a git repository" in warnings[0]

    def test_broken_default_task_entry_is_a_named_problem_and_other_tasks_runs_are_still_graded(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # The DEFAULT task's entry lacks a required key: that task alone is
        # named as a problem, never a batch-wide abort.
        bench_root, policy_path = self._fixture(tmp_path)
        policy = yaml.safe_load(policy_path.read_text())
        other_repo = tmp_path / "other-repo"
        other_repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=other_repo, check=True)
        policy["tasks"]["other-task"] = _task_entry(str(other_repo))
        del policy["tasks"][TASK_ID]["plan_file"]
        policy_path.write_text(yaml.safe_dump(policy), encoding="utf-8")
        run_dir = self._run_dir(tmp_path, "run-1")
        monkeypatch.setattr(cr, "resolve_ungraded_run_dirs", lambda repo, prefix, root: ([("run-1", run_dir)], []))
        calls: list[tuple[str, list[str]]] = []
        monkeypatch.setattr(cr.grade_run, "main", _recording_main("grade_run", calls))
        monkeypatch.setattr(cr.model_report, "main", _recording_main("model_report", calls))
        monkeypatch.setattr(cr.leaderboard, "main", _recording_main("leaderboard", calls))

        rc = cr.run_analyze_all(self._args(policy_path), bench_root)

        assert rc == 1
        assert dict(calls)["grade_run"][:4] == ["--run-dir", str(run_dir), "--task", "other-task"]
        warnings = [line for line in capsys.readouterr().err.splitlines() if "warning" in line]
        assert len(warnings) == 1
        assert TASK_ID in warnings[0]
        assert "plan_file" in warnings[0]

    def test_run_found_under_two_tasks_sharing_repo_and_prefix_is_named_ambiguous_and_not_graded(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        # Two configured tasks sharing one (repo, branch_prefix) pair discover
        # the SAME run directory twice: it is named once as ambiguous (with
        # both claimants) and not graded, while an unrelated task's run is
        # still graded.
        bench_root, policy_path = self._fixture(tmp_path)
        policy = yaml.safe_load(policy_path.read_text())
        # Deliberately give other-task the FIRST task's own repo/prefix.
        policy["tasks"]["other-task"] = _task_entry(str(tmp_path / "repo"))
        (tmp_path / "third-repo").mkdir()
        subprocess.run(["git", "init", "-q"], cwd=tmp_path / "third-repo", check=True)
        policy["tasks"]["third-task"] = _task_entry(str(tmp_path / "third-repo"))
        policy_path.write_text(yaml.safe_dump(policy), encoding="utf-8")
        shared_run = self._run_dir(tmp_path, "run-shared")
        third_run = self._run_dir(tmp_path, "run-third")

        def resolve_by_repo(repo: Path, prefix: str, root: Path):
            return ([("run-third", third_run)] if repo.name == "third-repo" else [("run-shared", shared_run)]), []

        monkeypatch.setattr(cr, "resolve_ungraded_run_dirs", resolve_by_repo)
        calls: list[tuple[str, list[str]]] = []
        monkeypatch.setattr(cr.grade_run, "main", _recording_main("grade_run", calls))
        monkeypatch.setattr(cr.model_report, "main", _recording_main("model_report", calls))
        monkeypatch.setattr(cr.leaderboard, "main", _recording_main("leaderboard", calls))

        rc = cr.run_analyze_all(self._args(policy_path), bench_root)

        assert rc == 1
        assert [argv[:4] for label, argv in calls if label == "grade_run"] == [
            ["--run-dir", str(third_run), "--task", "third-task"]
        ]
        warnings = [line for line in capsys.readouterr().err.splitlines() if "warning" in line]
        assert len(warnings) == 1
        assert str(shared_run.resolve()) in warnings[0]
        assert "other-task, relative-velocity" in warnings[0]

    def test_empty_task_id_is_a_named_refusal_not_a_silent_widen_to_every_task(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # An explicit --task "" must take the same named-refusal path
        # setup/analyze/cleanup route through resolve_task -- never silently
        # widen into scanning every configured task, and discovery must not
        # even start.
        bench_root, policy_path = self._fixture(tmp_path)
        policy = yaml.safe_load(policy_path.read_text())
        policy["tasks"]["other-task"] = _task_entry(str(tmp_path / "other-repo"))
        (tmp_path / "other-repo").mkdir()
        subprocess.run(["git", "init", "-q"], cwd=tmp_path / "other-repo", check=True)
        policy_path.write_text(yaml.safe_dump(policy), encoding="utf-8")

        def fail_if_called(*_args: Any, **_kwargs: Any):
            raise AssertionError("discovery must never start for an invalid --task id")

        monkeypatch.setattr(cr, "resolve_ungraded_run_dirs", fail_if_called)

        with pytest.raises(cr.CohortRunError, match=r"non-empty string"):
            cr.run_analyze_all(self._args(policy_path, task=""), bench_root)

    def test_without_task_flag_discovery_spans_every_configured_task_and_tags_each_run(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # No --task: discovery iterates EVERY configured task's own
        # repo/branch-prefix pair, and each discovered run is tagged with --
        # and graded under -- the task whose worktrees it was found under,
        # even when that is not the default_task.
        bench_root, policy_path = self._fixture(tmp_path)
        policy = yaml.safe_load(policy_path.read_text())
        policy["default_task"] = "other-task"
        policy["tasks"]["other-task"] = _task_entry(str(tmp_path / "other-repo"))
        (tmp_path / "other-repo").mkdir()
        subprocess.run(["git", "init", "-q"], cwd=tmp_path / "other-repo", check=True)
        policy_path.write_text(yaml.safe_dump(policy), encoding="utf-8")
        run_a = self._run_dir(tmp_path, "run-a")
        run_b = self._run_dir(tmp_path, "run-b")

        def resolve_by_repo(repo: Path, prefix: str, root: Path):
            if repo.name == "repo":
                return [("run-a", run_a)], []
            return [("run-b", run_b)], []

        monkeypatch.setattr(cr, "resolve_ungraded_run_dirs", resolve_by_repo)
        calls: list[tuple[str, list[str]]] = []
        monkeypatch.setattr(cr.grade_run, "main", _recording_main("grade_run", calls))
        monkeypatch.setattr(cr.model_report, "main", _recording_main("model_report", calls))
        monkeypatch.setattr(cr.leaderboard, "main", _recording_main("leaderboard", calls))

        rc = cr.run_analyze_all(self._args(policy_path), bench_root)

        assert rc == 0
        # Task ids are visited in sorted order ("other-task" < "relative-velocity"),
        # so run-b (found under other-task) is graded first, then run-a.
        assert calls[0][0] == "grade_run"
        assert calls[0][1] == ["--run-dir", str(run_b), "--task", "other-task", "--policy", str(policy_path)]
        assert calls[2][0] == "grade_run"
        assert calls[2][1] == ["--run-dir", str(run_a), "--task", TASK_ID, "--policy", str(policy_path)]


# --- reset-leaderboard --------------------------------------------------------


class TestRunResetLeaderboard:
    def _make_results(self, tmp_path: Path) -> tuple[Path, Path]:
        root = tmp_path / "root"
        results_dir = root / "results"
        run_dir = results_dir / "runs" / "run-1"
        run_dir.mkdir(parents=True)
        (run_dir / "slice-1.json").write_text("{}", encoding="utf-8")
        (results_dir / "leaderboard.json").write_text("{}", encoding="utf-8")
        (results_dir / "leaderboard.md").write_text("# Leaderboard\n", encoding="utf-8")
        return root, results_dir

    def test_dry_run_moves_nothing(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        root, results_dir = self._make_results(tmp_path)
        rc = cr.main(["reset-leaderboard", "--results-dir", str(results_dir)])
        assert rc == 0
        assert (results_dir / "runs" / "run-1" / "slice-1.json").is_file()
        assert (results_dir / "leaderboard.json").is_file()
        assert (results_dir / "leaderboard.md").is_file()
        assert "dry run only" in capsys.readouterr().out

    def test_yes_archives_everything_and_recreates_empty_runs_dir(self, tmp_path: Path) -> None:
        root, results_dir = self._make_results(tmp_path)
        archive_dir = tmp_path / "archive-target"
        rc = cr.main(["reset-leaderboard", "--results-dir", str(results_dir), "--archive-dir", str(archive_dir), "--yes"])
        assert rc == 0
        assert not (results_dir / "leaderboard.json").exists()
        assert not (results_dir / "leaderboard.md").exists()
        assert (results_dir / "runs").is_dir()
        assert not (results_dir / "runs" / "run-1").exists()
        assert (archive_dir / "runs" / "run-1" / "slice-1.json").is_file()
        assert (archive_dir / "leaderboard.json").is_file()
        assert (archive_dir / "leaderboard.md").is_file()

    def test_scoped_to_one_run_id_leaves_others_alone(self, tmp_path: Path) -> None:
        root, results_dir = self._make_results(tmp_path)
        (results_dir / "runs" / "run-2").mkdir(parents=True)
        archive_dir = tmp_path / "archive-target"
        rc = cr.main(
            ["reset-leaderboard", "--results-dir", str(results_dir), "--archive-dir", str(archive_dir), "--run-id", "run-1", "--yes"]
        )
        assert rc == 0
        assert not (results_dir / "runs" / "run-1").exists()
        assert (results_dir / "runs" / "run-2").is_dir()
        assert (results_dir / "leaderboard.json").is_file()
        assert (results_dir / "leaderboard.md").is_file()
        assert (archive_dir / "run-1" / "slice-1.json").is_file()

    def test_a_later_collision_does_not_leave_an_earlier_target_already_moved(self, tmp_path: Path) -> None:
        # Every destination is validated before any target is moved -- a
        # collision on leaderboard.json (processed second) must not leave
        # results/runs already archived with no way back.
        root, results_dir = self._make_results(tmp_path)
        archive_dir = tmp_path / "archive-target"
        archive_dir.mkdir(parents=True)
        (archive_dir / "leaderboard.json").write_text("{}", encoding="utf-8")

        with pytest.raises(cr.CohortRunError, match="refusing to overwrite existing archive entries"):
            cr.main(["reset-leaderboard", "--results-dir", str(results_dir), "--archive-dir", str(archive_dir), "--yes"])

        assert (results_dir / "runs" / "run-1" / "slice-1.json").is_file()
        assert (results_dir / "leaderboard.json").is_file()
        assert (results_dir / "leaderboard.md").is_file()
        assert not (archive_dir / "runs").exists()

    def test_only_one_leaderboard_file_present_is_still_archived(self, tmp_path: Path) -> None:
        # leaderboard.md may not exist yet (an older results/ predating this
        # tool's own Markdown output) -- only the file that's actually on
        # disk should be a target; the other must never appear as a phantom
        # destination/collision.
        root, results_dir = self._make_results(tmp_path)
        (results_dir / "leaderboard.md").unlink()
        archive_dir = tmp_path / "archive-target"
        rc = cr.main(["reset-leaderboard", "--results-dir", str(results_dir), "--archive-dir", str(archive_dir), "--yes"])
        assert rc == 0
        assert not (results_dir / "leaderboard.json").exists()
        assert not (results_dir / "leaderboard.md").exists()
        assert (archive_dir / "leaderboard.json").is_file()
        assert not (archive_dir / "leaderboard.md").exists()

    def test_unknown_run_id_is_a_named_error(self, tmp_path: Path) -> None:
        root, results_dir = self._make_results(tmp_path)
        with pytest.raises(cr.CohortRunError, match="no results found for run_id"):
            cr.main(["reset-leaderboard", "--results-dir", str(results_dir), "--run-id", "does-not-exist"])

    def test_nothing_to_archive_is_not_an_error(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        results_dir = tmp_path / "empty-results"
        rc = cr.main(["reset-leaderboard", "--results-dir", str(results_dir)])
        assert rc == 0
        assert "nothing under" in capsys.readouterr().out

    def test_yes_refuses_to_overwrite_an_existing_archive_entry(self, tmp_path: Path) -> None:
        root, results_dir = self._make_results(tmp_path)
        archive_dir = tmp_path / "archive-target"
        (archive_dir / "runs").mkdir(parents=True)
        with pytest.raises(cr.CohortRunError, match="refusing to overwrite existing archive entries"):
            cr.main(["reset-leaderboard", "--results-dir", str(results_dir), "--archive-dir", str(archive_dir), "--yes"])


# --- CLI plumbing -------------------------------------------------------------


class TestCliPlumbing:
    def test_no_subcommand_exits_nonzero(self) -> None:
        with pytest.raises(SystemExit):
            cr.main([])

    def test_top_level_help_exits_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        with pytest.raises(SystemExit) as exc_info:
            cr.main(["--help"])
        assert exc_info.value.code == 0

    def test_each_subcommand_help_exits_zero(self, capsys: pytest.CaptureFixture[str]) -> None:
        for command in ("setup", "analyze", "analyze-all", "cleanup", "reset-leaderboard"):
            with pytest.raises(SystemExit) as exc_info:
                cr.main([command, "--help"])
            assert exc_info.value.code == 0
