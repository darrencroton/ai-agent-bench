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
