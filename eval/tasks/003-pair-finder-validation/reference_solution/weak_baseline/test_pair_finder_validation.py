"""DISCRIMINATION CONTROL -- not part of the reference solution.

A deliberately vacuous submission: it calls find_pairs() once on a
hand-built two-galaxy catalog with a default config and asserts only that
one pair came back. It exercises the accepted-input happy path -- nothing
raises -- but checks none of the rejection matrix, none of the pinned pair
properties, none of the integer-dtype semantics, and none of the driver
integration path the reference suite (test_pair_finder_validation.py)
actually verifies. Scored to confirm the mutation gate measures test
*strength* rather than mere presence of a passing suite, the same way
reference_solution/weak_baseline/ works for Tasks 004 and 005.

Copied into a scratch worktree as `tests/test_pair_finder_validation.py`
next to the reference solution's own (correct) src/pair_finder.py, and
graded the same way as any submission. Expected: own_suite_command green,
hidden tests unaffected (correctness driven only by src/, which this file
never touches), mutation kill rate at or near zero.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from pair_finder import find_pairs

BASE_CONFIG = dict(
    box_size       = 1.0,
    log_mass_min   = 8.0,
    log_mass_max   = 11.0,
    mass_bin_width = 1.0,
    sep_bins       = [0, 10, 15, 20, 25],
    mass_ratio_min = 0.1,
    mass_bin_by    = "primary",
    max_sep        = 100.0,
)


def _catalog():
    """Two galaxies 10 kpc apart."""
    return dict(
        x=np.array([0.0, 0.010]), y=np.array([0.0, 0.0]), z=np.array([0.0, 0.0]),
        vx=np.array([0.0, 0.0]), vy=np.array([0.0, 0.0]), vz=np.array([0.0, 0.0]),
        log_stellar_mass=np.array([10.0, 9.5]), box_size=1.0,
    )


def test_find_pairs_runs_on_accepted_input():
    pairs = find_pairs(_catalog(), BASE_CONFIG)

    assert len(pairs["delta_v"]) == 1
