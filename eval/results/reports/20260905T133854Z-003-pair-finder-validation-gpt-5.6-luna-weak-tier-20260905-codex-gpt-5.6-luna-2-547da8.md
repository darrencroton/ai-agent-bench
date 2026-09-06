# Trial report: 20260905T133854Z-003-pair-finder-validation-gpt-5.6-luna-weak-tier-20260905-codex-gpt-5.6-luna-2-547da8

- Task: `003-pair-finder-validation`
- Model: `gpt-5.6-luna` (harness: codex)
- Model duration: 112.2s | venv setup: 26.9s | timed out: False | committed: False
- Changed files: src/pair_finder.py
- Profile: `default` | Complete submission: False (missing: tests/test_pair_finder_validation.py)
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 70.3 / 100

## Judged: readability 75% of weight, maintainability 75% of weight (judge claude-opus-5, status ok)

## Composite score: 71.0 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 99% |
| test_adequacy | automated | 25 | 0% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 100% |
| readability | judged | 8 | 75% |
| maintainability | judged | 7 | 75% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| rejection_matrix | 197 | 205 | 0.96 |
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
    "total": 315,
    "passed": 307,
    "failed": [
      "tests/test_hA.py::test_A100_rejects[catalog_short_x]",
      "tests/test_hA.py::test_A100_rejects[catalog_short_y]",
      "tests/test_hA.py::test_A100_rejects[catalog_short_z]",
      "tests/test_hA.py::test_A100_rejects[catalog_short_vx]",
      "tests/test_hA.py::test_A100_rejects[catalog_short_vy]",
      "tests/test_hA.py::test_A100_rejects[catalog_short_vz]",
      "tests/test_hA.py::test_A100_rejects[catalog_short_log_stellar_mass]",
      "tests/test_hA.py::test_A100_rejects[mass_bin_width_value_10.0]"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "jects.<locals>.<genexpr> at 0x10b308f40>)\n______________________ test_A100_rejects[catalog_short_y] ______________________\ntests/test_hA.py:513: in test_A100_rejects\n    assert any(re.search(rf\"\\b{re.escape(n)}\\b\", message) for n in names), (\nE   AssertionError: message names none of ['x', 'y', 'z', 'vx', 'vy', 'vz', 'log_stellar_mass']: 'catalog arrays must be the same length'\nE   assert False\nE    +  where False = any(<generator object test_A100_rejects.<locals>.<genexpr> at 0x10be41740>)\n______________________ test_A100_rejects[catalog_short_z] ______________________\ntests/test_hA.py:513: in test_A100_rejects\n    assert any(re.search(rf\"\\b{re.escape(n)}\\b\", message) for n in names), (\nE   AssertionError: message names none of ['x', 'y', 'z', 'vx', 'vy', 'vz', 'log_stellar_mass']: 'catalog arrays must be the same length'\nE   assert False\nE    +  where False = any(<generator object test_A100_rejects.<locals>.<genexpr> at 0x10be41d40>)\n_____________________ test_A100_rejects[catalog_short_vx] ______________________\ntests/test_hA.py:513: in test_A100_rejects\n    assert any(re.search(rf\"\\b{re.escape(n)}\\b\", message) for n in names), (\nE   AssertionError: message names none of ['x', 'y', 'z', 'vx', 'vy', 'vz', 'log_stellar_mass']: 'catalog arrays must be the same length'\nE   assert False\nE    +  where False = any(<generator object test_A100_rejects.<locals>.<genexpr> at 0x10be42340>)\n_____________________ test_A100_rejects[catalog_short_vy] ______________________\ntests/test_hA.py:513: in test_A100_rejects\n    assert any(re.search(rf\"\\b{re.escape(n)}\\b\", message) for n in names), (\nE   AssertionError: message names none of ['x', 'y', 'z', 'vx', 'vy', 'vz', 'log_stellar_mass']: 'catalog arrays must be the same length'\nE   assert False\nE    +  where False = any(<generator object test_A100_rejects.<locals>.<genexpr> at 0x10be42a40>)\n_____________________ test_A100_rejects[catalog_short_vz] ______________________\ntests/test_hA.py:513: in test_A100_rejects\n    assert any(re.search(rf\"\\b{re.escape(n)}\\b\", message) for n in names), (\nE   AssertionError: message names none of ['x', 'y', 'z', 'vx', 'vy', 'vz', 'log_stellar_mass']: 'catalog arrays must be the same length'\nE   assert False\nE    +  where False = any(<generator object test_A100_rejects.<locals>.<genexpr> at 0x10be43240>)\n______________ test_A100_rejects[catalog_short_log_stellar_mass] _______________\ntests/test_hA.py:513: in test_A100_rejects\n    assert any(re.search(rf\"\\b{re.escape(n)}\\b\", message) for n in names), (\nE   AssertionError: message names none of ['x', 'y', 'z', 'vx', 'vy', 'vz', 'log_stellar_mass']: 'catalog arrays must be the same length'\nE   assert False\nE    +  where False = any(<generator object test_A100_rejects.<locals>.<genexpr> at 0x10be43540>)\n_________________ test_A100_rejects[mass_bin_width_value_10.0] _________________\ntests/test_hA.py:513: in test_A100_rejects\n    assert any(re.search(rf\"\\b{re.escape(n)}\\b\", message) for n in names), (\nE   AssertionError: message names none of ['mass_bin_width']: 'mass grid must define at least one mass bin'\nE   assert False\nE    +  where False = any(<generator object test_A100_rejects.<locals>.<genexpr> at 0x10be42a40>)\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A100_rejects[catalog_short_x] - AssertionError:...\nFAILED tests/test_hA.py::test_A100_rejects[catalog_short_y] - AssertionError:...\nFAILED tests/test_hA.py::test_A100_rejects[catalog_short_z] - AssertionError:...\nFAILED tests/test_hA.py::test_A100_rejects[catalog_short_vx] - AssertionError...\nFAILED tests/test_hA.py::test_A100_rejects[catalog_short_vy] - AssertionError...\nFAILED tests/test_hA.py::test_A100_rejects[catalog_short_vz] - AssertionError...\nFAILED tests/test_hA.py::test_A100_rejects[catalog_short_log_stellar_mass] - ...\nFAILED tests/test_hA.py::test_A100_rejects[mass_bin_width_value_10.0] - Asser...\n======================== 8 failed, 307 passed in 0.67s =========================\n",
    "stderr_tail": "",
    "obligations": [
      {
        "id": "rejection_matrix",
        "passed": 197,
        "collected": 205,
        "fraction": 0.9609756097560975,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_A100_rejects[catalog_short_log_stellar_mass]",
          "tests/test_hA.py::test_A100_rejects[catalog_short_vx]",
          "tests/test_hA.py::test_A100_rejects[catalog_short_vy]",
          "tests/test_hA.py::test_A100_rejects[catalog_short_vz]",
          "tests/test_hA.py::test_A100_rejects[catalog_short_x]",
          "tests/test_hA.py::test_A100_rejects[catalog_short_y]",
          "tests/test_hA.py::test_A100_rejects[catalog_short_z]",
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
    "tail": "y::TestMaxwellDistribution::test_ks_against_maxwell[3-5.0] PASSED [ 62%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-2.0] PASSED [ 63%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-3.0] PASSED [ 65%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-4.0] PASSED [ 66%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-5.0] PASSED [ 67%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-2.0] PASSED [ 68%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-3.0] PASSED [ 70%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-4.0] PASSED [ 71%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-5.0] PASSED [ 72%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[0] PASSED [ 73%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[1] PASSED [ 75%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[2] PASSED [ 76%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[3] PASSED [ 77%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[4] PASSED [ 78%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[5] PASSED [ 80%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[0] PASSED       [ 81%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[1] PASSED       [ 82%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[2] PASSED       [ 83%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[3] PASSED       [ 85%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[4] PASSED       [ 86%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[5] PASSED       [ 87%]\ntests/test_statistical.py::TestMaxwellMoments::test_skewness_scale_invariant PASSED [ 88%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[0] PASSED [ 90%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[1] PASSED [ 91%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[2] PASSED [ 92%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[3] PASSED [ 93%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[4] PASSED [ 95%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[5] PASSED [ 96%]\ntests/test_statistical.py::TestBulkVelocityCancellation::test_delta_v_independent_of_bulk_sigma PASSED [ 97%]\ntests/test_statistical.py::TestCrossBinKineticTheory::test_cross_bin_sigma_eff PASSED [ 98%]\ntests/test_statistical.py::TestMassRatioDistribution::test_mass_ratio_is_uniform PASSED [100%]\n\n============================== 80 passed in 1.89s ==============================\n"
  },
  "ships_red_outside_root": {
    "ships_red_outside_root": false,
    "returncode": 0,
    "timed_out": false,
    "tail": "........................................................................ [ 90%]\n........                                                                 [100%]\n80 passed in 1.88s\n"
  },
  "test_adequacy": {
    "note": "no baseline-passing test in the authorized test path; no mutation can earn credit",
    "total": 145,
    "killed": 0,
    "baseline_passed_count": 0,
    "credit_paths": [
      "tests/test_pair_finder_validation.py"
    ],
    "baseline_passed_eligible": 0,
    "baseline_passed_total": 80
  },
  "scope_discipline": {
    "changed_files": [
      "src/pair_finder.py"
    ],
    "violations": [],
    "integrity_violations": [],
    "out_of_scope": [],
    "frozen_touched": [],
    "penalty_per_file": 0.5
  },
  "hygiene": {
    "findings_count": 0,
    "findings": [],
    "all_findings_count": 0,
    "baseline_failing_nodes": 0
  },
  "judge": {
    "attempts": [
      {
        "attempt": 1,
        "returncode": 0,
        "raw": "xtWindow\":1000000,\"maxOutputTokens\":64000,\"thinkingTokens\":819,\"canonicalModel\":\"claude-opus-5\",\"provider\":\"firstParty\",\"costBasis\":\"list\"}},\"permission_denials\":[],\"terminal_reason\":\"completed\",\"fast_mode_state\":\"off\",\"fast_mode_disabled_reason\":\"sdk_opt_in_required\",\"subagent_stats\":{\"spawned\":0,\"requested\":{\"background\":0,\"foreground\":0,\"unset\":0},\"started_in_background\":0,\"max_depth\":0,\"spawned_by_subagents\":0,\"completed\":0,\"failed\":0,\"killed\":{\"parent\":0,\"user\":0,\"system\":0},\"refused\":{\"depth_limit\":0,\"concurrency_limit\":0,\"budget\":0},\"by_type\":{}},\"is_error\":false,\"num_turns\":1,\"subtype\":\"success\",\"api_error_status\":null,\"result\":\"{\\\"readability\\\": 4, \\\"maintainability\\\": 4, \\\"notes\\\": \\\"readability: `_validate_inputs` carries an accurate docstring and nearly every assert message names the offending field and expectation, and the module-level `_CATALOG_ARRAY_FIELDS`/`_CONFIG_SCALAR_FIELDS` tuples make the contract legible at a glance; marks off for the uninformative \\\\\\\"{name} has rejected dtype\\\\\\\" messages (says nothing about what is accepted) and two very long unwrapped assert lines (the log_mass_max and mass-grid checks), plus `_is_real_scalar` having no docstring for its non-obvious bool/np.bool_ exclusion. maintainability: field checks are driven by loops over the shared tuples and the scalar type test is factored into one reusable `_is_real_scalar` used at both box_size and config sites, with no dead code and a single call site in find_pairs; the knock is that `_validate_inputs` is one ~60-line function covering four distinct concerns (array fields, box geometry, config scalars, sep_bins) that would read better split into `_validate_catalog`/`_validate_config`, and the scalar+finite+float() sequence is repeated for box_size separately from the config loop.\\\"}\",\"ttft_ms\":12220,\"type\":\"result\",\"duration_ms\":17139,\"uuid\":\"562e6a2d-669e-42b3-ac62-fff45702160f\",\"ttft_stream_m
```
