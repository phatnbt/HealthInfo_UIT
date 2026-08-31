# NHẬT KÝ NGHIÊN CỨU NHIS 2024
## Day 11–13 — Survey-aware weighted-vs-unweighted sensitivity

**Workstream:** UIT — kỹ thuật  
**Status:** UIT TECHNICAL DAY 11–13 COMPLETE

## 1. Mục tiêu

- mô tả tỷ lệ MEDNG và MEDDL ở mức dân số bằng `WTFA_A`;
- đưa `PSTRAT` và `PPSU` vào ước lượng bất định;
- so sánh unweighted với weighted training/evaluation trên đúng mô hình Day 8–10 đã khóa;
- ghi rõ giới hạn giữa survey-aware sensitivity và full official survey inference.

## 2. Nguyên tắc khóa

Không tune lại hyperparameter, không đổi split, feature, probability version hay threshold. `WTFA_A`, `PSTRAT`, `PPSU`, `HHX` không phải predictor. Test chỉ dùng để báo cáo sensitivity tổng hợp, không dùng để chọn model.

Audit tái lập Day 8–10: **PASS**, 6/6 dòng; sai khác tuyệt đối lớn nhất `3.83e-09` với tolerance `1e-08`. XGBoost được cố định ở phiên bản `3.0.4`; phiên bản mới hơn tạo model drift và bị audit chặn.

## 3. Xử lý thiết kế khảo sát

- `WTFA_A`: point estimate dân số và sample weight cho sensitivity.
- `PSTRAT` + `PPSU`: Taylor-linearized SE cho prevalence.
- 400 stratified-PSU bootstrap replicates: 95% sensitivity CI cho weighted AUROC/AUPRC/Brier.
- Hai cohort đều có 52 strata, 662 stratum-specific PSUs, design df 610 và không có lonely stratum trong full cohort.

## 4. Kết quả chính

| Outcome | Unweighted prevalence | Weighted prevalence | Taylor 95% CI |
|---|---:|---:|---:|
| MEDNG | 6.78% | 7.39% | 6.99%–7.78% |
| MEDDL | 7.92% | 8.58% | 8.15%–9.01% |

Trong matched weighted training + weighted evaluation:

- MEDNG: AUROC 0.7958–0.8073; AUPRC 0.3154–0.3258.
- MEDDL: AUROC 0.7792–0.7980; AUPRC 0.3134–0.3384.
- So với locked conventional arm, AUROC chỉ thay đổi từ -0.0057 đến +0.0016.
- AUPRC tăng ở 5/6 outcome-model pairs; ngoại lệ là MEDDL XGBoost giảm nhẹ -0.0018 ở combined comparison.
- Weighted fitting của MEDDL XGBoost làm weighted-evaluation AUPRC giảm khoảng 0.0159 so với cùng model unweighted-trained; đây là sensitivity signal, không phải lý do tune/chọn lại model.

## 5. Quyết định diễn giải

**Không có universal winner.** RF thiên về recall; LR/XGBoost thường giữ precision/specificity hoặc F1 tốt hơn tùy outcome. Các bootstrap CI theo model chồng lấp đáng kể và không phải paired difference CI, nên không có cơ sở nói một model vượt trội có ý nghĩa thống kê.

Kết luận Day 11–13: discrimination nhìn chung ổn định trước survey weighting, nhưng prevalence và precision–recall/calibration trade-off nhạy với thành phần dân số được trọng số đại diện.

## 6. Giới hạn

- Stratified-PSU bootstrap là survey-aware sensitivity, không thay thế official NCHS replicate-weight inference.
- Weighted ML không tạo bằng chứng causal hoặc external/deployment validity.
- Kết quả là contemporaneous classification cho outcome tự báo cáo trong 12 tháng qua, không phải dự báo nguy cơ tương lai.
- Không dùng các kết quả test này để mở lại tuning.

## 7. Sản phẩm

- `scripts/day11_13_survey_sensitivity.py`
- `modeling/day11_13/day11_13_survey_design_audit.csv`
- `modeling/day11_13/day11_13_weighted_outcome_prevalence.csv`
- `modeling/day11_13/day11_13_weighted_subgroup_prevalence.csv`
- `modeling/day11_13/day11_13_weighted_model_sensitivity.csv`
- `modeling/day11_13/day11_13_weighted_model_sensitivity_deltas.csv`
- `modeling/day11_13/day11_13_weighted_performance_cluster_bootstrap_ci.csv`
- `modeling/day11_13/day11_13_config_log.json`
- `docs/Day11_13_Survey_Aware_Methodological_Rationale.md`

## 8. Gate tiếp theo

Day 11–13: **COMPLETE**. Tiếp theo là Day 14–16 SHAP/explainability trên các model đã khóa. Day 14–16 không được dùng SHAP hoặc test performance để tune lại pipeline.
