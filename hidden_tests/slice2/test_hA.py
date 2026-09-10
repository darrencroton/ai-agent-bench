"""Slice 2 hidden unit tests: pinned unit criteria derived solely from
docs/MERGER_RATE_PLAN-2SLICE.md's Slice 2 (weighted redshift-evolution fit
and validation). Assumes Slice 1 is already implemented and accepted.

Not visible to the Developer model. Copied into the trial worktree's tests/
directory at grading time and run with the trial's own pytest/venv.

Re-partitioned from ai-agent-bench's Task 001 `hidden_tests/test_hA.py`
(Part 3 only; Parts 1-2 live in hidden_tests/slice1/test_hA.py) -- see
docs/MODE2-REWRITE-PLAN.md gap G4. Test bodies are unmodified from that
source; only the file's scope and this header changed.
"""
import contextlib
import copy
import decimal
import io
import math
import os
import re
import sys
import warnings

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import h5py
import numpy as np
import pytest

import config as cfgmod

try:
    import merger_rate as MR
except Exception as e:                      # pragma: no cover
    MR = None
    _MR_ERR = e

BASE = cfgmod.config


def cfg(**kw):
    c = copy.deepcopy(BASE)
    c.update(kw)
    return c


def nbins(c=BASE):
    return int(round((c["log_mass_max"] - c["log_mass_min"]) / c["mass_bin_width"]))


def rejects(fn, *a, **k):
    """Plan-conformant rejection == AssertionError (no new TypeError/ValueError)."""
    try:
        fn(*a, **k)
    except AssertionError:
        return "assert"
    except Exception as e:
        return type(e).__name__
    return None


# ---------------------------------------------------------------- Part 3
def test_C01_exact_power_law():
    s, se, ic, nx = MR.fit_log_rate_vs_redshift(
        np.array([2.0, 4.0, 8.0]), np.array([1e-9, 1e-9, 1e-9]), np.array([1.0, 3.0, 7.0]))
    assert abs(float(s) - 1.0) < 1e-9
    assert int(nx) == 0


def test_C02_provably_weighted():
    z = np.array([1.0, 3.0, 7.0, 15.0])
    r = np.array([2.0, 4.0, 8.0, 16.0])
    r[2] = 80.0
    e = np.array([1e-6, 1e-6, 1e3, 1e-6])
    s, _, _, _ = MR.fit_log_rate_vs_redshift(r, e, z)
    x = np.log10(1 + z); y = np.log10(r)
    unw = np.polyfit(x, y, 1)[0]
    assert abs(float(s) - 1.0) < abs(unw - 1.0)


def test_C03_two_point_slope_err_pinned():
    s, se, ic, nx = MR.fit_log_rate_vs_redshift(
        np.array([2.0, 4.0]), np.array([0.2, 0.4]), np.array([1.0, 3.0]))
    assert abs(float(s) - 1.0) < 1e-12
    assert abs(float(se) - 0.2040278893193579) < 1e-12
    assert np.isfinite(float(ic))
    assert int(nx) == 0


def test_C04_two_usable_with_exclusions_finite():
    s, se, ic, nx = MR.fit_log_rate_vs_redshift(
        np.array([2.0, 0.0, 4.0]), np.array([0.2, 0.1, 0.4]), np.array([1.0, 2.0, 3.0]))
    assert np.isfinite(float(s)) and np.isfinite(float(se)) and np.isfinite(float(ic))
    assert int(nx) == 1


def test_C05_fewer_than_two_usable():
    s, se, ic, nx = MR.fit_log_rate_vs_redshift(
        np.array([2.0, 0.0, np.nan, 5.0]), np.array([0.2, 0.1, 0.1, -1.0]),
        np.array([1.0, 2.0, 3.0, 4.0]))
    assert math.isnan(float(s)) and math.isnan(float(se)) and math.isnan(float(ic))
    assert int(nx) == 3


def test_C06_single_redshift_returns_nan():
    s, se, ic, nx = MR.fit_log_rate_vs_redshift(
        np.array([2.0, 4.0]), np.array([0.2, 0.4]), np.array([1.0, 1.0]))
    assert math.isnan(float(s)) and math.isnan(float(se)) and math.isnan(float(ic))
    assert int(nx) == 0


def test_C07_malformed_redshifts_and_rank():
    for zz in ([-1.0, 2.0], [-2.0, 2.0], [np.nan, 2.0], [np.inf, 2.0]):
        assert rejects(MR.fit_log_rate_vs_redshift, np.array([2.0, 4.0]),
                       np.array([0.2, 0.4]), np.array(zz)) == "assert", zz
    assert rejects(MR.fit_log_rate_vs_redshift, np.array([[2.0, 4.0]]),
                   np.array([[0.2, 0.4]]), np.array([[1.0, 3.0]])) == "assert"
    assert rejects(MR.fit_log_rate_vs_redshift, np.array([2.0, 4.0]),
                   np.array([0.2]), np.array([1.0, 3.0])) == "assert"


