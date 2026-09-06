# Trial report: 20260905T142934Z-001-merger-rate-feature-opencode-go_deepseek-v4-flash-local-cloud-20260906-opencode-opencode-go_deepseek-v4-flash-2-0abb56

- Task: `001-merger-rate-feature`
- Model: `opencode-go/deepseek-v4-flash` (harness: opencode)
- Model duration: 717.5s | venv setup: 26.0s | timed out: False | committed: False
- Changed files: src/calc.py, src/config.py, src/merger_rate.py, tests/test_merger_rate.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 90.3 / 100

## Judged: readability 75% of weight, maintainability 75% of weight (judge claude-opus-5, status ok)

## Composite score: 88.0 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 98% |
| test_adequacy | automated | 25 | 70% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 100% |
| readability | judged | 8 | 75% |
| maintainability | judged | 7 | 75% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| calc_galaxy_denominator | 4 | 4 | 1.00 |
| persistence_schema_provenance | 5 | 5 | 1.00 |
| load_pair_counts_rejections | 8 | 8 | 1.00 |
| pair_fraction_core | 10 | 10 | 1.00 |
| merger_timescale_and_rate_conversion | 13 | 13 | 1.00 |
| run_merger_rate_calculation_pipeline | 4 | 4 | 1.00 |
| redshift_evolution_fit_and_consistency | 10 | 10 | 1.00 |
| validation_reporting_and_e2e | 6 | 7 | 0.86 |

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
    "passed": 60,
    "failed": [
      "tests/test_hA.py::test_C11_validation_result_keys"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "                    [ 42%]\ntests/test_hA.py::test_B04_merger_rate_pinned PASSED                     [ 44%]\ntests/test_hA.py::test_B05_reduced_identity_exact PASSED                 [ 45%]\ntests/test_hA.py::test_B06_zero_sigma_exact_zero PASSED                  [ 47%]\ntests/test_hA.py::test_B07_zero_galaxies_rules PASSED                    [ 49%]\ntests/test_hA.py::test_B08_mass_bin_by_assertion PASSED                  [ 50%]\ntests/test_hA.py::test_B09_timescale_rejections PASSED                   [ 52%]\ntests/test_hA.py::test_B10_timescale_rejects_string_and_array PASSED     [ 54%]\ntests/test_hA.py::test_B11_merger_rate_scalar_rejections PASSED          [ 55%]\ntests/test_hA.py::test_B12_merger_rate_array_rejections PASSED           [ 57%]\ntests/test_hA.py::test_B13_merger_rate_rejects_string_box_by_assertion PASSED [ 59%]\ntests/test_hA.py::test_B14_docstring_wording PASSED                      [ 60%]\ntests/test_hA.py::test_B15_rejection_messages_name_the_reason PASSED     [ 62%]\ntests/test_hA.py::test_C01_exact_power_law PASSED                        [ 63%]\ntests/test_hA.py::test_C02_provably_weighted PASSED                      [ 65%]\ntests/test_hA.py::test_C03_two_point_slope_err_pinned PASSED             [ 67%]\ntests/test_hA.py::test_C04_two_usable_with_exclusions_finite PASSED      [ 68%]\ntests/test_hA.py::test_C05_fewer_than_two_usable PASSED                  [ 70%]\ntests/test_hA.py::test_C06_single_redshift_returns_nan PASSED            [ 72%]\ntests/test_hA.py::test_C07_malformed_redshifts_and_rank PASSED           [ 73%]\ntests/test_hA.py::test_C08_check_slope_consistency PASSED                [ 75%]\ntests/test_hA.py::test_C09_collapsed_predictor PASSED                    [ 77%]\ntests/test_hA.py::test_C10_y_centring_numerical_stability PASSED         [ 78%]\ntests/test_hA.py::test_C11_validation_result_keys FAILED                 [ 80%]\ntests/test_hA.py::test_C12_validation_rejects_malformed_stored_redshift_before_fit PASSED [ 81%]\ntests/test_hA.py::test_C13_validation_prints_insufficient_data PASSED    [ 83%]\ntests/test_hA.py::test_C14_mass_bin_is_index_not_string PASSED           [ 85%]\ntests/test_hA.py::test_C15_consistent_is_python_bool_or_none PASSED      [ 86%]\ntests/test_hB.py::test_E01_slice1_additive_schema PASSED                 [ 88%]\ntests/test_hB.py::test_E02_denominator_from_full_catalog PASSED          [ 90%]\ntests/test_hB.py::test_E03_box_size_from_catalog_not_config PASSED       [ 91%]\ntests/test_hB.py::test_E04_per_file_box_size_used PASSED                 [ 93%]\ntests/test_hB.py::test_E05_preflight_atomicity_sha256 PASSED             [ 95%]\ntests/test_hB.py::test_E06_output_schema PASSED                          [ 96%]\ntests/test_hB.py::test_E07_end_to_end_science PASSED                     [ 98%]\ntests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha PASSED [100%]\n\n=================================== FAILURES ===================================\n_______________________ test_C11_validation_result_keys ________________________\ntests/test_hA.py:589: in test_C11_validation_result_keys\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:557: in _parse_bin_line\n    assert all((mass, slope, slope_err, expected, excluded, status)), line\nE   AssertionError:   bin 0: mass [8.0, 8.5) slope=1.0000 +/- 0.0966 expected=1.0000 n_excluded=0 -> consistent\nE   assert False\nE    +  where False = all((<re.Match object; span=(14, 24), match='[8.0, 8.5)'>, <re.Match object; span=(25, 37), match='slope=1.0000'>, <re.Match object; span=(38, 48), match='+/- 0.0966'>, <re.Match object; span=(49, 64), match='expected=1.0000'>, <re.Match object; span=(65, 77), match='n_excluded=0'>, None))\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_C11_validation_result_keys - AssertionError:   ...\n========================= 1 failed, 60 passed in 1.89s =========================\n",
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
        "passed": 10,
        "collected": 10,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
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
        "passed": 6,
        "collected": 7,
        "fraction": 0.8571428571428571,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_C11_validation_result_keys"
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
      "tests/test_merger_rate.py::TestCalcMassBinEdges::test_default_edges",
      "tests/test_merger_rate.py::TestCalcMassBinEdges::test_matches_pair_finder",
      "tests/test_merger_rate.py::TestCalcSavePairsOutput::test_box_size_from_catalog_not_config",
      "tests/test_merger_rate.py::TestCalcSavePairsOutput::test_existing_datasets_unchanged",
      "tests/test_merger_rate.py::TestCalcSavePairsOutput::test_new_dataset_and_attr_present",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_asserts_on_invalid_n_sigma[-1.0]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_asserts_on_invalid_n_sigma[0.0]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_asserts_on_invalid_n_sigma[inf]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_asserts_on_invalid_n_sigma[nan]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_far_outside",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_for_non_finite_or_non_positive[args0]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_for_non_finite_or_non_positive[args1]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_for_non_finite_or_non_positive[args2]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_for_non_finite_or_non_positive[args3]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_for_non_finite_or_non_positive[args4]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_for_non_finite_or_non_positive[args5]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_true_within_range",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_docstring_contains_convention_sentence",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_exact_values",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reduced_identity",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_box[-1.0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_box[0.0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_box[inf]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_box[nan]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_box_scalar_form[(500+0j)]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_box_scalar_form[500_0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_box_scalar_form[500_1]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_box_scalar_form[True]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_box_scalar_form[bad4]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_merger_fraction[-0.1]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_merger_fraction[0.0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_merger_fraction[1.5]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_merger_fraction[inf]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_merger_fraction[nan]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_timescale[-1.0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_timescale[0.0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_timescale[inf]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_timescale[nan]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_mismatched_arrays",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_negative_array_values",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_non_1d",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_non_finite_array_values",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_non_integer_n_galaxies",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_with_both_zero_valid",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_with_nonzero_f_pair_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_with_nonzero_sigma_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_sigma_f_pair_gives_zero_sigma_rate",
      "tests/test_merger_rate.py::TestComputePairFraction::test_accepts_integer_dtypes",
      "tests/test_merger_rate.py::TestComputePairFraction::test_accepts_integer_valued_float64",
      "tests/test_merger_rate.py::TestComputePairFraction::test_asserts_pair_without_galaxy",
      "tests/test_merger_rate.py::TestComputePairFraction::test_docstring_contains_convention_sentence",
      "tests/test_merger_rate.py::TestComputePairFraction::test_exact_values",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_mismatched_shapes",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_negative",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_1d",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_finite",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_integer",
      "tests/test_merger_rate.py::TestComputePairFraction::test_zero_zero_bin_is_exact_zero",
      "tests/test_merger_rate.py::TestConfigKeys::test_default_values",
      "tests/test_merger_rate.py::TestConfigKeys::test_existing_keys_unchanged",
      "tests/test_merger_rate.py::TestConfigKeys::test_three_keys_added",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_denominator_from_full_catalog",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_exact_upper_edge_excluded",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_returns_int_array_length_n_bins",
      "tests/test_merger_rate.py::TestEndToEnd::test_end_to_end_with_non_default_alpha",
      "tests/test_merger_rate.py::TestEndToEnd::test_mock_data_recovers_injected_timescale",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_all_sharing_single_redshift",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_collapsed_predictor_from_rounding",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_exact_power_law_recovered",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_exactly_two_usable_points_finite",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fewer_than_two_usable_points",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_malformed_redshift_asserts[z0]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_malformed_redshift_asserts[z1]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_malformed_redshift_asserts[z2]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_provably_weighted",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_shape_rank_violations_assert[args0]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_shape_rank_violations_assert[args1]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_shape_rank_violations_assert[args2]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_shape_rank_violations_assert[args3]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_shape_rank_violations_assert[args4]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_single_usable_point",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_slope_err_hand_computed",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_known_values_from_fixture",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size_scalar_form[(500+0j)]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size_scalar_form[500_0]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size_scalar_form[500_1]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size_scalar_form[bad3]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_attr",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_dataset",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_file",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_non_finite_box_size",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_non_positive_box_size",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_out_of_range_mass_bin",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_wrong_length_dataset",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_accepts_numpy_scalars",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_at_z0",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_custom_values",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_gyr0[-1.0]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_gyr0[0.0]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_gyr0[inf]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_gyr0[nan]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_gyr0_scalar_form[(2+0j)]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_gyr0_scalar_form[2_0]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_gyr0_scalar_form[2_1]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_gyr0_scalar_form[True]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_gyr0_scalar_form[bad4]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_form[(1+0j)]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_form[1_0]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_form[1_1]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_form[True]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_scalar_form[bad4]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_z[-1.0]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_z[-5.0]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_z[-inf]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_z[inf]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_invalid_z[nan]",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_non_finite_alpha",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_mass_bin_by_primary_required",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_per_file_box_size_used",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_malformed_redshift_attr_leaves_output_untouched",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_mismatched_redshift_leaves_output_untouched",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_missing_pair_file_leaves_output_untouched",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_written_schema",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_expected_slope_tracks_non_default_alpha",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_fails_on_malformed_stored_redshift_before_any_fit",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_heading_and_parseable_lines",
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
```
