"""Hidden Harness A: the two new provenance attributes, for Task 005.

Not visible to the Developer model. Copied into the trial worktree's tests/
directory at grade time and run with the trial's own pytest/venv. Scores the
"correctness" rubric category together with test_hB.py.

This file owns the criteria about what the fix *adds*: `box_size` and
`n_galaxies` present in every results file `run_calculation()` writes, with the
right value and the right stored type, across every configured redshift, under
the default config and a non-default one, on a snapshot that produces no pairs
at all, and -- for `box_size` -- on a snapshot whose catalog declares a
different box from the one the config does. test_hB.py owns everything the fix
must not have broken.

Both files drive the real `calc.run_calculation(config)` and read the written
files back with h5py. Neither calls `_save_pairs` directly: it is a private
helper, spec.md does not pin its signature, and a submission is free to
restructure it.

**The fixtures are hand-built, not generated.** Every galaxy below is placed by
hand so the expected pair count, galaxy count and raw row count are derivable
on paper. `generate_test_data.generate_all_snapshots` was deliberately not
used: NumPy does not guarantee `Generator`'s bit stream across versions, so
pinning generated counts would fail a correct submission on a legitimate numpy
upgrade (Task 003's r1 finding).

The whole import block is guarded: `calc` imports `find_pairs` and
`load_galaxy_catalog` at module scope, so a submission that broke any of them
would otherwise turn this file into a pytest collection error and take
test_hB.py's already-correct results down with it.
"""
import contextlib
import copy
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

BASE = cfgmod.config if cfgmod is not None else {}

# ==========================================================================
# The hand-built snapshots.
#
# Each snapshot is described by three counts. Galaxies occupy 1 Mpc-spaced
# "slots" so nothing pairs across slots (1000 kpc >> the 25 kpc max_sep):
#
#   n_pairs  slots holding a close pair: a primary at x and a secondary at
#            x + 0.005 Mpc (5 kpc apart), masses 9.2 and 9.0 so the pair
#            survives the default mass_ratio_min = 0.1 cut (ratio ~ 0.63).
#   n_field  slots holding one isolated in-range galaxy (mass 9.5).
#   n_out    slots holding one isolated galaxy above the default mass range
#            (mass 12.0), dropped by load_galaxy_catalog's selection.
#
# So for one snapshot:
#     raw rows in the file = 2*n_pairs + n_field + n_out
#     galaxies find_pairs sees (default mass range) = 2*n_pairs + n_field
#     pairs found = n_pairs
#
# The counts below are chosen so that, for every snapshot, all three of those
# numbers are different from each other, AND the galaxy count differs between
# snapshots. A submission that records the pair count, the raw row count, or
# one snapshot's count for all of them therefore fails rather than
# coincidentally passing.
#
#   z    n_pairs  n_field  n_out | raw  galaxies  pairs
#   2.0     3        2       2   | 10      8        3
#   3.0     2        3       1   |  8      7        2
#   4.0     4        1       3   | 12      9        4
#   5.0     0        5       2   |  7      5        0     <- zero-pair snapshot
# ==========================================================================
SNAPSHOTS = {
    2.0: {"n_pairs": 3, "n_field": 2, "n_out": 2},
    3.0: {"n_pairs": 2, "n_field": 3, "n_out": 1},
    4.0: {"n_pairs": 4, "n_field": 1, "n_out": 3},
    5.0: {"n_pairs": 0, "n_field": 5, "n_out": 2},
}
REDSHIFTS = sorted(SNAPSHOTS)
ZERO_PAIR_Z = 5.0

PAIR_MASS_PRIMARY = 9.2
PAIR_MASS_SECONDARY = 9.0
FIELD_MASS = 9.5
OUT_OF_RANGE_MASS = 12.0        # above the default log_mass_max = 11.0
PAIR_SEP_MPC = 0.005            # 5 kpc
PAIR_DV = (30.0, 40.0, 0.0)     # |dv| = 50 km/s

#: The two-sided discriminating fixture for where box_size comes from. The
#: catalog declares one box and the config another; nothing in the pipeline
#: makes them agree, and find_pairs() follows the catalog (src/pair_finder.py
#: takes its KD-tree boxsize from catalog["box_size"], which src/data_reader.py
#: read out of the input file's own attribute -- config["box_size"] is not read
#: by the pair-finding at all). Both differ from the 500.0 default, so a
#: hardcoded default fails here too. Both are integral, so M05's dtype-only
#: mutation stays applicable (see mutations/sitecustomize.py note 7).
MISMATCH_CATALOG_BOX = 10.0     # what find_pairs actually ran in
MISMATCH_CONFIG_BOX = 20.0      # what config says, and nothing reads


