"""Hidden Harness A: unit criteria for Task 003, derived solely from spec.md.

Not visible to the Developer model. Copied into the trial worktree's tests/
directory at grade time and run with the trial's own pytest/venv. Scores the
"correctness" rubric category (see eval/rubric.yaml) together with test_hB.py.

Structure: every malformed input is **one independently scored parametrized
case**, checked in a single invocation for all three things the contract
requires of it (an `AssertionError`, a message naming the offending argument or
key, and the message's required reason token). Every declared-valid input is
likewise one case. This is the fairness convention docs/DESIGN.md records for
Task 002: an aggregate loop test costs the same single failure whether a
submission missed one case or a whole behavioural category, which
under-penalizes corner-cutting.

Three things this file deliberately does NOT do:
  * inspect the submission's source text -- every check is behavioural;
  * pin a bit-exact `==` across intermediate floating-point arithmetic --
    values that came out of arithmetic are compared with assert_allclose;
  * import the module under test unguarded -- a broken submission must fail
    its own tests, not collapse this file's collection (and, with pytest's
    default behaviour, test_hB.py's too).

Cross-*key* ordering is never tested: spec.md declares it unspecified. The only
combined-fault cases below are the ones whose precedence spec.md does pin.
"""
import copy
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np
import pytest

try:
    import pair_finder as PF
except Exception as e:                      # pragma: no cover
    PF = None
    _PF_ERR = e


# --------------------------------------------------------------------------
# Fixtures: a config and catalog shape independent of src/config.py, so this
# file pins the contract rather than whatever config.py happens to say.
# --------------------------------------------------------------------------
CFG = dict(
    box_size       = 1.0,            # not read by find_pairs; present for realism
    log_mass_min   = 8.0,
    log_mass_max   = 11.0,
    mass_bin_width = 1.0,            # 3 bins: [8,9), [9,10), [10,11)
    sep_bins       = [0, 10, 15, 20, 25],   # kpc, 4 bins
    mass_ratio_min = 0.1,
    mass_bin_by    = "primary",
    max_sep        = 100.0,          # kpc, wide so sep_bin == -1 is reachable
)

ARRAYS = ("x", "y", "z", "vx", "vy", "vz", "log_stellar_mass")
CATALOG_KEYS = ARRAYS + ("box_size",)
CONFIG_KEYS = ("max_sep", "mass_ratio_min", "sep_bins",
               "log_mass_min", "log_mass_max", "mass_bin_width", "mass_bin_by")
SCALAR_CONFIG_KEYS = ("max_sep", "mass_ratio_min", "log_mass_min",
                      "log_mass_max", "mass_bin_width")

DELETE = object()          # sentinel: remove this key rather than replace it


def good_config():
    return copy.deepcopy(CFG)


def make_catalog(positions_mpc, velocities_kms, log_masses, box_size_mpc=1.0):
    pos = np.array(positions_mpc, dtype=float).reshape(-1, 3)
    vel = np.array(velocities_kms, dtype=float).reshape(-1, 3)
    return dict(
        x=pos[:, 0].copy(), y=pos[:, 1].copy(), z=pos[:, 2].copy(),
        vx=vel[:, 0].copy(), vy=vel[:, 1].copy(), vz=vel[:, 2].copy(),
        log_stellar_mass=np.array(log_masses, dtype=float),
        box_size=float(box_size_mpc),
    )


def good_catalog():
    """Two galaxies 10 kpc apart; |dv| == 5 km/s exactly; ratio 10**-0.5."""
    return make_catalog(
        positions_mpc=[[0.0, 0.0, 0.0], [0.010, 0.0, 0.0]],
        velocities_kms=[[3.0, 4.0, 0.0], [0.0, 0.0, 0.0]],
        log_masses=[10.0, 9.5],
    )


def cat_with(**over):
    c = good_catalog()
    for key, value in over.items():
        if value is DELETE:
            del c[key]
        else:
            c[key] = value
    return c


def cfg_with(**over):
    c = good_config()
    for key, value in over.items():
        if value is DELETE:
            del c[key]
        else:
            c[key] = value
    return c


EMPTY_KEYS = ("mass_primary", "mass_secondary", "mass_ratio",
              "separation_kpc", "delta_v", "mass_bin", "sep_bin")


def assert_empty_result(pairs):
    assert isinstance(pairs, dict)
    assert set(pairs.keys()) == set(EMPTY_KEYS), set(pairs.keys())
    for key in EMPTY_KEYS:
        arr = np.asarray(pairs[key])
        assert arr.ndim == 1 and arr.size == 0, (key, arr.shape)
    for key in EMPTY_KEYS[:5]:
        assert np.asarray(pairs[key]).dtype.kind == "f", (key, np.asarray(pairs[key]).dtype)
    for key in ("mass_bin", "sep_bin"):
        assert np.asarray(pairs[key]).dtype.kind in "iu", (key, np.asarray(pairs[key]).dtype)


