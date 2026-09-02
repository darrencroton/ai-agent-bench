# Task 005: Self-Describing Results Files

> **This is a single-shot evaluation task. Read this document once, implement
> everything it describes in one sitting, and submit your final diff. There is
> no slice-by-slice checkpoint, no reviewer, and no correction round — nobody
> will read your work and hand it back for another attempt. Decide your own
> validation, run it yourself, and stop when you believe the Acceptance
> Criteria below are met.**

## Purpose

`src/calc.py`'s `run_calculation(config)` writes one HDF5 results file per
redshift snapshot, and `_save_pairs()` stamps each file with a block of
provenance attributes: `redshift`, `n_pairs`, `timestamp`, `mass_bin_by`,
`mass_ratio_min` and `max_sep_kpc`.

Two things a reader of a results file needs are missing from that block:

- **`box_size`** — the size of the periodic box the pair-finding ran in. Every
  input catalog carries it as an HDF5 attribute; `load_galaxy_catalog()` reads
  it out as `catalog["box_size"]`, and `find_pairs()` uses that value — and
  only that value — to set the KD-tree's periodic boundary. It appears nowhere
  in the results file.
- **`n_galaxies`** — how many galaxies actually went into that snapshot's
  pair-finding. `run_calculation()` already computes this, as the local
  variable `n_gal`, and uses it only in a progress message; it is never
  recorded.

Add both to the provenance block.

## Why this is worth doing

A results file should be self-describing: everything needed to interpret the
pair catalog it holds should be readable from the file itself.

Today it is not. The single most obvious derived quantity — the pair-finding
efficiency, `n_pairs / n_galaxies` — cannot be computed from a results file at
all, because its denominator is not there. Recovering it means re-opening the
matching input catalog, re-applying `load_galaxy_catalog`'s mass selection
with the same `log_mass_min` / `log_mass_max`, and hoping the `config` in the
working tree is still the one the results were produced with. The box
geometry has the same problem: `mass_ratio_min` and `max_sep_kpc` are recorded
so a reader can tell how the pairs were selected, but `box_size` — which sets
the volume, and therefore every number density derivable from the file — is
not, so any density has to be taken on trust from a `config.py` that the run
may never have consulted for this value in the first place.

Both values are already in hand at the moment the file is written. Recording
them costs nothing and closes the gap.

## Required behaviour

Every results file written by `run_calculation(config)` — one per entry in
`config["redshifts"]` — carries these two attributes in addition to the six it
carries today:

| attribute | stored as | value |
|---|---|---|
| `box_size` | a **floating-point** scalar | the box size of the catalog that snapshot's `find_pairs()` call was given — `catalog["box_size"]`, as `load_galaxy_catalog()` returned it — in **Mpc**, exactly as it stands, no unit conversion |
| `n_galaxies` | an **integer** scalar | the number of galaxies in the catalog that snapshot's `find_pairs()` call was given |

"Stored as" is checkable and is part of the contract: read back through
`h5py`, `numpy.asarray(f.attrs["box_size"]).dtype.kind` must be `"f"` and
`numpy.asarray(f.attrs["n_galaxies"]).dtype.kind` must be `"i"`. This mirrors
the block's existing attributes, where `redshift` is floating and `n_pairs` is
integral.

Two points the value of `box_size` turns on:

- The **catalog's** value is the one to record, not `config["box_size"]`.
  `find_pairs()` reads the periodic box out of the catalog it is handed and
  never looks at `config["box_size"]` at all, and nothing in the pipeline
  enforces that the two agree. Recording the configured value would therefore
  put a number in the file that can be flatly wrong about the geometry the
  pairs were actually found in. Where a catalog's `box_size` differs from
  `config["box_size"]`, the catalog's is what belongs in the results file.
- It is **per snapshot**, for the same reason `n_galaxies` is: each snapshot's
  catalog carries its own value, and each redshift's file records that one.

Three points the value of `n_galaxies` turns on:

- It counts **galaxies, not pairs**. It is unrelated to `n_pairs`, and it is
  not the number of galaxies that ended up in a pair.
- It counts the catalog **as `find_pairs()` received it**, i.e. after
  `load_galaxy_catalog()` has applied the
  `[log_mass_min, log_mass_max]` stellar-mass selection — not the number of
  rows in the input HDF5 file. Those two differ whenever the input catalog
  contains galaxies outside the configured mass range, which it normally does.
- It is **per snapshot**. Each redshift's file records its own snapshot's
  count.

Neither attribute is conditional. A snapshot whose pair-finding yields **no
pairs** still writes its results file today (with zero-length datasets and
`n_pairs == 0`), and that file must carry both new attributes too, with
`n_galaxies` still the real galaxy count — a snapshot with no pairs is
precisely the case where the efficiency `n_pairs / n_galaxies` is worth
recording, and `n_galaxies` is not zero just because `n_pairs` is.

