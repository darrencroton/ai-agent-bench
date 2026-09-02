"""Weak baseline: the shallowest suite that still passes.

NOT a reference solution. This is a checked-in control for the mutation gate,
standing in for the plausible-looking-but-shallow suite a submission can write
in five minutes: one snapshot, the default config, and a check that the two new
attribute *names* exist. It exercises the deliverable without being able to
fail on a wrong value, a wrong stored type, a wrong snapshot, or a regression
in anything it did not add.

Its kill count is the floor Task 005's test_adequacy score is measured against;
see ../README.md.
"""

import contextlib
import copy
import io
import os
import sys

import h5py
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import calc
from config import config as BASE_CONFIG

Z = 2.0


@pytest.fixture(scope="module")
def results(tmp_path_factory):
    root = tmp_path_factory.mktemp("weak")
    cfg = copy.deepcopy(BASE_CONFIG)
    cfg.update(
        data_dir=os.path.join(str(root), "data") + os.sep,
        results_dir=os.path.join(str(root), "results") + os.sep,
        redshifts=[Z],
    )
    os.makedirs(cfg["data_dir"], exist_ok=True)
    x = np.array([1.0, 1.005, 2.0])
    zeros = np.zeros(3)
    with h5py.File(os.path.join(cfg["data_dir"], f"test_z{Z:.1f}.hdf5"), "w") as f:
        f.create_dataset("x", data=x)
        f.create_dataset("y", data=zeros)
        f.create_dataset("z", data=zeros)
        f.create_dataset("vx", data=np.array([30.0, 0.0, 0.0]))
        f.create_dataset("vy", data=np.array([40.0, 0.0, 0.0]))
        f.create_dataset("vz", data=zeros)
        f.create_dataset("log_stellar_mass", data=np.array([9.2, 9.0, 9.5]))
        f.attrs["redshift"] = Z
        f.attrs["box_size"] = float(cfg["box_size"])

    with contextlib.redirect_stdout(io.StringIO()):
        calc.run_calculation(cfg)

    path = os.path.join(cfg["results_dir"], f"pairs_z{Z:.1f}.hdf5")
    with h5py.File(path, "r") as f:
        return dict(f.attrs)


def test_box_size_is_recorded(results):
    assert "box_size" in results


def test_n_galaxies_is_recorded(results):
    assert "n_galaxies" in results
