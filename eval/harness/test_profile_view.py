"""Focused regression tests for profile_view.py: the independent-columns
"model profile" view that replaces aggregate.py's weighted composite (see
docs/EVAL-CONSOLIDATION-PROPOSAL.md).

Run from eval/harness/:
    cd eval/harness && ../../venv/bin/python -m pytest test_profile_view.py -v

Deliberately small: synthetic record dicts built by make_record() below
rather than the real 219, and only the behaviours that would break silently
if a future edit regressed them -- the correctness-gate boundary, null vs.
zero for an unscored structural entry, cohort isolation, macro-averaging,
and (the whole reason this file exists) that no composite ever creeps back
into the rendered output.
"""
import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import aggregate
import profile_view as pv


def make_record(**overrides):
    """A minimal but schema-complete v2 graded record. Every field present
    on a real eval/results/runs/*.json record (see the field inventory
    checked during development) gets a sane default here; tests override
    only what they're exercising."""
    base = {
        "run_id": "20260101T000000Z-999-synth-test-model-1-abc123",
        "task_id": "999-synth",
        "model": "test-model",
        "harness": "claude",
        "effort": "high",
        "baseline_ref": "frozen-substrate",
        "duration_seconds": 100.0,
        "venv_setup_seconds": 5.0,
        "timed_out": False,
        "committed": False,
        "changed_files": ["src/thing.py"],
        "token_usage": {"source": "test", "input_tokens": 10, "output_tokens": 10},
        "rubric_profile": "default",
        "judge_same_model": False,
        "missing_deliverables": [],
        "complete_submission": True,
        "gate_status": "not_applicable",
        "failed_gates": [],
        "integrity_violation": False,
        "judge_status": "ok",
        "deterministic_score": 80.0,
        "composite_score": 78.0,
        "category_scores": {
            "correctness": 0.9,
            "test_adequacy": 0.5,
            "scope_discipline": 1.0,
            "hygiene": 1.0,
        },
        "provenance": {
            "rubric_version": 2,
            "rubric_sha256": "rubric-sha-a",
            "task_contract_sha256": "contract-sha-a",
            "evaluator_content_sha256": "evaluator-sha-a",
            "judge": {"prompt_sha256": "judge-sha-a"},
            "baseline_commit": "baseline-a",
            "grader_git_rev": "rev1",
            "grader_git_dirty": False,
        },
    }
    base.update(overrides)
    return base


# ---- correctness gate: pass/fail split at threshold, None is a FAIL ----

def test_gate_passes_at_exactly_the_threshold():
    r = make_record(category_scores={"correctness": 0.70})
    assert pv.correctness_gate_pass(r, 0.70) is True


def test_gate_fails_just_below_threshold():
    r = make_record(category_scores={"correctness": 0.699})
    assert pv.correctness_gate_pass(r, 0.70) is False


def test_gate_none_correctness_is_a_fail_not_a_skip():
    assert pv.correctness_gate_pass(make_record(category_scores={"correctness": None}), 0.70) is False
    assert pv.correctness_gate_pass(make_record(category_scores={}), 0.70) is False


# ---- reliability status ladder ----

def test_reliability_timed_out_takes_priority():
    r = make_record(timed_out=True, changed_files=[])
    assert pv.reliability_status(r) == "timed_out"


def test_reliability_no_submission_from_empty_diff():
    r = make_record(timed_out=False, changed_files=[])
    assert pv.reliability_status(r) == "no_submission"


def test_reliability_no_submission_flag_honoured_even_with_files_listed():
    r = make_record(timed_out=False, changed_files=["x.py"], no_submission=True)
    assert pv.reliability_status(r) == "no_submission"


def test_reliability_gate_failed():
    r = make_record(gate_status="failed", changed_files=["x.py"], missing_deliverables=[])
    assert pv.reliability_status(r) == "gate_failed"


def test_reliability_incomplete():
    r = make_record(gate_status="passed", changed_files=["x.py"],
                     missing_deliverables=["src/thing.py"])
    assert pv.reliability_status(r) == "incomplete"


def test_reliability_completed():
    r = make_record(gate_status="passed", changed_files=["x.py"], missing_deliverables=[])
    assert pv.reliability_status(r) == "completed"


# ---- structural score: null vs. missing vs. zero ----

