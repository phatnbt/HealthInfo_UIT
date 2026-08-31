# Literature Review Plan — Cost-Related Barriers to Healthcare Access (NHIS 2024)

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

**UIT TECHNICAL DAY 1–13 COMPLETE.**

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

**Current boundary:** Day 14–16 SHAP/explainability is next; subgroup/fairness work remains subsequent. Day 8–13 test and sensitivity results must not be used for another tuning cycle or a post-hoc winner claim.

Day 11–13 supports a sensitivity conclusion, not a model-selection conclusion: survey weighting changes population prevalence and some precision–recall/calibration trade-offs, while AUROC changes are small. No model is a universal winner across outcomes and metrics. See `docs/Day11_13_Survey_Aware_Methodological_Rationale.md` and `research_log/Day11_13_Survey_Aware_Sensitivity.md`.

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
