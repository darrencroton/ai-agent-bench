"""Tests for tools/review_score.py (Tools 2/3: harvest a reviewer report into the scoring sheet).

Fixtures are hand-written per test: a synthetic `run.json`, `events.jsonl`, one or
more Markdown reports, and a pre-existing scoring sheet, all under `tmp_path`.
Nothing here asserts the implementation back at itself — each test encodes a
requirement from docs/MODE2-REWRITE-PLAN.md §7/§6 and
docs/LEADERBOARD-REBUILD-PLAN.md Stage 4a independently of how review_score.py
happens to be written.

Finding-shape and verdict fixtures below are copied verbatim (or, where noted,
lightly adapted to fit the drift-audit report template) from the real
reviewer reports named in docs/LEADERBOARD-REBUILD-PLAN.md Stage 4a's Part 2 —
never read from `substrate/` at test time, per AGENTS.md's read-only-against-PM
boundary and the plan's own "build a fixture from its real shape" instruction.
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

# The real trial 11 slice 1 drift-audit attempt-1 non-report, verbatim
# (docs/LEADERBOARD-REBUILD-PLAN.md Stage 4a's own fixture instruction: "The
# first (review-1) is a one-line non-report"). No section headers at all, so
# it must fail with a missing-required-sections error, never a zero-findings
# pass.
TRIAL11_ONE_LINE_NON_REPORT = (
    "I need permission to read the pinned diff file. Requesting access to continue with the drift audit."
)


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
        "effort": None,
        "head": "abc123",
        "before_head": "abc000",
        "artifact": artifact,
        "sha256": sha256,
        "at": "2026-01-01T00:00:01Z",
        "grants_seen": 0,
        "review_id": None,
    }
    entry.update(overrides)
    return entry


def _make_record(
    *,
    event_index: int,
    skill: str = "code-review",
    tool: str | None = "codex",
    model: str | None = "m",
    effort: str | None = None,
    head: str | None = "h",
    before_head: str | None = "bh",
    grants_seen: int | None = 0,
    at: str | None = "t",
    report_ref: str = "r.md",
    report_sha256: str = "sha",
    review_id: str | None = None,
    parsed: dict,
) -> dict:
    """A `build_record` call with sensible test defaults for every field a
    real `run.json` reviews[] entry carries -- keeps the tests below focused
    on what each one is actually exercising."""
    return rs.build_record(
        review_id=review_id,
        event_index=event_index,
        skill=skill,
        tool=tool,
        model=model,
        effort=effort,
        head=head,
        before_head=before_head,
        grants_seen=grants_seen,
        at=at,
        report_ref=report_ref,
        report_sha256=report_sha256,
        parsed=parsed,
    )


def _reviews_for(attempt_entry: dict) -> list[dict]:
    return attempt_entry.get("reviews") or []


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

    # The sheet must be untouched: no reviews were ever written.
    sheet_after = json.loads(sheet_path.read_text())
    assert _reviews_for(sheet_after["attempts"][0]) == []


# --- A3: a timed-out review must not block harvesting an earlier one ------


def test_a3_timeout_review_event_is_excluded_from_harvest(tmp_path):
    """PM's reviewer-timeout path (pm_lib.review) appends a `review` event with
    the same "<skill> via <tool>" note prefix as a successful commission, but
    no `evidence` field at all. Before A3, matching on the note prefix alone
    picked up the timeout as harvestable and this tool then died on the
    missing evidence -- permanently blocking a harvest of the earlier, real
    review."""
    events = [
        {"kind": "review", "slice": "Slice 1", "note": "drift-audit via codex", "evidence": "report0.md"},
        {
            "kind": "review",
            "slice": "Slice 1",
            "note": "drift-audit via codex timed out after 900s; reviewer process group killed",
            # No 'evidence' key at all -- see pm_lib.review's timeout path.
        },
    ]
    matches = rs.find_review_events(events, "Slice 1", "drift-audit")
    assert matches == [(0, events[0])]


def test_a3_only_timeout_events_present_fails_loudly_naming_evidence(tmp_path):
    events = [
        {"kind": "review", "slice": "Slice 1", "note": "drift-audit via codex timed out after 900s; reviewer process group killed"},
    ]
    with pytest.raises(rs.ReviewScoreError, match="evidence"):
        rs.find_review_events(events, "Slice 1", "drift-audit")


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

    record = _make_record(event_index=0, skill="code-review", parsed=parsed)
    # A parse error must never be confusable with "reviewer found nothing".
    assert "findings_by_severity" not in record
    assert "findings" not in record
    assert record["parse_error"]
    assert record["superseded_by"] is None


def test_trial11_one_line_non_report_stays_a_named_parse_error() -> None:
    """The real trial 11 slice 1 drift-audit attempt-1 review-1 report: a
    single sentence, no section headers at all. This is a genuine reliability
    outcome (the reviewer never produced a report), not something a parser
    fix should paper over -- it must still be a named, missing-sections
    error, never a zero-findings pass (docs/LEADERBOARD-REBUILD-PLAN.md
    Stage 4a, Part 2)."""
    parsed = rs.parse_report("drift-audit", TRIAL11_ONE_LINE_NON_REPORT)
    assert "parse_error" in parsed
    assert "missing required section(s)" in parsed["parse_error"]
    assert "Authorization Gate" in parsed["parse_error"]


# --- Finding-line shapes (docs/LEADERBOARD-REBUILD-PLAN.md Stage 4a, Part 2) -


def _drift_findings(finding_lines: str) -> list[dict]:
    text = DRIFT_REPORT_TEMPLATE.format(verdict="PASS", findings=finding_lines)
    parsed = rs.parse_report("drift-audit", text)
    assert "parse_error" not in parsed, parsed.get("parse_error")
    return parsed["findings"]


def test_shape1_location_after_title_is_recovered_but_title_keeps_full_text():
    """Real line (trial 6 slice 1 review-1): severity first, a path-shaped
    location later in the sentence, no bold at all. Today's parser rejects
    this outright; the fix must record the location AND keep the full
    sentence as the title (the asymmetry the brief requires -- there is no
    pre-existing title to preserve, so the least lossy choice wins)."""
    findings = _drift_findings("1. [P2] Missing required vector-redshift preflight test at `tests/test_merger_rate.py:249-283`")
    assert len(findings) == 1
    finding = findings[0]
    assert finding["severity"] == "P2"
    assert finding["file"] == "tests/test_merger_rate.py:249-283"
    assert finding["line"] is None  # a range, not a single line -- today's rsplit(":", 1) semantics, unchanged
    assert finding["title"] == "Missing required vector-redshift preflight test at `tests/test_merger_rate.py:249-283`"


def test_shape1_non_path_backtick_mid_title_is_never_mistaken_for_a_location():
    """Real line (trial 4 slice 1 review-1): the only backticked span is an
    attribute name (`redshift`), not a path -- it must never become a
    location, and the title keeps it verbatim."""
    findings = _drift_findings(
        "2. [P1] Preflight accepts a length-one vector `redshift` attribute despite the scalar-shape requirement"
    )
    assert len(findings) == 1
    finding = findings[0]
    assert finding["severity"] == "P1"
    assert finding["file"] is None
    assert finding["line"] is None
    assert finding["title"] == (
        "Preflight accepts a length-one vector `redshift` attribute despite the scalar-shape requirement"
    )


def test_shape1_no_backtick_at_all_has_no_location():
    """Real line (trial 8 slice 2 review-1, trailing-whitespace and all)."""
    findings = _drift_findings("1. [P1] End-to-end acceptance test does not assert scientific validation success  ")
    assert len(findings) == 1
    finding = findings[0]
    assert finding["file"] is None
    assert finding["line"] is None
    assert finding["title"] == "End-to-end acceptance test does not assert scientific validation success"


def test_shape2_bold_wraps_whole_finding_no_location_at_all():
    """Real line (trial 5 slice 1 review-2, adapted into a code-review
    findings list): bold wraps the entire finding, no backtick anywhere."""
    text = CODE_REVIEW_REPORT_TEMPLATE.format(
        verdict="PASS WITH RISKS",
        findings="1. **[P1] Fractional counts are incorrectly accepted by tolerant integer checks**",
    )
    parsed = rs.parse_report("code-review", text)
    assert "parse_error" not in parsed, parsed.get("parse_error")
    finding = parsed["findings"][0]
    assert finding["severity"] == "P1"
    assert finding["file"] is None
    assert finding["line"] is None
    assert finding["title"] == "Fractional counts are incorrectly accepted by tolerant integer checks"


def test_shape2_bold_wraps_whole_finding_leading_path_shaped_location_is_consumed():
    """Real line (trial 6 slice 1 review-2): bold wraps everything, but the
    leading backtick span right after the severity IS path-shaped -- treated
    exactly like today's leading-location shape, just inside the bold."""
    text = CODE_REVIEW_REPORT_TEMPLATE.format(
        verdict="PASS WITH RISKS",
        findings="1. **[P2] `src/merger_rate.py:41-47` silently truncates non-integer galaxy counts**",
    )
    parsed = rs.parse_report("code-review", text)
    assert "parse_error" not in parsed, parsed.get("parse_error")
    finding = parsed["findings"][0]
    assert finding["file"] == "src/merger_rate.py:41-47"
    assert finding["line"] is None
    assert finding["title"] == "silently truncates non-integer galaxy counts"


