"""Tools 2/3 (merged): harvest a commissioned reviewer report into the scoring sheet.

See docs/MODE2-REWRITE-PLAN.md §6 (scoring-sheet schema) and §7 ("Tools 2/3") for
the full contract this module implements. In short: `pm.py` runs `drift-audit` and
`code-review` as one-shot reviewer subprocesses and writes their reports plus a
`review.py`-recorded `run.json["slices"][i]["reviews"][...]` entry itself. This
tool never invokes a reviewer or writes PM state; it only reads the trail PM
already produced and folds a deterministic summary of it into this repo's own
scoring sheet (`results/runs/<run_id>/slice-<N>.json`, written by `dev_check.py`).

Race-safe read (binding, not an optimisation): the in-worktree `.pm/` mirror of a
review report is written non-atomically, so file existence alone can mean a
partial file. The safe sequence, mirroring `pm_lib.slice_ops.is_review_fresh`:
read `events.jsonl` for the `"review"` event on this slice/skill, read the
matching `run.json["slices"][i]["reviews"]` entry, and verify the sha256 of the
file on disk against the recorded sha256 *before* parsing it. A mismatch is a
loud, named failure — never a silent re-parse or a warning.

Attempt attribution (binding): a review belongs to the attempt that was live
when it ran. PM's attempt counter is 0 on the initial `launch` and +1 per
`relaunch`/`steer`. This tool computes a review's attempt number as (the count
of `launch`/`relaunch`/`steer` events for the slice that occur, in file order,
strictly before the review event) minus 1 — never from `run.json` timestamps.

`open_after_this_attempt` — the subtle part. It is only knowable retrospectively:
a finding in attempt N's review of a given skill counts as still open if a
finding with the same identity — (normalised file path, normalised lowercase
title); severity may legitimately change between attempts and is deliberately
excluded from the identity — appears in attempt N+1's review of that same
skill. So when this tool parses attempt N+1's review, it backfills attempt N's
`open_after_this_attempt` in the sheet. Until a successor review exists for that
skill, the field is `null` ("not yet determinable") — never `0`, which would
falsely claim every finding was fixed. (There is no symmetric "parse attempt N
after N+1 already exists" backfill: this tool always resolves and parses the
*latest* review event for a skill/slice, so it can never be asked to parse an
attempt whose successor's review is already recorded — see C1's resolution.)
A review that fails to parse contributes no findings and is therefore skipped
entirely for backfill purposes (an unparseable review can neither confirm nor
deny that a predecessor's findings recurred).

An unparseable report is recorded as a loud, explicit `parse_error` naming the
reason on the sheet's `drift_review`/`code_review` record — `findings_by_severity`
and `findings` are omitted entirely in that case, never fabricated as zero,
because a real "reviewer found nothing" result is recorded as explicit zero
counts and an absent/parse_error result must never be confusable with that.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import sys
from pathlib import Path
from typing import Any

import bench_lib

SEVERITIES = ("P0", "P1", "P2", "P3")

# A finding line looks like: `1. [P1] \`path/to/file:123\` Title`
_FINDING_RE = re.compile(r"^\d+\.\s*\[(P[0-3])\]\s*`([^`]+)`\s*(.*)$")
_LIST_ITEM_RE = re.compile(r"^\s*-\s+(.*)$")
_HEADER_RE = re.compile(r"^##\s+(.+?)\s*$")

# Per-skill report shape, taken verbatim from each skill's own SKILL.md Output
# section (drift-audit/SKILL.md, code-review/SKILL.md) — not re-derived here.
_SKILL_CONFIG: dict[str, dict[str, Any]] = {
    "drift-audit": {
        "sheet_field": "drift_review",
        "findings_header": "Drift Findings",
        "required_headers": (
            "Authorization Gate",
            "Drift Findings",
            "Behaviour Added",
            "Behaviour Removed",
            "Missing Tests",
            "New Coupling",
            "Contract Defects",
            "Non-Goals Check",
            "Next Action",
        ),
        # Structured, non-finding sections whose item count feeds `sections`.
        "count_headers": (
            "Behaviour Added",
            "Behaviour Removed",
            "Missing Tests",
            "New Coupling",
            "Contract Defects",
            "Non-Goals Check",
        ),
        "verdict_header": "Authorization Gate",
        "verdict_values": ("PASS WITH RISKS", "BLOCKED", "PASS", "FAIL"),
    },
    "code-review": {
        "sheet_field": "code_review",
        "findings_header": "Findings",
        "required_headers": (
            "Authorization Status",
            "Findings",
            "Contract Defects",
            "Open Questions / Assumptions",
            "Coverage Summary",
            "Verdict",
        ),
        "count_headers": (
            "Contract Defects",
            "Open Questions / Assumptions",
            "Coverage Summary",
        ),
        "verdict_header": "Verdict",
        "verdict_values": ("PASS WITH RISKS", "PASS", "FAIL"),
    },
}


class ReviewScoreError(bench_lib.BenchLibError):
    """A loud, specific failure — every message names the concrete artifact involved.

    Subclasses bench_lib's shared base so a bench_lib helper's failure
    surfaces under this tool's own name once re-raised (see
    repo_root_from_git()), never as an unfamiliar third type.
    """


def read_json(path: Path) -> Any:
    """Read and parse one JSON file, failing loudly with the path on error."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReviewScoreError(f"required file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReviewScoreError(f"invalid JSON in {path}: {exc}") from exc


