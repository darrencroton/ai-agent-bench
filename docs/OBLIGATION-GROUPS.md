# Obligation groups for the 2-slice plan

Purpose: record how `hidden_tests/obligations.yaml` partitions the 61 hidden tests into acceptance-obligation groups, why that partition differs from Task 001's, and how to check it stays honest. This is the definition Tool 1 (`tools/dev_check.py`) scores `correctness.by_obligation` against.

## Why the partition is the rubric

A slice's correctness score is the equally weighted mean of its groups, each group scored as the fraction of its own nodes that pass. Nothing else weights the tests. So the grouping decision *is* the weighting decision: a group holding one assertion counts exactly as much as a group holding twenty. Groups are therefore balanced by obligation importance, never by test or node count — the same rule `main`'s `AGENTS.md` states for the one-shot bench, and the same failure mode it warns about (a stale or badly balanced map reads as a permanently low ceiling across many runs, much later, not as a loud error now).

## What changed from Task 001, and why

The redundancy motivating the old 3-slice plan's collapse into two slices was real and present in Task 001's map — several groups dominated by one underlying capability. Task 001's `meta.yaml` has eight `acceptance_obligations` groups in total, six covering Slice 1 content and two covering Slice 2 content; checking that six/two split against that redundancy found exactly that:

- **Input-validation guards were spread across three groups and dominated two of them.** `load_pair_counts_rejections` was entirely guards; `pair_fraction_core` was 6 guards to 3 science assertions; `merger_timescale_and_rate_conversion` was 5 guards to 8. Under equal group weighting that gave "reject bad input" roughly a third of Slice 1's correctness weight, against a much smaller share for the pinned scientific values. That is the same capability being paid for three times — precisely the redundancy the 3-slice plan's rho +0.68 finding exposed.

The re-partition fixes this by cutting along capability lines rather than along function boundaries:

- All input-domain rejections across all four functions become one group, `input_domain_rejections` (19 nodes, one sixth of the weight instead of roughly a third).
- The pinned scientific values keep their own groups, `pair_fraction_science` and `timescale_and_rate_science`, which together now carry a third of Slice 1.
- Each function's *semantic* invariant — pairs cannot exist in a bin with no galaxies (`A07`), `n_galaxies == 0` with non-zero `f_pair` (`B07`) — stays with the science group it belongs to rather than joining the guards. These require understanding why the invariant holds, not just checking a dtype.
- Persistence/read-back and pipeline orchestration stay separate, as in Task 001: additive-schema correctness and preflight atomicity are genuinely different capabilities, and `E05` (a pre-existing output left byte-for-byte unchanged on every failure path) is one of the harder things in the slice.

Slice 2's two Task 001 groups became four, for the opposite reason — they were too coarse rather than redundant. `redshift_evolution_fit_and_consistency` bundled the weighted-fit statistics with the malformed-versus-excluded data distinction, which the plan's own Acceptance Criteria treat as separate obligations (its amendment note exists specifically to pin the collapsed-predictor case as in-domain). `validation_reporting_and_e2e` bundled the reporting contract with the end-to-end science, which put the plan's single stated "scientific assertion of the plan" (`E07`) at one seventh of the group it sat in. It now shares a group only with `E09`, and that group carries a full quarter of the slice — two nodes, deliberately, because they are the only tests that exercise what the slice exists to deliver.

Resulting shape: Slice 1 has 6 groups over 44 nodes, Slice 2 has 4 over 17.

One group's id names two things, `consistency_gate_and_reporting_contract` (`check_slope_consistency`'s gate plus `run_merger_rate_validation`'s output contract). That is deliberate, not an unresolved merge: `check_slope_consistency` (`C08`) computes the `consistent` field that `run_merger_rate_validation`'s contract carries, so it is the same obligation's internal mechanism, not a separate one — and split out on its own it would be a single node holding a full fifth of the slice, which is exactly the kind of node-count-driven weighting this partition otherwise avoids.

## Checking it