def test_shape2_bold_wraps_whole_finding_leading_function_name_is_not_a_location():
    """Real line (trial 9 slice 1 review-7, adapted): the leading backtick
    span is a function name, `_load_pair_counts()` -- never path-shaped -- and
    a second span, `box_size_mpc`, is an attribute name, also never
    path-shaped. Neither becomes a location; the title keeps both verbatim."""
    text = CODE_REVIEW_REPORT_TEMPLATE.format(
        verdict="PASS WITH RISKS",
        findings=(
            "2. **[P2] `_load_pair_counts()` does not reliably reject non-scalar `box_size_mpc` "
            "attrs with the required assertion**"
        ),
    )
    parsed = rs.parse_report("code-review", text)
    assert "parse_error" not in parsed, parsed.get("parse_error")
    finding = parsed["findings"][0]
    assert finding["file"] is None
    assert finding["line"] is None
    assert finding["title"] == (
        "`_load_pair_counts()` does not reliably reject non-scalar `box_size_mpc` attrs with the required assertion"
    )


def test_shape2_bold_wraps_whole_finding_leading_path_with_line_number():
    """Real line (trial 9 slice 1 review-7): a leading path-shaped span with
    a single line number (no range) -- `location.rsplit(":", 1)` must still
    split it into (file, line), exactly as it already does for today's shape."""
    text = CODE_REVIEW_REPORT_TEMPLATE.format(
        verdict="PASS WITH RISKS",
        findings="1. **[P1] `src/merger_rate.py:501` Preflight accepts mismatched recorded redshifts**",
    )
    parsed = rs.parse_report("code-review", text)
    assert "parse_error" not in parsed, parsed.get("parse_error")
    finding = parsed["findings"][0]
    assert finding["file"] == "src/merger_rate.py"
    assert finding["line"] == 501
    assert finding["title"] == "Preflight accepts mismatched recorded redshifts"


