# Task 003: Fail-Loud Input Validation for `find_pairs`

> **This is a single-shot evaluation task. Read this document once, implement
> everything it describes in one sitting, and submit your final diff. There is
> no slice-by-slice checkpoint, no reviewer, and no correction round — nobody
> will read your work and hand it back for another attempt. Decide your own
> validation, run it yourself, and stop when you believe the Acceptance
> Criteria below are met.**

## Purpose

`src/pair_finder.py`'s `find_pairs(catalog, config)` is the numerical core of
this pipeline, and it currently trusts its two arguments completely. It does no
checking at all: not that the catalog's arrays are the same length, not that
they are finite, not that they are one-dimensional, not that `box_size` is a
positive number, not that `max_sep` is positive, not that `sep_bins` is a
usable set of bin edges.

Add fail-loud, assertion-based input validation to `find_pairs`, following the
repo's house convention (`assert` with a message naming the offending value)
and the "validate form before coercion" rule spelled out below. **The
computation itself is correct for the float64 inputs it is given today, and
must not change for them.** This task is almost entirely about the boundary.

The one exception is stated in full under "Integer and unsigned dtypes are
accepted, and must actually work" below, and it is not a change to a working
behaviour: integer- and unsigned-dtype catalogs have no correct behaviour to
preserve today — they raise, or silently drop pairs, or silently misreport
speeds — so the contract gives them one, namely the output of their float64
twin. Everywhere else in this document, "must not change", "unchanged" and
"exactly what it returns today" mean **for the previously supported float64
inputs**.

`data_reader.load_galaxy_catalog()` happens to check a few of these things when
a catalog is loaded from disk, and that is not a substitute: `find_pairs` is
called directly, with a hand-built `catalog` dict, by `tests/test_pair_finder.py`
and `tests/test_statistical.py`, and any downstream user can do the same. It
must defend itself.

## Why this is worth doing (what actually happens today)

The failure modes split into two kinds, and both are defects:

**1. A low-level exception leaks out of a dependency.** Measured against the
current code, with `numpy 2.5` / `scipy 1.18`:

| malformed input | what escapes `find_pairs` today |
|---|---|
| `NaN` or `inf` in `x` / `y` / `z` | `ValueError: data must be finite, check for nan or inf values` (from `cKDTree`) |
| a position `>= box_size` | `ValueError: Some input data are greater than the size of the periodic box.` |
| a negative position | `ValueError: Negative input data are outside of the periodic box.` |
| catalog arrays of unequal length | `ValueError` from `np.column_stack` |
| `config['mass_bin_width'] == 0` | `ZeroDivisionError` |
| `config['mass_bin_width'] < 0` | `ValueError: Number of samples, -5, must be non-negative.` |
| `config['sep_bins']` given as a 2-D array | `ValueError: object too deep for desired array` |

None of these name the caller's mistake, and none of them is the repo's
convention for an invalid input.

**2. Worse: garbage in, plausible-looking numbers out.** These produce no
exception at all today, just wrong answers with no indication anything happened:

| malformed input | observed behaviour today |
|---|---|
| `catalog['box_size']` of `0.0`, `-5.0` or `nan` | `cKDTree` accepts it and pair finding proceeds against a meaningless periodic box |
| `config['max_sep'] = nan` | every pair is silently missed; `find_pairs` returns the empty result |
| `config['max_sep'] = -1.0` | pairs are still returned, from a negative search radius |
| `config['sep_bins']` unsorted, or containing a duplicate edge or a `NaN` | `np.digitize` accepts it and returns bin indices that do not correspond to the edges |
| 2-D `catalog['x']` / `['y']` / `['z']` | `np.column_stack` produces a 6-column array and the KD-tree silently searches a 6-dimensional space |
| a `mass_bin_width` too large to yield a bin (e.g. `10.0` over a 3 dex range) | every pair is silently assigned `mass_bin = -1` |

Silent wrong answers are the reason this pipeline's house style is to fail
loud. The point of this task is to convert every row of both tables into a
clean, named `AssertionError`.

## Validation and Failure Conventions

Binding throughout.