The partition must stay exhaustive and non-duplicating against the test files themselves — every collected node in exactly one group, no group naming a test that does not exist. Tool 1 enforces this at grade time and fails loudly rather than scoring a partial map. Re-run that check after any edit to either the hidden tests or this map; the two drift silently otherwise.

The groups are a calibration judgement, not a frozen contract. If real run data shows two groups moving together across every model — the rho +0.68 signature — that is evidence to merge them, exactly as it was for the 3-slice plan. Record any such change here with the evidence that prompted it.

## 2026-09-15: fixed `test_E09` discriminating on float format, not capability

`hidden_tests/slice2/test_hB.py`'s `test_E09_expected_slope_tracks_nondefault_alpha` closed with `assert re.search(r"expected(?:_slope)?\s*=\s*\+?0\.7\b", buf.getvalue())`. The trailing `\b` matched `expected_slope=0.7` but not `expected=0.700000` or any other fixed-precision format, so the assertion passed or failed purely on the implementation's choice of print format string (`%g`-style versus `.Nf`/`+.Nf`), regardless of whether `expected_slope` was correctly derived from `config["merger_timescale_alpha"]` at call time. This is the single heaviest-weighted test in the rubric: it is one of only two nodes in `end_to_end_science`, which carries a full quarter of Slice 2 and therefore 6.25pp of a run's overall score. It was measured across the cohort to fail two of the four Developer configurations, and to vary run to run *within* one of them purely because that model's format string changed between runs — a false signal entirely unrelated to the capability the test exists to check, and one that corrupted the reported spread rather than only the mean.

Fixed by parsing every printed number out with a capture group and comparing numerically (tolerance `1e-9`), matching the convention `test_hA.py`'s own `_FLOAT` pattern already establishes for exactly this kind of line-scraping assertion. `_FLOAT` is duplicated verbatim into `test_hB.py` rather than imported, to avoid coupling two test-fixture files that are copied side by side into a grading worktree.

**The replacement collects every printed occurrence and passes if any one of them equals the tracked value** (`re.findall` plus `any`, not `re.search` on the first match alone). This is deliberate and is the point on which the change is easiest to get subtly wrong: the original literal-match assertion succeeded if the string `0.7` appeared *anywhere* in the printed summary, so matching only the first parseable occurrence would have been a strictly *stronger* test than the one being repaired — quietly changing what is scored beyond the defect, and able to newly fail a correct implementation that printed some other `expected=` value on a heading line first. The failure message still distinguishes "nothing printed at all" from "wrong value printed", and names the values actually found in the latter case.

Validated per `.claude/CLAUDE.md`'s reference-implementation requirement, using the recipe in `docs/reference-impl/README.md` (fresh disposable worktree of `substrate/relative-velocity` at the plan's pinned commit `043b13adc264689c376bdd337603e94d5447623a`, reference `calc.py`/`config.py`/`merger_rate.py` from `main`'s `eval/tasks/001-merger-rate-feature/reference_solution/`, removed after use):

- Unmodified reference implementation (prints `expected_slope:+.6g`): `pytest tests/` 80/80 passed; slice-2 hidden tests 17/17 passed, `test_E09` among them — confirms no regression from the change.
- Positive control: same reference with only its print format changed from `+.6g` to `.6f` (prints `expected_slope=0.700000`) — `test_E09` FAILED under the pre-change assertion and PASSED under the fixed assertion, both runs shown side by side. This is the exact defect the fix closes.
- Negative control A: same reference with `expected_slope` hardcoded to `1.0` (ignoring `config["merger_timescale_alpha"]`) while still printed — `test_E09` still FAILED under the fixed assertion.
- Negative control B, the one that actually exercises the changed assertion: reference left correct so the returned dicts still carry `expected_slope == 0.7`, but the *printed* value replaced with a wrong constant (`expected_slope=1.000000`). `test_E09` still FAILED, naming the values it found. Control A alone is insufficient evidence here, because the untouched sibling assertion on the returned dicts catches that case before execution ever reaches the printed-summary check — so it would pass even if the printed-summary assertion had been destroyed outright.

No test was added or removed; the slice-2 hidden test count is unchanged at 17 and the obligation map's node accounting is unaffected.
