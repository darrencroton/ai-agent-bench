import subprocess

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


# -- install_branch_files -------------------------------------------------

def test_install_branch_files_installs_present_and_reports_missing_without_skipping(tmp_path):
    repo = _init_repo(tmp_path, "src_repo")
    (repo / "src").mkdir()
    (repo / "tests").mkdir()
    (repo / "src" / "foo.py").write_text("# base foo\n")
    (repo / "tests" / "test_foo.py").write_text("# base tests\n")
    _commit_all(repo, "base")
    _git(["checkout", "-q", "-b", "feature/model-x"], repo)
    (repo / "src" / "foo.py").write_text("# branch foo, byte for byte\n")
    _commit_all(repo, "branch change")

    meta = {"authorized_surface": ["src/foo.py", "tests/test_foo.py", "src/never_created.py"]}
    dest = tmp_path / "dest"
    dest.mkdir()

    installed, missing = bc.install_branch_files(str(repo), "feature/model-x", meta, str(dest))

    assert installed == ["src/foo.py", "tests/test_foo.py"]
    assert missing == ["src/never_created.py"]  # reported, not silently dropped
    assert (dest / "src" / "foo.py").read_text() == "# branch foo, byte for byte\n"
    assert (dest / "tests" / "test_foo.py").read_text() == "# base tests\n"


# -- check_frozen_unchanged -------------------------------------------------

def test_check_frozen_unchanged_reports_matched_mismatched_and_missing(tmp_path):
    root = _init_repo(tmp_path, "root")
    (root / "docs.txt").write_text("frozen content\n")
    (root / "shared.txt").write_text("shared content\n")
    _commit_all(root, "baseline")
    _git(["tag", "frozen-substrate"], root)

    src_repo = _init_repo(tmp_path, "src_repo")
    (src_repo / "docs.txt").write_text("frozen content\n")  # identical to baseline
    (src_repo / "shared.txt").write_text("DIFFERENT content\n")  # diverged
    _commit_all(src_repo, "branch")
    _git(["branch", "feature/model-x"], src_repo)

    result = bc.check_frozen_unchanged(
        str(src_repo), "feature/model-x", str(root), "frozen-substrate",
        ["docs.txt", "shared.txt", "absent_on_branch.txt"],
    )

    assert result["matched"] == ["docs.txt"]
    assert result["mismatched"] == ["shared.txt"]
    assert result["missing_on_branch"] == ["absent_on_branch.txt"]


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
        missing=[], frozen_check={"matched": ["docs.txt"], "mismatched": [], "missing_on_branch": []},
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
    # a realistic dotted slug must survive into the model field, and
    # missing authorized paths must be passed through as missing_deliverables
    dotted = bc.build_manifest(
        run_id="run-1", task_id="001-merger-rate-feature", slug="mixed-ornith-1.5-397b-q6-2",
        baseline_ref="frozen-substrate", before_head="abc123", venv_setup_seconds=1.0,
        changed_files=[], worktree="/tmp/worktree", src_repo="/tmp/src", branch="b",
        branch_sha="deadbeef", missing=["src/foo.py"],
        frozen_check={"matched": [], "mismatched": [], "missing_on_branch": []})
    assert dotted["model"] == "pmbranch/mixed-ornith-1.5-397b-q6-2"
    assert dotted["missing_deliverables"] == ["src/foo.py"]
