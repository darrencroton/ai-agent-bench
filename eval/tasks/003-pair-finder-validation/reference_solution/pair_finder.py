"""
KD-tree pair finding and relative velocity computation.

Given a galaxy catalog (Mpc, km/s, log10 M_sun), finds all pairs within
max_sep kpc and returns their properties as arrays.

The only unit conversion in the pipeline: positions Mpc → kpc (×1000)
at the top of find_pairs(), so separations and the KD-tree radius are in kpc.

find_pairs() validates its own `catalog` and `config` arguments before doing
any arithmetic, because it is callable directly (the test suite and any
downstream user do exactly that) and must not rely on
data_reader.load_galaxy_catalog() having run first. Every rejection is an
AssertionError whose message names the offending key and the reason; see
"Validation conventions" below.
"""

import numpy as np
from scipy.spatial import cKDTree

# Catalog array fields find_pairs() reads. Any other key in the catalog dict
# (e.g. 'redshift', or the extra 'is_paired'/'pair_id' columns
# generate_test_data.py produces) is ignored and never validated: the frozen
# callers pass those through, and they are not inputs to this computation.
_REQUIRED_CATALOG_ARRAYS = ("x", "y", "z", "vx", "vy", "vz", "log_stellar_mass")

# Config keys find_pairs() and its private helpers read.
_REQUIRED_CONFIG_KEYS = (
    "max_sep", "mass_ratio_min", "sep_bins",
    "log_mass_min", "log_mass_max", "mass_bin_width", "mass_bin_by",
)


# --------------------------------------------------------------------------
# Validation conventions
#
# * Form before coercion. A dtype / shape / scalar-type check always runs
#   *before* the value is converted, so a numeric-looking string or a
#   complex value is reported rather than silently parsed or truncated.
# * Every rejection is an `assert` whose message names the reason plus either
#   the offending argument (`catalog` / `config`, for a top-level form
#   failure) or the offending key (everywhere else). For unequal array
#   lengths the message names at least one of the seven array fields.
#   No new TypeError/ValueError is introduced, and no low-level
#   exception (ZeroDivisionError from `mass_bin_width == 0`, scipy's
#   "data must be finite", numpy's "bins must be monotonically increasing")
#   is allowed to leak out of find_pairs() for any input class listed here.
# * `config['mass_bin_by']` is checked for *presence* only. Its value is
#   validated by _assign_mass_bins(), which raises ValueError for an unknown
#   strategy; that pre-existing behaviour is frozen by
#   tests/test_pair_finder.py and is deliberately left alone.
# --------------------------------------------------------------------------

def _real_scalar(value, name):
    """
    Validate that `value` is a real numeric scalar, then return it as float.

    Accepted: Python int/float and NumPy integer/floating scalars.
    Rejected by assertion, before any coercion: booleans, strings, bytes,
    complex values, and every ndarray (including 0-D arrays).

    Two assertions rather than one because `bool` is a subclass of `int`, so
    it has to be excluded ahead of the accepted-type check, not by it.
    """
    assert not isinstance(value, (bool, np.bool_)), (
        f"{name} must be a real numeric scalar, not a boolean"
    )
    assert isinstance(value, (int, float, np.integer, np.floating)), (
        f"{name} must be a real numeric scalar (Python or NumPy "
        f"integer/floating), not {type(value).__name__}: {value!r}"
    )
    return float(value)


def _finite_scalar(value, name):
    """_real_scalar plus a finiteness check."""
    out = _real_scalar(value, name)
    assert np.isfinite(out), f"{name} must be finite, got {out!r}"
    return out


def _catalog_array(catalog, key):
    """Validate the form of one required catalog array field and return it."""
    assert key in catalog, f"catalog is missing required key '{key}'"
    arr = catalog[key]
    assert isinstance(arr, np.ndarray), (
        f"catalog['{key}'] must be a numpy.ndarray, got {type(arr).__name__}"
    )
    assert arr.dtype.kind in "iuf", (
        f"catalog['{key}'] must have a real integer or floating dtype, "
        f"got dtype {arr.dtype}"
    )
    assert arr.ndim == 1, (
        f"catalog['{key}'] must be 1-D, got {arr.ndim}-D with shape {arr.shape}"
    )
    return arr


