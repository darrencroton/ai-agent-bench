"""Reference test suite for merger_rate.py -- smoke-test fixture only.

Written to validate the harness's mutation gate and hidden-test scoring, not
as an exemplar of what a Developer model should submit.
"""
import contextlib
import copy
import decimal
import hashlib
import inspect
import io
import math
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import h5py
import merger_rate as MR
import numpy as np

import calc
import config as cfgmod
from data_reader import load_galaxy_catalog
from generate_test_data import generate_all_snapshots

BASE = cfgmod.config


def cfg(**kw):
    c = copy.deepcopy(BASE)
    c.update(kw)
    return c


def nbins(c=BASE):
    return int(round((c["log_mass_max"] - c["log_mass_min"]) / c["mass_bin_width"]))


def rejects(fn, *a, **k):
    try:
        fn(*a, **k)
    except AssertionError:
        return "assert"
    except Exception as e:
        return type(e).__name__
    return None


def test_count_galaxies_pinned():
    got = calc._count_galaxies_per_mass_bin(
        np.array([7.9, 8.0, 8.5, 10.999, 11.0, 11.1]), BASE)
    assert list(np.asarray(got)) == [1, 1, 0, 0, 0, 1]
    assert np.asarray(got).dtype.kind in "iu"


def test_pair_fraction_pinned():
    f, s = MR.compute_pair_fraction(np.array([0, 5, 20]), np.array([10, 10, 10]))
    np.testing.assert_allclose(f, [0.0, 0.5, 2.0], rtol=1e-14, atol=0)
    np.testing.assert_allclose(s[1:], [0.22360679774997896, 0.4472135954999579],
                               rtol=1e-14, atol=0)


def test_pair_fraction_zero_zero_exact():
    f, s = MR.compute_pair_fraction(np.array([0]), np.array([0]))
    assert f[0] == 0.0 and s[0] == 0.0


def test_pair_fraction_rejections():
    assert rejects(MR.compute_pair_fraction, np.array([1, 2]), np.array([1])) == "assert"
    assert rejects(MR.compute_pair_fraction, np.array([[1, 2]]), np.array([1, 2])) == "assert"
    assert rejects(MR.compute_pair_fraction, np.array([1, 2]), np.array([[1, 2]])) == "assert"
    assert rejects(MR.compute_pair_fraction, np.array([-1]), np.array([10])) == "assert"
    assert rejects(MR.compute_pair_fraction, np.array([np.nan]), np.array([10.0])) == "assert"
    assert rejects(MR.compute_pair_fraction, np.array([1.5]), np.array([10.0])) == "assert"
    assert rejects(MR.compute_pair_fraction, np.array([1]), np.array([np.nan])) == "assert"
    assert rejects(MR.compute_pair_fraction, np.array([1]), np.array([-10])) == "assert"
    assert rejects(MR.compute_pair_fraction, np.array([1]), np.array([10.5])) == "assert"
    assert rejects(MR.compute_pair_fraction, np.array([1]), np.array([0])) == "assert"


def _write_pairs_file(path, mass_bin, n_gal, box=500.0, z=2.0):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    n = len(mass_bin)
    with h5py.File(path, "w") as f:
        f.create_dataset("mass_primary", data=np.full(n, 10.0))
        f.create_dataset("mass_secondary", data=np.full(n, 9.0))
        f.create_dataset("mass_ratio", data=np.full(n, 0.5))
        f.create_dataset("separation_kpc", data=np.full(n, 10.0))
        f.create_dataset("delta_v", data=np.full(n, 100.0))
        f.create_dataset("sep_bin", data=np.zeros(n, dtype=np.int64))
        f.create_dataset("mass_bin", data=np.asarray(mass_bin, dtype=np.int64))
        f.create_dataset("n_galaxies_per_mass_bin", data=np.asarray(n_gal, dtype=np.int64))
        f.attrs["redshift"] = z
        f.attrs["n_pairs"] = n
        f.attrs["timestamp"] = "x"
        f.attrs["mass_bin_by"] = "primary"
        f.attrs["mass_ratio_min"] = 0.1
        f.attrs["max_sep_kpc"] = 25.0
        f.attrs["box_size_mpc"] = box


def test_load_pair_counts_values(tmp_path):
    c = cfg(results_dir=str(tmp_path) + os.sep)
    _write_pairs_file(MR._results_path(2.0, c), [0, 0, 1, 5, -1, -1, 3],
                       [7, 8, 9, 10, 11, 12], box=321.0)
    npair, ngal, box = MR._load_pair_counts(2.0, c)
    assert list(np.asarray(npair)) == [2, 1, 0, 1, 0, 1]
    assert float(box) == 321.0


