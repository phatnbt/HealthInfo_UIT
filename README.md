# HealthInfo_UIT — NHIS 2024

Reproducible data-audit and modeling project for **cost-related unmet medical care** among U.S. adults using the **2024 National Health Interview Survey (NHIS)**.

## Day 1–4 status

**Data-side Day 1–4 is complete. UHS/domain predictor review has now been incorporated into the modeling plan.**

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

## Predictor status after UHS review

The original technical audit covered **22 candidate predictors**. UHS/domain review supports a more parsimonious scientific specification.

### Provisional main predictors (11 existing variables)

`AGEP_A`, `SEX_A`, `HISPALLP_A`, `EDUCP_A`, `RATCAT_A`, `EMPWRKLSW1_A`, `NOTCOV_A`, `FDSCAT3_A`, `PHSTAT_A`, `DISAB3_A`, `K6SPD_A`.

### Supporting/contextual

`MARSTAT_A`, `URBRRL23`, `REGION`.

### Exploratory/sensitivity

`DIBEV_A`, `HYPEV_A`, `BMICAT_A`, `ANXFREQ_A`, `DEPFREQ_A`, `LONELY_A`, `SOCSCLPAR_A`.

`SMKEV_A` is no longer the preferred smoking-status variable. If smoking is retained, `SMKCIGST_A` will be technically audited and used instead.

### Planned additions before final lock

- Prespecified **chronic-condition burden** feature; if it passes audit it becomes an additional main construct, yielding 12 core constructs.
- `POVRATTC_A` as an MI-aware SES sensitivity alternative to `RATCAT_A`, not simultaneously in the same primary model.
- `SMKCIGST_A` for exploratory smoking status if retained.

Full decision record: [`docs/UHS_Day3_4_predictor_review.md`](docs/UHS_Day3_4_predictor_review.md).

**Important:** the verified Day 1–4 data outputs remain valid, but they are not yet the final modeling feature matrix. Newly introduced variables/features must undergo the same code/missing audit before Day 5 training.

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
│   └── reproduce_day1_4.py
├── docs/
│   └── UHS_Day3_4_predictor_review.md
├── research_log/
└── audit/
    ├── cohort_flow.csv
    ├── predictor_code_missing_audit.csv
    ├── subgroup_EDA_EXACT.csv
    ├── poverty_MI_pooled_point_estimates.csv
    └── AUDIT_MANIFEST.json
```

## Reproduce Day 1–4

Download the official CDC/NCHS files `adult24csv.zip` and `adultinc24csv.zip`, then run:

```bash
python scripts/reproduce_day1_4.py adult24csv.zip adultinc24csv.zip
```

The script verifies the official MD5 checksums, target frequencies, independent outcome cohorts, and all 10 income imputations before writing analysis-ready CSV files locally.

## Data policy

Raw NHIS files and generated person-level analysis-ready CSV files are intentionally **not committed to this public repository**. They can be reproduced from official CDC/NCHS downloads using the included script.

## Interpretation cautions

- This is cross-sectional prediction/classification of contemporaneous outcomes, not future-risk forecasting or causal inference.
- SHAP values represent predictive contributions and must not be described as causal effects.
- Subgroup performance/fairness differences do not by themselves establish discrimination.
- `WTFA_A`-weighted point estimates are not a substitute for full design-based variance estimation; formal SE/CI should incorporate `PSTRAT` and `PPSU`.
- Poverty multiple-imputation point estimates here are descriptive; formal inferential pooling should combine MI and complex-survey variance appropriately.

## Gate to Day 5 modeling

Before LR/RF/XGBoost training, the project must:

1. Define and audit the chronic-condition burden variable.
2. Audit `SMKCIGST_A` if smoking is retained.
3. Lock the MI strategy for `POVRATTC_A` sensitivity analysis.
4. Re-run code/missing audit for newly added variables/features.
5. Freeze the final main/supporting/exploratory feature specification.

## Official sources

- NHIS 2024 documentation: https://www.cdc.gov/nchs/nhis/documentation/2024-nhis.html
- Adult codebook: https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Dataset_Documentation/NHIS/2024/Adult-codebook.pdf
- Survey description: https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Dataset_Documentation/NHIS/2024/srvydesc-508.pdf
- Checksum file list: https://ftp.cdc.gov/pub/health_statistics/nchs/dataset_documentation/NHIS/2024/Checksum-Filelist.pdf
- Dataset directory: https://ftp.cdc.gov/pub/health_Statistics/nchs/Datasets/NHIS/2024/
