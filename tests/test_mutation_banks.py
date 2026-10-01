"""Validate every task's mutation bank named in the real policy.yaml.

dev_check.load_mutation_bank re-checks the slice being graded at grading
time; these tests check each bank as a whole, so a malformed bank is caught
before any run is graded against it. Mutant behaviour itself (every mutant
killable by a correct suite, few killed by a weak one, none by the frozen
suite) is validated against each task's reference implementation and
recorded in that task's reference README -- it needs the task's own
dependencies, which this repo's requirements deliberately exclude.
"""

from __future__ import annotations

import builtins
import importlib
import importlib.util
import re
import sys
import uuid
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import bench_lib  # noqa: E402
import dev_check  # noqa: E402

_POLICY = yaml.safe_load((REPO_ROOT / "policy.yaml").read_text(encoding="utf-8"))
_SLICE_LIST_RE = re.compile(r"^slice(\d+)\.txt$")


def _load_hook(bank_dir: Path) -> Any:
    """Import the bank's sitecustomize.py by file path under a unique module
    name, so it never collides with the interpreter's own sitecustomize."""
    spec = importlib.util.spec_from_file_location(
        f"mutation_bank_{uuid.uuid4().hex}", bank_dir / "sitecustomize.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("task_id", sorted(_POLICY["tasks"]))
def test_bank_is_inert_unset_and_its_slice_lists_partition_its_registry(
    task_id: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """For one configured task's bank:

    - sitecustomize.py loads with MUTATION unset and installs no hook;
    - every id in slice1..slice<expected_slices>.txt is registered in
      all_mutation_ids() (parse_mutation_list itself refuses an empty or
      duplicated list);
    - every registered id is owned by exactly one `slice<N>.txt` in the bank
      directory -- counted over every list there, not only this task's own
      slices, because one bank may serve plans of different lengths (the
      shorter plan never reads the later lists). A registered mutant no list
      owns would never be measured; one owned twice would count under two
      slices.
    """
    monkeypatch.delenv("MUTATION", raising=False)
    task = bench_lib.resolve_task(_POLICY, task_id)
    bank_dir = REPO_ROOT / task["mutations_dir"]
    assert (bank_dir / "sitecustomize.py").is_file(), (
        f"task {task_id!r} has no bank hook at {bank_dir}"
    )

    hooks_before = (builtins.__import__, importlib.import_module, importlib.reload)
    module = _load_hook(bank_dir)
    assert (
        builtins.__import__,
        importlib.import_module,
        importlib.reload,
    ) == hooks_before
    registered = list(module.all_mutation_ids())

    for slice_number in range(1, task["expected_slices"] + 1):
        ids = dev_check.parse_mutation_list(bank_dir / f"slice{slice_number}.txt")
        unregistered = [mutant for mutant in ids if mutant not in registered]
        assert not unregistered, (
            f"{task_id} slice {slice_number} lists unregistered ids {unregistered}"
        )

    owners: dict[str, list[str]] = {}
    for path in sorted(bank_dir.iterdir()):
        if _SLICE_LIST_RE.match(path.name):
            for mutant in dev_check.parse_mutation_list(path):
                owners.setdefault(mutant, []).append(path.name)
    misowned = {
        mutant: owners.get(mutant, [])
        for mutant in registered
        if len(owners.get(mutant, [])) != 1
    }
    assert not misowned, (
        f"{task_id}: registered ids not owned by exactly one slice list: {misowned}"
    )
