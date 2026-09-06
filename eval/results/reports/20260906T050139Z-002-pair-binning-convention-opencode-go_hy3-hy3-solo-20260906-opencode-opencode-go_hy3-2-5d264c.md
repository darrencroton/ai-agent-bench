# Trial report: 20260906T050139Z-002-pair-binning-convention-opencode-go_hy3-hy3-solo-20260906-opencode-opencode-go_hy3-2-5d264c

- Task: `002-pair-binning-convention`
- Model: `opencode-go/hy3` (harness: opencode)
- Model duration: 655.3s | venv setup: 25.2s | timed out: False | committed: False
- Changed files: src/config.py, src/pair_binning.py, tests/test_pair_binning.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 86.7 / 100

## Judged: readability 75% of weight, maintainability 75% of weight (judge claude-opus-5, status ok)

## Composite score: 85.0 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 99% |
| test_adequacy | automated | 25 | 65% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 77% |
| readability | judged | 8 | 75% |
| maintainability | judged | 7 | 75% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| api_surface_and_bin_geometry | 5 | 5 | 1.00 |
| denominator_galaxy_counting | 10 | 10 | 1.00 |
| pinned_pair_counts_under_every_supported_convention | 11 | 11 | 1.00 |
| additivity_and_exclusion_invariant_preservation | 14 | 14 | 1.00 |
| rejection_semantics_of_the_pure_counting_functions | 42 | 44 | 0.95 |
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
    "total": 140,
    "passed": 138,
    "failed": [
      "tests/test_hA.py::test_A16_pair_array_rejections[primary6-secondary6-keywords6-count_excluded_pairs]",
      "tests/test_hA.py::test_A16b_ordering_invariant_violation_on_two_element_array[count_excluded_pairs]"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "PASSED         [ 82%]\ntests/test_hB.py::test_B15_one_denominator_shared_by_every_convention PASSED [ 83%]\ntests/test_hB.py::test_B16_end_to_end_counts_recomputed_independently PASSED [ 84%]\ntests/test_hB.py::test_B17_conventions_config_tracks_through_the_driver PASSED [ 85%]\ntests/test_hB.py::test_B18_single_redshift_run PASSED                    [ 85%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[missing_data-<lambda>-None] PASSED [ 86%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[missing_results-<lambda>-None] PASSED [ 87%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_redshift-None-override2] PASSED [ 87%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_mass_ratio_min-None-override3] PASSED [ 88%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_max_sep-None-override4] PASSED [ 89%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[malformed_redshift-None-override5] PASSED [ 90%]\ntests/test_hB.py::test_B19b_preflight_checks_every_configured_redshift_before_writing PASSED [ 90%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad0] PASSED [ 91%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad1] PASSED [ 92%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad2] PASSED [ 92%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad3] PASSED [ 93%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad4] PASSED [ 94%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[primary] PASSED [ 95%]\ntests/test_hB.py::test_B21_console_summary_fields PASSED                 [ 95%]\ntests/test_hB.py::test_B21b_console_line_selection_is_token_exact_not_substring PASSED [ 96%]\ntests/test_hB.py::test_B22_console_reports_not_checked_for_partial_convention_set PASSED [ 97%]\ntests/test_hB.py::test_B23_provenance_compared_against_config_not_defaults PASSED [ 97%]\ntests/test_hB.py::test_B24_additivity_false_from_check_propagates_everywhere PASSED [ 98%]\ntests/test_hB.py::test_B26_full_driver_run_on_nondefault_bin_grid PASSED [ 99%]\ntests/test_hB.py::test_B27_low_mass_ratio_pair_not_refiltered PASSED     [100%]\n\n=================================== FAILURES ===================================\n_ test_A16_pair_array_rejections[primary6-secondary6-keywords6-count_excluded_pairs] _\ntests/test_hA.py:260: in test_A16_pair_array_rejections\n    assert rejects(fn, primary, secondary, \"primary\", BASE) == \"assert\"\nE   AssertionError: assert None == 'assert'\nE    +  where None = rejects(<function count_excluded_pairs at 0x108495c70>, array([8.]), array([9.]), 'primary', {'box_size': 500.0, 'redshifts': [2.0, 3.0, 4.0, 5.0], 'log_mass_min': 8.0, 'log_mass_max': 11.0, ...})\n_ test_A16b_ordering_invariant_violation_on_two_element_array[count_excluded_pairs] _\ntests/test_hA.py:270: in test_A16b_ordering_invariant_violation_on_two_element_array\n    assert rejects(fn, np.array([9.0, 8.0]), np.array([8.0, 9.0]), \"either\", BASE) == \"assert\"\nE   AssertionError: assert None == 'assert'\nE    +  where None = rejects(<function count_excluded_pairs at 0x108495c70>, array([9., 8.]), array([8., 9.]), 'either', {'box_size': 500.0, 'redshifts': [2.0, 3.0, 4.0, 5.0], 'log_mass_min': 8.0, 'log_mass_max': 11.0, ...})\nE    +    where array([9., 8.]) = <built-in function array>([9.0, 8.0])\nE    +      where <built-in function array> = np.array\nE    +    and   array([8., 9.]) = <built-in function array>([8.0, 9.0])\nE    +      where <built-in function array> = np.array\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A16_pair_array_rejections[primary6-secondary6-keywords6-count_excluded_pairs]\nFAILED tests/test_hA.py::test_A16b_ordering_invariant_violation_on_two_element_array[count_excluded_pairs]\n======================== 2 failed, 138 passed in 2.15s =========================\n",
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
        "passed": 42,
        "collected": 44,
        "fraction": 0.9545454545454546,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_A16_pair_array_rejections[primary6-secondary6-keywords6-count_excluded_pairs]",
          "tests/test_hA.py::test_A16b_ordering_invariant_violation_on_two_element_array[count_excluded_pairs]"
        ]
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
      "tests/test_pair_binning.py::TestAdditivityCheck::test_all_zero",
      "tests/test_pair_binning.py::TestAdditivityCheck::test_holds_and_violated",
      "tests/test_pair_binning.py::TestAdditivityCheck::test_rejections",
      "tests/test_pair_binning.py::TestConfigKey::test_key_present_and_mass_bin_by_unchanged",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_additivity_and_exclusion_on_generated",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_galaxy_count_matches_catalog",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_honours_conventions_list",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_keys_and_no_convention_axis",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_n_pairs_total_matches_rows",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_per_convention_counts_vary",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_reject_attr_problems",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_reject_invalid_conventions_list",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_reject_missing_dataset_and_length",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_reject_missing_files",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_stored_bin_assignment_not_used",
      "tests/test_pair_binning.py::TestMassBinEdgesAndCounts::test_edges_and_counts_custom_config",
      "tests/test_pair_binning.py::TestMassBinEdgesAndCounts::test_galaxy_count_convention_independent",
      "tests/test_pair_binning.py::TestMassBinEdgesAndCounts::test_galaxy_count_default",
      "tests/test_pair_binning.py::TestPairCounting::test_both_members_in_bin_counted_twice_under_either",
      "tests/test_pair_binning.py::TestPairCounting::test_different_bin_pair_totals_differ",
      "tests/test_pair_binning.py::TestPairCounting::test_exclusion_sum_rule",
      "tests/test_pair_binning.py::TestPairCounting::test_sample_counts_and_additivity",
      "tests/test_pair_binning.py::TestPairCounting::test_sample_excluded_counts",
      "tests/test_pair_binning.py::TestPairCounting::test_zero_length",
      "tests/test_pair_binning.py::TestPairFraction::test_assert_pairs_without_galaxies",
      "tests/test_pair_binning.py::TestPairFraction::test_basic",
      "tests/test_pair_binning.py::TestPairFraction::test_docstring_sentence",
      "tests/test_pair_binning.py::TestPairFraction::test_float64_integer_valued_accepted",
      "tests/test_pair_binning.py::TestPairFraction::test_rejections",
      "tests/test_pair_binning.py::TestPairFraction::test_zero_pair_zero_galaxy_exact",
      "tests/test_pair_binning.py::TestRejectionsPart1::test_complex",
      "tests/test_pair_binning.py::TestRejectionsPart1::test_galaxy_count_rejections",
      "tests/test_pair_binning.py::TestRejectionsPart1::test_mismatched_shapes",
      "tests/test_pair_binning.py::TestRejectionsPart1::test_non_1d",
      "tests/test_pair_binning.py::TestRejectionsPart1::test_non_finite",
      "tests/test_pair_binning.py::TestRejectionsPart1::test_secondary_gt_primary",
      "tests/test_pair_binning.py::TestRejectionsPart1::test_unsupported_conventions",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_console_summary_tokens",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_conventions_track_config",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_end_to_end_independent_recompute",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_invalid_conventions_leaves_sentinel",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_preflight_leaves_sentinel_untouched",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_schema_and_values",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_single_redshift",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_two_convention_summary_not_checked",
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
    "tail": "y::TestMaxwellDistribution::test_ks_against_maxwell[3-5.0] PASSED [ 76%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-2.0] PASSED [ 76%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-3.0] PASSED [ 77%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-4.0] PASSED [ 78%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-5.0] PASSED [ 79%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-2.0] PASSED [ 80%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-3.0] PASSED [ 80%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-4.0] PASSED [ 81%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-5.0] PASSED [ 82%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[0] PASSED [ 83%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[1] PASSED [ 84%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[2] PASSED [ 84%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[3] PASSED [ 85%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[4] PASSED [ 86%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[5] PASSED [ 87%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[0] PASSED       [ 88%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[1] PASSED       [ 88%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[2] PASSED       [ 89%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[3] PASSED       [ 90%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[4] PASSED       [ 91%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[5] PASSED       [ 92%]\ntests/test_statistical.py::TestMaxwellMoments::test_skewness_scale_invariant PASSED [ 92%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[0] PASSED [ 93%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributi
```
