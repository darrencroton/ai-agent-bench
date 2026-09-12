#!/usr/bin/env python3
"""Operator convenience wrapper around the five scoring tools
(docs/MODE2-REWRITE-PLAN.md §6, "Tool 6"): `setup` prints a ready-to-paste
Mode B launcher prompt and the steps to follow; `analyze` runs
`grade_run.py` -> `model_report.py` -> `leaderboard.py` in one command once
a run is finished; `cleanup` archives (never deletes) old `results/`
output.

This module never launches PM, never writes into a Developer/PM directory,
and never talks to a run in progress -- the same read-only, PM-is-never-
instrumented boundary every other tool in this repo holds (AGENTS.md,
docs/MODE2-REWRITE-PLAN.md §2). `setup`'s prompt text is extracted, verbatim
and read-only, from project-manager's own `SKILL.md` -- never a hardcoded
copy that could silently drift from what that skill actually asks for.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import bench_lib
import dev_check
import grade_run
import leaderboard
import model_report


class CohortRunError(bench_lib.BenchLibError):
    """Raised for every condition this tool must fail loudly on.

    main() catches exactly this exception type, prints it, and exits 1 --
    matching every other tool's own __main__ pattern. A subprocess tool
    (grade_run.py/model_report.py/leaderboard.py) raising its own
    bench_lib.BenchLibError subclass is caught separately, at the call
    site -- see _call_tool -- rather than re-wrapped as this type, so the
    failing tool's own name stays in the message.
    """


def bench_root() -> Path:
    """Absolute path to this repo's root -- see bench_lib.repo_root()."""
    try:
        return bench_lib.repo_root()
    except bench_lib.BenchLibError as exc:
        raise CohortRunError(str(exc)) from exc


# --- setup ----------------------------------------------------------------


def extract_launcher_template(skill_md: Path) -> str:
    """Pull project-manager's own launcher prompt out of its `SKILL.md`,
    verbatim: the fenced code block under its `## Launcher` heading.

    Read live from disk on every call rather than vendored, deliberately --
    unlike the frozen plan (G8), the launcher's *wording* is not something
    this bench scores, so a stale copy would only mislead an operator about
    what project-manager currently asks for, never protect a measurement.

    Raises:
        CohortRunError: no `## Launcher` heading, or no fenced code block
            under it -- never a stale fallback.
    """
    text = skill_md.read_text(encoding="utf-8")
    heading_idx = text.find("## Launcher")
    if heading_idx == -1:
        raise CohortRunError(f"{skill_md} has no '## Launcher' section; cannot extract the launcher prompt")
    section_start = heading_idx + len("## Launcher")
    next_heading_idx = text.find("\n## ", section_start)
    section = text[section_start : next_heading_idx if next_heading_idx != -1 else len(text)]
    match = re.search(r"```(?:md)?\n(.*?)\n```", section, re.DOTALL)
    if not match:
        raise CohortRunError(f"{skill_md} has a '## Launcher' section but no fenced code block under it")
    return match.group(1)


def render_launcher_prompt(
    template: str,
    *,
    plan_file: str | None = None,
    repo: str | None = None,
    harness: str | None = None,
    model: str | None = None,
) -> tuple[str, set[str]]:
    """Fill in whichever of the launcher template's bracketed gaps the
    caller supplied, leaving every other gap exactly as project-manager's
    own template states it -- so the printed prompt is always safe to
    paste, filled or not.

    There is deliberately no reviewer-seat gap to fill: PM commissions
    whichever reviewer tool/model it judges right per slice, on its own
    judgement, and policy.yaml carries no reviewer-seat key for the same
    reason (see policy.yaml's own comment on this).

    Returns:
        The rendered prompt, and the set of gap names actually substituted
        (a caller can compare this against which arguments it was given, to
        warn if the template's own wording moved out from under a
        substitution -- see run_setup).
    """
    substituted: set[str] = set()
    lines = []
    for line in template.splitlines():
        if line.startswith("Plan file:") and plan_file:
            lines.append(f"Plan file: {plan_file}")
            substituted.add("plan_file")
        elif line.startswith("Repo:") and repo:
            lines.append(f"Repo: {repo}")
            substituted.add("repo")
        elif line.startswith("Harness:") and (harness or model):
            harness_token = harness or "<codex|claude|copilot|opencode|qwen>"
            model_clause = f"(model {model})" if model else "(optionally: model <model name>)"
            lines.append(f"Harness: {harness_token} {model_clause}")
            if harness:
                substituted.add("harness")
            if model:
                substituted.add("model")
        else:
            lines.append(line)
    return "\n".join(lines), substituted