def _validate_catalog(catalog):
    """
    Fail loud on a malformed `catalog` argument.

    A zero-length catalog is valid: find_pairs() returns its empty-result
    structure for it, exactly as it does for a catalog with no pairs.
    """
    assert isinstance(catalog, dict), (
        f"catalog must be a dict, got {type(catalog).__name__}"
    )

    arrays = {key: _catalog_array(catalog, key)
              for key in _REQUIRED_CATALOG_ARRAYS}

    n = arrays["x"].size
    for key, arr in arrays.items():
        assert arr.size == n, (
            f"catalog arrays must all have the same length: catalog['{key}'] "
            f"has {arr.size} entries but catalog['x'] has {n}"
        )

    for key, arr in arrays.items():
        assert np.all(np.isfinite(arr)), (
            f"catalog['{key}'] must be finite: found NaN or inf"
        )

    assert "box_size" in catalog, "catalog is missing required key 'box_size'"
    box_size = _finite_scalar(catalog["box_size"], "catalog['box_size']")
    assert box_size > 0, (
        f"catalog['box_size'] must be positive, got {box_size!r}"
    )

    for key in ("x", "y", "z"):
        arr = arrays[key]
        assert np.all(arr >= 0.0) and np.all(arr < box_size), (
            f"catalog['{key}'] must lie inside the periodic box "
            f"[0, box_size) = [0, {box_size}) Mpc; the KD-tree's periodic "
            f"wrapping is undefined outside it"
        )


def _validate_sep_bins(value):
    """Fail loud on a malformed config['sep_bins']."""
    name = "config['sep_bins']"
    if isinstance(value, np.ndarray):
        assert value.dtype.kind in "iuf", (
            f"{name} must have a real integer or floating dtype, "
            f"got dtype {value.dtype}"
        )
        assert value.ndim == 1, (
            f"{name} must be 1-D, got {value.ndim}-D with shape {value.shape}"
        )
        edges = value.astype(float)
    else:
        assert isinstance(value, (list, tuple)), (
            f"{name} must be a list, tuple or numpy.ndarray, "
            f"got {type(value).__name__}"
        )
        edges = np.array(
            [_real_scalar(v, f"{name}[{i}]") for i, v in enumerate(value)],
            dtype=float,
        )

    assert edges.size >= 2, (
        f"{name} must have at least 2 edges to define one separation bin, "
        f"got {edges.size}"
    )
    assert np.all(np.isfinite(edges)), (
        f"{name} must be finite: found NaN or inf"
    )
    assert np.all(np.diff(edges) > 0), (
        f"{name} must be strictly increasing, got {list(edges)}"
    )


def _validate_config(config):
    """Fail loud on a malformed `config` argument."""
    assert isinstance(config, dict), (
        f"config must be a dict, got {type(config).__name__}"
    )
    for key in _REQUIRED_CONFIG_KEYS:
        assert key in config, f"config is missing required key '{key}'"

    max_sep = _finite_scalar(config["max_sep"], "config['max_sep']")
    assert max_sep > 0, f"config['max_sep'] must be positive, got {max_sep!r}"

    mass_ratio_min = _finite_scalar(
        config["mass_ratio_min"], "config['mass_ratio_min']")
    assert 0.0 <= mass_ratio_min <= 1.0, (
        f"config['mass_ratio_min'] must be in [0, 1], got {mass_ratio_min!r}"
    )

    log_mass_min = _finite_scalar(
        config["log_mass_min"], "config['log_mass_min']")
    log_mass_max = _finite_scalar(
        config["log_mass_max"], "config['log_mass_max']")
    mass_bin_width = _finite_scalar(
        config["mass_bin_width"], "config['mass_bin_width']")

    assert mass_bin_width > 0, (
        f"config['mass_bin_width'] must be positive, got {mass_bin_width!r}"
    )
    assert log_mass_max > log_mass_min, (
        f"config['log_mass_max'] must be greater than config['log_mass_min'], "
        f"got {log_mass_max!r} <= {log_mass_min!r}"
    )
    n_mass_bins = round((log_mass_max - log_mass_min) / mass_bin_width)
    assert n_mass_bins >= 1, (
        f"config['mass_bin_width'] must yield at least one mass bin over "
        f"[{log_mass_min}, {log_mass_max}], got {n_mass_bins}"
    )

    _validate_sep_bins(config["sep_bins"])


