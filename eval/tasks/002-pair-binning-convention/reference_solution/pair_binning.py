"""
Reference solution for Task 002 (Pair-to-Mass-Bin Assignment Conventions).

Kept for harness self-validation only -- never shown to a Developer model.

Recomputes close-pair counts per stellar-mass bin under three pair-to-bin
assignment conventions ("primary", "secondary", "either"; see
docs/BACKGROUND.md section 4.2) from pair catalogs calc.py has already
written, and compares them.

The denominator decision (spec.md section 5, D1-D3): f_pair(C, b) is a
per-galaxy incidence rate, its denominator is a count of individual galaxies
binned by each galaxy's *own* stellar mass, and all three supported
conventions bin on a single galaxy's own mass. The denominator is therefore
the *same* count for all three -- N_gal(b) has no convention axis. Only the
numerator changes, and under "either" the numerator counts (pair, member)
incidences rather than pairs, so a pair with both members in one bin
contributes two.

Units: masses in log10(M_star/M_sun), separations in kpc, positions in Mpc.
This module introduces no new units and no unit conversions.
"""
import datetime
import numbers
import os

import h5py
import numpy as np

from data_reader import load_galaxy_catalog

# The three conventions of docs/BACKGROUND.md section 4.2 that bin on a
# single galaxy's own stellar mass. "mean" and "total" bin on a joint
# quantity of both members, for which no single-galaxy denominator exists
# (spec.md section 5, D3), so they are not supported here.
SUPPORTED_CONVENTIONS = ("primary", "secondary", "either")

_OUTPUT_FILENAME = "pair_binning.hdf5"


# --------------------------------------------------------------- helpers

def _mass_bin_edges(config):
    """Return array of mass bin edges in log10(M_sun)."""
    n_bins = round((config["log_mass_max"] - config["log_mass_min"]) / config["mass_bin_width"])
    return np.linspace(config["log_mass_min"], config["log_mass_max"], n_bins + 1)


def _data_path(z, config):
    return os.path.join(config["data_dir"], f"test_z{z:.1f}.hdf5")


def _results_path(z, config):
    return os.path.join(config["results_dir"], f"pairs_z{z:.1f}.hdf5")


def _output_path(config):
    return os.path.join(config["results_dir"], _OUTPUT_FILENAME)


def _real_scalar(value, name):
    """Validate *form* before coercion: a non-boolean real numeric scalar.

    Rejects strings, bytes, complex values and arrays (including 0D ones)
    by assertion rather than letting float() raise TypeError/ValueError.
    """
    assert not isinstance(value, np.ndarray), (
        f"{name} must be a real-number scalar, not an array: {value!r}")
    is_real = isinstance(value, (numbers.Real, np.integer, np.floating))
    assert is_real and not isinstance(value, (bool, np.bool_)), (
        f"{name} must be a real-number scalar, got {value!r}")
    return float(value)


def _real_1d_array(value, name):
    """Validate form before coercion, then return a float64 1D copy."""
    arr = np.asarray(value)
    assert arr.ndim == 1, f"{name} must be 1D, got ndim={arr.ndim}"
    assert np.issubdtype(arr.dtype, np.number), (
        f"{name} must be numeric, got dtype {arr.dtype}")
    assert not np.iscomplexobj(arr), f"{name} must not be complex"
    farr = arr.astype(float)
    assert np.all(np.isfinite(farr)), f"{name} must be finite"
    return farr


def _validate_convention(convention):
    assert isinstance(convention, str), (
        f"convention must be a string, got {convention!r}")
    assert convention in SUPPORTED_CONVENTIONS, (
        f"unsupported convention '{convention}'; supported: {list(SUPPORTED_CONVENTIONS)}. "
        "'mean' and 'total' bin on a joint quantity of both members, for which no "
        "single-galaxy denominator exists.")