def assert_result_shape(pairs):
    assert isinstance(pairs, dict)
    assert set(pairs.keys()) == set(EMPTY_KEYS), set(pairs.keys())
    n = np.asarray(pairs["delta_v"]).size
    for key in EMPTY_KEYS:
        arr = np.asarray(pairs[key])
        assert arr.ndim == 1 and arr.size == n, (key, arr.shape)
    return n


# ==========================================================================
# The rejection matrix. One entry == one independently scored test case.
# names: any one of these must appear in the message (word-boundary match).
# token: must appear in the message as a literal substring.
# ==========================================================================
REJECTIONS = []


def R(case_id, catalog, config, names, token):
    if isinstance(names, str):
        names = (names,)
    REJECTIONS.append((case_id, catalog, config, names, token))


# -- top-level argument form ----------------------------------------------
for _label, _bad in (("list", []), ("tuple", ()), ("none", None),
                     ("str", "catalog"), ("int", 5),
                     ("ndarray", np.array([1.0, 2.0]))):
    R(f"catalog_not_a_dict_{_label}", _bad, good_config(), "catalog", "dict")
for _label, _bad in (("list", []), ("none", None), ("str", "config")):
    R(f"config_not_a_dict_{_label}", good_catalog(), _bad, "config", "dict")

# -- catalog: missing required fields -------------------------------------
for _key in CATALOG_KEYS:
    R(f"catalog_missing_{_key}", cat_with(**{_key: DELETE}), good_config(),
      _key, "missing")

# -- catalog: rejected containers and dtypes, EVERY field x EVERY form ----
# Cartesian and generated rather than hand-written. spec.md requires every
# rejection to be tested for every field, not sampled, and an r2 review found
# that an implementation checking only some fields could accept
# boolean/string/object arrays in the five fields the earlier sampled matrix
# never reached, and still score 225/225.
N_GAL = 2

REJECTED_CONTAINERS = (
    ("list", lambda n: [0.0] * n),
    ("tuple", lambda n: tuple([0.0] * n)),
    ("none", lambda n: None),
    ("scalar", lambda n: 0.0),
)

REJECTED_DTYPES = (
    ("complex", lambda n: np.zeros(n, dtype=complex)),
    ("str", lambda n: np.array(["0.0"] * n)),
    ("bytes", lambda n: np.array([b"0.0"] * n)),
    ("bool", lambda n: np.zeros(n, dtype=bool)),
    ("object", lambda n: np.array([0.0] * (n - 1) + [None], dtype=object)),
)

for _key in ARRAYS:
    for _label, _make in REJECTED_CONTAINERS:
        R(f"catalog_container_{_label}_{_key}",
          cat_with(**{_key: _make(N_GAL)}), good_config(), _key, "ndarray")
    for _label, _make in REJECTED_DTYPES:
        R(f"catalog_dtype_{_label}_{_key}",
          cat_with(**{_key: _make(N_GAL)}), good_config(), _key, "dtype")

# -- catalog: wrong rank (every field, plus 0-D on two) -------------------
for _key in ARRAYS:
    R(f"catalog_2d_{_key}", cat_with(**{_key: np.zeros((2, 1))}), good_config(),
      _key, "1-D")
for _key in ("x", "vy"):
    R(f"catalog_0d_{_key}", cat_with(**{_key: np.array(0.0)}), good_config(),
      _key, "1-D")

# -- catalog: unequal lengths (every field) -------------------------------
# The message may name whichever field the implementation noticed, so any of
# the seven is accepted -- but naming none of them is not.
for _key in ARRAYS:
    R(f"catalog_short_{_key}", cat_with(**{_key: good_catalog()[_key][:1]}),
      good_config(), ARRAYS, "same length")

# -- catalog: non-finite values (every field, plus inf on three) ----------
for _key in ARRAYS:
    _bad = good_catalog()[_key].copy()
    _bad[0] = np.nan
    R(f"catalog_nan_{_key}", cat_with(**{_key: _bad}), good_config(),
      _key, "finite")
for _key in ("x", "vz", "log_stellar_mass"):
    _bad = good_catalog()[_key].copy()
    _bad[0] = np.inf
    R(f"catalog_inf_{_key}", cat_with(**{_key: _bad}), good_config(),
      _key, "finite")

# -- catalog: box_size value and form -------------------------------------
for _bad, _token in ((0.0, "positive"), (-1.0, "positive"),
                     (float("nan"), "finite"), (float("inf"), "finite")):
    R(f"box_size_value_{_bad}", cat_with(box_size=_bad), good_config(),
      "box_size", _token)
