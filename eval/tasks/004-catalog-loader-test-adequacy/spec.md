# Task 004: A Test Suite for `load_galaxy_catalog`

> **This is a single-shot evaluation task. Read this document once, implement
> everything it describes in one sitting, and submit your final diff. There is
> no slice-by-slice checkpoint, no reviewer, and no correction round — nobody
> will read your work and hand it back for another attempt. Decide your own
> validation, run it yourself, and stop when you believe the Acceptance
> Criteria below are met.**

## Purpose

`src/data_reader.py`'s `load_galaxy_catalog(filepath, config)` is the pipeline's
entry point: every galaxy catalog that reaches the science code comes through
it. It is 73 lines long, it is correct, and it is the only module in `src/`
with **no dedicated test file**. Nothing in the existing suite calls it at all:
`tests/test_statistical.py` re-implements part of the mass selection by hand
rather than importing `data_reader`, so not one line of this function's actual
behaviour is pinned anywhere today.

Write that test file: `tests/test_data_reader.py`.

**You are writing tests, and only tests.** `src/data_reader.py` is frozen. You
may read it — you are expected to — but you may not change it, and neither may
you change any other file in `src/` or any existing file in `tests/`. If you
believe you have found a bug in the function, you have not: the behaviour
described below is the contract, deliberately, including the parts that look
like oversights. Test what is documented here, not what you would have written.

## How this task is scored

Unusually, and deliberately, this is worth stating up front, because it changes
what "a good submission" means.

Nothing you write can change what `load_galaxy_catalog` does. So the hidden
acceptance tests that run against the frozen function after your trial ends are
a **floor**, not the measurement — they confirm the substrate still works and
that your one authorized file exists and is collectable. Every submission that
stays inside its Authorized Surface and does not break the repository should
clear that floor completely.

What is actually being measured is whether **your tests can fail**. The
obligations documented below are perturbed one at a time in the frozen function
afterwards, and your suite is re-run against each perturbation. An obligation
your suite would not notice being broken scores nothing, however many lines of
test it took to not notice it. (A few clauses have no plausible independent
failure mode and are not perturbed — the contract still holds for them, they
just are not where the score comes from.) A test that calls the function and asserts that
something came back is worth exactly zero here, and so is a test that would
still pass if the mass selection were silently dropped from one of the seven
arrays.

Concretely, that means:

- **Assert values, not shapes.** `assert isinstance(catalog, dict)` and
  `assert len(catalog["x"]) > 0` cannot fail on any plausible defect.
- **Assert the reason, not just the failure.** All five rejections below raise
  `AssertionError`. A test that only checks *that* an `AssertionError` was
  raised cannot tell "empty catalog" from "no galaxies in the mass range" —
  and those two are one deleted line apart. Match on the message.
- **Cover each field, not a representative one.** The selection is applied to
  seven arrays independently. So is the float conversion.
- **Make your fixtures able to disagree.** A fixture whose seven arrays all
  hold the same value in every row, or whose galaxies all fall inside the mass
  range, cannot distinguish a correct selection from a wrong one no matter what
  you assert about it. Give each galaxy distinguishable values, and include
  galaxies that the selection must drop.
- **Cover what must be accepted, not only what must be rejected.** A guard that
  is too strict is as much a defect as a missing one, and only a test that
  pins an accepted input can catch it.

## The function under test

```python
load_galaxy_catalog(filepath, config) -> dict
```

`filepath` is a path to an HDF5 file. `config` is the pipeline configuration
dict; the function reads exactly two keys from it, `config["log_mass_min"]` and
`config["log_mass_max"]`, both `log10(M_star / M_sun)`, and ignores every other
key. `src/config.py` holds the pipeline's defaults (`8.0` and `11.0`), but the
function is not entitled to assume them and neither should your tests.

The file is expected to hold seven 1-D datasets at its root —

| dataset | meaning | unit |
|---|---|---|
| `x`, `y`, `z` | comoving positions | Mpc |
| `vx`, `vy`, `vz` | velocities | km/s |
| `log_stellar_mass` | stellar mass | log10(M_star / M_sun) |

— plus two file-level attributes, `redshift` and `box_size` (Mpc).

## Contract

This section is normative. Where it and the source disagree, the source is
right and this document is a defect — but they do not disagree.

### Rejections