def test_shape3_bold_around_severity_only_then_backticked_location():
    """The one real shape-3 line (trial 11 slice 1 review-3, code-review):
    bold wraps only `[P3]`, then a plain (unbolded) path-shaped location."""
    text = CODE_REVIEW_REPORT_TEMPLATE.format(
        verdict="PASS WITH RISKS",
        findings="1. **[P3]** `tests/test_merger_rate.py:52` Dead code in test fixture",
    )
    parsed = rs.parse_report("code-review", text)
    assert "parse_error" not in parsed, parsed.get("parse_error")
    finding = parsed["findings"][0]
    assert finding["severity"] == "P3"
    assert finding["file"] == "tests/test_merger_rate.py"
    assert finding["line"] == 52
    assert finding["title"] == "Dead code in test fixture"


def test_finding_with_no_recoverable_severity_still_a_named_parse_error():
    """Severity is always required -- a numbered line with no `[P0-3]` token
    in any recognised shape must never silently disappear or invent one."""
    text = DRIFT_REPORT_TEMPLATE.format(verdict="PASS", findings="1. Some finding with no severity tag at all")
    parsed = rs.parse_report("drift-audit", text)
    assert "parse_error" in parsed
    assert "malformed finding line" in parsed["parse_error"]


def test_finding_identity_handles_a_missing_location_without_raising():
    """`finding_identity`/`count_open_findings` must not crash on a `file`
    of `None` -- normalize_path is never called on it."""
    location_less = {"severity": "P2", "file": None, "line": None, "title": "Some finding"}
    assert rs.finding_identity(location_less) == (None, "some finding")
    assert rs.count_open_findings([location_less], [location_less]) == 1
    assert rs.count_open_findings([location_less], []) == 0


# --- Verdict extraction (docs/LEADERBOARD-REBUILD-PLAN.md Stage 4a, Part 2) -


