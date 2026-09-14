# Current repair status — 2026-09-15

This is a repair/sensitivity release for review, **not an approved final submission**. Historical Day22 results and their 30-entry freeze manifest are unchanged. Independent Linux training reproduces all historical LR/RF/XGBoost metrics within1e-8; XGB max drift1.11e-16. The Windows wheel still differs by up to0.0181306514. See SECOND_HOST_VERIFICATION.md and linux_reference_validation.json. Artifact-integrity PASS does not mean that every model has been retrained successfully.

## Completed technical repairs

- Exact Git LF bytes restored and `.gitattributes` specifies LF for frozen text and binary handling for XLSX/ZIP/PNG/DOCX. Day20–22 gate now passes on the Windows working checkout without modifying its manifest.
- Historical Literature_18 workbook recovered from 17 CRC-valid local ZIP members. Worksheet content was retained, not reconstructed from CSV19. `literature/historical_matrix_recovery.json` records hashes; `literature/CORRECTED_SOURCE_NOTES.md` records the Bertoldo erratum and Kim sample-size inconsistency.
- Implemented model diagram generated from `audit/final_feature_lock.csv`: [`../model/locked_12_constructs.svg`](../model/locked_12_constructs.svg), all 12 constructs including food security. Conceptual PNG22 and training PNG11 are historical diagrams superseded for implementation reporting. RACEALLP_A in the old conceptual diagram is not the implemented HISPALLP_A predictor; duplicated Employment represents two proposed pathways, not two model inputs.
- Four corrected calibration/DCA legends in `figures/` contain matching solid/dashed/dotted line samples. Curve coordinates and numerical values are unchanged.
- Day5 baseline accepts explicit data/output directories, is import-safe and creates parent directories. Person-level prediction export is opt-in with `--export-person-level`, for private use only.
- Current manuscript front-door status and C16 locator corrected; NHIS/SHAP methodological sources and bootstrap/calibration boundaries added. Literature19 remains the authoritative narrative matrix.
- New full MI run: 132 fits, 240 performance rows, 2,880 aggregate construct-SHAP rows and 120 additivity audit rows across ten imputations, two outcomes, three models and two training strategies. The same deterministic 128-row test sample per outcome is used across all arms; LR uses a fixed 500-row train background. These are sampled explanation-sensitivity summaries, not full-test SHAP, MI subgroup fairness or Rubin-pooled inference.
- KG reconstructed for **2 overall +74 subgroup =76 total rows**, filtering subgroup N≥30. Original Taylor estimates agree with an independent array implementation; Beta/F KG formulations agree per row. The original subgroup file was intentionally excluded from Git for Drive distribution, not accidentally deleted.

Aggregate result CSVs are distributed in the local `00_CURRENT_REPAIR_V2` handoff. Do not commit raw inputs, generated cohort CSVs, HHX predictions or per-person SHAP matrices. The subgroup health tables retain their local/Drive distribution boundary.

## Important newly confirmed SHAP defect

The frozen Day14–16 code transforms sparse test inputs into dense arrays before explaining XGBoost and disables additivity checking. For a sparse-trained booster, absent CSR entries act as missing, while explicit dense zero values follow a different path. New MI tests observed sparse-versus-dense probability differences up to **0.7790173888**. This measures representation differences for the same newly fitted MI estimators, not the historical 0.01813 model-reproduction drift.

`scripts/mi_explainability.py` and `scripts/day14_16_shap_explainability_v2.py` use exact native TreeSHAP on a CSR DMatrix and check that contributions sum to the native raw margin. Across the 120 MI explanation arms, maximum additivity residual was **7.6294e-6 on Linux** and **7.1526e-6 on Windows**, both below 3e-5 (float32 tree arithmetic); LR/RF residuals were at machine precision. Historical dense XGBoost SHAP figures/tables are superseded by sparse-corrected full-test explanations of the Linux estimator that passes the strict historical metric gate. The Windows current-runtime RATCAT sample remains a separate sensitivity artifact. No historical model parameters or predictions are changed.

## Reproduce from a clean checkout

