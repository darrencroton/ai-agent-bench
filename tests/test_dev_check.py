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
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import dev_check  # noqa: E402


@pytest.fixture(autouse=True)
def _clear_baseline_complexity_cache() -> None:
    """dev_check._BASELINE_COMPLEXITY_CACHE is deliberately module-level/
    process-local (see its own docstring) -- clear it around every test in
    this file so one test's cached baseline can never leak into another's,
    regardless of test order."""
    dev_check._BASELINE_COMPLEXITY_CACHE.clear()
    yield
    dev_check._BASELINE_COMPLEXITY_CACHE.clear()


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


def _head(repo: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()


def _commit_all(repo: Path, message: str) -> str:
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=repo, check=True)
    return _head(repo)


_MEASUREMENT_POLICY = {
    "production_paths": ["src/**/*.py"],
    "test_paths": ["tests/**/*.py"],
    "doc_paths": ["docs/**/*.md", "*.md"],
    "loc_definition": "net_physical_lines",
    "loc_category_definition": "ast_tokenize_line_classification",
    "metric_version": 2,
}


# --- obligations.yaml validated against the real hidden test files --------


class TestObligationMapAgainstRealFiles:
    # This is the one integration check kept here. It already
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
            # The file set comes from DERIVATION off this slice's own
            # obligation groups, never a hardcoded constant -- the same
            # derivation main() uses to copy and target pytest.
            filenames = dev_check.hidden_test_filenames(slice_map["obligations"], REPO_ROOT / dev_check.OBLIGATIONS_RELATIVE_PATH)
            expected_nodes = {
                f"tests/{filename}::{name}"
                for filename in filenames
                for name in _collect_test_function_names(source_dir / filename)
            }
            mapped_nodes = dev_check.node_to_group_map(slice_map["obligations"])
            assert set(mapped_nodes) == expected_nodes, (
                f"slice {slice_number}: obligations.yaml's node set does not exactly match the real test files "
                f"(missing from map: {sorted(expected_nodes - set(mapped_nodes))}, "
                f"in map but not a real test: {sorted(set(mapped_nodes) - expected_nodes)})"
            )

    def test_derived_filename_set_for_relative_velocity_is_exactly_the_two_h_files(self) -> None:
        """For both slices of the existing task, derivation yields exactly
        {"test_hA.py", "test_hB.py"} -- by derivation from the checked-in
        obligations file, not by any remaining hardcoded fallback."""
        obligations = dev_check.load_obligations(REPO_ROOT)
        for slice_number in sorted(obligations["slices"]):
            derived = dev_check.hidden_test_filenames(
                obligations["slices"][slice_number]["obligations"], REPO_ROOT / dev_check.OBLIGATIONS_RELATIVE_PATH
            )
            assert derived == {"test_hA.py", "test_hB.py"}, f"slice {slice_number}: {derived!r}"


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


# --- hidden-test filename derivation ---------------------------------------


class TestHiddenTestFilenames:
    """The slice's hidden test files are DERIVED from its obligation groups'
    node ids (the obligations file uniquely holds that fact), replacing the
    old hardcoded two-file constant -- so a task whose slice references other
    or more files is graded against precisely its own suite. Every structural
    assumption (group is a mapping, tests is a list, each node is a shaped
    string) is validated into a named DevCheckError naming the obligations
    file, never a raw TypeError/AttributeError."""

    _OB_PATH = Path("hidden_tests/obligations.yaml")

    def test_distinct_filenames_are_derived_from_node_ids(self) -> None:
        groups = [
            {"id": "g1", "tests": ["tests/test_hA.py::test_one", "tests/test_hB.py::test_two"]},
            {"id": "g2", "tests": ["tests/test_hA.py::test_three"]},
        ]
        assert dev_check.hidden_test_filenames(groups, self._OB_PATH) == {"test_hA.py", "test_hB.py"}

    def test_more_than_two_referenced_files_are_all_derived(self) -> None:
        groups = [
            {"id": "g1", "tests": ["tests/test_zz.py::test_one", "tests/test_qq.py::test_two"]},
            {"id": "g2", "tests": ["tests/test_ww.py::test_three", "tests/test_zz.py::test_four"]},
        ]
        assert dev_check.hidden_test_filenames(groups, self._OB_PATH) == {"test_zz.py", "test_qq.py", "test_ww.py"}

    def test_parametrize_suffix_does_not_corrupt_the_derived_filename(self) -> None:
        # obligations.yaml documents that @pytest.mark.parametrize would yield
        # node ids like "test_foo[param]"; the suffix sits after "::", so the
        # filename part must derive identically with or without it.
        groups = [{"id": "g1", "tests": ["tests/test_p.py::test_foo[param]", "tests/test_p.py::test_bar"]}]
        assert dev_check.hidden_test_filenames(groups, self._OB_PATH) == {"test_p.py"}

    def test_parametrize_value_containing_a_space_is_still_accepted(self) -> None:
        # The derivation validates shape (tests/ prefix + first :: split), not
        # an exact \S+ tail -- a legal parametrize id with spaces inside the
        # brackets must not be spuriously rejected.
        groups = [{"id": "g1", "tests": ["tests/test_p.py::test_foo[a b c]"]}]
        assert dev_check.hidden_test_filenames(groups, self._OB_PATH) == {"test_p.py"}

    def test_class_method_node_id_derives_the_same_filename(self) -> None:
        # Class-based tests carry a second '::'; only the FIRST one separates
        # the file from the test name.
        groups = [{"id": "g1", "tests": ["tests/test_c.py::TestClass::test_method"]}]
        assert dev_check.hidden_test_filenames(groups, self._OB_PATH) == {"test_c.py"}

    def test_malformed_node_id_fails_loudly_naming_file_group_and_node(self) -> None:
        for bad in ("src/test_x.py::test_one", "tests/test_x.py", "tests/sub/test_x.py::test_one", "test_x.py::t"):
            groups = [{"id": "bad_group", "tests": [bad]}]
            with pytest.raises(dev_check.DevCheckError) as excinfo:
                dev_check.hidden_test_filenames(groups, self._OB_PATH)
            message = str(excinfo.value)
            assert str(self._OB_PATH) in message
            assert "bad_group" in message
            assert bad in message

    def test_non_mapping_group_fails_loudly_naming_file_and_position(self) -> None:
        for bad_group in ("just-a-string", 42, None):
            with pytest.raises(dev_check.DevCheckError) as excinfo:
                dev_check.hidden_test_filenames([{"id": "ok", "tests": ["tests/t.py::x"]}, bad_group], self._OB_PATH)
            message = str(excinfo.value)
            assert str(self._OB_PATH) in message
            assert "#1" in message

    def test_non_list_tests_field_fails_loudly_naming_file_and_group(self) -> None:
        for bad_tests in ("not-a-list", 7, None):
            with pytest.raises(dev_check.DevCheckError) as excinfo:
                dev_check.hidden_test_filenames([{"id": "g_bad", "tests": bad_tests}], self._OB_PATH)
            message = str(excinfo.value)
            assert str(self._OB_PATH) in message
            assert "g_bad" in message

    def test_non_string_node_fails_loudly_naming_file_group_and_value(self) -> None:
        for bad_node in (42, None):
            with pytest.raises(dev_check.DevCheckError) as excinfo:
                dev_check.hidden_test_filenames([{"id": "g_int", "tests": [bad_node]}], self._OB_PATH)
            message = str(excinfo.value)
            assert str(self._OB_PATH) in message
            assert "g_int" in message
            assert repr(bad_node) in message

    def test_group_without_a_usable_id_fails_loudly_naming_file_and_index(self) -> None:
        # A missing/malformed id used to slip through derivation and crash
        # later with a raw KeyError at node_to_group_map/score_correctness.
        for bad_groups in (
            [{"tests": ["tests/t.py::x"]}],
            [{"id": 7, "tests": ["tests/t.py::x"]}],
            [{"id": "", "tests": ["tests/t.py::x"]}],
        ):
            with pytest.raises(dev_check.DevCheckError) as excinfo:
                dev_check.hidden_test_filenames(bad_groups, self._OB_PATH)
            message = str(excinfo.value)
            assert str(self._OB_PATH) in message
            assert "#0" in message

    def test_groups_referencing_no_file_at_all_fail_loudly(self) -> None:
        with pytest.raises(dev_check.DevCheckError, match="no obligation group references any hidden test file"):
            dev_check.hidden_test_filenames([], self._OB_PATH)
        with pytest.raises(dev_check.DevCheckError, match="no obligation group references any hidden test file"):
            dev_check.hidden_test_filenames([{"id": "empty", "tests": []}], self._OB_PATH)


class TestObligationGroupsForSliceShape:
    """obligation_groups_for_slice guards the two structural escapes load_
    obligations' top-level check does not cover: a non-mapping slice entry and
    a non-list `obligations` value."""

    def test_non_mapping_slice_entry_fails_loudly(self) -> None:
        with pytest.raises(dev_check.DevCheckError, match="not a mapping"):
            dev_check.obligation_groups_for_slice({"slices": {1: "oops"}}, 1)

    def test_non_list_obligations_field_fails_loudly(self) -> None:
        with pytest.raises(dev_check.DevCheckError, match="not a list"):
            dev_check.obligation_groups_for_slice({"slices": {1: {"obligations": "oops"}}}, 1)


# --- obligations-vs-task consistency checks ----------------------------------


def _fixture_task(tmp_path: Path, **overrides: Any) -> dict[str, Any]:
    """A minimal resolved-task-shaped dict pointing at a throwaway provenance
    file under `tmp_path`, ready for validate_obligations_against_task."""
    provenance = tmp_path / "provenance.md"
    provenance.write_text("Pinned commit: `043b13adc264689c376bdd337603e94d5447623a`\n", encoding="utf-8")
    task = {
        "task_id": "fixture-task",
        "plan_file": "docs/FIXTURE_PLAN.md",
        "provenance_file": str(provenance.relative_to(tmp_path)),
    }
    task.update(overrides)
    return task