for _label, _bad in (("str", "1.0"), ("bytes", b"1.0"), ("complex", 1.0 + 0.0j),
                     ("bool", True), ("array0d", np.array(1.0)),
                     ("array1d", np.array([1.0]))):
    R(f"box_size_form_{_label}", cat_with(box_size=_bad), good_config(),
      "box_size", "scalar")

# -- catalog: positions outside the periodic box --------------------------
for _key in ("x", "y", "z"):
    for _label, _bad in (("at_box", 1.0), ("above_box", 1.5),
                         ("negative", -1e-9)):
        _arr = good_catalog()[_key].copy()
        _arr[0] = _bad
        R(f"position_{_label}_{_key}", cat_with(**{_key: _arr}), good_config(),
          _key, "box")

# -- config: missing required keys ----------------------------------------
for _key in CONFIG_KEYS:
    R(f"config_missing_{_key}", good_catalog(), cfg_with(**{_key: DELETE}),
      _key, "missing")

# -- config: max_sep value ------------------------------------------------
for _bad, _token in ((0.0, "positive"), (-1.0, "positive"),
                     (float("nan"), "finite"), (float("inf"), "finite")):
    R(f"max_sep_value_{_bad}", good_catalog(), cfg_with(max_sep=_bad),
      "max_sep", _token)

# -- config: mass_ratio_min value -----------------------------------------
for _bad, _token in ((-0.1, "[0, 1]"), (1.1, "[0, 1]"), (2.0, "[0, 1]"),
                     (float("nan"), "finite"), (float("inf"), "finite")):
    R(f"mass_ratio_min_value_{_bad}", good_catalog(),
      cfg_with(mass_ratio_min=_bad), "mass_ratio_min", _token)

# -- config: mass limits must be finite -----------------------------------
for _key in ("log_mass_min", "log_mass_max"):
    for _label, _bad in (("nan", float("nan")), ("inf", float("inf"))):
        R(f"{_key}_{_label}", good_catalog(), cfg_with(**{_key: _bad}),
          _key, "finite")

# -- config: mass_bin_width value -----------------------------------------
for _bad, _token in ((0.0, "positive"), (-1.0, "positive"),
                     (float("nan"), "finite"), (float("inf"), "finite"),
                     (10.0, "at least one mass bin")):
    R(f"mass_bin_width_value_{_bad}", good_catalog(),
      cfg_with(mass_bin_width=_bad), "mass_bin_width", _token)

# -- config: mass range ordering ------------------------------------------
for _bad in (8.0, 7.0, -1.0):
    R(f"log_mass_max_le_min_{_bad}", good_catalog(),
      cfg_with(log_mass_max=_bad), "log_mass_max", "greater than")

# -- config: scalar form, every scalar key --------------------------------
for _key in SCALAR_CONFIG_KEYS:
    for _label, _bad in (("str", "25.0"), ("complex", 25.0 + 0.0j),
                         ("bool", True), ("array0d", np.array(25.0))):
        R(f"config_form_{_key}_{_label}", good_catalog(),
          cfg_with(**{_key: _bad}), _key, "scalar")
for _label, _bad in (("bytes", b"25.0"), ("array1d", np.array([25.0]))):
    R(f"config_form_max_sep_{_label}", good_catalog(),
      cfg_with(max_sep=_bad), "max_sep", "scalar")

# -- config: sep_bins -----------------------------------------------------
for _label, _bad, _token in (
    ("one_edge_list", [0], "at least 2"),
    ("empty_list", [], "at least 2"),
    ("one_edge_tuple", (5.0,), "at least 2"),
    ("one_edge_ndarray", np.array([0.0]), "at least 2"),
    ("unsorted", [0, 10, 5, 25], "strictly increasing"),
    ("duplicate_edge", [0, 10, 10, 25], "strictly increasing"),
    ("decreasing", [25, 20, 10, 0], "strictly increasing"),
    ("unsorted_ndarray", np.array([0.0, 10.0, 5.0]), "strictly increasing"),
    ("nan_edge", [0, float("nan"), 25], "finite"),
    ("inf_edge", [0, float("inf")], "finite"),
    ("nan_edge_ndarray", np.array([0.0, np.nan, 25.0]), "finite"),
    ("2d_ndarray", np.array([[0.0, 10.0], [20.0, 30.0]]), "1-D"),
    ("0d_ndarray", np.array(10.0), "1-D"),
    ("complex_ndarray", np.array([0.0 + 0.0j, 10.0 + 0.0j]), "dtype"),
    ("str_ndarray", np.array(["0", "10"]), "dtype"),
    ("bool_ndarray", np.array([True, False]), "dtype"),
    ("str_elements", ("0", "10"), "scalar"),
    ("complex_element", (0, 10.0 + 0.0j), "scalar"),
    ("nested_element", [0, [10]], "scalar"),
    ("bool_element", [0, True], "scalar"),
    ("float_not_a_sequence", 25.0, "list, tuple or numpy.ndarray"),
    ("str_not_a_sequence", "0,10,25", "list, tuple or numpy.ndarray"),
    ("none_not_a_sequence", None, "list, tuple or numpy.ndarray"),
):
    R(f"sep_bins_{_label}", good_catalog(), cfg_with(sep_bins=_bad),
      "sep_bins", _token)

