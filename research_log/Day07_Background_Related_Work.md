# Day 7 — Background and Related Work

> **Role / ownership:** UHS / collaborative literature work under the original 4-week plan. This file is **not** an UIT technical Day 7 deliverable. It is kept in the shared repository as a working paper artifact.

## Mục tiêu
Dùng literature matrix Day 6 để viết Background + Related Work và chốt cách diễn đạt gap/novelty.

## Phân công theo kế hoạch gốc
- **UIT — kỹ thuật, Day 5–7:** preprocessing pipeline chống leakage, train/validation/test split, Logistic Regression baseline, weighting/class-weight comparison khi cần.
- **UHS — y tế/tổng quan, Day 5–7:** Background + Related Work và literature matrix 12–20 bài.

Do đó file này thuộc nhánh **UHS / collaborative literature**, không được tính là công việc kỹ thuật chính của UIT.

## Đã viết
1. Cost-related unmet care và affordability.
2. Andersen Model + Healthy People 2030 SDOH.
3. Health equity / subgroup performance.
4. Machine learning + XAI.
5. Complex survey / survey-aware prediction.
6. Research gap + proposed contribution.

## Literature update sau Day 1–10 audit
Current authoritative CSV matrix có **19 peer-reviewed sources**. Kim et al. (2025, *BMC Health Services Research*) đã được thêm như closest methodological comparator vì dùng nhiều ML models + SHAP để dự báo unmet medical needs trên Korean Health Panel Survey. Điều này củng cố guardrail rằng ML/SHAP cho unmet medical needs không phải novelty tự thân.

## Guardrails
- Không claim first ever.
- SHAP không causal.
- `WTFA_A`-weighted ML không tự động là full design-based inference.
- Race/ethnicity là social/structural equity stratifier.
- NHIS 2024 cross-sectional: contemporaneous prediction, không future forecasting.
- Day 7 là working literature draft; các câu về SHAP/fairness nên được viết như planned/design components cho đến khi các analyses đó thật sự hoàn tất.

## Trạng thái Day 5–7 theo vai trò
### UIT — kỹ thuật
- Dataset/preprocessing v1: complete.
- Deterministic train/validation/test split: complete.
- Baseline Logistic Regression: complete.
- Conventional vs `WTFA_A`-weighted comparison: complete.
- RF/XGBoost đã được benchmark sớm ở Day 5, tức là đã làm trước một phần kế hoạch Day 8–10.

### UHS / collaborative literature
- Literature matrix 12–20 bài: complete với **19 bài** trong current authoritative CSV.
- Background + Related Work working draft: complete.

Hai nhánh trên cùng hỗ trợ bài nghiên cứu nhưng không nên gộp thành một loại công việc khi báo cáo phân công.
