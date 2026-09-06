# Trial report: 20260905T135656Z-002-pair-binning-convention-claude-haiku-4-5-20251001-weak-tier-20260905-claude-claude-haiku-4-5-20251001-1-e60517

- Task: `002-pair-binning-convention`
- Model: `claude-haiku-4-5-20251001` (harness: claude)
- Model duration: 440.0s | venv setup: 23.7s | timed out: False | committed: False
- Changed files: src/config.py, src/pair_binning.py, tests/test_pair_binning.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 75.3 / 100

## Judged: readability 50% of weight, maintainability 25% of weight (judge claude-opus-5, status ok)

## Composite score: 69.7 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 96% |
| test_adequacy | automated | 25 | 41% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 53% |
| readability | judged | 8 | 50% |
| maintainability | judged | 7 | 25% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| api_surface_and_bin_geometry | 5 | 5 | 1.00 |
| denominator_galaxy_counting | 9 | 10 | 0.90 |
| pinned_pair_counts_under_every_supported_convention | 11 | 11 | 1.00 |
| additivity_and_exclusion_invariant_preservation | 13 | 14 | 0.93 |
| rejection_semantics_of_the_pure_counting_functions | 42 | 44 | 0.95 |
| pair_fraction_and_uncertainty | 4 | 4 | 1.00 |
| snapshot_loading_contract_and_provenance_rejections | 28 | 28 | 1.00 |
| config_tracking_through_loader_and_driver | 4 | 4 | 1.00 |
| persistence_schema_atomicity_and_console_reporting | 18 | 20 | 0.90 |

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
    "passed": 134,
    "failed": [
      "tests/test_hA.py::test_A06_galaxy_count_rejections[bad4-keywords4]",
      "tests/test_hA.py::test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_pairs_per_mass_bin]",
      "tests/test_hA.py::test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_excluded_pairs]",
      "tests/test_hB.py::test_B21_console_summary_fields",
      "tests/test_hB.py::test_B22_console_reports_not_checked_for_partial_convention_set",
      "tests/test_hB.py::test_B24_additivity_false_from_check_propagates_everywhere"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "st_B19_preflight_leaves_sentinel_untouched[bad_max_sep-None-override4] PASSED [ 89%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[malformed_redshift-None-override5] PASSED [ 90%]\ntests/test_hB.py::test_B19b_preflight_checks_every_configured_redshift_before_writing PASSED [ 90%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad0] PASSED [ 91%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad1] PASSED [ 92%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad2] PASSED [ 92%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad3] PASSED [ 93%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad4] PASSED [ 94%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[primary] PASSED [ 95%]\ntests/test_hB.py::test_B21_console_summary_fields FAILED                 [ 95%]\ntests/test_hB.py::test_B21b_console_line_selection_is_token_exact_not_substring PASSED [ 96%]\ntests/test_hB.py::test_B22_console_reports_not_checked_for_partial_convention_set FAILED [ 97%]\ntests/test_hB.py::test_B23_provenance_compared_against_config_not_defaults PASSED [ 97%]\ntests/test_hB.py::test_B24_additivity_false_from_check_propagates_everywhere FAILED [ 98%]\ntests/test_hB.py::test_B26_full_driver_run_on_nondefault_bin_grid PASSED [ 99%]\ntests/test_hB.py::test_B27_low_mass_ratio_pair_not_refiltered PASSED     [100%]\n\n=================================== FAILURES ===================================\n_______________ test_A06_galaxy_count_rejections[bad4-keywords4] _______________\ntests/test_hA.py:149: in test_A06_galaxy_count_rejections\n    assert rejects(PB.count_galaxies_per_mass_bin, bad, BASE) == \"assert\"\nE   AssertionError: assert 'TypeError' == 'assert'\nE     \nE     - assert\nE     + TypeError\n_ test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_pairs_per_mass_bin] _\ntests/test_hA.py:260: in test_A16_pair_array_rejections\n    assert rejects(fn, primary, secondary, \"primary\", BASE) == \"assert\"\nE   AssertionError: assert 'TypeError' == 'assert'\nE     \nE     - assert\nE     + TypeError\n_ test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_excluded_pairs] _\ntests/test_hA.py:260: in test_A16_pair_array_rejections\n    assert rejects(fn, primary, secondary, \"primary\", BASE) == \"assert\"\nE   AssertionError: assert 'TypeError' == 'assert'\nE     \nE     - assert\nE     + TypeError\n_______________________ test_B21_console_summary_fields ________________________\ntests/test_hB.py:702: in test_B21_console_summary_fields\n    assert len(matches) == 1, (z, conv, matches)\nE   AssertionError: (2.0, 'primary', [])\nE   assert 0 == 1\nE    +  where 0 = len([])\n_______ test_B22_console_reports_not_checked_for_partial_convention_set ________\ntests/test_hB.py:748: in test_B22_console_reports_not_checked_for_partial_convention_set\n    assert len(add) == 1, (z, add)\nE   AssertionError: (2.0, [])\nE   assert 0 == 1\nE    +  where 0 = len([])\n__________ test_B24_additivity_false_from_check_propagates_everywhere __________\ntests/test_hB.py:790: in test_B24_additivity_false_from_check_propagates_everywhere\n    assert len(add) == 1, add\nE   AssertionError: []\nE   assert 0 == 1\nE    +  where 0 = len([])\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A06_galaxy_count_rejections[bad4-keywords4] - A...\nFAILED tests/test_hA.py::test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_pairs_per_mass_bin]\nFAILED tests/test_hA.py::test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_excluded_pairs]\nFAILED tests/test_hB.py::test_B21_console_summary_fields - AssertionError: (2...\nFAILED tests/test_hB.py::test_B22_console_reports_not_checked_for_partial_convention_set\nFAILED tests/test_hB.py::test_B24_additivity_false_from_check_propagates_everywhere\n======================== 6 failed, 134 passed in 1.89s =========================\n",
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
        "passed": 9,
        "collected": 10,
        "fraction": 0.9,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_A06_galaxy_count_rejections[bad4-keywords4]"
        ]
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
        "passed": 13,
        "collected": 14,
        "fraction": 0.9285714285714286,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hB.py::test_B24_additivity_false_from_check_propagates_everywhere"
        ]
      },
      {
        "id": "rejection_semantics_of_the_pure_counting_functions",
        "passed": 42,
        "collected": 44,
        "fraction": 0.9545454545454546,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_excluded_pairs]",
          "tests/test_hA.py::test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_pairs_per_mass_bin]"
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
        "passed": 18,
        "collected": 20,
        "fraction": 0.9,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hB.py::test_B21_console_summary_fields",
          "tests/test_hB.py::test_B22_console_reports_not_checked_for_partial_convention_set"
        ]
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
      "tests/test_pair_binning.py::TestCheckAdditivity::test_complex_rejected",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_fails_on_invalid_counts",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_holds_on_all_zeros",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_holds_on_valid_counts",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_mismatched_shapes_rejected",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_negative_rejected",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_non_1d_rejected",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_non_finite_rejected",
      "tests/test_pair_binning.py::TestComputePairFraction::test_accepts_integer_dtypes",
      "tests/test_pair_binning.py::TestComputePairFraction::test_accepts_integer_valued_float",
      "tests/test_pair_binning.py::TestComputePairFraction::test_complex_rejected",
      "tests/test_pair_binning.py::TestComputePairFraction::test_docstring_requirement",
      "tests/test_pair_binning.py::TestComputePairFraction::test_example_fractions",
      "tests/test_pair_binning.py::TestComputePairFraction::test_mismatched_shapes_rejected",
      "tests/test_pair_binning.py::TestComputePairFraction::test_negative_counts_rejected",
      "tests/test_pair_binning.py::TestComputePairFraction::test_non_1d_rejected",
      "tests/test_pair_binning.py::TestComputePairFraction::test_non_finite_rejected",
      "tests/test_pair_binning.py::TestComputePairFraction::test_requires_nonzero_galaxies_for_nonzero_pairs",
      "tests/test_pair_binning.py::TestComputePairFraction::test_zero_pairs_nonzero_galaxies",
      "tests/test_pair_binning.py::TestComputePairFraction::test_zero_pairs_zero_galaxies",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_all_pairs_in_range",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_empty_array",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_example_pair_sample",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_exclusion_sum_rule",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_complex_rejected",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_custom_config",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_default_config_example",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_empty_array",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_independent_of_convention",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_non_1d_rejected",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_non_finite_rejected",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_additivity_identity",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_both_members_same_bin",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_complex_rejected",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_empty_array",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_example_pair_sample",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_mass_secondary_exceeds_primary_rejected",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_mismatched_shapes_rejected",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_non_1d_rejected",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_non_finite_rejected",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_unsupported_convention_rejected",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_additivity_on_generated_data",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_attr_validation_before_coercion",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_conventions_tracked",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_exclusion_sum_rule",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_galaxy_count_matches_catalog",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_generated_mock_data",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_missing_data_file",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_missing_results_file",
      "tests/test_pair_binning.py::TestMassBinEdges::test_custom_config",
      "tests/test_pair_binning.py::TestMassBinEdges::test_default_config",
      "tests/test_pair_binning.py::TestPathFunctions::test_data_path",
      "tests/test_pair_binning.py::TestPathFunctions::test_results_path",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_console_output",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_conventions_ordered",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_end_to_end_on_generated_data",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_output_attrs",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_output_file_created",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_output_schema",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_pair_fraction_computation",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_subset_conventions",
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
    "tail": "y::TestMaxwellDistribution::test_ks_against_maxwell[3-5.0] PAS
```