def raw_rows(z):
    s = SNAPSHOTS[z]
    return 2 * s["n_pairs"] + s["n_field"] + s["n_out"]


def n_galaxies_default_range(z):
    """Galaxies surviving the DEFAULT [8, 11] mass selection."""
    s = SNAPSHOTS[z]
    return 2 * s["n_pairs"] + s["n_field"]


def n_galaxies_wide_range(z):
    """Galaxies surviving a mass selection wide enough to admit the 12.0s."""
    return raw_rows(z)


def build_arrays(z, box_size):
    """Return the seven catalog arrays for one snapshot, in row order."""
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


def write_catalog(path, shape_z, box_size, file_z=None):
    """Write one input catalog.

    `shape_z` selects which row of SNAPSHOTS to build; `file_z` is the
    redshift stamped into the file, which defaults to it. The two are split so
    a snapshot's shape can be reused at a redshift the default config does not
    list.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with h5py.File(path, "w") as f:
        for key, arr in build_arrays(shape_z, box_size).items():
            f.create_dataset(key, data=arr)
        f.attrs["redshift"] = float(shape_z if file_z is None else file_z)
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
    """The stored dtype kind of an HDF5 attribute, as read back.

    h5py hands back a numpy scalar for numeric attributes and a plain str for
    string ones; np.asarray normalises both so 'f' / 'i' / 'U' can be compared
    without special-casing.
    """
    return np.asarray(value).dtype.kind


def read_attrs(path):
    with h5py.File(path, "r") as f:
        return dict(f.attrs)


@pytest.fixture(scope="module")
def default_run(tmp_path_factory):
    """One run of the real driver over the four default-config snapshots."""
    root = tmp_path_factory.mktemp("t005a_default")
    c = cfg(root, redshifts=list(REDSHIFTS))
    for z in REDSHIFTS:
        write_catalog(data_path(c, z), z, float(c["box_size"]))
    quiet(calc.run_calculation, c)
    return c, {z: read_attrs(results_path(c, z)) for z in REDSHIFTS}


@pytest.fixture(scope="module")
def nondefault_run(tmp_path_factory):
    """The same driver under a config that shares no relevant default.

    A different box (120 Mpc, not 500), a mass range wide enough to admit the
    12.0 galaxies the default range drops, and a single redshift that is not
    in the default list. A submission that hardcoded any default fails here
    and passes `default_run`.
    """
    root = tmp_path_factory.mktemp("t005a_nondefault")
    z = 7.0
    box = 120.0
    c = cfg(root, redshifts=[z], box_size=box,
            log_mass_min=8.0, log_mass_max=13.0)
    write_catalog(data_path(c, z), 4.0, box, file_z=z)   # reuse the z=4.0 shape
    quiet(calc.run_calculation, c)
    return c, z, read_attrs(results_path(c, z))


@pytest.fixture(scope="module")
def mismatched_box_run(tmp_path_factory):
    """One snapshot whose catalog declares a box size the config does not.

    The z=3.0 shape spans six 1 Mpc slots, so every galaxy sits well inside the
    catalog's 10 Mpc box and the run is a legitimate one -- the config's 20 Mpc
    is simply a number the pair-finding never consults.
    """
    root = tmp_path_factory.mktemp("t005a_mismatch")
    z = 3.0
    c = cfg(root, redshifts=[z], box_size=MISMATCH_CONFIG_BOX)
    write_catalog(data_path(c, z), z, MISMATCH_CATALOG_BOX)
    quiet(calc.run_calculation, c)
    return c, z, read_attrs(results_path(c, z))


# ==================================================================== sanity
def test_A00_pipeline_imports():
    assert calc is not None and cfgmod is not None, \
        f"the pipeline failed to import: {_IMPORT_ERR!r}"


# ================================================== the attributes exist ...
@pytest.mark.parametrize("z", REDSHIFTS)
def test_A01_results_file_written(default_run, z):
    c, _ = default_run
    assert os.path.isfile(results_path(c, z)), \
        f"no results file written for z={z}"


@pytest.mark.parametrize("z", REDSHIFTS)
def test_A02_box_size_attribute_present(default_run, z):
    _, attrs = default_run
    assert "box_size" in attrs[z], \
        f"z={z}: results file carries no 'box_size' provenance attribute"


@pytest.mark.parametrize("z", REDSHIFTS)
def test_A03_n_galaxies_attribute_present(default_run, z):
    _, attrs = default_run
    assert "n_galaxies" in attrs[z], \
        f"z={z}: results file carries no 'n_galaxies' provenance attribute"


# ==================================================== ... with the right value
@pytest.mark.parametrize("z", REDSHIFTS)
def test_A04_box_size_value(default_run, z):
    """The self-consistent case, where the catalog's box and the config's are
    the same number; test_A18 is the one that says which of them is meant."""
    c, attrs = default_run
    np.testing.assert_allclose(
        float(attrs[z]["box_size"]), float(c["box_size"]), rtol=0, atol=1e-12,
        err_msg=f"z={z}: box_size is not the snapshot's box size in Mpc")


@pytest.mark.parametrize("z", REDSHIFTS)
def test_A05_n_galaxies_value(default_run, z):
    _, attrs = default_run
    assert int(attrs[z]["n_galaxies"]) == n_galaxies_default_range(z), (
        f"z={z}: n_galaxies is {int(attrs[z]['n_galaxies'])}, expected "
        f"{n_galaxies_default_range(z)} (the post-mass-selection catalog size)")


# ==================================================== ... and the right type
@pytest.mark.parametrize("z", REDSHIFTS)
def test_A06_box_size_stored_as_float(default_run, z):
    _, attrs = default_run
    assert kind_of(attrs[z]["box_size"]) == "f", (
        f"z={z}: box_size stored with dtype kind "
        f"{kind_of(attrs[z]['box_size'])!r}, expected floating ('f')")


@pytest.mark.parametrize("z", REDSHIFTS)
def test_A07_n_galaxies_stored_as_integer(default_run, z):
    _, attrs = default_run
    assert kind_of(attrs[z]["n_galaxies"]) == "i", (
        f"z={z}: n_galaxies stored with dtype kind "
        f"{kind_of(attrs[z]['n_galaxies'])!r}, expected integer ('i')")


# ================================================ n_galaxies is not something else
@pytest.mark.parametrize("z", REDSHIFTS)
def test_A08_n_galaxies_is_not_the_pair_count(default_run, z):
    """The fixture guarantees the two differ in every snapshot."""
    _, attrs = default_run
    n_gal = int(attrs[z]["n_galaxies"])
    n_pairs = int(attrs[z]["n_pairs"]) if "n_pairs" in attrs[z] \
        else SNAPSHOTS[z]["n_pairs"]
    assert n_gal != n_pairs, \
        f"z={z}: n_galaxies equals the pair count ({n_gal}) -- it counts galaxies"
    assert n_gal != 2 * n_pairs, \
        f"z={z}: n_galaxies equals twice the pair count -- it counts the whole catalog"


@pytest.mark.parametrize("z", REDSHIFTS)
def test_A09_n_galaxies_is_not_the_raw_row_count(default_run, z):
    """Post-selection, not the number of rows in the input HDF5 file."""
    _, attrs = default_run
    assert int(attrs[z]["n_galaxies"]) != raw_rows(z), (
        f"z={z}: n_galaxies equals the input file's row count ({raw_rows(z)}); "
        f"the mass selection drops {SNAPSHOTS[z]['n_out']} galaxies before "
        f"find_pairs sees them")


def test_A10_n_galaxies_varies_per_snapshot(default_run):
    """Each redshift records its own snapshot, not the first one's."""
    _, attrs = default_run
    got = {z: int(attrs[z]["n_galaxies"]) for z in REDSHIFTS}
    want = {z: n_galaxies_default_range(z) for z in REDSHIFTS}
    assert got == want, \
        f"per-snapshot galaxy counts wrong: got {got}, expected {want}"
    assert len(set(got.values())) == len(REDSHIFTS), \
        "every snapshot recorded the same galaxy count"


