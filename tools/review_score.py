"""Tools 2/3 (merged): harvest a commissioned reviewer report into the scoring sheet.

See docs/MODE2-REWRITE-PLAN.md §7 (scoring-sheet schema) and §6 ("Tools 2/3"),
and docs/LEADERBOARD-REBUILD-PLAN.md Stage 4a ("panel-preserving review
records, parser repair") for the full contract this module implements. In
short: `pm.py` runs `drift-audit` and `code-review` as one-shot reviewer
subprocesses and writes their reports plus a `review.py`-recorded
`run.json["slices"][i]["reviews"][...]` entry itself. This tool never invokes
a reviewer or writes PM state; it only reads the trail PM already produced
and folds a deterministic summary of it into this repo's own scoring sheet
(`results/runs/<run_id>/slice-<N>.json`, written by `dev_check.py`).

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

**One record per commission, never one slot per (attempt, skill)
(Stage 4a — supersedes finding 1's "canonical review per (attempt, skill)"
design below).** The per-attempt `drift_review`/`code_review` single slots
this module used to write are gone; every attempt entry instead carries a
`reviews` list, one record per successful commission. Two reviewer models on
one submission are two records — a genuine panel, never collapsed. A
re-commission of the *same* reviewer (same skill, tool, model and effort —
its "lineage", see `lineage_key`) against the *same* attempt is a retry: it
supersedes the earlier record (the earlier one's `superseded_by` is set to
the later record's `event_index`; it stays in the list, never discarded, so
a trace of the failed attempt survives). Two different lineages on the same
attempt are a panel: both stand, both `superseded_by: null`. Verified
against a real collision: trial 11 slice 1's drift-audit attempt 1 carries
`review-1` (a one-line non-report: "I need permission to read the pinned
diff file...") immediately followed by `review-2` (the real report) — same
reviewer identity, so `review-1` is superseded by `review-2`'s event index,
and the old single-slot design would have silently discarded `review-1`
entirely with no trace it ever happened.

**The record's primary key is `event_index`, never `review_id`.** Verified
against all eight real runs on disk (trials 4-11): trials 4-7 carry no
`review_id` at all in `run.json`'s `reviews[]`, and where `review_id` does
exist (trials 8-11) it is only unique *within one slice* — Slice 1 and Slice
2 both have their own `review-1`. `event_index` is the index into
`events.jsonl` this module's own `find_review_events` already returns from
its scan: it exists for every run ever produced, is unique per commission
across the whole log, and is strictly ordered (file order is time order).
`review_id` is still carried on the record, verbatim, null when PM never
recorded one — purely so a future join (PM's own `review_judgments`, out of
this module's scope; see docs/LEADERBOARD-REBUILD-PLAN.md Stage 4b) can key
on `(run_id, slice.id, review_id)` the way PM's own structured judgments do.
It is never used as a key inside this module.

Earlier versions of this tool resolved and parsed only the single latest
matching `review` event for a slice+skill (permanently skipping an earlier
review if two landed between driver polls), then later walked every
unrecorded event and skip-guarded re-processing by comparing the recorded
`report_sha256` against the event's own sha256. Both designs break when PM
commissions the same skill twice against the same attempt (`pm_lib.review`'s
`_claim_commission_seq`: each successful commission gets its own sequence
number, its own `reviews[]` entry and its own `events.jsonl` event — nothing
separates the two into different attempts): a hash-keyed skip guard can only
ever hold one slot's worth of "already recorded" state per attempt, so a
second, different-content review on the same attempt reprocesses and
clobbers the first (resetting `open_after_this_attempt` back to `None` and
stranding the real successor review's backfill), and two byte-identical-
content reviews on the same attempt collide on the same hash, so the second,
later, real review is silently dropped — losing its own `head`, `at`,
`report_ref` and `model`.

The fix is to make harvesting deterministic rather than incremental: select
**every** successful commission for (slice, skill) — `select_review_commissions`
(formerly `select_canonical_reviews`, which collapsed to one per attempt) —
*before* any sheet mutation, then upsert each one in ascending `event_index`
order (which is also non-decreasing attempt order, see
`compute_attempt_number`'s docstring), recomputing supersession and
`open_after_this_attempt` carry-over fresh every time from what is now on the
sheet. A rerun recomputes the identical commission list from the same (only
ever growing) event log and therefore performs the identical upserts,
producing the identical sheet by construction — a stronger and simpler
guarantee than a skip-guard, and one with no reset-on-reprocess failure mode
to have in the first place. `report_sha256` stays on the record as recorded
evidence of what was actually parsed; it is never read back to decide what to
skip. Each commission's upsert happens immediately (inside the loop, not
batched at the end), so a failure partway through a backlog never loses the
commissions already harvested before it.

`open_after_this_attempt` — the subtle part, now scoped per lineage rather
than per skill (Stage 4a: "mixing two reviewers' findings into one survival
count would be meaningless"). A finding in attempt N's ACTIVE (non-
superseded) record for lineage L counts as still open if a finding with the
same identity — (normalised file path or `None`, normalised lowercase title);
severity may legitimately change between attempts and is deliberately
excluded from the identity — appears in attempt N+1's ACTIVE record for that
SAME lineage L. So when this tool parses attempt N+1's record for L, it
backfills attempt N's active L-record's `open_after_this_attempt` in the
sheet. Until a successor record for that exact lineage exists, the field is
`null` ("not yet determinable") — never `0`, which would falsely claim every
finding was fixed. A lineage with no successor at all keeps `null`
permanently — this is the honest reading of "no later commission of this
same reviewer exists to say whether the finding survived", not a defect.
(There is still no symmetric "parse attempt N after N+1 already exists"
backfill: `compute_attempt_number` is non-decreasing as `event_index`
increases, so commissions are always processed in ascending attempt order —
both within one call and across separate invocations over time, since
events.jsonl only ever grows. This tool can therefore never be asked to
parse an attempt whose successor's review is already in the sheet.)
A review that fails to parse contributes no findings and is therefore skipped
entirely for backfill purposes (an unparsable review can neither confirm nor
deny that a predecessor's findings recurred).

An unparsable report is recorded as a loud, explicit `parse_error` naming the
reason on the record — `findings_by_severity` and `findings` are omitted
entirely in that case, never fabricated as zero, because a real "reviewer
found nothing" result is recorded as explicit zero counts and an
absent/parse_error result must never be confusable with that.
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

# A finding's leading `N. ` plus its severity token, in the three real shapes
# measured across all 72 reviewer reports in trials 4-11 (docs/
# LEADERBOARD-REBUILD-PLAN.md Stage 4a, "Part 2"; that document says 144,
# which counts each report's `-prompt.md` sibling alongside it -- there are
# 72 actual commissions, one report each): plain (`[P1] ...`, the
# only shape the parser originally accepted), bold wrapping the whole finding
# (`**[P1] ...**`), and bold around the severity token alone (`**[P3]** ...`).
# Group 1 (an optional leading `**`) and group 3 (an optional `**` closing
# immediately after the bracket) tell the three apart: neither present is
# plain; both present is bold-severity-only; only group 1 present is
# bold-wraps-everything, whose trailing `**` is stripped in `_parse_findings`
# before location/title extraction (never left dangling in the title).
_SEVERITY_RE = re.compile(r"^\d+\.\s*(\*\*)?\[(P[0-3])\](\*\*)?\s*(.*)$")

# Any backticked span in a finding's post-severity text -- a candidate
# location, filtered by `_is_path_shaped` before ever being trusted as one.
_BACKTICK_SPAN_RE = re.compile(r"`([^`]+)`")

# Extensions this project's own file kinds can plausibly appear as (this
# repo's style-guide baseline: Python/C/C++/Fortran, plus Markdown/YAML/etc.
# a reviewer report might cite in passing) -- deliberately a fixed allowlist,
# not "any `.xxx` suffix", so a version-like token such as "v1.2" can never
# accidentally look path-shaped.
_SOURCE_EXTENSIONS = (
    "py", "c", "cc", "cpp", "cxx", "h", "hh", "hpp", "hxx",
    "f", "f90", "f95", "md", "yaml", "yml", "toml", "sh", "txt", "json",
)
# A backticked span "ends in a source-file extension, optionally followed by
# `:<line>` or `:<start>-<end>`" (docs/LEADERBOARD-REBUILD-PLAN.md Stage 4a) --
# the second half of `_is_path_shaped`'s test; the first half (a literal `/`)
# is checked directly in that function, since a mid-span `/` need not be at
# the end.
_PATH_EXTENSION_RE = re.compile(r"\.(?:" + "|".join(_SOURCE_EXTENSIONS) + r")(?::\d+(?:-\d+)?)?$")

_LIST_ITEM_RE = re.compile(r"^\s*-\s+(.*)$")
_HEADER_RE = re.compile(r"^##\s+(.+?)\s*$")

# Per-skill report shape, taken verbatim from each skill's own SKILL.md Output
# section (drift-audit/SKILL.md, code-review/SKILL.md) — not re-derived here.
_SKILL_CONFIG: dict[str, dict[str, Any]] = {
    "drift-audit": {
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

# The skills this tool knows how to harvest, for a caller (tools/grade_run.py)
# that needs to recognise which skill a "review" event's note names without
# reaching into _SKILL_CONFIG directly.
REVIEW_SKILLS: tuple[str, ...] = tuple(sorted(_SKILL_CONFIG))


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
    (finding 2). Monotonic as `review_index` increases -- see the module
    docstring's `open_after_this_attempt` section for why that ordering
    property is load-bearing, not incidental.
    """
    try:
        return bench_lib.attempt_ordinal(events, slice_id, before_index=review_index)
    except bench_lib.BenchLibError as exc:
        raise ReviewScoreError(str(exc)) from exc