def _validate_conventions(config):
    """Validate config['pair_binning_conventions'] and return it as a tuple."""
    conventions = config["pair_binning_conventions"]
    assert isinstance(conventions, (list, tuple)), (
        f"pair_binning_conventions must be a list or tuple, got {type(conventions).__name__}")
    assert len(conventions) > 0, "pair_binning_conventions must not be empty"
    for c in conventions:
        _validate_convention(c)
    assert len(set(conventions)) == len(conventions), (
        f"pair_binning_conventions must not contain duplicates: {list(conventions)}")
    return tuple(conventions)


def _bin_indices(log_mass, config):
    """Right-open digitize into mass bins; -1 for anything outside every bin.

    Identical rule to pair_finder._assign_mass_bins, reimplemented locally per
    the repo's duplication convention (pair_finder.py is frozen by this task,
    and its helper knows nothing about the 'either' convention).
    """
    edges = _mass_bin_edges(config)
    n_bins = len(edges) - 1
    raw = np.digitize(log_mass, edges) - 1
    return np.where((raw < 0) | (raw >= n_bins), -1, raw)


def _counts_from_bins(bin_index_arrays, n_bins):
    """Sum incidence counts over one or more arrays of bin indices."""
    counts = np.zeros(n_bins, dtype=np.int64)
    for bins in bin_index_arrays:
        for b in range(n_bins):
            counts[b] += int(np.count_nonzero(bins == b))
    return counts


def _pair_member_bins(log_mass_primary, log_mass_secondary, convention, config):
    """Validate the pair inputs and return the member bin-index arrays.

    Returns (primary_bins, secondary_bins, member_bin_arrays) where the last
    is the tuple of member bin arrays the convention actually selects.
    """
    _validate_convention(convention)
    mp = _real_1d_array(log_mass_primary, "log_mass_primary")
    ms = _real_1d_array(log_mass_secondary, "log_mass_secondary")
    assert mp.shape == ms.shape, (
        f"log_mass_primary and log_mass_secondary must have matching shape, "
        f"got {mp.shape} and {ms.shape}")
    assert np.all(ms <= mp), (
        "log_mass_secondary must be <= log_mass_primary elementwise "
        "(the pipeline's primary/secondary ordering invariant)")

    bp = _bin_indices(mp, config)
    bs = _bin_indices(ms, config)
    if convention == "primary":
        selected = (bp,)
    elif convention == "secondary":
        selected = (bs,)
    else:  # "either" -- both members of every pair
        selected = (bp, bs)
    return bp, bs, selected


# --------------------------------------------------------- Part 1 API

def count_galaxies_per_mass_bin(log_stellar_mass, config):
    """Count individual galaxies per mass bin, by each galaxy's own mass.

    This is the pair fraction's denominator. It is convention-independent by
    construction: every supported convention bins on a single galaxy's own
    stellar mass, so the set of galaxies capable of supplying an incidence in
    bin b is the same set in every case (spec.md section 5, D1-D3). This
    function therefore never consults config['mass_bin_by'] or any convention.

    Bin assignment is right-open, so a galaxy sitting exactly at
    config['log_mass_max'] is selected by data_reader but falls in no bin --
    a pre-existing pipeline inconsistency this task deliberately preserves.
    """
    masses = _real_1d_array(log_stellar_mass, "log_stellar_mass")
    n_bins = len(_mass_bin_edges(config)) - 1
    return _counts_from_bins((_bin_indices(masses, config),), n_bins)


def count_pairs_per_mass_bin(log_mass_primary, log_mass_secondary, convention, config):
    """Count (pair, member) incidences per mass bin under `convention`.

    N_pairs(C, b) = |I(C, b)| where I(C, b) is the set of (pair, member)
    combinations convention C places in bin b. Under "either" both members of
    every pair are candidates, so a pair whose members share a bin
    contributes two incidences to it.
    """
    _, _, selected = _pair_member_bins(
        log_mass_primary, log_mass_secondary, convention, config)
    n_bins = len(_mass_bin_edges(config)) - 1
    return _counts_from_bins(selected, n_bins)


