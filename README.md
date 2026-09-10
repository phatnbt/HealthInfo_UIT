# Literature Review Plan — Cost-Related Barriers to Healthcare Access (NHIS 2024)

> **UHS start here:** [`docs/UHS_READ_ME_FIRST_DAY1_22.md`](docs/UHS_READ_ME_FIRST_DAY1_22.md) is the curated Day 1–22 file map, result-explanation guide, and boundary between UHS review files and UIT reproducibility artifacts.

This document defines the shared workflow for the literature review supporting our HEALTHINFO IV submission. Everyone on the team should follow the same extraction structure so individual notes can be merged into one coherent review without rewriting.

**Deadline context:** Submission is due September 15, 2026. The Day 4 primary feature specification has already been frozen before modeling. New literature may refine interpretation, sensitivity analyses, Discussion, and citation support, but should not silently reopen the locked primary predictor set or Day 5–10 model-selection protocol.

---

## 1. Scope

We are reviewing prior studies on:
- Unmet medical needs (UMN) / forgone or delayed care due to cost
- Andersen Behavioral Model of Health Services Use (Predisposing–Enabling–Need framework) applied to healthcare access
- Machine learning approaches to predicting healthcare access barriers
- Use of national health survey data (NHIS, KHPS, or equivalent) with complex survey design
- Explainability and subgroup/fairness evaluation relevant to health-equity prediction

**Out of scope:** general health disparities research not tied to a specific access/utilization outcome, and papers older than ~15 years unless foundational (e.g., original Andersen model).

---

## 2. Reading order (per paper)

Do not read papers front-to-back. Read in this order — it is faster and surfaces what matters first:

1. **Abstract** — decide quickly whether the paper is relevant enough to continue.
2. **Methods → Measurements** — how did the authors define the outcome and predictors?
3. **Results → main table/figure** — what predictors or model patterns were most important?
4. **Discussion** — identify limitations, interpretation, and additional citations.
5. **Introduction** — read last as a synthesis of the surrounding literature.

---

## 3. Extraction fields (use for every paper)

Record every paper using these fields. Keep entries short — this is a working evidence matrix, not a summary essay.

| Field | What to record |
|---|---|
| **Citation** | Author(s), year, journal |
| **Data source & sample** | Survey name, year, country, sample size/design when reported |
| **Outcome definition** | Exact question/definition used for the outcome |
| **Predictors used** | Input variables, grouped by framework category if applicable |
| **Statistical/ML method** | Logistic regression, RF, XGBoost, SHAP, validation approach, etc. |
| **Key findings** | Main model/feature findings and direction when appropriate |
| **Author-stated gap** | Limitation or future direction stated by the source |
| **Relevance to our study** | How the paper supports or differs from NHIS 2024 project design |
| **Caution / limitation** | Why the paper cannot be transferred directly to our setting |

Kim et al. (2025, *BMC Health Services Research*) is retained as a **closest methodological comparator** because it applies multiple ML models and SHAP to unmet medical needs using the 2020 Korean Health Panel Survey. It is now included explicitly in the current literature matrix rather than being referenced only in this README.

---

## 4. Workflow

1. **Claim a paper** — add your name next to it in the shared tracking sheet before starting to avoid duplicate work.
2. **Extract using the fields above** — one row per paper.
3. **Flag conflicts** — if papers define the outcome differently or disagree on a predictor, record the conflict explicitly.
4. **Synthesize by theme**, not paper-by-paper, in the manuscript.
5. **Identify the remaining gap** across the whole evidence set without making unsupported “first-ever” claims.
6. **Preserve protocol boundaries** — after Day 4, literature findings can motivate prespecified sensitivity analyses or Discussion, but any change to the locked primary model must be documented as a protocol amendment rather than silently introduced after seeing model/test results.

---

## 5. Common mistakes to avoid

- **Do not summarize each paper in isolation.** A list of “Paper A found X, Paper B found Y” is an annotated bibliography, not a literature review.
- **Do not copy wording from abstracts/results.** Paraphrase and verify citation details.
- **Do not confuse association with causation.**
- **Do not skip the gap step.**
- **Do not claim ML, SHAP, SDOH, or unmet-care prediction is novel by itself.** Kim et al. (2025) and other matrix sources are direct counterexamples.
- **Do not use later literature to justify post-hoc tuning on the locked Day 8–10 test set.**

---

## 6. Intended manuscript organization

The literature review should be organized as:

1. Prevalence and consequences of unmet medical need / cost-related care barriers
2. Andersen Behavioral Model and SDOH framing
3. Traditional statistical approaches to healthcare-access barriers
4. Machine-learning approaches to UMN/access prediction, including the Kim et al. comparator
5. Complex-survey-aware predictive modeling
6. Explainability and health-equity/fairness evaluation
7. Defensible research gap and study contribution

---

## 7. Current project progress and role split

The project has two parallel workstreams and they should remain distinguishable in reporting.

### UIT — technical workstream

**UIT TECHNICAL DAY 1–24 COMPLETE; GATE 4 PASS; MANUSCRIPT V1 READY.**

