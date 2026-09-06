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

## Tasks

Five tasks exist so far, under `eval/tasks/`, spanning five different
capability axes so a model's result shows up as a profile, not a single
number. Each declares its own `rubric_profile`, mutation-bank size and
one-shot time budget in `meta.yaml` (see "The rubric" below for what a
profile changes); mutation counts and budgets are noted per task below.

| id | axis | difficulty | time budget |
|---|---|---|---|
| `001-merger-rate-feature` | feature-extension | High | 6h |
| `002-pair-binning-convention` | design-decision | High | 6h |
| `003-pair-finder-validation` | validation-hardening | Medium-High | 3h |
| `004-catalog-loader-test-adequacy` | test-adequacy | Medium | 2h |
| `005-scope-temptation` | scope-temptation | Low (impl.) / High (discipline) | 3h |

**001 -- Close-Pair Merger Rate Estimation.** Adds `src/merger_rate.py`,
converting the pipeline's existing close-pair counts into a merger-rate
density via the Kitzbichler & White close-pair method: a galaxy-count
denominator threaded back into `calc.py`, a parameterized merger-timescale
model, Poisson error propagation, and a weighted-least-squares check that
the recovered redshift slope matches the injected timescale exponent. Three
parts; the heaviest scientific-reasoning load in the bank (algebraic
identities, numerical-stability requirements on the fit, careful non-goal
boundaries around which redshift convention and whose `box_size` is
authoritative). 73 scored mutations.

**002 -- Pair-to-Mass-Bin Assignment Conventions.** Adds
`src/pair_binning.py`, which recomputes pair statistics under three
different binning conventions (primary/secondary/either mass) from data
`calc.py` already wrote -- and, distinctively, does not hand the model the
denominator formula: it has to derive `N_gal` from three stated invariant
properties and prove an additivity identity holds at runtime. The one
task in the bank built specifically around "figure out the right design,"
not just "match a pinned number." 111 scored mutations.

**003 -- Fail-Loud Input Validation for `find_pairs`.** Hardens one
existing function against malformed input: a large rejection matrix (bad
dtypes, NaNs, out-of-box positions, malformed bins), a strict "validate
form before coercion" discipline, precedence rules for which of several
simultaneous violations gets reported, and a subtle correctness trap
(integer/unsigned-dtype catalogs must be silently promoted to float64
before arithmetic to avoid wraparound bugs). Narrowest implementation
surface with the largest mutation bank in the repo, 145 mutations.

**004 -- Test Suite for `load_galaxy_catalog`.** Pure test-writing: the
function under test is frozen and already correct, and the model's only
deliverable is `tests/test_data_reader.py`. Scored almost entirely on
mutation-kill rate rather than passing tests (`rubric_profile:
test_authoring`) -- a shallow "assert it returns a dict" suite scores near
zero. Isolates "can this model write a test that can actually fail" from
implementation ability. 53 scored mutations, smallest time budget in the
bank.

**005 -- Self-Describing Results Files.** A tiny, well-specified fix (two
new HDF5 provenance attributes) sitting three lines above two duplicated,
obviously-messy private helpers in `calc.py`/`plot.py`. Measures scope
discipline rather than implementation skill: does the model resist
"cleaning up" code it wasn't authorized to touch, even though the rubric's
maintainability category would otherwise reward exactly that cleanup. The
tension is real, not manufactured -- the one task purpose-built to stress
`scope_discipline`. 33 scored mutations.

`docs/DESIGN.md`'s Task backlog section has the reasoning behind each of
these five and the candidates under consideration for what comes next.

## Repo layout