# -- combined faults whose precedence spec.md pins ------------------------
_nan_x = good_catalog()["x"].copy()
_nan_x[0] = np.nan
R("order_catalog_before_config", cat_with(x=_nan_x), cfg_with(max_sep=0.0),
  "x", "finite")
R("order_catalog_before_config_missing", cat_with(y=DELETE),
  cfg_with(max_sep=DELETE), "y", "missing")
R("order_sep_bins_finite_before_monotonic", good_catalog(),
  cfg_with(sep_bins=[0, float("nan"), 5, 25]), "sep_bins", "finite")
R("order_sep_bins_count_before_finite", good_catalog(),
  cfg_with(sep_bins=[float("nan")]), "sep_bins", "at least 2")
R("order_width_finite_before_bin_count", good_catalog(),
  cfg_with(mass_bin_width=float("inf")), "mass_bin_width", "finite")
R("order_width_positive_before_range", good_catalog(),
  cfg_with(mass_bin_width=0.0, log_mass_max=7.0), "mass_bin_width", "positive")
R("order_range_before_bin_count", good_catalog(),
  cfg_with(log_mass_max=7.0, mass_bin_width=10.0), "log_mass_max",
  "greater than")


# ==========================================================================
# The accepted-input matrix. One entry == one independently scored case.
# Everything here is declared valid by spec.md; rejecting any of it is an
# over-tightening defect.
# ==========================================================================
ACCEPTED = []


def A(case_id, catalog, config, expect_pairs=None):
    ACCEPTED.append((case_id, catalog, config, expect_pairs))


# Narrow dtypes first: 16-bit is where a realistic km/s velocity difference
# overflows the squared sum. 32- and 64-bit stay correct at these magnitudes
# and are here to prove the conversion does not change an already-right answer.
INT_DTYPES = (np.int16, np.uint16, np.int32, np.uint32, np.int64)


# |dv| = 500 exactly (a 3-4-5 triple scaled by 100) -- an ordinary peculiar
# velocity for this pipeline, which draws bulk motions at SIGMA_BULK = 200
# km/s. Under a 16-bit dtype the squared sum overflows: 300**2 = 90000 wraps
# to 24464 and 400**2 = 160000 wraps to 28928, so the recovered |dv| is
# 231.07 instead of 500.
_DV_COMPONENTS = (300, 400, 0)
_DV_MAGNITUDE = 500.0


def _int_catalog(dtype, descending_velocity=False):
    """All seven fields in one integer dtype, in a box where ints work.

    Positions are whole Mpc, so the one separation is 1000 kpc -- hence the
    wide max_sep and sep_bins in the config these cases are paired with.

    The velocity magnitude matters more than it looks. An r2 review pointed
    out that the earlier fixture's `(3,4,0)` could never expose a velocity
    fault, and it was right, but not for the reason either of us assumed:
    an unsigned subtraction wrap is *harmless on its own*, because modular
    squaring cancels it exactly (`(2**32 - 3)**2 mod 2**32 == 9`). The fault
    that does survive to the output is overflow of the squared sum, which is
    a function of the dtype's WIDTH, not the sign of the difference -- hence
    the 16-bit entries in INT_DTYPES and the 500 km/s magnitude above.

    `descending_velocity` swaps which galaxy carries the velocity so that
    `vel[i] - vel[j]` (pairs always come back with `i < j`) goes negative. It
    is kept because it costs nothing and pins that the sign direction is
    irrelevant.
    """
    fast, slow = ((0, 0, 0), _DV_COMPONENTS) if descending_velocity \
        else (_DV_COMPONENTS, (0, 0, 0))
    return dict(
        x=np.array([0, 1], dtype=dtype), y=np.array([0, 0], dtype=dtype),
        z=np.array([0, 0], dtype=dtype),
        vx=np.array([fast[0], slow[0]], dtype=dtype),
        vy=np.array([fast[1], slow[1]], dtype=dtype),
        vz=np.array([fast[2], slow[2]], dtype=dtype),
        log_stellar_mass=np.array([10, 9], dtype=dtype),
        box_size=np.array([3], dtype=dtype)[0],
    )


