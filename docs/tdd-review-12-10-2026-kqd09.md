# Biên bản review TDD — Thu nhận hồ sơ học viên (phạm vi §11D.11)

- **File review:** `docs/TDD.md` §11D.11 (+ §11D.6, dòng `Phục vụ`)
- **Ngày:** 12/10/2026
- **Người soát:** subagent `general-purpose` (Sonnet) đọc độc lập TDD + PRD + code + sổ mẫu TT17; user quyết từng điểm
- **Phạm vi:** KQD-09 — Xuất Excel kết quả học tập theo từng khóa
- **Số phát hiện:** 13 (Chặn: 2 · Nên sửa: 6 · Ghi nhận: 5) — Điểm 5 hiệu năng không có phát hiện

## Đã sửa

| # | Mức | Phát hiện | Cách xử |
|---|---|---|---|
| 4.1 | **Chặn** | Chuỗi bắt đầu `=` (họ tên, ghi chú, tên cơ sở) được ghi thành công thức Excel thật | **Sửa code** `_sach`/`_ghi_chu`: ép kiểu chữ + `quotePrefix` cho `= + - @`; test |
| 3.1 | **Chặn** | Một ký tự điều khiển trong tên làm openpyxl ném lỗi → cả khóa không xuất được | **Sửa code**: bỏ ký tự không hợp lệ, cắt 32.000 ký tự; test |
| 4.2 | Nên sửa | `PUT /local/config/co-so` không gác phiên | **Sửa code**: `require_session`; UI báo "cần đăng nhập" |
| 2.2 | Nên sửa | Hạng khối đầu không ổn định khi hòa phiếu | **Sửa code** (sắp chữ cái) + TDD; test |
| 1.3 | Nên sửa | Nhãn "Chưa đủ điểm Z" thực chất đếm HV chưa có kết luận | **Sửa code + PRD + TDD**: nhãn "Chưa có kết luận" |
| 1.2 | Nên sửa | TDD ghi `Thiếu: <môn>`, code ghi thêm `Chưa có điểm` khi trống cả 5 | Sửa TDD theo code |
| 2.1 | Nên sửa | "Hoàn thành" có thể nằm cạnh ô điểm trống (hệ quả §25) | Ghi rõ trong TDD, không lật quyết định |
| 6.1 | Nên sửa | Thiếu sơ đồ luồng + bảng cột → nguồn | Chèn ASCII + bảng vào đầu §11D.11 |

## Ghi nhận (đã ghi vào TDD)

| # | Phát hiện |
|---|---|
| 1.1 | TDD thiếu so với code: 2 loại 404, 500 chung, `Expose-Headers`, tên file dự phòng ở UI |
| 2.3 | Ngày xét hoàn thành trống khi khóa chưa có `NgayThi` |
| 3.2 | Khóa lớn: 5.000 HV ≈ 4 giây; CSĐT thực tế vài chục–vài trăm; hai người xuất cùng lúc không tranh chấp |
| 3.3 | Hai truy vấn riêng có thể lệch mili giây; `now()` là giờ máy CSĐT |
| 3.4 | `ORDER BY CAST(SoHoSo AS INT)` (dùng chung từ trước) lỗi nếu `SoHoSo` không phải số |

## Chưa kiểm được

- Mở file bằng Excel thật (cảnh báo công thức, định dạng in A4 ngang): chờ người dùng thử trên máy CSĐT.
