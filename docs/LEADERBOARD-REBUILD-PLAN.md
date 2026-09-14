# Leaderboard rebuild: implementation plan

**Status: approved, stage 0 complete. Stages 1-5 are outstanding.**

This is the self-contained work order for rebuilding the Developer/reviewer leaderboard, written so every stage can be executed from a fresh session with no dependence on the conversation that produced it. `docs/MODE2-REWRITE-PLAN.md` remains the authority for the system as a whole; this document is the work order that amends it, and each stage folds its own outcome back into that plan (`AGENTS.md`: "fold decisions into `docs/MODE2-REWRITE-PLAN.md`, not only into `HANDOFF.md`").

---

## Context

`docs/LEADERBOARD-EVALUATION-2026-09-13.md` investigated whether the four-run leaderboard is trustworthy enough to select a Developer model. It is not, and the failure is in the measuring apparatus, not the runs. Four defects are confirmed against live output (`results/leaderboard.md`):

1. **A run with no recorded model currently ranks first, as a model literally named `None`.** `dev_check.py:1142` passes `run_state["harness"]["model"]` straight through; `model_report._require_consistent` accepts every sheet agreeing on `null`; `leaderboard.discover_reports` (`leaderboard.py:188`) checks that a `model` key *exists*, not that its value identifies anything; `group_reports_by_model` then keys a model group on `None`. `harness.name` and `harness.effort` are read nowhere and discarded, so two runs of the same model under different harnesses or efforts are indistinguishable, while one model's two runs split across two rows when one run lost its name.
2. **"Quality = 1.0" means "the measurement tool ran", not "the code is good."** `dev_check.run_code_health` synthesizes `verdict="pass"` from exit 0 (`dev_check.py:817`) even though health.py emits no verdict of its own and its payload says `candidate_selection.verdict = "none"`; `leaderboard._slice_quality` (`leaderboard.py:262`) awards 1.0 for that verdict. Trial 4's slice 1 carries ten code-health candidates (5 cyclomatic, 4 file-size, 1 duplication) and scores a clean 1.0. Every one of the 28 stored attempts scores quality 1.0 and scope 1.0, so two of the composite's four terms discriminate nothing.
3. **The composite ranks on saturated terms.** `0.50 correctness + 0.25 quality + 0.15 scope + 0.10 iterations`, evaluated only on final submissions. Quality and scope are constant; the iterations term gives one, two and three attempts the identical score. Correctness is doing all the work while carrying half the weight, and it is measured at the *end* of supervision, which is the thing PM's steering is designed to improve.
4. **Presentation misreports what happened.** `_slice_section` (`leaderboard.py:573`) interpolates the 0-based `accepted_at_attempt` beside the 1-based `attempts_total`, so every heading reads "accepted at attempt 1 of 2" for a slice accepted on its second attempt. `_review_trend_table` (`leaderboard.py:555`) sorts by `(attempt, role name)` and calls it a trend, so `code_review` always precedes `drift_review` regardless of when each ran — in trial 6 slice 1 the event log records drift at 11:21:03Z and code at 11:22:51Z, and the table reverses them. Its "Reviewer" column holds the sheet *field name*, never the reviewer's model. Attempts PM steered without commissioning a review are absent from the table entirely, making the numbering look like it skips.

Two further gaps are structural rather than cosmetic. `review_score.select_canonical_reviews` (`review_score.py:270`) keeps the **last** review per `(attempt, skill)`, so a genuine panel of two reviewer models on one submission would silently collapse to one, with no record that the other existed — the sheet has one `drift_review`/`code_review` slot per attempt and cannot represent a panel at all. And `model_report.build_report` carries only `final_attempt` per slice, so first-attempt correctness — the signal that best separates these models — exists in the sheets but reaches no report.

Since that evaluation was written, **`project-manager` has landed exactly the structured PM-side output the evaluation asked for, and more** (`ai-agent-coder` commits `d7307dd`, `b9c10f4`, `04f3b86`). Four new runs (trials 8–11) already carry it. This changes the plan materially:

- `slices[].review_judgments[]` — PM's own 0/1/2 rating per review report (`assessment: "rating"`), and *independently* a best-first `rank_groups` panel comparison (`assessment: "comparison"`), plus explicit `status: "unavailable"` records. Joined by `(run_id, slice.id, review_id)`.
- `slices[].developer_judgments[]` — **new, and not anticipated by the evaluation**: PM's 0/1/2 rating of each Developer *submission*, with an immutable `submission` snapshot (`origin_event.index`, `head`, `before_head`, `grants_seen`) and a `developer` snapshot (`tool`, `model`, `effort`). Joined by `(run_id, slice.id, submission.origin_event.index)`.
- `slices[].reviews[]` now carries stable `review_id`, `effort`, `origin_event {index, kind, slice}` and `review_context`.

The `developer` snapshot resolves the identity defect structurally rather than by attestation, for every run that has one. Verified against the runs on disk:

| Trial | `harness` in run.json | `developer_judgments[].developer` | Resolution |
|---|---|---|---|
| 8 | `claude` / `claude-haiku-4-5` / effort **null** | `claude` / `claude-haiku-4-5` / **`low`** | judgment fills the missing effort |
| 9 | `claude` / `claude-haiku-4-5` / `low` | same | agree |
| 10 | `opencode` / model **null** | `opencode` / **`github-copilot/gpt-5.6-luna`** / null | judgment fills the missing model |
| 11 | `opencode` / model **null** | same | judgment fills the missing model |
| 4, 5, 7 | populated | *(none — pre-judgment PM)* | harness alone |
| 6 | `opencode` / model **null** | *(none — pre-judgment PM)* | **only run needing an operator attestation** |

Trials 8 and 9 are the same real configuration and would have been split into two leaderboard rows by `harness.effort` alone; the judgment snapshot merges them correctly. Only trial 6 has no structural evidence at all.

**Checked and worth stating plainly: no run in the cohort contains a real reviewer panel.** Grouping every review in trials 4–11 by `(slice, head, skill)` yields exactly one `(tool, model)` pair in every group. Trials 4–9 used `github-copilot/gpt-5.6-luna` via opencode for both roles; trials 10–11 used `claude-haiku-4-5` via claude for both. Trial 10's PM prose says "two independent reviewers", but that means the two *skills*, not two models. So the panel-preserving schema is built for correctness and for future cohorts — it is not fixing observed data loss, and the reviewer comparison tables will honestly read "single reviewer, no comparative score" until a multi-model panel is actually run.

### Intended outcome

A leaderboard that answers the question the bench exists to ask — *which model writes good code on its first submission, and how much supervision does it then need* — from eight runs instead of four, with every number traceable to a named measurement and every gap labelled rather than filled.

### Decisions taken (do not re-litigate)

| Decision | Choice |
|---|---|
| Ranking basis | **Mean first-attempt correctness.** The existing composite is removed entirely, and its `leaderboard.weights` / `scope_violation_penalty` / `iteration_reference_attempts` keys are deleted from `policy.yaml` (`AGENTS.md`: no config key nothing reads). No experimental composite is built. ΔLOC, ΔCC, gain, attempts, steers and PM elapsed stay visible as supporting columns, never blended. |
| Cohort | **All eight runs, trials 4–11.** Trials 8–11 have never been graded. Trials 4–7 are re-graded under the new schema and labelled historical/unjudged where PM recorded no structured judgments. |
| Delivery | **Five staged increments**, in the evaluation's own priority order, each lint-clean with tests and its own commit. |
| PM judgments | Harvested and displayed **separately and labelled as PM assessments**, never blended into any deterministic number — the same separation `pm_subjective_rating` already gets (`MODE2-REWRITE-PLAN.md` §6 Tool 4). |
| Implementation model | Each stage delegated to a **Sonnet** subagent with the stage brief; the main agent reviews the diff, runs lint and the suite itself, and is accountable for what lands. The suite is ~20 s (326 tests), well under the "delegate long suites" threshold, so it runs in the main context. |

---

## Boundaries that still hold

Nothing in this work touches the measured object. Restating, because several stages run tools over PM state:

