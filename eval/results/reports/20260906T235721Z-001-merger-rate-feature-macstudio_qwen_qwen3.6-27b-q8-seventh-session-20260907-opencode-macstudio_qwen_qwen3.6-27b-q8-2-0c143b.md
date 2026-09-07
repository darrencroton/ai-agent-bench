# Trial report: 20260906T235721Z-001-merger-rate-feature-macstudio_qwen_qwen3.6-27b-q8-seventh-session-20260907-opencode-macstudio_qwen_qwen3.6-27b-q8-2-0c143b

- Task: `001-merger-rate-feature`
- Model: `macstudio/qwen/qwen3.6-27b-q8` (harness: opencode)
- Model duration: 6600.6s | venv setup: 25.8s | timed out: False | committed: False
- Changed files: src/calc.py, src/config.py, src/merger_rate.py, tests/test_merger_rate.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 82.6 / 100

## Judged: readability 75% of weight, maintainability 50% of weight (judge claude-opus-5, status ok)

## Composite score: 79.7 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 92% |
| test_adequacy | automated | 25 | 53% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 100% |
| readability | judged | 8 | 75% |
| maintainability | judged | 7 | 50% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| calc_galaxy_denominator | 4 | 4 | 1.00 |
| persistence_schema_provenance | 5 | 5 | 1.00 |
| load_pair_counts_rejections | 6 | 8 | 0.75 |
| pair_fraction_core | 9 | 10 | 0.90 |
| merger_timescale_and_rate_conversion | 13 | 13 | 1.00 |
| run_merger_rate_calculation_pipeline | 4 | 4 | 1.00 |
| redshift_evolution_fit_and_consistency | 10 | 10 | 1.00 |
| validation_reporting_and_e2e | 5 | 7 | 0.71 |

## Provenance