def _mass_bin_edges(config):
    """Return array of mass bin edges in log10(M_sun)."""
    n_bins = round((config["log_mass_max"] - config["log_mass_min"]) / config["mass_bin_width"])
    return np.linspace(config["log_mass_min"], config["log_mass_max"], n_bins + 1)


def _assign_mass_bins(log_mass_primary, log_mass_secondary, config):
    """
    Assign each pair to an integer mass bin based on config['mass_bin_by'].

    Returns an int array of bin indices (0-based). Pairs falling outside the
    mass range [log_mass_min, log_mass_max] are assigned index -1.
    """
    strategy = config["mass_bin_by"]
    if strategy == "primary":
        ref_mass = log_mass_primary
    elif strategy == "secondary":
        ref_mass = log_mass_secondary
    elif strategy == "mean":
        ref_mass = 0.5 * (log_mass_primary + log_mass_secondary)
    elif strategy == "total":
        # Total stellar mass in log space: log10(10^m1 + 10^m2)
        ref_mass = np.log10(10**log_mass_primary + 10**log_mass_secondary)
    else:
        raise ValueError(
            f"Unknown mass_bin_by strategy: '{strategy}'. "
            "Valid options: 'primary', 'secondary', 'mean', 'total'."
        )

    edges = _mass_bin_edges(config)
    # np.digitize returns 1-based; subtract 1 for 0-based, set out-of-range to -1.
    raw = np.digitize(ref_mass, edges) - 1
    n_bins = len(edges) - 1
    out_of_range = (raw < 0) | (raw >= n_bins)
    raw[out_of_range] = -1
    return raw


def _assign_sep_bins(separations_kpc, config):
    """
    Assign each pair to an integer separation bin.

    Returns int array; pairs outside the bin range get index -1.
    """
    edges = config["sep_bins"]
    raw = np.digitize(separations_kpc, edges) - 1
    n_bins = len(edges) - 1
    out_of_range = (raw < 0) | (raw >= n_bins)
    raw[out_of_range] = -1
    return raw


