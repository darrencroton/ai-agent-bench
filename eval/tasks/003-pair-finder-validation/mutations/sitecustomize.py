"""Injects one behavioural mutation into pair_finder after import.

Used to test whether the Developer's OWN test suite can actually FAIL --
the test_adequacy rubric category. Selected by the MUTATION environment
variable. Works by monkey-patching the already-imported module's public
function post-import, so it operates identically regardless of how the
Developer structured their implementation internally, and no trial file is
ever edited.

Activated by putting this file's directory on PYTHONPATH (Python auto-imports
any sitecustomize.py found on sys.path at interpreter startup) and setting
MUTATION=<id> before running the trial's own pytest.

Four design constraints specific to this task -- read before adding a mutation:

1. **Patch only `find_pairs`.** It is the one name the task's Authorized
   Surface guarantees exists and keeps its signature; a submission is free to
   restructure or rename every private helper, so a mutation that patched
   `_assign_sep_bins` or a validator by name would silently no-op on a
   legitimate restructuring and hand out a free test_adequacy point.
   Modules are matched by BASENAME, so `import pair_finder`,
   `from src import pair_finder` and `import src.pair_finder` are all patched
   identically (Task 001's audit found exact-name matching gave a submission
   using a different import style zero mutations).

2. **Every mutation must be a strict no-op on valid input.** The mutation gate
   runs `pytest tests/`, which includes the frozen `tests/test_pair_finder.py`
   and `tests/test_statistical.py`. A mutation those files could kill on their
   own is a freebie that measures nothing about the submission's own tests. The
   sanitizing mutations below therefore fire only on input that violates the
   spec's contract; the over-tightening mutations reject only input classes no
   frozen fixture uses (empty catalogs, integer dtypes, tuple/ndarray
   `sep_bins`, NumPy scalars, boundary `mass_ratio_min`, negative masses); and
   the result mutations touch only the `-1` sentinels and integer-dtype input,
   neither of which any frozen fixture produces. Re-run the freebie control
   (each id against the three frozen files alone) before adding one.

3. **One mutation, one predicate.** An r1 review found that broad mutations
   (one covering every rejected `sep_bins` form at once, say) let a suite kill
   them with a single representative case, so a materially incomplete suite
   still scored 16/16. Each entry below removes, weakens or over-tightens
   exactly one requirement.

4. **Registry, not a dispatcher.** Mutations register themselves into one of
   five tables -- `_SANITIZERS`, `_RAW_SANITIZERS`, `_REJECTORS`,
   `_RESULT_MUTATORS`, `_CALL_WRAPPERS` -- and the families that vary only by
   field or key are generated in a loop. `_patch_pair_finder` is constant-size
   regardless of how many mutations there are.
"""
import functools
import importlib
import os
import sys

MUT = os.environ.get("MUTATION")

_CATALOG_ARRAYS = ("x", "y", "z", "vx", "vy", "vz", "log_stellar_mass")

_CONFIG_DEFAULTS = dict(
    max_sep=25.0,
    mass_ratio_min=0.1,
    sep_bins=[0, 10, 15, 20, 25],
    log_mass_min=8.0,
    log_mass_max=11.0,
    mass_bin_width=0.5,
    mass_bin_by="primary",
)

_SCALAR_CONFIG_KEYS = ("max_sep", "mass_ratio_min", "log_mass_min",
                       "log_mass_max", "mass_bin_width")

# --------------------------------------------------------------- registries
_SANITIZERS = {}        # id -> fn(catalog: dict, config: dict) -> (dict, dict)
_RAW_SANITIZERS = {}    # id -> fn(catalog, config) -> (catalog, config)
_REJECTORS = {}         # id -> fn(catalog, config) -> message or None
_RESULT_MUTATORS = {}   # id -> fn(result, catalog, config) -> result
_CALL_WRAPPERS = {}     # id -> fn(original) -> patched


def _register(table, name):
    def deco(fn):
        table[name] = fn
        return fn
    return deco


def sanitizer(name):
    """Repairs one malformed input class, so its rejection stops happening."""
    return _register(_SANITIZERS, name)


def raw_sanitizer(name):
    """As `sanitizer`, but also runs when an argument is not a dict."""
    return _register(_RAW_SANITIZERS, name)


def rejector(name):
    """Over-tightens: rejects an input the contract declares valid."""
    return _register(_REJECTORS, name)


def result_mutator(name):
    """Corrupts the computed result rather than the validation."""
    return _register(_RESULT_MUTATORS, name)


def call_wrapper(name):
    """Full control over the call, for mutations that are neither of the above."""
    return _register(_CALL_WRAPPERS, name)


def all_mutation_ids():
    """Every scored mutation id, for mutation_list.txt."""
    tables = (_SANITIZERS, _RAW_SANITIZERS, _REJECTORS, _RESULT_MUTATORS,
              _CALL_WRAPPERS)
    ids = set().union(*tables)
    assert sum(len(table) for table in tables) == len(ids), (
        f"an id is registered in two registries: {sorted(ids)}"
    )
    return sorted(ids)


