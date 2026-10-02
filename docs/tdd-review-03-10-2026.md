# Biên bản review TDD — PMCSĐTLX

- **File review:** docs/TDD.md (phạm vi phần #24: §4.3, §4.4, §7.1, §9.1, §11.7)
- **Ngày:** 03/10/2026
- **Số phát hiện:** 6 (Chặn: 2 · Nên sửa: 2 · Ghi nhận: 2) — tất cả đã xử, không có phát hiện bị bỏ qua.

## Đã sửa

| # | Điểm | Mức | Phát hiện | Đã sửa thế nào |
|---|---|---|---|---|
| 1 | 2 | Chặn | §11.7 "đồng bộ xóa khi kéo" suy "đã xóa" từ việc uuid vắng mặt trong `GET /api/nap/keo` — nhưng `keo` còn lọc `locked_by IS NULL` + `limit` → dòng còn `pending` nhưng bị khóa/rớt limit cũng vắng mặt → **xóa nhầm** hồ sơ chưa xóa | §11.7 chốt dùng `GET /api/nap/da-xoa?since=<mốc>` (danh sách uuid chuyển `deleted` từ mốc), bỏ hẳn cách suy-từ-vắng-mặt |
| 2 | 2 | Chặn | §4.4 thiếu endpoint để lấy danh sách uuid đã xóa | Thêm `GET /api/nap/da-xoa?since=<ts>` (đọc `audit_log`) vào §4.4 |
| 3 | 2 | Nên sửa | §11.7 bước 2 "fallback hỏi VPS theo ma_dk" dựa vào endpoint chưa định nghĩa | Thêm `GET /api/nap/tra-uuid?ma_dk=` vào §4.4; §11.7 bước 2 trỏ tới endpoint này |
| 4 | 3 | Nên sửa | `DELETE` và `tra-ve-cho-nap` nếu đọc-rồi-ghi sẽ hở race với `lock` (pending→importing) đồng thời → lệch VPS↔CSDT | §4.3/§4.4 thêm quy tắc CAS: `UPDATE … WHERE trang_thai='pending'/'imported'`, 0 dòng→409; `tra-ve-cho-nap` idempotent khi retry |
| 5 | 5 | Ghi nhận | `da-xoa?since=` cần mốc thời điểm xóa, §7.1/§4.3 chưa nói lưu đâu | §4.3 ghi rõ dùng `audit_log.created_at` (+`idx_audit_created` sẵn có), không thêm cột `deleted_at` |
| 6 | 6 | Ghi nhận→vẽ | §11.7 mô tả luồng xóa-CSDT-trước-rồi-VPS (2 hệ thống, không hoàn tác) chỉ bằng chữ | Chèn sơ đồ ASCII §11.7: điểm không-hoàn-tác sau bước (3), nhánh retry chỉ-bước-(4), idempotent `tra-ve-cho-nap` |

## Cố tình bỏ qua

Không có. (Không có phát hiện mức Chặn/Nên sửa nào bị bỏ qua.)

## Hoãn lại

| # | Phát hiện | Chờ gì |
|---|---|---|
| 1 (Điểm 1) | PRD `[THU-05]`/`[QLY-08]` gọi trạng thái VPS là `done`, nhưng DB thật (`init.sql:28`) + TDD là `imported` | Chạy `/capnhat` sửa PRD `done`→`imported` (ranh giới: lệnh review TDD không sửa PRD) |
| 2 (Điểm 4) | `DELETE /api/ho-so/:uuid` phải kiểm `created_by` ở **tầng handler**, không chỉ ở guard route (IDOR) — §4.3 đã ghi đúng ý, chỉ nhắc khi code | Khi code THU-05 + vòng `review-baomat` lúc đóng Feature |

## Kết luận

**TDD #24 đã đủ để bắt đầu code.** 0 phát hiện Chặn còn mở (2/2 đã sửa). Còn 2 việc hoãn: sửa nhãn `done` trong PRD bằng `/capnhat`, và kiểm IDOR ở tầng handler lúc code/review bảo mật.
