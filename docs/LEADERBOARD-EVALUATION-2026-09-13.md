# Developer and reviewer leaderboard evaluation

Date: 13 September 2026. Decision: how to make the four-run leaderboard trustworthy, useful for model selection, and simple to extend.

This is an investigation and recommendation, not an approved design change or implementation. The harness, generated results, PM state, hidden tests, and frozen plan were not changed. Accepted recommendations should be folded into `MODE2-REWRITE-PLAN.md` in the implementation session.

## Recommended direction

1. Repair model identity at ingestion, preserve run provenance, and rebuild derived reports without changing graded attempts.
2. Rank developers by **first-attempt correctness**, with final performance and supervision cost alongside it. Replace the present binary “quality” score with visible size and complexity measurements; do not award quality points for successfully running a measurement tool.
3. Use two compact developer tables, both in the same model order: first submission, then supervised outcome. Show mean and observed minimum–maximum across runs, with sample counts and links to every run.
4. Keep reviewer evaluation separate and explicitly subjective. Use normalized rank points for genuine code-review panels, and PM's 0/1/2 acceptability rating for drift reviewers. The current runs contain only one reviewer model, so there is no comparative reviewer ranking to calculate yet.
5. Fix reviewer harvesting before adding panels: the current canonical-selection rule retains only one review per attempt and skill, even if several reviewers participated.

## Proposed leaderboard preview

First-submission ability and supervised outcomes for the frozen two-slice task. Higher correctness is better; smaller edits and shorter elapsed time are supporting measures.

- **Correctness:** mean percentage across both slices and then runs; brackets show the observed run minimum–maximum.
- **ΔLOC / ΔCC:** mean production line/complexity growth for **S1 / S2**, respectively; per-slice ranges stay in the run/model details to keep these tables readable.
- **Gain:** mean paired final-minus-first correctness, in percentage points.
- **Attempts / steers:** mean submissions for **S1 / S2**, and mean total steer events per run; individual run counts remain integers.
- **PM elapsed:** mean supervised wall time, rounded to minutes, including reviews and waits.
- **Runs:** completed/total runs, with numbered links to the evidence for each run.

### Developer — first submission