_SETUP_STEPS = """\
Steps to follow:

  1. Copy the prompt block below into a brand-new PM-capable session (a
     fresh Claude Code, Codex CLI, or equivalent session -- NOT this one,
     and not one already mid-task). Fill in any remaining <...> gaps by
     hand first.
  2. Send it, then let PM supervise the run entirely on its own to
     completion. This repo has no code path that launches PM and never
     will -- do not paste anything else into that session on this repo's
     behalf, and never put PM_RUN_TOKEN anywhere this repo can read it.
  3. When PM is done -- run.json["status"] is "complete", or "stopped" with
     PM's own closing event on record ("needs-human" is a pause, not a
     finish) -- find its authoritative run directory: it is
     <worktree-git-dir>/pm/<run-id>/ (PM prints this at `init`/`start-run`;
     or derive <worktree-git-dir> yourself with
     `git -C <dev-repo> rev-parse --absolute-git-dir` in the Developer's
     repo -- the in-worktree .pm/ copy is a mirror, not the authority).
  4. Grade it end to end in one command:

       python tools/cohort_run.py analyze --run-dir <pm-run-dir>

     (or `--dev-repo <dev-repo>` instead of `--run-dir`, if there is
     exactly one run under that repo's PM state). This runs grade_run.py,
     then model_report.py, then leaderboard.py, and reports the result.
  5. Check results/leaderboard.json. analyze is idempotent -- re-run it any
     time, including after a later cohort member finishes, to refold the
     leaderboard.
"""


def load_policy(policy_path: Path) -> dict[str, Any]:
    """`setup`'s own policy validation -- reuses dev_check.py's (this tool
    needs no key of its own beyond `pm_scripts_dir`, which dev_check.py
    already requires), wrapped into this module's own error type so a bad
    policy.yaml fails as `cohort_run.py: error: ...` like every other
    failure path here, not an unhandled dev_check.DevCheckError traceback.
    """
    try:
        return dev_check.load_policy(policy_path)
    except dev_check.DevCheckError as exc:
        raise CohortRunError(str(exc)) from exc


def run_setup(args: argparse.Namespace, root: Path) -> int:
    policy_path = (args.policy or (root / "policy.yaml")).expanduser().resolve()
    policy = load_policy(policy_path)
    skill_root = Path(policy["pm_scripts_dir"]).expanduser().resolve().parent
    skill_md = skill_root / "SKILL.md"
    if not skill_md.is_file():
        raise CohortRunError(
            f"project-manager's SKILL.md not found at {skill_md} (derived from policy.yaml's "
            f"pm_scripts_dir={policy['pm_scripts_dir']!r}); is pm_scripts_dir still correct?"
        )
    template = extract_launcher_template(skill_md)
    prompt, substituted = render_launcher_prompt(
        template, plan_file=args.plan_file, repo=args.repo, harness=args.harness, model=args.model
    )
    for name, value in (("plan_file", args.plan_file), ("repo", args.repo), ("harness", args.harness), ("model", args.model)):
        if value and name not in substituted:
            print(
                f"cohort_run.py: warning: --{name.replace('_', '-')} was given but the launcher template has no "
                f"matching '{name}' line to fill -- add it by hand below",
                file=sys.stderr,
            )

    print(_SETUP_STEPS)
    print(
        "Note: there is no reviewer gap above -- PM commissions whichever reviewer tool/model it judges "
        "right per slice, on its own judgement (see policy.yaml's comment on this). Nothing to fill in for it.\n"
    )
    print("Prompt to paste (fill in any remaining <...> gaps):\n")
    print("```md")
    print(prompt)
    print("```")
    return 0


# --- analyze ----------------------------------------------------------------