# ------------------------------------------------------------------ helpers
def _np():
    import numpy as np
    return np


def _is_real_scalar(value):
    np = _np()
    return (not isinstance(value, (bool, np.bool_))
            and isinstance(value, (int, float, np.integer, np.floating)))


def _is_bad_form(value):
    """True for the scalar forms the contract rejects before coercion."""
    np = _np()
    return isinstance(value, (bool, np.bool_, str, bytes, bytearray,
                              complex, np.complexfloating, np.ndarray))


def _force_float(value):
    """Coerce a rejected scalar form to a float, the way a missing form check
    would let it through. Returns None if even that fails."""
    np = _np()
    try:
        if isinstance(value, (bytes, bytearray)):
            return float(value.decode())
        if isinstance(value, np.ndarray):
            return float(np.real(value.ravel()[0]))
        return float(np.real(np.asarray(value, dtype=complex)))
    except Exception:
        return None


def _real_1d(value):
    """Return value as a 1-D float array, or None if it is not one."""
    np = _np()
    if not isinstance(value, np.ndarray) or value.dtype.kind not in "iuf":
        return None
    if value.ndim != 1:
        return None
    return value.astype(float)


def _common_length(catalog):
    for key in _CATALOG_ARRAYS:
        arr = _real_1d(catalog.get(key))
        if arr is not None:
            return arr.size
    return 1


def _safe_box(catalog, fallback=1.0):
    np = _np()
    try:
        return 1.0 + max(
            float(np.max(np.abs(np.asarray(catalog[k], dtype=float))))
            for k in ("x", "y", "z"))
    except Exception:
        return fallback


def _sep_bins_edges(value):
    """The edge array the contract would form, or None if the form is wrong."""
    np = _np()
    if isinstance(value, np.ndarray):
        if value.dtype.kind not in "iuf" or value.ndim != 1:
            return None
        return value.astype(float)
    if isinstance(value, (list, tuple)):
        if not all(_is_real_scalar(v) for v in value):
            return None
        return np.asarray([float(v) for v in value], dtype=float)
    return None


def _valid_catalog():
    np = _np()
    zero = np.zeros(1, dtype=float)
    cat = {key: zero.copy() for key in _CATALOG_ARRAYS}
    cat["box_size"] = 1.0
    return cat


# =========================================================================
# Sanitizing mutations: each removes exactly one required check.
# =========================================================================
def _peer_length(cat, key):
    """The shared length of the other valid arrays, if they agree."""
    lengths = {_real_1d(cat.get(other)).size for other in _CATALOG_ARRAYS
               if other != key and _real_1d(cat.get(other)) is not None}
    return lengths.pop() if len(lengths) == 1 else None


def _make_missing_catalog_key(key):
    @sanitizer(f"M01_catalog_key_presence_{key}")
    def _sanitize(cat, cfg, _key=key):
        if _key not in cat:
            if _key == "box_size":
                cat[_key] = _safe_box(cat)
            else:
                cat[_key] = _np().zeros(_common_length(cat), dtype=float)
        return cat, cfg
    return _sanitize


for _field in _CATALOG_ARRAYS + ("box_size",):
    _make_missing_catalog_key(_field)


def _make_length_repair(key):
    @sanitizer(f"M02_catalog_length_mismatch_{key}")
    def _sanitize(cat, cfg, _key=key):
        arr = _real_1d(cat.get(_key))
        n = _peer_length(cat, _key)
        if arr is not None and n is not None and arr.size != n:
            cat[_key] = _np().resize(arr, n)
        return cat, cfg
    return _sanitize


def _make_nonfinite_repair(key):
    @sanitizer(f"M03_catalog_nonfinite_{key}")
    def _sanitize(cat, cfg, _key=key):
        np = _np()
        arr = _real_1d(cat.get(_key))
        if arr is not None and not np.all(np.isfinite(arr)):
            cat[_key] = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
        return cat, cfg
    return _sanitize


def _make_rank_repair(key):
    @sanitizer(f"M04_catalog_rank_{key}")
    def _sanitize(cat, cfg, _key=key):
        np = _np()
        value = cat.get(_key)
        if isinstance(value, np.ndarray) and value.ndim != 1:
            arr = np.atleast_1d(value.ravel())
            n = _peer_length(cat, _key)
            cat[_key] = np.resize(arr, n) if n is not None else arr
        return cat, cfg
    return _sanitize


def _make_container_repair(key):
    @sanitizer(f"M05a_catalog_container_{key}")
    def _sanitize(cat, cfg, _key=key):
        if _key in cat and not isinstance(cat[_key], _np().ndarray):
            arr = _np().asarray(cat[_key])
            if arr.ndim != 1 or arr.dtype.kind not in "iuf":
                arr = _np().zeros(_common_length(cat), dtype=float)
            cat[_key] = arr
        return cat, cfg
    return _sanitize