def select_review_commissions(
    events: list[dict[str, Any]], slice_id: str, skill: str
) -> list[dict[str, Any]]:
    """Every successful commission of `skill` for this slice, in file
    (= time = event_index) order (Stage 4a; formerly `select_canonical_reviews`,
    which collapsed to one event per attempt and silently discarded every
    earlier commission on a retry or a panel).

    PM permits re-commissioning the same skill against the same attempt --
    `pm_lib.review`'s `_claim_commission_seq` gives each successful
    commission its own sequence number, its own `run.json` `reviews[]` entry
    and its own `events.jsonl` event, and no launch-family event separates
    two commissions on the same attempt. Nothing is collapsed here: deciding
    whether two commissions on one attempt are a retry (same lineage,
    supersede) or a panel (different lineage, both stand) is
    `upsert_sheet`'s job downstream, never this selection step's -- this
    function only ever enumerates, in the one true order the event log
    defines.

    Selecting this full list here, before any sheet mutation, is what makes
    the harvest a pure function of the event log: a rerun sees the same
    (only ever growing) log, selects the identical commission list, and
    performs the identical upserts in the identical order.

    Returns:
        A list of `{"event_index": i, "attempt": <ordinal>, "event": e}`
        dicts, one per successful review event, in ascending `event_index`
        order -- which is also non-decreasing attempt order (`attempt`),
        per `compute_attempt_number`'s monotonicity.
    """
    commissions: list[dict[str, Any]] = []
    for event_index, review_event in find_review_events(events, slice_id, skill):
        attempt = compute_attempt_number(events, slice_id, event_index)
        commissions.append({"event_index": event_index, "attempt": attempt, "event": review_event})
    return commissions


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


