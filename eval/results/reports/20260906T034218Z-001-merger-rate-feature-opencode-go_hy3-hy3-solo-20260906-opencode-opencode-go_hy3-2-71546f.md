# Trial report: 20260906T034218Z-001-merger-rate-feature-opencode-go_hy3-hy3-solo-20260906-opencode-opencode-go_hy3-2-71546f

- Task: `001-merger-rate-feature`
- Model: `opencode-go/hy3` (harness: opencode)
- Model duration: 820.7s | venv setup: 26.4s | timed out: False | committed: False
- Changed files: src/calc.py, src/config.py, src/merger_rate.py, tests/test_merger_rate.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 87.1 / 100

## Judged: readability 75% of weight, maintainability 50% of weight (judge claude-opus-5, status ok)

## Composite score: 83.6 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 97% |
| test_adequacy | automated | 25 | 62% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 100% |
| readability | judged | 8 | 75% |
| maintainability | judged | 7 | 50% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| calc_galaxy_denominator | 4 | 4 | 1.00 |
| persistence_schema_provenance | 5 | 5 | 1.00 |
| load_pair_counts_rejections | 7 | 8 | 0.88 |
| pair_fraction_core | 10 | 10 | 1.00 |
| merger_timescale_and_rate_conversion | 13 | 13 | 1.00 |
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
      "tests/test_hA.py::test_A20_load_pair_counts_bad_box",
      "tests/test_hA.py::test_C11_validation_result_keys"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "s PASSED                    [ 49%]\ntests/test_hA.py::test_B08_mass_bin_by_assertion PASSED                  [ 50%]\ntests/test_hA.py::test_B09_timescale_rejections PASSED                   [ 52%]\ntests/test_hA.py::test_B10_timescale_rejects_string_and_array PASSED     [ 54%]\ntests/test_hA.py::test_B11_merger_rate_scalar_rejections PASSED          [ 55%]\ntests/test_hA.py::test_B12_merger_rate_array_rejections PASSED           [ 57%]\ntests/test_hA.py::test_B13_merger_rate_rejects_string_box_by_assertion PASSED [ 59%]\ntests/test_hA.py::test_B14_docstring_wording PASSED                      [ 60%]\ntests/test_hA.py::test_B15_rejection_messages_name_the_reason PASSED     [ 62%]\ntests/test_hA.py::test_C01_exact_power_law PASSED                        [ 63%]\ntests/test_hA.py::test_C02_provably_weighted PASSED                      [ 65%]\ntests/test_hA.py::test_C03_two_point_slope_err_pinned PASSED             [ 67%]\ntests/test_hA.py::test_C04_two_usable_with_exclusions_finite PASSED      [ 68%]\ntests/test_hA.py::test_C05_fewer_than_two_usable PASSED                  [ 70%]\ntests/test_hA.py::test_C06_single_redshift_returns_nan PASSED            [ 72%]\ntests/test_hA.py::test_C07_malformed_redshifts_and_rank PASSED           [ 73%]\ntests/test_hA.py::test_C08_check_slope_consistency PASSED                [ 75%]\ntests/test_hA.py::test_C09_collapsed_predictor PASSED                    [ 77%]\ntests/test_hA.py::test_C10_y_centring_numerical_stability PASSED         [ 78%]\ntests/test_hA.py::test_C11_validation_result_keys FAILED                 [ 80%]\ntests/test_hA.py::test_C12_validation_rejects_malformed_stored_redshift_before_fit PASSED [ 81%]\ntests/test_hA.py::test_C13_validation_prints_insufficient_data PASSED    [ 83%]\ntests/test_hA.py::test_C14_mass_bin_is_index_not_string PASSED           [ 85%]\ntests/test_hA.py::test_C15_consistent_is_python_bool_or_none PASSED      [ 86%]\ntests/test_hB.py::test_E01_slice1_additive_schema PASSED                 [ 88%]\ntests/test_hB.py::test_E02_denominator_from_full_catalog PASSED          [ 90%]\ntests/test_hB.py::test_E03_box_size_from_catalog_not_config PASSED       [ 91%]\ntests/test_hB.py::test_E04_per_file_box_size_used PASSED                 [ 93%]\ntests/test_hB.py::test_E05_preflight_atomicity_sha256 PASSED             [ 95%]\ntests/test_hB.py::test_E06_output_schema PASSED                          [ 96%]\ntests/test_hB.py::test_E07_end_to_end_science PASSED                     [ 98%]\ntests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha PASSED [100%]\n\n=================================== FAILURES ===================================\n______________________ test_A20_load_pair_counts_bad_box _______________________\ntests/test_hA.py:219: in test_A20_load_pair_counts_bad_box\n    assert r == \"assert\", (bad, r)\nE   AssertionError: (0.0, None)\nE   assert None == 'assert'\n_______________________ test_C11_validation_result_keys ________________________\ntests/test_hA.py:589: in test_C11_validation_result_keys\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:557: in _parse_bin_line\n    assert all((mass, slope, slope_err, expected, excluded, status)), line\nE   AssertionError:   bin 0 [8.0, 8.5): slope=+1.0000 +/- 0.0966 expected=+1.000 n_excluded=0 -> consistent\nE   assert False\nE    +  where False = all((<re.Match object; span=(8, 18), match='[8.0, 8.5)'>, <re.Match object; span=(20, 33), match='slope=+1.0000'>, <re.Match object; span=(34, 44), match='+/- 0.0966'>, <re.Match object; span=(45, 60), match='expected=+1.000'>, <re.Match object; span=(61, 73), match='n_excluded=0'>, None))\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A20_load_pair_counts_bad_box - AssertionError: ...\nFAILED tests/test_hA.py::test_C11_validation_result_keys - AssertionError:   ...\n========================= 2 failed, 59 passed in 1.92s =========================\n",
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
        "passed": 7,
        "collected": 8,
        "fraction": 0.875,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_A20_load_pair_counts_bad_box"
        ]
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
      "tests/test_merger_rate.py::TestCheckSlope::test_n_sigma_validation",
      "tests/test_merger_rate.py::TestCheckSlope::test_nonfinite_or_nonpos",
      "tests/test_merger_rate.py::TestCheckSlope::test_within_and_outside",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_array_rejections",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_known_value",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reduced_identity",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_scalar_rejections[kw0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_scalar_rejections[kw1]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_scalar_rejections[kw2]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_scalar_rejections[kw3]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_scalar_rejections[kw4]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_scalar_rejections[kw5]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_scalar_rejections[kw6]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_scalar_rejections[kw7]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_scalar_rejections[kw8]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_scalar_rejections[kw9]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_both_zero_valid",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_with_nonzero_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_sigma_exact",
      "tests/test_merger_rate.py::TestConfigKeys::test_keys_added_and_unchanged",
      "tests/test_merger_rate.py::TestCountGalaxies::test_box_size_from_catalog_not_config",
      "tests/test_merger_rate.py::TestCountGalaxies::test_exact_edge_exclusion",
      "tests/test_merger_rate.py::TestCountGalaxies::test_sum_equals_right_open_selected",
      "tests/test_merger_rate.py::TestExistingUntouched::test_pair_finder_unchanged",
      "tests/test_merger_rate.py::TestFit::test_exact_power_law",
      "tests/test_merger_rate.py::TestFit::test_exactly_two_usable_finite",
      "tests/test_merger_rate.py::TestFit::test_fewer_than_two_usable",
      "tests/test_merger_rate.py::TestFit::test_malformed_redshift_fails[z0]",
      "tests/test_merger_rate.py::TestFit::test_malformed_redshift_fails[z1]",
      "tests/test_merger_rate.py::TestFit::test_malformed_redshift_fails[z2]",
      "tests/test_merger_rate.py::TestFit::test_provably_weighted",
      "tests/test_merger_rate.py::TestFit::test_shape_violation_fails",
      "tests/test_merger_rate.py::TestFit::test_single_redshift_usable",
      "tests/test_merger_rate.py::TestFit::test_slope_err_hand_computed",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_accepts_np_scalar_box_size",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_hand_written_fixture",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_bad_box_size[(250+0j)]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_bad_box_size[-5.0]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_bad_box_size[250.0_0]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_bad_box_size[250.0_1]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_bad_box_size[True]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_bad_box_size[inf]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_bad_box_size[nan]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_bad_box_size[value7]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_attr",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_dataset",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_missing_file",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_out_of_range_index",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_wrong_length_n_gal",
      "tests/test_merger_rate.py::TestMergerTimescale::test_nondefault_values",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejections[kwargs0]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejections[kwargs10]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejections[kwargs1]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejections[kwargs2]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejections[kwargs3]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejections[kwargs4]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejections[kwargs5]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejections[kwargs6]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejections[kwargs7]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejections[kwargs8]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_rejections[kwargs9]",
      "tests/test_merger_rate.py::TestMergerTimescale::test_z0_equals_gyr0",
      "tests/test_merger_rate.py::TestPairFraction::test_exact_values",
      "tests/test_merger_rate.py::TestPairFraction::test_integer_inputs_accepted",
      "tests/test_merger_rate.py::TestPairFraction::test_pair_without_galaxies_rejected",
      "tests/test_merger_rate.py::TestPairFraction::test_rejections[args0]",
      "tests/test_merger_rate.py::TestPairFraction::test_rejections[args1]",
      "tests/test_merger_rate.py::TestPairFraction::test_rejections[args2]",
      "tests/test_merger_rate.py::TestPairFraction::test_rejections[args3]",
      "tests/test_merger_rate.py::TestPairFraction::test_rejections[args4]",
      "tests/test_merger_rate.py::TestPairFraction::test_zero_bin_exact",
      "tests/test_merger_rate.py::TestRunCalculation::test_accepts_np_scalar_redshift_attr",
      "tests/test_merger_rate.py::TestRunCalculation::test_bool_redshift_attr_rejected",
      "tests/test_merger_rate.py::TestRunCalculation::test_mass_bin_by_guard",
      "tests/test_merger_rate.py::TestRunCalculation::test_output_schema",
      "tests/test_merger_rate.py::TestRunCalculation::test_per_file_box_size_used",
      "tests/test_merger_rate.py::TestRunCalculation::test_preflight_gate_byte_for_byte_on_failure",
      "tests/test_merger_rate.py::TestRunCalculation::test_results_have_new_dataset_and_attr",
      "tests/test_merger_rate.py::TestValidationRun::test_end_to_end_consistent",
      "tests/test_merger_rate.py::TestValidationRun::test_expected_slope_tracks_alpha",
      "tests/test_merger_rate.py::TestValidationRun::test_insufficient_data_printed",
      "tests/test_merger_rate.py::TestValidationRun::test_malformed_stored_redshift_fails",
      "tests/test_merger_rate.py::test_docstring_sentence_present",
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
      "tests/test_statistical.py::TestMaxwellMoments::test_mean[2]",
      "tests/test_statistical.py::TestMaxwellMoments::test_mean[3]",
      "tests/test_statistical.py::TestMaxwellMoments::test_mean[4]",
      "tests/test_statistical.py::TestMaxwellMoments::test_mean[5]",
      "tests/test_statistical.py::TestMaxwellMoments::test_second_moment[0]",
      "tests/test_statistical.py::TestMaxwellMoments::test_second_moment[1]",
      "tests/test_statistical.py::TestMaxwellMoments::test_second_moment[2]",
      "tests/test_statistical.py::TestMaxwellMoments::test_second_moment[3]",
      "tests/test_statistical.py::TestMaxwellMoments::test_second_moment[4]",
      "tests/test_statistical.py::TestMaxwellMoments::test_second_moment[5]",
      "tests/test_statistical.py::TestMaxwellMoments::test_skewness_scale_invariant",
      "tests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[0]",
      "tests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[1]",
      "tests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[2]",
      "tests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[3]",
      "tests/test_statistical.py::TestRedshi
```
