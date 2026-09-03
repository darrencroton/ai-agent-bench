# Trial report: 20260903T025510Z-003-pair-finder-validation-gpt-5.6-luna-weak-tier-r2-lowfx-3-44a0ea

- Task: `003-pair-finder-validation`
- Model: `gpt-5.6-luna` (harness: codex)
- Duration: 95.7s | timed out: False | committed: False
- Changed files: src/pair_finder.py

## Total score: 69.7 / 100
(scored 100% of rubric weight -- unscored categories, typically the judged ones with no judge model configured, are excluded rather than defaulted)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 100% |
| test_adequacy | automated | 25 | 0% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 77% |
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
    "raw_tail": "test_hA.py::test_A302_no_pairs_early_return_preserved PASSED       [ 86%]\ntests/test_hA.py::test_A303_mass_ratio_cut_early_return_preserved PASSED [ 86%]\ntests/test_hA.py::test_A304_empty_catalog_accepted PASSED                [ 87%]\ntests/test_hA.py::test_A305_mass_bin_sentinel_above_range PASSED         [ 87%]\ntests/test_hA.py::test_A306_mass_bin_sentinel_below_range PASSED         [ 87%]\ntests/test_hA.py::test_A307_sep_bin_sentinel_beyond_last_edge PASSED     [ 88%]\ntests/test_hA.py::test_A308_unknown_mass_bin_by_still_raises_value_error PASSED [ 88%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[primary] PASSED [ 88%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[secondary] PASSED [ 89%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[mean] PASSED [ 89%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[total] PASSED [ 89%]\ntests/test_hA.py::test_A310_signature_unchanged PASSED                   [ 90%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int16-ascending_dv] PASSED [ 90%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int16-descending_dv] PASSED [ 90%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint16-ascending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint16-descending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int32-ascending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int32-descending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint32-ascending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint32-descending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int64-ascending_dv] PASSED [ 93%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int64-descending_dv] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vx] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vy] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vz] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vx] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vy] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vz] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vx] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vy] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vz] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vx] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vy] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vz] PASSED [ 97%]\ntests/test_hA.py::test_A311_validation_precedes_no_pairs_return_nonfinite PASSED [ 97%]\ntests/test_hA.py::test_A312_validation_precedes_no_pairs_return_length PASSED [ 97%]\ntests/test_hA.py::test_A313_validation_precedes_mass_ratio_cut_return PASSED [ 98%]\ntests/test_hB.py::test_B00_pipeline_imports PASSED                       [ 98%]\ntests/test_hB.py::test_B01_driver_output_matches_the_analytic_expectation PASSED [ 98%]\ntests/test_hB.py::test_B02_nonfinite_position_on_disk_asserts PASSED     [ 99%]\ntests/test_hB.py::test_B03_position_outside_box_on_disk_asserts PASSED   [ 99%]\ntests/test_hB.py::test_B04_malformed_config_through_driver PASSED        [ 99%]\ntests/test_hB.py::test_B05_driver_honours_nondefault_config PASSED       [100%]\n\n============================= 315 passed in 0.68s ==============================\n",
    "stderr_tail": ""
  },
  "own_suite_baseline": {
    "returncode": 0,
    "timed_out": false,
    "passed_clean": true,
    "tail": "........................................................................ [ 90%]\n........                                                                 [100%]\n80 passed in 1.87s\n"
  },
  "ships_red_outside_root": {
    "ships_red_outside_root": false,
    "returncode": 0,
    "timed_out": false,
    "tail": "........................................................................ [ 90%]\n........                                                                 [100%]\n80 passed in 1.87s\n"
  },
  "test_adequacy": {
    "per_mutation": {
      "M01_catalog_key_presence": "survive",
      "M02_catalog_length_mismatch": "survive",
      "M03_catalog_nonfinite": "survive",
      "M04_catalog_rank": "survive",
      "M05a_catalog_container": "survive",
      "M05b_catalog_dtype": "survive",
      "M06_box_size_form": "survive",
      "M07_box_size_value": "survive",
      "M08_positions_outside_box": "survive",
      "M09_config_key_presence": "survive",
      "M10_max_sep_value": "survive",
      "M11_mass_ratio_min_value": "survive",
      "M12_config_scalar_form": "survive",
      "M13a_sep_bins_container": "survive",
      "M13b_sep_bins_dtype": "survive",
      "M13c_sep_bins_rank": "survive",
      "M13d_sep_bins_element_form": "survive",
      "M13e_sep_bins_min_length": "survive",
      "M13f_sep_bins_finite": "survive",
      "M13g_sep_bins_monotonic": "survive",
      "M14a_mass_limits_finite": "survive",
      "M14b_mass_bin_width_finite_positive": "survive",
      "M14c_mass_range_ordering": "survive",
      "M14d_mass_bin_count": "survive",
      "M15_mass_bin_sentinel_dropped": "survive",
      "M16_sep_bin_sentinel_clipped": "survive",
      "M17_catalog_argument_form": "survive",
      "M18_config_argument_form": "survive",
      "M19a_message_omits_names": "survive",
      "M19b_message_omits_form_reasons": "survive",
      "M19c_message_omits_value_reasons": "survive",
      "M20_reject_empty_catalog": "survive",
      "M21_reject_integer_dtype_log_stellar_mass": "survive",
      "M21_reject_integer_dtype_vx": "survive",
      "M21_reject_integer_dtype_vy": "survive",
      "M21_reject_integer_dtype_vz": "survive",
      "M21_reject_integer_dtype_x": "survive",
      "M21_reject_integer_dtype_y": "survive",
      "M21_reject_integer_dtype_z": "survive",
      "M22_reject_sep_bins_float_ndarray": "survive",
      "M22_reject_sep_bins_int_ndarray": "survive",
      "M22_reject_sep_bins_numpy_scalar_elements": "survive",
      "M22_reject_sep_bins_tuple": "survive",
      "M23_reject_numpy_floating_box_size": "survive",
      "M23_reject_numpy_floating_log_mass_max": "survive",
      "M23_reject_numpy_floating_log_mass_min": "survive",
      "M23_reject_numpy_floating_mass_bin_width": "survive",
      "M23_reject_numpy_floating_mass_ratio_min": "survive",
      "M23_reject_numpy_integer_box_size": "survive",
      "M23_reject_numpy_integer_log_mass_max": "survive",
      "M23_reject_numpy_integer_log_mass_min": "survive",
      "M23_reject_numpy_integer_mass_bin_width": "survive",
      "M23_reject_numpy_integer_mass_ratio_min": "survive",
      "M23_reject_numpy_integer_max_sep": "survive",
      "M24_reject_mass_ratio_min_boundaries": "survive",
      "M25_reject_negative_masses": "survive",
      "M26a_signed_integer_mass_cast_removed": "survive",
      "M26b_unsigned_integer_mass_cast_removed": "survive",
      "M26c_narrow_integer_velocity_cast_removed": "survive"
    },
    "killed": 0,
    "total": 59
  },
  "scope_discipline": {
    "changed_files": [
      "src/pair_finder.py"
    ],
    "out_of_scope": [],
    "frozen_touched": []
  },
  "hygiene": {
    "findings_count": 3,
    "findings": [
      "src/pair_finder.py:186:16: C408 Unnecessary `dict()` call (rewrite as a literal)",
      "src/pair_finder.py:222:16: C408 Unnecessary `dict()` call (rewrite as a literal)",
      "src/pair_finder.py:245:12: C408 Unnecessary `dict()` call (rewrite as a literal)"
    ]
  },
  "judge": {
    "attempts": [
      {
        "attempt": 1,
        "returncode": 0,
        "raw": "{\"readability\": 4, \"maintainability\": 4, \"notes\": \"readability: naming and assertion messages are clear and specific (e.g. \\\"mass_bin_width must define at least one mass bin\\\" at pair_finder.py); docstrings on _is_real_scalar and _validate_inputs accurately describe behavior, though the function has no inline comments to explain the box-membership or bin-count checks, leaving intent slightly implicit. maintainability: validation is centralized in one boundary function using shared field-name tuples (_ARRAY_FIELDS, _CONFIG_FIELDS) and a reusable _is_real_scalar helper rather than repeating checks per field, and array/scalar/sep_bins validation each iterate over a list instead of being copy-pasted, keeping the function DRY despite its length.\"}\n",
        "stderr_tail": "",
        "parsed": {
          "readability": 4,
          "maintainability": 4,
          "notes": "readability: naming and assertion messages are clear and specific (e.g. \"mass_bin_width must define at least one mass bin\" at pair_finder.py); docstrings on _is_real_scalar and _validate_inputs accurately describe behavior, though the function has no inline comments to explain the box-membership or bin-count checks, leaving intent slightly implicit. maintainability: validation is centralized in one boundary function using shared field-name tuples (_ARRAY_FIELDS, _CONFIG_FIELDS) and a reusable _is_real_scalar helper rather than repeating checks per field, and array/scalar/sep_bins validation each iterate over a list instead of being copy-pasted, keeping the function DRY despite its length."
        },
        "timed_out": false
      }
    ]
  }
}
```
