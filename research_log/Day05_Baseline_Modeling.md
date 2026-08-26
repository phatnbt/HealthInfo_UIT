# Day 5 — Preprocessing và baseline modeling

## 1. Mục tiêu
Bắt đầu giai đoạn modeling sau khi Day 4 và UHS feature lock hoàn tất. Train baseline Logistic Regression, Random Forest và XGBoost cho hai outcome độc lập `MEDNG12M_A` và `MEDDL12M_A`, đồng thời so sánh conventional unweighted với `WTFA_A`-weighted training.

## 2. Feature set
Main model dùng 12 constructs đã khóa sau UHS review:
`AGEP_A`, `SEX_A`, `HISPALLP_A`, `EDUCP_A`, `RATCAT_A`, `EMPWRKLSW1_A`, `NOTCOV_A`, `FDSCAT3_A`, `PHSTAT_A`, `DISAB3_A`, `K6SPD_A`, `CHRONIC_BURDEN_CAT`.

`HHX`, `WTFA_A`, `PPSU`, `PSTRAT` không bao giờ là predictors.

## 3. Split
Dùng deterministic split theo `HHX` với SHA-256 và seed 2026 để tránh thay đổi split giữa các lần chạy:
- Train: khoảng 70%
- Validation: khoảng 10%
- Test: khoảng 20%

Validation được reserve, chưa dùng để fit/model selection trong baseline Day 5.

MEDNG:
- Train 22,711; positive 1,524
- Validation 3,226; positive 233
- Test 6,417; positive 438

MEDDL:
- Train 22,711; positive 1,761
- Validation 3,225; positive 280
- Test 6,419; positive 523

## 4. Preprocessing
- Missing/special codes tiếp tục xử lý variable-specific theo Day 4 audit.
- `AGEP_A`: special code → missing, median imputation trên train, sau đó standardize.
- Categorical variables: special code → missing, explicit `Missing`, one-hot encoding fitted trên train; unknown category ở test được ignore an toàn.
- `CHRONIC_BURDEN_CAT`: giữ `Missing/indeterminate` như explicit category.
- Sau encoding: 63 model columns cho mỗi outcome.

Không dùng complete-case deletion, SMOTE hoặc resampling trong baseline Day 5.

## 5. Models
- Logistic Regression: `C=1`, `lbfgs`, max_iter=2000.
- Random Forest: 250 trees, `max_features=sqrt`, `min_samples_leaf=5`.
- XGBoost: 250 trees, depth 4, learning rate 0.05, subsample 0.85, colsample_bytree 0.85.

Mỗi model được train theo hai regime:
1. Unweighted.
2. `WTFA_A` sample-weighted; train weights được normalize về mean 1 để giữ relative survey weighting mà không phóng đại scale của loss/regularization.

## 6. Held-out test results
### MEDNG — unweighted evaluation
- XGBoost: AUROC 0.809; AUPRC 0.308; Recall 0.080; Precision 0.565; Brier 0.0551.
- Random Forest: AUROC 0.796; AUPRC 0.301; Recall 0.014; Precision 0.857; Brier 0.0557.
- Logistic Regression: AUROC 0.794; AUPRC 0.301; Recall 0.098; Precision 0.581; Brier 0.0555.

### MEDNG — WTFA_A-weighted training/evaluation
- XGBoost: AUROC 0.810; AUPRC 0.322; Recall 0.104; Precision 0.623; Brier 0.0567.
- Random Forest: AUROC 0.797; AUPRC 0.316; Recall 0.021; Precision 0.856; Brier 0.0572.
- Logistic Regression: AUROC 0.796; AUPRC 0.315; Recall 0.116; Precision 0.554; Brier 0.0566.

### MEDDL — unweighted evaluation
- XGBoost: AUROC 0.806; AUPRC 0.319; Recall 0.080; Precision 0.575; Brier 0.0647.
- Logistic Regression: AUROC 0.784; AUPRC 0.317; Recall 0.088; Precision 0.541; Brier 0.0652.
- Random Forest: AUROC 0.792; AUPRC 0.310; Recall 0.019; Precision 0.714; Brier 0.0654.

### MEDDL — WTFA_A-weighted training/evaluation
- Logistic Regression: AUROC 0.779; AUPRC 0.337; Recall 0.097; Precision 0.542; Brier 0.0698.
- Random Forest: AUROC 0.792; AUPRC 0.328; Recall 0.025; Precision 0.596; Brier 0.0703.
- XGBoost: AUROC 0.801; AUPRC 0.321; Recall 0.098; Precision 0.594; Brier 0.0700.

## 7. Diễn giải
- Với target prevalence thấp, AUPRC được ưu tiên hơn accuracy.
- XGBoost có AUPRC cao nhất ở MEDNG và ở MEDDL-unweighted baseline; với MEDDL weighted evaluation, LR có AUPRC cao nhất trong baseline này.
- Không kết luận model nào là final chỉ từ Day 5. Validation chưa được sử dụng cho threshold/calibration/tuning.
- Recall ở threshold 0.50 còn thấp, đặc biệt RF. Đây là lý do threshold selection/calibration phải được làm trên validation trước final reporting.
- `WTFA_A`-weighted ML là survey-weighted predictive comparison; chưa phải full design-based inference vì `PSTRAT/PPSU` chưa được đưa vào variance estimation.

## 8. Quyết định
**DAY 5 BASELINE MODELING COMPLETE.**

Bước tiếp theo: dùng validation để kiểm calibration/threshold, sau đó thực hiện explainability (SHAP) và subgroup fairness/performance audit mà không chạm test set cho model selection.

## 9. Sản phẩm
- `scripts/run_day5_baseline.py`
- `modeling/day5_model_metrics.csv`
- `modeling/day5_primary_matched_summary.csv`
- `modeling/day5_best_by_auprc.csv`
- `modeling/day5_split_audit.csv`
- `modeling/day5_preprocessing_missing_audit.csv`
- `modeling/day5_encoded_feature_audit.csv`
- `modeling/DAY5_MANIFEST.json`

Person-level test predictions được giữ local và không commit vào public repository.