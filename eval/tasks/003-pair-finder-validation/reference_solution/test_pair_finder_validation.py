"""
Input-validation tests for pair_finder.find_pairs().

Two halves, and both matter:

  * the rejection half -- every malformed catalog / config listed in the task
    contract must raise AssertionError with a message naming the offending key
    and the reason, never a TypeError/ValueError/KeyError/ZeroDivisionError
    leaking out of numpy or scipy;
  * the preservation half -- everything find_pairs did before must still be
    true: the pinned separations and velocities, both early-return paths, the
    `-1` out-of-range sentinels, the accepted non-default configurations, and
    the pre-existing ValueError for an unknown `mass_bin_by`.

A suite that only covered the first half would pass while the computation
rotted underneath it.

Tests are independent of random seeds, file I/O and external data.
"""

import copy
import os
import re
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from pair_finder import find_pairs

# Config with a deliberately non-default mass grid and separation grid, so the
# suite would notice an implementation that validated against config.py's
# literals instead of the config it was handed.
BASE_CONFIG = dict(
    box_size       = 1.0,          # Mpc (= 1000 kpc); not read by find_pairs
    log_mass_min   = 8.0,
    log_mass_max   = 11.0,
    mass_bin_width = 1.0,          # 3 bins: [8,9), [9,10), [10,11)
    sep_bins       = [0, 10, 15, 20, 25],   # kpc, 4 bins
    mass_ratio_min = 0.1,
    mass_bin_by    = "primary",
    max_sep        = 100.0,        # kpc, wide enough that sep_bin == -1 is reachable
)

ARRAY_FIELDS = ("x", "y", "z", "vx", "vy", "vz", "log_stellar_mass")
CONFIG_KEYS = ("max_sep", "mass_ratio_min", "sep_bins", "log_mass_min",
               "log_mass_max", "mass_bin_width", "mass_bin_by")

# The scalar forms the contract rejects before any coercion.
BAD_SCALAR_FORMS = ("25.0", b"25.0", 25.0 + 0.0j, True,
                    np.array(25.0), np.array([25.0]))


def cfg(**kw):
    c = copy.deepcopy(BASE_CONFIG)
    c.update(kw)
    return c


def make_catalog(positions_mpc, velocities_kms, log_masses, box_size_mpc=1.0):
    pos = np.array(positions_mpc, dtype=float).reshape(-1, 3)
    vel = np.array(velocities_kms, dtype=float).reshape(-1, 3)
    return dict(
        x=pos[:, 0].copy(), y=pos[:, 1].copy(), z=pos[:, 2].copy(),
        vx=vel[:, 0].copy(), vy=vel[:, 1].copy(), vz=vel[:, 2].copy(),
        log_stellar_mass=np.array(log_masses, dtype=float),
        box_size=float(box_size_mpc),
    )


def catalog():
    """Two galaxies 10 kpc apart; |dv| == 5 km/s; mass ratio 10**-0.5."""
    return make_catalog(
        positions_mpc=[[0.0, 0.0, 0.0], [0.010, 0.0, 0.0]],
        velocities_kms=[[3.0, 4.0, 0.0], [0.0, 0.0, 0.0]],
        log_masses=[10.0, 9.5],
    )


INT_DTYPES = (np.int16, np.uint16, np.int32, np.uint32, np.int64)

# |dv| = 500 (a 3-4-5 triple scaled by 100), an ordinary peculiar velocity for
# this pipeline. Under a 16-bit dtype the squared sum overflows -- 300**2 wraps
# to 24464 and 400**2 to 28928 -- so the recovered speed is 231.07, not 500.
# The plain subtraction wrap is NOT the fault: modular squaring cancels it
# exactly, `(2**32 - 3)**2 mod 2**32 == 9`. What survives to the output is the
# WIDTH of the dtype, which is why 16-bit is in the list.
DV_COMPONENTS = (300, 400, 0)
DV_MAGNITUDE = 500.0