def test_structural_score_null_renders_dash_and_is_excluded_from_the_mean():
    trials = [make_record(run_id="r1"), make_record(run_id="r2")]
    structure_lookup = {
        "r1": {"status": "ok", "structural_score": 80.0},
        "r2": {"status": "not_applicable", "structural_score": None,
               "note": "no non-test deliverable"},
    }
    stats = pv.group_stats_profile(trials, structure_lookup, False, 0.70)
    # only r1's 80.0 counted -- r2's null must never be coerced to 0
    assert stats["structure_mean"] == 80.0
    assert pv.fmt_structure(stats["structure_mean"]) == "80.0"
    assert pv.fmt_structure(None) == "--"
    reasons = dict(stats["struct_missing"])
    assert reasons["r2"].startswith("not_applicable")


def test_structural_entry_absent_from_file_renders_dash():
    trials = [make_record(run_id="r3")]
    stats = pv.group_stats_profile(trials, {}, False, 0.70)
    assert stats["structure_mean"] is None
    assert stats["struct_missing"][0][1].startswith("no structural entry")


def test_structure_json_entirely_missing_degrades_to_dash_without_crashing():
    trials = [make_record(run_id="r4")]
    stats = pv.group_stats_profile(trials, {}, True, 0.70)
    assert stats["structure_mean"] is None
    assert stats["struct_missing"][0][1] == "structure.json not found"


# ---- lint/scope "clean" flags ----

def test_clean_fraction_excludes_unscored_trials_from_denominator():
    scored_clean = make_record(run_id="a",
                                category_scores={"correctness": 0.9, "test_adequacy": 0.5,
                                                  "scope_discipline": 1.0, "hygiene": 1.0})
    scored_dirty = make_record(run_id="b",
                                category_scores={"correctness": 0.9, "test_adequacy": 0.5,
                                                  "scope_discipline": 1.0, "hygiene": 0.5})
    unscored = make_record(run_id="c",
                            category_scores={"correctness": 0.9, "test_adequacy": 0.5,
                                              "scope_discipline": 1.0})
    frac = pv.clean_fraction([scored_clean, scored_dirty, unscored], "hygiene")
    assert frac == 0.5  # 1 of 2 SCORED trials clean; the unscored one is excluded, not counted dirty


def test_scope_clean_fraction_forced_dirty_by_integrity_violation():
    r = make_record(category_scores={"correctness": 0.9, "test_adequacy": 0.5,
                                      "scope_discipline": 1.0, "hygiene": 1.0},
                     integrity_violation=True)
    frac = pv.clean_fraction([r], "scope_discipline",
                              extra_dirty=lambda t: t.get("integrity_violation"))
    assert frac == 0.0  # scope_discipline itself reads 1.0, but the integrity flag must still count


# ---- small formatting helpers ----

def test_fmt_reliability_and_merge_counts():
    assert pv.fmt_reliability({"completed": 3}) == "completed 3/3"
    assert pv.fmt_reliability({"completed": 2, "timed_out": 1}) == "completed 2/3 (1 timed_out)"
    merged = pv.merge_counts([{"completed": 2}, {"completed": 1, "incomplete": 1}])
    assert merged == {"completed": 3, "incomplete": 1}


def test_fmt_gate():
    assert pv.fmt_gate(3, 5) == "3/5 pass"
    assert pv.fmt_gate(0, 0) == "--"


# ---- macro-averaging: equal weight per task regardless of trial count ----

def test_macro_averaging_gives_equal_weight_per_task():
    task_a_trials = [
        make_record(run_id=f"a{i}",
                    category_scores={"correctness": 0.9, "test_adequacy": v,
                                      "scope_discipline": 1.0, "hygiene": 1.0})
        for i, v in enumerate([0.2, 0.4, 0.6])
    ]
    task_b_trials = [
        make_record(run_id="b0",
                    category_scores={"correctness": 0.9, "test_adequacy": 1.0,
                                      "scope_discipline": 1.0, "hygiene": 1.0})
    ]
    stats_a = pv.group_stats_profile(task_a_trials, {}, True, 0.70)  # mean 0.4, n=3
    stats_b = pv.group_stats_profile(task_b_trials, {}, True, 0.70)  # mean 1.0, n=1
    row = pv.build_model_row("claude", "test-model", "high", [stats_a, stats_b], n_tasks_total=2)
    # macro average of per-task means: mean(0.4, 1.0) = 0.7 -- NOT the trial-weighted
    # (0.2+0.4+0.6+1.0)/4 = 0.55 that a naive pooled-mean would give.
    assert row["mutation_mean"] == pytest.approx(0.7, abs=1e-6)


