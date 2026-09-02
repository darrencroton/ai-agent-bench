"""Hidden Harness B: preserved behaviour, for Task 005.

Not visible to the Developer model. Copied into the trial worktree's tests/
directory at grade time and run with the trial's own pytest/venv. Scores the
"correctness" rubric category together with test_hA.py.

test_hA.py owns the criteria about what the fix *adds*. This file owns
everything spec.md says must not change: the six pre-existing provenance
attributes with their values and stored types, the seven pair datasets with
their values, `run_calculation`'s signature and its missing-input assertion,
the absence of provenance attributes nobody asked for, and the fact that
`src/plot.py` still consumes the results files it is handed.

The fixture builder is duplicated from test_hA.py rather than shared. The two
hidden-test files are copied into the trial worktree independently and must
stay standalone -- a cross-import between them would make either file's
collection depend on the other's.

The whole import block is guarded, `plot` separately from `calc`: `plot`
imports matplotlib at module scope, and a matplotlib-level failure must not
turn the rest of this file into a collection error.
"""
import contextlib
import copy
import datetime
import inspect
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import h5py
import numpy as np
import pytest

try:
    import calc
    import config as cfgmod
except Exception as e:                      # pragma: no cover
    calc = cfgmod = None
    _IMPORT_ERR = e

try:
    import plot as plotmod
except Exception as e:                      # pragma: no cover
    plotmod = None
    _PLOT_IMPORT_ERR = e

BASE = cfgmod.config if cfgmod is not None else {}

# The same hand-built snapshots as test_hA.py; see that file's header comment
# for why each count is what it is.
SNAPSHOTS = {
    2.0: {"n_pairs": 3, "n_field": 2, "n_out": 2},
    3.0: {"n_pairs": 2, "n_field": 3, "n_out": 1},
    4.0: {"n_pairs": 4, "n_field": 1, "n_out": 3},
    5.0: {"n_pairs": 0, "n_field": 5, "n_out": 2},
}
REDSHIFTS = sorted(SNAPSHOTS)

PAIR_MASS_PRIMARY = 9.2
PAIR_MASS_SECONDARY = 9.0
FIELD_MASS = 9.5
OUT_OF_RANGE_MASS = 12.0
PAIR_SEP_MPC = 0.005            # 5 kpc
PAIR_SEP_KPC = 5.0
PAIR_DV = (30.0, 40.0, 0.0)     # |dv| = 50 km/s
PAIR_DELTA_V = 50.0

#: Every pair in the fixture is identical, so one row describes them all.
#: mass bin edges are linspace(8, 11, 7) = [8, 8.5, 9, 9.5, 10, 10.5, 11], so a
#: primary of 9.2 lands in bin 2; sep bin edges are [0, 10, 15, 20, 25], so a
#: 5 kpc separation lands in bin 0.
EXPECTED_MASS_BIN = 2
EXPECTED_SEP_BIN = 0

DATASET_NAMES = ("mass_primary", "mass_secondary", "mass_ratio",
                 "separation_kpc", "delta_v", "mass_bin", "sep_bin")

#: The provenance block as it must look after the fix: the six that were
#: already there plus the two the task adds, and nothing else.
EXPECTED_ATTR_NAMES = {"redshift", "n_pairs", "timestamp", "mass_bin_by",
                       "mass_ratio_min", "max_sep_kpc",
                       "box_size", "n_galaxies"}
PRE_EXISTING_ATTR_NAMES = ("redshift", "n_pairs", "timestamp", "mass_bin_by",
                           "mass_ratio_min", "max_sep_kpc")


def build_arrays(z, box_size):
    s = SNAPSHOTS[z]
    x, y, zc, vx, vy, vz, mass = [], [], [], [], [], [], []
    slot = 1.0

    def add(px, pm, pv):
        x.append(px); y.append(0.0); zc.append(0.0)
        vx.append(pv[0]); vy.append(pv[1]); vz.append(pv[2])
        mass.append(pm)

    for _ in range(s["n_pairs"]):
        add(slot, PAIR_MASS_PRIMARY, PAIR_DV)
        add(slot + PAIR_SEP_MPC, PAIR_MASS_SECONDARY, (0.0, 0.0, 0.0))
        slot += 1.0
    for _ in range(s["n_field"]):
        add(slot, FIELD_MASS, (0.0, 0.0, 0.0))
        slot += 1.0
    for _ in range(s["n_out"]):
        add(slot, OUT_OF_RANGE_MASS, (0.0, 0.0, 0.0))
        slot += 1.0

    assert all(0.0 <= v < box_size for v in x), \
        "fixture places a galaxy outside the box"
    return {
        "x": np.array(x), "y": np.array(y), "z": np.array(zc),
        "vx": np.array(vx), "vy": np.array(vy), "vz": np.array(vz),
        "log_stellar_mass": np.array(mass),
    }


