"""Tests for tools/review_score.py (Tools 2/3: harvest a reviewer report into the scoring sheet).

Fixtures are hand-written per test: a synthetic `run.json`, `events.jsonl`, one or
more Markdown reports, and a pre-existing scoring sheet, all under `tmp_path`.
Nothing here asserts the implementation back at itself — each test encodes a
requirement from docs/MODE2-REWRITE-PLAN.md §6/§7 independently of how
review_score.py happens to be written.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import review_score as rs  # noqa: E402

DRIFT_REPORT_TEMPLATE = """\
## Authorization Gate
- Intended slice: Slice 1
- Authorized surface: calc.py
- Actual changed surface: calc.py
- Verdict: {verdict}

## Drift Findings
{findings}

## Behaviour Added
- none

## Behaviour Removed
- none

## Missing Tests
- none

## New Coupling
- none

## Contract Defects
- none

## Non-Goals Check
- Preserved: no global state added
- Violated: none

## Next Action
- proceed to code-review
"""

CODE_REVIEW_REPORT_TEMPLATE = """\
## Authorization Status
- Drift audit verdict: PASS WITH RISKS

## Findings
{findings}

## Contract Defects
- none

## Open Questions / Assumptions
- none

## Coverage Summary
- Scope reviewed: calc.py
- Requirements checked against: plan slice 1
- Dimensions checked: correctness, tests
- Validation run / not run: pytest run

