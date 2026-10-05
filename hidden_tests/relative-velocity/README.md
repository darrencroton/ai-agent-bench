# Reference implementation -- validation evidence for the hidden tests

This directory validates this bench's hidden-test partition (`slice1/`, `slice2/`, mapped by `obligations.yaml`) and its mutation bank (`mutations/`), all in this directory, against a correct implementation of `docs/MERGER_RATE_PLAN-2SLICE.md`'s Slices 1-2. `reference_solution/` holds that implementation (`calc.py`, `config.py`, `merger_rate.py`), its own test suite (`test_merger_rate.py`) and a deliberately weak control suite (`weak_baseline/test_merger_rate.py`); this README is the durable record of what was validated, how to redo it, and the known deviations between the vendored plan text and the tests. Nothing here is executed by the grading tools: `dev_check.py` never imports these files, and no Developer model is ever shown them.

This directory, `plans/relative-velocity/`, and their files were moved here from `hidden_tests/{slice1,slice2,mutations,obligations.yaml}`, `docs/reference-impl/` and `docs/` so every task keeps its files under its own `plans/<task>/` and `hidden_tests/<task>/`. The hidden tests' and bank's own docstrings still cite the old paths: their bytes are part of `hidden_tests_hash` and `bank_hash`, which hash file names and contents but not directories, so they are deliberately left unedited and the move is not a new rubric or bank version.

## Provenance

`reference_solution/{calc,config,merger_rate}.py` are byte-for-byte copies of `eval/tasks/001-merger-rate-feature/reference_solution/{calc,config,merger_rate}.py` at commit `62fb1466ae129fa11804bdd742a400ff0d703599` of this repository's `coding-bench-original` branch, the one-shot predecessor of this bench. That task's scientific content is what `docs/MERGER_RATE_PLAN-2SLICE.md` restructures into PM slices, so its reference solution implements this plan's formulas, pinned values, scalar-form rejection (`_real_scalar`) and centred weighted-least-squares fit exactly. The files are vendored here, like the plan itself, because they no longer exist on `main`: a reference that lives only on another branch is not reproducible from a clone of `main` alone. They are frozen with the plan -- do not edit them; if the plan or the hidden tests ever change, re-run the recipe below and record the result here.

`reference_solution/test_merger_rate.py` and `reference_solution/weak_baseline/test_merger_rate.py` are copies of the same task's `reference_solution/test_merger_rate.py` and `reference_solution/weak_baseline/test_merger_rate.py` at the same commit, and `hidden_tests/mutations/sitecustomize.py` is a copy of that task's `mutations/sitecustomize.py` (source sha256 `cefb6541eb030b29ae4a87776f2c19e0410225bf554e9d7a63c6cf2c5c33212a`), the 73-mutant bank that passed that branch's systematic mutation-integrity audit (`docs/DESIGN.md` there). These three are the one exception to byte-identity: each was passed once through the `lint` skill's `ruff format` so this repository lints clean, which changes whitespace only -- `ast.dump` of each vendored file equals `ast.dump` of its source, so the behaviour validated below is the source's behaviour. The relative-velocity substrate is byte-identical to that task's frozen substrate, so the bank applies unchanged; `hidden_tests/mutations/slice1.txt` and `slice2.txt` are this bench's own partition of its registry by plan slice (see "Mutation bank" below). The same freeze applies to all of them.

The validation run recorded below used these files with two docstring-only edits that do not affect behaviour: `merger_rate.py`'s module docstring, and its two "Uncertainty follows Task 001's plug-in Poisson-error convention" docstrings, read "this plan's" in place of "Task 001's". The vendored copies keep the original wording so they stay byte-identical to their source.

## Reproduction recipe

To re-validate (after any future change to `plans/relative-velocity/MERGER_RATE_PLAN-2SLICE.md`, the hidden tests, or `hidden_tests/relative-velocity/obligations.yaml`):

