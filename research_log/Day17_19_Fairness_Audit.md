# NHẬT KÝ NGHIÊN CỨU NHIS 2024
## Day 17–19 — Fairness, calibration và error-rate audit theo subgroup

**Nhóm thực hiện:** UIT — kỹ thuật

**Trạng thái:** HOÀN THÀNH DAY 17–19

**Phạm vi:** Audit LR, RF, XGBoost đã khóa cho MEDNG và MEDDL theo race/ethnicity, poverty, insurance, sex và age; báo cáo weighted–unweighted song song

## 1. Mục tiêu trong ngày

- Thực hiện fairness audit đúng kế hoạch 4 tuần mà không mở lại vòng tuning.
- Đánh giá AUPRC, AUROC, Recall, FNR, FPR, Specificity, Precision, F1, Brier và calibration theo subgroup.
- Dùng `WTFA_A` cho ước lượng population-relevant và giữ unweighted làm sensitivity.
- Chỉ tính chênh lệch khi subgroup có đủ cỡ mẫu/số ca dương/số ca âm.
- Kiểm tra Equal Opportunity ở dạng TPR/Recall span khi phù hợp, đồng thời báo FPR riêng.
- Không kết luận “công bằng/không công bằng” chỉ từ một metric.

## 2. Công việc đã thực hiện

- Khôi phục đúng cohort hậu-UHS có `CHRONIC_BURDEN_CAT` và đối chiếu split đã khóa.
- Tái dựng 6 estimator: 2 outcome × 3 model.
- Áp dụng đúng Raw/Platt và threshold đã chọn từ validation Day 8–10.
- Audit 5 axis thuộc 4 miền equity của plan: race/ethnicity, income/poverty, insurance, và demographic sex/age.
- Tính metric subgroup weighted và unweighted trên locked test.
- Chạy 400 stratified-PSU bootstrap trong từng `PSTRAT` cho metric và disparity span.
- Áp dụng stability gate: N ≥ 100, positive N ≥ 20, negative N ≥ 20.
- Tạo bảng skipped để không che giấu nhóm chưa đủ dữ liệu.
- Tạo heatmap FNR/FPR span và biểu đồ calibration-in-the-large.
- Viết validator độc lập cho metric invariant, bootstrap, disparity recomputation, privacy và manifest.

## 3. Công cụ sử dụng

- Python 3.12.
- `scikit-learn==1.8.0`.
- `xgboost==3.0.4`.
- `numpy==2.3.5`, `pandas==2.2.3`, `scipy==1.17.0`, `matplotlib==3.10.8`.
- Git/GitHub và Graphify để quản lý phiên bản và knowledge graph.

## 4. Các bước xử lý

1. Nạp hai cohort MEDNG/MEDDL hậu-UHS và artifact khóa Day 8–10/Day 11–13.
2. Xác nhận `HHX` duy nhất, survey field đầy đủ, `WTFA_A > 0`, và đúng số dòng/positive từng split.
3. Fit preprocessing chỉ trên train; tái dựng LR/RF/XGBoost bằng hyperparameter đã khóa.
4. Fit lại Platt trên validation calibration role cho MEDDL; MEDNG giữ Raw.
5. So sánh lại unweighted với Day 8–10 và weighted với đúng arm Day 11–13.
6. Tạo subgroup labels prespecified; không gộp nhóm sau khi nhìn outcome.
7. Loại comparative metric nếu N < 100, positive N < 20 hoặc negative N < 20.
8. Tính metric với cùng threshold cho mọi subgroup; không tối ưu threshold theo nhóm.
9. Bootstrap PSU trong `PSTRAT`, 400 lần, cho cả weighted và unweighted sensitivity.
10. Tính unsigned max-minus-min span; dùng Recall span làm descriptive Equal Opportunity signal và giữ FPR riêng.
11. Chạy validator và kiểm tra trực quan bốn SVG.

## 5. Kết quả

### Audit tái lập và QA

- PASS 12/12 reference rows.
- Sai khác metric lớn nhất: `3,33e-16`, nhỏ hơn tolerance `1e-08`.
- 168 dòng subgroup performance đủ điều kiện; 48 dòng skipped theo outcome–model–axis–group.
- Tất cả subgroup/gap CI có 400/400 replicate hợp lệ.
- `Recall + FNR = 1` và `Specificity + FPR = 1` cho mọi dòng.
- Không xuất `HHX`, person-level probability hoặc person-level prediction.

### Phát hiện kỹ thuật chính