def read_events(run_dir: Path) -> list[dict[str, Any]]:
    """Read `events.jsonl` -- see bench_lib.read_events(). Contract: a missing
    log returns `[]`, not an error (dev_check.py's original behaviour, now
    shared); a review harvest genuinely cannot proceed without events, so
    run_review_score() fails loudly itself on an empty result rather than
    relying on this function to do it."""
    try:
        return bench_lib.read_events(run_dir)
    except bench_lib.BenchLibError as exc:
        raise ReviewScoreError(str(exc)) from exc


def find_latest_review_event(
    events: list[dict[str, Any]], slice_id: str, skill: str
) -> tuple[int, dict[str, Any]]:
    """Find the most recent successful `review` event for this slice+skill.

    Returns (index into `events`, event). The note PM writes is `"<skill> via
    <tool>"` (see `pm_lib.review`), so matching the skill is a prefix check on
    the part before " via " -- but PM's reviewer-timeout path (`pm_lib.review`)
    appends a `review` event with the *same* note prefix
    (f"{skill} via {tool} timed out after ...s; ...") and no `evidence` field
    at all (verified: a timeout raises before `mirror_artifact`/`sha256_file`
    ever run, so there is no report to record). Matching on the note prefix
    alone would pick a timeout as "latest" and this tool would then die on
    the missing evidence path, permanently blocking a harvest of an earlier
    successful review. `evidence` is therefore the discriminator, not just
    the note: a successful commission always records it, a timeout never
    does.
    """
    prefix = f"{skill} via "
    matches = [
        (i, e)
        for i, e in enumerate(events)
        if e.get("kind") == "review"
        and e.get("slice") == slice_id
        and str(e.get("note", "")).startswith(prefix)
        and e.get("evidence")
    ]
    if not matches:
        raise ReviewScoreError(f"no '{skill}' review event with recorded evidence found for slice {slice_id!r} in events log")
    return matches[-1]


def compute_attempt_number(events: list[dict[str, Any]], slice_id: str, review_index: int) -> int:
    """Compute the attempt a review at `events[review_index]` belongs to.

    Per the module docstring: (count of launch/relaunch/steer events for this
    slice strictly before `review_index`) - 1. This mirrors PM's own attempts
    counter (0 on initial launch, +1 per relaunch/steer) without reading it
    directly off `run.json`, which is not itself a reliable attempt marker at
    read time (see docs/MODE2-REWRITE-PLAN.md §6's rotation-ordering note).
    """
    count = sum(
        1
        for e in events[:review_index]
        if e.get("kind") in ("launch", "relaunch", "steer") and e.get("slice") == slice_id
    )
    if count == 0:
        raise ReviewScoreError(
            f"no launch/relaunch/steer event precedes the review event for slice {slice_id!r}; "
            "cannot attribute it to an attempt"
        )
    return count - 1


