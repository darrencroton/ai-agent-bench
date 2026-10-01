#!/usr/bin/env python3
"""Commission the labelled, subjective quality panel for one graded slice attempt.

After a run is graded, this tool asks one fixed read-only reviewer
configuration (policy.yaml's `quality_panel` block: one tool, model and
effort) to read a slice attempt's commit against the frozen plan and return
five 1-5 scores with `path:line` evidence, using the fixed rubric in
`quality_panel.rubric_file`. The result is appended as one record to that
attempt's `quality_panel` list on the scoring sheet.

The scores are a model's judgement, not a measurement: they are not
repeatable the way a test is, so they are surfaced in their own labelled
table and never enter correctness, kill rate or any rank (AGENTS.md:
"deterministic first"). One record per commission, never overwritten: a
repeat commission against the same attempt appends a second record, which is
exactly what makes the panel's repeatability visible. Every record carries
the reviewer's identity, the rubric's sha256 and the sha256 of the prompt
the launcher actually rendered, so a mid-cohort configuration swap or rubric
edit is visible on the record rather than hidden. `rubric_sha256` is the
cross-commission comparable identity; `prompt_sha256` pins the exact prompt
delivered, which also embeds that commission's commits and worktree path.

Boundaries. This tool never invokes a harness directly: it drives the
orchestrator skill's own `delegate_jobs.py` (`init`, `launch`, one `wait`,
`extract`), which validates the read-only contract and records the launch
evidence under `quality_panel.artifact_root`. It never touches PM state
(run.json is read only for the same task cross-checks dev_check.py applies)
and never reads or writes the Developer's directory: the reviewer works in a
disposable worktree at the attempt's commit (`dev_check.grading_worktree`),
with no hidden test copied in, and the worktree is removed afterwards.
Grading must already have happened (the commit and base come from the sheet),
so like grading this is strictly post-hoc.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import bench_lib
import dev_check

SCORE_KEYS = (
    "correctness_beyond_tests",
    "design",
    "readability_docs",
    "tests",
    "contract_discipline",
)
_SECTIONS = ("SCORES", "EVIDENCE", "SUMMARY")
SCORE_MIN, SCORE_MAX = 1, 5

# The reviewer's output contract, sent as the request's `expected_output`.
# docs/QUALITY-PANEL-RUBRIC.md states the same block verbatim (a test pins
# the two together), and parse_panel_output below accepts exactly this shape.
OUTPUT_CONTRACT = (
    "SECTION: SCORES\n"
    + "".join(f"{key}: <1-5>\n" for key in SCORE_KEYS)
    + "SECTION: EVIDENCE\n"
    "- <path:line> -- <one line>\n"
    "SECTION: SUMMARY\n"
    "<at most five sentences>"
)

_CONTEXT = (
    "This repository is checked out read-only at a Developer's commit implementing one slice of a frozen "
    "implementation plan. Evaluate how well that slice was implemented, against the plan's own contract for it. "
    "You are an evaluator only: do not propose, make or describe changes."
)
_CONSTRAINTS = [
    "Read-only: do not edit, create or delete any file; reading files and running `git diff`, `git show` and "
    "`git log` are permitted.",
    "Cite path:line evidence for every score.",
    "Answer only in the output contract: the three SECTION blocks, with nothing before or after them.",
]

# Same tolerance as delegate_jobs.py's own SECTION_RE (a model may prefix a
# header with Markdown `#`), so a header the launcher's contract check
# accepted is never rejected here for formatting alone. Everything inside a
# section is parsed strictly.
_SECTION_HEADER_RE = re.compile(r"^\s*(?:#+\s*)?SECTION:\s*([A-Za-z0-9_ -]+?)\s*$")
_SCORE_LINE_RE = re.compile(r"^([a-z_]+):\s*(\S+)$")
_LIST_ITEM_RE = re.compile(r"^-\s+(.*\S)$")


class QualityPanelError(bench_lib.BenchLibError):
    """A loud, specific failure; nothing is written to the sheet when raised."""


# --- policy ------------------------------------------------------------


def load_policy(policy_path: Path, root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """dev_check.load_policy for the shared keys, plus this tool's own block.

    Returns:
        The parsed policy and the validated `quality_panel` configuration,
        with `rubric_path`, `scripts_dir` and `artifact_root` resolved to
        absolute paths (`~` expanded; relative paths against `root`).

    Raises:
        QualityPanelError: the block is missing or not a mapping, a string key
            is missing or empty, the rubric file does not exist, or
            `timeout_seconds` is not a positive integer -- each naming the key.
    """
    try:
        policy = dev_check.load_policy(policy_path)
    except bench_lib.BenchLibError as exc:
        raise QualityPanelError(str(exc)) from exc
    block = policy.get("quality_panel")
    if not isinstance(block, dict):
        raise QualityPanelError(
            f"policy file {policy_path} has no quality_panel mapping"
        )
    for key in (
        "tool",
        "model",
        "effort",
        "rubric_file",
        "orchestrator_scripts_dir",
        "artifact_root",
    ):
        value = block.get(key)
        if not isinstance(value, str) or not value.strip():
            raise QualityPanelError(
                f"policy file {policy_path}: quality_panel.{key} must be a non-empty string, got {value!r}"
            )
    timeout = block.get("timeout_seconds")
    if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout <= 0:
        raise QualityPanelError(
            f"policy file {policy_path}: quality_panel.timeout_seconds must be a positive integer, got {timeout!r}"
        )
    rubric_path = (root / Path(block["rubric_file"]).expanduser()).resolve()
    if not rubric_path.is_file():
        raise QualityPanelError(
            f"policy file {policy_path}: quality_panel.rubric_file {rubric_path} does not exist"
        )
    panel = {
        "tool": block["tool"],
        "model": block["model"],
        "effort": block["effort"],
        "rubric_file": block["rubric_file"],
        "rubric_path": rubric_path,
        "scripts_dir": Path(block["orchestrator_scripts_dir"]).expanduser().resolve(),
        "artifact_root": (root / Path(block["artifact_root"]).expanduser()).resolve(),
        "timeout_seconds": timeout,
    }
    return policy, panel


# --- pure builders and parsers -------------------------------------------


def delegate_label(tool: str) -> str:
    return f"01-{tool}-quality-panel"


def build_delegate_policy(
    *,
    run_id: str,
    slice_id: str,
    plan_sha256: str,
    worktree: Path,
    panel: dict[str, Any],
) -> dict[str, Any]:
    """The schema-v3 delegate-policy.json authorizing exactly one read-only reviewer."""
    return {
        "schema_version": 3,
        "run_id": run_id,
        "slice_id": slice_id,
        "plan_sha256": plan_sha256,
        "repo_path": str(worktree),
        "delegate_artifact_root": str(panel["artifact_root"]),
        "required_tools": [panel["tool"]],
        "required_model": panel["model"],
        "required_effort": panel["effort"],
        "required_access": ["read-only"],
    }


def build_delegate_request(
    *,
    slice_id: str,
    plan_sha256: str,
    plan_file: str,
    rubric_text: str,
    commit: str,
    before_head: str,
    panel: dict[str, Any],
) -> dict[str, Any]:
    """The schema-v3 delegate-request.json: the rubric plus this attempt's concrete coordinates."""
    task = (
        f"{rubric_text.rstrip()}\n\n"
        f"Slice under review: {slice_id} of the plan file {plan_file}.\n"
        f"Commit under review: {commit}\n"
        f"Base commit (before_head): {before_head}\n"
        f"Read the change with: git diff {before_head} {commit}"
    )
    return {
        "schema_version": 3,
        "label": delegate_label(panel["tool"]),
        "slice_id": slice_id,
        "plan_sha256": plan_sha256,
        "tool": panel["tool"],
        "model": panel["model"],
        "effort": panel["effort"],
        "access": "read-only",
        "task": task,
        "context": _CONTEXT,
        "required_skills": [],
        "files": [plan_file],
        "constraints": list(_CONSTRAINTS),
        "expected_output": OUTPUT_CONTRACT,
    }