def write_catalog(path, z, box_size):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with h5py.File(path, "w") as f:
        for key, arr in build_arrays(z, box_size).items():
            f.create_dataset(key, data=arr)
        f.attrs["redshift"] = float(z)
        f.attrs["box_size"] = box_size


def cfg(root, **overrides):
    c = copy.deepcopy(BASE)
    c.update(
        data_dir=os.path.join(str(root), "data") + os.sep,
        results_dir=os.path.join(str(root), "results") + os.sep,
        figures_dir=os.path.join(str(root), "figures") + os.sep,
    )
    c.update(overrides)
    return c


def data_path(c, z):
    return os.path.join(c["data_dir"], f"test_z{z:.1f}.hdf5")


def results_path(c, z):
    return os.path.join(c["results_dir"], f"pairs_z{z:.1f}.hdf5")


def quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        return fn(*a, **k)


def kind_of(value):
    return np.asarray(value).dtype.kind


@pytest.fixture(scope="module")
def default_run(tmp_path_factory):
    """One run of the real driver over the four default-config snapshots."""
    root = tmp_path_factory.mktemp("t005b_default")
    c = cfg(root, redshifts=list(REDSHIFTS))
    for z in REDSHIFTS:
        write_catalog(data_path(c, z), z, float(c["box_size"]))
    started = datetime.datetime.now(datetime.timezone.utc)
    quiet(calc.run_calculation, c)
    finished = datetime.datetime.now(datetime.timezone.utc)
    attrs = {}
    datasets = {}
    for z in REDSHIFTS:
        with h5py.File(results_path(c, z), "r") as f:
            attrs[z] = dict(f.attrs)
            datasets[z] = {k: f[k][...] for k in f}
    return c, attrs, datasets, (started, finished)


# ==================================================================== sanity
def test_B00_pipeline_imports():
    assert calc is not None and cfgmod is not None, \
        f"the pipeline failed to import: {_IMPORT_ERR!r}"


def test_B01_plot_module_still_imports():
    """src/plot.py reads these results files and is outside the authorized
    surface; it must still be importable."""
    assert plotmod is not None, \
        f"src/plot.py failed to import: {_PLOT_IMPORT_ERR!r}"


# ============================================ the six pre-existing attributes
@pytest.mark.parametrize("z", REDSHIFTS)
@pytest.mark.parametrize("name", PRE_EXISTING_ATTR_NAMES)
def test_B02_pre_existing_attribute_present(default_run, name, z):
    _, attrs, _, _ = default_run
    assert name in attrs[z], (
        f"z={z}: the pre-existing provenance attribute {name!r} is gone; "
        f"file has {sorted(attrs[z])}")


@pytest.mark.parametrize("z", REDSHIFTS)
def test_B03_redshift_attribute_unchanged(default_run, z):
    _, attrs, _, _ = default_run
    np.testing.assert_allclose(float(attrs[z]["redshift"]), z,
                               rtol=0, atol=1e-12)
    assert kind_of(attrs[z]["redshift"]) == "f", \
        "redshift is no longer stored as a floating scalar"


@pytest.mark.parametrize("z", REDSHIFTS)
def test_B04_n_pairs_attribute_unchanged(default_run, z):
    """Still the pair count -- not quietly repurposed into the galaxy count."""
    _, attrs, datasets, _ = default_run
    expected = SNAPSHOTS[z]["n_pairs"]
    assert int(attrs[z]["n_pairs"]) == expected, (
        f"z={z}: n_pairs is {int(attrs[z]['n_pairs'])}, expected {expected}")
    assert int(attrs[z]["n_pairs"]) == len(datasets[z]["delta_v"]), \
        f"z={z}: n_pairs disagrees with the delta_v dataset it counts"
    assert kind_of(attrs[z]["n_pairs"]) == "i", \
        "n_pairs is no longer stored as an integer scalar"


