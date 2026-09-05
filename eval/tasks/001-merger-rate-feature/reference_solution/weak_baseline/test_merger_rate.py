"""DISCRIMINATION CONTROL -- not part of the reference solution.

A deliberately vacuous submission: it runs the full pipeline once on
generated mock data (default config, every configured redshift) and asserts
only that a non-empty validation result list came back. It exercises
merger_rate.py's whole happy path end to end -- every function gets called,
nothing raises -- but checks none of the pinned values, none of the
rejection matrix, and none of the persisted schema the reference suite
(test_merger_rate.py) actually verifies. Scored to confirm the mutation
gate measures test *strength* rather than mere presence of a passing suite,
the same way reference_solution/weak_baseline/ works for Tasks 004 and 005.

Copied into a scratch worktree as `tests/test_merger_rate.py` next to the
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
import config as cfgmod
import merger_rate as MR
from generate_test_data import generate_all_snapshots


def test_pipeline_runs_end_to_end(tmp_path):
    c = dict(cfgmod.config)
    c["data_dir"] = str(tmp_path / "data") + os.sep
    c["results_dir"] = str(tmp_path / "results") + os.sep
    c["figures_dir"] = str(tmp_path / "fig") + os.sep
    os.makedirs(c["data_dir"], exist_ok=True)
    os.makedirs(c["results_dir"], exist_ok=True)

    with contextlib.redirect_stdout(io.StringIO()):
        generate_all_snapshots(c)
        calc.run_calculation(c)
        MR.run_merger_rate_calculation(c)
        results = MR.run_merger_rate_validation(c)

    assert results
