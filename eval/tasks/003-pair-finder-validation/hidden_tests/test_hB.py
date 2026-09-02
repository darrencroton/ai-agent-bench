"""Hidden Harness B: integration criteria for Task 003.

Not visible to the Developer model. Copied into the trial worktree's tests/
directory at grade time and run with the trial's own pytest/venv. Scores the
"correctness" rubric category together with test_hA.py.

test_hA.py calls find_pairs() directly. This file only ever reaches it through
the real driver (`calc.run_calculation`) and a real catalog on disk, so it
answers a different question: is the hardened function actually wired into the
pipeline, does a malformed catalog on disk now fail with a named assertion
instead of a ValueError from inside SciPy, and does the driver still produce
the same science on valid data?

**The fixture is hand-built and analytic, not generated.** Every galaxy below
is placed by hand so that the expected pair set, mass bins, separation bins and
relative speeds are derivable on paper. An earlier draft ran
`generate_test_data.generate_all_snapshots` and pinned the resulting counts;
that was wrong, because NumPy explicitly does *not* guarantee `Generator`'s bit
stream across versions, so a legitimate numpy upgrade could have failed a
correct submission through no fault of its own.

The whole import block is guarded, not just `pair_finder`: `calc` imports
`find_pairs` at module scope, so a submission that breaks pair_finder.py would
otherwise turn this file into a pytest collection error and (with pytest's
default behaviour) take test_hA.py's already-correct results down with it.
"""
import contextlib
import copy
import io
import os
import shutil
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import h5py
import numpy as np
import pytest

try:
    import calc
    import config as cfgmod
    import pair_finder as PF
except Exception as e:                      # pragma: no cover
    calc = cfgmod = PF = None
    _IMPORT_ERR = e

BASE = cfgmod.config if cfgmod is not None else {}
Z = 2.0

# ==========================================================================
# The hand-built catalog.
#
# Default config: box 500 Mpc, masses [8, 11] in 0.5 dex (6 bins),
# sep_bins [0, 10, 15, 20, 25] kpc, mass_ratio_min 0.1, max_sep 25 kpc.
#
# Each group sits at its own whole-Mpc x, i.e. >= 1000 kpc from every other
# group, so the only pairs within 25 kpc are the intended intra-group ones.
# Every galaxy is on the x axis (y = z = 0); the secondary sits at
# x_primary + sep_kpc/1000.
#
# (label, x_mpc, m_primary, m_secondary, sep_kpc, (dvx, dvy, dvz), note)
# ==========================================================================
GROUPS = [
    ("A",  10.0, 8.2,  8.0,   5.0, (3.0, 4.0, 0.0),  "pair: mass bin 0, sep bin 0"),
    ("B",  20.0, 8.7,  8.5,  12.0, (5.0, 12.0, 0.0), "pair: mass bin 1, sep bin 1"),
    ("C",  30.0, 9.2,  9.0,  17.0, (1.0, 2.0, 2.0),  "pair: mass bin 2, sep bin 2"),
    ("D",  40.0, 9.7,  9.5,  22.0, (2.0, 3.0, 6.0),  "pair: mass bin 3, sep bin 3"),
    ("E",  50.0, 10.2, 10.0,  8.0, (4.0, 4.0, 7.0),  "pair: mass bin 4, sep bin 0"),
    ("F",  60.0, 10.7, 10.5, 13.0, (6.0, 6.0, 7.0),  "pair: mass bin 5, sep bin 1"),
    ("G",  70.0, 10.5, 9.0,   9.0, (1.0, 0.0, 0.0),  "cut: ratio 10**-1.5 < 0.1"),
    ("H",  80.0, 10.0, 9.8,  30.0, (1.0, 0.0, 0.0),  "not a pair: 30 kpc > max_sep"),
    ("I",  90.0, 11.0, 10.9,  5.0, (8.0, 15.0, 0.0), "pair: mass bin -1 (11.0 is the exclusive upper edge)"),
    ("J", 100.0, 11.5, 10.6,  6.0, (1.0, 0.0, 0.0),  "11.5 is dropped by the [8, 11] selection"),
]

# Two galaxies straddling the periodic boundary: 499.999 Mpc and 0.001 Mpc are
# 2 kpc apart through the wrap, 999.998 kpc apart without it.
PBC_PRIMARY_X = 499.999
PBC_SECONDARY_X = 0.001
PBC_MASSES = (9.4, 9.3)
PBC_DV = (5.0, 12.0, 0.0)          # |dv| = 13

# Singles: one below the mass selection, three isolated in-range galaxies.
SINGLES = [(110.0, 7.5), (120.0, 8.1), (121.0, 9.1), (122.0, 10.1)]

