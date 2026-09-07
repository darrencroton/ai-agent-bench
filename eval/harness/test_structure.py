"""Focused tests for structure.py's AST metrics, the frozen scoring formula,
and the archived-patch reconstruction the sweep relies on.

Deliberately does NOT run the full 219-record sweep (see AGENTS.md's "Don't
overtest" and docs/EVAL-CONSOLIDATION-TRIAL.md's test scope) -- each test
below targets one thing whose breakage would be silent and expensive: a
metric definition drifting from docs/EVAL-CONSOLIDATION-TRIAL.md's frozen
formula, per-file scores getting averaged instead of pooled (the specific
bug aggregate_metrics exists to prevent), or a policy file silently
defaulting instead of failing loud.

Run from eval/harness/:
    cd eval/harness && ../../venv/bin/python -m pytest test_structure.py -v
"""
import glob
import json
import os
import shutil
import subprocess
import tempfile

import pytest

import structure


# ---------------------------------------------------------------------------
# module_metrics
# ---------------------------------------------------------------------------

# Hand-verified against structure.module_metrics() during development (see
# this test module's own assertions for the arithmetic):
#   top_level_a: 4 lines, complexity 4  (1 base + 1 If + 2 for a 3-operand BoolOp)
#   top_level_b: 2 lines, complexity 3  (1 base + 2 comprehension `if`s)
#   top_level_c: 6 lines, complexity 2  (1 base + 1 If, from the NESTED function)
#   Foo.method: not a top-level function -- must not appear at all.
SAMPLE_MODULE = '''\
def top_level_a(x, y, z):
    if x and y and z:
        return 1
    return 0


def top_level_b(items):
    return [i for i in items if i > 0 if i < 10]


def top_level_c():
    def inner():
        if True:
            return 1
        return 0
    return inner()


class Foo:
    def method(self):
        return 1
'''


def test_module_metrics_matches_the_frozen_ast_definitions():
    mm = structure.module_metrics(SAMPLE_MODULE)
    functions = mm["functions"]

    assert len(functions) == 3  # Foo.method excluded -- not top-level
    assert functions[0] == {"loc": 4, "cyclomatic": 4}  # a: If(+1) + BoolOp/3(+2)
    assert functions[1] == {"loc": 2, "cyclomatic": 3}  # b: 2 comprehension ifs
    assert functions[2] == {"loc": 6, "cyclomatic": 2}  # c: nested function's own If

    summary = structure.summarize_functions(functions)
    assert summary == {"function_count": 3, "median_function_loc": 4, "mean_cyclomatic": 3}


def test_module_metrics_raises_syntax_error_on_bad_source():
    with pytest.raises(SyntaxError):
        structure.module_metrics("def broken(:\n    pass\n")


# ---------------------------------------------------------------------------
# aggregate_metrics -- pools across files, never averages per-file scores
# ---------------------------------------------------------------------------

def test_aggregate_metrics_pools_functions_rather_than_averaging_per_file_scores():
    file_a = [{"loc": 10, "cyclomatic": 2}]
    file_b = [{"loc": 100, "cyclomatic": 20}, {"loc": 100, "cyclomatic": 20}]

    pooled = structure.aggregate_metrics([file_a, file_b])

    # The bug this guards against: averaging file_a's summary (fc=1,
    # median=10, mean=2) with file_b's (fc=2, median=100, mean=20) gives
    # fc=1.5, median=55, mean=11 -- all wrong. Pooling first gives the
    # correct numbers over all 3 functions together.
    assert pooled == {"function_count": 3, "median_function_loc": 100, "mean_cyclomatic": 14.0}


# ---------------------------------------------------------------------------
# structural_score -- clamping at both ends, and the no-functions None case
# ---------------------------------------------------------------------------

_POLICY = {
    "structure": {
        "scope": "new_files_only",
        "decomposition": {"metric": "function_count", "zero_at": 3, "one_at": 18},
        "length": {"metric": "median_function_loc", "zero_at": 100, "one_at": 15},
        "complexity": {"metric": "mean_cyclomatic", "zero_at": 15, "one_at": 2},
    }
}


def test_structural_score_is_none_for_a_module_with_no_functions():
    score, components = structure.structural_score(
        {"function_count": 0, "median_function_loc": None, "mean_cyclomatic": None}, _POLICY)
    assert score is None
    assert components == {}