@pytest.mark.parametrize(
    "gate_lines",
    [
        # Real trial 10 slice 1 shape: dash bullet, bold label, backtick value.
        "- **Verdict:** `PASS`",
        # Real trial 10 slice 2 shape: no dash at all, bold label, bold value.
        "**Verdict:** **PASS**",
        # Real trial 11 slice 1 review-2 shape: no dash, everything bolded together.
        "**Verdict: PASS**",
    ],
)
def test_bold_drift_verdict_is_recovered_in_every_real_shape(gate_lines):
    text = DRIFT_REPORT_TEMPLATE.format(verdict="ignored", findings="- none").replace(
        "- Verdict: ignored", gate_lines
    )
    parsed = rs.parse_report("drift-audit", text)
    assert "parse_error" not in parsed, parsed.get("parse_error")
    assert parsed["verdict"] == "PASS"


def test_drift_verdict_genuinely_absent_stays_a_named_parse_error():
    text = DRIFT_REPORT_TEMPLATE.format(verdict="PASS", findings="- none").replace("- Verdict: PASS", "")
    parsed = rs.parse_report("drift-audit", text)
    assert "parse_error" in parsed
    assert "Verdict" in parsed["parse_error"]


# --- Stage 4a: one record per commission, lineage-scoped supersession ------


def test_open_after_this_attempt_null_then_backfilled_with_severity_change(tmp_path):
    sheet = _base_sheet([_attempt_entry(0), _attempt_entry(1)])

    finding_attempt0 = {"severity": "P1", "file": "calc.py", "line": 10, "title": "Missing input validation"}
    finding_attempt1_same = {"severity": "P2", "file": "calc.py", "line": 10, "title": "Missing input validation"}
    finding_attempt1_new = {"severity": "P1", "file": "calc.py", "line": 30, "title": "New unrelated issue"}

    record0 = _make_record(
        event_index=0, head="h0", at="t0", report_ref="r0.md", report_sha256="sha0",
        parsed={"verdict": "PASS WITH RISKS", "findings": [finding_attempt0], "sections": {}},
    )
    rs.upsert_sheet(sheet, 0, record0)
    assert _reviews_for(sheet["attempts"][0])[0]["open_after_this_attempt"] is None

    record1 = _make_record(
        event_index=1, head="h1", at="t1", report_ref="r1.md", report_sha256="sha1",
        parsed={"verdict": "PASS", "findings": [finding_attempt1_same, finding_attempt1_new], "sections": {}},
    )
    rs.upsert_sheet(sheet, 1, record1)

    # Attempt 0's finding recurred (severity changed, identity did not) -> backfilled to 1.
    assert _reviews_for(sheet["attempts"][0])[0]["open_after_this_attempt"] == 1
    # Attempt 1 has no successor yet -> still null.
    assert _reviews_for(sheet["attempts"][1])[0]["open_after_this_attempt"] is None


def test_upsert_preserves_other_attempts_and_tool1_fields(tmp_path):
    sheet = _base_sheet([_attempt_entry(0), _attempt_entry(1)])
    before = json.loads(json.dumps(sheet))  # deep copy for comparison

    record = _make_record(
        event_index=0, skill="drift-audit", report_ref="r.md", report_sha256="sha-x",
        parsed={"verdict": "PASS", "findings": [], "sections": {"Behaviour Added": 0}},
    )
    rs.upsert_sheet(sheet, 0, record)

    # Attempt 1 (untouched) is byte-for-byte identical.
    assert sheet["attempts"][1] == before["attempts"][1]
    # Attempt 0's Tool 1 fields are preserved exactly.
    for key in ("correctness", "quality", "scope", "commit_sha", "timestamp", "pm_decision"):
        assert sheet["attempts"][0][key] == before["attempts"][0][key]
    assert _reviews_for(sheet["attempts"][0]) == [record]


def test_upsert_missing_attempt_entry_is_a_loud_failure(tmp_path):
    sheet = _base_sheet([_attempt_entry(0)])
    record = _make_record(event_index=0, skill="drift-audit", parsed={"verdict": "PASS", "findings": [], "sections": {}})
    with pytest.raises(rs.ReviewScoreError, match="attempt 5"):
        rs.upsert_sheet(sheet, 5, record)


