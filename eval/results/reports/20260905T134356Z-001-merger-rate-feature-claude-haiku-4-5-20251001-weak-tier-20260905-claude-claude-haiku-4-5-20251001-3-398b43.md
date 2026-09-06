# Trial report: 20260905T134356Z-001-merger-rate-feature-claude-haiku-4-5-20251001-weak-tier-20260905-claude-claude-haiku-4-5-20251001-3-398b43

- Task: `001-merger-rate-feature`
- Model: `claude-haiku-4-5-20251001` (harness: claude)
- Model duration: 418.5s | venv setup: 26.2s | timed out: False | committed: False
- Changed files: src/calc.py, src/config.py, src/merger_rate.py, tests/test_merger_rate.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 70.9 / 100

## Judged: readability 50% of weight, maintainability 25% of weight (judge claude-opus-5, status ok)

## Composite score: 66.0 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 89% |
| test_adequacy | automated | 25 | 36% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 59% |
| readability | judged | 8 | 50% |
| maintainability | judged | 7 | 25% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| calc_galaxy_denominator | 4 | 4 | 1.00 |
| persistence_schema_provenance | 5 | 5 | 1.00 |
| load_pair_counts_rejections | 8 | 8 | 1.00 |
| pair_fraction_core | 9 | 10 | 0.90 |
| merger_timescale_and_rate_conversion | 10 | 13 | 0.77 |
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
    "passed": 53,
    "failed": [
      "tests/test_hA.py::test_B10_timescale_rejects_string_and_array",
      "tests/test_hA.py::test_B11_merger_rate_scalar_rejections",
      "tests/test_hA.py::test_B13_merger_rate_rejects_string_box_by_assertion",
      "tests/test_hA.py::test_B15_rejection_messages_name_the_reason",
      "tests/test_hA.py::test_C11_validation_result_keys",
      "tests/test_hA.py::test_C13_validation_prints_insufficient_data",
      "tests/test_hB.py::test_E07_end_to_end_science",
      "tests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "5.0], 'log_mass_min': 8.0, 'log_mass_max': 11.0, ...})\nE    +    where <function merger_timescale_gyr at 0x10df97690> = MR.merger_timescale_gyr\n____________________ test_B11_merger_rate_scalar_rejections ____________________\ntests/test_hA.py:352: in test_B11_merger_rate_scalar_rejections\n    assert rejects(MR.compute_merger_rate, *ok, bad, 2.2, 0.6) == \"assert\", (\"box\", bad)\nE   AssertionError: ('box', '500.0')\nE   assert None == 'assert'\nE    +  where None = rejects(<function compute_merger_rate at 0x10df97740>, *(array([0.5]), array([0.1]), array([10])), '500.0', 2.2, 0.6)\nE    +    where <function compute_merger_rate at 0x10df97740> = MR.compute_merger_rate\n_____________ test_B13_merger_rate_rejects_string_box_by_assertion _____________\ntests/test_hA.py:385: in test_B13_merger_rate_rejects_string_box_by_assertion\n    assert r == \"assert\", r\nE   AssertionError: None\nE   assert None == 'assert'\n_________________ test_B15_rejection_messages_name_the_reason __________________\ntests/test_hA.py:401: in test_B15_rejection_messages_name_the_reason\n    assert_rejects_with(\"non-negative\", MR.compute_pair_fraction,\ntests/test_hA.py:57: in assert_rejects_with\n    with pytest.raises(AssertionError, match=pattern):\n         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE   AssertionError: Regex pattern did not match.\nE     Expected regex: 'non-negative'\nE     Actual message: 'n_pairs contains negative values'\n_______________________ test_C11_validation_result_keys ________________________\ntests/test_hA.py:589: in test_C11_validation_result_keys\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:544: in _parse_bin_line\n    assert len(lines) == 1, f\"expected one output line for bin {b}, got {lines!r}\"\nE   AssertionError: expected one output line for bin 0, got []\nE   assert 0 == 1\nE    +  where 0 = len([])\n_________________ test_C13_validation_prints_insufficient_data _________________\ntests/test_hA.py:640: in test_C13_validation_prints_insufficient_data\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:544: in _parse_bin_line\n    assert len(lines) == 1, f\"expected one output line for bin {b}, got {lines!r}\"\nE   AssertionError: expected one output line for bin 0, got []\nE   assert 0 == 1\nE    +  where 0 = len([])\n_________________________ test_E07_end_to_end_science __________________________\ntests/test_hB.py:294: in test_E07_end_to_end_science\n    assert d[\"consistent\"] is True, d\nE   AssertionError: {'mass_bin': 0, 'slope': np.float64(0.926776233510532), 'slope_err': np.float64(0.13946676597215996), 'intercept': np.float64(-6.3196658466462), ...}\nE   assert np.True_ is True\n_______________ test_E09_expected_slope_tracks_nondefault_alpha ________________\ntests/test_hB.py:322: in test_E09_expected_slope_tracks_nondefault_alpha\n    assert d[\"consistent\"] is True, d\nE   AssertionError: {'mass_bin': 0, 'slope': np.float64(0.6267762335105314), 'slope_err': np.float64(0.13946676597215996), 'intercept': np.float64(-6.3196658466462), ...}\nE   assert np.True_ is True\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_B10_timescale_rejects_string_and_array - Assert...\nFAILED tests/test_hA.py::test_B11_merger_rate_scalar_rejections - AssertionEr...\nFAILED tests/test_hA.py::test_B13_merger_rate_rejects_string_box_by_assertion\nFAILED tests/test_hA.py::test_B15_rejection_messages_name_the_reason - Assert...\nFAILED tests/test_hA.py::test_C11_validation_result_keys - AssertionError: ex...\nFAILED tests/test_hA.py::test_C13_validation_prints_insufficient_data - Asser...\nFAILED tests/test_hB.py::test_E07_end_to_end_science - AssertionError: {'mass...\nFAILED tests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha - As...\n========================= 8 failed, 53 passed in 1.74s =========================\n",
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
        "passed": 10,
        "collected": 13,
        "fraction": 0.7692307692307693,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_B10_timescale_rejects_string_and_array",
          "tests/test_hA.py::test_B11_merger_rate_scalar_rejections",
          "tests/test_hA.py::test_B13_merger_rate_rejects_string_box_by_assertion"
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
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_boundary_case",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_consistent_slope",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_inconsistent_slope",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_invalid_n_sigma",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_slope",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_positive_error",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_merger_fraction_out_of_range",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_nonzero_f_with_zero_galaxies_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rate_computation",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reduced_form_identity",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_zero_rate",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_uncertainty_preserved",
      "tests/test_merger_rate.py::TestComputePairFraction::test_basic_computation",
      "tests/test_merger_rate.py::TestComputePairFraction::test_integer_input_validation",
      "tests/test_merger_rate.py::TestComputePairFraction::test_negative_values_rejected",
      "tests/test_merger_rate.py::TestComputePairFraction::test_non_1d_rejected",
      "tests/test_merger_rate.py::TestComputePairFraction::test_non_finite_rejected",
      "tests/test_merger_rate.py::TestComputePairFraction::test_non_integer_rejected",
      "tests/test_merger_rate.py::TestComputePairFraction::test_pairs_without_galaxies_rejected",
      "tests/test_merger_rate.py::TestComputePairFraction::test_shape_mismatch_rejected",
      "tests/test_merger_rate.py::TestComputePairFraction::test_zero_both",
      "tests/test_merger_rate.py::TestComputePairFraction::test_zero_uncertainty_preserved",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_collapsed_predictor",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_exact_power_law",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_excluded_nonpositive_errors",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_excluded_nonpositive_rates",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_insufficient_points",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_invalid_redshifts",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_two_point_fit",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_different_box_vs_config",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_load_from_fixture",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_missing_dataset",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_missing_file",
      "tests/test_merger_rate.py::TestMassBinEdges::test_bin_count",
      "tests/test_merger_rate.py::TestMassBinEdges::test_standard_config",
      "tests/test_merger_rate.py::TestMergerTimescale::test_gyr0_negative_rejected",
      "tests/test_merger_rate.py::TestMergerTimescale::test_negative_alpha",
      "tests/test_merger_rate.py::TestMergerTimescale::test_scalar_form_validation",
      "tests/test_merger_rate.py::TestMergerTimescale::test_timescale_at_z0",
      "tests/test_merger_rate.py::TestMergerTimescale::test_timescale_custom_alpha",
      "tests/test_merger_rate.py::TestMergerTimescale::test_z_boundary_rejected",
      "tests/test_merger_rate.py::TestMergerTimescale::test_z_non_finite_rejected",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_calculation_with_generated_data",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_rejects_non_primary_mass_bin_by",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_validation_with_generated_data",
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
    "tail": "y::TestMaxwellDistribution::test_ks_against_maxwell[3-5.0] PASSED [ 76%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-2.0] PASSED [ 76%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-3.0] PASSED [ 77%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-4.0] PASSED [ 78%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-5.0] PASSED [ 79%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-2.0] PASSED [ 80%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-3.0] PASSED [ 80%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-4.0] PASSED [ 81%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-5.0] PASSED [ 82%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[0] PASSED [ 83%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[1] PASSED [ 84%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[2] PASSED [ 84%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[3] PASSED [ 85%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[4] PASSED [ 86%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[5] PASSED [ 87%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[0] PASSED       [ 88%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[1] PASSED       [ 88%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[2] PASSED       [ 89%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[3] PASSED       [ 90%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[4] PASSED       [ 91%]\ntests/test_statistical.py::TestM
```
