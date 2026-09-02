"""Injects one behavioural mutation into data_reader after import.

Used to test whether the Developer's OWN test suite can actually FAIL -- the
test_adequacy rubric category, which for this task is the *only* thing being
measured (see spec.md's "How this task is scored" and
reference_solution/README.md). Selected by the MUTATION environment variable.
Works by monkey-patching the already-imported module's public function
post-import, so it operates identically regardless of how the Developer's test
file imports it, and no trial file is ever edited.

Activated by putting this file's directory on PYTHONPATH (Python auto-imports
any sitecustomize.py found on sys.path at interpreter startup) and setting
MUTATION=<id> before running the trial's own pytest.

Design constraints specific to this task -- read before adding a mutation:

1. **Patch only `load_galaxy_catalog`.** It is the one name in `data_reader`
   the task is about, and the module is frozen (`frozen_unchanged` in
   meta.yaml), so its signature and internal structure cannot vary between
   submissions. Modules are matched by BASENAME, so `import data_reader`,
   `from src import data_reader`, `import src.data_reader` and
   `from data_reader import load_galaxy_catalog` are all patched identically
   (Task 001's audit found exact-name matching gave a submission using a
   different import style zero mutations).

   **Three module-loading paths are hooked**: `builtins.__import__` (the
   `import` statement), `importlib.import_module`, which does not route
   through `__import__` at all, and `importlib.reload`, which re-executes the
   module body and would otherwise restore the unwrapped function while the
   `__MUTATED__` marker survived on the same namespace. An r1 review found the
   first gap and an r2 review the second; either one silently hands a perfect
   suite a 0/N, a false negative in this task's only real signal rather than a
   weak submission. Both are covered by before/after controls recorded in
   reference_solution/README.md.

   **Known, accepted residual gap**: a submission that loads the module
   through `importlib.util.spec_from_file_location(...)` +
   `loader.exec_module(...)` builds a module object no import hook ever sees,
   and would receive no mutation. Chasing it would mean either intercepting
   `importlib.util` far deeper or moving to source-patching the frozen file,
   which this repo's conventions (AGENTS.md) deliberately steer away from --
   post-import monkeypatching is chosen for insensitivity to *reasonable*
   import styles, not to every module-loading API in the stdlib. No test file
   in this repo's history, including this task's reference, loads a module
   that way; every one uses `sys.path.insert` plus a plain import.

2. **The frozen suite cannot kill any of these, and that is checked.** The
   mutation gate runs `pytest tests/`, which includes the three frozen test
   files -- but none of them imports `data_reader` or `calc` at all (verified:
   `grep -rn data_reader tests/` matches only a comment in
   test_statistical.py). Every kill therefore comes from the submission's own
   test file. The freebie control in reference_solution/README.md re-measures
   this rather than trusting it, and must be re-run before adding a mutation.

3. **One mutation, one predicate.** Task 003's r1/r2 reviews found that broad
   mutations let a suite kill them with a single representative case, so a
   materially incomplete suite still scored full marks. Each entry below
   removes, weakens or over-tightens exactly one documented obligation. The
   families that vary only by field -- `M10` (the float64 conversion) and
   `M13` (the mass selection), one mutation per catalog array each -- are
   generated in loops.

4. **No mutation may be killable by a shape-only check.** An r1 review found
   the original `M13` family substituted the whole *unmasked* array back in,
   which changes that field's length: a single "all seven arrays are the same
   length" assertion killed all seven without checking one selected value.
   Every `M13` now keeps the correct post-selection length and corrupts only
   *which* rows survived (`np.roll` of the mask), so a shape-only suite scores
   zero on the family. `reference_solution/degenerate_controls/shape_only/`
   is the checked-in control that measures this.

5. **Guard-removal mutations re-run a transcription of the frozen body, and
   only on inputs the real function rejects.** `_body()` below is the frozen
   `load_galaxy_catalog` body with named guards skippable. It is only ever
   reached after the real function has already raised, i.e. on input that has
   no accepted behaviour to be unfaithful about, so it cannot perturb a valid
   call. `M00_identity_control` (registered, deliberately NOT in
   mutation_list.txt) runs `_body()` with no guard skipped on every such call
   and is the control that proves that: it must leave a suite green.

6. **Nothing here silently swallows its own bugs.** A mutation whose transform
   raised would otherwise degrade to a no-op and read as "the submission's
   tests are weak" instead of "this mutation is broken". Exceptions from a
   transform propagate, and so do exceptions from `_patch_data_reader` in the
   import hook -- an r1 review found the hook's outer `except Exception: pass`
   swallowing a failed patch install, which would have silently graded a trial
   against the *unmutated* function and reported every mutation as survived.

`mutation_list.txt` is generated from the registries below, never hand-typed:

    cd eval/tasks/004-catalog-loader-test-adequacy/mutations
    PYTHONPATH=. ../../../../venv/bin/python -c "import sitecustomize as s; \
        print('\\n'.join(s.all_mutation_ids()))" > mutation_list.txt

PYTHONPATH matters even here: Homebrew's CPython ships its own
lib/python3.14/sitecustomize.py, so a plain `import sitecustomize` from this
directory resolves to that one instead. The mutation gate is unaffected --
grade_trial.py puts this directory on PYTHONPATH, which precedes the stdlib
directory on sys.path, so the interpreter auto-imports this file at startup.
"""
import functools
import importlib
import os
import sys

