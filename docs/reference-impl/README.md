# Reference implementation (G4) — validation evidence, not tracked code

This directory used to hold a copy of a correct implementation of
`docs/MERGER_RATE_PLAN-2SLICE.md`'s Slices 1-2, kept only to validate this
bench's hidden-test partition (`hidden_tests/slice1/`, `hidden_tests/slice2/`).
**The `.py` files were removed 2026-09-11** (see "Trimmed as bloat" below) —
this README is the durable record of what was validated and how to redo it,
not a place that needs source code sitting in it permanently.

## Provenance and reconstruction

A correct `calc.py`/`config.py`/`merger_rate.py` for this plan already exists,
permanently, in this same git repository: `main`'s
`eval/tasks/001-merger-rate-feature/reference_solution/`. It already
implements this exact plan's formulas, pinned values, and (per its
`_real_scalar` helper and centred weighted-least-squares fit) its stricter
scalar-form-rejection and numerical-stability requirements — because the
2-slice plan is Task 001's own scientific content restructured into PM
slices (see `docs/MODE2-REWRITE-PLAN.md`'s "What this measures" section).
This is *not* the same
situation as `docs/MERGER_RATE_PLAN-2SLICE.md` itself, which is vendored
(gap G8) because it lives in a genuinely different repository
(`relative-velocity`) that could drift out from under a pinned commit;
`main` and `pm-eval-v2` are branches of *this* repository, so `main`'s copy
is exactly as durable as vendoring it here would be, at zero ongoing cost.

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
   worktree, drop the three files above into `src/` there.
3. Run `pytest tests/` (the frozen substrate's own suite).
4. Copy `hidden_tests/slice1/*.py` into that worktree and run pytest on
   that directory alone; then the same for `hidden_tests/slice2/*.py`.
   **Run one slice's directory per pytest invocation, never both together**
   — both directories contain a same-named `test_hA.py`/`test_hB.py`, so a
   combined run fails module collection (duplicate basenames, no
   `__init__.py`). Never actually needed operationally: Slice 2 isn't
   graded until Slice 1 is already accepted.

## Validation performed 2026-09-10 (execution) and 2026-09-11 (independent review)

Following the recipe above, in a disposable worktree:

- `pytest tests/`: **80/80 passed**, unmodified — confirms Slice 1/2's
  "behaviour that must not change" requirement.
- `hidden_tests/slice1/`: **44/44 passed**.
- `hidden_tests/slice2/`: **17/17 passed**.
- 44 + 17 = 61, matching `main`'s own historical validation of the
  unpartitioned `hidden_tests/test_hA.py` + `test_hB.py` (61/61) — confirms
  the re-partition moved every test exactly once, with none lost or
  duplicated.
- **Red check**: two independent defects were injected directly into
  `merger_rate.py` (dropping the `sqrt(N_pairs)` term from
  `compute_pair_fraction`'s `sigma_f_pair`, a Slice 1 defect; and flipping
  `check_slope_consistency`'s comparison operator, a Slice 2 defect). Slice
  1's hidden tests caught the first (`test_A05`, `test_E06`) while Slice 2
  stayed green; Slice 2's hidden tests caught the second (`test_C08`,
  `test_E07`, `test_E09`). Confirms each partition actually discriminates a
  broken implementation, not just that it imports and runs.
- All of the above was executed twice independently: once by the session
  that did the re-partition, and again from scratch by a separate
  fresh-eyes review subagent (same session, before commit) that reproduced
  every count exactly via its own worktree, and separately by an
  AST-level diff confirming the 61-test partition is exhaustive and
  non-duplicating.

## Independent codex/gpt-5.6-sol review, 2026-09-11 (medium effort, read-only, static — no code executed)

A second, tool-independent review (via this repo's `orchestrator` skill,
codex CLI) read the plan, the hidden tests, and the (then still present)
reference-impl source directly, without running anything. Findings and
resolutions:

- **Confirmed correct**: the Slice 1/Slice 2 directory boundary is faithful
  to the plan's own Authorized Surface sections; `run_merger_rate_calculation`
  is unambiguously a Slice 1 deliverable (used correctly by several Slice 1
  integration tests); every one of 61 test functions is classified into the
  right slice, none lost or duplicated; every reference-implementation
  function traced directly to a specific Acceptance Criteria bullet with
  `path:line` evidence.
- **Real gap found and fixed**: `test_E09_expected_slope_tracks_nondefault_alpha`
  (`hidden_tests/slice2/test_hB.py`) checked the returned per-bin dicts but
  never checked that the *printed* summary also reports the tracked
  `expected_slope`, even though the plan's own bullet requires both ("every
  returned per-bin dict reports `expected_slope == 1.5`, **and the printed
  summary reports the same**"). This gap pre-dated the re-partition (it was
  already present, unmodified, in Task 001's original `test_hB.py` on
  `main`) but is real and cheap to close — one assertion added, no new test,
  no new helper machinery.
- **Investigated and deliberately not changed**: the reviewer also flagged
  `test_B03_timescale_pinned` (`hidden_tests/slice1/test_hA.py`) for using
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
  implements the bullet's actual intent correctly. Left as-is; recorded
  here rather than silently worked around, since the vendored plan copy is
  deliberately frozen (gap G8) and not ours to edit.
- Two low-severity items reviewed and deliberately left alone: an unused
  `_MR_ERR` variable in each file's import-guard (inherited verbatim from
  Task 001's original hidden tests on `main`, present before this branch
  existed — not worth another edit-and-review cycle for a single
  cosmetic unused local in test-fixture code that is otherwise meant to
  stay byte-identical to its source); and a minor `np.errstate`/`np.where`
  redundancy in the now-removed reference-impl `merger_rate.py`, moot
  now that file is gone.

