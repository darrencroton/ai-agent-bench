"""Mutation bank for the bench-multitask tasks: injects one behavioural defect
into the candidate's own tools after import.

Used by dev_check.py's test_kill_rate measurement, which asks whether the
Developer's OWN test suite can fail. Activated by putting this file's
directory first on PYTHONPATH (the interpreter auto-imports any
sitecustomize.py found there at startup) and setting MUTATION=<id>. With
MUTATION unset, or naming no registered mutant, nothing is installed.

Contract:

- **Post-import, by basename.** Each mutant wraps one plan-named public
  function of `bench_lib`, `dev_check`, `grade_run` or `model_report`
  after the module is imported. Modules are matched by the last component of
  their name, so `import bench_lib`, `from tools import bench_lib` and
  `importlib.import_module("tools.bench_lib")` are all patched, and no trial
  file is ever edited. Three loading paths are hooked: `builtins.__import__`,
  `importlib.import_module` (which bypasses `__import__`) and
  `importlib.reload` (which would otherwise restore the unwrapped function
  while the `__MUTATED__` marker survived).
- **Script runs.** A tool run as a script (`python tools/grade_run.py ...`)
  executes as `__main__`, which no import hook sees. For the three mutants
  that make a CLI ignore a flag, the flag is also removed from `sys.argv` at
  startup when the script's basename matches, so both invocation styles see
  the same defect. Any module the script imports is patched as usual.
- **One mutant, one obligation.** Each id breaks exactly one obligation of
  one slice of `docs/plans/MULTI-TASK-PLAN-3SLICE.md`, behaviourally, through
  the function's own inputs and outputs -- never the candidate's internal
  helpers, whose names the plan leaves free.
- **Structurally incomplete candidates.** `_REQUIRED_API` names the one
  attribute each mutant wraps. A module lacking it leaves that mutant
  uninstalled (so it survives) instead of failing every run.
- **Fail loudly.** A transform that raises, or a failed installation,
  propagates: a broken mutant is an invalid mutant, never evidence that a
  suite's tests survived it.

The mutants, by slice (the owning `slice<N>.txt` lists each id once):

Slice 1 -- `bench_lib`:
  S1_resolve_unknown_falls_back_to_default  resolve_task resolves an unknown
      id to `default_task` instead of raising.
  S1_resolve_fills_missing_key              resolve_task fills a key missing
      from the entry with another entry's value instead of raising.
  S1_resolve_accepts_nonpositive_slices     resolve_task accepts
      `expected_slices <= 0`.
  S1_resolve_none_takes_first_entry         resolve_task(policy, None)
      resolves the registry's first entry, ignoring `default_task`.
  S1_resolve_rejects_null_worktree_root     resolve_task rejects
      `worktree_root: null`.
  S1_resolve_aliases_policy_entry           resolve_task returns the policy's
      own entry object, so mutating the result rewrites the policy.
  S1_membership_by_path_equality            repo_belongs_to_task answers by
      path equality alone, so a registered worktree is not a member.
  S1_membership_false_instead_of_raising    repo_belongs_to_task returns False
      where it should raise (a missing or non-git configured path).
  S1_pin_parse_returns_empty                parse_pinned_plan_commit returns
      "" instead of raising on a missing file or a missing pin line.

Slice 2 -- `dev_check`, `grade_run`:
  S2_dev_check_ignores_task                 dev_check.main drops `--task`, so
      the policy's default task is graded instead.
  S2_provenance_omits_task_id               dev_check.build_provenance omits
      `task_id`.
  S2_grade_run_ignores_task                 grade_run.main drops `--task`, so
      the default task is threaded to every grade.

Slice 3 -- `model_report` (and `bench_lib.resolve_task` as model_report sees it):
  S3_task_id_source_always_graded           build_report reports
      `task_id_source: "graded"` even for a backfilled run.
  S3_explicit_null_task_id_backfilled       build_report silently backfills
      an attempt whose provenance records `task_id: null`.
  S3_middle_attempts_not_inspected          build_report sees every middle
      attempt carrying the first attempt's task_id state, as if only the
      first and final attempts were inspected.
  S3_obligations_from_bench_root_default    bench_lib.resolve_task, when
      called from model_report, reports the bench-root default
      `hidden_tests/obligations.yaml` as the task's obligations_file, so the
      report is reconstructed against the default rubric, not the task's.
  S3_model_report_ignores_policy            model_report.main drops
      `--policy`, so the bench-root policy is read instead.
  S3_correctness_provenance_drops_task_id   resolve_correctness_provenance
      drops its per-slice `task_id` echo.
"""

