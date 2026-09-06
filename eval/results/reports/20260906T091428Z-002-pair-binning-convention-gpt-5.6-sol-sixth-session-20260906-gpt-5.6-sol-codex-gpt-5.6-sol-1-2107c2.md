# Trial report: 20260906T091428Z-002-pair-binning-convention-gpt-5.6-sol-sixth-session-20260906-gpt-5.6-sol-codex-gpt-5.6-sol-1-2107c2

- Task: `002-pair-binning-convention`
- Model: `gpt-5.6-sol` (harness: codex)
- Model duration: 808.7s | venv setup: 29.3s | timed out: False | committed: False
- Changed files: src/config.py, src/pair_binning.py, tests/test_pair_binning.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 93.6 / 100

## Judged: readability 75% of weight, maintainability 75% of weight (judge claude-opus-5, status ok)

## Composite score: 90.8 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 100% |
| test_adequacy | automated | 25 | 78% |
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
    "passed": 140,
    "failed": [],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "y::test_B10_load_snapshot_counts_file_rejections[missing_data] PASSED [ 70%]\ntests/test_hB.py::test_B10_load_snapshot_counts_file_rejections[missing_results] PASSED [ 71%]\ntests/test_hB.py::test_B10_load_snapshot_counts_file_rejections[wrong_redshift] PASSED [ 72%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override0-redshift] PASSED [ 72%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override1-redshift] PASSED [ 73%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override2-redshift] PASSED [ 74%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override3-mass_ratio_min] PASSED [ 75%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override4-mass_ratio_min] PASSED [ 75%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override5-max_sep_kpc] PASSED [ 76%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override6-max_sep_kpc] PASSED [ 77%]\ntests/test_hB.py::test_B12a_load_snapshot_counts_missing_attr[redshift] PASSED [ 77%]\ntests/test_hB.py::test_B12a_load_snapshot_counts_missing_attr[mass_ratio_min] PASSED [ 78%]\ntests/test_hB.py::test_B12a_load_snapshot_counts_missing_attr[max_sep_kpc] PASSED [ 79%]\ntests/test_hB.py::test_B12b_load_snapshot_counts_missing_dataset[mass_primary] PASSED [ 80%]\ntests/test_hB.py::test_B12b_load_snapshot_counts_missing_dataset[mass_secondary] PASSED [ 80%]\ntests/test_hB.py::test_B12c_load_snapshot_counts_length_mismatch PASSED  [ 81%]\ntests/test_hB.py::test_B13_output_schema_on_mock PASSED                  [ 82%]\ntests/test_hB.py::test_B14_returned_dicts_match_persisted PASSED         [ 82%]\ntests/test_hB.py::test_B15_one_denominator_shared_by_every_convention PASSED [ 83%]\ntests/test_hB.py::test_B16_end_to_end_counts_recomputed_independently PASSED [ 84%]\ntests/test_hB.py::test_B17_conventions_config_tracks_through_the_driver PASSED [ 85%]\ntests/test_hB.py::test_B18_single_redshift_run PASSED                    [ 85%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[missing_data-<lambda>-None] PASSED [ 86%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[missing_results-<lambda>-None] PASSED [ 87%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_redshift-None-override2] PASSED [ 87%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_mass_ratio_min-None-override3] PASSED [ 88%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_max_sep-None-override4] PASSED [ 89%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[malformed_redshift-None-override5] PASSED [ 90%]\ntests/test_hB.py::test_B19b_preflight_checks_every_configured_redshift_before_writing PASSED [ 90%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad0] PASSED [ 91%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad1] PASSED [ 92%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad2] PASSED [ 92%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad3] PASSED [ 93%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad4] PASSED [ 94%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[primary] PASSED [ 95%]\ntests/test_hB.py::test_B21_console_summary_fields PASSED                 [ 95%]\ntests/test_hB.py::test_B21b_console_line_selection_is_token_exact_not_substring PASSED [ 96%]\ntests/test_hB.py::test_B22_console_reports_not_checked_for_partial_convention_set PASSED [ 97%]\ntests/test_hB.py::test_B23_provenance_compared_against_config_not_defaults PASSED [ 97%]\ntests/test_hB.py::test_B24_additivity_false_from_check_propagates_everywhere PASSED [ 98%]\ntests/test_hB.py::test_B26_full_driver_run_on_nondefault_bin_grid PASSED [ 99%]\ntests/test_hB.py::test_B27_low_mass_ratio_pair_not_refiltered PASSED     [100%]\n\n============================= 140 passed in 2.02s ==============================\n",
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
      "tests/test_pair_binning.py::TestComparisonDriver::test_full_run_schema_values_independent_recomputation_and_summary",
      "tests/test_pair_binning.py::TestComparisonDriver::test_invalid_conventions_preserve_existing_output[conventions0]",
      "tests/test_pair_binning.py::TestComparisonDriver::test_invalid_conventions_preserve_existing_output[conventions1]",
      "tests/test_pair_binning.py::TestComparisonDriver::test_invalid_conventions_preserve_existing_output[conventions2]",
      "tests/test_pair_binning.py::TestComparisonDriver::test_invalid_conventions_preserve_existing_output[conventions3]",
      "tests/test_pair_binning.py::TestComparisonDriver::test_invalid_conventions_preserve_existing_output[conventions4]",
      "tests/test_pair_binning.py::TestComparisonDriver::test_invalid_conventions_preserve_existing_output[primary]",
      "tests/test_pair_binning.py::TestComparisonDriver::test_preflight_failures_preserve_existing_output[bad_mass_ratio]",
      "tests/test_pair_binning.py::TestComparisonDriver::test_preflight_failures_preserve_existing_output[bad_max_sep]",
      "tests/test_pair_binning.py::TestComparisonDriver::test_preflight_failures_preserve_existing_output[bad_redshift]",
      "tests/test_pair_binning.py::TestComparisonDriver::test_preflight_failures_preserve_existing_output[late_bad_redshift]",
      "tests/test_pair_binning.py::TestComparisonDriver::test_preflight_failures_preserve_existing_output[malformed_redshift]",
      "tests/test_pair_binning.py::TestComparisonDriver::test_preflight_failures_preserve_existing_output[missing_data]",
      "tests/test_pair_binning.py::TestComparisonDriver::test_preflight_failures_preserve_existing_output[missing_results]",
      "tests/test_pair_binning.py::TestComparisonDriver::test_single_redshift_matches_its_row_from_full_run",
      "tests/test_pair_binning.py::TestComparisonDriver::test_subset_order_disables_additivity_and_matches_full_rows",
      "tests/test_pair_binning.py::TestPartOneCounting::test_all_bin_shapes_and_edges_come_from_config",
      "tests/test_pair_binning.py::TestPartOneCounting::test_config_addition_does_not_change_frozen_convention",
      "tests/test_pair_binning.py::TestPartOneCounting::test_denominator_is_independent_of_frozen_convention[None]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_denominator_is_independent_of_frozen_convention[mean]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_denominator_is_independent_of_frozen_convention[nonsense]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_denominator_is_independent_of_frozen_convention[primary]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_denominator_is_independent_of_frozen_convention[secondary]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_denominator_is_independent_of_frozen_convention[total]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_either_counts_two_same_bin_members_and_both_different_bins",
      "tests/test_pair_binning.py::TestPartOneCounting::test_empty_pair_arrays_are_valid[either]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_empty_pair_arrays_are_valid[primary]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_empty_pair_arrays_are_valid[secondary]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_galaxy_count_validation[masses0-1D]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_galaxy_count_validation[masses1-finite]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_galaxy_count_validation[masses2-finite]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_galaxy_count_validation[masses3-real numeric]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_galaxy_count_validation[masses4-real numeric]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_galaxy_count_validation[masses5-real numeric]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_galaxy_edges_are_right_open",
      "tests/test_pair_binning.py::TestPartOneCounting::test_pair_conventions_and_exclusion_identities",
      "tests/test_pair_binning.py::TestPartOneCounting::test_pair_functions_reject_unsupported_conventions[1-count_excluded_pairs]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_pair_functions_reject_unsupported_conventions[1-count_pairs_per_mass_bin]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_pair_functions_reject_unsupported_conventions[None-count_excluded_pairs]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_pair_functions_reject_unsupported_conventions[None-count_pairs_per_mass_bin]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_pair_functions_reject_unsupported_conventions[mean-count_excluded_pairs]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_pair_functions_reject_unsupported_conventions[mean-count_pairs_per_mass_bin]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_pair_functions_reject_unsupported_conventions[total-count_excluded_pairs]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_pair_functions_reject_unsupported_conventions[total-count_pairs_per_mass_bin]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_pair_functions_reject_unsupported_conventions[unknown-count_excluded_pairs]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_pair_functions_reject_unsupported_conventions[unknown-count_pairs_per_mass_bin]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_pair_functions_validate_mass_arrays[primary0-secondary0-identical shapes-count_excluded_pairs]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_pair_functions_validate_mass_arrays[primary0-secondary0-identical shapes-count_pairs_per_mass_bin]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_pair_functions_validate_mass_arrays[primary1-secondary1-1D-count_excluded_pairs]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_pair_functions_validate_mass_arrays[primary1-secondary1-1D-count_pairs_per_mass_bin]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_pair_functions_validate_mass_arrays[primary2-secondary2-finite-count_excluded_pairs]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_pair_functions_validate_mass_arrays[primary2-secondary2-finite-count_pairs_per_mass_bin]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_pair_functions_validate_mass_arrays[primary3-secondary3-finite-count_excluded_pairs]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_pair_functions_validate_mass_arrays[primary3-secondary3-finite-count_pairs_per_mass_bin]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_pair_functions_validate_mass_arrays[primary4-secondary4-real numeric-count_excluded_pairs]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_pair_functions_validate_mass_arrays[primary4-secondary4-real numeric-count_pairs_per_mass_bin]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_pair_functions_validate_mass_arrays[primary5-secondary5-real numeric-count_excluded_pairs]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_pair_functions_validate_mass_arrays[primary5-secondary5-real numeric-count_pairs_per_mass_bin]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_pair_functions_validate_mass_arrays[primary6-secondary6-real numeric-count_excluded_pairs]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_pair_functions_validate_mass_arrays[primary6-secondary6-real numeric-count_pairs_per_mass_bin]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_pair_functions_validate_mass_arrays[primary7-secondary7-secondary-count_excluded_pairs]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_pair_functions_validate_mass_arrays[primary7-secondary7-secondary-count_pairs_per_mass_bin]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_pair_ordering_is_checked_before_float_narrowing[count_excluded_pairs]",
      "tests/test_pair_binning.py::TestPartOneCounting::test_pair_ordering_is_checked_before_float_narrowing[count_pairs_per_mass_bin]",
      "tests/test_pair_binning.py::TestPartOneFractions::test_additivity_true_false_and_zero",
      "tests/test_pair_binning.py::TestPartOneFractions::test_additivity_validation[primary0-secondary0-either0-identical shapes]",
      "tests/test_pair_binning.py::TestPartOneFractions::test_additivity_validation[primary1-secondary1-either1-1D]",
      "tests/test_pair_binning.py::TestPartOneFractions::test_additivity_validation[primary2-secondary2-either2-non-negative]",
      "tests/test_pair_binning.py::TestPartOneFractions::test_additivity_validation[primary3-secondary3-either3-finite]",
      "tests/test_pair_binning.py::TestPartOneFractions::test_additivity_validation[primary4-secondary4-either4-integer-valued]",
      "tests/test_pair_binning.py::TestPartOneFractions::test_additivity_validation[primary5-secondary5-either5-real numeric]",
      "tests/test_pair_binning.py::TestPartOneFractions::test_additivity_validation[primary6-secondary6-either6-real numeric]",
      "tests/test_pair_binning.py::TestPartOneFractions::test_integer_valued_floats_are_valid",
      "tests/test_pair_binning.py::TestPartOneFractions::test_pair_fraction_validation[pairs0-galaxies0-identical shapes]",
      "tests/test_pair_binning.py::TestPartOneFractions::test_pair_fraction_validation[pairs1-galaxies1-1D]",
      "tests/test_pair_binning.py::TestPartOneFractions::test_pair_fraction_validation[pairs10-galaxies10-real numeric]",
      "tests/test_pair_binning.py::TestPartOneFractions::test_pair_fraction_validation[pairs2-galaxies2-non-negative]",
      "tests/test_pair_binning.py::TestPartOneFractions::test_pair_fraction_validation[pairs3-galaxies3-non-negative]",
      "tests/test_pair_binning.py::TestPartOneFractions::test_pair_fraction_validation[pairs4-galaxies4-finite]",
      "tests/test_pair_binning.py::TestPartOneFractions::test_pair_fraction_validation[pairs5-galaxies5-finite]",
      "tests/test_pair_binning.py::TestPartOneFractions::test_pair_fraction_validation[pairs6-galaxies6-integer-valued]",
      "tests/test_pair_binning.py::TestPartOneFractions::test_pair_fraction_validation[pairs7-galaxies7-integer-valued]",
      "tests/test_pair_binning.py::TestPartOneFractions::test_pair_fraction_validation[pairs8-galaxies8-real numeric]",
      "tests/test_pair_binning.py::TestPartOneFractions::test_pair_fraction_validation[pairs9-galaxies9-real numeric]",
      "tests/test_pair_binning.py::TestPartOneFractions::test_pair_fraction_values_and_required_docstring",
      "tests/test_pair_binning.py::TestPartOneFractions::test_positive_incidence_requires_a_galaxy",
      "tests/test_pair_binning.py::TestPartOneFractions::test_zero_over_zero_is_exactly_zero",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_generated_snapshot_schema_denominator_and_identities",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_handwritten_counts_differ_and_match_fixture_columns",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_loading_honours_configured_convention_subset[conventions0]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_loading_honours_configured_convention_subset[conventions1]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_loading_rejects_invalid_convention_config[conventions0]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_loading_rejects_invalid_convention_config[conventions1]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_loading_rejects_invalid_convention_config[conventions2]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_loading_rejects_invalid_convention_config[conventions3]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_loading_rejects_invalid_convention_config[conventions4]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_loading_rejects_invalid_convention_config[primary]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_loading_rejects_malformed_provenance[(2+0j)-mass_ratio_min]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_loading_rejects_malformed_provenance[(2+0j)-max_sep_kpc]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_loading_rejects_malformed_provenance[(2+0j)-redshift]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_loading_rejects_malformed_provenance[2.0_0-mass_ratio_min]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_loading_rejects_malformed_provenance[2.0_0-max_sep_kpc]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_loading_rejects_malformed_provenance[2.0_0-redshift]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_loading_rejects_malformed_provenance[2.0_1-mass_ratio_min]",
      "tests/test_pair_binning.py::TestSnapshotLoading::test_loading_rejects_malforme
```
