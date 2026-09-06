# Trial report: 20260905T134141Z-003-pair-finder-validation-gpt-5.6-luna-weak-tier-20260905-codex-gpt-5.6-luna-3-3fe5f8

- Task: `003-pair-finder-validation`
- Model: `gpt-5.6-luna` (harness: codex)
- Model duration: 118.0s | venv setup: 24.3s | timed out: False | committed: False
- Changed files: src/pair_finder.py
- Profile: `default` | Complete submission: False (missing: tests/test_pair_finder_validation.py)
- Gate status: not_applicable | Integrity violation: False

## Deterministic score: 70.5 / 100

## Judged: readability 75% of weight, maintainability 75% of weight (judge claude-opus-5, status ok)

## Composite score: 71.2 / 100

(scored 100% of profile weight)

## Category scores

| Category | Kind | Weight | Score |
|---|---|---|---|
| correctness | automated | 40 | 100% |
| test_adequacy | automated | 25 | 0% |
| scope_discipline | automated | 10 | 100% |
| hygiene | automated | 10 | 100% |
| readability | judged | 8 | 75% |
| maintainability | judged | 7 | 75% |

## Obligations

| Obligation | Passed | Collected | Fraction |
|---|---|---|---|
| rejection_matrix | 204 | 205 | 1.00 |
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
    "passed": 314,
    "failed": [
      "tests/test_hA.py::test_A100_rejects[order_sep_bins_count_before_finite]"
    ],
    "missing": [],
    "collect_timed_out": false,
    "timed_out": false,
    "raw_tail": "\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[primary] PASSED [ 88%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[secondary] PASSED [ 89%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[mean] PASSED [ 89%]\ntests/test_hA.py::test_A309_mass_bin_by_strategies_still_work[total] PASSED [ 89%]\ntests/test_hA.py::test_A310_signature_unchanged PASSED                   [ 90%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int16-ascending_dv] PASSED [ 90%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int16-descending_dv] PASSED [ 90%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint16-ascending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint16-descending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int32-ascending_dv] PASSED [ 91%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int32-descending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint32-ascending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[uint32-descending_dv] PASSED [ 92%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int64-ascending_dv] PASSED [ 93%]\ntests/test_hA.py::test_A314_integer_catalog_matches_its_float_twin[int64-descending_dv] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vx] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vy] PASSED [ 93%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int16-vz] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vx] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vy] PASSED [ 94%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint16-vz] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vx] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vy] PASSED [ 95%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[int8-vz] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vx] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vy] PASSED [ 96%]\ntests/test_hA.py::test_A315_integer_velocity_component_matches_float_twin[uint8-vz] PASSED [ 97%]\ntests/test_hA.py::test_A311_validation_precedes_no_pairs_return_nonfinite PASSED [ 97%]\ntests/test_hA.py::test_A312_validation_precedes_no_pairs_return_length PASSED [ 97%]\ntests/test_hA.py::test_A313_validation_precedes_mass_ratio_cut_return PASSED [ 98%]\ntests/test_hB.py::test_B00_pipeline_imports PASSED                       [ 98%]\ntests/test_hB.py::test_B01_driver_output_matches_the_analytic_expectation PASSED [ 98%]\ntests/test_hB.py::test_B02_nonfinite_position_on_disk_asserts PASSED     [ 99%]\ntests/test_hB.py::test_B03_position_outside_box_on_disk_asserts PASSED   [ 99%]\ntests/test_hB.py::test_B04_malformed_config_through_driver PASSED        [ 99%]\ntests/test_hB.py::test_B05_driver_honours_nondefault_config PASSED       [100%]\n\n=================================== FAILURES ===================================\n____________ test_A100_rejects[order_sep_bins_count_before_finite] _____________\ntests/test_hA.py:510: in test_A100_rejects\n    assert token in message, (\nE   AssertionError: message does not contain the required reason token 'at least 2': 'sep_bins must be finite'\nE   assert 'at least 2' in 'sep_bins must be finite'\n=========================== short test summary info ============================\nFAILED tests/test_hA.py::test_A100_rejects[order_sep_bins_count_before_finite]\n======================== 1 failed, 314 passed in 1.56s =========================\n",
    "stderr_tail": "",
    "obligations": [
      {
        "id": "rejection_matrix",
        "passed": 204,
        "collected": 205,
        "fraction": 0.9951219512195122,
        "uncollected": false,
        "failed_nodes": [
          "tests/test_hA.py::test_A100_rejects[order_sep_bins_count_before_finite]"
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
    "tail": "y::TestMaxwellDistribution::test_ks_against_maxwell[3-5.0] PASSED [ 62%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-2.0] PASSED [ 63%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-3.0] PASSED [ 65%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-4.0] PASSED [ 66%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[4-5.0] PASSED [ 67%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-2.0] PASSED [ 68%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-3.0] PASSED [ 70%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-4.0] PASSED [ 71%]\ntests/test_statistical.py::TestMaxwellDistribution::test_ks_against_maxwell[5-5.0] PASSED [ 72%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[0] PASSED [ 73%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[1] PASSED [ 75%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[2] PASSED [ 76%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[3] PASSED [ 77%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[4] PASSED [ 78%]\ntests/test_statistical.py::TestMaxwellMoments::test_second_moment[5] PASSED [ 80%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[0] PASSED       [ 81%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[1] PASSED       [ 82%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[2] PASSED       [ 83%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[3] PASSED       [ 85%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[4] PASSED       [ 86%]\ntests/test_statistical.py::TestMaxwellMoments::test_mean[5] PASSED       [ 87%]\ntests/test_statistical.py::TestMaxwellMoments::test_skewness_scale_invariant PASSED [ 88%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[0] PASSED [ 90%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[1] PASSED [ 91%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[2] PASSED [ 92%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[3] PASSED [ 93%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[4] PASSED [ 95%]\ntests/test_statistical.py::TestRedshiftIndependence::test_distributions_consistent_across_redshifts[5] PASSED [ 96%]\ntests/test_statistical.py::TestBulkVelocityCancellation::test_delta_v_independent_of_bulk_sigma PASSED [ 97%]\ntests/test_statistical.py::TestCrossBinKineticTheory::test_cross_bin_sigma_eff PASSED [ 98%]\ntests/test_statistical.py::TestMassRatioDistribution::test_mass_ratio_is_uniform PASSED [100%]\n\n============================== 80 passed in 2.07s ==============================\n"
  },
  "ships_red_outside_root": {
    "ships_red_outside_root": false,
    "returncode": 0,
    "timed_out": false,
    "tail": "........................................................................ [ 90%]\n........                                                                 [100%]\n80 passed in 1.92s\n"
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
        "raw": "tWindow\":200000,\"maxOutputTokens\":32000,\"thinkingTokens\":0,\"canonicalModel\":\"claude-haiku-4-5\",\"provider\":\"firstParty\",\"costBasis\":\"list\"},\"claude-opus-5\":{\"inputTokens\":2,\"outputTokens\":1283,\"cacheReadInputTokens\":10251,\"cacheCreationInputTokens\":9365,\"webSearchRequests\":0,\"costUSD\":0.1308605,\"contextWindow\":1000000,\"maxOutputTokens\":64000,\"thinkingTokens\":961,\"canonicalModel\":\"claude-opus-5\",\"provider\":\"firstParty\",\"costBasis\":\"list\"}},\"permission_denials\":[],\"terminal_reason\":\"completed\",\"fast_mode_state\":\"off\",\"fast_mode_disabled_reason\":\"sdk_opt_in_required\",\"subagent_stats\":{\"spawned\":0,\"requested\":{\"background\":0,\"foreground\":0,\"unset\":0},\"started_in_background\":0,\"max_depth\":0,\"spawned_by_subagents\":0,\"completed\":0,\"failed\":0,\"killed\":{\"parent\":0,\"user\":0,\"system\":0},\"refused\":{\"depth_limit\":0,\"concurrency_limit\":0,\"budget\":0},\"by_type\":{}},\"is_error\":false,\"num_turns\":1,\"subtype\":\"success\",\"api_error_status\":null,\"result\":\"{\\\"readability\\\": 4, \\\"maintainability\\\": 4, \\\"notes\\\": \\\"Readability: both helpers carry accurate one-line docstrings and the assertion messages are mostly self-describing, but `_validate_inputs`' docstring never says it returns a three-element `(arrays, box_size, validated_config)` tuple, messages like \\\\\\\"x has rejected dtype\\\\\\\" read oddly, and the `catalog = {**catalog, **arrays, \\\\\\\"box_size\\\\\\\": box_size}` re-binding in `find_pairs` gets no comment explaining why coerced values are folded back. Maintainability: `_real_scalar` is a genuine shared helper reused at ~7 call sites and nothing is dead, but `_validate_inputs` is one ~55-line function covering array, box, scalar-config and sep_bins concerns with no sub-helpers, and it re-derives `round((log_mass_max - log_mass_min) / mass_bin_width)` which already lives in `_mass_bin_edges`.\\\"}\",\"ttft_ms\":14482,\"type\":\"result\",\"duration_ms\":17773,\"uuid\":\"23b8af9b-5453-4ebd-ab81-1d8c075d6733\",\"ttft_stream_ms\":1073,\"time_to_request_ms\":21,\"first_content_frame_ms\":1816,\"queued_turn_count\":0}\n",
        "stderr_tail": "",
        "parsed": {
          "readability": 4,
          "maintainability": 4,
          "notes": "Readability: both helpers carry accurate one-line docstrings and the assertion messages are mostly self-describing, but `_validate_inputs`' docstring never says it returns a three-element `(arrays, box_size, validated_config)` tuple, messages like \"x has rejected dtype\" read oddly, and the `catalog = {**catalog, **arrays, \"box_size\": box_size}` re-binding in `find_pairs` gets no comment explaining why coerced values are folded back. Maintainability: `_real_scalar` is a genuine shared helper reused at ~7 call sites and nothing is dead, but `_validate_inputs` is one ~55-line function covering array, box, scalar-config and sep_bins concerns with no sub-helpers, and it re-deriv
```
