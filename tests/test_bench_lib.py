"""Tests for tools/bench_lib.py, the shared helpers factored out of dev_check.py
and review_score.py (AGENTS.md: "minimum, no dead code"; prefer one
parameterised implementation over two near-identical ones).
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

import bench_lib
import cohort_run


def test_repo_root_resolves_this_repos_root() -> None:
    assert bench_lib.repo_root() == REPO_ROOT


def test_repo_root_is_pinned_to_this_module_not_the_callers_cwd(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)  # tmp_path is not a git repo at all
    assert bench_lib.repo_root() == REPO_ROOT


def test_repo_root_raises_benchliberror_not_calledprocesserror(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, returncode=128, stdout="", stderr="fatal: not a git repository")

    monkeypatch.setattr(bench_lib.subprocess, "run", fake_run)
    with pytest.raises(bench_lib.BenchLibError, match="not a git repo"):
        bench_lib.repo_root()


def test_read_events_missing_file_returns_empty_list_not_an_error(tmp_path: Path) -> None:
    assert bench_lib.read_events(tmp_path) == []


def test_read_events_reads_in_file_order(tmp_path: Path) -> None:
    (tmp_path / "events.jsonl").write_text(
        '{"kind": "launch"}\n{"kind": "floor"}\n\n{"kind": "accept"}\n', encoding="utf-8"
    )
    events = bench_lib.read_events(tmp_path)
    assert [e["kind"] for e in events] == ["launch", "floor", "accept"]


def test_read_events_corrupt_line_fails_loudly_naming_the_line(tmp_path: Path) -> None:
    (tmp_path / "events.jsonl").write_text('{"kind": "launch"}\nnot json\n', encoding="utf-8")
    with pytest.raises(bench_lib.BenchLibError, match="events.jsonl:2"):
        bench_lib.read_events(tmp_path)


def test_attempt_ordinal_counts_launch_family_events_for_the_slice() -> None:
    events = [
        {"kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
        {"kind": "floor", "slice": "Slice 1"},
        {"kind": "steer", "slice": "Slice 1"},
        {"kind": "floor", "slice": "Slice 1"},
        {"kind": "relaunch", "slice": "Slice 1"},
    ]
    assert bench_lib.attempt_ordinal(events, "Slice 1") == 2
    assert bench_lib.attempt_ordinal(events, "Slice 1", before_index=1) == 0
    assert bench_lib.attempt_ordinal(events, "Slice 1", before_index=3) == 1


def test_attempt_ordinal_survives_a_stop_then_restart_without_resetting() -> None:
    """A restarted slice's next launch is another plain `launch` event (PM's
    own `attempts` counter resets, but the event log does not)."""
    events = [
        {"kind": "launch", "slice": "Slice 1"},
        {"kind": "slice-stop", "slice": "Slice 1"},
        {"kind": "launch", "slice": "Slice 1"},  # restart -- still counted
    ]
    assert bench_lib.attempt_ordinal(events, "Slice 1") == 1


def test_attempt_ordinal_raises_when_no_launch_family_event_exists() -> None:
    with pytest.raises(bench_lib.BenchLibError, match="Slice 1"):
        bench_lib.attempt_ordinal([{"kind": "floor", "slice": "Slice 1"}], "Slice 1")


def test_epoch_start_ordinals_single_epoch_stays_at_zero() -> None:
    events = [
        {"kind": "launch", "slice": "Slice 1"},
        {"kind": "steer", "slice": "Slice 1"},
        {"kind": "steer", "slice": "Slice 1"},
    ]
    assert bench_lib.epoch_start_ordinals(events, "Slice 1") == [0, 0, 0]


def test_epoch_start_ordinals_resets_on_a_restart_launch_not_on_relaunch() -> None:
    # ordinal 0: launch (epoch start). ordinal 1: relaunch -- same epoch
    # (PM's own attempts counter increments, doesn't reset; relaunch only
    # follows a top-level `pm stop`, which preserves current_slice). ordinal
    # 2: a SECOND "launch" -- only reachable after a `finalize --stop`
    # cleared current_slice, so this is a genuine new epoch. ordinal 3:
    # steer, continuing that new epoch.
    events = [
        {"kind": "launch", "slice": "Slice 1"},
        {"kind": "relaunch", "slice": "Slice 1"},
        {"kind": "launch", "slice": "Slice 1"},
        {"kind": "steer", "slice": "Slice 1"},
    ]
    assert bench_lib.epoch_start_ordinals(events, "Slice 1") == [0, 0, 2, 2]


def test_epoch_start_ordinals_ignores_other_slices_and_non_launch_family_events() -> None:
    events = [
        {"kind": "launch", "slice": "Slice 1"},
        {"kind": "launch", "slice": "Slice 2"},
        {"kind": "floor", "slice": "Slice 1"},
        {"kind": "steer", "slice": "Slice 1"},
    ]
    assert bench_lib.epoch_start_ordinals(events, "Slice 1") == [0, 0]
    assert bench_lib.epoch_start_ordinals(events, "Slice 2") == [0]


def test_validate_sheet_identity_accepts_a_matching_sheet() -> None:
    bench_lib.validate_sheet_identity({"run_id": "r1", "slice": 1}, "r1", 1, Path("sheet.json"))


def test_validate_sheet_identity_rejects_a_foreign_run_or_slice() -> None:
    with pytest.raises(bench_lib.BenchLibError, match="run_id"):
        bench_lib.validate_sheet_identity({"run_id": "other", "slice": 1}, "r1", 1, Path("sheet.json"))
    with pytest.raises(bench_lib.BenchLibError, match="slice"):
        bench_lib.validate_sheet_identity({"run_id": "r1", "slice": 2}, "r1", 1, Path("sheet.json"))


def test_write_json_atomically_round_trips(tmp_path: Path) -> None:
    out_path = tmp_path / "nested" / "sheet.json"
    bench_lib.write_json_atomically(out_path, {"a": 1, "b": [1, 2, 3]})
    assert out_path.is_file()
    assert json.loads(out_path.read_text(encoding="utf-8")) == {"a": 1, "b": [1, 2, 3]}
    # No leftover temp file.
    assert list(out_path.parent.glob(".bench-lib-*")) == []


def test_write_text_atomically_round_trips(tmp_path: Path) -> None:
    out_path = tmp_path / "nested" / "report.md"
    bench_lib.write_text_atomically(out_path, "# Title\n\nbody\n", suffix=".md.tmp")
    assert out_path.is_file()
    assert out_path.read_text(encoding="utf-8") == "# Title\n\nbody\n"
    assert list(out_path.parent.glob(".bench-lib-*")) == []


def test_report_problems_returns_0_and_prints_nothing_when_empty(capsys: pytest.CaptureFixture[str]) -> None:
    assert bench_lib.report_problems("tool", []) == 0
    assert capsys.readouterr().err == ""


def test_report_problems_prints_count_and_each_problem_and_returns_1(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = bench_lib.report_problems("tool", ["first", "second"], kind="widget(s)")
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "tool: 2 widget(s) occurred:" in captured.err
    assert "  - first" in captured.err
    assert "  - second" in captured.err


# --- active_judgments -------------------------------------------------------


class TestActiveJudgments:
    def test_no_supersession_keeps_every_record(self) -> None:
        records = [{"judgment_id": "j1"}, {"judgment_id": "j2"}]
        assert bench_lib.active_judgments(records) == records

    def test_a_superseded_record_is_dropped(self) -> None:
        # developer-judgment-2 supersedes developer-judgment-1; both judge
        # the same submission.
        j1 = {"judgment_id": "developer-judgment-1", "developer": {"tool": "opencode"}}
        j2 = {"judgment_id": "developer-judgment-2", "supersedes": "developer-judgment-1", "developer": {"tool": "opencode"}}
        assert bench_lib.active_judgments([j1, j2]) == [j2]

    def test_a_record_with_no_judgment_id_can_never_be_superseded(self) -> None:
        records = [{"note": "malformed, no judgment_id"}]
        assert bench_lib.active_judgments(records) == records

    def test_empty_list_stays_empty(self) -> None:
        assert bench_lib.active_judgments([]) == []


# --- resolve_developer_identity ----------------------------------------------


class TestResolveDeveloperIdentity:
    def _judgment(self, tool: str | None, model: str | None, effort: str | None, *, judgment_id: str = "developer-judgment-1", supersedes: str | None = None) -> dict:
        record = {
            "judgment_id": judgment_id,
            "developer": {"tool": tool, "model": model, "effort": effort},
        }
        if supersedes:
            record["supersedes"] = supersedes
        return record

    def _slice(self, developer_judgments: list[dict] | None = None) -> dict:
        return {"id": "Slice 1", "developer_judgments": developer_judgments or []}

    def test_both_structural_sources_agreeing_resolves_cleanly(self) -> None:
        # harness and judgment agree on every field.
        run_state = {
            "harness": {"name": "claude", "model": "claude-haiku-4-5", "effort": "low", "command_override": None},
            "slices": [self._slice([self._judgment("claude", "claude-haiku-4-5", "low")])],
        }
        block, problems = bench_lib.resolve_developer_identity(run_state, run_id="r1", corrections={})
        assert problems == []
        assert block == {
            "harness": "claude",
            "model": "claude-haiku-4-5",
            "effort": "low",
            "configuration_key": "claude-haiku-4-5 · claude · low",
            "sources": {"harness": "pm_developer_judgment", "model": "pm_developer_judgment", "effort": "pm_developer_judgment"},
            "attributed": True,
            "attestation": None,
        }

    def test_judgment_fills_a_null_harness_effort_field(self) -> None:
        # harness.effort is null; the judgment records "low".
        run_state = {
            "harness": {"name": "claude", "model": "claude-haiku-4-5", "effort": None, "command_override": None},
            "slices": [self._slice([self._judgment("claude", "claude-haiku-4-5", "low")])],
        }
        block, problems = bench_lib.resolve_developer_identity(run_state, run_id="r1", corrections={})
        assert problems == []
        assert block["effort"] == "low"
        assert block["sources"]["effort"] == "pm_developer_judgment"
        assert block["attributed"] is True

    def test_judgment_fills_a_null_harness_model_field(self) -> None:
        # harness.model is null; the judgment names it.
        run_state = {
            "harness": {"name": "opencode", "model": None, "effort": None, "command_override": None},
            "slices": [self._slice([self._judgment("opencode", "github-copilot/gpt-5.6-luna", None)])],
        }
        block, problems = bench_lib.resolve_developer_identity(run_state, run_id="r1", corrections={})
        assert problems == []
        assert block["model"] == "github-copilot/gpt-5.6-luna"
        assert block["sources"]["model"] == "pm_developer_judgment"
        assert block["attributed"] is True

    def test_two_non_null_differing_values_is_a_named_error(self) -> None:
        run_state = {
            "harness": {"name": "claude", "model": "model-a", "effort": None, "command_override": None},
            "slices": [self._slice([self._judgment("claude", "model-b", None)])],
        }
        block, problems = bench_lib.resolve_developer_identity(run_state, run_id="r1", corrections={})
        assert len(problems) == 1
        assert "developer.model conflict" in problems[0]
        assert "model-a" in problems[0] and "model-b" in problems[0]
        assert block["model"] is None
        assert block["attributed"] is False  # model could not be resolved

    def test_no_source_at_all_is_unattributed_not_an_error(self) -> None:
        run_state = {"harness": {"name": None, "model": None, "effort": None, "command_override": None}, "slices": []}
        block, problems = bench_lib.resolve_developer_identity(run_state, run_id="r1", corrections={})
        assert problems == []
        assert block["attributed"] is False
        assert block["harness"] is None and block["model"] is None

    def test_attestation_fills_a_gap_neither_structural_source_recorded(self) -> None:
        # harness.model/effort are null and no judgments exist.
        run_state = {"harness": {"name": "opencode", "model": None, "effort": None, "command_override": None}, "slices": []}
        corrections = {"r1": {"harness": "opencode", "model": "github-copilot/mai-code-1.1-flash", "effort": None}}
        block, problems = bench_lib.resolve_developer_identity(run_state, run_id="r1", corrections=corrections)
        assert problems == []
        assert block["model"] == "github-copilot/mai-code-1.1-flash"
        assert block["sources"]["model"] == "operator_attestation"
        assert block["attributed"] is True
        assert block["attestation"] == corrections["r1"]

    def test_attestation_conflicting_with_a_recorded_value_is_a_named_error(self) -> None:
        run_state = {"harness": {"name": "opencode", "model": "recorded-model", "effort": None, "command_override": None}, "slices": []}
        corrections = {"r1": {"harness": "opencode", "model": "attested-different-model", "effort": None}}
        block, problems = bench_lib.resolve_developer_identity(run_state, run_id="r1", corrections=corrections)
        assert len(problems) == 1
        assert "developer.model conflict" in problems[0]
        assert block["model"] is None
        # An attestation that was never actually usable (it conflicted) must
        # not be recorded as if it had been applied.
        assert block["attestation"] is None

    def test_command_override_set_and_unattested_resolves_unattributed(self) -> None:
        # pm_lib deliberately nulls model/effort for a custom command --
        # an honest unknown, not a gap this function should paper over.
        run_state = {
            "harness": {"name": "custom", "model": None, "effort": None, "command_override": "./run-my-agent.sh"},
            "slices": [],
        }
        block, problems = bench_lib.resolve_developer_identity(run_state, run_id="r1", corrections={})
        assert problems == []
        assert block["attributed"] is False

    def test_a_superseded_developer_judgment_is_ignored(self) -> None:
        stale = self._judgment("opencode", "stale-model", None, judgment_id="developer-judgment-1")
        current = self._judgment(
            "opencode", "current-model", None, judgment_id="developer-judgment-2", supersedes="developer-judgment-1"
        )
        run_state = {
            "harness": {"name": "opencode", "model": None, "effort": None, "command_override": None},
            "slices": [self._slice([stale, current])],
        }
        block, problems = bench_lib.resolve_developer_identity(run_state, run_id="r1", corrections={})
        assert problems == []
        assert block["model"] == "current-model"

    def test_effort_unknown_is_kept_distinct_from_effort_low(self) -> None:
        run_state_unknown = {
            "harness": {"name": "opencode", "model": "m", "effort": None, "command_override": None},
            "slices": [],
        }
        run_state_low = {
            "harness": {"name": "opencode", "model": "m", "effort": "low", "command_override": None},
            "slices": [],
        }
        block_unknown, _ = bench_lib.resolve_developer_identity(run_state_unknown, run_id="r1", corrections={})
        block_low, _ = bench_lib.resolve_developer_identity(run_state_low, run_id="r1", corrections={})
        assert block_unknown["configuration_key"] != block_low["configuration_key"]
        assert "effort unknown" in block_unknown["configuration_key"]
        assert "low" in block_low["configuration_key"]

    def test_no_corrections_entry_for_this_run_id_is_fine(self) -> None:
        run_state = {"harness": {"name": "claude", "model": "m", "effort": "low", "command_override": None}, "slices": []}
        block, problems = bench_lib.resolve_developer_identity(
            run_state, run_id="r1", corrections={"some-other-run": {"model": "x"}}
        )
        assert problems == []
        assert block["attributed"] is True

    def test_a_non_mapping_correction_is_a_named_error(self) -> None:
        # policy.yaml is hand-edited, so a correction written as a bare
        # string (or any non-mapping) is a realistic operator typo -- it
        # must name the run and what was found, never escape as a bare
        # AttributeError from the field lookup.
        run_state = {"harness": {"name": "opencode", "model": None, "effort": None}, "slices": []}
        for malformed in ("opencode", ["opencode"], 42):
            with pytest.raises(bench_lib.BenchLibError, match=r"identity\.corrections\['r1'\] must be a mapping"):
                bench_lib.resolve_developer_identity(run_state, run_id="r1", corrections={"r1": malformed})

    def test_a_non_string_correction_field_is_a_named_error(self) -> None:
        run_state = {"harness": {"name": "opencode", "model": None, "effort": None}, "slices": []}
        with pytest.raises(bench_lib.BenchLibError, match=r"identity\.corrections\['r1'\]\.model must be a string or null"):
            bench_lib.resolve_developer_identity(run_state, run_id="r1", corrections={"r1": {"model": 7}})


# --- parse_pinned_plan_commit (relocated from tools/cohort_run.py) -----------


class TestParsePinnedPlanCommit:
    """The relocated tests, re-pointed at bench_lib.parse_pinned_plan_commit
    and asserting its own BenchLibError type rather than CohortRunError."""

    def test_extracts_the_hash(self, tmp_path: Path) -> None:
        provenance = tmp_path / "provenance.md"
        provenance.write_text("Pinned commit: `043b13adc264689c376bdd337603e94d5447623a` (\"a message\")\n", encoding="utf-8")
        assert bench_lib.parse_pinned_plan_commit(provenance) == "043b13adc264689c376bdd337603e94d5447623a"

    def test_missing_file_is_a_named_error(self, tmp_path: Path) -> None:
        with pytest.raises(bench_lib.BenchLibError, match="not found"):
            bench_lib.parse_pinned_plan_commit(tmp_path / "does-not-exist.md")

    def test_missing_pinned_commit_line_is_a_named_error(self, tmp_path: Path) -> None:
        provenance = tmp_path / "provenance.md"
        provenance.write_text("No pinned commit line here.\n", encoding="utf-8")
        with pytest.raises(bench_lib.BenchLibError, match="Pinned commit"):
            bench_lib.parse_pinned_plan_commit(provenance)

    def test_cohort_run_keeps_no_second_copy(self) -> None:
        # The relocation exists precisely so dev_check.py can share this logic
        # without a circular import on cohort_run.py; a second copy drifting
        # back into that module would silently reintroduce the divergence risk
        # the move removes.
        assert not hasattr(cohort_run, "parse_pinned_plan_commit")


# --- resolve_task -------------------------------------------------------------


def _real_policy() -> dict[str, Any]:
    return yaml.safe_load((REPO_ROOT / "policy.yaml").read_text(encoding="utf-8"))


def _task_policy(**overrides: Any) -> dict[str, Any]:
    """A minimal valid single-task policy for error-path tests -- fresh dicts
    on every call, so mutating one never leaks into another test."""
    entry = {
        "repo": "substrate/some-repo",
        "branch_prefix": "prefix",
        "worktree_root": None,
        "plan_file": "docs/PLAN.md",
        "provenance_file": "docs/PLAN.provenance.md",
        "hidden_tests_dir": "hidden_tests",
        "obligations_file": "hidden_tests/obligations.yaml",
        "expected_slices": 2,
        "measurement": {
            "production_paths": ["src/**/*.py"],
            "test_paths": ["tests/**/*.py"],
            "doc_paths": ["*.md"],
        },
    }
    entry.update(overrides)
    return {"default_task": "t1", "tasks": {"t1": entry}}


class TestResolveTask:
    def test_none_resolves_to_default_task_entry(self) -> None:
        task = bench_lib.resolve_task(_real_policy(), None)
        assert task["task_id"] == "relative-velocity"

    def test_explicit_task_id_resolves_that_entry(self) -> None:
        task = bench_lib.resolve_task(_real_policy(), "relative-velocity")
        assert task["task_id"] == "relative-velocity"

    def test_unknown_task_id_names_it_and_the_configured_ids(self) -> None:
        with pytest.raises(bench_lib.BenchLibError) as excinfo:
            bench_lib.resolve_task(_real_policy(), "does-not-exist")
        message = str(excinfo.value)
        assert "'does-not-exist'" in message
        assert "relative-velocity" in message

    def test_non_string_task_id_is_a_named_error(self) -> None:
        with pytest.raises(bench_lib.BenchLibError, match="task_id must be a non-empty string or None"):
            bench_lib.resolve_task(_real_policy(), 42)

    @pytest.mark.parametrize("bad_key", [2, True, ""])
    def test_non_string_or_empty_tasks_key_is_a_named_error_not_a_raw_typeerror(self, bad_key: Any) -> None:
        # YAML parses an unquoted numeric/boolean-looking key as int/bool, so
        # a hand-edited policy can carry non-string task ids; resolution must
        # refuse that loudly rather than crash inside sorted()/join() on some
        # later message path with a bare TypeError.
        policy = _task_policy()
        policy["tasks"][bad_key] = dict(policy["tasks"]["t1"])
        with pytest.raises(bench_lib.BenchLibError, match="keyed by non-empty task-id strings"):
            bench_lib.resolve_task(policy, "does-not-exist")

    def test_explicit_valid_task_id_still_refused_when_default_task_points_nowhere(self) -> None:
        # Distinct from the fallback-path test below: here the requested task
        # IS configured and valid, yet default_task points nowhere -- the
        # documented contract refuses the broken policy file anyway.
        policy = _task_policy()
        policy["default_task"] = "ghost"
        with pytest.raises(bench_lib.BenchLibError) as excinfo:
            bench_lib.resolve_task(policy, "t1")
        message = str(excinfo.value)
        assert "'ghost'" in message
        assert "default_task" in message

    def test_relative_velocity_entry_reproduces_todays_flat_keys_and_constants(self) -> None:
        policy = _real_policy()
        task = bench_lib.resolve_task(policy, "relative-velocity")
        # The exact values today's hardcoded constants and flat keys carry --
        # asserted literally, so a silent edit to either side fails here.
        assert set(task) == {
            "task_id",
            "repo",
            "branch_prefix",
            "worktree_root",
            "plan_file",
            "provenance_file",
            "hidden_tests_dir",
            "obligations_file",
            "expected_slices",
            "measurement",
        }
        assert task["repo"] == "substrate/relative-velocity"
        assert task["branch_prefix"] == "pm-eval-v2"
        assert task["worktree_root"] is None
        assert task["plan_file"] == "docs/MERGER_RATE_PLAN-2SLICE.md"
        assert task["provenance_file"] == "docs/MERGER_RATE_PLAN-2SLICE.provenance.md"
        assert task["hidden_tests_dir"] == "hidden_tests"
        assert task["obligations_file"] == "hidden_tests/obligations.yaml"
        assert task["expected_slices"] == 2
        assert task["measurement"]["production_paths"] == ["src/**/*.py"]
        assert task["measurement"]["test_paths"] == ["tests/**/*.py"]
        assert task["measurement"]["doc_paths"] == ["docs/**/*.md", "*.md"]
        # ...and equal to the one still-present flat key, so the two blocks
        # cannot drift apart while they coexist during migration (the other
        # three flat keys were deleted by Slice 4, their last reader).
        assert task["expected_slices"] == policy["leaderboard"]["expected_slices"]

    def test_mutating_the_result_never_touches_the_callers_policy_mapping(self) -> None:
        # The returned dict is deep-copied: a caller mutating it (top level
        # or the nested measurement sub-block) must never rewrite the shared
        # parsed policy object it was resolved from.
        policy = _task_policy()
        task = bench_lib.resolve_task(policy, "t1")
        task["repo"] = "mutated"
        task["measurement"]["production_paths"].append("mutated/**")
        assert policy["tasks"]["t1"]["repo"] == "substrate/some-repo"
        assert policy["tasks"]["t1"]["measurement"]["production_paths"] == ["src/**/*.py"]

    def test_missing_required_key_is_a_named_error_naming_task_and_key(self) -> None:
        policy = _task_policy()
        del policy["tasks"]["t1"]["plan_file"]
        with pytest.raises(bench_lib.BenchLibError) as excinfo:
            bench_lib.resolve_task(policy, "t1")
        message = str(excinfo.value)
        assert "'t1'" in message
        assert "plan_file" in message

    @pytest.mark.parametrize(
        ("key", "bad_value"),
        [
            ("repo", None),
            ("branch_prefix", ""),
            ("worktree_root", 0),
            ("expected_slices", "two"),
            ("expected_slices", True),
            ("measurement", "not-a-mapping"),
        ],
    )
    def test_wrong_typed_key_is_a_named_error_naming_task_and_key(self, key: str, bad_value: Any) -> None:
        policy = _task_policy(**{key: bad_value})
        with pytest.raises(bench_lib.BenchLibError) as excinfo:
            bench_lib.resolve_task(policy, "t1")
        message = str(excinfo.value)
        assert "'t1'" in message
        assert key in message

    def test_empty_glob_bucket_is_a_named_error_naming_task_and_bucket(self) -> None:
        policy = _task_policy(measurement={"production_paths": [], "test_paths": ["t"], "doc_paths": ["d"]})
        with pytest.raises(bench_lib.BenchLibError) as excinfo:
            bench_lib.resolve_task(policy, "t1")
        message = str(excinfo.value)
        assert "'t1'" in message
        assert "measurement.production_paths" in message

    def test_missing_tasks_section_is_a_named_error(self) -> None:
        with pytest.raises(bench_lib.BenchLibError, match="'tasks' mapping"):
            bench_lib.resolve_task({}, None)

    def test_malformed_default_task_is_a_named_error_even_with_an_explicit_id(self) -> None:
        for bad_default in (None, 42, ""):
            policy = _task_policy()
            policy["default_task"] = bad_default
            with pytest.raises(bench_lib.BenchLibError, match="default_task"):
                bench_lib.resolve_task(policy, "t1")

    def test_default_task_pointing_at_an_unconfigured_entry_fails_when_used_as_fallback(self) -> None:
        policy = _task_policy()
        policy["default_task"] = "ghost"
        with pytest.raises(bench_lib.BenchLibError) as excinfo:
            bench_lib.resolve_task(policy, None)
        assert "'ghost'" in str(excinfo.value)

    def test_non_mapping_entry_is_a_named_error(self) -> None:
        policy = _task_policy()
        policy["tasks"]["t1"] = "not-a-mapping"
        with pytest.raises(bench_lib.BenchLibError) as excinfo:
            bench_lib.resolve_task(policy, "t1")
        message = str(excinfo.value)
        assert "'t1'" in message
        assert "entry must be a mapping" in message


# --- repo_belongs_to_task -----------------------------------------------------


class TestRepoBelongsToTask:
    """Verified against real git repos carrying registered worktrees -- never
    by path-string comparison alone."""

    @pytest.fixture()
    def substrate_with_worktree(self, tmp_path: Path) -> tuple[Path, Path]:
        """A throwaway git repo plus one registered linked worktree of it."""
        repo = tmp_path / "substrate"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
        (repo / "README.md").write_text("x\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "initial"], cwd=repo, check=True)
        worktree = tmp_path / "substrate-trial-1"
        subprocess.run(["git", "-C", str(repo), "worktree", "add", "--detach", str(worktree)], check=True)
        return repo, worktree

    def test_configured_path_itself_belongs(self, substrate_with_worktree: tuple[Path, Path]) -> None:
        repo, _worktree = substrate_with_worktree
        assert bench_lib.repo_belongs_to_task(repo, repo) is True

    def test_registered_worktree_of_the_configured_repo_belongs(self, substrate_with_worktree: tuple[Path, Path]) -> None:
        repo, worktree = substrate_with_worktree
        assert bench_lib.repo_belongs_to_task(worktree, repo) is True

    def test_unrelated_path_does_not_belong(self, substrate_with_worktree: tuple[Path, Path], tmp_path: Path) -> None:
        repo, _worktree = substrate_with_worktree
        unrelated = tmp_path / "unrelated"
        unrelated.mkdir()
        assert bench_lib.repo_belongs_to_task(unrelated, repo) is False

    def test_worktree_of_a_different_repo_does_not_belong(
        self, substrate_with_worktree: tuple[Path, Path], tmp_path: Path
    ) -> None:
        _repo, worktree = substrate_with_worktree
        other = tmp_path / "other-repo"
        other.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=other, check=True)
        assert bench_lib.repo_belongs_to_task(worktree, other) is False

    def test_git_failure_on_the_configured_side_is_loud_not_silent_false(
        self, substrate_with_worktree: tuple[Path, Path], tmp_path: Path
    ) -> None:
        # Membership cannot be determined structurally when the configured side
        # isn't a usable git repository; guessing False here would silently
        # misattribute runs.
        _repo, worktree = substrate_with_worktree
        not_a_repo = tmp_path / "not-a-repo"
        not_a_repo.mkdir()
        with pytest.raises(bench_lib.BenchLibError, match="worktree list"):
            bench_lib.repo_belongs_to_task(worktree, not_a_repo)

    def test_configured_plain_subdirectory_of_a_repo_is_refused_as_a_different_repository(
        self, substrate_with_worktree: tuple[Path, Path]
    ) -> None:
        # A plain subdirectory of some repo makes git enumerate THAT repo's
        # worktrees (discovery walks up to the enclosing .git); answering
        # membership from that foreign enumeration would be a silent guess, so
        # the guard refuses loudly instead of returning False. Deterministic
        # regardless of where tmp_path itself lives, because the fixture repo
        # carries its own .git and discovery stops there.
        repo, worktree = substrate_with_worktree
        plain_subdir = repo / "plain-subdir"
        plain_subdir.mkdir()
        with pytest.raises(bench_lib.BenchLibError, match="different repository"):
            bench_lib.repo_belongs_to_task(worktree, plain_subdir)
