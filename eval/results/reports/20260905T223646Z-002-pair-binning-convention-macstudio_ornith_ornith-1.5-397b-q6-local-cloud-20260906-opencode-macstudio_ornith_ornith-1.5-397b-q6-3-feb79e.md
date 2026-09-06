# Trial report: 20260905T223646Z-002-pair-binning-convention-macstudio_ornith_ornith-1.5-397b-q6-local-cloud-20260906-opencode-macstudio_ornith_ornith-1.5-397b-q6-3-feb79e

- Task: `002-pair-binning-convention`
- Model: `macstudio/ornith/ornith-1.5-397b-q6` (harness: opencode)
- Model duration: 5080.9s | venv setup: 41.1s | timed out: False | committed: False
- Changed files: src/config.py, src/pair_binning.py, tests/test_pair_binning.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 85.9 / 100

## Judged: readability 75% of weight, maintainability 75% of weight (judge claude-opus-5, status ok)

## Composite score: 84.3 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 99% |
| test_adequacy | automated | 25 | 65% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 71% |
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
    "passed": 139,
    "failed": [
      "tests/test_hA.py::test_A30_check_additivity_exact_above_2_53"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "est_B11_load_snapshot_counts_attr_rejections[override4-mass_ratio_min] PASSED [ 75%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override5-max_sep_kpc] PASSED [ 76%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override6-max_sep_kpc] PASSED [ 77%]\ntests/test_hB.py::test_B12a_load_snapshot_counts_missing_attr[redshift] PASSED [ 77%]\ntests/test_hB.py::test_B12a_load_snapshot_counts_missing_attr[mass_ratio_min] PASSED [ 78%]\ntests/test_hB.py::test_B12a_load_snapshot_counts_missing_attr[max_sep_kpc] PASSED [ 79%]\ntests/test_hB.py::test_B12b_load_snapshot_counts_missing_dataset[mass_primary] PASSED [ 80%]\ntests/test_hB.py::test_B12b_load_snapshot_counts_missing_dataset[mass_secondary] PASSED [ 80%]\ntests/test_hB.py::test_B12c_load_snapshot_counts_length_mismatch PASSED  [ 81%]\ntests/test_hB.py::test_B13_output_schema_on_mock PASSED                  [ 82%]\ntests/test_hB.py::test_B14_returned_dicts_match_persisted PASSED         [ 82%]\ntests/test_hB.py::test_B15_one_denominator_shared_by_every_convention PASSED [ 83%]\ntests/test_hB.py::test_B16_end_to_end_counts_recomputed_independently PASSED [ 84%]\ntests/test_hB.py::test_B17_conventions_config_tracks_through_the_driver PASSED [ 85%]\ntests/test_hB.py::test_B18_single_redshift_run PASSED                    [ 85%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[missing_data-<lambda>-None] PASSED [ 86%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[missing_results-<lambda>-None] PASSED [ 87%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_redshift-None-override2] PASSED [ 87%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_mass_ratio_min-None-override3] PASSED [ 88%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_max_sep-None-override4] PASSED [ 89%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[malformed_redshift-None-override5] PASSED [ 90%]\ntests/test_hB.py::test_B19b_preflight_checks_every_configured_redshift_before_writing PASSED [ 90%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad0] PASSED [ 91%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad1] PASSED [ 92%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad2] PASSED [ 92%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad3] PASSED [ 93%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad4] PASSED [ 94%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[primary] PASSED [ 95%]\ntests/test_hB.py::test_B21_console_summary_fields PASSED                 [ 95%]\ntests/test_hB.py::test_B21b_console_line_selection_is_token_exact_not_substring PASSED [ 96%]\ntests/test_hB.py::test_B22_console_reports_not_checked_for_partial_convention_set PASSED [ 97%]\ntests/test_hB.py::test_B23_provenance_compared_against_config_not_defaults PASSED [ 97%]\ntests/test_hB.py::test_B24_additivity_false_from_check_propagates_everywhere PASSED [ 98%]\ntests/test_hB.py::test_B26_full_driver_run_on_nondefault_bin_grid PASSED [ 99%]\ntests/test_hB.py::test_B27_low_mass_ratio_pair_not_refiltered PASSED     [100%]\n\n=================================== FAILURES ===================================\n__________________ test_A30_check_additivity_exact_above_2_53 __________________\ntests/test_hA.py:476: in test_A30_check_additivity_exact_above_2_53\n    assert PB.check_additivity(big, one, big) is False\nE   assert True is False\nE    +  where True = <function check_additivity at 0x109b51fe0>(array([9007199254740992]), array([1]), array([9007199254740992]))\nE    +    where <function check_additivity at 0x109b51fe0> = PB.check_additivity\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A30_check_additivity_exact_above_2_53 - assert ...\n======================== 1 failed, 139 passed in 2.58s =========================\n",
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
      "tests/test_pair_binning.py::TestCheckAdditivity::test_false_when_violated_no_raise",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_complex",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_mismatched_shapes",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_negative",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_non_1d",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_non_finite",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_non_integer",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_true_for_all_zero",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_true_when_holds",
      "tests/test_pair_binning.py::TestComputePairFraction::test_accepts_integer_and_integer_valued_float",
      "tests/test_pair_binning.py::TestComputePairFraction::test_algebraically_equivalent_evaluation_order_accepted",
      "tests/test_pair_binning.py::TestComputePairFraction::test_asserts_incidence_without_galaxies",
      "tests/test_pair_binning.py::TestComputePairFraction::test_docstring_contains_required_sentence",
      "tests/test_pair_binning.py::TestComputePairFraction::test_empty_bin_is_exactly_zero_not_nan",
      "tests/test_pair_binning.py::TestComputePairFraction::test_exact_values_with_tight_rtol",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_complex_counts",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_mismatched_shapes",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_negative_counts",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_non_1d",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_non_finite_counts",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_non_integer_counts",
      "tests/test_pair_binning.py::TestComputePairFraction::test_returns_float_arrays_of_input_shape",
      "tests/test_pair_binning.py::TestConfigKey::test_key_added_and_existing_unchanged",
      "tests/test_pair_binning.py::TestConventionTrackingAndSubsets::test_reordered_two_convention_run",
      "tests/test_pair_binning.py::TestConventionTrackingAndSubsets::test_single_redshift_matches_full_run_row",
      "tests/test_pair_binning.py::TestConventionTrackingAndSubsets::test_two_convention_summary_reports_not_checked",
      "tests/test_pair_binning.py::TestCountGalaxies::test_default_sample_exact_counts_and_int_dtype",
      "tests/test_pair_binning.py::TestCountGalaxies::test_edges_and_lengths_from_config_values",
      "tests/test_pair_binning.py::TestCountGalaxies::test_independent_of_mass_bin_by[None]",
      "tests/test_pair_binning.py::TestCountGalaxies::test_independent_of_mass_bin_by[mean]",
      "tests/test_pair_binning.py::TestCountGalaxies::test_independent_of_mass_bin_by[nonsense]",
      "tests/test_pair_binning.py::TestCountGalaxies::test_independent_of_mass_bin_by[primary]",
      "tests/test_pair_binning.py::TestCountGalaxies::test_independent_of_mass_bin_by[secondary]",
      "tests/test_pair_binning.py::TestCountGalaxies::test_independent_of_mass_bin_by[total]",
      "tests/test_pair_binning.py::TestCountGalaxies::test_rejects_complex",
      "tests/test_pair_binning.py::TestCountGalaxies::test_rejects_non_1d",
      "tests/test_pair_binning.py::TestCountGalaxies::test_rejects_non_finite",
      "tests/test_pair_binning.py::TestCountGalaxies::test_rejects_numeric_string_before_coercion",
      "tests/test_pair_binning.py::TestCountPairs::test_both_members_same_bin_counted_twice_under_either",
      "tests/test_pair_binning.py::TestCountPairs::test_excluded_pairs_section7_and_sum_rule",
      "tests/test_pair_binning.py::TestCountPairs::test_rejects_complex",
      "tests/test_pair_binning.py::TestCountPairs::test_rejects_mismatched_shapes",
      "tests/test_pair_binning.py::TestCountPairs::test_rejects_non_1d",
      "tests/test_pair_binning.py::TestCountPairs::test_rejects_non_finite",
      "tests/test_pair_binning.py::TestCountPairs::test_rejects_non_string_convention[3.0]",
      "tests/test_pair_binning.py::TestCountPairs::test_rejects_non_string_convention[5]",
      "tests/test_pair_binning.py::TestCountPairs::test_rejects_non_string_convention[None]",
      "tests/test_pair_binning.py::TestCountPairs::test_rejects_secondary_more_massive_than_primary",
      "tests/test_pair_binning.py::TestCountPairs::test_rejects_unsupported_or_unknown_convention[mean]",
      "tests/test_pair_binning.py::TestCountPairs::test_rejects_unsupported_or_unknown_convention[nonsense]",
      "tests/test_pair_binning.py::TestCountPairs::test_rejects_unsupported_or_unknown_convention[total]",
      "tests/test_pair_binning.py::TestCountPairs::test_rejects_unsupported_or_unknown_convention[unknown]",
      "tests/test_pair_binning.py::TestCountPairs::test_three_conventions_satisfy_section4_and_section7",
      "tests/test_pair_binning.py::TestCountPairs::test_three_vectors_distinct_and_either_not_equal_to_others",
      "tests/test_pair_binning.py::TestCountPairs::test_zero_length_returns_all_zero_vector_no_raise",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsGenerated::test_additivity_and_exclusion_sum_rule_per_redshift",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsGenerated::test_denominator_is_full_selected_catalog_below_inclusive_count",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsGenerated::test_n_pairs_total_matches_results_rows",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsGenerated::test_return_dict_keys_exact",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_invalid_conventions_list[bad0]",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_invalid_conventions_list[bad1]",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_invalid_conventions_list[bad2]",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_invalid_conventions_list[bad3]",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_invalid_conventions_list[bad4]",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_invalid_conventions_list[primary]",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_malformed_bytes_attr",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_malformed_string_attr",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_mass_ratio_min_mismatch",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_max_sep_kpc_mismatch",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_missing_attr",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_missing_data_file",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_missing_mass_primary_dataset",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_missing_results_file",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_non_scalar_vector_attr",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_redshift_mismatch",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_tuple_conventions_is_accepted",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsRejections::test_unequal_dataset_lengths",
      "tests/test_pair_binning.py::TestMassBinEdgesAndPaths::test_default_edges",
      "tests/test_pair_binning.py::TestMassBinEdgesAndPaths::test_edges_derived_from_config_not_defaults",
      "tests/test_pair_binning.py::TestMassBinEdgesAndPaths::test_paths_match_calc_layout",
      "tests/test_pair_binning.py::TestPerConventionCountsVary::test_hand_written_fixture_counts_match_manual",
      "tests/test_pair_binning.py::TestPerConventionCountsVary::test_honours_single_and_two_entry_convention_lists",
      "tests/test_pair_binning.py::TestPreflightSentinelProtection::test_sentinel_unchanged_on_failure[bad_mr]",
      "tests/test_pair_binning.py::TestPreflightSentinelProtection::test_sentinel_unchanged_on_failure[bad_redshift]",
      "tests/test_pair_binning.py::TestPreflightSentinelProtection::test_sentinel_unchanged_on_failure[bad_sep]",
      "tests/test_pair_binning.py::TestPreflightSentinelProtection::test_sentinel_unchanged_on_failure[dup_conv]",
      "tests/test_pair_binning.py::TestPreflightSentinelProtection::test_sentinel_unchanged_on_failure[empty_conv]",
      "tests/test_pair_binning.py::TestPreflightSentinelProtection::test_sentinel_unchanged_on_failure[malformed_redshift]",
      "tests/test_pair_binning.py::TestPreflightSentinelProtection::test_sentinel_unchanged_on_failure[missing_data]",
      "tests/test_pair_binning.py::TestPreflightSentinelProtection::test_sentinel_unchanged_on_failure[missing_results]",
      "tests/test_pair_binning.py::TestPreflightSentinelProtection::test_sentinel_unchanged_on_failure[nonstr_conv]",
      "tests/test_pair_binning.py::TestPreflightSentinelProtection::test_sentinel_unchanged_on_failure[notlist_conv]",
      "tests/test_pair_binning.py::TestPreflightSentinelProtection::test_sentinel_unchanged_on_failure[unsup_conv]",
      "tests/test_pair_binning.py::TestRunGenerated::test_additivity_flags_on_generated_data",
      "tests/test_pair_binning.py::TestRunGenerated::test_console_summary_tokens_and_heading",
      "tests/test_pair_binning.py::TestRunGenerated::test_end_to_end_independent_recompute",
      "tests/test_pair_binning.py::TestRunGenerated::test_file_schema_shapes_dtypes_and_ordering",
      "tests/test_pair_binning.py::TestRunGenerated::test_persisted_fraction_is_npairs_over_same_ngal_row",
      "tests/test_pair_binning.py::TestRunGenerated::test_persisted_matches_returned_dicts_and_seven_keys",
      "tests/test_pair_binning.py::TestStoredAssignmentNotUsed::test_overwritten_mass_bin_and_total_attr_do_not_change_counts",
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
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_
```
