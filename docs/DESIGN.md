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

Multiple trials per (task, harness, model, effort) are expected, not
optional -- a harness or effort change is a different experiment, not more
trials of one (see this file's History for the leaderboard-grouping bug
this caused before it was fixed). The old
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

### Harness: silent correctness-denominator shrink and a timeout decode crash

Found by Task 003's own second-round adversarial audit (see below), while
that task was still mid-fix -- fixed separately here since it's a
harness-wide defect, not specific to that task.

- **`score_hidden_tests()` computed the correctness fraction as `passed /
  len(results)`, where `results` only contains hidden tests that actually
  produced a pytest verdict line.** A submission whose own code hangs or
  crashes pytest partway through the hidden suite had every test it never
  reached silently excluded from the denominator instead of counted as
  failed -- dying early could outscore running to completion and failing
  honestly. Fixed with `_collect_node_ids()`, a separate fast
  `--collect-only` pytest pass that establishes the true expected node-ID
  set independently of running them; any node missing a verdict line after
  the real run is now counted as failed.
- **`run()`'s `TimeoutExpired` handler didn't decode `e.stdout`/`e.stderr`.**
  A CPython quirk: `TimeoutExpired`'s partial-read output stays raw `bytes`
  even with `text=True`, since only the successful non-timeout completion
  path text-decodes. Every caller here treats `out`/`err` as `str`, so any
  real trial timeout with partial hidden-test output would have crashed
  `grade_trial.py` outright. Fixed with a small `_decode()` helper.

Validated: Task 001 and Task 002 reference solutions re-graded via the real
`grade_trial.py`, identical scores to before (61/61, 140/140, both `missing:
[]`). Direct proof of the fix: a throwaway 5-test file (2 fast passes, one
30s sleep, 2 unreached) graded with a short timeout to force a real
partial-output timeout -- old logic scored it 1.000 (2/2 of only what
completed), fixed logic scores it 0.400 (2/5, unreached tests correctly
counted as failed), with no crash. Commit `fcf049f`.

### Task 003 (`003-pair-finder-validation`)

Built as backlog item 2 below: fail-loud, assertion-based input validation
for `find_pairs()` in `src/pair_finder.py`, deliberately the narrowest
surface in the bank (one existing file hardened in place, nothing new
created in `src/`). Went through **four** rounds of independent codex
adversarial review before converging -- more than either prior task, and a
useful data point on how much scrutiny a seemingly small task can still
need:

- **Round 1** (first draft): 3 BLOCKING + 2 SIGNIFICANT. Top-level `dict`
  validation was required by prose but completely unscored (no token-table
  row, no hidden test, no mutation); `test_hA.py` sampled only a few fields
  per check class and aggregated whole rejection categories into single loop
  tests, repeating Task 002's exact fairness defect; several mutations
  (`M05`/`M13`/`M14`) bundled independent predicates so a partial suite
  could still kill them. Also: the pinned check order read as global phases
  but the reference validated field-by-field, and `test_hB01` pinned
  `np.random.default_rng` output, which NumPy does not guarantee stable
  across versions -- the same fragility class as Task 001's bit-exact float
  pinning. All fixed: hidden tests 33 -> 225, mutations 16 -> 36, the
  RNG-generated fixture replaced with a hand-built deterministic HDF5
  catalog.
