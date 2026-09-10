"""Slice 1 hidden unit tests: pinned unit criteria derived solely from
docs/MERGER_RATE_PLAN-2SLICE.md's Slice 1 (galaxy-count denominator, pair
fraction, merger timescale, rate conversion, and persistence).

Not visible to the Developer model. Copied into the trial worktree's tests/
directory at grading time and run with the trial's own pytest/venv.

Re-partitioned from ai-agent-bench's Task 001 `hidden_tests/test_hA.py`
(Parts 1-2 only; Part 3 moved to hidden_tests/slice2/test_hA.py) -- see
docs/MODE2-REWRITE-PLAN.md gap G4. All but one test body are unmodified
from that source: `test_B14_docstring_wording` was updated to expect
"this plan's" rather than "Task 001's" in the assertion text, matching
the same wording change made to docs/reference-impl/merger_rate.py's
docstrings (see docs/reference-impl/README.md).
"""
import copy
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import h5py
import numpy as np
import pytest

import calc
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


def assert_rejects_with(pattern, fn, *args, **kwargs):
    with pytest.raises(AssertionError, match=pattern):
        fn(*args, **kwargs)


# ---------------------------------------------------------------- Part 1
def test_A01_calc_exposes_helpers():
    assert callable(calc._mass_bin_edges)
    assert callable(calc._count_galaxies_per_mass_bin)


def test_A02_pinned_count_vector():
    got = calc._count_galaxies_per_mass_bin(
        np.array([7.9, 8.0, 8.5, 10.999, 11.0, 11.1]), BASE)
    assert list(np.asarray(got)) == [1, 1, 0, 0, 0, 1]
    assert np.asarray(got).dtype.kind in "iu"


def test_A03_merger_rate_exposes_slice1_api():
    assert MR is not None
    for n in ("_mass_bin_edges", "_results_path", "_load_pair_counts", "compute_pair_fraction"):
        assert hasattr(MR, n), n


def test_A04_results_path():
    p = MR._results_path(2.0, BASE)
    assert os.path.basename(p) == "pairs_z2.0.hdf5"
    assert os.path.normpath(os.path.dirname(p)) == os.path.normpath(BASE["results_dir"])


def test_A05_pair_fraction_pinned():
    f, s = MR.compute_pair_fraction(np.array([0, 5, 20]), np.array([10, 10, 10]))
    np.testing.assert_allclose(np.asarray(f), [0.0, 0.5, 2.0], rtol=1e-14, atol=0)
    assert np.asarray(s)[0] == 0.0
    np.testing.assert_allclose(
        np.asarray(s)[1:], [0.22360679774997896, 0.4472135954999579],
        rtol=1e-14, atol=0)


def test_A06_zero_zero_bin_exact_zero():
    f, s = MR.compute_pair_fraction(np.array([0, 0]), np.array([0, 10]))
    f, s = np.asarray(f), np.asarray(s)
    assert f[0] == 0.0 and s[0] == 0.0
    assert np.all(np.isfinite(f)) and np.all(np.isfinite(s))


def test_A07_pairs_without_galaxies_rejected():
    assert rejects(MR.compute_pair_fraction, np.array([1]), np.array([0])) == "assert"


def test_A08_shape_mismatch_rejected():
    assert rejects(MR.compute_pair_fraction, np.array([1, 2]), np.array([1])) == "assert"


def test_A09_non_1d_rejected():
    assert rejects(MR.compute_pair_fraction,
                   np.array([[1, 2]]), np.array([[3, 4]])) == "assert"


def test_A10_negative_rejected():
    assert rejects(MR.compute_pair_fraction, np.array([-1]), np.array([10])) == "assert"
    assert rejects(MR.compute_pair_fraction, np.array([1]), np.array([-10])) == "assert"


def test_A11_nonfinite_rejected():
    assert rejects(MR.compute_pair_fraction, np.array([np.nan]), np.array([10.0])) == "assert"
    assert rejects(MR.compute_pair_fraction, np.array([np.inf]), np.array([10.0])) == "assert"
    assert rejects(MR.compute_pair_fraction, np.array([1.0]), np.array([np.nan])) == "assert"


