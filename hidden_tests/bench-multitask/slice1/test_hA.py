"""Slice 1 hidden tests: the `tasks:` registry, `bench_lib.resolve_task`,
`bench_lib.repo_belongs_to_task` and the `parse_pinned_plan_commit`
relocation, derived from docs/plans/MULTI-TASK-PLAN-3SLICE.md's Slice 1
Acceptance Criteria.

Not visible to the Developer model. Copied into the grading worktree's tests/
directory and run there. Only surfaces the plan itself names are exercised;
every repository-membership claim is checked against real git repositories
and worktrees, never path strings.
"""

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import bench_lib  # noqa: E402

# The commit every trial of this task branches from; its policy.yaml holds the
# flat keys the relative-velocity entry must reproduce.
PRE_PLAN_COMMIT = "77b24c4"


def _entry(**overrides):
    entry = {
        "repo": "substrate/alpha-repo",
        "branch_prefix": "pm-eval-alpha",
        "worktree_root": "substrate/alpha-trials",
        "plan_file": "docs/ALPHA_PLAN.md",
        "provenance_file": "docs/ALPHA_PLAN.provenance.md",
        "hidden_tests_dir": "hidden_tests/alpha",
        "obligations_file": "hidden_tests/alpha/obligations.yaml",
        "expected_slices": 3,
        "measurement": {
            "production_paths": ["lib/**/*.py"],
            "test_paths": ["checks/**/*.py"],
            "doc_paths": ["notes/**/*.md"],
        },
    }
    entry.update(overrides)
    return entry


def _beta_entry(**overrides):
    entry = {
        "repo": "substrate/beta-repo",
        "branch_prefix": "pm-eval-beta",
        "worktree_root": None,
        "plan_file": "docs/BETA_PLAN.md",
        "provenance_file": "docs/BETA_PLAN.provenance.md",
        "hidden_tests_dir": "hidden_tests/beta",
        "obligations_file": "hidden_tests/beta/obligations-beta.yaml",
        "expected_slices": 2,
        "measurement": {
            "production_paths": ["src/**/*.py", "bin/*.py"],
            "test_paths": ["tests/**/*.py"],
            "doc_paths": ["*.md"],
        },
    }
    entry.update(overrides)
    return entry


def _policy(*, alpha=None, beta=None, default_task="beta"):
    """Two complete entries; the default is deliberately the second key, so
    resolving None cannot pass by picking the first configured entry."""
    return {
        "default_task": default_task,
        "tasks": {"alpha": alpha or _entry(), "beta": beta or _beta_entry()},
    }


def _plain(value):
    """Path-valued fields may come back as str or Path; compare as text."""
    return None if value is None else str(value)


def _assert_resolves_to(resolved, task_id, entry):
    assert resolved["task_id"] == task_id
    for key in (
        "repo",
        "branch_prefix",
        "worktree_root",
        "plan_file",
        "provenance_file",
        "hidden_tests_dir",
        "obligations_file",
    ):
        assert _plain(resolved[key]) == entry[key], key
    assert resolved["expected_slices"] == entry["expected_slices"]
    for bucket in ("production_paths", "test_paths", "doc_paths"):
        assert [str(g) for g in resolved["measurement"][bucket]] == entry[
            "measurement"
        ][bucket], bucket


