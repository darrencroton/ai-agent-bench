"""Hidden Harness A: pure-function criteria derived solely from spec.md.

Not visible to the Developer model. Copied into the trial worktree's tests/
directory at grade time and run with the trial's own pytest/venv. Scores the
"correctness" rubric category together with test_hB.py.

Everything here is in-memory: no data file, no results file, no output file.
"""
import copy
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np
import pytest  # noqa: F401  (imported for parity with the rest of the suite)

import config as cfgmod

try:
    import pair_binning as PB
except Exception as e:                      # pragma: no cover
    PB = None
    _PB_ERR = e

BASE = cfgmod.config

# The pinned pair sample of spec.md Part 1. Six pairs exercising: both members
# in one bin (0 and 2), members straddling two bins (1 and 4), a primary
# exactly on the excluded upper edge (3), and both members on it (5).
FIX_PRIMARY = np.array([8.2, 9.7, 10.6, 11.0, 10.2, 11.0])
FIX_SECONDARY = np.array([8.1, 8.9, 10.6, 10.4, 9.5, 11.0])

# Ground truth under spec.md section 4's incidence-set definition.
EXPECT_PRIMARY = [1, 0, 0, 1, 1, 1]
EXPECT_SECONDARY = [1, 1, 0, 1, 1, 1]
EXPECT_EITHER = [2, 1, 0, 2, 2, 2]
EXPECT_EXCLUDED = {"primary": 2, "secondary": 1, "either": 1}

PAIRFRAC_SENTENCE = (
    "Under the 'either' convention the numerator counts galaxy-pair incidences "
    "rather than independent pairs, so this plug-in Poisson error is an "
    "approximation and not a confidence interval."
)


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


def norm(text):
    """Collapse whitespace so a wrapped docstring/heading still matches verbatim."""
    return re.sub(r"\s+", " ", text or "").strip()


def reject_message(fn, *a, **k):
    """Like rejects(), but returns the AssertionError's message text (or None)."""
    try:
        fn(*a, **k)
    except AssertionError as e:
        return str(e)
    except Exception:
        return None
    return None


# ---------------------------------------------------------------- API

def test_A01_module_exposes_api():
    assert PB is not None
    for n in ("_mass_bin_edges", "_data_path", "_results_path",
              "count_galaxies_per_mass_bin", "count_pairs_per_mass_bin",
              "count_excluded_pairs", "compute_pair_fraction", "check_additivity"):
        assert hasattr(PB, n), n
        assert callable(getattr(PB, n)), n


def test_A02_paths_match_calc_convention():
    d = PB._data_path(2.0, BASE)
    r = PB._results_path(3.0, BASE)
    assert os.path.basename(d) == "test_z2.0.hdf5"
    assert os.path.basename(r) == "pairs_z3.0.hdf5"
    assert os.path.normpath(os.path.dirname(d)) == os.path.normpath(BASE["data_dir"])
    assert os.path.normpath(os.path.dirname(r)) == os.path.normpath(BASE["results_dir"])


def test_A03_mass_bin_edges():
    edges = np.asarray(PB._mass_bin_edges(BASE))
    assert edges.shape == (nbins() + 1,)
    np.testing.assert_allclose(edges, np.linspace(8.0, 11.0, 7), rtol=0, atol=0)


# ------------------------------------------------- denominator counting

def test_A04_pinned_galaxy_count_vector():
    got_raw = PB.count_galaxies_per_mass_bin(
        np.array([7.99, 8.0, 8.499, 8.5, 9.75, 10.5, 10.9999, 11.0]), BASE)
    assert isinstance(got_raw, np.ndarray), (
        f"count_galaxies_per_mass_bin must return an ndarray, not {type(got_raw).__name__}")
    got = np.asarray(got_raw)
    assert list(got) == [2, 1, 0, 1, 0, 2]
    assert got.dtype.kind in "iu"
    assert got.shape == (nbins(),)


