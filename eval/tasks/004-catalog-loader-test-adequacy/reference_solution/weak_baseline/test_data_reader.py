"""DISCRIMINATION CONTROL -- not part of the reference solution.

A deliberately vacuous submission: it loads one valid catalog and asserts only
that something dict-shaped came back. It exercises `load_galaxy_catalog`'s
whole happy path (which is why a line-coverage floor would not separate it from
a real suite -- see reference_solution/README.md), passes cleanly, and is
scored to confirm the mutation gate measures test *strength* rather than mere
presence of a test file.

Copied into a scratch worktree as `tests/test_data_reader.py` exactly the way
the reference suite is, and graded the same way. Expected: `own_suite_command`
green, hidden tests unaffected, mutation kill rate at or near zero.
"""
import os
import sys

import h5py
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from data_reader import load_galaxy_catalog


@pytest.fixture
def catalog_path(tmp_path):
    path = str(tmp_path / "catalog.hdf5")
    with h5py.File(path, "w") as f:
        for key in ("x", "y", "z", "vx", "vy", "vz"):
            f.create_dataset(key, data=np.array([1.0, 2.0, 3.0]))
        f.create_dataset("log_stellar_mass", data=np.array([9.0, 9.5, 10.0]))
        f.attrs["redshift"] = 2.0
        f.attrs["box_size"] = 500.0
    return path


def test_load_galaxy_catalog_returns_a_dict(catalog_path):
    catalog = load_galaxy_catalog(catalog_path, {"log_mass_min": 8.0,
                                                 "log_mass_max": 11.0})
    assert isinstance(catalog, dict)


def test_load_galaxy_catalog_returns_arrays(catalog_path):
    catalog = load_galaxy_catalog(catalog_path, {"log_mass_min": 8.0,
                                                 "log_mass_max": 11.0})
    assert len(catalog) > 0
