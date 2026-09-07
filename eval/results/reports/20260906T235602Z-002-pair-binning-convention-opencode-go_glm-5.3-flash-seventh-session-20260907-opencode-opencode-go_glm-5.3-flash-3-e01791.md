# Trial report: 20260906T235602Z-002-pair-binning-convention-opencode-go_glm-5.3-flash-seventh-session-20260907-opencode-opencode-go_glm-5.3-flash-3-e01791

- Task: `002-pair-binning-convention`
- Model: `opencode-go/glm-5.3-flash` (harness: opencode)
- Model duration: 360.2s | venv setup: 25.7s | timed out: False | committed: False
- Changed files: src/config.py, src/pair_binning.py, tests/test_pair_binning.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 88.7 / 100

## Judged: readability 75% of weight, maintainability 50% of weight (judge claude-opus-5, status ok)

## Composite score: 84.9 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 100% |
| test_adequacy | automated | 25 | 73% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 71% |
| readability | judged | 8 | 75% |
| maintainability | judged | 7 | 50% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| api_surface_and_bin_geometry | 5 | 5 | 1.00 |
| denominator_galaxy_counting | 10 | 10 | 1.00 |
| pinned_pair_counts_under_every_supported_convention | 11 | 11 | 1.00 |
| additivity_and_exclusion_invariant_preservation | 14 | 14 | 1.00 |
| rejection_semantics_of_the_pure_counting_functions | 44 | 44 | 1.00 |
| pair_fraction_and_uncertainty | 4 | 4 | 1.00 |
| snapshot_loading_contract_and_provenance_rejections | 28 | 28 | 1.00 |
| config_tracking_through_loader_and_driver | 4 | 4 | 1.00 |
| persistence_schema_atomicity_and_console_reporting | 20 | 20 | 1.00 |

## Provenance

