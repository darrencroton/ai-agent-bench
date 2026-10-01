# ai-agent-bench

Measures which local model should sit in the Developer seat of a real, supervised `project-manager` (PM) Mode B run on production scientific code — by running a completely normal, unmodified PM session against a frozen plan, then grading what the Developer seat produced from PM's own artifact trail.

Contributor rules: `AGENTS.md`.

## How it works

The PM session is never instrumented, wrapped, or told anything about this bench — the operator launches it exactly as they always do, with `project-manager`'s own unmodified launcher prompt. `pm.py` already writes a rich, structured artifact trail (`run.json`, `events.jsonl`, per-slice diffs, reviewer reports); this repo's tools read that trail from outside, strictly read-only — no run token, no writes to PM state, `pm.py` is never invoked as a subprocess, and nothing is ever added to the launcher prompt. That boundary is deliberate: the premise is a normal supervised run, so anything that made measurement easier by changing PM's behavior would contaminate the thing being measured.

What gets scored is a *trajectory*, not just an end state: how many attempts a slice took, and what correctness, quality, scope discipline, and reviewer findings looked like for every attempt a git-log walk can recover (falling back to just the final attempt where it can't — see "Known scope limit" below).

## Setup

```bash
# Python 3.11 or newer (the tools use the stdlib `tomllib`)
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

python -m pytest tests/ -q
```

Every path, threshold, and tunable this repo uses lives in `policy.yaml` — nothing is hardcoded in the tools:

- **Machine-specific absolute paths** — `pm_scripts_dir` (project-manager's `scripts/` directory, so `pm_lib` is importable read-only), `lint_script`, `health_script` and `python_interpreter` are paths on the operator's machine (absolute, or `~`-relative so one file serves several machines); edit them for yours before grading anything.
- **`python_interpreter`** — point this at an interpreter with the Developer repo's own dependencies installed (numpy, scipy, h5py for `relative-velocity`); this repo's own `requirements.txt` deliberately doesn't duplicate them.
- **`default_task` + `tasks:`** — the multi-task registry: which scientific tasks this bench can run side by side, keyed by operator-chosen task id, plus `default_task`, the entry every tool applies when no `--task` flag is given anywhere downstream. Each entry carries everything task-specific: `repo` (the target repo — for `relative-velocity`, that's `substrate/relative-velocity`, a local clone vendored under this repo (gitignored) so `cohort_run.py setup` is self-contained and immune to your own `relative-velocity` checkout moving, being on the wrong branch, or having uncommitted changes; if it's ever missing, repopulate it with `git clone git@github.com:darrencroton/relative-velocity.git substrate/relative-velocity`), `branch_prefix`/`worktree_root` (where and how that task's trial worktrees/branches are named), `plan_file` (the frozen plan's path relative to the *target repo*), `provenance_file`/`hidden_tests_dir`/`obligations_file` (paths relative to *this bench's* root), `expected_slices`, and a `measurement` sub-block holding the target repo's layout globs (`production_paths`/`test_paths`/`doc_paths`). The global `measurement:` block keeps only the methodology keys applied uniformly to any task (`loc_definition`/`loc_category_definition`/`metric_version`). Adding a second task means adding its entry plus its own plan/provenance/hidden-tests files — no code change.

There's no reviewer-seat key: PM commissions whichever reviewer tool/model it judges right per slice, and that composition is recorded per-review (`run.json`'s `reviews[].tool`/`.model`) rather than pinned in policy ahead of time. There's also no one-shot pre-filter key: a candidate model is only ever run through PM because the operator already cares about it, so every candidate goes straight to a full PM run.

## Steps to run a cohort member

This bench runs whatever scientific tasks `policy.yaml`'s `tasks:` registry defines, each with its own target repo, frozen plan, and held-out test suite. Three entries are configured. `relative-velocity`'s frozen plan is `docs/MERGER_RATE_PLAN-2SLICE.md` (vendored from `relative-velocity` at a pinned commit — see `docs/MERGER_RATE_PLAN-2SLICE.provenance.md`), graded by `hidden_tests/slice{1,2}/` and `hidden_tests/mutations/`. `bench-multitask-3slice` and its two-slice fallback `bench-multitask-2slice` are the second task from `docs/SECOND-TASK-PROPOSAL.md`: the Developer implements multi-task support for this bench's own tools in a dedicated clone of this repository, against the frozen plans under `docs/plans/` (each with its own provenance file naming the pin), graded by `hidden_tests/bench-multitask/` (one hidden-test directory and one mutation bank shared by both cuts, with a separate obligations map per cut; `hidden_tests/bench-multitask/README.md` is the calibration record). The registry itself has no limit on how many entries it holds. Either way a trial's `Repo:`/`Plan file:` never need hand-typing: `tools/cohort_run.py` derives them from the resolved task (see "The tools" below; it invents no measurement of its own, only sequencing and preparation).

1. **Create a trial worktree and print the launcher prompt for it:**

   ```bash
   python tools/cohort_run.py setup
   ```

   This creates a fresh git worktree of the resolved task's configured substrate repo (the default task's is `substrate/relative-velocity`), checked out from that task's pinned plan commit, on its own branch (`<branch_prefix>/<label>` — `pm-eval-v2/trial-N` for the default task — auto-numbered from `trial` unless `--label` names it yourself), best-effort pre-builds the Developer repo's `venv/` by running its own `setup.sh` once (a failure is reported, never fatal), and prints project-manager's own launcher prompt — extracted live from `SKILL.md`, never a hardcoded copy that could drift stale. Copy that prompt into a brand-new PM-capable session (not this one) — `Repo:`/`Plan file:` are already filled in — fill in the `Developer:`/`Reviewer:` harness and model by hand, and send it. Who plays either seat is entirely your own choice made in the pasted prompt; this tool has no flag for it. Pass `--task <id>` to set up the whole trial (worktree, branch prefix, plan) against a different configured task instead of `default_task`, and `--base-commit <sha>` to branch the worktree from a commit other than the task's pinned plan commit.

   Already have a prepared repo you'd rather use instead? Pass `--repo <path>` to skip worktree creation entirely (`--plan-file <path>` overrides the derived path to the plan inside it). Since a trial's directory is brand new, whichever harness you paste the prompt into may prompt once to trust/permit it before it will work there — pass `--harness <codex|claude|copilot|opencode|qwen>` to pre-register the new directory as trusted for that harness ahead of time (claude/codex/copilot are supported directly; opencode/qwen have no known safe way to do this externally, and `setup` says so rather than pretending to). This is the only thing `--harness` does — it is never filled into the printed `Developer:`/`Reviewer:` lines.

2. **Let PM supervise the run to completion.** It handles Developer sessions, commissions whatever reviewers it judges right per slice (often a panel of several models), and makes every accept/steer/stop decision on its own. Nothing here launches PM for you, and never will.

3. **Once the run is finished** — `run.json["status"]` is `complete`, or `stopped` with PM's own closing event on record (`needs-human` is a pause, not a finish) — grade it, build its per-model report, and refold the cross-model leaderboard in one command (`setup` already printed the exact one to run, pointed at the trial worktree it created):

   ```bash
   python tools/cohort_run.py analyze --dev-repo <dev-repo>
   ```

   `<dev-repo>` resolves to PM's one run directory under that repo's git state automatically (refusing by name if more than one exists there — pass `--run-dir <pm-run-dir>` explicitly to pick one then). Omit `--task` and `analyze` infers which configured task the run belongs to from `--dev-repo`'s own worktree membership (with exactly one configured task there is nothing to infer); zero or several matching tasks is a named refusal telling you to pass `--task` explicitly, never a silent guess — as is `--run-dir` alone once more than one task is configured, since there is then no worktree to infer from. `analyze` refuses to grade a run still in progress, and is always safe to re-run. `--skip-leaderboard` grades and builds the model report without refolding the leaderboard.

   **Grading several runs at once, or lost track of which trial directories they landed in?**

   ```bash
   python tools/cohort_run.py analyze-all
   ```

   Finds every ungraded run across every configured task's `<branch_prefix>/*` trial worktrees of its own configured repo on its own (or just the one named by `--task`; no `--dev-repo`/`--run-dir` needed), keyed on each run's own authoritative `run_id` rather than a directory name, grades each one under the task whose worktrees it was found under, then refolds the leaderboard once at the end regardless of whether anything new was found (`--skip-leaderboard` omits that refold). Two configured tasks sharing one repo/branch-prefix pair would discover the same run twice — such a run is named as ambiguous and not graded, and a task whose entry or repo is broken is named and skipped; every other run is still graded and the command exits 1. One run's grading failure is likewise reported and never stops the rest of the batch. It does *not* durably remove a deleted run on its own: delete `results/runs/<run_id>/` while that run's trial worktree is still checked out, and the next `analyze-all` will simply rediscover and grade it right back. To actually drop a run from the leaderboard, delete its results *and* remove its worktree (`cleanup`, step 4).

   You can also run the same three tools yourself, in order — either path is fine; just know that `analyze` additionally threads `--task <id>` into `grade_run.py`, `--run-dir <pm-run-dir>` into `model_report.py`, and `--policy <path>` into all three whenever a non-default policy is in use, so add those flags yourself to match:

   ```bash
   python tools/grade_run.py --run-dir <pm-run-dir>
   python tools/model_report.py --run-id <run-id>
   python tools/leaderboard.py
   ```

   Or run just `python tools/leaderboard.py` on its own to refold the leaderboard from whatever's already on disk, without grading or discovering anything new.

   **Which tools take `--task`:** `cohort_run.py setup`, `cleanup`, `grade_run.py`, and `dev_check.py` all accept `--task <id>` selecting an entry of `policy.yaml`'s `tasks:` registry (omitted: that policy's `default_task`). `cohort_run.py analyze` accepts it too but can also *infer* it from `--dev-repo`'s worktree membership when omitted (above); `analyze-all` uses it to restrict discovery to one task's worktrees (omitted: every configured task). `model_report.py` takes no `--task` — it reads the run's task from its graded sheets' own provenance (a sheet with no recorded `task_id` backfills to `default_task` and the report is marked `task_id_source: "backfilled"`) — but it does take `--policy <path>`, because resolving that task requires reading the registry: pass the same non-default policy the run was graded with if there was one, else the root `policy.yaml` applies. `leaderboard.py` takes no `--task` — it partitions whatever reports are on disk by their recorded top-level `task_id` automatically — and accepts `--policy` so the task registry can be resolved from a non-default policy file. Every command above works with none of these flags given.

   Grading doesn't have to happen in this session: tell the same or a fresh PM/agent session, once the plan is finished, to read this repo's instructions and run it — the tool doesn't care who invokes it, only that the run is actually over. Nothing about grading is ever added to PM's own prompt.

