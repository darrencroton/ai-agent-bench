# Trial report: 20260906T044643Z-002-pair-binning-convention-gpt-5.6-terra-medium-frontier-20260906-v2-codex-gpt-5.6-terra-3-d593c1

- Task: `002-pair-binning-convention`
- Model: `gpt-5.6-terra` (harness: codex)
- Model duration: 343.3s | venv setup: 25.5s | timed out: False | committed: False
- Changed files: src/config.py, src/pair_binning.py, tests/test_pair_binning.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 75.9 / 100

## Judged: readability 75% of weight, maintainability 75% of weight (judge claude-opus-5, status ok)

## Composite score: 75.8 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 100% |
| test_adequacy | automated | 25 | 18% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 100% |
| readability | judged | 8 | 75% |
| maintainability | judged | 7 | 75% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| api_surface_and_bin_geometry | 5 | 5 | 1.00 |
| denominator_galaxy_counting | 10 | 10 | 1.00 |
| pinned_pair_counts_under_every_supported_convention | 11 | 11 | 1.00 |
| additivity_and_exclusion_invariant_preservation | 14 | 14 | 1.00 |
| rejection_semantics_of_the_pure_counting_functions | 44 | 44 | 1.00 |
| pair_fraction_and_uncertainty | 4 | 4 | 1.00 |
| snapshot_loading_contract_and_provenance_rejections | 28 | 28 | 1.00 |
| config_tracking_through_loader_and_driver | 4 | 4 | 1.00 |
| persistence_schema_atomicity_and_console_reporting | 20 | 20 | 1.00 |

## Provenance

