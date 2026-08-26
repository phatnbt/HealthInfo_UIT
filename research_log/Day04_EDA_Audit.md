# Day 4 — Missing/code audit và EDA

## 1. Mục tiêu
Kiểm chất lượng coding/missing của 22 predictors ban đầu và thực hiện exploratory data analysis cho hai outcome trước khi train model.

## 2. Công cụ sử dụng
- Python 3
- `csv`, `collections`, `statistics`
- Excel
- NHIS 2024 Adult Codebook
- `WTFA_A` survey weight
- `adultinc24.csv` cho poverty multiple imputation

## 3. Các bước xử lý
1. Lấy observed codes của từng predictor và so với expected codes từ codebook.
2. Xây dựng missing/special-code rule theo từng biến; không dùng global rule `7/8/9 = missing`.
3. Tính special/missing N và % cho raw, MEDNG cohort và MEDDL cohort.
4. Tính unweighted và WTFA_A-weighted prevalence cho MEDNG/MEDDL.
5. Thực hiện subgroup EDA theo Age, Sex, Race/ethnicity, Poverty, Insurance, Food security, Urban-rural.
6. Với mỗi subgroup lưu N, positive N, unweighted prevalence, weighted prevalence.
7. Kiểm 10 income imputations và tính poverty estimate riêng ở từng imputation; tạo descriptive MI-pooled point estimate bằng trung bình 10 estimates.

## 4. Kết quả
- 22/22 predictors ban đầu không có unexpected code so với tập expected đã audit.
- MEDNG weighted prevalence ≈ 7.387%.
- MEDDL weighted prevalence ≈ 8.579%.
- Hoàn thành exact subgroup EDA cho cả hai independent cohorts.

## 5. Vấn đề / lưu ý
- `WTFA_A` weighted estimate là point estimate; formal SE/CI cần `PSTRAT + PPSU`.
- Poverty MI pooled ở Day 4 là descriptive point estimate, chưa phải Rubin + Taylor confidence interval.
- Không suy diễn association hoặc subgroup gap thành causality/discrimination.
- UHS review sau Day 4 đề xuất thay đổi scientific feature specification; điều này không làm mất hiệu lực của audit lịch sử trên 22 candidate predictors, nhưng các feature mới phải được audit lại trước modeling.

## 6. Quyết định sau UHS review
Data-side Day 1–4 hoàn tất và **chưa train AI**.

UHS/domain review đã được chấp nhận về định hướng. Trước Day 5 cần hoàn tất technical gate:
1. Define + audit chronic-condition burden.
2. Audit `SMKCIGST_A` nếu giữ smoking; `SMKEV_A` không còn là smoking-status operationalization ưu tiên.
3. Lock multiple-imputation strategy cho `POVRATTC_A` sensitivity analysis.
4. Re-run code/missing audit cho mọi biến/feature mới.
5. Freeze final main/supporting/exploratory feature set.

Provisional main set hiện có 11 existing predictors; chronic-condition burden sẽ là main construct bổ sung nếu vượt technical audit.

## 7. Sản phẩm
- `subgroup_EDA_EXACT.csv`
- `predictor_code_missing_audit.csv`
- `poverty_MI_10_imputations_detail.csv`
- `poverty_MI_pooled_point_estimates.csv`
- `AUDIT_MANIFEST.json`
- `NHIS2024_UIT_Day1_4_FINAL.xlsx`
- `docs/UHS_Day3_4_predictor_review.md`
