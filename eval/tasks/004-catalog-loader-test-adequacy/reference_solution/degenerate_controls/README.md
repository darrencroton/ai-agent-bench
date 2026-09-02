# Degenerate controls

**Not part of the reference solution.** Two deliberately deficient submissions,
checked in so the discrimination numbers in `../README.md` are reproducible
rather than merely asserted. Each is copied into a scratch worktree as
`tests/test_data_reader.py`, exactly the way the reference suite is, and scored
against the same 53-mutation gate.

| directory | what it is | mutations killed |
|---|---|---|
| `shape_only/` | asserts only that the seven arrays have equal length; pins no value | **0 / 53** |
| `rejections_only/` | pins all five rejections with bare `pytest.raises(AssertionError)`, no message matching, nothing about the return value | **4 / 53** |

`shape_only/` is the standing guard for a specific defect an r1 review found:
the original `M13` family substituted the whole *unmasked* array back in, so
this file alone killed 7 of the then-19 mutations without checking a single
selected value. Measured both ways against the same file: **7/7 killed** with
the old M13, **0/7** with the current one.

`rejections_only/` is the evidence that the gate grades rather than switches.
It kills **exactly** `M01`, `M03`, `M04` and `M05` — the same four it killed
against the 19-, 36- and 47-mutation sets, and for a reason worth stating precisely,
because it is *not* "these four are shallow":

- `M01` is killed because the mutated call raises `OSError` where an
  `AssertionError` was expected — an **exception-type** discrimination.
- `M03`, `M04` and `M05` are killed because the mutated call **raises nothing
  at all**, so the `pytest.raises` block fails.
- Everything else survives, including all nine `M14` message mutations and
  `M02`: each of those still raises an `AssertionError`, and a bare
  `pytest.raises(AssertionError)` cannot see that the message changed or that
  a different guard fired.

So the two controls fail for different reasons and are not redundant:
`shape_only/` shows that no mutation is reachable by inspecting the *shape* of
what comes back, and `rejections_only/` shows how far exception-type
discrimination alone gets a suite — 4 of 53 — before it has to start asserting
what the function returns and what its messages say.

Do not "fix" either file. Their weakness is the instrument.