_WIDE = dict(max_sep=2000.0, sep_bins=[0, 1500, 3000])

for _dtype in INT_DTYPES:
    for _descending in (False, True):
        _suffix = "descending_dv" if _descending else "ascending_dv"
        A(f"all_{_dtype.__name__}_catalog_{_suffix}",
          _int_catalog(_dtype, _descending), cfg_with(**_WIDE), 1)

# One integer-dtype field at a time, across every field and both signedness
# families. Zeros are valid everywhere: inside the box for positions, a legal
# velocity, and a mass ratio of 1 for log_stellar_mass.
for _field in ARRAYS:
    for _dtype in (np.int64, np.uint32):
        A(f"int_dtype_field_{_field}_{_dtype.__name__}",
          cat_with(**{_field: np.zeros(N_GAL, dtype=_dtype)}), good_config(), 1)
A("int_mass", cat_with(log_stellar_mass=np.array([10, 9], dtype=np.int64)),
  good_config(), 1)

A("sep_bins_int_list", good_catalog(), cfg_with(sep_bins=[0, 10, 15, 20, 25]), 1)
A("sep_bins_float_tuple", good_catalog(),
  cfg_with(sep_bins=(0.0, 10.0, 15.0, 20.0, 25.0)), 1)
A("sep_bins_float_ndarray", good_catalog(),
  cfg_with(sep_bins=np.array([0.0, 10.0, 15.0, 20.0, 25.0])), 1)
A("sep_bins_int_ndarray", good_catalog(),
  cfg_with(sep_bins=np.array([0, 10, 15, 20, 25])), 1)
A("sep_bins_numpy_scalar_elements", good_catalog(),
  cfg_with(sep_bins=[np.int64(0), np.float32(10.0), 15, 20, np.float64(25.0)]), 1)
A("sep_bins_nondefault_grid", good_catalog(),
  cfg_with(sep_bins=[0.0, 5.0, 50.0]), 1)

# Every scalar key x every accepted scalar family. spec.md declares Python
# int/float and NumPy integer/floating all valid; an r2 review found no
# np.integer case existed for any config key, so an implementation rejecting
# every NumPy integer scalar scored full marks.
#
# (key, where, python_int, python_float, numpy_int, numpy_float)
SCALAR_ACCEPTED = (
    ("box_size",       "catalog", 1,   1.0,   np.int64(1),   np.float64(1.0)),
    ("max_sep",        "config",  100, 100.0, np.int64(100), np.float64(100.0)),
    ("mass_ratio_min", "config",  0,   0.1,   np.int64(0),   np.float32(0.1)),
    ("log_mass_min",   "config",  8,   8.0,   np.int64(8),   np.float32(8.0)),
    ("log_mass_max",   "config",  11,  11.0,  np.int64(11),  np.float64(11.0)),
    ("mass_bin_width", "config",  1,   1.0,   np.int64(1),   np.float64(1.0)),
)

for _key, _where, *_values in SCALAR_ACCEPTED:
    for _label, _value in zip(
            ("python_int", "python_float", "numpy_int", "numpy_float"),
            _values, strict=True):
        if _where == "catalog":
            A(f"scalar_{_key}_{_label}", cat_with(**{_key: _value}),
              good_config(), 1)
        else:
            A(f"scalar_{_key}_{_label}", good_catalog(),
              cfg_with(**{_key: _value}), 1)

A("mass_ratio_min_zero", good_catalog(), cfg_with(mass_ratio_min=0.0), 1)
A("mass_ratio_min_one", good_catalog(), cfg_with(mass_ratio_min=1.0), 0)
A("negative_finite_masses",
  make_catalog([[0.0, 0.0, 0.0], [0.010, 0.0, 0.0]],
               [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], [-1.0, -1.5]),
  good_config(), 1)
A("masses_far_above_log_mass_max",
  make_catalog([[0.0, 0.0, 0.0], [0.010, 0.0, 0.0]],
               [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], [14.0, 13.8]),
  good_config(), 1)
A("extra_valid_keys",
  {**good_catalog(), "redshift": 2.0,
   "is_paired": np.array([True, True]), "pair_id": np.array([0, 0])},
  good_config(), 1)
A("extra_malformed_keys",
  {**good_catalog(), "is_paired": "nonsense", "junk": None,
   "rubbish": np.array([[1.0, 2.0], [3.0, 4.0]]), "empty": np.array([])},
  good_config(), 1)