**Fail loud with `assert` and a clear message naming the offending value.**
Do not introduce a `TypeError` or a `ValueError` for new input validation.

> A `TypeError` / `ValueError` / `KeyError` / `IndexError` /
> `ZeroDivisionError` that *leaks* out of an unguarded operation is **not** a
> valid rejection, even though it fails loudly. It is the exact failure this
> clause exists to prevent, and it is a defect for every input class the
> Required Validation table below lists. For an input class the table does
> **not** list, behaviour stays unspecified and no guard is to be added.

**Validate form before coercion.** A dtype, rank or scalar-type check must run
*before* the value is converted. `np.asarray(x, dtype=float)` placed ahead of a
dtype check silently parses a numeric-looking string and silently discards the
imaginary part of a complex value, which defeats the check entirely. The same
applies to `float(value)` on a 0-D array or a string.

**Validate exactly the conditions in the Required Validation table.** Those are
the only specified behaviour outside the valid input domain. Do not add further
input validation, and do not reject any input the table declares valid — a
guard that rejects a legitimate non-default `config`, an empty catalog, or an
integer-dtype array is a defect, not extra safety.

**Validation runs before any arithmetic and before any early return.** All of
it, on both arguments, at the top of `find_pairs` — not interleaved with the
computation, and not after the "no pairs found" or "no pairs survived the mass
ratio cut" early returns. A malformed catalog that happens to contain no pairs
must still be rejected. Validate `catalog` first, then `config`.

## Required Validation

### `catalog`

`catalog` must be a `dict`. Its seven **required array fields** are `x`, `y`,
`z`, `vx`, `vy`, `vz` and `log_stellar_mass`, plus the required scalar field
`box_size`.

Every required array field must be:

1. **present** — a missing key is rejected;
2. a **`numpy.ndarray`** — a Python `list` or `tuple` is rejected (this is
   what every caller in the repo already passes, and it is what makes the
   dtype check below meaningful without coercing first);
3. of **real integer or floating dtype** (`dtype.kind in "iuf"`) — boolean,
   complex, string, bytes and object dtypes are rejected;
4. **1-D**;
5. the **same length** as the other six;
6. **finite** — no `NaN`, no `inf`.

`box_size` must be present, a **finite positive real numeric scalar**, and
`x`, `y`, `z` must then satisfy `0 <= coord < box_size` (in Mpc, the units
they arrive in) — the half-open interval `cKDTree`'s periodic wrapping
requires. `coord == box_size` is rejected; `coord == 0` is valid.

**Integer and unsigned dtypes are accepted, and must actually work.** An
integer-dtype catalog must return the same values as the float64 catalog
holding the same numbers. That does not happen by itself, because the existing
body does integer arithmetic on whatever it is handed. Three distinct things
go wrong, measured against the current code:

| integer input | what happens today |
|---|---|
| **signed** integer `log_stellar_mass` | `10 ** (m_secondary - m_primary)` raises `ValueError: Integers to negative integer powers are not allowed` |
| **unsigned** integer `log_stellar_mass` | that subtraction wraps to a huge positive, `10 ** huge` overflows to `0`, so `mass_ratio` is `0` and the pair is silently cut — no error, just a missing pair |
| **narrow** (16-bit) integer velocities | `(dv**2).sum()` overflows: at an ordinary `\|dv\| = 500` km/s, `300**2` wraps to `24464` and `400**2` to `28928`, so the reported speed is `231.07` instead of `500` |

Note what is *not* on that list: an unsigned subtraction wrapping is harmless
on its own, because the modular squaring that follows cancels it exactly
(`(2**32 - 3)**2 mod 2**32 == 9`). The velocity fault is a function of the
dtype's **width**, not of the sign of the difference — a 32- or 64-bit
velocity column is already correct at any realistic km/s magnitude. Converting
only the masses fixes the first two rows and leaves the third.

So after validating an array's form,
convert it before use — `np.asarray(arr, dtype=float)` returns a float64 input
unchanged, so this costs the existing float64 callers nothing and changes none
of their results. This is a conversion *after* the form check, which is
precisely what "validate form before coercion" asks for; it is not a licence
to coerce instead of checking.