MUT = os.environ.get("MUTATION")

_ARRAY_FIELDS = ("x", "y", "z", "vx", "vy", "vz", "log_stellar_mass")

#: The pipeline's own defaults, for the mutation that ignores `config`.
_DEFAULT_LOG_MASS_MIN = 8.0
_DEFAULT_LOG_MASS_MAX = 11.0

# --------------------------------------------------------------- registries
_REJECTORS = {}          # id -> fn(filepath, config) -> message or None
_GUARD_REMOVERS = {}     # id -> fn(filepath, config) -> result dict or PASS
_RESULT_MUTATORS = {}    # id -> fn(result, filepath, config) -> result
_MESSAGE_SCRUBBERS = {}  # id -> fn(filepath) -> substring to erase

#: Returned by a guard remover that does not apply to this input: the original
#: AssertionError is re-raised untouched.
PASS = object()

#: Registered but deliberately absent from mutation_list.txt -- the control
#: that proves `_body()` reproduces the frozen function's rejections.
IDENTITY_CONTROL = "M00_identity_control"


def _register(table, name):
    def deco(fn):
        table[name] = fn
        return fn
    return deco


def rejector(name):
    """Over-tightens: rejects an input the contract declares valid, or reports
    a different guard than the contract's order requires."""
    return _register(_REJECTORS, name)


def guard_remover(name):
    """Removes one rejection: input the frozen function rejects now returns
    (or fails differently). Consulted only after the real call has raised
    AssertionError."""
    return _register(_GUARD_REMOVERS, name)


def result_mutator(name):
    """Corrupts the value returned for input the contract declares valid."""
    return _register(_RESULT_MUTATORS, name)


def message_scrubber(name):
    """Erases one required substring from every rejection message that carries
    it. Killed only by a suite that matches on that substring."""
    return _register(_MESSAGE_SCRUBBERS, name)


def all_mutation_ids():
    """Every scored mutation id, for mutation_list.txt. The identity control is
    excluded: it is a validation instrument, not a mutation."""
    ids = (set(_REJECTORS) | set(_GUARD_REMOVERS) | set(_RESULT_MUTATORS)
           | set(_MESSAGE_SCRUBBERS))
    ids.discard(IDENTITY_CONTROL)
    return sorted(ids)


# ------------------------------------------------------------------ helpers
def _np():
    import numpy as np
    return np


def _read_file(filepath):
    """The seven arrays exactly as stored (no dtype conversion), plus the two
    scalar attributes and the file's dataset and attribute names."""
    import h5py
    np = _np()
    with h5py.File(filepath, "r") as f:
        raw = {key: np.asarray(f[key][:]) for key in _ARRAY_FIELDS}
        raw["redshift"] = float(f.attrs["redshift"])
        raw["box_size"] = float(f.attrs["box_size"])
        raw["datasets"] = sorted(f.keys())
        raw["attributes"] = sorted(f.attrs.keys())
    return raw


def _read_or_none(filepath):
    """`_read_file` for the guard removers and rejectors, which must decline
    rather than raise on any input they were not written for -- a file that
    does not exist, is not HDF5, or is missing a required dataset."""
    try:
        return _read_file(filepath)
    except Exception:
        return None


def _mask_for(raw, log_mass_min, log_mass_max):
    """The selection mask the frozen body would build for these limits."""
    mass = raw["log_stellar_mass"].astype(float)
    return (mass >= float(log_mass_min)) & (mass <= float(log_mass_max))


