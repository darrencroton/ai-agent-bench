import os
import subprocess
import sys

import pytest

import branch_check as bc


def _git(args, cwd):
    subprocess.run(["git"] + args, cwd=cwd, check=True, capture_output=True)


def _init_repo(tmp_path, name):
    repo = tmp_path / name
    repo.mkdir()
    _git(["init", "-q"], repo)
    _git(["config", "user.email", "t@t.com"], repo)
    _git(["config", "user.name", "t"], repo)
    return repo


def _commit_all(repo, message):
    _git(["add", "-A"], repo)
    _git(["commit", "-q", "-m", message], repo)


def _rev(repo):
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo,
                           capture_output=True, text=True, check=True).stdout.strip()


# -- branch_slug --------------------------------------------------------

@pytest.mark.parametrize("branch,expected", [
    ("simple-branch", "simple-branch"),
    ("merger-rate-revised/mixed-ornith-1.5-397b-q6-2", "mixed-ornith-1.5-397b-q6-2"),
    ("plans/nested/path/model-name", "model-name"),
])
def test_branch_slug_takes_last_path_component(branch, expected):
    assert bc.branch_slug(branch) == expected


@pytest.mark.parametrize("branch", ["plans/", "some/plan/."])
def test_branch_slug_raises_when_no_safe_slug_can_be_derived(branch):
    """A trailing '/' yields an empty last component; a last component of
    '.' is syntactically 'safe' by the character-class regex alone but is a
    traversal-adjacent value this function explicitly excludes -- both must
    raise, never silently produce '' or '.' as a run id / model field."""
    with pytest.raises(SystemExit, match="cannot derive"):
        bc.branch_slug(branch)


# -- compute_full_diff / transplant_full_diff --------------------------------
#
# Together these replace the old authorized-surface-only install_branch_files:
# the P1 fix is that the COMPLETE diff against --base-ref is installed, not
# just the task's authorized_surface, so an unauthorized change is visible in
# the resulting worktree for grade_trial.py's own scope check to catch.

def test_transplant_full_diff_installs_unauthorized_changes_too(tmp_path):
    """The end-to-end case the P1 finding named: a branch changes one
    authorized and one unauthorized path relative to --base-ref. The old
    authorized-surface-only installer would have silently left the
    unauthorized change out of the worktree; the full-diff transplant must
    not."""
    repo = _init_repo(tmp_path, "src_repo")
    (repo / "src").mkdir()
    (repo / "src" / "authorized.py").write_text("# base authorized\n")
    (repo / "src" / "frozen.py").write_text("# base frozen\n")
    _commit_all(repo, "base")
    base_ref = _rev(repo)

    _git(["checkout", "-q", "-b", "feature/model-x"], repo)
    (repo / "src" / "authorized.py").write_text("# branch authorized, changed\n")
    (repo / "src" / "frozen.py").write_text("# branch SNUCK IN a change here\n")
    _commit_all(repo, "branch change touches both")

    dest = tmp_path / "dest"
    dest.mkdir()
    (dest / "src").mkdir()
    (dest / "src" / "authorized.py").write_text("# base authorized\n")
    (dest / "src" / "frozen.py").write_text("# base frozen\n")

    changes = bc.compute_full_diff(str(repo), base_ref, "feature/model-x")
    touched = bc.transplant_full_diff(str(repo), "feature/model-x", changes, str(dest))

    # The unauthorized path is NOT filtered out -- it is transplanted exactly
    # like the authorized one, so grade_trial.py's own scope-discipline check
    # (which flags any change outside authorized_surface) can see it.
    assert set(touched) == {"src/authorized.py", "src/frozen.py"}
    assert (dest / "src" / "authorized.py").read_text() == "# branch authorized, changed\n"
    assert (dest / "src" / "frozen.py").read_text() == "# branch SNUCK IN a change here\n"