Every one of these fails with a bare `assert`, i.e. an `AssertionError`, and
the message is part of the contract because it is the only thing that tells the
five apart:

| condition | the message contains |
|---|---|
| `filepath` is not an existing file | `Catalog file not found` and the offending path |
| the catalog holds zero galaxies | `Empty catalog` and the path |
| `box_size` is zero or negative | `box_size must be positive` |
| any `log_stellar_mass` entry is negative | `log_stellar_mass`, and a note about expected units |
| no galaxy falls inside `[log_mass_min, log_mass_max]` | `No galaxies in mass range` and the path (it also quotes both limits, which nothing requires you to assert) |

They are evaluated in that order, and the order is observable: a zero-galaxy
catalog that *also* has a non-positive `box_size` is reported as an empty
catalog, and an empty catalog is never reported as an empty mass selection.

### Values returned

The returned `dict` has exactly nine keys and no others:

| key | value |
|---|---|
| `x`, `y`, `z`, `vx`, `vy`, `vz`, `log_stellar_mass` | 1-D `numpy` arrays of dtype **`float64`**, after the mass selection |
| `redshift` | the file attribute, as a Python `float`, unscaled |
| `box_size` | the file attribute, as a Python `float`, unscaled |

- **Every array is converted to `float64`**, independently, whatever numeric
  dtype the file stored it in: signed integer, unsigned integer, `float32`.
  (Numeric dtypes whose values are representable as `float64` are the whole
  domain here — HDF5 string, compound and other non-numeric dtypes are outside
  the contract, see "Outside the contract".) Downstream code does float
  arithmetic on these arrays and relies on the conversion.
- **The mass selection is applied to all seven arrays**, independently and
  identically: a galaxy kept in `x` is kept in `vz` and in `log_stellar_mass`,
  at the same position. Catalog order is preserved; the surviving galaxies come
  back in the order they appear in the file.
- The two scalars are **not** affected by the selection, and their *values*
  pass through untouched — not rescaled, offset, or unit-converted. (They are
  type-coerced to Python `float`, per the table above; "unscaled" is a
  statement about the number, not about its type.)

### The mass selection

```python
mask = (log_stellar_mass >= config["log_mass_min"])
     & (log_stellar_mass <= config["log_mass_max"])
```

**Both edges are inclusive.** A galaxy at exactly `log_mass_min`, and one at
exactly `log_mass_max`, are both kept.

### Input that must be accepted

These are legal and must not raise. Each is a place where a stricter
implementation would look defensible and would be wrong:

- **`log_stellar_mass` of exactly `0.0`.** The guard rejects *negative* masses
  only, even though its message says "non-positive". A one-solar-mass galaxy is
  legal input.
- **Galaxies outside the config mass range.** They are selected out, silently;
  that is the selection's job, not an error — as long as at least one galaxy
  survives.
- **Extra datasets and extra attributes in the file.** Catalogs written by
  `src/generate_test_data.py` carry `is_paired` and `pair_id` alongside the
  seven required datasets. They are ignored, and they do not appear in the
  returned dict.
- **Any numeric storage dtype for the seven arrays** whose values are
  representable as `float64` — signed integer, unsigned integer, `float32`
  (see above).
- **Any positive `box_size`**, and any `redshift`, including `0.0`. The
  function does not check positions against the box, and does not validate
  `redshift` at all.

### Outside the contract

The function's behaviour for the following is **unspecified**. Do not write
tests that pin it: they are pinning an implementation detail of `h5py` or
`numpy`, they can break on a legitimate dependency upgrade, and nothing here
scores them.

- A file that is missing one of the seven datasets or one of the two attributes
  (today: a `KeyError` from `h5py`, whose text is an h5py implementation
  detail).
- A file that is not HDF5, an unreadable path, a directory.
- A dataset stored with a non-numeric HDF5 dtype (string, compound, opaque), or
  a numeric one whose values are not representable as `float64`.
- `NaN` or `inf` anywhere in the arrays or attributes.
- Datasets that are not 1-D, or that differ in length from each other.
- A `config` missing `log_mass_min` or `log_mass_max`.

## Acceptance Criteria

- **Deliverable:** one new file, `tests/test_data_reader.py`, containing a
  pytest suite for `load_galaxy_catalog`.
- **Inputs:** your own fixtures. Build the HDF5 catalogs your tests need by
  hand with `h5py` — fixed, literal arrays.
