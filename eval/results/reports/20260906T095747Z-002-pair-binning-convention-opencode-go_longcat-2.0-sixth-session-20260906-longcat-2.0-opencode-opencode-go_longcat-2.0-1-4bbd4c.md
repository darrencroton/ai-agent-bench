# Trial report: 20260906T095747Z-002-pair-binning-convention-opencode-go_longcat-2.0-sixth-session-20260906-longcat-2.0-opencode-opencode-go_longcat-2.0-1-4bbd4c

- Task: `002-pair-binning-convention`
- Model: `opencode-go/longcat-2.0` (harness: opencode)
- Model duration: 1526.1s | venv setup: 25.6s | timed out: False | committed: False
- Changed files: src/config.py, src/pair_binning.py, tests/test_pair_binning.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 88.9 / 100

## Judged: readability 75% of weight, maintainability 50% of weight (judge claude-opus-5, status ok)

## Composite score: 85.0 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 96% |
| test_adequacy | automated | 25 | 68% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 100% |
| readability | judged | 8 | 75% |
| maintainability | judged | 7 | 50% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| api_surface_and_bin_geometry | 5 | 5 | 1.00 |
| denominator_galaxy_counting | 9 | 10 | 0.90 |
| pinned_pair_counts_under_every_supported_convention | 11 | 11 | 1.00 |
| additivity_and_exclusion_invariant_preservation | 12 | 14 | 0.86 |
| rejection_semantics_of_the_pure_counting_functions | 39 | 44 | 0.89 |
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
    "passed": 132,
    "failed": [
      "tests/test_hA.py::test_A06_galaxy_count_rejections[bad4-keywords4]",
      "tests/test_hA.py::test_A15_unsupported_conventions_rejected[bad7-count_pairs_per_mass_bin]",
      "tests/test_hA.py::test_A15_unsupported_conventions_rejected[bad7-count_excluded_pairs]",
      "tests/test_hA.py::test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_pairs_per_mass_bin]",
      "tests/test_hA.py::test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_excluded_pairs]",
      "tests/test_hA.py::test_A22_pair_fraction_rejections[npair10-ngal10-keywords10]",
      "tests/test_hA.py::test_A25_check_additivity_rejections[a16-a26-a36-keywords6]",
      "tests/test_hA.py::test_A30_check_additivity_exact_above_2_53"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "s_per_mass_bin] ___\ntests/test_hA.py:242: in test_A15_unsupported_conventions_rejected\n    assert rejects(fn, FIX_PRIMARY, FIX_SECONDARY, bad, BASE) == \"assert\", (fn, bad)\nE   AssertionError: (<function count_pairs_per_mass_bin at 0x10be0ddd0>, ['primary'])\nE   assert 'TypeError' == 'assert'\nE     \nE     - assert\nE     + TypeError\n_____ test_A15_unsupported_conventions_rejected[bad7-count_excluded_pairs] _____\ntests/test_hA.py:242: in test_A15_unsupported_conventions_rejected\n    assert rejects(fn, FIX_PRIMARY, FIX_SECONDARY, bad, BASE) == \"assert\", (fn, bad)\nE   AssertionError: (<function count_excluded_pairs at 0x10be0de80>, ['primary'])\nE   assert 'TypeError' == 'assert'\nE     \nE     - assert\nE     + TypeError\n_ test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_pairs_per_mass_bin] _\ntests/test_hA.py:260: in test_A16_pair_array_rejections\n    assert rejects(fn, primary, secondary, \"primary\", BASE) == \"assert\"\nE   AssertionError: assert None == 'assert'\nE    +  where None = rejects(<function count_pairs_per_mass_bin at 0x10be0ddd0>, array(['9.0'], dtype='<U3'), array(['8.0'], dtype='<U3'), 'primary', {'box_size': 500.0, 'redshifts': [2.0, 3.0, 4.0, 5.0], 'log_mass_min': 8.0, 'log_mass_max': 11.0, ...})\n_ test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_excluded_pairs] _\ntests/test_hA.py:260: in test_A16_pair_array_rejections\n    assert rejects(fn, primary, secondary, \"primary\", BASE) == \"assert\"\nE   AssertionError: assert None == 'assert'\nE    +  where None = rejects(<function count_excluded_pairs at 0x10be0de80>, array(['9.0'], dtype='<U3'), array(['8.0'], dtype='<U3'), 'primary', {'box_size': 500.0, 'redshifts': [2.0, 3.0, 4.0, 5.0], 'log_mass_min': 8.0, 'log_mass_max': 11.0, ...})\n_________ test_A22_pair_fraction_rejections[npair10-ngal10-keywords10] _________\ntests/test_hA.py:327: in test_A22_pair_fraction_rejections\n    assert rejects(PB.compute_pair_fraction, npair, ngal) == \"assert\"\nE   AssertionError: assert None == 'assert'\nE    +  where None = rejects(<function compute_pair_fraction at 0x10be0df30>, array(['1'], dtype='<U1'), array(['10'], dtype='<U2'))\nE    +    where <function compute_pair_fraction at 0x10be0df30> = PB.compute_pair_fraction\n_________ test_A25_check_additivity_rejections[a16-a26-a36-keywords6] __________\ntests/test_hA.py:360: in test_A25_check_additivity_rejections\n    assert rejects(PB.check_additivity, a1, a2, a3) == \"assert\"\nE   AssertionError: assert None == 'assert'\nE    +  where None = rejects(<function check_additivity at 0x10be0dfe0>, ['1'], ['1'], ['2'])\nE    +    where <function check_additivity at 0x10be0dfe0> = PB.check_additivity\n__________________ test_A30_check_additivity_exact_above_2_53 __________________\ntests/test_hA.py:476: in test_A30_check_additivity_exact_above_2_53\n    assert PB.check_additivity(big, one, big) is False\nE   assert True is False\nE    +  where True = <function check_additivity at 0x10be0dfe0>(array([9007199254740992]), array([1]), array([9007199254740992]))\nE    +    where <function check_additivity at 0x10be0dfe0> = PB.check_additivity\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A06_galaxy_count_rejections[bad4-keywords4] - A...\nFAILED tests/test_hA.py::test_A15_unsupported_conventions_rejected[bad7-count_pairs_per_mass_bin]\nFAILED tests/test_hA.py::test_A15_unsupported_conventions_rejected[bad7-count_excluded_pairs]\nFAILED tests/test_hA.py::test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_pairs_per_mass_bin]\nFAILED tests/test_hA.py::test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_excluded_pairs]\nFAILED tests/test_hA.py::test_A22_pair_fraction_rejections[npair10-ngal10-keywords10]\nFAILED tests/test_hA.py::test_A25_check_additivity_rejections[a16-a26-a36-keywords6]\nFAILED tests/test_hA.py::test_A30_check_additivity_exact_above_2_53 - assert ...\n======================== 8 failed, 132 passed in 2.13s =========================\n",
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
        "passed": 12,
        "collected": 14,
        "fraction": 0.8571428571428571,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_A25_check_additivity_rejections[a16-a26-a36-keywords6]",
          "tests/test_hA.py::test_A30_check_additivity_exact_above_2_53"
        ]
      },
      {
        "id": "rejection_semantics_of_the_pure_counting_functions",
        "passed": 39,
        "collected": 44,
        "fraction": 0.8863636363636364,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_A15_unsupported_conventions_rejected[bad7-count_excluded_pairs]",
          "tests/test_hA.py::test_A15_unsupported_conventions_rejected[bad7-count_pairs_per_mass_bin]",
          "tests/test_hA.py::test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_excluded_pairs]",
          "tests/test_hA.py::test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_pairs_per_mass_bin]",
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
      "tests/test_pair_binning.py::TestCheckAdditivity::test_all_zero",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_holds",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_complex",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_mismatched_shapes",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_negative",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_non_1d",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_non_finite",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_non_integer_valued",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_violated",
      "tests/test_pair_binning.py::TestComputePairFraction::test_basic",
      "tests/test_pair_binning.py::TestComputePairFraction::test_docstring",
      "tests/test_pair_binning.py::TestComputePairFraction::test_integer_dtype_input",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_complex",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_mismatched_shapes",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_negative",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_non_1d",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_non_finite",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_non_integer_valued",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_pairs_positive_galaxies_zero",
      "tests/test_pair_binning.py::TestComputePairFraction::test_zero_over_zero",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_either",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_exclusion_sum_rule",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_primary",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_rejects_complex",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_rejects_mismatched_shapes",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_rejects_non_1d",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_rejects_non_finite",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_rejects_secondary_gt_primary",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_rejects_unsupported_convention",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_secondary",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_zero_length",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_custom_config",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_default_config_exact",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_no_convention_dependency",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_rejects_complex",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_rejects_non_1d",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_rejects_non_finite",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_zero_length",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_additivity",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_both_members_same_bin",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_different_bins",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_either",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_primary",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_rejects_complex",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_rejects_mismatched_shapes",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_rejects_non_1d",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_rejects_non_finite",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_rejects_secondary_gt_primary",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_rejects_unsupported_convention",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_secondary",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_vectors_distinct",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_zero_length",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_additivity_holds",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_exclusion_sum_rule",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_honours_configured_conventions",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_ignores_stored_mass_bin",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_n_galaxies_matches_catalog",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_n_galaxies_no_convention_axis",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_n_pairs_keyed_by_convention",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_n_pairs_total",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_duplicate_conventions",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_empty_conventions",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_malformed_redshift_attr",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_mismatched_mass_ratio_min",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_mismatched_max_sep_kpc",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_mismatched_redshift",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_missing_data_file",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_missing_dataset",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_missing_redshift_attr",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_missing_results_file",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_non_list_conventions",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_non_string_convention",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_unequal_dataset_lengths",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_unsupported_convention",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_returns_correct_keys",
      "tests/test_pair_binning.py::TestMassBinEdges::test_custom_config",
      "tests/test_pair_binning.py::TestMassBinEdges::test_default_config",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_console_summary",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_console_summary_not_checked",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_end_to_end_reproduces_counts",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_output_file_schema",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_pair_fraction_equals_n_pairs_over_n_galaxies",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_persisted_matches_returned",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_preflight_leaves_file_unchanged_bad_conventions",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_preflight_leaves_file_unchanged_malformed_attr",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_preflight_leaves_file_unchanged_missing_data",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_returned_dicts",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_same_n_galaxies_all_conventions",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_single_redshift",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_two_convention_run",
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
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell
```
