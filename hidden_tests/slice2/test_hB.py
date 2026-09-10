"""Slice 2 hidden integration tests: end-to-end recovery of the injected
merger-timescale model on generated mock data, including the
non-default-alpha check that closes the mutation this plan's Slice 2 added
(see docs/MERGER_RATE_PLAN-2SLICE.md's Slice 2 Acceptance Criteria, item
added 2026-09-07). Assumes Slice 1 is already implemented and accepted.

Not visible to the Developer model. Copied into the trial worktree's tests/
directory at grading time and run with the trial's own pytest/venv.

Re-partitioned from ai-agent-bench's Task 001 `hidden_tests/test_hB.py`
(E07/E09 only; E01-E06 live in hidden_tests/slice1/test_hB.py) -- see
docs/MODE2-REWRITE-PLAN.md gap G4. Test bodies are unmodified from that
source; only the file's scope and this header changed.
"""
import contextlib
import copy
import io
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest

import calc
import config as cfgmod
from generate_test_data import generate_all_snapshots

try:
    import merger_rate as MR
except Exception as e:                      # pragma: no cover
    MR = None
    _MR_ERR = e

BASE = cfgmod.config


def cfg(**kw):
    c = copy.deepcopy(BASE); c.update(kw); return c


def nbins(c=BASE):
    return int(round((c["log_mass_max"] - c["log_mass_min"]) / c["mass_bin_width"]))


@pytest.fixture(scope="module")
def mock(tmp_path_factory):
    root = tmp_path_factory.mktemp("e2e")
    c = cfg(data_dir=str(root / "data") + os.sep,
            results_dir=str(root / "results") + os.sep,
            figures_dir=str(root / "figures") + os.sep)
    os.makedirs(c["data_dir"], exist_ok=True)
    os.makedirs(c["results_dir"], exist_ok=True)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        generate_all_snapshots(c)
        calc.run_calculation(c)
    return c


def test_E07_end_to_end_science(mock):
    c = mock
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        MR.run_merger_rate_calculation(c)
        res = MR.run_merger_rate_validation(c)
    expected = -c["merger_timescale_alpha"]
    checked = 0
    for d in res:
        if d["consistent"] is None:
            continue
        checked += 1
        assert d["consistent"] is True, d
        assert abs(d["slope"] - expected) < 0.4, d
        assert d["expected_slope"] == expected
    assert checked == nbins(c), checked
    print("SLOPES " + " ".join(f"{d['slope']:+.4f}" for d in res))


def test_E09_expected_slope_tracks_nondefault_alpha(mock):
    """report 04's M18: expected_slope must be derived from config at call
    time, not hardcoded anywhere in the call chain -- the one mutation that
    survived in 10 of 12 prior branches. Recompute with a distinct alpha and
    confirm the validation checks against THAT value, not the default -1.0."""
    c = mock
    c2 = copy.deepcopy(c)
    c2["merger_timescale_alpha"] = -0.7
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        MR.run_merger_rate_calculation(c2)
        res = MR.run_merger_rate_validation(c2)
    expected = -c2["merger_timescale_alpha"]
    assert abs(expected - 0.7) < 1e-12
    checked = 0
    for d in res:
        if d["consistent"] is None:
            continue
        checked += 1
        assert d["expected_slope"] == expected, \
            f"expected_slope={d['expected_slope']!r} did not track alpha=-0.7 (hardcoded expected_slope?)"
        assert d["consistent"] is True, d
        assert abs(d["slope"] - expected) < 0.4, d
    assert checked == nbins(c), "not every bin had enough usable points -- fixture problem, not a pass"
