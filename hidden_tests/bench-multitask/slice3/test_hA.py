"""Slice 3 hidden tests: `model_report.py` propagates and backfills
`task_id`, derived from docs/plans/MULTI-TASK-PLAN-3SLICE.md's Slice 3
Acceptance Criteria.

Not visible to the Developer model. Copied into the grading worktree's tests/
directory and run there. Every report is a real `model_report.main` run with
`--policy` naming a fixture policy; the sheets it reads are written where
model_report.py discovers them (results/runs/<run_id>/ under the bench root)
under a unique run id and removed afterwards. The fixture obligations files
live in a uniquely named directory inside the bench root, removed the same
way, and their node ids exist in no real obligations map, so reading the
wrong file is a loud failure rather than a coincidental pass.
"""

import json
import re
import shutil
import sys
import uuid
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import model_report  # noqa: E402

# Per task, per slice: the obligation groups and each node's recorded outcome.
OUTCOMES = {
    "a": {
        1: {
            "alpha_group": {
                "tests/test_hA.py::test_alpha_one": "passed",
                "tests/test_hA.py::test_alpha_two": "failed",
            }
        },
        2: {"alpha_late": {"tests/test_hA.py::test_alpha_three": "passed"}},
    },
    "b": {
        1: {"beta_group": {"tests/test_hZ.py::test_beta_only": "passed"}},
        2: {
            "beta_late": {
                "tests/test_hZ.py::test_beta_late_one": "failed",
                "tests/test_hZ.py::test_beta_late_two": "failed",
            }
        },
    },
}


def _obligations(flavour):
    return {
        "version": 1,
        "plan": "docs/PLAN.md",
        "plan_pin": "0123456789abcdef0123456789abcdef01234567",
        "slices": {
            number: {
                "obligations": [
                    {"id": gid, "description": "fixture", "tests": list(nodes)}
                    for gid, nodes in groups.items()
                ]
            }
            for number, groups in OUTCOMES[flavour].items()
        },
    }


def _correctness(flavour, slice_number):
    groups = OUTCOMES[flavour][slice_number]
    by_node = {
        node: outcome for nodes in groups.values() for node, outcome in nodes.items()
    }
    by_obligation = {}
    for gid, nodes in groups.items():
        passed = sum(1 for outcome in nodes.values() if outcome == "passed")
        by_obligation[gid] = {
            "passed": passed,
            "total": len(nodes),
            "fraction": passed / len(nodes),
        }
    return {
        "hidden_tests_passed": sum(1 for o in by_node.values() if o == "passed"),
        "hidden_tests_total": len(by_node),
        "by_obligation": by_obligation,
        "by_node": by_node,
    }


ABSENT = object()


def _provenance(task_id):
    """`ABSENT` leaves the task_id key out entirely (a sheet graded before
    task stamping); any other value, None included, is recorded as given."""
    block = {
        "plan_hash": "plan-hash",
        "policy_hash": "policy-hash",
        "obligations_hash": "obligations-hash",
        "hidden_tests_hash": "hidden-tests-hash",
        "base_commit": "base-commit",
        "pm_skill_version": None,
    }
    if task_id is not ABSENT:
        block["task_id"] = task_id
    return block


def _attempt(ordinal, flavour, slice_number, provenance):
    return {
        "attempt": ordinal,
        "pm_attempts_counter": ordinal,
        "commit_sha": f"sha-{slice_number}-{ordinal}",
        "timestamp": "2026-10-01T00:00:00Z",
        "provenance": provenance,
        "correctness": _correctness(flavour, slice_number),
        "quality": {
            "lint_findings_by_tool": {},
            "code_health_findings_by_category": {},
        },
        "scope": {
            "violations": [],
            "changed_files": [],
            "effective_authorized_surface": [],
        },
        "pm_decision": "accept",
        "reviews": [],
    }


def _entry(obligations_file, **overrides):
    entry = {
        "repo": "substrate/fixture-repo",
        "branch_prefix": "pm-eval-fixture",
        "worktree_root": None,
        "plan_file": "docs/PLAN.md",
        "provenance_file": "docs/PLAN.provenance.md",
        "hidden_tests_dir": "hidden_tests/fixture",
        "obligations_file": obligations_file,
        "expected_slices": 2,
        "measurement": {
            "production_paths": ["tools/**/*.py"],
            "test_paths": ["tests/**/*.py"],
            "doc_paths": ["*.md"],
        },
    }
    entry.update(overrides)
    return entry