def _strip_markdown_emphasis(line: str) -> str:
    """Remove Markdown emphasis markers (`*`, `_`) for locating the drift
    verdict line only -- never used to parse anything else.

    Safe here because this project's verdict line is always the fixed
    phrase "Verdict: <TOKEN>", with or without a leading "- " bullet marker;
    stripping emphasis characters can only ever reveal that phrase, never
    manufacture it out of unrelated text. This is what recovers all three
    real bold shapes verified across trials 10-11 (docs/
    LEADERBOARD-REBUILD-PLAN.md Stage 4a): "- **Verdict:** `PASS`",
    `**Verdict:** **PASS**`, and `**Verdict: PASS**` -- the last two aren't
    even bulleted list items, which is why the bullet dash is matched as
    optional below, not just the emphasis.
    """
    return line.replace("*", "").replace("_", "")


# The verdict line, once Markdown emphasis is stripped: an optional "- "
# bullet marker (present in some real reports, absent in others -- verified,
# not assumed) followed directly by "Verdict:". Confirmed safe against every
# drift-audit report in trials 4-11: each one's "Authorization Gate" section
# contains exactly one line mentioning "verdict" at all, so loosening the
# bullet requirement cannot pick up the wrong line.
_VERDICT_BULLET_RE = re.compile(r"^\s*-?\s*Verdict:")


