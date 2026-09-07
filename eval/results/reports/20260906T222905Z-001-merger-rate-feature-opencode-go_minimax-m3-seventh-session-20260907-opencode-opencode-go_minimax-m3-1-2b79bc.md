# Trial report: 20260906T222905Z-001-merger-rate-feature-opencode-go_minimax-m3-seventh-session-20260907-opencode-opencode-go_minimax-m3-1-2b79bc

- Task: `001-merger-rate-feature`
- Model: `opencode-go/minimax-m3` (harness: opencode)
- Model duration: 399.8s | venv setup: 24.7s | timed out: False | committed: False
- Changed files: src/calc.py, src/config.py, src/merger_rate.py, tests/test_merger_rate.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 91.3 / 100

## Judged: readability 75% of weight, maintainability 25% of weight (judge claude-opus-5, status ok)

## Composite score: 85.3 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 95% |
| test_adequacy | automated | 25 | 78% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 100% |
| readability | judged | 8 | 75% |
| maintainability | judged | 7 | 25% |

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
    "raw_tail": "sts/test_hA.py::test_C08_check_slope_consistency PASSED                [ 75%]\ntests/test_hA.py::test_C09_collapsed_predictor PASSED                    [ 77%]\ntests/test_hA.py::test_C10_y_centring_numerical_stability PASSED         [ 78%]\ntests/test_hA.py::test_C11_validation_result_keys FAILED                 [ 80%]\ntests/test_hA.py::test_C12_validation_rejects_malformed_stored_redshift_before_fit PASSED [ 81%]\ntests/test_hA.py::test_C13_validation_prints_insufficient_data FAILED    [ 83%]\ntests/test_hA.py::test_C14_mass_bin_is_index_not_string PASSED           [ 85%]\ntests/test_hA.py::test_C15_consistent_is_python_bool_or_none PASSED      [ 86%]\ntests/test_hB.py::test_E01_slice1_additive_schema PASSED                 [ 88%]\ntests/test_hB.py::test_E02_denominator_from_full_catalog PASSED          [ 90%]\ntests/test_hB.py::test_E03_box_size_from_catalog_not_config PASSED       [ 91%]\ntests/test_hB.py::test_E04_per_file_box_size_used PASSED                 [ 93%]\ntests/test_hB.py::test_E05_preflight_atomicity_sha256 PASSED             [ 95%]\ntests/test_hB.py::test_E06_output_schema PASSED                          [ 96%]\ntests/test_hB.py::test_E07_end_to_end_science PASSED                     [ 98%]\ntests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha PASSED [100%]\n\n=================================== FAILURES ===================================\n_________________ test_B15_rejection_messages_name_the_reason __________________\ntests/test_hA.py:401: in test_B15_rejection_messages_name_the_reason\n    assert_rejects_with(\"non-negative\", MR.compute_pair_fraction,\ntests/test_hA.py:57: in assert_rejects_with\n    with pytest.raises(AssertionError, match=pattern):\n         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE   AssertionError: Regex pattern did not match.\nE     Expected regex: 'non-negative'\nE     Actual message: 'compute_pair_fraction: n_pairs has negative values'\n_______________________ test_C11_validation_result_keys ________________________\ntests/test_hA.py:589: in test_C11_validation_result_keys\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:557: in _parse_bin_line\n    assert all((mass, slope, slope_err, expected, excluded, status)), line\nE   AssertionError:   bin 0: mass [8.0, 8.5) | slope = 1.000000 +/-0.096602 | expected = 1.0 | n_excluded = 0 | PASS\nE   assert False\nE    +  where False = all((<re.Match object; span=(14, 24), match='[8.0, 8.5)'>, <re.Match object; span=(27, 43), match='slope = 1.000000'>, <re.Match object; span=(44, 55), match='+/-0.096602'>, <re.Match object; span=(58, 72), match='expected = 1.0'>, <re.Match object; span=(75, 89), match='n_excluded = 0'>, None))\n_________________ test_C13_validation_prints_insufficient_data _________________\ntests/test_hA.py:640: in test_C13_validation_prints_insufficient_data\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:557: in _parse_bin_line\n    assert all((mass, slope, slope_err, expected, excluded, status)), line\nE   AssertionError:   bin 0: mass [8.0, 8.5) | slope = nan nan | expected = 1.0 | n_excluded = 4 | insufficient data\nE   assert False\nE    +  where False = all((<re.Match object; span=(14, 24), match='[8.0, 8.5)'>, <re.Match object; span=(27, 38), match='slope = nan'>, None, <re.Match object; span=(45, 59), match='expected = 1.0'>, <re.Match object; span=(62, 76), match='n_excluded = 4'>, <re.Match object; span=(79, 96), match='insufficient data'>))\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_B15_rejection_messages_name_the_reason - Assert...\nFAILED tests/test_hA.py::test_C11_validation_result_keys - AssertionError:   ...\nFAILED tests/test_hA.py::test_C13_validation_prints_insufficient_data - Asser...\n========================= 3 failed, 58 passed in 1.98s =========================\n",
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
      "tests/test_merger_rate.py::TestBoxSizeProvenance::test_box_size_mpc_comes_from_catalog_not_config",
      "tests/test_merger_rate.py::TestCalcAdditions::test_calc_exposes_count_galaxies_per_mass_bin",
      "tests/test_merger_rate.py::TestCalcAdditions::test_calc_exposes_mass_bin_edges",
      "tests/test_merger_rate.py::TestCalcAdditions::test_count_sum_excludes_upper_edge_galaxies",
      "tests/test_merger_rate.py::TestCalcAdditions::test_count_uses_right_open_upper_edge",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_asserts_non_finite_n_sigma",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_asserts_non_positive_n_sigma",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_far_outside_returns_false",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_expected_slope_returns_false",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_slope_err_returns_false",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_slope_returns_false",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_slope_err_non_positive_returns_false",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_within_range_returns_true",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_acceptance_criterion_exact_values",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reduced_identity_holds",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_scalar_forms",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_merger_fraction_outside_unit_interval",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_mismatched_shapes",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_negative_or_non_finite_array_values",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_non_1d_arrays",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_non_finite_box_size",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_non_integer_valued_galaxies",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_non_positive_box_size",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_non_positive_timescale",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_zero_galaxies_with_nonzero_f_pair",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_sigma_f_pair_zero_yields_exact_zero_sigma_rate",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_with_both_zero_is_valid",
      "tests/test_merger_rate.py::TestComputePairFraction::test_acceptance_criterion_exact_values",
      "tests/test_merger_rate.py::TestComputePairFraction::test_accepts_integer_dtype",
      "tests/test_merger_rate.py::TestComputePairFraction::test_accepts_integer_valued_float64",
      "tests/test_merger_rate.py::TestComputePairFraction::test_mismatched_shapes_asserts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_negative_counts_asserts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_non_1d_asserts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_non_finite_counts_asserts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_non_integer_valued_counts_asserts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_pairs_without_galaxies_asserts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_zero_zero_yields_exact_zero",
      "tests/test_merger_rate.py::TestConfigKeys::test_no_pre_existing_key_changed",
      "tests/test_merger_rate.py::TestConfigKeys::test_three_keys_added_with_expected_defaults",
      "tests/test_merger_rate.py::TestDenominatorFromFullCatalog::test_count_sum_matches_log_mass_min_leq_mass_lt_log_mass_max",
      "tests/test_merger_rate.py::TestDocstrings::test_compute_merger_rate_docstring_contains_required_sentence",
      "tests/test_merger_rate.py::TestDocstrings::test_compute_pair_fraction_docstring_contains_required_sentence",
      "tests/test_merger_rate.py::TestEndToEnd::test_end_to_end_consistency_on_generated_mock",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fewer_than_two_usable_points_returns_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_n_excluded_mixed",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_power_law_recovered",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_provably_weighted_versus_unweighted",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_rejects_malformed_redshifts",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_rejects_mismatched_shapes",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_rejects_non_1d_inputs",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_slope_err_matches_hand_computed",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_two_plus_points_one_redshift_returns_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_two_plus_points_with_collapsed_predictor_returns_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_two_usable_points_returns_finite_fit",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_bad_box_size_scalar_forms",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_attr",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_dataset",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_file",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_non_positive_box_size",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_out_of_range_mass_bin",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_wrong_length_dataset",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_returns_known_values_against_hand_written_fixture",
      "tests/test_merger_rate.py::TestMergerRateModuleExports::test_merger_rate_exposes_required_callables",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_bad_scalar_forms",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_non_finite_alpha",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_non_finite_t0",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_non_finite_z",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_non_positive_t0",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_z_le_minus_one",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_t0_2_5_alpha_minus_0_5_at_z_3_is_1_25",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_z_zero_equals_t0_exactly",
      "tests/test_merger_rate.py::TestPipelineWritesNewDatasetAndAttr::test_pre_existing_datasets_and_attrs_unchanged",
      "tests/test_merger_rate.py::TestPipelineWritesNewDatasetAndAttr::test_results_file_has_box_size_mpc_attr",
      "tests/test_merger_rate.py::TestPipelineWritesNewDatasetAndAttr::test_results_file_has_n_galaxies_per_mass_bin",
      "tests/test_merger_rate.py::TestRunMergerRateCalculationBoxSizeUsed::test_per_file_box_size_used_not_config",
      "tests/test_merger_rate.py::TestRunMergerRateCalculationMassBinByGate::test_asserts_mass_bin_by_primary",
      "tests/test_merger_rate.py::TestRunMergerRateCalculationOutputSchema::test_written_output_schema_and_contents",
      "tests/test_merger_rate.py::TestRunMergerRateCalculationPreflightLeavesSentinel::test_malformed_redshift_attr_forms_each_rejected[(2+0j)]",
      "tests/test_merger_rate.py::TestRunMergerRateCalculationPreflightLeavesSentinel::test_malformed_redshift_attr_forms_each_rejected[2.0]",
      "tests/test_merger_rate.py::TestRunMergerRateCalculationPreflightLeavesSentinel::test_malformed_redshift_attr_forms_each_rejected[True]",
      "tests/test_merger_rate.py::TestRunMergerRateCalculationPreflightLeavesSentinel::test_malformed_redshift_attr_forms_each_rejected[bad_attr3]",
      "tests/test_merger_rate.py::TestRunMergerRateCalculationPreflightLeavesSentinel::test_malformed_redshift_attr_leaves_sentinel_unchanged",
      "tests/test_merger_rate.py::TestRunMergerRateCalculationPreflightLeavesSentinel::test_mismatched_redshift_attr_leaves_sentinel_unchanged",
      "tests/test_merger_rate.py::TestRunMergerRateCalculationPreflightLeavesSentinel::test_missing_pair_file_leaves_sentinel_unchanged",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_bin_lines_contain_required_fields",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_expected_slope_tracks_non_default_alpha",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_fails_on_malformed_stored_redshift",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_heading_states_injected_model_recovery",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_prints_insufficient_data_for_nan_slope_bin",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_reports_n_excluded_per_bin",
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
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_m
```
