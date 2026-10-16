# Biên bản review TDD — PMCSĐTLX (KQD-04 đổi, §11D.13)

- **File review:** docs/TDD.md (§11D.13 mới; §11D.1, §11D.6, §11D.9 đã sửa)
- **Ngày:** 16/10/2026
- **Người soát:** subagent review-tdd (context độc lập)
- **Đối chiếu:** PRD v4.19 (KQD-01/03/04/07), TDD-decisions §27, CHANGES #77, code `tool/app/routers/ketqua.py`, `config_store.py`
- **Số phát hiện:** 20 (Chặn: 3 · Nên sửa: 11 · Ghi nhận: 6)
- **Kết luận:** TDD v6.23 đủ để bắt đầu task 136 — cả 3 điểm Chặn đã đóng.

## Đã sửa

| # | Điểm | Mức | Phát hiện | Đã sửa thế nào |
|---|---|---|---|---|
| 1.1 | 1 PRD | Chặn | Lô không kiểm "chưa đủ điểm" như PRD | Dùng `hv_chua_du` (§11D.9) trước khi chuyển; bỏ qua `chua_du_diem` kèm mục thiếu |
| 1.2/4.1 | 1/4 | Nên sửa | Giải trình chung đè riêng | `CASE WHEN rỗng` + `ghi_de_rieng` (mặc định tắt); hộp xác nhận nêu số người giữ riêng |
| 1.3/3.1 | 1/3 | Chặn | HV 90 Không đạt/NULL không thuộc nhóm nào | Chip đỏ + tab "Cần xử lý"; KQD-07 đếm `khong_dat_o_90`/`thieu_ket_luan` |
| 1.4 | 1 | Ghi nhận | Thiếu dòng Phục vụ | Thêm `> Phục vụ: KQD-04, KQD-01, KQD-03, KQD-07` |
| 2.1 | 2 | Chặn | "Một giao dịch" nhưng kết nối tự lưu từng lệnh | Lô: `autocommit=False` + một UPDATE; `cap_nhat` lỗi bước chuyển → 200 `chua_chuyen_90` |
| 2.2 | 2 | Nên sửa | "Riêng rỗng thì dùng chung" mơ hồ | Giải trình hiệu lực: riêng → chung → giữ nguyên; xóa chỉ khi riêng rỗng và không có chung |
| 2.3 | 2 | Nên sửa | Hai đường vào 90 chưa nói chung luật | Một hàm `chuyen_14_sang_90` + cùng guard SQL |
| 3.2 | 3 | Nên sửa | Đua trạng thái khi lưu | Mọi ghi chặn 12/13; đọc lại trước SP → 409 `trang_thai_da_doi`; khe hở còn lại ghi Rủi ro (d) |
| 3.3 | 3 | Nên sửa | Lô không lọc cơ sở | `MaCSDT` = cơ sở máy, sai → `khong_thuoc_co_so` (cả `/cap-nhat`) |
| 3.4 | 3 | Nên sửa | Biên lô chưa nêu | Khử trùng/bỏ rỗng; >200 hoặc giải trình rỗng/>1000 → 422 |
| 3.5 | 3 | Ghi nhận | Giải trình bị xóa trắng sau phản hồi Sở | Chip `giai_trinh_trong` ở KQD-07 |
| 4.2 | 4 | Ghi nhận | Mẫu lưu chung máy, có thể lẫn PII | Lưu theo `target_key` + cảnh báo không ghi tên/căn cước |
| 5.1 | 5 | Nên sửa | Lưu mẫu có thể mất thay đổi cấu hình khác | Khóa ghi cấu hình + `phien_ban` + giới hạn 20×1000 (422) |
| 5.2 | 5 | Ghi nhận | `_NHOM_TT` không biểu diễn được điều kiện | Đổi sang điều kiện SQL dùng chung đếm/lọc/kiểm trước |
| 5.3 | 5 | Nên sửa | Thiếu lỗi/mất kết nối của lô | 502 `lo_loi`/`khong_ro`, gọi lại idempotent, timeout 30 giây |
| 6.1 | 6 | Nên sửa | Sơ đồ §11D.1 thiếu 90→12, nhánh giữ 14, ghi sai nguồn 90 | Thay nhánh 14/90 + đánh dấu ❔ |
| 6.2 | 6 | Ghi nhận | Thiếu sơ đồ trình tự lô | Thêm vào §11D.13 |
| U1 | user bổ sung giữa buổi | Yêu cầu | "Phải có cảnh báo chưa giải trình thì không kết xuất được" | Mục "Cảnh báo bắt buộc" §11D.13: 4 chỗ (sau Lưu, chip trên dòng, hộp hàng loạt, KQD-07) |
| 4.3 | 4 | Ghi nhận | Gác quyền ổn | Không cần sửa |

## Cố tình bỏ qua

| # | Phát hiện | Mức | Vì sao chấp nhận |
|---|---|---|---|
| — | Khe hở giữa "đọc lại trạng thái" và SP `_CapNhat` (SP không nhận guard `TT_XuLy`) | Nên sửa (còn lại một phần) | Máy một người dùng; ghi vào Rủi ro (d) §11D.13 |

## Hoãn lại

| # | Phát hiện | Chờ gì |
|---|---|---|
| — | PRD v4.19 lệch TDD v6.23: tab đổi tên "Cần xử lý", chip `giai_trinh_trong`, mẫu theo cơ sở | `/capnhat` đồng bộ PRD KQD-01/KQD-04 + mock `ui-mock/ketqua.html` |
| — | Phần mềm CDB có tự đặt `90` ở màn giải trình riêng không | Nghiệm thu máy CSĐT (BUILD-PLAN task 145) |
