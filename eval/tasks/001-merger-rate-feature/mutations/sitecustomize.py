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

`mutation_list.txt` is generated from `MUTATION_REGISTRY`, never maintained
as a separate inventory:

    cd eval/tasks/001-merger-rate-feature/mutations
    PYTHONPATH=. ../../../../venv/bin/python -c "import sitecustomize as s; \
        print('\\n'.join(s.all_mutation_ids()))" > mutation_list.txt

Mutation transforms and patch installation fail loudly. A broken transform is
an invalid mutation, never evidence that a submission's tests survived it.
"""
import functools
import importlib
import os
import sys

MUT = os.environ.get("MUTATION")

# The mutation-list generator reads this registry rather than maintaining a
# second, hand-written inventory. Keep ids in the stable rubric order.
MUTATION_REGISTRY = {
    name: None for name in (
        "M1_sigma_no_sqrt", "M2_timescale_sign", "M3_box_squared", "M4_config_box",
        "M5_slope_err_x2", "M6_consistency_bad_err", "M7_fabricate_fit",
        "M8a_pairfrac_n_pairs_rank_validation", "M8b_pairfrac_n_galaxies_rank_validation",
        "M8c_pairfrac_shape_equality_validation", "M8d_pairfrac_n_pairs_finite_validation",
        "M8e_pairfrac_n_pairs_nonnegative_validation", "M8f_pairfrac_n_pairs_integer_validation",
        "M8g_pairfrac_n_galaxies_finite_validation", "M8h_pairfrac_n_galaxies_nonnegative_validation",
        "M8i_pairfrac_n_galaxies_integer_validation", "M8j_pairfrac_zero_denominator_validation",
        "M9a_timescale_z_form_validation", "M9b_timescale_z_finite_validation",
        "M9c_timescale_z_lower_bound_validation", "M9d_timescale_gyr0_form_validation",
        "M9e_timescale_alpha_form_validation", "M9f_timescale_gyr0_finite_validation",
        "M9g_timescale_gyr0_positive_validation", "M9h_timescale_alpha_finite_validation",
        "M10a_rate_f_pair_rank_validation", "M10b_rate_sigma_f_pair_rank_validation",
        "M10c_rate_n_galaxies_rank_validation", "M10d_rate_array_shape_equality_validation",
        "M10e_rate_f_pair_finite_validation", "M10f_rate_f_pair_nonnegative_validation",
        "M10g_rate_sigma_f_pair_finite_validation", "M10h_rate_sigma_f_pair_nonnegative_validation",
        "M10i_rate_n_galaxies_finite_validation", "M10j_rate_n_galaxies_nonnegative_validation",
        "M10k_rate_n_galaxies_integer_validation", "M10l_rate_box_size_form_validation",
        "M10m_rate_timescale_form_validation", "M10n_rate_merger_fraction_form_validation",
        "M10o_rate_box_size_finite_validation", "M10p_rate_box_size_positive_validation",
        "M10q_rate_timescale_finite_validation", "M10r_rate_timescale_positive_validation",
        "M10s_rate_merger_fraction_finite_validation", "M10t_rate_merger_fraction_positive_validation",
        "M10u_rate_merger_fraction_upper_bound_validation", "M10v_rate_zero_galaxy_validation",
        "M11_fit_no_weights", "M12_count_includes_upper_edge", "M13_write_before_preflight",
        "M14_sentinel_counted", "M17_hardcode_alpha", "M18_hardcode_expected_slope",
        "M20_n_excluded_zero", "M21_count_float_dtype", "M23_zero_zero_nan",
        "M24_count_from_pair_rows", "M25a_reverse_pair_fraction_mass_bins",
        "M25b_reverse_n_pairs_mass_bins", "M25c_reverse_merger_rate_mass_bins",
        "M25d_reverse_merger_rate_err_mass_bins", "M26a_corrupt_merger_fraction_provenance",
        "M26b_corrupt_merger_timescale_alpha_provenance",
        "M27a_drop_validation_stored_redshift_finite_preflight",
        "M27b_drop_validation_stored_redshift_lower_bound_preflight",
        "M28a_omit_console_heading", "M28b_omit_console_mass_range",
        "M28c_omit_console_slope", "M28d_omit_console_slope_uncertainty",
        "M28e_omit_console_expected_slope", "M28f_omit_console_n_excluded",
        "M28g_omit_console_status", "M29_uncentred_y_cross_term",
    )
}


def all_mutation_ids():
    """Return the deterministic mutation-gate inventory."""
    return tuple(MUTATION_REGISTRY)


def _is_accepted_real_scalar(value):
    """Match the task's scalar contract before a value mutation coerces it."""
    import numpy as np
    return (not isinstance(value, (bool, np.bool_, np.ndarray))
            and isinstance(value, (int, float, np.integer, np.floating)))


