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


def _write_policy(tmp_path: Path, skill_dir: Path) -> Path:
    policy = {
        "backend": "local",
        "pm_scripts_dir": str(skill_dir / "scripts"),
        "lint_script": str(tmp_path / "lint.py"),
        "health_script": str(tmp_path / "health.py"),
        "python_interpreter": str(tmp_path / "python3"),
        "subprocess_timeout_seconds": 600,
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
        skill_dir = _write_skill_md(tmp_path)
        policy_path = _write_policy(tmp_path, skill_dir)
        rc = cr.main(["--policy", str(policy_path), "setup", "--model", "my-model", "--harness", "claude"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "Harness: claude (model my-model)" in out
        assert "Steps to follow" in out
        assert "python tools/cohort_run.py analyze" in out
        assert "no reviewer gap" in out

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
        rc = cr.main(["--policy", str(policy_path), "setup", "--model", "my-model"])
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


# --- cleanup ----------------------------------------------------------------


class TestRunCleanup:
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
        rc = cr.main(["cleanup", "--results-dir", str(results_dir)])
        assert rc == 0
        assert (results_dir / "runs" / "run-1" / "slice-1.json").is_file()
        assert (results_dir / "leaderboard.json").is_file()
        assert "dry run only" in capsys.readouterr().out

    def test_yes_archives_everything_and_recreates_empty_runs_dir(self, tmp_path: Path) -> None:
        root, results_dir = self._make_results(tmp_path)
        archive_dir = tmp_path / "archive-target"
        rc = cr.main(["cleanup", "--results-dir", str(results_dir), "--archive-dir", str(archive_dir), "--yes"])
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
            ["cleanup", "--results-dir", str(results_dir), "--archive-dir", str(archive_dir), "--run-id", "run-1", "--yes"]
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
            cr.main(["cleanup", "--results-dir", str(results_dir), "--archive-dir", str(archive_dir), "--yes"])

        assert (results_dir / "runs" / "run-1" / "slice-1.json").is_file()
        assert (results_dir / "leaderboard.json").is_file()
        assert not (archive_dir / "runs").exists()

    def test_unknown_run_id_is_a_named_error(self, tmp_path: Path) -> None:
        root, results_dir = self._make_results(tmp_path)
        with pytest.raises(cr.CohortRunError, match="no results found for run_id"):
            cr.main(["cleanup", "--results-dir", str(results_dir), "--run-id", "does-not-exist"])

    def test_nothing_to_archive_is_not_an_error(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        results_dir = tmp_path / "empty-results"
        rc = cr.main(["cleanup", "--results-dir", str(results_dir)])
        assert rc == 0
        assert "nothing under" in capsys.readouterr().out

    def test_yes_refuses_to_overwrite_an_existing_archive_entry(self, tmp_path: Path) -> None:
        root, results_dir = self._make_results(tmp_path)
        archive_dir = tmp_path / "archive-target"
        (archive_dir / "runs").mkdir(parents=True)
        with pytest.raises(cr.CohortRunError, match="refusing to overwrite existing archive entries"):
            cr.main(["cleanup", "--results-dir", str(results_dir), "--archive-dir", str(archive_dir), "--yes"])


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
        for command in ("setup", "analyze", "cleanup"):
            with pytest.raises(SystemExit) as exc_info:
                cr.main([command, "--help"])
            assert exc_info.value.code == 0
