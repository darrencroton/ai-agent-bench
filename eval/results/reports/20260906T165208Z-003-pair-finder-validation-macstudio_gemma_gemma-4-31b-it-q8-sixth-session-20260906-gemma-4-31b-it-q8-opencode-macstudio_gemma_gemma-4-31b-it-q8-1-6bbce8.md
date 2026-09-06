# Trial report: 20260906T165208Z-003-pair-finder-validation-macstudio_gemma_gemma-4-31b-it-q8-sixth-session-20260906-gemma-4-31b-it-q8-opencode-macstudio_gemma_gemma-4-31b-it-q8-1-6bbce8

- Task: `003-pair-finder-validation`
- Model: `macstudio/gemma/gemma-4-31b-it-q8` (harness: opencode)
- Model duration: 1857.3s | venv setup: 26.8s | timed out: False | committed: False
- Changed files: src/pair_finder.py, tests/test_pair_finder_validation.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 83.3 / 100

## Judged: readability 50% of weight, maintainability 50% of weight (judge claude-opus-5, status ok)

## Composite score: 78.3 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 100% |
| test_adequacy | automated | 25 | 43% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 100% |
| readability | judged | 8 | 50% |
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
      "tests/test_hA.py::test_A100_rejects[mass_bin_width_value_10.0]"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "n_by_strategies_still_work[secondary] PASSED [ 89%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[mean] PASSED [ 89%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[total] PASSED [ 89%]\ntests/test_hA.py::test_A310_signature_unchanged PASSED                   [ 90%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int16-ascending_dv] PASSED [ 90%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int16-descending_dv] PASSED [ 90%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint16-ascending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint16-descending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int32-ascending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int32-descending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint32-ascending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint32-descending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int64-ascending_dv] PASSED [ 93%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int64-descending_dv] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vx] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vy] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vz] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vx] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vy] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vz] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vx] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vy] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vz] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vx] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vy] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vz] PASSED [ 97%]\ntests/test_hA.py::test_A311_validation_precedes_no_pairs_return_nonfinite PASSED [ 97%]\ntests/test_hA.py::test_A312_validation_precedes_no_pairs_return_length PASSED [ 97%]\ntests/test_hA.py::test_A313_validation_precedes_mass_ratio_cut_return PASSED [ 98%]\ntests/test_hB.py::test_B00_pipeline_imports PASSED                       [ 98%]\ntests/test_hB.py::test_B01_driver_output_matches_the_analytic_expectation PASSED [ 98%]\ntests/test_hB.py::test_B02_nonfinite_position_on_disk_asserts PASSED     [ 99%]\ntests/test_hB.py::test_B03_position_outside_box_on_disk_asserts PASSED   [ 99%]\ntests/test_hB.py::test_B04_malformed_config_through_driver PASSED        [ 99%]\ntests/test_hB.py::test_B05_driver_honours_nondefault_config PASSED       [100%]\n\n=================================== FAILURES ===================================\n_________________ test_A100_rejects[mass_bin_width_value_10.0] _________________\ntests/test_hA.py:513: in test_A100_rejects\n    assert any(re.search(rf\"\\b{re.escape(n)}\\b\", message) for n in names), (\nE   AssertionError: message names none of ['mass_bin_width']: 'config mass grid must define at least one mass bin; got 0'\nE   assert False\nE    +  where False = any(<generator object test_A100_rejects.<locals>.<genexpr> at 0x10bd04240>)\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A100_rejects[mass_bin_width_value_10.0] - Asser...\n======================== 1 failed, 314 passed in 0.76s =========================\n",
    "stderr_tail": "",
    "obligations": [
      {
        "id": "rejection_matrix",
        "passed": 204,
        "collected": 205,
        "fraction": 0.9951219512195122,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_A100_rejects[mass_bin_width_value_10.0]"
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
      "tests/test_pair_finder_validation.py::test_box_size_missing",
      "tests/test_pair_finder_validation.py::test_box_size_non_finite",
      "tests/test_pair_finder_validation.py::test_box_size_not_positive",
      "tests/test_pair_finder_validation.py::test_box_size_not_scalar",
      "tests/test_pair_finder_validation.py::test_catalog_invalid_dtype",
      "tests/test_pair_finder_validation.py::test_catalog_missing_key",
      "tests/test_pair_finder_validation.py::test_catalog_non_finite",
      "tests/test_pair_finder_validation.py::test_catalog_not_1d",
      "tests/test_pair_finder_validation.py::test_catalog_not_dict",
      "tests/test_pair_finder_validation.py::test_catalog_not_ndarray",
      "tests/test_pair_finder_validation.py::test_catalog_unequal_length",
      "tests/test_pair_finder_validation.py::test_config_missing_key",
      "tests/test_pair_finder_validation.py::test_config_not_dict",
      "tests/test_pair_finder_validation.py::test_config_scalar_non_finite",
      "tests/test_pair_finder_validation.py::test_config_scalar_not_positive",
      "tests/test_pair_finder_validation.py::test_config_scalar_not_scalar",
      "tests/test_pair_finder_validation.py::test_log_mass_max_not_greater",
      "tests/test_pair_finder_validation.py::test_mass_grid_no_bin",
      "tests/test_pair_finder_validation.py::test_mass_ratio_min_boundaries",
      "tests/test_pair_finder_validation.py::test_mass_ratio_min_range",
      "tests/test_pair_finder_validation.py::test_position_boundaries",
      "tests/test_pair_finder_validation.py::test_position_outside_box",
      "tests/test_pair_finder_validation.py::test_precedence_finiteness_before_position",
      "tests/test_pair_finder_validation.py::test_precedence_mass_grid",
      "tests/test_pair_finder_validation.py::test_precedence_sep_bins",
      "tests/test_pair_finder_validation.py::test_sep_bins_elements_not_scalars",
      "tests/test_pair_finder_validation.py::test_sep_bins_invalid_type",
      "tests/test_pair_finder_validation.py::test_sep_bins_ndarray_invalid_dtype",
      "tests/test_pair_finder_validation.py::test_sep_bins_ndarray_not_1d",
      "tests/test_pair_finder_validation.py::test_sep_bins_non_finite",
      "tests/test_pair_finder_validation.py::test_sep_bins_not_increasing",
      "tests/test_pair_finder_validation.py::test_sep_bins_too_few_edges",
      "tests/test_pair_finder_validation.py::test_valid_extra_keys",
      "tests/test_pair_finder_validation.py::test_valid_integer_catalog",
      "tests/test_pair_finder_validation.py::test_valid_masses_outside_range",
      "tests/test_pair_finder_validation.py::test_valid_numpy_scalars_in_config",
      "tests/test_pair_finder_validation.py::test_valid_sep_bins_types",
      "tests/test_pair_finder_validation.py::test_valid_zero_length_catalog",
      "tests/test_pair_finder_validation.py::test_validation_before_early_return",
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
      "tests/test_statistical.py::TestMaxwellMoments::test_mean[0]",
      "tests/test_statistical.py::TestMaxwellMoments::test_mean[1]",
      "tests/test_statistical.py::TestMaxwellMoments::test_mean[2]",
      "tests/test_statistical.py::TestMaxwellMoments::test_mean[3]",
      "tests/test_statistical.py::TestMaxwellMoments::test_mean[4]",
      "tests/test_statistical.py::TestMaxwellMoments::test_mean[5]",
      "tests/test_statistical.py::TestMaxwellMoments::test_second_moment[0]",
      "tests/test_statistical.py::TestMaxwellMoments::test_second_moment[1]",
      "tests/test_statistical.py::TestMaxwellMoments::test_second_moment[2]",
      "tests/test_statistical.py::TestMaxwellMoments::test_second_moment[3]",
      "tests/test_statistical.py::TestMaxwellMoments::test_second_moment[4]",
      "tests/test_statistical.py::TestMaxwellMoments::test_second_moment[5]",
      "tests/test_statistical.py::TestMaxwellMoments::test_skewness_scale_invariant",
      "tests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[0]",
      "tests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[1]",
      "tests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[2]",
      "tests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[3]",
      "tests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[4]",
      "tests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[5]"
    ],
    "failed_nodes": [],
    "unparsable": false,
    "collect_timed_out": false,
    "tail": "y::TestMaxwellDistribution::test_ks_against_maxwell[3-5.0] PASSED [ 74%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-2.0] PASSED [ 75%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-3.0] PASSED [ 76%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-4.0] PASSED [ 77%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-5.0] PASSED [ 78%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-2.0] PASSED [ 78%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-3.0] PASSED [ 79%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-4.0] PASSED [ 80%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-5.0] PASSED [ 81%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[0] PASSED [ 82%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[1] PASSED [ 83%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[2] PASSED [ 84%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[3] PASSED [ 84%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[4] PASSED [ 85%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[5] PASSED [ 86%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[0] PASSED       [ 87%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[1] PASSED       [ 88%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[2] PASSED       [ 89%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[3] PASSED       [ 89%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[4] PASSED       [ 90%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[5] PASSED       [ 91%]\ntests/test_statistical.py::TestMaxwellMoments::test_skewness_scale_invariant PASSED [ 92%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[0] PASSED [ 93%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[1] PASSED [ 94%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[2] PASSED [ 94%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[3] PASSED [ 95%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[4] PASSED [ 96%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[5] PASSED [ 97%]\ntests/test_statistical.py::TestBulkVelocityCancellation::test_delta_v_independent_of_bulk_sigma PASSED [ 98%]\ntests/test_statistical.py::TestCrossBinKineticTheory::test_cross_bin_sigma_eff PASSED [ 99%]\ntests/test_statistical.py::TestMassRatioDistribution::test_mass_ratio_is_uniform PASSED [100%]\n\n============================= 119 passed in 1.86s ==============================\n"
  },
  "ships_red_outside_root": {
    "ships_red_outside_root": false,
    "returncode": 0,
    "timed_out": false,
    "tail": "........................................................................ [ 60%]\n...............................................                          [100%]\n119 passed in 1.97s\n"
  },
  "test_adequacy": {
    "per_mutation": {
      "M01_catalog_key_presence_box_size": "kill",
      "M01_catalog_key_presence_log_stellar_mass": "survive",
      "M01_catalog_key_presence_vx": "survive",
      "M01_catalog_key_presence_vy": "survive",
      "M01_catalog_key_presence_vz": "survive",
      "M01_catalog_key_presence_x": "kill",
      "M01_catalog_key_presence_y": "survive",
      "M01_catalog_key_presence_z": "survive",
      "M02_catalog_length_mismatch_log_stellar_mass": "survive",
      "M02_catalog_length_mismatch_vx": "survive",
      "M02_catalog_length_mismatch_vy": "survive",
      "M02_catalog_length_mismatch_vz": "survive",
      "M02_catalog_length_mismatch_x": "kill",
      "M02_catalog_length_mismatch_y": "survive",
      "M02_catalog_length_mismatch_z": "survive",
      "M03_catalog_nonfinite_log_stellar_mass": "survive",
   
```
