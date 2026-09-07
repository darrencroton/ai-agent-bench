# Trial report: 20260906T221913Z-002-pair-binning-convention-claude-sonnet-5-seventh-session-20260907-claude-sonnet-5-claude-claude-sonnet-5-2-81f752

- Task: `002-pair-binning-convention`
- Model: `claude-sonnet-5` (harness: claude)
- Model duration: 666.6s | venv setup: 34.2s | timed out: False | committed: False
- Changed files: src/config.py, src/pair_binning.py, tests/test_pair_binning.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 90.6 / 100

## Judged: readability 75% of weight, maintainability 75% of weight (judge claude-opus-5, status ok)

## Composite score: 88.3 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 99% |
| test_adequacy | automated | 25 | 69% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 100% |
| readability | judged | 8 | 75% |
| maintainability | judged | 7 | 75% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| api_surface_and_bin_geometry | 5 | 5 | 1.00 |
| denominator_galaxy_counting | 10 | 10 | 1.00 |
| pinned_pair_counts_under_every_supported_convention | 11 | 11 | 1.00 |
| additivity_and_exclusion_invariant_preservation | 13 | 14 | 0.93 |
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
  "grader_git_dirty": false,
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
    "passed": 139,
    "failed": [
      "tests/test_hA.py::test_A30_check_additivity_exact_above_2_53"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "est_B11_load_snapshot_counts_attr_rejections[override4-mass_ratio_min] PASSED [ 75%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override5-max_sep_kpc] PASSED [ 76%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override6-max_sep_kpc] PASSED [ 77%]\ntests/test_hB.py::test_B12a_load_snapshot_counts_missing_attr[redshift] PASSED [ 77%]\ntests/test_hB.py::test_B12a_load_snapshot_counts_missing_attr[mass_ratio_min] PASSED [ 78%]\ntests/test_hB.py::test_B12a_load_snapshot_counts_missing_attr[max_sep_kpc] PASSED [ 79%]\ntests/test_hB.py::test_B12b_load_snapshot_counts_missing_dataset[mass_primary] PASSED [ 80%]\ntests/test_hB.py::test_B12b_load_snapshot_counts_missing_dataset[mass_secondary] PASSED [ 80%]\ntests/test_hB.py::test_B12c_load_snapshot_counts_length_mismatch PASSED  [ 81%]\ntests/test_hB.py::test_B13_output_schema_on_mock PASSED                  [ 82%]\ntests/test_hB.py::test_B14_returned_dicts_match_persisted PASSED         [ 82%]\ntests/test_hB.py::test_B15_one_denominator_shared_by_every_convention PASSED [ 83%]\ntests/test_hB.py::test_B16_end_to_end_counts_recomputed_independently PASSED [ 84%]\ntests/test_hB.py::test_B17_conventions_config_tracks_through_the_driver PASSED [ 85%]\ntests/test_hB.py::test_B18_single_redshift_run PASSED                    [ 85%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[missing_data-<lambda>-None] PASSED [ 86%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[missing_results-<lambda>-None] PASSED [ 87%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_redshift-None-override2] PASSED [ 87%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_mass_ratio_min-None-override3] PASSED [ 88%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_max_sep-None-override4] PASSED [ 89%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[malformed_redshift-None-override5] PASSED [ 90%]\ntests/test_hB.py::test_B19b_preflight_checks_every_configured_redshift_before_writing PASSED [ 90%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad0] PASSED [ 91%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad1] PASSED [ 92%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad2] PASSED [ 92%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad3] PASSED [ 93%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad4] PASSED [ 94%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[primary] PASSED [ 95%]\ntests/test_hB.py::test_B21_console_summary_fields PASSED                 [ 95%]\ntests/test_hB.py::test_B21b_console_line_selection_is_token_exact_not_substring PASSED [ 96%]\ntests/test_hB.py::test_B22_console_reports_not_checked_for_partial_convention_set PASSED [ 97%]\ntests/test_hB.py::test_B23_provenance_compared_against_config_not_defaults PASSED [ 97%]\ntests/test_hB.py::test_B24_additivity_false_from_check_propagates_everywhere PASSED [ 98%]\ntests/test_hB.py::test_B26_full_driver_run_on_nondefault_bin_grid PASSED [ 99%]\ntests/test_hB.py::test_B27_low_mass_ratio_pair_not_refiltered PASSED     [100%]\n\n=================================== FAILURES ===================================\n__________________ test_A30_check_additivity_exact_above_2_53 __________________\ntests/test_hA.py:476: in test_A30_check_additivity_exact_above_2_53\n    assert PB.check_additivity(big, one, big) is False\nE   assert True is False\nE    +  where True = <function check_additivity at 0x10a2cb3d0>(array([9007199254740992]), array([1]), array([9007199254740992]))\nE    +    where <function check_additivity at 0x10a2cb3d0> = PB.check_additivity\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A30_check_additivity_exact_above_2_53 - assert ...\n======================== 1 failed, 139 passed in 2.14s =========================\n",
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
      "tests/test_pair_binning.py::TestCheckAdditivity::test_false_when_identity_violated",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_complex",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_mismatched_shapes",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_negative",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_non_1d",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_non_finite",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_non_integer_valued",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_true_on_all_zero_vectors",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_true_when_identity_holds",
      "tests/test_pair_binning.py::TestComputePairFraction::test_accepts_integer_dtype_and_integer_valued_float",
      "tests/test_pair_binning.py::TestComputePairFraction::test_docstring_contains_required_sentence",
      "tests/test_pair_binning.py::TestComputePairFraction::test_exact_values",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_complex",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_mismatched_shapes",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_n_pairs_positive_with_zero_galaxies",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_negative_counts",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_non_1d",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_non_finite_counts",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_non_integer_valued_counts",
      "tests/test_pair_binning.py::TestComputePairFraction::test_zero_pairs_zero_galaxies_exact_zero",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_exact_recovery_default_config",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_independent_of_mass_bin_by[None]",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_independent_of_mass_bin_by[mean]",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_independent_of_mass_bin_by[nonsense-strategy]",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_independent_of_mass_bin_by[primary]",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_independent_of_mass_bin_by[secondary]",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_independent_of_mass_bin_by[total]",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_rejects_complex",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_rejects_non_1d",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_rejects_non_finite",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_rejects_non_real_string_dtype",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_zero_length_input",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_additivity_holds_on_sample",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_excluded_pairs_hand_computed",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_exclusion_sum_rule_on_sample",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_hand_computed_sample_all_conventions",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_rejects_bad_convention[123]",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_rejects_bad_convention[None]",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_rejects_bad_convention[convention5]",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_rejects_bad_convention[mean]",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_rejects_bad_convention[nonsense]",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_rejects_bad_convention[total]",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_rejects_complex",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_rejects_mismatched_shapes",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_rejects_non_1d",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_rejects_non_finite",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_rejects_secondary_greater_than_primary",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_same_bin_vs_different_bin_pairs",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_zero_length_arrays",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsHandWritten::test_additivity_and_exclusion_sum_rule",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsHandWritten::test_exact_keys_and_no_convention_axis_on_n_galaxies",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsHandWritten::test_honours_single_entry_conventions_list",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsHandWritten::test_honours_two_entry_conventions_list_order",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsHandWritten::test_n_galaxies_matches_full_selected_catalog",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsHandWritten::test_n_pairs_total_matches_dataset_length",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsHandWritten::test_per_convention_counts_vary_and_match_hand_computation",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsHandWritten::test_stored_mass_bin_and_mass_bin_by_are_ignored",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_malformed_attr_rejected[(2+1j)-mass_ratio_min]",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_malformed_attr_rejected[(2+1j)-max_sep_kpc]",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_malformed_attr_rejected[(2+1j)-redshift]",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_malformed_attr_rejected[2.0_0-mass_ratio_min]",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_malformed_attr_rejected[2.0_0-max_sep_kpc]",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_malformed_attr_rejected[2.0_0-redshift]",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_malformed_attr_rejected[2.0_1-mass_ratio_min]",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_malformed_attr_rejected[2.0_1-max_sep_kpc]",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_malformed_attr_rejected[2.0_1-redshift]",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_malformed_attr_rejected[malformed_value3-mass_ratio_min]",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_malformed_attr_rejected[malformed_value3-max_sep_kpc]",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_malformed_attr_rejected[malformed_value3-redshift]",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_mass_ratio_min_mismatch",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_max_sep_kpc_mismatch",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_missing_data_file",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_missing_mass_primary_dataset",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_missing_mass_ratio_min_attr",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_missing_mass_secondary_dataset",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_missing_max_sep_kpc_attr",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_missing_redshift_attr",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_missing_results_file",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_redshift_mismatch",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_rejects_duplicate_conventions",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_rejects_empty_conventions",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_rejects_unsupported_or_malformed_conventions[bad_conventions0]",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_rejects_unsupported_or_malformed_conventions[bad_conventions1]",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_rejects_unsupported_or_malformed_conventions[bad_conventions2]",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_rejects_unsupported_or_malformed_conventions[bad_conventions4]",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_rejects_unsupported_or_malformed_conventions[primary]",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_unequal_dataset_lengths",
      "tests/test_pair_binning.py::TestMassBinEdges::test_default_config_edges_and_lengths",
      "tests/test_pair_binning.py::TestPaths::test_data_path",
      "tests/test_pair_binning.py::TestPaths::test_results_path",
      "tests/test_pair_binning.py::TestPreflightGate::test_empty_conventions_leaves_sentinel_untouched",
      "tests/test_pair_binning.py::TestPreflightGate::test_invalid_conventions_leaves_sentinel_untouched",
      "tests/test_pair_binning.py::TestPreflightGate::test_malformed_redshift_attr_leaves_sentinel_untouched",
      "tests/test_pair_binning.py::TestPreflightGate::test_mismatched_mass_ratio_min_leaves_sentinel_untouched",
      "tests/test_pair_binning.py::TestPreflightGate::test_mismatched_max_sep_kpc_leaves_sentinel_untouched",
      "tests/test_pair_binning.py::TestPreflightGate::test_mismatched_redshift_leaves_sentinel_untouched",
      "tests/test_pair_binning.py::TestPreflightGate::test_missing_data_file_leaves_sentinel_untouched",
      "tests/test_pair_binning.py::TestPreflightGate::test_missing_results_file_leaves_sentinel_untouched",
      "tests/test_pair_binning.py::TestPreflightGate::test_unsupported_convention_name_leaves_sentinel_untouched",
      "tests/test_pair_binning.py::TestRunBinningComparisonMockData::test_additivity_true_on_mock_data",
      "tests/test_pair_binning.py::TestRunBinningComparisonMockData::test_console_summary_content",
      "tests/test_pair_binning.py::TestRunBinningComparisonMockData::test_console_summary_not_checked_in_two_convention_run",
      "tests/test_pair_binning.py::TestRunBinningComparisonMockData::test_conventions_tracks_config_two_entry_run",
      "tests/test_pair_binning.py::TestRunBinningComparisonMockData::test_end_to_end_recomputation_matches_independent_calculation",
      "tests/test_pair_binning.py::TestRunBinningComparisonMockData::test_pair_fraction_uses_same_n_galaxies_row_for_all_conventions",
      "tests/test_pair_binning.py::TestRunBinningComparisonMockData::test_returned_dicts_match_persisted_file",
      "tests/test_pair_binning.py::TestRunBinningComparisonMockData::test_single_redshift_run_matches_full_run",
      "tests/test_pair_binning.py::TestRunBinningComparisonMockData::test_written_file_schema",
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
      "tests/test_
```
