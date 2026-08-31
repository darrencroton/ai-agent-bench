# Task 002: Pair-to-Mass-Bin Assignment Conventions

> **This is a single-shot evaluation task. Read this document once, implement
> everything it describes in one sitting, and submit your final diff. There is
> no slice-by-slice checkpoint, no reviewer, and no correction round — nobody
> will read your work and hand it back for another attempt. Decide your own
> validation, run it yourself, and stop when you believe the Acceptance
> Criteria below are met.**

## Purpose

Add `src/pair_binning.py`, which recomputes close-pair statistics per stellar-mass
bin under **more than one pair-to-bin assignment convention**, from pair catalogs
that `calc.py` has already written, and compares those conventions against each
other.

`docs/BACKGROUND.md` §4.2 lists five candidate rules for deciding which stellar
mass a galaxy pair is binned by. The pipeline currently hard-freezes one of them
at calculation time (`config["mass_bin_by"]`, written into every results file and
baked into that file's `mass_bin` dataset). That makes it impossible to ask the
obvious scientific question — *how much does the answer depend on the
convention?* — without re-running pair finding once per convention.

This task removes that limitation for three of the five rules, and requires you
to work out **what the pair fraction's denominator means under each of them**.
That denominator is the substance of this task. It is deliberately not handed to
you as a formula; the properties it must satisfy are stated below and are
sufficient to determine it.

This delivers the computational core only. **Plotting, CLI flags, and
documentation updates are out of scope** and are not restated below: the outputs
are a results file, a returned list of per-redshift result dicts, and a console
summary, consumed directly or by a later presentation layer.

## Scientific Background

See `docs/BACKGROUND.md` §4.2 ("Which Mass Defines the Bin?"), §4.3 (mass-ratio
cut) and §10 (resolved design decisions).

**1. Close pairs are already defined by the pipeline.** Every row in
`results/pairs_z{z}.hdf5` is a pair within `config["max_sep"]` kpc 3D separation
with mass ratio `>= config["mass_ratio_min"]`, de-duplicated by
`cKDTree.query_pairs`'s `i < j` indexing, so each unordered pair appears exactly
once. Each row records `mass_primary` (the more massive member's
`log10(M_star/M_sun)`) and `mass_secondary` (the less massive member's).
`mass_secondary <= mass_primary` holds for every row by construction. **This task
adds no new pair finding and re-applies no mass-ratio cut**: the stored rows are
the pair sample, exactly as they are.

**2. The stored `mass_bin` dataset is frozen at the wrong level for this
question.** `calc.py` calls `pair_finder._assign_mass_bins` once, under whatever
`config["mass_bin_by"]` was in force, and stores the result. Recomputing bin
assignment from the stored `mass_primary` / `mass_secondary` columns is what makes
a convention comparison possible without re-running pair finding.

Consequently: **`src/pair_binning.py` must never read the stored `mass_bin`
dataset, must never read the stored `mass_bin_by` attr, and must never read
`config["mass_bin_by"]`.** Those three record the convention frozen at
calculation time; this module's whole point is that it is not bound by it. They
are also not to be *validated* — a results file whose `mass_bin_by` attr says
`"total"` and whose `mass_bin` dataset is nonsense is still a perfectly usable
input to this module, and must be processed without complaint.

**3. Bin edges.** Mass bin edges are
`numpy.linspace(config["log_mass_min"], config["log_mass_max"], n_bins + 1)` with
`n_bins = round((log_mass_max - log_mass_min) / mass_bin_width)`, and assignment
is right-open via `numpy.digitize`, exactly as `pair_finder._mass_bin_edges` /
`pair_finder._assign_mass_bins` already do: a mass exactly equal to
`config["log_mass_max"]` falls **outside every bin**. `data_reader`'s selection
mask is inclusive of `log_mass_max`, so a selected galaxy can legitimately sit in
no bin at all. That inconsistency is pre-existing and **this task does not fix
it**; what matters is that every count this task produces — numerator and
denominator alike — uses the identical right-open rule.

**4. Conventions and the incidence set.** This task supports exactly three of
`docs/BACKGROUND.md` §4.2's five options, named `"primary"`, `"secondary"` and
`"either"`.

Define, for a convention `C` and a mass bin `b`, the **incidence set**
`I(C, b)`: the set of `(pair p, member g of p)` combinations that convention `C`
places in bin `b`.

```text
I("primary",   b) = { (p, g) : g is p's more massive member, and g's mass is in bin b }
I("secondary", b) = { (p, g) : g is p's less massive member, and g's mass is in bin b }
I("either",    b) = { (p, g) : g is either member of p,      and g's mass is in bin b }
```

The numerator is the size of that set:

```text
N_pairs(C, b) = |I(C, b)|
```

A pair whose two members are exactly equal in mass still has one more-massive
member and one less-massive member: `find_pairs` breaks that tie when it writes
`mass_primary` / `mass_secondary`, and this module takes the columns as given.
The two members are distinct galaxies in every case.

**5. The denominator — the decision this task turns on.** The pair fraction is

```text
f_pair(C, b) = N_pairs(C, b) / N_gal(C, b)
```

`N_gal` is **not** given to you as a formula. It is fixed by these three binding
properties, which your implementation must satisfy:

- **D1.** `f_pair(C, b)` is a **per-galaxy incidence rate**: the mean number of
  incidences in `I(C, b)` per galaxy that is *capable of supplying* one. It is
  not a probability and is not bounded by 1 — one galaxy can appear in several
  stored pairs, so `f_pair > 1` is legal in a crowded bin.
- **D2.** The denominator is a count of **individual galaxies drawn from the full
  mass-selected catalog** — paired *and* unpaired — assigned to bins by that
  galaxy's own stellar mass under the §3 rule. It is never derived from the pair
  catalog, and it counts each galaxy at most once.
- **D3.** A convention admits a denominator at all only if the quantity it bins
  by is a property of **one** galaxy. `"total"` — `docs/BACKGROUND.md` §4.2's
  candidate 3, the pair mass `M1 + M2` — and `"mean"` — a `config["mass_bin_by"]`
  value accepted by the frozen pipeline but not itself one of §4.2's five named
  candidates — both bin on a joint quantity of both members, which is not a
  property of any single galaxy, so no single-galaxy denominator exists for
  either and this module rejects both. `"primary"`, `"secondary"` and `"either"`
  all bin on one galaxy's own mass and are supported.

Work out from D1–D3 what `N_gal` is for each of the three supported conventions,
implement that, and make the module's public API and its output file schema
reflect the answer. The API and schema stated in Parts 1–3 below are consistent
with the correct answer and with no other; if you find yourself needing a shape
those sections do not provide, re-read D1–D3.

**6. Uncertainty.** `N_pairs` is treated as Poisson-distributed; `N_gal` as an
exact count (it is the full mass-selected sample, not a subsample).

```text
sigma_f_pair(C, b) = f_pair(C, b) / sqrt(N_pairs(C, b))   if N_pairs > 0, else 0
```

The `N_pairs == 0` case is exactly zero — not `nan`, not a divide-by-zero. This
is a **plug-in point-estimate simplification for downstream fitting, not a
rigorous Poisson confidence interval**; small-`N` Poisson intervals (e.g.
Gehrels) are out of scope. Under `"either"` the numerator counts incidences
rather than independent pairs, and the two incidences a both-members-in-bin pair
contributes are manifestly not independent, so the approximation is weaker there
still. Code and docstrings must describe this as *this task's convention*, never
as "the Poisson uncertainty" unqualified.

**7. The additivity identity.** Every pair has exactly one more massive member
and exactly one less massive member, and `"either"` selects both. Therefore, for
every bin `b`, on any pair sample whatsoever:

```text
N_pairs("primary", b) + N_pairs("secondary", b) == N_pairs("either", b)
```

exactly, in integers, with no tolerance. This holds even when a member's mass
falls outside every bin: such a member simply contributes no incidence anywhere,
on both sides of the identity.

This is a **theorem about the counting rule, not a property of the data**. An
implementation that satisfies it on one catalog and violates it on another has a
counting bug, not an interesting result. Part 3 requires it to be checked at
runtime and the outcome recorded — as a self-consistency check on the
implementation, and it is expected to hold on every input.

The companion **exclusion sum rule**, for `C` in `{"primary", "secondary"}`:

```text
sum over b of N_pairs(C, b)  +  n_excluded_pairs(C)  ==  total stored pairs
```

where `n_excluded_pairs(C)` is the number of stored pairs contributing **no**
incidence to **any** bin under `C`. For `"either"` the same definition of
`n_excluded_pairs` applies (a pair neither of whose members lands in a bin), but
the sum rule above does not, because a pair can contribute two incidences.

## Architecture Fit

- New file `src/pair_binning.py`, structured like `plot.py`: reads already-written
  data and results files and writes its own outputs; it does not re-run pair
  finding.
- Per existing repo convention (`_mass_bin_edges` is already duplicated
  independently in `pair_finder.py` and `plot.py`), `pair_binning.py` defines its
  own local `_mass_bin_edges(config)` rather than importing a private helper, and
  implements its own bin assignment rather than calling
  `pair_finder._assign_mass_bins`. The latter is not merely a style point: that
  helper raises `ValueError` for an unknown strategy and knows nothing about
  `"either"`, and `pair_finder.py` is frozen by this task.
- The galaxy catalog is read through `data_reader.load_galaxy_catalog`, which
  already applies the `[log_mass_min, log_mass_max]` selection. Do not re-implement
  catalog loading or re-apply the selection.
- All tunable scientific parameters live in `config.py` and are passed explicitly.
  Frozen filenames (`pairs_z{z:.1f}.hdf5`, `test_z{z:.1f}.hdf5`,
  `pair_binning.hdf5`) may be local constants or f-strings — API choices, not
  hidden scientific inputs.
- Units follow the existing convention: masses in `log10(M_star/M_sun)`,
  separations in kpc, positions in Mpc. This task introduces no new units and no
  new unit conversions.

## Validation and Failure Conventions

Binding throughout.

**Fail loud with `assert` and a clear message naming the offending value.** This
matches the repo's house style: use assertions with clear messages for invalid
inputs. The rule governs **validation newly introduced by this task**; it is not
a licence to change existing behaviour. In particular
`pair_finder._assign_mass_bins` raises `ValueError` for an unknown `mass_bin_by`
and `tests/test_pair_finder.py` freezes that, so it stays as it is. Do not
introduce `TypeError` / `ValueError` raises for new input validation.

> A `TypeError` or `ValueError` that *leaks* from an unguarded coercion —
> `float(attr)` on a vector or a `None` — is **not** a valid rejection, even
> though it fails loudly. It is the exact failure this clause and *Validate form
> before coercion* below exist to prevent, so it is a defect wherever the value
> is one the Acceptance Criteria require it to reject. Where the Criteria do
> **not** list the input class, its behaviour stays unspecified and no guard is
> to be added — the two rules do not conflict: this note governs *how* a listed
> rejection must happen, not *which* inputs are rejected.

Missing-file behaviour: `data_reader.load_galaxy_catalog` already asserts on a
missing catalog file, and this task's own file-reading entry points must assert
too, naming the offending path.

**Validate form before coercion.** Where a dtype or shape check is required, it
must run *before* the value is converted: `np.asarray(x, dtype=float)` placed
ahead of a dtype check silently parses a numeric-looking string or discards an
imaginary part, which defeats the check entirely.

**Validate exactly the rejection conditions explicitly listed in the Acceptance
Criteria below.** Those rejections are the only specified behaviour outside the
valid input domain; all other out-of-domain behaviour, including intermediate
overflow at extreme magnitudes, is unspecified. Do not add further input
validation, and do not reject any declared-valid value — a guard that rejects a
zero-length pair array, or a results file whose `mass_bin_by` attr names a
convention this module does not support, is a defect.

## Test Isolation

- Tests in `tests/test_pair_binning.py` use a copied config whose `data_dir` and
  `results_dir` point beneath pytest's `tmp_path` / `tmp_path_factory`. Tests must
  never read or overwrite the repository's gitignored `data/` or `results/`.
- The generated-mock integration fixture calls `generate_all_snapshots(config)`
  and `run_calculation(config)` directly with those temporary directories. It may
  be module-scoped so the four-snapshot setup is shared. "Generated mock data"
  below always means this isolated fixture, never shelling out to the CLI.

---

## Part 1: Convention-aware counting and the pair fraction

### Intended Change

Create `src/pair_binning.py` with:

- `_mass_bin_edges(config)` — local copy of the standard formula (§3).
- `_data_path(z, config)` — `os.path.join(config["data_dir"], f"test_z{z:.1f}.hdf5")`,
  matching `calc.py`.
- `_results_path(z, config)` — `os.path.join(config["results_dir"], f"pairs_z{z:.1f}.hdf5")`,
  matching `calc.py` / `plot.py`.
- `count_galaxies_per_mass_bin(log_stellar_mass, config)` — the denominator's
  underlying count, over an array of individual galaxy masses. Returns a 1D array
  of integer dtype and length `n_mass_bins`, in bin-index order.
- `count_pairs_per_mass_bin(log_mass_primary, log_mass_secondary, convention, config)`
  — the numerator, `N_pairs(convention, b)` per §4. Returns a 1D array of integer
  dtype and length `n_mass_bins`, in bin-index order.
- `count_excluded_pairs(log_mass_primary, log_mass_secondary, convention, config)`
  — the number of stored pairs contributing no incidence to any bin under
  `convention` (§7). Returns a Python or NumPy integer scalar.
- `compute_pair_fraction(n_pairs, n_galaxies)` — vectorized over the mass-bin
  array, returns `(f_pair, sigma_f_pair)` per §5 and §6 as float arrays of the
  input shape.
- `check_additivity(n_primary, n_secondary, n_either)` — pure; returns `True` if
  the §7 identity holds elementwise and `False` otherwise. A violation is a
  return value, never an exception.

`convention` is an explicit argument on every function that needs one. It is
never read from `config` — see §2.

### Acceptance Criteria — Part 1

- **Inputs:** `config` (existing keys only for this part). Declared input domain:
  `log_stellar_mass`, `log_mass_primary` and `log_mass_secondary` are 1D, finite,
  real-valued numeric arrays; the two pair arrays are identically shaped and
  satisfy `log_mass_secondary <= log_mass_primary` elementwise. Zero-length arrays
  are **valid** input. For `compute_pair_fraction`, `n_pairs` and `n_galaxies` are
  1D, identically shaped, finite, non-negative and integer-valued, with counts
  below `2**53`. Behaviour outside those domains is unspecified, and implementers
  need not guard overflow or underflow of intermediate products for
  out-of-domain magnitudes.
- **Outputs:** `pair_binning.py` exposing `_mass_bin_edges`, `_data_path`,
  `_results_path`, `count_galaxies_per_mass_bin`, `count_pairs_per_mass_bin`,
  `count_excluded_pairs`, `compute_pair_fraction` and `check_additivity` as
  importable, directly testable functions.
- **User-visible behaviour:** none in this part; nothing is reached through the
  CLI.
- **Behaviour that must not change:** every existing file outside the Authorized
  Surface, and all existing tests in `tests/test_geometric.py`,
  `tests/test_pair_finder.py`, `tests/test_statistical.py` pass unmodified.

- [ ] With the default config, `count_galaxies_per_mass_bin` on
      `[7.99, 8.0, 8.499, 8.5, 9.75, 10.5, 10.9999, 11.0]` returns exactly
      `[2, 1, 0, 1, 0, 2]`, with an integer dtype — the exact upper edge is
      excluded, an interior edge value is assigned to the upper adjacent bin, and
      a value below `log_mass_min` is excluded.
- [ ] Every bin edge and every count length is derived from `config`'s
      `log_mass_min`, `log_mass_max` and `mass_bin_width`, never from their
      default values: with those three set to `9.0`, `12.0` and `1.5`,
      `_mass_bin_edges` returns exactly `[9.0, 10.5, 12.0]` and every count
      vector this task produces has length 2, with
      `count_galaxies_per_mass_bin([8.9, 9.0, 10.4, 10.5, 11.9, 12.0], config)`
      returning `[2, 2]`.
- [ ] `count_galaxies_per_mass_bin` does **not** depend on any convention: it
      returns the same counts when `config` has no `mass_bin_by` key at all, and
      when `config["mass_bin_by"]` is set to each of `"primary"`, `"secondary"`,
      `"mean"`, `"total"` and a nonsense string. It must not raise in any of those
      cases.
- [ ] With the default config and the pair sample
      `log_mass_primary = [8.2, 9.7, 10.6, 11.0, 10.2, 11.0]`,
      `log_mass_secondary = [8.1, 8.9, 10.6, 10.4, 9.5, 11.0]`,
      `count_pairs_per_mass_bin` returns integer-dtype arrays that satisfy §4 and
      §7 for all three conventions, and `count_excluded_pairs` returns the §7
      count for each. The three count vectors are distinct from each other, and
      the `"either"` vector is *not* equal to either of the other two.
- [ ] On that same sample, `check_additivity` on the three returned vectors is
      `True`, and the exclusion sum rule of §7 holds for `"primary"` and
      `"secondary"` against the sample's 6 pairs.
- [ ] A pair whose two members fall in the **same** bin and a pair whose members
      fall in **different** bins are both handled per §4, and the totals differ
      between `"either"` and the single-member conventions as §7 requires. An
      implementation that counts a both-members-in-bin pair once under `"either"`
      fails the additivity check above.
- [ ] Zero-length `log_mass_primary` / `log_mass_secondary` return an all-zero
      count vector of length `n_mass_bins` and `count_excluded_pairs == 0`, for
      every convention, without raising.
- [ ] `count_pairs_per_mass_bin` and `count_excluded_pairs` reject, with an
      assertion naming the reason: `convention` values `"mean"`, `"total"`, any
      other unknown string, and any non-string; mismatched array shapes; non-1D
      input; non-finite masses; complex or otherwise non-real numeric input; and
      any element with `log_mass_secondary > log_mass_primary`.
- [ ] `count_galaxies_per_mass_bin` rejects, with an assertion naming the reason:
      non-1D input, non-finite values, and complex or otherwise non-real numeric
      input.
- [ ] `compute_pair_fraction([0, 4, 9], [4, 16, 4])` returns
      `f_pair == [0.0, 0.25, 2.25]` and `sigma_f_pair == [0.0, 0.125, 0.75]`, with
      non-zero floating values compared using `rtol=1e-14, atol=0` so
      algebraically equivalent floating-point evaluation orders are accepted.
- [ ] A bin with `n_pairs == 0` and `n_galaxies == 0` yields `f_pair == 0` and
      `sigma_f_pair == 0` exactly — not `nan`, not `inf`. This must hold on every
      path.
- [ ] `compute_pair_fraction` asserts that every bin with `n_pairs > 0` has
      `n_galaxies > 0`, since an incidence cannot exist in a bin with no galaxies.
- [ ] `compute_pair_fraction` rejects, with an assertion naming the reason:
      mismatched shapes, non-1D input, negative counts, non-finite counts,
      non-integer-valued counts, and complex or otherwise non-real numeric
      input. Integer dtypes and integer-valued float64 are both valid input and
      must be accepted.
- [ ] `compute_pair_fraction`'s docstring contains this exact sentence:
      "Under the 'either' convention the numerator counts galaxy-pair incidences
      rather than independent pairs, so this plug-in Poisson error is an
      approximation and not a confidence interval."
- [ ] `check_additivity` returns `False` — it does not raise — when the identity
      is violated, and `True` when it holds, including for all-zero vectors. It
      rejects, with an assertion, non-1D inputs, mismatched shapes, non-finite
      values, negative values, non-integer-valued input, and complex or
      otherwise non-real numeric input.
- [ ] `venv/bin/python -m pytest tests/` passes with 0 failed.

### Explicit Non-Goals — Part 1

- No file I/O in any Part 1 function.
- No support for `"mean"` or `"total"` (§5, D3).
- No changes to `pair_finder.py`, `calc.py`, `data_reader.py`, `plot.py`,
  `generate_test_data.py`, or `pipeline.py`.
- No re-application of the mass-ratio cut, the separation cut, or the catalog
  mass selection (§1).

---

## Part 2: Per-snapshot loading and provenance

### Intended Change

Add to `config.py`, under a `# Pair-binning comparison` section:

- `pair_binning_conventions = ["primary", "secondary", "either"]` — the
  conventions Part 3 compares, in the order they are reported and persisted.

Add to `src/pair_binning.py`:

- `load_snapshot_counts(z, config)` — assembles one redshift's raw counts from
  disk. Returns a dict with **exactly** these keys:

  | key | value |
  |---|---|
  | `redshift` | `float(z)`, the configured redshift |
  | `n_galaxies` | 1D integer array, length `n_mass_bins` |
  | `n_pairs` | dict `{convention: 1D integer array of length n_mass_bins}` |
  | `n_excluded_pairs` | dict `{convention: int}` |
  | `n_pairs_total` | `int`, the number of stored pair rows |

  The two dicts have one entry per convention in
  `config["pair_binning_conventions"]`, and no others.

  `n_galaxies` comes from `data_reader.load_galaxy_catalog(_data_path(z, config), config)`
  — the **full mass-selected catalog**, paired and unpaired galaxies alike — via
  `count_galaxies_per_mass_bin`. `n_pairs` and `n_excluded_pairs` come from the
  results file's `mass_primary` and `mass_secondary` datasets via the Part 1
  functions. Note what the table does and does not have a convention axis on; §5
  D1–D3 say why.

  Validation, all by assertion, all naming the offending value or path:

  - `config["pair_binning_conventions"]` is a non-empty list or tuple of strings,
    each one of `"primary"`, `"secondary"`, `"either"`, with no duplicates.
  - The data file `_data_path(z, config)` exists.
  - The results file `_results_path(z, config)` exists.
  - The results file contains the datasets `mass_primary` and `mass_secondary`,
    each 1D and of equal length.
  - The results file's `redshift`, `mass_ratio_min` and `max_sep_kpc` attrs are
    present, and each equals the configured `z`, `config["mass_ratio_min"]` and
    `config["max_sep"]` respectively. A stored pair sample cut at a different
    mass ratio or separation is not comparable with the configured one, so it is
    rejected rather than silently mixed in. Validate each attr's dtype and scalar
    shape **before** coercion, so a malformed string or vector attr is reported
    rather than crashing on comparison. Accepted scalar forms are Python or NumPy
    integer/floating scalars, excluding booleans; strings, bytes, complex values
    and non-scalar arrays are rejected. HDF5 normalizes a stored 0D numeric array
    to a NumPy scalar on read, so the read value is governed by its observable
    form.

  Per §2, `load_snapshot_counts` reads neither the `mass_bin` dataset nor the
  `mass_bin_by` attr, and neither is validated.

### Acceptance Criteria — Part 2

- **Inputs:** `config` with the new key; on-disk `data/test_z{z}.hdf5` as written
  by `generate_test_data.py` and `results/pairs_z{z}.hdf5` as written by
  `calc.py`, both unmodified by this task.
- **Outputs:** `load_snapshot_counts` importable and independently callable,
  returning the dict above.
- **User-visible behaviour:** none in this part.
- **Behaviour that must not change:** everything validated in Part 1; `calc.py`
  and the schema of the files it writes are untouched.

- [ ] The new config key is added and no existing key changes in value or
      meaning. `config["mass_bin_by"]` in particular is left at `"primary"`.
- [ ] On generated mock data, `load_snapshot_counts` returns a dict whose keys are
      exactly the five named in the table above, with `n_pairs` and
      `n_excluded_pairs` keyed by exactly the configured conventions and
      `n_galaxies` carrying **no** convention axis.
- [ ] On generated mock data, `sum(n_galaxies)` equals the number of galaxies in
      the loaded catalog whose mass satisfies
      `log_mass_min <= mass < log_mass_max` — drawn from the full selected
      catalog, not from galaxies appearing in pairs, and below `data_reader`'s
      inclusive selected count whenever a galaxy sits exactly at
      `log_mass_max`.
- [ ] On generated mock data, for every redshift: `check_additivity` holds on the
      three returned count vectors, and the §7 exclusion sum rule holds against
      `n_pairs_total` for `"primary"` and `"secondary"`.
- [ ] `n_pairs_total` equals the number of rows in the results file's
      `mass_primary` dataset.
- [ ] **The stored bin assignment is provably not used:** against a fixture whose
      `mass_bin` dataset is overwritten with values inconsistent with
      `mass_primary` / `mass_secondary` and whose `mass_bin_by` attr is set to
      `"total"`, `load_snapshot_counts` returns exactly the same counts as against
      the unmodified fixture, and does not raise. An implementation reading
      `mass_bin` or `mass_bin_by` fails this.
- [ ] **The per-convention counts provably vary with the convention:** on a
      hand-written fixture, the `"secondary"` and `"either"` count vectors differ
      from the `"primary"` one, and each matches the value hand-computed from the
      fixture's own `mass_primary` / `mass_secondary` columns.
- [ ] `load_snapshot_counts` honours `config["pair_binning_conventions"]`: with a
      single-entry list, exactly one entry appears in `n_pairs` and
      `n_excluded_pairs`; with a two-entry list, exactly those two, in that order.
- [ ] `load_snapshot_counts` rejects, by assertion: a missing data file, a missing
      results file, a missing `mass_primary` or `mass_secondary` dataset, unequal
      dataset lengths, a missing `redshift` / `mass_ratio_min` / `max_sep_kpc`
      attr, a `redshift` attr that disagrees with the configured `z`, a
      `mass_ratio_min` attr that disagrees with `config["mass_ratio_min"]`, a
      `max_sep_kpc` attr that disagrees with `config["max_sep"]`, and a malformed
      (string, bytes, complex or non-scalar) value for any of those three attrs.
- [ ] `load_snapshot_counts` rejects, by assertion, a
      `config["pair_binning_conventions"]` that is empty, contains a duplicate,
      contains an unsupported name such as `"mean"` or `"total"`, contains a
      non-string, or is not a list or tuple.
- [ ] `venv/bin/python -m pytest tests/` passes with 0 failed.

### Explicit Non-Goals — Part 2

- No writing of any file in this part.
- No changes to `calc.py` or to the schema of `results/pairs_z{z}.hdf5`.
- No provenance checks beyond `redshift`, `mass_ratio_min` and `max_sep_kpc`;
  bin-edge and box-size cross-validation are deliberately out of scope.
- No caching of loaded catalogs between calls.

---

## Part 3: Convention comparison, invariant check, and persistence

### Intended Change

Add to `src/pair_binning.py`:

- `run_binning_comparison(config)` — the driver.

  **Order of operations is binding.** First validate
  `config["pair_binning_conventions"]` as in Part 2. Then, **before opening the
  output for writing**, preflight every configured redshift: assert that both
  `_data_path(z, config)` and `_results_path(z, config)` exist, naming the first
  absent path, and assert each results file's `redshift`, `mass_ratio_min` and
  `max_sep_kpc` attrs are present, well-formed and in agreement with the config,
  under the same before-coercion form validation as Part 2. **A failure at this
  gate must leave any pre-existing `pair_binning.hdf5` byte-for-byte untouched.**

  Then for each `z` in `config["redshifts"]`, in order: `load_snapshot_counts`,
  then `compute_pair_fraction` per configured convention against the
  convention-appropriate denominator from §5.

  Compute per redshift an `additivity_holds` value: `check_additivity` on the
  three count vectors when **all three** conventions are configured, and `None`
  when they are not — the identity is not defined on a subset, and reporting
  `False` for "not checked" would be a false alarm.

  Write `os.path.join(config["results_dir"], "pair_binning.hdf5")`, creating
  `config["results_dir"]` if needed, containing — with
  `nz = len(config["redshifts"])`, `nc = len(config["pair_binning_conventions"])`
  and `nb = n_mass_bins`:

  | dataset | shape | dtype |
  |---|---|---|
  | `n_galaxies` | `(nz, nb)` | integer |
  | `n_pairs` | `(nz, nc, nb)` | integer |
  | `pair_fraction` | `(nz, nc, nb)` | float |
  | `pair_fraction_err` | `(nz, nc, nb)` | float |
  | `n_excluded_pairs` | `(nz, nc)` | integer |

  plus attrs `redshifts` (float array, in config order), `conventions` (string
  array, in config order), `mass_bin_edges` (float array of length `nb + 1`),
  `mass_ratio_min`, `max_sep_kpc`, `timestamp` (timezone-aware ISO 8601, mirroring
  `_save_pairs`'s provenance pattern), and `additivity_checked` (bool).
  `additivity_holds` (bool, the logical AND over redshifts) is written **only
  when** `additivity_checked` is `True`, so a reader cannot mistake "not checked"
  for "checked and failed".

  Note again the shape of `n_galaxies` relative to the other datasets; §5 D1–D3
  say why it is what it is.

  Print a summary to stdout:

  - A heading containing this exact sentence:
    "N_gal(b) is the same galaxy count for every convention; only the numerator
    changes."
  - One line per (redshift, convention) pair, in redshift-major order, each
    containing the tokens
    `z=<redshift with one decimal place>`, `convention=<name>`,
    `n_galaxies=<sum over bins>`, `n_pairs=<sum over bins>` and
    `n_excluded=<integer>`. Leading whitespace and additional text on the line are
    permitted; the tokens themselves are not.
  - One line per redshift containing `z=<redshift with one decimal place>` and
    `additivity=holds`, `additivity=FAILED` or `additivity=not_checked`.

  Return a list of per-redshift dicts, in config redshift order, each with
  **exactly** these keys: `redshift`, `n_galaxies`, `n_pairs`, `pair_fraction`,
  `pair_fraction_err`, `n_excluded_pairs`, `additivity_holds`. `n_galaxies` is a
  1D integer array; `n_pairs`, `pair_fraction`, `pair_fraction_err` and
  `n_excluded_pairs` are dicts keyed by the configured conventions;
  `additivity_holds` is a bool or `None`.

### Acceptance Criteria — Part 3

- **Inputs:** `config` as in Part 2, plus the on-disk inputs it names.
- **Outputs:** `run_binning_comparison` importable and independently callable;
  `results/pair_binning.hdf5` as specified; the console summary; and the returned
  list of per-redshift dicts.
- **User-visible behaviour:** `run_binning_comparison(config)` prints the labelled
  summary. Nothing is reached through the CLI.
- **Behaviour that must not change:** everything validated in Parts 1-2.

- [ ] On generated mock data, the written file contains every dataset and attr in
      the schema above with the stated shapes and dtype kinds; `n_galaxies` has
      **no** convention axis; redshift, convention and mass-bin ordering are
      preserved; and `pair_fraction` and `pair_fraction_err` are finite and
      non-negative everywhere.
- [ ] The persisted `n_pairs`, `pair_fraction`, `pair_fraction_err`,
      `n_excluded_pairs` and `n_galaxies` agree element-by-element with the values
      in the returned list of dicts, and the returned dicts have exactly the seven
      keys named above.
- [ ] The persisted `pair_fraction` equals `n_pairs / n_galaxies` per element
      (with the §6 zero conventions), computed against the **same** `n_galaxies`
      row for all three conventions at a given redshift — compared using
      `rtol=1e-14, atol=0` for non-zero values and exact equality for zeros.
- [ ] On generated mock data, `additivity_checked` is `True`, `additivity_holds`
      is `True`, and every returned dict's `additivity_holds` is `True`.
- [ ] **`conventions` tracks `config["pair_binning_conventions"]`:** running with
      `["secondary", "primary"]` writes exactly those two names in that order,
      gives `nc == 2`, omits the `additivity_holds` attr, sets
      `additivity_checked` to `False`, sets every returned dict's
      `additivity_holds` to `None`, and yields per-convention rows that match the
      corresponding rows from the three-convention run. A hardcoded convention
      list anywhere in the call chain fails this.
- [ ] Running with a single-redshift `config["redshifts"]` gives `nz == 1` and
      values matching that redshift's row from the full run.
- [ ] The preflight gate leaves a sentinel output file byte-for-byte unchanged on
      every failure path — a missing data file, a missing results file, a
      mismatched recorded `redshift`, a mismatched `mass_ratio_min`, a mismatched
      `max_sep_kpc`, and a malformed `redshift` attr — compared by SHA-256 of the
      file contents, not by its size.
- [ ] An invalid `config["pair_binning_conventions"]` (empty, duplicated,
      unsupported name, non-string element, or not a list/tuple) fails by
      assertion and likewise leaves a sentinel output file byte-for-byte
      unchanged.
- [ ] The console summary's heading contains the exact sentence required above;
      every (redshift, convention) line contains all five required tokens with
      values matching the returned dicts; and every redshift has an
      `additivity=` line reporting `holds` on generated mock data and
      `not_checked` in the two-convention run.
- [ ] **End-to-end on generated mock data:** after `generate_all_snapshots` and
      `run_calculation`, `run_binning_comparison` reproduces, for every redshift
      and every configured convention, counts recomputed independently in the test
      from the results file's `mass_primary` / `mass_secondary` columns and the
      catalog's `log_stellar_mass`, element by element. This is the scientific
      assertion of the task and must be allowed to fail loudly if the counting or
      the denominator is wrong.
- [ ] `venv/bin/python -m pytest tests/` passes with 0 failed.

### Explicit Non-Goals — Part 3

- No Matplotlib import anywhere in this task.
- No re-running of pair finding, and no modification of
  `results/pairs_z{z}.hdf5`.
- No `"mean"` or `"total"` convention, and no fifth convention beyond the three
  named.
- No merger-rate conversion, timescale model, volume normalization, or redshift
  fitting — this task compares conventions, nothing more.
- No changes to `src/config.py` beyond Part 2's single key.

---

## Authorized Surface (all parts combined)

Files you may change: `src/config.py`, `src/pair_binning.py`,
`tests/test_pair_binning.py`. No other file in the repository should differ from
its current committed state when you are done — including cosmetic re-formatting
of lines you did not need to touch.

## What "done" means

- `venv/bin/python -m pytest tests/` passes with 0 failed, including your new
  `tests/test_pair_binning.py`.
- Every Acceptance Criteria checkbox above has at least one test that would fail
  if the behaviour it names were broken. A test that merely exercises a code
  path without being able to fail on a wrong answer does not count.
- You have run a differential lint pass (`ruff`/`pyflakes` or equivalent) over
  your diff and addressed what it finds.
- You have committed your work. There is no second attempt: submit what you
  have when you stop.
