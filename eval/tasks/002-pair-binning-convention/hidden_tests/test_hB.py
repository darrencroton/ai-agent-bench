"""Hidden Harness B: integration criteria (provenance, atomicity, schema,
config tracking, end-to-end science).

Not visible to the Developer model. Copied into the trial worktree's tests/
directory at grade time and run with the trial's own pytest/venv. Scores the
"correctness" rubric category together with test_hA.py.
"""
import contextlib
import copy
import datetime
import hashlib
import io
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import h5py
import numpy as np
import pytest

import config as cfgmod
import calc
import pair_binning as PB
from data_reader import load_galaxy_catalog
from generate_test_data import generate_all_snapshots

BASE = cfgmod.config

ALL_CONVENTIONS = ("primary", "secondary", "either")

HEADING_SENTENCE = (
    "N_gal(b) is the same galaxy count for every convention; only the "
    "numerator changes."
)

# The pinned hand-fixture pair sample (same as test_hA.py's).
FIX_PRIMARY = np.array([8.2, 9.7, 10.6, 11.0, 10.2, 11.0])
FIX_SECONDARY = np.array([8.1, 8.9, 10.6, 10.4, 9.5, 11.0])
# The fixture catalog must contain the pair members themselves (as a real
# catalog does) plus unpaired field galaxies, or the denominator would be
# smaller than the numerator in some bin -- physically impossible, and
# correctly rejected by compute_pair_fraction.
FIX_FIELD = np.array([7.99, 8.0, 8.499, 9.75, 10.5, 10.9999, 11.0])
FIX_GALAXIES = np.concatenate([FIX_PRIMARY, FIX_SECONDARY, FIX_FIELD])
FIX_EXPECT = {
    "primary": [1, 0, 0, 1, 1, 1],
    "secondary": [1, 1, 0, 1, 1, 1],
    "either": [2, 1, 0, 2, 2, 2],
}
FIX_EXCLUDED = {"primary": 2, "secondary": 1, "either": 1}
FIX_GAL_COUNTS = [4, 1, 0, 3, 2, 4]


def cfg(**kw):
    c = copy.deepcopy(BASE)
    c.update(kw)
    return c


def nbins(c=BASE):
    return int(round((c["log_mass_max"] - c["log_mass_min"]) / c["mass_bin_width"]))


def norm(text):
    return re.sub(r"\s+", " ", text or "").strip()


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def rejects(fn, *a, **k):
    try:
        fn(*a, **k)
    except AssertionError:
        return "assert"
    except Exception as e:
        return type(e).__name__
    return None


def reject_message(fn, *a, **k):
    """Like rejects(), but returns the AssertionError's message text (or None)."""
    try:
        fn(*a, **k)
    except AssertionError as e:
        return str(e)
    except Exception:
        return None
    return None


def line_tokens(line):
    return line.split()


def lines_with_tokens(lines, *tokens):
    """Whitespace-delimited exact-token match, not naive substring search --
    a label like 'notz=2.0' must not false-positive against token 'z=2.0'."""
    return [ln for ln in lines if all(t in line_tokens(ln) for t in tokens)]