def _make_dtype_repair(key):
    @sanitizer(f"M05b_catalog_dtype_{key}")
    def _sanitize(cat, cfg, _key=key):
        np = _np()
        value = cat.get(_key)
        if not isinstance(value, np.ndarray) or value.dtype.kind in "iuf":
            return cat, cfg
        try:
            raw = np.real(value) if value.dtype.kind == "c" else value
            cat[_key] = np.atleast_1d(raw.astype(float))
        except (TypeError, ValueError):
            cat[_key] = np.zeros(_common_length(cat), dtype=float)
        return cat, cfg
    return _sanitize


for _field in _CATALOG_ARRAYS:
    _make_length_repair(_field)
    _make_nonfinite_repair(_field)
    _make_rank_repair(_field)
    _make_container_repair(_field)
    _make_dtype_repair(_field)


@sanitizer("M06_box_size_form")
def _m06(cat, cfg):
    if "box_size" in cat and _is_bad_form(cat["box_size"]):
        coerced = _force_float(cat["box_size"])
        if coerced is not None:
            cat["box_size"] = coerced
    return cat, cfg


def _make_box_size_value_repair(name, predicate):
    @sanitizer(name)
    def _sanitize(cat, cfg, _predicate=predicate):
        value = cat.get("box_size")
        if _is_real_scalar(value) and _predicate(float(value)):
            cat["box_size"] = _safe_box(cat)
        return cat, cfg
    return _sanitize


_make_box_size_value_repair("M07_box_size_nonfinite",
                            lambda value: not _np().isfinite(value))
_make_box_size_value_repair("M07_box_size_nonpositive",
                            lambda value: _np().isfinite(value) and value <= 0)


def _make_position_repair(key):
    @sanitizer(f"M08_position_outside_box_{key}")
    def _sanitize(cat, cfg, _key=key):
        np = _np()
        value = cat.get("box_size")
        arr = _real_1d(cat.get(_key))
        if (_is_real_scalar(value) and arr is not None
                and np.all(np.isfinite(arr))):
            box = float(value)
            if np.isfinite(box) and box > 0 and (
                    np.any(arr < 0) or np.any(arr >= box)):
                cat[_key] = np.mod(arr, box)
        return cat, cfg
    return _sanitize


for _field in ("x", "y", "z"):
    _make_position_repair(_field)


def _make_missing_config_key(key, default):
    @sanitizer(f"M09_config_key_presence_{key}")
    def _sanitize(cat, cfg, _key=key, _default=default):
        if _key not in cfg:
            cfg[_key] = _default
        return cat, cfg
    return _sanitize


for _field, _default in _CONFIG_DEFAULTS.items():
    _make_missing_config_key(_field, _default)


def _make_scalar_value_repair(name, key, predicate, replacement):
    @sanitizer(name)
    def _sanitize(cat, cfg, _predicate=predicate, _key=key,
                  _replacement=replacement):
        value = cfg.get(_key)
        if _is_real_scalar(value) and _predicate(float(value)):
            cfg[_key] = _replacement
        return cat, cfg
    return _sanitize


_make_scalar_value_repair("M10_max_sep_nonfinite", "max_sep",
                          lambda value: not _np().isfinite(value), 25.0)
_make_scalar_value_repair("M10_max_sep_nonpositive", "max_sep",
                          lambda value: _np().isfinite(value) and value <= 0,
                          25.0)
_make_scalar_value_repair("M11_mass_ratio_min_nonfinite", "mass_ratio_min",
                          lambda value: not _np().isfinite(value), 0.1)
_make_scalar_value_repair("M11_mass_ratio_min_outside_range",
                          "mass_ratio_min",
                          lambda value: _np().isfinite(value)
                          and not 0.0 <= value <= 1.0, 0.1)


def _make_scalar_form_repair(key):
    @sanitizer(f"M12_config_scalar_form_{key}")
    def _sanitize(cat, cfg, _key=key):
        if _key in cfg and _is_bad_form(cfg[_key]):
            coerced = _force_float(cfg[_key])
            if coerced is not None:
                cfg[_key] = coerced
        return cat, cfg
    return _sanitize


for _field in _SCALAR_CONFIG_KEYS:
    _make_scalar_form_repair(_field)


# ---- sep_bins, one predicate per mutation -------------------------------
@sanitizer("M13a_sep_bins_container")
def _m13a(cat, cfg):
    np = _np()
    value = cfg.get("sep_bins")
    if "sep_bins" in cfg and not isinstance(value, (list, tuple, np.ndarray)):
        cfg["sep_bins"] = list(_CONFIG_DEFAULTS["sep_bins"])
    return cat, cfg


@sanitizer("M13b_sep_bins_dtype")
def _m13b(cat, cfg):
    np = _np()
    value = cfg.get("sep_bins")
    if isinstance(value, np.ndarray) and value.dtype.kind not in "iuf":
        try:
            raw = np.real(value) if value.dtype.kind == "c" else value
            cfg["sep_bins"] = raw.astype(float)
        except Exception:
            pass
    return cat, cfg