def parse_panel_output(text: str) -> dict[str, Any]:
    """Parse the extracted SCORES/EVIDENCE/SUMMARY blocks, strictly.

    SCORES must carry each of SCORE_KEYS exactly once as `key: N` with an
    integer N in 1-5 and nothing else; EVIDENCE must list at least one
    `- ...` item; SUMMARY must be non-empty. Text outside the three sections
    and blank lines are ignored.

    Raises:
        QualityPanelError: naming the section and the offending line or key.
    """
    sections: dict[str, list[str]] = {}
    current: list[str] | None = None
    for line in text.splitlines():
        header = _SECTION_HEADER_RE.match(line)
        if header:
            name = header.group(1).strip().upper().replace(" ", "_").replace("-", "_")
            if name in sections:
                raise QualityPanelError(
                    f"reviewer output has SECTION: {name} more than once"
                )
            current = sections[name] = []
        elif current is not None and line.strip():
            current.append(line.strip())
    missing = [name for name in _SECTIONS if name not in sections]
    if missing:
        raise QualityPanelError(
            f"reviewer output is missing section(s): {', '.join(missing)}"
        )

    scores: dict[str, int] = {}
    for line in sections["SCORES"]:
        match = _SCORE_LINE_RE.match(line)
        if not match:
            raise QualityPanelError(f"SCORES line {line!r} is not `<dimension>: <1-5>`")
        key, raw = match.groups()
        if key not in SCORE_KEYS:
            raise QualityPanelError(
                f"SCORES names unknown dimension {key!r}; expected {', '.join(SCORE_KEYS)}"
            )
        if key in scores:
            raise QualityPanelError(f"SCORES gives dimension {key!r} more than once")
        if not raw.isdigit() or not SCORE_MIN <= int(raw) <= SCORE_MAX:
            raise QualityPanelError(
                f"SCORES {key!r} is {raw!r}, not an integer {SCORE_MIN}-{SCORE_MAX}"
            )
        scores[key] = int(raw)
    absent = [key for key in SCORE_KEYS if key not in scores]
    if absent:
        raise QualityPanelError(f"SCORES is missing dimension(s): {', '.join(absent)}")

    evidence: list[str] = []
    for line in sections["EVIDENCE"]:
        match = _LIST_ITEM_RE.match(line)
        if not match:
            raise QualityPanelError(
                f"EVIDENCE line {line!r} is not a `- <path:line> -- <one line>` item"
            )
        evidence.append(match.group(1))
    if not evidence:
        raise QualityPanelError(
            "EVIDENCE lists no items; every score must cite path:line evidence"
        )
    if not sections["SUMMARY"]:
        raise QualityPanelError("SUMMARY is empty")
    return {
        "scores": {key: scores[key] for key in SCORE_KEYS},
        "evidence": evidence,
        "summary": " ".join(sections["SUMMARY"]),
    }


