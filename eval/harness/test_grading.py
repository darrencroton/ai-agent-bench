"""Regression tests for rubric v2 scoring: grade_trial.py's arithmetic,
correctness-by-obligation, scope discipline, and judge handling, plus
aggregate.py's pure grouping helpers.

Run from eval/harness/:
    cd eval/harness && ../../venv/bin/python -m pytest test_grading.py -v

Deliberately does not spin up git worktrees, venvs, subprocesses, or a real
judge -- grade_trial.run() is patched wherever a function shells out to git,
and every arithmetic/validation test calls the real function against either
the real eval/rubric.yaml (so a rubric/code disagreement is caught) or a
small synthetic dict (only where the real rubric would obscure the point,
e.g. validate_profile's failure cases).
"""
import json
import os
from unittest.mock import patch

import pytest
import yaml

import aggregate
import grade_trial

ROOT = grade_trial.repo_root()
JUDGE_PROMPT_PATH = os.path.join(ROOT, "eval", "harness", "judge_prompt.md")


def load_rubric():
    with open(os.path.join(ROOT, "eval", "rubric.yaml")) as f:
        return yaml.safe_load(f)


def _stub_name_only_run(changed_files):
    """scope_discipline makes exactly one `git diff --name-only` call."""
    def _run(cmd, cwd=None, env=None, timeout=None):
        return 0, "\n".join(changed_files) + "\n", "", False
    return _run


def _stub_git_diff_calls(diffs):
    """render_judge_diff makes one --name-only call, then one per path."""
    def _run(cmd, cwd=None, env=None, timeout=None):
        if "--name-only" in cmd:
            return 0, "\n".join(diffs) + "\n", "", False
        return 0, diffs[cmd[-1]], "", False
    return _run


# ---- Scoring arithmetic and profiles ----

def test_default_profile_scoring_matches_hand_computed_arithmetic():
    rubric = load_rubric()
    weights = rubric["profiles"]["default"]["weights"]
    automated_ids = [c["id"] for c in rubric["categories"] if c["kind"] == "automated"]
    judged_ids = [c["id"] for c in rubric["categories"] if c["kind"] == "judged"]
    scores = {"correctness": 0.9, "test_adequacy": 0.8, "scope_discipline": 1.0,
              "hygiene": 0.9, "readability": 0.75, "maintainability": 0.5}

    det, det_ws = grade_trial.weighted_score(automated_ids, weights, scores)
    comp, comp_ws = grade_trial.weighted_score(automated_ids + judged_ids, weights, scores)

    assert det_ws == 85       # 40+25+10+10 -- judged weight excluded
    assert det == 88.2
    assert comp_ws == 100
    assert comp == 84.5
    assert det != comp        # deterministic genuinely excludes judged weight


def test_test_authoring_profile_dominance_not_generic_renormalization():
    """The single most important test in the file: test_authoring's gated
    correctness carries no weight, so its explicit weights make test_adequacy
    dominant. A naive renormalization of default's non-gated weights over
    the remaining 60 points would score the same submission differently --
    proving the profile's weights are an explicit design choice, not a
    generic fallback."""
    rubric = load_rubric()
    weights = rubric["profiles"]["test_authoring"]["weights"]
    automated_ids = [c["id"] for c in rubric["categories"] if c["kind"] == "automated"]
    scores = {"correctness": 1.0, "test_adequacy": 0.6, "scope_discipline": 1.0, "hygiene": 1.0}

    det, ws = grade_trial.weighted_score(automated_ids, weights, scores)
    assert ws == 85          # correctness absent from weights (gated) -- 65+10+10
    assert det == 69.4

    # Counterfactual: naively renormalize default's automated weights (minus
    # gated correctness) instead of using test_authoring's own explicit ones.
    naive_weights = {c: rubric["profiles"]["default"]["weights"][c]
                      for c in ("test_adequacy", "scope_discipline", "hygiene")}
    naive_det, naive_ws = grade_trial.weighted_score(automated_ids, naive_weights, scores)
    assert naive_ws == 45
    assert naive_det == 77.8
    assert naive_det != det


