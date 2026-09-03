#!/usr/bin/env python3
"""Grade one trial produced by run_trial.py.

Everything here is automated and mechanical except the two `judged`
categories in rubric.yaml, which call a fixed judge model if one is
configured. No step in this file re-prompts the Developer model or gives it
a chance to fix anything -- grading happens once, after the fact, exactly
like a real benchmark run.

Usage:
    python eval/harness/grade_trial.py --manifest <path-to-manifest.json>
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harnesses import build_command  # noqa: E402


def repo_root():
    out = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                          capture_output=True, text=True, check=True)
    return out.stdout.strip()


def _decode(x):
    """CPython quirk: subprocess.run's TimeoutExpired.stdout/.stderr carry
    raw bytes from the partial read even when text=True was passed -- the
    text decoding only applies on the successful, non-timeout completion
    path. Every caller of run() below treats out/err as str."""
    if isinstance(x, bytes):
        return x.decode(errors="replace")
    return x or ""


def run(cmd, cwd=None, env=None, timeout=None):
    try:
        p = subprocess.run(cmd, cwd=cwd, env=env, timeout=timeout,
                            capture_output=True, text=True)
        return p.returncode, p.stdout, p.stderr, False
    except subprocess.TimeoutExpired as e:
        return None, _decode(e.stdout), _decode(e.stderr), True


PYTEST_LINE = re.compile(r"^(\S+::\S+)\s+(PASSED|FAILED|ERROR|SKIPPED)\b")
COLLECT_ONLY_LINE = re.compile(r"^(\S+::\S+)$")


def parse_pytest_verbose(stdout):
    results = {}
    for line in stdout.splitlines():
        m = PYTEST_LINE.match(line.strip())
        if m:
            results[m.group(1)] = m.group(2)
    return results


def _collect_node_ids(py, installed, worktree, timeout=120):
    """Enumerate hidden-test node IDs independently of running them, so a
    node that never gets a verdict line (the run hangs, or the process dies
    partway through) can be told apart from a node that was never supposed
    to exist. `--collect-only -q` prints one bare "path::test" per line and
    doesn't execute any test body, so it isn't subject to the same
    hang/crash risk as the real run -- guarded against anyway with its own
    shorter timeout."""
    rc, out, err, timed_out = run(
        [py, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider",
         "--continue-on-collection-errors"] + installed,
        cwd=worktree, timeout=timeout)
    ids = {line.strip() for line in out.splitlines()
           if COLLECT_ONLY_LINE.match(line.strip())}
    return ids, timed_out


def score_hidden_tests(root, worktree, task_dir, meta):
    """Copy hidden tests into the worktree, score pass rate, then remove
    them again. Returns (fraction, detail_dict).

    The removal matters: every check that runs after this one (own-suite
    baseline, the outside-root suite-health check, the mutation gate) runs
    `pytest tests/` against whatever is sitting in the worktree's tests/
    directory. Leaving the hidden tests there would make those checks score
    the hidden tests' ability to catch a mutation instead of the model's
    own tests' -- silently inflating test_adequacy on every trial, since
    the hidden tests are comprehensive by construction. Caught in this
    repo's own harness-validation smoke test: the mutation kill rate read
    19/19 with the hidden tests still present and 17/19 once this cleanup
    was added, against the same reference submission.
    """
    hidden_paths = [os.path.join(task_dir, p) for p in meta["hidden_tests"]]
    installed = []
    for hp in hidden_paths:
        dest = os.path.join(worktree, "tests", os.path.basename(hp))
        shutil.copy(hp, dest)
        installed.append(dest)

    try:
        py = sys.executable
        # A fixed, submission-independent expected node count: without
        # this, a submission whose own code hangs or crashes pytest
        # partway through the hidden suite would have the tests it never
        # reached silently excluded from the denominator (results only
        # ever contains nodes that produced a verdict line) rather than
        # scored as failed -- so dying early could outscore running to
        # completion and failing honestly.
        expected_ids, collect_timed_out = _collect_node_ids(py, installed, worktree)
        # Without this flag, a collection error in ANY one hidden-test file
        # (e.g. a broken import in test_hB.py) aborts the whole pytest
        # session by default, silently zeroing out an unrelated file's
        # already-correct results (e.g. test_hA.py) too.
        rc, out, err, timed_out = run(
            [py, "-m", "pytest", "-v", "--tb=short", "-p", "no:cacheprovider",
             "--continue-on-collection-errors"] + installed,
            cwd=worktree, timeout=600)
    finally:
        for dest in installed:
            if os.path.exists(dest):
                os.remove(dest)

    results = parse_pytest_verbose(out)
    # Fall back to what actually produced a verdict only if collection
    # itself didn't yield a usable expected set (e.g. it also timed out) --
    # the previous, weaker behavior, not a new failure mode.
    missing = sorted(expected_ids - set(results)) if expected_ids else []
    for node_id in missing:
        results[node_id] = "MISSING"
    passed = sum(1 for v in results.values() if v == "PASSED")
    total = len(expected_ids) if expected_ids else len(results)
    fraction = (passed / total) if total else 0.0
    return fraction, {
        "total": total, "passed": passed,
        "failed": [k for k, v in results.items() if v != "PASSED"],
        "missing": missing, "collect_timed_out": collect_timed_out,
        "timed_out": timed_out, "raw_tail": out[-4000:], "stderr_tail": err[-2000:],
    }


def own_suite_baseline(root, worktree, meta):
    py = sys.executable
    cmd_parts = meta.get("own_suite_command", "python -m pytest tests/ -q").split()
    cmd_parts[0] = py  # use the grading env's interpreter, not a bare "python"
    rc, out, err, timed_out = run(cmd_parts, cwd=worktree, timeout=900)
    return {"returncode": rc, "timed_out": timed_out, "passed_clean": rc == 0,
            "tail": out[-3000:]}


def ships_red_outside_root(worktree, meta):
    """report 04's §7.4 gate #1: run the own suite once from outside the repo
    root. Catches CWD-relative subprocess/path assumptions in the model's
    own tests that a run from the repository root would never expose."""
    py = sys.executable
    outside = tempfile.mkdtemp(prefix="ai-agent-bench-outside-")
    tests_dir = os.path.join(worktree, "tests")
    rc, out, err, timed_out = run([py, "-m", "pytest", "-q", tests_dir],
                                   cwd=outside, timeout=900)
    shutil.rmtree(outside, ignore_errors=True)
    return {"ships_red_outside_root": rc not in (0, None), "returncode": rc,
            "timed_out": timed_out, "tail": out[-2000:]}


def load_mutations(task_dir, meta):
    mut_list_path = os.path.join(task_dir, meta["mutations_file"])
    with open(mut_list_path) as f:
        return [l.strip() for l in f if l.strip()]


def mutation_gate(root, worktree, task_dir, meta):
    mut_dir = os.path.join(task_dir, "mutations")
    mutations = load_mutations(task_dir, meta)

    py = sys.executable
    pytest_args = [py, "-m", "pytest", "tests/", "-q", "--tb=no", "-p", "no:cacheprovider"]

    results = {}
    for mut in mutations:
        env = dict(os.environ)
        env["PYTHONPATH"] = mut_dir + os.pathsep + env.get("PYTHONPATH", "")
        env["MUTATION"] = mut
        rc, out, err, timed_out = run(pytest_args, cwd=worktree, env=env, timeout=180)
        if timed_out:
            results[mut] = "timeout"
        elif rc is None:
            results[mut] = "error"
        elif rc != 0:
            results[mut] = "kill"
        else:
            results[mut] = "survive"

    killed = sum(1 for v in results.values() if v == "kill")
    # Divide by every configured mutation, not just the resolved kill/survive
    # ones -- a timeout/error must count as a non-kill, not shrink the
    # denominator (mirrors this file's own correctness-denominator fix).
    fraction = (killed / len(mutations)) if mutations else 0.0
    return fraction, {"per_mutation": results, "killed": killed, "total": len(mutations)}


# Dropped into every worktree by run_trial.py so the model can read its
# task; never part of the model's own submission. Left in, it reads as a
# scope violation and crowds out the real diff from the judge's truncated
# prompt budget.
HARNESS_ARTIFACTS_PATHSPEC = ["--", ".", ":(exclude)TASK.md"]


def scope_discipline(worktree, before_head, meta):
    # --no-renames: git's default rename detection would otherwise report only
    # the destination path for an exact rename, hiding that a frozen source
    # file was deleted (e.g. renaming a frozen test onto an authorized name).
    # Forcing the delete+add pair keeps both endpoints visible to the checks
    # below.
    rc, out, err, _ = run(["git", "diff", "--name-only", "--no-renames", before_head]
                           + HARNESS_ARTIFACTS_PATHSPEC, cwd=worktree)
    changed = [l for l in out.splitlines() if l.strip()]
    authorized = set(meta.get("authorized_surface", []))
    frozen = set(meta.get("frozen_unchanged", []))
    out_of_scope = [f for f in changed if f not in authorized]
    frozen_touched = [f for f in changed if f in frozen]
    # A frozen file is almost never also in authorized_surface, so touching one
    # lands it in both lists above; count each offending path once rather than
    # charging it twice against the changed-file denominator. out_of_scope and
    # frozen_touched stay separate in the detail dict for the report.
    violations = len(set(out_of_scope) | set(frozen_touched))
    fraction = 1.0 - violations / len(changed) if changed else 0.0
    return fraction, {"changed_files": changed, "out_of_scope": out_of_scope,
                       "frozen_touched": frozen_touched}


def lint_diff(worktree, before_head):
    rc, out, err, _ = run(["git", "diff", "--name-only", before_head], cwd=worktree)
    py_files = [l for l in out.splitlines() if l.strip().endswith(".py")]
    if not py_files or shutil.which("ruff") is None:
        return None, {"note": "no changed .py files or ruff not installed"}
    # --quiet: ruff's concise format still writes non-finding summary lines to
    # stdout ("All checks passed!" clean, "Found N errors." / fixability notes
    # otherwise); --quiet suppresses exactly those, leaving only real
    # `path:line:col: CODE message` lines to count, with no path assumptions.
    rc, out, err, _ = run(["ruff", "check", "--quiet", "--output-format=concise"] + py_files,
                           cwd=worktree)
    findings = [l for l in out.splitlines() if l.strip()]
    # Simple decaying penalty: 0 findings -> 1.0, asymptotically -> 0 as findings grow.
    fraction = 1.0 / (1.0 + 0.1 * len(findings))
    return fraction, {"findings_count": len(findings), "findings": findings[:50]}


def _extract_json_object(text):
    """Find and parse the first {...} object in free-form model output."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return {}
    try:
        return json.loads(text[start:end + 1])
    except Exception:
        return {}


