# Obligation groups for the 2-slice plan

Purpose: record how `hidden_tests/obligations.yaml` partitions the hidden tests (44 in Slice 1, 20 in Slice 2) into acceptance-obligation groups, why the partition is shaped this way, and how to check it stays honest. This is the definition Tool 1 (`tools/dev_check.py`) scores `correctness.by_obligation` against.

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

The partition must stay exhaustive and non-duplicating against the test files themselves — every collected node in exactly one group, no group naming a test that does not exist. Tool 1 enforces this at grade time and fails loudly rather than scoring a partial map. Re-run that check after any edit to either the hidden tests or this map; the two drift silently otherwise.

The groups are a calibration judgement, not a frozen contract. If real run data shows two groups moving together across every model, that is evidence to merge them. Record any such change here with the evidence that prompted it.