def test_structural_score_clamps_at_the_high_end():
    # Comfortably past every one_at: more functions, shorter, simpler than
    # the calibration ceiling -- every component must clamp to 1.0, not
    # extrapolate past it.
    metrics = {"function_count": 40, "median_function_loc": 5, "mean_cyclomatic": 1}
    score, components = structure.structural_score(metrics, _POLICY)
    assert components == {"decomposition": 1.0, "length": 1.0, "complexity": 1.0}
    assert score == 100.0


def test_structural_score_clamps_at_the_low_end():
    # Worse than every zero_at (but function_count != 0, so still scored,
    # not None): fewer functions than the floor, longer, more complex than
    # the floor -- every component must clamp to 0.0, not go negative.
    metrics = {"function_count": 1, "median_function_loc": 500, "mean_cyclomatic": 50}
    score, components = structure.structural_score(metrics, _POLICY)
    assert components == {"decomposition": 0.0, "length": 0.0, "complexity": 0.0}
    assert score == 0.0


def test_structural_score_mid_range_matches_hand_computed_ramp():
    # function_count=10 -> (10-3)/(18-3) = 7/15
    # median_function_loc=50 -> (100-50)/(100-15) = 50/85
    # mean_cyclomatic=8 -> (15-8)/(15-2) = 7/13
    metrics = {"function_count": 10, "median_function_loc": 50, "mean_cyclomatic": 8}
    score, components = structure.structural_score(metrics, _POLICY)
    assert components["decomposition"] == pytest.approx(7 / 15)
    assert components["length"] == pytest.approx(50 / 85)
    assert components["complexity"] == pytest.approx(7 / 13)
    assert score == pytest.approx(100 * (7 / 15 + 50 / 85 + 7 / 13) / 3)


# ---------------------------------------------------------------------------
# load_policy -- fails loud on a missing/incomplete structure: block
# ---------------------------------------------------------------------------

def test_load_policy_reads_the_real_profile_yaml():
    root = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True, check=True).stdout.strip()
    policy = structure.load_policy(root)
    for name in ("decomposition", "length", "complexity"):
        cfg = policy["structure"][name]
        assert {"metric", "zero_at", "one_at"} <= cfg.keys()


def test_load_policy_raises_on_missing_structure_block(tmp_path):
    bad = tmp_path / "profile.yaml"
    bad.write_text("version: 1\ngate:\n  correctness:\n    threshold: 0.7\n")
    with pytest.raises(ValueError, match="structure"):
        structure.load_policy(str(tmp_path), path=str(bad))


def test_load_policy_raises_on_incomplete_component(tmp_path):
    bad = tmp_path / "profile.yaml"
    bad.write_text(
        "structure:\n"
        "  scope: new_files_only\n"
        "  decomposition: {metric: function_count, zero_at: 3, one_at: 18}\n"
        "  length: {metric: median_function_loc, zero_at: 100}\n"  # missing one_at
        "  complexity: {metric: mean_cyclomatic, zero_at: 15, one_at: 2}\n"
    )
    with pytest.raises(ValueError, match="length"):
        structure.load_policy(str(tmp_path), path=str(bad))


@pytest.mark.parametrize("scope_line", ["", "  scope: whole_repo\n"])
def test_load_policy_raises_on_missing_or_unknown_scope(tmp_path, scope_line):
    """`scope` decides whether the three metrics describe the submission or
    the frozen substrate it was added to (see eval/profile.yaml). Defaulting
    it silently would compute a different measurement than the operator
    chose, across every record, without saying so."""
    bad = tmp_path / "profile.yaml"
    bad.write_text(
        "structure:\n"
        + scope_line +
        "  decomposition: {metric: function_count, zero_at: 3, one_at: 18}\n"
        "  length: {metric: median_function_loc, zero_at: 100, one_at: 15}\n"
        "  complexity: {metric: mean_cyclomatic, zero_at: 15, one_at: 2}\n"
    )
    with pytest.raises(ValueError, match="scope"):
        structure.load_policy(str(tmp_path), path=str(bad))


def test_policy_sha256_is_stable_and_sensitive_to_the_structure_block():
    sha_a = structure.policy_sha256(_POLICY)
    sha_b = structure.policy_sha256(_POLICY)
    assert sha_a == sha_b
    tweaked = json.loads(json.dumps(_POLICY))
    tweaked["structure"]["decomposition"]["one_at"] = 19
    assert structure.policy_sha256(tweaked) != sha_a


# ---------------------------------------------------------------------------
# End-to-end reconstruction: a real git repo, a real patch, a real
# `git apply` against a plain (non-repo) directory tree.
# ---------------------------------------------------------------------------

def _git(args, cwd):
    subprocess.run(["git"] + args, cwd=cwd, check=True, capture_output=True)


