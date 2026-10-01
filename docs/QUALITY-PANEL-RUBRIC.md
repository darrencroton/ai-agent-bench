# Quality panel rubric

You are rating one slice of a frozen implementation plan as implemented by a Developer. The repository is checked out at the commit under review. Read the slice's change with `git diff <before_head> <commit>` (the two commits are given below), read that slice's contract in the plan file (its purpose, authorized surface, acceptance criteria and non-goals), and read whatever surrounding code you need to judge the change in context.

Score each of the five dimensions from 1 to 5. The anchors below fix 1, 3 and 5; use 2 and 4 for work that falls between them.

- `correctness_beyond_tests`: behaviour beyond what the acceptance criteria literally test. 1: plausible inputs or edge cases the plan implies are handled wrongly or crash. 3: the stated cases are right, but some implied edge cases are unhandled or silently mishandled. 5: implied edge cases and failure modes are handled deliberately, failing loudly where the plan asks for it.
- `design`: structure of the change. 1: tangled, duplicated or speculative; the change fights the existing code. 3: workable, with some needless coupling, duplication or misplaced responsibility. 5: minimal, cohesive, and fits the existing architecture with no dead code.
- `readability_docs`: how easily a maintainer can follow it. 1: names, comments or docstrings mislead, or the contract is undocumented. 3: readable, with gaps or comments that restate code instead of explaining contracts. 5: clear names, docstrings where the contract is not obvious, comments that explain why.
- `tests`: the Developer's own tests for this slice. 1: missing, or would pass against a broken implementation. 3: cover the main path, but miss important edge cases or assert weakly. 5: behaviour-named tests that would catch realistic regressions, including the edge cases above.
- `contract_discipline`: fidelity to the slice contract. 1: changes outside the authorized surface, violated non-goals, or missing required behaviour. 3: within contract, with minor unrequested additions or ambiguous readings taken without saying so. 5: exactly the slice, nothing more, every acceptance criterion addressed.

Cite `path:line` evidence for every score: each dimension should be traceable to at least one evidence line. Judge only what is in the repository; do not propose or make changes.

Answer in exactly this output contract, with nothing before or after it:

```text
SECTION: SCORES
correctness_beyond_tests: <1-5>
design: <1-5>
readability_docs: <1-5>
tests: <1-5>
contract_discipline: <1-5>
SECTION: EVIDENCE
- <path:line> -- <one line>
SECTION: SUMMARY
<at most five sentences>
```
