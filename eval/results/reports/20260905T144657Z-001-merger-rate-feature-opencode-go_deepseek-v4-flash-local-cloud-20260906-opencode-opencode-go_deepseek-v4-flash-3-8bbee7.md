# Trial report: 20260905T144657Z-001-merger-rate-feature-opencode-go_deepseek-v4-flash-local-cloud-20260906-opencode-opencode-go_deepseek-v4-flash-3-8bbee7

- Task: `001-merger-rate-feature`
- Model: `opencode-go/deepseek-v4-flash` (harness: opencode)
- Model duration: 1186.4s | venv setup: 28.8s | timed out: False | committed: False
- Changed files: src/calc.py, src/config.py, src/merger_rate.py, tests/test_merger_rate.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 87.5 / 100

## Judged: readability 75% of weight, maintainability 50% of weight (judge claude-opus-5, status ok)

## Composite score: 83.9 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 96% |
| test_adequacy | automated | 25 | 70% |
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
| pair_fraction_core | 10 | 10 | 1.00 |
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
    "passed": 59,
    "failed": [
      "tests/test_hA.py::test_C11_validation_result_keys",
      "tests/test_hA.py::test_C13_validation_prints_insufficient_data"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "est_B11_merger_rate_scalar_rejections PASSED          [ 55%]\ntests/test_hA.py::test_B12_merger_rate_array_rejections PASSED           [ 57%]\ntests/test_hA.py::test_B13_merger_rate_rejects_string_box_by_assertion PASSED [ 59%]\ntests/test_hA.py::test_B14_docstring_wording PASSED                      [ 60%]\ntests/test_hA.py::test_B15_rejection_messages_name_the_reason PASSED     [ 62%]\ntests/test_hA.py::test_C01_exact_power_law PASSED                        [ 63%]\ntests/test_hA.py::test_C02_provably_weighted PASSED                      [ 65%]\ntests/test_hA.py::test_C03_two_point_slope_err_pinned PASSED             [ 67%]\ntests/test_hA.py::test_C04_two_usable_with_exclusions_finite PASSED      [ 68%]\ntests/test_hA.py::test_C05_fewer_than_two_usable PASSED                  [ 70%]\ntests/test_hA.py::test_C06_single_redshift_returns_nan PASSED            [ 72%]\ntests/test_hA.py::test_C07_malformed_redshifts_and_rank PASSED           [ 73%]\ntests/test_hA.py::test_C08_check_slope_consistency PASSED                [ 75%]\ntests/test_hA.py::test_C09_collapsed_predictor PASSED                    [ 77%]\ntests/test_hA.py::test_C10_y_centring_numerical_stability PASSED         [ 78%]\ntests/test_hA.py::test_C11_validation_result_keys FAILED                 [ 80%]\ntests/test_hA.py::test_C12_validation_rejects_malformed_stored_redshift_before_fit PASSED [ 81%]\ntests/test_hA.py::test_C13_validation_prints_insufficient_data FAILED    [ 83%]\ntests/test_hA.py::test_C14_mass_bin_is_index_not_string PASSED           [ 85%]\ntests/test_hA.py::test_C15_consistent_is_python_bool_or_none PASSED      [ 86%]\ntests/test_hB.py::test_E01_slice1_additive_schema PASSED                 [ 88%]\ntests/test_hB.py::test_E02_denominator_from_full_catalog PASSED          [ 90%]\ntests/test_hB.py::test_E03_box_size_from_catalog_not_config PASSED       [ 91%]\ntests/test_hB.py::test_E04_per_file_box_size_used PASSED                 [ 93%]\ntests/test_hB.py::test_E05_preflight_atomicity_sha256 PASSED             [ 95%]\ntests/test_hB.py::test_E06_output_schema PASSED                          [ 96%]\ntests/test_hB.py::test_E07_end_to_end_science PASSED                     [ 98%]\ntests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha PASSED [100%]\n\n=================================== FAILURES ===================================\n_______________________ test_C11_validation_result_keys ________________________\ntests/test_hA.py:589: in test_C11_validation_result_keys\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:557: in _parse_bin_line\n    assert all((mass, slope, slope_err, expected, excluded, status)), line\nE   AssertionError: bin 0 [8.0,8.5) | slope 1.0000 +/- 0.0966 | expected 1.0 | n_excluded 0 | pass\nE   assert False\nE    +  where False = all((<re.Match object; span=(6, 15), match='[8.0,8.5)'>, None, <re.Match object; span=(31, 41), match='+/- 0.0966'>, None, None, None))\n_________________ test_C13_validation_prints_insufficient_data _________________\ntests/test_hA.py:640: in test_C13_validation_prints_insufficient_data\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:557: in _parse_bin_line\n    assert all((mass, slope, slope_err, expected, excluded, status)), line\nE   AssertionError: bin 0 [8.0,8.5) | slope nan | slope_err nan | expected 1.0 | n_excluded 4 | insufficient data\nE   assert False\nE    +  where False = all((<re.Match object; span=(6, 15), match='[8.0,8.5)'>, None, None, None, None, <re.Match object; span=(76, 93), match='insufficient data'>))\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_C11_validation_result_keys - AssertionError: bi...\nFAILED tests/test_hA.py::test_C13_validation_prints_insufficient_data - Asser...\n========================= 2 failed, 59 passed in 2.01s =========================\n",
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
      "tests/test_merger_rate.py::TestCalcMassBinning::test_count_galaxies_per_mass_bin_default_edges",
      "tests/test_merger_rate.py::TestCalcMassBinning::test_exact_upper_edge_excluded",
      "tests/test_merger_rate.py::TestCalcMassBinning::test_interior_edge_assigned_to_upper_bin",
      "tests/test_merger_rate.py::TestCalcMassBinning::test_mass_bin_edges_agree_with_pair_finder",
      "tests/test_merger_rate.py::TestCalcWritesDenominator::test_box_size_mpc_from_catalog_not_config",
      "tests/test_merger_rate.py::TestCalcWritesDenominator::test_denominator_from_full_selected_catalog",
      "tests/test_merger_rate.py::TestCalcWritesDenominator::test_existing_datasets_unchanged",
      "tests/test_merger_rate.py::TestCalcWritesDenominator::test_new_dataset_and_attr_present",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_asserts_on_bad_n_sigma[-1.0]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_asserts_on_bad_n_sigma[-inf]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_asserts_on_bad_n_sigma[0.0]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_asserts_on_bad_n_sigma[inf]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_asserts_on_bad_n_sigma[nan]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_far_outside",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_for_bad_values[args0]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_for_bad_values[args1]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_for_bad_values[args2]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_for_bad_values[args3]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_for_bad_values[args4]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_for_bad_values[args5]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_true_within_range",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_docstring_has_poisson_sentence",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_example",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reduced_identity",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_arrays",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_scalars[kwargs0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_scalars[kwargs10]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_scalars[kwargs1]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_scalars[kwargs2]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_scalars[kwargs3]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_scalars[kwargs4]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_scalars[kwargs5]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_scalars[kwargs6]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_scalars[kwargs7]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_scalars[kwargs8]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_scalars[kwargs9]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form[kw0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form[kw10]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form[kw11]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form[kw12]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form[kw13]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form[kw14]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form[kw15]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form[kw16]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form[kw17]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form[kw1]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form[kw2]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form[kw3]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form[kw4]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form[kw5]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form[kw6]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form[kw7]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form[kw8]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form[kw9]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_with_nonzero_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_with_zero_quantities_valid",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_uncertainty_exact_zero",
      "tests/test_merger_rate.py::TestComputePairFraction::test_accepts_integer_dtype_and_float_int",
      "tests/test_merger_rate.py::TestComputePairFraction::test_docstring_has_poisson_sentence",
      "tests/test_merger_rate.py::TestComputePairFraction::test_empty_bin_exact_zero",
      "tests/test_merger_rate.py::TestComputePairFraction::test_example_values",
      "tests/test_merger_rate.py::TestComputePairFraction::test_n_pairs_positive_requires_n_galaxies_positive",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_invalid[bad0]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_invalid[bad1]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_invalid[bad2]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_invalid[bad3]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_invalid[bad4]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_invalid[bad5]",
      "tests/test_merger_rate.py::TestConfigKeys::test_keys_added",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_all_share_single_redshift",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_collapsed_predictor_distinct_z",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_exact_power_law",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fewer_than_two_usable",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_malformed_redshifts_assert[bad_z0]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_malformed_redshifts_assert[bad_z1]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_malformed_redshifts_assert[bad_z2]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_malformed_redshifts_assert[bad_z3]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_n_excluded_correct",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_shape_and_rank_violations_assert",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_slope_err_matches_hand_computed",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_weighted_is_better_than_unweighted",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_bad_box_size_mpc[-1.0]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_bad_box_size_mpc[0.0]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_bad_box_size_mpc[inf]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_bad_box_size_mpc[nan]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_hand_written_fixture",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_missing_dataset_or_attr",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_missing_file",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_index_outside_range",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_scalar_form[(250+1j)]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_scalar_form[500_0]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_scalar_form[500_1]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_scalar_form[True]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_scalar_form[bad_box4]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_scalar_form[bad_box5]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_wrong_length_n_galaxies",
      "tests/test_merger_rate.py::TestMergerTimescale::test_non_default_alpha",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_bad_alpha",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_bad_gyr0",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_bad_z[-1.0]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_bad_z[-2.0]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_bad_z[-inf]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_bad_z[inf]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_bad_z[nan]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_invalid_scalar_form[(2+1j)]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_invalid_scalar_form[2.0_0]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_invalid_scalar_form[2.0_1]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_invalid_scalar_form[True]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_invalid_scalar_form[bad4]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_invalid_scalar_form[bad5]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_zero",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_mass_bin_by_assertion",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_output_schema_and_shapes",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_leaves_sentinel_unchanged",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_uses_per_file_box_size",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_end_to_end_mock_data",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_expected_slope_tracks_non_default_alpha",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_insufficient_data_line_and_heading",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_insufficient_data_printed",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_malformed_stored_redshift_fails_before_fit",
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
      "tests/test_pair_finder.py::TestVelocityRecovery::t
```
