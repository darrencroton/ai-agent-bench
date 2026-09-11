"""Tests for tools/dev_check.py (Tool 1).

Run with plain pytest from the repo root: `pytest tests/test_dev_check.py`.
These tests use synthetic fixtures (a throwaway git repo, hand-written
run.json) and monkeypatch/stub the external quality tools -- they never
invoke the real lint.py/health.py subprocesses or a real relative-velocity
checkout. The obligation-map tests are the one deliberate exception: they
validate hidden_tests/obligations.yaml against the real, checked-in test
files by parsing them with `ast`, not a stub.
"""

from __future__ import annotations

import ast
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import dev_check  # noqa: E402


# --- helpers -----------------------------------------------------------


def _collect_test_function_names(path: Path) -> set[str]:
    """Every top-level `def test_*(...)` in a file, via static AST parsing --
    mirrors pytest's own default collection convention without importing the
    module (the hidden tests import h5py/numpy, which this repo's own
    requirements.txt deliberately excludes)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_") and node.col_offset == 0
    }


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "dev-repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=repo, check=True)
    return repo


# --- obligations.yaml validated against the real hidden test files --------


class TestObligationMapAgainstRealFiles:
    # finding 10: this is the one integration check kept here. It already
    # calls node_to_group_map() (which raises on any duplicated node) and its
    # own set-equality assertion below catches an unknown node in the map or
    # a real test function missing from it -- exactly the guarantees two
    # neighbouring tests used to check separately against synthetic input
    # that this real map never triggers. Dropped as redundant, not as
    # untested: the malformed-map behaviour itself is still covered by
    # TestObligationMapFailsLoudlyOnDefects below, against synthetic data
    # that actually exercises each failure.
    def test_every_real_test_function_is_mapped_exactly_once(self) -> None:
        obligations = dev_check.load_obligations(REPO_ROOT)
        for slice_number, slice_map in obligations["slices"].items():
            source_dir = REPO_ROOT / slice_map["source_dir"]
            expected_nodes = {
                f"tests/{filename}::{name}"
                for filename in dev_check.HIDDEN_TEST_FILENAMES
                for name in _collect_test_function_names(source_dir / filename)
            }
            mapped_nodes = dev_check.node_to_group_map(slice_map["obligations"])
            assert set(mapped_nodes) == expected_nodes, (
                f"slice {slice_number}: obligations.yaml's node set does not exactly match the real test files "
                f"(missing from map: {sorted(expected_nodes - set(mapped_nodes))}, "
                f"in map but not a real test: {sorted(set(mapped_nodes) - expected_nodes)})"
            )


# --- loud failures on a malformed obligation map --------------------------


class TestObligationMapFailsLoudlyOnDefects:
    _GROUPS = [
        {"id": "group_a", "tests": ["tests/test_hA.py::test_one", "tests/test_hA.py::test_two"]},
        {"id": "group_b", "tests": ["tests/test_hA.py::test_three"]},
    ]

    def test_unmapped_collected_node_fails_loudly(self) -> None:
        outcomes = {
            "tests/test_hA.py::test_one": "passed",
            "tests/test_hA.py::test_two": "passed",
            "tests/test_hA.py::test_three": "passed",
            "tests/test_hA.py::test_unexpected": "passed",
        }
        with pytest.raises(dev_check.DevCheckError, match="test_unexpected"):
            dev_check.score_correctness(outcomes, self._GROUPS, slice_number=1)

    def test_mapped_but_missing_node_fails_loudly(self) -> None:
        outcomes = {
            "tests/test_hA.py::test_one": "passed",
            "tests/test_hA.py::test_two": "passed",
            # test_three never collected.
        }
        with pytest.raises(dev_check.DevCheckError, match="test_three"):
            dev_check.score_correctness(outcomes, self._GROUPS, slice_number=1)

    def test_duplicated_node_fails_loudly(self) -> None:
        groups = [
            {"id": "group_a", "tests": ["tests/test_hA.py::test_one"]},
            {"id": "group_b", "tests": ["tests/test_hA.py::test_one"]},
        ]
        with pytest.raises(dev_check.DevCheckError, match="test_one"):
            dev_check.node_to_group_map(groups)


# --- correctness scoring (well-formed map) --------------------------------


def test_score_correctness_computes_per_group_fractions() -> None:
    groups = [
        {"id": "group_a", "tests": ["tests/test_hA.py::test_one", "tests/test_hA.py::test_two"]},
        {"id": "group_b", "tests": ["tests/test_hA.py::test_three"]},
    ]
    outcomes = {
        "tests/test_hA.py::test_one": "passed",
        "tests/test_hA.py::test_two": "failed",
        "tests/test_hA.py::test_three": "passed",
    }
    result = dev_check.score_correctness(outcomes, groups, slice_number=1)
    assert result["hidden_tests_passed"] == 2
    assert result["hidden_tests_total"] == 3
    assert result["by_obligation"]["group_a"] == {"passed": 1, "total": 2, "fraction": 0.5}
    assert result["by_obligation"]["group_b"] == {"passed": 1, "total": 1, "fraction": 1.0}


# --- cumulative upsert -----------------------------------------------------


class TestCumulativeUpsert:
    def _base_kwargs(self, attempt_entry: dict) -> dict:
        return dict(
            run_id="run-1",
            model="some/model",
            slice_number=1,
            run_status={"pm_status": "active", "slice_status": None, "stop_reason": None, "infrastructure_failure_suspected": False},
            attempt_entry=attempt_entry,
            accepted_at_attempt=None,
            pm_model_performance_ref=None,
        )

    def test_first_attempt_creates_a_new_sheet(self) -> None:
        sheet = dev_check.upsert_attempt(None, **self._base_kwargs({"attempt": 1, "commit_sha": "aaa"}))
        assert sheet["run_id"] == "run-1"
        assert [a["attempt"] for a in sheet["attempts"]] == [1]

    def test_second_attempt_preserves_the_first(self) -> None:
        sheet = dev_check.upsert_attempt(None, **self._base_kwargs({"attempt": 1, "commit_sha": "aaa"}))
        sheet = dev_check.upsert_attempt(sheet, **self._base_kwargs({"attempt": 2, "commit_sha": "bbb"}))
        assert [a["attempt"] for a in sheet["attempts"]] == [1, 2]
        assert sheet["attempts"][0]["commit_sha"] == "aaa"
        assert sheet["attempts"][1]["commit_sha"] == "bbb"

    def test_regrading_an_attempt_preserves_existing_drift_and_code_review(self) -> None:
        sheet = dev_check.upsert_attempt(None, **self._base_kwargs({"attempt": 1, "commit_sha": "aaa"}))
        sheet["attempts"][0]["drift_review"] = {"commissioned": True, "findings_by_severity": {"P1": 0}}
        sheet["attempts"][0]["code_review"] = {"commissioned": True, "findings_by_severity": {"P2": 1}}

        # Tool 1 re-grades attempt 1 (e.g. re-run for idempotency) without
        # touching review fields -- its upsert must not clobber them.
        sheet = dev_check.upsert_attempt(sheet, **self._base_kwargs({"attempt": 1, "commit_sha": "aaa-regraded"}))

        assert sheet["attempts"][0]["commit_sha"] == "aaa-regraded"
        assert sheet["attempts"][0]["drift_review"] == {"commissioned": True, "findings_by_severity": {"P1": 0}}
        assert sheet["attempts"][0]["code_review"] == {"commissioned": True, "findings_by_severity": {"P2": 1}}

    def test_mismatched_run_id_is_rejected(self) -> None:
        sheet = dev_check.upsert_attempt(None, **self._base_kwargs({"attempt": 1, "commit_sha": "aaa"}))
        kwargs = self._base_kwargs({"attempt": 2, "commit_sha": "bbb"})
        kwargs["run_id"] = "a-different-run"
        with pytest.raises(dev_check.DevCheckError, match="run_id"):
            dev_check.upsert_attempt(sheet, **kwargs)

    def test_write_sheet_atomically_round_trips(self, tmp_path: Path) -> None:
        out_path = tmp_path / "runs" / "r1" / "slice-1.json"
        sheet = dev_check.upsert_attempt(None, **self._base_kwargs({"attempt": 1, "commit_sha": "aaa"}))
        dev_check.write_sheet_atomically(out_path, sheet)
        assert out_path.is_file()
        reloaded = json.loads(out_path.read_text(encoding="utf-8"))
        assert reloaded["run_id"] == "run-1"
        assert list(reloaded.keys())[0] == "run_id"  # key order preserved


# --- resolve_before_head's structural fallbacks (2026-09-11) --------------


class TestResolveBeforeHead:
    """A slice's before_head is a permanent, structural fact (set once at
    start_slice, never touched by steer/relaunch -- verified directly
    against pm_lib source, docs/MODE2-REWRITE-PLAN.md §5's redesign note).
    These cover the four resolution paths in priority order, plus the
    explicit-override escape hatch and the fully-exhausted failure case.
    """

    def test_explicit_override_wins_over_everything_else(self) -> None:
        run_state = {"current_slice": {"id": "Slice 1", "before_head": "live-value"}}
        result = dev_check.resolve_before_head(run_state, "Slice 1", None, 0, {}, "explicit-value")
        assert result == "explicit-value"

    def test_live_current_slice_is_used_when_present(self) -> None:
        run_state = {"current_slice": {"id": "Slice 1", "before_head": "live-value"}}
        assert dev_check.resolve_before_head(run_state, "Slice 1", None, 0, {}) == "live-value"

    def test_live_current_slice_with_no_before_head_fails_loudly(self) -> None:
        run_state = {"current_slice": {"id": "Slice 1"}}
        with pytest.raises(dev_check.DevCheckError, match="before_head"):
            dev_check.resolve_before_head(run_state, "Slice 1", None, 0, {})

    def test_cached_sheet_row_is_used_when_slice_is_no_longer_current(self) -> None:
        run_state = {"current_slice": None, "slices": [{"id": "Slice 1"}]}
        existing_sheet = {"attempts": [{"attempt": 2, "provenance": {"base_commit": "cached-value"}}]}
        assert dev_check.resolve_before_head(run_state, "Slice 1", existing_sheet, 2, {}) == "cached-value"

    def test_previous_slices_recorded_commit_is_used_for_a_later_slice(self) -> None:
        # Mode B gates progression on acceptance, so Slice 2 existing at all
        # means Slice 1 is accepted and its commit is recorded structurally
        # -- no live pointer or cached row needed.
        run_state = {
            "current_slice": None,
            "slices": [{"id": "Slice 1", "commit": "slice1-end-commit"}, {"id": "Slice 2", "commit": None}],
        }
        result = dev_check.resolve_before_head(run_state, "Slice 2", None, 0, {"id": "Slice 2"})
        assert result == "slice1-end-commit"

    def test_a_reviews_recorded_before_head_is_used_for_the_first_slice(self) -> None:
        # The first slice has no "previous slice" to fall back on, but any
        # review ever commissioned for it recorded the same before_head
        # permanently in run.json -- this is what actually recovers a real
        # post-hoc grade of Slice 1's final attempt (verified against a real
        # completed run, 2026-09-11).
        run_state = {"current_slice": None, "slices": [{"id": "Slice 1", "commit": "slice1-end-commit"}]}
        entry = {"reviews": [{"skill": "drift-audit", "before_head": "plan-base-commit"}]}
        assert dev_check.resolve_before_head(run_state, "Slice 1", None, 3, entry) == "plan-base-commit"

    def test_first_slice_never_graded_and_never_reviewed_fails_loudly_naming_every_path(self) -> None:
        run_state = {"current_slice": None, "slices": [{"id": "Slice 1", "commit": "x"}]}
        with pytest.raises(dev_check.DevCheckError, match="pass --before-head explicitly"):
            dev_check.resolve_before_head(run_state, "Slice 1", None, 0, {"reviews": []})

    def test_the_most_recent_review_is_used_not_the_first_restart_epoch_regression(self) -> None:
        # Real defect found by independent review, 2026-09-11: before_head is
        # only constant WITHIN one uninterrupted in-flight epoch -- a
        # finalize --stop followed by a later start-slice on the same
        # still-unaccepted slice captures a brand-new before_head. Picking
        # the FIRST review found could return a stale, pre-restart value for
        # a post-restart attempt. The most recent review is correct: this
        # bench's plan mandates a fresh review before acceptance, so the
        # last-recorded review for an accepted slice always belongs to the
        # attempt that was actually accepted.
        run_state = {"current_slice": None, "slices": [{"id": "Slice 1", "commit": "slice1-end-commit"}]}
        entry = {
            "reviews": [
                {"skill": "drift-audit", "before_head": "PRE-restart-stale-value", "at": "t1"},
                {"skill": "drift-audit", "before_head": "POST-restart-correct-value", "at": "t9"},
            ]
        }
        assert dev_check.resolve_before_head(run_state, "Slice 1", None, 5, entry) == "POST-restart-correct-value"

    def test_a_stale_review_appended_after_the_accepted_epochs_review_is_not_picked(self) -> None:
        # Second independent review, 2026-09-11: reviews commission
        # concurrently and a slow, earlier-epoch review's report can be
        # parsed and appended to entry["reviews"] AFTER a faster,
        # current-epoch review's -- so "most recent by list position" alone
        # can still pick a stale before_head for an ACCEPTED slice. The
        # fix: for an accepted slice, filter to the review whose `head`
        # matches entry["commit"] (the exact accepted commit) before taking
        # the most recent such match.
        run_state = {"current_slice": None, "slices": [{"id": "Slice 1", "commit": "accepted-commit"}]}
        entry = {
            "status": "accepted",
            "commit": "accepted-commit",
            "reviews": [
                {"skill": "drift-audit", "head": "accepted-commit", "before_head": "CORRECT-value"},
                # Appended LAST (list position), but ran against an earlier,
                # superseded commit -- must not win just because it's last.
                {"skill": "code-review", "head": "some-earlier-superseded-commit", "before_head": "STALE-value"},
            ],
        }
        assert dev_check.resolve_before_head(run_state, "Slice 1", None, 5, entry) == "CORRECT-value"

    def test_previous_slice_attested_not_accepted_falls_through_to_reviews(self) -> None:
        # An `attested` predecessor (operator pre-approval; PM never
        # launches it, so it never records a commit) must not be mistaken
        # for a resolvable previous-slice commit -- fall through to this
        # slice's own reviews instead of returning None/crashing.
        run_state = {
            "current_slice": None,
            "slices": [{"id": "Slice 1", "status": "attested", "commit": None}, {"id": "Slice 2"}],
        }
        entry = {"reviews": [{"skill": "code-review", "before_head": "slice2-own-before-head"}]}
        assert dev_check.resolve_before_head(run_state, "Slice 2", None, 0, entry) == "slice2-own-before-head"


# --- grading worktree isolation --------------------------------------------


def test_grading_worktree_inside_the_developer_repo_is_rejected(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    commit = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    policy = {"grading_worktree_root": str(repo / "inside-worktrees")}
    with pytest.raises(dev_check.DevCheckError, match="inside the Developer's repo"):
        with dev_check.grading_worktree(repo, commit, policy):
            pass  # pragma: no cover -- must never be entered


def test_grading_worktree_outside_the_repo_is_created_and_cleaned_up(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    commit = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    grading_root = tmp_path / "grading"
    policy = {"grading_worktree_root": str(grading_root)}
    with dev_check.grading_worktree(repo, commit, policy) as worktree:
        assert worktree.is_dir()
        assert (worktree / "README.md").is_file()
    assert not worktree.exists()


def test_grading_worktree_removal_failure_is_warned_not_silently_swallowed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A `git worktree remove` failure must be surfaced (not raised, so it
    never masks a real grading error already propagating) -- but must never
    disappear silently either, or a stale worktree registration in the
    Developer's repo goes unnoticed."""
    repo = _make_repo(tmp_path)
    commit = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    policy = {"grading_worktree_root": str(tmp_path / "grading")}
    with dev_check.grading_worktree(repo, commit, policy) as worktree:
        # Deleting the repo's own .git out from under the worktree makes
        # `git worktree remove` fail once the context manager tries to clean up.
        shutil.rmtree(repo / ".git")
    captured = capsys.readouterr()
    assert "warning: failed to remove grading worktree" in captured.err
    assert str(worktree) in captured.err


