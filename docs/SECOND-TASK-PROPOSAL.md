# Proposal: a second bench task built from the multi-task comparison, and what it can and cannot measure

Written 2026-10-01 for a fresh session to build from. Everything a builder needs is either in this document or at a path it names; paths under `archive/`, `.orchestrator/` and `.pm/` are gitignored local artifacts on the operator's machine, not part of a clone. Read it in full before starting.

## 1. The question

The relative-velocity task no longer separates capable models: on the live leaderboard the top four Developer configurations sit at 92.6%, 92.5%, 92.4% and 91.1% first-attempt correctness with overlapping min-max ranges (n = 2–3). The two-model comparison on the multi-task-support plan (`archive/2026-09-30-multi-task-model-comparison/qwen-vs-ornith-developer-assessment.md`) separated the same two local models decisively, on accuracy and far more on quality. The operator asks: can that comparison be turned into a second task in the now-generalised `tasks:` registry, smaller than eight slices, that captures most of what made the comparison informative, so the leaderboard itself does the separating?

Short answer: **yes for the accuracy half, partially for the quality half, and the single highest-leverage step is one the old one-shot bench already proved and the PM bench never carried over.** Sections 2–4 explain; section 5 is the build spec; section 6 the executive summary.

## 2. Where the separation in the comparison actually came from

Decomposing the assessment and its appendices (`appendices/R1`–`R7`, `M1`–`M4`) by what produced each discriminating finding:

| Source of separation | Share of the verdict | Deterministic? | How the bench could capture it |
|---|---|---|---|
| **Negative-space behaviour**: malformed registry, missing `default_task`, non-git configured repo, bare repo, explicit-null `task_id`, corrupt provenance, empty obligations slice, two tasks sharing a repo, broken sibling task. Found by reviewer probes; the plan's own acceptance criteria demanded "fail loudly naming X" for most of them. | Largest share of the *accuracy* difference (R1, R2, R3, R4) | Yes | **Hidden tests that assert the negative space**, weighted as obligation groups. Relative-velocity's 64 hidden nodes are mostly happy-path science assertions; its two rejection groups are the only negative-space ones. |
| **Test quality by mutation**: does the candidate's own suite catch removal of its own fix? Ornith's suite stayed green when `_effective_measurement` was removed; qwen's failed 16 tests. Neither suite caught the reviewer-formula swap. | Decisive in R2, R6 | Yes | **A seeded mutation bank per task, scored as kill rate.** The old bench had exactly this (`coding-bench-original:eval/tasks/*/mutations/`, a `sitecustomize.py` that monkey-patches one behaviour per `MUTATION=<id>` run and reruns the candidate's own tests). It is absent from this repo's `tools/`. |
| **Plan fidelity**: ornith silently swapped the reviewer standing formula; qwen added two unauthorised checks under recorded steers. | R6, R7 | Partly | Hidden tests pin the formula (hand-computed fixtures); scope discipline (already measured) catches surface drift; silent reinterpretation inside the surface is only catchable by a test that encodes the contract. |
| **Comment and docstring accuracy, history narration, commit hygiene**: stale `policy.yaml` sentences 8 vs 20; plan-slice citations in production code 2 vs 14; `steer-attempt` commit subjects 4 vs 29. | R1, R5, R7 | Yes, crudely | A **hygiene census**: counts of policy-listed narration tokens in added comment lines, subject-line length and process labels over the trial branch, added-comment-to-code ratio. Descriptive columns, never scored, like ΔLOC today. |
| **Design and readability judgement**: function size and cohesion, parameter sprawl, JSON shape self-containment, anchor over-engineering. | R2, R4, R5 | No | Only as a **labelled subjective column** from a fixed read-only reviewer configuration with a fixed rubric, exactly as PM's reviewer ratings are surfaced today. Never blended. Repeatability is the known cost. |
| **Process under supervision**: 22 vs 39 steers, 2 vs 10 floor failures, 3 vs 18 nudges. | M4 | Yes | Attempts and steers are already measured. Floor-failure count and nudge count are derivable from `events.jsonl` and would be two cheap new descriptive columns. The reviewer-panel confound must be controlled by holding the Reviewer configuration fixed across a cohort. |