def find_run_review_entry(
    run_state: dict[str, Any], slice_id: str, skill: str, artifact: str
) -> dict[str, Any]:
    """Find the `run.json` `reviews[]` entry matching this event's skill and artifact path.

    Looks the slice up by its `id` (e.g. "Slice 1"), not by position in
    `run.json["slices"]` -- dev_check.py's `find_slice_entry` already does
    this the robust way; positional indexing (`slices[slice_num - 1]`) only
    works today because slices happen to appear in plan order, and is one
    reordering away from silently reading the wrong slice's reviews.
    """
    slices = run_state.get("slices") or []
    matching = [s for s in slices if isinstance(s, dict) and s.get("id") == slice_id]
    if not matching:
        raise ReviewScoreError(f"run.json has no slices[] entry with id={slice_id!r}")
    reviews = matching[0].get("reviews") or []
    matches = [r for r in reviews if r.get("skill") == skill and r.get("artifact") == artifact]
    if not matches:
        raise ReviewScoreError(
            f"run.json slice {slice_id!r}'s 'reviews' has no '{skill}' entry with artifact={artifact!r}"
        )
    return matches[-1]


def verify_report_sha256(report_path: Path, expected_sha256: str) -> None:
    """Verify the on-disk report hash before any parsing. Mismatch is a loud, named failure."""
    if not report_path.exists():
        raise ReviewScoreError(f"review report not found on disk: {report_path}")
    actual = hashlib.sha256(report_path.read_bytes()).hexdigest()
    if actual != expected_sha256:
        raise ReviewScoreError(
            f"sha256 mismatch for {report_path}: run.json recorded {expected_sha256}, disk has {actual} "
            "— refusing to parse a possibly-partial or tampered report"
        )


def _split_sections(text: str) -> dict[str, list[str]]:
    """Split a Markdown report into {header text -> body lines} by `## ` headers."""
    sections: dict[str, list[str]] = {}
    current: str | None = None
    buf: list[str] = []
    for line in text.splitlines():
        m = _HEADER_RE.match(line)
        if m:
            if current is not None:
                sections[current] = buf
            current = m.group(1)
            buf = []
        elif current is not None:
            buf.append(line)
    if current is not None:
        sections[current] = buf
    return sections


def _is_none_section(lines: list[str]) -> bool:
    stripped = [ln.strip() for ln in lines if ln.strip()]
    return len(stripped) == 1 and stripped[0].lower() in ("- none", "none")


def _count_list_items(lines: list[str]) -> int:
    """Count bullet items in a section; a bare `- none` section scores 0."""
    if _is_none_section(lines):
        return 0
    return sum(1 for ln in lines if _LIST_ITEM_RE.match(ln))


def _extract_verdict(section_lines: list[str], skill: str, config: dict[str, Any]) -> str:
    """Extract the verdict token from its section, longest candidate value first."""
    text = "\n".join(section_lines)
    if skill == "drift-audit":
        verdict_line = next((ln for ln in section_lines if re.match(r"^\s*-\s*Verdict:", ln)), None)
        if verdict_line is None:
            raise ReviewScoreError(f"'{config['verdict_header']}' section has no '- Verdict:' line")
        text = verdict_line
    for value in sorted(config["verdict_values"], key=len, reverse=True):
        if re.search(r"\b" + re.escape(value) + r"\b", text):
            return value
    raise ReviewScoreError(
        f"could not find a recognised verdict ({', '.join(config['verdict_values'])}) "
        f"in '{config['verdict_header']}' section"
    )


def _parse_findings(lines: list[str], header: str) -> list[dict[str, Any]]:
    """Parse numbered finding lines; a malformed numbered entry is a hard parse failure."""
    if _is_none_section(lines):
        return []
    findings: list[dict[str, Any]] = []
    for ln in lines:
        if not re.match(r"^\d+\.", ln.strip()):
            continue
        m = _FINDING_RE.match(ln.strip())
        if not m:
            raise ReviewScoreError(f"malformed finding line in '{header}' section: {ln!r}")
        severity, location, title = m.groups()
        if ":" in location and location.rsplit(":", 1)[1].isdigit():
            file_, line_no = location.rsplit(":", 1)
            line_no = int(line_no)
        else:
            file_, line_no = location, None
        findings.append({"severity": severity, "file": file_, "line": line_no, "title": title.strip()})
    return findings