# ---- integration: cohort isolation and the no-composite regression check ----

def _write_policy(root):
    """Seed a synthetic repo root with the eval/profile.yaml the view now
    REQUIRES. load_gate_threshold() fails loud on a missing or malformed one
    rather than defaulting, so an integration test that renders the view must
    supply a policy exactly as a real checkout does."""
    eval_dir = os.path.join(root, "eval")
    os.makedirs(eval_dir, exist_ok=True)
    with open(os.path.join(eval_dir, "profile.yaml"), "w") as f:
        f.write("gate:\n"
                "  correctness:\n"
                "    threshold: 0.70\n"
                "structure:\n"
                "  scope: new_files_only\n"
                "  decomposition: {metric: function_count, zero_at: 3, one_at: 18}\n"
                "  length: {metric: median_function_loc, zero_at: 100, one_at: 15}\n"
                "  complexity: {metric: mean_cyclomatic, zero_at: 15, one_at: 2}\n")


def _write_record(runs_dir, record):
    path = os.path.join(runs_dir, record["run_id"] + ".json")
    with open(path, "w") as f:
        json.dump(record, f)


def test_two_cohorts_of_the_same_task_render_as_separate_sections_never_averaged(
        tmp_path, monkeypatch):
    monkeypatch.setattr(aggregate, "repo_root", lambda: str(tmp_path))
    runs_dir = os.path.join(tmp_path, "eval", "results", "runs")
    os.makedirs(runs_dir)
    _write_policy(str(tmp_path))

    old = make_record(
        run_id="20260101T000000Z-999-synth-test-model-1-aaa111", task_id="999-synth",
        category_scores={"correctness": 0.9, "test_adequacy": 0.2,
                          "scope_discipline": 1.0, "hygiene": 1.0},
        provenance={"rubric_version": 2, "rubric_sha256": "sha-old",
                    "task_contract_sha256": "contract-a", "evaluator_content_sha256": "ev-a",
                    "judge": {"prompt_sha256": "judge-a"}, "baseline_commit": "base-a",
                    "grader_git_rev": "rev1", "grader_git_dirty": False})
    new = make_record(
        run_id="20260201T000000Z-999-synth-test-model-1-bbb222", task_id="999-synth",
        category_scores={"correctness": 0.9, "test_adequacy": 0.8,
                          "scope_discipline": 1.0, "hygiene": 1.0},
        provenance={"rubric_version": 2, "rubric_sha256": "sha-new",
                    "task_contract_sha256": "contract-a", "evaluator_content_sha256": "ev-a",
                    "judge": {"prompt_sha256": "judge-a"}, "baseline_commit": "base-a",
                    "grader_git_rev": "rev1", "grader_git_dirty": False})
    _write_record(runs_dir, old)
    _write_record(runs_dir, new)

    assert pv.main() == 0
    content = open(os.path.join(tmp_path, "eval", "profile.md")).read()

    assert content.count("## Task: `999-synth`") == 2
    # Model profile (headline) reports only the CURRENT cohort (later run_id,
    # test_adequacy 0.8 -> 80%), never a blend of 0.2 and 0.8.
    model_section = content.split("## Task:")[0]
    assert "80%" in model_section
    assert "50%" not in model_section  # the naive (0.2+0.8)/2 average must never appear


def test_output_contains_no_composite_column_or_value(tmp_path, monkeypatch):
    monkeypatch.setattr(aggregate, "repo_root", lambda: str(tmp_path))
    runs_dir = os.path.join(tmp_path, "eval", "results", "runs")
    os.makedirs(runs_dir)
    _write_policy(str(tmp_path))
    _write_record(runs_dir, make_record())

    assert pv.main() == 0
    content = open(os.path.join(tmp_path, "eval", "profile.md")).read()

    # The whole point of this file: no composite COLUMN OR VALUE anywhere.
    # The header legitimately uses the word "composite" in prose to explain
    # that it has been removed (required by the task spec) -- that is not
    # what this test guards against, so it checks structure, not the word.
    assert "composite_score" not in content  # raw field name must never leak through
    header_rows = [line for line in content.splitlines() if line.startswith("| ")]
    for line in header_rows:
        cells = [c.strip() for c in line.strip("|").split("|")]
        assert not any(cell.lower() == "composite" for cell in cells)