def test_transplant_full_diff_applies_deletions(tmp_path):
    repo = _init_repo(tmp_path, "src_repo")
    (repo / "src").mkdir()
    (repo / "src" / "doomed.py").write_text("# will be deleted\n")
    _commit_all(repo, "base")
    base_ref = _rev(repo)

    _git(["checkout", "-q", "-b", "feature/model-x"], repo)
    (repo / "src" / "doomed.py").unlink()
    _commit_all(repo, "delete it")

    dest = tmp_path / "dest"
    (dest / "src").mkdir(parents=True)
    (dest / "src" / "doomed.py").write_text("# will be deleted\n")

    changes = bc.compute_full_diff(str(repo), base_ref, "feature/model-x")
    touched = bc.transplant_full_diff(str(repo), "feature/model-x", changes, str(dest))

    assert touched == []
    assert not (dest / "src" / "doomed.py").exists()


# -- check_frozen_unchanged -------------------------------------------------
#
# Now compares the branch's OWN STARTING POINT (base_ref), never its tip --
# see the module docstring and check_frozen_unchanged's own docstring for why.

def test_check_frozen_unchanged_compares_base_ref_content_directly(tmp_path):
    """check_frozen_unchanged() takes base_ref, not a branch -- there is no
    branch tip it could read even if it wanted to (see the module docstring
    for why substrate identity must be checked against the starting point,
    never the tip)."""
    root = _init_repo(tmp_path, "root")
    (root / "docs.txt").write_text("frozen content\n")
    (root / "shared.txt").write_text("shared content\n")
    _commit_all(root, "baseline")
    _git(["tag", "frozen-substrate"], root)

    src_repo = _init_repo(tmp_path, "src_repo")
    (src_repo / "docs.txt").write_text("frozen content\n")  # identical to baseline
    (src_repo / "shared.txt").write_text("shared content\n")  # also identical at base
    _commit_all(src_repo, "base")
    base_ref = _rev(src_repo)

    result = bc.check_frozen_unchanged(
        str(src_repo), base_ref, str(root), "frozen-substrate",
        ["docs.txt", "shared.txt", "absent_at_base.txt"],
    )

    assert result["matched"] == ["docs.txt", "shared.txt"]
    assert result["mismatched"] == []
    assert result["missing_at_base"] == ["absent_at_base.txt"]


def test_check_frozen_unchanged_reports_a_genuine_base_mismatch(tmp_path):
    root = _init_repo(tmp_path, "root")
    (root / "shared.txt").write_text("shared content\n")
    _commit_all(root, "baseline")
    _git(["tag", "frozen-substrate"], root)

    src_repo = _init_repo(tmp_path, "src_repo")
    (src_repo / "shared.txt").write_text("a genuinely different starting point\n")
    _commit_all(src_repo, "base")
    base_ref = _rev(src_repo)

    result = bc.check_frozen_unchanged(
        str(src_repo), base_ref, str(root), "frozen-substrate", ["shared.txt"])

    assert result["mismatched"] == ["shared.txt"]


# -- check_installed_python_parses -------------------------------------------------

def test_check_installed_python_parses_reports_syntax_errors_and_skips_non_python(tmp_path):
    dest = tmp_path / "dest"
    (dest / "src").mkdir(parents=True)
    (dest / "src" / "good.py").write_text("def f():\n    return 1\n")
    (dest / "src" / "bad.py").write_text("def f(:\n    return 1\n")
    (dest / "notes.txt").write_text("not python -- must not be parsed\n")

    errors = bc.check_installed_python_parses(
        str(dest), ["src/good.py", "src/bad.py", "notes.txt"])

    assert [rel for rel, _msg in errors] == ["src/bad.py"]


# -- --label validation -------------------------------------------------

@pytest.mark.parametrize("value", ["../escape", "a/b", "/etc/passwd", "..", ".", ""])
def test_validate_component_rejects_path_unsafe_label(value):
    with pytest.raises(SystemExit):
        bc._validate_component(value, "--label")


@pytest.mark.parametrize("value", ["ceiling-run.1", "model-x", None])
def test_validate_component_accepts_safe_label(value):
    bc._validate_component(value, "--label")  # must not raise


# -- build_manifest -------------------------------------------------

