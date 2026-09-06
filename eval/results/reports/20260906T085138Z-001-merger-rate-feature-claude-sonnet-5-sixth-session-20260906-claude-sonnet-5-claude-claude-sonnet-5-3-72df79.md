# Trial report: 20260906T085138Z-001-merger-rate-feature-claude-sonnet-5-sixth-session-20260906-claude-sonnet-5-claude-claude-sonnet-5-3-72df79

- Task: `001-merger-rate-feature`
- Model: `claude-sonnet-5` (harness: claude)
- Model duration: 780.9s | venv setup: 26.3s | timed out: False | committed: False
- Changed files: src/calc.py, src/config.py, src/merger_rate.py, tests/test_merger_rate.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 88.8 / 100

## Judged: readability 100% of weight, maintainability 75% of weight (judge claude-opus-5, status ok)

## Composite score: 88.7 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 94% |
| test_adequacy | automated | 25 | 71% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 100% |
| readability | judged | 8 | 100% |
| maintainability | judged | 7 | 75% |

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
    "raw_tail": "           [ 85%]\ntests/test_hA.py::test_C15_consistent_is_python_bool_or_none PASSED      [ 86%]\ntests/test_hB.py::test_E01_slice1_additive_schema PASSED                 [ 88%]\ntests/test_hB.py::test_E02_denominator_from_full_catalog PASSED          [ 90%]\ntests/test_hB.py::test_E03_box_size_from_catalog_not_config PASSED       [ 91%]\ntests/test_hB.py::test_E04_per_file_box_size_used PASSED                 [ 93%]\ntests/test_hB.py::test_E05_preflight_atomicity_sha256 PASSED             [ 95%]\ntests/test_hB.py::test_E06_output_schema PASSED                          [ 96%]\ntests/test_hB.py::test_E07_end_to_end_science PASSED                     [ 98%]\ntests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha PASSED [100%]\n\n=================================== FAILURES ===================================\n__________________________ test_B14_docstring_wording __________________________\ntests/test_hA.py:395: in test_B14_docstring_wording\n    assert required in doc, f\"{fn.__name__} lacks the required uncertainty wording\"\nE   AssertionError: compute_pair_fraction lacks the required uncertainty wording\nE   assert \"Uncertainty follows Task 001's plug-in Poisson-error convention; it is not a confidence interval.\" in \"Compute the pairs-per-galaxy incidence ratio f_pair and its uncertainty,\\nvectorized over the mass-bin array.\\n\\nf_pair(b)       = n_pairs(b) / n_galaxies(b)\\nsigma_f_pair(b) = f_pair(b) / sqrt(n_pairs(b))   if n_pairs(b) > 0 else 0\\n\\nf_pair is a pairs-per-galaxy incidence ratio, not a probability bounded\\nby 1: a single galaxy can appear in several stored pairs, so f_pair > 1\\nis legal in a crowded bin.\\n\\nUncertainty follows Task 001's plug-in Poisson-error convention; it is\\nnot a confidence interval.\\n\\nParameters\\n----------\\nn_pairs, n_galaxies : array-like, 1D, identically shaped\\n    Finite, non-negative, integer-valued counts, below 2**53.\\n\\nReturns\\n-------\\n(f_pair, sigma_f_pair) : tuple of float ndarrays, same shape as input.\"\n_________________ test_B15_rejection_messages_name_the_reason __________________\ntests/test_hA.py:401: in test_B15_rejection_messages_name_the_reason\n    assert_rejects_with(\"non-negative\", MR.compute_pair_fraction,\ntests/test_hA.py:57: in assert_rejects_with\n    with pytest.raises(AssertionError, match=pattern):\n         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE   AssertionError: Regex pattern did not match.\nE     Expected regex: 'non-negative'\nE     Actual message: 'n_pairs contains negative values: [-1.]'\n_______________________ test_C11_validation_result_keys ________________________\ntests/test_hA.py:589: in test_C11_validation_result_keys\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:544: in _parse_bin_line\n    assert len(lines) == 1, f\"expected one output line for bin {b}, got {lines!r}\"\nE   AssertionError: expected one output line for bin 0, got []\nE   assert 0 == 1\nE    +  where 0 = len([])\n_________________ test_C13_validation_prints_insufficient_data _________________\ntests/test_hA.py:640: in test_C13_validation_prints_insufficient_data\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:544: in _parse_bin_line\n    assert len(lines) == 1, f\"expected one output line for bin {b}, got {lines!r}\"\nE   AssertionError: expected one output line for bin 0, got []\nE   assert 0 == 1\nE    +  where 0 = len([])\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_B14_docstring_wording - AssertionError: compute...\nFAILED tests/test_hA.py::test_B15_rejection_messages_name_the_reason - Assert...\nFAILED tests/test_hA.py::test_C11_validation_result_keys - AssertionError: ex...\nFAILED tests/test_hA.py::test_C13_validation_prints_insufficient_data - Asser...\n========================= 4 failed, 57 passed in 1.90s =========================\n",
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
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_far_outside",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_for_non_finite_inputs[1.0-0.1-nan]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_for_non_finite_inputs[1.0-nan-1.0]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_for_non_finite_inputs[inf-0.1-1.0]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_for_non_finite_inputs[nan-0.1-1.0]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_for_nonpositive_slope_err",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_rejects_bad_n_sigma[-1.0]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_rejects_bad_n_sigma[0.0]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_rejects_bad_n_sigma[inf]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_rejects_bad_n_sigma[nan]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_true_within_range",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_accepts_merger_fraction_of_exactly_one",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_pinned_values",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reduced_identity",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_box_size_mpc[-1.0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_box_size_mpc[0.0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_box_size_mpc[inf]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_box_size_mpc[nan]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_merger_fraction[-0.1]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_merger_fraction[0.0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_merger_fraction[1.1]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_merger_fraction[inf]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_merger_fraction[nan]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_timescale_gyr[-1.0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_timescale_gyr[0.0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_timescale_gyr[inf]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_timescale_gyr[nan]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form_of_box_size_mpc[(500+0j)]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form_of_box_size_mpc[500.0_0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form_of_box_size_mpc[500.0_1]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form_of_box_size_mpc[True]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form_of_box_size_mpc[bad_val3]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form_of_merger_fraction[(0.6+0j)]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form_of_merger_fraction[0.6_0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form_of_merger_fraction[0.6_1]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form_of_merger_fraction[True]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form_of_merger_fraction[bad_val3]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form_of_timescale_gyr[(2.2+0j)]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form_of_timescale_gyr[2.2_0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form_of_timescale_gyr[2.2_1]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form_of_timescale_gyr[True]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form_of_timescale_gyr[bad_val3]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_mismatched_array_shapes",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_negative_array_values",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_non_1d_arrays",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_non_finite_array_values",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_non_integer_n_galaxies",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_nonzero_fraction_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_zero_fraction_is_valid",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_sigma_f_pair_gives_exact_zero_sigma_rate",
      "tests/test_merger_rate.py::TestComputePairFraction::test_accepts_integer_dtype",
      "tests/test_merger_rate.py::TestComputePairFraction::test_accepts_integer_valued_float64",
      "tests/test_merger_rate.py::TestComputePairFraction::test_f_pair_can_exceed_one",
      "tests/test_merger_rate.py::TestComputePairFraction::test_pinned_values",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_mismatched_shapes",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_negative_counts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_1d",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_finite_counts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_integer_valued_counts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_pairs_without_galaxies",
      "tests/test_merger_rate.py::TestComputePairFraction::test_zero_pairs_zero_galaxies_exact_zero",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_denominator_sum_matches_selected_catalog_count",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_pinned_example",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_returns_int_array_of_correct_length",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_upper_edge_excluded_matches_pair_finder_convention",
      "tests/test_merger_rate.py::TestEndToEndMockData::test_merger_rate_finite_and_nonnegative",
      "tests/test_merger_rate.py::TestEndToEndMockData::test_slope_recovery_passes_for_every_populated_mass_bin",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_all_usable_points_share_single_redshift_returns_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_collapsed_predictor_from_distinct_but_rounding_equal_redshifts",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_exact_power_law_recovered",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_exactly_two_usable_points_returns_finite_fit",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fewer_than_two_usable_points_returns_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fit_is_provably_weighted",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_malformed_redshift_raises[-1.0]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_malformed_redshift_raises[-2.0]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_malformed_redshift_raises[inf]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_malformed_redshift_raises[nan]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_non_1d_raises",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_shape_mismatch_raises",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_slope_err_matches_hand_computed_value",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_accepts_valid_scalar_forms_of_box_size_mpc[250.0]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_accepts_valid_scalar_forms_of_box_size_mpc[250]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_accepts_valid_scalar_forms_of_box_size_mpc[good_box_size2]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_accepts_valid_scalar_forms_of_box_size_mpc[good_box_size3]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_hand_written_fixture",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_complex_box_size_mpc",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size_mpc[-5.0]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size_mpc[0.0]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size_mpc[250.0]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size_mpc[inf]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size_mpc[nan]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_mass_bin_index_outside_range",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_attr",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_dataset",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_file",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_non_scalar_box_size_mpc",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_wrong_length_n_galaxies",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_pinned_nondefault_values",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_bad_alpha[-inf]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_bad_alpha[inf]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_bad_alpha[nan]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_bad_gyr0[-1.0]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_bad_gyr0[0.0]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_bad_gyr0[inf]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_bad_gyr0[nan]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_bad_z[-1.0]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_bad_z[-2.0]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_bad_z[inf]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_bad_z[nan]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_form_of_alpha[(-1+0j)]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_form_of_alpha[-1.0_0]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_form_of_alpha[-1.0_1]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_form_of_alpha[True]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_form_of_alpha[bad_val3]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_form_of_gyr0[(2.2+0j)]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_form_of_gyr0[2.2_0]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_form_of_gyr0[2.2_1]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_form_of_gyr0[True]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_form_of_gyr0[bad_val3]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_form_of_z[(2+0j)]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_form_of_z[2.0_0]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_form_of_z[2.0_1]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_form_of_z[True]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_form_of_z[bad_z3]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_z_zero_returns_gyr0_exactly",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_config_keys_added_with_correct_defaults",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_failure_leaves_sentinel_output_unto
```
