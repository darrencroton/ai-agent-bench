# Trial report: 20260906T081153Z-001-merger-rate-feature-opencode-go_longcat-2.0-sixth-session-20260906-longcat-2.0-opencode-opencode-go_longcat-2.0-1-365871

- Task: `001-merger-rate-feature`
- Model: `opencode-go/longcat-2.0` (harness: opencode)
- Model duration: 1362.0s | venv setup: 34.4s | timed out: False | committed: False
- Changed files: src/calc.py, src/config.py, src/merger_rate.py, tests/test_merger_rate.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 87.2 / 100

## Judged: readability 75% of weight, maintainability 50% of weight (judge claude-opus-5, status ok)

## Composite score: 83.6 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 94% |
| test_adequacy | automated | 25 | 66% |
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
| merger_timescale_and_rate_conversion | 12 | 13 | 0.92 |
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
      "tests/test_hA.py::test_B14_docstring_wording",
      "tests/test_hA.py::test_B15_rejection_messages_name_the_reason",
      "tests/test_hA.py::test_C11_validation_result_keys",
      "tests/test_hA.py::test_C13_validation_prints_insufficient_data"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "nd_to_end_science PASSED                     [ 98%]\ntests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha PASSED [100%]\n\n=================================== FAILURES ===================================\n__________________________ test_B14_docstring_wording __________________________\ntests/test_hA.py:395: in test_B14_docstring_wording\n    assert required in doc, f\"{fn.__name__} lacks the required uncertainty wording\"\nE   AssertionError: compute_pair_fraction lacks the required uncertainty wording\nE   assert \"Uncertainty follows Task 001's plug-in Poisson-error convention; it is not a confidence interval.\" in \"Compute the close-pair fraction and its Poisson uncertainty per mass bin.\\n\\nf_pair(b, z) = N_pairs(b, z) / N_gal(b, z)\\n\\nUncertainty follows Task 001's plug-in Poisson-error convention;\\nit is not a confidence interval.\\n\\nsigma_f_pair = f_pair / sqrt(N_pairs)  if N_pairs > 0, else 0\\n\\nParameters\\n----------\\nn_pairs : array-like\\n    1D, non-negative integer counts of pairs per mass bin.\\nn_galaxies : array-like\\n    1D, non-negative integer counts of galaxies per mass bin.\\n\\nReturns\\n-------\\nf_pair : numpy.ndarray\\n    Pair fraction per mass bin (float).\\nsigma_f_pair : numpy.ndarray\\n    Poisson uncertainty on f_pair per mass bin (float).\\n\\nRaises\\n------\\nAssertionError\\n    On mismatched shapes, non-1D input, negative counts, non-finite counts,\\n    non-integer-valued counts, or n_pairs > 0 with n_galaxies == 0.\"\n_________________ test_B15_rejection_messages_name_the_reason __________________\ntests/test_hA.py:399: in test_B15_rejection_messages_name_the_reason\n    assert_rejects_with(\"shape\", MR.compute_pair_fraction,\ntests/test_hA.py:57: in assert_rejects_with\n    with pytest.raises(AssertionError, match=pattern):\n         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE   AssertionError: Regex pattern did not match.\nE     Expected regex: 'shape'\nE     Actual message: 'Shape mismatch: n_pairs (2,) vs n_galaxies (1,)'\n_______________________ test_C11_validation_result_keys ________________________\ntests/test_hA.py:589: in test_C11_validation_result_keys\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:557: in _parse_bin_line\n    assert all((mass, slope, slope_err, expected, excluded, status)), line\nE   AssertionError:   Bin 0 (log M = [8.0, 8.5)): slope=1.0000 +/- 0.0966, expected=1.0000, n_excluded=0, PASS\nE   assert False\nE    +  where False = all((<re.Match object; span=(17, 27), match='[8.0, 8.5)'>, <re.Match object; span=(30, 42), match='slope=1.0000'>, <re.Match object; span=(43, 53), match='+/- 0.0966'>, <re.Match object; span=(55, 70), match='expected=1.0000'>, <re.Match object; span=(72, 84), match='n_excluded=0'>, None))\n_________________ test_C13_validation_prints_insufficient_data _________________\ntests/test_hA.py:640: in test_C13_validation_prints_insufficient_data\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:557: in _parse_bin_line\n    assert all((mass, slope, slope_err, expected, excluded, status)), line\nE   AssertionError:   Bin 0 (log M = [8.0, 8.5)): insufficient data, n_excluded=4\nE   assert False\nE    +  where False = all((<re.Match object; span=(17, 27), match='[8.0, 8.5)'>, None, None, None, <re.Match object; span=(49, 61), match='n_excluded=4'>, <re.Match object; span=(30, 47), match='insufficient data'>))\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_B14_docstring_wording - AssertionError: compute...\nFAILED tests/test_hA.py::test_B15_rejection_messages_name_the_reason - Assert...\nFAILED tests/test_hA.py::test_C11_validation_result_keys - AssertionError:   ...\nFAILED tests/test_hA.py::test_C13_validation_prints_insufficient_data - Asser...\n========================= 4 failed, 57 passed in 2.00s =========================\n",
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
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_far_outside",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_invalid_n_sigma",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_expected",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_slope",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_slope_err",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_positive_slope_err",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_within_range",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_basic_values",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_bool_box_size_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_docstring_contains_sentence",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_merger_fraction_out_of_range",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_mismatched_arrays",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_ndarray_timescale_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_negative_array_values",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_non_1d_arrays",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_non_finite_box_size",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_non_finite_timescale",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_non_integer_n_galaxies",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_non_positive_box_size",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_non_positive_timescale",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reduced_identity",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_with_nonzero_f_pair_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_with_nonzero_sigma_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_with_zero_f_pair_valid",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_sigma_yields_zero_sigma_rate",
      "tests/test_merger_rate.py::TestComputePairFraction::test_basic_values",
      "tests/test_merger_rate.py::TestComputePairFraction::test_docstring_contains_sentence",
      "tests/test_merger_rate.py::TestComputePairFraction::test_integer_dtype_accepted",
      "tests/test_merger_rate.py::TestComputePairFraction::test_integer_valued_float_accepted",
      "tests/test_merger_rate.py::TestComputePairFraction::test_mismatched_shapes",
      "tests/test_merger_rate.py::TestComputePairFraction::test_negative_counts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_non_1d_input",
      "tests/test_merger_rate.py::TestComputePairFraction::test_non_finite_counts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_non_integer_counts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_pairs_positive_galaxies_zero_asserts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_zero_pairs_zero_galaxies",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_exact_upper_edge_excluded",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_returns_int_array",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_sum_equals_selected",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_collapsed_predictor_returns_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_exact_power_law",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_exactly_two_usable_points_finite",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fewer_than_2_usable_returns_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_hand_computed_slope_err",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_malformed_redshifts_assert",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_non_1d_assert",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_non_finite_rate_err_excluded",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_non_finite_rate_excluded",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_shape_mismatch_assert",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_single_redshift_returns_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_weighted_fit",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_zero_rate_err_excluded",
      "tests/test_merger_rate.py::TestIntegration::test_box_size_from_catalog_not_config",
      "tests/test_merger_rate.py::TestIntegration::test_denominator_from_full_catalog",
      "tests/test_merger_rate.py::TestIntegration::test_end_to_end_slope_consistency",
      "tests/test_merger_rate.py::TestIntegration::test_merger_rate_calculation_on_mock",
      "tests/test_merger_rate.py::TestIntegration::test_results_files_have_new_dataset_and_attr",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_bool_box_size_raises",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_excludes_mass_bin_neg1",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_loads_known_values",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_missing_box_size_attr_raises",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_missing_dataset_raises",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_missing_file_raises",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_ndarray_box_size_raises",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_non_finite_box_size_raises",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_non_positive_box_size_raises",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_index_above_n_bins",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_index_below_neg1",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_string_box_size_raises",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_wrong_length_n_galaxies_raises",
      "tests/test_merger_rate.py::TestMassBinEdges::test_default_config",
      "tests/test_merger_rate.py::TestMassBinEdges::test_matches_calc",
      "tests/test_merger_rate.py::TestMergerTimescale::test_non_default_values",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_bool_t0",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_bool_z",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_ndarray_z",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_non_finite_alpha",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_non_finite_t0",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_non_finite_z",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_non_positive_t0",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_string_alpha",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_string_z",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_z_le_neg1",
      "tests/test_merger_rate.py::TestMergerTimescale::test_z0_equals_t0",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_malformed_redshift_attr_asserts",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_mass_bin_by_not_primary_asserts",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_mismatched_redshift_asserts",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_missing_pair_file_asserts",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_output_schema",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_per_file_box_size_used",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_expected_slope_tracks_config",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_heading_states_mock_data",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_insufficient_data_reported",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_malformed_stored_redshift_fails",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_returns_list_of_dicts",
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
     
```