def test_A12_non_integer_valued_rejected():
    assert rejects(MR.compute_pair_fraction, np.array([1.5]), np.array([10.0])) == "assert"
    assert rejects(MR.compute_pair_fraction, np.array([1.0]), np.array([10.5])) == "assert"


def test_A13_int_dtype_and_integer_float_both_accepted():
    f1, s1 = MR.compute_pair_fraction(np.array([5], dtype=np.int64), np.array([10], dtype=np.int64))
    f2, s2 = MR.compute_pair_fraction(np.array([5.0]), np.array([10.0]))
    assert float(np.asarray(f1)[0]) == 0.5 and float(np.asarray(f2)[0]) == 0.5


# -- _load_pair_counts fixtures ------------------------------------------
def _write_pairs_file(path, mass_bin, n_gal, box=500.0, z=2.0, omit=None, bad_attr=None):
    omit = omit or set()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    n = len(mass_bin)
    with h5py.File(path, "w") as f:
        f.create_dataset("mass_primary", data=np.full(n, 10.0))
        f.create_dataset("mass_secondary", data=np.full(n, 9.0))
        f.create_dataset("mass_ratio", data=np.full(n, 0.5))
        f.create_dataset("separation_kpc", data=np.full(n, 10.0))
        f.create_dataset("delta_v", data=np.full(n, 100.0))
        f.create_dataset("sep_bin", data=np.zeros(n, dtype=np.int64))
        if "mass_bin" not in omit:
            f.create_dataset("mass_bin", data=np.asarray(mass_bin, dtype=np.int64))
        if "n_galaxies_per_mass_bin" not in omit:
            f.create_dataset("n_galaxies_per_mass_bin", data=np.asarray(n_gal, dtype=np.int64))
        f.attrs["redshift"] = z
        f.attrs["n_pairs"] = n
        f.attrs["timestamp"] = "x"
        f.attrs["mass_bin_by"] = "primary"
        f.attrs["mass_ratio_min"] = 0.1
        f.attrs["max_sep_kpc"] = 25.0
        if "box_size_mpc" not in omit:
            f.attrs["box_size_mpc"] = box if bad_attr is None else bad_attr
    return path


def test_A14_load_pair_counts_values_and_sentinel(tmp_path):
    c = cfg(results_dir=str(tmp_path) + os.sep)
    _write_pairs_file(MR._results_path(2.0, c), [0, 0, 1, 5, -1, -1, 3],
                      [7, 8, 9, 10, 11, 12], box=321.0)
    npair, ngal, box = MR._load_pair_counts(2.0, c)
    assert list(np.asarray(npair)) == [2, 1, 0, 1, 0, 1]
    assert list(np.asarray(ngal)) == [7, 8, 9, 10, 11, 12]
    assert float(box) == 321.0
    assert np.asarray(npair).dtype.kind in "iu"
    assert np.asarray(ngal).dtype.kind in "iu"


def test_A15_load_pair_counts_bad_bin_index(tmp_path):
    c = cfg(results_dir=str(tmp_path) + os.sep)
    _write_pairs_file(MR._results_path(2.0, c), [0, 6], [1] * 6)
    r = rejects(MR._load_pair_counts, 2.0, c)
    assert r == "assert", r
    c2 = cfg(results_dir=str(tmp_path / "b") + os.sep)
    _write_pairs_file(MR._results_path(2.0, c2), [0, -2], [1] * 6)
    r = rejects(MR._load_pair_counts, 2.0, c2)
    assert r == "assert", r


def test_A16_load_pair_counts_missing_file(tmp_path):
    c = cfg(results_dir=str(tmp_path) + os.sep)
    r = rejects(MR._load_pair_counts, 2.0, c)
    assert r in ("assert", "FileNotFoundError"), r


def test_A17_load_pair_counts_missing_dataset(tmp_path):
    c = cfg(results_dir=str(tmp_path) + os.sep)
    _write_pairs_file(MR._results_path(2.0, c), [0], [1] * 6, omit={"n_galaxies_per_mass_bin"})
    assert rejects(MR._load_pair_counts, 2.0, c) == "assert"
    c2 = cfg(results_dir=str(tmp_path / "mass-bin") + os.sep)
    _write_pairs_file(MR._results_path(2.0, c2), [0], [1] * 6, omit={"mass_bin"})
    assert_rejects_with("mass_bin", MR._load_pair_counts, 2.0, c2)


