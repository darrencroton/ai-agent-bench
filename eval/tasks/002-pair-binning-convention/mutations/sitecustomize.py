"""Injects one behavioural mutation into pair_binning after import.

Used to test whether the Developer's OWN test suite can actually FAIL --
the test_adequacy rubric category. Selected by the MUTATION environment
variable. Works by monkey-patching the already-imported module's public
functions post-import, so it operates identically regardless of how the
Developer structured their implementation internally, and no trial file is
ever edited.

Activated by putting this file's directory on PYTHONPATH (Python auto-
imports any sitecustomize.py found on sys.path at interpreter startup) and
setting MUTATION=<id> before running the trial's own pytest:

    PYTHONPATH=eval/tasks/002-pair-binning-convention/mutations \\
    MUTATION=M01_either_counts_once \\
    venv/bin/python -m pytest tests/ -q

Modules are matched by **basename**, so `import pair_binning`,
`from src import pair_binning` and `import src.pair_binning` are all patched
identically. Nothing here depends on a private helper existing: everything a
mutation needs (bin edges, result paths) is recomputed locally from the
config it is handed, so a submission that structured its internals
differently is still mutated the same way.

Same mechanism as Task 001's gate; see docs/DESIGN.md for that gate's
provenance.
"""
import functools
import importlib
import numbers
import os
import re
import sys

MUT = os.environ.get("MUTATION")

_CONVENTIONS = ("primary", "secondary", "either")
_OUTPUT_NAME = "pair_binning.hdf5"


# Mutation families are declared once, so the scored list cannot silently
# diverge from the branches below. Regenerate mutation_list.txt with:
#   PYTHONPATH=mutations python -c 'import sitecustomize as s; print("\\n".join(s.all_mutation_ids()))'
_M09 = tuple(f"M09_zero_zero_{field}_nan" for field in ("pair_fraction", "pair_fraction_err"))
_M10 = tuple(f"M10_pairfrac_{predicate}_validation" for predicate in
             ("n_pairs_rank", "n_galaxies_rank", "shape"))
_M11 = tuple(f"M11_pairfrac_{argument}_{predicate}_validation"
             for argument in ("n_pairs", "n_galaxies")
             for predicate in ("form", "finite", "nonnegative", "integer"))
_M13 = tuple(f"M13_{api}_convention_{predicate}_validation"
             for api in ("count_pairs", "count_excluded")
             for predicate in ("nonstring", "unsupported"))
_M14 = tuple(f"M14_{api}_mass_order_validation"
             for api in ("count_pairs", "count_excluded"))
_M15 = tuple(f"M15_{api}_{predicate}_validation"
             for api in ("count_pairs", "count_excluded")
             for predicate in ("primary_rank", "secondary_rank", "shape"))
_M16 = ("M16_count_galaxies_nonfinite_validation",
        "M16_count_pairs_primary_nonfinite_validation",
        "M16_count_pairs_secondary_nonfinite_validation",
        "M16_count_excluded_primary_nonfinite_validation",
        "M16_count_excluded_secondary_nonfinite_validation")
_M20 = tuple(f"M20_additivity_{argument}_{predicate}_validation"
             for argument in ("n_primary", "n_secondary", "n_either")
             for predicate in ("form", "rank", "finite", "nonnegative", "integer")) + (
                 "M20_additivity_shape_validation",)
_M22 = (
    "M22_driver_conventions_wrong_container_rejected",
    "M22_driver_conventions_empty_rejected",
    "M22_driver_conventions_duplicate_rejected",
    "M22_driver_conventions_unsupported_rejected",
    "M22_driver_conventions_nonstring_rejected",
    "M22_driver_data_file_missing_rejected",
    "M22_driver_results_file_missing_rejected",
) + tuple(f"M22_driver_provenance_{attr}_{predicate}_rejected"
            for attr in ("redshift", "mass_ratio_min", "max_sep_kpc")
            for predicate in ("missing", "form", "mismatch"))
_M24 = tuple(f"M24_reverse_persisted_{dataset}_mass_bins" for dataset in
             ("n_galaxies", "n_pairs", "pair_fraction", "pair_fraction_err"))
_M25 = tuple(f"M25_reverse_persisted_{dataset}_conventions" for dataset in
             ("n_pairs", "pair_fraction", "pair_fraction_err", "n_excluded_pairs"))
_M26 = tuple(f"M26_corrupt_output_{attr}_provenance" for attr in
             ("mass_ratio_min", "max_sep_kpc"))
_M27 = tuple(f"M27_{attr}_attr_always_true" for attr in
             ("additivity_checked", "additivity_holds"))
_M28 = ("M28_console_omits_heading",) + tuple(
    f"M28_console_omits_{field}" for field in
    ("z", "convention", "n_galaxies", "n_pairs", "n_excluded", "additivity"))
_M31 = tuple(f"M31_{key}_ignores_config" for key in
             ("log_mass_min", "log_mass_max", "mass_bin_width"))
_M34 = tuple(f"M34_provenance_{attr}_{predicate}_validation_disabled"
             for attr in ("redshift", "mass_ratio_min", "max_sep_kpc")
             for predicate in ("missing", "form", "mismatch"))