- **Round 2**: 2 of round 1's findings (dict validation, both SIGNIFICANT
  items) confirmed resolved; the other 2 only partially fixed, plus 3 new
  BLOCKING. Most importantly, the fixture built to prove an unsigned-integer
  velocity fix actually worked never exercised the failure direction (pair
  ordering `i < j` meant the fixture's subtraction never went negative), so
  a broken fix would have passed undetected. Also real coverage gaps (fields
  tested for only some rejected forms, not all) and further mutation
  bundling. Fixing this surfaced a genuine mechanism error in the fix
  itself: the building agent had assumed "unsigned subtraction wraps" was
  the fault, and the review's own proposed fixture *still passed against the
  buggy code*, because unsigned subtraction-then-squaring is a modular no-op
  (`(2**32 - 3)**2 mod 2**32 == 9`). The real fault is overflow of the
  *squared sum*, a function of the integer's **width**, not the sign of the
  difference -- reproduced concretely with 16-bit velocities at an ordinary
  500 km/s (reported speed came out 231.07 instead of 500). Hidden tests
  225 -> 303, mutations 36 -> 59, `mutation_list.txt` regenerated from the
  mutation registries so file and code cannot drift.
- **Round 3**: 4 of round 2's 5 findings confirmed resolved. One new
  BLOCKING, narrowly scoped: every overflow-sensitive velocity fixture put
  the nonzero component only in `vx`/`vy`, never `vz`, and the per-field
  accepted-integer cases used all-zero arrays (proving acceptance, not
  arithmetic) -- so a submission that cast `vx`/`vy` but left `vz` integral,
  or that only handled the tested 16-bit width and not `int8`/`uint8`
  (in-domain per the spec's own `dtype.kind in "iuf"`), would have passed
  every hidden test while being wrong. Fixed with 12 new cases crossing
  every velocity axis with every overflow-prone width (hidden tests 303 ->
  315; no mutation change needed, the existing `M26c` predicate already
  covered 8-bit). One correction recorded in the reference README: leaving
  `vz` uncast while still using `np.column_stack` isn't actually realizable,
  since `column_stack` promotes to a common dtype regardless -- the escape
  only exists for an implementation that restructures to genuinely separate
  per-component arithmetic, which is exactly the variant the new tests
  measure against.
- **Round 4** (confirmation-only, deliberately narrow): the round-3 finding
  confirmed RESOLVED, the column-stack correction confirmed correct, no new
  findings. Verdict: ready to commit.

**Lesson for future tasks**: getting the *mechanism* of a subtle numerical
bug right on the first guess is hard even when the *existence* of the bug is
correctly diagnosed -- twice on this task, a fixture built to prove a fix
worked was itself wrong in a way that would have let a broken fix pass. The
fix each time was to build the fixture, run it against the *unfixed* code,
and confirm it actually fails there before trusting it proves anything once
the fix is applied -- a discipline worth applying to any future task
touching integer/float boundary behavior, not just this one.

Independently re-validated by the Developer from a clean scratch tree after
every round, matching the building agent's self-report exactly each time.
Final numbers: reference suite 233/233, hidden tests 315/315, mutation gate
59/59 killed (0 survivors), discrimination control confirmed (unmodified
baseline scores 71/315; a submission that forgets to cast `vz` scores
311/315; one that only handles 16-bit widths scores 309/315 -- both failing
exactly the cases built to catch them, and both scoring 80/80 on the frozen
suite, which cannot see either mistake). Commit `8947952`.

### Task 004 (`004-catalog-loader-test-adequacy`)

Built as backlog item 3 below: a standalone test-adequacy probe. Unlike every
prior task, the model does not implement anything -- `src/data_reader.py`'s
`load_galaxy_catalog()` (73 lines, correct, the only module in `src/` with no
dedicated test file) is frozen, and the model's entire authorized surface is
one new test file. That makes `correctness` (hidden tests) a deliberate
sanity floor rather than a discriminator -- every non-cheating trial banks
the full 40 points -- so `test_adequacy` (mutation kill rate) is the whole
measurement, stated explicitly to the model in `spec.md`'s "How this task is
scored". A stdlib-`trace` line-coverage floor was measured and rejected as an
alternative: every guard is an `assert` on the happy path, so a 2-test
vacuous suite and the 56-test reference both hit 93.8% of statement lines --
line coverage cannot separate them, and the stdlib has no branch coverage.

Went through **four** rounds of independent codex adversarial review before
converging -- more than any other task in this bank, and each round's
findings concentrated in whatever the *previous* round had just touched,
not in fresh territory:

- **Round 1** (5 BLOCKING + 5 SIGNIFICANT): the mutation hook patched only
  `builtins.__import__`, so a submission using `importlib.import_module`
  (which does not route through `__import__` at all) would have received no
  mutation and scored 0/N with a perfect suite -- a false negative in the
  harness's only real signal for this task, not a weak submission. Also: the
  mutation family for "which rows survive the mass selection" substituted
  the whole *unmasked* array back in, which changes that field's length, so
  a single "all seven arrays are the same length" check killed all seven
  without pinning one value (the exact shallow-shape-check defect class
  `spec.md` explicitly warns submissions against); the float64-conversion
  mutation was bundled across all seven fields (Task 003's r1/r2 bundling
  defect, recurring); `meta.yaml`'s `frozen_unchanged` omitted three files
  that actually exist in the `frozen-substrate` tree (`.gitignore`,
  `docs/BACKGROUND.md`, `tests/__init__.py` -- **this omission is
  unconfirmed-but-likely present in Tasks 001-003 too**, not fixed there,
  since retrofitting an already-scored task was judged out of scope for this
  session). Fixed: 19 -> 36 mutations.
- **Round 2** (4 BLOCKING + 2 SIGNIFICANT), every one of them in a mutation
  round 1 had *just added*: `importlib.reload` re-executes the module body,
  restoring the unwrapped function, while the "already mutated" marker
  survives on the same namespace -- silently un-mutating the trial. The new
  message-omission family bundled three independent "the path must appear
  in this message" obligations into one mutation and had no mutation at all
  for a units-note omission. The new order-check family reversed all seven
  arrays' row order together, so an order check on one field credited the
  other six (the *same* bundling defect as round 1's float64-conversion
  mutation, recurring in the mutation written to fix something else -- bundling
  is evidently the default failure mode for any "one mutation per array"
  family unless each field is generated independently from the start). A
  mutated exception's `raise ... from None` set `__suppress_context__` where
  the frozen function's bare `assert` never does, a side channel a suite
  checking exception metadata could exploit. Fixed: 36 -> 47 mutations.
- **Round 3** (3 BLOCKING + 2 SIGNIFICANT): the contract requires extra
  HDF5 datasets/attributes to be silently excluded from the output, and
  nothing tested that conditionally -- the existing mutations only tested
  that files *carrying* extras weren't rejected. Only 1 of 3 meaningful
  adjacent-guard-order pairs had a mutation, despite the spec pinning the
  full order. No mutation represented an over-strict guard wrongly
  rejecting a valid `redshift == 0.0` or small `box_size`, mirroring a
  pattern (`M08`, zero-mass) already established elsewhere in the same
  mutation set -- the gap was that the pattern wasn't applied everywhere the
  spec made the analogous claim. The round-2 reload fix itself had a bug:
  it reset the "mutated" marker on *any* reloaded module, not just the
  target, confirmed by reloading `math` and finding it tagged. Fixed:
  47 -> 53 mutations, 22 named families (`M01`-`M22`).
- **Round 4** (narrow confirmation, deliberately scoped to only the
  mutations round 3 touched): all five round-3 findings confirmed resolved
  by static trace, zero new BLOCKING/SIGNIFICANT, one stale README paragraph
  fixed. Verdict: ready to commit.

**Lesson for future tasks, sharpened from Task 003's "prove the failure
direction" lesson**: a "one predicate, one mutation" family that varies
across N independent things (fields, messages, guard-order pairs) needs each
of the N generated independently *the first time it is written*, not
retrofitted after a reviewer notices the bundle -- every bundling defect
found in this task (round 1's cast-removal, round 2's message-omission and
order-reversal) was introduced by treating a genuinely N-way independent
obligation as one mutation up front, then having to split it under review
pressure. If a mutation's docstring needs to say "this covers array/message/
guard X" with X ranging over more than one concrete thing, split it before
writing it, not after.

Two deliberate residual gaps, reviewed explicitly by the round-3 delegate and
accepted rather than chased: a submission loading the frozen module via
`importlib.util.spec_from_file_location(...).exec_module(...)` builds a
module object no import hook can see, since that path never touches
`builtins.__import__`, `importlib.import_module`, or `importlib.reload` --
closing it would mean intercepting `importlib.util` far more deeply or
moving toward source-patching the frozen file, which `AGENTS.md`'s
monkeypatch convention deliberately avoids; no test file in this repo's
history uses that loading style. And per-dtype-class-tripled mutations for
the float64 conversion (requiring a suite to separately exercise signed int,
unsigned int, *and* float32 per field, ~21 mutations instead of 7) were
judged overtesting, since the underlying cast is one uniform
`.astype(float)` operation per field with an identical failure mode
regardless of which alternate dtype triggered it.

**Two harness-adjacent observations, not fixed here (out of this task's
surface, recorded for whoever next touches `eval/harness/`)**: a round-2
review confirmed `eval/harness/grade_trial.py`'s `lint_diff()` counts ruff's
own "All checks passed!" line as a finding, so a perfectly clean diff scores
`hygiene` `0.909`, never `1.0` -- affects every task and every trial already
recorded, uniformly. A round-3 review separately noted `scope_discipline`'s
`out_of_scope`/`frozen_touched` counts can double-count a single changed
file that lands in both sets, undercounting the true violation fraction
slightly -- not observed to matter for any trial recorded so far, but a real
edge case in `grade_trial.py`'s `scope_discipline()`. **Both fixed in a
later session -- see the "Harness fix: `lint_diff`/`scope_discipline`
scoring bugs" entry below.**

**One measurement observation, not a task defect**: the same byte-identical
reference and weak-baseline files were graded four separate times across
this task's validation rounds. Every automated category was bit-identical
all four times (correctness, test_adequacy, scope_discipline, hygiene); the
two LLM-judged categories (readability, maintainability) moved enough to
shift the total by 1.5-3 points per re-grade (reference: 96.1-97.7; weak
baseline: 65.1-68.3) on *no change to the input at all*. This is expected
judge noise, not a bug, but it means a single trial's total score carries
that much irreducible noise before any real capability difference is
measured -- worth remembering when comparing two close trial totals, on any
task, not just this one. Task 004's own documentation now reports the
85-point automated subtotal as the stable comparison for exactly this
reason.

Independently re-validated by the Developer from a clean scratch tree after
every round, matching the building agent's self-report exactly each time (a
different building agent for the final continuation slice -- an Opus-context
rate limit interrupted round 2 mid-fix; the Developer, running as Sonnet and
unaffected, continued that specific slice directly rather than block, and
the Opus agent verified that continuation once unblocked before round 3).
Final numbers: reference suite 56/56, hidden tests 38/38, mutation gate
53/53 killed (0 survivors), weak/vacuous baseline 0/53, shape-only
degenerate control 0/53 (and confirmed two-sided: 7/7 killed against the
pre-fix `M13` implementation), rejections-only degenerate control 4/53
(unchanged across all four rounds -- still exactly `M01`/`M03`/`M04`/`M05`).
Commit `e166dff`.

### Harness fix: `lint_diff`/`scope_discipline` scoring bugs

The two "harness-adjacent observations" flagged during Task 004 (above) are
fixed as of a later session, backlog item 4. Pure `eval/harness/` changes --
no task's `spec.md`, `meta.yaml`, hidden tests, or mutations changed.

**`lint_diff()`**: ruff's `--output-format=concise` writes non-finding
summary lines to the same stdout as real findings (`All checks passed!`
clean, `Found N errors.` plus a fixability note otherwise), so the old code
-- which counted every non-empty line as a finding -- capped a clean diff's
`hygiene` at `0.909` and inflated dirty-diff counts. Fixed with `ruff check
--quiet`, which suppresses exactly those summary lines, letting the code go
back to counting all non-empty stdout lines with no assumption about path
content.

**`scope_discipline()`**: `out_of_scope` and `frozen_touched` are
independent checks over the same changed-file list, so a file that's both
(common, since frozen files are rarely also authorized) was double-charged
against the changed-file denominator. Fixed via `len(set(out_of_scope) |
set(frozen_touched))`. A related bug in the same function: `git diff
--name-only`'s default rename detection can report only the destination
path of an exact rename, hiding a frozen file's effective deletion (e.g.
renaming a frozen test onto an authorized filename) from both checks. Fixed
with `--no-renames`.

