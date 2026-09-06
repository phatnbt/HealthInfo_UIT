# Day 20–22 — Error analysis, robustness, and initial code freeze

## 1. What was locked before this analysis

Day 20–22 does not reopen model development. For MEDNG and MEDDL, the following are inherited exactly from Day 8–10:

- the deterministic `HHX` train/validation/test split;
- the 12 predictor constructs;
- train-only preprocessing;
- LR/RF/XGBoost hyperparameters;
- Raw probabilities for MEDNG and Platt probabilities for MEDDL;
- the validation-selected F1 operating threshold for each outcome-model pair.

The locked test set is used only for aggregate error and robustness reporting. No Day 20–22 result is used to choose a new model, seed, calibration method, feature, or threshold.

## 2. Day 20 — What the error analysis asks

Overall AUROC does not reveal how a model behaves at its selected operating point. Day 20 therefore separates:

- false negatives: people with the outcome whom the model classifies negative;
- false positives: people without the outcome whom the model classifies positive;
- FNR: the proportion of actual positives missed;
- FPR: the proportion of actual negatives incorrectly flagged.

Both unweighted and `WTFA_A`-weighted estimates are retained. Weighted confusion totals represent weighted population mass, not a literal count of sampled respondents.

### Weighted locked-threshold results

| Outcome | Model | FNR | FPR | Recall | Precision | F1 |
|---|---:|---:|---:|---:|---:|---:|
| MEDNG | LR | 0.504 | 0.100 | 0.496 | 0.275 | 0.354 |
| MEDNG | RF | 0.417 | 0.159 | 0.583 | 0.218 | 0.317 |
| MEDNG | XGBoost | 0.562 | 0.074 | 0.438 | 0.310 | 0.363 |
| MEDDL | LR | 0.535 | 0.090 | 0.465 | 0.334 | 0.389 |
| MEDDL | RF | 0.301 | 0.255 | 0.699 | 0.211 | 0.324 |
| MEDDL | XGBoost | 0.467 | 0.126 | 0.533 | 0.292 | 0.377 |

The trade-off is consistent with earlier findings: RF misses fewer positives but flags many more negatives, while LR and XGBoost generally reduce false-positive burden. Therefore, RF’s higher recall is not a universal advantage; its value depends on whether the intended use can tolerate substantially more false positives.

### Insurance and age require focused interpretation

The Day 17–19 insurance signal is confirmed as an operating-point problem rather than a ranking-only problem. For RF, uninsured FPR remains 0.975 for MEDNG and 1.000 for MEDDL. This means nearly all or all eligible uninsured negatives are flagged at the locked threshold. It must not be described as a good screening result merely because uninsured recall is 1.000.

For age, the highest eligible-group FNR is often in age 65–74, while age 75+ remains excluded from comparative metrics because it does not meet the positive-event gate. This is insufficient evidence for a causal age effect and insufficient evidence to claim performance for the excluded group.

The aggregate error profile additionally reports each eligible group’s share of all false negatives or false positives. These shares are affected by both group size and error rate; they are not person-level risk scores and must not be used for micro-targeting.

## 3. Day 21 — Robustness checks

### 3.1 Threshold perturbation

Each locked threshold is multiplied by 0.8, 1.0, and 1.2. This is a prespecified perturbation, not a search for a better test threshold.

- Weighted F1 ranges from 0.326–0.360 for MEDNG-LR, 0.297–0.332 for MEDNG-RF, and 0.339–0.363 for MEDNG-XGBoost.
- Weighted F1 ranges from 0.368–0.389 for MEDDL-LR, 0.285–0.351 for MEDDL-RF, and 0.358–0.377 for MEDDL-XGBoost.
- Lower thresholds increase recall and usually decrease precision/specificity; higher thresholds do the reverse.

The fact that another perturbation may score better on a test metric does not authorize replacing the validation-selected threshold.

### 3.2 Random-seed sensitivity

The same locked hyperparameters are refitted with seeds 2026, 2037, and 2048. No seed is selected by test performance.

