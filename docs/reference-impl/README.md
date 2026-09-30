# Reference implementation -- validation evidence for the hidden tests

This directory validates this bench's hidden-test partition (`hidden_tests/slice1/`, `hidden_tests/slice2/`, mapped by `hidden_tests/obligations.yaml`) against a correct implementation of `docs/MERGER_RATE_PLAN-2SLICE.md`'s Slices 1-2. `reference_solution/` holds that implementation (`calc.py`, `config.py`, `merger_rate.py`); this README is the durable record of what was validated, how to redo it, and the known deviations between the vendored plan text and the tests. Nothing here is executed by the grading tools: `dev_check.py` never imports these files, and no Developer model is ever shown them.

## Provenance

`reference_solution/*.py` are byte-for-byte copies of `eval/tasks/001-merger-rate-feature/reference_solution/{calc,config,merger_rate}.py` at commit `62fb1466ae129fa11804bdd742a400ff0d703599` of this repository's `coding-bench-original` branch, the one-shot predecessor of this bench. That task's scientific content is what `docs/MERGER_RATE_PLAN-2SLICE.md` restructures into PM slices, so its reference solution implements this plan's formulas, pinned values, scalar-form rejection (`_real_scalar`) and centred weighted-least-squares fit exactly. The files are vendored here, like the plan itself, because they no longer exist on `main`: a reference that lives only on another branch is not reproducible from a clone of `main` alone. They are frozen with the plan -- do not edit them; if the plan or the hidden tests ever change, re-run the recipe below and record the result here.

The validation run recorded below used these files with two docstring-only edits that do not affect behaviour: `merger_rate.py`'s module docstring, and its two "Uncertainty follows Task 001's plug-in Poisson-error convention" docstrings, read "this plan's" in place of "Task 001's". The vendored copies keep the original wording so they stay byte-identical to their source.

## Reproduction recipe

To re-validate (after any future change to `docs/MERGER_RATE_PLAN-2SLICE.md`, the hidden tests, or `hidden_tests/obligations.yaml`):

1. Check out `relative-velocity` at the plan's pinned base commit (`043b13adc264689c376bdd337603e94d5447623a`, see `docs/MERGER_RATE_PLAN-2SLICE.provenance.md`) into a fresh disposable worktree of the vendored `substrate/relative-velocity` (never an operator's own separate checkout, so the evidence stays reproducible from this repository alone) and copy `reference_solution/*.py` into its `src/`.
2. Run `pytest tests/` there (the frozen substrate's own suite).
3. Copy `hidden_tests/slice1/*.py` into that worktree and run pytest on that directory alone; then the same for `hidden_tests/slice2/*.py`. **Run one slice's directory per pytest invocation, never both together**: both directories contain a same-named `test_hA.py`/`test_hB.py`, so a combined run fails module collection (duplicate basenames, no `__init__.py`). This never arises operationally, since Slice 2 is not graded until Slice 1 is accepted.

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
  still pass. Task 001's own `spec.md` (the plan's source before restructuring;
  `eval/tasks/001-merger-rate-feature/spec.md` at the same
  `coding-bench-original` commit named above) uses `-0.5` for the identical
  bullet, correctly distinct from the default. This is a transcription defect introduced when the
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