@sanitizer("M13c_sep_bins_rank")
def _m13c(cat, cfg):
    np = _np()
    value = cfg.get("sep_bins")
    if isinstance(value, np.ndarray) and value.dtype.kind in "iuf" and value.ndim != 1:
        cfg["sep_bins"] = np.atleast_1d(value.ravel())
    return cat, cfg


@sanitizer("M13d_sep_bins_element_form")
def _m13d(cat, cfg):
    value = cfg.get("sep_bins")
    if isinstance(value, (list, tuple)) and not all(_is_real_scalar(v) for v in value):
        coerced = [v if _is_real_scalar(v) else _force_float(v) for v in value]
        if all(v is not None for v in coerced):
            cfg["sep_bins"] = [float(v) for v in coerced]
    return cat, cfg


@sanitizer("M13e_sep_bins_min_length")
def _m13e(cat, cfg):
    edges = _sep_bins_edges(cfg.get("sep_bins"))
    if edges is not None and edges.size < 2:
        cfg["sep_bins"] = list(_CONFIG_DEFAULTS["sep_bins"])
    return cat, cfg


@sanitizer("M13f_sep_bins_finite")
def _m13f(cat, cfg):
    np = _np()
    edges = _sep_bins_edges(cfg.get("sep_bins"))
    if edges is not None and edges.size >= 2 and not np.all(np.isfinite(edges)):
        kept = edges[np.isfinite(edges)]
        cfg["sep_bins"] = (list(kept) if kept.size >= 2
                           else list(_CONFIG_DEFAULTS["sep_bins"]))
    return cat, cfg


@sanitizer("M13g_sep_bins_monotonic")
def _m13g(cat, cfg):
    np = _np()
    edges = _sep_bins_edges(cfg.get("sep_bins"))
    if (edges is not None and edges.size >= 2 and np.all(np.isfinite(edges))
            and not np.all(np.diff(edges) > 0)):
        fixed = np.unique(edges)
        cfg["sep_bins"] = (list(fixed) if fixed.size >= 2
                           else list(_CONFIG_DEFAULTS["sep_bins"]))
    return cat, cfg


# ---- the mass grid, one predicate per mutation --------------------------
def _grid_floats(cfg):
    """(min, max, width) as floats when all three have an accepted form."""
    values = []
    for key in ("log_mass_min", "log_mass_max", "mass_bin_width"):
        value = cfg.get(key)
        if not _is_real_scalar(value):
            return None
        values.append(float(value))
    return tuple(values)


def _make_mass_limit_finite_repair(key, default):
    @sanitizer(f"M14a_{key}_finite")
    def _sanitize(cat, cfg, _key=key, _default=default):
        value = cfg.get(_key)
        if _is_real_scalar(value) and not _np().isfinite(float(value)):
            cfg[_key] = _default
        return cat, cfg
    return _sanitize


_make_mass_limit_finite_repair("log_mass_min", 8.0)
_make_mass_limit_finite_repair("log_mass_max", 11.0)


_make_scalar_value_repair("M14b_mass_bin_width_nonfinite", "mass_bin_width",
                          lambda value: not _np().isfinite(value), 0.5)
_make_scalar_value_repair("M14b_mass_bin_width_nonpositive", "mass_bin_width",
                          lambda value: _np().isfinite(value) and value <= 0,
                          0.5)


@sanitizer("M14c_mass_range_ordering")
def _m14c(cat, cfg):
    np = _np()
    grid = _grid_floats(cfg)
    if grid is None:
        return cat, cfg
    lo, hi, width = grid
    if np.isfinite(lo) and np.isfinite(hi) and hi <= lo:
        cfg["log_mass_max"] = lo + max(1.0, abs(width) if np.isfinite(width) else 1.0)
    return cat, cfg


@sanitizer("M14d_mass_bin_count")
def _m14d(cat, cfg):
    np = _np()
    grid = _grid_floats(cfg)
    if grid is None:
        return cat, cfg
    lo, hi, width = grid
    if (np.isfinite(lo) and np.isfinite(hi) and np.isfinite(width)
            and width > 0 and hi > lo and round((hi - lo) / width) < 1):
        cfg["mass_bin_width"] = hi - lo
    return cat, cfg


# =========================================================================
# Top-level argument form (these must see the raw, possibly non-dict args).
# =========================================================================
@raw_sanitizer("M17_catalog_argument_form")
def _m17(catalog, config):
    if not isinstance(catalog, dict):
        catalog = _valid_catalog()
    return catalog, config


@raw_sanitizer("M18_config_argument_form")
def _m18(catalog, config):
    if not isinstance(config, dict):
        config = dict(_CONFIG_DEFAULTS)
    return catalog, config


# =========================================================================
# Over-tightening mutations: reject something the contract declares valid.
# Killed only by a suite that tests the "must NOT reject" half of the spec.
# =========================================================================
@rejector("M20_reject_empty_catalog")
def _m20(catalog, config):
    np = _np()
    if not isinstance(catalog, dict):
        return None
    arrays = [catalog.get(k) for k in _CATALOG_ARRAYS]
    if all(isinstance(a, np.ndarray) and a.size == 0 for a in arrays):
        return "catalog must contain at least one galaxy"
    return None


