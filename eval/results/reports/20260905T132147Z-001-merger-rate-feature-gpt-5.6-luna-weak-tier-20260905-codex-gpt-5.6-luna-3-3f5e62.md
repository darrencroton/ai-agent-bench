# Trial report: 20260905T132147Z-001-merger-rate-feature-gpt-5.6-luna-weak-tier-20260905-codex-gpt-5.6-luna-3-3f5e62

- Task: `001-merger-rate-feature`
- Model: `gpt-5.6-luna` (harness: codex)
- Model duration: 163.1s | venv setup: 24.1s | timed out: False | committed: False
- Changed files: src/calc.py, src/config.py, src/merger_rate.py
- Profile: `default` | Complete submission: False (missing: tests/test_merger_rate.py)
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 59.6 / 100

## Judged: readability 25% of weight, maintainability 25% of weight (judge claude-opus-5, status ok)

## Composite score: 54.4 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 95% |
| test_adequacy | automated | 25 | 0% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 25% |
| readability | judged | 8 | 25% |
| maintainability | judged | 7 | 25% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| calc_galaxy_denominator | 4 | 4 | 1.00 |
| persistence_schema_provenance | 5 | 5 | 1.00 |
| load_pair_counts_rejections | 7 | 8 | 0.88 |
| pair_fraction_core | 9 | 10 | 0.90 |
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
    "passed": 58,
    "failed": [
      "tests/test_hA.py::test_A17_load_pair_counts_missing_dataset",
      "tests/test_hA.py::test_B15_rejection_messages_name_the_reason",
      "tests/test_hA.py::test_C11_validation_result_keys"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "t_C05_fewer_than_two_usable PASSED                  [ 70%]\ntests/test_hA.py::test_C06_single_redshift_returns_nan PASSED            [ 72%]\ntests/test_hA.py::test_C07_malformed_redshifts_and_rank PASSED           [ 73%]\ntests/test_hA.py::test_C08_check_slope_consistency PASSED                [ 75%]\ntests/test_hA.py::test_C09_collapsed_predictor PASSED                    [ 77%]\ntests/test_hA.py::test_C10_y_centring_numerical_stability PASSED         [ 78%]\ntests/test_hA.py::test_C11_validation_result_keys FAILED                 [ 80%]\ntests/test_hA.py::test_C12_validation_rejects_malformed_stored_redshift_before_fit PASSED [ 81%]\ntests/test_hA.py::test_C13_validation_prints_insufficient_data PASSED    [ 83%]\ntests/test_hA.py::test_C14_mass_bin_is_index_not_string PASSED           [ 85%]\ntests/test_hA.py::test_C15_consistent_is_python_bool_or_none PASSED      [ 86%]\ntests/test_hB.py::test_E01_slice1_additive_schema PASSED                 [ 88%]\ntests/test_hB.py::test_E02_denominator_from_full_catalog PASSED          [ 90%]\ntests/test_hB.py::test_E03_box_size_from_catalog_not_config PASSED       [ 91%]\ntests/test_hB.py::test_E04_per_file_box_size_used PASSED                 [ 93%]\ntests/test_hB.py::test_E05_preflight_atomicity_sha256 PASSED             [ 95%]\ntests/test_hB.py::test_E06_output_schema PASSED                          [ 96%]\ntests/test_hB.py::test_E07_end_to_end_science PASSED                     [ 98%]\ntests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha PASSED [100%]\n\n=================================== FAILURES ===================================\n__________________ test_A17_load_pair_counts_missing_dataset ___________________\ntests/test_hA.py:199: in test_A17_load_pair_counts_missing_dataset\n    assert_rejects_with(\"mass_bin\", MR._load_pair_counts, 2.0, c2)\ntests/test_hA.py:57: in assert_rejects_with\n    with pytest.raises(AssertionError, match=pattern):\n         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE   AssertionError: Regex pattern did not match.\nE     Expected regex: 'mass_bin'\nE     Actual message: 'missing required dataset in /private/var/folders/mw/53tcw7cn0ng7lm248lq60tvhlhmg9l/T/pytest-of-dcroton/pytest-10377/test_A17_load_pair_counts_miss0/mass-bin/pairs_z2.0.hdf5'\n_________________ test_B15_rejection_messages_name_the_reason __________________\ntests/test_hA.py:407: in test_B15_rejection_messages_name_the_reason\n    assert_rejects_with(\"n_pairs\", MR.compute_pair_fraction,\ntests/test_hA.py:57: in assert_rejects_with\n    with pytest.raises(AssertionError, match=pattern):\n         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE   AssertionError: Regex pattern did not match.\nE     Expected regex: 'n_pairs'\nE     Actual message: 'positive pair counts require positive galaxy counts'\n_______________________ test_C11_validation_result_keys ________________________\ntests/test_hA.py:589: in test_C11_validation_result_keys\n    _, mass_range, excluded = _parse_bin_line(buf.getvalue(), b)\n                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\ntests/test_hA.py:557: in _parse_bin_line\n    assert all((mass, slope, slope_err, expected, excluded, status)), line\nE   AssertionError: bin 0 [8.0, 8.5) slope=1.0 +/- 0.09660176804140658 expected=1.0 n_excluded=0 status=True\nE   assert False\nE    +  where False = all((<re.Match object; span=(6, 16), match='[8.0, 8.5)'>, <re.Match object; span=(17, 26), match='slope=1.0'>, <re.Match object; span=(27, 50), match='+/- 0.09660176804140658'>, <re.Match object; span=(51, 63), match='expected=1.0'>, <re.Match object; span=(64, 76), match='n_excluded=0'>, None))\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A17_load_pair_counts_missing_dataset - Assertio...\nFAILED tests/test_hA.py::test_B15_rejection_messages_name_the_reason - Assert...\nFAILED tests/test_hA.py::test_C11_validation_result_keys - AssertionError: bi...\n========================= 3 failed, 58 passed in 1.81s =========================\n",
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
          "tests/test_hA.py::test_A17_load_pair_counts_missing_dataset"
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
    "tail": "y::TestMaxwellDistribution::test_ks_against_maxwell[3-5.0] PASSED [ 62%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-2.0] PASSED [ 63%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-3.0] PASSED [ 65%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-4.0] PASSED [ 66%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-5.0] PASSED [ 67%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-2.0] PASSED [ 68%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-3.0] PASSED [ 70%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-4.0] PASSED [ 71%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-5.0] PASSED [ 72%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[0] PASSED [ 73%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[1] PASSED [ 75%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[2] PASSED [ 76%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[3] PASSED [ 77%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[4] PASSED [ 78%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[5] PASSED [ 80%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[0] PASSED       [ 81%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[1] PASSED       [ 82%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[2] PASSED       [ 83%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[3] PASSED       [ 85%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[4] PASSED       [ 86%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[5] PASSED       [ 87%]\ntests/test_statistical.py::TestMaxwellMoments::test_skewness_scale_invariant PASSED [ 88%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[0] PASSED [ 90%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[1] PASSED [ 91%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[2] PASSED [ 92%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[3] PASSED [ 93%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[4] PASSED [ 95%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[5] PASSED [ 96%]\ntests/test_statistical.py::TestBulkVelocityCancellation::test_delta_v_independent_of_bulk_sigma PASSED [ 97%]\ntests/test_statistical.py::TestCrossBinKineticTheory::test_cross_bin_sigma_eff PASSED [ 98%]\ntests/test_statistical.py::TestMassRatioDistribution::test_mass_ratio_is_uniform PASSED [100%]\n\n============================== 80 passed in 1.97s ==============================\n"
  },
  "ships_red_outside_root": {
    "ships_red_outside_root": false,
    "returncode": 0,
    "timed_out": false,
    "tail": "........................................................................ [ 90%]\n........                                                                 [100%]\n80 passed in 1.95s\n"
  },
  "test_adequacy": {
    "note": "no baseline-passing test in the authorized test path; no mutation can earn credit",
    "total": 73,
    "killed": 0,
    "baseline_passed_count": 0,
    "credit_paths": [
      "tests/test_merger_rate.py"
    ],
    "baseline_passed_eligible": 0,
    "baseline_passed_total": 80
  },
  "scope_discipline": {
    "changed_files": [
      "src/calc.py",
      "src/config.py",
      "src/merger_rate.py"
    ],
    "violations": [],
    "integrity_violations": [],
    "out_of_scope": [],
    "frozen_touched": [],
    "penalty_per_file": 0.5
  },
  "hygiene": {
    "findings_count": 30,
    "findings": [
      "src/merger_rate.py:55:24: E702 Multiple statements on one line (semicolon)",
      "src/merger_rate.py:55:96: E702 Multiple statements on one line (semicolon)",
      "src/merger_rate.py:73:48: E702 Multiple statements on one line (semicolon)",
      "src/merger_rate.py:73:93: E702 Multiple statements on one line (semicolon)",
      "src/merger_rate.py:84:40: E702 Multiple statements on one line (semicolon)",
      "src/merger_rate.py:86:75: E702 Multiple statements on one line (semicolon)",
      "src/merger_rate.py:87:41: E702 Multiple statements on one line (semicolon)",
      "src/merger_rate.py:90:56: E702 Multiple statements on one line (semicolon)",
      "src/merger_rate.py:93:66: E702 Multiple statements on one line (semicolon)",
      "src/merger_rate.py:100:62: E702 Multiple statements on one line (semicolon)",
      "src/merger_rate.py:102:64: E702 Multiple statements on one line (semicolon)",
      "src/merger_rate.py:102:90: E702 Multiple statements on one line (semicolon)",
      "src/merger_rate.py:102:116: E702 Multiple statements on one line (semicolon)",
      "src/merger_rate.py:102:139: E702 Multiple statements on one line (semicolon)",
      "src/merger_rate.py:103:43: E701 Multiple statements on one line (colon)",
      "src/merger_rate.py:104:18: E702 Multiple statements on one line (semicolon)",
      "src/merger_rate.py:104:32: E702 Multiple statements on one line (semicolon)",
      "src/merger_rate.py:104:50: E702 Multiple statements on one line (semicolon)",
      "src/merger_rate.py:104:69: E702 Multiple statements on one line (semicolon)",
      "src/merger_rate.py:104:78: E702 Multiple statements on one line (semicolon)",
      "src/merger_rate.py:104:99: E702 Multiple statements on one line (semicolon)",
      "src/merger_rate.py:104:131: E702 Multiple statements on one line (semicolon)",
      "src/merger_rate.py:104:154: E702 Multiple statements on one line (semicolon)",
      "src/merger_rate.py:112:30: E701 Multiple statements on one line (colon)",
      "src/merger_rate.py:113:99: E702 Multiple statements on one line (semicolon)",
      "src/merger_rate.py:113:143: E702 Multiple statements on one line (semicolon)",
      "src/merger_rate.py:113:154: E702 Multiple statements on one line (semicolon)",
      "src/merger_rate.py:115:51: E702 Multiple statements on one line (semicolon)",
      "src/merger_rate.py:115:127: E702 Multiple statements on one line (
```