def build_record(
    *,
    panel: dict[str, Any],
    rubric_sha256: str,
    prompt_sha256: str,
    delegate_run_dir: Path,
    commit_sha: str,
    before_head: str,
    parsed: dict[str, Any],
    at: str,
) -> dict[str, Any]:
    """One `quality_panel` list record -- one per commission, never rewritten."""
    return {
        "tool": panel["tool"],
        "model": panel["model"],
        "effort": panel["effort"],
        "rubric_file": panel["rubric_file"],
        "rubric_sha256": rubric_sha256,
        "prompt_sha256": prompt_sha256,
        "delegate_run_dir": str(delegate_run_dir),
        "label": delegate_label(panel["tool"]),
        "at": at,
        "commit_sha": commit_sha,
        "before_head": before_head,
        "scores": parsed["scores"],
        "evidence": parsed["evidence"],
        "summary": parsed["summary"],
    }


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# --- sheet ---------------------------------------------------------------


def select_attempt(
    sheet: dict[str, Any], requested: int | None, sheet_path: Path
) -> dict[str, Any]:
    """The attempt row to review: `requested`, else the sheet's accepted attempt.

    Raises:
        QualityPanelError: no `requested` and no accepted attempt (the panel
            reads an accepted commit by default), the row is missing, or it
            lacks a `commit_sha` or `provenance.base_commit`.
    """
    attempt = requested if requested is not None else sheet.get("accepted_at_attempt")
    if attempt is None:
        raise QualityPanelError(
            f"scoring sheet {sheet_path} records no accepted attempt and no --attempt was given; the panel reads "
            "an accepted commit by default"
        )
    row = next(
        (
            entry
            for entry in sheet.get("attempts") or []
            if entry.get("attempt") == attempt
        ),
        None,
    )
    if row is None:
        raise QualityPanelError(
            f"scoring sheet {sheet_path} has no attempt {attempt} row; grade that attempt first"
        )
    commit = row.get("commit_sha")
    base = (row.get("provenance") or {}).get("base_commit")
    if (
        not isinstance(commit, str)
        or not commit
        or not isinstance(base, str)
        or not base
    ):
        raise QualityPanelError(
            f"scoring sheet {sheet_path} attempt {attempt} lacks commit_sha ({commit!r}) or provenance.base_commit "
            f"({base!r})"
        )
    return row