# M21: one mutation per catalog field. An r2 review found the single bundled
# version was killed by any one field's integer-acceptance test, so a suite
# covering one field scored the same as a suite covering all seven.
def _make_reject_integer_field(field):
    @rejector(f"M21_reject_integer_dtype_{field}")
    def _reject(catalog, config, _field=field):
        np = _np()
        if not isinstance(catalog, dict):
            return None
        value = catalog.get(_field)
        if isinstance(value, np.ndarray) and value.dtype.kind in "iu":
            return f"catalog['{_field}'] must have a floating dtype"
        return None
    return _reject


for _field in _CATALOG_ARRAYS:
    _make_reject_integer_field(_field)


# M22: one mutation per accepted sep_bins container form. The frozen suite
# only ever passes a plain int list, so every one of these is freebie-free.
def _make_reject_sep_bins_form(name, predicate):
    @rejector(f"M22_reject_sep_bins_{name}")
    def _reject(catalog, config, _predicate=predicate):
        if not isinstance(config, dict) or "sep_bins" not in config:
            return None
        try:
            hit = _predicate(config["sep_bins"])
        except Exception:
            hit = False
        if hit:
            return f"config['sep_bins'] must not be given as {name}"
        return None
    return _reject


def _is_numpy_scalar_element_list(value):
    np = _np()
    return (isinstance(value, (list, tuple))
            and any(isinstance(v, (np.integer, np.floating)) for v in value))


_make_reject_sep_bins_form(
    "tuple", lambda v: isinstance(v, tuple))
_make_reject_sep_bins_form(
    "float_ndarray",
    lambda v: isinstance(v, _np().ndarray) and v.dtype.kind == "f")
_make_reject_sep_bins_form(
    "int_ndarray",
    lambda v: isinstance(v, _np().ndarray) and v.dtype.kind in "iu")
_make_reject_sep_bins_form(
    "numpy_scalar_elements", _is_numpy_scalar_element_list)


# M23: one mutation per (scalar key, NumPy scalar family). spec.md declares
# Python int/float and NumPy integer/floating all valid for every scalar key.
#
# `max_sep` + np.floating is the one combination deliberately absent: frozen
# tests/test_pair_finder.py::TestPeriodicBoundary::test_pair_across_corner
# passes `np.sqrt(3.0) * 2.0 + 1.0`, a np.float64, so rejecting it would be
# killed by the frozen suite alone -- a freebie. `max_sep` + np.integer is
# used by no frozen fixture and is included. Re-run the freebie control before
# "completing" this table.
_M23_TARGETS = [
    ("box_size", "catalog", "integer"), ("box_size", "catalog", "floating"),
    ("max_sep", "config", "integer"),
    ("mass_ratio_min", "config", "integer"),
    ("mass_ratio_min", "config", "floating"),
    ("log_mass_min", "config", "integer"),
    ("log_mass_min", "config", "floating"),
    ("log_mass_max", "config", "integer"),
    ("log_mass_max", "config", "floating"),
    ("mass_bin_width", "config", "integer"),
    ("mass_bin_width", "config", "floating"),
]


def _make_reject_numpy_scalar(key, where, family):
    @rejector(f"M23_reject_numpy_{family}_{key}")
    def _reject(catalog, config, _key=key, _where=where, _family=family):
        np = _np()
        holder = catalog if _where == "catalog" else config
        if not isinstance(holder, dict):
            return None
        wanted = np.integer if _family == "integer" else np.floating
        if isinstance(holder.get(_key), wanted):
            return (f"{_where}['{_key}'] must be a Python scalar, "
                    f"not a NumPy {_family}")
        return None
    return _reject


for _key, _where, _family in _M23_TARGETS:
    _make_reject_numpy_scalar(_key, _where, _family)


@rejector("M24_reject_mass_ratio_min_boundaries")
def _m24(catalog, config):
    # Only the upper boundary: frozen tests/test_statistical.py runs the
    # pipeline with mass_ratio_min = 0.0, so rejecting the lower boundary
    # would be a freebie. 1.0 is used by no frozen fixture.
    if not isinstance(config, dict):
        return None
    value = config.get("mass_ratio_min")
    if _is_real_scalar(value) and float(value) == 1.0:
        return "config['mass_ratio_min'] must be strictly below 1"
    return None


@rejector("M25_reject_negative_masses")
def _m25(catalog, config):
    np = _np()
    if not isinstance(catalog, dict):
        return None
    arr = _real_1d(catalog.get("log_stellar_mass"))
    if arr is not None and arr.size and np.any(arr < 0):
        return "catalog['log_stellar_mass'] must be non-negative"
    return None


# =========================================================================
# Result mutations: the computation itself, on paths no frozen fixture takes.
# =========================================================================
@result_mutator("M15_mass_bin_sentinel_dropped")
def _m15(out, catalog, config):
    np = _np()
    mb = np.asarray(out["mass_bin"])
    if mb.size and np.any(mb == -1):
        mb = mb.copy()
        mb[mb == -1] = 0
        out = dict(out)
        out["mass_bin"] = mb
    return out