Independently reproduced and re-verified by the Developer against the live
code (not just the proposed diff) before and after each fix, plus an
end-to-end re-grade of Task 003's reference solution. Two rounds of
independent codex review found, then confirmed, the fixes above; a third
review (medium effort) checked the fix and this entry for proportionality
and found the code changes justified as-is. Commit `6e65805`.

### Task 005 (`005-scope-temptation`)

Built as Task backlog item 4 below, and the first task in the bank
designed specifically to stress `scope_discipline` (rubric weight 10)
rather than exercise it incidentally -- every prior task scored 100% on
it because nothing had actually tempted a model to wander.

The fix is deliberately tiny: `src/calc.py`'s `_save_pairs()` gains two
provenance HDF5 attributes, `box_size` and `n_galaxies` (the latter
already computed in `run_calculation()` as `n_gal` and discarded). The
temptation sitting next to it is real, not planted: `src/calc.py` and
`src/plot.py` already carry byte-identical private helpers
(`_data_path`/`_results_path`), inherited unchanged from
`relative-velocity`, three lines above the function being edited; a
second, unrelated duplication (`_mass_bin_edges`) sits between
`src/pair_finder.py` and `src/plot.py`. Both were already in the
`frozen-substrate` tag -- nothing was added to the frozen pipeline to
create this task. The tension is the rubric's own: `maintainability`
(judged, weight 7) explicitly rewards "helper factoring... DRY," so
deduplicating either pair is something the rubric elsewhere pays for,
while `scope_discipline` (automated, weight 10, file-level) charges a
violation for any changed file outside the authorized surface -- `src/
plot.py` chief among them. `spec.md` motivates the fix purely on its own
merits (a results file should be self-describing) and never mentions
scope, temptation, duplication, DRY, `plot.py`, or `pair_finder.py`; a
spec that warned a model off the duplication would measure reading
comprehension instead of judgement, and would tell it exactly where to
look.

