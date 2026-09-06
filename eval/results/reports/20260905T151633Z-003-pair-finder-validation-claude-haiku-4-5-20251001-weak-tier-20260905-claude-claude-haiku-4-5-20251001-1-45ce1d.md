# Trial report: 20260905T151633Z-003-pair-finder-validation-claude-haiku-4-5-20251001-weak-tier-20260905-claude-claude-haiku-4-5-20251001-1-45ce1d

- Task: `003-pair-finder-validation`
- Model: `claude-haiku-4-5-20251001` (harness: claude)
- Model duration: 301.8s | venv setup: 31.1s | timed out: False | committed: False
- Changed files: src/pair_finder.py, tests/test_pair_finder_validation.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 89.4 / 100

## Judged: readability 75% of weight, maintainability 25% of weight (judge claude-opus-5, status ok)

## Composite score: 83.7 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 100% |
| test_adequacy | automated | 25 | 64% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 100% |
| readability | judged | 8 | 75% |
| maintainability | judged | 7 | 25% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| rejection_matrix | 203 | 205 | 0.99 |
| accepted_input_sweep | 64 | 64 | 1.00 |
| preserved_behaviour | 14 | 14 | 1.00 |
| integer_dtype_semantics | 22 | 22 | 1.00 |
| validation_ordering_precedes_early_returns | 3 | 3 | 1.00 |
| driver_integration_path | 7 | 7 | 1.00 |

## Provenance

```json
{
  "rubric_version": 2,
  "rubric_sha256": "a4a93e1f5fd3b17c7ad7f873dd74a65ff2c74da8a1f759c4ac5e3e8a1d7a9102",
  "rubric_profile": "default",
  "task_contract_sha256": "3a83f13cc1c56dc536783edc669feea2e7b4cbe325fa67ac7e221667d6a2c797",
  "evaluator_content_sha256": "4a0569ac508369aa56ea3017e4c390ade1fc5a8567517ed2ba91f9a044a0ca2e",
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
    "status": "ok",
    "same_model": false
  }
}
```

## Detail

