# Trial report: 20260906T031045Z-004-catalog-loader-test-adequacy-macstudio_ornith_ornith-1.5-397b-q6-local-cloud-20260906-opencode-macstudio_ornith_ornith-1.5-397b-q6-1-1920f7

- Task: `004-catalog-loader-test-adequacy`
- Model: `macstudio/ornith/ornith-1.5-397b-q6` (harness: opencode)
- Model duration: 314.2s | venv setup: 29.6s | timed out: False | committed: False
- Changed files: (none)
- Profile: `test_authoring` | Complete submission: False (missing: tests/test_data_reader.py)
- Gate status: failed (correctness 0.0<1.0) | Integrity violation: False

## Deterministic score: 0.0 / 100

## Judged: readability 0% of weight, maintainability 0% of weight (judge claude-opus-5, status not_run)

## Composite score: 0.0 / 100

(scored 0% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | gate | 0% |
| test_adequacy | automated | 65 | 0% |
| scope_discipline | automated | 10 | 0% |
| hygiene | automated | 10 | 0% |
| readability | judged | 8 | 0% |
| maintainability | judged | 7 | 0% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| (none -- not computed for this trial) | | | |

## Provenance

```json
{
  "rubric_version": 2,
  "rubric_sha256": "a4a93e1f5fd3b17c7ad7f873dd74a65ff2c74da8a1f759c4ac5e3e8a1d7a9102",
  "rubric_profile": "test_authoring",
  "task_contract_sha256": "829548edc6c2fe8a850dbe11c99ac2f3d07fef5ddc2ef2325deb4821b581e5f7",
  "evaluator_content_sha256": "c1fbfe8ba8842539080d3d8814ada4b1b7895523611bbc1b73cabe5cfe3f504d",
  "grader_git_rev": "feda36838d92392b63b1f3890a169aea2b619036",
  "grader_git_dirty": true,
  "baseline_ref": "frozen-substrate",
  "baseline_commit": "5118620f9e5b0f43f515d995f839a4026eae52af",
  "python_version": "3.14.7",
  "ruff_version": "0.16.5",
  "ruff_version_pinned": "0.16.5",
  "ruff_config": "eval/harness/ruff_eval.toml",
  "dependency_versions": {
    "numpy": "2.5.2",
    "scipy": "1.18.1",
    "h5py": "3.16.0",
    "pytest": "9.1.1",
    "pyyaml": "6.0.3"
  },
  "judge": {
    "model": "claude-opus-5",
    "harness": "claude",
    "effort": "high",
    "prompt_sha256": "f764d223b2a788ad75fbdd10d9c29a23cc95b849573b3dca439b53c252a97c4c",
    "status": "not_run",
    "same_model": false
  }
}
```

## Detail

```json
{
  "reason": "no diff produced (timeout, crash, or empty run)"
}
```
