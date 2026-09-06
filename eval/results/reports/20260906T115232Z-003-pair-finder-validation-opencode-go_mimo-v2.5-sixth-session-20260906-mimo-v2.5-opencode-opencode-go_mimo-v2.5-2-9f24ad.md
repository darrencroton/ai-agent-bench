# Trial report: 20260906T115232Z-003-pair-finder-validation-opencode-go_mimo-v2.5-sixth-session-20260906-mimo-v2.5-opencode-opencode-go_mimo-v2.5-2-9f24ad

- Task: `003-pair-finder-validation`
- Model: `opencode-go/mimo-v2.5` (harness: opencode)
- Model duration: 420.5s | venv setup: 29.2s | timed out: False | committed: False
- Changed files: src/pair_finder.py, tests/test_pair_finder_validation.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 92.9 / 100

## Judged: readability 75% of weight, maintainability 50% of weight (judge claude-opus-5, status ok)

## Composite score: 88.4 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 100% |
| test_adequacy | automated | 25 | 76% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 100% |
| readability | judged | 8 | 75% |
| maintainability | judged | 7 | 50% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| rejection_matrix | 204 | 205 | 1.00 |
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
  "grader_git_rev": "c694b1064b22a735ff2d76bded64e31ddd49df7e",
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
    "passed": 314,
    "failed": [
      "tests/test_hA.py::test_A100_rejects[order_width_positive_before_range]"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "tegies_still_work[primary] PASSED [ 88%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[secondary] PASSED [ 89%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[mean] PASSED [ 89%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[total] PASSED [ 89%]\ntests/test_hA.py::test_A310_signature_unchanged PASSED                   [ 90%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int16-ascending_dv] PASSED [ 90%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int16-descending_dv] PASSED [ 90%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint16-ascending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint16-descending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int32-ascending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int32-descending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint32-ascending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint32-descending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int64-ascending_dv] PASSED [ 93%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int64-descending_dv] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vx] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vy] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vz] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vx] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vy] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vz] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vx] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vy] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vz] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vx] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vy] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vz] PASSED [ 97%]\ntests/test_hA.py::test_A311_validation_precedes_no_pairs_return_nonfinite PASSED [ 97%]\ntests/test_hA.py::test_A312_validation_precedes_no_pairs_return_length PASSED [ 97%]\ntests/test_hA.py::test_A313_validation_precedes_mass_ratio_cut_return PASSED [ 98%]\ntests/test_hB.py::test_B00_pipeline_imports PASSED                       [ 98%]\ntests/test_hB.py::test_B01_driver_output_matches_the_analytic_expectation PASSED [ 98%]\ntests/test_hB.py::test_B02_nonfinite_position_on_disk_asserts PASSED     [ 99%]\ntests/test_hB.py::test_B03_position_outside_box_on_disk_asserts PASSED   [ 99%]\ntests/test_hB.py::test_B04_malformed_config_through_driver PASSED        [ 99%]\ntests/test_hB.py::test_B05_driver_honours_nondefault_config PASSED       [100%]\n\n=================================== FAILURES ===================================\n_____________ test_A100_rejects[order_width_positive_before_range] _____________\ntests/test_hA.py:510: in test_A100_rejects\n    assert token in message, (\nE   AssertionError: message does not contain the required reason token 'positive': 'log_mass_max: expected greater than log_mass_min'\nE   assert 'positive' in 'log_mass_max: expected greater than log_mass_min'\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A100_rejects[order_width_positive_before_range]\n======================== 1 failed, 314 passed in 0.68s =========================\n",
    "stderr_tail": "",
    "obligations": [
      {
        "id": "rejection_matrix",
        "passed": 204,
        "collected": 205,
        "fraction": 0.9951219512195122,
        "uncollected": false,
        "failed_nodes": [
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
      "tests/test_pair_finder_validation.py::TestBehaviourPreserved::test_all_four_mass_bin_by_strategies",
      "tests/test_pair_finder_validation.py::TestBehaviourPreserved::test_empty_result_dtypes",
      "tests/test_pair_finder_validation.py::TestBehaviourPreserved::test_mass_bin_by_unknown_raises_value_error",
      "tests/test_pair_finder_validation.py::TestBehaviourPreserved::test_mass_bin_out_of_range_sentinel",
      "tests/test_pair_finder_validation.py::TestBehaviourPreserved::test_mass_ratio_min_one_empty_result",
      "tests/test_pair_finder_validation.py::TestBehaviourPreserved::test_sep_bin_out_of_range_sentinel",
      "tests/test_pair_finder_validation.py::TestBoxSize::test_box_size_bool",
      "tests/test_pair_finder_validation.py::TestBoxSize::test_box_size_complex",
      "tests/test_pair_finder_validation.py::TestBoxSize::test_box_size_inf",
      "tests/test_pair_finder_validation.py::TestBoxSize::test_box_size_nan",
      "tests/test_pair_finder_validation.py::TestBoxSize::test_box_size_ndarray",
      "tests/test_pair_finder_validation.py::TestBoxSize::test_box_size_negative",
      "tests/test_pair_finder_validation.py::TestBoxSize::test_box_size_string",
      "tests/test_pair_finder_validation.py::TestBoxSize::test_box_size_zero",
      "tests/test_pair_finder_validation.py::TestCatalogArrayTypes::test_vx_is_list",
      "tests/test_pair_finder_validation.py::TestCatalogArrayTypes::test_x_is_list",
      "tests/test_pair_finder_validation.py::TestCatalogArrayTypes::test_x_is_string",
      "tests/test_pair_finder_validation.py::TestCatalogArrayTypes::test_x_is_tuple",
      "tests/test_pair_finder_validation.py::TestCatalogDimensionality::test_log_stellar_mass_2d",
      "tests/test_pair_finder_validation.py::TestCatalogDimensionality::test_x_2d",
      "tests/test_pair_finder_validation.py::TestCatalogDimensionality::test_y_2d",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_x_bool_dtype",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_x_bytes_dtype",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_x_complex",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_x_object_dtype",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_x_string_dtype",
      "tests/test_pair_finder_validation.py::TestCatalogFiniteness::test_log_stellar_mass_inf",
      "tests/test_pair_finder_validation.py::TestCatalogFiniteness::test_log_stellar_mass_nan",
      "tests/test_pair_finder_validation.py::TestCatalogFiniteness::test_vx_nan",
      "tests/test_pair_finder_validation.py::TestCatalogFiniteness::test_x_inf",
      "tests/test_pair_finder_validation.py::TestCatalogFiniteness::test_x_nan",
      "tests/test_pair_finder_validation.py::TestCatalogFiniteness::test_x_neg_inf",
      "tests/test_pair_finder_validation.py::TestCatalogFiniteness::test_y_nan",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_catalog_is_list",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_catalog_is_none",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_catalog_not_dict",
      "tests/test_pair_finder_validation.py::TestCatalogLengthMismatch::test_vz_different_length",
      "tests/test_pair_finder_validation.py::TestCatalogLengthMismatch::test_x_different_length",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_missing_box_size",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_missing_log_stellar_mass",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_missing_vx",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_missing_vy",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_missing_vz",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_missing_x",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_missing_y",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_missing_z",
      "tests/test_pair_finder_validation.py::TestCheckOrder::test_box_size_nan_reported_as_finite_not_positive",
      "tests/test_pair_finder_validation.py::TestCheckOrder::test_mass_bin_width_inf_reported_as_finite",
      "tests/test_pair_finder_validation.py::TestCheckOrder::test_nan_in_x_reported_as_finite_not_box",
      "tests/test_pair_finder_validation.py::TestCheckOrder::test_sep_bins_nan_finite_before_monotonicity",
      "tests/test_pair_finder_validation.py::TestConfigForm::test_config_is_list",
      "tests/test_pair_finder_validation.py::TestConfigForm::test_config_is_none",
      "tests/test_pair_finder_validation.py::TestConfigForm::test_config_not_dict",
      "tests/test_pair_finder_validation.py::TestConfigMissingKeys::test_missing_log_mass_max",
      "tests/test_pair_finder_validation.py::TestConfigMissingKeys::test_missing_log_mass_min",
      "tests/test_pair_finder_validation.py::TestConfigMissingKeys::test_missing_mass_bin_by",
      "tests/test_pair_finder_validation.py::TestConfigMissingKeys::test_missing_mass_bin_width",
      "tests/test_pair_finder_validation.py::TestConfigMissingKeys::test_missing_mass_ratio_min",
      "tests/test_pair_finder_validation.py::TestConfigMissingKeys::test_missing_max_sep",
      "tests/test_pair_finder_validation.py::TestConfigMissingKeys::test_missing_sep_bins",
      "tests/test_pair_finder_validation.py::TestCorrectnessPreserved::test_mass_ratio_exact",
      "tests/test_pair_finder_validation.py::TestCorrectnessPreserved::test_periodic_boundary_pair",
      "tests/test_pair_finder_validation.py::TestCorrectnessPreserved::test_separation_exact",
      "tests/test_pair_finder_validation.py::TestCorrectnessPreserved::test_velocity_pythagorean",
      "tests/test_pair_finder_validation.py::TestExtraCatalogKeys::test_extra_keys_ignored",
      "tests/test_pair_finder_validation.py::TestIntegerDtypes::test_int64_catalog_matches_float64",
      "tests/test_pair_finder_validation.py::TestIntegerDtypes::test_uint64_catalog_matches_float64",
      "tests/test_pair_finder_validation.py::TestLogMassRange::test_log_mass_max_bool",
      "tests/test_pair_finder_validation.py::TestLogMassRange::test_log_mass_max_equal_to_min",
      "tests/test_pair_finder_validation.py::TestLogMassRange::test_log_mass_max_inf",
      "tests/test_pair_finder_validation.py::TestLogMassRange::test_log_mass_max_nan",
      "tests/test_pair_finder_validation.py::TestLogMassRange::test_log_mass_max_not_greater_than_min",
      "tests/test_pair_finder_validation.py::TestLogMassRange::test_log_mass_max_string",
      "tests/test_pair_finder_validation.py::TestLogMassRange::test_log_mass_min_inf",
      "tests/test_pair_finder_validation.py::TestLogMassRange::test_log_mass_min_nan",
      "tests/test_pair_finder_validation.py::TestLogMassRange::test_log_mass_min_ndarray",
      "tests/test_pair_finder_validation.py::TestLogMassRange::test_log_mass_min_string",
      "tests/test_pair_finder_validation.py::TestMassBinWidth::test_mass_bin_width_bool",
      "tests/test_pair_finder_validation.py::TestMassBinWidth::test_mass_bin_width_inf",
      "tests/test_pair_finder_validation.py::TestMassBinWidth::test_mass_bin_width_nan",
      "tests/test_pair_finder_validation.py::TestMassBinWidth::test_mass_bin_width_ndarray",
      "tests/test_pair_finder_validation.py::TestMassBinWidth::test_mass_bin_width_negative",
      "tests/test_pair_finder_validation.py::TestMassBinWidth::test_mass_bin_width_string",
      "tests/test_pair_finder_validation.py::TestMassBinWidth::test_mass_bin_width_too_large",
      "tests/test_pair_finder_validation.py::TestMassBinWidth::test_mass_bin_width_zero",
      "tests/test_pair_finder_validation.py::TestMassRatioMin::test_mass_ratio_min_bool",
      "tests/test_pair_finder_validation.py::TestMassRatioMin::test_mass_ratio_min_greater_than_one",
      "tests/test_pair_finder_validation.py::TestMassRatioMin::test_mass_ratio_min_inf",
      "tests/test_pair_finder_validation.py::TestMassRatioMin::test_mass_ratio_min_nan",
      "tests/test_pair_finder_validation.py::TestMassRatioMin::test_mass_ratio_min_ndarray",
      "tests/test_pair_finder_validation.py::TestMassRatioMin::test_mass_ratio_min_negative",
      "tests/test_pair_finder_validation.py::TestMassRatioMin::test_mass_ratio_min_string",
      "tests/test_pair_finder_validation.py::TestMaxSep::test_max_sep_bool",
      "tests/test_pair_finder_validation.py::TestMaxSep::test_max_sep_inf",
      "tests/test_pair_finder_validation.py::TestMaxSep::test_max_sep_nan",
      "tests/test_pair_finder_validation.py::TestMaxSep::test_max_sep_ndarray",
      "tests/test_pair_finder_validation.py::TestMaxSep::test_max_sep_negative",
      "tests/test_pair_finder_validation.py::TestMaxSep::test_max_sep_string",
      "tests/test_pair_finder_validation.py::TestMaxSep::test_max_sep_zero",
      "tests/test_pair_finder_validation.py::TestPositionRange::test_x_geq_box_size",
      "tests/test_pair_finder_validation.py::TestPositionRange::test_x_negative",
      "tests/test_pair_finder_validation.py::TestPositionRange::test_y_geq_box_size",
      "tests/test_pair_finder_validation.py::TestPositionRange::test_z_geq_box_size",
      "tests/test_pair_finder_validation.py::TestSepBins::test_sep_bins_bool",
      "tests/test_pair_finder_validation.py::TestSepBins::test_sep_bins_duplicate_edge",
      "tests/test_pair_finder_validation.py::TestSepBins::test_sep_bins_empty",
      "tests/test_pair_finder_validation.py::TestSepBins::test_sep_bins_list_with_bool_element",
      "tests/test_pair_finder_validation.py::TestSepBins::test_sep_bins_list_with_ndarray_element",
      "tests/test_pair_finder_validation.py::TestSepBins::test_sep_bins_list_with_string_element",
      "tests/test_pair_finder_validation.py::TestSepBins::test_sep_bins_nan_in_list",
      "tests/test_pair_finder_validation.py::TestSepBins::test_sep_bins_nan_in_ndarray",
      "tests/test_pair_finder_validation.py::TestSepBins::test_sep_bins_ndarray_2d",
      "tests/test_pair_finder_validation.py::TestSepBins::test_sep_bins_ndarray_bad_dtype",
      "tests/test_pair_finder_validation.py::TestSepBins::test_sep_bins_not_increasing",
      "tests/test_pair_finder_validation.py::TestSepBins::test_sep_bins_not_list_tuple_ndarray",
      "tests/test_pair_finder_validation.py::TestSepBins::test_sep_bins_single_element",
      "tests/test_pair_finder_validation.py::TestSignaturePreserved::test_two_positional_parameters",
      "tests/test_pair_finder_validation.py::TestValidInputs::test_float_ndarray_sep_bins",
      "tests/test_pair_finder_validation.py::TestValidInputs::test_float_tuple_sep_bins",
      "tests/test_pair_finder_validation.py::TestValidInputs::test_int_list_sep_bins",
      "tests/test_pair_finder_validation.py::TestValidInputs::test_int_ndarray_sep_bins",
      "tests/test_pair_finder_validation.py::TestValidInputs::test_log_stellar_mass_outside_config_range",
      "tests/test_pair_finder_validation.py::TestValidInputs::test_mass_ratio_min_one",
      "tests/test_pair_finder_validation.py::TestValidInputs::test_mass_ratio_min_zero",
      "tests/test_pair_finder_validation.py::TestValidInputs::test_negative_finite_mass",
      "tests/test_pair_finder_validation.py::TestValidInputs
```
