# Trial report: 20260907T041321Z-002-pair-binning-convention-macstudio_qwen_qwen3.6-27b-q8-seventh-session-20260907-opencode-macstudio_qwen_qwen3.6-27b-q8-2-e34799

- Task: `002-pair-binning-convention`
- Model: `macstudio/qwen/qwen3.6-27b-q8` (harness: opencode)
- Model duration: 4240.7s | venv setup: 33.2s | timed out: False | committed: False
- Changed files: src/config.py, src/pair_binning.py, tests/test_pair_binning.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 88.1 / 100

## Judged: readability 75% of weight, maintainability 50% of weight (judge claude-opus-5, status ok)

## Composite score: 84.4 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 99% |
| test_adequacy | automated | 25 | 61% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 100% |
| readability | judged | 8 | 75% |
| maintainability | judged | 7 | 50% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| api_surface_and_bin_geometry | 5 | 5 | 1.00 |
| denominator_galaxy_counting | 10 | 10 | 1.00 |
| pinned_pair_counts_under_every_supported_convention | 11 | 11 | 1.00 |
| additivity_and_exclusion_invariant_preservation | 13 | 14 | 0.93 |
| rejection_semantics_of_the_pure_counting_functions | 43 | 44 | 0.98 |
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
  "grader_git_rev": "af3a9197df22b6452cc2911a89a0f6df87cc9c9d",
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
      "tests/test_hA.py::test_A21_incidence_without_galaxies_rejected",
      "tests/test_hA.py::test_A30_check_additivity_exact_above_2_53"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "unts_length_mismatch PASSED  [ 81%]\ntests/test_hB.py::test_B13_output_schema_on_mock PASSED                  [ 82%]\ntests/test_hB.py::test_B14_returned_dicts_match_persisted PASSED         [ 82%]\ntests/test_hB.py::test_B15_one_denominator_shared_by_every_convention PASSED [ 83%]\ntests/test_hB.py::test_B16_end_to_end_counts_recomputed_independently PASSED [ 84%]\ntests/test_hB.py::test_B17_conventions_config_tracks_through_the_driver PASSED [ 85%]\ntests/test_hB.py::test_B18_single_redshift_run PASSED                    [ 85%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[missing_data-<lambda>-None] PASSED [ 86%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[missing_results-<lambda>-None] PASSED [ 87%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_redshift-None-override2] PASSED [ 87%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_mass_ratio_min-None-override3] PASSED [ 88%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_max_sep-None-override4] PASSED [ 89%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[malformed_redshift-None-override5] PASSED [ 90%]\ntests/test_hB.py::test_B19b_preflight_checks_every_configured_redshift_before_writing PASSED [ 90%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad0] PASSED [ 91%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad1] PASSED [ 92%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad2] PASSED [ 92%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad3] PASSED [ 93%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad4] PASSED [ 94%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[primary] PASSED [ 95%]\ntests/test_hB.py::test_B21_console_summary_fields PASSED                 [ 95%]\ntests/test_hB.py::test_B21b_console_line_selection_is_token_exact_not_substring PASSED [ 96%]\ntests/test_hB.py::test_B22_console_reports_not_checked_for_partial_convention_set PASSED [ 97%]\ntests/test_hB.py::test_B23_provenance_compared_against_config_not_defaults PASSED [ 97%]\ntests/test_hB.py::test_B24_additivity_false_from_check_propagates_everywhere PASSED [ 98%]\ntests/test_hB.py::test_B26_full_driver_run_on_nondefault_bin_grid PASSED [ 99%]\ntests/test_hB.py::test_B27_low_mass_ratio_pair_not_refiltered PASSED     [100%]\n\n=================================== FAILURES ===================================\n_________________ test_A21_incidence_without_galaxies_rejected _________________\ntests/test_hA.py:310: in test_A21_incidence_without_galaxies_rejected\n    assert rejects(PB.compute_pair_fraction, np.array([1]), np.array([0])) == \"assert\"\nE   AssertionError: assert None == 'assert'\nE    +  where None = rejects(<function compute_pair_fraction at 0x10a339dd0>, array([1]), array([0]))\nE    +    where <function compute_pair_fraction at 0x10a339dd0> = PB.compute_pair_fraction\nE    +    and   array([1]) = <built-in function array>([1])\nE    +      where <built-in function array> = np.array\nE    +    and   array([0]) = <built-in function array>([0])\nE    +      where <built-in function array> = np.array\n__________________ test_A30_check_additivity_exact_above_2_53 __________________\ntests/test_hA.py:476: in test_A30_check_additivity_exact_above_2_53\n    assert PB.check_additivity(big, one, big) is False\nE   assert True is False\nE    +  where True = <function check_additivity at 0x10a339e80>(array([9007199254740992]), array([1]), array([9007199254740992]))\nE    +    where <function check_additivity at 0x10a339e80> = PB.check_additivity\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A21_incidence_without_galaxies_rejected - Asser...\nFAILED tests/test_hA.py::test_A30_check_additivity_exact_above_2_53 - assert ...\n======================== 2 failed, 138 passed in 3.17s =========================\n",
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
        "passed": 13,
        "collected": 14,
        "fraction": 0.9285714285714286,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_A30_check_additivity_exact_above_2_53"
        ]
      },
      {
        "id": "rejection_semantics_of_the_pure_counting_functions",
        "passed": 43,
        "collected": 44,
        "fraction": 0.9772727272727273,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_A21_incidence_without_galaxies_rejected"
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
      "tests/test_pair_binning.py::TestCheckAdditivity::test_all_zero_vectors",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_reject_complex",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_reject_mismatched_shapes",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_reject_negative",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_reject_non_1d",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_reject_non_finite",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_reject_non_integer_valued",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_returns_false_when_violated",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_returns_true_when_holds",
      "tests/test_pair_binning.py::TestComputePairFraction::test_accept_float64_integer_valued",
      "tests/test_pair_binning.py::TestComputePairFraction::test_accept_integer_dtype_input",
      "tests/test_pair_binning.py::TestComputePairFraction::test_docstring_contains_required_sentence",
      "tests/test_pair_binning.py::TestComputePairFraction::test_exact_values",
      "tests/test_pair_binning.py::TestComputePairFraction::test_n_pairs_positive_with_zero_galaxies_yields_zero",
      "tests/test_pair_binning.py::TestComputePairFraction::test_reject_complex",
      "tests/test_pair_binning.py::TestComputePairFraction::test_reject_mismatched_shapes",
      "tests/test_pair_binning.py::TestComputePairFraction::test_reject_negative_counts",
      "tests/test_pair_binning.py::TestComputePairFraction::test_reject_non_1d",
      "tests/test_pair_binning.py::TestComputePairFraction::test_reject_non_finite",
      "tests/test_pair_binning.py::TestComputePairFraction::test_reject_non_integer_valued",
      "tests/test_pair_binning.py::TestComputePairFraction::test_zero_zero_yields_zero_not_nan",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_either_excluded",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_primary_excluded",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_reject_complex",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_reject_mismatched_shapes",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_reject_non_1d",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_reject_non_finite",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_reject_non_string_convention",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_reject_secondary_gt_primary",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_reject_unsupported_convention",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_secondary_excluded",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_custom_range_length_2",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_exact_values_default_config",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_independent_of_convention_no_key",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_independent_of_convention_various[mean]",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_independent_of_convention_various[nonsense]",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_independent_of_convention_various[primary]",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_independent_of_convention_various[secondary]",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_independent_of_convention_various[total]",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_integer_dtype",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_reject_complex",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_reject_nan",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_reject_non_1d",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_reject_non_finite",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_zero_length",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_additivity_holds_on_sample",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_either_counts",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_exclusion_sum_rule_primary",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_exclusion_sum_rule_secondary",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_primary_counts",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_reject_complex_input",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_reject_mismatched_shapes",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_reject_non_1d",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_reject_non_finite_primary",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_reject_non_finite_secondary",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_reject_non_string_convention",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_reject_secondary_gt_primary",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_reject_unsupported_convention_string[mean]",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_reject_unsupported_convention_string[total]",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_reject_unsupported_convention_string[unknown]",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_same_bin_vs_different_bin",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_secondary_counts",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_three_vectors_distinct",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_zero_length_arrays",
      "tests/test_pair_binning.py::TestDataPathHelpers::test_data_path",
      "tests/test_pair_binning.py::TestDataPathHelpers::test_results_path",
      "tests/test_pair_binning.py::TestEndToEndVerification::test_end_to_end_counts_match",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_additivity_on_mock_data",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_exclusion_sum_rule_primary",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_exclusion_sum_rule_secondary",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_honours_single_entry_list",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_honours_two_entry_list",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_keys_on_mock_data",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_n_galaxies_no_convention_axis",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_n_pairs_keyed_by_conventions",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_n_pairs_total_equals_dataset_length",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_per_convention_counts_vary",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_reject_invalid_conventions_list[conventions0]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_reject_invalid_conventions_list[conventions1]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_reject_invalid_conventions_list[conventions2]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_reject_invalid_conventions_list[conventions3]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_reject_invalid_conventions_list[conventions4]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_reject_invalid_conventions_list[primary]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_reject_malformed_string_attr",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_reject_mismatched_redshift_attr",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_reject_missing_data_file",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_reject_missing_mass_primary_dataset",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_reject_missing_results_file",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_reject_unequal_dataset_lengths",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_stored_bin_assignment_not_used",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_sum_n_galaxies_matches_catalog",
      "tests/test_pair_binning.py::TestMassBinEdges::test_custom_range",
      "tests/test_pair_binning.py::TestMassBinEdges::test_default_config",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_additivity_line_in_summary",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_additivity_on_mock_data",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_console_summary_heading",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_console_summary_tokens",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_conventions_tracks_config_reversed_order",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_invalid_conventions_leaves_sentinel_untouched",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_n_galaxies_no_convention_axis",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_pair_fraction_and_err_finite_non_negative",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_pair_fraction_equals_n_pairs_over_n_galaxies",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_persisted_values_match_returned_dicts",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_preflight_mismatched_attr_leaves_sentinel_untouched",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_preflight_missing_data_leaves_sentinel_untouched",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_returned_dicts_have_seven_keys",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_single_redshift",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_two_convention_run_not_checked",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_written_file_schema",
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
  
```