def _git(*args, cwd=None):
    return subprocess.run(
        [
            "git",
            "-c",
            "user.name=bench",
            "-c",
            "user.email=bench@example.invalid",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def _make_repo(path):
    path.mkdir(parents=True)
    _git("init", "-q", str(path))
    (path / "README.md").write_text("fixture\n", encoding="utf-8")
    _git("-C", str(path), "add", "README.md")
    _git("-C", str(path), "commit", "-q", "-m", "init")
    return path


def _names_path(message, path):
    return str(path) in message or str(path.resolve()) in message


# --- registry_resolution -------------------------------------------------------


def test_resolve_task_none_resolves_the_default_task_entry():
    _assert_resolves_to(bench_lib.resolve_task(_policy(), None), "beta", _beta_entry())


def test_resolve_task_explicit_id_returns_that_entrys_exact_values():
    _assert_resolves_to(bench_lib.resolve_task(_policy(), "alpha"), "alpha", _entry())


def test_resolve_task_unknown_id_names_the_id_and_configured_ids():
    with pytest.raises(bench_lib.BenchLibError) as excinfo:
        bench_lib.resolve_task(_policy(), "does-not-exist")
    message = str(excinfo.value)
    assert "does-not-exist" in message
    assert "alpha" in message and "beta" in message


def test_real_policy_relative_velocity_entry_reproduces_the_pinned_flat_values():
    """The relative-velocity entry must equal what the pre-plan policy.yaml's
    flat keys and cohort_run/dev_check constants said, value for value."""
    pinned = yaml.safe_load(
        subprocess.run(
            ["git", "-C", str(REPO_ROOT), "show", f"{PRE_PLAN_COMMIT}:policy.yaml"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    )
    policy = yaml.safe_load((REPO_ROOT / "policy.yaml").read_text(encoding="utf-8"))
    expected = {
        "repo": pinned["relative_velocity_repo"],
        "branch_prefix": pinned["dev_branch_prefix"],
        "worktree_root": pinned["dev_worktree_root"],
        "plan_file": "docs/MERGER_RATE_PLAN-2SLICE.md",
        "provenance_file": "docs/MERGER_RATE_PLAN-2SLICE.provenance.md",
        "hidden_tests_dir": "hidden_tests",
        "obligations_file": "hidden_tests/obligations.yaml",
        "expected_slices": pinned["leaderboard"]["expected_slices"],
        "measurement": {
            bucket: pinned["measurement"][bucket]
            for bucket in ("production_paths", "test_paths", "doc_paths")
        },
    }
    _assert_resolves_to(
        bench_lib.resolve_task(policy, "relative-velocity"),
        "relative-velocity",
        expected,
    )


# --- entry_validation_fail_loud ------------------------------------------------


def test_entry_missing_a_required_key_names_the_task_and_the_key():
    beta = _beta_entry()
    del beta["obligations_file"]
    with pytest.raises(bench_lib.BenchLibError) as excinfo:
        bench_lib.resolve_task(_policy(beta=beta), "beta")
    assert "beta" in str(excinfo.value) and "obligations_file" in str(excinfo.value)


def test_entry_with_a_wrong_typed_key_names_the_task_and_the_key():
    with pytest.raises(bench_lib.BenchLibError) as excinfo:
        bench_lib.resolve_task(_policy(beta=_beta_entry(expected_slices="2")), "beta")
    assert "beta" in str(excinfo.value) and "expected_slices" in str(excinfo.value)


def test_entry_with_a_non_list_measurement_bucket_names_the_task_and_the_bucket():
    beta = _beta_entry()
    beta["measurement"]["test_paths"] = "tests/**/*.py"
    with pytest.raises(bench_lib.BenchLibError) as excinfo:
        bench_lib.resolve_task(_policy(beta=beta), "beta")
    assert "beta" in str(excinfo.value) and "test_paths" in str(excinfo.value)


def test_entry_with_non_positive_expected_slices_names_the_task_and_the_key():
    with pytest.raises(bench_lib.BenchLibError) as excinfo:
        bench_lib.resolve_task(_policy(alpha=_entry(expected_slices=0)), "alpha")
    assert "alpha" in str(excinfo.value) and "expected_slices" in str(excinfo.value)


def test_registry_with_a_non_string_task_key_is_a_named_error_not_a_crash():
    """A YAML-unquoted numeric task id must not escape as a raw TypeError
    while the unknown-id message lists the configured ids."""
    policy = {"default_task": "alpha", "tasks": {"alpha": _entry(), 7: _beta_entry()}}
    with pytest.raises(bench_lib.BenchLibError) as excinfo:
        bench_lib.resolve_task(policy, "does-not-exist")
    assert "7" in str(excinfo.value)


def test_null_worktree_root_is_accepted_and_preserved():
    resolved = bench_lib.resolve_task(
        _policy(alpha=_entry(worktree_root=None)), "alpha"
    )
    assert resolved["worktree_root"] is None


# --- repo_membership_real_git --------------------------------------------------


def test_configured_repo_itself_belongs(tmp_path):
    repo = _make_repo(tmp_path / "substrate")
    assert bench_lib.repo_belongs_to_task(repo, repo) is True


def test_registered_worktree_of_the_configured_repo_belongs(tmp_path):
    repo = _make_repo(tmp_path / "substrate")
    trial = tmp_path / "substrate-trial-1"
    _git("-C", str(repo), "worktree", "add", "-q", "-b", "trial-1", str(trial))
    assert bench_lib.repo_belongs_to_task(trial, repo) is True


def test_unrelated_repository_does_not_belong(tmp_path):
    repo = _make_repo(tmp_path / "substrate")
    _git(
        "-C",
        str(repo),
        "worktree",
        "add",
        "-q",
        "-b",
        "trial-1",
        str(tmp_path / "substrate-trial-1"),
    )
    other = _make_repo(tmp_path / "other")
    assert bench_lib.repo_belongs_to_task(other, repo) is False


def test_worktree_of_a_bare_configured_repo_belongs(tmp_path):
    seed = _make_repo(tmp_path / "seed")
    bare = tmp_path / "substrate.git"
    _git("clone", "-q", "--bare", str(seed), str(bare))
    trial = tmp_path / "bare-trial-1"
    _git("-C", str(bare), "worktree", "add", "-q", "-b", "trial-1", str(trial))
    assert bench_lib.repo_belongs_to_task(trial, bare) is True


def test_configured_path_that_is_not_a_git_repo_raises_naming_it(tmp_path):
    configured = tmp_path / "plain-directory"
    configured.mkdir()
    candidate_repo = _make_repo(tmp_path / "elsewhere")
    candidate = tmp_path / "elsewhere-trial"
    _git(
        "-C",
        str(candidate_repo),
        "worktree",
        "add",
        "-q",
        "-b",
        "trial",
        str(candidate),
    )
    with pytest.raises(bench_lib.BenchLibError) as excinfo:
        bench_lib.repo_belongs_to_task(candidate, configured)
    assert _names_path(str(excinfo.value), configured)


def test_missing_configured_path_raises_naming_it(tmp_path):
    configured = tmp_path / "never-created"
    candidate = _make_repo(tmp_path / "elsewhere")
    with pytest.raises(bench_lib.BenchLibError) as excinfo:
        bench_lib.repo_belongs_to_task(candidate, configured)
    assert str(configured.name) in str(excinfo.value)


# --- pinned_commit_relocation --------------------------------------------------

PINNED = "0123456789abcdef0123456789abcdef01234567"


def test_parse_pinned_plan_commit_lives_in_bench_lib_and_reads_the_line(tmp_path):
    provenance = tmp_path / "PLAN.provenance.md"
    provenance.write_text(
        f"# Provenance\n\nVendored verbatim.\n\nPinned commit: `{PINNED}`\n",
        encoding="utf-8",
    )
    assert bench_lib.parse_pinned_plan_commit(provenance) == PINNED


def test_parse_pinned_plan_commit_missing_file_raises_bench_lib_error_naming_it(
    tmp_path,
):
    provenance = tmp_path / "absent.provenance.md"
    with pytest.raises(bench_lib.BenchLibError) as excinfo:
        bench_lib.parse_pinned_plan_commit(provenance)
    assert "absent.provenance.md" in str(excinfo.value)


def test_parse_pinned_plan_commit_without_a_pinned_line_raises_bench_lib_error_naming_it(
    tmp_path,
):
    provenance = tmp_path / "unpinned.provenance.md"
    provenance.write_text(
        "# Provenance\n\nNo commit recorded here.\n", encoding="utf-8"
    )
    with pytest.raises(bench_lib.BenchLibError) as excinfo:
        bench_lib.parse_pinned_plan_commit(provenance)
    assert "unpinned.provenance.md" in str(excinfo.value)
