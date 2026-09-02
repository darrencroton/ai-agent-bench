"""Tests for `data_reader.load_galaxy_catalog`.

The function is frozen: it reads an HDF5 catalog, rejects five classes of bad
input with named assertions, converts every array to float64, applies the
`[log_mass_min, log_mass_max]` stellar-mass selection to all seven arrays, and
returns the two file-level scalars alongside them. This file pins each of those
obligations separately, so that breaking any one of them turns at least one test
(or one parametrized case) red — usually exactly one, and never zero.

Every fixture is hand-built: fixed arrays written straight to HDF5 with h5py,
no RNG anywhere, so nothing here depends on values NumPy does not guarantee
stable across versions. Every catalog is written under pytest's `tmp_path`, so
the file runs identically from any working directory.
"""
import os
import sys

import h5py
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from data_reader import load_galaxy_catalog

ARRAY_FIELDS = ("x", "y", "z", "vx", "vy", "vz", "log_stellar_mass")
SCALAR_FIELDS = ("redshift", "box_size")

BOX_SIZE = 1000.0
REDSHIFT = 2.5

# One distinct base value per positional/velocity field, so an array returned
# for the wrong field -- or with the selection left unapplied -- cannot be
# mistaken for the right one.
FIELD_BASE = {"x": 100.0, "y": 200.0, "z": 300.0,
              "vx": 400.0, "vy": 500.0, "vz": 600.0}

# Eight galaxies. Indices 1, 2, 3, 4 and 6 survive a [8.0, 11.0] selection;
# 8.0 and 11.0 sit exactly on the two edges, which are inclusive.
MASSES = [7.5, 8.0, 9.25, 10.5, 11.0, 12.0, 8.75, 7.9]
SELECTED = [1, 2, 3, 4, 6]

CONFIG = {"log_mass_min": 8.0, "log_mass_max": 11.0}


def write_catalog(path, *, masses=None, box_size=BOX_SIZE, redshift=REDSHIFT,
                  dtype=np.float64, extras=False):
    """Write one hand-built HDF5 catalog and return the arrays it holds.

    `dtype` is the storage dtype of all seven arrays -- the contract says the
    loader converts whatever it finds to float64. `extras` adds the kind of
    extra dataset and attribute `generate_test_data.py` writes, which the
    loader must ignore.
    """
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
            f.create_dataset("pair_id", data=np.arange(n, dtype=np.int64))
            f.attrs["generated_by"] = "test fixture"
        f.attrs["redshift"] = redshift
        f.attrs["box_size"] = box_size
    return arrays


@pytest.fixture
def catalog_path(tmp_path):
    """The eight-galaxy reference catalog, stored as float64."""
    path = str(tmp_path / "catalog.hdf5")
    write_catalog(path)
    return path


# ---------------------------------------------------------------------------
# Rejections. Each names its own reason, so a suite cannot pass by treating
# every failure as interchangeable: the message is the only thing that tells
# a caller which of the five guards fired.
# ---------------------------------------------------------------------------
def test_missing_file_is_rejected(tmp_path):
    missing = str(tmp_path / "does-not-exist.hdf5")
    with pytest.raises(AssertionError, match="Catalog file not found"):
        load_galaxy_catalog(missing, CONFIG)


def test_missing_file_message_names_the_path(tmp_path):
    missing = str(tmp_path / "does-not-exist.hdf5")
    with pytest.raises(AssertionError) as excinfo:
        load_galaxy_catalog(missing, CONFIG)
    assert missing in str(excinfo.value)


def test_empty_catalog_is_rejected(tmp_path):
    path = str(tmp_path / "empty.hdf5")
    write_catalog(path, masses=[])
    with pytest.raises(AssertionError, match="Empty catalog"):
        load_galaxy_catalog(path, CONFIG)


@pytest.mark.parametrize("box_size", [0.0, -1.0, -500.0])
def test_non_positive_box_size_is_rejected(tmp_path, box_size):
    path = str(tmp_path / "badbox.hdf5")
    write_catalog(path, box_size=box_size)
    with pytest.raises(AssertionError, match="box_size must be positive"):
        load_galaxy_catalog(path, CONFIG)


def test_negative_stellar_mass_is_rejected(tmp_path):
    path = str(tmp_path / "negmass.hdf5")
    write_catalog(path, masses=[9.0, -1.0, 10.0])
    with pytest.raises(AssertionError, match="log_stellar_mass"):
        load_galaxy_catalog(path, CONFIG)


