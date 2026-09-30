# Biên bản review PRD — Thu nhận hồ sơ học viên

> Ghi ở `docs/prd-review-30-09-2026.md`, không ghi đè PRD. PRD sửa riêng ở `docs/PRD.md`.

| | |
|---|---|
| **File PRD được review** | `docs/PRD.md` — phiên bản v1 → v2, ngày 30/09/2026 |
| **Ngày review** | 30/09/2026 |
| **Người review** | AI (senior PM) |
| **Người quyết định** | Chủ dự án |
| **Có `docs/ba/` để đối chiếu** | Có — `docs/ba/thu-nhan-ho-so-hoc-vien/` (cỡ Vừa, không có 12/13) |

---

## 1. Kết luận

> **PRD này đã đủ để bắt đầu code chưa?** → **Đủ để bắt đầu** (với 2 giả định Nền móng phải kiểm trước khi code phần liên quan).
>
> PRD phủ đủ 9 mục, năng lực, edge case (bao gồm 4 trục bắt buộc T2/T3/T4/T7), lỗ hổng vận hành và phân quyền. Sau review đã đóng ca đồng thời (2 tool/double-click), chốt khung ảnh 3:4 + nền trắng, và làm rõ Done-khi. Còn 2 việc kiểm trước khi viết code phần liên quan: **AS-001 test thẻ CCCD thật** (định dạng đã xác nhận) và **AS-003 nạp thử 1 HV** ra bản ghi khớp app cũ. 4 ô `[CHƯA CHỐT]` (budget/timeline/team/số HV) không chặn thiết kế.

| Mức | Phát hiện | Đã sửa | Bỏ qua |
|---|---|---|---|
| Chặn | 1 | 1 | 0 |
| Nên sửa | 7 | 7 | 0 |
| Ghi nhận | 2 | 2 | 0 |
| **Tổng** | 10 | 10 | 0 |

Còn 4 ô `[CHƯA CHỐT]` trong PRD (budget, timeline, team size, số HV/thời gian gõ).

---

## 2. Đối chiếu với `docs/ba/`

| Phép | Tổng | Khớp | Thiếu | Mâu thuẫn |
|---|---|---|---|---|
| Đ1 — CAP (từ 11-brd §9) | 15 | 15 | 0 | 0 (lưu ý ưu tiên: CAP-010/011/012 BA ghi "Bắt buộc" nhưng PRD để SHOULD theo quyết định user lúc /prd) |
| Đ2 — EC mức Chặn | 4 | 4 | 0 (EC-010 đã bổ sung sau review) | 0 |
| Đ3 — BR liên quan | 20 | 20 | — | 0 |
| Đ4 — OG mức `Chặn go-live` | 4 | 4 | 0 | 0 |

---

## 3. Danh sách phát hiện

| Mã | Điểm | Mức | Vị trí | Vấn đề (1 câu) | Quyết định |
|---|---|---|---|---|---|
| PH-001 | 1 | Ghi nhận | ⑧+⑨ | 4 ô [CHƯA CHỐT] | Giữ, gắn hạn trước /kehoach |
| PH-002 | 1 | Nên sửa | ② Target User | Số lượng user mơ hồ | Sửa |
| PH-003 | 1 | Nên sửa | ⑧ Metrics | "phần lớn học viên" không đo được | Sửa |
| PH-004 | 2 | Nên sửa | ③ NAP-05 Done | "đầy đủ" mơ hồ | Sửa |
| PH-005 | 3 | Chặn | ③ NAP-05 + ⑦ | Thiếu ca 2 tool/double-click cùng nạp | Sửa |
| PH-006 | 3 | Nên sửa | ③ THU-02/NAP | Thiếu ca tên/địa chỉ vượt độ dài cột | Sửa |
| PH-007 | 4 | Nên sửa | ⑨ Assumptions | GĐ smartphone, đồng hồ máy, rembg, tài nguyên máy chưa ghi | Sửa (thêm 4 GĐ) |
| PH-008 | 5 | Nên sửa | ③ NAP-05 | Giấy tờ auto "đủ" vs bỏ tick tay | Sửa (theo tick cuối) |
| PH-009 | 5 | Ghi nhận | 🟠 THU-03 | Offline vs kiểm trùng/map DVHC cần DB | Sửa (thêm ghi chú) |
| PH-010 | 3(ảnh) | Nên sửa | ③ NAP-04 | Chưa chốt khung chuẩn + grab | Sửa (3:4 grab, nền trắng, 353×471) |