A("nondefault_mass_grid", good_catalog(),
  cfg_with(log_mass_min=9.0, log_mass_max=12.0, mass_bin_width=1.5), 1)
A("position_at_zero_and_just_below_box",
  make_catalog([[0.0, 0.0, 0.0], [np.nextafter(1.0, 0.0), 0.0, 0.0]],
               [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], [10.0, 9.5]),
  cfg_with(max_sep=10.0), 1)
A("extra_config_keys", good_catalog(),
  cfg_with(vel_bin_width=20.0, vel_max=1000.0, nonsense=None), 1)


# ==========================================================================
# Tests
# ==========================================================================
def test_A000_module_importable():
    assert PF is not None, f"src/pair_finder.py failed to import: {_PF_ERR!r}"
    assert callable(PF.find_pairs)


@pytest.mark.parametrize(
    "catalog,config,names,token",
    [c[1:] for c in REJECTIONS],
    ids=[c[0] for c in REJECTIONS],
)
def test_A100_rejects(catalog, config, names, token):
    """One malformed input: must assert, name the argument/key, name the reason."""
    try:
        PF.find_pairs(catalog, config)
    except AssertionError as e:
        message = str(e)
    except Exception as e:
        pytest.fail(
            f"expected AssertionError, got {type(e).__name__}: {e} -- a "
            f"low-level exception leaking from numpy/scipy is not a valid "
            f"rejection"
        )
    else:
        pytest.fail("malformed input was accepted without any exception")

    assert token in message, (
        f"message does not contain the required reason token {token!r}: {message!r}"
    )
    assert any(re.search(rf"\b{re.escape(n)}\b", message) for n in names), (
        f"message names none of {list(names)}: {message!r}"
    )


@pytest.mark.parametrize(
    "catalog,config,expect_pairs",
    [c[1:] for c in ACCEPTED],
    ids=[c[0] for c in ACCEPTED],
)
def test_A200_accepts(catalog, config, expect_pairs):
    """One declared-valid input: must not be rejected and must still compute."""
    try:
        pairs = PF.find_pairs(catalog, config)
    except Exception as e:
        pytest.fail(
            f"a declared-valid input was rejected with "
            f"{type(e).__name__}: {e} -- over-tightened validation"
        )
    n = assert_result_shape(pairs)
    if expect_pairs is not None:
        assert n == expect_pairs, f"expected {expect_pairs} pair(s), got {n}"


# ------------------------------------------------- preserved valid behaviour
def test_A300_pinned_pair_properties():
    pairs = PF.find_pairs(good_catalog(), good_config())
    assert len(pairs["delta_v"]) == 1
    np.testing.assert_allclose(pairs["separation_kpc"][0], 10.0, rtol=1e-12, atol=0)
    assert float(pairs["delta_v"][0]) == 5.0            # exact: sqrt(3**2+4**2)
    np.testing.assert_allclose(pairs["mass_ratio"][0], 10.0 ** -0.5,
                               rtol=1e-14, atol=0)
    assert float(pairs["mass_primary"][0]) == 10.0
    assert float(pairs["mass_secondary"][0]) == 9.5
    assert int(pairs["mass_bin"][0]) == 2                # primary 10.0 -> [10,11)
    assert int(pairs["sep_bin"][0]) == 1                 # 10 kpc -> [10,15)


