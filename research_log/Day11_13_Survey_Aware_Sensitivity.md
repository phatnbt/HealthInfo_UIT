# NHẬT KÝ NGHIÊN CỨU NHIS 2024
## Day 11–13 — Phân tích độ nhạy có xét thiết kế khảo sát

**Nhóm thực hiện:** UIT — kỹ thuật

**Trạng thái:** HOÀN THÀNH DAY 11–13

**Phạm vi:** Phân tích độ nhạy weighted–unweighted trên các mô hình đã khóa ở Day 8–10

## 1. Mục tiêu trong ngày

- Tiếp thu nhận xét của UHS về việc chưa có mô hình thắng tuyệt đối và không ép chọn một “winner”.
- Ước lượng tỷ lệ thiếu chăm sóc y tế do chi phí (`MEDNG`) và trì hoãn chăm sóc y tế do chi phí (`MEDDL`) ở mức dân số bằng trọng số `WTFA_A`.
- Đưa cấu trúc phân tầng `PSTRAT` và cụm mẫu `PPSU` vào ước lượng độ bất định.
- So sánh kết quả khi huấn luyện và đánh giá có/không dùng trọng số khảo sát, nhưng giữ nguyên toàn bộ pipeline Day 8–10 đã khóa.
- Kiểm tra xem kết luận về LR, RF và XGBoost có nhạy đáng kể với thiết kế khảo sát hay không.

## 2. Công việc đã thực hiện

- Kiểm tra và tái lập 6 kết quả mô hình đã khóa của Day 8–10 trước khi chạy phân tích mới.
- Xác thực các biến thiết kế khảo sát `WTFA_A`, `PSTRAT`, `PPSU` và khóa `HHX`.
- Tính tỷ lệ outcome không trọng số và có trọng số, kèm khoảng tin cậy 95% theo Taylor linearization.
- Chạy bốn cấu hình độ nhạy cho từng outcome–model: huấn luyện không trọng số/có trọng số kết hợp với đánh giá không trọng số/có trọng số.
- Ước lượng khoảng tin cậy 95% cho AUROC, AUPRC và Brier bằng 400 lần stratified-PSU bootstrap.
- So sánh LR, RF và XGBoost theo AUROC, AUPRC, Recall, Precision, F1, Specificity và Brier.
- Ghi nhận kết quả theo đúng nhận xét UHS: mỗi mô hình có thế mạnh khác nhau và chưa có bằng chứng về một mô hình thắng tuyệt đối.
- Chỉ xuất dữ liệu tổng hợp; không đưa dữ liệu cá nhân hoặc dự đoán ở cấp cá nhân lên GitHub.

## 3. Công cụ sử dụng

- Python 3.
- `pandas` và `numpy`: đọc, làm sạch, biến đổi và tổng hợp dữ liệu.
- `scikit-learn`: Logistic Regression và các chỉ số đánh giá.
- `xgboost==3.0.4`: tái lập đúng mô hình XGBoost đã khóa.
- `scipy`: phân phối t cho khoảng tin cậy Taylor.
- Git và GitHub: quản lý phiên bản, kiểm tra thay đổi và lưu vết nghiên cứu.
- Graphify: cập nhật đồ thị tri thức của dự án sau merge commit.

## 4. Các bước xử lý

1. Nạp hai cohort phân tích `MEDNG` và `MEDDL` cùng các artifact Day 8–10.
2. Giữ nguyên phép chia train–validation–test theo `HHX`, 12 nhóm predictor, preprocessing, hyperparameter, dạng xác suất và threshold đã khóa.
3. Chạy audit tái lập: so sánh 6 dòng kết quả conventional với artifact Day 8–10 bằng tolerance `1e-08`.
4. Kiểm tra `WTFA_A` hữu hạn và dương; kiểm tra số strata, PSU, design degrees of freedom và lonely stratum.
5. Tính prevalence có trọng số trên full cohort và Taylor-linearized 95% CI bằng `PSTRAT` + `PPSU`.
6. Chuẩn hóa trọng số huấn luyện về trung bình 1 để ổn định số học; không dùng `WTFA_A`, `PSTRAT`, `PPSU` hoặc `HHX` làm predictor.
7. Với mỗi LR, RF và XGBoost, chạy hai điều kiện huấn luyện rồi đánh giá cả có và không có trọng số.
8. Với nhánh MEDDL có weighted training, giữ Platt scaling đã khóa và fit calibration bằng trọng số trên phần validation dành cho calibration.
9. Thực hiện 400 bootstrap replicates, lấy lại PSU trong từng stratum và giữ `WTFA_A`, để tạo sensitivity CI cho AUROC/AUPRC/Brier.
10. Xuất bảng tổng hợp, delta giữa các cấu hình, log cấu hình và báo cáo phương pháp; không dùng test để tune lại mô hình.

## 5. Kết quả

Audit tái lập Day 8–10 đạt **PASS 6/6 dòng**. Sai khác tuyệt đối lớn nhất là `3.83e-09`, nhỏ hơn tolerance `1e-08`. XGBoost được cố định ở phiên bản `3.0.4` để tránh model drift.

