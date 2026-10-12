# Biên bản review TDD — Thu nhận hồ sơ học viên (phạm vi §11D.12)

- **File review:** `docs/TDD.md` §11D.12 (+ §11D.6, dòng `Phục vụ`)
- **Ngày:** 12/10/2026
- **Người soát:** subagent `general-purpose` (Sonnet) đọc độc lập TDD + PRD + code + file mẫu `SO_PHU_LUC_VI`; user quyết từng điểm
- **Phạm vi:** KQD-10 — Xuất Sổ theo dõi kết quả học tập (mẫu Phụ lục VI, TT17)
- **Số phát hiện:** 11 (Chặn: 0 · Nên sửa: 5 · Ghi nhận: 6) — Điểm 4 bảo mật và Điểm 5 hiệu năng không có phát hiện

## Đã sửa

| # | Mức | Phát hiện | Cách xử |
|---|---|---|---|
| 2.1 | Nên sửa | Thanh điệu so từng ký tự → `Hòa`/`Hoà`, `Thúy`/`Thuý` xếp lệch nhau | **Sửa code** (một thanh mỗi âm tiết) + test |
| 3.1 | Nên sửa | Độ rộng cột Họ tên đoán thấp với tên VIẾT HOA (DB lưu hoa) → bị thu nhỏ chữ sớm | **Sửa code** (hoa 1,6 / khác 1,05) + test |
| 1.1 | Nên sửa | Viền đen, chân trang cỡ 11, hàng 5/9 mặc định — lệch mẫu (xám `A6A6A6`, 10, 15,75) | **Sửa code** theo mẫu + test so trực tiếp file mẫu |
| 1.2 | Nên sửa | `footer` 0,5 inch đè dòng cuối khi lề dưới 1,5 cm | **Sửa code** `footer = 0,3` |
| 1.3 | Nên sửa | §11D.6 còn ghi `GET xuat-excel … tải file` | Sửa TDD |
| 2.4 | Ghi nhận | HV có kết luận nhưng thiếu điểm → ô kết quả trống, màn hình không giải thích | **Thêm** `so_hv_trong_ket_qua` + dòng lưu ý ở thanh thông báo |
| 3.2 | Ghi nhận | Khối cơ quan/cơ sở tên dài > 3 dòng bị cắt | **Sửa code** tăng chiều cao hàng 2 |

## Ghi nhận (đã ghi vào TDD)

| # | Phát hiện |
|---|---|
| 2.2 | Đủ 5 điểm nhưng chưa có kết luận → ô kết quả trống |
| 2.3 | Khóa chưa có `NgayThi` → ô Ngày xét trống dù Hoàn thành |
| 3.3 | Cột C (Khóa học) cũng thu nhỏ chữ khi vượt trần 14 |
| 3.4 | `ORDER BY CAST(SoHoSo AS INT)` dùng chung lỗi nếu `SoHoSo` không phải số (chưa thấy dữ liệu như vậy) |
| 6.1 | "~22/~31 dòng mỗi trang" chỉ đúng khi cột B giữ 25; tên dài ~27/~35 (ước lượng, cần in thử) |

## Chưa kiểm được

- Hiển thị/in thật bằng Excel (tên có thật sự giữ 1 dòng, `Trang x/y` không đè, số dòng/trang): máy dev không có Excel/LibreOffice — cần người dùng in thử.