def quiet(fn, *a, **k):
    """Call fn with stdout suppressed; return (result, captured_stdout)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        result = fn(*a, **k)
    return result, buf.getvalue()


def ref_bins(masses, c):
    edges = np.linspace(c["log_mass_min"], c["log_mass_max"],
                        int(round((c["log_mass_max"] - c["log_mass_min"]) / c["mass_bin_width"])) + 1)
    raw = np.digitize(np.asarray(masses, dtype=float), edges) - 1
    n = len(edges) - 1
    return np.where((raw < 0) | (raw >= n), -1, raw)


def ref_counts(bin_arrays, n):
    out = np.zeros(n, dtype=np.int64)
    for arr in bin_arrays:
        for b in range(n):
            out[b] += int(np.count_nonzero(arr == b))
    return out


# ------------------------------------------------------------- fixtures

def write_snapshot(c, z, gal_masses, pair_primary, pair_secondary,
                   attr_overrides=None, mass_bin=None, mass_bin_by="primary"):
    """Write one hand-built (catalog, pair-results) snapshot pair to disk."""
    os.makedirs(c["data_dir"], exist_ok=True)
    os.makedirs(c["results_dir"], exist_ok=True)

    gal_masses = np.asarray(gal_masses, dtype=float)
    n_gal = len(gal_masses)
    data_path = os.path.join(c["data_dir"], f"test_z{z:.1f}.hdf5")
    with h5py.File(data_path, "w") as f:
        coords = np.linspace(0.0, float(c["box_size"]) * 0.5, n_gal)
        for key in ("x", "y", "z"):
            f.create_dataset(key, data=coords)
        for key in ("vx", "vy", "vz"):
            f.create_dataset(key, data=np.zeros(n_gal))
        f.create_dataset("log_stellar_mass", data=gal_masses)
        f.attrs["redshift"] = float(z)
        f.attrs["box_size"] = float(c["box_size"])

    mp = np.asarray(pair_primary, dtype=float)
    ms = np.asarray(pair_secondary, dtype=float)
    n_pair = len(mp)
    if mass_bin is None:
        mass_bin = ref_bins(mp, c)
    results_path = os.path.join(c["results_dir"], f"pairs_z{z:.1f}.hdf5")
    with h5py.File(results_path, "w") as f:
        f.create_dataset("mass_primary", data=mp)
        f.create_dataset("mass_secondary", data=ms)
        f.create_dataset("mass_ratio", data=10.0 ** (ms - mp))
        f.create_dataset("separation_kpc", data=np.full(n_pair, 12.0))
        f.create_dataset("delta_v", data=np.full(n_pair, 120.0))
        f.create_dataset("mass_bin", data=np.asarray(mass_bin, dtype=np.int64))
        f.create_dataset("sep_bin", data=np.ones(n_pair, dtype=np.int64))
        f.attrs["redshift"] = float(z)
        f.attrs["n_pairs"] = n_pair
        f.attrs["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        f.attrs["mass_bin_by"] = mass_bin_by
        f.attrs["mass_ratio_min"] = float(c["mass_ratio_min"])
        f.attrs["max_sep_kpc"] = float(c["max_sep"])
        for key, value in (attr_overrides or {}).items():
            f.attrs[key] = value
    return data_path, results_path


def tmp_cfg(tmp_path, **kw):
    c = cfg(data_dir=str(tmp_path / "data") + os.sep,
            results_dir=str(tmp_path / "results") + os.sep,
            figures_dir=str(tmp_path / "figures") + os.sep)
    c.update(kw)
    os.makedirs(c["data_dir"], exist_ok=True)
    os.makedirs(c["results_dir"], exist_ok=True)
    return c


@pytest.fixture(scope="module")
def mock(tmp_path_factory):
    root = tmp_path_factory.mktemp("e2e")
    c = cfg(data_dir=str(root / "data") + os.sep,
            results_dir=str(root / "results") + os.sep,
            figures_dir=str(root / "figures") + os.sep)
    os.makedirs(c["data_dir"], exist_ok=True)
    os.makedirs(c["results_dir"], exist_ok=True)
    with contextlib.redirect_stdout(io.StringIO()):
        generate_all_snapshots(c)
        calc.run_calculation(c)
    return c


@pytest.fixture
def fixture_cfg(tmp_path):
    c = tmp_cfg(tmp_path, redshifts=[2.0])
    write_snapshot(c, 2.0, FIX_GALAXIES, FIX_PRIMARY, FIX_SECONDARY)
    return c


def sentinel(c):
    path = os.path.join(c["results_dir"], "pair_binning.hdf5")
    with open(path, "wb") as f:
        f.write(b"SENTINEL-NOT-A-REAL-HDF5-FILE")
    return path, sha(path)


# ------------------------------------------------- Part 2: loading

def test_B01_load_snapshot_counts_contract(mock):
    got = PB.load_snapshot_counts(mock["redshifts"][0], mock)
    assert set(got.keys()) == {
        "redshift", "n_galaxies", "n_pairs", "n_excluded_pairs", "n_pairs_total"}
    assert got["redshift"] == float(mock["redshifts"][0])
    assert isinstance(got["n_galaxies"], np.ndarray), (
        f"n_galaxies must be an ndarray, not {type(got['n_galaxies']).__name__}")
    ng = np.asarray(got["n_galaxies"])
    assert ng.ndim == 1 and ng.shape == (nbins(mock),) and ng.dtype.kind in "iu"
    assert set(got["n_pairs"]) == set(mock["pair_binning_conventions"])
    assert set(got["n_excluded_pairs"]) == set(mock["pair_binning_conventions"])
    for conv, arr_raw in got["n_pairs"].items():
        assert isinstance(arr_raw, np.ndarray), (
            f"n_pairs[{conv!r}] must be an ndarray, not {type(arr_raw).__name__}")
        arr = np.asarray(arr_raw)
        assert arr.shape == (nbins(mock),) and arr.dtype.kind in "iu", conv
    for conv, val in got["n_excluded_pairs"].items():
        assert isinstance(val, (int, np.integer)) and not isinstance(val, bool), (
            f"n_excluded_pairs[{conv!r}] must be an int-kind scalar, got {type(val).__name__}")
    assert isinstance(got["n_pairs_total"], (int, np.integer))


def test_B02_denominator_is_the_full_selected_catalog(mock):
    for z in mock["redshifts"]:
        got = PB.load_snapshot_counts(z, mock)
        catalog = load_galaxy_catalog(PB._data_path(z, mock), mock)
        masses = np.asarray(catalog["log_stellar_mass"], dtype=float)
        expected_in_bins = int(np.count_nonzero(
            (masses >= mock["log_mass_min"]) & (masses < mock["log_mass_max"])))
        assert int(np.sum(np.asarray(got["n_galaxies"]))) == expected_in_bins
        # and it is not the pair-derived count
        assert expected_in_bins > got["n_pairs_total"]


def test_B03_upper_edge_galaxy_is_selected_but_unbinned(tmp_path):
    c = tmp_cfg(tmp_path, redshifts=[2.0])
    masses = np.array([8.1, 9.1, 11.0])       # the 11.0 is selected but in no bin
    write_snapshot(c, 2.0, masses, np.array([9.1]), np.array([8.1]))
    got = PB.load_snapshot_counts(2.0, c)
    catalog = load_galaxy_catalog(PB._data_path(2.0, c), c)
    assert len(catalog["log_stellar_mass"]) == 3
    assert int(np.sum(np.asarray(got["n_galaxies"]))) == 2


def test_B04_counts_and_invariants_on_mock(mock):
    for z in mock["redshifts"]:
        got = PB.load_snapshot_counts(z, mock)
        counts = {c: np.asarray(got["n_pairs"][c]) for c in ALL_CONVENTIONS}
        np.testing.assert_array_equal(counts["primary"] + counts["secondary"], counts["either"])
        assert PB.check_additivity(counts["primary"], counts["secondary"], counts["either"]) is True
        for conv in ("primary", "secondary"):
            assert int(np.sum(counts[conv])) + int(got["n_excluded_pairs"][conv]) \
                == got["n_pairs_total"], (z, conv)


def test_B05_n_pairs_total_matches_file_rows(mock):
    for z in mock["redshifts"]:
        with h5py.File(PB._results_path(z, mock), "r") as f:
            rows = len(f["mass_primary"][...])
        assert PB.load_snapshot_counts(z, mock)["n_pairs_total"] == rows


def test_B06_hand_fixture_counts_are_hand_computed(fixture_cfg):
    got = PB.load_snapshot_counts(2.0, fixture_cfg)
    assert list(np.asarray(got["n_galaxies"])) == FIX_GAL_COUNTS
    for conv in ALL_CONVENTIONS:
        assert list(np.asarray(got["n_pairs"][conv])) == FIX_EXPECT[conv], conv
        assert int(got["n_excluded_pairs"][conv]) == FIX_EXCLUDED[conv], conv
    assert got["n_pairs_total"] == 6


def test_B07_stored_mass_bin_and_mass_bin_by_are_not_used(tmp_path):
    """spec.md section 2: the frozen convention must not leak into this module."""
    c = tmp_cfg(tmp_path, redshifts=[2.0])
    garbage = np.full(len(FIX_PRIMARY), 2, dtype=np.int64)
    write_snapshot(c, 2.0, FIX_GALAXIES, FIX_PRIMARY, FIX_SECONDARY,
                   mass_bin=garbage, mass_bin_by="total")
    got = PB.load_snapshot_counts(2.0, c)
    for conv in ALL_CONVENTIONS:
        assert list(np.asarray(got["n_pairs"][conv])) == FIX_EXPECT[conv], conv
        assert int(got["n_excluded_pairs"][conv]) == FIX_EXCLUDED[conv], conv


def test_B08_conventions_config_is_honoured(tmp_path):
    c = tmp_cfg(tmp_path, redshifts=[2.0])
    write_snapshot(c, 2.0, FIX_GALAXIES, FIX_PRIMARY, FIX_SECONDARY)

    c["pair_binning_conventions"] = ["either"]
    got = PB.load_snapshot_counts(2.0, c)
    assert list(got["n_pairs"].keys()) == ["either"]
    assert list(got["n_excluded_pairs"].keys()) == ["either"]

    c["pair_binning_conventions"] = ["secondary", "primary"]
    got = PB.load_snapshot_counts(2.0, c)
    assert list(got["n_pairs"].keys()) == ["secondary", "primary"]
    assert list(np.asarray(got["n_pairs"]["secondary"])) == FIX_EXPECT["secondary"]
    assert list(np.asarray(got["n_pairs"]["primary"])) == FIX_EXPECT["primary"]


@pytest.mark.parametrize("bad", [
    [], ["primary", "primary"], ["mean"], ["total"], ["nonsense"],
    [None], [3], "primary", ("primary", "primary"),
])
def test_B09_invalid_conventions_config_rejected(fixture_cfg, bad):
    c = dict(fixture_cfg)
    c["pair_binning_conventions"] = bad
    assert rejects(PB.load_snapshot_counts, 2.0, c) == "assert", bad
    msg = reject_message(PB.load_snapshot_counts, 2.0, c)
    assert msg, f"assertion for pair_binning_conventions={bad!r} carried no message"
    assert "pair_binning_conventions" in msg.lower() or "convention" in msg.lower(), msg


@pytest.mark.parametrize("which", ["missing_data", "missing_results", "wrong_redshift"])
def test_B10_load_snapshot_counts_file_rejections(tmp_path, which):
    c = tmp_cfg(tmp_path / which, redshifts=[2.0])
    write_snapshot(c, 2.0, FIX_GALAXIES, FIX_PRIMARY, FIX_SECONDARY)

    if which == "missing_data":
        target = PB._data_path(2.0, c)
        os.remove(target)
        assert rejects(PB.load_snapshot_counts, 2.0, c) == "assert"
        msg = reject_message(PB.load_snapshot_counts, 2.0, c)
        assert msg and (target in msg or os.path.basename(target) in msg), msg
    elif which == "missing_results":
        target = PB._results_path(2.0, c)
        os.remove(target)
        assert rejects(PB.load_snapshot_counts, 2.0, c) == "assert"
        msg = reject_message(PB.load_snapshot_counts, 2.0, c)
        assert msg and (target in msg or os.path.basename(target) in msg), msg
    else:  # wrong configured redshift for this file
        assert rejects(PB.load_snapshot_counts, 3.0, c) == "assert"


@pytest.mark.parametrize("override,attr", [
    ({"redshift": 9.0}, "redshift"),
    ({"redshift": "2.0"}, "redshift"),
    ({"redshift": np.array([2.0, 2.0])}, "redshift"),
    ({"mass_ratio_min": 0.25}, "mass_ratio_min"),
    ({"mass_ratio_min": "0.1"}, "mass_ratio_min"),
    ({"max_sep_kpc": 50.0}, "max_sep_kpc"),
    ({"max_sep_kpc": b"25.0"}, "max_sep_kpc"),
])
def test_B11_load_snapshot_counts_attr_rejections(tmp_path, override, attr):
    c = tmp_cfg(tmp_path, redshifts=[2.0])
    write_snapshot(c, 2.0, FIX_GALAXIES, FIX_PRIMARY, FIX_SECONDARY,
                   attr_overrides=override)
    assert rejects(PB.load_snapshot_counts, 2.0, c) == "assert", override
    msg = reject_message(PB.load_snapshot_counts, 2.0, c)
    assert msg, f"assertion for {override!r} carried no message"
    assert attr in msg, (attr, msg)


@pytest.mark.parametrize("drop", ["redshift", "mass_ratio_min", "max_sep_kpc"])
def test_B12a_load_snapshot_counts_missing_attr(tmp_path, drop):
    c = tmp_cfg(tmp_path / f"drop_{drop}", redshifts=[2.0])
    write_snapshot(c, 2.0, FIX_GALAXIES, FIX_PRIMARY, FIX_SECONDARY)
    with h5py.File(PB._results_path(2.0, c), "r+") as f:
        del f.attrs[drop]
    assert rejects(PB.load_snapshot_counts, 2.0, c) == "assert", drop
    msg = reject_message(PB.load_snapshot_counts, 2.0, c)
    assert msg, f"assertion for missing attr {drop!r} carried no message"
    assert drop in msg, (drop, msg)


@pytest.mark.parametrize("drop", ["mass_primary", "mass_secondary"])
def test_B12b_load_snapshot_counts_missing_dataset(tmp_path, drop):
    c = tmp_cfg(tmp_path / f"dsdrop_{drop}", redshifts=[2.0])
    write_snapshot(c, 2.0, FIX_GALAXIES, FIX_PRIMARY, FIX_SECONDARY)
    with h5py.File(PB._results_path(2.0, c), "r+") as f:
        del f[drop]
    assert rejects(PB.load_snapshot_counts, 2.0, c) == "assert", drop
    msg = reject_message(PB.load_snapshot_counts, 2.0, c)
    assert msg, f"assertion for missing dataset {drop!r} carried no message"
    assert drop in msg, (drop, msg)


def test_B12c_load_snapshot_counts_length_mismatch(tmp_path):
    c = tmp_cfg(tmp_path / "lenmismatch", redshifts=[2.0])
    write_snapshot(c, 2.0, FIX_GALAXIES, FIX_PRIMARY, FIX_SECONDARY)
    with h5py.File(PB._results_path(2.0, c), "r+") as f:
        del f["mass_secondary"]
        f.create_dataset("mass_secondary", data=FIX_SECONDARY[:3])
    assert rejects(PB.load_snapshot_counts, 2.0, c) == "assert"
    msg = reject_message(PB.load_snapshot_counts, 2.0, c)
    assert msg and ("mass_primary" in msg or "mass_secondary" in msg
                     or "length" in msg.lower() or "len" in msg.lower()), msg


# ------------------------------------------------- Part 3: comparison

def test_B13_output_schema_on_mock(mock):
    results, _ = quiet(PB.run_binning_comparison, mock)
    path = os.path.join(mock["results_dir"], "pair_binning.hdf5")
    assert os.path.isfile(path)
    nz, nc, nb = len(mock["redshifts"]), len(mock["pair_binning_conventions"]), nbins(mock)
    with h5py.File(path, "r") as f:
        assert f["n_galaxies"].shape == (nz, nb)
        assert f["n_pairs"].shape == (nz, nc, nb)
        assert f["pair_fraction"].shape == (nz, nc, nb)
        assert f["pair_fraction_err"].shape == (nz, nc, nb)
        assert f["n_excluded_pairs"].shape == (nz, nc)
        assert f["n_galaxies"].dtype.kind in "iu"
        assert f["n_pairs"].dtype.kind in "iu"
        assert f["n_excluded_pairs"].dtype.kind in "iu"
        assert f["pair_fraction"].dtype.kind == "f"
        assert f["pair_fraction_err"].dtype.kind == "f"
        for a in ("redshifts", "conventions", "mass_bin_edges", "mass_ratio_min",
                  "max_sep_kpc", "timestamp", "additivity_checked", "additivity_holds"):
            assert a in f.attrs, a
        np.testing.assert_allclose(np.asarray(f.attrs["redshifts"], dtype=float),
                                   np.asarray(mock["redshifts"], dtype=float),
                                   rtol=0, atol=0)
        stored_conv = [c.decode() if isinstance(c, bytes) else str(c)
                       for c in np.atleast_1d(f.attrs["conventions"])]
        assert stored_conv == list(mock["pair_binning_conventions"])
        np.testing.assert_allclose(np.asarray(f.attrs["mass_bin_edges"], dtype=float),
                                   np.linspace(8.0, 11.0, nb + 1), rtol=0, atol=0)
        assert float(f.attrs["mass_ratio_min"]) == float(mock["mass_ratio_min"])
        assert float(f.attrs["max_sep_kpc"]) == float(mock["max_sep"])
        assert bool(f.attrs["additivity_checked"]) is True
        assert bool(f.attrs["additivity_holds"]) is True
        # Not silently coerced from an integer 0/1 via bool(...): the stored
        # attr itself must be boolean-typed.
        assert np.asarray(f.attrs["additivity_checked"]).dtype == np.bool_, \
            np.asarray(f.attrs["additivity_checked"]).dtype
        assert np.asarray(f.attrs["additivity_holds"]).dtype == np.bool_, \
            np.asarray(f.attrs["additivity_holds"]).dtype
        parsed = datetime.datetime.fromisoformat(str(f.attrs["timestamp"]))
        assert parsed.tzinfo is not None
        frac = f["pair_fraction"][...]
        ferr = f["pair_fraction_err"][...]
    assert np.all(np.isfinite(frac)) and np.all(frac >= 0)
    assert np.all(np.isfinite(ferr)) and np.all(ferr >= 0)
    assert len(results) == nz


def test_B14_returned_dicts_match_persisted(mock):
    results, _ = quiet(PB.run_binning_comparison, mock)
    conventions = list(mock["pair_binning_conventions"])
    path = os.path.join(mock["results_dir"], "pair_binning.hdf5")
    with h5py.File(path, "r") as f:
        ngal = f["n_galaxies"][...]
        npair = f["n_pairs"][...]
        frac = f["pair_fraction"][...]
        ferr = f["pair_fraction_err"][...]
        excl = f["n_excluded_pairs"][...]

    for iz, r in enumerate(results):
        assert set(r.keys()) == {"redshift", "n_galaxies", "n_pairs", "pair_fraction",
                                 "pair_fraction_err", "n_excluded_pairs", "additivity_holds"}
        # Nested dicts too: an extra unspecified key in any of these would
        # otherwise pass unnoticed.
        assert set(r["n_pairs"].keys()) == set(conventions), r["n_pairs"].keys()
        assert set(r["pair_fraction"].keys()) == set(conventions), r["pair_fraction"].keys()
        assert set(r["pair_fraction_err"].keys()) == set(conventions), r["pair_fraction_err"].keys()
        assert set(r["n_excluded_pairs"].keys()) == set(conventions), r["n_excluded_pairs"].keys()
        assert r["redshift"] == float(mock["redshifts"][iz])
        np.testing.assert_array_equal(np.asarray(r["n_galaxies"]), ngal[iz])
        assert r["additivity_holds"] is True
        for ic, conv in enumerate(conventions):
            np.testing.assert_array_equal(np.asarray(r["n_pairs"][conv]), npair[iz, ic])
            np.testing.assert_allclose(np.asarray(r["pair_fraction"][conv]), frac[iz, ic],
                                       rtol=0, atol=0)
            np.testing.assert_allclose(np.asarray(r["pair_fraction_err"][conv]), ferr[iz, ic],
                                       rtol=0, atol=0)
            assert int(r["n_excluded_pairs"][conv]) == int(excl[iz, ic])


def test_B15_one_denominator_shared_by_every_convention(mock):
    """The denominator decision, checked numerically rather than structurally."""
    quiet(PB.run_binning_comparison, mock)
    path = os.path.join(mock["results_dir"], "pair_binning.hdf5")
    with h5py.File(path, "r") as f:
        ngal = f["n_galaxies"][...].astype(float)
        npair = f["n_pairs"][...].astype(float)
        frac = f["pair_fraction"][...]
        ferr = f["pair_fraction_err"][...]
    nz, nc, _ = npair.shape
    for iz in range(nz):
        for ic in range(nc):
            expected = np.where(ngal[iz] > 0, npair[iz, ic] / np.where(ngal[iz] > 0, ngal[iz], 1.0), 0.0)
            zero = expected == 0
            assert np.all(frac[iz, ic][zero] == 0.0)
            np.testing.assert_allclose(frac[iz, ic][~zero], expected[~zero], rtol=1e-14, atol=0)
            exp_err = np.where(npair[iz, ic] > 0,
                               expected / np.sqrt(np.where(npair[iz, ic] > 0, npair[iz, ic], 1.0)),
                               0.0)
            zero_e = exp_err == 0
            assert np.all(ferr[iz, ic][zero_e] == 0.0)
            np.testing.assert_allclose(ferr[iz, ic][~zero_e], exp_err[~zero_e], rtol=1e-14, atol=0)


def test_B16_end_to_end_counts_recomputed_independently(mock):
    results, _ = quiet(PB.run_binning_comparison, mock)
    nb = nbins(mock)
    for iz, z in enumerate(mock["redshifts"]):
        with h5py.File(PB._results_path(z, mock), "r") as f:
            mp = f["mass_primary"][...]
            ms = f["mass_secondary"][...]
        catalog = load_galaxy_catalog(PB._data_path(z, mock), mock)
        bp, bs = ref_bins(mp, mock), ref_bins(ms, mock)
        expected = {
            "primary": ref_counts([bp], nb),
            "secondary": ref_counts([bs], nb),
            "either": ref_counts([bp, bs], nb),
        }
        np.testing.assert_array_equal(
            np.asarray(results[iz]["n_galaxies"]),
            ref_counts([ref_bins(catalog["log_stellar_mass"], mock)], nb))
        for conv in ALL_CONVENTIONS:
            np.testing.assert_array_equal(
                np.asarray(results[iz]["n_pairs"][conv]), expected[conv],
                err_msg=f"z={z} convention={conv}")
        assert int(results[iz]["n_excluded_pairs"]["primary"]) == int(np.count_nonzero(bp == -1))
        assert int(results[iz]["n_excluded_pairs"]["secondary"]) == int(np.count_nonzero(bs == -1))
        assert int(results[iz]["n_excluded_pairs"]["either"]) == \
            int(np.count_nonzero((bp == -1) & (bs == -1)))


def test_B17_conventions_config_tracks_through_the_driver(mock, tmp_path):
    full, _ = quiet(PB.run_binning_comparison, mock)
    c = cfg(data_dir=mock["data_dir"],
            results_dir=str(tmp_path / "out") + os.sep,
            pair_binning_conventions=["secondary", "primary"])
    os.makedirs(c["results_dir"], exist_ok=True)
    # point the driver at the mock's pair files without clobbering them
    for z in c["redshifts"]:
        with open(PB._results_path(z, mock), "rb") as src, \
                open(PB._results_path(z, c), "wb") as dst:
            dst.write(src.read())

    results, _ = quiet(PB.run_binning_comparison, c)
    path = os.path.join(c["results_dir"], "pair_binning.hdf5")
    with h5py.File(path, "r") as f:
        stored_conv = [x.decode() if isinstance(x, bytes) else str(x)
                       for x in np.atleast_1d(f.attrs["conventions"])]
        assert stored_conv == ["secondary", "primary"]
        assert f["n_pairs"].shape[1] == 2
        assert f["n_excluded_pairs"].shape[1] == 2
        assert bool(f.attrs["additivity_checked"]) is False
        assert "additivity_holds" not in f.attrs
        npair = f["n_pairs"][...]
        ngal = f["n_galaxies"][...]
        frac = f["pair_fraction"][...]
        ferr = f["pair_fraction_err"][...]
        excl = f["n_excluded_pairs"][...]

    # Every returned/persisted element, not only n_pairs -- a partial run
    # that got the numerator right but silently recomputed a different
    # denominator, fraction or exclusion count would otherwise pass.
    for iz, r in enumerate(results):
        assert r["additivity_holds"] is None
        assert set(r["n_pairs"].keys()) == {"secondary", "primary"}
        np.testing.assert_array_equal(np.asarray(r["n_galaxies"]),
                                      np.asarray(full[iz]["n_galaxies"]))
        np.testing.assert_array_equal(ngal[iz], np.asarray(full[iz]["n_galaxies"]))
        for ic, conv in enumerate(("secondary", "primary")):
            np.testing.assert_array_equal(np.asarray(r["n_pairs"][conv]),
                                          np.asarray(full[iz]["n_pairs"][conv]))
            np.testing.assert_allclose(np.asarray(r["pair_fraction"][conv]),
                                       np.asarray(full[iz]["pair_fraction"][conv]),
                                       rtol=1e-14, atol=0)
            np.testing.assert_allclose(np.asarray(r["pair_fraction_err"][conv]),
                                       np.asarray(full[iz]["pair_fraction_err"][conv]),
                                       rtol=1e-14, atol=0)
            assert int(r["n_excluded_pairs"][conv]) == int(full[iz]["n_excluded_pairs"][conv])

            np.testing.assert_array_equal(npair[iz, ic], np.asarray(full[iz]["n_pairs"][conv]))
            np.testing.assert_allclose(frac[iz, ic], np.asarray(full[iz]["pair_fraction"][conv]),
                                       rtol=1e-14, atol=0)
            np.testing.assert_allclose(ferr[iz, ic], np.asarray(full[iz]["pair_fraction_err"][conv]),
                                       rtol=1e-14, atol=0)
            assert int(excl[iz, ic]) == int(full[iz]["n_excluded_pairs"][conv])


def test_B18_single_redshift_run(mock, tmp_path):
    full, _ = quiet(PB.run_binning_comparison, mock)
    z = mock["redshifts"][1]
    c = cfg(data_dir=mock["data_dir"],
            results_dir=str(tmp_path / "one") + os.sep,
            redshifts=[z])
    os.makedirs(c["results_dir"], exist_ok=True)
    with open(PB._results_path(z, mock), "rb") as src, \
            open(PB._results_path(z, c), "wb") as dst:
        dst.write(src.read())

    results, _ = quiet(PB.run_binning_comparison, c)
    assert len(results) == 1
    r = results[0]
    full_r = full[1]
    with h5py.File(os.path.join(c["results_dir"], "pair_binning.hdf5"), "r") as f:
        assert f["n_pairs"].shape[0] == 1
        assert f["n_galaxies"].shape[0] == 1
        np.testing.assert_array_equal(f["n_galaxies"][0], np.asarray(full_r["n_galaxies"]))
        for ic, conv in enumerate(ALL_CONVENTIONS):
            np.testing.assert_array_equal(f["n_pairs"][0, ic], np.asarray(full_r["n_pairs"][conv]))
            np.testing.assert_allclose(f["pair_fraction"][0, ic],
                                       np.asarray(full_r["pair_fraction"][conv]),
                                       rtol=1e-14, atol=0)
            np.testing.assert_allclose(f["pair_fraction_err"][0, ic],
                                       np.asarray(full_r["pair_fraction_err"][conv]),
                                       rtol=1e-14, atol=0)
            assert int(f["n_excluded_pairs"][0, ic]) == int(full_r["n_excluded_pairs"][conv])
    np.testing.assert_array_equal(np.asarray(r["n_galaxies"]), np.asarray(full_r["n_galaxies"]))
    for conv in ALL_CONVENTIONS:
        np.testing.assert_array_equal(np.asarray(r["n_pairs"][conv]),
                                      np.asarray(full_r["n_pairs"][conv]))
        np.testing.assert_allclose(np.asarray(r["pair_fraction"][conv]),
                                   np.asarray(full_r["pair_fraction"][conv]),
                                   rtol=1e-14, atol=0)
        np.testing.assert_allclose(np.asarray(r["pair_fraction_err"][conv]),
                                   np.asarray(full_r["pair_fraction_err"][conv]),
                                   rtol=1e-14, atol=0)
        assert int(r["n_excluded_pairs"][conv]) == int(full_r["n_excluded_pairs"][conv])


@pytest.mark.parametrize("name,mutate,override", [
    ("missing_data", lambda c: os.remove(PB._data_path(2.0, c)), None),
    ("missing_results", lambda c: os.remove(PB._results_path(2.0, c)), None),
    ("bad_redshift", None, {"redshift": 9.0}),
    ("bad_mass_ratio_min", None, {"mass_ratio_min": 0.25}),
    ("bad_max_sep", None, {"max_sep_kpc": 50.0}),
    ("malformed_redshift", None, {"redshift": "2.0"}),
])
def test_B19_preflight_leaves_sentinel_untouched(tmp_path, name, mutate, override):
    c = tmp_cfg(tmp_path / name, redshifts=[2.0])
    write_snapshot(c, 2.0, FIX_GALAXIES, FIX_PRIMARY, FIX_SECONDARY,
                   attr_overrides=override)
    path, digest = sentinel(c)
    if mutate is not None:
        mutate(c)
    assert rejects(PB.run_binning_comparison, c) == "assert", name
    assert sha(path) == digest, name
    msg = reject_message(PB.run_binning_comparison, c)
    assert msg, f"assertion for {name} carried no message"


def test_B19b_preflight_checks_every_configured_redshift_before_writing(tmp_path):
    """spec.md Part 3: 'preflight every configured redshift' before opening
    the output. A single-redshift fixture (test_B19) can't distinguish an
    all-upfront preflight from one that starts writing after checking only
    the first snapshot -- so break only the SECOND of two redshifts."""
    breakages = [
        ("missing_data_z2", lambda c: os.remove(PB._data_path(3.0, c)), None),
        ("missing_results_z2", lambda c: os.remove(PB._results_path(3.0, c)), None),
        ("bad_redshift_z2", None, {"redshift": 9.0}),
        ("bad_mass_ratio_min_z2", None, {"mass_ratio_min": 0.25}),
        ("malformed_redshift_z2", None, {"redshift": "3.0"}),
    ]
    for name, mutate, override in breakages:
        c = tmp_cfg(tmp_path / name, redshifts=[2.0, 3.0])
        write_snapshot(c, 2.0, FIX_GALAXIES, FIX_PRIMARY, FIX_SECONDARY)
        write_snapshot(c, 3.0, FIX_GALAXIES, FIX_PRIMARY, FIX_SECONDARY,
                       attr_overrides=override)
        path, digest = sentinel(c)
        if mutate is not None:
            mutate(c)
        assert rejects(PB.run_binning_comparison, c) == "assert", name
        assert sha(path) == digest, name


@pytest.mark.parametrize("bad", [[], ["primary", "primary"], ["mean"], ["nonsense"], [7], "primary"])
def test_B20_invalid_conventions_leaves_sentinel_untouched(tmp_path, bad):
    c = tmp_cfg(tmp_path, redshifts=[2.0])
    write_snapshot(c, 2.0, FIX_GALAXIES, FIX_PRIMARY, FIX_SECONDARY)
    path, digest = sentinel(c)
    c["pair_binning_conventions"] = bad
    assert rejects(PB.run_binning_comparison, c) == "assert", bad
    assert sha(path) == digest, bad
    msg = reject_message(PB.run_binning_comparison, c)
    assert msg, f"assertion for pair_binning_conventions={bad!r} carried no message"


def test_B21_console_summary_fields(mock):
    results, out = quiet(PB.run_binning_comparison, mock)
    assert norm(HEADING_SENTENCE) in norm(out)
    lines = out.splitlines()
    for iz, z in enumerate(mock["redshifts"]):
        ztok = f"z={z:.1f}"
        for conv in mock["pair_binning_conventions"]:
            matches = lines_with_tokens(lines, ztok, f"convention={conv}")
            assert len(matches) == 1, (z, conv, matches)
            line = matches[0]
            got = {}
            for token in ("n_galaxies", "n_pairs", "n_excluded"):
                m = re.search(rf"\b{token}=(-?\d+)\b", line)
                assert m, (token, line)
                got[token] = int(m.group(1))
            assert got["n_galaxies"] == int(np.sum(np.asarray(results[iz]["n_galaxies"])))
            assert got["n_pairs"] == int(np.sum(np.asarray(results[iz]["n_pairs"][conv])))
            assert got["n_excluded"] == int(results[iz]["n_excluded_pairs"][conv])
        add = [ln for ln in lines if ztok in line_tokens(ln)
               and any(t.startswith("additivity=") for t in line_tokens(ln))]
        assert len(add) == 1, (z, add)
        assert re.search(r"\badditivity=holds\b", add[0]), add[0]


def test_B21b_console_line_selection_is_token_exact_not_substring(mock):
    """spec.md's tokens are whitespace-delimited key/value pairs. A line
    selector using naive substring matching (e.g. 'z=2.0' in line) would
    false-positive against an unrelated label like 'notz=2.0' or
    'not_convention=primary' that merely contains the token as a substring."""
    _, out = quiet(PB.run_binning_comparison, mock)
    lines = out.splitlines()
    decoy = "notz=2.0 not_convention=primary xn_galaxies=999"
    poisoned = lines + [decoy]
    z = mock["redshifts"][0]
    ztok = f"z={z:.1f}"
    matches = lines_with_tokens(poisoned, ztok, "convention=primary")
    assert decoy not in matches, "token matching must not substring-match a decoy line"


def test_B22_console_reports_not_checked_for_partial_convention_set(mock, tmp_path):
    c = cfg(data_dir=mock["data_dir"],
            results_dir=str(tmp_path / "partial") + os.sep,
            pair_binning_conventions=["primary", "either"])
    os.makedirs(c["results_dir"], exist_ok=True)
    for z in c["redshifts"]:
        with open(PB._results_path(z, mock), "rb") as src, \
                open(PB._results_path(z, c), "wb") as dst:
            dst.write(src.read())
    _, out = quiet(PB.run_binning_comparison, c)
    lines = out.splitlines()
    for z in c["redshifts"]:
        ztok = f"z={z:.1f}"
        add = [ln for ln in lines if ztok in line_tokens(ln)
               and any(t.startswith("additivity=") for t in line_tokens(ln))]
        assert len(add) == 1, (z, add)
        assert re.search(r"\badditivity=not_checked\b", add[0]), add[0]


def test_B23_provenance_compared_against_config_not_defaults(tmp_path):
    """A provenance check hardcoding 0.1 / 25.0 passes only under the default config."""
    c = tmp_cfg(tmp_path / "nondefault", redshifts=[2.0], mass_ratio_min=0.25, max_sep=15.0)
    write_snapshot(c, 2.0, FIX_GALAXIES, FIX_PRIMARY, FIX_SECONDARY)
    got = PB.load_snapshot_counts(2.0, c)
    for conv in ALL_CONVENTIONS:
        assert list(np.asarray(got["n_pairs"][conv])) == FIX_EXPECT[conv], conv

    # ... and under that config it is the *default* recorded cuts that disagree.
    c2 = tmp_cfg(tmp_path / "defaultattrs", redshifts=[2.0],
                 mass_ratio_min=0.25, max_sep=15.0)
    write_snapshot(c2, 2.0, FIX_GALAXIES, FIX_PRIMARY, FIX_SECONDARY,
                   attr_overrides={"mass_ratio_min": 0.1, "max_sep_kpc": 25.0})
    assert rejects(PB.load_snapshot_counts, 2.0, c2) == "assert"


# ------------------------------------------ additivity actually consulted

def test_B24_additivity_false_from_check_propagates_everywhere(fixture_cfg, monkeypatch):
    """spec.md section 7: additivity_holds must be genuinely derived from
    check_additivity's return value, not hardcoded to True. Every fixture in
    this file satisfies the identity by construction (it is a theorem, true
    on any valid pair sample -- spec.md section 7), so no real dataset can
    ever exercise a driver's False branch; only monkeypatching
    check_additivity itself can distinguish a driver that truly consults it
    from one that just writes 'OK' regardless."""
    monkeypatch.setattr(PB, "check_additivity", lambda *a, **k: False)
    results, out = quiet(PB.run_binning_comparison, fixture_cfg)
    assert results[0]["additivity_holds"] is False

    path = os.path.join(fixture_cfg["results_dir"], "pair_binning.hdf5")
    with h5py.File(path, "r") as f:
        assert bool(f.attrs["additivity_checked"]) is True
        assert bool(f.attrs["additivity_holds"]) is False

    lines = out.splitlines()
    add = [ln for ln in lines if "z=2.0" in line_tokens(ln)
           and any(t.startswith("additivity=") for t in line_tokens(ln))]
    assert len(add) == 1, add
    assert re.search(r"\badditivity=FAILED\b", add[0]), add[0]


# -------------------------------------------- full driver, nondefault grid

def test_B26_full_driver_run_on_nondefault_bin_grid(tmp_path):
    """spec.md Part 1's alternate-grid pin ([9.0, 12.0) width 1.5 -> edges
    [9.0, 10.5, 12.0]), exercised through the FULL driver rather than only
    the Part 1 pure functions (test_A27's job). Neither existing hB test
    varies the bin grid, so a driver that silently reverts to the default
    [8,11)/0.5 grid -- even if every Part 1 function honours config -- would
    otherwise pass every driver-level test in this file."""
    c = tmp_cfg(tmp_path, redshifts=[2.0],
                log_mass_min=9.0, log_mass_max=12.0, mass_bin_width=1.5)
    galaxies = np.array([8.9, 9.0, 10.4, 10.5, 11.9, 12.0, 10.6, 11.0, 9.5, 10.0])
    p = np.array([10.6, 11.0])
    s = np.array([9.5, 10.0])
    write_snapshot(c, 2.0, galaxies, p, s)

    results, _ = quiet(PB.run_binning_comparison, c)
    r = results[0]
    nb = nbins(c)
    assert nb == 2

    catalog = load_galaxy_catalog(PB._data_path(2.0, c), c)
    bp, bs = ref_bins(p, c), ref_bins(s, c)
    expected = {
        "primary": ref_counts([bp], nb),
        "secondary": ref_counts([bs], nb),
        "either": ref_counts([bp, bs], nb),
    }
    expected_gal = ref_counts([ref_bins(catalog["log_stellar_mass"], c)], nb)

    np.testing.assert_array_equal(np.asarray(r["n_galaxies"]), expected_gal)
    for conv in ALL_CONVENTIONS:
        np.testing.assert_array_equal(np.asarray(r["n_pairs"][conv]), expected[conv], err_msg=conv)
    assert int(r["n_excluded_pairs"]["primary"]) == int(np.count_nonzero(bp == -1))
    assert int(r["n_excluded_pairs"]["secondary"]) == int(np.count_nonzero(bs == -1))
    assert int(r["n_excluded_pairs"]["either"]) == int(np.count_nonzero((bp == -1) & (bs == -1)))
    for conv in ALL_CONVENTIONS:
        with np.errstate(divide="ignore", invalid="ignore"):
            expected_frac = np.where(expected_gal > 0,
                                     expected[conv] / np.where(expected_gal > 0, expected_gal, 1),
                                     0.0)
        np.testing.assert_allclose(np.asarray(r["pair_fraction"][conv]), expected_frac,
                                   rtol=1e-14, atol=0)

    path = os.path.join(c["results_dir"], "pair_binning.hdf5")
    with h5py.File(path, "r") as f:
        assert f["n_galaxies"].shape == (1, nb)
        assert f["n_pairs"].shape == (1, 3, nb)
        assert f["pair_fraction"].shape == (1, 3, nb)
        np.testing.assert_allclose(np.asarray(f.attrs["mass_bin_edges"], dtype=float),
                                   [9.0, 10.5, 12.0], rtol=0, atol=0)
        np.testing.assert_array_equal(f["n_galaxies"][0], expected_gal)
        for ic, conv in enumerate(ALL_CONVENTIONS):
            np.testing.assert_array_equal(f["n_pairs"][0, ic], expected[conv])


# --------------------------------------- mass-ratio cut not reapplied (driver)

def test_B27_low_mass_ratio_pair_not_refiltered(tmp_path):
    """spec.md section 1: stored pairs are used unchanged -- Part 1 imposes
    no mass-ratio restriction. Every other pair fixture in this file sits
    above the default mass_ratio_min=0.1, so a load_snapshot_counts that
    silently reapplied that cut would still pass every other hB test."""
    c = tmp_cfg(tmp_path, redshifts=[2.0])
    p = np.array([10.0])
    s = np.array([8.0])
    ratio = 10.0 ** (float(s[0]) - float(p[0]))
    assert ratio < c["mass_ratio_min"], ratio
    galaxies = np.concatenate([p, s, FIX_FIELD])
    write_snapshot(c, 2.0, galaxies, p, s)

    got = PB.load_snapshot_counts(2.0, c)
    assert list(np.asarray(got["n_pairs"]["primary"])) == [0, 0, 0, 0, 1, 0]
    assert list(np.asarray(got["n_pairs"]["secondary"])) == [1, 0, 0, 0, 0, 0]
    assert list(np.asarray(got["n_pairs"]["either"])) == [1, 0, 0, 0, 1, 0]
    assert got["n_pairs_total"] == 1
