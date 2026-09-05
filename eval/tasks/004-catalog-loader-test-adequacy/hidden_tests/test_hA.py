"""Hidden Harness A: substrate integrity for Task 004.

Not visible to the Developer model. Copied into the trial worktree's tests/
directory at grade time and run with the trial's own pytest/venv. Scores the
"correctness" rubric category together with test_hB.py.

**What this file is for, and what it deliberately is not.** Task 004 asks for
tests only: `src/data_reader.py` is frozen, and the submission's authorized
surface is one new test file. Nothing a submission writes can change what
`load_galaxy_catalog` does, so "correctness" here is a *floor*, not the
measurement -- it confirms the frozen function still behaves exactly as
spec.md documents when the trial ends, which is false only if the submission
edited the frozen surface, shadowed a module, or dropped a conftest.py that
breaks collection. Under rubric v2 that floor is a pass/fail GATE carrying no
weight of its own (eval/rubric.yaml's `test_authoring` profile): clearing it
earns no points, and failing any obligation in it scores the whole attempt
zero. So this file's job is to be exactly right, never generous. The measurement this task exists for is the mutation gate
(test_adequacy). The rationale is spelled out in spec.md's "How this task is
scored" and in reference_solution/README.md; it is a deliberate choice, not an
oversight, and it is why this file re-confirms documented behaviour rather than
probing for it.

Consequently this file stays small and does not try to be exhaustive. It is a
substrate check, not the acceptance matrix a Task 001-003 hidden harness is:
it exercises each rejection, the selection (per field, per edge, config-driven,
order-preserving), the float64 conversion, the two scalars, the exact key set,
and the accepted-input clauses once each, so a broken substrate shows up as a
specific failure rather than a wall of red. What the *submission* is required
to cover is stated in spec.md and measured by the mutation gate, not here.

Every fixture is hand-built -- fixed arrays written straight to HDF5 -- so
nothing here depends on `np.random`'s bit stream, which NumPy does not
guarantee stable across versions (Task 003's r1 finding). Everything is written
under `tmp_path`, so the file runs identically from any working directory.

The import is guarded: a submission that breaks the import path would otherwise
turn this file into a pytest collection error and take test_hB.py's
already-correct results down with it (Task 003's r1 finding, and the reason
grade_trial.py passes --continue-on-collection-errors).
"""
import os
import sys

import h5py
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

try:
    import data_reader
except Exception as e:                          # pragma: no cover
    data_reader = None
    _IMPORT_ERR = e

ARRAY_FIELDS = ("x", "y", "z", "vx", "vy", "vz", "log_stellar_mass")
SCALAR_FIELDS = ("redshift", "box_size")

BOX_SIZE = 800.0
REDSHIFT = 3.0
FIELD_BASE = {"x": 11.0, "y": 21.0, "z": 31.0,
              "vx": 41.0, "vy": 51.0, "vz": 61.0}

# Six galaxies; indices 1-4 survive a [8.0, 11.0] selection, with 8.0 and 11.0
# sitting exactly on the two inclusive edges.
MASSES = [7.0, 8.0, 8.4, 10.0, 11.0, 11.5]
SELECTED = [1, 2, 3, 4]
CONFIG = {"log_mass_min": 8.0, "log_mass_max": 11.0}


def loader():
    assert data_reader is not None, (
        f"could not import data_reader: {globals().get('_IMPORT_ERR')}")
    return data_reader.load_galaxy_catalog


def write_catalog(path, *, masses=None, box_size=BOX_SIZE, redshift=REDSHIFT,
                  dtype=np.float64, extras=False):
    """One hand-built HDF5 catalog; returns the arrays it holds."""
    masses = MASSES if masses is None else masses
    n = len(masses)
    arrays = {field: np.asarray(FIELD_BASE[field] + np.arange(n), dtype=dtype)
              for field in FIELD_BASE}
    arrays["log_stellar_mass"] = np.asarray(masses, dtype=dtype)
    with h5py.File(path, "w") as f:
        for key, arr in arrays.items():
            f.create_dataset(key, data=arr)
        if extras:
            f.create_dataset("is_paired", data=np.zeros(n, dtype=bool))
            f.attrs["provenance"] = "hidden fixture"
        f.attrs["redshift"] = redshift
        f.attrs["box_size"] = box_size
    return arrays


@pytest.fixture
def catalog_path(tmp_path):
    path = str(tmp_path / "catalog.hdf5")
    write_catalog(path)
    return path


# --------------------------------------------------------------- rejections
def test_A01_missing_file_rejected(tmp_path):
    with pytest.raises(AssertionError, match="Catalog file not found"):
        loader()(str(tmp_path / "absent.hdf5"), CONFIG)


def test_A02_missing_file_message_names_path(tmp_path):
    missing = str(tmp_path / "absent.hdf5")
    with pytest.raises(AssertionError) as excinfo:
        loader()(missing, CONFIG)
    assert missing in str(excinfo.value)


def test_A03_empty_catalog_rejected(tmp_path):
    path = str(tmp_path / "empty.hdf5")
    write_catalog(path, masses=[])
    with pytest.raises(AssertionError, match="Empty catalog"):
        loader()(path, CONFIG)


@pytest.mark.parametrize("box_size", [0.0, -2.0])
def test_A04_non_positive_box_size_rejected(tmp_path, box_size):
    path = str(tmp_path / "badbox.hdf5")
    write_catalog(path, box_size=box_size)
    with pytest.raises(AssertionError, match="box_size must be positive"):
        loader()(path, CONFIG)


