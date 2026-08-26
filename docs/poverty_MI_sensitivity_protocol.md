# POVRATTC_A sensitivity protocol

Primary SES predictor remains `RATCAT_A`.

For the `POVRATTC_A` sensitivity analysis:

1. Use the 10 records per `HHX` in `adultinc24.csv`, one model dataset per `IMPNUM_A`.
2. Use the same outcome cohort IDs and the same train/test `HHX` split across all 10 imputations.
3. In each sensitivity run, replace `RATCAT_A` with continuous `POVRATTC_A`; do not include both simultaneously.
4. Fit the same LR/RF/XGBoost pipeline separately for each imputation, with the same survey-weight strategy used in the corresponding primary model.
5. Report performance and explainability results across the 10 runs as sensitivity summaries (for example mean plus range/SD).
6. Do not describe these summaries as Rubin-pooled design-based inferential estimates unless a formally valid MI + complex-survey procedure is implemented.

`POVRATTC_A` is top-coded at 11.00 in NHIS 2024.
