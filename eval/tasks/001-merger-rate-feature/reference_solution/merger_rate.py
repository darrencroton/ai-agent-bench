"""
Reference solution for Task 001 (Close-Pair Merger Rate Estimation).

Kept for harness self-validation only -- never shown to a Developer model.
Converts close-pair counts (pair_finder.py / calc.py) into a merger rate
density via the Kitzbichler & White 2008 close-pair method. See
eval/tasks/001-merger-rate-feature/spec.md for the full contract.
"""
import os
import math
import numpy as np
import h5py


def _mass_bin_edges(config):
    n_bins = round((config["log_mass_max"] - config["log_mass_min"]) / config["mass_bin_width"])
    return np.linspace(config["log_mass_min"], config["log_mass_max"], n_bins + 1)


def _results_path(z, config):
    return os.path.join(config["results_dir"], f"pairs_z{z:.1f}.hdf5")


def _load_pair_counts(z, config):
    path = _results_path(z, config)
    assert os.path.isfile(path), f"pair results file not found: {path}"
    n_bins = len(_mass_bin_edges(config)) - 1
    with h5py.File(path, "r") as f:
        assert "mass_bin" in f, f"missing dataset 'mass_bin' in {path}"
        assert "n_galaxies_per_mass_bin" in f, f"missing dataset 'n_galaxies_per_mass_bin' in {path}"
        mass_bin = f["mass_bin"][...]
        ngal = f["n_galaxies_per_mass_bin"][...]
        assert "box_size_mpc" in f.attrs, f"missing attr 'box_size_mpc' in {path}"
        box = f.attrs["box_size_mpc"]

    assert np.ndim(mass_bin) == 1
    if len(mass_bin):
        assert mass_bin.min() >= -1 and mass_bin.max() < n_bins, (
            f"mass_bin values out of range [-1, {n_bins - 1}]: {path}")
    npair = np.zeros(n_bins, dtype=np.int64)
    for b in range(n_bins):
        npair[b] = int(np.sum(mass_bin == b))

    ngal = np.asarray(ngal)
    assert ngal.ndim == 1 and len(ngal) == n_bins, (
        f"n_galaxies_per_mass_bin length {len(ngal)} != {n_bins} bins: {path}")
    ngal = ngal.astype(np.int64)

    assert np.isscalar(box) or (hasattr(box, "shape") and box.shape == ()), (
        f"box_size_mpc must be a scalar, got shape {getattr(box, 'shape', None)}: {path}")
    box = float(box)
    assert math.isfinite(box) and box > 0, f"box_size_mpc must be finite and positive: {box}"

    return npair, ngal, box


def compute_pair_fraction(n_pairs, n_galaxies):
    n_pairs = np.asarray(n_pairs)
    n_galaxies = np.asarray(n_galaxies)
    assert n_pairs.ndim == 1 and n_galaxies.ndim == 1, "inputs must be 1D"
    assert n_pairs.shape == n_galaxies.shape, "n_pairs and n_galaxies must have matching shape"

    for name, arr in (("n_pairs", n_pairs), ("n_galaxies", n_galaxies)):
        assert np.issubdtype(arr.dtype, np.number), f"{name} must be numeric, got {arr.dtype}"
        assert not np.iscomplexobj(arr), f"{name} must not be complex"
        farr = arr.astype(float)
        assert np.all(np.isfinite(farr)), f"{name} must be finite"
        assert np.all(farr >= 0), f"{name} must be non-negative"
        assert np.all(farr == np.round(farr)), f"{name} must be integer-valued"

    assert np.all((n_galaxies > 0) | (n_pairs == 0)), (
        "a bin with n_pairs > 0 must have n_galaxies > 0")

    n_pairs_f = n_pairs.astype(float)
    n_galaxies_f = n_galaxies.astype(float)
    with np.errstate(divide="ignore", invalid="ignore"):
        f_pair = np.where(n_galaxies_f > 0, n_pairs_f / np.where(n_galaxies_f > 0, n_galaxies_f, 1.0), 0.0)
        sigma_f_pair = np.where(n_pairs_f > 0, f_pair / np.sqrt(np.where(n_pairs_f > 0, n_pairs_f, 1.0)), 0.0)
    return f_pair, sigma_f_pair


