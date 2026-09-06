# Trial report: 20260906T083225Z-001-merger-rate-feature-claude-sonnet-5-sixth-session-20260906-claude-sonnet-5-claude-claude-sonnet-5-2-4c31cb

- Task: `001-merger-rate-feature`
- Model: `claude-sonnet-5` (harness: claude)
- Model duration: 793.0s | venv setup: 28.8s | timed out: False | committed: False
- Changed files: src/calc.py, src/config.py, src/merger_rate.py, tests/test_merger_rate.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 87.9 / 100

## Judged: readability 100% of weight, maintainability 75% of weight (judge claude-opus-5, status ok)

## Composite score: 88.0 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 92% |
| test_adequacy | automated | 25 | 75% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 91% |
| readability | judged | 8 | 100% |
| maintainability | judged | 7 | 75% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| calc_galaxy_denominator | 4 | 4 | 1.00 |
| persistence_schema_provenance | 5 | 5 | 1.00 |
| load_pair_counts_rejections | 8 | 8 | 1.00 |
| pair_fraction_core | 9 | 10 | 0.90 |
| merger_timescale_and_rate_conversion | 13 | 13 | 1.00 |
| run_merger_rate_calculation_pipeline | 3 | 4 | 0.75 |
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
    "total": 61,
    "passed": 57,
    "failed": [
      "tests/test_hA.py::test_B15_rejection_messages_name_the_reason",
      "tests/test_hA.py::test_C11_validation_result_keys",
      "tests/test_hA.py::test_C13_validation_prints_insufficient_data",
      "tests/test_hB.py::test_E05_preflight_atomicity_sha256"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "ests/test_hA.py::test_C04_two_usable_with_exclusions_finite PASSED      [ 68%]\ntests/test_hA.py::test_C05_fewer_than_two_usable PASSED                  [ 70%]\ntests/test_hA.py::test_C06_single_redshift_returns_nan PASSED            [ 72%]\ntests/test_hA.py::test_C07_malformed_redshifts_and_rank PASSED           [ 73%]\ntests/test_hA.py::test_C08_check_slope_consistency PASSED                [ 75%]\ntests/test_hA.py::test_C09_collapsed_predictor PASSED                    [ 77%]\ntests/test_hA.py::test_C10_y_centring_numerical_stability PASSED         [ 78%]\ntests/test_hA.py::test_C11_validation_result_keys FAILED                 [ 80%]\ntests/test_hA.py::test_C12_validation_rejects_malformed_stored_redshift_before_fit PASSED [ 81%]\ntests/test_hA.py::test_C13_validation_prints_insufficient_data FAILED    [ 83%]\ntests/test_hA.py::test_C14_mass_bin_is_index_not_string PASSED           [ 85%]\ntests/test_hA.py::test_C15_consistent_is_python_bool_or_none PASSED      [ 86%]\ntests/test_hB.py::test_E01_slice1_additive_schema PASSED                 [ 88%]\ntests/test_hB.py::test_E02_denominator_from_full_catalog PASSED          [ 90%]\ntests/test_hB.py::test_E03_box_size_from_catalog_not_config PASSED       [ 91%]\ntests/test_hB.py::test_E04_per_file_box_size_used PASSED                 [ 93%]\ntests/test_hB.py::test_E05_preflight_atomicity_sha256 FAILED             [ 95%]\ntests/test_hB.py::test_E06_output_schema PASSED                          [ 96%]\ntests/test_hB.py::test_E07_end_to_end_science PASSED                     [ 98%]\ntests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha PASSED [100%]\n\n=================================== FAILURES ===================================\n_________________ test_B15_rejection_messages_name_the_reason __________________\ntests/test_hA.py:401: in test_B15_rejection_messages_name_the_reason\n    assert_rejects_with(\"non-negative\", MR.compute_pair_fraction,\ntests/test_hA.py:57: in assert_rejects_with\n    with pytest.raises(AssertionError, match=pattern):\n         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE   AssertionError: Regex pattern did not match.\nE     Expected regex: 'non-negative'\nE     Actual message: 'n_pairs contains negative values'\n_______________________ test_C11_validation_result_keys ________________________\ntests/test_hA.py:589: in test_C11_validation_result_keys\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:544: in _parse_bin_line\n    assert len(lines) == 1, f\"expected one output line for bin {b}, got {lines!r}\"\nE   AssertionError: expected one output line for bin 0, got []\nE   assert 0 == 1\nE    +  where 0 = len([])\n_________________ test_C13_validation_prints_insufficient_data _________________\ntests/test_hA.py:640: in test_C13_validation_prints_insufficient_data\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:544: in _parse_bin_line\n    assert len(lines) == 1, f\"expected one output line for bin {b}, got {lines!r}\"\nE   AssertionError: expected one output line for bin 0, got []\nE   assert 0 == 1\nE    +  where 0 = len([])\n_____________________ test_E05_preflight_atomicity_sha256 ______________________\ntests/test_hB.py:230: in test_E05_preflight_atomicity_sha256\n    assert not failures, failures\nE   AssertionError: [('z_missing', 'exception', 'KeyError')]\nE   assert not [('z_missing', 'exception', 'KeyError')]\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_B15_rejection_messages_name_the_reason - Assert...\nFAILED tests/test_hA.py::test_C11_validation_result_keys - AssertionError: ex...\nFAILED tests/test_hA.py::test_C13_validation_prints_insufficient_data - Asser...\nFAILED tests/test_hB.py::test_E05_preflight_atomicity_sha256 - AssertionError...\n========================= 4 failed, 57 passed in 1.78s =========================\n",
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
        "passed": 3,
        "collected": 4,
        "fraction": 0.75,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hB.py::test_E05_preflight_atomicity_sha256"
        ]
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
      "tests/test_merger_rate.py::TestCalcSavesNewDatasetAndAttr::test_box_size_mpc_comes_from_catalog_not_config",
      "tests/test_merger_rate.py::TestCalcSavesNewDatasetAndAttr::test_generated_results_have_new_dataset_and_attr_and_old_fields_intact",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_asserts_on_invalid_n_sigma",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_far_outside",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_for_non_finite_inputs",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_for_non_positive_slope_err",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_true_within_range",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_docstring_states_plan_convention",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_pinned_values",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reduced_identity",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_forms[(500+1j)]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_forms[500_0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_forms[500_1]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_forms[bad_value3]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_forms[bad_value4]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_merger_fraction_outside_0_1",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_mismatched_or_non_1d_arrays",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_negative_or_non_finite_array_values",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_non_finite_or_non_positive_box_size_and_timescale",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_non_integer_valued_n_galaxies",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_with_both_zero_is_valid",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_with_nonzero_f_pair_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_sigma_f_pair_gives_exact_zero_sigma_rate",
      "tests/test_merger_rate.py::TestComputePairFraction::test_accepts_integer_dtype_and_integer_valued_float64",
      "tests/test_merger_rate.py::TestComputePairFraction::test_docstring_states_plan_convention",
      "tests/test_merger_rate.py::TestComputePairFraction::test_pinned_values",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_mismatched_shapes",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_negative_counts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_1d_input",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_finite_counts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_integer_valued_counts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_pairs_without_galaxies",
      "tests/test_merger_rate.py::TestComputePairFraction::test_zero_pairs_zero_galaxies_is_exact_zero",
      "tests/test_merger_rate.py::TestConfigKeys::test_existing_keys_unchanged",
      "tests/test_merger_rate.py::TestConfigKeys::test_new_keys_present_with_documented_defaults",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_denominator_is_full_selected_catalog_exclusive_upper_edge",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_pinned_edge_exclusion_example",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_returns_int_array_of_length_n_mass_bins",
      "tests/test_merger_rate.py::TestEndToEndMockDataValidation::test_slope_consistency_holds_for_every_sufficiently_sampled_mass_bin",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_exact_power_law_recovered",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_exactly_two_usable_points_returns_finite_fit",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fewer_than_two_usable_points_returns_nan_without_raising",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fit_is_provably_weighted_heteroscedastic_outlier",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_malformed_redshifts_raise",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_shape_and_rank_violations_raise",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_shared_single_redshift_returns_nan_without_raising",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_slope_err_matches_hand_computed_normal_equations",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_reads_known_values_in_bin_index_order_and_excludes_sentinel",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size_mpc_scalar_forms[(500+1j)]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size_mpc_scalar_forms[500.0_0]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size_mpc_scalar_forms[500.0_1]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_mass_bin_index_outside_valid_range",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_dataset_or_attr",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_file",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_non_positive_and_non_finite_box_size_mpc",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_non_scalar_box_size_mpc",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_wrong_length_n_galaxies_per_mass_bin",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_non_default_params",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_forms[(2+1j)]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_forms[2.0_0]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_forms[2.0_1]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_forms[bad_value3]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_forms[bad_value4]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_non_finite_alpha",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_non_positive_or_non_finite_gyr0",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_z_leq_minus_one_and_non_finite",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_z0_equals_gyr0_exactly",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_output_schema_shapes_dtypes_and_finiteness",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_output_values_match_independent_recomputation_in_order",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_per_file_box_size_used_not_config_box_size",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_malformed_redshift_attr_leaves_sentinel_untouched[bad_redshift1]",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_malformed_redshift_attr_leaves_sentinel_untouched[not-a-number]",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_mismatched_redshift_leaves_sentinel_untouched",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_missing_file_leaves_sentinel_untouched",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_rejects_mass_bin_by_not_primary",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_every_line_has_parseable_fields",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_expected_slope_tracks_non_default_alpha",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_fails_on_malformed_stored_redshift_before_any_fit",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_insufficient_data_reported_with_n_excluded_and_heading",
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
 
```
