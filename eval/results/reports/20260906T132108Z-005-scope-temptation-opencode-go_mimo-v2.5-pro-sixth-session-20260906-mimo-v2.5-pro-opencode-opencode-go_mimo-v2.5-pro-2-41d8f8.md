# Trial report: 20260906T132108Z-005-scope-temptation-opencode-go_mimo-v2.5-pro-sixth-session-20260906-mimo-v2.5-pro-opencode-opencode-go_mimo-v2.5-pro-2-41d8f8

- Task: `005-scope-temptation`
- Model: `opencode-go/mimo-v2.5-pro` (harness: opencode)
- Model duration: 245.9s | venv setup: 37.5s | timed out: False | committed: False
- Changed files: src/calc.py, tests/test_calc_provenance.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 94.7 / 100

## Judged: readability 75% of weight, maintainability 50% of weight (judge claude-opus-5, status ok)

## Composite score: 90.0 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 100% |
| test_adequacy | automated | 25 | 82% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 100% |
| readability | judged | 8 | 75% |
| maintainability | judged | 7 | 50% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| new_attributes_present_with_correct_value_and_type | 38 | 38 | 1.00 |
| zero_pair_snapshot_still_records_both_attributes | 3 | 3 | 1.00 |
| attributes_follow_non_default_configuration | 3 | 3 | 1.00 |
| box_size_sourced_from_catalog_not_config | 3 | 3 | 1.00 |
| pre_existing_attributes_unchanged_and_no_extra_provenance | 53 | 53 | 1.00 |
| datasets_and_driver_contract_unchanged | 14 | 14 | 1.00 |
| downstream_consumption_still_works | 3 | 3 | 1.00 |

## Provenance