def test_A05_galaxy_count_is_convention_independent():
    """spec.md section 5 D1-D3: the denominator has no convention axis."""
    masses = np.array([7.99, 8.0, 8.499, 8.5, 9.75, 10.5, 10.9999, 11.0])
    reference = list(np.asarray(PB.count_galaxies_per_mass_bin(masses, BASE)))

    no_key = cfg()
    no_key.pop("mass_bin_by", None)
    assert list(np.asarray(PB.count_galaxies_per_mass_bin(masses, no_key))) == reference

    for value in ("primary", "secondary", "either", "mean", "total", "not-a-convention"):
        c = cfg(mass_bin_by=value)
        assert list(np.asarray(PB.count_galaxies_per_mass_bin(masses, c))) == reference, value


@pytest.mark.parametrize("bad,keywords", [
    (np.array([[8.0, 9.0]]), ("1d", "dimension", "ndim", "shape")),
    (np.array([np.nan]), ("finite", "nan")),
    (np.array([np.inf]), ("finite", "inf")),
    (np.array([8.0 + 1j]), ("complex",)),
    (np.array(["8.0"]), ("numeric", "real", "dtype", "float")),
])
def test_A06_galaxy_count_rejections(bad, keywords):
    """Both the rejection kind AND a message identifying why (spec.md's
    'clear message naming the offending value' clause) -- a bare
    `assert False` would satisfy the type check alone."""
    assert rejects(PB.count_galaxies_per_mass_bin, bad, BASE) == "assert"
    msg = reject_message(PB.count_galaxies_per_mass_bin, bad, BASE)
    assert msg, f"assertion for {bad!r} carried no message"
    low = msg.lower()
    assert "log_stellar_mass" in low or any(k in low for k in keywords), msg


# ---------------------------------------------------- numerator counting

def test_A07_pinned_pair_counts_all_conventions():
    got = {}
    for convention, expected in (("primary", EXPECT_PRIMARY),
                                 ("secondary", EXPECT_SECONDARY),
                                 ("either", EXPECT_EITHER)):
        raw = PB.count_pairs_per_mass_bin(FIX_PRIMARY, FIX_SECONDARY, convention, BASE)
        assert isinstance(raw, np.ndarray), (
            f"count_pairs_per_mass_bin must return an ndarray, not "
            f"{type(raw).__name__} ({convention})")
        arr = np.asarray(raw)
        assert arr.dtype.kind in "iu", convention
        assert arr.shape == (nbins(),), convention
        assert list(arr) == expected, convention
        got[convention] = list(arr)
    # The three conventions must genuinely differ, and "either" is not a copy.
    assert got["primary"] != got["secondary"]
    assert got["either"] != got["primary"]
    assert got["either"] != got["secondary"]


def test_A08_pinned_excluded_pair_counts():
    for convention, expected in EXPECT_EXCLUDED.items():
        got = PB.count_excluded_pairs(FIX_PRIMARY, FIX_SECONDARY, convention, BASE)
        assert int(got) == expected, convention
        assert not isinstance(got, bool)
        # spec.md: "a Python or NumPy integer scalar" -- not a float like 1.0.
        assert isinstance(got, (int, np.integer)), (
            f"count_excluded_pairs must return an int-kind scalar, "
            f"got {type(got).__name__} ({convention})")


def test_A09_additivity_identity_on_fixture():
    counts = {c: np.asarray(PB.count_pairs_per_mass_bin(FIX_PRIMARY, FIX_SECONDARY, c, BASE))
              for c in ("primary", "secondary", "either")}
    np.testing.assert_array_equal(counts["primary"] + counts["secondary"], counts["either"])
    assert PB.check_additivity(counts["primary"], counts["secondary"], counts["either"]) is True


def test_A10_exclusion_sum_rule_on_fixture():
    n_total = len(FIX_PRIMARY)
    for convention in ("primary", "secondary"):
        counted = int(np.sum(np.asarray(
            PB.count_pairs_per_mass_bin(FIX_PRIMARY, FIX_SECONDARY, convention, BASE))))
        excluded = int(PB.count_excluded_pairs(FIX_PRIMARY, FIX_SECONDARY, convention, BASE))
        assert counted + excluded == n_total, convention


