# Trial report: 20260906T091841Z-002-pair-binning-convention-opencode-go_mimo-v2.5-sixth-session-20260906-mimo-v2.5-opencode-opencode-go_mimo-v2.5-1-4ef706

- Task: `002-pair-binning-convention`
- Model: `opencode-go/mimo-v2.5` (harness: opencode)
- Model duration: 1541.5s | venv setup: 27.7s | timed out: False | committed: False
- Changed files: src/config.py, src/pair_binning.py, tests/test_pair_binning.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 79.4 / 100

## Judged: readability 75% of weight, maintainability 50% of weight (judge claude-opus-5, status ok)

## Composite score: 77.0 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 99% |
| test_adequacy | automated | 25 | 52% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 50% |
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
| snapshot_loading_contract_and_provenance_rejections | 27 | 28 | 0.96 |
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
    "passed": 137,
    "failed": [
      "tests/test_hA.py::test_A22_pair_fraction_rejections[npair10-ngal10-keywords10]",
      "tests/test_hA.py::test_A25_check_additivity_rejections[a16-a26-a36-keywords6]",
      "tests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override0-redshift]"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "_B18_single_redshift_run PASSED                    [ 85%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[missing_data-<lambda>-None] PASSED [ 86%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[missing_results-<lambda>-None] PASSED [ 87%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_redshift-None-override2] PASSED [ 87%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_mass_ratio_min-None-override3] PASSED [ 88%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_max_sep-None-override4] PASSED [ 89%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[malformed_redshift-None-override5] PASSED [ 90%]\ntests/test_hB.py::test_B19b_preflight_checks_every_configured_redshift_before_writing PASSED [ 90%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad0] PASSED [ 91%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad1] PASSED [ 92%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad2] PASSED [ 92%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad3] PASSED [ 93%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad4] PASSED [ 94%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[primary] PASSED [ 95%]\ntests/test_hB.py::test_B21_console_summary_fields PASSED                 [ 95%]\ntests/test_hB.py::test_B21b_console_line_selection_is_token_exact_not_substring PASSED [ 96%]\ntests/test_hB.py::test_B22_console_reports_not_checked_for_partial_convention_set PASSED [ 97%]\ntests/test_hB.py::test_B23_provenance_compared_against_config_not_defaults PASSED [ 97%]\ntests/test_hB.py::test_B24_additivity_false_from_check_propagates_everywhere PASSED [ 98%]\ntests/test_hB.py::test_B26_full_driver_run_on_nondefault_bin_grid PASSED [ 99%]\ntests/test_hB.py::test_B27_low_mass_ratio_pair_not_refiltered PASSED     [100%]\n\n=================================== FAILURES ===================================\n_________ test_A22_pair_fraction_rejections[npair10-ngal10-keywords10] _________\ntests/test_hA.py:327: in test_A22_pair_fraction_rejections\n    assert rejects(PB.compute_pair_fraction, npair, ngal) == \"assert\"\nE   AssertionError: assert 'TypeError' == 'assert'\nE     \nE     - assert\nE     + TypeError\n_________ test_A25_check_additivity_rejections[a16-a26-a36-keywords6] __________\ntests/test_hA.py:360: in test_A25_check_additivity_rejections\n    assert rejects(PB.check_additivity, a1, a2, a3) == \"assert\"\nE   AssertionError: assert 'TypeError' == 'assert'\nE     \nE     - assert\nE     + TypeError\n______ test_B11_load_snapshot_counts_attr_rejections[override0-redshift] _______\ntests/test_hB.py:370: in test_B11_load_snapshot_counts_attr_rejections\n    assert attr in msg, (attr, msg)\nE   AssertionError: ('redshift', 'Redshift mismatch: stored 9.0 != configured 2.0')\nE   assert 'redshift' in 'Redshift mismatch: stored 9.0 != configured 2.0'\n=============================== warnings summary ===============================\ntests/test_hA.py::test_A21_incidence_without_galaxies_rejected\n  /Users/dcroton/Local/git-repos/ai-agent-bench/eval/results/tmp/worktrees/20260906T091841Z-002-pair-binning-convention-opencode-go_mimo-v2.5-sixth-session-20260906-mimo-v2.5-opencode-opencode-go_mimo-v2.5-1-4ef706/tests/../src/pair_binning.py:299: RuntimeWarning: divide by zero encountered in divide\n    f_pair[mask] = n_pairs[mask] / n_galaxies[mask]\n\n-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A22_pair_fraction_rejections[npair10-ngal10-keywords10]\nFAILED tests/test_hA.py::test_A25_check_additivity_rejections[a16-a26-a36-keywords6]\nFAILED tests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override0-redshift]\n=================== 3 failed, 137 passed, 1 warning in 2.18s ===================\n",
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
          "tests/test_hA.py::test_A25_check_additivity_rejections[a16-a26-a36-keywords6]"
        ]
      },
      {
        "id": "rejection_semantics_of_the_pure_counting_functions",
        "passed": 43,
        "collected": 44,
        "fraction": 0.9772727272727273,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_A22_pair_fraction_rejections[npair10-ngal10-keywords10]"
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
        "passed": 27,
        "collected": 28,
        "fraction": 0.9642857142857143,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override0-redshift]"
        ]
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
      "tests/test_pair_binning.py::TestCheckAdditivity::test_all_zero",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_holds",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_complex",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_mismatched_shapes",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_negative",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_non_1d",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_non_finite",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_non_integer",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_violated",
      "tests/test_pair_binning.py::TestComputePairFractionAssertions::test_complex",
      "tests/test_pair_binning.py::TestComputePairFractionAssertions::test_integer_dtype_accepted",
      "tests/test_pair_binning.py::TestComputePairFractionAssertions::test_integer_valued_float64_accepted",
      "tests/test_pair_binning.py::TestComputePairFractionAssertions::test_mismatched_shapes",
      "tests/test_pair_binning.py::TestComputePairFractionAssertions::test_negative",
      "tests/test_pair_binning.py::TestComputePairFractionAssertions::test_non_1d",
      "tests/test_pair_binning.py::TestComputePairFractionAssertions::test_non_finite",
      "tests/test_pair_binning.py::TestComputePairFractionAssertions::test_non_integer_float",
      "tests/test_pair_binning.py::TestComputePairFractionAssertions::test_positive_pairs_zero_galaxies",
      "tests/test_pair_binning.py::TestComputePairFractionDocstring::test_exact_sentence",
      "tests/test_pair_binning.py::TestComputePairFractionValues::test_spec",
      "tests/test_pair_binning.py::TestComputePairFractionValues::test_zero_pairs_positive_galaxies",
      "tests/test_pair_binning.py::TestComputePairFractionValues::test_zero_pairs_zero_galaxies",
      "tests/test_pair_binning.py::TestConsoleSummary::test_additivity_holds_line",
      "tests/test_pair_binning.py::TestConsoleSummary::test_heading_sentence",
      "tests/test_pair_binning.py::TestConsoleSummary::test_per_z_convention_lines",
      "tests/test_pair_binning.py::TestConsoleSummary::test_two_convention_not_checked",
      "tests/test_pair_binning.py::TestCountExcludedPairsInputValidation::test_invalid_convention",
      "tests/test_pair_binning.py::TestCountGalaxiesInputValidation::test_complex",
      "tests/test_pair_binning.py::TestCountGalaxiesInputValidation::test_non_1d",
      "tests/test_pair_binning.py::TestCountGalaxiesInputValidation::test_non_finite",
      "tests/test_pair_binning.py::TestCountGalaxiesValues::test_all_outside_range",
      "tests/test_pair_binning.py::TestCountGalaxiesValues::test_custom_config",
      "tests/test_pair_binning.py::TestCountGalaxiesValues::test_default_config_spec",
      "tests/test_pair_binning.py::TestCountGalaxiesValues::test_independent_of_mass_bin_by",
      "tests/test_pair_binning.py::TestCountGalaxiesValues::test_zero_length",
      "tests/test_pair_binning.py::TestCountPairsInputValidation::test_complex",
      "tests/test_pair_binning.py::TestCountPairsInputValidation::test_invalid_convention_non_string",
      "tests/test_pair_binning.py::TestCountPairsInputValidation::test_invalid_convention_string",
      "tests/test_pair_binning.py::TestCountPairsInputValidation::test_invalid_convention_total",
      "tests/test_pair_binning.py::TestCountPairsInputValidation::test_mismatched_shapes",
      "tests/test_pair_binning.py::TestCountPairsInputValidation::test_non_1d",
      "tests/test_pair_binning.py::TestCountPairsInputValidation::test_non_finite",
      "tests/test_pair_binning.py::TestCountPairsInputValidation::test_secondary_exceeds_primary",
      "tests/test_pair_binning.py::TestCountPairsValues::test_additivity",
      "tests/test_pair_binning.py::TestCountPairsValues::test_both_members_in_same_bin",
      "tests/test_pair_binning.py::TestCountPairsValues::test_either",
      "tests/test_pair_binning.py::TestCountPairsValues::test_either_not_equal_to_others",
      "tests/test_pair_binning.py::TestCountPairsValues::test_excluded_values",
      "tests/test_pair_binning.py::TestCountPairsValues::test_exclusion_sum_rule",
      "tests/test_pair_binning.py::TestCountPairsValues::test_primary",
      "tests/test_pair_binning.py::TestCountPairsValues::test_secondary",
      "tests/test_pair_binning.py::TestCountPairsValues::test_zero_length",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_additivity_holds",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_conventions_subset",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_exclusion_sum_rule",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_ignores_stored_mass_bin",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_n_galaxies_no_convention_axis",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_n_pairs_keys_match_conventions",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_n_pairs_total_matches_file",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_duplicate_conventions",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_empty_conventions",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_missing_data_file",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_missing_results_file",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_non_list_conventions",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_non_string_convention",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_unsupported_convention",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_return_keys",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_two_conventions",
      "tests/test_pair_binning.py::TestLoadSnapshotCountsPerConventionVary::test_secondary_differs_from_primary",
      "tests/test_pair_binning.py::TestMassBinEdges::test_custom_config",
      "tests/test_pair_binning.py::TestMassBinEdges::test_default_config",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_additivity_checked_and_holds",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_conventions_tracks_config",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_end_to_end_independent_recount",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_invalid_conventions_leaves_sentinel",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_n_galaxies_same_across_conventions",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_output_file_datasets_and_attrs",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_pair_fraction_equals_n_pairs_over_n_galaxies",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_persisted_matches_returned",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_preflight_leaves_sentinel_unchanged",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_preflight_mismatched_mass_ratio_min",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_preflight_mismatched_max_sep",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_preflight_mismatched_stored_z",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_returned_dicts",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_single_redshift",
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
      "tests/test_statistical.py::TestMaxwellMoments::test
```
