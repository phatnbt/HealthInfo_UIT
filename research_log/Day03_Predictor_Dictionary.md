# Day 3 — Data dictionary và 22 candidate predictors

## 1. Mục tiêu
Lập danh sách candidate predictors, kiểm chính xác ý nghĩa/coding từ NHIS data dictionary và tổ chức biến theo conceptual framework trước modeling.

## 2. Công cụ sử dụng
- NHIS 2024 Adult Codebook
- Python
- Excel
- Andersen Behavioral Model of Health Services Use
- Healthy People 2030 SDOH
- Literature review
- UHS/domain review để chốt interpretation và KEEP/DROP

## 3. Các bước xử lý
1. Lập 22 candidate predictors: `AGEP_A`, `SEX_A`, `HISPALLP_A`, `EDUCP_A`, `MARSTAT_A`, `RATCAT_A`, `EMPWRKLSW1_A`, `NOTCOV_A`, `FDSCAT3_A`, `REGION`, `URBRRL23`, `PHSTAT_A`, `DISAB3_A`, `DIBEV_A`, `HYPEV_A`, `BMICAT_A`, `K6SPD_A`, `ANXFREQ_A`, `DEPFREQ_A`, `LONELY_A`, `SOCSCLPAR_A`, `SMKEV_A`.
2. Với từng biến, kiểm: variable name → meaning/question wording → codes → special/missing codes → observed codes → role dự kiến.
3. Map theo Andersen:
   - Predisposing: AGEP_A, SEX_A, HISPALLP_A, EDUCP_A, MARSTAT_A.
   - Enabling/contextual: RATCAT_A, EMPWRKLSW1_A, NOTCOV_A, FDSCAT3_A, REGION, URBRRL23.
   - Need: PHSTAT_A, DISAB3_A, DIBEV_A, HYPEV_A, BMICAT_A, K6SPD_A, ANXFREQ_A, DEPFREQ_A.
   - Supplementary social/behavioral: LONELY_A, SOCSCLPAR_A, SMKEV_A.
4. Phân loại tạm thời Core / Supporting / Exploratory-Optional dựa trên framework và literature, không dựa vào SHAP.
5. Đánh dấu các biến có nguy cơ diễn giải sai để UHS review kỹ.

## 4. Kết quả
Hoàn thành technical dictionary cho 22 candidate predictors và xác định được role/domain dự kiến.

## 5. Vấn đề / lưu ý
- Candidate set chưa đồng nghĩa với final feature set.
- Race/ethnicity cần diễn giải như social/structural stratifier, không phải nguyên nhân sinh học.
- `NOTCOV_A` là access/enabling predictor gần outcome nhưng không phải leakage trực tiếp.
- SHAP sau này chỉ được diễn giải là predictive contribution, không phải causal effect.

## 6. Quyết định
Trước Day 5 cần UHS review để chốt `KEEP / DROP / SENSITIVITY` cho final predictor set.

## 7. Sản phẩm
- `predictor_code_missing_audit.csv`
- Sheets `Predictor_Audit`, `Design_Lock`
- UHS review package
