# Day 2 — Xác minh outcome và xây dựng cohort

## 1. Mục tiêu
Xác minh hai outcome cost-related unmet medical care và tạo cohort phân tích độc lập cho từng outcome.

## 2. Công cụ sử dụng
- NHIS 2024 Adult Codebook
- Python 3
- `csv`, `collections.Counter`
- Excel để kiểm target counts và cohort flow

## 3. Các bước xử lý
1. Kiểm `MEDNG12M_A` trong raw data.
2. Giữ code `1=Yes`, `2=No`; loại `7/8/9` khỏi cohort của outcome này.
3. Tạo `TARGET_FORGONE_COST` với 1=Yes, 0=No.
4. Kiểm `MEDDL12M_A` tương tự và tạo `TARGET_DELAYED_COST`.
5. Tạo hai cohort độc lập trực tiếp từ `adult24.csv`.
6. Tạo thêm common-valid cohort chỉ để paired/overlap analysis.
7. Tính unweighted và `WTFA_A`-weighted prevalence.

## 4. Kết quả
### MEDNG12M_A
- Yes: 2,195
- No: 30,159
- Valid N: 32,354
- Unweighted prevalence ≈ 6.784%
- Weighted prevalence ≈ 7.387%

### MEDDL12M_A
- Yes: 2,564
- No: 29,791
- Valid N: 32,355
- Unweighted prevalence ≈ 7.925%
- Weighted prevalence ≈ 8.579%

### Common-valid cohort
- N = 32,345

## 5. Vấn đề / lưu ý
Không được lọc MEDDL từ cohort MEDNG hoặc ngược lại, vì sẽ làm mất người hợp lệ của outcome còn lại.

## 6. Quyết định
- `MEDNG12M_A` = primary outcome.
- `MEDDL12M_A` = secondary/comparative outcome.
- Main analysis không gộp hai outcome.
- Mỗi model sau này dùng cohort riêng.

## 7. Sản phẩm
- `analysis_ready_MEDNG_EXACT_RAWCODES.csv`
- `analysis_ready_MEDDL_EXACT_RAWCODES.csv`
- `analysis_ready_COMMON_EXACT_RAWCODES.csv`
- `cohort_flow.csv`
- Sheets `Target_Audit`, `Cohort_Flow`