# ============================================================ zero-pair snapshot
def test_A11_zero_pair_snapshot_is_written(default_run):
    c, attrs = default_run
    z = ZERO_PAIR_Z
    assert os.path.isfile(results_path(c, z)), \
        "the zero-pair snapshot produced no results file at all"
    with h5py.File(results_path(c, z), "r") as f:
        assert len(f["delta_v"][...]) == 0, \
            "the fixture's zero-pair snapshot found pairs -- bad fixture"
    assert int(attrs[z]["n_pairs"]) == 0


def test_A12_zero_pair_snapshot_carries_both_attributes(default_run):
    _, attrs = default_run
    a = attrs[ZERO_PAIR_Z]
    assert "box_size" in a and "n_galaxies" in a, (
        "the zero-pair snapshot's results file is missing a new provenance "
        f"attribute: has {sorted(a)}")


def test_A13_zero_pair_snapshot_n_galaxies_is_the_real_count(default_run):
    """n_galaxies is not zero just because n_pairs is."""
    _, attrs = default_run
    expected = n_galaxies_default_range(ZERO_PAIR_Z)
    got = int(attrs[ZERO_PAIR_Z]["n_galaxies"])
    assert got == expected, (
        f"zero-pair snapshot recorded n_galaxies={got}, expected {expected} "
        f"-- the snapshot has {expected} galaxies and no pairs")


