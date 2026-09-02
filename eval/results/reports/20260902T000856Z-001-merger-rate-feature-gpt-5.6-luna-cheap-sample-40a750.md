# Trial report: 20260902T000856Z-001-merger-rate-feature-gpt-5.6-luna-cheap-sample-40a750

- Task: `001-merger-rate-feature`
- Model: `gpt-5.6-luna` (harness: codex)
- Duration: 274.3s | timed out: False | committed: False
- Changed files: TASK.md, src/calc.py, src/config.py, src/merger_rate.py

## Total score: 62.7 / 100
(scored 100% of rubric weight -- unscored categories, typically the judged ones with no judge model configured, are excluded rather than defaulted)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 93% |
| test_adequacy | automated | 25 | 0% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 77% |
| readability | judged | 8 | 60% |
| maintainability | judged | 7 | 40% |

## Detail

```json
{
  "correctness": {
    "total": 61,
    "passed": 57,
    "failed": [
      "tests/test_hA.py::test_C11_validation_result_keys",
      "tests/test_hB.py::test_E05_preflight_atomicity_sha256",
      "tests/test_hB.py::test_E07_end_to_end_science",
      "tests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha"
    ],
    "timed_out": false,
    "raw_tail": "   [ 68%]\ntests/test_hA.py::test_C05_fewer_than_two_usable PASSED                  [ 70%]\ntests/test_hA.py::test_C06_single_redshift_returns_nan PASSED            [ 72%]\ntests/test_hA.py::test_C07_malformed_redshifts_and_rank PASSED           [ 73%]\ntests/test_hA.py::test_C08_check_slope_consistency PASSED                [ 75%]\ntests/test_hA.py::test_C09_collapsed_predictor PASSED                    [ 77%]\ntests/test_hA.py::test_C10_y_centring_numerical_stability PASSED         [ 78%]\ntests/test_hA.py::test_C11_validation_result_keys FAILED                 [ 80%]\ntests/test_hA.py::test_C12_validation_rejects_malformed_stored_redshift_before_fit PASSED [ 81%]\ntests/test_hA.py::test_C13_validation_prints_insufficient_data PASSED    [ 83%]\ntests/test_hA.py::test_C14_mass_bin_is_index_not_string PASSED           [ 85%]\ntests/test_hA.py::test_C15_consistent_is_python_bool_or_none PASSED      [ 86%]\ntests/test_hB.py::test_E01_slice1_additive_schema PASSED                 [ 88%]\ntests/test_hB.py::test_E02_denominator_from_full_catalog PASSED          [ 90%]\ntests/test_hB.py::test_E03_box_size_from_catalog_not_config PASSED       [ 91%]\ntests/test_hB.py::test_E04_per_file_box_size_used PASSED                 [ 93%]\ntests/test_hB.py::test_E05_preflight_atomicity_sha256 FAILED             [ 95%]\ntests/test_hB.py::test_E06_output_schema PASSED                          [ 96%]\ntests/test_hB.py::test_E07_end_to_end_science FAILED                     [ 98%]\ntests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha FAILED [100%]\n\n=================================== FAILURES ===================================\n_______________________ test_C11_validation_result_keys ________________________\ntests/test_hA.py:589: in test_C11_validation_result_keys\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:557: in _parse_bin_line\n    assert all((mass, slope, slope_err, expected, excluded, status)), line\nE   AssertionError: bin 0 [8.0, 8.5): slope=1.0 +/- 0.09660176804140658, expected=1.0, n_excluded=0, True\nE   assert False\nE    +  where False = all((<re.Match object; span=(6, 16), match='[8.0, 8.5)'>, <re.Match object; span=(18, 27), match='slope=1.0'>, <re.Match object; span=(28, 51), match='+/- 0.09660176804140658'>, <re.Match object; span=(53, 65), match='expected=1.0'>, <re.Match object; span=(67, 79), match='n_excluded=0'>, None))\n_____________________ test_E05_preflight_atomicity_sha256 ______________________\ntests/test_hB.py:230: in test_E05_preflight_atomicity_sha256\n    assert not failures, failures\nE   AssertionError: [('z_missing', 'exception', 'KeyError')]\nE   assert not [('z_missing', 'exception', 'KeyError')]\n_________________________ test_E07_end_to_end_science __________________________\ntests/test_hB.py:294: in test_E07_end_to_end_science\n    assert d[\"consistent\"] is True, d\nE   AssertionError: {'mass_bin': 0, 'slope': np.float64(0.9267762335105318), 'slope_err': np.float64(0.13946676597215996), 'intercept': np.float64(-6.319665846646199), ...}\nE   assert np.True_ is True\n_______________ test_E09_expected_slope_tracks_nondefault_alpha ________________\ntests/test_hB.py:322: in test_E09_expected_slope_tracks_nondefault_alpha\n    assert d[\"consistent\"] is True, d\nE   AssertionError: {'mass_bin': 0, 'slope': np.float64(0.6267762335105316), 'slope_err': np.float64(0.13946676597215998), 'intercept': np.float64(-6.319665846646201), ...}\nE   assert np.True_ is True\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_C11_validation_result_keys - AssertionError: bi...\nFAILED tests/test_hB.py::test_E05_preflight_atomicity_sha256 - AssertionError...\nFAILED tests/test_hB.py::test_E07_end_to_end_science - AssertionError: {'mass...\nFAILED tests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha - As...\n========================= 4 failed, 57 passed in 3.17s =========================\n",
    "stderr_tail": ""
  },
  "own_suite_baseline": {
    "returncode": 0,
    "timed_out": false,
    "passed_clean": true,
    "tail": "........................................................................ [ 90%]\n........                                                                 [100%]\n80 passed in 2.99s\n"
  },
  "ships_red_outside_root": {
    "ships_red_outside_root": false,
    "returncode": 0,
    "timed_out": false,
    "tail": "........................................................................ [ 90%]\n........                                                                 [100%]\n80 passed in 2.33s\n"
  },
  "test_adequacy": {
    "per_mutation": {
      "M1_sigma_no_sqrt": "survive",
      "M2_timescale_sign": "survive",
      "M3_box_squared": "survive",
      "M4_config_box": "survive",
      "M5_slope_err_x2": "survive",
      "M6_consistency_bad_err": "survive",
      "M7_fabricate_fit": "survive",
      "M8a_pairfrac_shape_validation": "survive",
      "M8b_pairfrac_count_value_validation": "survive",
      "M8c_pairfrac_zero_denominator_validation": "survive",
      "M9a_timescale_z_form_validation": "survive",
      "M9b_timescale_z_value_validation": "survive",
      "M9c_timescale_config_form_validation": "survive",
      "M9d_timescale_config_value_validation": "survive",
      "M10a_rate_array_shape_validation": "survive",
      "M10b_rate_array_value_validation": "survive",
      "M10c_rate_scalar_form_validation": "survive",
      "M10d_rate_scalar_value_validation": "survive",
      "M10e_rate_zero_galaxy_validation": "survive",
      "M11_fit_no_weights": "survive",
      "M12_count_includes_upper_edge": "survive",
      "M13_write_before_preflight": "survive",
      "M14_sentinel_counted": "survive",
      "M17_hardcode_alpha": "survive",
      "M18_hardcode_expected_slope": "survive",
      "M20_n_excluded_zero": "survive",
      "M21_count_float_dtype": "survive",
      "M23_zero_zero_nan": "survive",
      "M24_count_from_pair_rows": "survive",
      "M25_reverse_persisted_mass_bins": "survive",
      "M26_corrupt_output_provenance": "survive",
      "M27_drop_validation_redshift_preflight": "survive",
      "M28_omit_console_fields": "survive",
      "M29_uncentred_y_cross_term": "survive"
    },
    "killed": 0,
    "total": 34
  },
  "scope_discipline": {
    "changed_files": [
      "src/calc.py",
      "src/config.py",
      "src/merger_rate.py"
    ],
    "out_of_scope": [],
    "frozen_touched": []
  },
  "hygiene": {
    "findings_count": 3,
    "findings": [
      "src/config.py:6:10: C408 Unnecessary `dict()` call (rewrite as a literal)",
      "Found 1 error.",
      "No fixes available (1 hidden fix can be enabled with the `--unsafe-fixes` option)."
    ]
  },
  "judge": {
    "raw": "{\"readability\": 3, \"maintainability\": 2, \"notes\": \"readability: Function and variable names are generally clear (merger_timescale_gyr, compute_pair_fraction), and the two docstrings correctly flag the plug-in Poisson convention, but dense one-line assert chains (e.g. merger_rate.py:63-70, 79-85) and inline if/else on one line (line 87) hurt legibility, and console output in run_merger_rate_validation (lines 168-172) crams many values into an unstructured print with no alignment. maintainability: `_mass_bin_edges` and `_results_path` are copy-pasted verbatim between calc.py and merger_rate.py instead of sharing a module, and the numeric-scalar validation pattern (`assert not isinstance(value, (bool, np.bool_)) and isinstance(...)`) is repeated three times (lines 17, 111, 132-ish) rather than factored into `_scalar`'s existing helper being reused consistently.\"}\n",
    "parsed": {
      "readability": 3,
      "maintainability": 2,
      "notes": "readability: Function and variable names are generally clear (merger_timescale_gyr, compute_pair_fraction), and the two docstrings correctly flag the plug-in Poisson convention, but dense one-line assert chains (e.g. merger_rate.py:63-70, 79-85) and inline if/else on one line (line 87) hurt legibility, and console output in run_merger_rate_validation (lines 168-172) crams many values into an unstructured print with no alignment. maintainability: `_mass_bin_edges` and `_results_path` are copy-pasted verbatim between calc.py and merger_rate.py instead of sharing a module, and the numeric-scalar validation pattern (`assert not isinstance(value, (bool, np.bool_)) and isinstance(...)`) is repeated three times (lines 17, 111, 132-ish) rather than factored into `_scalar`'s existing helper being reused consistently."
    },
    "timed_out": false
  }
}
```
