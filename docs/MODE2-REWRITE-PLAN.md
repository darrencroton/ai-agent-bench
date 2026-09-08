# Mode 2 Rewrite Plan: PM-Only Evaluation, Minimal Repo

**Status: design for a fresh session to implement on a new, empty branch. Not yet built. This document is the complete brief — a fresh session should be able to work from this alone, without re-reading the full history of `eval-consolidation-trial` or `main`.**

## 1. Why this exists (short version — see `HANDOFF.md`'s "corrected theory of the case" for the full history)

This repo exists to answer one operational question: which local model should sit in the Developer seat for a real, supervised, multi-step `project-manager` run on production scientific code? Prior real-world use of `relative-velocity` showed local models converge to scientifically-equivalent code but differ a lot in final quality and how many review/fix iterations it takes to get there. That variance, under a real PM process, is the thing worth measuring — and it needs to be measurable repeatably and offline, not by using a model "in the wild" on real production code and hoping.

Two prior attempts did not get there:

- **The five one-shot tasks (001-005)** tested a proxy (one-shot quality predicts iteration-need) but never validated it against a real PM run, and never established whether the five tasks were redundant or covered real gaps.
- **This branch's Mode 1 + Mode 2 infrastructure** (profile view, structural scoring, fail-closed provenance) never got to a single real Mode 2 data point, and — confirmed by direct code inspection — measures nothing about iteration count or per-checkpoint quality trajectory anywhere. It scores a finished diff, once, exactly like Mode 1 does.

**Decision made this session: abandon that path. Start over on a new branch, scoped only to what this design needs.** Everything not needed for that is left behind — not deleted from history (it stays on `main` and `eval-consolidation-trial`), just not carried forward.

## 2. What this branch is for, precisely

Run the `relative-velocity` 2-slice merger-rate plan (`docs/MERGER_RATE_PLAN-2SLICE.md`) as a real, **completely normal, unmodified** `project-manager` Mode B session, rotating local models through the Developer seat under one (probably frontier) PM supervisor, with **deterministic scoring instrumentation that externally watches and harvests the PM toolkit's own artifact trail** — not a replacement for the PM skill's own workflow, and not instructions injected into the PM's own decision-making at all: the launcher prompt is `SKILL.md`'s standard, unmodified text (see §7 and gap G13 on why both slices' own frozen Risk Flags very likely already require mandatory review without needing anything added to the prompt — pending confirmation against `pm_lib`'s actual plan parser, not asserted as certain). The PM skill already runs Developer → review → accept/reject per slice and already writes a structured record of every attempt and review to disk; this repo adds four small scripts (one of which handles both review types, parameterized — see §7) plus a driver that reads that record as it's produced, so every iteration is scored, not just the final result.

This directly closes last session's biggest identified gap: because the scoring sheet is updated every time around the review loop, the **iteration count and the quality trajectory across iterations fall out of the data automatically** — that was the one thing neither Mode 1 nor the old Mode 2 ever captured, and it was the operator's original motivating observation about local models in production use.

## 3. Design principles (binding for the fresh session)

- **Minimum, no dead code.** Every file in the new branch must be load-bearing for running the 2-slice plan and scoring it. If a prior file's *pattern* is worth keeping (fail-closed scope checks, provenance hashing, externalized policy), reimplement it fresh and small — do not carry over a script written for a different purpose (five-task grading, one-shot batch running, composite scoring) and adapt it in place. This applies most strongly to Tool 1 below — it must be purpose-built for this single plan, not a repurposed `grade_trial.py`.
- **Deterministic first.** Correctness and quality should be measured by tools, not by asking a model to judge a model. Reach for an LLM judge only if a deterministic proxy is tried and found insufficient — do not pre-build judged scoring on spec.
- **Externalize policy as data.** Whatever weights, thresholds, or gates the scoring uses belong in a small policy file (YAML), never hardcoded in the tools. This is the one thing worth keeping from the old repo's philosophy regardless of the rewrite — it's cheap and it's correct practice, not scope creep.
- **Provenance on every record.** Every scored artifact should record: the plan file's hash, the policy file's hash, the base/frozen-substrate commit or tag it was checked out from, the PM skill version if identifiable, and the branch/commit SHA being scored. This is what lets a later comparison detect "the rules changed" instead of silently mixing incompatible cohorts.
- **Isolate every grading run in its own worktree — and the whole PM run in real containment.** The dev-side tool will run many times against an evolving branch (once per review round); each run must check out the branch's current HEAD into a fresh, disposable worktree, never the PM's live working directory. That directory separation is necessary but, per gap G12, not sufficient on its own: `project-manager`'s own documentation requires the entire PM/Developer/Reviewer run to execute inside a container or VM, since a fully-autonomous Developer session can otherwise reach anywhere else on the host, hidden tests included. Reimplement the worktree pattern minimally (don't drag over `worktree_lifecycle.py` as-is); resolve the containment boundary itself as an architecture decision (G12), not an implementation afterthought.
- **The PM skill's own workflow is out of scope.** This repo does not reimplement Developer/reviewer orchestration, slice sequencing, or acceptance logic — `project-manager` Mode B already does that. These five tools are instrumentation invoked at its checkpoints, nothing more.