## Trimmed as bloat, 2026-09-11

The original commit for this gap (G4) included full copies of
`calc.py`/`config.py`/`merger_rate.py` (~420 lines) here. On review against
this branch's own design principle ("minimum, no dead code... every file
must be load-bearing," `docs/MODE2-REWRITE-PLAN.md`'s design principles):
nothing in Tools 1-5's design ever reads this directory, it is absent from
the plan's own repo layout, and — per the reconstruction recipe above — it
is fully and trivially reproducible from `main` within this same
repository at any time. Keeping ~420 lines of code that exists permanently,
unchanged, one `git show` away is exactly the dead weight the plan warns
against. The files were removed; this README (the actual G4 deliverable —
evidence that the hidden tests are correct and discriminating) stays.

## Validation performed 2026-09-15: `test_E09` float-format defect fixed

The 2026-09-11 codex/gpt-5.6-sol review above is the same review that
*added* the assertion this validation now fixes: it correctly found that
`test_E09_expected_slope_tracks_nondefault_alpha` never checked the printed
summary, only the returned dict, and added one assertion to close that
gap. The regex it added, `expected(?:_slope)?\s*=\s*\+?0\.7\b`, turned out
to itself be defective — the trailing `\b` matched `expected_slope=0.7`
(`%g`-style formatting) but not `expected=0.700000` (fixed-precision
formatting), so the new assertion discriminated on the implementation's
choice of print format string rather than on whether `expected_slope` was
correctly derived from config. Measured across the cohort: this failed two
of four Developer configurations, and varied run to run within one
configuration purely because that model's format string changed. See
`docs/OBLIGATION-GROUPS.md`'s 2026-09-15 entry for the full account.

