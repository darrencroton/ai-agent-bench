# Trial report: 20260906T085848Z-001-merger-rate-feature-opencode-go_mimo-v2.5-pro-sixth-session-20260906-mimo-v2.5-pro-opencode-opencode-go_mimo-v2.5-pro-3-e0765b

- Task: `001-merger-rate-feature`
- Model: `opencode-go/mimo-v2.5-pro` (harness: opencode)
- Model duration: 1043.1s | venv setup: 29.3s | timed out: False | committed: False
- Changed files: src/calc.py, src/config.py, src/merger_rate.py, tests/test_merger_rate.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 81.2 / 100

## Judged: readability 75% of weight, maintainability 50% of weight (judge claude-opus-5, status ok)

## Composite score: 78.5 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 92% |
| test_adequacy | automated | 25 | 55% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 83% |
| readability | judged | 8 | 75% |
| maintainability | judged | 7 | 50% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| calc_galaxy_denominator | 4 | 4 | 1.00 |
| persistence_schema_provenance | 5 | 5 | 1.00 |
| load_pair_counts_rejections | 8 | 8 | 1.00 |
| pair_fraction_core | 9 | 10 | 0.90 |
| merger_timescale_and_rate_conversion | 12 | 13 | 0.92 |
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
    "passed": 56,
    "failed": [
      "tests/test_hA.py::test_B14_docstring_wording",
      "tests/test_hA.py::test_B15_rejection_messages_name_the_reason",
      "tests/test_hA.py::test_C11_validation_result_keys",
      "tests/test_hB.py::test_E07_end_to_end_science",
      "tests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "_E03_box_size_from_catalog_not_config PASSED       [ 91%]\ntests/test_hB.py::test_E04_per_file_box_size_used PASSED                 [ 93%]\ntests/test_hB.py::test_E05_preflight_atomicity_sha256 PASSED             [ 95%]\ntests/test_hB.py::test_E06_output_schema PASSED                          [ 96%]\ntests/test_hB.py::test_E07_end_to_end_science FAILED                     [ 98%]\ntests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha FAILED [100%]\n\n=================================== FAILURES ===================================\n__________________________ test_B14_docstring_wording __________________________\ntests/test_hA.py:395: in test_B14_docstring_wording\n    assert required in doc, f\"{fn.__name__} lacks the required uncertainty wording\"\nE   AssertionError: compute_pair_fraction lacks the required uncertainty wording\nE   assert \"Uncertainty follows Task 001's plug-in Poisson-error convention; it is not a confidence interval.\" in \"Compute pair fraction and its Poisson uncertainty per mass bin.\\n\\nUncertainty follows Task 001's plug-in Poisson-error convention; it is not\\na confidence interval.\\n\\nParameters\\n----------\\nn_pairs : 1D array-like, non-negative integer-valued\\nn_galaxies : 1D array-like, non-negative integer-valued\\n\\nReturns\\n-------\\nf_pair : 1D float array\\nsigma_f_pair : 1D float array\"\n_________________ test_B15_rejection_messages_name_the_reason __________________\ntests/test_hA.py:399: in test_B15_rejection_messages_name_the_reason\n    assert_rejects_with(\"shape\", MR.compute_pair_fraction,\ntests/test_hA.py:57: in assert_rejects_with\n    with pytest.raises(AssertionError, match=pattern):\n         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE   AssertionError: Regex pattern did not match.\nE     Expected regex: 'shape'\nE     Actual message: 'Shape mismatch: n_pairs (2,) vs n_galaxies (1,)'\n_______________________ test_C11_validation_result_keys ________________________\ntests/test_hA.py:589: in test_C11_validation_result_keys\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:557: in _parse_bin_line\n    assert all((mass, slope, slope_err, expected, excluded, status)), line\nE   AssertionError:   Bin 0 [8.0, 8.5): slope=1.000000 +/- 0.096602, expected=1.000000, n_excluded=0, PASS\nE   assert False\nE    +  where False = all((<re.Match object; span=(8, 18), match='[8.0, 8.5)'>, <re.Match object; span=(20, 34), match='slope=1.000000'>, <re.Match object; span=(35, 47), match='+/- 0.096602'>, <re.Match object; span=(49, 66), match='expected=1.000000'>, <re.Match object; span=(68, 80), match='n_excluded=0'>, None))\n_________________________ test_E07_end_to_end_science __________________________\ntests/test_hB.py:294: in test_E07_end_to_end_science\n    assert d[\"consistent\"] is True, d\nE   AssertionError: {'mass_bin': 0, 'slope': np.float64(0.926776233510532), 'slope_err': np.float64(0.13946676597215996), 'intercept': np.float64(-6.3196658466462), ...}\nE   assert np.True_ is True\n_______________ test_E09_expected_slope_tracks_nondefault_alpha ________________\ntests/test_hB.py:322: in test_E09_expected_slope_tracks_nondefault_alpha\n    assert d[\"consistent\"] is True, d\nE   AssertionError: {'mass_bin': 0, 'slope': np.float64(0.6267762335105314), 'slope_err': np.float64(0.13946676597215996), 'intercept': np.float64(-6.3196658466462), ...}\nE   assert np.True_ is True\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_B14_docstring_wording - AssertionError: compute...\nFAILED tests/test_hA.py::test_B15_rejection_messages_name_the_reason - Assert...\nFAILED tests/test_hA.py::test_C11_validation_result_keys - AssertionError:   ...\nFAILED tests/test_hB.py::test_E07_end_to_end_science - AssertionError: {'mass...\nFAILED tests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha - As...\n========================= 5 failed, 56 passed in 1.82s =========================\n",
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
        "passed": 12,
        "collected": 13,
        "fraction": 0.9230769230769231,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_B14_docstring_wording"
        ]
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
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_assert_non_finite_n_sigma",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_assert_non_positive_n_sigma",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_far_outside",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_non_finite_expected",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_non_finite_slope",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_non_finite_slope_err",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_non_positive_slope_err",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_true_within_range",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_known_values",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reduced_identity",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reject_bool_scalar",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reject_merger_fraction_outside_range",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reject_n_gal_zero_with_nonzero_f_pair",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reject_ndarray_scalar",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reject_non_finite_box_size",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reject_non_positive_box_size",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reject_non_positive_timescale",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_valid_n_gal_zero_with_zero_f_pair",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_sigma_f_pair_gives_zero_sigma_rate",
      "tests/test_merger_rate.py::TestComputePairFraction::test_accept_integer_dtype",
      "tests/test_merger_rate.py::TestComputePairFraction::test_accept_integer_valued_float",
      "tests/test_merger_rate.py::TestComputePairFraction::test_assert_n_pairs_gt_0_requires_n_gal_gt_0",
      "tests/test_merger_rate.py::TestComputePairFraction::test_known_values",
      "tests/test_merger_rate.py::TestComputePairFraction::test_reject_mismatched_shapes",
      "tests/test_merger_rate.py::TestComputePairFraction::test_reject_negative_counts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_reject_non_1d",
      "tests/test_merger_rate.py::TestComputePairFraction::test_reject_non_finite",
      "tests/test_merger_rate.py::TestComputePairFraction::test_reject_non_integer_values",
      "tests/test_merger_rate.py::TestComputePairFraction::test_zero_pairs_zero_galaxies",
      "tests/test_merger_rate.py::TestComputePairFraction::test_zero_pairs_zero_galaxies_array",
      "tests/test_merger_rate.py::TestConfigKeys::test_existing_keys_unchanged",
      "tests/test_merger_rate.py::TestConfigKeys::test_three_keys_added",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_all_below_range",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_each_bin_gets_one",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_exact_upper_edge_excluded",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_interior_edge_goes_to_upper_bin",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_sum_equals_selected",
      "tests/test_merger_rate.py::TestEndToEnd::test_slope_consistency_on_mock_data",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_collapsed_predictor_returns_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_exact_power_law",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fewer_than_2_usable_returns_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_mixed_excluded_count",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_reject_inf_redshift",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_reject_malformed_redshift_le_neg1",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_reject_mismatched_shapes",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_reject_nan_redshift",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_reject_non_1d",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_same_redshift_returns_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_slope_err_hand_computed",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_two_points_finite",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_weighted_fit",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_accept_numpy_scalar_box_size",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_excludes_sentinel",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_reject_bool_box_size",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_reject_missing_box_size_attr",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_reject_missing_dataset",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_reject_missing_file",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_reject_non_positive_box_size",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_reject_out_of_range_index",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_reject_string_box_size",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_reject_wrong_length_n_gal",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_returns_correct_values",
      "tests/test_merger_rate.py::TestMassBinEdges::test_default_edges",
      "tests/test_merger_rate.py::TestMassBinEdges::test_edges_match_calc",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_at_z0",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_custom_values",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_reject_bool_z",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_reject_ndarray_z",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_reject_non_finite_alpha",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_reject_non_finite_z",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_reject_non_positive_gyr0",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_reject_string_z",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_reject_z_exactly_neg1",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_reject_z_le_neg1",
      "tests/test_merger_rate.py::TestPart1Integration::test_box_size_from_catalog_not_config",
      "tests/test_merger_rate.py::TestPart1Integration::test_denominator_from_full_catalog",
      "tests/test_merger_rate.py::TestPart1Integration::test_existing_datasets_unchanged",
      "tests/test_merger_rate.py::TestPart1Integration::test_n_galaxies_and_box_size_present",
      "tests/test_merger_rate.py::TestResultsPath::test_path_format",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_box_size_mpc_from_file",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_output_schema",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_preserves_existing_output_on_failure",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_reject_mismatched_redshift",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_reject_missing_file",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_rates_finite_nonnegative",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_reject_non_primary_mass_bin_by",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_expected_slope_tracks_alpha",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_expected_slope_tracks_non_default_alpha",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_heading_states_mock_recovery",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_n_excluded_reported_per_bin",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_per_bin_fields_parseable",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_prints_insufficient_data",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_reject_malformed_stored_redshift",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_returns_result_dicts",
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
   
```
