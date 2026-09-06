# UHS READ ME FIRST — NHIS 2024 Day 1–22

## Mục đích

File này là điểm vào duy nhất dành cho nhóm UHS. UHS không cần mở toàn bộ script, config, audit và CSV chi tiết trong repository. Các file kỹ thuật vẫn phải được giữ để tái lập kết quả, nhưng chỉ một tập nhỏ cần được đọc để diễn giải y tế công cộng và viết bài. Day 20–22 đã bổ sung error analysis, robustness, composite sensitivity và code freeze.

## 1. Thứ tự đọc ngắn nhất

### Bắt buộc — đọc theo thứ tự

1. `docs/UHS_Day3_4_predictor_review.md`
   - Xác nhận ý nghĩa của predictor, feature lock và các giới hạn diễn giải.
   - Dùng khi UHS cần kiểm tra biến nào được đưa vào primary model và vì sao.

2. `docs/UHS_Day8_10_Model_Evaluation_Handoff.md`
   - Bản handoff chính về LR, RF, XGBoost, 95% CI, calibration và DCA.
   - Dùng để hiểu vì sao chưa có model winner.

3. `docs/Day11_13_Survey_Aware_Methodological_Rationale.md`
   - Giải thích weighted–unweighted, `WTFA_A`, `PSTRAT`, `PPSU` và giới hạn survey-aware sensitivity.
   - Dùng để trả lời câu hỏi “có dùng weighted hết không?”.

4. `docs/Day14_16_SHAP_Methodological_Rationale.md`
   - Giải thích SHAP global, direction, interaction và subgroup explanation.
   - Dùng để tránh biến predictive attribution thành causal interpretation.

5. `docs/Day17_19_Fairness_Methodological_Rationale.md`
   - Giải thích subgroup performance, calibration, Recall/FNR/FPR và disparity span.
   - Dùng để diễn giải insurance, age và các nhóm không đủ dữ liệu.

6. `research_log/Day17_19_Fairness_Audit.md`
   - Bản kết luận fairness và lý do phải làm error analysis.

7. `docs/Day20_22_Error_Robustness_Methodological_Rationale.md`
   - Giải thích false negative/false positive, threshold/seed/missingness robustness và composite sensitivity.
   - Dùng để hiểu vì sao Day 20–22 vẫn không tạo model winner.

8. `docs/Day22_Methods_Results_Draft.md`
   - Bản Methods–Results đầu tiên có số liệu truy ngược tới output đã kiểm tra.
   - UHS rà thuật ngữ y tế, use case, mức độ khẳng định và Limitations; không tự sửa số.

### Bắt buộc khi viết Background/Discussion

- `literature/literature_matrix_day6.csv`
  - Ma trận hiện hành gồm 19 nguồn; đây là bản authoritative.
- `docs/Background_Related_Work_Day7.md`
  - Working draft cho Background và Related Work.

Không dùng `literature/NHIS2024_Day6_Literature_Matrix_18.xlsx` làm bản hiện hành. Đây chỉ là snapshot lịch sử 18 nguồn và gói XLSX hiện có bị lỗi cấu trúc ZIP nội bộ, nên một số phần mềm có thể không mở được hoặc đọc không ổn định. Nguồn chính xác phải dùng là `literature/literature_matrix_day6.csv` với 19 nguồn.

## 2. Bảng kết quả UHS thực sự cần xem

### Model performance và lựa chọn model

- `modeling/day8_10/uhs_extensions/day8_10_model_selection_evidence_table.csv`
  - Bảng gọn nhất để so sánh LR, RF, XGBoost.
  - Có AUROC, AUPRC, Recall, Precision, F1, Specificity, Brier, probability version và threshold.
- `modeling/day8_10/uhs_extensions/day8_10_auroc_auprc_bootstrap_ci.csv`
  - Dùng để đọc uncertainty; không dùng point estimate đơn lẻ để tuyên bố model vượt trội.
