"""
Provenance metadata written by calc.run_calculation().

Each results file must be self-describing: alongside the pair catalog it holds,
it records the redshift, the pair count, the galaxy count that went into the
pair-finding, the box the pair-finding ran in, and the selection parameters the
run used. These tests drive the real driver against hand-built input catalogs
and read the written files back, because the file is the contract -- not any
particular internal helper.

Two of those values have more than one plausible source, so each has a fixture
that tells the sources apart: n_galaxies is the post-selection catalog size and
not the input file's row count or anything derived from the pair count, and
box_size is the box the *catalog* declares -- the one find_pairs() wrapped its
KD-tree in -- and not config["box_size"], which the pair-finding never reads.

The fixture catalogs are built by hand rather than generated, so every expected
count is derivable on paper: see SNAPSHOTS below.
"""

import contextlib
import copy
import datetime
import inspect
import io
import os
import sys

import h5py
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import calc
from config import config as BASE_CONFIG
from plot import _load_all_results

# ---------------------------------------------------------------------------
# The hand-built snapshots.
#
# Galaxies sit in 1 Mpc-spaced slots, so nothing pairs across slots (1000 kpc
# is far outside the 25 kpc max_sep). Each snapshot is described by three
# counts:
#
#   n_pairs  slots holding a close pair -- a primary at x and a secondary at
#            x + 5 kpc, masses 9.2 and 9.0 so the pair clears the default
#            mass_ratio_min = 0.1 cut.
#   n_field  slots holding one isolated galaxy inside the mass range.
#   n_out    slots holding one isolated galaxy above the default mass range,
#            dropped by load_galaxy_catalog's selection before find_pairs runs.
#
# so that, per snapshot:
#
#   rows in the input file  = 2*n_pairs + n_field + n_out
#   galaxies find_pairs saw = 2*n_pairs + n_field       <- what n_galaxies is
#   pairs found             = n_pairs
#
# The counts are chosen so those three numbers differ from each other in every
# snapshot, and so the galaxy count differs between snapshots. Both matter: a
# fixture where any two coincide cannot tell a correct implementation from one
# that recorded the wrong quantity.
# ---------------------------------------------------------------------------
SNAPSHOTS = {
    2.0: {"n_pairs": 3, "n_field": 2, "n_out": 2},  # 10 rows, 8 galaxies, 3 pairs
    3.0: {"n_pairs": 2, "n_field": 3, "n_out": 1},  #  8 rows, 7 galaxies, 2 pairs
    4.0: {"n_pairs": 4, "n_field": 1, "n_out": 3},  # 12 rows, 9 galaxies, 4 pairs
    5.0: {"n_pairs": 0, "n_field": 5, "n_out": 2},  #  7 rows, 5 galaxies, 0 pairs
}
REDSHIFTS = sorted(SNAPSHOTS)
ZERO_PAIR_Z = 5.0

PAIR_MASS_PRIMARY = 9.2
PAIR_MASS_SECONDARY = 9.0
FIELD_MASS = 9.5
OUT_OF_RANGE_MASS = 12.0        # above the default log_mass_max of 11.0
PAIR_SEP_MPC = 0.005            # 5 kpc
PAIR_SEP_KPC = 5.0
PAIR_VELOCITY = (30.0, 40.0, 0.0)
PAIR_DELTA_V = 50.0             # |(30, 40, 0)|

#: Every fixture pair is identical, so the two integer columns have one known
#: value each. Mass bin edges are linspace(8, 11, 7) = [8, 8.5, ..., 11], so a
#: 9.2 primary lands in bin 2; separation bin edges are [0, 10, 15, 20, 25], so
#: a 5 kpc separation lands in bin 0. The two differ, which is what lets a test
#: tell the columns apart.
EXPECTED_MASS_BIN = 2
EXPECTED_SEP_BIN = 0

#: A catalog whose declared box size is not the configured one. find_pairs()
#: takes the KD-tree's periodic box from catalog["box_size"] and never reads
#: config["box_size"], and nothing makes the two agree, so this is the fixture
#: that says which of them the results file is supposed to record. Both differ
#: from the 500.0 default, and both are integral so a dtype check stays
#: meaningful.
MISMATCH_CATALOG_BOX = 10.0     # what the pair-finding actually ran in
MISMATCH_CONFIG_BOX = 20.0      # what config says, and nothing reads

