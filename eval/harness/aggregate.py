#!/usr/bin/env python3
"""Roll up every graded v2 trial in eval/results/runs/*.json into eval/leaderboard.md.

This is the single running artifact: one row per (task, harness, model,
effort), aggregated across every trial that has ever been run, each linking
to its full per-trial report. Never hand-edit leaderboard.md -- re-run this
script after every new trial is graded.

A record's `provenance` block is what makes it safe to aggregate at all: two
trials of the "same" task graded under a different rubric.yaml or a different
spec.md/meta.yaml must never be averaged into one number, since a fixed
score under a changed policy isn't the same measurement. `cohort_key()` below
is exactly that partition -- rubric version and hash, task-contract hash, judge
prompt hash, and the resolved baseline commit -- and a task_id that spans more
than one cohort gets split into clearly labelled sections rather than silently
blended.

Usage:
    python eval/harness/aggregate.py
"""
import glob
import json
import os
import statistics
import subprocess
import sys

import yaml


def repo_root():
    out = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True, check=True)
    return out.stdout.strip()


def load_rubric(root):
    with open(os.path.join(root, "eval", "rubric.yaml")) as f:
        return yaml.safe_load(f)


def load_task_summaries(root):
    """task_id -> its leaderboard_summary (or None if absent), read from
    eval/leaderboard_summaries.yaml -- NOT from eval/tasks/<id>/meta.yaml.

    Deliberately kept out of meta.yaml: grade_trial.py hashes spec.md +
    meta.yaml bytes into `task_contract_sha256`, which cohort_key() below
    uses to decide whether trials may be averaged together. A purely
    cosmetic edit to meta.yaml still changes that hash and silently splits
    a task's rows into unmergeable cohorts -- this happened for real on
    2026-09-07 (see leaderboard_summaries.yaml's own header comment) before
    this file existed. Always the current summary, even for a superseded
    cohort still shown in its own section below -- what a task tests and
    what a low/high score means does not change across a task revision, so
    this is not kept per-cohort the way scores are."""
    path = os.path.join(root, "eval", "leaderboard_summaries.yaml")
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def load_records(root):
    """Returns (v2_records, n_skipped_pre_v2, n_skipped_reference). A record
    with no `provenance` block predates the v2 rubric rewrite and carries
    `total_score` instead of `deterministic_score`/`composite_score` --
    mixing it in would silently average two different scoring definitions
    together. A record with harness == "none" was never a real trial at
    all -- eval/harness/reference_check.py grades a task's reference_solution/
    (or a control variant of it) through the real pipeline as evaluator-
    validation evidence, and such a record should always be archived out of
    eval/results/runs/ once its purpose is served (see reference_check.py's
    own docstring). This is a defense-in-depth backstop for a record left
    behind by mistake: it must never reach the leaderboard as a fake "model"
    row (codex/gpt-5.6-sol review, 2026-09-05)."""
    v2, skipped, skipped_reference = [], 0, 0
    for path in sorted(glob.glob(os.path.join(root, "eval", "results", "runs", "*.json"))):
        with open(path) as f:
            record = json.load(f)
        if not record.get("provenance"):
            skipped += 1
            continue
        if record.get("harness") == "none":
            skipped_reference += 1
            continue
        v2.append(record)
    return v2, skipped, skipped_reference


def cohort_key(record):
    """What has to match before two records may be averaged together: the
    scoring policy (rubric bytes), the task contract (spec.md + meta.yaml
    bytes), the evaluator content actually exercised (hidden tests + mutation
    bank bytes), the judged instrument (judge prompt bytes), and the
    substrate the trial started from.

    Deliberately NOT keyed on the grader revision. Partitioning on that would
    start a new cohort on every commit to this repository, including
    documentation-only ones, fragmenting a batch that was graded by identical
    code. A grader revision that differs within a group is surfaced as a loud
    warning and a footnote instead -- see grader_provenance_warnings()."""
    p = record["provenance"]
    return (p.get("rubric_version"), p.get("rubric_sha256"), p.get("task_contract_sha256"),
            p.get("evaluator_content_sha256"),
            (p.get("judge") or {}).get("prompt_sha256"), p.get("baseline_commit"))


