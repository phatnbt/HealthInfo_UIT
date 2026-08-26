# HealthInfo_UIT — NHIS 2024

Reproducible data-audit and modeling project for **cost-related unmet medical care** among U.S. adults using the **2024 National Health Interview Survey (NHIS)**.

## Day 1–4 status

**DAY 1–4 COMPLETE.** Raw-source verification, outcome-specific cohorts, the original 22-variable technical audit, UHS/domain review, and the post-UHS technical feature lock are complete. The project is ready to begin Day 5 preprocessing/modeling.

Verified raw CDC/NCHS files:

- `adult24.csv`: **32,629 rows**, MD5 `6b0d5e572841ffef7b0f7df4ddfed556`
- `adultinc24.csv`: **326,290 rows**, MD5 `14a1d5780100c1b0a13acce433e00360`
- Income file integrity: **10 imputations × 32,629 Sample Adults**

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

The two outcomes are constructed **independently** from raw `adult24.csv`. The common-valid cohort (N=32,345) is reserved for overlap/paired analyses only.

## Final feature specification after UHS review

### Main model — 12 constructs

11 existing NHIS predictors:

`AGEP_A`, `SEX_A`, `HISPALLP_A`, `EDUCP_A`, `RATCAT_A`, `EMPWRKLSW1_A`, `NOTCOV_A`, `FDSCAT3_A`, `PHSTAT_A`, `DISAB3_A`, `K6SPD_A`.

Plus one engineered construct:

`CHRONIC_BURDEN_CAT` = **0 / 1 / 2 / 3+ selected chronic-condition domains**.

The eight prespecified domains are:

1. Hypertension — `HYPEV_A`
2. Cardiovascular disease — any of `CHDEV_A`, `ANGEV_A`, `MIEV_A`, `STREV_A` (counted once)
3. Asthma — `ASEV_A`
4. COPD — `COPDEV_A`
5. Cancer — `CANEV_A`
6. Diabetes — `DIBEV_A`
7. Arthritis — `ARTHEV_A`
8. Kidney disease — `KIDWEAKEV_A`

This is a **selected-condition count/category for prediction**, not a validated clinical severity index. If any required domain is unresolved, the burden feature is left indeterminate rather than treating the condition as absent. Indeterminate burden is **222/32,354 (0.686%)** in the MEDNG cohort and **222/32,355 (0.686%)** in the MEDDL cohort.

### Supporting/contextual

`MARSTAT_A`, `URBRRL23`, `REGION`.

### Exploratory/sensitivity

`BMICAT_A`, `ANXFREQ_A`, `DEPFREQ_A`, `LONELY_A`, `SOCSCLPAR_A`, `SMKCIGST_A`.

`DIBEV_A` and `HYPEV_A` are retained for **disease-specific sensitivity analyses**, but are not added alongside `CHRONIC_BURDEN_CAT` in the primary model.

`SMKEV_A` is replaced by `SMKCIGST_A` when smoking status is analyzed. `SMKCIGST_A` has passed the post-UHS code audit; codes 1–4 are substantive smoking-status groups, while 5/9 are handled as an explicit unknown group.

### Poverty sensitivity

`RATCAT_A` remains the primary SES predictor. `POVRATTC_A` is an alternative sensitivity operationalization only.

The MI strategy is locked: run the same model separately for each of the **10 `IMPNUM_A` datasets**, use the same `HHX` train/test split across imputations, replace `RATCAT_A` with `POVRATTC_A`, and summarize the 10 sensitivity runs descriptively. Do not call these summaries formal Rubin-pooled design-based inference unless that procedure is explicitly implemented.

Full scientific review: [`docs/UHS_Day3_4_predictor_review.md`](docs/UHS_Day3_4_predictor_review.md).

Final lock: [`audit/final_feature_lock.csv`](audit/final_feature_lock.csv).

## Post-UHS Day 4 checks

- All newly used chronic-condition component variables have **no unexpected observed codes** against the official NHIS code sets.
- `SMKCIGST_A` code audit: **PASS**.
- `POVRATTC_A`: **10 × 32,629** records verified; observed range is **0.00–11.00** in every imputation.
- Age equity groups are finalized as **18–34, 35–49, 50–64, 65–74, 75+**.
- Disability is retained as an **exploratory equity subgroup**.
- `MARSTAT_A` codes 7/8/9 remain valid recode categories; the project never applies a global `7/8/9 = missing` rule.

## Survey design

- `WTFA_A`: final annual survey weight
- `PSTRAT`: pseudo-stratum
- `PPSU`: pseudo-PSU

`HHX`, `WTFA_A`, `PSTRAT`, and `PPSU` are retained for audit/survey analysis and are **not ML predictors**.

## Repository structure

```text
.
├── README.md
├── .gitignore
├── scripts/
│   ├── reproduce_day1_4.py
│   └── finalize_day4_post_uhs.py
├── docs/
│   ├── UHS_Day3_4_predictor_review.md
│   └── poverty_MI_sensitivity_protocol.md
├── research_log/
└── audit/
    ├── cohort_flow.csv
    ├── predictor_code_missing_audit.csv
    ├── subgroup_EDA_EXACT.csv
    ├── subgroup_EDA_post_UHS_addendum.csv
    ├── day4_post_uhs_variable_audit.csv
    ├── chronic_burden_summary.csv
    ├── poverty_MI_input_audit.csv
    ├── final_feature_lock.csv
    ├── poverty_MI_pooled_point_estimates.csv
    └── AUDIT_MANIFEST.json
```

## Reproduce / finalize Day 1–4

Download the official CDC/NCHS files `adult24csv.zip` and `adultinc24csv.zip`, then run:

```bash
python scripts/reproduce_day1_4.py adult24csv.zip adultinc24csv.zip
python scripts/finalize_day4_post_uhs.py adult24csv.zip adultinc24csv.zip
```

The second script verifies the post-UHS variables, constructs the final chronic-burden feature, verifies the 10 poverty imputations, and writes final feature-lock MEDNG/MEDDL cohort files locally.

## Data policy

Raw NHIS files and generated person-level analysis-ready CSV files are intentionally **not committed to this public repository**. They can be reproduced from official CDC/NCHS downloads using the included scripts.

## Interpretation cautions

- This is cross-sectional prediction/classification of contemporaneous outcomes, not future-risk forecasting or causal inference.
- SHAP values represent predictive contributions and must not be described as causal effects.
- Correlated predictors may share predictive information; SHAP importance is not independent etiologic contribution.
- Subgroup performance/fairness differences do not by themselves establish discrimination.
- `WTFA_A`-weighted point estimates are not a substitute for full design-based variance estimation; formal SE/CI should incorporate `PSTRAT` and `PPSU`.
- Poverty MI sensitivity summaries are not formal MI + complex-survey inference unless such a method is explicitly implemented.

## Day 5 gate

**PASSED.** Final technical feature specification is frozen and Day 5 may begin with independent MEDNG/MEDDL preprocessing and LR/RF/XGBoost modeling.

## Official sources

- NHIS 2024 documentation: https://www.cdc.gov/nchs/nhis/documentation/2024-nhis.html
- Adult codebook: https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Dataset_Documentation/NHIS/2024/Adult-codebook.pdf
- Survey description: https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Dataset_Documentation/NHIS/2024/srvydesc-508.pdf
- Checksum file list: https://ftp.cdc.gov/pub/health_statistics/nchs/dataset_documentation/NHIS/2024/Checksum-Filelist.pdf
- Dataset directory: https://ftp.cdc.gov/pub/health_Statistics/nchs/Datasets/NHIS/2024/