Completed technical components include:
- Day 1–4 source integrity, outcome/cohort audit, 22-candidate audit, UHS review, and final 12-construct feature lock;
- leakage-safe preprocessing and deterministic `HHX` train/validation/test split;
- Logistic Regression, Random Forest, and XGBoost baseline modeling for MEDNG and MEDDL;
- conventional vs `WTFA_A`-weighted baseline predictive comparison;
- Day 8–10 moderate RF/XGBoost tuning using validation-only model-selection roles;
- validation-fitted Platt calibration check and validation-based F1 operating thresholds;
- locked-test re-evaluation;
- UHS-requested 95% bootstrap CI for AUROC/AUPRC, calibration plots, and exploratory Decision Curve Analysis.
- Day 11–13 design-based prevalence using `WTFA_A`, Taylor-linearized uncertainty using `PSTRAT`/`PPSU`, and locked weighted-vs-unweighted predictive sensitivity;
- 400-replicate stratified-PSU bootstrap sensitivity intervals for weighted AUROC, AUPRC, and Brier;
- an exact reproduction gate confirming that the conventional arm retains the locked Day 8–10 results.
- Day 14–16 locked-model SHAP for LR/RF/XGBoost across both outcomes, including global and `WTFA_A`-weighted construct importance, direction/dependence patterns, exploratory tree-model interactions, and subgroup explanation patterns;
- a second exact reproduction gate confirming 6/6 locked-test rows before explanation, with no person-level SHAP output committed.
- Day 17–19 locked-test fairness/error-rate audit over four equity domains (five operational axes), reporting subgroup discrimination, calibration, Recall/FNR/FPR, weighted–unweighted sensitivity, and 400-replicate stratified-PSU intervals;
- a twelve-row reproduction gate against the Day 8–10 and Day 11–13 reference arms, plus explicit exclusion of underpowered subgroup levels and aggregate-only output validation.
- Day 20–21 aggregate false-negative/false-positive analysis, including weighted/unweighted overall errors and 168 eligible subgroup error profiles without person-level export;
- prespecified robustness checks for threshold multipliers 0.8/1.0/1.2, seeds 2026/2037/2048, and missingness strata, with no post-test reselection;
- a separate `MEDNG OR MEDDL` composite-outcome sensitivity on the 32,345-person common cohort using reused MEDNG hyperparameters and validation-only calibration/threshold selection;
- Day 22 manuscript-facing final tables, two summary figures, a ten-check leakage/integrity gate, and a current 30-entry SHA-256 computational freeze manifest after the controlled chronic-burden report-layer correction.
- Day 23–24 full manuscript v1 assembly, 16-claim traceability table, UHS review guide, and final figure/table index without reopening the frozen analysis.

**Current boundary:** Day 23–24 manuscript v1 is complete. Day 25–26 consistency audit is next. The Day 22 computational state is frozen; Day 8–22 test, sensitivity, SHAP, subgroup, error, and robustness results must not be used for another tuning cycle, a post-hoc winner claim, or a causal interpretation.

Day 11–13 supports a sensitivity conclusion, not a model-selection conclusion: survey weighting changes population prevalence and some precision–recall/calibration trade-offs, while AUROC changes are small. No model is a universal winner across outcomes and metrics. See `docs/Day11_13_Survey_Aware_Methodological_Rationale.md` and `research_log/Day11_13_Survey_Aware_Sensitivity.md`.

Day 14–16 supports an explainability conclusion, not a causal or fairness conclusion: weighted and unweighted SHAP rankings are stable within models, but the feature patterns differ across LR, RF, XGBoost and some subgroups. See `docs/Day14_16_SHAP_Methodological_Rationale.md` and `research_log/Day14_16_SHAP_Explainability.md`.

Day 17–19 supports a subgroup audit conclusion, not a categorical fair/unfair verdict. Insurance and age show the largest locked-threshold error-rate signals, while sparse race/ethnicity levels and age 75+ cannot be compared reliably on this test split. No model is a universal fairness winner. See `docs/Day17_19_Fairness_Methodological_Rationale.md` and `research_log/Day17_19_Fairness_Audit.md`.

Day 20–22 confirms the operating-point trade-off: RF reduces false negatives but increases false positives, while LR/XGBoost generally do the reverse. Threshold, seed, missingness, and composite sensitivity do not identify a universal winner. Gate 4 passes, and the computational state is frozen for manuscript work. See `docs/Day20_22_Error_Robustness_Methodological_Rationale.md`, `docs/Day22_Methods_Results_Draft.md`, and `research_log/Day20_22_Error_Robustness_Code_Freeze.md`.

Day 23–24 assembles the full first manuscript from the frozen evidence and adds explicit code-to-claim traceability. UHS should review the public-health interpretation, use case, FN/FP trade-off, insurance wording, sparse groups, and Vietnam future-work boundary without editing the frozen numbers. See `docs/Day23_24_Manuscript_V1.md`, `docs/Day23_24_UHS_Review_Guide.md`, `docs/Day23_24_Claim_Traceability.csv`, and `research_log/Day23_24_Manuscript_Assembly.md`.

### UHS / collaborative literature workstream

The current authoritative narrative-review matrix contains **19 peer-reviewed sources**, including Kim et al. (2025) as the closest ML+SHAP UMN comparator.

Supporting/shared literature artifacts:
- `literature/literature_matrix_day6.csv` — **authoritative current 19-source matrix**
- `literature/NHIS2024_Day6_Literature_Matrix_18.xlsx` — historical 18-source snapshot retained for provenance; not the current authoritative matrix
- `research_log/Day06_Literature_Matrix.md`
- `research_log/Day07_Background_Related_Work.md`
- `docs/Background_Related_Work_Day7.md`
- `docs/README_DAY5_7.md`

These literature outputs belong to the **UHS / collaborative y tế–tổng quan workstream** under the original plan. They support the shared manuscript but are not counted as UIT technical deliverables.

The literature review remains a **targeted narrative review**, not a PRISMA systematic review. The Day 7 prose is a working draft and still requires UHS/supervisor/venue-specific final editing before submission.
