"""Hidden Harness B: pipeline integration and deliverable checks for Task 004.

Not visible to the Developer model. Copied into the trial worktree's tests/
directory at grade time and run with the trial's own pytest/venv. Scores the
"correctness" rubric category together with test_hA.py.

test_hA.py calls `load_galaxy_catalog` directly. This file answers two
different questions:

1. **Is the substrate still wired together?** A real catalog on disk, through
   the real driver (`calc.run_calculation`), to a results file -- the path a
   submission would break by editing a frozen module, shadowing one, or leaving
   a stray conftest.py behind.
2. **Did the submission actually deliver its one authorized artifact?** The
   task's whole deliverable is `tests/test_data_reader.py`. This file checks
   that it exists and that pytest can collect at least one test from it -- by
   *running* pytest, never by reading the file's source. Task 001's history
   records why source-text inspection is a defect class: a correct submission
   that uses a different-but-equivalent structure must not be penalized for
   failing to match an expected shape. Nothing here looks at what the tests
   assert; the mutation gate does that, by running them.

The whole import block is guarded (Task 003's r1 finding): `calc` imports
`data_reader` and `pair_finder` at module scope, so a submission that broke any
of them would otherwise turn this file into a collection error and take
test_hA.py's already-correct results down with it.
"""
import contextlib
import copy
import io
import os
import subprocess
import sys

import h5py
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

try:
    import calc
    import config as cfgmod
except Exception as e:                          # pragma: no cover
    calc = cfgmod = None
    _IMPORT_ERR = e

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TESTS_DIR)
DELIVERABLE = os.path.join(TESTS_DIR, "test_data_reader.py")

Z = 2.0
BOX_SIZE = 500.0

# Two galaxies, 5 kpc apart on the x axis, both inside the default [8, 11] mass
# selection, mass ratio 10**-0.2 = 0.63 (above the 0.1 cut), relative velocity
# (3, 4, 0) -> |dv| = 5 km/s. Every expected number below is derivable on paper
# from these six lines; no RNG is involved anywhere.
GALAXIES = [
    # x (Mpc),  y,   z,   vx,  vy,  vz,  log_stellar_mass
    (10.0,      0.0, 0.0, 3.0, 4.0, 0.0, 9.0),
    (10.005,    0.0, 0.0, 0.0, 0.0, 0.0, 9.2),
]
EXPECTED_N_PAIRS = 1
EXPECTED_SEPARATION_KPC = 5.0
EXPECTED_DELTA_V = 5.0


def require_pipeline():
    assert calc is not None and cfgmod is not None, (
        f"could not import the pipeline: {globals().get('_IMPORT_ERR')}")


def write_catalog(path, *, masses=None, box_size=BOX_SIZE):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    columns = list(zip(*GALAXIES, strict=True))
    arrays = dict(zip(("x", "y", "z", "vx", "vy", "vz", "log_stellar_mass"),
                      [np.asarray(c, dtype=float) for c in columns],
                      strict=True))
    if masses is not None:
        arrays["log_stellar_mass"] = np.asarray(masses, dtype=float)
    with h5py.File(path, "w") as f:
        for key, arr in arrays.items():
            f.create_dataset(key, data=arr)
        f.attrs["redshift"] = Z
        f.attrs["box_size"] = box_size


@pytest.fixture
def case(tmp_path):
    """A config pointing at a fresh data/ and results/ directory, plus the
    catalog path the driver will look for."""
    require_pipeline()
    config = copy.deepcopy(cfgmod.config)
    config["data_dir"] = str(tmp_path / "data") + os.sep
    config["results_dir"] = str(tmp_path / "results") + os.sep
    config["redshifts"] = [Z]
    data_path = os.path.join(config["data_dir"], f"test_z{Z:.1f}.hdf5")
    results_path = os.path.join(config["results_dir"], f"pairs_z{Z:.1f}.hdf5")
    return config, data_path, results_path


def quiet(fn, *a, **k):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*a, **k)


def test_B01_driver_loads_a_catalog_and_writes_results(case):
    config, data_path, results_path = case
    write_catalog(data_path)
    quiet(calc.run_calculation, config)

    assert os.path.isfile(results_path)
    with h5py.File(results_path, "r") as f:
        assert int(f.attrs["n_pairs"]) == EXPECTED_N_PAIRS
        np.testing.assert_allclose(f["separation_kpc"][:],
                                   [EXPECTED_SEPARATION_KPC], rtol=1e-9)
        np.testing.assert_allclose(f["delta_v"][:], [EXPECTED_DELTA_V],
                                   rtol=1e-9)


def test_B02_driver_rejects_an_out_of_range_catalog(case):
    """The loader's mass-selection guard still fires through the driver."""
    config, data_path, _ = case
    write_catalog(data_path, masses=[13.0, 13.5])
    with pytest.raises(AssertionError, match="No galaxies in mass range"):
        quiet(calc.run_calculation, config)


def test_B03_driver_rejects_a_bad_box_size(case):
    config, data_path, _ = case
    write_catalog(data_path, box_size=-1.0)
    with pytest.raises(AssertionError, match="box_size must be positive"):
        quiet(calc.run_calculation, config)


def test_B04_deliverable_exists():
    assert os.path.isfile(DELIVERABLE), (
        "the task's one authorized deliverable, tests/test_data_reader.py, "
        "is not present in the submitted worktree")


def test_B05_deliverable_collects_at_least_one_test():
    """Runs pytest's collector against the submitted file. This is behavioural
    -- it never reads the file's text -- and it is the floor the mutation gate
    depends on: an uncollectable suite cannot fail on a mutation either."""
    if not os.path.isfile(DELIVERABLE):
        pytest.fail("tests/test_data_reader.py is missing")
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q",
             "-p", "no:cacheprovider", DELIVERABLE],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=180,
            check=False)
    except subprocess.TimeoutExpired:
        pytest.fail("collecting tests/test_data_reader.py timed out")
    collected = [line for line in proc.stdout.splitlines()
                 if "::" in line and not line.startswith(" ")]
    assert proc.returncode == 0 and collected, (
        f"pytest could not collect tests/test_data_reader.py "
        f"(rc={proc.returncode})\n{proc.stdout[-2000:]}")