def _extract_verdict(section_lines: list[str], skill: str, config: dict[str, Any]) -> str:
    """Extract the verdict token from its section, longest candidate value first."""
    text = "\n".join(section_lines)
    if skill == "drift-audit":
        verdict_line = next(
            (ln for ln in section_lines if _VERDICT_BULLET_RE.match(_strip_markdown_emphasis(ln))), None
        )
        if verdict_line is None:
            raise ReviewScoreError(
                f"'{config['verdict_header']}' section has no 'Verdict:' line "
                "(a leading '- ' bullet and Markdown emphasis are both optional)"
            )
        text = _strip_markdown_emphasis(verdict_line)
    for value in sorted(config["verdict_values"], key=len, reverse=True):
        if re.search(r"\b" + re.escape(value) + r"\b", text):
            return value
    raise ReviewScoreError(
        f"could not find a recognised verdict ({', '.join(config['verdict_values'])}) "
        f"in '{config['verdict_header']}' section"
    )


def _is_path_shaped(span: str) -> bool:
    """Conservative test for whether a backticked span names a source
    location rather than an attribute or function name (docs/
    LEADERBOARD-REBUILD-PLAN.md Stage 4a): it contains a `/` (a path with at
    least one directory component), or it ends in a known source-file
    extension, optionally followed by `:<line>` or `:<start>-<end>`.

    This is exactly what keeps `` `redshift` `` (an attribute name) and
    `` `_load_pair_counts()` `` (a function name) from ever becoming a
    location -- neither contains a slash or a recognised extension -- while
    still recognising `` `tests/test_merger_rate.py:249-283` `` and
    `` `src/merger_rate.py:501` ``, both real examples that must resolve.
    """
    if "/" in span:
        return True
    return bool(_PATH_EXTENSION_RE.search(span))