def test_weighted_score_excludes_none_scored_category():
    weights = {"correctness": 40, "test_adequacy": 25}
    scores = {"correctness": 0.9, "test_adequacy": None}
    score, ws = grade_trial.weighted_score(["correctness", "test_adequacy"], weights, scores)
    assert ws == 40
    assert score == 90.0


def test_validate_profile_rejects_unknown_or_missing_name():
    rubric = {"categories": [{"id": "a", "kind": "automated"}],
              "profiles": {"good": {"weights": {"a": 100}}}}
    with pytest.raises(ValueError):
        grade_trial.validate_profile(rubric, "nonexistent")
    with pytest.raises(ValueError):
        grade_trial.validate_profile(rubric, None)


def test_validate_profile_rejects_unknown_category_id():
    rubric = {"categories": [{"id": "a", "kind": "automated"}, {"id": "b", "kind": "automated"}],
              "profiles": {"bad": {"weights": {"a": 50, "c": 50}}}}
    with pytest.raises(ValueError):
        grade_trial.validate_profile(rubric, "bad")


def test_validate_profile_rejects_category_in_both_weights_and_gates():
    rubric = {"categories": [{"id": "a", "kind": "automated"}, {"id": "b", "kind": "automated"}],
              "profiles": {"bad": {"weights": {"a": 100}, "gates": {"a": 1.0}}}}
    with pytest.raises(ValueError):
        grade_trial.validate_profile(rubric, "bad")


def test_validate_profile_rejects_non_gated_category_missing_from_weights():
    rubric = {"categories": [{"id": "a", "kind": "automated"}, {"id": "b", "kind": "automated"}],
              "profiles": {"bad": {"weights": {"a": 100}}}}  # b is neither weighted nor gated
    with pytest.raises(ValueError):
        grade_trial.validate_profile(rubric, "bad")


def test_evaluate_gates_no_gates_is_not_applicable():
    status, failed = grade_trial.evaluate_gates({}, {"correctness": 0.9})
    assert status == "not_applicable"
    assert failed == []


def test_evaluate_gates_below_threshold_fails_with_offending_entry():
    status, failed = grade_trial.evaluate_gates({"correctness": 1.0}, {"correctness": 0.87})
    assert status == "failed"
    assert failed == [{"category": "correctness", "score": 0.87, "threshold": 1.0}]


def test_evaluate_gates_none_score_fails_never_silently_passes():
    status, failed = grade_trial.evaluate_gates({"correctness": 1.0}, {"correctness": None})
    assert status == "failed"
    assert failed == [{"category": "correctness", "score": None, "threshold": 1.0}]


# ---- Correctness by obligation ----

def test_score_obligations_equal_weighting_independent_of_group_size():
    obligations = [
        {"id": "small", "tests": ["t_small"]},
        {"id": "big", "tests": [f"t_big_{i}" for i in range(200)]},
    ]
    all_fail = {"t_small": "FAILED", **{f"t_big_{i}": "FAILED" for i in range(200)}}
    baseline, _ = grade_trial.score_obligations(all_fail, obligations, "equal")
    assert baseline == 0.0

    # Flipping the ONE node in the small group moves correctness by exactly
    # 1/n_groups, same as flipping ALL 200 nodes in the big group -- group
    # count, not node count, carries the weight.
    small_passes = dict(all_fail, t_small="PASSED")
    small_score, _ = grade_trial.score_obligations(small_passes, obligations, "equal")

    big_passes = dict(all_fail, **{f"t_big_{i}": "PASSED" for i in range(200)})
    big_score, _ = grade_trial.score_obligations(big_passes, obligations, "equal")

    assert small_score == big_score == 0.5


def test_score_obligations_uncollected_group_scores_zero_not_dropped():
    obligations = [{"id": "present", "tests": ["t1"]}, {"id": "vanished", "tests": ["t2"]}]
    results = {"t1": "PASSED"}  # t2 never collected at all (e.g. import broke)
    correctness, detail = grade_trial.score_obligations(results, obligations, "equal")
    assert correctness == 0.5  # (1.0 + 0.0) / 2 -- vanished group stays in the denominator
    vanished = next(d for d in detail if d["id"] == "vanished")
    assert vanished == {"id": "vanished", "passed": 0, "collected": 0, "fraction": 0.0,
                         "uncollected": True, "failed_nodes": []}


