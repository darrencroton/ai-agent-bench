"""Tests for tools/quality_panel.py.

Run with plain pytest from the repo root. A throwaway git repo and a
hand-written run.json/scoring sheet stand in for a graded PM run, and a stub
`delegate_jobs.py` written under tmp_path stands in for the orchestrator
launcher: it implements init/launch/wait/extract/cancel by writing canned
files, so no real reviewer is ever launched.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import quality_panel  # noqa: E402

RUN_ID = "run-a1"
PLAN_FILE = "docs/MERGER_RATE_PLAN-2SLICE.md"

GOOD_OUTPUT = """SECTION: SCORES
correctness_beyond_tests: 4
design: 3
readability_docs: 5
tests: 2
contract_discipline: 4
SECTION: EVIDENCE
- src/a.py:10 -- handles the empty case explicitly
- tests/test_a.py:3 -- only the happy path is asserted
SECTION: SUMMARY
Solid slice. Tests are thin.
"""

# The stub launcher. Its behaviour for wait/extract comes from stub.json next
# to it, so each test controls the delegate's outcome without a real harness.
_STUB = r"""
import json, os, sys
from pathlib import Path

config = json.loads((Path(__file__).parent / "stub.json").read_text())
args = sys.argv[1:]
command = args[0]
opts = dict(zip(args[1::2], args[2::2]))
root = Path(os.environ["ORCHESTRATOR_ARTIFACT_ROOT"])
if command == "init":
    index = len(list(root.glob(opts["--prefix"] + "-*")))
    run_dir = root / f"{opts['--prefix']}-{index}"
    run_dir.mkdir(parents=True)
    print(run_dir)
elif command == "launch":
    run_dir = Path(opts["--run-dir"])
    request = json.loads(Path(opts["--request"]).read_text())
    (run_dir / f"{request['label']}-prompt.md").write_text("PROMPT\n" + request["task"])
elif command == "wait":
    print(f"{opts['--label']}: state={config['wait_state']}")
    sys.exit(config["wait_rc"])
elif command == "extract":
    print(config["output"])
elif command == "cancel":
    (Path(opts["--run-dir"]) / "cancelled").write_text("")