class Bench:
    def __init__(self, tmp_path, fixture_dir):
        self.tmp_path = tmp_path
        self.rel = fixture_dir.relative_to(REPO_ROOT).as_posix()
        self.run_id = f"hidden-mt-{uuid.uuid4().hex[:12]}"
        for flavour in OUTCOMES:
            (fixture_dir / f"obligations-{flavour}.yaml").write_text(
                yaml.safe_dump(_obligations(flavour)), encoding="utf-8"
            )

    def obligations_file(self, flavour):
        return f"{self.rel}/obligations-{flavour}.yaml"

    def policy(self, tasks=None, *, default_task="task-a"):
        if tasks is None:
            tasks = {
                "task-a": _entry(self.obligations_file("a")),
                "task-b": _entry(self.obligations_file("b")),
            }
        policy = {
            "backend": "local",
            "pm_scripts_dir": str(self.tmp_path / "pm-scripts"),
            "lint_script": str(self.tmp_path / "no-such-lint.py"),
            "health_script": str(self.tmp_path / "no-such-health.py"),
            "python_interpreter": sys.executable,
            "subprocess_timeout_seconds": 600,
            "measurement": {
                "loc_definition": "net_physical_lines",
                "loc_category_definition": "ast_tokenize_line_classification",
                "metric_version": 2,
            },
            "default_task": default_task,
            "tasks": tasks,
        }
        path = self.tmp_path / f"policy-{uuid.uuid4().hex[:8]}.yaml"
        path.write_text(yaml.safe_dump(policy, sort_keys=False), encoding="utf-8")
        return path

    def sheets_dir(self):
        return REPO_ROOT / "results" / "runs" / self.run_id

    def write_sheet(self, slice_number, flavour, task_ids):
        """One sheet whose attempts 0..n-1 carry `task_ids[i]` as their
        provenance task_id (ABSENT, None, a string, or a non-mapping
        provenance passed as `("provenance", value)`)."""
        attempts = []
        for ordinal, task_id in enumerate(task_ids):
            provenance = (
                task_id[1] if isinstance(task_id, tuple) else _provenance(task_id)
            )
            attempts.append(_attempt(ordinal, flavour, slice_number, provenance))
        sheet = {
            "run_id": self.run_id,
            "developer": {
                "harness": "fixture",
                "model": "fixture/model",
                "effort": None,
                "configuration_key": "fixture/model · fixture · effort unknown",
                "sources": {
                    "harness": "run_harness",
                    "model": "run_harness",
                    "effort": "run_harness",
                },
                "attributed": True,
                "attestation": None,
            },
            "slice": slice_number,
            "run_status": {
                "pm_status": "complete",
                "slice_status": "accepted",
                "stop_reason": None,
                "infrastructure_failure_suspected": False,
            },
            "attempts": attempts,
            "accepted_at_attempt": len(attempts) - 1,
            "pm_model_performance_ref": None,
        }
        directory = self.sheets_dir()
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"slice-{slice_number}.json").write_text(
            json.dumps(sheet), encoding="utf-8"
        )

    def report(self, policy):
        out = self.tmp_path / "model-report.json"
        model_report.main(
            ["--run-id", self.run_id, "--policy", str(policy), "--out", str(out)]
        )
        return json.loads(out.read_text(encoding="utf-8"))

    def refused(self, policy):
        with pytest.raises(model_report.ModelReportError) as excinfo:
            model_report.main(
                [
                    "--run-id",
                    self.run_id,
                    "--policy",
                    str(policy),
                    "--out",
                    str(self.tmp_path / "refused.json"),
                ]
            )
        assert not (self.tmp_path / "refused.json").exists()
        return str(excinfo.value)


@pytest.fixture
def bench(tmp_path):
    fixture_dir = REPO_ROOT / f".hidden-fixture-{uuid.uuid4().hex}"
    fixture_dir.mkdir()
    world = None
    try:
        world = Bench(tmp_path, fixture_dir)
        yield world
    finally:
        shutil.rmtree(fixture_dir, ignore_errors=True)
        if world is not None:
            shutil.rmtree(world.sheets_dir(), ignore_errors=True)


def _node_outcomes(report, slice_number):
    return next(s for s in report["slices"] if s["slice"] == slice_number)[
        "first_attempt_node_outcomes"
    ]


def _names_slice_one(message):
    return re.search(r"[Ss]lice\W+1\b", message) is not None


# --- task_id_propagation -------------------------------------------------------


def test_natively_stamped_sheets_report_their_task_as_graded(bench):
    bench.write_sheet(1, "b", ["task-b", "task-b"])
    bench.write_sheet(2, "b", ["task-b"])
    report = bench.report(bench.policy())
    assert (report["task_id"], report["task_id_source"]) == ("task-b", "graded")
    assert [s["correctness_provenance"]["task_id"] for s in report["slices"]] == [
        "task-b",
        "task-b",
    ]


def test_unstamped_sheets_backfill_to_the_default_task(bench):
    bench.write_sheet(1, "a", [ABSENT, ABSENT])
    bench.write_sheet(2, "a", [ABSENT])
    report = bench.report(bench.policy())
    assert (report["task_id"], report["task_id_source"]) == ("task-a", "backfilled")


def test_slices_disagreeing_on_task_id_are_refused_naming_the_run_and_both_values(
    bench,
):
    bench.write_sheet(1, "a", ["task-a"])
    bench.write_sheet(2, "b", ["task-b"])
    message = bench.refused(bench.policy())
    assert bench.run_id in message and "task-a" in message and "task-b" in message