4. **Check the results.** `results/leaderboard.md` is the human-readable ranking: one `## Task:` section per task present on disk, wrapping that task's Developer tables (first submission, then supervised outcome in the same row order), its code/drift reviewer tables, and a per-configuration, per-slice breakdown (obligation-group fractions, test kill rate, ΔLOC/ΔCC, the hygiene census, lint and code-health as a hygiene badge, scope exceptions, review-finding trend, quality-panel records, PM's own subjective rating verbatim) — followed by one derived `Cross-task standing` section (each configuration's percentile rank of first-attempt correctness *within* each task's own field, averaged equally across the tasks it appears in, and the same, separately, for first-attempt test kill rate; a derived, never-authoritative-on-its-own measure, defined exactly once in the document's own Glossary, which also defines the columns used throughout), then a run index. One task's numbers never enter another task's tables anywhere in the file. `results/leaderboard.json` carries the same ranking for machine use, with its tables grouped under a top-level `tasks` mapping keyed by task id plus the cross-task standing (the per-slice detail is read fresh from each run's own `model-report.json`, not duplicated into it). Optionally, and still before `cleanup`, `python tools/quality_panel.py --run-dir <pm-run-dir> --slice <N>` commissions the quality panel for one graded slice: post-hoc, at the cost of one reviewer session per slice, it records a fixed reviewer's five 1–5 scores as a labelled model's judgement that never enters any rank.

   Once you're done with a trial's worktree, `python tools/cohort_run.py cleanup --label <label>` removes it (dry run by default; `--yes` to actually remove; an ungraded trial is flagged with a warning, not refused). Its branch is left in place either way. `--force` passes through to `git worktree remove` for a dirty worktree. Separately, `python tools/cohort_run.py reset-leaderboard` archives (never deletes) `results/` into `archive/results-<UTC timestamp>` for starting a whole cohort pass over clean (dry run by default; `--yes` to actually move; `--run-id <id>` archives one run only).

