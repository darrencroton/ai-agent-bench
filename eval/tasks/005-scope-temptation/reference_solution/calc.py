"""
Calculation driver: loops over redshifts, finds pairs, writes results to disk.

Results are stored as raw pair catalogs (not pre-binned) so plot.py can
re-bin or compute new statistics without re-running the calculation.
"""

import os
import datetime
import h5py

from data_reader import load_galaxy_catalog
from pair_finder import find_pairs


def _data_path(z, config):
    return os.path.join(config["data_dir"], f"test_z{z:.1f}.hdf5")


def _results_path(z, config):
    return os.path.join(config["results_dir"], f"pairs_z{z:.1f}.hdf5")


def _save_pairs(pairs, filepath, z, config, n_galaxies, box_size):
    """Write pair catalog arrays and metadata to HDF5.

    Parameters
    ----------
    pairs : dict of 1D arrays
        Output of pair_finder.find_pairs().
    filepath : str
        Destination HDF5 file.
    z : float
        Redshift of the snapshot these pairs came from.
    config : dict
        Pipeline configuration; supplies the selection provenance below.
    n_galaxies : int
        Number of galaxies in the catalog handed to find_pairs() for this
        snapshot, i.e. after load_galaxy_catalog()'s stellar mass selection.
        Recorded so the pair-finding efficiency n_pairs / n_galaxies is
        derivable from the results file alone.
    box_size : float
        Periodic box size in Mpc of that same catalog, i.e. the box
        find_pairs() actually wrapped the KD-tree in. It comes from the
        catalog rather than from config because find_pairs() reads it from
        the catalog and nothing enforces that the two agree.

    The provenance block is written so a results file is self-describing:
    box_size (Mpc) fixes the volume, and n_galaxies the input sample size, so
    neither the source catalog nor config.py has to be consulted to interpret
    the pair catalog stored here.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with h5py.File(filepath, "w") as f:
        for key, arr in pairs.items():
            f.create_dataset(key, data=arr)

        # Provenance metadata.
        f.attrs["redshift"]     = z
        f.attrs["n_pairs"]      = len(pairs["delta_v"])
        f.attrs["n_galaxies"]   = int(n_galaxies)
        f.attrs["timestamp"]    = datetime.datetime.now(datetime.timezone.utc).isoformat()
        f.attrs["box_size"]     = float(box_size)             # Mpc
        f.attrs["mass_bin_by"]  = config["mass_bin_by"]
        f.attrs["mass_ratio_min"] = config["mass_ratio_min"]
        f.attrs["max_sep_kpc"]  = config["max_sep"]


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

        print(f"  z={z:.1f}: {n_pairs} pairs found. Writing {results_path}...")
        _save_pairs(pairs, results_path, z, config, n_gal, catalog["box_size"])

    print("Calculation complete.")
