# Trial report: 20260906T164721Z-003-pair-finder-validation-macstudio_kwaipilot_kat-coder-v2.5-dev-q8-sixth-session-20260906-kat-coder-v2.5-dev-q8-opencode-macstudio_kwaipilot_kat-coder-v2.5-dev-q8-1-c577e3

- Task: `003-pair-finder-validation`
- Model: `macstudio/kwaipilot/kat-coder-v2.5-dev-q8` (harness: opencode)
- Model duration: 2082.4s | venv setup: 29.2s | timed out: False | committed: False
- Changed files: src/pair_finder.py, tests/test_pair_finder_validation.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 90.6 / 100

## Judged: readability 75% of weight, maintainability 25% of weight (judge claude-opus-5, status ok)

## Composite score: 84.8 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 100% |
| test_adequacy | automated | 25 | 68% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 100% |
| readability | judged | 8 | 75% |
| maintainability | judged | 7 | 25% |

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
  "grader_git_rev": "61cb1854a0ffae112afee8be38f0bc5c9d4130d2",
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
    "raw_tail": "ass_bin_by_strategies_still_work[secondary] PASSED [ 89%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[mean] PASSED [ 89%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[total] PASSED [ 89%]\ntests/test_hA.py::test_A310_signature_unchanged PASSED                   [ 90%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int16-ascending_dv] PASSED [ 90%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int16-descending_dv] PASSED [ 90%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint16-ascending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint16-descending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int32-ascending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int32-descending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint32-ascending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint32-descending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int64-ascending_dv] PASSED [ 93%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int64-descending_dv] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vx] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vy] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vz] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vx] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vy] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vz] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vx] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vy] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vz] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vx] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vy] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vz] PASSED [ 97%]\ntests/test_hA.py::test_A311_validation_precedes_no_pairs_return_nonfinite PASSED [ 97%]\ntests/test_hA.py::test_A312_validation_precedes_no_pairs_return_length PASSED [ 97%]\ntests/test_hA.py::test_A313_validation_precedes_mass_ratio_cut_return PASSED [ 98%]\ntests/test_hB.py::test_B00_pipeline_imports PASSED                       [ 98%]\ntests/test_hB.py::test_B01_driver_output_matches_the_analytic_expectation PASSED [ 98%]\ntests/test_hB.py::test_B02_nonfinite_position_on_disk_asserts PASSED     [ 99%]\ntests/test_hB.py::test_B03_position_outside_box_on_disk_asserts PASSED   [ 99%]\ntests/test_hB.py::test_B04_malformed_config_through_driver PASSED        [ 99%]\ntests/test_hB.py::test_B05_driver_honours_nondefault_config PASSED       [100%]\n\n=================================== FAILURES ===================================\n_____________ test_A100_rejects[order_width_positive_before_range] _____________\ntests/test_hA.py:510: in test_A100_rejects\n    assert token in message, (\nE   AssertionError: message does not contain the required reason token 'positive': \"config['log_mass_max'] must be greater than config['log_mass_min'], got 7.0 and 8.0\"\nE   assert 'positive' in \"config['log_mass_max'] must be greater than config['log_mass_min'], got 7.0 and 8.0\"\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A100_rejects[order_width_positive_before_range]\n======================== 1 failed, 314 passed in 0.76s =========================\n",
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
      "tests/test_pair_finder_validation.py::TestBehaviourPreservation::test_all_four_mass_bin_by_strategies_work",
      "tests/test_pair_finder_validation.py::TestBehaviourPreservation::test_array_finiteness_before_position_range",
      "tests/test_pair_finder_validation.py::TestBehaviourPreservation::test_empty_result_dtypes_after_mass_ratio_cut",
      "tests/test_pair_finder_validation.py::TestBehaviourPreservation::test_empty_result_dtypes_after_no_pairs",
      "tests/test_pair_finder_validation.py::TestBehaviourPreservation::test_finite_catalog_with_nan_in_position_rejected_before_query",
      "tests/test_pair_finder_validation.py::TestBehaviourPreservation::test_invalid_mass_bin_by_still_raises_valueerror",
      "tests/test_pair_finder_validation.py::TestBehaviourPreservation::test_mass_bin_width_finiteness_before_bin_count",
      "tests/test_pair_finder_validation.py::TestBehaviourPreservation::test_minimum_image_across_periodic_boundary",
      "tests/test_pair_finder_validation.py::TestBehaviourPreservation::test_order_catalog_before_config",
      "tests/test_pair_finder_validation.py::TestBehaviourPreservation::test_out_of_range_mass_gives_negative_one_sentinel",
      "tests/test_pair_finder_validation.py::TestBehaviourPreservation::test_out_of_range_separation_gives_negative_one_sentinel",
      "tests/test_pair_finder_validation.py::TestBehaviourPreservation::test_primary_is_more_massive_tie_keeps_i",
      "tests/test_pair_finder_validation.py::TestBehaviourPreservation::test_sep_bins_finiteness_before_monotonicity",
      "tests/test_pair_finder_validation.py::TestBehaviourPreservation::test_two_argument_signature_unchanged",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_box_size_nan",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_box_size_negative",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_box_size_not_scalar_list",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_box_size_zero",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_log_mass_not_1d_2d",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_missing_box_size",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_missing_log_stellar_mass",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_missing_vx",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_missing_vy",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_missing_vz",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_missing_x",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_missing_y",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_missing_z",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_not_dict",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_position_at_box_size_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_position_negative_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_unequal_lengths",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_vx_bad_dtype_string",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_vy_not_1d_2d",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_vz_not_1d_2d",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_x_has_nan",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_x_not_ndarray_list",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_x_not_ndarray_tuple",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_y_bad_dtype_bool",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_y_has_inf",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_z_bad_dtype_complex",
      "tests/test_pair_finder_validation.py::TestConfigForm::test_missing_log_mass_max",
      "tests/test_pair_finder_validation.py::TestConfigForm::test_missing_log_mass_min",
      "tests/test_pair_finder_validation.py::TestConfigForm::test_missing_mass_bin_by",
      "tests/test_pair_finder_validation.py::TestConfigForm::test_missing_mass_bin_width",
      "tests/test_pair_finder_validation.py::TestConfigForm::test_missing_mass_ratio_min",
      "tests/test_pair_finder_validation.py::TestConfigForm::test_missing_max_sep",
      "tests/test_pair_finder_validation.py::TestConfigForm::test_missing_sep_bins",
      "tests/test_pair_finder_validation.py::TestConfigForm::test_not_dict",
      "tests/test_pair_finder_validation.py::TestScalarConfigErrors::test_log_mass_max_equal_to_min",
      "tests/test_pair_finder_validation.py::TestScalarConfigErrors::test_log_mass_max_not_finite_inf",
      "tests/test_pair_finder_validation.py::TestScalarConfigErrors::test_log_mass_max_not_greater_than_min",
      "tests/test_pair_finder_validation.py::TestScalarConfigErrors::test_log_mass_min_not_scalar_string",
      "tests/test_pair_finder_validation.py::TestScalarConfigErrors::test_mass_bin_width_negative",
      "tests/test_pair_finder_validation.py::TestScalarConfigErrors::test_mass_bin_width_not_scalar_bytes",
      "tests/test_pair_finder_validation.py::TestScalarConfigErrors::test_mass_bin_width_too_large_no_bins",
      "tests/test_pair_finder_validation.py::TestScalarConfigErrors::test_mass_bin_width_zero",
      "tests/test_pair_finder_validation.py::TestScalarConfigErrors::test_mass_ratio_min_not_scalar_bool",
      "tests/test_pair_finder_validation.py::TestScalarConfigErrors::test_mass_ratio_min_out_of_range_high",
      "tests/test_pair_finder_validation.py::TestScalarConfigErrors::test_mass_ratio_min_out_of_range_low",
      "tests/test_pair_finder_validation.py::TestScalarConfigErrors::test_max_sep_nan",
      "tests/test_pair_finder_validation.py::TestScalarConfigErrors::test_max_sep_negative",
      "tests/test_pair_finder_validation.py::TestScalarConfigErrors::test_max_sep_not_scalar_list",
      "tests/test_pair_finder_validation.py::TestSepBinsErrors::test_duplicate_edge",
      "tests/test_pair_finder_validation.py::TestSepBinsErrors::test_nan_in_edges",
      "tests/test_pair_finder_validation.py::TestSepBinsErrors::test_ndarray_bad_dtype_bool",
      "tests/test_pair_finder_validation.py::TestSepBinsErrors::test_ndarray_not_1d",
      "tests/test_pair_finder_validation.py::TestSepBinsErrors::test_non_scalar_element_in_list",
      "tests/test_pair_finder_validation.py::TestSepBinsErrors::test_not_list_tuple_ndarray",
      "tests/test_pair_finder_validation.py::TestSepBinsErrors::test_too_few_edges",
      "tests/test_pair_finder_validation.py::TestSepBinsErrors::test_unsorted_edges",
      "tests/test_pair_finder_validation.py::TestValidInputs::test_box_size_numpy_scalar",
      "tests/test_pair_finder_validation.py::TestValidInputs::test_config_keys_as_numpy_scalars",
      "tests/test_pair_finder_validation.py::TestValidInputs::test_extra_keys_ignored",
      "tests/test_pair_finder_validation.py::TestValidInputs::test_integer_dtype_arrays",
      "tests/test_pair_finder_validation.py::TestValidInputs::test_log_mass_outside_config_range_gives_sentinel",
      "tests/test_pair_finder_validation.py::TestValidInputs::test_mass_ratio_min_exactly_one",
      "tests/test_pair_finder_validation.py::TestValidInputs::test_mass_ratio_min_exactly_zero",
      "tests/test_pair_finder_validation.py::TestValidInputs::test_negative_finite_mass_allowed",
      "tests/test_pair_finder_validation.py::TestValidInputs::test_non_default_mass_grid",
      "tests/test_pair_finder_validation.py::TestValidInputs::test_non_default_sep_bins",
      "tests/test_pair_finder_validation.py::TestValidInputs::test_position_exactly_zero_valid",
      "tests/test_pair_finder_validation.py::TestValidInputs::test_position_just_below_box_size_valid",
      "tests/test_pair_finder_validation.py::TestValidInputs::test_sep_bins_as_float_ndarray",
      "tests/test_pair_finder_validation.py::TestValidInputs::test_sep_bins_as_float_tuple",
      "tests/test_pair_finder_validation.py::TestValidInputs::test_sep_bins_as_int_list",
      "tests/test_pair_finder_validation.py::TestValidInputs::test_sep_bins_as_integer_ndarray",
      "tests/test_pair_finder_validation.py::TestValidInputs::test_sep_bins_with_numpy_scalar_elements",
      "tests/test_pair_finder_validation.py::TestValidInputs::test_unsigned_integer_dtype_arrays",
      "tests/test_pair_finder_validation.py::TestValidInputs::test_zero_length_catalog",
      "tests/test_pair_finder_validation.py::TestValidationBeforeEarlyReturns::test_malformed_catalog_with_no_pairs_still_rejected",
      "tests/test_pair_finder_validation.py::TestValidationBeforeEarlyReturns::test_malformed_config_with_no_pairs_still_rejected",
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
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[2-3.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[2-4.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[2-5.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[3-2.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[3-3.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[3-4.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[3-5.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-2.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-3.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-4.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-5.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-2.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-3.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-4.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-5.0]",
      "tests/test_statistical.py:
```
