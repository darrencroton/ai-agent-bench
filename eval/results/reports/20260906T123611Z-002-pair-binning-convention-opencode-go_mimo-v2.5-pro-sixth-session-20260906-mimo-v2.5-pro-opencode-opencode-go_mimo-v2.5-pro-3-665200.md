# Trial report: 20260906T123611Z-002-pair-binning-convention-opencode-go_mimo-v2.5-pro-sixth-session-20260906-mimo-v2.5-pro-opencode-opencode-go_mimo-v2.5-pro-3-665200

- Task: `002-pair-binning-convention`
- Model: `opencode-go/mimo-v2.5-pro` (harness: opencode)
- Model duration: 1683.6s | venv setup: 36.4s | timed out: False | committed: False
- Changed files: src/config.py, src/pair_binning.py, tests/test_pair_binning.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 83.8 / 100

## Judged: readability 75% of weight, maintainability 25% of weight (judge claude-opus-5, status ok)

## Composite score: 79.0 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 96% |
| test_adequacy | automated | 25 | 61% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 77% |
| readability | judged | 8 | 75% |
| maintainability | judged | 7 | 25% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| api_surface_and_bin_geometry | 5 | 5 | 1.00 |
| denominator_galaxy_counting | 9 | 10 | 0.90 |
| pinned_pair_counts_under_every_supported_convention | 11 | 11 | 1.00 |
| additivity_and_exclusion_invariant_preservation | 12 | 14 | 0.86 |
| rejection_semantics_of_the_pure_counting_functions | 39 | 44 | 0.89 |
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
    "passed": 131,
    "failed": [
      "tests/test_hA.py::test_A06_galaxy_count_rejections[bad4-keywords4]",
      "tests/test_hA.py::test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_pairs_per_mass_bin]",
      "tests/test_hA.py::test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_excluded_pairs]",
      "tests/test_hA.py::test_A22_pair_fraction_rejections[npair7-ngal7-keywords7]",
      "tests/test_hA.py::test_A22_pair_fraction_rejections[npair8-ngal8-keywords8]",
      "tests/test_hA.py::test_A22_pair_fraction_rejections[npair10-ngal10-keywords10]",
      "tests/test_hA.py::test_A25_check_additivity_rejections[a16-a26-a36-keywords6]",
      "tests/test_hA.py::test_A30_check_additivity_exact_above_2_53",
      "tests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override6-max_sep_kpc]"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "keywords5-count_excluded_pairs] _\ntests/test_hA.py:260: in test_A16_pair_array_rejections\n    assert rejects(fn, primary, secondary, \"primary\", BASE) == \"assert\"\nE   AssertionError: assert None == 'assert'\nE    +  where None = rejects(<function count_excluded_pairs at 0x10c50dc70>, array(['9.0'], dtype='<U3'), array(['8.0'], dtype='<U3'), 'primary', {'box_size': 500.0, 'redshifts': [2.0, 3.0, 4.0, 5.0], 'log_mass_min': 8.0, 'log_mass_max': 11.0, ...})\n__________ test_A22_pair_fraction_rejections[npair7-ngal7-keywords7] ___________\ntests/test_hA.py:327: in test_A22_pair_fraction_rejections\n    assert rejects(PB.compute_pair_fraction, npair, ngal) == \"assert\"\nE   AssertionError: assert None == 'assert'\nE    +  where None = rejects(<function compute_pair_fraction at 0x10c50dd20>, array([1.5]), array([10.]))\nE    +    where <function compute_pair_fraction at 0x10c50dd20> = PB.compute_pair_fraction\n__________ test_A22_pair_fraction_rejections[npair8-ngal8-keywords8] ___________\ntests/test_hA.py:327: in test_A22_pair_fraction_rejections\n    assert rejects(PB.compute_pair_fraction, npair, ngal) == \"assert\"\nE   AssertionError: assert None == 'assert'\nE    +  where None = rejects(<function compute_pair_fraction at 0x10c50dd20>, array([1.]), array([10.5]))\nE    +    where <function compute_pair_fraction at 0x10c50dd20> = PB.compute_pair_fraction\n_________ test_A22_pair_fraction_rejections[npair10-ngal10-keywords10] _________\ntests/test_hA.py:327: in test_A22_pair_fraction_rejections\n    assert rejects(PB.compute_pair_fraction, npair, ngal) == \"assert\"\nE   AssertionError: assert None == 'assert'\nE    +  where None = rejects(<function compute_pair_fraction at 0x10c50dd20>, array(['1'], dtype='<U1'), array(['10'], dtype='<U2'))\nE    +    where <function compute_pair_fraction at 0x10c50dd20> = PB.compute_pair_fraction\n_________ test_A25_check_additivity_rejections[a16-a26-a36-keywords6] __________\ntests/test_hA.py:360: in test_A25_check_additivity_rejections\n    assert rejects(PB.check_additivity, a1, a2, a3) == \"assert\"\nE   AssertionError: assert None == 'assert'\nE    +  where None = rejects(<function check_additivity at 0x10c50ddd0>, ['1'], ['1'], ['2'])\nE    +    where <function check_additivity at 0x10c50ddd0> = PB.check_additivity\n__________________ test_A30_check_additivity_exact_above_2_53 __________________\ntests/test_hA.py:476: in test_A30_check_additivity_exact_above_2_53\n    assert PB.check_additivity(big, one, big) is False\nE   assert True is False\nE    +  where True = <function check_additivity at 0x10c50ddd0>(array([9007199254740992]), array([1]), array([9007199254740992]))\nE    +    where <function check_additivity at 0x10c50ddd0> = PB.check_additivity\n_____ test_B11_load_snapshot_counts_attr_rejections[override6-max_sep_kpc] _____\ntests/test_hB.py:370: in test_B11_load_snapshot_counts_attr_rejections\n    assert attr in msg, (attr, msg)\nE   AssertionError: ('max_sep_kpc', 'max_sep must be numeric, got str')\nE   assert 'max_sep_kpc' in 'max_sep must be numeric, got str'\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A06_galaxy_count_rejections[bad4-keywords4] - A...\nFAILED tests/test_hA.py::test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_pairs_per_mass_bin]\nFAILED tests/test_hA.py::test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_excluded_pairs]\nFAILED tests/test_hA.py::test_A22_pair_fraction_rejections[npair7-ngal7-keywords7]\nFAILED tests/test_hA.py::test_A22_pair_fraction_rejections[npair8-ngal8-keywords8]\nFAILED tests/test_hA.py::test_A22_pair_fraction_rejections[npair10-ngal10-keywords10]\nFAILED tests/test_hA.py::test_A25_check_additivity_rejections[a16-a26-a36-keywords6]\nFAILED tests/test_hA.py::test_A30_check_additivity_exact_above_2_53 - assert ...\nFAILED tests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override6-max_sep_kpc]\n======================== 9 failed, 131 passed in 2.03s =========================\n",
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
          "tests/test_hA.py::test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_excluded_pairs]",
          "tests/test_hA.py::test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_pairs_per_mass_bin]",
          "tests/test_hA.py::test_A22_pair_fraction_rejections[npair10-ngal10-keywords10]",
          "tests/test_hA.py::test_A22_pair_fraction_rejections[npair7-ngal7-keywords7]",
          "tests/test_hA.py::test_A22_pair_fraction_rejections[npair8-ngal8-keywords8]"
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
          "tests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override6-max_sep_kpc]"
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
      "tests/test_pair_binning.py::TestCheckAdditivity::test_all_zeros",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_holds",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_complex",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_mismatched_shapes",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_negative",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_non_1d",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_non_finite",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_non_integer_valued",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_violation_returns_false",
      "tests/test_pair_binning.py::TestComputePairFraction::test_accepts_integer_dtypes",
      "tests/test_pair_binning.py::TestComputePairFraction::test_accepts_integer_valued_float64",
      "tests/test_pair_binning.py::TestComputePairFraction::test_asserts_n_pairs_gt0_requires_n_galaxies_gt0",
      "tests/test_pair_binning.py::TestComputePairFraction::test_docstring_contains_required_sentence",
      "tests/test_pair_binning.py::TestComputePairFraction::test_known_values",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_complex",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_mismatched_shapes",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_negative",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_non_1d",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_non_finite",
      "tests/test_pair_binning.py::TestComputePairFraction::test_zero_pairs_zero_galaxies",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_rejects_complex",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_rejects_mismatched_shapes",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_rejects_non_1d",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_rejects_non_finite",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_rejects_non_string_convention",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_rejects_secondary_greater_than_primary",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_rejects_unknown_convention",
      "tests/test_pair_binning.py::TestCountGalaxies::test_custom_config",
      "tests/test_pair_binning.py::TestCountGalaxies::test_default_config_exact_values",
      "tests/test_pair_binning.py::TestCountGalaxies::test_independent_of_mass_bin_by",
      "tests/test_pair_binning.py::TestCountGalaxies::test_no_mass_bin_by_key",
      "tests/test_pair_binning.py::TestCountGalaxies::test_rejects_complex",
      "tests/test_pair_binning.py::TestCountGalaxies::test_rejects_non_1d",
      "tests/test_pair_binning.py::TestCountGalaxies::test_rejects_non_finite",
      "tests/test_pair_binning.py::TestCountGalaxies::test_zero_length",
      "tests/test_pair_binning.py::TestCountPairs::test_additivity_holds",
      "tests/test_pair_binning.py::TestCountPairs::test_either_counts_both_members",
      "tests/test_pair_binning.py::TestCountPairs::test_exclusion_sum_rule",
      "tests/test_pair_binning.py::TestCountPairs::test_pair_in_different_bins",
      "tests/test_pair_binning.py::TestCountPairs::test_rejects_complex",
      "tests/test_pair_binning.py::TestCountPairs::test_rejects_mismatched_shapes",
      "tests/test_pair_binning.py::TestCountPairs::test_rejects_non_1d",
      "tests/test_pair_binning.py::TestCountPairs::test_rejects_non_finite",
      "tests/test_pair_binning.py::TestCountPairs::test_rejects_non_string_convention",
      "tests/test_pair_binning.py::TestCountPairs::test_rejects_secondary_greater_than_primary",
      "tests/test_pair_binning.py::TestCountPairs::test_rejects_unknown_convention",
      "tests/test_pair_binning.py::TestCountPairs::test_returns_distinct_arrays",
      "tests/test_pair_binning.py::TestCountPairs::test_zero_length",
      "tests/test_pair_binning.py::TestEdgeCases::test_both_members_outside_bins",
      "tests/test_pair_binning.py::TestEdgeCases::test_one_member_outside_bins",
      "tests/test_pair_binning.py::TestEdgeCases::test_zero_length_arrays",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_additivity_and_exclusion",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_convention_counts_vary",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_convention_keyed_dicts",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_honours_conventions_list",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_n_galaxies_no_convention_axis",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_n_pairs_total_matches_file",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_complex_attr",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_duplicate_conventions",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_empty_conventions",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_mismatched_mass_ratio",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_mismatched_max_sep",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_mismatched_redshift",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_missing_attr",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_missing_data_file",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_missing_dataset",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_missing_results_file",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_non_list_conventions",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_non_string_convention",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_string_attr",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_unequal_lengths",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_unsupported_convention",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_returns_correct_keys",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_stored_bin_not_used",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_sum_n_galaxies_matches_catalog",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_additivity_on_generated",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_console_summary",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_conventions_tracks_config",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_end_to_end_on_generated",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_invalid_conventions_preserves_sentinel",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_n_galaxies_no_convention_axis",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_output_file_schema",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_pair_fraction_matches_computation",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_persisted_values_match_returned",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_preflight_gate_malformed_redshift",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_preflight_gate_mismatched_mass_ratio",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_preflight_gate_mismatched_max_sep",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_preflight_gate_mismatched_redshift",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_preflight_gate_preserves_sentinel",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_returned_dict_keys",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_single_redshift",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_two_convention_console_summary",
      "tests/test_pair_binning.py::test_existing_tests_unchanged",
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
      "tests/test_statistical.p
```