# --- unavailable external quality tool ---------------------------------


def test_unavailable_lint_tool_is_recorded_as_unavailable_not_a_pass(tmp_path: Path) -> None:
    policy = {
        "python_interpreter": sys.executable,
        "lint_script": str(tmp_path / "does-not-exist.py"),
        "subprocess_timeout_seconds": 30,
    }
    result = dev_check.run_lint(tmp_path, "deadbeef", policy)
    assert result["available"] is False
    assert "error" in result
    assert "counts" not in result


def test_lint_tool_error_exit_is_recorded_as_unavailable_not_a_pass(tmp_path: Path) -> None:
    # Exit 2 is lint.py's own EXIT_ERROR -- a genuine tool failure, unlike
    # exit 1 (new findings) or exit 3 (coverage gap), both real answers.
    failing_script = tmp_path / "failing_lint.py"
    failing_script.write_text("import sys\nsys.exit(2)\n", encoding="utf-8")
    policy = {
        "python_interpreter": sys.executable,
        "lint_script": str(failing_script),
        "subprocess_timeout_seconds": 30,
    }
    result = dev_check.run_lint(tmp_path, "deadbeef", policy)
    assert result["available"] is False
    assert "error" in result


def test_lint_exit_1_with_new_findings_is_recorded_as_findings_not_unavailable(tmp_path: Path) -> None:
    """finding 1: lint.py exits 1 specifically when --base mode finds new
    findings -- that must be recorded as findings, never as "unavailable"."""
    fake_lint = tmp_path / "fake_lint.py"
    fake_lint.write_text(
        "import json, sys\n"
        "payload = {\n"
        "    'verdict': 'findings',\n"
        "    'uncovered': [],\n"
        "    'missing_binaries': [],\n"
        # 'tools[].findings' deliberately carries the ABSOLUTE head count (3)
        # while 'new_findings' carries only the DIFFERENTIAL ones (1) -- this
        # is exactly the shape that would fool an implementation counting
        # from the wrong field.
        "    'tools': [{'name': 'ruff', 'findings': 3}],\n"
        "    'new_findings': [{'tool': 'ruff', 'rule': 'F401', 'path': 'a.py', 'line': 1, 'message': 'unused import'}],\n"
        "}\n"
        "print(json.dumps(payload))\n"
        "sys.exit(1)\n",
        encoding="utf-8",
    )
    policy = {
        "python_interpreter": sys.executable,
        "lint_script": str(fake_lint),
        "subprocess_timeout_seconds": 30,
    }
    result = dev_check.run_lint(tmp_path, "deadbeef", policy)
    assert result["available"] is True
    assert result["verdict"] == "findings"
    # Differential (1), never the absolute head count (3).
    assert result["counts"] == {"ruff": 1}