```text
src/            frozen baseline pipeline (galaxy pair-finding; unmodified,
                imported by every task's tests)
tests/          the baseline pipeline's own test suite
docs/
  BACKGROUND.md   scientific motivation for the pipeline
  DESIGN.md       why this repo is shaped the way it is
eval/
  rubric.yaml         the scoring rubric -- versioned data, read at
                      grading time, never hardcoded in a script
  tasks/<id>/
    spec.md           the task, given to the model as TASK.md
    meta.yaml         authorized surface, hidden test list, mutation list,
                      rubric profile, required deliverables, and the named
                      acceptance obligations correctness is grouped by
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
    ruff_eval.toml    the pinned lint policy grading runs under
    judge_prompt.md   the judged-category prompt
    validate_obligations.py
                      checks each task's acceptance-obligation mapping
                      against its reference solution
    worktree_lifecycle.py
                      inventories/archives/prunes trial worktrees under
                      eval/results/tmp/worktrees/ -- see below
  results/
    runs/*.json       one structured record per graded trial
    reports/*.md      one human-readable report per graded trial
  leaderboard.md      generated -- don't hand-edit it
archive/          gitignored, not tracked. archive/<dated-reason>/ holds
                  trial records superseded by a harness/grader change,
                  moved here instead of deleted -- see docs/DESIGN.md's
                  History for why a given batch moved. archive/worktrees/
                  <run_id>/ is a standing store of per-trial evidence
                  (submission patch, manifest, transcript) written by
                  worktree_lifecycle.py before a worktree is pruned.
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

`ruff` supplies the lint half of the hygiene category, at the exact version
`eval/rubric.yaml` pins (`requirements.txt` pins the same one). Grading refuses
to run under any other version, checked before the slow steps -- see The rubric
below for why.

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
| `--timeout` | task's `developer_timeout_seconds` | model-invocation budget in seconds before the run is killed and scored as a non-submission; per-trial venv setup is excluded |
| `--label` | none | free text folded into the run id, for your own bookkeeping |

This prints a manifest path when it's done:

```text
[run_trial] manifest: eval/results/tmp/manifests/<run_id>.json
```

Each trial's fresh `./venv` is provisioned before the model starts; its setup
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
real result, not a data-collection failure. The same applies to a trial that
fails its task's compatibility gate, and to one whose diff is missing a
task-declared deliverable: both are scored honestly and kept, not filtered.

The record carries `deterministic_score`, `judged_scores` and
`composite_score` (see The rubric below) rather than a single total, plus a
`provenance` block recording exactly what graded it.

The mutation gate is the slow step (see the Tasks table above for each task's
mutation count; every mutation gets its own subprocess and timeout), so budget
several minutes for it on top of whatever the pytest suites themselves take.

## Cleaning up trial worktrees

Each trial leaves a git worktree (source + its own venv + caches) under
`eval/results/tmp/worktrees/` -- disk-heavy, and never needed again once
graded, but the model's uncommitted submission only exists there; an
archived graded report never contains a patch of it. Preserve that evidence
before deleting anything:

```bash
python eval/harness/worktree_lifecycle.py list             # inventory: size, age, archived/graded status
python eval/harness/worktree_lifecycle.py archive --all    # or --run-id <id> [--run-id <id> ...]
python eval/harness/worktree_lifecycle.py prune --all      # refuses any run whose patch isn't archived and current
```

`archive` writes `archive/worktrees/<run_id>/` (manifest, transcript, any
existing graded record, and a `git diff --binary --full-index` against
`before_head`). `prune` recomputes that diff fresh and refuses to remove the
worktree unless it still matches what's archived -- `--force` skips both
checks, destructively.

## Building the leaderboard

```bash
python eval/harness/aggregate.py
```

Rescans every file in `eval/results/runs/` and rewrites `eval/leaderboard.md`
from scratch. Run it after every graded trial, or in a batch after several.
Never hand-edit `leaderboard.md` -- it won't survive the next run.

## The rubric

`eval/rubric.yaml` is versioned data, and every weight, penalty, threshold
and policy value in it is read at grading time rather than hardcoded in a
script. It is currently at **version 2**; version 1 was superseded on
2026-09-05 before any valid leaderboard result was ever recorded against it,
which is why there was nothing to migrate. `docs/SCORING-REDESIGN-ASSESSMENT.md`
is the reasoning; `docs/DESIGN.md`'s History records what changed.

Four categories are fully automated (correctness, test adequacy via mutation
kill rate, scope discipline, hygiene); two (readability, maintainability)
are judged by a single fixed model, pinned to `claude-opus-5` via the
`claude` harness at high effort. Until a judge model is configured, judged
categories are reported as unscored and the totals are renormalized over what
was actually measured, not padded with a guess.

A graded trial produces three numbers, not one:

- **`deterministic_score`** -- the weighted mean over the scored automated
  categories. Fully repeatable, and the leaderboard's default ordering.
- **`judged_scores`** -- readability and maintainability, reported per
  dimension alongside judge identity and status.
- **`composite_score`** -- the weighted mean over every scored category. A
  convenience summary only. Differences inside the documented 1.5-3 point
  same-input rejudge band are ties, not ranks.

The parts worth knowing before you read a score:

- **Correctness is grouped by acceptance obligation, not by pytest node.**
  Each task's `meta.yaml` declares named `acceptance_obligations`; each group
  scores the fraction of its own hidden-test nodes that pass, and the groups
  are equally weighted. Task 003's rejection matrix is one obligation
  expressed as 205 parametrized cases -- under raw node counting it was two
  thirds of correctness on its own. Adding a parameter case to an existing
  obligation can no longer silently rewrite the rubric.
- **Profiles, not one weighting for every task.** A task selects one via
  `meta.yaml`'s `rubric_profile`. `default` weighs correctness directly;
  `test_authoring` (Task 004, whose source code is frozen and whose only
  deliverable is a test suite) makes correctness a pass/fail compatibility
  gate carrying no weight, and mutation adequacy the dominant result. A
  failed gate scores the trial zero and *keeps* it, flagged.
- **Scope penalties are fixed per file**, not divided by diff size: 0.5 of
  the scope fraction per ordinary unauthorized file. A change to something
  the grading process itself depends on -- `eval/`, a stray `conftest.py`,
  a frozen test -- is an integrity violation that zeroes the category and
  flags the trial.
- **Mutation credit only comes from the test file the task authorized.** The
  full suite still runs as a regression check, but a frozen or unrelated test
  can't earn test-adequacy credit.
- **Lint is pinned.** `eval/harness/ruff_eval.toml` is the repository's own
  ruleset, passed with `--config` so a submission can't change the policy it
  is graded under, at the exact ruff version `rubric.yaml` names. Grading
  refuses to run at all under a different ruff, checked up front before the
  slow steps -- a different linter is a different hygiene policy, and awarding
  the category's full weight with no lint coverage behind it would be worse
  than stopping.
- **Nothing failing is filtered away.** No-submission, incomplete submission
  (a non-empty diff missing a task-declared deliverable) and failed gates all
  stay in the primary aggregate; the leaderboard shows a completion rate
  beside every group so reliability failures stay visible instead of being
  laundered into survivorship bias.
- **Every record carries its provenance** -- rubric version and hash, task
  contract hash, grader revision, judge identity and prompt hash, Python,
  ruff and dependency versions. `aggregate.py` partitions on the parts that
  change what a score *means* -- rubric bytes, task-contract bytes, judge-prompt
  bytes, and the resolved baseline commit -- so records graded under different
  versions can never be averaged into one cohort. Grader revision is
  deliberately not part of that key (it would split a batch on a docs-only
  commit); a group spanning several grader revisions, or containing a trial
  graded from an uncommitted tree, is flagged loudly instead.

(Caveat: judging a `claude`-harness trial with a `claude`-harness judge
carries a same-family bias risk, disclosed and accepted rather than avoided
-- noted in `rubric.yaml` itself. The stronger case, a judge that *is* the
trial model, is detected and its judged and composite columns are withheld
from comparison.)

## Validating the evaluator itself

```bash
python eval/harness/validate_obligations.py
```

Rebuilds each task's frozen substrate in a temp directory, drops its
reference solution and hidden tests in, collects the hidden suite, and checks
that every collected node maps to exactly one declared acceptance obligation
and that every declared obligation matches at least one real node. Run it
after any change to a task's hidden tests or `acceptance_obligations` -- a
stale mapping would otherwise read as a permanently low ceiling on every
future trial, which is exactly the kind of defect this repo has learned to
catch early rather than months later.

`validate_obligations.py` never runs the mutation gate, though -- it only
checks the obligation mapping. To confirm a task's mutation bank actually
discriminates, run its reference solution through the real pipeline:

```bash
python eval/harness/reference_check.py --task 001-merger-rate-feature
python eval/harness/grade_trial.py --manifest eval/results/tmp/manifests/<run_id>.json
```

This builds a real worktree and venv and installs `reference_solution/*.py`
onto the task's authorized surface -- no harness, no model -- so
`grade_trial.py` grades it exactly like a real trial, mutation gate included.
Add `--variant weak_baseline` to grade a task's `weak_baseline/` control
instead (a deliberately weak test suite layered over the same correct
`src/`, proving the rubric penalizes a vacuous submission too). A
reference-check record is evaluator evidence, not a leaderboard entry --
`aggregate.py` excludes any record with `harness == "none"` from every
cohort, but archive it out of `eval/results/runs/` when you're done with it
rather than relying on that alone.

## Adding a task

Copy the shape of `eval/tasks/001-merger-rate-feature/`: a `spec.md` the
model reads, a `meta.yaml` declaring the authorized surface and pointing at
the hidden tests and (optionally) a mutation set, and `hidden_tests/` files
that get copied into the trial's `tests/` directory at grading time -- never
before. A `reference_solution/` isn't required, but it's the only way to
know your hidden tests and mutations are actually correct before you spend
a model's time finding out for you.

`meta.yaml` additionally needs a `rubric_profile` naming one of
`eval/rubric.yaml`'s profiles, a `required_deliverables` list, and
`acceptance_obligations` partitioning every hidden test function into named
obligations. Run `python eval/harness/validate_obligations.py --task <id>`
until it passes: every collected node must map to exactly one obligation and
every obligation must match at least one real node.

## What isn't here yet

- Only 5 tasks exist so far -- see "Tasks" above. `docs/DESIGN.md`'s Task
  backlog section has the reasoning behind each and the candidates proposed
  for what comes next, mined from a prior project's model-comparison series.
- `eval/leaderboard.md` now holds a real first batch: 90 graded v2 trials
  across 30 (task, harness, model, effort) groups and 6 models spanning weak
  frontier, local, subscription/cloud, and strong frontier tiers. Read
  `docs/V3-DISCRIMINATION-ASSESSMENT.md` before treating any of it as a
  finished comparison -- it documents a real discrimination problem found in
  this same data (`correctness` saturates at 88-100% for every model on
  every task) and the reweighting/task-coverage work still needed before a
  v3 rubric change. 68 earlier development trials across three rounds were
  separately archived (harness, grading, environment, and mutation defects
  made them unsuitable as official comparisons); see `docs/DESIGN.md`'s
  History for that sequence of fixes.
- No sandboxing beyond a git worktree. If you don't trust a model+harness
  combination to run arbitrary code on your machine, run this inside an
  isolated environment (an `agent-sbx` sandbox, a container, a VM) rather
  than directly on the host -- the repo doesn't care where it runs, since
  every path resolves relative to `git rev-parse --show-toplevel`.
