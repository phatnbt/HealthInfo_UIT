# Day 4 — Missing/code audit và EDA

## 1. Mục tiêu
Kiểm chất lượng coding/missing của 22 predictors và thực hiện exploratory data analysis cho hai outcome trước khi train model.

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
- 22/22 predictors không có unexpected code so với tập expected đã audit.
- MEDNG weighted prevalence ≈ 7.387%.
- MEDDL weighted prevalence ≈ 8.579%.
- Hoàn thành exact subgroup EDA cho cả hai independent cohorts.

## 5. Vấn đề / lưu ý
- `WTFA_A` weighted estimate là point estimate; formal SE/CI cần `PSTRAT + PPSU`.
- Poverty MI pooled ở Day 4 là descriptive point estimate, chưa phải Rubin + Taylor confidence interval.
- Không suy diễn association hoặc subgroup gap thành causality/discrimination.

## 6. Quyết định
Data-side Day 1–4 hoàn tất. Chưa train AI ở giai đoạn này. Bước tiếp theo: UHS final feature review → final predictor lock → preprocessing/modeling.

## 7. Sản phẩm
- `subgroup_EDA_EXACT.csv`
- `predictor_code_missing_audit.csv`
- `poverty_MI_10_imputations_detail.csv`
- `poverty_MI_pooled_point_estimates.csv`
- `AUDIT_MANIFEST.json`
- `NHIS2024_UIT_Day1_4_FINAL.xlsx`