@pytest.mark.parametrize("z", REDSHIFTS)
def test_B05_timestamp_attribute_unchanged(default_run, z):
    """Bracketed on both sides: a lower bound alone would accept an arbitrarily
    future stamp, which is as wrong as an arbitrarily old one and just as much
    a sign the attribute is no longer "when this file was written"."""
    _, attrs, _, (started, finished) = default_run
    raw = attrs[z]["timestamp"]
    assert isinstance(raw, str), \
        f"z={z}: timestamp is stored as {type(raw).__name__}, expected a string"
    stamp = datetime.datetime.fromisoformat(raw)
    assert stamp.tzinfo is not None, "timestamp lost its UTC offset"
    slack = datetime.timedelta(seconds=5)
    assert started - slack <= stamp <= finished + slack, (
        f"z={z}: timestamp {stamp.isoformat()} is outside the run that wrote "
        f"it ({started.isoformat()} .. {finished.isoformat()})")


@pytest.mark.parametrize("z", REDSHIFTS)
def test_B06_mass_bin_by_attribute_unchanged(default_run, z):
    c, attrs, _, _ = default_run
    assert attrs[z]["mass_bin_by"] == c["mass_bin_by"]
    assert kind_of(attrs[z]["mass_bin_by"]) == "U", \
        "mass_bin_by is no longer stored as a string"


@pytest.mark.parametrize("z", REDSHIFTS)
def test_B07_mass_ratio_min_attribute_unchanged(default_run, z):
    c, attrs, _, _ = default_run
    np.testing.assert_allclose(float(attrs[z]["mass_ratio_min"]),
                               float(c["mass_ratio_min"]), rtol=0, atol=1e-12)
    assert kind_of(attrs[z]["mass_ratio_min"]) == "f"


@pytest.mark.parametrize("z", REDSHIFTS)
def test_B08_max_sep_kpc_attribute_unchanged(default_run, z):
    """Still named max_sep_kpc, still config['max_sep'], still in kpc."""
    c, attrs, _, _ = default_run
    np.testing.assert_allclose(float(attrs[z]["max_sep_kpc"]),
                               float(c["max_sep"]), rtol=0, atol=1e-12)
    assert kind_of(attrs[z]["max_sep_kpc"]) == "f"


@pytest.mark.parametrize("z", REDSHIFTS)
def test_B09_no_unrequested_provenance_attributes(default_run, z):
    """Exactly two attributes were added, per spec.md's Explicit Non-Goals."""
    _, attrs, _, _ = default_run
    extra = set(attrs[z]) - EXPECTED_ATTR_NAMES
    assert not extra, \
        f"z={z}: results file carries provenance attributes nobody asked for: {sorted(extra)}"


# ======================================================= the seven datasets
@pytest.mark.parametrize("z", REDSHIFTS)
def test_B10_all_datasets_present_with_the_right_length(default_run, z):
    _, _, datasets, _ = default_run
    assert set(datasets[z]) == set(DATASET_NAMES), (
        f"z={z}: dataset names changed: {sorted(datasets[z])}")
    expected = SNAPSHOTS[z]["n_pairs"]
    for name in DATASET_NAMES:
        assert len(datasets[z][name]) == expected, \
            f"z={z}: dataset {name!r} has {len(datasets[z][name])} rows, expected {expected}"


@pytest.mark.parametrize("z", [z for z in REDSHIFTS if SNAPSHOTS[z]["n_pairs"]])
def test_B11_dataset_values_unchanged(default_run, z):
    """The science must not move: every fixture pair is identical by
    construction, so each column is pinned to one analytic value."""
    _, _, datasets, _ = default_run
    d = datasets[z]
    np.testing.assert_allclose(d["mass_primary"], PAIR_MASS_PRIMARY,
                               rtol=0, atol=1e-12, err_msg="mass_primary")
    np.testing.assert_allclose(d["mass_secondary"], PAIR_MASS_SECONDARY,
                               rtol=0, atol=1e-12, err_msg="mass_secondary")
    np.testing.assert_allclose(
        d["mass_ratio"], 10.0 ** (PAIR_MASS_SECONDARY - PAIR_MASS_PRIMARY),
        rtol=1e-12, atol=0, err_msg="mass_ratio")
    np.testing.assert_allclose(d["separation_kpc"], PAIR_SEP_KPC,
                               rtol=0, atol=1e-6, err_msg="separation_kpc")
    np.testing.assert_allclose(d["delta_v"], PAIR_DELTA_V,
                               rtol=1e-12, atol=0, err_msg="delta_v")
    np.testing.assert_array_equal(d["mass_bin"],
                                  np.full(len(d["mass_bin"]), EXPECTED_MASS_BIN))
    np.testing.assert_array_equal(d["sep_bin"],
                                  np.full(len(d["sep_bin"]), EXPECTED_SEP_BIN))