def test_A11_both_members_in_one_bin_contribute_two_incidences():
    """The counting rule that separates a correct 'either' from a wrong one."""
    p = np.array([10.6])
    s = np.array([10.6])
    either = np.asarray(PB.count_pairs_per_mass_bin(p, s, "either", BASE))
    assert list(either) == [0, 0, 0, 0, 0, 2]
    assert list(np.asarray(PB.count_pairs_per_mass_bin(p, s, "primary", BASE))) == [0, 0, 0, 0, 0, 1]
    assert list(np.asarray(PB.count_pairs_per_mass_bin(p, s, "secondary", BASE))) == [0, 0, 0, 0, 0, 1]


def test_A12_members_in_different_bins_split_across_bins():
    p = np.array([9.7])
    s = np.array([8.9])
    either = np.asarray(PB.count_pairs_per_mass_bin(p, s, "either", BASE))
    assert list(either) == [0, 1, 0, 1, 0, 0]


def test_A13_zero_length_pair_sample():
    empty = np.array([], dtype=float)
    for convention in ("primary", "secondary", "either"):
        arr = np.asarray(PB.count_pairs_per_mass_bin(empty, empty, convention, BASE))
        assert arr.shape == (nbins(),), convention
        assert arr.dtype.kind in "iu", convention
        assert list(arr) == [0] * nbins(), convention
        assert int(PB.count_excluded_pairs(empty, empty, convention, BASE)) == 0, convention


def test_A14_zero_length_galaxy_sample():
    arr = np.asarray(PB.count_galaxies_per_mass_bin(np.array([], dtype=float), BASE))
    assert list(arr) == [0] * nbins()
    assert arr.dtype.kind in "iu"


@pytest.mark.parametrize("fn", [PB.count_pairs_per_mass_bin, PB.count_excluded_pairs])
@pytest.mark.parametrize("bad", ["mean", "total", "Primary", "", "eiher", None, 3, ["primary"]])
def test_A15_unsupported_conventions_rejected(fn, bad):
    """Both the rejection kind AND a message naming the bad convention."""
    assert rejects(fn, FIX_PRIMARY, FIX_SECONDARY, bad, BASE) == "assert", (fn, bad)
    msg = reject_message(fn, FIX_PRIMARY, FIX_SECONDARY, bad, BASE)
    assert msg, f"assertion for convention={bad!r} carried no message"
    low = msg.lower()
    assert "convention" in low, msg


@pytest.mark.parametrize("fn", [PB.count_pairs_per_mass_bin, PB.count_excluded_pairs])
@pytest.mark.parametrize("primary,secondary,keywords", [
    (np.array([9.0, 9.0]), np.array([8.0]), ("shape", "match", "length", "len")),
    (np.array([[9.0]]), np.array([[8.0]]), ("1d", "dimension", "ndim", "shape")),
    (np.array([np.nan]), np.array([8.0]), ("finite", "nan")),
    (np.array([9.0]), np.array([np.inf]), ("finite", "inf")),
    (np.array([9.0 + 1j]), np.array([8.0 + 0j]), ("complex",)),
    (np.array(["9.0"]), np.array(["8.0"]), ("numeric", "real", "dtype", "float")),
    (np.array([8.0]), np.array([9.0]), ("secondary", "primary", "order", "<=", "invariant")),
])
def test_A16_pair_array_rejections(fn, primary, secondary, keywords):
    assert rejects(fn, primary, secondary, "primary", BASE) == "assert"
    msg = reject_message(fn, primary, secondary, "primary", BASE)
    assert msg, f"assertion for {(primary, secondary)!r} carried no message"
    low = msg.lower()
    assert ("log_mass_primary" in low or "log_mass_secondary" in low
            or any(k in low for k in keywords)), msg


