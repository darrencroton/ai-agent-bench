# ai-agent-bench

A benchmark for testing what a single model+harness combination can do on a
real scientific-coding task, unsupervised, in one shot -- no PM, no reviewer,
no correction round. It exists because a project-manager-style review/fix
loop is very good at producing uniform, correct output regardless of which
model is underneath it, which makes it useless for telling models apart. If
you want to know which model is actually good, you have to take the loop
away and look at what comes back the first time.

The task domain is a real astrophysics pipeline (close-pair galaxy
statistics, forked from the `relative-velocity` project) rather than a toy
problem, because that's the kind of work this is meant to predict
performance on.

## How it works

1. `run_trial.py` creates an isolated git worktree, provisions its own
   `./venv` from `requirements.txt`, drops a task's spec into it, and invokes
   a harness+model combination with a fixed prompt and a fixed time budget.
   The model gets one attempt. Nobody looks at its work and hands it back.
2. `grade_trial.py` scores the result afterward, mechanically: hidden tests
   the model never saw, a mutation-testing gate that checks whether the
   model's *own* tests can actually fail, a scope-discipline check against
   the task's authorized file list, and a lint pass. Two categories
   (readability, maintainability) are judged by a fixed model if you've
   configured one; otherwise they're left unscored rather than guessed at.
3. `aggregate.py` rolls every graded trial into `eval/leaderboard.md` -- one
   row per (task, harness, model, effort), linking to each trial's full
   report. A same model run through a different harness or effort is a
   different experiment, not more trials of one -- it gets its own row.

Nothing here reruns a failed step, argues with the model, or gives it a
second chance. That's the whole point.

## Repo layout

```text
src/            frozen baseline pipeline (galaxy pair-finding; unmodified,
                imported by every task's tests)
tests/          the baseline pipeline's own test suite
docs/
  BACKGROUND.md   scientific motivation for the pipeline
  DESIGN.md       why this repo is shaped the way it is
eval/
  rubric.yaml         the fixed scoring rubric -- versioned, never
                      re-weighted per report
  tasks/<id>/
    spec.md           the task, given to the model as TASK.md
    meta.yaml         authorized surface, hidden test list, mutation list
    hidden_tests/     pytest files copied in at grading time, never shown
                      to the model beforehand
    mutations/        the mutation-testing gate for this task
    reference_solution/  a correct implementation, used only to validate
                      the harness itself -- never touched at trial time
  harness/
    run_trial.py      runs one (task, model) trial
    grade_trial.py    grades one trial
    aggregate.py      rebuilds the leaderboard from eval/results/runs/
    harnesses.py      command-builders for each supported CLI
  results/
    runs/*.json       one structured record per graded trial
    reports/*.md      one human-readable report per graded trial
  leaderboard.md      generated -- don't hand-edit it
archive/          trial records superseded by a harness/grader change,
                  moved here instead of deleted; gitignored, not tracked --
                  see docs/DESIGN.md's History for why a given batch moved
```

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

This root environment runs the benchmark and grader. `run_trial.py` creates a
separate environment inside every trial worktree for the model under test.

You'll also need whichever harness CLI you plan to use, already
authenticated: `opencode` (the default), or `claude`, `codex`, `copilot`,
`qwen`. For local models via `opencode`, point its config at your
llama-server endpoint(s) the normal way (`~/.config/opencode/opencode.json`)
-- this repo doesn't manage that config, it just shells out to whatever
`opencode` resolves.

`ruff` is used for the lint category if it's on `PATH`; if it isn't, that
category is reported as unscored rather than as a pass.

## Running a trial

```bash
python eval/harness/run_trial.py \
    --task 001-merger-rate-feature \
    --model macstudio/qwen/qwen3.8-27b-bf16
```

opencode is the default harness because that's how local models actually
get run day to day, but it isn't opencode-specific -- point any supported
harness+model combination at a task and it tests:

```bash
python eval/harness/run_trial.py --task 001-merger-rate-feature \
    --harness claude --model claude-sonnet-5 --effort low

python eval/harness/run_trial.py --task 001-merger-rate-feature \
    --harness codex --model gpt-5-codex
```

Options:

