# Biên bản review TDD — PMCSĐTLX

- **File review:** docs/TDD.md (phạm vi #51 / NAP-01 — "Bỏ khỏi hàng đợi" cho dòng chờ/lỗi + tombstone `keo_ve_bo_qua`)
- **Ngày:** 08/10/2026
- **Số phát hiện:** 7 (Chặn: 0 · Nên sửa: 3 · Ghi nhận: 4)
- **Nguồn đối chiếu:** PRD [NAP-01] · CHANGES #51 · TDD-decisions §11 · code `tool/app/nap.py` + `tool/app/routers/nap.py`

## Đã sửa

| # | Điểm | Mức | Phát hiện | Đã sửa thế nào |
|---|---|---|---|---|
| 1 | Đ1 PRD / Đ2 logic | Nên sửa | Hai endpoint cùng lo "Bỏ khỏi hàng đợi" (`DELETE /keo-ve/:uuid` xong-only + `POST /bo-qua`); TDD không chốt số phận DELETE → rủi ro nới guard DELETE cho cho/lỗi mà không ghi tombstone → kéo lại mang về (đúng bug #51 muốn chặn) | Phương án A: **GỠ `DELETE /local/keo-ve/:uuid`**, gộp 1 đường `POST /local/nap/bo-qua` (mọi trạng thái, 1 hay nhiều dòng). Sửa §4 + §7.2. Ghi chú UI phải chuyển DELETE→POST |
| 2a | Đ2 logic | Nên sửa | Endpoint nhận `{uuids}` trần, không nói lấy trạng thái ở đâu để quyết định ghi tombstone | §9.3b +pseudo-logic: tra `keo_ve_trang_thai(uuid)` từng uuid; tombstone cho `cho`/`loi` |
| 2b | Đ2 logic | Nên sửa | uuid không còn trong `keo_ve` (`None`: kéo trôi / gọi lại) — có ghi tombstone không? | Chốt: `None` **vẫn ghi tombstone** (operator đã chủ ý bỏ, chặn kéo lại nếu VPS còn pending) |
| 2c | Đ2 logic | Ghi nhận | "Không tombstone cho `xong`" chỉ nói "ghi thừa" — chưa nêu hậu quả thật, dễ bị "ghi luôn cho đồng nhất" | §9.3b +lý do QLY-08: ghi tombstone cho `xong` sẽ **chặn vĩnh viễn** đường "Gỡ về chờ nạp" (VPS `imported→pending`) |
| 3a | Đ3 edge | Ghi nhận | Lô rỗng `{uuids: []}` chưa nói hành vi | §9.3b: no-op, trả `{bo:0,tombstone:0}` 200 |
| 3b | Đ3 edge | Ghi nhận | Lô cực lớn không có trần | §9.3b: trần `len(uuids) ≤ 1000`, vượt → 4xx |
| 3c | Đ3 edge | Ghi nhận | `keo_ve_bo_qua` không bao giờ dọn → phình theo thời gian | §9.3b: ghi nhận giới hạn (uuid index + nhỏ → chấp nhận; để ngỏ job dọn theo tuổi, không làm ở #51) |
| 4 | Đ4 bảo mật | Ghi nhận | `uuids` từ payload đi vào SQL — nhắc tham số hóa | §9.3b: 1 dòng "mọi query bỏ-qua phải placeholder `?`, không ghép chuỗi uuid" |

> Đ5 (hiệu năng) và Đ6 (sơ đồ): không có phát hiện cần sửa TDD. Hiệu năng chạy SQLite cục bộ, lọc theo index — ổn. Sơ đồ vòng đời nháp §9.3a đã cập nhật nhánh bỏ-qua ở v6.0, không cần vẽ thêm.

## Cố tình bỏ qua

(Không có — 0 phát hiện mức Chặn; mọi Nên-sửa/Ghi-nhận đều đã sửa.)

## Hoãn lại

| # | Phát hiện | Chờ gì |
|---|---|---|
| — | Nút "Khôi phục dòng đã bỏ qua" | ❓ user chưa chốt; mặc định KHÔNG làm. Tombstone khôi phục được ở mức dữ liệu nếu sau này cần. Nếu user muốn → đưa vào phạm vi TRƯỚC `/kehoach` |

## Kết luận

**TDD #51 (NAP-01) đã đủ để bắt đầu code.** 0 phát hiện Chặn chưa đóng. 3 Nên-sửa + 4 Ghi-nhận đều đã ghi vào TDD v6.1.

**Lưu ý phạm vi code:** phát hiện #1 (gỡ `DELETE`, gộp về `POST /bo-qua`) làm đổi phạm vi — thêm việc "chuyển UI từ `DELETE /keo-ve/:uuid` sang `POST /bo-qua`" + gỡ endpoint `DELETE` ở `routers/nap.py`. Phải phản ánh vào `/kehoach` khi bổ sung task #51.
