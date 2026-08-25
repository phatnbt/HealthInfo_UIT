# Day 1 — Xác minh nguồn dữ liệu và tính toàn vẹn

## 1. Mục tiêu
Xác nhận bộ dữ liệu sử dụng là NHIS 2024 Sample Adult chính thức của CDC/NCHS và xác định các biến survey design cần giữ.

## 2. Công cụ sử dụng
- CDC/NCHS NHIS 2024 Documentation
- Adult Codebook
- Survey Description
- Checksum/Filelist
- Python 3: `csv`, `hashlib`, `zipfile`
- Excel để tổng hợp audit

## 3. Các bước xử lý
1. Tải `adult24csv.zip` và `adultinc24csv.zip` từ CDC/NCHS.
2. Giải nén thành `adult24.csv` và `adultinc24.csv`.
3. Đếm số dòng bằng Python.
4. Tính MD5 và đối chiếu checksum official.
5. Kiểm `IMPNUM_A` trong income file để xác nhận 10 multiple imputations cho mỗi `HHX`.
6. Xác nhận `WTFA_A`, `PSTRAT`, `PPSU` tồn tại và giữ lại cho survey analysis.

## 4. Kết quả
- `adult24.csv`: 32,629 records; MD5 `6b0d5e572841ffef7b0f7df4ddfed556`.
- `adultinc24.csv`: 326,290 records; MD5 `14a1d5780100c1b0a13acce433e00360`.
- 326,290 = 32,629 × 10; mỗi `HHX` có `IMPNUM_A` 1–10.

## 5. Vấn đề / lưu ý
- Không chỉnh sửa trực tiếp raw data.
- `HHX` chỉ dùng làm ID/merge key.
- `WTFA_A`, `PSTRAT`, `PPSU` không dùng làm ML predictors.

## 6. Quyết định
Chấp nhận `adult24.csv` làm raw dataset chính. Income/poverty phải lưu ý 10 multiple imputations khi làm formal inference.

## 7. Sản phẩm
- Source integrity audit
- `AUDIT_MANIFEST.json`
- Sheet `Source_Integrity` trong workbook Day 1–4