@pytest.mark.parametrize("z", REDSHIFTS)
def test_B12_dataset_dtypes_unchanged(default_run, z):
    _, _, datasets, _ = default_run
    for name in ("mass_primary", "mass_secondary", "mass_ratio",
                 "separation_kpc", "delta_v"):
        assert datasets[z][name].dtype.kind == "f", \
            f"z={z}: dataset {name!r} is no longer floating"
    for name in ("mass_bin", "sep_bin"):
        assert datasets[z][name].dtype.kind == "i", \
            f"z={z}: dataset {name!r} is no longer integral"


# ================================================= the driver's own contract
def test_B13_run_calculation_takes_one_positional_parameter():
    """The new values are threaded internally, not bolted onto the public
    signature: pipeline.py calls run_calculation(config) and is frozen.

    The whole parameter list is asserted, not just the required-positional
    subset of it. Counting only required positionals accepts
    `run_calculation(config, n_galaxies=None)` and `run_calculation(config,
    *args)` alike, neither of which is "still exactly one positional
    parameter".
    """
    sig = inspect.signature(calc.run_calculation)
    params = list(sig.parameters.values())
    assert len(params) == 1, \
        f"run_calculation takes {len(params)} parameters, expected 1: {sig}"
    only = params[0]
    assert only.kind is only.POSITIONAL_OR_KEYWORD, (
        f"run_calculation's one parameter is {only.kind.description}, expected "
        f"an ordinary positional-or-keyword parameter: {sig}")
    assert only.default is only.empty, \
        f"run_calculation's config parameter gained a default: {sig}"


def test_B14_missing_input_file_still_asserts(tmp_path):
    """The pre-existing fail-loud guard on a missing input catalog."""
    c = cfg(tmp_path, redshifts=[2.0])
    os.makedirs(c["data_dir"], exist_ok=True)
    with pytest.raises(AssertionError, match="Data file not found"):
        quiet(calc.run_calculation, c)


def test_B15_results_filenames_unchanged(default_run):
    c, _, _, _ = default_run
    written = sorted(os.listdir(c["results_dir"]))
    expected = sorted(f"pairs_z{z:.1f}.hdf5" for z in REDSHIFTS)
    assert written == expected, \
        f"results directory holds {written}, expected {expected}"


# ============================================== downstream still consumes them
def test_B16_plot_loads_the_results(default_run):
    c, _, datasets, _ = default_run
    loaded = plotmod._load_all_results(c)
    assert sorted(loaded) == sorted(REDSHIFTS)
    for z in REDSHIFTS:
        for name in ("delta_v", "mass_bin", "sep_bin"):
            np.testing.assert_array_equal(
                loaded[z][name], datasets[z][name],
                err_msg=f"z={z}: plot.py read back a different {name}")


@pytest.mark.filterwarnings("ignore:No artists with labels found:UserWarning")
def test_B17_plot_runs_end_to_end(default_run):
    """A full make_plots pass over the results this run produced.

    The warning filter covers matplotlib's "no artists with labels" notice,
    raised by the frozen src/plot.py for the mass bins this small fixture
    leaves empty. It is baseline behaviour, not something a submission can
    change from inside the authorized surface.
    """
    c, _, _, _ = default_run
    quiet(plotmod.make_plots, c, validation_mode=False)
    figures = sorted(os.listdir(c["figures_dir"]))
    expected = sorted(["vrel_by_mass.png"]
                      + [f"vrel_by_sep_z{z:.1f}.png" for z in REDSHIFTS])
    assert figures == expected, \
        f"plot.py wrote {figures}, expected {expected}"
