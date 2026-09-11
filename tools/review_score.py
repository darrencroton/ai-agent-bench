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
when it ran. This tool computes a review's attempt number via
`bench_lib.attempt_ordinal` (the monotonic per-slice ordinal both this tool
and `dev_check.py` key the scoring sheet on — see that function's docstring
for why PM's own `attempts` counter cannot be used) — never from `run.json`
timestamps.

**Harvest every attempt's canonical review, deterministically (finding 3,
re-resolved as finding 1).** Earlier versions of this tool resolved and
parsed only the single latest matching `review` event for a slice+skill
(permanently skipping an earlier review if two landed between driver polls),
then later walked every unrecorded event and skip-guarded re-processing by
comparing the recorded `report_sha256` against the event's own sha256. Both
designs break when PM commissions the same skill twice against the same
attempt (`pm_lib.review`'s `_claim_commission_seq`: each successful
commission gets its own sequence number, its own `reviews[]` entry and its
own `events.jsonl` event — nothing separates the two into different
attempts): a hash-keyed skip guard can only ever hold one slot's worth of
"already recorded" state per attempt, so a second, different-content review
on the same attempt reprocesses and clobbers the first (resetting
`open_after_this_attempt` back to `None` and stranding the real successor
review's backfill), and two byte-identical-content reviews on the same
attempt collide on the same hash, so the second, later, real review is
silently dropped — losing its own `head`, `at`, `report_ref` and `model`.

The fix is to make harvesting deterministic rather than incremental: select
the **canonical review per (attempt, skill)** — the last successful event
for that pair in file order — *before* any sheet mutation (`select_canonical_reviews`),
then upsert those canonical records in ascending attempt order, recomputing
`open_after_this_attempt` carry-over from them fresh every time. A rerun
recomputes the identical canonical set from the same (only ever growing)
event log and therefore performs the identical upserts, producing the
identical sheet by construction — a stronger and simpler guarantee than a
skip-guard, and one with no reset-on-reprocess failure mode to have in the
first place. `report_sha256` stays on the record as recorded evidence of
what was actually parsed; it is never read back to decide what to skip.
Each attempt's upsert happens immediately (inside the loop, not batched at
the end), so a failure partway through a backlog never loses the attempts
already harvested before it.

