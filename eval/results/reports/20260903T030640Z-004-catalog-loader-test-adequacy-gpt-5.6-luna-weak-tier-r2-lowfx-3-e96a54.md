# Trial report: 20260903T030640Z-004-catalog-loader-test-adequacy-gpt-5.6-luna-weak-tier-r2-lowfx-3-e96a54

- Task: `004-catalog-loader-test-adequacy`
- Model: `gpt-5.6-luna` (harness: codex)
- Duration: 131.2s | timed out: False | committed: False
- Changed files: tests/test_data_reader.py

## Total score: 59.0 / 100
(scored 100% of rubric weight -- unscored categories, typically the judged ones with no judge model configured, are excluded rather than defaulted)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 100% |
| test_adequacy | automated | 25 | 0% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 0% |
| readability | judged | 8 | 60% |
| maintainability | judged | 7 | 60% |

## Detail

```json
{
  "correctness": {
    "total": 38,
    "passed": 38,
    "failed": [],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "============================= test session starts ==============================\nplatform darwin -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0 -- /Users/dcroton/Local/git-repos/ai-agent-bench/venv/bin/python\nrootdir: /Users/dcroton/Local/git-repos/ai-agent-bench/eval/results/tmp/worktrees/20260903T030640Z-004-catalog-loader-test-adequacy-gpt-5.6-luna-weak-tier-r2-lowfx-3-e96a54\ncollecting ... collected 38 items\n\ntests/test_hA.py::test_A01_missing_file_rejected PASSED                  [  2%]\ntests/test_hA.py::test_A02_missing_file_message_names_path PASSED        [  5%]\ntests/test_hA.py::test_A03_empty_catalog_rejected PASSED                 [  7%]\ntests/test_hA.py::test_A04_non_positive_box_size_rejected[0.0] PASSED    [ 10%]\ntests/test_hA.py::test_A04_non_positive_box_size_rejected[-2.0] PASSED   [ 13%]\ntests/test_hA.py::test_A05_negative_mass_rejected PASSED                 [ 15%]\ntests/test_hA.py::test_A06_empty_selection_rejected PASSED               [ 18%]\ntests/test_hA.py::test_A07_emptiness_reported_before_box_size PASSED     [ 21%]\ntests/test_hA.py::test_A08_zero_mass_accepted PASSED                     [ 23%]\ntests/test_hA.py::test_A09_extra_datasets_and_attrs_ignored PASSED       [ 26%]\ntests/test_hA.py::test_A10_returned_keys_exact PASSED                    [ 28%]\ntests/test_hA.py::test_A11_selection_applied_to_every_array[x] PASSED    [ 31%]\ntests/test_hA.py::test_A11_selection_applied_to_every_array[y] PASSED    [ 34%]\ntests/test_hA.py::test_A11_selection_applied_to_every_array[z] PASSED    [ 36%]\ntests/test_hA.py::test_A11_selection_applied_to_every_array[vx] PASSED   [ 39%]\ntests/test_hA.py::test_A11_selection_applied_to_every_array[vy] PASSED   [ 42%]\ntests/test_hA.py::test_A11_selection_applied_to_every_array[vz] PASSED   [ 44%]\ntests/test_hA.py::test_A11_selection_applied_to_every_array[log_stellar_mass] PASSED [ 47%]\ntests/test_hA.py::test_A12_selection_preserves_order PASSED              [ 50%]\ntests/test_hA.py::test_A13_selection_edges[masses0-expected0] PASSED     [ 52%]\ntests/test_hA.py::test_A13_selection_edges[masses1-expected1] PASSED     [ 55%]\ntests/test_hA.py::test_A13_selection_edges[masses2-expected2] PASSED     [ 57%]\ntests/test_hA.py::test_A13_selection_edges[masses3-expected3] PASSED     [ 60%]\ntests/test_hA.py::test_A14_selection_reads_the_config PASSED             [ 63%]\ntests/test_hA.py::test_A15_arrays_converted_to_float64[int32] PASSED     [ 65%]\ntests/test_hA.py::test_A15_arrays_converted_to_float64[uint16] PASSED    [ 68%]\ntests/test_hA.py::test_A15_arrays_converted_to_float64[float32] PASSED   [ 71%]\ntests/test_hA.py::test_A16_integer_values_survive_conversion PASSED      [ 73%]\ntests/test_hA.py::test_A17_redshift_returned PASSED                      [ 76%]\ntests/test_hA.py::test_A18_box_size_returned PASSED                      [ 78%]\ntests/test_hA.py::test_A19_scalars_returned_unscaled[0.0-1.0] PASSED     [ 81%]\ntests/test_hA.py::test_A19_scalars_returned_unscaled[4.0-62.5] PASSED    [ 84%]\ntests/test_hA.py::test_A20_scalars_unaffected_by_selection PASSED        [ 86%]\ntests/test_hB.py::test_B01_driver_loads_a_catalog_and_writes_results PASSED [ 89%]\ntests/test_hB.py::test_B02_driver_rejects_an_out_of_range_catalog PASSED [ 92%]\ntests/test_hB.py::test_B03_driver_rejects_a_bad_box_size PASSED          [ 94%]\ntests/test_hB.py::test_B04_deliverable_exists PASSED                     [ 97%]\ntests/test_hB.py::test_B05_deliverable_collects_at_least_one_test PASSED [100%]\n\n============================== 38 passed in 0.99s ==============================\n",
    "stderr_tail": ""
  },
  "own_suite_baseline": {
    "returncode": 1,
    "timed_out": false,
    "passed_clean": false,
    "tail": "........F............................................................... [ 79%]\n...................                                                      [100%]\n=================================== FAILURES ===================================\n_____________ test_selection_values_order_keys_and_float64_dtypes ______________\n\ntmp_path = PosixPath('/private/var/folders/mw/53tcw7cn0ng7lm248lq60tvhlhmg9l/T/pytest-of-dcroton/pytest-3289/test_selection_values_order_ke0')\n\n    def test_selection_values_order_keys_and_float64_dtypes(tmp_path):\n        path = write_catalog(tmp_path / \"selected.h5\", extra=True, redshift=0.0, box_size=37.25)\n        catalog = load_galaxy_catalog(str(path), {\"log_mass_min\": 8, \"log_mass_max\": 11})\n        assert set(catalog) == set(FIELDS) | {\"redshift\", \"box_size\"}\n        for index, field in enumerate(FIELDS):\n            expected = (np.array([8.0, 11.0]) if field == \"log_stellar_mass\"\n                        else np.array([10 + index, 40 + index], dtype=np.float64))\n>           assert np.array_equal(catalog[field], expected)\nE           assert False\nE            +  where False = <function array_equal at 0x1093f6a70>(array([10., 20., 30.]), array([10., 40.]))\nE            +    where <function array_equal at 0x1093f6a70> = np.array_equal\n\ntests/test_data_reader.py:102: AssertionError\n=========================== short test summary info ============================\nFAILED tests/test_data_reader.py::test_selection_values_order_keys_and_float64_dtypes\n1 failed, 90 passed in 1.99s\n"
  },
  "ships_red_outside_root": {
    "ships_red_outside_root": true,
    "returncode": 1,
    "timed_out": false,
    "tail": "........F............................................................... [ 79%]\n...................                                                      [100%]\n=================================== FAILURES ===================================\n_____________ test_selection_values_order_keys_and_float64_dtypes ______________\n\ntmp_path = PosixPath('/private/var/folders/mw/53tcw7cn0ng7lm248lq60tvhlhmg9l/T/pytest-of-dcroton/pytest-3290/test_selection_values_order_ke0')\n\n    def test_selection_values_order_keys_and_float64_dtypes(tmp_path):\n        path = write_catalog(tmp_path / \"selected.h5\", extra=True, redshift=0.0, box_size=37.25)\n        catalog = load_galaxy_catalog(str(path), {\"log_mass_min\": 8, \"log_mass_max\": 11})\n        assert set(catalog) == set(FIELDS) | {\"redshift\", \"box_size\"}\n        for index, field in enumerate(FIELDS):\n            expected = (np.array([8.0, 11.0]) if field == \"log_stellar_mass\"\n                        else np.array([10 + index, 40 + index], dtype=np.float64))\n>           assert np.array_equal(catalog[field], expected)\nE           assert False\nE            +  where False = <function array_equal at 0x10aca1bb0>(array([10., 20., 30.]), array([10., 40.]))\nE            +    where <function array_equal at 0x10aca1bb0> = np.array_equal\n\n/Users/dcroton/Local/git-repos/ai-agent-bench/eval/results/tmp/worktrees/20260903T030640Z-004-catalog-loader-test-adequacy-gpt-5.6-luna-weak-tier-r2-lowfx-3-e96a54/tests/test_data_reader.py:102: AssertionError\n=========================== short test summary info ============================\nFAILED ../../../../../../../Users/dcroton/Local/git-repos/ai-agent-bench/eval/results/tmp/worktrees/20260903T030640Z-004-catalog-loader-test-adequacy-gpt-5.6-luna-weak-tier-r2-lowfx-3-e96a54/tests/test_data_reader.py::test_selection_values_order_keys_and_float64_dtypes\n1 failed, 90 passed in 1.95s\n"
  },
  "test_adequacy": {
    "note": "own suite did not pass cleanly; mutation credit withheld"
  },
  "scope_discipline": {
    "changed_files": [
      "tests/test_data_reader.py"
    ],
    "out_of_scope": [],
    "frozen_touched": []
  },
  "hygiene": {
    "findings_count": 0,
    "findings": [],
    "ships_red_outside_root": true
  },
  "judge": {
    "attempts": [
      {
        "attempt": 1,
        "returncode": 0,
        "raw": "{\"readability\": 3, \"maintainability\": 3, \"notes\": \"Naming and the write_catalog helper docstring are clear, but compound test names like test_selection_values_order_keys_and_float64_dtypes and test_config_controls_selection_and_both_edges_are_inclusive (lines 96, 116) bundle multiple assertions under one vague label, and test_rejection_order's parametrize table passes a `values` argument that then gets silently overridden inside the body via `if name in (...)` string matching (lines 68-74), which is confusing to trace. Maintainability suffers from real duplication: the negative-mass and empty/zero-box scenarios in test_rejection_order (lines 55-75) re-implement logic already covered by the standalone test_negative_mass_rejection and test_nonpositive_box_rejection tests, rather than sharing a single parametrized definition.\"}\n",
        "stderr_tail": "",
        "parsed": {
          "readability": 3,
          "maintainability": 3,
          "notes": "Naming and the write_catalog helper docstring are clear, but compound test names like test_selection_values_order_keys_and_float64_dtypes and test_config_controls_selection_and_both_edges_are_inclusive (lines 96, 116) bundle multiple assertions under one vague label, and test_rejection_order's parametrize table passes a `values` argument that then gets silently overridden inside the body via `if name in (...)` string matching (lines 68-74), which is confusing to trace. Maintainability suffers from real duplication: the negative-mass and empty/zero-box scenarios in test_rejection_order (lines 55-75) re-implement logic already covered by the standalone test_negative_mass_rejection and test_nonpositive_box_rejection tests, rather than sharing a single parametrized definition."
        },
        "timed_out": false
      }
    ]
  }
}
```