## 4. Branch mechanics

Create a new branch from an orphan root (`git checkout --orphan <name>`), remove everything, then bring in only:

- This document (as the design brief for the fresh session).
- The 2-slice plan file, or a pinned reference to it (`relative-velocity`'s `docs/MERGER_RATE_PLAN-2SLICE.md` at a specific commit) — decide whether to vendor a copy in or reference it live; vendoring in a copy at a pinned commit hash is safer against the plan file changing under you mid-cohort.
- Task 001's `hidden_tests/test_hA.py` and `hidden_tests/test_hB.py` **as a starting point only** — see §7, Tool 1, for why and how these need to be re-partitioned by slice rather than used verbatim.
- Whatever small provenance/worktree-isolation helper functions are worth a fresh, minimal reimplementation (a few dozen lines each, not whole modules).
- `requirements.txt`, `.gitignore`, and any repo-level config actually needed (ruff config, if lint is used — see Tool 1).

Everything else — `eval/tasks/002-005`, the composite/profile scoring machinery, `aggregate.py`, `branch_check.py`, `structure.py`, the 219-record cohort, all of `docs/` except `BACKGROUND.md`-equivalent scientific reference material — stays on `main`/`eval-consolidation-trial` and is not carried forward. Nothing is lost; it's just not this branch's concern.

Suggested branch name: `pm-eval-v2` (or similar) — not fixed by this document, name it whatever reads clearly next to `main` and `eval-consolidation-trial`.

## 5. Proposed repo layout (new branch)

```text
docs/
  MODE2-REWRITE-PLAN.md        (this file, carried in)
  MERGER_RATE_PLAN-2SLICE.md   (vendored copy, pinned to a commit hash — record it in the file)
policy.yaml                     (all weights/gates/thresholds — see §8)
tools/
  dev_check.py                  (Tool 1: correctness + independent quality)
  review_score.py                (Tools 2/3, merged: --skill drift-audit|code-review — see §7, identical harvesting logic parameterized by which report it's reading)
  model_report.py                (Tool 4)
  leaderboard.py                  (Tool 5)
  run_seat.py                     (the driver, §7a)
hidden_tests/
  slice1/                       (adapted from Task 001's Part 1+2 tests)
  slice2/                       (adapted from Task 001's Part 3 tests)
results/
  runs/<run_id>/slice-<n>.json   (one cumulative scoring-sheet document per run+slice, matching §6 exactly — not one file per attempt)
  reports/<run_id>.md            (Tool 4 output — filename uses run_id, never a raw model name: see note below)
  leaderboard.md                  (Tool 5 output)
```

**Note on model names as identifiers:** a model name (e.g. `opencode-go/mimo-v2.5-pro`) can contain `/`, which would silently create unintended nested directories if used literally as a path component. Every on-disk path uses `run_id` (assigned by `pm.py init`, opaque and filesystem-safe); the human-readable model name is a *field inside* the JSON/Markdown content, never part of a filename or directory name.

## 6. The scoring sheet artifact

One JSON document per (run, slice), appended to or updated across attempts — not overwritten, since the whole point is watching the trajectory. **Keyed by `pm.py`'s own run/slice/attempt identity**, not an independently invented counter — this is what lets Tools 1-3 attach data to the correct record without needing the PM to coordinate anything. **The exact keying mechanism (what identifies "this attempt" unambiguously and how a later attempt supersedes an earlier one on disk) is not fully specified here — see gap G13: it requires reading `pm_lib`'s actual state/event schema (`references/run-state.md`, or the source itself) before implementation, not guessing from `SKILL.md`/`README.md` prose alone.** Proposed shape (metrics are raw counts, not an invented composite — see the note after the schema):

```json
{
  "run_id": "...",
  "model": "opencode-go/mimo-v2.5-pro",
  "slice": 1,
  "run_status": "in_progress | accepted | stopped | attempt_budget_exhausted | infrastructure_failure",
  "attempts": [
    {
      "attempt": 1,
      "commit_sha": "...",
      "timestamp": "...",
      "correctness": {"hidden_tests_passed": 41, "hidden_tests_total": 46, "by_obligation": {...}},
      "quality": {"lint_findings_by_severity": {...}, "code_health_findings_by_category": {...}},
      "scope": {"violations": []},
      "drift_review": {"commissioned": true, "report_ref": "...", "findings_by_severity": {...}, "open_after_this_attempt": 2},
      "code_review": {"commissioned": true, "report_ref": "...", "findings_by_severity": {...}, "open_after_this_attempt": 1},
      "pm_decision": "steer"
    }
  ],
  "accepted_at_attempt": 3,
  "pm_model_performance_ref": ".pm/runs/.../model-performance.md",
  "provenance": {"plan_hash": "...", "policy_hash": "...", "base_commit": "...", "pm_skill_version": "..."}
}
```

**No invented composite score at the per-attempt level** (dropped `structural_score` from the first draft — codex's review correctly flagged it as an undefined conversion from raw lint/code-health output). Per-attempt data is raw and diagnostic; any weighting into a single number happens only in Tool 5's leaderboard pass, driven entirely by `policy.yaml`, never invented ad hoc inside Tool 1.

**`run_status` is mandatory, not optional**, and must come from `pm.py`'s own authoritative run state, never inferred from "did `run-report.md` get written" (see gap G14) — a stopped or attempt-budget-exhausted run is a normal, informative outcome and must be recorded as such, distinctly from a technical/infrastructure failure (harness crash, an unresolved trust dialog) — the latter must never silently become a low model score. This directly answers a lesson this repo's own prior history already learned the hard way (an overdue "systematic technical-failure rule" from the branch being superseded by this plan) — build it in from the start here rather than relearning it.

The number of `attempts` entries before `accepted_at_attempt` **is** the iteration-count metric. The sequence of `correctness`/`quality` values across them **is** the trajectory the operator wants to watch. `drift_review`/`code_review`'s `commissioned: false` (rather than a missing field) would record that PM chose not to commission review for that attempt — though for this specific plan, see §7: both slices' frozen Risk Flags very likely mandate independent review on acceptance (pending G13's parser confirmation), so `commissioned: false` is expected to be rare here in practice, and its presence in the schema is defensive, not evidence it's confirmed to never fire.

## 7. The five tools

**Design correction (this session, verified directly against `project-manager`'s own `SKILL.md` and `README.md` — the first draft of this plan was written one level of abstraction above where the PM toolkit actually operates, and a fresh-eyes review caught it):**

`pm.py` already writes a rich, structured artifact trail for every slice and every commissioned review, in two places: `<repo>/.pm/runs/<run-id>/slices/slice-<N>/` (the **live/current** attempt's `diff.patch`/`result.json`/`validation.md`/pane captures/`assessment.md` at the slice directory root, `review-<skill>-<tool>.md` + its `-prompt.md` for every commissioned review, and an `attempt-<n>/` subdirectory holding each **superseded** launch once a steer or relaunch replaces it) and `<git-dir>/pm/<run-id>/` (the authoritative originals, plus `notes.md`, `model-performance.md`, `run-report.md`).

**This changes the tools' job from "the PM actively invokes our scripts mid-workflow" to "our tooling externally watches and harvests the PM's own artifact trail as it's produced."** That is a better design on every axis that matters here: it doesn't depend on the PM correctly remembering to call unfamiliar tools at the right moments (a real reliability risk the first draft didn't account for); it doesn't require deviating from a normal Mode B run to force reviews that wouldn't otherwise happen; and it reuses the attempt/slice identity PM already tracks instead of inventing a parallel counter that the checkpoint tools would have to agree on independently.

PM runs `lint` and, when structure materially changes, `code-health` itself as part of its own assessment — but only as prose narration ("say in the assessment that you did"), with no guarantee of machine-readable counts. **Tool 1 does not harvest these from PM's assessment; it always invokes them independently and directly** (below) so every attempt of every model gets the same, comparable, structured measurement — PM's own mention of them is qualitative color for Tool 4's report, never the numeric source.

**Codex's independent review (this session) confirmed two more errors in the first correction pass, verified against the actual `SKILL.md`/`README.md` text, and one real simplification opportunity. All three are fixed below:**

1. Current-attempt artifacts live at the **slice directory root** (`prompt.md`, `diff.patch`, `validation.md`, `result.json`, `assessment.md`); `attempt-<n>/` specifically holds **superseded** launches (`README.md`'s Layout section). The previous correction's trigger path (`.../attempt-<n>/`) was wrong for the live attempt.
2. `result.json` (the Developer's own artifact) is written *before* PM runs `finalize`, lint, code-health, and any review — so a single "harvest quality from the assessment" trigger conflated two different points in time. Quality must be computed independently and directly, not scraped from PM's free-text `assessment.md`, which is prose reasoning with no guaranteed structured numbers in it (`SKILL.md`'s Workflow step 3 only requires PM to *say* it ran lint, not to record parseable counts).
3. Both slices of the 2-slice plan declare `Independent audit required: yes` in their own frozen Risk Flags — this almost certainly marks both elevated at parse time (`SKILL.md`: "`plan_risk` is derived mechanically at parse time"), which makes both drift-audit and code-review **mandatory on every acceptance regardless of Developer-model discretion**. The first correction's "tell the PM these are unproven models so it invokes standing-practice review" reasoning was solving a problem the frozen plan already solves on its own — delete it; it was itself a small piece of unnecessary complexity. Confirm the parse-time elevation mapping against `pm_lib`'s plan parser before relying on it (gap G13), but do not add anything to the launcher prompt to compensate for it either way.

### Tool 1 — `dev_check.py` (correctness; independent, always-computed quality)

**Trigger:** a new Developer commit is recorded for the slice — in practice, watch for the slice-root `result.json`/`diff.patch` to change. The exact authoritative signal (and how to tell a live attempt from one that has just been superseded) needs settling against `pm_lib`'s real state/event schema before implementation — gap G13.

**Correctness (the genuinely new work — PM has no reason to know about held-out tests):** check out the attempt's recorded commit into a fresh, disposable worktree (never PM's, the Developer's, or the Reviewer's own directory — and never on the same unsandboxed host as any of them; see gap G12 on containment), copy in that slice's hidden test file, run it, score pass/fail per acceptance-obligation group. Groups must be re-derived fresh against the 2-slice plan's own Acceptance Criteria (see G4) — do not assume Task 001's existing `acceptance_obligations` mapping carries over unchanged. Re-partitioning "Part 1+2 → Slice 1, Part 3 → Slice 2" still needs its own obligation-group definition, and should watch for the same kind of redundancy (several groups dominated by one capability) that motivated collapsing the old 3-slice plan into 2 slices in the first place — don't just inherit Task 001's six groups uncritically.

Task 001's `hidden_tests/test_hA.py`/`test_hB.py` are a legitimate starting point for the *test content* (pinned fixtures and exact values, validated against a reference solution — not "a script written for another purpose"), but the 2-slice plan's Acceptance Criteria diverge in specifics (e.g. stricter scalar-form rejections in `_load_pair_counts` and `merger_timescale_gyr`) — do not assume a 1:1 test mapping without re-validating against a fresh reference implementation of the 2-slice plan (gap G4).

**Quality (always computed independently, never scraped from PM's prose):** invoke the `lint` and `code-health` skills directly against the exact recorded commit, in the same disposable worktree used for correctness — the same tools PM itself would use, applied identically and comparably to every attempt of every model, rather than depending on whether a given attempt's PM assessment happened to mention them. Treat anything PM's own `assessment.md` says about lint/code-health as qualitative color for Tool 4's report, never as the numeric source.

**Scope discipline:** whether to harvest PM's own floor fact 5 result or recompute the authorized-surface diff independently is not decided here — it depends on whether `run.json`/the floor's output exposes a structured, reliably parseable result including recorded surface grants (gap G13). Recomputing independently is simple for the frozen plan surface alone, but the *effective* surface also includes any grants PM issued mid-run, which live in PM's own state — so an independent reimplementation that ignores grants would be wrong, not just redundant. Investigate before choosing; do not default to reimplementing without checking whether that duplicates (and risks diverging from) logic PM already gets right.

**Output:** appends one entry to the scoring sheet (§6), keyed by `(run_id, slice, attempt)` per whatever G13 settles on.

### Tools 2/3 — `review_score.py --skill drift-audit|code-review` (harvest, not invoke; one script, not two)

**Simplification from the first correction pass:** Tools 2 and 3 were specified as separate scripts performing identical harvesting logic against two different report-filename patterns. That's duplication with no behavioral difference — one script, parameterized (or auto-detecting) by which `review-<skill>-*.md` it's reading, does the same job with less code. The operator's "one for drift review, one for code review" framing still holds at the level of *what gets scored*; it doesn't require two files.

**Trigger:** a new `review-drift-audit-*.md` or `review-code-review-*.md` file appears at the slice directory root. The exact moment this file becomes readable relative to PM's `review` command finishing is not confirmed from `SKILL.md`/`README.md` alone — part of the same artifact-lifecycle investigation as gap G13, not an independent question. What's established with more confidence (though still pending G13's parser confirmation, per the note in the Codex-review section above): this is *expected* on every accepted attempt for both slices of this specific plan, since their frozen Risk Flags declare independent audit required — not merely PM's per-attempt discretion. So the scoring sheet's `commissioned: false` case should be rare-to-absent here in practice; the field stays in the schema defensively, not because it's confirmed to never fire.

**Purpose, and the open problem the operator flagged**, unchanged: scoring the *quality* of a review is genuinely harder than scoring code, because there's no ground truth for "did the reviewer catch everything that mattered" without already knowing the answer.

**Recommended approach — do not attempt a holistic quality score. Extract deterministic structure instead:**

- Parse the review report's findings: count by severity (P1/P2/P3 or equivalent), by category, how many were subsequently fixed vs. left open into the next attempt (directly comparable across attempts because PM's own directory structure already numbers them).
- This gives a **coverage/thoroughness proxy**, not a claimed "goodness" score for the reviewer model.

**Deprioritized, not recommended for the first build (gap G1, revised):** the first correction pass floated seeding known, hand-placed defects into the frozen substrate to get an objective per-defect catch rate. Given both slices very likely mandate real, independent review on real Developer-introduced work at acceptance (not synthetic) — pending G13's confirmation, per §7 — this is now lower priority than originally framed — `SKILL.md` itself notes real reviewers already miss real mechanical findings routinely ("11 of ~14 non-correctness findings were mechanical, and both commissioned reviewers missed every one," observed across five real runs), so there's no shortage of genuine signal to harvest without inventing synthetic defects. Do not build this unless the coverage-proxy signal, once real data exists, proves insufficient — building it upfront would be exactly the overtesting the operator's design principles warn against.

**A third, non-deterministic but legitimate signal, per the operator's own field experience (this session):** the operator reports that in practice the PM is a reasonably reliable judge of *comparative* review quality specifically — noticing when one commissioned reviewer catches something other reviewers, or the PM itself, missed. That's a materially easier judgment than "was this review good in the abstract" (which G1 is right to distrust): it's a within-run delta a well-positioned reader (the PM, holding the code and every commissioned report at once) can actually make. This is already captured for free via `rate --text`/`model-performance.md` (§7, Tool 4) — subjective and not repeatable across runs the way the deterministic coverage-proxy is, but real signal, not noise to discard. Tool 4 should surface it labelled explicitly as PM's own subjective judgment, alongside (not blended into) the deterministic coverage numbers from this tool.

**Output:** appends the `drift_review`/`code_review` fields to the matching attempt's entry, matched per whatever G13 settles on.

### Tool 4 — `model_report.py` (run once the run reaches an authoritative terminal state — see gap G14, not merely "once `run-report.md` exists")

**Purpose:** gather every attempt's scoring-sheet data for one model's full run into a single per-model report: final correctness/quality, attempt count per slice and total, review-finding trends across attempts, injected-defect catch rate if Tool 2/3's optional addition is built. PM's own `rate --text` output (`model-performance.md`, written against `references/model-performance-rubric.md`) rates **every model that operated in the run — the Developer and each commissioned Reviewer role, not the Developer alone** (`SKILL.md`'s Workflow step 5) — fold in all of it, not just the Developer's portion, since the Reviewer ratings are exactly the PM's-comparative-judgment signal described under Tools 2/3 above; discarding them here would silently drop the signal the revision added.

**Output:** `results/reports/<run_id>.md` — never a raw model name (see §5's note on filesystem-safe identifiers); the model name is a field inside the report's content.

### Tool 5 — `leaderboard.py` (run after each model's report is done)

**Purpose:** rebuild the cross-model summary and ranking from every `results/reports/*.md`/scoring-sheet on disk, using `policy.yaml`'s weights, placing each newly run model against whatever's already in the table.

**Output:** `results/leaderboard.md`.

**Open question (gap G7), unchanged:** PM-only, or combined with a retained one-shot screen — depends on G6.

## 7a. The driver: one PM harness session, watched externally, run X times

**Corrected twice now** — once for conflating the PM's own harness invocation with the Developer's, and again (this session, by an independent Codex review) for a wrong claim about which sessions actually use tmux:

- **One outer harness session runs the PM itself**, using `SKILL.md`'s standard, unmodified launcher prompt — this is the only harness process the driver launches directly.
- The PM agent, inside that session, issues `pm.py` CLI commands (`init --harness <developer-harness> --model <developer-model> ...`, `start-slice`, `observe --wait`, `review`, `finalize`) as ordinary tool calls. `pm.py` itself launches the **Developer session in tmux** (`start-slice`) — `git`, `tmux`, and Python ≥ 3.13 are all hard requirements of the toolkit (`README.md`'s Requirements section). **A commissioned Reviewer, however, is not a tmux session**: `review` runs it as a one-shot subprocess that blocks until it exits (`README.md`'s CLI table and `SKILL.md`'s Workflow step 3) — correcting the first draft's claim that both seats run in tmux. The driver never touches Developer or Reviewer sessions directly either way; that is entirely `pm.py`'s job, already built and correct.
- **The driver's own job, concretely:** (1) prepare a fresh `relative-velocity` checkout/branch off the pinned frozen base commit and pass its path into the PM's launcher prompt; (2) launch the one outer PM harness session unattended, with this run's Developer harness/model filled into the launcher's bracketed values, **inside the containment this design requires (gap G12)**; (3) run a watch loop over `.pm/runs/<run-id>/` (and, once the run ID is known, `<git-dir>/pm/<run-id>/`) that triggers Tools 1-3 as their trigger artifacts appear (§7); (4) once the run reaches an authoritative terminal state (gap G14 — not simply "`run-report.md` exists," which `status --report` can regenerate on request and which a `stop` may not produce automatically), run Tool 4 then Tool 5.
- **Trust dialogs are a confirmed blocking condition on a fresh checkout — verified directly in `README.md`:** "If a harness displays a directory-trust or permission prompt, the PM stops and leaves that approval to the human... Autonomy flags do not clear a folder-trust dialog." A fresh worktree per run is a plausible trigger for a first-use trust prompt in some harnesses, and the README is explicit that neither the PM nor any wrapper around it may acknowledge such a dialog programmatically. **Which harnesses actually trigger this, and whether a one-time pre-trust of a stable parent directory actually prevents it, is not established by `SKILL.md`/`README.md` and must be empirically verified per harness** (softened from the previous draft's unverified "several harnesses" claim, per Codex's review) — do this first, before assuming any run in the rotation is unattended end to end.
- Repeat once per candidate Developer model (the "X times"). Repeats per model beyond that: gap G11.

## 8. Gaps and open questions (the critique requested — none of these are resolved by this document; the fresh session should either resolve them up front or explicitly defer them)

- **G1 — Review-quality scoring is inherently weak without ground truth**, as the operator already suspected. §7's coverage-proxy approach is a reasonable default; the injected-defect option is stronger but adds real setup cost per slice; PM's own comparative judgment (`rate --text`, per the operator's field experience that PM reliably notices when one reviewer catches what others missed) is a third, legitimate-but-subjective signal worth surfacing labelled as such, not blended into the deterministic numbers. Decide the mix before building Tools 2/3, not after.
- **G2 — PM acceptance itself is unscored.** This design treats the PM's own judgment as ground truth (the PM is presumably a strong frontier model, and this study is about the Developer seat, not the PM seat). That's a reasonable scope boundary, but it should be stated explicitly rather than left implicit, since a future extension ("which frontier model makes the best PM") would need different instrumentation.
- **G3 — Deterministic quality is a known-imperfect proxy.** Lint + structural metrics correlate with real code quality but not perfectly — that's exactly why the old repo had a judged `maintainability`/`readability` category alongside them, with all the cost and subjectivity that brought. Starting deterministic-only is the right call per the design principles above, but the fresh session should watch for cases where the deterministic score obviously disagrees with what a human reader would say, and treat that as a signal to reconsider — not silently accept a bad proxy.
- **G4 — The hidden-test re-partitioning by slice has not been validated against a reference solution.** Task 001's tests were validated against a reference implementation of Task 001's spec, not the 2-slice plan's slightly different Acceptance Criteria (they diverge in a few specifics — e.g., stricter scalar-form rejections). Before trusting Tool 1's correctness scoring, write a reference implementation of the 2-slice plan and confirm every re-partitioned hidden test passes against it and fails under a deliberately broken variant — the same validation discipline `AGENTS.md` already requires for any task's hidden tests, applied here to a plan's slices instead of a task.
- **G5 — Reviewer/Drift seat models: fixed or varied?** The operator's plan mentions rotating the Developer seat across 3 local models under one frontier PM. It does not say whether the drift/code-reviewer seats are held constant across all three runs (needed to isolate the Developer as the only variable) or also rotated. This must be pinned explicitly before running anything, or results will be confounded.
- **G6 — Is a cheap one-shot pre-filter still wanted?** Last session's conversation weighed "abandon PM" against "PM only." This message describes tooling exclusively for the PM path, with no mention of retaining any one-shot screening step to select which local models are worth the (still multi-hour) PM run. If there are more than 3 candidate local models in play, a cheap pre-filter (even just Task 001 one-shot, unmodified, sitting untouched on `main`) may still be worth running before committing a candidate to a full PM cycle. Not decided here — confirm with the operator before assuming PM-only replaces screening entirely.
- **G7 — Leaderboard scope**, see Tool 5 above — PM-only or combined with retained one-shot data. Depends on G6.
- **G8 — Vendoring vs. referencing the plan file.** §4 recommends vendoring a pinned copy of `MERGER_RATE_PLAN-2SLICE.md` into this branch so a later edit to it in `relative-velocity` doesn't silently change what's being scored mid-cohort. Confirm this is acceptable — the alternative (reading it live from `relative-velocity` each time) is simpler but loses that guarantee.
- **G9 — Worktree/checkout mechanics for a live PM run vs. a graded one-shot run differ.** Mode 1's worktree pattern assumes the model only ever sees `TASK.md`. Here, the Developer and PM are working in a real, fully-visible `relative-velocity` checkout — hidden tests can only stay hidden by never being present in that checkout at all, only injected into Tool 1's own disposable worktree copy. Confirm the PM/Developer's actual working directory is never the same directory Tool 1 checks out into.
- **G10 — Unattended, multi-phase harness automation risks a real, confirmed failure mode (trust dialogs) on a fresh worktree; the mitigation is unverified.** `project-manager`'s `README.md` confirms a directory-trust or permission prompt stops the PM run and requires a human, and "autonomy flags do not clear a folder-trust dialog." Since this design creates a fresh checkout per run (§3's isolation principle), the very first harness launch against each new directory is a plausible trigger. §7a's proposed mitigation (a one-time, per-harness manual trust setup on a stable parent directory) is a reasonable hypothesis, not a documented guarantee (a second independent review flagged the first draft's "several harnesses" phrasing as overclaiming what the source docs establish) — verify it empirically per harness before building anything else.
- **G11 — Repeats per model.** Does each candidate Developer model get exactly one PM run through the plan, or several for variance (mirroring Mode 1's "3 trials per task" convention)? A full PM run is far more expensive per attempt than a one-shot trial, so this is a real cost/reliability tradeoff, not a default to inherit unexamined from Mode 1.
- **G12 — Filesystem/process containment is required, not optional, and this document's first two drafts underestimated it.** `project-manager`'s `README.md` states plainly: "The harnesses no longer constrain what a Developer can touch outside the repository, and the floor cannot see it either... so a separate checkout is not containment: nothing stops a Developer reaching the rest of the host," and instructs running the whole PM toolkit "inside real process and filesystem isolation — a container or VM." A Developer session launches at full autonomy (`bypassPermissions` or equivalent) specifically because nobody is present to answer a permission prompt — which also means nothing stops it reading hidden test files anywhere else on the same host if it goes looking. Directory separation between the PM/Developer's worktree and Tool 1's disposable grading worktree (the previous drafts' G9) is necessary but not sufficient: the entire PM run (PM, Developer, Reviewers) must run inside a container or VM, with hidden tests and this repo's own tooling kept outside that boundary. Resolve the concrete isolation mechanism (what runs inside the container, what runs outside, how they exchange the git branch and scoring data) before writing Tool 1.
- **G13 — The authoritative attempt/review artifact schema is not fully known from the two documents this design was written against, and two real errors already resulted from guessing at it.** `SKILL.md` and `README.md` describe the artifact trail at a level that turned out to be insufficient to correctly design a trigger for "a new attempt exists" or to decide whether scope-discipline data should be harvested from the floor's own output or recomputed independently (which itself depends on whether recorded surface grants are exposed in structured form). Before implementing the watch loop, Tool 1, or the review harvester, read `references/run-state.md` and, if needed, the relevant `pm_lib` source directly — do not proceed on inference from prose alone a third time.
- **G14 — Run completion/termination must be read from `pm.py`'s authoritative state, never inferred from artifact existence.** The first two drafts both treated "`run-report.md` exists" as the completion signal; it doesn't necessarily hold for every path (`status --report` regenerates it on request, and a `stop` preserves evidence without a documented guarantee of an automatic fresh report). Define, from the real state schema (see G13), the exact terminal states this design must recognize (accepted, stopped, attempt-budget-exhausted, and an infrastructure/technical failure distinct from all three) and drive Tool 4/5 off that, not off a file's presence. An infrastructure failure (a harness crash, an unresolved trust dialog, a killed process) must be recorded as exactly that in `run_status` and must never be silently scored as if the model produced bad code — a repeat of a mistake this repo's own prior history already made and never fully fixed (the "systematic technical-failure rule" that was still overdue on the branch this design replaces).

## 9. What's reused vs. freshly written (explicit, per the "minimum, no dead code" principle)

| Component | Disposition |
|---|---|
| `relative-velocity`'s frozen `src/`/`tests/` substrate, `docs/BACKGROUND.md` | Reused as-is (it's the frozen baseline pipeline itself, not eval infrastructure) |
| `MERGER_RATE_PLAN-2SLICE.md` | Reused as-is (vendored copy, pinned commit — see G8) |
| Task 001's `hidden_tests/test_hA.py`/`test_hB.py` | Reused as a starting point for **content** (pinned values/fixtures), re-partitioned by slice, freshly validated against a reference solution of the 2-slice plan (G4) — not reused as running code unmodified |
| `grade_trial.py`, `branch_check.py`, `run_trial.py`, `run_batch.py` | Not carried forward. Their worktree-isolation and provenance-hashing *patterns* are reimplemented fresh and minimal inside Tool 1, not imported. Their scope-diff-against-frozen-list pattern is reimplemented fresh **only if** gap G13 shows PM's own floor output isn't reliably harvestable — do not assume reimplementation is the answer before checking |
| `structure.py`, `profile_view.py`, `aggregate.py`, `eval/rubric.yaml`, `eval/profile.yaml` | Not carried forward. `policy.yaml` replaces them, scoped to only what this plan's five tools need |
| The 219-record cohort, `eval/leaderboard.md`, `eval/leaderboard_summaries.yaml` | Not carried forward — no standing value of their own (per this session's corrected framing), stay on `main`/`eval-consolidation-trial` |
| `validate_obligations.py`, `reference_check.py` | Concept reused informally (G4's validation discipline), not the code itself — the fresh session should write a small equivalent scoped to two slices, not import the five-task version |
| The `lint` and `code-health` skills | Reused directly as invoked tools, not reimplemented — invoked independently and directly by Tool 1 on every attempt (§7), never scraped from PM's own prose assessment |
| `project-manager`'s own `.pm/runs/<run-id>/` and `<git-dir>/pm/<run-id>/` artifact trail | Harvested as the primary data source for Tools 1-4 (attempts, diffs, floor results, review reports, `model-performance.md`) — not duplicated by independent re-computation except where noted as a fallback |
| Judged `readability`/`maintainability` (LLM judge) | Not carried forward at all — see design principle "deterministic first" and gap G3 |

## 10. Next steps for the fresh session

This document has now been through two internal correction passes and one independent external review (Codex, `gpt-5.6-sol`, high effort) — see the git history of this file for what each pass changed and why. The remaining gaps are real, not polish; do not start writing tool code before working through them in order.

1. **Read `project-manager`'s `references/run-state.md` and, if it doesn't fully answer G13/G14, the relevant `pm_lib` source directly.** Two rounds of design errors in this document came from inferring artifact/state mechanics from `SKILL.md`/`README.md` prose alone when the real answer needed the actual schema. Do not make that mistake a third time. This resolves G13 and G14 and is a prerequisite for designing Tool 1's trigger, the scope-discipline decision, and the driver's completion check correctly.
2. **Resolve the containment architecture (G12)** — what runs inside a container/VM (PM, Developer, Reviewers) versus outside (Tool 1's grading worktree, the hidden tests, this repo's own tooling), and how they exchange the git branch and scoring data. This is architectural, not an implementation detail to defer.
3. **Validate G10** empirically: does a one-time trust setup actually let a fresh worktree launch each harness in play without a directory-trust prompt stopping the PM run? Then confirm a full `project-manager` Mode B session can run end-to-end through at least one harness CLI with zero further human input across every phase. If either doesn't hold, that's a blocker for this entire plan, not something Tools 1-5 can work around.
4. Resolve gaps G5, G6, G8, G9, G11 with the operator before writing any code — they change what gets built, not just how.
5. Create the orphan branch per §4.
6. Write a reference implementation of the 2-slice plan and validate the re-partitioned hidden tests against it (G4) before trusting Tool 1's correctness scoring.
7. Build Tool 1 first (it's the only one on the critical path for even a single manual dry run of the loop); the merged review harvester next; the driver (§7a) once both checkpoint tools work standalone; Tools 4-5 last, once at least one full model run exists to report on.
8. Do a single, real, manual dry run — one local model, one slice, through the full loop by hand, without the driver — before automating anything. Do not trust a fresh implementation's self-report without independently checking a real scoring sheet against what actually happened in the PM run.
9. Only after a manual dry run succeeds, build and trust the driver's automation of the loop end to end.
