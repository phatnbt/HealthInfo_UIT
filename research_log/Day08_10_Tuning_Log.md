# NHẬT KÝ NGHIÊN CỨU NHIS 2024
## Day 8–10 — Model tuning, preliminary calibration & locked test re-evaluation

**Workstream:** UIT — kỹ thuật  
**Status:** UIT TECHNICAL DAY 8–10 COMPLETE. UHS metric-interpretation review remains a collaborative sign-off step.

## 1. Mục tiêu theo plan gốc
Day 8–10 yêu cầu: (1) train/tune vừa phải Random Forest và XGBoost, giữ Logistic Regression làm comparator; (2) lưu seed/config; (3) đánh giá AUROC, AUPRC, Recall, F1, Specificity và Brier; (4) không dùng Accuracy làm metric ưu tiên khi outcome mất cân bằng; và (5) tạo bảng performance 3 model + calibration sơ bộ.

## 2. Các sửa đổi phương pháp so với bản PR ban đầu
Bản PR ban đầu chỉ chạy `MEDNG`, trộn thêm weighted training/evaluation thuộc phạm vi Day 11–13, dùng `GroupKFold` dù `HHX` là duy nhất trong hai cohort Sample Adult, chỉ vẽ calibration curve trên test chứ chưa thực hiện calibration, và chưa commit các output aggregate được mô tả trong log. Các điểm này đã được sửa.

Phiên bản hiện tại:
- chạy **hai outcome độc lập**: `MEDNG` và `MEDDL`;
- giữ nguyên 12 main constructs đã khóa sau Day 4/UHS review;
- giữ đúng deterministic split Day 5 bằng SHA-256 trên `HHX`;
- preprocessing được fit **chỉ trên TRAIN**, sau đó đóng băng cho validation/test;
- Day 8–10 chỉ làm conventional model tuning; `WTFA_A/PPSU/PSTRAT` survey-aware sensitivity được để đúng sang Day 11–13;
- bỏ hard-coded Windows path, dùng CLI `--data-dir` và `--out-dir`;
- không dùng test để chọn hyperparameter, calibration hay threshold.

## 3. Split audit
Split khớp tuyệt đối Day 5:

| Outcome | Train (positive) | Validation (positive) | Test (positive) |
|---|---:|---:|---:|
| MEDNG | 22,711 (1,524) | 3,226 (233) | 6,417 (438) |
| MEDDL | 22,711 (1,761) | 3,225 (280) | 6,419 (523) |

Validation được chia deterministic thành 3 phần độc lập theo hash `HHX`:
- **model_selection**: chọn candidate RF/XGBoost bằng AUPRC;
- **calibration**: fit Platt scaling;
- **threshold**: quyết định Raw vs Platt bằng Brier và chọn threshold tối đa F1.

MEDNG có 83 / 75 / 75 positive events tương ứng ba phần; MEDDL có 108 / 82 / 90.

## 4. Moderate tuning
Seed cố định: `2026`.

Random Forest dùng 4 cấu hình prespecified, giới hạn độ sâu để tránh exhaustive search và thời gian chạy không cần thiết. XGBoost dùng 8 cấu hình prespecified. Candidate được chọn bằng **AUPRC trên validation model-selection subset**. Logistic Regression giữ `C=1.0` như baseline Day 5 và không tune lại.

Best configuration:
- **MEDNG RF:** 300 trees, max_depth 8, min_samples_leaf 10, max_features log2.
- **MEDNG XGBoost:** 300 trees, depth 4, learning_rate 0.05, subsample 0.85, colsample_bytree 0.85, min_child_weight 2.
- **MEDDL RF:** 300 trees, max_depth 10, min_samples_leaf 5, max_features sqrt.
- **MEDDL XGBoost:** 400 trees, depth 5, learning_rate 0.03, subsample 0.85, colsample_bytree 0.85, min_child_weight 2.

## 5. Preliminary calibration & threshold
Platt scaling được fit trên validation-calibration subset. Trên validation-threshold subset, chỉ giữ Platt nếu Brier nhỏ hơn Raw; sau đó chọn operating threshold tối đa F1. Threshold này là **lựa chọn vận hành cho phân tích**, không phải clinical cutoff.

- MEDNG: Raw probability được giữ cho LR/RF/XGBoost vì Platt không cải thiện Brier trên threshold subset.
- MEDDL: Platt được giữ cho LR/RF/XGBoost, nhưng mức cải thiện Brier trên validation là nhỏ; vì vậy chỉ gọi là **preliminary calibration**.

