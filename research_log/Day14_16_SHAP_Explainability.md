# NHẬT KÝ NGHIÊN CỨU NHIS 2024
## Day 14–16 — SHAP và giải thích mô hình đã khóa

**Nhóm thực hiện:** UIT — kỹ thuật

**Trạng thái:** HOÀN THÀNH DAY 14–16

**Phạm vi:** SHAP global, direction/dependence, interaction screen và subgroup explanation pattern cho LR, RF, XGBoost trên MEDNG và MEDDL

## 1. Mục tiêu trong ngày

- Giải thích cả ba mô hình đã giữ lại vì Day 8–13 chưa xác lập universal winner.
- Xác định predictor construct quan trọng ở mức global cho MEDNG và MEDDL.
- Mô tả hướng hoặc pattern theo category mà không biến SHAP thành quan hệ nhân quả.
- Sàng lọc interaction cần thiết cho RF và XGBoost.
- So sánh SHAP pattern theo các nhóm health equity ưu tiên, nhưng chưa thực hiện fairness audit.
- Đạt Gate 3: mọi hình phải gắn rõ outcome, model, split và explained output.

## 2. Công việc đã thực hiện

- Tái dựng sáu estimator đã khóa: 2 outcome × 3 model.
- Audit lại toàn bộ locked-test performance trước khi chạy SHAP.
- Chạy SHAP trên toàn bộ 6.417 dòng test MEDNG và 6.419 dòng test MEDDL.
- Gộp các cột one-hot về đúng 12 predictor constructs.
- Tính global importance theo hai cách: unweighted và `WTFA_A`-weighted.
- Tạo summary plot, construct-level dependence plot và bảng direction/category pattern.
- Chạy TreeSHAP interaction screen cho RF/XGBoost trên mẫu test cố định 100 dòng.
- So sánh explanation pattern theo `HISPALLP_A`, `RATCAT_A`, `NOTCOV_A`, `SEX_A` và nhóm tuổi.
- Loại các subgroup level có N < 100 khỏi bảng pattern chính và lưu audit riêng.
- Chỉ lưu bảng/hình tổng hợp; không lưu `HHX`, prediction hoặc SHAP cấp cá nhân.

## 3. Công cụ sử dụng

- Python 3.12.
- `shap==0.52.0`.
- `xgboost==3.0.4`.
- `scikit-learn==1.8.0`.
- `numpy`, `pandas`, `scipy`, `matplotlib`.
- Git/GitHub và Graphify để quản lý phiên bản và cập nhật knowledge graph.

## 4. Các bước xử lý

1. Nạp cohort MEDNG/MEDDL và các artifact khóa của Day 8–10.
2. Xác nhận `HHX` duy nhất và split train–validation–test không drift.
3. Fit preprocessing chỉ trên train và dựng LR/RF/XGBoost bằng hyperparameter đã khóa.
4. Tái fit Platt trên validation calibration role để audit MEDDL; không dùng Platt làm mục tiêu SHAP.
5. So sánh lại bảy metric locked-test với tolerance `1e-08`.
6. Dùng LinearExplainer cho LR và TreeExplainer cho RF/XGBoost.
7. Tính SHAP trên locked test; gộp one-hot contribution về 12 constructs.
8. Tổng hợp mean absolute SHAP unweighted và `WTFA_A`-weighted.
9. Tạo direction/dependence output; category chỉ ghi raw public-use code.
10. Sàng lọc interaction cho hai tree models và tạo subgroup pattern tables.
11. Kiểm tra hình SVG, cấu hình chạy, quyền riêng tư và protocol non-retuning.

## 5. Kết quả

### Audit tái lập

- PASS 6/6 outcome–model rows.
- Sai khác metric lớn nhất: `1.11e-16`, nhỏ hơn tolerance `1e-08`.
- Không phát hiện split, probability-version, threshold hoặc model drift.

### Top-five constructs theo `WTFA_A`-weighted mean absolute SHAP