def test_lint_exit_3_coverage_gap_is_visible_not_a_clean_pass(tmp_path: Path) -> None:
    fake_lint = tmp_path / "fake_lint.py"
    fake_lint.write_text(
        "import json, sys\n"
        "payload = {\n"
        "    'verdict': 'coverage-gap',\n"
        "    'uncovered': ['some/path.py'],\n"
        "    'missing_binaries': ['ruff'],\n"
        "    'tools': [],\n"
        "    'new_findings': [],\n"
        "}\n"
        "print(json.dumps(payload))\n"
        "sys.exit(3)\n",
        encoding="utf-8",
    )
    policy = {
        "python_interpreter": sys.executable,
        "lint_script": str(fake_lint),
        "subprocess_timeout_seconds": 30,
    }
    result = dev_check.run_lint(tmp_path, "deadbeef", policy)
    assert result["available"] is True
    assert result["verdict"] == "coverage-gap"
    assert result["uncovered"] == ["some/path.py"]
    assert result["missing_binaries"] == ["ruff"]


def test_unavailable_health_tool_is_recorded_as_unavailable_not_a_pass(tmp_path: Path) -> None:
    policy = {
        "python_interpreter": sys.executable,
        "health_script": str(tmp_path / "does-not-exist.py"),
        "subprocess_timeout_seconds": 30,
    }
    result = dev_check.run_code_health(tmp_path, "deadbeef", policy)
    assert result["available"] is False
    assert "error" in result
    assert "counts" not in result


