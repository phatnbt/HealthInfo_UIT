# NHẬT KÝ NGHIÊN CỨU NHIS 2024
## Day 20–22 — Error analysis, robustness và đóng băng code bước đầu

**Nhóm thực hiện:** UIT — kỹ thuật

**Trạng thái:** HOÀN THÀNH DAY 20–22

**Phạm vi:** false negative/false positive, threshold/seed/missingness robustness, composite sensitivity, leakage review và SHA-256 code freeze

## 1. Mục tiêu trong ngày

- Hoàn tất Gate 4 sau fairness audit Day 17–19.
- Phân tích false negatives và false positives mà không xuất dữ liệu từng người.
- Kiểm tra độ bền với threshold, random seed và missingness.
- Hoàn thành sensitivity target `MEDNG OR MEDDL` trong kế hoạch gốc.
- Rà leakage lần cuối và tạo manifest đóng băng code đến Day 22.
- Chuẩn bị bảng/hình cùng bản Methods–Results có thể truy ngược.

## 2. Công việc đã thực hiện

- Tái dựng đúng 6 model-outcome đã khóa và xác nhận lại split, preprocessing, Raw/Platt và threshold.
- Tạo overall error table weighted/unweighted cho 2 outcome × 3 model.
- Tạo 168 dòng error profile aggregate cho các subgroup đủ stability gate.
- Chạy threshold perturbation ở 0,8×, 1,0× và 1,2× threshold khóa.
- Chạy seed sensitivity với 2026, 2037 và 2048, không chọn seed theo test.
- Audit missingness 12 constructs trên train/validation/test và so sánh hai test strata mà không refit.
- Tạo common cohort và chạy sensitivity `TARGET_FORGONE_COST OR TARGET_DELAYED_COST` bằng hyperparameter MEDNG đã khóa, không tuning composite.
- Chạy 10 leakage/integrity checks.
- Tạo 3 bảng rút gọn Day 22, 2 SVG và code-freeze manifest 29 file.
- Viết validator độc lập kiểm tra schema riêng tư, invariant, reproduction và hash.

## 3. Công cụ sử dụng

- Python 3.12.
- `numpy`, `pandas`, `scikit-learn`, `xgboost`, `matplotlib` theo `requirements.txt`.
- Git để theo dõi thay đổi; SHA-256 để đóng băng trạng thái tính toán.
- Graphify để truy ngược quan hệ giữa locked model, survey sensitivity, SHAP, fairness và validator.

## 4. Các bước xử lý

1. Đọc plan Day 20–22 và xác định ranh giới không được mở lại tuning.
2. Chạy validator Day 17–19 trước khi dùng output làm đầu vào.
3. Nạp hai cohort hậu-UHS; xác nhận `HHX` duy nhất, survey fields đầy đủ và trọng số dương.
4. Tái tạo split Day 5; kiểm tra không giao nhau và đúng số dòng/positive.
5. Fit preprocessing trên train, transform validation/test.
6. Tái dựng estimator bằng hyperparameter khóa; dùng validation calibration role cho Platt khi đã khóa.
7. Tính confusion/error metrics weighted và unweighted trên locked test.
8. Tổng hợp error profile theo 5 axes nhưng chỉ lưu subgroup đủ N/positive/negative gate.
9. Chạy threshold, seed và missingness sensitivity theo quy tắc định trước.
10. Inner join hai outcome cohort bằng `HHX` trong bộ nhớ để tạo common composite cohort; không xuất ID.
11. Chạy composite model với MEDNG hyperparameters, lựa chọn probability/threshold chỉ bằng validation.
12. Xuất bảng/hình aggregate, config, code-freeze manifest; chạy validator.

## 5. Kết quả

### QA và Gate 4

- PASS toàn bộ Day 17–19 validator trước khi chạy.
- PASS Day 20–22 validator.
- 12 overall error rows, 168 eligible aggregate subgroup profiles.
- 36 threshold rows, 36 seed rows, 72 feature-split missingness rows và 24 missingness-performance rows.
- Threshold factor 1,0 và seed 2026 tái lập toàn bộ 12 reference arms.
- 10/10 leakage/integrity checks PASS.
- 29/29 code/output hash entries khớp.
- Không lưu `HHX`, person-level probability hoặc person-level prediction.