| Outcome | Model | Top five |
|---|---|---|
| MEDNG | LR | `PHSTAT_A`, `AGEP_A`, `EMPWRKLSW1_A`, `NOTCOV_A`, `FDSCAT3_A` |
| MEDNG | RF | `FDSCAT3_A`, `NOTCOV_A`, `AGEP_A`, `EMPWRKLSW1_A`, `K6SPD_A` |
| MEDNG | XGBoost | `HISPALLP_A`, `K6SPD_A`, `NOTCOV_A`, `FDSCAT3_A`, `CHRONIC_BURDEN_CAT` |
| MEDDL | LR | `AGEP_A`, `PHSTAT_A`, `EMPWRKLSW1_A`, `FDSCAT3_A`, `EDUCP_A` |
| MEDDL | RF | `NOTCOV_A`, `FDSCAT3_A`, `AGEP_A`, `EMPWRKLSW1_A`, `PHSTAT_A` |
| MEDDL | XGBoost | `HISPALLP_A`, `K6SPD_A`, `RATCAT_A`, `NOTCOV_A`, `FDSCAT3_A` |

- Weighted–unweighted rank correlation: 0.979–1.000.
- Top-five overlap: 4–5/5 constructs.
- Mỗi model nhấn mạnh predictor khác nhau; SHAP không tạo ra một universal explanation hoặc universal winner.
- Interaction đứng đầu lần lượt là MEDNG–RF `EMPWRKLSW1_A × FDSCAT3_A`, MEDNG–XGBoost `RATCAT_A × FDSCAT3_A`, MEDDL–RF `NOTCOV_A × CHRONIC_BURDEN_CAT`, MEDDL–XGBoost `EDUCP_A × RATCAT_A`.
- Explanation pattern thay đổi ở một số subgroup; đây chưa phải bằng chứng về fairness hay discrimination.

## 6. Vấn đề phát sinh / lưu ý

- SHAP của LR/XGBoost nằm trên log-odds/raw-margin scale, còn RF trên positive-class probability scale; không so sánh độ lớn SHAP trực tiếp giữa model families.
- MEDDL dùng Platt cho performance đã khóa, nhưng SHAP giải thích base estimator trước lớp calibration đơn điệu.
- Correlated predictors có thể chia sẻ predictive information và làm thay đổi ranking.
- `HISPALLP_A` là social/structural equity stratifier, không phải biological cause.
- Các category hiện ghi raw public-use code; phải map bằng data dictionary trước khi viết manuscript.
- Interaction screen N=100 là exploratory, không phải kiểm định thống kê.
- Các nhóm N < 100 bị loại khỏi pattern table chính để tránh diễn giải bất ổn.
- SHAP/test output tuyệt đối không được dùng để tune lại model, feature, calibration hoặc threshold.

## 7. Quyết định / bước tiếp theo

- Giữ LR, RF và XGBoost cho bước fairness vì explanation pattern khác nhau giữa model.
- Không tuyên bố predictor “gây ra” MEDNG/MEDDL từ SHAP.
- Gửi các top predictor, direction/category pattern và interaction candidates cho UHS diễn giải theo y tế công cộng.
- Chuyển sang Day 17–19: fairness/error audit theo subgroup, gồm performance, calibration và error context.
- Day 17–19 phải kiểm tra trực tiếp chênh lệch metric; không được suy fairness từ SHAP importance.

## 8. Sản phẩm tạo ra

- `scripts/day14_16_shap_explainability.py`
- `modeling/day14_16/day14_16_shap_global_importance.csv`
- `modeling/day14_16/day14_16_shap_encoded_importance.csv`
- `modeling/day14_16/day14_16_shap_direction_summary.csv`
- `modeling/day14_16/day14_16_shap_category_patterns.csv`
- `modeling/day14_16/day14_16_shap_interaction_screen.csv`
- `modeling/day14_16/day14_16_shap_subgroup_patterns.csv`
- `modeling/day14_16/day14_16_shap_subgroup_skipped.csv`
- `modeling/day14_16/day14_16_locked_reproduction_audit.csv`
- `modeling/day14_16/day14_16_config_log.json`
- 20 SVG figures trong `modeling/day14_16/figures/`.
- `docs/Day14_16_SHAP_Methodological_Rationale.md`
- `research_log/Day14_16_SHAP_Explainability.md`

**Kết luận trạng thái:** Day 14–16 hoàn thành đúng Gate 3; SHAP chỉ được diễn giải là predictive attribution và pipeline vẫn khóa.