_SINGLE_MUTATIONS = (
    "M01_either_counts_once", "M02_either_is_primary", "M03_secondary_is_primary",
    "M04_denominator_from_pair_rows", "M05_count_gal_includes_upper_edge",
    "M06_count_gal_float_dtype", "M07_count_pairs_float_dtype", "M08_sigma_no_sqrt",
    "M12_pairfrac_zero_denominator_validation", "M17_excluded_zero",
    "M18_excluded_either_is_primary", "M19_additivity_always_true",
    "M21_write_before_preflight", "M23_use_stored_mass_bin",
    "M29_ignore_conventions_config", "M30_extra_result_key",
    "M32_additivity_forced_false", "M33_pairfrac_wrong_divisor",
)


def all_mutation_ids():
    """Every scored mutation id, in deterministic order."""
    return sorted(_SINGLE_MUTATIONS + _M09 + _M10 + _M11 + _M13 + _M14 + _M15
                  + _M16 + _M20 + _M22 + _M24 + _M25 + _M26 + _M27 + _M28
                  + _M31 + _M34)


def _edges_and_nbins(config):
    import numpy as np
    n = round((config["log_mass_max"] - config["log_mass_min"]) / config["mass_bin_width"])
    return np.linspace(config["log_mass_min"], config["log_mass_max"], n + 1), int(n)


def _bins(mass, config):
    """Local copy of the right-open bin assignment; -1 outside every bin."""
    import numpy as np
    edges, n = _edges_and_nbins(config)
    raw = np.digitize(np.asarray(mass, dtype=float), edges) - 1
    return np.where((raw < 0) | (raw >= n), -1, raw), n


def _counts(bin_arrays, n):
    import numpy as np
    out = np.zeros(n, dtype=np.int64)
    for arr in bin_arrays:
        for b in range(n):
            out[b] += int(np.count_nonzero(arr == b))
    return out


def _pairs_path(z, config):
    return os.path.join(config["results_dir"], f"pairs_z{z:.1f}.hdf5")


def _data_path(z, config):
    return os.path.join(config["data_dir"], f"test_z{z:.1f}.hdf5")


def _output_path(config):
    return os.path.join(config["results_dir"], _OUTPUT_NAME)


def _array(value):
    import numpy as np
    return np.asarray(value)


def _numeric_1d(value):
    import numpy as np
    arr = _array(value)
    return (arr.ndim == 1 and np.issubdtype(arr.dtype, np.number)
            and not np.iscomplexobj(arr))


def _predicate(value, predicate):
    """Whether one validation predicate, and no earlier one, is violated."""
    import numpy as np
    arr = _array(value)
    if predicate == "rank":
        return arr.ndim != 1
    if arr.ndim != 1:
        return False
    if predicate == "form":
        return not (np.issubdtype(arr.dtype, np.number) and not np.iscomplexobj(arr))
    if not _numeric_1d(value):
        return False
    farr = arr.astype(float)
    if predicate == "finite":
        return not np.all(np.isfinite(farr))
    if not np.all(np.isfinite(farr)):
        return False
    if predicate == "nonnegative":
        return np.any(farr < 0)
    if np.any(farr < 0):
        return False
    if predicate == "integer":
        return np.any(farr != np.round(farr))
    raise ValueError(f"unknown predicate: {predicate}")


def _valid_count_vector(value):
    return (_numeric_1d(value) and not _predicate(value, "finite")
            and not _predicate(value, "nonnegative")
            and not _predicate(value, "integer"))


def _safe_vector(value, *, minimum=0.0):
    """A valid numeric vector for malformed-input deferral mutations only."""
    import numpy as np
    try:
        arr = np.atleast_1d(np.asarray(value, dtype=float)).ravel()
    except (TypeError, ValueError):
        arr = np.zeros(1, dtype=float)
    arr = np.nan_to_num(arr, nan=minimum, posinf=minimum, neginf=minimum)
    return np.maximum(np.round(arr), minimum)


def _resized(vector, size):
    import numpy as np
    if len(vector) == size:
        return vector
    if len(vector) == 0:
        return np.zeros(size, dtype=vector.dtype)
    return np.resize(vector, size)


def _safe_pair_fraction_args(n_pairs, n_galaxies):
    import numpy as np
    p = _safe_vector(n_pairs)
    g = _safe_vector(n_galaxies)
    size = max(len(p), len(g))
    p = _resized(p, size)
    g = _resized(g, size)
    g = np.where((p > 0) & (g == 0), 1, g)
    return p, g


def _safe_pair_args(primary, secondary):
    import numpy as np
    p = _safe_vector(primary)
    s = _safe_vector(secondary)
    size = max(len(p), len(s))
    p = _resized(p, size)
    s = _resized(s, size)
    return np.maximum(p, s), np.minimum(p, s)


def _is_real_scalar(value):
    import numpy as np
    return (not isinstance(value, np.ndarray)
            and isinstance(value, (numbers.Real, np.integer, np.floating))
            and not isinstance(value, (bool, np.bool_)))


def _attr_state(z, config, attr):
    """Classify one provenance attr as valid, missing, form, or mismatch."""
    import h5py
    expected = {"redshift": float(z), "mass_ratio_min": float(config["mass_ratio_min"]),
                "max_sep_kpc": float(config["max_sep"])}
    with h5py.File(_pairs_path(z, config), "r") as fh:
        if attr not in fh.attrs:
            return "missing"
        value = fh.attrs[attr]
    if not _is_real_scalar(value):
        return "form"
    return "valid" if float(value) == expected[attr] else "mismatch"