Two conclusions follow. First, the deterministic part of the separation is reproducible inside the bench's existing rules: hidden tests for the negative space, plus a mutation bank for test quality, plus a few descriptive census columns. Second, the 113-versus-94 quality verdict as a whole is not reproducible deterministically; roughly a third of it is reader judgement, and the bench's principle is that such a signal is surfaced, labelled, and never blended. The realistic target is a leaderboard that separates models on correctness again *and* carries a test-quality column that spans the range, with judgement as an optional labelled extra.

## 3. What the old bench already knew

`coding-bench-original` (head `62fb146`) is this repository's one-shot predecessor. Three documents there are directly relevant and should be read by the builder:

- `docs/V3-DISCRIMINATION-ASSESSMENT.md`: diagnosed in 2026-09-06 that correctness saturated at 88–100% for every model on every task, including the one task built to require a design decision. Its recommendations: shift weight to test adequacy (already discriminating), add a deterministic code-quality category from `health.py`, and build categorically different task shapes (debugging/root-cause first, performance-at-scale second) rather than "another less-pinned spec task".
- `docs/EVAL-CONSOLIDATION-PROPOSAL.md`: the decision that produced this PM bench. Its scoring table made **mutation kill rate the score** ("the only category spanning 0–100% in 207 one-shot trials"), correctness a gate, structural quality a second score, lint and scope flags, and retired judged readability. The transplant experiment graded fourteen relative-velocity PM branches through the Task 001 instruments unmodified and found the 73-mutation bank spread their test suites from 0% to 93%.
- `docs/DESIGN.md` "Task backlog" and "Provenance of the mutation gate": the five one-shot tasks (001 feature, 002 design decision, 003 fail-loud validation, 004 test adequacy, 005 scope temptation), each with `spec.md`, `meta.yaml`, `hidden_tests/`, `reference_solution/` (and for 004/005 `mutations/mutation_list.txt` plus `mutations/sitecustomize.py`, and degenerate-control or weak-baseline suites that fail the mutation gate by design).

The PM bench kept hidden tests as the ranking basis and dropped the mutation gate. The relative-velocity substrate is byte-identical to Task 001's frozen substrate, so the 73-mutation Task 001 bank applies to every relative-velocity run already graded. **Porting the mutation gate into `dev_check.py` as a generic, policy-driven per-task measurement is therefore the cheapest way to break the clustering on the existing task, without a new task, and it is also the mechanism the new task needs.** It is a bench-mechanism plan (one new per-task key, one new measurement, one new leaderboard column), not a task.

## 4. Is the second task viable as described?

**Yes.** The multi-task plan is a good second-task shape for exactly the reason the old assessment predicted: it is not formula transcription. Its acceptance criteria are behavioural and largely negative-space ("raises BenchLibError naming the task id and the configured ids", "refuses loudly", "never silently defaults"), its correctness ceiling is high, and the two completed implementations plus the reviewed fix-up give three calibration points no other task has. The constraints and caveats:

