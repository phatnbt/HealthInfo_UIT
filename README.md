# HealthInfo_UIT — NHIS 2024

Reproducible data-audit and modeling project for **cost-related unmet medical care** among U.S. adults using the **2024 National Health Interview Survey (NHIS)**.

## Project status

**DAY 1–5 COMPLETE.**

- Day 1: official raw-source integrity and survey-design verification.
- Day 2: independent MEDNG/MEDDL outcome cohorts.
- Day 3: 22-candidate predictor dictionary and conceptual mapping.
- Day 4: missing/code audit, weighted/subgroup EDA, UHS review, final feature lock.
- Day 5: train/test preprocessing and baseline LR/RF/XGBoost modeling, conventional vs `WTFA_A`-weighted.

## Verified source files

- `adult24.csv`: **32,629 rows**, MD5 `6b0d5e572841ffef7b0f7df4ddfed556`
- `adultinc24.csv`: **326,290 rows**, MD5 `14a1d5780100c1b0a13acce433e00360`
- Income integrity: **10 imputations × 32,629 Sample Adults**

## Outcomes

### Primary — `MEDNG12M_A`
Needed medical care but did not get it because of cost in the past 12 months.

- Yes: **2,195**
- No: **30,159**
- Valid N: **32,354**
- Unweighted prevalence: **6.784%**
- `WTFA_A`-weighted prevalence: **7.387%**

### Secondary — `MEDDL12M_A`
Delayed medical care because of cost in the past 12 months.

- Yes: **2,564**
- No: **29,791**
- Valid N: **32,355**
- Unweighted prevalence: **7.925%**
- `WTFA_A`-weighted prevalence: **8.579%**

The outcomes are modeled **independently**. The common-valid cohort (N=32,345) is only for overlap/paired analyses and never replaces the two outcome-specific cohorts.

## Final main feature specification

### Main model — 12 constructs

11 existing NHIS predictors:

`AGEP_A`, `SEX_A`, `HISPALLP_A`, `EDUCP_A`, `RATCAT_A`, `EMPWRKLSW1_A`, `NOTCOV_A`, `FDSCAT3_A`, `PHSTAT_A`, `DISAB3_A`, `K6SPD_A`.

Plus:

`CHRONIC_BURDEN_CAT` = **0 / 1 / 2 / 3+ selected chronic-condition domains**.

The eight prespecified domains are:
1. Hypertension — `HYPEV_A`
2. Cardiovascular disease — any of `CHDEV_A`, `ANGEV_A`, `MIEV_A`, `STREV_A`, counted once
3. Asthma — `ASEV_A`
4. COPD — `COPDEV_A`
5. Cancer — `CANEV_A`
6. Diabetes — `DIBEV_A`
7. Arthritis — `ARTHEV_A`
8. Kidney disease — `KIDWEAKEV_A`

This is a selected-condition count/category for prediction, **not a validated clinical severity index**.

### Supporting/contextual
`MARSTAT_A`, `URBRRL23`, `REGION`.

### Exploratory/sensitivity
`BMICAT_A`, `ANXFREQ_A`, `DEPFREQ_A`, `LONELY_A`, `SOCSCLPAR_A`, `SMKCIGST_A`.

`DIBEV_A` and `HYPEV_A` remain disease-specific sensitivity variables and are not added alongside `CHRONIC_BURDEN_CAT` in the primary model.

`SMKEV_A` is not used as current smoking status; `SMKCIGST_A` is the smoking-status operationalization if smoking is analyzed.

### Poverty sensitivity
`RATCAT_A` remains the primary SES variable. `POVRATTC_A` is an MI-aware alternative only; it replaces `RATCAT_A` in sensitivity runs and is never included simultaneously with it in the primary model.

## Day 5 modeling design

- Deterministic `HHX` SHA-256 split with seed 2026: approximately **70% train / 10% validation / 20% test**.
- Validation is reserved and was not used for Day 5 fitting/model selection.
- Preprocessing fitted on train only.
- `AGEP_A`: variable-specific special codes → missing → median imputation → scaling.
- Categorical predictors: variable-specific special codes → missing → explicit `Missing` → one-hot encoding.
- 63 encoded model columns per outcome.
- Models: Logistic Regression, Random Forest, XGBoost.
- Training regimes: conventional unweighted and `WTFA_A`-weighted; weighted train weights normalized to mean 1.
- No SMOTE/resampling/class balancing in the Day 5 baseline.
- Test metrics: AUROC, AUPRC, recall, precision, F1, specificity, Brier.
- Threshold-dependent metrics at 0.50 are baseline/descriptive only.