# Derived by hand from the table above, for the default config.
#
# Whole ROWS, not per-column multisets. An r2 review pointed out that
# comparing each column's sorted values independently cannot catch a
# submission that computes every value correctly but misaligns which row it
# lands in -- a stray sort or reindex of one output array. Each tuple below is
# one pair as it must come back: every property of that pair, together.
#
#     (group, mass_primary, mass_secondary, separation_kpc, delta_v,
#      mass_bin, sep_bin)
#
# mass bin edges are [8, 8.5, 9, 9.5, 10, 10.5, 11]; sep bin edges are
# [0, 10, 15, 20, 25]. Group I's primary sits exactly on log_mass_max, which
# np.digitize's right-open convention puts outside every bin: mass_bin -1.
EXPECTED_ROWS = [
    ("A",   8.2,  8.0,   5.0,  5.0,  0, 0),
    ("B",   8.7,  8.5,  12.0, 13.0,  1, 1),
    ("C",   9.2,  9.0,  17.0,  3.0,  2, 2),
    ("D",   9.7,  9.5,  22.0,  7.0,  3, 3),
    ("E",  10.2, 10.0,   8.0,  9.0,  4, 0),
    ("F",  10.7, 10.5,  13.0, 11.0,  5, 1),
    ("I",  11.0, 10.9,   5.0, 17.0, -1, 0),
    ("PBC", 9.4,  9.3,   2.0, 13.0,  2, 0),
]

EXPECTED_N_PAIRS = len(EXPECTED_ROWS)
EXPECTED_MASS_BIN_COUNTS = [1, 1, 2, 1, 1, 1]     # bins 0..5
EXPECTED_MASS_BIN_SENTINELS = 1                    # group I
EXPECTED_SEP_BIN_COUNTS = [4, 2, 1, 1]             # bins 0..3
EXPECTED_SEP_BIN_SENTINELS = 0


def row_sort_key(separation, mass_primary):
    """Stable ordering shared by expected and actual rows.

    Separation alone is not unique (groups A and I are both 5 kpc), so the
    primary mass breaks the tie; the eight (separation, primary) pairs are
    distinct.
    """
    return (round(float(separation), 6), round(float(mass_primary), 6))


def build_catalog_arrays(box_size):
    x, y, z, vx, vy, vz, mass = [], [], [], [], [], [], []

    def add(px, pm, pv):
        x.append(px); y.append(0.0); z.append(0.0)
        vx.append(pv[0]); vy.append(pv[1]); vz.append(pv[2])
        mass.append(pm)

    for _label, gx, m_pri, m_sec, sep_kpc, dv, _note in GROUPS:
        add(gx, m_pri, dv)
        add(gx + sep_kpc / 1000.0, m_sec, (0.0, 0.0, 0.0))

    add(PBC_PRIMARY_X, PBC_MASSES[0], PBC_DV)
    add(PBC_SECONDARY_X, PBC_MASSES[1], (0.0, 0.0, 0.0))

    for sx, sm in SINGLES:
        add(sx, sm, (0.0, 0.0, 0.0))

    assert all(0.0 <= v < box_size for v in x), "fixture places a galaxy outside the box"
    return dict(
        x=np.array(x), y=np.array(y), z=np.array(z),
        vx=np.array(vx), vy=np.array(vy), vz=np.array(vz),
        log_stellar_mass=np.array(mass),
    )


def cfg(**kw):
    c = copy.deepcopy(BASE)
    c.update(kw)
    return c


def quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        return fn(*a, **k)


def data_path(c):
    return os.path.join(c["data_dir"], f"test_z{Z:.1f}.hdf5")


def results_path(c):
    return os.path.join(c["results_dir"], f"pairs_z{Z:.1f}.hdf5")


def write_catalog(path, box_size):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    arrays = build_catalog_arrays(box_size)
    with h5py.File(path, "w") as f:
        for key, arr in arrays.items():
            f.create_dataset(key, data=arr)
        f.attrs["redshift"] = Z
        f.attrs["box_size"] = box_size


@pytest.fixture(scope="module")
def make_case(tmp_path_factory):
    """Factory: a fresh directory with a pristine copy of the fixture catalog.

    One fixture for the whole file. Each call gets its own data/ and results/,
    so a test can corrupt its catalog without touching any other test's.
    """
    root = tmp_path_factory.mktemp("t003")
    pristine = str(root / "pristine.hdf5")
    write_catalog(pristine, float(BASE["box_size"]) if BASE else 500.0)
    counter = {"n": 0}

    def make(**overrides):
        counter["n"] += 1
        d = root / f"case{counter['n']}"
        c = cfg(data_dir=str(d / "data") + os.sep,
                results_dir=str(d / "results") + os.sep,
                figures_dir=str(d / "figures") + os.sep,
                redshifts=[Z], **overrides)
        os.makedirs(c["data_dir"], exist_ok=True)
        os.makedirs(c["results_dir"], exist_ok=True)
        shutil.copy(pristine, data_path(c))
        return c

    return make