# ========================================================== non-default config
def test_A14_box_size_follows_a_nondefault_config(nondefault_run):
    c, _z, attrs = nondefault_run
    assert "box_size" in attrs, "no box_size attribute under a non-default config"
    np.testing.assert_allclose(
        float(attrs["box_size"]), float(c["box_size"]), rtol=0, atol=1e-12,
        err_msg=f"box_size is {float(attrs['box_size'])}, expected "
                f"{float(c['box_size'])} -- a hardcoded default?")


def test_A15_n_galaxies_follows_a_nondefault_mass_range(nondefault_run):
    """The wide mass range admits galaxies the default range drops."""
    c, _z, attrs = nondefault_run
    expected = n_galaxies_wide_range(4.0)
    got = int(attrs["n_galaxies"])
    assert got == expected, (
        f"n_galaxies is {got}, expected {expected} under "
        f"log_mass_max={c['log_mass_max']} -- the count must follow the "
        f"config's mass selection, not the default one")


def test_A16_attributes_present_on_a_nondefault_redshift(nondefault_run):
    c, z, attrs = nondefault_run
    assert os.path.isfile(results_path(c, z)), \
        f"no results file for the non-default redshift z={z}"
    assert "box_size" in attrs and "n_galaxies" in attrs
    np.testing.assert_allclose(float(attrs["redshift"]), z, rtol=0, atol=1e-12)


# ============================================ box_size's source, discriminated
def test_A17_mismatch_fixture_is_discriminating(mismatched_box_run):
    """Guards the two tests below: they mean nothing unless the catalog's box,
    the config's box and the pipeline default are three different numbers."""
    c, z, _ = mismatched_box_run
    with h5py.File(data_path(c, z), "r") as f:
        catalog_box = float(f.attrs["box_size"])
    assert catalog_box == MISMATCH_CATALOG_BOX
    assert float(c["box_size"]) == MISMATCH_CONFIG_BOX
    assert len({catalog_box, float(c["box_size"]),
                float(BASE["box_size"])}) == 3, \
        "the mismatch fixture cannot tell the three candidate sources apart"


def test_A18_box_size_is_the_catalogs_not_the_configs(mismatched_box_run):
    """The value find_pairs() ran in, which is the catalog's.

    find_pairs() sets the KD-tree's periodic boundary from
    catalog["box_size"] and never reads config["box_size"], so recording the
    configured number puts a box in the file that the pairs were not found in.
    """
    _c, _z, attrs = mismatched_box_run
    assert "box_size" in attrs, \
        "no box_size attribute when catalog and config disagree"
    got = float(attrs["box_size"])
    assert got != MISMATCH_CONFIG_BOX, (
        f"box_size is {got}, the *configured* box; the pair-finding ran in the "
        f"catalog's {MISMATCH_CATALOG_BOX} Mpc box and that is what the file "
        f"must record")
    np.testing.assert_allclose(
        got, MISMATCH_CATALOG_BOX, rtol=0, atol=1e-12,
        err_msg="box_size is neither the catalog's box nor the config's")


def test_A19_mismatched_run_is_otherwise_intact(mismatched_box_run):
    """The rest of the block is unaffected by where box_size came from."""
    _c, z, attrs = mismatched_box_run
    assert kind_of(attrs["box_size"]) == "f", \
        "box_size stopped being a floating scalar under a mismatched box"
    assert int(attrs["n_galaxies"]) == n_galaxies_default_range(z), \
        "n_galaxies is wrong under a mismatched box"
    np.testing.assert_allclose(float(attrs["redshift"]), z, rtol=0, atol=1e-12)
