# Corrected figure and table index — version2

All primary estimators reproduce historical metrics on the verified Linux reference runtime. XGBoost explanations use corrected native CSR inputs and full-test additivity checks. Items are ready for UHS review, not approved final submission. Fairness captions accompany CI and eligibility tables.

## Manuscript tables

| Item | Source file | Manuscript use | Status |
|---|---|---|---|
| Table 1 | `audit/cohort_flow.csv`, `modeling/day5_split_audit.csv`, `modeling/day11_13/day11_13_weighted_outcome_prevalence.csv` | Cohort, split, outcome prevalence | Frozen source; caption ready |
| Table 2 | `modeling/day20_22/day22_final_model_table.csv` | Overall unweighted and weighted performance | Ready for review |
| Table 3 | `modeling/day14_16_corrected_linux/day14_16_shap_global_importance.csv` | Population-weighted top constructs by outcome and model | Corrected native CSR release; full test |
| Table 4 | `modeling/day17_19/day17_19_disparity_summary.csv`, `modeling/day17_19/day17_19_subgroup_skipped.csv` | Subgroup disparity spans and excluded comparisons | Ready for review |
| Table 5 | `modeling/day20_22/day22_final_error_table.csv`, `modeling/day20_22/day22_robustness_summary.csv` | Error trade-offs and robustness | Ready for review |

## Manuscript figures

| Item | Source file | Proposed caption | Status |
|---|---|---|---|
| Figure 1 | `repair/figures/calibration_MEDNG.svg`, `repair/figures/calibration_MEDDL.svg` | Calibration of retained models on the locked test sets. Matching line samples identify the models. Curves are descriptive and do not establish clinical utility. | Legend corrected; historical values retained |
| Figure 2 | `modeling/day14_16_corrected_linux/figures/shap_global_constructs_MEDNG.svg`, `shap_global_constructs_MEDDL.svg` | Population-weighted global construct attribution for the locked estimators. SHAP magnitudes are model-output specific and not causal effects. | Ready for review |
| Figure 3 | `modeling/day17_19/figures/fairness_error_gap_MEDNG.svg`, `fairness_error_gap_MEDDL.svg` | Weighted subgroup FNR and FPR spans at the common locked threshold within each outcome-model pair. Gaps are descriptive and exclude groups that failed the stability gate. | Ready for review |
| Figure 4 | `modeling/day20_22/figures/day20_22_weighted_error_tradeoff.svg` | Weighted false-negative and false-positive trade-offs at the locked operating points. Thresholds are analytical rather than clinical cutoffs. | Ready for review |
| Supplementary Figure S1 | `modeling/day20_22/figures/day20_22_threshold_robustness.svg` | Recall and F1 under prespecified 0.8, 1.0, and 1.2 threshold multipliers. Test perturbations were not used for reselection. | Ready for review |

## Assembly rule

Generate venue-formatted tables from the listed versioned CSV files and compare every manuscript number against `docs/Claim_Traceability_V2.csv`.
