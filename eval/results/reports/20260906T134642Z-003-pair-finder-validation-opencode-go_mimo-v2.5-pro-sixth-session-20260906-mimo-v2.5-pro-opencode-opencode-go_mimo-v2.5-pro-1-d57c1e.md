# Trial report: 20260906T134642Z-003-pair-finder-validation-opencode-go_mimo-v2.5-pro-sixth-session-20260906-mimo-v2.5-pro-opencode-opencode-go_mimo-v2.5-pro-1-d57c1e

- Task: `003-pair-finder-validation`
- Model: `opencode-go/mimo-v2.5-pro` (harness: opencode)
- Model duration: 1191.1s | venv setup: 30.4s | timed out: False | committed: False
- Changed files: src/pair_finder.py, tests/test_pair_finder_validation.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 94.5 / 100

## Judged: readability 50% of weight, maintainability 50% of weight (judge claude-opus-5, status ok)

## Composite score: 87.8 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 100% |
| test_adequacy | automated | 25 | 81% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 100% |
| readability | judged | 8 | 50% |
| maintainability | judged | 7 | 50% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| rejection_matrix | 205 | 205 | 1.00 |
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
    "passed": 315,
    "failed": [],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "test_hA.py::test_A302_no_pairs_early_return_preserved PASSED       [ 86%]\ntests/test_hA.py::test_A303_mass_ratio_cut_early_return_preserved PASSED [ 86%]\ntests/test_hA.py::test_A304_empty_catalog_accepted PASSED                [ 87%]\ntests/test_hA.py::test_A305_mass_bin_sentinel_above_range PASSED         [ 87%]\ntests/test_hA.py::test_A306_mass_bin_sentinel_below_range PASSED         [ 87%]\ntests/test_hA.py::test_A307_sep_bin_sentinel_beyond_last_edge PASSED     [ 88%]\ntests/test_hA.py::test_A308_unknown_mass_bin_by_still_raises_value_error PASSED [ 88%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[primary] PASSED [ 88%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[secondary] PASSED [ 89%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[mean] PASSED [ 89%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[total] PASSED [ 89%]\ntests/test_hA.py::test_A310_signature_unchanged PASSED                   [ 90%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int16-ascending_dv] PASSED [ 90%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int16-descending_dv] PASSED [ 90%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint16-ascending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint16-descending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int32-ascending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int32-descending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint32-ascending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint32-descending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int64-ascending_dv] PASSED [ 93%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int64-descending_dv] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vx] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vy] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vz] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vx] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vy] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vz] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vx] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vy] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vz] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vx] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vy] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vz] PASSED [ 97%]\ntests/test_hA.py::test_A311_validation_precedes_no_pairs_return_nonfinite PASSED [ 97%]\ntests/test_hA.py::test_A312_validation_precedes_no_pairs_return_length PASSED [ 97%]\ntests/test_hA.py::test_A313_validation_precedes_mass_ratio_cut_return PASSED [ 98%]\ntests/test_hB.py::test_B00_pipeline_imports PASSED                       [ 98%]\ntests/test_hB.py::test_B01_driver_output_matches_the_analytic_expectation PASSED [ 98%]\ntests/test_hB.py::test_B02_nonfinite_position_on_disk_asserts PASSED     [ 99%]\ntests/test_hB.py::test_B03_position_outside_box_on_disk_asserts PASSED   [ 99%]\ntests/test_hB.py::test_B04_malformed_config_through_driver PASSED        [ 99%]\ntests/test_hB.py::test_B05_driver_honours_nondefault_config PASSED       [100%]\n\n============================= 315 passed in 0.77s ==============================\n",
    "stderr_tail": "",
    "obligations": [
      {
        "id": "rejection_matrix",
        "passed": 205,
        "collected": 205,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
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
      "tests/test_pair_finder_validation.py::TestCatalogArrayForm::test_0d_array_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogArrayForm::test_2d_array_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogArrayForm::test_bool_dtype_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogArrayForm::test_bytes_dtype_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogArrayForm::test_complex_dtype_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogArrayForm::test_list_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogArrayForm::test_object_dtype_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogArrayForm::test_string_dtype_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogArrayForm::test_tuple_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_box_size_0d_array_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_box_size_bool_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_box_size_complex_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_box_size_inf_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_box_size_nan_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_box_size_ndarray_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_box_size_negative_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_box_size_string_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_box_size_zero_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogFiniteness::test_inf_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogFiniteness::test_log_stellar_mass_inf_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogFiniteness::test_nan_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogFiniteness::test_neg_inf_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogFiniteness::test_vx_nan_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_catalog_list",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_catalog_none",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_catalog_string",
      "tests/test_pair_finder_validation.py::TestCatalogPositionBounds::test_negative_x_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogPositionBounds::test_negative_y_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogPositionBounds::test_x_above_box_size_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogPositionBounds::test_x_at_box_size_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogPositionBounds::test_z_at_box_size_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogRequiredKeys::test_missing_key[box_size]",
      "tests/test_pair_finder_validation.py::TestCatalogRequiredKeys::test_missing_key[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogRequiredKeys::test_missing_key[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogRequiredKeys::test_missing_key[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogRequiredKeys::test_missing_key[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogRequiredKeys::test_missing_key[x]",
      "tests/test_pair_finder_validation.py::TestCatalogRequiredKeys::test_missing_key[y]",
      "tests/test_pair_finder_validation.py::TestCatalogRequiredKeys::test_missing_key[z]",
      "tests/test_pair_finder_validation.py::TestCatalogSameLength::test_longer_array",
      "tests/test_pair_finder_validation.py::TestCatalogSameLength::test_shorter_array",
      "tests/test_pair_finder_validation.py::TestConfigForm::test_config_list",
      "tests/test_pair_finder_validation.py::TestConfigForm::test_config_none",
      "tests/test_pair_finder_validation.py::TestConfigForm::test_config_string",
      "tests/test_pair_finder_validation.py::TestConfigMassGrid::test_log_mass_max_eq_min_rejected",
      "tests/test_pair_finder_validation.py::TestConfigMassGrid::test_log_mass_max_lt_min_rejected",
      "tests/test_pair_finder_validation.py::TestConfigMassGrid::test_mass_bin_width_negative_rejected",
      "tests/test_pair_finder_validation.py::TestConfigMassGrid::test_mass_bin_width_zero_rejected",
      "tests/test_pair_finder_validation.py::TestConfigMassGrid::test_no_mass_bins_rejected",
      "tests/test_pair_finder_validation.py::TestConfigMassRatioMin::test_above_one_rejected",
      "tests/test_pair_finder_validation.py::TestConfigMassRatioMin::test_below_zero_rejected",
      "tests/test_pair_finder_validation.py::TestConfigMassRatioMin::test_exactly_one_accepted",
      "tests/test_pair_finder_validation.py::TestConfigMassRatioMin::test_exactly_zero_accepted",
      "tests/test_pair_finder_validation.py::TestConfigMaxSep::test_negative_rejected",
      "tests/test_pair_finder_validation.py::TestConfigMaxSep::test_zero_rejected",
      "tests/test_pair_finder_validation.py::TestConfigRequiredKeys::test_missing_key[log_mass_max]",
      "tests/test_pair_finder_validation.py::TestConfigRequiredKeys::test_missing_key[log_mass_min]",
      "tests/test_pair_finder_validation.py::TestConfigRequiredKeys::test_missing_key[mass_bin_by]",
      "tests/test_pair_finder_validation.py::TestConfigRequiredKeys::test_missing_key[mass_bin_width]",
      "tests/test_pair_finder_validation.py::TestConfigRequiredKeys::test_missing_key[mass_ratio_min]",
      "tests/test_pair_finder_validation.py::TestConfigRequiredKeys::test_missing_key[max_sep]",
      "tests/test_pair_finder_validation.py::TestConfigRequiredKeys::test_missing_key[sep_bins]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_bool_rejected[log_mass_max]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_bool_rejected[log_mass_min]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_bool_rejected[mass_bin_width]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_bool_rejected[mass_ratio_min]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_bool_rejected[max_sep]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_complex_rejected[log_mass_max]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_complex_rejected[log_mass_min]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_complex_rejected[mass_bin_width]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_complex_rejected[mass_ratio_min]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_complex_rejected[max_sep]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_inf_rejected[log_mass_max]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_inf_rejected[log_mass_min]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_inf_rejected[mass_bin_width]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_inf_rejected[mass_ratio_min]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_inf_rejected[max_sep]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_nan_rejected[log_mass_max]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_nan_rejected[log_mass_min]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_nan_rejected[mass_bin_width]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_nan_rejected[mass_ratio_min]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_nan_rejected[max_sep]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_ndarray_rejected[log_mass_max]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_ndarray_rejected[log_mass_min]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_ndarray_rejected[mass_bin_width]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_ndarray_rejected[mass_ratio_min]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_ndarray_rejected[max_sep]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_numpy_int_scalar_accepted[log_mass_max]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_numpy_int_scalar_accepted[log_mass_min]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_numpy_int_scalar_accepted[mass_bin_width]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_numpy_int_scalar_accepted[mass_ratio_min]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_numpy_int_scalar_accepted[max_sep]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_numpy_scalar_accepted[log_mass_max]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_numpy_scalar_accepted[log_mass_min]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_numpy_scalar_accepted[mass_bin_width]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_numpy_scalar_accepted[mass_ratio_min]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_numpy_scalar_accepted[max_sep]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_string_rejected[log_mass_max]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_string_rejected[log_mass_min]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_string_rejected[mass_bin_width]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_string_rejected[mass_ratio_min]",
      "tests/test_pair_finder_validation.py::TestConfigScalars::test_string_rejected[max_sep]",
      "tests/test_pair_finder_validation.py::TestConfigSepBins::test_decreasing_rejected",
      "tests/test_pair_finder_validation.py::TestConfigSepBins::test_duplicate_edge_rejected",
      "tests/test_pair_finder_validation.py::TestConfigSepBins::test_empty_list_rejected",
      "tests/test_pair_finder_validation.py::TestConfigSepBins::test_float_tuple_accepted",
      "tests/test_pair_finder_validation.py::TestConfigSepBins::test_inf_rejected",
      "tests/test_pair_finder_validation.py::TestConfigSepBins::test_int_list_accepted",
      "tests/test_pair_finder_validation.py::TestConfigSepBins::test_int_rejected",
      "tests/test_pair_finder_validation.py::TestConfigSepBins::test_list_element_bool_rejected",
      "tests/test_pair_finder_validation.py::TestConfigSepBins::test_list_element_complex_rejected",
      "tests/test_pair_finder_validation.py::TestConfigSepBins::test_list_element_ndarray_rejected",
      "tests/test_pair_finder_validation.py::TestConfigSepBins::test_list_element_string_rejected",
      "tests/test_pair_finder_validation.py::TestConfigSepBins::test_nan_rejected",
      "tests/test_pair_finder_validation.py::TestConfigSepBins::test_ndarray_2d_rejected",
      "tests/test_pair_finder_validation.py::TestConfigSepBins::test_ndarray_bool_dtype_rejected",
      "tests/test_pair_finder_validation.py::TestConfigSepBins::test_ndarray_string_dtype_rejected",
      "tests/test_pair_finder_validation.py::TestConfigSepBins::test_numpy_float_array_accepted",
      "tests/test_pair_finder_validation.py::TestConfigSepBins::test_numpy_int_array_ac
```
