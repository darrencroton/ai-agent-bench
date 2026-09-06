# Trial report: 20260906T091622Z-001-merger-rate-feature-opencode-go_longcat-2.0-sixth-session-20260906-longcat-2.0-opencode-opencode-go_longcat-2.0-3-498adb

- Task: `001-merger-rate-feature`
- Model: `opencode-go/longcat-2.0` (harness: opencode)
- Model duration: 1966.3s | venv setup: 28.9s | timed out: False | committed: False
- Changed files: src/calc.py, src/config.py, src/merger_rate.py, tests/test_merger_rate.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 87.1 / 100

## Judged: readability 50% of weight, maintainability 25% of weight (judge claude-opus-5, status ok)

## Composite score: 79.8 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 95% |
| test_adequacy | automated | 25 | 68% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 91% |
| readability | judged | 8 | 50% |
| maintainability | judged | 7 | 25% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| calc_galaxy_denominator | 4 | 4 | 1.00 |
| persistence_schema_provenance | 5 | 5 | 1.00 |
| load_pair_counts_rejections | 8 | 8 | 1.00 |
| pair_fraction_core | 10 | 10 | 1.00 |
| merger_timescale_and_rate_conversion | 13 | 13 | 1.00 |
| run_merger_rate_calculation_pipeline | 4 | 4 | 1.00 |
| redshift_evolution_fit_and_consistency | 10 | 10 | 1.00 |
| validation_reporting_and_e2e | 4 | 7 | 0.57 |

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
    "passed": 58,
    "failed": [
      "tests/test_hA.py::test_C11_validation_result_keys",
      "tests/test_hB.py::test_E07_end_to_end_science",
      "tests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "5_rejection_messages_name_the_reason PASSED     [ 62%]\ntests/test_hA.py::test_C01_exact_power_law PASSED                        [ 63%]\ntests/test_hA.py::test_C02_provably_weighted PASSED                      [ 65%]\ntests/test_hA.py::test_C03_two_point_slope_err_pinned PASSED             [ 67%]\ntests/test_hA.py::test_C04_two_usable_with_exclusions_finite PASSED      [ 68%]\ntests/test_hA.py::test_C05_fewer_than_two_usable PASSED                  [ 70%]\ntests/test_hA.py::test_C06_single_redshift_returns_nan PASSED            [ 72%]\ntests/test_hA.py::test_C07_malformed_redshifts_and_rank PASSED           [ 73%]\ntests/test_hA.py::test_C08_check_slope_consistency PASSED                [ 75%]\ntests/test_hA.py::test_C09_collapsed_predictor PASSED                    [ 77%]\ntests/test_hA.py::test_C10_y_centring_numerical_stability PASSED         [ 78%]\ntests/test_hA.py::test_C11_validation_result_keys FAILED                 [ 80%]\ntests/test_hA.py::test_C12_validation_rejects_malformed_stored_redshift_before_fit PASSED [ 81%]\ntests/test_hA.py::test_C13_validation_prints_insufficient_data PASSED    [ 83%]\ntests/test_hA.py::test_C14_mass_bin_is_index_not_string PASSED           [ 85%]\ntests/test_hA.py::test_C15_consistent_is_python_bool_or_none PASSED      [ 86%]\ntests/test_hB.py::test_E01_slice1_additive_schema PASSED                 [ 88%]\ntests/test_hB.py::test_E02_denominator_from_full_catalog PASSED          [ 90%]\ntests/test_hB.py::test_E03_box_size_from_catalog_not_config PASSED       [ 91%]\ntests/test_hB.py::test_E04_per_file_box_size_used PASSED                 [ 93%]\ntests/test_hB.py::test_E05_preflight_atomicity_sha256 PASSED             [ 95%]\ntests/test_hB.py::test_E06_output_schema PASSED                          [ 96%]\ntests/test_hB.py::test_E07_end_to_end_science FAILED                     [ 98%]\ntests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha FAILED [100%]\n\n=================================== FAILURES ===================================\n_______________________ test_C11_validation_result_keys ________________________\ntests/test_hA.py:589: in test_C11_validation_result_keys\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:557: in _parse_bin_line\n    assert all((mass, slope, slope_err, expected, excluded, status)), line\nE   AssertionError: bin 0: mass [8.0, 8.5)  slope = +1.0000 +/- 0.0966  expected = +1.0000  n_excluded = 0  True\nE   assert False\nE    +  where False = all((<re.Match object; span=(12, 22), match='[8.0, 8.5)'>, <re.Match object; span=(24, 39), match='slope = +1.0000'>, <re.Match object; span=(40, 50), match='+/- 0.0966'>, <re.Match object; span=(52, 70), match='expected = +1.0000'>, <re.Match object; span=(72, 86), match='n_excluded = 0'>, None))\n_________________________ test_E07_end_to_end_science __________________________\ntests/test_hB.py:294: in test_E07_end_to_end_science\n    assert d[\"consistent\"] is True, d\nE   AssertionError: {'mass_bin': 0, 'slope': np.float64(0.9267762335105318), 'slope_err': np.float64(0.13946676597215996), 'intercept': np.float64(-6.319665846646199), ...}\nE   assert np.True_ is True\n_______________ test_E09_expected_slope_tracks_nondefault_alpha ________________\ntests/test_hB.py:322: in test_E09_expected_slope_tracks_nondefault_alpha\n    assert d[\"consistent\"] is True, d\nE   AssertionError: {'mass_bin': 0, 'slope': np.float64(0.6267762335105316), 'slope_err': np.float64(0.13946676597215996), 'intercept': np.float64(-6.319665846646201), ...}\nE   assert np.True_ is True\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_C11_validation_result_keys - AssertionError: bi...\nFAILED tests/test_hB.py::test_E07_end_to_end_science - AssertionError: {'mass...\nFAILED tests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha - As...\n========================= 3 failed, 58 passed in 1.86s =========================\n",
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
        "passed": 10,
        "collected": 10,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
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
        "passed": 4,
        "collected": 7,
        "fraction": 0.5714285714285714,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_C11_validation_result_keys",
          "tests/test_hB.py::test_E07_end_to_end_science",
          "tests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha"
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
      "tests/test_merger_rate.py::TestCalcIntegration::test_box_size_mpc_from_catalog_not_config",
      "tests/test_merger_rate.py::TestCalcIntegration::test_denominator_from_full_catalog",
      "tests/test_merger_rate.py::TestCalcIntegration::test_existing_datasets_unchanged",
      "tests/test_merger_rate.py::TestCalcIntegration::test_new_dataset_and_attr_present",
      "tests/test_merger_rate.py::TestCalcIntegration::test_sum_below_inclusive_count",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_far_outside",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_invalid_n_sigma",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_expected",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_slope",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_slope_err",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_positive_slope_err",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_within_range",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_0d_array_box_size_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_basic_values",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_bool_box_size_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_complex_box_size_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_merger_fraction_out_of_range_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_mismatched_arrays_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_negative_array_values_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_non_1d_arrays_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_non_finite_array_values_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_non_finite_box_size_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_non_finite_timescale_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_non_integer_n_galaxies_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_non_positive_box_size_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_non_positive_timescale_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reduced_identity",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_string_box_size_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_with_nonzero_f_pair_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_with_nonzero_sigma_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_with_zero_f_pair_valid",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_sigma_yields_zero_sigma_rate",
      "tests/test_merger_rate.py::TestComputePairFraction::test_basic_values",
      "tests/test_merger_rate.py::TestComputePairFraction::test_integer_dtype_accepted",
      "tests/test_merger_rate.py::TestComputePairFraction::test_integer_valued_float64_accepted",
      "tests/test_merger_rate.py::TestComputePairFraction::test_mismatched_shapes_rejected",
      "tests/test_merger_rate.py::TestComputePairFraction::test_negative_counts_rejected",
      "tests/test_merger_rate.py::TestComputePairFraction::test_non_1d_rejected",
      "tests/test_merger_rate.py::TestComputePairFraction::test_non_finite_rejected",
      "tests/test_merger_rate.py::TestComputePairFraction::test_non_integer_valued_rejected",
      "tests/test_merger_rate.py::TestComputePairFraction::test_pairs_exist_without_galaxies_rejected",
      "tests/test_merger_rate.py::TestComputePairFraction::test_zero_pairs_zero_galaxies",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_all_above_range",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_all_below_range",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_empty_input",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_exact_upper_edge_excluded",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_interior_edge_goes_to_upper_bin",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_returns_int_array",
      "tests/test_merger_rate.py::TestDocstrings::test_compute_merger_rate_docstring",
      "tests/test_merger_rate.py::TestDocstrings::test_compute_pair_fraction_docstring",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_collapsed_predictor_returns_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_exact_power_law",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_exactly_two_usable_points_finite",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fewer_than_two_usable_returns_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_hand_computed_slope_err",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_malformed_redshifts_assert",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_non_1d_assert",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_non_finite_rate_err_excluded",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_non_finite_rate_excluded",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_non_positive_rate_excluded",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_provably_weighted",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_shape_mismatch_assert",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_single_redshift_returns_nan",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_box_size_mpc_complex_rejected",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_box_size_mpc_negative_rejected",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_box_size_mpc_non_scalar_rejected",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_box_size_mpc_string_rejected",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_excludes_mass_bin_minus_one",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_loads_known_values",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_missing_attr_rejected",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_missing_dataset_rejected",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_missing_file_rejected",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_out_of_range_index",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_wrong_length_n_galaxies_rejected",
      "tests/test_merger_rate.py::TestMassBinEdges::test_default_config",
      "tests/test_merger_rate.py::TestMassBinEdges::test_merger_rate_mass_bin_edges",
      "tests/test_merger_rate.py::TestMergerTimescale::test_non_default_values",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_0d_array_z",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_bool_z",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_non_finite_alpha",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_non_finite_t0",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_non_finite_z",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_non_positive_t0",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_string_z",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_z_le_minus_one",
      "tests/test_merger_rate.py::TestMergerTimescale::test_z0_equals_t0",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_mass_bin_by_not_primary_rejected",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_output_schema",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_malformed_redshift_attr_untouched",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_mismatched_redshift_untouched",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_missing_file_untouched",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_rates_finite_and_nonnegative",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_uses_per_file_box_size",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_end_to_end_on_mock_data",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_expected_slope_from_config",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_expected_slope_non_default_alpha",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_heading_states_mock_data",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_malformed_stored_redshift_fails",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_n_excluded_per_bin",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_prints_insufficient_data",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_stored_redshift_le_minus_one_fails",
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
      "tests/test_statistical.py:
```