def int_catalog(dtype, descending_velocity=False):
    """All seven fields in one integer dtype. Positions are whole Mpc, so the
    single separation is 1000 kpc -- pair this with a wide max_sep.

    `descending_velocity` puts the faster galaxy at the higher index, so
    `vel[i] - vel[j]` goes negative for the `i < j` pair the tree returns.
    """
    fast, slow = ((0, 0, 0), DV_COMPONENTS) if descending_velocity \
        else (DV_COMPONENTS, (0, 0, 0))
    return dict(
        x=np.array([0, 1], dtype=dtype), y=np.array([0, 0], dtype=dtype),
        z=np.array([0, 0], dtype=dtype),
        vx=np.array([fast[0], slow[0]], dtype=dtype),
        vy=np.array([fast[1], slow[1]], dtype=dtype),
        vz=np.array([fast[2], slow[2]], dtype=dtype),
        log_stellar_mass=np.array([10, 9], dtype=dtype),
        box_size=np.array([3], dtype=dtype)[0],
    )


def rejected(cat, config):
    """Return the AssertionError message, or raise if the rejection is wrong."""
    try:
        find_pairs(cat, config)
    except AssertionError as e:
        return str(e)
    except Exception as e:
        pytest.fail(
            f"expected AssertionError, got {type(e).__name__}: {e} -- a "
            f"low-level exception leaking from numpy/scipy is not a valid "
            f"rejection"
        )
    pytest.fail("malformed input was accepted without any exception")


def assert_names(message, key, token):
    """The message must carry the reason and the offending argument/key.

    `key` may be a tuple when more than one name is acceptable -- the
    unequal-length failure may legitimately report whichever array field the
    implementation noticed first.
    """
    assert token in message, f"message does not name the reason {token!r}: {message}"
    if key is None:
        return
    names = (key,) if isinstance(key, str) else tuple(key)
    assert any(re.search(rf"\b{re.escape(n)}\b", message) for n in names), \
        f"message names none of {list(names)}: {message}"


EMPTY_KEYS = ("mass_primary", "mass_secondary", "mass_ratio",
              "separation_kpc", "delta_v", "mass_bin", "sep_bin")


def assert_empty_result(pairs):
    assert set(pairs) == set(EMPTY_KEYS)
    for key in EMPTY_KEYS:
        arr = np.asarray(pairs[key])
        assert arr.ndim == 1 and arr.size == 0, (key, arr.shape)
    for key in EMPTY_KEYS[:5]:
        assert np.asarray(pairs[key]).dtype.kind == "f", key
    for key in ("mass_bin", "sep_bin"):
        assert np.asarray(pairs[key]).dtype.kind in "iu", key


# ---------------------------------------------------------------------------
# 1. Preserved behaviour: the numbers must not move
# ---------------------------------------------------------------------------