def test_negative_stellar_mass_message_states_expected_units(tmp_path):
    """The message names *which* guard fired (previous test) and *why the
    units matter* -- two independent obligations, one message."""
    path = str(tmp_path / "negmass.hdf5")
    write_catalog(path, masses=[9.0, -1.0, 10.0])
    with pytest.raises(AssertionError, match=r"check units.*log10 M_sun"):
        load_galaxy_catalog(path, CONFIG)


def test_empty_catalog_message_names_the_path(tmp_path):
    path = str(tmp_path / "empty.hdf5")
    write_catalog(path, masses=[])
    with pytest.raises(AssertionError) as excinfo:
        load_galaxy_catalog(path, CONFIG)
    assert path in str(excinfo.value)


def test_empty_mass_selection_is_rejected(catalog_path):
    config = {"log_mass_min": 20.0, "log_mass_max": 21.0}
    with pytest.raises(AssertionError, match="No galaxies in mass range"):
        load_galaxy_catalog(catalog_path, config)


def test_empty_mass_selection_message_names_the_path(catalog_path):
    config = {"log_mass_min": 20.0, "log_mass_max": 21.0}
    with pytest.raises(AssertionError) as excinfo:
        load_galaxy_catalog(catalog_path, config)
    assert catalog_path in str(excinfo.value)


def test_empty_catalog_is_reported_before_the_box_size_guard(tmp_path):
    """A zero-galaxy catalog with a bad box_size trips the emptiness guard
    first -- the two guards are ordered, and the message says which fired."""
    path = str(tmp_path / "empty-badbox.hdf5")
    write_catalog(path, masses=[], box_size=-5.0)
    with pytest.raises(AssertionError, match="Empty catalog"):
        load_galaxy_catalog(path, CONFIG)


def test_box_size_is_reported_before_the_negative_mass_guard(tmp_path):
    """A catalog with both a non-positive box_size and a negative mass trips
    the box_size guard first."""
    path = str(tmp_path / "badbox-negmass.hdf5")
    write_catalog(path, masses=[9.0, -1.0, 10.0], box_size=0.0)
    with pytest.raises(AssertionError, match="box_size must be positive"):
        load_galaxy_catalog(path, CONFIG)


def test_negative_mass_is_reported_before_the_empty_selection_guard(tmp_path):
    """A catalog with a negative mass whose galaxies would all be selected out
    trips the mass guard, not the empty-selection guard."""
    path = str(tmp_path / "negmass-noselection.hdf5")
    write_catalog(path, masses=[-1.0, 9.0])
    with pytest.raises(AssertionError, match="log_stellar_mass"):
        load_galaxy_catalog(path, {"log_mass_min": 20.0, "log_mass_max": 21.0})


# ---------------------------------------------------------------------------
# Input the contract declares valid, and which therefore must NOT be rejected.
# ---------------------------------------------------------------------------
def test_stellar_mass_of_exactly_zero_is_accepted(tmp_path):
    """The guard is `>= 0`: log10(M) == 0 (a one-solar-mass galaxy) is legal,
    even though the message talks about "non-positive" values."""
    path = str(tmp_path / "zeromass.hdf5")
    write_catalog(path, masses=[0.0, 5.0])
    catalog = load_galaxy_catalog(path, {"log_mass_min": 0.0,
                                         "log_mass_max": 11.0})
    np.testing.assert_allclose(catalog["log_stellar_mass"], [0.0, 5.0])


def test_extra_datasets_and_attributes_are_ignored(tmp_path):
    """Two obligations, one fixture: extras must not be *rejected*, and they
    must not be *copied into the result* either. The exact-key-set assertion is
    what covers the second -- naming the two datasets is not enough, since it
    would miss an implementation that leaks the extra file attribute."""
    path = str(tmp_path / "extras.hdf5")
    arrays = write_catalog(path, extras=True)
    catalog = load_galaxy_catalog(path, CONFIG)
    np.testing.assert_allclose(catalog["x"], arrays["x"][SELECTED])
    assert set(catalog) == set(ARRAY_FIELDS) | set(SCALAR_FIELDS)
    assert "is_paired" not in catalog
    assert "pair_id" not in catalog
    assert "generated_by" not in catalog


def test_returned_keys_are_exactly_the_documented_nine(catalog_path):
    catalog = load_galaxy_catalog(catalog_path, CONFIG)
    assert set(catalog) == set(ARRAY_FIELDS) | set(SCALAR_FIELDS)


