#!/usr/bin/env python3
"""Operator convenience wrapper around the five scoring tools
(docs/MODE2-REWRITE-PLAN.md §6, "Tool 6"): `setup` creates a fresh trial
worktree of the substrate repo (unless `--repo` is given) and prints a
ready-to-paste Mode B launcher prompt for it; `analyze` runs `grade_run.py`
-> `model_report.py` -> `leaderboard.py` in one command once a run is
finished; `cleanup` removes trial worktrees `setup` created; `reset-
leaderboard` archives (never deletes) old `results/` output.

This module never launches PM, never writes into a Developer/PM directory,
and never talks to a run in progress -- the same read-only, PM-is-never-
instrumented boundary every other tool in this repo holds (AGENTS.md,
docs/MODE2-REWRITE-PLAN.md §2). `setup`'s prompt text is extracted, verbatim
and read-only, from project-manager's own `SKILL.md` -- never a hardcoded
copy that could silently drift from what that skill actually asks for.
Creating/removing a trial worktree of the substrate repo is not "launching
PM" or "adding to its prompt" -- it is ordinary git housekeeping on a repo
outside this one, the same kind of preparation an operator would otherwise
do by hand before pasting the printed prompt into their own harness.
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

import yaml

import bench_lib
import dev_check
import grade_run
import leaderboard
import model_report

# This bench's one frozen plan (AGENTS.md: "The vendored plan is frozen"),
# and the provenance file naming the exact commit it was vendored from --
# see parse_pinned_plan_commit().
_FROZEN_PLAN_RELATIVE_PATH = Path("docs/MERGER_RATE_PLAN-2SLICE.md")
_PROVENANCE_RELATIVE_PATH = Path("docs/MERGER_RATE_PLAN-2SLICE.provenance.md")
_PINNED_PLAN_COMMIT_RE = re.compile(r"Pinned commit:\s*`([0-9a-f]{7,40})`")


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


def load_raw_policy(policy_path: Path) -> dict[str, Any]:
    """A minimal policy.yaml load with no dev_check.py-specific validation
    -- used by callers (`cleanup`, and `setup`'s worktree-creation path)
    that only need this module's own keys (`relative_velocity_repo`/
    `dev_branch_prefix`/`dev_worktree_root`), never dev_check.py's
    (`lint_script`, `health_script`, ...), which have nothing to do with
    creating or removing a trial worktree.
    """
    if not policy_path.is_file():
        raise CohortRunError(f"policy file not found: {policy_path}")
    with policy_path.open("r", encoding="utf-8") as handle:
        policy = yaml.safe_load(handle)
    if not isinstance(policy, dict):
        raise CohortRunError(f"policy file {policy_path} did not parse to a mapping")
    return policy


def load_policy(policy_path: Path) -> dict[str, Any]:
    """`setup`'s own policy validation for the launcher-prompt path --
    reuses dev_check.py's (it already requires `pm_scripts_dir`, which
    `setup` also needs), wrapped into this module's own error type so a bad
    policy.yaml fails as `cohort_run.py: error: ...` like every other
    failure path here, not an unhandled dev_check.DevCheckError traceback.
    """
    try:
        return dev_check.load_policy(policy_path)
    except dev_check.DevCheckError as exc:
        raise CohortRunError(str(exc)) from exc


def parse_pinned_plan_commit(provenance_path: Path) -> str:
    """The exact commit this bench's one frozen plan was vendored from,
    parsed live from `docs/MERGER_RATE_PLAN-2SLICE.provenance.md`'s own
    "Pinned commit: `<hash>`" line -- never duplicated as a second,
    driftable source of truth (the same reasoning `extract_launcher_template`
    already applies to `SKILL.md`). This bench tests exactly one plan
    (AGENTS.md: "The vendored plan is frozen"), so every trial worktree
    `create_dev_worktree` makes starts from this commit: the identical,
    known-clean baseline the plan and hidden tests were validated against.

    Raises:
        CohortRunError: the provenance file is missing, or has no
            "Pinned commit: `...`" line to parse -- never a stale fallback.
    """
    if not provenance_path.is_file():
        raise CohortRunError(f"{provenance_path} not found; cannot determine this bench's pinned plan commit")
    match = _PINNED_PLAN_COMMIT_RE.search(provenance_path.read_text(encoding="utf-8"))
    if not match:
        raise CohortRunError(f"{provenance_path} has no \"Pinned commit: `...`\" line to parse")
    return match.group(1)


def slugify(value: str) -> str:
    """Lowercase, alphanumeric-and-hyphen only -- for a worktree/branch
    label derived from a model or harness name, e.g.
    "codex/gpt-5.6-luna" -> "codex-gpt-5-6-luna"."""
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    if not slug:
        raise CohortRunError(f"{value!r} has no usable characters for a worktree/branch label")
    return slug


def load_dev_repo_policy(policy: dict[str, Any]) -> tuple[Path, str, Path]:
    """Validate and resolve the three policy.yaml keys trial-worktree
    creation/removal need: `relative_velocity_repo` (must exist and look
    like a git repo), `dev_branch_prefix`, and `dev_worktree_root`
    (defaulting to `relative_velocity_repo`'s own parent directory).

    Raises:
        CohortRunError: a required key is missing, or `relative_velocity_repo`
            doesn't exist / isn't a git repo.
    """
    repo_value = policy.get("relative_velocity_repo")
    branch_prefix = policy.get("dev_branch_prefix")
    missing = [key for key, value in (("relative_velocity_repo", repo_value), ("dev_branch_prefix", branch_prefix)) if not value]
    if missing:
        raise CohortRunError(
            f"policy.yaml is missing required key(s) for trial-worktree creation/removal: {', '.join(missing)} "
            "-- or pass --repo yourself to `setup` to skip creating one"
        )
    repo = Path(repo_value).expanduser().resolve()
    if not (repo / ".git").exists():
        raise CohortRunError(f"policy.yaml's relative_velocity_repo={repo} does not look like a git repository")
    worktree_root = (
        Path(policy["dev_worktree_root"]).expanduser().resolve() if policy.get("dev_worktree_root") else repo.parent
    )
    return repo, branch_prefix, worktree_root


def _run_git(args: list[str], *, error_prefix: str) -> str:
    """Run a git command, returning stdout on success or raising
    CohortRunError naming the command and its stderr on failure -- shared
    by every worktree/branch helper below."""
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise CohortRunError(f"{error_prefix}: {result.stderr.strip() or result.returncode}")
    return result.stdout


def _parse_worktree_list(output: str) -> list[dict[str, str]]:
    """Parse `git worktree list --porcelain -z` output (NUL-terminated
    fields, an extra NUL between entries) into one dict per worktree entry
    (at least a `worktree` key; a `branch` key too unless that worktree is
    in a detached-HEAD state).

    `-z` matters, not just `--porcelain`: a worktree path is an arbitrary
    filesystem path and can legally contain a newline, which a line-based
    parse of plain `--porcelain` output would misread as a field boundary.
    NUL cannot appear in a path, so it is the only safe delimiter here.
    """
    entries: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for field in output.split("\0"):
        if not field:
            if current:
                entries.append(current)
                current = {}
            continue
        key, _, value = field.partition(" ")
        current[key] = value
    if current:
        entries.append(current)
    return entries


def list_bench_worktrees(repo: Path, branch_prefix: str) -> list[dict[str, str]]:
    """Every currently checked-out worktree of `repo` whose branch is under
    `branch_prefix/` -- i.e. every trial worktree `setup` has created and
    `cleanup` hasn't removed yet, regardless of label or model."""
    output = _run_git(
        ["git", "-C", str(repo), "worktree", "list", "--porcelain", "-z"],
        error_prefix=f"`git -C {repo} worktree list` failed",
    )
    prefix = f"refs/heads/{branch_prefix}/"
    return [entry for entry in _parse_worktree_list(output) if entry.get("branch", "").startswith(prefix)]


def list_bench_branches(repo: Path, branch_prefix: str) -> set[str]:
    """Every local branch's label under `branch_prefix/`, whether or not it
    currently has a worktree checked out -- `cleanup` removes only a trial's
    worktree, never its branch, so a label can be "taken" by a branch alone."""
    output = _run_git(
        ["git", "-C", str(repo), "branch", "--list", f"{branch_prefix}/*", "--format=%(refname:short)"],
        error_prefix=f"`git -C {repo} branch --list` failed",
    )
    return {line.rsplit("/", 1)[-1] for line in output.splitlines() if line}


def next_available_label(repo: Path, branch_prefix: str, worktree_root: Path, base_slug: str) -> str:
    """The first `<base_slug>-<n>` (n starting at 1) whose branch doesn't
    already exist and whose worktree directory isn't already present -- so
    re-running `setup` for the same model auto-picks up the next repeat
    (`policy.yaml`'s `repeats`) rather than colliding with it."""
    existing_labels = list_bench_branches(repo, branch_prefix)
    n = 1
    while True:
        label = f"{base_slug}-{n}"
        worktree_path = worktree_root / f"{repo.name}-{label}"
        if label not in existing_labels and not worktree_path.exists():
            return label
        n += 1


def _rollback_worktree(repo: Path, worktree_path: Path, branch_name: str) -> None:
    """Best-effort teardown of a worktree/branch `create_dev_worktree` just
    created, used only on its own failure paths -- both calls are
    best-effort (errors ignored) since the goal is "leave nothing orphaned
    behind a raised error", not to surface a second failure over the first.
    Removing the worktree first matters: `git branch -D` on a branch still
    checked out by a worktree refuses.
    """
    subprocess.run(["git", "-C", str(repo), "worktree", "remove", "--force", str(worktree_path)], capture_output=True, check=False)
    subprocess.run(["git", "-C", str(repo), "branch", "-D", branch_name], capture_output=True, check=False)


def create_dev_worktree(
    policy: dict[str, Any],
    root: Path,
    *,
    model: str | None,
    harness: str | None,
    label: str | None,
    base_commit: str | None,
) -> tuple[Path, str, str]:
    """Create one disposable git worktree of policy.yaml's
    `relative_velocity_repo`, on a fresh branch `<dev_branch_prefix>/<label>`,
    checked out from this bench's pinned plan commit (or `base_commit`, an
    explicit override) -- so the result is immediately ready for a normal
    Mode B run: `run_setup` points the launcher prompt's `Repo:`/`Plan
    file:` gaps straight at it, with no manual git setup by the operator.

    Returns:
        (worktree_path, branch_name, label) -- all resolved/absolute
        except `label` and `branch_name`.

    Raises:
        CohortRunError: `relative_velocity_repo`/`dev_branch_prefix` aren't
            configured, an explicit `label` collides with an existing
            branch or worktree directory, `git worktree add` itself fails,
            or the new worktree unexpectedly has no frozen plan file in it.
    """
    repo, branch_prefix, worktree_root = load_dev_repo_policy(policy)
    resolved_commit = base_commit or parse_pinned_plan_commit(root / _PROVENANCE_RELATIVE_PATH)

    if label:
        worktree_path = worktree_root / f"{repo.name}-{label}"
        if label in list_bench_branches(repo, branch_prefix) or worktree_path.exists():
            raise CohortRunError(
                f"label {label!r} already has a branch ({branch_prefix}/{label}) or a worktree directory "
                f"({worktree_path}) -- pick a different --label, or `cleanup --label {label}` the existing one first"
            )
    else:
        label = next_available_label(repo, branch_prefix, worktree_root, slugify(model or harness or "trial"))
        worktree_path = worktree_root / f"{repo.name}-{label}"

    branch_name = f"{branch_prefix}/{label}"
    worktree_root.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["git", "-C", str(repo), "worktree", "add", "-b", branch_name, str(worktree_path), resolved_commit],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        # Git can still leave the branch/worktree registered even on a
        # nonzero exit here (e.g. a failing post-checkout hook runs after
        # both are created) -- reconcile whatever exists before raising, the
        # same as the plan-file check below, so a failed `setup` never
        # leaves orphaned state an operator can't see behind a clean error.
        _rollback_worktree(repo, worktree_path, branch_name)
        raise CohortRunError(
            f"`git worktree add` for {worktree_path} failed: {result.stderr.strip() or result.returncode}"
        )

    plan_in_worktree = worktree_path / _FROZEN_PLAN_RELATIVE_PATH
    if not plan_in_worktree.is_file():
        _rollback_worktree(repo, worktree_path, branch_name)
        raise CohortRunError(
            f"created {worktree_path} at {resolved_commit}, but it has no {_FROZEN_PLAN_RELATIVE_PATH} -- "
            "is relative_velocity_repo, or the pinned commit, still correct? (the worktree and branch were removed again)"
        )
    return worktree_path, branch_name, label


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


_PLAN_NOTE = (
    "This bench has exactly one frozen plan: docs/MERGER_RATE_PLAN-2SLICE.md, vendored from\n"
    "relative-velocity at a pinned commit (see docs/MERGER_RATE_PLAN-2SLICE.provenance.md). Every\n"
    "trial runs against it. Repo:/Plan file: below point at a freshly created worktree of it unless\n"
    "--repo was given.\n"
)

_SETUP_STEPS = """\
Steps to follow:

  1. Run this command (as above), unless you passed --repo yourself to
     point at an already-prepared repo instead -- either way, Repo:/Plan
     file: below are already correct; there is nothing to hand-type.
  2. Copy the prompt block below into a brand-new PM-capable session (a
     fresh Claude Code, Codex CLI, or equivalent session -- NOT this one,
     and not one already mid-task). Fill in any remaining <...> gaps by
     hand first.
  3. Send it, then let PM supervise the run entirely on its own to
     completion. This repo has no code path that launches PM and never
     will -- do not paste anything else into that session on this repo's
     behalf, and never put PM_RUN_TOKEN anywhere this repo can read it.
  4. When PM is done -- run.json["status"] is "complete", or "stopped" with
     PM's own closing event on record ("needs-human" is a pause, not a
     finish) -- find its authoritative run directory: it is
     <worktree-git-dir>/pm/<run-id>/ (PM prints this at `init`/`start-run`;
     or derive <worktree-git-dir> yourself with
     `git -C <dev-repo> rev-parse --absolute-git-dir` in the Developer's
     repo -- the in-worktree .pm/ copy is a mirror, not the authority).
  5. Grade it end to end in one command:

       python tools/cohort_run.py analyze --run-dir <pm-run-dir>

     (or `--dev-repo <dev-repo>` instead of `--run-dir`, if there is
     exactly one run under that repo's PM state). This runs grade_run.py,
     then model_report.py, then leaderboard.py, and reports the result.
  6. Check results/leaderboard.json. analyze is idempotent -- re-run it any
     time, including after a later cohort member finishes, to refold the
     leaderboard.
  7. Once you're done with a trial's worktree, `python tools/cohort_run.py
     cleanup` removes it (dry run by default; --yes to actually remove).
     Grading first isn't required -- an ungraded trial is flagged with a
     warning, not refused.
"""


def run_setup(args: argparse.Namespace, root: Path) -> int:
    if args.repo and (args.label or args.base_commit):
        raise CohortRunError("--label/--base-commit only apply when creating a new worktree; omit --repo to use them")

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

    repo = args.repo
    plan_file = args.plan_file
    if plan_file is not None:
        # Validated once, up front, regardless of whether --repo is also
        # given -- an explicit override must be just as real as a derived
        # path, in both the auto-created-worktree and manual-repo cases.
        plan_file_path = Path(plan_file).expanduser().resolve()
        if not plan_file_path.is_file():
            raise CohortRunError(f"--plan-file {plan_file_path} is not an existing file")
        plan_file = str(plan_file_path)

    created: tuple[Path, str, str] | None = None
    if repo is None:
        worktree_path, branch_name, label = create_dev_worktree(
            policy, root, model=args.model, harness=args.harness, label=args.label, base_commit=args.base_commit
        )
        repo = str(worktree_path)
        if plan_file is None:
            plan_file = str(worktree_path / _FROZEN_PLAN_RELATIVE_PATH)
        created = (worktree_path, branch_name, label)
    else:
        # A relative or nonexistent --repo would otherwise print an
        # "already correct" Repo:/Plan file: pair that is neither absolute
        # (unsafe once pasted into a session with a different cwd) nor
        # actually real -- resolve and verify both, the same rigor the
        # auto-created worktree path already gets.
        repo_path = Path(repo).expanduser().resolve()
        if not repo_path.is_dir():
            raise CohortRunError(f"--repo {repo_path} is not an existing directory")
        repo = str(repo_path)
        if plan_file is None:
            derived_plan_file = repo_path / _FROZEN_PLAN_RELATIVE_PATH
            if not derived_plan_file.is_file():
                raise CohortRunError(
                    f"--repo {repo_path} has no {_FROZEN_PLAN_RELATIVE_PATH} -- pass --plan-file explicitly if it lives elsewhere"
                )
            plan_file = str(derived_plan_file)

    prompt, substituted = render_launcher_prompt(template, plan_file=plan_file, repo=repo, harness=args.harness, model=args.model)
    for name, value in (("plan_file", plan_file), ("repo", repo), ("harness", args.harness), ("model", args.model)):
        if value and name not in substituted:
            print(
                f"cohort_run.py: warning: --{name.replace('_', '-')} was given but the launcher template has no "
                f"matching '{name}' line to fill -- add it by hand below",
                file=sys.stderr,
            )

    print(_PLAN_NOTE)
    if created:
        worktree_path, branch_name, label = created
        print(f"cohort_run.py: created worktree {worktree_path} on branch {branch_name} (label {label!r})\n")

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


# --- cleanup (trial worktrees) ----------------------------------------------


def _worktree_grading_status(worktree_path: str, root: Path) -> list[str]:
    """Every PM run recorded under this worktree's own git-dir that has no
    `results/runs/<run_id>/model-report.json` yet -- i.e. `analyze` hasn't
    (successfully) run for it. Empty means every recorded run is graded, or
    none was ever recorded (PM never ran here) -- both are fine to remove.
    """
    result = subprocess.run(
        ["git", "-C", worktree_path, "rev-parse", "--absolute-git-dir"], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        return [f"could not resolve this worktree's own git-dir: {result.stderr.strip() or result.returncode}"]
    pm_root = Path(result.stdout.strip()) / "pm"
    if not pm_root.is_dir():
        return []
    return [
        run_dir.name
        for run_dir in sorted(p for p in pm_root.iterdir() if p.is_dir())
        if not (root / "results" / "runs" / run_dir.name / "model-report.json").is_file()
    ]


def run_cleanup(args: argparse.Namespace, root: Path) -> int:
    """Remove trial worktrees `setup` created -- never their branch
    (AGENTS.md's "archive, never delete" spirit: a branch is cheap,
    recoverable history; the worktree is just disk space this operator no
    longer needs).

    Dry-run by default; `--yes` actually removes. An ungraded trial (no
    `model-report.json` recorded for any PM run found in it) is flagged
    with a warning, never refused outright -- the operator may deliberately
    not want to grade every trial (an explicit operator decision, not this
    tool's call to make).
    """
    policy_path = (args.policy or (root / "policy.yaml")).expanduser().resolve()
    policy = load_raw_policy(policy_path)
    repo, branch_prefix, _worktree_root = load_dev_repo_policy(policy)

    worktrees = list_bench_worktrees(repo, branch_prefix)
    if args.label:
        target_branch = f"refs/heads/{branch_prefix}/{args.label}"
        worktrees = [entry for entry in worktrees if entry.get("branch") == target_branch]
        if not worktrees:
            raise CohortRunError(f"no worktree found for label {args.label!r} (branch {branch_prefix}/{args.label})")

    if not worktrees:
        print(f"cohort_run.py: no {branch_prefix}/* trial worktrees found under {repo}")
        return 0

    print(f"cohort_run.py: {'removing' if args.yes else 'would remove'}:")
    for entry in worktrees:
        worktree_path = entry["worktree"]
        branch = entry.get("branch", "").removeprefix("refs/heads/")
        ungraded = _worktree_grading_status(worktree_path, root)
        note = f" -- WARNING: ungraded run(s): {', '.join(ungraded)}" if ungraded else ""
        print(f"  - {worktree_path} (branch {branch}){note}")

    if not args.yes:
        print("cohort_run.py: dry run only -- nothing removed. Pass --yes to actually remove these.")
        return 0

    problems = []
    for entry in worktrees:
        worktree_path = entry["worktree"]
        cmd = ["git", "-C", str(repo), "worktree", "remove", worktree_path]
        if args.force:
            cmd.append("--force")
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            problems.append(f"{worktree_path}: {result.stderr.strip() or result.returncode}")

    if problems:
        for problem in problems:
            print(f"cohort_run.py: warning: failed to remove {problem}", file=sys.stderr)
        return 1
    print(f"cohort_run.py: removed {len(worktrees)} worktree(s) (their branches were left in place)")
    return 0


# --- reset-leaderboard --------------------------------------------------------


def run_reset_leaderboard(args: argparse.Namespace, root: Path) -> int:
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

_SETUP_EPILOG = """\
Example:

  python tools/cohort_run.py setup --harness claude --model claude-sonnet-5

  This creates a fresh trial worktree of policy.yaml's relative_velocity_repo
  (label auto-derived from --model and auto-numbered, e.g.
  pm-eval-v2/claude-sonnet-5-1), checked out from this bench's one pinned plan
  commit, and prints the launcher prompt with Repo:/Plan file: pointing
  straight at it -- paste it into a fresh Claude Code session running Sonnet 5
  at low reasoning effort (a harness-side setting, not a flag here) and it
  runs correctly with nothing else to prepare by hand.

  PM still chooses its own reviewer per slice, on its own judgement -- there
  is no reviewer flag or gap. A full trial might, for example, pit that
  Developer seat against whatever reviewer PM itself commissions (codex
  running gpt-5.6-luna at low effort is one plausible pick PM might make on
  its own -- shown here only for illustration, never something to pass here).
"""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Operator convenience wrapper: `setup` creates a fresh trial worktree (unless --repo is given) and "
            "prints project-manager's own launcher prompt (extracted live, never a stale copy) ready to paste; "
            "`analyze` runs grade_run.py -> model_report.py -> leaderboard.py in one command; `cleanup` removes "
            "trial worktrees `setup` created; `reset-leaderboard` archives old results/ output. Never launches "
            "PM itself (docs/MODE2-REWRITE-PLAN.md §2)."
        )
    )
    parser.add_argument("--policy", type=Path, default=None, help="defaults to policy.yaml at this repo's root")
    subparsers = parser.add_subparsers(dest="command", required=True)

    setup_parser = subparsers.add_parser(
        "setup",
        help="create a fresh trial worktree (unless --repo given) and print the launcher prompt for it",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_SETUP_EPILOG,
    )
    setup_parser.add_argument("--harness", default=None, help="e.g. codex|claude|copilot|opencode|qwen")
    setup_parser.add_argument("--model", default=None, help="candidate Developer model to fill into the Harness line")
    setup_parser.add_argument(
        "--label",
        default=None,
        help="trial label for the new worktree/branch; default: derived from --model/--harness, auto-numbered",
    )
    setup_parser.add_argument(
        "--base-commit",
        default=None,
        help="override the commit a new worktree is created from (default: this bench's pinned plan commit)",
    )
    setup_parser.add_argument(
        "--repo", default=None, help="skip creating a worktree; use this already-prepared Developer repo/worktree directly"
    )
    setup_parser.add_argument(
        "--plan-file", default=None, help="override the derived path to the frozen plan inside --repo (or the created worktree)"
    )

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

    cleanup_parser = subparsers.add_parser(
        "cleanup", help="remove trial worktrees `setup` created (never their branch); dry run by default"
    )
    cleanup_parser.add_argument("--label", default=None, help="remove only this trial's worktree; default: every trial found")
    cleanup_parser.add_argument("--yes", action="store_true", help="actually remove; omit for a dry run")
    cleanup_parser.add_argument("--force", action="store_true", help="pass --force to `git worktree remove` for a dirty worktree")

    reset_leaderboard_parser = subparsers.add_parser(
        "reset-leaderboard", help="archive (never delete) old results/ output, e.g. before a fresh cohort pass"
    )
    reset_leaderboard_parser.add_argument(
        "--run-id", default=None, help="archive only this run's results; default: everything"
    )
    reset_leaderboard_parser.add_argument(
        "--results-dir", type=Path, default=None, help="defaults to results/ at this repo's root"
    )
    reset_leaderboard_parser.add_argument(
        "--archive-dir", type=Path, default=None, help="defaults to archive/results-<UTC timestamp>"
    )
    reset_leaderboard_parser.add_argument("--yes", action="store_true", help="actually move files; omit for a dry run")

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
    if args.command == "reset-leaderboard":
        return run_reset_leaderboard(args, root)
    raise CohortRunError(f"unknown command {args.command!r}")  # unreachable: argparse's subparsers already gate this


if __name__ == "__main__":
    try:
        sys.exit(main())
    except CohortRunError as exc:
        print(f"cohort_run.py: error: {exc}", file=sys.stderr)
        sys.exit(1)
