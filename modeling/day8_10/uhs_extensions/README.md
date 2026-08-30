# Day 8–10 UHS metric extension — reproducibility README

## Run
```bash
python scripts/day8_10_uhs_extensions.py \
  --data-dir /path/to/Day4_featurelocked_cohorts \
  --out-dir modeling/day8_10/uhs_extensions \
  --bootstrap-reps 1000 \
  --n-jobs 2
```

Required input files in `--data-dir`:
- `analysis_ready_MEDNG_FINAL_FEATURELOCK_RAWCODES.csv`
- `analysis_ready_MEDDL_FINAL_FEATURELOCK_RAWCODES.csv`

The person-level input files are intentionally not committed to the public repository.

## What the script locks
The script reconstructs the already locked Day 8–10 models. It does not search for new hyperparameters or thresholds.

## Outputs
Committed summary/audit outputs include:
- `day8_10_auroc_auprc_bootstrap_ci.csv`
- `day8_10_model_selection_evidence_table.csv`
- `day8_10_calibration_selected.csv`
- `day8_10_extension_prediction_manifest.csv`
- `day8_10_dca_common_threshold_summary.csv`
- `calibration_MEDNG.svg`
- `calibration_MEDDL.svg`
- `decision_curve_MEDNG.svg`
- `decision_curve_MEDDL.svg`
- `day8_10_uhs_extension_config.json`

The reproduction script also writes the full threshold-grid file `day8_10_dca_values.csv`; the compact common-threshold summary is committed for review while the full grid is deterministically reproducible from the script and locked inputs.

## Caveats
- Bootstrap CIs are locked-test predictive-performance CIs, not survey-design CIs.
- Calibration plots are evaluation-only.
- DCA is exploratory and assumes hypothetical risk-based outreach/prioritization; it is not a validated clinical/policy utility analysis.
- The test set was already reported once at Day 5; no output from this extension should be used for further tuning.