- **Read-only against PM.** No run token, no writes to PM state, `pm.py` never invoked as a subprocess. `pm_lib` stays a library import for plan/git helpers. `run.json` is never edited to repair a benchmark label.
- **Grading stays post-hoc, in disposable worktrees.** Stage 3 adds measurements that check commits out; they use the existing `dev_check.grading_worktree` contextmanager and the same post-hoc contract. Do not add a live-grading path.
- **Never hand-edit a scoring sheet, and never re-run a graded Developer attempt as if it were the same one.** Re-grading under a new schema is a metric-version rebuild of the apparatus's own derived output, which is legitimate; it is recorded as such and the superseded `results/` tree is archived first, never deleted.
- **Every threshold, path and tunable in `policy.yaml`.** New measurement definitions (production path globs, LOC definition, expected slice coverage, identity corrections) go there, not into Python.
- **Fail loudly and specifically.** Every new error names the concrete run id, slice, attempt, path or key. An unavailable measurement is recorded unavailable, never as a clean pass or a zero.

---

## Stage 0 — set up

1. Write this document to `docs/LEADERBOARD-REBUILD-PLAN.md`.
2. Archive the current generated results before anything regrades: `python tools/cohort_run.py reset-leaderboard --yes` (archives `results/` into `archive/results-<UTC>/`; never deletes). Trials 4–7's sheets are the only copies of that generation's derived output, and the sheet schema changes in stages 1–4.
3. Confirm the baseline is green: `python -m pytest tests/ -q` (expect 326 passed, ~20 s) and `python <lint.py> --repo . check --base HEAD` clean.

---

## Stage 1 — identity, and strict missing-data representation

**Goal:** a run is attributed to a Developer *configuration*, or it is conspicuously unattributed and excluded from ranking. One resolver, used at ingestion and at every report boundary.

### `tools/bench_lib.py` — new shared helpers

```python
def active_judgments(records: list[dict]) -> list[dict]:
    """Judgment records still in force: every record whose judgment_id is not
    named by a later record's `supersedes`, within this one collection."""

def resolve_developer_identity(
    run_state: dict, *, run_id: str, corrections: dict
) -> tuple[dict, list[str]]:
    """The Developer configuration this run measured, with its provenance."""
```

`resolve_developer_identity` merges three sources, in this order, and returns a block plus any named problems:

1. **`developer_judgments[].developer` snapshots** across every slice, taken through `active_judgments`. These are PM's own immutable record of what it launched. If two active snapshots disagree on a non-null field, that is a named error, never an average or a pick.
2. **`run.json`'s `harness`** — `{name, model, effort, command_override}`.
3. **`policy.yaml`'s `identity.corrections[<run_id>]`** — an operator attestation, used only to fill a field neither structural source recorded.

