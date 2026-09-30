# Biên bản review TDD — Thu nhận hồ sơ học viên

- **File review:** `docs/TDD.md` (v1.0 → v1.1)
- **Ngày:** 30/09/2026
- **Người review:** AI (senior developer)
- **Người quyết định:** Chủ dự án
- **Nguồn đối chiếu:** `docs/PRD.md` (v2, đã gắn mã), `docs/TDD-decisions.md`, BR (20), EC (22), `prd-review-30-09-2026.md`
- **Dự án đã có code?** Chưa — soi nội bộ TDD + đối chiếu PRD/BR/EC bằng mã.
- **Số phát hiện:** 18 (Chặn: 1 · Nên sửa: 11 · Ghi nhận: 6) + 3 sơ đồ bổ sung.

## Kết luận

> **TDD này đã đủ để bắt đầu code chưa?** → **Đủ.** Phát hiện Chặn duy nhất (PH-3.1 trùng SoHoSo) đã đóng bằng `sp_getapplock`. Không còn phát hiện Chặn nào treo.

Phủ 11/11 story MUST, không thừa bảng/endpoint, scope + quy mô khớp PRD. Lỗ nặng nhất là đồng thời (SoHoSo không có ràng buộc UNIQUE nên "retry PK" vô hiệu) — đã sửa. Các lỗ còn lại là bảo mật (IDOR/upload/JWT), tách họ tên, và bền vững compensation — đều đã vá.

## Đã sửa

| # | Điểm | Mức | Phát hiện | Đã sửa thế nào |
|---|---|---|---|---|
| PH-3.1 | 3 | **Chặn** | "retry nếu trùng PK" không chạy vì SoHoSo không phải PK → 2 máy nạp cùng khóa trùng SoHoSo | §10.1: bọc {MAX+1 → HoSo_Insert} trong `sp_getapplock(MaKhoaHoc)` |
| PH-1.1 | 1 | Nên sửa | HTG-01 thiếu màn Cấu hình + Kiểm tra kết nối | §4.6 thêm `/local/config` + `/local/config/test`; §5.0 mô tả màn Cấu hình |
| PH-1.2 | 1 | Nên sửa | §5 thiếu tag `Phục vụ: HTG-01` | Thêm `> Phục vụ: HTG-01` |
| PH-2.1 | 2 | Nên sửa | Trạng thái `duplicate` không rõ ai set | Bỏ `duplicate` khỏi enum §3.2; trùng CCCD giữ `pending` + cảnh báo |
| PH-2.2 | 2 | Nên sửa | §10.3 mâu thuẫn "sinh trong transaction" vs "không transaction" | Viết lại §10.1/§10.3 với applock |
| PH-2.3 | 2 | Nên sửa | §8.1 thiếu tiền tố Quận/Huyện/Thị xã → miss map cấp huyện | Bổ sung danh sách tiền tố |
| PH-3.2 | 3 | Nên sửa | Compensation không bền, tool chết giữa khe → NguoiLX mồ côi | §10.3 ghi `madk_dang_nap` vào staging, dọn ở retry |
| PH-3.3 | 3 | Nên sửa | EC-030 thiếu validate độ dài tên + tách họ/đệm/tên | §6.2 validate độ dài; §10.2 quy tắc tách tên |
| PH-4.1 | 4 | Nên sửa | IDOR dựa vào UUID khó đoán | §5.3 kiểm sở hữu `created_by` |
| PH-4.2 | 4 | Nên sửa | Upload ảnh thô không validate (bomb/đầy đĩa) | §7.4 giới hạn size + magic-byte + MAX_IMAGE_PIXELS |
| PH-4.3 | 4 | Nên sửa | JWT không kiểm is_active/vai trò → khóa tài khoản không hiệu lực ngay | §5.1 đọc từ DB mỗi request + blocklist logout |
| PH-5.1 | 5 | Nên sửa | rembg cold-start vượt <5s | §9.2 warm-up model lúc khởi động |
| PH-5.2 | 5 | Ghi nhận | Kéo/lọc chưa phân trang | §4.4/§4.5 thêm `limit` |
| PH-5.3 | 5 | Ghi nhận | Thiếu index `created_by` | §3.2 thêm `idx_hstt_creator` |
| PH-2.4 | 2 | Ghi nhận | timeout "vd 15'" + "480×640 nếu nét hơn" chưa chốt | §7.2 chốt 15' (env); §9.2 mặc định 353×471 |
| PH-3.4 | 3 | Ghi nhận | Vài ca chưa restate | §10.4 dropdown rỗng, cảnh báo tuổi, offline staging, token hết hạn |
| PH-4.4 | 4 | Ghi nhận | key dùng chung / /local trống / SQL động | §12 ghi chú parameterized SQL, buộc token /local, key riêng mỗi máy |
| PH-1.3 | 1 | Ghi nhận | HTG-03 chỉ có endpoint, không tag | §4.5 thêm `Phục vụ: HTG-03` |
| SĐ-1/2/3 | 6 | — | Thiếu sequence, ma trận quyền, state machine rõ | §10.1b sequence; §5.3 ma trận; §7.1 state machine mới |

## Cố tình bỏ qua

Không có — mọi phát hiện đều đã sửa.

## Hoãn lại (không đổi TDD, chuyển việc khác)

| # | Phát hiện | Chờ gì |
|---|---|---|
| PH-1.4 | PRD ⑦/NAP-05/EC-061 dùng chữ "transaction/rollback" nhưng thiết kế là compensation | Cập nhật câu chữ PRD qua `/capnhat` (đã ghi chú ở §16 TDD; không đổi hành vi) |

## Việc còn treo trước khi code (từ bàn giao, không thuộc review này)

- AS-001: test chuỗi QR trên thẻ CCCD thật.
- AS-003: nạp thử 1 HV thật → mở app cũ đối chiếu (đặc biệt xác minh applock + tách tên + đường dẫn ảnh = MaDK).
- 4 ô `[CHƯA CHỐT]` trong PRD ⑨ (budget/timeline/team/số HV) — chốt trước `/kehoach`.