def _extract_location_and_title(rest: str) -> tuple[str, str | None]:
    """Split a finding's post-severity text into (title, location).

    Two distinct behaviours, both required and both verified against every
    finding that parses successfully today (docs/LEADERBOARD-REBUILD-PLAN.md
    Stage 4a, Part 2 -- "no report that parses successfully today may parse
    differently after your change"):

    - A path-shaped backticked span sitting immediately at the start of
      `rest` is consumed as the location and stripped from the title,
      leaving only the prose that follows. This is the shape the parser
      already accepted, and it is the only branch that ever rewrites a
      title -- which is what guarantees the no-regression property: every
      leading backtick span in the 53 reports that parsed before this
      repair is already path-shaped (verified directly against all 72 real
      reports), so each of them still takes exactly this branch and keeps
      byte-identical `verdict`/`findings`/`sections`. The branch is not
      exclusive to those reports, though: a bold-wrapped finding whose
      location happens to lead (real example, trial 6's
      `` 1. **[P2] `src/merger_rate.py:41-47` silently truncates ...** ``,
      a parse error before this repair) reaches it too once
      `_parse_findings` has stripped the wrapping `**`, and is treated
      identically -- structurally it *is* the leading-location shape, so
      giving it a different title would be the inconsistency.
    - A path-shaped span appearing anywhere else in the text (including a
      leading span that ISN'T path-shaped, so a later one is used instead)
      is recorded as the location, but the title keeps the FULL original
      text, backticks included -- the brief's own shape-1 examples show
      this asymmetry explicitly (e.g. "Missing required vector-redshift
      preflight test at `tests/test_merger_rate.py:249-283`" keeps that
      whole sentence, including the location, as its title). Rewriting the
      title here would invent a new, previously-nonexistent title for a
      line that is a parse error today -- there is no existing value to
      preserve, so the least lossy, most honest choice is to keep
      everything the reviewer wrote.
    - No qualifying span anywhere: the location is explicitly absent
      (`None`, never invented -- `file`/`line` become `None`/`None` in
      `_parse_findings`), and the title is the full text.

    When more than one span in the non-leading case is path-shaped (a real,
    if rare, case: a finding citing two locations), the first one found
    (left to right) is used -- simple, deterministic, and the title carries
    the full text regardless, so which one is chosen never changes what a
    human reads, only which single `(file, line)` `finding_identity` keys
    on.
    """
    rest = rest.strip()
    spans = list(_BACKTICK_SPAN_RE.finditer(rest))
    if spans and spans[0].start() == 0 and _is_path_shaped(spans[0].group(1)):
        location = spans[0].group(1)
        title = rest[spans[0].end() :].strip()
        return title, location
    for m in spans:
        if _is_path_shaped(m.group(1)):
            return rest, m.group(1)
    return rest, None


def _parse_findings(lines: list[str], header: str) -> list[dict[str, Any]]:
    """Parse numbered finding lines; a malformed numbered entry is a hard parse failure.

    Severity is always required -- a numbered line with no recoverable
    `[P0-3]` token, in any of `_SEVERITY_RE`'s three shapes, stays a named
    parse error; this function never invents one. Location is a secondary,
    best-effort extraction (`_extract_location_and_title`) and its absence
    is never itself a parse failure.
    """
    if _is_none_section(lines):
        return []
    findings: list[dict[str, Any]] = []
    for ln in lines:
        stripped_ln = ln.strip()
        if not re.match(r"^\d+\.", stripped_ln):
            continue
        m = _SEVERITY_RE.match(stripped_ln)
        if not m:
            raise ReviewScoreError(f"malformed finding line in '{header}' section: {ln!r}")
        bold_open, severity, bold_close, rest = m.groups()
        if bold_open and not bold_close:
            # Bold wraps the whole finding; its closing `**` sits at the
            # line's end and must never leak into the title.
            rest = rest.rstrip()
            if rest.endswith("**"):
                rest = rest[:-2].rstrip()
        title, location = _extract_location_and_title(rest)
        if location is not None and ":" in location and location.rsplit(":", 1)[1].isdigit():
            file_, line_no_str = location.rsplit(":", 1)
            file_field: str | None = file_
            line_no: int | None = int(line_no_str)
        elif location is not None:
            file_field, line_no = location, None
        else:
            file_field, line_no = None, None
        findings.append({"severity": severity, "file": file_field, "line": line_no, "title": title.strip()})
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


