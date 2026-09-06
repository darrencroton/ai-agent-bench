# Trial report: 20260906T081153Z-001-merger-rate-feature-macstudio_kwaipilot_kat-coder-v2.5-dev-q8-sixth-session-20260906-kat-coder-v2.5-dev-q8-opencode-macstudio_kwaipilot_kat-coder-v2.5-dev-q8-1-f77b68

- Task: `001-merger-rate-feature`
- Model: `macstudio/kwaipilot/kat-coder-v2.5-dev-q8` (harness: opencode)
- Model duration: 4824.3s | venv setup: 34.4s | timed out: False | committed: False
- Changed files: src/calc.py, src/config.py, src/merger_rate.py, tests/test_merger_rate.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 81.7 / 100

## Judged: readability 75% of weight, maintainability 50% of weight (judge claude-opus-5, status ok)

## Composite score: 78.9 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 89% |
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
| load_pair_counts_rejections | 8 | 8 | 1.00 |
| pair_fraction_core | 9 | 10 | 0.90 |
| merger_timescale_and_rate_conversion | 12 | 13 | 0.92 |
| run_merger_rate_calculation_pipeline | 3 | 4 | 0.75 |
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
    "passed": 55,
    "failed": [
      "tests/test_hA.py::test_B12_merger_rate_array_rejections",
      "tests/test_hA.py::test_B15_rejection_messages_name_the_reason",
      "tests/test_hA.py::test_C11_validation_result_keys",
      "tests/test_hB.py::test_E05_preflight_atomicity_sha256",
      "tests/test_hB.py::test_E07_end_to_end_science",
      "tests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "s_nondefault_alpha FAILED [100%]\n\n=================================== FAILURES ===================================\n____________________ test_B12_merger_rate_array_rejections _____________________\ntests/test_hA.py:364: in test_B12_merger_rate_array_rejections\n    assert rejects(MR.compute_merger_rate, np.array([-0.5]), np.array([0.1]),\nE   AssertionError: assert None == 'assert'\nE    +  where None = rejects(<function compute_merger_rate at 0x10a5e6770>, array([-0.5]), array([0.1]), array([10]), 500.0, 2.2, 0.6)\nE    +    where <function compute_merger_rate at 0x10a5e6770> = MR.compute_merger_rate\nE    +    and   array([-0.5]) = <built-in function array>([-0.5])\nE    +      where <built-in function array> = np.array\nE    +    and   array([0.1]) = <built-in function array>([0.1])\nE    +      where <built-in function array> = np.array\nE    +    and   array([10]) = <built-in function array>([10])\nE    +      where <built-in function array> = np.array\n_________________ test_B15_rejection_messages_name_the_reason __________________\ntests/test_hA.py:399: in test_B15_rejection_messages_name_the_reason\n    assert_rejects_with(\"shape\", MR.compute_pair_fraction,\ntests/test_hA.py:57: in assert_rejects_with\n    with pytest.raises(AssertionError, match=pattern):\n         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE   AssertionError: Regex pattern did not match.\nE     Expected regex: 'shape'\nE     Actual message: 'Shape mismatch: n_pairs (2,) vs n_galaxies (1,)'\n_______________________ test_C11_validation_result_keys ________________________\ntests/test_hA.py:589: in test_C11_validation_result_keys\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:557: in _parse_bin_line\n    assert all((mass, slope, slope_err, expected, excluded, status)), line\nE   AssertionError:   Bin 0  [8.0, 8.5)  slope=1.000000 +/- 0.096602  expected=1.0000  n_excluded=0  PASS\nE   assert False\nE    +  where False = all((<re.Match object; span=(9, 19), match='[8.0, 8.5)'>, <re.Match object; span=(21, 35), match='slope=1.000000'>, <re.Match object; span=(36, 48), match='+/- 0.096602'>, <re.Match object; span=(50, 65), match='expected=1.0000'>, <re.Match object; span=(67, 79), match='n_excluded=0'>, None))\n_____________________ test_E05_preflight_atomicity_sha256 ______________________\ntests/test_hB.py:230: in test_E05_preflight_atomicity_sha256\n    assert not failures, failures\nE   AssertionError: [('z_missing', 'exception', 'KeyError')]\nE   assert not [('z_missing', 'exception', 'KeyError')]\n_________________________ test_E07_end_to_end_science __________________________\ntests/test_hB.py:294: in test_E07_end_to_end_science\n    assert d[\"consistent\"] is True, d\nE   AssertionError: {'mass_bin': 0, 'slope': np.float64(0.926776233510532), 'slope_err': np.float64(0.13946676597215996), 'intercept': np.float64(-6.319665846646199), ...}\nE   assert np.True_ is True\n_______________ test_E09_expected_slope_tracks_nondefault_alpha ________________\ntests/test_hB.py:322: in test_E09_expected_slope_tracks_nondefault_alpha\n    assert d[\"consistent\"] is True, d\nE   AssertionError: {'mass_bin': 0, 'slope': np.float64(0.6267762335105315), 'slope_err': np.float64(0.13946676597215996), 'intercept': np.float64(-6.3196658466462), ...}\nE   assert np.True_ is True\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_B12_merger_rate_array_rejections - AssertionErr...\nFAILED tests/test_hA.py::test_B15_rejection_messages_name_the_reason - Assert...\nFAILED tests/test_hA.py::test_C11_validation_result_keys - AssertionError:   ...\nFAILED tests/test_hB.py::test_E05_preflight_atomicity_sha256 - AssertionError...\nFAILED tests/test_hB.py::test_E07_end_to_end_science - AssertionError: {'mass...\nFAILED tests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha - As...\n========================= 6 failed, 55 passed in 1.96s =========================\n",
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
          "tests/test_hA.py::test_B12_merger_rate_array_rejections"
        ]
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
      "tests/test_merger_rate.py::TestCalcAdditions::test_box_size_mpc_from_catalog_not_config",
      "tests/test_merger_rate.py::TestCalcAdditions::test_count_galaxies_per_mass_bin_exact",
      "tests/test_merger_rate.py::TestCalcAdditions::test_denominator_from_full_selected_catalog",
      "tests/test_merger_rate.py::TestCalcAdditions::test_mass_bin_edges_matches_pair_finder_convention",
      "tests/test_merger_rate.py::TestCalcAdditions::test_n_galaxies_and_box_size_mpc_in_results",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_asserts_on_invalid_n_sigma",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_far_outside",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_inputs",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_within_range",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_zero_or_negative_slope_err",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_basic_values",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reduced_identity",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_0d_array_scalar_inputs",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_merger_fraction_out_of_range",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_mismatched_shapes",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_negative_n_galaxies",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_non_finite_box_size",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_non_integer_n_galaxies",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_non_positive_box_size",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_non_positive_timescale",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_string_scalar_box_size",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_both_zero_valid",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_with_nonzero_f_pair_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_sigma_f_pair_gives_zero_sigma_rate",
      "tests/test_merger_rate.py::TestComputePairFraction::test_accepts_integer_dtype",
      "tests/test_merger_rate.py::TestComputePairFraction::test_accepts_integer_valued_float64",
      "tests/test_merger_rate.py::TestComputePairFraction::test_basic_values",
      "tests/test_merger_rate.py::TestComputePairFraction::test_n_pairs_gt_0_requires_n_galaxies_gt_0",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_mismatched_shapes",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_negative_counts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_1d",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_finite_counts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_integer_values",
      "tests/test_merger_rate.py::TestComputePairFraction::test_zero_both_bins",
      "tests/test_merger_rate.py::TestConfigKeys::test_keys_present_and_unchanged",
      "tests/test_merger_rate.py::TestConfigKeys::test_merger_timescale_at_zero",
      "tests/test_merger_rate.py::TestConfigKeys::test_merger_timescale_power_law",
      "tests/test_merger_rate.py::TestDocstrings::test_compute_merger_rate_docstring",
      "tests/test_merger_rate.py::TestDocstrings::test_compute_pair_fraction_docstring",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_exact_power_law",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fewer_than_two_usable_points",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_finite_fit_two_points",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_malformed_redshifts_fail",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_n_excluded_correct",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_shape_rank_violations",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_single_distinct_redshift_collapses",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_slope_err_hand_computed",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_weighted_fit",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_accepts_numpy_scalar_box_size",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_excludes_mass_bin_minus_one",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_complex_box_size",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_mass_bin_index",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_attr",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_dataset",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_file",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_negative_box_size",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_non_finite_box_size",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_string_box_size",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_wrong_length_n_galaxies",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_returns_known_values",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_basic",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_0d_array_z",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_bool_z",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_non_finite_alpha",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_non_finite_z",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_non_positive_t0",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_string_z",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_z_leq_minus_one",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_output_schema",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_per_file_box_size_used",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_bad_redshift_attr_preserves_output",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_missing_file_preserves_output",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_primary_required",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_end_to_end_slope_consistency",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_expected_slope_tracks_config_alpha",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_fails_on_malformed_stored_redshift",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_prints_sufficient_data_info",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_result_dict_keys",
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
      "tests/test_statistical.py::
```