1. **Eight slices is too many; four is right.** Plan Slices 1, 2, 3 and 5 are the dependency chain and the grading-correctness core. Slices 4 (cohort_run), 6 (reviewer scoping), 7 (cross-task standing) and 8 (docs) can be dropped without breaking 1–3 and 5, provided the plan text is re-cut (see 5.3). Cost: the full eight-slice plan took about 37 developer-active hours for qwen (the ornith run, at about 46, is not a fair basis: a larger panel, outages and stalls); Slices 2 and 5 were the heaviest. Expect about 20 hours per trial for the four-slice cut and about 13 for the three-slice cut recommended in section 10, so a cohort of five models at n = 3 is roughly eight to nine days of Mac Studio time on the three-slice form.
2. **The substrate is this repository itself at `77b24c4`.** That is unusual but mechanically fine: `setup` makes a worktree of whatever `repo` the task configures; the Developer edits `tools/` and `tests/`; `dev_check` copies the task's hidden test files into the worktree's `tests/` and runs pytest there. The plan must be committed inside the substrate at the pinned commit (relative-velocity's plan lives in the relative-velocity repo the same way), so the substrate is a dedicated clone of this repository at `77b24c4` plus one commit adding the re-cut plan; that commit is the pin. Two caveats: the substrate copy carries relative-velocity's `hidden_tests/` (already public in this repository, so not a new leak, but note it), and the Developer can read `AGENTS.md`, which states the fail-loud rules the hidden tests assert; that is fair, since the plan's criteria state them too.
3. **Hidden tests must survive implementer freedom.** The plan lets the implementer choose helper names. Tests must therefore target only what the plan itself names (`bench_lib.resolve_task`, `bench_lib.repo_belongs_to_task`, `bench_lib.parse_pinned_plan_commit`, the `--task` flags, `provenance.task_id`, `task_id`/`task_id_source` on the report, the partitioned `leaderboard.json`) and observable CLI behaviour (exit codes, error text naming the id/path/key, written files). No test may import a helper the plan did not name. Both candidate branches satisfy this: every plan-named interface exists in both.
4. **Calibration is unusually strong.** The reference implementation is `main` at `310ab63` (every hidden test must pass there). The two red checks are `multi-task-support` at `3838855` (qwen) and `multi-task-support-2` at `f3ff079` (ornith): a well-designed suite fails each on exactly its known defects (section 5.5) and nothing else. This mirrors the red-check discipline recorded in `docs/reference-impl/README.md`.
5. **The quality half needs the mutation gate.** Without it, the new task separates on correctness only. With it, the candidate's own test suite is scored by how many seeded mutants it kills, which is where the two models differed most (R2). The mutation bank for this task is seeded from the defect catalogue: each confirmed defect class becomes a mutant of the reference implementation (for example: drop the registry-shape check; make `repo_belongs_to_task` return False for a non-git configured path; compare the whole provenance dict; inspect only first and final attempts). A candidate's suite that would have caught these kills them.
6. **Hold the reviewer configuration fixed per cohort.** Half the process-metric gap in M4 is confounded by ornith facing a newer, larger panel. The bench cannot control PM, but the operator can: one Reviewer configuration for every trial of a cohort, recorded.

What it will not do: it will not reproduce a reader's judgement of design quality, and it should not try to. If the operator wants that signal, section 5.7 describes the labelled-subjective form that fits the house rules.

## 5. Build specification for the fresh session

### 5.1 Order of work

1. **Mechanism first: port the mutation gate** as a generic per-task measurement (section 5.6). Apply the existing Task 001 bank to relative-velocity and regrade; the new column is additive, correctness is unchanged, so existing sheets stay comparable. This alone should re-separate the current cohort.
2. **Then the second task** (5.2–5.5, in the 3-slice form section 10 recommends): re-cut plan, hidden tests, obligations map, mutation bank, calibration, registry entry, README task table.
3. **Then, optionally**, the descriptive hygiene census and process columns (5.7), and last the labelled quality panel.

Each step is its own frozen plan run through the normal plan → implement → audit → review → commit chain. Do not fold them into one plan.

### 5.2 Registry entry for the new task

A `tasks:` entry in `policy.yaml` (every key `bench_lib.resolve_task` requires; `tools/bench_lib.py` `_TASK_ENTRY_REQUIRED_KEYS` is the authority):

```yaml
  bench-multitask:
    repo: substrate/ai-agent-bench-task          # dedicated clone, see 5.3
    branch_prefix: pm-eval-mt
    worktree_root: null
    plan_file: docs/plans/MULTI-TASK-PLAN-4SLICE.md   # relative to the target repo
    provenance_file: docs/MULTI-TASK-PLAN-4SLICE.provenance.md   # relative to this bench root
    hidden_tests_dir: hidden_tests/bench-multitask
    obligations_file: hidden_tests/bench-multitask/obligations.yaml
    expected_slices: 3          # 4 if the Slice-5 leaderboard slice is kept, see section 10
    measurement:
      production_paths: ["tools/**/*.py"]
      test_paths: ["tests/**/*.py"]
      doc_paths: ["*.md", "docs/**/*.md"]
```

`policy.yaml` itself falls in the unclassified bucket under these globs, which is correct: it is configuration, and the ΔLOC on it is not production code. `python_interpreter` must have `pyyaml` installed, because the hidden tests import the substrate's tools.

### 5.3 The re-cut plan

Source: `archive/2026-09-30-plan-retired/multi-task-support-plan.md` (the frozen eight-slice original; the PM-amended nine-slice variant is on `multi-task-support-2` at `docs/plans/multi-task-support-plan.md`). Produce `MULTI-TASK-PLAN-4SLICE.md`, committed into the substrate clone on top of `77b24c4`:

| New slice | From original | Keep | Change |
|---|---|---|---|
| 1 | Slice 1 | All: `tasks:` schema, `resolve_task`, `parse_pinned_plan_commit` relocation, `repo_belongs_to_task` | None |
| 2 | Slice 2 | All: `dev_check`/`grade_run` task-aware, filename derivation, plan/plan_pin check, run-repo cross-check, per-task measurement, provenance `task_id` | Drop the sentence deferring `model_report`'s obligations loading to Slice 3 only if Slice 3 is kept (it is) |
| 3 | Slice 3 | All: `task_id`/`task_id_source`, backfill, task-resolved obligations, `--policy` | None |
| 4 | Slice 5 | Developer-table partitioning, `task_id` required key, per-task `expected_slices`, `## Task:` sectioning, provenance consistency scoped per task **and to the three hash keys** | Remove the "reviewers stay global until Slice 6" asymmetry paragraph (reviewers simply stay global, stated as a non-goal); remove cross-references to Slices 4, 6, 7, 8; fold the nine-slice variant's Slice 9 fix into this slice's Intended Change so the latent whole-dict comparison is in-contract |

Also: delete the "Implementation Profiles"/"Slice Batches" references to dropped slices; keep "How rigid this plan is meant to be" and "Migration approach" verbatim (they are what made the task fair); update the Next Chat Prompts' dependency sentence. Freeze it, record its sha256 in the provenance file, and never edit it again; a defect found later is documented in the task's reference README exactly as `docs/reference-impl/README.md` does today.

Known plan defects to document up front rather than re-discover (from both runs' records, `archive/HANDOFF-multi-task-support.md` §5 and `archive/HANDOFF-multi-task-support-2.md`): the Slice 2 authorised-components list omits the run-repository and plan-identity checks the acceptance criteria imply; `policy.yaml` comment staleness has no authorised slice (acceptable for a graded task, since comments are not scored); the Slice 3 echo breaking the pre-partitioning leaderboard is resolved by folding Slice 9 into new Slice 4.

### 5.4 Hidden tests and obligation groups

Layout: `hidden_tests/bench-multitask/slice{1..4}/test_hA.py` (and `test_hB.py` where a slice needs two files). `dev_check` copies them into the worktree's `tests/`, so node ids are `tests/test_hA.py::test_name`; node matching is exact set equality, so no `parametrize` unless every generated id is listed. One slice per pytest invocation. `obligations.yaml` carries `plan:` (the plan's repo-relative path) and `plan_pin:` (the substrate commit); `dev_check` refuses to grade if either disagrees with the task entry.

Design rules, derived from what separated the models:

- **Assert the negative space first.** For every "raises/refuses/never silently" clause in a slice's acceptance criteria, one test that provokes it and asserts the error type, exit code, and that the message names the concrete id, key or path. These are the tests the relative-velocity suite lacks.
- **Test through the plan's named surface only** (section 4.3). For CLI behaviour, invoke `main([...])` or a subprocess and assert exit code and stderr text, never internals.
- **Use real git** for every membership and worktree claim (throwaway repos with real `git worktree add`), as the plan itself demands; the comparison showed monkeypatched versions of these tests passed broken code.
- **Pin formulas with hand-computed fixtures** (literal expected values), because the one formula deviation found was invisible to every fixture where two readings coincided.
- **Balance groups by obligation, not node count**, per `AGENTS.md`. A first cut, four to six groups per slice:
  - Slice 1: `registry_resolution` (default, explicit, unknown, available-ids named), `entry_validation_fail_loud` (missing key, wrong type, non-string key, `expected_slices` ≤ 0, nullable `worktree_root`), `repo_membership_real_git` (same path, registered worktree, unrelated path, not-a-repo configured path, bare repo), `pinned_commit_relocation`, `existing_suite_unchanged`.
  - Slice 2: `task_flag_threading` (`--task` reaches `dev_check` on both `grade_run` paths; unknown task refused before grading), `filename_derivation` (fixture obligations naming `test_hC.py` reaches the pytest argv; zero-group slice refuses before any worktree), `plan_consistency` (plan/plan_pin mismatch named), `run_repository_cross_check` (trial worktree accepted, foreign worktree refused by name), `measurement_per_task` (classification identical to the flat baseline on a real diff; `loc_definition` still reaches ΔLOC), `provenance_task_id`.
  - Slice 3: `task_id_propagation` (graded/backfilled), `every_attempt_inspected` (middle-attempt disagreement, stamped/unstamped mix), `malformed_provenance_refused` (explicit null, non-mapping), `task_resolved_obligations` (fixture path actually read), `policy_flag`, `broken_sibling_entry_not_blocking`.
  - Slice 4: `partition_isolation` (two-task fixture, no leakage in any per-task number), `missing_task_id_refused`, `per_task_expected_slices`, `provenance_scoped_to_hash_keys` (differing echo tolerated, differing hash refused), `single_task_numeric_parity` (hand-pinned numbers), `markdown_sectioning` (every heading under its `## Task:`).

### 5.5 Calibration recipe

Three worktrees, as in the comparison: reference `main@310ab63`, red check A `multi-task-support@3838855`, red check B `multi-task-support-2@f3ff079`. Run each slice's hidden tests in each. Required outcome:

- Reference: every node passes.
- A fails exactly: whole-dict provenance comparison (Slice 4 group `provenance_scoped_to_hash_keys`), first/final-only attempt inspection (Slice 3 `every_attempt_inspected`), and nothing in Slices 1–2.
- B fails exactly: explicit-null `task_id` backfilled and non-mapping provenance leaking (Slice 3 `malformed_provenance_refused`), `repo_belongs_to_task` returning False for a missing or non-git configured path and for a bare repo's worktree (Slice 1 `repo_membership_real_git`), `expected_slices` ≤ 0 accepted (Slice 1 `entry_validation_fail_loud`), broken default entry blocking a sibling run's report (Slice 3 `broken_sibling_entry_not_blocking`).

A test that fails the reference is wrong. A test that passes both red checks is not discriminating and needs a reason to exist. Record the outcome in `hidden_tests/bench-multitask/README.md`, the way `docs/reference-impl/README.md` records relative-velocity's.

### 5.6 The mutation gate as a generic measurement

Port, do not reinvent: `coding-bench-original:eval/tasks/004-catalog-loader-test-adequacy/mutations/sitecustomize.py` documents the mechanism and its hard-won constraints (patch public names post-import, match modules by basename so import style does not matter, one mutation per `MUTATION=<id>` run, never edit a trial file). Design for this repository:

- New per-task key `mutations_dir` (relative to the bench root) holding `mutation_list.txt` and `sitecustomize.py`; validated by `resolve_task` like every other path key.
- `dev_check` gains one measurement: for each mutation id, run the candidate's **own** test suite (the task's `test_paths`) in the grading worktree with `PYTHONPATH` prepended by `mutations_dir` and `MUTATION=<id>`; a mutant is killed if the suite fails. Record `killed`, `survived`, `errored` per id and the kill rate on the attempt entry. Subprocess timeout from policy. An errored mutation is recorded as errored, never as killed.
- `model_report` passes it through; `leaderboard` renders a `Test kill rate` column with the mean [min-max], n convention, descriptive beside correctness; `aggregate_model` is unchanged otherwise. Deterministic first: it is a measured fraction, so it may stand as its own column; whether it ever joins the ranking basis is a later, separate decision.
- Relative-velocity's bank: `coding-bench-original:eval/tasks/001-merger-rate-feature/mutations/` (73 mutants, provenance in that branch's `docs/DESIGN.md`). The substrates are byte-identical, so it applies as is; vendor it under `hidden_tests/relative-velocity-mutations/` or similar with provenance.
- The new task's bank: seed from section 5.5's defect list plus the fix-up contract (`.orchestrator/review-input/multi-task-fixup/fixup-contract.md`): one mutant per confirmed defect class, applied to the plan-named functions by monkey-patching, so it works on any implementer's internals.

