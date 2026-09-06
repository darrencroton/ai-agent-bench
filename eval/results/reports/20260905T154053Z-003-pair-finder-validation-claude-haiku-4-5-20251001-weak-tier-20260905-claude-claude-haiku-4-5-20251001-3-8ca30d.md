# Trial report: 20260905T154053Z-003-pair-finder-validation-claude-haiku-4-5-20251001-weak-tier-20260905-claude-claude-haiku-4-5-20251001-3-8ca30d

- Task: `003-pair-finder-validation`
- Model: `claude-haiku-4-5-20251001` (harness: claude)
- Model duration: 274.6s | venv setup: 27.0s | timed out: False | committed: False
- Changed files: src/pair_finder.py, tests/test_pair_finder_validation.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 90.7 / 100

## Judged: readability 75% of weight, maintainability 50% of weight (judge claude-opus-5, status ok)

## Composite score: 86.6 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 99% |
| test_adequacy | automated | 25 | 74% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 91% |
| readability | judged | 8 | 75% |
| maintainability | judged | 7 | 50% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| rejection_matrix | 192 | 205 | 0.94 |
| accepted_input_sweep | 64 | 64 | 1.00 |
| preserved_behaviour | 14 | 14 | 1.00 |
| integer_dtype_semantics | 22 | 22 | 1.00 |
| validation_ordering_precedes_early_returns | 3 | 3 | 1.00 |
| driver_integration_path | 7 | 7 | 1.00 |

## Provenance

