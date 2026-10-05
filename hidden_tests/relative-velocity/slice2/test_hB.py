"""Slice 2 hidden integration tests: end-to-end recovery of the injected
merger-timescale model on generated mock data.

Not visible to the Developer model. Copied into the trial worktree's tests/
directory at grading time and run with the trial's own pytest/venv.

Re-partitioned from ai-agent-bench's Task 001 `hidden_tests/test_hB.py`
(E07 and its successors only; E01-E06 live in
hidden_tests/slice1/test_hB.py).

Node ids E10-E13 deliberately start after E09, which does not appear in
this file: an archived scoring corpus's `test_E09` used different
semantics, and a node id must never mean two different things across
cohorts. See docs/OBLIGATION-GROUPS.md for what each node in
`end_to_end_science` checks and why.
"""
import contextlib
import copy
import io
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import h5py
import numpy as np
import pytest

import calc
import config as cfgmod
from generate_test_data import generate_all_snapshots

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


def test_E10_expected_slope_tracks_pinned_alpha(mock):
    """docs/MERGER_RATE_PLAN-2SLICE.md:669-674: with merger_timescale_alpha =
    -1.5 (the plan's own pinned non-default value, distinct from the default
    -1.0), every returned per-bin dict with usable data reports
    expected_slope == 1.5 and consistent is True.

    Deliberately no absolute slope tolerance here (unlike E07): the mock
    catalogs are only statistically flat, so a fixed |slope - expected| < x
    bound is seed-sensitive. The plan's own contract for "recovered" is the
    3-sigma check_slope_consistency gate, which `consistent` already encodes
    -- duplicating it with a second, cruder bound would just add a second
    way to be flaky, not a second way to be correct.

    Catches an implementation that clips merger_timescale_alpha (e.g. at
    -1.0) before deriving expected_slope while leaving the unclipped value
    in the config-echoing path elsewhere -- invisible at -0.5, -0.7, or the
    default -1.0, and invisible to E07 which never varies alpha.
    """
    c = mock
    c2 = copy.deepcopy(c)
    c2["merger_timescale_alpha"] = -1.5
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        MR.run_merger_rate_calculation(c2)
        res = MR.run_merger_rate_validation(c2)
    checked = 0
    for d in res:
        if d["consistent"] is None:
            continue
        checked += 1
        assert d["expected_slope"] == 1.5, d
        assert d["consistent"] is True, d
    assert checked > 0, "no bin had enough usable points -- fixture problem, not a pass"
    # The plan also requires the printed summary to report the same tracked
    # value, but every attempt at a presentation-insensitive regex here
    # ended up either accepting a stale/wrong value or rejecting a
    # differently-but-correctly formatted one (this is the exact defect
    # class E09 had). Deliberately left unchecked rather than reintroducing
    # a format-sensitive assertion; the returned-dict check above is the
    # part of this obligation that is checked here.