class TestPreservedBehaviour:
    def test_pinned_pair_properties(self):
        pairs = find_pairs(catalog(), cfg())
        assert len(pairs["delta_v"]) == 1
        np.testing.assert_allclose(pairs["separation_kpc"][0], 10.0,
                                   rtol=1e-12, atol=0)
        assert pairs["delta_v"][0] == 5.0          # exact: sqrt(3**2 + 4**2)
        np.testing.assert_allclose(pairs["mass_ratio"][0], 10.0 ** -0.5,
                                   rtol=1e-14, atol=0)
        assert pairs["mass_primary"][0] == 10.0
        assert pairs["mass_secondary"][0] == 9.5
        assert pairs["mass_bin"][0] == 2
        assert pairs["sep_bin"][0] == 1

    def test_periodic_boundary_still_wraps(self):
        cat = make_catalog([[0.001, 0.0, 0.0], [0.999, 0.0, 0.0]],
                           [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], [10.0, 9.5])
        pairs = find_pairs(cat, cfg(max_sep=10.0))
        assert len(pairs["delta_v"]) == 1
        np.testing.assert_allclose(pairs["separation_kpc"][0], 2.0,
                                   rtol=1e-9, atol=0)

    def test_no_pairs_found_returns_empty_structure(self):
        cat = make_catalog([[0.0, 0.0, 0.0]], [[0.0, 0.0, 0.0]], [10.0])
        assert_empty_result(find_pairs(cat, cfg()))

    def test_all_pairs_cut_by_mass_ratio_returns_empty_structure(self):
        cat = make_catalog([[0.0, 0.0, 0.0], [0.010, 0.0, 0.0]],
                           [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], [10.5, 9.3])
        assert_empty_result(find_pairs(cat, cfg()))

    def test_empty_catalog_is_valid(self):
        e = np.array([], dtype=float)
        cat = {k: e.copy() for k in ARRAY_FIELDS}
        cat["box_size"] = 1.0
        assert_empty_result(find_pairs(cat, cfg()))

    def test_mass_bin_minus_one_sentinel_survives(self):
        """A pair above log_mass_max keeps mass_bin == -1, not bin 0."""
        cat = make_catalog([[0.0, 0.0, 0.0], [0.010, 0.0, 0.0]],
                           [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], [12.0, 11.8])
        pairs = find_pairs(cat, cfg())
        assert len(pairs["delta_v"]) == 1
        assert pairs["mass_bin"][0] == -1

    def test_mass_bin_minus_one_below_lower_edge(self):
        cat = make_catalog([[0.0, 0.0, 0.0], [0.010, 0.0, 0.0]],
                           [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], [7.5, 7.0])
        pairs = find_pairs(cat, cfg())
        assert len(pairs["delta_v"]) == 1
        assert pairs["mass_bin"][0] == -1

    def test_sep_bin_minus_one_sentinel_survives(self):
        """A pair beyond the last sep_bins edge keeps sep_bin == -1."""
        cat = make_catalog([[0.0, 0.0, 0.0], [0.030, 0.0, 0.0]],
                           [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], [10.0, 9.5])
        pairs = find_pairs(cat, cfg())
        assert len(pairs["delta_v"]) == 1
        np.testing.assert_allclose(pairs["separation_kpc"][0], 30.0,
                                   rtol=1e-12, atol=0)
        assert pairs["sep_bin"][0] == -1

    def test_unknown_mass_bin_by_still_raises_value_error(self):
        with pytest.raises(ValueError, match="mass_bin_by"):
            find_pairs(catalog(), cfg(mass_bin_by="nonsense"))

    @pytest.mark.parametrize("strategy",
                             ["primary", "secondary", "mean", "total"])
    def test_every_mass_bin_by_strategy_still_works(self, strategy):
        pairs = find_pairs(catalog(), cfg(mass_bin_by=strategy))
        assert len(pairs["delta_v"]) == 1


# ---------------------------------------------------------------------------
# 2. Declared-valid inputs must not be rejected
# ---------------------------------------------------------------------------

