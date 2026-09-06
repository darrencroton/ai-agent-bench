# Trial report: 20260906T115930Z-003-pair-finder-validation-opencode-go_mimo-v2.5-pro-sixth-session-20260906-mimo-v2.5-pro-opencode-opencode-go_mimo-v2.5-pro-2-ce6361

- Task: `003-pair-finder-validation`
- Model: `opencode-go/mimo-v2.5-pro` (harness: opencode)
- Model duration: 837.7s | venv setup: 28.2s | timed out: False | committed: False
- Changed files: src/pair_finder.py, tests/test_pair_finder_validation.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 95.3 / 100

## Judged: readability 75% of weight, maintainability 25% of weight (judge claude-opus-5, status ok)

## Composite score: 88.8 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 100% |
| test_adequacy | automated | 25 | 84% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 100% |
| readability | judged | 8 | 75% |
| maintainability | judged | 7 | 25% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| rejection_matrix | 204 | 205 | 1.00 |
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
    "passed": 314,
    "failed": [
      "tests/test_hA.py::test_A100_rejects[mass_bin_width_value_10.0]"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "t_A309_mass_bin_by_strategies_still_work[secondary] PASSED [ 89%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[mean] PASSED [ 89%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[total] PASSED [ 89%]\ntests/test_hA.py::test_A310_signature_unchanged PASSED                   [ 90%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int16-ascending_dv] PASSED [ 90%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int16-descending_dv] PASSED [ 90%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint16-ascending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint16-descending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int32-ascending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int32-descending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint32-ascending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint32-descending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int64-ascending_dv] PASSED [ 93%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int64-descending_dv] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vx] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vy] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vz] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vx] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vy] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vz] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vx] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vy] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vz] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vx] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vy] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vz] PASSED [ 97%]\ntests/test_hA.py::test_A311_validation_precedes_no_pairs_return_nonfinite PASSED [ 97%]\ntests/test_hA.py::test_A312_validation_precedes_no_pairs_return_length PASSED [ 97%]\ntests/test_hA.py::test_A313_validation_precedes_mass_ratio_cut_return PASSED [ 98%]\ntests/test_hB.py::test_B00_pipeline_imports PASSED                       [ 98%]\ntests/test_hB.py::test_B01_driver_output_matches_the_analytic_expectation PASSED [ 98%]\ntests/test_hB.py::test_B02_nonfinite_position_on_disk_asserts PASSED     [ 99%]\ntests/test_hB.py::test_B03_position_outside_box_on_disk_asserts PASSED   [ 99%]\ntests/test_hB.py::test_B04_malformed_config_through_driver PASSED        [ 99%]\ntests/test_hB.py::test_B05_driver_honours_nondefault_config PASSED       [100%]\n\n=================================== FAILURES ===================================\n_________________ test_A100_rejects[mass_bin_width_value_10.0] _________________\ntests/test_hA.py:513: in test_A100_rejects\n    assert any(re.search(rf\"\\b{re.escape(n)}\\b\", message) for n in names), (\nE   AssertionError: message names none of ['mass_bin_width']: 'mass grid must define at least one mass bin'\nE   assert False\nE    +  where False = any(<generator object test_A100_rejects.<locals>.<genexpr> at 0x10da10140>)\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A100_rejects[mass_bin_width_value_10.0] - Asser...\n======================== 1 failed, 314 passed in 0.66s =========================\n",
    "stderr_tail": "",
    "obligations": [
      {
        "id": "rejection_matrix",
        "passed": 204,
        "collected": 205,
        "fraction": 0.9951219512195122,
        "uncollected": false,
        "failed_nodes": [
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
      "tests/test_pair_finder_validation.py::TestBug2DArrays::test_2d_x_raises_assertionerror",
      "tests/test_pair_finder_validation.py::TestBugMassBinWidthZero::test_mass_bin_width_zero_raises_assertionerror",
      "tests/test_pair_finder_validation.py::TestBugSepBins2D::test_sep_bins_2d_raises_assertionerror",
      "tests/test_pair_finder_validation.py::TestBugSepBinsNan::test_sep_bins_nan_raises_assertionerror",
      "tests/test_pair_finder_validation.py::TestBugSepBinsUnsorted::test_sep_bins_unsorted_raises_assertionerror",
      "tests/test_pair_finder_validation.py::TestCatalog1D::test_2d_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalog1D::test_2d_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestCatalog1D::test_2d_rejected[vy]",
      "tests/test_pair_finder_validation.py::TestCatalog1D::test_2d_rejected[vz]",
      "tests/test_pair_finder_validation.py::TestCatalog1D::test_2d_rejected[x]",
      "tests/test_pair_finder_validation.py::TestCatalog1D::test_2d_rejected[y]",
      "tests/test_pair_finder_validation.py::TestCatalog1D::test_2d_rejected[z]",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_box_size_bool",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_box_size_complex",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_box_size_inf",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_box_size_missing",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_box_size_nan",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_box_size_negative",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_box_size_not_scalar",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_box_size_numpy_scalar",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_box_size_string",
      "tests/test_pair_finder_validation.py::TestCatalogBoxSize::test_box_size_zero",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_bool_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_bool_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_bool_rejected[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_bool_rejected[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_bool_rejected[x]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_bool_rejected[y]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_bool_rejected[z]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_bytes_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_bytes_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_bytes_rejected[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_bytes_rejected[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_bytes_rejected[x]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_bytes_rejected[y]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_bytes_rejected[z]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_complex_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_complex_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_complex_rejected[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_complex_rejected[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_complex_rejected[x]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_complex_rejected[y]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_complex_rejected[z]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_object_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_object_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_object_rejected[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_object_rejected[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_object_rejected[x]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_object_rejected[y]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_object_rejected[z]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_string_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_string_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_string_rejected[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_string_rejected[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_string_rejected[x]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_string_rejected[y]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_string_rejected[z]",
      "tests/test_pair_finder_validation.py::TestCatalogDtype::test_valid_dtypes_accepted",
      "tests/test_pair_finder_validation.py::TestCatalogExtraKeys::test_extra_keys_ignored",
      "tests/test_pair_finder_validation.py::TestCatalogExtraKeys::test_malformed_extra_keys_ignored",
      "tests/test_pair_finder_validation.py::TestCatalogFinite::test_inf_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogFinite::test_inf_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogFinite::test_inf_rejected[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogFinite::test_inf_rejected[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogFinite::test_inf_rejected[x]",
      "tests/test_pair_finder_validation.py::TestCatalogFinite::test_inf_rejected[y]",
      "tests/test_pair_finder_validation.py::TestCatalogFinite::test_inf_rejected[z]",
      "tests/test_pair_finder_validation.py::TestCatalogFinite::test_nan_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogFinite::test_nan_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogFinite::test_nan_rejected[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogFinite::test_nan_rejected[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogFinite::test_nan_rejected[x]",
      "tests/test_pair_finder_validation.py::TestCatalogFinite::test_nan_rejected[y]",
      "tests/test_pair_finder_validation.py::TestCatalogFinite::test_nan_rejected[z]",
      "tests/test_pair_finder_validation.py::TestCatalogFinite::test_neg_inf_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogFinite::test_neg_inf_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogFinite::test_neg_inf_rejected[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogFinite::test_neg_inf_rejected[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogFinite::test_neg_inf_rejected[x]",
      "tests/test_pair_finder_validation.py::TestCatalogFinite::test_neg_inf_rejected[y]",
      "tests/test_pair_finder_validation.py::TestCatalogFinite::test_neg_inf_rejected[z]",
      "tests/test_pair_finder_validation.py::TestCatalogFinitenessBeforeBox::test_inf_in_x_reported_as_finite_not_box",
      "tests/test_pair_finder_validation.py::TestCatalogFinitenessBeforeBox::test_nan_in_x_reported_as_finite_not_box",
      "tests/test_pair_finder_validation.py::TestCatalogIntegerDtypeConversion::test_float_dtypes_accepted[float32]",
      "tests/test_pair_finder_validation.py::TestCatalogIntegerDtypeConversion::test_float_dtypes_accepted[float64]",
      "tests/test_pair_finder_validation.py::TestCatalogIntegerDtypeConversion::test_narrow_integer_velocity_no_overflow",
      "tests/test_pair_finder_validation.py::TestCatalogIntegerDtypeConversion::test_signed_integer_catalog_matches_float64[int32]",
      "tests/test_pair_finder_validation.py::TestCatalogIntegerDtypeConversion::test_signed_integer_catalog_matches_float64[int64]",
      "tests/test_pair_finder_validation.py::TestCatalogIntegerDtypeConversion::test_unsigned_integer_catalog_matches_float64[uint32]",
      "tests/test_pair_finder_validation.py::TestCatalogIntegerDtypeConversion::test_unsigned_integer_catalog_matches_float64[uint64]",
      "tests/test_pair_finder_validation.py::TestCatalogIsDict::test_catalog_not_a_dict",
      "tests/test_pair_finder_validation.py::TestCatalogIsDict::test_catalog_string",
      "tests/test_pair_finder_validation.py::TestCatalogNdarray::test_list_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogNdarray::test_list_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogNdarray::test_list_rejected[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogNdarray::test_list_rejected[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogNdarray::test_list_rejected[x]",
      "tests/test_pair_finder_validation.py::TestCatalogNdarray::test_list_rejected[y]",
      "tests/test_pair_finder_validation.py::TestCatalogNdarray::test_list_rejected[z]",
      "tests/test_pair_finder_validation.py::TestCatalogNdarray::test_tuple_rejected[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogNdarray::test_tuple_rejected[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogNdarray::test_tuple_rejected[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogNdarray::test_tuple_rejected[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogNdarray::test_tuple_rejected[x]",
      "tests/test_pair_finder_validation.py::TestCatalogNdarray::test_tuple_rejected[y]",
      "tests/test_pair_finder_validation.py::TestCatalogNdarray::test_tuple_rejected[z]",
      "tests/test_pair_finder_validation.py::TestCatalogPositionRange::test_negative_x",
      "tests/test_pair_finder_validation.py::TestCatalogPositionRange::test_negative_y",
      "tests/test_pair_finder_validation.py::TestCatalogPositionRange::test_negative_z",
      "tests/test_pair_finder_validation.py::TestCatalogPositionRange::test_x_equals_box_size",
      "tests/test_pair_finder_validation.py::TestCatalogPositionRange::test_x_equals_zero",
      "tests/test_pair_finder_validation.py::TestCatalogPositionRange::test_x_just_below_box_size",
      "tests/test_pair_finder_validation.py::TestCatalogRequiredKeys::test_missing_array_key[log_stellar_mass]",
      "tests/test_pair_finder_validation.py::TestCatalogRequiredKeys::test_missing_array_key[vx]",
      "tests/test_pair_finder_validation.py::TestCatalogRequiredKeys::test_missing_array_key[vy]",
      "tests/test_pair_finder_validation.py::TestCatalogRequiredKeys::test_missing_array_key[vz]",
      "tests/test_pair_finder_validation.py::TestCatalogRequiredKeys::test_missing_array_key[x]",
      "tests/test_pair_finder_validation.py::TestCatalogRequiredKeys::test_missing_array_key[y]",
      "tests/test_pair_finder_validation.py::TestCatalogRequiredKeys::test_missing_array_key[z]",
      "tests/test_pair_finder_validation.py::TestCatalogRequiredKeys::test_missing_box_size",
   
```
