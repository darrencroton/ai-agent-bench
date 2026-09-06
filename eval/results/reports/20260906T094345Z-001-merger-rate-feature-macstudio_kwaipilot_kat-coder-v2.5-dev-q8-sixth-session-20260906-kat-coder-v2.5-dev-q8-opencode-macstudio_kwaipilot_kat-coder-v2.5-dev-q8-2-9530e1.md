# Trial report: 20260906T094345Z-001-merger-rate-feature-macstudio_kwaipilot_kat-coder-v2.5-dev-q8-sixth-session-20260906-kat-coder-v2.5-dev-q8-opencode-macstudio_kwaipilot_kat-coder-v2.5-dev-q8-2-9530e1

- Task: `001-merger-rate-feature`
- Model: `macstudio/kwaipilot/kat-coder-v2.5-dev-q8` (harness: opencode)
- Model duration: 3158.0s | venv setup: 25.9s | timed out: False | committed: False
- Changed files: src/calc.py, src/config.py, src/merger_rate.py, tests/test_merger_rate.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 82.3 / 100

## Judged: readability 75% of weight, maintainability 50% of weight (judge claude-opus-5, status ok)

## Composite score: 79.5 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 89% |
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
| merger_timescale_and_rate_conversion | 10 | 13 | 0.77 |
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
    "passed": 53,
    "failed": [
      "tests/test_hA.py::test_A17_load_pair_counts_missing_dataset",
      "tests/test_hA.py::test_B10_timescale_rejects_string_and_array",
      "tests/test_hA.py::test_B11_merger_rate_scalar_rejections",
      "tests/test_hA.py::test_B12_merger_rate_array_rejections",
      "tests/test_hA.py::test_B15_rejection_messages_name_the_reason",
      "tests/test_hA.py::test_C11_validation_result_keys",
      "tests/test_hB.py::test_E07_end_to_end_science",
      "tests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "t_B15_rejection_messages_name_the_reason\n    assert_rejects_with(\"shape\", MR.compute_pair_fraction,\ntests/test_hA.py:57: in assert_rejects_with\n    with pytest.raises(AssertionError, match=pattern):\n         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE   AssertionError: Regex pattern did not match.\nE     Expected regex: 'shape'\nE     Actual message: 'Shape mismatch: n_pairs (2,) vs n_galaxies (1,)'\n_______________________ test_C11_validation_result_keys ________________________\ntests/test_hA.py:589: in test_C11_validation_result_keys\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:557: in _parse_bin_line\n    assert all((mass, slope, slope_err, expected, excluded, status)), line\nE   AssertionError:   Bin 0  [8.0, 8.5)  slope=1.0000 +/- 0.0966  expected=1.0000  N_excluded=0  PASS\nE   assert False\nE    +  where False = all((<re.Match object; span=(9, 19), match='[8.0, 8.5)'>, <re.Match object; span=(21, 33), match='slope=1.0000'>, <re.Match object; span=(34, 44), match='+/- 0.0966'>, <re.Match object; span=(46, 61), match='expected=1.0000'>, <re.Match object; span=(63, 75), match='N_excluded=0'>, None))\n_________________________ test_E07_end_to_end_science __________________________\ntests/test_hB.py:294: in test_E07_end_to_end_science\n    assert d[\"consistent\"] is True, d\nE   AssertionError: {'mass_bin': 0, 'slope': np.float64(0.9267762335105321), 'slope_err': np.float64(0.13946676597215996), 'intercept': np.float64(-6.3196658466462), ...}\nE   assert np.True_ is True\n_______________ test_E09_expected_slope_tracks_nondefault_alpha ________________\ntests/test_hB.py:322: in test_E09_expected_slope_tracks_nondefault_alpha\n    assert d[\"consistent\"] is True, d\nE   AssertionError: {'mass_bin': 0, 'slope': np.float64(0.6267762335105316), 'slope_err': np.float64(0.13946676597215996), 'intercept': np.float64(-6.319665846646201), ...}\nE   assert np.True_ is True\n=============================== warnings summary ===============================\ntests/test_hA.py::test_A05_pair_fraction_pinned\ntests/test_hA.py::test_A06_zero_zero_bin_exact_zero\ntests/test_hB.py::test_E04_per_file_box_size_used\n  /Users/dcroton/Local/git-repos/ai-agent-bench/eval/results/tmp/worktrees/20260906T094345Z-001-merger-rate-feature-macstudio_kwaipilot_kat-coder-v2.5-dev-q8-sixth-session-20260906-kat-coder-v2.5-dev-q8-opencode-macstudio_kwaipilot_kat-coder-v2.5-dev-q8-2-9530e1/tests/../src/merger_rate.py:139: RuntimeWarning: invalid value encountered in divide\n    f_pair / np.sqrt(n_pairs_f),\n\ntests/test_hA.py::test_A06_zero_zero_bin_exact_zero\ntests/test_hB.py::test_E04_per_file_box_size_used\n  /Users/dcroton/Local/git-repos/ai-agent-bench/eval/results/tmp/worktrees/20260906T094345Z-001-merger-rate-feature-macstudio_kwaipilot_kat-coder-v2.5-dev-q8-sixth-session-20260906-kat-coder-v2.5-dev-q8-opencode-macstudio_kwaipilot_kat-coder-v2.5-dev-q8-2-9530e1/tests/../src/merger_rate.py:136: RuntimeWarning: invalid value encountered in divide\n    f_pair = np.where(n_galaxies_f > 0, n_pairs_f / n_galaxies_f, 0.0)\n\n-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A17_load_pair_counts_missing_dataset - KeyError...\nFAILED tests/test_hA.py::test_B10_timescale_rejects_string_and_array - Assert...\nFAILED tests/test_hA.py::test_B11_merger_rate_scalar_rejections - AssertionEr...\nFAILED tests/test_hA.py::test_B12_merger_rate_array_rejections - AssertionErr...\nFAILED tests/test_hA.py::test_B15_rejection_messages_name_the_reason - Assert...\nFAILED tests/test_hA.py::test_C11_validation_result_keys - AssertionError:   ...\nFAILED tests/test_hB.py::test_E07_end_to_end_science - AssertionError: {'mass...\nFAILED tests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha - As...\n=================== 8 failed, 53 passed, 5 warnings in 2.04s ===================\n",
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
        "passed": 10,
        "collected": 13,
        "fraction": 0.7692307692307693,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_B10_timescale_rejects_string_and_array",
          "tests/test_hA.py::test_B11_merger_rate_scalar_rejections",
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
      "tests/test_merger_rate.py::TestCalcIntegration::test_new_dataset_and_attr_present",
      "tests/test_merger_rate.py::TestCalcMassBinEdges::test_matches_default_config",
      "tests/test_merger_rate.py::TestCalcMassBinEdges::test_right_open_excludes_upper_edge",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_asserts_n_sigma",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_bad_slope_err[-0.1]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_bad_slope_err[0.0]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_bad_slope_err[nan]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_far_outside",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_slope[-inf]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_slope[inf]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_slope[nan]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_within_range",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_basic_value",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_negative_n_galaxies_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_non_integer_n_galaxies_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reduced_identity",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_box_size[-1.0-positive]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_box_size[0.0-positive]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_box_size[500-scalar]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_box_size[True-boolean]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_box_size[bad_box5-scalar]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_box_size[nan-finite]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_merger_fraction[-0.1-merger_fraction]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_merger_fraction[0.0-merger_fraction]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_merger_fraction[0.6-scalar]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_merger_fraction[1.1-merger_fraction]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_merger_fraction[nan-finite]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_timescale[0.0-positive]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_timescale[2.2-scalar]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_timescale[nan-finite]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_shape_mismatch_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_with_nonzero_fraction_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_with_zero_fraction_valid",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_sigma_f_pair_yields_zero_sigma_rate",
      "tests/test_merger_rate.py::TestComputePairFraction::test_asserts_n_pairs_gt_0_requires_n_gal_gt_0",
      "tests/test_merger_rate.py::TestComputePairFraction::test_basic_values",
      "tests/test_merger_rate.py::TestComputePairFraction::test_integer_dtype_accepted",
      "tests/test_merger_rate.py::TestComputePairFraction::test_integer_valued_float64_accepted",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_invalid_inputs[bad_pairs0-bad_gals0-Shape mismatch]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_invalid_inputs[bad_pairs1-bad_gals1-must be 1D]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_invalid_inputs[bad_pairs2-bad_gals2-negative]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_invalid_inputs[bad_pairs3-bad_gals3-non-finite]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_invalid_inputs[bad_pairs4-bad_gals4-non-integer]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_zero_pairs_zero_galaxies",
      "tests/test_merger_rate.py::TestConfigKeys::test_default_values",
      "tests/test_merger_rate.py::TestConfigKeys::test_no_existing_key_changed",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_exact_upper_edge_excluded",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_sum_equals_selected_count",
      "tests/test_merger_rate.py::TestDocstrings::test_compute_merger_rate_docstring",
      "tests/test_merger_rate.py::TestDocstrings::test_compute_pair_fraction_docstring",
      "tests/test_merger_rate.py::TestEndToEndMockData::test_box_size_mpc_from_file_not_config",
      "tests/test_merger_rate.py::TestEndToEndMockData::test_output_schema",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_all_same_redshift_returns_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_exact_power_law",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_exactly_two_points_returns_finite",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fewer_than_two_usable_points",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_malformed_redshift_raises",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_n_excluded_correct",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_shape_rank_violations_raise",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_slope_err_hand_computed",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_weighted_vs_unweighted",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_excludes_mass_bin_minus_one",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_bad_box_size_mpc[(500+0j)-ndarray]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_bad_box_size_mpc[-1.0-positive]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_bad_box_size_mpc[0.0-positive]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_bad_box_size_mpc[500-scalar0]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_bad_box_size_mpc[500-scalar1]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_bad_box_size_mpc[True-scalar]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_bad_box_size_mpc[bad_val7-scalar]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_bad_box_size_mpc[inf-finite]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_bad_box_size_mpc[nan-finite]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_index_outside_range",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_attr",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_dataset",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_file",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_wrong_n_galaxies_length",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_returns_known_values",
      "tests/test_merger_rate.py::TestMergerTimescale::test_at_z_zero",
      "tests/test_merger_rate.py::TestMergerTimescale::test_power_law_value",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_bad_t0[-1.0-positive]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_bad_t0[0.0-positive]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_bad_t0[inf-finite]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_bad_t0[nan-finite]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_bad_z[-1.0-> -1]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_bad_z[-2.0-> -1]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_bad_z[-inf-finite]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_bad_z[inf-finite]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_bad_z[nan-finite]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_invalid_scalar_form[2-z]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_invalid_scalar_form[2.0-z]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_invalid_scalar_form[True-z]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_invalid_scalar_form[bad_val2-z]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_invalid_scalar_form[bad_val3-z]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_non_finite_alpha",
      "tests/test_merger_rate.py::TestRegression::test_existing_tests_pass",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_mass_bin_by_not_primary_raises",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_malformed_redshift_attr_leaves_output_untouched",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_mismatched_redshift_leaves_output_untouched",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_missing_file_leaves_output_untouched",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_expected_slope_tracks_config_alpha",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_insufficient_data_prints_correctly",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_malformed_stored_redshift_raises_before_fit",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_output_contains_expected_keys",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_slope_consistent_on_mock_data",
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
      "tests/test_pair_finder.py::TestVelocityRecovery::test_velocity_is_symmetric
```