**A zero-length catalog is valid.** All seven arrays being empty is not an
error: `find_pairs` returns its existing empty-result structure, exactly as it
already does for a catalog with no pairs. Do not add a non-empty requirement.

**Extra keys are ignored and never validated.** `catalog` legitimately carries
other entries — `redshift` from `data_reader`, and `is_paired` (boolean dtype)
and `pair_id` from `generate_test_data.generate_snapshot` — and
`tests/test_statistical.py` passes a dict built that way. Validate the eight
required fields and nothing else.

### `config`

`config` must be a `dict` carrying these seven keys; a missing one is rejected:
`max_sep`, `mass_ratio_min`, `sep_bins`, `log_mass_min`, `log_mass_max`,
`mass_bin_width`, `mass_bin_by`.

| key | required |
|---|---|
| `max_sep` | finite positive real numeric scalar |
| `mass_ratio_min` | finite real numeric scalar, in `[0, 1]` inclusive (`0` and `1` are both valid) |
| `log_mass_min`, `log_mass_max` | finite real numeric scalars, with `log_mass_max > log_mass_min` |
| `mass_bin_width` | finite positive real numeric scalar, and `round((log_mass_max - log_mass_min) / mass_bin_width) >= 1` — i.e. the grid must define at least one mass bin |
| `sep_bins` | see below |
| `mass_bin_by` | **presence only** — see "Behaviour that must not change" |

`sep_bins` must be a `list`, a `tuple` or a `numpy.ndarray`. If it is an
ndarray it must have real integer or floating dtype and be 1-D; if it is a list
or tuple, every element must be a real numeric scalar. Then, whichever form it
came in, it must have **at least 2 edges**, be **finite**, and be **strictly
increasing** (a duplicated edge is rejected).

> `sep_bins` accepts a Python list while the catalog's array fields do not.
> That asymmetry is deliberate, not an oversight: `src/config.py` and
> `tests/test_pair_finder.py` both supply `sep_bins` as a plain list of ints,
> and every caller supplies the catalog fields as ndarrays.

### Order of checks

One value can violate two checks at once, so the precedence that decides
*which* reason gets reported is part of the contract. Only these relationships
are pinned:

- validate `catalog` before `config`;
- validate each argument's `dict` form before looking up any of its keys;
- validate **form before coercion** (see above);
- report an array field's **finiteness before** its position range;
- for `sep_bins`: container / dtype / rank / element form, **then** edge count,
  **then** finiteness, **then** monotonicity;
- for the mass grid: scalar form and finiteness, **then** `mass_bin_width > 0`,
  **then** `log_mass_max > log_mass_min`, **then** the bin count.

**Ordering between distinct keys is otherwise unspecified**, and no test
depends on it. So a `NaN` in `x` must be reported as a finiteness failure
rather than a position-outside-the-box failure, `mass_bin_width = inf` as a
finiteness failure rather than a bin-count failure, and
`sep_bins = [0, nan, 25]` as a finiteness failure rather than a monotonicity
failure — but if `catalog['x']` has a bad dtype *and* `catalog['y']` is
missing, either reason is acceptable.

### Real numeric scalar

Wherever the tables above say "real numeric scalar", the accepted forms are
Python `int` / `float` and NumPy integer / floating scalars. **Booleans,
strings, bytes, complex values, and every `ndarray` (including a 0-D array)
are rejected by assertion before any coercion.** `np.float64(500.0)` and
`np.int64(25)` are valid.

## Rejection messages must name the reason

"Invalid input" is not an acceptable message. Every rejection message must
contain **both**:

- a **name**, namely:
  - for a top-level form failure (the argument itself is not a `dict`), the
    name of the offending **argument** — `catalog` or `config`;
  - for unequal array lengths, **at least one** of the seven array field names
    (which one is up to you — the implementation is free to report whichever
    field it noticed);
  - otherwise, the **name of the offending key**, spelled as it appears in the
    input (`x`, `vz`, `log_stellar_mass`, `box_size`, `max_sep`,
    `mass_ratio_min`, `sep_bins`, `log_mass_min`, `log_mass_max`,
    `mass_bin_width`, `mass_bin_by`);
- and one of these **exact reason tokens**, per condition:

| condition | token the message must contain |
|---|---|
| `catalog` or `config` is not a dict | `dict` |
| required key absent | `missing` |
| array field is not an ndarray | `ndarray` |
| array field has a rejected dtype | `dtype` |
| array field is not 1-D, or `sep_bins` ndarray is not 1-D | `1-D` |
| array fields differ in length | `same length` |
| array field contains `NaN` / `inf` | `finite` |
| position outside `[0, box_size)` | `box` |
| scalar must be positive but is not | `positive` |
| scalar is not finite | `finite` |
| `mass_ratio_min` outside its range | `[0, 1]` |
| `log_mass_max <= log_mass_min` | `greater than` |
| mass grid yields no bin | `at least one mass bin` |
| `sep_bins` has fewer than 2 edges | `at least 2` |
| `sep_bins` not strictly increasing | `strictly increasing` |
| `sep_bins` is not a list, tuple or ndarray | `list, tuple or numpy.ndarray` |
| value has a rejected scalar form (bool / str / bytes / complex / ndarray) | `scalar` |

These tokens are the contract, not a suggestion — they are what makes a
message machine-checkable. Anything else in the message (the offending value,
the shape, a hint) is welcome.

## Behaviour that must not change

- **The numbers.** For every valid **float64** input, `find_pairs` returns
  exactly what it returns today: the same pairs, the same `separation_kpc`
  (minimum-image, in kpc), the same `delta_v`, the same `mass_ratio`, the same
  primary/secondary assignment (`>=`, so ties keep index `i` as primary), the
  same `mass_bin` and `sep_bin`. For a valid **integer- or unsigned-dtype**
  input there is no "today" behaviour to preserve — see the table above — and
  the requirement is instead that it return exactly what its float64 twin
  returns.
- **Both early-return paths.** A catalog whose KD-tree query finds no pairs,
  and a catalog whose pairs are all removed by the `mass_ratio_min` cut, each
  return the existing dict of empty arrays — `float` dtype for the five
  float fields, `int` dtype for `mass_bin` and `sep_bin`. Neither is an error.
- **The `-1` out-of-range sentinel.** A pair whose reference mass falls outside
  `[log_mass_min, log_mass_max]` still gets `mass_bin == -1`, and a pair whose
  separation falls outside `sep_bins` still gets `sep_bin == -1`. Neither is an
  error and neither is validated away.
- **`config['mass_bin_by']`'s existing `ValueError`.** `_assign_mass_bins`
  raises `ValueError` for an unknown strategy, and
  `tests/test_pair_finder.py::TestMassAssignment::test_invalid_mass_bin_by_raises`
  freezes that. Validate that the key is **present**; do **not** validate its
  value, and do not convert that `ValueError` into an `AssertionError`. All
  four existing strategies (`primary`, `secondary`, `mean`, `total`) stay
  valid.
- **Everything the existing suite pins.** `venv/bin/python -m pytest tests/`
  must pass unmodified, including `tests/test_pair_finder.py`,
  `tests/test_geometric.py` and `tests/test_statistical.py`. Those files pass
  catalogs with `box_size = 1.0`, `mass_bin_width = 1.0` and
  `sep_bins = [0, 500, 1000]` — non-default values your validation must
  accept.

## Acceptance Criteria

- **Inputs:** `catalog` and `config` as described above. Behaviour outside the
  declared domain — an input class no table row lists, or intermediate
  overflow at extreme magnitudes — is unspecified and needs no guard.
- **Outputs:** `find_pairs` unchanged in signature (still exactly two
  positional parameters, `catalog` then `config`) and in return value for
  every valid input; an `AssertionError` naming the offending argument or key
  plus the reason for every malformed input listed above.
- **User-visible behaviour:** `pipeline.py` / `calc.run_calculation` behave
  identically on valid data. A malformed catalog on disk that reaches
  `find_pairs` now fails with a named `AssertionError` instead of a `ValueError`
  from inside SciPy.

The **Required Validation** section above is the normative statement of what
must be rejected and accepted, and **Rejection messages must name the reason**
is the normative statement of what each message must contain. These checkboxes
do not restate them; they say what has to be *demonstrably true* of the result.