def finding_identity(finding: dict[str, Any]) -> tuple[str | None, str]:
    """Identity used to match a finding across attempts: severity is
    deliberately excluded (see the module docstring).

    `finding["file"]` can now genuinely be `None` (docs/
    LEADERBOARD-REBUILD-PLAN.md Stage 4a, Part 2: a finding whose report
    text gave no path-shaped backticked span at all). Such a finding
    identifies by its title alone -- the file component of its identity
    stays `None`, never a fabricated path `normalize_path` could crash on.
    This is the honest reading of "the report gave nothing more precise to
    key on than the title text": two location-less findings with the same
    title, for the same reviewer lineage, are treated as the same finding
    across attempts, which is no less sound than treating two findings with
    the same (file, title) as the same finding today.
    """
    file_ = finding["file"]
    normalized_file = normalize_path(file_) if file_ is not None else None
    return (normalized_file, finding["title"].strip().lower())


def count_open_findings(earlier: list[dict[str, Any]], later: list[dict[str, Any]]) -> int:
    """Count how many of `earlier`'s findings recur (by identity) in `later`."""
    later_ids = {finding_identity(f) for f in later}
    return sum(1 for f in earlier if finding_identity(f) in later_ids)


def lineage_key(record: dict[str, Any]) -> tuple[Any, Any, Any, Any]:
    """A commission's reviewer lineage: (skill, tool, model, effort).

    Two commissions on the same attempt with the same lineage are a retry
    of the same reviewer -- the later one supersedes the earlier (see
    `upsert_sheet`). Two commissions with different lineages are a genuine
    panel and never interact. `skill` is included even though one
    `run_review_score` call only ever harvests one skill at a time: the
    `reviews` list it upserts into accumulates records from BOTH skills'
    separate calls, so without `skill` here a drift-audit and a code-review
    commission by the same (tool, model, effort) could wrongly be treated
    as one lineage.
    """
    return (record["skill"], record["tool"], record["model"], record["effort"])


