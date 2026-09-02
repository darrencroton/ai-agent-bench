# Reference solution

A strong submission for Task 004, kept for harness self-validation only.

**Never shown to a Developer model.** `run_trial.py` only ever copies `spec.md`
into a trial's worktree as `TASK.md`; nothing in this directory is referenced by
`run_trial.py` or `grade_trial.py` at trial time.

## What is in here

| path | what it is |
|---|---|
| `test_data_reader.py` | the reference deliverable — copied into a scratch worktree as `tests/test_data_reader.py`, exactly where a submission puts its own |
| `weak_baseline/` | the vacuous control: loads one catalog, asserts a dict came back |
| `degenerate_controls/shape_only/` | asserts only that the seven arrays have equal length; pins no value |
| `degenerate_controls/rejections_only/` | pins all five rejections with bare `pytest.raises`, no message matching, nothing about the return value |

Unlike Tasks 001-003 there is no `src/` file here, because this task changes no
production code. `src/data_reader.py` is `frozen_unchanged`; the whole
authorized surface is one new test file.

## The design decision: what "correctness" means on a test-only task

This is the one thing about Task 004 that needed deciding rather than
inheriting, and it is worth stating plainly because it changes how the
leaderboard should be read for this task.

In Tasks 001-003 the model both implements and tests something, so `correctness`
(hidden tests, weight 40) and `test_adequacy` (mutation kill rate, weight 25)
measure two different things. Here the model **only** writes tests, against a
function it may not touch. Nothing it writes can change what
`load_galaxy_catalog` does, so any hidden test that calls the function and
checks its behaviour passes for every submission that stays inside its
authorized surface.

**The decision: let `correctness` be an explicit sanity floor, and say so
everywhere.** The hidden tests re-confirm the frozen function's documented
behaviour (`test_hA.py`) plus the driver path and the presence and
collectability of the one authorized deliverable (`test_hB.py`). That is
exactly what `docs/DESIGN.md`'s backlog item 3 asks for — "grade purely by
mutation kill rate ... isolates the 'can this model write a test that can fail'
question from correctness entirely" — so correctness saturating is the design,
not an accident. It is stated in `spec.md`'s "How this task is scored" (the
model is told its correctness score is a floor), in `meta.yaml`'s
`hidden_tests` comment, and in `test_hA.py`'s own module docstring, so no
future reader mistakes a saturated column for a broken one.

The floor is not vacuous. It goes red for a submission that edits the frozen
`src/data_reader.py`, shadows a module, leaves a broken `conftest.py` behind,
puts its tests somewhere other than the authorized path, or ships a file pytest
cannot collect — all of which are things a one-shot unsupervised model actually
does. `scope_discipline` catches the first of those from the diff side;
`correctness` catches all of them from the behavioural side.

### The alternative that was measured and rejected

The other option was a **coverage floor**: a hidden test that runs the
submission's own file under the stdlib `trace` module and requires it to
exercise most of `load_galaxy_catalog`'s lines. That was rejected on evidence,
not taste.

`trace` gives statement counts, not branch counts, and every guard in this
function is an `assert` whose line executes on the happy path. So a single
valid-catalog call covers essentially the whole function. Measured, with
`trace.Trace(count=1)` over each suite:

| suite | statement lines of `load_galaxy_catalog` hit |
|---|---|
| `weak_baseline/test_data_reader.py` (2 vacuous tests) | 15 / 16 (93.8%) |
| `test_data_reader.py` (the reference, 56 tests) | 15 / 16 (93.8%) |

The one unhit line is the docstring. A line-coverage floor cannot tell these two
apart at all, so it would have added a fragile subprocess-inside-a-hidden-test
mechanism in exchange for zero discrimination. Branch coverage would be
different, but the stdlib does not offer it and `coverage`/`pytest-cov` is a
harness-wide dependency change that is out of scope for one task.

### Consequence for scores, stated up front

