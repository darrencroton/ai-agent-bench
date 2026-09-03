"""Injects one behavioural mutation into merger_rate/calc after import.

Used to test whether the Developer's OWN test suite can actually FAIL --
the test_adequacy rubric category. Selected by the MUTATION environment
variable. Works by monkey-patching the already-imported module's public
functions post-import, so it operates identically regardless of how the
Developer structured their implementation internally, and no trial file is
ever edited.

Activated by putting this file's directory on PYTHONPATH (Python auto-
imports any sitecustomize.py found on sys.path at interpreter startup) and
setting MUTATION=<id> before running the trial's own pytest.

Ported near-verbatim from the mutation gate used to produce the original
14-run model-eval report this task's spec.md and hidden tests are drawn
from; see docs/DESIGN.md for provenance.
"""
import functools
import importlib
import os
import sys

MUT = os.environ.get("MUTATION")


def _patch_merger_rate(m):
    import numpy as np

    if MUT == "M1_sigma_no_sqrt":
        o = m.compute_pair_fraction
        @functools.wraps(o)
        def f(*a, **k):
            fp, sg = o(*a, **k)
            fp = np.asarray(fp, dtype=float)
            npair = np.asarray(a[0], dtype=float)
            sg = np.where(npair > 0, fp / np.where(npair > 0, npair, 1.0), 0.0)
            return fp, sg
        m.compute_pair_fraction = f

    elif MUT == "M2_timescale_sign":
        o = m.merger_timescale_gyr
        @functools.wraps(o)
        def f(z, config, *a, **k):
            c = dict(config); c["merger_timescale_alpha"] = -config["merger_timescale_alpha"]
            return o(z, c, *a, **k)
        m.merger_timescale_gyr = f

    elif MUT == "M3_box_squared":
        o = m.compute_merger_rate
        @functools.wraps(o)
        def f(fp, sf, ng, box, tg, mf, *a, **k):
            r, s = o(fp, sf, ng, box, tg, mf, *a, **k)
            return np.asarray(r) * float(box), np.asarray(s) * float(box)
        m.compute_merger_rate = f

    elif MUT == "M4_config_box":
        if hasattr(m, "_load_pair_counts"):
            o = m._load_pair_counts
            @functools.wraps(o)
            def f(z, config, *a, **k):
                res = o(z, config, *a, **k)
                try:
                    npair, ngal, box = res
                except Exception:
                    return res
                return npair, ngal, float(config["box_size"])
            m._load_pair_counts = f

    elif MUT == "M5_slope_err_x2":
        o = m.fit_log_rate_vs_redshift
        @functools.wraps(o)
        def f(*a, **k):
            s, se, ic, nx = o(*a, **k)
            return s, se * 2.0, ic, nx
        m.fit_log_rate_vs_redshift = f

    elif MUT == "M6_consistency_bad_err":
        o = m.check_slope_consistency
        @functools.wraps(o)
        def f(slope, slope_err, expected, n_sigma=3.0, *a, **k):
            try:
                if float(slope_err) <= 0.0:
                    return True
            except Exception:
                pass
            return o(slope, slope_err, expected, n_sigma, *a, **k)
        m.check_slope_consistency = f

    elif MUT == "M7_fabricate_fit":
        o = m.fit_log_rate_vs_redshift
        @functools.wraps(o)
        def f(*a, **k):
            s, se, ic, nx = o(*a, **k)
            if not np.isfinite(s):
                return 0.0, 1.0, 0.0, nx
            return s, se, ic, nx
        m.fit_log_rate_vs_redshift = f

    elif MUT == "M8a_pairfrac_shape_validation":
        o = m.compute_pair_fraction
        @functools.wraps(o)
        def f(npair, ngal, *a, **k):
            p = np.asarray(npair)
            g = np.asarray(ngal)
            if p.ndim != 1 or g.ndim != 1 or p.shape != g.shape:
                npair = np.atleast_1d(np.asarray(npair, dtype=float)).ravel()
                ngal = np.atleast_1d(np.asarray(ngal, dtype=float)).ravel()
                n = max(len(npair), len(ngal))
                npair = np.resize(npair, n); ngal = np.resize(ngal, n)
                with np.errstate(all="ignore"):
                    fp = np.where(ngal > 0, npair / np.where(ngal > 0, ngal, 1.0), 0.0)
                    sg = np.where(npair > 0, fp / np.sqrt(np.abs(npair)), 0.0)
                return np.nan_to_num(fp), np.nan_to_num(sg)
            return o(npair, ngal, *a, **k)
        m.compute_pair_fraction = f

    elif MUT == "M8b_pairfrac_count_value_validation":
        o = m.compute_pair_fraction
        @functools.wraps(o)
        def f(npair, ngal, *a, **k):
            p = np.asarray(npair)
            g = np.asarray(ngal)
            if p.ndim == g.ndim == 1 and p.shape == g.shape:
                try:
                    pf = p.astype(float); gf = g.astype(float)
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
                        sg = np.where(pf > 0, fp / np.sqrt(pf), 0.0)
                    return fp, sg
            return o(npair, ngal, *a, **k)
        m.compute_pair_fraction = f

    elif MUT == "M8c_pairfrac_zero_denominator_validation":
        o = m.compute_pair_fraction
        @functools.wraps(o)
        def f(npair, ngal, *a, **k):
            p = np.asarray(npair, dtype=float)
            g = np.asarray(ngal, dtype=float)
            if p.ndim == g.ndim == 1 and p.shape == g.shape and np.any((p > 0) & (g == 0)):
                with np.errstate(all="ignore"):
                    fp = np.where(g > 0, p / g, 0.0)
                    sg = np.where(p > 0, fp / np.sqrt(p), 0.0)
                return fp, sg
            return o(npair, ngal, *a, **k)
        m.compute_pair_fraction = f

    elif MUT == "M9a_timescale_z_form_validation":
        o = m.merger_timescale_gyr
        @functools.wraps(o)
        def f(z, config, *a, **k):
            invalid_form = (isinstance(z, (str, bytes, bool, complex, np.ndarray))
                            or isinstance(z, np.bool_))
            if invalid_form:
                z = float(np.real(np.asarray(z, dtype=complex).ravel()[0]))
            return o(z, config, *a, **k)
        m.merger_timescale_gyr = f

    elif MUT == "M9b_timescale_z_value_validation":
        o = m.merger_timescale_gyr
        @functools.wraps(o)
        def f(z, config, *a, **k):
            if np.isscalar(z) and not isinstance(z, (str, bytes, complex)):
                try:
                    zf = float(z)
                    if not np.isfinite(zf) or zf <= -1:
                        z = 0.0
                except Exception:
                    pass
            return o(z, config, *a, **k)
        m.merger_timescale_gyr = f

    elif MUT == "M9c_timescale_config_form_validation":
        o = m.merger_timescale_gyr
        @functools.wraps(o)
        def f(z, config, *a, **k):
            c = dict(config)
            for key in ("merger_timescale_gyr0", "merger_timescale_alpha"):
                val = c[key]
                if isinstance(val, (str, bytes, bool, complex, np.ndarray, np.bool_)):
                    c[key] = float(np.real(np.asarray(val, dtype=complex).ravel()[0]))
            return o(z, c, *a, **k)
        m.merger_timescale_gyr = f

    elif MUT == "M9d_timescale_config_value_validation":
        o = m.merger_timescale_gyr
        @functools.wraps(o)
        def f(z, config, *a, **k):
            c = dict(config)
            g0 = float(c["merger_timescale_gyr0"])
            alpha = float(c["merger_timescale_alpha"])
            if not np.isfinite(g0) or g0 <= 0:
                c["merger_timescale_gyr0"] = 2.2
            if not np.isfinite(alpha):
                c["merger_timescale_alpha"] = -1.0
            return o(z, c, *a, **k)
        m.merger_timescale_gyr = f

    elif MUT == "M10a_rate_array_shape_validation":
        o = m.compute_merger_rate
        @functools.wraps(o)
        def f(fp, sf, ng, box, tg, mf, *a, **k):
            arrays = [np.asarray(v) for v in (fp, sf, ng)]
            if any(v.ndim != 1 for v in arrays) or len({v.shape for v in arrays}) != 1:
                fp = np.atleast_1d(np.asarray(fp, dtype=float)).ravel()
                sf = np.atleast_1d(np.asarray(sf, dtype=float)).ravel()
                ng = np.atleast_1d(np.asarray(ng, dtype=float)).ravel()
                n = max(len(fp), len(sf), len(ng))
                fp, sf, ng = np.resize(fp, n), np.resize(sf, n), np.resize(ng, n)
                denom = float(box) ** 3 * float(tg)
                return float(mf) * fp * ng / denom, float(mf) * sf * ng / denom
            return o(fp, sf, ng, box, tg, mf, *a, **k)
        m.compute_merger_rate = f

    elif MUT == "M10b_rate_array_value_validation":
        o = m.compute_merger_rate
        @functools.wraps(o)
        def f(fp, sf, ng, box, tg, mf, *a, **k):
            arrays = [np.asarray(v) for v in (fp, sf, ng)]
            if all(v.ndim == 1 for v in arrays) and len({v.shape for v in arrays}) == 1:
                vals = [v.astype(float) for v in arrays]
                invalid = (any(not np.all(np.isfinite(v)) for v in vals)
                           or any(np.any(v < 0) for v in vals)
                           or np.any(vals[2] != np.round(vals[2])))
                if invalid:
                    fp2 = np.abs(np.nan_to_num(vals[0], nan=0.0, posinf=0.0, neginf=0.0))
                    sf2 = np.abs(np.nan_to_num(vals[1], nan=0.0, posinf=0.0, neginf=0.0))
                    ng2 = np.round(np.abs(np.nan_to_num(vals[2], nan=1.0, posinf=1.0, neginf=1.0)))
                    ng2 = np.where((ng2 == 0) & ((fp2 != 0) | (sf2 != 0)), 1.0, ng2)
                    denom = float(box) ** 3 * float(tg)
                    return float(mf) * fp2 * ng2 / denom, float(mf) * sf2 * ng2 / denom
            return o(fp, sf, ng, box, tg, mf, *a, **k)
        m.compute_merger_rate = f

    elif MUT == "M10c_rate_scalar_form_validation":
        o = m.compute_merger_rate
        @functools.wraps(o)
        def f(fp, sf, ng, box, tg, mf, *a, **k):
            vals = [box, tg, mf]
            if any(isinstance(v, (str, bytes, bool, complex, np.ndarray, np.bool_)) for v in vals):
                box, tg, mf = [float(np.real(np.asarray(v, dtype=complex).ravel()[0])) for v in vals]
            return o(fp, sf, ng, box, tg, mf, *a, **k)
        m.compute_merger_rate = f

    elif MUT == "M10d_rate_scalar_value_validation":
        o = m.compute_merger_rate
        @functools.wraps(o)
        def f(fp, sf, ng, box, tg, mf, *a, **k):
            boxf, tgf, mff = float(box), float(tg), float(mf)
            if not np.isfinite(boxf) or boxf <= 0:
                box = 500.0
            if not np.isfinite(tgf) or tgf <= 0:
                tg = 2.2
            if not np.isfinite(mff) or not 0 < mff <= 1:
                mf = 0.6
            return o(fp, sf, ng, box, tg, mf, *a, **k)
        m.compute_merger_rate = f

    elif MUT == "M10e_rate_zero_galaxy_validation":
        o = m.compute_merger_rate
        @functools.wraps(o)
        def f(fp, sf, ng, box, tg, mf, *a, **k):
            fpv = np.asarray(fp); sfv = np.asarray(sf); ngv = np.asarray(ng)
            if fpv.shape == sfv.shape == ngv.shape and np.any((ngv == 0) & ((fpv != 0) | (sfv != 0))):
                ngv = np.where((ngv == 0) & ((fpv != 0) | (sfv != 0)), 1, ngv)
                return o(fp, sf, ngv, box, tg, mf, *a, **k)
            return o(fp, sf, ng, box, tg, mf, *a, **k)
        m.compute_merger_rate = f

    elif MUT == "M11_fit_no_weights":
        o = m.fit_log_rate_vs_redshift
        @functools.wraps(o)
        def f(rates, errs, zs, *a, **k):
            e = np.asarray(errs, dtype=float)
            flat = np.where(np.isfinite(e) & (e > 0), 1.0, e)
            return o(rates, flat, zs, *a, **k)
        m.fit_log_rate_vs_redshift = f

    elif MUT == "M13_write_before_preflight":
        if hasattr(m, "run_merger_rate_calculation"):
            o = m.run_merger_rate_calculation
            @functools.wraps(o)
            def f(config, *a, **k):
                try:
                    os.makedirs(config["results_dir"], exist_ok=True)
                    with open(os.path.join(config["results_dir"], "merger_rate.hdf5"), "wb") as fh:
                        fh.write(b"CLOBBERED")
                except Exception:
                    pass
                return o(config, *a, **k)
            m.run_merger_rate_calculation = f

    elif MUT == "M14_sentinel_counted":
        if hasattr(m, "_load_pair_counts"):
            o = m._load_pair_counts
            @functools.wraps(o)
            def f(z, config, *a, **k):
                res = o(z, config, *a, **k)
                try:
                    npair, ngal, box = res
                except Exception:
                    return res
                try:
                    import h5py
                    with h5py.File(m._results_path(z, config), "r") as fh:
                        mb = fh["mass_bin"][...]
                    extra = int(np.sum(np.asarray(mb) == -1))
                except Exception:
                    extra = 0
                npair = np.asarray(npair).copy()
                if extra and len(npair):
                    npair[0] = npair[0] + extra
                return npair, ngal, box
            m._load_pair_counts = f

    elif MUT == "M17_hardcode_alpha":
        o = m.merger_timescale_gyr
        @functools.wraps(o)
        def f(z, config, *a, **k):
            c = dict(config); c["merger_timescale_alpha"] = -1.0
            return o(z, c, *a, **k)
        m.merger_timescale_gyr = f

    elif MUT == "M18_hardcode_expected_slope":
        if hasattr(m, "run_merger_rate_validation"):
            o = m.run_merger_rate_validation
            @functools.wraps(o)
            def f(config, *a, **k):
                c = dict(config); c["merger_timescale_alpha"] = -1.0
                return o(c, *a, **k)
            m.run_merger_rate_validation = f

    elif MUT == "M20_n_excluded_zero":
        o = m.fit_log_rate_vs_redshift
        @functools.wraps(o)
        def f(*a, **k):
            s, se, ic, nx = o(*a, **k)
            return s, se, ic, 0
        m.fit_log_rate_vs_redshift = f

    elif MUT == "M23_zero_zero_nan":
        o = m.compute_pair_fraction
        @functools.wraps(o)
        def f(npair, ngal, *a, **k):
            fp, sg = o(npair, ngal, *a, **k)
            fp = np.asarray(fp, dtype=float).copy(); sg = np.asarray(sg, dtype=float).copy()
            p = np.asarray(npair, dtype=float).ravel(); g = np.asarray(ngal, dtype=float).ravel()
            mask = (p == 0) & (g == 0)
            if mask.shape == fp.shape:
                fp[mask] = np.nan; sg[mask] = np.nan
            return fp, sg
        m.compute_pair_fraction = f

    elif MUT == "M25_reverse_persisted_mass_bins":
        o = m.run_merger_rate_calculation
        @functools.wraps(o)
        def f(config, *a, **k):
            result = o(config, *a, **k)
            import h5py
            path = os.path.join(config["results_dir"], "merger_rate.hdf5")
            with h5py.File(path, "r+") as fh:
                for name in ("pair_fraction", "n_pairs", "merger_rate", "merger_rate_err"):
                    data = fh[name][...]
                    fh[name][...] = data[:, ::-1]
            return result
        m.run_merger_rate_calculation = f

    elif MUT == "M26_corrupt_output_provenance":
        o = m.run_merger_rate_calculation
        @functools.wraps(o)
        def f(config, *a, **k):
            result = o(config, *a, **k)
            import h5py
            path = os.path.join(config["results_dir"], "merger_rate.hdf5")
            with h5py.File(path, "r+") as fh:
                fh.attrs["merger_fraction"] = -999.0
                fh.attrs["merger_timescale_alpha"] = 999.0
            return result
        m.run_merger_rate_calculation = f

    elif MUT == "M27_drop_validation_redshift_preflight":
        o = m.run_merger_rate_validation
        @functools.wraps(o)
        def f(config, *a, **k):
            try:
                return o(config, *a, **k)
            except AssertionError:
                import h5py
                path = os.path.join(config["results_dir"], "merger_rate.hdf5")
                with h5py.File(path, "r") as fh:
                    redshifts = np.asarray(fh.attrs["redshifts"])
                try:
                    values = redshifts.astype(float)
                    malformed = np.any(~np.isfinite(values)) or np.any(values <= -1)
                except (TypeError, ValueError):
                    malformed = True
                if malformed:
                    return []
                raise
        m.run_merger_rate_validation = f

    elif MUT == "M28_omit_console_fields":
        o = m.run_merger_rate_validation
        @functools.wraps(o)
        def f(config, *a, **k):
            import contextlib
            import io
            with contextlib.redirect_stdout(io.StringIO()):
                result = o(config, *a, **k)
            print("Merger-rate validation summary")
            for item in result:
                print(f"  bin {item['mass_bin']}: {item['consistent']}")
            return result
        m.run_merger_rate_validation = f

    elif MUT == "M29_uncentred_y_cross_term":
        o = m.fit_log_rate_vs_redshift
        @functools.wraps(o)
        def f(rates, errs, zs, *a, **k):
            slope, slope_err, intercept, n_excluded = o(rates, errs, zs, *a, **k)
            if not np.isfinite(slope):
                return slope, slope_err, intercept, n_excluded
            rates = np.asarray(rates, dtype=float)
            errs = np.asarray(errs, dtype=float)
            zs = np.asarray(zs, dtype=float)
            usable = np.isfinite(rates) & (rates > 0) & np.isfinite(errs) & (errs > 0)
            x = np.log10(1.0 + zs[usable])
            y = np.log10(rates[usable])
            sigma = errs[usable] / (rates[usable] * np.log(10.0))
            weights = 1.0 / sigma ** 2
            weights = weights / np.max(weights)
            x_mean = np.sum(weights * x) / np.sum(weights)
            y_mean = np.sum(weights * y) / np.sum(weights)
            xc = x - x_mean
            s_xx = np.sum(weights * xc * xc)
            bad_slope = np.sum(weights * xc * y) / s_xx
            bad_intercept = y_mean - bad_slope * x_mean
            return float(bad_slope), slope_err, float(bad_intercept), n_excluded
        m.fit_log_rate_vs_redshift = f