```json
{
  "rubric_version": 2,
  "rubric_sha256": "a4a93e1f5fd3b17c7ad7f873dd74a65ff2c74da8a1f759c4ac5e3e8a1d7a9102",
  "rubric_profile": "default",
  "task_contract_sha256": "ba2fd08a32821553bca1847a3c956ddd680ddb140c6db6da5ad131918ee23bd7",
  "evaluator_content_sha256": "fe9fc605d85bfeee8dbf7669ef4eb4db367fb7d2ef0d51b8335e7c27d6993913",
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
    "total": 61,
    "passed": 56,
    "failed": [
      "tests/test_hA.py::test_A15_load_pair_counts_bad_bin_index",
      "tests/test_hA.py::test_A19_load_pair_counts_wrong_length",
      "tests/test_hA.py::test_B15_rejection_messages_name_the_reason",
      "tests/test_hA.py::test_C11_validation_result_keys",
      "tests/test_hA.py::test_C13_validation_prints_insufficient_data"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "lity PASSED         [ 78%]\ntests/test_hA.py::test_C11_validation_result_keys FAILED                 [ 80%]\ntests/test_hA.py::test_C12_validation_rejects_malformed_stored_redshift_before_fit PASSED [ 81%]\ntests/test_hA.py::test_C13_validation_prints_insufficient_data FAILED    [ 83%]\ntests/test_hA.py::test_C14_mass_bin_is_index_not_string PASSED           [ 85%]\ntests/test_hA.py::test_C15_consistent_is_python_bool_or_none PASSED      [ 86%]\ntests/test_hB.py::test_E01_slice1_additive_schema PASSED                 [ 88%]\ntests/test_hB.py::test_E02_denominator_from_full_catalog PASSED          [ 90%]\ntests/test_hB.py::test_E03_box_size_from_catalog_not_config PASSED       [ 91%]\ntests/test_hB.py::test_E04_per_file_box_size_used PASSED                 [ 93%]\ntests/test_hB.py::test_E05_preflight_atomicity_sha256 PASSED             [ 95%]\ntests/test_hB.py::test_E06_output_schema PASSED                          [ 96%]\ntests/test_hB.py::test_E07_end_to_end_science PASSED                     [ 98%]\ntests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha PASSED [100%]\n\n=================================== FAILURES ===================================\n___________________ test_A15_load_pair_counts_bad_bin_index ____________________\ntests/test_hA.py:184: in test_A15_load_pair_counts_bad_bin_index\n    assert r == \"assert\", r\nE   AssertionError: None\nE   assert None == 'assert'\n____________________ test_A19_load_pair_counts_wrong_length ____________________\ntests/test_hA.py:211: in test_A19_load_pair_counts_wrong_length\n    assert rejects(MR._load_pair_counts, 2.0, c) == \"assert\"\nE   AssertionError: assert None == 'assert'\nE    +  where None = rejects(<function _load_pair_counts at 0x10e15e610>, 2.0, {'box_size': 500.0, 'redshifts': [2.0, 3.0, 4.0, 5.0], 'log_mass_min': 8.0, 'log_mass_max': 11.0, ...})\nE    +    where <function _load_pair_counts at 0x10e15e610> = MR._load_pair_counts\n_________________ test_B15_rejection_messages_name_the_reason __________________\ntests/test_hA.py:399: in test_B15_rejection_messages_name_the_reason\n    assert_rejects_with(\"shape\", MR.compute_pair_fraction,\ntests/test_hA.py:57: in assert_rejects_with\n    with pytest.raises(AssertionError, match=pattern):\n         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE   AssertionError: Regex pattern did not match.\nE     Expected regex: 'shape'\nE     Actual message: 'Shape mismatch: n_pairs (2,) vs n_galaxies (1,)'\n_______________________ test_C11_validation_result_keys ________________________\ntests/test_hA.py:589: in test_C11_validation_result_keys\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:544: in _parse_bin_line\n    assert len(lines) == 1, f\"expected one output line for bin {b}, got {lines!r}\"\nE   AssertionError: expected one output line for bin 0, got []\nE   assert 0 == 1\nE    +  where 0 = len([])\n_________________ test_C13_validation_prints_insufficient_data _________________\ntests/test_hA.py:640: in test_C13_validation_prints_insufficient_data\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:544: in _parse_bin_line\n    assert len(lines) == 1, f\"expected one output line for bin {b}, got {lines!r}\"\nE   AssertionError: expected one output line for bin 0, got []\nE   assert 0 == 1\nE    +  where 0 = len([])\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A15_load_pair_counts_bad_bin_index - AssertionE...\nFAILED tests/test_hA.py::test_A19_load_pair_counts_wrong_length - AssertionEr...\nFAILED tests/test_hA.py::test_B15_rejection_messages_name_the_reason - Assert...\nFAILED tests/test_hA.py::test_C11_validation_result_keys - AssertionError: ex...\nFAILED tests/test_hA.py::test_C13_validation_prints_insufficient_data - Asser...\n========================= 5 failed, 56 passed in 1.96s =========================\n",
    "stderr_tail": "",
    "obligations": [
      {
        "id": "calc_galaxy_denominator",
        "passed": 4,
        "collected": 4,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "persistence_schema_provenance",
        "passed": 5,
        "collected": 5,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "load_pair_counts_rejections",
        "passed": 6,
        "collected": 8,
        "fraction": 0.75,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_A15_load_pair_counts_bad_bin_index",
          "tests/test_hA.py::test_A19_load_pair_counts_wrong_length"
        ]
      },
      {
        "id": "pair_fraction_core",
        "passed": 9,
        "collected": 10,
        "fraction": 0.9,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_B15_rejection_messages_name_the_reason"
        ]
      },
      {
        "id": "merger_timescale_and_rate_conversion",
        "passed": 13,
        "collected": 13,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "run_merger_rate_calculation_pipeline",
        "passed": 4,
        "collected": 4,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "redshift_evolution_fit_and_consistency",
        "passed": 10,
        "collected": 10,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "validation_reporting_and_e2e",
        "passed": 5,
        "collected": 7,
        "fraction": 0.7142857142857143,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_C11_validation_result_keys",
          "tests/test_hA.py::test_C13_validation_prints_insufficient_data"
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
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_custom_n_sigma",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_far_outside",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_invalid_n_sigma_asserts",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_negative_slope_err",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_expected",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_slope",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_slope_err",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_within_range",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_zero_slope_err",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_asserts_n_gal_zero_with_nonzero_f_pair",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_exact_zero_sigma_when_sigma_f_pair_zero",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_pinned_values",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reduced_identity",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bool_scalar",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_box_size[-1.0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_box_size[0.0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_box_size[inf]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_box_size[nan]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_timescale[-1.0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_timescale[0.0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_timescale[inf]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_timescale[nan]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_mf_out_of_range",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_mismatched_arrays",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_ndarray_scalar",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_negative_array_values",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_non_integer_n_galaxies",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_string_scalar",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_valid_n_gal_zero_with_both_zero",
      "tests/test_merger_rate.py::TestComputePairFraction::test_accepts_int_dtype",
      "tests/test_merger_rate.py::TestComputePairFraction::test_accepts_integer_valued_float64",
      "tests/test_merger_rate.py::TestComputePairFraction::test_asserts_n_pairs_gt_0_with_n_gal_0",
      "tests/test_merger_rate.py::TestComputePairFraction::test_f_pair_can_exceed_one",
      "tests/test_merger_rate.py::TestComputePairFraction::test_pinned_values",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_mismatched_shapes",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_negative_counts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_1d",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_finite",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_integer_valued",
      "tests/test_merger_rate.py::TestComputePairFraction::test_zero_zero_returns_exact_zero",
      "tests/test_merger_rate.py::TestConfigKeys::test_default_values",
      "tests/test_merger_rate.py::TestConfigKeys::test_existing_keys_unchanged",
      "tests/test_merger_rate.py::TestConfigKeys::test_new_keys_exist",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_excludes_at_upper_edge",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_excludes_below_range",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_includes_interior_edge",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_length_equals_n_bins",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_pinned_input",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_sum_matches_selected_catalog",
      "tests/test_merger_rate.py::TestEndToEndMockData::test_slope_consistency_on_generated_mock",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_exact_power_law_recovery",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fewer_than_2_usable_returns_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_malformed_redshift_asserts[-1.0]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_malformed_redshift_asserts[-2.0]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_malformed_redshift_asserts[inf]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_malformed_redshift_asserts[nan]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_n_excluded_correct",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_provably_weighted",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_rank_violation_asserts",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_shape_violation_asserts",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_single_redshift_returns_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_slope_err_hand_computed",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_two_points_returns_finite",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_accepts_int_scalar_box_size",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_excludes_sentinel_minus_one",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_known_values",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_bool_box_size",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size[-1.0]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size[0.0]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size[inf]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size[nan]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_attr_box_size",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_dataset",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_file",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_out_of_range_index",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_string_box_size",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_wrong_n_gal_length",
      "tests/test_merger_rate.py::TestMassBinEdges::test_default_config",
      "tests/test_merger_rate.py::TestMassBinEdges::test_matches_pair_finder_formula",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_accepts_int_z",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_at_zero_redshift",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_pinned_calculation",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_bool_input",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_complex_input",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_ndarray_input",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_non_finite_alpha",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_non_finite_z",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_non_positive_t0",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_string_input",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_z_leq_minus_one",
      "tests/test_merger_rate.py::TestResultsFileNewDatasets::test_box_size_from_catalog_not_config",
      "tests/test_merger_rate.py::TestResultsFileNewDatasets::test_existing_datasets_unchanged",
      "tests/test_merger_rate.py::TestResultsFileNewDatasets::test_new_dataset_and_attr_present",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_docstrings_contain_required_sentence",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_mass_bin_by_primary_required",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_output_schema",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_malformed_redshift_attr_preserves_sentinel",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_missing_file_preserves_sentinel",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_redshift_mismatch_preserves_sentinel",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_uses_per_file_box_size_not_config",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_expected_slope_tracks_alpha",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_insufficient_data_printed_and_returned",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_malformed_stored_redshift_fails_before_fit",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_result_dict_keys",
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
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_a
```