class TestValidateObligationsAgainstTask:
    def test_matching_plan_and_pin_pass_silently(self, tmp_path: Path) -> None:
        task = _fixture_task(tmp_path)
        obligations = {"plan": "docs/FIXTURE_PLAN.md", "plan_pin": "043b13adc264689c376bdd337603e94d5447623a"}
        dev_check.validate_obligations_against_task(obligations, task, tmp_path, tmp_path / "obligations.yaml")

    def test_plan_mismatch_names_expected_and_found_values(self, tmp_path: Path) -> None:
        task = _fixture_task(tmp_path)
        obligations = {"plan": "docs/OTHER_PLAN.md", "plan_pin": "043b13adc264689c376bdd337603e94d5447623a"}
        with pytest.raises(dev_check.DevCheckError) as excinfo:
            dev_check.validate_obligations_against_task(obligations, task, tmp_path, tmp_path / "obligations.yaml")
        message = str(excinfo.value)
        assert "docs/OTHER_PLAN.md" in message and "docs/FIXTURE_PLAN.md" in message

    def test_plan_pin_mismatch_names_expected_and_found_values(self, tmp_path: Path) -> None:
        task = _fixture_task(tmp_path)
        obligations = {"plan": "docs/FIXTURE_PLAN.md", "plan_pin": "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"}
        with pytest.raises(dev_check.DevCheckError) as excinfo:
            dev_check.validate_obligations_against_task(obligations, task, tmp_path, tmp_path / "obligations.yaml")
        message = str(excinfo.value)
        assert "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef" in message
        assert "043b13adc264689c376bdd337603e94d5447623a" in message

    def test_missing_fields_count_as_disagreement_never_guesses(self, tmp_path: Path) -> None:
        task = _fixture_task(tmp_path)
        with pytest.raises(dev_check.DevCheckError, match="plan=None"):
            dev_check.validate_obligations_against_task({}, task, tmp_path, tmp_path / "obligations.yaml")
        with pytest.raises(dev_check.DevCheckError):
            dev_check.validate_obligations_against_task({"plan": "docs/FIXTURE_PLAN.md"}, task, tmp_path, tmp_path / "o.yaml")

    def test_provenance_without_a_pinned_line_is_a_named_error(self, tmp_path: Path) -> None:
        task = _fixture_task(tmp_path)
        (tmp_path / task["provenance_file"]).write_text("no pin here\n", encoding="utf-8")
        obligations = {"plan": "docs/FIXTURE_PLAN.md"}
        with pytest.raises(dev_check.DevCheckError, match="Pinned commit"):
            dev_check.validate_obligations_against_task(obligations, task, tmp_path, tmp_path / "obligations.yaml")


# --- run/task repository cross-check -----------------------------------------


