# Literature Review Plan — Cost-Related Barriers to Healthcare Access (NHIS 2024)

This document defines the shared workflow for the literature review supporting our HEALTHINFO IV submission. Everyone on the team should follow the same extraction structure so individual notes can be merged into one coherent review without rewriting.

**Deadline context:** Submission is due September 15, 2026. Literature review should be substantially complete before the Statistical Analysis section of Methods is finalized — findings from prior studies may still change our predictor set or modeling approach.

---

## 1. Scope

We are reviewing prior studies on:
- Unmet medical needs (UMN) / forgone or delayed care due to cost
- Andersen Behavioral Model of Health Services Use (Predisposing–Enabling–Need framework) applied to healthcare access
- Machine learning approaches to predicting healthcare access barriers
- Use of national health survey data (NHIS, KHPS, or equivalent) with complex survey design

**Out of scope:** general health disparities research not tied to a specific access/utilization outcome, and papers older than ~15 years unless foundational (e.g., original Andersen model).

---

## 2. Reading order (per paper)

Do not read papers front-to-back. Read in this order — it's faster and surfaces what matters first:

1. **Abstract** — decide in 2 minutes if the paper is relevant enough to continue.
2. **Methods → Measurements** — how did they define the outcome and predictors? This is usually the most reusable part for our own Methods section.
3. **Results → main table** — what predictors came out significant / important?
4. **Discussion** — authors usually summarize related literature here; a good source for finding more papers.
5. **Introduction** — read last. It's already a synthesis of related work and helps identify additional citations.

---

## 3. Extraction fields (use for every paper)

Record every paper using these fields. Keep entries short — this is a working table, not a summary essay.

| Field | What to record |
|---|---|
| **Citation** | Author(s), year, journal |
| **Data source & sample** | Survey name, year, country, sample size, sampling design (e.g., complex multistage survey) |
| **Outcome definition** | Exact question/definition used for the outcome (e.g., "needed care but did not get it due to cost, Yes/No") |
| **Predictors used** | List of input variables, grouped by framework category if the paper uses one (Predisposing/Enabling/Need or similar) |
| **Statistical/ML method** | Method(s) used (logistic regression, random forest, SHAP, etc.) and validation approach (train/test split, k-fold CV) |
| **Key findings** | Which predictors were most significant/important, and direction of effect |
| **Author-stated gap** | What limitation or future direction the authors themselves note |
| **Relevance to our study** | One sentence: how does this compare to or support our framework/methods? Where do we differ? |

This mirrors the structure of Kim et al. (2025, *BMC Health Services Research*), which is our closest methodological comparator (KHPS data, Andersen-style predictors, ML prediction of UMN with SHAP).

---

## 4. Workflow

1. **Claim a paper** — add your name next to a paper in the shared tracking sheet before starting, to avoid duplicate work.
2. **Extract using the fields above** — one row per paper.
3. **Flag conflicts** — if two papers define the outcome differently or disagree on a predictor's effect, flag it explicitly rather than silently picking one. These conflicts often become useful sentences in our Discussion.
4. **Do not summarize sequentially by paper** in the final write-up. Once extraction is done, group findings **by theme** (e.g., "ML approaches to predicting UMN," "role of insurance/income barriers," "gaps in survey-weighted modeling") — this is how the literature review section should actually read.
5. **Note what's missing across the whole set** — literature reviews are stronger when they identify a genuine gap, not just describe prior work. Explicitly discuss what none of the reviewed papers do that our study does (e.g., integrating survey weights into ML training, or separating forgone vs. delayed care as distinct outcomes).

---

## 5. Common mistakes to avoid

- **Don't just summarize each paper in isolation.** A list of "Paper A found X, Paper B found Y" is not a literature review — it's an annotated bibliography. Synthesize across papers.
- **Don't copy phrasing from abstracts/results.** Paraphrase in your own words; direct quotes should be rare and short.
- **Don't confuse association with causation** when reporting other studies' findings — stay faithful to what the original authors actually claimed.
- **Don't skip the "gap" step.** Every paper we read should end with a one-line answer to: *why does this NOT already answer our research question?*

---

## 6. Output

Once extraction is complete, the literature review section should be organized as:

1. Prevalence and consequences of unmet medical need (brief, sets up why this matters)
2. Theoretical frameworks used in prior work (Andersen model and variants)
3. Traditional statistical approaches to predicting access barriers
4. Machine learning approaches to predicting access barriers (closest comparators, e.g., Kim et al.)
5. Identified gap(s) our study addresses

Each subsection should end with a transition sentence connecting back to our own framework and Methods.

---

## 7. Current project progress and role split

The original Day 5–7 plan has **two parallel workstreams**. They must be reported separately.

### UIT — technical workstream

**UIT TECHNICAL DAY 1–7 COMPLETE.**

For Day 5–7, UIT technical work consists of:
- leakage-safe preprocessing pipeline;
- deterministic train/validation/test split;
- Logistic Regression baseline;
- conventional vs `WTFA_A`-weighted predictive comparison;
- weighting/class-weight review when needed.

Random Forest and XGBoost were also benchmarked early during Day 5, so part of the original Day 8–10 technical plan was completed ahead of schedule.

### UHS / collaborative literature workstream

Supporting/shared literature artifacts are also available:
- `literature/literature_matrix_day6.csv`
- `literature/NHIS2024_Day6_Literature_Matrix_18.xlsx`
- `research_log/Day06_Literature_Matrix.md`
- `research_log/Day07_Background_Related_Work.md`
- `docs/Background_Related_Work_Day7.md`
- `docs/README_DAY5_7.md`

These literature outputs belong to the **UHS / collaborative y tế–tổng quan workstream** under the original plan. They support the shared manuscript but are **not counted as UIT technical Day 5–7 deliverables**.

The literature review remains a **targeted narrative review**, not a PRISMA systematic review. The Day 7 prose is a working draft and still requires UHS/supervisor/venue-specific final editing before submission.
