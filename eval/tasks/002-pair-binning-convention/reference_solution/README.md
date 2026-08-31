# Reference solution

A working implementation of Task 002, kept for harness self-validation only.

**Never shown to a Developer model.** `run_trial.py` only ever copies `spec.md`
into a trial's worktree as `TASK.md`; nothing in this directory is referenced by
`run_trial.py` or `grade_trial.py` at trial time.

## What this directory adds relative to the baseline `src/`

`pair_binning.py` is a **new** file with no baseline counterpart: `_mass_bin_edges`,
`_data_path`, `_results_path`, `count_galaxies_per_mass_bin`,
`count_pairs_per_mass_bin`, `count_excluded_pairs`, `compute_pair_fraction`,
`check_additivity`, `load_snapshot_counts` and `run_binning_comparison`, plus the
private helpers `_bin_indices`, `_counts_from_bins`, `_pair_member_bins`,
`_real_scalar`, `_real_1d_array`, `_validate_convention(s)`,
`_check_results_provenance`, `_output_path` and `_print_summary`. `config.py` here
is the full post-edit file, not a diff — `diff src/config.py
eval/tasks/002-pair-binning-convention/reference_solution/config.py` shows the
whole change: one added `pair_binning_conventions = ["primary", "secondary",
"either"]` key under a new `# Pair-binning comparison` comment block, and nothing
else. No baseline file is modified.

## The design decision this task turns on

`spec.md` §5 states three binding properties (D1–D3) and refuses to hand over a
formula for `N_gal`. The answer they force is that the denominator is the
**same** count for all three conventions: every supported convention bins on one
galaxy's own stellar mass, so the set of galaxies capable of supplying an
incidence in bin *b* is the same set in every case. `n_galaxies` therefore carries
no convention axis — visible in the output schema's `(nz, nb)` against the other
datasets' `(nz, nc, nb)`. Only the numerator changes, and under `"either"` it
counts `(pair, member)` incidences, so a pair with both members in one bin
contributes two.

## Measured verification