- `modeling/day8_10/uhs_extensions/calibration_MEDNG.svg`
- `modeling/day8_10/uhs_extensions/calibration_MEDDL.svg`
  - Chỉ cần xem hai hình này nếu thảo luận calibration.
- `modeling/day8_10/uhs_extensions/decision_curve_MEDNG.svg`
- `modeling/day8_10/uhs_extensions/decision_curve_MEDDL.svg`
  - Chỉ dùng như DCA exploratory; chưa chứng minh clinical utility.

### Weighted–unweighted sensitivity

- `modeling/day11_13/day11_13_weighted_outcome_prevalence.csv`
  - Tỷ lệ outcome có và không có trọng số.
- `modeling/day11_13/day11_13_weighted_model_sensitivity.csv`
  - Hiệu năng model trong nhánh weighted.
- `modeling/day11_13/day11_13_weighted_model_sensitivity_deltas.csv`
  - Cho biết weighting làm metric thay đổi bao nhiêu.
- `modeling/day11_13/day11_13_weighted_performance_cluster_bootstrap_ci.csv`
  - Dùng khi cần uncertainty của AUROC, AUPRC và Brier trong survey-aware sensitivity.

### SHAP/explainability

- `modeling/day14_16/day14_16_shap_global_importance.csv`
  - Bảng chính về importance ở cấp 12 constructs.
- `modeling/day14_16/day14_16_shap_direction_summary.csv`
  - Dùng để đọc direction/pattern, không dùng để kết luận causal effect.
- `modeling/day14_16/day14_16_shap_category_patterns.csv`
  - Chỉ dùng sau khi UHS map raw code bằng data dictionary.
- `modeling/day14_16/day14_16_shap_subgroup_patterns.csv`
- `modeling/day14_16/day14_16_shap_subgroup_skipped.csv`
  - Dùng để hiểu explanation pattern và nhóm bị loại vì N nhỏ.
- Hai hình tổng quan dễ đọc nhất:
  - `modeling/day14_16/figures/shap_global_constructs_MEDNG.svg`
  - `modeling/day14_16/figures/shap_global_constructs_MEDDL.svg`

UHS không cần đọc `day14_16_shap_encoded_importance.csv` trong vòng review đầu. Đây là bảng one-hot chi tiết dành cho technical audit.

### Fairness/subgroup audit

- `modeling/day17_19/day17_19_subgroup_performance.csv`
  - Metric của từng subgroup đủ điều kiện.
- `modeling/day17_19/day17_19_disparity_summary.csv`
  - Bảng gọn về max-minus-min gap theo axis.
- `modeling/day17_19/day17_19_disparity_cluster_bootstrap_ci.csv`
  - Uncertainty của gap.
- `modeling/day17_19/day17_19_subgroup_skipped.csv`
  - Bắt buộc xem để không kết luận cho nhóm thiếu dữ liệu.
- Bốn hình tổng quan:
  - `modeling/day17_19/figures/fairness_error_gap_MEDNG.svg`
  - `modeling/day17_19/figures/fairness_error_gap_MEDDL.svg`
  - `modeling/day17_19/figures/fairness_calibration_MEDNG.svg`
  - `modeling/day17_19/figures/fairness_calibration_MEDDL.svg`

### Error analysis, robustness và code freeze

- `modeling/day20_22/day22_final_error_table.csv`
  - Bảng ngắn nhất về FNR/FPR weighted ở locked threshold.
- `modeling/day20_22/day22_robustness_summary.csv`
  - Tóm tắt threshold, seed và missingness sensitivity; không dùng để chọn lại model.
- `modeling/day20_22/day20_22_composite_sensitivity_performance.csv`
  - Kết quả riêng cho target `MEDNG OR MEDDL`; chỉ là sensitivity.
- `modeling/day20_22/day20_22_leakage_integrity_checklist.csv`
  - 10/10 kiểm tra leakage và lock đều PASS.
- Hai hình tổng quan:
  - `modeling/day20_22/figures/day20_22_weighted_error_tradeoff.svg`
  - `modeling/day20_22/figures/day20_22_threshold_robustness.svg`