def test_upsert_is_idempotent_by_event_index_not_a_growing_list(tmp_path):
    """Re-upserting the same event_index replaces the record in place --
    a rerun must never append a duplicate."""
    sheet = _base_sheet([_attempt_entry(0)])
    record = _make_record(event_index=0, skill="drift-audit", parsed={"verdict": "PASS", "findings": [], "sections": {}})
    rs.upsert_sheet(sheet, 0, record)
    rs.upsert_sheet(sheet, 0, dict(record))  # identical re-upsert
    assert len(_reviews_for(sheet["attempts"][0])) == 1


def test_two_different_lineages_on_one_attempt_are_a_panel_both_stand():
    """Two reviewer models commissioned for the same skill on the same
    attempt: a genuine panel (hypothetical -- no real one exists in the
    cohort yet, per docs/LEADERBOARD-REBUILD-PLAN.md). Both records must
    stand, neither superseded, and each tracks its OWN open_after_this_attempt
    lineage independently."""
    sheet = _base_sheet([_attempt_entry(0), _attempt_entry(1)])

    finding_a = {"severity": "P1", "file": "calc.py", "line": 1, "title": "Reviewer A's finding"}
    finding_b = {"severity": "P1", "file": "calc.py", "line": 2, "title": "Reviewer B's finding"}

    record_a0 = _make_record(
        event_index=0, skill="drift-audit", tool="claude", model="model-a", at="t0",
        parsed={"verdict": "PASS", "findings": [finding_a], "sections": {}},
    )
    record_b0 = _make_record(
        event_index=1, skill="drift-audit", tool="opencode", model="model-b", at="t1",
        parsed={"verdict": "PASS", "findings": [finding_b], "sections": {}},
    )
    rs.upsert_sheet(sheet, 0, record_a0)
    rs.upsert_sheet(sheet, 0, record_b0)

    reviews0 = _reviews_for(sheet["attempts"][0])
    assert len(reviews0) == 2
    assert all(r["superseded_by"] is None for r in reviews0)

    # Attempt 1: reviewer A is commissioned again, B is not.
    record_a1 = _make_record(
        event_index=2, skill="drift-audit", tool="claude", model="model-a", at="t2",
        parsed={"verdict": "PASS", "findings": [], "sections": {}},
    )
    rs.upsert_sheet(sheet, 1, record_a1)

    reviews0 = _reviews_for(sheet["attempts"][0])
    by_model = {r["model"]: r for r in reviews0}
    # A's attempt-0 finding did not recur in A's attempt-1 review -> 0.
    assert by_model["model-a"]["open_after_this_attempt"] == 0
    # B was never reviewed again -> still null, not 0 -- no successor for B's lineage.
    assert by_model["model-b"]["open_after_this_attempt"] is None


def test_same_lineage_retry_supersedes_the_earlier_record_trial11_shape():
    """The real trial 11 slice 1 collision: the same reviewer identity
    (skill, tool, model, effort) commissioned twice on one attempt. The
    earlier record must be superseded by the later's event_index, stay on
    the sheet (never discarded), and the active (later) record must be the
    one open_after_this_attempt backfill and lineage tracking use."""
    sheet = _base_sheet([_attempt_entry(0), _attempt_entry(1)])

    review1 = _make_record(
        event_index=14, skill="drift-audit", tool="claude", model="claude-haiku-4-5", effort="low",
        report_ref="review-1-drift-audit-claude.md",
        parsed=rs.parse_report("drift-audit", TRIAL11_ONE_LINE_NON_REPORT),
    )
    assert "parse_error" in review1

    review2_findings = "- none"
    review2_text = DRIFT_REPORT_TEMPLATE.format(verdict="PASS", findings=review2_findings)
    review2 = _make_record(
        event_index=15, skill="drift-audit", tool="claude", model="claude-haiku-4-5", effort="low",
        report_ref="review-2-drift-audit-claude.md",
        parsed=rs.parse_report("drift-audit", review2_text),
    )

    rs.upsert_sheet(sheet, 0, review1)
    rs.upsert_sheet(sheet, 0, review2)

    reviews0 = sorted(_reviews_for(sheet["attempts"][0]), key=lambda r: r["event_index"])
    assert len(reviews0) == 2
    assert reviews0[0]["event_index"] == 14
    assert reviews0[0]["parse_error"]
    assert reviews0[0]["superseded_by"] == 15
    assert reviews0[1]["event_index"] == 15
    assert reviews0[1]["superseded_by"] is None
    assert reviews0[1]["verdict"] == "PASS"


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
    reviews = _reviews_for(sheet["attempts"][0])
    assert len(reviews) == 1
    record = reviews[0]
    assert "commissioned" not in record  # dead field, deleted (Stage 4a)
    assert record["event_index"] == 1
    assert record["review_id"] is None  # this fixture's run.json never recorded one
    assert record["skill"] == "drift-audit"
    assert record["tool"] == "codex"
    assert record["verdict"] == "PASS"
    assert record["findings_by_severity"] == {"P0": 0, "P1": 0, "P2": 1, "P3": 0}
    assert record["open_after_this_attempt"] is None
    assert record["superseded_by"] is None