def test_load_pair_counts_rejects_string_box_and_needs_no_mass_bin_by(tmp_path):
    c = cfg(results_dir=str(tmp_path) + os.sep)
    c.pop("mass_bin_by")
    path = MR._results_path(2.0, c)
    _write_pairs_file(path, [0], [1] * 6)
    with h5py.File(path, "r+") as f:
        del f.attrs["box_size_mpc"]
        f.attrs["box_size_mpc"] = "500.0"
    assert rejects(MR._load_pair_counts, 2.0, c) == "assert"


def test_timescale_at_zero_exact():
    assert MR.merger_timescale_gyr(0, BASE) == BASE["merger_timescale_gyr0"]


def test_timescale_pinned():
    c = cfg(merger_timescale_gyr0=2.5, merger_timescale_alpha=-0.5)
    np.testing.assert_allclose(MR.merger_timescale_gyr(3, c), 1.25,
                               rtol=1e-14, atol=0)


def test_timescale_rejections():
    for z in (-1.0, -2.0, float("nan"), float("inf")):
        assert rejects(MR.merger_timescale_gyr, z, BASE) == "assert"
    assert rejects(MR.merger_timescale_gyr, "1.0", BASE) == "assert"
    assert rejects(MR.merger_timescale_gyr, np.array([1.0, 2.0]), BASE) == "assert"
    assert rejects(MR.merger_timescale_gyr, 1.0, cfg(merger_timescale_gyr0=0.0)) == "assert"
    for key in ("merger_timescale_gyr0", "merger_timescale_alpha"):
        for bad in ("1.0", np.array(1.0), np.array([1.0]), 1.0 + 0.0j, True):
            assert rejects(MR.merger_timescale_gyr, 1.0, cfg(**{key: bad})) == "assert"
    assert rejects(MR.merger_timescale_gyr, 1.0,
                   cfg(merger_timescale_alpha=float("nan"))) == "assert"
    assert rejects(MR.merger_timescale_gyr, 1.0,
                   cfg(merger_timescale_gyr0=float("nan"))) == "assert"


def test_merger_rate_pinned():
    r, s = MR.compute_merger_rate(np.array([0.5]), np.array([0.1]), np.array([10]),
                                   500.0, 2.2, 0.6)
    np.testing.assert_allclose(r[0], 1.090909090909091e-08, rtol=1e-14, atol=0)
    np.testing.assert_allclose(s[0], 2.181818181818182e-09, rtol=1e-14, atol=0)


def test_merger_rate_zero_sigma_exact():
    r, s = MR.compute_merger_rate(np.array([0.5, 0.0]), np.array([0.0, 0.0]),
                                   np.array([10, 10]), 500.0, 2.2, 0.6)
    assert float(np.asarray(s)[0]) == 0.0 and float(np.asarray(s)[1]) == 0.0


