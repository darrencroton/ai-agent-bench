# Trial report: 20260906T081153Z-001-merger-rate-feature-opencode-go_mimo-v2.5-pro-sixth-session-20260906-mimo-v2.5-pro-opencode-opencode-go_mimo-v2.5-pro-1-dd1b67

- Task: `001-merger-rate-feature`
- Model: `opencode-go/mimo-v2.5-pro` (harness: opencode)
- Model duration: 669.0s | venv setup: 34.4s | timed out: False | committed: False
- Changed files: src/calc.py, src/config.py, src/merger_rate.py, tests/test_merger_rate.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 82.7 / 100

## Judged: readability 75% of weight, maintainability 50% of weight (judge claude-opus-5, status ok)

## Composite score: 79.8 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 91% |
| test_adequacy | automated | 25 | 55% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 100% |
| readability | judged | 8 | 75% |
| maintainability | judged | 7 | 50% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| calc_galaxy_denominator | 4 | 4 | 1.00 |
| persistence_schema_provenance | 5 | 5 | 1.00 |
| load_pair_counts_rejections | 7 | 8 | 0.88 |
| pair_fraction_core | 9 | 10 | 0.90 |
| merger_timescale_and_rate_conversion | 12 | 13 | 0.92 |
| run_merger_rate_calculation_pipeline | 4 | 4 | 1.00 |
| redshift_evolution_fit_and_consistency | 9 | 10 | 0.90 |
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
    "passed": 55,
    "failed": [
      "tests/test_hA.py::test_A17_load_pair_counts_missing_dataset",
      "tests/test_hA.py::test_B14_docstring_wording",
      "tests/test_hA.py::test_B15_rejection_messages_name_the_reason",
      "tests/test_hA.py::test_C08_check_slope_consistency",
      "tests/test_hA.py::test_C11_validation_result_keys",
      "tests/test_hA.py::test_C13_validation_prints_insufficient_data"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "nty wording\"\nE   AssertionError: compute_pair_fraction lacks the required uncertainty wording\nE   assert \"Uncertainty follows Task 001's plug-in Poisson-error convention; it is not a confidence interval.\" in \"Compute pair fraction and its Poisson uncertainty per mass bin.\\n\\nf_pair = N_pairs / N_galaxies\\nsigma_f_pair = f_pair / sqrt(N_pairs)  if N_pairs > 0, else 0\\n\\nUncertainty follows Task 001's plug-in Poisson-error convention; it is not\\na confidence interval.\\n\\nParameters\\n----------\\nn_pairs : 1D array-like\\n    Number of pairs per mass bin (non-negative integer-valued).\\nn_galaxies : 1D array-like\\n    Number of galaxies per mass bin (non-negative integer-valued).\\n\\nReturns\\n-------\\nf_pair : 1D float array\\nsigma_f_pair : 1D float array\"\n_________________ test_B15_rejection_messages_name_the_reason __________________\ntests/test_hA.py:399: in test_B15_rejection_messages_name_the_reason\n    assert_rejects_with(\"shape\", MR.compute_pair_fraction,\ntests/test_hA.py:57: in assert_rejects_with\n    with pytest.raises(AssertionError, match=pattern):\n         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE   AssertionError: Regex pattern did not match.\nE     Expected regex: 'shape'\nE     Actual message: 'Shape mismatch: n_pairs (2,) vs n_galaxies (1,)'\n_______________________ test_C08_check_slope_consistency _______________________\ntests/test_hA.py:480: in test_C08_check_slope_consistency\n    assert MR.check_slope_consistency(float(\"nan\"), 0.1, 1.0) is False\nE   AssertionError: assert None is False\nE    +  where None = <function check_slope_consistency at 0x10e17e6c0>(nan, 0.1, 1.0)\nE    +    where <function check_slope_consistency at 0x10e17e6c0> = MR.check_slope_consistency\nE    +    and   nan = float('nan')\n_______________________ test_C11_validation_result_keys ________________________\ntests/test_hA.py:589: in test_C11_validation_result_keys\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:557: in _parse_bin_line\n    assert all((mass, slope, slope_err, expected, excluded, status)), line\nE   AssertionError:   bin 0 [8.0, 8.5): slope=1.000000, +/-=0.096602, expected=1.0000, n_excluded=0, PASS\nE   assert False\nE    +  where False = all((<re.Match object; span=(8, 18), match='[8.0, 8.5)'>, <re.Match object; span=(20, 34), match='slope=1.000000'>, None, <re.Match object; span=(50, 65), match='expected=1.0000'>, <re.Match object; span=(67, 79), match='n_excluded=0'>, None))\n_________________ test_C13_validation_prints_insufficient_data _________________\ntests/test_hA.py:640: in test_C13_validation_prints_insufficient_data\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:557: in _parse_bin_line\n    assert all((mass, slope, slope_err, expected, excluded, status)), line\nE   AssertionError:   bin 0 [8.0, 8.5): slope=nan, +/-=nan, expected=1.0000, n_excluded=4, insufficient data\nE   assert False\nE    +  where False = all((<re.Match object; span=(8, 18), match='[8.0, 8.5)'>, <re.Match object; span=(20, 29), match='slope=nan'>, None, <re.Match object; span=(40, 55), match='expected=1.0000'>, <re.Match object; span=(57, 69), match='n_excluded=4'>, <re.Match object; span=(71, 88), match='insufficient data'>))\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A17_load_pair_counts_missing_dataset - KeyError...\nFAILED tests/test_hA.py::test_B14_docstring_wording - AssertionError: compute...\nFAILED tests/test_hA.py::test_B15_rejection_messages_name_the_reason - Assert...\nFAILED tests/test_hA.py::test_C08_check_slope_consistency - AssertionError: a...\nFAILED tests/test_hA.py::test_C11_validation_result_keys - AssertionError:   ...\nFAILED tests/test_hA.py::test_C13_validation_prints_insufficient_data - Asser...\n========================= 6 failed, 55 passed in 2.14s =========================\n",
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
        "passed": 7,
        "collected": 8,
        "fraction": 0.875,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_A17_load_pair_counts_missing_dataset"
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
        "passed": 9,
        "collected": 10,
        "fraction": 0.9,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_C08_check_slope_consistency"
        ]
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
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_asserts_non_finite_n_sigma",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_asserts_non_positive_n_sigma",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_far_outside",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_for_nan_slope",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_for_nan_slope_err",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_for_non_finite_expected",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_for_zero_slope_err",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_true_within_range",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_known_values",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reduced_identity",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_merger_fraction_outside_0_1",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_mismatched_shapes",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_ndarray_box_size",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_negative_f_pair",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_non_1d",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_non_finite_box_size",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_non_integer_n_galaxies",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_non_positive_box_size",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_non_positive_timescale",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_string_box_size",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_zero_gal_with_nonzero_f_pair",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_sigma_f_gives_zero_sigma_rate",
      "tests/test_merger_rate.py::TestComputePairFraction::test_accepts_integer_dtype",
      "tests/test_merger_rate.py::TestComputePairFraction::test_accepts_integer_valued_float64",
      "tests/test_merger_rate.py::TestComputePairFraction::test_asserts_pairs_without_galaxies",
      "tests/test_merger_rate.py::TestComputePairFraction::test_known_values",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_mismatched_shapes",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_negative_counts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_1d",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_finite",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_integer_valued",
      "tests/test_merger_rate.py::TestComputePairFraction::test_zero_zero_bin",
      "tests/test_merger_rate.py::TestConfigParameters::test_existing_keys_unchanged",
      "tests/test_merger_rate.py::TestConfigParameters::test_new_keys_present",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_basic_counts",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_below_range_excluded",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_excludes_upper_edge",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_includes_interior_edge",
      "tests/test_merger_rate.py::TestDocstrings::test_compute_merger_rate_docstring",
      "tests/test_merger_rate.py::TestDocstrings::test_compute_pair_fraction_docstring",
      "tests/test_merger_rate.py::TestEndToEndRedshiftEvolution::test_slope_consistent_for_all_bins",
      "tests/test_merger_rate.py::TestExpectedSlopeTracksAlpha::test_non_default_alpha",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_collapsed_predictor_returns_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_exact_power_law",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_non_finite_err_excluded",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_non_finite_rate_excluded",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_non_positive_err_excluded",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_one_usable_point_returns_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_rejects_mismatched_shapes",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_rejects_non_1d",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_rejects_non_finite_redshift",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_rejects_redshift_le_minus1",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_slope_err_hand_computed",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_two_points_finite",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_weighted_fit",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_zero_rate_excluded",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_accepts_numpy_scalar_box_size",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_excludes_sentinel",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_array_box_size",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_complex_box_size",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_box_size_attr",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_dataset",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_file",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_non_positive_box_size",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_string_box_size",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_unexpected_bin_index",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_wrong_length_n_galaxies",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_returns_known_values",
      "tests/test_merger_rate.py::TestMassBinEdges::test_default_edges",
      "tests/test_merger_rate.py::TestMassBinEdges::test_edges_match",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_at_z_zero",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_custom_values",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_bool_z",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_ndarray_gyr0",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_ndarray_z",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_non_finite_alpha",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_non_finite_gyr0",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_non_finite_z",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_non_positive_gyr0",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_string_gyr0",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_string_z",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_z_le_minus1",
      "tests/test_merger_rate.py::TestResultsFileContents::test_box_size_mpc_from_catalog",
      "tests/test_merger_rate.py::TestResultsFileContents::test_denominator_from_full_catalog",
      "tests/test_merger_rate.py::TestResultsFileContents::test_existing_attrs_unchanged",
      "tests/test_merger_rate.py::TestResultsFileContents::test_existing_datasets_unchanged",
      "tests/test_merger_rate.py::TestResultsFileContents::test_new_dataset_and_attr_present",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_finite_nonnegative_rates",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_mass_bin_by_not_primary_fails",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_output_schema",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_leaves_sentinel_unchanged_on_mismatched_redshift",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_leaves_sentinel_unchanged_on_missing_file",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_rejects_malformed_redshift_attr",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_uses_per_file_box_size",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_expected_slope_tracks_alpha",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_fails_on_malformed_stored_redshift",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_heading_states_mock_validation",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_insufficient_data_consistent_is_none",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_per_bin_line_contains_required_fields",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_prints_insufficient_data",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_return_dict_keys",
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
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_max
```