@pytest.mark.parametrize("fn", [PB.count_pairs_per_mass_bin, PB.count_excluded_pairs])
def test_A16b_ordering_invariant_violation_on_two_element_array(fn):
    assert rejects(fn, np.array([9.0, 8.0]), np.array([8.0, 9.0]), "either", BASE) == "assert"


def test_A17_equal_masses_are_valid_not_a_violation():
    """secondary == primary is the tie case find_pairs produces, not an error."""
    p = np.array([9.25])
    s = np.array([9.25])
    assert list(np.asarray(PB.count_pairs_per_mass_bin(p, s, "either", BASE))) == [0, 0, 2, 0, 0, 0]
    assert list(np.asarray(PB.count_pairs_per_mass_bin(p, s, "primary", BASE))) == [0, 0, 1, 0, 0, 0]
    assert int(PB.count_excluded_pairs(p, s, "either", BASE)) == 0


# ------------------------------------------------------- pair fraction

def test_A18_pair_fraction_pinned():
    f_raw, s_raw = PB.compute_pair_fraction(np.array([0, 4, 9]), np.array([4, 16, 4]))
    assert isinstance(f_raw, np.ndarray), (
        f"compute_pair_fraction must return f_pair as an ndarray, not {type(f_raw).__name__}")
    assert isinstance(s_raw, np.ndarray), (
        f"compute_pair_fraction must return sigma_f_pair as an ndarray, not {type(s_raw).__name__}")
    f, s = np.asarray(f_raw), np.asarray(s_raw)
    assert f[0] == 0.0 and s[0] == 0.0
    np.testing.assert_allclose(f[1:], [0.25, 2.25], rtol=1e-14, atol=0)
    np.testing.assert_allclose(s[1:], [0.125, 0.75], rtol=1e-14, atol=0)


def test_A19_pair_fraction_accepts_integer_valued_floats():
    f, s = PB.compute_pair_fraction(np.array([0.0, 4.0, 9.0]), np.array([4.0, 16.0, 4.0]))
    np.testing.assert_allclose(np.asarray(f)[1:], [0.25, 2.25], rtol=1e-14, atol=0)
    np.testing.assert_allclose(np.asarray(s)[1:], [0.125, 0.75], rtol=1e-14, atol=0)


def test_A20_zero_zero_bin_exact_zero():
    f, s = PB.compute_pair_fraction(np.array([0, 0]), np.array([0, 10]))
    f, s = np.asarray(f), np.asarray(s)
    assert f[0] == 0.0 and s[0] == 0.0
    assert np.all(np.isfinite(f)) and np.all(np.isfinite(s))


def test_A21_incidence_without_galaxies_rejected():
    assert rejects(PB.compute_pair_fraction, np.array([1]), np.array([0])) == "assert"


@pytest.mark.parametrize("npair,ngal,keywords", [
    (np.array([1, 2]), np.array([1]), ("shape", "match", "length", "len")),
    (np.array([[1, 2]]), np.array([[3, 4]]), ("1d", "dimension", "ndim", "shape")),
    (np.array([-1]), np.array([10]), ("negative", "non-negative", ">=0", ">= 0")),
    (np.array([1]), np.array([-10]), ("negative", "non-negative", ">=0", ">= 0")),
    (np.array([np.nan]), np.array([10.0]), ("finite", "nan")),
    (np.array([np.inf]), np.array([10.0]), ("finite", "inf")),
    (np.array([1.0]), np.array([np.nan]), ("finite", "nan")),
    (np.array([1.5]), np.array([10.0]), ("integer",)),
    (np.array([1.0]), np.array([10.5]), ("integer",)),
    (np.array([1 + 0j]), np.array([10 + 0j]), ("complex",)),
    (np.array(["1"]), np.array(["10"]), ("numeric", "real", "dtype", "float")),
])
def test_A22_pair_fraction_rejections(npair, ngal, keywords):
    assert rejects(PB.compute_pair_fraction, npair, ngal) == "assert"
    msg = reject_message(PB.compute_pair_fraction, npair, ngal)
    assert msg, f"assertion for {(npair, ngal)!r} carried no message"
    low = msg.lower()
    assert "n_pairs" in low or "n_galaxies" in low or any(k in low for k in keywords), msg