| Flag | Default | What it does |
|---|---|---|
| `--task` | *(required)* | task directory name under `eval/tasks/` |
| `--model` | *(required)* | model id, in whatever form the chosen harness expects |
| `--harness` | `opencode` | one of `opencode`, `claude`, `codex`, `copilot`, `qwen` |
| `--effort` | none | reasoning effort/variant, passed through in the harness's own flag form (qwen's tested CLI has none -- passing `--effort` there fails closed rather than silently doing nothing) |
| `--baseline-ref` | `frozen-substrate` | git ref the trial's worktree is created from. **Must not be a ref that contains `eval/`, `.orchestrator/`, or `HANDOFF.md`** (e.g. `HEAD` or `main` on this repo) -- `run_trial.py` refuses and cleans up rather than leaking hidden tests/mutations/reference solutions to the model under test. The `frozen-substrate` tag pins the commit before any eval content existed. |
| `--timeout` | task's `developer_timeout_seconds` | wall-clock budget in seconds before the run is killed and scored as a non-submission |
| `--label` | none | free text folded into the run id, for your own bookkeeping |

This prints a manifest path when it's done:

```text
[run_trial] manifest: eval/results/tmp/manifests/<run_id>.json
```

Each trial's fresh `./venv` is installed before the model starts; its setup
time is recorded separately as `venv_setup_seconds`, not counted in the
model's `duration_seconds`. If provisioning fails, the runner removes the
incomplete worktree and exits before invoking the model.

## Grading a trial

```bash
python eval/harness/grade_trial.py --manifest eval/results/tmp/manifests/<run_id>.json
```

Writes `eval/results/runs/<run_id>.json` (the structured record) and
`eval/results/reports/<run_id>.md` (the human-readable version). A trial
that timed out or produced no diff at all scores 0 in every category rather
than being silently dropped -- an unsupervised model that can't finish is a
real result, not a data-collection failure.

The mutation gate is the slow step (currently 33-59 mutations depending on
the task × the model's own suite, each with its own subprocess and
timeout); budget a few minutes for it on top of whatever the pytest suites
themselves take.

## Building the leaderboard

```bash
python eval/harness/aggregate.py
```

Rescans every file in `eval/results/runs/` and rewrites `eval/leaderboard.md`
from scratch. Run it after every graded trial, or in a batch after several.
Never hand-edit `leaderboard.md` -- it won't survive the next run.

## The rubric

`eval/rubric.yaml` is fixed and versioned: the same categories and weights
apply to every trial of every task, forever, so scores stay comparable
across time without a "the rubric changed between reports" caveat. Four
categories are fully automated (correctness, test adequacy via mutation
kill rate, scope discipline, hygiene); two (readability, maintainability)
are judged and need a model set in `rubric.yaml`'s `judge.model` field
before they'll score -- currently pinned to `claude-sonnet-5` via the
`claude` harness. Until a judge model is configured, judged categories are
reported as unscored and the total is renormalized over what was actually
measured, not padded with a guess. (Caveat: judging a `claude`-harness trial
with a `claude-sonnet-5` judge carries a same-family bias risk the judge is
otherwise designed to avoid -- noted in `rubric.yaml` itself.)

## Adding a task

Copy the shape of `eval/tasks/001-merger-rate-feature/`: a `spec.md` the
model reads, a `meta.yaml` declaring the authorized surface and pointing at
the hidden tests and (optionally) a mutation set, and `hidden_tests/` files
that get copied into the trial's `tests/` directory at grading time -- never
before. A `reference_solution/` isn't required, but it's the only way to
know your hidden tests and mutations are actually correct before you spend
a model's time finding out for you.

## What isn't here yet

- Five tasks exist so far (`001-merger-rate-feature`,
  `002-pair-binning-convention`, `003-pair-finder-validation`,
  `004-catalog-loader-test-adequacy`, `005-scope-temptation`). `docs/DESIGN.md`
  has the backlog for more, mined from a prior project's model-comparison
  series.
- `eval/leaderboard.md` is currently empty. 68 development trials across
  three rounds were archived after harness, grading, environment, or mutation
  defects made them unsuitable as official comparisons. The environment leak
  is fixed; Tasks 001-003's mutation sets must be repaired before the weak tier
  is run again. A strong-tier batch (higher-capability models, `--effort high`)
  and opencode-hosted cloud models haven't run yet either. See
  `docs/DESIGN.md`'s History for the evidence and sequence of fixes.
- No sandboxing beyond a git worktree. If you don't trust a model+harness
  combination to run arbitrary code on your machine, run this inside an
  isolated environment (an `agent-sbx` sandbox, a container, a VM) rather
  than directly on the host -- the repo doesn't care where it runs, since
  every path resolves relative to `git rev-parse --show-toplevel`.