def parse_report(skill: str, text: str) -> dict[str, Any]:
    """Parse a reviewer report into structured fields, or a named `parse_error`.

    Returns a dict with either:
    - {"parse_error": "<reason>"} — nothing else is populated, or
    - {"verdict": ..., "findings": [...], "sections": {...}}
    """
    config = _SKILL_CONFIG[skill]
    try:
        sections = _split_sections(text)
        missing = [h for h in config["required_headers"] if h not in sections]
        if missing:
            raise ReviewScoreError(f"report missing required section(s): {', '.join(missing)}")
        verdict = _extract_verdict(sections[config["verdict_header"]], skill, config)
        findings = _parse_findings(sections[config["findings_header"]], config["findings_header"])
        section_counts = {h: _count_list_items(sections[h]) for h in config["count_headers"]}
        return {"verdict": verdict, "findings": findings, "sections": section_counts}
    except ReviewScoreError as exc:
        return {"parse_error": str(exc)}


def findings_by_severity(findings: list[dict[str, Any]]) -> dict[str, int]:
    """Count findings by severity, all four keys always present (zeros explicit)."""
    counts = dict.fromkeys(SEVERITIES, 0)
    for f in findings:
        counts[f["severity"]] += 1
    return counts


def normalize_path(path: str) -> str:
    """Normalise a finding's file path for identity comparison across attempts."""
    return posixpath.normpath(path.strip().replace("\\", "/"))


def finding_identity(finding: dict[str, Any]) -> tuple[str, str]:
    """Identity used to match a finding across attempts: severity is deliberately excluded."""
    return (normalize_path(finding["file"]), finding["title"].strip().lower())


def count_open_findings(earlier: list[dict[str, Any]], later: list[dict[str, Any]]) -> int:
    """Count how many of `earlier`'s findings recur (by identity) in `later`."""
    later_ids = {finding_identity(f) for f in later}
    return sum(1 for f in earlier if finding_identity(f) in later_ids)


def build_record(
    skill: str,
    tool: str,
    model: str | None,
    head: str | None,
    grants_seen: int,
    at: str | None,
    report_ref: str,
    parsed: dict[str, Any],
) -> dict[str, Any]:
    """Assemble the sheet record for §6's `drift_review`/`code_review` field."""
    record: dict[str, Any] = {
        "commissioned": True,
        "report_ref": report_ref,
        "skill": skill,
        "tool": tool,
        "model": model,
        "head": head,
        "grants_seen": grants_seen,
        "at": at,
    }
    if "parse_error" in parsed:
        record["parse_error"] = parsed["parse_error"]
        return record
    record["verdict"] = parsed["verdict"]
    record["findings"] = parsed["findings"]
    record["findings_by_severity"] = findings_by_severity(parsed["findings"])
    record["sections"] = parsed["sections"]
    record["open_after_this_attempt"] = None
    return record


def upsert_sheet(
    sheet: dict[str, Any],
    sheet_field: str,
    attempt: int,
    record: dict[str, Any],
) -> None:
    """Upsert `record` onto the matching attempt entry, backfilling the predecessor.

    Mutates `sheet` in place. Every other attempt and every other field
    (notably Tool 1's `correctness`/`quality`/`scope`) is left untouched.
    """
    attempts = sheet.get("attempts")
    if not isinstance(attempts, list):
        raise ReviewScoreError("scoring sheet has no 'attempts' list")
    entries_by_number = {e.get("attempt"): e for e in attempts}
    current_entry = entries_by_number.get(attempt)
    if current_entry is None:
        raise ReviewScoreError(f"scoring sheet has no attempt {attempt} entry to upsert onto")

    if "findings" in record:
        # Backfill the predecessor's open_after_this_attempt now that this
        # attempt's findings (its "successor" from the predecessor's view) exist.
        # (C1: no symmetric "successor already parsed" branch here -- this CLI
        # always resolves and parses the *latest* review event
        # (find_latest_review_event), so it can never be asked to parse an
        # attempt whose successor's review is already in the sheet; that
        # branch was unreachable dead code and has been removed.)
        predecessor = entries_by_number.get(attempt - 1)
        if predecessor is not None:
            pred_record = predecessor.get(sheet_field)
            if pred_record is not None and "findings" in pred_record:
                pred_record["open_after_this_attempt"] = count_open_findings(
                    pred_record["findings"], record["findings"]
                )

    current_entry[sheet_field] = record