def _backlog_fixture(tmp_path: Path):
    """Two never-before-harvested drift-audit reviews for the same slice,
    across attempts 0 and 1 -- a driver catching up after missing both polls
    (finding 3)."""
    run_dir = tmp_path / "run"
    report0_path = tmp_path / "reports" / "review-drift-audit-codex-0.md"
    report1_path = tmp_path / "reports" / "review-drift-audit-codex-1.md"
    text0 = DRIFT_REPORT_TEMPLATE.format(
        verdict="PASS WITH RISKS",
        findings="1. [P1] `calc.py:12` Unvalidated bin edge",
    )
    text1 = DRIFT_REPORT_TEMPLATE.format(verdict="PASS", findings="- none")
    sha0 = _write(report0_path, text0)
    sha1 = _write(report1_path, text1)

    _events_jsonl(run_dir / "events.jsonl", [
        {"ts": "t0", "kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
        {"ts": "t1", "kind": "review", "slice": "Slice 1", "note": "drift-audit via codex", "evidence": str(report0_path)},
        {"ts": "t2", "kind": "steer", "slice": "Slice 1", "note": "fix the bin edge"},
        {"ts": "t3", "kind": "review", "slice": "Slice 1", "note": "drift-audit via codex", "evidence": str(report1_path)},
    ])
    run_state = _run_state([
        _review_state_entry("drift-audit", str(report0_path), sha0),
        _review_state_entry("drift-audit", str(report1_path), sha1),
    ])
    (run_dir / "run.json").write_text(json.dumps(run_state), encoding="utf-8")

    sheet_path = tmp_path / "sheet.json"
    sheet_path.write_text(json.dumps(_base_sheet([_attempt_entry(0), _attempt_entry(1)])), encoding="utf-8")
    return run_dir, sheet_path


def test_a_backlog_of_two_reviews_is_harvested_in_one_call(tmp_path: Path) -> None:
    run_dir, sheet_path = _backlog_fixture(tmp_path)
    rs.run_review_score(run_dir, 1, "drift-audit", sheet_path)

    sheet = json.loads(sheet_path.read_text())
    attempt0_record = _reviews_for(sheet["attempts"][0])[0]
    attempt1_record = _reviews_for(sheet["attempts"][1])[0]
    assert attempt0_record["findings_by_severity"]["P1"] == 1
    assert attempt1_record["verdict"] == "PASS"
    # Attempt 1's review recorded no matching finding, so attempt 0's finding
    # did not recur -- backfilled to 0, not left null.
    assert attempt0_record["open_after_this_attempt"] == 0
    assert attempt1_record["open_after_this_attempt"] is None


def test_a_backlog_harvest_is_idempotent_by_reselecting_the_same_commission_set(tmp_path: Path) -> None:
    """Stage 4a: harvesting is deterministic by construction -- a rerun
    reselects the identical commission list from the same event log and
    performs the identical upserts, so the sheet is unchanged."""
    run_dir, sheet_path = _backlog_fixture(tmp_path)
    rs.run_review_score(run_dir, 1, "drift-audit", sheet_path)
    first = json.loads(sheet_path.read_text())

    rs.run_review_score(run_dir, 1, "drift-audit", sheet_path)
    second = json.loads(sheet_path.read_text())
    assert first == second


def _panel_fixture(tmp_path: Path):
    """A hypothetical two-reviewer panel: two different drift-audit
    reviewers commissioned on the same attempt (no real one exists in the
    cohort -- docs/LEADERBOARD-REBUILD-PLAN.md is explicit this must be
    built, not read from real data)."""
    run_dir = tmp_path / "run"
    report_a = tmp_path / "reports" / "review-a.md"
    report_b = tmp_path / "reports" / "review-b.md"
    text_a = DRIFT_REPORT_TEMPLATE.format(verdict="PASS", findings="1. [P1] `calc.py:1` Finding from A")
    text_b = DRIFT_REPORT_TEMPLATE.format(verdict="PASS WITH RISKS", findings="1. [P2] `calc.py:2` Finding from B")
    sha_a = _write(report_a, text_a)
    sha_b = _write(report_b, text_b)

    _events_jsonl(run_dir / "events.jsonl", [
        {"ts": "t0", "kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
        {"ts": "t1", "kind": "review", "slice": "Slice 1", "note": "drift-audit via claude", "evidence": str(report_a)},
        {"ts": "t2", "kind": "review", "slice": "Slice 1", "note": "drift-audit via opencode", "evidence": str(report_b)},
    ])
    run_state = _run_state([
        _review_state_entry("drift-audit", str(report_a), sha_a, tool="claude", model="model-a"),
        _review_state_entry("drift-audit", str(report_b), sha_b, tool="opencode", model="model-b"),
    ])
    (run_dir / "run.json").write_text(json.dumps(run_state), encoding="utf-8")

    sheet_path = tmp_path / "sheet.json"
    sheet_path.write_text(json.dumps(_base_sheet([_attempt_entry(0)])), encoding="utf-8")
    return run_dir, sheet_path


def test_end_to_end_panel_of_two_reviewers_both_records_survive(tmp_path: Path) -> None:
    """Two reviewer models on one submission (docs/LEADERBOARD-REBUILD-PLAN.md
    Stage 4a's panel requirement) must both land as independent, non-superseded
    records -- the old single-slot schema would have silently kept only the
    later of the two."""
    run_dir, sheet_path = _panel_fixture(tmp_path)

    # PM commissions both skills' events on the same slice; this call only
    # ever harvests drift-audit, matching run_review_score's own contract.
    rs.run_review_score(run_dir, 1, "drift-audit", sheet_path)

    sheet = json.loads(sheet_path.read_text())
    reviews = _reviews_for(sheet["attempts"][0])
    assert len(reviews) == 2
    assert {r["model"] for r in reviews} == {"model-a", "model-b"}
    assert all(r["superseded_by"] is None for r in reviews)
    by_model = {r["model"]: r for r in reviews}
    assert by_model["model-a"]["findings"][0]["title"] == "Finding from A"
    assert by_model["model-b"]["findings"][0]["title"] == "Finding from B"


def _retry_fixture(tmp_path: Path):
    """The real trial 11 slice 1 shape end-to-end: the same reviewer
    identity commissioned twice on one attempt -- the first a one-line
    non-report, the second the real report."""
    run_dir = tmp_path / "run"
    report1 = tmp_path / "reports" / "review-1-drift-audit-claude.md"
    report2 = tmp_path / "reports" / "review-2-drift-audit-claude.md"
    sha1 = _write(report1, TRIAL11_ONE_LINE_NON_REPORT)
    sha2 = _write(report2, DRIFT_REPORT_TEMPLATE.format(verdict="PASS", findings="- none"))

    _events_jsonl(run_dir / "events.jsonl", [
        {"ts": "t0", "kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
        {"ts": "t1", "kind": "review", "slice": "Slice 1", "note": "drift-audit via claude", "evidence": str(report1)},
        {"ts": "t2", "kind": "review", "slice": "Slice 1", "note": "drift-audit via claude", "evidence": str(report2)},
    ])
    run_state = _run_state([
        _review_state_entry("drift-audit", str(report1), sha1, tool="claude", model="claude-haiku-4-5",
                             effort="low", review_id="review-1"),
        _review_state_entry("drift-audit", str(report2), sha2, tool="claude", model="claude-haiku-4-5",
                             effort="low", review_id="review-2"),
    ])
    (run_dir / "run.json").write_text(json.dumps(run_state), encoding="utf-8")

    sheet_path = tmp_path / "sheet.json"
    sheet_path.write_text(json.dumps(_base_sheet([_attempt_entry(0)])), encoding="utf-8")
    return run_dir, sheet_path


def test_end_to_end_retry_supersedes_and_preserves_review_ids(tmp_path: Path) -> None:
    run_dir, sheet_path = _retry_fixture(tmp_path)
    rs.run_review_score(run_dir, 1, "drift-audit", sheet_path)

    sheet = json.loads(sheet_path.read_text())
    reviews = sorted(_reviews_for(sheet["attempts"][0]), key=lambda r: r["event_index"])
    assert len(reviews) == 2
    assert reviews[0]["review_id"] == "review-1"
    assert reviews[0]["parse_error"]
    assert reviews[0]["superseded_by"] == reviews[1]["event_index"]
    assert reviews[1]["review_id"] == "review-2"
    assert reviews[1]["superseded_by"] is None
    assert reviews[1]["verdict"] == "PASS"


def test_a_sheet_for_a_different_run_or_slice_is_refused(tmp_path: Path) -> None:
    """finding 5: --sheet must be validated the same way dev_check.py
    validates --out, or an explicit path into another run's or slice's sheet
    is silently modified."""
    run_dir, sheet_path = _full_fixture(tmp_path)
    foreign_sheet = _base_sheet([_attempt_entry(0)])
    foreign_sheet["run_id"] = "some-other-run"
    sheet_path.write_text(json.dumps(foreign_sheet), encoding="utf-8")

    with pytest.raises(rs.ReviewScoreError, match="run_id"):
        rs.run_review_score(run_dir, 1, "drift-audit", sheet_path)

    # Refused before any write: the foreign sheet is untouched.
    assert json.loads(sheet_path.read_text()) == foreign_sheet


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


def test_a_missing_row_for_an_earlier_attempt_does_not_block_a_later_attempts_review(tmp_path: Path) -> None:
    """Real defect found by independent review, 2026-09-11: this used to
    raise on the FIRST attempt (in ascending order) with no sheet row and
    abort the whole harvest -- so under tools/grade_run.py's post-hoc
    design, which only ever creates a row for a slice's FINAL attempt, one
    superseded attempt's missing row silently discarded the final attempt's
    own review too, before it was ever reached. Still holds verbatim under
    the commission-per-record schema (Stage 4a).

    Fixture: two code-review events for Slice 1, one at attempt 0
    (superseded -- no sheet row, matching grade_run.py's real shape) and one
    at attempt 2 (the final, accepted attempt -- has a sheet row). The
    attempt 2 review must still be harvested, and the attempt 0 gap must be
    reported, not silently dropped or fatally raised.
    """
    run_dir = tmp_path / "run"
    report0 = tmp_path / "reports" / "review-0.md"
    report2 = tmp_path / "reports" / "review-2.md"
    sha0 = _write(report0, CODE_REVIEW_REPORT_TEMPLATE.format(verdict="PASS", findings="- none"))
    sha2 = _write(report2, CODE_REVIEW_REPORT_TEMPLATE.format(verdict="PASS", findings="- none"))

    _events_jsonl(run_dir / "events.jsonl", [
        {"ts": "t0", "kind": "launch", "slice": "Slice 1", "note": "attempt 0"},
        {"ts": "t1", "kind": "review", "slice": "Slice 1", "note": "code-review via codex", "evidence": str(report0)},
        {"ts": "t2", "kind": "steer", "slice": "Slice 1", "note": "steer 1"},
        {"ts": "t3", "kind": "steer", "slice": "Slice 1", "note": "steer 2"},
        {"ts": "t4", "kind": "review", "slice": "Slice 1", "note": "code-review via codex", "evidence": str(report2)},
        {"ts": "t5", "kind": "accept", "slice": "Slice 1", "note": "accepted"},
    ])
    run_state = _run_state([
        _review_state_entry("code-review", str(report0), sha0, at="2026-01-01T00:00:01Z"),
        _review_state_entry("code-review", str(report2), sha2, at="2026-01-01T00:00:04Z"),
    ])
    (run_dir / "run.json").write_text(json.dumps(run_state), encoding="utf-8")

    sheet_path = tmp_path / "sheet.json"
    # Only attempt 2 (the final attempt) has a row -- exactly what
    # grade_run.py's gradeable_slice_targets() produces; attempt 0's row is
    # deliberately absent, matching the real bug's shape.
    sheet_path.write_text(json.dumps(_base_sheet([_attempt_entry(2)])), encoding="utf-8")

    problems = rs.run_review_score(run_dir, 1, "code-review", sheet_path)

    assert len(problems) == 1
    assert "attempt 0" in problems[0]

    sheet = json.loads(sheet_path.read_text())
    attempt2 = next(a for a in sheet["attempts"] if a["attempt"] == 2)
    reviews = _reviews_for(attempt2)
    assert len(reviews) == 1
    assert reviews[0]["report_ref"] == str(report2)