UHS không cần đọc `day20_22_error_profile_by_group.csv` trước. Bảng này có 168 dòng aggregate để audit sâu, không phải danh sách người hoặc công cụ micro-targeting.

## 3. File UHS không cần mở trong vòng review thông thường

### Giữ lại nhưng chỉ UIT dùng

- `scripts/*.py`
  - Mã tái lập toàn bộ pipeline.
- `*_config_log.json`
  - Phiên bản thư viện, seed, tham số và manifest đầu ra.
- `*_split_audit.csv`
  - Kiểm tra train–validation–test và `HHX`.
- `*_locked_reproduction_audit.csv`
  - Chứng minh kết quả sau vẫn khớp pipeline đã khóa.
- `audit/AUDIT_MANIFEST.json` và `modeling/DAY5_MANIFEST.json`
  - Dùng cho provenance/integrity.
- `modeling/day8_10/day8_10_tuning_candidates.csv`
  - Chi tiết mọi candidate; UHS chỉ cần candidate được chọn và lý do chọn.
- `modeling/day8_10/day8_10_calibration_points.csv`
  - Dữ liệu tạo hình; UHS xem hình là đủ.
- Phần lớn 20 hình SHAP riêng lẻ.
  - Chỉ mở hình của predictor/model cụ thể khi cần giải thích sâu.
- `graphify-out/`
  - Knowledge graph nội bộ; không phải dữ liệu hoặc kết quả để đưa vào manuscript.

### Không xóa

Những file trên làm repository trông nhiều, nhưng chúng bảo vệ tính tái lập, phát hiện model drift và chứng minh UIT không sửa model sau khi xem test. Cách đúng là ẩn chúng khỏi luồng đọc UHS bằng file hướng dẫn này, không xóa hoặc gom thủ công làm mất provenance.

## 4. Vì sao xuất hiện các kết quả chính?

### 4.1 Outcome hiếm dẫn đến Accuracy dễ gây hiểu nhầm

Kết quả:

- MEDNG unweighted prevalence khoảng 6,78%; weighted khoảng 7,39%.
- MEDDL unweighted prevalence khoảng 7,92%; weighted khoảng 8,58%.

Nguyên nhân:

- Khoảng 91–93% quan sát là negative.
- Một model dự đoán tất cả là negative vẫn có Accuracy cao nhưng Recall bằng 0.

Hệ quả diễn giải:

- Dùng AUPRC làm metric ưu tiên cho positive class hiếm.
- Đọc AUROC như discrimination bổ sung.
- Không chọn model bằng Accuracy.

### 4.2 Threshold thấp hơn 0,50 vì probability của outcome hiếm thường thấp

Kết quả locked threshold:

- MEDNG: LR 0,135; RF 0,110; XGBoost 0,185.
- MEDDL: LR 0,160; RF 0,080; XGBoost 0,140.

Nguyên nhân:

- Với prevalence thấp, predicted probability hiếm khi vượt 0,50.
- Giữ threshold 0,50 làm Recall rất thấp, đặc biệt ở RF baseline.
- Threshold được chọn trên validation để tối đa F1, không chọn trên test.

Hệ quả diễn giải:

- Đây là analytical operating point.
- Không phải clinical cutoff hoặc policy threshold.

### 4.3 RF có Recall cao nhưng Precision/Specificity thấp

Ví dụ MEDDL locked test:

- RF Recall 0,6730; Precision 0,2065; Specificity 0,7705.
- LR Recall 0,4283; Precision 0,3256; Specificity 0,9213.

Nguyên nhân:

- RF dùng operating threshold thấp 0,080 và gọi nhiều người là positive hơn.
- Gọi nhiều positive giúp giảm false negatives nhưng làm tăng false positives.

Hệ quả diễn giải:

- RF phù hợp hơn nếu ưu tiên không bỏ sót.
- LR/XGBoost có thể phù hợp hơn nếu false positive gây tốn nguồn lực.
- UHS phải xác định chi phí y tế công cộng của false negative so với false positive trước khi chọn primary model.