# ================================================================== sanity
def test_B00_pipeline_imports():
    assert PF is not None and calc is not None, \
        f"the pipeline failed to import: {_IMPORT_ERR!r}"


# ================================================== valid data is unchanged
def test_B01_driver_output_matches_the_analytic_expectation(make_case):
    """The whole point of a validation task: the science must not move."""
    c = make_case()
    quiet(calc.run_calculation, c)

    p = results_path(c)
    assert os.path.isfile(p), "the driver wrote no results file"
    with h5py.File(p, "r") as f:
        for name in ("mass_primary", "mass_secondary", "mass_ratio",
                     "separation_kpc", "delta_v", "mass_bin", "sep_bin"):
            assert name in f, name
        mass_bin = f["mass_bin"][...]
        sep_bin = f["sep_bin"][...]
        sep = f["separation_kpc"][...]
        dv = f["delta_v"][...]
        ratio = f["mass_ratio"][...]
        m_pri = f["mass_primary"][...]
        m_sec = f["mass_secondary"][...]

    n_mass_bins = int(round((c["log_mass_max"] - c["log_mass_min"])
                            / c["mass_bin_width"]))
    n_sep_bins = len(c["sep_bins"]) - 1

    assert len(mass_bin) == EXPECTED_N_PAIRS, (
        f"expected {EXPECTED_N_PAIRS} pairs from the hand-built catalog, "
        f"got {len(mass_bin)}"
    )
    assert [int(np.sum(mass_bin == b)) for b in range(n_mass_bins)] \
        == EXPECTED_MASS_BIN_COUNTS
    assert [int(np.sum(sep_bin == b)) for b in range(n_sep_bins)] \
        == EXPECTED_SEP_BIN_COUNTS
    assert int(np.sum(mass_bin == -1)) == EXPECTED_MASS_BIN_SENTINELS, \
        "the mass_bin == -1 sentinel did not survive the driver"
    assert int(np.sum(sep_bin == -1)) == EXPECTED_SEP_BIN_SENTINELS

    # Row-by-row, not column-by-column: every property of a pair must still
    # belong to that pair. Both sides are ordered by the same stable key, so
    # this is insensitive to the order query_pairs happens to yield.
    actual_rows = sorted(
        zip(sep, m_pri, m_sec, dv, mass_bin, sep_bin, ratio, strict=True),
        key=lambda r: row_sort_key(r[0], r[1]))
    expected_rows = sorted(EXPECTED_ROWS,
                           key=lambda r: row_sort_key(r[3], r[1]))

    for got, want in zip(actual_rows, expected_rows, strict=True):
        got_sep, got_pri, got_sec, got_dv, got_mb, got_sb, got_ratio = got
        label, want_pri, want_sec, want_sep, want_dv, want_mb, want_sb = want
        where = f"group {label}"
        np.testing.assert_allclose(got_sep, want_sep, rtol=0, atol=1e-6,
                                   err_msg=f"{where}: separation_kpc")
        np.testing.assert_allclose(got_pri, want_pri, rtol=0, atol=1e-12,
                                   err_msg=f"{where}: mass_primary")
        np.testing.assert_allclose(got_sec, want_sec, rtol=0, atol=1e-12,
                                   err_msg=f"{where}: mass_secondary")
        np.testing.assert_allclose(got_dv, want_dv, rtol=1e-12, atol=0,
                                   err_msg=f"{where}: delta_v")
        np.testing.assert_allclose(got_ratio, 10.0 ** (want_sec - want_pri),
                                   rtol=1e-12, atol=0,
                                   err_msg=f"{where}: mass_ratio")
        assert int(got_mb) == want_mb, f"{where}: mass_bin"
        assert int(got_sb) == want_sb, f"{where}: sep_bin"

    assert np.all(m_pri >= m_sec)
    assert np.all(ratio >= c["mass_ratio_min"]) and np.all(ratio <= 1.0)
    assert np.all(sep <= c["max_sep"])


# ============================ malformed catalog on disk, through the driver
def test_B02_nonfinite_position_on_disk_asserts(make_case):
    """Today this escapes as scipy's 'data must be finite' ValueError."""
    c = make_case()
    with h5py.File(data_path(c), "r+") as f:
        f["x"][...] = np.nan

    with pytest.raises(AssertionError, match="finite"):
        quiet(calc.run_calculation, c)

    assert not os.path.isfile(results_path(c)), \
        "a results file was written for a catalog that should have been rejected"


