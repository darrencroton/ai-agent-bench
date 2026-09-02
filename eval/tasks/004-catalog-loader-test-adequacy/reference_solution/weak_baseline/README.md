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
| hidden tests (`correctness`) | 38/38 | 38/38 — the deliberate floor |
| mutations killed (`test_adequacy`) | **53/53** | **0/53** |
| automated subtotal (85 of the 100 rubric weight) | **98.9%** | **69.5%** |
| total (incl. judged) | 96.1-97.7 | 65.1-68.3 |

The automated rows are the stable comparison and have been bit-identical across
every re-grade. The totals also carry the two judged categories, which are
model-scored and move between runs: this file has totalled 66.7, 65.1, 68.3 and
66.7 on byte-identical content.

Two further degenerate controls live next door in `../degenerate_controls/`:
a shape-only suite (0/53) and a rejections-only suite (4/53).

It is also the evidence that a line-coverage floor would not have worked here:
these two tests hit 15 of the function's 16 statement lines, the same 93.8% the
56-test reference reaches. See the parent `README.md`.

Do not "fix" this file. Its weakness is the instrument.