- **Outputs:** `venv/bin/python -m pytest tests/` passes with 0 failed,
  including your new file.

The **Contract** section above is the normative statement of the behaviour to
be tested. These checkboxes do not restate it; they say what has to be
*demonstrably true* of the suite you submit.

- [ ] **Every** row of the rejection table has a test that fails if that
      rejection stops happening, **and** distinguishes it from the other four
      by matching on the substrings that row requires.
- [ ] The rejection **order** stated above is pinned. The order is only
      observable on input that violates two guards at once, so this needs a
      fixture per adjacent pair — a catalog that is empty *and* has a
      non-positive `box_size`, one with a bad `box_size` *and* a negative mass,
      one with a negative mass *and* a selection that keeps nothing.
- [ ] **Each of the seven arrays separately** has a test that fails if the
      wrong rows survive the selection for that array. Note that a length check
      is not such a test: seven arrays of the right length can still hold the
      wrong galaxies, and a fixture whose values repeat across galaxies cannot
      tell the difference either way.
- [ ] **Each of the seven arrays separately** has its returned **dtype**
      asserted against a catalog stored in *some* other numeric dtype — any one
      will do; you do not need a case per dtype class. A value assertion alone
      does not catch a missing conversion when the stored values are integral,
      and one field's dtype says nothing about the other six.
- [ ] Both **selection edges** are pinned as inclusive, and the selection is
      pinned as reading `config` — a catalog loaded twice under two different
      mass ranges must come back differently.
- [ ] The **order** of the surviving galaxies is pinned, and so is the
      **exact set of nine returned keys**.
- [ ] `redshift` and `box_size` are pinned to the values the file carries, and
      their **type** is asserted as `float`, not just their value — an h5py
      attribute can come back as a `numpy` scalar unless it is explicitly
      cast, and a numpy float compares equal to the Python value it matches.
- [ ] **Every bullet of "Input that must be accepted"** has a test that fails
      if that input starts being rejected or mangled — including a fixture that
      carries both an extra dataset and an extra file attribute.
- [ ] Nothing in the suite pins behaviour listed under "Outside the contract".

## What "done" means

- `venv/bin/python -m pytest tests/` passes with 0 failed.
- Your suite passes when run from **outside the repository root**
  (`venv/bin/python -m pytest /path/to/repo/tests`). Grading runs it that way.
  Write every fixture into pytest's `tmp_path`; never into `data/`, `results/`,
  the repository, or a hardcoded absolute path, and never depend on the current
  working directory.
- Your suite is **deterministic**: no `np.random`, no `numpy.random.default_rng`
  output pinned as an expected value (NumPy does not guarantee that bit stream
  across versions), no dependence on wall-clock time, ordering of `os.listdir`,
  or leftover state from another test.
- You have run a differential lint pass (`ruff`/`pyflakes` or equivalent) over
  your diff and addressed what it finds.
- There is no second attempt: submit what you have when you stop. You do
  not need to `git commit`; leave your final work in the working tree.

## Explicit Non-Goals

- **No change to any file other than `tests/test_data_reader.py`.** Not
  `src/data_reader.py`, not another module in `src/`, not an existing test
  file, not `requirements.txt`, not a new `conftest.py`, not a pytest
  configuration file.
- **No new dependency.** `numpy`, `h5py` and `pytest` are already installed and
  are all this needs. No `pytest-cov`, no `hypothesis`, no `mock` package (the
  stdlib `unittest.mock` is there if you want it, though nothing here needs
  it).
- **No tests for anything else.** Not `find_pairs`, not `calc`,
  not `plot`, not `generate_test_data`. They have their own suites, or are out
  of scope.
- **No fixtures generated by `src/generate_test_data.py`.** It is
  RNG-driven; hand-built arrays are what this task wants.
- **No performance, benchmark, or property-based testing**, and no test that
  needs the network or a catalog you do not create inside the test run.

## Authorized Surface

Files you may change:

- `tests/test_data_reader.py` (new file — your test suite)

No other file in the repository should differ from its current committed state
when you are done — including cosmetic re-formatting of lines you did not need
to touch. In particular `src/data_reader.py` is frozen: it is the subject of
the test suite, and editing it (to add a guard, to reword a message, to make
something easier to test) is a scope violation, not a fix.