def test_score_obligations_bracket_boundary_and_prefix_safety():
    obligations = [
        {"id": "a", "tests": ["tests/test_hA.py::test_A01"]},
        {"id": "b", "tests": ["tests/test_hA.py::test_A01_extra"]},
    ]
    results = {
        "tests/test_hA.py::test_A01[case0]": "PASSED",  # a parametrize case of A01
        "tests/test_hA.py::test_A01_extra": "PASSED",   # a distinct test, not A01's prefix victim
    }
    correctness, detail = grade_trial.score_obligations(results, obligations, "equal")
    by_id = {d["id"]: d for d in detail}
    assert by_id["a"]["collected"] == 1
    assert by_id["b"]["collected"] == 1
    assert correctness == 1.0


def test_score_obligations_unmapped_node_raises():
    obligations = [{"id": "a", "tests": ["t1"]}]
    results = {"t1": "PASSED", "t_stray": "PASSED"}
    with pytest.raises(ValueError):
        grade_trial.score_obligations(results, obligations, "equal")


def test_score_obligations_multiply_mapped_node_raises():
    obligations = [{"id": "a", "tests": ["t1"]}, {"id": "b", "tests": ["t1"]}]
    results = {"t1": "PASSED"}
    with pytest.raises(ValueError):
        grade_trial.score_obligations(results, obligations, "equal")


def test_score_obligations_rejects_non_equal_weighting():
    with pytest.raises(ValueError):
        grade_trial.score_obligations({}, [], "weighted_by_difficulty")


# ---- Scope ----

def test_scope_discipline_penalty_is_diff_size_independent():
    rubric = load_rubric()
    meta_small = {"authorized_surface": ["src/a.py"], "frozen_unchanged": []}
    with patch.object(grade_trial, "run", new=_stub_name_only_run(["src/a.py", "unauthorized/one.py"])):
        frac_small, _ = grade_trial.scope_discipline("wt", "HEAD", meta_small, rubric)

    authorized_many = [f"src/f{i}.py" for i in range(19)]
    meta_big = {"authorized_surface": authorized_many, "frozen_unchanged": []}
    with patch.object(grade_trial, "run", new=_stub_name_only_run(authorized_many + ["unauthorized/one.py"])):
        frac_big, _ = grade_trial.scope_discipline("wt", "HEAD", meta_big, rubric)

    assert frac_small == frac_big == 0.5


def test_scope_discipline_two_unauthorized_files_floor_at_zero():
    rubric = load_rubric()
    meta = {"authorized_surface": ["src/a.py"], "frozen_unchanged": []}
    changed = ["src/a.py", "unauthorized/one.py", "unauthorized/two.py"]
    with patch.object(grade_trial, "run", new=_stub_name_only_run(changed)):
        frac, detail = grade_trial.scope_discipline("wt", "HEAD", meta, rubric)
    assert frac == 0.0
    assert len(detail["out_of_scope"]) == 2


def test_scope_discipline_integrity_class_vs_frozen_source_unauthorized():
    rubric = load_rubric()
    meta = {
        "authorized_surface": ["src/allowed.py"],
        "frozen_unchanged": ["tests/frozen_test.py", "src/frozen_source.py"],
    }
    changed = [
        "src/allowed.py",
        "eval/harness/grade_trial.py",   # grader-owned path -> integrity via eval/**
        "conftest.py",                    # integrity via exact pattern
        "tests/frozen_test.py",           # frozen test -> integrity (integrity_includes_frozen_tests)
        "src/frozen_source.py",           # frozen SOURCE, outside authorized -> unauthorized
    ]
    with patch.object(grade_trial, "run", new=_stub_name_only_run(changed)):
        frac, detail = grade_trial.scope_discipline("wt", "HEAD", meta, rubric)

    by_path = {v["path"]: v["class"] for v in detail["violations"]}
    assert by_path["eval/harness/grade_trial.py"] == "integrity"
    assert by_path["conftest.py"] == "integrity"
    assert by_path["tests/frozen_test.py"] == "integrity"
    assert by_path["src/frozen_source.py"] == "unauthorized"
    assert frac == 0.0  # any integrity violation zeroes the whole category