class TestNoFalsePositives:
    def test_position_at_zero_and_just_below_box(self):
        box = 1.0
        cat = make_catalog([[0.0, 0.0, 0.0], [np.nextafter(box, 0.0), 0.0, 0.0]],
                           [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], [10.0, 9.5],
                           box_size_mpc=box)
        pairs = find_pairs(cat, cfg(max_sep=10.0))
        assert len(pairs["delta_v"]) == 1

    def test_integer_dtype_arrays_accepted(self):
        cat = catalog()
        cat["vx"] = np.array([3, 0], dtype=np.int64)
        cat["vy"] = np.array([4, 0], dtype=np.int32)
        pairs = find_pairs(cat, cfg())
        assert pairs["delta_v"][0] == 5.0

    def test_numpy_scalar_box_size_accepted(self):
        cat = catalog()
        cat["box_size"] = np.float64(1.0)
        assert len(find_pairs(cat, cfg())["delta_v"]) == 1

    def test_extra_catalog_keys_ignored(self):
        """generate_test_data's is_paired (bool) / pair_id columns ride along."""
        cat = catalog()
        cat["is_paired"] = np.array([True, True])
        cat["pair_id"] = np.array([0, 0])
        cat["redshift"] = 2.0
        assert len(find_pairs(cat, cfg())["delta_v"]) == 1

    @pytest.mark.parametrize("sep_bins", [
        [0, 10, 15, 20, 25],
        [0.0, 10.0, 15.0, 20.0, 25.0],
        (0.0, 10.0, 15.0, 20.0, 25.0),
        (0, 10, 15, 20, 25),
        np.array([0.0, 10.0, 15.0, 20.0, 25.0]),
        np.array([0, 10, 15, 20, 25]),
        [np.int64(0), np.float32(10.0), 15, 20, np.float64(25.0)],
    ], ids=["int_list", "float_list", "float_tuple", "int_tuple",
            "float_ndarray", "int_ndarray", "numpy_scalar_elements"])
    def test_sep_bins_accepted_forms(self, sep_bins):
        assert find_pairs(catalog(), cfg(sep_bins=sep_bins))["sep_bin"][0] == 1

    @pytest.mark.parametrize("value,n_expected",
                             [(0.0, 1), (1.0, 0), (0.1, 1)])
    def test_mass_ratio_min_range_ends_accepted(self, value, n_expected):
        pairs = find_pairs(catalog(), cfg(mass_ratio_min=value))
        assert len(pairs["delta_v"]) == n_expected

    def test_non_default_mass_grid_accepted_and_used(self):
        """[9.0, 12.0) in 1.5 dex -> edges [9.0, 10.5, 12.0]; primary 10.0 -> 0."""
        pairs = find_pairs(catalog(), cfg(log_mass_min=9.0, log_mass_max=12.0,
                                          mass_bin_width=1.5))
        assert pairs["mass_bin"][0] == 0

    def test_out_of_config_range_masses_are_not_rejected(self):
        """The mass range belongs to data_reader's selection, not to find_pairs."""
        cat = make_catalog([[0.0, 0.0, 0.0], [0.010, 0.0, 0.0]],
                           [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], [14.0, 13.8])
        assert len(find_pairs(cat, cfg())["delta_v"]) == 1

    def test_negative_finite_masses_are_not_rejected(self):
        """data_reader asserts masses >= 0; find_pairs must not duplicate it."""
        cat = make_catalog([[0.0, 0.0, 0.0], [0.010, 0.0, 0.0]],
                           [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], [-1.0, -1.5])
        pairs = find_pairs(cat, cfg())
        assert len(pairs["delta_v"]) == 1
        assert pairs["mass_bin"][0] == -1

    # Every scalar key x every accepted scalar family: Python int, Python
    # float, NumPy integer, NumPy floating are all declared valid.
    @pytest.mark.parametrize("key,value", [
        ("max_sep", 100), ("max_sep", 100.0),
        ("max_sep", np.int64(100)), ("max_sep", np.float64(100.0)),
        ("mass_ratio_min", 0), ("mass_ratio_min", 0.1),
        ("mass_ratio_min", np.int64(0)), ("mass_ratio_min", np.float32(0.1)),
        ("log_mass_min", 8), ("log_mass_min", 8.0),
        ("log_mass_min", np.int64(8)), ("log_mass_min", np.float32(8.0)),
        ("log_mass_max", 11), ("log_mass_max", 11.0),
        ("log_mass_max", np.int64(11)), ("log_mass_max", np.float64(11.0)),
        ("mass_bin_width", 1), ("mass_bin_width", 1.0),
        ("mass_bin_width", np.int64(1)), ("mass_bin_width", np.float64(1.0)),
    ])
    def test_numpy_and_python_scalar_config_values_accepted(self, key, value):
        assert len(find_pairs(catalog(), cfg(**{key: value}))["delta_v"]) == 1

    @pytest.mark.parametrize("value", [1, 1.0, np.int64(1), np.float64(1.0)])
    def test_numpy_and_python_scalar_box_size_accepted(self, value):
        cat = catalog()
        cat["box_size"] = value
        assert len(find_pairs(cat, cfg())["delta_v"]) == 1

    @pytest.mark.parametrize("descending", [False, True],
                             ids=["ascending_dv", "descending_dv"])
    @pytest.mark.parametrize("dtype", INT_DTYPES,
                             ids=[d.__name__ for d in INT_DTYPES])
    def test_integer_catalog_matches_its_float_twin(self, dtype, descending):
        """Accepting an integer dtype is not enough -- it must give the same
        answer. Unconverted: signed masses raise on `10 ** negative_int`,
        unsigned masses overflow the ratio to 0 and drop the pair silently,
        and 16-bit velocities overflow the squared sum."""
        int_cat = int_catalog(dtype, descending_velocity=descending)
        float_cat = {k: (np.asarray(v, dtype=float)
                         if isinstance(v, np.ndarray) else float(v))
                     for k, v in int_cat.items()}
        config = cfg(max_sep=2000.0, sep_bins=[0, 1500, 3000])

        got = find_pairs(int_cat, config)
        want = find_pairs(float_cat, config)
        assert len(got["delta_v"]) == len(want["delta_v"]) == 1
        # Anchor the twin, so this cannot pass by both sides being wrong.
        np.testing.assert_allclose(float(want["delta_v"][0]), DV_MAGNITUDE,
                                   rtol=1e-12, atol=0)
        np.testing.assert_allclose(float(want["mass_ratio"][0]), 0.1,
                                   rtol=1e-12, atol=0)
        for key in EMPTY_KEYS:
            np.testing.assert_allclose(
                np.asarray(got[key], dtype=float),
                np.asarray(want[key], dtype=float),
                rtol=1e-12, atol=0,
                err_msg=f"{dtype.__name__} catalog disagrees on {key}")

    # Each velocity component on its own, at each width that overflows at
    # ordinary values. Casting vx and vy but forgetting vz, or casting only
    # the 16-bit widths, are both silent wrong answers:
    #   int16/uint16 at 300 -> 156.41 instead of 300
    #   int8 at 30 -> nan;   uint8 at 30 -> 11.49   (instead of 30)
    @pytest.mark.parametrize("axis", ["vx", "vy", "vz"])
    @pytest.mark.parametrize("dtype,magnitude",
                             [(np.int16, 300), (np.uint16, 300),
                              (np.int8, 30), (np.uint8, 30)],
                             ids=["int16", "uint16", "int8", "uint8"])
    def test_integer_velocity_component_matches_float_twin(
            self, dtype, magnitude, axis):
        # Built from zeros rather than from int_catalog(), whose 300/400
        # components do not fit in an 8-bit dtype.
        int_cat = dict(
            x=np.array([0, 1], dtype=dtype), y=np.zeros(2, dtype=dtype),
            z=np.zeros(2, dtype=dtype), vx=np.zeros(2, dtype=dtype),
            vy=np.zeros(2, dtype=dtype), vz=np.zeros(2, dtype=dtype),
            log_stellar_mass=np.array([10, 9], dtype=dtype),
            box_size=np.array([3], dtype=dtype)[0],
        )
        int_cat[axis] = np.array([magnitude, 0], dtype=dtype)
        float_cat = {k: (np.asarray(v, dtype=float)
                         if isinstance(v, np.ndarray) else float(v))
                     for k, v in int_cat.items()}
        config = cfg(max_sep=2000.0, sep_bins=[0, 1500, 3000])

        got = find_pairs(int_cat, config)
        want = find_pairs(float_cat, config)
        assert len(got["delta_v"]) == len(want["delta_v"]) == 1
        np.testing.assert_allclose(float(want["delta_v"][0]), float(magnitude),
                                   rtol=1e-12, atol=0)
        for key in EMPTY_KEYS:
            np.testing.assert_allclose(
                np.asarray(got[key], dtype=float),
                np.asarray(want[key], dtype=float),
                rtol=1e-12, atol=0,
                err_msg=f"{dtype.__name__} velocity in {axis} disagrees on {key}")