@result_mutator("M16_sep_bin_sentinel_clipped")
def _m16(out, catalog, config):
    np = _np()
    sb = np.asarray(out["sep_bin"])
    if sb.size and np.any(sb == -1):
        n_bins = len(config["sep_bins"]) - 1
        sb = sb.copy()
        sb[sb == -1] = max(0, n_bins - 1)
        out = dict(out)
        out["sep_bin"] = sb
    return out


# M26: the integer-dtype conversion, split by the three distinct faults
# spec.md's table names. Each reproduces what the *unconverted* body does for
# one of them, so each is killed only by a suite that checks that fault's
# values -- not merely that no exception was raised.
def _mass_dtype_kind(catalog):
    np = _np()
    mass = catalog.get("log_stellar_mass") if isinstance(catalog, dict) else None
    if isinstance(mass, np.ndarray):
        return mass.dtype.kind
    return None


@call_wrapper("M26a_signed_integer_mass_cast_removed")
def _m26a(original):
    """Signed integer masses: the uncast body raises on `10 ** negative_int`."""
    @functools.wraps(original)
    def patched(catalog, config, *a, **k):
        if _mass_dtype_kind(catalog) == "i":
            raise ValueError(
                "Integers to negative integer powers are not allowed.")
        return original(catalog, config, *a, **k)

    return patched


@call_wrapper("M26b_unsigned_integer_mass_cast_removed")
def _m26b(original):
    """Unsigned integer masses: the uncast body wraps the mass difference,
    `10 ** huge` overflows to 0, so every pair is silently cut by the mass
    ratio and an empty result comes back."""
    np = _np()

    @functools.wraps(original)
    def patched(catalog, config, *a, **k):
        out = original(catalog, config, *a, **k)
        if _mass_dtype_kind(catalog) == "u":
            return {key: np.asarray(value)[:0] for key, value in out.items()}
        return out

    return patched


def _make_narrow_velocity_cast_removal(axis):
    @call_wrapper(f"M26c_narrow_integer_velocity_cast_removed_{axis}")
    def _wrapper(original, _axis=axis):
        """One velocity axis left integral: narrow integers overflow the
        squared sum, so the float-twin delta_v disagrees."""
        np = _np()

        @functools.wraps(original)
        def patched(catalog, config, *a, **k):
            if (isinstance(catalog, dict)
                    and isinstance(catalog.get(_axis), np.ndarray)
                    and catalog[_axis].dtype.kind in "iu"
                    and catalog[_axis].dtype.itemsize <= 2):
                catalog = dict(catalog)
                catalog[_axis] = catalog[_axis].astype(float) * 2.0
            return original(catalog, config, *a, **k)

        return patched
    return _wrapper


for _axis in ("vx", "vy", "vz"):
    _make_narrow_velocity_cast_removal(_axis)


# M19: one message obligation per mutation.  A global scrubber turns any one
# message assertion into credit for all messages sharing a word such as
# "finite" or "missing".  Each scrubber therefore applies to one concrete
# rejection class only.  The single unequal-length obligation is special: the
# spec accepts *any* array field name there, so its scrubber removes all seven
# accepted names, but only for that rejection.
def _is_valid_dict(value):
    return isinstance(value, dict)


def _valid_arguments(catalog, config):
    return _is_valid_dict(catalog) and _is_valid_dict(config)


def _missing_catalog(key):
    return lambda catalog, config: _valid_arguments(catalog, config) and key not in catalog


def _missing_config(key):
    return lambda catalog, config: (
        _valid_arguments(catalog, config) and key not in config
    )


def _wrong_catalog_container(key):
    return lambda catalog, config: (
        _valid_arguments(catalog, config) and key in catalog
        and not isinstance(catalog[key], _np().ndarray)
    )


def _wrong_catalog_dtype(key):
    return lambda catalog, config: (
        _valid_arguments(catalog, config)
        and isinstance(catalog.get(key), _np().ndarray)
        and catalog[key].dtype.kind not in "iuf"
    )


def _wrong_catalog_rank(key):
    return lambda catalog, config: (
        _valid_arguments(catalog, config)
        and isinstance(catalog.get(key), _np().ndarray)
        and catalog[key].ndim != 1
    )


def _unequal_lengths(catalog, config):
    if not _valid_arguments(catalog, config):
        return False
    arrays = (_real_1d(catalog.get(key)) for key in _CATALOG_ARRAYS)
    lengths = [array.size for array in arrays if array is not None]
    return len(lengths) == len(_CATALOG_ARRAYS) and len(set(lengths)) > 1


