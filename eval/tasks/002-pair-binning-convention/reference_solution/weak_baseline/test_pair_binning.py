"""DISCRIMINATION CONTROL -- not part of the reference solution.

A deliberately vacuous submission: it runs the full pipeline once on
generated mock data (default config, every configured redshift) and asserts
only that one result came back per configured redshift. It exercises
pair_binning.py's whole happy path end to end -- every function gets
called, nothing raises -- but checks none of the pinned counts, none of the
convention comparisons, none of the additivity invariant, and none of the
persisted schema the reference suite (test_pair_binning.py) actually
verifies. Scored to confirm the mutation gate measures test *strength*
rather than mere presence of a passing suite, the same way
reference_solution/weak_baseline/ works for Tasks 004 and 005.

Copied into a scratch worktree as `tests/test_pair_binning.py` next to the
reference solution's own (correct) src/*.py, and graded the same way as any
submission. Expected: own_suite_command green, hidden tests unaffected
(correctness driven only by src/, which this file never touches), mutation
kill rate at or near zero.
"""
import contextlib
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import calc
import pair_binning as pb
from config import config as BASE_CONFIG
from generate_test_data import generate_all_snapshots


def test_pipeline_runs_end_to_end(tmp_path):
    c = dict(BASE_CONFIG)
    c["data_dir"] = str(tmp_path / "data") + os.sep
    c["results_dir"] = str(tmp_path / "results") + os.sep
    c["figures_dir"] = str(tmp_path / "fig") + os.sep
    os.makedirs(c["data_dir"], exist_ok=True)
    os.makedirs(c["results_dir"], exist_ok=True)

    with contextlib.redirect_stdout(io.StringIO()):
        generate_all_snapshots(c)
        calc.run_calculation(c)
        results = pb.run_binning_comparison(c)

    assert len(results) == len(c["redshifts"])