def test_C08_check_slope_consistency():
    assert MR.check_slope_consistency(1.0, 0.1, 1.05) is True
    assert MR.check_slope_consistency(1.0, 0.1, 5.0) is False
    assert MR.check_slope_consistency(float("nan"), 0.1, 1.0) is False
    assert MR.check_slope_consistency(1.0, float("nan"), 1.0) is False
    assert MR.check_slope_consistency(1.0, 0.1, float("nan")) is False
    assert MR.check_slope_consistency(1.0, 0.0, 1.0) is False
    assert MR.check_slope_consistency(1.0, -1.0, 1.0) is False
    for bad in (0.0, -1.0, float("nan"), float("inf")):
        assert rejects(MR.check_slope_consistency, 1.0, 0.1, 1.0, bad) == "assert", bad


def test_C09_collapsed_predictor():
    """Distinctness on the formed predictor."""
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        s, se, ic, nx = MR.fit_log_rate_vs_redshift(
            np.array([2.0, 4.0]), np.array([0.1, 0.1]),
            np.array([1.0, np.nextafter(1.0, 2.0)]))
    assert math.isnan(float(s)), float(s)
    assert math.isnan(float(se)), float(se)
    assert math.isnan(float(ic)), float(ic)
    assert int(nx) == 0


def _decimal_wls_slope(rates, rate_errs, redshifts):
    """Independent high-precision oracle for the narrow-predictor fixture."""
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


def test_C10_y_centring_numerical_stability():
    """Extreme y offset exposes the rounding bias from an uncentred cross term."""
    z = np.array([1.0, 1.0 + 2.0**-40, 1.0 + 2.0**-39, 1.0 + 2.0**-38])
    x = np.log10(1.0 + z)
    y = 200.0 + 1.0e12 * (x - x[0])
    rates = np.power(10.0, y)
    errs = rates * np.array([0.05, 0.08, 0.04, 0.09])
    expected = _decimal_wls_slope(rates, errs, z)
    slope, slope_err, intercept, n_excluded = MR.fit_log_rate_vs_redshift(rates, errs, z)
    np.testing.assert_allclose(slope, expected, rtol=1e-6, atol=0)
    assert np.isfinite(slope_err) and np.isfinite(intercept)
    assert n_excluded == 0


_FLOAT = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"


def _parse_bin_line(text, b):
    lines = [line for line in text.splitlines()
             if re.search(rf"\bbin\s+{b}\b", line, flags=re.IGNORECASE)]
    assert len(lines) == 1, f"expected one output line for bin {b}, got {lines!r}"
    line = lines[0]
    mass = re.search(rf"\[\s*({_FLOAT})\s*,\s*({_FLOAT})\s*\)", line)
    slope = re.search(rf"\bslope\s*=\s*({_FLOAT}|nan)", line, flags=re.IGNORECASE)
    slope_err = re.search(
        rf"(?:\bslope_err\s*=|\+/-)\s*({_FLOAT}|nan)", line, flags=re.IGNORECASE)
    expected = re.search(
        rf"\bexpected(?:_slope)?\s*=\s*({_FLOAT})", line, flags=re.IGNORECASE)
    excluded = re.search(r"\bn_excluded\s*=\s*(\d+)", line, flags=re.IGNORECASE)
    status = re.search(
        r"(?:\bstatus\s*=\s*(consistent|inconsistent|insufficient data)|"
        r"\bconsistent\s*=\s*(True|False|None)|\binsufficient data\b)",
        line, flags=re.IGNORECASE)
    assert all((mass, slope, slope_err, expected, excluded, status)), line
    return line, tuple(map(float, mass.groups())), int(excluded.group(1))


def test_C11_validation_result_keys(tmp_path):
    c = cfg(results_dir=str(tmp_path) + os.sep)
    nb = nbins(c); zs = np.array(c["redshifts"], dtype=float)
    rate = np.outer((1 + zs) ** 1.0, np.ones(nb)) * 1e-8
    err = rate * 0.05
    with h5py.File(os.path.join(c["results_dir"], "merger_rate.hdf5"), "w") as f:
        f.create_dataset("pair_fraction", data=np.full((len(zs), nb), 0.5))
        f.create_dataset("n_pairs", data=np.full((len(zs), nb), 5, dtype=np.int64))
        f.create_dataset("merger_rate", data=rate)
        f.create_dataset("merger_rate_err", data=err)
        f.attrs["redshifts"] = zs
        f.attrs["mass_bin_by"] = "primary"
        f.attrs["merger_fraction"] = c["merger_fraction"]
        f.attrs["merger_timescale_gyr0"] = c["merger_timescale_gyr0"]
        f.attrs["merger_timescale_alpha"] = c["merger_timescale_alpha"]
        f.attrs["timestamp"] = "x"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        res = MR.run_merger_rate_validation(c)
    assert isinstance(res, list) and len(res) == nb
    want = {"mass_bin", "slope", "slope_err", "intercept", "expected_slope",
            "n_excluded", "consistent"}
    for d in res:
        assert set(d.keys()) == want, set(d.keys()) ^ want
    out = buf.getvalue().lower()
    assert "mock" in out or "injected" in out, "heading does not label mock/injected model"
    edges = MR._mass_bin_edges(c)
    for b in range(nb):
        _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)
        np.testing.assert_allclose(mass_range, edges[b:b + 2], rtol=0, atol=1e-12)
        assert excluded == 0


