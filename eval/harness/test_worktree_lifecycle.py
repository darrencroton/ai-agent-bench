import argparse
import os
import subprocess
from unittest.mock import patch

import worktree_lifecycle as wl


def test_human_formats_bytes_through_gb():
    assert wl.human(512) == "512B"
    assert wl.human(2048) == "2KB"
    assert wl.human(5 * 1024 * 1024) == "5MB"
    assert wl.human(3 * 1024 * 1024 * 1024) == "3GB"


def test_registered_trial_worktrees_filters_to_trial_worktrees_dir(tmp_path):
    root = str(tmp_path)
    live = os.path.join(root, "eval", "results", "tmp", "worktrees", "run-1")
    os.makedirs(live)
    # "run-gone" is registered per git but its directory is already missing
    # (e.g. git reports it prunable) -- must be excluded, not crash later
    # code that does `cwd=<that path>`.
    gone = os.path.join(root, "eval", "results", "tmp", "worktrees", "run-gone")
    porcelain = (
        f"worktree {root}\n"
        f"HEAD abc123\n"
        f"branch refs/heads/main\n"
        f"\n"
        f"worktree {live}\n"
        f"HEAD def456\n"
        f"detached\n"
        f"\n"
        f"worktree {gone}\n"
        f"HEAD 789abc\n"
        f"detached\n"
        f"prunable gitdir file points to non-existent location\n"
        f"\n"
    )
    with patch.object(wl.subprocess, "run") as run:
        run.return_value = subprocess.CompletedProcess([], 0, stdout=porcelain)
        result = wl.registered_trial_worktrees(root)

    assert result == {"run-1": live}


def _git(args, cwd):
    subprocess.run(["git"] + args, cwd=cwd, check=True, capture_output=True)


def _init_repo_with_worktree(tmp_path):
    """A real git repo + a real `git worktree add`, mirroring what
    run_trial.py does -- exercises the actual diff/staging path rather than
    mocking git."""
    root = tmp_path / "root"
    root.mkdir()
    _git(["init", "-q"], root)
    _git(["config", "user.email", "t@t.com"], root)
    _git(["config", "user.name", "t"], root)
    (root / "src.py").write_text("original\n")
    _git(["add", "-A"], root)
    _git(["commit", "-q", "-m", "base"], root)
    before_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                                  capture_output=True, text=True, check=True).stdout.strip()

    wt_dir = root / "eval" / "results" / "tmp" / "worktrees" / "run-1"
    wt_dir.parent.mkdir(parents=True)
    _git(["worktree", "add", "--detach", str(wt_dir), before_head], root)

    (wt_dir / "src.py").write_text("changed\n")
    (wt_dir / "new_file.py").write_text("new\n")
    return str(root), str(wt_dir), before_head


def test_cmd_archive_captures_a_real_submission_diff(tmp_path):
    root, _wt_dir, before_head = _init_repo_with_worktree(tmp_path)
    manifest_dir = os.path.join(root, "eval", "results", "tmp", "manifests")
    os.makedirs(manifest_dir, exist_ok=True)
    import json
    with open(os.path.join(manifest_dir, "run-1.json"), "w") as f:
        json.dump({"before_head": before_head}, f)

    args = argparse.Namespace(run_id=["run-1"], all=False)
    ok = wl.cmd_archive(root, args)

    assert ok
    patch_path = os.path.join(root, "archive", "worktrees", "run-1", "submission.patch")
    with open(patch_path) as f:
        diff = f.read()
    assert "-original" in diff and "+changed" in diff
    assert "new_file.py" in diff
    assert os.path.exists(os.path.join(root, "archive", "worktrees", "run-1", "manifest.json"))


def test_cmd_prune_refuses_without_archived_evidence(tmp_path):
    root, _wt_dir, _ = _init_repo_with_worktree(tmp_path)
    args = argparse.Namespace(run_id=["run-1"], all=False, force=False)

    with patch.object(wl.run_trial, "remove_worktree") as remove:
        ok = wl.cmd_prune(root, args)

    assert not ok
    remove.assert_not_called()


def test_cmd_prune_proceeds_with_force_despite_missing_evidence(tmp_path):
    root, wt_dir, _ = _init_repo_with_worktree(tmp_path)
    args = argparse.Namespace(run_id=["run-1"], all=False, force=True)

    with patch.object(wl.run_trial, "remove_worktree", return_value=0) as remove:
        ok = wl.cmd_prune(root, args)

    assert ok
    remove.assert_called_once_with(root, wt_dir)


def test_cmd_prune_proceeds_once_archived(tmp_path):
    root, wt_dir, before_head = _init_repo_with_worktree(tmp_path)
    manifest_dir = os.path.join(root, "eval", "results", "tmp", "manifests")
    os.makedirs(manifest_dir, exist_ok=True)
    import json
    with open(os.path.join(manifest_dir, "run-1.json"), "w") as f:
        json.dump({"before_head": before_head}, f)
    wl.cmd_archive(root, argparse.Namespace(run_id=["run-1"], all=False))

    with patch.object(wl.run_trial, "remove_worktree", return_value=0) as remove:
        ok = wl.cmd_prune(root, argparse.Namespace(run_id=["run-1"], all=False, force=False))

    assert ok
    remove.assert_called_once_with(root, wt_dir)


def test_cmd_prune_refuses_when_worktree_changed_after_archiving(tmp_path):
    root, wt_dir, before_head = _init_repo_with_worktree(tmp_path)
    manifest_dir = os.path.join(root, "eval", "results", "tmp", "manifests")
    os.makedirs(manifest_dir, exist_ok=True)
    import json
    with open(os.path.join(manifest_dir, "run-1.json"), "w") as f:
        json.dump({"before_head": before_head}, f)
    wl.cmd_archive(root, argparse.Namespace(run_id=["run-1"], all=False))

    # Worktree keeps changing after the patch was captured -- the archived
    # patch is now stale evidence of what's actually there.
    with open(os.path.join(wt_dir, "src.py"), "w") as f:
        f.write("changed again\n")

    with patch.object(wl.run_trial, "remove_worktree") as remove:
        ok = wl.cmd_prune(root, argparse.Namespace(run_id=["run-1"], all=False, force=False))

    assert not ok
    remove.assert_not_called()


def test_cmd_archive_reports_failure_when_git_diff_fails(tmp_path):
    root, _wt_dir, before_head = _init_repo_with_worktree(tmp_path)
    manifest_dir = os.path.join(root, "eval", "results", "tmp", "manifests")
    os.makedirs(manifest_dir, exist_ok=True)
    import json
    with open(os.path.join(manifest_dir, "run-1.json"), "w") as f:
        json.dump({"before_head": before_head}, f)

    real_run = wl.subprocess.run

    def fake_run(cmd, **kwargs):
        if cmd[:2] == ["git", "diff"]:
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="boom")
        return real_run(cmd, **kwargs)

    with patch.object(wl.subprocess, "run", side_effect=fake_run):
        ok = wl.cmd_archive(root, argparse.Namespace(run_id=["run-1"], all=False))

    assert not ok
    assert not os.path.exists(os.path.join(root, "archive", "worktrees", "run-1", "submission.patch"))


def test_cmd_prune_skips_unregistered_run_id(tmp_path):
    root, _, _ = _init_repo_with_worktree(tmp_path)
    args = argparse.Namespace(run_id=["not-a-real-run"], all=False, force=False)

    with patch.object(wl.run_trial, "remove_worktree") as remove:
        ok = wl.cmd_prune(root, args)

    assert not ok
    remove.assert_not_called()