| Rank | Developer configuration | Correctness % [range] | ΔLOC S1 / S2 | ΔCC S1 / S2 | Runs |
|---|---|---|---|---|---|
| 1 | MAI Flash · opencode | **89.69 [88.43–90.95]** | +271.5 / +159.5 | +40 / +25 † | 2/2 · [1](#run-20260912T105700Z-c207d3), [2](#run-20260912T105743Z-56d31b) |
| 2 | Haiku 4.5 · claude · low | **75.49 [71.33–79.66]** | +441 / +245 | +60 / +35 † | 2/2 · [1](#run-20260912T065634Z-91ea9a), [2](#run-20260912T085427Z-846993) |

### Developer — supervised outcome

Same model order as above; final performance does not change the first-submission rank.

| Developer | Final correctness % [range] | Gain, pp | Final ΔLOC S1 / S2 | Final ΔCC S1 / S2 | Attempts S1 / S2 | Steers | PM elapsed |
|---|---|---|---|---|---|---|---|
| MAI Flash | **89.91 [88.43–91.39]** | +0.22 | +277 / +160 | +42 / +25 † | 3 / 3.5 | 4.5 | 1h 06m |
| Haiku 4.5 | **79.28 [71.77–86.79]** | +3.78 | +447 / +250 | +63 / +36 † | 4.5 / 3 | 5.5 | 0h 53m |

### Code reviewer — PM-assessed utility

Rank points compare reviewers on the same submission; a sole reviewer supplies no comparative ranking evidence.

| Reviewer configuration | Rank points | Compared runs / rounds | Other opponents | Observed panel size | Report extraction |
|---|---|---|---|---|---|
| gpt-5.6-luna · opencode | — single reviewer | 0 / 0 | 0 | 1 | 9/11 parsed; 2 parse errors |

All four runs contain code reviews, but none contains a multi-reviewer code-review panel. “0 compared runs” therefore does not mean no reviews occurred.

### Drift reviewer — PM-assessed acceptability

Ratings: 0 unacceptable, 1 acceptable, 2 excellent; finding a real violation is good reviewing, even when its verdict is FAIL.

| Reviewer configuration | Mean rating /2 | Unacceptable / assessed | Runs | Report extraction |
|---|---|---|---|---|
| gpt-5.6-luna · opencode | 1.5 † | 0/4 † | 4 | 17/21 parsed; 4 parse errors |

**Preview disclaimer:** all ΔCC values marked † are invented layout placeholders, not measured complexity. The drift rating and unacceptable count marked † are illustrative analyst mappings of PM prose, not recorded PM ratings; the production table would currently show “not rated.” Every other number is calculated from the existing four runs. Trial 6 is grouped with MAI using the operator's attestation; this does not repair the generated leaderboard. Model aliases mean `github-copilot/mai-code-1.1-flash`, `claude-haiku-4-5`, and reviewer `github-copilot/gpt-5.6-luna`; MAI effort is unrecorded. Numbered links in this report jump to its run-evidence rows; the implemented leaderboard should link to full run-detail sections. No composite appears because the recommended default ranks on first correctness.

The preview intentionally keeps spread on correctness and means on supporting metrics; the per-run tables below expose the underlying size, attempt, steer and time variation. A production model-detail summary should show the corresponding minimum–maximum for each supporting metric too, as recommended later.

## What the four runs actually show

Evidence: `results/runs/*/slice-{1,2}.json`, their `model-report.json` files, `results/leaderboard.{json,md}`, and each trial's authoritative `.git/worktrees/<worktree>/pm/<run_id>/{run.json,events.jsonl}`. All eight slices have attempt 0 and their accepted attempt available. All four runs reached completion. No hidden tests or graded Developer attempts were rerun during this investigation.

“First/final” below means **attempt 0 and the accepted attempt within each slice**, not slice 1 versus slice 2. The slices implement different obligations; comparing their scores as if one were a revision of the other would be misleading. Slice 2 also inherits accepted slice 1 code, so its first attempt is conditional on that earlier supervised outcome. “First submission under PM” is more accurate than “intrinsic, unsupervised ability”; even attempt 0 can include ordinary PM interaction before the first committed submission.

Correctness is the mean of obligation-group pass fractions, averaged equally across the two slices for the run. Values below are percentages; arrows show first → final.

| Run ID | Trial | Developer | Slice 1 correctness | Slice 2 correctness | Run correctness | Attempts [S1, S2] | Steers | PM elapsed |
|---|---|---|---|---|---|---|---|---|
| <a id="run-20260912T065634Z-91ea9a"></a>`20260912T065634Z-91ea9a` | `trial-4` | Haiku 4.5 | 88.49 → 89.36 | 54.17 → 54.17 | 71.33 → 71.77 | [5, 2] | 5 | 0h 53m |
| <a id="run-20260912T085427Z-846993"></a>`20260912T085427Z-846993` | `trial-5` | Haiku 4.5 | 92.65 → 94.41 | 66.67 → 79.17 | 79.66 → 86.79 | [4, 4] | 6 | 0h 53m |
| <a id="run-20260912T105700Z-c207d3"></a>`20260912T105700Z-c207d3` | `trial-6` | MAI Flash, currently null | 89.36 → 89.36 | 87.50 → 87.50 | 88.43 → 88.43 | [2, 3] | 3 | 0h 57m |
| <a id="run-20260912T105743Z-56d31b"></a>`20260912T105743Z-56d31b` | `trial-7` | MAI Flash | 94.41 → 95.29 | 87.50 → 87.50 | 90.95 → 91.39 | [4, 4] | 6 | 1h 14m |

Elapsed is `init` to `complete`, rounded to the nearest minute. Exact values are 53m15s, 52m45s, 57m04s, and 74m06s respectively. Trial 5 has a later `stop` event; using the last event would incorrectly include post-completion time. The two MAI runs overlap in wall time, another reason not to interpret elapsed time as pure model speed.

After assigning trial 6 to MAI using the identity evidence discussed below, descriptive model means would be:

| Developer | Runs | First correctness: mean [min–max] | Final correctness: mean [min–max] |
|---|---|---|---|
| MAI Flash | 2 | 89.69 [88.43–90.95] | 89.91 [88.43–91.39] |
| Haiku 4.5 | 2 | 75.49 [71.33–79.66] | 79.28 [71.77–86.79] |

These are report calculations, not repaired production results or a statistically established ordering. All 28 stored attempts have passing lint and zero file-surface violations. The existing final quality and scope scores are therefore 1.0 for every run. Final correctness has **not** converged to perfection: it still distinguishes these models, and acceptance by PM is not evidence of hidden-test correctness.

## Confirmed defects and design gaps

### Attempt numbering and review order: presentation bugs, not duplicated attempts

**Confirmed:** `_slice_section()` in `tools/leaderboard.py` interpolates the zero-based `accepted_at_attempt` directly beside the one-based `attempts_total` count. All eight accepted-slice headings mix these conventions. Trial 6's “Slice 1 — accepted at attempt 1 of 2” should read **“Slice 1 — accepted on attempt 2 of 2”**; its slice 2 should say **“attempt 3 of 3.”** Keep machine ordinals zero-based, as the design requires, and convert `ordinal + 1` only at the human-display boundary. Apply that conversion consistently to headings, attempt rows and links; never renumber stored sheets or add one to an already computed total. The existing renderer test asserting “accepted at attempt 1 of 2” encodes the display bug and needs its expected wording corrected.

**Repeated numbers are multiple reviews of one attempt, not duplicate Developer attempts.** The current “Review trend” table has one row per retained review, so drift and code review can legitimately share attempt 3. It also omits attempts without a commissioned review: trial 6 slice 1's initial attempt was steered directly by PM, and only its second attempt received these reviews. This explains a table starting at machine ordinal 1 and appearing to skip other attempts. The four runs' sheet ordinals are unique, contiguous and correctly associated with launch/steer events; no duplicate attempt record or numerical ordering corruption was found.

**The review-row order does not represent PM chronology.** `_review_trend_table()` sorts by `(attempt, role name)`, putting `code_review` before `drift_review` alphabetically. In trial 6 slice 1, `events.jsonl` records drift at **11:21:03 UTC**, then code at **11:22:51 UTC**, but the leaderboard reverses them. The “Reviewer” column also contains skill names, not the reviewer's model identity. These are real presentation defects. Changing the sort alone is insufficient because `_review_trend_entry()` currently drops timestamp and commission identity.

Recommended detail layout: an **Attempt history** with exactly one row per Developer attempt, including unreviewed attempts and the final PM decision, followed by a separate **Review history** with one row per commission. Label the latter “Reviews of each attempt — multiple rows can refer to the same submission.” Give it columns **Event order | Attempt | Recorded time | Role | Reviewer | Verdict / extraction status**; severity counts can follow where useful. Use the authoritative event-log position as the order key, retaining `at`/timestamp for display. A completion event is not necessarily the start of a concurrent review, so label this recorded order rather than pretending to reconstruct unrecorded execution starts. Retain machine ordinal and commission ID in provenance, and show all human attempt numbers from 1. For historical data lacking ordering provenance, label order unavailable rather than sorting by role and calling it chronology.

For trial 6 slice 1, the intended human-readable relationship is:

| Attempt | PM outcome | Reviews recorded for this submission |
|---|---|---|
| 1 | Steered | No commissioned review; PM steered after its own checks |
| 2 | Accepted | Drift at 11:21:03 UTC, then code at 11:22:51 UTC; both reports have bench extraction errors |

The parse errors describe the bench's extraction coverage, not PM's inability to read the reviews. This separation also accommodates future panels without confusing reviewer commissions with Developer iterations.

### Additional check of the generated report

A fresh in-memory rebuild of all four model reports matched their stored sheets, and a fresh leaderboard calculation/render matched both existing generated outputs exactly. These checks wrote no outputs. The current display is therefore not stale; the defects above arise from its rendering and schema choices. Cross-checking headings, review attribution/counts and ordering found no further current-run numerical mismatch beyond the issues documented here. In particular, the 32 retained reviews match 32 authoritative review entries; repeated attempt labels are not duplicated reviews. Preserve the earlier findings about null identity, misleading quality/scope labels, missing-data handling, parser errors and inconsistent PM prose—those remain relevant, rather than treating this follow-up as an all-clear for the existing report.

### Model identity: null is being treated as a model

`dev_check.py` passes `run_state.get("harness", {}).get("model")` directly to the sheet. `model_report.build_report()` checks agreement across sheets but accepts agreement on null. `leaderboard.discover_reports()` checks that a `model` key exists, not that its value is a usable identity; grouping therefore admits null and the Markdown renders `None`.

The concrete upstream omission is in trial 6’s authoritative `run.json`: `harness.name="opencode"`, `harness.model=null`, and `command_override=null`. Its `model-performance.md` and `notes.md` identify MAI Flash, matching the operator’s explicit identification; no inspected structured launch record supplies the missing model. This proves the metadata omission, not which default model the harness actually selected internally. Use the operator’s attestation for this historical correction and label that provenance; do not promote prose parsing into an automatic identity source.

The repair belongs upstream, with a shared identity resolver/validator in `bench_lib.py`, not a renderer substitution for the word “None.” Validate nonempty strings and preserve harness, provider/model, and known effort separately. Do not generically strip provider prefixes or merge aliases based on spelling similarity. Model-plus-harness/effort should define the default comparison configuration when these differ; unknown effort must remain unknown.

For this historical run, recover identity from authoritative recorded launch configuration if available, preserving its source; otherwise use the operator's explicit identification through a small, auditable bench-owned correction record keyed by run ID. Put any such override mapping in `policy.yaml`, with reason and evidence, rather than hardcoding a special case or editing a scoring sheet. Snapshot the applied correction and its attestation in report provenance so later policy changes do not erase how that generation was attributed. Conflicting evidence must produce a named error, not silently select a model. Never modify historical `run.json` to repair a benchmark label.

Missing identity should leave a conspicuous **unattributed run** entry, excluded from model ranks until resolved, rather than create a model named null or discard the evidence. Keep ordinary scoreable runs available. Use the same resolver and validation rules at ingestion and report boundaries rather than implementing competing fallback chains.

### “Quality = 1” currently means measurement coverage, not good code

`dev_check.run_code_health()` synthesizes `verdict="pass"` from exit 0; `leaderboard._slice_quality()` awards it 1.0. The raw health payload explicitly says `candidate_selection.verdict="none"`. Haiku trial 4's first slice has five cyclomatic candidates, four file-size candidates, and two duplication candidates while receiving a pass. This is consistent with the current written scoring rule but a defect in its interpretation as code quality.

The candidates are a bounded reading list: `limit_per_family=5`. Do not “fix” quality by counting those rows or summing their deltas. That would turn the display cap into a scoring ceiling and omit removed functions and other facts. Use full measurements and explicit before/after baselines.

### Reports lose information needed for the requested comparisons

`model_report.build_report()` retains only `final_attempt` for developer metrics; first-attempt correctness, size, and health remain in the sheets. Extend that reshape to expose first and final summaries, plus a compact attempt trajectory. Keep detailed raw payloads in sheets rather than duplicating every function in every rendered report.

`review_score.select_canonical_reviews()` intentionally keeps the last successful review event for each `(attempt, skill)`. That is incompatible with measuring multiple reviewers in the same round. The plan/policy prose suggesting panels are already fully representable overstates the implementation. In addition, `model_report._review_trend_entry()` drops `tool`, `model`, report identity and hash, so even retained reviewer records lose attribution in the trend output.

Retain one record per actual commission with a stable commission identifier, and separately record whether it supersedes an earlier commission. Derive a panel's participating reviews from those identifiers. A retry should not get a second vote; two distinct reviewers should not overwrite each other. Preserve independent per-attempt outcomes and hash verification while changing this selection rule.

### Missing-data treatment and prose can overstate results

The current leaderboard averages whatever slices are present and renormalizes the composite over available sub-scores. That can make an incomplete run look competitive with a full two-slice run. Also, `_slice_scope()` treats a missing scope dictionary as zero violations. These are existing design choices worth replacing during this redesign, not evidence that the four present runs are incomplete.

Use explicit expected-slice coverage, first/final coverage, tool coverage, completion status, and identity validity. Do not substitute the earliest available graded attempt for missing attempt 0 under G16 fallback. Mark incomplete comparisons unranked and retain them in run details; show how many eligible runs contribute to each model statistic. Report all launched/discovered runs alongside eligible counts so exclusions cannot hide a model's failure rate. A missing scope measurement is unavailable, not clean.

PM narrative is evidence of PM judgment, not metric authority. Trial 7's prose says “6 total attempts (3 each),” but sheets and launch/steer events show eight attempts [4,4]. Several PM narratives call the accepted science correct despite held-out failures. Keep these statements quoted and labelled; derive counts and correctness structurally.

## Developer scoring and uncertainty

### Correctness

Retain the existing obligation-based definition: for slice s and attempt a, `C(s,a) = mean(group passed / group total)`. Slice 1 has six groups over 44 tests and slice 2 four groups over 17 tests. Average the two slice scores equally, then average run scores equally within a model configuration. Do not flatten every test, every attempt, or an unequal number of available slices across runs into one pool.

The hidden tests cover scientific calculations, input-domain rejection, persistence, orchestration, fitting, reporting, and end-to-end science; [OBLIGATION-GROUPS.md](OBLIGATION-GROUPS.md) explains their weights. [Reference validation](reference-impl/README.md) records 44/44 and 17/17 passes and deliberate-defect checks. Preserve the known frozen-plan ambiguity there; this report recommends no rubric or test change mid-cohort.

A useful additional correctness safeguard is the **unchanged substrate regression suite**, run in the disposable grading environment before hidden-test injection, with baseline failures distinguished from introduced failures. Keep it a separate regression flag or eligibility gate, not an extra pass-count pool that dilutes the scientific obligations. Developer-authored test count and PM acceptance should not earn correctness points: tests may be weak or wrong, as the PM feedback demonstrates. More scientific invariants belong in a later, reference-validated rubric version applied consistently to the cohort.

Rank by mean first-attempt correctness. Display slice 1 first-attempt correctness in run details for the closest available cold-start signal. Alternative: rank only slice 1 if strictly fresh-start ability is the primary question, but that would discard the important slice 2 scientific task. Neither design isolates model ability from the PM, harness, effort, or reviewer configuration.

### Quality: size first, complexity alongside

Make production ΔLOC and Δcomplexity independent columns. Keep lint as a hygiene/coverage badge and file-scope violations as exceptions in details, with a top-level alert if nonzero. Scope's lack of violations does not establish semantic authorization: trial 7's PM feedback describes edits inside authorized files that its mechanical file check could not see. This supports keeping drift review even while removing scope from the numerical composite.

Use a documented line-count definition. For the first implementation I recommend **net physical lines added to production source**, `added - deleted` from Git, because it is cheap, auditable, and already distinguishable without a new analyzer. Label it explicitly; also preserve additions/deletions, and test/documentation deltas separately in details. Do not reward removing tests/docs or minifying code; smaller is a proxy, not a correctness guarantee. SLOC excluding comments/blanks is a reasonable later alternative, using one pinned analyzer on both revisions; do not mix its values with physical LOC.

Read-only `git diff --numstat <recorded base> <attempt commit> -- 'src/*.py'` gives these current production physical-line deltas. This path filter is an investigation definition; production patterns for implementation must live in policy.

| Trial | Slice 1 ΔLOC first → final | Slice 2 ΔLOC first → final |
|---|---|---|
| 4 | +442 → +453 | +248 → +248 |
| 5 | +440 → +441 | +242 → +252 |
| 6 | +263 → +263 | +149 → +150 |
| 7 | +280 → +291 | +170 → +170 |

Compare each slice's attempts against its **original slice baseline** for size/complexity trajectories, not the preceding attempt. Existing scope checks must retain their PM epoch baseline semantics. In a stop/restart case the stored grading baseline may have reset; never silently reuse that reset baseline for an apparent first-to-final improvement. For final whole-run growth, compare the final accepted slice-2 commit directly with the pinned substrate base; do not sum overlapping cumulative diffs. A whole-run “first” snapshot does not exist: slice 2 first was built on slice 1 final.

For complexity, use total production function cyclomatic complexity at endpoint minus that at baseline, with absolute endpoint total and maximum-function complexity in details. Count added and removed functions, and keep production/test code separate. Function splitting can raise total complexity through additional function-entry counts; consequently it should initially be descriptive, not an automatic penalty. The health payload has full endpoint functions and composition facts, but does not export a complete baseline fact bundle: a complete delta needs the same collector on the baseline as well. Reuse the configured analyzer; do not derive it from the top-five candidates or write a parallel Python complexity implementation.

Other already available facts include duplication signatures, function-size/complexity distributions, and dependency cycles. Add production duplicated-line burden and newly introduced dependency cycles as diagnostics only after validating coverage and attribution. Overlapping clone windows must count each source line once. Avoid candidate counts, whole-repository averages diluted by unchanged legacy files, or a weighted score assembled from every available correlated measure.

The linked [Earendil article](https://earendil.com/posts/measuring-code-sloppiness/) supports trying ΔLOC as a simple proxy while warning that optimization can invalidate it. It also discusses duplicated/flagged-line verbosity and complexity-weighted concentration in large functions. Adopt the practical idea of measuring size alongside correctness; defer the richer “erosion” and AST-pattern metrics until simpler measurements demonstrably miss important differences. Their thresholds and language-specific heuristics add calibration work, and their effectiveness on other repositories does not validate a score for this two-slice task.

### Composite: do not split correctness and quality evenly yet

The current formula is `0.50 correctness + 0.25 quality + 0.15 scope + 0.10 iterations`, evaluated on final submissions. Three terms are saturated or weakly discriminating here; the iteration formula gives the same perfect score to one, two, and three attempts.

**Recommended default:** correctness determines rank; ΔLOC, Δcomplexity, final improvement, attempts, and elapsed time remain visible decision criteria. Remove the misleading existing composite from the primary table until a quality score has a defensible interpretation. Resolve exact correctness ties by smaller first-attempt production ΔLOC, then stable model identity; label tied correctness so a formatting tiebreak is not mistaken for strong evidence.

If a single composite is desired immediately, use a plainly labelled **experimental first-attempt score**, e.g. `0.8 C + 0.2 Q`, where initially Q is only normalized production-size economy. Do not call it comprehensive code quality. Keep correctness visible and keep default rank correctness-first. A 50/50 version is easy but gives the entire observed economy range the same influence as the entire correctness scale: an empty failing edit can receive 0.5 from size alone. It is a poor primary ranking for scientific software. Another alternative, `C × (0.8 + 0.2 Q)`, prevents a zero-correctness solution earning points but still requires explicit policy calibration.

For lower-is-better metric x, the requested normalization is `N(x) = (max_x - x) / (max_x - min_x)`. Define its comparison pool as eligible run observations for the **same slice, endpoint, task/rubric, measurement version, and policy cohort**, never unrelated tasks or first/final values mixed together. Normalize per slice, average the two within a run, then average runs. If all x values are equal, assign every observation 1.0 and note “no discrimination”; missing measurements remain missing. Use all eligible raw run values for extrema so repeats are observations rather than hidden model-level preprocessing.

Store raw values, cohort member IDs, extrema, weights, and scoring version/hash with the generated leaderboard. Rebuild cohort-relative values together when adding a run; historical raw measurements remain unchanged. This makes moving composites explainable. Min/max scaling is sensitive to an unusually large or small edit; rank/percentile normalization is an alternative but coarse at four runs. Fixed reference anchors are more stable but need calibration. For this small cohort, min/max is acceptable as a labelled secondary experiment.

### Repeats, spread, and trajectory

With three to five repeats, show **mean [min–max], n** for each principal scalar metric, rather than variance in squared units or confidence intervals suggesting unjustified precision. At n=1 show the value and “n=1,” not zero variability. Standard deviation may be exported in JSON, but adds little to the main table. Min/max is observed spread, not a forecast interval; it naturally changes as samples are added.

Use the mean to match the existing arithmetic; median [min–max] is a reasonable alternative if operator delays dominate time. Do not switch estimators selectively after seeing which favors a model. Compute improvement within each paired run first, then summarize those deltas; separate endpoint ranges do not describe the range of improvements. Preserve exact [S1,S2] attempts for each run and show per-slice means/ranges at model level. Never average slice 1 and 2 into one cryptic iteration score.

Attempts count committed launch-family submissions, including the initial one; steers count `steer` events. Relaunches and free PM nudges are distinct, not automatically `attempts - 1`. Retain the existing monotonic ordinal rules and G16 refusal behavior. In run details, show each attempt's correctness, size, complexity, decision, and elapsed-from-start where recoverable, so unchanged correctness after several steers is visible.

### Time and tokens

Show **PM elapsed**, in hours/minutes, as an informational cost of the whole supervised process. Derive it from authoritative event timestamps, from initialization through the matching terminal event for the evaluated run lifecycle. Do not use scoring-sheet timestamps (grading time), report mtimes, or `updated_at`. For stopped/restarted runs choose the final evaluated lifecycle's terminal event, include earlier elapsed time, and label pauses; do not stop at an obsolete earlier stop. Missing or invalid timestamps produce unavailable timing. Store seconds so rounding never affects calculations.

Attempt time to the first floor/observation event is at best a submission-latency proxy: polling, queueing, reviews, PM work, operator pauses, and missing-artifact waits all contribute. Trial 7's PM prose explicitly reports two roughly 15-minute unproductive waits. Some of that is real process unreliability and matters operationally; it still is not model inference speed.

Do **not** put total time in the first-submission composite: it includes later steering and reviewers, so it would violate the intended meaning. If a separate final operational-utility score is later wanted, time can use the same min/max formula and a small explicit policy weight, among equally complete runs only. A stopped failure must never win for being fast.

Token support on `main` lives in `eval/harness/harnesses.py` and `aggregate.py`: parsers consume captured harness stdout, with different cache/reasoning fields and parsing strategies per harness. That older bench owned invocation and log capture; this one deliberately does not. Reusing the parser functions alone will not provide complete PM, developer, and reviewer totals. **Defer token reporting** unless the normal artifact trail already exposes complete structured usage with documented scope. Any future read-only adapter should report role, harness, parser source, coverage and cache/reasoning semantics, never zero for missing usage; do not add launcher instrumentation merely to collect it.

## Reviewer evaluation

### What is measurable from outside

Deterministic harvesting describes what was reported, not whether the review was good. Finding counts reward verbosity; a PASS on an easy final revision is not evidence of superior detection; an issue disappearing in the next report does not prove it was fixed. PM adjudication supplies useful external-to-reviewer judgment but is subjective and can miss the same scientific defects as reviewers. Label the table **PM-assessed reviewer utility**, separate from developer scoring.

For now, judge usefulness by valid in-scope defects, evidence/reproducibility, actionable specificity, false positives/overreach, and material omissions PM actually discovers. Do not rank on raw severity counts. A stronger future external check would use a separate fixed set of patches with known seeded defects and adjudicated false positives; that would measure detection against ground truth, but is a separate reviewer benchmark, not an extension to live PM runs or exposure of hidden tests to a running Developer.

### Smallest useful PM output contract

> **Since shipped, and superseded — this section is kept as the record of what was proposed, not as current state.** `project-manager` has landed exactly this contract and more (`ai-agent-coder` `d7307dd`, `b9c10f4`, `04f3b86`): per-slice `review_judgments` carrying both a 0–2 rating per report and an independent best-first `rank_groups` panel comparison, *plus* `developer_judgments` — PM's 0–2 rating of each Developer **submission**, with an immutable `developer: {tool, model, effort}` snapshot — which this report did not anticipate at all and which resolves its identity finding structurally rather than by attestation. The implementation brief this paragraph links to has been archived (`archive/`), so the link below is intentionally left unresolved rather than repointed at a moved file.

Concrete PM-side implementation brief: a fresh-session prompt for ai-agent-coder, `PROJECT-MANAGER-REVIEW-JUDGMENTS-PROMPT.md` (since archived). The recommended authority is an optional per-slice `review_judgments` list in PM’s existing signed `run.json`, written by a small authenticated `judge-reviews --file` command. The existing `pm rate --text` writes the final narrative to `model-performance.md`; keep that as context and render new judgments in the final report from JSON, rather than asking the bench to extract them from prose.

Assuming the user's planned PM change, add a structured assessment through PM's own normal state-writing path after it has read and adjudicated a round's reviews and before the steer/accept decision. The bench only reads it after completion. This should be a general PM feature, with no bench prompt instructions. Record:

- A stable round ID and the evaluated slice, attempt, head and authorization/grant context.
- Participating commission IDs; reviewer identity comes from those existing records, not retyped prose.
- Ordered tie groups of commission IDs, or `not_comparable` with reason when reports assessed different revisions/scopes; no forced ranking of unlike opportunities.
- A short reason/evidence reference for each judgment, including an explicit missing/unusable assessment state.
- For drift, one explicit 0/1/2 rating per evaluated review: unacceptable, acceptable, excellent.

Only finished reviews of the same opportunity form a comparative panel. A timed-out or unreadable review remains an explicit reliability outcome; do not silently pretend it ranked last on substantive review quality. Recommissioning retains history but supplies one effective submission per reviewer for a round. PM final prose can summarize these records, not replace them. Bench validation must reject unknown commission IDs, duplicates, impossible ranks, or mismatched heads/roles.

### Ranking method and changing panel sizes

Use normalized rank points: for a panel of N reviewers and 1-based rank r, `score = (N - r) / (N - 1)`. This is the simple N, N−1, … points scheme with panel size removed. Two-member panels give 1 and 0; four-member panels give 1, 2/3, 1/3, 0. Ties share the mean occupied rank, so an all-tied panel gives each reviewer 0.5. N=1 has **no comparative score**, not 1.0.

Average a reviewer's eligible round scores within each run, then average those run means, showing both round and distinct-run counts. This prevents a difficult Developer run with many repeated reviews dominating the leaderboard. A straight round mean is simpler and defensible if the question is “utility per commission”; choose and document one, rather than mixing them.

New reviewers can join any panel without rewriting old results. However, normalized rank does not correct for opponent strength: winning against weak reviewers differs from winning against strong ones. Include a recurring anchor reviewer where practical, rotate panel membership, show unique opponents and panel-size range, and mark disconnected comparison groups as not globally comparable. With only one contributing run, display a provisional result. Do not invent missing comparisons or award nonparticipants losses. Two reviewers per comparable round are a sensible default; three or four buy diversity at additional cost, not automatic statistical reliability.

Bradley–Terry (pair comparisons) or Plackett–Luce (ordered panels) could eventually account for opponent strength, but add fitting, identifiability, sparse/disconnected-data and tie-handling decisions. They cannot conjure evidence between disconnected groups. At this sample size, normalized points plus coverage is the preferable 80/20 choice. Reconsider a fitted model only when there is a reasonably connected set of repeated mixed panels and opponent imbalance demonstrably changes decisions.

Keep drift separate: show mean 0–2 rating, unacceptable count/assessed count, and distinct runs. A mean alone could conceal a catastrophic 0 among several 2s. Never automatically translate a drift FAIL into a bad reviewer rating: detecting a real violation is good work. A low drift score should help the operator identify unsuitable reviewers, not enter the Developer composite.

### Current-run illustration, explicitly not new graded evidence

There are 32 harvested review records (8, 11, 6 and 7 by trial), matching the 32 authoritative commissioned review entries; six records carry parse errors. Thus the panel-loss defect is a confirmed code-path limitation, not observed loss of a current panel. All harvested reviewer identities are `opencode` / `github-copilot/gpt-5.6-luna`, across both roles. Rank 1 in each one-member panel is tautological and is excluded from the proposed comparative score. There is no defensible ordering of multiple reviewer models across these four runs.

To exercise the proposed drift presentation, the following are **illustrative analyst mappings of PM prose**, not PM-authored structured ratings and not production leaderboard data:

| Trial | Illustrative drift rating | PM evidence motivating the illustration | Comparative code-review score |
|---|---|---|---|
| 4 | 1, acceptable | Valuable defects; PM rejected one false-positive P1 | Unavailable: sole reviewer |
| 5 | 1, acceptable | Useful findings; one out-of-scope request | Unavailable: sole reviewer |
| 6 | 2, excellent | PM says all drift findings were material and adopted | Unavailable: sole reviewer |
| 7 | 2, excellent | PM praises real within-file authorization catches and reproducible findings; role-specific judgment is less explicit | Unavailable: sole reviewer |

These four illustrative observations would display mean 1.5/2, unacceptable 0/4. They illustrate formatting only; the conversion threshold is analyst judgment, and trial 7's combined reviewer narrative is weaker evidence for a role-specific score. Use hypothetical multi-reviewer fixtures to test points, ties, variable panel sizes and disconnected groups; never insert fictional reviewer results into `results/`.

The existing finding parser also rejects real reports with Markdown bolding or title-before-location formatting. Preserve named parse errors and hashes, and make narrowly tested syntax accommodation where severity/location can be recovered unambiguously. Separate **parser coverage** from reviewer reliability: a bench parser rejecting a human-usable report is not automatically evidence the reviewer was bad. Do not add an LLM parser or silently turn failed extraction into zero findings.

## Human-readable layout

Use this opening: “First-submission ability and supervised outcomes for the frozen two-slice task. Higher correctness is better; smaller edits and shorter elapsed time are supporting measures.” Put generation mechanics, versions and regeneration instructions at the bottom.

Then a short bullet glossary, one sentence per displayed metric:

- **Rank:** order by mean first-attempt correctness, with tied correctness identified explicitly.
- **Developer:** the model, harness and known effort configuration being compared.
- **Correctness:** equally weighted obligation-group pass fractions, averaged equally over both slices and then runs.
- **ΔLOC:** net production physical-line growth from each slice's original baseline, with smaller changes interpreted alongside correctness.
- **ΔCC:** change in total production function cyclomatic complexity from the same baseline.
- **Gain:** paired final-minus-first correctness, in percentage points.
- **Attempts [S1,S2]:** initial submission plus subsequent launch/relaunch/steer submissions for each slice.
- **PM elapsed:** initialization to completion of the supervised run, including reviews and waits.
- **Runs:** eligible/total run counts and numbered links to each run's details; brackets on scalar metrics show observed minimum–maximum.

Recommended order and columns:

1. **Developer — first submission:** Rank | Developer | Correctness | ΔLOC [S1,S2] | ΔCC [S1,S2] | Runs. Keep size and complexity vectors labelled so slice difficulties are not obscured; if spread makes this too wide, place per-slice size/complexity spread in the model detail while retaining model means here.
2. **Developer — supervised outcome:** Developer | Final correctness | Gain | Final ΔLOC [S1,S2] | Final ΔCC [S1,S2] | Attempts [S1,S2] | PM elapsed | Completed/total. Preserve the first table's row order; do not silently re-rank by final results.
3. **Code reviewer — PM-assessed utility:** Reviewer | Rank points | Runs/rounds | Opponents | Panel sizes | Coverage/reliability. Add a sentence explaining normalized points and unranked single-member panels.
4. **Drift reviewer — PM-assessed acceptability:** Reviewer | Mean /2 | Unacceptable/assessed | Runs | Coverage. Define 0/1/2 immediately below the heading.
5. **Model/run details:** compact model summary followed by chronological runs; identity/provenance, first/final per-slice table, attempt trajectory, failed obligations, reviewer judgments/findings, and links to full PM prose/raw reports. Quote short relevant PM excerpts; avoid repeating all of the prose in the main document.
6. **Run index**, then measurement notes and actionable data problems.

Use explicit stable anchors such as `run-20260912T105700Z-c207d3`, independent of rank or model name. A top model row's Runs cell should contain numbered links (1, 2, etc.) to its actual run subsections, as shown in the preview. Numbers can be chronological within each model; full run IDs and trial labels are the durable identifiers.

Each run should show full run ID, recorded branch, original Developer worktree path, observed worktree presence at generation, accepted commit(s), results-directory link, and PM artifact location when available. Snapshot original provenance during post-hoc analysis so a later cleanup does not erase the mapping. A recorded path is historical; “present/absent as of generation” is a separate observation, and absence is not proof that `cleanup` ran.

The current index can map these exact strings from `git branch` and `ls results/runs`:

| Branch in substrate repository | Original worktree under `substrate/` | Results directory / run ID |
|---|---|---|
| `pm-eval-v2/trial-4` | `relative-velocity-trial-4` | `20260912T065634Z-91ea9a` |
| `pm-eval-v2/trial-5` | `relative-velocity-trial-5` | `20260912T085427Z-846993` |
| `pm-eval-v2/trial-6` | `relative-velocity-trial-6` | `20260912T105700Z-c207d3` |
| `pm-eval-v2/trial-7` | `relative-velocity-trial-7` | `20260912T105743Z-56d31b` |

Sort the index by full branch string, link every row back to run details, and include developer identity. `git -C substrate/relative-velocity branch` lists the relevant branches; running `git branch` in the bench itself lists a different repository. Retain original paths even after worktree removal, avoid dangling “open worktree” links, and use readable relative links where possible. The repeated identity in this compact index serves lookup; repeating all data problems both per model and globally does not. Store each problem once with its run reference and link to it from affected summaries.

## Implementation priorities and verification

Proceed in this order after choosing the scoring policy:

1. Shared identity resolution and historical correction; provenance snapshot; strict missing-data representation. Regenerate only affected metadata and derived reports through tooling, preserving attempt IDs, commit hashes, measurements and provenance. Do not hand-edit scoring sheets or rerun a graded Developer attempt.
2. First/final extraction, complete-run aggregation, run anchors/index, and the two-table renderer. Retain raw evidence and put new thresholds, normalization choices, patterns and weights in policy.
3. Production size/complexity summaries and elapsed timing, with explicit baselines and metric versions. Supplementary measurement must remain post-hoc in disposable grading worktrees; archive superseded generated artifacts and distinguish a metric-version rebuild from a new trial.
4. Panel-preserving review schema and parsing repair; then read PM's new structured judgments once the PM feature exists. Old runs remain explicitly unranked where no comparison was recorded.
5. Update the authoritative design and README to match the adopted behavior. Keep the frozen task plan unchanged.

Target verification at actual risks: zero-based machine ordinals versus one-based human headings/rows, multiple reviews for one attempt, unreviewed attempts still shown, recorded review order versus role-name sorting, null/empty/conflicting identity, corrected identity round-trip with unchanged grades, missing attempt 0, incomplete two-slice coverage, paired improvement arithmetic, equal/extreme/missing normalization inputs, baseline resets and deletions, tests/docs excluded from production size, completion followed by a later stop, multiple reviewers on one attempt, retry versus new participant, ties and singleton panels, malformed report versus genuine zero findings, and stable links after rank changes/worktree disappearance. Test against copies or fixtures; do not contaminate real results with synthetic rows. Run lint and the existing suite for implementation; full suites exceeding a minute should run through a test subagent.

A fresh-eyes `gpt-5.6-terra` subagent reviewed the original report against the request and repository evidence, including identities, attempt/review counts, metric definitions and measurement boundaries; it found no material errors or gaps. Two wording clarifications were incorporated. A follow-up lower-power reviewer checked the added leaderboard preview and attempt/order findings against the four runs and found no further numerical or logical gap. The main agent independently checked the numerical summaries, authoritative review counts and local document links.

This report used direct code/doc inspection, read-only JSON calculations, Git diffs of recorded commits, event timestamp checks, the article above, and bounded lower-power subagent investigations. It did not revalidate hidden tests, execute production grading, fit a statistical ranking model, or measure complete token usage. Two ad hoc inspection commands initially failed (`python` unavailable and an incorrect JSON key); corrected `python3` checks completed successfully. The next action is to choose correctness-first versus an experimental composite, accept or adjust the layout and reviewer policy, then implement the agreed changes in a fresh session.