Fixed by parsing every printed number with a capture group (reusing
`test_hA.py`'s own `_FLOAT` pattern, duplicated rather than imported) and
comparing numerically, tolerance `1e-9`, instead of matching the digit
string literally. The assertion collects all occurrences and passes if any
one matches, deliberately preserving the original's "appears somewhere in
the printed summary" semantics — matching only the first occurrence would
have been a strictly stronger test than the one being repaired. Re-ran the
reconstruction recipe above in a fresh
disposable worktree to validate the fix, using the reference
implementation exactly as reconstructed above (unmodified for the first
check; `merger_rate.py`'s two `expected_slope:+.6g` print sites edited to
`expected_slope:.6f` for the positive control; `run_merger_rate_validation`'s
`expected_slope` line hardcoded to `1.0` instead of
`-float(config["merger_timescale_alpha"])` for the negative control — each
change reverted before the next):

- Unmodified reference: `pytest tests/` 80/80 passed; slice-2 hidden tests
  17/17 passed, `test_E09` included — no regression from the fix.
- Positive control (print format changed to `.6f`, prints
  `expected_slope=0.700000`): `test_E09` FAILED under the pre-fix
  assertion, PASSED under the fixed assertion — the exact defect closed.
- Negative control A (`expected_slope` hardcoded to the default-derived
  `1.0`, still printed): `test_E09` still FAILED under the fixed
  assertion.
- Negative control B (returned dicts left correct at `0.7`, but the
  *printed* value replaced with a wrong constant `1.000000`): `test_E09`
  still FAILED, naming the values found. This is the control that actually
  exercises the changed assertion — under control A the untouched sibling
  assertion on the returned dicts fails first, so control A would pass even
  if the printed-summary check had been removed entirely.

No test was added or removed; slice 2 remains 17 hidden tests, and the
change touched only that one assertion plus the duplicated `_FLOAT`
constant it needs.

## Validation performed 2026-09-15 (second): `end_to_end_science` deepened to five nodes

`test_E09` was retired outright rather than repaired a second time, and four new
nodes were added — see `docs/OBLIGATION-GROUPS.md`'s 2026-09-15 entry for the
reasoning and the frozen-plan citation licensing each. Slice 2 goes from 17 to
20 hidden tests.

Reconstruction recipe above, run in a disposable worktree of the **vendored**
`substrate/relative-velocity` at the pinned commit (not an operator's own
checkout of `relative-velocity`, so the evidence below is reproducible from
this repository alone):

- **Green check**: slice-2 hidden tests **20/20 passed** against the unmodified
  reference implementation, and the substrate's own `pytest tests/` still
  **80/80 passed**. Re-run after a dead-code removal (`re` and `_FLOAT` became
  unused once `test_E09` was deleted) and still 20/20.
- **Red check, one defect per new node**, injected one at a time and reverted
  between each:
  - `test_E10` — alpha clipped at `-1.0` before deriving the timescale while
    `expected_slope` echoes the unclipped config: **E10 failed** as intended.
    E11 also fails on this defect, which is expected rather than a leak — its
    ratio check is strictly more sensitive to the same fault.
  - `test_E11` — an alpha-dependent multiplicative normalisation applied to
    every rate (moves the intercept, leaves the log-log slope untouched):
    **only E11 failed**; the other 19 nodes passed. This is the clearest
    evidence in the suite that the new node closes a real gap — no existing
    slope or consistency assertion can see this fault at all.
  - `test_E12` — `slope_err` and `intercept` swapped when assembling the
    returned dict: **only E12 failed**; the other 19 passed.
  - `test_E13` — validation's bin count hardcoded to the default 6 while the
    lower-level functions honour the config: **only E13 failed**; the other 19
    passed.
- The E11, E12 and E13 red checks were re-run **independently** rather than
  taken from the implementing agent's report, each against the vendored
  substrate, with the reference restored and re-verified at 20/20 afterwards.

Empirical fixture facts, measured rather than assumed: at
`merger_timescale_alpha = -1.5` all 6 default-grid bins remain eligible
(`consistent is not None`), and at `test_E13`'s grid (`mass_bin_width = 1.0`,
3 bins over `[8.0, 11.0]`, which divides exactly) all 3 are eligible.

One obligation is now deliberately unchecked: plan:669-674 requires the printed
summary as well as the returned dicts to report the tracked `expected_slope`,
and `test_E10` checks only the returned dicts. Every presentation-insensitive
form of the printed check either accepted a stale value or rejected a
correctly-but-differently formatted one — the exact defect class that retired
`test_E09`. Recorded rather than closed with a third format-sensitive regex.