DATASET_NAMES = ("mass_primary", "mass_secondary", "mass_ratio",
                 "separation_kpc", "delta_v", "mass_bin", "sep_bin")
PRE_EXISTING_ATTRS = ("redshift", "n_pairs", "timestamp", "mass_bin_by",
                      "mass_ratio_min", "max_sep_kpc")
NEW_ATTRS = ("box_size", "n_galaxies")


# --------------------------------------------------------------- fixture helpers
def input_rows(z):
    """Rows written to the input catalog for snapshot z."""
    s = SNAPSHOTS[z]
    return 2 * s["n_pairs"] + s["n_field"] + s["n_out"]


def selected_galaxies(z, admit_out_of_range=False):
    """Galaxies find_pairs receives for snapshot z, under a mass range that
    either drops the 12.0 galaxies (the default) or admits them."""
    s = SNAPSHOTS[z]
    kept = 2 * s["n_pairs"] + s["n_field"]
    return kept + s["n_out"] if admit_out_of_range else kept


def build_arrays(z, box_size):
    """The seven catalog arrays for one snapshot."""
    s = SNAPSHOTS[z]
    columns = {k: [] for k in
               ("x", "y", "z", "vx", "vy", "vz", "log_stellar_mass")}
    slot = 1.0

    def add(x, log_mass, velocity):
        columns["x"].append(x)
        columns["y"].append(0.0)
        columns["z"].append(0.0)
        columns["vx"].append(velocity[0])
        columns["vy"].append(velocity[1])
        columns["vz"].append(velocity[2])
        columns["log_stellar_mass"].append(log_mass)

    for _ in range(s["n_pairs"]):
        add(slot, PAIR_MASS_PRIMARY, PAIR_VELOCITY)
        add(slot + PAIR_SEP_MPC, PAIR_MASS_SECONDARY, (0.0, 0.0, 0.0))
        slot += 1.0
    for _ in range(s["n_field"]):
        add(slot, FIELD_MASS, (0.0, 0.0, 0.0))
        slot += 1.0
    for _ in range(s["n_out"]):
        add(slot, OUT_OF_RANGE_MASS, (0.0, 0.0, 0.0))
        slot += 1.0

    assert all(0.0 <= x < box_size for x in columns["x"]), \
        "fixture places a galaxy outside the box"
    return {k: np.array(v) for k, v in columns.items()}


