# Day 6 — Literature matrix and evidence map

> **Role / ownership:** UHS / collaborative literature work under the original 4-week plan. This file is **not** an UIT technical Day 6 deliverable. It is retained in the shared repository because it supports the common paper and provides evidence for later interpretation.

## Mục tiêu
Hoàn thành literature matrix cho 5 cụm: Andersen/SDOH, cost-related unmet care, health equity, XAI/fairness, và complex-survey-aware modeling.

## Phân công theo kế hoạch gốc
- **UIT — kỹ thuật, Day 5–7:** preprocessing chống leakage, train/validation/test split, Logistic Regression baseline, thử weighting/class weight khi cần.
- **UHS — y tế/tổng quan, Day 5–7:** Background + Related Work và literature matrix 12–20 bài.

Vì vậy nội dung của file này thuộc nhánh **UHS / collaborative literature**, không được ghi nhận như công việc kỹ thuật chính của UIT.

## Đã làm
- Rà evidence pack cũ của project.
- Xác minh/bổ sung nguồn bằng PubMed, PMC, publisher và official CDC/HHS.
- Khóa **19 bài peer-reviewed** trong current authoritative CSV matrix.
- Bổ sung **Kim et al. (2025), BMC Health Services Research** — *Machine learning approach for unmet medical needs among middle-aged adults in South Korea: a cross-sectional study* — vì đây là closest methodological comparator trực tiếp cho ML prediction of unmet medical needs + SHAP.
- Tách official framework/data sources khỏi academic literature.
- Lập gap map để tránh novelty claim quá mức.

## Kết quả
19 bài vẫn nằm trong yêu cầu 12–20 bài của kế hoạch.
Review này là targeted narrative review, không phải PRISMA systematic review.

Current authoritative artifact:
- `literature/literature_matrix_day6.csv` — 19 sources.

Historical artifact retained for provenance:
- `literature/NHIS2024_Day6_Literature_Matrix_18.xlsx` — 18-source snapshot trước khi bổ sung Kim et al.; không dùng làm current source count.

## Research gap
Không viết “chưa ai dùng ML cho unmet healthcare”. Kim et al. (2025) là một counterexample trực tiếp cho ML + SHAP trong unmet medical needs.

Gap an toàn: joint integration của NHIS 2024 **cost-related** unmet/delayed care + survey-weight sensitivity + subgroup performance/fairness + subgroup-specific explainability trong cùng một design.

## Liên hệ với nhánh UIT kỹ thuật
Literature matrix có thể được UIT dùng để kiểm tra tính hợp lý của interpretation, sensitivity analysis, metric framing và Discussion. Sau Day 4, main 12-construct specification đã được khóa trước modeling; literature update không được dùng để silently reopen feature selection hoặc Day 8–10 test-driven tuning.

## AI disclosure
AI hỗ trợ tìm kiếm, tổng hợp, cấu trúc matrix và soạn nháp. Nguồn học thuật/official đến từ bên ngoài; citation/DOI/claim chính được đối chiếu với PubMed/PMC/publisher/official pages. Người nghiên cứu chịu trách nhiệm kiểm tra lại trước khi nộp.