def test_scope_discipline_authorized_file_not_flagged_despite_integrity_glob():
    rubric = load_rubric()
    meta = {"authorized_surface": ["conftest.py"], "frozen_unchanged": []}
    with patch.object(grade_trial, "run", new=_stub_name_only_run(["conftest.py"])):
        frac, detail = grade_trial.scope_discipline("wt", "HEAD", meta, rubric)
    assert detail["violations"] == []
    assert frac == 1.0


# ---- Judge ----

def test_validate_judge_score_accepts_and_rejects():
    valid = load_rubric()["judge"]["valid_scores"]
    assert grade_trial._validate_judge_score(1, valid) == 1
    assert grade_trial._validate_judge_score(5.0, valid) == 5
    assert grade_trial._validate_judge_score(0, valid) is None
    assert grade_trial._validate_judge_score(6, valid) is None
    assert grade_trial._validate_judge_score(2.5, valid) is None
    assert grade_trial._validate_judge_score("3", valid) is None
    assert grade_trial._validate_judge_score(None, valid) is None
    # bool is an int subclass in Python -- must be excluded explicitly.
    assert grade_trial._validate_judge_score(True, valid) is None
    assert grade_trial._validate_judge_score(False, valid) is None


def test_map_judge_score_shifted_and_linear():
    valid = load_rubric()["judge"]["valid_scores"]
    assert grade_trial._map_judge_score(1, valid, "shifted") == 0.0
    assert grade_trial._map_judge_score(5, valid, "shifted") == 1.0
    assert grade_trial._map_judge_score(5, valid, "linear") == 1.0
    assert grade_trial._map_judge_score(1, valid, "linear") == 0.2


def test_render_judge_diff_under_budget_returns_whole_files_sorted():
    diffs = {"b.py": "BBB", "a.py": "AAA"}
    with patch.object(grade_trial, "run", new=_stub_git_diff_calls(diffs)):
        out = grade_trial.render_judge_diff("wt", "HEAD", 1000)
    assert out == "AAA" + "BBB"  # sorted path order: a.py before b.py


def test_render_judge_diff_over_budget_keeps_every_file_and_is_deterministic():
    diffs = {"a.py": "A" * 100, "b.py": "B" * 100, "c.py": "C" * 100}
    with patch.object(grade_trial, "run", new=_stub_git_diff_calls(diffs)):
        out1 = grade_trial.render_judge_diff("wt", "HEAD", 150)
        out2 = grade_trial.render_judge_diff("wt", "HEAD", 150)
    assert out1 == out2  # same diff always produces the same prompt
    for path in diffs:
        assert path in out1
    assert out1.count("truncated") == 3  # every file marked, none silently dropped


def test_judge_prompt_empty_context_no_stray_blank_line():
    """Guards a real past bug: judge_context empty renders context_block=""
    (contract §8), so the placeholder must sit directly against "DIFF:" with
    no newline of its own -- otherwise an empty-context prompt would gain a
    blank line a non-empty-context prompt would not have."""
    with open(JUDGE_PROMPT_PATH) as f:
        template = f.read()
    assert "{{JUDGE_CONTEXT}}DIFF:" in template


def test_judge_prompt_does_not_ask_to_unify_across_files():
    """Task 005 deliberately sets maintainability against scope: a judge told
    to unify/deduplicate code across the whole repo would disarm that
    tension. Note the prompt DOES legitimately say the opposite -- that code
    living elsewhere in the repo is never a reason to lower a score -- so
    only directive (not disclaiming) phrasing is forbidden here."""
    with open(JUDGE_PROMPT_PATH) as f:
        text = f.read().lower()
    forbidden = ["unify", "deduplicate", "de-duplicate", "consolidate",
                 "across files", "across the repo", "across the codebase",
                 "wider repository", "rest of the repo", "other files in the repo"]
    hits = [w for w in forbidden if w in text]
    assert not hits, f"judge_prompt.md contains cross-file dedup language: {hits}"