def test_E11_alpha_response_relation(mock):
    """docs/MERGER_RATE_PLAN-2SLICE.md:139-161: R(b, z) is proportional to
    (1 + z) ** (-alpha), and "the only source of the slope is the injected
    T_merge(z)". Rerunning only run_merger_rate_calculation at a different
    alpha, with the same generated pair counts, must scale every finite,
    positive rate by exactly (1 + z) ** (delta -alpha) -- an intercept-only
    (normalisation) bug in the alpha-dependent path would leave this ratio
    wrong while every slope-based check (E07, E10) still passes, because a
    per-redshift multiplicative offset does not change a log-log slope.

    Catches an alpha-dependent normalisation error in the calculation
    orchestration that changes only the rate's intercept, not its slope --
    invisible to every existing and new slope/consistency assertion.
    """
    c = mock
    path = os.path.join(c["results_dir"], "merger_rate.hdf5")

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        MR.run_merger_rate_calculation(c)
    # Read eagerly into plain in-memory copies -- the second run below
    # overwrites this same file, and a lazy h5py dataset handle would then
    # silently read the second run's data instead of the first's.
    with h5py.File(path, "r") as f:
        rate_default = np.array(f["merger_rate"][...])
        redshifts_default = np.array(f.attrs["redshifts"], dtype=float)

    c2 = copy.deepcopy(c)
    c2["merger_timescale_alpha"] = -1.5
    with contextlib.redirect_stdout(buf):
        MR.run_merger_rate_calculation(c2)
    with h5py.File(path, "r") as f:
        rate_shifted = np.array(f["merger_rate"][...])
        redshifts_shifted = np.array(f.attrs["redshifts"], dtype=float)

    assert np.array_equal(redshifts_default, redshifts_shifted)
    n_z, n_bins = rate_default.shape
    checked = 0
    for iz in range(n_z):
        z = redshifts_default[iz]
        expected_ratio = (1.0 + z) ** 0.5  # delta(-alpha) = 1.5 - 1.0
        for b in range(n_bins):
            r0 = rate_default[iz, b]
            r1 = rate_shifted[iz, b]
            if not (np.isfinite(r0) and r0 > 0 and np.isfinite(r1) and r1 > 0):
                continue
            checked += 1
            assert math.isclose(r1 / r0, expected_ratio, rel_tol=1e-6), \
                (iz, b, r0, r1, expected_ratio)
    assert checked > 0, "no (bin, redshift) pair had two finite positive rates"

    with contextlib.redirect_stdout(buf):
        res = MR.run_merger_rate_validation(c2)
    checked_bins = 0
    for d in res:
        if d["consistent"] is None:
            continue
        checked_bins += 1
        assert d["consistent"] is True, d
        assert d["expected_slope"] == 1.5, d
    assert checked_bins > 0


def _oracle_fit(rates, errs, redshifts):
    """Independent reimplementation of docs/MERGER_RATE_PLAN-2SLICE.md's
    weighted-least-squares fit (lines 592-625): both variables centred on
    their weighted mean, covariance left unscaled (no residual rescaling),
    same malformed-vs-excluded distinction and collapsed-predictor rule as
    fit_log_rate_vs_redshift itself. Deliberately reimplemented from the
    plan's prose rather than calling the module under test."""
    rates = np.asarray(rates, dtype=float)
    errs = np.asarray(errs, dtype=float)
    redshifts = np.asarray(redshifts, dtype=float)
    usable = np.isfinite(rates) & (rates > 0) & np.isfinite(errs) & (errs > 0)
    n_excluded = int(np.sum(~usable))
    if np.sum(usable) < 2:
        return float("nan"), float("nan"), float("nan"), n_excluded
    x = np.log10(1.0 + redshifts[usable])
    y = np.log10(rates[usable])
    if len(np.unique(x)) < 2:
        return float("nan"), float("nan"), float("nan"), n_excluded
    sigma_log_rate = errs[usable] / (rates[usable] * math.log(10))
    w = 1.0 / sigma_log_rate ** 2
    w_sum = np.sum(w)
    x_mean = np.sum(w * x) / w_sum
    y_mean = np.sum(w * y) / w_sum
    xc = x - x_mean
    yc = y - y_mean
    # Accumulated with unnormalized weights `w`, not the normalized weights
    # (each divided by w_sum) docs/MERGER_RATE_PLAN-2SLICE.md:566-568 tells
    # the *implementation* to use before restoring covariance scale. The
    # two are algebraically identical -- w_sum cancels in slope/intercept,
    # and slope_err's sqrt(1/s_xx) differs only by the same constant factor
    # that a normalized accumulation's "restore covariance scale" step
    # would multiply back in -- so this oracle and the implementation
    # differ only at float-precision level, far below E12's rel_tol=1e-6.
    # Deliberate: this oracle checks the *result*, not the accumulation
    # order, which test_C03/test_C10 already police directly against
    # weighted_fit_core -- enforcing that method is not E12's job.
    s_xx = np.sum(w * xc * xc)
    s_xy = np.sum(w * xc * yc)
    slope = s_xy / s_xx
    intercept = y_mean - slope * x_mean
    slope_err = math.sqrt(1.0 / s_xx)
    return float(slope), float(slope_err), float(intercept), n_excluded


