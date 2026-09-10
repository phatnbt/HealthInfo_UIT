# NHẬT KÝ NGHIÊN CỨU NHIS 2024
## Day 23–24 — Hoàn thiện bản thảo v1 từ kết quả đã đóng băng

**Nhóm thực hiện:** UIT — kỹ thuật; UHS — rà y tế công cộng và tổng quan

**Trạng thái:** HOÀN THÀNH DAY 23–24

**Phạm vi:** ghép Introduction, Methods, Results, Discussion, Limitations, Conclusion; lập bảng truy vết số liệu; khóa danh sách bảng/hình; không chạy lại model

## 1. Mục tiêu trong ngày

- Hoàn thành bản thảo v1 theo mốc Day 22–24 của plan bốn tuần.
- Ghép Methods và Results đã tái lập với Background, Discussion và Limitations.
- Đảm bảo mọi con số trong bản thảo có thể truy ngược tới output đã freeze.
- Tách rõ phần kỹ thuật UIT và phần UHS cần xác nhận.
- Không tạo winner, không mở lại tuning và không diễn giải SHAP thành nguyên nhân.

## 2. Công việc đã thực hiện

- Đối chiếu lại plan bốn tuần và xác nhận Day 22–24 là mốc code freeze cộng manuscript v1.
- Truy ngược quan hệ giữa Day 8–10, Day 11–13, Day 14–16, Day 17–19 và Day 20–22 bằng graph dự án.
- Kiểm tra cohort flow, feature lock, split audit, final performance, SHAP, subgroup fairness, error và robustness tables.
- Viết bản thảo đầy đủ gồm Abstract, Introduction, Methods, Results, Discussion, Limitations, Conclusions, Data availability và Ethics/privacy.
- Tạo bảng claim traceability 16 dòng để mỗi nhóm kết luận có file nguồn, locator và giới hạn diễn giải.
- Tạo hướng dẫn UHS bằng tiếng Việt, nêu bốn quyết định UHS cần trả lại trước khi chọn primary model.
- Lập index năm bảng chính, bốn figure chính và một supplementary figure; tái sử dụng output đã freeze thay vì tạo bản sao dễ lệch số.
- Cập nhật số lượng manifest hiện hành từ 29 lên 30 sau controlled correction ở lớp báo cáo `CHRONIC_BURDEN_CAT`.

## 3. Công cụ sử dụng

- Git để kiểm tra trạng thái và provenance.
- Graphify knowledge graph để lần từ script tới output và nhật ký.
- Python và `pandas` để đọc, lọc và đối chiếu các bảng aggregate.
- SHA-256 manifest và validator của Day 20–22 để xác nhận trạng thái freeze.
- `python-docx` và LibreOffice renderer để tạo, render và kiểm tra bản Word bàn giao.

## 4. Các bước xử lý

1. Đọc plan gốc và xác nhận đầu ra bắt buộc Day 22–24 là bản thảo v1 đầy đủ cộng figures/tables final.
2. Giữ nguyên computational freeze; không chạy modeling, tuning, calibration hoặc threshold selection mới.
3. Dùng `audit/cohort_flow.csv`, feature lock và split audit để viết Data, Outcomes, Predictors và Leakage control.
4. Dùng Day 8–10 và Day 11–13 để viết Performance và Survey-aware sensitivity.
5. Dùng Day 14–16 để viết Explainability, kèm ranh giới predictive attribution, không causal.
6. Dùng Day 17–19 và Day 20–22 để viết subgroup errors, robustness và limitations.
7. Đối chiếu từng số quan trọng với file nguồn và ghi vào claim traceability.
8. Viết Discussion theo logic kết quả: không có winner vì metric và error trade-off trả lời các câu hỏi khác nhau.
9. Tạo checklist UHS cho use case, FN/FP cost, insurance, causal language, sparse groups và liên hệ Việt Nam.
10. Chạy validator Day 23–24 và các validator upstream; render toàn bộ trang Word để kiểm tra bố cục.

## 5. Kết quả

- Bản thảo v1 đầy đủ đã được tạo mà không thay đổi model hoặc số liệu freeze.
- 16 nhóm claim được gắn với file nguồn và giới hạn diễn giải.
- Kết luận chính vẫn là không có universal winner.
- Tín hiệu cần UHS ưu tiên giải thích là trade-off false negative–false positive, đặc biệt RF ở nhóm uninsured.
- SHAP chỉ được dùng cho predictive attribution; `CHRONIC_BURDEN_CAT` được mô tả là burden category, không phải clinical severity.
- Liên hệ Việt Nam/ĐBSCL được giữ ở future work, không suy rộng trực tiếp từ NHIS Hoa Kỳ.
- Manifest hiện hành có 30/30 hash entries khớp sau controlled report-layer correction.

## 6. Vấn đề phát sinh / lưu ý

- Plan gộp Day 22–24 trong một hàng; Day 22 đã hoàn thành code freeze trước đó, nên Day 23–24 chỉ làm manuscript assembly.
- Tài liệu Day 20–22 cũ ghi 29 manifest entries. Trạng thái hiện hành là 30 vì validator Day 14–16 được thêm vào freeze sau bản sửa nhãn `3+`; đây không phải model retuning.
- Phần Discussion cần UHS xác nhận use case. Nếu chưa chốt chi phí FN/FP, không được chọn model chính.
- References hiện là ma trận narrative review 19 nguồn, chưa được format theo tạp chí.
- Bản thảo chưa phải bản nộp; Day 25–26 vẫn cần audit code-to-manuscript và phản biện chéo.

## 7. Quyết định / bước tiếp theo

- Đánh dấu Day 23–24 hoàn thành và chuyển sang Gate 5 preparation.
- Giữ nguyên code, model, threshold, seed và output đã freeze.
- UHS rà bản thảo bằng comment, không tự thay số.
- UHS trả lời bốn quyết định: use case, ưu tiên FN hay FP, vai trò insurance và venue mục tiêu.
- Day 25–26 chạy consistency audit toàn bộ con số, caption, tên biến, causal language, ethics/privacy và references.

## 8. Sản phẩm tạo ra

- `docs/Day23_24_Manuscript_V1.md`
- `docs/Day23_24_Claim_Traceability.csv`
- `docs/Day23_24_UHS_Review_Guide.md`
- `docs/Day23_24_Final_Figure_Table_Index.md`
- `scripts/validate_day23_24_outputs.py`
- `research_log/Day23_24_Manuscript_Assembly.md`
- Bản Word manuscript, bản Word nhật ký và gói ZIP bàn giao.

**Kết luận trạng thái:** Day 23–24 hoàn thành ở mức manuscript v1; computational state vẫn freeze; bước tiếp theo là consistency audit Day 25–26.