def merger_timescale_gyr(z, config):
    assert np.isscalar(z) or (hasattr(z, "shape") and z.shape == ()), "z must be a scalar"
    assert not isinstance(z, (str, bytes)), "z must be numeric, not a string"
    zf = float(z)
    assert math.isfinite(zf) and zf > -1, f"z must be finite and > -1, got {z}"

    gyr0 = config["merger_timescale_gyr0"]
    alpha = config["merger_timescale_alpha"]
    assert not isinstance(gyr0, (str, bytes)) and not isinstance(alpha, (str, bytes))
    gyr0f, alphaf = float(gyr0), float(alpha)
    assert math.isfinite(gyr0f) and gyr0f > 0, f"merger_timescale_gyr0 must be finite and > 0, got {gyr0}"
    assert math.isfinite(alphaf), f"merger_timescale_alpha must be finite, got {alpha}"

    t = gyr0f * (1.0 + zf) ** alphaf
    assert math.isfinite(t) and t > 0, f"computed T_merge must be finite and > 0, got {t}"
    return t


def compute_merger_rate(f_pair, sigma_f_pair, n_galaxies, box_size_mpc, timescale_gyr, merger_fraction):
    f_pair = np.asarray(f_pair, dtype=None)
    sigma_f_pair = np.asarray(sigma_f_pair, dtype=None)
    n_galaxies = np.asarray(n_galaxies, dtype=None)

    for name, arr in (("f_pair", f_pair), ("sigma_f_pair", sigma_f_pair), ("n_galaxies", n_galaxies)):
        assert arr.ndim == 1, f"{name} must be 1D"
    assert f_pair.shape == sigma_f_pair.shape == n_galaxies.shape, "array shapes must match"

    for name, arr in (("f_pair", f_pair), ("sigma_f_pair", sigma_f_pair)):
        farr = arr.astype(float)
        assert np.all(np.isfinite(farr)), f"{name} must be finite"
        assert np.all(farr >= 0), f"{name} must be non-negative"

    assert np.issubdtype(n_galaxies.dtype, np.number) and not np.iscomplexobj(n_galaxies)
    ngf = n_galaxies.astype(float)
    assert np.all(np.isfinite(ngf)) and np.all(ngf >= 0), "n_galaxies must be finite and non-negative"
    assert np.all(ngf == np.round(ngf)), "n_galaxies must be integer-valued"
    assert np.all((ngf > 0) | ((f_pair == 0) & (sigma_f_pair == 0))), (
        "n_galaxies == 0 requires f_pair == 0 and sigma_f_pair == 0")

    for name, val in (("box_size_mpc", box_size_mpc), ("timescale_gyr", timescale_gyr)):
        assert not isinstance(val, (str, bytes)), f"{name} must be numeric, not a string"
        fv = float(val)
        assert math.isfinite(fv) and fv > 0, f"{name} must be finite and > 0, got {val}"

    assert not isinstance(merger_fraction, (str, bytes)), "merger_fraction must be numeric"
    mf = float(merger_fraction)
    assert math.isfinite(mf) and 0 < mf <= 1, f"merger_fraction must be in (0, 1], got {merger_fraction}"

    box = float(box_size_mpc)
    T = float(timescale_gyr)
    denom = box ** 3 * T
    rate = mf * f_pair.astype(float) * ngf / denom
    sigma_rate = mf * sigma_f_pair.astype(float) * ngf / denom
    return rate, sigma_rate


