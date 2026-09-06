# Trial report: 20260905T175618Z-001-merger-rate-feature-macstudio_ornith_ornith-1.5-397b-q6-local-cloud-20260906-opencode-macstudio_ornith_ornith-1.5-397b-q6-3-ac74c2

- Task: `001-merger-rate-feature`
- Model: `macstudio/ornith/ornith-1.5-397b-q6` (harness: opencode)
- Model duration: 5021.4s | venv setup: 28.4s | timed out: False | committed: False
- Changed files: src/calc.py, src/config.py, src/merger_rate.py, tests/test_merger_rate.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 87.7 / 100

## Judged: readability 75% of weight, maintainability 50% of weight (judge claude-opus-5, status ok)

## Composite score: 84.0 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 95% |
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
| merger_timescale_and_rate_conversion | 13 | 13 | 1.00 |
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
    "passed": 58,
    "failed": [
      "tests/test_hA.py::test_B15_rejection_messages_name_the_reason",
      "tests/test_hA.py::test_C11_validation_result_keys",
      "tests/test_hA.py::test_C13_validation_prints_insufficient_data"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "test_B14_docstring_wording PASSED                      [ 60%]\ntests/test_hA.py::test_B15_rejection_messages_name_the_reason FAILED     [ 62%]\ntests/test_hA.py::test_C01_exact_power_law PASSED                        [ 63%]\ntests/test_hA.py::test_C02_provably_weighted PASSED                      [ 65%]\ntests/test_hA.py::test_C03_two_point_slope_err_pinned PASSED             [ 67%]\ntests/test_hA.py::test_C04_two_usable_with_exclusions_finite PASSED      [ 68%]\ntests/test_hA.py::test_C05_fewer_than_two_usable PASSED                  [ 70%]\ntests/test_hA.py::test_C06_single_redshift_returns_nan PASSED            [ 72%]\ntests/test_hA.py::test_C07_malformed_redshifts_and_rank PASSED           [ 73%]\ntests/test_hA.py::test_C08_check_slope_consistency PASSED                [ 75%]\ntests/test_hA.py::test_C09_collapsed_predictor PASSED                    [ 77%]\ntests/test_hA.py::test_C10_y_centring_numerical_stability PASSED         [ 78%]\ntests/test_hA.py::test_C11_validation_result_keys FAILED                 [ 80%]\ntests/test_hA.py::test_C12_validation_rejects_malformed_stored_redshift_before_fit PASSED [ 81%]\ntests/test_hA.py::test_C13_validation_prints_insufficient_data FAILED    [ 83%]\ntests/test_hA.py::test_C14_mass_bin_is_index_not_string PASSED           [ 85%]\ntests/test_hA.py::test_C15_consistent_is_python_bool_or_none PASSED      [ 86%]\ntests/test_hB.py::test_E01_slice1_additive_schema PASSED                 [ 88%]\ntests/test_hB.py::test_E02_denominator_from_full_catalog PASSED          [ 90%]\ntests/test_hB.py::test_E03_box_size_from_catalog_not_config PASSED       [ 91%]\ntests/test_hB.py::test_E04_per_file_box_size_used PASSED                 [ 93%]\ntests/test_hB.py::test_E05_preflight_atomicity_sha256 PASSED             [ 95%]\ntests/test_hB.py::test_E06_output_schema PASSED                          [ 96%]\ntests/test_hB.py::test_E07_end_to_end_science PASSED                     [ 98%]\ntests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha PASSED [100%]\n\n=================================== FAILURES ===================================\n_________________ test_B15_rejection_messages_name_the_reason __________________\ntests/test_hA.py:407: in test_B15_rejection_messages_name_the_reason\n    assert_rejects_with(\"n_pairs\", MR.compute_pair_fraction,\ntests/test_hA.py:57: in assert_rejects_with\n    with pytest.raises(AssertionError, match=pattern):\n         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE   AssertionError: Regex pattern did not match.\nE     Expected regex: 'n_pairs'\nE     Actual message: 'a bin has pairs but zero galaxies'\n_______________________ test_C11_validation_result_keys ________________________\ntests/test_hA.py:589: in test_C11_validation_result_keys\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:544: in _parse_bin_line\n    assert len(lines) == 1, f\"expected one output line for bin {b}, got {lines!r}\"\nE   AssertionError: expected one output line for bin 0, got []\nE   assert 0 == 1\nE    +  where 0 = len([])\n_________________ test_C13_validation_prints_insufficient_data _________________\ntests/test_hA.py:640: in test_C13_validation_prints_insufficient_data\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:544: in _parse_bin_line\n    assert len(lines) == 1, f\"expected one output line for bin {b}, got {lines!r}\"\nE   AssertionError: expected one output line for bin 0, got []\nE   assert 0 == 1\nE    +  where 0 = len([])\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_B15_rejection_messages_name_the_reason - Assert...\nFAILED tests/test_hA.py::test_C11_validation_result_keys - AssertionError: ex...\nFAILED tests/test_hA.py::test_C13_validation_prints_insufficient_data - Asser...\n========================= 3 failed, 58 passed in 1.87s =========================\n",
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
        "passed": 13,
        "collected": 13,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
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
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_bad_n_sigma_asserts[-1.0]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_bad_n_sigma_asserts[0.0]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_bad_n_sigma_asserts[3]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_bad_n_sigma_asserts[inf]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_bad_n_sigma_asserts[nan]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_applicable_returns_false[1.0--0.1-1.0]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_applicable_returns_false[1.0-0.0-1.0]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_applicable_returns_false[1.0-0.1-nan]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_applicable_returns_false[1.0-nan-1.0]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_applicable_returns_false[nan-0.1-1.0]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_within_range_true_far_false",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_bad_box_scalar_rejected[(500+0j)]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_bad_box_scalar_rejected[-500.0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_bad_box_scalar_rejected[0.0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_bad_box_scalar_rejected[500_0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_bad_box_scalar_rejected[500_1]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_bad_box_scalar_rejected[True]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_bad_box_scalar_rejected[bad7]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_bad_box_scalar_rejected[inf]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_bad_box_scalar_rejected[nan]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_bad_timescale_scalar_rejected[(2.2+0j)]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_bad_timescale_scalar_rejected[-2.2]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_bad_timescale_scalar_rejected[0.0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_bad_timescale_scalar_rejected[2.2]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_bad_timescale_scalar_rejected[True]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_bad_timescale_scalar_rejected[bad6]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_bad_timescale_scalar_rejected[inf]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_bad_timescale_scalar_rejected[nan]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_merger_fraction_one_accepted",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_merger_fraction_out_of_range_rejected[-0.1]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_merger_fraction_out_of_range_rejected[0.0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_merger_fraction_out_of_range_rejected[1.5]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_merger_fraction_out_of_range_rejected[inf]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_merger_fraction_out_of_range_rejected[nan]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_noninteger_ngalaxies_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_pinned_values",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reduced_identity",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_shape_and_rank_rejections",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_ngal_with_signal_rejected_both_zero_valid",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_sigma_f_pair_gives_exact_zero",
      "tests/test_merger_rate.py::TestComputePairFraction::test_accepts_integer_valued_float64",
      "tests/test_merger_rate.py::TestComputePairFraction::test_empty_bin_both_zero_exact",
      "tests/test_merger_rate.py::TestComputePairFraction::test_f_pair_can_exceed_one",
      "tests/test_merger_rate.py::TestComputePairFraction::test_pairs_without_galaxies_rejected",
      "tests/test_merger_rate.py::TestComputePairFraction::test_pinned_values",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejections[bad0]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejections[bad1]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejections[bad2]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejections[bad3]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejections[bad4]",
      "tests/test_merger_rate.py::TestConfigKeys::test_keys_added_existing_unchanged",
      "tests/test_merger_rate.py::TestCountHelper::test_count_ignores_mass_bin_by",
      "tests/test_merger_rate.py::TestCountHelper::test_exact_edge_exclusion",
      "tests/test_merger_rate.py::TestCountHelper::test_matches_assign_mass_bins_rule",
      "tests/test_merger_rate.py::TestCountHelper::test_returns_int_array_of_correct_length",
      "tests/test_merger_rate.py::TestDocstringContract::test_required_sentence_present",
      "tests/test_merger_rate.py::TestFit::test_all_zero_rates_returns_nans",
      "tests/test_merger_rate.py::TestFit::test_fewer_than_two_usable_returns_nans",
      "tests/test_merger_rate.py::TestFit::test_is_weighted_beats_unweighted_with_outlier",
      "tests/test_merger_rate.py::TestFit::test_malformed_redshifts_fail[bad_z0]",
      "tests/test_merger_rate.py::TestFit::test_malformed_redshifts_fail[bad_z1]",
      "tests/test_merger_rate.py::TestFit::test_malformed_redshifts_fail[bad_z2]",
      "tests/test_merger_rate.py::TestFit::test_nextafter_collapse_returns_nans",
      "tests/test_merger_rate.py::TestFit::test_power_law_recovered",
      "tests/test_merger_rate.py::TestFit::test_rank_and_shape_violations_fail",
      "tests/test_merger_rate.py::TestFit::test_single_distinct_redshift_returns_nans",
      "tests/test_merger_rate.py::TestFit::test_two_point_slope_err_pinned",
      "tests/test_merger_rate.py::TestFit::test_two_usable_points_returns_finite_fit_with_correct_exclusions",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_bad_box_scalar_rejected[(250+0j)]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_bad_box_scalar_rejected[-250.0]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_bad_box_scalar_rejected[0.0]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_bad_box_scalar_rejected[250.0_0]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_bad_box_scalar_rejected[250.0_1]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_bad_box_scalar_rejected[True]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_bad_box_scalar_rejected[bad_box0]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_bad_box_scalar_rejected[inf]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_index_out_of_range_rejected",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_known_values_and_sentinel_excluded",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_missing_box_attr_rejected",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_missing_dataset_rejected[mass_bin]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_missing_dataset_rejected[n_galaxies_per_mass_bin]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_missing_file_rejected",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_negative_index_below_sentinel_rejected",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_wrong_length_n_galaxies_rejected",
      "tests/test_merger_rate.py::TestMergerTimescale::test_invalid_scalar_form_rejected[merger_timescale_alpha-bad5]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_invalid_scalar_form_rejected[merger_timescale_gyr0-(2.2+0j)]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_invalid_scalar_form_rejected[merger_timescale_gyr0-2.2_0]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_invalid_scalar_form_rejected[merger_timescale_gyr0-2.2_1]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_invalid_scalar_form_rejected[merger_timescale_gyr0-True]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_invalid_scalar_form_rejected[merger_timescale_gyr0-bad3]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_nondefault_params_pinned",
      "tests/test_merger_rate.py::TestMergerTimescale::test_nonfinite_alpha_rejected",
      "tests/test_merger_rate.py::TestMergerTimescale::test_nonfinite_gyr0_rejected",
      "tests/test_merger_rate.py::TestMergerTimescale::test_nonfinite_z_rejected[inf]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_nonfinite_z_rejected[nan]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_nonpositive_gyr0_rejected",
      "tests/test_merger_rate.py::TestMergerTimescale::test_string_z_rejected_before_coercion",
      "tests/test_merger_rate.py::TestMergerTimescale::test_z0_returns_normalization_exactly",
      "tests/test_merger_rate.py::TestMergerTimescale::test_z_le_minus_one_rejected[-1.0]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_z_le_minus_one_rejected[-2.0]",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_mass_bin_by_must_be_primary",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_output_schema_and_shapes",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_malformed_redshift_attr_leaves_output_untouched[(2+0j)]",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_malformed_redshift_attr_leaves_output_untouched[True]",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_malformed_redshift_attr_leaves_output_untouched[abc]",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_malformed_redshift_attr_leaves_output_untouched[bad_z1]",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_missing_pair_file_leaves_output_untouched",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_redshift_mismatch_leaves_output_untouched",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_uses_per_file_box_not_config",
      "tests/test_merger_rate.py::TestRunValidation::test_end_to_end_consistency_default_alpha",
      "tests/test_merger_rate.py::TestRunValidation::test_end_to_end_consistency_nondefault_alpha",
      "tests/test_merger_rate.py::TestRunValidation::test_expected_slope_tracks_nondefault_alpha",
      "tests/test_merger_rate.py::TestRunValidation::test_insufficient_data_line_and_heading",
      "tests/test_merger_rate.py::TestRunValidation::test_malformed_stored_redshift_fails_before_fit",
      "tests/test_merger_rate.py::TestSavePairsAndRunCalculation::test_box_size_comes_from_catalog_not_config",
      "tests/test_merger_rate.py::TestSavePairsAndRunCalculation::test_denominator_is_full_selected_catalog",
      "tests/test_merger_rate.py::TestSavePairsAndRunCalculation::test_new_dataset_and_attr_present_existing_unchanged",
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
      "tests/test_pair_f
```
