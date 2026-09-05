# Weak baseline — discrimination control

**This is not part of the reference solution.** `test_data_reader.py` in this
directory is a deliberately vacuous submission: it loads one valid catalog and
asserts only that a dict came back. It is here so the claim "the reference kills
53/53 mutations" means something — a mutation gate that also gave 53/53 to this
file would be measuring nothing.

Scored the same way the reference is (copied into a scratch worktree from the
`frozen-substrate` tag as `tests/test_data_reader.py`, then graded by the real
`eval/harness/grade_trial.py`):

| | reference | this file |
|---|---|---|
| own suite | 56 passed | 2 passed |
| hidden tests (`correctness` gate) | 38/38, passed | 38/38, passed -- the deliberate floor |
| mutations killed (`test_adequacy`, weight 65) | **53/53** | **0/53** |
| **deterministic score** | **100.0** | **23.5** |
| composite (incl. judged) | 98.2 | 27.5 |

The deterministic row is the stable comparison and is bit-identical across every
re-grade; the composite also carries the two judged categories, which are
model-scored and move a little between runs. Under rubric v1 this file scored
69.5% of automated weight against the reference's 98.9%, because clearing the
correctness floor was worth 40 points to both. Under v2 that floor is a gate
carrying no weight, so this file's vacuousness is no longer cushioned.

Two further degenerate controls live next door in `../degenerate_controls/`:
a shape-only suite (0/53) and a rejections-only suite (4/53).

It is also the evidence that a line-coverage floor would not have worked here:
these two tests hit 15 of the function's 16 statement lines, the same 93.8% the
56-test reference reaches. See the parent `README.md`.

Do not "fix" this file. Its weakness is the instrument.
