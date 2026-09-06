# Day 22 — Reproducible Methods and Results draft

## Methods — analysis freeze through Day 22

We analyzed the 2024 National Health Interview Survey Sample Adult public-use data. Cost-related forgone care (`MEDNG12M_A`) was the primary outcome, and cost-related delayed care (`MEDDL12M_A`) was modeled independently as a complementary outcome. A separate sensitivity outcome represented either barrier (`MEDNG12M_A OR MEDDL12M_A`) among respondents with valid responses to both items. The main predictor set contained 12 prespecified constructs spanning predisposing, enabling, and need domains.

Respondents were assigned deterministically by `HHX` to train, validation, and locked test sets using the Day 5 SHA-256 rule. Preprocessing was fitted on the training set only. Logistic Regression, Random Forest, and XGBoost hyperparameters, probability calibration, and operating thresholds were selected using prespecified validation roles before locked-test evaluation. MEDNG retained raw probabilities, whereas MEDDL used validation-fitted Platt scaling. The operating thresholds maximized F1 within the validation threshold role and were treated as analytical operating points rather than clinical cutoffs.

Population-relevant estimates used `WTFA_A`; unweighted estimates were retained as sensitivity results. Survey uncertainty in earlier stages used `PSTRAT` and `PPSU`. Subgroup and error analyses were aggregate-only. Comparative subgroup results required N ≥ 100, at least 20 positive observations, and at least 20 negative observations.

Day 20 error analysis quantified false-negative and false-positive rates overall and across prespecified equity axes while preserving the locked model pipeline. Robustness analyses perturbed each threshold by prespecified multipliers of 0.8 and 1.2, refitted stochastic models with three prespecified seeds, evaluated strata with versus without cleaned-feature missingness, and fitted a separate composite-outcome sensitivity without test-driven hyperparameter tuning. No robustness result was used to replace the locked model, threshold, calibration method, or seed.

## Results — locked models and errors

Weighted locked-test AUROC ranged from 0.780 to 0.809 and weighted AUPRC from 0.315 to 0.339 across the six main outcome-model combinations. The operating-point results showed clear error trade-offs. For MEDNG, RF had the lowest weighted FNR (0.417) but a higher FPR (0.159), whereas XGBoost had the lowest FPR (0.074) but the highest FNR (0.562). For MEDDL, RF again had the lowest FNR (0.301) and the highest FPR (0.255); LR had the lowest FPR (0.090) but an FNR of 0.535.

Insurance remained the most prominent threshold-level audit signal. In the eligible uninsured group, RF produced FPR values of 0.975 for MEDNG and 1.000 for MEDDL at the locked thresholds. These findings indicate an operating-point concern requiring contextual interpretation; they do not establish discriminatory intent, causal harm, or deployment readiness.

## Results — robustness

Threshold perturbation produced the largest movement in recall and precision, as expected when a fixed cutoff is shifted. Weighted F1 remained within 0.297–0.363 for the three MEDNG models and 0.285–0.389 for the three MEDDL models across the three threshold factors. These test results were not used to choose a replacement threshold.

Seed sensitivity was smaller for discrimination metrics. Across seeds 2026, 2037, and 2048, weighted AUPRC varied by at most approximately 0.006 within an outcome-model pair, and weighted AUROC varied by at most approximately 0.005. Missingness-stratum findings were less stable because only 375–376 test observations, including 36 positives per outcome, had at least one cleaned-feature missing value.

The composite sensitivity included 32,345 respondents and 3,014 positive outcomes. Weighted test prevalence was 10.18%. Weighted AUROC/AUPRC were 0.788/0.390 for LR, 0.797/0.393 for RF, and 0.806/0.382 for XGBoost. RF had the highest recall (0.612), while LR had the highest precision (0.359), F1 (0.409), and specificity (0.904). Thus, the composite sensitivity also did not identify a universal winner.

## Results — integrity and privacy

The final leakage checklist passed for both main outcomes. The Day 20–22 validator reproduced all locked arms at threshold factor 1.0 and seed 2026, verified all threshold/seed/missingness/composite outputs, parsed both final SVG figures, and matched every SHA-256 code-freeze entry. Only aggregate tables, figures, and hashes were written; no `HHX`, person-level probability, or person-level prediction was exported.

## Draft limitations to retain

- This is cross-sectional classification, not prospective risk prediction or causal inference.
- Thresholds are analytical and validation-selected, not clinical or policy cutoffs.
- Weighted analysis improves population relevance but is not a complete substitute for all official NCHS variance procedures.
- Small subgroup and missingness-stratum estimates remain uncertain even when minimum gates are met.
- The composite outcome is a separate sensitivity analysis using reused MEDNG hyperparameters and should not replace independent outcome reporting.
- Model comparison remains multi-criteria; the intended use and relative cost of false negatives versus false positives must be defined before selecting a primary operational model.