def test_build_manifest_uses_pmbranch_model_and_none_harness():
    """This is what keeps PM-branch records out of every leaderboard cohort
    -- aggregate.py's load_records and profile_view.py both filter on
    harness=='none', and model='pmbranch/<slug>' is what makes such a record
    unmistakable in a listing next to real trials."""
    manifest = bc.build_manifest(
        run_id="20260907T000000Z-PMBRANCH-001-merger-rate-feature-model-x-abc123",
        task_id="001-merger-rate-feature", slug="model-x",
        baseline_ref="frozen-substrate", before_head="abc123", venv_setup_seconds=12.34,
        changed_files=["src/merger_rate.py"], worktree="/tmp/worktree",
        src_repo="/tmp/src_repo", branch="plans/model-x", branch_sha="deadbeef",
        base_ref="basecommit123", missing=[],
        frozen_check={"matched": ["docs.txt"], "mismatched": [], "missing_at_base": []},
    )

    assert manifest["model"] == "pmbranch/model-x"
    assert manifest["harness"] == "none"
    assert manifest["effort"] is None
    assert manifest["timed_out"] is False
    assert manifest["committed"] is False
    assert manifest["venv_setup_seconds"] == 12.3
    assert manifest["before_head"] == "abc123"
    assert manifest["changed_files"] == ["src/merger_rate.py"]
    assert manifest["worktree_path"] == "/tmp/worktree"
    assert manifest["token_usage"] is None
    assert manifest["base_ref"] == "basecommit123"
    # a realistic dotted slug must survive into the model field, and
    # missing authorized paths must be passed through as missing_deliverables
    dotted = bc.build_manifest(
        run_id="run-1", task_id="001-merger-rate-feature", slug="mixed-ornith-1.5-397b-q6-2",
        baseline_ref="frozen-substrate", before_head="abc123", venv_setup_seconds=1.0,
        changed_files=[], worktree="/tmp/worktree", src_repo="/tmp/src", branch="b",
        branch_sha="deadbeef", base_ref="basecommit456", missing=["src/foo.py"],
        frozen_check={"matched": [], "mismatched": [], "missing_at_base": []})
    assert dotted["model"] == "pmbranch/mixed-ornith-1.5-397b-q6-2"
    assert dotted["missing_deliverables"] == ["src/foo.py"]


# -- end-to-end: fail closed before any worktree is created ------------------

def test_main_fails_closed_before_creating_a_worktree_on_substrate_mismatch(tmp_path, monkeypatch):
    """The second P1 fix's core guarantee: a branch whose starting point does
    not match this repo's own baseline for a real task's frozen_unchanged
    files must be refused BEFORE any worktree is created -- not graded with a
    warning. Uses the real repo and a real task (001-merger-rate-feature) so
    this exercises the actual main() control flow, with a synthetic --repo
    standing in for relative-velocity."""
    root = bc.repo_root()
    worktrees_dir = os.path.join(root, "eval", "results", "tmp", "worktrees")
    before = set(os.listdir(worktrees_dir)) if os.path.isdir(worktrees_dir) else set()

    src_repo = _init_repo(tmp_path, "fake_relative_velocity")
    (src_repo / "src").mkdir()
    # src/pair_finder.py is real Task 001's frozen_unchanged content -- give
    # the synthetic repo's OWN base_ref a deliberately different version, so
    # check_frozen_unchanged must report a mismatch against this repo's real
    # frozen-substrate baseline.
    (src_repo / "src" / "pair_finder.py").write_text(
        "# deliberately incompatible starting point -- not the real baseline\n")
    _commit_all(src_repo, "base")
    base_ref = _rev(src_repo)
    _git(["checkout", "-q", "-b", "feature/model-x"], src_repo)

    # Safety net, not just an assertion-ordering hope: if main()'s ordering
    # ever regresses, this makes the test fail loudly instead of silently
    # creating a real worktree in the developer's actual checkout.
    real_run = subprocess.run

    def _guarded_run(cmd, *args, **kwargs):
        if isinstance(cmd, list) and "worktree" in cmd and "add" in cmd:
            pytest.fail(f"main() attempted to create a worktree before the substrate check "
                        f"failed closed: {cmd}")
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(bc.subprocess, "run", _guarded_run)
    monkeypatch.setattr(sys, "argv", [
        "branch_check.py", "--task", "001-merger-rate-feature",
        "--repo", str(src_repo), "--branch", "feature/model-x", "--base-ref", base_ref,
    ])

    with pytest.raises(SystemExit, match="substrate identity check FAILED"):
        bc.main()

    after = set(os.listdir(worktrees_dir)) if os.path.isdir(worktrees_dir) else set()
    assert after == before, "no worktree directory may be created on a substrate-check failure"