## 6. Locked test performance
Sau khi toàn bộ quyết định tuning/calibration/threshold đã khóa bằng validation, script mới đánh giá lại test.

| Outcome | Model | Prob. | Threshold | AUROC | AUPRC | Recall | Precision | F1 | Specificity | Brier |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| MEDNG | LR | Raw | 0.135 | 0.7942 | 0.3007 | 0.4406 | 0.2773 | 0.3404 | 0.9159 | 0.0555 |
| MEDNG | RF | Raw | 0.110 | 0.8062 | 0.3050 | 0.5411 | 0.2238 | 0.3166 | 0.8625 | 0.0564 |
| MEDNG | XGBoost | Raw | 0.185 | 0.8083 | 0.3049 | 0.3995 | 0.3165 | 0.3532 | 0.9368 | 0.0553 |
| MEDDL | LR | Platt | 0.160 | 0.7845 | 0.3168 | 0.4283 | 0.3256 | 0.3699 | 0.9213 | 0.0651 |
| MEDDL | RF | Platt | 0.080 | 0.7967 | 0.3107 | 0.6730 | 0.2065 | 0.3160 | 0.7705 | 0.0652 |
| MEDDL | XGBoost | Platt | 0.140 | 0.8036 | 0.3152 | 0.5201 | 0.2860 | 0.3691 | 0.8848 | 0.0649 |

## 7. Diễn giải kỹ thuật cần giữ
- Outcome hiếm (~7–9%), vì vậy **AUPRC** được ưu tiên hơn Accuracy; AUROC là metric discrimination bổ sung.
- Recall phải đọc cùng Precision/Specificity. Ví dụ RF có recall cao hơn nhưng đổi lại precision và specificity thấp hơn; không được gọi đơn giản là “tốt hơn”.
- MEDNG: RF và XGBoost có AUPRC gần như ngang nhau trên test; XGBoost có AUROC/F1 cao hơn, RF có recall cao hơn. Không có bằng chứng để gọi một model “vượt trội” chỉ từ các chênh lệch nhỏ này.
- MEDDL: LR có AUPRC test cao nhất rất nhẹ, trong khi XGBoost có AUROC cao nhất; khác biệt nhỏ nên chưa khóa “winner” bằng test.
- Tuning Day 8–10 không tạo ra cải thiện lớn, ổn định so với baseline Day 5; đây là kết quả hợp lệ và không nên ép narrative thành “tuning làm model tốt hơn rõ rệt”.
- Test split đã từng được báo cáo ở Day 5 baseline. Day 8–10 là **locked re-evaluation** sau validation; từ thời điểm này không được tiếp tục chỉnh hyperparameter/threshold dựa trên test.
- Không diễn giải model metric, calibration hoặc feature effect như causal evidence.

## 8. Phần UHS cần review/sign-off
Plan gốc giao UHS kiểm tra ý nghĩa y tế của metric ưu tiên. Bản kỹ thuật đề xuất UHS review các điểm sau trước khi đưa vào paper:
1. AUPRC là metric ưu tiên vì positive class hiếm; Accuracy không dùng làm metric chính.
2. Recall thể hiện khả năng phát hiện người thật sự có cost-related unmet/delayed care, nhưng tăng Recall có thể làm giảm Precision/Specificity.
3. Threshold tối đa F1 là operating point phục vụ phân tích, không phải ngưỡng lâm sàng hay chính sách.
4. Không gọi model “tốt nhất” chỉ dựa vào một metric duy nhất; cần xét discrimination, calibration và trade-off error cùng nhau.

## 9. Sản phẩm tạo ra
- `scripts/day8_10_modeling.py`
- `modeling/day8_10/day8_10_split_audit.csv`
- `modeling/day8_10/day8_10_validation_role_audit.csv`
- `modeling/day8_10/day8_10_tuning_candidates.csv`
- `modeling/day8_10/day8_10_validation_selection.csv`
- `modeling/day8_10/day8_10_model_performance.csv`
- `modeling/day8_10/day8_10_calibration_points.csv`
- `modeling/day8_10/day8_10_config_log.json`

## 10. Gate tiếp theo
**UIT technical Day 8–10: COMPLETE.**  
Tiếp theo là **Day 11–13 survey-aware sensitivity analysis**: `WTFA_A` weighted-vs-unweighted predictive sensitivity, đồng thời xử lý vai trò `PPSU/PSTRAT` đúng mức và ghi rõ giới hạn giữa sample-weighted ML với full design-based inference. Không dùng Day 8–10 test results để tuning thêm.