```json
{
  "rubric_version": 2,
  "rubric_sha256": "a4a93e1f5fd3b17c7ad7f873dd74a65ff2c74da8a1f759c4ac5e3e8a1d7a9102",
  "rubric_profile": "default",
  "task_contract_sha256": "5e163ed2ca2245525b6d1e59ecf201f4bdcd796f84a730de7f92dd6c14cf4826",
  "evaluator_content_sha256": "9de3dc7be290bae7ed25ba7c1df72cac8882f4528a284c3edd64ed15afa7c0ea",
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
    "total": 140,
    "passed": 140,
    "failed": [],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "y::test_B10_load_snapshot_counts_file_rejections[missing_data] PASSED [ 70%]\ntests/test_hB.py::test_B10_load_snapshot_counts_file_rejections[missing_results] PASSED [ 71%]\ntests/test_hB.py::test_B10_load_snapshot_counts_file_rejections[wrong_redshift] PASSED [ 72%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override0-redshift] PASSED [ 72%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override1-redshift] PASSED [ 73%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override2-redshift] PASSED [ 74%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override3-mass_ratio_min] PASSED [ 75%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override4-mass_ratio_min] PASSED [ 75%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override5-max_sep_kpc] PASSED [ 76%]\ntests/test_hB.py::test_B11_load_snapshot_counts_attr_rejections[override6-max_sep_kpc] PASSED [ 77%]\ntests/test_hB.py::test_B12a_load_snapshot_counts_missing_attr[redshift] PASSED [ 77%]\ntests/test_hB.py::test_B12a_load_snapshot_counts_missing_attr[mass_ratio_min] PASSED [ 78%]\ntests/test_hB.py::test_B12a_load_snapshot_counts_missing_attr[max_sep_kpc] PASSED [ 79%]\ntests/test_hB.py::test_B12b_load_snapshot_counts_missing_dataset[mass_primary] PASSED [ 80%]\ntests/test_hB.py::test_B12b_load_snapshot_counts_missing_dataset[mass_secondary] PASSED [ 80%]\ntests/test_hB.py::test_B12c_load_snapshot_counts_length_mismatch PASSED  [ 81%]\ntests/test_hB.py::test_B13_output_schema_on_mock PASSED                  [ 82%]\ntests/test_hB.py::test_B14_returned_dicts_match_persisted PASSED         [ 82%]\ntests/test_hB.py::test_B15_one_denominator_shared_by_every_convention PASSED [ 83%]\ntests/test_hB.py::test_B16_end_to_end_counts_recomputed_independently PASSED [ 84%]\ntests/test_hB.py::test_B17_conventions_config_tracks_through_the_driver PASSED [ 85%]\ntests/test_hB.py::test_B18_single_redshift_run PASSED                    [ 85%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[missing_data-<lambda>-None] PASSED [ 86%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[missing_results-<lambda>-None] PASSED [ 87%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_redshift-None-override2] PASSED [ 87%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_mass_ratio_min-None-override3] PASSED [ 88%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[bad_max_sep-None-override4] PASSED [ 89%]\ntests/test_hB.py::test_B19_preflight_leaves_sentinel_untouched[malformed_redshift-None-override5] PASSED [ 90%]\ntests/test_hB.py::test_B19b_preflight_checks_every_configured_redshift_before_writing PASSED [ 90%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad0] PASSED [ 91%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad1] PASSED [ 92%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad2] PASSED [ 92%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad3] PASSED [ 93%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[bad4] PASSED [ 94%]\ntests/test_hB.py::test_B20_invalid_conventions_leaves_sentinel_untouched[primary] PASSED [ 95%]\ntests/test_hB.py::test_B21_console_summary_fields PASSED                 [ 95%]\ntests/test_hB.py::test_B21b_console_line_selection_is_token_exact_not_substring PASSED [ 96%]\ntests/test_hB.py::test_B22_console_reports_not_checked_for_partial_convention_set PASSED [ 97%]\ntests/test_hB.py::test_B23_provenance_compared_against_config_not_defaults PASSED [ 97%]\ntests/test_hB.py::test_B24_additivity_false_from_check_propagates_everywhere PASSED [ 98%]\ntests/test_hB.py::test_B26_full_driver_run_on_nondefault_bin_grid PASSED [ 99%]\ntests/test_hB.py::test_B27_low_mass_ratio_pair_not_refiltered PASSED     [100%]\n\n============================= 140 passed in 1.98s ==============================\n",
    "stderr_tail": "",
    "obligations": [
      {
        "id": "api_surface_and_bin_geometry",
        "passed": 5,
        "collected": 5,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "denominator_galaxy_counting",
        "passed": 10,
        "collected": 10,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "pinned_pair_counts_under_every_supported_convention",
        "passed": 11,
        "collected": 11,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "additivity_and_exclusion_invariant_preservation",
        "passed": 14,
        "collected": 14,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "rejection_semantics_of_the_pure_counting_functions",
        "passed": 44,
        "collected": 44,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "pair_fraction_and_uncertainty",
        "passed": 4,
        "collected": 4,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "snapshot_loading_contract_and_provenance_rejections",
        "passed": 28,
        "collected": 28,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "config_tracking_through_loader_and_driver",
        "passed": 4,
        "collected": 4,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "persistence_schema_atomicity_and_console_reporting",
        "passed": 20,
        "collected": 20,
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
      "tests/test_pair_binning.py::test_pair_count_rejects_unsupported_conventions[None]",
      "tests/test_pair_binning.py::test_pair_count_rejects_unsupported_conventions[mean]",
      "tests/test_pair_binning.py::test_pair_count_rejects_unsupported_conventions[total]",
      "tests/test_pair_binning.py::test_pair_count_rejects_unsupported_conventions[unknown]",
      "tests/test_pair_binning.py::test_preflight_does_not_overwrite_existing_output",
      "tests/test_pair_binning.py::test_right_open_counts_incidence_and_errors",
      "tests/test_pair_binning.py::test_snapshot_loading_and_persistence_ignore_frozen_bin_assignment",
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
      "tests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[4]",
      "tests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[5]"
    ],
    "failed_nodes": [],
    "unparsable": false,
    "collect_timed_out": false,
    "tail": "y::TestMaxwellDistribution::test_ks_against_maxwell[3-5.0] PASSED [ 65%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-2.0] PASSED [ 66%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-3.0] PASSED [ 67%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-4.0] PASSED [ 68%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-5.0] PASSED [ 70%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-2.0] PASSED [ 71%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-3.0] PASSED [ 72%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-4.0] PASSED [ 73%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-5.0] PASSED [ 74%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[0] PASSED [ 75%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[1] PASSED [ 77%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[2] PASSED [ 78%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[3] PASSED [ 79%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[4] PASSED [ 80%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[5] PASSED [ 81%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[0] PASSED       [ 82%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[1] PASSED       [ 83%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[2] PASSED       [ 85%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[3] PASSED       [ 86%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[4] PASSED       [ 87%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[5] PASSED       [ 88%]\ntests/test_statistical.py::TestMaxwellMoments::test_skewness_scale_invariant PASSED [ 89%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[0] PASSED [ 90%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[1] PASSED [ 91%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[2] PASSED [ 93%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[3] PASSED [ 94%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[4] PASSED [ 95%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[5] PASSED [ 96%]\ntests/test_statistical.py::TestBulkVelocityCancellation::test_delta_v_independent_of_bulk_sigma PASSED [ 97%]\ntests/test_statistical.py::TestCrossBinKineticTheory::test_cross_bin_sigma_eff PASSED [ 98%]\ntests/test_statistical.py::TestMassRatioDistribution::test_mass_ratio_is_uniform PASSED [100%]\n\n============================== 87 passed in 2.06s ==============================\n"
  },
  "ships_red_outside_root": {
    "ships_red_outside_root": false,
    "returncode": 0,
    "timed_out": false,
    "tail": "........................................................................ [ 82%]\n...............                                                          [100%]\n87 passed in 2.06s\n"
  },
  "test_adequacy": {
    "per_mutation": {
      "M01_either_counts_once": "kill",
      "M02_either_is_primary": "kill",
      "M03_secondary_is_primary": "kill",
      "M04_denominator_from_pair_rows": "survive",
      "M05_count_gal_includes_upper_edge": "kill",
      "M06_count_gal_float_dtype": "survive",
      "M07_count_pairs_float_dtype": "survive",
      "M08_sigma_no_sqrt": "kill",
      "M09_zero_zero_pair_fraction_err_nan": "survive",
      "M09_zero_zero_pair_fraction_nan": "survive",
      "M10_pairfrac_n_galaxies_rank_validation": "survive",
      "M10_pairfrac_n_pairs_rank_validation": "survive",
      "M10_pairfrac_shape_validation": "survive",
      "M11_pairfrac_n_galaxies_finite_validation": "survive",
      "M11_pairfrac_n_galaxies_form_validation": "survive",
      "M11_pairfrac_n_galaxies_integer_validation": "survive",
      "M11_pairfrac_n_galaxies_nonnegative_validation": "survive",
      "M11_pairfrac_n_pairs_finite_validation": "survive",
      "M11_pairfrac_n_pairs_form_validation": "survive",
      "M11_pairfrac_n_pairs_integer_validation": "survive",
      "M11_pairfrac_n_pairs_nonnegative_validation": "survive",
      "M12_pairfrac_zero_denominator_validation": "survive",
      "M13_count_excluded_convention_nonstring_validation": "survive",
      "M13_count_excluded_convention_unsupported_validation": "survive",
      "M13_count_pairs_convention_nonstring_validation": "kill",
      "M13_count_pairs_convention_unsupported_validation": "kill",
      "M14_count_excluded_mass_order_validation": "survive",
      "M14_count_pairs_mass_order_validation": "survive",
      "M15_count_excluded_primary_rank_validation": "survive",
      "M15_count_excluded_secondary_rank_validation": "survive",
      "M15_count_excluded_shape_validation": "survive",
      "M15_count_pairs_primary_rank_validation": "survive",
      "M15_count_pairs_secondary_rank_validation": "survive",
      "M15_count_pairs_shape_validation": "survive",
      "M16_count_excluded_primary_nonfinite_validation": "survive",
      "M16_count_excluded_secondary_nonfinite_validation": "survive",
      "M16_count_galaxies_nonfinite_validation": "survive",
      "M16_count_pairs_primary_nonfinite_validation": "survive",
      "M16_count_pairs_secondary_nonfinite_validation": "survive",
      "M17_excluded_zero": "kill",
      "M18_excluded_either_is_primary": "survive",
      "M19_additivity_always_true": "survive",
      "M20_additivity_n_either_finite_validation": "survive",
      "M20_additivity_n_either_form_validation": "survive",
      "M20_additivity_n_either_integer
```