"""


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def _make_repo(tmp_path: Path) -> tuple[Path, str, str]:
    """A throwaway repo with the plan committed, plus one Developer commit."""
    repo = tmp_path / "dev-repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "docs").mkdir()
    (repo / PLAN_FILE).write_text("plan\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "plan")
    base = _git(repo, "rev-parse", "HEAD")
    (repo / "src").mkdir()
    (repo / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "work")
    return repo, base, _git(repo, "rev-parse", "HEAD")


def _panel_block(tmp_path: Path, **overrides: Any) -> dict[str, Any]:
    block = {
        "tool": "claude",
        "model": "claude-opus-5-5",
        "effort": "high",
        "rubric_file": str(REPO_ROOT / "docs" / "QUALITY-PANEL-RUBRIC.md"),
        "orchestrator_scripts_dir": str(tmp_path / "scripts"),
        "artifact_root": str(tmp_path / "artifacts"),
        "timeout_seconds": 60,
    }
    block.update(overrides)
    return block


def _write_policy(tmp_path: Path, repo: Path, panel: dict[str, Any] | None) -> Path:
    """The real policy.yaml with its task registry replaced by one entry
    pointing at the throwaway `repo` (plan/provenance files are the real
    frozen ones under the bench root) and its quality_panel block replaced by
    `panel` (dropped when None). Starting from the real file keeps the shared
    sections dev_check.load_policy requires in step with it."""
    policy: dict[str, Any] = yaml.safe_load(
        (REPO_ROOT / "policy.yaml").read_text(encoding="utf-8")
    )
    policy.pop("quality_panel")
    policy["grading_worktree_root"] = str(tmp_path / "grading")
    policy["untagged_sheet_task"] = "fixture-task"
    policy["tasks"] = {
        "fixture-task": {
            "repo": str(repo),
            "branch_prefix": "pm-eval-v2",
            "worktree_root": None,
            "plan_file": PLAN_FILE,
            "provenance_file": "docs/MERGER_RATE_PLAN-2SLICE.provenance.md",
            "hidden_tests_dir": "hidden_tests",
            "obligations_file": "hidden_tests/obligations.yaml",
            "mutations_dir": "hidden_tests/mutations",
            "expected_slices": 2,
            "measurement": {
                "production_paths": ["src/**/*.py"],
                "test_paths": ["tests/**/*.py"],
                "doc_paths": ["docs/**/*.md", "*.md"],
            },
        }
    }
    if panel is not None:
        policy["quality_panel"] = panel
    path = tmp_path / "policy.yaml"
    path.write_text(yaml.safe_dump(policy, sort_keys=False), encoding="utf-8")
    return path


@pytest.fixture
def run(tmp_path: Path) -> dict[str, Any]:
    """A graded run: repo, run.json, a sheet with an accepted attempt 0, the stub launcher and policy."""
    repo, base, commit = _make_repo(tmp_path)
    run_dir = tmp_path / "pm-run"
    run_dir.mkdir()
    (run_dir / "run.json").write_text(
        json.dumps(
            {
                "run_id": RUN_ID,
                "repo": str(repo),
                "plan": {"path": str(repo / PLAN_FILE)},
                "slices": [],
            }
        ),
        encoding="utf-8",
    )
    sheet = {
        "run_id": RUN_ID,
        "slice": 1,
        "developer": {"model": "test/model"},
        "run_status": {"pm_status": "completed"},
        "attempts": [
            {
                "attempt": 0,
                "commit_sha": commit,
                "provenance": {"task_id": "fixture-task", "base_commit": base},
                "correctness": {"score": 0.5},
                "reviews": [{"event_index": 3}],
            }
        ],
        "accepted_at_attempt": 0,
        "pm_model_performance_ref": None,
    }
    sheet_path = tmp_path / "sheet.json"
    sheet_path.write_text(json.dumps(sheet, indent=2) + "\n", encoding="utf-8")
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "delegate_jobs.py").write_text(_STUB, encoding="utf-8")
    _configure_stub(tmp_path)
    policy_path = _write_policy(tmp_path, repo, _panel_block(tmp_path))
    argv = [
        "--run-dir",
        str(run_dir),
        "--slice",
        "1",
        "--policy",
        str(policy_path),
        "--sheet",
        str(sheet_path),
        "--task",
        "fixture-task",
    ]
    return {
        "tmp": tmp_path,
        "repo": repo,
        "base": base,
        "commit": commit,
        "sheet_path": sheet_path,
        "argv": argv,
    }


def _configure_stub(
    tmp_path: Path,
    *,
    output: str = GOOD_OUTPUT,
    wait_rc: int = 0,
    wait_state: str = "completed",
) -> None:
    (tmp_path / "scripts" / "stub.json").write_text(
        json.dumps({"output": output, "wait_rc": wait_rc, "wait_state": wait_state}),
        encoding="utf-8",
    )


class TestCommission:
    def test_happy_path_appends_one_record_and_leaves_everything_else_identical(
        self, run: dict[str, Any]
    ) -> None:
        before = json.loads(run["sheet_path"].read_text())

        assert quality_panel.main(run["argv"]) == 0

        after = json.loads(run["sheet_path"].read_text())
        records = after["attempts"][0].pop("quality_panel")
        assert after == before
        assert len(records) == 1
        record = records[0]
        assert record["scores"] == {
            "correctness_beyond_tests": 4,
            "design": 3,
            "readability_docs": 5,
            "tests": 2,
            "contract_discipline": 4,
        }
        assert record["evidence"] == [
            "src/a.py:10 -- handles the empty case explicitly",
            "tests/test_a.py:3 -- only the happy path is asserted",
        ]
        assert record["summary"] == "Solid slice. Tests are thin."
        assert (record["tool"], record["model"], record["effort"]) == (
            "claude",
            "claude-opus-5-5",
            "high",
        )
        assert (record["commit_sha"], record["before_head"]) == (
            run["commit"],
            run["base"],
        )
        rubric = REPO_ROOT / "docs" / "QUALITY-PANEL-RUBRIC.md"
        assert (
            record["rubric_sha256"] == hashlib.sha256(rubric.read_bytes()).hexdigest()
        )
        prompt = Path(record["delegate_run_dir"]) / f"{record['label']}-prompt.md"
        assert (
            record["prompt_sha256"] == hashlib.sha256(prompt.read_bytes()).hexdigest()
        )
        assert record["label"] == "01-claude-quality-panel"
        # The disposable worktree is gone and was never the Developer's repo.
        assert not any((run["tmp"] / "grading").iterdir())

    def test_a_second_commission_appends_a_second_record(
        self, run: dict[str, Any]
    ) -> None:
        assert quality_panel.main(run["argv"]) == 0
        assert quality_panel.main(run["argv"]) == 0
        records = json.loads(run["sheet_path"].read_text())["attempts"][0][
            "quality_panel"
        ]
        assert len(records) == 2
        assert records[0]["delegate_run_dir"] != records[1]["delegate_run_dir"]

    @pytest.mark.parametrize(
        ("output", "message"),
        [
            (GOOD_OUTPUT.replace("design: 3\n", ""), "missing dimension(s): design"),
            (GOOD_OUTPUT.replace("tests: 2", "tests: 6"), "'tests' is '6'"),
            (
                GOOD_OUTPUT.replace("design: 3\n", "design: 3\ndesign: 4\n"),
                "'design' more than once",
            ),
            (
                GOOD_OUTPUT.replace("design: 3", "**design**: 3"),
                "is not `<dimension>: <1-5>`",
            ),
            (GOOD_OUTPUT.split("SECTION: SUMMARY")[0], "missing section(s): SUMMARY"),
        ],
    )
    def test_malformed_scores_are_a_named_error_and_the_sheet_is_untouched(
        self, run: dict[str, Any], output: str, message: str
    ) -> None:
        _configure_stub(run["tmp"], output=output)
        before = run["sheet_path"].read_bytes()
        with pytest.raises(
            quality_panel.QualityPanelError, match=f"{re.escape(message)}.*delegate run"
        ):
            quality_panel.main(run["argv"])
        assert run["sheet_path"].read_bytes() == before

    def test_wait_failure_names_the_run_dir_cancels_and_writes_nothing(
        self, run: dict[str, Any]
    ) -> None:
        _configure_stub(run["tmp"], wait_rc=1, wait_state="incomplete")
        before = run["sheet_path"].read_bytes()
        with pytest.raises(
            quality_panel.QualityPanelError, match="state=incomplete"
        ) as excinfo:
            quality_panel.main(run["argv"])
        run_dir = run["tmp"] / "artifacts" / "quality-panel-0"
        assert str(run_dir) in str(excinfo.value)
        assert (run_dir / "cancelled").exists()
        assert run["sheet_path"].read_bytes() == before

    def test_no_accepted_attempt_and_no_attempt_flag_is_refused(
        self, run: dict[str, Any]
    ) -> None:
        sheet = json.loads(run["sheet_path"].read_text())
        sheet["accepted_at_attempt"] = None
        run["sheet_path"].write_text(json.dumps(sheet), encoding="utf-8")
        with pytest.raises(
            quality_panel.QualityPanelError, match="reads an accepted commit by default"
        ):
            quality_panel.main(run["argv"])
        # An explicit --attempt still works on an unaccepted slice.
        assert quality_panel.main([*run["argv"], "--attempt", "0"]) == 0


class TestPolicyBlock:
    @pytest.mark.parametrize(
        ("overrides", "message"),
        [
            ({"model": ""}, "quality_panel.model must be a non-empty string"),
            ({"tool": None}, "quality_panel.tool must be a non-empty string"),
            (
                {"timeout_seconds": 0},
                "quality_panel.timeout_seconds must be a positive integer",
            ),
            (
                {"timeout_seconds": True},
                "quality_panel.timeout_seconds must be a positive integer",
            ),
            (
                {"rubric_file": "docs/NO-SUCH-RUBRIC.md"},
                "quality_panel.rubric_file .* does not exist",
            ),
        ],
    )
    def test_invalid_block_is_refused_by_key(
        self, tmp_path: Path, overrides: dict[str, Any], message: str
    ) -> None:
        policy_path = _write_policy(
            tmp_path, tmp_path, _panel_block(tmp_path, **overrides)
        )
        with pytest.raises(quality_panel.QualityPanelError, match=message):
            quality_panel.load_policy(policy_path, REPO_ROOT)

    def test_missing_block_is_refused(self, tmp_path: Path) -> None:
        with pytest.raises(
            quality_panel.QualityPanelError, match="no quality_panel mapping"
        ):
            quality_panel.load_policy(
                _write_policy(tmp_path, tmp_path, None), REPO_ROOT
            )

    def test_the_real_policy_block_validates(self) -> None:
        _, panel = quality_panel.load_policy(REPO_ROOT / "policy.yaml", REPO_ROOT)
        assert panel["rubric_path"] == REPO_ROOT / "docs" / "QUALITY-PANEL-RUBRIC.md"
        assert panel["artifact_root"].is_relative_to(REPO_ROOT)


class TestDelegateContract:
    def test_policy_and_request_carry_the_exact_read_only_fields(
        self, tmp_path: Path
    ) -> None:
        worktree = tmp_path / "wt"
        (worktree / "docs").mkdir(parents=True)
        (worktree / PLAN_FILE).write_text("the plan\n", encoding="utf-8")
        plan_sha = hashlib.sha256((worktree / PLAN_FILE).read_bytes()).hexdigest()
        panel = {
            "tool": "claude",
            "model": "m",
            "effort": "high",
            "artifact_root": tmp_path / "art",
        }

        policy = quality_panel.build_delegate_policy(
            run_id=RUN_ID,
            slice_id="Slice 1",
            plan_sha256=plan_sha,
            worktree=worktree,
            panel=panel,
        )
        request = quality_panel.build_delegate_request(
            slice_id="Slice 1",
            plan_sha256=plan_sha,
            plan_file=PLAN_FILE,
            rubric_text="RUBRIC",
            commit="c0ffee",
            before_head="ba5e",
            panel=panel,
        )

        assert policy == {
            "schema_version": 3,
            "run_id": RUN_ID,
            "slice_id": "Slice 1",
            "plan_sha256": plan_sha,
            "repo_path": str(worktree),
            "delegate_artifact_root": str(tmp_path / "art"),
            "required_tools": ["claude"],
            "required_model": "m",
            "required_effort": "high",
            "required_access": ["read-only"],
        }
        assert request["access"] == "read-only"
        assert request["required_skills"] == []
        assert request["files"] == [PLAN_FILE]
        assert request["plan_sha256"] == plan_sha
        assert (request["tool"], request["model"], request["effort"]) == (
            "claude",
            "m",
            "high",
        )
        assert request["label"] == "01-claude-quality-panel"
        assert request["expected_output"] == quality_panel.OUTPUT_CONTRACT
        assert request["task"].startswith("RUBRIC")
        assert "git diff ba5e c0ffee" in request["task"]

    def test_rubric_states_the_same_output_contract_the_parser_accepts(self) -> None:
        rubric = (REPO_ROOT / "docs" / "QUALITY-PANEL-RUBRIC.md").read_text(
            encoding="utf-8"
        )
        assert quality_panel.OUTPUT_CONTRACT in rubric