def build_record(
    *,
    review_id: str | None,
    event_index: int,
    skill: str,
    tool: str | None,
    model: str | None,
    effort: str | None,
    head: str | None,
    before_head: str | None,
    grants_seen: int | None,
    at: str | None,
    report_ref: str,
    report_sha256: str,
    parsed: dict[str, Any],
) -> dict[str, Any]:
    """Assemble one `reviews` list record (docs/LEADERBOARD-REBUILD-PLAN.md
    Stage 4a, "one record per commission").

    `event_index` is the record's real primary key (see the module
    docstring for why, not `review_id`) -- required, never defaulted.
    `review_id` is carried verbatim, `None` when PM never recorded one
    (trials 4-7), purely so a future PM-judgment join can use it; nothing in
    this module keys on it. `superseded_by` starts `None` here; it is only
    ever set by `upsert_sheet`, which is the one place that can see whether
    a later commission of the same lineage exists.

    `report_sha256` is the run.json-recorded hash of the report already
    verified before this is called -- kept on the record as evidence of
    what was actually parsed; it is never read back to decide what to skip
    (harvesting is deterministic by construction, see the module docstring).
    Required, not defaulted (AGENTS.md forbids a test-only compatibility
    default): every call site, including this module's own tests, supplies
    the real hash.

    `commissioned: True` (the old single-slot design's field, meaningful
    only when the field could be absent) is deleted: every entry in a
    `reviews` list IS a commission, so the field would be dead weight on
    every record (AGENTS.md: "minimum, no dead code").
    """
    record: dict[str, Any] = {
        "review_id": review_id,
        "event_index": event_index,
        "skill": skill,
        "tool": tool,
        "model": model,
        "effort": effort,
        "head": head,
        "before_head": before_head,
        "grants_seen": grants_seen,
        "at": at,
        "report_ref": report_ref,
        "report_sha256": report_sha256,
        "superseded_by": None,
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
    attempt: int,
    record: dict[str, Any],
) -> None:
    """Merge `record` into the attempt's `reviews` list, keyed on
    `event_index` (idempotent: a rerun replaces the same record in place
    rather than appending a duplicate), then recompute this lineage's
    supersession within the attempt and the predecessor attempt's
    `open_after_this_attempt` carry-over.

    Mutates `sheet` in place. Every other attempt and every other field
    (notably Tool 1's `correctness`/`quality`/`scope`) is left untouched.

    Lineage rule (Stage 4a, "one record per commission"; see `lineage_key`):
    within one attempt, commissions are grouped by (skill, tool, model,
    effort). A later commission of the SAME lineage is a retry -- it
    supersedes the earlier one (`superseded_by` set to the later record's
    `event_index`; the earlier record stays on the sheet, never discarded),
    and does not earn a second vote. Commissions of two DIFFERENT lineages
    on the same attempt are a panel: both stand, both `superseded_by: null`.
    This is what lets two independent reviewer models never overwrite each
    other while a retry of the same reviewer still only counts once.
    Supersession is recomputed from scratch across the attempt's whole
    lineage group every call (never incrementally, e.g. "mark the previous
    active record superseded"), so a rerun that re-upserts an
    already-recorded commission reproduces the identical result.
    """
    attempts = sheet.get("attempts")
    if not isinstance(attempts, list):
        raise ReviewScoreError("scoring sheet has no 'attempts' list")
    entries_by_number = {e.get("attempt"): e for e in attempts}
    current_entry = entries_by_number.get(attempt)
    if current_entry is None:
        raise ReviewScoreError(f"scoring sheet has no attempt {attempt} entry to upsert onto")

    reviews: list[dict[str, Any]] = current_entry.setdefault("reviews", [])
    reviews[:] = [r for r in reviews if r.get("event_index") != record["event_index"]]
    reviews.append(record)
    reviews.sort(key=lambda r: r["event_index"])

    same_lineage = sorted(
        (r for r in reviews if lineage_key(r) == lineage_key(record)), key=lambda r: r["event_index"]
    )
    for earlier, later in zip(same_lineage, same_lineage[1:], strict=False):
        earlier["superseded_by"] = later["event_index"]
    same_lineage[-1]["superseded_by"] = None  # same_lineage is non-empty: record is always in it

    if "findings" not in record:
        # An unparsable successor can neither confirm nor deny that a
        # predecessor's findings recurred (module docstring).
        return

    # Backfill the predecessor attempt's ACTIVE same-lineage record now that
    # this record (its "successor" from that record's view) has parsed
    # findings. No symmetric "successor already parsed" branch is needed
    # here: run_review_score processes select_review_commissions()'s
    # commissions in ascending event_index order, and that order is
    # guaranteed by compute_attempt_number's monotonicity, both within one
    # call and across separate invocations over time (the log only grows).
    # This tool can therefore never be asked to parse an attempt whose
    # successor's review is already in the sheet.
    predecessor = entries_by_number.get(attempt - 1)
    if predecessor is None:
        return
    for pred_record in predecessor.get("reviews") or []:
        if pred_record.get("superseded_by") is not None:
            continue  # only the active record of a lineage participates
        if lineage_key(pred_record) != lineage_key(record):
            continue  # carry-over is scoped per lineage, never per skill alone
        if "findings" in pred_record:
            pred_record["open_after_this_attempt"] = count_open_findings(pred_record["findings"], record["findings"])


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


