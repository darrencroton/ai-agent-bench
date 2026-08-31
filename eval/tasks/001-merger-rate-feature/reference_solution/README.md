# Reference solution

A working implementation of Task 001, kept for harness self-validation only.

**Never shown to a Developer model.** `run_trial.py` only ever copies `spec.md`
into a trial's worktree; nothing in this directory is referenced by
`run_trial.py` or `grade_trial.py` at trial time.

Used to confirm, before pointing any real model at this task, that:

- the hidden tests (`../hidden_tests/test_hA.py`, `test_hB.py`) all pass
  against a genuinely correct implementation (61/61 passed here) --
  otherwise a bug in the hidden tests themselves would fail every model
  through no fault of its own;
- the mutation gate (`../mutations/`) actually kills mutations when the
  implementation and its tests are both correct (34/34 killed by the 26-test
  reference suite here), including the targeted validation, persistence,
  provenance, preflight, console-output, and numerical-stability mutations;
- `scope_discipline` and the lint-diff pass correctly see newly created
  files (`merger_rate.py` itself is new -- this caught a real `git diff`
  untracked-file bug during development, fixed in `run_trial.py`/`grade_trial.py`
  by staging with `git add -A` before diffing);
- `grade_trial.py` cleans up the hidden test files it copies in for
  correctness scoring before any later check runs `pytest tests/` --
  otherwise the mutation gate and the own-suite baseline silently score
  the hidden tests' ability to catch a mutation instead of the
  submission's own tests'. Caught here too: against the then-current
  19-mutation set, the cleanup-less code measured 19/19 killed; once the
  hidden tests stopped leaking into `tests/`, the true historical number
  was 17/19.

`calc.py` and `config.py` here are the full post-edit files, not diffs --
diff them against the repo root's `src/calc.py` / `src/config.py` to see
exactly what Part 1/Part 2 add.

Measured verification on 2026-08-31: reference suite 26/26, hidden tests 61/61,
and mutation gate 34/34 killed. These are local harness self-validation counts,
not a benchmark score.