def cohort_label(cohort):
    rubric_version, rubric_sha, contract_sha, evaluator_sha, prompt_sha, baseline = cohort
    return (f"rubric v{rubric_version}, contract {(contract_sha or '?')[:8]} "
            f"(rubric {(rubric_sha or '?')[:8]}, evaluator content {(evaluator_sha or '?')[:8]}, "
            f"judge prompt {(prompt_sha or '?')[:8]}, baseline {(baseline or '?')[:8]})")


def grader_provenance_warnings(trials):
    """Cohort membership does not pin the grader code itself. Two things can
    still make a group's records incomparable without changing the cohort:
    more than one grader revision, or a grader graded from a dirty tree (where
    HEAD says nothing about what the arithmetic actually was)."""
    revs = {(t["provenance"] or {}).get("grader_git_rev") for t in trials}
    dirty = sum(1 for t in trials if (t["provenance"] or {}).get("grader_git_dirty"))
    notes = []
    if len(revs) > 1:
        notes.append(f"{len(revs)} different grader revisions")
    if dirty:
        notes.append(f"{dirty} trial(s) graded from an uncommitted grader tree")
    return notes


def group_and_order(records, warn_prefix="aggregate"):
    """The grouping and cohort-ordering both leaderboard.md and profile.md
    need, computed once so the two can never silently diverge.

    profile_view.py previously reimplemented this block character-for-
    character against the copy that used to live in main(), which is exactly
    the fork its own docstring forbade -- an external review caught it while
    the two were still identical, i.e. before the divergence could surface as
    a blended cohort in one artifact and not the other. Returns:

      by_group                 (cohort, task_id, harness, model, effort) -> [record]
      cohorts_by_task          task_id -> {cohort}
      ordered_cohorts_by_task  task_id -> [cohort], chronological by oldest run_id
                               so the LAST entry is that task's current cohort
      multi_cohort_tasks       task_ids spanning more than one cohort
      current_cohort           task_id -> its current cohort

    Ordering is chronological, not hash order, deliberately: a task
    re-versioned into a new cohort must render its sections oldest-first and
    summarize only its newest. Emits the same loud multi-cohort warning as
    before, tagged with the caller's name."""
    by_group = {}
    for r in records:
        key = (cohort_key(r), r["task_id"], r["harness"], r["model"], r.get("effort"))
        by_group.setdefault(key, []).append(r)

    cohorts_by_task = {}
    for (cohort, task_id, _, _, _) in by_group:
        cohorts_by_task.setdefault(task_id, set()).add(cohort)
    multi_cohort_tasks = {t for t, c in cohorts_by_task.items() if len(c) > 1}
    ordered_cohorts_by_task = {
        task_id: sorted(cohorts,
                        key=lambda c: min(r["run_id"] for r in records
                                          if r["task_id"] == task_id and cohort_key(r) == c))
        for task_id, cohorts in cohorts_by_task.items()}
    for t in sorted(multi_cohort_tasks):
        print(f"[{warn_prefix}] WARNING: task {t!r} has {len(cohorts_by_task[t])} distinct "
              f"rubric/task-contract cohorts -- rendering each as its own section; "
              f"they are never averaged together.", file=sys.stderr)
    current_cohort = {t: cohorts[-1] for t, cohorts in ordered_cohorts_by_task.items()}
    return (by_group, cohorts_by_task, ordered_cohorts_by_task,
            multi_cohort_tasks, current_cohort)


def fmt_pct(x):
    return f"{x*100:.0f}%" if isinstance(x, (int, float)) else "--"


def fmt_pct_or_dagger(x, withheld):
    return "--†" if withheld else fmt_pct(x)


