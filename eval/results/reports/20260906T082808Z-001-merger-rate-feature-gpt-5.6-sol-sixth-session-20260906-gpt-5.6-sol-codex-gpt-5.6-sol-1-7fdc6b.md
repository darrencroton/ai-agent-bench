# Trial report: 20260906T082808Z-001-merger-rate-feature-gpt-5.6-sol-sixth-session-20260906-gpt-5.6-sol-codex-gpt-5.6-sol-1-7fdc6b

- Task: `001-merger-rate-feature`
- Model: `gpt-5.6-sol` (harness: codex)
- Model duration: 596.1s | venv setup: 29.9s | timed out: False | committed: False
- Changed files: src/calc.py, src/config.py, src/merger_rate.py, tests/test_merger_rate.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 94.7 / 100

## Judged: readability 75% of weight, maintainability 50% of weight (judge claude-opus-5, status ok)

## Composite score: 90.0 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 96% |
| test_adequacy | automated | 25 | 88% |
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
    "passed": 59,
    "failed": [
      "tests/test_hA.py::test_C11_validation_result_keys",
      "tests/test_hA.py::test_C13_validation_prints_insufficient_data"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "\ntests/test_hA.py::test_B07_zero_galaxies_rules PASSED                    [ 49%]\ntests/test_hA.py::test_B08_mass_bin_by_assertion PASSED                  [ 50%]\ntests/test_hA.py::test_B09_timescale_rejections PASSED                   [ 52%]\ntests/test_hA.py::test_B10_timescale_rejects_string_and_array PASSED     [ 54%]\ntests/test_hA.py::test_B11_merger_rate_scalar_rejections PASSED          [ 55%]\ntests/test_hA.py::test_B12_merger_rate_array_rejections PASSED           [ 57%]\ntests/test_hA.py::test_B13_merger_rate_rejects_string_box_by_assertion PASSED [ 59%]\ntests/test_hA.py::test_B14_docstring_wording PASSED                      [ 60%]\ntests/test_hA.py::test_B15_rejection_messages_name_the_reason PASSED     [ 62%]\ntests/test_hA.py::test_C01_exact_power_law PASSED                        [ 63%]\ntests/test_hA.py::test_C02_provably_weighted PASSED                      [ 65%]\ntests/test_hA.py::test_C03_two_point_slope_err_pinned PASSED             [ 67%]\ntests/test_hA.py::test_C04_two_usable_with_exclusions_finite PASSED      [ 68%]\ntests/test_hA.py::test_C05_fewer_than_two_usable PASSED                  [ 70%]\ntests/test_hA.py::test_C06_single_redshift_returns_nan PASSED            [ 72%]\ntests/test_hA.py::test_C07_malformed_redshifts_and_rank PASSED           [ 73%]\ntests/test_hA.py::test_C08_check_slope_consistency PASSED                [ 75%]\ntests/test_hA.py::test_C09_collapsed_predictor PASSED                    [ 77%]\ntests/test_hA.py::test_C10_y_centring_numerical_stability PASSED         [ 78%]\ntests/test_hA.py::test_C11_validation_result_keys FAILED                 [ 80%]\ntests/test_hA.py::test_C12_validation_rejects_malformed_stored_redshift_before_fit PASSED [ 81%]\ntests/test_hA.py::test_C13_validation_prints_insufficient_data FAILED    [ 83%]\ntests/test_hA.py::test_C14_mass_bin_is_index_not_string PASSED           [ 85%]\ntests/test_hA.py::test_C15_consistent_is_python_bool_or_none PASSED      [ 86%]\ntests/test_hB.py::test_E01_slice1_additive_schema PASSED                 [ 88%]\ntests/test_hB.py::test_E02_denominator_from_full_catalog PASSED          [ 90%]\ntests/test_hB.py::test_E03_box_size_from_catalog_not_config PASSED       [ 91%]\ntests/test_hB.py::test_E04_per_file_box_size_used PASSED                 [ 93%]\ntests/test_hB.py::test_E05_preflight_atomicity_sha256 PASSED             [ 95%]\ntests/test_hB.py::test_E06_output_schema PASSED                          [ 96%]\ntests/test_hB.py::test_E07_end_to_end_science PASSED                     [ 98%]\ntests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha PASSED [100%]\n\n=================================== FAILURES ===================================\n_______________________ test_C11_validation_result_keys ________________________\ntests/test_hA.py:589: in test_C11_validation_result_keys\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:544: in _parse_bin_line\n    assert len(lines) == 1, f\"expected one output line for bin {b}, got {lines!r}\"\nE   AssertionError: expected one output line for bin 0, got []\nE   assert 0 == 1\nE    +  where 0 = len([])\n_________________ test_C13_validation_prints_insufficient_data _________________\ntests/test_hA.py:640: in test_C13_validation_prints_insufficient_data\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:544: in _parse_bin_line\n    assert len(lines) == 1, f\"expected one output line for bin {b}, got {lines!r}\"\nE   AssertionError: expected one output line for bin 0, got []\nE   assert 0 == 1\nE    +  where 0 = len([])\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_C11_validation_result_keys - AssertionError: ex...\nFAILED tests/test_hA.py::test_C13_validation_prints_insufficient_data - Asser...\n========================= 2 failed, 59 passed in 1.78s =========================\n",
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
      "tests/test_merger_rate.py::test_calculation_requires_primary_before_preflight",
      "tests/test_merger_rate.py::test_calculation_uses_recorded_box_and_writes_schema",
      "tests/test_merger_rate.py::test_config_and_mass_bin_counting_contract",
      "tests/test_merger_rate.py::test_counting_does_not_require_mass_bin_strategy",
      "tests/test_merger_rate.py::test_fit_excludes_bad_data_and_handles_insufficient_points",
      "tests/test_merger_rate.py::test_fit_handles_repeated_and_collapsed_predictors_as_data_conditions",
      "tests/test_merger_rate.py::test_fit_is_weighted_for_heteroscedastic_data",
      "tests/test_merger_rate.py::test_fit_recovers_exact_power_law_and_two_point_error",
      "tests/test_merger_rate.py::test_fit_rejects_malformed_redshifts[redshifts0]",
      "tests/test_merger_rate.py::test_fit_rejects_malformed_redshifts[redshifts1]",
      "tests/test_merger_rate.py::test_fit_rejects_malformed_redshifts[redshifts2]",
      "tests/test_merger_rate.py::test_fit_rejects_shape_and_rank_violations[rates0-errors0-redshifts0]",
      "tests/test_merger_rate.py::test_fit_rejects_shape_and_rank_violations[rates1-errors1-redshifts1]",
      "tests/test_merger_rate.py::test_generated_pipeline_recovers_injected_timescale_model",
      "tests/test_merger_rate.py::test_generated_pipeline_schema_and_finite_rates",
      "tests/test_merger_rate.py::test_load_pair_counts_known_fixture_and_sentinel",
      "tests/test_merger_rate.py::test_load_pair_counts_rejects_bad_length_and_index",
      "tests/test_merger_rate.py::test_load_pair_counts_rejects_invalid_box_form_or_value[(1+0j)]",
      "tests/test_merger_rate.py::test_load_pair_counts_rejects_invalid_box_form_or_value[-1.0]",
      "tests/test_merger_rate.py::test_load_pair_counts_rejects_invalid_box_form_or_value[0.0]",
      "tests/test_merger_rate.py::test_load_pair_counts_rejects_invalid_box_form_or_value[500_0]",
      "tests/test_merger_rate.py::test_load_pair_counts_rejects_invalid_box_form_or_value[500_1]",
      "tests/test_merger_rate.py::test_load_pair_counts_rejects_invalid_box_form_or_value[True]",
      "tests/test_merger_rate.py::test_load_pair_counts_rejects_invalid_box_form_or_value[bad_box8]",
      "tests/test_merger_rate.py::test_load_pair_counts_rejects_invalid_box_form_or_value[inf]",
      "tests/test_merger_rate.py::test_load_pair_counts_rejects_invalid_box_form_or_value[nan]",
      "tests/test_merger_rate.py::test_load_pair_counts_rejects_missing_file",
      "tests/test_merger_rate.py::test_load_pair_counts_rejects_missing_schema[box_size]",
      "tests/test_merger_rate.py::test_load_pair_counts_rejects_missing_schema[mass_bin]",
      "tests/test_merger_rate.py::test_load_pair_counts_rejects_missing_schema[n_galaxies]",
      "tests/test_merger_rate.py::test_merger_rate_norm_identity_and_zero_error",
      "tests/test_merger_rate.py::test_merger_rate_rejects_bad_arrays[fractions0-errors0-galaxies0-shapes must match]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_bad_arrays[fractions1-errors1-galaxies1-must be 1D]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_bad_arrays[fractions2-errors2-galaxies2-non-negative]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_bad_arrays[fractions3-errors3-galaxies3-non-negative]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_bad_arrays[fractions4-errors4-galaxies4-finite]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_bad_arrays[fractions5-errors5-galaxies5-finite]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_bad_arrays[fractions6-errors6-galaxies6-non-negative]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_bad_arrays[fractions7-errors7-galaxies7-integer-valued]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_bad_arrays[fractions8-errors8-galaxies8-zero n_galaxies]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_bad_arrays[fractions9-errors9-galaxies9-zero n_galaxies]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_bad_scalar_values[-1.0-2.2-0.6-box_size_mpc]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_bad_scalar_values[0.0-2.2-0.6-box_size_mpc]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_bad_scalar_values[500.0--1.0-0.6-timescale_gyr]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_bad_scalar_values[500.0-0.0-0.6-timescale_gyr]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_bad_scalar_values[500.0-2.2-0.0-merger_fraction]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_bad_scalar_values[500.0-2.2-1.1-merger_fraction]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_bad_scalar_values[500.0-2.2-nan-merger_fraction]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_bad_scalar_values[500.0-inf-0.6-timescale_gyr]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_bad_scalar_values[500.0-nan-0.6-timescale_gyr]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_bad_scalar_values[inf-2.2-0.6-box_size_mpc]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_bad_scalar_values[nan-2.2-0.6-box_size_mpc]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_invalid_scalar_forms[(1+0j)-box_size_mpc]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_invalid_scalar_forms[(1+0j)-merger_fraction]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_invalid_scalar_forms[(1+0j)-timescale_gyr]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_invalid_scalar_forms[1_0-box_size_mpc]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_invalid_scalar_forms[1_0-merger_fraction]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_invalid_scalar_forms[1_0-timescale_gyr]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_invalid_scalar_forms[1_1-box_size_mpc]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_invalid_scalar_forms[1_1-merger_fraction]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_invalid_scalar_forms[1_1-timescale_gyr]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_invalid_scalar_forms[True-box_size_mpc]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_invalid_scalar_forms[True-merger_fraction]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_invalid_scalar_forms[True-timescale_gyr]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_invalid_scalar_forms[bad4-box_size_mpc]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_invalid_scalar_forms[bad4-merger_fraction]",
      "tests/test_merger_rate.py::test_merger_rate_rejects_invalid_scalar_forms[bad4-timescale_gyr]",
      "tests/test_merger_rate.py::test_merger_timescale_rejects_bad_alpha[-inf]",
      "tests/test_merger_rate.py::test_merger_timescale_rejects_bad_alpha[inf]",
      "tests/test_merger_rate.py::test_merger_timescale_rejects_bad_alpha[nan]",
      "tests/test_merger_rate.py::test_merger_timescale_rejects_bad_normalization[-1.0]",
      "tests/test_merger_rate.py::test_merger_timescale_rejects_bad_normalization[0.0]",
      "tests/test_merger_rate.py::test_merger_timescale_rejects_bad_normalization[inf]",
      "tests/test_merger_rate.py::test_merger_timescale_rejects_bad_normalization[nan]",
      "tests/test_merger_rate.py::test_merger_timescale_rejects_bad_redshift[-1.0]",
      "tests/test_merger_rate.py::test_merger_timescale_rejects_bad_redshift[-2.0]",
      "tests/test_merger_rate.py::test_merger_timescale_rejects_bad_redshift[-inf]",
      "tests/test_merger_rate.py::test_merger_timescale_rejects_bad_redshift[inf]",
      "tests/test_merger_rate.py::test_merger_timescale_rejects_bad_redshift[nan]",
      "tests/test_merger_rate.py::test_merger_timescale_rejects_invalid_scalar_forms[(1+0j)-merger_timescale_alpha]",
      "tests/test_merger_rate.py::test_merger_timescale_rejects_invalid_scalar_forms[(1+0j)-merger_timescale_gyr0]",
      "tests/test_merger_rate.py::test_merger_timescale_rejects_invalid_scalar_forms[(1+0j)-z]",
      "tests/test_merger_rate.py::test_merger_timescale_rejects_invalid_scalar_forms[1_0-merger_timescale_alpha]",
      "tests/test_merger_rate.py::test_merger_timescale_rejects_invalid_scalar_forms[1_0-merger_timescale_gyr0]",
      "tests/test_merger_rate.py::test_merger_timescale_rejects_invalid_scalar_forms[1_0-z]",
      "tests/test_merger_rate.py::test_merger_timescale_rejects_invalid_scalar_forms[1_1-merger_timescale_alpha]",
      "tests/test_merger_rate.py::test_merger_timescale_rejects_invalid_scalar_forms[1_1-merger_timescale_gyr0]",
      "tests/test_merger_rate.py::test_merger_timescale_rejects_invalid_scalar_forms[1_1-z]",
      "tests/test_merger_rate.py::test_merger_timescale_rejects_invalid_scalar_forms[True-merger_timescale_alpha]",
      "tests/test_merger_rate.py::test_merger_timescale_rejects_invalid_scalar_forms[True-merger_timescale_gyr0]",
      "tests/test_merger_rate.py::test_merger_timescale_rejects_invalid_scalar_forms[True-z]",
      "tests/test_merger_rate.py::test_merger_timescale_rejects_invalid_scalar_forms[bad4-merger_timescale_alpha]",
      "tests/test_merger_rate.py::test_merger_timescale_rejects_invalid_scalar_forms[bad4-merger_timescale_gyr0]",
      "tests/test_merger_rate.py::test_merger_timescale_rejects_invalid_scalar_forms[bad4-z]",
      "tests/test_merger_rate.py::test_merger_timescale_uses_configured_power_law",
      "tests/test_merger_rate.py::test_pair_fraction_accepts_integer_valued_float_counts",
      "tests/test_merger_rate.py::test_pair_fraction_rejects_malformed_counts[pairs0-galaxies0-shapes must match]",
      "tests/test_merger_rate.py::test_pair_fraction_rejects_malformed_counts[pairs1-galaxies1-must be 1D]",
      "tests/test_merger_rate.py::test_pair_fraction_rejects_malformed_counts[pairs2-galaxies2-non-negative]",
      "tests/test_merger_rate.py::test_pair_fraction_rejects_malformed_counts[pairs3-galaxies3-non-negative]",
      "tests/test_merger_rate.py::test_pair_fraction_rejects_malformed_counts[pairs4-galaxies4-finite]",
      "tests/test_merger_rate.py::test_pair_fraction_rejects_malformed_counts[pairs5-galaxies5-finite]",
      "tests/test_merger_rate.py::test_pair_fraction_rejects_malformed_counts[pairs6-galaxies6-integer-valued]",
      "tests/test_merger_rate.py::test_pair_fraction_rejects_malformed_counts[pairs7-galaxies7-integer-valued]",
      "tests/test_merger_rate.py::test_pair_fraction_rejects_malformed_counts[pairs8-galaxies8-n_pairs > 0]",
      "tests/test_merger_rate.py::test_pair_fraction_values_and_exact_zero_convention",
      "tests/test_merger_rate.py::test_preflight_failure_preserves_existing_output[malformed]",
      "tests/test_merger_rate.py::test_preflight_failure_preserves_existing_output[mismatch]",
      "tests/test_merger_rate.py::test_preflight_failure_preserves_existing_output[missing]",
      "tests/test_merger_rate.py::test_required_uncertainty_docstrings_are_exact",
      "tests/test_merger_rate.py::test_run_calculation_saves_full_catalog_counts_and_catalog_box",
      "tests/test_merger_rate.py::test_slope_consistency_contract",
      "tests/test_merger_rate.py::test_validation_output_results_and_nondefault_expectation",
      "tests/test_merger_rate.py::test_validation_rejects_malformed_stored_redshift_before_fit",
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
      "tests/test_pair_finder.py::TestSepBinAss
```
