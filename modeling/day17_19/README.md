# Day 17–19 aggregate fairness and error audit

This folder contains subgroup performance, calibration, error-rate, uncertainty, and disparity-span artifacts for the locked Day 8–10 LR, RF, and XGBoost models.

## Core review files

- `day17_19_subgroup_performance.csv` — eligible subgroup point estimates, reported unweighted and `WTFA_A`-weighted.
- `day17_19_subgroup_metric_cluster_bootstrap_ci.csv` — 400-replicate stratified-PSU intervals for AUROC, AUPRC, Recall, FNR, FPR, Brier, and absolute calibration-in-the-large error.
- `day17_19_disparity_summary.csv` — unsigned max-minus-min spans across eligible groups.
- `day17_19_disparity_cluster_bootstrap_ci.csv` — uncertainty intervals for those descriptive spans.
- `day17_19_subgroup_skipped.csv` — levels excluded because N < 100, positive N < 20, or negative N < 20.
- `day17_19_locked_reproduction_audit.csv` — twelve-row Day 8–10/Day 11–13 lock-integrity gate.
- `day17_19_config_log.json` — complete methods, versions, exclusions, boundaries, and output manifest.
- `figures/` — four SVG figures tied to outcome, model, locked test, threshold, and weighting.

## Interpretation lock

The recall span is an unsigned descriptive equal-opportunity TPR span at the locked validation threshold. FPR is reported separately. These are audit signals, not a formal finding of discrimination. AUPRC is prevalence-sensitive, and Brier score also changes with outcome prevalence; compare them with subgroup prevalence, AUROC, calibration, and uncertainty.

The threshold is the validation F1 operating point, not a clinical cutoff. No subgroup threshold was fitted, and no Day 17–19 result was used to tune or select a model.

No person-level prediction, `HHX`, `PPSU`, or `PSTRAT` is stored here.