def fmt_score(x):
    return f"{x:.1f}" if isinstance(x, (int, float)) else "--"


def fmt_score_or_dagger(x, withheld):
    return "--†" if withheld else fmt_score(x)


def mean_or_none(vals, ndigits=1):
    vals = [v for v in vals if isinstance(v, (int, float))]
    return round(statistics.mean(vals), ndigits) if vals else None


def mean_cat(trials, cat_id):
    """Mean of a category's fraction (0-1) across trials that scored it --
    unscored (null) entries are excluded from the denominator, same principle
    as grade_trial.py's own renormalization over scored weight."""
    vals = [t.get("category_scores", {}).get(cat_id) for t in trials]
    return mean_or_none(vals, ndigits=3)


def median_range(vals, unit="s"):
    vals = [v for v in vals if isinstance(v, (int, float))]
    if not vals:
        return "--"
    med = statistics.median(vals)
    return f"{med:.0f}{unit} ({min(vals):.0f}-{max(vals):.0f}{unit})"


def fmt_hm(seconds):
    """Seconds -> 'HhMMm' (or 'Mm' under an hour), for the model summary's
    median-duration column. `median_range()` above stays in raw seconds with
    a min-max range for the per-task operational telemetry table; this is a
    coarser, single-number sibling for the top-level summary."""
    if not isinstance(seconds, (int, float)):
        return "--"
    total_minutes = round(seconds / 60)
    h, m = divmod(total_minutes, 60)
    return f"{h}h {m:02d}m" if h else f"{m}m"


def full_pass_duration_and_tokens(stats_list, n_tasks_total):
    """(median duration_seconds, median total tokens) to complete one full
    pass through every task -- i.e., sum a matching attempt's duration/tokens
    across all N tasks, then take the median over the model's repeated
    attempts. NOT the median of a single task-trial in isolation: a model's
    "attempt 1" on Task 001 and "attempt 1" on Task 002 were never run in the
    same session (run_batch.py runs task-major: all of Task 001's trials,
    then all of Task 002's), so pairing by same trial index is a proxy for
    "one full benchmark pass", not a literal shared run -- the best available
    one, since trial_index isn't itself a field on the graded record and each
    task's own attempts are otherwise interchangeable repeats.

    `stats_list` is one model's per-task stats for its current cohort (each
    carrying its own `trials` list). Returns (None, None) unless every task
    in the whole leaderboard (`n_tasks_total`) is present AND every task has
    at least one trial to pair -- a model with incomplete task coverage has
    no well-defined "time/tokens for a full pass" figure."""
    if len(stats_list) < n_tasks_total:
        return None, None
    per_task = [sorted(s["trials"], key=lambda t: t["run_id"]) for s in stats_list]
    n_attempts = min(len(pt) for pt in per_task)
    if n_attempts == 0:
        return None, None
    duration_sums, token_sums = [], []
    for i in range(n_attempts):
        attempt = [pt[i] for pt in per_task]
        durations = [t.get("duration_seconds") for t in attempt]
        if all(isinstance(d, (int, float)) for d in durations):
            duration_sums.append(sum(durations))
        tok_totals = []
        for t in attempt:
            tu = t.get("token_usage") or {}
            i_tok, o_tok = tu.get("input_tokens"), tu.get("output_tokens")
            if not (isinstance(i_tok, (int, float)) or isinstance(o_tok, (int, float))):
                tok_totals = None
                break
            tok_totals.append((i_tok or 0) + (o_tok or 0))
        if tok_totals is not None:
            token_sums.append(sum(tok_totals))
    med_dur = statistics.median(duration_sums) if duration_sums else None
    med_tok = statistics.median(token_sums) if token_sums else None
    return med_dur, med_tok


