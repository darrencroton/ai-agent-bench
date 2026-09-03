# Trial report: 20260903T024809Z-003-pair-finder-validation-gpt-5.6-luna-weak-tier-r2-lowfx-1-3ab2ce

- Task: `003-pair-finder-validation`
- Model: `gpt-5.6-luna` (harness: codex)
- Duration: 126.1s | timed out: False | committed: False
- Changed files: src/pair_finder.py, tests/test_pair_finder_validation.py

## Total score: 62.0 / 100
(scored 100% of rubric weight -- unscored categories, typically the judged ones with no judge model configured, are excluded rather than defaulted)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 100% |
| test_adequacy | automated | 25 | 0% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 0% |
| readability | judged | 8 | 80% |
| maintainability | judged | 7 | 80% |

## Detail

```json
{
  "correctness": {
    "total": 315,
    "passed": 315,
    "failed": [],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "test_hA.py::test_A302_no_pairs_early_return_preserved PASSED       [ 86%]\ntests/test_hA.py::test_A303_mass_ratio_cut_early_return_preserved PASSED [ 86%]\ntests/test_hA.py::test_A304_empty_catalog_accepted PASSED                [ 87%]\ntests/test_hA.py::test_A305_mass_bin_sentinel_above_range PASSED         [ 87%]\ntests/test_hA.py::test_A306_mass_bin_sentinel_below_range PASSED         [ 87%]\ntests/test_hA.py::test_A307_sep_bin_sentinel_beyond_last_edge PASSED     [ 88%]\ntests/test_hA.py::test_A308_unknown_mass_bin_by_still_raises_value_error PASSED [ 88%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[primary] PASSED [ 88%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[secondary] PASSED [ 89%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[mean] PASSED [ 89%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[total] PASSED [ 89%]\ntests/test_hA.py::test_A310_signature_unchanged PASSED                   [ 90%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int16-ascending_dv] PASSED [ 90%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int16-descending_dv] PASSED [ 90%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint16-ascending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint16-descending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int32-ascending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int32-descending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint32-ascending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint32-descending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int64-ascending_dv] PASSED [ 93%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int64-descending_dv] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vx] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vy] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vz] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vx] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vy] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vz] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vx] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vy] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vz] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vx] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vy] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vz] PASSED [ 97%]\ntests/test_hA.py::test_A311_validation_precedes_no_pairs_return_nonfinite PASSED [ 97%]\ntests/test_hA.py::test_A312_validation_precedes_no_pairs_return_length PASSED [ 97%]\ntests/test_hA.py::test_A313_validation_precedes_mass_ratio_cut_return PASSED [ 98%]\ntests/test_hB.py::test_B00_pipeline_imports PASSED                       [ 98%]\ntests/test_hB.py::test_B01_driver_output_matches_the_analytic_expectation PASSED [ 98%]\ntests/test_hB.py::test_B02_nonfinite_position_on_disk_asserts PASSED     [ 99%]\ntests/test_hB.py::test_B03_position_outside_box_on_disk_asserts PASSED   [ 99%]\ntests/test_hB.py::test_B04_malformed_config_through_driver PASSED        [ 99%]\ntests/test_hB.py::test_B05_driver_honours_nondefault_config PASSED       [100%]\n\n============================= 315 passed in 0.70s ==============================\n",
    "stderr_tail": ""
  },
  "own_suite_baseline": {
    "returncode": 1,
    "timed_out": false,
    "passed_clean": false,
    "tail": "............................................F........................... [ 77%]\n.....................                                                    [100%]\n=================================== FAILURES ===================================\n__________________ test_integer_catalog_matches_float_catalog __________________\n\n    def test_integer_catalog_matches_float_catalog():\n        integer_result = find_pairs(catalog(np.int16), config())\n        float_result = find_pairs(catalog(float), config())\n        for key in float_result:\n>           np.testing.assert_array_equal(integer_result[key], float_result[key])\nE           AssertionError: \nE           Arrays are not equal\nE           \nE           Mismatched elements: 1 / 1 (100%)\nE           Mismatch at index:\nE            [0]: 0.0 (ACTUAL), 10.0 (DESIRED)\nE           Max absolute difference among violations: 10.\nE           Max relative difference among violations: 1.\nE            ACTUAL: array([0.])\nE            DESIRED: array([10.])\n\ntests/test_pair_finder_validation.py:46: AssertionError\n=========================== short test summary info ============================\nFAILED tests/test_pair_finder_validation.py::test_integer_catalog_matches_float_catalog\n1 failed, 92 passed in 2.06s\n"
  },
  "ships_red_outside_root": {
    "ships_red_outside_root": true,
    "returncode": 1,
    "timed_out": false,
    "tail": "............................................F........................... [ 77%]\n.....................                                                    [100%]\n=================================== FAILURES ===================================\n__________________ test_integer_catalog_matches_float_catalog __________________\n\n    def test_integer_catalog_matches_float_catalog():\n        integer_result = find_pairs(catalog(np.int16), config())\n        float_result = find_pairs(catalog(float), config())\n        for key in float_result:\n>           np.testing.assert_array_equal(integer_result[key], float_result[key])\nE           AssertionError: \nE           Arrays are not equal\nE           \nE           Mismatched elements: 1 / 1 (100%)\nE           Mismatch at index:\nE            [0]: 0.0 (ACTUAL), 10.0 (DESIRED)\nE           Max absolute difference among violations: 10.\nE           Max relative difference among violations: 1.\nE            ACTUAL: array([0.])\nE            DESIRED: array([10.])\n\n/Users/dcroton/Local/git-repos/ai-agent-bench/eval/results/tmp/worktrees/20260903T024809Z-003-pair-finder-validation-gpt-5.6-luna-weak-tier-r2-lowfx-1-3ab2ce/tests/test_pair_finder_validation.py:46: AssertionError\n=========================== short test summary info ============================\nFAILED ../../../../../../../Users/dcroton/Local/git-repos/ai-agent-bench/eval/results/tmp/worktrees/20260903T024809Z-003-pair-finder-validation-gpt-5.6-luna-weak-tier-r2-lowfx-1-3ab2ce/tests/test_pair_finder_validation.py::test_integer_catalog_matches_float_catalog\n1 failed, 92 passed in 1.97s\n"
  },
  "test_adequacy": {
    "note": "own suite did not pass cleanly; mutation credit withheld"
  },
  "scope_discipline": {
    "changed_files": [
      "src/pair_finder.py",
      "tests/test_pair_finder_validation.py"
    ],
    "out_of_scope": [],
    "frozen_touched": []
  },
  "hygiene": {
    "findings_count": 3,
    "findings": [
      "src/pair_finder.py:176:16: C408 Unnecessary `dict()` call (rewrite as a literal)",
      "src/pair_finder.py:212:16: C408 Unnecessary `dict()` call (rewrite as a literal)",
      "src/pair_finder.py:235:12: C408 Unnecessary `dict()` call (rewrite as a literal)"
    ],
    "ships_red_outside_root": true
  },
  "judge": {
    "attempts": [
      {
        "attempt": 1,
        "returncode": 0,
        "raw": "{\"readability\": 4, \"maintainability\": 4, \"notes\": \"readability: names like _real_scalar, array_names, and assert messages (e.g. 'box_size must be positive', 'sep_bins must be strictly increasing') are clear and accurate, though _validate_inputs itself lacks a docstring and the merge-back line `catalog = {**catalog, **arrays, \\\"box_size\\\": scalars.get(...)}` in pair_finder.py is dense and requires re-reading to parse; test names (test_config_scalars_fail_with_named_reason, test_validation_precedes_empty_result) are self-explanatory. maintainability: validation logic is centralized in one _validate_inputs helper called once at the top of find_pairs rather than scattered checks, and _real_scalar is reused for every scalar (good DRY), but _validate_inputs itself is a ~50-line function doing four distinct jobs (array checks, box_size, config scalars, sep_bins) that could be split further; no dead code, and tests use parametrize to avoid duplication.\"}\n",
        "stderr_tail": "",
        "parsed": {
          "readability": 4,
          "maintainability": 4,
          "notes": "readability: names like _real_scalar, array_names, and assert messages (e.g. 'box_size must be positive', 'sep_bins must be strictly increasing') are clear and accurate, though _validate_inputs itself lacks a docstring and the merge-back line `catalog = {**catalog, **arrays, \"box_size\": scalars.get(...)}` in pair_finder.py is dense and requires re-reading to parse; test names (test_config_scalars_fail_with_named_reason, test_validation_precedes_empty_result) are self-explanatory. maintainability: validation logic is centralized in one _validate_inputs helper called once at the top of find_pairs rather than scattered checks, and _real_scalar is reused for every scalar (good DRY), but _validate_inputs itself is a ~50-line function doing four distinct jobs (array checks, box_size, config scalars, sep_bins) that could be split further; no dead code, and tests use parametrize to avoid duplication."
        },
        "timed_out": false
      }
    ]
  }
}
```
