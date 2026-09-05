import os

import pytest

import reference_check as rc


def _make_task(tmp_path, authorized_surface, ref_files, variant=None, variant_files=None):
    """ref_files/variant_files: {relative_authorized_path: content}."""
    task_dir = tmp_path / "task"
    ref_dir = task_dir / "reference_solution"
    ref_dir.mkdir(parents=True)
    for rel, content in ref_files.items():
        (ref_dir / os.path.basename(rel)).write_text(content)
    if variant is not None:
        variant_dir = ref_dir / variant
        variant_dir.mkdir()
        for rel, content in (variant_files or {}).items():
            (variant_dir / os.path.basename(rel)).write_text(content)
    meta = {"authorized_surface": authorized_surface}
    return str(task_dir), meta


def test_install_variant_installs_plain_reference_with_no_variant(tmp_path):
    task_dir, meta = _make_task(
        tmp_path,
        authorized_surface=["src/foo.py", "tests/test_foo.py"],
        ref_files={"src/foo.py": "# real foo\n", "tests/test_foo.py": "# real tests\n"},
    )
    dest = tmp_path / "dest"
    dest.mkdir()

    rc.install_variant(task_dir, meta, str(dest), None)

    assert (dest / "src" / "foo.py").read_text() == "# real foo\n"
    assert (dest / "tests" / "test_foo.py").read_text() == "# real tests\n"


def test_install_variant_layers_variant_over_base(tmp_path):
    """A variant that ships only the test file must still run against the
    base reference solution's own (correct) src/ -- matching how this repo's
    weak_baseline/ controls are actually used (Task 005's
    weak_baseline/test_calc_provenance.py over the reference's calc.py)."""
    task_dir, meta = _make_task(
        tmp_path,
        authorized_surface=["src/foo.py", "tests/test_foo.py"],
        ref_files={"src/foo.py": "# real foo\n", "tests/test_foo.py": "# real tests\n"},
        variant="weak_baseline",
        variant_files={"tests/test_foo.py": "# vacuous test\n"},
    )
    dest = tmp_path / "dest"
    dest.mkdir()

    rc.install_variant(task_dir, meta, str(dest), "weak_baseline")

    assert (dest / "src" / "foo.py").read_text() == "# real foo\n"
    assert (dest / "tests" / "test_foo.py").read_text() == "# vacuous test\n"


def test_install_variant_raises_when_variant_directory_missing(tmp_path):
    task_dir, meta = _make_task(
        tmp_path,
        authorized_surface=["src/foo.py"],
        ref_files={"src/foo.py": "# real foo\n"},
    )
    dest = tmp_path / "dest"
    dest.mkdir()

    with pytest.raises(SystemExit, match="does not exist"):
        rc.install_variant(task_dir, meta, str(dest), "weak_baseline")


def test_install_variant_raises_when_variant_file_not_authorized(tmp_path):
    task_dir, meta = _make_task(
        tmp_path,
        authorized_surface=["tests/test_foo.py"],
        ref_files={"tests/test_foo.py": "# real tests\n"},
        variant="weak_baseline",
        variant_files={"tests/test_bogus.py": "# oops\n"},
    )
    dest = tmp_path / "dest"
    dest.mkdir()

    with pytest.raises(SystemExit, match="no authorized_surface entry"):
        rc.install_variant(task_dir, meta, str(dest), "weak_baseline")


def test_install_variant_raises_when_variant_directory_empty(tmp_path):
    task_dir, meta = _make_task(
        tmp_path,
        authorized_surface=["tests/test_foo.py"],
        ref_files={"tests/test_foo.py": "# real tests\n"},
        variant="weak_baseline",
        variant_files={},
    )
    dest = tmp_path / "dest"
    dest.mkdir()

    with pytest.raises(SystemExit, match="no .py files to install"):
        rc.install_variant(task_dir, meta, str(dest), "weak_baseline")


def test_build_manifest_labels_variant_in_model_field():
    manifest = rc.build_manifest(
        run_id="REFCHECK-001-weak_baseline", task_id="001-merger-rate-feature",
        variant="weak_baseline", baseline_ref="frozen-substrate", before_head="abc123",
        venv_setup_seconds=12.34, changed_files=["tests/test_merger_rate.py"],
        worktree="/tmp/worktree",
    )

    assert manifest["model"] == "reference-solution+weak_baseline"
    assert manifest["harness"] == "none"
    assert manifest["timed_out"] is False
    assert manifest["committed"] is False
    assert manifest["venv_setup_seconds"] == 12.3
    assert manifest["before_head"] == "abc123"
    assert manifest["changed_files"] == ["tests/test_merger_rate.py"]


def test_build_manifest_plain_reference_has_no_variant_suffix():
    manifest = rc.build_manifest(
        run_id="REFCHECK-001", task_id="001-merger-rate-feature", variant=None,
        baseline_ref="frozen-substrate", before_head="abc123", venv_setup_seconds=1.0,
        changed_files=[], worktree="/tmp/worktree",
    )

    assert manifest["model"] == "reference-solution"


def test_make_run_id_is_unique_across_calls_with_identical_arguments():
    """A deterministic id (task+variant+label alone) would let a second run
    silently overwrite an earlier canonical eval/results/runs/ record --
    grade_trial.py's own overwrite guard only checks the rubric hash, not
    whether the underlying task contract changed in between (codex/
    gpt-5.6-sol review, 2026-09-05)."""
    a = rc.make_run_id("001-merger-rate-feature", "weak_baseline", "ceiling")
    b = rc.make_run_id("001-merger-rate-feature", "weak_baseline", "ceiling")

    assert a != b
    assert a.startswith(b[:8])  # same UTC-timestamp prefix format
    assert "REFCHECK-001-merger-rate-feature-weak_baseline-ceiling" in a


def test_make_run_id_omits_absent_variant_and_label():
    run_id = rc.make_run_id("001-merger-rate-feature", None, None)

    assert "REFCHECK-001-merger-rate-feature-" in run_id
    assert "weak_baseline" not in run_id


@pytest.mark.parametrize("value", ["../escape", "a/b", "/etc/passwd", "..", ".", ""])
def test_validate_component_rejects_path_unsafe_values(value):
    with pytest.raises(SystemExit):
        rc._validate_component(value, "--variant")


@pytest.mark.parametrize("value", ["weak_baseline", "ceiling-run.1", None])
def test_validate_component_accepts_safe_values(value):
    rc._validate_component(value, "--variant")  # must not raise


def test_check_no_basename_collisions_raises_on_ambiguous_authorized_surface():
    """src/config.py and tests/config.py would both resolve to the same
    basename lookup key, so a reference_solution/config.py file could
    silently land at the wrong one (codex/gpt-5.6-sol review, 2026-09-05)."""
    with pytest.raises(SystemExit, match="ambiguous basenames"):
        rc._check_no_basename_collisions(["src/config.py", "tests/config.py"])


def test_check_no_basename_collisions_accepts_unique_authorized_surface():
    rc._check_no_basename_collisions(["src/config.py", "tests/test_foo.py"])  # must not raise