def test_code_health_exit_3_coverage_gap_is_available_not_unavailable(tmp_path: Path) -> None:
    fake_health = tmp_path / "fake_health.py"
    fake_health.write_text(
        "import json, sys\nprint(json.dumps({'candidates': []}))\nsys.exit(3)\n",
        encoding="utf-8",
    )
    policy = {
        "python_interpreter": sys.executable,
        "health_script": str(fake_health),
        "subprocess_timeout_seconds": 30,
    }
    result = dev_check.run_code_health(tmp_path, "deadbeef", policy)
    assert result["available"] is True
    assert result["verdict"] == "coverage-gap"


# --- finding 7: --require-coverage is actually passed, making the exit-3 ---
# --- coverage-gap path real rather than dead -------------------------------


def test_run_lint_passes_require_coverage_flag(tmp_path: Path) -> None:
    fake_lint = tmp_path / "fake_lint.py"
    fake_lint.write_text(
        "import json, sys\n"
        "print(json.dumps({'verdict': 'pass', 'uncovered': [], 'missing_binaries': [], "
        "'tools': [], 'new_findings': [], 'argv': sys.argv[1:]}))\n",
        encoding="utf-8",
    )
    policy = {
        "python_interpreter": sys.executable,
        "lint_script": str(fake_lint),
        "subprocess_timeout_seconds": 30,
    }
    result = dev_check.run_lint(tmp_path, "deadbeef", policy)
    assert result["available"] is True
    assert "--require-coverage" in result["raw"]["argv"]