MAX_JUDGE_ATTEMPTS = 3


def run_judge(root, worktree, before_head, rubric, categories):
    """Returns (scores, detail, status).

    status: "no_judge_configured" (rubric.yaml has no judge.model -- a
    static, report-wide condition, safe to renormalize over) vs "ok" (every
    category parsed) vs "failed" (judge ran but never parsed after retrying
    -- looks identical to "no_judge_configured" in the scores dict alone, but
    must NOT be renormalized: a trial silently missing rubric weight isn't
    comparable to a fully-scored one, and needs investigation, not a
    quietly smaller total). Partial success across attempts (e.g. one
    category parses on attempt 1, another only on attempt 2) still counts as
    "failed" if no single attempt scored every category -- a category's
    score should come from one coherent judgement, not be stitched together.
    """
    judge_cfg = rubric.get("judge", {})
    model = judge_cfg.get("model")
    if not model:
        return ({c: None for c in categories},
                {"note": "no judge model configured in rubric.yaml"}, "no_judge_configured")
    harness = judge_cfg.get("harness", "opencode")
    effort = judge_cfg.get("effort")

    rc, diff, err, _ = run(["git", "diff", before_head] + HARNESS_ARTIFACTS_PATHSPEC, cwd=worktree)
    prompt_path = os.path.join(root, "eval", "harness", judge_cfg.get("prompt_template", "judge_prompt.md"))
    template = ""
    if os.path.exists(prompt_path):
        with open(prompt_path) as f:
            template = f.read()
    prompt = template.replace("{{DIFF}}", diff[:40000]) if template else (
        "Score this diff on readability and maintainability, 1-5 each, "
        "as JSON {\"readability\": N, \"maintainability\": N, \"notes\": \"...\"}."
        "\n\nDIFF:\n" + diff[:40000]
    )

    attempts = []
    for attempt in range(1, MAX_JUDGE_ATTEMPTS + 1):
        cmd, extra_env, cwd = build_command(harness, prompt, model, effort, worktree)
        env = {**os.environ, **extra_env} if extra_env else None
        rc, out, err, timed_out = run(cmd, cwd=cwd, env=env, timeout=600)
        if harness == "opencode":
            # opencode --format json emits a stream of JSON events; take the
            # last text payload and parse a JSON object out of it.
            try:
                text = out.strip().splitlines()[-1] if out.strip() else "{}"
                obj = json.loads(text)
                parsed = _extract_json_object(obj.get("text", "") if isinstance(obj, dict) else "")
            except Exception:
                parsed = {}
        else:
            # Every other supported harness prints its final response as
            # plain text on stdout -- pull the JSON object out of that
            # directly.
            parsed = _extract_json_object(out)

        scores = {c: (float(parsed[c]) / 5.0 if isinstance(parsed.get(c), (int, float)) else None)
                  for c in categories}
        # rc/stderr distinguish a parse hiccup (stdout has content) from a
        # hard invocation failure (bad model id, auth, rate limit).
        attempts.append({"attempt": attempt, "returncode": rc, "raw": out[-2000:],
                          "stderr_tail": err[-2000:], "parsed": parsed, "timed_out": timed_out})
        if all(scores[c] is not None for c in categories):
            return scores, {"attempts": attempts}, "ok"

    return {c: None for c in categories}, {"attempts": attempts}, "failed"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--manifest", required=True)
    args = ap.parse_args()

    root = repo_root()
    with open(args.manifest) as f:
        manifest = json.load(f)
    task_dir = os.path.join(root, "eval", "tasks", manifest["task_id"])
    with open(os.path.join(task_dir, "meta.yaml")) as f:
        meta = yaml.safe_load(f)
    with open(os.path.join(root, "eval", "rubric.yaml")) as f:
        rubric = yaml.safe_load(f)

    worktree = manifest["worktree_path"]
    before_head = manifest["before_head"]

    # Defensive: run_trial.py already stages everything so untracked new
    # files (e.g. merger_rate.py itself) are visible to `git diff`, but this
    # script must be safe to run standalone against a hand-built manifest too.
    run(["git", "add", "-A"], cwd=worktree)

    record = {"run_id": manifest["run_id"], "task_id": manifest["task_id"],
              "model": manifest["model"], "harness": manifest["harness"],
              "effort": manifest.get("effort"), "baseline_ref": manifest.get("baseline_ref"),
              "duration_seconds": manifest["duration_seconds"],
              "timed_out": manifest["timed_out"], "committed": manifest["committed"],
              "changed_files": manifest["changed_files"]}

    no_submission = manifest["timed_out"] or not manifest["changed_files"]
    category_scores = {}
    category_detail = {}

    if no_submission:
        record["no_submission"] = True
        for cat in rubric["categories"]:
            category_scores[cat["id"]] = 0.0
        category_detail["reason"] = "no diff produced (timeout, crash, or empty run)"
    else:
        print("[grade_trial] scoring correctness (hidden tests)...")
        frac, detail = score_hidden_tests(root, worktree, task_dir, meta)
        category_scores["correctness"] = frac
        category_detail["correctness"] = detail

        print("[grade_trial] running own-suite baseline...")
        baseline = own_suite_baseline(root, worktree, meta)
        category_detail["own_suite_baseline"] = baseline

        print("[grade_trial] checking suite health from outside repo root...")
        outside = ships_red_outside_root(worktree, meta)
        category_detail["ships_red_outside_root"] = outside

        mutation_count = len(load_mutations(task_dir, meta))
        print(f"[grade_trial] running {mutation_count}-mutation test-adequacy gate "
              f"(this takes a while)...")
        if baseline["passed_clean"]:
            frac, detail = mutation_gate(root, worktree, task_dir, meta)
        else:
            frac, detail = 0.0, {"note": "own suite did not pass cleanly; mutation credit withheld"}
        category_scores["test_adequacy"] = frac
        category_detail["test_adequacy"] = detail

        print("[grade_trial] checking scope discipline...")
        frac, detail = scope_discipline(worktree, before_head, meta)
        category_scores["scope_discipline"] = frac
        category_detail["scope_discipline"] = detail

        print("[grade_trial] running differential lint...")
        frac, detail = lint_diff(worktree, before_head)
        # Only charge hygiene for ships_red_outside_root when the baseline was
        # otherwise clean -- a baseline already red at the root makes the
        # outside-root run red too and confirms nothing new, so charging
        # hygiene as well as test_adequacy would double-penalize one defect.
        if baseline["passed_clean"] and outside["ships_red_outside_root"]:
            frac = 0.0
            detail = dict(detail or {}, ships_red_outside_root=True)
        category_scores["hygiene"] = frac
        category_detail["hygiene"] = detail

        judged_ids = [c["id"] for c in rubric["categories"] if c["kind"] == "judged"]
        print(f"[grade_trial] judged categories {judged_ids}: "
              f"{'calling judge model' if rubric.get('judge', {}).get('model') else 'skipped (no judge configured)'}...")
        jscores, jdetail, judge_status = run_judge(root, worktree, before_head, rubric, judged_ids)
        if judge_status == "failed":
            unparsed = [c for c in judged_ids if jscores.get(c) is None]
            diag_dir = os.path.join(root, "eval", "results", "tmp", "judge_failures")
            os.makedirs(diag_dir, exist_ok=True)
            diag_path = os.path.join(diag_dir, f"{manifest['run_id']}.json")
            with open(diag_path, "w") as f:
                # Save the automated categories too -- already computed
                # above, otherwise lost on failure and only recoverable via
                # a full re-grade (the mutation gate is the slow step).
                json.dump({"run_id": manifest["run_id"], "unparsed_categories": unparsed,
                           "automated_category_scores": category_scores,
                           "automated_category_detail": category_detail,
                           "detail": jdetail}, f, indent=2, default=str)
            print(f"[grade_trial] ERROR: judge ran {MAX_JUDGE_ATTEMPTS} times but never "
                  f"returned a parseable score for {unparsed}. No run record was written -- "
                  f"this trial is NOT graded and must not be compared to others until "
                  f"investigated. Diagnostic: {diag_path}", file=sys.stderr)
            return 1
        for c in judged_ids:
            category_scores[c] = jscores.get(c)
        category_detail["judge"] = jdetail

    # ---- combine into total, renormalizing over categories that were scored ----
    weight_sum = 0.0
    weighted = 0.0
    for cat in rubric["categories"]:
        cid, w = cat["id"], cat["weight"]
        s = category_scores.get(cid)
        if s is None:
            continue
        weight_sum += w
        weighted += w * s
    total = round(100.0 * weighted / weight_sum, 1) if weight_sum else None

    record["category_scores"] = category_scores
    record["category_detail"] = category_detail
    record["total_score"] = total
    record["scored_weight_fraction"] = round(weight_sum / sum(c["weight"] for c in rubric["categories"]), 2)

    results_dir = os.path.join(root, "eval", "results", "runs")
    os.makedirs(results_dir, exist_ok=True)
    out_path = os.path.join(results_dir, f"{manifest['run_id']}.json")
    with open(out_path, "w") as f:
        json.dump(record, f, indent=2, default=str)

    report_dir = os.path.join(root, "eval", "results", "reports")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f"{manifest['run_id']}.md")
    write_report(report_path, manifest, record, rubric)

    print(f"[grade_trial] total_score={total} (scored {record['scored_weight_fraction']*100:.0f}% of rubric weight)")
    print(f"[grade_trial] record: {out_path}")
    print(f"[grade_trial] report: {report_path}")


def write_report(path, manifest, record, rubric):
    lines = [
        f"# Trial report: {record['run_id']}",
        "",
        f"- Task: `{record['task_id']}`",
        f"- Model: `{record['model']}` (harness: {record['harness']})",
        f"- Duration: {record['duration_seconds']}s | timed out: {record['timed_out']} | committed: {record['committed']}",
        f"- Changed files: {', '.join(record['changed_files']) or '(none)'}",
        "",
        f"## Total score: {record['total_score']} / 100",
        f"(scored {record['scored_weight_fraction']*100:.0f}% of rubric weight -- unscored categories, "
        "typically the judged ones with no judge model configured, are excluded rather than defaulted)",
        "",
        "## Category scores",
        "",
        "| Category | Kind | Weight | Score |",
        "|---|---|---|---|",
    ]
    for cat in rubric["categories"]:
        s = record["category_scores"].get(cat["id"])
        s_str = f"{s*100:.0f}%" if isinstance(s, (int, float)) else "not scored"
        lines.append(f"| {cat['id']} | {cat['kind']} | {cat['weight']} | {s_str} |")

    lines += ["", "## Detail", "", "```json",
              json.dumps(record["category_detail"], indent=2, default=str)[:20000],
              "```"]
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    sys.exit(main())