def test_reconstruct_file_returns_the_post_image_and_verifies_the_blob_sha(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(["init", "-q"], repo)
    _git(["config", "user.email", "t@t.com"], repo)
    _git(["config", "user.name", "t"], repo)
    src_dir = repo / "src"
    src_dir.mkdir()
    (src_dir / "foo.py").write_text("def foo():\n    return 1\n")
    _git(["add", "-A"], repo)
    _git(["commit", "-q", "-m", "base"], repo)
    before_head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo,
                                  capture_output=True, text=True, check=True).stdout.strip()

    post_image = "def foo():\n    return 2\n\n\ndef bar():\n    return 3\n"
    (src_dir / "foo.py").write_text(post_image)
    patch_text = subprocess.run(["git", "--no-pager", "diff", "--no-color"], cwd=repo,
                                 capture_output=True, text=True, check=True).stdout
    patch_path = tmp_path / "submission.patch"
    patch_path.write_text(patch_text)

    dest_dir = tmp_path / "dest"
    dest_dir.mkdir()
    recon = structure.reconstruct_file(str(repo), before_head, str(patch_path),
                                       "src/foo.py", str(dest_dir))

    assert recon["existed_at_baseline"] is True
    assert recon["applied"] is True
    assert recon["dest_path"] is not None
    with open(recon["dest_path"]) as f:
        assert f.read() == post_image

    # The reconstruction must be byte-exact: the patch's own declared
    # post-image blob sha (from its `index a..b` header) must match
    # `git hash-object` on the file this function actually wrote.
    patch_index = structure.parse_patch_index(patch_text)
    declared_blob = patch_index["src/foo.py"]["new_blob"]
    actual_blob = subprocess.run(["git", "hash-object", recon["dest_path"]],
                                 capture_output=True, text=True, check=True).stdout.strip()
    n = min(len(actual_blob), len(declared_blob))
    assert actual_blob[:n] == declared_blob[:n]


# ---------------------------------------------------------------------------
# structure.scope == "new_files_only": the metrics must describe what the
# model wrote, not the frozen module it was added to. Measured directly over
# all 219 records before this existed, Task 005 scored an identical 68.9 for
# all 42 of its trials, because src/calc.py's pre-existing structure swamps
# the few lines a submission adds -- see eval/profile.yaml's `structure:`
# block. These two run against the real repo and the real archive, on ONE
# record each, because the behaviour under test is precisely the interaction
# between a task's real deliverable list and a real submission patch.
# ---------------------------------------------------------------------------

def _one_run_id_for_task(root, task_prefix):
    for path in sorted(glob.glob(os.path.join(root, "eval", "results", "runs", "*.json"))):
        with open(path) as f:
            record = json.load(f)
        if record["task_id"].startswith(task_prefix):
            archive = os.path.join(root, "archive", "worktrees", record["run_id"],
                                    "submission.patch")
            if os.path.isfile(archive):
                return record
    return None


def _real_root():
    return subprocess.run(["git", "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True, check=True).stdout.strip()


def test_new_files_only_scores_only_the_module_the_submission_authored():
    """Task 001 declares src/config.py, src/calc.py and src/merger_rate.py as
    non-test deliverables, but only merger_rate.py is new. Scoring all three
    diluted the score with two barely-changed frozen modules; scoring the new
    one alone is also exactly what the rho +0.72 validation measured."""
    root = _real_root()
    record = _one_run_id_for_task(root, "001")
    if record is None:
        pytest.skip("no archived Task 001 submission.patch available (archive/ is local-only)")
    tmp_root = tempfile.mkdtemp(prefix="test-structure-scope-")
    try:
        entry = structure._score_record(
            root, record, os.path.join(root, "archive", "worktrees"), tmp_root,
            structure.load_policy(root))
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)
    assert entry["status"] == "ok"
    scored = [p for p, d in entry["files"].items() if "note" not in d]
    assert scored == ["src/merger_rate.py"]
    excluded = {p for p, d in entry["files"].items() if "existed at baseline" in d.get("note", "")}
    assert excluded == {"src/config.py", "src/calc.py"}
    assert entry["structural_score"] is not None


def test_new_files_only_makes_a_modify_only_task_not_applicable():
    """Task 005's only non-test deliverable is src/calc.py, which already
    exists at the baseline -- so there is nothing the submission authored to
    measure. That must be `not_applicable` with a null score, never a 0: a 0
    reads as "measured, and bad"."""
    root = _real_root()
    record = _one_run_id_for_task(root, "005")
    if record is None:
        pytest.skip("no archived Task 005 submission.patch available (archive/ is local-only)")
    tmp_root = tempfile.mkdtemp(prefix="test-structure-scope-")
    try:
        entry = structure._score_record(
            root, record, os.path.join(root, "archive", "worktrees"), tmp_root,
            structure.load_policy(root))
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)
    assert entry["status"] == "not_applicable"
    assert entry.get("structural_score") is None
    assert "authored from scratch" in entry["note"]