def test_A23_pair_fraction_docstring_sentence_verbatim():
    doc = norm(PB.compute_pair_fraction.__doc__)
    assert norm(PAIRFRAC_SENTENCE) in doc


# ---------------------------------------------------- additivity check

def test_A24_check_additivity_true_and_false_without_raising():
    assert PB.check_additivity([1, 2], [3, 4], [4, 6]) is True
    assert PB.check_additivity([0, 0], [0, 0], [0, 0]) is True
    assert PB.check_additivity([1, 2], [3, 4], [4, 7]) is False
    # the classic wrong 'either': a both-in-bin pair counted once
    assert PB.check_additivity([1, 0], [1, 0], [1, 0]) is False


@pytest.mark.parametrize("a1,a2,a3,keywords", [
    ([[1]], [[1]], [[2]], ("1d", "dimension", "ndim", "shape")),
    ([1, 2], [1], [2, 3], ("shape", "match", "length", "len")),
    ([1.5], [1], [2.5], ("integer",)),
    ([-1], [1], [0], ("negative", "non-negative", ">=0", ">= 0")),
    ([np.nan], [1.0], [1.0], ("finite", "nan")),
    ([np.inf], [1.0], [1.0], ("finite", "inf")),
    (["1"], ["1"], ["2"], ("numeric", "real", "dtype", "float")),
    ([1 + 0j], [1 + 0j], [2 + 0j], ("complex",)),
])
def test_A25_check_additivity_rejections(a1, a2, a3, keywords):
    assert rejects(PB.check_additivity, a1, a2, a3) == "assert"
    msg = reject_message(PB.check_additivity, a1, a2, a3)
    assert msg, f"assertion for {(a1, a2, a3)!r} carried no message"
    low = msg.lower()
    assert ("n_primary" in low or "n_secondary" in low or "n_either" in low
            or any(k in low for k in keywords)), msg


# ------------------------------------------------- config, not defaults

# The frozen baseline config (src/config.py before Part 2's single-key edit).
# Comparing every key -- not just mass_bin_by -- against this catches any
# other existing key being changed in value, dropped, or repurposed.
EXPECTED_BASE_CONFIG = dict(
    box_size=500.0,
    redshifts=[2.0, 3.0, 4.0, 5.0],
    log_mass_min=8.0,
    log_mass_max=11.0,
    mass_ratio_min=0.1,
    mass_bin_width=0.5,
    sep_bins=[0, 10, 15, 20, 25],
    vel_bin_width=20.0,
    vel_max=1000.0,
    max_sep=25.0,
    mass_bin_by="primary",
    data_dir="data/",
    results_dir="results/",
    figures_dir="figures/",
)


def test_A26_config_gains_one_key_and_keeps_the_frozen_one():
    """Part 2's config contract: exactly one key added, nothing existing
    changed. Comparing only mass_bin_by (as the original test did) would
    miss any other existing key being silently altered."""
    assert list(BASE["pair_binning_conventions"]) == ["primary", "secondary", "either"]
    assert BASE["mass_bin_by"] == "primary"

    assert set(BASE.keys()) == set(EXPECTED_BASE_CONFIG.keys()) | {"pair_binning_conventions"}
    for key, expected in EXPECTED_BASE_CONFIG.items():
        assert BASE[key] == expected, (
            f"config[{key!r}] changed from the frozen baseline: "
            f"got {BASE[key]!r}, expected {expected!r}")


