# Biên bản review TDD — PMCSĐTLX

- **File review:** docs/TDD.md (§9.3a, §10.5, §11.5) + docs/TDD-decisions.md (§11) — phạm vi CHANGES #32
- **Ngày:** 04/10/2026
- **Đối chiếu:** docs/PRD.md (NAP-01, QLY-05), docs/CHANGES.md #32, code tool hiện có, DB thật GPLX_CSDT (chỉ đọc)
- **Số phát hiện:** 4 (Chặn: 0 · Nên sửa: 2 · Ghi nhận: 2)

## Đã sửa

| # | Điểm | Mức | Phát hiện | Đã sửa thế nào |
|---|---|---|---|---|
| 1 | 4 — PII | Nên sửa | Nháp bỏ dở (dòng `cho` không nạp, VPS không xóa) giữ ảnh căn cước vĩnh viễn trên máy tool; 3 lối tự-xóa không phủ, trái cam kết §11 "không để tồn dư". Job PII 30 ngày VPS không kéo theo xóa nháp tool. | Hướng B: thu hẹp cam kết TDD-decisions §11 (ghi rõ giới hạn) + thêm nút "Xóa nháp" chủ động trên drawer (§9.3a/§10.5). |
| 2 | 5 — Hiệu năng | Nên sửa | §9.3a chỉ có GET-theo-uuid trả full `jp2_b64`+preview; vẽ 2 chip cho cả lưới phải tải toàn bộ ảnh base64 cả khóa chỉ để biết "có hình chưa" → giật, tốn RAM. | Hướng A: thêm endpoint list NHẸ `GET /local/nap/nhap?uuids=` trả cờ boolean; full GET chỉ khi mở drawer (§9.3a/§10.5). |
| 3 | 2 — Logic | Ghi nhận | BUG-04 reset "chi_tiet tính lại từ raw" đè phần operator tự gõ. | Hướng A: giữ recompute (raw đổi = địa chỉ khác hẳn, map lại đằng nào cũng xem lại chi_tiet). |
| 4 | 6 — Sơ đồ | Ghi nhận | §9.3a mô tả vòng đời nháp bằng chữ, nhiều nhánh xóa dễ sót khi code. | Chèn sơ đồ ASCII vòng đời nháp vào cuối §9.3a. |

### Phát sinh trong review (ngoài 6 điểm) — đã xử

| Chủ đề | Xử lý |
|---|---|
| Luật ghép địa chỉ `chi_tiet` + 2 cấp phải có dấu phẩy | Soi DB thật: DB **không** ghép (2 cột riêng), `DM_DVHC.TenDayDu` đã có phẩy giữa các cấp, tool popup đã `join(", ")`. Chốt chuẩn hóa ở **lớp hiển thị tool** (không nhét phẩy vào `NoiTT` — giữ §10.2); app cũ render ngoài tầm. Ghi luật vào §9.3a + áp preview drawer §10.5. |

## Cố tình bỏ qua

(không có — 2 phát hiện Nên sửa đều đã xử)

## Hoãn lại

(không có)

## Kết luận

TDD #32 **đã đủ để bắt đầu code** — 0 phát hiện Chặn còn mở. 2 Nên sửa đã đưa vào thiết kế (endpoint list nhẹ + nút Xóa nháp/giới hạn PII), 2 Ghi nhận đã áp. Bước tiếp theo: `/kehoach` bổ sung task #32 vào BUILD-PLAN, rồi code (UI chạy skill `impeccable`), xong `/capnhatgitnexus`.