def run_review_score(run_dir: Path, slice_num: int, skill: str, sheet_path: Path) -> list[str]:
    """End-to-end: select every commission of this slice+skill, then verify,
    parse and upsert each in ascending `event_index` order (Stage 4a).

    Deterministic by construction: `select_review_commissions` is computed
    once, before any sheet mutation, from the full event log -- a rerun
    against the same (only ever growing) log selects the identical
    commission list and performs the identical upserts, so re-running this
    function produces the same sheet content rather than depending on a
    skip-guard to avoid reprocessing. Each commission's upsert is written to
    disk immediately, one at a time -- not batched into a single write at
    the end -- so a failure partway through a backlog never loses the
    commissions already harvested before it.

    **A commission whose attempt has no sheet row is skipped, not fatal
    (2026-09-11, real defect found by independent review of the post-hoc
    grading redesign; still holds verbatim under the commission-per-record
    schema).** `tools/grade_run.py` only ever creates a sheet row for each
    slice's FINAL attempt (a deliberate, documented scope limit -- a
    superseded attempt's own commit isn't recoverable post-hoc), so under
    that caller a row is now the *normal* case for exactly one attempt, not
    every one. This function must never raise the instant it hits the first
    missing row, in ascending order -- doing so would mean one superseded
    attempt's missing row silently aborts the harvest for every LATER
    attempt too, including the final one this bench actually needs, before
    it is ever reached. Confirmed empirically once, pre-Stage-4a: a real
    graded run's final, accepted attempt had neither `drift_review` nor
    `code_review` populated at all, even though both reviews existed and
    were independently harvestable. Each commission is attempted
    independently; a missing row is recorded as a returned problem string
    and processing continues to every other commission in the list.

    Returns:
        A problem string per commission that could not be harvested because
        its attempt's sheet row doesn't exist (empty list if every
        commission was harvested successfully). Any OTHER failure (a
        malformed report, a sha256 mismatch, missing run_id/events) still
        raises `ReviewScoreError` immediately -- those indicate a genuine
        data problem worth stopping on, not the expected shape of this
        scope limit.
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

    commissions = select_review_commissions(events, slice_id, skill)
    sheet = read_json(sheet_path)
    # finding 5: refuse to read into (and, below, write into) another run's
    # or slice's sheet -- the same guard dev_check.py applies to --out.
    try:
        bench_lib.validate_sheet_identity(sheet, run_id, slice_num, sheet_path)
    except bench_lib.BenchLibError as exc:
        raise ReviewScoreError(str(exc)) from exc

    problems: list[str] = []
    for commission in commissions:
        attempt = commission["attempt"]
        event_index = commission["event_index"]
        review_event = commission["event"]

        # Checked before doing any of this commission's work, not just
        # before upsert_sheet's own guard: a missing row is this scope
        # limit's normal, expected shape now, not a reason to abort every
        # commission after it (see this function's docstring).
        entries_by_number = {e.get("attempt"): e for e in sheet.get("attempts") or []}
        if attempt not in entries_by_number:
            problems.append(
                f"slice {slice_id!r} attempt {attempt}: no scoring-sheet row to attach its {skill} review "
                f"(event_index={event_index}) to (this attempt was never graded -- only a slice's final "
                "attempt is, per tools/grade_run.py)"
            )
            continue

        evidence = review_event.get("evidence")
        if not evidence:
            raise ReviewScoreError(f"review event for slice {slice_id!r} has no 'evidence' path")

        run_review = find_run_review_entry(run_state, slice_id, skill, evidence)
        expected_sha256 = run_review["sha256"]

        verify_report_sha256(Path(evidence), expected_sha256)
        report_text = Path(evidence).read_text(encoding="utf-8")
        parsed = parse_report(skill, report_text)
        record = build_record(
            review_id=run_review.get("review_id"),
            event_index=event_index,
            skill=skill,
            tool=run_review.get("tool"),
            model=run_review.get("model"),
            effort=run_review.get("effort"),
            head=run_review.get("head"),
            before_head=run_review.get("before_head"),
            grants_seen=run_review.get("grants_seen"),
            at=run_review.get("at"),
            report_ref=evidence,
            report_sha256=expected_sha256,
            parsed=parsed,
        )

        upsert_sheet(sheet, attempt, record)
        write_sheet_atomically(sheet_path, sheet)

    return problems


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
        problems = run_review_score(run_dir, args.slice, args.skill, sheet_path)
    except ReviewScoreError as exc:
        print(f"review_score: error: {exc}", file=sys.stderr)
        sys.exit(1)

    if problems:
        for problem in problems:
            print(f"review_score: warning: {problem}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
