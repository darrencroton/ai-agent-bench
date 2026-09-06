# Trial report: 20260906T052721Z-003-pair-finder-validation-gpt-5.6-terra-medium-frontier-20260906-v2-codex-gpt-5.6-terra-3-086536

- Task: `003-pair-finder-validation`
- Model: `gpt-5.6-terra` (harness: codex)
- Model duration: 384.9s | venv setup: 25.7s | timed out: False | committed: False
- Changed files: src/pair_finder.py, tests/test_pair_finder_validation.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 98.8 / 100

## Judged: readability 75% of weight, maintainability 50% of weight (judge claude-opus-5, status ok)

## Composite score: 93.5 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 100% |
| test_adequacy | automated | 25 | 96% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 100% |
| readability | judged | 8 | 75% |
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
    "passed": 315,
    "failed": [],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "test_hA.py::test_A302_no_pairs_early_return_preserved PASSED       [ 86%]\ntests/test_hA.py::test_A303_mass_ratio_cut_early_return_preserved PASSED [ 86%]\ntests/test_hA.py::test_A304_empty_catalog_accepted PASSED                [ 87%]\ntests/test_hA.py::test_A305_mass_bin_sentinel_above_range PASSED         [ 87%]\ntests/test_hA.py::test_A306_mass_bin_sentinel_below_range PASSED         [ 87%]\ntests/test_hA.py::test_A307_sep_bin_sentinel_beyond_last_edge PASSED     [ 88%]\ntests/test_hA.py::test_A308_unknown_mass_bin_by_still_raises_value_error PASSED [ 88%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[primary] PASSED [ 88%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[secondary] PASSED [ 89%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[mean] PASSED [ 89%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[total] PASSED [ 89%]\ntests/test_hA.py::test_A310_signature_unchanged PASSED                   [ 90%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int16-ascending_dv] PASSED [ 90%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int16-descending_dv] PASSED [ 90%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint16-ascending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint16-descending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int32-ascending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int32-descending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint32-ascending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint32-descending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int64-ascending_dv] PASSED [ 93%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int64-descending_dv] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vx] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vy] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vz] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vx] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vy] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vz] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vx] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vy] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vz] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vx] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vy] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vz] PASSED [ 97%]\ntests/test_hA.py::test_A311_validation_precedes_no_pairs_return_nonfinite PASSED [ 97%]\ntests/test_hA.py::test_A312_validation_precedes_no_pairs_return_length PASSED [ 97%]\ntests/test_hA.py::test_A313_validation_precedes_mass_ratio_cut_return PASSED [ 98%]\ntests/test_hB.py::test_B00_pipeline_imports PASSED                       [ 98%]\ntests/test_hB.py::test_B01_driver_output_matches_the_analytic_expectation PASSED [ 98%]\ntests/test_hB.py::test_B02_nonfinite_position_on_disk_asserts PASSED     [ 99%]\ntests/test_hB.py::test_B03_position_outside_box_on_disk_asserts PASSED   [ 99%]\ntests/test_hB.py::test_B04_malformed_config_through_driver PASSED        [ 99%]\ntests/test_hB.py::test_B05_driver_honours_nondefault_config PASSED       [100%]\n\n============================= 315 passed in 0.67s ==============================\n",
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
      "tests/test_pair_finder_validation.py::test_all_valid_sep_bin_forms_and_coordinate_boundaries_are_accepted[sep_bins0]",
      "tests/test_pair_finder_validation.py::test_all_valid_sep_bin_forms_and_coordinate_boundaries_are_accepted[sep_bins1]",
      "tests/test_pair_finder_validation.py::test_all_valid_sep_bin_forms_and_coordinate_boundaries_are_accepted[sep_bins2]",
      "tests/test_pair_finder_validation.py::test_all_valid_sep_bin_forms_and_coordinate_boundaries_are_accepted[sep_bins3]",
      "tests/test_pair_finder_validation.py::test_box_size_must_be_finite[inf]",
      "tests/test_pair_finder_validation.py::test_box_size_must_be_finite[nan]",
      "tests/test_pair_finder_validation.py::test_box_size_must_be_positive[-1.0]",
      "tests/test_pair_finder_validation.py::test_box_size_must_be_positive[0.0]",
      "tests/test_pair_finder_validation.py::test_box_size_requires_a_real_numeric_scalar[(1+0j)]",
      "tests/test_pair_finder_validation.py::test_box_size_requires_a_real_numeric_scalar[1_0]",
      "tests/test_pair_finder_validation.py::test_box_size_requires_a_real_numeric_scalar[1_1]",
      "tests/test_pair_finder_validation.py::test_box_size_requires_a_real_numeric_scalar[True]",
      "tests/test_pair_finder_validation.py::test_box_size_requires_a_real_numeric_scalar[bad_value4]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[S4-log_stellar_mass]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[S4-vx]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[S4-vy]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[S4-vz]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[S4-x]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[S4-y]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[S4-z]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[U4-log_stellar_mass]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[U4-vx]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[U4-vy]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[U4-vz]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[U4-x]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[U4-y]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[U4-z]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[bool-log_stellar_mass]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[bool-vx]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[bool-vy]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[bool-vz]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[bool-x]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[bool-y]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[bool-z]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[complex-log_stellar_mass]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[complex-vx]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[complex-vy]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[complex-vz]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[complex-x]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[complex-y]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[complex-z]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[object-log_stellar_mass]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[object-vx]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[object-vy]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[object-vz]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[object-x]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[object-y]",
      "tests/test_pair_finder_validation.py::test_catalog_array_dtype_is_checked_before_coercion[object-z]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_be_finite_before_position_checks[inf-log_stellar_mass]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_be_finite_before_position_checks[inf-vx]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_be_finite_before_position_checks[inf-vy]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_be_finite_before_position_checks[inf-vz]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_be_finite_before_position_checks[inf-x]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_be_finite_before_position_checks[inf-y]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_be_finite_before_position_checks[inf-z]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_be_finite_before_position_checks[nan-log_stellar_mass]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_be_finite_before_position_checks[nan-vx]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_be_finite_before_position_checks[nan-vy]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_be_finite_before_position_checks[nan-vz]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_be_finite_before_position_checks[nan-x]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_be_finite_before_position_checks[nan-y]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_be_finite_before_position_checks[nan-z]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_be_ndarrays[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_be_ndarrays[vx]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_be_ndarrays[vy]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_be_ndarrays[vz]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_be_ndarrays[x]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_be_ndarrays[y]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_be_ndarrays[z]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_be_one_dimensional[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_be_one_dimensional[vx]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_be_one_dimensional[vy]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_be_one_dimensional[vz]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_be_one_dimensional[x]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_be_one_dimensional[y]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_be_one_dimensional[z]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_have_equal_lengths[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_have_equal_lengths[vx]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_have_equal_lengths[vy]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_have_equal_lengths[vz]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_have_equal_lengths[y]",
      "tests/test_pair_finder_validation.py::test_catalog_arrays_must_have_equal_lengths[z]",
      "tests/test_pair_finder_validation.py::test_catalog_must_be_dict[None]",
      "tests/test_pair_finder_validation.py::test_catalog_must_be_dict[bad_catalog1]",
      "tests/test_pair_finder_validation.py::test_catalog_must_be_dict[catalog]",
      "tests/test_pair_finder_validation.py::test_catalog_required_fields_must_be_present[box_size]",
      "tests/test_pair_finder_validation.py::test_catalog_required_fields_must_be_present[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::test_catalog_required_fields_must_be_present[vx]",
      "tests/test_pair_finder_validation.py::test_catalog_required_fields_must_be_present[vy]",
      "tests/test_pair_finder_validation.py::test_catalog_required_fields_must_be_present[vz]",
      "tests/test_pair_finder_validation.py::test_catalog_required_fields_must_be_present[x]",
      "tests/test_pair_finder_validation.py::test_catalog_required_fields_must_be_present[y]",
      "tests/test_pair_finder_validation.py::test_catalog_required_fields_must_be_present[z]",
      "tests/test_pair_finder_validation.py::test_config_must_be_dict[None]",
      "tests/test_pair_finder_validation.py::test_config_must_be_dict[bad_config1]",
      "tests/test_pair_finder_validation.py::test_config_must_be_dict[config]",
      "tests/test_pair_finder_validation.py::test_config_required_keys_must_be_present[log_mass_max]",
      "tests/test_pair_finder_validation.py::test_config_required_keys_must_be_present[log_mass_min]",
      "tests/test_pair_finder_validation.py::test_config_required_keys_must_be_present[mass_bin_by]",
      "tests/test_pair_finder_validation.py::test_config_required_keys_must_be_present[mass_bin_width]",
      "tests/test_pair_finder_validation.py::test_config_required_keys_must_be_present[mass_ratio_min]",
      "tests/test_pair_finder_validation.py::test_config_required_keys_must_be_present[max_sep]",
      "tests/test_pair_finder_validation.py::test_config_required_keys_must_be_present[sep_bins]",
      "tests/test_pair_finder_validation.py::test_config_scalars_are_checked_before_coercion[(1+0j)-log_mass_max]",
      "tests/test_pair_finder_validation.py::test_config_scalars_are_checked_before_coercion[(1+0j)-log_mass_min]",
      "tests/test_pair_finder_validation.py::test_config_scalars_are_checked_before_coercion[(1+0j)-mass_bin_width]",
      "tests/test_pair_finder_validation.py::test_config_scalars_are_checked_before_coercion[(1+0j)-mass_ratio_min]",
      "tests/test_pair_finder_validation.py::test_config_scalars_are_checked_before_coercion[(1+0j)-max_sep]",
      "tests/test_pair_finder_validation.py::test_config_scalars_are_checked_before_coercion[1_0-log_mass_max]",
      "tests/test_pair_finder_validation.py::test_config_scalars_are_checked_before_coercion[1_0-log_mass_min]",
      "tests/test_pair_finder_validation.py::test_config_scalars_are_checked_before_coe
```
