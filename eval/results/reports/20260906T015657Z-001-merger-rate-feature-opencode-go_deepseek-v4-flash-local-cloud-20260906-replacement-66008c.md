# Trial report: 20260906T015657Z-001-merger-rate-feature-opencode-go_deepseek-v4-flash-local-cloud-20260906-replacement-66008c

- Task: `001-merger-rate-feature`
- Model: `opencode-go/deepseek-v4-flash` (harness: opencode)
- Model duration: 1192.0s | venv setup: 29.2s | timed out: False | committed: False
- Changed files: src/calc.py, src/config.py, src/merger_rate.py, tests/test_merger_rate.py
- Profile: `default` | Complete submission: True
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 97.5 / 100

## Judged: readability 75% of weight, maintainability 50% of weight (judge claude-opus-5, status ok)

## Composite score: 92.3 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 97% |
| test_adequacy | automated | 25 | 96% |
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
| pair_fraction_core | 9 | 10 | 0.90 |
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
    "passed": 59,
    "failed": [
      "tests/test_hA.py::test_A17_load_pair_counts_missing_dataset",
      "tests/test_hA.py::test_B15_rejection_messages_name_the_reason"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "                      [ 60%]\ntests/test_hA.py::test_B15_rejection_messages_name_the_reason FAILED     [ 62%]\ntests/test_hA.py::test_C01_exact_power_law PASSED                        [ 63%]\ntests/test_hA.py::test_C02_provably_weighted PASSED                      [ 65%]\ntests/test_hA.py::test_C03_two_point_slope_err_pinned PASSED             [ 67%]\ntests/test_hA.py::test_C04_two_usable_with_exclusions_finite PASSED      [ 68%]\ntests/test_hA.py::test_C05_fewer_than_two_usable PASSED                  [ 70%]\ntests/test_hA.py::test_C06_single_redshift_returns_nan PASSED            [ 72%]\ntests/test_hA.py::test_C07_malformed_redshifts_and_rank PASSED           [ 73%]\ntests/test_hA.py::test_C08_check_slope_consistency PASSED                [ 75%]\ntests/test_hA.py::test_C09_collapsed_predictor PASSED                    [ 77%]\ntests/test_hA.py::test_C10_y_centring_numerical_stability PASSED         [ 78%]\ntests/test_hA.py::test_C11_validation_result_keys PASSED                 [ 80%]\ntests/test_hA.py::test_C12_validation_rejects_malformed_stored_redshift_before_fit PASSED [ 81%]\ntests/test_hA.py::test_C13_validation_prints_insufficient_data PASSED    [ 83%]\ntests/test_hA.py::test_C14_mass_bin_is_index_not_string PASSED           [ 85%]\ntests/test_hA.py::test_C15_consistent_is_python_bool_or_none PASSED      [ 86%]\ntests/test_hB.py::test_E01_slice1_additive_schema PASSED                 [ 88%]\ntests/test_hB.py::test_E02_denominator_from_full_catalog PASSED          [ 90%]\ntests/test_hB.py::test_E03_box_size_from_catalog_not_config PASSED       [ 91%]\ntests/test_hB.py::test_E04_per_file_box_size_used PASSED                 [ 93%]\ntests/test_hB.py::test_E05_preflight_atomicity_sha256 PASSED             [ 95%]\ntests/test_hB.py::test_E06_output_schema PASSED                          [ 96%]\ntests/test_hB.py::test_E07_end_to_end_science PASSED                     [ 98%]\ntests/test_hB.py::test_E09_expected_slope_tracks_nondefault_alpha PASSED [100%]\n\n=================================== FAILURES ===================================\n__________________ test_A17_load_pair_counts_missing_dataset ___________________\ntests/test_hA.py:199: in test_A17_load_pair_counts_missing_dataset\n    assert_rejects_with(\"mass_bin\", MR._load_pair_counts, 2.0, c2)\ntests/test_hA.py:58: in assert_rejects_with\n    fn(*args, **kwargs)\nsrc/merger_rate.py:99: in _load_pair_counts\n    mass_bin      = f[\"mass_bin\"][:]\n                    ^^^^^^^^^^^^^\n../../../../../venv/lib/python3.14/site-packages/h5py/_hl/group.py:407: in __getitem__\n    return self._get(name)\n           ^^^^^^^^^^^^^^^\nh5py/_objects.pyx:54: in h5py._objects.with_phil.wrapper\n    ???\nh5py/_objects.pyx:55: in h5py._objects.with_phil.wrapper\n    ???\n../../../../../venv/lib/python3.14/site-packages/h5py/_hl/group.py:421: in _get\n    oid = h5o.open(self.id, self._e(name), lapl=lapl)\n          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nh5py/_objects.pyx:54: in h5py._objects.with_phil.wrapper\n    ???\nh5py/_objects.pyx:55: in h5py._objects.with_phil.wrapper\n    ???\nh5py/h5o.pyx:255: in h5py.h5o.open\n    ???\nE   KeyError: \"Unable to synchronously open object (object 'mass_bin' doesn't exist)\"\n_________________ test_B15_rejection_messages_name_the_reason __________________\ntests/test_hA.py:401: in test_B15_rejection_messages_name_the_reason\n    assert_rejects_with(\"non-negative\", MR.compute_pair_fraction,\ntests/test_hA.py:57: in assert_rejects_with\n    with pytest.raises(AssertionError, match=pattern):\n         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nE   AssertionError: Regex pattern did not match.\nE     Expected regex: 'non-negative'\nE     Actual message: 'n_pairs contains negative counts'\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A17_load_pair_counts_missing_dataset - KeyError...\nFAILED tests/test_hA.py::test_B15_rejection_messages_name_the_reason - Assert...\n========================= 2 failed, 59 passed in 1.94s =========================\n",
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
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_asserts_on_invalid_n_sigma[-3.0]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_asserts_on_invalid_n_sigma[0.0]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_asserts_on_invalid_n_sigma[inf]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_asserts_on_invalid_n_sigma[nan]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_at_threshold_boundary",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_false_far_outside",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_nonfinite_returns_false[1.0-0.1-inf]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_nonfinite_returns_false[1.0-0.1-nan]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_nonfinite_returns_false[1.0-inf-1.0]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_nonfinite_returns_false[1.0-nan-1.0]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_nonfinite_returns_false[inf-0.1-1.0]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_nonfinite_returns_false[nan-0.1-1.0]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_nonpositive_slope_err_returns_false[-0.5]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_nonpositive_slope_err_returns_false[0.0]",
      "tests/test_merger_rate.py::TestCheckSlopeConsistency::test_true_within_range",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_accepts_merger_fraction_one",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_pinned_values",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_reduced_identity",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_arrays[f0-s0-ng0-shapes]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_arrays[f1-s1-ng1-1D]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_arrays[f2-s2-ng2-1D]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_arrays[f3-s3-ng3-negative]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_arrays[f4-s4-ng4-negative]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_arrays[f5-s5-ng5-negative]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_arrays[f6-s6-ng6-finite]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_arrays[f7-s7-ng7-finite]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_arrays[f8-s8-ng8-finite]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_arrays[f9-s9-ng9-integer-valued]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_box_size[(500+0j)]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_box_size[-1]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_box_size[0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_box_size[500.0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_box_size[True]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_box_size[bad_box6]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_box_size[bad_box7]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_box_size[inf]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_box_size[nan]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_merger_fraction[-0.1]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_merger_fraction[0.6]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_merger_fraction[0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_merger_fraction[1.5]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_merger_fraction[True]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_merger_fraction[bad_frac7]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_merger_fraction[bad_frac8]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_merger_fraction[inf]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_merger_fraction[nan]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_timescale[-2.2]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_timescale[0]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_timescale[2.2]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_timescale[True]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_timescale[bad_ts6]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_timescale[bad_ts7]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_timescale[inf]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_rejects_invalid_timescale[nan]",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_with_both_zero_valid",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_with_nonzero_f_pair_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_galaxies_with_nonzero_sigma_rejected",
      "tests/test_merger_rate.py::TestComputeMergerRate::test_zero_sigma_f_pair_gives_exact_zero",
      "tests/test_merger_rate.py::TestComputePairFraction::test_accepts_integer_dtypes_and_integer_valued_floats",
      "tests/test_merger_rate.py::TestComputePairFraction::test_asserts_pair_bin_has_galaxies",
      "tests/test_merger_rate.py::TestComputePairFraction::test_pinned_values",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_malformed_inputs[n_pairs0-n_galaxies0-shapes]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_malformed_inputs[n_pairs1-n_galaxies1-1D]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_malformed_inputs[n_pairs10-n_galaxies10-integer-valued]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_malformed_inputs[n_pairs2-n_galaxies2-1D]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_malformed_inputs[n_pairs3-n_galaxies3-1D]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_malformed_inputs[n_pairs4-n_galaxies4-negative]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_malformed_inputs[n_pairs5-n_galaxies5-negative]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_malformed_inputs[n_pairs6-n_galaxies6-finite]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_malformed_inputs[n_pairs7-n_galaxies7-finite]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_malformed_inputs[n_pairs8-n_galaxies8-finite]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_rejects_malformed_inputs[n_pairs9-n_galaxies9-integer-valued]",
      "tests/test_merger_rate.py::TestComputePairFraction::test_zero_counts_exactly_zero",
      "tests/test_merger_rate.py::TestComputePairFraction::test_zero_pair_bin_with_galaxies_exact_zero",
      "tests/test_merger_rate.py::TestConfigKeys::test_existing_keys_unchanged",
      "tests/test_merger_rate.py::TestConfigKeys::test_new_keys_present_with_expected_values",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_denominator_from_full_catalog",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_galaxy_at_log_mass_max_excluded",
      "tests/test_merger_rate.py::TestCountGalaxiesPerMassBin::test_pinned_edges_convention",
      "tests/test_merger_rate.py::TestDocstringConventions::test_poisson_convention_sentence",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_collapsed_predictor_many_points",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_collapsed_predictor_two_points",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_exact_powerlaw_recovered",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fewer_than_two_usable_points[rates0-rate_errs0-redshifts0-1]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fewer_than_two_usable_points[rates1-rate_errs1-redshifts1-2]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fewer_than_two_usable_points[rates2-rate_errs2-redshifts2-1]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fewer_than_two_usable_points[rates3-rate_errs3-redshifts3-1]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fewer_than_two_usable_points[rates4-rate_errs4-redshifts4-1]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fewer_than_two_usable_points[rates5-rate_errs5-redshifts5-1]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fewer_than_two_usable_points[rates6-rate_errs6-redshifts6-1]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_fewer_than_two_usable_points[rates7-rate_errs7-redshifts7-1]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_finite_two_point_fit",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_malformed_redshifts_raise[redshifts0]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_malformed_redshifts_raise[redshifts1]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_malformed_redshifts_raise[redshifts2]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_malformed_redshifts_raise[redshifts3]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_malformed_redshifts_raise[redshifts4]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_provably_weighted",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_shape_and_rank_violations_raise[rates0-rate_errs0-redshifts0]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_shape_and_rank_violations_raise[rates1-rate_errs1-redshifts1]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_shape_and_rank_violations_raise[rates2-rate_errs2-redshifts2]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_shape_and_rank_violations_raise[rates3-rate_errs3-redshifts3]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_shape_and_rank_violations_raise[rates4-rate_errs4-redshifts4]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_shape_and_rank_violations_raise[rates5-rate_errs5-redshifts5]",
      "tests/test_merger_rate.py::TestFitLogRateVsRedshift::test_slope_err_hand_computed",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_accepts_valid_box_size_scalar_forms[250.0]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_accepts_valid_box_size_scalar_forms[250]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_accepts_valid_box_size_scalar_forms[good_box2]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_accepts_valid_box_size_scalar_forms[good_box3]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_accepts_valid_box_size_scalar_forms[good_box4]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_handwritten_fixture",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_missing_attr",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_missing_dataset",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_missing_file",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size[(250+1j)]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size[-1]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size[0]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size[250.0]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size[250]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size[True]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size[bad_box8]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size[inf]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_invalid_box_size[nan]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_out_of_range_mass_bin[-2]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_out_of_range_mass_bin[6]",
      "tests/test_merger_rate.py::TestLoadPairCounts::test_rejects_out_of_range_mass_bin[7]",
      "tests/test_me
```
