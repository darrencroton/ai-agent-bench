#!/usr/bin/env python3
"""Operator convenience wrapper around the five scoring tools
(docs/MODE2-REWRITE-PLAN.md §6, "Tool 6"): `setup` creates a fresh trial
worktree of the substrate repo (unless `--repo` is given) and prints a
ready-to-paste Mode B launcher prompt for it; `analyze` runs `grade_run.py`
-> `model_report.py` -> `leaderboard.py` in one command once a run is
finished; `cleanup` removes trial worktrees `setup` created; `reset-leaderboard`
archives (never deletes) old `results/` output.

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
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import tomllib
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


def _resolve_policy_path(value: str, root: Path) -> Path:
    """A policy.yaml path value, expanded and made absolute. A relative
    value resolves against this bench's own repo root, never the caller's
    cwd -- policy.yaml is checked-in, portable config, not a CLI argument
    typed in some particular shell."""
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def load_dev_repo_policy(policy: dict[str, Any], root: Path) -> tuple[Path, str, Path]:
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
    repo = _resolve_policy_path(repo_value, root)
    if not (repo / ".git").exists():
        raise CohortRunError(f"policy.yaml's relative_velocity_repo={repo} does not look like a git repository")
    worktree_root = _resolve_policy_path(policy["dev_worktree_root"], root) if policy.get("dev_worktree_root") else repo.parent
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
    re-running `setup` with no `--label` auto-picks up the next repeat
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
    repo, branch_prefix, worktree_root = load_dev_repo_policy(policy, root)
    resolved_commit = base_commit or parse_pinned_plan_commit(root / _PROVENANCE_RELATIVE_PATH)

    if label:
        worktree_path = worktree_root / f"{repo.name}-{label}"
        if label in list_bench_branches(repo, branch_prefix) or worktree_path.exists():
            raise CohortRunError(
                f"label {label!r} already has a branch ({branch_prefix}/{label}) or a worktree directory "
                f"({worktree_path}) -- pick a different --label, or `cleanup --label {label}` the existing one first"
            )
    else:
        label = next_available_label(repo, branch_prefix, worktree_root, "trial")
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

# Every supported harness's own on-disk trust/permission store, verified by
# inspecting each tool's real local config on a machine that already had
# several trusted directories in it -- never guessed. `claude`/`codex`/
# `copilot` each persist a simple per-directory trust flag this function can
# safely add to (a JSON object, a TOML table, and a JSON array respectively).
# `opencode` keeps its own equivalent in a live, actively-written SQLite
# database with a `permission` schema that maps a project's tool-call
# approvals, not a simple "trust this folder" bit -- there is no evidence of
# a safe external-write path, so it is deliberately not automated here.
# `qwen` was checked (its per-project directories hold only chat transcripts)
# and no persistent trust store was found for it at all. Both report this
# plainly rather than silently doing nothing.
_HARNESS_TRUST_CONFIG_PATHS = {
    "claude": Path.home() / ".claude.json",
    "codex": Path.home() / ".codex" / "config.toml",
    "copilot": Path.home() / ".copilot" / "config.json",
}


def _atomic_write_text(path: Path, content: str) -> None:
    """Write `content` to `path` via a uniquely-named same-directory temp
    file and an atomic rename -- so a process reading `path` concurrently
    (the owning harness may have its own session open right now) never
    observes a partially-written file, and two concurrent `setup` calls
    pre-trusting the same config never collide on a shared temp filename.
    A symlinked `path` (common for a dotfile-managed config) is resolved
    first, so the write lands on the real target and the symlink itself
    survives; the new file's permission bits are copied from the original
    rather than left at the process umask's default, so a config file with
    restrictive permissions doesn't become more permissive."""
    target = path.resolve()
    original_mode = target.stat().st_mode
    fd, tmp_name = tempfile.mkstemp(dir=target.parent, prefix=target.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.chmod(tmp_name, original_mode)
        os.replace(tmp_name, target)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


def _pretrust_claude(repo: str, config_path: Path) -> str:
    """Add (or confirm) a `hasTrustDialogAccepted: true` entry for `repo` in
    Claude Code's own `~/.claude.json`, matching the exact minimal shape
    Claude Code's own native worktree feature already writes for a freshly
    created, not-yet-used project -- this is that tool's own established
    pattern, not an invented one. An existing entry for `repo` is merged
    into (only `hasTrustDialogAccepted` is touched), never replaced, so any
    of its own accumulated fields (session history, allowed tools, ...)
    survive untouched.
    """
    if not config_path.is_file():
        return f"no {config_path} found -- Claude Code may not be installed/configured yet; skipped"
    data = json.loads(config_path.read_text(encoding="utf-8"))
    projects = data.setdefault("projects", {})
    entry = projects.get(repo)
    if entry is not None:
        if entry.get("hasTrustDialogAccepted"):
            return f"{config_path} already trusts {repo}"
        entry["hasTrustDialogAccepted"] = True
    else:
        projects[repo] = {
            "allowedTools": [],
            "mcpContextUris": [],
            "enabledMcpjsonServers": [],
            "disabledMcpjsonServers": [],
            "hasTrustDialogAccepted": True,
            "hasClaudeMdExternalIncludesApproved": False,
            "hasClaudeMdExternalIncludesWarningShown": False,
        }
    _atomic_write_text(config_path, json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return f"pre-trusted {repo} in {config_path}"


_TOML_BASIC_STRING_ESCAPES = {
    "\\": "\\\\",
    '"': '\\"',
    "\b": "\\b",
    "\t": "\\t",
    "\n": "\\n",
    "\f": "\\f",
    "\r": "\\r",
}


def _toml_basic_string_body(value: str) -> str:
    """Escape `value` as the body of a TOML basic string (the part between
    the quotes), per the TOML spec -- every control character a real
    filesystem path can legally contain (a literal newline is rare but
    possible, and this repo's own worktree-listing tests already treat that
    as a real case, not a hypothetical one), not just backslash/quote."""
    chars = []
    for ch in value:
        if ch in _TOML_BASIC_STRING_ESCAPES:
            chars.append(_TOML_BASIC_STRING_ESCAPES[ch])
        elif ord(ch) < 0x20 or ord(ch) == 0x7F:
            chars.append(f"\\u{ord(ch):04X}")
        else:
            chars.append(ch)
    return "".join(chars)


def _pretrust_codex(repo: str, config_path: Path) -> str:
    """Append a `[projects."<repo>"]` / `trust_level = "trusted"` table to
    Codex CLI's own `~/.codex/config.toml`, in the exact shape Codex CLI's
    own existing entries already use -- append-only, so every other setting
    in the file is left byte-for-byte untouched.

    The file is parsed structurally (never substring-matched) to decide
    whether `repo` is already trusted: a `[projects."<repo>"]` table with
    some other `trust_level` (or none) is left alone rather than silently
    treated as already-trusted, or duplicated into an invalid second table
    of the same name -- TOML forbids declaring one table twice, so this
    function refuses to modify that case rather than corrupt the file. The
    appended text is itself re-validated as TOML before it's written.
    """
    if not config_path.is_file():
        return f"no {config_path} found -- Codex CLI may not be installed/configured yet; skipped"
    text = config_path.read_text(encoding="utf-8")
    try:
        parsed = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        return f"{config_path} is not valid TOML ({exc}); not modified"
    existing = parsed.get("projects", {}).get(repo)
    if existing is not None:
        if existing.get("trust_level") == "trusted":
            return f"{config_path} already trusts {repo}"
        return (
            f"{config_path} already has a projects entry for {repo} with trust_level={existing.get('trust_level')!r}; "
            "leaving it as-is rather than create a duplicate table -- edit it by hand if you want to trust this directory"
        )
    block = f'\n[projects."{_toml_basic_string_body(repo)}"]\ntrust_level = "trusted"\n'
    new_text = text + block
    tomllib.loads(new_text)  # never persist a document this tool can't parse back
    _atomic_write_text(config_path, new_text)
    return f"pre-trusted {repo} in {config_path}"


def _split_leading_jsonc_comments(text: str) -> tuple[str, str]:
    """Split `text` into its leading run of blank/`//`-comment lines and
    everything from the first other line on. Copilot CLI's config.json is
    JSONC only in this narrow sense (comment lines, and blank lines between
    them, before the JSON object begins) -- never comments interspersed
    with real content, which this deliberately does not attempt to parse."""
    lines = text.splitlines(keepends=True)
    split_at = 0
    for line in lines:
        stripped = line.strip()
        if stripped == "" or stripped.startswith("//"):
            split_at += 1
        else:
            break
    return "".join(lines[:split_at]), "".join(lines[split_at:])


def _pretrust_copilot(repo: str, config_path: Path) -> str:
    """Add `repo` to GitHub Copilot CLI's own `~/.copilot/config.json`
    `trustedFolders` array. Its leading `//`-comment lines (JSONC, not plain
    JSON) are preserved verbatim; only the JSON object after them is
    parsed, modified, and re-serialized. A file whose comments don't fit
    that narrow leading-lines shape is left untouched and named as such,
    rather than guessed at."""
    if not config_path.is_file():
        return f"no {config_path} found -- Copilot CLI may not be installed/configured yet; skipped"
    leading, body = _split_leading_jsonc_comments(config_path.read_text(encoding="utf-8"))
    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        return (
            f"{config_path} has content after its leading comments that isn't valid JSON ({exc}); not modified"
        )
    trusted_folders = data.setdefault("trustedFolders", [])
    if repo in trusted_folders:
        return f"{config_path} already trusts {repo}"
    trusted_folders.append(repo)
    _atomic_write_text(config_path, leading + json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    return f"pre-trusted {repo} in {config_path}"


def _pretrust_opencode(repo: str) -> str:
    return (
        "OpenCode keeps its own trust/permission state in a live SQLite database with no documented safe "
        f"external-write path; not automated -- accept its own prompt once for {repo}"
    )


def _pretrust_qwen(repo: str) -> str:
    return (
        f"no persistent per-directory trust store was found for Qwen Code; not automated -- accept its own "
        f"prompt once for {repo}, if it asks"
    )


def pretrust_repo_for_harness(harness: str, repo: str) -> str:
    """Best-effort: pre-register `repo` as a trusted directory for
    `harness`, so its own first-launch trust/permission prompt doesn't fire
    for a trial worktree it has never seen before. Always returns a
    human-readable status line -- including when a harness has no known
    safe way to do this -- never silent.

    A failure here (a config file in an unexpected shape, a permissions
    error, ...) is caught and reported as a status line rather than raised:
    this is a convenience on top of an unrelated tool's own state, and must
    never stop `setup` from creating the worktree and printing the prompt.
    """
    try:
        if harness == "claude":
            return _pretrust_claude(repo, _HARNESS_TRUST_CONFIG_PATHS["claude"])
        if harness == "codex":
            return _pretrust_codex(repo, _HARNESS_TRUST_CONFIG_PATHS["codex"])
        if harness == "copilot":
            return _pretrust_copilot(repo, _HARNESS_TRUST_CONFIG_PATHS["copilot"])
        if harness == "opencode":
            return _pretrust_opencode(repo)
        if harness == "qwen":
            return _pretrust_qwen(repo)
        raise CohortRunError(f"unknown --harness {harness!r}")  # unreachable: argparse's choices already gate this
    except Exception as exc:  # noqa: BLE001 -- see docstring: never let this abort `setup`
        return f"could not pre-trust {repo} for {harness}: {exc}"


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
) -> tuple[str, set[str]]:
    """Fill in whichever of the launcher template's `Plan file:`/`Repo:`
    gaps the caller supplied, leaving every other line -- including
    `Developer:`/`Reviewer:` and their own bracketed placeholders -- exactly
    as project-manager's own template states it, so the printed prompt is
    always safe to paste, filled or not. Who plays Developer/Reviewer is the
    operator's own choice, typed in by hand when the prompt is pasted; this
    tool carries no flag for it and never touches those lines (matching
    policy.yaml's own comment on why there is no reviewer-seat key either).

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
        else:
            lines.append(line)
    return "\n".join(lines), substituted


_PLAN_NOTE = (
    "This bench has exactly one frozen plan (docs/MERGER_RATE_PLAN-2SLICE.md, vendored from "
    "relative-velocity at a pinned commit -- see docs/MERGER_RATE_PLAN-2SLICE.provenance.md); every trial runs against it.\n"
)


def _render_setup_steps(repo: str, cleanup_label: str | None) -> str:
    """The numbered follow-up steps printed after the prompt. `repo` (and,
    when this call created a trial worktree, its `cleanup_label`) are
    substituted in directly -- `setup` already knows both, so neither is
    left as a `<...>` placeholder for the operator to fill in or derive.
    Both are shell-quoted: `repo` can be an arbitrary filesystem path (a
    space is legal), and an explicit `--label` is never validated against
    shell metacharacters, so an unquoted copy-paste could otherwise run more
    than the one intended command.
    """
    quoted_repo = shlex.quote(repo)
    cleanup_step = (
        f"5. When you're done with this trial, `python tools/cohort_run.py cleanup --label {shlex.quote(cleanup_label)}` "
        "removes its worktree (dry run by default; --yes to actually remove). Its branch is kept.\n"
        if cleanup_label
        else ""
    )
    return (
        "Steps to follow:\n\n"
        "1. Paste the prompt below into a brand-new PM-capable session (not this one) and fill in the "
        "Developer/Reviewer harness and model. Repo:/Plan file: above are already correct -- nothing else to hand-type.\n"
        "2. Let PM supervise the run to completion on its own. This repo has no code path that launches PM -- never "
        "paste anything else into that session on its behalf, and never expose PM_RUN_TOKEN to it.\n"
        '3. Once PM is finished (run.json["status"] is "complete", or "stopped" with its own closing event recorded -- '
        '"needs-human" is a pause, not a finish), grade it end to end:\n\n'
        f"     python tools/cohort_run.py analyze --dev-repo {quoted_repo}\n\n"
        "4. Check results/leaderboard.json. analyze is idempotent -- re-run it any time, including after a later "
        "cohort member finishes, to refold the leaderboard.\n"
        f"{cleanup_step}"
    )


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
        worktree_path, branch_name, label = create_dev_worktree(policy, root, label=args.label, base_commit=args.base_commit)
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

    prompt, substituted = render_launcher_prompt(template, plan_file=plan_file, repo=repo)
    for name, value in (("plan_file", plan_file), ("repo", repo)):
        if value and name not in substituted:
            print(
                f"cohort_run.py: warning: --{name.replace('_', '-')} was given but the launcher template has no "
                f"matching '{name}' line to fill -- add it by hand below",
                file=sys.stderr,
            )

    print(_PLAN_NOTE)
    cleanup_label = None
    if created:
        worktree_path, branch_name, label = created
        print(f"cohort_run.py: created worktree {worktree_path} on branch {branch_name} (label {label!r})\n")
        cleanup_label = label

    if args.harness:
        print(f"cohort_run.py: {pretrust_repo_for_harness(args.harness, repo)}\n")
    else:
        print(
            "cohort_run.py: no --harness given -- this trial's directory is not pre-trusted for any harness; "
            "accept your harness's own trust/permission prompt once when you first open it here.\n"
        )

    print(_render_setup_steps(repo, cleanup_label))
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
    repo, branch_prefix, _worktree_root = load_dev_repo_policy(policy, root)

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

  python tools/cohort_run.py setup --harness claude

  Creates a fresh trial worktree of policy.yaml's relative_velocity_repo (auto-numbered label, e.g. pm-eval-v2/trial-1), checked out from this bench's one pinned plan commit, and prints the launcher prompt with Repo:/Plan file: already filled in. Fill in Developer:/Reviewer: by hand when you paste it -- this tool has no flag for either; both are the operator's own choice made in the pasted prompt, not something set here. --harness only pre-trusts the new directory for that harness (claude/codex/copilot are supported; opencode/qwen print why they aren't) -- pass it to skip that harness's own first-launch prompt for this trial. Pass --label to name the trial yourself instead of auto-numbering.
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
    setup_parser.add_argument(
        "--harness",
        default=None,
        choices=sorted(_HARNESS_TRUST_CONFIG_PATHS) + ["opencode", "qwen"],
        help=(
            "candidate harness for this trial -- used ONLY to pre-register this trial's directory as trusted for "
            "that harness (so it doesn't prompt on first launch there); never filled into the printed "
            "Developer:/Reviewer: lines, which remain the operator's own choice made when the prompt is pasted"
        ),
    )
    setup_parser.add_argument(
        "--label", default=None, help="trial label for the new worktree/branch; default: auto-numbered from 'trial'"
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