All numbers below were re-measured on 2026-08-31 with `venv/bin/python`
against a scratch worktree assembled the way a trial worktree is: baseline
`src/` + `tests/`, with this directory's `config.py` and `pair_binning.py`
copied over `src/` and `test_pair_binning.py`, `test_hA.py` and `test_hB.py`
copied into `tests/`. This re-measurement followed an independent adversarial
audit that found real gaps in the hidden tests and mutation set (see "Audit
fixes" below); the numbers below are post-fix.

| check | command | result |
|---|---|---|
| baseline pipeline unaffected | `pytest tests/test_geometric.py tests/test_pair_finder.py tests/test_statistical.py -q` | **80 passed** |
| reference's own suite | `pytest tests/test_pair_binning.py -q` | **129 passed** |
| `own_suite_command` from `meta.yaml` | `pytest tests/ -q` | **349 passed, 0 failed** |
| hidden tests | `pytest tests/test_hA.py tests/test_hB.py -q` | **140 passed** |
| mutation gate | `PYTHONPATH=../mutations MUTATION=<id> pytest tests/ -q --tb=no` for each of the 34 ids | **34/34 killed, 0 survivors** |

### No survivors, and why that claim is worth anything

Two controls were run so that "34/34" means the mutations fired rather than
the harness tripping over itself:

- `PYTHONPATH=mutations` with `MUTATION` **unset** → 349 passed.
- `PYTHONPATH=mutations MUTATION=M99_nonexistent` (hook installed, no branch
  matches) → 349 passed.

Every kill is therefore attributable to its own mutation, not to `sitecustomize`
import overhead. Each of the 34 runs also collected all 349 tests — no kill came
from a collection error. Kills range from thin (`M26`, `M30` at 2 failing tests)
to broad (`M34_provenance_validation_disabled` at 50, since disabling
per-attribute provenance validation entirely trips every rejection test that
exercises it).

### Audit fixes (post-initial-validation)

An independent adversarial audit of this task found several real gaps after
the initial validation above. All were fixed in place rather than noted for
later, per `AGENTS.md`'s "fix the spec/tests, don't leave it for the model to
guess at":

- The runtime additivity check (`run_binning_comparison`'s `additivity_holds`)
  was never exercised on a `False` result — every fixture satisfies the
  identity by construction (it is a theorem, spec.md section 7), so a driver
  that hardcoded `additivity_holds=True` without ever calling
  `check_additivity` could not have been caught. Fixed by monkeypatching
  `check_additivity` itself in a new hidden test (`test_B24`) and a new
  mutation (`M32_additivity_forced_false`).
- The preflight-atomicity tests only used a single configured redshift, so a
  driver that starts writing after checking only the first snapshot could
  pass. Fixed with a two-redshift case (`test_B19b`) that breaks only the
  second snapshot.
- The nondefault bin-grid criterion (`test_A27`) was only ever exercised
  through the Part 1 pure functions, never through the full driver
  (`run_binning_comparison`). Fixed with `test_B26`, which runs the driver
  end-to-end on the `[9.0, 12.0)` / 1.5 dex grid and checks every returned and
  persisted value against it.
- Every pinned pair fixture in this task happened to sit above the default
  `mass_ratio_min=0.1`, so a driver or Part 1 function that silently
  reapplied the mass-ratio cut (which Part 1 explicitly does not impose)
  would still have passed. Fixed with `test_A28` and `test_B27`, using a
  primary=10.0/secondary=8.0 pair at ratio 0.01.
- `check_additivity` converted integer counts to `float64` before comparing,
  which loses precision above `2**53` (spec.md's `<2**53` domain restriction
  is stated only for `compute_pair_fraction`, not `check_additivity`). Fixed
  by comparing in exact `int64` arithmetic instead; `test_A30` pins the
  `[2**53]+[1]` vs `[2**53]` boundary case.
- The mutation set never corrupted the core `f_pair` formula itself, and
  covered the additivity/provenance/nondefault-grid driver paths only
  weakly. Added `M33_pairfrac_wrong_divisor` (denominator off-by-one),
  `M32_additivity_forced_false` and `M34_provenance_validation_disabled`
  (paired with the fixes above).
- Several other gaps (rejection-message content, loosely-typed outputs
  silently accepted, console line selection via substring instead of
  whitespace-token matching, partial/single-redshift driver runs compared
  only via `n_pairs`, `test_A26` comparing only two config keys instead of
  the full frozen baseline, missing lower-mass-edge coverage) were closed
  across `test_hA.py` and `test_hB.py`; see those files' test names and
  docstrings for the specifics.

### The coverage gap that was found and closed

The 30-mutation set the earlier session left behind, run against the reference
suite as it then stood, killed 30/30 — but only because nothing in either the
hidden tests or the reference suite ever varied `log_mass_min`, `log_mass_max` or
`mass_bin_width` from their `config.py` defaults. An implementation that hardcoded
the `[8.0, 11.0)` / 0.5 dex grid would have passed every test in the package. This
is the same defect class an independent audit found in Task 001 ("an undetected
hardcoded default parameter"), so it was closed rather than noted:

- `M31_bin_grid_ignores_config` was added — it forces every binning entry point to
  use the default grid regardless of the config handed to it. It is a **no-op**
  under the shipped defaults, so it is killed only by a suite that varies them.
  Measured: with `test_binning_follows_config_not_the_defaults` deselected, M31
  **survives** (208 passed); with it, M31 is killed. The mutation is a genuine
  coverage probe, not a freebie.
- `test_A27` (hidden) and `test_binning_follows_config_not_the_defaults`
  (reference suite) pin the alternate grid `log_mass_min=9.0`,
  `log_mass_max=12.0`, `mass_bin_width=1.5` → edges `[9.0, 10.5, 12.0]`, and the
  corresponding `spec.md` acceptance criterion was added so the requirement is in
  the contract the model reads, not only in the grader.
- `test_B23` (hidden) and `test_provenance_compared_against_config_not_defaults`
  (reference suite) close the same hole on the provenance check, which previously
  could have compared the stored `mass_ratio_min` / `max_sep_kpc` attrs against
  hardcoded `0.1` / `25.0` and passed everything. Verified by hand against a
  deliberately hardcoded variant of `pair_binning.py`: that variant fails exactly
  `test_B23` and nothing else.

### Spec defects found and fixed during this pass

Three hidden-test cases asserted rejections that `spec.md`'s Acceptance Criteria
did not list, while the spec's *Validation and Failure Conventions* section
explicitly says "Where the Criteria do **not** list the input class, its behaviour
stays unspecified and no guard is to be added". A model following the spec
literally would have leaked a `TypeError` and failed those tests through no fault
of its own — the exact "oddly low ceiling across many trials" failure `AGENTS.md`
warns about. Fixed by completing the spec rather than weakening the tests, since
`count_galaxies_per_mass_bin`'s criterion already listed complex input and the
omission in the other three was plainly an oversight: `count_pairs_per_mass_bin` /
`count_excluded_pairs`, `compute_pair_fraction` and `check_additivity` now all
state that complex or otherwise non-real numeric input is rejected. The reference
implementation already guarded all four uniformly, so no implementation change was
needed.

### Notes for whoever reviews this next

- `mutations/sitecustomize.py` matches modules by **basename**, so `import
  pair_binning`, `from src import pair_binning` and `import src.pair_binning` are
  all patched identically. This was checked explicitly against the Task 001 audit
  finding about exact-name matching.
- No hidden test inspects submission source text; the one docstring assertion
  (`test_A23`) reads `compute_pair_fraction.__doc__` after collapsing whitespace,
  which is the sentence `spec.md` pins verbatim.
- Float comparisons in the hidden tests use `rtol=1e-14, atol=0` wherever a value
  came out of arithmetic. The three places using `rtol=0, atol=0` compare either a
  value round-tripped unchanged through HDF5 (`test_B14`) or exactly representable
  bin edges reproduced from the same pinned `np.linspace` call (`test_A03`,
  `test_B13`) — no non-associative arithmetic sits on either side.
- The integration tests check per-bin values against counts recomputed
  independently inside the test (`test_B15`, `test_B16`), not totals or schema
  alone.

These are local harness self-validation counts, not a benchmark score.
