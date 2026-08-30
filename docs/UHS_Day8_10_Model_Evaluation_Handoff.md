# UHS handoff — Day 8–10 model-evaluation extension

## Status
**UIT technical extension complete.** This addendum was produced in response to the UHS request for additional evidence before discussing a leading model.

This extension does **not** re-tune models, re-select Raw vs Platt probabilities, or re-select thresholds. It reconstructs the already locked Day 8–10 models and adds evaluation-only evidence on the same held-out test split.

## What was added
1. **95% CI for AUROC and AUPRC** using 1,000 nonparametric paired bootstrap resamples of locked-test individual rows.
2. **Calibration plots** using the probability version already selected by validation: Raw for all MEDNG models; Platt for all MEDDL models.
3. **Exploratory Decision Curve Analysis (DCA)** over threshold probabilities 0.01–0.30, with treat-all and treat-none comparators.
4. **Model-selection evidence table** combining discrimination, 95% CI, Recall, Precision, F1, Specificity, Brier, selected probability version and threshold.

## 95% CI results

### MEDNG
| Model | AUROC (95% CI) | AUPRC (95% CI) |
|---|---|---|
| LR | 0.7942 (0.7708–0.8160) | 0.3007 (0.2583–0.3469) |
| RF | 0.8062 (0.7850–0.8266) | 0.3050 (0.2616–0.3543) |
| XGBoost | 0.8083 (0.7880–0.8293) | 0.3049 (0.2636–0.3519) |

### MEDDL
| Model | AUROC (95% CI) | AUPRC (95% CI) |
|---|---|---|
| LR | 0.7845 (0.7614–0.8056) | 0.3168 (0.2782–0.3591) |
| RF | 0.7967 (0.7763–0.8154) | 0.3107 (0.2713–0.3548) |
| XGBoost | 0.8036 (0.7831–0.8214) | 0.3152 (0.2774–0.3601) |

### Technical interpretation of the intervals
The intervals overlap substantially. This means the point-estimate ranking alone is not strong evidence of a clearly superior model. However, **overlapping individual CIs are not a formal test that model differences equal zero**. No paired bootstrap CI for model-to-model differences was prespecified in this UHS request, so no significance claim is made here.

These are **predictive-performance bootstrap CIs on the locked test sample**, not NCHS complex-survey design-based confidence intervals. They do not incorporate `WTFA_A`, `PPSU`, or `PSTRAT`. Survey-aware sensitivity remains the Day 11–13 workstream.

## Calibration evidence
- **MEDNG:** validation previously retained **Raw** probabilities for LR, RF and XGBoost. The new test calibration plot is evaluation-only.
- **MEDDL:** validation previously retained **Platt** probabilities for LR, RF and XGBoost. The new test calibration plot evaluates those locked calibrated probabilities.
- Calibration uses 10 equal-frequency probability bins. The 45-degree line is perfect calibration.
- Test plots must **not** be used to fit another calibration layer.

The existing Brier results remain:
- MEDNG: LR 0.0555, RF 0.0564, XGBoost 0.0553.
- MEDDL: LR 0.0651, RF 0.0652, XGBoost 0.0649.

## Exploratory Decision Curve Analysis
DCA uses:

`Net benefit = TP/N − FP/N × pt/(1−pt)`

where `pt` is threshold probability.

The plots compare each locked model against **treat all** and **treat none** over 0.01–0.30. Across this exploratory range, the three model curves are close and cross one another; **no model dominates the full threshold range**. Therefore DCA does not justify a universal winner without an agreed decision threshold/action.

DCA is intentionally labelled **exploratory** because the project has not established a validated clinical or policy action threshold. A possible interpretation for later UHS discussion is hypothetical risk-based outreach/prioritization, such as financial-support navigation or access-barrier screening. This is not evidence of demonstrated clinical utility.

## Locked test metric context
### MEDNG
- RF has the highest Recall (0.5411) but lower Precision (0.2238) and Specificity (0.8625).
- XGBoost has higher F1 (0.3532), Specificity (0.9368) and slightly lower Brier (0.0553), while RF and XGBoost AUPRC are nearly identical (~0.305).
- LR remains competitive but has lower AUROC than RF/XGBoost.

### MEDDL
- RF has the highest Recall (0.6730), but Precision is only 0.2065 and Specificity 0.7705.
- LR has the numerically highest AUPRC (0.3168) by a very small margin.
- XGBoost has the highest AUROC (0.8036) and lowest Brier (0.0649) among the three, with F1 almost identical to LR.

## What UHS can now review
UHS can use this package to prepare the requested **Metric Interpretation Guide** and model-by-model interpretation. Recommended review dimensions are:
- AUPRC as the primary discrimination metric for the rare positive class;
- AUROC as complementary discrimination evidence;
- 95% CI and uncertainty around both metrics;
- calibration/Brier;
- Recall versus Precision/Specificity trade-off;
- exploratory DCA under an explicitly stated hypothetical action;
- later SHAP and subgroup/fairness evidence before a paper-level final model is declared.

## Model-selection boundary
At this stage the project should use language such as **“leading candidate model(s)”** or **“models retained for further evaluation.”** The added test evidence must not be used to launch new hyperparameter, calibration, or threshold tuning on the same test split.

Also note that this test split was already reported once in Day 5 baseline work. Therefore this package is a **locked test evaluation extension**, not a pristine first-use test analysis.

## Files
- `scripts/day8_10_uhs_extensions.py`
- `modeling/day8_10/uhs_extensions/day8_10_auroc_auprc_bootstrap_ci.csv`
- `modeling/day8_10/uhs_extensions/day8_10_model_selection_evidence_table.csv`
- `modeling/day8_10/uhs_extensions/day8_10_calibration_selected.csv`
- `modeling/day8_10/uhs_extensions/calibration_MEDNG.svg`
- `modeling/day8_10/uhs_extensions/calibration_MEDDL.svg`
- `modeling/day8_10/uhs_extensions/day8_10_dca_common_threshold_summary.csv`
- `modeling/day8_10/uhs_extensions/decision_curve_MEDNG.svg`
- `modeling/day8_10/uhs_extensions/decision_curve_MEDDL.svg`
- `modeling/day8_10/uhs_extensions/day8_10_extension_prediction_manifest.csv`
- `modeling/day8_10/uhs_extensions/day8_10_uhs_extension_config.json`

The reproduction script additionally generates the full threshold-grid `day8_10_dca_values.csv` from the locked inputs; the committed common-threshold summary is the compact review artifact.