def test_A27_binning_follows_config_not_the_defaults():
    """A hardcoded [8.0, 11.0, 0.5) bin grid passes every default-config test."""
    c = cfg(log_mass_min=9.0, log_mass_max=12.0, mass_bin_width=1.5)  # 2 bins
    np.testing.assert_allclose(np.asarray(PB._mass_bin_edges(c)),
                               [9.0, 10.5, 12.0], rtol=0, atol=0)

    gal = np.asarray(PB.count_galaxies_per_mass_bin(
        np.array([8.9, 9.0, 10.4, 10.5, 11.9, 12.0]), c))
    assert list(gal) == [2, 2]          # 8.9 below the range, 12.0 on the excluded edge

    p = np.array([10.6, 11.0])
    s = np.array([9.5, 10.0])
    assert list(np.asarray(PB.count_pairs_per_mass_bin(p, s, "primary", c))) == [0, 2]
    assert list(np.asarray(PB.count_pairs_per_mass_bin(p, s, "secondary", c))) == [2, 0]
    assert list(np.asarray(PB.count_pairs_per_mass_bin(p, s, "either", c))) == [2, 2]
    assert int(PB.count_excluded_pairs(p, s, "either", c)) == 0


def test_A28_low_mass_ratio_pair_still_counted():
    """spec.md section 1: Part 1 imposes no mass-ratio restriction -- stored
    pair rows are used exactly as given. Every other pinned fixture in this
    file happens to sit above the default mass_ratio_min=0.1, so a submission
    that silently reapplied that cut would still pass every one of them."""
    p = np.array([10.0])
    s = np.array([8.0])
    ratio = 10.0 ** (float(s[0]) - float(p[0]))
    assert ratio < BASE["mass_ratio_min"], ratio  # 0.01 << 0.1, well below the cut

    # edges [8,8.5,9,9.5,10,10.5,11]: mass 10.0 -> bin index 4, mass 8.0 -> bin index 0
    expect = {
        "primary":   [0, 0, 0, 0, 1, 0],
        "secondary": [1, 0, 0, 0, 0, 0],
        "either":    [1, 0, 0, 0, 1, 0],
    }
    for convention, exp in expect.items():
        got = np.asarray(PB.count_pairs_per_mass_bin(p, s, convention, BASE))
        assert list(got) == exp, convention
        assert int(PB.count_excluded_pairs(p, s, convention, BASE)) == 0, convention


def test_A29_pair_binning_at_and_below_lower_mass_edge():
    """The lower-edge analogue of test_A04/A11: bins are right-open, so a
    mass exactly at log_mass_min sits in the lowest bin (unlike the excluded
    upper edge), while a mass strictly below log_mass_min is excluded from
    every bin, on both sides of a pair."""
    p = np.array([8.0, 8.0, 7.99])
    s = np.array([8.0, 7.99, 7.99])
    expect = {
        "primary":   [2, 0, 0, 0, 0, 0],
        "secondary": [1, 0, 0, 0, 0, 0],
        "either":    [3, 0, 0, 0, 0, 0],
    }
    excluded = {"primary": 1, "secondary": 2, "either": 1}
    counts = {}
    for convention in ("primary", "secondary", "either"):
        got = np.asarray(PB.count_pairs_per_mass_bin(p, s, convention, BASE))
        assert list(got) == expect[convention], convention
        assert int(PB.count_excluded_pairs(p, s, convention, BASE)) == excluded[convention], convention
        counts[convention] = got
    assert PB.check_additivity(counts["primary"], counts["secondary"], counts["either"]) is True


def test_A30_check_additivity_exact_above_2_53():
    """spec.md section 6 restricts compute_pair_fraction's domain to counts
    below 2**53, but check_additivity's own Acceptance Criteria state no
    such restriction (only non-negative, integer-valued, finite). A naive
    float64 comparison loses precision above 2**53 and could silently
    misreport this violation as holding."""
    big = np.array([2 ** 53], dtype=np.int64)
    one = np.array([1], dtype=np.int64)
    zero = np.array([0], dtype=np.int64)
    assert PB.check_additivity(big, one, big) is False
    assert PB.check_additivity(big, zero, big) is True
