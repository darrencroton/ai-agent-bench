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
import os, sys, functools

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

    elif MUT == "M8_drop_pairfrac_validation":
        o = m.compute_pair_fraction
        @functools.wraps(o)
        def f(npair, ngal, *a, **k):
            try:
                return o(npair, ngal, *a, **k)
            except AssertionError:
                npair = np.atleast_1d(np.asarray(npair, dtype=float)).ravel()
                ngal = np.atleast_1d(np.asarray(ngal, dtype=float)).ravel()
                n = max(len(npair), len(ngal))
                npair = np.resize(npair, n); ngal = np.resize(ngal, n)
                with np.errstate(all="ignore"):
                    fp = np.where(ngal > 0, npair / np.where(ngal > 0, ngal, 1.0), 0.0)
                    sg = np.where(npair > 0, fp / np.sqrt(np.abs(npair)), 0.0)
                return np.nan_to_num(fp), np.nan_to_num(sg)
        m.compute_pair_fraction = f

    elif MUT == "M9_drop_timescale_validation":
        o = m.merger_timescale_gyr
        @functools.wraps(o)
        def f(z, config, *a, **k):
            try:
                return o(z, config, *a, **k)
            except AssertionError:
                import numpy as _np
                with _np.errstate(all="ignore"):
                    return float(config["merger_timescale_gyr0"]) * \
                        (1.0 + float(_np.real(_np.asarray(z, dtype=complex).ravel()[0]))) ** \
                        float(config["merger_timescale_alpha"])
        m.merger_timescale_gyr = f

    elif MUT == "M10_drop_rate_validation":
        o = m.compute_merger_rate
        @functools.wraps(o)
        def f(fp, sf, ng, box, tg, mf, *a, **k):
            try:
                return o(fp, sf, ng, box, tg, mf, *a, **k)
            except AssertionError:
                fp = np.atleast_1d(np.asarray(fp, dtype=float)).ravel()
                sf = np.atleast_1d(np.asarray(sf, dtype=float)).ravel()
                ng = np.atleast_1d(np.asarray(ng, dtype=float)).ravel()
                n = max(len(fp), len(sf), len(ng))
                fp, sf, ng = np.resize(fp, n), np.resize(sf, n), np.resize(ng, n)
                with np.errstate(all="ignore"):
                    r = float(mf) * fp * ng / (float(np.real(complex(box if not isinstance(box, str) else float(box)))) ** 3 * float(tg))
                    s = float(mf) * sf * ng / (float(np.real(complex(box if not isinstance(box, str) else float(box)))) ** 3 * float(tg))
                return np.nan_to_num(r), np.nan_to_num(s)
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


_orig_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__


def _imp(name, *a, **k):
    m = _orig_import(name, *a, **k)
    try:
        mod = sys.modules.get(name)
        if mod is not None and not getattr(mod, "__MUTATED__", False):
            if name == "merger_rate" and hasattr(mod, "compute_pair_fraction"):
                _patch_merger_rate(mod); mod.__MUTATED__ = True
            elif name == "calc" and hasattr(mod, "_count_galaxies_per_mass_bin"):
                _patch_calc(mod); mod.__MUTATED__ = True
    except Exception:
        pass
    return m


if MUT:
    if isinstance(__builtins__, dict):
        __builtins__["__import__"] = _imp
    else:
        __builtins__.__import__ = _imp