### Error trade-off weighted

| Outcome | Model | FNR | FPR | Recall | Precision | F1 |
|---|---:|---:|---:|---:|---:|---:|
| MEDNG | LR | 0,504 | 0,100 | 0,496 | 0,275 | 0,354 |
| MEDNG | RF | 0,417 | 0,159 | 0,583 | 0,218 | 0,317 |
| MEDNG | XGBoost | 0,562 | 0,074 | 0,438 | 0,310 | 0,363 |
| MEDDL | LR | 0,535 | 0,090 | 0,465 | 0,334 | 0,389 |
| MEDDL | RF | 0,301 | 0,255 | 0,699 | 0,211 | 0,324 |
| MEDDL | XGBoost | 0,467 | 0,126 | 0,533 | 0,292 | 0,377 |

- RF giảm false negatives nhưng tăng false positives.
- LR/XGBoost giảm false positives hơn nhưng bỏ sót nhiều positive hơn RF.
- Insurance vẫn là cờ cảnh báo: RF uninsured FPR = 0,975 cho MEDNG và 1,000 cho MEDDL.

### Robustness

- Weighted F1 dưới threshold perturbation nằm trong 0,297–0,363 cho MEDNG và 0,285–0,389 cho MEDDL.
- Seed sensitivity của AUROC/AUPRC nhỏ; threshold-dependent F1 biến động nhiều hơn.
- Missingness stratum chỉ có 375–376 dòng và 36 positive cho mỗi outcome; kết quả phải ghi descriptive/uncertain.
- Composite common cohort có N = 32.345, positive N = 3.014; weighted prevalence test = 10,18%.
- Composite vẫn không có winner: RF cao nhất AUPRC/Recall, XGBoost cao nhất AUROC, LR cao nhất F1/Precision/Specificity.

## 6. Vấn đề phát sinh / lưu ý

- Kế hoạch ban đầu ghi target phụ dạng composite, trong khi Day 1–19 đã báo MEDDL độc lập. Day 20–22 giải quyết bằng cách giữ MEDNG/MEDDL độc lập làm main reporting và thêm composite dưới nhãn sensitivity.
- Weighted confusion totals không phải số người mẫu thực tế.
- Threshold perturbation không được dùng chọn threshold tốt hơn trên test.
- Seed robustness không được dùng chọn seed tốt nhất.
- Error share theo subgroup chịu ảnh hưởng của cả error rate và kích thước subgroup.
- Group profile là aggregate audit, không được dùng micro-targeting.
- Code freeze Day 22 khóa phần tính toán; manuscript vẫn cần UHS rà y khoa và causal language.

## 7. Quyết định / bước tiếp theo

- Gate 4 được đánh dấu PASS.
- Không mở lại model tuning hoặc threshold selection.
- UHS cần chốt use case và chi phí tương đối của false negative so với false positive trước khi chọn primary model.
- Day 23–24 tiếp tục Introduction, Discussion, Limitations và hoàn thiện Methods/Results từ bản Day 22.
- Day 25–26 thực hiện consistency audit code-to-manuscript và phản biện chéo.

## 8. Sản phẩm tạo ra

- `scripts/day20_22_error_robustness_freeze.py`
- `scripts/validate_day20_22_outputs.py`
- `modeling/day20_22/` với 15 CSV, 1 config JSON, 2 SVG và README.
- `docs/Day20_22_Error_Robustness_Methodological_Rationale.md`
- `docs/Day22_Methods_Results_Draft.md`
- `research_log/Day20_22_Error_Robustness_Code_Freeze.md`

**Kết luận trạng thái:** Day 20–22 hoàn thành; Gate 4 PASS; phần tính toán được đóng băng bước đầu và sẵn sàng chuyển sang viết Day 23–24.