def count_excluded_pairs(log_mass_primary, log_mass_secondary, convention, config):
    """Count stored pairs contributing no incidence to any bin under `convention`."""
    _, _, selected = _pair_member_bins(
        log_mass_primary, log_mass_secondary, convention, config)
    if len(selected) == 1:
        excluded = selected[0] == -1
    else:
        excluded = (selected[0] == -1) & (selected[1] == -1)
    return int(np.count_nonzero(excluded))


def compute_pair_fraction(n_pairs, n_galaxies):
    """Pair incidence per galaxy, and this task's plug-in count error.

    Under the 'either' convention the numerator counts galaxy-pair incidences
    rather than independent pairs, so this plug-in Poisson error is an
    approximation and not a confidence interval.
    """
    n_pairs = np.asarray(n_pairs)
    n_galaxies = np.asarray(n_galaxies)
    assert n_pairs.ndim == 1 and n_galaxies.ndim == 1, (
        f"n_pairs and n_galaxies must be 1D, got ndim {n_pairs.ndim} and {n_galaxies.ndim}")
    assert n_pairs.shape == n_galaxies.shape, (
        f"n_pairs and n_galaxies must have matching shape, "
        f"got {n_pairs.shape} and {n_galaxies.shape}")

    for name, arr in (("n_pairs", n_pairs), ("n_galaxies", n_galaxies)):
        assert np.issubdtype(arr.dtype, np.number), f"{name} must be numeric, got {arr.dtype}"
        assert not np.iscomplexobj(arr), f"{name} must not be complex"
        farr = arr.astype(float)
        assert np.all(np.isfinite(farr)), f"{name} must be finite"
        assert np.all(farr >= 0), f"{name} must be non-negative"
        assert np.all(farr == np.round(farr)), f"{name} must be integer-valued"

    n_pairs_f = n_pairs.astype(float)
    n_galaxies_f = n_galaxies.astype(float)
    assert np.all((n_galaxies_f > 0) | (n_pairs_f == 0)), (
        "a bin with n_pairs > 0 must have n_galaxies > 0")

    with np.errstate(divide="ignore", invalid="ignore"):
        f_pair = np.where(
            n_galaxies_f > 0,
            n_pairs_f / np.where(n_galaxies_f > 0, n_galaxies_f, 1.0),
            0.0)
        sigma_f_pair = np.where(
            n_pairs_f > 0,
            f_pair / np.sqrt(np.where(n_pairs_f > 0, n_pairs_f, 1.0)),
            0.0)
    return f_pair, sigma_f_pair


def check_additivity(n_primary, n_secondary, n_either):
    """Return True iff N("primary", b) + N("secondary", b) == N("either", b) for all b.

    A violation is a counting bug in this module, not a property of the data,
    so it is reported as False rather than raised: the caller records it.

    Unlike compute_pair_fraction, this function has no spec-stated domain
    restriction below 2**53, so the final equality is evaluated in exact
    integer arithmetic rather than float64 -- float64 cannot represent every
    integer above 2**53, and comparing sums there could silently misreport
    both a true violation as holding and a true identity as violated.
    """
    arrays = {"n_primary": n_primary, "n_secondary": n_secondary, "n_either": n_either}
    checked = {}
    for name, value in arrays.items():
        arr = np.asarray(value)
        assert arr.ndim == 1, f"{name} must be 1D, got ndim={arr.ndim}"
        assert np.issubdtype(arr.dtype, np.number), f"{name} must be numeric, got {arr.dtype}"
        assert not np.iscomplexobj(arr), f"{name} must not be complex"
        farr = arr.astype(float)
        assert np.all(np.isfinite(farr)), f"{name} must be finite"
        assert np.all(farr >= 0), f"{name} must be non-negative"
        assert np.all(farr == np.round(farr)), f"{name} must be integer-valued"
        checked[name] = arr
    shapes = {name: arr.shape for name, arr in checked.items()}
    assert len(set(shapes.values())) == 1, f"count vectors must have matching shape, got {shapes}"

    # Recover exact integers: an integer-dtype input is cast directly (no
    # float round-trip); an integer-valued float input is rounded first (safe
    # because the loop above already confirmed it is integer-valued) and then
    # cast, which is exact for any magnitude float64 can hold without already
    # having lost the information in the input itself.
    ints = {}
    for name, arr in checked.items():
        if np.issubdtype(arr.dtype, np.integer):
            ints[name] = arr.astype(np.int64)
        else:
            ints[name] = np.round(arr).astype(np.int64)

    return bool(np.all(ints["n_primary"] + ints["n_secondary"] == ints["n_either"]))