def test_same_model_detection_ignores_harness_specific_spelling():
    """Every harness spells a model differently, so raw equality let an
    opencode trial of the judge's own model escape the withholding policy."""
    assert grade_trial._same_model("claude-opus-5", "anthropic/claude-opus-5")
    assert grade_trial._same_model("claude-opus-5", "claude-opus-5")
    assert not grade_trial._same_model("claude-opus-5", "claude-sonnet-5")
    assert not grade_trial._same_model("claude-opus-5", None)


def test_validate_categories_rejects_a_category_the_grader_cannot_compute():
    """Renaming a category in YAML alone would leave the grader writing an
    orphan key and silently drop that category's weight from every score."""
    rubric = {"categories": [{"id": "spec_conformance", "kind": "automated"}]}
    with pytest.raises(ValueError):
        grade_trial.validate_categories(rubric, {})
    real = load_rubric()
    grade_trial.validate_categories(real, {"correctness": 1.0})   # the shipped shape
    with pytest.raises(ValueError):
        # Gates run straight after correctness, before hygiene exists.
        grade_trial.validate_categories(real, {"hygiene": 1.0})


def test_validate_judge_config_rejects_unimplemented_same_model_policy():
    rubric = {"judge": {"model": "m", "score_map": "shifted",
                        "same_model_policy": "ignore_it"}}
    with pytest.raises(ValueError):
        grade_trial.validate_judge_config(rubric)


# ---- Provenance ----

def _write_task_dir(tmp_path, hidden_test_body, mutation_body, mutation_list_body="m1\n"):
    task_dir = tmp_path / "task"
    (task_dir / "hidden_tests").mkdir(parents=True)
    (task_dir / "mutations").mkdir()
    (task_dir / "spec.md").write_text("spec")
    (task_dir / "meta.yaml").write_text("meta: 1")
    (task_dir / "hidden_tests" / "test_x.py").write_text(hidden_test_body)
    (task_dir / "mutations" / "mutation_list.txt").write_text(mutation_list_body)
    (task_dir / "mutations" / "sitecustomize.py").write_text(mutation_body)
    meta = {"hidden_tests": ["hidden_tests/test_x.py"], "mutations_file": "mutations/mutation_list.txt"}
    return str(task_dir), meta


def _build_provenance(tmp_path, hidden_test_body, mutation_body, mutation_list_body="m1\n"):
    root = grade_trial.repo_root()
    rubric = load_rubric()
    task_dir, meta = _write_task_dir(tmp_path, hidden_test_body, mutation_body, mutation_list_body)
    return grade_trial.build_provenance(root, rubric, b"rb", {}, meta, task_dir,
                                        "1.0.0", True, "disabled", False)


def test_evaluator_content_sha256_changes_with_hidden_test_content(tmp_path):
    a = _build_provenance(tmp_path / "a", "def test_a(): assert 1 == 1\n", "MUTATIONS = {}\n")
    b = _build_provenance(tmp_path / "b", "def test_a(): assert 1 == 2\n", "MUTATIONS = {}\n")
    assert a["evaluator_content_sha256"] != b["evaluator_content_sha256"]
    # task_contract_sha256 is unaffected -- spec.md/meta.yaml didn't change,
    # confirming this is genuinely new signal, not a duplicate of it.
    assert a["task_contract_sha256"] == b["task_contract_sha256"]


def test_evaluator_content_sha256_changes_with_mutation_implementation_content(tmp_path):
    """Exercises the mutations/*.py glob arm (sitecustomize.py's mutation
    implementations)."""
    a = _build_provenance(tmp_path / "a", "def test_a(): assert 1 == 1\n", "MUTATIONS = {}\n")
    b = _build_provenance(tmp_path / "b", "def test_a(): assert 1 == 1\n", "MUTATIONS = {'x': 1}\n")
    assert a["evaluator_content_sha256"] != b["evaluator_content_sha256"]


