"""Tests for tools/bench_lib.py, the shared helpers factored out of dev_check.py
and review_score.py (docs/MODE2-REWRITE-PLAN.md §2 "minimum, no dead code";
AGENTS.md: prefer one parameterised implementation over two near-identical ones).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import bench_lib  # noqa: E402


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
    """finding 2: a restarted slice's next launch is another plain `launch`
    event (PM's own `attempts` counter resets, but the event log does not)."""
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


# --- active_judgments (Stage 1, docs/LEADERBOARD-REBUILD-PLAN.md) ----------


class TestActiveJudgments:
    def test_no_supersession_keeps_every_record(self) -> None:
        records = [{"judgment_id": "j1"}, {"judgment_id": "j2"}]
        assert bench_lib.active_judgments(records) == records

    def test_a_superseded_record_is_dropped(self) -> None:
        # Real shape, verified against trial 10 slice 1: developer-judgment-2
        # supersedes developer-judgment-1, both judging the same submission.
        j1 = {"judgment_id": "developer-judgment-1", "developer": {"tool": "opencode"}}
        j2 = {"judgment_id": "developer-judgment-2", "supersedes": "developer-judgment-1", "developer": {"tool": "opencode"}}
        assert bench_lib.active_judgments([j1, j2]) == [j2]

    def test_a_record_with_no_judgment_id_can_never_be_superseded(self) -> None:
        records = [{"note": "malformed, no judgment_id"}]
        assert bench_lib.active_judgments(records) == records

    def test_empty_list_stays_empty(self) -> None:
        assert bench_lib.active_judgments([]) == []


# --- resolve_developer_identity (Stage 1) -----------------------------------


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
        # Trial 9's real shape: harness and judgment agree on every field.
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
        # Trial 8's real shape: harness.effort is null, the judgment records "low".
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
        # Trials 10/11's real shape: harness.model is null, the judgment names it.
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
        # Trial 6's real shape: harness.model/effort are null, no judgments exist.
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