# ---------------------------------------------------------------------------
# Source resolution: a freshly graded trial has a live worktree and NO
# archived patch, because neither run_trial.py nor run_batch.py archives
# anything -- archiving is a separate worktree_lifecycle.py step, and this
# repo deliberately keeps worktrees on disk afterwards so a run can be
# re-graded under a different scoring scheme. Reading the worktree first is
# what makes the structural column correct at every point in a worktree's
# lifecycle: worktree only (fresh), both (archived but kept), patch only
# (pruned -- and prune already refuses without archived evidence).
# ---------------------------------------------------------------------------

def test_find_worktree_prefers_the_manifest_path_then_the_conventional_one(tmp_path):
    root = tmp_path / "repo"
    conventional = root / "eval" / "results" / "tmp" / "worktrees" / "run-1"
    conventional.mkdir(parents=True)
    record = {"run_id": "run-1"}

    # no manifest -> the conventional location
    assert structure.find_worktree(str(root), record, None) == str(conventional)

    # a manifest path that exists wins
    explicit = tmp_path / "elsewhere"
    explicit.mkdir()
    assert structure.find_worktree(
        str(root), record, {"worktree_path": str(explicit)}) == str(explicit)

    # a manifest path that does NOT exist falls back rather than returning a
    # dead path (the case after a worktree is moved or pruned)
    assert structure.find_worktree(
        str(root), record, {"worktree_path": str(tmp_path / "gone")}) == str(conventional)

    # nothing anywhere -> None, so the caller falls through to the patch
    assert structure.find_worktree(str(tmp_path / "empty"), record, None) is None


def test_scores_a_fresh_trial_from_its_live_worktree_with_no_archived_patch(tmp_path):
    """The end-to-end gap this exists to close: grade a trial, sweep
    immediately, get a real structural score -- no archive step in between."""
    root = _real_root()
    record = _one_run_id_for_task(root, "001")
    if record is None:
        pytest.skip("no archived Task 001 record available (archive/ is local-only)")

    # Stand up a synthetic 'live worktree' holding just the scored deliverable.
    wt = tmp_path / "worktrees" / record["run_id"]
    (wt / "src").mkdir(parents=True)
    (wt / "src" / "merger_rate.py").write_text(
        "def a():\n    return 1\n\n\ndef b(x):\n    if x:\n        return 2\n    return 3\n")
    manifest = {"worktree_path": str(wt), "before_head": "frozen-substrate"}

    tmp_root = tempfile.mkdtemp(prefix="test-structure-live-")
    try:
        entry = structure._score_record(
            root, record, str(tmp_path / "no-archive-here"), tmp_root,
            structure.load_policy(root), manifest=manifest)
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)

    assert entry["status"] == "ok"
    assert entry["source"] == "worktree"
    assert entry["structural_score"] is not None
    # Nothing to verify against: the worktree IS the graded artifact.
    assert entry["files"]["src/merger_rate.py"]["blob_verified"] is None
    assert entry["files"]["src/merger_rate.py"]["function_count"] == 2


def test_source_can_be_pinned_so_the_two_paths_can_be_audited(tmp_path):
    """`--source worktree` / `--source patch` exist so the two post-image
    paths can be checked against each other; sweeping the real cohort both
    ways produces identical scores for every record both can reach. Here just
    pin each direction and check the refusal is loud rather than a silent
    fallback."""
    root = _real_root()
    record = _one_run_id_for_task(root, "001")
    if record is None:
        pytest.skip("no archived Task 001 record available (archive/ is local-only)")
    arch = os.path.join(root, "archive", "worktrees")
    pol = structure.load_policy(root)

    # pinned to patch: must use the patch even when a worktree exists, and the
    # patch path is the one that carries blob verification
    tmp_root = tempfile.mkdtemp(prefix="test-structure-src-")
    try:
        via_patch = structure._score_record(root, record, arch, tmp_root, pol,
                                             prefer=structure.SOURCE_PATCH)
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)
    assert via_patch["status"] == "ok"
    assert via_patch["source"] == "patch"
    assert via_patch["files"]["src/merger_rate.py"]["blob_verified"] is True

    # pinned to worktree with no worktree: refuse loudly, never fall back.
    # find_worktree is stubbed rather than pointed at a nonexistent path,
    # because it falls back to the conventional worktree location -- which for
    # some records really exists, so the assertion would otherwise pass or fail
    # on local disk state rather than on the refusal logic under test.
    original = structure.find_worktree
    structure.find_worktree = lambda *a, **k: None
    tmp_root = tempfile.mkdtemp(prefix="test-structure-src-")
    try:
        via_wt = structure._score_record(root, record, arch, tmp_root, pol,
                                          prefer=structure.SOURCE_WORKTREE)
    finally:
        structure.find_worktree = original
        shutil.rmtree(tmp_root, ignore_errors=True)
    assert via_wt["status"] == "missing_submission"
    assert "forbids" in via_wt["note"]