1. Check out `relative-velocity` at the plan's pinned base commit (`043b13adc264689c376bdd337603e94d5447623a`, see `plans/relative-velocity/MERGER_RATE_PLAN-2SLICE.provenance.md`) into a fresh disposable worktree of the vendored `substrate/relative-velocity` (never an operator's own separate checkout, so the evidence stays reproducible from this repository alone) and copy `reference_solution/*.py` into its `src/`.
2. Run `pytest tests/` there (the frozen substrate's own suite).
3. Copy `hidden_tests/relative-velocity/slice1/*.py` into that worktree and run pytest on that directory alone; then the same for `hidden_tests/relative-velocity/slice2/*.py`. **Run one slice's directory per pytest invocation, never both together**: both directories contain a same-named `test_hA.py`/`test_hB.py`, so a combined run fails module collection (duplicate basenames, no `__init__.py`). This never arises operationally, since Slice 2 is not graded until Slice 1 is accepted.

## Current validation status

Following the recipe above, against the unmodified reconstructed reference,
in a disposable worktree of the vendored substrate:

- `pytest tests/`: **80/80 passed** — confirms Slice 1/2's "behaviour that
  must not change" requirement.
- `hidden_tests/relative-velocity/slice1/`: **44/44 passed**.
- `hidden_tests/relative-velocity/slice2/`: **20/20 passed**.
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

## Mutation bank

`dev_check.py`'s `test_kill_rate` measures how many of a slice's seeded mutants the Developer's own test files kill. The bank's `sitecustomize.py` monkey-patches one plan-named public function after import when its directory leads `PYTHONPATH` and `MUTATION=<id>` is set; `slice1.txt` lists the 57 mutants whose function belongs to Slice 1 (pair fraction, merger timescale, merger rate, `_load_pair_counts`, `run_merger_rate_calculation`, and `calc.py`'s per-bin counting and `run_calculation`), and `slice2.txt` the 16 belonging to Slice 2 (`fit_log_rate_vs_redshift`, `check_slope_consistency`, `run_merger_rate_validation` and its console output). The split follows each mutant's wrapped function, `sitecustomize._required_api`, and agrees with the plan's own provenance note, whose merged Slice 1 carries the 18 + 39 = 57 mutations of the revised plan's first two slices, leaving 16 of the 73 for Slice 2.

### Recipe

1. Create a disposable worktree of the vendored `substrate/relative-velocity` at `043b13adc264689c376bdd337603e94d5447623a` outside `substrate/`, copy `reference_solution/{calc,config,merger_rate}.py` into its `src/` and `reference_solution/test_merger_rate.py` into its `tests/`, and `git add -A` (the gate measures tracked test files only).
2. Drive the gate directly, never through a PM run: `dev_check.load_mutation_bank(<bench root>, <resolved relative-velocity task>, <slice>)`, then `dev_check.measure_test_kill_rate(<worktree>, <bank>, <policy>, task["measurement"])`, once for slice 1 and once for slice 2.
3. Repeat with `weak_baseline/test_merger_rate.py` staged as `tests/test_merger_rate.py`, then with no candidate test file at all (the frozen suite alone).
4. Run `pytest tests/` on the reference suite plainly, with the bank on `PYTHONPATH` and `MUTATION` unset, and with an unregistered `MUTATION` id; compare the passing node sets. Remove the worktree.

### Results (2026-10-01)

Interpreter `~/.conda/envs/work/bin/python3` (Python 3.12.9, pytest 9.1.1), `mutation_gate.parallel_workers: 4`, `subprocess_timeout_seconds: 600`; times are the wall clock of `measure_test_kill_rate` alone.

| Own suite | Passing at baseline | Slice 1 killed | Slice 2 killed | Errored | Wall clock (slice 1 / slice 2) |
|---|---|---|---|---|---|
| Reference (`test_merger_rate.py` + the frozen suite) | 106 | 57/57 | 16/16 | 0 | 61.3 s / 20.4 s |
| Weak baseline (one end-to-end smoke test + the frozen suite) | 81 | 0/57 | 0/16 | 0 | 66.2 s / 25.1 s |
| Frozen suite only | 80 | 0/57 | 0/16 | 0 | 50.7 s / 16.1 s |

- **Every mutant is detectable**: the reference suite kills all 73, each under the slice that lists it, so no mutant is listed under the wrong slice and none is equivalent. This matches the predecessor's own audit (106 combined tests, 73/73 killed).
- **The bank discriminates**: the weak baseline, which calls every function end to end but asserts only a non-empty result, kills none.
- **Zero freebies**: the frozen 80-test suite kills none, so every kill comes from the candidate's own tests.
- **Inert when unset**: the reference suite passes the same 106 nodes plainly, with the bank on `PYTHONPATH` and `MUTATION` unset, and with an unregistered `MUTATION` id. The gate re-checks this on every measurement: its control run of the baseline-passing nodes, bank on the path and `MUTATION` unset, passed in every run above.

## Known deviations from the vendored plan text

A tool-independent review read the plan, the hidden tests, and the
reference implementation directly. Two things worth recording permanently:

- **`test_B03_timescale_pinned`** (`hidden_tests/relative-velocity/slice1/test_hA.py`) uses
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