def test_C12_validation_rejects_malformed_stored_redshift_before_fit(tmp_path, monkeypatch):
    c = cfg(results_dir=str(tmp_path) + os.sep)
    nb = nbins(c)
    zs = np.array([2.0, np.nan, 4.0, 5.0])
    with h5py.File(os.path.join(c["results_dir"], "merger_rate.hdf5"), "w") as f:
        f.create_dataset("pair_fraction", data=np.full((4, nb), 0.5))
        f.create_dataset("n_pairs", data=np.full((4, nb), 5, dtype=np.int64))
        f.create_dataset("merger_rate", data=np.full((4, nb), 1e-8))
        f.create_dataset("merger_rate_err", data=np.full((4, nb), 1e-9))
        f.attrs["redshifts"] = zs
        f.attrs["mass_bin_by"] = "primary"
        f.attrs["merger_fraction"] = c["merger_fraction"]
        f.attrs["merger_timescale_gyr0"] = c["merger_timescale_gyr0"]
        f.attrs["merger_timescale_alpha"] = c["merger_timescale_alpha"]
        f.attrs["timestamp"] = "x"
    buf = io.StringIO()
    def fit_must_not_run(*args, **kwargs):
        pytest.fail("fit called before stored-redshift preflight completed")
    monkeypatch.setattr(MR, "fit_log_rate_vs_redshift", fit_must_not_run)
    with contextlib.redirect_stdout(buf):
        r = rejects(MR.run_merger_rate_validation, c)
    assert r == "assert", r


def test_C13_validation_prints_insufficient_data(tmp_path):
    c = cfg(results_dir=str(tmp_path) + os.sep)
    nb = nbins(c); zs = np.array(c["redshifts"], dtype=float)
    rate = np.zeros((len(zs), nb)); err = np.zeros((len(zs), nb))
    with h5py.File(os.path.join(c["results_dir"], "merger_rate.hdf5"), "w") as f:
        f.create_dataset("pair_fraction", data=np.zeros((len(zs), nb)))
        f.create_dataset("n_pairs", data=np.zeros((len(zs), nb), dtype=np.int64))
        f.create_dataset("merger_rate", data=rate)
        f.create_dataset("merger_rate_err", data=err)
        f.attrs["redshifts"] = zs
        f.attrs["mass_bin_by"] = "primary"
        f.attrs["merger_fraction"] = c["merger_fraction"]
        f.attrs["merger_timescale_gyr0"] = c["merger_timescale_gyr0"]
        f.attrs["merger_timescale_alpha"] = c["merger_timescale_alpha"]
        f.attrs["timestamp"] = "x"
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        res = MR.run_merger_rate_validation(c)
    assert "insufficient data" in buf.getvalue().lower()
    assert all(d["consistent"] is None for d in res)
    edges = MR._mass_bin_edges(c)
    for b in range(nb):
        _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)
        np.testing.assert_allclose(mass_range, edges[b:b + 2], rtol=0, atol=1e-12)
        assert excluded == len(zs)


def test_C14_mass_bin_is_index_not_string(tmp_path):
    """report 04 recorded a mass_bin string-label defect twice; pin it directly."""
    c = cfg(results_dir=str(tmp_path) + os.sep)
    nb = nbins(c); zs = np.array(c["redshifts"], dtype=float)
    rate = np.outer((1 + zs) ** 1.0, np.ones(nb)) * 1e-8
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
    for i, d in enumerate(res):
        assert isinstance(d["mass_bin"], (int, np.integer)), \
            f"mass_bin must be an integer bin index, got {type(d['mass_bin'])}: {d['mass_bin']!r}"
        assert int(d["mass_bin"]) == i


def test_C15_consistent_is_python_bool_or_none():
    """report 04 recorded a numpy.bool_ leak where the contract says 'a bool'."""
    v = MR.check_slope_consistency(1.0, 0.1, 1.05)
    assert v is True or v is False, f"expected a Python bool, got {type(v)}: {v!r}"
