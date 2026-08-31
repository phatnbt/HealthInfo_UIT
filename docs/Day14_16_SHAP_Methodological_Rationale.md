# Day 14–16 — Locked-model SHAP explainability: methodological rationale

## Purpose

Day 14–16 explains what the already locked LR, RF, and XGBoost estimators learned for MEDNG and MEDDL. It does not start another model-selection cycle. The analysis addresses four prespecified questions:

1. Which of the 12 locked constructs contribute most strongly to each model's output?
2. What direction or category-specific pattern is visible for important predictors?
3. Which construct pairs show the strongest exploratory interaction signal in the two tree models?
4. Does the relative SHAP pattern vary across prespecified health-equity subgroups?

SHAP values quantify predictive attribution within a fitted model. They are not causal effects, independent etiologic contributions, evidence of biological difference, or proof that a subgroup difference is unfair.

## Locked analysis boundary

The script reconstructs the six Day 8–10 unweighted estimators using:

- the deterministic `HHX` train/validation/test membership;
- train-only preprocessing and the 12 locked predictor constructs;
- the locked LR/RF/XGBoost hyperparameters;
- the fixed runtime, including `xgboost==3.0.4`;
- the validation-selected probability version and threshold solely for the reproduction audit.

All six locked-test rows reproduce with a maximum absolute metric difference of `1.11e-16`, below the `1e-08` tolerance. No SHAP result changes a predictor, hyperparameter, probability version, calibration model, threshold, or model-retention decision.

MEDDL performance uses the locked Platt-scaled probabilities. SHAP explains the underlying base estimator before that monotonic calibration layer. The plots and tables state the explained output explicitly:

- LR: base-estimator log-odds;
- RF: positive-class probability;
- XGBoost: raw margin/log-odds.

Absolute SHAP magnitudes therefore must not be compared directly across model families. Within-model ranks and normalized importance shares are the intended comparisons.

## SHAP computation

- LR uses `SHAP LinearExplainer` with a deterministic 500-row training background.
- RF and XGBoost use `SHAP TreeExplainer`.
- Global and subgroup summaries use the full locked test split: 6,417 MEDNG rows and 6,419 MEDDL rows.
- One-hot SHAP values are summed within each person to recover the 12 original constructs before construct-level aggregation.
- Global importance is reported both unweighted and weighted by test-set `WTFA_A`.
- The beeswarm figures use a deterministic unweighted display sample of at most 1,500 test rows; aggregate tables use the full test split.
- Person-level predictions and person-level SHAP matrices remain in memory and are not written to disk.

## Direction and dependence

For numeric age, direction is summarized using the Spearman correlation between raw age and construct-level SHAP. For categorical constructs, the output reports the `WTFA_A`-weighted mean signed SHAP by raw public-use category code. These raw codes must be mapped through the locked NHIS data dictionary before manuscript publication.

The dependence figure for each outcome–model pair uses that model's highest `WTFA_A`-weighted construct. A linear trend in LR or a category contrast in a tree model describes fitted-model behavior only; it is not a dose-response or causal relationship.

## Interaction screen

RF and XGBoost receive an exploratory TreeSHAP interaction screen on a deterministic 100-row subset of the locked test data. Encoded interaction values are aggregated to pairs of original constructs. LR has no explicit interaction terms and therefore does not receive an interaction screen.

The interaction output is descriptive. It is not a confirmatory statistical interaction test, and RF versus XGBoost magnitudes are not directly comparable because their explained-output scales differ.

## Subgroup explanation patterns

SHAP importance patterns are summarized for:

- `HISPALLP_A` — primary race/ethnicity equity stratifier;
- `RATCAT_A` — poverty/income category;
- `NOTCOV_A` — insurance coverage status;
- `SEX_A` — sex, not gender;
- derived age groups: 18–34, 35–49, 50–64, and 65+.

Only subgroup levels with at least 100 locked-test observations are retained in the pattern table. Smaller levels are listed in a separate skipped-level audit. These tables describe which features a model relies on within each subgroup; they do not measure subgroup performance, error parity, calibration, equalized odds, or fairness. Those questions remain the Day 17–19 workstream.

## Results

### Population-weighted top-five constructs

| Outcome | Model | Top five constructs in rank order |
|---|---|---|
| MEDNG | LR | `PHSTAT_A`, `AGEP_A`, `EMPWRKLSW1_A`, `NOTCOV_A`, `FDSCAT3_A` |
| MEDNG | RF | `FDSCAT3_A`, `NOTCOV_A`, `AGEP_A`, `EMPWRKLSW1_A`, `K6SPD_A` |
| MEDNG | XGBoost | `HISPALLP_A`, `K6SPD_A`, `NOTCOV_A`, `FDSCAT3_A`, `CHRONIC_BURDEN_CAT` |
| MEDDL | LR | `AGEP_A`, `PHSTAT_A`, `EMPWRKLSW1_A`, `FDSCAT3_A`, `EDUCP_A` |
| MEDDL | RF | `NOTCOV_A`, `FDSCAT3_A`, `AGEP_A`, `EMPWRKLSW1_A`, `PHSTAT_A` |
| MEDDL | XGBoost | `HISPALLP_A`, `K6SPD_A`, `RATCAT_A`, `NOTCOV_A`, `FDSCAT3_A` |

The weighted-versus-unweighted construct rankings are stable: Spearman correlations range from 0.979 to 1.000, and four or five of each model's top five constructs are shared between the two aggregations.

The differences across LR, RF, and XGBoost are substantive. In particular, `HISPALLP_A` has high model-specific attribution in XGBoost but not in every model. This must not be described as a biological or causal effect. Categorical split structure, nonlinearity, correlation, and allocation of shared predictive information can all alter SHAP rankings.

### Exploratory interaction signals

- MEDNG RF: `EMPWRKLSW1_A × FDSCAT3_A` is the largest screened pair.
- MEDNG XGBoost: `RATCAT_A × FDSCAT3_A` is the largest screened pair.
- MEDDL RF: `NOTCOV_A × CHRONIC_BURDEN_CAT` is the largest screened pair.
- MEDDL XGBoost: `EDUCP_A × RATCAT_A` is the largest screened pair.

These are candidates for cautious domain review, not discovered causal mechanisms.

### Subgroup pattern finding

The top construct varies across some `HISPALLP_A` levels for LR and RF, whereas XGBoost assigns `HISPALLP_A` the largest within-group importance share across the retained raw-code levels. This is an explanation-pattern difference only. It does not establish disparate performance or unfairness and must be interpreted together with the upcoming Day 17–19 performance, calibration, and error audit.

## Reproducibility

Run from the repository root:

```bash
PYTHONPATH=scripts .venv/bin/python scripts/day14_16_shap_explainability.py \
  --data-dir /path/to/analysis-ready-cohorts \
  --locked-dir modeling/day8_10 \
  --out-dir modeling/day14_16 \
  --display-n 1500 \
  --interaction-n 100 \
  --n-jobs 2
```

Only aggregate outputs and SVG figures are committed. Source cohorts, `HHX`, person-level predictions, and person-level SHAP matrices are excluded.