def test_A05_negative_mass_rejected(tmp_path):
    path = str(tmp_path / "negmass.hdf5")
    write_catalog(path, masses=[9.0, -0.5, 10.0])
    with pytest.raises(AssertionError, match="log_stellar_mass"):
        loader()(path, CONFIG)


def test_A06_empty_selection_rejected(catalog_path):
    with pytest.raises(AssertionError, match="No galaxies in mass range"):
        loader()(catalog_path, {"log_mass_min": 20.0, "log_mass_max": 21.0})


def test_A07_emptiness_reported_before_box_size(tmp_path):
    path = str(tmp_path / "empty-badbox.hdf5")
    write_catalog(path, masses=[], box_size=-3.0)
    with pytest.raises(AssertionError, match="Empty catalog"):
        loader()(path, CONFIG)


# ------------------------------------------------- input that must be taken
def test_A08_zero_mass_accepted(tmp_path):
    path = str(tmp_path / "zeromass.hdf5")
    write_catalog(path, masses=[0.0, 4.0])
    catalog = loader()(path, {"log_mass_min": 0.0, "log_mass_max": 11.0})
    np.testing.assert_allclose(catalog["log_stellar_mass"], [0.0, 4.0])


def test_A09_extra_datasets_and_attrs_ignored(tmp_path):
    path = str(tmp_path / "extras.hdf5")
    arrays = write_catalog(path, extras=True)
    catalog = loader()(path, CONFIG)
    np.testing.assert_allclose(catalog["vz"], arrays["vz"][SELECTED])
    assert "is_paired" not in catalog


def test_A10_returned_keys_exact(catalog_path):
    catalog = loader()(catalog_path, CONFIG)
    assert set(catalog) == set(ARRAY_FIELDS) | set(SCALAR_FIELDS)


# ---------------------------------------------------------- mass selection
@pytest.mark.parametrize("field", ARRAY_FIELDS)
def test_A11_selection_applied_to_every_array(tmp_path, field):
    path = str(tmp_path / "catalog.hdf5")
    arrays = write_catalog(path)
    catalog = loader()(path, CONFIG)
    np.testing.assert_allclose(catalog[field], arrays[field][SELECTED])


def test_A12_selection_preserves_order(catalog_path):
    catalog = loader()(catalog_path, CONFIG)
    np.testing.assert_allclose(catalog["log_stellar_mass"],
                               [MASSES[i] for i in SELECTED])


@pytest.mark.parametrize("masses,expected", [
    ([8.0, 9.0], [8.0, 9.0]),        # lower edge is inclusive
    ([9.0, 11.0], [9.0, 11.0]),      # upper edge is inclusive
    ([7.999, 9.0], [9.0]),           # just below the lower edge is dropped
    ([9.0, 11.001], [9.0]),          # just above the upper edge is dropped
])
def test_A13_selection_edges(tmp_path, masses, expected):
    path = str(tmp_path / "edges.hdf5")
    write_catalog(path, masses=masses)
    catalog = loader()(path, CONFIG)
    np.testing.assert_allclose(catalog["log_stellar_mass"], expected)


def test_A14_selection_reads_the_config(catalog_path):
    catalog = loader()(catalog_path, {"log_mass_min": 8.2,
                                      "log_mass_max": 10.5})
    np.testing.assert_allclose(catalog["log_stellar_mass"], [8.4, 10.0])


# ------------------------------------------------ dtype and scalar handling
@pytest.mark.parametrize("dtype", [np.int32, np.uint16, np.float32])
def test_A15_arrays_converted_to_float64(tmp_path, dtype):
    path = str(tmp_path / "typed.hdf5")
    write_catalog(path, masses=[8, 9, 10, 11], dtype=dtype)
    catalog = loader()(path, CONFIG)
    for field in ARRAY_FIELDS:
        assert catalog[field].dtype == np.float64, field


def test_A16_integer_values_survive_conversion(tmp_path):
    path = str(tmp_path / "int.hdf5")
    arrays = write_catalog(path, masses=[8, 9, 10, 11], dtype=np.int32)
    catalog = loader()(path, CONFIG)
    for field in ARRAY_FIELDS:
        np.testing.assert_allclose(catalog[field], arrays[field].astype(float))


def test_A17_redshift_returned(catalog_path):
    catalog = loader()(catalog_path, CONFIG)
    assert catalog["redshift"] == REDSHIFT
    assert isinstance(catalog["redshift"], float)


def test_A18_box_size_returned(catalog_path):
    catalog = loader()(catalog_path, CONFIG)
    assert catalog["box_size"] == BOX_SIZE
    assert isinstance(catalog["box_size"], float)


@pytest.mark.parametrize("redshift,box_size", [(0.0, 1.0), (4.0, 62.5)])
def test_A19_scalars_returned_unscaled(tmp_path, redshift, box_size):
    path = str(tmp_path / "scalars.hdf5")
    write_catalog(path, redshift=redshift, box_size=box_size)
    catalog = loader()(path, CONFIG)
    assert catalog["redshift"] == redshift
    assert catalog["box_size"] == box_size


def test_A20_scalars_unaffected_by_selection(catalog_path):
    catalog = loader()(catalog_path, {"log_mass_min": 8.2,
                                      "log_mass_max": 10.5})
    assert len(catalog["x"]) == 2
    assert catalog["redshift"] == REDSHIFT
    assert catalog["box_size"] == BOX_SIZE
