# Biên bản review TDD — PMCSĐTLX

- **File review:** docs/TDD.md §11C (+ docs/TDD-decisions.md §16)
- **Phạm vi:** Feature DGT (#38) — đóng gói tool độc lập + khởi chạy + wizard lần đầu + phiên vĩnh viễn (DGT-01..04)
- **Ngày:** 05/10/2026
- **Số phát hiện:** 11 (Chặn: 1 · Nên sửa: 5 · Ghi nhận: 5) — tất cả đã xử lý

## Đã sửa

| # | Điểm | Mức | Phát hiện | Đã sửa thế nào |
|---|---|---|---|---|
| 2.1 | 2 Logic | 🔴 Chặn | Phiên local vĩnh viễn nhưng `vps_token` (JWT VPS) hết 8h → sau 8h mọi call VPS (kéo/lock/đã-nạp/đối soát) 401, tool câm lặng hỏng việc nạp | §11C.4 +mục ⚠️: fix **cách A** — heartbeat kiêm refresh-token; ghi rõ **cần `/capnhat`** (đụng VPS `/api/auth`) trước khi code DGT-04. +1 dòng Risks §16 |
| 2.2 | 2 Logic | 🟡 Nên sửa | "Đưa tab cũ lên trước" không làm chính xác bằng `webbrowser.open` | §11C.2 sửa câu: "mở lại trình duyệt tới đúng URL bản đang chạy; không bật tiến trình thứ hai" |
| 2.3 | 2 Logic | 🟡 Nên sửa | Trộn "chống 2 bản" (bind cổng cố định) với "dò cổng trống" → app khác chiếm cổng thì single-instance mất tác dụng | §11C.2 tách: single-instance = **named mutex/lock-file**; chọn cổng phục vụ độc lập |
| 3.1 | 3 Edge | 🟡 Nên sửa | File phiên đĩa ghi-dở/giải-mã-lỗi khi khởi động → exe màn trắng (console ẩn) | §11C.4: đọc phiên đĩa **bọc try/except** → hỏng thì về màn đăng nhập |
| 3.2 | 3 Edge | 🟡 Nên sửa | `key.bin` CÓ nhưng hỏng ≠ "chưa có key.bin" → kẹt (không wizard, không đọc được config) | §11C.3: phân biệt **3 trạng thái khởi động** (a/b/c), ca (c) key.bin hỏng → wizard + cảnh báo |
| 4.1 | 4 Bảo mật | 🟡 Nên sửa | Phiên đĩa + `key.bin` cùng chỗ → copy cả thư mục là chiếm phiên ở máy khác, không cần mật khẩu | §11C.4: mã hóa phiên bằng **DPAPI (CurrentUser)** thay `key.bin` |
| 2.4 | 2 Logic | 🟢 Ghi nhận | "Thu hồi từ xa" chưa nêu endpoint | §11C.4: nêu `GET /api/auth/me` (gộp vào cách A) |
| 3.3 | 3 Edge | 🟢 Ghi nhận | Dev→exe không di cư dữ liệu | §11C.1: +1 câu ghi chú (không phải bug) |
| 4.2 | 4 Bảo mật | 🟢 Ghi nhận | Tự-chạy-khi-bật-máy + phiên vĩnh viễn cộng hưởng rủi ro | §11C.2 + Risks §16: tự-chạy **mặc định TẮT**, dựa khóa màn hình Windows |
| 4.3 | 4 Bảo mật | 🟢 Ghi nhận | FastAPI phải bind 127.0.0.1 (endpoint config/test/login không gác token) | §11C.2: uvicorn **bind `host=127.0.0.1`** |
| 5.1 | 5 Hiệu năng | 🟢 Ghi nhận | `rembg`+`onnxruntime` làm exe to ~150–200MB | §11C.1: cân nhắc không gói rembg nếu máy CSDT không xóa phông |
| 6.1 | 6 Sơ đồ | — | Thiếu sơ đồ vòng đời phiên | +**§11C.5** sơ đồ khởi động & vòng đời phiên (ASCII) |

## Cố tình bỏ qua

| # | Phát hiện | Mức | Vì sao chấp nhận |
|---|---|---|---|
| — | (không có) | — | User nhận xử lý toàn bộ. Riêng 2.1 được **sửa** (hướng A + cờ /capnhat), không bỏ qua. |

## Hoãn lại

| # | Phát hiện | Chờ gì |
|---|---|---|
| 2.1 | Refresh-token VPS cho DGT-04 | **Chạy `/capnhat`** để đưa thay đổi VPS `/api/auth` vào phạm vi, TRƯỚC khi code DGT-04 |

## Kết luận

**TDD §11C đã đủ để bắt đầu code — TRỪ DGT-04.** Số phát hiện Chặn chưa đóng: **0 về mặt thiết kế** (đã ghi hướng fix), nhưng **DGT-04 bị chặn quy trình**: phải `/capnhat` thêm refresh-token VPS trước khi code. DGT-01/02/03 code được ngay.

---

# Bổ sung — /reviewtdd (hẹp) refresh-token §12 · 05/10/2026

- **Phạm vi:** chỉ cơ chế refresh-token VPS vừa thêm ở /capnhat #39 (TDD §12 + §11C.4) — phần server chưa soi ở review #38. Soi Điểm 2/3/4; bỏ 1/5/6 (không đụng PRD mapping/hiệu năng/sơ đồ).
- **Số phát hiện:** 4 (Chặn: 1 · Nên sửa: 3) — đã sửa hết vào §12 (TDD v4.3).

## Đã sửa

| # | Điểm | Mức | Phát hiện | Đã sửa thế nào |
|---|---|---|---|---|
| 4.1 | 4 Bảo mật | 🔴 Chặn | Refresh token (bí mật vĩnh viễn) chưa nói lưu thế nào → nguy cơ lưu plaintext, lộ DB = chiếm phiên mọi tài khoản | §12: lưu **HASH** ở DB, bảng `refresh_token(user_id, token_hash, created_at, last_used_at, revoked)` |
| 2.1 | 2 Logic | 🟡 Nên sửa | Chưa rõ refresh có xoay mỗi lần dùng; logout có xóa refresh token không | §12: **xoay một-lần-dùng** (trả access+refresh mới, vô hiệu cũ), không TTL lịch nhưng revoke được; logout xóa refresh token |
| 3.1 | 3 Edge | 🟡 Nên sửa | Rotation một-lần-dùng + mạng chập chờn (máy CSDT) → đá nhầm phiên hợp lệ khi retry refresh cũ | §12: **cửa sổ ân hạn** / chỉ replay khi refresh cũ dùng lại sau khi token mới đã dùng |
| 4.2 | 4 Bảo mật | 🟡 Nên sửa | `doi-mat-khau` không thu hồi phiên → đổi mật khẩu không đá được kẻ đã chiếm phiên vĩnh viễn | §12: đổi mật khẩu **thu hồi toàn bộ** refresh token của user |

## Cố tình bỏ qua / Hoãn lại

(không có — đã nhận sửa hết)

## Kết luận bổ sung

Thiết kế refresh-token §12 đã đủ để code DGT-04 (phần server). **0 Chặn chưa đóng.** DGT-04 hết chặn quy trình; bước tiếp: `/kehoach` bổ sung rồi `/tieptheo`.
