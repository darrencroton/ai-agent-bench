# Trial report: 20260903T023324Z-002-pair-binning-convention-gpt-5.6-luna-weak-tier-r2-lowfx-1-74e186

- Task: `002-pair-binning-convention`
- Model: `gpt-5.6-luna` (harness: codex)
- Duration: 167.6s | timed out: False | committed: False
- Changed files: src/config.py, src/pair_binning.py

## Total score: 64.5 / 100
(scored 100% of rubric weight -- unscored categories, typically the judged ones with no judge model configured, are excluded rather than defaulted)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 99% |
| test_adequacy | automated | 25 | 0% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 91% |
| readability | judged | 8 | 40% |
| maintainability | judged | 7 | 40% |

## Detail

```json
{
  "correctness": {
    "total": 140,
    "passed": 138,
    "failed": [
      "tests/test_hA.py::test_A25_check_additivity_rejections[a17-a27-a37-keywords7]",
      "tests/test_hA.py::test_A30_check_additivity_exact_above_2_53"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "ad_snapshot_counts_missing_dataset[mass_secondary] PASSED [ 80%]\ntests/test_hB.py::test_B12c_load_snapshot_counts_length_mismatch PASSED  [ 81%]\ntests/test_hB.py::test_B13_output_schema_on_mock PASSED                  [ 82%]\ntests/test_hB.py::test_B14_returned_dicts_match_persisted PASSED         [ 82%]\ntests/test_hB.py::test_B15_one_denominator_shared_by_every_convention PASSED [ 83%]\ntests/test_hB.py::test_B16_end_to_end_counts_recomputed_independently PASSED [ 84%]\ntests/test_hB.py::test_B17_conventions_config_tracks_through_the_driver PASSED [ 85%]\ntests/test_hB.py::test_B18_single_redshift_run PASSED                    [ 85%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[missing_data-<lambda>-None] PASSED [ 86%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[missing_results-<lambda>-None] PASSED [ 87%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_redshift-None-override2] PASSED [ 87%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_mass_ratio_min-None-override3] PASSED [ 88%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_max_sep-None-override4] PASSED [ 89%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[malformed_redshift-None-override5] PASSED [ 90%]\ntests/test_hB.py::test_B19b_preflight_checks_every_configured_redshift_before_writing PASSED [ 90%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad0] PASSED [ 91%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad1] PASSED [ 92%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad2] PASSED [ 92%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad3] PASSED [ 93%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad4] PASSED [ 94%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[primary] PASSED [ 95%]\ntests/test_hB.py::test_B21_console_summary_fields PASSED                 [ 95%]\ntests/test_hB.py::test_B21b_console_line_selection_is_token_exact_not_substring PASSED [ 96%]\ntests/test_hB.py::test_B22_console_reports_not_checked_for_partial_convention_set PASSED [ 97%]\ntests/test_hB.py::test_B23_provenance_compared_against_config_not_defaults PASSED [ 97%]\ntests/test_hB.py::test_B24_additivity_false_from_check_propagates_everywhere PASSED [ 98%]\ntests/test_hB.py::test_B26_full_driver_run_on_nondefault_bin_grid PASSED [ 99%]\ntests/test_hB.py::test_B27_low_mass_ratio_pair_not_refiltered PASSED     [100%]\n\n=================================== FAILURES ===================================\n_________ test_A25_check_additivity_rejections[a17-a27-a37-keywords7] __________\ntests/test_hA.py:364: in test_A25_check_additivity_rejections\n    assert (\"n_primary\" in low or \"n_secondary\" in low or \"n_either\" in low\nE   AssertionError: additivity counts must be real numeric\nE   assert ('n_primary' in 'additivity counts must be real numeric' or 'n_secondary' in 'additivity counts must be real numeric' or 'n_either' in 'additivity counts must be real numeric' or False)\nE    +  where False = any(<generator object test_A25_check_additivity_rejections.<locals>.<genexpr> at 0x10dd1e960>)\n__________________ test_A30_check_additivity_exact_above_2_53 __________________\ntests/test_hA.py:476: in test_A30_check_additivity_exact_above_2_53\n    assert PB.check_additivity(big, one, big) is False\nE   assert True is False\nE    +  where True = <function check_additivity at 0x10bd35e80>(array([9007199254740992]), array([1]), array([9007199254740992]))\nE    +    where <function check_additivity at 0x10bd35e80> = PB.check_additivity\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A25_check_additivity_rejections[a17-a27-a37-keywords7]\nFAILED tests/test_hA.py::test_A30_check_additivity_exact_above_2_53 - assert ...\n======================== 2 failed, 138 passed in 1.95s =========================\n",
    "stderr_tail": ""
  },
  "own_suite_baseline": {
    "returncode": 0,
    "timed_out": false,
    "passed_clean": true,
    "tail": "........................................................................ [ 90%]\n........                                                                 [100%]\n80 passed in 1.87s\n"
  },
  "ships_red_outside_root": {
    "ships_red_outside_root": false,
    "returncode": 0,
    "timed_out": false,
    "tail": "........................................................................ [ 90%]\n........                                                                 [100%]\n80 passed in 1.86s\n"
  },
  "test_adequacy": {
    "per_mutation": {
      "M01_either_counts_once": "survive",
      "M02_either_is_primary": "survive",
      "M03_secondary_is_primary": "survive",
      "M04_denominator_from_pair_rows": "survive",
      "M05_count_gal_includes_upper_edge": "survive",
      "M06_count_gal_float_dtype": "survive",
      "M07_count_pairs_float_dtype": "survive",
      "M08_sigma_no_sqrt": "survive",
      "M09_zero_zero_nan": "survive",
      "M10_pairfrac_shape_validation": "survive",
      "M11_pairfrac_value_validation": "survive",
      "M12_pairfrac_zero_denominator_validation": "survive",
      "M13_convention_validation": "survive",
      "M14_mass_order_validation": "survive",
      "M15_pair_shape_validation": "survive",
      "M16_nonfinite_mass_validation": "survive",
      "M17_excluded_zero": "survive",
      "M18_excluded_either_is_primary": "survive",
      "M19_additivity_always_true": "survive",
      "M20_additivity_validation": "survive",
      "M21_write_before_preflight": "survive",
      "M22_drop_validation_gate": "survive",
      "M23_use_stored_mass_bin": "survive",
      "M24_reverse_persisted_mass_bins": "survive",
      "M25_reverse_persisted_conventions": "survive",
      "M26_corrupt_output_provenance": "survive",
      "M27_additivity_attr_always_true": "survive",
      "M28_console_omits_fields": "survive",
      "M29_ignore_conventions_config": "survive",
      "M30_extra_result_key": "survive",
      "M31_bin_grid_ignores_config": "survive",
      "M32_additivity_forced_false": "survive",
      "M33_pairfrac_wrong_divisor": "survive",
      "M34_provenance_validation_disabled": "survive"
    },
    "killed": 0,
    "total": 34
  },
  "scope_discipline": {
    "changed_files": [
      "src/config.py",
      "src/pair_binning.py"
    ],
    "out_of_scope": [],
    "frozen_touched": []
  },
  "hygiene": {
    "findings_count": 1,
    "findings": [
      "src/config.py:6:10: C408 Unnecessary `dict()` call (rewrite as a literal)"
    ]
  },
  "judge": {
    "attempts": [
      {
        "attempt": 1,
        "returncode": 0,
        "raw": "{\"readability\": 2, \"maintainability\": 2, \"notes\": \"readability: run_binning_comparison and load_snapshot_counts pack many statements per line with semicolons (e.g. the rows.append(...) dict-literal line, the five chained f.create_dataset(...) calls on one line, and 'fractions = {}; errors = {}' followed by a semicolon-joined for-loop), producing very long, hard-to-scan lines rather than normal multi-statement Python; _validated_attr's assert lines are also dense enough to require re-reading. maintainability: some good factoring exists (_masses/_pair_inputs/_bin_indices/_validate_conventions are reused), but _masses and _counts are near-duplicate validators that could share a base, count_excluded_pairs recomputes _bin_indices(p,...) and _bin_indices(s,...) twice each instead of reusing count_pairs_per_mass_bin's logic, and the crammed one-liner blocks in run_binning_comparison bundle validation, aggregation, file I/O and printing into functions that are hard to modify safely.\"}\n",
        "stderr_tail": "",
        "parsed": {
          "readability": 2,
          "maintainability": 2,
          "notes": "readability: run_binning_comparison and load_snapshot_counts pack many statements per line with semicolons (e.g. the rows.append(...) dict-literal line, the five chained f.create_dataset(...) calls on one line, and 'fractions = {}; errors = {}' followed by a semicolon-joined for-loop), producing very long, hard-to-scan lines rather than normal multi-statement Python; _validated_attr's assert lines are also dense enough to require re-reading. maintainability: some good factoring exists (_masses/_pair_inputs/_bin_indices/_validate_conventions are reused), but _masses and _counts are near-duplicate validators that could share a base, count_excluded_pairs recomputes _bin_indices(p,...) and _bin_indices(s,...) twice each instead of reusing count_pairs_per_mass_bin's logic, and the crammed one-liner blocks in run_binning_comparison bundle validation, aggregation, file I/O and printing into functions that are hard to modify safely."
        },
        "timed_out": false
      }
    ]
  }
}
```