def _body(filepath, config, skip=()):
    """The frozen `load_galaxy_catalog` body, with named guards skippable.

    Behaviourally transcribed from src/data_reader.py rather than copied
    character for character: the file read goes through `_read_file` above,
    and the missing-file guard is not reproduced here at all (a guard remover
    is only consulted once the real function has raised, and `M01` handles
    that case before this is ever reached). Every guard this *does* carry
    fires on the same condition and with the same message as the frozen
    function, which `M00_identity_control` measures rather than assumes.
    """
    np = _np()
    raw = _read_file(filepath)
    catalog = {key: raw[key].astype(float) for key in _ARRAY_FIELDS}
    catalog["redshift"] = raw["redshift"]
    catalog["box_size"] = raw["box_size"]

    n = len(catalog["x"])
    if "empty" not in skip:
        assert n > 0, f"Empty catalog: {filepath}"

    if "box_size" not in skip:
        assert catalog["box_size"] > 0, "box_size must be positive"
    if "mass_nonneg" not in skip:
        assert np.all(catalog["log_stellar_mass"] >= 0), (
            "log_stellar_mass contains non-positive values; "
            "check units (expected log10 M_sun)"
        )

    log_m = catalog["log_stellar_mass"]
    mask = (log_m >= config["log_mass_min"]) & (log_m <= config["log_mass_max"])
    n_selected = mask.sum()
    if "empty_selection" not in skip:
        assert n_selected > 0, (
            f"No galaxies in mass range [{config['log_mass_min']}, "
            f"{config['log_mass_max']}] log10 M_sun in {filepath}"
        )

    for key in _ARRAY_FIELDS:
        catalog[key] = catalog[key][mask]
    return catalog


def _selection_message(filepath, config):
    """The message the frozen function raises when nothing survives the cut."""
    return (f"No galaxies in mass range [{config['log_mass_min']}, "
            f"{config['log_mass_max']}] log10 M_sun in {filepath}")


# =========================================================================
# Guard removers: each deletes exactly one of the five documented rejections.
#
# Note what a faithful removal implies: deleting a guard does not always make
# the call succeed, it makes it fail *later and for a different reason*. M02 is
# the clearest case -- with the empty-catalog guard gone, a zero-galaxy catalog
# runs on and trips the mass-selection guard instead. That mutation is killed
# only by a suite that distinguishes the two rejections by their message, which
# is exactly the obligation spec.md's message table states.
# =========================================================================
@guard_remover("M01_missing_file_guard_removed")
def _m01(filepath, config):
    """Without `assert os.path.isfile(...)`, h5py's own OSError escapes."""
    if os.path.isfile(str(filepath)):
        return PASS
    raise OSError(
        f"Unable to synchronously open file (unable to open file: "
        f"name = '{filepath}', errno = 2, error message = 'No such file or "
        f"directory', flags = 0, o_flags = 0)")


@guard_remover("M02_empty_catalog_guard_removed")
def _m02(filepath, config):
    raw = _read_or_none(filepath)
    if raw is None or raw["x"].size != 0:
        return PASS
    return _body(filepath, config, skip=("empty",))


@guard_remover("M03_box_size_positive_guard_removed")
def _m03(filepath, config):
    raw = _read_or_none(filepath)
    if raw is None or raw["x"].size == 0 or raw["box_size"] > 0:
        return PASS
    return _body(filepath, config, skip=("box_size",))


@guard_remover("M04_negative_mass_guard_removed")
def _m04(filepath, config):
    np = _np()
    raw = _read_or_none(filepath)
    if raw is None or raw["x"].size == 0 or raw["box_size"] <= 0:
        return PASS
    if np.all(raw["log_stellar_mass"].astype(float) >= 0):
        return PASS
    return _body(filepath, config, skip=("mass_nonneg",))


@guard_remover("M05_empty_selection_guard_removed")
def _m05(filepath, config):
    np = _np()
    raw = _read_or_none(filepath)
    if raw is None or raw["x"].size == 0 or raw["box_size"] <= 0:
        return PASS
    mass = raw["log_stellar_mass"].astype(float)
    if not np.all(mass >= 0):
        return PASS
    try:
        mask = _mask_for(raw, config["log_mass_min"], config["log_mass_max"])
    except Exception:
        return PASS
    if mask.sum() > 0:
        return PASS
    return _body(filepath, config, skip=("empty_selection",))