# ---------------------------------------------------------------------------
# 3. Catalog rejections
# ---------------------------------------------------------------------------

class TestArgumentRejections:
    """The top-level form check, which precedes every key lookup."""

    @pytest.mark.parametrize("bad", [[], (), None, "catalog", 5,
                                     np.array([1.0, 2.0])])
    def test_catalog_is_not_a_dict(self, bad):
        assert_names(rejected(bad, cfg()), "catalog", "dict")

    @pytest.mark.parametrize("bad", [[], (), None, "config", 5])
    def test_config_is_not_a_dict(self, bad):
        assert_names(rejected(catalog(), bad), "config", "dict")


class TestCatalogRejections:
    @pytest.mark.parametrize("key", ARRAY_FIELDS + ("box_size",))
    def test_missing_field(self, key):
        cat = catalog()
        del cat[key]
        assert_names(rejected(cat, cfg()), key, "missing")

    @pytest.mark.parametrize("key", ARRAY_FIELDS)
    def test_length_mismatch(self, key):
        cat = catalog()
        cat[key] = cat[key][:1]
        # Any of the seven names is acceptable; naming none of them is not.
        assert_names(rejected(cat, cfg()), ARRAY_FIELDS, "same length")

    @pytest.mark.parametrize("key", ARRAY_FIELDS)
    @pytest.mark.parametrize("bad", [np.nan, np.inf])
    def test_non_finite_values(self, key, bad):
        cat = catalog()
        cat[key] = cat[key].astype(float).copy()
        cat[key][0] = bad
        assert_names(rejected(cat, cfg()), key, "finite")

    @pytest.mark.parametrize("shape", [(2, 1), (1, 2), ()])
    def test_wrong_rank(self, shape):
        cat = catalog()
        cat["x"] = np.zeros(shape)
        assert_names(rejected(cat, cfg()), "x", "1-D")

    @pytest.mark.parametrize("value", [[0.0, 0.010], (0.0, 0.010), 0.0, None])
    def test_not_an_ndarray(self, value):
        cat = catalog()
        cat["x"] = value
        assert_names(rejected(cat, cfg()), "x", "ndarray")

    @pytest.mark.parametrize("value", [
        np.array([0.0 + 0.0j, 0.010 + 0.0j]),
        np.array(["0.0", "0.010"]),
        np.array([True, False]),
        np.array([0.0, None], dtype=object),
    ])
    def test_rejected_dtype(self, value):
        cat = catalog()
        cat["x"] = value
        assert_names(rejected(cat, cfg()), "x", "dtype")

    @pytest.mark.parametrize("bad,token", [
        (0.0, "positive"), (-1.0, "positive"),
        (np.nan, "finite"), (np.inf, "finite"),
    ])
    def test_box_size_value(self, bad, token):
        cat = catalog()
        cat["box_size"] = bad
        assert_names(rejected(cat, cfg()), "box_size", token)

    @pytest.mark.parametrize("bad", ["1.0", b"1.0", 1.0 + 0.0j, True,
                                     np.array(1.0), np.array([1.0])])
    def test_box_size_form(self, bad):
        cat = catalog()
        cat["box_size"] = bad
        assert_names(rejected(cat, cfg()), "box_size", "scalar")

    @pytest.mark.parametrize("key", ["x", "y", "z"])
    @pytest.mark.parametrize("bad", [1.0, 1.5, -1e-9, -1.0])
    def test_position_outside_box(self, key, bad):
        cat = catalog()
        cat[key] = cat[key].copy()
        cat[key][0] = bad
        assert_names(rejected(cat, cfg()), key, "box")


