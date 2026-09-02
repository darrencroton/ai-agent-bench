"""DISCRIMINATION CONTROL -- not part of the reference solution.

The shallowest suite that still looks like it tests the selection: it asserts
only that the seven returned arrays have the same length as each other, and
pins no value anywhere. It exists to keep one specific defect out of the
mutation set.

An r1 review found the original `M13` family substituted the whole *unmasked*
array back in for one field, which changes that field's length -- so this file
alone killed 7 of the then-19 mutations without checking a single selected
value. Every `M13` now preserves the post-selection length and corrupts only
which rows survived, and this file is the standing proof: it must score
**0/53**.

Copied into a scratch worktree as `tests/test_data_reader.py` exactly the way
the reference suite is, and scored the same way. See
`reference_solution/README.md` for the measured numbers.
"""
import os
import sys

import h5py
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from data_reader import load_galaxy_catalog

ARRAY_FIELDS = ("x", "y", "z", "vx", "vy", "vz", "log_stellar_mass")
CONFIG = {"log_mass_min": 8.0, "log_mass_max": 11.0}


@pytest.fixture
def catalog_path(tmp_path):
    path = str(tmp_path / "catalog.hdf5")
    masses = [7.5, 8.0, 9.25, 10.5, 11.0, 12.0, 8.75, 7.9]
    n = len(masses)
    with h5py.File(path, "w") as f:
        for i, key in enumerate(("x", "y", "z", "vx", "vy", "vz")):
            f.create_dataset(key, data=100.0 * (i + 1) + np.arange(n))
        f.create_dataset("log_stellar_mass", data=np.asarray(masses))
        f.attrs["redshift"] = 2.5
        f.attrs["box_size"] = 1000.0
    return path


def test_all_arrays_have_the_same_length(catalog_path):
    catalog = load_galaxy_catalog(catalog_path, CONFIG)
    lengths = {field: len(catalog[field]) for field in ARRAY_FIELDS}
    assert len(set(lengths.values())) == 1, lengths


def test_arrays_are_not_empty(catalog_path):
    catalog = load_galaxy_catalog(catalog_path, CONFIG)
    assert len(catalog["x"]) > 0