class TestRunBelongsToTaskCrossCheck:
    """The graded RUN must belong to the resolved TASK -- a mistyped-but-valid
    --task must fail loudly rather than silently grade under the wrong rubric.
    Membership is structural git-worktree membership, never literal path
    equality (a trial worktree's path is never equal to the configured one)."""

    @staticmethod
    def _git_repo(base: Path, name: str) -> Path:
        repo = base / name
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
        (repo / "README.md").write_text("hello\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=repo, check=True)
        return repo

    def test_recorded_repo_identical_to_configured_passes(self, tmp_path: Path) -> None:
        repo = self._git_repo(tmp_path, "substrate")
        task = {"task_id": "t", "repo": str(repo)}
        returned = dev_check.check_run_belongs_to_task({"repo": str(repo)}, task, tmp_path)
        assert returned == repo.resolve()

    def test_recorded_worktree_of_the_configured_repo_passes(self, tmp_path: Path) -> None:
        substrate = self._git_repo(tmp_path, "substrate")
        worktree = tmp_path / "trial-1"
        subprocess.run(
            ["git", "-C", str(substrate), "worktree", "add", "--detach", str(worktree), "HEAD"],
            check=True, capture_output=True, text=True,
        )
        task = {"task_id": "t", "repo": str(substrate)}
        returned = dev_check.check_run_belongs_to_task({"repo": str(worktree)}, task, tmp_path)
        assert returned == worktree.resolve()

    def test_unrelated_repo_fails_loudly_naming_both_paths(self, tmp_path: Path) -> None:
        substrate = self._git_repo(tmp_path, "substrate")
        other = self._git_repo(tmp_path, "other-repo")
        task = {"task_id": "t", "repo": str(substrate)}
        with pytest.raises(dev_check.DevCheckError) as excinfo:
            dev_check.check_run_belongs_to_task({"repo": str(other)}, task, tmp_path)
        message = str(excinfo.value)
        assert str(other) in message and str(substrate) in message and "'t'" in message

    def test_run_json_with_no_recorded_repo_fails_loudly(self, tmp_path: Path) -> None:
        task = {"task_id": "t", "repo": str(tmp_path / "substrate")}
        with pytest.raises(dev_check.DevCheckError, match="missing or not a string"):
            dev_check.check_run_belongs_to_task({}, task, tmp_path)

    def test_non_string_repo_value_fails_loudly_naming_the_offending_value(self, tmp_path: Path) -> None:
        # A syntactically valid run.json can still carry a non-string repo
        # value; that must be a named DevCheckError, never the raw TypeError
        # Path(42) would raise.
        task = {"task_id": "t", "repo": str(tmp_path / "substrate")}
        for bad in (42, ["not", "a", "path"]):
            with pytest.raises(dev_check.DevCheckError) as excinfo:
                dev_check.check_run_belongs_to_task({"repo": bad}, task, tmp_path)
            message = str(excinfo.value)
            assert repr(bad) in message
            assert "'t'" in message

    def test_configured_side_that_is_not_a_git_repo_fails_loudly_not_false(self, tmp_path: Path) -> None:
        # bench_lib raises BenchLibError when `git worktree list` fails on the
        # configured side; this wrapper must convert it to DevCheckError
        # (never a guessed False that would misattribute the run).
        recorded = self._git_repo(tmp_path, "recorded")
        not_a_repo = tmp_path / "not-a-repo"
        not_a_repo.mkdir()
        task = {"task_id": "t", "repo": str(not_a_repo)}
        with pytest.raises(dev_check.DevCheckError, match="could not determine whether"):
            dev_check.check_run_belongs_to_task({"repo": str(recorded)}, task, tmp_path)


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


def test_score_correctness_returns_by_node_with_every_outcome() -> None:
    groups = [
        {"id": "group_a", "tests": ["tests/test_hA.py::test_one", "tests/test_hA.py::test_two"]},
        {"id": "group_b", "tests": ["tests/test_hA.py::test_three"]},
    ]
    outcomes = {
        "tests/test_hA.py::test_one": "passed",
        "tests/test_hA.py::test_two": "failed",
        "tests/test_hA.py::test_three": "error",
    }
    result = dev_check.score_correctness(outcomes, groups, slice_number=1)
    assert result["by_node"] == outcomes


def test_score_correctness_by_node_keys_are_sorted() -> None:
    groups = [
        {"id": "group_a", "tests": ["tests/test_hA.py::test_two", "tests/test_hA.py::test_one"]},
        {"id": "group_b", "tests": ["tests/test_hA.py::test_three"]},
    ]
    outcomes = {
        "tests/test_hA.py::test_two": "passed",
        "tests/test_hA.py::test_one": "passed",
        "tests/test_hA.py::test_three": "skipped",
    }
    result = dev_check.score_correctness(outcomes, groups, slice_number=1)
    assert list(result["by_node"]) == sorted(outcomes)


# --- cumulative upsert -----------------------------------------------------


_TEST_DEVELOPER_BLOCK = {
    "harness": "claude",
    "model": "some/model",
    "effort": "low",
    "configuration_key": "some/model · claude · low",
    "sources": {"harness": "run_harness", "model": "run_harness", "effort": "run_harness"},
    "attributed": True,
    "attestation": None,
}


class TestCumulativeUpsert:
    def _base_kwargs(self, attempt_entry: dict) -> dict:
        return dict(
            run_id="run-1",
            developer=_TEST_DEVELOPER_BLOCK,
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

    def test_regrading_an_attempt_preserves_existing_reviews(self) -> None:
        """An attempt's `reviews` list (one record per commission) must
        never be clobbered when `upsert_attempt` re-grades that attempt."""
        sheet = dev_check.upsert_attempt(None, **self._base_kwargs({"attempt": 1, "commit_sha": "aaa"}))
        sheet["attempts"][0]["reviews"] = [
            {"skill": "drift-audit", "event_index": 3, "findings_by_severity": {"P1": 0}},
            {"skill": "code-review", "event_index": 4, "findings_by_severity": {"P2": 1}},
        ]

        # Tool 1 re-grades attempt 1 (e.g. re-run for idempotency) without
        # touching the reviews list -- its upsert must not clobber it.
        sheet = dev_check.upsert_attempt(sheet, **self._base_kwargs({"attempt": 1, "commit_sha": "aaa-regraded"}))

        assert sheet["attempts"][0]["commit_sha"] == "aaa-regraded"
        assert sheet["attempts"][0]["reviews"] == [
            {"skill": "drift-audit", "event_index": 3, "findings_by_severity": {"P1": 0}},
            {"skill": "code-review", "event_index": 4, "findings_by_severity": {"P2": 1}},
        ]

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


class TestCheckRegradeTaskIdentity:
    """The cross-task guard covers EVERY existing row, not just the one about
    to be replaced, and refuses malformed provenance values loudly."""

    @staticmethod
    def _sheet(*rows: dict[str, Any]) -> dict[str, Any]:
        return {"run_id": "run-1", "slice": 1, "attempts": list(rows)}

    def test_no_existing_sheet_is_a_noop(self) -> None:
        dev_check.check_regrade_task_identity(None, "task-a", "task-a")

    def test_matching_ids_pass(self) -> None:
        sheet = self._sheet({"attempt": 0, "provenance": {"task_id": "task-a"}})
        dev_check.check_regrade_task_identity(sheet, "task-a", "task-a")

    def test_legacy_provenance_counts_as_the_historical_default(self) -> None:
        # Missing task_id == pre-migration == structurally default_task only:
        # allowed under the default, refused under anything else.
        sheet = self._sheet({"attempt": 0, "provenance": {"plan_hash": "x"}})
        dev_check.check_regrade_task_identity(sheet, "task-a", "task-a")
        with pytest.raises(dev_check.DevCheckError) as excinfo:
            dev_check.check_regrade_task_identity(sheet, "task-b", "task-a")
        message = str(excinfo.value)
        assert "'task-a'" in message and "'task-b'" in message and "attempt 0" in message

    def test_new_attempt_under_a_different_task_than_an_existing_row_is_refused(self) -> None:
        # Attempt 1 has never been graded, so its row does not exist yet; a
        # guard that only inspected the row about to be replaced would pass
        # trivially and leave one sheet with two rubrics.
        sheet = self._sheet({"attempt": 0, "provenance": {"task_id": "task-a"}})
        with pytest.raises(dev_check.DevCheckError) as excinfo:
            dev_check.check_regrade_task_identity(sheet, "task-b", "task-a")
        message = str(excinfo.value)
        assert "'task-a'" in message and "'task-b'" in message and "attempt 0" in message

    def test_non_mapping_provenance_fails_loudly_naming_attempt_and_value(self) -> None:
        # A hand-corrupted sheet must fail loudly, never be silently read as
        # legacy (no task_id) regardless of which task is being resolved.
        for bad in ("corrupt", ["a", "list"], 42):
            sheet = self._sheet({"attempt": 3, "provenance": bad})
            with pytest.raises(dev_check.DevCheckError) as excinfo:
                dev_check.check_regrade_task_identity(sheet, "task-a", "task-a")
            message = str(excinfo.value)
            assert repr(bad) in message
            assert "attempt 3" in message


# --- resolve_before_head's structural fallbacks ---------------------------


class TestResolveBeforeHead:
    """A slice's before_head is a permanent, structural fact (set once at
    start_slice, never touched by steer/relaunch -- verified directly
    against pm_lib source). These cover the four resolution paths in
    priority order, plus the explicit-override escape hatch and the
    fully-exhausted failure case.
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
        # permanently in run.json -- this is what recovers a post-hoc grade
        # of Slice 1's final attempt.
        run_state = {"current_slice": None, "slices": [{"id": "Slice 1", "commit": "slice1-end-commit"}]}
        entry = {"reviews": [{"skill": "drift-audit", "before_head": "plan-base-commit"}]}
        assert dev_check.resolve_before_head(run_state, "Slice 1", None, 3, entry) == "plan-base-commit"

    def test_first_slice_never_graded_and_never_reviewed_fails_loudly_naming_every_path(self) -> None:
        run_state = {"current_slice": None, "slices": [{"id": "Slice 1", "commit": "x"}]}
        with pytest.raises(dev_check.DevCheckError, match="pass --before-head explicitly"):
            dev_check.resolve_before_head(run_state, "Slice 1", None, 0, {"reviews": []})

    def test_the_most_recent_review_is_used_not_the_first_restart_epoch_regression(self) -> None:
        # before_head is only constant WITHIN one uninterrupted in-flight
        # epoch -- a finalize --stop followed by a later start-slice on the
        # same still-unaccepted slice captures a brand-new before_head, so
        # picking the FIRST review found could return a stale, pre-restart
        # value for a post-restart attempt. The most recent review is
        # correct: this bench's plan mandates a fresh review before
        # acceptance, so the last-recorded review for an accepted slice
        # always belongs to the attempt that was actually accepted.
        run_state = {"current_slice": None, "slices": [{"id": "Slice 1", "commit": "slice1-end-commit"}]}
        entry = {
            "reviews": [
                {"skill": "drift-audit", "before_head": "PRE-restart-stale-value", "at": "t1"},
                {"skill": "drift-audit", "before_head": "POST-restart-correct-value", "at": "t9"},
            ]
        }
        assert dev_check.resolve_before_head(run_state, "Slice 1", None, 5, entry) == "POST-restart-correct-value"

    def test_a_stale_review_appended_after_the_accepted_epochs_review_is_not_picked(self) -> None:
        # Reviews commission concurrently, so a slow, earlier-epoch review's
        # report can be parsed and appended to entry["reviews"] AFTER a
        # faster, current-epoch review's -- "most recent by list position"
        # alone can still pick a stale before_head for an ACCEPTED slice.
        # For an accepted slice, resolution must filter to the review whose
        # `head` matches entry["commit"] (the exact accepted commit) before
        # taking the most recent such match.
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
    """lint.py exits 1 specifically when --base mode finds new
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


# --- --require-coverage is actually passed, making the exit-3 --------------
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


# --- sheet identity guard ---------------------------------------------------


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
    latest/live one."""

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


class TestHiddenTestsManifestHash:
    # The manifest hashes exactly the DERIVED filename set out of the resolved
    # task's own hidden_tests_dir -- no hardcoded file list remains anywhere.
    _TASK = {"task_id": "fixture-task", "hidden_tests_dir": "hidden_tests"}

    def _write_hidden_tests(self, root: Path, slice_number: int, contents: dict[str, str]) -> None:
        source_dir = root / "hidden_tests" / f"slice{slice_number}"
        source_dir.mkdir(parents=True, exist_ok=True)
        for filename, text in contents.items():
            (source_dir / filename).write_text(text, encoding="utf-8")

    def test_hash_changes_when_a_hidden_test_files_bytes_change(self, tmp_path: Path) -> None:
        self._write_hidden_tests(
            tmp_path, 1, {"test_hA.py": "def test_a():\n    pass\n", "test_hB.py": "def test_b():\n    pass\n"}
        )
        filenames = {"test_hA.py", "test_hB.py"}
        before = dev_check.hidden_tests_manifest_hash(tmp_path, self._TASK, 1, filenames)
        (tmp_path / "hidden_tests" / "slice1" / "test_hB.py").write_text(
            "def test_b():\n    assert True\n", encoding="utf-8"
        )
        after = dev_check.hidden_tests_manifest_hash(tmp_path, self._TASK, 1, filenames)
        assert before != after

    def test_manifest_follows_a_nonstandard_derived_filename_set(self, tmp_path: Path) -> None:
        # A task whose slice references other files: the manifest covers
        # precisely those, and ignores any leftover hA/hB files on disk.
        self._write_hidden_tests(
            tmp_path, 2,
            {
                "test_zz.py": "def test_z():\n    pass\n",
                "test_qq.py": "def test_q():\n    pass\n",
                "test_hA.py": "leftover, must not be hashed\n",
            },
        )
        digest = dev_check.hidden_tests_manifest_hash(tmp_path, self._TASK, 2, {"test_zz.py", "test_qq.py"})
        only_zz = dev_check.hidden_tests_manifest_hash(tmp_path, self._TASK, 2, {"test_zz.py"})
        assert digest != only_zz  # both referenced files contribute
        (tmp_path / "hidden_tests" / "slice2" / "test_hA.py").write_text("changed leftover\n", encoding="utf-8")
        assert dev_check.hidden_tests_manifest_hash(tmp_path, self._TASK, 2, {"test_zz.py", "test_qq.py"}) == digest

    def test_missing_hidden_test_file_raises_dev_check_error_naming_the_path(self, tmp_path: Path) -> None:
        source_dir = tmp_path / "hidden_tests" / "slice1"
        source_dir.mkdir(parents=True, exist_ok=True)
        (source_dir / "test_hA.py").write_text("def test_a():\n    pass\n", encoding="utf-8")
        # test_hB.py is deliberately not written.
        with pytest.raises(dev_check.DevCheckError, match=str(source_dir / "test_hB.py")):
            dev_check.hidden_tests_manifest_hash(tmp_path, self._TASK, 1, {"test_hA.py", "test_hB.py"})


class TestRunHiddenTests:
    def test_copies_and_pytest_argv_target_exactly_the_derived_nonstandard_filenames(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # A fixture task whose slice references filenames other than
        # test_hA.py/test_hB.py: BOTH the copy loop and the pytest subprocess
        # argv must target precisely the derived set -- proven by letting the
        # real pytest run against them and recording its actual argv.
        root = tmp_path / "bench-root"
        source_dir = root / "hidden_tests" / "slice1"
        source_dir.mkdir(parents=True)
        (source_dir / "test_zz.py").write_text("def test_z():\n    assert True\n", encoding="utf-8")
        (source_dir / "test_qq.py").write_text("def test_q():\n    assert True\n", encoding="utf-8")
        worktree = tmp_path / "worktree"
        worktree.mkdir()
        # Pin the child pytest's rootdir inside the throwaway worktree so no
        # ancestor configuration can leak into this invocation.
        (worktree / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
        policy = {"python_interpreter": sys.executable, "subprocess_timeout_seconds": 600}
        task = {"task_id": "fixture-task", "hidden_tests_dir": "hidden_tests"}

        recorded: list[list[str]] = []
        real_run = dev_check.subprocess.run

        def spy_run(cmd, *args, **kwargs):
            recorded.append(list(cmd))
            return real_run(cmd, *args, **kwargs)

        monkeypatch.setattr(dev_check.subprocess, "run", spy_run)

        outcomes = dev_check.run_hidden_tests(worktree, 1, root, policy, task, {"test_zz.py", "test_qq.py"})

        copied = sorted(p.name for p in (worktree / "tests").glob("*.py"))
        assert copied == ["test_qq.py", "test_zz.py"]
        assert len(recorded) == 1
        argv = recorded[0]
        assert argv[:3] == [sys.executable, "-m", "pytest"]
        assert argv[3:5] == ["tests/test_qq.py", "tests/test_zz.py"]
        assert set(outcomes) == {"tests/test_qq.py::test_q", "tests/test_zz.py::test_z"}
        assert all(value == "passed" for value in outcomes.values())


class TestReadEvents:
    def test_a_missing_log_is_empty_not_an_error(self, tmp_path: Path) -> None:
        assert dev_check.read_events(tmp_path) == []

    def test_a_corrupt_line_fails_loudly_naming_the_line(self, tmp_path: Path) -> None:
        (tmp_path / "events.jsonl").write_text('{"kind": "launch"}\nnot json\n', encoding="utf-8")
        with pytest.raises(dev_check.DevCheckError, match="events.jsonl:2"):
            dev_check.read_events(tmp_path)


# --- synthetic-fixture tests over main() -------------------------------------
#
# main() is otherwise untouched by any test in this module. pm_lib and the
# external quality/pytest subprocesses are stubbed; the git repo and the
# grading worktree are real (grading_worktree/run_git are exercised for real).


# The obligations map every synthetic main() run loads via the monkeypatched
# load_obligations below. Its plan:/plan_pin: must agree with the fixture
# policy's own task entry -- exactly what validate_obligations_against_task
# checks live inside main(), parsing the REAL pinned commit out of
# docs/MERGER_RATE_PLAN-2SLICE.provenance.md under the bench root.
_STUB_OBLIGATIONS = {
    "plan": "docs/MERGER_RATE_PLAN-2SLICE.md",
    "plan_pin": "043b13adc264689c376bdd337603e94d5447623a",
    "slices": {1: {"obligations": [{"id": "g1", "tests": ["tests/test_hA.py::test_one"]}]}},
}

# A minimal resolved-task-shaped view of the fixture policy's single entry --
# just the fields the functions under test read directly (task["task_id"],
# task["hidden_tests_dir"]). main() itself always gets the FULLY resolved and
# validated dict from bench_lib.resolve_task against the written policy file.
_FIXTURE_TASK_ENTRY = {"task_id": "fixture-task", "hidden_tests_dir": "hidden_tests"}


class TestMainSyntheticRun:
    def _make_run_dir(self, tmp_path: Path, repo: Path, head: str, *, current_slice: bool = True) -> Path:
        run_dir = tmp_path / "pm-run"
        run_dir.mkdir()
        # The recorded plan path points INSIDE the run's own repo -- exactly
        # what real runs record (a copy of the frozen plan inside the trial
        # worktree, e.g. <worktree>/docs/MERGER_RATE_PLAN-2SLICE.md) -- and it
        # must agree with the fixture task's plan_file, since main() cross-
        # checks the two via check_plan_matches_task before any grading work.
        plan_path = repo / "docs" / "MERGER_RATE_PLAN-2SLICE.md"
        plan_path.parent.mkdir(parents=True, exist_ok=True)
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
        # resolve_attempt() derives the attempt key from
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
        # Two args now: main() passes the resolved task's own obligations_file
        # as the second; the stub ignores which one was asked for.
        monkeypatch.setattr(dev_check, "load_obligations", lambda root, relative_path=None: _STUB_OBLIGATIONS)

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

        def fake_run_hidden_tests(worktree, slice_number, root, policy, task, filenames):
            # Copy something in for real -- every DERIVED filename main()
            # handed over -- so the pristine-worktree assertion above has
            # something to detect if the ordering ever regresses.
            target = Path(worktree) / "tests"
            target.mkdir(parents=True, exist_ok=True)
            for filename in sorted(filenames):
                (target / filename).write_text("def test_one():\n    pass\n", encoding="utf-8")
            call_order.append("hidden_tests")
            return {"tests/test_hA.py::test_one": "passed"}

        monkeypatch.setattr(dev_check, "run_lint", fake_run_lint)
        monkeypatch.setattr(dev_check, "run_code_health", fake_run_code_health)
        monkeypatch.setattr(dev_check, "run_hidden_tests", fake_run_hidden_tests)

    def _fixture_policy(self, repo: Path, *, configured_repo: Path | None = None) -> dict[str, Any]:
        """The full fixture policy as a dict: global measurement METHODOLOGY
        keys plus a tasks: registry whose single entry points at the
        throwaway `repo` itself (or `configured_repo`, when a test needs the
        task to configure a DIFFERENT repository than the run records), and
        whose plan/provenance files are the real frozen ones under the bench
        root (validate_obligations_against_task parses the pin from the real
        provenance file)."""
        return {
            "backend": "local",
            "pm_scripts_dir": "/x",
            "lint_script": "/x",
            "health_script": "/x",
            "python_interpreter": "python3",
            "grading_worktree_root": None,
            "subprocess_timeout_seconds": 600,
            "measurement": {
                "loc_definition": "net_physical_lines",
                "loc_category_definition": "ast_tokenize_line_classification",
                "metric_version": 2,
            },
            "default_task": "fixture-task",
            "tasks": {
                "fixture-task": {
                    "repo": str(configured_repo or repo),
                    "branch_prefix": "pm-eval-v2",
                    "worktree_root": None,
                    "plan_file": "docs/MERGER_RATE_PLAN-2SLICE.md",
                    "provenance_file": "docs/MERGER_RATE_PLAN-2SLICE.provenance.md",
                    "hidden_tests_dir": "hidden_tests",
                    "obligations_file": "hidden_tests/obligations.yaml",
                    "expected_slices": 2,
                    "measurement": {
                        "production_paths": ["src/**/*.py"],
                        "test_paths": ["tests/**/*.py"],
                        "doc_paths": ["docs/**/*.md", "*.md"],
                    },
                }
            },
        }

    def _policy_path(self, tmp_path: Path, repo: Path, *, configured_repo: Path | None = None) -> Path:
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text(
            yaml.safe_dump(self._fixture_policy(repo, configured_repo=configured_repo), sort_keys=False),
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
                "--policy", str(self._policy_path(tmp_path, repo)),
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

    def test_explicit_task_flag_and_omitted_default_resolve_to_the_same_grade(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """--task omitted falls back to default_task; giving the same id
        explicitly must produce an identical sheet apart from the always-
        refreshed timestamp."""
        repo = _make_repo(tmp_path)
        head = self._head(repo)
        run_dir = self._make_run_dir(tmp_path, repo, head)
        call_order: list = []
        self._stub_everything(monkeypatch, call_order)
        base_argv = [
            "--run-dir", str(run_dir), "--slice", "1",
            "--policy", str(self._policy_path(tmp_path, repo)),
        ]

        assert dev_check.main([*base_argv, "--out", str(tmp_path / "default.json")]) == 0
        assert dev_check.main([*base_argv, "--task", "fixture-task", "--out", str(tmp_path / "explicit.json")]) == 0

        default_sheet = json.loads((tmp_path / "default.json").read_text())
        explicit_sheet = json.loads((tmp_path / "explicit.json").read_text())
        for sheet in (default_sheet, explicit_sheet):
            provenance = sheet["attempts"][0]["provenance"]
            # task_id stamped alongside the existing hash triple on every attempt.
            assert provenance["task_id"] == "fixture-task"
            assert all(provenance.get(key) is not None for key in ("plan_hash", "obligations_hash", "hidden_tests_hash"))
        for sheet in (default_sheet, explicit_sheet):
            sheet["attempts"][0].pop("timestamp")
        assert default_sheet == explicit_sheet

    def test_unknown_task_fails_loudly_naming_it_and_the_configured_ids(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        repo = _make_repo(tmp_path)
        head = self._head(repo)
        run_dir = self._make_run_dir(tmp_path, repo, head)
        call_order: list = []
        self._stub_everything(monkeypatch, call_order)

        with pytest.raises(dev_check.DevCheckError, match="does-not-exist"):
            dev_check.main(
                [
                    "--run-dir", str(run_dir), "--slice", "1", "--task", "does-not-exist",
                    "--policy", str(self._policy_path(tmp_path, repo)),
                    "--out", str(tmp_path / "sheet.json"),
                ]
            )
        # Nothing was graded: resolution happens before any grading work.
        assert call_order == []
        assert not (tmp_path / "sheet.json").exists()

    def test_main_refuses_a_run_recorded_under_a_different_repo_than_the_task_configures(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Guards main()'s own call sequence: every other fixture grades a run
        # whose recorded repo matches the resolved task's configured one, so
        # silently dropping, reordering, or short-circuiting the
        # check_run_belongs_to_task call inside main() would leave the whole
        # suite green. Here the two repos are distinct REAL git repositories,
        # so the structural membership check genuinely determines "no".
        (tmp_path / "recorded-side").mkdir()
        (tmp_path / "configured-side").mkdir()
        recorded_repo = _make_repo(tmp_path / "recorded-side")
        configured_repo = _make_repo(tmp_path / "configured-side")
        head = self._head(recorded_repo)
        run_dir = self._make_run_dir(tmp_path, recorded_repo, head)
        call_order: list = []
        self._stub_everything(monkeypatch, call_order)
        out_path = tmp_path / "sheet.json"

        with pytest.raises(dev_check.DevCheckError) as excinfo:
            dev_check.main(
                [
                    "--run-dir", str(run_dir), "--slice", "1",
                    "--policy", str(self._policy_path(tmp_path, recorded_repo, configured_repo=configured_repo)),
                    "--out", str(out_path),
                ]
            )
        message = str(excinfo.value)
        assert str(recorded_repo) in message
        assert str(configured_repo) in message
        # The refusal lands before ANY grading work: no quality tool ran, no
        # hidden tests were copied, and nothing was written.
        assert call_order == []
        assert not out_path.exists()

    def test_main_refuses_when_the_selected_tasks_plan_differs_from_the_runs_recorded_plan(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Two tasks share ONE repository but configure different plan files:
        # scope discipline is computed from the plan the RUN records, entirely
        # independent of --task, so selecting the wrong sibling task must fail
        # loudly instead of blending its rubric with another plan's
        # authorization surface.
        repo = _make_repo(tmp_path)
        head = self._head(repo)
        run_dir = self._make_run_dir(tmp_path, repo, head)  # records <repo>/docs/MERGER_RATE_PLAN-2SLICE.md
        call_order: list = []
        self._stub_everything(monkeypatch, call_order)
        out_path = tmp_path / "sheet.json"

        base_entry = self._fixture_policy(repo)["tasks"]["fixture-task"]
        policy = {
            **self._fixture_policy(repo),
            "default_task": "task-a",
            "tasks": {
                "task-a": base_entry,  # its plan_file agrees with the run's record
                "task-b": {**base_entry, "plan_file": "docs/SOME_OTHER_PLAN.md"},
            },
        }
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text(yaml.safe_dump(policy, sort_keys=False), encoding="utf-8")
        argv_base = ["--run-dir", str(run_dir), "--slice", "1", "--policy", str(policy_path), "--out", str(out_path)]

        # Under the matching task everything passes ...
        assert dev_check.main([*argv_base, "--task", "task-a"]) == 0
        sheet_after_a = json.loads(out_path.read_text())

        # ...but the same-repo sibling task is refused, naming both values,
        # before any further grading work and without touching the sheet.
        calls_before = len(call_order)
        with pytest.raises(dev_check.DevCheckError) as excinfo:
            dev_check.main([*argv_base, "--task", "task-b"])
        message = str(excinfo.value)
        assert str(repo / "docs" / "MERGER_RATE_PLAN-2SLICE.md") in message
        assert "SOME_OTHER_PLAN.md" in message
        assert len(call_order) == calls_before
        assert json.loads(out_path.read_text()) == sheet_after_a

    def test_regrading_an_attempt_under_a_different_task_is_refused_naming_both_ids(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The preserved-provenance rule has one hard limit: an attempt already
        # graded under task A must not be silently re-scored under task B while
        # keeping A's provenance -- that would be a sheet whose numbers came
        # from one rubric while its identity names another. Both tasks here
        # share the repo AND the plan (so both cross-checks pass for either);
        # they differ only in their rubric location.
        repo = _make_repo(tmp_path)
        head = self._head(repo)
        run_dir = self._make_run_dir(tmp_path, repo, head)
        call_order: list = []
        self._stub_everything(monkeypatch, call_order)
        out_path = tmp_path / "sheet.json"

        base_entry = self._fixture_policy(repo)["tasks"]["fixture-task"]
        policy = {
            **self._fixture_policy(repo),
            "default_task": "task-a",
            "tasks": {
                "task-a": base_entry,
                "task-b": {
                    **base_entry,
                    "hidden_tests_dir": "hidden_tests_b",
                    "obligations_file": "hidden_tests_b/obligations.yaml",
                },
            },
        }
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text(yaml.safe_dump(policy, sort_keys=False), encoding="utf-8")

        argv_base = ["--run-dir", str(run_dir), "--slice", "1", "--policy", str(policy_path), "--out", str(out_path)]

        assert dev_check.main([*argv_base, "--task", "task-a"]) == 0
        sheet_after_a = json.loads(out_path.read_text())
        assert sheet_after_a["attempts"][0]["provenance"]["task_id"] == "task-a"
        calls_after_first_grade = len(call_order)

        with pytest.raises(dev_check.DevCheckError) as excinfo:
            dev_check.main([*argv_base, "--task", "task-b"])
        message = str(excinfo.value)
        assert "'task-a'" in message
        assert "'task-b'" in message
        # The refusal lands right after the sheet loads, BEFORE any grading
        # work: no lint/code-health/hidden-test call ran during the doomed regrade.
        assert len(call_order) == calls_after_first_grade
        # ...and nothing was rewritten on disk.
        assert json.loads(out_path.read_text()) == sheet_after_a

    def _write_legacy_sheet(self, out_path: Path, head: str) -> dict[str, Any]:
        """A pre-migration scoring sheet: same shape this tool writes, except
        the attempt's provenance block carries NO task_id (sheets graded
        before multi-task support landed never had one)."""
        sheet = {
            "run_id": "run-a1",
            "slice": 1,
            "developer": {"tool": "legacy-tool", "model": "legacy-model", "effort": None},
            "run_status": {},
            "attempts": [
                {
                    "attempt": 0,
                    "commit_sha": head,
                    "correctness": {"hidden_tests_passed": 0, "hidden_tests_total": 1, "fraction": 0.0},
                    "provenance": {
                        "plan_hash": "legacy-plan-hash",
                        "policy_hash": "legacy-policy-hash",
                        "obligations_hash": "legacy-obligations-hash",
                        "hidden_tests_hash": "legacy-hidden-tests-hash",
                        "base_commit": head,
                        "pm_skill_version": None,
                    },
                }
            ],
            "accepted_at_attempt": None,
            "pm_model_performance_ref": None,
        }
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(sheet), encoding="utf-8")
        return sheet

    def test_legacy_provenance_attempt_can_still_be_regraded_under_default_task(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Pre-migration sheets carry no provenance.task_id; they count as the
        # historical default_task, so a regrade under default_task must keep
        # working (Slice 3's backfill semantics rely on exactly this):
        # the results refresh while the legacy identity is preserved verbatim.
        repo = _make_repo(tmp_path)
        head = self._head(repo)
        run_dir = self._make_run_dir(tmp_path, repo, head)
        call_order: list = []
        self._stub_everything(monkeypatch, call_order)
        out_path = tmp_path / "sheet.json"
        legacy_sheet = self._write_legacy_sheet(out_path, head)

        rc = dev_check.main([
            "--run-dir", str(run_dir), "--slice", "1",
            "--policy", str(self._policy_path(tmp_path, repo)),
            "--out", str(out_path),
        ])
        assert rc == 0
        result = json.loads(out_path.read_text())
        # Legacy identity preserved untouched -- still no task_id key ...
        assert result["attempts"][0]["provenance"] == legacy_sheet["attempts"][0]["provenance"]
        assert "task_id" not in result["attempts"][0]["provenance"]
        # ...while the numbers themselves were refreshed by THIS regrade.
        assert result["attempts"][0]["correctness"] != legacy_sheet["attempts"][0]["correctness"]

    def test_legacy_provenance_attempt_cannot_be_regraded_under_a_non_default_task(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Mirror image of the test above: the SAME legacy sheet counts as the
        # historical default_task, so selecting any OTHER task must be refused
        # -- naming the resolved id, the default it stands in for, and the
        # attempt number -- before any grading work runs. Both tasks share the
        # repo AND the plan (so both cross-checks pass); they differ only in
        # rubric location.
        repo = _make_repo(tmp_path)
        head = self._head(repo)
        run_dir = self._make_run_dir(tmp_path, repo, head)
        call_order: list = []
        self._stub_everything(monkeypatch, call_order)
        out_path = tmp_path / "sheet.json"
        legacy_sheet = self._write_legacy_sheet(out_path, head)

        base_entry = self._fixture_policy(repo)["tasks"]["fixture-task"]
        policy = {
            **self._fixture_policy(repo),
            "default_task": "task-a",
            "tasks": {
                "task-a": base_entry,
                "task-b": {
                    **base_entry,
                    "hidden_tests_dir": "hidden_tests_b",
                    "obligations_file": "hidden_tests_b/obligations.yaml",
                },
            },
        }
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text(yaml.safe_dump(policy, sort_keys=False), encoding="utf-8")

        with pytest.raises(dev_check.DevCheckError) as excinfo:
            dev_check.main([
                "--run-dir", str(run_dir), "--slice", "1", "--task", "task-b",
                "--policy", str(policy_path), "--out", str(out_path),
            ])
        message = str(excinfo.value)
        assert "'task-b'" in message   # the resolved id
        assert "'task-a'" in message   # the historical default a missing task_id stands in for
        assert "attempt 0" in message
        assert call_order == []        # failed fast: no grading work ran at all
        assert json.loads(out_path.read_text()) == legacy_sheet   # sheet untouched

    def test_grading_a_brand_new_attempt_under_a_different_task_than_an_existing_row_is_refused(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The cross-task guard covers EVERY existing row, not just the one
        # about to be replaced: attempt 0 is graded under task A into a fresh
        # sheet, then brand-new attempt 1 (never previously graded, so NO
        # existing row) is attempted under task B. Both tasks share repo AND
        # plan (both cross-checks pass); they differ only in rubric location.
        # Without the broader check the second grade would slip through and
        # leave one sheet with two rubrics.
        repo = _make_repo(tmp_path)
        head = self._head(repo)
        run_dir = self._make_run_dir(tmp_path, repo, head)
        # Attempt 1 must exist as an event-derived ordinal: append a steer
        # event after the opening launch.
        events_path = run_dir / "events.jsonl"
        events_path.write_text(
            events_path.read_text(encoding="utf-8")
            + json.dumps({"kind": "steer", "slice": "Slice 1", "note": "attempt 1"}) + "\n",
            encoding="utf-8",
        )
        call_order: list = []
        self._stub_everything(monkeypatch, call_order)
        out_path = tmp_path / "sheet.json"

        base_entry = self._fixture_policy(repo)["tasks"]["fixture-task"]
        policy = {
            **self._fixture_policy(repo),
            "default_task": "task-a",
            "tasks": {
                "task-a": base_entry,
                "task-b": {
                    **base_entry,
                    "hidden_tests_dir": "hidden_tests_b",
                    "obligations_file": "hidden_tests_b/obligations.yaml",
                },
            },
        }
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text(yaml.safe_dump(policy, sort_keys=False), encoding="utf-8")

        argv_base = [
            "--run-dir", str(run_dir), "--slice", "1",
            "--policy", str(policy_path), "--out", str(out_path),
        ]

        assert dev_check.main([*argv_base, "--task", "task-a", "--attempt", "0"]) == 0
        sheet_after_first = json.loads(out_path.read_text())
        assert sheet_after_first["attempts"][0]["provenance"]["task_id"] == "task-a"
        calls_after_first_grade = len(call_order)

        with pytest.raises(dev_check.DevCheckError) as excinfo:
            dev_check.main([*argv_base, "--task", "task-b", "--attempt", "1"])
        message = str(excinfo.value)
        assert "'task-a'" in message   # the identity already on the sheet
        assert "'task-b'" in message   # the resolved id this invocation selected
        assert "attempt 0" in message  # the offending existing row
        # Zero grading work executed for the doomed attempt 1 ...
        assert len(call_order) == calls_after_first_grade
        # ...and the sheet still holds exactly attempt 0 under task-a.
        assert json.loads(out_path.read_text()) == sheet_after_first

    def test_a1_accepted_slice_can_still_be_graded_via_sheet_fallback(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo = _make_repo(tmp_path)
        head = self._head(repo)
        run_dir = self._make_run_dir(tmp_path, repo, head)
        call_order: list = []
        self._stub_everything(monkeypatch, call_order)
        out_path = tmp_path / "sheet.json"
        policy_path = self._policy_path(tmp_path, repo)
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

        # Loading the existing sheet before resolving before_head matters
        # here: once accepted, current_slice no longer names Slice 1, so
        # before_head could otherwise never be resolved and the accepted
        # attempt could never be graded.
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
        policy_path = self._policy_path(tmp_path, repo)

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
            "--policy", str(self._policy_path(tmp_path, repo)), "--out", str(out_path),
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

    def test_pm_attempts_counter_survives_a_regrade(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A regrade of a historical attempt must not overwrite its recorded
        pm_attempts_counter with whatever PM's own counter currently reads.

        `resolve_pm_attempts_counter` only ever sees *current* run.json
        state, so calling it again after a later steer (or a stop/restart,
        which resets the counter to 0) would silently misrecord attempt 0's
        counter, defeating the field's only purpose: locating PM's
        historical attempt-<n>/ artifacts.
        """
        repo = _make_repo(tmp_path)
        head = self._head(repo)
        run_dir = self._make_run_dir(tmp_path, repo, head)
        call_order: list = []
        self._stub_everything(monkeypatch, call_order)
        out_path = tmp_path / "sheet.json"
        argv = [
            "--run-dir", str(run_dir), "--slice", "1", "--attempt", "0",
            "--policy", str(self._policy_path(tmp_path, repo)), "--out", str(out_path),
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

    def test_provenance_survives_a_regrade_after_policy_and_obligations_change(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Grade an attempt, change policy.yaml's and obligations.yaml's
        bytes, regrade the same attempt, and assert the original provenance
        block -- including policy_hash and obligations_hash -- survives
        byte-for-byte. The existing accepted-slice test only checks
        base_commit; this is the discriminating test for the rest of the
        provenance block."""
        repo = _make_repo(tmp_path)
        head = self._head(repo)
        run_dir = self._make_run_dir(tmp_path, repo, head)
        call_order: list = []
        self._stub_everything(monkeypatch, call_order)

        # build_provenance hashes the RESOLVED TASK's obligations file and
        # hidden tests under bench_root(), not the load_obligations() stub --
        # point bench_root at a throwaway directory this test controls so the
        # obligations file's bytes can be changed between grades.
        fake_bench_root = tmp_path / "fake-bench-root"
        obligations_path = fake_bench_root / "hidden_tests" / "obligations.yaml"  # the fixture task's obligations_file
        obligations_path.parent.mkdir(parents=True, exist_ok=True)
        obligations_path.write_text("slices: {}\n", encoding="utf-8")
        # validate_obligations_against_task parses the pinned commit out of
        # the task's provenance file under the same (now-fake) root.
        provenance_path = fake_bench_root / "docs" / "MERGER_RATE_PLAN-2SLICE.provenance.md"
        provenance_path.parent.mkdir(parents=True, exist_ok=True)
        provenance_path.write_text(
            "Pinned commit: `043b13adc264689c376bdd337603e94d5447623a`\n", encoding="utf-8"
        )
        monkeypatch.setattr(dev_check, "bench_root", lambda: fake_bench_root)

        # build_provenance also hashes this slice's DERIVED hidden test files
        # under bench_root() (hidden_tests_manifest_hash) -- give the fake
        # root exactly those, mirroring run_hidden_tests's own check.
        hidden_files = dev_check.hidden_test_filenames(_STUB_OBLIGATIONS["slices"][1]["obligations"], obligations_path)
        hidden_tests_dir = fake_bench_root / "hidden_tests" / "slice1"
        hidden_tests_dir.mkdir(parents=True, exist_ok=True)
        for filename in sorted(hidden_files):
            (hidden_tests_dir / filename).write_text("def test_one():\n    pass\n", encoding="utf-8")

        out_path = tmp_path / "sheet.json"
        policy_path = self._policy_path(tmp_path, repo)
        argv = [
            "--run-dir", str(run_dir), "--slice", "1", "--attempt", "0",
            "--policy", str(policy_path), "--out", str(out_path),
        ]

        assert dev_check.main(argv) == 0
        sheet = json.loads(out_path.read_text())
        original_provenance = sheet["attempts"][0]["provenance"]
        assert original_provenance["base_commit"] == head
        # task_id is stamped alongside the hash triple, naming the rubric.
        assert original_provenance["task_id"] == "fixture-task"
        assert set(original_provenance) >= {"plan_hash", "obligations_hash", "hidden_tests_hash"}
        assert original_provenance["hidden_tests_hash"] == dev_check.hidden_tests_manifest_hash(
            fake_bench_root, _FIXTURE_TASK_ENTRY, 1, hidden_files
        )

        # Change both files' bytes between grades.
        policy_path.write_text(policy_path.read_text() + "# changed\n", encoding="utf-8")
        obligations_path.write_text("slices: {}\n# changed\n", encoding="utf-8")

        assert dev_check.main(argv) == 0
        sheet_after = json.loads(out_path.read_text())
        assert sheet_after["attempts"][0]["provenance"] == original_provenance


# --- Production size and complexity ----------------------------------------


class TestLoadPolicyMeasurementValidation:
    _BASE = "backend: local\npm_scripts_dir: /x\nlint_script: /x\nhealth_script: /x\npython_interpreter: python3\nsubprocess_timeout_seconds: 600\n"

    def test_missing_measurement_section_fails_loudly(self, tmp_path: Path) -> None:
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text(self._BASE, encoding="utf-8")
        with pytest.raises(dev_check.DevCheckError, match="measurement"):
            dev_check.load_policy(policy_path)

    def test_missing_individual_measurement_key_fails_loudly_naming_it(self, tmp_path: Path) -> None:
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text(
            self._BASE + "measurement:\n  production_paths: ['src/**/*.py']\n  test_paths: ['tests/**/*.py']\n"
            "  doc_paths: ['docs/**/*.md']\n  loc_definition: net_physical_lines\n",
            encoding="utf-8",
        )
        with pytest.raises(dev_check.DevCheckError, match="metric_version"):
            dev_check.load_policy(policy_path)

    def test_top_level_path_buckets_are_no_longer_validated_here(self, tmp_path: Path) -> None:
        # The three layout globs moved to each task's own measurement sub-block
        # (multi-task-support Slice 2); their validation now lives in
        # bench_lib.resolve_task/_validate_task_entry (see tests/test_
        # bench_lib.py), so stray top-level copies of them neither help nor
        # fail load_policy anymore.
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text(
            self._BASE + "measurement:\n  production_paths: []\n  loc_definition: net_physical_lines\n"
            "  loc_category_definition: ast_tokenize_line_classification\n  metric_version: 1\n",
            encoding="utf-8",
        )
        assert isinstance(dev_check.load_policy(policy_path), dict)

    def test_unimplemented_loc_definition_fails_loudly(self, tmp_path: Path) -> None:
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text(
            self._BASE + "measurement:\n  production_paths: ['src/**/*.py']\n  test_paths: ['tests/**/*.py']\n"
            "  doc_paths: ['docs/**/*.md']\n  loc_definition: sloc_excluding_comments\n"
            "  loc_category_definition: ast_tokenize_line_classification\n  metric_version: 1\n",
            encoding="utf-8",
        )
        with pytest.raises(dev_check.DevCheckError, match="loc_definition"):
            dev_check.load_policy(policy_path)

    def test_unimplemented_loc_category_definition_fails_loudly(self, tmp_path: Path) -> None:
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text(
            self._BASE + "measurement:\n  production_paths: ['src/**/*.py']\n  test_paths: ['tests/**/*.py']\n"
            "  doc_paths: ['docs/**/*.md']\n  loc_definition: net_physical_lines\n"
            "  loc_category_definition: line_count_heuristic\n  metric_version: 1\n",
            encoding="utf-8",
        )
        with pytest.raises(dev_check.DevCheckError, match="loc_category_definition"):
            dev_check.load_policy(policy_path)

    def test_non_integer_metric_version_fails_loudly(self, tmp_path: Path) -> None:
        policy_path = tmp_path / "policy.yaml"
        policy_path.write_text(
            self._BASE + "measurement:\n  production_paths: ['src/**/*.py']\n  test_paths: ['tests/**/*.py']\n"
            "  doc_paths: ['docs/**/*.md']\n  loc_definition: net_physical_lines\n"
            "  loc_category_definition: ast_tokenize_line_classification\n  metric_version: '1'\n",
            encoding="utf-8",
        )
        with pytest.raises(dev_check.DevCheckError, match="metric_version"):
            dev_check.load_policy(policy_path)

    def test_the_repos_real_policy_yaml_measurement_section_loads(self) -> None:
        policy = dev_check.load_policy(REPO_ROOT / "policy.yaml")
        assert policy["measurement"]["loc_definition"] == "net_physical_lines"
        assert policy["measurement"]["loc_category_definition"] == "ast_tokenize_line_classification"
        assert policy["measurement"]["metric_version"] == 2


class TestClassifyPath:
    """Path classification is done in Python against policy.yaml's globs
    (never a git pathspec) -- these prove the hand-rolled glob translator
    handles the two cases neither `pathlib.PurePath.match` nor stdlib
    `fnmatch.translate` get right on this repo's Python version: a path
    living directly under the glob's own directory with NO intervening
    subdirectory ("**" matching zero directories, the standard glob
    meaning), and a bare `*.md` anchored to the top level only.
    """

    def test_nested_production_path_is_classified(self) -> None:
        assert dev_check.classify_path("src/a/b.py", _MEASUREMENT_POLICY) == "production"

    def test_production_path_directly_under_src_with_no_subdirectory_is_classified(self) -> None:
        # The crux case: relative-velocity's real production code lives
        # directly in src/ with no subdirectory at all -- "src/**/*.py" must
        # still match "src/merger_rate.py", not just a nested example.
        assert dev_check.classify_path("src/merger_rate.py", _MEASUREMENT_POLICY) == "production"

    def test_nested_test_path_is_classified(self) -> None:
        assert dev_check.classify_path("tests/sub/test_a.py", _MEASUREMENT_POLICY) == "test"

    def test_top_level_readme_is_a_doc(self) -> None:
        assert dev_check.classify_path("README.md", _MEASUREMENT_POLICY) == "doc"

    def test_nested_docs_markdown_is_a_doc(self) -> None:
        assert dev_check.classify_path("docs/x.md", _MEASUREMENT_POLICY) == "doc"

    def test_deeply_nested_docs_markdown_is_a_doc(self) -> None:
        assert dev_check.classify_path("docs/sub/deep/x.md", _MEASUREMENT_POLICY) == "doc"

    def test_unmatched_path_lands_in_its_own_unclassified_bucket(self) -> None:
        assert dev_check.classify_path("setup.sh", _MEASUREMENT_POLICY) == "unclassified"

    def test_glob_patterns_compile_once_and_are_cached(self) -> None:
        dev_check._compile_glob.cache_clear()
        dev_check.classify_path("src/a.py", _MEASUREMENT_POLICY)
        dev_check.classify_path("src/b.py", _MEASUREMENT_POLICY)
        info = dev_check._compile_glob.cache_info()
        assert info.hits >= 1


class TestParseNumstat:
    def test_additions_and_deletions_are_parsed(self) -> None:
        records = dev_check.parse_numstat("5\t2\tsrc/a.py\n")
        assert records == [{"path": "src/a.py", "added": 5, "deleted": 2, "binary": False}]

    def test_a_binary_files_line_is_recorded_without_a_zero_line_count(self) -> None:
        records = dev_check.parse_numstat("-\t-\tsrc/blob.bin\n")
        assert records == [{"path": "src/blob.bin", "added": None, "deleted": None, "binary": True}]

    def test_an_empty_diff_parses_to_no_records(self) -> None:
        assert dev_check.parse_numstat("") == []
        assert dev_check.parse_numstat("\n\n") == []

    def test_unparsable_line_fails_loudly(self) -> None:
        with pytest.raises(dev_check.DevCheckError, match="unparsable"):
            dev_check.parse_numstat("not-a-numstat-line\n")

    def test_a_rename_under_no_renames_is_two_plain_lines_not_the_arrow_syntax(self, tmp_path: Path) -> None:
        # --no-renames makes git decompose a rename into a full delete of the
        # old path plus a full add of the new one -- never the `old => new`
        # numstat syntax parse_numstat does not attempt to understand.
        repo = _make_repo(tmp_path)
        (repo / "src").mkdir()
        (repo / "src" / "old_name.py").write_text("line one\nline two\nline three\n", encoding="utf-8")
        after_add = _commit_all(repo, "add file")
        subprocess.run(
            ["git", "mv", "src/old_name.py", "src/new_name.py"], cwd=repo, check=True, capture_output=True
        )
        after_rename = _commit_all(repo, "rename file")

        raw = dev_check.run_git(repo, "diff", "--numstat", "--no-renames", after_add, after_rename)
        records = dev_check.parse_numstat(raw)
        paths = {r["path"] for r in records}
        assert paths == {"src/old_name.py", "src/new_name.py"}
        by_path = {r["path"]: r for r in records}
        assert by_path["src/old_name.py"]["deleted"] == 3
        assert by_path["src/old_name.py"]["added"] == 0
        assert by_path["src/new_name.py"]["added"] == 3
        assert by_path["src/new_name.py"]["deleted"] == 0


class TestComputeLocDelta:
    def test_production_test_and_doc_deltas_are_recorded_separately(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        before = _head(repo)
        (repo / "src").mkdir()
        (repo / "tests").mkdir()
        (repo / "docs").mkdir()
        (repo / "src" / "main.py").write_text("a\nb\nc\n", encoding="utf-8")
        (repo / "tests" / "test_main.py").write_text("x\ny\n", encoding="utf-8")
        (repo / "docs" / "notes.md").write_text("note one\n", encoding="utf-8")
        (repo / "setup.cfg").write_text("[metadata]\n", encoding="utf-8")
        after = _commit_all(repo, "add production/test/doc/unclassified files")

        loc = dev_check.compute_loc_delta(repo, before, after, _MEASUREMENT_POLICY)
        assert loc["available"] is True
        assert loc["buckets"]["production"]["added"] == 3
        assert loc["buckets"]["production"]["net"] == 3
        assert loc["buckets"]["test"]["added"] == 2
        assert loc["buckets"]["doc"]["added"] == 1
        assert loc["buckets"]["unclassified"]["added"] == 1
        assert loc["buckets"]["unclassified"]["files"] == ["setup.cfg"]
        # Test/doc deltas must never be folded into production's own net.
        assert loc["buckets"]["production"]["net"] != (
            loc["buckets"]["production"]["net"] + loc["buckets"]["test"]["net"] + loc["buckets"]["doc"]["net"]
        ) or loc["buckets"]["test"]["net"] == loc["buckets"]["doc"]["net"] == 0

    def test_a_binary_file_is_recorded_without_a_zero_line_count(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        before = _head(repo)
        (repo / "src").mkdir()
        # git classifies a file as binary by sniffing its content (a NUL
        # byte), not by extension -- a ".py" name with binary bytes still
        # falls in the production bucket by path, but numstat still reports
        # it "-"/"-".
        (repo / "src" / "blob.py").write_bytes(b"\x00\x01\x02binary\x00content")
        after = _commit_all(repo, "add a binary file under src/")

        loc = dev_check.compute_loc_delta(repo, before, after, _MEASUREMENT_POLICY)
        production = loc["buckets"]["production"]
        assert production["binary_files"] == ["src/blob.py"]
        # A binary file's unmeasurable line count must never silently read
        # as a clean (zero-line) addition.
        assert production["added"] == 0
        assert production["deleted"] == 0

    def test_an_empty_diff_between_identical_commits_has_no_changes(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        head = _head(repo)
        loc = dev_check.compute_loc_delta(repo, head, head, _MEASUREMENT_POLICY)
        for bucket in loc["buckets"].values():
            assert bucket["added"] == bucket["deleted"] == bucket["net"] == 0
            assert bucket["files"] == []


class TestClassifySourceLines:
    """`classify_source_lines`'s code/docstring/comment/blank precedence,
    one edge case per test per the implementation brief."""

    def _counts_sum_to_physical_lines(self, source: str) -> None:
        counts = dev_check.classify_source_lines(source)
        physical = source.count("\n") + (1 if source and not source.endswith("\n") else 0)
        assert sum(counts.values()) == physical

    def test_module_docstring_is_classified_as_docstring(self) -> None:
        source = '"""Module doc."""\nx = 1\n'
        counts = dev_check.classify_source_lines(source)
        assert counts == {"code": 1, "docstring": 1, "comment": 0, "blank": 0}
        self._counts_sum_to_physical_lines(source)

    def test_function_docstring_is_classified_as_docstring(self) -> None:
        source = "def f():\n    '''doc'''\n    return 1\n"
        counts = dev_check.classify_source_lines(source)
        assert counts["docstring"] == 1
        assert counts["code"] == 2  # def line + return line
        self._counts_sum_to_physical_lines(source)

    def test_string_expression_not_first_statement_is_code_not_docstring(self) -> None:
        source = "def f():\n    x = 1\n    'not a docstring'\n    return x\n"
        counts = dev_check.classify_source_lines(source)
        assert counts["docstring"] == 0
        assert counts["code"] == 4
        self._counts_sum_to_physical_lines(source)

    def test_multiline_string_sharing_a_docstring_line_keeps_its_interior_lines_as_code(self) -> None:
        # Regression: a docstring token was originally recognised by its
        # START LINE alone, so a non-docstring multi-line string opening on
        # that same physical line was skipped entirely and its interior
        # lines fell through to "blank". Recognition is by span containment
        # for exactly this reason -- see _within_a_docstring_span.
        source = 'def f():\n    """doc"""; x = """a\nb"""\n    return x\n'
        counts = dev_check.classify_source_lines(source)
        assert counts == {"code": 4, "docstring": 0, "comment": 0, "blank": 0}
        self._counts_sum_to_physical_lines(source)

    def test_implicitly_concatenated_docstring_stays_a_docstring(self) -> None:
        # One ast.Constant but two STRING tokens; span containment keeps
        # both inside the docstring rather than promoting them to code.
        source = 'def f():\n    """part one""" """part two"""\n    return 1\n'
        counts = dev_check.classify_source_lines(source)
        assert counts == {"code": 2, "docstring": 1, "comment": 0, "blank": 0}
        self._counts_sum_to_physical_lines(source)

    def test_multiline_non_docstring_string_constant_interior_lines_are_code(self) -> None:
        source = "x = (\n    'a'\n    'b'\n)\n"
        counts = dev_check.classify_source_lines(source)
        assert counts["blank"] == 0
        assert counts["code"] == 4
        self._counts_sum_to_physical_lines(source)

    def test_docstring_closing_quotes_followed_by_code_on_same_line_is_code(self) -> None:
        source = 'def f():\n    """doc"""; x = 1\n    return x\n'
        counts = dev_check.classify_source_lines(source)
        # The docstring's own line carries a statement after it, so code
        # wins on that line -- it must not also be counted as docstring.
        assert counts["docstring"] == 0
        assert counts["code"] == 3
        self._counts_sum_to_physical_lines(source)

    def test_trailing_comment_after_code_is_code_not_comment(self) -> None:
        source = "x = 1  # trailing comment\n"
        counts = dev_check.classify_source_lines(source)
        assert counts == {"code": 1, "docstring": 0, "comment": 0, "blank": 0}
        self._counts_sum_to_physical_lines(source)

    def test_decorator_line_is_code_even_though_def_lineno_is_the_docstring_anchor(self) -> None:
        source = "@staticmethod\ndef f():\n    '''doc'''\n    return 1\n"
        counts = dev_check.classify_source_lines(source)
        assert counts["code"] == 3  # decorator + def + return
        assert counts["docstring"] == 1
        self._counts_sum_to_physical_lines(source)

    def test_non_ascii_identifier_before_docstring_classifies_continuation_correctly(self) -> None:
        # ast col_offset is a UTF-8 BYTE offset, tokenize's column is a
        # character offset. "café" before the docstring on the same line
        # makes the two disagree by one (the two-byte "é") if compared
        # uncorrected -- which broke containment and misclassified the
        # docstring's own continuation line as code.
        source = 'def café(): """doc\nmore"""\n'
        counts = dev_check.classify_source_lines(source)
        assert counts == {"code": 1, "docstring": 1, "comment": 0, "blank": 0}
        self._counts_sum_to_physical_lines(source)

    def test_form_feed_does_not_shift_docstring_line_indexing(self) -> None:
        # str.splitlines() breaks on \f, \v and other Unicode line
        # boundaries that ast does not count as physical lines, so a form
        # feed (legal, and real in older Python source) shifted every
        # subsequent lineno and converted the wrong line's byte columns.
        source = '\fdef café():\n    """doc\n    more"""\n    return 1\n'
        counts = dev_check.classify_source_lines(source)
        assert counts == {"code": 2, "docstring": 2, "comment": 0, "blank": 0}
        self._counts_sum_to_physical_lines(source)

    def test_backslash_continuation_both_lines_are_code(self) -> None:
        source = "x = 1 + \\\n    2\n"
        counts = dev_check.classify_source_lines(source)
        assert counts["code"] == 2
        assert counts["blank"] == 0
        self._counts_sum_to_physical_lines(source)

    def test_comment_only_line_inside_parenthesised_expression_is_comment(self) -> None:
        source = "x = (\n    1 +\n    # a comment on its own line\n    2\n)\n"
        counts = dev_check.classify_source_lines(source)
        assert counts["comment"] == 1
        self._counts_sum_to_physical_lines(source)

    def test_consecutive_blank_lines_are_all_blank(self) -> None:
        source = "x = 1\n\n\n\ny = 2\n"
        counts = dev_check.classify_source_lines(source)
        assert counts["blank"] == 3
        assert counts["code"] == 2
        self._counts_sum_to_physical_lines(source)

    def test_file_ending_without_a_trailing_newline(self) -> None:
        source = "x = 1"
        counts = dev_check.classify_source_lines(source)
        assert counts["code"] == 1
        assert sum(counts.values()) == 1

    def test_empty_file_has_zero_lines_of_every_category(self) -> None:
        counts = dev_check.classify_source_lines("")
        assert counts == {"code": 0, "docstring": 0, "comment": 0, "blank": 0}

    def test_unparsable_source_raises_named_line_classification_error(self) -> None:
        with pytest.raises(dev_check.LineClassificationError, match="ast.parse"):
            dev_check.classify_source_lines("def f(:\n    pass\n")


class TestDecomposeProductionCategories:
    """Real-git integration: reading both revisions' blobs, the binary/
    unparsable availability rules, and the reconciliation invariant against
    compute_loc_delta's own numstat-derived net."""

    def test_available_result_reconciles_with_physical_net(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        before = _head(repo)
        (repo / "src").mkdir()
        (repo / "src" / "a.py").write_text(
            '"""Module doc."""\n\n\ndef f():\n    """f doc."""\n    # a comment\n    return 1\n',
            encoding="utf-8",
        )
        after = _commit_all(repo, "add src/a.py")

        loc = dev_check.compute_loc_delta(repo, before, after, _MEASUREMENT_POLICY)
        result = dev_check.decompose_production_categories(repo, before, after, loc)
        assert result["available"] is True
        assert result["definition"] == "ast_tokenize_line_classification"
        assert sum(result["net"].values()) == loc["buckets"]["production"]["net"]
        assert result["net"]["docstring"] == 2
        assert result["net"]["comment"] == 1

    def test_binary_production_file_makes_the_block_unavailable(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        before = _head(repo)
        (repo / "src").mkdir()
        (repo / "src" / "blob.py").write_bytes(b"\x00\x01binary")
        after = _commit_all(repo, "add a binary file under src/")

        loc = dev_check.compute_loc_delta(repo, before, after, _MEASUREMENT_POLICY)
        result = dev_check.decompose_production_categories(repo, before, after, loc)
        assert result["available"] is False
        assert "blob.py" in result["error"]

    def test_unparsable_production_file_makes_the_block_unavailable_not_a_hard_failure(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        before = _head(repo)
        (repo / "src").mkdir()
        (repo / "src" / "broken.py").write_text("def f(:\n    pass\n", encoding="utf-8")
        after = _commit_all(repo, "add syntactically broken production file")

        loc = dev_check.compute_loc_delta(repo, before, after, _MEASUREMENT_POLICY)
        # Must not raise: a Developer attempt can legitimately commit
        # syntactically broken code, and correctness/scope/complexity for
        # that attempt are still worth recording.
        result = dev_check.decompose_production_categories(repo, before, after, loc)
        assert result["available"] is False
        assert "broken.py" in result["error"]

    def test_a_deleted_production_file_contributes_only_its_baseline_side(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        (repo / "src").mkdir()
        (repo / "src" / "a.py").write_text("x = 1\ny = 2\n", encoding="utf-8")
        before = _commit_all(repo, "add src/a.py")
        (repo / "src" / "a.py").unlink()
        after = _commit_all(repo, "delete src/a.py")

        loc = dev_check.compute_loc_delta(repo, before, after, _MEASUREMENT_POLICY)
        result = dev_check.decompose_production_categories(repo, before, after, loc)
        assert result["available"] is True
        assert result["net"]["code"] == -2
        assert sum(result["net"].values()) == loc["buckets"]["production"]["net"]

    def test_an_added_empty_production_file_does_not_abort_decomposition(self, tmp_path: Path) -> None:
        # An empty added file has added == deleted == 0 in numstat --
        # the old "added > 0" gate wrongly treated this as an unexplained
        # missing blob and raised, rather than recognising (from
        # deleted == 0 alone) that the path simply did not exist at
        # baseline.
        repo = _make_repo(tmp_path)
        before = _head(repo)
        (repo / "src").mkdir()
        (repo / "src" / "empty.py").write_text("", encoding="utf-8")
        after = _commit_all(repo, "add an empty production file")

        loc = dev_check.compute_loc_delta(repo, before, after, _MEASUREMENT_POLICY)
        result = dev_check.decompose_production_categories(repo, before, after, loc)
        assert result["available"] is True
        assert result["net"] == {"code": 0, "docstring": 0, "comment": 0, "blank": 0}

    def test_no_production_files_in_the_diff_is_trivially_available(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        head = _head(repo)
        loc = dev_check.compute_loc_delta(repo, head, head, _MEASUREMENT_POLICY)
        result = dev_check.decompose_production_categories(repo, head, head, loc)
        assert result["available"] is True
        assert result["net"] == {"code": 0, "docstring": 0, "comment": 0, "blank": 0}


class TestComplexityDelta:
    """compute_complexity_delta / _extract_functions: ΔCC is derived from
    the FULL `facts.python.functions`/`facts.lizard.functions` inventory,
    never from the capped, display-only `candidates` list."""

    def _payload(self, python_functions: list[dict], lizard_functions: list[dict] | None = None, lizard_error: str | None = None) -> dict:
        return {
            "candidates": [],  # deliberately truncated/empty -- must never be read
            "facts": {
                "python": {"functions": python_functions},
                "lizard": {"functions": lizard_functions or [], "error": lizard_error},
            },
        }

    def test_production_and_test_totals_are_kept_separate(self) -> None:
        baseline = self._payload(
            [
                {"path": "src/a.py", "name": "f1", "line": 1, "cyclomatic": 3},
                {"path": "tests/test_a.py", "name": "test_f1", "line": 1, "cyclomatic": 2},
            ]
        )
        endpoint = self._payload(
            [
                {"path": "src/a.py", "name": "f1", "line": 1, "cyclomatic": 5},
                {"path": "tests/test_a.py", "name": "test_f1", "line": 1, "cyclomatic": 2},
            ]
        )
        delta = dev_check.compute_complexity_delta(baseline, endpoint, _MEASUREMENT_POLICY)
        assert delta["available"] is True
        assert delta["production"]["baseline_total"] == 3
        assert delta["production"]["endpoint_total"] == 5
        assert delta["production"]["net"] == 2
        assert delta["test"]["net"] == 0

    def test_a_removed_function_is_reflected_in_counts_not_silently_dropped(self) -> None:
        baseline = self._payload(
            [
                {"path": "src/a.py", "name": "f1", "line": 1, "cyclomatic": 3},
                {"path": "src/a.py", "name": "f2_removed", "line": 10, "cyclomatic": 4},
            ]
        )
        endpoint = self._payload([{"path": "src/a.py", "name": "f1", "line": 1, "cyclomatic": 3}])
        delta = dev_check.compute_complexity_delta(baseline, endpoint, _MEASUREMENT_POLICY)
        production = delta["production"]
        assert production["baseline_total"] == 7
        assert production["endpoint_total"] == 3
        assert production["net"] == -4
        assert production["function_count"] == {"baseline": 2, "endpoint": 1, "added": 0, "removed": 1}

    def test_lizard_error_is_recorded_as_a_named_coverage_note_not_a_silent_zero(self) -> None:
        baseline = self._payload([], lizard_error="lizard not installed")
        endpoint = self._payload([], lizard_error="lizard not installed")
        delta = dev_check.compute_complexity_delta(baseline, endpoint, _MEASUREMENT_POLICY)
        assert delta["available"] is True
        assert "lizard not installed" in delta["coverage_note"]

    def test_no_lizard_error_leaves_coverage_note_none(self) -> None:
        baseline = self._payload([])
        endpoint = self._payload([])
        delta = dev_check.compute_complexity_delta(baseline, endpoint, _MEASUREMENT_POLICY)
        assert delta["coverage_note"] is None

    def test_delta_ignores_the_capped_candidates_list_entirely(self) -> None:
        # `candidates` is capped at limit_per_family=5 and empty here on
        # purpose -- if compute_complexity_delta ever read it, this would
        # score 0 functions instead of the 6 the full `facts` list carries.
        many_functions = [
            {"path": "src/a.py", "name": f"f{i}", "line": i, "cyclomatic": 1} for i in range(6)
        ]
        payload = self._payload(many_functions)
        assert payload["candidates"] == []
        delta = dev_check.compute_complexity_delta(payload, payload, _MEASUREMENT_POLICY)
        assert delta["production"]["function_count"]["baseline"] == 6
        assert delta["production"]["baseline_total"] == 6

    def test_max_function_cyclomatic_is_recorded_at_both_ends(self) -> None:
        baseline = self._payload([{"path": "src/a.py", "name": "f1", "line": 1, "cyclomatic": 9}])
        endpoint = self._payload([{"path": "src/a.py", "name": "f1", "line": 1, "cyclomatic": 2}])
        delta = dev_check.compute_complexity_delta(baseline, endpoint, _MEASUREMENT_POLICY)
        assert delta["production"]["max_function_cyclomatic"] == {"baseline": 9, "endpoint": 2}


class TestRunCodeHealthAbsolute:
    def test_passes_all_and_json_never_require_coverage(self, tmp_path: Path) -> None:
        fake_health = tmp_path / "fake_health.py"
        fake_health.write_text(
            "import json, sys\nprint(json.dumps({'candidates': [], 'facts': {}, 'argv': sys.argv[1:]}))\n",
            encoding="utf-8",
        )
        policy = {"python_interpreter": sys.executable, "health_script": str(fake_health), "subprocess_timeout_seconds": 30}
        result = dev_check.run_code_health_absolute(tmp_path, policy)
        assert result["available"] is True
        assert "--all" in result["raw"]["argv"]
        assert "--require-coverage" not in result["raw"]["argv"]
        assert "--base" not in result["raw"]["argv"]

    def test_exit_3_without_require_coverage_is_unavailable_not_a_coverage_gap(self, tmp_path: Path) -> None:
        # Without --require-coverage, health.py never emits exit 3 on its
        # own -- but if a future health.py version (or a misconfigured
        # policy) somehow did, this invocation must treat it as a genuine
        # failure, unlike run_code_health's --require-coverage invocation.
        fake_health = tmp_path / "fake_health.py"
        fake_health.write_text("import sys\nsys.exit(3)\n", encoding="utf-8")
        policy = {"python_interpreter": sys.executable, "health_script": str(fake_health), "subprocess_timeout_seconds": 30}
        result = dev_check.run_code_health_absolute(tmp_path, policy)
        assert result["available"] is False

    def test_unavailable_health_script_is_recorded_as_unavailable(self, tmp_path: Path) -> None:
        policy = {
            "python_interpreter": sys.executable,
            "health_script": str(tmp_path / "does-not-exist.py"),
            "subprocess_timeout_seconds": 30,
        }
        result = dev_check.run_code_health_absolute(tmp_path, policy)
        assert result["available"] is False
        assert "error" in result


class TestRunCodeHealthVerdictIsHonest:
    def test_exit_0_verdict_is_measured_not_pass(self, tmp_path: Path) -> None:
        fake_health = tmp_path / "fake_health.py"
        fake_health.write_text("import json\nprint(json.dumps({'candidates': []}))\n", encoding="utf-8")
        policy = {"python_interpreter": sys.executable, "health_script": str(fake_health), "subprocess_timeout_seconds": 30}
        result = dev_check.run_code_health(tmp_path, "deadbeef", policy)
        assert result["verdict"] == "measured"
        assert result["verdict"] != "pass"


class TestBaselineComplexityCache:
    def test_second_call_with_the_same_repo_and_before_head_does_not_reinvoke_the_analyzer(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo = _make_repo(tmp_path)
        head = _head(repo)
        policy = {"grading_worktree_root": None}

        call_count = {"n": 0}

        def fake_run_code_health_absolute(worktree: Path, policy: dict) -> dict:
            call_count["n"] += 1
            return {"available": True, "raw": {"facts": {"python": {"functions": []}, "lizard": {"functions": [], "error": None}}}}

        monkeypatch.setattr(dev_check, "run_code_health_absolute", fake_run_code_health_absolute)

        first = dev_check._baseline_complexity_payload(repo, head, policy)
        second = dev_check._baseline_complexity_payload(repo, head, policy)
        assert call_count["n"] == 1
        assert first is second

    def test_a_different_before_head_is_not_served_from_the_others_cache_entry(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo = _make_repo(tmp_path)
        head_one = _head(repo)
        (repo / "src").mkdir()
        (repo / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
        head_two = _commit_all(repo, "second commit")
        policy = {"grading_worktree_root": None}

        call_count = {"n": 0}

        def fake_run_code_health_absolute(worktree: Path, policy: dict) -> dict:
            call_count["n"] += 1
            return {"available": True, "raw": {"facts": {}}}

        monkeypatch.setattr(dev_check, "run_code_health_absolute", fake_run_code_health_absolute)

        dev_check._baseline_complexity_payload(repo, head_one, policy)
        dev_check._baseline_complexity_payload(repo, head_two, policy)
        assert call_count["n"] == 2


class TestComputeSizeComplexity:
    def test_endpoint_unavailable_propagates_as_a_named_complexity_error(self, tmp_path: Path) -> None:
        repo = _make_repo(tmp_path)
        head = _head(repo)
        endpoint_payload = {"available": False, "error": "health.py exited 2: boom"}
        result = dev_check.compute_size_complexity(repo, head, head, endpoint_payload, {}, _MEASUREMENT_POLICY)
        assert result["complexity"]["available"] is False
        assert "endpoint" in result["complexity"]["error"]
        # ΔLOC has no dependency on the health tool at all -- it still
        # computes even though ΔCC could not.
        assert result["loc"]["available"] is True

    def test_baseline_unavailable_propagates_as_a_named_complexity_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo = _make_repo(tmp_path)
        head = _head(repo)
        endpoint_payload = {"available": True, "raw": {"facts": {}}}
        monkeypatch.setattr(
            dev_check, "_baseline_complexity_payload", lambda repo, before_head, policy: {"available": False, "error": "boom"}
        )
        result = dev_check.compute_size_complexity(repo, head, head, endpoint_payload, {}, _MEASUREMENT_POLICY)
        assert result["complexity"]["available"] is False
        assert "baseline" in result["complexity"]["error"]

    def test_shape_carries_metric_version_and_both_commits(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        repo = _make_repo(tmp_path)
        before = _head(repo)
        (repo / "src").mkdir()
        (repo / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
        commit = _commit_all(repo, "add file")
        endpoint_payload = {"available": True, "raw": {"facts": {"python": {"functions": []}, "lizard": {"functions": [], "error": None}}}}
        monkeypatch.setattr(
            dev_check,
            "_baseline_complexity_payload",
            lambda repo, before_head, policy: {"available": True, "raw": {"facts": {}}},
        )
        result = dev_check.compute_size_complexity(repo, before, commit, endpoint_payload, {}, _MEASUREMENT_POLICY)
        assert result["metric_version"] == 2
        assert result["baseline_commit"] == before
        assert result["endpoint_commit"] == commit
        assert result["complexity"]["available"] is True
