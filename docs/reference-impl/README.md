# Reference implementation (G4)

A correct implementation of `docs/MERGER_RATE_PLAN-2SLICE.md`'s Slices 1-2,
kept so this bench's own hidden-test partition (`hidden_tests/slice1/`,
`hidden_tests/slice2/`) can be re-validated without redoing the work by
hand. Never shown to a Developer model in a real PM run.

## Provenance

`calc.py`, `config.py`, and `merger_rate.py` here are adapted from
`main`'s `eval/tasks/001-merger-rate-feature/reference_solution/` at the
commit this branch (`pm-eval-v2`) was seeded from. That reference solution
already implements this exact plan's formulas, pinned values, and (per its
`_real_scalar` helper and centred weighted-least-squares fit) its stricter
scalar-form-rejection and numerical-stability requirements -- because the
2-slice plan is Task 001's own scientific content restructured into PM
slices (see `docs/MODE2-REWRITE-PLAN.md` §1). Only two things changed
relative to the `main` source:

- The module docstring and the two `Uncertainty follows ... plug-in
  Poisson-error convention` docstrings now say "this plan's" rather than
  "Task 001's", matching this plan's own binding wording (Validation and
  Failure Conventions section).
- Nothing else -- no weak-baseline variant, no mutation-testing hooks, no
  `pipeline.py`/CLI wiring, and no Developer-facing `tests/test_merger_rate.py`
  were carried over, since nothing in this branch's design exercises them
  (Tool 1 never runs a "Developer's own tests" step, and PM/Developer write
  their own `tests/test_merger_rate.py` during a real run).

## Validation performed 2026-09-10

In a disposable worktree of `relative-velocity` at the plan's pinned base
commit (`043b13adc264689c376bdd337603e94d5447623a`), with `calc.py`/
`config.py` replaced by the files here and `merger_rate.py` added:

- `pytest tests/` (the frozen substrate's own suite): **80/80 passed**,
  unmodified -- confirms Slice 1/2's "behaviour that must not change"
  requirement.
- `hidden_tests/slice1/` copied in and run standalone: **44/44 passed**.
- `hidden_tests/slice2/` copied in and run standalone: **17/17 passed**.
- 44 + 17 = 61, matching `main`'s own historical validation of the
  unpartitioned `hidden_tests/test_hA.py` + `test_hB.py` (61/61, see that
  branch's `reference_solution/README.md`) -- confirms the re-partition
  moved every test exactly once, with none lost or duplicated.
- **Red check**: two independent defects were injected directly into this
  `merger_rate.py` (dropping the `sqrt(N_pairs)` term from
  `compute_pair_fraction`'s `sigma_f_pair`, a Slice 1 defect; and flipping
  `check_slope_consistency`'s comparison operator, a Slice 2 defect). Slice
  1's hidden tests caught the first (2 failures: `test_A05`, `test_E06`)
  while Slice 2's stayed green; Slice 2's hidden tests caught the second (3
  failures: `test_C08`, `test_E07`, `test_E09`). Confirms each partition
  actually discriminates a broken implementation from a correct one, not
  just that it imports and runs.
- **Implementation note for Tool 1** (`dev_check.py`, not yet built):
  `hidden_tests/slice1/` and `hidden_tests/slice2/` both contain a
  `test_hA.py` and a `test_hB.py`. Running both directories in a single
  `pytest` invocation fails module collection (duplicate basenames, no
  `__init__.py`). This is never actually needed -- Slice 2 doesn't exist to
  grade until Slice 1 is already accepted -- but Tool 1 must invoke pytest
  once per slice being graded, never pointed at both `hidden_tests/slice1/`
  and `hidden_tests/slice2/` in the same run.

Re-run this validation (e.g. after any future edit to `docs/MERGER_RATE_PLAN-2SLICE.md`
or the hidden tests) by checking out the pinned commit above into a fresh
worktree, copying these three files over `src/`, copying each
`hidden_tests/slice*/` directory in turn, and running `pytest` as described.