### 4.4 Không có universal winner vì mỗi metric trả lời một câu hỏi khác

MEDNG:

- RF AUPRC 0,3050 và XGBoost 0,3049 gần như bằng nhau.
- RF có Recall cao hơn.
- XGBoost có AUROC, F1, Specificity và Brier tốt hơn.

MEDDL:

- LR có AUPRC cao nhất nhẹ: 0,3168.
- XGBoost có AUROC cao nhất 0,8036 và Brier thấp nhất 0,0649.
- RF có Recall cao nhất nhưng Precision/Specificity thấp.

Nguyên nhân:

- AUPRC, AUROC, Recall, Precision, calibration và error trade-off đo các khía cạnh khác nhau.
- 95% CI của AUROC/AUPRC chồng lấp đáng kể.
- DCA exploratory cho thấy đường cong gần nhau và giao nhau.

Hệ quả diễn giải:

- Dùng cụm “models retained for further evaluation” hoặc “trade-offs across models”.
- Nếu cần primary model, UIT–UHS phải prespecify utility criterion; không chọn hậu nghiệm bằng test/fairness/SHAP.

### 4.5 Weighted và unweighted khác nhau vì người tham gia đại diện cho số người khác nhau

Nguyên nhân:

- Unweighted cho mỗi sample adult trọng số bằng nhau.
- `WTFA_A` làm mỗi người đóng góp theo số người trong dân số mà họ đại diện.
- Nếu outcome hoặc subgroup phân bố khác nhau giữa các vùng trọng số, prevalence, AUPRC, Brier và threshold-dependent metric sẽ thay đổi.

Kết quả:

- Weighted prevalence cao hơn unweighted cho cả MEDNG và MEDDL.
- AUROC thay đổi nhỏ, cho thấy ranking tương đối ổn định.
- AUPRC tăng ở 5/6 cặp trong so sánh kết hợp, nhưng MEDDL–XGBoost giảm nhẹ.

Hệ quả diễn giải:

- Không dùng weighted “thay thế” toàn bộ unweighted.
- Báo weighted như population-relevant analysis và unweighted như reference/sensitivity.
- `PSTRAT` và `PPSU` dùng cho uncertainty; không phải predictor.

### 4.6 MEDNG giữ Raw còn MEDDL dùng Platt vì calibration được quyết định trên validation

Nguyên nhân:

- Platt chỉ được giữ nếu cải thiện Brier trên validation-threshold role.
- MEDNG không cải thiện nên giữ Raw.
- MEDDL cải thiện nhẹ nên giữ Platt.

Hệ quả diễn giải:

- Gọi là preliminary calibration.
- Không gọi là clinically calibrated hoặc deployment-ready.
- Test calibration plots chỉ để đánh giá; không được dùng để fit thêm calibration layer.

### 4.7 SHAP khác nhau giữa LR, RF và XGBoost vì model học cấu trúc khác nhau

Nguyên nhân:

- LR biểu diễn quan hệ tuyến tính trên log-odds.
- RF và XGBoost học nonlinearities và interactions theo cách khác nhau.
- Correlated predictors có thể chia sẻ predictive information.
- Thang SHAP của LR/XGBoost và RF không hoàn toàn giống nhau.

Kết quả:

- Weighted–unweighted rank correlation 0,979–1,000 và top-five overlap 4–5/5 trong từng model.
- Tuy vậy, top predictor khác theo outcome và model.

Hệ quả diễn giải:

- Có thể nói ranking khá ổn định với weighting trong cùng model.
- Không so sánh trực tiếp độ lớn SHAP giữa model families.
- Không nói predictor “gây ra” MEDNG/MEDDL.

### 4.8 Insurance có gap lớn dù AUROC giữa nhóm khá gần

Kết quả:

- Insurance Recall span từ 0,431 đến 0,641.
- Insurance FPR span từ 0,367 đến 0,883.
- Insurance AUROC span chỉ từ 0,004 đến 0,062.
- MEDDL–RF ở uninsured có Recall 1,000 và FPR 1,000.
- MEDNG–RF ở uninsured có Recall 1,000 và FPR 0,975.
- Weighted prevalence uninsured cao hơn insured: MEDNG 25,7% so với 5,1%; MEDDL 27,7% so với 6,9%.

Nguyên nhân khả dĩ cần kiểm tra ở Day 20–21:

- AUROC đo ranking trên mọi threshold; Recall/FPR đo hành vi tại một locked threshold.
- Score distribution và base rate khác mạnh giữa insured và uninsured.
- Insurance đồng thời là predictor và equity axis, nên model có thể dùng biến này mạnh trong quyết định.

Hệ quả diễn giải:

- Không khen RF vì Recall bằng 1 khi FPR cũng gần hoặc bằng 1.
- Gọi đây là threshold-level disparity signal cần error analysis.
- Chưa đủ bằng chứng để gọi discrimination hoặc causal effect của insurance.

### 4.9 Một số race/ethnicity và age groups bị skip vì không đủ positive events

Nguyên nhân:

- Stability gate yêu cầu N ≥ 100, positive N ≥ 20 và negative N ≥ 20.
- Metric như Recall hoặc FPR rất bất ổn khi chỉ có vài ca dương/âm.

Kết quả:

- 168 dòng subgroup performance đủ điều kiện.
- 48 dòng bị skip.
- Một số nhóm NH Asian, NH AIAN, other/multiple và age 75+ không đủ support.

Hệ quả diễn giải:

- “Insufficient evidence” không có nghĩa là “không có disparity”.
- Không suy rộng kết luận fairness sang các nhóm bị skip.

### 4.10 Đây là cross-sectional classification, không phải dự báo tương lai hay causal model

Nguyên nhân:

- Outcome và nhiều predictor cùng được hỏi trong NHIS tại một thời điểm hoặc cùng khoảng 12 tháng.
- Không có trật tự thời gian và intervention design để chứng minh nguyên nhân.

Hệ quả diễn giải:

- Dùng “classification”, “predictive association” và “model attribution”.
- Tránh “future risk prediction”, “causes”, “effect” hoặc “ready for intervention”.

### 4.11 Day 20 cho thấy false negative và false positive đổi ngược chiều

Kết quả weighted:

- MEDNG–RF có FNR thấp nhất 0,417 nhưng FPR 0,159; MEDNG–XGBoost có FPR thấp nhất 0,074 nhưng FNR cao nhất 0,562.
- MEDDL–RF có FNR thấp nhất 0,301 nhưng FPR cao nhất 0,255; MEDDL–LR có FPR thấp nhất 0,090 nhưng FNR 0,535.

Nguyên nhân:

- RF sử dụng threshold thấp và gọi nhiều positive hơn.
- Gọi nhiều positive làm giảm số ca bị bỏ sót nhưng tăng số người không có outcome bị gắn cờ.

Hệ quả diễn giải:

- Không thể gọi Recall cao là tốt nếu chưa biết false positive gây tốn nguồn lực đến mức nào.
- UHS phải chốt use case và chi phí tương đối của hai loại lỗi trước khi chọn primary model.

### 4.12 Threshold robustness không cho phép chọn lại threshold bằng test

Kết quả:

- Threshold được nhân trước với 0,8; 1,0; 1,2.
- Recall tăng khi threshold giảm, còn precision/specificity thường giảm.
- Weighted F1 nằm trong 0,297–0,363 cho MEDNG và 0,285–0,389 cho MEDDL.

Hệ quả diễn giải:

- Đây là độ nhạy của operating point, không phải vòng tối ưu mới.
- Dù một threshold perturbation cho F1 test cao hơn, threshold khóa từ validation vẫn được giữ.

### 4.13 Missingness sensitivity có cỡ mẫu nhỏ nên chỉ mô tả

Kết quả:

- Test có 375 dòng MEDNG và 376 dòng MEDDL có ít nhất một cleaned-feature missing; mỗi outcome chỉ có 36 positive trong stratum này.
- LR/XGBoost có weighted F1 thấp hơn ở missingness stratum; RF cho pattern không nhất quán.

Nguyên nhân:

- Missingness stratum nhỏ hơn rất nhiều so với no-missing stratum.
- Tập này có thể khác về case mix và metric threshold-level biến động mạnh khi chỉ có 36 positive.

Hệ quả diễn giải:

- Giữ train-fitted imputation và explicit missing category.
- Không chọn model mới từ missingness subgroup và không khẳng định nguyên nhân của chênh lệch.

### 4.14 Composite sensitivity vẫn không có winner

Kết quả:

- Common cohort N = 32.345, positive N = 3.014; weighted test prevalence = 10,18%.
- RF có weighted AUPRC/Recall cao nhất; XGBoost có AUROC cao nhất; LR có F1/Precision/Specificity cao nhất.

Nguyên nhân:

- Composite thay đổi định nghĩa positive và prevalence.
- Hyperparameter RF/XGBoost được tái sử dụng từ MEDNG, không tune lại theo composite/test.

Hệ quả diễn giải:

- Composite chỉ kiểm tra độ nhạy đối với định nghĩa outcome.
- Không thay thế báo cáo MEDNG và MEDDL độc lập; không dùng để chọn winner hậu nghiệm.

## 5. UHS cần quyết định điều gì?

1. False negative hay false positive nghiêm trọng hơn trong use case giả định?
2. Use case là mô tả học thuật, screening/outreach hay phân bổ hỗ trợ?
3. Có cần chọn một primary model hay giữ multi-model comparison?
4. Nếu chọn primary model, utility criterion nào được thống nhất trước?
5. Cách diễn giải health-equity cho insurance và age mà không gắn nhãn discrimination quá mức?
6. Cách map và gọi tên các raw NHIS categories trong manuscript?
7. Nhóm nào được báo kết quả và nhóm nào phải ghi insufficient evidence?
8. Cách viết novelty tránh tuyên bố “lần đầu dùng ML/SHAP cho unmet care”?
9. Với mục tiêu bài báo hiện tại, có cần chọn primary model hay giữ ba model như benchmark minh bạch?
10. Nếu buộc phải chọn, false negative và false positive được định giá thế nào trước khi nhìn thêm kết quả?

## 6. Quy tắc giữ repository không bị rối thêm

1. UHS bắt đầu từ file này, không duyệt folder theo thứ tự alphabet.
2. Nhật ký là narrative history; `docs/` là giải thích phương pháp; `modeling/` là bằng chứng số; `scripts/` là tái lập.
3. Mỗi kết luận trong manuscript phải trỏ được về một bảng aggregate hoặc một methodological rationale.
4. Không copy cùng một CSV sang nhiều folder.
5. Không chỉnh sửa file output bằng tay; thay đổi phải đi qua script và audit.
6. File lịch sử được giữ để provenance nhưng phải ghi rõ historical/non-authoritative.
7. Sau mỗi giai đoạn chỉ bổ sung một README/handoff; không tạo thêm nhiều bản “final”, “final2”, “new”.

## 7. Sơ đồ đọc nhanh

`UHS_READ_ME_FIRST_DAY1_22.md`

→ predictor meaning: `UHS_Day3_4_predictor_review.md`

→ model trade-off: `UHS_Day8_10_Model_Evaluation_Handoff.md`

→ weighting: `Day11_13_Survey_Aware_Methodological_Rationale.md`

→ explanation: `Day14_16_SHAP_Methodological_Rationale.md`

→ fairness/error: `Day17_19_Fairness_Methodological_Rationale.md`

→ error/robustness: `Day20_22_Error_Robustness_Methodological_Rationale.md`

→ manuscript draft: `Day22_Methods_Results_Draft.md`

→ exact numbers: selected CSV/SVG files listed in Section 2

→ next action: Day 23–24 Introduction, Discussion và Limitations; không thay đổi computational lock Day 22