`open_after_this_attempt` — the subtle part. It is only knowable retrospectively:
a finding in attempt N's review of a given skill counts as still open if a
finding with the same identity — (normalised file path, normalised lowercase
title); severity may legitimately change between attempts and is deliberately
excluded from the identity — appears in attempt N+1's review of that same
skill. So when this tool parses attempt N+1's review, it backfills attempt N's
`open_after_this_attempt` in the sheet. Until a successor review exists for that
skill, the field is `null` ("not yet determinable") — never `0`, which would
falsely claim every finding was fixed. (There is still no symmetric "parse
attempt N after N+1 already exists" backfill: `compute_attempt_number` is
non-decreasing as `review_index` increases (attempt N's ordinal only counts
launch-family events strictly before it, and those only ever increase with
index), so the canonical-per-attempt selection is always processed in
ascending attempt order — both within one call and across separate
invocations over time, since events.jsonl only ever grows. This tool can
therefore never be asked to parse an attempt whose successor's review is
already in the sheet. See C1's original resolution and finding 1's report
note on why this still holds under deterministic, re-commission-safe
harvesting.)
A review that fails to parse contributes no findings and is therefore skipped
entirely for backfill purposes (an unparsable review can neither confirm nor
deny that a predecessor's findings recurred).

An unparsable report is recorded as a loud, explicit `parse_error` naming the
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


def find_review_events(
    events: list[dict[str, Any]], slice_id: str, skill: str
) -> list[tuple[int, dict[str, Any]]]:
    """Every successful `review` event for this slice+skill, in file order.

    Returns a list of (index into `events`, event) -- finding 3: harvesting
    every one of these, not just the latest, is what makes a driver restart
    after a backlog (or two reviews landing between polls) recoverable
    without permanently skipping an earlier review.

    The note PM writes is `"<skill> via <tool>"` (see `pm_lib.review`), so
    matching the skill is a prefix check on the part before " via " -- but
    PM's reviewer-timeout path (`pm_lib.review`) appends a `review` event
    with the *same* note prefix (f"{skill} via {tool} timed out after
    ...s; ...") and no `evidence` field at all (verified: a timeout raises
    before `mirror_artifact`/`sha256_file` ever run, so there is no report to
    record). Matching on the note prefix alone would pick up a timeout as a
    harvestable review and this tool would then die on the missing evidence
    path. `evidence` is therefore the discriminator, not just the note: a
    successful commission always records it, a timeout never does.

    Raises:
        ReviewScoreError: no matching event with recorded evidence exists at all.
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
    return matches


def compute_attempt_number(events: list[dict[str, Any]], slice_id: str, review_index: int) -> int:
    """The attempt a review at `events[review_index]` belongs to --
    `bench_lib.attempt_ordinal` counting strictly before `review_index`, per
    the module docstring. Both this tool and dev_check.py key the scoring
    sheet on this same derivation so they cannot disagree by construction
    (finding 2).
    """
    try:
        return bench_lib.attempt_ordinal(events, slice_id, before_index=review_index)
    except bench_lib.BenchLibError as exc:
        raise ReviewScoreError(str(exc)) from exc


def select_canonical_reviews(
    events: list[dict[str, Any]], slice_id: str, skill: str
) -> dict[int, dict[str, Any]]:
    """The canonical review event per attempt: the last successful `review`
    event for (attempt, skill) in file order (finding 1).

    PM permits re-commissioning the same skill against the same attempt --
    `pm_lib.review`'s `_claim_commission_seq` gives each successful
    commission its own sequence number, its own `run.json` `reviews[]`
    entry and its own `events.jsonl` event, and no launch-family event
    separates two commissions on the same attempt. Policy (decided, not
    re-litigated here): the sheet keeps the latest successful review per
    (attempt, skill). Selecting that canonical set here, before any sheet
    mutation, is what makes the harvest a pure function of the event log --
    a rerun sees the same (only ever growing) log, selects the identical
    canonical set, and performs the identical upserts.

    Returns:
        {attempt: event} -- one entry per attempt that has at least one
        successful review event for this skill, keyed by
        `compute_attempt_number`. A later event for the same attempt
        overwrites an earlier one (dict insertion order follows
        `find_review_events`'s file order).
    """
    canonical: dict[int, dict[str, Any]] = {}
    for review_index, review_event in find_review_events(events, slice_id, skill):
        attempt = compute_attempt_number(events, slice_id, review_index)
        canonical[attempt] = review_event
    return canonical


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
    report_sha256: str,
) -> dict[str, Any]:
    """Assemble the sheet record for §6's `drift_review`/`code_review` field.

    `report_sha256` is the run.json-recorded hash of the report already
    verified before this is called -- kept on the record as evidence of
    what was actually parsed (finding 1: it is no longer read back to decide
    what to skip; harvesting is now deterministic by construction, see the
    module docstring and `select_canonical_reviews`). Required, not
    defaulted (AGENTS.md forbids a test-only compatibility default): every
    call site, including this module's own tests, supplies the real hash.
    """
    record: dict[str, Any] = {
        "commissioned": True,
        "report_ref": report_ref,
        "report_sha256": report_sha256,
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
        # (C1, reconfirmed under finding 1's deterministic canonical-per-
        # attempt harvest: no symmetric "successor already parsed" branch
        # here -- run_review_score processes select_canonical_reviews()'s
        # attempts in ascending order, and that order is guaranteed by
        # compute_attempt_number's monotonicity, both within one call and
        # across separate invocations over time (the log only grows). This
        # tool can therefore never be asked to parse an attempt whose
        # successor's review is already in the sheet; that branch was
        # unreachable dead code and stays removed.)
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
    """End-to-end: select this slice+skill's canonical review per attempt,
    then verify, parse and upsert each in ascending attempt order (finding 1).

    Deterministic by construction: `select_canonical_reviews` is computed
    once, before any sheet mutation, from the full event log -- a rerun
    against the same (only ever growing) log selects the identical canonical
    set and performs the identical upserts, so re-running this function
    produces the same sheet content rather than depending on a skip-guard to
    avoid reprocessing. Each attempt's upsert is written to disk immediately,
    one at a time -- not batched into a single write at the end -- so a
    failure partway through a backlog never loses the attempts already
    harvested before it.
    """
    slice_id = f"Slice {slice_num}"
    run_state = read_json(run_dir / "run.json")
    run_id = run_state.get("run_id")
    if not run_id:
        raise ReviewScoreError(f"run.json at {run_dir} has no 'run_id'")
    events = read_events(run_dir)
    if not events:
        # bench_lib.read_events() is deliberately tolerant of a missing log
        # (an unstarted run has nothing to report yet); a review harvest is
        # never meaningful against zero events, so this caller fails loudly
        # rather than letting find_review_events' message imply a search
        # that never actually looked at anything.
        raise ReviewScoreError(f"no events found at {run_dir / 'events.jsonl'}; a review harvest cannot proceed without events")

    canonical = select_canonical_reviews(events, slice_id, skill)
    sheet = read_json(sheet_path)
    # finding 5: refuse to read into (and, below, write into) another run's
    # or slice's sheet -- the same guard dev_check.py applies to --out.
    try:
        bench_lib.validate_sheet_identity(sheet, run_id, slice_num, sheet_path)
    except bench_lib.BenchLibError as exc:
        raise ReviewScoreError(str(exc)) from exc

    config = _SKILL_CONFIG[skill]
    for attempt in sorted(canonical):
        review_event = canonical[attempt]

        evidence = review_event.get("evidence")
        if not evidence:
            raise ReviewScoreError(f"review event for slice {slice_id!r} has no 'evidence' path")

        run_review = find_run_review_entry(run_state, slice_id, skill, evidence)
        expected_sha256 = run_review["sha256"]

        verify_report_sha256(Path(evidence), expected_sha256)
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
            report_sha256=expected_sha256,
            parsed=parsed,
        )

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