## Regenerating reports that lack a `task_id`

`leaderboard.py` refuses any `model-report.json` with no top-level `task_id`, such as one built by an older checkout, until it is regenerated: re-run `model_report.py` for every such already-graded run.

```bash
python tools/model_report.py --run-id <run-id> [--run-dir <pm-run-dir>] [--policy <path>]
```

- **While the run's trial worktree still exists**, pass its original `--run-dir` (and the same non-default `--policy`, if that run was graded with one) so the timing/provenance/judgment fields stay fully populated. Ideally do this *before* running `cohort_run.py cleanup` on that worktree — once it's gone the path is stale, and an explicitly-given but missing `--run-dir` is a hard failure, never a graceful degrade.
- **For a run whose worktree is already cleaned up**, omit `--run-dir` entirely — the standard `--run-id`-only form rebuilds the report fine, with the `--run-dir`-dependent fields reported unavailable-and-named rather than guessed. Never pass a stale path.
- Each regenerated report carries `task_id` plus `task_id_source`: `"graded"` when every contributing sheet stamped it natively, `"backfilled"` when it was inferred as `default_task` for sheets with no recorded `task_id` — always visible, never silent. A run whose sheets mix the two sources is refused loudly; for a sheet whose already-graded attempt lacks a `task_id`, that refusal is *permanent* rather than curable by re-grading — `dev_check.py` deliberately preserves an already-graded attempt's captured provenance verbatim on every regrade (it never rewrites what rubric an attempt was graded under), so no in-band command can add the missing `task_id` to it.
- Re-running is safe: `model_report.py` fully rebuilds its output from scratch on every invocation, so a failed attempt costs nothing but the retry.

