# Day 11–13 — Survey-aware sensitivity: methodological rationale

## Purpose

NHIS is a complex probability survey. The person weight (`WTFA_A`) is needed when the target of description is the US civilian noninstitutionalized adult population rather than only the realized analytic sample. Stratification (`PSTRAT`) and clustering (`PPSU`) also affect uncertainty: treating all sampled adults as independent simple-random observations can make standard errors too small.

Day 11–13 therefore asks two separate questions:

1. How common are the two outcomes in the represented population after applying the survey design?
2. Are the locked Day 8–10 predictive conclusions materially sensitive to weighting during model fitting or evaluation?

This is a sensitivity analysis, not a new model-selection cycle.

## Locked elements

The following Day 8–10 decisions were preserved:

- deterministic `HHX` train/validation/test membership;
- the 12 previously locked predictor constructs and train-fitted preprocessing;
- LR/RF/XGBoost hyperparameters;
- Raw probabilities for MEDNG and Platt probabilities for MEDDL;
- validation-selected operating thresholds (MEDNG: LR 0.135, RF 0.110, XGBoost 0.185; MEDDL: LR 0.160, RF 0.080, XGBoost 0.140).

`WTFA_A`, `PSTRAT`, `PPSU`, and `HHX` are not model predictors. No test result is used to retune a model, reselect a probability version, change a threshold, change a feature, or declare a winner.

The unweighted-training/unweighted-evaluation arm reproduces all six locked Day 8–10 rows. The maximum absolute numerical difference is `3.83e-09`, below the audit tolerance of `1e-08`.

## Analysis

### Population description

Point estimates use the full-cohort person weight `WTFA_A`. Standard errors for weighted prevalence use Taylor linearization of a ratio mean, with PSU totals evaluated within `PSTRAT`. No finite-population correction is applied. Domain estimates keep the full design structure and give observations outside the domain zero linearized contribution.

### Predictive sensitivity

Each locked model is run under two training conditions:

- conventional unweighted fitting;
- `WTFA_A`-weighted fitting, after normalizing training weights to mean 1 for numerical stability.

Each set of predictions is then evaluated both conventionally and with raw `WTFA_A` test weights. For the MEDDL weighted-training arm, Platt scaling remains the locked probability method and is fitted with validation calibration weights; the probability method and threshold are not reselected.

Weighted AUROC, AUPRC, and Brier intervals use 400 stratified-PSU bootstrap resamples within `PSTRAT` on the locked test set, retaining `WTFA_A`. All 400 replicates were valid. These are survey-aware sensitivity intervals, not official NCHS replicate-weight variance estimates and not paired confidence intervals for between-model differences.

## Results

### Outcome prevalence in the full analytic cohorts

| Outcome | N | Unweighted prevalence | Weighted prevalence | Taylor 95% CI | Approx. design effect |
|---|---:|---:|---:|---:|---:|
| MEDNG — forgone care due to cost | 32,354 | 6.78% | 7.39% | 6.99%–7.78% | 1.88 |
| MEDDL — delayed care due to cost | 32,355 | 7.92% | 8.58% | 8.15%–9.01% | 1.99 |

Weighting raises the estimated prevalence by about 0.60 percentage points for MEDNG and 0.65 percentage points for MEDDL. The approximate design effects near 1.9 show why simple-random-sample uncertainty would be too optimistic for these population descriptions.

### Matched weighted training and weighted evaluation

| Outcome | Model | AUROC | AUPRC | Recall | Precision | F1 | Specificity | Brier |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| MEDNG | LR | 0.7958 | 0.3154 | 0.4812 | 0.2691 | 0.3451 | 0.9005 | 0.0566 |
| MEDNG | RF | 0.8072 | 0.3258 | 0.5850 | 0.2167 | 0.3162 | 0.8390 | 0.0577 |
| MEDNG | XGBoost | 0.8073 | 0.3207 | 0.4302 | 0.2945 | 0.3496 | 0.9215 | 0.0569 |
| MEDDL | LR | 0.7792 | 0.3368 | 0.4458 | 0.3383 | 0.3847 | 0.9150 | 0.0703 |
| MEDDL | RF | 0.7954 | 0.3384 | 0.7308 | 0.2000 | 0.3141 | 0.7152 | 0.0700 |
| MEDDL | XGBoost | 0.7980 | 0.3134 | 0.5300 | 0.2678 | 0.3558 | 0.8588 | 0.0705 |

Relative to the locked conventional arm, combined weighted training/evaluation changes AUROC by only -0.0057 to +0.0016. AUPRC rises for five outcome-model combinations (+0.0147 to +0.0278) and falls slightly for MEDDL XGBoost (-0.0018). Brier is numerically higher by 0.0011–0.0056; this should be read together with the changed weighted outcome prevalence rather than as a standalone ranking.

Most point-estimate movement comes from weighting the evaluation population, not from refitting with training weights. The notable exception is MEDDL XGBoost, for which weighted training lowers weighted-evaluation AUPRC by about 0.0159 relative to the same unweighted-trained model. This is a sensitivity finding, not a basis for post-hoc model replacement.

## Interpretation

There is still no universal winner.

- MEDNG: RF has the largest weighted AUPRC and recall; XGBoost has the largest weighted AUROC and F1; LR has the lowest Brier.
- MEDDL: RF has the largest weighted AUPRC and recall; XGBoost has the largest weighted AUROC; LR has the largest F1 and precision.
- The model-specific bootstrap intervals overlap substantially. They do not establish statistically significant superiority, and this analysis did not compute paired difference intervals.

The defensible conclusion is that the broad discrimination pattern is reasonably stable to survey weighting, while absolute prevalence, precision–recall behavior, calibration loss, and operating trade-offs are population-composition sensitive.

## Limits

- This is not the complete NCHS variance-estimation framework and does not use official replicate weights.
- Weighted machine learning does not by itself make predictions design-unbiased, causal, transportable, or deployment-ready.
- Outcomes and predictors are contemporaneous, self-reported past-12-month measures. Results are classification/association, not future-risk forecasting or causal effects.
- Test data have already been reported. Day 11–13 outputs are evaluation-only and must not reopen tuning.
- Subgroup output currently retains raw public-use codes; manuscript tables should map these codes through the locked data dictionary before publication.

## Reproducibility

Run from the repository root after making the two analysis-ready person-level cohort files available outside Git:

```bash
python scripts/day11_13_survey_sensitivity.py \
  --data-dir /path/to/analysis-ready-cohorts \
  --locked-dir modeling/day8_10 \
  --out-dir modeling/day11_13 \
  --bootstrap-reps 400 \
  --n-jobs 2
```

Person-level predictions and source cohort files are not written to the repository. Only aggregate outputs are committed.