Every non-cheating trial of this task gets the full 40 points of `correctness`.
The spread between a good and a bad submission is therefore the 25 points of
`test_adequacy` (plus what the judged categories see). Measured below: the
reference scores **98.9%** of the automated rubric weight and the vacuous
baseline **69.5%**. Those two numbers have been bit-identical on every
re-grade; the totals that also carry the two judged categories move a point or
two per run on byte-identical content (see the grading table below), so the
automated pair is the comparison to quote.
That compression is inherent to the task type and is the price of isolating the
one axis it exists to measure; it is a reason to read this task's column
alongside Tasks 001-003, not instead of them.

## Mutation set: 53 mutations, 22 named families

Every mutation is one predicate. `mutations/sitecustomize.py` patches only
`load_galaxy_catalog`, by module basename, post-import, on the
`builtins.__import__` path, the `importlib.import_module` path, and
`importlib.reload`. Three families are generated per catalog array (`M10`,
`M13`, `M16`, ×7 each), one per required message obligation (`M14`, ×9), one
per observable guard-order pair (`M19`, ×3), and three pairs (`M20`, `M21`,
`M22`, ×2 each); the remaining 14 families (`M01`-`M09`, `M11`, `M12`, `M15`,
`M17`, `M18`) are single mutations.

| id | what it does | killed only by |
|---|---|---|
| `M01_missing_file_guard_removed` | drops `assert os.path.isfile(...)`; h5py's `OSError` escapes instead | a test that pins `AssertionError` (not "some exception") for a missing file |
| `M02_empty_catalog_guard_removed` | drops the `n > 0` guard; the call runs on and trips the mass-selection guard instead, with that guard's message | a test that matches the *message* — bare `pytest.raises(AssertionError)` survives |
| `M03_box_size_positive_guard_removed` | drops the `box_size > 0` guard | any test pinning the rejection |
| `M04_negative_mass_guard_removed` | drops the non-negativity guard | any test pinning the rejection |
| `M05_empty_selection_guard_removed` | drops the `n_selected > 0` guard; an empty catalog comes back instead | any test pinning the rejection |
| `M06_mass_min_boundary_excluded` | `>` instead of `>=` at `log_mass_min` | a fixture with a galaxy exactly on the lower edge |
| `M07_mass_max_boundary_excluded` | `<` instead of `<=` at `log_mass_max` | a fixture with a galaxy exactly on the upper edge |
| `M08_zero_mass_rejected` | over-tightens to `> 0`, which is what the guard's own "non-positive" message suggests | a test that a mass of exactly `0.0` is accepted |
| `M09_extra_datasets_rejected` | over-tightens: a file carrying an extra *dataset* is rejected | a test that extra datasets are ignored |
| `M10_float64_cast_removed_<field>` (×7) | that one array comes back in the dtype the file stored | a **dtype** assertion on that field against a non-float64 fixture |
| `M11_redshift_off_by_one` | `redshift` returned as `1 + z` | a test pinning the redshift value |
| `M12_box_size_scaled` | `box_size` returned doubled (an h-factor-shaped slip) | a test pinning the box size |
| `M13_wrong_rows_selected_<field>` (×7) | that one array keeps the **right number** of rows and the **wrong ones** (mask rotated by one) | a test pinning that field's selected *values* — a length check cannot |
| `M14_message_omits_<token>` (×6: `file_not_found`, `empty_catalog`, `box_size_positive`, `log_stellar_mass`, `units_note`, `no_galaxies_in_range`) | erases one required substring from the one rejection message that carries it | a test matching on that substring |
| `M14_message_omits_filepath_<rejection>` (×3: `missing_file`, `empty_catalog`, `mass_range`) | erases the path from just *that one* of the three messages required to quote it | a test checking the path is present in *that specific* message — checking it in only one of the three no longer credits the other two |
| `M15_config_bounds_ignored` | the selection uses the default `[8, 11]` instead of the `config` handed in | a test loading one catalog under a non-default mass range |
| `M16_selected_order_reversed_<field>` (×7) | that one array's surviving rows come back in reverse order (contiguity-preserving, so a stray layout check can't kill it for the wrong reason) | a test pinning that field's row order — checking order for one field no longer credits the other six |
| `M17_unexpected_result_key_leaked` | an extra key in the returned dict | a test asserting the exact nine-key set |
| `M18_extra_attributes_rejected` | over-tightens: a file carrying an extra *attribute* is rejected | a test whose fixture carries one |
| `M19_<pair>` (×3) | swaps one adjacent guard pair, so a doubly-invalid catalog reports the wrong reason: empty + bad `box_size`, bad `box_size` + negative mass, negative mass + empty selection | a fixture per pair that violates both guards at once and pins which one is reported |
| `M21_extra_<dataset\|attribute>_leaked` (×2) | when the file carries an extra dataset (or attribute), it is copied into the returned dict; a strict no-op otherwise | a test that pins the **exact key set** on a fixture that carries extras |
| `M22_zero_redshift_rejected`, `M22_small_box_size_rejected` | over-tightens a plausibility guard onto values the contract accepts: `redshift == 0.0`, and a box smaller than 10 Mpc | a test that loads a catalog carrying those values and expects success |
| `M20_<redshift\|box_size>_not_cast_to_float` (×2) | that scalar comes back as `numpy.float64` instead of Python `float` | `type(x) is float` — `isinstance(x, float)` is True for both, since `numpy.float64` subclasses `float` |

