# Design notes

## Why this repo exists

`relative-velocity` had accumulated a `project-manager`-driven workflow for
testing local LLMs: a frozen implementation plan, a PM that ran a slice,
commissioned drift-audit and code-review, steered corrections, and only
accepted a slice once it passed. Across 32 supervised runs and four
model-comparison reports, that setup produced one extremely consistent
finding: **every completed run converged on numerically identical output**,
regardless of which model wrote it. A 3B-active-parameter model and a
397B-parameter model, given the same plan, produced the same six fitted
slopes to the same significant figures.

That is a success of the review/fix loop, not evidence about the models. A
PM that runs the test suite itself, re-derives pinned constants, commissions
independent review, and steers up to three correction rounds per slice will
converge almost any Developer model toward the same accepted artifact --
report 04 measured this directly: a mediocre Developer pushed through ten
steer rounds over 20 hours produced code that scored as well on mutation
kill-rate as the best zero-steer run from the best model. The loop was doing
the work.

If the question is "which model is actually good," the loop has to come
off. This repo is what's left when it does: one harness invocation, one
model, one attempt, graded afterward by machinery that doesn't care what
the run claims about itself.

## What was kept from the old repo

- The scientific pipeline (`src/`, `tests/`) -- unmodified, as the domain
  substrate every task is built against. The point was never to test models
  on toy problems.
- `docs/BACKGROUND.md` -- the scientific motivation, unchanged.
- The close-pair merger-rate feature plan (`MERGER_RATE_PLAN-REVISED.md`)
  became Task 001's `spec.md`, reframed from a three-session PM-mediated
  plan into a single-shot task. Its Acceptance Criteria prose survived
  three rounds of amendment across the old report series specifically to
  close ambiguities that let models write vacuous tests -- that refinement
  is exactly what makes it useful here, so it was kept almost verbatim
  rather than rewritten.
- Task 001's hidden tests (`hidden_tests/test_hA.py`, `test_hB.py`) and its
  19-mutation gate (`mutations/sitecustomize.py`) are near-verbatim ports of
  the actual scratch harness that produced the old repo's report 04 --
  proven instruments, not reconstructions from memory. See the provenance
  note below.

## What was dropped

- `project-manager`, `drift-audit`, `code-review` as *run-time* participants.
  A one-shot trial has no PM to adjudicate, no reviewer to commission, no
  steer budget to spend. Independent review still exists in this repo, but
  only as the fixed, post-hoc `judge` categories in the rubric -- it never
  talks back to the model.
- The per-run branches, `.pm/runs/`, `.orchestrator/runs/`. Those were the
  artifacts of the old methodology; they're preserved in `relative-velocity`,
  not carried forward here.
- Report-writing as prose. `eval/leaderboard.md` is generated from
  structured JSON, not hand-authored per comparison.

## Protocol

Held constant across every trial of a given task: the prompt template, the
starting repo state, the harness invocation shape, the time budget, and the
grading code. The only thing that varies between trials is the
harness+model pair. That is deliberate -- see `eval/harness/harnesses.py`'s
docstring for why the per-harness command shapes are treated as fixed
infrastructure, not something a task or a run should improvise.

Multiple trials per (task, model) are expected, not optional. The old
report series found within-model variance collapsing as the plan tightened
(report 04: 1-2 points on a 30-point scale) but never below the point where
n=1 was defensible for a ranking. Run at least 3-5 trials before treating a
score as a model's, not a lucky seed's.

## Rubric

Four automated categories (correctness, test adequacy, scope discipline,
hygiene) and two judged ones (readability, maintainability), fixed in
`eval/rubric.yaml`. The weighting favors what's automatable: 75 of 100
points come from checks that don't require a judge's opinion. The two
judged categories are excluded from the total (not defaulted to a
mid-scale guess) until a judge model is actually configured, so an
unconfigured judge can't silently look like a passing grade.

## Provenance of the mutation gate

The 19 mutations in `eval/tasks/001-merger-rate-feature/mutations/` and the
`sitecustomize.py` import-hook mechanism that applies them were recovered
from the scratch harness used to produce `relative-velocity`'s report 04
(fourteen mixed-harness runs, 2026-08-26) -- not reimplemented from the
report's prose description. That harness monkey-patches the already-imported
module's public functions post-import via a `PYTHONPATH`-loaded
`sitecustomize.py`, so it works identically regardless of how a submission
structured its implementation internally, and never edits a trial's files.
Validated in this repo by running it against a known-correct reference
implementation (`eval/tasks/001-merger-rate-feature/reference_solution/`):
19/19 mutations killed, 59/59 hidden tests passed.

## Task backlog

Only one task exists so far. Candidates for the next ones, in rough order of
how cheaply they'd add discriminating signal:

1. **A genuinely harder task with a design decision, not just pinned
   literals.** The old report series' own conclusion (report 04 §7.8 #2):
   once every acceptance criterion pins an exact value, the task stops
   discriminating on capability and only discriminates on hygiene. A task
   that requires choosing *how* to solve something -- not just matching a
   number -- would separate models the current task can't.
2. **Validation-hardening tasks against the baseline pipeline itself.**
   `pair_finder.py`, `calc.py`, and `data_reader.py` currently do almost no
   input validation (they're trusted, hand-fed pipeline stages). A task
   that asks a model to add fail-loud validation to an existing function,
   under the same "validate form before coercion" convention Task 001
   documents, tests the same discipline axis on a shorter, more isolated
   surface.
3. **Standalone test-adequacy probes.** Give a model a correct, unguarded
   function and ask only for tests. Grade purely by mutation kill rate
   against a small seeded mutation set. Isolates the "can this model write
   a test that can fail" question from correctness entirely -- useful
   because Task 001 currently conflates the two into one score.
4. **Scope-temptation tasks.** A narrow, well-specified fix sitting next to
   an obviously messy, unrelated piece of code. Scores whether the diff
   stays inside the declared surface when there's a nearby "attractive
   nuisance" to clean up. `scope_discipline` already exists as a rubric
   category; this task type would be the first one designed specifically
   to stress it.
5. **Re-test whether harness matters independent of model.** Every trial in
   the old report series used `opencode`. This repo can now run the same
   model through `opencode`, `claude`, `codex`, `copilot`, or `qwen` --
   worth deliberately holding a model fixed and varying only the harness
   once more than one task exists, to separate harness effects from model
   effects (a distinction the field literature flags as commonly conflated).
