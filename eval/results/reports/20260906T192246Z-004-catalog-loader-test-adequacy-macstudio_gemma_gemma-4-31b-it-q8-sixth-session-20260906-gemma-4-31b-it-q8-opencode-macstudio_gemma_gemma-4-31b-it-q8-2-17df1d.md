# Trial report: 20260906T192246Z-004-catalog-loader-test-adequacy-macstudio_gemma_gemma-4-31b-it-q8-sixth-session-20260906-gemma-4-31b-it-q8-opencode-macstudio_gemma_gemma-4-31b-it-q8-2-17df1d

- Task: `004-catalog-loader-test-adequacy`
- Model: `macstudio/gemma/gemma-4-31b-it-q8` (harness: opencode)
- Model duration: 1240.3s | venv setup: 30.0s | timed out: False | committed: False
- Changed files: tests/test_data_reader.py
- Profile: `test_authoring` | Complete submission: True
- Gate status: passed | Integrity violation: False

## Deterministic score: 89.9 / 100

## Judged: readability 75% of weight, maintainability 50% of weight (judge claude-opus-5, status ok)

## Composite score: 85.9 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | gate | 100% |
| test_adequacy | automated | 65 | 87% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 100% |
| readability | judged | 8 | 75% |
| maintainability | judged | 7 | 50% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| frozen_rejection_semantics | 8 | 8 | 1.00 |
| accepted_input_and_return_shape | 3 | 3 | 1.00 |
| mass_selection_semantics | 13 | 13 | 1.00 |
| dtype_and_scalar_semantics | 9 | 9 | 1.00 |
| driver_integration_path | 3 | 3 | 1.00 |
| deliverable_exists_and_collects | 2 | 2 | 1.00 |

## Provenance

