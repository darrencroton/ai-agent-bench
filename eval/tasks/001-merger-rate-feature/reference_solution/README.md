# Reference solution

A working implementation of Task 001, kept for harness self-validation only.

**Never shown to a Developer model.** `run_trial.py` only ever copies `spec.md`
into a trial's worktree; nothing in this directory is referenced by
`run_trial.py` or `grade_trial.py` at trial time.

Used to confirm, before pointing any real model at this task, that:

- the hidden tests (`../hidden_tests/test_hA.py`, `test_hB.py`) all pass
  against a genuinely correct implementation (59/59 passed here) --
  otherwise a bug in the hidden tests themselves would fail every model
  through no fault of its own;
- the mutation gate (`../mutations/`) actually kills mutations when the
  implementation and its tests are both correct, and correctly reports a
  survivor when the test suite genuinely doesn't cover something (17/19
  killed here -- `test_merger_rate.py` in this directory doesn't happen to
  test a hardcoded timescale exponent or the count array's dtype in
  isolation, so `M17_hardcode_alpha` and `M21_count_float_dtype` survive,
  correctly);
- `scope_discipline` and the lint-diff pass correctly see newly created
  files (`merger_rate.py` itself is new -- this caught a real `git diff`
  untracked-file bug during development, fixed in `run_trial.py`/`grade_trial.py`
  by staging with `git add -A` before diffing);
- `grade_trial.py` cleans up the hidden test files it copies in for
  correctness scoring before any later check runs `pytest tests/` --
  otherwise the mutation gate and the own-suite baseline silently score
  the hidden tests' ability to catch a mutation instead of the
  submission's own tests'. Caught here too: the first version of this
  cleanup-less code measured 19/19 mutations killed against this exact
  reference; once the hidden tests stopped leaking into `tests/`, the true
  number was 17/19.

`calc.py` and `config.py` here are the full post-edit files, not diffs --
diff them against the repo root's `src/calc.py` / `src/config.py` to see
exactly what Part 1/Part 2 add.

Measured result at the time this was written: 88.9/100 (correctness 100%,
test_adequacy 89% [17/19 mutations], scope_discipline 100%, hygiene ~32% --
this reference prioritizes contract correctness over lint cleanliness and
exhaustive test coverage, and was not written to be a style exemplar).
