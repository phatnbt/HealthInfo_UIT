# UHS Day 3–4 Predictor Review — Project Update

Status: **scientific/domain review accepted; post-UHS technical implementation complete; Day 5 gate passed**.

## 1. What is accepted

The UHS review is broadly methodologically sound and is adopted as the scientific feature-selection plan before Day 5 modeling.

### Core predictors (existing variables)

1. `AGEP_A` — age; keep numeric for modeling, derive age groups only for fairness reporting.
2. `SEX_A` — sex; do not relabel as gender.
3. `HISPALLP_A` — combined Hispanic origin/race recode; primary race/ethnicity equity stratifier.
4. `EDUCP_A` — educational attainment; socioeconomic position.
5. `RATCAT_A` — family income-to-poverty ratio category; primary poverty/SES operationalization.
6. `EMPWRKLSW1_A` — NHIS employment/work-status recode; do not simplify to paid employment only.
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

- `BMICAT_A`
- `ANXFREQ_A`
- `DEPFREQ_A`
- `LONELY_A`
- `SOCSCLPAR_A`
- `SMKCIGST_A`

`DIBEV_A` and `HYPEV_A` are retained for disease-specific sensitivity analyses because they are represented inside the final chronic-burden construct.

`SMKEV_A` is **not** retained as the preferred smoking-status operationalization and is replaced by `SMKCIGST_A` when smoking status is analyzed.

## 2. Post-UHS additions implemented

### A. Chronic-condition burden — IMPLEMENTED

A prespecified selected chronic-condition count/category was created:

`CHRONIC_BURDEN_CAT` = `0`, `1`, `2`, `3+` selected condition domains.

Eight domains:

1. Hypertension — `HYPEV_A`
2. Cardiovascular disease — any of `CHDEV_A`, `ANGEV_A`, `MIEV_A`, `STREV_A`; counted once to avoid double-counting related CVD diagnoses
3. Asthma — `ASEV_A`
4. COPD — `COPDEV_A`
5. Cancer — `CANEV_A`
6. Diabetes — `DIBEV_A`
7. Arthritis — `ARTHEV_A`
8. Kidney disease — `KIDWEAKEV_A`

This is a **selected-condition count/category for prediction**, not a validated clinical severity index.

Technical audit result:
- All component variables: PASS; no unexpected observed code.
- MEDNG burden indeterminate: 222/32,354 = 0.686%.
- MEDDL burden indeterminate: 222/32,355 = 0.686%.
- Unresolved components are not recoded as disease absence.

`CHRONIC_BURDEN_CAT` is now the 12th main construct.

### B. `POVRATTC_A` sensitivity — PROTOCOL LOCKED

`RATCAT_A` remains the primary categorical poverty predictor.

`POVRATTC_A` is an alternative/sensitivity SES operationalization. Adultinc integrity was re-verified:
- 10 imputations × 32,629 Sample Adults.
- Every `HHX` has `IMPNUM_A = 1..10`.
- Observed `POVRATTC_A` range is 0.00–11.00 in every imputation.

Sensitivity protocol:
- same `HHX` train/test split across all imputations;
- one LR/RF/XGBoost run per imputation;
- replace `RATCAT_A` with `POVRATTC_A` rather than include both;
- summarize the 10 runs descriptively (mean/range/SD);
- do not call the result formal Rubin-pooled design-based inference unless a valid MI + complex-survey inferential method is implemented.

### C. `SMKCIGST_A` — AUDITED

`SMKCIGST_A` passed technical code audit.

Observed codes: `1,2,3,4,5,9`, matching the NHIS recode.
- 1–4 = substantive smoking-status groups.
- 5/9 = explicit Unknown in exploratory modeling.

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

## 5. Final modeling specification

### Main — 12 constructs

Existing 11:
`AGEP_A`, `SEX_A`, `HISPALLP_A`, `EDUCP_A`, `RATCAT_A`, `EMPWRKLSW1_A`, `NOTCOV_A`, `FDSCAT3_A`, `PHSTAT_A`, `DISAB3_A`, `K6SPD_A`.

Engineered:
`CHRONIC_BURDEN_CAT`.

### Supporting
`MARSTAT_A`, `URBRRL23`, `REGION`.

### Exploratory/sensitivity
`BMICAT_A`, `ANXFREQ_A`, `DEPFREQ_A`, `LONELY_A`, `SOCSCLPAR_A`, `SMKCIGST_A`.

### Planned sensitivity analyses

- Main model without `NOTCOV_A`.
- `RATCAT_A` versus MI-aware `POVRATTC_A` alternative.
- Supporting geography/social-context variables added to the core model.
- Exploratory symptom/behavior variables added separately or as a secondary model.
- Disease-specific `DIBEV_A` / `HYPEV_A` analyses instead of adding them to the same primary model as chronic burden.

## 6. Fairness addendum

Age groups are finalized as:
- 18–34
- 35–49
- 50–64
- 65–74
- 75+

Disability is retained as an exploratory equity subgroup.

## 7. Provenance

The verified original Day 1–4 raw-source checks, outcome cohorts, prevalence estimates, and 22-candidate-variable code audit remain historically valid.

Post-UHS outputs are stored separately so the project preserves the distinction between:
- original candidate-variable audit, and
- final scientific/technical feature lock.

## 8. Gate to Day 5

**PASSED.**

All requested post-UHS technical checks are complete:
1. Chronic-condition burden defined and audited.
2. `SMKCIGST_A` audited.
3. `POVRATTC_A` 10-imputation sensitivity strategy locked.
4. New variables/features passed code/missing checks.
5. Final main/supporting/exploratory feature specification frozen.

Preprocessing and independent MEDNG/MEDDL LR/RF/XGBoost modeling may now begin.
