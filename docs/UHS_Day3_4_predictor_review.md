# UHS Day 3–4 Predictor Review — Project Update

Status: **scientific/domain review accepted with technical corrections and pending implementation checks**.

## 1. What is accepted

The UHS review is broadly methodologically sound and is adopted as the scientific feature-selection plan before Day 5 modeling.

### Provisional core predictors (existing variables)

1. `AGEP_A` — age; keep numeric for modeling, derive age groups only for fairness reporting.
2. `SEX_A` — sex; do not relabel as gender.
3. `HISPALLP_A` — combined Hispanic origin/race recode; primary race/ethnicity equity stratifier.
4. `EDUCP_A` — educational attainment; socioeconomic position.
5. `RATCAT_A` — family income-to-poverty ratio category; primary poverty/SES operationalization.
6. `EMPWRKLSW1_A` — NHIS employment/work-status recode (official description: Worked last week); do not simplify to paid employment only.
7. `NOTCOV_A` — current health insurance coverage status; predictive/enabling variable, not a direct measure of access quality.
8. `FDSCAT3_A` — 3-category adult food-security status; material hardship.
9. `PHSTAT_A` — self-rated general health; health-need/status construct, not a causal factor.
10. `DISAB3_A` — Washington Group composite functional disability indicator; predictor and equity-relevant subgroup.
11. `K6SPD_A` — serious psychological distress (K6); preferred mental-health composite for the main model.

### Supporting/contextual predictors

- `MARSTAT_A` — marital/household context.
- `URBRRL23` — urban-rural context.
- `REGION` — Census-region context.

### Exploratory/sensitivity predictors

- `DIBEV_A`
- `HYPEV_A`
- `BMICAT_A`
- `ANXFREQ_A`
- `DEPFREQ_A`
- `LONELY_A`
- `SOCSCLPAR_A`

`SMKEV_A` is **not** retained as the preferred smoking-status operationalization. If smoking is retained, the planned replacement is `SMKCIGST_A` after a technical code/missing audit.

## 2. Additions before final feature lock

These are accepted as **planned additions**, not yet implemented in the current Day 1–4 analysis-ready cohorts.

### A. Chronic-condition burden

Create a prespecified chronic-condition count/category (for example 0, 1, 2, 3+) using a documented list of NHIS chronic-condition variables. `DIBEV_A` and `HYPEV_A` alone should not be described as overall chronic-condition burden.

**Important:** the condition list, coding, missing rules, and prevalence must be audited before this engineered feature enters the main model. Until then, `DIBEV_A` and `HYPEV_A` remain exploratory.

### B. `POVRATTC_A` sensitivity analysis

Keep `RATCAT_A` as the primary categorical poverty predictor. Add `POVRATTC_A` only as an alternative/sensitivity SES operationalization.

Because NHIS income has 10 imputations, any poverty analysis using `POVRATTC_A` must explicitly account for the multiple-imputation structure. Do not include `RATCAT_A` and `POVRATTC_A` together in the same primary model.

### C. `SMKCIGST_A` if smoking is retained

Use `SMKCIGST_A` (cigarette smoking status) rather than `SMKEV_A` (ever smoked at least 100 cigarettes) when the scientific construct is smoking status.

## 3. Technical correction to the UHS feedback

`MARSTAT_A` codes `7`, `8`, and `9` must **not** be globally recoded as missing. In the 2024 NHIS public-use recode they are valid categories:

- 7 = Never married
- 8 = Living with a partner
- 9 = Unknown marital status

This remains consistent with the project rule: **missing/special handling is variable-specific; never apply a global 7/8/9 missing rule.**

## 4. Interpretation rules adopted

- This is cross-sectional prediction/classification of contemporaneous cost-related unmet/delayed medical care, not forecasting a future outcome.
- SHAP values are predictive contributions, not causal effects.
- `NOTCOV_A`, poverty, mental health, disability, and other predictors must not be described as causes based only on model/SHAP results.
- Correlated predictors can share predictive information; SHAP importance should not be interpreted as independent etiologic contribution.
- Race/ethnicity is treated as a social/structural equity stratifier, not a biological cause.
- `WTFA_A`, `PSTRAT`, `PPSU`, and `HHX` remain non-predictor design/reproducibility fields.

## 5. Modeling implications

### Main-model plan before engineered-feature implementation

Use the 11 existing core predictors above as the **provisional main set**.

### Final main model after technical audit

If the chronic-condition burden feature passes technical audit, it becomes an additional main construct. Therefore the final main model would contain **12 core constructs**, not merely the original 11.

### Planned sensitivity analyses

- Main model without `NOTCOV_A`.
- `RATCAT_A` versus MI-aware `POVRATTC_A` alternative.
- Supporting geography/social-context variables added to the core model.
- Exploratory symptom/behavior variables added separately or as a secondary model.
- Smoking status via `SMKCIGST_A` if retained.

## 6. What is NOT changed yet

The verified Day 1–4 raw-source checks, outcome cohorts, prevalence estimates, and existing 22-variable code audit remain historically valid.

However, any newly introduced variable/feature (`POVRATTC_A` as a model input, chronic-condition burden, `SMKCIGST_A`) must pass the same technical code/missing audit before Day 5 modeling. The current analysis-ready files are therefore **not yet the final modeling feature matrix**.

## 7. Gate to Day 5

Before modeling:

1. Define and audit the chronic-condition burden variable.
2. Audit `SMKCIGST_A` if smoking is kept.
3. Lock the multiple-imputation strategy for `POVRATTC_A` sensitivity analysis.
4. Re-run predictor/code/missing audit for any newly added variable.
5. Freeze the final main/supporting/exploratory feature specification.

Only after these checks should preprocessing and LR/RF/XGBoost training begin.
