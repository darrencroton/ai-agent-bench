#!/usr/bin/env python3
"""Render eval/profile.md: an independent-columns view of every graded v2
trial, with NO composite score anywhere.

docs/EVAL-CONSOLIDATION-PROPOSAL.md's argument is that aggregate.py's
weighted composite is itself the problem -- averaging one discriminating
signal (mutation kill rate, spread 34-90 across models in the 219-trial
cohort) with several saturated ones (correctness 95-100, scope 218/219
perfect, ...) compresses the distribution until a frontier anchor outranks
models whose tests are demonstrably weaker. The fix tried here is not a
re-weight; it is deleting the average and reporting each signal on its own:

  - mutation kill rate (category_scores.test_adequacy)  -- THE score
  - correctness (category_scores.correctness)            -- gate, pass/fail, no weight
  - structural quality (eval/results/structure.json)      -- second score
  - lint (category_scores.hygiene)                        -- flag, < 1.0
  - scope discipline (category_scores.scope_discipline)   -- flag, < 1.0, + integrity
  - reliability (derived status + wall-clock)             -- record

This script re-grades nothing and writes no record. It reads the SAME
eval/results/runs/*.json files aggregate.py reads, plus the structural-score
sidecar eval/results/structure.json (written by structure.py, a sibling
script -- see eval/profile.yaml and docs/EVAL-CONSOLIDATION-TRIAL.md for
that boundary), and emits eval/profile.md.

Grouping, cohort handling, and every generic helper (repo_root, load_records,
cohort_key, cohort_label, grader_provenance_warnings, mean_or_none,
median_range, fmt_hm, mean_cat, ...) are imported from aggregate.py rather
than re-implemented -- this file must never fork that logic, or a task
spanning two rubric/task-contract cohorts could silently get blended here
even though aggregate.py itself is careful never to blend it.

Usage:
    python eval/harness/profile_view.py
"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aggregate  # noqa: E402 -- sibling module, see module docstring


def load_gate_threshold(root):
    """The correctness-gate threshold, read from eval/profile.yaml's
    `gate.correctness.threshold` via structure.py's `load_policy()`. See
    docs/EVAL-CONSOLIDATION-TRIAL.md for why the value sits in an empty band
    of the observed distribution.

    Fails loud. There is deliberately NO hardcoded default: eval/profile.yaml
    is a tracked file committed alongside this script, so an unreadable or
    malformed one is a broken checkout, not a condition to paper over. A
    silent fallback would render a whole Gate column under a threshold nobody
    chose and give no sign of it -- the same failure grade_trial.py refuses
    when the installed ruff is not the pinned version ("scoring hygiene's
    full weight with no lint coverage behind it would be worse than
    stopping"). Reporting policy gets the same treatment as scoring policy.

    Note the deliberate asymmetry with load_structure_scores() below, which
    DOES degrade: eval/results/structure.json is regenerable derived data and
    the rest of this view stays useful without it. Policy is loud; derived
    data may degrade."""
    import structure  # noqa: PLC0415 -- sibling module, resolved via sys.path above
    policy = structure.load_policy(root)
    try:
        threshold = policy["gate"]["correctness"]["threshold"]
    except (KeyError, TypeError) as exc:
        raise ValueError(
            "eval/profile.yaml: missing gate.correctness.threshold -- the correctness "
            "gate has no policy to apply") from exc
    if not isinstance(threshold, (int, float)) or isinstance(threshold, bool):
        raise ValueError(f"eval/profile.yaml: gate.correctness.threshold must be a number, "
                          f"got {threshold!r}")
    return float(threshold)


def check_policy_freshness(root, structure_meta):
    """Best-effort: if structure.py is importable, recompute the sha256 of
    the CURRENT eval/profile.yaml `structure:` block and compare it against
    the one recorded in structure.json's `_meta.policy_sha256`. A mismatch
    means eval/results/structure.json was generated under a policy that has
    since changed -- the structural column would then be silently stale.
    Never raises; a missing/incompatible structure.py just skips the check."""
    if not structure_meta:
        return None
    try:
        import structure  # noqa: PLC0415
        policy = structure.load_policy(root)
        current_sha = structure.policy_sha256(policy)
        recorded_sha = structure_meta.get("policy_sha256")
        if current_sha and recorded_sha and current_sha != recorded_sha:
            return (f"eval/results/structure.json was generated under structure: policy "
                    f"sha {recorded_sha[:8]}, but eval/profile.yaml's current one hashes to "
                    f"{current_sha[:8]} -- re-run `structure.py sweep` before trusting the "
                    f"Structure column.")
    except Exception:  # noqa: BLE001 -- best-effort only, never fatal
        return None
    return None


def load_structure_scores(root):
    """Returns (lookup, meta, warning). `lookup` maps run_id -> that run's
    structure.json entry (or {} if the file is entirely missing -- every
    run_id then falls through group_stats_profile's "no structural entry"
    path, which renders `--` and records why, exactly the degradation this
    function exists to make safe). `meta` is the `_meta` block, or None.
    `warning`, if not None, must be printed loudly by the caller -- this
    file must never crash or silently show blanks with no explanation when
    the structural sidecar has not been generated yet."""
    path = os.path.join(root, "eval", "results", "structure.json")
    if not os.path.exists(path):
        return {}, None, (
            "eval/results/structure.json not found -- the Structure column will render `--` "
            "for every row. Run `structure.py sweep` (see eval/harness/structure.py) to "
            "generate it, then re-run this script.")
    with open(path) as f:
        data = json.load(f)
    meta = data.pop("_meta", None)
    return data, meta, None


def correctness_gate_pass(record, threshold):
    """A record whose category_scores.correctness is missing or None is a
    gate FAIL, never a skip -- docs/EVAL-CONSOLIDATION-TRIAL.md is explicit
    about this because a None here means grading stopped before correctness
    was ever measured (e.g. a no-submission or an earlier-gate failure),
    which is exactly the case this gate exists to catch, not exempt."""
    correctness = (record.get("category_scores") or {}).get("correctness")
    if not isinstance(correctness, (int, float)):
        return False
    return correctness >= threshold


def reliability_status(record):
    """Derived only from fields that actually exist on a graded record --
    see the field inventory in eval/results/runs/*.json. Order matters: a
    timed-out trial is reported as `timed_out` even though grade_trial.py's
    own `no_submission` computation folds timeouts in (no_submission =
    timed_out OR no changed files) -- we want the more specific label
    whenever we can give one, and only fall through to `no_submission` for
    the remaining "no diff, but did not time out" case."""
    if record.get("timed_out"):
        return "timed_out"
    if record.get("no_submission") or not record.get("changed_files"):
        return "no_submission"
    if record.get("gate_status") == "failed":
        return "gate_failed"
    if record.get("missing_deliverables"):
        return "incomplete"
    return "completed"


def fmt_reliability(counts):
    total = sum(counts.values())
    if not total:
        return "--"
    completed = counts.get("completed", 0)
    others = {k: v for k, v in counts.items() if k != "completed" and v}
    s = f"completed {completed}/{total}"
    if others:
        s += " (" + ", ".join(f"{v} {k}" for k, v in sorted(others.items())) + ")"
    return s


def merge_counts(counts_list):
    total = collections.Counter()
    for c in counts_list:
        total.update(c)
    return dict(total)


def clean_fraction(trials, cat_id, extra_dirty=None):
    """Fraction of trials with `cat_id` >= 1.0 (the flag clear), among
    trials that actually scored that category -- an unscored (None) entry
    is excluded from both numerator and denominator, same principle as
    aggregate.mean_cat's renormalization over scored weight. `extra_dirty`,
    if given, marks a scored trial dirty regardless of its category value
    (used for scope_discipline: an integrity_violation must count against
    "scope clean" even on the rare record where scope_discipline itself
    reads 1.0)."""
    scored = [t for t in trials
              if isinstance((t.get("category_scores") or {}).get(cat_id), (int, float))]
    if not scored:
        return None
    clean = 0
    for t in scored:
        val = t["category_scores"][cat_id]
        dirty = val < 1.0 or (extra_dirty and extra_dirty(t))
        if not dirty:
            clean += 1
    return clean / len(scored)


def structural_lookup_for_trial(structure_lookup, structure_file_missing, trial):
    """Returns (score_or_None, missing_reason_or_None). A `structural_score`
    of null for a `not_applicable`/`missing_submission`/`apply_failed`/
    `parse_error` entry must render as `--` and be excluded from every mean
    -- docs/EVAL-CONSOLIDATION-TRIAL.md is explicit that 0 would mean
    "measured, and bad", which null is not."""
    if structure_file_missing:
        return None, "structure.json not found"
    entry = structure_lookup.get(trial["run_id"])
    if entry is None:
        return None, "no structural entry (run_id not present in structure.json)"
    score = entry.get("structural_score")
    if isinstance(score, (int, float)):
        return score, None
    reason = entry.get("status", "unknown")
    if entry.get("note"):
        reason += f": {entry['note']}"
    return None, reason


def group_stats_profile(trials, structure_lookup, structure_file_missing, threshold):
    """Aggregate one (cohort, task_id, harness, model, effort) group of
    trials into the profile-view numbers. Deliberately parallel in shape to
    aggregate.group_stats -- same grouping unit, same "trials" list kept for
    the telemetry/report-link use below -- but every number here is an
    independent column; nothing is combined into a single score."""
    n = len(trials)
    gate_n_pass = sum(1 for t in trials if correctness_gate_pass(t, threshold))

    struct_vals, struct_missing = [], []
    for t in trials:
        score, reason = structural_lookup_for_trial(structure_lookup, structure_file_missing, t)
        if score is not None:
            struct_vals.append(score)
        else:
            struct_missing.append((t["run_id"], reason))

    rel_counts = collections.Counter(reliability_status(t) for t in trials)
    latest = sorted(trials, key=lambda t: t["run_id"])[-1]

    return {
        "n": n,
        "gate_n_pass": gate_n_pass,
        "gate_n_total": n,
        "mutation_mean": aggregate.mean_cat(trials, "test_adequacy"),
        "structure_mean": aggregate.mean_or_none(struct_vals, ndigits=1),
        # How many of this group's trials actually contributed a structural
        # score. A group whose sidecar entries are only partly present would
        # otherwise show a real-looking Structure number computed over fewer
        # trials than its own Trials column claims -- worse than a blank cell,
        # because nothing marks it (external review, 2026-09-07).
        "structure_n_scored": len(struct_vals),
        "structure_n_absent": sum(1 for _, reason in struct_missing
                                   if reason and "not present in structure.json" in reason),
        "struct_missing": struct_missing,
        "lint_clean_fraction": clean_fraction(trials, "hygiene"),
        "scope_clean_fraction": clean_fraction(
            trials, "scope_discipline", extra_dirty=lambda t: t.get("integrity_violation")),
        "reliability_counts": dict(rel_counts),
        "latest_report": f"results/reports/{latest['run_id']}.md",
        "gate_fail_n": n - gate_n_pass,
        "integrity_n": sum(1 for t in trials if t.get("integrity_violation")),
        "trials": trials,
    }


def fmt_pct_range(mean, vals):
    """`62% (34-90%)` -- the model-profile Mutation-kill cell: a
    macro-averaged mean plus the min-max spread across the model's per-task
    means (not per-trial values -- docs/EVAL-CONSOLIDATION-TRIAL.md's column
    semantics table is specific that the range is across task means)."""
    if mean is None:
        return "--"
    vals = [v for v in vals if isinstance(v, (int, float))]
    if len(vals) <= 1:
        return aggregate.fmt_pct(mean)
    return f"{aggregate.fmt_pct(mean)} ({aggregate.fmt_pct(min(vals))}-{aggregate.fmt_pct(max(vals))})"


def fmt_structure_partial(stats):
    """The per-task Structure cell, suffixed `*` when the sidecar covered only
    some of the group's trials -- i.e. `structure.py sweep` has not been re-run
    since these trials were graded. Silence there would present a mean over an
    unstated subset as if it covered the whole group."""
    cell = fmt_structure(stats["structure_mean"])
    if stats["structure_n_absent"]:
        return f"{cell}*"
    return cell


def fmt_structure_or_dagger(x, withheld):
    """`--‡` when a structural mean was WITHHELD, distinct from a plain `--`
    meaning "not measured".

    Without this the two are indistinguishable, and the withheld case fires on
    exactly the workflow README.md recommends -- a single-task Mode 1 screen --
    because only Tasks 001 and 002 are structure-eligible, so a Task-001-only
    model is always withheld. Mirrors aggregate.py's own fmt_*_or_dagger plus
    footnote convention for the same problem (external review, 2026-09-07)."""
    return "--‡" if withheld else fmt_structure(x)


def fmt_structure(x):
    return f"{x:.1f}" if isinstance(x, (int, float)) else "--"


def fmt_gate(n_pass, n_total):
    return f"{n_pass}/{n_total} pass" if n_total else "--"


def structure_eligible_tasks(structure_lookup):
    """The set of task_ids that actually yield a structural score, read off
    the sidecar rather than configured anywhere.

    Needed because the structural score is scoped to deliverables a model
    authored from scratch (see eval/profile.yaml's `structure.scope`), so only
    some tasks contribute. Averaging a model's structural means over only the
    eligible tasks it happens to have run makes two models incomparable: the
    per-task substrate baselines differ, so a model missing a low-baseline
    task scores higher for no better reason than that it ran fewer tasks. This
    was measured, not hypothesised -- before the scope fix,
    opencode-go/minimax-m3 held the cohort's HIGHEST structural score purely
    because it had never run Tasks 003 and 005."""
    # No _meta guard needed: load_structure_scores pops it before this sees
    # the lookup, and every other caller passes a run_id-keyed dict.
    return {e["task_id"] for e in structure_lookup.values()
            if e.get("structural_score") is not None}


def build_model_row(harness, model, effort, stats_list, n_tasks_total,
                     eligible_tasks=frozenset()):
    """Macro-average across this combo's per-task groups, mirroring
    aggregate.py's own combo_units treatment of det_mean/complete_fraction:
    each task contributes one number regardless of how many trials it ran,
    so a task re-run 3 times never outweighs a task run once. Gate and
    Reliability are the one deliberate exception -- docs/EVAL-CONSOLIDATION-TRIAL.md's
    column semantics describe both as raw trial counts ("N/M pass", "completed
    N/M"), not means, so they sum trials directly across every task instead
    of averaging per-task fractions."""
    mutation_task_means = [s["mutation_mean"] for s in stats_list
                            if isinstance(s["mutation_mean"], (int, float))]
    # Withheld unless this combo covers EVERY structure-eligible task -- the
    # same rule aggregate.full_pass_duration_and_tokens already applies to a
    # model with incomplete task coverage ("no well-defined figure"), for the
    # same reason. See structure_eligible_tasks() above.
    structure_task_means = [s["structure_mean"] for s in stats_list
                             if isinstance(s["structure_mean"], (int, float))]
    # task_id via the group's own trials: group_stats_profile keeps the trial
    # list (as aggregate.group_stats does) and every trial in one group shares
    # a task_id by construction of the grouping key.
    covered = {s["trials"][0]["task_id"] for s in stats_list
               if isinstance(s["structure_mean"], (int, float))}
    structure_withheld = bool(eligible_tasks) and not eligible_tasks <= covered
    med_duration, _ = aggregate.full_pass_duration_and_tokens(stats_list, n_tasks_total)

    return {
        "harness": harness, "model": model, "effort": effort,
        "n_tasks": len(stats_list),
        "n_trials": sum(s["n"] for s in stats_list),
        "gate_n_pass": sum(s["gate_n_pass"] for s in stats_list),
        "gate_n_total": sum(s["gate_n_total"] for s in stats_list),
        "mutation_mean": aggregate.mean_or_none(mutation_task_means, ndigits=3),
        "mutation_task_means": mutation_task_means,
        "structure_mean": (None if structure_withheld
                            else aggregate.mean_or_none(structure_task_means, ndigits=1)),
        "structure_withheld": structure_withheld,
        "structure_n_covered": len(covered),
        "structure_n_eligible": len(eligible_tasks),
        "lint_clean_fraction": aggregate.mean_or_none(
            [s["lint_clean_fraction"] for s in stats_list]),
        "scope_clean_fraction": aggregate.mean_or_none(
            [s["scope_clean_fraction"] for s in stats_list]),
        "reliability_counts": merge_counts(s["reliability_counts"] for s in stats_list),
        "median_duration_seconds": med_duration,
    }


def render_header(structure_meta, structure_warning, policy_warning):
    lines = [
        "# Model profile",
        "",
        "Generated by `eval/harness/profile_view.py` from the same graded v2 trials "
        "`eval/harness/aggregate.py` reads in `eval/results/runs/`, plus the structural-score "
        "sidecar `eval/results/structure.json`. This view re-grades nothing and writes no "
        "record.",
        "",
        "**There is no composite score anywhere in this file.** "
        "`docs/EVAL-CONSOLIDATION-PROPOSAL.md` argues that averaging one discriminating "
        "signal (mutation kill rate) with several saturated ones is what compresses the "
        "leaderboard until a frontier model can rank below models whose tests demonstrably "
        "kill fewer mutations. This file reports each signal as its own column instead: "
        "mutation kill rate is the score, correctness is a pass/fail gate carrying no weight, "
        "structural quality is a second, independent score, lint and scope discipline are "
        "flags, and reliability is a record. None of these columns are combined into a total.",
        "",
    ]
    if structure_meta:
        lines.append(
            f"Structural scores: `eval/results/structure.json`, generated under "
            f"`eval/profile.yaml`'s `structure:` policy (sha256 "
            f"`{structure_meta.get('policy_sha256', '?')[:16]}...`), "
            f"{structure_meta.get('n_scored', '?')} scored / "
            f"{structure_meta.get('n_not_applicable', '?')} not-applicable / "
            f"{structure_meta.get('n_failed', '?')} failed of "
            f"{structure_meta.get('n_records', '?')} records.")
    else:
        lines.append(
            "Structural scores: **not available.** " + (structure_warning or ""))
    if policy_warning:
        lines.append("")
        lines.append(f"**Warning:** {policy_warning}")
    return lines


def render_model_summary(summary_rows):
    lines = ["", "## All models", "",
             "Macro-averaged across tasks: each model's per-task means are averaged together "
             "so a task with more trials carries no extra weight. Gate and Reliability are raw "
             "counts across every trial (not macro-averaged), since they are pass/fail "
             "headcounts rather than continuous means. Sorted by mutation kill rate, "
             "descending -- this is the ranking the composite obscured.", "",
             "| Model | Harness | Effort | Tasks | Trials | Gate | Mutation kill | Structure | "
             "Lint clean | Scope clean | Reliability | Median full-pass duration |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in summary_rows:
        lines.append(
            f"| `{r['model']}` | {r['harness']} | {r['effort'] or '--'} | {r['n_tasks']} | "
            f"{r['n_trials']} | {fmt_gate(r['gate_n_pass'], r['gate_n_total'])} | "
            f"{fmt_pct_range(r['mutation_mean'], r['mutation_task_means'])} | "
            f"{fmt_structure_or_dagger(r['structure_mean'], r['structure_withheld'])} | "
            f"{aggregate.fmt_pct(r['lint_clean_fraction'])} | "
            f"{aggregate.fmt_pct(r['scope_clean_fraction'])} | "
            f"{fmt_reliability(r['reliability_counts'])} | "
            f"{aggregate.fmt_hm(r['median_duration_seconds'])} |"
        )
    return lines


def main():
    root = aggregate.repo_root()
    records, n_skipped, n_skipped_reference = aggregate.load_records(root)
    out_path = os.path.join(root, "eval", "profile.md")

    threshold = load_gate_threshold(root)
    structure_lookup, structure_meta, structure_warning = load_structure_scores(root)
    structure_file_missing = structure_meta is None and structure_warning is not None
    if structure_warning:
        print(f"[profile_view] WARNING: {structure_warning}", file=sys.stderr)
    policy_warning = check_policy_freshness(root, structure_meta)
    if policy_warning:
        print(f"[profile_view] WARNING: {policy_warning}", file=sys.stderr)

    if not records:
        with open(out_path, "w") as f:
            f.write("\n".join(render_header(structure_meta, structure_warning,
                                             policy_warning)) + "\nNo graded trials yet.\n")
        print(f"[profile_view] no graded trials found -- wrote empty {out_path}")
        return 0

    # P1 (external review, 2026-09-07): a sidecar that merely LAGS the records
    # is more dangerous than a missing one. Nothing in run_batch -> run_trial ->
    # grade_trial regenerates it, so this is the state after every fresh
    # grading run, and the only previous trace was one aggregated footnote line
    # among a hundred others.
    absent_from_sidecar = ([] if structure_file_missing
                            else [r["run_id"] for r in records
                                  if r["run_id"] not in structure_lookup])
    if absent_from_sidecar:
        print(f"[profile_view] WARNING: {len(absent_from_sidecar)} of {len(records)} graded "
              f"trial(s) have no entry in eval/results/structure.json -- their Structure "
              f"cells are computed over the remaining trials only, and any affected per-task "
              f"cell is marked '*'. Run `python eval/harness/structure.py sweep` and re-run "
              f"this script.", file=sys.stderr)

    if n_skipped_reference:
        print(f"[profile_view] {n_skipped_reference} reference-check or PM-branch record(s) "
              f"(harness=='none') excluded -- evaluator-validation evidence, not trials.")

    # ---- group by (cohort, task_id, harness, model, effort) ----
    # aggregate.group_and_order() is the single implementation, shared with
    # aggregate.py's own main(). This file used to reimplement it character-
    # for-character, which is exactly the fork this module's docstring
    # forbids: the two agreed at the time, so a later change to cohort
    # ordering would have diverged silently, blending a multi-cohort task in
    # one artifact and not the other.
    (by_group, cohorts_by_task, ordered_cohorts_by_task,
     multi_cohort_tasks, current_cohort) = aggregate.group_and_order(
        records, warn_prefix="profile_view")

    units = {}  # (cohort, task_id) -> {(harness, model, effort): stats}
    for (cohort, task_id, harness, model, effort), trials in by_group.items():
        stats = group_stats_profile(trials, structure_lookup, structure_file_missing, threshold)
        units.setdefault((cohort, task_id), {})[(harness, model, effort)] = stats

    # ---- model profile: macro-average each combo's per-task stats, current cohort only ----
    combo_units = {}
    for (cohort, task_id), combos in units.items():
        if cohort != current_cohort[task_id]:
            continue
        for combo, stats in combos.items():
            combo_units.setdefault(combo, []).append(stats)

    n_tasks_total = len(current_cohort)
    eligible_tasks = structure_eligible_tasks(structure_lookup)
    summary_rows = [
        build_model_row(harness, model, effort, stats_list, n_tasks_total,
                         eligible_tasks)
        for (harness, model, effort), stats_list in combo_units.items()
    ]
    summary_rows.sort(key=lambda r: (r["mutation_mean"] is None, -(r["mutation_mean"] or 0)))

    lines = render_header(structure_meta, structure_warning, policy_warning)
    lines.append(f"\nTotal graded v2 trials: {len(records)} across {len(by_group)} "
                 f"(cohort, task, harness, model, effort) groups.")
    if n_skipped:
        lines.append(f"Pre-v2 records skipped (no `provenance` block): {n_skipped}.")
    lines += render_model_summary(summary_rows)

    # ---- per task (per cohort) ----
    footnote_gate = footnote_incomplete = footnote_integrity = 0
    footnote_withheld = sum(1 for r in summary_rows if r["structure_withheld"])
    grader_notes = set()
    struct_missing_reasons = collections.Counter()
    for task_id in sorted(cohorts_by_task):
        ordered_cohorts = ordered_cohorts_by_task[task_id]
        multi = len(ordered_cohorts) > 1
        for cohort in ordered_cohorts:
            combos = units.get((cohort, task_id), {})
            heading = f"## Task: `{task_id}`"
            if multi:
                heading += f" -- {aggregate.cohort_label(cohort)}"
            lines += ["", heading, "",
                      "| Model | Harness | Effort | Trials | Gate | Mutation kill | Structure | "
                      "Lint clean | Scope clean | Reliability | Latest report |",
                      "|---|---|---|---|---|---|---|---|---|---|---|"]
            rows = sorted(combos.items(),
                          key=lambda kv: (kv[1]["mutation_mean"] is None,
                                          -(kv[1]["mutation_mean"] or 0)))
            for (harness, model, effort), s in rows:
                footnote_gate += s["gate_fail_n"]
                footnote_incomplete += sum(1 for t in s["trials"] if t.get("missing_deliverables"))
                footnote_integrity += s["integrity_n"]
                for note in aggregate.grader_provenance_warnings(s["trials"]):
                    grader_notes.add(f"`{task_id}` / `{model}`: {note}")
                for _run_id, reason in s["struct_missing"]:
                    struct_missing_reasons[reason] += 1
                lines.append(
                    f"| `{model}` | {harness} | {effort or '--'} | {s['n']} | "
                    f"{fmt_gate(s['gate_n_pass'], s['gate_n_total'])} | "
                    f"{aggregate.fmt_pct(s['mutation_mean'])} | "
                    f"{fmt_structure_partial(s)} | "
                    f"{aggregate.fmt_pct(s['lint_clean_fraction'])} | "
                    f"{aggregate.fmt_pct(s['scope_clean_fraction'])} | "
                    f"{fmt_reliability(s['reliability_counts'])} | "
                    f"[report]({s['latest_report']}) |"
                )

    lines += ["", "## Footnotes", "",
              f"- Gate failures are retained, not excluded: {footnote_gate} trial(s) scored "
              f"below the correctness-gate threshold ({threshold:.2f}); they still appear in "
              "every other column.",
              f"- Incomplete submissions are retained, not excluded: {footnote_incomplete} "
              "trial(s) were missing a required deliverable.",
              f"- ‡ structural mean withheld: {footnote_withheld} model row(s) do not cover "
              f"every structure-eligible task ({', '.join(f'`{t}`' for t in sorted(eligible_tasks)) or 'none'}), "
              "so their structural means are not comparable and are withheld rather than "
              "averaged over whichever subset they happen to have run. Per-task Structure "
              "cells below are unaffected. See docs/EVAL-CONSOLIDATION-TRIAL.md.",
              f"- `*` partial structural coverage: {len(absent_from_sidecar)} graded trial(s) "
              "have no entry in `eval/results/structure.json`, so a marked Structure cell is a "
              "mean over only the trials the sidecar covers. Re-run "
              "`python eval/harness/structure.py sweep`.",
              f"- Integrity violations: {footnote_integrity} trial(s) touched a grader-owned "
              "path outside their authorized surface (counted as scope-dirty above)."]
    if struct_missing_reasons:
        breakdown = ", ".join(f"{reason} ({n})" for reason, n in
                              sorted(struct_missing_reasons.items(), key=lambda kv: -kv[1]))
        lines.append(f"- Structural score not available for "
                     f"{sum(struct_missing_reasons.values())} trial(s): {breakdown}. A `null` "
                     "structural score (e.g. a task whose only deliverable is a test file) is "
                     "rendered `--`, never coerced to 0.")
    if n_skipped:
        lines.append(f"- Pre-v2 records skipped: {n_skipped} (graded before rubric v2's "
                     "provenance block existed; not comparable to the trials above).")
    if grader_notes:
        # Grouped by note text, not semicolon-joined into one line. There are
        # 81 of these over the current 219 records and ~79 carry the identical
        # message, so joining them (as aggregate.py does) yields a single
        # ~6000-character paragraph nobody reads -- functionally the same as
        # not reporting it. Grouping keeps every (task, model) pair visible
        # while making the shape of the caveat legible at a glance.
        by_note = collections.defaultdict(list)
        for entry in sorted(grader_notes):
            group, _, note = entry.partition(": ")
            by_note[note].append(group)
        lines.append("- Grader provenance (not part of the cohort key, so these ARE averaged "
                     "together -- check before quoting them):")
        for note, groups in sorted(by_note.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            lines.append(f"  - {note} -- {len(groups)} group(s): " + ", ".join(groups))
        # Deliberately a one-line summary, unlike aggregate.py, which prints
        # every note. There are 84 of them over the current 219 records (all
        # historical "uncommitted grader tree" conditions the operator already
        # knows about), and enumerating them on every run buries the one line
        # that says where the output went. The full list is still in this
        # file's own footnote above -- nothing is hidden, only relocated.
        print(f"[profile_view] NOTE: {len(grader_notes)} grader-provenance caveat(s) "
              f"across {len({n.split(' / ')[0] for n in grader_notes})} task(s) -- "
              f"listed in the Footnotes section of the generated file.", file=sys.stderr)
    if multi_cohort_tasks:
        lines.append(f"- Cohort split: {len(multi_cohort_tasks)} task(s) span more than one "
                     "rubric/task-contract cohort -- "
                     + ", ".join(f"`{t}`" for t in sorted(multi_cohort_tasks)) + ".")

    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[profile_view] wrote {out_path} ({len(by_group)} groups from {len(records)} "
          f"v2 trials, {n_skipped} pre-v2 skipped)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
