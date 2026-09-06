# Day 17–19 methodological rationale: locked-test subgroup fairness audit

## Purpose and boundary

Day 17–19 evaluates whether predictive discrimination, calibration, and error behavior differ across prespecified health-equity subgroups. It does not train a new model or decide that one model is a universal winner.

The analysis reconstructs the unweighted Day 8–10 Logistic Regression, Random Forest, and XGBoost estimators for MEDNG and MEDDL. It preserves the deterministic `HHX` split, 12 locked predictor constructs, train-only preprocessing, hyperparameters, Raw/Platt probability choice, validation calibration role, and validation-selected F1 threshold. The test set is used only for aggregate audit reporting.

## Prespecified equity domains

The plan requested two to four priority domains. Four conceptual domains are audited through five operational axes:

| Equity domain | Operational axis | Groups considered |
|---|---|---|
| Race/ethnicity | `HISPALLP_A` | Hispanic, NH White, NH Black, NH Asian, NH AIAN, NH AIAN + other, other/multiple |
| Income/poverty | collapsed `RATCAT_A` | <100%, 100–199%, and ≥200% FPL |
| Insurance | `NOTCOV_A` | uninsured and insured |
| Demographic | `SEX_A` and prespecified age bands | male/female; 18–34, 35–49, 50–64, 65–74, 75+ |

`SEX_A` is sex, not gender. `HISPALLP_A` is a social/structural equity stratifier and must not be interpreted as a biological cause.

## Estimands and uncertainty

The population-relevant view uses raw `WTFA_A` at evaluation. The unweighted view is retained as a matched sensitivity analysis. `PSTRAT`, `PPSU`, and `WTFA_A` are design variables, never predictors.

For each eligible subgroup, the point-estimate table reports:

- AUPRC as the primary rare-outcome discrimination metric and AUROC as complementary;
- Recall/TPR, FNR, FPR, specificity, precision, and F1 at the locked threshold;
- Brier score, observed prevalence, mean predicted probability, calibration-in-the-large error, calibration intercept/slope, and five-bin ECE;

The uncertainty table provides 95% percentile intervals for AUROC, AUPRC, Recall, FNR, FPR, Brier, and absolute calibration-in-the-large error from 400 PSU resamples within each `PSTRAT`, retaining `WTFA_A` for weighted estimates. The remaining metrics are descriptive point estimates only.

These bootstrap intervals are survey-aware sensitivity intervals, not official NCHS replicate-weight variance estimates. Accuracy is intentionally not used because both outcomes are uncommon.

## Stability gate

A subgroup enters comparative gap calculations only when it has at least 100 test observations, 20 outcome-positive observations, and 20 outcome-negative observations. Otherwise it is recorded in `day17_19_subgroup_skipped.csv` and not pooled post hoc.

Consequently, race/ethnicity comparisons are estimable for Hispanic, NH White, and NH Black groups only. NH Asian and the smaller race/ethnicity levels do not have enough positive events. Age 75+ is also excluded from comparative metrics because the locked test contains only 12 MEDNG and 15 MEDDL positive events. No conclusion should be made for excluded groups.

## Main findings

### Reproduction and data integrity

- All 12 reference comparisons passed: six unweighted rows reproduce Day 8–10, and six `WTFA_A` rows reproduce the Day 11–13 unweighted-training/weighted-evaluation arm.
- Maximum absolute metric drift was `3.33e-16`, below the `1e-08` tolerance.
- All subgroup and disparity intervals retained 400/400 bootstrap replicates.
- No person-level identifier or prediction was exported.

### Insurance is the dominant threshold-level audit signal

The insured–uninsured AUROC spans are small (`0.004–0.062` across outcome/model combinations), yet locked-threshold error spans are large:

| Outcome | Model | Recall/TPR span | FPR span | AUPRC span |
|---|---:|---:|---:|---:|
| MEDNG | LR | 0.584 | 0.526 | 0.322 |
| MEDNG | RF | 0.641 | 0.883 | 0.359 |
| MEDNG | XGBoost | 0.469 | 0.367 | 0.305 |
| MEDDL | LR | 0.535 | 0.495 | 0.293 |
| MEDDL | RF | 0.431 | 0.808 | 0.338 |
| MEDDL | XGBoost | 0.540 | 0.571 | 0.262 |

At the locked RF threshold, every weighted MEDDL uninsured observation is classified positive (Recall = 1.000; FPR = 1.000). For MEDNG, RF has Recall = 1.000 and FPR = 0.975 in the uninsured group. This is a serious operating-point flag, but not by itself evidence of discriminatory intent or clinical harm.

The uninsured prevalence is much higher than the insured prevalence in the locked test: 25.7% versus 5.1% for MEDNG, and 27.7% versus 6.9% for MEDDL after weighting. This explains part of the AUPRC and Brier contrast and is why those gaps cannot be interpreted alone. Insurance is also an input predictor, so the threshold behavior requires explicit Day 20–21 error analysis and UHS interpretation.

### Other subgroup patterns

- Age has substantial recall spans: `0.307–0.487` for MEDNG and `0.213–0.405` for MEDDL across the three models. These estimates exclude age 75+ because of insufficient positive events.
- Poverty recall spans are `0.161–0.305` for MEDNG and `0.180–0.204` for MEDDL; FPR spans are `0.091–0.274` and `0.095–0.289`, respectively.
- Among the three estimable race/ethnicity groups, recall spans are `0.155–0.330` for MEDNG and `0.061–0.165` for MEDDL; FPR spans are `0.072–0.214` and `0.091–0.223`.
- Sex point-estimate spans are smaller than the insurance and age signals: weighted recall spans are `0.001–0.044` for MEDNG and `0.011–0.056` for MEDDL; FPR spans remain below `0.033`.
- Weighting changes some point estimates, especially AUPRC spans, but does not remove the insurance operating-point signal. Both views therefore remain necessary.

## Interpretation rules

1. The unsigned recall span is descriptive equal-opportunity information, not a signed privileged-versus-unprivileged effect and not a hypothesis test.
2. FPR remains separate; no single scalar is labeled “equalized odds.”
3. AUPRC depends on subgroup prevalence. A higher AUPRC in a higher-prevalence group does not prove that the model serves that group better.
4. Brier score also reflects prevalence and probability calibration. Read it with observed prevalence and calibration-in-the-large.
5. A gap is not proof of discrimination. Sampling variability, measurement, subgroup composition, the inclusion of insurance as a predictor, and the nonclinical threshold all matter.
6. Fairness results may motivate robustness/error analysis and cautious reporting, but they must not trigger test-driven retuning or a post hoc winner claim.

## Decision and handoff

No universal fairness winner is declared. All three model families remain for transparent comparison. Day 20–21 should inspect false-positive and false-negative composition, especially the RF insurance behavior and older-age false negatives, and should run robustness checks without replacing the locked primary analysis. UHS should co-interpret the health-equity meaning and manuscript language.
