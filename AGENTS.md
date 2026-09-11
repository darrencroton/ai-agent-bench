# AGENTS.md

Guidance for AI coding assistants (Claude Code, Codex CLI, and equivalents) working in this repository. `README.md` is the user-facing entry point; this file is the contributor contract. `docs/MODE2-REWRITE-PLAN.md` is the authoritative design and wins over both.

## What this repo measures, and what you are doing in it

This bench measures the Developer seat of a real `project-manager` Mode B run: which local model produces good code, and how many supervised iterations it needs to get there. **You are working on the measuring apparatus, never inside the thing being measured.** Adding a task, fixing a tool, extending the scoring sheet is ordinary software engineering on the harness. Never help a run along, never re-run a graded attempt and record it as the same one, never hand-edit a scoring sheet.

## The boundaries that make the measurement valid

- **Everything this repo does to a PM run is read-only.** Read `run.json` and `events.jsonl`; never write PM state, never hold or ask for a run token, never invoke `pm.py` as a subprocess. `pm_lib` is imported as a library for its plan and git helpers, nothing more.
- **Nothing is added to PM's launcher prompt, and PM is never asked to cooperate.** The premise is a completely normal, unmodified Mode B session; an instruction added to make measurement easier is an observer effect on the exact variable being measured. The operator launches PM personally — this repo has no code path that launches it, deliberately.
- **Grading happens in a disposable worktree**, never PM's, the Developer's, or a reviewer's directory. Under `ai-agent-sbx` that separation is enforced by construction; run bare it is only a convention, so do not describe it as equally safe in either case.
- **Held-out tests stay held out — with a known, accepted limitation of the bare (no `ai-agent-sbx`) case.** Under `ai-agent-sbx` the Developer session has no host filesystem reach at all, and the boundary is real. Run bare, the grading worktree is created with `git worktree add` from the Developer's own repo, so its path is listed by `git worktree list` inside that repo for the lifetime of the grading run — discoverable by a Developer session that goes looking, hidden test copy included. See `docs/MODE2-REWRITE-PLAN.md` §8's G9 entry; do not re-architect this, only avoid describing the bare case as equally safe.

## Working on the tools

- **Every path, threshold and tunable lives in `policy.yaml`**, never hardcoded in a script. A policy change must not require a code change. Do not invent scoring weights outside it.
- **Fail loudly and specifically.** Every error names the concrete file, path, node id or parameter. Never silently degrade, never guess a missing value, never write a partial result as if it were complete. An unavailable linter is recorded as unavailable, never as a clean pass; an unparseable review report is a named parse error, never zero findings.
- **Recompute what PM does not persist; reuse what it does.** The floor check's per-fact evidence is never written in structured form, so scope discipline is recomputed via `pm_lib.plan.effective_authorized_files` — the same function PM's own floor calls. Grants, reviews and the attempt counter *are* structured and authoritative in `run.json`; read those rather than deriving a parallel copy.
- **Respect the race-safe read patterns.** A new attempt is detected from an `events.jsonl` `launch`/`relaunch`/`steer` event and only then from `run.json`, because file rotation precedes the state write, which precedes the event. A review report is read only after verifying its recorded sha256, because the mirrored copy is written non-atomically. Both are correctness requirements, not optimisations.
- **Attempt numbering is PM's own 0-based counter** — 0 on the initial launch, +1 per relaunch and per steer. Every tool keys on it. A tool that quietly used a 1-based index would leave the scoring sheet silently incomplete rather than raising anything.
- **Minimum, no dead code.** Every file and function must be load-bearing. No speculative abstraction, no config key nothing reads, no compatibility shim for a case that cannot occur. Prefer one parameterised script to two near-identical ones — that is why the drift-audit and code-review harvesters are a single tool.
- **Deterministic first.** Scores come from tools that produce the same answer twice. A subjective signal (PM's own comparative rating of its reviewers) may be surfaced, labelled as such, but is never blended into a deterministic number: the two differ in repeatability, and averaging them destroys that distinction silently.

## Working on the hidden tests

- **The obligation partition in `hidden_tests/obligations.yaml` is the rubric weight.** Correctness is the equally weighted mean of the groups, so grouping decisions are weighting decisions. Balance by obligation importance, never by test or node count. `docs/OBLIGATION-GROUPS.md` records the current partition's reasoning; record any change there with the evidence that prompted it.
- **Re-validate after any change to the tests or the map**, in both directions: every collected node in exactly one group, no group naming a test that does not exist. `dev_check.py` enforces this and fails loudly. A stale map does not fail at grade time — it reads as a permanently low ceiling across many runs, much later, which is the failure mode this repo has already learned the hard way.
- **Validate a changed hidden test against a reference implementation before trusting it.** A wrong hidden test fails every model through no fault of its own, and one trial will not reveal it. `docs/reference-impl/README.md` has the reproduction recipe.
- `slice1/` and `slice2/` both contain a `test_hA.py` and a `test_hB.py`; a single pytest invocation over both fails collection. Grade one slice per invocation.

## The vendored plan is frozen

`docs/MERGER_RATE_PLAN-2SLICE.md` is a pinned copy from `relative-velocity` (see its `.provenance.md`). Do not edit it, and do not silently re-vendor it — a change there changes what is being scored mid-cohort. A defect found in its text is documented, not patched: one such defect is already recorded in `docs/reference-impl/README.md`, along with why the corresponding hidden test was deliberately left as it is rather than edited to match a self-contradictory bullet.

## Conventions

- **Archive, never delete.** Superseded files move to a dated directory under `archive/` (gitignored). This is not decoration: a blanket `rm -rf` while clearing this branch's working tree once destroyed the gitignored `HANDOFF.md`, which git offered no protection at all. Run `git clean -ndx` first to see what is untracked before removing anything.
- **Style** follows the `style-guide` skill's baseline: `snake_case`, test names describing behaviour, docstrings where the contract is not obvious, `Path` over string paths, CLI parsing confined to `main()`, comments explaining contracts and non-obvious choices rather than restating code. Markdown prose is never hand-wrapped.
- **Lint before committing** — `lint` skill or `lint.py check` directly. It must be clean, not merely improved.
- **Update `HANDOFF.md` before every commit**, and refresh its commit hash after. It is gitignored on purpose, so its local state is still required even though it is never staged. Preserve time-scoped historical prose rather than rewriting it as current state.
- **Fold decisions into `docs/MODE2-REWRITE-PLAN.md`, not only into `HANDOFF.md`.** This has already gone wrong once: several resolutions lived only in the gitignored handoff while the design document still said the opposite, in one case the exact opposite. The plan is the authority; the handoff is a session log explaining how the plan got that way.
