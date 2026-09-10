# Day 23–24 final figure and table index

## Manuscript tables

| Item | Source file | Manuscript use | Status |
|---|---|---|---|
| Table 1 | `audit/cohort_flow.csv`, `modeling/day5_split_audit.csv`, `modeling/day11_13/day11_13_weighted_outcome_prevalence.csv` | Cohort, split, outcome prevalence | Frozen source; caption ready |
| Table 2 | `modeling/day20_22/day22_final_model_table.csv` | Overall unweighted and weighted performance | Final |
| Table 3 | `modeling/day14_16/day14_16_shap_global_importance.csv` | Population-weighted top constructs by outcome and model | Final after controlled chronic-burden label correction |
| Table 4 | `modeling/day17_19/day17_19_disparity_summary.csv`, `modeling/day17_19/day17_19_subgroup_skipped.csv` | Subgroup disparity spans and excluded comparisons | Final |
| Table 5 | `modeling/day20_22/day22_final_error_table.csv`, `modeling/day20_22/day22_robustness_summary.csv` | Error trade-offs and robustness | Final |

## Manuscript figures

| Item | Source file | Proposed caption | Status |
|---|---|---|---|
| Figure 1 | `modeling/day8_10/uhs_extensions/calibration_MEDNG.svg`, `calibration_MEDDL.svg` | Calibration of retained models on the locked test sets. Curves are descriptive and do not establish clinical utility. | Final |
| Figure 2 | `modeling/day14_16/figures/shap_global_constructs_MEDNG.svg`, `shap_global_constructs_MEDDL.svg` | Population-weighted global construct attribution for the locked estimators. SHAP magnitudes are model-output specific and not causal effects. | Final |
| Figure 3 | `modeling/day17_19/figures/fairness_error_gap_MEDNG.svg`, `fairness_error_gap_MEDDL.svg` | Weighted subgroup FNR and FPR spans at the common locked threshold within each outcome-model pair. Gaps are descriptive and exclude groups that failed the stability gate. | Final |
| Figure 4 | `modeling/day20_22/figures/day20_22_weighted_error_tradeoff.svg` | Weighted false-negative and false-positive trade-offs at the locked operating points. Thresholds are analytical rather than clinical cutoffs. | Final |
| Supplementary Figure S1 | `modeling/day20_22/figures/day20_22_threshold_robustness.svg` | Recall and F1 under prespecified 0.8, 1.0, and 1.2 threshold multipliers. Test perturbations were not used for reselection. | Final |

## Assembly rule

Do not copy values manually into a new spreadsheet. During Day 25–26, generate venue-formatted tables from the listed frozen CSV files and compare every manuscript number against `docs/Day23_24_Claim_Traceability.csv`.