def _real_numeric_1d(value):
    """Return a numeric real 1-D array, or None for a rejected array form."""
    import numpy as np
    array = np.asarray(value)
    if array.ndim != 1 or array.dtype.kind not in "iuf":
        return None
    return array.astype(float)


def _real_numeric_array(value):
    import numpy as np
    array = np.asarray(value)
    return array if array.dtype.kind in "iuf" else None


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

    elif MUT == "M8a_pairfrac_n_pairs_rank_validation":
        o = m.compute_pair_fraction
        @functools.wraps(o)
        def f(npair, ngal, *a, **k):
            p = np.asarray(npair)
            g = np.asarray(ngal)
            if (_real_numeric_array(p) is not None and _real_numeric_1d(g) is not None
                    and p.ndim != 1 and g.ndim == 1):
                npair = np.resize(np.asarray(npair, dtype=float).ravel(), g.size)
                with np.errstate(all="ignore"):
                    fp = np.where(ngal > 0, npair / np.where(ngal > 0, ngal, 1.0), 0.0)
                    sg = np.where(npair > 0, fp / np.sqrt(np.abs(npair)), 0.0)
                return np.nan_to_num(fp), np.nan_to_num(sg)
            return o(npair, ngal, *a, **k)
        m.compute_pair_fraction = f

    elif MUT == "M8b_pairfrac_n_galaxies_rank_validation":
        o = m.compute_pair_fraction
        @functools.wraps(o)
        def f(npair, ngal, *a, **k):
            p = np.asarray(npair)
            g = np.asarray(ngal)
            if (_real_numeric_1d(p) is not None and _real_numeric_array(g) is not None
                    and g.ndim != 1 and p.ndim == 1):
                ngal = np.resize(np.asarray(ngal, dtype=float).ravel(), p.size)
                with np.errstate(all="ignore"):
                    fp = np.where(ngal > 0, npair / np.where(ngal > 0, ngal, 1.0), 0.0)
                    sg = np.where(npair > 0, fp / np.sqrt(np.abs(npair)), 0.0)
                return np.nan_to_num(fp), np.nan_to_num(sg)
            return o(npair, ngal, *a, **k)
        m.compute_pair_fraction = f

    elif MUT == "M8c_pairfrac_shape_equality_validation":
        o = m.compute_pair_fraction
        @functools.wraps(o)
        def f(npair, ngal, *a, **k):
            p = np.asarray(npair)
            g = np.asarray(ngal)
            if (_real_numeric_1d(p) is not None and _real_numeric_1d(g) is not None
                    and p.shape != g.shape):
                npair = np.resize(np.asarray(npair, dtype=float), g.size)
                with np.errstate(all="ignore"):
                    fp = np.where(g > 0, npair / np.where(g > 0, g, 1.0), 0.0)
                    sg = np.where(npair > 0, fp / np.sqrt(np.abs(npair)), 0.0)
                return np.nan_to_num(fp), np.nan_to_num(sg)
            return o(npair, ngal, *a, **k)
        m.compute_pair_fraction = f

    elif MUT in {
            "M8d_pairfrac_n_pairs_finite_validation",
            "M8e_pairfrac_n_pairs_nonnegative_validation",
            "M8f_pairfrac_n_pairs_integer_validation",
            "M8g_pairfrac_n_galaxies_finite_validation",
            "M8h_pairfrac_n_galaxies_nonnegative_validation",
            "M8i_pairfrac_n_galaxies_integer_validation"}:
        o = m.compute_pair_fraction
        @functools.wraps(o)
        def f(npair, ngal, *a, **k):
            p = np.asarray(npair)
            g = np.asarray(ngal)
            pf = _real_numeric_1d(p)
            gf = _real_numeric_1d(g)
            if pf is not None and gf is not None and p.shape == g.shape:
                try:
                    checks = {
                        "M8d_pairfrac_n_pairs_finite_validation": not np.all(np.isfinite(pf)),
                        "M8e_pairfrac_n_pairs_nonnegative_validation": np.any(pf < 0),
                        "M8f_pairfrac_n_pairs_integer_validation": np.any(pf != np.round(pf)),
                        "M8g_pairfrac_n_galaxies_finite_validation": not np.all(np.isfinite(gf)),
                        "M8h_pairfrac_n_galaxies_nonnegative_validation": np.any(gf < 0),
                        "M8i_pairfrac_n_galaxies_integer_validation": np.any(gf != np.round(gf)),
                    }
                    invalid = checks[MUT]
                except (TypeError, ValueError):
                    return o(npair, ngal, *a, **k)
                if invalid:
                    if MUT.startswith(("M8d", "M8e", "M8f")):
                        pf = np.round(np.abs(np.nan_to_num(pf, nan=0.0, posinf=0.0, neginf=0.0)))
                    else:
                        gf = np.round(np.abs(np.nan_to_num(gf, nan=1.0, posinf=1.0, neginf=1.0)))
                    with np.errstate(all="ignore"):
                        fp = np.where(gf > 0, pf / gf, 0.0)
                        sg = np.where(pf > 0, fp / np.sqrt(pf), 0.0)
                    return fp, sg
            return o(npair, ngal, *a, **k)
        m.compute_pair_fraction = f

    elif MUT == "M8j_pairfrac_zero_denominator_validation":
        o = m.compute_pair_fraction
        @functools.wraps(o)
        def f(npair, ngal, *a, **k):
            p = _real_numeric_1d(npair)
            g = _real_numeric_1d(ngal)
            if p is not None and g is not None and p.shape == g.shape and np.any((p > 0) & (g == 0)):
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

    elif MUT == "M9b_timescale_z_finite_validation":
        o = m.merger_timescale_gyr
        @functools.wraps(o)
        def f(z, config, *a, **k):
            if _is_accepted_real_scalar(z) and not np.isfinite(float(z)):
                z = 0.0
            return o(z, config, *a, **k)
        m.merger_timescale_gyr = f

    elif MUT == "M9c_timescale_z_lower_bound_validation":
        o = m.merger_timescale_gyr
        @functools.wraps(o)
        def f(z, config, *a, **k):
            if _is_accepted_real_scalar(z) and float(z) <= -1:
                z = 0.0
            return o(z, config, *a, **k)
        m.merger_timescale_gyr = f

    elif MUT in {"M9d_timescale_gyr0_form_validation",
                 "M9e_timescale_alpha_form_validation"}:
        o = m.merger_timescale_gyr
        @functools.wraps(o)
        def f(z, config, *a, **k):
            key = "merger_timescale_gyr0" if MUT.startswith("M9d") else "merger_timescale_alpha"
            if (not isinstance(config, dict)
                    or "merger_timescale_gyr0" not in config
                    or "merger_timescale_alpha" not in config):
                return o(z, config, *a, **k)
            val = config[key]
            if not isinstance(val, (str, bytes, bool, complex, np.ndarray, np.bool_)):
                return o(z, config, *a, **k)
            coerced = float(np.real(np.asarray(val, dtype=complex).ravel()[0]))
            c = dict(config)
            c[key] = coerced
            return o(z, c, *a, **k)
        m.merger_timescale_gyr = f

    elif MUT in {"M9f_timescale_gyr0_finite_validation",
                 "M9g_timescale_gyr0_positive_validation",
                 "M9h_timescale_alpha_finite_validation"}:
        o = m.merger_timescale_gyr
        @functools.wraps(o)
        def f(z, config, *a, **k):
            if (not isinstance(config, dict)
                    or not _is_accepted_real_scalar(config.get("merger_timescale_gyr0"))
                    or not _is_accepted_real_scalar(config.get("merger_timescale_alpha"))):
                return o(z, config, *a, **k)
            c = dict(config)
            g0 = float(c["merger_timescale_gyr0"])
            alpha = float(c["merger_timescale_alpha"])
            if MUT == "M9f_timescale_gyr0_finite_validation" and not np.isfinite(g0):
                c["merger_timescale_gyr0"] = 2.2
            if MUT == "M9g_timescale_gyr0_positive_validation" and g0 <= 0:
                c["merger_timescale_gyr0"] = 2.2
            if MUT == "M9h_timescale_alpha_finite_validation" and not np.isfinite(alpha):
                c["merger_timescale_alpha"] = -1.0
            return o(z, c, *a, **k)
        m.merger_timescale_gyr = f

    elif MUT in {"M10a_rate_f_pair_rank_validation", "M10b_rate_sigma_f_pair_rank_validation",
                 "M10c_rate_n_galaxies_rank_validation"}:
        o = m.compute_merger_rate
        @functools.wraps(o)
        def f(fp, sf, ng, box, tg, mf, *a, **k):
            arrays = [np.asarray(v) for v in (fp, sf, ng)]
            index = {"M10a_rate_f_pair_rank_validation": 0,
                     "M10b_rate_sigma_f_pair_rank_validation": 1,
                     "M10c_rate_n_galaxies_rank_validation": 2}[MUT]
            others = [v for i, v in enumerate(arrays) if i != index]
            if (_real_numeric_array(arrays[index]) is not None
                    and all(_real_numeric_1d(v) is not None for v in others)
                    and others[0].shape == others[1].shape and arrays[index].ndim != 1):
                arrays[index] = np.resize(arrays[index].astype(float).ravel(), others[0].size)
                fp, sf, ng = arrays
                denom = float(box) ** 3 * float(tg)
                return float(mf) * fp * ng / denom, float(mf) * sf * ng / denom
            return o(fp, sf, ng, box, tg, mf, *a, **k)
        m.compute_merger_rate = f

    elif MUT == "M10d_rate_array_shape_equality_validation":
        o = m.compute_merger_rate
        @functools.wraps(o)
        def f(fp, sf, ng, box, tg, mf, *a, **k):
            arrays = [np.asarray(v) for v in (fp, sf, ng)]
            if (all(_real_numeric_1d(v) is not None for v in arrays)
                    and len({v.shape for v in arrays}) != 1):
                arrays = [np.resize(v.astype(float), max(v.size for v in arrays)) for v in arrays]
                fp, sf, ng = arrays
                denom = float(box) ** 3 * float(tg)
                return float(mf) * fp * ng / denom, float(mf) * sf * ng / denom
            return o(fp, sf, ng, box, tg, mf, *a, **k)
        m.compute_merger_rate = f

    elif MUT in {"M10e_rate_f_pair_finite_validation", "M10f_rate_f_pair_nonnegative_validation",
                 "M10g_rate_sigma_f_pair_finite_validation", "M10h_rate_sigma_f_pair_nonnegative_validation",
                 "M10i_rate_n_galaxies_finite_validation", "M10j_rate_n_galaxies_nonnegative_validation",
                 "M10k_rate_n_galaxies_integer_validation"}:
        o = m.compute_merger_rate
        @functools.wraps(o)
        def f(fp, sf, ng, box, tg, mf, *a, **k):
            arrays = [np.asarray(v) for v in (fp, sf, ng)]
            vals = [_real_numeric_1d(v) for v in arrays]
            if all(v is not None for v in vals) and len({v.shape for v in vals}) == 1:
                checks = {
                    "M10e_rate_f_pair_finite_validation": not np.all(np.isfinite(vals[0])),
                    "M10f_rate_f_pair_nonnegative_validation": np.any(vals[0] < 0),
                    "M10g_rate_sigma_f_pair_finite_validation": not np.all(np.isfinite(vals[1])),
                    "M10h_rate_sigma_f_pair_nonnegative_validation": np.any(vals[1] < 0),
                    "M10i_rate_n_galaxies_finite_validation": not np.all(np.isfinite(vals[2])),
                    "M10j_rate_n_galaxies_nonnegative_validation": np.any(vals[2] < 0),
                    "M10k_rate_n_galaxies_integer_validation": np.any(vals[2] != np.round(vals[2])),
                }
                invalid = checks[MUT]
                if invalid:
                    fp2, sf2, ng2 = vals
                    if MUT.startswith(("M10e", "M10f")):
                        fp2 = np.abs(np.nan_to_num(fp2, nan=0.0, posinf=0.0, neginf=0.0))
                    elif MUT.startswith(("M10g", "M10h")):
                        sf2 = np.abs(np.nan_to_num(sf2, nan=0.0, posinf=0.0, neginf=0.0))
                    else:
                        ng2 = np.round(np.abs(np.nan_to_num(ng2, nan=0.0, posinf=0.0, neginf=0.0)))
                    denom = float(box) ** 3 * float(tg)
                    return float(mf) * fp2 * ng2 / denom, float(mf) * sf2 * ng2 / denom
            return o(fp, sf, ng, box, tg, mf, *a, **k)
        m.compute_merger_rate = f

    elif MUT in {"M10l_rate_box_size_form_validation", "M10m_rate_timescale_form_validation",
                 "M10n_rate_merger_fraction_form_validation"}:
        o = m.compute_merger_rate
        @functools.wraps(o)
        def f(fp, sf, ng, box, tg, mf, *a, **k):
            vals = [box, tg, mf]
            index = {"M10l_rate_box_size_form_validation": 0,
                     "M10m_rate_timescale_form_validation": 1,
                     "M10n_rate_merger_fraction_form_validation": 2}[MUT]
            if isinstance(vals[index], (str, bytes, bool, complex, np.ndarray, np.bool_)):
                vals[index] = float(np.real(np.asarray(vals[index], dtype=complex).ravel()[0]))
                box, tg, mf = vals
            return o(fp, sf, ng, box, tg, mf, *a, **k)
        m.compute_merger_rate = f

    elif MUT in {"M10o_rate_box_size_finite_validation", "M10p_rate_box_size_positive_validation",
                 "M10q_rate_timescale_finite_validation", "M10r_rate_timescale_positive_validation",
                 "M10s_rate_merger_fraction_finite_validation", "M10t_rate_merger_fraction_positive_validation",
                 "M10u_rate_merger_fraction_upper_bound_validation"}:
        o = m.compute_merger_rate
        @functools.wraps(o)
        def f(fp, sf, ng, box, tg, mf, *a, **k):
            if not all(_is_accepted_real_scalar(value) for value in (box, tg, mf)):
                return o(fp, sf, ng, box, tg, mf, *a, **k)
            boxf, tgf, mff = float(box), float(tg), float(mf)
            if MUT == "M10o_rate_box_size_finite_validation" and not np.isfinite(boxf):
                box = 500.0
            if MUT == "M10p_rate_box_size_positive_validation" and boxf <= 0:
                box = 500.0
            if MUT == "M10q_rate_timescale_finite_validation" and not np.isfinite(tgf):
                tg = 2.2
            if MUT == "M10r_rate_timescale_positive_validation" and tgf <= 0:
                tg = 2.2
            if MUT == "M10s_rate_merger_fraction_finite_validation" and not np.isfinite(mff):
                mf = 0.6
            if MUT == "M10t_rate_merger_fraction_positive_validation" and mff <= 0:
                mf = 0.6
            if MUT == "M10u_rate_merger_fraction_upper_bound_validation" and mff > 1:
                mf = 0.6
            return o(fp, sf, ng, box, tg, mf, *a, **k)
        m.compute_merger_rate = f

    elif MUT == "M10v_rate_zero_galaxy_validation":
        o = m.compute_merger_rate
        @functools.wraps(o)
        def f(fp, sf, ng, box, tg, mf, *a, **k):
            fpv = _real_numeric_1d(fp); sfv = _real_numeric_1d(sf); ngv = _real_numeric_1d(ng)
            if (fpv is not None and sfv is not None and ngv is not None
                    and fpv.shape == sfv.shape == ngv.shape
                    and np.any((ngv == 0) & ((fpv != 0) | (sfv != 0)))):
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

    elif MUT in {"M25a_reverse_pair_fraction_mass_bins",
                 "M25b_reverse_n_pairs_mass_bins",
                 "M25c_reverse_merger_rate_mass_bins",
                 "M25d_reverse_merger_rate_err_mass_bins"}:
        o = m.run_merger_rate_calculation
        @functools.wraps(o)
        def f(config, *a, **k):
            result = o(config, *a, **k)
            import h5py
            path = os.path.join(config["results_dir"], "merger_rate.hdf5")
            with h5py.File(path, "r+") as fh:
                name = {
                    "M25a_reverse_pair_fraction_mass_bins": "pair_fraction",
                    "M25b_reverse_n_pairs_mass_bins": "n_pairs",
                    "M25c_reverse_merger_rate_mass_bins": "merger_rate",
                    "M25d_reverse_merger_rate_err_mass_bins": "merger_rate_err",
                }[MUT]
                data = fh[name][...]
                fh[name][...] = data[:, ::-1]
            return result
        m.run_merger_rate_calculation = f

    elif MUT in {"M26a_corrupt_merger_fraction_provenance",
                 "M26b_corrupt_merger_timescale_alpha_provenance"}:
        o = m.run_merger_rate_calculation
        @functools.wraps(o)
        def f(config, *a, **k):
            result = o(config, *a, **k)
            import h5py
            path = os.path.join(config["results_dir"], "merger_rate.hdf5")
            with h5py.File(path, "r+") as fh:
                name, value = (
                    ("merger_fraction", -999.0)
                    if MUT == "M26a_corrupt_merger_fraction_provenance"
                    else ("merger_timescale_alpha", 999.0)
                )
                fh.attrs[name] = value
            return result
        m.run_merger_rate_calculation = f

    elif MUT in {"M27a_drop_validation_stored_redshift_finite_preflight",
                 "M27b_drop_validation_stored_redshift_lower_bound_preflight"}:
        o = m.run_merger_rate_validation
        @functools.wraps(o)
        def f(config, *a, **k):
            try:
                return o(config, *a, **k)
            except AssertionError:
                # Decide from the stored input, not the implementation's
                # assertion wording: submissions may use any equally valid
                # message. The guards below keep absent artifacts and mixed
                # malformed predicates observable to the original function.
                import h5py
                try:
                    path = os.path.join(config["results_dir"], "merger_rate.hdf5")
                    if not os.path.isfile(path):
                        raise OSError(path)
                    with h5py.File(path, "r") as fh:
                        if "redshifts" not in fh.attrs:
                            raise KeyError("redshifts")
                        if "merger_rate" not in fh or "merger_rate_err" not in fh:
                            raise KeyError("required rate dataset")
                        values = np.atleast_1d(np.asarray(fh.attrs["redshifts"]))
                    if values.dtype.kind not in "iuf":
                        raise TypeError("stored redshifts are not numeric real values")
                except (KeyError, OSError, TypeError, ValueError):
                    values = None
                if values is None:
                    raise
                malformed = (
                    np.any(~np.isfinite(values)) and np.all(values[np.isfinite(values)] > -1)
                    if MUT == "M27a_drop_validation_stored_redshift_finite_preflight"
                    else np.all(np.isfinite(values)) and np.any(values <= -1)
                )
                if malformed:
                    return []
                raise
        m.run_merger_rate_validation = f

    elif MUT in {"M28a_omit_console_heading",
                 "M28b_omit_console_mass_range",
                 "M28c_omit_console_slope",
                 "M28d_omit_console_slope_uncertainty",
                 "M28e_omit_console_expected_slope",
                 "M28f_omit_console_n_excluded",
                 "M28g_omit_console_status"}:
        o = m.run_merger_rate_validation
        @functools.wraps(o)
        def f(config, *a, **k):
            import contextlib
            import io
            import re
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream):
                result = o(config, *a, **k)
            # Mutate the original rendering, never rebuild it: each member of
            # this family removes one reporting obligation and leaves the
            # other six observable to the submission's tests.
            text = stream.getvalue()
            if MUT == "M28a_omit_console_heading":
                text = "\n".join(text.splitlines()[1:]) + "\n"
            elif MUT == "M28b_omit_console_mass_range":
                text = re.sub(r"\s*\[[^\]\n]+\)", "", text)
            elif MUT == "M28c_omit_console_slope":
                text = re.sub(r"(?<![_\w])slope\s*=", "fit=", text)
            elif MUT == "M28d_omit_console_slope_uncertainty":
                text = re.sub(r"\bslope_err\s*=\s*[^\s;]+|(?:\+/-|±)\s*[^\s;]+",
                              "uncertainty omitted", text)
            elif MUT == "M28e_omit_console_expected_slope":
                text = re.sub(r"\bexpected(?:_slope)?\s*=\s*[^\s;]+", "expected omitted", text)
            elif MUT == "M28f_omit_console_n_excluded":
                text = re.sub(r"\bn[_ ]excluded\s*=\s*[^\s;]+", "excluded omitted", text)
            elif MUT == "M28g_omit_console_status":
                text = re.sub(r"\bstatus\s*=\s*[^\s;]+|\b(?:consistent|inconsistent|insufficient\s+data)\b",
                              "result omitted", text)
            print(text, end="")
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
    return leaf in {"merger_rate", "calc"}


