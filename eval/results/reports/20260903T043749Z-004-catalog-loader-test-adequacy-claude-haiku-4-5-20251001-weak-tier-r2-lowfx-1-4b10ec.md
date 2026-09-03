# Trial report: 20260903T043749Z-004-catalog-loader-test-adequacy-claude-haiku-4-5-20251001-weak-tier-r2-lowfx-1-4b10ec

- Task: `004-catalog-loader-test-adequacy`
- Model: `claude-haiku-4-5-20251001` (harness: claude)
- Duration: 173.1s | timed out: False | committed: False
- Changed files: tests/test_data_reader.py

## Total score: 92.8 / 100
(scored 100% of rubric weight -- unscored categories, typically the judged ones with no judge model configured, are excluded rather than defaulted)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 100% |
| test_adequacy | automated | 25 | 92% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 91% |
| readability | judged | 8 | 80% |
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
    "raw_tail": "============================= test session starts ==============================\nplatform darwin -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0 -- /Users/dcroton/Local/git-repos/ai-agent-bench/venv/bin/python\nrootdir: /Users/dcroton/Local/git-repos/ai-agent-bench/eval/results/tmp/worktrees/20260903T043749Z-004-catalog-loader-test-adequacy-claude-haiku-4-5-20251001-weak-tier-r2-lowfx-1-4b10ec\ncollecting ... collected 38 items\n\ntests/test_hA.py::test_A01_missing_file_rejected PASSED                  [  2%]\ntests/test_hA.py::test_A02_missing_file_message_names_path PASSED        [  5%]\ntests/test_hA.py::test_A03_empty_catalog_rejected PASSED                 [  7%]\ntests/test_hA.py::test_A04_non_positive_box_size_rejected[0.0] PASSED    [ 10%]\ntests/test_hA.py::test_A04_non_positive_box_size_rejected[-2.0] PASSED   [ 13%]\ntests/test_hA.py::test_A05_negative_mass_rejected PASSED                 [ 15%]\ntests/test_hA.py::test_A06_empty_selection_rejected PASSED               [ 18%]\ntests/test_hA.py::test_A07_emptiness_reported_before_box_size PASSED     [ 21%]\ntests/test_hA.py::test_A08_zero_mass_accepted PASSED                     [ 23%]\ntests/test_hA.py::test_A09_extra_datasets_and_attrs_ignored PASSED       [ 26%]\ntests/test_hA.py::test_A10_returned_keys_exact PASSED                    [ 28%]\ntests/test_hA.py::test_A11_selection_applied_to_every_array[x] PASSED    [ 31%]\ntests/test_hA.py::test_A11_selection_applied_to_every_array[y] PASSED    [ 34%]\ntests/test_hA.py::test_A11_selection_applied_to_every_array[z] PASSED    [ 36%]\ntests/test_hA.py::test_A11_selection_applied_to_every_array[vx] PASSED   [ 39%]\ntests/test_hA.py::test_A11_selection_applied_to_every_array[vy] PASSED   [ 42%]\ntests/test_hA.py::test_A11_selection_applied_to_every_array[vz] PASSED   [ 44%]\ntests/test_hA.py::test_A11_selection_applied_to_every_array[log_stellar_mass] PASSED [ 47%]\ntests/test_hA.py::test_A12_selection_preserves_order PASSED              [ 50%]\ntests/test_hA.py::test_A13_selection_edges[masses0-expected0] PASSED     [ 52%]\ntests/test_hA.py::test_A13_selection_edges[masses1-expected1] PASSED     [ 55%]\ntests/test_hA.py::test_A13_selection_edges[masses2-expected2] PASSED     [ 57%]\ntests/test_hA.py::test_A13_selection_edges[masses3-expected3] PASSED     [ 60%]\ntests/test_hA.py::test_A14_selection_reads_the_config PASSED             [ 63%]\ntests/test_hA.py::test_A15_arrays_converted_to_float64[int32] PASSED     [ 65%]\ntests/test_hA.py::test_A15_arrays_converted_to_float64[uint16] PASSED    [ 68%]\ntests/test_hA.py::test_A15_arrays_converted_to_float64[float32] PASSED   [ 71%]\ntests/test_hA.py::test_A16_integer_values_survive_conversion PASSED      [ 73%]\ntests/test_hA.py::test_A17_redshift_returned PASSED                      [ 76%]\ntests/test_hA.py::test_A18_box_size_returned PASSED                      [ 78%]\ntests/test_hA.py::test_A19_scalars_returned_unscaled[0.0-1.0] PASSED     [ 81%]\ntests/test_hA.py::test_A19_scalars_returned_unscaled[4.0-62.5] PASSED    [ 84%]\ntests/test_hA.py::test_A20_scalars_unaffected_by_selection PASSED        [ 86%]\ntests/test_hB.py::test_B01_driver_loads_a_catalog_and_writes_results PASSED [ 89%]\ntests/test_hB.py::test_B02_driver_rejects_an_out_of_range_catalog PASSED [ 92%]\ntests/test_hB.py::test_B03_driver_rejects_a_bad_box_size PASSED          [ 94%]\ntests/test_hB.py::test_B04_deliverable_exists PASSED                     [ 97%]\ntests/test_hB.py::test_B05_deliverable_collects_at_least_one_test PASSED [100%]\n\n============================== 38 passed in 1.36s ==============================\n",
    "stderr_tail": ""
  },
  "own_suite_baseline": {
    "returncode": 0,
    "timed_out": false,
    "passed_clean": true,
    "tail": "........................................................................ [ 57%]\n.....................................................                    [100%]\n125 passed in 2.24s\n"
  },
  "ships_red_outside_root": {
    "ships_red_outside_root": false,
    "returncode": 0,
    "timed_out": false,
    "tail": "........................................................................ [ 57%]\n.....................................................                    [100%]\n125 passed in 2.07s\n"
  },
  "test_adequacy": {
    "per_mutation": {
      "M01_missing_file_guard_removed": "kill",
      "M02_empty_catalog_guard_removed": "kill",
      "M03_box_size_positive_guard_removed": "kill",
      "M04_negative_mass_guard_removed": "kill",
      "M05_empty_selection_guard_removed": "kill",
      "M06_mass_min_boundary_excluded": "kill",
      "M07_mass_max_boundary_excluded": "kill",
      "M08_zero_mass_rejected": "kill",
      "M09_extra_datasets_rejected": "kill",
      "M10_float64_cast_removed_log_stellar_mass": "kill",
      "M10_float64_cast_removed_vx": "kill",
      "M10_float64_cast_removed_vy": "kill",
      "M10_float64_cast_removed_vz": "kill",
      "M10_float64_cast_removed_x": "kill",
      "M10_float64_cast_removed_y": "kill",
      "M10_float64_cast_removed_z": "kill",
      "M11_redshift_off_by_one": "kill",
      "M12_box_size_scaled": "kill",
      "M13_wrong_rows_selected_log_stellar_mass": "kill",
      "M13_wrong_rows_selected_vx": "kill",
      "M13_wrong_rows_selected_vy": "kill",
      "M13_wrong_rows_selected_vz": "kill",
      "M13_wrong_rows_selected_x": "kill",
      "M13_wrong_rows_selected_y": "kill",
      "M13_wrong_rows_selected_z": "kill",
      "M14_message_omits_box_size_positive": "kill",
      "M14_message_omits_empty_catalog": "kill",
      "M14_message_omits_file_not_found": "kill",
      "M14_message_omits_filepath_empty_catalog": "kill",
      "M14_message_omits_filepath_mass_range": "kill",
      "M14_message_omits_filepath_missing_file": "kill",
      "M14_message_omits_log_stellar_mass": "kill",
      "M14_message_omits_no_galaxies_in_range": "kill",
      "M14_message_omits_units_note": "survive",
      "M15_config_bounds_ignored": "kill",
      "M16_selected_order_reversed_log_stellar_mass": "kill",
      "M16_selected_order_reversed_vx": "kill",
      "M16_selected_order_reversed_vy": "kill",
      "M16_selected_order_reversed_vz": "kill",
      "M16_selected_order_reversed_x": "kill",
      "M16_selected_order_reversed_y": "kill",
      "M16_selected_order_reversed_z": "kill",
      "M17_unexpected_result_key_leaked": "kill",
      "M18_extra_attributes_rejected": "kill",
      "M19_box_size_reported_before_emptiness": "kill",
      "M19_empty_selection_reported_before_negative_mass": "kill",
      "M19_negative_mass_reported_before_box_size": "kill",
      "M20_box_size_not_cast_to_float": "survive",
      "M20_redshift_not_cast_to_float": "survive",
      "M21_extra_attribute_leaked": "kill",
      "M21_extra_dataset_leaked": "kill",
      "M22_small_box_size_rejected": "survive",
      "M22_zero_redshift_rejected": "kill"
    },
    "killed": 49,
    "total": 53
  },
  "scope_discipline": {
    "changed_files": [
      "tests/test_data_reader.py"
    ],
    "out_of_scope": [],
    "frozen_touched": []
  },
  "hygiene": {
    "findings_count": 1,
    "findings": [
      "tests/test_data_reader.py:8:1: I001 [*] Import block is un-sorted or un-formatted"
    ]
  },
  "judge": {
    "attempts": [
      {
        "attempt": 1,
        "returncode": 0,
        "raw": "{\"readability\": 4, \"maintainability\": 3, \"notes\": \"readability: test names and docstrings clearly state the single behavior under test (e.g. test_selection_inclusive_lower_bound line 168, test_negative_mass_before_no_range line 148), and assertions are paired with explanatory comments matching actual behavior (e.g. '# Only 8.5 and 10.0 should survive' line 205). maintainability: good DRY via the shared _make_catalog_file factory (lines 21-64), but TestArraySelection (lines 253-321) and TestDtypeConversion (lines 324-394) repeat the same 6-7 line pattern per array/dtype almost verbatim, which could be collapsed with pytest.mark.parametrize.\"}\n",
        "stderr_tail": "",
        "parsed": {
          "readability": 4,
          "maintainability": 3,
          "notes": "readability: test names and docstrings clearly state the single behavior under test (e.g. test_selection_inclusive_lower_bound line 168, test_negative_mass_before_no_range line 148), and assertions are paired with explanatory comments matching actual behavior (e.g. '# Only 8.5 and 10.0 should survive' line 205). maintainability: good DRY via the shared _make_catalog_file factory (lines 21-64), but TestArraySelection (lines 253-321) and TestDtypeConversion (lines 324-394) repeat the same 6-7 line pattern per array/dtype almost verbatim, which could be collapsed with pytest.mark.parametrize."
        },
        "timed_out": false
      }
    ]
  }
}
```