Merge rule, stated once and tested: **`null` means "not recorded", not a conflicting value.** Two non-null differing values for the same field are a named error naming both sources. This is what lets trial 8 resolve to `effort: "low"` (harness recorded null, PM's judgment recorded low) without special-casing anything.

`command_override` non-null means PM launched a custom command, and `pm_lib` deliberately records `tool: "custom"` with null model/effort. That is an honest unknown, not a gap to fill — such a run resolves unattributed unless an attestation names it.

Returned block:

```json
{"harness": "claude", "model": "claude-haiku-4-5", "effort": "low",
 "configuration_key": "claude-haiku-4-5 · claude · low",
 "sources": {"harness": "run_harness", "model": "run_harness", "effort": "pm_developer_judgment"},
 "attributed": true, "attestation": null}
```

- `configuration_key` is the grouping and display identity: model, harness, effort. An unrecorded effort renders `effort unknown` and **stays a distinct configuration** — never merged with a run that recorded one, never normalised by spelling similarity, and provider prefixes are never stripped.
- `attributed: false` when model or harness is unresolvable. Such a run keeps every measurement and appears in the run index and run details as an **unattributed run**, and is excluded from model ranking. It is never discarded and never becomes a model named `None`.

### `policy.yaml`

```yaml
# Operator attestations for runs whose PM state never recorded the Developer
# identity, keyed by run id. Used only to fill a field neither run.json's own
# `harness` block nor PM's `developer_judgments[].developer` snapshots
# recorded -- a structurally recorded value always wins, and a conflict
# between an attestation and a recorded value is a named error, never a
# silent override. Each entry states its reason and the evidence behind it;
# the applied correction is snapshotted into report provenance so a later
# policy edit cannot rewrite how an earlier generation was attributed.
identity:
  corrections:
    20260912T105700Z-c207d3:
      harness: opencode
      model: github-copilot/mai-code-1.1-flash
      effort: null
      reason: >-
        PM recorded harness.model=null (opencode, no command_override) and this
        run predates project-manager's developer_judgments, so no structured
        launch record survives.
      evidence: >-
        Operator's explicit identification, corroborated by this run's own
        model-performance.md and notes.md, both of which name MAI Flash.
        Prose is corroboration only -- it is never parsed as an identity source.
```

Trial 6 is the only entry. Trials 10 and 11 need none: their identity is recovered structurally.

### Call sites

- `dev_check.py` `main()` replaces `model=run_state.get("harness", {}).get("model")` with the resolver, and `upsert_attempt` writes a structured `developer` block onto the sheet in place of the flat `model` string.
- `model_report.build_report` checks sheets agree on the whole `developer` block via `_require_consistent`, and **rejects agreement on an unattributed block reaching the ranked path** — an unattributed run produces a report flagged `attributed: false`, not a report claiming a model.
- `leaderboard.discover_reports` validates the block rather than the mere presence of a key; `group_reports_by_model` groups on `configuration_key`.

### Strict missing-data representation (same stage, same schema)

- `leaderboard._slice_scope`'s `or {} / or []` must stop reading a **missing** scope measurement as zero violations. A measured empty list is clean; an absent `scope` block is `None` plus a named problem, exactly as correctness and quality already behave.
- Every run gains an explicit `coverage` block: expected slices (`policy.yaml`'s new `leaderboard.expected_slices: 2`) versus graded, whether attempt 0 and the final attempt both carry rows per slice, which measurement tools were available, PM completion status, and identity validity.
- **Eligibility, computed from that block:** a run is eligible for first-submission ranking only when identity is attributed, PM status is `complete`, every expected slice is graded, and each slice has a real attempt-0 row. Under G16's fallback a slice can legitimately hold only its final attempt's row — in that case attempt 0 is genuinely absent, and the run is unranked for first submission with that named reason. **Never substitute the earliest available graded attempt for a missing attempt 0.** Ineligible runs stay fully visible in run details, and every model row reports eligible-versus-discovered counts so an exclusion can never hide a failure.

### Verification

Fixtures for: both structural sources agreeing; judgment filling a null harness field (trial 8's shape); judgment filling a null model (trial 10's shape); two non-null sources conflicting → named error; no source at all → unattributed, excluded from rank, present in the index; an attestation filling a gap; an attestation conflicting with a recorded value → named error; `command_override` set → unattributed; a superseded developer judgment ignored by `active_judgments`; effort unknown kept distinct from effort low. `tests/test_tool_contract.py` drives the real upsert functions against a shared sheet and will need its hardcoded `model=` updated to the block.

---

## Stage 2 — first/final extraction, the two-table renderer, anchors and index

**Goal:** the reports carry what the tables need, and the tables say what actually happened.

### `tools/model_report.py`

Per slice, emit `first_attempt` (ordinal 0) and `final_attempt` summaries, plus a compact `attempt_trajectory` — one entry **per Developer attempt**, including attempts that were steered with no commissioned review:

```text
attempt (0-based machine ordinal) · pm_attempts_counter · commit_sha ·
correctness · size/complexity (stage 3) · pm_decision · pm_developer_judgment ·
commissioned review_ids
```

Keep the bulky raw payloads in the sheets; the trajectory is a summary, not a second copy. `resolve_attempts_total`'s `max(ordinal) + 1` rule is correct and stays.

Add a `timing` block: `init` event to the matching terminal event (`complete`, or `stop` for a stopped run), **stored in seconds**, derived only from `events.jsonl` timestamps — never sheet timestamps (grading time), file mtimes, or `updated_at`. Trial 5 has a `stop` event *after* its `complete`; the terminal event is the one matching the recorded status, so that trailing event must not extend the measured span. Unparsable or offset-naive timestamps produce unavailable timing, never a guess.

`_review_trend_entry` stops dropping attribution: it carries `review_id`, `skill`, `tool`, `model`, `effort`, `head`, `at`, the event index, report ref and sha256, alongside verdict/findings or the named parse error.

### `tools/leaderboard.py` — the renderer

Delete the composite (`_slice_quality`, `_slice_scope`, `_slice_iterations`, the weight blending and renormalisation, and `_SUB_SCORES`). Rank by mean first-attempt correctness: per slice, the equally weighted mean of obligation-group `fraction`s; averaged equally across the two slices within a run; then equally across a configuration's eligible runs. Ties on exact correctness break by smaller first-attempt production ΔLOC, then by `configuration_key`, and tied correctness is **labelled as tied** so the tiebreak is not read as evidence.

Document opening, verbatim: *"First-submission ability and supervised outcomes for the frozen two-slice task. Higher correctness is better; smaller edits and shorter elapsed time are supporting measures."* Then a one-line-per-metric glossary. Generation mechanics, metric versions and the regeneration command move to the bottom.

Four tables, in this order:

1. **Developer — first submission:** Rank | Developer configuration | Correctness % [min–max] | ΔLOC S1/S2 | ΔCC S1/S2 | Runs (eligible/discovered, with numbered links).
2. **Developer — supervised outcome:** same row order, never silently re-ranked. Final correctness [range] | Gain (pp) | Final ΔLOC S1/S2 | Final ΔCC S1/S2 | Attempts S1/S2 | Steers | PM elapsed | PM Developer rating (mean /2, n) | Completed/total.
3. **Code reviewer — PM-assessed utility** (stage 4).
4. **Drift reviewer — PM-assessed acceptability** (stage 4).

Then per-configuration detail, a run index, measurement notes, and data problems **stored once** with their run reference and linked from affected summaries rather than repeated per model and again globally.

Spread convention throughout: **mean [min–max], n**. No variance in squared units, no confidence intervals. At n=1, show the value and `n=1`, never zero spread. Improvement is computed **within each paired run first**, then summarised — never as a difference of two independently summarised endpoints.

### The two presentation defects, fixed properly

**Ordinals.** Machine ordinals stay 0-based everywhere in the sheets and JSON, per `MODE2-REWRITE-PLAN.md` §7. Convert `ordinal + 1` **only** at the human-display boundary, consistently across headings, attempt rows and links. Never renumber a stored sheet; never add one to an already computed total. `tests/test_leaderboard.py:471`'s `assert "#### Slice 1 -- accepted at attempt 1 of 2"` encodes the bug and must become `accepted on attempt 2 of 2`.

**Attempt history and review history become two separate tables.** One row per Developer attempt in the first, including unreviewed attempts and PM's final decision. One row per review *commission* in the second, headed *"Reviews of each attempt — multiple rows can refer to the same submission"*, with columns **Event order | Attempt | Recorded time | Role | Reviewer | Verdict / extraction status**. Order by the authoritative `events.jsonl` position, displaying `at` alongside; a completion timestamp is not a start time, so this is labelled *recorded* order, never reconstructed execution order. Historical data with no ordering provenance is labelled order-unavailable rather than sorted by role and called chronology.

For trial 6 slice 1 the tables must read: attempt 1 steered with no commissioned review; attempt 2 accepted, with drift at 11:21:03Z then code at 11:22:51Z, both reports carrying bench extraction errors.

Anchors are stable and independent of rank and model name (`run-20260912T105700Z-c207d3`), so a rank change never breaks a link. Each run shows full run id, recorded branch, original Developer worktree path, presence-as-of-generation, accepted commits, results-directory link and PM artifact location. A recorded path is historical; absence at generation time is a separate observation and is not proof that `cleanup` ran.

---

## Stage 3 — production size and complexity, and elapsed time

**Goal:** replace a binary that measured tool availability with two measurements a reader can argue with.

Both are recorded per attempt by `dev_check.py`, against **that slice's own original baseline**, never the preceding attempt — a trajectory against a moving base would hide a regression introduced early and never touched again. Existing scope checks keep their PM epoch baseline semantics, unchanged. In a stop/restart case the stored grading baseline may have reset; that case is refused or labelled, never quietly reused as an apparent first-to-final improvement.

**ΔLOC — net physical lines added to production source.** `git diff --numstat <baseline> <attempt commit> -- <policy production globs>`, storing `added`, `deleted` and `net` separately, with test and documentation deltas recorded separately and never netted against production. Cheap, auditable, and needs no new analyzer. It is labelled explicitly as physical lines: SLOC-excluding-comments is a reasonable later alternative under one pinned analyzer on both revisions, but the two definitions are never mixed.

**ΔCC — total production function cyclomatic complexity at endpoint minus baseline.** Reuse the configured `health_script`, run as `analyze --all --json` at both revisions, summing `facts.python.functions[].cyclomatic` (and `facts.lizard.functions` for non-Python) over the production globs. Also store absolute endpoint total, maximum single-function complexity, and added/removed function counts, production and test kept separate.

Three constraints, each of which the evaluation establishes:

- **Do not derive this from `candidates`.** That list is capped at `limit_per_family = 5`; counting it would turn a display cap into a scoring ceiling and would omit removed functions entirely.
- **Do not write a parallel complexity implementation.** The differential `--base` invocation dev_check already makes narrows scope to changed files and cannot supply a complete baseline total, which is exactly why the absolute run is needed at both ends.
- **ΔCC is descriptive, not a penalty.** Splitting one function into three raises total complexity through added function-entry counts alone. It is displayed, not scored.

Cache the baseline measurement per `before_head` within a run — a slice's baseline is constant across an epoch, so this is one extra absolute analyzer run per attempt plus one per epoch, not two per attempt.

`policy.yaml` gains the definitions (the path globs are policy, not investigation constants):

```yaml
measurement:
  production_paths: ["src/**/*.py"]
  test_paths: ["tests/**/*.py"]
  doc_paths: ["docs/**/*.md", "*.md"]
  loc_definition: net_physical_lines   # git --numstat added - deleted
  metric_version: 1
```

Lint survives as a **hygiene/coverage badge**, not a score, and code-health's synthesized `verdict = "pass"` stops being read as a quality verdict — the honest reading of exit 0 is "the tool ran and produced a payload", which is what it will now say. Scope violations become an exceptions list in run details with a top-level alert when nonzero. Scope leaving the numerical ranking does not weaken drift review: trial 7's own PM feedback describes edits *inside* authorized files that a mechanical file-surface check cannot see, which is precisely why the reviewer role stays.

Store measurement seconds and the `metric_version` with every generated report, so a metric-version rebuild is distinguishable from a new trial.

---

## Stage 4 — panel-preserving review records, parser repair, PM judgments

**Goal:** one record per actual commission, and PM's own structured judgments surfaced as what they are.

### Sheet schema: one record per commission

The per-attempt `drift_review` / `code_review` single slots are replaced by a `reviews` list, one entry per successful commission, keyed by PM's own stable `review_id`. `select_canonical_reviews` becomes `select_review_commissions` and stops collapsing on `(attempt, skill)`. Each record carries `review_id`, `skill`, `tool`, `model`, `effort`, `head`, `before_head`, `grants_seen`, `at`, the event index, report ref and verified sha256, and either the parsed verdict/findings or a named parse error.

Two reviewers on one submission are two records. A re-commission of the same skill against the same submission is retained with its own `review_id` and marked as superseding the earlier one, so **a retry does not earn a second vote and two distinct reviewers never overwrite each other**. Report reads still verify the recorded sha256 first — the mirrored copy is written non-atomically, and that remains a correctness requirement.

`open_after_this_attempt` must now carry over per `(skill, reviewer identity)` lineage rather than per skill alone; mixing two reviewers' findings into one survival count would be meaningless. Document the chosen lineage rule where it is implemented.

Preserve the property `review_score` already guarantees and `AGENTS.md` calls out by name: **each attempt is processed independently**, so one attempt's missing sheet row is a reported, recoverable problem and never aborts before a later attempt that does have one. This was a real data-loss bug once.

### Parser repair, narrowly

Six of 32 harvested records in trials 4–7 are parse errors from real, human-usable reports — `_parse_findings` raises on any numbered line not matching `_FINDING_RE`. **Measured, not assumed:** scanning all 144 review reports across trials 4–11 for numbered lines the current regex rejects gives exactly three shapes, in descending frequency:

| Count | Shape | Real example |
|---|---|---|
| 23 | severity first, location **after** the title, backticked | `` 2. [P1] Preflight accepts a length-one vector `redshift` attribute despite the scalar-shape requirement `` |
| 8 | bold wrapping the whole finding, no backticked location at all | `1. **[P1] Fractional counts are incorrectly accepted by tolerant integer checks**` |
| 1 | bold around the severity only, then a backticked location | `` 1. **[P3]** `tests/test_merger_rate.py:52` Dead code in test fixture `` |

(A further 616 rejected numbered lines are ordinary prose lists in *other* sections, which the parser never reaches — it only parses the findings section. They are not a parser problem and must not be "fixed".)

Accommodate exactly these three shapes where severity and location are recoverable unambiguously; shape 2 has no location at all, so it must record the finding with an explicitly absent location rather than inventing one. Use the real reports above as fixtures.

Separately, drift reports also fail on `'Authorization Gate' section has no '- Verdict:' line` — `_extract_verdict` requires a literal `- Verdict:` bullet for drift-audit only. Check the real reports before changing it: the verdict may be present in another form, in which case recover it, or genuinely absent, in which case the named error is correct and must stand. Keep every other malformed line a named parse error. **Separate parser coverage from reviewer reliability** in the display: a bench parser rejecting a readable report is not evidence the reviewer was bad. Do not add an LLM parser, and never let failed extraction become zero findings.

### PM judgments

Harvested through `bench_lib.active_judgments`, joined by `(run_id, slice.id, review_id)` for reviewers and `(run_id, slice.id, submission.origin_event.index)` for the Developer — **never by list position, model, or artifact content**. The Developer join converts the stored absolute event index to the bench's own attempt ordinal via `bench_lib.attempt_ordinal(..., before_index=...)`; note `bench_lib.read_events` must filter to dict lines exactly as `pm_lib.state.read_events` does, or the indices will not correspond.

Validation is loud: an unknown `review_id`, a duplicate, an impossible rank, or a head/role mismatch is a named error, never a silently dropped judgment.

Display:

- **Code reviewers** — normalized rank points from PM's `rank_groups`: for a panel of N and 1-based rank r, `(N - r) / (N - 1)`; ties share the mean occupied rank; **N = 1 has no comparative score, not 1.0**. Average a reviewer's eligible round scores within a run, then average run means, showing both round and distinct-run counts (documented as the chosen estimator, not mixed with a straight round mean). Show unique opponents and observed panel sizes, and mark disconnected comparison groups not globally comparable. Normalized rank does not correct for opponent strength; Bradley–Terry / Plackett–Luce are not worth their identifiability and sparse-data cost at this sample size. **In this cohort every panel is a singleton, so this table will read "single reviewer — no comparative score" for every row, with a sentence explaining that reviews did occur.**
- **Drift reviewers** — mean 0–2 rating, plus `unacceptable / assessed` shown alongside, because a mean alone can conceal a catastrophic 0 among 2s. Never translate a drift FAIL into a poor rating: **finding a real violation is good reviewing.** This never enters any Developer number.
- **Developer** — PM's 0–2 submission ratings surfaced as a labelled column (mean /2, n) and per attempt in the trajectory. An attempt PM never rated while it was current is **explicitly unjudged**, never inferred — `pm_lib` refuses historical backfill by construction, so a gap here is a real gap.
- A timed-out or unreadable review is an explicit reliability outcome, never silently ranked last on substantive quality.

PM narrative (`model-performance.md`) stays quoted and labelled, never a metric source. Trial 7's prose says "6 total attempts (3 each)" where the event log shows eight, [4,4] — counts are always derived structurally.

---

## Stage 5 — regrade, docs, and close out

1. **Regrade the full cohort**, one run per invocation: `python tools/cohort_run.py analyze --dev-repo substrate/relative-velocity-trial-<N>` for N = 4…11. Trials 8–11 have never been graded at all. Watch specifically for G16 walk refusals on trials 8 and 9 (8 attempts on slice 1 each) — a refusal there means only the final attempt gets a row, which makes that run unranked for first submission with a named reason. That outcome is correct behaviour, not a bug to work around.
2. **Read `results/leaderboard.md` end to end** against the run evidence before trusting it. The evaluation's numbers for trials 4–7 (first → final correctness 71.33 → 71.77, 79.66 → 86.79, 88.43 → 88.43, 90.95 → 91.39; attempts [5,2], [4,4], [2,3], [4,4]; elapsed 53m15s, 52m45s, 57m04s, 74m06s) are an independent cross-check on the new pipeline: correctness and attempt counts must reproduce exactly, since neither definition changed.
3. **Documentation.**
   - `docs/MODE2-REWRITE-PLAN.md` is the authority and must be amended, not just appended to: rewrite §6's Tool 4 and Tool 5 sections (the composite paragraph is normative and now describes something that no longer exists), update §7's sheet schema for the `developer` block and the `reviews` list, and add §8 entries for the new resolved questions — identity resolution, size/complexity replacing the binary quality score, panel-preserving review records, and PM judgment consumption. G3 ("deterministic quality is an imperfect proxy") is the existing hook for the quality rewrite and should be resolved rather than left standing.
   - `README.md`: the tool table's `leaderboard.py` row, the repo-layout block, and step 4's description of what `leaderboard.md` contains.
   - `AGENTS.md`: the scoring bullets that describe the composite and the sheet schema.
   - `docs/LEADERBOARD-EVALUATION-2026-09-13.md`: leave the analysis intact as the record of why this work happened, but fix its one dangling link — it references `PROJECT-MANAGER-REVIEW-JUDGMENTS-PROMPT.md` as a sibling doc, and that file is in `archive/`. Note in place that the PM feature it proposed has since shipped, and that PM additionally delivered Developer judgments the report did not anticipate.
   - `HANDOFF.md` before every commit, with its commit hash refreshed after. It is gitignored on purpose; preserve its time-scoped historical prose rather than rewriting it as current state.
4. **Lint clean, not merely improved** (`lint` skill or `lint.py check`), and the full suite green, before each stage's commit. Ask before committing; commit to `pm-eval-v2`; never `--no-verify`; never amend.

---

## Verification, targeted at the real risks

Test against fixtures and copies. **Never write a synthetic row into `results/`**, and never insert fictional reviewer results anywhere. Hypothetical multi-reviewer fixtures are the right way to exercise points, ties, variable panel sizes and disconnected groups, precisely because no real panel exists yet.

| Risk | Must be covered |
|---|---|
| Ordinals | 0-based machine ordinal vs 1-based display, in headings, rows and links; a stored sheet never renumbered |
| Review tables | Multiple reviews of one attempt; unreviewed attempts still shown; recorded event order vs role-name sorting; reviewer column holds a model, not a skill |
| Identity | Null, empty, conflicting; judgment filling a null harness field; attestation filling a gap; attestation conflicting with a record; `command_override`; superseded judgment ignored; effort unknown kept distinct; corrected identity round-trips with grades unchanged |
| Coverage | Missing attempt 0; incomplete two-slice coverage; a run `complete` followed by a later `stop`; eligible-vs-discovered counts |
| Arithmetic | Paired improvement computed within runs; equal, extreme and missing inputs; n=1 spread |
| Measurement | Baseline resets and deletions; tests and docs excluded from production size; ΔCC from a full baseline, not from `candidates` |
| Reviews | Two reviewers on one attempt; retry vs new participant; ties and singleton panels; malformed report vs genuine zero findings |
| Links | Stable anchors after a rank change and after a worktree disappears |

---

## Files

| Path | Change |
|---|---|
| `tools/bench_lib.py` | `active_judgments`, `resolve_developer_identity`; `read_events` filtered to dict lines to match PM's own index semantics |
| `tools/dev_check.py` | identity resolver at `main()`; structured `developer` block in `upsert_attempt`; ΔLOC/ΔCC collection; honest code-health verdict |
| `tools/review_score.py` | commission-keyed selection; parser accommodation; reviewer judgment harvest |
| `tools/model_report.py` | first/final/trajectory; timing; full review attribution; coverage and eligibility |
| `tools/leaderboard.py` | composite removed; correctness-first ranking; four tables; attempt vs review history; anchors and index |
| `policy.yaml` | `identity.corrections`, `measurement.*`, `leaderboard.expected_slices`; **delete** `weights`, `scope_violation_penalty`, `iteration_reference_attempts` |
| `tests/test_*.py` | per stage; `test_leaderboard.py:471` and `test_tool_contract.py`'s hardcoded `model=` both change |
| `docs/MODE2-REWRITE-PLAN.md`, `README.md`, `AGENTS.md`, `HANDOFF.md`, `docs/LEADERBOARD-EVALUATION-2026-09-13.md` | stage 5 |

## Style

`AGENTS.md`'s conventions and the `style-guide` baseline: `snake_case`; test names describing behaviour; docstrings where the contract is not obvious; `Path` over string paths; CLI parsing confined to `main()`; comments explaining contracts and non-obvious choices rather than restating code; Markdown prose never hand-wrapped. Match the surrounding modules' existing comment density and error-message specificity — these files explain *why* at every non-obvious decision, and new code should read the same way. Archive, never delete; run `git clean -ndx` before removing anything untracked.