def test_E12_fit_matches_independent_oracle(mock):
    """docs/MERGER_RATE_PLAN-2SLICE.md:521,556,592,625,681-686: the end-to-end
    check "must be allowed to fail loudly if the rate calculation or its
    error propagation is wrong". Recomputes each mass bin's fit independently
    from the persisted merger_rate/merger_rate_err/redshifts using the plan's
    own equations (see _oracle_fit) and compares every field of the returned
    dict, plus the consistency inequality applied here rather than trusted
    from the returned `consistent` flag.

    Catches a validation implementation that unpacks its own fit correctly
    for internal consistency checking but swaps slope_err and intercept (or
    otherwise mis-assembles) the returned per-bin dict -- something every
    existing pure-fit node (which never touches the returned dict's key
    order) and E07 (which never checks slope_err or intercept) would miss.
    """
    c = mock
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        MR.run_merger_rate_calculation(c)
        res = MR.run_merger_rate_validation(c)

    path = os.path.join(c["results_dir"], "merger_rate.hdf5")
    with h5py.File(path, "r") as f:
        merger_rate = np.array(f["merger_rate"][...])
        merger_rate_err = np.array(f["merger_rate_err"][...])
        redshifts = np.array(f.attrs["redshifts"], dtype=float)

    expected_slope = -c["merger_timescale_alpha"]
    assert len(res) == nbins(c)
    checked = 0
    for d in res:
        b = d["mass_bin"]
        slope, slope_err, intercept, n_excluded = _oracle_fit(
            merger_rate[:, b], merger_rate_err[:, b], redshifts)
        assert d["n_excluded"] == n_excluded, d
        if math.isnan(slope):
            assert d["consistent"] is None, d
            assert math.isnan(d["slope"]), d
            continue
        assert d["consistent"] is not None, d
        assert math.isclose(d["slope"], slope, rel_tol=1e-6, abs_tol=1e-9), (d, slope)
        assert math.isclose(d["slope_err"], slope_err, rel_tol=1e-6, abs_tol=1e-9), (d, slope_err)
        assert math.isclose(d["intercept"], intercept, rel_tol=1e-6, abs_tol=1e-9), (d, intercept)
        my_consistent = bool(abs(slope - expected_slope) < 3.0 * slope_err)
        assert d["consistent"] == my_consistent, (d, my_consistent)
        checked += 1
    assert checked > 0


def test_E13_alternate_mass_bin_grid(tmp_path):
    """docs/MERGER_RATE_PLAN-2SLICE.md:260,286,592,681-684: the mass-bin grid
    is config-derived (mass_bin_width), and validation runs "for each mass
    bin", with the consistency criterion applying to "every mass bin with at
    least 2 usable redshift points". Runs the whole pipeline, isolated in a
    fresh temp directory, at a wider-than-default mass_bin_width that still
    divides [log_mass_min, log_mass_max] exactly, and checks the returned
    results correspond to that grid rather than the default six-bin one.

    Catches a hardcoded range(6) (or similarly hardcoded bin count) in
    run_merger_rate_validation while lower-level functions honour the
    config -- every other slice-2 fixture uses the default six-bin grid, so
    this is the only node that would ever see a mismatch.
    """
    c = cfg(data_dir=str(tmp_path / "data") + os.sep,
            results_dir=str(tmp_path / "results") + os.sep,
            figures_dir=str(tmp_path / "figures") + os.sep,
            mass_bin_width=1.0)
    assert (c["log_mass_max"] - c["log_mass_min"]) % c["mass_bin_width"] == 0, \
        "chosen mass_bin_width does not divide the mass range exactly"
    os.makedirs(c["data_dir"], exist_ok=True)
    os.makedirs(c["results_dir"], exist_ok=True)
    expected_n_bins = nbins(c)
    assert expected_n_bins != nbins(BASE), \
        "grid must differ from the default six-bin grid to be discriminating"

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        generate_all_snapshots(c)
        calc.run_calculation(c)
        MR.run_merger_rate_calculation(c)
        res = MR.run_merger_rate_validation(c)

    assert len(res) == expected_n_bins, res
    seen_bins = [d["mass_bin"] for d in res]
    assert all(isinstance(b, int) for b in seen_bins)
    assert seen_bins == sorted(seen_bins), "bin ordering not preserved"
    assert seen_bins == list(range(expected_n_bins)), \
        "mass-bin identifiers must be unique and cover the configured grid"

    eligible = [d for d in res if d["consistent"] is not None]
    assert eligible, "no eligible bin at the wider grid -- fixture problem, not a pass"
    assert all(d["consistent"] is True for d in eligible), eligible