| Outcome | Tỷ lệ không trọng số | Tỷ lệ có trọng số | Taylor 95% CI |
|---|---:|---:|---:|
| MEDNG | 6.78% | 7.39% | 6.99%–7.78% |
| MEDDL | 7.92% | 8.58% | 8.15%–9.01% |

Trong cấu hình weighted training + weighted evaluation:

| Outcome | Model | AUROC | AUPRC | Recall | Precision | F1 | Specificity | Brier |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| MEDNG | LR | 0.7958 | 0.3154 | 0.4812 | 0.2691 | 0.3451 | 0.9005 | 0.0566 |
| MEDNG | RF | 0.8072 | 0.3258 | 0.5850 | 0.2167 | 0.3162 | 0.8390 | 0.0577 |
| MEDNG | XGBoost | 0.8073 | 0.3207 | 0.4302 | 0.2945 | 0.3496 | 0.9215 | 0.0569 |
| MEDDL | LR | 0.7792 | 0.3368 | 0.4458 | 0.3383 | 0.3847 | 0.9150 | 0.0703 |
| MEDDL | RF | 0.7954 | 0.3384 | 0.7308 | 0.2000 | 0.3141 | 0.7152 | 0.0700 |
| MEDDL | XGBoost | 0.7980 | 0.3134 | 0.5300 | 0.2678 | 0.3558 | 0.8588 | 0.0705 |

- AUROC thay đổi từ `-0.0057` đến `+0.0016` so với nhánh conventional đã khóa, cho thấy discrimination nhìn chung ổn định.
- AUPRC tăng ở 5/6 cặp outcome–model; MEDDL–XGBoost giảm nhẹ `-0.0018` trong so sánh kết hợp.
- MEDDL–XGBoost giảm khoảng `0.0159` AUPRC khi weighted fitting so với chính mô hình unweighted-trained dưới cùng weighted evaluation.
- Không có universal winner: RF thiên về recall; LR/XGBoost thường giữ precision, specificity hoặc F1 tốt hơn tùy outcome.

## 6. Vấn đề phát sinh / lưu ý

- Phiên bản XGBoost mới hơn làm kết quả tái lập bị lệch; vì vậy môi trường được khóa ở `xgboost==3.0.4`.
- Khoảng tin cậy của các mô hình chồng lấp đáng kể và chưa phải paired difference CI; không được diễn giải là một mô hình vượt trội có ý nghĩa thống kê.
- Stratified-PSU bootstrap chỉ là phân tích độ nhạy có xét thiết kế khảo sát, không thay thế quy trình suy luận chính thức của NCHS bằng replicate weights.
- Weighted machine learning không tự tạo ra bằng chứng nhân quả, khả năng khái quát ngoài mẫu hoặc tính sẵn sàng triển khai.
- Outcome và predictor đều là thông tin tự báo cáo trong 12 tháng qua; đây là bài toán classification/association, không phải dự báo nguy cơ tương lai.
- Test đã được dùng để báo cáo đánh giá cuối; tuyệt đối không dùng kết quả Day 11–13 để tune lại hyperparameter, đổi threshold, đổi feature hoặc chọn lại mô hình.
- Bảng subgroup còn dùng mã public-use thô; trước khi đưa vào bản thảo phải ánh xạ qua data dictionary đã khóa.

## 7. Quyết định / bước tiếp theo

- Chấp nhận kết luận của UHS rằng **không có một mô hình thắng tuyệt đối**.
- Giữ cả LR, RF và XGBoost cho bước giải thích tiếp theo, trình bày rõ trade-off của từng mô hình thay vì gán nhãn “best model”.
- Khóa toàn bộ pipeline Day 8–13; không mở lại tuning từ kết quả survey sensitivity.
- Chuyển sang Day 14–16: SHAP/explainability trên các mô hình đã khóa.
- SHAP và test performance ở Day 14–16 chỉ phục vụ giải thích/đánh giá, không được dùng để sửa mô hình hậu nghiệm.

## 8. Sản phẩm tạo ra

- `scripts/day11_13_survey_sensitivity.py`
- `modeling/day11_13/day11_13_survey_design_audit.csv`
- `modeling/day11_13/day11_13_weighted_outcome_prevalence.csv`
- `modeling/day11_13/day11_13_weighted_subgroup_prevalence.csv` — lưu trong gói Drive, chưa công khai trên GitHub.
- `modeling/day11_13/day11_13_weighted_model_sensitivity.csv`
- `modeling/day11_13/day11_13_weighted_model_sensitivity_deltas.csv`
- `modeling/day11_13/day11_13_weighted_performance_cluster_bootstrap_ci.csv`
- `modeling/day11_13/day11_13_config_log.json`
- `docs/Day11_13_Survey_Aware_Methodological_Rationale.md`
- `research_log/Day11_13_Survey_Aware_Sensitivity.md`

**Kết luận trạng thái:** Day 11–13 hoàn thành, tuân thủ protocol khóa và sẵn sàng chuyển sang Day 14–16.
