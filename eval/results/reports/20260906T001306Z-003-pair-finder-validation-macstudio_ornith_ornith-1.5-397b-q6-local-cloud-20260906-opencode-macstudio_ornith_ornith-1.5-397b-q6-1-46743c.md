# Trial report: 20260906T001306Z-003-pair-finder-validation-macstudio_ornith_ornith-1.5-397b-q6-local-cloud-20260906-opencode-macstudio_ornith_ornith-1.5-397b-q6-1-46743c

- Task: `003-pair-finder-validation`
- Model: `macstudio/ornith/ornith-1.5-397b-q6` (harness: opencode)
- Model duration: 2651.0s | venv setup: 47.2s | timed out: False | committed: False
- Changed files: src/pair_finder.py, tests/test_pair_finder_validation.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 99.0 / 100

## Judged: readability 100% of weight, maintainability 100% of weight (judge claude-opus-5, status ok)

## Composite score: 99.1 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 100% |
| test_adequacy | automated | 25 | 97% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 100% |
| readability | judged | 8 | 100% |
| maintainability | judged | 7 | 100% |

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
    "raw_tail": "test_hA.py::test_A302_no_pairs_early_return_preserved PASSED       [ 86%]\ntests/test_hA.py::test_A303_mass_ratio_cut_early_return_preserved PASSED [ 86%]\ntests/test_hA.py::test_A304_empty_catalog_accepted PASSED                [ 87%]\ntests/test_hA.py::test_A305_mass_bin_sentinel_above_range PASSED         [ 87%]\ntests/test_hA.py::test_A306_mass_bin_sentinel_below_range PASSED         [ 87%]\ntests/test_hA.py::test_A307_sep_bin_sentinel_beyond_last_edge PASSED     [ 88%]\ntests/test_hA.py::test_A308_unknown_mass_bin_by_still_raises_value_error PASSED [ 88%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[primary] PASSED [ 88%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[secondary] PASSED [ 89%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[mean] PASSED [ 89%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[total] PASSED [ 89%]\ntests/test_hA.py::test_A310_signature_unchanged PASSED                   [ 90%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int16-ascending_dv] PASSED [ 90%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int16-descending_dv] PASSED [ 90%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint16-ascending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint16-descending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int32-ascending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int32-descending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint32-ascending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint32-descending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int64-ascending_dv] PASSED [ 93%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int64-descending_dv] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vx] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vy] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vz] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vx] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vy] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vz] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vx] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vy] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vz] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vx] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vy] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vz] PASSED [ 97%]\ntests/test_hA.py::test_A311_validation_precedes_no_pairs_return_nonfinite PASSED [ 97%]\ntests/test_hA.py::test_A312_validation_precedes_no_pairs_return_length PASSED [ 97%]\ntests/test_hA.py::test_A313_validation_precedes_mass_ratio_cut_return PASSED [ 98%]\ntests/test_hB.py::test_B00_pipeline_imports PASSED                       [ 98%]\ntests/test_hB.py::test_B01_driver_output_matches_the_analytic_expectation PASSED [ 98%]\ntests/test_hB.py::test_B02_nonfinite_position_on_disk_asserts PASSED     [ 99%]\ntests/test_hB.py::test_B03_position_outside_box_on_disk_asserts PASSED   [ 99%]\ntests/test_hB.py::test_B04_malformed_config_through_driver PASSED        [ 99%]\ntests/test_hB.py::test_B05_driver_honours_nondefault_config PASSED       [100%]\n\n============================= 315 passed in 0.98s ==============================\n",
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
      "tests/test_pair_finder_validation.py::TestAcceptedInputs::test_extra_and_malformed_extra_keys_ignored",
      "tests/test_pair_finder_validation.py::TestAcceptedInputs::test_mass_ratio_min_exactly_one_accepted",
      "tests/test_pair_finder_validation.py::TestAcceptedInputs::test_mass_ratio_min_exactly_zero_accepted",
      "tests/test_pair_finder_validation.py::TestAcceptedInputs::test_masses_outside_config_range_accepted",
      "tests/test_pair_finder_validation.py::TestAcceptedInputs::test_negative_finite_masses_accepted",
      "tests/test_pair_finder_validation.py::TestAcceptedInputs::test_non_default_mass_grid_accepted",
      "tests/test_pair_finder_validation.py::TestAcceptedInputs::test_non_default_sep_bins_accepted",
      "tests/test_pair_finder_validation.py::TestAcceptedInputs::test_numpy_integer_box_size_accepted",
      "tests/test_pair_finder_validation.py::TestAcceptedInputs::test_numpy_integer_scalars_accepted_for_config_keys",
      "tests/test_pair_finder_validation.py::TestAcceptedInputs::test_numpy_scalar_box_size_accepted",
      "tests/test_pair_finder_validation.py::TestAcceptedInputs::test_numpy_scalars_accepted_for_every_config_key[log_mass_max]",
      "tests/test_pair_finder_validation.py::TestAcceptedInputs::test_numpy_scalars_accepted_for_every_config_key[log_mass_min]",
      "tests/test_pair_finder_validation.py::TestAcceptedInputs::test_numpy_scalars_accepted_for_every_config_key[mass_bin_width]",
      "tests/test_pair_finder_validation.py::TestAcceptedInputs::test_numpy_scalars_accepted_for_every_config_key[mass_ratio_min]",
      "tests/test_pair_finder_validation.py::TestAcceptedInputs::test_numpy_scalars_accepted_for_every_config_key[max_sep]",
      "tests/test_pair_finder_validation.py::TestAcceptedInputs::test_position_exactly_zero_and_just_below_box_ok",
      "tests/test_pair_finder_validation.py::TestAcceptedInputs::test_sep_bins_forms_accepted[edges0]",
      "tests/test_pair_finder_validation.py::TestAcceptedInputs::test_sep_bins_forms_accepted[edges1]",
      "tests/test_pair_finder_validation.py::TestAcceptedInputs::test_sep_bins_forms_accepted[edges2]",
      "tests/test_pair_finder_validation.py::TestAcceptedInputs::test_sep_bins_forms_accepted[edges3]",
      "tests/test_pair_finder_validation.py::TestAcceptedInputs::test_sep_bins_forms_accepted[edges4]",
      "tests/test_pair_finder_validation.py::TestAcceptedInputs::test_zero_length_catalog",
      "tests/test_pair_finder_validation.py::TestBoxSizeAndPositionRange::test_box_size_bad_scalar_form[(1+2j)]",
      "tests/test_pair_finder_validation.py::TestBoxSizeAndPositionRange::test_box_size_bad_scalar_form[5_0]",
      "tests/test_pair_finder_validation.py::TestBoxSizeAndPositionRange::test_box_size_bad_scalar_form[5_1]",
      "tests/test_pair_finder_validation.py::TestBoxSizeAndPositionRange::test_box_size_bad_scalar_form[None]",
      "tests/test_pair_finder_validation.py::TestBoxSizeAndPositionRange::test_box_size_bad_scalar_form[True]",
      "tests/test_pair_finder_validation.py::TestBoxSizeAndPositionRange::test_box_size_bad_scalar_form[bad5]",
      "tests/test_pair_finder_validation.py::TestBoxSizeAndPositionRange::test_box_size_bad_scalar_form[bad6]",
      "tests/test_pair_finder_validation.py::TestBoxSizeAndPositionRange::test_box_size_missing",
      "tests/test_pair_finder_validation.py::TestBoxSizeAndPositionRange::test_box_size_non_positive[-1.0]",
      "tests/test_pair_finder_validation.py::TestBoxSizeAndPositionRange::test_box_size_non_positive[-5.0]",
      "tests/test_pair_finder_validation.py::TestBoxSizeAndPositionRange::test_box_size_non_positive[0.0]",
      "tests/test_pair_finder_validation.py::TestBoxSizeAndPositionRange::test_box_size_nonfinite[-inf]",
      "tests/test_pair_finder_validation.py::TestBoxSizeAndPositionRange::test_box_size_nonfinite[inf]",
      "tests/test_pair_finder_validation.py::TestBoxSizeAndPositionRange::test_box_size_nonfinite[nan]",
      "tests/test_pair_finder_validation.py::TestBoxSizeAndPositionRange::test_finiteness_reported_before_position_range",
      "tests/test_pair_finder_validation.py::TestBoxSizeAndPositionRange::test_negative_position_rejected",
      "tests/test_pair_finder_validation.py::TestBoxSizeAndPositionRange::test_position_above_box_size_rejected",
      "tests/test_pair_finder_validation.py::TestBoxSizeAndPositionRange::test_position_equal_box_size_rejected",
      "tests/test_pair_finder_validation.py::TestBoxSizeAndPositionRange::test_y_and_z_range_enforced",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_2d_rank_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_2d_rank_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_2d_rank_rejected[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_2d_rank_rejected[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_2d_rank_rejected[x]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_2d_rank_rejected[y]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_2d_rank_rejected[z]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_boolean_dtype_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_boolean_dtype_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_boolean_dtype_rejected[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_boolean_dtype_rejected[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_boolean_dtype_rejected[x]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_boolean_dtype_rejected[y]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_boolean_dtype_rejected[z]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_complex_dtype_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_complex_dtype_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_complex_dtype_rejected[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_complex_dtype_rejected[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_complex_dtype_rejected[x]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_complex_dtype_rejected[y]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_complex_dtype_rejected[z]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_inf_nonfinite_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_inf_nonfinite_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_inf_nonfinite_rejected[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_inf_nonfinite_rejected[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_inf_nonfinite_rejected[x]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_inf_nonfinite_rejected[y]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_inf_nonfinite_rejected[z]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_missing_field[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_missing_field[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_missing_field[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_missing_field[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_missing_field[x]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_missing_field[y]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_missing_field[z]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_nonfinite_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_nonfinite_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_nonfinite_rejected[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_nonfinite_rejected[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_nonfinite_rejected[x]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_nonfinite_rejected[y]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_nonfinite_rejected[z]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_object_dtype_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_object_dtype_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_object_dtype_rejected[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_object_dtype_rejected[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_object_dtype_rejected[x]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_object_dtype_rejected[y]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_object_dtype_rejected[z]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_python_list_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_python_list_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_python_list_rejected[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_python_list_rejected[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_python_list_rejected[x]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_python_list_rejected[y]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_python_list_rejected[z]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_python_tuple_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_python_tuple_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_python_tuple_rejected[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_python_tuple_rejected[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_python_tuple_rejected[x]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_python_tuple_rejected[y]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_python_tuple_rejected[z]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_unequal_length_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_unequal_length_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_unequal_length_rejected[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_unequal_length_rejected[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFields::test_unequal_length_rejected[x]",
      "tests/test_pair_finder_validation.py::Te
```
