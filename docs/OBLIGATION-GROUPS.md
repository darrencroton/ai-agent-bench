# Obligation groups for the 2-slice plan

Purpose: record how `hidden_tests/obligations.yaml` partitions the hidden tests (44 in Slice 1, 20 in Slice 2) into acceptance-obligation groups, why the partition is shaped this way, and how to check it stays honest. This is the definition `tools/dev_check.py` scores `correctness.by_obligation` against.

## Why the partition is the rubric

A slice's correctness score is the equally weighted mean of its groups, each group scored as the fraction of its own nodes that pass. Nothing else weights the tests. So the grouping decision *is* the weighting decision: a group holding one assertion counts exactly as much as a group holding twenty. Groups are therefore balanced by obligation importance, never by test or node count — the same rule `AGENTS.md` states for this bench, and the same failure mode it warns about (a stale or badly balanced map reads as a permanently low ceiling across many runs, discovered much later, not as a loud error now).

## How the groups are shaped, and why

The partition cuts along capability lines rather than function boundaries, so that a single underlying capability is never paid for more than once:

- All input-domain rejections across all four functions form one group, `input_domain_rejections` (19 nodes, one sixth of Slice 1's weight) — rather than being spread across several groups and dominating them by sheer assertion count.
- The pinned scientific values keep their own groups, `pair_fraction_science` and `timescale_and_rate_science`, which together carry a third of Slice 1's weight.
- Each function's *semantic* invariant — pairs cannot exist in a bin with no galaxies (`A07`), `n_galaxies == 0` with non-zero `f_pair` (`B07`) — stays with the science group it belongs to rather than joining the guards, because these require understanding why the invariant holds, not just checking a dtype.
- Persistence/read-back and pipeline orchestration are separate groups: additive-schema correctness and preflight atomicity are genuinely different capabilities, and `E05` (a pre-existing output left byte-for-byte unchanged on every failure path) is one of the harder things in the slice.
- Slice 2 has four groups rather than two, because the reporting contract and the weighted-fit statistics are separate obligations (the plan's own Acceptance Criteria treat them as such, with an amendment note pinning the collapsed-predictor case as in-domain), and because the plan's single stated scientific assertion (`test_E07`) deserves its own weight rather than sitting as one seventh of a bundled group.

Resulting shape: Slice 1 has 6 groups over 44 nodes; Slice 2 has 4 groups over 20 nodes.

One group's id names two things, `consistency_gate_and_reporting_contract` (`check_slope_consistency`'s gate plus `run_merger_rate_validation`'s output contract). That is deliberate, not an unresolved merge: `check_slope_consistency` (`C08`) computes the `consistent` field that `run_merger_rate_validation`'s contract carries, so it is the same obligation's internal mechanism, not a separate one — and split out on its own it would be a single node holding a full fifth of the slice, which is exactly the kind of node-count-driven weighting this partition otherwise avoids.

## `end_to_end_science`

This group is the plan's own scientific assertion, end to end on generated mock data. It carries a full quarter of Slice 2's weight, deliberately, since these are the only tests that exercise the science the slice exists to deliver:

- **`test_E07_end_to_end_science`** — the full pipeline recovers the injected timescale slope for every mass bin with enough usable points.
- **`test_E10_expected_slope_tracks_pinned_alpha`** — plan-pinned alpha (`merger_timescale_alpha = -1.5`, `expected_slope == 1.5`). Catches an implementation that clips alpha at `-1.0` before deriving the timescale while echoing the unclipped config value, invisible at `-0.5`, `-0.7` and the default `-1.0`. Carries no absolute slope tolerance — the mock catalogs are only statistically flat, so a fixed bound would be seed-sensitive; the plan's own contract for "recovered" is the 3-sigma consistency gate that `consistent` already encodes.
- **`test_E11_alpha_response_relation`** — the injected alpha-response relation, `R(b, z) ∝ (1 + z) ** (-alpha)`, holds exactly between two runs sharing the same pair counts. Catches an alpha-dependent multiplicative normalisation error, which moves the intercept but not the log-log slope, so it is invisible to every slope and consistency assertion in the suite.
- **`test_E12_fit_matches_independent_oracle`** — the returned per-bin dict matches an independent fit oracle (slope, unscaled slope error, intercept and exclusion count, recomputed from each bin's own persisted inputs) field-for-field, not just via the `consistent` flag. Catches a swap of `slope_err` and `intercept` when assembling the returned dict, which every pure-fit node and `test_E07` miss entirely. The oracle applies the same 3-sigma consistency gate the implementation does and compares against the returned `consistent` flag directly — an implementation whose slope lands within roughly `1e-6` relative of the gate boundary could in principle disagree with the oracle there; this is the first place to look if this node ever fails an otherwise-correct implementation.
- **`test_E13_alternate_mass_bin_grid`** — the pipeline honours a config-derived, non-default mass-bin grid (`mass_bin_width = 1.0`, 3 bins over `[8.0, 11.0]`) rather than a hardcoded one. Catches a hardcoded default bin count in validation while lower-level functions honour the config.

Per-node weight in this group is 2.5pp of a run's overall score (5 nodes over a quarter of the slice) — an outcome of what the plan's own scientific assertions require, not a target chosen to hit a particular resolution.

**One obligation is deliberately unchecked.** The plan requires the printed console summary, not just the returned dicts, to report the tracked `expected_slope` (plan §"Validation and Failure Conventions"). `test_E10` checks only the returned dicts. Every presentation-insensitive formulation of the printed check either accepts a stale value or rejects a correctly-but-differently formatted one — a labelled inline value (`expected=0.700000`) is straightforward to match, but an unlabelled table column (`f"{expected_slope:11.4f}"`) is not distinguishable from an arbitrary number by regex alone. If this is closed later, it belongs in `consistency_gate_and_reporting_contract` (the reporting-contract group) rather than here, and must be validated against both a tabular and an inline implementation before being trusted.

## Checking it

The partition must stay exhaustive and non-duplicating against the test files themselves — every collected node in exactly one group, no group naming a test that does not exist. `tools/dev_check.py` enforces this at grade time and fails loudly rather than scoring a partial map. Re-run that check after any edit to either the hidden tests or this map; the two drift silently otherwise.

The groups are a calibration judgement, not a frozen contract. If real run data shows two groups moving together across every model, that is evidence to merge them. Record any such change here with the evidence that prompted it.

<!-- markdownlint-disable-next-line MD025 -->
# Obligation groups for the bench-multitask tasks

Purpose: record how `hidden_tests/bench-multitask/obligations-3slice.yaml` partitions that task's hidden tests (20 nodes in Slice 1, 12 in Slice 2, 14 in Slice 3) into acceptance-obligation groups, and why. The same rule governs it as the relative-velocity map above: a slice's correctness is the equally weighted mean of its groups, so the grouping is the weighting. The calibration evidence cited here is recorded in full in `hidden_tests/bench-multitask/README.md`.

**The 2-slice map is the 3-slice map's slices 1-2, verbatim.** `obligations-2slice.yaml` differs from `obligations-3slice.yaml` only in its header comment, its `plan:` (which must name its own task's `plan_file`) and the absence of slice 3. The two plans share Slices 1-2 word for word, so both tasks grade the same hidden tests under the same weights. Edit the two files together; `tests/test_dev_check.py`'s obligation-map test validates both against the real files.

## How the groups are shaped, and why

The partition follows the shape of the plan's own Acceptance Criteria, and it follows what separated the two models in the comparative review: the negative space ("raises", "refuses", "never silently"), and real-git membership rather than path strings. Each group is one obligation a reviewer would check separately. Refusals are not pooled into one "error handling" group: a model that gets resolution right but validation wrong should lose exactly one group's weight.

### Slice 1 (5 groups, 20 nodes)

- **`registry_resolution`** (4 nodes): default, explicit and unknown-id resolution, plus the plan's explicit requirement that the real `relative-velocity` entry reproduce the pre-plan flat keys value for value (read from `77b24c4:policy.yaml`, so it cannot pass by restating a candidate's own edit). The default is a non-first key, so "pick the first entry" fails.
- **`entry_validation_fail_loud`** (6 nodes): missing key, wrong-typed key, non-list measurement bucket, `expected_slices <= 0`, non-string task key, and the acceptance of a null `worktree_root`. Six fail-loud clauses together carry a fifth of the slice, one group, not six, so a validator that is mostly right is not paid six times. Ornith's accepted state fails the `expected_slices: 0` node; both lineages' first attempts failed the non-string-key node with a raw `TypeError`.
- **`repo_membership_real_git`** (6 nodes): same path, registered worktree, unrelated repository, a bare repo's worktree, and the two "cannot determine" cases (non-git configured path, missing configured path) that must raise rather than guess False. Every node uses real `git init`/`git worktree add`/`git clone --bare`; monkeypatched versions of these checks passed broken code in the comparison. Ornith's accepted state fails three nodes: the bare repo, the non-git path and the missing path.
- **`pinned_commit_relocation`** (3 nodes): the function lives in `bench_lib`, reads the line, and raises `BenchLibError` naming the file for each of its two error conditions. The relocation is asserted through `bench_lib` alone. Neither `cohort_run`'s lack of a same-named attribute nor its `CohortRunError` re-raise is asserted, because a thin delegating wrapper there is a legitimate form of the relocation; the README records why.
- **`existing_suite_unchanged`** (1 node, deliberately a fifth of the slice): the plan calls it "the slice's core regression guarantee". It is one expensive node: every pinned test function still defined and the five files passing. A single node carrying a fifth of the weight is the intended outcome, as with relative-velocity's `end_to_end_science`. Breaking the existing suite in a purely additive slice is the most serious Slice 1 failure there is. It is calibrated at Slice-1 commits, not final trees; the README explains why.

### Slice 2 (6 groups, 12 nodes)

- **`task_flag_threading`** (4 nodes): `--task` reaches `dev_check.py` on both `grade_run.py` paths, the git-log walk and the final-attempt fallback. The policy's `default_task` names a task this run does not belong to, so a dropped flag is refused rather than coincidentally right. An unknown task is refused before anything is graded, by both tools. Ornith's first attempt failed both threading nodes: it did not forward the flag.
- **`filename_derivation`** (2 nodes): fixture obligations naming `test_hC.py`/`test_hD.py` lead to those files being copied in and run, with a deliberately failing node proving the outcomes are real; a slice with no test files is refused before any worktree. Ornith's first attempt ran pytest on an empty set instead of refusing; qwen's refused without naming the file.
- **`plan_consistency`** (2 nodes) and **`run_repository_cross_check`** (2 nodes): kept separate because they are distinct checks. One validates a task's internal configuration (obligations file against plan/provenance). The other validates a run's association with a task. The plan itself insists on the distinction ("this only validates a task's own internal configuration, not its association with the specific run").
- **`measurement_per_task`** (1 node): the net-line buckets of a real diff classified by non-default globs. The globs are chosen so `app/` is production and `src/` is unclassified, the reverse of the relative-velocity layout, so a leftover global read cannot reproduce the hand-computed numbers. Ornith's first attempt lost `loc_definition` here.
- **`provenance_task_id`** (1 node): the stamp for both the omitted (non-first default) and the explicit flag.

Both final trees pass Slice 2 in full; both converged after five steers. The groups are weighted for first-attempt separation, which is what the leaderboard ranks: qwen's first attempt scores 11/12 nodes, ornith's 5/12.

### Slice 3 (6 groups, 14 nodes)

- **`task_id_propagation`** (4 nodes): graded and backfilled sources, plus the two cross-slice refusals (value disagreement; graded/backfilled mixture with the stamped value equal to the default, so only the source distinction can refuse).
- **`every_attempt_inspected`** (2 nodes): a middle attempt disagreeing by value, and a middle attempt unstamped between two stamped with the default. qwen (first/final only) fails both. Ornith fails the second: it treats a slice as native when any attempt is stamped. This defect is not listed in the proposal but was confirmed by the comparative review's probes P4, P8 and P9.
- **`malformed_provenance_refused`** (2 nodes): explicit null `task_id` refused, never backfilled; non-mapping provenance a named error, never a raw `AttributeError`. Ornith fails both. Both sheets are single-attempt, so first/final-only inspection cannot excuse a miss.
- **`task_resolved_obligations`** (2 nodes): node outcomes rebuilt from the stamped task's and from the backfilled default task's own `obligations_file`. The fixture node ids exist in no real map, so reading `hidden_tests/obligations.yaml` fails loudly.
- **`policy_flag`** (2 nodes): `--policy` defines `relative-velocity` differently from the bench root's `policy.yaml`, and the passed file must win. A missing file is refused, not silently replaced.
- **`broken_sibling_entry_not_blocking`** (2 nodes): a broken default entry must not block a natively stamped sibling, and the run's own broken entry must be refused naming the task and key. Both red checks fail the first node. qwen does because it fully resolves `default_task` up front; this was not in the proposal's expectation, and the reference fixed it in `c7ec6b3`.

## Checking it

`dev_check.py` enforces exhaustiveness at grade time. `tests/test_dev_check.py::TestObligationMapAgainstRealFiles::test_every_real_test_function_is_mapped_exactly_once` checks every task in `policy.yaml` against its real hidden test files, deriving each slice's directory as `<hidden_tests_dir>/slice<N>`. Re-run the README's calibration recipe after any change to the tests or either map, and record the outcome there.
