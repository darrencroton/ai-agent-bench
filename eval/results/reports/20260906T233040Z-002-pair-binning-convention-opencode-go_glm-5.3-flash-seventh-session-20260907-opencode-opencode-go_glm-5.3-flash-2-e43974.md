# Trial report: 20260906T233040Z-002-pair-binning-convention-opencode-go_glm-5.3-flash-seventh-session-20260907-opencode-opencode-go_glm-5.3-flash-2-e43974

- Task: `002-pair-binning-convention`
- Model: `opencode-go/glm-5.3-flash` (harness: opencode)
- Model duration: 780.2s | venv setup: 30.1s | timed out: False | committed: False
- Changed files: src/config.py, src/pair_binning.py, tests/test_pair_binning.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 94.6 / 100

## Judged: readability 75% of weight, maintainability 75% of weight (judge claude-opus-5, status ok)

## Composite score: 91.7 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 99% |
| test_adequacy | automated | 25 | 83% |
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
    "raw_tail": "est_B11_load_snapshot_counts_attr_rejections[override4-mass_ratio_min] PASSED [ 75%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override5-max_sep_kpc] PASSED [ 76%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override6-max_sep_kpc] PASSED [ 77%]\ntests/test_hB.py::test_B12a_load_snapshot_counts_missing_attr[redshift] PASSED [ 77%]\ntests/test_hB.py::test_B12a_load_snapshot_counts_missing_attr[mass_ratio_min] PASSED [ 78%]\ntests/test_hB.py::test_B12a_load_snapshot_counts_missing_attr[max_sep_kpc] PASSED [ 79%]\ntests/test_hB.py::test_B12b_load_snapshot_counts_missing_dataset[mass_primary] PASSED [ 80%]\ntests/test_hB.py::test_B12b_load_snapshot_counts_missing_dataset[mass_secondary] PASSED [ 80%]\ntests/test_hB.py::test_B12c_load_snapshot_counts_length_mismatch PASSED  [ 81%]\ntests/test_hB.py::test_B13_output_schema_on_mock PASSED                  [ 82%]\ntests/test_hB.py::test_B14_returned_dicts_match_persisted PASSED         [ 82%]\ntests/test_hB.py::test_B15_one_denominator_shared_by_every_convention PASSED [ 83%]\ntests/test_hB.py::test_B16_end_to_end_counts_recomputed_independently PASSED [ 84%]\ntests/test_hB.py::test_B17_conventions_config_tracks_through_the_driver PASSED [ 85%]\ntests/test_hB.py::test_B18_single_redshift_run PASSED                    [ 85%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[missing_data-<lambda>-None] PASSED [ 86%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[missing_results-<lambda>-None] PASSED [ 87%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_redshift-None-override2] PASSED [ 87%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_mass_ratio_min-None-override3] PASSED [ 88%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_max_sep-None-override4] PASSED [ 89%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[malformed_redshift-None-override5] PASSED [ 90%]\ntests/test_hB.py::test_B19b_preflight_checks_every_configured_redshift_before_writing PASSED [ 90%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad0] PASSED [ 91%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad1] PASSED [ 92%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad2] PASSED [ 92%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad3] PASSED [ 93%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad4] PASSED [ 94%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[primary] PASSED [ 95%]\ntests/test_hB.py::test_B21_console_summary_fields PASSED                 [ 95%]\ntests/test_hB.py::test_B21b_console_line_selection_is_token_exact_not_substring PASSED [ 96%]\ntests/test_hB.py::test_B22_console_reports_not_checked_for_partial_convention_set PASSED [ 97%]\ntests/test_hB.py::test_B23_provenance_compared_against_config_not_defaults PASSED [ 97%]\ntests/test_hB.py::test_B24_additivity_false_from_check_propagates_everywhere PASSED [ 98%]\ntests/test_hB.py::test_B26_full_driver_run_on_nondefault_bin_grid PASSED [ 99%]\ntests/test_hB.py::test_B27_low_mass_ratio_pair_not_refiltered PASSED     [100%]\n\n=================================== FAILURES ===================================\n__________________ test_A30_check_additivity_exact_above_2_53 __________________\ntests/test_hA.py:476: in test_A30_check_additivity_exact_above_2_53\n    assert PB.check_additivity(big, one, big) is False\nE   assert True is False\nE    +  where True = <function check_additivity at 0x10bb562a0>(array([9007199254740992]), array([1]), array([9007199254740992]))\nE    +    where <function check_additivity at 0x10bb562a0> = PB.check_additivity\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A30_check_additivity_exact_above_2_53 - assert ...\n======================== 1 failed, 139 passed in 1.86s =========================\n",
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
      "tests/test_pair_binning.py::TestCheckAdditivity::test_holds_and_violates",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_complex_and_non_real",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_mismatched_shapes",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_negative",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_non_1d",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_non_finite",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_non_integer_valued",
      "tests/test_pair_binning.py::TestComputePairFraction::test_accepts_integer_and_integer_valued_float64",
      "tests/test_pair_binning.py::TestComputePairFraction::test_docstring_exact_sentence",
      "tests/test_pair_binning.py::TestComputePairFraction::test_reference_values",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_complex_and_non_real",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_mismatched_shapes",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_negative",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_non_1d",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_non_finite",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_non_integer_valued",
      "tests/test_pair_binning.py::TestComputePairFraction::test_requires_galaxies_where_pairs_exist",
      "tests/test_pair_binning.py::TestComputePairFraction::test_zero_pairs_path_exact_zeros[n_pairs0-n_galaxies0]",
      "tests/test_pair_binning.py::TestComputePairFraction::test_zero_pairs_path_exact_zeros[n_pairs1-n_galaxies1]",
      "tests/test_pair_binning.py::TestComputePairFraction::test_zero_pairs_zero_galaxies_exact_zeros",
      "tests/test_pair_binning.py::TestConfigKey::test_new_key_added_and_existing_keys_unchanged",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_convention_independent_with_key[mean]",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_convention_independent_with_key[nonsense]",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_convention_independent_with_key[primary]",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_convention_independent_with_key[secondary]",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_convention_independent_with_key[total]",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_convention_independent_without_key",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_default_config_binning",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_edges_and_counts_from_config",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_rejects_complex_and_non_numeric",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_rejects_non_1d",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_rejects_non_finite",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_rejects_bad_convention[3.5]",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_rejects_bad_convention[42]",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_rejects_bad_convention[None]",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_rejects_bad_convention[]",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_rejects_bad_convention[mean]",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_rejects_bad_convention[nonsense]",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_rejects_bad_convention[primary]",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_rejects_bad_convention[total]",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_zero_length_pairs[either]",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_zero_length_pairs[primary]",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_zero_length_pairs[secondary]",
      "tests/test_pair_binning.py::TestEndToEnd::test_recomputation_from_files",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_additivity_and_exclusion_on_mock",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_convention_counts_vary_on_handwritten_fixture",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_galaxy_at_log_mass_max_excluded",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_honours_single_and_two_entry_convention_lists",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_keys_exact_on_mock",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_n_galaxies_from_full_mass_selected_catalog",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_n_pairs_total_equals_dataset_rows",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_invalid_convention_list[42]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_invalid_convention_list[None]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_invalid_convention_list[bad0]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_invalid_convention_list[bad1]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_invalid_convention_list[bad2]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_invalid_convention_list[bad3]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_invalid_convention_list[bad4]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_invalid_convention_list[bad5]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_invalid_convention_list[primary]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_malformed_attr[(2+0j)-mass_ratio_min]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_malformed_attr[(2+0j)-max_sep_kpc]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_malformed_attr[(2+0j)-redshift]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_malformed_attr[2.0_0-mass_ratio_min]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_malformed_attr[2.0_0-max_sep_kpc]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_malformed_attr[2.0_0-redshift]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_malformed_attr[2.0_1-mass_ratio_min]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_malformed_attr[2.0_1-max_sep_kpc]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_malformed_attr[2.0_1-redshift]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_malformed_attr[bad_value3-mass_ratio_min]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_malformed_attr[bad_value3-max_sep_kpc]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_malformed_attr[bad_value3-redshift]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_malformed_attr[bad_value4-mass_ratio_min]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_malformed_attr[bad_value4-max_sep_kpc]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_malformed_attr[bad_value4-redshift]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_mismatched_attr[mass_ratio_min-0.5]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_mismatched_attr[max_sep_kpc-30.0]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_mismatched_attr[redshift-9.9]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_missing_attr[mass_ratio_min]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_missing_attr[max_sep_kpc]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_missing_attr[redshift]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_missing_data_file",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_missing_mass_primary_dataset",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_missing_mass_secondary_dataset",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_missing_results_file",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_unequal_dataset_lengths",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_stored_mass_bin_and_attr_not_used",
      "tests/test_pair_binning.py::TestRunBinningComparisonPreflight::test_invalid_conventions_leave_sentinel[bad0]",
      "tests/test_pair_binning.py::TestRunBinningComparisonPreflight::test_invalid_conventions_leave_sentinel[bad1]",
      "tests/test_pair_binning.py::TestRunBinningComparisonPreflight::test_invalid_conventions_leave_sentinel[bad2]",
      "tests/test_pair_binning.py::TestRunBinningComparisonPreflight::test_invalid_conventions_leave_sentinel[bad3]",
      "tests/test_pair_binning.py::TestRunBinningComparisonPreflight::test_invalid_conventions_leave_sentinel[primary]",
      "tests/test_pair_binning.py::TestRunBinningComparisonPreflight::test_malformed_redshift_attr_leaves_sentinel[(2+0j)]",
      "tests/test_pair_binning.py::TestRunBinningComparisonPreflight::test_malformed_redshift_attr_leaves_sentinel[2.0_0]",
      "tests/test_pair_binning.py::TestRunBinningComparisonPreflight::test_malformed_redshift_attr_leaves_sentinel[2.0_1]",
      "tests/test_pair_binning.py::TestRunBinningComparisonPreflight::test_malformed_redshift_attr_leaves_sentinel[bad3]",
      "tests/test_pair_binning.py::TestRunBinningComparisonPreflight::test_mismatched_mass_ratio_min_leaves_sentinel",
      "tests/test_pair_binning.py::TestRunBinningComparisonPreflight::test_mismatched_max_sep_kpc_leaves_sentinel",
      "tests/test_pair_binning.py::TestRunBinningComparisonPreflight::test_mismatched_redshift_leaves_sentinel",
      "tests/test_pair_binning.py::TestRunBinningComparisonPreflight::test_missing_data_file_leaves_sentinel",
      "tests/test_pair_binning.py::TestRunBinningComparisonPreflight::test_missing_results_file_leaves_sentinel",
      "tests/test_pair_binning.py::TestRunBinningComparisonSchema::test_additivity_flags_on_mock",
      "tests/test_pair_binning.py::TestRunBinningComparisonSchema::test_conventions_track_config",
      "tests/test_pair_binning.py::TestRunBinningComparisonSchema::test_output_schema_and_persisted_vs_returned",
      "tests/test_pair_binning.py::TestRunBinningComparisonSchema::test_persisted_fraction_matches_counts",
      "tests/test_pair_binning.py::TestRunBinningComparisonSchema::test_single_redshift_matches_full_run_row",
      "tests/test_pair_binning.py::TestRunBinningComparisonSummary::test_console_summary_three_conventions",
      "tests/test_pair_binning.py::TestRunBinningComparisonSummary::test_console_summary_two_conventions",
      "tests/test_pair_binning.py::TestSampleCounts::test_additivity_on_sample_vectors",
      "tests/test_pair_binning.py::TestSampleCounts::test_either_breaks_exclusion_sum_rule_by_two_incidences",
      "tests/test_pair_binning.py::TestSampleCounts::test_excluded_pairs_sample",
      "tests/test_pair_binning.py::TestSampleCounts::test_exclusion_sum_rule_single_member_conventions",
      "tests/test_pair_binning.py::TestSampleCounts::test_rejects_complex_and_non_real[either]",
      "tests/test_pair_binning.py::TestSampleCounts::test_rejects_complex_and_non_real[primary]",
      "tests/test_pair_binning.py::TestSampleCounts::test_rejects_complex_and_non_real[secondary]",
      "tests/test_pair_binning.py::TestSampleCounts::test_rejects_mismatched_shapes",
      "tests/test_pair_binning.py::TestSampleCounts::test_rejects_non_1d[either]",
      "tests/test_pair_binning.py::TestSampleCounts::test_rejects_non_1d[primary]",
      "tests/test_pair_binning.py::TestSampleCounts::test_rejects_non_1d[secondary]",
      "tests/test_pair_binning.py::TestSampleCounts::test_rejects_non_finite[either]",
      "tests/test_pair_binning.py::TestSampleCounts::test_rejects_non_finite[primary]",
      "tests/test_pair_binning.py::TestSampleCounts::test_rejects_non_finite[secondary]",
      "tests/test_pair_binning.py::TestSampleCounts::test_rejects_secondary_gt_primary",
      "tests/test_pair_binning.py::TestSampleCounts::test_same_bin_and_cross_bin_pairs",
      "tests/test_pair_binning.py::TestSampleCounts::test_sample_all_conventions",
      "tests/test_pair_finder.py::TestBasicPairRecovery::test_empty_catalog_returns_empty",
      "tests/test_pair_finder.py::TestBasicPairRecovery::test_no_do
```
