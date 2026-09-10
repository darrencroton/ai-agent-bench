"""Hidden Harness B: integration criteria (provenance, atomicity, schema,
end-to-end science).

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
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import h5py
import numpy as np
import pytest

import calc
import config as cfgmod
from data_reader import load_galaxy_catalog
from generate_test_data import generate_all_snapshots
from pair_finder import find_pairs

try:
    import merger_rate as MR
except Exception as e:                      # pragma: no cover
    MR = None
    _MR_ERR = e

BASE = cfgmod.config


def cfg(**kw):
    c = copy.deepcopy(BASE); c.update(kw); return c


def nbins(c=BASE):
    return int(round((c["log_mass_max"] - c["log_mass_min"]) / c["mass_bin_width"]))


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def assert_iso_timestamp(value):
    assert isinstance(value, str) and value
    parsed = datetime.datetime.fromisoformat(value)
    assert parsed.tzinfo is not None


@pytest.fixture(scope="module")
def mock(tmp_path_factory):
    root = tmp_path_factory.mktemp("e2e")
    c = cfg(data_dir=str(root / "data") + os.sep,
            results_dir=str(root / "results") + os.sep,
            figures_dir=str(root / "figures") + os.sep)
    os.makedirs(c["data_dir"], exist_ok=True)
    os.makedirs(c["results_dir"], exist_ok=True)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        generate_all_snapshots(c)
        calc.run_calculation(c)
    return c


def test_E01_slice1_additive_schema(mock):
    c = mock
    for z in c["redshifts"]:
        cat = load_galaxy_catalog(os.path.join(c["data_dir"], f"test_z{z:.1f}.hdf5"), c)
        expected_pairs = find_pairs(cat, c)
        with h5py.File(MR._results_path(z, c), "r") as f:
            for d in ("mass_primary", "mass_secondary", "mass_ratio", "separation_kpc",
                      "delta_v", "mass_bin", "sep_bin", "n_galaxies_per_mass_bin"):
                assert d in f, (z, d)
            for a in ("redshift", "n_pairs", "timestamp", "mass_bin_by",
                      "mass_ratio_min", "max_sep_kpc", "box_size_mpc"):
                assert a in f.attrs, (z, a)
            ng = f["n_galaxies_per_mass_bin"][...]
            assert ng.ndim == 1 and len(ng) == nbins(c)
            assert np.asarray(ng).dtype.kind in "iu"
            for name, expected in expected_pairs.items():
                np.testing.assert_array_equal(f[name][...], expected, err_msg=f"z={z}, dataset={name}")
            assert float(f.attrs["redshift"]) == float(z)
            assert int(f.attrs["n_pairs"]) == len(expected_pairs["mass_bin"])
            assert f.attrs["mass_bin_by"] == c["mass_bin_by"]
            assert float(f.attrs["mass_ratio_min"]) == float(c["mass_ratio_min"])
            assert float(f.attrs["max_sep_kpc"]) == float(c["max_sep"])
            assert float(f.attrs["box_size_mpc"]) == float(c["box_size"])
            assert_iso_timestamp(f.attrs["timestamp"])


def test_E02_denominator_from_full_catalog(mock):
    c = mock
    for z in c["redshifts"]:
        cat = load_galaxy_catalog(os.path.join(c["data_dir"], f"test_z{z:.1f}.hdf5"), c)
        m = np.asarray(cat["log_stellar_mass"])
        edges = np.linspace(c["log_mass_min"], c["log_mass_max"], nbins(c) + 1)
        raw = np.digitize(m, edges) - 1
        valid = raw[(raw >= 0) & (raw < nbins(c))]
        expect = np.bincount(valid, minlength=nbins(c)).astype(np.int64)
        with h5py.File(MR._results_path(z, c), "r") as f:
            got = f["n_galaxies_per_mass_bin"][...]
        np.testing.assert_array_equal(got, expect, err_msg=f"z={z}")
        npairs_total = 0
        with h5py.File(MR._results_path(z, c), "r") as f:
            npairs_total = len(f["mass_bin"][...])
        assert int(np.sum(got)) > npairs_total


def test_E03_box_size_from_catalog_not_config(tmp_path):
    """Part 1 AC: box_size_mpc provably comes from catalog['box_size']."""
    c = cfg(data_dir=str(tmp_path / "d") + os.sep,
            results_dir=str(tmp_path / "r") + os.sep,
            figures_dir=str(tmp_path / "f") + os.sep,
            redshifts=[2.0])
    os.makedirs(c["data_dir"], exist_ok=True)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        generate_all_snapshots(c)
    p = os.path.join(c["data_dir"], "test_z2.0.hdf5")
    with h5py.File(p, "r+") as f:
        f.attrs["box_size"] = 1000.0
    with contextlib.redirect_stdout(buf):
        calc.run_calculation(c)
    with h5py.File(MR._results_path(2.0, c), "r") as f:
        assert float(f.attrs["box_size_mpc"]) == 1000.0, float(f.attrs["box_size_mpc"])


def _write_slice1_file(path, box, z, nb=6, npairs=5):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with h5py.File(path, "w") as f:
        f.create_dataset("mass_primary", data=np.full(npairs, 10.0))
        f.create_dataset("mass_secondary", data=np.full(npairs, 9.0))
        f.create_dataset("mass_ratio", data=np.full(npairs, 0.5))
        f.create_dataset("separation_kpc", data=np.full(npairs, 10.0))
        f.create_dataset("delta_v", data=np.full(npairs, 100.0))
        f.create_dataset("sep_bin", data=np.zeros(npairs, dtype=np.int64))
        f.create_dataset("mass_bin", data=np.zeros(npairs, dtype=np.int64))
        f.create_dataset("n_galaxies_per_mass_bin",
                         data=np.array([10] + [0] * (nb - 1), dtype=np.int64))
        f.attrs["redshift"] = z
        f.attrs["n_pairs"] = npairs
        f.attrs["timestamp"] = "x"
        f.attrs["mass_bin_by"] = "primary"
        f.attrs["mass_ratio_min"] = 0.1
        f.attrs["max_sep_kpc"] = 25.0
        f.attrs["box_size_mpc"] = box


def test_E04_per_file_box_size_used(tmp_path):
    """Part 2 AC: fixture box 250.0 vs config box 500.0, single redshift."""
    c = cfg(results_dir=str(tmp_path) + os.sep, redshifts=[2.0], box_size=500.0)
    _write_slice1_file(MR._results_path(2.0, c), 250.0, 2.0)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        MR.run_merger_rate_calculation(c)
    with h5py.File(os.path.join(c["results_dir"], "merger_rate.hdf5"), "r") as f:
        rate = f["merger_rate"][...]
    T = c["merger_timescale_gyr0"] * (1 + 2.0) ** c["merger_timescale_alpha"]
    expect = c["merger_fraction"] * 5 / (250.0 ** 3 * T)
    assert abs(float(rate[0, 0]) - expect) / expect < 1e-12, (float(rate[0, 0]), expect)


def test_E05_preflight_atomicity_sha256(tmp_path):
    """Sentinel merger_rate.hdf5 must be byte-identical after every preflight failure."""
    cases = []
    d = tmp_path / "a"; d.mkdir()
    c = cfg(results_dir=str(d) + os.sep, redshifts=[2.0, 3.0])
    _write_slice1_file(MR._results_path(2.0, c), 500.0, 2.0)
    cases.append(("missing_file", c))
    d = tmp_path / "b"; d.mkdir()
    c = cfg(results_dir=str(d) + os.sep, redshifts=[2.0])
    _write_slice1_file(MR._results_path(2.0, c), 500.0, 9.0)
    cases.append(("z_mismatch", c))
    d = tmp_path / "c"; d.mkdir()
    c = cfg(results_dir=str(d) + os.sep, redshifts=[2.0])
    p = MR._results_path(2.0, c); _write_slice1_file(p, 500.0, 2.0)
    with h5py.File(p, "r+") as f:
        del f.attrs["redshift"]; f.attrs["redshift"] = "2.0"
    cases.append(("z_string", c))
    d = tmp_path / "dd"; d.mkdir()
    c = cfg(results_dir=str(d) + os.sep, redshifts=[2.0])
    p = MR._results_path(2.0, c); _write_slice1_file(p, 500.0, 2.0)
    with h5py.File(p, "r+") as f:
        del f.attrs["redshift"]; f.attrs["redshift"] = np.array([2.0, 3.0])
    cases.append(("z_vector", c))
    d = tmp_path / "e"; d.mkdir()
    c = cfg(results_dir=str(d) + os.sep, redshifts=[2.0])
    p = MR._results_path(2.0, c); _write_slice1_file(p, 500.0, 2.0)
    with h5py.File(p, "r+") as f:
        del f.attrs["redshift"]; f.attrs["redshift"] = 2.0 + 0.0j
    cases.append(("z_complex", c))
    d = tmp_path / "f"; d.mkdir()
    c = cfg(results_dir=str(d) + os.sep, redshifts=[2.0])
    p = MR._results_path(2.0, c); _write_slice1_file(p, 500.0, 2.0)
    with h5py.File(p, "r+") as f:
        del f.attrs["redshift"]; f.attrs["redshift"] = True
    cases.append(("z_bool", c))
    d = tmp_path / "g"; d.mkdir()
    c = cfg(results_dir=str(d) + os.sep, redshifts=[2.0])
    p = MR._results_path(2.0, c); _write_slice1_file(p, 500.0, 2.0)
    with h5py.File(p, "r+") as f:
        del f.attrs["redshift"]
    cases.append(("z_missing", c))

    failures = []
    for name, c in cases:
        sentinel = os.path.join(c["results_dir"], "merger_rate.hdf5")
        with open(sentinel, "wb") as fh:
            fh.write(b"SENTINEL-DO-NOT-TOUCH")
        before = sha(sentinel)
        buf = io.StringIO()
        raised = None
        try:
            with contextlib.redirect_stdout(buf):
                MR.run_merger_rate_calculation(c)
        except AssertionError:
            raised = "assert"
        except Exception as e:
            raised = type(e).__name__
        after = sha(sentinel)
        if raised != "assert":
            failures.append((name, "exception", raised))
        if before != after:
            failures.append((name, "sentinel_modified", None))
    assert not failures, failures


def test_E06_output_schema(mock):
    c = mock
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        MR.run_merger_rate_calculation(c)
    p = os.path.join(c["results_dir"], "merger_rate.hdf5")
    with h5py.File(p, "r") as f:
        for d in ("pair_fraction", "n_pairs", "merger_rate", "merger_rate_err"):
            assert d in f, d
            assert f[d].shape == (len(c["redshifts"]), nbins(c)), (d, f[d].shape)
        assert f["n_pairs"].dtype.kind in "iu"
        for a in ("redshifts", "mass_bin_by", "merger_fraction",
                  "merger_timescale_gyr0", "merger_timescale_alpha", "timestamp"):
            assert a in f.attrs, a
        assert list(np.asarray(f.attrs["redshifts"], dtype=float)) == list(map(float, c["redshifts"]))
        assert f.attrs["mass_bin_by"] == c["mass_bin_by"]
        assert float(f.attrs["merger_fraction"]) == float(c["merger_fraction"])
        assert float(f.attrs["merger_timescale_gyr0"]) == float(c["merger_timescale_gyr0"])
        assert float(f.attrs["merger_timescale_alpha"]) == float(c["merger_timescale_alpha"])
        assert_iso_timestamp(f.attrs["timestamp"])
        pair_fraction = f["pair_fraction"][...]
        n_pairs = f["n_pairs"][...]
        r = f["merger_rate"][...]; e = f["merger_rate_err"][...]
        assert np.all(np.isfinite(r)) and np.all(r >= 0)
        assert np.all(np.isfinite(e)) and np.all(e >= 0)
        for iz, z in enumerate(c["redshifts"]):
            with h5py.File(MR._results_path(z, c), "r") as pf:
                mass_bin = pf["mass_bin"][...]
                ngal = pf["n_galaxies_per_mass_bin"][...]
                box = float(pf.attrs["box_size_mpc"])
            expected_pairs = np.array(
                [np.sum(mass_bin == b) for b in range(nbins(c))], dtype=np.int64)
            expected_fraction = np.divide(
                expected_pairs, ngal, out=np.zeros(nbins(c), dtype=float), where=ngal > 0)
            expected_sigma_fraction = np.divide(
                expected_fraction, np.sqrt(expected_pairs),
                out=np.zeros(nbins(c), dtype=float), where=expected_pairs > 0)
            timescale = (c["merger_timescale_gyr0"]
                         * (1.0 + z) ** c["merger_timescale_alpha"])
            denom = box ** 3 * timescale
            expected_rate = c["merger_fraction"] * expected_fraction * ngal / denom
            expected_err = c["merger_fraction"] * expected_sigma_fraction * ngal / denom
            np.testing.assert_array_equal(n_pairs[iz], expected_pairs)
            np.testing.assert_allclose(
                pair_fraction[iz], expected_fraction, rtol=1e-14, atol=0)
            np.testing.assert_allclose(r[iz], expected_rate, rtol=1e-14, atol=0)
            np.testing.assert_allclose(e[iz], expected_err, rtol=1e-14, atol=0)


def test_E07_end_to_end_science(mock):
    c = mock
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        MR.run_merger_rate_calculation(c)
        res = MR.run_merger_rate_validation(c)
    expected = -c["merger_timescale_alpha"]
    checked = 0
    for d in res:
        if d["consistent"] is None:
            continue
        checked += 1
        assert d["consistent"] is True, d
        assert abs(d["slope"] - expected) < 0.4, d
        assert d["expected_slope"] == expected
    assert checked == nbins(c), checked
    print("SLOPES " + " ".join(f"{d['slope']:+.4f}" for d in res))


def test_E09_expected_slope_tracks_nondefault_alpha(mock):
    """report 04's M18: expected_slope must be derived from config at call
    time, not hardcoded anywhere in the call chain -- the one mutation that
    survived in 10 of 12 prior branches. Recompute with a distinct alpha and
    confirm the validation checks against THAT value, not the default -1.0."""
    c = mock
    c2 = copy.deepcopy(c)
    c2["merger_timescale_alpha"] = -0.7
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        MR.run_merger_rate_calculation(c2)
        res = MR.run_merger_rate_validation(c2)
    expected = -c2["merger_timescale_alpha"]
    assert abs(expected - 0.7) < 1e-12
    checked = 0
    for d in res:
        if d["consistent"] is None:
            continue
        checked += 1
        assert d["expected_slope"] == expected, \
            f"expected_slope={d['expected_slope']!r} did not track alpha=-0.7 (hardcoded expected_slope?)"
        assert d["consistent"] is True, d
        assert abs(d["slope"] - expected) < 0.4, d
    assert checked == nbins(c), "not every bin had enough usable points -- fixture problem, not a pass"