def resolve_run_dir_from_dev_repo(dev_repo: Path) -> Path:
    """The one PM run directory under `<dev_repo>`'s git dir, per
    docs/MODE2-REWRITE-PLAN.md §4: `<worktree-git-dir>/pm/<run-id>/`.

    Refuses, naming every candidate, rather than guessing "the latest one"
    when more than one run directory exists -- the same "never default to a
    guess" discipline every other tool in this repo already holds.
    """
    result = subprocess.run(
        ["git", "-C", str(dev_repo), "rev-parse", "--absolute-git-dir"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise CohortRunError(
            f"`git -C {dev_repo} rev-parse --absolute-git-dir` failed: {result.stderr.strip() or result.returncode}"
        )
    pm_root = Path(result.stdout.strip()) / "pm"
    if not pm_root.is_dir():
        raise CohortRunError(f"no {pm_root} directory -- has PM ever run against {dev_repo}?")
    candidates = sorted(p for p in pm_root.iterdir() if p.is_dir())
    if not candidates:
        raise CohortRunError(f"{pm_root} exists but has no run directories")
    if len(candidates) > 1:
        listing = "\n".join(f"  - {candidate}" for candidate in candidates)
        raise CohortRunError(
            f"{pm_root} has {len(candidates)} run directories; pass --run-dir explicitly to pick one:\n{listing}"
        )
    return candidates[0]


def _read_run_id(run_dir: Path) -> str:
    run_json = run_dir / "run.json"
    if not run_json.is_file():
        raise CohortRunError(
            f"no run.json under --run-dir {run_dir}; pass PM's authoritative run directory "
            "(<worktree-git-dir>/pm/<run-id>/), not the in-worktree .pm/ mirror"
        )
    try:
        run_state = json.loads(run_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CohortRunError(f"{run_json} is not valid JSON: {exc}") from exc
    if not isinstance(run_state, dict) or not run_state.get("run_id"):
        raise CohortRunError(f"{run_json} did not parse to an object with a non-empty 'run_id' field")
    return run_state["run_id"]


def _call_tool(main_fn: Any, label: str, argv: list[str]) -> int:
    """Call one tool's own main(argv) directly (never a subprocess -- this
    mirrors how grade_run.py already calls dev_check.main() and
    review_score.run_review_score() in-process), catching only that tool's
    own bench_lib.BenchLibError so a hard refusal is reported and this
    pipeline continues to whichever later steps are still meaningful,
    rather than the whole command crashing.
    """
    print(f"cohort_run.py: running {label} {' '.join(argv)}")
    try:
        code = main_fn(argv)
    except bench_lib.BenchLibError as exc:
        print(f"cohort_run.py: {label} refused: {exc}", file=sys.stderr)
        return 1
    if code:
        print(f"cohort_run.py: {label} exited {code} (see warnings above)", file=sys.stderr)
    return code


def run_analyze(args: argparse.Namespace) -> int:
    run_dir = (args.run_dir or resolve_run_dir_from_dev_repo(args.dev_repo)).expanduser().resolve()
    run_id = _read_run_id(run_dir)

    grade_argv = ["--run-dir", str(run_dir)]
    if args.policy:
        grade_argv += ["--policy", str(args.policy)]
    codes = [_call_tool(grade_run.main, "grade_run.py", grade_argv)]

    codes.append(_call_tool(model_report.main, "model_report.py", ["--run-id", run_id]))

    if args.skip_leaderboard:
        print("cohort_run.py: --skip-leaderboard set; not refolding results/leaderboard.json")
    else:
        board_argv = []
        if args.policy:
            board_argv += ["--policy", str(args.policy)]
        codes.append(_call_tool(leaderboard.main, "leaderboard.py", board_argv))

    exit_code = max(codes)
    print(f"cohort_run.py: analyze finished for run_id={run_id}; exit code {exit_code}")
    return exit_code


# --- cleanup ----------------------------------------------------------------


def run_cleanup(args: argparse.Namespace, root: Path) -> int:
    """Archive (never delete -- AGENTS.md's "archive, never delete"
    convention) this repo's own regenerable `results/` output, so a fresh
    cohort pass can start clean without losing any prior run's evidence.

    Dry-run by default: lists what would move and where, and does nothing
    until `--yes` is given. Nothing here is git-tracked (`results/` and
    `archive/` are both gitignored), so this is always safely reversible by
    hand even after `--yes`.
    """
    results_dir = (args.results_dir or (root / "results")).expanduser().resolve()
    runs_dir = results_dir / "runs"
    leaderboard_path = results_dir / "leaderboard.json"

    if args.run_id:
        target = runs_dir / args.run_id
        if not target.is_dir():
            raise CohortRunError(f"no results found for run_id={args.run_id!r} under {runs_dir}")
        targets = [target]
    else:
        targets = [path for path in (runs_dir, leaderboard_path) if path.exists()]
        if not targets:
            print(f"cohort_run.py: nothing under {results_dir} to archive")
            return 0

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive_dir = (args.archive_dir or (root / "archive" / f"results-{stamp}")).expanduser().resolve()

    print(f"cohort_run.py: {'archiving' if args.yes else 'would archive'} into {archive_dir}:")
    for target in targets:
        print(f"  - {target}")

    if not args.yes:
        print("cohort_run.py: dry run only -- nothing moved. Pass --yes to actually archive these.")
        return 0

    # Validate every destination before moving any target -- a collision on
    # a later target must never leave an earlier one already moved with no
    # rollback (an operator seeing a raised error should be able to assume
    # nothing happened).
    destinations = [archive_dir / target.name for target in targets]
    collisions = [destination for destination in destinations if destination.exists()]
    if collisions:
        listing = "\n".join(f"  - {collision}" for collision in collisions)
        raise CohortRunError(f"refusing to overwrite existing archive entries:\n{listing}")

    archive_dir.mkdir(parents=True, exist_ok=True)
    for target, destination in zip(targets, destinations, strict=True):
        shutil.move(str(target), str(destination))
    if not args.run_id:
        runs_dir.mkdir(parents=True, exist_ok=True)  # leave results/runs/ ready for the next cohort pass
    print(f"cohort_run.py: archived {len(targets)} item(s) to {archive_dir}")
    return 0


# --- CLI --------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Operator convenience wrapper: `setup` prints project-manager's own launcher prompt (extracted "
            "live, never a stale copy) ready to paste; `analyze` runs grade_run.py -> model_report.py -> "
            "leaderboard.py in one command; `cleanup` archives old results/ output. Never launches PM itself "
            "(docs/MODE2-REWRITE-PLAN.md §2)."
        )
    )
    parser.add_argument("--policy", type=Path, default=None, help="defaults to policy.yaml at this repo's root")
    subparsers = parser.add_subparsers(dest="command", required=True)

    setup_parser = subparsers.add_parser(
        "setup", help="print project-manager's launcher prompt, ready to paste, plus the steps to follow"
    )
    setup_parser.add_argument("--model", default=None, help="candidate Developer model to fill into the Harness line")
    setup_parser.add_argument("--harness", default=None, help="e.g. codex|claude|copilot|opencode|qwen")
    setup_parser.add_argument("--repo", default=None, help="absolute path to the Developer repo/worktree PM will run in")
    setup_parser.add_argument("--plan-file", default=None, help="absolute path to the frozen plan inside that repo")

    analyze_parser = subparsers.add_parser(
        "analyze", help="grade a finished run and fold it into the per-model report and cross-model leaderboard"
    )
    run_dir_group = analyze_parser.add_mutually_exclusive_group(required=True)
    run_dir_group.add_argument("--run-dir", type=Path, default=None, help="PM's authoritative run directory")
    run_dir_group.add_argument(
        "--dev-repo", type=Path, default=None, help="Developer repo/worktree; used only when it has exactly one PM run"
    )
    analyze_parser.add_argument(
        "--skip-leaderboard", action="store_true", help="grade and build the model report, but don't refold the leaderboard"
    )

    cleanup_parser = subparsers.add_parser("cleanup", help="archive (never delete) old results/ output")
    cleanup_parser.add_argument("--run-id", default=None, help="archive only this run's results; default: everything")
    cleanup_parser.add_argument("--results-dir", type=Path, default=None, help="defaults to results/ at this repo's root")
    cleanup_parser.add_argument("--archive-dir", type=Path, default=None, help="defaults to archive/results-<UTC timestamp>")
    cleanup_parser.add_argument("--yes", action="store_true", help="actually move files; omit for a dry run")

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = bench_root()

    if args.command == "setup":
        return run_setup(args, root)
    if args.command == "analyze":
        return run_analyze(args)
    if args.command == "cleanup":
        return run_cleanup(args, root)
    raise CohortRunError(f"unknown command {args.command!r}")  # unreachable: argparse's subparsers already gate this


if __name__ == "__main__":
    try:
        sys.exit(main())
    except CohortRunError as exc:
        print(f"cohort_run.py: error: {exc}", file=sys.stderr)
        sys.exit(1)