# --------------------------------------------------------- Part 2 API

def _check_results_provenance(z, config):
    """Assert one snapshot's inputs exist and its recorded cuts match config.

    Reads neither the 'mass_bin' dataset nor the 'mass_bin_by' attr: both
    record the convention frozen at calculation time, which this module is
    explicitly not bound by (spec.md section 2).
    """
    data_path = _data_path(z, config)
    results_path = _results_path(z, config)
    assert os.path.isfile(data_path), f"galaxy catalog file not found: {data_path}"
    assert os.path.isfile(results_path), f"pair results file not found: {results_path}"

    expected = (
        ("redshift", float(z)),
        ("mass_ratio_min", float(config["mass_ratio_min"])),
        ("max_sep_kpc", float(config["max_sep"])),
    )
    with h5py.File(results_path, "r") as f:
        for name, want in expected:
            assert name in f.attrs, f"missing attr '{name}' in {results_path}"
            got = _real_scalar(f.attrs[name], f"attr '{name}' in {results_path}")
            assert got == want, (
                f"attr '{name}' in {results_path} is {got}, expected {want}; "
                "the stored pair sample was produced under different settings")


def load_snapshot_counts(z, config):
    """Assemble one redshift's raw counts from disk.

    n_galaxies has no convention axis: see this module's docstring and
    spec.md section 5.
    """
    conventions = _validate_conventions(config)
    _check_results_provenance(z, config)

    results_path = _results_path(z, config)
    with h5py.File(results_path, "r") as f:
        for name in ("mass_primary", "mass_secondary"):
            assert name in f, f"missing dataset '{name}' in {results_path}"
        mass_primary = f["mass_primary"][...]
        mass_secondary = f["mass_secondary"][...]

    assert np.ndim(mass_primary) == 1 and np.ndim(mass_secondary) == 1, (
        f"mass_primary and mass_secondary must be 1D in {results_path}")
    assert len(mass_primary) == len(mass_secondary), (
        f"mass_primary and mass_secondary lengths differ "
        f"({len(mass_primary)} vs {len(mass_secondary)}) in {results_path}")

    catalog = load_galaxy_catalog(_data_path(z, config), config)
    n_galaxies = count_galaxies_per_mass_bin(catalog["log_stellar_mass"], config)

    n_pairs = {}
    n_excluded_pairs = {}
    for convention in conventions:
        n_pairs[convention] = count_pairs_per_mass_bin(
            mass_primary, mass_secondary, convention, config)
        n_excluded_pairs[convention] = count_excluded_pairs(
            mass_primary, mass_secondary, convention, config)

    return {
        "redshift": float(z),
        "n_galaxies": n_galaxies,
        "n_pairs": n_pairs,
        "n_excluded_pairs": n_excluded_pairs,
        "n_pairs_total": len(mass_primary),
    }


# --------------------------------------------------------- Part 3 API