def test_A301_periodic_boundary_pair_unchanged():
    """Minimum-image separation across the x boundary: 2 kpc, not 998 kpc."""
    cat = make_catalog(
        positions_mpc=[[0.001, 0.0, 0.0], [0.999, 0.0, 0.0]],
        velocities_kms=[[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
        log_masses=[10.0, 9.5],
    )
    pairs = PF.find_pairs(cat, cfg_with(max_sep=10.0))
    assert len(pairs["delta_v"]) == 1, "pair straddling the boundary was lost"
    np.testing.assert_allclose(pairs["separation_kpc"][0], 2.0, rtol=1e-9, atol=0)


def test_A302_no_pairs_early_return_preserved():
    cat = make_catalog([[0.0, 0.0, 0.0]], [[0.0, 0.0, 0.0]], [10.0])
    assert_empty_result(PF.find_pairs(cat, good_config()))


def test_A303_mass_ratio_cut_early_return_preserved():
    """Sole pair falls below mass_ratio_min: empty result, not an error."""
    cat = make_catalog(
        positions_mpc=[[0.0, 0.0, 0.0], [0.010, 0.0, 0.0]],
        velocities_kms=[[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]],
        log_masses=[10.5, 9.3],          # ratio 10**-1.2 ~ 0.063 < 0.1
    )
    assert_empty_result(PF.find_pairs(cat, good_config()))


def test_A304_empty_catalog_accepted():
    """Zero-length arrays are declared valid: no false-positive rejection."""
    e = np.array([], dtype=float)
    cat = {k: e.copy() for k in ARRAYS}
    cat["box_size"] = 1.0
    assert_empty_result(PF.find_pairs(cat, good_config()))


def test_A305_mass_bin_sentinel_above_range():
    cat = make_catalog([[0.0, 0.0, 0.0], [0.010, 0.0, 0.0]],
                       [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], [12.0, 11.8])
    pairs = PF.find_pairs(cat, good_config())
    assert len(pairs["delta_v"]) == 1
    assert int(pairs["mass_bin"][0]) == -1, int(pairs["mass_bin"][0])


def test_A306_mass_bin_sentinel_below_range():
    cat = make_catalog([[0.0, 0.0, 0.0], [0.010, 0.0, 0.0]],
                       [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], [7.5, 7.0])
    pairs = PF.find_pairs(cat, good_config())
    assert len(pairs["delta_v"]) == 1
    assert int(pairs["mass_bin"][0]) == -1, int(pairs["mass_bin"][0])


def test_A307_sep_bin_sentinel_beyond_last_edge():
    cat = make_catalog([[0.0, 0.0, 0.0], [0.030, 0.0, 0.0]],   # 30 kpc > 25
                       [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], [10.0, 9.5])
    pairs = PF.find_pairs(cat, good_config())
    assert len(pairs["delta_v"]) == 1
    np.testing.assert_allclose(pairs["separation_kpc"][0], 30.0, rtol=1e-12, atol=0)
    assert int(pairs["sep_bin"][0]) == -1, int(pairs["sep_bin"][0])


def test_A308_unknown_mass_bin_by_still_raises_value_error():
    with pytest.raises(ValueError, match="mass_bin_by"):
        PF.find_pairs(good_catalog(), cfg_with(mass_bin_by="nonsense"))


@pytest.mark.parametrize("strategy", ["primary", "secondary", "mean", "total"])
def test_A309_mass_bin_by_strategies_still_work(strategy):
    pairs = PF.find_pairs(good_catalog(), cfg_with(mass_bin_by=strategy))
    assert len(pairs["delta_v"]) == 1


def test_A310_signature_unchanged():
    """Two arguments, callable positionally and by the documented names."""
    positional = PF.find_pairs(good_catalog(), good_config())
    keyword = PF.find_pairs(catalog=good_catalog(), config=good_config())
    assert len(positional["delta_v"]) == len(keyword["delta_v"]) == 1


@pytest.mark.parametrize("descending", [False, True],
                         ids=["ascending_dv", "descending_dv"])
@pytest.mark.parametrize("dtype", INT_DTYPES,
                         ids=[d.__name__ for d in INT_DTYPES])
def test_A314_integer_catalog_matches_its_float_twin(dtype, descending):
    """Accepting an integer dtype is not enough -- it must give the same answer.

    The unconverted body does integer arithmetic on whatever it is handed:
    `10 ** (m_secondary - m_primary)` raises on signed integer masses, and
    overflows to 0 on unsigned ones (silently cutting the pair). For the
    velocities the fault is the component-wise `dv**2`, which overflows before
    NumPy's promoted reduction ever runs -- so it depends on the dtype's
    WIDTH, not on the sign of the difference. A subtraction wrap on its own is
    harmless, because the squaring that follows cancels it exactly.

    The 16-bit entries are the ones that reach the velocity fault here: at
    |dv| = 500 km/s the squared sum overflows and the recovered speed is
    231.07. An implementation that casts the masses (fixing the raise and the
    unsigned zero-ratio) but leaves the velocities integral passes every
    32/64-bit case here and fails the 16-bit ones. test_A315 covers the
    narrower widths and the per-component isolation.
    """
    int_cat = _int_catalog(dtype, descending_velocity=descending)
    float_cat = {k: (np.asarray(v, dtype=float) if isinstance(v, np.ndarray)
                     else float(v))
                 for k, v in int_cat.items()}
    config = cfg_with(**_WIDE)

    got = PF.find_pairs(int_cat, config)
    want = PF.find_pairs(float_cat, config)

    assert len(got["delta_v"]) == len(want["delta_v"]) == 1
    # Anchor the float twin itself, so this cannot pass by both sides being
    # equally wrong.
    np.testing.assert_allclose(float(np.asarray(want["delta_v"])[0]),
                               _DV_MAGNITUDE, rtol=1e-12, atol=0)
    np.testing.assert_allclose(float(np.asarray(want["mass_ratio"])[0]), 0.1,
                               rtol=1e-12, atol=0)
    for key in EMPTY_KEYS:
        np.testing.assert_allclose(
            np.asarray(got[key], dtype=float),
            np.asarray(want[key], dtype=float),
            rtol=1e-12, atol=0,
            err_msg=f"{dtype.__name__} catalog ({'descending' if descending else 'ascending'}"
                    f" dv) disagrees with its float twin on {key}")


# One nonzero velocity component, one dtype width. Two full-score-but-wrong
# implementations motivate this, both named by the r3 review:
#   * one that casts vx and vy but leaves vz integral -- every other
#     overflow-sensitive fixture in this file puts the motion in vx/vy, and
#     the per-field accepted cases use all-zero arrays, which prove acceptance
#     but not arithmetic;
#   * one that casts only the 16-bit widths -- the contract accepts every
#     `dtype.kind in "iuf"`, and 8-bit squares overflow at ordinary values.
# Magnitudes are the smallest ordinary ones that overflow each width, and the
# expected |dv| is just the magnitude, since only one component is nonzero.
#
#   int16/uint16 at 300 -> squares to 24464, |dv| 156.41 instead of 300
#   int8        at 30  -> squares to   -124, |dv| nan    instead of 30
#   uint8       at 30  -> squares to    132, |dv| 11.49  instead of 30
VELOCITY_WIDTH_CASES = ((np.int16, 300), (np.uint16, 300),
                        (np.int8, 30), (np.uint8, 30))


def _velocity_component_catalog(dtype, axis, magnitude):
    """A valid integer catalog whose only nonzero velocity is `axis`."""
    cat = dict(
        x=np.array([0, 1], dtype=dtype), y=np.zeros(N_GAL, dtype=dtype),
        z=np.zeros(N_GAL, dtype=dtype), vx=np.zeros(N_GAL, dtype=dtype),
        vy=np.zeros(N_GAL, dtype=dtype), vz=np.zeros(N_GAL, dtype=dtype),
        log_stellar_mass=np.array([10, 9], dtype=dtype),
        box_size=np.array([3], dtype=dtype)[0],
    )
    cat[axis] = np.array([magnitude, 0], dtype=dtype)
    return cat


@pytest.mark.parametrize("axis", ["vx", "vy", "vz"])
@pytest.mark.parametrize("dtype,magnitude", VELOCITY_WIDTH_CASES,
                         ids=[d.__name__ for d, _ in VELOCITY_WIDTH_CASES])
def test_A315_integer_velocity_component_matches_float_twin(dtype, magnitude, axis):
    """Every velocity component, at every width that overflows ordinarily."""
    int_cat = _velocity_component_catalog(dtype, axis, magnitude)
    float_cat = {k: (np.asarray(v, dtype=float) if isinstance(v, np.ndarray)
                     else float(v))
                 for k, v in int_cat.items()}
    config = cfg_with(**_WIDE)

    got = PF.find_pairs(int_cat, config)
    want = PF.find_pairs(float_cat, config)

    assert len(got["delta_v"]) == len(want["delta_v"]) == 1
    np.testing.assert_allclose(float(np.asarray(want["delta_v"])[0]),
                               float(magnitude), rtol=1e-12, atol=0)
    for key in EMPTY_KEYS:
        np.testing.assert_allclose(
            np.asarray(got[key], dtype=float),
            np.asarray(want[key], dtype=float),
            rtol=1e-12, atol=0,
            err_msg=f"{dtype.__name__} velocity in {axis} disagrees with its "
                    f"float twin on {key}")


def test_A311_validation_precedes_no_pairs_return_nonfinite():
    far = [[0.0, 0.0, 0.0], [0.5, 0.0, 0.0]]              # 500 kpc apart
    still = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    cat = make_catalog(far, still, [10.0, 9.5])
    cat["vz"] = cat["vz"].copy()
    cat["vz"][1] = np.nan
    with pytest.raises(AssertionError, match="finite"):
        PF.find_pairs(cat, cfg_with(max_sep=25.0))


def test_A312_validation_precedes_no_pairs_return_length():
    far = [[0.0, 0.0, 0.0], [0.5, 0.0, 0.0]]
    still = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    cat = make_catalog(far, still, [10.0, 9.5])
    cat["log_stellar_mass"] = cat["log_stellar_mass"][:1]
    with pytest.raises(AssertionError, match="same length"):
        PF.find_pairs(cat, cfg_with(max_sep=25.0))


def test_A313_validation_precedes_mass_ratio_cut_return():
    cat = make_catalog([[0.0, 0.0, 0.0], [0.010, 0.0, 0.0]],
                       [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]], [10.5, 9.3])
    cat["vx"] = cat["vx"].copy()
    cat["vx"][0] = np.inf
    with pytest.raises(AssertionError, match="finite"):
        PF.find_pairs(cat, good_config())