### Every claim `spec.md` makes is measured by something

An r1 review found the spec claiming coverage the 19-mutation set did not have
(message content beyond `M02`, a hardcoded mass range, row order, the nine-key
contract, extra *attributes*, the guard order). Rather than quietly narrowing
the spec, each obligation got a mutation, except one deliberate narrowing:

| spec.md obligation | measured by |
|---|---|
| five rejections, each distinguishable by message | `M01`-`M05`, `M14` (×6) |
| the path is named in each of the three messages that must quote it | `M14_message_omits_filepath_<rejection>` (×3) |
| rejection order, all three observable adjacent pairs | `M19` (×3), plus `M02` from the other side |
| selection applied per array | `M13` (×7) |
| float64 conversion per array | `M10` (×7) |
| both edges inclusive | `M06`, `M07` |
| selection reads `config`, not a hardcoded range | `M15` |
| catalog order preserved, per array | `M16` (×7) |
| exactly nine returned keys | `M17` |
| extra datasets / attributes not rejected | `M09`, `M18` |
| extra datasets / attributes not copied into the result | `M21` (×2) |
| `redshift` of `0.0` and any positive `box_size` accepted | `M22` (×2) |
| mass of exactly `0.0` accepted | `M08` |
| `redshift` / `box_size` values pass through | `M11`, `M12` |
| `redshift` / `box_size` are Python `float`, not a numpy scalar | `M20` (×2) |
| the selection message also quotes both mass limits | **narrowed in spec.md** — the table now says nothing requires that half to be asserted |

An r2 review found `M14`'s single "omit the filepath" mutation covering all
three path-carrying messages at once (so checking the path in one of them
credited all three) and no mutation at all for the units-note omission in the
negative-mass message. Fixed: the filepath obligation is now three mutations,
one per message that must carry it, and `M14_message_omits_units_note` was
added. `M14` is now the finest split that corresponds to something the spec
actually requires — one mutation per (message, required substring) pair, not
one per rejection.