## The tools

| Tool | What it does |
|---|---|
| `tools/grade_run.py` | Grades one **finished** run in a single pass: resolves every attempt of every slice it can (falling back to just the final attempt per slice when it can't — see "Known scope limit" below), calls `dev_check.py` on each, then harvests every commissioned review via `review_score.py`. Takes `--task <id>` (default `default_task`) and threads it into every `dev_check.py` call it makes. This is what you run. |
| `tools/dev_check.py` | Grades one specific attempt under the resolved task (`--task <id>`, default `default_task`; resolved via `bench_lib.resolve_task`, which validates the registry's own shape and the resolved entry itself, failing loudly naming the task id and any missing or malformed key): checks its commit out into a disposable worktree, runs that slice's held-out hidden tests and scores them by acceptance obligation, independently invokes lint/code-health (never trusting PM's own prose about them), measures the **test kill rate** — the fraction of that slice's seeded mutants (the task's `mutations_dir` bank) the Developer's *own* test files kill, a mutant being killed when a test that passed unmutated stops passing, measured before the hidden tests are copied in — and recomputes scope discipline via `pm_lib`'s own `effective_authorized_files` helper. Before grading it cross-checks the run's own recorded repository against the resolved task's configured repo — a mistyped-but-valid `--task` is refused loudly, never silently graded under the wrong rubric — and stamps the resolved `task_id` into the attempt's provenance. Callable directly for a manual/ad-hoc grade. |
| `tools/review_score.py --skill drift-audit\|code-review` | Harvests each commissioned reviewer's report onto its attempt's `reviews` list — one record per commission, so two reviewers on one submission are a panel and a re-commission of the same reviewer is a retry marked `superseded_by`, never an overwrite. Records findings by severity, per-section item counts, the verdict, and how many findings survive into that same reviewer's next review. |
| `tools/quality_panel.py` | Optional and post-hoc: commissions one fixed read-only reviewer (`policy.yaml`'s `quality_panel` block) through the orchestrator skill's launcher to read a graded slice attempt's commit (default: the accepted one) against the frozen plan, in a disposable worktree, and score five dimensions 1–5 with `path:line` evidence under `docs/QUALITY-PANEL-RUBRIC.md`. Appends one record per commission to that attempt's `quality_panel` list — never overwriting, so repeat commissions show the panel's repeatability — carrying the reviewer identity, rubric hash and prompt hash. Subjective: surfaced as a labelled model's judgement, never blended into correctness, kill rate or any rank. |
| `tools/bench_lib.py` | Shared helpers (attempt numbering, event-log reading, atomic JSON writes) — not a CLI tool. |
| `tools/model_report.py` | Gathers one model's full run (every `slice-<N>.json` sheet under `results/runs/<run_id>/`) into one report: first- and final-attempt correctness, quality, size/complexity and scope, attempt count and trajectory per slice, every review commission with its full attribution, and PM's own structured judgments and subjective rating — all read back verbatim, never blended into the deterministic scores. Carries the run's `task_id` onto the report's top level, read from the sheets' own provenance (backfilled to `default_task` for sheets with no recorded `task_id` and explicitly marked `task_id_source: "backfilled"`; a run whose slices disagree after backfilling is refused loudly) and uses it to load that task's own obligations file when reconstructing node outcomes. Takes `--policy <path>` so the task registry comes from the same policy the run was graded with. Invents no composite score; fully rebuilds `results/runs/<run_id>/model-report.json` from scratch on every invocation. |
| `tools/leaderboard.py` | Folds every `model-report.json` on disk into one cross-model leaderboard: partitions reports by their top-level `task_id` before any aggregation (a missing or invalid `task_id` is a named refusal, never a silent default), then, within each task partition, groups runs by their resolved Developer configuration (model · harness · effort), ranks on **mean first-attempt correctness** — there is no composite score — adds an independent second ranking, `Rank by test kill rate`, by mean first-attempt test kill rate (never combined with correctness, which stays the primary rank), and shows final test kill rate, ΔLOC, ΔCC, final correctness, gain, attempts, steers and PM elapsed beside it as supporting columns, never blended in. Per task, two further tables rate the code and drift reviewers from PM's own judgments, built from that task's own rounds only (a reviewer identity active under two tasks gets independent scores per task, never pooled), and PM's subjective rating is carried through per run, verbatim. After every task's own sections comes one derived `Cross-task standing` section — each configuration's within-task percentile rank of first-attempt correctness (and, separately, of first-attempt test kill rate, and of reviewer comparative-rank means) averaged equally across the contributing tasks; computed strictly after every task's tables are final, reading only from them, feeding back into none of them, and defined exactly once in the document's own Glossary. Writes `results/leaderboard.json` and `results/leaderboard.md` (per-task ranking sections plus each configuration's per-slice detail and a stably anchored run index, read fresh from `model-report.json` rather than duplicated into the JSON). Refuses outright — never writing an empty leaderboard — when zero `model-report.json` files exist, leaving the previous `leaderboard.json`/`.md` on disk untouched. |
| `tools/cohort_run.py` | Operator convenience wrapper, not a scoring tool — see "Steps to run a cohort member" above for the full flow. Subcommands: `setup` (create a trial worktree, pre-build its `venv/`, print PM's launcher prompt), `analyze` (grade one finished run and refold the leaderboard), `analyze-all` (same, batched across every ungraded run this bench can find), `cleanup` (remove a trial worktree), `reset-leaderboard` (archive old `results/`). Task selection (`--task`, with `analyze`'s worktree-membership inference) is documented in step 3; `reset-leaderboard` has no task dimension. Never launches PM, never writes into a Developer/PM directory. |

`dev_check.py` and `review_score.py` are both pure, one-shot, idempotent commands — the same inputs always produce the same measurement, and re-running one for an already-graded attempt refreshes only its own fields, never disturbing anything the other tool wrote. Both write into one cumulative scoring sheet per run and slice, `results/runs/<run_id>/slice-<N>.json`.

**Known scope limit:** every attempt of a slice gets a deterministic grade when a git-log walk recovers exactly one commit per attempt between the slice's own before_head and its final commit; a slice whose history doesn't satisfy that (most commonly a multi-epoch first slice with no review recorded from its earliest epoch) falls back to grading only its *final* attempt, reported as a named problem, not silently. A review commissioned against an attempt with no sheet row is likewise reported as a named, loud problem when harvested — never silently dropped. The attempt count and PM's per-attempt decision (steer/accept/stop) are unaffected either way, since both come from `events.jsonl` directly for every attempt.

## Repo layout

```text
docs/
  MERGER_RATE_PLAN-2SLICE.md       the frozen two-slice plan PM runs against,
                                   vendored from relative-velocity at a pinned
                                   commit so a later edit there cannot silently
                                   change what is being scored mid-cohort
  MERGER_RATE_PLAN-2SLICE.provenance.md   that pin
  OBLIGATION-GROUPS.md             how each task's hidden tests are
                                   partitioned, and why
  QUALITY-PANEL-RUBRIC.md          the fixed rubric tools/quality_panel.py
                                   sends its reviewer; its sha256 rides on
                                   every rating
  reference-impl/README.md         evidence relative-velocity's hidden tests
                                   and mutation bank are correct and
                                   discriminating, plus how to reproduce it
  reference-impl/reference_solution/   the reference implementation that
                                   evidence is produced against, plus its
                                   own test suite and a weak-baseline control
                                   for validating the mutation bank
  SECOND-TASK-PROPOSAL.md          the assessed proposal for the next task
                                   and the mutation-gate measurement
  plans/MULTI-TASK-PLAN-3SLICE.md  the frozen three-slice plan for
                                   bench-multitask-3slice, pinned in a
                                   dedicated clone of this repository
  plans/MULTI-TASK-PLAN-2SLICE.md  its two-slice fallback (bench-multitask-2slice)
  plans/*.provenance.md            those pins
hidden_tests/
  slice1/, slice2/                 relative-velocity's held-out tests, one
                                   directory per slice
  obligations.yaml                 its acceptance-obligation partition
  mutations/                       its mutation bank: sitecustomize.py plus
                                   one slice<N>.txt per slice, for the test
                                   kill rate
  bench-multitask/                 the second task's held-out tests
                                   (slice1/..slice3/), the two cuts'
                                   obligations maps, its mutation bank, and
                                   README.md, the calibration record for both
policy.yaml                        all thresholds, task registry and tool paths
requirements.txt                   this repo's own dependencies (pyyaml, pytest)
tools/                             see "The tools" above
tests/                             this repo's own test suite
archive/                           superseded files and archived results
                                   (gitignored)
substrate/relative-velocity/       vendored local clone of the substrate repo
                                   (gitignored); trial worktrees from
                                   `cohort_run.py setup` are its siblings
substrate/ai-agent-bench-task/     vendored clone of this repository at the
                                   bench-multitask pin (gitignored); its
                                   trial worktrees are its siblings too
results/runs/<run_id>/
  slice-<N>.json                   the cumulative scoring sheet (gitignored, generated)
  model-report.json                one model's full run, reshaped (gitignored, generated)
results/leaderboard.json          the cross-model ranking, machine-readable (gitignored, generated)
results/leaderboard.md            the same ranking plus per-slice detail, for a human (gitignored, generated)
```

## Multi-machine use (an iCloud-synced `results/`)

The generated `results/` tree can be shared between machines over iCloud sync; three assumptions keep that safe:

- **Rebuilds are idempotent.** Every generated file (`model-report.json`, `leaderboard.json`/`.md`) is rebuilt from scratch on each invocation from inputs that outlive it, and each individual file write is atomic, so no torn or corrupted file can ever result; a failure before any write (e.g. during rendering) leaves the prior outputs untouched. The one caveat: `leaderboard.json` and `leaderboard.md` are two *separate* atomic writes, so an interruption landing between them can momentarily leave the pair at different generations. Simply re-running is the recovery path either way — the next successful run rewrites both consistently.
- **Don't run `leaderboard.py` / `cohort_run.py analyze(-all)` literally simultaneously from both machines** — concurrent builds write the same shared files last-write-wins. Sequential builds from either machine are fine.
- **A mid-sync read fails loudly, not silently.** A `model-report.json` caught mid-iCloud-sync parses as invalid JSON and the build refuses with a named error naming the file (a wrapped `JSONDecodeError`) — nothing downstream is written and nothing is corrupted. If a build fails immediately after a sync completes, retry once before treating it as a real bug.

## Before you touch the hidden tests

**The obligation partition is the rubric weight.** A slice's correctness score is the equally weighted mean of its obligation groups. There is no other weighting, so how the tests are grouped *is* how they are weighted — a group holding one decisive assertion counts exactly as much as one holding twenty type checks. Balance by importance, never by test count, and read `docs/OBLIGATION-GROUPS.md` (one section per task) before regrouping anything.

**Never run two slices' hidden tests in one pytest invocation.** Every slice directory of a task contains a `test_hA.py`, so a combined run fails module collection. This never arises operationally — a slice is not graded until the one before it is accepted — and `dev_check.py` grades one slice per invocation by construction.

**A mutation bank is validated the same way, and a changed bank is a new measurement version.** Every mutant must be killed by the task's reference suite under the slice that lists it, few by a deliberately weak suite, none by the frozen pre-plan suite (`docs/reference-impl/README.md` and `hidden_tests/bench-multitask/README.md` record the numbers); `dev_check.py` stamps the bank's per-slice hash on every kill-rate measurement, and `leaderboard.py` refuses to mix two bank versions in one table.
