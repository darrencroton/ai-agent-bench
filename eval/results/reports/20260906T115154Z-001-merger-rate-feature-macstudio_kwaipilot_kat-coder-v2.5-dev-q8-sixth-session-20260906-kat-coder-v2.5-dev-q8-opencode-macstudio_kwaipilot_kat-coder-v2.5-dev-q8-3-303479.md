# Trial report: 20260906T115154Z-001-merger-rate-feature-macstudio_kwaipilot_kat-coder-v2.5-dev-q8-sixth-session-20260906-kat-coder-v2.5-dev-q8-opencode-macstudio_kwaipilot_kat-coder-v2.5-dev-q8-3-303479

- Task: `001-merger-rate-feature`
- Model: `macstudio/kwaipilot/kat-coder-v2.5-dev-q8` (harness: opencode)
- Model duration: 4592.8s | venv setup: 36.0s | timed out: False | committed: False
- Changed files: src/calc.py, src/config.py, src/merger_rate.py, tests/test_merger_rate.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 84.1 / 100

## Judged: readability 75% of weight, maintainability 50% of weight (judge claude-opus-5, status ok)

## Composite score: 80.9 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 93% |
| test_adequacy | automated | 25 | 58% |
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
    "passed": 56,
    "failed": [
      "tests/test_hA.py::test_A17_load_pair_counts_missing_dataset",
      "tests/test_hA.py::test_B12_merger_rate_array_rejections",
      "tests/test_hA.py::test_B15_rejection_messages_name_the_reason",
      "tests/test_hA.py::test_C11_validation_result_keys",
      "tests/test_hA.py::test_C13_validation_prints_insufficient_data"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "    where <built-in function array> = np.array\n_________________ test_B15_rejection_messages_name_the_reason __________________\ntests/test_hA.py:401: in test_B15_rejection_messages_name_the_reason\n    assert_rejects_with(\"non-negative\", MR.compute_pair_fraction,\ntests/test_hA.py:57: in assert_rejects_with\n    with pytest.raises(AssertionError, match=pattern):\n         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE   AssertionError: Regex pattern did not match.\nE     Expected regex: 'non-negative'\nE     Actual message: 'n_pairs contains negative values.'\n_______________________ test_C11_validation_result_keys ________________________\ntests/test_hA.py:589: in test_C11_validation_result_keys\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:557: in _parse_bin_line\n    assert all((mass, slope, slope_err, expected, excluded, status)), line\nE   AssertionError:   bin 0  [8.0, 8.5)  slope=1.000000  +/-0.096602  expected=1.000000  n_excluded=0  PASS\nE   assert False\nE    +  where False = all((<re.Match object; span=(9, 19), match='[8.0, 8.5)'>, <re.Match object; span=(21, 35), match='slope=1.000000'>, <re.Match object; span=(37, 48), match='+/-0.096602'>, <re.Match object; span=(50, 67), match='expected=1.000000'>, <re.Match object; span=(69, 81), match='n_excluded=0'>, None))\n_________________ test_C13_validation_prints_insufficient_data _________________\ntests/test_hA.py:640: in test_C13_validation_prints_insufficient_data\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:557: in _parse_bin_line\n    assert all((mass, slope, slope_err, expected, excluded, status)), line\nE   AssertionError:   bin 0  [8.0, 8.5)  slope=nan  nan  expected=1.000000  n_excluded=4  insufficient data\nE   assert False\nE    +  where False = all((<re.Match object; span=(9, 19), match='[8.0, 8.5)'>, <re.Match object; span=(21, 30), match='slope=nan'>, None, <re.Match object; span=(37, 54), match='expected=1.000000'>, <re.Match object; span=(56, 68), match='n_excluded=4'>, <re.Match object; span=(70, 87), match='insufficient data'>))\n=============================== warnings summary ===============================\ntests/test_hA.py::test_A05_pair_fraction_pinned\ntests/test_hA.py::test_A06_zero_zero_bin_exact_zero\ntests/test_hB.py::test_E04_per_file_box_size_used\n  /Users/dcroton/Local/git-repos/ai-agent-bench/eval/results/tmp/worktrees/20260906T115154Z-001-merger-rate-feature-macstudio_kwaipilot_kat-coder-v2.5-dev-q8-sixth-session-20260906-kat-coder-v2.5-dev-q8-opencode-macstudio_kwaipilot_kat-coder-v2.5-dev-q8-3-303479/tests/../src/merger_rate.py:192: RuntimeWarning: invalid value encountered in divide\n    f_pair / np.sqrt(n_pairs_f),\n\ntests/test_hA.py::test_A06_zero_zero_bin_exact_zero\ntests/test_hB.py::test_E04_per_file_box_size_used\n  /Users/dcroton/Local/git-repos/ai-agent-bench/eval/results/tmp/worktrees/20260906T115154Z-001-merger-rate-feature-macstudio_kwaipilot_kat-coder-v2.5-dev-q8-sixth-session-20260906-kat-coder-v2.5-dev-q8-opencode-macstudio_kwaipilot_kat-coder-v2.5-dev-q8-3-303479/tests/../src/merger_rate.py:189: RuntimeWarning: invalid value encountered in divide\n    f_pair = np.where(n_galaxies_f > 0, n_pairs_f / n_galaxies_f, 0.0)\n\n-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A17_load_pair_counts_missing_dataset - KeyError...\nFAILED tests/test_hA.py::test_B12_merger_rate_array_rejections - AssertionErr...\nFAILED tests/test_hA.py::test_B15_rejection_messages_name_the_reason - Assert...\nFAILED tests/test_hA.py::test_C11_validation_result_keys - AssertionError:   ...\nFAILED tests/test_hA.py::test_C13_validation_prints_insufficient_data - Asser...\n=================== 5 failed, 56 passed, 5 warnings in 2.00s ===================\n",
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
          "tests/test_hA.py::test_B12_merger_rate_array_rejections"
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
      "tests/test_merger_rate.py::TestCalcIntegrationPart1::test_box_size_mpc_comes_from_catalog_not_config",
      "tests/test_merger_rate.py::TestCalcIntegrationPart1::test_new_dataset_and_attr_present",
      "tests/test_merger_rate.py::TestCalcMassBinEdges::test_matches_default",
      "tests/test_merger_rate.py::TestCalcMassBinEdges::test_right_open_excludes_upper_edge",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_asserts_on_invalid_n_sigma",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_far_outside_fails",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_or_zero_err_returns_false[1.0--0.1-1.0]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_or_zero_err_returns_false[1.0-0.0-1.0]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_or_zero_err_returns_false[1.0-0.1-nan]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_or_zero_err_returns_false[1.0-nan-1.0]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_or_zero_err_returns_false[nan-0.1-1.0]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_within_range_passes",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_basic_values",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reduced_identity_with_n_pairs_5",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_box_size[-1.0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_box_size[0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_box_size[500]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_box_size[inf]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_box_size[nan]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_merger_fraction[-0.1]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_merger_fraction[0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_merger_fraction[1.1]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_merger_fraction[inf]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_merger_fraction[nan]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_scalar_forms_in_compute_merger_rate[(1+0j)]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_scalar_forms_in_compute_merger_rate[500_0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_scalar_forms_in_compute_merger_rate[500_1]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_scalar_forms_in_compute_merger_rate[True]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_scalar_forms_in_compute_merger_rate[bad_scalar3]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_timescale[-1.0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_timescale[0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_timescale[inf]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_timescale[nan]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_negative_array_values",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_non_1d_arrays",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_non_integer_n_galaxies",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_with_all_zeros_valid",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_with_nonzero_f_pair_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_sigma_f_pair_yields_zero_sigma_rate",
      "tests/test_merger_rate.py::TestComputePairFraction::test_accepts_integer_valued_float64",
      "tests/test_merger_rate.py::TestComputePairFraction::test_asserts_n_pairs_gt_0_with_n_gal_eq_0",
      "tests/test_merger_rate.py::TestComputePairFraction::test_basic_values",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_mismatched_shapes_or_non_1d[n_pairs0-n_gal0]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_mismatched_shapes_or_non_1d[n_pairs1-n_gal1]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_mismatched_shapes_or_non_1d[n_pairs2-n_gal2]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_negative_counts[-1]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_negative_counts[-5.0]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_finite_counts[-inf]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_finite_counts[inf]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_finite_counts[nan]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_integer_float_values",
      "tests/test_merger_rate.py::TestComputePairFraction::test_zero_pairs_zero_galaxies_yields_exact_zero",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_all_in_range",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_exact_values_for_sample_input",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_sum_equals_selected_count_minus_upper_edge",
      "tests/test_merger_rate.py::TestDocstrings::test_compute_merger_rate_docstring",
      "tests/test_merger_rate.py::TestDocstrings::test_compute_pair_fraction_docstring",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_all_same_redshift_returns_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_exact_power_law",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fewer_than_2_usable_points_returns_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_finite_fit_for_two_points",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_n_excluded_correct_in_mixed_case",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_rejects_malformed_redshifts[-1.0]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_rejects_malformed_redshifts[-2.0]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_rejects_malformed_redshifts[inf]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_rejects_malformed_redshifts[nan]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_rejects_shape_rank_violations",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_slope_err_matches_hand_computation",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_weighted_vs_unweighted",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_excludes_mass_bin_minus_one",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_bad_box_size_mpc_forms[(500+0j)]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_bad_box_size_mpc_forms[500.0_0]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_bad_box_size_mpc_forms[500.0_1]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_bad_box_size_mpc_forms[True]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_bad_box_size_mpc_forms[bad_val3]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_index_outside_valid_range",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_dataset",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_file",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_non_finite_box_size",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_wrong_n_galaxies_length",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_returns_known_values",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_at_z_zero_equals_t0",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_power_law_value",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_bad_scalar_forms[(1+0j)]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_bad_scalar_forms[2.0_0]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_bad_scalar_forms[2.0_1]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_bad_scalar_forms[True]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_bad_scalar_forms[bad_scalar3]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_t0[-1.0]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_t0[0]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_t0[inf]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_t0[nan]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_z[-1.0]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_z[-2.0]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_z[-inf]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_z[inf]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_z[nan]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_non_finite_alpha",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_mass_bin_by_not_primary_fails",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_output_schema",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_per_file_box_size_used_not_config",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_leaves_existing_output_untouched_on_missing_file",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_leaves_output_untouched_on_bad_redshift_attr",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_leaves_output_untouched_on_redshift_mismatch",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_end_to_end_slope_consistent",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_expected_slope_tracks_non_default_alpha",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_fails_on_malformed_stored_redshift",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_output_dict_keys",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_prints_insufficient_data_for_nan_slope",
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
      "t
```
