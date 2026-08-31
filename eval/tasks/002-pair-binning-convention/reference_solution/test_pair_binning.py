"""
Tests for pair_binning.py -- the reference solution's own suite for Task 002.

Kept for harness self-validation only; never shown to a Developer model. This
is what the mutation gate runs, standing in for the suite a submission would
have written itself.

Covers: the three pair-to-bin conventions and their incidence counting, the
convention-independent denominator, the additivity identity, the plug-in
Poisson error, every rejection the spec lists, and the driver's preflight
atomicity, persisted schema, config tracking and console summary.
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

import calc
import pair_binning as pb
from config import config as BASE_CONFIG
from data_reader import load_galaxy_catalog
from generate_test_data import generate_all_snapshots

CONVENTIONS = ("primary", "secondary", "either")

# Six pairs: both members in one bin (0, 2), members straddling bins (1, 4),
# a primary exactly on the excluded upper edge (3), both members on it (5).
PAIR_PRIMARY = np.array([8.2, 9.7, 10.6, 11.0, 10.2, 11.0])
PAIR_SECONDARY = np.array([8.1, 8.9, 10.6, 10.4, 9.5, 11.0])
# A real catalog contains the pair members themselves plus unpaired field
# galaxies; a fixture catalog that omitted the members would give a bin with
# more incidences than galaxies, which compute_pair_fraction rightly rejects.
FIELD = np.array([7.99, 8.0, 8.499, 9.75, 10.5, 10.9999, 11.0])
GALAXIES = np.concatenate([PAIR_PRIMARY, PAIR_SECONDARY, FIELD])
# Standalone masses for the pure-function pinned count vector.
EDGE_MASSES = np.array([7.99, 8.0, 8.499, 8.5, 9.75, 10.5, 10.9999, 11.0])
EXPECT_EDGE_COUNTS = [2, 1, 0, 1, 0, 2]

EXPECT_COUNTS = {
    "primary": [1, 0, 0, 1, 1, 1],
    "secondary": [1, 1, 0, 1, 1, 1],
    "either": [2, 1, 0, 2, 2, 2],
}
EXPECT_EXCLUDED = {"primary": 2, "secondary": 1, "either": 1}
EXPECT_GALAXY_COUNTS = [4, 1, 0, 3, 2, 4]


def cfg(**kw):
    c = copy.deepcopy(BASE_CONFIG)
    c.update(kw)
    return c


def n_mass_bins(c=BASE_CONFIG):
    return int(round((c["log_mass_max"] - c["log_mass_min"]) / c["mass_bin_width"]))


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        result = fn(*a, **k)
    return result, buf.getvalue()


def write_snapshot(c, z, gal_masses, pair_primary, pair_secondary,
                   attr_overrides=None, mass_bin=None, mass_bin_by="primary"):
    """Hand-build one (catalog, pair-results) snapshot pair on disk."""
    os.makedirs(c["data_dir"], exist_ok=True)
    os.makedirs(c["results_dir"], exist_ok=True)

    gal_masses = np.asarray(gal_masses, dtype=float)
    n_gal = len(gal_masses)
    with h5py.File(pb._data_path(z, c), "w") as f:
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
    if mass_bin is None:
        mass_bin = pb._bin_indices(mp, c)
    with h5py.File(pb._results_path(z, c), "w") as f:
        f.create_dataset("mass_primary", data=mp)
        f.create_dataset("mass_secondary", data=ms)
        f.create_dataset("mass_ratio", data=10.0 ** (ms - mp))
        f.create_dataset("separation_kpc", data=np.full(len(mp), 12.0))
        f.create_dataset("delta_v", data=np.full(len(mp), 120.0))
        f.create_dataset("mass_bin", data=np.asarray(mass_bin, dtype=np.int64))
        f.create_dataset("sep_bin", data=np.ones(len(mp), dtype=np.int64))
        f.attrs["redshift"] = float(z)
        f.attrs["n_pairs"] = len(mp)
        f.attrs["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        f.attrs["mass_bin_by"] = mass_bin_by
        f.attrs["mass_ratio_min"] = float(c["mass_ratio_min"])
        f.attrs["max_sep_kpc"] = float(c["max_sep"])
        for key, value in (attr_overrides or {}).items():
            f.attrs[key] = value


def tmp_config(tmp_path, **kw):
    c = cfg(data_dir=str(tmp_path / "data") + os.sep,
            results_dir=str(tmp_path / "results") + os.sep,
            figures_dir=str(tmp_path / "figures") + os.sep)
    c.update(kw)
    os.makedirs(c["data_dir"], exist_ok=True)
    os.makedirs(c["results_dir"], exist_ok=True)
    return c


def write_sentinel(c):
    path = os.path.join(c["results_dir"], "pair_binning.hdf5")
    with open(path, "wb") as f:
        f.write(b"SENTINEL")
    return path, sha256(path)


@pytest.fixture
def fixture_config(tmp_path):
    c = tmp_config(tmp_path, redshifts=[2.0])
    write_snapshot(c, 2.0, GALAXIES, PAIR_PRIMARY, PAIR_SECONDARY)
    return c


@pytest.fixture(scope="module")
def mock_config(tmp_path_factory):
    root = tmp_path_factory.mktemp("pair_binning_e2e")
    c = cfg(data_dir=str(root / "data") + os.sep,
            results_dir=str(root / "results") + os.sep,
            figures_dir=str(root / "figures") + os.sep)
    os.makedirs(c["data_dir"], exist_ok=True)
    os.makedirs(c["results_dir"], exist_ok=True)
    with contextlib.redirect_stdout(io.StringIO()):
        generate_all_snapshots(c)
        calc.run_calculation(c)
    return c


# ------------------------------------------------------ the denominator

def test_galaxy_count_pinned_vector():
    got = np.asarray(pb.count_galaxies_per_mass_bin(EDGE_MASSES, BASE_CONFIG))
    assert list(got) == EXPECT_EDGE_COUNTS
    assert got.dtype.kind in "iu"
    assert got.shape == (n_mass_bins(),)


def test_galaxy_count_excludes_exact_upper_edge():
    """A galaxy at exactly log_mass_max is selected by data_reader but binned nowhere."""
    counts = np.asarray(pb.count_galaxies_per_mass_bin(np.array([10.9, 11.0]), BASE_CONFIG))
    assert int(np.sum(counts)) == 1
    assert counts[-1] == 1


def test_galaxy_count_is_convention_independent():
    reference = list(np.asarray(pb.count_galaxies_per_mass_bin(EDGE_MASSES, BASE_CONFIG)))
    stripped = cfg()
    stripped.pop("mass_bin_by")
    assert list(np.asarray(pb.count_galaxies_per_mass_bin(EDGE_MASSES, stripped))) == reference
    for value in ("primary", "secondary", "either", "mean", "total", "nonsense"):
        c = cfg(mass_bin_by=value)
        assert list(np.asarray(pb.count_galaxies_per_mass_bin(EDGE_MASSES, c))) == reference, value


def test_config_gains_one_key_and_keeps_the_frozen_one():
    assert list(BASE_CONFIG["pair_binning_conventions"]) == ["primary", "secondary", "either"]
    assert BASE_CONFIG["mass_bin_by"] == "primary"


def test_binning_follows_config_not_the_defaults():
    """Guards against a hardcoded [8.0, 11.0, 0.5) grid, which every
    default-config test in this file would otherwise accept."""
    c = cfg(log_mass_min=9.0, log_mass_max=12.0, mass_bin_width=1.5)  # 2 bins
    np.testing.assert_allclose(np.asarray(pb._mass_bin_edges(c)),
                               [9.0, 10.5, 12.0], rtol=0, atol=0)

    gal = np.asarray(pb.count_galaxies_per_mass_bin(
        np.array([8.9, 9.0, 10.4, 10.5, 11.9, 12.0]), c))
    assert list(gal) == [2, 2]

    p, s = np.array([10.6, 11.0]), np.array([9.5, 10.0])
    assert list(np.asarray(pb.count_pairs_per_mass_bin(p, s, "primary", c))) == [0, 2]
    assert list(np.asarray(pb.count_pairs_per_mass_bin(p, s, "secondary", c))) == [2, 0]
    assert list(np.asarray(pb.count_pairs_per_mass_bin(p, s, "either", c))) == [2, 2]
    assert int(pb.count_excluded_pairs(p, s, "either", c)) == 0


def test_galaxy_count_zero_length():
    got = np.asarray(pb.count_galaxies_per_mass_bin(np.array([], dtype=float), BASE_CONFIG))
    assert list(got) == [0] * n_mass_bins()
    assert got.dtype.kind in "iu"


@pytest.mark.parametrize("bad", [
    np.array([[8.0, 9.0]]),
    np.array([np.nan]),
    np.array([np.inf]),
    np.array([8.0 + 1j]),
    np.array(["8.0"]),
])
def test_galaxy_count_rejections(bad):
    with pytest.raises(AssertionError):
        pb.count_galaxies_per_mass_bin(bad, BASE_CONFIG)


# -------------------------------------------------------- the numerator

@pytest.mark.parametrize("convention", CONVENTIONS)
def test_pair_counts_pinned_vector(convention):
    got = np.asarray(pb.count_pairs_per_mass_bin(
        PAIR_PRIMARY, PAIR_SECONDARY, convention, BASE_CONFIG))
    assert list(got) == EXPECT_COUNTS[convention]
    assert got.dtype.kind in "iu"
    assert got.shape == (n_mass_bins(),)


def test_conventions_give_different_answers():
    got = {c: list(np.asarray(pb.count_pairs_per_mass_bin(
        PAIR_PRIMARY, PAIR_SECONDARY, c, BASE_CONFIG))) for c in CONVENTIONS}
    assert got["primary"] != got["secondary"]
    assert got["either"] != got["primary"]
    assert got["either"] != got["secondary"]


def test_both_members_in_one_bin_give_two_incidences():
    p, s = np.array([10.6]), np.array([10.6])
    assert list(np.asarray(pb.count_pairs_per_mass_bin(p, s, "either", BASE_CONFIG))) \
        == [0, 0, 0, 0, 0, 2]
    assert list(np.asarray(pb.count_pairs_per_mass_bin(p, s, "primary", BASE_CONFIG))) \
        == [0, 0, 0, 0, 0, 1]
    assert list(np.asarray(pb.count_pairs_per_mass_bin(p, s, "secondary", BASE_CONFIG))) \
        == [0, 0, 0, 0, 0, 1]


def test_members_in_different_bins_split():
    p, s = np.array([9.7]), np.array([8.9])
    assert list(np.asarray(pb.count_pairs_per_mass_bin(p, s, "either", BASE_CONFIG))) \
        == [0, 1, 0, 1, 0, 0]


@pytest.mark.parametrize("convention", CONVENTIONS)
def test_excluded_pair_counts_pinned(convention):
    got = pb.count_excluded_pairs(PAIR_PRIMARY, PAIR_SECONDARY, convention, BASE_CONFIG)
    assert int(got) == EXPECT_EXCLUDED[convention]


def test_exclusion_sum_rule():
    for convention in ("primary", "secondary"):
        counted = int(np.sum(np.asarray(pb.count_pairs_per_mass_bin(
            PAIR_PRIMARY, PAIR_SECONDARY, convention, BASE_CONFIG))))
        excluded = int(pb.count_excluded_pairs(
            PAIR_PRIMARY, PAIR_SECONDARY, convention, BASE_CONFIG))
        assert counted + excluded == len(PAIR_PRIMARY), convention


def test_additivity_identity_on_fixture():
    counts = {c: np.asarray(pb.count_pairs_per_mass_bin(
        PAIR_PRIMARY, PAIR_SECONDARY, c, BASE_CONFIG)) for c in CONVENTIONS}
    np.testing.assert_array_equal(counts["primary"] + counts["secondary"], counts["either"])
    assert pb.check_additivity(counts["primary"], counts["secondary"], counts["either"]) is True


@pytest.mark.parametrize("convention", CONVENTIONS)
def test_zero_length_pair_sample(convention):
    empty = np.array([], dtype=float)
    got = np.asarray(pb.count_pairs_per_mass_bin(empty, empty, convention, BASE_CONFIG))
    assert list(got) == [0] * n_mass_bins()
    assert got.dtype.kind in "iu"
    assert int(pb.count_excluded_pairs(empty, empty, convention, BASE_CONFIG)) == 0


@pytest.mark.parametrize("fn", [pb.count_pairs_per_mass_bin, pb.count_excluded_pairs])
@pytest.mark.parametrize("bad", ["mean", "total", "Primary", "", "nonsense", None, 3, ["primary"]])
def test_unsupported_convention_rejected(fn, bad):
    with pytest.raises(AssertionError):
        fn(PAIR_PRIMARY, PAIR_SECONDARY, bad, BASE_CONFIG)


@pytest.mark.parametrize("fn", [pb.count_pairs_per_mass_bin, pb.count_excluded_pairs])
@pytest.mark.parametrize("primary,secondary", [
    (np.array([9.0, 9.0]), np.array([8.0])),          # shape mismatch
    (np.array([[9.0]]), np.array([[8.0]])),           # non-1D
    (np.array([np.nan]), np.array([8.0])),            # non-finite primary
    (np.array([9.0]), np.array([np.inf])),            # non-finite secondary
    (np.array([9.0 + 1j]), np.array([8.0 + 0j])),     # complex
    (np.array(["9.0"]), np.array(["8.0"])),           # non-numeric
    (np.array([8.0]), np.array([9.0])),               # ordering invariant violated
])
def test_pair_array_rejections(fn, primary, secondary):
    with pytest.raises(AssertionError):
        fn(primary, secondary, "primary", BASE_CONFIG)


def test_equal_masses_are_valid():
    p, s = np.array([9.25]), np.array([9.25])
    assert list(np.asarray(pb.count_pairs_per_mass_bin(p, s, "either", BASE_CONFIG))) \
        == [0, 0, 2, 0, 0, 0]
    assert int(pb.count_excluded_pairs(p, s, "either", BASE_CONFIG)) == 0


# ------------------------------------------------------- pair fraction

def test_pair_fraction_pinned():
    f, s = pb.compute_pair_fraction(np.array([0, 4, 9]), np.array([4, 16, 4]))
    f, s = np.asarray(f), np.asarray(s)
    assert f[0] == 0.0 and s[0] == 0.0
    np.testing.assert_allclose(f[1:], [0.25, 2.25], rtol=1e-14, atol=0)
    np.testing.assert_allclose(s[1:], [0.125, 0.75], rtol=1e-14, atol=0)


def test_pair_fraction_accepts_integer_valued_floats():
    f, s = pb.compute_pair_fraction(np.array([0.0, 4.0, 9.0]), np.array([4.0, 16.0, 4.0]))
    np.testing.assert_allclose(np.asarray(f)[1:], [0.25, 2.25], rtol=1e-14, atol=0)
    np.testing.assert_allclose(np.asarray(s)[1:], [0.125, 0.75], rtol=1e-14, atol=0)


def test_pair_fraction_zero_zero_is_exactly_zero():
    f, s = pb.compute_pair_fraction(np.array([0, 0]), np.array([0, 10]))
    f, s = np.asarray(f), np.asarray(s)
    assert f[0] == 0.0 and s[0] == 0.0
    assert np.all(np.isfinite(f)) and np.all(np.isfinite(s))


def test_pair_fraction_may_exceed_one():
    f, _ = pb.compute_pair_fraction(np.array([9]), np.array([4]))
    assert float(np.asarray(f)[0]) == 2.25


@pytest.mark.parametrize("npair,ngal", [
    (np.array([1]), np.array([0])),          # incidence without galaxies
    (np.array([1, 2]), np.array([1])),       # shape mismatch
    (np.array([[1, 2]]), np.array([[3, 4]])),  # non-1D
    (np.array([-1]), np.array([10])),        # negative
    (np.array([1]), np.array([-10])),
    (np.array([np.nan]), np.array([10.0])),  # non-finite
    (np.array([np.inf]), np.array([10.0])),
    (np.array([1.0]), np.array([np.nan])),
    (np.array([1.5]), np.array([10.0])),     # non-integer-valued
    (np.array([1.0]), np.array([10.5])),
    (np.array([1 + 0j]), np.array([10 + 0j])),  # complex
    (np.array(["1"]), np.array(["10"])),        # non-numeric
])
def test_pair_fraction_rejections(npair, ngal):
    with pytest.raises(AssertionError):
        pb.compute_pair_fraction(npair, ngal)


def test_pair_fraction_documents_the_error_convention():
    doc = re.sub(r"\s+", " ", pb.compute_pair_fraction.__doc__ or "")
    assert ("Under the 'either' convention the numerator counts galaxy-pair incidences "
            "rather than independent pairs, so this plug-in Poisson error is an "
            "approximation and not a confidence interval.") in doc


# --------------------------------------------------------- additivity

def test_check_additivity_returns_bool_not_exception():
    assert pb.check_additivity([1, 2], [3, 4], [4, 6]) is True
    assert pb.check_additivity([0, 0], [0, 0], [0, 0]) is True
    assert pb.check_additivity([1, 2], [3, 4], [4, 7]) is False
    # the classic wrong 'either': a both-members-in-bin pair counted once
    assert pb.check_additivity([1, 0], [1, 0], [1, 0]) is False


@pytest.mark.parametrize("args", [
    ([[1]], [[1]], [[2]]),
    ([1, 2], [1], [2, 3]),
    ([1.5], [1], [2.5]),
    ([-1], [1], [0]),
    ([np.nan], [1.0], [1.0]),
    ([np.inf], [1.0], [1.0]),
    (["1"], ["1"], ["2"]),
    ([1 + 0j], [1 + 0j], [2 + 0j]),
])
def test_check_additivity_rejections(args):
    with pytest.raises(AssertionError):
        pb.check_additivity(*args)


# ------------------------------------------------------------ loading

def test_load_snapshot_counts_contract(fixture_config):
    got = pb.load_snapshot_counts(2.0, fixture_config)
    assert set(got.keys()) == {
        "redshift", "n_galaxies", "n_pairs", "n_excluded_pairs", "n_pairs_total"}
    assert got["redshift"] == 2.0
    assert list(np.asarray(got["n_galaxies"])) == EXPECT_GALAXY_COUNTS
    assert np.asarray(got["n_galaxies"]).dtype.kind in "iu"
    assert got["n_pairs_total"] == 6
    for convention in CONVENTIONS:
        assert list(np.asarray(got["n_pairs"][convention])) == EXPECT_COUNTS[convention]
        assert np.asarray(got["n_pairs"][convention]).dtype.kind in "iu"
        assert int(got["n_excluded_pairs"][convention]) == EXPECT_EXCLUDED[convention]


def test_stored_mass_bin_and_mass_bin_by_are_ignored(tmp_path):
    c = tmp_config(tmp_path, redshifts=[2.0])
    garbage = np.full(len(PAIR_PRIMARY), 2, dtype=np.int64)
    write_snapshot(c, 2.0, GALAXIES, PAIR_PRIMARY, PAIR_SECONDARY,
                   mass_bin=garbage, mass_bin_by="total")
    got = pb.load_snapshot_counts(2.0, c)
    for convention in CONVENTIONS:
        assert list(np.asarray(got["n_pairs"][convention])) == EXPECT_COUNTS[convention]
        assert int(got["n_excluded_pairs"][convention]) == EXPECT_EXCLUDED[convention]


def test_load_snapshot_counts_honours_convention_list(fixture_config):
    fixture_config["pair_binning_conventions"] = ["either"]
    got = pb.load_snapshot_counts(2.0, fixture_config)
    assert list(got["n_pairs"].keys()) == ["either"]
    assert list(got["n_excluded_pairs"].keys()) == ["either"]

    fixture_config["pair_binning_conventions"] = ["secondary", "primary"]
    got = pb.load_snapshot_counts(2.0, fixture_config)
    assert list(got["n_pairs"].keys()) == ["secondary", "primary"]


@pytest.mark.parametrize("bad", [
    [], ["primary", "primary"], ["mean"], ["total"], ["nonsense"],
    [None], [3], "primary", ("primary", "primary"),
])
def test_invalid_convention_list_rejected(fixture_config, bad):
    fixture_config["pair_binning_conventions"] = bad
    with pytest.raises(AssertionError):
        pb.load_snapshot_counts(2.0, fixture_config)


def test_load_snapshot_counts_missing_files(tmp_path):
    c = tmp_config(tmp_path, redshifts=[2.0])
    write_snapshot(c, 2.0, GALAXIES, PAIR_PRIMARY, PAIR_SECONDARY)

    os.remove(pb._data_path(2.0, c))
    with pytest.raises(AssertionError):
        pb.load_snapshot_counts(2.0, c)

    write_snapshot(c, 2.0, GALAXIES, PAIR_PRIMARY, PAIR_SECONDARY)
    os.remove(pb._results_path(2.0, c))
    with pytest.raises(AssertionError):
        pb.load_snapshot_counts(2.0, c)


@pytest.mark.parametrize("override", [
    {"redshift": 9.0},
    {"redshift": "2.0"},
    {"redshift": np.array([2.0, 2.0])},
    {"mass_ratio_min": 0.25},
    {"mass_ratio_min": "0.1"},
    {"max_sep_kpc": 50.0},
    {"max_sep_kpc": b"25.0"},
])
def test_load_snapshot_counts_provenance_rejections(tmp_path, override):
    c = tmp_config(tmp_path, redshifts=[2.0])
    write_snapshot(c, 2.0, GALAXIES, PAIR_PRIMARY, PAIR_SECONDARY, attr_overrides=override)
    with pytest.raises(AssertionError):
        pb.load_snapshot_counts(2.0, c)


def test_provenance_compared_against_config_not_defaults(tmp_path):
    """A check hardcoding 0.1 / 25.0 passes only under the default config."""
    c = tmp_config(tmp_path / "nondefault", redshifts=[2.0],
                   mass_ratio_min=0.25, max_sep=15.0)
    write_snapshot(c, 2.0, GALAXIES, PAIR_PRIMARY, PAIR_SECONDARY)
    got = pb.load_snapshot_counts(2.0, c)
    for convention in CONVENTIONS:
        assert list(np.asarray(got["n_pairs"][convention])) == EXPECT_COUNTS[convention]

    c2 = tmp_config(tmp_path / "defaultattrs", redshifts=[2.0],
                    mass_ratio_min=0.25, max_sep=15.0)
    write_snapshot(c2, 2.0, GALAXIES, PAIR_PRIMARY, PAIR_SECONDARY,
                   attr_overrides={"mass_ratio_min": 0.1, "max_sep_kpc": 25.0})
    with pytest.raises(AssertionError):
        pb.load_snapshot_counts(2.0, c2)


@pytest.mark.parametrize("attr", ["redshift", "mass_ratio_min", "max_sep_kpc"])
def test_load_snapshot_counts_missing_attr(tmp_path, attr):
    c = tmp_config(tmp_path, redshifts=[2.0])
    write_snapshot(c, 2.0, GALAXIES, PAIR_PRIMARY, PAIR_SECONDARY)
    with h5py.File(pb._results_path(2.0, c), "r+") as f:
        del f.attrs[attr]
    with pytest.raises(AssertionError):
        pb.load_snapshot_counts(2.0, c)


@pytest.mark.parametrize("dataset", ["mass_primary", "mass_secondary"])
def test_load_snapshot_counts_missing_dataset(tmp_path, dataset):
    c = tmp_config(tmp_path, redshifts=[2.0])
    write_snapshot(c, 2.0, GALAXIES, PAIR_PRIMARY, PAIR_SECONDARY)
    with h5py.File(pb._results_path(2.0, c), "r+") as f:
        del f[dataset]
    with pytest.raises(AssertionError):
        pb.load_snapshot_counts(2.0, c)


def test_load_snapshot_counts_length_mismatch(tmp_path):
    c = tmp_config(tmp_path, redshifts=[2.0])
    write_snapshot(c, 2.0, GALAXIES, PAIR_PRIMARY, PAIR_SECONDARY)
    with h5py.File(pb._results_path(2.0, c), "r+") as f:
        del f["mass_secondary"]
        f.create_dataset("mass_secondary", data=PAIR_SECONDARY[:3])
    with pytest.raises(AssertionError):
        pb.load_snapshot_counts(2.0, c)


# ------------------------------------------------------------- driver

def test_run_binning_comparison_schema_and_values(fixture_config):
    results, out = quiet(pb.run_binning_comparison, fixture_config)
    assert len(results) == 1
    r = results[0]
    assert set(r.keys()) == {"redshift", "n_galaxies", "n_pairs", "pair_fraction",
                             "pair_fraction_err", "n_excluded_pairs", "additivity_holds"}
    assert r["additivity_holds"] is True

    nb = n_mass_bins()
    path = os.path.join(fixture_config["results_dir"], "pair_binning.hdf5")
    with h5py.File(path, "r") as f:
        assert f["n_galaxies"].shape == (1, nb)
        assert f["n_pairs"].shape == (1, 3, nb)
        assert f["pair_fraction"].shape == (1, 3, nb)
        assert f["pair_fraction_err"].shape == (1, 3, nb)
        assert f["n_excluded_pairs"].shape == (1, 3)
        assert f["n_galaxies"].dtype.kind in "iu"
        assert f["n_pairs"].dtype.kind in "iu"
        assert f["n_excluded_pairs"].dtype.kind in "iu"
        assert f["pair_fraction"].dtype.kind == "f"
        assert f["pair_fraction_err"].dtype.kind == "f"
        stored_conventions = [c.decode() if isinstance(c, bytes) else str(c)
                              for c in np.atleast_1d(f.attrs["conventions"])]
        assert stored_conventions == list(CONVENTIONS)
        np.testing.assert_array_equal(f["n_galaxies"][0], EXPECT_GALAXY_COUNTS)
        for ic, convention in enumerate(CONVENTIONS):
            np.testing.assert_array_equal(f["n_pairs"][0, ic], EXPECT_COUNTS[convention])
            assert int(f["n_excluded_pairs"][0, ic]) == EXPECT_EXCLUDED[convention]
        assert float(f.attrs["mass_ratio_min"]) == float(fixture_config["mass_ratio_min"])
        assert float(f.attrs["max_sep_kpc"]) == float(fixture_config["max_sep"])
        np.testing.assert_allclose(np.asarray(f.attrs["mass_bin_edges"], dtype=float),
                                   np.linspace(8.0, 11.0, nb + 1), rtol=0, atol=0)
        np.testing.assert_allclose(np.asarray(f.attrs["redshifts"], dtype=float), [2.0],
                                   rtol=0, atol=0)
        assert bool(f.attrs["additivity_checked"]) is True
        assert bool(f.attrs["additivity_holds"]) is True
        parsed = datetime.datetime.fromisoformat(str(f.attrs["timestamp"]))
        assert parsed.tzinfo is not None
    assert out.strip()


def test_returned_dicts_match_persisted(fixture_config):
    results, _ = quiet(pb.run_binning_comparison, fixture_config)
    path = os.path.join(fixture_config["results_dir"], "pair_binning.hdf5")
    with h5py.File(path, "r") as f:
        ngal, npair = f["n_galaxies"][...], f["n_pairs"][...]
        frac, ferr = f["pair_fraction"][...], f["pair_fraction_err"][...]
        excl = f["n_excluded_pairs"][...]
    r = results[0]
    np.testing.assert_array_equal(np.asarray(r["n_galaxies"]), ngal[0])
    for ic, convention in enumerate(CONVENTIONS):
        np.testing.assert_array_equal(np.asarray(r["n_pairs"][convention]), npair[0, ic])
        np.testing.assert_allclose(np.asarray(r["pair_fraction"][convention]), frac[0, ic],
                                   rtol=0, atol=0)
        np.testing.assert_allclose(np.asarray(r["pair_fraction_err"][convention]), ferr[0, ic],
                                   rtol=0, atol=0)
        assert int(r["n_excluded_pairs"][convention]) == int(excl[0, ic])


def test_one_denominator_shared_by_every_convention(fixture_config):
    results, _ = quiet(pb.run_binning_comparison, fixture_config)
    r = results[0]
    ngal = np.asarray(r["n_galaxies"], dtype=float)
    for convention in CONVENTIONS:
        npair = np.asarray(r["n_pairs"][convention], dtype=float)
        expected = np.where(ngal > 0, npair / np.where(ngal > 0, ngal, 1.0), 0.0)
        got = np.asarray(r["pair_fraction"][convention])
        zero = expected == 0
        assert np.all(got[zero] == 0.0)
        np.testing.assert_allclose(got[~zero], expected[~zero], rtol=1e-14, atol=0)


def test_conventions_config_tracks_through_the_driver(tmp_path):
    c = tmp_config(tmp_path, redshifts=[2.0],
                   pair_binning_conventions=["secondary", "primary"])
    write_snapshot(c, 2.0, GALAXIES, PAIR_PRIMARY, PAIR_SECONDARY)
    results, out = quiet(pb.run_binning_comparison, c)

    assert results[0]["additivity_holds"] is None
    assert set(results[0]["n_pairs"].keys()) == {"secondary", "primary"}
    with h5py.File(os.path.join(c["results_dir"], "pair_binning.hdf5"), "r") as f:
        stored = [x.decode() if isinstance(x, bytes) else str(x)
                  for x in np.atleast_1d(f.attrs["conventions"])]
        assert stored == ["secondary", "primary"]
        assert f["n_pairs"].shape[1] == 2
        assert f["n_excluded_pairs"].shape[1] == 2
        assert bool(f.attrs["additivity_checked"]) is False
        assert "additivity_holds" not in f.attrs
        np.testing.assert_array_equal(f["n_pairs"][0, 0], EXPECT_COUNTS["secondary"])
        np.testing.assert_array_equal(f["n_pairs"][0, 1], EXPECT_COUNTS["primary"])
    assert re.search(r"\badditivity=not_checked\b", out)


def test_console_summary_fields(fixture_config):
    results, out = quiet(pb.run_binning_comparison, fixture_config)
    assert ("N_gal(b) is the same galaxy count for every convention; only the "
            "numerator changes.") in re.sub(r"\s+", " ", out)
    lines = out.splitlines()
    r = results[0]
    for convention in CONVENTIONS:
        matches = [ln for ln in lines if "z=2.0" in ln and f"convention={convention}" in ln]
        assert len(matches) == 1, (convention, matches)
        line = matches[0]
        for token, expected in (
                ("n_galaxies", int(np.sum(np.asarray(r["n_galaxies"])))),
                ("n_pairs", int(np.sum(np.asarray(r["n_pairs"][convention])))),
                ("n_excluded", int(r["n_excluded_pairs"][convention]))):
            m = re.search(rf"\b{token}=(-?\d+)\b", line)
            assert m, (token, line)
            assert int(m.group(1)) == expected, (token, line)
    additivity = [ln for ln in lines if "z=2.0" in ln and "additivity=" in ln]
    assert len(additivity) == 1
    assert re.search(r"\badditivity=holds\b", additivity[0])


@pytest.mark.parametrize("name,remove,override", [
    ("missing_data", "data", None),
    ("missing_results", "results", None),
    ("bad_redshift", None, {"redshift": 9.0}),
    ("bad_mass_ratio_min", None, {"mass_ratio_min": 0.25}),
    ("bad_max_sep", None, {"max_sep_kpc": 50.0}),
    ("malformed_redshift", None, {"redshift": "2.0"}),
])
def test_preflight_leaves_output_untouched(tmp_path, name, remove, override):
    c = tmp_config(tmp_path / name, redshifts=[2.0])
    write_snapshot(c, 2.0, GALAXIES, PAIR_PRIMARY, PAIR_SECONDARY, attr_overrides=override)
    path, digest = write_sentinel(c)
    if remove == "data":
        os.remove(pb._data_path(2.0, c))
    elif remove == "results":
        os.remove(pb._results_path(2.0, c))
    with pytest.raises(AssertionError):
        pb.run_binning_comparison(c)
    assert sha256(path) == digest


@pytest.mark.parametrize("bad", [[], ["primary", "primary"], ["mean"], ["nonsense"], [7], "primary"])
def test_invalid_conventions_leave_output_untouched(tmp_path, bad):
    c = tmp_config(tmp_path, redshifts=[2.0])
    write_snapshot(c, 2.0, GALAXIES, PAIR_PRIMARY, PAIR_SECONDARY)
    path, digest = write_sentinel(c)
    c["pair_binning_conventions"] = bad
    with pytest.raises(AssertionError):
        pb.run_binning_comparison(c)
    assert sha256(path) == digest


# ---------------------------------------------------------- end to end

def test_end_to_end_on_generated_mock(mock_config):
    results, out = quiet(pb.run_binning_comparison, mock_config)
    nb = n_mass_bins(mock_config)
    assert len(results) == len(mock_config["redshifts"])

    for iz, z in enumerate(mock_config["redshifts"]):
        with h5py.File(pb._results_path(z, mock_config), "r") as f:
            mp, ms = f["mass_primary"][...], f["mass_secondary"][...]
        catalog = load_galaxy_catalog(pb._data_path(z, mock_config), mock_config)
        bp = pb._bin_indices(mp, mock_config)
        bs = pb._bin_indices(ms, mock_config)
        expected = {
            "primary": np.array([np.count_nonzero(bp == b) for b in range(nb)]),
            "secondary": np.array([np.count_nonzero(bs == b) for b in range(nb)]),
        }
        expected["either"] = expected["primary"] + expected["secondary"]
        expected_gal = np.array([
            np.count_nonzero(pb._bin_indices(catalog["log_stellar_mass"], mock_config) == b)
            for b in range(nb)])

        r = results[iz]
        np.testing.assert_array_equal(np.asarray(r["n_galaxies"]), expected_gal)
        assert r["additivity_holds"] is True
        for convention in CONVENTIONS:
            np.testing.assert_array_equal(
                np.asarray(r["n_pairs"][convention]), expected[convention],
                err_msg=f"z={z} convention={convention}")
        assert int(r["n_excluded_pairs"]["primary"]) == int(np.count_nonzero(bp == -1))
        assert int(r["n_excluded_pairs"]["secondary"]) == int(np.count_nonzero(bs == -1))
        assert int(r["n_excluded_pairs"]["either"]) == \
            int(np.count_nonzero((bp == -1) & (bs == -1)))
        assert re.search(rf"z={z:.1f}.*additivity=holds", out)


def test_end_to_end_denominator_is_the_selected_catalog(mock_config):
    for z in mock_config["redshifts"]:
        got = pb.load_snapshot_counts(z, mock_config)
        catalog = load_galaxy_catalog(pb._data_path(z, mock_config), mock_config)
        masses = np.asarray(catalog["log_stellar_mass"], dtype=float)
        in_bins = int(np.count_nonzero(
            (masses >= mock_config["log_mass_min"]) & (masses < mock_config["log_mass_max"])))
        assert int(np.sum(np.asarray(got["n_galaxies"]))) == in_bins
        assert in_bins > got["n_pairs_total"]


def test_end_to_end_invariants(mock_config):
    for z in mock_config["redshifts"]:
        got = pb.load_snapshot_counts(z, mock_config)
        counts = {c: np.asarray(got["n_pairs"][c]) for c in CONVENTIONS}
        assert pb.check_additivity(counts["primary"], counts["secondary"],
                                   counts["either"]) is True
        for convention in ("primary", "secondary"):
            assert int(np.sum(counts[convention])) + int(got["n_excluded_pairs"][convention]) \
                == got["n_pairs_total"], (z, convention)