@guard_remover(IDENTITY_CONTROL)
def _m00(filepath, config):
    """Not a mutation and not in mutation_list.txt. Runs `_body()` with every
    guard intact, so it re-raises exactly what the frozen function raised --
    the control that `_body()`'s transcription is faithful."""
    raw = _read_or_none(filepath)
    if raw is None:
        return PASS
    return _body(filepath, config)


# =========================================================================
# Rejectors: over-tightening, plus the one guard-order swap. Killed only by a
# suite that tests the "must NOT be rejected" half of the contract, or that
# pins which guard reports a doubly-invalid input.
# =========================================================================
@rejector("M08_zero_mass_rejected")
def _m08(filepath, config):
    """The guard is `>= 0`, and its message says "non-positive" -- so a
    submission mis-reading the message and writing `> 0` is the natural
    mistake. Killed only by a suite whose fixture carries a mass of exactly
    0.0."""
    np = _np()
    raw = _read_or_none(filepath)
    if raw is None:
        return None
    mass = raw["log_stellar_mass"].astype(float)
    if mass.size and np.any(mass == 0.0):
        return ("log_stellar_mass contains non-positive values; "
                "check units (expected log10 M_sun)")
    return None


@rejector("M09_extra_datasets_rejected")
def _m09(filepath, config):
    """Extra datasets in the file are ignored by contract. Killed only by a
    suite whose fixture carries one (as every catalog written by
    generate_test_data.py does)."""
    raw = _read_or_none(filepath)
    if raw is None:
        return None
    extra = [name for name in raw["datasets"] if name not in _ARRAY_FIELDS]
    if extra:
        return f"Catalog file contains unexpected datasets: {extra}"
    return None


@rejector("M18_extra_attributes_rejected")
def _m18(filepath, config):
    """As M09, for the *attribute* half of the same contract clause. Separate
    mutation because a fixture can easily carry one and not the other."""
    raw = _read_or_none(filepath)
    if raw is None:
        return None
    extra = [name for name in raw["attributes"]
             if name not in ("redshift", "box_size")]
    if extra:
        return f"Catalog file contains unexpected attributes: {extra}"
    return None


# M19: one mutation per adjacent pair of guards whose order the contract pins.
# Each fires only on the doubly-invalid input where that pair's order is
# observable at all, so each is a strict no-op everywhere else. An r3 review
# found only one of the three meaningful pairs covered (the fourth,
# empty-before-selection, is already covered from the other side by M02).
@rejector("M19_box_size_reported_before_emptiness")
def _m19a(filepath, config):
    """Empty catalog + non-positive box_size: the contract reports emptiness."""
    raw = _read_or_none(filepath)
    if raw is None:
        return None
    if raw["x"].size == 0 and raw["box_size"] <= 0:
        return "box_size must be positive"
    return None


@rejector("M19_negative_mass_reported_before_box_size")
def _m19b(filepath, config):
    """Non-positive box_size + a negative mass: the contract reports the box."""
    np = _np()
    raw = _read_or_none(filepath)
    if raw is None or raw["x"].size == 0 or raw["box_size"] > 0:
        return None
    mass = raw["log_stellar_mass"].astype(float)
    if mass.size and np.any(mass < 0):
        return ("log_stellar_mass contains non-positive values; "
                "check units (expected log10 M_sun)")
    return None


@rejector("M19_empty_selection_reported_before_negative_mass")
def _m19c(filepath, config):
    """A negative mass + a selection that keeps nothing: the contract reports
    the mass."""
    np = _np()
    raw = _read_or_none(filepath)
    if raw is None or raw["x"].size == 0 or raw["box_size"] <= 0:
        return None
    mass = raw["log_stellar_mass"].astype(float)
    if not (mass.size and np.any(mass < 0)):
        return None
    try:
        mask = _mask_for(raw, config["log_mass_min"], config["log_mass_max"])
    except Exception:
        return None
    if mask.sum() > 0:
        return None
    return _selection_message(filepath, config)


# =========================================================================
# Result mutators: the value returned for input the contract declares valid.
# =========================================================================
def _drop_at_edge(out, filepath, config, key):
    """Exclude the galaxies sitting exactly on one mass-selection edge, i.e.
    what a strict `>` / `<` in place of the contract's `>=` / `<=` would do."""
    np = _np()
    edge = float(config[key])
    mass = np.asarray(out["log_stellar_mass"], dtype=float)
    keep = mass != edge
    if keep.all():
        return out
    if not keep.any():
        raise AssertionError(_selection_message(filepath, config))
    out = dict(out)
    for field in _ARRAY_FIELDS:
        out[field] = np.asarray(out[field])[keep]
    return out


