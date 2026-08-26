# Day 3 — Data dictionary và candidate predictors

## 1. Mục tiêu
Lập danh sách candidate predictors, kiểm chính xác ý nghĩa/coding từ NHIS data dictionary, tổ chức biến theo conceptual framework và nhận domain review trước modeling.

## 2. Công cụ sử dụng
- NHIS 2024 Adult Codebook
- Python
- Excel
- Andersen Behavioral Model of Health Services Use
- Healthy People 2030 SDOH
- Literature review
- UHS/domain review

## 3. Các bước xử lý
1. Lập 22 candidate predictors ban đầu: `AGEP_A`, `SEX_A`, `HISPALLP_A`, `EDUCP_A`, `MARSTAT_A`, `RATCAT_A`, `EMPWRKLSW1_A`, `NOTCOV_A`, `FDSCAT3_A`, `REGION`, `URBRRL23`, `PHSTAT_A`, `DISAB3_A`, `DIBEV_A`, `HYPEV_A`, `BMICAT_A`, `K6SPD_A`, `ANXFREQ_A`, `DEPFREQ_A`, `LONELY_A`, `SOCSCLPAR_A`, `SMKEV_A`.
2. Với từng biến, kiểm: variable name → meaning/question wording → codes → special/missing codes → observed codes → role dự kiến.
3. Map theo Andersen/context:
   - Predisposing: AGEP_A, SEX_A, HISPALLP_A, EDUCP_A, MARSTAT_A.
   - Enabling/material: RATCAT_A, EMPWRKLSW1_A, NOTCOV_A, FDSCAT3_A.
   - Contextual: REGION, URBRRL23.
   - Need/health/functioning: PHSTAT_A, DISAB3_A, DIBEV_A, HYPEV_A, BMICAT_A, K6SPD_A, ANXFREQ_A, DEPFREQ_A.
   - Supplementary social/behavioral: LONELY_A, SOCSCLPAR_A, SMKEV_A.
4. UHS rà từng biến theo ý nghĩa y tế, nguy cơ overlap, nguy cơ diễn giải sai và mức độ phù hợp với main model.
5. Đối chiếu các đề xuất UHS với NHIS 2024 codebook trước khi cập nhật scientific plan.

## 4. Kết quả UHS review

### Provisional main predictors — 11 existing variables
- `AGEP_A`
- `SEX_A`
- `HISPALLP_A`
- `EDUCP_A`
- `RATCAT_A`
- `EMPWRKLSW1_A`
- `NOTCOV_A`
- `FDSCAT3_A`
- `PHSTAT_A`
- `DISAB3_A`
- `K6SPD_A`

### Supporting/contextual
- `MARSTAT_A`
- `URBRRL23`
- `REGION`

### Exploratory/sensitivity
- `DIBEV_A`
- `HYPEV_A`
- `BMICAT_A`
- `ANXFREQ_A`
- `DEPFREQ_A`
- `LONELY_A`
- `SOCSCLPAR_A`

`SMKEV_A` không còn là operationalization ưu tiên cho smoking status. Nếu giữ smoking, sẽ audit và dùng `SMKCIGST_A`.

### Planned additions before final lock
- Chronic-condition burden được định nghĩa trước và audit kỹ; nếu đạt yêu cầu sẽ trở thành main construct bổ sung.
- `POVRATTC_A` là sensitivity alternative cho SES/poverty và phải xử lý cấu trúc 10 imputations.
- `SMKCIGST_A` là exploratory smoking-status candidate nếu smoking được giữ.

## 5. Technical correction / lưu ý
- Không dùng global rule `7/8/9 = missing`.
- Đặc biệt `MARSTAT_A` codes 7/8/9 là các category hợp lệ trong recode 2024 (Never married / Living with a partner / Unknown marital status), không được tự động đổi thành missing.
- `EMPWRKLSW1_A` là NHIS recode có logic rộng hơn cách hiểu đơn giản “paid employment last week”; dùng concept `employment/work status`.
- `SMKEV_A` chỉ đo ever smoked ≥100 cigarettes, không phải current smoking status.
- `SOCSCLPAR_A` phản ánh difficulty participating in social activities due to a physical/mental/emotional condition, không phải pure social participation.
- `PHSTAT_A`, `K6SPD_A`, `DISAB3_A` là health/functioning constructs; không diễn giải như causal determinants.

## 6. Quyết định
UHS review được **chấp nhận về định hướng**, nhưng final feature lock chưa hoàn tất vì các biến/feature mới cần technical audit.

Provisional gate to Day 5:
1. Define + audit chronic-condition burden.
2. Audit `SMKCIGST_A` nếu smoking được giữ.
3. Lock MI strategy cho `POVRATTC_A` sensitivity.
4. Freeze final main/supporting/exploratory feature specification.

Nếu chronic-condition burden được chấp nhận sau audit, final main model sẽ có **12 core constructs** thay vì 11.

## 7. Interpretation lock
- Race/ethnicity = social/structural equity stratifier, không phải biological cause.
- `NOTCOV_A`, poverty, K6, disability và các predictors khác không được diễn giải causal từ model/SHAP.
- SHAP = predictive contribution, không phải independent etiologic effect.
- Cross-sectional NHIS ML = contemporaneous classification/prediction, không phải future-risk forecasting.

## 8. Sản phẩm
- `predictor_code_missing_audit.csv`
- Sheets `Predictor_Audit`, `Design_Lock`
- UHS review package
- `docs/UHS_Day3_4_predictor_review.md`
