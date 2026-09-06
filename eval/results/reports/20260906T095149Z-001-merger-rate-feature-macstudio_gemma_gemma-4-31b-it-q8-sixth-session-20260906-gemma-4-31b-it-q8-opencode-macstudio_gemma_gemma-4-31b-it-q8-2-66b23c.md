# Trial report: 20260906T095149Z-001-merger-rate-feature-macstudio_gemma_gemma-4-31b-it-q8-sixth-session-20260906-gemma-4-31b-it-q8-opencode-macstudio_gemma_gemma-4-31b-it-q8-2-66b23c

- Task: `001-merger-rate-feature`
- Model: `macstudio/gemma/gemma-4-31b-it-q8` (harness: opencode)
- Model duration: 5194.1s | venv setup: 26.9s | timed out: False | committed: False
- Changed files: src/calc.py, src/config.py, src/merger_rate.py, tests/test_merger_rate.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 73.0 / 100

## Judged: readability 50% of weight, maintainability 25% of weight (judge claude-opus-5, status ok)

## Composite score: 67.8 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 85% |
| test_adequacy | automated | 25 | 36% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 91% |
| readability | judged | 8 | 50% |
| maintainability | judged | 7 | 25% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| calc_galaxy_denominator | 4 | 4 | 1.00 |
| persistence_schema_provenance | 5 | 5 | 1.00 |
| load_pair_counts_rejections | 6 | 8 | 0.75 |
| pair_fraction_core | 9 | 10 | 0.90 |
| merger_timescale_and_rate_conversion | 11 | 13 | 0.85 |
| run_merger_rate_calculation_pipeline | 3 | 4 | 0.75 |
| redshift_evolution_fit_and_consistency | 10 | 10 | 1.00 |
| validation_reporting_and_e2e | 4 | 7 | 0.57 |

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
    "passed": 52,
    "failed": [
      "tests/test_hA.py::test_A17_load_pair_counts_missing_dataset",
      "tests/test_hA.py::test_A22_load_pair_counts_rejects_non_numeric_scalar_box_attr",
      "tests/test_hA.py::test_B10_timescale_rejects_string_and_array",
      "tests/test_hA.py::test_B11_merger_rate_scalar_rejections",
      "tests/test_hA.py::test_B15_rejection_messages_name_the_reason",
      "tests/test_hA.py::test_C11_validation_result_keys",
      "tests/test_hB.py::test_E05_preflight_atomicity_sha256",
      "tests/test_hB.py::test_E07_end_to_end_science",
      "tests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": " pattern did not match.\nE     Expected regex: 'non-negative'\nE     Actual message: 'negative counts'\n_______________________ test_C11_validation_result_keys ________________________\ntests/test_hA.py:589: in test_C11_validation_result_keys\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:557: in _parse_bin_line\n    assert all((mass, slope, slope_err, expected, excluded, status)), line\nE   AssertionError: Bin 0 [8.00, 8.50): slope=1.0000 +/- 0.0966, expected=1.0000, n_excluded=0, status=PASS\nE   assert False\nE    +  where False = all((<re.Match object; span=(6, 18), match='[8.00, 8.50)'>, <re.Match object; span=(20, 32), match='slope=1.0000'>, <re.Match object; span=(33, 43), match='+/- 0.0966'>, <re.Match object; span=(45, 60), match='expected=1.0000'>, <re.Match object; span=(62, 74), match='n_excluded=0'>, None))\n_____________________ test_E05_preflight_atomicity_sha256 ______________________\ntests/test_hB.py:230: in test_E05_preflight_atomicity_sha256\n    assert not failures, failures\nE   AssertionError: [('z_complex', 'exception', None), ('z_complex', 'sentinel_modified', None)]\nE   assert not [('z_complex', 'exception', None), ('z_complex', 'sentinel_modified', None)]\n_________________________ test_E07_end_to_end_science __________________________\ntests/test_hB.py:294: in test_E07_end_to_end_science\n    assert d[\"consistent\"] is True, d\nE   AssertionError: {'mass_bin': 0, 'slope': np.float64(0.926776233510532), 'slope_err': np.float64(0.13946676597215996), 'intercept': np.float64(-6.319665846646199), ...}\nE   assert np.True_ is True\n_______________ test_E09_expected_slope_tracks_nondefault_alpha ________________\ntests/test_hB.py:322: in test_E09_expected_slope_tracks_nondefault_alpha\n    assert d[\"consistent\"] is True, d\nE   AssertionError: {'mass_bin': 0, 'slope': np.float64(0.6267762335105316), 'slope_err': np.float64(0.13946676597215998), 'intercept': np.float64(-6.3196658466462), ...}\nE   assert np.True_ is True\n=============================== warnings summary ===============================\ntests/test_hA.py::test_A22_load_pair_counts_rejects_non_numeric_scalar_box_attr\n  /Users/dcroton/Local/git-repos/ai-agent-bench/eval/results/tmp/worktrees/20260906T095149Z-001-merger-rate-feature-macstudio_gemma_gemma-4-31b-it-q8-sixth-session-20260906-gemma-4-31b-it-q8-opencode-macstudio_gemma_gemma-4-31b-it-q8-2-66b23c/tests/../src/merger_rate.py:49: ComplexWarning: Casting complex values to real discards the imaginary part\n    box_size_val = float(box_size)\n\ntests/test_hB.py::test_E05_preflight_atomicity_sha256\n  /Users/dcroton/Local/git-repos/ai-agent-bench/eval/results/tmp/worktrees/20260906T095149Z-001-merger-rate-feature-macstudio_gemma_gemma-4-31b-it-q8-sixth-session-20260906-gemma-4-31b-it-q8-opencode-macstudio_gemma_gemma-4-31b-it-q8-2-66b23c/tests/../src/merger_rate.py:216: ComplexWarning: Casting complex values to real discards the imaginary part\n    z_val = float(z_attr)\n\n-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A17_load_pair_counts_missing_dataset - Assertio...\nFAILED tests/test_hA.py::test_A22_load_pair_counts_rejects_non_numeric_scalar_box_attr\nFAILED tests/test_hA.py::test_B10_timescale_rejects_string_and_array - Assert...\nFAILED tests/test_hA.py::test_B11_merger_rate_scalar_rejections - AssertionEr...\nFAILED tests/test_hA.py::test_B15_rejection_messages_name_the_reason - Assert...\nFAILED tests/test_hA.py::test_C11_validation_result_keys - AssertionError: Bi...\nFAILED tests/test_hB.py::test_E05_preflight_atomicity_sha256 - AssertionError...\nFAILED tests/test_hB.py::test_E07_end_to_end_science - AssertionError: {'mass...\nFAILED tests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha - As...\n=================== 9 failed, 52 passed, 2 warnings in 1.86s ===================\n",
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
        "passed": 6,
        "collected": 8,
        "fraction": 0.75,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_A17_load_pair_counts_missing_dataset",
          "tests/test_hA.py::test_A22_load_pair_counts_rejects_non_numeric_scalar_box_attr"
        ]
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
          "tests/test_hA.py::test_B10_timescale_rejects_string_and_array",
          "tests/test_hA.py::test_B11_merger_rate_scalar_rejections"
        ]
      },
      {
        "id": "run_merger_rate_calculation_pipeline",
        "passed": 3,
        "collected": 4,
        "fraction": 0.75,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hB.py::test_E05_preflight_atomicity_sha256"
        ]
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
        "passed": 4,
        "collected": 7,
        "fraction": 0.5714285714285714,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_C11_validation_result_keys",
          "tests/test_hB.py::test_E07_end_to_end_science",
          "tests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha"
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
      "tests/test_merger_rate.py::test_check_slope_consistency",
      "tests/test_merger_rate.py::test_compute_merger_rate_rejections",
      "tests/test_merger_rate.py::test_compute_merger_rate_values",
      "tests/test_merger_rate.py::test_compute_merger_rate_zero_uncertainty",
      "tests/test_merger_rate.py::test_compute_pair_fraction_assertions",
      "tests/test_merger_rate.py::test_compute_pair_fraction_values",
      "tests/test_merger_rate.py::test_compute_pair_fraction_zero_bins",
      "tests/test_merger_rate.py::test_count_galaxies_per_mass_bin_edges",
      "tests/test_merger_rate.py::test_fit_log_rate_vs_redshift_insufficient_data",
      "tests/test_merger_rate.py::test_fit_log_rate_vs_redshift_malformed",
      "tests/test_merger_rate.py::test_fit_log_rate_vs_redshift_powerlaw",
      "tests/test_merger_rate.py::test_fit_log_rate_vs_redshift_two_points",
      "tests/test_merger_rate.py::test_fit_log_rate_vs_redshift_weighted",
      "tests/test_merger_rate.py::test_load_pair_counts_invalid_indices",
      "tests/test_merger_rate.py::test_load_pair_counts_rejections",
      "tests/test_merger_rate.py::test_load_pair_counts_valid",
      "tests/test_merger_rate.py::test_merger_timescale_gyr_rejections",
      "tests/test_merger_rate.py::test_merger_timescale_gyr_values",
      "tests/test_merger_rate.py::test_run_merger_rate_calculation_output",
      "tests/test_merger_rate.py::test_run_merger_rate_calculation_preflight",
      "tests/test_merger_rate.py::test_run_merger_rate_validation_malformed",
      "tests/test_merger_rate.py::test_run_merger_rate_validation_output",
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
    "tail": "y::TestMaxwellDistribution::test_ks_against_maxwell[3-5.0] PASSED [ 70%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-2.0] PASSED [ 71%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-3.0] PASSED [ 72%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-4.0] PASSED [ 73%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-5.0] PASSED [ 74%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-2.0] PASSED [ 75%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-3.0] PASSED [ 76%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-4.0] PASSED [ 77%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-5.0] PASSED [ 78%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[0] PASSED [ 79%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[1] PASSED [ 80%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[2] PASSED [ 81%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[3] PASSED [ 82%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[4] PASSED [ 83%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[5] PASSED [ 84%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[0] PASSED       [ 85%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[1] PASSED       [ 86%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[2] PASSED       [ 87%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[3] PASSED       [ 88%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[4] PASSED       [ 89%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[5] PASSED       [ 90%]\ntests/test_statistical.py::TestMaxwellMoments::test_skewness_scale_invariant PASSED [ 91%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[0] PASSED [ 92%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[1] PASSED [ 93%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[2] PASSED [ 94%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[3] PASSED [ 95%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[4] PASSED [ 96%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[5] PASSED [ 97%]\ntests/test_statistical.py::TestBulkVelocityCancellation::test_delta_v_independent_of_bulk_sigma PASSED [ 98%]\ntests/test_statistical.py::TestCrossBinKineticTheory::test_cross_bin_sigma_eff PASSED [ 99%]\ntests/test_statistical.py::TestMassRatioDistribution::test_mass_ratio_is_uniform PASSED [100%]\n\n============================= 102 passed in 2.22s ==============================\n"
  },
  "ships_red_outside_root": {
    "ships_red_outside_root": false,
    "returncode": 0,
    "timed_out": false,
    "tail": "........................................................................ [ 70%]\n..............................                                           [100%]\n102 passed in 2.04s\n"
  },
  "test_adequacy": {
    "per_mutation": {
      "M1_sigma_no_sqrt": "kill",
      "M2_timescale_sign": "kill",
      "M3_box_squared": "kill",
      "M4_config_box": "survive",
      "M5_slope_err_x2": "kill",
      "M6_consistency_bad_err": "kill",
      "M7_fabricate_fit": "kill",
      "M8a_pairfrac_n_pairs_rank_validation": "survive",
      "M8b_pairfrac_n_galaxies_rank_validation": "survive",
      "M8c_pairfrac_shape_equality_validation": "kill",
      "M8d_pairfrac_n_pairs_finite_validation": "kill",
      "M8e_pairfrac_n_pairs_nonnegative_validation": "kill",
```