def test_slices_mixing_graded_and_backfilled_attribution_are_refused(bench):
    """Slice 1 is stamped with the default task itself, so only the
    graded-versus-backfilled distinction, not a value mismatch, can refuse."""
    bench.write_sheet(1, "a", ["task-a"])
    bench.write_sheet(2, "a", [ABSENT])
    message = bench.refused(bench.policy())
    assert bench.run_id in message


# --- every_attempt_inspected ---------------------------------------------------


def test_a_middle_attempt_disagreeing_on_task_id_is_refused_naming_run_slice_and_values(
    bench,
):
    bench.write_sheet(1, "b", ["task-b", "task-a", "task-b"])
    message = bench.refused(bench.policy())
    assert bench.run_id in message and _names_slice_one(message)
    assert "task-a" in message and "task-b" in message


def test_a_slice_mixing_stamped_and_unstamped_attempts_is_refused(bench):
    """The unstamped attempt sits between two attempts stamped with the
    default task, so backfilling it would agree by value; it must still be
    refused rather than attributed by guesswork."""
    bench.write_sheet(1, "a", ["task-a", ABSENT, "task-a"])
    message = bench.refused(bench.policy())
    assert bench.run_id in message and _names_slice_one(message)


# --- malformed_provenance_refused ----------------------------------------------


def test_explicit_null_task_id_is_refused_never_backfilled(bench):
    bench.write_sheet(1, "a", [None])
    message = bench.refused(bench.policy())
    assert bench.run_id in message and "task_id" in message


def test_non_mapping_provenance_is_refused_by_name(bench):
    bench.write_sheet(1, "a", [("provenance", "corrupted-provenance")])
    message = bench.refused(bench.policy())
    assert bench.run_id in message and "provenance" in message


# --- task_resolved_obligations -------------------------------------------------


def test_node_outcomes_are_rebuilt_from_the_stamped_tasks_obligations_file(bench):
    bench.write_sheet(1, "b", ["task-b"])
    report = bench.report(bench.policy())
    assert _node_outcomes(report, 1) == {
        "beta_group": {"tests/test_hZ.py::test_beta_only": "passed"}
    }


def test_a_backfilled_run_rebuilds_node_outcomes_from_the_default_tasks_obligations_file(
    bench,
):
    bench.write_sheet(1, "a", [ABSENT])
    report = bench.report(bench.policy())
    assert _node_outcomes(report, 1) == {
        "alpha_group": {
            "tests/test_hA.py::test_alpha_one": "passed",
            "tests/test_hA.py::test_alpha_two": "failed",
        }
    }


# --- policy_flag ---------------------------------------------------------------


def test_policy_flag_resolves_the_task_registry_from_the_given_file(bench):
    """The bench root's own policy.yaml configures relative-velocity with the
    real hidden_tests/obligations.yaml, where these node ids do not exist;
    only the --policy file points relative-velocity at the fixture map."""
    policy = bench.policy(
        {"relative-velocity": _entry(bench.obligations_file("b"))},
        default_task="relative-velocity",
    )
    bench.write_sheet(1, "b", ["relative-velocity"])
    bench.write_sheet(2, "b", ["relative-velocity"])
    report = bench.report(policy)
    assert (report["task_id"], report["task_id_source"]) == (
        "relative-velocity",
        "graded",
    )
    assert _node_outcomes(report, 2) == {
        "beta_late": {
            "tests/test_hZ.py::test_beta_late_one": "failed",
            "tests/test_hZ.py::test_beta_late_two": "failed",
        }
    }


def test_policy_flag_naming_a_missing_file_is_refused_naming_it(bench):
    bench.write_sheet(1, "a", ["task-a"])
    missing = bench.tmp_path / "absent-policy.yaml"
    message = bench.refused(missing)
    assert "absent-policy.yaml" in message


# --- broken_sibling_entry_not_blocking -----------------------------------------


def test_a_broken_default_entry_does_not_block_a_run_stamped_under_a_valid_task(bench):
    broken_default = _entry(bench.obligations_file("a"))
    del broken_default["expected_slices"]
    policy = bench.policy(
        {"task-a": broken_default, "task-b": _entry(bench.obligations_file("b"))}
    )
    bench.write_sheet(1, "b", ["task-b"])
    report = bench.report(policy)
    assert (report["task_id"], report["task_id_source"]) == ("task-b", "graded")
    assert _node_outcomes(report, 1) == {
        "beta_group": {"tests/test_hZ.py::test_beta_only": "passed"}
    }


def test_a_run_stamped_under_a_broken_entry_is_refused_naming_the_task_and_key(bench):
    broken = _entry(bench.obligations_file("b"))
    del broken["expected_slices"]
    policy = bench.policy(
        {"task-a": _entry(bench.obligations_file("a")), "task-b": broken}
    )
    bench.write_sheet(1, "b", ["task-b"])
    message = bench.refused(policy)
    assert "task-b" in message and "expected_slices" in message