def run_binning_comparison(config):
    """Compare pair-to-bin conventions across every configured redshift.

    Validates config and every input file before opening the output for
    writing, so a preflight failure leaves any pre-existing pair_binning.hdf5
    byte-for-byte untouched.
    """
    conventions = _validate_conventions(config)
    redshifts = list(config["redshifts"])

    # --- preflight: nothing is written until every input has been checked ---
    for z in redshifts:
        _check_results_provenance(z, config)

    edges = _mass_bin_edges(config)
    n_bins = len(edges) - 1
    nz = len(redshifts)
    nc = len(conventions)
    check_all_three = set(conventions) == set(SUPPORTED_CONVENTIONS)

    n_galaxies_all = np.zeros((nz, n_bins), dtype=np.int64)
    n_pairs_all = np.zeros((nz, nc, n_bins), dtype=np.int64)
    fraction_all = np.zeros((nz, nc, n_bins), dtype=float)
    fraction_err_all = np.zeros((nz, nc, n_bins), dtype=float)
    excluded_all = np.zeros((nz, nc), dtype=np.int64)

    results = []
    for iz, z in enumerate(redshifts):
        counts = load_snapshot_counts(z, config)
        n_galaxies = counts["n_galaxies"]
        n_galaxies_all[iz, :] = n_galaxies

        pair_fraction = {}
        pair_fraction_err = {}
        for ic, convention in enumerate(conventions):
            # The same n_galaxies row for every convention -- that is the
            # denominator decision, made visible in the array shapes.
            frac, frac_err = compute_pair_fraction(counts["n_pairs"][convention], n_galaxies)
            pair_fraction[convention] = frac
            pair_fraction_err[convention] = frac_err
            n_pairs_all[iz, ic, :] = counts["n_pairs"][convention]
            fraction_all[iz, ic, :] = frac
            fraction_err_all[iz, ic, :] = frac_err
            excluded_all[iz, ic] = counts["n_excluded_pairs"][convention]

        if check_all_three:
            additivity_holds = check_additivity(
                counts["n_pairs"]["primary"],
                counts["n_pairs"]["secondary"],
                counts["n_pairs"]["either"])
        else:
            additivity_holds = None

        results.append({
            "redshift": float(z),
            "n_galaxies": n_galaxies,
            "n_pairs": dict(counts["n_pairs"]),
            "pair_fraction": pair_fraction,
            "pair_fraction_err": pair_fraction_err,
            "n_excluded_pairs": dict(counts["n_excluded_pairs"]),
            "additivity_holds": additivity_holds,
        })

    output_path = _output_path(config)
    os.makedirs(config["results_dir"], exist_ok=True)
    with h5py.File(output_path, "w") as f:
        f.create_dataset("n_galaxies", data=n_galaxies_all)
        f.create_dataset("n_pairs", data=n_pairs_all)
        f.create_dataset("pair_fraction", data=fraction_all)
        f.create_dataset("pair_fraction_err", data=fraction_err_all)
        f.create_dataset("n_excluded_pairs", data=excluded_all)

        f.attrs["redshifts"] = np.array([float(z) for z in redshifts], dtype=float)
        f.attrs["conventions"] = [str(c) for c in conventions]
        f.attrs["mass_bin_edges"] = np.asarray(edges, dtype=float)
        f.attrs["mass_ratio_min"] = float(config["mass_ratio_min"])
        f.attrs["max_sep_kpc"] = float(config["max_sep"])
        f.attrs["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        f.attrs["additivity_checked"] = bool(check_all_three)
        if check_all_three:
            f.attrs["additivity_holds"] = bool(
                all(r["additivity_holds"] for r in results))

    _print_summary(results, conventions)
    return results


def _print_summary(results, conventions):
    print("Pair-to-mass-bin convention comparison on the configured snapshots. "
          "N_gal(b) is the same galaxy count for every convention; only the "
          "numerator changes.")
    for r in results:
        z = r["redshift"]
        n_gal_total = int(np.sum(r["n_galaxies"]))
        for convention in conventions:
            n_pair_total = int(np.sum(r["n_pairs"][convention]))
            print(f"  z={z:.1f} convention={convention} n_galaxies={n_gal_total} "
                  f"n_pairs={n_pair_total} n_excluded={int(r['n_excluded_pairs'][convention])}")
        if r["additivity_holds"] is None:
            status = "not_checked"
        elif r["additivity_holds"]:
            status = "holds"
        else:
            status = "FAILED"
        print(f"  z={z:.1f} additivity={status}")