def _patch_calc(m):
    import numpy as np

    if MUT == "M21_count_float_dtype":
        o = m._count_galaxies_per_mass_bin
        @functools.wraps(o)
        def f(*a, **k):
            return np.asarray(o(*a, **k), dtype=float)
        m._count_galaxies_per_mass_bin = f

    if MUT == "M12_count_includes_upper_edge":
        o = m._count_galaxies_per_mass_bin
        @functools.wraps(o)
        def f(mass, config, *a, **k):
            out = np.asarray(o(mass, config, *a, **k)).copy()
            mass = np.asarray(mass, dtype=float)
            extra = int(np.sum(mass == float(config["log_mass_max"])))
            if extra and len(out):
                out[-1] += extra
            return out
        m._count_galaxies_per_mass_bin = f

    if MUT == "M24_count_from_pair_rows":
        o = m.run_calculation
        @functools.wraps(o)
        def f(config, *a, **k):
            result = o(config, *a, **k)
            import h5py
            for z in config["redshifts"]:
                path = m._results_path(z, config)
                with h5py.File(path, "r+") as fh:
                    mass_bin = fh["mass_bin"][...]
                    counts = np.array(
                        [np.sum(mass_bin == b)
                         for b in range(len(fh["n_galaxies_per_mass_bin"]))],
                        dtype=np.int64)
                    fh["n_galaxies_per_mass_bin"][...] = counts
            return result
        m.run_calculation = f


