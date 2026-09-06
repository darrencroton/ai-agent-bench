# Trial report: 20260905T160203Z-001-merger-rate-feature-macstudio_ornith_ornith-1.5-397b-q6-local-cloud-20260906-opencode-macstudio_ornith_ornith-1.5-397b-q6-2-f3a674

- Task: `001-merger-rate-feature`
- Model: `macstudio/ornith/ornith-1.5-397b-q6` (harness: opencode)
- Model duration: 6466.5s | venv setup: 31.2s | timed out: False | committed: False
- Changed files: src/calc.py, src/config.py, src/merger_rate.py, tests/test_merger_rate.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 89.9 / 100

## Judged: readability 75% of weight, maintainability 75% of weight (judge claude-opus-5, status ok)

## Composite score: 87.7 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 100% |
| test_adequacy | automated | 25 | 66% |
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
| validation_reporting_and_e2e | 7 | 7 | 1.00 |

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
    "passed": 61,
    "failed": [],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "teger_float_both_accepted PASSED [ 21%]\ntests/test_hA.py::test_A14_load_pair_counts_values_and_sentinel PASSED   [ 22%]\ntests/test_hA.py::test_A15_load_pair_counts_bad_bin_index PASSED         [ 24%]\ntests/test_hA.py::test_A16_load_pair_counts_missing_file PASSED          [ 26%]\ntests/test_hA.py::test_A17_load_pair_counts_missing_dataset PASSED       [ 27%]\ntests/test_hA.py::test_A18_load_pair_counts_missing_attr PASSED          [ 29%]\ntests/test_hA.py::test_A19_load_pair_counts_wrong_length PASSED          [ 31%]\ntests/test_hA.py::test_A20_load_pair_counts_bad_box PASSED               [ 32%]\ntests/test_hA.py::test_A21_load_pair_counts_vector_box_attr PASSED       [ 34%]\ntests/test_hA.py::test_A22_load_pair_counts_rejects_non_numeric_scalar_box_attr PASSED [ 36%]\ntests/test_hA.py::test_A23_part1_helpers_do_not_require_mass_bin_by PASSED [ 37%]\ntests/test_hA.py::test_B01_config_keys PASSED                            [ 39%]\ntests/test_hA.py::test_B02_timescale_at_zero_exact PASSED                [ 40%]\ntests/test_hA.py::test_B03_timescale_pinned PASSED                       [ 42%]\ntests/test_hA.py::test_B04_merger_rate_pinned PASSED                     [ 44%]\ntests/test_hA.py::test_B05_reduced_identity_exact PASSED                 [ 45%]\ntests/test_hA.py::test_B06_zero_sigma_exact_zero PASSED                  [ 47%]\ntests/test_hA.py::test_B07_zero_galaxies_rules PASSED                    [ 49%]\ntests/test_hA.py::test_B08_mass_bin_by_assertion PASSED                  [ 50%]\ntests/test_hA.py::test_B09_timescale_rejections PASSED                   [ 52%]\ntests/test_hA.py::test_B10_timescale_rejects_string_and_array PASSED     [ 54%]\ntests/test_hA.py::test_B11_merger_rate_scalar_rejections PASSED          [ 55%]\ntests/test_hA.py::test_B12_merger_rate_array_rejections PASSED           [ 57%]\ntests/test_hA.py::test_B13_merger_rate_rejects_string_box_by_assertion PASSED [ 59%]\ntests/test_hA.py::test_B14_docstring_wording PASSED                      [ 60%]\ntests/test_hA.py::test_B15_rejection_messages_name_the_reason PASSED     [ 62%]\ntests/test_hA.py::test_C01_exact_power_law PASSED                        [ 63%]\ntests/test_hA.py::test_C02_provably_weighted PASSED                      [ 65%]\ntests/test_hA.py::test_C03_two_point_slope_err_pinned PASSED             [ 67%]\ntests/test_hA.py::test_C04_two_usable_with_exclusions_finite PASSED      [ 68%]\ntests/test_hA.py::test_C05_fewer_than_two_usable PASSED                  [ 70%]\ntests/test_hA.py::test_C06_single_redshift_returns_nan PASSED            [ 72%]\ntests/test_hA.py::test_C07_malformed_redshifts_and_rank PASSED           [ 73%]\ntests/test_hA.py::test_C08_check_slope_consistency PASSED                [ 75%]\ntests/test_hA.py::test_C09_collapsed_predictor PASSED                    [ 77%]\ntests/test_hA.py::test_C10_y_centring_numerical_stability PASSED         [ 78%]\ntests/test_hA.py::test_C11_validation_result_keys PASSED                 [ 80%]\ntests/test_hA.py::test_C12_validation_rejects_malformed_stored_redshift_before_fit PASSED [ 81%]\ntests/test_hA.py::test_C13_validation_prints_insufficient_data PASSED    [ 83%]\ntests/test_hA.py::test_C14_mass_bin_is_index_not_string PASSED           [ 85%]\ntests/test_hA.py::test_C15_consistent_is_python_bool_or_none PASSED      [ 86%]\ntests/test_hB.py::test_E01_slice1_additive_schema PASSED                 [ 88%]\ntests/test_hB.py::test_E02_denominator_from_full_catalog PASSED          [ 90%]\ntests/test_hB.py::test_E03_box_size_from_catalog_not_config PASSED       [ 91%]\ntests/test_hB.py::test_E04_per_file_box_size_used PASSED                 [ 93%]\ntests/test_hB.py::test_E05_preflight_atomicity_sha256 PASSED             [ 95%]\ntests/test_hB.py::test_E06_output_schema PASSED                          [ 96%]\ntests/test_hB.py::test_E07_end_to_end_science PASSED                     [ 98%]\ntests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha PASSED [100%]\n\n============================== 61 passed in 1.80s ==============================\n",
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
      "tests/test_merger_rate.py::TestCalcMassBinEdges::test_edges_formula",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_asserts_on_bad_n_sigma[-1.0]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_asserts_on_bad_n_sigma[0.0]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_asserts_on_bad_n_sigma[inf]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_asserts_on_bad_n_sigma[nan]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_far_outside",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_for_non_finite",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_for_nonpositive_err",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_true_within_range",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_accepts_merger_fraction_one",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_exact_zero_uncertainty_preserved",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_pinned_values",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reduced_identity",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bad_box_or_ts",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form[(1+2j)]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form[500.0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form[True]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_scalar_form[bad2]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_merger_fraction_outside_unit_interval[-0.1]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_merger_fraction_outside_unit_interval[0.0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_merger_fraction_outside_unit_interval[1.5]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_mismatched_and_non_1d",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_negative_and_non_integer_ngal",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_ngal_both_zero_valid",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_ngal_with_nonzero_fraction_asserts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_accepts_integer_and_integer_valued_float",
      "tests/test_merger_rate.py::TestComputePairFraction::test_empty_over_empty_is_exact_zero",
      "tests/test_merger_rate.py::TestComputePairFraction::test_f_pair_can_exceed_one",
      "tests/test_merger_rate.py::TestComputePairFraction::test_pair_without_galaxy_asserts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_pinned_values",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_mismatched_shapes",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_negative",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_1d",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_finite",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_integer_valued",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_string_dtype_before_coercion",
      "tests/test_merger_rate.py::TestConfigKeys::test_existing_keys_unchanged",
      "tests/test_merger_rate.py::TestConfigKeys::test_keys_added_with_defaults",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_does_not_read_mass_bin_by",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_exact_upper_edge_excluded",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_length_matches_n_mass_bins",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_sum_equals_right_open_selected_count",
      "tests/test_merger_rate.py::TestEndToEnd::test_slopes_consistent_with_injected_model",
      "tests/test_merger_rate.py::TestFit::test_exactly_two_usable_returns_finite_with_exclusion",
      "tests/test_merger_rate.py::TestFit::test_fewer_than_two_usable",
      "tests/test_merger_rate.py::TestFit::test_fewer_than_two_usable_via_nonpositive_err",
      "tests/test_merger_rate.py::TestFit::test_malformed_redshifts_assert[bad_z0]",
      "tests/test_merger_rate.py::TestFit::test_malformed_redshifts_assert[bad_z1]",
      "tests/test_merger_rate.py::TestFit::test_malformed_redshifts_assert[bad_z2]",
      "tests/test_merger_rate.py::TestFit::test_nextafter_redshifts_collapse_predictor",
      "tests/test_merger_rate.py::TestFit::test_power_law_recovered",
      "tests/test_merger_rate.py::TestFit::test_rank_and_shape_violations_assert",
      "tests/test_merger_rate.py::TestFit::test_single_distinct_redshift_collapses",
      "tests/test_merger_rate.py::TestFit::test_slope_err_pinned_two_point",
      "tests/test_merger_rate.py::TestFit::test_weighted_beats_unweighted",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_known_fixture_values",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_bad_box_scalar_forms[250.0]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_bad_box_scalar_forms[True]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_bad_box_scalar_forms[bad1]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_below_minus_one",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_box_attr",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_file",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_ngal_dataset",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_non_finite_or_non_positive_box[-5.0]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_non_finite_or_non_positive_box[inf]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_non_finite_or_non_positive_box[nan]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_out_of_range_index",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_wrong_length_ngal",
      "tests/test_merger_rate.py::TestMergerTimescale::test_distinct_params",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_invalid_scalar_form_any_input[(1+2j)]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_invalid_scalar_form_any_input[2.2_0]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_invalid_scalar_form_any_input[2.2_1]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_invalid_scalar_form_any_input[True]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_invalid_scalar_form_any_input[bad3]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_invalid_scalar_form_any_input[bad4]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_non_finite_alpha",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_non_finite_z",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_non_positive_t0",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejects_z_leq_minus_one",
      "tests/test_merger_rate.py::TestMergerTimescale::test_zero_redshift_exact",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_mass_bin_by_must_be_primary",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_output_schema_and_finiteness",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_per_file_box_size_used_not_config",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_malformed_redshift_attr_leaves_output_untouched",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_missing_pair_file_leaves_output_untouched",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_redshift_mismatch_leaves_output_untouched",
      "tests/test_merger_rate.py::TestRunValidation::test_expected_slope_tracks_nondefault_alpha",
      "tests/test_merger_rate.py::TestRunValidation::test_insufficient_data_line_and_heading",
      "tests/test_merger_rate.py::TestRunValidation::test_malformed_stored_redshift_fails_before_fit",
      "tests/test_merger_rate.py::TestRunValidation::test_result_dict_keys_and_types",
      "tests/test_merger_rate.py::TestSavePairsAdditions::test_box_size_comes_from_catalog_not_config",
      "tests/test_merger_rate.py::TestSavePairsAdditions::test_denominator_is_full_selected_catalog",
      "tests/test_merger_rate.py::TestSavePairsAdditions::test_new_dataset_and_attr_present",
      "tests/test_merger_rate.py::TestUncertaintyConventionDocstring::test_exact_sentence_in_both_docstrings",
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
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[0-3.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[0-4.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[0-5.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[1-2.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[1-3.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[1-4.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[1-5.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[2-2.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[2-3.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[2-4.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[2-5.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[3-2.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[3-3.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[3-4.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[3-5.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-2.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-3.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-4.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-5.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-2.0]",
      "tests/test_statistical.py::TestMaxwellDistributio
```
