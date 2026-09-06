# Trial report: 20260906T100136Z-002-pair-binning-convention-gpt-5.6-sol-sixth-session-20260906-gpt-5.6-sol-codex-gpt-5.6-sol-3-3bd045

- Task: `002-pair-binning-convention`
- Model: `gpt-5.6-sol` (harness: codex)
- Model duration: 678.9s | venv setup: 26.5s | timed out: False | committed: False
- Changed files: src/config.py, src/pair_binning.py, tests/test_pair_binning.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 93.0 / 100

## Judged: readability 75% of weight, maintainability 50% of weight (judge claude-opus-5, status ok)

## Composite score: 88.6 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 99% |
| test_adequacy | automated | 25 | 77% |
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
  "grader_git_rev": "c694b1064b22a735ff2d76bded64e31ddd49df7e",
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
    "raw_tail": "est_B11_load_snapshot_counts_attr_rejections[override4-mass_ratio_min] PASSED [ 75%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override5-max_sep_kpc] PASSED [ 76%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override6-max_sep_kpc] PASSED [ 77%]\ntests/test_hB.py::test_B12a_load_snapshot_counts_missing_attr[redshift] PASSED [ 77%]\ntests/test_hB.py::test_B12a_load_snapshot_counts_missing_attr[mass_ratio_min] PASSED [ 78%]\ntests/test_hB.py::test_B12a_load_snapshot_counts_missing_attr[max_sep_kpc] PASSED [ 79%]\ntests/test_hB.py::test_B12b_load_snapshot_counts_missing_dataset[mass_primary] PASSED [ 80%]\ntests/test_hB.py::test_B12b_load_snapshot_counts_missing_dataset[mass_secondary] PASSED [ 80%]\ntests/test_hB.py::test_B12c_load_snapshot_counts_length_mismatch PASSED  [ 81%]\ntests/test_hB.py::test_B13_output_schema_on_mock PASSED                  [ 82%]\ntests/test_hB.py::test_B14_returned_dicts_match_persisted PASSED         [ 82%]\ntests/test_hB.py::test_B15_one_denominator_shared_by_every_convention PASSED [ 83%]\ntests/test_hB.py::test_B16_end_to_end_counts_recomputed_independently PASSED [ 84%]\ntests/test_hB.py::test_B17_conventions_config_tracks_through_the_driver PASSED [ 85%]\ntests/test_hB.py::test_B18_single_redshift_run PASSED                    [ 85%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[missing_data-<lambda>-None] PASSED [ 86%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[missing_results-<lambda>-None] PASSED [ 87%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_redshift-None-override2] PASSED [ 87%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_mass_ratio_min-None-override3] PASSED [ 88%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_max_sep-None-override4] PASSED [ 89%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[malformed_redshift-None-override5] PASSED [ 90%]\ntests/test_hB.py::test_B19b_preflight_checks_every_configured_redshift_before_writing PASSED [ 90%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad0] PASSED [ 91%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad1] PASSED [ 92%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad2] PASSED [ 92%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad3] PASSED [ 93%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad4] PASSED [ 94%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[primary] PASSED [ 95%]\ntests/test_hB.py::test_B21_console_summary_fields PASSED                 [ 95%]\ntests/test_hB.py::test_B21b_console_line_selection_is_token_exact_not_substring PASSED [ 96%]\ntests/test_hB.py::test_B22_console_reports_not_checked_for_partial_convention_set PASSED [ 97%]\ntests/test_hB.py::test_B23_provenance_compared_against_config_not_defaults PASSED [ 97%]\ntests/test_hB.py::test_B24_additivity_false_from_check_propagates_everywhere PASSED [ 98%]\ntests/test_hB.py::test_B26_full_driver_run_on_nondefault_bin_grid PASSED [ 99%]\ntests/test_hB.py::test_B27_low_mass_ratio_pair_not_refiltered PASSED     [100%]\n\n=================================== FAILURES ===================================\n__________________ test_A30_check_additivity_exact_above_2_53 __________________\ntests/test_hA.py:476: in test_A30_check_additivity_exact_above_2_53\n    assert PB.check_additivity(big, one, big) is False\nE   assert True is False\nE    +  where True = <function check_additivity at 0x109981f30>(array([9007199254740992]), array([1]), array([9007199254740992]))\nE    +    where <function check_additivity at 0x109981f30> = PB.check_additivity\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A30_check_additivity_exact_above_2_53 - assert ...\n======================== 1 failed, 139 passed in 1.96s =========================\n",
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
      "tests/test_pair_binning.py::TestComparisonDriver::test_generated_data_end_to_end",
      "tests/test_pair_binning.py::TestComparisonDriver::test_invalid_conventions_preserve_output[conventions0]",
      "tests/test_pair_binning.py::TestComparisonDriver::test_invalid_conventions_preserve_output[conventions1]",
      "tests/test_pair_binning.py::TestComparisonDriver::test_invalid_conventions_preserve_output[conventions2]",
      "tests/test_pair_binning.py::TestComparisonDriver::test_invalid_conventions_preserve_output[conventions3]",
      "tests/test_pair_binning.py::TestComparisonDriver::test_invalid_conventions_preserve_output[primary]",
      "tests/test_pair_binning.py::TestComparisonDriver::test_preflight_failure_preserves_output[invalid_conventions-convention]",
      "tests/test_pair_binning.py::TestComparisonDriver::test_preflight_failure_preserves_output[malformed_redshift-numeric scalar]",
      "tests/test_pair_binning.py::TestComparisonDriver::test_preflight_failure_preserves_output[mass_ratio_min-mismatch]",
      "tests/test_pair_binning.py::TestComparisonDriver::test_preflight_failure_preserves_output[max_sep_kpc-mismatch]",
      "tests/test_pair_binning.py::TestComparisonDriver::test_preflight_failure_preserves_output[missing_data-data file]",
      "tests/test_pair_binning.py::TestComparisonDriver::test_preflight_failure_preserves_output[missing_results-results file]",
      "tests/test_pair_binning.py::TestComparisonDriver::test_preflight_failure_preserves_output[redshift-mismatch]",
      "tests/test_pair_binning.py::TestComparisonDriver::test_subset_order_and_single_redshift",
      "tests/test_pair_binning.py::TestComparisonDriver::test_written_schema_return_values_and_summary",
      "tests/test_pair_binning.py::TestCounting::test_config_drives_every_edge_and_count_length",
      "tests/test_pair_binning.py::TestCounting::test_default_edges_and_right_open_galaxy_counts",
      "tests/test_pair_binning.py::TestCounting::test_empty_pair_arrays[either]",
      "tests/test_pair_binning.py::TestCounting::test_empty_pair_arrays[primary]",
      "tests/test_pair_binning.py::TestCounting::test_empty_pair_arrays[secondary]",
      "tests/test_pair_binning.py::TestCounting::test_galaxy_count_ignores_frozen_convention[None]",
      "tests/test_pair_binning.py::TestCounting::test_galaxy_count_ignores_frozen_convention[mean]",
      "tests/test_pair_binning.py::TestCounting::test_galaxy_count_ignores_frozen_convention[nonsense]",
      "tests/test_pair_binning.py::TestCounting::test_galaxy_count_ignores_frozen_convention[primary]",
      "tests/test_pair_binning.py::TestCounting::test_galaxy_count_ignores_frozen_convention[secondary]",
      "tests/test_pair_binning.py::TestCounting::test_galaxy_count_ignores_frozen_convention[total]",
      "tests/test_pair_binning.py::TestCounting::test_galaxy_count_validates_input[values0-1D]",
      "tests/test_pair_binning.py::TestCounting::test_galaxy_count_validates_input[values1-1D real numeric]",
      "tests/test_pair_binning.py::TestCounting::test_galaxy_count_validates_input[values2-non-finite]",
      "tests/test_pair_binning.py::TestCounting::test_galaxy_count_validates_input[values3-real numeric]",
      "tests/test_pair_binning.py::TestCounting::test_galaxy_count_validates_input[values4-real numeric]",
      "tests/test_pair_binning.py::TestCounting::test_pair_counts_exclusions_and_additivity",
      "tests/test_pair_binning.py::TestCounting::test_pair_functions_reject_invalid_conventions[3-count_excluded_pairs]",
      "tests/test_pair_binning.py::TestCounting::test_pair_functions_reject_invalid_conventions[3-count_pairs_per_mass_bin]",
      "tests/test_pair_binning.py::TestCounting::test_pair_functions_reject_invalid_conventions[None-count_excluded_pairs]",
      "tests/test_pair_binning.py::TestCounting::test_pair_functions_reject_invalid_conventions[None-count_pairs_per_mass_bin]",
      "tests/test_pair_binning.py::TestCounting::test_pair_functions_reject_invalid_conventions[mean-count_excluded_pairs]",
      "tests/test_pair_binning.py::TestCounting::test_pair_functions_reject_invalid_conventions[mean-count_pairs_per_mass_bin]",
      "tests/test_pair_binning.py::TestCounting::test_pair_functions_reject_invalid_conventions[total-count_excluded_pairs]",
      "tests/test_pair_binning.py::TestCounting::test_pair_functions_reject_invalid_conventions[total-count_pairs_per_mass_bin]",
      "tests/test_pair_binning.py::TestCounting::test_pair_functions_reject_invalid_conventions[unknown-count_excluded_pairs]",
      "tests/test_pair_binning.py::TestCounting::test_pair_functions_reject_invalid_conventions[unknown-count_pairs_per_mass_bin]",
      "tests/test_pair_binning.py::TestCounting::test_pair_functions_validate_mass_arrays[primary0-secondary0-shapes-count_excluded_pairs]",
      "tests/test_pair_binning.py::TestCounting::test_pair_functions_validate_mass_arrays[primary0-secondary0-shapes-count_pairs_per_mass_bin]",
      "tests/test_pair_binning.py::TestCounting::test_pair_functions_validate_mass_arrays[primary1-secondary1-1D-count_excluded_pairs]",
      "tests/test_pair_binning.py::TestCounting::test_pair_functions_validate_mass_arrays[primary1-secondary1-1D-count_pairs_per_mass_bin]",
      "tests/test_pair_binning.py::TestCounting::test_pair_functions_validate_mass_arrays[primary2-secondary2-non-finite-count_excluded_pairs]",
      "tests/test_pair_binning.py::TestCounting::test_pair_functions_validate_mass_arrays[primary2-secondary2-non-finite-count_pairs_per_mass_bin]",
      "tests/test_pair_binning.py::TestCounting::test_pair_functions_validate_mass_arrays[primary3-secondary3-non-finite-count_excluded_pairs]",
      "tests/test_pair_binning.py::TestCounting::test_pair_functions_validate_mass_arrays[primary3-secondary3-non-finite-count_pairs_per_mass_bin]",
      "tests/test_pair_binning.py::TestCounting::test_pair_functions_validate_mass_arrays[primary4-secondary4-real numeric-count_excluded_pairs]",
      "tests/test_pair_binning.py::TestCounting::test_pair_functions_validate_mass_arrays[primary4-secondary4-real numeric-count_pairs_per_mass_bin]",
      "tests/test_pair_binning.py::TestCounting::test_pair_functions_validate_mass_arrays[primary5-secondary5-real numeric-count_excluded_pairs]",
      "tests/test_pair_binning.py::TestCounting::test_pair_functions_validate_mass_arrays[primary5-secondary5-real numeric-count_pairs_per_mass_bin]",
      "tests/test_pair_binning.py::TestCounting::test_pair_functions_validate_mass_arrays[primary6-secondary6-secondary-count_excluded_pairs]",
      "tests/test_pair_binning.py::TestCounting::test_pair_functions_validate_mass_arrays[primary6-secondary6-secondary-count_pairs_per_mass_bin]",
      "tests/test_pair_binning.py::TestFractionsAndInvariant::test_additivity_true_false_and_zeros",
      "tests/test_pair_binning.py::TestFractionsAndInvariant::test_additivity_validates_counts[primary0-secondary0-either0-1D]",
      "tests/test_pair_binning.py::TestFractionsAndInvariant::test_additivity_validates_counts[primary1-secondary1-either1-shapes]",
      "tests/test_pair_binning.py::TestFractionsAndInvariant::test_additivity_validates_counts[primary2-secondary2-either2-non-finite]",
      "tests/test_pair_binning.py::TestFractionsAndInvariant::test_additivity_validates_counts[primary3-secondary3-either3-negative]",
      "tests/test_pair_binning.py::TestFractionsAndInvariant::test_additivity_validates_counts[primary4-secondary4-either4-integer-valued]",
      "tests/test_pair_binning.py::TestFractionsAndInvariant::test_additivity_validates_counts[primary5-secondary5-either5-real numeric]",
      "tests/test_pair_binning.py::TestFractionsAndInvariant::test_additivity_validates_counts[primary6-secondary6-either6-real numeric]",
      "tests/test_pair_binning.py::TestFractionsAndInvariant::test_fraction_and_plugin_error",
      "tests/test_pair_binning.py::TestFractionsAndInvariant::test_fraction_validates_counts[pairs0-galaxies0-shapes]",
      "tests/test_pair_binning.py::TestFractionsAndInvariant::test_fraction_validates_counts[pairs1-galaxies1-1D]",
      "tests/test_pair_binning.py::TestFractionsAndInvariant::test_fraction_validates_counts[pairs2-galaxies2-negative]",
      "tests/test_pair_binning.py::TestFractionsAndInvariant::test_fraction_validates_counts[pairs3-galaxies3-non-finite]",
      "tests/test_pair_binning.py::TestFractionsAndInvariant::test_fraction_validates_counts[pairs4-galaxies4-integer-valued]",
      "tests/test_pair_binning.py::TestFractionsAndInvariant::test_fraction_validates_counts[pairs5-galaxies5-real numeric]",
      "tests/test_pair_binning.py::TestFractionsAndInvariant::test_fraction_validates_counts[pairs6-galaxies6-real numeric]",
      "tests/test_pair_binning.py::TestFractionsAndInvariant::test_incidence_without_galaxy_rejected",
      "tests/test_pair_binning.py::TestFractionsAndInvariant::test_integer_valued_float_counts_are_valid",
      "tests/test_pair_binning.py::TestFractionsAndInvariant::test_required_either_docstring_warning",
      "tests/test_pair_binning.py::TestFractionsAndInvariant::test_zero_over_zero_is_exactly_zero",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_honours_configured_convention_subset[conventions0]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_honours_configured_convention_subset[conventions1]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_loads_exact_schema_and_independent_counts",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_rejects_invalid_convention_collections[conventions0]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_rejects_invalid_convention_collections[conventions1]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_rejects_invalid_convention_collections[conventions2]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_rejects_invalid_convention_collections[conventions3]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_rejects_invalid_convention_collections[conventions4]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_rejects_invalid_convention_collections[primary]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_rejects_missing_data_path",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_rejects_missing_pair_dataset[mass_primary]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_rejects_missing_pair_dataset[mass_secondary]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_rejects_missing_results_path",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_rejects_unequal_or_non_1d_pair_datasets",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_stored_mass_bin_and_convention_are_ignored",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_validates_results_provenance[mass_ratio_min-0.1-numeric scalar]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_validates_results_provenance[mass_ratio_min-0.2-mismatch]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_validates_results_provenance[mass_ratio_min-None-mass_ratio_min]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_validates_results_provenance[max_sep_kpc-(25+0j)-numeric scalar]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_validates_results_provenance[max_sep_kpc-20.0-mismatch]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_validates_results_provenance[max_sep_kpc-None-max_sep_kpc]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_validates_results_provenance[redshift-2.0-numeric scalar]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_validates_results_provenance[redshift-3.0-mismatch]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_validates_results_provenance[redshift-None-redshift]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_validates_results_provenance[redshift-value9-numeric scalar]",
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
     
```
