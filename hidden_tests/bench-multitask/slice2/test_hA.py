"""Slice 2 hidden tests: `dev_check.py` and `grade_run.py` become task-aware,
derived from docs/plans/MULTI-TASK-PLAN-3SLICE.md's Slice 2 Acceptance
Criteria.

Not visible to the Developer model. Copied into the grading worktree's tests/
directory and run there. Every grade is a real end-to-end `dev_check.main` /
`grade_run.main` run over a fixture policy, a real throwaway git repository
with a real trial worktree, and a fixture run directory; external
dependencies are stubbed only through policy.yaml itself (a stub `pm_lib`
under `pm_scripts_dir`, lint/health scripts that do not exist and so are
recorded as unavailable). No tool internal is imported or monkeypatched.

Paths a task entry holds relative to the bench root (provenance, hidden tests,
obligations) live in a uniquely named directory inside the bench root,
removed after each test; sheets grade_run.py writes under results/runs/ use a
unique run id and are removed the same way.
"""

import json
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import dev_check  # noqa: E402
import grade_run  # noqa: E402

PINNED = "0123456789abcdef0123456789abcdef01234567"
PLAN_TEXT = "# Fixture plan\n\n## Slice 1: fixture slice\n"
HIDDEN_FILES = {
    "test_hC.py": "def test_fixture_passes():\n    assert True\n",
    "test_hD.py": "def test_fixture_fails():\n    assert False\n\n\ndef test_fixture_also_passes():\n    assert True\n",
}
GROUPS = [
    {
        "id": "group_c",
        "description": "fixture",
        "tests": ["tests/test_hC.py::test_fixture_passes"],
    },
    {
        "id": "group_d",
        "description": "fixture",
        "tests": [
            "tests/test_hD.py::test_fixture_fails",
            "tests/test_hD.py::test_fixture_also_passes",
        ],
    },
]
MEASUREMENT = {
    "production_paths": ["app/**/*.py"],
    "test_paths": ["checks/**/*.py"],
    "doc_paths": ["notes/**/*.txt"],
}