@result_mutator("M06_mass_min_boundary_excluded")
def _m06(out, filepath, config):
    return _drop_at_edge(out, filepath, config, "log_mass_min")


@result_mutator("M07_mass_max_boundary_excluded")
def _m07(out, filepath, config):
    return _drop_at_edge(out, filepath, config, "log_mass_max")


# M10: one mutation per catalog array. `.astype(float)` is applied field by
# field in the frozen body, so "converted six of the seven" is a real defect,
# and an r1 review of this task found the original single bundled mutation let
# a suite asserting one field's dtype take credit for all seven (the same
# bundling defect Task 003 records for its M05/M13/M14).
def _make_cast_removed(field):
    @result_mutator(f"M10_float64_cast_removed_{field}")
    def _mut(out, filepath, config, _field=field):
        np = _np()
        raw = _read_file(filepath)
        stored = raw[_field].dtype
        if stored == np.float64:
            return out
        out = dict(out)
        out[_field] = np.asarray(out[_field]).astype(stored)
        return out
    return _mut


for _field in _ARRAY_FIELDS:
    _make_cast_removed(_field)


@result_mutator("M11_redshift_off_by_one")
def _m11(out, filepath, config):
    """`redshift` read as `1 + z` -- the pipeline's most common unit slip."""
    out = dict(out)
    out["redshift"] = float(out["redshift"]) + 1.0
    return out


@result_mutator("M12_box_size_scaled")
def _m12(out, filepath, config):
    """`box_size` returned scaled, the shape an h-factor slip takes. Never a
    no-op: box_size is positive by the time this runs."""
    out = dict(out)
    out["box_size"] = float(out["box_size"]) * 2.0
    return out


# M13: one mutation per catalog array, for *which rows* survived.
#
# Read note 4 in the module docstring before touching this. The mutation keeps
# the correct post-selection length and rotates the mask by one position, so
# the field comes back with the right number of rows and the wrong ones. A
# suite that only compares lengths across the seven arrays cannot kill any of
# them; only a suite that pins that field's selected *values* can.
#
# `np.roll` is a permutation, so the selected count is preserved exactly. The
# mutation is a genuine no-op when the mask is uniform (every galaxy selected,
# which is the fixture shape that cannot detect a selection defect at all) or
# when the field's values do not vary between the shifted rows -- an all-zero
# velocity column, say. That is a real property of such a fixture, not a gap:
# spec.md tells the submission that a fixture whose values repeat across
# galaxies cannot detect a mis-selection.
def _make_selection_shifted(field):
    @result_mutator(f"M13_wrong_rows_selected_{field}")
    def _mut(out, filepath, config, _field=field):
        np = _np()
        raw = _read_file(filepath)
        try:
            mask = _mask_for(raw, config["log_mass_min"], config["log_mass_max"])
        except Exception:
            return out
        if mask.size < 2 or bool(np.all(mask)) or not bool(np.any(mask)):
            return out
        shifted = np.roll(mask, 1)
        out = dict(out)
        out[_field] = raw[_field].astype(float)[shifted]
        return out
    return _mut


for _field in _ARRAY_FIELDS:
    _make_selection_shifted(_field)


@result_mutator("M15_config_bounds_ignored")
def _m15(out, filepath, config):
    """The selection uses the pipeline's default [8, 11] range instead of the
    `config` it was handed -- what hardcoding the limits looks like from the
    outside. Killed only by a suite that loads the same catalog under a
    non-default mass range."""
    np = _np()
    raw = _read_file(filepath)
    try:
        true_mask = _mask_for(raw, config["log_mass_min"], config["log_mass_max"])
    except Exception:
        return out
    hard_mask = _mask_for(raw, _DEFAULT_LOG_MASS_MIN, _DEFAULT_LOG_MASS_MAX)
    if np.array_equal(true_mask, hard_mask):
        return out
    if not bool(np.any(hard_mask)):
        raise AssertionError(_selection_message(filepath, config))
    out = dict(out)
    for field in _ARRAY_FIELDS:
        out[field] = raw[field].astype(float)[hard_mask]
    return out