def test_A18_load_pair_counts_missing_attr(tmp_path):
    c = cfg(results_dir=str(tmp_path) + os.sep)
    _write_pairs_file(MR._results_path(2.0, c), [0], [1] * 6, omit={"box_size_mpc"})
    assert rejects(MR._load_pair_counts, 2.0, c) == "assert"


def test_A19_load_pair_counts_wrong_length(tmp_path):
    c = cfg(results_dir=str(tmp_path) + os.sep)
    _write_pairs_file(MR._results_path(2.0, c), [0], [1, 2, 3])
    assert rejects(MR._load_pair_counts, 2.0, c) == "assert"


def test_A20_load_pair_counts_bad_box(tmp_path):
    for i, bad in enumerate([0.0, -1.0, float("nan"), float("inf")]):
        c = cfg(results_dir=str(tmp_path / f"d{i}") + os.sep)
        _write_pairs_file(MR._results_path(2.0, c), [0], [1] * 6, bad_attr=bad)
        r = rejects(MR._load_pair_counts, 2.0, c)
        assert r == "assert", (bad, r)


def test_A21_load_pair_counts_vector_box_attr(tmp_path):
    """Form-before-coercion: a vector box_size_mpc must assert, not leak TypeError."""
    c = cfg(results_dir=str(tmp_path) + os.sep)
    _write_pairs_file(MR._results_path(2.0, c), [0], [1] * 6, bad_attr=np.array([500.0, 1.0]))
    r = rejects(MR._load_pair_counts, 2.0, c)
    assert r == "assert", r


def test_A22_load_pair_counts_rejects_non_numeric_scalar_box_attr(tmp_path):
    for i, bad in enumerate(["500.0", b"500.0", 500.0 + 0.0j, True]):
        c = cfg(results_dir=str(tmp_path / f"bad-form-{i}") + os.sep)
        _write_pairs_file(MR._results_path(2.0, c), [0], [1] * 6, bad_attr=bad)
        assert rejects(MR._load_pair_counts, 2.0, c) == "assert", bad


def test_A23_part1_helpers_do_not_require_mass_bin_by(tmp_path):
    c = cfg(results_dir=str(tmp_path) + os.sep)
    c.pop("mass_bin_by")
    assert len(calc._mass_bin_edges(c)) - 1 == nbins(c)
    got = calc._count_galaxies_per_mass_bin(np.array([8.1, 8.6]), c)
    assert list(np.asarray(got)[:2]) == [1, 1]
    assert len(MR._mass_bin_edges(c)) - 1 == nbins(c)
    _write_pairs_file(MR._results_path(2.0, c), [0, 1], [1] * nbins(c))
    npair, ngal, box = MR._load_pair_counts(2.0, c)
    assert list(np.asarray(npair)[:2]) == [1, 1]
    assert len(ngal) == nbins(c) and float(box) == 500.0


# ---------------------------------------------------------------- Part 2
def test_B01_config_keys():
    for k, v in (("merger_timescale_gyr0", 2.2), ("merger_timescale_alpha", -1.0),
                 ("merger_fraction", 0.6)):
        assert k in BASE, k
        assert BASE[k] == v, (k, BASE[k])
    assert BASE["box_size"] == 500.0 and BASE["redshifts"] == [2.0, 3.0, 4.0, 5.0]


def test_B02_timescale_at_zero_exact():
    assert MR.merger_timescale_gyr(0, BASE) == BASE["merger_timescale_gyr0"]


def test_B03_timescale_pinned():
    c = cfg(merger_timescale_gyr0=2.5, merger_timescale_alpha=-0.5)
    np.testing.assert_allclose(
        MR.merger_timescale_gyr(3, c), 1.25, rtol=1e-14, atol=0)


def test_B04_merger_rate_pinned():
    r, s = MR.compute_merger_rate(np.array([0.5]), np.array([0.1]), np.array([10]),
                                  500.0, 2.2, 0.6)
    np.testing.assert_allclose(
        float(np.asarray(r)[0]), 1.090909090909091e-08, rtol=1e-14, atol=0)
    np.testing.assert_allclose(
        float(np.asarray(s)[0]), 2.181818181818182e-09, rtol=1e-14, atol=0)