def _make_message_scrubber(name, tokens, applies):
    """Erase tokens only from the representative rejection `applies` picks."""
    ordered = tuple(sorted((tokens,) if isinstance(tokens, str) else tokens,
                           key=len, reverse=True))

    @call_wrapper(name)
    def _wrapper(original, _ordered=ordered, _applies=applies):
        @functools.wraps(original)
        def patched(catalog, config, *a, **k):
            try:
                return original(catalog, config, *a, **k)
            except AssertionError as exc:
                if not _applies(catalog, config):
                    raise
                message = str(exc)
                if not any(token in message for token in _ordered):
                    raise
                scrubbed = message
                for token in _ordered:
                    scrubbed = scrubbed.replace(token, "")
                scrubbed = scrubbed.strip() or "rejected"
            # This must be outside the handler. Raising here gives the mutated
            # AssertionError the same exception metadata as the bare assertion
            # from find_pairs; ``raise ... from None`` leaks a side channel.
            raise AssertionError(scrubbed)

        return patched
    return _wrapper


# Names: seventeen independently scored obligations.  `M19_name_x` is the
# flexible unequal-length rule: no particular field is required, so it removes
# every accepted field name from that one message rather than pretending the
# seven alternatives are seven separate obligations.
_make_message_scrubber("M19_name_catalog", "catalog",
                       lambda catalog, config: not _is_valid_dict(catalog))
_make_message_scrubber("M19_name_config", "config",
                       lambda catalog, config: _is_valid_dict(catalog)
                       and not _is_valid_dict(config))
_make_message_scrubber("M19_name_x", _CATALOG_ARRAYS, _unequal_lengths)
for _field in ("y", "z", "vx", "vy", "vz", "log_stellar_mass"):
    _make_message_scrubber(f"M19_name_{_field}", _field,
                           _missing_catalog(_field))
for _field in ("box_size",) + tuple(_CONFIG_DEFAULTS):
    _make_message_scrubber(f"M19_name_{_field}", _field,
                           (_missing_catalog(_field) if _field == "box_size"
                            else _missing_config(_field)))

# Reasons: each token is scoped to one representative concrete rejection.
_make_message_scrubber("M19_reason_dict", "dict",
                       lambda catalog, config: not _is_valid_dict(catalog))
_make_message_scrubber("M19_reason_missing", "missing", _missing_catalog("x"))
_make_message_scrubber("M19_reason_ndarray", "ndarray",
                       _wrong_catalog_container("x"))
_make_message_scrubber("M19_reason_dtype", "dtype", _wrong_catalog_dtype("x"))
_make_message_scrubber("M19_reason_1d", "1-D", _wrong_catalog_rank("x"))
_make_message_scrubber("M19_reason_same_length", "same length", _unequal_lengths)
_make_message_scrubber("M19_reason_finite", "finite",
                       lambda catalog, config: _valid_arguments(catalog, config)
                       and _real_1d(catalog.get("x")) is not None
                       and not _np().all(_np().isfinite(catalog["x"])))
_make_message_scrubber("M19_reason_box", "box",
                       lambda catalog, config: _valid_arguments(catalog, config)
                       and _is_real_scalar(catalog.get("box_size"))
                       and _real_1d(catalog.get("x")) is not None
                       and _np().any(catalog["x"] < 0))
_make_message_scrubber("M19_reason_positive", "positive",
                       lambda catalog, config: _valid_arguments(catalog, config)
                       and _is_real_scalar(catalog.get("box_size"))
                       and _np().isfinite(float(catalog["box_size"]))
                       and float(catalog["box_size"]) <= 0)
_make_message_scrubber("M19_reason_mass_ratio_range", "[0, 1]",
                       lambda catalog, config: _valid_arguments(catalog, config)
                       and _is_real_scalar(config.get("mass_ratio_min"))
                       and _np().isfinite(float(config["mass_ratio_min"]))
                       and not 0 <= float(config["mass_ratio_min"]) <= 1)
_make_message_scrubber("M19_reason_greater_than", "greater than",
                       lambda catalog, config: _valid_arguments(catalog, config)
                       and _grid_floats(config) is not None
                       and _grid_floats(config)[1] <= _grid_floats(config)[0])
_make_message_scrubber("M19_reason_mass_bin", "at least one mass bin",
                       lambda catalog, config: _valid_arguments(catalog, config)
                       and _grid_floats(config) is not None
                       and _grid_floats(config)[2] > 0
                       and _grid_floats(config)[1] > _grid_floats(config)[0]
                       and round((_grid_floats(config)[1] - _grid_floats(config)[0])
                                 / _grid_floats(config)[2]) < 1)
_make_message_scrubber("M19_reason_at_least_2", "at least 2",
                       lambda catalog, config: _valid_arguments(catalog, config)
                       and _sep_bins_edges(
                           config.get("sep_bins")) is not None
                       and _sep_bins_edges(config["sep_bins"]).size < 2)
_make_message_scrubber("M19_reason_strictly_increasing", "strictly increasing",
                       lambda catalog, config: _valid_arguments(catalog, config)
                       and _sep_bins_edges(
                           config.get("sep_bins")) is not None
                       and _sep_bins_edges(config["sep_bins"]).size >= 2
                       and _np().all(_np().isfinite(_sep_bins_edges(
                           config["sep_bins"])))
                       and not _np().all(_np().diff(_sep_bins_edges(
                           config["sep_bins"])) > 0))