# --- orchestrator ---------------------------------------------------------


def _delegate_jobs(
    scripts_dir: Path, artifact_root: Path, *args: str
) -> subprocess.CompletedProcess[str]:
    script = scripts_dir / "delegate_jobs.py"
    if not script.is_file():
        raise QualityPanelError(
            f"orchestrator launcher not found: {script} (policy quality_panel.orchestrator_scripts_dir)"
        )
    env = {**os.environ, "ORCHESTRATOR_ARTIFACT_ROOT": str(artifact_root)}
    return subprocess.run(
        [sys.executable, str(script), *args],
        check=False,
        capture_output=True,
        text=True,
        env=env,
        cwd=str(artifact_root),
    )


def _output(result: subprocess.CompletedProcess[str]) -> str:
    return (result.stdout.strip() + "\n" + result.stderr.strip()).strip()


def commission_panel(
    scripts_dir: Path,
    artifact_root: Path,
    delegate_policy: dict[str, Any],
    delegate_request: dict[str, Any],
    timeout_seconds: int,
) -> dict[str, Any]:
    """Run one read-only delegate through delegate_jobs.py: init, launch, wait, extract.

    ORCHESTRATOR_ARTIFACT_ROOT is set to `artifact_root` on every call, which
    is both where `init` creates the run directory and what `launch` requires
    the run directory to live under (it must equal the policy's
    `delegate_artifact_root`). A `wait` failure -- a failed, timed-out or
    `incomplete` delegate (a clean exit whose output never met the SECTION
    contract) -- cancels the delegate, so it never outlives the disposable
    worktree it was launched in, and is raised naming the run directory.

    Returns:
        `run_dir`, `prompt_sha256` (of the launcher's rendered
        `<label>-prompt.md`) and `text` (the extracted sections).
    """
    artifact_root.mkdir(parents=True, exist_ok=True)
    init = _delegate_jobs(
        scripts_dir, artifact_root, "init", "--prefix", "quality-panel"
    )
    lines = init.stdout.strip().splitlines()
    if init.returncode != 0 or not lines:
        raise QualityPanelError(
            f"delegate_jobs.py init failed (exit {init.returncode}): {_output(init)}"
        )
    run_dir = Path(lines[-1]).resolve()
    if artifact_root not in run_dir.parents:
        raise QualityPanelError(
            f"delegate_jobs.py init created {run_dir}, outside the artifact root {artifact_root}"
        )

    label = delegate_request["label"]
    policy_path = run_dir / "delegate-policy.json"
    request_path = run_dir / "delegate-request.json"
    bench_lib.write_json_atomically(policy_path, delegate_policy)
    bench_lib.write_json_atomically(request_path, delegate_request)

    launch = _delegate_jobs(
        scripts_dir,
        artifact_root,
        "launch",
        "--run-dir",
        str(run_dir),
        "--policy",
        str(policy_path),
        "--request",
        str(request_path),
    )
    if launch.returncode != 0:
        raise QualityPanelError(
            f"delegate_jobs.py launch refused or failed (exit {launch.returncode}) in {run_dir}: {_output(launch)}"
        )
    prompt_path = run_dir / f"{label}-prompt.md"
    if not prompt_path.is_file():
        raise QualityPanelError(
            f"delegate_jobs.py launch left no rendered prompt at {prompt_path}"
        )
    prompt_sha256 = sha256_file(prompt_path)

    wait = _delegate_jobs(
        scripts_dir,
        artifact_root,
        "wait",
        "--run-dir",
        str(run_dir),
        "--label",
        label,
        "--timeout",
        str(timeout_seconds),
    )
    if wait.returncode != 0:
        _delegate_jobs(
            scripts_dir,
            artifact_root,
            "cancel",
            "--run-dir",
            str(run_dir),
            "--label",
            label,
        )
        raise QualityPanelError(
            f"quality-panel delegate did not complete cleanly (wait exit {wait.returncode}) in {run_dir}: {_output(wait)}"
        )
    extract = _delegate_jobs(
        scripts_dir,
        artifact_root,
        "extract",
        "--run-dir",
        str(run_dir),
        "--label",
        label,
        "--sections",
        ",".join(_SECTIONS),
    )
    if extract.returncode != 0:
        raise QualityPanelError(
            f"delegate_jobs.py extract failed (exit {extract.returncode}) in {run_dir}: {_output(extract)}"
        )
    return {"run_dir": run_dir, "prompt_sha256": prompt_sha256, "text": extract.stdout}