# M16: one mutation per catalog array, for the *order* the surviving rows come
# back in. An r2 review found the original single mutation reversed all seven
# arrays together, so an order check on one field took credit for the other
# six -- the same bundling defect as round 1's M10, and the reason M10 and M13
# are per-field families. Reversing one field also misaligns it against the
# other six, which is the property "at the same position" in spec.md's
# selection clause.
#
# The reversed view is copied back into a contiguous array: `[::-1]` alone
# leaves a negative stride, and a suite checking `flags.c_contiguous` (for
# whatever unrelated reason) would then kill the mutation without ever looking
# at the order.
def _make_order_reversed(field):
    @result_mutator(f"M16_selected_order_reversed_{field}")
    def _mut(out, filepath, config, _field=field):
        np = _np()
        values = np.asarray(out[_field])
        if values.size < 2:
            return out
        out = dict(out)
        out[_field] = np.ascontiguousarray(values[::-1])
        return out
    return _mut


for _field in _ARRAY_FIELDS:
    _make_order_reversed(_field)


# M20: the two `float(...)` casts on the file attributes, one mutation each
# (the casts are independent statements, and the r1/r2 reviews' dominant
# finding was mutations bundling independent obligations). h5py hands back a
# `numpy.float64` for a scalar float attribute, which is what these return.
#
# Note carefully what can and cannot kill these: `numpy.float64` is a SUBCLASS
# of Python `float`, so `isinstance(x, float)` is True for the mutated value
# and a suite asserting that survives. Only `type(x) is float` -- which is what
# spec.md's Values Returned table pins -- sees the difference. This is the
# scalar twin of the lesson M10 teaches for the arrays: the value is right, the
# type is not, and a value assertion cannot tell.
def _make_scalar_cast_removed(key):
    @result_mutator(f"M20_{key}_not_cast_to_float")
    def _mut(out, filepath, config, _key=key):
        np = _np()
        out = dict(out)
        out[_key] = np.float64(out[_key])
        return out
    return _mut


for _key in ("redshift", "box_size"):
    _make_scalar_cast_removed(_key)


# M21: the *conditional* half of the extras contract. M09/M18 prove extras are
# not rejected and M17 leaks a key unconditionally, but an r3 review found
# nothing covering the implementation that actually copies the file's extra
# datasets or attributes into the result -- the shape a `for name in f: ...`
# loop takes. Each of these is a strict no-op on a fixture with no extras, so
# it is killed only by a suite whose extras fixture pins the returned key set.
@result_mutator("M21_extra_dataset_leaked")
def _m21a(out, filepath, config):
    import h5py
    np = _np()
    raw = _read_file(filepath)
    extra = [name for name in raw["datasets"] if name not in _ARRAY_FIELDS]
    if not extra:
        return out
    out = dict(out)
    with h5py.File(filepath, "r") as f:
        for name in extra:
            out[name] = np.asarray(f[name][:])
    return out


@result_mutator("M21_extra_attribute_leaked")
def _m21b(out, filepath, config):
    import h5py
    raw = _read_file(filepath)
    extra = [name for name in raw["attributes"]
             if name not in ("redshift", "box_size")]
    if not extra:
        return out
    out = dict(out)
    with h5py.File(filepath, "r") as f:
        for name in extra:
            out[name] = f.attrs[name]
    return out


# M22: over-tightening on the two scalars spec.md lists as must-accept, the
# same shape as M08 does for a zero mass. Expressed as result mutators rather
# than rejectors on purpose: a rejector runs *before* the frozen function and
# would preempt a genuine rejection on a doubly-invalid fixture, reporting the
# wrong reason for an unrelated test. Running after a successful call
# guarantees the input was one the contract accepts.
@result_mutator("M22_zero_redshift_rejected")
def _m22a(out, filepath, config):
    """`redshift` of exactly 0.0 is legal (z=0 is the present day). An
    over-strict "redshift must be positive" guard is the plausible mistake."""
    if float(out["redshift"]) == 0.0:
        raise AssertionError("redshift must be positive")
    return out


@result_mutator("M22_small_box_size_rejected")
def _m22b(out, filepath, config):
    """Any positive box_size is legal, including a 1 Mpc test box. An
    over-strict plausibility floor is the mistake this catches."""
    if float(out["box_size"]) < 10.0:
        raise AssertionError("box_size must be at least 10 Mpc (check units)")
    return out


