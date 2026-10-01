# Biên bản review TDD — PMCSĐTLX

- **File review:** docs/TDD.md (phạm vi §10 — nạp HV qua SP gộp)
- **Ngày:** 01/10/2026
- **Nguồn đối chiếu:** thân SP `usp_QuangLA_PM4_ThuNhanHS_ThemMoiCapNhat` (DBcu), DB thật GPLX_CSDT (khóa B-K149, tham số hệ thống)
- **Số phát hiện:** 8 (Chặn: 2 · Nên sửa: 4 · Ghi nhận: 2)

## Đã sửa

| # | Điểm | Mức | Phát hiện | Đã sửa thế nào |
|---|---|---|---|---|
| P2.1 | 2 | Chặn | SP gộp KHÔNG ghi ảnh (set `TT_XuLy='01'`, `KIEM_TRA_ANH='fpt@'`≠`'fpt@123'`); 55/55 HV thật `'03'`+ảnh. Luồng §10.1/§10.1b thiếu bước ghi ảnh | Thêm bước (hướng A): sau SP → ghi `.jp2` → UPDATE 5 cột ảnh (`DuongDanAnh`,`ChatLuongAnh=1`,`TT_XuLy='03'`,`NgayThuNhanAnh`,`NguoiThuNhanAnh`); chưa ảnh giữ `'01'`. §10.1, §10.1b, §10.3 |
| P3.1 | 3 | Chặn | SP trả lỗi nghiệp vụ qua `@p_out` (-1..-4), KHÔNG raiserror → tool bắt exception sẽ bỏ sót | §10.1 + §10.3: tool đọc `@p_out`, `≠0`→không insert, báo lỗi, giữ pending |
| P2.2 | 2 | Nên sửa | §10.1 còn để ngỏ MaDK/SoHoSo/DuongDanAnh | Chốt: `@p_MaDK=NULL`→SP sinh (`70004-<ts>`, OUTPUT); `SoHoSo` caller truyền; SP không ghi ảnh |
| P2.3 | 2 | Nên sửa | §10.2 ghi "tool tách họ tên" — thực ra SP tự tách | §10.1 + §10.2: SP tự tách từ `@p_HoVaTen`; tool tách chỉ để kiểm độ dài |
| P2.4 | 2 | Nên sửa | §10.2 `GiayCNSK=1` (hằng) sai | §10.2: `=1` chỉ khi `@p_GiayTo` chứa `'3,'` (giấy KSK) |
| P3.2 | 3 | Nên sửa | §10.3 "SP atomic an toàn" — SP dùng `@@error` cũ, không TRY/CATCH | §10.3: tool `SET XACT_ABORT ON` trước EXEC |
| P2.5 | 2 | Ghi nhận | §10.2 `MaLoaiHs` thiếu case 3 (nâng hạng) | §10.2: thêm case `HangDT` chứa `'-'`→3 |
| — | 1 | Ghi nhận | Tên tham số ảnh thật = `IMG_PATH_CSDT` (TDD ghi chung "IMG_PATH") | §10.1: sửa thành `IMG_PATH_CSDT` |

## Cố tình bỏ qua

(Không có — mọi phát hiện Chặn đều đã đóng.)

## Hoãn lại / cần `/capnhat` (việc PRD, ngoài phạm vi review TDD)

| # | Phát hiện | Chờ gì |
|---|---|---|
| 1 | Hướng A (UPDATE thẳng 5 cột ảnh) đụng dòng ❌ PRD NAP-05 "không UPDATE bảng trực tiếp" | `/capnhat` nới ràng buộc: cho phép UPDATE cột ảnh kỹ thuật (CHANGES #5) |
| 2 | Kịch bản 3: nút "Nạp ảnh" riêng cho HV đã nạp (bổ sung ảnh sau bằng tool) | Story mới qua `/capnhat` — làm SAU NAP-05 (code ghi ảnh dùng lại được) |
| 3 | Tiêu đề PRD NAP-05 vẫn ghi "qua 3 SP" (Steps/Done đã đổi) | `/capnhat` sửa tiêu đề |

## Quyết định UX đã chốt (user, 01/10/2026)

- **Một nút "Nhập học viên"**, khu ảnh là phần tùy chọn trong cùng màn; bấm Nạp một lần. Chưa ảnh → cảnh báo mềm, vẫn nạp (`TT_XuLy='01'`).
- **Bổ sung ảnh sau:** bằng app cũ (được ngay, cùng DB) hoặc bằng nút "Nạp ảnh" trên màn tra cứu HV (kịch bản 3, story mới).

## Kết luận

**TDD §10 đã đủ để bắt đầu code lại NAP-05** — 0 phát hiện Chặn còn treo. Trước khi code cần `/capnhat` nới dòng ❌ PRD NAP-05 (mục Hoãn #1) để hướng A không nghịch PRD. Bước tiếp theo: `/kehoach` bổ sung (reconcile task 9+10) → `/tieptheo` code NAP-05.