```json
{
  "rubric_version": 2,
  "rubric_sha256": "a4a93e1f5fd3b17c7ad7f873dd74a65ff2c74da8a1f759c4ac5e3e8a1d7a9102",
  "rubric_profile": "default",
  "task_contract_sha256": "5e163ed2ca2245525b6d1e59ecf201f4bdcd796f84a730de7f92dd6c14cf4826",
  "evaluator_content_sha256": "9de3dc7be290bae7ed25ba7c1df72cac8882f4528a284c3edd64ed15afa7c0ea",
  "grader_git_rev": "1d0b896ab8074d0f43e62c120b6ce0ee68d8ea47",
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
    "total": 140,
    "passed": 140,
    "failed": [],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "y::test_B10_load_snapshot_counts_file_rejections[missing_data] PASSED [ 70%]\ntests/test_hB.py::test_B10_load_snapshot_counts_file_rejections[missing_results] PASSED [ 71%]\ntests/test_hB.py::test_B10_load_snapshot_counts_file_rejections[wrong_redshift] PASSED [ 72%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override0-redshift] PASSED [ 72%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override1-redshift] PASSED [ 73%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override2-redshift] PASSED [ 74%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override3-mass_ratio_min] PASSED [ 75%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override4-mass_ratio_min] PASSED [ 75%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override5-max_sep_kpc] PASSED [ 76%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override6-max_sep_kpc] PASSED [ 77%]\ntests/test_hB.py::test_B12a_load_snapshot_counts_missing_attr[redshift] PASSED [ 77%]\ntests/test_hB.py::test_B12a_load_snapshot_counts_missing_attr[mass_ratio_min] PASSED [ 78%]\ntests/test_hB.py::test_B12a_load_snapshot_counts_missing_attr[max_sep_kpc] PASSED [ 79%]\ntests/test_hB.py::test_B12b_load_snapshot_counts_missing_dataset[mass_primary] PASSED [ 80%]\ntests/test_hB.py::test_B12b_load_snapshot_counts_missing_dataset[mass_secondary] PASSED [ 80%]\ntests/test_hB.py::test_B12c_load_snapshot_counts_length_mismatch PASSED  [ 81%]\ntests/test_hB.py::test_B13_output_schema_on_mock PASSED                  [ 82%]\ntests/test_hB.py::test_B14_returned_dicts_match_persisted PASSED         [ 82%]\ntests/test_hB.py::test_B15_one_denominator_shared_by_every_convention PASSED [ 83%]\ntests/test_hB.py::test_B16_end_to_end_counts_recomputed_independently PASSED [ 84%]\ntests/test_hB.py::test_B17_conventions_config_tracks_through_the_driver PASSED [ 85%]\ntests/test_hB.py::test_B18_single_redshift_run PASSED                    [ 85%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[missing_data-<lambda>-None] PASSED [ 86%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[missing_results-<lambda>-None] PASSED [ 87%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_redshift-None-override2] PASSED [ 87%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_mass_ratio_min-None-override3] PASSED [ 88%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_max_sep-None-override4] PASSED [ 89%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[malformed_redshift-None-override5] PASSED [ 90%]\ntests/test_hB.py::test_B19b_preflight_checks_every_configured_redshift_before_writing PASSED [ 90%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad0] PASSED [ 91%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad1] PASSED [ 92%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad2] PASSED [ 92%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad3] PASSED [ 93%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad4] PASSED [ 94%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[primary] PASSED [ 95%]\ntests/test_hB.py::test_B21_console_summary_fields PASSED                 [ 95%]\ntests/test_hB.py::test_B21b_console_line_selection_is_token_exact_not_substring PASSED [ 96%]\ntests/test_hB.py::test_B22_console_reports_not_checked_for_partial_convention_set PASSED [ 97%]\ntests/test_hB.py::test_B23_provenance_compared_against_config_not_defaults PASSED [ 97%]\ntests/test_hB.py::test_B24_additivity_false_from_check_propagates_everywhere PASSED [ 98%]\ntests/test_hB.py::test_B26_full_driver_run_on_nondefault_bin_grid PASSED [ 99%]\ntests/test_hB.py::test_B27_low_mass_ratio_pair_not_refiltered PASSED     [100%]\n\n============================= 140 passed in 1.90s ==============================\n",
    "stderr_tail": "",
    "obligations": [
      {
        "id": "api_surface_and_bin_geometry",
        "passed": 5,
        "collected": 5,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "denominator_galaxy_counting",
        "passed": 10,
        "collected": 10,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "pinned_pair_counts_under_every_supported_convention",
        "passed": 11,
        "collected": 11,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "additivity_and_exclusion_invariant_preservation",
        "passed": 14,
        "collected": 14,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "rejection_semantics_of_the_pure_counting_functions",
        "passed": 44,
        "collected": 44,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "pair_fraction_and_uncertainty",
        "passed": 4,
        "collected": 4,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "snapshot_loading_contract_and_provenance_rejections",
        "passed": 28,
        "collected": 28,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "config_tracking_through_loader_and_driver",
        "passed": 4,
        "collected": 4,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "persistence_schema_atomicity_and_console_reporting",
        "passed": 20,
        "collected": 20,
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
      "tests/test_pair_binning.py::TestCheckAdditivity::test_holds_and_fails_without_raising",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejections",
      "tests/test_pair_binning.py::TestComputePairFraction::test_accepts_integer_dtypes_and_integer_valued_floats",
      "tests/test_pair_binning.py::TestComputePairFraction::test_docstring_exact_sentence",
      "tests/test_pair_binning.py::TestComputePairFraction::test_positive_pairs_require_galaxies",
      "tests/test_pair_binning.py::TestComputePairFraction::test_reference_values",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejections",
      "tests/test_pair_binning.py::TestComputePairFraction::test_zero_pairs_zero_galaxies_is_exact_zero",
      "tests/test_pair_binning.py::TestEdgesAndGalaxyCounts::test_config_derived_edges_and_lengths",
      "tests/test_pair_binning.py::TestEdgesAndGalaxyCounts::test_count_galaxies_ignores_convention",
      "tests/test_pair_binning.py::TestEdgesAndGalaxyCounts::test_default_edges_and_counts",
      "tests/test_pair_binning.py::TestEdgesAndGalaxyCounts::test_galaxy_count_rejections",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_additivity_and_exclusion_sum_rule",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_conventions_list_honoured",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_counts_do_not_vary_with_stored_bin_assignment",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_counts_vary_with_convention_on_hand_fixture",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_missing_files_rejected",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_n_galaxies_is_half_open_count_of_full_catalog",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_structure",
      "tests/test_pair_binning.py::TestLoadSnapshotRejections::test_conventions_config_rejections",
      "tests/test_pair_binning.py::TestLoadSnapshotRejections::test_mismatched_and_malformed_attrs",
      "tests/test_pair_binning.py::TestLoadSnapshotRejections::test_missing_attr",
      "tests/test_pair_binning.py::TestLoadSnapshotRejections::test_missing_dataset",
      "tests/test_pair_binning.py::TestLoadSnapshotRejections::test_unequal_dataset_lengths",
      "tests/test_pair_binning.py::TestPairCounts::test_additivity_on_reference_sample",
      "tests/test_pair_binning.py::TestPairCounts::test_convention_rejections",
      "tests/test_pair_binning.py::TestPairCounts::test_pair_array_rejections",
      "tests/test_pair_binning.py::TestPairCounts::test_reference_sample_counts",
      "tests/test_pair_binning.py::TestPairCounts::test_reference_sample_exclusion_sum_rule",
      "tests/test_pair_binning.py::TestPairCounts::test_same_bin_and_different_bin_pairs",
      "tests/test_pair_binning.py::TestPairCounts::test_zero_length_inputs",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_console_summary",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_end_to_end_independent_recomputation",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_fraction_is_numerator_over_galaxy_denominator",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_gate_invalid_conventions_untouched",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_gate_malformed_redshift_attr",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_gate_mismatched_mass_ratio_min",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_gate_mismatched_max_sep_kpc",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_gate_mismatched_recorded_redshift",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_gate_missing_data_file",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_gate_missing_results_file",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_output_schema_and_attrs",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_returned_dicts_have_exactly_seven_keys_and_match_file",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_single_redshift_run",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_two_conventions_marked_not_checked",
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
    "tail": "y::TestMaxwellDistribution::test_ks_against_maxwell[3-5.0] PASSED [ 76%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-2.0] PASSED [ 76%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-3.0] PASSED [ 77%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-4.0] PASSED [ 78%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-5.0] PASSED [ 79%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-2.0] PASSED [ 80%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-3.0] PASSED [ 80%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-4.0] PASSED [ 81%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-5.0] PASSED [ 82%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[0] PASSED [ 83%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[1] PASSED [ 84%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[2] PASSED [ 84%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[3] PASSED [ 85%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[4] PASSED [ 86%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[5] PASSED [ 87%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[0] PASSED       [ 88%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[1] PASSED       [ 88%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[2] PASSED       [ 89%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[3] PASSED       [ 90%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[4] PASSED       [ 91%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[5] PASSED       [ 92%]\ntests/test_statistical.py::TestMaxwellMoments::test_skewness_scale_invariant PASSED [ 92%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[0] PASSED [ 93%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[1] PASSED [ 94%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[2] PASSED [ 95%]\ntests/test_statistical.py::Tes
```
