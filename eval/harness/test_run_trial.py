import os
from unittest.mock import patch

import grade_trial
import run_trial


def test_trial_environment_prefers_trial_python_without_hiding_other_tools():
    old_venv = "/operator/venv"
    fresh_venv = "/trial/venv"
    env = run_trial.trial_environment(
        {"PATH": f"{old_venv}/bin{os.pathsep}/usr/bin", "VIRTUAL_ENV": old_venv,
         "PYTHONHOME": "/operator/python", "PYTHONPATH": "/operator/packages"},
        fresh_venv,
    )

    assert env["VIRTUAL_ENV"] == fresh_venv
    assert env["PATH"] == (
        f"{fresh_venv}/bin{os.pathsep}{old_venv}/bin{os.pathsep}/usr/bin"
    )
    assert "PYTHONHOME" not in env
    assert "PYTHONPATH" not in env


def test_provision_trial_venv_uses_runner_python_and_worktree_requirements(tmp_path):
    worktree = str(tmp_path)
    with patch.object(run_trial.subprocess, "run") as run:
        env, duration = run_trial.provision_trial_venv(worktree, {"PATH": "/usr/bin"})

    venv_dir = os.path.join(worktree, "venv")
    assert run.call_args_list[0].args[0] == [run_trial.sys.executable, "-m", "venv", venv_dir]
    assert run.call_args_list[1].args[0] == [
        os.path.join(venv_dir, "bin", "python"), "-m", "pip", "install", "--quiet",
        "--disable-pip-version-check", "--requirement", os.path.join(worktree, "requirements.txt"),
    ]
    assert all(call.kwargs["cwd"] == worktree and call.kwargs["check"] for call in run.call_args_list)
    assert env["VIRTUAL_ENV"] == venv_dir
    assert duration >= 0


def test_provision_trial_venv_creates_an_isolated_environment(tmp_path):
    (tmp_path / "requirements.txt").write_text("")

    env, _ = run_trial.provision_trial_venv(str(tmp_path), {"PATH": os.environ["PATH"]})

    venv_python = tmp_path / "venv" / "bin" / "python"
    assert venv_python.exists()
    assert env["VIRTUAL_ENV"] == str(tmp_path / "venv")
    selected_python = run_trial.subprocess.run(
        ["python", "-c", "import sys; print(sys.prefix)"],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert selected_python.stdout.strip() == str(tmp_path / "venv")


def test_trial_report_includes_venv_setup_time(tmp_path):
    record = {
        "run_id": "test-run", "task_id": "001", "model": "test-model", "harness": "test",
        "duration_seconds": 12.3, "venv_setup_seconds": 4.5, "timed_out": False,
        "committed": False, "changed_files": [],
        "rubric_profile": "default", "complete_submission": True, "missing_deliverables": [],
        "gate_status": "not_applicable", "failed_gates": [], "integrity_violation": False,
        "judge_same_model": False, "judge_status": "no_judge_configured",
        "category_scores": {}, "category_detail": {},
        "deterministic_score": 0.0, "judged_scores": {}, "composite_score": 0.0,
        "scored_weight_fraction": 1.0, "provenance": {},
    }
    report = tmp_path / "report.md"

    grade_trial.write_report(report, record, {
        "categories": [],
        "profiles": {"default": {"weights": {}, "gates": {}}},
    })

    assert "Model duration: 12.3s | venv setup: 4.5s" in report.read_text()