def test_B05_reduced_identity_exact():
    r, _ = MR.compute_merger_rate(np.array([0.5]), np.array([0.1]), np.array([10]),
                                  500.0, 2.2, 0.6)
    np.testing.assert_allclose(
        float(np.asarray(r)[0]), 0.6 * 5 / (500.0 ** 3 * 2.2),
        rtol=1e-14, atol=0)


def test_B06_zero_sigma_exact_zero():
    r, s = MR.compute_merger_rate(np.array([0.5, 0.0]), np.array([0.0, 0.0]),
                                  np.array([10, 10]), 500.0, 2.2, 0.6)
    assert float(np.asarray(s)[0]) == 0.0 and float(np.asarray(s)[1]) == 0.0


def test_B07_zero_galaxies_rules():
    r, s = MR.compute_merger_rate(np.array([0.0]), np.array([0.0]), np.array([0]),
                                  500.0, 2.2, 0.6)
    assert float(np.asarray(r)[0]) == 0.0 and float(np.asarray(s)[0]) == 0.0
    assert rejects(MR.compute_merger_rate, np.array([0.5]), np.array([0.0]),
                   np.array([0]), 500.0, 2.2, 0.6) == "assert"
    assert rejects(MR.compute_merger_rate, np.array([0.0]), np.array([0.5]),
                   np.array([0]), 500.0, 2.2, 0.6) == "assert"


def test_B08_mass_bin_by_assertion(tmp_path):
    c = cfg(mass_bin_by="mean", results_dir=str(tmp_path) + os.sep)
    try:
        MR.run_merger_rate_calculation(c)
    except AssertionError as e:
        assert "mean" in str(e), str(e)
        return
    except Exception as e:
        pytest.fail(f"wrong exception {type(e).__name__}: {e}")
    pytest.fail("no rejection")


def test_B09_timescale_rejections():
    for z in (-1.0, -2.0, float("nan"), float("inf")):
        assert rejects(MR.merger_timescale_gyr, z, BASE) == "assert", z
    for bad in ({"merger_timescale_gyr0": 0.0}, {"merger_timescale_gyr0": -1.0},
                {"merger_timescale_gyr0": float("nan")},
                {"merger_timescale_gyr0": float("inf")},
                {"merger_timescale_alpha": float("nan")},
                {"merger_timescale_alpha": float("inf")}):
        assert rejects(MR.merger_timescale_gyr, 1.0, cfg(**bad)) == "assert", bad
    assert rejects(
        MR.merger_timescale_gyr, 1.0,
        cfg(merger_timescale_gyr0=1e308, merger_timescale_alpha=2.0)) == "assert"


def test_B10_timescale_rejects_string_and_array():
    bad_forms = ("1.0", b"1.0", 1.0 + 0.0j, True,
                 np.array(1.0), np.array([1.0, 2.0]))
    for bad in bad_forms:
        assert rejects(MR.merger_timescale_gyr, bad, BASE) == "assert", bad
    for key in ("merger_timescale_gyr0", "merger_timescale_alpha"):
        for bad in bad_forms:
            assert rejects(MR.merger_timescale_gyr, 1.0, cfg(**{key: bad})) == "assert", (key, bad)
    assert np.isfinite(MR.merger_timescale_gyr(
        np.float64(1.0), cfg(merger_timescale_gyr0=np.int64(2),
                             merger_timescale_alpha=np.float32(-0.5))))


def test_B11_merger_rate_scalar_rejections():
    ok = (np.array([0.5]), np.array([0.1]), np.array([10]))
    for box in (0.0, -1.0, float("nan"), float("inf")):
        assert rejects(MR.compute_merger_rate, *ok, box, 2.2, 0.6) == "assert", box
    for t in (0.0, -1.0, float("nan"), float("inf")):
        assert rejects(MR.compute_merger_rate, *ok, 500.0, t, 0.6) == "assert", t
    for mf in (0.0, -0.1, 1.5, float("nan"), float("inf")):
        assert rejects(MR.compute_merger_rate, *ok, 500.0, 2.2, mf) == "assert", mf
    bad_forms = ("500.0", b"500.0", 500.0 + 0.0j, True,
                 np.array(500.0), np.array([500.0]))
    for bad in bad_forms:
        assert rejects(MR.compute_merger_rate, *ok, bad, 2.2, 0.6) == "assert", ("box", bad)
        assert rejects(MR.compute_merger_rate, *ok, 500.0, bad, 0.6) == "assert", ("time", bad)
        assert rejects(MR.compute_merger_rate, *ok, 500.0, 2.2, bad) == "assert", ("fraction", bad)
    r, s = MR.compute_merger_rate(*ok, np.int64(500), np.float32(2.2), np.float64(0.6))
    assert np.all(np.isfinite(r)) and np.all(np.isfinite(s))