Không có phát hiện nào bị rút.

---

## 4. Chi tiết phát hiện chính

### PH-005 · Điểm 3 · Mức: Chặn
📍 NAP-05 + ⑦
🔍 Nguyên văn (trước): chỉ có "Nạp đồng thời tranh Số hồ sơ".
❗ Vấn đề: chưa xử lý hai tool cùng nạp một bản ghi + bấm nút hai lần → tạo học viên trùng trong DB thật.
✍️ Đề xuất: khóa bản ghi khi `importing`; disable nút + idempotent theo UUID.
💬 User: OK.
✅ Quyết định: Sửa — đã thêm 2 edge NAP-05 + 2 dòng ⑦.

### PH-010 · Ảnh · Mức: Nên sửa
📍 NAP-04
🔍 Nguyên văn (trước): ".jp2 480×640".
❗ Vấn đề: chưa xác định khung chuẩn; user yêu cầu grab ảnh + nền trắng.
✍️ Đề xuất: đo 300 ảnh thật → khung 3:4 (78%), cụm áp đảo 353×471, RGB, ~48 KB. Crop 3:4 grab di chuyển+zoom, nền trắng, xuất 353×471 (hoặc 480×640).
💬 User: OK, nhớ nền trắng.
✅ Quyết định: Sửa — đã cập nhật NAP-04.

### PH-002/003/004/006/007/008/009
Đều mức Ghi nhận/Nên sửa, user duyệt "OK" theo từng điểm; đã ghi vào PRD (xem mục 5).

---

## 5. Thay đổi đã ghi vào PRD (v2)

| # | Mục PRD | Từ phát hiện |
|---|---|---|
| 1 | ② số lượng user (~3–10 / 1–2) | PH-002 |
| 2 | ③ THU-02 edge tên/địa chỉ dài | PH-006 |
| 3 | ③ NAP-04 khung 3:4 grab + nền trắng + 353×471 | PH-010 |
| 4 | ③ NAP-05 Done trường khớp cụ thể | PH-004 |
| 5 | ③ NAP-05 giấy tờ theo tick cuối | PH-008 |
| 6 | ③ NAP-05 edge + ⑦ ca đồng thời | PH-005 |
| 7 | ⑧ metric ≥80% đếm theo NgayTao | PH-003 |
| 8 | ⑨ +4 giả định + AS-001 6/7 trường | PH-007 |
| 9 | 🟠 THU-03 ghi chú offline | PH-009 |

Dòng Changelog đã thêm: `30/09/2026 | v2 — sửa sau review: ... | PM`

---

## 6. Rủi ro đã biết và chấp nhận

Không có (không có phát hiện Chặn nào bị bỏ qua).

---

## 7. Việc phải làm trước khi code

| # | Việc | Ai làm | Từ |
|---|---|---|---|
| 1 | Test chuỗi QR trên vài thẻ CCCD thật của cơ sở | NV thu nhận | AS-001 |
| 2 | Nạp thử 1 HV thật → mở app cũ đối chiếu | Dev + chủ dự án | AS-003 |
| 3 | Chốt 4 ô [CHƯA CHỐT] (budget/timeline/team/số HV) trước /kehoach | Chủ dự án | PH-001 |
| 4 | (Tùy chọn) Đồng bộ ưu tiên CAP-010/011/012 giữa 11-brd §9 và PRD qua `/phantichnghiepvu` Pha 8 | BA | Đ1 |
