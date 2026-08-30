# Day 8–10 addendum — UHS-requested uncertainty, calibration plot & Decision Curve Analysis

## 1. Trigger
After the locked Day 8–10 evaluation, UHS requested three additional evidence components before the group discusses which model is most suitable for the research direction:
1. 95% CI for AUROC/AUPRC;
2. calibration plots;
3. Decision Curve Analysis (DCA).

UHS plans to use these outputs to prepare a Metric Interpretation Guide and model-specific review before group discussion.

## 2. Methodological lock
This addendum **does not re-open model selection**. The already locked Day 8–10 choices are retained:
- same deterministic Day-5 `HHX` split;
- same 12 main constructs;
- same best RF/XGBoost configurations;
- LR fixed at `C=1.0`;
- same validation-fitted Platt procedure;
- same Raw/Platt decision;
- same F1 operating thresholds.

The test set is used only to add evaluation evidence.

## 3. 95% CI
Method: 1,000 nonparametric **paired bootstrap** resamples of individual rows in each locked test cohort. The same bootstrap resample is applied to LR/RF/XGBoost within an outcome. Percentile 2.5th and 97.5th percentiles form the 95% CI.

This is a predictive-performance CI, **not** a complex-survey design-based CI. `WTFA_A/PPSU/PSTRAT` are not used in this extension.

### MEDNG
- LR AUROC 0.7942 [0.7708, 0.8160]; AUPRC 0.3007 [0.2583, 0.3469].
- RF AUROC 0.8062 [0.7850, 0.8266]; AUPRC 0.3050 [0.2616, 0.3543].
- XGBoost AUROC 0.8083 [0.7880, 0.8293]; AUPRC 0.3049 [0.2636, 0.3519].

### MEDDL
- LR AUROC 0.7845 [0.7614, 0.8056]; AUPRC 0.3168 [0.2782, 0.3591].
- RF AUROC 0.7967 [0.7763, 0.8154]; AUPRC 0.3107 [0.2713, 0.3548].
- XGBoost AUROC 0.8036 [0.7831, 0.8214]; AUPRC 0.3152 [0.2774, 0.3601].

Intervals overlap substantially. No formal pairwise superiority/significance claim is made.

## 4. Calibration plots
Calibration plots were generated on the locked test set using the already selected probability version:
- MEDNG: Raw for LR/RF/XGBoost.
- MEDDL: Platt for LR/RF/XGBoost.

Plots use 10 equal-frequency bins and a 45-degree perfect-calibration reference line. These plots are evaluation-only and must not be used to fit another calibration layer.

## 5. Exploratory DCA
DCA was generated over threshold probabilities 0.01–0.30 using standard net benefit:

`TP/N − FP/N × pt/(1−pt)`.

Model curves are compared with treat-all and treat-none. The three curves are close and cross; no model dominates every threshold. DCA is therefore not used to declare a universal winner.

Because no validated clinical/policy action threshold has been defined, DCA is labelled exploratory and framed as hypothetical risk-based outreach/prioritization rather than demonstrated clinical utility.

## 6. Main implication for model review
The extension reinforces the existing conclusion that model choice is a trade-off problem rather than a one-metric leaderboard:
- MEDNG RF maximizes Recall, while XGBoost has stronger F1/Specificity/Brier and essentially tied AUPRC.
- MEDDL RF maximizes Recall at substantial Precision/Specificity cost; LR has slightly highest AUPRC; XGBoost has highest AUROC and lowest Brier.
- AUROC/AUPRC CIs overlap broadly.
- DCA does not show one model dominating the entire explored threshold range.

Therefore the group should retain candidate models for UHS interpretation and later SHAP/fairness review rather than declare a final paper model solely from this extension.

## 7. Outputs
Outputs are stored under `modeling/day8_10/uhs_extensions/` with a standalone reproduction script at `scripts/day8_10_uhs_extensions.py`.

## 8. Next step
UHS prepares its Metric Interpretation Guide and model-specific comments. UIT and UHS then jointly agree on model-selection criteria. Day 11–13 remains the survey-aware sensitivity phase; these bootstrap CIs must not be presented as NCHS design-based CIs.