@result_mutator("M17_unexpected_result_key_leaked")
def _m17(out, filepath, config):
    """An extra convenience key in the returned dict. The contract says the
    dict has exactly nine keys; killed only by a suite that asserts the whole
    key set rather than the presence of the ones it happens to use."""
    out = dict(out)
    out["n_selected"] = int(len(out["x"]))
    return out


# =========================================================================
# Message scrubbers: each erases one substring spec.md's rejection-message
# table requires. Killed only by a suite that matches on that substring, which
# is the difference between "the suite noticed a failure" and "the suite
# noticed the right failure".
# =========================================================================
# One mutation per required substring *per message*. An r2 review found the
# original single "omit the filepath" mutation covered all three messages that
# must quote the path at once, so a suite checking the path in one of them took
# credit for all three -- and that no mutation covered the units note in the
# negative-mass message at all.
def _make_message_scrubber(name, token, only_when=None, count=1):
    """token: the substring to erase, or a callable(filepath) returning it.
    only_when: this mutation applies only to messages containing this marker,
    which is what makes one obligation-per-message possible for the filepath.
    count: how many occurrences to erase. The reason tokens erase exactly one
    (an r3 review noted an unbounded replace could double-scrub if a reason
    token happened to appear inside a contrived filename as well); the filepath
    scrubbers erase every occurrence of the one literal path they were handed,
    which is the obligation they exist to remove."""
    @message_scrubber(name)
    def _scrub(message, filepath, _token=token, _only=only_when, _count=count):
        if _only is not None and _only not in message:
            return None
        resolved = _token(filepath) if callable(_token) else _token
        return (resolved, _count)
    return _scrub


def _filepath_token(filepath):
    return str(filepath)


# The reason each message names.
_make_message_scrubber("M14_message_omits_file_not_found",
                       "Catalog file not found")
_make_message_scrubber("M14_message_omits_empty_catalog", "Empty catalog")
_make_message_scrubber("M14_message_omits_box_size_positive",
                       "box_size must be positive")
_make_message_scrubber("M14_message_omits_log_stellar_mass",
                       "log_stellar_mass")
_make_message_scrubber("M14_message_omits_units_note",
                       "check units (expected log10 M_sun)")
_make_message_scrubber("M14_message_omits_no_galaxies_in_range",
                       "No galaxies in mass range")

# The offending path, in each of the three messages that must quote it.
_make_message_scrubber("M14_message_omits_filepath_missing_file",
                       _filepath_token, only_when="Catalog file not found",
                       count=-1)
_make_message_scrubber("M14_message_omits_filepath_empty_catalog",
                       _filepath_token, only_when="Empty catalog", count=-1)
_make_message_scrubber("M14_message_omits_filepath_mass_range",
                       _filepath_token, only_when="No galaxies in mass range",
                       count=-1)


# ============================================================ installation
def _install_rejector(module, fn):
    original = module.load_galaxy_catalog

    @functools.wraps(original)
    def patched(filepath, config, *a, **k):
        message = fn(filepath, config)
        if message:
            raise AssertionError(message)
        return original(filepath, config, *a, **k)

    module.load_galaxy_catalog = patched


def _install_guard_remover(module, fn):
    original = module.load_galaxy_catalog

    @functools.wraps(original)
    def patched(filepath, config, *a, **k):
        try:
            return original(filepath, config, *a, **k)
        except AssertionError:
            out = fn(filepath, config)
            if out is PASS:
                raise
            return out

    module.load_galaxy_catalog = patched


def _install_result_mutator(module, fn):
    original = module.load_galaxy_catalog

    @functools.wraps(original)
    def patched(filepath, config, *a, **k):
        out = original(filepath, config, *a, **k)
        return fn(out, filepath, config)

    module.load_galaxy_catalog = patched


def _install_message_scrubber(module, fn):
    original = module.load_galaxy_catalog

    @functools.wraps(original)
    def patched(filepath, config, *a, **k):
        try:
            return original(filepath, config, *a, **k)
        except AssertionError as exc:
            message = str(exc)
            scrub = fn(message, filepath)
            token, count = scrub if scrub else (None, 0)
            if not token or token not in message:
                raise
            scrubbed = message.replace(token, "", count).strip() or "rejected"
        # Raised deliberately OUTSIDE the handler. Inside it, CPython would
        # chain the original exception onto __context__, and `raise ... from
        # None` would set __suppress_context__ -- either is exception metadata
        # the frozen function's bare `assert` never produces, and an r2 review
        # noted that a suite checking those flags could kill every M14 without
        # ever looking at a message. Out here no exception is being handled, so
        # the mutated AssertionError has the same shape as the real one and
        # only its text differs.
        raise AssertionError(scrubbed)

    module.load_galaxy_catalog = patched