```json
{
  "correctness": {
    "total": 315,
    "passed": 313,
    "failed": [
      "tests/test_hA.py::test_A100_rejects[mass_bin_width_value_10.0]",
      "tests/test_hA.py::test_A100_rejects[order_width_positive_before_range]"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "sts/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint16-ascending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint16-descending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int32-ascending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int32-descending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint32-ascending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint32-descending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int64-ascending_dv] PASSED [ 93%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int64-descending_dv] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vx] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vy] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vz] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vx] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vy] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vz] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vx] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vy] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vz] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vx] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vy] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vz] PASSED [ 97%]\ntests/test_hA.py::test_A311_validation_precedes_no_pairs_return_nonfinite PASSED [ 97%]\ntests/test_hA.py::test_A312_validation_precedes_no_pairs_return_length PASSED [ 97%]\ntests/test_hA.py::test_A313_validation_precedes_mass_ratio_cut_return PASSED [ 98%]\ntests/test_hB.py::test_B00_pipeline_imports PASSED                       [ 98%]\ntests/test_hB.py::test_B01_driver_output_matches_the_analytic_expectation PASSED [ 98%]\ntests/test_hB.py::test_B02_nonfinite_position_on_disk_asserts PASSED     [ 99%]\ntests/test_hB.py::test_B03_position_outside_box_on_disk_asserts PASSED   [ 99%]\ntests/test_hB.py::test_B04_malformed_config_through_driver PASSED        [ 99%]\ntests/test_hB.py::test_B05_driver_honours_nondefault_config PASSED       [100%]\n\n=================================== FAILURES ===================================\n_________________ test_A100_rejects[mass_bin_width_value_10.0] _________________\ntests/test_hA.py:513: in test_A100_rejects\n    assert any(re.search(rf\"\\b{re.escape(n)}\\b\", message) for n in names), (\nE   AssertionError: message names none of ['mass_bin_width']: 'config mass grid must have at least one mass bin, got 0 from (11.0 - 8.0) / 10.0'\nE   assert False\nE    +  where False = any(<generator object test_A100_rejects.<locals>.<genexpr> at 0x106ca6e40>)\n_____________ test_A100_rejects[order_width_positive_before_range] _____________\ntests/test_hA.py:510: in test_A100_rejects\n    assert token in message, (\nE   AssertionError: message does not contain the required reason token 'positive': \"config['log_mass_max'] must be greater than config['log_mass_min']\"\nE   assert 'positive' in \"config['log_mass_max'] must be greater than config['log_mass_min']\"\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A100_rejects[mass_bin_width_value_10.0] - Asser...\nFAILED tests/test_hA.py::test_A100_rejects[order_width_positive_before_range]\n======================== 2 failed, 313 passed in 0.76s =========================\n",
    "stderr_tail": "",
    "obligations": [
      {
        "id": "rejection_matrix",
        "passed": 203,
        "collected": 205,
        "fraction": 0.9902439024390244,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_A100_rejects[mass_bin_width_value_10.0]",
          "tests/test_hA.py::test_A100_rejects[order_width_positive_before_range]"
        ]
      },
      {
        "id": "accepted_input_sweep",
        "passed": 64,
        "collected": 64,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "preserved_behaviour",
        "passed": 14,
        "collected": 14,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "integer_dtype_semantics",
        "passed": 22,
        "collected": 22,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "validation_ordering_precedes_early_returns",
        "passed": 3,
        "collected": 3,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "driver_integration_path",
        "passed": 7,
        "collected": 7,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      }
    ]
  },
  "own_suite_baseline": {
    "returncode": 0,
    "timed_out": false,
    "passed_clean": true,
    "passed_nodes": [
      "tests/test_geometric.py::TestPairCountFormula::test_pair_count_matches_formula",
      "tests/test_geometric.py::TestPairCountFormula::test_pair_count_n_squared_scaling",
      "tests/test_geometric.py::TestPairCountFormula::test_pair_count_r_cubed_scaling",
      "tests/test_geometric.py::TestPairCountFormula::test_pair_count_reproducible",
      "tests/test_geometric.py::TestPeriodicBoundaryGeometry::test_no_duplicate_pairs",
      "tests/test_geometric.py::TestPeriodicBoundaryGeometry::test_no_self_pairs",
      "tests/test_geometric.py::TestPeriodicBoundaryGeometry::test_pair_count_independent_of_box_replication",
      "tests/test_geometric.py::TestPeriodicBoundaryGeometry::test_translation_invariance",
      "tests/test_pair_finder.py::TestBasicPairRecovery::test_empty_catalog_returns_empty",
      "tests/test_pair_finder.py::TestBasicPairRecovery::test_no_double_counting",
      "tests/test_pair_finder.py::TestBasicPairRecovery::test_pair_at_max_sep_boundary",
      "tests/test_pair_finder.py::TestBasicPairRecovery::test_pair_beyond_max_sep_not_found",
      "tests/test_pair_finder.py::TestBasicPairRecovery::test_single_pair_found",
      "tests/test_pair_finder.py::TestBasicPairRecovery::test_single_pair_separation",
      "tests/test_pair_finder.py::TestMassAssignment::test_invalid_mass_bin_by_raises",
      "tests/test_pair_finder.py::TestMassAssignment::test_mass_bin_assignment",
      "tests/test_pair_finder.py::TestMassAssignment::test_mass_bin_by_mean",
      "tests/test_pair_finder.py::TestMassAssignment::test_mass_bin_by_secondary",
      "tests/test_pair_finder.py::TestMassAssignment::test_mass_bin_by_total",
      "tests/test_pair_finder.py::TestMassAssignment::test_mass_ratio_always_leq_1",
      "tests/test_pair_finder.py::TestMassAssignment::test_mass_ratio_cut_excludes_pair",
      "tests/test_pair_finder.py::TestMassAssignment::test_mass_ratio_cut_keeps_pair",
      "tests/test_pair_finder.py::TestMassAssignment::test_primary_is_more_massive",
      "tests/test_pair_finder.py::TestPeriodicBoundary::test_pair_across_boundary_velocity_unaffected",
      "tests/test_pair_finder.py::TestPeriodicBoundary::test_pair_across_corner",
      "tests/test_pair_finder.py::TestPeriodicBoundary::test_pair_across_x_boundary",
      "tests/test_pair_finder.py::TestSepBinAssignment::test_sep_bin_correct",
      "tests/test_pair_finder.py::TestSepBinAssignment::test_sep_bin_first_bin",
      "tests/test_pair_finder.py::TestSepBinAssignment::test_sep_bin_last_bin",
      "tests/test_pair_finder.py::TestVelocityRecovery::test_1d_velocity",
      "tests/test_pair_finder.py::TestVelocityRecovery::test_3d_velocity_all_components",
      "tests/test_pair_finder.py::TestVelocityRecovery::test_3d_velocity_pythagorean",
      "tests/test_pair_finder.py::TestVelocityRecovery::test_velocity_is_symmetric",
      "tests/test_pair_finder.py::TestVelocityRecovery::test_zero_relative_velocity",
      "tests/test_pair_finder_validation.py::TestBehaviorPreservation::test_empty_result_from_no_pairs",
      "tests/test_pair_finder_validation.py::TestBehaviorPreservation::test_mass_ratio_min_sentinel_preserved",
      "tests/test_pair_finder_validation.py::TestBehaviorPreservation::test_non_default_mass_grid_accepted",
      "tests/test_pair_finder_validation.py::TestBehaviorPreservation::test_non_default_sep_bins_accepted",
      "tests/test_pair_finder_validation.py::TestBehaviorPreservation::test_numpy_scalar_box_size_accepted",
      "tests/test_pair_finder_validation.py::TestBehaviorPreservation::test_numpy_scalar_config_values_accepted",
      "tests/test_pair_finder_validation.py::TestBehaviorPreservation::test_out_of_range_mass_bin_negative_one",
      "tests/test_pair_finder_validation.py::TestBehaviorPreservation::test_single_pair_still_found",
      "tests/test_pair_finder_validation.py::TestBehaviorPreservation::test_validation_before_early_return",
      "tests/test_pair_finder_validation.py::TestBehaviorPreservation::test_velocity_computation_unchanged",
      "tests/test_pair_finder_validation.py::TestCatalogArrayTypeValidation::test_catalog_vx_list_raises",
      "tests/test_pair_finder_validation.py::TestCatalogArrayTypeValidation::test_catalog_x_list_raises",
      "tests/test_pair_finder_validation.py::TestCatalogArrayTypeValidation::test_catalog_y_tuple_raises",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSizeValidation::test_catalog_box_size_bool_raises",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSizeValidation::test_catalog_box_size_complex_raises",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSizeValidation::test_catalog_box_size_inf_raises",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSizeValidation::test_catalog_box_size_list_raises",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSizeValidation::test_catalog_box_size_nan_raises",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSizeValidation::test_catalog_box_size_ndarray_raises",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSizeValidation::test_catalog_box_size_negative_raises",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSizeValidation::test_catalog_box_size_zero_raises",
      "tests/test_pair_finder_validation.py::TestCatalogDtypeConversion::test_catalog_int32_dtype_accepted",
      "tests/test_pair_finder_validation.py::TestCatalogDtypeConversion::test_catalog_int_converts_to_float_result",
      "tests/test_pair_finder_validation.py::TestCatalogDtypeConversion::test_catalog_uint16_dtype_accepted",
      "tests/test_pair_finder_validation.py::TestCatalogDtypeValidation::test_catalog_vx_object_dtype_raises",
      "tests/test_pair_finder_validation.py::TestCatalogDtypeValidation::test_catalog_x_bool_dtype_raises",
      "tests/test_pair_finder_validation.py::TestCatalogDtypeValidation::test_catalog_y_complex_dtype_raises",
      "tests/test_pair_finder_validation.py::TestCatalogDtypeValidation::test_catalog_z_string_dtype_raises",
      "tests/test_pair_finder_validation.py::TestCatalogExtraKeys::test_catalog_extra_key_accepted",
      "tests/test_pair_finder_validation.py::TestCatalogExtraKeys::test_catalog_extra_malformed_key_ignored",
      "tests/test_pair_finder_validation.py::TestCatalogFiniteValidation::test_catalog_log_stellar_mass_inf_raises",
      "tests/test_pair_finder_validation.py::TestCatalogFiniteValidation::test_catalog_vx_nan_raises",
      "tests/test_pair_finder_validation.py::TestCatalogFiniteValidation::test_catalog_x_nan_raises",
      "tests/test_pair_finder_validation.py::TestCatalogFiniteValidation::test_catalog_y_inf_raises",
      "tests/test_pair_finder_validation.py::TestCatalogFiniteValidation::test_catalog_z_neginf_raises",
      "tests/test_pair_finder_validation.py::TestCatalogFormValidation::test_catalog_box_size_missing_raises",
      "tests/test_pair_finder_validation.py::TestCatalogFormValidation::test_catalog_log_stellar_mass_missing_raises",
      "tests/test_pair_finder_validation.py::TestCatalogFormValidation::test_catalog_none_raises",
      "tests/test_pair_finder_validation.py::TestCatalogFormValidation::test_catalog_not_dict_raises",
      "tests/test_pair_finder_validation.py::TestCatalogFormValidation::test_catalog_vx_missing_raises",
      "tests/test_pair_finder_validation.py::TestCatalogFormValidation::test_catalog_vy_missing_raises",
      "tests/test_pair_finder_validation.py::TestCatalogFormValidation::test_catalog_vz_missing_raises",
      "tests/test_pair_finder_validation.py::TestCatalogFormValidation::test_catalog_x_missing_raises",
      "tests/test_pair_finder_validation.py::TestCatalogFormValidation::test_catalog_y_missing_raises",
      "tests/test_pair_finder_validation.py::TestCatalogFormValidation::test_catalog_z_missing_raises",
      "tests/test_pair_finder_validation.py::TestCatalogLengthValidation::test_catalog_vz_different_length_raises",
      "tests/test_pair_finder_validation.py::TestCatalogLengthValidation::test_catalog_x_different_length_raises",
      "tests/test_pair_finder_validation.py::TestCatalogPositionRangeValidation::test_catalog_x_at_zero_valid",
      "tests/test_pair_finder_validation.py::TestCatalogPositionRangeValidation::test_catalog_x_negative_raises",
      "tests/test_pair_finder_validation.py::TestCatalogPositionRangeValidation::test_catalog_y_equals_box_size_raises",
      "tests/test_pair_finder_validation.py::TestCatalogPositionRangeValidation::test_catalog_y_just_below_box_size_valid",
      "tests/test_pair_finder_validation.py::TestCatalogPositionRangeValidation::test_catalog_z_greater_than_box_size_raises",
      "tests/test_pair_finder_validation.py::TestCatalogRankValidation::test_catalog_vz_0d_raises",
      "tests/test_pair_finder_validation.py::TestCatalogRankValidation::test_catalog_x_2d_raises",
      "tests/test_pair_finder_validation.py::TestCatalogRankValidation::test_catalog_y_3d_raises",
      "tests/test_pair_finder_validation.py::TestCatalogZeroLength::test_catalog_empty_valid",
      "tests/test_pair_finder_validation.py::TestConfigFormValidation::test_config_log_mass_max_missing_raises",
      "tests/test_pair_finder_validation.py::TestConfigFormValidation::test_config_log_mass_min_missing_raises",
      "tests/test_pair_finder_validation.py::TestConfigFormValidation::test_config_mass_bin_by_missing_raises",
      "tests/test_pair_finder_validation.py::TestConfigFormValidation::test_config_mass_bin_width_missing_raises",
      "tests/test_pair_finder_validation.py::TestConfigFormValidation::test_config_mass_ratio_min_missing_raises",
      "tests/test_pair_finder_validation.py::TestConfigFormValidation::test_config_max_sep_missing_raises",
      "tests/test_pair_finder_validation.py::TestConfigFormValidation::test_config_not_dict_raises",
      "tests/test_pair_finder_validation.py::TestConfigFormValidation::test_config_sep_bins_missing_raises",
      "tests/test_pair_finder_validation.py::TestConfigMassBinByValidation::test_config_mass_bin_by_invalid_raises_value_error",
      "tests/test_pair_finder_validation.py::TestConfigMassBinByValidation::test_config_mass_bin_by_mean_accepted",
      "tests/test_pair_finder_validation.py::TestConfigMassBinByValidation::test_config_mass_bin_by_primary_accepted",
      "tests/test_pair_finder_validation.py::TestConfigMassBinByValidation::test_config_mass_bin_by_secondary_accepted",
      "tests/test_pair_finder_validation.py::TestConfigMassBinByValidation::test_config_mass_bin_by_total_accepted",
      "tests/test_pair_finder_validation.py::TestConfigMassBinValidation::test_config_log_mass_max_equal_to_min_raises",
      "tests/test_pair_finder_validation.py::TestConfigMassBinValidation::test_config_log_mass_max_inf_raises",
      "tests/test_pair_finder_validation.py::TestConfigMassBinValidation::test_config_log_mass_max_less_than_min_raises",
      "tests/test_pair_finder_validation.py::TestConfigMassBinValidation::test_config_log_mass_min_nan_raises",
      "tests/test_pair_finder_validation.py::TestConfigMassBinValidation::test_config_mass_bin_width_nan_raises",
      "tests/test_pair_finder_validation.py::TestConfigMassBinValidation::test_config_mass_bin_width_negative_raises",
      "tests/test_pair_finder_validation.py::TestConfigMassBinValidation::test_config_mass_bin_width_too_large_raises",
      "tests/test_pair_finder_validation.py::TestConfigMassBinValidation::test_config_mass_bin_width_zero_raises",
      "tests/test_pair_finder_validation.py::TestConfigMassRatioMinValidation::test_config_mass_ratio_min_greater_than_one_raises",
      "tests/test_pair_finder_validation.py::TestConfigMassRatioMinValidation::test_config_mass_ratio_min_nan_raises",
      "tests/test_pair_finder_validation.py::TestConfigMassRatioMinValidation::test_config_mass_ratio_min_negative_raises",
      "tests/test_pair_finder_validation.py::TestConfigMassRatioMinValidation::test_config_mass_ratio_min_one_valid",
      "tests/test_pair_finder_validation.py::TestConfigMassRatioMinValidation::test_config_mass_ratio_min_zero_valid",
      "tests/test_pair_finder_validation.py::TestConfigMaxSepValidation::test_config_max_sep_inf_raises",
      "tests/test_pair_finder_validation.py::TestConfigMaxSepValidation::test_config_max_sep_nan_raises",
      "tests/test_pair_finder_validation.py::TestConfigMaxSepValidation::test_config_max_sep_negative_raises",
      "tests/test_pair_finder_validation.py::TestConfigMaxSepValidation::test_config_max_sep_zero_raises",
      "tests/test_pair_finder_validation.py::TestConfigScalarValidation::test_config_log_mass_min_complex_raises",
      "tests/test_pair_finder_validation.py::TestConfigScalarValidation::test_config_mass_ratio_min_bool_raises",
      "tests/test_pair_finder_validation.py::TestConfigScalarValidation::test_config_max_sep_list_raises",
      "tests/test_pair_finder_validation.py::TestConfigScalarValidation::test_config_max_sep_ndarray_raises",
      "tests/test_pair_finder_validation.py::TestConfigSepBinsValidation::test_config_sep_bins_dict_raises",
      "tests/test_pair_finder_validation.py::TestConfigSepBinsValidation::test_config_sep_bins_duplicate_raises",
      "tests/test_pair_finder_validation.py::TestConfigSepBinsValidation::test_config_sep_bins_inf_raises",
      "tests/test_pair_finder_validation.py::TestConfigSepBinsValidation::test_config_sep_bins_list_accepted",
      "tests/test_pair_finder_validation.py::TestConfigSepBinsValidation::test_config_sep_bins_list_with_non_scalar_raises",
      "tests/test_pair_finder_validation.py::TestConfigSepBinsValidation::test_config_sep_bins_nan_raises",
      "tests/test_pair_finder_validation.py::TestConfigSepBinsValidation::test_config_sep_bins_ndarray_2d_raises",
      "tests/test_pair_finder_validation.py::TestConfigSepBinsValidation::test_config_sep_bins_ndarray_accepted",
      "tests/test_pair_finder_validation.py::TestConfigSepBinsValidation::test_config_sep_bins_ndarray_bool_dtype_raises",
      "tests/test_pair_finder_validation.py::TestConfigSepBinsValidation::test_config_sep_bins_ndarray_float_accepted",
      "tests/test_pair_finder_vali
```