def _is_target(fullname, mod):
    if mod is None:
        return False
    leaf = str(fullname).rsplit(".", 1)[-1]
    return ((leaf == "merger_rate" and hasattr(mod, "compute_pair_fraction")) or
            (leaf == "calc" and hasattr(mod, "_count_galaxies_per_mass_bin")))


def _patch_candidate(fullname, mod):
    try:
        if not _is_target(fullname, mod) or getattr(mod, "__MUTATED__", False):
            return
        leaf = str(fullname).rsplit(".", 1)[-1]
        mod.__MUTATED__ = True
        try:
            _patch_merger_rate(mod) if leaf == "merger_rate" else _patch_calc(mod)
        except Exception:
            mod.__MUTATED__ = False
            raise
    except Exception:
        pass


def _patch_all(candidates):
    seen = set()
    for fullname, mod in candidates:
        if mod is None or id(mod) in seen:
            continue
        seen.add(id(mod))
        _patch_candidate(fullname, mod)


_orig_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__
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
    # importlib.import_module does not route through builtins.__import__.
    m = _orig_import_module(name, package)
    candidates = [(getattr(m, "__name__", name), m)]
    if not str(name).startswith("."):
        candidates.append((name, sys.modules.get(name)))
    _patch_all(candidates)
    return m


def _reload(module):
    # Reload re-executes the module body: __MUTATED__ survives in the same
    # namespace even though the functions are back to unwrapped.
    m = _orig_reload(module)
    name = getattr(m, "__name__", "")
    if not _is_target(name, m):
        return m
    try:
        m.__MUTATED__ = False
    except Exception:
        return m
    _patch_all([(name, m)])
    return m


if MUT:
    if isinstance(__builtins__, dict):
        __builtins__["__import__"] = _imp
    else:
        __builtins__.__import__ = _imp
    importlib.import_module = _import_module
    importlib.reload = _reload