import copy
import functools
import importlib
import os
import sys

MUT = os.environ.get("MUTATION")

# Mutant id -> (module basename, the one public attribute it wraps), in slice
# order. This is the registry all_mutation_ids() reads.
_REQUIRED_API = {
    "S1_resolve_unknown_falls_back_to_default": ("bench_lib", "resolve_task"),
    "S1_resolve_fills_missing_key": ("bench_lib", "resolve_task"),
    "S1_resolve_accepts_nonpositive_slices": ("bench_lib", "resolve_task"),
    "S1_resolve_none_takes_first_entry": ("bench_lib", "resolve_task"),
    "S1_resolve_rejects_null_worktree_root": ("bench_lib", "resolve_task"),
    "S1_resolve_aliases_policy_entry": ("bench_lib", "resolve_task"),
    "S1_membership_by_path_equality": ("bench_lib", "repo_belongs_to_task"),
    "S1_membership_false_instead_of_raising": ("bench_lib", "repo_belongs_to_task"),
    "S1_pin_parse_returns_empty": ("bench_lib", "parse_pinned_plan_commit"),
    "S2_dev_check_ignores_task": ("dev_check", "main"),
    "S2_provenance_omits_task_id": ("dev_check", "build_provenance"),
    "S2_grade_run_ignores_task": ("grade_run", "main"),
    "S3_task_id_source_always_graded": ("model_report", "build_report"),
    "S3_explicit_null_task_id_backfilled": ("model_report", "build_report"),
    "S3_middle_attempts_not_inspected": ("model_report", "build_report"),
    "S3_obligations_from_bench_root_default": ("bench_lib", "resolve_task"),
    "S3_model_report_ignores_policy": ("model_report", "main"),
    "S3_correctness_provenance_drops_task_id": (
        "model_report",
        "resolve_correctness_provenance",
    ),
}

# What a model_report that ignores the task's own obligations file loads.
_BENCH_ROOT_DEFAULT_OBLIGATIONS = "hidden_tests/obligations.yaml"

# The CLI-flag mutants: mutant id -> (script basename, flag removed).
_DROPPED_FLAGS = {
    "S2_dev_check_ignores_task": ("dev_check.py", "--task"),
    "S2_grade_run_ignores_task": ("grade_run.py", "--task"),
    "S3_model_report_ignores_policy": ("model_report.py", "--policy"),
}


def all_mutation_ids():
    """Every registered mutant id, in slice order."""
    return tuple(_REQUIRED_API)


# ------------------------------------------------------------------ helpers


def _without_flag(argv, flag):
    """`argv` with every `flag <value>` and `flag=<value>` removed."""
    out = []
    skip = False
    for arg in argv:
        if skip:
            skip = False
        elif arg == flag:
            skip = True
        elif not str(arg).startswith(flag + "="):
            out.append(arg)
    return out


def _tasks(policy):
    """The policy's `tasks:` mapping, or None when it is not a usable one --
    the mutant then defers to the real function's own handling."""
    tasks = policy.get("tasks") if isinstance(policy, dict) else None
    return tasks if isinstance(tasks, dict) and tasks else None


def _with_entry(policy, task_id, entry):
    """A copy of `policy` whose `tasks[task_id]` is `entry` (never mutates
    the caller's policy)."""
    patched = dict(policy)
    patched["tasks"] = dict(policy["tasks"])
    patched["tasks"][task_id] = entry
    return patched


def _requested_id(policy, task_id):
    return policy.get("default_task") if task_id is None else task_id