def write_catalog(path, shape_z, box_size, file_z=None):
    """Write one input catalog in generate_test_data.py's format.

    `shape_z` picks the SNAPSHOTS row to build; `file_z` is the redshift
    stamped into the file, defaulting to it, so a shape can be reused at a
    redshift the default config does not list.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with h5py.File(path, "w") as f:
        for name, array in build_arrays(shape_z, box_size).items():
            f.create_dataset(name, data=array)
        f.attrs["redshift"] = float(shape_z if file_z is None else file_z)
        f.attrs["box_size"] = float(box_size)


def make_config(root, **overrides):
    """A copy of the pipeline config pointed at a throwaway directory."""
    cfg = copy.deepcopy(BASE_CONFIG)
    cfg.update(
        data_dir=os.path.join(str(root), "data") + os.sep,
        results_dir=os.path.join(str(root), "results") + os.sep,
        figures_dir=os.path.join(str(root), "figures") + os.sep,
    )
    cfg.update(overrides)
    return cfg


def results_path(cfg, z):
    return os.path.join(cfg["results_dir"], f"pairs_z{z:.1f}.hdf5")


def data_path(cfg, z):
    return os.path.join(cfg["data_dir"], f"test_z{z:.1f}.hdf5")


def run_quietly(fn, *args, **kwargs):
    """Run a chatty pipeline stage without its progress output."""
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*args, **kwargs)


def stored_kind(value):
    """The dtype kind of an HDF5 attribute as read back.

    h5py returns a numpy scalar for numeric attributes and a plain str for
    string ones; np.asarray normalises both.
    """
    return np.asarray(value).dtype.kind


def read_results(path):
    with h5py.File(path, "r") as f:
        return dict(f.attrs), {name: f[name][...] for name in f}


# ------------------------------------------------------------------- fixtures
@pytest.fixture(scope="module")
def default_run(tmp_path_factory):
    """One driver run over the four default-config snapshots."""
    root = tmp_path_factory.mktemp("provenance_default")
    cfg = make_config(root, redshifts=list(REDSHIFTS))
    for z in REDSHIFTS:
        write_catalog(data_path(cfg, z), z, float(cfg["box_size"]))
    started = datetime.datetime.now(datetime.timezone.utc)
    run_quietly(calc.run_calculation, cfg)
    finished = datetime.datetime.now(datetime.timezone.utc)
    files = {z: read_results(results_path(cfg, z)) for z in REDSHIFTS}
    return cfg, files, (started, finished)


@pytest.fixture(scope="module")
def nondefault_run(tmp_path_factory):
    """The same driver under a config sharing none of the relevant defaults.

    A 120 Mpc box instead of 500, a mass range wide enough to admit the 12.0
    galaxies the default range drops, and a redshift the default list does not
    contain. Anything hardcoded to a default fails here and passes above.
    """
    root = tmp_path_factory.mktemp("provenance_nondefault")
    z, box_size = 7.0, 120.0
    cfg = make_config(root, redshifts=[z], box_size=box_size,
                      log_mass_min=8.0, log_mass_max=13.0)
    write_catalog(data_path(cfg, z), 4.0, box_size, file_z=z)
    run_quietly(calc.run_calculation, cfg)
    return cfg, z, read_results(results_path(cfg, z))


@pytest.fixture(scope="module")
def mismatched_box_run(tmp_path_factory):
    """A snapshot whose catalog declares a box size the config does not.

    The z=3.0 shape spans six 1 Mpc slots, so every galaxy sits well inside the
    catalog's 10 Mpc box: this is a legitimate run, and the config's 20 Mpc is
    simply a number the pair-finding never consults.
    """
    root = tmp_path_factory.mktemp("provenance_mismatch")
    z = 3.0
    cfg = make_config(root, redshifts=[z], box_size=MISMATCH_CONFIG_BOX)
    write_catalog(data_path(cfg, z), z, MISMATCH_CATALOG_BOX)
    run_quietly(calc.run_calculation, cfg)
    return cfg, z, read_results(results_path(cfg, z))


# ================================================================ box_size
@pytest.mark.parametrize("z", REDSHIFTS)
def test_box_size_is_recorded(default_run, z):
    _, files, _ = default_run
    attrs, _ = files[z]
    assert "box_size" in attrs, \
        f"z={z}: no box_size in the results file's provenance block"


@pytest.mark.parametrize("z", REDSHIFTS)
def test_box_size_is_the_snapshots_box_in_mpc(default_run, z):
    """The self-consistent case: the catalog's box and the config's agree, so
    this pins the number without saying where it came from. The mismatch tests
    below say where it came from."""
    cfg, files, _ = default_run
    attrs, _ = files[z]
    np.testing.assert_allclose(
        float(attrs["box_size"]), float(cfg["box_size"]), rtol=0, atol=1e-12,
        err_msg=f"z={z}: box_size is not the snapshot's box size in Mpc")


@pytest.mark.parametrize("z", REDSHIFTS)
def test_box_size_is_stored_as_a_float(default_run, z):
    _, files, _ = default_run
    attrs, _ = files[z]
    assert stored_kind(attrs["box_size"]) == "f", (
        f"z={z}: box_size stored with dtype kind "
        f"{stored_kind(attrs['box_size'])!r}, expected floating")


def test_box_size_follows_a_nondefault_config(nondefault_run):
    """Not the 500 Mpc default, and not the input catalog's own guess."""
    cfg, _, (attrs, _) = nondefault_run
    np.testing.assert_allclose(
        float(attrs["box_size"]), float(cfg["box_size"]), rtol=0, atol=1e-12,
        err_msg="box_size ignores a non-default config")
    assert float(attrs["box_size"]) != float(BASE_CONFIG["box_size"]), \
        "box_size looks hardcoded to the pipeline default"