def test_merger_rate_rejections():
    ok = (np.array([0.5]), np.array([0.1]), np.array([10]))
    assert rejects(MR.compute_merger_rate, *ok, 0.0, 2.2, 0.6) == "assert"
    assert rejects(MR.compute_merger_rate, *ok, float("nan"), 2.2, 0.6) == "assert"
    assert rejects(MR.compute_merger_rate, *ok, 500.0, 0.0, 0.6) == "assert"
    assert rejects(MR.compute_merger_rate, *ok, 500.0, float("nan"), 0.6) == "assert"
    assert rejects(MR.compute_merger_rate, *ok, 500.0, 2.2, 1.5) == "assert"
    assert rejects(MR.compute_merger_rate, *ok, 500.0, 2.2, float("nan")) == "assert"
    assert rejects(MR.compute_merger_rate, *ok, 500.0, 2.2, 0.0) == "assert"
    assert rejects(MR.compute_merger_rate, np.array([0.5]), np.array([0.1]),
                    np.array([0]), 500.0, 2.2, 0.6) == "assert"
    assert rejects(MR.compute_merger_rate, np.array([[0.5]]), np.array([0.1]),
                   np.array([10]), 500.0, 2.2, 0.6) == "assert"
    assert rejects(MR.compute_merger_rate, np.array([0.5]), np.array([[0.1]]),
                   np.array([10]), 500.0, 2.2, 0.6) == "assert"
    assert rejects(MR.compute_merger_rate, np.array([0.5]), np.array([0.1]),
                   np.array([[10]]), 500.0, 2.2, 0.6) == "assert"
    assert rejects(MR.compute_merger_rate, np.array([0.5, 0.5]), np.array([0.1]),
                   np.array([10]), 500.0, 2.2, 0.6) == "assert"
    assert rejects(MR.compute_merger_rate, np.array([-0.5]), np.array([0.1]),
                   np.array([10]), 500.0, 2.2, 0.6) == "assert"
    assert rejects(MR.compute_merger_rate, np.array([np.nan]), np.array([0.1]),
                   np.array([10]), 500.0, 2.2, 0.6) == "assert"
    assert rejects(MR.compute_merger_rate, np.array([0.5]), np.array([np.nan]),
                   np.array([10]), 500.0, 2.2, 0.6) == "assert"
    assert rejects(MR.compute_merger_rate, np.array([0.5]), np.array([-0.1]),
                   np.array([10]), 500.0, 2.2, 0.6) == "assert"
    assert rejects(MR.compute_merger_rate, np.array([0.5]), np.array([0.1]),
                   np.array([np.nan]), 500.0, 2.2, 0.6) == "assert"
    assert rejects(MR.compute_merger_rate, np.array([0.5]), np.array([0.1]),
                   np.array([-10]), 500.0, 2.2, 0.6) == "assert"
    assert rejects(MR.compute_merger_rate, np.array([0.5]), np.array([0.1]),
                   np.array([10.5]), 500.0, 2.2, 0.6) == "assert"


def test_merger_rate_rejects_string_box():
    r = rejects(MR.compute_merger_rate, np.array([0.5]), np.array([0.1]),
                np.array([10]), "500.0", 2.2, 0.6)
    assert r == "assert"
    for position in (3, 4, 5):
        args = [np.array([0.5]), np.array([0.1]), np.array([10]), 500.0, 2.2, 0.6]
        args[position] = np.array(args[position])
        assert rejects(MR.compute_merger_rate, *args) == "assert"


def test_required_uncertainty_docstrings():
    required = ("Uncertainty follows Task 001's plug-in Poisson-error convention; "
                "it is not a confidence interval.")
    for fn in (MR.compute_pair_fraction, MR.compute_merger_rate):
        assert required in inspect.getdoc(fn)


def test_mass_bin_by_assertion(tmp_path):
    c = cfg(mass_bin_by="mean", results_dir=str(tmp_path) + os.sep)
    assert rejects(MR.run_merger_rate_calculation, c) == "assert"


def _sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def test_preflight_atomicity(tmp_path):
    c = cfg(results_dir=str(tmp_path) + os.sep, redshifts=[2.0, 3.0])
    _write_pairs_file(MR._results_path(2.0, c), [0], [1] * 6)  # missing z=3.0 file
    sentinel = os.path.join(c["results_dir"], "merger_rate.hdf5")
    with open(sentinel, "wb") as fh:
        fh.write(b"SENTINEL")
    before = _sha(sentinel)
    assert rejects(MR.run_merger_rate_calculation, c) == "assert"
    assert _sha(sentinel) == before


def test_per_file_box_size_used(tmp_path):
    c = cfg(results_dir=str(tmp_path) + os.sep, redshifts=[2.0], box_size=500.0)
    _write_pairs_file(MR._results_path(2.0, c), [0], [10, 0, 0, 0, 0, 0], box=250.0)
    MR.run_merger_rate_calculation(c)
    with h5py.File(os.path.join(c["results_dir"], "merger_rate.hdf5"), "r") as f:
        rate = f["merger_rate"][...]
    T = c["merger_timescale_gyr0"] * (1 + 2.0) ** c["merger_timescale_alpha"]
    expect = c["merger_fraction"] * 1 / (250.0 ** 3 * T)
    assert abs(float(rate[0, 0]) - expect) / expect < 1e-9


def test_fit_exact_power_law():
    s, se, ic, nx = MR.fit_log_rate_vs_redshift(
        np.array([2.0, 4.0, 8.0]), np.array([1e-9, 1e-9, 1e-9]), np.array([1.0, 3.0, 7.0]))
    assert abs(float(s) - 1.0) < 1e-9
    assert int(nx) == 0


def test_fit_two_point_slope_err_pinned():
    s, se, ic, nx = MR.fit_log_rate_vs_redshift(
        np.array([2.0, 4.0]), np.array([0.2, 0.4]), np.array([1.0, 3.0]))
    assert abs(float(s) - 1.0) < 1e-12
    assert abs(float(se) - 0.2040278893193579) < 1e-9