# ---------------------------------------------------------------------------
# The mass selection, applied field by field.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("field", ARRAY_FIELDS)
def test_mass_selection_is_applied_to_every_array(tmp_path, field):
    path = str(tmp_path / "catalog.hdf5")
    arrays = write_catalog(path)
    catalog = load_galaxy_catalog(path, CONFIG)
    np.testing.assert_allclose(catalog[field], arrays[field][SELECTED])


def test_mass_selection_keeps_the_catalog_order(catalog_path):
    catalog = load_galaxy_catalog(catalog_path, CONFIG)
    np.testing.assert_allclose(catalog["log_stellar_mass"],
                               [MASSES[i] for i in SELECTED])


def test_mass_selection_lower_edge_is_inclusive(tmp_path):
    path = str(tmp_path / "edge.hdf5")
    write_catalog(path, masses=[8.0, 9.0])
    catalog = load_galaxy_catalog(path, CONFIG)
    np.testing.assert_allclose(catalog["log_stellar_mass"], [8.0, 9.0])


def test_mass_selection_upper_edge_is_inclusive(tmp_path):
    path = str(tmp_path / "edge.hdf5")
    write_catalog(path, masses=[9.0, 11.0])
    catalog = load_galaxy_catalog(path, CONFIG)
    np.testing.assert_allclose(catalog["log_stellar_mass"], [9.0, 11.0])


def test_mass_selection_follows_the_config_it_is_given(tmp_path, catalog_path):
    """The two config keys are read, not hardcoded: a narrower range keeps
    fewer galaxies, from the same file."""
    catalog = load_galaxy_catalog(catalog_path, {"log_mass_min": 9.0,
                                                 "log_mass_max": 10.6})
    np.testing.assert_allclose(catalog["log_stellar_mass"], [9.25, 10.5])


# ---------------------------------------------------------------------------
# dtype conversion and the two scalars.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("dtype", [np.int32, np.uint16, np.float32])
@pytest.mark.parametrize("field", ARRAY_FIELDS)
def test_every_array_comes_back_as_float64(tmp_path, dtype, field):
    """Integer- and float32-stored catalogs are converted, not passed through:
    downstream code (`find_pairs`) does float arithmetic on these arrays."""
    path = str(tmp_path / "typed.hdf5")
    write_catalog(path, masses=[8, 9, 10, 11], dtype=dtype)
    catalog = load_galaxy_catalog(path, CONFIG)
    assert catalog[field].dtype == np.float64


def test_integer_stored_values_survive_the_conversion(tmp_path):
    path = str(tmp_path / "int.hdf5")
    arrays = write_catalog(path, masses=[8, 9, 10, 11], dtype=np.int32)
    catalog = load_galaxy_catalog(path, CONFIG)
    for field in ARRAY_FIELDS:
        np.testing.assert_allclose(catalog[field], arrays[field].astype(float))


def test_redshift_is_read_from_the_file_attributes(catalog_path):
    catalog = load_galaxy_catalog(catalog_path, CONFIG)
    assert catalog["redshift"] == REDSHIFT
    # type(x) is float, not isinstance: numpy.float64 is a float SUBCLASS, so
    # isinstance(x, float) is True even for an uncast h5py attribute value and
    # would not catch a missing conversion (the scalar twin of the per-array
    # dtype lesson above).
    assert type(catalog["redshift"]) is float


def test_box_size_is_read_from_the_file_attributes(catalog_path):
    catalog = load_galaxy_catalog(catalog_path, CONFIG)
    assert catalog["box_size"] == BOX_SIZE
    assert type(catalog["box_size"]) is float


@pytest.mark.parametrize("redshift,box_size", [(0.0, 1.0), (3.0, 250.0),
                                                (5.0, 500.0)])
def test_scalars_are_returned_unscaled(tmp_path, redshift, box_size):
    """No unit conversion is applied to either scalar on the way out -- and,
    via the first case, that a redshift of exactly 0.0 and a 1 Mpc box are
    accepted at all. Both are values an over-strict plausibility guard would
    reject and the contract does not."""
    path = str(tmp_path / "scalars.hdf5")
    write_catalog(path, redshift=redshift, box_size=box_size)
    catalog = load_galaxy_catalog(path, CONFIG)
    assert catalog["redshift"] == redshift
    assert catalog["box_size"] == box_size


def test_scalars_are_unaffected_by_the_mass_selection(catalog_path):
    """A tighter selection changes the arrays' length and nothing else."""
    catalog = load_galaxy_catalog(catalog_path, {"log_mass_min": 9.0,
                                                 "log_mass_max": 10.6})
    assert len(catalog["x"]) == 2
    assert catalog["redshift"] == REDSHIFT
    assert catalog["box_size"] == BOX_SIZE
