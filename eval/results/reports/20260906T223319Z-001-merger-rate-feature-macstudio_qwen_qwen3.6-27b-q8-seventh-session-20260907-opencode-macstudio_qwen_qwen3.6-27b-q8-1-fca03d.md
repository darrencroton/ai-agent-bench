# Trial report: 20260906T223319Z-001-merger-rate-feature-macstudio_qwen_qwen3.6-27b-q8-seventh-session-20260907-opencode-macstudio_qwen_qwen3.6-27b-q8-1-fca03d

- Task: `001-merger-rate-feature`
- Model: `macstudio/qwen/qwen3.6-27b-q8` (harness: opencode)
- Model duration: 4603.4s | venv setup: 25.2s | timed out: False | committed: False
- Changed files: src/calc.py, src/config.py, src/merger_rate.py, tests/test_merger_rate.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 83.6 / 100

## Judged: readability 75% of weight, maintainability 50% of weight (judge claude-opus-5, status ok)

## Composite score: 80.6 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 95% |
| test_adequacy | automated | 25 | 52% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 100% |
| readability | judged | 8 | 75% |
| maintainability | judged | 7 | 50% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| calc_galaxy_denominator | 4 | 4 | 1.00 |
| persistence_schema_provenance | 5 | 5 | 1.00 |
| load_pair_counts_rejections | 8 | 8 | 1.00 |
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
    "passed": 58,
    "failed": [
      "tests/test_hA.py::test_B15_rejection_messages_name_the_reason",
      "tests/test_hA.py::test_C11_validation_result_keys",
      "tests/test_hA.py::test_C13_validation_prints_insufficient_data"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "PASSED            [ 72%]\ntests/test_hA.py::test_C07_malformed_redshifts_and_rank PASSED           [ 73%]\ntests/test_hA.py::test_C08_check_slope_consistency PASSED                [ 75%]\ntests/test_hA.py::test_C09_collapsed_predictor PASSED                    [ 77%]\ntests/test_hA.py::test_C10_y_centring_numerical_stability PASSED         [ 78%]\ntests/test_hA.py::test_C11_validation_result_keys FAILED                 [ 80%]\ntests/test_hA.py::test_C12_validation_rejects_malformed_stored_redshift_before_fit PASSED [ 81%]\ntests/test_hA.py::test_C13_validation_prints_insufficient_data FAILED    [ 83%]\ntests/test_hA.py::test_C14_mass_bin_is_index_not_string PASSED           [ 85%]\ntests/test_hA.py::test_C15_consistent_is_python_bool_or_none PASSED      [ 86%]\ntests/test_hB.py::test_E01_slice1_additive_schema PASSED                 [ 88%]\ntests/test_hB.py::test_E02_denominator_from_full_catalog PASSED          [ 90%]\ntests/test_hB.py::test_E03_box_size_from_catalog_not_config PASSED       [ 91%]\ntests/test_hB.py::test_E04_per_file_box_size_used PASSED                 [ 93%]\ntests/test_hB.py::test_E05_preflight_atomicity_sha256 PASSED             [ 95%]\ntests/test_hB.py::test_E06_output_schema PASSED                          [ 96%]\ntests/test_hB.py::test_E07_end_to_end_science PASSED                     [ 98%]\ntests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha PASSED [100%]\n\n=================================== FAILURES ===================================\n_________________ test_B15_rejection_messages_name_the_reason __________________\ntests/test_hA.py:401: in test_B15_rejection_messages_name_the_reason\n    assert_rejects_with(\"non-negative\", MR.compute_pair_fraction,\ntests/test_hA.py:57: in assert_rejects_with\n    with pytest.raises(AssertionError, match=pattern):\n         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE   AssertionError: Regex pattern did not match.\nE     Expected regex: 'non-negative'\nE     Actual message: 'n_pairs contains negative counts'\n_______________________ test_C11_validation_result_keys ________________________\ntests/test_hA.py:589: in test_C11_validation_result_keys\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:557: in _parse_bin_line\n    assert all((mass, slope, slope_err, expected, excluded, status)), line\nE   AssertionError: Bin 0 ([8.0, 8.5)): slope=1.0000 +/- 0.0966, expected=+1.0, n_excluded=0 \u2014 PASS\nE   assert False\nE    +  where False = all((<re.Match object; span=(7, 17), match='[8.0, 8.5)'>, <re.Match object; span=(20, 32), match='slope=1.0000'>, <re.Match object; span=(33, 43), match='+/- 0.0966'>, <re.Match object; span=(45, 58), match='expected=+1.0'>, <re.Match object; span=(60, 72), match='n_excluded=0'>, None))\n_________________ test_C13_validation_prints_insufficient_data _________________\ntests/test_hA.py:640: in test_C13_validation_prints_insufficient_data\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:557: in _parse_bin_line\n    assert all((mass, slope, slope_err, expected, excluded, status)), line\nE   AssertionError: Bin 0 ([8.0, 8.5)): slope=N/A +/- N/A, expected=+1.0, n_excluded=4 \u2014 insufficient data\nE   assert False\nE    +  where False = all((<re.Match object; span=(7, 17), match='[8.0, 8.5)'>, None, None, <re.Match object; span=(39, 52), match='expected=+1.0'>, <re.Match object; span=(54, 66), match='n_excluded=4'>, <re.Match object; span=(69, 86), match='insufficient data'>))\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_B15_rejection_messages_name_the_reason - Assert...\nFAILED tests/test_hA.py::test_C11_validation_result_keys - AssertionError: Bi...\nFAILED tests/test_hA.py::test_C13_validation_prints_insufficient_data - Asser...\n========================= 3 failed, 58 passed in 2.00s =========================\n",
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
        "passed": 8,
        "collected": 8,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
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
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_assert_bad_n_sigma",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_assert_non_finite_n_sigma",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_far_outside",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_negative_slope_err",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_expected",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_slope",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_within_range",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_zero_slope_err",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_assert_n_gal_zero_with_nonzero_f_pair",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_basic_computation",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reduced_identity",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalars[-1.0-2.2-0.6-negative box]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalars[0.0-2.2-0.6-zero box]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalars[500.0--1.0-0.6-negative timescale]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalars[500.0-0.0-0.6-zero timescale]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalars[500.0-2.2--0.1-negative fraction]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalars[500.0-2.2-0.0-zero fraction]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalars[500.0-2.2-1.5-fraction > 1]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_mismatched_array_shapes",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_negative_array_values",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_non_integer_n_galaxies",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_sigma_f_pair_zero_yields_exact_zero",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_valid_n_gal_zero_with_both_zero",
      "tests/test_merger_rate.py::TestComputePairFraction::test_accepts_int_dtypes",
      "tests/test_merger_rate.py::TestComputePairFraction::test_accepts_integer_valued_float64",
      "tests/test_merger_rate.py::TestComputePairFraction::test_assert_n_pairs_gt_0_requires_n_gal_gt_0",
      "tests/test_merger_rate.py::TestComputePairFraction::test_basic_values",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_mismatched_shapes",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_negative_counts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_1d",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_finite",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_integer_valued",
      "tests/test_merger_rate.py::TestComputePairFraction::test_zero_zero_yields_zero_not_nan",
      "tests/test_merger_rate.py::TestConfigKeys::test_default_values",
      "tests/test_merger_rate.py::TestConfigKeys::test_new_keys_exist",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_assert_malformed_redshifts[-1.0]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_assert_malformed_redshifts[inf]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_assert_malformed_redshifts[nan]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_assert_shape_violation",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_exact_power_law_recovery",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fewer_than_2_usable_returns_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_n_excluded_correct",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_provably_weighted",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_single_redshift_all_usable_returns_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_slope_err_two_points",
      "tests/test_merger_rate.py::TestGalaxyCountDenominator::test_count_sum_matches_selected_catalog",
      "tests/test_merger_rate.py::TestGalaxyCountDenominator::test_exact_upper_edge_excluded",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_excludes_sentinel_minus_one",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size_mpc[(500+0j)]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size_mpc[-1.0]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size_mpc[0.0]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size_mpc[500_0]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size_mpc[500_1]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size_mpc[False]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size_mpc[True]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size_mpc[bad_box10]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size_mpc[bad_box9]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size_mpc[inf]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size_mpc[nan]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_dataset",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_file",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_out_of_range_mass_bin",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_wrong_length_n_galaxies",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_returns_known_values",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_at_zero_equals_t0",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_non_default_parameters",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_bad_config_params[-1.0--1.0-negative t0]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_bad_config_params[0.0--1.0-zero t0]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_bad_config_params[2.2-inf-inf alpha]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_bad_config_params[2.2-nan-nan alpha]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_bad_config_params[inf--1.0-inf t0]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_bad_config_params[nan--1.0-nan t0]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_bad_z[-1.0-z <= -1]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_bad_z[-2.0-z < -1]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_bad_z[inf-infinite z]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_bad_z[nan-non-finite z]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_form_for_z[(1+0j)-z]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_form_for_z[1.0-z0]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_form_for_z[1.0-z1]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_form_for_z[False-z]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_form_for_z[True-z]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_form_for_z[val3-z]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_form_for_z[val4-z]",
      "tests/test_merger_rate.py::TestNewDatasetsInResultsFiles::test_box_size_from_catalog_not_config",
      "tests/test_merger_rate.py::TestNewDatasetsInResultsFiles::test_new_dataset_and_attr_present",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_box_size_from_file_not_config",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_docstrings_contain_required_sentence",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_mass_bin_by_assertion",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_output_schema_and_values",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_malformed_redshift_attr",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_missing_file_leaves_sentinel_untouched",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_redshift_mismatch_leaves_sentinel_untouched",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_end_to_end_mock_data_consistent",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_expected_slope_tracks_alpha",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_malformed_stored_redshift_fails_before_fit",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_prints_insufficient_data_and_heading",
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
  
```