def test_fit_fewer_than_two_usable():
    s, se, ic, nx = MR.fit_log_rate_vs_redshift(
        np.array([2.0, 0.0]), np.array([0.2, 0.1]), np.array([1.0, 2.0]))
    assert math.isnan(float(s)) and int(nx) == 1


def test_fit_collapsed_predictor():
    s, se, ic, nx = MR.fit_log_rate_vs_redshift(
        np.array([2.0, 4.0]), np.array([0.1, 0.1]),
        np.array([1.0, np.nextafter(1.0, 2.0)]))
    assert math.isnan(float(s))


def _decimal_wls_slope(rates, rate_errs, redshifts):
    x_float = np.log10(1.0 + np.asarray(redshifts, dtype=float))
    y_float = np.log10(np.asarray(rates, dtype=float))
    sigma_float = (np.asarray(rate_errs, dtype=float)
                   / (np.asarray(rates, dtype=float) * np.log(10.0)))
    with decimal.localcontext() as ctx:
        ctx.prec = 80
        D = decimal.Decimal
        x = [D.from_float(float(v)) for v in x_float]
        y = [D.from_float(float(v)) for v in y_float]
        sigma = [D.from_float(float(v)) for v in sigma_float]
        weights = [D(1) / (s * s) for s in sigma]
        w_sum = sum(weights)
        x_mean = sum(w * xx for w, xx in zip(weights, x, strict=True)) / w_sum
        y_mean = sum(w * yy for w, yy in zip(weights, y, strict=True)) / w_sum
        s_xx = sum(w * (xx - x_mean) ** 2 for w, xx in zip(weights, x, strict=True))
        s_xy = sum(w * (xx - x_mean) * (yy - y_mean)
                   for w, xx, yy in zip(weights, x, y, strict=True))
        return float(s_xy / s_xx)


def test_fit_centres_y_for_numerical_stability():
    z = np.array([1.0, 1.0 + 2.0**-40, 1.0 + 2.0**-39, 1.0 + 2.0**-38])
    x = np.log10(1.0 + z)
    y = 200.0 + 1.0e12 * (x - x[0])
    rates = np.power(10.0, y)
    errs = rates * np.array([0.05, 0.08, 0.04, 0.09])
    expected = _decimal_wls_slope(rates, errs, z)
    slope, _, _, _ = MR.fit_log_rate_vs_redshift(rates, errs, z)
    np.testing.assert_allclose(slope, expected, rtol=1e-6, atol=0)


def test_check_slope_consistency():
    assert MR.check_slope_consistency(1.0, 0.1, 1.05) is True
    assert MR.check_slope_consistency(1.0, 0.1, 5.0) is False
    assert MR.check_slope_consistency(1.0, 0.0, 1.0) is False
    assert rejects(MR.check_slope_consistency, 1.0, 0.1, 1.0, 0.0) == "assert"


def test_validation_result_keys_and_nondefault_alpha(tmp_path):
    c = cfg(results_dir=str(tmp_path) + os.sep, merger_timescale_alpha=-0.7)
    nb = nbins(c); zs = np.array(c["redshifts"], dtype=float)
    rate = np.outer((1 + zs) ** 0.7, np.ones(nb)) * 1e-8
    with h5py.File(os.path.join(c["results_dir"], "merger_rate.hdf5"), "w") as f:
        f.create_dataset("pair_fraction", data=np.full((len(zs), nb), 0.5))
        f.create_dataset("n_pairs", data=np.full((len(zs), nb), 5, dtype=np.int64))
        f.create_dataset("merger_rate", data=rate)
        f.create_dataset("merger_rate_err", data=rate * 0.05)
        f.attrs["redshifts"] = zs
        f.attrs["mass_bin_by"] = "primary"
        f.attrs["merger_fraction"] = c["merger_fraction"]
        f.attrs["merger_timescale_gyr0"] = c["merger_timescale_gyr0"]
        f.attrs["merger_timescale_alpha"] = c["merger_timescale_alpha"]
        f.attrs["timestamp"] = "x"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        res = MR.run_merger_rate_validation(c)
    want = {"mass_bin", "slope", "slope_err", "intercept", "expected_slope", "n_excluded", "consistent"}
    for d in res:
        assert set(d.keys()) == want
        if d["consistent"] is not None:
            assert abs(d["expected_slope"] - 0.7) < 1e-12