## Verdict
- {verdict}
"""


def _write(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _events_jsonl(path: Path, events: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")


def _base_sheet(attempts: list[dict]) -> dict:
    return {
        "run_id": "20260101T000000Z-abc123",
        "model": "test/model",
        "slice": 1,
        "run_status": {"pm_status": "active", "slice_status": None, "stop_reason": None,
                        "infrastructure_failure_suspected": False},
        "attempts": attempts,
        "accepted_at_attempt": None,
        "provenance": {"plan_hash": "x", "policy_hash": "y", "base_commit": "z", "pm_skill_version": "1"},
    }


def _attempt_entry(n: int) -> dict:
    return {
        "attempt": n,
        "commit_sha": f"deadbeef{n}",
        "timestamp": "2026-01-01T00:00:00Z",
        "correctness": {"hidden_tests_passed": 40 + n, "hidden_tests_total": 46, "by_obligation": {}},
        "quality": {"lint_findings_by_tool": {"cli-tool-name": 0}, "code_health_findings_by_category": {}},
        "scope": {"violations": []},
        "pm_decision": "steer",
    }


def _run_state(slice_reviews: list[dict]) -> dict:
    return {
        "run_id": "20260101T000000Z-abc123",
        "slices": [{"id": "Slice 1", "title": "t", "status": None, "reviews": slice_reviews}],
    }


def _review_state_entry(skill: str, artifact: str, sha256: str, **overrides) -> dict:
    entry = {
        "skill": skill,
        "tool": "codex",
        "model": "gpt-x",
        "head": "abc123",
        "before_head": "abc000",
        "artifact": artifact,
        "sha256": sha256,
        "at": "2026-01-01T00:00:01Z",
        "grants_seen": 0,
    }
    entry.update(overrides)
    return entry


def test_sha256_mismatch_fails_loudly_and_parses_nothing(tmp_path):
    run_dir = tmp_path / "run"
    report_path = tmp_path / "report.md"
    _write(report_path, DRIFT_REPORT_TEMPLATE.format(verdict="PASS", findings="- none"))

    _events_jsonl(run_dir / "events.jsonl", [
        {"ts": "t0", "kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
        {"ts": "t1", "kind": "review", "slice": "Slice 1", "note": "drift-audit via codex", "evidence": str(report_path)},
    ])
    run_state = _run_state([_review_state_entry("drift-audit", str(report_path), "0" * 64)])
    (run_dir / "run.json").write_text(json.dumps(run_state), encoding="utf-8")

    sheet_path = tmp_path / "sheet.json"
    sheet_path.write_text(json.dumps(_base_sheet([_attempt_entry(0)])), encoding="utf-8")

    with pytest.raises(rs.ReviewScoreError) as excinfo:
        rs.run_review_score(run_dir, 1, "drift-audit", sheet_path)

    message = str(excinfo.value)
    assert "0" * 64 in message  # the (wrong) recorded hash
    assert str(report_path) in message
    assert "sha256 mismatch" in message

    # The sheet must be untouched: no drift_review field was written.
    sheet_after = json.loads(sheet_path.read_text())
    assert "drift_review" not in sheet_after["attempts"][0]


# --- A3: a timed-out review must not block harvesting an earlier one ------


def test_a3_timeout_review_event_is_not_selected_as_latest(tmp_path):
    """PM's reviewer-timeout path (pm_lib.review) appends a `review` event with
    the same "<skill> via <tool>" note prefix as a successful commission, but
    no `evidence` field at all. Before A3, matching on the note prefix alone
    picked the timeout as "latest" and this tool then died on the missing
    evidence -- permanently blocking a harvest of the earlier, real review."""
    events = [
        {"kind": "review", "slice": "Slice 1", "note": "drift-audit via codex", "evidence": "report0.md"},
        {
            "kind": "review",
            "slice": "Slice 1",
            "note": "drift-audit via codex timed out after 900s; reviewer process group killed",
            # No 'evidence' key at all -- see pm_lib.review's timeout path.
        },
    ]
    index, event = rs.find_latest_review_event(events, "Slice 1", "drift-audit")
    assert index == 0
    assert event["evidence"] == "report0.md"


def test_a3_only_timeout_events_present_fails_loudly_naming_evidence(tmp_path):
    events = [
        {"kind": "review", "slice": "Slice 1", "note": "drift-audit via codex timed out after 900s; reviewer process group killed"},
    ]
    with pytest.raises(rs.ReviewScoreError, match="evidence"):
        rs.find_latest_review_event(events, "Slice 1", "drift-audit")


# --- A4: repo_root_from_git pins cwd and fails loudly, not via a raw --------
# --- CalledProcessError -----------------------------------------------------


def test_a4_repo_root_from_git_is_pinned_to_this_files_location_not_cwd(tmp_path, monkeypatch):
    # tmp_path is not a git repo at all; if repo_root_from_git used the bare
    # caller's cwd (the original bug) this would fail here. Pinned to
    # bench_lib.py's own directory, it must still resolve this repo's root.
    monkeypatch.chdir(tmp_path)
    root = rs.repo_root_from_git()
    assert (root / "tools" / "review_score.py").is_file()


def test_a4_not_a_git_repo_raises_reviewscoreerror_not_calledprocesserror(monkeypatch):
    def fake_run(*args, **kwargs):
        import subprocess as _subprocess

        return _subprocess.CompletedProcess(args, returncode=128, stdout="", stderr="fatal: not a git repository")

    monkeypatch.setattr(rs.bench_lib.subprocess, "run", fake_run)
    with pytest.raises(rs.ReviewScoreError, match="not a git repo"):
        rs.repo_root_from_git()


# --- C5: find_run_review_entry looks a slice up by id, not by position -----


def test_c5_find_run_review_entry_looks_up_by_id_not_position():
    # Slice 2 appears first in run.json's slices list -- a positional lookup
    # of slices[0] for "Slice 1" (slice_num - 1 == 0) would silently read
    # Slice 2's reviews instead.
    run_state = {
        "slices": [
            {"id": "Slice 2", "reviews": [{"skill": "drift-audit", "artifact": "wrong.md", "sha256": "aaa"}]},
            {"id": "Slice 1", "reviews": [{"skill": "drift-audit", "artifact": "right.md", "sha256": "bbb"}]},
        ]
    }
    entry = rs.find_run_review_entry(run_state, "Slice 1", "drift-audit", "right.md")
    assert entry["artifact"] == "right.md"
    assert entry["sha256"] == "bbb"


def test_c5_unknown_slice_id_fails_loudly(tmp_path):
    run_state = {"slices": [{"id": "Slice 1", "reviews": []}]}
    with pytest.raises(rs.ReviewScoreError, match="Slice 2"):
        rs.find_run_review_entry(run_state, "Slice 2", "drift-audit", "r.md")


def test_attempt_attribution_across_launch_steer_relaunch(tmp_path):
    events = [
        {"ts": "t0", "kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
        {"ts": "t1", "kind": "review", "slice": "Slice 1", "note": "drift-audit via codex", "evidence": "r0.md"},
        {"ts": "t2", "kind": "steer", "slice": "Slice 1", "note": "fix this"},
        {"ts": "t3", "kind": "review", "slice": "Slice 1", "note": "drift-audit via codex", "evidence": "r1.md"},
        {"ts": "t4", "kind": "relaunch", "slice": "Slice 1", "note": "attempt 2"},
        {"ts": "t5", "kind": "review", "slice": "Slice 1", "note": "drift-audit via codex", "evidence": "r2.md"},
    ]
    assert rs.compute_attempt_number(events, "Slice 1", 1) == 0  # after 1 launch
    assert rs.compute_attempt_number(events, "Slice 1", 3) == 1  # after launch + steer
    assert rs.compute_attempt_number(events, "Slice 1", 5) == 2  # after launch + steer + relaunch


def test_drift_audit_report_parses_verdict_and_none_sections_score_zero(tmp_path):
    text = DRIFT_REPORT_TEMPLATE.format(
        verdict="PASS WITH RISKS",
        findings="1. [P2] `calc.py:42` Unauthorized helper added\n   Adds a helper not in the frozen surface.",
    )
    parsed = rs.parse_report("drift-audit", text)
    assert "parse_error" not in parsed
    assert parsed["verdict"] == "PASS WITH RISKS"
    assert len(parsed["findings"]) == 1
    finding = parsed["findings"][0]
    assert finding == {"severity": "P2", "file": "calc.py", "line": 42, "title": "Unauthorized helper added"}
    # "- none" sections score 0; Non-Goals Check has two real bullets.
    assert parsed["sections"]["Behaviour Added"] == 0
    assert parsed["sections"]["Missing Tests"] == 0
    assert parsed["sections"]["Non-Goals Check"] == 2


def test_code_review_report_parses_severities_and_verdict(tmp_path):
    findings = "\n".join([
        "1. [P1] `calc.py:10` Missing input validation",
        "   Could crash on malformed input.",
        "2. [P3] `calc.py:20` Minor naming nit",
        "   Purely cosmetic.",
    ])
    text = CODE_REVIEW_REPORT_TEMPLATE.format(verdict="PASS WITH RISKS", findings=findings)
    parsed = rs.parse_report("code-review", text)
    assert "parse_error" not in parsed
    assert parsed["verdict"] == "PASS WITH RISKS"
    counts = rs.findings_by_severity(parsed["findings"])
    assert counts == {"P0": 0, "P1": 1, "P2": 0, "P3": 1}


def test_unparseable_report_records_explicit_parse_error_not_zero_findings(tmp_path):
    # Missing the '## Verdict' section entirely -> must fail loudly, not silently pass.
    broken = CODE_REVIEW_REPORT_TEMPLATE.replace("## Verdict\n- {verdict}\n", "")
    text = broken.format(findings="- none")
    parsed = rs.parse_report("code-review", text)
    assert "parse_error" in parsed
    assert "findings" not in parsed
    assert "verdict" not in parsed

    record = rs.build_record(
        skill="code-review", tool="codex", model="m", head="h", grants_seen=0, at="t",
        report_ref="ref", parsed=parsed,
    )
    # A parse error must never be confusable with "reviewer found nothing".
    assert "findings_by_severity" not in record
    assert "findings" not in record
    assert record["parse_error"]


def test_open_after_this_attempt_null_then_backfilled_with_severity_change(tmp_path):
    sheet = _base_sheet([_attempt_entry(0), _attempt_entry(1)])

    finding_attempt0 = {"severity": "P1", "file": "calc.py", "line": 10, "title": "Missing input validation"}
    finding_attempt1_same = {"severity": "P2", "file": "calc.py", "line": 10, "title": "Missing input validation"}
    finding_attempt1_new = {"severity": "P1", "file": "calc.py", "line": 30, "title": "New unrelated issue"}

    record0 = rs.build_record(
        skill="code-review", tool="codex", model="m", head="h0", grants_seen=0, at="t0",
        report_ref="r0.md", parsed={"verdict": "PASS WITH RISKS", "findings": [finding_attempt0], "sections": {}},
    )
    rs.upsert_sheet(sheet, "code_review", 0, record0)
    assert sheet["attempts"][0]["code_review"]["open_after_this_attempt"] is None

    record1 = rs.build_record(
        skill="code-review", tool="codex", model="m", head="h1", grants_seen=0, at="t1",
        report_ref="r1.md",
        parsed={
            "verdict": "PASS",
            "findings": [finding_attempt1_same, finding_attempt1_new],
            "sections": {},
        },
    )
    rs.upsert_sheet(sheet, "code_review", 1, record1)

    # Attempt 0's finding recurred (severity changed, identity did not) -> backfilled to 1.
    assert sheet["attempts"][0]["code_review"]["open_after_this_attempt"] == 1
    # Attempt 1 has no successor yet -> still null.
    assert sheet["attempts"][1]["code_review"]["open_after_this_attempt"] is None


def test_upsert_preserves_other_attempts_and_tool1_fields(tmp_path):
    sheet = _base_sheet([_attempt_entry(0), _attempt_entry(1)])
    before = json.loads(json.dumps(sheet))  # deep copy for comparison

    record = rs.build_record(
        skill="drift-audit", tool="codex", model="m", head="h", grants_seen=0, at="t",
        report_ref="r.md", parsed={"verdict": "PASS", "findings": [], "sections": {"Behaviour Added": 0}},
    )
    rs.upsert_sheet(sheet, "drift_review", 0, record)

    # Attempt 1 (untouched) is byte-for-byte identical.
    assert sheet["attempts"][1] == before["attempts"][1]
    # Attempt 0's Tool 1 fields are preserved exactly.
    for key in ("correctness", "quality", "scope", "commit_sha", "timestamp", "pm_decision"):
        assert sheet["attempts"][0][key] == before["attempts"][0][key]
    assert sheet["attempts"][0]["drift_review"] == record


def test_upsert_missing_attempt_entry_is_a_loud_failure(tmp_path):
    sheet = _base_sheet([_attempt_entry(0)])
    record = rs.build_record(
        skill="drift-audit", tool="codex", model="m", head="h", grants_seen=0, at="t",
        report_ref="r.md", parsed={"verdict": "PASS", "findings": [], "sections": {}},
    )
    with pytest.raises(rs.ReviewScoreError, match="attempt 5"):
        rs.upsert_sheet(sheet, "drift_review", 5, record)


def _full_fixture(tmp_path: Path):
    """A complete run_dir + report + sheet fixture for one drift-audit review at attempt 0."""
    run_dir = tmp_path / "run"
    report_path = tmp_path / "reports" / "review-drift-audit-codex.md"
    text = DRIFT_REPORT_TEMPLATE.format(
        verdict="PASS",
        findings="1. [P2] `calc.py:5` Some finding",
    )
    sha = _write(report_path, text)

    _events_jsonl(run_dir / "events.jsonl", [
        {"ts": "t0", "kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
        {"ts": "t1", "kind": "review", "slice": "Slice 1", "note": "drift-audit via codex", "evidence": str(report_path)},
    ])
    run_state = _run_state([_review_state_entry("drift-audit", str(report_path), sha)])
    (run_dir / "run.json").write_text(json.dumps(run_state), encoding="utf-8")

    sheet_path = tmp_path / "sheet.json"
    sheet_path.write_text(json.dumps(_base_sheet([_attempt_entry(0)])), encoding="utf-8")
    return run_dir, sheet_path


def test_rerun_on_same_review_is_idempotent(tmp_path):
    run_dir, sheet_path = _full_fixture(tmp_path)

    rs.run_review_score(run_dir, 1, "drift-audit", sheet_path)
    first = json.loads(sheet_path.read_text())

    rs.run_review_score(run_dir, 1, "drift-audit", sheet_path)
    second = json.loads(sheet_path.read_text())

    assert first == second


def test_end_to_end_writes_expected_record(tmp_path):
    run_dir, sheet_path = _full_fixture(tmp_path)
    rs.run_review_score(run_dir, 1, "drift-audit", sheet_path)

    sheet = json.loads(sheet_path.read_text())
    record = sheet["attempts"][0]["drift_review"]
    assert record["commissioned"] is True
    assert record["skill"] == "drift-audit"
    assert record["tool"] == "codex"
    # C2: sha256_verified was a constant that could only ever be True (a
    # mismatch raises before build_record is ever reached) -- removed.
    assert "sha256_verified" not in record
    assert record["verdict"] == "PASS"
    assert record["findings_by_severity"] == {"P0": 0, "P1": 0, "P2": 1, "P3": 0}
    assert record["open_after_this_attempt"] is None


def test_a_run_with_no_events_yet_fails_loudly_rather_than_finding_nothing(tmp_path: Path) -> None:
    """The shared read_events() tolerates a missing log; this caller must not.

    bench_lib.read_events() returns [] for a run whose first event has not
    landed, which is right for dev_check (an unstarted run simply has no
    decision to report). A review harvest against zero events is never
    meaningful, so this tool has to reject it itself -- otherwise the
    tolerant contract would surface here as a confusing "no review event
    found" for a run that was never searched at all.
    """
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "run.json").write_text(json.dumps(_run_state([])), encoding="utf-8")
    # No events.jsonl written at all.

    sheet_path = tmp_path / "sheet.json"
    sheet_path.write_text(json.dumps(_base_sheet([_attempt_entry(0)])), encoding="utf-8")

    with pytest.raises(rs.ReviewScoreError, match="no events found"):
        rs.run_review_score(run_dir, 1, "drift-audit", sheet_path)