Python: 3.12.10. Create an isolated venv and install `requirements-repair.lock` (all installed direct/transitive pins); keep root `requirements.txt` as the original seven direct pins. Record native XGBoost library SHA-256, compiler/build info, threads, raw checksums, source hashes and runtime versions. Equal Python package versions alone do not guarantee equal XGBoost native behavior.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-repair.lock
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -I scripts/finalize_day4_post_uhs.py inputs/adult24csv.zip inputs/adultinc24csv.zip
.\.venv\Scripts\python.exe -I -u scripts/run_repair_analysis.py --reference-dir . --out-dir rerun_outputs --adult-zip inputs/adult24csv.zip --income-zip inputs/adultinc24csv.zip --n-jobs 4 --include-shap --shap-sample-size 128
.\.venv\Scripts\python.exe -I scripts/run_survey_companion.py --data-dir nhis_day4_post_uhs_final --out-dir rerun_outputs/survey_prevalence
.\.venv\Scripts\python.exe -I scripts/validate_repair_outputs.py --results rerun_outputs
```

Download public-use input ZIPs from [CDC NHIS2024](https://www.cdc.gov/nchs/nhis/documentation/2024-nhis.html); the cohort builder and MI runner verify official CSV MD5 and counts. `validate_repair_outputs.py --require-historical-match` additionally fails if any model exceeds the historical tolerance. The normal command writes separate artifact and historical-reproduction statuses; an OPEN XGB issue is never hidden behind artifact PASS.

`.github/workflows/independent-repair.yml` performs the same sequence on an Ubuntu24.04 GitHub-hosted machine and saves aggregate-only evidence. Its completion and model-specific results must be read before claiming second-host verification; a configured workflow alone is not proof.

## Scope still requiring evidence or review

- Linux reference runtime resolves the historical metric reproduction issue. Windows/native-build portability remains limited; original model/prediction byte identity cannot be proven without those files.
- Historical152 manifest and historical Day25–28 execution/approval records are unavailable. Actual release inventory and new dated repair log are supplied; no fabricated reconstruction.
- Additional Day4 candidate branches are tracked in `SCOPE_REGISTER.csv`. They remain deferred with no claim of completion or approval of scope removal.
- Venue formatting, UHS interpretation and final approval remain OPEN. No approver/date is inferred from a Day milestone.
- MI SHAP is sampled global construct attribution; it does not establish imputation-robust subgroup explanations, causal effects, clinical utility or transportability to Vietnam.

Fairness figure captions must link `modeling/day17_19/day17_19_subgroup_metric_cluster_bootstrap_ci.csv`, `day17_19_disparity_cluster_bootstrap_ci.csv` and `day17_19_subgroup_skipped.csv` for uncertainty/eligibility, along with subgroup_performance.csv for point estimates; spans alone are not a categorical fair/unfair verdict. Calibration/DCA curves are descriptive/exploratory. Do not compare RF probability SHAP magnitudes directly with LR/XGB log-odds or describe base SHAP as Platt-probability attribution.

The completed independent Linux132-fit run is at https://github.com/phatnbt/HealthInfo_UIT/actions/runs/34880716053 . The full-test corrected primary SHAP release is tracked at https://github.com/phatnbt/HealthInfo_UIT/actions/runs/34881598998 . After validation its source is modeling/day14_16_corrected_linux; primary performance remains the frozen Day22 table. Original raster diagrams carry LEGACY names; the two new vector diagrams contain exactly12 constructs, one employment entry and HISPALLP_A.

## Completed corrected primary release

Full-test strict Linux workflow34881598998 completed successfully. Six primary reproduction arms PASS, maximum metric drift1.11e-16; native CSR SHAP additivity max7.1526e-6. All6,417/6,419 test records explained;20 figure files generated. Source tables/figures: modeling/day14_16_corrected_linux.

Current manuscript: [Manuscript_V2_Corrected_SHAP.md](../docs/Manuscript_V2_Corrected_SHAP.md), [Claim_Traceability_V2.csv](../docs/Claim_Traceability_V2.csv), [Corrected_Figure_Table_Index_V2.md](../docs/Corrected_Figure_Table_Index_V2.md). Weighted/unweighted rank correlations0.979–1.000; XGB top constructs now age/food security/insurance for MEDNG and age/insurance/food security for MEDDL. Prior dense XGB rankings are superseded. UHS and final venue review remain open.

Canonical new MI results use the independently verified Linux runtime, with historical reference metrics passing. Windows results remain dated evidence of portability differences; cross-host outputs are not pooled. The root ZIP is regenerated with the actual inventory and every non-control payload hash; it is not the historical152-file package.
