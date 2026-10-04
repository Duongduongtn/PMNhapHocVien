# Biên bản review TDD — PMCSĐTLX (§11B.7 Tra cứu CDB đích)

- **File review:** docs/TDD.md §11B.7 (Feature Tra cứu CDB đích, TCB-01..04)
- **Ngày:** 04/10/2026
- **Nguồn đối chiếu:** PRD [TCB-01..04], CHANGES #35, code thật `tool/app/` (routers/hoso.py, nap.py, khoahoc.py, db.py), DB-GPLX_CDB_CSDT.md
- **Số phát hiện:** 4 (Chặn: 1 · Nên sửa: 2 · Ghi nhận: 1)

## Đã sửa

| # | Điểm | Mức | Phát hiện | Đã sửa thế nào |
|---|---|---|---|---|
| 1 | 2 Logic mơ hồ | Chặn | "Đã BC1" trộn 3 tín hiệu khác cấp: `EXISTS BaoCaoI WHERE MaKH` (cấp khóa, code Nạp dùng) · `NguoiLX_HoSo.MaBC1` (cấp HV, FK NO_ACTION neo) · `TT_XuLy ≥ '05'` (cấp HV, thang mới). Chúng lệch nhau → TCB-04 (xóa không hoàn tác) chặn oan hoặc để lỗi SQL thô. | Chốt mốc "đã BC1" = **`NguoiLX_HoSo.MaBC1` có giá trị** (đúng cái FK chặn), bỏ 2 cách còn lại; vẫn bắt lỗi FK làm lưới. Sửa §11B.7 + PRD TCB-04. (user chọn A) |
| 2 | 3 Edge case | Nên sửa | Thay ảnh TCB-02 ghi đè file `.jp2` **dùng chung 2 DB** = phá hủy ảnh cũ vĩnh viễn, không backup (khác QLY-07 có `_BACKUP`). | Thêm bước **sao lưu `<tên>_BACKUP.jp2` cùng thư mục ảnh (chỉ nếu chưa có)** trước khi ghi đè. Sửa §11B.7 + PRD TCB-02. (user chọn A, lưu cùng thư mục ảnh) |
| 3 | 4 Bảo mật | Nên sửa | Endpoint TCB ghi vào CDB không ghi rõ chặn quyền (§12 buộc `/local/*` token operator). | Thêm câu: endpoint TCB ghi buộc **token operator**, collector 403. Sửa §11B.7. |
| 4 | 4 Bảo mật | Ghi nhận | Câu chữ §12 "DB đích: chỉ gọi SP" sai — TCB-02 UPDATE trực tiếp cột ảnh (SP không ghi ảnh). | Nới câu chữ §12: ghi nhân thân/kết quả qua SP, UPDATE cột ảnh trực tiếp parameterized. |
| 5 | 6 Sơ đồ | Ghi nhận | Luật khóa diễn đạt bằng 3 gạch đầu dòng, dễ sót. | +Bảng ma trận quyết định (3 thao tác × 3 mốc) vào §11B.7. |

## Điểm ổn (không phát hiện)

- **Điểm 1 (PRD↔TDD):** 4 mã TCB khớp đủ dòng `Phục vụ`, không thừa/thiếu; quy mô khớp (~60 bản ghi/khóa, nội bộ 1 CSDT).
- **Điểm 5 (Hiệu năng):** avatar lazy-load, thống kê đầu khóa 1 truy vấn, lưới ~60 bản ghi — đã tránh bài học "tải base64 cả khóa" (§9.3a).

## Cố tình bỏ qua

(không có)

## Hoãn lại

| # | Phát hiện | Chờ gì |
|---|---|---|
| — | CDB có `usp_NguoiLX_Update` / SP đổi khóa / SP xóa không (như GPLX_CSDT) | Kiểm khi code TCB-03/04; thiếu thì tắt nút + báo (đã ghi trong §11B.7 + CHANGES #35) |

## Kết luận

**§11B.7 đã đủ để bắt đầu code.** 0 phát hiện Chặn còn mở. Lưu ý khi code: mốc chặn đọc `MaBC1`/`SoQD_KhaiGiang` (KHÔNG đọc `TT_XuLy`); thay ảnh backup trước; endpoint ghi buộc token operator; xác minh SP CDB tồn tại trước TCB-03/04.
