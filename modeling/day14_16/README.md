# Day 14–16 aggregate SHAP outputs

This folder contains aggregate-only explainability artifacts for the locked Day 8–10 LR, RF, and XGBoost estimators on MEDNG and MEDDL.

## Core review files

- `day14_16_shap_global_importance.csv` — construct-level unweighted and `WTFA_A`-weighted importance.
- `day14_16_shap_direction_summary.csv` — numeric direction and categorical pattern summaries.
- `day14_16_shap_category_patterns.csv` — category-level signed SHAP by raw public-use code.
- `day14_16_shap_interaction_screen.csv` — exploratory RF/XGBoost construct-pair screen.
- `day14_16_shap_subgroup_patterns.csv` — explanation patterns by prespecified subgroup.
- `day14_16_shap_subgroup_skipped.csv` — subgroup levels excluded because N < 100.
- `day14_16_locked_reproduction_audit.csv` — six-row lock-integrity gate.
- `day14_16_config_log.json` — methods, versions, boundaries, and output manifest.
- `figures/` — 20 SVG figures tied to outcome, model, split, and explained output.

`day14_16_shap_encoded_importance.csv` is the detailed one-hot-level audit table. Use the construct-level table for primary reporting.

## Interpretation lock

SHAP values are predictive attributions, not causes. Importance magnitudes are not directly comparable across LR, RF, and XGBoost because the explained-output scales differ. Subgroup SHAP patterns are not fairness metrics.

No person-level prediction, `HHX`, or person-level SHAP matrix is stored here.
