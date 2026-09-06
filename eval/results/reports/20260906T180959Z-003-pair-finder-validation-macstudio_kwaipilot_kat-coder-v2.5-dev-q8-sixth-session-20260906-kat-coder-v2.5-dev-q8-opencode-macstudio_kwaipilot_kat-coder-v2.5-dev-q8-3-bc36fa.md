# Trial report: 20260906T180959Z-003-pair-finder-validation-macstudio_kwaipilot_kat-coder-v2.5-dev-q8-sixth-session-20260906-kat-coder-v2.5-dev-q8-opencode-macstudio_kwaipilot_kat-coder-v2.5-dev-q8-3-bc36fa

- Task: `003-pair-finder-validation`
- Model: `macstudio/kwaipilot/kat-coder-v2.5-dev-q8` (harness: opencode)
- Model duration: 3758.4s | venv setup: 26.4s | timed out: False | committed: False
- Changed files: src/pair_finder.py, tests/test_pair_finder_validation.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 91.3 / 100

## Judged: readability 50% of weight, maintainability 50% of weight (judge claude-opus-5, status ok)

## Composite score: 85.1 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 100% |
| test_adequacy | automated | 25 | 71% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 100% |
| readability | judged | 8 | 50% |
| maintainability | judged | 7 | 50% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| rejection_matrix | 201 | 205 | 0.98 |
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
  "grader_git_rev": "49c3dbbb58fda4574328ca04658c2e6c7a159d01",
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
    "passed": 311,
    "failed": [
      "tests/test_hA.py::test_A100_rejects[mass_bin_width_value_10.0]",
      "tests/test_hA.py::test_A100_rejects[sep_bins_complex_ndarray]",
      "tests/test_hA.py::test_A100_rejects[sep_bins_str_ndarray]",
      "tests/test_hA.py::test_A100_rejects[sep_bins_bool_ndarray]"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "n[int16-vy] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vz] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vx] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vy] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vz] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vx] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vy] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vz] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vx] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vy] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vz] PASSED [ 97%]\ntests/test_hA.py::test_A311_validation_precedes_no_pairs_return_nonfinite PASSED [ 97%]\ntests/test_hA.py::test_A312_validation_precedes_no_pairs_return_length PASSED [ 97%]\ntests/test_hA.py::test_A313_validation_precedes_mass_ratio_cut_return PASSED [ 98%]\ntests/test_hB.py::test_B00_pipeline_imports PASSED                       [ 98%]\ntests/test_hB.py::test_B01_driver_output_matches_the_analytic_expectation PASSED [ 98%]\ntests/test_hB.py::test_B02_nonfinite_position_on_disk_asserts PASSED     [ 99%]\ntests/test_hB.py::test_B03_position_outside_box_on_disk_asserts PASSED   [ 99%]\ntests/test_hB.py::test_B04_malformed_config_through_driver PASSED        [ 99%]\ntests/test_hB.py::test_B05_driver_honours_nondefault_config PASSED       [100%]\n\n=================================== FAILURES ===================================\n_________________ test_A100_rejects[mass_bin_width_value_10.0] _________________\ntests/test_hA.py:513: in test_A100_rejects\n    assert any(re.search(rf\"\\b{re.escape(n)}\\b\", message) for n in names), (\nE   AssertionError: message names none of ['mass_bin_width']: 'the mass grid yields no bin; need at least one mass bin, but round((11.0 - 8.0) / 10.0) = 0'\nE   assert False\nE    +  where False = any(<generator object test_A100_rejects.<locals>.<genexpr> at 0x10dc1c240>)\n_________________ test_A100_rejects[sep_bins_complex_ndarray] __________________\ntests/test_hA.py:510: in test_A100_rejects\n    assert token in message, (\nE   AssertionError: message does not contain the required reason token 'dtype': \"config['sep_bins'] must be a list, tuple or numpy.ndarray, got ndarray\"\nE   assert 'dtype' in \"config['sep_bins'] must be a list, tuple or numpy.ndarray, got ndarray\"\n___________________ test_A100_rejects[sep_bins_str_ndarray] ____________________\ntests/test_hA.py:510: in test_A100_rejects\n    assert token in message, (\nE   AssertionError: message does not contain the required reason token 'dtype': \"config['sep_bins'] must be a list, tuple or numpy.ndarray, got ndarray\"\nE   assert 'dtype' in \"config['sep_bins'] must be a list, tuple or numpy.ndarray, got ndarray\"\n___________________ test_A100_rejects[sep_bins_bool_ndarray] ___________________\ntests/test_hA.py:510: in test_A100_rejects\n    assert token in message, (\nE   AssertionError: message does not contain the required reason token 'dtype': \"config['sep_bins'] must be a list, tuple or numpy.ndarray, got ndarray\"\nE   assert 'dtype' in \"config['sep_bins'] must be a list, tuple or numpy.ndarray, got ndarray\"\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A100_rejects[mass_bin_width_value_10.0] - Asser...\nFAILED tests/test_hA.py::test_A100_rejects[sep_bins_complex_ndarray] - Assert...\nFAILED tests/test_hA.py::test_A100_rejects[sep_bins_str_ndarray] - AssertionE...\nFAILED tests/test_hA.py::test_A100_rejects[sep_bins_bool_ndarray] - Assertion...\n======================== 4 failed, 311 passed in 0.68s =========================\n",
    "stderr_tail": "",
    "obligations": [
      {
        "id": "rejection_matrix",
        "passed": 201,
        "collected": 205,
        "fraction": 0.9804878048780488,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_A100_rejects[mass_bin_width_value_10.0]",
          "tests/test_hA.py::test_A100_rejects[sep_bins_bool_ndarray]",
          "tests/test_hA.py::test_A100_rejects[sep_bins_complex_ndarray]",
          "tests/test_hA.py::test_A100_rejects[sep_bins_str_ndarray]"
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
      "tests/test_pair_finder_validation.py::TestArrayMustBeNdarray::test_list_instead_of_ndarray[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestArrayMustBeNdarray::test_list_instead_of_ndarray[vx]",
      "tests/test_pair_finder_validation.py::TestArrayMustBeNdarray::test_list_instead_of_ndarray[vy]",
      "tests/test_pair_finder_validation.py::TestArrayMustBeNdarray::test_list_instead_of_ndarray[vz]",
      "tests/test_pair_finder_validation.py::TestArrayMustBeNdarray::test_list_instead_of_ndarray[x]",
      "tests/test_pair_finder_validation.py::TestArrayMustBeNdarray::test_list_instead_of_ndarray[y]",
      "tests/test_pair_finder_validation.py::TestArrayMustBeNdarray::test_list_instead_of_ndarray[z]",
      "tests/test_pair_finder_validation.py::TestArrayMustBeNdarray::test_tuple_instead_of_ndarray",
      "tests/test_pair_finder_validation.py::TestBoxSizeRejections::test_box_size_bool",
      "tests/test_pair_finder_validation.py::TestBoxSizeRejections::test_box_size_inf",
      "tests/test_pair_finder_validation.py::TestBoxSizeRejections::test_box_size_list",
      "tests/test_pair_finder_validation.py::TestBoxSizeRejections::test_box_size_missing",
      "tests/test_pair_finder_validation.py::TestBoxSizeRejections::test_box_size_nan",
      "tests/test_pair_finder_validation.py::TestBoxSizeRejections::test_box_size_ndarray",
      "tests/test_pair_finder_validation.py::TestBoxSizeRejections::test_box_size_negative",
      "tests/test_pair_finder_validation.py::TestBoxSizeRejections::test_box_size_string",
      "tests/test_pair_finder_validation.py::TestBoxSizeRejections::test_box_size_zero",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_list_instead_of_dict",
      "tests/test_pair_finder_validation.py::TestCatalogForm::test_not_a_dict",
      "tests/test_pair_finder_validation.py::TestConfigForm::test_list_instead_of_dict",
      "tests/test_pair_finder_validation.py::TestConfigForm::test_not_a_dict",
      "tests/test_pair_finder_validation.py::TestLogMassRangeRejections::test_log_mass_max_equal_to_min",
      "tests/test_pair_finder_validation.py::TestLogMassRangeRejections::test_log_mass_max_less_than_min",
      "tests/test_pair_finder_validation.py::TestLogMassRangeRejections::test_log_mass_max_not_finite",
      "tests/test_pair_finder_validation.py::TestLogMassRangeRejections::test_log_mass_min_not_finite",
      "tests/test_pair_finder_validation.py::TestMassBinWidthRejections::test_negative",
      "tests/test_pair_finder_validation.py::TestMassBinWidthRejections::test_no_bins_yields_error",
      "tests/test_pair_finder_validation.py::TestMassBinWidthRejections::test_not_finite",
      "tests/test_pair_finder_validation.py::TestMassBinWidthRejections::test_zero",
      "tests/test_pair_finder_validation.py::TestMassRatioMinRejections::test_above_one",
      "tests/test_pair_finder_validation.py::TestMassRatioMinRejections::test_below_zero",
      "tests/test_pair_finder_validation.py::TestMassRatioMinRejections::test_not_finite",
      "tests/test_pair_finder_validation.py::TestMaxSepRejections::test_infinite",
      "tests/test_pair_finder_validation.py::TestMaxSepRejections::test_negative",
      "tests/test_pair_finder_validation.py::TestMaxSepRejections::test_not_finite",
      "tests/test_pair_finder_validation.py::TestMaxSepRejections::test_zero",
      "tests/test_pair_finder_validation.py::TestMissingArrayKeys::test_missing_array_key[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestMissingArrayKeys::test_missing_array_key[vx]",
      "tests/test_pair_finder_validation.py::TestMissingArrayKeys::test_missing_array_key[vy]",
      "tests/test_pair_finder_validation.py::TestMissingArrayKeys::test_missing_array_key[vz]",
      "tests/test_pair_finder_validation.py::TestMissingArrayKeys::test_missing_array_key[x]",
      "tests/test_pair_finder_validation.py::TestMissingArrayKeys::test_missing_array_key[y]",
      "tests/test_pair_finder_validation.py::TestMissingArrayKeys::test_missing_array_key[z]",
      "tests/test_pair_finder_validation.py::TestMissingArrayKeys::test_missing_box_size",
      "tests/test_pair_finder_validation.py::TestMissingConfigKeys::test_missing_config_key[log_mass_max]",
      "tests/test_pair_finder_validation.py::TestMissingConfigKeys::test_missing_config_key[log_mass_min]",
      "tests/test_pair_finder_validation.py::TestMissingConfigKeys::test_missing_config_key[mass_bin_by]",
      "tests/test_pair_finder_validation.py::TestMissingConfigKeys::test_missing_config_key[mass_bin_width]",
      "tests/test_pair_finder_validation.py::TestMissingConfigKeys::test_missing_config_key[mass_ratio_min]",
      "tests/test_pair_finder_validation.py::TestMissingConfigKeys::test_missing_config_key[max_sep]",
      "tests/test_pair_finder_validation.py::TestMissingConfigKeys::test_missing_config_key[sep_bins]",
      "tests/test_pair_finder_validation.py::TestNonFiniteArrays::test_inf_in_array[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestNonFiniteArrays::test_inf_in_array[vx]",
      "tests/test_pair_finder_validation.py::TestNonFiniteArrays::test_inf_in_array[vy]",
      "tests/test_pair_finder_validation.py::TestNonFiniteArrays::test_inf_in_array[vz]",
      "tests/test_pair_finder_validation.py::TestNonFiniteArrays::test_inf_in_array[x]",
      "tests/test_pair_finder_validation.py::TestNonFiniteArrays::test_inf_in_array[y]",
      "tests/test_pair_finder_validation.py::TestNonFiniteArrays::test_inf_in_array[z]",
      "tests/test_pair_finder_validation.py::TestNonFiniteArrays::test_nan_in_array[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestNonFiniteArrays::test_nan_in_array[vx]",
      "tests/test_pair_finder_validation.py::TestNonFiniteArrays::test_nan_in_array[vy]",
      "tests/test_pair_finder_validation.py::TestNonFiniteArrays::test_nan_in_array[vz]",
      "tests/test_pair_finder_validation.py::TestNonFiniteArrays::test_nan_in_array[x]",
      "tests/test_pair_finder_validation.py::TestNonFiniteArrays::test_nan_in_array[y]",
      "tests/test_pair_finder_validation.py::TestNonFiniteArrays::test_nan_in_array[z]",
      "tests/test_pair_finder_validation.py::TestNonFiniteArrays::test_neg_inf_in_array[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestNonFiniteArrays::test_neg_inf_in_array[vx]",
      "tests/test_pair_finder_validation.py::TestNonFiniteArrays::test_neg_inf_in_array[vy]",
      "tests/test_pair_finder_validation.py::TestNonFiniteArrays::test_neg_inf_in_array[vz]",
      "tests/test_pair_finder_validation.py::TestNonFiniteArrays::test_neg_inf_in_array[x]",
      "tests/test_pair_finder_validation.py::TestNonFiniteArrays::test_neg_inf_in_array[y]",
      "tests/test_pair_finder_validation.py::TestNonFiniteArrays::test_neg_inf_in_array[z]",
      "tests/test_pair_finder_validation.py::TestNot1D::test_2d_array[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestNot1D::test_2d_array[vx]",
      "tests/test_pair_finder_validation.py::TestNot1D::test_2d_array[vy]",
      "tests/test_pair_finder_validation.py::TestNot1D::test_2d_array[vz]",
      "tests/test_pair_finder_validation.py::TestNot1D::test_2d_array[x]",
      "tests/test_pair_finder_validation.py::TestNot1D::test_2d_array[y]",
      "tests/test_pair_finder_validation.py::TestNot1D::test_2d_array[z]",
      "tests/test_pair_finder_validation.py::TestOrderOfChecks::test_catalog_validated_before_config",
      "tests/test_pair_finder_validation.py::TestOrderOfChecks::test_dict_form_checked_before_keys",
      "tests/test_pair_finder_validation.py::TestOrderOfChecks::test_mass_bin_width_inf_reported_as_finite_not_bin_count",
      "tests/test_pair_finder_validation.py::TestOrderOfChecks::test_nan_in_x_reported_as_finite_not_box",
      "tests/test_pair_finder_validation.py::TestOrderOfChecks::test_sep_bins_nan_reported_as_finite_not_monotonicity",
      "tests/test_pair_finder_validation.py::TestPositionRange::test_negative_position",
      "tests/test_pair_finder_validation.py::TestPositionRange::test_position_equal_to_box_size",
      "tests/test_pair_finder_validation.py::TestPositionRange::test_y_above_box_size",
      "tests/test_pair_finder_validation.py::TestPositionRange::test_z_above_box_size",
      "tests/test_pair_finder_validation.py::TestPreservedBehaviour::test_empty_result_after_mass_ratio_cut",
      "tests/test_pair_finder_validation.py::TestPreservedBehaviour::test_empty_result_after_no_pairs_found",
      "tests/test_pair_finder_validation.py::TestPreservedBehaviour::test_invalid_mass_bin_by_still_raises_valueerror",
      "tests/test_pair_finder_validation.py::TestPreservedBehaviour::test_mass_ratio_always_leq_one",
      "tests/test_pair_finder_validation.py::TestPreservedBehaviour::test_minimum_image_separation_across_boundary",
      "tests/test_pair_finder_validation.py::TestPreservedBehaviour::test_negative_sentinel_for_out_of_range_mass",
      "tests/test_pair_finder_validation.py::TestPreservedBehaviour::test_negative_sentinel_for_out_of_range_sep",
      "tests/test_pair_finder_validation.py::TestPreservedBehaviour::test_primary_is_always_more_massive",
      "tests/test_pair_finder_validation.py::TestPreservedBehaviour::test_two_argument_signature",
      "tests/test_pair_finder_validation.py::TestPreservedBehaviour::test_validation_runs_before_mass_ratio_early_return",
      "tests/test_pair_finder_validation.py::TestPreservedBehaviour::test_validation_runs_before_no_pairs_early_return",
      "tests/test_pair_finder_validation.py::TestRejectedDtypes::test_bytes_dtype",
      "tests/test_pair_finder_validation.py::TestRejectedDtypes::test_rejected_dtype[bool]",
      "tests/test_pair_finder_validation.py::TestRejectedDtypes::test_rejected_dtype[complex]",
      "tests/test_pair_finder_validation.py::TestRejectedDtypes::test_rejected_dtype[object]",
      "tests/test_pair_finder_validation.py::TestRejectedDtypes::test_string_dtype",
      "tests/test_pair_finder_validation.py::TestScalarFormRejections::test_scalar_is_bool",
      "tests/test_pair_finder_validation.py::TestScalarFormRejections::test_scalar_is_complex",
      "tests/test_pair_finder_validation.py::TestScalarFormRejections::test_scalar_is_list[log_mass_max]",
      "tests/test_pair_finder_validation.py::TestScalarFormRejections::test_scalar_is_list[log_mass_min]",
      "tests/test_pair_finder_validation.py::TestScalarFormRejections::test_scalar_is_list[mass_bin_width]",
      "tests/test_pair_finder_validation.py::TestScalarFormRejections::test_scalar_is_list[mass_ratio_min]",
      "tests/test_pair_finder_validation.py::TestScalarFormRejections::test_scalar_is_list[max_sep]",
      "tests/test_pair_finder_validation.py::TestScalarFormRejections::test_scalar_is_ndarray",
      "tests/test_pair_finder_validation.py::TestScalarFormRejections::test_scalar_is_string",
    
```