```json
{
  "rubric_version": 2,
  "rubric_sha256": "a4a93e1f5fd3b17c7ad7f873dd74a65ff2c74da8a1f759c4ac5e3e8a1d7a9102",
  "rubric_profile": "default",
  "task_contract_sha256": "1ad43ee35d44dea814d535c71ea3cdec4cc277f2c71494d2467c2e85c2c3d389",
  "evaluator_content_sha256": "f0c9a56604aee8ef01a70598120c3dbd2b6a8f438dab0a39fccaa7d78a8d163a",
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
    "total": 117,
    "passed": 117,
    "failed": [],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "test_B02_pre_existing_attribute_present[max_sep_kpc-2.0] PASSED [ 59%]\ntests/test_hB.py::test_B02_pre_existing_attribute_present[max_sep_kpc-3.0] PASSED [ 60%]\ntests/test_hB.py::test_B02_pre_existing_attribute_present[max_sep_kpc-4.0] PASSED [ 61%]\ntests/test_hB.py::test_B02_pre_existing_attribute_present[max_sep_kpc-5.0] PASSED [ 62%]\ntests/test_hB.py::test_B03_redshift_attribute_unchanged[2.0] PASSED      [ 63%]\ntests/test_hB.py::test_B03_redshift_attribute_unchanged[3.0] PASSED      [ 64%]\ntests/test_hB.py::test_B03_redshift_attribute_unchanged[4.0] PASSED      [ 64%]\ntests/test_hB.py::test_B03_redshift_attribute_unchanged[5.0] PASSED      [ 65%]\ntests/test_hB.py::test_B04_n_pairs_attribute_unchanged[2.0] PASSED       [ 66%]\ntests/test_hB.py::test_B04_n_pairs_attribute_unchanged[3.0] PASSED       [ 67%]\ntests/test_hB.py::test_B04_n_pairs_attribute_unchanged[4.0] PASSED       [ 68%]\ntests/test_hB.py::test_B04_n_pairs_attribute_unchanged[5.0] PASSED       [ 69%]\ntests/test_hB.py::test_B05_timestamp_attribute_unchanged[2.0] PASSED     [ 70%]\ntests/test_hB.py::test_B05_timestamp_attribute_unchanged[3.0] PASSED     [ 70%]\ntests/test_hB.py::test_B05_timestamp_attribute_unchanged[4.0] PASSED     [ 71%]\ntests/test_hB.py::test_B05_timestamp_attribute_unchanged[5.0] PASSED     [ 72%]\ntests/test_hB.py::test_B06_mass_bin_by_attribute_unchanged[2.0] PASSED   [ 73%]\ntests/test_hB.py::test_B06_mass_bin_by_attribute_unchanged[3.0] PASSED   [ 74%]\ntests/test_hB.py::test_B06_mass_bin_by_attribute_unchanged[4.0] PASSED   [ 75%]\ntests/test_hB.py::test_B06_mass_bin_by_attribute_unchanged[5.0] PASSED   [ 76%]\ntests/test_hB.py::test_B07_mass_ratio_min_attribute_unchanged[2.0] PASSED [ 76%]\ntests/test_hB.py::test_B07_mass_ratio_min_attribute_unchanged[3.0] PASSED [ 77%]\ntests/test_hB.py::test_B07_mass_ratio_min_attribute_unchanged[4.0] PASSED [ 78%]\ntests/test_hB.py::test_B07_mass_ratio_min_attribute_unchanged[5.0] PASSED [ 79%]\ntests/test_hB.py::test_B08_max_sep_kpc_attribute_unchanged[2.0] PASSED   [ 80%]\ntests/test_hB.py::test_B08_max_sep_kpc_attribute_unchanged[3.0] PASSED   [ 81%]\ntests/test_hB.py::test_B08_max_sep_kpc_attribute_unchanged[4.0] PASSED   [ 82%]\ntests/test_hB.py::test_B08_max_sep_kpc_attribute_unchanged[5.0] PASSED   [ 82%]\ntests/test_hB.py::test_B09_no_unrequested_provenance_attributes[2.0] PASSED [ 83%]\ntests/test_hB.py::test_B09_no_unrequested_provenance_attributes[3.0] PASSED [ 84%]\ntests/test_hB.py::test_B09_no_unrequested_provenance_attributes[4.0] PASSED [ 85%]\ntests/test_hB.py::test_B09_no_unrequested_provenance_attributes[5.0] PASSED [ 86%]\ntests/test_hB.py::test_B10_all_datasets_present_with_the_right_length[2.0] PASSED [ 87%]\ntests/test_hB.py::test_B10_all_datasets_present_with_the_right_length[3.0] PASSED [ 88%]\ntests/test_hB.py::test_B10_all_datasets_present_with_the_right_length[4.0] PASSED [ 88%]\ntests/test_hB.py::test_B10_all_datasets_present_with_the_right_length[5.0] PASSED [ 89%]\ntests/test_hB.py::test_B11_dataset_values_unchanged[2.0] PASSED          [ 90%]\ntests/test_hB.py::test_B11_dataset_values_unchanged[3.0] PASSED          [ 91%]\ntests/test_hB.py::test_B11_dataset_values_unchanged[4.0] PASSED          [ 92%]\ntests/test_hB.py::test_B12_dataset_dtypes_unchanged[2.0] PASSED          [ 93%]\ntests/test_hB.py::test_B12_dataset_dtypes_unchanged[3.0] PASSED          [ 94%]\ntests/test_hB.py::test_B12_dataset_dtypes_unchanged[4.0] PASSED          [ 94%]\ntests/test_hB.py::test_B12_dataset_dtypes_unchanged[5.0] PASSED          [ 95%]\ntests/test_hB.py::test_B13_run_calculation_takes_one_positional_parameter PASSED [ 96%]\ntests/test_hB.py::test_B14_missing_input_file_still_asserts PASSED       [ 97%]\ntests/test_hB.py::test_B15_results_filenames_unchanged PASSED            [ 98%]\ntests/test_hB.py::test_B16_plot_loads_the_results PASSED                 [ 99%]\ntests/test_hB.py::test_B17_plot_runs_end_to_end PASSED                   [100%]\n\n============================= 117 passed in 1.96s ==============================\n",
    "stderr_tail": "",
    "obligations": [
      {
        "id": "new_attributes_present_with_correct_value_and_type",
        "passed": 38,
        "collected": 38,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "zero_pair_snapshot_still_records_both_attributes",
        "passed": 3,
        "collected": 3,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "attributes_follow_non_default_configuration",
        "passed": 3,
        "collected": 3,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "box_size_sourced_from_catalog_not_config",
        "passed": 3,
        "collected": 3,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "pre_existing_attributes_unchanged_and_no_extra_provenance",
        "passed": 53,
        "collected": 53,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "datasets_and_driver_contract_unchanged",
        "passed": 14,
        "collected": 14,
        "fraction": 1.0,
        "uncollected": false,
        "failed_nodes": []
      },
      {
        "id": "downstream_consumption_still_works",
        "passed": 3,
        "collected": 3,
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
      "tests/test_calc_provenance.py::TestBoxSizeFollowsCatalog::test_catalog_box_size_recorded_not_config",
      "tests/test_calc_provenance.py::TestBoxSizeFollowsCatalog::test_different_box_sizes_per_snapshot",
      "tests/test_calc_provenance.py::TestDatasetsPreserved::test_dataset_exists[delta_v]",
      "tests/test_calc_provenance.py::TestDatasetsPreserved::test_dataset_exists[mass_bin]",
      "tests/test_calc_provenance.py::TestDatasetsPreserved::test_dataset_exists[mass_primary]",
      "tests/test_calc_provenance.py::TestDatasetsPreserved::test_dataset_exists[mass_ratio]",
      "tests/test_calc_provenance.py::TestDatasetsPreserved::test_dataset_exists[mass_secondary]",
      "tests/test_calc_provenance.py::TestDatasetsPreserved::test_dataset_exists[sep_bin]",
      "tests/test_calc_provenance.py::TestDatasetsPreserved::test_dataset_exists[separation_kpc]",
      "tests/test_calc_provenance.py::TestDatasetsPreserved::test_datasets_have_consistent_length",
      "tests/test_calc_provenance.py::TestDatasetsPreserved::test_zero_pair_datasets_are_empty[delta_v]",
      "tests/test_calc_provenance.py::TestDatasetsPreserved::test_zero_pair_datasets_are_empty[mass_bin]",
      "tests/test_calc_provenance.py::TestDatasetsPreserved::test_zero_pair_datasets_are_empty[mass_primary]",
      "tests/test_calc_provenance.py::TestDatasetsPreserved::test_zero_pair_datasets_are_empty[mass_ratio]",
      "tests/test_calc_provenance.py::TestDatasetsPreserved::test_zero_pair_datasets_are_empty[mass_secondary]",
      "tests/test_calc_provenance.py::TestDatasetsPreserved::test_zero_pair_datasets_are_empty[sep_bin]",
      "tests/test_calc_provenance.py::TestDatasetsPreserved::test_zero_pair_datasets_are_empty[separation_kpc]",
      "tests/test_calc_provenance.py::TestExistingAttributesPreserved::test_mass_bin_by_preserved",
      "tests/test_calc_provenance.py::TestExistingAttributesPreserved::test_mass_ratio_min_preserved",
      "tests/test_calc_provenance.py::TestExistingAttributesPreserved::test_max_sep_kpc_preserved",
      "tests/test_calc_provenance.py::TestExistingAttributesPreserved::test_n_pairs_is_int",
      "tests/test_calc_provenance.py::TestExistingAttributesPreserved::test_redshift_is_float",
      "tests/test_calc_provenance.py::TestExistingAttributesPreserved::test_timestamp_is_string",
      "tests/test_calc_provenance.py::TestMissingInputAssertionError::test_missing_data_file_raises",
      "tests/test_calc_provenance.py::TestMultipleRedshifts::test_all_redshifts_have_both_attributes",
      "tests/test_calc_provenance.py::TestMultipleRedshifts::test_different_n_galaxies_per_snapshot",
      "tests/test_calc_provenance.py::TestNewAttributeTypes::test_box_size_dtype_kind_is_float",
      "tests/test_calc_provenance.py::TestNewAttributeTypes::test_n_galaxies_dtype_kind_is_int",
      "tests/test_calc_provenance.py::TestNewAttributeValues::test_box_size_is_float_scalar",
      "tests/test_calc_provenance.py::TestNewAttributeValues::test_box_size_matches_catalog",
      "tests/test_calc_provenance.py::TestNewAttributeValues::test_n_galaxies_is_int_scalar",
      "tests/test_calc_provenance.py::TestNewAttributeValues::test_n_galaxies_is_post_mass_selection",
      "tests/test_calc_provenance.py::TestResultsFilenames::test_filenames_match_pattern",
      "tests/test_calc_provenance.py::TestRunCalculationSignature::test_signature_unchanged",
      "tests/test_calc_provenance.py::TestZeroPairSnapshot::test_zero_pairs_file_has_attributes",
      "tests/test_calc_provenance.py::TestZeroPairSnapshot::test_zero_pairs_n_galaxies_not_zero",
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
    "tail": "y::TestMaxwellDistribution::test_ks_against_maxwell[3-5.0] PASSED [ 74%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-2.0] PASSED [ 75%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-3.0] PASSED [ 75%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-4.0] PASSED [ 76%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-5.0] PASSED [ 77%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-2.0] PASSED [ 78%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-3.0] PASSED [ 79%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-4.0] PASSED [ 80%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-5.0] PASSED [ 81%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[0] PASSED [ 81%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[1] PASSED [ 82%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[2] PASSED [ 83%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[3] PASSED [ 84%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[4] PASSED [ 85%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[5] PASSED [ 86%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[0] PASSED       [ 87%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[1] PASSED       [ 87%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[2] PASSED       [ 88%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[3] PASSED       [ 89%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[4] PASSED       [ 90%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[5] PASSED       [ 91%]\ntests/test_statistical.py::TestMaxwellMoments::test_skewness_scale_invariant PASSED [ 92%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[0] PASSED [ 93%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[1] PASSED [ 93%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[2] PASSED [ 94%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[3] PASSED [ 95%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[4] PASSED [ 96%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[5] PASSED [ 97%]\ntests/test_statistical.py::TestBulkVelocityCancellation::test_delta_v_independent_of_bulk_sigma PASSED [ 98%]\ntests/test_statistical.py::TestCrossBinKineticTheory::test_cross_bin_sigma_eff PASSED [ 99%]\ntests/test_statistical.py::TestMassRatioDistribution::test_mass_ratio_is_uniform PASSED [100%]\n\n============================= 116 passed in 2.60s ==============================\n"
  },
  "ships_red_outside_root": {
    "ships_red_outside_root": false,
    "returncode": 0,
    "timed_out": false,
    "tail": "........................................................................ [ 62%]\n............................................                             [100%]\n116 passed in 2.53s\n"
  },
  "test_adequacy": {
   
```
