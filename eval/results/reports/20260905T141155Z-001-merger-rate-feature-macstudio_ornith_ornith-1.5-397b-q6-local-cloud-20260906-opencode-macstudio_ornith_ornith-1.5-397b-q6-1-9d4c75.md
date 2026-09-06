# Trial report: 20260905T141155Z-001-merger-rate-feature-macstudio_ornith_ornith-1.5-397b-q6-local-cloud-20260906-opencode-macstudio_ornith_ornith-1.5-397b-q6-1-9d4c75

- Task: `001-merger-rate-feature`
- Model: `macstudio/ornith/ornith-1.5-397b-q6` (harness: opencode)
- Model duration: 6078.9s | venv setup: 27.5s | timed out: False | committed: False
- Changed files: src/calc.py, src/config.py, src/merger_rate.py, tests/test_merger_rate.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 88.9 / 100

## Judged: readability 75% of weight, maintainability 75% of weight (judge claude-opus-5, status ok)

## Composite score: 86.8 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 95% |
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
    "raw_tail": ") slope=nan slope_err=nan expected=1.0000 n_excluded=4 status=insufficient_data\\nbin=4 mass=[10.0,10.5) slope=nan slope_err=nan expected=1.0000 n_excluded=4 status=insufficient_data\\nbin=5 mass=[10.5,11.0) slope=nan slope_err=nan expected=1.0000 n_excluded=4 status=insufficient_data\\n'\nE    +  where '==============================================================================\\nmerger-rate redshift-evolution check\\nverifies recovery of the injected merger-timescale model on mock data\\n(expected slope = -merger_timescale_alpha); this is not a measurement of\\nreal merger-rate evolution.\\n==============================================================================\\nbin=0 mass=[8.0,8.5) slope=nan slope_err=nan expected=1.0000 n_excluded=4 status=insufficient_data\\nbin=1 mass=[8.5,9.0) slope=nan slope_err=nan expected=1.0000 n_excluded=4 status=insufficient_data\\nbin=2 mass=[9.0,9.5) slope=nan slope_err=nan expected=1.0000 n_excluded=4 status=insufficient_data\\nbin=3 mass=[9.5,10.0) slope=nan slope_err=nan expected=1.0000 n_excluded=4 status=insufficient_data\\nbin=4 mass=[10.0,10.5) slope=nan slope_err=nan expected=1.0000 n_excluded=4 status=insufficient_data\\nbin=5 mass=[10.5,11.0) slope=nan slope_err=nan expected=1.0000 n_excluded=4 status=insufficient_data\\n' = <built-in method lower of str object at 0x87dca4500>()\nE    +    where <built-in method lower of str object at 0x87dca4500> = '==============================================================================\\nMerger-rate redshift-evolution check\\nVerifies RECOVERY OF THE INJECTED merger-timescale model on MOCK data\\n(expected slope = -merger_timescale_alpha); this is NOT a measurement of\\nreal merger-rate evolution.\\n==============================================================================\\nbin=0 mass=[8.0,8.5) slope=nan slope_err=nan expected=1.0000 n_excluded=4 status=insufficient_data\\nbin=1 mass=[8.5,9.0) slope=nan slope_err=nan expected=1.0000 n_excluded=4 status=insufficient_data\\nbin=2 mass=[9.0,9.5) slope=nan slope_err=nan expected=1.0000 n_excluded=4 status=insufficient_data\\nbin=3 mass=[9.5,10.0) slope=nan slope_err=nan expected=1.0000 n_excluded=4 status=insufficient_data\\nbin=4 mass=[10.0,10.5) slope=nan slope_err=nan expected=1.0000 n_excluded=4 status=insufficient_data\\nbin=5 mass=[10.5,11.0) slope=nan slope_err=nan expected=1.0000 n_excluded=4 status=insufficient_data\\n'.lower\nE    +      where '==============================================================================\\nMerger-rate redshift-evolution check\\nVerifies RECOVERY OF THE INJECTED merger-timescale model on MOCK data\\n(expected slope = -merger_timescale_alpha); this is NOT a measurement of\\nreal merger-rate evolution.\\n==============================================================================\\nbin=0 mass=[8.0,8.5) slope=nan slope_err=nan expected=1.0000 n_excluded=4 status=insufficient_data\\nbin=1 mass=[8.5,9.0) slope=nan slope_err=nan expected=1.0000 n_excluded=4 status=insufficient_data\\nbin=2 mass=[9.0,9.5) slope=nan slope_err=nan expected=1.0000 n_excluded=4 status=insufficient_data\\nbin=3 mass=[9.5,10.0) slope=nan slope_err=nan expected=1.0000 n_excluded=4 status=insufficient_data\\nbin=4 mass=[10.0,10.5) slope=nan slope_err=nan expected=1.0000 n_excluded=4 status=insufficient_data\\nbin=5 mass=[10.5,11.0) slope=nan slope_err=nan expected=1.0000 n_excluded=4 status=insufficient_data\\n' = <built-in method getvalue of _io.StringIO object at 0x10e401510>()\nE    +        where <built-in method getvalue of _io.StringIO object at 0x10e401510> = <_io.StringIO object at 0x10e401510>.getvalue\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_B15_rejection_messages_name_the_reason - Assert...\nFAILED tests/test_hA.py::test_C11_validation_result_keys - AssertionError: ex...\nFAILED tests/test_hA.py::test_C13_validation_prints_insufficient_data - Asser...\n========================= 3 failed, 58 passed in 1.92s =========================\n",
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
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_asserts_on_bad_n_sigma",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_far_outside",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_for_non_finite",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_for_non_positive_slope_err",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_true_within_range",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_accepts_merger_fraction_endpoints_correctly",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_exact_zero_uncertainty_when_sigma_f_zero",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_pinned_values_and_tolerance",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reject_bad_box_size[-1.0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reject_bad_box_size[0.0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reject_bad_box_size[inf]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reject_bad_box_size[nan]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reject_bad_timescale[-2.2]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reject_bad_timescale[0.0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reject_bad_timescale[inf]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reject_bad_timescale[nan]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reject_invalid_scalar_forms_before_coercion[(2+0j)]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reject_invalid_scalar_forms_before_coercion[2.2]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reject_invalid_scalar_forms_before_coercion[True]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reject_invalid_scalar_forms_before_coercion[bad3]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reject_invalid_scalar_forms_before_coercion[bad4]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reject_invalid_scalar_forms_before_coercion[x]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reject_merger_fraction_outside_unit_interval[-0.1]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reject_merger_fraction_outside_unit_interval[0.0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reject_merger_fraction_outside_unit_interval[1.1]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reject_merger_fraction_outside_unit_interval[2.0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reject_merger_fraction_outside_unit_interval[nan]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reject_mismatched_and_non_1d_arrays",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reject_negative_and_nonfinite_array_values",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reject_non_integer_valued_n_galaxies",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reject_zero_ngal_with_nonzero_fraction",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reproduces_reduced_identity",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_ngal_with_both_zero_valid",
      "tests/test_merger_rate.py::TestComputePairFraction::test_accepts_integer_dtype",
      "tests/test_merger_rate.py::TestComputePairFraction::test_accepts_integer_valued_float64",
      "tests/test_merger_rate.py::TestComputePairFraction::test_accepts_unsigned_integer_dtype",
      "tests/test_merger_rate.py::TestComputePairFraction::test_asserts_pair_without_galaxy",
      "tests/test_merger_rate.py::TestComputePairFraction::test_both_zero_bin_is_exact_zero",
      "tests/test_merger_rate.py::TestComputePairFraction::test_f_pair_can_exceed_one",
      "tests/test_merger_rate.py::TestComputePairFraction::test_pinned_values_and_tolerance",
      "tests/test_merger_rate.py::TestComputePairFraction::test_reject_mismatched_shapes",
      "tests/test_merger_rate.py::TestComputePairFraction::test_reject_negative_counts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_reject_non_1d",
      "tests/test_merger_rate.py::TestComputePairFraction::test_reject_non_finite_counts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_reject_non_integer_valued",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_string_array_before_coercion",
      "tests/test_merger_rate.py::TestConfig::test_no_existing_key_changed",
      "tests/test_merger_rate.py::TestConfig::test_three_merger_rate_keys_added",
      "tests/test_merger_rate.py::TestCountGalaxies::test_denominator_from_full_selected_catalog",
      "tests/test_merger_rate.py::TestCountGalaxies::test_does_not_read_mass_bin_by",
      "tests/test_merger_rate.py::TestCountGalaxies::test_edge_example_exact",
      "tests/test_merger_rate.py::TestCountGalaxies::test_returns_int_array_length_nbins",
      "tests/test_merger_rate.py::TestFit::test_collapsed_predictor_nextafter_returns_nan",
      "tests/test_merger_rate.py::TestFit::test_exactly_two_points_finite_fit",
      "tests/test_merger_rate.py::TestFit::test_fewer_than_two_usable_returns_nan",
      "tests/test_merger_rate.py::TestFit::test_is_provably_weighted",
      "tests/test_merger_rate.py::TestFit::test_malformed_redshifts_fail",
      "tests/test_merger_rate.py::TestFit::test_mixed_exclusion_counts_correctly",
      "tests/test_merger_rate.py::TestFit::test_power_law_recovered",
      "tests/test_merger_rate.py::TestFit::test_shape_and_rank_violations_fail",
      "tests/test_merger_rate.py::TestFit::test_single_shared_redshift_returns_nan",
      "tests/test_merger_rate.py::TestFit::test_slope_err_matches_hand_computed_two_point",
      "tests/test_merger_rate.py::TestFit::test_slope_err_not_residual_rescaled",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_accepts_python_int_and_numpy_scalar_box_size",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_bad_box_size_scalar_forms[(1+2j)]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_bad_box_size_scalar_forms[abc]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_bad_box_size_scalar_forms[bad3]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_bad_box_size_scalar_forms[bytes]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_attr",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_dataset",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_file",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_nonpositive_or_nonfinite_box_size",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_out_of_range_index",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_wrong_length_denominator",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_returns_known_values_in_bin_order",
      "tests/test_merger_rate.py::TestMergerTimescale::test_pinned_distinct_parameters",
      "tests/test_merger_rate.py::TestMergerTimescale::test_reject_invalid_scalar_form_before_coercion[(2+0j)]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_reject_invalid_scalar_form_before_coercion[2.0]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_reject_invalid_scalar_form_before_coercion[2]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_reject_invalid_scalar_form_before_coercion[True]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_reject_invalid_scalar_form_before_coercion[bad3]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_reject_invalid_scalar_form_before_coercion[bad4]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_reject_non_finite_alpha",
      "tests/test_merger_rate.py::TestMergerTimescale::test_reject_non_finite_z",
      "tests/test_merger_rate.py::TestMergerTimescale::test_reject_non_positive_t0",
      "tests/test_merger_rate.py::TestMergerTimescale::test_reject_z_le_minus_one",
      "tests/test_merger_rate.py::TestMergerTimescale::test_zero_redshift_is_normalization_exactly",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_docstrings_contain_required_sentence",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_mass_bin_by_primary_required",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_output_finite_nonnegative_on_mock",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_output_schema_and_ordering",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_accepts_numpy_int_recorded_redshift",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_malformed_redshift_attr_preserves_output[(2+0j)]",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_malformed_redshift_attr_preserves_output[bad2]",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_malformed_redshift_attr_preserves_output[not_a_number]",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_missing_pair_file_preserves_output",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_redshift_mismatch_preserves_output",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_uses_per_file_box_size_not_config",
      "tests/test_merger_rate.py::TestRunValidation::test_end_to_end_recovers_injected_slope",
      "tests/test_merger_rate.py::TestRunValidation::test_expected_slope_tracks_non_default_alpha",
      "tests/test_merger_rate.py::TestRunValidation::test_insufficient_data_line_and_heading",
      "tests/test_merger_rate.py::TestRunValidation::test_rejects_malformed_stored_redshift_before_fit",
      "tests/test_merger_rate.py::TestRunValidation::test_result_dict_keys_exact",
      "tests/test_merger_rate.py::TestSavePairsPersistence::test_box_size_from_catalog_not_config",
      "tests/test_merger_rate.py::TestSavePairsPersistence::test_existing_datasets_unchanged_value",
      "tests/test_merger_rate.py::TestSavePairsPersistence::test_new_dataset_and_attr_present",
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
      "tests/test_statistical.py::TestBulkVelocityCancellation::test_delta_v_independent_of_bulk_sigma",
      "tests/test_statistical.py::TestCrossBinKineticTheory::test_cross_bin_sigma_eff",
      "tests/test_statistical.py::TestMassRatioDistribution::test_mass_ratio_is_uniform",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[0-2.0]",
    
```