def run_merger_rate_calculation(config):
    mbb = config["mass_bin_by"]
    assert mbb == "primary", f"merger_rate requires mass_bin_by == 'primary', got {mbb!r}"

    redshifts = config["redshifts"]
    paths = [_results_path(z, config) for z in redshifts]
    for p, z in zip(paths, redshifts, strict=True):
        assert os.path.isfile(p), f"pair results file not found: {p}"
        with h5py.File(p, "r") as f:
            assert "redshift" in f.attrs, f"missing attr 'redshift' in {p}"
            rz = f.attrs["redshift"]
            assert np.isscalar(rz) or (hasattr(rz, "shape") and rz.shape == ()), (
                f"redshift attr must be a scalar in {p}, got shape {getattr(rz, 'shape', None)}")
            assert not isinstance(rz, (str, bytes)), f"redshift attr must be numeric in {p}"
            rzf = float(rz)
            assert rzf == float(z), f"recorded redshift {rzf} != configured {z} in {p}"

    n_bins = len(_mass_bin_edges(config)) - 1
    n_z = len(redshifts)
    pair_fraction = np.zeros((n_z, n_bins))
    n_pairs_out = np.zeros((n_z, n_bins), dtype=np.int64)
    merger_rate = np.zeros((n_z, n_bins))
    merger_rate_err = np.zeros((n_z, n_bins))

    for iz, z in enumerate(redshifts):
        npair, ngal, box = _load_pair_counts(z, config)
        f_pair, sigma_f_pair = compute_pair_fraction(npair, ngal)
        T = merger_timescale_gyr(z, config)
        rate, sigma_rate = compute_merger_rate(
            f_pair, sigma_f_pair, ngal, box, T, config["merger_fraction"])
        pair_fraction[iz] = f_pair
        n_pairs_out[iz] = npair
        merger_rate[iz] = rate
        merger_rate_err[iz] = sigma_rate

    os.makedirs(config["results_dir"], exist_ok=True)
    out_path = os.path.join(config["results_dir"], "merger_rate.hdf5")
    import datetime
    with h5py.File(out_path, "w") as f:
        f.create_dataset("pair_fraction", data=pair_fraction)
        f.create_dataset("n_pairs", data=n_pairs_out)
        f.create_dataset("merger_rate", data=merger_rate)
        f.create_dataset("merger_rate_err", data=merger_rate_err)
        f.attrs["redshifts"] = np.array(redshifts, dtype=float)
        f.attrs["mass_bin_by"] = mbb
        f.attrs["merger_fraction"] = config["merger_fraction"]
        f.attrs["merger_timescale_gyr0"] = config["merger_timescale_gyr0"]
        f.attrs["merger_timescale_alpha"] = config["merger_timescale_alpha"]
        f.attrs["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()


def fit_log_rate_vs_redshift(rates, rate_errs, redshifts):
    rates = np.asarray(rates, dtype=float)
    rate_errs = np.asarray(rate_errs, dtype=float)
    redshifts = np.asarray(redshifts, dtype=float)
    assert rates.ndim == 1 and rate_errs.ndim == 1 and redshifts.ndim == 1, "inputs must be 1D"
    assert rates.shape == rate_errs.shape == redshifts.shape, "inputs must have identical shapes"

    assert np.all(np.isfinite(redshifts)) and np.all(redshifts > -1), (
        "redshifts must be finite and > -1")

    usable = np.isfinite(rates) & (rates > 0) & np.isfinite(rate_errs) & (rate_errs > 0)
    n_excluded = int(np.sum(~usable))

    if np.sum(usable) < 2:
        return float("nan"), float("nan"), float("nan"), n_excluded

    x = np.log10(1.0 + redshifts[usable])
    y = np.log10(rates[usable])
    sigma_log_rate = rate_errs[usable] / (rates[usable] * math.log(10))
    w = 1.0 / sigma_log_rate ** 2

    ux = np.unique(x)
    if len(ux) < 2:
        return float("nan"), float("nan"), float("nan"), n_excluded

    w_sum = np.sum(w)
    x_mean = np.sum(w * x) / w_sum
    y_mean = np.sum(w * y) / w_sum
    xc = x - x_mean
    yc = y - y_mean

    s_xx = np.sum(w * xc * xc)
    s_xy = np.sum(w * xc * yc)
    slope = s_xy / s_xx
    intercept = y_mean - slope * x_mean
    slope_err = math.sqrt(1.0 / s_xx)

    return float(slope), float(slope_err), float(intercept), n_excluded


def check_slope_consistency(slope, slope_err, expected_slope, n_sigma=3.0):
    assert math.isfinite(n_sigma) and n_sigma > 0, f"n_sigma must be finite and > 0, got {n_sigma}"
    for v in (slope, slope_err, expected_slope):
        if not math.isfinite(v):
            return False
    if slope_err <= 0:
        return False
    return bool(abs(slope - expected_slope) < n_sigma * slope_err)


def run_merger_rate_validation(config):
    path = os.path.join(config["results_dir"], "merger_rate.hdf5")
    with h5py.File(path, "r") as f:
        redshifts = np.asarray(f.attrs["redshifts"], dtype=float)
        assert np.all(np.isfinite(redshifts)) and np.all(redshifts > -1), (
            "stored redshifts must be finite and > -1")
        merger_rate = f["merger_rate"][...]
        merger_rate_err = f["merger_rate_err"][...]

    expected_slope = -float(config["merger_timescale_alpha"])
    n_bins = merger_rate.shape[1]

    print("Merger-rate redshift-evolution check (recovery of the injected "
          "mock/injected timescale model, not a measurement of real merger-rate evolution):")
    results = []
    for b in range(n_bins):
        slope, slope_err, intercept, n_excluded = fit_log_rate_vs_redshift(
            merger_rate[:, b], merger_rate_err[:, b], redshifts)
        if math.isnan(slope):
            consistent = None
            print(f"  bin {b}: insufficient data (n_excluded={n_excluded})")
        else:
            consistent = check_slope_consistency(slope, slope_err, expected_slope)
            print(f"  bin {b}: slope={slope:+.4f} +/- {slope_err:.4f} "
                  f"expected={expected_slope:+.4f} n_excluded={n_excluded} "
                  f"consistent={consistent}")
        results.append(dict(mass_bin=int(b), slope=slope, slope_err=slope_err,
                             intercept=intercept, expected_slope=expected_slope,
                             n_excluded=n_excluded, consistent=consistent))
    return results