def token_stats(trials):
    """Mean input/output tokens plus the parser source(s) that produced them.
    Claude, Codex, and opencode (the default harness) each expose differently
    named cache/reasoning token fields under `token_usage` (see harnesses.py's
    USAGE_PARSERS), so a bare in/out total is only ever comparable within one
    harness's own parser, not across."""
    ins, outs, sources = [], [], set()
    for t in trials:
        tu = t.get("token_usage") or {}
        if tu.get("source"):
            sources.add(tu["source"])
        if isinstance(tu.get("input_tokens"), (int, float)):
            ins.append(tu["input_tokens"])
        if isinstance(tu.get("output_tokens"), (int, float)):
            outs.append(tu["output_tokens"])
    if not ins and not outs:
        return "--"
    in_str = f"{statistics.mean(ins):,.0f}" if ins else "--"
    out_str = f"{statistics.mean(outs):,.0f}" if outs else "--"
    src = ", ".join(sorted(sources)) if sources else "unknown source"
    return f"{in_str} / {out_str} ({src})"


# Display labels only -- which categories exist, their order, and their kind
# (automated vs judged) all come from rubric.yaml's `categories` list; this
# map never changes which categories are scored or how, only how their column
# header reads. An id with no entry falls back to a titleized form of itself.
_LABELS = {
    "correctness": "Correctness",
    "test_adequacy": "Test adequacy",
    "scope_discipline": "Scope",
    "hygiene": "Hygiene",
    "readability": "Readability",
    "maintainability": "Maintainability",
}


def label(cat_id):
    return _LABELS.get(cat_id, cat_id.replace("_", " ").capitalize())


def group_stats(trials, automated_ids, judged_ids):
    """Aggregate one (cohort, task_id, harness, model, effort) group of
    trials into the numbers every table needs. A group where any trial has
    judge_same_model set withholds ALL judged and composite evidence for the
    whole group -- the judge scored its own submission, so those numbers
    must never enter a comparison anywhere, including the macro-averaged
    model summary. Deterministic evidence is unaffected (see rubric.yaml's
    judge.same_model_policy)."""
    judge_same_model = any(t.get("judge_same_model") for t in trials)

    det = mean_or_none([t.get("deterministic_score") for t in trials])
    det_vals = [t.get("deterministic_score") for t in trials
                if isinstance(t.get("deterministic_score"), (int, float))]

    comp = None if judge_same_model else mean_or_none(
        [t.get("composite_score") for t in trials])

    judged = {}
    for cat_id in judged_ids:
        if judge_same_model:
            judged[cat_id] = None
        else:
            judged[cat_id] = mean_or_none(
                [(t.get("judged_scores") or {}).get(cat_id) for t in trials])

    n = len(trials)
    n_complete = sum(1 for t in trials if t.get("complete_submission"))
    latest = sorted(trials, key=lambda t: t["run_id"])[-1]

    return {
        "n": n,
        "n_complete": n_complete,
        "complete_fraction": (n_complete / n) if n else None,
        "det_mean": det,
        "det_best": max(det_vals) if det_vals else None,
        "det_worst": min(det_vals) if det_vals else None,
        "comp_mean": comp,
        "judged": judged,
        "judge_same_model": judge_same_model,
        "automated": {cat_id: mean_cat(trials, cat_id) for cat_id in automated_ids},
        "latest_report": f"results/reports/{latest['run_id']}.md",
        "gate_failed_n": sum(1 for t in trials if t.get("gate_status") == "failed"),
        "incomplete_n": n - n_complete,
        "integrity_n": sum(1 for t in trials if t.get("integrity_violation")),
    }


