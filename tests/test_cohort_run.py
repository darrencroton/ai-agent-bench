"""Tests for tools/cohort_run.py (the operator convenience wrapper: setup /
analyze / cleanup, docs/MODE2-REWRITE-PLAN.md §6, "Tool 6").

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
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import bench_lib  # noqa: E402
import cohort_run as cr  # noqa: E402

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
Harness: <codex|claude|copilot|opencode|qwen> (optionally: model <model name>)

Use the project-manager skill.
```

Details the launcher relies on: see README.md.
"""

_EXPECTED_TEMPLATE = (
    "Plan file: <absolute path>\n"
    "Repo: <absolute path>\n"
    "Harness: <codex|claude|copilot|opencode|qwen> (optionally: model <model name>)\n"
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


def _write_policy(tmp_path: Path, skill_dir: Path, **extra: Any) -> Path:
    policy = {
        "backend": "local",
        "pm_scripts_dir": str(skill_dir / "scripts"),
        "lint_script": str(tmp_path / "lint.py"),
        "health_script": str(tmp_path / "health.py"),
        "python_interpreter": str(tmp_path / "python3"),
        "subprocess_timeout_seconds": 600,
        **extra,
    }
    policy_path = tmp_path / "policy.yaml"
    policy_path.write_text(yaml.safe_dump(policy), encoding="utf-8")
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

    def test_fills_plan_file_and_repo(self) -> None:
        prompt, substituted = cr.render_launcher_prompt(_EXPECTED_TEMPLATE, plan_file="/p/plan.md", repo="/p/repo")
        assert "Plan file: /p/plan.md" in prompt
        assert "Repo: /p/repo" in prompt
        assert "Harness: <codex|claude|copilot|opencode|qwen> (optionally: model <model name>)" in prompt
        assert substituted == {"plan_file", "repo"}

    def test_fills_harness_only(self) -> None:
        prompt, substituted = cr.render_launcher_prompt(_EXPECTED_TEMPLATE, harness="claude")
        assert "Harness: claude (optionally: model <model name>)" in prompt
        assert substituted == {"harness"}

    def test_fills_model_only(self) -> None:
        prompt, substituted = cr.render_launcher_prompt(_EXPECTED_TEMPLATE, model="qwen3-coder")
        assert "Harness: <codex|claude|copilot|opencode|qwen> (model qwen3-coder)" in prompt
        assert substituted == {"model"}

    def test_fills_harness_and_model_together(self) -> None:
        prompt, substituted = cr.render_launcher_prompt(_EXPECTED_TEMPLATE, harness="claude", model="qwen3-coder")
        assert "Harness: claude (model qwen3-coder)" in prompt
        assert substituted == {"harness", "model"}


# --- setup (CLI) -------------------------------------------------------------


class TestRunSetup:
    def test_prints_prompt_and_steps(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        # --repo given: the manual escape hatch, so no worktree creation is
        # attempted (create_dev_worktree is exercised separately, below).
        skill_dir = _write_skill_md(tmp_path)
        policy_path = _write_policy(tmp_path, skill_dir)
        dev_repo = _make_prepared_repo(tmp_path)
        rc = cr.main(
            ["--policy", str(policy_path), "setup", "--harness", "claude", "--model", "my-model", "--repo", str(dev_repo)]
        )
        assert rc == 0
        out = capsys.readouterr().out
        assert "Harness: claude (model my-model)" in out
        assert f"Repo: {dev_repo}" in out
        assert f"Plan file: {dev_repo / 'docs' / 'MERGER_RATE_PLAN-2SLICE.md'}" in out
        assert "Steps to follow" in out
        assert "python tools/cohort_run.py analyze" in out
        assert "no reviewer gap" in out
        assert "exactly one frozen plan" in out

    def test_label_or_base_commit_with_repo_is_a_named_error(self, tmp_path: Path) -> None:
        skill_dir = _write_skill_md(tmp_path)
        policy_path = _write_policy(tmp_path, skill_dir)
        with pytest.raises(cr.CohortRunError, match="only apply when creating a new worktree"):
            cr.main(["--policy", str(policy_path), "setup", "--repo", str(tmp_path), "--label", "x"])

    def test_nonexistent_repo_is_a_named_error(self, tmp_path: Path) -> None:
        skill_dir = _write_skill_md(tmp_path)
        policy_path = _write_policy(tmp_path, skill_dir)
        with pytest.raises(cr.CohortRunError, match="is not an existing directory"):
            cr.main(["--policy", str(policy_path), "setup", "--repo", str(tmp_path / "does-not-exist")])

    def test_repo_with_no_frozen_plan_at_the_fixed_path_is_a_named_error(self, tmp_path: Path) -> None:
        skill_dir = _write_skill_md(tmp_path)
        policy_path = _write_policy(tmp_path, skill_dir)
        empty_repo = tmp_path / "empty-repo"
        empty_repo.mkdir()
        with pytest.raises(cr.CohortRunError, match="has no docs/MERGER_RATE_PLAN-2SLICE.md"):
            cr.main(["--policy", str(policy_path), "setup", "--repo", str(empty_repo)])

    def test_nonexistent_plan_file_override_is_a_named_error(self, tmp_path: Path) -> None:
        skill_dir = _write_skill_md(tmp_path)
        policy_path = _write_policy(tmp_path, skill_dir)
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
            relative_velocity_repo=str(substrate_repo),
            dev_branch_prefix="pm-eval-v2",
            dev_worktree_root=str(tmp_path / "worktrees"),
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
        policy_path = _write_policy(tmp_path, skill_dir)
        dev_repo = _make_prepared_repo(tmp_path, name="rel-dev-repo")
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
            relative_velocity_repo=str(substrate_repo),
            dev_branch_prefix="pm-eval-v2",
            dev_worktree_root=str(worktree_root),
        )

        rc = cr.main(
            [
                "--policy",
                str(policy_path),
                "setup",
                "--harness",
                "claude",
                "--model",
                "claude-sonnet-5",
                "--label",
                "trial-1",
                "--base-commit",
                commit,
            ]
        )

        assert rc == 0
        out = capsys.readouterr().out
        expected_worktree = worktree_root / f"{substrate_repo.name}-trial-1"
        assert f"created worktree {expected_worktree}" in out
        assert f"Repo: {expected_worktree}" in out
        assert f"Plan file: {expected_worktree / 'docs' / 'MERGER_RATE_PLAN-2SLICE.md'}" in out
        assert (expected_worktree / "docs" / "MERGER_RATE_PLAN-2SLICE.md").is_file()

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
        policy_path = _write_policy(tmp_path, skill_dir)
        with pytest.raises(cr.CohortRunError, match="SKILL.md not found"):
            cr.main(["--policy", str(policy_path), "setup"])

    def test_warns_when_a_given_field_has_no_matching_template_line(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        skill_dir = _write_skill_md(tmp_path, text="# PM\n\n## Launcher\n\n```md\nNothing to fill here.\n```\n")
        policy_path = _write_policy(tmp_path, skill_dir)
        dev_repo = _make_prepared_repo(tmp_path)
        rc = cr.main(["--policy", str(policy_path), "setup", "--model", "my-model", "--repo", str(dev_repo)])
        assert rc == 0
        err = capsys.readouterr().err
        assert "--model was given but the launcher template has no matching 'model' line" in err


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


class TestParsePinnedPlanCommit:
    def test_extracts_the_hash(self, tmp_path: Path) -> None:
        provenance = tmp_path / "provenance.md"
        provenance.write_text("Pinned commit: `043b13adc264689c376bdd337603e94d5447623a` (\"a message\")\n", encoding="utf-8")
        assert cr.parse_pinned_plan_commit(provenance) == "043b13adc264689c376bdd337603e94d5447623a"

    def test_missing_file_is_a_named_error(self, tmp_path: Path) -> None:
        with pytest.raises(cr.CohortRunError, match="not found"):
            cr.parse_pinned_plan_commit(tmp_path / "does-not-exist.md")

    def test_missing_pinned_commit_line_is_a_named_error(self, tmp_path: Path) -> None:
        provenance = tmp_path / "provenance.md"
        provenance.write_text("No pinned commit line here.\n", encoding="utf-8")
        with pytest.raises(cr.CohortRunError, match="Pinned commit"):
            cr.parse_pinned_plan_commit(provenance)


class TestSlugify:
    def test_normalizes_to_lowercase_hyphenated(self) -> None:
        assert cr.slugify("codex/gpt-5.6-luna") == "codex-gpt-5-6-luna"

    def test_no_usable_characters_is_a_named_error(self) -> None:
        with pytest.raises(cr.CohortRunError, match="no usable characters"):
            cr.slugify("///")


class TestLoadDevRepoPolicy:
    def test_missing_keys_is_a_named_error(self) -> None:
        with pytest.raises(cr.CohortRunError, match="missing required key"):
            cr.load_dev_repo_policy({})

    def test_not_a_git_repo_is_a_named_error(self, tmp_path: Path) -> None:
        not_a_repo = tmp_path / "not-a-repo"
        not_a_repo.mkdir()
        with pytest.raises(cr.CohortRunError, match="does not look like a git repository"):
            cr.load_dev_repo_policy({"relative_velocity_repo": str(not_a_repo), "dev_branch_prefix": "pm-eval-v2"})

    def test_worktree_root_defaults_to_repo_parent(self, tmp_path: Path) -> None:
        repo, _ = _make_substrate_repo(tmp_path)
        resolved_repo, prefix, worktree_root = cr.load_dev_repo_policy(
            {"relative_velocity_repo": str(repo), "dev_branch_prefix": "pm-eval-v2"}
        )
        assert resolved_repo == repo.resolve()
        assert prefix == "pm-eval-v2"
        assert worktree_root == repo.resolve().parent

    def test_worktree_root_override_is_honored(self, tmp_path: Path) -> None:
        repo, _ = _make_substrate_repo(tmp_path)
        override = tmp_path / "custom-worktrees"
        _, _, worktree_root = cr.load_dev_repo_policy(
            {"relative_velocity_repo": str(repo), "dev_branch_prefix": "pm-eval-v2", "dev_worktree_root": str(override)}
        )
        assert worktree_root == override.resolve()


class TestCreateDevWorktree:
    def _policy(self, repo: Path, worktree_root: Path, *, prefix: str = "pm-eval-v2") -> dict[str, Any]:
        return {
            "relative_velocity_repo": str(repo),
            "dev_branch_prefix": prefix,
            "dev_worktree_root": str(worktree_root),
        }

    def test_creates_worktree_on_the_expected_branch_at_the_given_commit(self, tmp_path: Path) -> None:
        repo, commit = _make_substrate_repo(tmp_path)
        worktree_root = tmp_path / "worktrees"
        policy = self._policy(repo, worktree_root)

        worktree_path, branch_name, label = cr.create_dev_worktree(
            policy, tmp_path, model="claude-sonnet-5", harness="claude", label="explicit-label", base_commit=commit
        )

        assert label == "explicit-label"
        assert branch_name == "pm-eval-v2/explicit-label"
        assert worktree_path == (worktree_root / f"{repo.name}-explicit-label").resolve()
        assert (worktree_path / "docs" / "MERGER_RATE_PLAN-2SLICE.md").is_file()
        assert label in cr.list_bench_branches(repo, "pm-eval-v2")

    def test_auto_label_derives_from_model_and_auto_numbers(self, tmp_path: Path) -> None:
        repo, commit = _make_substrate_repo(tmp_path)
        worktree_root = tmp_path / "worktrees"
        policy = self._policy(repo, worktree_root)

        _, _, label1 = cr.create_dev_worktree(
            policy, tmp_path, model="claude-sonnet-5", harness=None, label=None, base_commit=commit
        )
        _, _, label2 = cr.create_dev_worktree(
            policy, tmp_path, model="claude-sonnet-5", harness=None, label=None, base_commit=commit
        )

        assert label1 == "claude-sonnet-5-1"
        assert label2 == "claude-sonnet-5-2"

    def test_explicit_label_colliding_with_existing_branch_is_a_named_error(self, tmp_path: Path) -> None:
        repo, commit = _make_substrate_repo(tmp_path)
        worktree_root = tmp_path / "worktrees"
        policy = self._policy(repo, worktree_root)
        cr.create_dev_worktree(policy, tmp_path, model="m", harness=None, label="dup", base_commit=commit)

        with pytest.raises(cr.CohortRunError, match="already has a branch"):
            cr.create_dev_worktree(policy, tmp_path, model="m", harness=None, label="dup", base_commit=commit)

    def test_missing_plan_file_at_base_commit_is_a_named_error_and_leaves_no_orphaned_worktree(
        self, tmp_path: Path
    ) -> None:
        repo, commit = _make_substrate_repo(tmp_path, with_plan=False)
        worktree_root = tmp_path / "worktrees"
        policy = self._policy(repo, worktree_root)

        with pytest.raises(cr.CohortRunError, match="has no docs/MERGER_RATE_PLAN-2SLICE.md"):
            cr.create_dev_worktree(policy, tmp_path, model="m", harness=None, label="no-plan", base_commit=commit)

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
        policy = self._policy(repo, worktree_root)

        with pytest.raises(cr.CohortRunError, match="worktree add"):
            cr.create_dev_worktree(policy, tmp_path, model="m", harness=None, label="hook-fail", base_commit=commit)

        assert not (worktree_root / f"{repo.name}-hook-fail").exists()
        assert cr.list_bench_worktrees(repo, "pm-eval-v2") == []
        assert "hook-fail" not in cr.list_bench_branches(repo, "pm-eval-v2")

    def test_base_commit_defaults_to_the_pinned_provenance_commit(self, tmp_path: Path) -> None:
        repo, commit = _make_substrate_repo(tmp_path)
        worktree_root = tmp_path / "worktrees"
        policy = self._policy(repo, worktree_root)
        (tmp_path / "docs").mkdir(exist_ok=True)
        (tmp_path / "docs" / "MERGER_RATE_PLAN-2SLICE.provenance.md").write_text(
            f"Pinned commit: `{commit}`\n", encoding="utf-8"
        )

        worktree_path, _, _ = cr.create_dev_worktree(policy, tmp_path, model="m", harness=None, label="pinned", base_commit=None)

        checked_out = subprocess.run(
            ["git", "-C", str(worktree_path), "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip()
        assert checked_out == commit


class TestListBenchWorktreesAndBranches:
    def test_filters_by_branch_prefix(self, tmp_path: Path) -> None:
        repo, commit = _make_substrate_repo(tmp_path)
        worktree_root = tmp_path / "worktrees"
        policy = {"relative_velocity_repo": str(repo), "dev_branch_prefix": "pm-eval-v2", "dev_worktree_root": str(worktree_root)}
        cr.create_dev_worktree(policy, tmp_path, model="m", harness=None, label="a", base_commit=commit)
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
    def _run_dir(self, tmp_path: Path, run_id: str = "20260101T000000Z-abc") -> Path:
        run_dir = tmp_path / "pm-run"
        run_dir.mkdir()
        (run_dir / "run.json").write_text(json.dumps({"run_id": run_id}), encoding="utf-8")
        return run_dir

    def test_runs_all_three_tools_in_order_with_expected_argv(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        run_dir = self._run_dir(tmp_path)
        calls: list[tuple[str, list[str]]] = []

        monkeypatch.setattr(cr.grade_run, "main", _recording_main("grade_run", calls))
        monkeypatch.setattr(cr.model_report, "main", _recording_main("model_report", calls))
        monkeypatch.setattr(cr.leaderboard, "main", _recording_main("leaderboard", calls))

        rc = cr.main(["analyze", "--run-dir", str(run_dir)])

        assert rc == 0
        assert [label for label, _ in calls] == ["grade_run", "model_report", "leaderboard"]
        assert calls[0][1] == ["--run-dir", str(run_dir.resolve())]
        assert calls[1][1] == ["--run-id", "20260101T000000Z-abc"]
        assert calls[2][1] == []

    def test_exit_code_is_the_max_across_steps(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        run_dir = self._run_dir(tmp_path)
        monkeypatch.setattr(cr.grade_run, "main", lambda argv: 0)
        monkeypatch.setattr(cr.model_report, "main", lambda argv: 1)
        monkeypatch.setattr(cr.leaderboard, "main", lambda argv: 0)
        rc = cr.main(["analyze", "--run-dir", str(run_dir)])
        assert rc == 1

    def test_skip_leaderboard_does_not_call_leaderboard(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        run_dir = self._run_dir(tmp_path)
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
        run_dir = self._run_dir(tmp_path)
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
        run_dir = self._run_dir(tmp_path)
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

    def test_policy_override_is_forwarded_to_grade_run_and_leaderboard_not_model_report(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        run_dir = self._run_dir(tmp_path)
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text("backend: local\n", encoding="utf-8")
        calls: list[tuple[str, list[str]]] = []

        monkeypatch.setattr(cr.grade_run, "main", _recording_main("grade_run", calls))
        monkeypatch.setattr(cr.model_report, "main", _recording_main("model_report", calls))
        monkeypatch.setattr(cr.leaderboard, "main", _recording_main("leaderboard", calls))

        cr.main(["--policy", str(policy_path), "analyze", "--run-dir", str(run_dir)])

        grade_argv = dict(calls)["grade_run"]
        report_argv = dict(calls)["model_report"]
        board_argv = dict(calls)["leaderboard"]
        assert grade_argv == ["--run-dir", str(run_dir.resolve()), "--policy", str(policy_path)]
        assert report_argv == ["--run-id", "20260101T000000Z-abc"]
        assert board_argv == ["--policy", str(policy_path)]


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
                    "relative_velocity_repo": str(substrate_repo),
                    "dev_branch_prefix": "pm-eval-v2",
                    "dev_worktree_root": str(worktree_root),
                }
            ),
            encoding="utf-8",
        )
        bench_root = tmp_path / "bench-root"
        bench_root.mkdir()
        return bench_root, policy_path, substrate_repo, commit

    def _args(self, policy_path: Path, *, label: str | None = None, yes: bool = False, force: bool = False) -> Any:
        return type("Args", (), {"policy": policy_path, "label": label, "yes": yes, "force": force})()

    def _make_trial(self, bench_root: Path, policy_path: Path, commit: str, label: str = "trial-1") -> tuple[Path, str]:
        """Create one trial worktree from an already-written policy.yaml --
        returns (worktree_path, branch_name)."""
        policy = yaml.safe_load(policy_path.read_text())
        worktree_path, branch_name, _ = cr.create_dev_worktree(
            policy, bench_root, model="m", harness=None, label=label, base_commit=commit
        )
        return worktree_path, branch_name

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


# --- reset-leaderboard --------------------------------------------------------


class TestRunResetLeaderboard:
    def _make_results(self, tmp_path: Path) -> tuple[Path, Path]:
        root = tmp_path / "root"
        results_dir = root / "results"
        run_dir = results_dir / "runs" / "run-1"
        run_dir.mkdir(parents=True)
        (run_dir / "slice-1.json").write_text("{}", encoding="utf-8")
        (results_dir / "leaderboard.json").write_text("{}", encoding="utf-8")
        return root, results_dir

    def test_dry_run_moves_nothing(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        root, results_dir = self._make_results(tmp_path)
        rc = cr.main(["reset-leaderboard", "--results-dir", str(results_dir)])
        assert rc == 0
        assert (results_dir / "runs" / "run-1" / "slice-1.json").is_file()
        assert (results_dir / "leaderboard.json").is_file()
        assert "dry run only" in capsys.readouterr().out

    def test_yes_archives_everything_and_recreates_empty_runs_dir(self, tmp_path: Path) -> None:
        root, results_dir = self._make_results(tmp_path)
        archive_dir = tmp_path / "archive-target"
        rc = cr.main(["reset-leaderboard", "--results-dir", str(results_dir), "--archive-dir", str(archive_dir), "--yes"])
        assert rc == 0
        assert not (results_dir / "leaderboard.json").exists()
        assert (results_dir / "runs").is_dir()
        assert not (results_dir / "runs" / "run-1").exists()
        assert (archive_dir / "runs" / "run-1" / "slice-1.json").is_file()
        assert (archive_dir / "leaderboard.json").is_file()

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
        assert not (archive_dir / "runs").exists()

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
        for command in ("setup", "analyze", "cleanup", "reset-leaderboard"):
            with pytest.raises(SystemExit) as exc_info:
                cr.main([command, "--help"])
            assert exc_info.value.code == 0
