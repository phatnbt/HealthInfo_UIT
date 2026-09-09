# NHẬT KÝ NGHIÊN CỨU NHIS 2024
## Day 14–16 — SHAP và giải thích mô hình đã khóa

**Nhóm thực hiện:** UIT — kỹ thuật

**Trạng thái:** HOÀN THÀNH DAY 14–16

**Phạm vi:** SHAP global, direction/dependence, interaction screen và subgroup explanation pattern cho LR, RF, XGBoost trên MEDNG và MEDDL

**Hiệu chỉnh ngày 09/09/2026:** sửa lỗi gắn nhãn `CHRONIC_BURDEN_CAT = 3+` trong bảng SHAP theo category. Đây là hiệu chỉnh lớp báo cáo, không thay đổi mô hình hoặc kết quả đánh giá đã khóa.

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
- Kiểm tra lại luồng tạo nhãn category sau khi phát hiện chuỗi `3+` bị ép sang số và nhận nhầm thành missing.
- Sửa hàm `cleaned_category()` để bảo toàn `3+` thành `code_3+`, đồng thời bổ sung validator đối chiếu trực tiếp với locked test.

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
12. Tách `code_3+` khỏi `Missing/special`; giữ missing trong bảng kiểm toán nhưng loại missing khỏi hai endpoint thấp nhất/cao nhất của direction summary.
13. Chạy validator Day 14–16 và kiểm tra lại code-freeze Day 20–22 sau hiệu chỉnh.

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

### Hiệu chỉnh `CHRONIC_BURDEN_CAT`

| Outcome | Nhóm `code_3+` | Missing thật |
|---|---:|---:|
| MEDNG | 1.172 | 46 |
| MEDDL | 1.172 | 46 |

- Số lượng trên được đếm trực tiếp từ locked test theo split `HHX`, không gắn thủ công theo từng mô hình.
- LR, RF và XGBoost có cùng số người trong mỗi outcome vì chúng dùng chung cohort test; giá trị SHAP vẫn được tính riêng cho từng mô hình.
- Direction sau sửa: MEDNG LR/RF thấp nhất `code_0`, cao nhất `code_2`; MEDNG XGBoost thấp nhất `code_0`, cao nhất `code_3+`; MEDDL LR/RF thấp nhất `code_0`, cao nhất `code_2`; MEDDL XGBoost thấp nhất `code_3+`, cao nhất `code_0`.
- `day14_16_shap_global_importance.csv`, `day14_16_shap_encoded_importance.csv` và sáu hàng audit tái lập mô hình không thay đổi.

## 6. Vấn đề phát sinh / lưu ý

- SHAP của LR/XGBoost nằm trên log-odds/raw-margin scale, còn RF trên positive-class probability scale; không so sánh độ lớn SHAP trực tiếp giữa model families.
- MEDDL dùng Platt cho performance đã khóa, nhưng SHAP giải thích base estimator trước lớp calibration đơn điệu.
- Correlated predictors có thể chia sẻ predictive information và làm thay đổi ranking.
- `HISPALLP_A` là social/structural equity stratifier, không phải biological cause.
- Các category hiện ghi raw public-use code; phải map bằng data dictionary trước khi viết manuscript.
- Interaction screen N=100 là exploratory, không phải kiểm định thống kê.
- Các nhóm N < 100 bị loại khỏi pattern table chính để tránh diễn giải bất ổn.
- SHAP/test output tuyệt đối không được dùng để tune lại model, feature, calibration hoặc threshold.
- Nguyên nhân lỗi là phép ép chuỗi category sang số: `0`, `1`, `2` chuyển được nhưng `3+` trở thành `NaN` rồi bị gắn `Missing/special`.
- `CHRONIC_BURDEN_CAT` là số miền bệnh mạn được chọn ở mức `0`, `1`, `2`, `3+`; không diễn giải đây là chỉ số mức độ nặng lâm sàng.

## 7. Quyết định / bước tiếp theo

- Giữ LR, RF và XGBoost cho bước fairness vì explanation pattern khác nhau giữa model.
- Không tuyên bố predictor “gây ra” MEDNG/MEDDL từ SHAP.
- Gửi các top predictor, direction/category pattern và interaction candidates cho UHS diễn giải theo y tế công cộng.
- Chuyển sang Day 17–19: fairness/error audit theo subgroup, gồm performance, calibration và error context.
- Day 17–19 phải kiểm tra trực tiếp chênh lệch metric; không được suy fairness từ SHAP importance.
- Yêu cầu UHS thay các hàng category/direction cũ của riêng `CHRONIC_BURDEN_CAT` bằng bản đã hiệu chỉnh; các kết luận global importance, encoded importance và hiệu suất mô hình được giữ nguyên.
- Mọi lần tái tạo Day 14–16 phải chạy `scripts/validate_day14_16_outputs.py`; pipeline phải dừng nếu `code_3+` bị gộp vào missing hoặc missing được chọn làm endpoint direction.

## 8. Sản phẩm tạo ra

- `scripts/day14_16_shap_explainability.py`
- `scripts/validate_day14_16_outputs.py`
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

**Kết luận trạng thái:** Day 14–16 hoàn thành đúng Gate 3; lỗi nhãn `CHRONIC_BURDEN_CAT = 3+` đã được sửa và kiểm tra hồi quy; SHAP chỉ được diễn giải là predictive attribution và pipeline vẫn khóa.
