# Trial report: 20260906T084535Z-001-merger-rate-feature-opencode-go_mimo-v2.5-sixth-session-20260906-mimo-v2.5-opencode-opencode-go_mimo-v2.5-3-1fd568

- Task: `001-merger-rate-feature`
- Model: `opencode-go/mimo-v2.5` (harness: opencode)
- Model duration: 1521.7s | venv setup: 28.0s | timed out: False | committed: False
- Changed files: src/calc.py, src/config.py, src/merger_rate.py, tests/test_merger_rate.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 82.1 / 100

## Judged: readability 50% of weight, maintainability 25% of weight (judge claude-opus-5, status ok)

## Composite score: 75.5 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 95% |
| test_adequacy | automated | 25 | 51% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 91% |
| readability | judged | 8 | 50% |
| maintainability | judged | 7 | 25% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| calc_galaxy_denominator | 4 | 4 | 1.00 |
| persistence_schema_provenance | 5 | 5 | 1.00 |
| load_pair_counts_rejections | 8 | 8 | 1.00 |
| pair_fraction_core | 9 | 10 | 0.90 |
| merger_timescale_and_rate_conversion | 11 | 13 | 0.85 |
| run_merger_rate_calculation_pipeline | 4 | 4 | 1.00 |
| redshift_evolution_fit_and_consistency | 10 | 10 | 1.00 |
| validation_reporting_and_e2e | 6 | 7 | 0.86 |

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
      "tests/test_hA.py::test_B12_merger_rate_array_rejections",
      "tests/test_hA.py::test_B14_docstring_wording",
      "tests/test_hA.py::test_B15_rejection_messages_name_the_reason",
      "tests/test_hA.py::test_C11_validation_result_keys"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "s_index_not_string PASSED           [ 85%]\ntests/test_hA.py::test_C15_consistent_is_python_bool_or_none PASSED      [ 86%]\ntests/test_hB.py::test_E01_slice1_additive_schema PASSED                 [ 88%]\ntests/test_hB.py::test_E02_denominator_from_full_catalog PASSED          [ 90%]\ntests/test_hB.py::test_E03_box_size_from_catalog_not_config PASSED       [ 91%]\ntests/test_hB.py::test_E04_per_file_box_size_used PASSED                 [ 93%]\ntests/test_hB.py::test_E05_preflight_atomicity_sha256 PASSED             [ 95%]\ntests/test_hB.py::test_E06_output_schema PASSED                          [ 96%]\ntests/test_hB.py::test_E07_end_to_end_science PASSED                     [ 98%]\ntests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha PASSED [100%]\n\n=================================== FAILURES ===================================\n____________________ test_B12_merger_rate_array_rejections _____________________\ntests/test_hA.py:378: in test_B12_merger_rate_array_rejections\n    assert rejects(MR.compute_merger_rate, fp, sf, ng, 500.0, 2.2, 0.6) == \"assert\"\nE   AssertionError: assert None == 'assert'\nE    +  where None = rejects(<function compute_merger_rate at 0x10bdf38a0>, array([0.5]), array([0.1]), array([inf]), 500.0, 2.2, 0.6)\nE    +    where <function compute_merger_rate at 0x10bdf38a0> = MR.compute_merger_rate\n__________________________ test_B14_docstring_wording __________________________\ntests/test_hA.py:395: in test_B14_docstring_wording\n    assert required in doc, f\"{fn.__name__} lacks the required uncertainty wording\"\nE   AssertionError: compute_pair_fraction lacks the required uncertainty wording\nE   assert \"Uncertainty follows Task 001's plug-in Poisson-error convention; it is not a confidence interval.\" in \"Compute pair fraction and its Poisson uncertainty per mass bin.\\n\\nf_pair(b) = n_pairs(b) / n_galaxies(b)\\n\\nUncertainty follows Task 001's plug-in Poisson-error convention; it is\\nnot a confidence interval.\\n\\nParameters\\n----------\\nn_pairs : array-like, 1D, non-negative integers\\nn_galaxies : array-like, 1D, non-negative integers, same shape as n_pairs\\n\\nReturns\\n-------\\n(f_pair, sigma_f_pair) as float64 arrays of the input shape.\"\n_________________ test_B15_rejection_messages_name_the_reason __________________\ntests/test_hA.py:399: in test_B15_rejection_messages_name_the_reason\n    assert_rejects_with(\"shape\", MR.compute_pair_fraction,\ntests/test_hA.py:57: in assert_rejects_with\n    with pytest.raises(AssertionError, match=pattern):\n         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE   AssertionError: Regex pattern did not match.\nE     Expected regex: 'shape'\nE     Actual message: 'Shape mismatch: n_pairs (2,) != n_galaxies (1,)'\n_______________________ test_C11_validation_result_keys ________________________\ntests/test_hA.py:589: in test_C11_validation_result_keys\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:557: in _parse_bin_line\n    assert all((mass, slope, slope_err, expected, excluded, status)), line\nE   AssertionError:   bin 0 [8.0, 8.5): slope=1.0000 +/- 0.0966, expected=1.0, n_excluded=0, PASS\nE   assert False\nE    +  where False = all((<re.Match object; span=(8, 18), match='[8.0, 8.5)'>, <re.Match object; span=(20, 32), match='slope=1.0000'>, <re.Match object; span=(33, 43), match='+/- 0.0966'>, <re.Match object; span=(45, 57), match='expected=1.0'>, <re.Match object; span=(59, 71), match='n_excluded=0'>, None))\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_B12_merger_rate_array_rejections - AssertionErr...\nFAILED tests/test_hA.py::test_B14_docstring_wording - AssertionError: compute...\nFAILED tests/test_hA.py::test_B15_rejection_messages_name_the_reason - Assert...\nFAILED tests/test_hA.py::test_C11_validation_result_keys - AssertionError:   ...\n========================= 4 failed, 57 passed in 1.95s =========================\n",
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
        "passed": 11,
        "collected": 13,
        "fraction": 0.8461538461538461,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_B12_merger_rate_array_rejections",
          "tests/test_hA.py::test_B14_docstring_wording"
        ]
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
        "passed": 6,
        "collected": 7,
        "fraction": 0.8571428571428571,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_C11_validation_result_keys"
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
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_custom_n_sigma",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_expected",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_slope",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_non_finite_slope_err",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_outside_range",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_rejects_negative_n_sigma",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_rejects_non_finite_n_sigma",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_slope_err_negative",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_slope_err_zero",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_within_range",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_accepts_zero_galaxies_zero_fpair",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_known_values",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reduced_identity",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_bool_box_size",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_merger_fraction_gt_one",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_merger_fraction_zero",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_ndarray_box_size",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_negative_box_size",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_negative_timescale",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_non_integer_n_galaxies",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_zero_galaxies_nonzero_fpair",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_zero_galaxies_nonzero_sigma",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_sigma_f_pair",
      "tests/test_merger_rate.py::TestComputePairFraction::test_accepts_integer_dtype",
      "tests/test_merger_rate.py::TestComputePairFraction::test_accepts_integer_valued_float64",
      "tests/test_merger_rate.py::TestComputePairFraction::test_known_values",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_mismatched_shapes",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_negative_counts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_1d",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_finite",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_non_integer_counts",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_pairs_without_galaxies",
      "tests/test_merger_rate.py::TestComputePairFraction::test_zero_pairs_zero_galaxies",
      "tests/test_merger_rate.py::TestConfigAdditions::test_default_values",
      "tests/test_merger_rate.py::TestConfigAdditions::test_keys_present",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_all_in_one_bin",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_empty_input",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_known_values",
      "tests/test_merger_rate.py::TestEndToEndMockData::test_all_bins_consistent",
      "tests/test_merger_rate.py::TestEndToEndMockData::test_all_bins_finite_rates",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_exact_power_law",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_exactly_two_usable_points_finite",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fewer_than_two_usable_returns_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_malformed_redshifts_fail",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_mismatched_shapes",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_mix_of_excluded_reasons",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_non_1d_shape_violation",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_single_redshift_all_usable_returns_nan",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_slope_err_matches_hand_computed",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_weighted_fit_provably_closer",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_basic_loading",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_excludes_sentinel_minus_one",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_mass_bin_index",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_box_size_attr",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_dataset",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_file",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_negative_box_size",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_non_scalar_box_size",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_wrong_length_n_galaxies",
      "tests/test_merger_rate.py::TestMassBinEdges::test_default_config",
      "tests/test_merger_rate.py::TestMassBinEdges::test_different_width",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_custom_values",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_bool_z",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_complex_z",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_ndarray_z",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_negative_gyr0",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_non_finite_alpha",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_string_z",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_z_inf",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_z_minus_one",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_z_nan",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_rejects_zero_gyr0",
      "tests/test_merger_rate.py::TestMergerTimescaleGyr::test_z_zero",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_leaves_sentinel_unchanged",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_malformed_redshift_leaves_sentinel",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_preflight_mismatched_redshift_leaves_sentinel",
      "tests/test_merger_rate.py::TestRunMergerRateCalculation::test_rejects_non_primary_mass_bin_by",
      "tests/test_merger_rate.py::TestRunMergerRateCalculationEndToEnd::test_compute_pair_fraction_docstring",
      "tests/test_merger_rate.py::TestRunMergerRateCalculationEndToEnd::test_merger_rate_docstring",
      "tests/test_merger_rate.py::TestRunMergerRateCalculationEndToEnd::test_output_schema",
      "tests/test_merger_rate.py::TestRunMergerRateCalculationEndToEnd::test_uses_per_file_box_size",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_bin_line_parseable",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_expected_slope_tracks_alpha",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_fails_on_malformed_stored_redshift",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_heading_states_injected_model",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_insufficient_data_printed",
      "tests/test_merger_rate.py::TestRunMergerRateValidation::test_result_dict_keys",
      "tests/test_merger_rate.py::TestSavePairsSignature::test_save_and_reload",
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
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-3.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-4.0]",
      "tests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-5.0]",
      "tests/test_statistical.py::TestMaxwellMoments::test_mean[0]",
      "tests/test_statistical.py::TestMaxwellMoments::test_mean[1]",
      "tests/test_statistical.py::TestM
```
