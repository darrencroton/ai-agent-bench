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
import os
import sys

MUT = os.environ.get("MUTATION")

_CONVENTIONS = ("primary", "secondary", "either")
_OUTPUT_NAME = "pair_binning.hdf5"


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


def _patch_pair_binning(m):  # noqa: C901 -- one flat branch per mutation, by design
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
                try:
                    import h5py
                    with h5py.File(_pairs_path(z, config), "r") as fh:
                        mp = fh["mass_primary"][...]
                        ms = fh["mass_secondary"][...]
                    bp, n = _bins(mp, config)
                    bs, _ = _bins(ms, config)
                except Exception:
                    return res
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

    elif MUT == "M09_zero_zero_nan":
        o = m.compute_pair_fraction

        @functools.wraps(o)
        def f(npair, ngal, *a, **k):
            fp, sg = o(npair, ngal, *a, **k)
            fp = np.asarray(fp, dtype=float).copy()
            sg = np.asarray(sg, dtype=float).copy()
            p = np.asarray(npair, dtype=float).ravel()
            g = np.asarray(ngal, dtype=float).ravel()
            mask = (p == 0) & (g == 0)
            if mask.shape == fp.shape:
                fp[mask] = np.nan
                sg[mask] = np.nan
            return fp, sg
        m.compute_pair_fraction = f

    elif MUT == "M10_pairfrac_shape_validation":
        o = m.compute_pair_fraction

        @functools.wraps(o)
        def f(npair, ngal, *a, **k):
            p = np.asarray(npair)
            g = np.asarray(ngal)
            if p.ndim != 1 or g.ndim != 1 or p.shape != g.shape:
                p = np.atleast_1d(np.asarray(npair, dtype=float)).ravel()
                g = np.atleast_1d(np.asarray(ngal, dtype=float)).ravel()
                n = max(len(p), len(g))
                p, g = np.resize(p, n), np.resize(g, n)
                with np.errstate(all="ignore"):
                    fp = np.where(g > 0, p / np.where(g > 0, g, 1.0), 0.0)
                    sg = np.where(p > 0, fp / np.sqrt(np.abs(np.where(p > 0, p, 1.0))), 0.0)
                return np.nan_to_num(fp), np.nan_to_num(sg)
            return o(npair, ngal, *a, **k)
        m.compute_pair_fraction = f

    elif MUT == "M11_pairfrac_value_validation":
        o = m.compute_pair_fraction

        @functools.wraps(o)
        def f(npair, ngal, *a, **k):
            p = np.asarray(npair)
            g = np.asarray(ngal)
            if p.ndim == g.ndim == 1 and p.shape == g.shape:
                try:
                    pf = p.astype(float)
                    gf = g.astype(float)
                    invalid = (not np.all(np.isfinite(pf)) or not np.all(np.isfinite(gf))
                               or np.any(pf < 0) or np.any(gf < 0)
                               or np.any(pf != np.round(pf)) or np.any(gf != np.round(gf)))
                except Exception:
                    pf = np.zeros(p.shape, dtype=float)
                    gf = np.ones(g.shape, dtype=float)
                    invalid = True
                if invalid:
                    pf = np.round(np.abs(np.nan_to_num(pf, nan=0.0, posinf=0.0, neginf=0.0)))
                    gf = np.round(np.abs(np.nan_to_num(gf, nan=1.0, posinf=1.0, neginf=1.0)))
                    gf = np.where((pf > 0) & (gf == 0), 1.0, gf)
                    with np.errstate(all="ignore"):
                        fp = np.where(gf > 0, pf / gf, 0.0)
                        sg = np.where(pf > 0, fp / np.sqrt(np.where(pf > 0, pf, 1.0)), 0.0)
                    return fp, sg
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

    elif MUT == "M13_convention_validation":
        def wrap(o):
            @functools.wraps(o)
            def f(mp, ms, convention, config, *a, **k):
                if not isinstance(convention, str) or convention not in _CONVENTIONS:
                    convention = "primary"
                return o(mp, ms, convention, config, *a, **k)
            return f
        m.count_pairs_per_mass_bin = wrap(m.count_pairs_per_mass_bin)
        if hasattr(m, "count_excluded_pairs"):
            m.count_excluded_pairs = wrap(m.count_excluded_pairs)

    elif MUT == "M14_mass_order_validation":
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
        m.count_pairs_per_mass_bin = wrap(m.count_pairs_per_mass_bin)
        if hasattr(m, "count_excluded_pairs"):
            m.count_excluded_pairs = wrap(m.count_excluded_pairs)

    elif MUT == "M15_pair_shape_validation":
        def wrap(o):
            @functools.wraps(o)
            def f(mp, ms, convention, config, *a, **k):
                try:
                    a1 = np.asarray(mp)
                    a2 = np.asarray(ms)
                except Exception:
                    return o(mp, ms, convention, config, *a, **k)
                if a1.ndim != 1 or a2.ndim != 1 or a1.shape != a2.shape:
                    try:
                        f1 = np.atleast_1d(np.asarray(mp, dtype=float)).ravel()
                        f2 = np.atleast_1d(np.asarray(ms, dtype=float)).ravel()
                    except Exception:
                        return o(mp, ms, convention, config, *a, **k)
                    n = max(len(f1), len(f2), 1)
                    f1, f2 = np.resize(f1, n), np.resize(f2, n)
                    hi, lo = np.maximum(f1, f2), np.minimum(f1, f2)
                    return o(hi, lo, convention, config, *a, **k)
                return o(mp, ms, convention, config, *a, **k)
            return f
        m.count_pairs_per_mass_bin = wrap(m.count_pairs_per_mass_bin)
        if hasattr(m, "count_excluded_pairs"):
            m.count_excluded_pairs = wrap(m.count_excluded_pairs)

    elif MUT == "M16_nonfinite_mass_validation":
        def _clean(value):
            arr = np.asarray(value, dtype=float)
            if np.all(np.isfinite(arr)):
                return value
            return np.nan_to_num(arr, nan=0.0, posinf=1e30, neginf=-1e30)

        def wrap_pair(o):
            @functools.wraps(o)
            def f(mp, ms, convention, config, *a, **k):
                try:
                    mp, ms = _clean(mp), _clean(ms)
                except Exception:
                    pass
                return o(mp, ms, convention, config, *a, **k)
            return f

        def wrap_gal(o):
            @functools.wraps(o)
            def f(mass, config, *a, **k):
                try:
                    mass = _clean(mass)
                except Exception:
                    pass
                return o(mass, config, *a, **k)
            return f

        m.count_galaxies_per_mass_bin = wrap_gal(m.count_galaxies_per_mass_bin)
        m.count_pairs_per_mass_bin = wrap_pair(m.count_pairs_per_mass_bin)
        if hasattr(m, "count_excluded_pairs"):
            m.count_excluded_pairs = wrap_pair(m.count_excluded_pairs)

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

    elif MUT == "M20_additivity_validation":
        o = m.check_additivity

        @functools.wraps(o)
        def f(*a, **k):
            try:
                return o(*a, **k)
            except AssertionError:
                try:
                    arrays = [np.atleast_1d(np.asarray(v, dtype=float)).ravel() for v in a[:3]]
                except Exception:
                    return False
                n = max(len(v) for v in arrays)
                arrays = [np.nan_to_num(np.resize(v, n)) for v in arrays]
                return bool(np.all(arrays[0] + arrays[1] == arrays[2]))
        m.check_additivity = f

    # ------------------------------------------------------- the driver

    elif MUT == "M21_write_before_preflight":
        if hasattr(m, "run_binning_comparison"):
            o = m.run_binning_comparison

            @functools.wraps(o)
            def f(config, *a, **k):
                try:
                    os.makedirs(config["results_dir"], exist_ok=True)
                    with open(_output_path(config), "wb") as fh:
                        fh.write(b"CLOBBERED")
                except Exception:
                    pass
                return o(config, *a, **k)
            m.run_binning_comparison = f

    elif MUT == "M22_drop_validation_gate":
        if hasattr(m, "run_binning_comparison"):
            o = m.run_binning_comparison

            @functools.wraps(o)
            def f(config, *a, **k):
                try:
                    return o(config, *a, **k)
                except AssertionError:
                    return []
            m.run_binning_comparison = f

    elif MUT == "M23_use_stored_mass_bin":
        if hasattr(m, "load_snapshot_counts"):
            o = m.load_snapshot_counts

            @functools.wraps(o)
            def f(z, config, *a, **k):
                res = o(z, config, *a, **k)
                if not isinstance(res, dict) or "n_pairs" not in res:
                    return res
                try:
                    import h5py
                    with h5py.File(_pairs_path(z, config), "r") as fh:
                        stored = np.asarray(fh["mass_bin"][...])
                    _, n = _edges_and_nbins(config)
                    counts = _counts([stored], n)
                except Exception:
                    return res
                res = dict(res)
                res["n_pairs"] = {c: counts.copy() for c in res["n_pairs"]}
                return res
            m.load_snapshot_counts = f

    elif MUT == "M24_reverse_persisted_mass_bins":
        if hasattr(m, "run_binning_comparison"):
            o = m.run_binning_comparison

            @functools.wraps(o)
            def f(config, *a, **k):
                result = o(config, *a, **k)
                import h5py
                with h5py.File(_output_path(config), "r+") as fh:
                    for name in ("n_galaxies", "n_pairs", "pair_fraction", "pair_fraction_err"):
                        if name in fh:
                            fh[name][...] = fh[name][...][..., ::-1]
                return result
            m.run_binning_comparison = f

    elif MUT == "M25_reverse_persisted_conventions":
        if hasattr(m, "run_binning_comparison"):
            o = m.run_binning_comparison

            @functools.wraps(o)
            def f(config, *a, **k):
                result = o(config, *a, **k)
                import h5py
                with h5py.File(_output_path(config), "r+") as fh:
                    for name in ("n_pairs", "pair_fraction", "pair_fraction_err"):
                        if name in fh and fh[name].ndim == 3:
                            fh[name][...] = fh[name][...][:, ::-1, :]
                    if "n_excluded_pairs" in fh and fh["n_excluded_pairs"].ndim == 2:
                        fh["n_excluded_pairs"][...] = fh["n_excluded_pairs"][...][:, ::-1]
                return result
            m.run_binning_comparison = f

    elif MUT == "M26_corrupt_output_provenance":
        if hasattr(m, "run_binning_comparison"):
            o = m.run_binning_comparison

            @functools.wraps(o)
            def f(config, *a, **k):
                result = o(config, *a, **k)
                import h5py
                with h5py.File(_output_path(config), "r+") as fh:
                    fh.attrs["mass_ratio_min"] = -999.0
                    fh.attrs["max_sep_kpc"] = -999.0
                return result
            m.run_binning_comparison = f

    elif MUT == "M27_additivity_attr_always_true":
        if hasattr(m, "run_binning_comparison"):
            o = m.run_binning_comparison

            @functools.wraps(o)
            def f(config, *a, **k):
                result = o(config, *a, **k)
                import h5py
                with h5py.File(_output_path(config), "r+") as fh:
                    fh.attrs["additivity_checked"] = True
                    fh.attrs["additivity_holds"] = True
                return result
            m.run_binning_comparison = f

    elif MUT == "M28_console_omits_fields":
        if hasattr(m, "run_binning_comparison"):
            o = m.run_binning_comparison

            @functools.wraps(o)
            def f(config, *a, **k):
                import contextlib
                import io
                with contextlib.redirect_stdout(io.StringIO()):
                    result = o(config, *a, **k)
                print("Pair-binning convention comparison")
                for item in result:
                    print(f"  redshift {item['redshift']}")
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

    elif MUT == "M31_bin_grid_ignores_config":
        # Every binning function silently uses the *default* mass grid instead
        # of the configured one. A no-op under config.py's shipped defaults, so
        # only a suite that varies log_mass_min / log_mass_max / mass_bin_width
        # can see it -- which is exactly the coverage this mutation measures.
        _DEFAULT_GRID = {"log_mass_min": 8.0, "log_mass_max": 11.0,
                         "mass_bin_width": 0.5}

        def _forced(config):
            try:
                forced = dict(config)
            except Exception:
                return config
            forced.update(_DEFAULT_GRID)
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

    elif MUT == "M34_provenance_validation_disabled":
        # Simulates a no-op per-attribute provenance check: whenever
        # load_snapshot_counts would reject on validation (missing/malformed
        # redshift, mass_ratio_min or max_sep_kpc attrs -- or any other
        # AssertionError), silently answer anyway from whatever is on disk
        # instead of rejecting a pair sample cut under different settings
        # than the configured ones.
        if hasattr(m, "load_snapshot_counts"):
            o = m.load_snapshot_counts

            @functools.wraps(o)
            def f(z, config, *a, **k):
                try:
                    return o(z, config, *a, **k)
                except AssertionError:
                    pass
                conventions = tuple(config.get("pair_binning_conventions", _CONVENTIONS))
                try:
                    import h5py
                    with h5py.File(_pairs_path(z, config), "r") as fh:
                        mp = np.asarray(fh["mass_primary"][...], dtype=float)
                        ms = np.asarray(fh["mass_secondary"][...], dtype=float)
                except Exception:
                    mp = ms = np.array([], dtype=float)
                bp, n = _bins(mp, config)
                bs, _ = _bins(ms, config)
                n_pairs, n_excluded = {}, {}
                for c in conventions:
                    if c == "primary":
                        sel = (bp,)
                    elif c == "secondary":
                        sel = (bs,)
                    else:
                        sel = (bp, bs)
                    n_pairs[c] = _counts(sel, n)
                    excl = (sel[0] == -1) if len(sel) == 1 else ((sel[0] == -1) & (sel[1] == -1))
                    n_excluded[c] = int(np.count_nonzero(excl))
                try:
                    import h5py
                    with h5py.File(_data_path(z, config), "r") as fh:
                        gal = np.asarray(fh["log_stellar_mass"][...], dtype=float)
                    mask = (gal >= config["log_mass_min"]) & (gal <= config["log_mass_max"])
                    gb, _ = _bins(gal[mask], config)
                    n_gal = _counts([gb], n)
                except Exception:
                    n_gal = np.zeros(n, dtype=np.int64)
                return {
                    "redshift": float(z),
                    "n_galaxies": n_gal,
                    "n_pairs": n_pairs,
                    "n_excluded_pairs": n_excluded,
                    "n_pairs_total": len(mp),
                }
            m.load_snapshot_counts = f


_orig_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__

# Re-entrancy guard. _patch_* imports numpy, and some stdlib modules (e.g.
# importlib.machinery) implement a module-level __getattr__ that imports on
# attribute access. Without this guard, and with `getattr(mod, ...)` used to
# probe modules, the hook re-enters itself once per probe and recurses until
# the interpreter pins a core at 100% and never returns -- which is what a
# hung mutation looks like from the outside. Two defences, both required:
# this flag, and probing `mod.__dict__` (a real slot, never routed through a
# module __getattr__) instead of getattr/hasattr. The leaf-name test runs
# first so the common case touches no module attributes at all.
_BUSY = False


def _imp(name, *a, **k):
    global _BUSY
    m = _orig_import(name, *a, **k)
    if _BUSY:
        return m
    _BUSY = True
    try:
        for fullname, mod in tuple(sys.modules.items()):
            if mod is None or fullname.rsplit(".", 1)[-1] != "pair_binning":
                continue
            try:
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
            except Exception:
                pass
    finally:
        _BUSY = False
    return m


if MUT:
    if isinstance(__builtins__, dict):
        __builtins__["__import__"] = _imp
    else:
        __builtins__.__import__ = _imp