def test_run_code_health_passes_require_coverage_flag(tmp_path: Path) -> None:
    fake_health = tmp_path / "fake_health.py"
    fake_health.write_text(
        "import json, sys\nprint(json.dumps({'candidates': [], 'argv': sys.argv[1:]}))\n",
        encoding="utf-8",
    )
    policy = {
        "python_interpreter": sys.executable,
        "health_script": str(fake_health),
        "subprocess_timeout_seconds": 30,
    }
    result = dev_check.run_code_health(tmp_path, "deadbeef", policy)
    assert result["available"] is True
    assert "--require-coverage" in result["raw"]["argv"]


# --- sheet identity guard (finding 5) --------------------------------------


def test_load_existing_sheet_rejects_a_foreign_run_or_slice(tmp_path: Path) -> None:
    out_path = tmp_path / "sheet.json"
    out_path.write_text(json.dumps({"run_id": "other-run", "slice": 1, "attempts": []}), encoding="utf-8")
    with pytest.raises(dev_check.DevCheckError, match="run_id"):
        dev_check.load_existing_sheet(out_path, "this-run", 1)


def test_load_existing_sheet_accepts_a_matching_sheet(tmp_path: Path) -> None:
    out_path = tmp_path / "sheet.json"
    out_path.write_text(json.dumps({"run_id": "this-run", "slice": 1, "attempts": []}), encoding="utf-8")
    sheet = dev_check.load_existing_sheet(out_path, "this-run", 1)
    assert sheet["run_id"] == "this-run"


# --- policy loading ------------------------------------------------------


class TestLoadPolicy:
    def test_missing_backend_key_or_non_local_backend_fails_loudly(self, tmp_path: Path) -> None:
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text(
            "backend: sbx\npm_scripts_dir: /x\nlint_script: /x\nhealth_script: /x\npython_interpreter: python3\n",
            encoding="utf-8",
        )
        with pytest.raises(dev_check.DevCheckError, match="not implemented"):
            dev_check.load_policy(policy_path)

    def test_missing_required_key_fails_loudly(self, tmp_path: Path) -> None:
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text("backend: local\n", encoding="utf-8")
        with pytest.raises(dev_check.DevCheckError, match="missing required keys"):
            dev_check.load_policy(policy_path)

    def test_the_repos_real_policy_yaml_loads(self) -> None:
        policy = dev_check.load_policy(REPO_ROOT / "policy.yaml")
        assert policy["backend"] == "local"

    def test_missing_subprocess_timeout_seconds_fails_loudly(self, tmp_path: Path) -> None:
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text(
            "backend: local\npm_scripts_dir: /x\nlint_script: /x\nhealth_script: /x\npython_interpreter: python3\n",
            encoding="utf-8",
        )
        with pytest.raises(dev_check.DevCheckError, match="subprocess_timeout_seconds"):
            dev_check.load_policy(policy_path)

    def test_non_positive_subprocess_timeout_seconds_fails_loudly(self, tmp_path: Path) -> None:
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text(
            "backend: local\npm_scripts_dir: /x\nlint_script: /x\nhealth_script: /x\n"
            "python_interpreter: python3\nsubprocess_timeout_seconds: 0\n",
            encoding="utf-8",
        )
        with pytest.raises(dev_check.DevCheckError, match="subprocess_timeout_seconds"):
            dev_check.load_policy(policy_path)


# --- per-attempt PM decision --------------------------------------------


