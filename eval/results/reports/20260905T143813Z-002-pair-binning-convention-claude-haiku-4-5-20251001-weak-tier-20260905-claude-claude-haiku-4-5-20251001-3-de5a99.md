# Trial report: 20260905T143813Z-002-pair-binning-convention-claude-haiku-4-5-20251001-weak-tier-20260905-claude-claude-haiku-4-5-20251001-3-de5a99

- Task: `002-pair-binning-convention`
- Model: `claude-haiku-4-5-20251001` (harness: claude)
- Model duration: 366.7s | venv setup: 28.7s | timed out: False | committed: False
- Changed files: src/config.py, src/pair_binning.py, tests/test_pair_binning.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 71.9 / 100

## Judged: readability 75% of weight, maintainability 25% of weight (judge claude-opus-5, status ok)

## Composite score: 68.9 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 92% |
| test_adequacy | automated | 25 | 37% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 53% |
| readability | judged | 8 | 75% |
| maintainability | judged | 7 | 25% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| api_surface_and_bin_geometry | 5 | 5 | 1.00 |
| denominator_galaxy_counting | 9 | 10 | 0.90 |
| pinned_pair_counts_under_every_supported_convention | 10 | 11 | 0.91 |
| additivity_and_exclusion_invariant_preservation | 8 | 14 | 0.57 |
| rejection_semantics_of_the_pure_counting_functions | 40 | 44 | 0.91 |
| pair_fraction_and_uncertainty | 4 | 4 | 1.00 |
| snapshot_loading_contract_and_provenance_rejections | 28 | 28 | 1.00 |
| config_tracking_through_loader_and_driver | 4 | 4 | 1.00 |
| persistence_schema_atomicity_and_console_reporting | 19 | 20 | 0.95 |

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
    "passed": 127,
    "failed": [
      "tests/test_hA.py::test_A06_galaxy_count_rejections[bad4-keywords4]",
      "tests/test_hA.py::test_A09_additivity_identity_on_fixture",
      "tests/test_hA.py::test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_pairs_per_mass_bin]",
      "tests/test_hA.py::test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_excluded_pairs]",
      "tests/test_hA.py::test_A22_pair_fraction_rejections[npair9-ngal9-keywords9]",
      "tests/test_hA.py::test_A22_pair_fraction_rejections[npair10-ngal10-keywords10]",
      "tests/test_hA.py::test_A24_check_additivity_true_and_false_without_raising",
      "tests/test_hA.py::test_A25_check_additivity_rejections[a16-a26-a36-keywords6]",
      "tests/test_hA.py::test_A25_check_additivity_rejections[a17-a27-a37-keywords7]",
      "tests/test_hA.py::test_A29_pair_binning_at_and_below_lower_mass_edge",
      "tests/test_hA.py::test_A30_check_additivity_exact_above_2_53",
      "tests/test_hB.py::test_B04_counts_and_invariants_on_mock",
      "tests/test_hB.py::test_B14_returned_dicts_match_persisted"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "y([633, 872, 957, 871, 820, 621]))\nE    +    where <function check_additivity at 0x10a156da0> = PB.check_additivity\n___________________ test_B14_returned_dicts_match_persisted ____________________\ntests/test_hB.py:479: in test_B14_returned_dicts_match_persisted\n    assert r[\"additivity_holds\"] is True\nE   assert np.True_ is True\n=============================== warnings summary ===============================\ntests/test_hA.py::test_A22_pair_fraction_rejections[npair9-ngal9-keywords9]\n  /Users/dcroton/Local/git-repos/ai-agent-bench/eval/results/tmp/worktrees/20260905T143813Z-002-pair-binning-convention-claude-haiku-4-5-20251001-weak-tier-20260905-claude-claude-haiku-4-5-20251001-3-de5a99/tests/../src/pair_binning.py:239: ComplexWarning: Casting complex values to real discards the imaginary part\n    n_pairs = np.asarray(n_pairs, dtype=float)\n\ntests/test_hA.py::test_A22_pair_fraction_rejections[npair9-ngal9-keywords9]\n  /Users/dcroton/Local/git-repos/ai-agent-bench/eval/results/tmp/worktrees/20260905T143813Z-002-pair-binning-convention-claude-haiku-4-5-20251001-weak-tier-20260905-claude-claude-haiku-4-5-20251001-3-de5a99/tests/../src/pair_binning.py:240: ComplexWarning: Casting complex values to real discards the imaginary part\n    n_galaxies = np.asarray(n_galaxies, dtype=float)\n\ntests/test_hA.py::test_A25_check_additivity_rejections[a17-a27-a37-keywords7]\n  /Users/dcroton/Local/git-repos/ai-agent-bench/eval/results/tmp/worktrees/20260905T143813Z-002-pair-binning-convention-claude-haiku-4-5-20251001-weak-tier-20260905-claude-claude-haiku-4-5-20251001-3-de5a99/tests/../src/pair_binning.py:326: ComplexWarning: Casting complex values to real discards the imaginary part\n    n_primary_int = np.asarray(n_primary, dtype=int)\n\ntests/test_hA.py::test_A25_check_additivity_rejections[a17-a27-a37-keywords7]\n  /Users/dcroton/Local/git-repos/ai-agent-bench/eval/results/tmp/worktrees/20260905T143813Z-002-pair-binning-convention-claude-haiku-4-5-20251001-weak-tier-20260905-claude-claude-haiku-4-5-20251001-3-de5a99/tests/../src/pair_binning.py:327: ComplexWarning: Casting complex values to real discards the imaginary part\n    n_secondary_int = np.asarray(n_secondary, dtype=int)\n\ntests/test_hA.py::test_A25_check_additivity_rejections[a17-a27-a37-keywords7]\n  /Users/dcroton/Local/git-repos/ai-agent-bench/eval/results/tmp/worktrees/20260905T143813Z-002-pair-binning-convention-claude-haiku-4-5-20251001-weak-tier-20260905-claude-claude-haiku-4-5-20251001-3-de5a99/tests/../src/pair_binning.py:328: ComplexWarning: Casting complex values to real discards the imaginary part\n    n_either_int = np.asarray(n_either, dtype=int)\n\n-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A06_galaxy_count_rejections[bad4-keywords4] - A...\nFAILED tests/test_hA.py::test_A09_additivity_identity_on_fixture - assert np....\nFAILED tests/test_hA.py::test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_pairs_per_mass_bin]\nFAILED tests/test_hA.py::test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_excluded_pairs]\nFAILED tests/test_hA.py::test_A22_pair_fraction_rejections[npair9-ngal9-keywords9]\nFAILED tests/test_hA.py::test_A22_pair_fraction_rejections[npair10-ngal10-keywords10]\nFAILED tests/test_hA.py::test_A24_check_additivity_true_and_false_without_raising\nFAILED tests/test_hA.py::test_A25_check_additivity_rejections[a16-a26-a36-keywords6]\nFAILED tests/test_hA.py::test_A25_check_additivity_rejections[a17-a27-a37-keywords7]\nFAILED tests/test_hA.py::test_A29_pair_binning_at_and_below_lower_mass_edge\nFAILED tests/test_hA.py::test_A30_check_additivity_exact_above_2_53 - assert ...\nFAILED tests/test_hB.py::test_B04_counts_and_invariants_on_mock - assert np.T...\nFAILED tests/test_hB.py::test_B14_returned_dicts_match_persisted - assert np....\n================== 13 failed, 127 passed, 5 warnings in 2.16s ==================\n",
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
        "passed": 10,
        "collected": 11,
        "fraction": 0.9090909090909091,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_A29_pair_binning_at_and_below_lower_mass_edge"
        ]
      },
      {
        "id": "additivity_and_exclusion_invariant_preservation",
        "passed": 8,
        "collected": 14,
        "fraction": 0.5714285714285714,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_A09_additivity_identity_on_fixture",
          "tests/test_hA.py::test_A24_check_additivity_true_and_false_without_raising",
          "tests/test_hA.py::test_A25_check_additivity_rejections[a16-a26-a36-keywords6]",
          "tests/test_hA.py::test_A25_check_additivity_rejections[a17-a27-a37-keywords7]",
          "tests/test_hA.py::test_A30_check_additivity_exact_above_2_53",
          "tests/test_hB.py::test_B04_counts_and_invariants_on_mock"
        ]
      },
      {
        "id": "rejection_semantics_of_the_pure_counting_functions",
        "passed": 40,
        "collected": 44,
        "fraction": 0.9090909090909091,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_excluded_pairs]",
          "tests/test_hA.py::test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_pairs_per_mass_bin]",
          "tests/test_hA.py::test_A22_pair_fraction_rejections[npair10-ngal10-keywords10]",
          "tests/test_hA.py::test_A22_pair_fraction_rejections[npair9-ngal9-keywords9]"
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
        "passed": 19,
        "collected": 20,
        "fraction": 0.95,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hB.py::test_B14_returned_dicts_match_persisted"
        ]
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
      "tests/test_pair_binning.py::TestCheckAdditivity::test_detects_violation",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_holds_identity",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejects_mismatched_shapes",
      "tests/test_pair_binning.py::TestComputePairFraction::test_basic_computation",
      "tests/test_pair_binning.py::TestComputePairFraction::test_docstring_contains_required_sentence",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_negative_counts",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejects_non_integer_valued",
      "tests/test_pair_binning.py::TestComputePairFraction::test_requires_galaxies_for_pairs",
      "tests/test_pair_binning.py::TestComputePairFraction::test_zero_zero_case",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_excluded_pairs",
      "tests/test_pair_binning.py::TestCountExcludedPairs::test_exclusion_sum_rule",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_basic_counting",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_custom_config",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_no_convention_dependency",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_rejects_2d_input",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_rejects_complex",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_rejects_non_finite",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_zero_length_input",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_additivity_identity",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_distinct_conventions",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_either_convention",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_primary_convention",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_rejects_2d_input",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_rejects_mismatched_lengths",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_rejects_non_string_convention",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_rejects_secondary_greater_than_primary",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_rejects_unknown_convention",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_secondary_convention",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_zero_length_pairs",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_additivity_holds_on_mock_data",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_conventions_in_dicts",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_exclusion_sum_rule_on_mock_data",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_loads_correct_structure",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_validates_attributes",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_validates_conventions_list",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_validates_file_existence",
      "tests/test_pair_binning.py::TestMassBinEdges::test_custom_config",
      "tests/test_pair_binning.py::TestMassBinEdges::test_default_config",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_additivity_checked_and_holds",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_console_output_contains_required_text",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_convention_order_preserved",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_output_file_written",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_output_schema",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_pair_fraction_equals_n_pairs_over_n_galaxies",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_preflight_gate_preserves_output_on_failure",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_returned_dicts_structure",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_single_convention",
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
      "tests/test_statistical.py::TestMaxwellMoments::test_mean[1]",
      "tests/test_statistical.py::TestMaxwellMoments::test_mean[2]",
      "tests/test_statistical.py::TestMaxwellMoments::test_mean[3]",
      "tests/test_statistical.py::TestMaxwellMoments::test_mean[4]",
      "tests/test_statistical.py::TestMaxwellMoments::test_mean[5]",
      "tests/test_statistical.py::TestMaxwellMoments::test_second_moment[0]",
      "tests/test_statistical.py::TestMaxwellMoments::test_second_moment[1]",
      "tests/test_statistical.py::TestMaxwellMoments::test_second_moment[2]",
      "tests/test_statistical.py::TestMaxwellMoments::test_second_moment[3]",
      "tests/test_statistical.py::TestMaxwellMoments::test_second_moment[4]",
      "tests/test_statistical.py::TestMaxwellMoments::test_second_moment[5]",
      "tests/test_statistical.py::TestMaxwellMoments::test_skewness_scale_invariant",
      "tests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[0]",
      "tests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[1]",
      "tests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[2]",
      "tests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[3]",
      "tests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[4]",
      "tests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[5]"
    ],
    "failed_nodes": [],
    "unparsable": false,
    "collect_t
```