def _git(*args):
    return subprocess.run(
        [
            "git",
            "-c",
            "user.name=bench",
            "-c",
            "user.email=bench@example.invalid",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _commit_files(repo, files, message):
    for relative, text in files.items():
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        _git("-C", str(repo), "add", relative)
    _git("-C", str(repo), "commit", "-q", "-m", message)
    return _git("-C", str(repo), "rev-parse", "HEAD")


def _make_repo(path):
    path.mkdir(parents=True)
    _git("init", "-q", str(path))
    base = _commit_files(
        path, {"docs/PLAN.md": PLAN_TEXT, "src/legacy.py": "X = 1\n"}, "base"
    )
    return path, base


def _worktrees(repo):
    return set(_git("-C", str(repo), "worktree", "list", "--porcelain").splitlines())


@pytest.fixture(scope="module")
def pm_scripts_dir(tmp_path_factory):
    root = tmp_path_factory.mktemp("pm-scripts")
    package = root / "pm_lib"
    package.mkdir()
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "plan.py").write_text(
        "def parse_plan(path):\n    return ['Slice 1']\n\n\n"
        "def plan_slice_by_id(slices, slice_id):\n    return slice_id if slice_id in slices else None\n\n\n"
        "def effective_authorized_files(plan_slice, run_state):\n    return []\n",
        encoding="utf-8",
    )
    (package / "git_ops.py").write_text(
        "def changed_files_between(repo, before, after, status):\n    return []\n\n\n"
        "def unauthorized_files(changed, authorized):\n    return []\n",
        encoding="utf-8",
    )
    return root


@pytest.fixture
def fixture_dir():
    path = REPO_ROOT / f".hidden-fixture-{uuid.uuid4().hex}"
    path.mkdir()
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


class Bench:
    """One fixture world: a substrate repo with a trial worktree carrying one
    attempt commit, a task registry pointing at it, and a PM run directory."""

    def __init__(self, tmp_path, fixture_dir, pm_scripts_dir):
        self.tmp_path = tmp_path
        self.fixture_dir = fixture_dir
        self.rel = fixture_dir.relative_to(REPO_ROOT).as_posix()
        self.pm_scripts_dir = pm_scripts_dir
        self.run_id = f"hidden-mt-{uuid.uuid4().hex[:12]}"
        self.grading_root = tmp_path / "grading"
        self.substrate, self.base = _make_repo(tmp_path / "substrate")
        self.trial = tmp_path / "substrate-trial-1"
        _git(
            "-C",
            str(self.substrate),
            "worktree",
            "add",
            "-q",
            "-b",
            "trial-1",
            str(self.trial),
        )
        self.decoy, _ = _make_repo(tmp_path / "decoy")
        (fixture_dir / "PLAN.provenance.md").write_text(
            f"# Provenance\n\nPinned commit: `{PINNED}`\n", encoding="utf-8"
        )
        hidden = fixture_dir / "hidden" / "slice1"
        hidden.mkdir(parents=True)
        for name, text in HIDDEN_FILES.items():
            (hidden / name).write_text(text, encoding="utf-8")
        self.write_obligations({1: {"obligations": GROUPS}})

    def write_obligations(self, slices, *, plan="docs/PLAN.md", plan_pin=PINNED):
        path = self.fixture_dir / "obligations.yaml"
        path.write_text(
            yaml.safe_dump(
                {"version": 1, "plan": plan, "plan_pin": plan_pin, "slices": slices}
            ),
            encoding="utf-8",
        )
        return path

    def entry(self, repo):
        return {
            "repo": str(repo),
            "branch_prefix": "pm-eval-fixture",
            "worktree_root": None,
            "plan_file": "docs/PLAN.md",
            "provenance_file": f"{self.rel}/PLAN.provenance.md",
            "hidden_tests_dir": f"{self.rel}/hidden",
            "obligations_file": f"{self.rel}/obligations.yaml",
            "expected_slices": 1,
            "measurement": json.loads(json.dumps(MEASUREMENT)),
        }

    def policy(self, *, default_task="fixture-task", extra_tasks=None):
        tasks = {
            "fixture-task": self.entry(self.substrate),
            "decoy-task": self.entry(self.decoy),
        }
        tasks.update(extra_tasks or {})
        policy = {
            "backend": "local",
            "pm_scripts_dir": str(self.pm_scripts_dir),
            "lint_script": str(self.tmp_path / "no-such-lint.py"),
            "health_script": str(self.tmp_path / "no-such-health.py"),
            "python_interpreter": sys.executable,
            "grading_worktree_root": str(self.grading_root),
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

    def attempt_commit(self, label="1"):
        return _commit_files(
            self.trial,
            {
                "app/core.py": f"def answer():\n    value = {label}\n    return value\n",
                "checks/check_core.py": "def check_answer():\n    return True\n",
                "notes/readme.txt": f"fixture notes {label}\n",
                "src/legacy.py": "X = 1\nY = 2\nZ = 3\nW = 4\nV = 5\n",
            },
            f"attempt {label}",
        )

    def live_run(self, *, repo=None):
        """An in-progress run whose current slice is Slice 1."""
        return self._run_dir(
            {
                "status": "active",
                "current_slice": {
                    "id": "Slice 1",
                    "attempts": 0,
                    "before_head": self.base,
                },
                "slices": [{"id": "Slice 1", "status": None, "attempts": 0}],
            },
            ["launch"],
            repo=repo,
        )

    def finished_run(self, final_commit, launches):
        """A completed run whose Slice 1 was accepted at `final_commit`."""
        return self._run_dir(
            {
                "status": "complete",
                "slices": [
                    {
                        "id": "Slice 1",
                        "status": "accepted",
                        "attempts": len(launches) - 1,
                        "commit": final_commit,
                        "reviews": [{"before_head": self.base, "head": final_commit}],
                    }
                ],
            },
            [*launches, "complete"],
        )

    def _run_dir(self, state, kinds, *, repo=None):
        run_dir = self.tmp_path / f"pm-run-{uuid.uuid4().hex[:8]}"
        run_dir.mkdir()
        run_repo = repo or self.trial
        run_state = {
            "run_id": self.run_id,
            "repo": str(run_repo),
            "stop_reason": None,
            "plan": {
                "path": str(run_repo / "docs" / "PLAN.md"),
                "sha256": "fixture-plan-hash",
            },
            "harness": {"model": "fixture/model"},
            **state,
        }
        (run_dir / "run.json").write_text(json.dumps(run_state), encoding="utf-8")
        events = [{"kind": kind, "slice": "Slice 1", "note": kind} for kind in kinds]
        (run_dir / "events.jsonl").write_text(
            "".join(json.dumps(e) + "\n" for e in events), encoding="utf-8"
        )
        return run_dir

    def dev_check(self, run_dir, policy, commit, out, *extra):
        argv = [
            "--run-dir",
            str(run_dir),
            "--slice",
            "1",
            "--policy",
            str(policy),
            "--commit",
            commit,
            "--out",
            str(out),
        ]
        return dev_check.main([*argv, *extra])

    def results_dir(self):
        return REPO_ROOT / "results" / "runs" / self.run_id


@pytest.fixture
def bench(tmp_path, fixture_dir, pm_scripts_dir):
    world = Bench(tmp_path, fixture_dir, pm_scripts_dir)
    try:
        yield world
    finally:
        shutil.rmtree(world.results_dir(), ignore_errors=True)


def _sheet(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _names_path(message, path):
    return str(path) in message or str(Path(path).resolve()) in message


# --- task_flag_threading -------------------------------------------------------


def _grade_finished(bench, commits, launches):
    run_dir = bench.finished_run(commits[-1], launches)
    rc = grade_run.main(
        [
            "--run-dir",
            str(run_dir),
            "--policy",
            str(bench.policy(default_task="decoy-task")),
            "--task",
            "fixture-task",
        ]
    )
    return rc, _sheet(bench.results_dir() / "slice-1.json")


def test_grade_run_threads_task_to_every_attempt_on_the_git_walk_path(bench):
    """Two launches, two commits: every attempt is graded, each under the
    explicit --task, although the policy's default_task names a task whose
    repository this run does not belong to."""
    commits = [bench.attempt_commit("1"), bench.attempt_commit("2")]
    rc, sheet = _grade_finished(bench, commits, ["launch", "steer"])
    assert rc == 0
    attempts = sorted(sheet["attempts"], key=lambda a: a["attempt"])
    assert [a["attempt"] for a in attempts] == [0, 1]
    assert [a["commit_sha"] for a in attempts] == commits
    assert [a["provenance"]["task_id"] for a in attempts] == [
        "fixture-task",
        "fixture-task",
    ]


def test_grade_run_threads_task_on_the_final_attempt_fallback_path(bench):
    """Two launches but three commits: the walk refuses, only the final
    attempt is graded, still under the explicit --task."""
    commits = [
        bench.attempt_commit("1"),
        bench.attempt_commit("2"),
        bench.attempt_commit("3"),
    ]
    _rc, sheet = _grade_finished(bench, commits, ["launch", "steer"])
    assert [
        (a["attempt"], a["commit_sha"], a["provenance"]["task_id"])
        for a in sheet["attempts"]
    ] == [(1, commits[-1], "fixture-task")]


def test_grade_run_unknown_task_is_refused_before_anything_is_graded(bench):
    commit = bench.attempt_commit()
    run_dir = bench.finished_run(commit, ["launch"])
    before = _worktrees(bench.substrate)
    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "tools" / "grade_run.py"),
            "--run-dir",
            str(run_dir),
            "--policy",
            str(bench.policy()),
            "--task",
            "does-not-exist",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert result.returncode != 0
    # Naming the configured ids shows the refusal came from task resolution,
    # not from an argument parser that does not know --task at all.
    assert "does-not-exist" in result.stderr and "fixture-task" in result.stderr
    assert not bench.results_dir().exists()
    assert _worktrees(bench.substrate) == before


def test_dev_check_unknown_task_is_refused_naming_it_and_the_configured_ids(bench):
    commit = bench.attempt_commit()
    out = bench.tmp_path / "sheet.json"
    with pytest.raises(dev_check.DevCheckError) as excinfo:
        bench.dev_check(
            bench.live_run(), bench.policy(), commit, out, "--task", "does-not-exist"
        )
    message = str(excinfo.value)
    assert (
        "does-not-exist" in message
        and "fixture-task" in message
        and "decoy-task" in message
    )
    assert not out.exists()


# --- filename_derivation -------------------------------------------------------


def test_hidden_test_files_are_derived_from_the_obligations_and_actually_run(bench):
    """The fixture obligations name test_hC.py and test_hD.py, never
    test_hA.py/test_hB.py; their real outcomes must reach the sheet."""
    commit = bench.attempt_commit()
    out = bench.tmp_path / "sheet.json"
    assert (
        bench.dev_check(
            bench.live_run(), bench.policy(), commit, out, "--task", "fixture-task"
        )
        == 0
    )
    correctness = _sheet(out)["attempts"][0]["correctness"]
    assert correctness["by_node"] == {
        "tests/test_hC.py::test_fixture_passes": "passed",
        "tests/test_hD.py::test_fixture_fails": "failed",
        "tests/test_hD.py::test_fixture_also_passes": "passed",
    }
    by_obligation = {
        gid: (g["passed"], g["total"])
        for gid, g in correctness["by_obligation"].items()
    }
    assert by_obligation == {"group_c": (1, 1), "group_d": (1, 2)}


def test_slice_whose_obligations_reference_no_test_file_is_refused_before_any_worktree(
    bench,
):
    obligations = bench.write_obligations({1: {"obligations": []}})
    commit = bench.attempt_commit()
    out = bench.tmp_path / "sheet.json"
    before = _worktrees(bench.substrate)
    with pytest.raises(dev_check.DevCheckError) as excinfo:
        bench.dev_check(
            bench.live_run(), bench.policy(), commit, out, "--task", "fixture-task"
        )
    assert obligations.name in str(excinfo.value)
    assert _worktrees(bench.substrate) == before
    assert not out.exists()


# --- plan_consistency ----------------------------------------------------------


def test_obligations_plan_disagreeing_with_the_task_plan_file_names_both(bench):
    bench.write_obligations({1: {"obligations": GROUPS}}, plan="docs/OTHER_PLAN.md")
    commit = bench.attempt_commit()
    out = bench.tmp_path / "sheet.json"
    with pytest.raises(dev_check.DevCheckError) as excinfo:
        bench.dev_check(
            bench.live_run(), bench.policy(), commit, out, "--task", "fixture-task"
        )
    assert "docs/OTHER_PLAN.md" in str(excinfo.value) and "docs/PLAN.md" in str(
        excinfo.value
    )
    assert not out.exists()


def test_obligations_plan_pin_disagreeing_with_the_provenance_names_both(bench):
    stale_pin = "fedcba9876543210fedcba9876543210fedcba98"
    bench.write_obligations({1: {"obligations": GROUPS}}, plan_pin=stale_pin)
    commit = bench.attempt_commit()
    out = bench.tmp_path / "sheet.json"
    with pytest.raises(dev_check.DevCheckError) as excinfo:
        bench.dev_check(
            bench.live_run(), bench.policy(), commit, out, "--task", "fixture-task"
        )
    assert stale_pin in str(excinfo.value) and PINNED in str(excinfo.value)
    assert not out.exists()


# --- run_repository_cross_check ------------------------------------------------


def test_run_recorded_in_a_real_worktree_of_the_configured_repo_grades(bench):
    commit = bench.attempt_commit()
    out = bench.tmp_path / "sheet.json"
    assert bench.trial.resolve() != bench.substrate.resolve()
    assert (
        bench.dev_check(
            bench.live_run(), bench.policy(), commit, out, "--task", "fixture-task"
        )
        == 0
    )
    assert _sheet(out)["attempts"][0]["commit_sha"] == commit


def test_run_recorded_in_a_foreign_worktree_is_refused_naming_both_repositories(bench):
    foreign_trial = bench.tmp_path / "decoy-trial-1"
    _git(
        "-C",
        str(bench.decoy),
        "worktree",
        "add",
        "-q",
        "-b",
        "trial-1",
        str(foreign_trial),
    )
    commit = _commit_files(
        foreign_trial, {"app/core.py": "VALUE = 1\n"}, "foreign attempt"
    )
    out = bench.tmp_path / "sheet.json"
    with pytest.raises(dev_check.DevCheckError) as excinfo:
        bench.dev_check(
            bench.live_run(repo=foreign_trial),
            bench.policy(),
            commit,
            out,
            "--task",
            "fixture-task",
        )
    message = str(excinfo.value)
    assert _names_path(message, foreign_trial) and _names_path(message, bench.substrate)
    assert not out.exists()


# --- measurement_per_task ------------------------------------------------------


def test_loc_buckets_classify_the_diff_by_the_tasks_own_globs(bench):
    """app/ is production and src/ unclassified under this task's globs --
    the reverse of the relative-velocity layout -- so a global or default
    glob read cannot reproduce these numbers."""
    commit = bench.attempt_commit()
    out = bench.tmp_path / "sheet.json"
    assert (
        bench.dev_check(
            bench.live_run(), bench.policy(), commit, out, "--task", "fixture-task"
        )
        == 0
    )
    loc = _sheet(out)["attempts"][0]["size_complexity"]["loc"]
    buckets = {
        name: (b["added"], b["deleted"], b["net"], b["files"])
        for name, b in loc["buckets"].items()
    }
    assert buckets == {
        "production": (3, 0, 3, ["app/core.py"]),
        "test": (2, 0, 2, ["checks/check_core.py"]),
        "doc": (1, 0, 1, ["notes/readme.txt"]),
        "unclassified": (4, 0, 4, ["src/legacy.py"]),
    }
    assert loc["loc_definition"] == "net_physical_lines"


# --- provenance_task_id --------------------------------------------------------


def test_every_attempt_provenance_carries_the_resolved_task_id_explicit_and_default(
    bench,
):
    """default_task names a non-first entry; omitting --task must stamp it,
    and an explicit --task must stamp the explicit id instead."""
    commit = bench.attempt_commit()
    policy = bench.policy(
        default_task="alt-task", extra_tasks={"alt-task": bench.entry(bench.substrate)}
    )
    default_out = bench.tmp_path / "default.json"
    explicit_out = bench.tmp_path / "explicit.json"
    assert bench.dev_check(bench.live_run(), policy, commit, default_out) == 0
    assert (
        bench.dev_check(
            bench.live_run(), policy, commit, explicit_out, "--task", "fixture-task"
        )
        == 0
    )
    default_provenance = _sheet(default_out)["attempts"][0]["provenance"]
    explicit_provenance = _sheet(explicit_out)["attempts"][0]["provenance"]
    assert default_provenance["task_id"] == "alt-task"
    assert explicit_provenance["task_id"] == "fixture-task"
    for provenance in (default_provenance, explicit_provenance):
        assert all(
            provenance.get(key)
            for key in ("plan_hash", "obligations_hash", "hidden_tests_hash")
        )