def main():
    root = repo_root()
    rubric = load_rubric(root)
    task_summaries = load_task_summaries(root)
    records, n_skipped, n_skipped_reference = load_records(root)
    out_path = os.path.join(root, "eval", "leaderboard.md")

    if not records:
        # Still (re)write the file rather than leave stale rows behind --
        # e.g. after every prior run was archived out of eval/results/runs/.
        # Kept byte-identical to the pre-v2 empty case; the skip counts (if
        # any) are reported on stdout only, not in this file.
        with open(out_path, "w") as f:
            f.write("# Leaderboard\n\nGenerated by `eval/harness/aggregate.py` "
                     "from every graded trial in `eval/results/runs/`. Do not "
                     "hand-edit -- re-run the script instead.\n\nNo graded "
                     "trials yet.\n")
        notes = []
        if n_skipped:
            notes.append(f"{n_skipped} pre-v2 record(s) skipped")
        if n_skipped_reference:
            notes.append(f"{n_skipped_reference} reference-check record(s) skipped")
        note = f" ({', '.join(notes)})" if notes else ""
        print(f"[aggregate] no graded trials found -- wrote empty {out_path}{note}")
        return 0

    if n_skipped_reference:
        print(f"[aggregate] {n_skipped_reference} reference-check record(s) "
              f"(harness=='none') found in eval/results/runs/ and excluded from "
              f"the leaderboard -- these are evaluator-validation evidence, not "
              f"trials; archive them out (see reference_check.py's docstring).")

    automated_ids = [c["id"] for c in rubric["categories"] if c["kind"] == "automated"]
    judged_ids = [c["id"] for c in rubric["categories"] if c["kind"] == "judged"]

    order_field_by_ordering = {"deterministic": "det_mean", "composite": "comp_mean"}
    ordering = rubric.get("scoring", {}).get("default_ordering")
    sort_field = order_field_by_ordering.get(ordering)
    if sort_field is None:
        print(f"[aggregate] WARNING: rubric.yaml's scoring.default_ordering "
              f"{ordering!r} is not 'deterministic' or 'composite' -- defaulting "
              f"leaderboard sort to deterministic.", file=sys.stderr)
        sort_field = "det_mean"

    def sort_key(stats):
        v = stats[sort_field]
        return (v is None, -(v or 0))

    # ---- group by (cohort, task_id, harness, model, effort) ----
    # Shared with profile_view.py -- see group_and_order()'s docstring.
    (by_group, cohorts_by_task, ordered_cohorts_by_task,
     multi_cohort_tasks, current_cohort) = group_and_order(records)

    # unit = one (cohort, task_id) pair, the thing the model summary
    # macro-averages over. A task re-versioned into a new cohort counts as a
    # separate unit, same as a different task_id would -- never blended.
    units = {}  # (cohort, task_id) -> {(harness, model, effort): stats}
    for (cohort, task_id, harness, model, effort), trials in by_group.items():
        stats = group_stats(trials, automated_ids, judged_ids)
        stats["trials"] = trials          # kept for the telemetry table below
        units.setdefault((cohort, task_id), {})[(harness, model, effort)] = stats

    # ---- 1. model summary: macro-average each combo's per-TASK stats ----
    # One unit per task_id, never per (cohort, task_id): a task that spans two
    # cohorts would otherwise be counted twice in a single headline row, which
    # is exactly the blending the per-task sections below exist to prevent.
    # Superseded cohorts are reachable in their own task sections; the summary
    # reports only each task's current one.
    combo_units = {}  # (harness, model, effort) -> [stats, ...] one per task
    for (cohort, task_id), combos in units.items():
        if cohort != current_cohort[task_id]:
            continue
        for combo, stats in combos.items():
            combo_units.setdefault(combo, []).append(stats)

    n_tasks_total = len(current_cohort)
    summary_rows = []
    for (harness, model, effort), stats_list in combo_units.items():
        med_duration, med_tokens = full_pass_duration_and_tokens(stats_list, n_tasks_total)
        row = {
            "harness": harness, "model": model, "effort": effort,
            "n_tasks": len(stats_list),
            "n_trials": sum(s["n"] for s in stats_list),
            "complete_fraction": mean_or_none([s["complete_fraction"] for s in stats_list]),
            "det_mean": mean_or_none([s["det_mean"] for s in stats_list]),
            "comp_mean": mean_or_none([s["comp_mean"] for s in stats_list]),
            "judged": {cid: mean_or_none([s["judged"][cid] for s in stats_list])
                       for cid in judged_ids},
            "any_withheld": any(s["judge_same_model"] for s in stats_list),
            "median_duration_seconds": med_duration,
            "median_tokens": med_tokens,
        }
        summary_rows.append(row)
    summary_rows.sort(key=sort_key)

    lines = [
        "# Leaderboard",
        "",
        "Generated by `eval/harness/aggregate.py` from every graded v2 trial in "
        "`eval/results/runs/`. Do not hand-edit -- re-run the script instead.",
        "",
        f"Total graded v2 trials: {len(records)} across {len(by_group)} "
        f"(cohort, task, harness, model, effort) groups.",
    ]
    if n_skipped:
        lines.append(f"Pre-v2 records skipped (no `provenance` block): {n_skipped}.")
    lines += ["", "## Model summary", "",
              "Macro-averaged across tasks: each model's per-task means are averaged "
              "together, so a task with more trials, hidden-test nodes, or mutations "
              "carries no extra weight in this table. Where a task spans more than one "
              "rubric/task-contract cohort, only its current cohort is summarized here; "
              "superseded cohorts appear in that task's own section below. Duration and "
              "tokens are not part of any score: each is the median, over the model's "
              "repeated attempts, of that attempt's total across every task -- e.g. "
              "attempt 1's Task 001 + Task 002 + ... + Task 005 duration summed, then "
              "the median of that sum over attempts 1/2/3 -- i.e. one full pass through "
              "the whole task bank, not a single task-trial in isolation. Shown only for "
              "a model with a complete, equal-count trial run on every task; `--` "
              "otherwise. Token totals (input+output) are only comparable within one "
              "harness's own usage parser, never across rows with a different harness "
              "(see the per-task operational telemetry tables below).", "",
              "| Model | Harness | Effort | Tasks | Trials | Complete | Deterministic | "
              "Readability | Maintainability | Composite | Median full-pass duration | "
              "Median full-pass tokens |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in summary_rows:
        w = r["any_withheld"]
        med_tok = r["median_tokens"]
        lines.append(
            f"| `{r['model']}` | {r['harness']} | {r['effort'] or '--'} | {r['n_tasks']} | "
            f"{r['n_trials']} | {fmt_pct(r['complete_fraction'])} | {fmt_score(r['det_mean'])} | "
            f"{fmt_pct_or_dagger(r['judged'].get('readability'), w)} | "
            f"{fmt_pct_or_dagger(r['judged'].get('maintainability'), w)} | "
            f"{fmt_score_or_dagger(r['comp_mean'], w)} | "
            f"{fmt_hm(r['median_duration_seconds'])} | "
            f"{f'{med_tok:,.0f}' if isinstance(med_tok, (int, float)) else '--'} |"
        )

    # ---- 2 & 3. per-task (per-cohort, when a task spans more than one)
    # quality + operational telemetry tables ----
    footnote_gate = footnote_incomplete = footnote_integrity = footnote_withheld = 0
    grader_notes = set()
    for task_id in sorted(cohorts_by_task):
        ordered_cohorts = ordered_cohorts_by_task[task_id]
        multi = len(ordered_cohorts) > 1
        for cohort in ordered_cohorts:
            combos = units.get((cohort, task_id), {})
            heading = f"## Task: `{task_id}`"
            if multi:
                heading += f" -- {cohort_label(cohort)}"
            lines += ["", heading]
            summary = task_summaries.get(task_id)
            if summary:
                lines += ["", summary.strip()]
            else:
                print(f"[aggregate] WARNING: no leaderboard_summary in "
                      f"eval/tasks/{task_id}/meta.yaml", file=sys.stderr)

            quality_rows = sorted(combos.items(), key=lambda kv: sort_key(kv[1]))
            lines += ["", "### Quality", "",
                      "| Model | Harness | Effort | Trials | Complete | Det. mean | "
                      "Det. best | Det. worst | " + " | ".join(label(c) for c in automated_ids)
                      + " | " + " | ".join(label(c) for c in judged_ids)
                      + " | Composite | Latest report |",
                      "|" + "---|" * (10 + len(automated_ids) + len(judged_ids))]
            for (harness, model, effort), s in quality_rows:
                w = s["judge_same_model"]
                footnote_gate += s["gate_failed_n"]
                footnote_incomplete += s["incomplete_n"]
                footnote_integrity += s["integrity_n"]
                footnote_withheld += 1 if w else 0
                for note in grader_provenance_warnings(s["trials"]):
                    grader_notes.add(f"`{task_id}` / `{model}`: {note}")
                cat_cells = " | ".join(fmt_pct(s["automated"].get(c)) for c in automated_ids)
                judged_cells = " | ".join(
                    fmt_pct_or_dagger(s["judged"].get(c), w) for c in judged_ids)
                lines.append(
                    f"| `{model}` | {harness} | {effort or '--'} | {s['n']} | "
                    f"{fmt_pct(s['complete_fraction'])} | {fmt_score(s['det_mean'])} | "
                    f"{fmt_score(s['det_best'])} | {fmt_score(s['det_worst'])} | "
                    f"{cat_cells} | {judged_cells} | {fmt_score_or_dagger(s['comp_mean'], w)} | "
                    f"[report]({s['latest_report']}) |"
                )

            lines += ["", "### Operational telemetry (not part of any score)", "",
                      "Claude, Codex, and opencode each expose differently named "
                      "cache/reasoning token fields in `token_usage` -- cross-harness token "
                      "totals below are not directly comparable, only within one harness's "
                      "own parser.", "",
                      "| Model | Harness | Effort | Model duration median (min-max) | "
                      "Venv setup median (min-max) | Tokens in/out (source) |",
                      "|---|---|---|---|---|---|"]
            for (harness, model, effort), s in sorted(
                    combos.items(), key=lambda kv: (kv[0][1], kv[0][0], kv[0][2] or "")):
                trials = s["trials"]
                lines.append(
                    f"| `{model}` | {harness} | {effort or '--'} | "
                    f"{median_range([t['duration_seconds'] for t in trials])} | "
                    f"{median_range([t['venv_setup_seconds'] for t in trials])} | "
                    f"{token_stats(trials)} |"
                )

    lines += ["", "## Footnotes", "",
              f"- † judge is the trial model: {footnote_withheld} group(s) have their "
              "Readability, Maintainability, and Composite columns withheld from every "
              "comparison (deterministic evidence is unaffected). See rubric.yaml's "
              "judge.same_model_policy.",
              f"- Gate failures are retained, not excluded: {footnote_gate} trial(s) failed "
              "a rubric gate and were scored 0 rather than dropped.",
              f"- Incomplete submissions are retained, not excluded: {footnote_incomplete} "
              "trial(s) were missing a required deliverable.",
              f"- Integrity violations: {footnote_integrity} trial(s) touched a "
              "grader-owned path outside their authorized surface (scope_discipline "
              "forced to 0 for that trial)."]
    if n_skipped:
        lines.append(f"- Pre-v2 records skipped: {n_skipped} (graded before rubric v2's "
                      "provenance block existed; not comparable to the trials above).")
    if grader_notes:
        lines.append("- Grader provenance (not part of the cohort key, so these ARE averaged "
                      "together -- check before quoting them): "
                      + "; ".join(sorted(grader_notes)) + ".")
        for note in sorted(grader_notes):
            print(f"[aggregate] WARNING: {note}", file=sys.stderr)
    if multi_cohort_tasks:
        lines.append(f"- Cohort split: {len(multi_cohort_tasks)} task(s) span more than one "
                      "rubric/task-contract cohort -- "
                      + ", ".join(f"`{t}`" for t in sorted(multi_cohort_tasks)) + ".")

    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[aggregate] wrote {out_path} ({len(by_group)} groups from {len(records)} "
          f"v2 trials, {n_skipped} pre-v2 skipped)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
