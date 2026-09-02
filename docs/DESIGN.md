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

The mutations in `eval/tasks/001-merger-rate-feature/mutations/` and the
`sitecustomize.py` import-hook mechanism that applies them were originally
recovered from the scratch harness used to produce `relative-velocity`'s
report 04 (fourteen mixed-harness runs, 2026-08-26) -- not reimplemented from
the report's prose description. That harness monkey-patches the
already-imported module's public functions post-import via a
`PYTHONPATH`-loaded `sitecustomize.py`, so it works identically regardless of
how a submission structured its implementation internally, and never edits a
trial's files. The set grew from the original 19 to 34 during this repo's own
adversarial audit (see History below); as of that fix, validated against the
reference implementation (`eval/tasks/001-merger-rate-feature/reference_solution/`):
34/34 mutations killed, 0 survivors, 61/61 hidden tests passed.

## History

Per this repo's own convention (see `AGENTS.md`): when a task's spec turns
out to be ambiguous or its hidden tests/mutations turn out to be wrong, the
fix is recorded here, not left for a future model to rediscover by guessing.

### Task 001 (`001-merger-rate-feature`)

Built by forking `relative-velocity`'s `MERGER_RATE_PLAN-REVISED.md` into
`spec.md` and porting its hidden tests/mutation gate near-verbatim (see
Provenance above). An independent adversarial audit of the *task's own
content* (as opposed to the harness plumbing around it, which had already
been checked) found real defects, all fixed and re-validated from a clean
scratch tree:

- **Spec self-contradiction**: the spec instructed computing the merger rate
  via one route (`f_pair * n_gal`) while a hidden test pinned bit-exact
  equality to an algebraically-but-not-bit-identical reduced-form
  expression. Floating point isn't associative, so a correct implementation
  following the spec's own literal instruction could fail on the last bit.
  Fixed by switching to `np.testing.assert_allclose` wherever arithmetic is
  involved, keeping exact `==` only for literal pinned values with no
  intermediate arithmetic.
- **`test_C10` inspected submission source text** (checked for
  `"sum("`/`"dot("` substrings) instead of numerical behavior -- a correct
  `@`/`einsum` implementation would have failed this test through no fault
  of its own. Replaced with a numerical fixture that exercises the actual
  computation.
- **Mutation hook patched only the exact bare import name.** A submission
  written as `from src import merger_rate` received zero mutations,
  silently inflating `test_adequacy` to 100% regardless of test quality.
  Fixed to patch by module basename instead, so it's insensitive to how a
  submission imports the module under test.
- **6 BLOCKING + 8 SIGNIFICANT defects** found by an independent codex
  adversarial audit beyond the three items above (full detail was in that
  session's `.orchestrator/` delegate history, which does not survive a
  fresh clone -- the durable record is the fix itself and the commit
  message). Fixed and independently re-validated: reference suite 26/26,
  hidden tests 61/61 (up from 59), mutation gate 34/34 killed, 0 survivors
  (up from 19 mutations / 17 killed). Commit `6eeedf2`.

### Task 002 (`002-pair-binning-convention`)

Built as backlog item 1 below: a genuine design-decision task (three
mass-bin-assignment conventions, with the fraction's denominator derived
from first principles rather than pinned as a literal), not just pinned
literals. Built with every Task 001 lesson applied up front; an independent
codex adversarial audit still found **5 more BLOCKING gaps specific to this
task's own integration/driver layer**:

- A driver could hardcode "additivity holds" -- no fixture built from real
  data can ever exercise the `False` branch of an additivity check, since
  additivity is a mathematical identity true on all valid data. Only a
  monkeypatch of the check itself can confirm the driver actually consults
  it and propagates the result (added as `test_B24`: patches
  `check_additivity`, asserts propagation through the returned dict, the
  persisted HDF5 attrs, and the console output).
- A driver could hardcode the default mass-bin grid even though the pure
  functions were correctly tested against an alternate one.
- Preflight atomicity was tested with only one redshift.
- Mass-ratio-cut reapplication was invisible because every fixture pair
  happened to sit above the default cut.
