# Hướng dẫn UHS rà bản thảo Day 23–24

## Kết luận cần giữ nguyên

Bản thảo v1 đã đủ Introduction, Methods, Results, Discussion, Limitations và Conclusion. Phần kỹ thuật đã khóa, nên UHS không cần chạy lại model hoặc tự sửa số trong bài. UHS cần rà ý nghĩa y tế công cộng, chọn cách mô tả use case và kiểm soát mức độ khẳng định.

## UHS cần làm gì

### 1. Chốt use case trước khi nói model nào phù hợp

UHS cần trả lời mô hình này chỉ dùng cho nghiên cứu mô tả, sàng lọc để mời đánh giá thêm, hay phân bổ một nguồn lực cụ thể. Sau đó mới mô tả chi phí của hai loại sai:

- False negative là bỏ sót người thực sự có rào cản chi phí.
- False positive là gắn cờ người không báo cáo rào cản, làm tăng khối lượng liên hệ hoặc nguồn lực theo dõi.

Nếu chưa có use case và tỷ lệ đánh đổi cụ thể, giữ câu “không có universal winner”. Không được chọn RF chỉ vì Recall cao, hoặc chọn XGBoost chỉ vì AUROC cao.

### 2. Rà tín hiệu insurance

RF ở threshold đã khóa gọi gần như toàn bộ người uninsured là positive. Với MEDNG, FPR uninsured là 0,975; với MEDDL là 1,000. Điều này nghĩa là RF bỏ sót ít positive trong nhóm này nhưng đồng thời gắn cờ gần như mọi negative. UHS cần diễn giải đây là vấn đề ở operating point, không phải bằng chứng model công bằng, không công bằng, phân biệt đối xử hoặc gây hại.

### 3. Rà cách viết SHAP

Chỉ dùng các cụm “đóng góp vào dự báo”, “predictive attribution”, “mô hình dựa nhiều hơn vào thông tin”. Không dùng “gây ra”, “dẫn đến”, “tác động làm tăng/giảm” nếu chỉ dựa trên SHAP. `HISPALLP_A` là biến phân tầng xã hội/cấu trúc, không phải nguyên nhân sinh học.

`CHRONIC_BURDEN_CAT` là số miền bệnh mạn đã chọn, gộp thành 0, 1, 2 và 3+. Nó không đo độ nặng lâm sàng. Bản mới đã sửa nhãn để 3+ không bị gộp với missing. Không cần chạy lại model; chỉ dùng bảng category đã sửa khi diễn giải mức 3+.

### 4. Rà các nhóm không đủ dữ liệu

Không viết kết luận so sánh cho NH Asian, NH AIAN, NH AIAN cộng nhóm khác, other or multiple và age 75+ nếu các nhóm này bị stability gate loại. “Không đủ dữ liệu để so sánh ổn định” không có nghĩa là “không có chênh lệch”.

### 5. Rà liên hệ Việt Nam

Chỉ đặt Việt Nam hoặc Đồng bằng sông Cửu Long trong phần bối cảnh và future work. Không chuyển trực tiếp prevalence, threshold, feature importance hoặc fairness gap từ NHIS Hoa Kỳ sang Việt Nam. Một nghiên cứu tại Việt Nam cần dữ liệu, định nghĩa outcome, thiết kế lấy mẫu và validation riêng.

### 6. Rà tài liệu tham khảo

Dùng `literature/literature_matrix_day6.csv` là danh sách hiện hành 19 nguồn. File XLSX 18 nguồn chỉ là snapshot cũ. Trước khi nộp, UHS cần kiểm tra lại tác giả, năm, DOI hoặc PubMed và chuyển sang style của tạp chí.

## UHS không nên làm gì

- Không tự sửa số trong Word; ghi comment và đối chiếu `docs/Day23_24_Claim_Traceability.csv`.
- Không mở lại tuning, calibration, feature selection hoặc threshold từ kết quả test.
- Không tạo một “winner” hậu nghiệm từ SHAP hoặc fairness.
- Không coi weighted count là số người được khảo sát.
- Không dùng threshold như cutoff lâm sàng hoặc chính sách.
- Không mô tả DCA exploratory là bằng chứng clinical utility.

## Bốn quyết định UHS cần trả lại UIT

1. Use case dự kiến là nghiên cứu mô tả, sàng lọc, hay phân bổ nguồn lực.
2. Trong use case đó, false negative hay false positive nghiêm trọng hơn, và vì sao.
3. Insurance có được giữ như predictor trong một kịch bản triển khai giả định hay chỉ dùng cho audit và mô tả.
4. Tạp chí hoặc hội nghị mục tiêu để chuẩn hóa word count, reference style, table và figure limits.

## File UHS cần đọc theo thứ tự

1. `docs/Day23_24_Manuscript_V1.md`
2. `docs/Day23_24_Claim_Traceability.csv`
3. `modeling/day20_22/day22_final_model_table.csv`
4. `modeling/day20_22/day22_final_error_table.csv`
5. `modeling/day14_16/figures/shap_global_constructs_MEDNG.svg` và `shap_global_constructs_MEDDL.svg`
6. `modeling/day17_19/figures/fairness_error_gap_MEDNG.svg` và `fairness_error_gap_MEDDL.svg`
7. `modeling/day20_22/figures/day20_22_weighted_error_tradeoff.svg`

Các script, config chi tiết và bảng one-hot chỉ cần UIT dùng khi audit sâu.
