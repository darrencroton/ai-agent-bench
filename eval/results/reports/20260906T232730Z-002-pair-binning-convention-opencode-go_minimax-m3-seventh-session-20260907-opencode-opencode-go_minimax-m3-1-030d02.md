# Trial report: 20260906T232730Z-002-pair-binning-convention-opencode-go_minimax-m3-seventh-session-20260907-opencode-opencode-go_minimax-m3-1-030d02

- Task: `002-pair-binning-convention`
- Model: `opencode-go/minimax-m3` (harness: opencode)
- Model duration: 1031.6s | venv setup: 27.5s | timed out: False | committed: False
- Changed files: src/config.py, src/pair_binning.py, tests/test_pair_binning.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 90.7 / 100

## Judged: readability 50% of weight, maintainability 25% of weight (judge claude-opus-5, status ok)

## Composite score: 82.9 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 100% |
| test_adequacy | automated | 25 | 72% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 91% |
| readability | judged | 8 | 50% |
| maintainability | judged | 7 | 25% |

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
    "raw_tail": "y::test_B10_load_snapshot_counts_file_rejections[missing_data] PASSED [ 70%]\ntests/test_hB.py::test_B10_load_snapshot_counts_file_rejections[missing_results] PASSED [ 71%]\ntests/test_hB.py::test_B10_load_snapshot_counts_file_rejections[wrong_redshift] PASSED [ 72%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override0-redshift] PASSED [ 72%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override1-redshift] PASSED [ 73%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override2-redshift] PASSED [ 74%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override3-mass_ratio_min] PASSED [ 75%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override4-mass_ratio_min] PASSED [ 75%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override5-max_sep_kpc] PASSED [ 76%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override6-max_sep_kpc] PASSED [ 77%]\ntests/test_hB.py::test_B12a_load_snapshot_counts_missing_attr[redshift] PASSED [ 77%]\ntests/test_hB.py::test_B12a_load_snapshot_counts_missing_attr[mass_ratio_min] PASSED [ 78%]\ntests/test_hB.py::test_B12a_load_snapshot_counts_missing_attr[max_sep_kpc] PASSED [ 79%]\ntests/test_hB.py::test_B12b_load_snapshot_counts_missing_dataset[mass_primary] PASSED [ 80%]\ntests/test_hB.py::test_B12b_load_snapshot_counts_missing_dataset[mass_secondary] PASSED [ 80%]\ntests/test_hB.py::test_B12c_load_snapshot_counts_length_mismatch PASSED  [ 81%]\ntests/test_hB.py::test_B13_output_schema_on_mock PASSED                  [ 82%]\ntests/test_hB.py::test_B14_returned_dicts_match_persisted PASSED         [ 82%]\ntests/test_hB.py::test_B15_one_denominator_shared_by_every_convention PASSED [ 83%]\ntests/test_hB.py::test_B16_end_to_end_counts_recomputed_independently PASSED [ 84%]\ntests/test_hB.py::test_B17_conventions_config_tracks_through_the_driver PASSED [ 85%]\ntests/test_hB.py::test_B18_single_redshift_run PASSED                    [ 85%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[missing_data-<lambda>-None] PASSED [ 86%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[missing_results-<lambda>-None] PASSED [ 87%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_redshift-None-override2] PASSED [ 87%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_mass_ratio_min-None-override3] PASSED [ 88%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_max_sep-None-override4] PASSED [ 89%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[malformed_redshift-None-override5] PASSED [ 90%]\ntests/test_hB.py::test_B19b_preflight_checks_every_configured_redshift_before_writing PASSED [ 90%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad0] PASSED [ 91%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad1] PASSED [ 92%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad2] PASSED [ 92%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad3] PASSED [ 93%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad4] PASSED [ 94%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[primary] PASSED [ 95%]\ntests/test_hB.py::test_B21_console_summary_fields PASSED                 [ 95%]\ntests/test_hB.py::test_B21b_console_line_selection_is_token_exact_not_substring PASSED [ 96%]\ntests/test_hB.py::test_B22_console_reports_not_checked_for_partial_convention_set PASSED [ 97%]\ntests/test_hB.py::test_B23_provenance_compared_against_config_not_defaults PASSED [ 97%]\ntests/test_hB.py::test_B24_additivity_false_from_check_propagates_everywhere PASSED [ 98%]\ntests/test_hB.py::test_B26_full_driver_run_on_nondefault_bin_grid PASSED [ 99%]\ntests/test_hB.py::test_B27_low_mass_ratio_pair_not_refiltered PASSED     [100%]\n\n============================= 140 passed in 2.04s ==============================\n",
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
      "tests/test_pair_binning.py::TestCheckAdditivity::test_all_zero_holds_true",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_holds_true",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_invalid_input[bad_a0-bad_b0-bad_c0-1D]",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_invalid_input[bad_a1-bad_b1-bad_c1-[Ss]hape]",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_invalid_input[bad_a2-bad_b2-bad_c2-non-finite]",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_invalid_input[bad_a3-bad_b3-bad_c3-negative]",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_invalid_input[bad_a4-bad_b4-bad_c4-non-integer]",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_invalid_input[bad_a5-bad_b5-bad_c5-complex]",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_violation_returns_false",
      "tests/test_pair_binning.py::TestComputePairFraction::test_accepts_integer_and_float_dtypes",
      "tests/test_pair_binning.py::TestComputePairFraction::test_default_example",
      "tests/test_pair_binning.py::TestComputePairFraction::test_docstring_contains_caveat",
      "tests/test_pair_binning.py::TestComputePairFraction::test_pair_without_galaxies_asserts",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_invalid_input[bad_p0-bad_g0-1D]",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_invalid_input[bad_p1-bad_g1-[Ss]hape]",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_invalid_input[bad_p2-bad_g2-negative]",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_invalid_input[bad_p3-bad_g3-non-finite]",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_invalid_input[bad_p4-bad_g4-non-integer]",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_invalid_input[bad_p5-bad_g5-complex]",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_invalid_input[bad_p6-bad_g6-bool]",
      "tests/test_pair_binning.py::TestComputePairFraction::test_zero_zero_yields_zero_not_nan",
      "tests/test_pair_binning.py::TestConfigKey::test_default_value",
      "tests/test_pair_binning.py::TestConfigKey::test_existing_keys_unchanged",
      "tests/test_pair_binning.py::TestConfigKey::test_pair_binning_conventions_added",
      "tests/test_pair_binning.py::TestConsoleSummary::test_summary_heading_and_tokens",
      "tests/test_pair_binning.py::TestConsoleSummary::test_summary_not_checked_in_two_convention_run",
      "tests/test_pair_binning.py::TestConventionsTracking::test_two_convention_counts_match_three_convention_counts",
      "tests/test_pair_binning.py::TestConventionsTracking::test_two_conventions",
      "tests/test_pair_binning.py::TestCountGalaxies::test_default_config_default_values",
      "tests/test_pair_binning.py::TestCountGalaxies::test_independent_of_mass_bin_by",
      "tests/test_pair_binning.py::TestCountPairsSample::test_additivity_identity_holds",
      "tests/test_pair_binning.py::TestCountPairsSample::test_count_vectors_are_distinct",
      "tests/test_pair_binning.py::TestCountPairsSample::test_counts_match_hand_computation",
      "tests/test_pair_binning.py::TestCountPairsSample::test_excluded_counts_match_hand_computation",
      "tests/test_pair_binning.py::TestCountPairsSample::test_exclusion_sum_rule_primary_secondary",
      "tests/test_pair_binning.py::TestCountPairsSample::test_same_bin_and_different_bin_pairs",
      "tests/test_pair_binning.py::TestCountPairsSample::test_zero_length_arrays",
      "tests/test_pair_binning.py::TestEndToEndMock::test_e2e_counts_match_independent_recomputation",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsAgree::test_additivity_holds_on_mock_data[2.0]",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsAgree::test_additivity_holds_on_mock_data[3.0]",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsAgree::test_additivity_holds_on_mock_data[4.0]",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsAgree::test_additivity_holds_on_mock_data[5.0]",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsAgree::test_exclusion_sum_rule_on_mock_data[2.0]",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsAgree::test_exclusion_sum_rule_on_mock_data[3.0]",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsAgree::test_exclusion_sum_rule_on_mock_data[4.0]",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsAgree::test_exclusion_sum_rule_on_mock_data[5.0]",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsAgree::test_sum_n_galaxies_matches_catalog_strict_lt",
      "tests/test_pair_binning.py::TestLoadSnapshotHonoursConventionsList::test_single_entry",
      "tests/test_pair_binning.py::TestLoadSnapshotHonoursConventionsList::test_two_entries_order_preserved",
      "tests/test_pair_binning.py::TestLoadSnapshotRejections::test_bool_redshift_attr_rejected",
      "tests/test_pair_binning.py::TestLoadSnapshotRejections::test_invalid_conventions_rejected[None-list or tuple]",
      "tests/test_pair_binning.py::TestLoadSnapshotRejections::test_invalid_conventions_rejected[bad_conv0-non-empty]",
      "tests/test_pair_binning.py::TestLoadSnapshotRejections::test_invalid_conventions_rejected[bad_conv1-duplicates]",
      "tests/test_pair_binning.py::TestLoadSnapshotRejections::test_invalid_conventions_rejected[bad_conv2-unsupported]",
      "tests/test_pair_binning.py::TestLoadSnapshotRejections::test_invalid_conventions_rejected[bad_conv3-unsupported]",
      "tests/test_pair_binning.py::TestLoadSnapshotRejections::test_invalid_conventions_rejected[bad_conv4-string]",
      "tests/test_pair_binning.py::TestLoadSnapshotRejections::test_invalid_conventions_rejected[primary-list or tuple]",
      "tests/test_pair_binning.py::TestLoadSnapshotRejections::test_malformed_redshift_attr_rejected",
      "tests/test_pair_binning.py::TestLoadSnapshotRejections::test_mismatched_mass_ratio_min_attr_rejected",
      "tests/test_pair_binning.py::TestLoadSnapshotRejections::test_mismatched_max_sep_attr_rejected",
      "tests/test_pair_binning.py::TestLoadSnapshotRejections::test_mismatched_redshift_attr_rejected",
      "tests/test_pair_binning.py::TestLoadSnapshotRejections::test_missing_data_file_rejected",
      "tests/test_pair_binning.py::TestLoadSnapshotRejections::test_missing_mass_primary_dataset_rejected",
      "tests/test_pair_binning.py::TestLoadSnapshotRejections::test_missing_results_file_rejected",
      "tests/test_pair_binning.py::TestLoadSnapshotRejections::test_vector_redshift_attr_rejected",
      "tests/test_pair_binning.py::TestLoadSnapshotStructure::test_n_galaxies_has_no_convention_axis",
      "tests/test_pair_binning.py::TestLoadSnapshotStructure::test_n_pairs_and_n_excluded_keyed_by_conventions",
      "tests/test_pair_binning.py::TestLoadSnapshotStructure::test_n_pairs_total_equals_mass_primary_length",
      "tests/test_pair_binning.py::TestLoadSnapshotStructure::test_redshift_value",
      "tests/test_pair_binning.py::TestLoadSnapshotStructure::test_returns_exactly_five_keys",
      "tests/test_pair_binning.py::TestMassBinEdges::test_custom_bin_edges",
      "tests/test_pair_binning.py::TestMassBinEdges::test_default_bin_edges",
      "tests/test_pair_binning.py::TestMassBinEdges::test_galaxies_count_custom_config",
      "tests/test_pair_binning.py::TestPerConventionCountsVary::test_secondary_and_either_differ_from_primary",
      "tests/test_pair_binning.py::TestPreflightGatePreservesSentinel::test_invalid_conventions_leaves_sentinel_unchanged[bad_conv0]",
      "tests/test_pair_binning.py::TestPreflightGatePreservesSentinel::test_invalid_conventions_leaves_sentinel_unchanged[bad_conv1]",
      "tests/test_pair_binning.py::TestPreflightGatePreservesSentinel::test_invalid_conventions_leaves_sentinel_unchanged[bad_conv2]",
      "tests/test_pair_binning.py::TestPreflightGatePreservesSentinel::test_invalid_conventions_leaves_sentinel_unchanged[bad_conv3]",
      "tests/test_pair_binning.py::TestPreflightGatePreservesSentinel::test_invalid_conventions_leaves_sentinel_unchanged[primary]",
      "tests/test_pair_binning.py::TestPreflightGatePreservesSentinel::test_malformed_redshift_attr",
      "tests/test_pair_binning.py::TestPreflightGatePreservesSentinel::test_mismatched_mass_ratio_min",
      "tests/test_pair_binning.py::TestPreflightGatePreservesSentinel::test_mismatched_max_sep",
      "tests/test_pair_binning.py::TestPreflightGatePreservesSentinel::test_mismatched_redshift",
      "tests/test_pair_binning.py::TestPreflightGatePreservesSentinel::test_missing_data_file",
      "tests/test_pair_binning.py::TestPreflightGatePreservesSentinel::test_missing_results_file",
      "tests/test_pair_binning.py::TestRejectionsCountGalaxies::test_rejects_invalid_mass_array[bad0]",
      "tests/test_pair_binning.py::TestRejectionsCountGalaxies::test_rejects_invalid_mass_array[bad1]",
      "tests/test_pair_binning.py::TestRejectionsCountGalaxies::test_rejects_invalid_mass_array[bad2]",
      "tests/test_pair_binning.py::TestRejectionsCountGalaxies::test_rejects_invalid_mass_array[bad3]",
      "tests/test_pair_binning.py::TestRejectionsCountGalaxies::test_rejects_invalid_mass_array[bad4]",
      "tests/test_pair_binning.py::TestRejectionsCountPairs::test_rejects_complex_masses",
      "tests/test_pair_binning.py::TestRejectionsCountPairs::test_rejects_mismatched_shapes",
      "tests/test_pair_binning.py::TestRejectionsCountPairs::test_rejects_non_1d_input",
      "tests/test_pair_binning.py::TestRejectionsCountPairs::test_rejects_non_finite_masses",
      "tests/test_pair_binning.py::TestRejectionsCountPairs::test_rejects_non_string_convention[5.0]",
      "tests/test_pair_binning.py::TestRejectionsCountPairs::test_rejects_non_string_convention[5]",
      "tests/test_pair_binning.py::TestRejectionsCountPairs::test_rejects_non_string_convention[None]",
      "tests/test_pair_binning.py::TestRejectionsCountPairs::test_rejects_non_string_convention[bad_conv3]",
      "tests/test_pair_binning.py::TestRejectionsCountPairs::test_rejects_non_string_convention[bad_conv4]",
      "tests/test_pair_binning.py::TestRejectionsCountPairs::test_rejects_non_string_convention[primary]",
      "tests/test_pair_binning.py::TestRejectionsCountPairs::test_rejects_secondary_greater_than_primary",
      "tests/test_pair_binning.py::TestRejectionsCountPairs::test_rejects_unknown_string_convention[]",
      "tests/test_pair_binning.py::TestRejectionsCountPairs::test_rejects_unknown_string_convention[mean]",
      "tests/test_pair_binning.py::TestRejectionsCountPairs::test_rejects_unknown_string_convention[nonsense]",
      "tests/test_pair_binning.py::TestRejectionsCountPairs::test_rejects_unknown_string_convention[total]",
      "tests/test_pair_binning.py::TestReturnValueShape::test_additivity_true_on_mock_data",
      "tests/test_pair_binning.py::TestReturnValueShape::test_pair_fraction_equals_n_pairs_over_n_galaxies",
      "tests/test_pair_binning.py::TestReturnValueShape::test_persisted_equals_returned",
      "tests/test_pair_binning.py::TestReturnValueShape::test_returned_dicts_have_exactly_seven_keys",
      "tests/test_pair_binning.py::TestRunBinningComparisonSchema::test_pair_fraction_finite_nonneg",
      "tests/test_pair_binning.py::TestRunBinningComparisonSchema::test_schema",
      "tests/test_pair_binning.py::TestSingleRedshift::test_single_redshift_run",
      "tests/test_pair_binning.py::TestStoredBinAssignmentNotUsed::test_overwriting_mass_bin_and_attr_does_not_change_output",
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
      "tests/test_pair_finder.py::TestPeriodicBoundary::test_pair_across_b
```