def test_B03_position_outside_box_on_disk_asserts(make_case):
    """Today this escapes as scipy's 'greater than the size of the periodic
    box' ValueError."""
    c = make_case()
    with h5py.File(data_path(c), "r+") as f:
        f["x"][...] = float(c["box_size"]) + 1.0

    with pytest.raises(AssertionError, match="box"):
        quiet(calc.run_calculation, c)

    assert not os.path.isfile(results_path(c)), \
        "a results file was written for a catalog that should have been rejected"


def test_B04_malformed_config_through_driver(make_case):
    """A bad config reaches find_pairs through the driver too."""
    failures = []
    for label, overrides, token in (
        ("max_sep=0", dict(max_sep=0.0), "max_sep"),
        ("max_sep=nan", dict(max_sep=float("nan")), "max_sep"),
        ("mass_ratio_min=1.5", dict(mass_ratio_min=1.5), "mass_ratio_min"),
        ("sep_bins unsorted", dict(sep_bins=[0, 10, 5, 25]), "sep_bins"),
        ("mass_bin_width=0", dict(mass_bin_width=0.0), "mass_bin_width"),
    ):
        c = make_case(**overrides)
        try:
            quiet(calc.run_calculation, c)
        except AssertionError as e:
            if token not in str(e):
                failures.append((label, f"message did not name {token}", str(e)))
        except Exception as e:
            failures.append((label, type(e).__name__, str(e)))
        else:
            failures.append((label, "no exception", ""))
    assert not failures, failures


# ============================ the driver still follows the config it is given
def test_B05_driver_honours_nondefault_config(make_case):
    """Validation must not have hardcoded the defaults it was written against.

    Runs the real driver on the same catalog with a tighter max_sep, a
    different sep_bins grid and a different mass grid, then recomputes the
    stored bin assignments from the stored separations/masses using *those*
    edges.
    """
    sep_bins = [0, 4, 6, 9]
    c = make_case(max_sep=9.0, sep_bins=sep_bins,
                  log_mass_min=9.0, log_mass_max=12.0, mass_bin_width=1.5)
    quiet(calc.run_calculation, c)

    with h5py.File(results_path(c), "r") as f:
        sep = f["separation_kpc"][...]
        mass_bin = f["mass_bin"][...]
        sep_bin = f["sep_bin"][...]
        m_pri = f["mass_primary"][...]

    assert len(sep) > 0, "the tightened run found no pairs at all -- bad fixture"
    assert len(sep) < EXPECTED_N_PAIRS, \
        "max_sep=9.0 returned as many pairs as max_sep=25.0; config ignored"
    assert np.all(sep <= 9.0)

    n_mass_bins = 2                          # [9.0, 10.5), [10.5, 12.0)
    edges = np.linspace(9.0, 12.0, n_mass_bins + 1)
    raw = np.digitize(m_pri, edges) - 1
    raw = np.where((raw < 0) | (raw >= n_mass_bins), -1, raw)
    np.testing.assert_array_equal(mass_bin, raw,
                                  err_msg="mass_bin ignores the config mass grid")

    n_sep_bins = len(sep_bins) - 1
    raw_sep = np.digitize(sep, sep_bins) - 1
    raw_sep = np.where((raw_sep < 0) | (raw_sep >= n_sep_bins), -1, raw_sep)
    np.testing.assert_array_equal(sep_bin, raw_sep,
                                  err_msg="sep_bin ignores the config sep_bins")

    # Independent of the recomputations above: the *set* of indices produced
    # can only come from the alternate grids. The default 6-bin mass grid
    # would reach index 5, and the default sep_bins would put every pair at
    # these separations into bin 0 alone.
    assert set(np.unique(mass_bin).tolist()) == {0, 1}, \
        f"mass_bin indices {sorted(set(np.unique(mass_bin).tolist()))} are not " \
        f"the alternate 2-bin grid's -- a hardcoded default grid?"
    assert set(np.unique(sep_bin).tolist()) == {0, 1, 2}, \
        f"sep_bin indices {sorted(set(np.unique(sep_bin).tolist()))} are not " \
        f"the alternate 3-bin grid's -- hardcoded default sep_bins?"

    # The [9, 12] selection admits the 11.5 galaxy the default [8, 11] one
    # drops, so its pair appears only under the alternate mass range.
    assert float(np.max(m_pri)) > 11.0, \
        "the alternate mass selection did not admit the 11.5 galaxy"
