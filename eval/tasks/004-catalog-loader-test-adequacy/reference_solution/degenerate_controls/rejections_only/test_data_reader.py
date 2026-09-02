"""DISCRIMINATION CONTROL -- not part of the reference solution.

A plausible half-done submission rather than a strawman: it pins all five
rejections, but with a bare `pytest.raises(AssertionError)` that never looks at
the message, and it asserts nothing at all about what the function *returns*.

It is the checked-in evidence that the mutation gate grades rather than
switches: it scores well above the vacuous baseline and far below the
reference, and in particular it fails to kill `M02` (with the emptiness guard
removed the call still raises `AssertionError`, just with the mass-selection
guard's message) and every `M14` message mutation.

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

CONFIG = {"log_mass_min": 8.0, "log_mass_max": 11.0}


def write(path, masses, box_size=500.0):
    n = len(masses)
    with h5py.File(path, "w") as f:
        for key in ("x", "y", "z", "vx", "vy", "vz"):
            f.create_dataset(key, data=np.arange(n, dtype=float))
        f.create_dataset("log_stellar_mass",
                         data=np.asarray(masses, dtype=float))
        f.attrs["redshift"] = 2.0
        f.attrs["box_size"] = box_size
    return path


def test_missing_file(tmp_path):
    with pytest.raises(AssertionError):
        load_galaxy_catalog(str(tmp_path / "nope.hdf5"), CONFIG)


def test_empty_catalog(tmp_path):
    with pytest.raises(AssertionError):
        load_galaxy_catalog(write(str(tmp_path / "e.hdf5"), []), CONFIG)


def test_bad_box_size(tmp_path):
    with pytest.raises(AssertionError):
        load_galaxy_catalog(
            write(str(tmp_path / "b.hdf5"), [9.0, 10.0], box_size=0.0), CONFIG)


def test_negative_mass(tmp_path):
    with pytest.raises(AssertionError):
        load_galaxy_catalog(
            write(str(tmp_path / "n.hdf5"), [9.0, -1.0, 10.0]), CONFIG)


def test_no_galaxies_in_range(tmp_path):
    with pytest.raises(AssertionError):
        load_galaxy_catalog(write(str(tmp_path / "s.hdf5"), [20.0, 21.0]),
                            CONFIG)
