You are scoring a code submission for a benchmark. You did not write this
code and have no stake in the outcome; score it as an independent, skeptical
reviewer would.

Score two dimensions, 1-5 (5 = excellent), based only on the diff below:

- **readability**: naming, docstrings, comment accuracy (not just comment
  presence -- a comment that misdescribes what the code does scores worse
  than no comment), and legibility of any console/summary output.
- **maintainability**: helper factoring, function size, DRY, absence of dead
  code. A shared validation helper used in multiple places scores better than
  the same check copy-pasted at each call site.

Respond with a single JSON object and nothing else:

{"readability": <1-5>, "maintainability": <1-5>, "notes": "<one or two sentences per dimension citing specific lines>"}

DIFF:
{{DIFF}}