# ---------------------------------------------------------------------------
# 4. Config rejections
# ---------------------------------------------------------------------------

class TestConfigRejections:
    @pytest.mark.parametrize("key", CONFIG_KEYS)
    def test_missing_key(self, key):
        c = cfg()
        del c[key]
        assert_names(rejected(catalog(), c), key, "missing")

    @pytest.mark.parametrize("bad,token", [
        (0.0, "positive"), (-1.0, "positive"),
        (np.nan, "finite"), (np.inf, "finite"),
    ])
    def test_max_sep_value(self, bad, token):
        assert_names(rejected(catalog(), cfg(max_sep=bad)), "max_sep", token)

    @pytest.mark.parametrize("bad,token", [
        (-0.1, "[0, 1]"), (1.1, "[0, 1]"), (2.0, "[0, 1]"),
        (np.nan, "finite"), (np.inf, "finite"),
    ])
    def test_mass_ratio_min_value(self, bad, token):
        assert_names(rejected(catalog(), cfg(mass_ratio_min=bad)),
                     "mass_ratio_min", token)

    @pytest.mark.parametrize("key", ["max_sep", "mass_ratio_min",
                                     "log_mass_min", "log_mass_max",
                                     "mass_bin_width"])
    @pytest.mark.parametrize("bad", BAD_SCALAR_FORMS)
    def test_scalar_form(self, key, bad):
        assert_names(rejected(catalog(), cfg(**{key: bad})), key, "scalar")

    @pytest.mark.parametrize("bad,token", [
        (0.0, "positive"), (-1.0, "positive"),
        (np.nan, "finite"), (np.inf, "finite"),
        (10.0, "at least one mass bin"),
    ])
    def test_mass_bin_width(self, bad, token):
        assert_names(rejected(catalog(), cfg(mass_bin_width=bad)),
                     "mass_bin_width", token)

    @pytest.mark.parametrize("log_mass_max", [8.0, 7.0, -1.0])
    def test_mass_range_ordering(self, log_mass_max):
        assert_names(rejected(catalog(), cfg(log_mass_max=log_mass_max)),
                     "log_mass_max", "greater than")

    @pytest.mark.parametrize("key", ["log_mass_min", "log_mass_max"])
    @pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
    def test_mass_limits_must_be_finite(self, key, bad):
        assert_names(rejected(catalog(), cfg(**{key: bad})), key, "finite")

    @pytest.mark.parametrize("bad,token", [
        ([0], "at least 2"),
        ([], "at least 2"),
        ((5.0,), "at least 2"),
        ([0, 10, 5, 25], "strictly increasing"),
        ([0, 10, 10, 25], "strictly increasing"),
        ([25, 20, 10, 0], "strictly increasing"),
        ([0, float("nan"), 25], "finite"),
        ([0, float("inf")], "finite"),
        (np.array([[0.0, 10.0], [20.0, 30.0]]), "1-D"),
        (np.array(10.0), "1-D"),
        (np.array([0.0 + 0.0j, 10.0 + 0.0j]), "dtype"),
        (np.array(["0", "10"]), "dtype"),
        (np.array([True, False]), "dtype"),
        (("0", "10"), "scalar"),
        ((0, 10.0 + 0.0j), "scalar"),
        ([0, [10]], "scalar"),
        (25.0, "list, tuple or numpy.ndarray"),
        ("0,10,25", "list, tuple or numpy.ndarray"),
        (None, "list, tuple or numpy.ndarray"),
    ])
    def test_sep_bins(self, bad, token):
        assert_names(rejected(catalog(), cfg(sep_bins=bad)), "sep_bins", token)


