# Trial report: 20260905T131207Z-001-merger-rate-feature-claude-haiku-4-5-20251001-weak-tier-20260905-claude-claude-haiku-4-5-20251001-1-35d4fc

- Task: `001-merger-rate-feature`
- Model: `claude-haiku-4-5-20251001` (harness: claude)
- Model duration: 419.3s | venv setup: 35.3s | timed out: False | committed: False
- Changed files: src/calc.py, src/config.py, src/merger_rate.py, tests/test_merger_rate.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 73.0 / 100

## Judged: readability 75% of weight, maintainability 25% of weight (judge claude-opus-5, status ok)

## Composite score: 69.8 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 91% |
| test_adequacy | automated | 25 | 48% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 38% |
| readability | judged | 8 | 75% |
| maintainability | judged | 7 | 25% |

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
| validation_reporting_and_e2e | 3 | 7 | 0.43 |

## Provenance

```json
{
  "rubric_version": 2,
  "rubric_sha256": "a4a93e1f5fd3b17c7ad7f873dd74a65ff2c74da8a1f759c4ac5e3e8a1d7a9102",
  "rubric_profile": "default",
  "task_contract_sha256": "ba2fd08a32821553bca1847a3c956ddd680ddb140c6db6da5ad131918ee23bd7",
  "evaluator_content_sha256": "fe9fc605d85bfeee8dbf7669ef4eb4db367fb7d2ef0d51b8335e7c27d6993913",
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
    "total": 61,
    "passed": 55,
    "failed": [
      "tests/test_hA.py::test_B14_docstring_wording",
      "tests/test_hA.py::test_B15_rejection_messages_name_the_reason",
      "tests/test_hA.py::test_C11_validation_result_keys",
      "tests/test_hA.py::test_C13_validation_prints_insufficient_data",
      "tests/test_hB.py::test_E07_end_to_end_science",
      "tests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "sk 001's plug-in Poisson-error convention; it is not\\na confidence interval.\\n\\nParameters\\n----------\\nn_pairs : 1D array-like, int\\n    Number of pairs per bin.\\nn_galaxies : 1D array-like, int\\n    Total number of galaxies per bin.\\n\\nReturns\\n-------\\nf_pair : 1D float array\\n    Pair fraction per bin (can exceed 1).\\nsigma_f_pair : 1D float array\\n    Poisson uncertainty in f_pair.\\n\\nRaises\\n------\\nAssertionError\\n    If inputs are not 1D, have different shapes, contain negative values,\\n    non-finite values, or non-integer-valued floats.\"\n_________________ test_B15_rejection_messages_name_the_reason __________________\ntests/test_hA.py:401: in test_B15_rejection_messages_name_the_reason\n    assert_rejects_with(\"non-negative\", MR.compute_pair_fraction,\ntests/test_hA.py:57: in assert_rejects_with\n    with pytest.raises(AssertionError, match=pattern):\n         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE   AssertionError: Regex pattern did not match.\nE     Expected regex: 'non-negative'\nE     Actual message: 'n_pairs contains negative values'\n_______________________ test_C11_validation_result_keys ________________________\ntests/test_hA.py:589: in test_C11_validation_result_keys\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:557: in _parse_bin_line\n    assert all((mass, slope, slope_err, expected, excluded, status)), line\nE   AssertionError:   Bin 0: [8.0, 8.5) \u2014 slope=1.0000 +/- 0.0966, expected=1.0000, n_excluded=0 \u2014 PASS\nE   assert False\nE    +  where False = all((<re.Match object; span=(9, 19), match='[8.0, 8.5)'>, <re.Match object; span=(22, 34), match='slope=1.0000'>, <re.Match object; span=(35, 45), match='+/- 0.0966'>, <re.Match object; span=(47, 62), match='expected=1.0000'>, <re.Match object; span=(64, 76), match='n_excluded=0'>, None))\n_________________ test_C13_validation_prints_insufficient_data _________________\ntests/test_hA.py:640: in test_C13_validation_prints_insufficient_data\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:557: in _parse_bin_line\n    assert all((mass, slope, slope_err, expected, excluded, status)), line\nE   AssertionError:   Bin 0: [8.0, 8.5) \u2014 insufficient data (n_excluded=4)\nE   assert False\nE    +  where False = all((<re.Match object; span=(9, 19), match='[8.0, 8.5)'>, None, None, None, <re.Match object; span=(41, 53), match='n_excluded=4'>, <re.Match object; span=(22, 39), match='insufficient data'>))\n_________________________ test_E07_end_to_end_science __________________________\ntests/test_hB.py:294: in test_E07_end_to_end_science\n    assert d[\"consistent\"] is True, d\nE   AssertionError: {'mass_bin': 0, 'slope': np.float64(0.9267762335105321), 'slope_err': np.float64(0.13946676597215996), 'intercept': np.float64(-6.3196658466462), ...}\nE   assert np.True_ is True\n_______________ test_E09_expected_slope_tracks_nondefault_alpha ________________\ntests/test_hB.py:322: in test_E09_expected_slope_tracks_nondefault_alpha\n    assert d[\"consistent\"] is True, d\nE   AssertionError: {'mass_bin': 0, 'slope': np.float64(0.6267762335105316), 'slope_err': np.float64(0.13946676597215996), 'intercept': np.float64(-6.319665846646201), ...}\nE   assert np.True_ is True\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_B14_docstring_wording - AssertionError: compute...\nFAILED tests/test_hA.py::test_B15_rejection_messages_name_the_reason - Assert...\nFAILED tests/test_hA.py::test_C11_validation_result_keys - AssertionError:   ...\nFAILED tests/test_hA.py::test_C13_validation_prints_insufficient_data - Asser...\nFAILED tests/test_hB.py::test_E07_end_to_end_science - AssertionError: {'mass...\nFAILED tests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha - As...\n========================= 6 failed, 55 passed in 1.76s =========================\n",
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
        "passed": 3,
        "collected": 7,
        "fraction": 0.42857142857142855,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_C11_validation_result_keys",
          "tests/test_hA.py::test_C13_validation_prints_insufficient_data",
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
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_asserts_invalid_n_sigma",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_far_outside",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_expected_slope",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_slope",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_slope_err",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_positive_slope_err",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_within_range",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_accepts_zero_galaxies_with_both_zero",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_exact_values",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_per_file_box_size_used",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reduced_identity",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_merger_fraction",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_non_positive_box_size",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_zero_galaxies_with_nonzero_fpair",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_zero_galaxies_with_nonzero_sigma",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_uncertainty_preserved",
      "tests/test_merger_rate.py::TestComputePairFraction::test_accepts_integer_dtypes",
      "tests/test_merger_rate.py::TestComputePairFraction::test_accepts_integer_valued_floats",
      "tests/test_merger_rate.py::TestComputePairFraction::test_exact_values",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_mismatched_shapes",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_negative_counts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_1d",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_finite",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_integer_valued_floats",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_pairs_without_galaxies",
      "tests/test_merger_rate.py::TestComputePairFraction::test_zero_galaxies_zero_pairs",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_exact_edge_case_exclusion",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_sum_equals_full_selected_catalog",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_exact_power_law_recovery",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_exactly_two_usable_points",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_excludes_non_finite_rate",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_excludes_non_positive_rate_err",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fewer_than_two_usable_points",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fit_is_weighted",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_rejects_malformed_redshifts",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_rejects_mismatched_shapes",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_rejects_non_1d",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_single_distinct_redshift",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_slope_error_from_normal_equations",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_box_size_from_catalog_not_config",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_excludes_out_of_range",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_hand_crafted_file",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size_type",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_mismatched_galaxy_count_length",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_dataset",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_file",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_non_positive_box_size",
      "tests/test_merger_rate.py::TestMassBinEdges::test_edges_match_pair_finder",
      "tests/test_merger_rate.py::TestMassBinEdges::test_edges_values",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_at_z_equals_0",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_power_law_form",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_z_type",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_non_finite_alpha",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_non_finite_z",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_non_positive_gyr0",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_z_too_negative",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_output_file_untouched_on_preflight_failure",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_catches_missing_file",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_rates_finite_nonnegative",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_rejects_wrong_mass_bin_by",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_writes_correct_schema",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_expected_slope_tracks_config",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_prints_insufficient_data_for_nan_slope",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_rejects_malformed_stored_redshift",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_validation_on_generated_mock_data",
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
      "tests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[1]",
      "tests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[2]",
      "tests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[3]",
      "tests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[4]",
      "tests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[5]"
    ],
    "failed_nodes": [],
    "unparsable": false,
    "collect_timed_out": false,
    "tail": "y::TestMaxwellDistribution::test_ks_against_maxwell[3-5.0] 
```