_make_message_scrubber("M19_reason_sep_bins_container",
                       "list, tuple or numpy.ndarray",
                       lambda catalog, config: _valid_arguments(catalog, config)
                       and "sep_bins" in config
                       and not isinstance(config["sep_bins"],
                                          (list, tuple, _np().ndarray)))
_make_message_scrubber("M19_reason_scalar", "scalar",
                       lambda catalog, config: _valid_arguments(catalog, config)
                       and "max_sep" in config and _is_bad_form(config["max_sep"]))


# ============================================================ installation
def _install_sanitizer(module, fn, needs_dicts):
    original = module.find_pairs

    @functools.wraps(original)
    def patched(catalog, config, *a, **k):
        if needs_dicts:
            if not isinstance(catalog, dict) or not isinstance(config, dict):
                return original(catalog, config, *a, **k)
            cat, cfg = fn(dict(catalog), dict(config))
        else:
            cat, cfg = fn(catalog, config)
        return original(cat, cfg, *a, **k)

    module.find_pairs = patched


def _install_rejector(module, fn):
    original = module.find_pairs

    @functools.wraps(original)
    def patched(catalog, config, *a, **k):
        message = fn(catalog, config)
        if message:
            raise AssertionError(message)
        return original(catalog, config, *a, **k)

    module.find_pairs = patched


def _install_result_mutator(module, fn):
    original = module.find_pairs

    @functools.wraps(original)
    def patched(catalog, config, *a, **k):
        out = original(catalog, config, *a, **k)
        return fn(out, catalog, config)

    module.find_pairs = patched


def _patch_pair_finder(m):
    if MUT in _SANITIZERS:
        _install_sanitizer(m, _SANITIZERS[MUT], needs_dicts=True)
    elif MUT in _RAW_SANITIZERS:
        _install_sanitizer(m, _RAW_SANITIZERS[MUT], needs_dicts=False)
    elif MUT in _REJECTORS:
        _install_rejector(m, _REJECTORS[MUT])
    elif MUT in _RESULT_MUTATORS:
        _install_result_mutator(m, _RESULT_MUTATORS[MUT])
    elif MUT in _CALL_WRAPPERS:
        m.find_pairs = _CALL_WRAPPERS[MUT](m.find_pairs)


# --------------------------------------------------- the import hooks
# Ported from Task 001's mutations/sitecustomize.py, whose basename matching
# was the fix for that task's audit finding about exact-import-name patching.
# Extended with importlib.import_module/reload per Task 004/005's r1/r2
# findings: neither routes through builtins.__import__, so a submission using
# either would otherwise get no mutation at all.
def _is_target(fullname, mod):
    if mod is None:
        return False
    leaf = str(fullname).rsplit(".", 1)[-1]
    return leaf == "pair_finder" and hasattr(mod, "find_pairs")


def _patch_candidate(fullname, mod):
    """Install the selected mutation; never hide a failed patch install."""
    if not _is_target(fullname, mod):
        return
    if getattr(mod, "__MUTATED__", False):
        return
    mod.__MUTATED__ = True
    try:
        _patch_pair_finder(mod)
    except Exception:
        mod.__MUTATED__ = False
        raise


def _patch_all(candidates):
    seen = set()
    for fullname, mod in candidates:
        if mod is None or id(mod) in seen:
            continue
        seen.add(id(mod))
        _patch_candidate(fullname, mod)


_orig_import = (__builtins__["__import__"] if isinstance(__builtins__, dict)
                else __builtins__.__import__)
_orig_import_module = importlib.import_module
_orig_reload = importlib.reload


def _imp(name, *a, **k):
    m = _orig_import(name, *a, **k)
    candidates = [(name, sys.modules.get(name))]
    returned_name = getattr(m, "__name__", None)
    if returned_name:
        candidates.append((returned_name, m))
    fromlist = a[2] if len(a) > 2 else k.get("fromlist", ())
    for item in fromlist or ():
        if item != "*":
            fullname = f"{name}.{item}"
            candidates.append((fullname, sys.modules.get(fullname)))
    _patch_all(candidates)
    return m


def _import_module(name, package=None):
    m = _orig_import_module(name, package)
    candidates = [(getattr(m, "__name__", name), m)]
    if not str(name).startswith("."):
        candidates.append((name, sys.modules.get(name)))
    _patch_all(candidates)
    return m


def _reload(module):
    # Reload re-executes the module body in the same namespace: the
    # unwrapped function comes back but __MUTATED__ survives, so reset it
    # before re-patching or the trial silently runs unmutated.
    m = _orig_reload(module)
    name = getattr(m, "__name__", "")
    if not _is_target(name, m):
        return m
    m.__MUTATED__ = False
    _patch_all([(name, m)])
    return m


if MUT:
    if isinstance(__builtins__, dict):
        __builtins__["__import__"] = _imp
    else:
        __builtins__.__import__ = _imp
    importlib.import_module = _import_module
    importlib.reload = _reload