def write_sheet_atomically(sheet_path: Path, sheet: dict[str, Any]) -> None:
    """Write the sheet -- see bench_lib.write_json_atomically() (mkstemp +
    os.replace, temp file cleaned up on failure)."""
    bench_lib.write_json_atomically(sheet_path, sheet)


def default_sheet_path(repo_root: Path, run_id: str, slice_num: int) -> Path:
    return repo_root / "results" / "runs" / run_id / f"slice-{slice_num}.json"


def repo_root_from_git() -> Path:
    """This repo's root -- see bench_lib.repo_root().

    Resolved relative to bench_lib.py's own location, not the caller's cwd
    (A4): the original implementation used a bare `git rev-parse` with no
    `cwd=`, so running review_score.py from the Developer's own repo (the
    natural place to run it from) silently resolved the default --sheet path
    into the wrong repository, and let a raw CalledProcessError escape when
    cwd was not a git repo at all.
    """
    try:
        return bench_lib.repo_root()
    except bench_lib.BenchLibError as exc:
        raise ReviewScoreError(str(exc)) from exc


def run_review_score(run_dir: Path, slice_num: int, skill: str, sheet_path: Path) -> None:
    """End-to-end: locate the review, verify it, parse it, and upsert the sheet."""
    slice_id = f"Slice {slice_num}"
    run_state = read_json(run_dir / "run.json")
    events = read_events(run_dir)
    if not events:
        # bench_lib.read_events() is deliberately tolerant of a missing log
        # (an unstarted run has nothing to report yet); a review harvest is
        # never meaningful against zero events, so this caller fails loudly
        # rather than letting find_latest_review_event's message imply a
        # search that never actually looked at anything.
        raise ReviewScoreError(f"no events found at {run_dir / 'events.jsonl'}; a review harvest cannot proceed without events")

    review_index, review_event = find_latest_review_event(events, slice_id, skill)
    attempt = compute_attempt_number(events, slice_id, review_index)

    evidence = review_event.get("evidence")
    if not evidence:
        raise ReviewScoreError(f"review event for slice {slice_id!r} has no 'evidence' path")

    run_review = find_run_review_entry(run_state, slice_id, skill, evidence)
    verify_report_sha256(Path(evidence), run_review["sha256"])

    report_text = Path(evidence).read_text(encoding="utf-8")
    parsed = parse_report(skill, report_text)
    record = build_record(
        skill=skill,
        tool=run_review.get("tool"),
        model=run_review.get("model"),
        head=run_review.get("head"),
        grants_seen=run_review.get("grants_seen"),
        at=run_review.get("at"),
        report_ref=evidence,
        parsed=parsed,
    )

    sheet = read_json(sheet_path)
    config = _SKILL_CONFIG[skill]
    upsert_sheet(sheet, config["sheet_field"], attempt, record)
    write_sheet_atomically(sheet_path, sheet)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run-dir", required=True, type=Path, help="PM run directory holding run.json/events.jsonl")
    parser.add_argument("--slice", required=True, type=int, help="1-based slice number, e.g. 1 for 'Slice 1'")
    parser.add_argument("--skill", required=True, choices=sorted(_SKILL_CONFIG), help="which reviewer report to harvest")
    parser.add_argument("--sheet", type=Path, default=None, help="scoring sheet path (default: results/runs/<run_id>/slice-<N>.json)")
    args = parser.parse_args()

    try:
        run_dir = args.run_dir
        sheet_path = args.sheet
        if sheet_path is None:
            run_state = read_json(run_dir / "run.json")
            run_id = run_state.get("run_id")
            if not run_id:
                raise ReviewScoreError(f"run.json at {run_dir} has no 'run_id'")
            sheet_path = default_sheet_path(repo_root_from_git(), run_id, args.slice)
        run_review_score(run_dir, args.slice, args.skill, sheet_path)
    except ReviewScoreError as exc:
        print(f"review_score: error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
