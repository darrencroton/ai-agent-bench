# Trial report: 20260906T224113Z-001-merger-rate-feature-opencode-go_glm-5.3-flash-seventh-session-20260907-opencode-opencode-go_glm-5.3-flash-2-4e9a66

- Task: `001-merger-rate-feature`
- Model: `opencode-go/glm-5.3-flash` (harness: opencode)
- Model duration: 1401.2s | venv setup: 24.5s | timed out: False | committed: False
- Changed files: src/calc.py, src/config.py, src/merger_rate.py, tests/test_merger_rate.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 94.1 / 100

## Judged: readability 75% of weight, maintainability 75% of weight (judge claude-opus-5, status ok)

## Composite score: 91.2 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 95% |
| test_adequacy | automated | 25 | 88% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 100% |
| readability | judged | 8 | 75% |
| maintainability | judged | 7 | 75% |

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
    "raw_tail": "tests/test_hA.py::test_C08_check_slope_consistency PASSED                [ 75%]\ntests/test_hA.py::test_C09_collapsed_predictor PASSED                    [ 77%]\ntests/test_hA.py::test_C10_y_centring_numerical_stability PASSED         [ 78%]\ntests/test_hA.py::test_C11_validation_result_keys FAILED                 [ 80%]\ntests/test_hA.py::test_C12_validation_rejects_malformed_stored_redshift_before_fit PASSED [ 81%]\ntests/test_hA.py::test_C13_validation_prints_insufficient_data FAILED    [ 83%]\ntests/test_hA.py::test_C14_mass_bin_is_index_not_string PASSED           [ 85%]\ntests/test_hA.py::test_C15_consistent_is_python_bool_or_none PASSED      [ 86%]\ntests/test_hB.py::test_E01_slice1_additive_schema PASSED                 [ 88%]\ntests/test_hB.py::test_E02_denominator_from_full_catalog PASSED          [ 90%]\ntests/test_hB.py::test_E03_box_size_from_catalog_not_config PASSED       [ 91%]\ntests/test_hB.py::test_E04_per_file_box_size_used PASSED                 [ 93%]\ntests/test_hB.py::test_E05_preflight_atomicity_sha256 PASSED             [ 95%]\ntests/test_hB.py::test_E06_output_schema PASSED                          [ 96%]\ntests/test_hB.py::test_E07_end_to_end_science PASSED                     [ 98%]\ntests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha PASSED [100%]\n\n=================================== FAILURES ===================================\n_________________ test_B15_rejection_messages_name_the_reason __________________\ntests/test_hA.py:401: in test_B15_rejection_messages_name_the_reason\n    assert_rejects_with(\"non-negative\", MR.compute_pair_fraction,\ntests/test_hA.py:57: in assert_rejects_with\n    with pytest.raises(AssertionError, match=pattern):\n         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE   AssertionError: Regex pattern did not match.\nE     Expected regex: 'non-negative'\nE     Actual message: 'n_pairs contains negative counts'\n_______________________ test_C11_validation_result_keys ________________________\ntests/test_hA.py:589: in test_C11_validation_result_keys\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:557: in _parse_bin_line\n    assert all((mass, slope, slope_err, expected, excluded, status)), line\nE   AssertionError:   mass bin 0 [8.000, 8.500): slope=+1.00000 +/- 0.09660, expected=+1.00000, n_excluded=0 -> consistent\nE   assert False\nE    +  where False = all((<re.Match object; span=(13, 27), match='[8.000, 8.500)'>, <re.Match object; span=(29, 43), match='slope=+1.00000'>, <re.Match object; span=(44, 55), match='+/- 0.09660'>, <re.Match object; span=(57, 74), match='expected=+1.00000'>, <re.Match object; span=(76, 88), match='n_excluded=0'>, None))\n_________________ test_C13_validation_prints_insufficient_data _________________\ntests/test_hA.py:640: in test_C13_validation_prints_insufficient_data\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:557: in _parse_bin_line\n    assert all((mass, slope, slope_err, expected, excluded, status)), line\nE   AssertionError:   mass bin 0 [8.000, 8.500): slope=+nan +/- nan, expected=+1.00000, n_excluded=4 -> insufficient data\nE   assert False\nE    +  where False = all((<re.Match object; span=(13, 27), match='[8.000, 8.500)'>, None, <re.Match object; span=(40, 47), match='+/- nan'>, <re.Match object; span=(49, 66), match='expected=+1.00000'>, <re.Match object; span=(68, 80), match='n_excluded=4'>, <re.Match object; span=(84, 101), match='insufficient data'>))\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_B15_rejection_messages_name_the_reason - Assert...\nFAILED tests/test_hA.py::test_C11_validation_result_keys - AssertionError:   ...\nFAILED tests/test_hA.py::test_C13_validation_prints_insufficient_data - Asser...\n========================= 3 failed, 58 passed in 1.94s =========================\n",
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
      "tests/test_merger_rate.py::TestCalcGalaxyCounts::test_count_is_1d_int_of_n_mass_bins",
      "tests/test_merger_rate.py::TestCalcGalaxyCounts::test_empty_input_gives_zero_counts",
      "tests/test_merger_rate.py::TestCalcGalaxyCounts::test_pinned_bin_assignment",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_exact_boundary_is_strict",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_far_outside_false",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_invalid_n_sigma_asserts",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_inputs_false",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_positive_slope_err_false",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_within_range_true",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_accepts_numpy_scalar_forms",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_docstring_states_convention",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_output_shape_and_dtype",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_pinned_values",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reduced_identity_for_n_pairs",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_array_inputs",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_scalars",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_forms",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_with_nonzero_f_pair_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_with_nonzero_sigma_f_pair_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_with_zero_fractions_is_valid",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_sigma_f_pair_gives_zero_sigma_rate",
      "tests/test_merger_rate.py::TestComputePairFraction::test_accepts_integer_dtypes_and_integer_valued_floats",
      "tests/test_merger_rate.py::TestComputePairFraction::test_docstring_states_convention",
      "tests/test_merger_rate.py::TestComputePairFraction::test_pinned_values",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_mismatched_shapes",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_negative_counts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_1d",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_finite_counts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_integer_valued_counts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_requires_galaxies_where_pairs_exist",
      "tests/test_merger_rate.py::TestComputePairFraction::test_zero_pair_bin_is_exactly_zero",
      "tests/test_merger_rate.py::TestConfigKeys::test_existing_keys_unchanged",
      "tests/test_merger_rate.py::TestConfigKeys::test_merger_rate_keys_added",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_collapsed_predictor_returns_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_exact_power_law_recovered",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fewer_than_two_usable_points_returns_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fit_is_provably_weighted",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_malformed_redshifts_fail",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_shape_and_rank_violations_fail",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_single_distinct_redshift_returns_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_single_usable_point_returns_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_slope_err_matches_hand_computed_normal_equations",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_two_usable_points_give_finite_fit",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_box_size_mpc_scalar_forms",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_empty_mass_bin_dataset",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_hand_fixture_values_in_bin_order",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_box_size_attr",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_file",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_mass_bin_dataset",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_n_galaxies_dataset",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_out_of_range_mass_bin_indices",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_wrong_length_n_galaxies",
      "tests/test_merger_rate.py::TestMergerTimescale::test_accepted_scalar_forms",
      "tests/test_merger_rate.py::TestMergerTimescale::test_at_z0_equals_gyr0_exactly",
      "tests/test_merger_rate.py::TestMergerTimescale::test_nondefault_parameters",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_invalid_alpha",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_invalid_gyr0",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_invalid_z",
      "tests/test_merger_rate.py::TestMergerTimescale::test_scalar_power_law",
      "tests/test_merger_rate.py::TestRegeneratedResultsFiles::test_box_size_mpc_comes_from_catalog_not_config",
      "tests/test_merger_rate.py::TestRegeneratedResultsFiles::test_box_size_mpc_uses_catalog_value_when_they_differ",
      "tests/test_merger_rate.py::TestRegeneratedResultsFiles::test_denominator_is_full_selected_catalog",
      "tests/test_merger_rate.py::TestRegeneratedResultsFiles::test_new_dataset_and_attr_present_and_old_unchanged",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_output_schema",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_leaves_output_untouched",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_missing_file_names_path",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_requires_primary_binning",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_uses_per_file_box_size",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_all_bins_consistent_on_generated_mock",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_expected_slope_tracks_non_default_alpha",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_fails_on_malformed_stored_redshift",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_insufficient_data_lines_and_return_structure",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_validation_output_on_mock",
      "tests/test_merger_rate.py::TestSavePairsExtension::test_save_pairs_writes_new_dataset_and_attr",
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
      "tests/test_statistical.py::TestRedshiftIndependence::tes
```