def _required_api(leaf):
    """The one public/task-required entry point each mutation wraps.

    A structurally incomplete submission must leave only that mutation
    uninstalled (and therefore survived), never make sitecustomize fail during
    import and accidentally affect every mutation run.
    """
    if leaf == "calc":
        if MUT in {"M12_count_includes_upper_edge", "M21_count_float_dtype"}:
            return "_count_galaxies_per_mass_bin"
        if MUT == "M24_count_from_pair_rows":
            return "run_calculation"
        return None
    if MUT in {"M1_sigma_no_sqrt", "M8a_pairfrac_n_pairs_rank_validation",
               "M8b_pairfrac_n_galaxies_rank_validation", "M8c_pairfrac_shape_equality_validation",
               "M8d_pairfrac_n_pairs_finite_validation", "M8e_pairfrac_n_pairs_nonnegative_validation",
               "M8f_pairfrac_n_pairs_integer_validation", "M8g_pairfrac_n_galaxies_finite_validation",
               "M8h_pairfrac_n_galaxies_nonnegative_validation", "M8i_pairfrac_n_galaxies_integer_validation",
               "M8j_pairfrac_zero_denominator_validation", "M23_zero_zero_nan"}:
        return "compute_pair_fraction"
    if MUT in {"M2_timescale_sign", "M9a_timescale_z_form_validation",
               "M9b_timescale_z_finite_validation", "M9c_timescale_z_lower_bound_validation",
               "M9d_timescale_gyr0_form_validation", "M9e_timescale_alpha_form_validation",
               "M9f_timescale_gyr0_finite_validation", "M9g_timescale_gyr0_positive_validation",
               "M9h_timescale_alpha_finite_validation", "M17_hardcode_alpha"}:
        return "merger_timescale_gyr"
    if MUT in {"M3_box_squared", "M10a_rate_f_pair_rank_validation",
               "M10b_rate_sigma_f_pair_rank_validation", "M10c_rate_n_galaxies_rank_validation",
               "M10d_rate_array_shape_equality_validation", "M10e_rate_f_pair_finite_validation",
               "M10f_rate_f_pair_nonnegative_validation", "M10g_rate_sigma_f_pair_finite_validation",
               "M10h_rate_sigma_f_pair_nonnegative_validation", "M10i_rate_n_galaxies_finite_validation",
               "M10j_rate_n_galaxies_nonnegative_validation", "M10k_rate_n_galaxies_integer_validation",
               "M10l_rate_box_size_form_validation", "M10m_rate_timescale_form_validation",
               "M10n_rate_merger_fraction_form_validation", "M10o_rate_box_size_finite_validation",
               "M10p_rate_box_size_positive_validation", "M10q_rate_timescale_finite_validation",
               "M10r_rate_timescale_positive_validation", "M10s_rate_merger_fraction_finite_validation",
               "M10t_rate_merger_fraction_positive_validation", "M10u_rate_merger_fraction_upper_bound_validation",
               "M10v_rate_zero_galaxy_validation"}:
        return "compute_merger_rate"
    if MUT in {"M5_slope_err_x2", "M7_fabricate_fit", "M11_fit_no_weights",
               "M20_n_excluded_zero", "M29_uncentred_y_cross_term"}:
        return "fit_log_rate_vs_redshift"
    if MUT == "M6_consistency_bad_err":
        return "check_slope_consistency"
    if MUT in {"M4_config_box", "M14_sentinel_counted"}:
        return "_load_pair_counts"
    if MUT in {"M13_write_before_preflight", "M25a_reverse_pair_fraction_mass_bins",
               "M25b_reverse_n_pairs_mass_bins", "M25c_reverse_merger_rate_mass_bins",
               "M25d_reverse_merger_rate_err_mass_bins", "M26a_corrupt_merger_fraction_provenance",
               "M26b_corrupt_merger_timescale_alpha_provenance"}:
        return "run_merger_rate_calculation"
    if MUT in {"M18_hardcode_expected_slope",
               "M27a_drop_validation_stored_redshift_finite_preflight",
               "M27b_drop_validation_stored_redshift_lower_bound_preflight",
               "M28a_omit_console_heading", "M28b_omit_console_mass_range",
               "M28c_omit_console_slope", "M28d_omit_console_slope_uncertainty",
               "M28e_omit_console_expected_slope", "M28f_omit_console_n_excluded",
               "M28g_omit_console_status"}:
        return "run_merger_rate_validation"
    return None


def _patch_candidate(fullname, mod):
    if not _is_target(fullname, mod) or getattr(mod, "__MUTATED__", False):
        return
    leaf = str(fullname).rsplit(".", 1)[-1]
    required = _required_api(leaf)
    if required is None or not hasattr(mod, required):
        return
    mod.__MUTATED__ = True
    try:
        _patch_merger_rate(mod) if leaf == "merger_rate" else _patch_calc(mod)
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