def test_validation_rejects_malformed_stored_redshift(tmp_path):
    c = cfg(results_dir=str(tmp_path) + os.sep)
    nb = nbins(c)
    with h5py.File(os.path.join(c["results_dir"], "merger_rate.hdf5"), "w") as f:
        f.create_dataset("merger_rate", data=np.ones((2, nb)))
        f.create_dataset("merger_rate_err", data=np.ones((2, nb)))
        f.attrs["redshifts"] = np.array([2.0, np.nan])
    assert rejects(MR.run_merger_rate_validation, c) == "assert"
    with h5py.File(os.path.join(c["results_dir"], "merger_rate.hdf5"), "r+") as f:
        f.attrs["redshifts"] = np.array([2.0, -1.0])
    assert rejects(MR.run_merger_rate_validation, c) == "assert"


def test_end_to_end_mock(tmp_path):
    c = cfg(data_dir=str(tmp_path / "data") + os.sep,
            results_dir=str(tmp_path / "results") + os.sep,
            figures_dir=str(tmp_path / "fig") + os.sep)
    os.makedirs(c["data_dir"], exist_ok=True)
    os.makedirs(c["results_dir"], exist_ok=True)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        generate_all_snapshots(c)
        calc.run_calculation(c)
        MR.run_merger_rate_calculation(c)
        res = MR.run_merger_rate_validation(c)
    expected = -c["merger_timescale_alpha"]
    checked = 0
    for d in res:
        if d["consistent"] is None:
            continue
        checked += 1
        assert d["consistent"] is True
        assert abs(d["slope"] - expected) < 0.4
    assert checked == nbins(c)
    edges = np.linspace(c["log_mass_min"], c["log_mass_max"], nbins(c) + 1)
    with h5py.File(os.path.join(c["results_dir"], "merger_rate.hdf5"), "r") as f:
        assert f.attrs["mass_bin_by"] == c["mass_bin_by"]
        assert float(f.attrs["merger_fraction"]) == c["merger_fraction"]
        assert float(f.attrs["merger_timescale_gyr0"]) == c["merger_timescale_gyr0"]
        assert float(f.attrs["merger_timescale_alpha"]) == c["merger_timescale_alpha"]
        stored_pairs = f["n_pairs"][...]
        stored_fraction = f["pair_fraction"][...]
        stored_rate_err = f["merger_rate_err"][...]
        for iz, z in enumerate(c["redshifts"]):
            catalog = load_galaxy_catalog(
                os.path.join(c["data_dir"], f"test_z{z:.1f}.hdf5"), c)
            masses = catalog["log_stellar_mass"]
            raw = np.digitize(masses, edges) - 1
            valid = raw[(raw >= 0) & (raw < nbins(c))]
            expected_galaxies = np.bincount(valid, minlength=nbins(c))
            with h5py.File(MR._results_path(z, c), "r") as pf:
                actual_galaxies = pf["n_galaxies_per_mass_bin"][...]
                mass_bin = pf["mass_bin"][...]
            expected_pairs = np.array(
                [np.sum(mass_bin == b) for b in range(nbins(c))], dtype=np.int64)
            expected_fraction = expected_pairs / expected_galaxies
            expected_sigma_fraction = np.divide(
                expected_fraction, np.sqrt(expected_pairs), out=np.zeros(nbins(c)),
                where=expected_pairs > 0)
            with h5py.File(MR._results_path(z, c), "r") as pf:
                box = float(pf.attrs["box_size_mpc"])
            timescale = c["merger_timescale_gyr0"] * (1.0 + z) ** c["merger_timescale_alpha"]
            expected_rate_err = c["merger_fraction"] * expected_sigma_fraction * expected_galaxies / (box ** 3 * timescale)
            np.testing.assert_array_equal(actual_galaxies, expected_galaxies)
            np.testing.assert_array_equal(stored_pairs[iz], expected_pairs)
            np.testing.assert_allclose(
                stored_fraction[iz], expected_fraction, rtol=1e-14, atol=0)
            np.testing.assert_allclose(stored_rate_err[iz], expected_rate_err, rtol=1e-14, atol=0)
    text = buf.getvalue()
    assert "recovery of the injected" in text and "mock" in text
    for b in range(nbins(c)):
        lines = [line for line in text.splitlines() if f"bin {b} [" in line]
        assert len(lines) == 1, (b, lines)
        line = lines[0]
        assert re.search(r"(?<![_\w])slope\s*=", line), line
        for field in ("slope_err=", "expected_slope=", "n_excluded=", "status="):
            assert field in line, (field, line)