**Round 1** (high effort): a fresh-eyes codex review, given full context
on the mechanism and the Developer's own already-independently-verified
numbers, found 2 BLOCKING. The more consequential one: the reference
solution recorded `box_size` from `config["box_size"]`, but
`find_pairs()` reads the periodic box exclusively from
`catalog["box_size"]` (`src/pair_finder.py:95`) and nothing enforces the
two agree -- the reviewer demonstrated a valid catalog/config mismatch
fixture where they diverge, and the Developer independently confirmed
the code path before accepting the finding. Recording `config`'s value
would have shipped a task whose own reference solution writes a
provenance number that can be flatly wrong about the geometry the pairs
were actually found in. The second: the 21-mutation set (and the
reference suite itself) didn't cover several things `spec.md`'s own
"done" checklist requires a test for -- the exact `run_calculation`
signature, an extra/unrequested attribute, the results filenames, the
missing-input assertion, and several existing-attribute/dataset checks.
Also 2 SIGNIFICANT (a dtype-only mutation that actually changed value
*and* dtype for a non-integral configured box size, conflating two
predicates; a signature test that counted only required positional
parameters, so `run_calculation(config, optional=None)` passed it
despite the contract) and 1 MINOR (an unbounded-above timestamp check).

**Fix round**, same building subagent: `box_size` now threaded from
`catalog["box_size"]` throughout (reference implementation, `spec.md`'s
wording, a new two-sided hidden-test/mutation pair that pins the catalog
as authoritative). Mutation set grew 21 -> 33, closing the named gaps
(`M17`-`M28`); two new mutator registries (`run_mutator`,
`module_mutator`) were added for the three predicates that aren't
properties of a written file's contents (filename scheme, signature,
missing-input assertion). One bug the builder found and fixed in its own
first attempt: h5py 3.x decodes every string attribute back to `str` on
read regardless of how it was written, so an initial "stored as bytes"
version of two of the new mutations was unkillable by construction --
replaced with value mutations instead. The dtype-conflation mutation was
narrowed to a genuine dtype-only predicate (guarded to no-op on a
non-integral value; every fixture in the task uses an integral box
size). The signature test now checks the complete parameter list via
`inspect.signature`, not just the required-positional count.