def test_mismatched_box_fixture_is_discriminating(mismatched_box_run):
    """Guards the test below: it means nothing unless the catalog's box, the
    config's box and the pipeline default are three different numbers."""
    cfg, z, _ = mismatched_box_run
    with h5py.File(data_path(cfg, z), "r") as f:
        catalog_box = float(f.attrs["box_size"])
    assert catalog_box == MISMATCH_CATALOG_BOX
    assert float(cfg["box_size"]) == MISMATCH_CONFIG_BOX
    assert len({catalog_box, float(cfg["box_size"]),
                float(BASE_CONFIG["box_size"])}) == 3, \
        "the mismatch fixture cannot tell the three candidate sources apart"


def test_box_size_is_the_catalogs_not_the_configs(mismatched_box_run):
    """Where the two disagree, the file records the box the pairs were found
    in -- find_pairs() takes its periodic boundary from catalog['box_size']
    and never reads config['box_size'] at all."""
    _cfg, _z, (attrs, _) = mismatched_box_run
    recorded = float(attrs["box_size"])
    assert recorded != MISMATCH_CONFIG_BOX, (
        f"box_size is {recorded}, the configured box; the pair-finding ran in "
        f"the catalog's {MISMATCH_CATALOG_BOX} Mpc box")
    np.testing.assert_allclose(recorded, MISMATCH_CATALOG_BOX,
                               rtol=0, atol=1e-12)
    assert stored_kind(attrs["box_size"]) == "f"


def test_mismatched_box_run_is_otherwise_intact(mismatched_box_run):
    """Nothing else in the block depends on where box_size came from."""
    _cfg, z, (attrs, _) = mismatched_box_run
    assert int(attrs["n_galaxies"]) == selected_galaxies(z)
    np.testing.assert_allclose(float(attrs["redshift"]), z, rtol=0, atol=1e-12)


# ============================================================== n_galaxies
@pytest.mark.parametrize("z", REDSHIFTS)
def test_n_galaxies_is_recorded(default_run, z):
    _, files, _ = default_run
    attrs, _ = files[z]
    assert "n_galaxies" in attrs, \
        f"z={z}: no n_galaxies in the results file's provenance block"


@pytest.mark.parametrize("z", REDSHIFTS)
def test_n_galaxies_counts_the_selected_catalog(default_run, z):
    """The catalog as find_pairs received it: after the mass selection."""
    _, files, _ = default_run
    attrs, _ = files[z]
    expected = selected_galaxies(z)
    assert int(attrs["n_galaxies"]) == expected, (
        f"z={z}: n_galaxies is {int(attrs['n_galaxies'])}, expected {expected}")


@pytest.mark.parametrize("z", REDSHIFTS)
def test_n_galaxies_is_stored_as_an_integer(default_run, z):
    _, files, _ = default_run
    attrs, _ = files[z]
    assert stored_kind(attrs["n_galaxies"]) == "i", (
        f"z={z}: n_galaxies stored with dtype kind "
        f"{stored_kind(attrs['n_galaxies'])!r}, expected integer")


@pytest.mark.parametrize("z", REDSHIFTS)
def test_n_galaxies_is_not_the_input_row_count(default_run, z):
    """The mass selection drops galaxies before find_pairs sees them."""
    _, files, _ = default_run
    attrs, _ = files[z]
    assert int(attrs["n_galaxies"]) != input_rows(z), (
        f"z={z}: n_galaxies equals the input file's {input_rows(z)} rows; the "
        f"{SNAPSHOTS[z]['n_out']} out-of-range galaxies should not be counted")


@pytest.mark.parametrize("z", REDSHIFTS)
def test_n_galaxies_is_not_derived_from_the_pair_count(default_run, z):
    _, files, _ = default_run
    attrs, _ = files[z]
    n_galaxies = int(attrs["n_galaxies"])
    n_pairs = SNAPSHOTS[z]["n_pairs"]
    assert n_galaxies != n_pairs, f"z={z}: n_galaxies equals the pair count"
    assert n_galaxies != 2 * n_pairs, \
        f"z={z}: n_galaxies counts only the galaxies that ended up in a pair"