def test_evaluator_content_sha256_changes_with_mutation_list_content(tmp_path):
    """Exercises meta["mutations_file"] specifically, separate from the glob
    arm above -- mutation_list.txt is the scored-mutation list load_mutations()
    reads, so a regenerated list changes what a trial is actually graded
    against even with sitecustomize.py held constant."""
    a = _build_provenance(tmp_path / "a", "def test_a(): pass\n", "MUTATIONS = {}\n", "m1\n")
    b = _build_provenance(tmp_path / "b", "def test_a(): pass\n", "MUTATIONS = {}\n", "m1\nm2\n")
    assert a["evaluator_content_sha256"] != b["evaluator_content_sha256"]


def test_evaluator_content_sha256_stable_for_identical_content(tmp_path):
    a = _build_provenance(tmp_path / "a", "def test_a(): pass\n", "MUTATIONS = {}\n")
    b = _build_provenance(tmp_path / "b", "def test_a(): pass\n", "MUTATIONS = {}\n")
    assert a["evaluator_content_sha256"] == b["evaluator_content_sha256"]


# ---- Aggregation ----

def _prov(**over):
    p = {"rubric_version": 2, "rubric_sha256": "r1", "task_contract_sha256": "c1",
         "evaluator_content_sha256": "e1",
         "baseline_commit": "b1", "judge": {"prompt_sha256": "p1"}}
    p.update(over)
    return {"provenance": p}


def test_cohort_key_differs_on_every_score_affecting_input():
    base = _prov()
    for field, value in [("rubric_sha256", "r2"), ("task_contract_sha256", "c2"),
                         ("evaluator_content_sha256", "e2"), ("baseline_commit", "b2")]:
        assert aggregate.cohort_key(base) != aggregate.cohort_key(_prov(**{field: value})), field
    # The judged instrument itself: a changed judge prompt is a changed rubric.
    assert aggregate.cohort_key(base) != aggregate.cohort_key(_prov(judge={"prompt_sha256": "p2"}))
    assert aggregate.cohort_key(base) == aggregate.cohort_key(_prov())


def test_grader_provenance_warnings_flag_what_the_cohort_key_does_not():
    """Grader revision is deliberately outside the cohort key (it would split
    a batch on a docs-only commit), so it has to surface as a warning."""
    same = [{"provenance": {"grader_git_rev": "a", "grader_git_dirty": False}}] * 2
    assert aggregate.grader_provenance_warnings(same) == []
    mixed = [{"provenance": {"grader_git_rev": "a", "grader_git_dirty": False}},
             {"provenance": {"grader_git_rev": "b", "grader_git_dirty": True}}]
    notes = aggregate.grader_provenance_warnings(mixed)
    assert len(notes) == 2   # differing revisions, and one dirty tree


def test_group_stats_withholds_judged_and_composite_for_same_model_group():
    trials = [{"run_id": "r1", "deterministic_score": 80.0, "composite_score": 75.0,
               "judged_scores": {"readability": 0.8, "maintainability": 0.6},
               "judge_same_model": True, "complete_submission": True,
               "category_scores": {"correctness": 0.9}, "gate_status": "passed",
               "integrity_violation": False}]
    stats = aggregate.group_stats(trials, ["correctness"], ["readability", "maintainability"])
    assert stats["det_mean"] == 80.0        # deterministic evidence is unaffected
    assert stats["comp_mean"] is None
    assert stats["judged"] == {"readability": None, "maintainability": None}
    assert stats["judge_same_model"] is True