def _prior_provenance_is_valid(z, config, attr):
    for earlier in ("redshift", "mass_ratio_min", "max_sep_kpc"):
        if earlier == attr:
            return True
        if _attr_state(z, config, earlier) != "valid":
            return False
    return True


def _provenance_issue(z, config, attr, predicate):
    return (_prior_provenance_is_valid(z, config, attr)
            and _attr_state(z, config, attr) == predicate)


def _only_provenance_issue(z, config, attr, predicate):
    """True only when this is the sole invalid provenance attribute."""
    attrs = ("redshift", "mass_ratio_min", "max_sep_kpc")
    return (_attr_state(z, config, attr) == predicate
            and all(_attr_state(z, config, other) == "valid"
                    for other in attrs if other != attr))


def _conventions_valid(config):
    values = config.get("pair_binning_conventions")
    return (isinstance(values, (list, tuple)) and bool(values)
            and all(isinstance(value, str) and value in _CONVENTIONS for value in values)
            and len(set(values)) == len(values))


def _driver_config_ready(config):
    if not isinstance(config, dict) or not all(
            key in config for key in
            ("redshifts", "data_dir", "results_dir", "pair_binning_conventions",
             "mass_ratio_min", "max_sep")):
        return False
    try:
        iter(config["redshifts"])
    except TypeError:
        return False
    return True


