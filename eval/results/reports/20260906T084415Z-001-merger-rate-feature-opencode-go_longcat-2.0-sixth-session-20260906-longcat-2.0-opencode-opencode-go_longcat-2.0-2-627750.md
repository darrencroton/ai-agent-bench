# Trial report: 20260906T084415Z-001-merger-rate-feature-opencode-go_longcat-2.0-sixth-session-20260906-longcat-2.0-opencode-opencode-go_longcat-2.0-2-627750

- Task: `001-merger-rate-feature`
- Model: `opencode-go/longcat-2.0` (harness: opencode)
- Model duration: 1508.5s | venv setup: 28.6s | timed out: False | committed: False
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
| correctness | automated | 40 | 93% |
| test_adequacy | automated | 25 | 75% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 83% |
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
    "passed": 57,
    "failed": [
      "tests/test_hA.py::test_B15_rejection_messages_name_the_reason",
      "tests/test_hA.py::test_C11_validation_result_keys",
      "tests/test_hB.py::test_E07_end_to_end_science",
      "tests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": " PASSED           [ 73%]\ntests/test_hA.py::test_C08_check_slope_consistency PASSED                [ 75%]\ntests/test_hA.py::test_C09_collapsed_predictor PASSED                    [ 77%]\ntests/test_hA.py::test_C10_y_centring_numerical_stability PASSED         [ 78%]\ntests/test_hA.py::test_C11_validation_result_keys FAILED                 [ 80%]\ntests/test_hA.py::test_C12_validation_rejects_malformed_stored_redshift_before_fit PASSED [ 81%]\ntests/test_hA.py::test_C13_validation_prints_insufficient_data PASSED    [ 83%]\ntests/test_hA.py::test_C14_mass_bin_is_index_not_string PASSED           [ 85%]\ntests/test_hA.py::test_C15_consistent_is_python_bool_or_none PASSED      [ 86%]\ntests/test_hB.py::test_E01_slice1_additive_schema PASSED                 [ 88%]\ntests/test_hB.py::test_E02_denominator_from_full_catalog PASSED          [ 90%]\ntests/test_hB.py::test_E03_box_size_from_catalog_not_config PASSED       [ 91%]\ntests/test_hB.py::test_E04_per_file_box_size_used PASSED                 [ 93%]\ntests/test_hB.py::test_E05_preflight_atomicity_sha256 PASSED             [ 95%]\ntests/test_hB.py::test_E06_output_schema PASSED                          [ 96%]\ntests/test_hB.py::test_E07_end_to_end_science FAILED                     [ 98%]\ntests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha FAILED [100%]\n\n=================================== FAILURES ===================================\n_________________ test_B15_rejection_messages_name_the_reason __________________\ntests/test_hA.py:407: in test_B15_rejection_messages_name_the_reason\n    assert_rejects_with(\"n_pairs\", MR.compute_pair_fraction,\ntests/test_hA.py:57: in assert_rejects_with\n    with pytest.raises(AssertionError, match=pattern):\n         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE   AssertionError: Regex pattern did not match.\nE     Expected regex: 'n_pairs'\nE     Actual message: 'a pair cannot exist in a bin with no galaxies'\n_______________________ test_C11_validation_result_keys ________________________\ntests/test_hA.py:589: in test_C11_validation_result_keys\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:557: in _parse_bin_line\n    assert all((mass, slope, slope_err, expected, excluded, status)), line\nE   AssertionError:   bin 0: log M = [8.0, 8.5), slope = 1.0000 +/- 0.0966, expected = 1.0, n_excluded = 0 -> True\nE   assert False\nE    +  where False = all((<re.Match object; span=(17, 27), match='[8.0, 8.5)'>, <re.Match object; span=(29, 43), match='slope = 1.0000'>, <re.Match object; span=(44, 54), match='+/- 0.0966'>, <re.Match object; span=(56, 70), match='expected = 1.0'>, <re.Match object; span=(72, 86), match='n_excluded = 0'>, None))\n_________________________ test_E07_end_to_end_science __________________________\ntests/test_hB.py:294: in test_E07_end_to_end_science\n    assert d[\"consistent\"] is True, d\nE   AssertionError: {'mass_bin': 0, 'slope': np.float64(0.926776233510532), 'slope_err': np.float64(0.13946676597215996), 'intercept': np.float64(-6.319665846646199), ...}\nE   assert np.True_ is True\n_______________ test_E09_expected_slope_tracks_nondefault_alpha ________________\ntests/test_hB.py:322: in test_E09_expected_slope_tracks_nondefault_alpha\n    assert d[\"consistent\"] is True, d\nE   AssertionError: {'mass_bin': 0, 'slope': np.float64(0.6267762335105316), 'slope_err': np.float64(0.13946676597215998), 'intercept': np.float64(-6.3196658466462), ...}\nE   assert np.True_ is True\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_B15_rejection_messages_name_the_reason - Assert...\nFAILED tests/test_hA.py::test_C11_validation_result_keys - AssertionError:   ...\nFAILED tests/test_hB.py::test_E07_end_to_end_science - AssertionError: {'mass...\nFAILED tests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha - As...\n========================= 4 failed, 57 passed in 1.88s =========================\n",
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
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_n_sigma_negative",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_n_sigma_non_finite",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_n_sigma_non_positive",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_expected",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_slope",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_slope_err",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_outside_n_sigma",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_slope_err_negative",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_slope_err_zero",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_within_n_sigma",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_within_range",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_basic_values",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_box_size_mpc_bool_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_box_size_mpc_nan_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_box_size_mpc_ndarray_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_box_size_mpc_negative_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_box_size_mpc_nonpositive_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_box_size_mpc_string_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_docstring_convention",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_merger_fraction_above_one_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_merger_fraction_bool_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_merger_fraction_nan_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_merger_fraction_ndarray_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_merger_fraction_negative_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_merger_fraction_string_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_merger_fraction_zero_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_mismatched_arrays_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_negative_f_pair_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_negative_n_galaxies_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_negative_sigma_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_non_1d_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_non_finite_f_pair_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_non_integer_n_galaxies_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reduced_identity",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_timescale_gyr_nan_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_timescale_gyr_nonpositive_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_timescale_gyr_string_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_nonzero_f_pair_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_nonzero_sigma_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_zero_f_pair_valid",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_sigma_yields_zero_sigma_rate",
      "tests/test_merger_rate.py::TestComputePairFraction::test_basic_values",
      "tests/test_merger_rate.py::TestComputePairFraction::test_docstring_convention",
      "tests/test_merger_rate.py::TestComputePairFraction::test_integer_dtype_accepted",
      "tests/test_merger_rate.py::TestComputePairFraction::test_integer_valued_float_accepted",
      "tests/test_merger_rate.py::TestComputePairFraction::test_mismatched_shapes_rejected",
      "tests/test_merger_rate.py::TestComputePairFraction::test_negative_galaxies_rejected",
      "tests/test_merger_rate.py::TestComputePairFraction::test_negative_rejected",
      "tests/test_merger_rate.py::TestComputePairFraction::test_non_1d_rejected",
      "tests/test_merger_rate.py::TestComputePairFraction::test_non_finite_galaxies_rejected",
      "tests/test_merger_rate.py::TestComputePairFraction::test_non_finite_rejected",
      "tests/test_merger_rate.py::TestComputePairFraction::test_non_integer_galaxies_rejected",
      "tests/test_merger_rate.py::TestComputePairFraction::test_non_integer_rejected",
      "tests/test_merger_rate.py::TestComputePairFraction::test_pair_without_galaxy_rejected",
      "tests/test_merger_rate.py::TestComputePairFraction::test_zero_pairs_nonzero_galaxies",
      "tests/test_merger_rate.py::TestComputePairFraction::test_zero_pairs_zero_galaxies",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_all_above_range",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_all_below_range",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_all_in_range",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_empty_input",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_exact_bin_edges",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_mass_bin_edges_match",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_returns_int_array",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_all_excluded_returns_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_exact_power_law",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_exactly_two_usable_points_finite",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fewer_than_two_usable_returns_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_hand_computed_slope_err",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_malformed_redshift_inf",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_malformed_redshift_leq_neg1",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_malformed_redshift_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_n_excluded_correct_mixed",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_non_1d_rejected",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_non_finite_rate_err_excluded",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_non_finite_rate_excluded",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_provably_weighted",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_shape_mismatch_rejected",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_single_redshift_returns_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_zero_rate_err_excluded",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_box_size_mpc_array_rejected",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_box_size_mpc_bool_rejected",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_box_size_mpc_complex_rejected",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_box_size_mpc_nan_rejected",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_box_size_mpc_nonpositive_rejected",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_box_size_mpc_numpy_int_accepted",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_box_size_mpc_numpy_scalar_accepted",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_box_size_mpc_string_rejected",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_loads_known_values",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_mass_bin_above_max_rejected",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_mass_bin_below_neg1_rejected",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_missing_box_size_attr_rejected",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_missing_dataset_rejected",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_missing_file_rejected",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_wrong_length_n_galaxies_rejected",
      "tests/test_merger_rate.py::TestMergerTimescale::test_alpha_nan_rejected",
      "tests/test_merger_rate.py::TestMergerTimescale::test_alpha_string_rejected",
      "tests/test_merger_rate.py::TestMergerTimescale::test_non_default_values",
      "tests/test_merger_rate.py::TestMergerTimescale::test_t0_nan_rejected",
      "tests/test_merger_rate.py::TestMergerTimescale::test_t0_negative_rejected",
      "tests/test_merger_rate.py::TestMergerTimescale::test_t0_nonpositive_rejected",
      "tests/test_merger_rate.py::TestMergerTimescale::test_t0_string_rejected",
      "tests/test_merger_rate.py::TestMergerTimescale::test_z0_equals_t0",
      "tests/test_merger_rate.py::TestMergerTimescale::test_z_0d_array_rejected",
      "tests/test_merger_rate.py::TestMergerTimescale::test_z_bool_rejected",
      "tests/test_merger_rate.py::TestMergerTimescale::test_z_inf_rejected",
      "tests/test_merger_rate.py::TestMergerTimescale::test_z_leq_neg1_rejected",
      "tests/test_merger_rate.py::TestMergerTimescale::test_z_nan_rejected",
      "tests/test_merger_rate.py::TestMergerTimescale::test_z_ndarray_rejected",
      "tests/test_merger_rate.py::TestMergerTimescale::test_z_neg2_rejected",
      "tests/test_merger_rate.py::TestMergerTimescale::test_z_numpy_int_accepted",
      "tests/test_merger_rate.py::TestMergerTimescale::test_z_numpy_scalar_accepted",
      "tests/test_merger_rate.py::TestMergerTimescale::test_z_string_rejected",
      "tests/test_merger_rate.py::TestPart1ConfigUnchanged::test_existing_keys_unchanged",
      "tests/test_merger_rate.py::TestPart1ConfigUnchanged::test_new_key_defaults",
      "tests/test_merger_rate.py::TestPart1ConfigUnchanged::test_new_keys_present",
      "tests/test_merger_rate.py::TestPart1Integration::test_box_size_from_catalog_not_config",
      "tests/test_merger_rate.py::TestPart1Integration::test_denominator_from_full_catalog",
      "tests/test_merger_rate.py::TestPart1Integration::test_existing_attrs_unchanged",
      "tests/test_merger_rate.py::TestPart1Integration::test_new_dataset_and_attr_present",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_mass_bin_by_not_primary_rejected",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_output_schema",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_per_file_box_size_used",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_malformed_redshift_attr_untouched",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_mismatched_redshift_untouched",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_missing_file_untouched",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_rates_finite_and_nonneg",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_end_to_end_on_mock_data",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_expected_slope_tracks_non_default_alpha",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_fails_on_malformed_stored_redshift",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_fails_on_redshift_leq_neg1",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_heading_states_recovery_not_real",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_insufficient_data_printed",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_n_excluded_reported",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_returns_list_of_dicts",
      "tests/test_pair_finder.py::TestBasicPairRecovery::test_empty_catalog_returns_empty",
      "tests/test_pair_finder.py::TestBasicPairRecovery::test_no_double_counting",
      "tests/test_pair_finder.py::TestBasicPairRecovery::test_pair_at_max_sep_boundary",
      "tests/test_pair_finder.py::TestBasicPairRecovery::test_pair_beyond_max_sep_not_found",
      "tests/test_pair_finder.py::TestBasicPairRecovery::test_single_pair_found",
      "tests/test_pair_finder.py::TestBasicPairRecovery::test_single_pair_separation",
      "tests/test_pair_finder.py::TestMassAssignment::test_invalid_mass_bin_by_raises",
      "tests/test_pair_finder.py::TestMassAssignment::test_mass_bin_assignment",
      "tests
```
