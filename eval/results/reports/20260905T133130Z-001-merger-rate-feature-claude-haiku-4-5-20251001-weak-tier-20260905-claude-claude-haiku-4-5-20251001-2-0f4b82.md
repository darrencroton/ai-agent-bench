# Trial report: 20260905T133130Z-001-merger-rate-feature-claude-haiku-4-5-20251001-weak-tier-20260905-claude-claude-haiku-4-5-20251001-2-0f4b82

- Task: `001-merger-rate-feature`
- Model: `claude-haiku-4-5-20251001` (harness: claude)
- Model duration: 449.5s | venv setup: 29.3s | timed out: False | committed: False
- Changed files: src/calc.py, src/config.py, src/merger_rate.py, tests/test_merger_rate.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 69.0 / 100

## Judged: readability 75% of weight, maintainability 50% of weight (judge claude-opus-5, status ok)

## Composite score: 68.1 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 86% |
| test_adequacy | automated | 25 | 37% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 50% |
| readability | judged | 8 | 75% |
| maintainability | judged | 7 | 50% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| calc_galaxy_denominator | 4 | 4 | 1.00 |
| persistence_schema_provenance | 5 | 5 | 1.00 |
| load_pair_counts_rejections | 5 | 8 | 0.62 |
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
    "passed": 52,
    "failed": [
      "tests/test_hA.py::test_A15_load_pair_counts_bad_bin_index",
      "tests/test_hA.py::test_A17_load_pair_counts_missing_dataset",
      "tests/test_hA.py::test_A22_load_pair_counts_rejects_non_numeric_scalar_box_attr",
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
    "raw_tail": " with pytest.raises(AssertionError, match=pattern):\n         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE   AssertionError: Regex pattern did not match.\nE     Expected regex: 'non-negative'\nE     Actual message: 'n_pairs contains negative values'\n_______________________ test_C11_validation_result_keys ________________________\ntests/test_hA.py:589: in test_C11_validation_result_keys\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:544: in _parse_bin_line\n    assert len(lines) == 1, f\"expected one output line for bin {b}, got {lines!r}\"\nE   AssertionError: expected one output line for bin 0, got []\nE   assert 0 == 1\nE    +  where 0 = len([])\n_________________ test_C13_validation_prints_insufficient_data _________________\ntests/test_hA.py:640: in test_C13_validation_prints_insufficient_data\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:544: in _parse_bin_line\n    assert len(lines) == 1, f\"expected one output line for bin {b}, got {lines!r}\"\nE   AssertionError: expected one output line for bin 0, got []\nE   assert 0 == 1\nE    +  where 0 = len([])\n_________________________ test_E07_end_to_end_science __________________________\ntests/test_hB.py:294: in test_E07_end_to_end_science\n    assert d[\"consistent\"] is True, d\nE   AssertionError: {'mass_bin': 0, 'slope': np.float64(0.9267762335105321), 'slope_err': np.float64(0.13946676597215996), 'intercept': np.float64(-6.3196658466462), ...}\nE   assert np.True_ is True\n_______________ test_E09_expected_slope_tracks_nondefault_alpha ________________\ntests/test_hB.py:322: in test_E09_expected_slope_tracks_nondefault_alpha\n    assert d[\"consistent\"] is True, d\nE   AssertionError: {'mass_bin': 0, 'slope': np.float64(0.6267762335105315), 'slope_err': np.float64(0.13946676597215996), 'intercept': np.float64(-6.319665846646198), ...}\nE   assert np.True_ is True\n=============================== warnings summary ===============================\ntests/test_hA.py::test_A05_pair_fraction_pinned\ntests/test_hA.py::test_A06_zero_zero_bin_exact_zero\ntests/test_hB.py::test_E04_per_file_box_size_used\n  /Users/dcroton/Local/git-repos/ai-agent-bench/eval/results/tmp/worktrees/20260905T133130Z-001-merger-rate-feature-claude-haiku-4-5-20251001-weak-tier-20260905-claude-claude-haiku-4-5-20251001-2-0f4b82/tests/../src/merger_rate.py:153: RuntimeWarning: invalid value encountered in divide\n    f_pair / np.sqrt(n_pairs),\n\ntests/test_hA.py::test_A06_zero_zero_bin_exact_zero\ntests/test_hB.py::test_E04_per_file_box_size_used\n  /Users/dcroton/Local/git-repos/ai-agent-bench/eval/results/tmp/worktrees/20260905T133130Z-001-merger-rate-feature-claude-haiku-4-5-20251001-weak-tier-20260905-claude-claude-haiku-4-5-20251001-2-0f4b82/tests/../src/merger_rate.py:150: RuntimeWarning: invalid value encountered in divide\n    f_pair = np.where(n_galaxies > 0, n_pairs / n_galaxies, 0.0)\n\n-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A15_load_pair_counts_bad_bin_index - AssertionE...\nFAILED tests/test_hA.py::test_A17_load_pair_counts_missing_dataset - KeyError...\nFAILED tests/test_hA.py::test_A22_load_pair_counts_rejects_non_numeric_scalar_box_attr\nFAILED tests/test_hA.py::test_B14_docstring_wording - AssertionError: compute...\nFAILED tests/test_hA.py::test_B15_rejection_messages_name_the_reason - Assert...\nFAILED tests/test_hA.py::test_C11_validation_result_keys - AssertionError: ex...\nFAILED tests/test_hA.py::test_C13_validation_prints_insufficient_data - Asser...\nFAILED tests/test_hB.py::test_E07_end_to_end_science - AssertionError: {'mass...\nFAILED tests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha - As...\n=================== 9 failed, 52 passed, 5 warnings in 1.79s ===================\n",
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
        "passed": 5,
        "collected": 8,
        "fraction": 0.625,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_A15_load_pair_counts_bad_bin_index",
          "tests/test_hA.py::test_A17_load_pair_counts_missing_dataset",
          "tests/test_hA.py::test_A22_load_pair_counts_rejects_non_numeric_scalar_box_attr"
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
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_consistent_slope",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_inconsistent_slope",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_nan_slope_returns_false",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_rejects_non_positive_n_sigma",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_zero_slope_err_returns_false",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rate_basic",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rate_matches_reduced_formula",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rate_rejects_merger_frac_outside_bounds",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rate_rejects_non_positive_box",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rate_rejects_non_positive_timescale",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rate_rejects_zero_gal_with_nonzero_f_pair",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rate_zero_sigma_gives_zero_sigma_rate",
      "tests/test_merger_rate.py::TestComputePairFraction::test_pair_fraction_accepts_integer_dtype",
      "tests/test_merger_rate.py::TestComputePairFraction::test_pair_fraction_accepts_integer_valued_float64",
      "tests/test_merger_rate.py::TestComputePairFraction::test_pair_fraction_basic",
      "tests/test_merger_rate.py::TestComputePairFraction::test_pair_fraction_rejects_invalid_form_boolean",
      "tests/test_merger_rate.py::TestComputePairFraction::test_pair_fraction_rejects_invalid_form_string",
      "tests/test_merger_rate.py::TestComputePairFraction::test_pair_fraction_rejects_mismatch_shape",
      "tests/test_merger_rate.py::TestComputePairFraction::test_pair_fraction_rejects_negative",
      "tests/test_merger_rate.py::TestComputePairFraction::test_pair_fraction_rejects_non_1d",
      "tests/test_merger_rate.py::TestComputePairFraction::test_pair_fraction_rejects_non_finite",
      "tests/test_merger_rate.py::TestComputePairFraction::test_pair_fraction_rejects_non_integer_valued",
      "tests/test_merger_rate.py::TestComputePairFraction::test_pair_fraction_rejects_pairs_without_galaxies",
      "tests/test_merger_rate.py::TestComputePairFraction::test_pair_fraction_zero_zero",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_count_galaxies_exact_bins",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fit_collapsed_predictor",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fit_exact_power_law",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fit_fewer_than_two_points",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fit_rejects_mismatched_shapes",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fit_rejects_non_finite_redshift",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fit_rejects_z_leq_minus_1",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fit_two_points_exact",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fit_weighted",
      "tests/test_merger_rate.py::TestIntegrationMockData::test_box_size_from_file_not_config",
      "tests/test_merger_rate.py::TestIntegrationMockData::test_galaxy_counts_match_catalog",
      "tests/test_merger_rate.py::TestIntegrationMockData::test_mass_bin_by_validation",
      "tests/test_merger_rate.py::TestIntegrationMockData::test_merger_rate_calculation_runs",
      "tests/test_merger_rate.py::TestIntegrationMockData::test_merger_rate_output_schema",
      "tests/test_merger_rate.py::TestIntegrationMockData::test_preflight_gates_output",
      "tests/test_merger_rate.py::TestIntegrationMockData::test_validation_runs",
      "tests/test_merger_rate.py::TestIntegrationMockData::test_validation_slope_recovery",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_load_pair_counts_from_fixture",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_load_pair_counts_rejects_missing_attr",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_load_pair_counts_rejects_missing_dataset",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_load_pair_counts_rejects_missing_file",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_load_pair_counts_rejects_non_finite_box",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_load_pair_counts_rejects_non_positive_box",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_load_pair_counts_rejects_wrong_length",
      "tests/test_merger_rate.py::TestMassBinEdges::test_mass_bin_edges_default_config",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_timescale_at_z_zero",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_timescale_power_law",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_timescale_rejects_invalid_form_z",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_timescale_rejects_non_finite_alpha",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_timescale_rejects_non_finite_z",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_timescale_rejects_non_positive_T0",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_timescale_rejects_z_leq_minus_1",
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
    "tail": "%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[5] PASSED [ 88%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[0] PASSED       [ 88%]\ntests/test_statistical.py::TestMaxwellMom
```
