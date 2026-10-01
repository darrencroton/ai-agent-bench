"""Slice 1 hidden test: the existing suite still passes unchanged.

Kept in its own file because it is the one deliberately expensive node (it
runs five existing test files in a subprocess, about 55 s). Not visible to
the Developer model.

Every test function the five files defined at the pre-plan commit must still
exist somewhere under tests/ (a test moved to another file, e.g.
test_bench_lib.py, still counts), and the five files must pass as they stand.
The pinned tests of `cohort_run.parse_pinned_plan_commit` are exempt from the
name check: the plan lets them be relocated and re-pointed at bench_lib,
which legitimately renames them.
"""

import ast
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

PRE_PLAN_COMMIT = "77b24c4"
EXISTING_FILES = (
    "test_cohort_run.py",
    "test_dev_check.py",
    "test_grade_run.py",
    "test_model_report.py",
    "test_leaderboard.py",
)
HIDDEN_FILES = {"test_hA.py", "test_hB.py"}


def _test_functions(source):
    return [
        node
        for node in ast.walk(ast.parse(source))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test")
    ]


def _test_function_names(source):
    return {node.name for node in _test_functions(source)}


def test_existing_suite_still_present_and_passing():
    pinned = set()
    for filename in EXISTING_FILES:
        source = subprocess.run(
            [
                "git",
                "-C",
                str(REPO_ROOT),
                "show",
                f"{PRE_PLAN_COMMIT}:tests/{filename}",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        pinned |= {
            node.name
            for node in _test_functions(source)
            if "parse_pinned_plan_commit" not in ast.unparse(node)
        }
    present = set()
    for path in (REPO_ROOT / "tests").rglob("*.py"):
        if path.name not in HIDDEN_FILES:
            present |= _test_function_names(path.read_text(encoding="utf-8"))
    assert not sorted(pinned - present), (
        f"existing tests no longer defined anywhere under tests/: {sorted(pinned - present)}"
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *[f"tests/{f}" for f in EXISTING_FILES],
            "-q",
            "-x",
            "-p",
            "no:cacheprovider",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=1800,
    )
    assert result.returncode == 0, (
        f"existing suite failed (exit {result.returncode}):\n{result.stdout[-4000:]}\n{result.stderr[-2000:]}"
    )