def test_group_stats_retains_gate_failed_and_incomplete_trials():
    trials = [
        {"run_id": "r1", "deterministic_score": 0.0, "composite_score": 0.0, "judged_scores": {},
         "judge_same_model": False, "complete_submission": False, "category_scores": {},
         "gate_status": "failed", "integrity_violation": False},
        {"run_id": "r2", "deterministic_score": 80.0, "composite_score": 75.0,
         "judged_scores": {"readability": 0.8, "maintainability": 0.6}, "judge_same_model": False,
         "complete_submission": True, "category_scores": {"correctness": 0.9},
         "gate_status": "passed", "integrity_violation": False},
    ]
    stats = aggregate.group_stats(trials, ["correctness"], ["readability", "maintainability"])
    assert stats["n"] == 2
    assert stats["gate_failed_n"] == 1
    assert stats["incomplete_n"] == 1
    assert stats["det_mean"] == 40.0  # mean of 0.0 and 80.0 -- both counted, neither dropped


def test_load_records_skips_record_with_no_provenance(tmp_path):
    runs_dir = tmp_path / "eval" / "results" / "runs"
    runs_dir.mkdir(parents=True)
    (runs_dir / "a.json").write_text(json.dumps({"provenance": {"rubric_version": 2}, "harness": "h"}))
    (runs_dir / "b.json").write_text(json.dumps({"total_score": 50}))  # pre-v2, no provenance
    records, skipped, skipped_reference = aggregate.load_records(str(tmp_path))
    assert len(records) == 1
    assert skipped == 1
    assert skipped_reference == 0


def test_load_records_skips_reference_check_records(tmp_path):
    """harness == "none" is reference_check.py's evaluator-validation marker
    (see its build_manifest()) -- such a record must never reach the
    leaderboard as a fake model row even if left behind in eval/results/runs/
    by mistake."""
    runs_dir = tmp_path / "eval" / "results" / "runs"
    runs_dir.mkdir(parents=True)
    (runs_dir / "a.json").write_text(json.dumps({"provenance": {"rubric_version": 2}, "harness": "h"}))
    (runs_dir / "b.json").write_text(json.dumps(
        {"provenance": {"rubric_version": 2}, "harness": "none", "model": "reference-solution"}))
    records, skipped, skipped_reference = aggregate.load_records(str(tmp_path))
    assert len(records) == 1
    assert skipped == 0
    assert skipped_reference == 1


def _minimal_record(run_id, rubric_sha256):
    return {
        "run_id": run_id, "task_id": "001-merger-rate-feature", "model": "m", "harness": "h",
        "duration_seconds": 1.0, "venv_setup_seconds": None, "timed_out": False,
        "committed": False, "changed_files": [], "rubric_profile": "default",
        "gate_status": "not_applicable", "complete_submission": True,
        "scored_weight_fraction": 1.0, "deterministic_score": 50.0, "composite_score": 50.0,
        "judged_scores": {}, "category_scores": {}, "category_detail": {},
        "provenance": {"rubric_sha256": rubric_sha256, "judge": {}},
    }


def test_write_and_report_refuses_to_overwrite_a_record_graded_under_a_different_rubric(tmp_path):
    root = str(tmp_path)
    rubric = load_rubric()
    manifest = {"run_id": "run-1"}
    ok_path = os.path.join(root, "eval", "results", "runs", "run-1.json")
    os.makedirs(os.path.dirname(ok_path))
    with open(ok_path, "w") as f:
        json.dump(_minimal_record("run-1", "original-hash"), f)

    rc = grade_trial._write_and_report(root, manifest, rubric,
                                        _minimal_record("run-1", "different-hash"))

    assert rc == 1
    with open(ok_path) as f:
        assert json.load(f)["provenance"]["rubric_sha256"] == "original-hash"


def test_write_and_report_allows_overwrite_with_the_same_rubric_hash(tmp_path):
    root = str(tmp_path)
    rubric = load_rubric()
    manifest = {"run_id": "run-1"}
    ok_path = os.path.join(root, "eval", "results", "runs", "run-1.json")
    os.makedirs(os.path.dirname(ok_path))
    with open(ok_path, "w") as f:
        json.dump(_minimal_record("run-1", "same-hash"), f)

    rc = grade_trial._write_and_report(root, manifest, rubric,
                                        _minimal_record("run-1", "same-hash"))

    assert rc == 0