```json
{
  "rubric_version": 2,
  "rubric_sha256": "a4a93e1f5fd3b17c7ad7f873dd74a65ff2c74da8a1f759c4ac5e3e8a1d7a9102",
  "rubric_profile": "test_authoring",
  "task_contract_sha256": "829548edc6c2fe8a850dbe11c99ac2f3d07fef5ddc2ef2325deb4821b581e5f7",
  "evaluator_content_sha256": "c1fbfe8ba8842539080d3d8814ada4b1b7895523611bbc1b73cabe5cfe3f504d",
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
    "total": 38,
    "passed": 38,
    "failed": [],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "============================= test session starts ==============================\nplatform darwin -- Python 3.14.7, pytest-9.1.1, pluggy-1.6.0 -- /Users/dcroton/Local/git-repos/ai-agent-bench/venv/bin/python\nrootdir: /Users/dcroton/Local/git-repos/ai-agent-bench/eval/results/tmp/worktrees/20260906T192246Z-004-catalog-loader-test-adequacy-macstudio_gemma_gemma-4-31b-it-q8-sixth-session-20260906-gemma-4-31b-it-q8-opencode-macstudio_gemma_gemma-4-31b-it-q8-2-17df1d\ncollecting ... collected 38 items\n\ntests/test_hA.py::test_A01_missing_file_rejected PASSED                  [  2%]\ntests/test_hA.py::test_A02_missing_file_message_names_path PASSED        [  5%]\ntests/test_hA.py::test_A03_empty_catalog_rejected PASSED                 [  7%]\ntests/test_hA.py::test_A04_non_positive_box_size_rejected[0.0] PASSED    [ 10%]\ntests/test_hA.py::test_A04_non_positive_box_size_rejected[-2.0] PASSED   [ 13%]\ntests/test_hA.py::test_A05_negative_mass_rejected PASSED                 [ 15%]\ntests/test_hA.py::test_A06_empty_selection_rejected PASSED               [ 18%]\ntests/test_hA.py::test_A07_emptiness_reported_before_box_size PASSED     [ 21%]\ntests/test_hA.py::test_A08_zero_mass_accepted PASSED                     [ 23%]\ntests/test_hA.py::test_A09_extra_datasets_and_attrs_ignored PASSED       [ 26%]\ntests/test_hA.py::test_A10_returned_keys_exact PASSED                    [ 28%]\ntests/test_hA.py::test_A11_selection_applied_to_every_array[x] PASSED    [ 31%]\ntests/test_hA.py::test_A11_selection_applied_to_every_array[y] PASSED    [ 34%]\ntests/test_hA.py::test_A11_selection_applied_to_every_array[z] PASSED    [ 36%]\ntests/test_hA.py::test_A11_selection_applied_to_every_array[vx] PASSED   [ 39%]\ntests/test_hA.py::test_A11_selection_applied_to_every_array[vy] PASSED   [ 42%]\ntests/test_hA.py::test_A11_selection_applied_to_every_array[vz] PASSED   [ 44%]\ntests/test_hA.py::test_A11_selection_applied_to_every_array[log_stellar_mass] PASSED [ 47%]\ntests/test_hA.py::test_A12_selection_preserves_order PASSED              [ 50%]\ntests/test_hA.py::test_A13_selection_edges[masses0-expected0] PASSED     [ 52%]\ntests/test_hA.py::test_A13_selection_edges[masses1-expected1] PASSED     [ 55%]\ntests/test_hA.py::test_A13_selection_edges[masses2-expected2] PASSED     [ 57%]\ntests/test_hA.py::test_A13_selection_edges[masses3-expected3] PASSED     [ 60%]\ntests/test_hA.py::test_A14_selection_reads_the_config PASSED             [ 63%]\ntests/test_hA.py::test_A15_arrays_converted_to_float64[int32] PASSED     [ 65%]\ntests/test_hA.py::test_A15_arrays_converted_to_float64[uint16] PASSED    [ 68%]\ntests/test_hA.py::test_A15_arrays_converted_to_float64[float32] PASSED   [ 71%]\ntests/test_hA.py::test_A16_integer_values_survive_conversion PASSED      [ 73%]\ntests/test_hA.py::test_A17_redshift_returned PASSED                      [ 76%]\ntests/test_hA.py::test_A18_box_size_returned PASSED                      [ 78%]\ntests/test_hA.py::test_A19_scalars_returned_unscaled[0.0-1.0] PASSED     [ 81%]\ntests/test_hA.py::test_A19_scalars_returned_unscaled[4.0-62.5] PASSED    [ 84%]\ntests/test_hA.py::test_A20_scalars_unaffected_by_selection PASSED        [ 86%]\ntests/test_hB.py::test_B01_driver_loads_a_catalog_and_writes_results PASSED [ 89%]\ntests/test_hB.py::test_B02_driver_rejects_an_out_of_range_catalog PASSED [ 92%]\ntests/test_hB.py::test_B03_driver_rejects_a_bad_box_size PASSED          [ 94%]\ntests/test_hB.py::test_B04_deliverable_exists PASSED                     [ 97%]\ntests/test_hB.py::test_B05_deliverable_collects_at_least_one_test PASSED [100%]\n\n============================== 38 passed in 1.33s ==============================\n",
    "stderr_tail": "",
    "obligations": [
      {
        "id": "frozen_rejection_semantics",
        "passed": 8,
        "collected": 8,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "accepted_input_and_return_shape",
        "passed": 3,
        "collected": 3,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "mass_selection_semantics",
        "passed": 13,
        "collected": 13,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "dtype_and_scalar_semantics",
        "passed": 9,
        "collected": 9,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "driver_integration_path",
        "passed": 3,
        "collected": 3,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "deliverable_exists_and_collects",
        "passed": 2,
        "collected": 2,
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
      "tests/test_data_reader.py::test_accept_any_positive_box_and_redshift",
      "tests/test_data_reader.py::test_accept_extra_data",
      "tests/test_data_reader.py::test_accept_various_numeric_dtypes",
      "tests/test_data_reader.py::test_accept_zero_mass",
      "tests/test_data_reader.py::test_array_dtypes",
      "tests/test_data_reader.py::test_load_empty_catalog",
      "tests/test_data_reader.py::test_load_file_not_found",
      "tests/test_data_reader.py::test_load_invalid_box_size",
      "tests/test_data_reader.py::test_load_negative_mass",
      "tests/test_data_reader.py::test_load_no_galaxies_in_range",
      "tests/test_data_reader.py::test_mass_selection_config_dependency",
      "tests/test_data_reader.py::test_mass_selection_filtering_and_consistency",
      "tests/test_data_reader.py::test_mass_selection_inclusive",
      "tests/test_data_reader.py::test_mass_selection_order",
      "tests/test_data_reader.py::test_rejection_order_boxsize_vs_mass",
      "tests/test_data_reader.py::test_rejection_order_empty_vs_boxsize",
      "tests/test_data_reader.py::test_rejection_order_mass_vs_range",
      "tests/test_data_reader.py::test_returned_keys",
      "tests/test_data_reader.py::test_scalar_types_and_values",
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
    "tail": "y::TestMaxwellDistribution::test_ks_against_maxwell[3-5.0] PASSED [ 69%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-2.0] PASSED [ 70%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-3.0] PASSED [ 71%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-4.0] PASSED [ 72%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-5.0] PASSED [ 73%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-2.0] PASSED [ 74%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-3.0] PASSED [ 75%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-4.0] PASSED [ 76%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-5.0] PASSED [ 77%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[0] PASSED [ 78%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[1] PASSED [ 79%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[2] PASSED [ 80%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[3] PASSED [ 81%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[4] PASSED [ 82%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[5] PASSED [ 83%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[0] PASSED       [ 84%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[1] PASSED       [ 85%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[2] PASSED       [ 86%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[3] PASSED       [ 87%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[4] PASSED       [ 88%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[5] PASSED       [ 89%]\ntests/test_statistical.py::TestMaxwellMoments::test_skewness_scale_invariant PASSED [ 90%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[0] PASSED [ 91%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[1] PASSED [ 92%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[2] PASSED [ 93%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[3] PASSED [ 94%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[4] PASSED [ 95%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[5] PASSED [ 96%]\ntests/test_statistical.py::TestBulkVelocityCancellation::test_delta_v_independent_of_bulk_sigma PASSED [ 97%]\ntests/test_statistical.py::TestCrossBinKineticTheory::test_cross_bin_sigma_eff PASSED [ 98%]\ntests/test_statistical.py::TestMassRatioDistribution::test_mass_ratio_is_uniform PASSED [100%]\n\n============================== 99 passed in 2.34s ==============================\n"
  },
  "ships_red_outside_root": {
    "ships_red_outside_root": false,
    "returncode": 0,
    "timed_out": false,
    "tail": "........................................................................ [ 72%]\n...........................                                              [100%]\n99 passed in 2.17s\n"
  },
  "test_adequacy": {
    "per_mutation": {
      "M01_missing_file_guard_removed": "kill",
      "M02_empty_catalog_guard_removed": "kill",
      "M03_box_size_positive_guard_removed": "kill",
      "M04_negative_mass_guard_removed": "kill",
      "M05_empty_selection_guard_removed": "kill",
      "M06_mass_min_boundary_excluded": "kill",
      "M07_mass_max_boundary_excluded": "kill",
      "M08_zero_mass_rejected": "kill",
      "M09_extra_datasets_rejected": "kill",
      "M10_float64_cast_removed_log_stellar_mass": "kill",
      "M10_float64_cast_removed_vx": "kill",
      "M10_float64_cast_removed_vy": "kill",
      "M10_float64_cast_removed_vz": "kill",
      "M10_float64_cast_removed_x": "kill",
      "M10_float64_cast_removed_y": "kill",
      "M10_float64_cast_removed_z": "kill",
      "M11_redshift_off_by_one": "kill",
      "M12_box_size_scaled": "kill",
      "M13_wrong_rows_selected_log_stellar_mass": "kill",
      "M13_wrong_rows_selected_vx": "kill",
      "M13_wrong_rows_selected_vy": "kill",
      "M13_wrong_rows_selected_vz": "kill",
      "M13_wrong_rows_selected_x": "kill",
      "M13_wrong_rows_selected_y": "kill",
      "M13_wrong_rows_selected_z": "kill",
      "M14_message_omits_box_size_positive": "kill",
      "M14_message_omits_empty_catalog": "kill",
      "M14_message_omits_file_not_found": "kill",
      "M14_message_omits_filepath_empty_catalog": "kill",
      "M14_message_omits_filepath_mass_range": "kill",
      "M14_message_omits_filepath_missing_file": "kill",
      "M14_message_omits_log_stellar_mass": "kill",
      "M14_message_omits_no_galaxies_in_range": "kill",
      "M14_message_omits_units_note": "kill",
      "M15_config_bounds_ignored": "kill",
      "M16_selected_order_reversed_log_stellar_mass": "kill",
      "M16_selected_order_reversed_vx": "survive",
      "M16_selected_order_reversed_vy": "survive",
      "M16_selected_order_reversed_vz": "survive",
      "M16_selected_order_reversed_x": "kill",
      "M16_selected_order_reversed_y": "survive",
      "M16_selected_order_reversed_z": "survive",
      "M17_unexpected_result_key_leaked": "kill",
      "M18_extra_attributes_rejected": "kill",
      "M19_box_size_reported_before_emptiness": "kill",
      "M19_empty_selection_reported_before_negative_mass": "kill",
      "M19_negative_mass_reported_before_box_size": "kill",
      "M20_box_size_not_cast_to_float": "survive",
      "M20_redshift_not_cast_to_float": "survive",
      "M21_extra_attribute_leaked": "kill",
      "M21_extra_dataset_leaked": "kill",
      "M22_small_box_size_rejected": "kill",
      "M22_zero_redshift_rejected": "kill"
    },
    "killed": 46,
    "total": 53,
    "baseline_passed_count": 19,
    "credit_paths": [
      "tests/test_data_reader.py"
    ],
    "baseline_passed_eligible": 19,
    "baseline_passed_total": 99
  },
  "scope_discipline": {
    "changed_files": [
      "tests/test_data_reader.py"
    ],
    "violations": [],
    "integrity_violations": [],
    "out_of_scope": [],
    "frozen_touched": [],
    "penalty_per_file"
```