- [ ] **Every** rejection the Required Validation section requires — for
      **every** required field and key, not a representative sample of them —
      raises `AssertionError`, never `TypeError`, `ValueError`, `KeyError`,
      `IndexError` or `ZeroDivisionError`.
- [ ] **Every** rejection message satisfies the name-plus-token rule for its
      condition.
- [ ] The **Order of checks** precedences all hold.
- [ ] **Nothing the section declares valid is rejected.** Specifically, and
      each of these is tested: a zero-length catalog; integer- and
      unsigned-dtype array fields, which must also return the *same values* as
      the float64 catalog holding the same numbers; extra catalog keys,
      including malformed
      ones; `log_stellar_mass` outside the config mass range, including
      negative finite masses; `sep_bins` as an int list, a float tuple and an
      integer or floating ndarray, and with NumPy-scalar elements; a NumPy
      integer or floating scalar for `box_size` and for every scalar config
      key; `mass_ratio_min` of exactly `0.0` and exactly `1.0`; a position of
      exactly `0` and one just below `box_size`; a non-default mass grid and a
      non-default `sep_bins`.
- [ ] **Validation runs before both early returns**, so a malformed catalog
      that happens to yield no pairs is still rejected.
- [ ] **Everything under "Behaviour that must not change" still holds**, each
      of it tested: the pinned pair properties, the minimum-image separation
      across the periodic boundary, both empty-result early returns with their
      dtypes, both `-1` sentinels, `mass_bin_by`'s existing `ValueError` for an
      unknown value against an `AssertionError` for a missing key, all four
      `mass_bin_by` strategies, and the unchanged two-argument signature.
- [ ] `venv/bin/python -m pytest tests/` passes with 0 failed, including your
      new `tests/test_pair_finder_validation.py`.

## Explicit Non-Goals

- No change to `find_pairs`'s signature, return keys, dtypes or numerical
  results for valid input.
- No validation of `config['mass_bin_by']`'s *value*, and no change to the
  existing `ValueError` (see above).
- No re-checking of what `data_reader.load_galaxy_catalog` owns: it selects on
  the `[log_mass_min, log_mass_max]` mass range and asserts
  `log_stellar_mass >= 0`. `find_pairs` must **not** require its masses to lie
  inside the config mass range (out-of-range masses are the `-1` sentinel's
  whole purpose) and must not add a non-negativity check on masses.
- No validation of `catalog['redshift']`, `config['box_size']`,
  `config['vel_bin_width']`, `config['vel_max']`, `config['data_dir']`,
  `config['results_dir']` or `config['figures_dir']` — `find_pairs` does not
  read any of them.
- No relationship checks between `max_sep` and `sep_bins`, or between
  `max_sep` and `box_size`. Both are legitimate configurations the pipeline
  already uses in different combinations.
- No logging, no warnings module, no custom exception class, no `if ...: raise`
  in place of `assert`.
- No changes to any other file — see the Authorized Surface.

## Authorized Surface

Files you may change:

- `src/pair_finder.py`
- `tests/test_pair_finder_validation.py` (new file — your own test suite)

No other file in the repository should differ from its current committed state
when you are done — including cosmetic re-formatting of lines you did not need
to touch. In particular `tests/test_pair_finder.py` is frozen: it already pins
the behaviour you must preserve, and editing it to accommodate your changes
would be a scope violation, not a fix.

## What "done" means

- `venv/bin/python -m pytest tests/` passes with 0 failed, including your new
  `tests/test_pair_finder_validation.py`.
- Every Acceptance Criteria checkbox above has at least one test in
  `tests/test_pair_finder_validation.py` that would fail if the behaviour it
  names were broken. A test that merely exercises a code path without being
  able to fail on a wrong answer does not count. Note that three of those
  checkboxes are about behaviour you are *preserving* or *not* rejecting, not
  about behaviour you are adding — a suite that covers every rejection and
  nothing else is incomplete.
- You have run a differential lint pass (`ruff`/`pyflakes` or equivalent) over
  your diff and addressed what it finds.
- You have committed your work. There is no second attempt: submit what you
  have when you stop.