| Outcome | Model | Insurance Recall span | Insurance FPR span | Insurance AUROC span |
|---|---:|---:|---:|---:|
| MEDNG | LR | 0.584 | 0.526 | 0.008 |
| MEDNG | RF | 0.641 | 0.883 | 0.018 |
| MEDNG | XGBoost | 0.469 | 0.367 | 0.038 |
| MEDDL | LR | 0.535 | 0.495 | 0.010 |
| MEDDL | RF | 0.431 | 0.808 | 0.004 |
| MEDDL | XGBoost | 0.540 | 0.571 | 0.062 |

- Insurance là tín hiệu threshold-level lớn nhất: AUROC giữa insured/uninsured khá gần nhưng Recall/FPR rất khác tại threshold khóa.
- RF gán positive cho toàn bộ nhóm uninsured ở MEDDL: Recall = 1.000 và FPR = 1.000. Với MEDNG, RF có Recall = 1.000 và FPR = 0.975 ở uninsured.
- Weighted prevalence uninsured cao hơn insured: MEDNG 25,7% so với 5,1%; MEDDL 27,7% so với 6,9%. Vì vậy AUPRC/Brier gap không được đọc độc lập.
- Age có Recall span đáng kể: MEDNG 0.307–0.487; MEDDL 0.213–0.405. Nhóm 75+ chưa đủ positive để so sánh ổn định.
- Poverty và race/ethnicity có chênh lệch vừa phải theo model; chỉ Hispanic, NH White và NH Black đủ gate cho race/ethnicity comparison.
- Sex có point-estimate gap nhỏ hơn insurance và age; điều này không tương đương bằng chứng “không có disparity”.
- Weighted và unweighted không giống hệt nhau; khác biệt nổi bật nhất nằm ở một số AUPRC span. Kết luận phải trình bày cả hai.
- Không có model nào tốt nhất đồng thời cho mọi outcome, axis và metric; Day 17–19 không tạo “winner”.

## 6. Vấn đề phát sinh / lưu ý

- Threshold là F1 operating point từ validation, không phải clinical cutoff; không được dùng như chỉ định can thiệp.
- Insurance vừa là predictor vừa là equity axis. Chênh lệch lớn cần kiểm tra kỹ, nhưng chưa chứng minh discrimination hay nguyên nhân xã hội.
- AUPRC phụ thuộc prevalence; Brier cũng chịu ảnh hưởng prevalence/calibration.
- Gap CI là CI mô tả độ lớn unsigned span, không phải kiểm định equality và không cho biết hướng privileged/unprivileged.
- NH Asian, NH AIAN, NH AIAN + other, other/multiple và age 75+ thiếu positive events trong locked test; không được suy rộng kết luận sang các nhóm này.
- 400-PSU bootstrap là survey-aware sensitivity, không phải official NCHS replicate-weight variance.
- Không được dùng kết quả subgroup test để tune model/feature/calibration/threshold hoặc chọn winner hậu nghiệm.

## 7. Quyết định / bước tiếp theo

- Giữ LR, RF và XGBoost để so sánh minh bạch; chưa chọn winner.
- Đánh dấu RF–insurance operating point là vấn đề ưu tiên cho Day 20–21.
- Day 20–21 thực hiện false-negative/false-positive error analysis và robustness checklist, đặc biệt theo insurance và age.
- Không đổi primary locked analysis; mọi sensitivity phải được ghi riêng.
- Gửi UHS bảng disparity, CI, skipped groups và interpretation notes để đồng diễn giải health equity.

## 8. Sản phẩm tạo ra

- `scripts/day17_19_fairness_audit.py`
- `scripts/validate_day17_19_outputs.py`
- `modeling/day17_19/day17_19_subgroup_performance.csv`
- `modeling/day17_19/day17_19_subgroup_metric_cluster_bootstrap_ci.csv`
- `modeling/day17_19/day17_19_disparity_summary.csv`
- `modeling/day17_19/day17_19_disparity_cluster_bootstrap_ci.csv`
- `modeling/day17_19/day17_19_subgroup_skipped.csv`
- `modeling/day17_19/day17_19_locked_reproduction_audit.csv`
- `modeling/day17_19/day17_19_split_audit.csv`
- `modeling/day17_19/day17_19_config_log.json`
- 4 SVG trong `modeling/day17_19/figures/`.
- `docs/Day17_19_Fairness_Methodological_Rationale.md`
- `research_log/Day17_19_Fairness_Audit.md`

**Kết luận trạng thái:** Day 17–19 hoàn thành; Gate 4 chưa hoàn tất cho tới khi làm xong error analysis/robustness Day 20–21.