def test_a_worktree_without_the_deliverable_falls_through_to_the_patch(tmp_path):
    """P1 (external review): a leftover or partial worktree directory must not
    shadow a valid archived patch. Before this, such a directory produced
    `not_applicable` with the note "no scored deliverable was authored from
    scratch by this submission" -- false -- and the patch was never read.
    Partial worktree directories demonstrably occur here (see
    archive/2026-09-07-pm-branch-transplant/orphan-worktree-*/)."""
    root = _real_root()
    record = _one_run_id_for_task(root, "001")
    if record is None:
        pytest.skip("no archived Task 001 record available (archive/ is local-only)")
    arch = os.path.join(root, "archive", "worktrees")

    empty_wt = tmp_path / "leftover"      # exists, holds nothing
    empty_wt.mkdir()
    tmp_root = tempfile.mkdtemp(prefix="test-structure-shadow-")
    try:
        entry = structure._score_record(
            root, record, arch, tmp_root, structure.load_policy(root),
            manifest={"worktree_path": str(empty_wt), "before_head": None})
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)

    assert entry["status"] == "ok", entry.get("note")
    assert entry["source"] == "patch"          # demoted, not trusted
    assert entry["structural_score"] is not None
    # and the patch path keeps its verification, which a late demotion lost
    assert entry["files"]["src/merger_rate.py"]["blob_verified"] is True


def test_an_absent_deliverable_is_reported_honestly_not_as_a_scope_exclusion(tmp_path):
    """The two `not_applicable` reasons must stay distinct: "excluded by
    scope" and "the file was not there" are different facts."""
    root = _real_root()
    record = _one_run_id_for_task(root, "001")
    if record is None:
        pytest.skip("no archived Task 001 record available (archive/ is local-only)")

    empty_wt = tmp_path / "leftover"
    empty_wt.mkdir()
    tmp_root = tempfile.mkdtemp(prefix="test-structure-honest-")
    try:
        # no archive to fall back to, so the empty worktree is the only source
        entry = structure._score_record(
            root, record, str(tmp_path / "no-archive"), tmp_root,
            structure.load_policy(root),
            manifest={"worktree_path": str(empty_wt), "before_head": None})
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)

    assert entry["status"] == "not_applicable"
    assert "absent from the worktree source" in entry["note"]
    assert "authored from scratch" not in entry["note"]


def test_status_ok_never_carries_a_null_score(tmp_path):
    """A submission that factors everything into a class parses fine but pools
    to zero module-level functions. That must be `not_applicable`, not `ok`
    with a null score, or _meta.n_scored over-counts and profile.md claims it
    as scored."""
    root = _real_root()
    record = _one_run_id_for_task(root, "001")
    if record is None:
        pytest.skip("no archived Task 001 record available (archive/ is local-only)")

    wt = tmp_path / "classy" / "src"
    wt.mkdir(parents=True)
    (wt / "merger_rate.py").write_text(
        "class Everything:\n    def a(self):\n        return 1\n\n"
        "    def b(self):\n        return 2\n")
    tmp_root = tempfile.mkdtemp(prefix="test-structure-null-")
    try:
        entry = structure._score_record(
            root, record, str(tmp_path / "no-archive"), tmp_root,
            structure.load_policy(root),
            manifest={"worktree_path": str(tmp_path / "classy"), "before_head": None})
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)

    assert entry["status"] == "not_applicable"
    assert entry.get("structural_score") is None
    assert "no module-level function" in entry["note"]


def test_structural_score_returns_none_for_a_null_function_count():
    """structural_score is a documented library entry point, so it must not
    raise on an all-null metrics row (the archived mixed-glm-5.2-1 branch has
    one -- merger_rate.py is absent there)."""
    score, components = structure.structural_score(
        {"function_count": None, "median_function_loc": None, "mean_cyclomatic": None},
        _POLICY)
    assert score is None and components == {}