```json
{
  "rubric_version": 2,
  "rubric_sha256": "a4a93e1f5fd3b17c7ad7f873dd74a65ff2c74da8a1f759c4ac5e3e8a1d7a9102",
  "rubric_profile": "default",
  "task_contract_sha256": "3a83f13cc1c56dc536783edc669feea2e7b4cbe325fa67ac7e221667d6a2c797",
  "evaluator_content_sha256": "4a0569ac508369aa56ea3017e4c390ade1fc5a8567517ed2ba91f9a044a0ca2e",
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
    "total": 315,
    "passed": 302,
    "failed": [
      "tests/test_hA.py::test_A100_rejects[catalog_short_x]",
      "tests/test_hA.py::test_A100_rejects[catalog_short_y]",
      "tests/test_hA.py::test_A100_rejects[catalog_short_z]",
      "tests/test_hA.py::test_A100_rejects[catalog_short_vx]",
      "tests/test_hA.py::test_A100_rejects[catalog_short_vy]",
      "tests/test_hA.py::test_A100_rejects[catalog_short_vz]",
      "tests/test_hA.py::test_A100_rejects[catalog_short_log_stellar_mass]",
      "tests/test_hA.py::test_A100_rejects[mass_bin_width_value_10.0]",
      "tests/test_hA.py::test_A100_rejects[sep_bins_str_elements]",
      "tests/test_hA.py::test_A100_rejects[sep_bins_complex_element]",
      "tests/test_hA.py::test_A100_rejects[sep_bins_nested_element]",
      "tests/test_hA.py::test_A100_rejects[sep_bins_bool_element]",
      "tests/test_hA.py::test_A100_rejects[order_width_positive_before_range]"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "e('float64') according to the rule 'safe'\n\nDuring handling of the above exception, another exception occurred:\ntests/test_hA.py:502: in test_A100_rejects\n    pytest.fail(\nE   Failed: expected AssertionError, got TypeError: Cannot cast array data from dtype('<U2') to dtype('float64') according to the rule 'safe' -- a low-level exception leaking from numpy/scipy is not a valid rejection\n_________________ test_A100_rejects[sep_bins_complex_element] __________________\ntests/test_hA.py:498: in test_A100_rejects\n    PF.find_pairs(catalog, config)\nsrc/pair_finder.py:249: in find_pairs\n    _validate_config(config)\nsrc/pair_finder.py:159: in _validate_config\n    sep_bins_arr = np.array(sep_bins, dtype=float)\n                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE   TypeError: float() argument must be a string or a real number, not 'complex'\n\nDuring handling of the above exception, another exception occurred:\ntests/test_hA.py:502: in test_A100_rejects\n    pytest.fail(\nE   Failed: expected AssertionError, got TypeError: float() argument must be a string or a real number, not 'complex' -- a low-level exception leaking from numpy/scipy is not a valid rejection\n__________________ test_A100_rejects[sep_bins_nested_element] __________________\ntests/test_hA.py:498: in test_A100_rejects\n    PF.find_pairs(catalog, config)\nsrc/pair_finder.py:249: in find_pairs\n    _validate_config(config)\nsrc/pair_finder.py:159: in _validate_config\n    sep_bins_arr = np.array(sep_bins, dtype=float)\n                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE   ValueError: setting an array element with a sequence. The requested array has an inhomogeneous shape after 1 dimensions. The detected shape was (2,) + inhomogeneous part.\n\nDuring handling of the above exception, another exception occurred:\ntests/test_hA.py:502: in test_A100_rejects\n    pytest.fail(\nE   Failed: expected AssertionError, got ValueError: setting an array element with a sequence. The requested array has an inhomogeneous shape after 1 dimensions. The detected shape was (2,) + inhomogeneous part. -- a low-level exception leaking from numpy/scipy is not a valid rejection\n___________________ test_A100_rejects[sep_bins_bool_element] ___________________\ntests/test_hA.py:508: in test_A100_rejects\n    pytest.fail(\"malformed input was accepted without any exception\")\nE   Failed: malformed input was accepted without any exception\n_____________ test_A100_rejects[order_width_positive_before_range] _____________\ntests/test_hA.py:510: in test_A100_rejects\n    assert token in message, (\nE   AssertionError: message does not contain the required reason token 'positive': \"config['log_mass_max'] (7.0) must be greater than log_mass_min (8.0)\"\nE   assert 'positive' in \"config['log_mass_max'] (7.0) must be greater than log_mass_min (8.0)\"\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A100_rejects[catalog_short_x] - AssertionError:...\nFAILED tests/test_hA.py::test_A100_rejects[catalog_short_y] - AssertionError:...\nFAILED tests/test_hA.py::test_A100_rejects[catalog_short_z] - AssertionError:...\nFAILED tests/test_hA.py::test_A100_rejects[catalog_short_vx] - AssertionError...\nFAILED tests/test_hA.py::test_A100_rejects[catalog_short_vy] - AssertionError...\nFAILED tests/test_hA.py::test_A100_rejects[catalog_short_vz] - AssertionError...\nFAILED tests/test_hA.py::test_A100_rejects[catalog_short_log_stellar_mass] - ...\nFAILED tests/test_hA.py::test_A100_rejects[mass_bin_width_value_10.0] - Asser...\nFAILED tests/test_hA.py::test_A100_rejects[sep_bins_str_elements] - Failed: e...\nFAILED tests/test_hA.py::test_A100_rejects[sep_bins_complex_element] - Failed...\nFAILED tests/test_hA.py::test_A100_rejects[sep_bins_nested_element] - Failed:...\nFAILED tests/test_hA.py::test_A100_rejects[sep_bins_bool_element] - Failed: m...\nFAILED tests/test_hA.py::test_A100_rejects[order_width_positive_before_range]\n======================== 13 failed, 302 passed in 0.95s ========================\n",
    "stderr_tail": "",
    "obligations": [
      {
        "id": "rejection_matrix",
        "passed": 192,
        "collected": 205,
        "fraction": 0.9365853658536586,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_A100_rejects[catalog_short_log_stellar_mass]",
          "tests/test_hA.py::test_A100_rejects[catalog_short_vx]",
          "tests/test_hA.py::test_A100_rejects[catalog_short_vy]",
          "tests/test_hA.py::test_A100_rejects[catalog_short_vz]",
          "tests/test_hA.py::test_A100_rejects[catalog_short_x]",
          "tests/test_hA.py::test_A100_rejects[catalog_short_y]",
          "tests/test_hA.py::test_A100_rejects[catalog_short_z]",
          "tests/test_hA.py::test_A100_rejects[mass_bin_width_value_10.0]",
          "tests/test_hA.py::test_A100_rejects[order_width_positive_before_range]",
          "tests/test_hA.py::test_A100_rejects[sep_bins_bool_element]",
          "tests/test_hA.py::test_A100_rejects[sep_bins_complex_element]",
          "tests/test_hA.py::test_A100_rejects[sep_bins_nested_element]",
          "tests/test_hA.py::test_A100_rejects[sep_bins_str_elements]"
        ]
      },
      {
        "id": "accepted_input_sweep",
        "passed": 64,
        "collected": 64,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "preserved_behaviour",
        "passed": 14,
        "collected": 14,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "integer_dtype_semantics",
        "passed": 22,
        "collected": 22,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "validation_ordering_precedes_early_returns",
        "passed": 3,
        "collected": 3,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "driver_integration_path",
        "passed": 7,
        "collected": 7,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
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
      "tests/test_pair_finder.py::TestVelocityRecovery::test_velocity_is_symmetric",
      "tests/test_pair_finder.py::TestVelocityRecovery::test_zero_relative_velocity",
      "tests/test_pair_finder_validation.py::TestBehaviourPreservation::test_empty_result_on_mass_ratio_cut",
      "tests/test_pair_finder_validation.py::TestBehaviourPreservation::test_empty_result_on_no_pairs",
      "tests/test_pair_finder_validation.py::TestBehaviourPreservation::test_float64_results_unchanged",
      "tests/test_pair_finder_validation.py::TestBehaviourPreservation::test_mass_bin_by_valueerror_still_raised",
      "tests/test_pair_finder_validation.py::TestBehaviourPreservation::test_mass_outside_config_range_allowed",
      "tests/test_pair_finder_validation.py::TestBehaviourPreservation::test_negative_mass_allowed",
      "tests/test_pair_finder_validation.py::TestBehaviourPreservation::test_out_of_range_mass_bin_sentinel",
      "tests/test_pair_finder_validation.py::TestBehaviourPreservation::test_out_of_range_sep_bin_sentinel",
      "tests/test_pair_finder_validation.py::TestCatalogArrayDtype::test_catalog_vx_object_dtype",
      "tests/test_pair_finder_validation.py::TestCatalogArrayDtype::test_catalog_x_bool_dtype",
      "tests/test_pair_finder_validation.py::TestCatalogArrayDtype::test_catalog_y_complex_dtype",
      "tests/test_pair_finder_validation.py::TestCatalogArrayDtype::test_catalog_z_string_dtype",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFieldTypes::test_catalog_x_is_list",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFieldTypes::test_catalog_y_is_tuple",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFieldTypes::test_catalog_z_is_list",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFiniteness::test_catalog_log_stellar_mass_nan",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFiniteness::test_catalog_x_nan",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFiniteness::test_catalog_y_inf",
      "tests/test_pair_finder_validation.py::TestCatalogArrayFiniteness::test_catalog_z_neginf",
      "tests/test_pair_finder_validation.py::TestCatalogArrayLength::test_catalog_vx_different_length",
      "tests/test_pair_finder_validation.py::TestCatalogArrayLength::test_catalog_x_different_length",
      "tests/test_pair_finder_validation.py::TestCatalogArrayShape::test_catalog_x_2d",
      "tests/test_pair_finder_validation.py::TestCatalogArrayShape::test_catalog_y_3d",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_box_size_inf",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_box_size_nan",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_box_size_negative",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_box_size_not_scalar_array",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_box_size_not_scalar_list",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_box_size_zero",
      "tests/test_pair_finder_validation.py::TestCatalogCoordinateRanges::test_position_above_box_size",
      "tests/test_pair_finder_validation.py::TestCatalogCoordinateRanges::test_position_at_box_size",
      "tests/test_pair_finder_validation.py::TestCatalogCoordinateRanges::test_position_below_zero",
      "tests/test_pair_finder_validation.py::TestCatalogCoordinateRanges::test_z_position_below_zero",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_catalog_missing_box_size",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_catalog_missing_log_stellar_mass",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_catalog_missing_vx",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_catalog_missing_vy",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_catalog_missing_vz",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_catalog_missing_x",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_catalog_missing_y",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_catalog_missing_z",
      "tests/test_pair_finder_validation.py::TestCatalogTopLevelForm::test_catalog_not_dict_list",
      "tests/test_pair_finder_validation.py::TestCatalogTopLevelForm::test_catalog_not_dict_none",
      "tests/test_pair_finder_validation.py::TestCatalogTopLevelForm::test_catalog_not_dict_string",
      "tests/test_pair_finder_validation.py::TestCatalogValidExtras::test_catalog_with_extra_keys",
      "tests/test_pair_finder_validation.py::TestCatalogValidExtras::test_catalog_with_malformed_extra_key",
      "tests/test_pair_finder_validation.py::TestCatalogValidInteger::test_catalog_signed_int32",
      "tests/test_pair_finder_validation.py::TestCatalogValidInteger::test_catalog_unsigned_uint32",
      "tests/test_pair_finder_validation.py::TestCatalogValidInteger::test_integer_produces_same_results_as_float",
      "tests/test_pair_finder_validation.py::TestCatalogValidZeroLength::test_zero_length_catalog",
      "tests/test_pair_finder_validation.py::TestConfigLogMassRange::test_log_mass_max_equals_min",
      "tests/test_pair_finder_validation.py::TestConfigLogMassRange::test_log_mass_max_less_than_min",
      "tests/test_pair_finder_validation.py::TestConfigLogMassRange::test_log_mass_max_nan",
      "tests/test_pair_finder_validation.py::TestConfigLogMassRange::test_log_mass_max_not_scalar",
      "tests/test_pair_finder_validation.py::TestConfigLogMassRange::test_log_mass_min_nan",
      "tests/test_pair_finder_validation.py::TestConfigLogMassRange::test_log_mass_min_not_scalar",
      "tests/test_pair_finder_validation.py::TestConfigMassBinBy::test_mass_bin_by_all_valid_strategies",
      "tests/test_pair_finder_validation.py::TestConfigMassBinBy::test_mass_bin_by_invalid_value_raises_valueerror",
      "tests/test_pair_finder_validation.py::TestConfigMassBinBy::test_mass_bin_by_missing",
      "tests/test_pair_finder_validation.py::TestConfigMassBinWidth::test_mass_bin_width_nan",
      "tests/test_pair_finder_validation.py::TestConfigMassBinWidth::test_mass_bin_width_negative",
      "tests/test_pair_finder_validation.py::TestConfigMassBinWidth::test_mass_bin_width_not_scalar",
      "tests/test_pair_finder_validation.py::TestConfigMassBinWidth::test_mass_bin_width_too_large",
      "tests/test_pair_finder_validation.py::TestConfigMassBinWidth::test_mass_bin_width_zero",
      "tests/test_pair_finder_validation.py::TestConfigMassRatioMin::test_mass_ratio_min_above_one",
      "tests/test_pair_finder_validation.py::TestConfigMassRatioMin::test_mass_ratio_min_below_zero",
      "tests/test_pair_finder_validation.py::TestConfigMassRatioMin::test_mass_ratio_min_exactly_one",
      "tests/test_pair_finder_validation.py::TestConfigMassRatioMin::test_mass_ratio_min_exactly_zero",
      "tests/test_pair_finder_validation.py::TestConfigMassRatioMin::test_mass_ratio_min_nan",
      "tests/test_pair_finder_validation.py::TestConfigMassRatioMin::test_mass_ratio_min_not_scalar",
      "tests/test_pair_finder_validation.py::TestConfigMaxSep::test_max_sep_inf",
      "tests/test_pair_finder_validation.py::TestConfigMaxSep::test_max_sep_nan",
      "tests/test_pair_finder_validation.py::TestConfigMaxSep::test_max_sep_negative",
      "tests/test_pair_finder_validation.py::TestConfigMaxSep::test_max_sep_not_scalar",
      "tests/test_pair_finder_validation.py::TestConfigMaxSep::test_max_sep_zero",
      "tests/test_pair_finder_validation.py::TestConfigMissingKeys::test_config_missing_log_mass_max",
      "tests/test_pair_finder_validation.py::TestConfigMissingKeys::test_config_missing_log_mass_min",
      "tests/test_pair_finder_validation.py::TestConfigMissingKeys::test_config_missing_mass_bin_by",
      "tests/test_pair_finder_validation.py::TestConfigMissingKeys::test_config_missing_mass_bin_width",
      "tests/test_pair_finder_validation.py::TestConfigMissingKeys::test_config_missing_mass_ratio_min",
      "tests/test_pair_finder_validation.py::TestConfigMissingKeys::test_config_missing_max_sep",
      "tests/test_pair_finder_validation.py::TestConfigMissingKeys::test_config_missing_sep_bins",
      "tests/test_pair_finder_validation.py::TestConfigSepBins::test_sep_bins_as_list",
      "tests/test_pair_finder_validation.py::TestConfigSepBins::test_sep_bins_as_ndarray_float",
      "tests/test_pair_finder_validation.py::TestConfigSepBins::test_sep_bins_as_ndarray_int",
      "tests/test_pair_finder_validation.py::TestConfigSepBins::test_sep_bins_as_tuple",
      "tests/test_pair_finder_validation.py::TestConfigSepBins::test_sep_bins_decreasing",
      "tests/test_pair_finder_validation.py::TestConfigSepBins::test_sep_bins_ndarray_2d",
      "tests/test_pair_finder_validation.py::TestConfigSepBins::test_sep_bins_ndarray_wrong_dtype",
      "tests/test_pair_finder_validation.py::TestConfigSepBins::test_sep_bins_not_list_tuple_ndarray",
      "tests/test_pair_finder_validation.py::TestConfigSepBins::test_sep_bins_not_strictly_increasing",
      "tests/test_pair_finder_validation.py::TestConfigSepBins::test_sep_bins_too_few_edges",
      "tests/test_pair_finder_validation.py::TestConfigSepBins::test_sep_bins_with_inf",
      "tests/test_pair_finder_validation.py::TestConfigSepBins::test_sep_bins_with_nan",
      "tests/test_pair_finder_validation.py::TestConfigTopLevelForm::test_config_not_dict_list",
      "tests/test_pair_finder_validation.py::TestConfigTopLevelForm::test_config_not_dict_string",
      "tests/test_pair_finder_validation.py::TestNonDefaultConfigs::test_fine_separation_bins",
      "tests/test_pair_finder_validation.py::TestNonDefaultConfigs::test_narrow_mass_range",
      "tests/test_pair_finder_validation.
```