class TestResolvePmDecision:
    """`run.json` holds one decision per slice; the trajectory this bench
    measures needs one per attempt, so it comes from the event log instead."""

    EVENTS = [
        {"kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
        {"kind": "floor", "slice": "Slice 1", "note": "6/7"},
        {"kind": "steer", "slice": "Slice 1", "note": "fix the sigma term"},
        {"kind": "floor", "slice": "Slice 1", "note": "7/7"},
        {"kind": "review", "slice": "Slice 1", "note": "code-review via codex"},
        {"kind": "accept", "slice": "Slice 1", "note": "accepted"},
    ]

    def test_each_attempt_gets_its_own_decision(self) -> None:
        assert dev_check.resolve_pm_decision(self.EVENTS, "Slice 1", 0) == "steer"
        assert dev_check.resolve_pm_decision(self.EVENTS, "Slice 1", 1) == "accept"

    def test_an_undecided_attempt_is_none_not_a_guess(self) -> None:
        events = self.EVENTS[:2]
        assert dev_check.resolve_pm_decision(events, "Slice 1", 0) is None

    def test_an_attempt_that_has_not_opened_yet_is_none(self) -> None:
        assert dev_check.resolve_pm_decision(self.EVENTS, "Slice 1", 5) is None

    def test_another_slices_events_do_not_decide_this_slices_attempt(self) -> None:
        events = [
            {"kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
            {"kind": "accept", "slice": "Slice 2", "note": "accepted"},
        ]
        assert dev_check.resolve_pm_decision(events, "Slice 1", 0) is None

    def test_a_top_level_stop_ends_the_attempt_despite_carrying_no_slice(self) -> None:
        events = [
            {"kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
            {"kind": "stop", "slice": None, "note": "operator stopped the run"},
        ]
        assert dev_check.resolve_pm_decision(events, "Slice 1", 0) == "stop"


class TestResolvePmAttemptsCounter:
    """PM's own per-slice `attempts` counter resets to 0 on a fresh `launch`
    and increments by 1 on every `relaunch`/`steer` in between
    (`pm_lib.slice_ops.start_slice`/`steer`) -- exactly the same rule
    `bench_lib.epoch_start_ordinals` applies to the event log, so this must
    give the historically correct value for ANY attempt, not just the
    latest/live one (G16, docs/MODE2-REWRITE-PLAN.md §8)."""

    def test_each_attempt_in_one_epoch_gets_its_own_counter(self) -> None:
        events = [
            {"kind": "launch", "slice": "Slice 1"},
            {"kind": "steer", "slice": "Slice 1"},
            {"kind": "steer", "slice": "Slice 1"},
        ]
        assert dev_check.resolve_pm_attempts_counter(events, "Slice 1", 0) == 0
        assert dev_check.resolve_pm_attempts_counter(events, "Slice 1", 1) == 1
        assert dev_check.resolve_pm_attempts_counter(events, "Slice 1", 2) == 2

    def test_counter_resets_at_a_restart_launch_not_at_relaunch(self) -> None:
        events = [
            {"kind": "launch", "slice": "Slice 1"},
            {"kind": "relaunch", "slice": "Slice 1"},
            {"kind": "launch", "slice": "Slice 1"},  # a genuine restart epoch
            {"kind": "steer", "slice": "Slice 1"},
        ]
        assert dev_check.resolve_pm_attempts_counter(events, "Slice 1", 1) == 1
        assert dev_check.resolve_pm_attempts_counter(events, "Slice 1", 2) == 0
        assert dev_check.resolve_pm_attempts_counter(events, "Slice 1", 3) == 1

    def test_an_attempt_with_no_matching_event_is_a_named_problem(self) -> None:
        events = [{"kind": "launch", "slice": "Slice 1"}]
        with pytest.raises(dev_check.DevCheckError, match="Slice 1.*attempt 5"):
            dev_check.resolve_pm_attempts_counter(events, "Slice 1", 5)


class TestReadEvents:
    def test_a_missing_log_is_empty_not_an_error(self, tmp_path: Path) -> None:
        assert dev_check.read_events(tmp_path) == []

    def test_a_corrupt_line_fails_loudly_naming_the_line(self, tmp_path: Path) -> None:
        (tmp_path / "events.jsonl").write_text('{"kind": "launch"}\nnot json\n', encoding="utf-8")
        with pytest.raises(dev_check.DevCheckError, match="events.jsonl:2"):
            dev_check.read_events(tmp_path)


# --- synthetic-fixture tests over main() (A1, A2, A5) -----------------------
#
# main() is otherwise untouched by any test in this module. pm_lib and the
# external quality/pytest subprocesses are stubbed; the git repo and the
# grading worktree are real (grading_worktree/run_git are exercised for real).


class TestMainSyntheticRun:
    def _make_run_dir(self, tmp_path: Path, repo: Path, head: str, *, current_slice: bool = True) -> Path:
        run_dir = tmp_path / "pm-run"
        run_dir.mkdir()
        plan_path = tmp_path / "plan.md"
        plan_path.write_text("plan\n", encoding="utf-8")
        run_state: dict = {
            "run_id": "run-a1",
            "repo": str(repo),
            "status": "active",
            "stop_reason": None,
            "plan": {"path": str(plan_path), "sha256": "planhash"},
            "harness": {"model": "test/model"},
            "slices": [{"id": "Slice 1", "status": None, "attempts": 0}],
        }
        if current_slice:
            run_state["current_slice"] = {"id": "Slice 1", "attempts": 0, "before_head": head}
        (run_dir / "run.json").write_text(json.dumps(run_state), encoding="utf-8")
        # resolve_attempt() (finding 2) derives the attempt key from
        # events.jsonl, not from run.json's counter -- every synthetic run
        # needs at least the opening launch event for Slice 1.
        (run_dir / "events.jsonl").write_text(
            json.dumps({"kind": "launch", "slice": "Slice 1", "note": "attempt 0"}) + "\n", encoding="utf-8"
        )
        return run_dir

    def _stub_everything(self, monkeypatch: pytest.MonkeyPatch, call_order: list) -> None:
        fake_pm_plan = type(
            "FakePmPlan",
            (),
            {
                "parse_plan": staticmethod(lambda path: "SLICES"),
                "plan_slice_by_id": staticmethod(lambda slices, sid: "SLICE"),
                "effective_authorized_files": staticmethod(lambda plan_slice, state: []),
            },
        )()
        fake_pm_git_ops = type(
            "FakePmGitOps",
            (),
            {
                "changed_files_between": staticmethod(lambda repo, before, after, status: []),
                "unauthorized_files": staticmethod(lambda changed, authorized: []),
            },
        )()
        monkeypatch.setattr(dev_check, "import_pm_lib", lambda policy: (fake_pm_plan, fake_pm_git_ops))
        monkeypatch.setattr(
            dev_check,
            "load_obligations",
            lambda root: {"slices": {1: {"obligations": [{"id": "g1", "tests": ["tests/test_hA.py::test_one"]}]}}},
        )

        # The invariant these stubs enforce is the one that matters, not the
        # call sequence: a hidden test file must not exist in the worktree
        # while either quality tool measures it. Asserting the property
        # rather than the order means hoisting the copy out of
        # run_hidden_tests into main() still trips the test.
        def _assert_worktree_is_pristine(worktree: Path, tool: str) -> None:
            copied = Path(worktree) / "tests" / "test_hA.py"
            assert not copied.exists(), f"{tool} ran with a hidden test already copied into {copied}"

        def fake_run_lint(worktree, before_head, policy):
            _assert_worktree_is_pristine(worktree, "lint")
            call_order.append("lint")
            return {"available": True, "dimension": "tool", "counts": {}}

        def fake_run_code_health(worktree, before_head, policy):
            _assert_worktree_is_pristine(worktree, "code-health")
            call_order.append("health")
            return {"available": True, "dimension": "kind", "counts": {}}

        def fake_run_hidden_tests(worktree, slice_number, root, policy):
            # Copy something in for real, so the pristine-worktree assertion
            # above has something to detect if the ordering ever regresses.
            target = Path(worktree) / "tests"
            target.mkdir(parents=True, exist_ok=True)
            (target / "test_hA.py").write_text("def test_one():\n    pass\n", encoding="utf-8")
            call_order.append("hidden_tests")
            return {"tests/test_hA.py::test_one": "passed"}

        monkeypatch.setattr(dev_check, "run_lint", fake_run_lint)
        monkeypatch.setattr(dev_check, "run_code_health", fake_run_code_health)
        monkeypatch.setattr(dev_check, "run_hidden_tests", fake_run_hidden_tests)

    def _policy_path(self, tmp_path: Path) -> Path:
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text(
            "backend: local\npm_scripts_dir: /x\nlint_script: /x\nhealth_script: /x\n"
            "python_interpreter: python3\ngrading_worktree_root: null\nsubprocess_timeout_seconds: 600\n",
            encoding="utf-8",
        )
        return policy_path

    def _head(self, repo: Path) -> str:
        return subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip()

    def test_a2_quality_runs_before_hidden_tests_are_copied_in(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = _make_repo(tmp_path)
        head = self._head(repo)
        run_dir = self._make_run_dir(tmp_path, repo, head)
        call_order: list = []
        self._stub_everything(monkeypatch, call_order)

        rc = dev_check.main(
            [
                "--run-dir", str(run_dir), "--slice", "1",
                "--policy", str(self._policy_path(tmp_path)),
                "--out", str(tmp_path / "sheet.json"),
            ]
        )
        assert rc == 0
        # Lint/code-health must measure the pristine worktree, before
        # run_hidden_tests copies this slice's held-out tests into tests/ --
        # otherwise both quality tools' --base differential mode (which
        # includes untracked files) attributes the bench's own hidden tests
        # to the Developer.
        # Both quality tools before the copy; their order relative to each
        # other is not part of the contract and is deliberately not pinned.
        assert set(call_order[:2]) == {"lint", "health"}
        assert call_order[2] == "hidden_tests"

    def test_a1_accepted_slice_can_still_be_graded_via_sheet_fallback(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo = _make_repo(tmp_path)
        head = self._head(repo)
        run_dir = self._make_run_dir(tmp_path, repo, head)
        call_order: list = []
        self._stub_everything(monkeypatch, call_order)
        out_path = tmp_path / "sheet.json"
        policy_path = self._policy_path(tmp_path)
        argv = ["--run-dir", str(run_dir), "--slice", "1", "--policy", str(policy_path), "--out", str(out_path)]

        # First grade while the slice is still current -- writes provenance.base_commit.
        assert dev_check.main(argv) == 0

        # Simulate PM's real accept-path write (pm_lib.slice_ops.finalize_accept):
        # entry["status"]="accepted" and state["current_slice"]=None in the
        # same state write.
        run_state = json.loads((run_dir / "run.json").read_text())
        run_state["slices"][0]["status"] = "accepted"
        run_state["current_slice"] = None
        (run_dir / "run.json").write_text(json.dumps(run_state), encoding="utf-8")

        # Before the A1 fix this raised DevCheckError: current_slice no
        # longer names Slice 1, so before_head could never be resolved and
        # the accepted attempt could never be graded.
        assert dev_check.main(["--attempt", "0", *argv]) == 0

        sheet = json.loads(out_path.read_text())
        assert sheet["accepted_at_attempt"] == 0
        assert sheet["attempts"][0]["provenance"]["base_commit"] == head

    def test_a1_neither_current_slice_nor_existing_sheet_fails_loudly(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo = _make_repo(tmp_path)
        head = self._head(repo)
        run_dir = self._make_run_dir(tmp_path, repo, head, current_slice=False)
        call_order: list = []
        self._stub_everything(monkeypatch, call_order)
        policy_path = self._policy_path(tmp_path)

        with pytest.raises(dev_check.DevCheckError, match="before_head could not be resolved"):
            dev_check.main(
                [
                    "--run-dir", str(run_dir), "--slice", "1", "--attempt", "0",
                    "--policy", str(policy_path), "--out", str(tmp_path / "sheet.json"),
                ]
            )

    def test_a5_infrastructure_failure_suspected_survives_a_regrade(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo = _make_repo(tmp_path)
        head = self._head(repo)
        run_dir = self._make_run_dir(tmp_path, repo, head)
        call_order: list = []
        self._stub_everything(monkeypatch, call_order)
        out_path = tmp_path / "sheet.json"
        argv = [
            "--run-dir", str(run_dir), "--slice", "1",
            "--policy", str(self._policy_path(tmp_path)), "--out", str(out_path),
        ]

        assert dev_check.main(argv) == 0
        sheet = json.loads(out_path.read_text())
        assert sheet["run_status"]["infrastructure_failure_suspected"] is False

        # The driver computes and sets this heuristic itself (§7); simulate
        # that having happened between grades.
        sheet["run_status"]["infrastructure_failure_suspected"] = True
        out_path.write_text(json.dumps(sheet), encoding="utf-8")

        assert dev_check.main(argv) == 0
        sheet_after = json.loads(out_path.read_text())
        assert sheet_after["run_status"]["infrastructure_failure_suspected"] is True

    def test_finding2_pm_attempts_counter_survives_a_regrade(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A regrade of a historical attempt must not overwrite its recorded
        pm_attempts_counter with whatever PM's own counter currently reads.

        `resolve_pm_attempts_counter` only ever sees *current* run.json
        state, so calling it again after a later steer (or a stop/restart,
        which resets the counter to 0 -- finding 2's original failure mode)
        would silently misrecord attempt 0's counter, defeating the field's
        only purpose: locating PM's historical attempt-<n>/ artifacts.
        """
        repo = _make_repo(tmp_path)
        head = self._head(repo)
        run_dir = self._make_run_dir(tmp_path, repo, head)
        call_order: list = []
        self._stub_everything(monkeypatch, call_order)
        out_path = tmp_path / "sheet.json"
        argv = [
            "--run-dir", str(run_dir), "--slice", "1", "--attempt", "0",
            "--policy", str(self._policy_path(tmp_path)), "--out", str(out_path),
        ]

        assert dev_check.main(argv) == 0
        sheet = json.loads(out_path.read_text())
        original_counter = sheet["attempts"][0]["pm_attempts_counter"]
        assert original_counter == 0

        # Simulate PM's own counter having moved on since -- e.g. a later
        # steer incremented it, or a stop/restart reset it -- without
        # touching the event log (attempt 0 is still being explicitly
        # re-graded via --attempt 0).
        run_state = json.loads((run_dir / "run.json").read_text())
        run_state["current_slice"]["attempts"] = 7
        (run_dir / "run.json").write_text(json.dumps(run_state), encoding="utf-8")

        assert dev_check.main(argv) == 0
        sheet_after = json.loads(out_path.read_text())
        assert sheet_after["attempts"][0]["pm_attempts_counter"] == original_counter

    def test_finding4_provenance_survives_a_regrade_after_policy_and_obligations_change(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Grade an attempt, change policy.yaml's and obligations.yaml's
        bytes, regrade the same attempt, and assert the original provenance
        block -- including policy_hash and obligations_hash -- survives
        byte-for-byte. The existing accepted-slice test only checks
        base_commit; this is the discriminating test for the rest of the
        provenance block (finding 4)."""
        repo = _make_repo(tmp_path)
        head = self._head(repo)
        run_dir = self._make_run_dir(tmp_path, repo, head)
        call_order: list = []
        self._stub_everything(monkeypatch, call_order)

        # build_provenance hashes root/OBLIGATIONS_RELATIVE_PATH via
        # bench_root(), not the load_obligations() stub -- point bench_root
        # at a throwaway directory this test controls so the obligations
        # file's bytes can be changed between grades.
        fake_bench_root = tmp_path / "fake-bench-root"
        obligations_path = fake_bench_root / dev_check.OBLIGATIONS_RELATIVE_PATH
        obligations_path.parent.mkdir(parents=True, exist_ok=True)
        obligations_path.write_text("slices: {}\n", encoding="utf-8")
        monkeypatch.setattr(dev_check, "bench_root", lambda: fake_bench_root)

        out_path = tmp_path / "sheet.json"
        policy_path = self._policy_path(tmp_path)
        argv = [
            "--run-dir", str(run_dir), "--slice", "1", "--attempt", "0",
            "--policy", str(policy_path), "--out", str(out_path),
        ]

        assert dev_check.main(argv) == 0
        sheet = json.loads(out_path.read_text())
        original_provenance = sheet["attempts"][0]["provenance"]
        assert original_provenance["base_commit"] == head

        # Change both files' bytes between grades.
        policy_path.write_text(policy_path.read_text() + "# changed\n", encoding="utf-8")
        obligations_path.write_text("slices: {}\n# changed\n", encoding="utf-8")

        assert dev_check.main(argv) == 0
        sheet_after = json.loads(out_path.read_text())
        assert sheet_after["attempts"][0]["provenance"] == original_provenance