def test_missing_structure_json_degrades_gracefully(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(aggregate, "repo_root", lambda: str(tmp_path))
    runs_dir = os.path.join(tmp_path, "eval", "results", "runs")
    os.makedirs(runs_dir)
    _write_policy(str(tmp_path))
    _write_record(runs_dir, make_record())

    assert pv.main() == 0
    captured = capsys.readouterr()
    assert "structure.json not found" in captured.err  # loud warning, not a silent blank
    content = open(os.path.join(tmp_path, "eval", "profile.md")).read()
    assert "not available" in content  # header names the reason, per EVAL-CONSOLIDATION-TRIAL.md


# ---------------------------------------------------------------------------
# Structural coverage withholding. The structural score is scoped to
# deliverables a model authored from scratch (eval/profile.yaml's
# structure.scope), so only some tasks contribute one, and the per-task
# substrate baselines differ. A model missing an eligible task therefore
# scores higher for no better reason than that it ran fewer tasks -- measured,
# not hypothesised: before the scope fix, opencode-go/minimax-m3 held the
# cohort's HIGHEST structural score purely because it never ran Tasks 003/005.
# ---------------------------------------------------------------------------

def _stats_for(task_id, struct_score):
    """One group's stats for `task_id`, with `struct_score` (or None) as the
    structural score of its single trial."""
    run_id = f"{task_id}-r0"
    trial = make_record(run_id=run_id, task_id=task_id,
                        category_scores={"correctness": 0.9, "test_adequacy": 0.5,
                                          "scope_discipline": 1.0, "hygiene": 1.0})
    lookup = {run_id: {"task_id": task_id, "status": "ok",
                       "structural_score": struct_score}}
    return pv.group_stats_profile([trial], lookup, False, 0.70)


def test_structure_eligible_tasks_reads_the_sidecar_not_a_config():
    lookup = {
        "r1": {"task_id": "001-x", "structural_score": 80.0},
        "r2": {"task_id": "002-y", "structural_score": 60.0},
        "r3": {"task_id": "005-z", "structural_score": None},   # scoped out
    }
    assert pv.structure_eligible_tasks(lookup, {"r1", "r2", "r3"}) == {"001-x", "002-y"}


def test_structure_eligible_tasks_ignores_entries_outside_current_run_ids():
    """An archived or superseded run's sidecar entry must not mark a task
    eligible on its own -- otherwise archiving a run record can leave a stale
    task in the eligible set and incorrectly withhold an otherwise-complete
    model's structural row for a task no CURRENT record even belongs to."""
    lookup = {
        "r1": {"task_id": "001-x", "structural_score": 80.0},
        "stale-r9": {"task_id": "999-archived", "structural_score": 55.0},
    }
    assert pv.structure_eligible_tasks(lookup, {"r1"}) == {"001-x"}


def test_structure_mean_withheld_when_an_eligible_task_is_uncovered():
    """A model that ran only one of the two structure-eligible tasks has no
    comparable structural mean -- same rule aggregate.full_pass_duration_and_
    tokens already applies to incomplete task coverage."""
    row = pv.build_model_row("claude", "partial", "high", [_stats_for("001-x", 95.0)],
                              n_tasks_total=2, eligible_tasks={"001-x", "002-y"})
    assert row["structure_mean"] is None
    assert row["structure_withheld"] is True
    assert pv.fmt_structure(row["structure_mean"]) == "--"


def test_structure_mean_reported_when_every_eligible_task_is_covered():
    row = pv.build_model_row(
        "claude", "full", "high",
        [_stats_for("001-x", 90.0), _stats_for("002-y", 70.0)],
        n_tasks_total=2, eligible_tasks={"001-x", "002-y"})
    assert row["structure_withheld"] is False
    assert row["structure_mean"] == pytest.approx(80.0, abs=1e-6)


def test_load_gate_threshold_reads_the_real_policy():
    root = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True, check=True).stdout.strip()
    assert pv.load_gate_threshold(root) == pytest.approx(0.70)