- The mutation set could score 31/31 without any mutation touching the core
  pair-fraction formula.

**Lesson for future tasks** (carried into this session's backlog-item work
below): a "lessons learned" briefing prevents recurrence of specific known
patterns, but each new task's own integration/driver layer needs its own
adversarial pass -- hardcoded-default and never-exercised-false-branch
defects recur at every new layer of integration, not just once per repo.

Also found during the same audit, in the reference solution itself (a real
correctness bug, not just a test gap): `check_additivity` converted integer
pair counts to float before comparing, losing precision above `2**53`.
Fixed to compare in exact `int64` arithmetic.

Fixed and independently re-validated from a clean scratch tree (numbers
matched the fix subagent's self-report exactly): baseline pipeline 80/80,
reference solution's own suite 129/129, hidden tests 140/140 (grown from an
original 50 -- structurally confirmed to be parametrization of existing
rejection-matrix loops into independently-scored cases, a fairness fix
rather than sprawl, since a loop test under-penalizes corner-cutting by
costing the same single failure whether one case or a whole behavioral
check is skipped), mutation gate 34/34 killed. Commit `106112d`.

### Harness: TASK.md diff pollution and judge reliability

The frontier-model spot-check (Task 001 + Task 002, `gpt-5.6-luna` and
`claude-haiku-4-5-20251001` at low/medium effort -- the first real trials
ever run through `run_trial.py`'s actual end-to-end path, not a
hand-assembled scratch tree) surfaced three harness defects in
`grade_trial.py`/`run_trial.py`, all found by inspecting the first graded
trial closely rather than trusting its score, and all fixed and verified
against real (re-graded, not re-run) trial data:

- **`TASK.md` (the spec file `run_trial.py` drops into every worktree) was
  polluting every diff-based check.** It isn't in any task's
  `authorized_surface`, so `scope_discipline` docked every single trial for
  "touching" it; worse, being the full `spec.md` text (tens of KB), it ate
  most of `run_judge()`'s 40000-character truncated diff budget ahead of the
  actual code -- confirmed directly: one trial's judge notes said it could
  only see "TASK.md and a trivial import-reordering hunk." Fixed with a git
  pathspec exclusion (`:(exclude)TASK.md`) in both checks.
- **The same pollution left `run_trial.py`'s `changed_files` never empty**,
  so `grade_trial.py`'s `no_submission` gate (meant to score 0 everywhere on
  an empty/crashed trial per `rubric.yaml`) could only ever fire on a
  timeout, never on a harness crash or auth failure that exits early.
  Fixed the same way. Found by an independent Opus review commissioned
  specifically to check the two fixes above for correctness and
  proportionality -- it is the reason that review step is worth doing even
  on a small diff.
- **An occasional malformed judge response silently produced a
  partial-weight total** (e.g. "93% of rubric weight scored") visually
  indistinguishable in the report from the legitimate "no judge configured"
  case, and not comparable to a trial that scored the full 100%. Fixed:
  `run_judge()` now retries (`MAX_JUDGE_ATTEMPTS = 3`) and a persistent
  failure hard-fails the grade instead -- a diagnostic is written under the
  gitignored `eval/results/tmp/judge_failures/`, `grade_trial.py` exits
  non-zero, and nothing is written to `eval/results/runs/` or `reports/`, so
  a failed grading can never silently enter `aggregate.py`'s leaderboard.

None of this changed any of the 8 spot-check trials' scores (all eight
scored 100% of rubric weight once fully re-graded) -- the fixes close gaps
that hadn't yet been hit by this particular batch, not gaps that had
silently corrupted it.

## Task backlog

Candidates for the next tasks, in rough order of how cheaply they'd add
discriminating signal. Status noted per item as the bench grows.

1. **A genuinely harder task with a design decision, not just pinned
   literals.** The old report series' own conclusion (report 04 §7.8 #2):
   once every acceptance criterion pins an exact value, the task stops
   discriminating on capability and only discriminates on hygiene. A task
   that requires choosing *how* to solve something -- not just matching a
   number -- would separate models the current task can't. **Done --
   Task 002, see History above.**
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
