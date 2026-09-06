# Trial report: 20260906T120643Z-003-pair-finder-validation-opencode-go_mimo-v2.5-sixth-session-20260906-mimo-v2.5-opencode-opencode-go_mimo-v2.5-3-ade150

- Task: `003-pair-finder-validation`
- Model: `opencode-go/mimo-v2.5` (harness: opencode)
- Model duration: 535.1s | venv setup: 28.8s | timed out: False | committed: False
- Changed files: src/pair_finder.py, tests/test_pair_finder_validation.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 86.9 / 100

## Judged: readability 75% of weight, maintainability 25% of weight (judge claude-opus-5, status ok)

## Composite score: 81.6 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 99% |
| test_adequacy | automated | 25 | 75% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 56% |
| readability | judged | 8 | 75% |
| maintainability | judged | 7 | 25% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| rejection_matrix | 190 | 205 | 0.93 |
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
    "total": 315,
    "passed": 300,
    "failed": [
      "tests/test_hA.py::test_A100_rejects[box_size_form_str]",
      "tests/test_hA.py::test_A100_rejects[box_size_form_bytes]",
      "tests/test_hA.py::test_A100_rejects[box_size_form_complex]",
      "tests/test_hA.py::test_A100_rejects[mass_bin_width_value_10.0]",
      "tests/test_hA.py::test_A100_rejects[config_form_max_sep_str]",
      "tests/test_hA.py::test_A100_rejects[config_form_max_sep_complex]",
      "tests/test_hA.py::test_A100_rejects[config_form_mass_ratio_min_str]",
      "tests/test_hA.py::test_A100_rejects[config_form_mass_ratio_min_complex]",
      "tests/test_hA.py::test_A100_rejects[config_form_log_mass_min_str]",
      "tests/test_hA.py::test_A100_rejects[config_form_log_mass_min_complex]",
      "tests/test_hA.py::test_A100_rejects[config_form_log_mass_max_str]",
      "tests/test_hA.py::test_A100_rejects[config_form_log_mass_max_complex]",
      "tests/test_hA.py::test_A100_rejects[config_form_mass_bin_width_str]",
      "tests/test_hA.py::test_A100_rejects[config_form_mass_bin_width_complex]",
      "tests/test_hA.py::test_A100_rejects[config_form_max_sep_bytes]"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "d reason token 'scalar': \"config: 'mass_ratio_min' has invalid type complex\"\nE   assert 'scalar' in \"config: 'mass_ratio_min' has invalid type complex\"\n_______________ test_A100_rejects[config_form_log_mass_min_str] ________________\ntests/test_hA.py:510: in test_A100_rejects\n    assert token in message, (\nE   AssertionError: message does not contain the required reason token 'scalar': \"config: 'log_mass_min' has invalid type str\"\nE   assert 'scalar' in \"config: 'log_mass_min' has invalid type str\"\n_____________ test_A100_rejects[config_form_log_mass_min_complex] ______________\ntests/test_hA.py:510: in test_A100_rejects\n    assert token in message, (\nE   AssertionError: message does not contain the required reason token 'scalar': \"config: 'log_mass_min' has invalid type complex\"\nE   assert 'scalar' in \"config: 'log_mass_min' has invalid type complex\"\n_______________ test_A100_rejects[config_form_log_mass_max_str] ________________\ntests/test_hA.py:510: in test_A100_rejects\n    assert token in message, (\nE   AssertionError: message does not contain the required reason token 'scalar': \"config: 'log_mass_max' has invalid type str\"\nE   assert 'scalar' in \"config: 'log_mass_max' has invalid type str\"\n_____________ test_A100_rejects[config_form_log_mass_max_complex] ______________\ntests/test_hA.py:510: in test_A100_rejects\n    assert token in message, (\nE   AssertionError: message does not contain the required reason token 'scalar': \"config: 'log_mass_max' has invalid type complex\"\nE   assert 'scalar' in \"config: 'log_mass_max' has invalid type complex\"\n______________ test_A100_rejects[config_form_mass_bin_width_str] _______________\ntests/test_hA.py:510: in test_A100_rejects\n    assert token in message, (\nE   AssertionError: message does not contain the required reason token 'scalar': \"config: 'mass_bin_width' has invalid type str\"\nE   assert 'scalar' in \"config: 'mass_bin_width' has invalid type str\"\n____________ test_A100_rejects[config_form_mass_bin_width_complex] _____________\ntests/test_hA.py:510: in test_A100_rejects\n    assert token in message, (\nE   AssertionError: message does not contain the required reason token 'scalar': \"config: 'mass_bin_width' has invalid type complex\"\nE   assert 'scalar' in \"config: 'mass_bin_width' has invalid type complex\"\n_________________ test_A100_rejects[config_form_max_sep_bytes] _________________\ntests/test_hA.py:510: in test_A100_rejects\n    assert token in message, (\nE   AssertionError: message does not contain the required reason token 'scalar': \"config: 'max_sep' has invalid type bytes\"\nE   assert 'scalar' in \"config: 'max_sep' has invalid type bytes\"\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A100_rejects[box_size_form_str] - AssertionErro...\nFAILED tests/test_hA.py::test_A100_rejects[box_size_form_bytes] - AssertionEr...\nFAILED tests/test_hA.py::test_A100_rejects[box_size_form_complex] - Assertion...\nFAILED tests/test_hA.py::test_A100_rejects[mass_bin_width_value_10.0] - Asser...\nFAILED tests/test_hA.py::test_A100_rejects[config_form_max_sep_str] - Asserti...\nFAILED tests/test_hA.py::test_A100_rejects[config_form_max_sep_complex] - Ass...\nFAILED tests/test_hA.py::test_A100_rejects[config_form_mass_ratio_min_str] - ...\nFAILED tests/test_hA.py::test_A100_rejects[config_form_mass_ratio_min_complex]\nFAILED tests/test_hA.py::test_A100_rejects[config_form_log_mass_min_str] - As...\nFAILED tests/test_hA.py::test_A100_rejects[config_form_log_mass_min_complex]\nFAILED tests/test_hA.py::test_A100_rejects[config_form_log_mass_max_str] - As...\nFAILED tests/test_hA.py::test_A100_rejects[config_form_log_mass_max_complex]\nFAILED tests/test_hA.py::test_A100_rejects[config_form_mass_bin_width_str] - ...\nFAILED tests/test_hA.py::test_A100_rejects[config_form_mass_bin_width_complex]\nFAILED tests/test_hA.py::test_A100_rejects[config_form_max_sep_bytes] - Asser...\n======================== 15 failed, 300 passed in 0.86s ========================\n",
    "stderr_tail": "",
    "obligations": [
      {
        "id": "rejection_matrix",
        "passed": 190,
        "collected": 205,
        "fraction": 0.926829268292683,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_A100_rejects[box_size_form_bytes]",
          "tests/test_hA.py::test_A100_rejects[box_size_form_complex]",
          "tests/test_hA.py::test_A100_rejects[box_size_form_str]",
          "tests/test_hA.py::test_A100_rejects[config_form_log_mass_max_complex]",
          "tests/test_hA.py::test_A100_rejects[config_form_log_mass_max_str]",
          "tests/test_hA.py::test_A100_rejects[config_form_log_mass_min_complex]",
          "tests/test_hA.py::test_A100_rejects[config_form_log_mass_min_str]",
          "tests/test_hA.py::test_A100_rejects[config_form_mass_bin_width_complex]",
          "tests/test_hA.py::test_A100_rejects[config_form_mass_bin_width_str]",
          "tests/test_hA.py::test_A100_rejects[config_form_mass_ratio_min_complex]",
          "tests/test_hA.py::test_A100_rejects[config_form_mass_ratio_min_str]",
          "tests/test_hA.py::test_A100_rejects[config_form_max_sep_bytes]",
          "tests/test_hA.py::test_A100_rejects[config_form_max_sep_complex]",
          "tests/test_hA.py::test_A100_rejects[config_form_max_sep_str]",
          "tests/test_hA.py::test_A100_rejects[mass_bin_width_value_10.0]"
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
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_bool_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_complex_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_inf_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_missing",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_nan_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_ndarray_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_negative_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_numpy_float_valid",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_numpy_int_valid",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_string_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_zero_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_bool_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_bool_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_bool_rejected[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_bool_rejected[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_bool_rejected[x]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_bool_rejected[y]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_bool_rejected[z]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_complex_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_complex_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_complex_rejected[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_complex_rejected[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_complex_rejected[x]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_complex_rejected[y]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_complex_rejected[z]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_string_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_string_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_string_rejected[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_string_rejected[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_string_rejected[x]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_string_rejected[y]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_string_rejected[z]",
      "tests/test_pair_finder_validation.py::TestCatalogExtraKeys::test_extra_keys_accepted",
      "tests/test_pair_finder_validation.py::TestCatalogExtraKeys::test_malformed_extra_keys_accepted",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_each_key_rejected[box_size]",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_each_key_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_each_key_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_each_key_rejected[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_each_key_rejected[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_each_key_rejected[x]",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_each_key_rejected[y]",
      "tests/test_pair_finder_validation.py::TestCatalogMissingKeys::test_each_key_rejected[z]",
      "tests/test_pair_finder_validation.py::TestCatalogNot1D::test_2d_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogNot1D::test_2d_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogNot1D::test_2d_rejected[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogNot1D::test_2d_rejected[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogNot1D::test_2d_rejected[x]",
      "tests/test_pair_finder_validation.py::TestCatalogNot1D::test_2d_rejected[y]",
      "tests/test_pair_finder_validation.py::TestCatalogNot1D::test_2d_rejected[z]",
      "tests/test_pair_finder_validation.py::TestCatalogNotDict::test_list_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogNotDict::test_ndarray_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogNotDict::test_string_rejected",
      "tests/test_pair_finder_validation.py::TestCatalogNotFinite::test_inf_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogNotFinite::test_inf_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogNotFinite::test_inf_rejected[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogNotFinite::test_inf_rejected[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogNotFinite::test_inf_rejected[x]",
      "tests/test_pair_finder_validation.py::TestCatalogNotFinite::test_inf_rejected[y]",
      "tests/test_pair_finder_validation.py::TestCatalogNotFinite::test_inf_rejected[z]",
      "tests/test_pair_finder_validation.py::TestCatalogNotFinite::test_nan_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogNotFinite::test_nan_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogNotFinite::test_nan_rejected[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogNotFinite::test_nan_rejected[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogNotFinite::test_nan_rejected[x]",
      "tests/test_pair_finder_validation.py::TestCatalogNotFinite::test_nan_rejected[y]",
      "tests/test_pair_finder_validation.py::TestCatalogNotFinite::test_nan_rejected[z]",
      "tests/test_pair_finder_validation.py::TestCatalogNotFinite::test_neg_inf_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogNotFinite::test_neg_inf_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogNotFinite::test_neg_inf_rejected[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogNotFinite::test_neg_inf_rejected[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogNotFinite::test_neg_inf_rejected[x]",
      "tests/test_pair_finder_validation.py::TestCatalogNotFinite::test_neg_inf_rejected[y]",
      "tests/test_pair_finder_validation.py::TestCatalogNotFinite::test_neg_inf_rejected[z]",
      "tests/test_pair_finder_validation.py::TestCatalogNotNdarray::test_list_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogNotNdarray::test_list_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogNotNdarray::test_list_rejected[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogNotNdarray::test_list_rejected[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogNotNdarray::test_list_rejected[x]",
      "tests/test_pair_finder_validation.py::TestCatalogNotNdarray::test_list_rejected[y]",
      "tests/test_pair_finder_validation.py::TestCatalogNotNdarray::test_list_rejected[z]",
      "tests/test_pair_finder_validation.py::TestCatalogNotNdarray::test_tuple_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogNotNdarray::test_tuple_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogNotNdarray::test_tuple_rejected[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogNotNdarray::test_tuple_rejected[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogNotNdarray::test_tuple_rejected[x]",
      "tests/test_pair_finder_validation.py::TestCatalogNotNdarray::test_tuple_rejected[y]",
      "tests/test_pair_finder_validation.py::TestCatalogNotNdarray::test_tuple_rejected[z]",
      "tests/test_pair_finder_validation.py::TestCatalogPositionBox::test_negative_position",
      "tests/test_pair_finder_validation.py::TestCatalogPositionBox::test_position_above_box_size",
      "tests/test_pair_finder_validation.py::TestCatalogPositionBox::test_position_at_box_size",
      "tests/test_pair_finder_validation.py::TestCatalogPositionBox::test_position_just_below_box_size_valid",
      "tests/test_pair_finder_validation.py::TestCatalogPositionBox::test_position_zero_valid",
      "tests/test_pair_finder_validation.py::TestCatalogUnequalLength::test_vz_longer",
      "tests/test_pair_finder_validation.py::TestCatalogUnequalLength::test_x_shorter",
      "tests/test_pair_finder_validation.py::TestCheckOrder::test_inf_in_x_reported_as_finite",
      "tests/test_pair_finder_validation.py::TestCheckOrder::test_inf_mass_bin_width_reported_as_finite",
      "tests/test_pair_finder_validation.py::TestCheckOrder::test_nan_box_size_reported_as_finite",
      "tests/test_pair_finder_validation.py::TestCheckOrder::test_nan_in_x_reported_as_finite",
      "tests/test_pair_finder_validation.py::TestCheckOrder::test_sep_bins
```