def test_n_galaxies_is_per_snapshot(default_run):
    """Each redshift records its own count, not the first snapshot's."""
    _, files, _ = default_run
    recorded = {z: int(files[z][0]["n_galaxies"]) for z in REDSHIFTS}
    assert recorded == {z: selected_galaxies(z) for z in REDSHIFTS}
    assert len(set(recorded.values())) == len(REDSHIFTS), \
        f"snapshots share a galaxy count: {recorded}"


def test_n_galaxies_follows_a_nondefault_mass_range(nondefault_run):
    """A wider mass range admits galaxies the default range drops."""
    _, _, (attrs, _) = nondefault_run
    expected = selected_galaxies(4.0, admit_out_of_range=True)
    assert int(attrs["n_galaxies"]) == expected, (
        f"n_galaxies is {int(attrs['n_galaxies'])}, expected {expected} under "
        f"the widened mass range")


# ====================================================== the zero-pair snapshot
def test_zero_pair_snapshot_still_writes_a_results_file(default_run):
    cfg, files, _ = default_run
    assert os.path.isfile(results_path(cfg, ZERO_PAIR_Z))
    _, datasets = files[ZERO_PAIR_Z]
    assert len(datasets["delta_v"]) == 0, \
        "the zero-pair snapshot found pairs -- bad fixture"


def test_zero_pair_snapshot_carries_both_new_attributes(default_run):
    _, files, _ = default_run
    attrs, _ = files[ZERO_PAIR_Z]
    missing = [name for name in NEW_ATTRS if name not in attrs]
    assert not missing, f"zero-pair snapshot is missing {missing}"


def test_zero_pair_snapshot_records_its_real_galaxy_count(default_run):
    """n_galaxies is not zero just because n_pairs is."""
    _, files, _ = default_run
    attrs, _ = files[ZERO_PAIR_Z]
    expected = selected_galaxies(ZERO_PAIR_Z)
    assert int(attrs["n_galaxies"]) == expected, (
        f"zero-pair snapshot recorded n_galaxies={int(attrs['n_galaxies'])}, "
        f"expected {expected}")


# ============================================ the pre-existing provenance block
@pytest.mark.parametrize("name", PRE_EXISTING_ATTRS)
@pytest.mark.parametrize("z", REDSHIFTS)
def test_pre_existing_attribute_survives(default_run, z, name):
    _, files, _ = default_run
    attrs, _ = files[z]
    assert name in attrs, \
        f"z={z}: the pre-existing attribute {name!r} was lost; file has {sorted(attrs)}"


@pytest.mark.parametrize("z", REDSHIFTS)
def test_redshift_attribute_unchanged(default_run, z):
    _, files, _ = default_run
    attrs, _ = files[z]
    np.testing.assert_allclose(float(attrs["redshift"]), z, rtol=0, atol=1e-12)
    assert stored_kind(attrs["redshift"]) == "f"


@pytest.mark.parametrize("z", REDSHIFTS)
def test_n_pairs_still_counts_pairs(default_run, z):
    """Not quietly repurposed into the galaxy count."""
    _, files, _ = default_run
    attrs, datasets = files[z]
    assert int(attrs["n_pairs"]) == SNAPSHOTS[z]["n_pairs"]
    assert int(attrs["n_pairs"]) == len(datasets["delta_v"])
    assert stored_kind(attrs["n_pairs"]) == "i"


@pytest.mark.parametrize("z", REDSHIFTS)
def test_timestamp_attribute_unchanged(default_run, z):
    """Bracketed on both sides: a lower bound alone accepts an arbitrarily
    future stamp, which says just as little about when the file was written."""
    _, files, (started, finished) = default_run
    attrs, _ = files[z]
    raw = attrs["timestamp"]
    assert isinstance(raw, str), \
        f"z={z}: timestamp is stored as {type(raw).__name__}, expected text"
    stamp = datetime.datetime.fromisoformat(raw)
    assert stamp.tzinfo is not None, "timestamp lost its UTC offset"
    slack = datetime.timedelta(seconds=5)
    assert started - slack <= stamp <= finished + slack, (
        f"z={z}: timestamp {stamp.isoformat()} falls outside the run that "
        f"wrote it ({started.isoformat()} .. {finished.isoformat()})")