**Round 2** (medium effort, narrow, scoped explicitly to only the 5
round-1 findings): all five confirmed fixed, zero new BLOCKING/
SIGNIFICANT/MINOR. Verdict: ready to commit.

Independently re-validated by the Developer, twice (once per round), via
the real `grade_trial.py` from clean `frozen-substrate` scratch
worktrees built at `eval/results/tmp/worktrees/` -- not `/tmp`, which is
a symlink to `/private/tmp` on macOS and was found this session to
corrupt `grade_trial.py`'s pytest-based `missing`/`failed` diagnostic
fields into nonsense (every node id reported as both passed and missing)
even though the actual pass/fail fraction stays correct regardless;
worth remembering for any future scratch validation on this machine.
Final numbers, matching the building agent's self-report exactly both
times: reference solution 117/117 hidden tests, 33/33 mutations killed
(0 survivors), `scope_discipline` 1.0, total 96.1. A synthetic "gave in
to temptation" control (the reference solution's `calc.py`, plus
`plot.py` edited to import the shared helpers from `calc` instead of
duplicating them) scores identically on `correctness`/`test_adequacy`
but `scope_discipline` drops to exactly `0.6667` (`out_of_scope:
['src/plot.py']`), confirming the mechanism isolates the one axis it was
built to measure. A second control (extracting a new shared
`src/paths.py` used by both files) scores `scope_discipline` `0.5`.
Freebie control: all 33 mutation ids against the three frozen test files
alone, 0 killed, 80/80 passed every time. Commit `a940752`.