def test_B12_merger_rate_array_rejections():
    assert rejects(MR.compute_merger_rate, np.array([0.5, 0.5]), np.array([0.1]),
                   np.array([10]), 500.0, 2.2, 0.6) == "assert"
    assert rejects(MR.compute_merger_rate, np.array([[0.5]]), np.array([[0.1]]),
                   np.array([[10]]), 500.0, 2.2, 0.6) == "assert"
    assert rejects(MR.compute_merger_rate, np.array([-0.5]), np.array([0.1]),
                   np.array([10]), 500.0, 2.2, 0.6) == "assert"
    assert rejects(MR.compute_merger_rate, np.array([np.nan]), np.array([0.1]),
                   np.array([10]), 500.0, 2.2, 0.6) == "assert"
    assert rejects(MR.compute_merger_rate, np.array([0.5]), np.array([np.inf]),
                   np.array([10]), 500.0, 2.2, 0.6) == "assert"
    assert rejects(MR.compute_merger_rate, np.array([0.5]), np.array([0.1]),
                   np.array([10.5]), 500.0, 2.2, 0.6) == "assert"
    for fp, sf, ng in (
        (np.array([0.5]), np.array([-0.1]), np.array([10])),
        (np.array([0.5]), np.array([np.nan]), np.array([10])),
        (np.array([0.5]), np.array([0.1]), np.array([-1])),
        (np.array([0.5]), np.array([0.1]), np.array([np.inf])),
    ):
        assert rejects(MR.compute_merger_rate, fp, sf, ng, 500.0, 2.2, 0.6) == "assert"


def test_B13_merger_rate_rejects_string_box_by_assertion():
    """Spec's named example: a string must not be silently accepted."""
    r = rejects(MR.compute_merger_rate, np.array([0.5]), np.array([0.1]),
                np.array([10]), "500.0", 2.2, 0.6)
    assert r == "assert", r


def test_B14_docstring_wording():
    import inspect
    required = ("Uncertainty follows this plan's plug-in Poisson-error convention; "
                "it is not a confidence interval.")
    for fn in (MR.compute_pair_fraction, MR.compute_merger_rate):
        doc = inspect.getdoc(fn)
        assert doc is not None, f"{fn.__name__} has no docstring"
        assert required in doc, f"{fn.__name__} lacks the required uncertainty wording"


def test_B15_rejection_messages_name_the_reason():
    assert_rejects_with("shape", MR.compute_pair_fraction,
                        np.array([1, 2]), np.array([1]))
    assert_rejects_with("non-negative", MR.compute_pair_fraction,
                        np.array([-1]), np.array([1]))
    assert_rejects_with("finite", MR.compute_pair_fraction,
                        np.array([np.nan]), np.array([1.0]))
    assert_rejects_with("integer", MR.compute_pair_fraction,
                        np.array([0.5]), np.array([1.0]))
    assert_rejects_with("n_pairs", MR.compute_pair_fraction,
                        np.array([1]), np.array([0]))
    assert_rejects_with("z", MR.merger_timescale_gyr, "1.0", BASE)
    assert_rejects_with("merger_timescale_gyr0", MR.merger_timescale_gyr, 1.0,
                        cfg(merger_timescale_gyr0=0.0))
    ok = (np.array([0.5]), np.array([0.1]), np.array([10]))
    assert_rejects_with("box_size_mpc", MR.compute_merger_rate, *ok, "500.0", 2.2, 0.6)
    assert_rejects_with("merger_fraction", MR.compute_merger_rate, *ok, 500.0, 2.2, 2.0)
