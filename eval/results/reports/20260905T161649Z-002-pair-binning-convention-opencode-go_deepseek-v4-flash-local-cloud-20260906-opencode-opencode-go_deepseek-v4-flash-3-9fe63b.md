# Trial report: 20260905T161649Z-002-pair-binning-convention-opencode-go_deepseek-v4-flash-local-cloud-20260906-opencode-opencode-go_deepseek-v4-flash-3-9fe63b

- Task: `002-pair-binning-convention`
- Model: `opencode-go/deepseek-v4-flash` (harness: opencode)
- Model duration: 863.2s | venv setup: 29.5s | timed out: False | committed: False
- Changed files: src/config.py, src/pair_binning.py, tests/test_pair_binning.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 91.2 / 100

## Judged: readability 75% of weight, maintainability 50% of weight (judge claude-opus-5, status ok)

## Composite score: 87.0 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 97% |
| test_adequacy | automated | 25 | 76% |
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
| rejection_semantics_of_the_pure_counting_functions | 41 | 44 | 0.93 |
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
    "passed": 134,
    "failed": [
      "tests/test_hA.py::test_A06_galaxy_count_rejections[bad4-keywords4]",
      "tests/test_hA.py::test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_pairs_per_mass_bin]",
      "tests/test_hA.py::test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_excluded_pairs]",
      "tests/test_hA.py::test_A22_pair_fraction_rejections[npair10-ngal10-keywords10]",
      "tests/test_hA.py::test_A25_check_additivity_rejections[a16-a26-a36-keywords6]",
      "tests/test_hA.py::test_A30_check_additivity_exact_above_2_53"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "97%]\ntests/test_hB.py::test_B24_additivity_false_from_check_propagates_everywhere PASSED [ 98%]\ntests/test_hB.py::test_B26_full_driver_run_on_nondefault_bin_grid PASSED [ 99%]\ntests/test_hB.py::test_B27_low_mass_ratio_pair_not_refiltered PASSED     [100%]\n\n=================================== FAILURES ===================================\n_______________ test_A06_galaxy_count_rejections[bad4-keywords4] _______________\ntests/test_hA.py:149: in test_A06_galaxy_count_rejections\n    assert rejects(PB.count_galaxies_per_mass_bin, bad, BASE) == \"assert\"\nE   AssertionError: assert None == 'assert'\nE    +  where None = rejects(<function count_galaxies_per_mass_bin at 0x107955c70>, array(['8.0'], dtype='<U3'), {'box_size': 500.0, 'redshifts': [2.0, 3.0, 4.0, 5.0], 'log_mass_min': 8.0, 'log_mass_max': 11.0, ...})\nE    +    where <function count_galaxies_per_mass_bin at 0x107955c70> = PB.count_galaxies_per_mass_bin\n_ test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_pairs_per_mass_bin] _\ntests/test_hA.py:260: in test_A16_pair_array_rejections\n    assert rejects(fn, primary, secondary, \"primary\", BASE) == \"assert\"\nE   AssertionError: assert None == 'assert'\nE    +  where None = rejects(<function count_pairs_per_mass_bin at 0x107955d20>, array(['9.0'], dtype='<U3'), array(['8.0'], dtype='<U3'), 'primary', {'box_size': 500.0, 'redshifts': [2.0, 3.0, 4.0, 5.0], 'log_mass_min': 8.0, 'log_mass_max': 11.0, ...})\n_ test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_excluded_pairs] _\ntests/test_hA.py:260: in test_A16_pair_array_rejections\n    assert rejects(fn, primary, secondary, \"primary\", BASE) == \"assert\"\nE   AssertionError: assert None == 'assert'\nE    +  where None = rejects(<function count_excluded_pairs at 0x107955dd0>, array(['9.0'], dtype='<U3'), array(['8.0'], dtype='<U3'), 'primary', {'box_size': 500.0, 'redshifts': [2.0, 3.0, 4.0, 5.0], 'log_mass_min': 8.0, 'log_mass_max': 11.0, ...})\n_________ test_A22_pair_fraction_rejections[npair10-ngal10-keywords10] _________\ntests/test_hA.py:327: in test_A22_pair_fraction_rejections\n    assert rejects(PB.compute_pair_fraction, npair, ngal) == \"assert\"\nE   AssertionError: assert None == 'assert'\nE    +  where None = rejects(<function compute_pair_fraction at 0x107955e80>, array(['1'], dtype='<U1'), array(['10'], dtype='<U2'))\nE    +    where <function compute_pair_fraction at 0x107955e80> = PB.compute_pair_fraction\n_________ test_A25_check_additivity_rejections[a16-a26-a36-keywords6] __________\ntests/test_hA.py:360: in test_A25_check_additivity_rejections\n    assert rejects(PB.check_additivity, a1, a2, a3) == \"assert\"\nE   AssertionError: assert None == 'assert'\nE    +  where None = rejects(<function check_additivity at 0x107955f30>, ['1'], ['1'], ['2'])\nE    +    where <function check_additivity at 0x107955f30> = PB.check_additivity\n__________________ test_A30_check_additivity_exact_above_2_53 __________________\ntests/test_hA.py:476: in test_A30_check_additivity_exact_above_2_53\n    assert PB.check_additivity(big, one, big) is False\nE   assert True is False\nE    +  where True = <function check_additivity at 0x107955f30>(array([9007199254740992]), array([1]), array([9007199254740992]))\nE    +    where <function check_additivity at 0x107955f30> = PB.check_additivity\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A06_galaxy_count_rejections[bad4-keywords4] - A...\nFAILED tests/test_hA.py::test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_pairs_per_mass_bin]\nFAILED tests/test_hA.py::test_A16_pair_array_rejections[primary5-secondary5-keywords5-count_excluded_pairs]\nFAILED tests/test_hA.py::test_A22_pair_fraction_rejections[npair10-ngal10-keywords10]\nFAILED tests/test_hA.py::test_A25_check_additivity_rejections[a16-a26-a36-keywords6]\nFAILED tests/test_hA.py::test_A30_check_additivity_exact_above_2_53 - assert ...\n======================== 6 failed, 134 passed in 2.24s =========================\n",
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
        "passed": 41,
        "collected": 44,
        "fraction": 0.9318181818181818,
        "uncollected": false,
        "failed_nodes": [
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
      "tests/test_pair_binning.py::TestCheckAdditivity::test_false_returns_not_raises",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejections[a0-b0-c0]",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejections[a1-b1-c1]",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejections[a2-b2-c2]",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejections[a3-b3-c3]",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejections[a4-b4-c4]",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejections[a5-b5-c5]",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_rejections[a6-b6-c6]",
      "tests/test_pair_binning.py::TestCheckAdditivity::test_true",
      "tests/test_pair_binning.py::TestComputePairFraction::test_accepts_integer_dtype_and_integer_valued_float",
      "tests/test_pair_binning.py::TestComputePairFraction::test_docstring_exact_sentence",
      "tests/test_pair_binning.py::TestComputePairFraction::test_example_values",
      "tests/test_pair_binning.py::TestComputePairFraction::test_n_pairs_positive_requires_n_galaxies_positive",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejections[n_pairs0-n_galaxies0]",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejections[n_pairs1-n_galaxies1]",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejections[n_pairs2-n_galaxies2]",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejections[n_pairs3-n_galaxies3]",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejections[n_pairs4-n_galaxies4]",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejections[n_pairs5-n_galaxies5]",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejections[n_pairs6-n_galaxies6]",
      "tests/test_pair_binning.py::TestComputePairFraction::test_rejections[n_pairs7-n_galaxies7]",
      "tests/test_pair_binning.py::TestComputePairFraction::test_zero_error_exactly_zero[n_pairs0-n_galaxies0]",
      "tests/test_pair_binning.py::TestComputePairFraction::test_zero_error_exactly_zero[n_pairs1-n_galaxies1]",
      "tests/test_pair_binning.py::TestComputePairFraction::test_zero_error_exactly_zero[n_pairs2-n_galaxies2]",
      "tests/test_pair_binning.py::TestComputePairFraction::test_zero_error_exactly_zero[n_pairs3-n_galaxies3]",
      "tests/test_pair_binning.py::TestConfig::test_existing_keys_unchanged",
      "tests/test_pair_binning.py::TestConfig::test_pair_binning_conventions_key_added",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_convention_independent[mean]",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_convention_independent[nonsense]",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_convention_independent[primary]",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_convention_independent[secondary]",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_convention_independent[total]",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_custom_config_counts",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_default_example_exact",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_no_mass_bin_by_key_at_all",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_rejections[bad0]",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_rejections[bad1]",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_rejections[bad2]",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_rejections[bad3]",
      "tests/test_pair_binning.py::TestCountGalaxiesPerMassBin::test_zero_length",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_excluded_pairs_sample",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_exclusion_sum_rule",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_reject_bad_arrays[mp0-ms0]",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_reject_bad_arrays[mp1-ms1]",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_reject_bad_arrays[mp2-ms2]",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_reject_bad_arrays[mp3-ms3]",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_reject_bad_arrays[mp4-ms4]",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_reject_bad_arrays[mp5-ms5]",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_reject_bad_arrays[mp6-ms6]",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_reject_bad_convention[5]",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_reject_bad_convention[None]",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_reject_bad_convention[mean]",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_reject_bad_convention[nonsense]",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_reject_bad_convention[total]",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_same_bin_and_diff_bin_pairs",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_sample_conventions",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_vectors_distinct_and_either_off_diagonal",
      "tests/test_pair_binning.py::TestCountPairsPerMassBin::test_zero_length",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_additivity_and_exclusion_on_mock[2.0]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_additivity_and_exclusion_on_mock[3.0]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_additivity_and_exclusion_on_mock[4.0]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_additivity_and_exclusion_on_mock[5.0]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_counts_vary_by_convention_and_match_hand_computed",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_galaxy_at_log_mass_max_unbinned",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_honours_single_convention",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_honours_two_conventions_in_order",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_keys_exactly",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_n_pairs_total_matches_rows",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejections[bad_mass_ratio_string]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejections[bad_mass_ratio_value]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejections[bad_max_sep_nonscalar]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejections[bad_max_sep_value]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejections[bad_redshift_bytes]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejections[bad_redshift_complex]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejections[bad_redshift_nonscalar]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejections[bad_redshift_string]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejections[bad_redshift_value]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejections[missing_data_file]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejections[missing_mass_primary]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejections[missing_mass_ratio_attr]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejections[missing_mass_secondary]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejections[missing_max_sep_attr]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejections[missing_redshift_attr]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejections[missing_results_file]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejections[unequal_lengths]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_invalid_config_conventions[conventions0]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_invalid_config_conventions[conventions1]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_invalid_config_conventions[conventions2]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_invalid_config_conventions[conventions3]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_invalid_config_conventions[conventions4]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_invalid_config_conventions[conventions6]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_rejects_invalid_config_conventions[primary]",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_stored_bin_assignment_not_used",
      "tests/test_pair_binning.py::TestLoadSnapshotCounts::test_sum_n_galaxies_matches_selected_catalog",
      "tests/test_pair_binning.py::TestMassBinEdges::test_default_edges",
      "tests/test_pair_binning.py::TestMassBinEdges::test_edges_derived_from_config_not_defaults",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_additivity_true_on_mock",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_console_summary",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_console_summary_not_checked",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_conventions_track_config",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_end_to_end_independent_recompute",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_invalid_conventions_leave_sentinel_untouched[conventions0]",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_invalid_conventions_leave_sentinel_untouched[conventions1]",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_invalid_conventions_leave_sentinel_untouched[conventions2]",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_invalid_conventions_leave_sentinel_untouched[conventions3]",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_invalid_conventions_leave_sentinel_untouched[conventions4]",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_invalid_conventions_leave_sentinel_untouched[conventions6]",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_invalid_conventions_leave_sentinel_untouched[primary]",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_pair_fraction_formula_same_denominator",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_persisted_matches_returned",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_preflight_gate_leaves_sentinel_untouched[bad_mass_ratio_value]",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_preflight_gate_leaves_sentinel_untouched[bad_max_sep_value]",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_preflight_gate_leaves_sentinel_untouched[bad_redshift_string]",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_preflight_gate_leaves_sentinel_untouched[bad_redshift_value]",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_preflight_gate_leaves_sentinel_untouched[missing_data_file]",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_preflight_gate_leaves_sentinel_untouched[missing_results_file]",
      "tests/test_pair_binning.py::TestRunBinningComparison::test_schema_on_mock",
      "tests/test_pair_binning.py:
```