@pytest.mark.parametrize("z", REDSHIFTS)
def test_selection_attributes_unchanged(default_run, z):
    cfg, files, _ = default_run
    attrs, _ = files[z]
    assert attrs["mass_bin_by"] == cfg["mass_bin_by"]
    np.testing.assert_allclose(float(attrs["mass_ratio_min"]),
                               float(cfg["mass_ratio_min"]), rtol=0, atol=1e-12)
    np.testing.assert_allclose(float(attrs["max_sep_kpc"]),
                               float(cfg["max_sep"]), rtol=0, atol=1e-12)


@pytest.mark.parametrize("z", REDSHIFTS)
def test_selection_attribute_stored_types_unchanged(default_run, z):
    """spec.md pins the stored type of all six pre-existing attributes, not
    only of the two that already had a type check here. Separate from the
    value test above because a value read through float() or == survives a
    stored-type change that this does not."""
    _, files, _ = default_run
    attrs, _ = files[z]
    assert stored_kind(attrs["mass_bin_by"]) == "U", (
        f"z={z}: mass_bin_by stored with dtype kind "
        f"{stored_kind(attrs['mass_bin_by'])!r}, expected text")
    assert stored_kind(attrs["mass_ratio_min"]) == "f", (
        f"z={z}: mass_ratio_min stored with dtype kind "
        f"{stored_kind(attrs['mass_ratio_min'])!r}, expected floating")
    assert stored_kind(attrs["max_sep_kpc"]) == "f", (
        f"z={z}: max_sep_kpc stored with dtype kind "
        f"{stored_kind(attrs['max_sep_kpc'])!r}, expected floating")


@pytest.mark.parametrize("z", REDSHIFTS)
def test_no_unrequested_attributes(default_run, z):
    _, files, _ = default_run
    attrs, _ = files[z]
    extra = set(attrs) - set(PRE_EXISTING_ATTRS) - set(NEW_ATTRS)
    assert not extra, f"z={z}: unexpected provenance attributes {sorted(extra)}"


# =================================================== the pair catalog itself
@pytest.mark.parametrize("z", REDSHIFTS)
def test_all_datasets_present_with_the_right_length(default_run, z):
    _, files, _ = default_run
    _, datasets = files[z]
    assert set(datasets) == set(DATASET_NAMES), \
        f"z={z}: dataset names changed: {sorted(datasets)}"
    for name in DATASET_NAMES:
        assert len(datasets[name]) == SNAPSHOTS[z]["n_pairs"], \
            f"z={z}: dataset {name!r} has the wrong length"


@pytest.mark.parametrize("z", [z for z in REDSHIFTS if SNAPSHOTS[z]["n_pairs"]])
def test_pair_values_unchanged(default_run, z):
    """Every fixture pair is identical, so each column has one known value."""
    _, files, _ = default_run
    _, datasets = files[z]
    np.testing.assert_allclose(datasets["mass_primary"], PAIR_MASS_PRIMARY,
                               rtol=0, atol=1e-12)
    np.testing.assert_allclose(datasets["mass_secondary"], PAIR_MASS_SECONDARY,
                               rtol=0, atol=1e-12)
    np.testing.assert_allclose(
        datasets["mass_ratio"],
        10.0 ** (PAIR_MASS_SECONDARY - PAIR_MASS_PRIMARY), rtol=1e-12, atol=0)
    np.testing.assert_allclose(datasets["separation_kpc"], PAIR_SEP_KPC,
                               rtol=0, atol=1e-6)
    np.testing.assert_allclose(datasets["delta_v"], PAIR_DELTA_V,
                               rtol=1e-12, atol=0)