def _patch_pair_binning(m):
    # A structurally incomplete submission must fail through its own missing
    # API, not through mutation installation.
    required = set()
    if MUT in {"M01_either_counts_once", "M02_either_is_primary", "M03_secondary_is_primary",
               "M07_count_pairs_float_dtype"} or MUT.startswith(("M13_count_pairs_", "M14_count_pairs_", "M15_count_pairs_", "M16_count_pairs_")):
        required.add("count_pairs_per_mass_bin")
    if MUT in {"M04_denominator_from_pair_rows", "M21_write_before_preflight", "M23_use_stored_mass_bin"}:
        required.add("load_snapshot_counts" if MUT != "M21_write_before_preflight" else "run_binning_comparison")
    if MUT in {"M05_count_gal_includes_upper_edge", "M06_count_gal_float_dtype", "M16_count_galaxies_nonfinite_validation"}:
        required.add("count_galaxies_per_mass_bin")
    if MUT in {"M08_sigma_no_sqrt", "M12_pairfrac_zero_denominator_validation", "M33_pairfrac_wrong_divisor"} or MUT.startswith(("M09_", "M10_", "M11_")):
        required.add("compute_pair_fraction")
    if MUT in {"M17_excluded_zero", "M18_excluded_either_is_primary"} or MUT.startswith(("M13_count_excluded_", "M14_count_excluded_", "M15_count_excluded_", "M16_count_excluded_")):
        required.add("count_excluded_pairs")
    if MUT == "M19_additivity_always_true" or MUT.startswith("M20_") or MUT == "M32_additivity_forced_false":
        required.add("check_additivity")
    if MUT.startswith(("M22_", "M24_", "M25_", "M26_", "M27_", "M28_", "M29_", "M30_")):
        required.add("run_binning_comparison")
    if MUT.startswith("M31_"):
        required.update(("count_galaxies_per_mass_bin", "count_pairs_per_mass_bin"))
    if MUT.startswith("M34_"):
        required.update(("load_snapshot_counts", "count_galaxies_per_mass_bin",
                         "count_pairs_per_mass_bin", "count_excluded_pairs"))
    if any(name not in m.__dict__ for name in required):
        return
    import numpy as np

    # ------------------------------------------------ counting semantics

    if MUT == "M01_either_counts_once":
        o = m.count_pairs_per_mass_bin

        @functools.wraps(o)
        def f(mp, ms, convention, config, *a, **k):
            out = o(mp, ms, convention, config, *a, **k)
            if convention != "either":
                return out
            bp, n = _bins(mp, config)
            bs, _ = _bins(ms, config)
            out = np.asarray(out).copy()
            same = (bp == bs) & (bp >= 0)
            for b in range(min(n, len(out))):
                out[b] -= int(np.count_nonzero(same & (bp == b)))
            return out
        m.count_pairs_per_mass_bin = f

    elif MUT == "M02_either_is_primary":
        o = m.count_pairs_per_mass_bin

        @functools.wraps(o)
        def f(mp, ms, convention, config, *a, **k):
            if convention == "either":
                convention = "primary"
            return o(mp, ms, convention, config, *a, **k)
        m.count_pairs_per_mass_bin = f

    elif MUT == "M03_secondary_is_primary":
        o = m.count_pairs_per_mass_bin

        @functools.wraps(o)
        def f(mp, ms, convention, config, *a, **k):
            if convention == "secondary":
                convention = "primary"
            return o(mp, ms, convention, config, *a, **k)
        m.count_pairs_per_mass_bin = f

    elif MUT == "M04_denominator_from_pair_rows":
        if hasattr(m, "load_snapshot_counts"):
            o = m.load_snapshot_counts

            @functools.wraps(o)
            def f(z, config, *a, **k):
                res = o(z, config, *a, **k)
                if not isinstance(res, dict) or "n_galaxies" not in res:
                    return res
                import h5py
                with h5py.File(_pairs_path(z, config), "r") as fh:
                    mp = fh["mass_primary"][...]
                    ms = fh["mass_secondary"][...]
                bp, n = _bins(mp, config)
                bs, _ = _bins(ms, config)
                res = dict(res)
                res["n_galaxies"] = _counts([bp, bs], n)
                return res
            m.load_snapshot_counts = f

    elif MUT == "M05_count_gal_includes_upper_edge":
        o = m.count_galaxies_per_mass_bin

        @functools.wraps(o)
        def f(mass, config, *a, **k):
            out = np.asarray(o(mass, config, *a, **k)).copy()
            extra = int(np.count_nonzero(
                np.asarray(mass, dtype=float) == float(config["log_mass_max"])))
            if extra and len(out):
                out[-1] += extra
            return out
        m.count_galaxies_per_mass_bin = f

    elif MUT == "M06_count_gal_float_dtype":
        o = m.count_galaxies_per_mass_bin

        @functools.wraps(o)
        def f(*a, **k):
            return np.asarray(o(*a, **k), dtype=float)
        m.count_galaxies_per_mass_bin = f

    elif MUT == "M07_count_pairs_float_dtype":
        o = m.count_pairs_per_mass_bin

        @functools.wraps(o)
        def f(*a, **k):
            return np.asarray(o(*a, **k), dtype=float)
        m.count_pairs_per_mass_bin = f

    # --------------------------------------------------- pair fraction

    elif MUT == "M08_sigma_no_sqrt":
        o = m.compute_pair_fraction

        @functools.wraps(o)
        def f(npair, ngal, *a, **k):
            fp, sg = o(npair, ngal, *a, **k)
            fp = np.asarray(fp, dtype=float)
            p = np.asarray(npair, dtype=float)
            sg = np.where(p > 0, fp / np.where(p > 0, p, 1.0), 0.0)
            return fp, sg
        m.compute_pair_fraction = f

    elif MUT in _M09:
        o = m.compute_pair_fraction
        field = MUT.removeprefix("M09_zero_zero_").removesuffix("_nan")

        @functools.wraps(o)
        def f(npair, ngal, *a, **k):
            fp, sg = o(npair, ngal, *a, **k)
            fp = np.asarray(fp, dtype=float).copy()
            sg = np.asarray(sg, dtype=float).copy()
            p = np.asarray(npair, dtype=float).ravel()
            g = np.asarray(ngal, dtype=float).ravel()
            mask = (p == 0) & (g == 0)
            if mask.shape == fp.shape:
                if field == "pair_fraction":
                    fp[mask] = np.nan
                else:
                    sg[mask] = np.nan
            return fp, sg
        m.compute_pair_fraction = f

    elif MUT in _M10:
        o = m.compute_pair_fraction
        predicate = MUT.removeprefix("M10_pairfrac_").removesuffix("_validation")

        @functools.wraps(o)
        def f(npair, ngal, *a, **k):
            p = np.asarray(npair)
            g = np.asarray(ngal)
            target = ((predicate == "n_pairs_rank" and p.ndim != 1 and _valid_count_vector(ngal))
                      or (predicate == "n_galaxies_rank" and p.ndim == 1 and g.ndim != 1
                          and _valid_count_vector(npair))
                      or (predicate == "shape" and _valid_count_vector(npair)
                          and _valid_count_vector(ngal) and p.shape != g.shape))
            if target:
                p, g = _safe_pair_fraction_args(npair, ngal)
                return o(p, g, *a, **k)
            return o(npair, ngal, *a, **k)
        m.compute_pair_fraction = f

    elif MUT in _M11:
        o = m.compute_pair_fraction
        suffix = MUT.removeprefix("M11_pairfrac_").removesuffix("_validation")
        argument = "n_pairs" if suffix.startswith("n_pairs_") else "n_galaxies"
        predicate = suffix.removeprefix(f"{argument}_")

        @functools.wraps(o)
        def f(npair, ngal, *a, **k):
            value = npair if argument == "n_pairs" else ngal
            other = ngal if argument == "n_pairs" else npair
            if (_valid_count_vector(other) and _array(other).shape == _array(value).shape
                    and _predicate(value, predicate)):
                p, g = _safe_pair_fraction_args(npair, ngal)
                return o(p, g, *a, **k)
            return o(npair, ngal, *a, **k)
        m.compute_pair_fraction = f

    elif MUT == "M12_pairfrac_zero_denominator_validation":
        o = m.compute_pair_fraction

        @functools.wraps(o)
        def f(npair, ngal, *a, **k):
            p = np.asarray(npair, dtype=float)
            g = np.asarray(ngal, dtype=float)
            if p.ndim == g.ndim == 1 and p.shape == g.shape and np.any((p > 0) & (g == 0)):
                with np.errstate(all="ignore"):
                    fp = np.where(g > 0, p / np.where(g > 0, g, 1.0), 0.0)
                    sg = np.where(p > 0, fp / np.sqrt(np.where(p > 0, p, 1.0)), 0.0)
                return fp, sg
            return o(npair, ngal, *a, **k)
        m.compute_pair_fraction = f

    # --------------------------------------------------- input validation

    elif MUT in _M13:
        api, predicate = MUT.removeprefix("M13_").removesuffix("_validation").split("_convention_")
        def wrap(o):
            @functools.wraps(o)
            def f(mp, ms, convention, config, *a, **k):
                if ((predicate == "nonstring" and not isinstance(convention, str))
                        or (predicate == "unsupported" and isinstance(convention, str)
                            and convention not in _CONVENTIONS)):
                    convention = "primary"
                return o(mp, ms, convention, config, *a, **k)
            return f
        if api == "count_pairs":
            m.count_pairs_per_mass_bin = wrap(m.count_pairs_per_mass_bin)
        else:
            m.count_excluded_pairs = wrap(m.count_excluded_pairs)

    elif MUT in _M14:
        api = MUT.removeprefix("M14_").removesuffix("_mass_order_validation")
        def wrap(o):
            @functools.wraps(o)
            def f(mp, ms, convention, config, *a, **k):
                try:
                    a1 = np.asarray(mp, dtype=float)
                    a2 = np.asarray(ms, dtype=float)
                except Exception:
                    return o(mp, ms, convention, config, *a, **k)
                if a1.shape == a2.shape and a1.ndim == 1 and np.any(a2 > a1):
                    hi = np.maximum(a1, a2)
                    lo = np.minimum(a1, a2)
                    return o(hi, lo, convention, config, *a, **k)
                return o(mp, ms, convention, config, *a, **k)
            return f
        if api == "count_pairs":
            m.count_pairs_per_mass_bin = wrap(m.count_pairs_per_mass_bin)
        else:
            m.count_excluded_pairs = wrap(m.count_excluded_pairs)

    elif MUT in _M15:
        suffix = MUT.removeprefix("M15_").removesuffix("_validation")
        api = "count_pairs" if suffix.startswith("count_pairs_") else "count_excluded"
        predicate = suffix.removeprefix(f"{api}_")
        def wrap(o):
            @functools.wraps(o)
            def f(mp, ms, convention, config, *a, **k):
                try:
                    a1 = np.asarray(mp)
                    a2 = np.asarray(ms)
                except Exception:
                    return o(mp, ms, convention, config, *a, **k)
                target = ((predicate == "primary_rank" and a1.ndim != 1)
                          or (predicate == "secondary_rank" and a1.ndim == 1 and a2.ndim != 1)
                          or (predicate == "shape" and a1.ndim == a2.ndim == 1
                              and a1.shape != a2.shape))
                if target:
                    hi, lo = _safe_pair_args(mp, ms)
                    return o(hi, lo, convention, config, *a, **k)
                return o(mp, ms, convention, config, *a, **k)
            return f
        if api == "count_pairs":
            m.count_pairs_per_mass_bin = wrap(m.count_pairs_per_mass_bin)
        else:
            m.count_excluded_pairs = wrap(m.count_excluded_pairs)

    elif MUT in _M16:
        target = MUT.removeprefix("M16_").removesuffix("_nonfinite_validation")
        def _clean(value, replacement):
            arr = np.asarray(value)
            if (arr.ndim != 1 or not np.issubdtype(arr.dtype, np.number)
                    or np.iscomplexobj(arr)):
                return value
            farr = arr.astype(float)
            if np.all(np.isfinite(farr)):
                return value
            return np.nan_to_num(farr, nan=replacement, posinf=replacement,
                                 neginf=replacement)

        def wrap_pair(o, argument):
            @functools.wraps(o)
            def f(mp, ms, convention, config, *a, **k):
                if argument == "primary":
                    # Keep the frozen primary >= secondary invariant after
                    # removing only the selected non-finite rejection.
                    mp = _clean(mp, 1e30)
                else:
                    ms = _clean(ms, -1e30)
                return o(mp, ms, convention, config, *a, **k)
            return f

        def wrap_gal(o):
            @functools.wraps(o)
            def f(mass, config, *a, **k):
                mass = _clean(mass, 0.0)
                return o(mass, config, *a, **k)
            return f

        if target == "count_galaxies":
            m.count_galaxies_per_mass_bin = wrap_gal(m.count_galaxies_per_mass_bin)
        elif target.startswith("count_pairs"):
            m.count_pairs_per_mass_bin = wrap_pair(m.count_pairs_per_mass_bin,
                                                    target.removeprefix("count_pairs_"))
        else:
            m.count_excluded_pairs = wrap_pair(m.count_excluded_pairs,
                                                target.removeprefix("count_excluded_"))

    elif MUT == "M17_excluded_zero":
        o = m.count_excluded_pairs

        @functools.wraps(o)
        def f(*a, **k):
            o(*a, **k)
            return 0
        m.count_excluded_pairs = f

    elif MUT == "M18_excluded_either_is_primary":
        o = m.count_excluded_pairs

        @functools.wraps(o)
        def f(mp, ms, convention, config, *a, **k):
            if convention == "either":
                convention = "primary"
            return o(mp, ms, convention, config, *a, **k)
        m.count_excluded_pairs = f

    # ------------------------------------------------- additivity check

    elif MUT == "M19_additivity_always_true":
        o = m.check_additivity

        @functools.wraps(o)
        def f(*a, **k):
            o(*a, **k)
            return True
        m.check_additivity = f

    elif MUT in _M20:
        o = m.check_additivity
        suffix = MUT.removeprefix("M20_additivity_").removesuffix("_validation")
        if suffix == "shape":
            argument = predicate = None
        else:
            argument, predicate = suffix.rsplit("_", 1)

        @functools.wraps(o)
        def f(n_primary, n_secondary, n_either, *a, **k):
            values = {"n_primary": n_primary, "n_secondary": n_secondary, "n_either": n_either}
            if predicate is None:
                active = (all(_valid_count_vector(value) for value in values.values())
                          and len({_array(value).shape for value in values.values()}) != 1)
            else:
                others = [value for name, value in values.items() if name != argument]
                if predicate == "rank":
                    # A rank defect necessarily has a different shape; do
                    # not require the valid sibling vectors to share it.
                    active = (_predicate(values[argument], predicate)
                              and all(_valid_count_vector(value) for value in others))
                else:
                    active = (_predicate(values[argument], predicate)
                              and all(_valid_count_vector(value)
                                      and _array(value).shape == _array(values[argument]).shape
                                      for value in others))
            if active:
                arrays = [_safe_vector(value) for value in values.values()]
                size = max(len(value) for value in arrays)
                arrays = [_resized(value, size) for value in arrays]
                return o(*arrays, *a, **k)
            return o(n_primary, n_secondary, n_either, *a, **k)
        m.check_additivity = f

    # ------------------------------------------------------- the driver

    elif MUT == "M21_write_before_preflight":
        if hasattr(m, "run_binning_comparison"):
            o = m.run_binning_comparison

            @functools.wraps(o)
            def f(config, *a, **k):
                os.makedirs(config["results_dir"], exist_ok=True)
                with open(_output_path(config), "wb") as fh:
                    fh.write(b"CLOBBERED")
                return o(config, *a, **k)
            m.run_binning_comparison = f

    elif MUT in _M22:
        kind = MUT.removeprefix("M22_driver_").removesuffix("_rejected")

        def _convention_issue(config, predicate):
            values = config.get("pair_binning_conventions")
            if values is None:
                return False
            if predicate == "wrong_container":
                return not isinstance(values, (list, tuple))
            if not isinstance(values, (list, tuple)):
                return False
            if predicate == "empty":
                return not values
            if not values:
                return False
            if predicate == "nonstring":
                return any(not isinstance(value, str) for value in values)
            if any(not isinstance(value, str) for value in values):
                return False
            if predicate == "unsupported":
                return any(value not in _CONVENTIONS for value in values)
            if any(value not in _CONVENTIONS for value in values):
                return False
            if predicate == "duplicate":
                return len(set(values)) != len(values)
            raise ValueError(f"unknown convention predicate: {predicate}")

        def _driver_issue(config):
            if not _driver_config_ready(config):
                return False
            issues = set()
            for predicate in ("wrong_container", "empty", "duplicate", "unsupported", "nonstring"):
                if _convention_issue(config, predicate):
                    issues.add(f"conventions_{predicate}")
            for z in config["redshifts"]:
                data_exists = os.path.isfile(_data_path(z, config))
                results_exists = os.path.isfile(_pairs_path(z, config))
                if not data_exists:
                    issues.add("data_file_missing")
                elif not results_exists:
                    issues.add("results_file_missing")
                else:
                    for attr in ("redshift", "mass_ratio_min", "max_sep_kpc"):
                        state = _attr_state(z, config, attr)
                        if state != "valid":
                            issues.add(f"provenance_{attr}_{state}")
            # A mutation may bypass exactly its selected preflight defect;
            # any simultaneous defect must remain visible to the original.
            return issues == {kind}

        if hasattr(m, "run_binning_comparison"):
            o = m.run_binning_comparison

            @functools.wraps(o)
            def f(config, *a, **k):
                try:
                    return o(config, *a, **k)
                except AssertionError:
                    if _driver_issue(config):
                        return []
                    raise
            m.run_binning_comparison = f

    elif MUT == "M23_use_stored_mass_bin":
        if hasattr(m, "load_snapshot_counts"):
            o = m.load_snapshot_counts

            @functools.wraps(o)
            def f(z, config, *a, **k):
                res = o(z, config, *a, **k)
                if not isinstance(res, dict) or "n_pairs" not in res:
                    return res
                import h5py
                with h5py.File(_pairs_path(z, config), "r") as fh:
                    stored = np.asarray(fh["mass_bin"][...])
                _, n = _edges_and_nbins(config)
                counts = _counts([stored], n)
                res = dict(res)
                res["n_pairs"] = {c: counts.copy() for c in res["n_pairs"]}
                return res
            m.load_snapshot_counts = f

    elif MUT in _M24:
        dataset = MUT.removeprefix("M24_reverse_persisted_").removesuffix("_mass_bins")
        if hasattr(m, "run_binning_comparison"):
            o = m.run_binning_comparison

            @functools.wraps(o)
            def f(config, *a, **k):
                result = o(config, *a, **k)
                import h5py
                with h5py.File(_output_path(config), "r+") as fh:
                    fh[dataset][...] = fh[dataset][...][..., ::-1]
                return result
            m.run_binning_comparison = f

    elif MUT in _M25:
        dataset = MUT.removeprefix("M25_reverse_persisted_").removesuffix("_conventions")
        if hasattr(m, "run_binning_comparison"):
            o = m.run_binning_comparison

            @functools.wraps(o)
            def f(config, *a, **k):
                result = o(config, *a, **k)
                import h5py
                with h5py.File(_output_path(config), "r+") as fh:
                    if fh[dataset].ndim == 3:
                        fh[dataset][...] = fh[dataset][...][:, ::-1, :]
                    else:
                        fh[dataset][...] = fh[dataset][...][:, ::-1]
                return result
            m.run_binning_comparison = f

    elif MUT in _M26:
        attr = MUT.removeprefix("M26_corrupt_output_").removesuffix("_provenance")
        if hasattr(m, "run_binning_comparison"):
            o = m.run_binning_comparison

            @functools.wraps(o)
            def f(config, *a, **k):
                result = o(config, *a, **k)
                import h5py
                with h5py.File(_output_path(config), "r+") as fh:
                    fh.attrs[attr] = -999.0
                return result
            m.run_binning_comparison = f

    elif MUT in _M27:
        attr = MUT.removeprefix("M27_").removesuffix("_attr_always_true")
        if hasattr(m, "run_binning_comparison"):
            o = m.run_binning_comparison

            @functools.wraps(o)
            def f(config, *a, **k):
                result = o(config, *a, **k)
                import h5py
                with h5py.File(_output_path(config), "r+") as fh:
                    fh.attrs[attr] = True
                return result
            m.run_binning_comparison = f

    elif MUT in _M28:
        field = MUT.removeprefix("M28_console_omits_")
        if hasattr(m, "run_binning_comparison"):
            o = m.run_binning_comparison

            @functools.wraps(o)
            def f(config, *a, **k):
                import contextlib
                import io
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    result = o(config, *a, **k)
                text = output.getvalue()
                if field == "heading":
                    text = re.sub(
                        r"N_gal\(b\)\s+is\s+the\s+same\s+galaxy\s+count\s+for\s+every\s+convention;\s+only\s+the\s+numerator\s+changes\.\s*",
                        "", text, count=1)
                elif field == "additivity":
                    text = re.sub(r"\badditivity=[^\s]+", "", text)
                else:
                    text = re.sub(rf"\b{re.escape(field)}=[^\s]+", "", text)
                print(text, end="")
                return result
            m.run_binning_comparison = f

    elif MUT == "M29_ignore_conventions_config":
        if hasattr(m, "run_binning_comparison"):
            o = m.run_binning_comparison

            @functools.wraps(o)
            def f(config, *a, **k):
                c = dict(config)
                c["pair_binning_conventions"] = list(_CONVENTIONS)
                return o(c, *a, **k)
            m.run_binning_comparison = f

    elif MUT == "M30_extra_result_key":
        if hasattr(m, "run_binning_comparison"):
            o = m.run_binning_comparison

            @functools.wraps(o)
            def f(config, *a, **k):
                result = o(config, *a, **k)
                for item in result:
                    if isinstance(item, dict):
                        item["note"] = "unspecified extra key"
                return result
            m.run_binning_comparison = f

    # ------------------------------------------------ config, not defaults

    elif MUT in _M31:
        # Every binning function silently uses the *default* mass grid instead
        # of the configured one. A no-op under config.py's shipped defaults, so
        # only a suite that varies log_mass_min / log_mass_max / mass_bin_width
        # can see it -- which is exactly the coverage this mutation measures.
        key = MUT.removeprefix("M31_").removesuffix("_ignores_config")
        _DEFAULT_GRID = {"log_mass_min": 8.0, "log_mass_max": 11.0,
                         "mass_bin_width": 0.5}

        def _forced(config):
            forced = dict(config)
            forced[key] = _DEFAULT_GRID[key]
            return forced

        if "_mass_bin_edges" in m.__dict__:
            o_edges = m._mass_bin_edges

            @functools.wraps(o_edges)
            def f_edges(config, *a, **k):
                return o_edges(_forced(config), *a, **k)
            m._mass_bin_edges = f_edges

        o_gal = m.count_galaxies_per_mass_bin

        @functools.wraps(o_gal)
        def f_gal(mass, config, *a, **k):
            return o_gal(mass, _forced(config), *a, **k)
        m.count_galaxies_per_mass_bin = f_gal

        def wrap_grid(o):
            @functools.wraps(o)
            def f(mp, ms, convention, config, *a, **k):
                return o(mp, ms, convention, _forced(config), *a, **k)
            return f
        m.count_pairs_per_mass_bin = wrap_grid(m.count_pairs_per_mass_bin)
        if "count_excluded_pairs" in m.__dict__:
            m.count_excluded_pairs = wrap_grid(m.count_excluded_pairs)

    # --------------------------------------------- driver honesty checks

    elif MUT == "M32_additivity_forced_false":
        # Forces check_additivity to report False on every call, regardless
        # of the real identity (which -- per spec.md section 7 -- always
        # holds on valid data). If run_binning_comparison genuinely derives
        # additivity_holds from this function's return value, the persisted
        # attr and every returned dict's additivity_holds flip to False; if
        # the driver instead hardcodes success without truly consulting
        # check_additivity, nothing observable changes and this mutation
        # survives -- exactly the gap this mutation targets.
        o = m.check_additivity

        @functools.wraps(o)
        def f(*a, **k):
            o(*a, **k)  # preserve the real function's own validation/rejections
            return False
        m.check_additivity = f

    elif MUT == "M33_pairfrac_wrong_divisor":
        # Corrupts the pair-fraction formula's denominator (off-by-one,
        # N_gal + 1 instead of N_gal) while preserving the original
        # function's validation/rejection behaviour by calling it first.
        o = m.compute_pair_fraction

        @functools.wraps(o)
        def f(npair, ngal, *a, **k):
            fp, sg = o(npair, ngal, *a, **k)
            p = np.asarray(npair, dtype=float)
            g = np.asarray(ngal, dtype=float)
            with np.errstate(all="ignore"):
                fp2 = np.where(g >= 0, p / (g + 1.0), 0.0)
            return fp2, sg
        m.compute_pair_fraction = f

    elif MUT in _M34:
        suffix = MUT.removeprefix("M34_provenance_").removesuffix("_validation_disabled")
        attr, predicate = suffix.rsplit("_", 1)
        o = m.load_snapshot_counts

        @functools.wraps(o)
        def f(z, config, *a, **k):
            try:
                return o(z, config, *a, **k)
            except AssertionError:
                if (not _driver_config_ready(config)
                        or not all(key in config for key in
                                   ("mass_ratio_min", "max_sep"))
                        or not os.path.isfile(_pairs_path(z, config))
                        or not _only_provenance_issue(z, config, attr, predicate)
                        or not _conventions_valid(config)):
                    raise
            # This replacement executes only after the selected assertion; it
            # preserves every unrelated rejection and uses public task APIs.
            import h5py
            if not os.path.isfile(_pairs_path(z, config)):
                raise AssertionError("pair results file is missing")
            if not os.path.isfile(_data_path(z, config)):
                raise AssertionError("galaxy catalog file is missing")
            with h5py.File(_pairs_path(z, config), "r") as fh:
                if "mass_primary" not in fh or "mass_secondary" not in fh:
                    raise AssertionError("pair mass datasets are required")
                primary = fh["mass_primary"][...]
                secondary = fh["mass_secondary"][...]
            if (primary.ndim != 1 or secondary.ndim != 1
                    or primary.shape != secondary.shape):
                raise AssertionError("pair mass datasets must be matching 1D arrays")
            # Resolve the frozen reader by package, rather than assuming a
            # submission re-exports it from pair_binning.  Both bare modules
            # and ``src.``-qualified imports are supported.
            package = m.__dict__.get("__package__", "")
            reader_name = f"{package}.data_reader" if package else "data_reader"
            reader = sys.modules.get(reader_name) or sys.modules.get("data_reader")
            if reader is None:
                reader = importlib.import_module(reader_name)
            catalog = reader.load_galaxy_catalog(_data_path(z, config), config)
            conventions = tuple(config["pair_binning_conventions"])
            return {
                "redshift": float(z),
                "n_galaxies": m.count_galaxies_per_mass_bin(
                    catalog["log_stellar_mass"], config),
                "n_pairs": {convention: m.count_pairs_per_mass_bin(
                    primary, secondary, convention, config) for convention in conventions},
                "n_excluded_pairs": {convention: m.count_excluded_pairs(
                    primary, secondary, convention, config) for convention in conventions},
                "n_pairs_total": len(primary),
            }
        m.load_snapshot_counts = f


