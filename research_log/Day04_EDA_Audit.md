# Day 4 — Missing/code audit, EDA và final feature lock sau UHS review

## 1. Mục tiêu
Hoàn tất quality audit, weighted/subgroup EDA và khóa feature specification cuối cùng sau khi UHS/domain review phản hồi bộ 22 candidate predictors.

## 2. Công cụ sử dụng
- Python 3
- `csv`, `collections`, `hashlib`, `zipfile`
- NHIS 2024 Adult Codebook
- `adult24.csv`, `adultinc24.csv`
- `WTFA_A` survey weight
- UHS/domain predictor review

## 3. Phần Day 4 cốt lõi đã hoàn tất trước UHS
1. Audit observed codes vs expected codes cho 22 candidate predictors.
2. Xử lý missing/special codes theo từng biến; không dùng global rule `7/8/9 = missing`.
3. Tính unweighted và `WTFA_A`-weighted prevalence cho MEDNG/MEDDL.
4. Thực hiện subgroup EDA theo age, sex, race/ethnicity, poverty, insurance, food security, urban-rural.
5. Kiểm 10 income imputations và tạo descriptive poverty MI point estimates.

Kết quả:
- 22/22 predictor ban đầu không có unexpected code.
- MEDNG weighted prevalence ≈ 7.387%.
- MEDDL weighted prevalence ≈ 8.579%.
- MEDNG cohort N=32,354; MEDDL cohort N=32,355.

## 4. UHS review được tiếp thu
UHS đề xuất:
- Giữ 11 existing core predictors.
- Supporting: `MARSTAT_A`, `URBRRL23`, `REGION`.
- Không dùng cả bộ symptom/behavior variables trong primary model.
- Tạo chronic-condition burden thay vì gọi riêng diabetes + hypertension là toàn bộ chronic burden.
- Dùng `SMKCIGST_A` nếu cần smoking status; không dùng `SMKEV_A` như current smoking status.
- Dùng `POVRATTC_A` như SES sensitivity alternative với xử lý đúng 10 imputations.

Technical correction được giữ: `MARSTAT_A` codes 7/8/9 là các category hợp lệ của recode, không phải global missing codes.

## 5. Post-UHS technical audit
### 5.1 Chronic-condition burden
Đã prespecify 8 chronic-condition domains:
1. Hypertension — `HYPEV_A`
2. Cardiovascular disease — any positive của `CHDEV_A`, `ANGEV_A`, `MIEV_A`, `STREV_A`; chỉ tính 1 domain để tránh double-counting CVD
3. Asthma — `ASEV_A`
4. COPD — `COPDEV_A`
5. Cancer — `CANEV_A`
6. Diabetes — `DIBEV_A`
7. Arthritis — `ARTHEV_A`
8. Kidney disease — `KIDWEAKEV_A`

Tạo `CHRONIC_BURDEN_CAT` = `0`, `1`, `2`, `3+` selected domains.

Đây là **selected-condition count/category cho prediction**, không phải validated clinical severity index.

Nếu một domain không xác định được thì không mặc định là disease absent. Burden được để indeterminate/missing.

Kết quả:
- MEDNG indeterminate: 222 / 32,354 = 0.686%.
- MEDDL indeterminate: 222 / 32,355 = 0.686%.
- Tất cả component variables đều PASS code audit, không có unexpected observed code.

### 5.2 Smoking
`SMKCIGST_A` đã được audit và PASS.

Observed raw codes: `1,2,3,4,5,9` đúng với NHIS recode.
- 1–4: substantive smoking-status categories.
- 5/9: collapse thành explicit `Unknown` trong exploratory modeling.

`SMKEV_A` được DROP/REPLACED cho smoking-status construct.

### 5.3 Poverty MI sensitivity
`POVRATTC_A` được xác nhận:
- 10 imputations × 32,629 Sample Adults.
- Mỗi `HHX` có đúng `IMPNUM_A = 1..10`.
- Observed range 0.00–11.00 trong cả 10 imputations.

Protocol được khóa:
- Primary SES vẫn là `RATCAT_A`.
- Sensitivity: chạy 10 model riêng, mỗi model dùng một imputation của `POVRATTC_A`.
- Giữ cùng `HHX` train/test split giữa 10 imputations.
- Thay `RATCAT_A` bằng `POVRATTC_A`; không đưa cả hai vào cùng primary model.
- Tổng hợp 10 run theo mean/range/SD như sensitivity summary; không gọi là formal Rubin-pooled design-based inference nếu chưa triển khai đúng phương pháp MI + survey variance.

### 5.4 Fairness subgroup addendum
- Age groups cuối: 18–34, 35–49, 50–64, 65–74, 75+.
- Disability được giữ như exploratory equity subgroup.

## 6. Final feature lock
### Main — 12 constructs
Existing:
`AGEP_A`, `SEX_A`, `HISPALLP_A`, `EDUCP_A`, `RATCAT_A`, `EMPWRKLSW1_A`, `NOTCOV_A`, `FDSCAT3_A`, `PHSTAT_A`, `DISAB3_A`, `K6SPD_A`.

Engineered:
`CHRONIC_BURDEN_CAT`.

### Supporting
`MARSTAT_A`, `URBRRL23`, `REGION`.

### Exploratory/sensitivity
`BMICAT_A`, `ANXFREQ_A`, `DEPFREQ_A`, `LONELY_A`, `SOCSCLPAR_A`, `SMKCIGST_A`.

### Disease-specific sensitivity
`DIBEV_A`, `HYPEV_A` — không đưa đồng thời với chronic burden trong primary model.

### SES sensitivity
`POVRATTC_A` — MI-aware alternative cho `RATCAT_A`.

## 7. Interpretation guardrails
- Cross-sectional contemporaneous prediction/classification, không phải future forecasting.
- SHAP = predictive contribution, không phải causal effect.
- Correlated features có thể chia sẻ predictive information.
- Race/ethnicity là social/structural equity stratifier, không phải biological cause.
- Fairness/subgroup performance gaps không tự động chứng minh discrimination.
- `WTFA_A`, `PSTRAT`, `PPSU`, `HHX` không bao giờ là ML predictors.

## 8. Quyết định
**DAY 4 COMPLETE. DAY 5 GATE PASSED.**

Có thể bắt đầu preprocessing và train LR/RF/XGBoost độc lập cho:
- MEDNG primary cohort N=32,354.
- MEDDL secondary cohort N=32,355.

## 9. Sản phẩm
- `audit/final_feature_lock.csv`
- `audit/day4_post_uhs_variable_audit.csv`
- `audit/chronic_burden_summary.csv`
- `audit/poverty_MI_input_audit.csv`
- `audit/subgroup_EDA_post_UHS_addendum.csv`
- `docs/poverty_MI_sensitivity_protocol.md`
- `scripts/finalize_day4_post_uhs.py`
- Existing Day 1–4 audit outputs remain retained for provenance/history.