@pytest.mark.parametrize("z", [z for z in REDSHIFTS if SNAPSHOTS[z]["n_pairs"]])
def test_bin_columns_unchanged(default_run, z):
    """The two integer columns, pinned by value and kept apart from each other.

    They are the datasets a length-and-presence check cannot speak for: both
    are integral and the same length, so nothing but their values distinguishes
    mass_bin from sep_bin, or either from a wrong bin assignment.
    """
    _, files, _ = default_run
    _, datasets = files[z]
    np.testing.assert_array_equal(
        datasets["mass_bin"],
        np.full(len(datasets["mass_bin"]), EXPECTED_MASS_BIN),
        err_msg=f"z={z}: mass_bin is not the bin a {PAIR_MASS_PRIMARY} primary "
                f"falls in")
    np.testing.assert_array_equal(
        datasets["sep_bin"],
        np.full(len(datasets["sep_bin"]), EXPECTED_SEP_BIN),
        err_msg=f"z={z}: sep_bin is not the bin a {PAIR_SEP_KPC} kpc "
                f"separation falls in")


@pytest.mark.parametrize("z", REDSHIFTS)
def test_dataset_stored_types_unchanged(default_run, z):
    _, files, _ = default_run
    _, datasets = files[z]
    for name in ("mass_primary", "mass_secondary", "mass_ratio",
                 "separation_kpc", "delta_v"):
        assert datasets[name].dtype.kind == "f", \
            f"z={z}: dataset {name!r} is no longer floating"
    for name in ("mass_bin", "sep_bin"):
        assert datasets[name].dtype.kind == "i", \
            f"z={z}: dataset {name!r} is no longer integral"


# ============================================================ driver contract
def test_run_calculation_still_takes_exactly_one_parameter():
    """pipeline.py calls run_calculation(config) and is frozen, so the new
    values are threaded internally rather than added to the signature.

    The whole parameter list is asserted, not just the required-positional
    subset: counting only required positionals accepts
    `run_calculation(config, n_galaxies=None)` and `run_calculation(config,
    *args)` alike, and neither is "exactly one positional parameter".
    """
    sig = inspect.signature(calc.run_calculation)
    params = list(sig.parameters.values())
    assert len(params) == 1, \
        f"run_calculation takes {len(params)} parameters, expected 1: {sig}"
    only = params[0]
    assert only.kind is only.POSITIONAL_OR_KEYWORD, (
        f"run_calculation's parameter is {only.kind.description}, expected an "
        f"ordinary positional-or-keyword parameter: {sig}")
    assert only.default is only.empty, \
        f"run_calculation's config parameter gained a default: {sig}"


def test_results_filenames_unchanged(default_run):
    cfg, _, _ = default_run
    assert sorted(os.listdir(cfg["results_dir"])) == \
        sorted(f"pairs_z{z:.1f}.hdf5" for z in REDSHIFTS)


def test_missing_input_catalog_still_asserts(tmp_path):
    cfg = make_config(tmp_path, redshifts=[2.0])
    os.makedirs(cfg["data_dir"], exist_ok=True)
    with pytest.raises(AssertionError, match="Data file not found"):
        run_quietly(calc.run_calculation, cfg)


def test_results_are_still_readable_by_plot(default_run):
    """The downstream consumer of these files is unaffected by the new
    provenance block."""
    cfg, files, _ = default_run
    loaded = _load_all_results(cfg)
    assert sorted(loaded) == sorted(REDSHIFTS)
    for z in REDSHIFTS:
        np.testing.assert_array_equal(loaded[z]["delta_v"],
                                      files[z][1]["delta_v"])


def test_pair_finding_efficiency_is_derivable_from_the_file_alone(default_run):
    """The motivating use case: n_pairs / n_galaxies, with no other input."""
    _, files, _ = default_run
    for z in REDSHIFTS:
        attrs, _ = files[z]
        efficiency = int(attrs["n_pairs"]) / int(attrs["n_galaxies"])
        expected = SNAPSHOTS[z]["n_pairs"] / selected_galaxies(z)
        assert efficiency == pytest.approx(expected), \
            f"z={z}: efficiency derived from the file is wrong"
