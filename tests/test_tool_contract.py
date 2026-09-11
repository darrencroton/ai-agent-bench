"""Contract tests for the scoring sheet shared by Tool 1 and Tools 2/3.

`dev_check.py` creates and updates a slice's cumulative scoring sheet;
`review_score.py` later writes review fields onto attempts inside the same
file. Each tool's own test module exercises its half in isolation, which
cannot catch the failure that matters most here: one tool silently discarding
what the other wrote. These tests drive both tools' real sheet functions
against one shared document, in the order a real run produces them.

Run with plain pytest from the repo root.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import dev_check  # noqa: E402
import review_score  # noqa: E402

RUN_ID = "20260911T090000Z-ab12cd"
SLICE = 1


def _attempt_entry(attempt: int) -> dict:
    """A minimal Tool 1 attempt entry, shaped like the real one."""
    return {
        "attempt": attempt,
        "commit_sha": f"{attempt:040d}",
        "timestamp": "2026-09-11T09:00:00Z",
        "correctness": {"hidden_tests_passed": 40 + attempt, "hidden_tests_total": 44, "by_obligation": {}},
        "quality": {"lint_findings_by_tool": {}, "code_health_findings_by_category": {}},
        "scope": {"violations": []},
        "pm_decision": "steer",
    }


def _upsert_tool1(sheet: dict | None, attempt: int) -> dict:
    return dev_check.upsert_attempt(
        sheet,
        run_id=RUN_ID,
        model="opencode-go/mimo-v2.5-pro",
        slice_number=SLICE,
        run_status={
            "pm_status": "active",
            "slice_status": None,
            "stop_reason": None,
            "infrastructure_failure_suspected": False,
        },
        attempt_entry=_attempt_entry(attempt),
        accepted_at_attempt=None,
        pm_model_performance_ref=None,
    )


def _review_record(findings: list[dict]) -> dict:
    return {
        "commissioned": True,
        "report_ref": "/tmp/review-1-code-review-codex.md",
        "skill": "code-review",
        "verdict": "PASS WITH RISKS",
        "findings_by_severity": {"P0": 0, "P1": len(findings), "P2": 0, "P3": 0},
        "findings": findings,
        "open_after_this_attempt": None,
    }


def test_review_upsert_preserves_tool1_measurements():
    sheet = _upsert_tool1(None, 0)
    review_score.upsert_sheet(sheet, "code_review", 0, _review_record([]))

    entry = sheet["attempts"][0]
    assert entry["correctness"]["hidden_tests_passed"] == 40
    assert entry["scope"] == {"violations": []}
    assert entry["code_review"]["verdict"] == "PASS WITH RISKS"


def test_tool1_regrade_preserves_a_review_already_recorded():
    """A re-graded attempt keeps its review fields.

    The driver can legitimately call Tool 1 again for an attempt that has
    already been reviewed -- a re-run after a transient failure, say. Losing
    the review there would be invisible in the sheet.
    """
    sheet = _upsert_tool1(None, 0)
    review_score.upsert_sheet(sheet, "code_review", 0, _review_record([]))
    review_score.upsert_sheet(sheet, "drift_review", 0, _review_record([]))

    sheet = _upsert_tool1(sheet, 0)

    entry = sheet["attempts"][0]
    assert entry["code_review"]["skill"] == "code-review"
    assert entry["drift_review"]["skill"] == "code-review"
    assert entry["correctness"]["hidden_tests_passed"] == 40


def test_a_later_attempt_backfills_the_earlier_one_across_both_tools():
    """The carry-over count survives the interleaving a real run produces.

    Real order is Tool 1 on attempt 0, Tool 2/3 on attempt 0, Tool 1 on
    attempt 1, Tool 2/3 on attempt 1 -- and only that last call can know
    whether attempt 0's findings were ever fixed.
    """
    carried = {"severity": "P1", "file": "src/calc.py", "line": 12, "title": "Unvalidated bin edge"}
    fixed = {"severity": "P2", "file": "src/calc.py", "line": 40, "title": "Missing docstring"}

    sheet = _upsert_tool1(None, 0)
    review_score.upsert_sheet(sheet, "code_review", 0, _review_record([carried, fixed]))
    assert sheet["attempts"][0]["code_review"]["open_after_this_attempt"] is None

    sheet = _upsert_tool1(sheet, 1)
    # Severity changed between attempts; identity is (file, title), so this is
    # still the same finding, still open.
    review_score.upsert_sheet(sheet, "code_review", 1, _review_record([{**carried, "severity": "P2"}]))

    assert sheet["attempts"][0]["code_review"]["open_after_this_attempt"] == 1
    assert len(sheet["attempts"]) == 2


def test_a_sheet_written_by_tool1_round_trips_as_json():
    """Tool 2/3 reads what Tool 1 wrote off disk, not in memory."""
    sheet = _upsert_tool1(None, 0)
    serialised = json.loads(json.dumps(sheet))
    review_score.upsert_sheet(serialised, "code_review", 0, _review_record([]))
    assert serialised["attempts"][0]["code_review"]["commissioned"] is True


def test_review_for_an_ungraded_attempt_fails_loudly():
    """Tool 1 runs first by design; a missing entry is an error, not a stub."""
    sheet = _upsert_tool1(None, 0)
    with pytest.raises(review_score.ReviewScoreError, match="attempt 2"):
        review_score.upsert_sheet(sheet, "code_review", 2, _review_record([]))


def test_stop_then_restart_keeps_both_attempt_rows_and_both_tools_agree_on_the_key():
    """finding 2: pm_lib.slice_ops.start_slice resets run.json's own
    `attempts` counter to 0 whenever a stopped slice is relaunched (a
    non-relaunch `start-slice` after `finalize --stop` cleared
    `current_slice`), even though the slice already has an attempt-0 row. The
    event log has no such reset: the restarted slice's next launch is still
    just another `launch` event for the same slice id (not a `relaunch`,
    since PM's own state has no live `current_slice` to relaunch), so the
    key both tools derive from it -- bench_lib.attempt_ordinal -- keeps
    counting up rather than repeating 0. This drives dev_check.py's and
    review_score.py's real key derivations (resolve_attempt/
    compute_attempt_number) against one synthetic event log spanning exactly
    that sequence: launch -> floor -> slice-stop -> (human review) ->
    launch (restart, PM's own counter back to 0) -> floor -> review -> accept.
    """
    events = [
        {"kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
        {"kind": "floor", "slice": "Slice 1", "note": "6/7"},
        {"kind": "slice-stop", "slice": "Slice 1", "note": "floor fact 5 failed"},
        # Human review happens between these two events; nothing in the log
        # marks it, but PM's own `attempts` counter is back to 0 by the time
        # the next launch event lands (verified directly against
        # pm_lib.slice_ops.start_slice's non-relaunch branch).
        {"kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
        {"kind": "floor", "slice": "Slice 1", "note": "7/7"},
        {"kind": "review", "slice": "Slice 1", "note": "code-review via codex", "evidence": "/tmp/r.md"},
        {"kind": "accept", "slice": "Slice 1", "note": "accepted"},
    ]

    # Tool 1 grades the pre-stop attempt (key 0) and the post-restart attempt
    # (key 1) -- both are real, distinct keys, never the same one twice.
    assert dev_check.resolve_attempt(events[:1], "Slice 1", None) == 0
    assert dev_check.resolve_attempt(events, "Slice 1", None) == 1

    sheet = _upsert_tool1(None, 0)
    sheet = _upsert_tool1(sheet, 1)
    assert [a["attempt"] for a in sheet["attempts"]] == [0, 1]

    # Tool 2/3 attributes the review event (index 5) to the same key Tool 1
    # used for the post-restart attempt -- computed independently, from the
    # same event log, and it agrees by construction.
    review_index, _ = review_score.find_review_events(events, "Slice 1", "code-review")[-1]
    review_attempt = review_score.compute_attempt_number(events, "Slice 1", review_index)
    assert review_attempt == 1
    review_score.upsert_sheet(sheet, "code_review", review_attempt, _review_record([]))

    # Neither row was lost or overwritten: attempt 0's row is exactly what
    # Tool 1 wrote for it, untouched by the restart or the later review.
    assert sheet["attempts"][0] == _attempt_entry(0)
    assert sheet["attempts"][1]["code_review"]["skill"] == "code-review"