## Behaviour that must not change

- **`run_calculation(config)`'s signature and contract.** Still exactly one
  positional parameter; still writes `config["results_dir"]/pairs_z{z:.1f}.hdf5`
  for each `z` in `config["redshifts"]`; still raises the same `AssertionError`
  when a snapshot's input catalog is not on disk.
- **The six existing provenance attributes** — `redshift`, `n_pairs`,
  `timestamp`, `mass_bin_by`, `mass_ratio_min`, `max_sep_kpc` — keep their
  names, their values and their stored types. In particular `n_pairs` is still
  the pair count, not the galaxy count.
- **The datasets.** Every results file still carries the same seven pair
  arrays `find_pairs()` returns (`mass_primary`, `mass_secondary`,
  `mass_ratio`, `separation_kpc`, `delta_v`, `mass_bin`, `sep_bin`), with the
  same values and the same lengths as today. The pipeline's downstream stages
  read these files and must keep working unchanged.
- **The numbers.** No pair-finding behaviour changes. The same pairs, the same
  separations, the same relative velocities, the same bin assignments.
- **Everything the existing suite pins.** `venv/bin/python -m pytest tests/`
  must pass unmodified.

## Acceptance Criteria

- **Inputs:** unchanged — `run_calculation(config)` takes the same `config`
  dict it takes today, and reads the same input catalogs.
- **Outputs:** each results file gains exactly the two attributes above and
  loses nothing.
- **User-visible behaviour:** `pipeline.py` behaves identically; the results
  files it produces now answer "how big was the box" and "how many galaxies
  went in" without reference to anything outside themselves.

- [ ] Every results file `run_calculation(config)` writes carries a
      `box_size` attribute, stored as a floating-point scalar, whose value is
      the box size of the catalog that snapshot's `find_pairs()` ran on, in
      Mpc — including when that differs from `config["box_size"]`.
- [ ] Every results file carries an `n_galaxies` attribute, stored as an
      integer scalar, whose value is the number of galaxies in the catalog
      passed to `find_pairs()` for that snapshot — post-mass-selection, not the
      input file's row count, and not derived from the pair count.
- [ ] Both attributes are correct for **every** entry in `config["redshifts"]`,
      not only the first, and for a non-default `config` (a different
      `box_size`, a different mass range, a different redshift list) as well as
      the default one.
- [ ] `box_size` follows the catalog and not the config: a snapshot whose input
      catalog declares a different box size from `config["box_size"]` records
      the catalog's.
- [ ] A snapshot that produces zero pairs still gets a results file carrying
      both attributes, with `n_galaxies` equal to that snapshot's real galaxy
      count.
- [ ] Everything under **Behaviour that must not change** still holds, each of
      it tested: the six existing attributes with their values and stored
      types, the seven datasets with their values, the results filenames, the
      missing-input `AssertionError`, and an unchanged `run_calculation`
      signature.
- [ ] `venv/bin/python -m pytest tests/` passes with 0 failed, including your
      new `tests/test_calc_provenance.py`.

## Explicit Non-Goals

- No new configuration keys, and no change to `src/config.py`. Both values are
  already in hand where the results file is written; neither needs a new
  parameter.
- No change to what `find_pairs()` computes or returns, and no change to the
  input catalogs or to `generate_test_data.py`'s output format.
- No further provenance attributes beyond the two named above — not a code
  version, not a hostname, not a config dump. The contract is exactly two new
  attributes.
- No input validation, no new assertions, no logging and no warnings module.
  This task adds a record; it does not add a boundary.
- No change to the results-file naming scheme, the results directory layout,
  or the HDF5 dataset names.
- No changes to any other file — see the Authorized Surface.

## Authorized Surface

Files you may change:

- `src/calc.py`
- `tests/test_calc_provenance.py` (new file — your own test suite)

No other file in the repository should differ from its current committed state
when you are done — including cosmetic re-formatting of lines you did not need
to touch.

## What "done" means

- `venv/bin/python -m pytest tests/` passes with 0 failed, including your new
  `tests/test_calc_provenance.py`.
- Every Acceptance Criteria checkbox above has at least one test in
  `tests/test_calc_provenance.py` that would fail if the behaviour it names
  were broken. A test that merely exercises a code path without being able to
  fail on a wrong answer does not count. Note that two of those checkboxes are
  about behaviour you are *preserving*, not about behaviour you are adding — a
  suite that checks only the two new attributes is incomplete.
- Your tests build their own input catalogs and run against their own
  temporary `data_dir` / `results_dir`; they do not depend on files left
  behind by a previous pipeline run.
- You have run a differential lint pass (`ruff`/`pyflakes` or equivalent) over
  your diff and addressed what it finds.
- You have committed your work. There is no second attempt: submit what you
  have when you stop.