### 5.7 Optional descriptive and subjective columns

Only after 5.1–5.6, each as its own small plan:

- **Hygiene census** (deterministic, descriptive): counts over the attempt's diff of added comment/docstring lines containing policy-listed narration tokens (`steer`, `round N`, `Slice N`, `today`, `legacy`, `TODO`), commit subjects over 72 characters and containing process labels on the trial branch, added-comment-to-code ratio. Policy carries the token list. Never scored.
- **Process columns** (deterministic, descriptive): floor-failure count and PM nudge count per run from `events.jsonl`, next to the existing attempts/steers.
- **Quality panel** (subjective, surfaced): a read-only reviewer configuration fixed per cohort, run post-hoc against the accepted commit with a fixed five-dimension rubric (correctness beyond tests, design, readability/docs, tests, contract discipline; 1–5 each), stored like PM's reviewer judgments and rendered in its own labelled table. The orchestrator skill already provides the launch mechanism. Record model, effort and prompt hash on every rating. This is the only way to carry the reader-judgement part of the comparison into the leaderboard without violating "deterministic first".

### 5.8 Assets and paths

- Assessment and appendices: `archive/2026-09-30-multi-task-model-comparison/` (`qwen-vs-ornith-developer-assessment.md`, `appendices/R1`–`R7`, `M1`–`M4`; the defect catalogue is in the assessment's Findings §1 tables).
- Run records: `archive/HANDOFF-multi-task-support.md`, `archive/HANDOFF-multi-task-support-2.md`; PM runs `.pm/runs/20260920T123917Z-bb7f71`, `.pm/runs/20260924T065311Z-987501`, `.pm/runs/20260928T123743Z-f3a533` (read-only; `run.json`/`events.jsonl` under `.git/pm/<run_id>/`).
- Frozen original plan: `archive/2026-09-30-plan-retired/multi-task-support-plan.md`; amended nine-slice copy on `multi-task-support-2`.
- Reference and red checks: `main@310ab63`, `multi-task-support@3838855`, `multi-task-support-2@f3ff079`; merge base and substrate pin `77b24c4`.
- Fix-up contract and panel reviews: `.orchestrator/review-input/multi-task-fixup/`, `.orchestrator/runs/delegates-20260930-182032-98380/`.
- Old bench: branch `coding-bench-original@62fb146`: `docs/DESIGN.md`, `docs/V3-DISCRIMINATION-ASSESSMENT.md`, `docs/EVAL-CONSOLIDATION-PROPOSAL.md`, `eval/tasks/001…005/` (specs, hidden tests, reference solutions, mutation banks, weak baselines).
- Bench mechanics to respect: `AGENTS.md` (boundaries, obligation partition rule, re-validate after any test or map change, one slice per pytest invocation), `tools/dev_check.py` (`hidden_test_filenames`, `run_hidden_tests`, `validate_obligations_against_task`, `check_run_belongs_to_task`, `check_plan_matches_task`), `tools/bench_lib.py` (`_TASK_ENTRY_REQUIRED_KEYS`, `resolve_task`), `docs/reference-impl/README.md` (the validation-record pattern to copy).

### 5.9 Open decisions for the operator

1. Dedicated substrate clone of this repository for the new task (recommended) versus a separate throwaway repository with a different name. The former is simplest; the self-reference is mechanical, not conceptual.
2. Whether the mutation kill rate stays descriptive or becomes a second ranking column. The old bench's conclusion was to make it the score; this bench's rule is deterministic-first and surfaced-never-blended, which a separate column satisfies either way.
3. Whether to build the quality panel at all. It is the only path to the design-judgement signal and also the only one with a repeatability cost.
4. Cohort design: repeats per model (`policy.yaml` `repeats`), the fixed Reviewer configuration, and whether to also PM-ify the old bench's debugging/root-cause backlog task as a third shape later.

## 6. Operator decisions recorded (2026-10-01)

1. **Substrate**: a dedicated clone of this repository at `77b24c4` plus one commit carrying the re-cut plan; that commit is the pin.
2. **Mutation kill rate is a second ranking column**, provided it can be measured with confidence (section 8 states what "with confidence" requires). Two independent rankings, never combined: the first-submission table gains a `Rank by test kill rate` beside `Rank by observed mean`, and cross-task standing gains a parallel developer standing on kill rate. Correctness remains the primary rank; the glossary says so.
3. **Quality panel**: explained in section 7; deferred, build last and only if the deterministic columns leave a gap the operator still cares about.
4. **Cohort design**: the bench works with whatever repeats it is given and always shows n and ranges; three repeats is the operational minimum. The Reviewer configuration is fixed per cohort in intent but may be swapped mid-cohort when a model becomes unavailable; the per-review identity is already recorded in `run.json` and surfaced per row, so the error this introduces is visible rather than hidden.
5. **One task at a time.** The goal is one plan that discriminates and evaluates reliably. The new task is a candidate for that role and is assessed on its own before any third shape is considered; the debugging/root-cause idea stays in the old bench's backlog as a next step only if the pipeline still needs improving afterwards.

What the bench evaluates, stated once so the "single plan" goal is judged on the right axis: the Developer seat's **implementation** of a frozen plan, for accuracy as the plan defines it and for quality (legibility, robustness, tests, discipline). The scientific reasoning lives in writing the plan, which a strong frontier model does with the `implementation-plan` skill; the bench's plans are deliberately artificial instruments built to test implementation, not to do science. On that axis the new task is fully on target: its plan is exacting about what "accurate" means and its negative space is where implementations differ. Relative-velocity remains alongside it as a second instrument with a different flavour, and the two together, through cross-task standing, are the ranking until one task alone proves to discriminate reliably.

## 7. The quality panel, explained

The comparison's quality verdict came from six Opus reviewers each reading one plan area of both branches with a fixed brief and scoring five dimensions 1–5: correctness beyond the acceptance criteria, design, readability and docs, tests, contract discipline. A "quality panel" in the bench would be the same thing made routine: after a run is accepted, a read-only reviewer configuration fixed for the cohort (one tool, model and effort, launched through the `orchestrator` skill as a read-only delegate) reads the accepted commit against the frozen plan and returns those five scores with `path:line` evidence. The scores would be stored like PM's own reviewer judgments and rendered in their own labelled table, headed as a model's judgement, never entering correctness, kill rate or any rank.

Why it is a decision rather than an obvious addition: it is the only way to carry the design-judgement third of the comparison into the leaderboard, but it costs one reviewer session per accepted run, its scores are not repeatable the way a test is (the same reviewer can score the same diff differently on two days), and the old bench measured a same-family bias in judged readability (scores tracked the harness family of the reviewer). Those costs are why this bench's rules keep such signals surfaced and unblended. Build it last, if at all; the deterministic columns in sections 5.6 and 5.7 cover most of what it would add.

## 8. Measuring kill rate with confidence

For the second ranking column to deserve the name, the bank must satisfy three checkable properties, each recorded in the task's reference README as relative-velocity's `docs/reference-impl/README.md` records its red checks:

- **Every mutant is detectable**: the reference implementation's own test suite (for the new task, `main@310ab63`'s `tests/`) kills every mutant. A mutant no correct suite can kill is an equivalent mutant and is removed.
- **The bank discriminates**: a deliberately weak suite (the old bench's `weak_baseline/` and `degenerate_controls/` pattern) kills few. Without this, a high kill rate is a property of the bank, not the suite.
- **Mutants are behavioural and import-style independent**: each monkey-patches one plan-named public function post-import (the `sitecustomize.py` design, modules matched by basename), so a candidate's internal naming cannot evade or accidentally dodge it.

The old bench's "Systematic mutation-integrity audit" (`coding-bench-original:docs/DESIGN.md`, History) is the procedure to follow; its Task 001 bank already passed it. Kill rate is scored on the **first attempt** for the ranking column, matching correctness; the final attempt's kill rate is shown as a descriptive companion.

## 9. Evidence: which criteria correlate in the ranking

Spearman rank correlations across the eight ranked configurations of the live relative-velocity cohort (n = 8, so indicative, not conclusive), against first-attempt correctness:

| Column | rho | Reading |
|---|---|---|
| Final (supervised) correctness | +0.83 | Supervision compresses gaps but barely reorders; the supervised-outcome table adds little ranking information. |
| Attempts per slice | -0.86 | Process metrics are largely redundant with first-attempt rank. |
| Steers | -0.81 | Same; steers and attempts correlate at +0.98 with each other. |
| PM Developer rating | +0.60 (n = 6) | Moderate agreement with the deterministic rank. |
| Gain (pp) | -0.33 | Weak and inverse: weaker first attempts gain more. |
| Code ΔLOC, ΔCC | -0.17, -0.36 | Essentially independent descriptive axes. |
| PM elapsed | +0.04 (n = 7) | Independent. |

Within the two-model comparison, the per-area reviewer scores tell the same story: the correctness and tests dimensions separated the models in every area, design separated in four of six, docs in five, and the one area where correctness tied (Slice 5, leaderboard partitioning) was the most expensive slice in both runs.

Consequences for plan length:

- The ranking rests on first-attempt correctness, and the proposed second rank on first-attempt kill rate. Neither depends on how many supervised rounds follow, so slice count buys ranking resolution only through **how many distinct obligations the hidden tests assert** and **how many independent first attempts are averaged**. With three repeats per model, averaging across slices matters less than it did at n = 1.
- Process columns (attempts, steers) can be dropped from any ranking consideration; they are already descriptive only.
- The supervised-outcome table costs the most wall-clock (every steer round) and adds the least rank information. The panel breadth the operator chooses per round is therefore as large a lever on trial time as slice count.

## 10. Plan-length variants, rated against the four-slice baseline

Time estimates scale the qwen run's per-slice round counts (S1 2, S2 6, S3 3, S5 6 of 31 rounds over about 37 developer-active hours, so about 1.2 h per round); the ornith run is excluded because its wall-clock was inflated by a larger panel and by backend outages and stalls that are not properties of the plan. The figures are for a local model under a full drift-audit plus three-seat review panel on every round; a lighter panel shortens every variant roughly in proportion.

| Variant | Slices (original numbering) | Hidden-test obligations retained | First-attempt separation expected | Kill-rate surface | Time per trial (local) | Rating vs 4-slice |
|---|---|---|---|---|---|---|
| **4-slice** | 1, 2, 3, 5 | all 22 groups in section 5.4 | reference | `bench_lib`, `dev_check`/`grade_run`, `model_report`, `leaderboard` tests | ~20 h | 100% |
| **3-slice** | 1, 2, 3 | 17 groups (drops Slice 5's six) | ~90%: Slice 5 was the one area where the two models **tied** on correctness; its separation was design and test quality, which the kill-rate column recovers in part | three of four test surfaces | ~13 h | **~90% of separation at ~65% of time: recommended baseline** |
| **2-slice** | 1, 2 | 11 groups | ~75%: loses Slice 3's fail-loud discriminators (null `task_id`, every-attempt inspection, broken sibling entry) which separated the models at 4 vs 3 and cost only two steers each | two surfaces, including the richest (`dev_check` tests, where mutation resistance differed 16 to 0) | ~9–10 h | ~75% at ~50%; the fast fallback if 3-slice trials still exceed budget |
| **1-slice** | 1 + 2 merged | 11 groups in one slice | ~65%: same obligations as 2-slice but one first attempt per run, so per-run variance rises and the plan loses the inter-slice "existing behaviour unchanged" regression backstop and any multi-slice PM dynamic; a merged High slice is also harder to steer atomically | two surfaces | ~8 h | ~65% at ~40%; not recommended |

Why Slice 5 is the right cut rather than Slice 3: Slice 5 had the highest round count in both runs (anchor-uniqueness saga, 5 and 8 rounds), the two models tied on its correctness, and its remaining discriminators (JSON shape, heading nesting, numeric parity) are design and rendering judgements better carried by the kill-rate column and, if built, the quality panel. Slice 3 is cheap and its discriminators are exactly the negative-space class that separates models.

**Recommendation: build the 3-slice variant** (original Slices 1, 2, 3; `expected_slices: 3`), with the hidden-test groups of section 5.4 for those slices and the mutation bank seeded from their defect classes. Keep the 2-slice cut as the documented fallback: it is the same plan with Slice 3 removed, so switching later costs only the plan re-freeze and the registry entry, not new tests. Fold the Slice 9 provenance fix nowhere, since the leaderboard slice is dropped; the bench's own `leaderboard.py` already carries it.

Section 5.3's table and 5.5's calibration list apply with Slice 4 (original 5) removed; the red-check expectations for qwen then reduce to the first/final-only attempt inspection in Slice 3, and ornith's remain as listed.

## 11. Executive summary

- The comparison separated the models for two reasons the bench can reproduce deterministically: hidden-style checks of the **negative space** and **mutation-style checks of the candidate's own tests**. Reader judgement of design is the third reason and can only be a labelled column (the "quality panel", section 7), built last if at all.
- The old one-shot bench reached the same diagnosis in September, made mutation kill rate the score, and left a 73-mutation bank for the exact relative-velocity substrate; it was never ported to the PM bench. **Port it first** as a generic per-task measurement and a second ranking column, with the confidence checks in section 8, and regrade relative-velocity.
- **A second task from the multi-task plan is viable.** Correlations in the live cohort show the ranking rests on first-attempt correctness alone, with attempts, steers and the supervised table largely redundant, so slice count buys resolution only through distinct obligations and averaged first attempts. On that basis the **3-slice cut (original Slices 1, 2, 3)** keeps about 90% of the separation at about 65% of the time (about 13 developer-active hours per trial on the qwen basis) and is the recommended build; 2-slice is the documented fast fallback; 1-slice is not recommended.
- Decisions recorded: dedicated clone of this repository as substrate; kill rate as a second rank; quality panel deferred; three repeats minimum with reviewer swaps tolerated and visible; one task at a time, with the new task judged on its own as a candidate single plan for what the bench evaluates: implementation accuracy as the plan defines it, and implementation quality.
