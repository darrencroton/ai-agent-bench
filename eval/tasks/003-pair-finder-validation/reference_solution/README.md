# Reference solution

A working implementation of Task 003, kept for harness self-validation only.

**Never shown to a Developer model.** `run_trial.py` only ever copies `spec.md`
into a trial's worktree as `TASK.md`; nothing in this directory is referenced by
`run_trial.py` or `grade_trial.py` at trial time.

## What this directory adds relative to the baseline `src/`

`pair_finder.py` here is the **full post-edit file**, not a diff — `diff
src/pair_finder.py
eval/tasks/003-pair-finder-validation/reference_solution/pair_finder.py` shows
the whole change. Unlike Tasks 001 and 002, this task creates nothing new in
`src/`; it hardens an existing function in place. The change is:

- two module-level constants, `_REQUIRED_CATALOG_ARRAYS` and
  `_REQUIRED_CONFIG_KEYS`;
- six new private helpers — `_real_scalar`, `_finite_scalar`,
  `_catalog_array`, `_validate_catalog`, `_validate_sep_bins`,
  `_validate_config` — plus a "Validation conventions" comment block stating
  the contract;
- two lines at the top of `find_pairs`: `_validate_catalog(catalog)` then
  `_validate_config(config)`;
- `np.asarray(..., dtype=float)` around the seven catalog arrays and `float()`
  around the two scalars where `find_pairs` first reads them (see "The integer
  dtype defect" below);
- an extended `find_pairs` docstring documenting the accepted input domain.

`_mass_bin_edges`, `_assign_mass_bins` (including its pre-existing `ValueError`
for an unknown `mass_bin_by`) and `_assign_sep_bins` are unchanged, and so is
every line of `find_pairs`'s computation after the reads.
`test_pair_finder_validation.py` is the reference's own test suite, standing in
for what a submission writes at `tests/test_pair_finder_validation.py`. No other
baseline file is touched, and `src/config.py` gains no key — this task adds no
parameter.

## The integer-dtype defects this task's coverage uncovered

`spec.md` declares integer and unsigned array dtypes valid. Building the
round-2 acceptance matrix showed that merely *accepting* them is not enough:
the unmodified body does integer arithmetic on whatever it is handed. There
are **three** distinct faults, each measured against the baseline:

| integer input | baseline behaviour |
|---|---|
| **signed** integer `log_stellar_mass` | `10 ** (m_secondary - m_primary)` raises `ValueError: Integers to negative integer powers are not allowed` |
| **unsigned** integer `log_stellar_mass` | the subtraction wraps, `10 ** huge` overflows to `0`, `mass_ratio` is `0`, and the pair is silently cut — a `uint32` fixture returns 0 pairs where its float twin returns 1 |
| **narrow** (8- or 16-bit) integer velocities | the component-wise `dv**2` overflows before NumPy's promoted reduction runs: 16-bit at an ordinary 500 km/s reports 231.07, and 8-bit at 30 km/s reports `nan` (signed) or 11.49 (unsigned) |

The third is worth reading carefully, because rounds 2 and 3 both got it
wrong before measuring it. Round 2 described the velocity fault as "unsigned
subtraction wraps instead of going negative", and the r2 review correctly
observed that no fixture exercised it. But building the fixture the review
asked for — the lower-indexed galaxy carrying the smaller velocity, so
`vel[i] - vel[j]` goes negative — **still passed**. That mechanism is harmless
on its own: the modular squaring that follows cancels the wrap exactly, since
`(2**32 - 3)**2 mod 2**32 == 9`. What actually survives to the output is
overflow of the *squared sum*, which is a function of the dtype's **width**,
not the sign of the difference. So the fixture now uses 16-bit dtypes and a
500 km/s velocity difference (ordinary for a pipeline whose mock bulk motions
are drawn at `SIGMA_BULK = 200` km/s), the descending-velocity direction is
kept only to pin that the sign is irrelevant, and `spec.md` states the
mechanism correctly.

The fix is the conversion listed above, a provable no-op for float64 input
(`np.asarray` returns a float64 array unchanged), so the frozen suite's 80
tests are unaffected. `spec.md` states the requirement, `test_A314` pins
float-twin equivalence across five dtypes × both velocity directions,
`test_A315` pins it per velocity component × each width that overflows at
ordinary values, and
`M26a`/`M26b`/`M26c` reproduce the three faults separately, so a submission
that fixes only the masses loses a mutation. That claim is measured, not
asserted: a variant that casts the masses and leaves the velocities integral
scores **299/303** on the hidden tests — failing exactly the four 16-bit
`test_A314` cases — while the frozen suite still reports 80/80.

## Design decisions worth knowing about

**1. All required validation lives at `find_pairs`'s boundary.** The private
helpers are not asked to validate their own inputs, because they are only ever
reached after `find_pairs` has validated. This keeps the authorized surface as
tight as the task's brief asked for, and it is also what makes the mutation
gate honest: `mutations/sitecustomize.py` patches **only `find_pairs`**, the one
name the Authorized Surface guarantees exists with a stable signature. A
mutation that patched `_assign_sep_bins` or a named validator would silently
no-op against a submission that factored its validation differently, handing
out a free `test_adequacy` point — the same defect class as Task 001's
exact-import-name finding, one level down.

**2. Catalog array fields must be `np.ndarray`; `config['sep_bins']` may also
be a list or tuple.** The asymmetry is deliberate and `spec.md` says so
explicitly. Every caller in the repo passes catalog fields as ndarrays
(`data_reader`, `tests/test_pair_finder.py`, `tests/test_statistical.py`),
and requiring that makes the dtype check meaningful with *zero* coercion —
whereas `np.asarray` on a list would either silently produce a string dtype or,
for a ragged list, raise `ValueError` from numpy, which is exactly the leak the
contract forbids. `sep_bins`, conversely, is a plain Python list of ints in
both `src/config.py` and `tests/test_pair_finder.py`, so rejecting lists there
would reject the pipeline's own configuration.

**3. Only reason-determining precedence is pinned.** `spec.md`'s "Order of
checks" fixes catalog-before-config, form-before-coercion,
finiteness-before-position-range, and `sep_bins`' and the mass grid's own
internal orders — the ones that decide *which* reason token a message must
carry — and declares cross-key ordering unspecified. An earlier draft pinned a
global phase order that the field-by-field reference did not actually
implement; the r1 review caught the disagreement.

## Measured verification

All numbers below were measured on 2026-09-02 with `venv/bin/python` (Python
3.14, numpy 2.5.2, scipy 1.18.1, h5py 3.16.0, pytest 9.1.1) against a scratch
tree assembled the way a trial worktree is: baseline `src/` + `tests/`, with
this directory's `pair_finder.py` copied over `src/pair_finder.py` and
`test_pair_finder_validation.py` copied into `tests/`. They are **post-r3**,
i.e. after both independent adversarial reviews recorded below.

| check | command | result |
|---|---|---|
| baseline pipeline unaffected | `pytest tests/test_geometric.py tests/test_pair_finder.py tests/test_statistical.py -q` | **80 passed** |
| reference's own suite | `pytest tests/test_pair_finder_validation.py -q` | **233 passed** |
| `own_suite_command` from `meta.yaml` | `pytest tests/ -q` | **313 passed, 0 failed** |
| same suite run from outside the repo root | `pytest -q <worktree>/tests` | **313 passed** (no CWD-relative assumptions) |
| hidden tests | `pytest tests/test_hA.py tests/test_hB.py -q` | **315 passed** (309 in A, 6 in B) |
| mutation gate | `PYTHONPATH=../mutations MUTATION=<id> pytest tests/ -q --tb=no` for each of the 59 ids | **59/59 killed, 0 survivors** |
| lint on the deliverable | `ruff check --output-format=concise src/pair_finder.py` | **3 findings, all pre-existing** — the baseline file reports the same 3 `C408` `dict()`-literal notes at the same three `return dict(...)` statements; the hardening adds none |

### No survivors, and why that claim is worth anything

Five controls were run so that "59/59" means the mutations fired, and fired for
the right reason:

- `PYTHONPATH=mutations` with `MUTATION` **unset** → 313 passed.
- `PYTHONPATH=mutations MUTATION=M99_nonexistent` (hook installed, no branch
  matches) → 313 passed. Every kill is therefore attributable to its own
  mutation, not to `sitecustomize` import overhead.
- **The freebie control, which matters more here than in Tasks 001/002.** The
  mutation gate runs `pytest tests/`, and in this task that directory contains
  the frozen `tests/test_pair_finder.py` and `tests/test_statistical.py` —
  which already test the function under mutation. A mutation those files could
  kill on their own would score 1/1 for every submission regardless of what it
  wrote, measuring nothing. So each of the 59 was run against **the three
  frozen files alone**: all 59 pass 80/80 there. **This control earned its
  keep**: it caught two real freebies in the first draft of the round-2
  mutation set — the frozen suite passes a `np.float64` `max_sep`
  (`test_pair_across_corner` computes `np.sqrt(3.0) * 2.0 + 1.0`) and runs the
  pipeline with `mass_ratio_min = 0.0`, so `M23` and `M24` are now scoped
  around both, with the reason recorded inline. Re-run it before adding a
  mutation.
- Import-style control: with `MUTATION=M01_catalog_key_presence`, `import
  pair_finder`, `from src import pair_finder` and `import src.pair_finder` were
  each confirmed to receive the patch (basename matching, per Task 001's
  audit finding).

Kill breadth ranges from thin (`M14d`, `M16`, `M20`, `M24`, `M25` and most of
the `M21`/`M22`/`M23` families at 1–3 failing tests each — by construction,
since each is aimed at one predicate) to broad (`M19a_message_omits_names` at
156, since every rejection case checks that the message names its argument or
key). Thin is the point, not a weakness: a targeted mutation is what makes a
suite that skips one obligation lose exactly one mutation.

**Split families are independently discriminating, measured not assumed.**
With the reference's two integer-equivalence tests deselected, all three of
`M26a_signed_integer_mass_cast_removed`,
`M26b_unsigned_integer_mass_cast_removed` and
`M26c_narrow_integer_velocity_cast_removed` **survive** (291 passed, 22
deselected); with the sep_bins accepted-forms test deselected,
`M22_reject_sep_bins_numpy_scalar_elements` **survives** (306 passed, 7
deselected). Each is therefore killed only by the specific coverage it probes,
not incidentally by something else in the suite. Finer still: `M26c` against
only the three `vz` cases is killed 4/4, so the per-component coverage carries
its own weight rather than riding on `vx`/`vy`.

### Discrimination controls: does the hidden test set measure anything?

Three deliberately wrong submissions were scored against the hidden tests, to
confirm the set separates them from a correct one rather than passing anything
that imports:

| submission | hidden tests | frozen suite |
|---|---|---|
| reference (correct) | **315/315** | 80/80 |
| **unmodified baseline** `src/pair_finder.py` (no validation at all) | **71/315** | 80/80 |
| **validation present but placed after the two early returns** | **229/315** | 80/80 |
| **integer masses cast, integer velocities left integral** | **299/315** | 80/80 |
| **`vz` alone left integral, per-component `dv`** | **311/315** (exactly the four `-vz` cases) | 80/80 |
| **only 16-bit velocities cast** | **309/315** (exactly the six 8-bit cases) | 80/80 |
| **`src/pair_finder.py` replaced by a module that raises on import** | **0/315**, all 315 still collected individually | n/a |

Harness A is 205 malformed-input cases, 64 declared-valid-input cases and 40
preserved-behaviour tests; Harness B is 6 integration tests. The baseline's 71
are the accepted-input and preserved-behaviour cases it does not break — a
submission that changes nothing gets credit only for having broken nothing;
on the malformed side it rejects **none** of the 205, and on the valid side it
fails the integer/unsigned-dtype cases described above.

The other three rows are the useful ones, because each is a *plausible*
mistake that the frozen suite cannot see (all three score 80/80 on it): the
late-validation variant is caught by the `test_A311`–`A313` ordering cases and
three `test_hB` driver tests; the mass-cast-only variant is caught by exactly
the four 16-bit `test_A314` cases. The broken-import row is the guard from
`grade_trial.py`'s `score_hidden_tests` docstring: both hidden files carry a
guarded import, so a broken submission produces 315 individually scored
failures rather than a collection error that would zero out an unrelated
file's correct results.

### Round-2 changes (independent adversarial review)

An independent read-only codex review (`gpt-5.6-sol`, high effort) of the first
draft returned an overall **No** with three BLOCKING and two SIGNIFICANT
findings. All five were fixed rather than argued with; the numbers above are
post-fix. In summary:

- **Top-level `dict` validation was undercontracted and completely unscored** —
  required by prose, absent from the reason-token table, tested by nothing, and
  covered by no mutation, so a submission could omit both checks and still
  score full marks. Fixed: a `dict` token row, an explicit "name the offending
  *argument* for a top-level form failure" message rule, nine hidden cases, and
  `M17`/`M18`.
- **Harness A sampled rather than covered, and scored aggregately** — only four
  of seven array fields were checked for rejected dtypes, whole rejection
  categories collapsed into single loop tests, and the unequal-length case
  checked no field name at all. This was the same fairness defect
  `docs/DESIGN.md` records for Task 002. Fixed: one independently scored
  parametrized case per malformed and per valid input, every field × every
  applicable check class, and the unequal-length message must now name at least
  one of the seven arrays.
- **Broad mutations let one representative case kill them** — `M05`, `M13` and
  `M14` each bundled several independent predicates. Split into 2, 7 and 4
  respectively, and joined by an assertion-message-erasure mutation, two
  argument-type mutations, six over-tightening mutations (which are killed only
  by a suite that tests the "must NOT reject" half of the contract), and the
  integer-equivalence mutation. 16 → 36.
- **The pinned check order was ambiguous and disagreed with the reference** —
  the spec read as global phases, the reference validates field-by-field.
  Replaced with the leaner precedence list described above.
- **`test_B01` pinned `np.random.default_rng` output.** NumPy does not
  guarantee `Generator`'s bit stream across versions, so a legitimate numpy
  upgrade could have failed a correct submission — the same fragility class as
  Task 001's bit-exact float pinning. The four generated snapshots and their
  `EXPECTED` table are gone, replaced by a hand-built 26-galaxy HDF5 catalog
  whose every expected pair, mass bin, separation bin and relative speed is
  derivable on paper. One fixture now serves B01–B05, which also resolved the
  review's "`mock` + `one_snapshot` + four-redshift table is excessive"
  simplification note.

The review's simplification notes were taken as well: `sitecustomize.py`'s dead
`_copy` helper is gone and its 16-way dispatcher is now a four-table registry
(constant-size regardless of mutation count), `_validate_sep_bins` no longer
returns an ignored value, `_real_scalar` is two assertions instead of four, and
`spec.md`'s Acceptance Criteria and "What done means" now reference the
normative tables instead of restating them.

The review agreed with seven of the nine tradeoffs flagged in the first
handover and disagreed with two (the rigid global check order, and the
RNG-pinned fixture); both disagreements are the two SIGNIFICANT fixes above.

### Round-3 changes (second independent adversarial review)

The same reviewer re-audited the round-2 package and returned another **No**.
BLOCKING-1 (dict validation) and both SIGNIFICANT findings were confirmed
resolved, the deterministic fixture confirmed genuinely RNG-independent, and
the float64 cast confirmed a true no-op and correctly scoped — but real gaps
remained. All are fixed here.

- **The velocity fault the spec named was never exercised.** Covered in full
  above. The mechanism turned out to be narrow-dtype overflow of the squared
  sum rather than the subtraction wrap that both the spec and the review had
  assumed, so the fix is a 16-bit fixture at a realistic velocity rather than
  the sign-reversal the review proposed. Measured consequence: a mass-cast-only
  submission now scores 299/303 where it previously scored 303/303.
- **Coverage was still sampled, not Cartesian.** Non-ndarray containers were
  tested on `x` only, string/bool/object dtypes on two fields only, bytes dtype
  nowhere, and no NumPy *integer* scalar was accepted-tested for any config key.
  All are now generated from a field list × a form list, so the case count grew
  (165 → 205 rejections, 33 → 64 accepted) while the generating code shrank.
- **Five mutations still bundled independent obligations.** `M19` (any single
  message assertion killed it), `M21` (all seven fields), `M22` (tuple vs
  ndarray), `M23` (six keys × two families) and `M26` (three distinct faults)
  are now 3, 7, 4, 11 and 3 mutations respectively, generated in loops.
  36 → 59, and `mutation_list.txt` is regenerated from the registries so it
  cannot drift from the code.
- **The preservation language contradicted the integer requirement.** "Must not
  change" and "exactly what it returns today" now explicitly scope to
  previously supported float64 inputs, with the integer/unsigned exception
  stated where the reader first meets it.
- **`test_B01` compared column multisets, not rows.** It now builds the eight
  expected pairs as whole rows, sorts both sides by `(separation, primary
  mass)` — unique across this fixture — and compares row by row. Verified by
  reversing one output column in a variant: the column-wise check passed it,
  the row-wise one fails it and names the group.
- **MINOR:** the module docstring said "four tables" where there are five.

The review also recorded a BLOCKING defect in `grade_trial.py` itself (an
incomplete hidden-test run could score against a shortened denominator). That
is explicitly out of this task's surface; the Developer fixed it separately.

### Round-4 changes (third independent adversarial review)

The r3 review confirmed four of round 2's five findings resolved and the
corrected overflow mechanism accurate, and raised exactly one BLOCKING gap,
naming two concrete full-score-but-wrong implementations. Both are closed.

- **Every overflow-sensitive fixture put the motion in `vx`/`vy`, never `vz`**,
  and the per-field accepted cases used all-zero arrays — proving acceptance,
  not arithmetic. Separately, `INT_DTYPES` started at 16 bits while the
  contract accepts every `dtype.kind in "iuf"`, so 8-bit went untested even
  though its squares overflow at a few tens of km/s. `test_A315` now pins
  float-twin equivalence for each velocity component × each width that
  overflows at ordinary values (`int16`/`uint16` at 300, `int8`/`uint8` at 30)
  — 12 cases, mirrored in the reference suite.

  Measured against the two named escapes: an implementation that forgets `vz`
  scores **311/315**, failing exactly the four `-vz` cases; one that casts only
  16-bit velocities scores **309/315**, failing exactly the six 8-bit cases.
  The frozen suite reports 80/80 for both.

  One correction to the finding as written: leaving `vz` uncast *while still
  using `np.column_stack`* is **not** realizable, because `column_stack`
  promotes the stacked result to the common dtype, so the uncast column becomes
  float64 regardless. That escape exists only if the implementation also
  restructures to per-component arithmetic — which is the variant the
  verification above uses, and which `test_A315`'s `vz` cases catch.

- `M26c`'s existing `itemsize <= 2` predicate already covers 8-bit — verified
  (it kills all 12 new cases), so **no mutation change was needed** and the
  count stays at 59.
- The two stale comments describing the disproven "unsigned subtraction wrap"
  as the velocity fault (in `reference_solution/pair_finder.py` and
  `test_A314`'s docstring) now state the width-dependent, component-wise
  overflow instead. The one remaining occurrence of that phrase in this file is
  a deliberate quotation of what round 2 got wrong.

The review also asked for the published ablation claims to be reproduced and
extended to the `M26b` branch; that is done, and recorded above.

### Deliberate scope decisions (flagged for review rather than buried)

- **No monkeypatch-based driver test.** Task 002 needed one because its driver
  could hardcode a check result no fixture could falsify. Here the "driver" is
  the frozen `calc.run_calculation`, which the submission may not touch, and the
  hardened function is the only thing in the call path — so `test_hB`'s
  malformed-catalog-on-disk tests already prove the wiring. The r1 review
  independently agreed.
- **Core-behaviour mutations are confined to `M15`/`M16` (the `-1` sentinels)
  and `M26` (integer equivalence).** Any other core mutation — max_sep,
  the mass-ratio cut, primary/secondary assignment, `delta_v` — is killed by
  the frozen suite for free. Consequence: `test_adequacy` here is measured
  almost entirely on validation coverage, which the r1 review judged correct
  for this task's intended capability axis.
- **`mass_bin_by`'s value is not validated**, only its presence. The existing
  `ValueError` is frozen by `tests/test_pair_finder.py`;
  `test_A308` and `config_missing_mass_bin_by` pin both halves.
- **A zero-length catalog is declared valid**, not an error. `cKDTree` on an
  empty point set is well-defined (measured: returns 0 pairs), so requiring
  non-emptiness would be over-tightening — and `data_reader` already asserts a
  non-empty catalog where that check belongs.
- **The mass range is not re-checked**, and negative finite masses are accepted.
  `find_pairs` must accept masses outside `[log_mass_min, log_mass_max]`; that
  is the `-1` sentinel's entire purpose, and `data_reader` owns both the
  selection and the non-negativity assertion.
- **`spec.md` pins an explicit set of reason tokens.** Prescriptive, but a
  message-content test is otherwise a guess about which word counts as "the
  reason". The r1 review agreed this half of the original tradeoff was
  justified even as it rejected the global check order.

These are local harness self-validation counts, not a benchmark score.