### Split audit

MEDNG:
- Train 22,711 / positive 1,524
- Validation 3,226 / positive 233
- Test 6,417 / positive 438

MEDDL:
- Train 22,711 / positive 1,761
- Validation 3,225 / positive 280
- Test 6,419 / positive 523

## Day 5 headline results

Because outcomes are imbalanced, **AUPRC is prioritized over accuracy**.

### MEDNG
- Unweighted XGBoost: AUROC **0.809**, AUPRC **0.308**.
- `WTFA_A`-weighted XGBoost: AUROC **0.810**, AUPRC **0.322**.
- `WTFA_A`-weighted LR: AUPRC **0.315**, recall **0.116** at threshold 0.50.

### MEDDL
- Unweighted XGBoost: AUROC **0.806**, AUPRC **0.319**.
- `WTFA_A`-weighted LR: AUPRC **0.337**.
- `WTFA_A`-weighted XGBoost: AUROC **0.801**, AUPRC **0.321**.

These are **baseline held-out test results**, not final model-selection claims. Recall at threshold 0.50 remains low, especially for RF; validation-based threshold/calibration work is required before final reporting.

Full Day 5 record: [`research_log/Day05_Baseline_Modeling.md`](research_log/Day05_Baseline_Modeling.md).

Aggregate results: [`modeling/day5_primary_matched_summary.csv`](modeling/day5_primary_matched_summary.csv).

## Survey design

- `WTFA_A`: final annual survey weight
- `PSTRAT`: pseudo-stratum
- `PPSU`: pseudo-PSU

`HHX`, `WTFA_A`, `PSTRAT`, and `PPSU` are retained for reproducibility/survey-aware analysis and are **not ML predictors**.

`WTFA_A`-weighted ML is a weighted predictive comparison. It is **not automatically full design-based inference**; formal SE/CI would require explicit handling of the complex design including `PSTRAT` and `PPSU`.

## Repository structure

```text
.
├── README.md
├── scripts/
│   ├── reproduce_day1_4.py
│   └── finalize_day4_post_uhs.py
├── docs/
├── audit/
├── modeling/
│   ├── DAY5_MANIFEST.json
│   ├── day5_model_metrics.csv
│   ├── day5_primary_matched_summary.csv
│   ├── day5_best_by_auprc.csv
│   ├── day5_split_audit.csv
│   ├── day5_preprocessing_missing_audit.csv
│   └── day5_encoded_feature_audit.csv
└── research_log/
    └── Day05_Baseline_Modeling.md
```

Person-level raw data, analysis-ready cohorts, and person-level predictions are intentionally **not committed to the public repository**.

## Interpretation guardrails

- Cross-sectional prediction/classification, not future-risk forecasting.
- SHAP values, when used later, represent predictive contribution and not causal effects.
- Correlated variables may share predictive information.
- Race/ethnicity is treated as a social/structural equity stratifier, not a biological cause.
- Subgroup performance differences do not by themselves prove discrimination.
- `MARSTAT_A` is handled using variable-specific coding; the project never applies a global `7/8/9 = missing` rule.

## Next step

Use the untouched validation split for threshold/calibration work, then proceed to explainability (SHAP), subgroup fairness/performance auditing, and planned sensitivity analyses without using the held-out test set for model-selection decisions.

## Official sources

- NHIS 2024 documentation: https://www.cdc.gov/nchs/nhis/documentation/2024-nhis.html
- Adult codebook: https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Dataset_Documentation/NHIS/2024/Adult-codebook.pdf
- Survey description: https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Dataset_Documentation/NHIS/2024/srvydesc-508.pdf
- Checksum file list: https://ftp.cdc.gov/pub/health_statistics/nchs/dataset_documentation/NHIS/2024/Checksum-Filelist.pdf