@pytest.mark.parametrize("gate_block", [
    "gate: {}\n",                                    # no correctness entry
    "gate:\n  correctness: {}\n",                    # no threshold
    "gate:\n  correctness:\n    threshold: high\n",  # not a number
    "gate:\n  correctness:\n    threshold: .nan\n",  # non-finite: silently fails every gate
    "gate:\n  correctness:\n    threshold: .inf\n",  # non-finite
])
def test_load_gate_threshold_fails_loud_rather_than_defaulting(tmp_path, gate_block):
    """A silently-defaulted threshold would render the whole Gate column under
    a policy nobody chose. eval/profile.yaml is tracked and committed next to
    this script, so an unreadable one is a broken checkout."""
    (tmp_path / "eval").mkdir()
    (tmp_path / "eval" / "profile.yaml").write_text(
        gate_block
        + "structure:\n"
          "  scope: new_files_only\n"
          "  decomposition: {metric: function_count, zero_at: 3, one_at: 18}\n"
          "  length: {metric: median_function_loc, zero_at: 100, one_at: 15}\n"
          "  complexity: {metric: mean_cyclomatic, zero_at: 15, one_at: 2}\n"
    )
    with pytest.raises(ValueError, match="threshold"):
        pv.load_gate_threshold(str(tmp_path))


# ---------------------------------------------------------------------------
# Mode 1 screen vs. full-bank summary: unlike task coverage must never enter
# one ranked column (docs/EVAL-CONSOLIDATION-CODE-REVIEW.md's first P1
# finding). A model with 2 tasks and a model with 5 must never be macro-
# averaged and sorted together as if they answered the same question.
# ---------------------------------------------------------------------------

def test_mode1_screen_ranks_every_model_and_full_bank_excludes_partial_coverage(
        tmp_path, monkeypatch):
    monkeypatch.setattr(aggregate, "repo_root", lambda: str(tmp_path))
    runs_dir = os.path.join(tmp_path, "eval", "results", "runs")
    os.makedirs(runs_dir)
    _write_policy(str(tmp_path))

    def _prov(sha):
        return {"rubric_version": 2, "rubric_sha256": sha, "task_contract_sha256": f"contract-{sha}",
                "evaluator_content_sha256": f"ev-{sha}", "judge": {"prompt_sha256": f"judge-{sha}"},
                "baseline_commit": f"base-{sha}", "grader_git_rev": "rev1", "grader_git_dirty": False}

    # full_model: runs both tasks in this synthetic bank (n_tasks_total == 2).
    _write_record(runs_dir, make_record(
        run_id="20260101T000000Z-001-merger-rate-feature-full_model-1-aaa111",
        task_id="001-merger-rate-feature", model="full_model",
        category_scores={"correctness": 0.9, "test_adequacy": 0.3,
                          "scope_discipline": 1.0, "hygiene": 1.0},
        provenance=_prov("shared")))
    _write_record(runs_dir, make_record(
        run_id="20260101T000000Z-002-pair-binning-convention-full_model-1-aaa222",
        task_id="002-pair-binning-convention", model="full_model",
        category_scores={"correctness": 0.9, "test_adequacy": 0.9,
                          "scope_discipline": 1.0, "hygiene": 1.0},
        provenance=_prov("shared")))
    # partial_model: only Task 001 -- a strong Task-001 score that would rank
    # ABOVE full_model in the old macro-averaged single column, which is
    # exactly the invalid comparison this fix removes from the headline.
    _write_record(runs_dir, make_record(
        run_id="20260101T000000Z-001-merger-rate-feature-partial_model-1-bbb111",
        task_id="001-merger-rate-feature", model="partial_model",
        category_scores={"correctness": 0.9, "test_adequacy": 0.95,
                          "scope_discipline": 1.0, "hygiene": 1.0},
        provenance=_prov("shared")))

    assert pv.main() == 0
    content = open(os.path.join(tmp_path, "eval", "profile.md")).read()

    mode1_section = content.split("## Mode 1 screen:")[1].split("## Full-bank summary")[0]
    full_bank_section = content.split("## Full-bank summary")[1].split("## Task:")[0]

    # Both models appear in the Mode 1 screen -- comparable evidence (both
    # ran Task 001) -- with partial_model ranked above full_model on its
    # higher Task 001 mutation kill rate.
    assert "`full_model`" in mode1_section
    assert "`partial_model`" in mode1_section
    assert mode1_section.index("`partial_model`") < mode1_section.index("`full_model`")

    # The full-bank summary excludes partial_model (only 1 of 2 tasks) and
    # says so by name; it must never macro-average partial_model's single-task
    # mean alongside full_model's two-task mean in the same ranked column.
    assert "`full_model`" in full_bank_section
    assert "`partial_model` (1/2 tasks)" in full_bank_section
    full_bank_table = full_bank_section.split("Excluded for incomplete")[1]
    table_rows = [line for line in full_bank_table.splitlines() if line.startswith("| `")]
    assert all("partial_model" not in row for row in table_rows)