_orig_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__
_orig_import_module = importlib.import_module
_orig_reload = importlib.reload

# Re-entrancy guard. _patch_* imports numpy, and some stdlib modules (e.g.
# importlib.machinery) implement a module-level __getattr__ that imports on
# attribute access. Without this guard, and with `getattr(mod, ...)` used to
# probe modules, the hook re-enters itself once per probe and recurses until
# the interpreter pins a core at 100% and never returns -- which is what a
# hung mutation looks like from the outside. Two defences, both required:
# this flag, and probing `mod.__dict__` (a real slot, never routed through a
# module __getattr__) instead of getattr/hasattr. The leaf-name test runs
# first so the common case touches no module attributes at all. Shared by
# all three hooks below -- none may scan while another already is.
_BUSY = False


def _scan_and_patch():
    global _BUSY
    if _BUSY:
        return
    _BUSY = True
    try:
        for fullname, mod in tuple(sys.modules.items()):
            if mod is None or fullname.rsplit(".", 1)[-1] != "pair_binning":
                continue
            namespace = mod.__dict__
            if namespace.get("__MUTATED__"):
                continue
            if "count_pairs_per_mass_bin" not in namespace:
                continue
            namespace["__MUTATED__"] = True
            try:
                _patch_pair_binning(mod)
            except Exception:
                namespace["__MUTATED__"] = False
                raise
    finally:
        _BUSY = False


def _imp(name, *a, **k):
    m = _orig_import(name, *a, **k)
    _scan_and_patch()
    return m


def _import_module(name, package=None):
    # importlib.import_module does not route through builtins.__import__.
    m = _orig_import_module(name, package)
    _scan_and_patch()
    return m


def _reload(module):
    # Reload re-executes the module body: __MUTATED__ survives in the same
    # namespace even though the functions are back to unwrapped, so clear it
    # before the scan can re-patch.
    m = _orig_reload(module)
    name = getattr(m, "__name__", "")
    if name.rsplit(".", 1)[-1] == "pair_binning":
        m.__dict__["__MUTATED__"] = False
    _scan_and_patch()
    return m


if MUT:
    if isinstance(__builtins__, dict):
        __builtins__["__import__"] = _imp
    else:
        __builtins__.__import__ = _imp
    importlib.import_module = _import_module
    importlib.reload = _reload