def _patch_data_reader(m):
    if MUT in _REJECTORS:
        _install_rejector(m, _REJECTORS[MUT])
    elif MUT in _GUARD_REMOVERS:
        _install_guard_remover(m, _GUARD_REMOVERS[MUT])
    elif MUT in _RESULT_MUTATORS:
        _install_result_mutator(m, _RESULT_MUTATORS[MUT])
    elif MUT in _MESSAGE_SCRUBBERS:
        _install_message_scrubber(m, _MESSAGE_SCRUBBERS[MUT])


# --------------------------------------------------- the import hooks
# Ported from Task 003's mutations/sitecustomize.py, whose basename matching
# was Task 001's fix for exact-import-name patching, and extended here with the
# importlib.import_module path (see note 1 in the module docstring).
def _is_target(fullname, mod):
    """Is this the module under test? Basename match plus the one attribute the
    task guarantees. Shared by the import hooks and the reload hook so no path
    can touch a module the other would have left alone."""
    if mod is None:
        return False
    leaf = str(fullname).rsplit(".", 1)[-1]
    try:
        return leaf == "data_reader" and hasattr(mod, "load_galaxy_catalog")
    except Exception:
        return False


def _patch_candidate(fullname, mod):
    """Install the selected mutation into `mod` if it is the module under test.

    The `except` here guards only the attribute probing -- a module object with
    an exploding `__getattr__`. A failure inside `_patch_data_reader` must
    propagate: swallowing it would leave the trial running against the correct
    function while the gate reported every mutation as survived (note 6)."""
    if not _is_target(fullname, mod):
        return
    try:
        already_patched = getattr(mod, "__MUTATED__", False)
    except Exception:
        return
    if already_patched:
        return
    mod.__MUTATED__ = True
    try:
        _patch_data_reader(mod)
    except Exception:
        mod.__MUTATED__ = False
        raise


def _patch_all(candidates):
    seen = set()
    for fullname, mod in candidates:
        if mod is None or id(mod) in seen:
            continue
        seen.add(id(mod))
        _patch_candidate(fullname, mod)


_orig_import = (__builtins__["__import__"] if isinstance(__builtins__, dict)
                else __builtins__.__import__)
_orig_import_module = importlib.import_module
_orig_reload = importlib.reload


def _imp(name, *a, **k):
    m = _orig_import(name, *a, **k)
    candidates = [(name, sys.modules.get(name))]
    returned_name = getattr(m, "__name__", None)
    if returned_name:
        candidates.append((returned_name, m))
    fromlist = a[2] if len(a) > 2 else k.get("fromlist", ())
    for item in fromlist or ():
        if item != "*":
            fullname = f"{name}.{item}"
            candidates.append((fullname, sys.modules.get(fullname)))
    _patch_all(candidates)
    return m


def _import_module(name, package=None):
    """importlib.import_module does not route through builtins.__import__, so
    it needs its own hook or a submission using it receives no mutation."""
    m = _orig_import_module(name, package)
    candidates = [(getattr(m, "__name__", name), m)]
    if not str(name).startswith("."):
        candidates.append((name, sys.modules.get(name)))
    _patch_all(candidates)
    return m


def _reload(module):
    """importlib.reload re-executes the module body in the same namespace, so
    `load_galaxy_catalog` goes back to the unwrapped original while the
    `__MUTATED__` marker set on that same namespace survives -- the hook would
    then decline to re-patch and the trial would silently run against the
    correct function. Reset the marker and re-apply.

    Scoped to the module under test: an r3 review found the first version
    resetting `__MUTATED__` on *every* reloaded module, so reloading something
    unrelated left an attribute behind on it. Nothing but `data_reader` is
    touched here now."""
    m = _orig_reload(module)
    name = getattr(m, "__name__", "")
    if not _is_target(name, m):
        return m
    try:
        m.__MUTATED__ = False
    except Exception:
        return m
    _patch_all([(name, m)])
    return m


if MUT:
    if isinstance(__builtins__, dict):
        __builtins__["__import__"] = _imp
    else:
        __builtins__.__import__ = _imp
    importlib.import_module = _import_module
    importlib.reload = _reload
