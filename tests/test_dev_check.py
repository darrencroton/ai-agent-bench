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
    def test_every_group_node_exists_in_its_source_file(self) -> None:
        obligations = dev_check.load_obligations(REPO_ROOT)
        for slice_number, slice_map in obligations["slices"].items():
            source_dir = REPO_ROOT / slice_map["source_dir"]
            real_by_file = {
                filename: _collect_test_function_names(source_dir / filename)
                for filename in dev_check.HIDDEN_TEST_FILENAMES
            }
            for group in slice_map["obligations"]:
                for node in group["tests"]:
                    file_part, _, func_name = node.partition("::")
                    filename = file_part.split("/")[-1]
                    assert filename in real_by_file, f"slice {slice_number} obligation {group['id']!r}: unknown file {file_part!r}"
                    assert func_name in real_by_file[filename], (
                        f"slice {slice_number} obligation {group['id']!r}: {node!r} names a function "
                        f"that does not exist in {source_dir / filename}"
                    )

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

    def test_no_node_is_claimed_by_two_groups(self) -> None:
        obligations = dev_check.load_obligations(REPO_ROOT)
        for slice_map in obligations["slices"].values():
            # Raises DevCheckError internally if any duplicate is found.
            dev_check.node_to_group_map(slice_map["obligations"])


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
            provenance={"plan_hash": "abc", "policy_hash": "def", "base_commit": "deadbeef", "pm_skill_version": None},
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


def test_nonzero_exit_lint_tool_is_recorded_as_unavailable_not_a_pass(tmp_path: Path) -> None:
    failing_script = tmp_path / "failing_lint.py"
    failing_script.write_text("import sys\nsys.exit(1)\n", encoding="utf-8")
    policy = {
        "python_interpreter": sys.executable,
        "lint_script": str(failing_script),
        "subprocess_timeout_seconds": 30,
    }
    result = dev_check.run_lint(tmp_path, "deadbeef", policy)
    assert result["available"] is False
    assert "error" in result


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
            "python_interpreter: python3\ngrading_worktree_root: null\n",
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
        assert sheet["provenance"]["base_commit"] == head

    def test_a1_neither_current_slice_nor_existing_sheet_fails_loudly(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo = _make_repo(tmp_path)
        head = self._head(repo)
        run_dir = self._make_run_dir(tmp_path, repo, head, current_slice=False)
        call_order: list = []
        self._stub_everything(monkeypatch, call_order)
        policy_path = self._policy_path(tmp_path)

        with pytest.raises(dev_check.DevCheckError, match="before_head cannot be resolved"):
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

        # The driver computes and sets this heuristic itself (§6); simulate
        # that having happened between grades.
        sheet["run_status"]["infrastructure_failure_suspected"] = True
        out_path.write_text(json.dumps(sheet), encoding="utf-8")

        assert dev_check.main(argv) == 0
        sheet_after = json.loads(out_path.read_text())
        assert sheet_after["run_status"]["infrastructure_failure_suspected"] is True