Stale as of r3: this paragraph used to record a deliberate gap here ("no
mutation for 'any positive `box_size` is accepted' as distinct from `M12`'s
value check"). `M22_small_box_size_rejected` (added in round 3, see below) is
exactly that mutation — an over-tightening rejector on a small positive
`box_size`, the same pattern `M08` already applies to zero mass. The gap this
paragraph described no longer exists.

Nothing here inspects the submission's source text. Task 001's history records
why that is a defect class, and it would be especially wrong on a task whose
entire deliverable is a test file that may legitimately be structured in any
number of ways.

## Measured verification

All numbers measured on 2026-09-02 with `venv/bin/python` (Python 3.14.7, numpy
2.5.2, scipy 1.18.1, h5py 3.16.0, pytest 9.1.1) against scratch worktrees
created from the `frozen-substrate` tag the way a trial worktree is
(`git worktree add --detach <path> frozen-substrate`), with this directory's
`test_data_reader.py` copied into `tests/`. They are **post-r2**, i.e. after
both rounds of independent adversarial review recorded at the end of this
file, independently reproduced by the Developer from a clean worktree each
time.

| check | command | result |
|---|---|---|
| baseline pipeline unaffected | `pytest tests/test_geometric.py tests/test_pair_finder.py tests/test_statistical.py -q` | **80 passed** |
| reference's own suite | `pytest tests/test_data_reader.py -q` | **56 passed** |
| `own_suite_command` from `meta.yaml` | `pytest tests/ -q` | **136 passed, 0 failed** |
| same suite from outside the repo root | `pytest -q <worktree>/tests` | **136 passed** (no CWD-relative assumptions) |
| hidden tests | `pytest tests/test_hA.py tests/test_hB.py -q` | **38 passed** (33 in A, 5 in B) |
| mutation gate | `PYTHONPATH=<mutations> MUTATION=<id> pytest tests/ -q --tb=no` for each of the 53 ids | **53/53 killed, 0 survivors** |
| lint on the deliverable | `ruff check --output-format=concise tests/test_data_reader.py` | **clean** |

### End-to-end grading through the real `grade_trial.py`

Both the reference and the vacuous control were graded by the actual harness
(`eval/harness/grade_trial.py --manifest <hand-built manifest>`), not by
re-implementing its checks. The judged categories (readability,
maintainability) are a single LLM judge call each and vary a point or two
between runs by nature; the automated categories are exact and reproduced
identically across three independent grading rounds:

| category (weight) | reference | weak baseline |
|---|---|---|
| `correctness` (40) | **100%** (38/38 hidden, 0 missing) | **100%** (38/38) |
| `test_adequacy` (25) | **100%** (53/53 killed) | **0%** (0/53 killed) |
| `scope_discipline` (10) | **100%** (1 changed file, in surface) | **100%** |
| `hygiene` (10) | 90.9% | 90.9% |
| **automated subtotal** (85 of the 100 rubric weight) | **98.9%** | **69.5%** |
| `readability` (8, judged) | 80-100% | 40-80% |
| `maintainability` (7, judged) | 80% | 40% |
| **total** | **96.1-97.7 / 100** | **65.1-68.3 / 100** |

The four automated rows are bit-identical on every re-grade of byte-identical
content. The judged rows are not: across four full re-grades the reference
totalled 97.7, 97.7, 97.7 and 96.1, and the vacuous baseline 66.7, 65.1, 68.3
and 66.7. That is per-run judge noise, not drift in the submission — a reason
to read this task's entries on the automated 85 points rather than on any one
run's total.

The identical `correctness` row is the design decision above, working as
intended: it is a floor both submissions clear, and the entire automated
separation comes from `test_adequacy`.

> **Harness observation, not a Task 004 defect (flagged for the Developer, not
> fixed here — `eval/harness/*.py` is out of this task's surface).** `hygiene`
> reads 90.9% for a diff with *zero* lint findings, in both runs.
> `lint_diff()` counts every non-blank line of `ruff --output-format=concise`
> output as a finding, and a clean run still prints `All checks passed!`, so a
> perfectly clean diff scores `1/(1 + 0.1*1) = 0.909` and can never reach 1.0.
> This affects every task and every trial already recorded, uniformly.

### No survivors, and why that claim is worth anything

Six controls, so that "53/53" means the mutations fired, and fired for the
right reason. Re-measured in full (all 53 ids, not spot-checked) after the r3
fix round:

- `PYTHONPATH=<mutations>` with `MUTATION` **unset** → 136 passed.
- `PYTHONPATH=<mutations> MUTATION=M99_nonexistent` (hook installed, no branch
  matches) → 136 passed. Every kill is therefore attributable to its own
  mutation, not to `sitecustomize` import overhead.
- **The identity control.** Four mutations remove a guard by re-running a
  transcription of the frozen body (`_body()` in `sitecustomize.py`) with that
  guard skipped, so the transcription's fidelity matters.
  `MUTATION=M00_identity_control` — registered but deliberately absent from
  `mutation_list.txt` — runs `_body()` with **no** guard skipped on every
  rejected input the suite feeds it: **136 passed**, i.e. it re-raises exactly
  what the frozen function raises. (The guard removers are only ever consulted
  after the real function has already raised, so no valid call reaches
  `_body()`.)
- **The freebie control, run in full against all 53 ids** (not a sample): each
  was run against the three frozen test files alone
  (`test_geometric.py`, `test_pair_finder.py`, `test_statistical.py`, no
  `test_data_reader.py` present): **0 killed, 53 survived, 80 passed every
  time**. This task's freebie risk is structurally low — no frozen test
  imports `data_reader` or `calc` at all — but it is measured rather than
  assumed, and it must be re-measured before any mutation is added.
- **Import-style control, six ways.** With
  `MUTATION=M01_missing_file_guard_removed`, each of `import data_reader`,
  `from data_reader import load_galaxy_catalog`, `from src import data_reader`,
  `importlib.import_module("data_reader")`,
  `from importlib import import_module`, and
  `importlib.import_module("src.data_reader")` was confirmed to receive the
  patch. The three `importlib` rows are the r1 fix, and the pre-fix control
  proves the gap was real: with the `importlib.import_module` hook removed,
  `importlib.import_module("data_reader")` receives **no** patch (the call
  raises the unmutated `AssertionError`) while `import data_reader` still does.
  `importlib.reload` is the r2 fix, addressed separately below.
- **The reload control**, the r2 fix's own before/after: a suite that calls
  `importlib.reload(data_reader)` mid-test and then pins the missing-file
  rejection **survives** `M01` with the reload hook removed (the reload
  restored the unwrapped function and the trial silently ran against the
  correct code) and **kills** it with the hook in place. The r3 follow-up
  measures its blast radius as well: reloading `math` under an active mutation
  left `math.__MUTATED__` behind with the first version of that hook and leaves
  it untouched now, while `data_reader` is still re-patched after its own
  reload.
- **Two side-channel controls**, each answering "could a suite kill this
  mutation for a reason that has nothing to do with its predicate?":
  a suite asserting only `flags.c_contiguous` on the seven arrays killed the
  pre-fix `M16` (a bare `[::-1]` view) and kills **0/7** of the current one
  (which copies); a suite asserting only `__context__ is None` and
  `__suppress_context__ is False` on the five rejections killed **9/9** of the
  pre-fix `M14` (raised with `from None` inside the handler) and kills
  **0/9** now that the mutated `AssertionError` is raised outside it. Both
  probe suites pass against the unmutated function, so they are valid suites,
  not broken ones.
- **The shape-only control** (below) proves that no mutation is reachable
  from the *lengths* of the returned arrays alone, without pinning array or
  scalar content. It is deliberately narrow, and two neighbouring axes are
  *not* what it covers: key-set membership (which is exactly what `M17` and
  `M21` require, and this control never inspects) and exception-type
  discrimination (which earns `rejections_only/` its four kills — see
  `degenerate_controls/README.md`).

**Known, accepted gap in the hook** (recorded so it is not rediscovered as a
surprise): a submission that loads the module via
`importlib.util.spec_from_file_location(...)` + `loader.exec_module(...)`
creates a module object no import hook observes, and would receive no mutation.
Closing it would mean intercepting `importlib.util` far deeper or
source-patching the frozen file, which `AGENTS.md`'s stated convention steers
away from — post-import monkeypatching is chosen for insensitivity to
*reasonable* import styles, not to every module-loading API in the stdlib. No
test file in this repo's history, including this task's reference and all three
degenerate controls, loads a module that way.

Kill breadth is thin by construction — most mutations cost a suite 1-3 failing
tests; the widest are `M06`, `M07`, `M10` and `M16`, which touch every fixture
with a boundary galaxy, a non-float64 dtype, or more than one surviving row.
Thin is the point: a targeted mutation is what makes a suite that skips one
obligation lose exactly one mutation (or, for the per-field families, exactly
one field's worth).

### Discrimination controls: does the mutation set measure anything?

| submission | own suite | hidden tests | mutations killed |
|---|---|---|---|
| reference | 56 passed | 38/38 | **53/53** |
| `degenerate_controls/rejections_only/` | 5 passed | (not graded) | **4/53** |
| `degenerate_controls/shape_only/` | 2 passed | (not graded) | **0/53** |
| `weak_baseline/` (vacuous) | 2 passed | 38/38 | **0/53** |

Both degenerate controls are checked in, so these numbers are reproducible
rather than narrated.

`rejections_only/` is the informative row, and it is a *plausible* half-done
submission rather than a strawman: it pins all five rejections, but with bare
`pytest.raises(AssertionError)` and no test of anything the function returns. It
kills `M01`, `M03`, `M04` and `M05` and nothing else — in particular it fails to
kill `M02` (with the emptiness guard gone the call still raises
`AssertionError`, just with the mass-selection guard's message) and every `M14`.
"The suite noticed a failure" and "the suite noticed the right failure" score
differently, which is the whole point of the gate.

`shape_only/` is the standing guard for the r1 BLOCKING finding described
below, and the measurement is two-sided: against the **old** `M13`
implementation it killed **7/7**; against the current one it kills **0/7**, and
0/53 overall.

## Round-1 changes (independent adversarial review)

An independent read-only codex review (`gpt-5.6-sol`, high effort) of the first
draft returned an overall **No**, with five BLOCKING and five SIGNIFICANT
findings. All were fixed rather than argued with; every number above is
post-fix. In summary:

- **The mutation hook missed `importlib.import_module`.** It does not route
  through `builtins.__import__`, so a submission whose test file used it would
  have received no mutation at all and scored 0/N with a perfect suite — a
  false negative in this task's *only* real signal. Both paths are hooked now,
  with the six-way import-style control above and a pre-fix control proving the
  gap was real. (`importlib.reload` was *not* hooked at this point; round 2
  below added it.) The hook
  was ported from Task 003's `sitecustomize.py`, so the same gap likely exists
  there; the Developer is recording that in `docs/DESIGN.md` rather than having
  this task reach outside its surface.
- **The BLOCKING one: `M13` was killable by a shape-only check.** Substituting
  the whole unmasked array changed that field's length, so a single "all seven
  arrays are the same length" assertion killed all seven — the shallow
  shape-check `spec.md` explicitly warns against. Each `M13` now rotates the
  mask by one position, preserving the post-selection length exactly and
  corrupting only which rows survived. Proven in both directions with the
  checked-in `shape_only/` control: 7/7 killed before, 0/7 after.
- **`M10` bundled all seven fields**, the same defect class Task 003 records for
  its `M05`/`M13`/`M14`. Split per field, and the matching Acceptance Criteria
  checkbox now requires each array's dtype to be asserted independently.
- **The spec claimed coverage the mutation set did not have.** Six new
  mutations (`M14` ×6) plus `M15`, `M16`, `M17`, `M18`, `M19`; one claim
  narrowed instead (the selection message's mass limits). The obligation →
  mutation table above is the audit trail. 19 → 36 mutations.
- **`meta.yaml`'s `frozen_unchanged` omitted three files** that exist in the
  frozen substrate (`.gitignore`, `docs/BACKGROUND.md`, `tests/__init__.py`).
  The list is now enumerated from `git ls-tree -r --name-only frozen-substrate`
  and verified to cover the tree exactly. (Tasks 001-003 share the omission;
  again the Developer's to record, not this task's to fix.)
- **The import hook swallowed a failed patch install.** Its outer
  `except Exception: pass` wrapped the `_patch_data_reader` call, so a broken
  installer would have run the trial against the *correct* function and reported
  every mutation as survived — a weak-looking submission that was actually a
  broken harness. The `except` now guards only the attribute probing, per the
  module's own stated design principle.
- Three documentation corrections: the spec's "any storage dtype" claim is now
  scoped to numeric dtypes representable as `float64` (string and compound
  dtypes moved to "Outside the contract"); the scalars' "not converted" prose no
  longer contradicts the table's "as a Python `float`" (it means not rescaled,
  offset or unit-converted); and the Purpose section no longer says
  `tests/test_statistical.py` exercises the loader, since it re-implements part
  of the selection by hand and never calls it. `_body()`'s docstring no longer
  claims to be a line-for-line copy, and `test_hA.py`'s no longer claims
  completeness it does not have.
- The review's SIMPLIFICATION note (trim the 33-node hidden harness and the
  51-node reference suite) was considered and not taken: the reviewer's own
  conclusion was that the task was under-built relative to its claims, and the
  fixes above are what closed that gap.


## Round-2 changes (second independent adversarial review)

The same reviewer re-audited the round-1 package and returned another **No**.
All five BLOCKING and all five SIGNIFICANT round-1 findings were confirmed
resolved with path:line evidence, and four new BLOCKING, two SIGNIFICANT and
three MINOR were raised — smaller in scope, and mostly the *same two defect
classes* recurring in the mutations round 1 had added: a family bundling
independent obligations, and a mutation killable through a side channel that
has nothing to do with its predicate. All are fixed here; every number above is
post-fix. 36 → 47 mutations.

- **`importlib.reload` bypassed an active mutation.** Reload re-executes the
  module body — restoring the unwrapped `load_galaxy_catalog` — while the
  `__MUTATED__` marker set on that same module namespace survives, so the hook
  declined to re-patch and the trial silently ran against the correct function.
  `importlib.reload` is now hooked as well, resetting the marker and
  re-applying the patch. Measured both ways with a probe suite that reloads
  mid-test: `M01` **survives** without the hook, **dies** with it.
- **`M14` bundled three obligations into one and missed a fourth.** The spec
  requires the offending path in *three* separate messages, so one global
  "omit the filepath" mutation let a suite that checked the path in one message
  take credit for all three; and nothing at all covered the units note in the
  negative-mass message. Split into one mutation per (message, required
  substring) pair: 6 → 9. The reference gained three tests to match (54 total).
- **`M16` reversed all seven arrays together**, so an order check on one field
  took credit for the other six — round 1's `M10` finding, recurring in a
  mutation round 1 had added. Split per array (1 → 7). Measured: a suite
  pinning only `log_stellar_mass`'s order killed the old bundled mutation
  **1/1**, and kills **1/7** of the new family.
- **Two side channels that could kill a mutation for the wrong reason**, both
  closed and both now standing controls (see the controls section above):
  `M16`'s `[::-1]` left a negative-stride array, so a contiguity check killed
  it without looking at the order (now copied, 0/7); and `M14`'s
  `raise ... from None` set `__suppress_context__`, which the frozen function's
  bare `assert` never does, so an exception-metadata check killed all nine
  without looking at a message (now raised outside the handler, 0/9).
- **A new mutation family for the two scalar `float()` casts** (`M20` ×2, one
  per scalar). It returns the `numpy.float64` h5py hands back, which is a
  *subclass* of Python `float` — so `isinstance(x, float)` cannot see it and
  only `type(x) is float` can. The reference's two scalar assertions were
  changed accordingly, and `spec.md` gained a checkbox for the type as distinct
  from the value. This is the scalar twin of the lesson `M10` teaches for the
  arrays.
- **Stale counts and one imprecise claim** were cleaned up: `meta.yaml`,
  `weak_baseline/README.md`, `degenerate_controls/README.md` and the
  `shape_only/` docstring all now state 47; and the shape-only control's claim
  is now specific — it proves no mutation is reachable from the *shape* of the
  result, which is a different axis from the exception-type discrimination that
  earns `rejections_only/` its four kills.

Three items the Developer explicitly ruled out of scope, recorded with their
reasons rather than silently dropped:

- **`importlib.util.spec_from_file_location` + `exec_module` remains
  unpatchable**, and is documented above as a known accepted gap rather than
  chased into deeper interception or source-patching.
- **`M10` was not split further into per-(field × dtype-class) mutations**
  (~21). The cast is one generic `.astype(float)` per field with an identical
  failure mode whatever dtype triggered it; per-field is the right granularity,
  and the matching Acceptance Criteria checkbox says "some non-float64 dtype,
  per field" rather than implying each dtype class must be exercised.
- **No "scalars unaffected by the selection" mutation**, because there is no
  structurally plausible bug shape behind it — the scalars are not touched by
  the masking path at all. The hidden `test_A20` covers it, and `spec.md` does
  not claim it is independently perturbed.

## Round-3 changes (third independent adversarial review)

The reviewer re-audited the round-2 package and confirmed all three BLOCKING
and both SIGNIFICANT round-2 findings resolved, and both of the Developer's
round-2 "not fixing" calls (the `spec_from_file_location` bypass, and not
splitting `M10` per dtype class) as reasonable rather than BLOCKING. It raised
three new BLOCKING and two new SIGNIFICANT, none of them in code either earlier
round had touched — the extras contract, the guard-order pairs, the two scalar
must-accepts, and the round-2 reload fix itself. All are fixed here; every
number above is post-fix. 47 → 53 mutations.

- **The extras contract was only half covered.** `M09`/`M18` prove a file
  carrying extras is not *rejected*, and `M17` leaks a key unconditionally —
  but nothing covered the implementation that actually copies the file's extra
  datasets or attributes into the result, which is the shape a
  `for name in f: ...` loop takes. Added `M21_extra_dataset_leaked` and
  `M21_extra_attribute_leaked`, each a strict no-op on a fixture with no
  extras. The reference's extras test now pins the **exact key set** rather
  than naming the two datasets it happens to know about. Measured both ways:
  the old assertion kills the dataset leak but **survives** the attribute leak;
  the new one kills both.
- **Only one of three observable guard-order pairs was tested.** `M19` covered
  empty-before-box_size, and `M02` covers empty-before-selection from the other
  side; box_size-before-negative_mass and negative_mass-before-empty_selection
  were unmeasured although `spec.md` pins the whole order. `M19` is now a
  family of 3, each firing only on the doubly-invalid input where its pair's
  order is observable, with a matching reference test each. Measured: a probe
  suite that pins all five rejections *by message* but uses no doubly-invalid
  fixture **survives all three**, so the order obligation is genuinely distinct
  from the message obligation.
- **Nothing represented an over-strict guard on the two accepted scalars.**
  `M08` does exactly this for a zero mass; `M22_zero_redshift_rejected` and
  `M22_small_box_size_rejected` extend it to `redshift == 0.0` and a 1 Mpc box,
  both of which `spec.md` lists as must-accept. Both are expressed as result
  mutators rather than rejectors so they can only fire on input the frozen
  function accepted — a rejector runs before the real call and could preempt a
  genuine rejection, reporting the wrong reason on an unrelated test. Confirmed
  by measurement, not assumption: both are killed by the pre-existing
  `test_scalars_are_returned_unscaled[0.0-1.0]` case and by nothing else.
- **The round-2 reload hook reset `__MUTATED__` on every reloaded module**
  before checking whether it was the target, so reloading anything unrelated
  left an attribute behind on it. The reset and re-patch are now gated on a
  shared `_is_target()` helper, the same basename-plus-attribute test the
  import hooks use. Measured: reloading `math` under an active mutation tagged
  it before the fix and does not now, while `data_reader` is still correctly
  re-patched after its own reload.
- **`M14`'s scrubbing used an unbounded `str.replace`**, which could erase a
  second, coincidental occurrence of a reason token (a contrived filename
  containing it, say). The reason-token scrubbers now erase exactly one
  occurrence; the filepath scrubbers still erase every occurrence of the one
  literal path they were handed, which is the obligation they exist to remove.
- Four documentation corrections: the family-cardinality summary now accounts
  for `M19`-`M22`; the shape-only control's claim is narrowed to array
  *lengths* (key-set membership is `M17`/`M21`'s axis and this control never
  inspects it); the reference suite's docstring says "at least one test" rather
  than "exactly one" (both missing-file tests fail under `M01`); and round 1's
  history no longer reads as if `importlib.reload` were still unhooked.

These are local harness self-validation counts, not a benchmark score.