def _sheet_dicts(value):
    """Every scoring-sheet dict (a dict carrying an `attempts` list) inside
    `value`, however build_report's sheets argument is shaped."""
    if isinstance(value, dict):
        if isinstance(value.get("attempts"), list):
            yield value
        else:
            for item in value.values():
                yield from _sheet_dicts(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _sheet_dicts(item)


def _ordered_attempts(sheet):
    attempts = [a for a in sheet["attempts"] if isinstance(a, dict)]
    return sorted(
        attempts,
        key=lambda a: a.get("attempt") if isinstance(a.get("attempt"), int) else 0,
    )


def _rewrite_sheets(args, kwargs, rewrite):
    """Deep copies of build_report's arguments with `rewrite(sheet)` applied
    to every sheet, so the caller's own sheet objects stay untouched."""
    args, kwargs = copy.deepcopy(args), copy.deepcopy(kwargs)
    for sheet in _sheet_dicts([args, kwargs]):
        rewrite(sheet)
    return args, kwargs


def _drop_null_task_ids(sheet):
    for attempt in sheet["attempts"]:
        provenance = attempt.get("provenance") if isinstance(attempt, dict) else None
        if (
            isinstance(provenance, dict)
            and "task_id" in provenance
            and provenance["task_id"] is None
        ):
            del provenance["task_id"]


def _mirror_first_attempt_onto_middles(sheet):
    ordered = _ordered_attempts(sheet)
    if len(ordered) < 3:
        return
    first_provenance = ordered[0].get("provenance")
    stamped = isinstance(first_provenance, dict) and "task_id" in first_provenance
    for middle in ordered[1:-1]:
        provenance = middle.get("provenance")
        if not isinstance(provenance, dict):
            provenance = {}
            middle["provenance"] = provenance
        if stamped:
            provenance["task_id"] = first_provenance["task_id"]
        else:
            provenance.pop("task_id", None)


def _report_of(result):
    """build_report's report dict, whether it returns the report alone or a
    (report, problems) tuple."""
    if isinstance(result, tuple) and result and isinstance(result[0], dict):
        return result[0]
    return result if isinstance(result, dict) else None


# ---------------------------------------------------------------- transforms


def _patch_bench_lib(m):
    error = getattr(m, "BenchLibError", Exception)

    if MUT == "S1_resolve_unknown_falls_back_to_default":
        o = m.resolve_task

        @functools.wraps(o)
        def f(policy, task_id=None, *a, **k):
            tasks = _tasks(policy)
            if (
                tasks is not None
                and isinstance(task_id, str)
                and task_id
                and task_id not in tasks
            ):
                return o(policy, None, *a, **k)
            return o(policy, task_id, *a, **k)

        m.resolve_task = f

    elif MUT == "S1_resolve_fills_missing_key":
        o = m.resolve_task

        @functools.wraps(o)
        def f(policy, task_id=None, *a, **k):
            try:
                return o(policy, task_id, *a, **k)
            except error:
                tasks = _tasks(policy)
                requested = (
                    _requested_id(policy, task_id) if tasks is not None else None
                )
                entry = tasks.get(requested) if tasks is not None else None
                donors = (
                    [
                        e
                        for key, e in tasks.items()
                        if key != requested and isinstance(e, dict)
                    ]
                    if tasks
                    else []
                )
                if not isinstance(entry, dict) or not donors:
                    raise
                filled = dict(entry)
                for donor in donors:
                    for key, value in donor.items():
                        filled.setdefault(key, copy.deepcopy(value))
                if filled.keys() == entry.keys():
                    raise
                try:
                    return o(_with_entry(policy, requested, filled), task_id, *a, **k)
                except error:
                    pass
                raise

        m.resolve_task = f

    elif MUT == "S1_resolve_accepts_nonpositive_slices":
        o = m.resolve_task

        @functools.wraps(o)
        def f(policy, task_id=None, *a, **k):
            tasks = _tasks(policy)
            requested = _requested_id(policy, task_id) if tasks is not None else None
            entry = tasks.get(requested) if tasks is not None else None
            slices = entry.get("expected_slices") if isinstance(entry, dict) else None
            if isinstance(slices, int) and not isinstance(slices, bool) and slices <= 0:
                result = o(
                    _with_entry(policy, requested, {**entry, "expected_slices": 1}),
                    task_id,
                    *a,
                    **k,
                )
                if isinstance(result, dict):
                    result["expected_slices"] = slices
                return result
            return o(policy, task_id, *a, **k)

        m.resolve_task = f

    elif MUT == "S1_resolve_none_takes_first_entry":
        o = m.resolve_task

        @functools.wraps(o)
        def f(policy, task_id=None, *a, **k):
            tasks = _tasks(policy)
            if task_id is None and tasks is not None:
                return o(policy, next(iter(tasks)), *a, **k)
            return o(policy, task_id, *a, **k)

        m.resolve_task = f

    elif MUT == "S1_resolve_rejects_null_worktree_root":
        o = m.resolve_task

        @functools.wraps(o)
        def f(policy, task_id=None, *a, **k):
            tasks = _tasks(policy)
            requested = _requested_id(policy, task_id) if tasks is not None else None
            entry = tasks.get(requested) if tasks is not None else None
            if (
                isinstance(entry, dict)
                and "worktree_root" in entry
                and entry["worktree_root"] is None
            ):
                raise error(
                    f"task {requested!r}'s worktree_root must be a non-empty string, got None"
                )
            return o(policy, task_id, *a, **k)

        m.resolve_task = f

    elif MUT == "S1_resolve_aliases_policy_entry":
        o = m.resolve_task

        @functools.wraps(o)
        def f(policy, task_id=None, *a, **k):
            result = o(policy, task_id, *a, **k)
            tasks = _tasks(policy)
            entry = (
                tasks.get(result.get("task_id"))
                if tasks is not None and isinstance(result, dict)
                else None
            )
            if not isinstance(entry, dict):
                return result
            entry.update(result)
            return entry

        m.resolve_task = f

    elif MUT == "S1_membership_by_path_equality":
        o = m.repo_belongs_to_task

        @functools.wraps(o)
        def f(candidate, configured, *a, **k):
            # The real call still runs first, so its refusals are unchanged;
            # only a genuine membership answer is replaced.
            o(candidate, configured, *a, **k)
            from pathlib import Path

            return (
                Path(candidate).expanduser().resolve()
                == Path(configured).expanduser().resolve()
            )

        m.repo_belongs_to_task = f

    elif MUT == "S1_membership_false_instead_of_raising":
        o = m.repo_belongs_to_task

        @functools.wraps(o)
        def f(candidate, configured, *a, **k):
            try:
                return o(candidate, configured, *a, **k)
            except error:
                return False

        m.repo_belongs_to_task = f

    elif MUT == "S1_pin_parse_returns_empty":
        o = m.parse_pinned_plan_commit

        @functools.wraps(o)
        def f(*a, **k):
            try:
                return o(*a, **k)
            except error:
                return ""

        m.parse_pinned_plan_commit = f

    elif MUT == "S3_obligations_from_bench_root_default":
        o = m.resolve_task

        @functools.wraps(o)
        def f(*a, **k):
            result = o(*a, **k)
            # Only model_report's resolution is redirected, so dev_check's
            # own grading path (a Slice 2 surface) is untouched.
            caller = sys._getframe(1).f_globals.get("__name__", "")
            if str(caller).rsplit(".", 1)[-1] == "model_report" and isinstance(
                result, dict
            ):
                result["obligations_file"] = _BENCH_ROOT_DEFAULT_OBLIGATIONS
            return result

        m.resolve_task = f


def _patch_dev_check(m):
    if MUT == "S2_dev_check_ignores_task":
        o = m.main

        @functools.wraps(o)
        def f(argv=None, *a, **k):
            return o(
                _without_flag(sys.argv[1:] if argv is None else list(argv), "--task"),
                *a,
                **k,
            )

        m.main = f

    elif MUT == "S2_provenance_omits_task_id":
        o = m.build_provenance

        @functools.wraps(o)
        def f(*a, **k):
            result = o(*a, **k)
            if isinstance(result, dict):
                result.pop("task_id", None)
            return result

        m.build_provenance = f


def _patch_grade_run(m):
    if MUT == "S2_grade_run_ignores_task":
        o = m.main

        @functools.wraps(o)
        def f(argv=None, *a, **k):
            return o(
                _without_flag(sys.argv[1:] if argv is None else list(argv), "--task"),
                *a,
                **k,
            )

        m.main = f


def _patch_model_report(m):
    if MUT == "S3_task_id_source_always_graded":
        o = m.build_report

        @functools.wraps(o)
        def f(*a, **k):
            result = o(*a, **k)
            report = _report_of(result)
            if report is not None and "task_id_source" in report:
                report["task_id_source"] = "graded"
            return result

        m.build_report = f

    elif MUT == "S3_explicit_null_task_id_backfilled":
        o = m.build_report

        @functools.wraps(o)
        def f(*a, **k):
            a, k = _rewrite_sheets(a, k, _drop_null_task_ids)
            return o(*a, **k)

        m.build_report = f

    elif MUT == "S3_middle_attempts_not_inspected":
        o = m.build_report

        @functools.wraps(o)
        def f(*a, **k):
            a, k = _rewrite_sheets(a, k, _mirror_first_attempt_onto_middles)
            return o(*a, **k)

        m.build_report = f

    elif MUT == "S3_model_report_ignores_policy":
        o = m.main

        @functools.wraps(o)
        def f(argv=None, *a, **k):
            return o(
                _without_flag(sys.argv[1:] if argv is None else list(argv), "--policy"),
                *a,
                **k,
            )

        m.main = f

    elif MUT == "S3_correctness_provenance_drops_task_id":
        o = m.resolve_correctness_provenance

        @functools.wraps(o)
        def f(*a, **k):
            result = o(*a, **k)
            if isinstance(result, dict):
                result.pop("task_id", None)
            return result

        m.resolve_correctness_provenance = f


_PATCHERS = {
    "bench_lib": _patch_bench_lib,
    "dev_check": _patch_dev_check,
    "grade_run": _patch_grade_run,
    "model_report": _patch_model_report,
}


# ------------------------------------------------------------- installation


def _patch_candidate(fullname, mod):
    if mod is None or MUT not in _REQUIRED_API or getattr(mod, "__MUTATED__", False):
        return
    leaf = str(fullname).rsplit(".", 1)[-1]
    target_leaf, required = _REQUIRED_API[MUT]
    if leaf != target_leaf or not hasattr(mod, required):
        return
    mod.__MUTATED__ = True
    try:
        _PATCHERS[leaf](mod)
    except Exception:
        mod.__MUTATED__ = False
        raise


def _patch_all(candidates):
    seen = set()
    for fullname, mod in candidates:
        if mod is None or id(mod) in seen:
            continue
        seen.add(id(mod))
        _patch_candidate(fullname, mod)


_orig_import = (
    __builtins__["__import__"]
    if isinstance(__builtins__, dict)
    else __builtins__.__import__
)
_orig_import_module = importlib.import_module
_orig_reload = importlib.reload


def _imp(name, *a, **k):
    m = _orig_import(name, *a, **k)
    candidates = [(name, sys.modules.get(name))]
    returned_name = getattr(m, "__name__", None)
    if returned_name:
        candidates.append((returned_name, m))
    fromlist = a[2] if len(a) > 2 else k.get("fromlist", ())
    for item in fromlist or ():
        if item != "*":
            fullname = f"{name}.{item}"
            candidates.append((fullname, sys.modules.get(fullname)))
    _patch_all(candidates)
    return m


def _import_module(name, package=None):
    # importlib.import_module does not route through builtins.__import__.
    m = _orig_import_module(name, package)
    candidates = [(getattr(m, "__name__", name), m)]
    if not str(name).startswith("."):
        candidates.append((name, sys.modules.get(name)))
    _patch_all(candidates)
    return m


def _reload(module):
    # Reload re-executes the module body: __MUTATED__ survives in the same
    # namespace even though the functions are back to unwrapped.
    m = _orig_reload(module)
    name = getattr(m, "__name__", "")
    if str(name).rsplit(".", 1)[-1] in _PATCHERS:
        m.__MUTATED__ = False
        _patch_all([(name, m)])
    return m


if MUT in _REQUIRED_API:
    if isinstance(__builtins__, dict):
        __builtins__["__import__"] = _imp
    else:
        __builtins__.__import__ = _imp
    importlib.import_module = _import_module
    importlib.reload = _reload
    if MUT in _DROPPED_FLAGS:
        script, flag = _DROPPED_FLAGS[MUT]
        if sys.argv and os.path.basename(str(sys.argv[0])) == script:
            sys.argv[1:] = _without_flag(sys.argv[1:], flag)
