# NHẬT KÝ NGHIÊN CỨU NHIS 2024
## Giai đoạn: Model Tuning & Baseline (Day 8-10)

**Mục tiêu trong ngày:** 
Đập đi xây lại script tuning (RandomForest, XGBoost, LogisticRegression) trên tập dữ liệu hoàn thiện từ Day 5, đảm bảo tính chặt chẽ về phương pháp (không rò rỉ dữ liệu qua Pipeline, tuning đúng không gian, chia tách tập đúng nguyên tắc).

**Công việc đã thực hiện:**
1. **Kiểm tra và xác minh tính toàn vẹn (Pre-check):**
   - Đã kiểm tra lại logic chia Split bằng SHA-256 trên `HHX`. Tập Train/Val/Test khớp tuyệt đối số dòng với báo cáo Day 5 (Train: 22,711; Val: 3,226; Test: 6,417). 
   - Tổng cộng có đúng 2,195 ca Positive của `MEDNG12M_A` (Forgone Care), khớp hoàn toàn với nhật ký Day 2.
   - Kiểm tra mã lỗi của `RATCAT_A` (imputed income recode): Chứng minh bằng cả tài liệu CDC và truy xuất trên file thô rằng biến này KHÔNG CÓ mã 97 (Refused) và 99 (Don't know). Việc chỉ cấu hình 98 (Not ascertained) vào từ điển `SPECIAL` là hoàn toàn chuẩn xác.

2. **Cấu trúc lại Script Tuning (`day8_10_modeling.py`):**
   - Đóng băng (Data Lock) hoàn toàn bộ tiền xử lý `prep__` (OneHotEncoding cho CAT, StandardScaler cho NUM, Imputation) giống nguyên mẫu Day 5.
   - Khởi tạo quá trình dò tìm siêu tham số bằng `RandomizedSearchCV` thay vì `GridSearchCV` để hiệu quả hóa tài nguyên trên không gian mẫu lớn. Param grid chỉ tác động lên bộ phân loại `clf__`.
   - Áp dụng kỹ thuật `GroupKFold(n_splits=5)` dựa trên `HHX` để ngăn ngừa leakage nội bộ (nếu có các thành viên cùng gia đình, dù thực tế HHX đã được hash để split tổng thể).

3. **Chạy Tuning và Lưu kết quả:**
   - Kết quả xuất ra thành công 3 file: `day8_10_model_performance.csv`, `day8_10_calibration_points.csv`, `day8_10_config_log.json`.
   - Model XGBoost (weighted) đạt AUROC 0.8115, AUPRC 0.3187, F1 0.3483, cải thiện nhẹ, nhất quán so với baseline Day 5 (AUROC 0.810), chứng tỏ độ tin cậy của thuật toán.
   - Model Random Forest (weighted) đạt mức Recall ấn tượng nhất (52.92%), giúp phát hiện nhiều hơn người trưởng thành trong mẫu khảo sát có nguy cơ (forgone care).

**Bước tiếp theo (Next Steps):**
Chuyển sang **Day 11-13 (Survey-aware sensitivity analysis)**: Cần sử dụng các biến trọng số phức hợp (`PPSU`, `PSTRAT`) để tính toán lại các metric và đánh giá xem kết luận có thay đổi (sensitivity) khi áp dụng cấu trúc mẫu phức tạp (complex survey design) theo đúng Gate đã chốt, trước khi đi qua Day 14-16 (SHAP) và Day 17-19 (Fairness).