# --- CLI -----------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--run-dir",
        required=True,
        type=Path,
        help="PM run state directory containing run.json",
    )
    parser.add_argument(
        "--slice", required=True, type=int, help="slice number N (PM's 'Slice N')"
    )
    parser.add_argument(
        "--attempt",
        type=int,
        default=None,
        help="graded attempt to review (default: the sheet's accepted attempt)",
    )
    parser.add_argument(
        "--task",
        default=None,
        help="task id from the policy's tasks: registry (default: default_task)",
    )
    parser.add_argument(
        "--policy",
        type=Path,
        default=None,
        help="policy file (default: policy.yaml at this repo's root)",
    )
    parser.add_argument(
        "--sheet",
        type=Path,
        default=None,
        help="scoring sheet (default: results/runs/<run_id>/slice-<N>.json)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = dev_check.bench_root()
    policy_path = (args.policy or (root / "policy.yaml")).expanduser().resolve()
    policy, panel = load_policy(policy_path, root)
    try:
        task = bench_lib.resolve_task(policy, args.task)
    except bench_lib.BenchLibError as exc:
        raise QualityPanelError(str(exc)) from exc

    # The same cross-checks dev_check.main applies before grading: the run
    # must belong to the task, and its recorded plan must be the task's plan.
    run_dir = args.run_dir.expanduser().resolve()
    run_state = dev_check.load_run_state(run_dir)
    repo = dev_check.check_run_belongs_to_task(run_state, task, root)
    dev_check.check_plan_matches_task(run_state, task, repo)
    run_id = run_state["run_id"]

    sheet_path = (
        (
            args.sheet
            or (root / "results" / "runs" / run_id / f"slice-{args.slice}.json")
        )
        .expanduser()
        .resolve()
    )
    sheet = dev_check.load_existing_sheet(sheet_path, run_id, args.slice)
    if sheet is None:
        raise QualityPanelError(
            f"no scoring sheet at {sheet_path}; grade the run first (tools/grade_run.py)"
        )
    dev_check.check_regrade_task_identity(
        sheet, task["task_id"], policy["default_task"]
    )
    row = select_attempt(sheet, args.attempt, sheet_path)
    attempt, commit, before_head = (
        row["attempt"],
        row["commit_sha"],
        row["provenance"]["base_commit"],
    )

    slice_id = f"Slice {args.slice}"
    rubric_text = panel["rubric_path"].read_text(encoding="utf-8")
    rubric_sha256 = sha256_file(panel["rubric_path"])
    with dev_check.grading_worktree(repo, commit, policy) as worktree:
        plan_path = worktree / task["plan_file"]
        if not plan_path.is_file():
            raise QualityPanelError(
                f"plan file {task['plan_file']!r} is not present at commit {commit} ({plan_path})"
            )
        plan_sha256 = sha256_file(plan_path)
        result = commission_panel(
            panel["scripts_dir"],
            panel["artifact_root"],
            build_delegate_policy(
                run_id=run_id,
                slice_id=slice_id,
                plan_sha256=plan_sha256,
                worktree=worktree,
                panel=panel,
            ),
            build_delegate_request(
                slice_id=slice_id,
                plan_sha256=plan_sha256,
                plan_file=task["plan_file"],
                rubric_text=rubric_text,
                commit=commit,
                before_head=before_head,
                panel=panel,
            ),
            panel["timeout_seconds"],
        )
    try:
        parsed = parse_panel_output(result["text"])
    except QualityPanelError as exc:
        raise QualityPanelError(f"{exc} (delegate run {result['run_dir']})") from exc

    record = build_record(
        panel=panel,
        rubric_sha256=rubric_sha256,
        prompt_sha256=result["prompt_sha256"],
        delegate_run_dir=result["run_dir"],
        commit_sha=commit,
        before_head=before_head,
        parsed=parsed,
        at=dev_check.utc_now_iso(),
    )
    # Re-read the sheet: a delegate session can take an hour, and another
    # tool may have written it meanwhile. Append onto the fresh copy, and
    # refuse if the attempt now names a different commit than was reviewed.
    # Only `commit_sha` is compared: a same-commit re-grade that landed
    # during the session is accepted and this record is appended onto its
    # row. No lock is held, so a re-grade written between this re-read and
    # the replace below would be overwritten -- its re-graded blocks, not any
    # panel record, are what would be lost.
    fresh = dev_check.load_existing_sheet(sheet_path, run_id, args.slice)
    fresh_row = next(
        (
            entry
            for entry in (fresh or {}).get("attempts") or []
            if entry.get("attempt") == attempt
        ),
        None,
    )
    if fresh_row is None or fresh_row.get("commit_sha") != commit:
        raise QualityPanelError(
            f"scoring sheet {sheet_path} attempt {attempt} changed while the panel ran (reviewed {commit}); "
            f"nothing written (delegate run {result['run_dir']})"
        )
    fresh_row.setdefault("quality_panel", []).append(record)
    bench_lib.write_json_atomically(sheet_path, fresh)

    for key in SCORE_KEYS:
        print(f"{key}: {parsed['scores'][key]}")
    print(
        f"recorded on {sheet_path} (attempt {attempt} of {slice_id}); delegate run {result['run_dir']}"
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except bench_lib.BenchLibError as exc:
        print(f"quality_panel.py: error: {exc}", file=sys.stderr)
        sys.exit(1)
