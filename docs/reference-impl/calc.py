"""
Calculation driver: loops over redshifts, finds pairs, writes results to disk.

Results are stored as raw pair catalogs (not pre-binned) so plot.py can
re-bin or compute new statistics without re-running the calculation.
"""

import os
import datetime
import numpy as np
import h5py

from data_reader import load_galaxy_catalog
from pair_finder import find_pairs


def _data_path(z, config):
    return os.path.join(config["data_dir"], f"test_z{z:.1f}.hdf5")


def _results_path(z, config):
    return os.path.join(config["results_dir"], f"pairs_z{z:.1f}.hdf5")


def _mass_bin_edges(config):
    n_bins = round((config["log_mass_max"] - config["log_mass_min"]) / config["mass_bin_width"])
    return np.linspace(config["log_mass_min"], config["log_mass_max"], n_bins + 1)


def _count_galaxies_per_mass_bin(log_stellar_mass, config):
    edges = _mass_bin_edges(config)
    raw = np.digitize(log_stellar_mass, edges) - 1
    n_bins = len(edges) - 1
    raw = raw[(raw >= 0) & (raw < n_bins)]
    return np.bincount(raw, minlength=n_bins).astype(np.int64)


def _save_pairs(pairs, n_galaxies_per_mass_bin, box_size_mpc, filepath, z, config):
    """Write pair catalog arrays and metadata to HDF5."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with h5py.File(filepath, "w") as f:
        for key, arr in pairs.items():
            f.create_dataset(key, data=arr)
        f.create_dataset("n_galaxies_per_mass_bin", data=n_galaxies_per_mass_bin)

        # Provenance metadata.
        f.attrs["redshift"]     = z
        f.attrs["n_pairs"]      = len(pairs["delta_v"])
        f.attrs["timestamp"]    = datetime.datetime.now(datetime.timezone.utc).isoformat()
        f.attrs["mass_bin_by"]  = config["mass_bin_by"]
        f.attrs["mass_ratio_min"] = config["mass_ratio_min"]
        f.attrs["max_sep_kpc"]  = config["max_sep"]
        f.attrs["box_size_mpc"] = box_size_mpc


def run_calculation(config):
    """
    Run pair-finding for all redshift snapshots and write results files.

    Asserts that data files exist before starting so the failure is clear.
    """
    os.makedirs(config["results_dir"], exist_ok=True)

    for z in config["redshifts"]:
        data_path    = _data_path(z, config)
        results_path = _results_path(z, config)

        assert os.path.isfile(data_path), (
            f"Data file not found: {data_path}\n"
            "Run with --generate-test first to create test data."
        )

        print(f"  z={z:.1f}: loading catalog...")
        catalog = load_galaxy_catalog(data_path, config)
        n_gal   = len(catalog["x"])

        print(f"  z={z:.1f}: {n_gal} galaxies selected; finding pairs...")
        pairs   = find_pairs(catalog, config)
        n_pairs = len(pairs["delta_v"])
        n_gal_per_bin = _count_galaxies_per_mass_bin(catalog["log_stellar_mass"], config)

        print(f"  z={z:.1f}: {n_pairs} pairs found. Writing {results_path}...")
        _save_pairs(pairs, n_gal_per_bin, catalog["box_size"], results_path, z, config)

    print("Calculation complete.")
