# Sổ bug

> File do `/suabug` ghi. Khác `CHANGES.md`: file kia ghi **thay đổi yêu cầu**, file này ghi **code không làm đúng yêu cầu đã có**.

| # | Ngày | Mức | Story | Bug | Trạng thái | Deploy |
|---|---|---|---|---|---|---|
| 1 | 03/10/2026 | 🔴 Chặn | `QLY-08` | Gỡ về chờ nạp rồi nạp lại cùng uuid → HV KHÔNG vào DB nhưng tool báo thành công | ✅ Đã sửa | ⬜ (tool chưa lên VPS — có hiệu lực khi chạy lại tool) |

Chú thích trạng thái: ✅ Đã sửa · 🔄 Đang sửa · ⏳ Đã xếp task · ⬜ Chưa xử

---

## BUG-01 — Gỡ về chờ nạp rồi nạp lại → học viên không vào DB · 03/10/2026

- **Mức:** 🔴 Chặn (mất dữ liệu: tool báo nạp thành công nhưng HV không có trong CSDT)
- **Story:** `QLY-08` (liên quan `NAP-01` nạp lô)
- **Ai báo:** chủ dự án, khi test tool trên máy CSDT (nạp Lê Thị Hồng vào khóa 70004K26B010, không thấy trong DB)
- **Tái hiện:** Nạp 1 HV → "Gỡ về chờ nạp" (QLY-08) → "Kéo về từ VPS" → chuẩn bị → "Nạp" lại cùng HV. Tool báo "đã nạp" với số hồ sơ cũ, nhưng tra DB theo CCCD/MaDK → **rỗng**.
- **Nguyên nhân gốc:** `nap.keo_ve_ve_cho()` (QLY-08 bước 5) reset dòng `keo_ve` về `'cho'` nhưng **không xóa vé idempotency trong bảng `nap_xong`** (uuid→MaDK). Vé này do lần nạp đầu tạo ra để chống bấm nạp 2 lần. Khi gỡ về chờ nạp, HV đã bị xóa khỏi CSDT nên vé cũ trỏ tới MaDK đã chết. Lần nạp lại, `nap.nap_mot_hv()` gọi `_done_get(uuid)` thấy vé còn → **trả kết quả cũ, bỏ qua INSERT thật** (short-circuit idempotency bắn nhầm). Hệ quả: không bản ghi mới trong DB, staging bị set lại `'xong'` với MaDK đã xóa.
- **Đã sửa:** `tool/app/nap.py` — `keo_ve_ve_cho()` xóa luôn `DELETE FROM nap_xong WHERE uuid=?` trước khi reset dòng (không phụ thuộc dòng keo_ve còn hay không).
- **Dọn dữ liệu kẹt:** vé `nap_xong` của Lê Thị Hồng (uuid `3e162f1e-…`, MaDK chết `70004-20261002214215390`) đã được gỡ; dòng về `'cho'` để nạp lại.
- **Test hồi quy:** `tool/tests/test_nap_keo.py` — `test_keo_ve_ve_cho_go_ve_khoi_nap_xong` + `test_keo_ve_ve_cho_go_ve_nap_xong_du_da_bo_khoi_hang_doi` (fail trên code cũ, pass trên code mới).
- **Deploy:** tool chạy cục bộ máy CSDT (chưa đóng gói/lên VPS) → có hiệu lực ngay khi chạy lại tool; backend dev đã restart code mới lúc sửa.