def find_pairs(catalog, config):
    """
    Find all galaxy pairs within max_sep kpc and compute their properties.

    Both arguments are validated before any arithmetic is done; a malformed
    one is rejected with an AssertionError naming the offending key and the
    reason. See the "Validation conventions" block at the top of this module
    for the exact contract.

    Parameters
    ----------
    catalog : dict
        Output of data_reader.load_galaxy_catalog(), or any dict carrying the
        same fields: 1D real ndarrays 'x', 'y', 'z' (Mpc, inside
        [0, box_size)), 'vx', 'vy', 'vz' (km/s) and 'log_stellar_mass'
        (log10 M_sun), all the same length and all finite, plus a finite
        positive real scalar 'box_size' (Mpc). Extra keys are ignored.
    config : dict
        Pipeline configuration. Must carry 'max_sep' (kpc, finite > 0),
        'mass_ratio_min' (finite, in [0, 1]), 'sep_bins' (>= 2 finite,
        strictly increasing edges), 'log_mass_min' / 'log_mass_max' /
        'mass_bin_width' (finite, max > min, width > 0, yielding >= 1 bin),
        and 'mass_bin_by'.

    Returns
    -------
    dict of 1D arrays, one entry per pair:
        'mass_primary'    : log10(M/M_sun), more massive galaxy
        'mass_secondary'  : log10(M/M_sun)
        'mass_ratio'      : M_secondary / M_primary (linear, always <= 1)
        'separation_kpc'  : 3D separation in kpc
        'delta_v'         : 3D relative speed in km/s
        'mass_bin'        : int, mass bin index (-1 if outside range)
        'sep_bin'         : int, separation bin index (-1 if outside range)
    """
    _validate_catalog(catalog)
    _validate_config(config)

    # Validated inputs become float64 working copies. `np.asarray(a, float)`
    # returns a float64 input unchanged, so this is a no-op for every caller
    # in this repo; it is here because the contract also accepts integer and
    # unsigned dtypes, and integer arithmetic would otherwise not merely be
    # slower but wrong, in three different ways:
    #
    #   * signed integer masses: `10 ** (m_secondary - m_primary)` raises
    #     "Integers to negative integer powers are not allowed";
    #   * unsigned integer masses: that same subtraction wraps, `10 ** huge`
    #     overflows to 0, and the pair is silently cut by the mass-ratio test;
    #   * integer velocities: the component-wise `dv**2` below overflows
    #     before NumPy's promoted reduction runs, so |dv| comes back wrong.
    #     This depends on the dtype's WIDTH, not on the sign of the
    #     difference -- an unsigned subtraction wrap is harmless by itself,
    #     since the squaring cancels it exactly. 16-bit overflows at a few
    #     hundred km/s, 8-bit at a few tens; both are ordinary values here.
    #
    # So every velocity column is converted, not just the ones any particular
    # fixture exercises. An integer-dtype catalog must give the same answer as
    # the float64 catalog holding the same numbers.
    #
    # Convert positions Mpc → kpc so the KD-tree radius is in kpc directly.
    pos_kpc = np.column_stack([
        np.asarray(catalog["x"], dtype=float) * 1e3,
        np.asarray(catalog["y"], dtype=float) * 1e3,
        np.asarray(catalog["z"], dtype=float) * 1e3,
    ])
    box_kpc   = float(catalog["box_size"]) * 1e3
    log_mass  = np.asarray(catalog["log_stellar_mass"], dtype=float)
    vel       = np.column_stack([
        np.asarray(catalog["vx"], dtype=float),
        np.asarray(catalog["vy"], dtype=float),
        np.asarray(catalog["vz"], dtype=float),
    ])

    max_sep   = float(config["max_sep"])     # kpc

    # Build KD-tree with periodic boundary conditions.
    tree = cKDTree(pos_kpc, boxsize=box_kpc)

    # query_pairs returns a set of (i, j) with i < j — no double-counting.
    raw_pairs = tree.query_pairs(r=max_sep)

    if len(raw_pairs) == 0:
        # Return empty arrays with correct structure so downstream code still runs.
        empty = np.array([], dtype=float)
        return dict(
            mass_primary=empty,
            mass_secondary=empty,
            mass_ratio=empty,
            separation_kpc=empty,
            delta_v=empty,
            mass_bin=np.array([], dtype=int),
            sep_bin=np.array([], dtype=int),
        )

    idx_i, idx_j = zip(*raw_pairs, strict=True)
    idx_i = np.array(idx_i)
    idx_j = np.array(idx_j)

    # Identify primary (more massive) and secondary.
    m_i = log_mass[idx_i]
    m_j = log_mass[idx_j]
    is_i_primary = m_i >= m_j

    log_mass_primary   = np.where(is_i_primary, m_i, m_j)
    log_mass_secondary = np.where(is_i_primary, m_j, m_i)

    # Mass ratio in linear space: always <= 1.
    mass_ratio = 10 ** (log_mass_secondary - log_mass_primary)

    # Apply mass ratio cut.
    mass_ratio_min = config["mass_ratio_min"]
    keep = mass_ratio >= mass_ratio_min
    idx_i              = idx_i[keep]
    idx_j              = idx_j[keep]
    log_mass_primary   = log_mass_primary[keep]
    log_mass_secondary = log_mass_secondary[keep]
    mass_ratio         = mass_ratio[keep]

    if len(idx_i) == 0:
        empty = np.array([], dtype=float)
        return dict(
            mass_primary=empty,
            mass_secondary=empty,
            mass_ratio=empty,
            separation_kpc=empty,
            delta_v=empty,
            mass_bin=np.array([], dtype=int),
            sep_bin=np.array([], dtype=int),
        )

    # Compute separations with minimum image convention (same as cKDTree uses internally).
    diff_kpc = pos_kpc[idx_i] - pos_kpc[idx_j]
    diff_kpc -= box_kpc * np.round(diff_kpc / box_kpc)
    separations_kpc = np.sqrt((diff_kpc**2).sum(axis=1))

    # Relative velocity magnitude.
    dv  = vel[idx_i] - vel[idx_j]
    delta_v = np.sqrt((dv**2).sum(axis=1))

    # Bin assignments.
    mass_bin = _assign_mass_bins(log_mass_primary, log_mass_secondary, config)
    sep_bin  = _assign_sep_bins(separations_kpc, config)

    return dict(
        mass_primary   = log_mass_primary,
        mass_secondary = log_mass_secondary,
        mass_ratio     = mass_ratio,
        separation_kpc = separations_kpc,
        delta_v        = delta_v,
        mass_bin       = mass_bin,
        sep_bin        = sep_bin,
    )
