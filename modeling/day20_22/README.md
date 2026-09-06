# Day 20–22 aggregate error analysis, robustness, and initial code freeze

This folder closes Gate 4 of the four-week plan. It audits false negatives and false positives, tests prespecified robustness conditions, evaluates the original composite-outcome sensitivity, and freezes the computational state through Day 22.

## UHS review order

1. `day22_final_error_table.csv` — weighted overall FNR/FPR and model trade-offs.
2. `day22_robustness_summary.csv` — compact threshold, seed, and missingness sensitivity ranges.
3. `day20_22_composite_sensitivity_performance.csv` — separate `MEDNG OR MEDDL` sensitivity.
4. `figures/day20_22_weighted_error_tradeoff.svg` — overall weighted error trade-off.
5. `figures/day20_22_threshold_robustness.svg` — F1 under threshold ±20%.

Use `docs/Day20_22_Error_Robustness_Methodological_Rationale.md` for interpretation. The detailed CSVs are technical evidence and should not be copied into the manuscript without the stated limitations.

## Technical audit files

- `day20_22_error_summary.csv` — 2 outcomes × 3 models × weighted/unweighted overall error metrics.
- `day20_22_error_profile_by_group.csv` — aggregate eligible-group FNR/FPR and shares of all errors; not an individual targeting file.
- `day20_22_threshold_robustness.csv` — locked threshold multiplied by 0.8, 1.0, and 1.2; no reselection.
- `day20_22_seed_robustness.csv` — seeds 2026, 2037, and 2048; no best-seed selection.
- `day20_22_missingness_by_split.csv` — feature-level missingness across train, validation, and test.
- `day20_22_missingness_performance.csv` — test evaluation strata with and without cleaned-feature missingness; no refit.
- `day20_22_leakage_integrity_checklist.csv` — final leakage and lock checks.
- `day20_22_composite_validation_selection.csv` — validation-only probability/threshold selection for the composite sensitivity.
- `day20_22_composite_split_audit.csv` and `day20_22_composite_validation_role_audit.csv` — common-cohort integrity.
- `day20_22_config_log.json` — analysis contract and output manifest.
- `day22_code_freeze_manifest.csv` — SHA-256 snapshot of upstream locks and Day 20–22 computational outputs.

## Interpretation lock

- MEDNG and MEDDL retain the Day 8–10 models, Raw/Platt choice, and validation-selected thresholds.
- Threshold and seed sensitivity ranges are diagnostics, not a new selection cycle.
- The composite outcome is a separate sensitivity analysis using MEDNG hyperparameters without composite tuning; it does not replace independent MEDNG/MEDDL reporting.
- Weighted false-positive/false-negative counts are survey-weighted population mass, not literal numbers of sampled people.
- Group error profiles are descriptive aggregate signals. They must not be used for person-level micro-targeting or presented as proof of discrimination.
- No person-level identifier, prediction, or probability is saved in this folder.