# ---------------------------------------------------------------------------
# 5. Where validation happens
# ---------------------------------------------------------------------------

FAR = [[0.0, 0.0, 0.0], [0.5, 0.0, 0.0]]           # 500 kpc apart
STILL = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]


class TestValidationOrdering:
    def test_rejects_before_the_no_pairs_early_return(self):
        cat = make_catalog(FAR, STILL, [10.0, 9.5])
        cat["vz"] = cat["vz"].copy()
        cat["vz"][1] = np.nan
        assert_names(rejected(cat, cfg(max_sep=25.0)), "vz", "finite")

    def test_rejects_length_mismatch_before_the_no_pairs_early_return(self):
        cat = make_catalog(FAR, STILL, [10.0, 9.5])
        cat["log_stellar_mass"] = cat["log_stellar_mass"][:1]
        assert_names(rejected(cat, cfg(max_sep=25.0)), None, "same length")

    def test_rejects_before_the_mass_ratio_cut_early_return(self):
        cat = make_catalog([[0.0, 0.0, 0.0], [0.010, 0.0, 0.0]],
                           STILL, [10.5, 9.3])   # ratio 0.063 < 0.1
        cat["vx"] = cat["vx"].copy()
        cat["vx"][0] = np.inf
        assert_names(rejected(cat, cfg()), "vx", "finite")

    def test_finiteness_is_reported_before_the_box_range(self):
        cat = catalog()
        cat["x"] = cat["x"].copy()
        cat["x"][0] = np.nan
        assert_names(rejected(cat, cfg()), "x", "finite")

    def test_form_is_validated_before_coercion(self):
        """A numeric-looking string must not be parsed; a complex value must
        not be silently truncated to its real part."""
        cat = catalog()
        cat["box_size"] = "1.0"
        assert_names(rejected(cat, cfg()), "box_size", "scalar")

        assert_names(rejected(catalog(), cfg(max_sep=np.array(25.0))),
                     "max_sep", "scalar")
        assert_names(rejected(catalog(), cfg(max_sep=25.0 + 1.0j)),
                     "max_sep", "scalar")

        cat = catalog()
        cat["x"] = np.array(["0.0", "0.010"])
        assert_names(rejected(cat, cfg()), "x", "dtype")
