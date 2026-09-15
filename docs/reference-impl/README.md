# Reference implementation — validation evidence, not tracked code

This directory validates this bench's hidden-test partition
(`hidden_tests/slice1/`, `hidden_tests/slice2/`) against a correct
implementation of `docs/MERGER_RATE_PLAN-2SLICE.md`'s Slices 1-2. It holds
no source code: a correct `calc.py`/`config.py`/`merger_rate.py` is fully
and trivially reproducible from `main` within this same repository (see
"Provenance and reconstruction" below), so keeping a permanent, unchanging
copy here would be exactly the dead weight `AGENTS.md`'s "minimum, no dead
code" rule warns against. This README is the durable record of what was
validated and how to redo it.

## Provenance and reconstruction

A correct `calc.py`/`config.py`/`merger_rate.py` for this plan already exists,
permanently, in this same git repository: `main`'s
`eval/tasks/001-merger-rate-feature/reference_solution/`. It already
implements this exact plan's formulas, pinned values, and (per its
`_real_scalar` helper and centred weighted-least-squares fit) its stricter
scalar-form-rejection and numerical-stability requirements — because the
2-slice plan is Task 001's own scientific content restructured into PM
slices (see `README.md`'s "How it works" section). This is *not* the same
situation as `docs/MERGER_RATE_PLAN-2SLICE.md` itself, which is vendored
because it lives in a genuinely different repository (`relative-velocity`)
that could drift out from under a pinned commit; `main` and `pm-eval-v2`
are branches of *this* repository, so `main`'s copy is exactly as durable
as vendoring it here would be, at zero ongoing cost.

To reconstruct and re-validate (e.g. after any future edit to
`docs/MERGER_RATE_PLAN-2SLICE.md` or the hidden tests):

1. `git show main:eval/tasks/001-merger-rate-feature/reference_solution/calc.py`,
   `.../config.py`, and `.../merger_rate.py` — these are byte-identical to
   what this validation used, except for two docstring-wording edits in
   `merger_rate.py`: the module docstring, and the two `Uncertainty follows
   ... plug-in Poisson-error convention` docstrings, changed from "Task
   001's" to "this plan's" (matching this plan's own binding wording in its
   Validation and Failure Conventions section).
2. Check out `relative-velocity` at the plan's pinned base commit
   (`043b13adc264689c376bdd337603e94d5447623a`, see
   `docs/MERGER_RATE_PLAN-2SLICE.provenance.md`) into a fresh disposable
   worktree — the **vendored** `substrate/relative-velocity`, never an
   operator's own separate checkout, so the evidence below stays
   reproducible from this repository alone — and drop the three files
   above into `src/` there.
3. Run `pytest tests/` (the frozen substrate's own suite).
4. Copy `hidden_tests/slice1/*.py` into that worktree and run pytest on
   that directory alone; then the same for `hidden_tests/slice2/*.py`.
   **Run one slice's directory per pytest invocation, never both together**
   — both directories contain a same-named `test_hA.py`/`test_hB.py`, so a
   combined run fails module collection (duplicate basenames, no
   `__init__.py`). Never actually needed operationally: Slice 2 isn't
   graded until Slice 1 is already accepted.

## Current validation status

Following the recipe above, against the unmodified reconstructed reference,
in a disposable worktree of the vendored substrate:

- `pytest tests/`: **80/80 passed** — confirms Slice 1/2's "behaviour that
  must not change" requirement.
- `hidden_tests/slice1/`: **44/44 passed**.
- `hidden_tests/slice2/`: **20/20 passed**.
- **Red check, discrimination at the slice level**: two independent defects
  injected directly into `merger_rate.py` (dropping the `sqrt(N_pairs)` term
  from `compute_pair_fraction`'s `sigma_f_pair`, a Slice 1 defect; and
  flipping `check_slope_consistency`'s comparison operator, a Slice 2
  defect) are each caught only by their own slice's hidden tests — Slice 1's
  catch the first (`test_A05`, `test_E06`) while Slice 2 stays green; Slice
  2's catch the second (`test_C08`, `test_E07`). Confirms each partition
  actually discriminates a broken implementation, not just that it imports
  and runs.
- **Red check, one defect per `end_to_end_science` node**, injected one at a
  time and reverted between each (see `docs/OBLIGATION-GROUPS.md` for what
  each node checks and why):
  - `test_E10` — alpha clipped at `-1.0` before deriving the timescale while
    `expected_slope` echoes the unclipped config: **E10 fails**, and so does
    **E11**, which is expected rather than a leak — its ratio check is
    strictly more sensitive to the same fault.
  - `test_E11` — an alpha-dependent multiplicative normalisation applied to
    every rate (moves the intercept, leaves the log-log slope untouched):
    **only E11 fails**; the other 19 nodes pass. No existing slope or
    consistency assertion can see this fault at all otherwise.
  - `test_E12` — `slope_err` and `intercept` swapped when assembling the
    returned dict: **only E12 fails**; the other 19 pass.
  - `test_E13` — validation's bin count hardcoded to the default 6 while the
    lower-level functions honour the config: **only E13 fails**; the other
    19 pass.

Empirical fixture facts, measured rather than assumed: at
`merger_timescale_alpha = -1.5` all 6 default-grid bins remain eligible
(`consistent is not None`), and at `test_E13`'s grid (`mass_bin_width = 1.0`,
3 bins over `[8.0, 11.0]`, which divides exactly) all 3 are eligible.

## Known deviations from the vendored plan text

A tool-independent review read the plan, the hidden tests, and the
reference implementation directly. Two things worth recording permanently:

- **`test_B03_timescale_pinned`** (`hidden_tests/slice1/test_hA.py`) uses
  `merger_timescale_alpha = -0.5` where the plan's own bullet literally
  writes `-1.0`. Checked directly: `-1.0` is this plan's own *default*
  value for `merger_timescale_alpha` (see Slice 1's config-key additions),
  so the plan's vendored bullet is self-contradictory — it claims "-1.0
  ... distinct from the defaults, so the test cannot pass by coincidence"
  while citing a value that *is* the default, which would let a broken
  implementation that ignores `config["merger_timescale_alpha"]` entirely
  still pass. `main`'s own Task 001 `spec.md` (the plan's source, before
  restructuring) uses `-0.5` for the identical bullet, correctly distinct
  from the default. This is a transcription defect introduced when the
  plan was restructured from Task 001, not something to fix by editing the
  hidden test to match it — the existing test (unmodified, `-0.5`) already
  implements the bullet's actual intent correctly. Left as-is and recorded
  here rather than silently worked around, since the vendored plan copy is
  deliberately frozen (`AGENTS.md`) and not ours to edit.
- **The plan requires the printed console summary, not just the returned
  dicts, to report the tracked `expected_slope`** (plan §"Validation and
  Failure Conventions"). `test_E10` checks only the returned dicts. Every
  presentation-insensitive formulation of the printed check either accepts
  a stale value or rejects a correctly-but-differently formatted one — a
  labelled inline value (`expected=0.700000`) is straightforward to match,
  but an unlabelled table column (`f"{expected_slope:11.4f}"`) is not
  distinguishable from an arbitrary number by regex alone. Recorded rather
  than closed with a format-sensitive regex. If it is closed later, it
  belongs in `consistency_gate_and_reporting_contract` (the
  reporting-contract group), and must be validated against both a tabular
  and an inline implementation before being trusted.

An unused `_MR_ERR` variable in each hidden-test file's import-guard is
inherited verbatim from Task 001's original hidden tests and left alone —
a single cosmetic unused local in test-fixture code that is otherwise meant
to stay byte-identical to its source.
