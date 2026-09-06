# Trial report: 20260906T125239Z-003-pair-finder-validation-opencode-go_longcat-2.0-sixth-session-20260906-longcat-2.0-opencode-opencode-go_longcat-2.0-2-ca0997

- Task: `003-pair-finder-validation`
- Model: `opencode-go/longcat-2.0` (harness: opencode)
- Model duration: 702.4s | venv setup: 29.3s | timed out: False | committed: False
- Changed files: src/pair_finder.py, tests/test_pair_finder_validation.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 90.1 / 100

## Judged: readability 50% of weight, maintainability 25% of weight (judge claude-opus-5, status ok)

## Composite score: 82.4 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 100% |
| test_adequacy | automated | 25 | 70% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 91% |
| readability | judged | 8 | 50% |
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
    "passed": 313,
    "failed": [
      "tests/test_hA.py::test_A100_rejects[mass_bin_width_value_10.0]",
      "tests/test_hA.py::test_A100_rejects[order_width_positive_before_range]"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "_its_float_twin[int16-descending_dv] PASSED [ 90%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint16-ascending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint16-descending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int32-ascending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int32-descending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint32-ascending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint32-descending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int64-ascending_dv] PASSED [ 93%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int64-descending_dv] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vx] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vy] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vz] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vx] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vy] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vz] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vx] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vy] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vz] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vx] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vy] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vz] PASSED [ 97%]\ntests/test_hA.py::test_A311_validation_precedes_no_pairs_return_nonfinite PASSED [ 97%]\ntests/test_hA.py::test_A312_validation_precedes_no_pairs_return_length PASSED [ 97%]\ntests/test_hA.py::test_A313_validation_precedes_mass_ratio_cut_return PASSED [ 98%]\ntests/test_hB.py::test_B00_pipeline_imports PASSED                       [ 98%]\ntests/test_hB.py::test_B01_driver_output_matches_the_analytic_expectation PASSED [ 98%]\ntests/test_hB.py::test_B02_nonfinite_position_on_disk_asserts PASSED     [ 99%]\ntests/test_hB.py::test_B03_position_outside_box_on_disk_asserts PASSED   [ 99%]\ntests/test_hB.py::test_B04_malformed_config_through_driver PASSED        [ 99%]\ntests/test_hB.py::test_B05_driver_honours_nondefault_config PASSED       [100%]\n\n=================================== FAILURES ===================================\n_________________ test_A100_rejects[mass_bin_width_value_10.0] _________________\ntests/test_hA.py:513: in test_A100_rejects\n    assert any(re.search(rf\"\\b{re.escape(n)}\\b\", message) for n in names), (\nE   AssertionError: message names none of ['mass_bin_width']: 'mass grid must define at least one mass bin'\nE   assert False\nE    +  where False = any(<generator object test_A100_rejects.<locals>.<genexpr> at 0x109ba8140>)\n_____________ test_A100_rejects[order_width_positive_before_range] _____________\ntests/test_hA.py:510: in test_A100_rejects\n    assert token in message, (\nE   AssertionError: message does not contain the required reason token 'positive': 'log_mass_max (7.0) must be greater than log_mass_min (8.0)'\nE   assert 'positive' in 'log_mass_max (7.0) must be greater than log_mass_min (8.0)'\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A100_rejects[mass_bin_width_value_10.0] - Asser...\nFAILED tests/test_hA.py::test_A100_rejects[order_width_positive_before_range]\n======================== 2 failed, 313 passed in 0.76s =========================\n",
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
      "tests/test_pair_finder_validation.py::TestArrayFieldDtype::test_bool_dtype_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestArrayFieldDtype::test_bool_dtype_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestArrayFieldDtype::test_bool_dtype_rejected[x]",
      "tests/test_pair_finder_validation.py::TestArrayFieldDtype::test_complex_dtype_rejected",
      "tests/test_pair_finder_validation.py::TestArrayFieldDtype::test_string_dtype_rejected",
      "tests/test_pair_finder_validation.py::TestArrayFieldFinite::test_inf_in_vel",
      "tests/test_pair_finder_validation.py::TestArrayFieldFinite::test_nan_in_x",
      "tests/test_pair_finder_validation.py::TestArrayFieldLength::test_unequal_lengths",
      "tests/test_pair_finder_validation.py::TestArrayFieldNdarray::test_field_is_list_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestArrayFieldNdarray::test_field_is_list_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestArrayFieldNdarray::test_field_is_list_rejected[x]",
      "tests/test_pair_finder_validation.py::TestArrayFieldNdarray::test_field_is_tuple_rejected[vz]",
      "tests/test_pair_finder_validation.py::TestArrayFieldNdarray::test_field_is_tuple_rejected[y]",
      "tests/test_pair_finder_validation.py::TestArrayFieldRank::test_2d_position_rejected",
      "tests/test_pair_finder_validation.py::TestArrayFieldRank::test_2d_velocity_rejected",
      "tests/test_pair_finder_validation.py::TestBoxSize::test_box_size_bool_rejected",
      "tests/test_pair_finder_validation.py::TestBoxSize::test_box_size_nan",
      "tests/test_pair_finder_validation.py::TestBoxSize::test_box_size_ndarray_rejected",
      "tests/test_pair_finder_validation.py::TestBoxSize::test_box_size_negative",
      "tests/test_pair_finder_validation.py::TestBoxSize::test_box_size_string",
      "tests/test_pair_finder_validation.py::TestBoxSize::test_box_size_zero",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_catalog_list",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_catalog_none",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_catalog_not_dict",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_missing_array_field[box_size]",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_missing_array_field[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_missing_array_field[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_missing_array_field[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_missing_array_field[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_missing_array_field[x]",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_missing_array_field[y]",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_missing_array_field[z]",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_missing_box_size",
      "tests/test_pair_finder_validation.py::TestConfigForm::test_config_not_dict",
      "tests/test_pair_finder_validation.py::TestConfigMissingKeys::test_missing_config_key[log_mass_max]",
      "tests/test_pair_finder_validation.py::TestConfigMissingKeys::test_missing_config_key[log_mass_min]",
      "tests/test_pair_finder_validation.py::TestConfigMissingKeys::test_missing_config_key[mass_bin_by]",
      "tests/test_pair_finder_validation.py::TestConfigMissingKeys::test_missing_config_key[mass_bin_width]",
      "tests/test_pair_finder_validation.py::TestConfigMissingKeys::test_missing_config_key[mass_ratio_min]",
      "tests/test_pair_finder_validation.py::TestConfigMissingKeys::test_missing_config_key[max_sep]",
      "tests/test_pair_finder_validation.py::TestConfigMissingKeys::test_missing_config_key[sep_bins]",
      "tests/test_pair_finder_validation.py::TestIntegerDtypes::test_signed_int_catalog_matches_float",
      "tests/test_pair_finder_validation.py::TestIntegerDtypes::test_signed_int_mass_ratio_works",
      "tests/test_pair_finder_validation.py::TestIntegerDtypes::test_unsigned_int_catalog_matches_float",
      "tests/test_pair_finder_validation.py::TestMassBinWidth::test_inf_reports_finite",
      "tests/test_pair_finder_validation.py::TestMassBinWidth::test_negative_rejected",
      "tests/test_pair_finder_validation.py::TestMassBinWidth::test_too_few_bins_rejected",
      "tests/test_pair_finder_validation.py::TestMassBinWidth::test_zero_rejected",
      "tests/test_pair_finder_validation.py::TestMassRange::test_log_mass_max_equals_min_rejected",
      "tests/test_pair_finder_validation.py::TestMassRange::test_log_mass_max_less_than_min_rejected",
      "tests/test_pair_finder_validation.py::TestMassRatioMin::test_greater_than_one_rejected",
      "tests/test_pair_finder_validation.py::TestMassRatioMin::test_nan_rejected",
      "tests/test_pair_finder_validation.py::TestMassRatioMin::test_negative_rejected",
      "tests/test_pair_finder_validation.py::TestMaxSep::test_max_sep_nan",
      "tests/test_pair_finder_validation.py::TestMaxSep::test_max_sep_ndarray_rejected",
      "tests/test_pair_finder_validation.py::TestMaxSep::test_max_sep_negative",
      "tests/test_pair_finder_validation.py::TestMaxSep::test_max_sep_string",
      "tests/test_pair_finder_validation.py::TestMaxSep::test_max_sep_zero",
      "tests/test_pair_finder_validation.py::TestPositionRange::test_coord_at_box_size_rejected",
      "tests/test_pair_finder_validation.py::TestPositionRange::test_coord_just_below_box_size_valid",
      "tests/test_pair_finder_validation.py::TestPositionRange::test_coord_zero_valid",
      "tests/test_pair_finder_validation.py::TestPositionRange::test_nan_in_x_reports_finite_not_box",
      "tests/test_pair_finder_validation.py::TestPositionRange::test_negative_coord_rejected",
      "tests/test_pair_finder_validation.py::TestSepBins::test_2d_ndarray_rejected",
      "tests/test_pair_finder_validation.py::TestSepBins::test_duplicate_edge_rejected",
      "tests/test_pair_finder_validation.py::TestSepBins::test_list_with_string_element_rejected",
      "tests/test_pair_finder_validation.py::TestSepBins::test_nan_edge_reports_finite",
      "tests/test_pair_finder_validation.py::TestSepBins::test_ndarray_string_dtype_rejected",
      "tests/test_pair_finder_validation.py::TestSepBins::test_not_list_tuple_ndarray_rejected",
      "tests/test_pair_finder_validation.py::TestSepBins::test_too_few_edges_rejected",
      "tests/test_pair_finder_validation.py::TestSepBins::test_unsorted_rejected",
      "tests/test_pair_finder_validation.py::TestUnchangedBehaviour::test_all_four_mass_bin_by_strategies",
      "tests/test_pair_finder_validation.py::TestUnchangedBehaviour::test_empty_result_dtypes",
      "tests/test_pair_finder_validation.py::TestUnchangedBehaviour::test_mass_bin_by_present_passes_validation",
      "tests/test_pair_finder_validation.py::TestUnchangedBehaviour::test_mass_bin_by_value_error_preserved",
      "tests/test_pair_finder_validation.py::TestUnchangedBehaviour::test_mass_outside_range_gets_minus_one_bin",
      "tests/test_pair_finder_validation.py::TestUnchangedBehaviour::test_mass_ratio_cut_early_return_dtypes",
      "tests/test_pair_finder_validation.py::TestUnchangedBehaviour::test_negative_finite_masses_accepted",
      "tests/test_pair_finder_validation.py::TestUnchangedBehaviour::test_sep_bin_out_of_range_minus_one",
      "tests/test_pair_finder_validation.py::TestUnchangedBehaviour::test_signature_still_two_positional",
      "tests/test_pair_finder_validation.py::TestUnchangedBehaviour::test_unchanged_pair_properties",
      "tests/test_pair_finder_validation.py::TestValidInputsAccepted::test_extra_keys_ignored",
      "tests/test_pair_finder_validation.py::TestValidInputsAccepted::test_extra_malformed_extra_key_ignored",
      "tests/test_pair_finder_validation.py::TestValidInputsAccepted::test_mass_ratio_min_one_valid",
      "tests/test_pair_finder_validation.py::TestValidInputsAccepted::test_mass_ratio_min_zero_valid",
      "tests/test_pair_finder_validation.py::TestValidInputsAccepted::test_non_default_mass_grid",
      "tests/test_pair_finder_validation.py::TestValidInputsAccepted::test_non_default_sep_bins",
      "tests/test_pair_finder_validation.py::TestValidInputsAccepted::test_numpy_int_box_size",
      "tests/test_pair_finder_validation.py::TestValidInputsAccepted::test_numpy_int_scalar_config",
      "tests/test_pair_finder_validation.py::TestValidInputsAccepted::test_numpy_scalar_box_size",
      "tests/test_pair_finder_validation.py::TestValidInputsAccepted::test_numpy_scalar_max_sep",
      "tests/test_pair_finder_validation.py::TestValidInputsAccepted::test_sep_bins_as_float_ndarray",
      "tests/test_pair_finder_validation.py::TestValidInputsAccepted::test_sep_bins_as_float_tuple",
      "tests/test_pair_finder_validation.py::TestValidInputsAccepted::test_sep_bins_as_int_list",
      "tests/test_pair_finder_validation.py::TestValidInputsAccepted::test_sep_bins_as_int_ndarray",
      "tests/test_pair_finder_validation.py::TestValidInputsAccepted::test_sep_bins_numpy_scalar_elements",
      "tests/test_pair_finder_validation.py::TestValidInputsAccepted::test_zero_length_catalog",
      "tests/test_pair_finder_validation.py::TestValidationBeforeEarlyReturns::test_all_pairs_cut_by_mass_ratio_still_validates",
      "tests/test_pair_finder_validation.py::TestValidationBeforeEarlyReturns::test_empty_catalog_with_bad_config_rejected",
      "tests/test_pair_finder_validation.py::TestValidationBeforeEarlyReturns::test_nan_box_size_with_no_pairs",
      "tests/test_pair_finder_validation.py::TestValidationOrder::test_catalog_checked_before_config",
      "tests/test_pair_finder_validation.py::TestValidationOrder::test_catalog_dict_form_before_keys",
      "tests/test_pair_finder_validation.py::TestValidationOrder::test_catalog_keys_before_config_keys",
      "tests/test_statistical.py::TestBulkVelocityCancellation::test_delta_v_independent_of_bulk_sigma",
      "tests/test_statistical.py::TestCrossBinKineticTheory::test_cross_bin_sigma_eff",
      "tests/test_statistical.py::TestMassRatioDistribution::test_mass_ratio_is_uniform",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[0-2.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[0-3.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[0-4.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[0-5.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[1-2.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[1-3.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[1-4.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[1-5.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[2-2.0]",
      "tests/test
```