- LR is deterministic in this pipeline and therefore unchanged.
- RF weighted AUPRC ranges are narrow: 0.325–0.328 for MEDNG and 0.338–0.340 for MEDDL.
- XGBoost weighted AUPRC ranges are 0.315–0.321 for MEDNG and 0.328–0.331 for MEDDL.
- XGBoost MEDNG weighted AUROC ranges from 0.809 to 0.814; other AUROC seed ranges are also small.

Discrimination is reasonably stable to these three seeds, while threshold-dependent F1 can move more because small probability changes can move observations across a fixed cutoff.

### 3.3 Missingness sensitivity

Missingness rates are checked separately in train, validation, and test for all 12 constructs. The largest recurring rates are approximately 3.0–3.6% for employment/food-security fields and approximately 1.6–1.9% for K6; most other fields are below 1%.

The test set contains 375 MEDNG rows and 376 MEDDL rows with at least one cleaned-feature missing value, including 36 positives in each outcome. This stratum passes the minimum gate but is still much smaller than the no-missing stratum, so its metric differences are descriptive and uncertain.

For LR and XGBoost, weighted F1 is lower in the missingness stratum for both outcomes. RF is mixed: MEDNG F1 is slightly higher, whereas MEDDL F1 is lower and its missingness stratum has very low specificity. These findings support retaining train-fitted imputation and explicit missing categories, while reporting missingness as a limitation; they do not support choosing a new model from this subgroup.

### 3.4 Composite-outcome sensitivity

The original plan specified a sensitivity target equal to `MEDNG OR MEDDL`. It is now evaluated on the common valid-outcome cohort:

- total N = 32,345;
- positive N = 3,014;
- test N = 6,416 with 607 positives;
- unweighted test prevalence = 9.46%;
- weighted test prevalence = 10.18%.

To avoid test-driven tuning, RF/XGBoost reuse the locked MEDNG hyperparameters. The Day 8–10 validation-only calibration/threshold protocol is applied inside this separate sensitivity analysis. LR and RF retain Raw probabilities; XGBoost selects Platt on validation. Weighted test results are:

| Model | Probability | Threshold | AUROC | AUPRC | Recall | Precision | F1 | Specificity |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LR | Raw | 0.175 | 0.788 | 0.390 | 0.477 | 0.359 | 0.409 | 0.904 |
| RF | Raw | 0.115 | 0.797 | 0.393 | 0.612 | 0.282 | 0.387 | 0.824 |
| XGBoost | Platt | 0.155 | 0.806 | 0.382 | 0.590 | 0.310 | 0.407 | 0.851 |

Again, no universal winner appears: RF has the highest weighted AUPRC and recall, XGBoost has the highest AUROC, and LR has the highest F1, precision, and specificity in this composite sensitivity. This analysis does not replace separate MEDNG and MEDDL results.

## 4. Final leakage and integrity review

Ten checks pass across the two main outcomes:

- no identifier, survey-design variable, raw outcome, or derived outcome is in the predictor lock;
- train, validation, and test counts match Day 5 and have no overlap;
- preprocessing is fitted only on train;
- probability version and threshold are read from the Day 8–10 validation record;
- MEDNG and MEDDL are modeled independently and never predict each other.

The independent validator also confirms that factor 1.0 in threshold sensitivity and seed 2026 reproduce every locked reference arm, all aggregate schemas exclude person-level fields, and every code-freeze hash matches.

## 5. What Day 22 freezes — and what remains a UHS decision

The computational state through Day 22 is recorded in `day22_code_freeze_manifest.csv`. It covers upstream model scripts/configs and the new aggregate outputs using SHA-256 hashes. Subsequent manuscript edits must not silently modify the locked analysis.

The technical analysis still does not decide the relative harm of a false negative versus a false positive. UHS must state the intended use case and the acceptable trade-off before one primary model can be justified. Until then, the defensible conclusion remains a transparent comparison of three retained models rather than a winner claim.