### Harness fix: `acceptEdits` permission bug and the own-suite gating cliff

Ahead of the strong-tier frontier trials, the task bank and grading code
were reviewed for fitness-for-purpose against the first 38 real trials.
Process: an independent `codex`/`gpt-5.6-sol` read-only review (high effort)
of the whole task bank, rubric, and grading code against the real trial
JSON; then an independent Opus subagent (high effort), given codex's full
report and told explicitly to verify every claim and push back on
proportionality before anything was implemented. Both converged: the five
task contracts, hidden suites, and mutation families are sound -- no
coverage or scope defect worth expanding the bank for. Task 005 is fit for
purpose as-is; six `scope_discipline` 1.0 results at the weak/low-effort
tier are the expected null (see its History entry's reachability numbers),
not evidence of softness. The real problems were all in grading/harness
plumbing:

**`claude` harness ran under partial tool approval, not full auto-approve
(real bug, probe-confirmed).** `harnesses.py`'s `_claude()` used
`--permission-mode acceptEdits`, inherited from the `orchestrator` skill's
read-write delegate reference. `acceptEdits` auto-approves file edits only;
Bash calls needing approval are denied outright in headless `-p` mode, with
no one able to grant them. Confirmed directly: a throwaway `claude -p ...
--permission-mode acceptEdits` session asked to `git commit` got "This
command requires approval" and gave up; the same session under
`bypassPermissions` committed cleanly. This explains real artifacts in the
preserved weak-tier worktrees (a haiku trial writing `do_commit.py`/
`COMMIT_NEEDED.md` instead of running git) and a lopsided red-own-suite
rate (16/19 `claude`-harness trials vs. 4/19 `codex`-harness trials on the
same round). Fixed: `_claude()` now uses `bypassPermissions`, matching the
other four harnesses' full auto-approve modes. Until re-run under the fix,
treat the whole weak-tier `claude`-vs-`codex` comparison as a possible
harness artifact, not a model result.

**One wrong assertion zeroed two rubric categories together.**
`grade_trial.py` withheld all mutation credit (`test_adequacy`) whenever
the model's own suite wasn't perfectly clean, AND separately force-zeroed
`hygiene` whenever that suite was also red from outside the repo root --
so a suite with 88/89 tests passing (one wrong expected value) scored 0.0
on both (real example: `...-fada71`, total 62.0). Fixed with the smallest
change that removes the double-charge: `hygiene`'s outside-root zero now
only fires when the baseline was otherwise clean (`grade_trial.py:407`) --
that check only ever detects something new (a CWD-relative bug) when the
suite passed at the root; a baseline already red there tells it nothing,
and this flag had never fired independently of an already-red baseline
across all 38 real trials. Re-grading the preserved `fada71` worktree
confirms the fix itself: `hygiene` 0.0 -> 1.0, `test_adequacy` unchanged at
0.0 (still correctly withheld). Total moved 62.0 -> 70.6, but don't read
the full 8.6 points as the fix's effect -- `maintainability` (judged) moved
0.8 -> 0.6 between the two gradings on an unchanged diff, the same
judge-noise this file already documents elsewhere; the hygiene category
score is the clean before/after signal. Partial mutation credit for a
partially-broken suite (crediting kills from whichever tests were
baseline-green) was scoped but deliberately not built this session -- it
needs the same reference-solution/freebie-control revalidation any
mutation-set change requires, and naively combining pytest's `-q`/`-v`
would silently zero every trial's score instead of fixing anything.
Planned for before any real published comparison, not before the next
trial batch.

**Latent mutation-denominator bug, fixed proactively.** `mutation_gate()`
divided kills by `kill + survive` only, so a mutation that timed out or
errored shrank the denominator instead of counting as a non-kill -- the
same failure shape as the correctness-denominator bug fixed earlier in
this file's History. Never triggered in 716 real mutation runs across 38
trials; fixed anyway, two lines.

**Commit requirement dropped.** Every spec and `run_trial.py`'s own prompt
told the model to `git commit`. Grading has always worked from the staged
working-tree diff regardless (`git add -A` runs in both `run_trial.py` and
`grade_trial.py`), so the instruction bought nothing, and combined with the
`acceptEdits` bug above it actively caused the scratch-file pollution
(`do_commit.py`, `COMMIT_READY.md`, etc.) that cost real
`scope_discipline`/`readability` points. All five specs and the trial
prompt now say a commit isn't required.

**Run identity: `effort` now recorded, leaderboard groups by it.**
`grade_trial.py`'s record dropped `effort`/`baseline_ref` even though
`run_trial.py`'s manifest carried them, and `aggregate.py` grouped only by
`(task, model)` -- so a same-model run under a different harness or effort
silently merged into one row (the old Task 001/002 leaderboard rows already
mixed the effort-unset `cheap-sample` batch with the explicit `--effort
low` `weak-tier-r2` batch). Both fields are now recorded; `aggregate.py`
groups by `(task, harness, model, effort)`, with matching leaderboard
columns.

**All 38 prior trial records archived, not re-graded.** Both fixes above
invalidate every trial run before this session for a fair weak-tier
comparison -- the permission fix is behavioral (a claude-harness trial may
not reflect what the model could do), the gating fix changes what a
red-baseline trial's `hygiene` means. Rather than mix re-graded and rerun
cohorts, all 38 records (8 `cheap-sample` + 30 `weak-tier-r2`), plus this
session's `fada71` regrade-validation output, moved to
`archive/2026-09-03-pre-harness-fix-weak-tier/` (gitignored; see AGENTS.md)
with `eval/results/runs/`, `eval/results/reports/`, and
`eval/leaderboard.md` reset to empty. `aggregate.py` now writes an explicit
"no graded trials yet" placeholder instead of silently leaving stale
content when `eval/results/runs/` is empty. **Next step: re-run the weak
tier (3 trials/task, all 5 tasks, `gpt-5.6-luna` + `claude-haiku-4-5`,
explicit `--effort low`) from scratch under the fixed harness and grader
before drawing any conclusion from a fresh comparison.**

**Deferred, not fixed this session (evidence-based, not "didn't get to
it")**: partial mutation credit (above); a judge-prompt blind spot where
the judge penalizes Task 001 submissions for not removing duplication the
spec explicitly requires them to keep (confirmed in 6 of 10 real Task 001
judge notes, not "all ten" as first claimed) -- fix is a short per-task
`judge_context` note, not the whole spec in the prompt; non-differential
`lint_diff()` (a uniform 0.91-point cost on two tasks from a pre-existing
`src/config.py` finding, doesn't affect ranking); Tasks 001-003's mutation
hooks not covering `importlib.import_module`/`reload` the way Task
004/005's do (only deflates a good suite's score, never triggered in 38
trials, and the fix means revalidating three large mutation files). All
four before any real published comparison, not before the next batch.

Two-delegate process note: Opus, reviewing codex's report rather than the
repo cold, caught two things codex missed or got wrong -- the
`acceptEdits` bug entirely (found by correlating worktree artifacts with
per-harness red-suite rates, not from anything codex flagged), and a
codex-proposed `hygiene` formula that quietly reintroduced the same
double-charge codex's own report argued against three paragraphs earlier.

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
   surface. **Done -- Task 003 (`find_pairs()`), see History above.**
3. **Standalone test-adequacy probes.** Give a model a correct, unguarded
   function and ask only for tests. Grade purely by mutation kill rate
   against a small seeded mutation set. Isolates the "can this model write
   a test that can fail" question from correctness entirely -- useful
   because Task 001 currently conflates the two into one score. **Done --
   Task 004 (`load_galaxy_catalog()`), see History above.**
4. **Scope-temptation tasks.** A narrow, well-specified fix sitting next to
   an obviously messy, unrelated piece of code. Scores whether the diff
   stays inside the declared surface when there's a nearby "attractive
   nuisance" to clean up. `scope_discipline` already exists as a rubric
   category; this task type would be the first one designed specifically
   to stress it. **Done -- Task 005 (`src/calc.py`'s provenance attributes,
   tempted by the real `_data_path`/`_results_path` duplication with
   `src/plot.py`), see History above.**
5. **Re-test whether harness matters independent of model.** Every trial in
   the old report series used `opencode`. This repo can now run the same
   model through `opencode`, `claude`, `codex`, `copilot`, or `qwen` --
   worth deliberately holding a model fixed and varying only the harness
   once more than one task exists, to separate harness effects from model
   effects (a distinction the field literature flags as commonly conflated).
   **Not started as a deliberate study, but a real harness confound (not a
   model effect) was already found and fixed the hard way -- see the
   `acceptEdits` entry in History above -- before this item was ever run.**
