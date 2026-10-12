# Biên bản review TDD — Thu nhận hồ sơ học viên (phạm vi §11D.10)

- **File review:** `docs/TDD.md` §11D.10 (+ §11D.6, dòng `Phục vụ`)
- **Ngày:** 12/10/2026
- **Người soát:** subagent `general-purpose` (Sonnet) đọc độc lập TDD + PRD + code; user quyết từng điểm
- **Phạm vi:** KQD-08 (nạp giờ/km đường từ PDF DAT) + KQD-02 phần giờ `hh:mm` / nạp sẵn giờ/km đã lưu
- **Số phát hiện:** 7 (Chặn: 0 · Nên sửa: 4 · Ghi nhận: 3) — Điểm 5 hiệu năng và phần lớn Điểm 4 bảo mật không có phát hiện

## Đã sửa

| # | Mức | Phát hiện | Cách xử |
|---|---|---|---|
| F1 | Nên sửa | TDD ghi endpoint "đề xuất" và thiếu field / mã lỗi / 6 giá trị `tinh_trang`; §11D.6 không có `/dat/*` | Sửa TDD theo code (code đúng hơn: đã có test) |
| F3 | Nên sửa | "Chọn tất cả" tick cả dòng chưa chạy DAT + điền `0` → ghi đè giá trị đang có (trái PRD, trái decisions §24) | **Sửa code** `NapDatModal.tsx` + TDD + test Playwright |
| F4 | Ghi nhận | TDD định nghĩa "chưa chạy DAT" hẹp hơn code | Sửa TDD theo code |
| F6 | Nên sửa | Dòng vượt trần tra lý do (50 tên / 500 mã) vẫn bị báo "không tìm thấy" | **Sửa code** (`chua_tra`) + TDD + 3 ca pytest |
| Điểm 6 | — | Thiếu sơ đồ luồng và bảng tình trạng dòng | Chèn ASCII vào đầu §11D.10 |

## Bỏ qua / chấp nhận (đã ghi vào TDD mục "Rủi ro đã biết")

| # | Mức | Phát hiện | Lý do chấp nhận |
|---|---|---|---|
| F5 | Nên sửa | `da_luu` đếm bằng `rowcount == 1` trong khi §11D.7b/§11D.8 tránh `rowcount` | UPDATE trần, dự án dùng tương tự ở `nap.py`/`tn_bc2_nhat_ky.py`; nếu trả -1 chỉ báo nhầm "bỏ qua", ghi lại idempotent |
| F7 | Ghi nhận | Hai phiên nạp cùng khóa: ghi sau thắng, không lưu giá trị cũ | Tool một máy, file cùng nguồn DAT; thêm nhật ký là thêm bảng + màn hình cho rủi ro thấp |
| F8 | Ghi nhận | PDF không giới hạn số trang | Tool localhost, một người dùng, file tự tải từ DAT; xem lại nếu nhận PDF nguồn lạ |

## Chưa kiểm được

- Index `NguoiLX.HoVaTen` / `NgaySinh` (tài liệu DB không ghi index): tệ nhất 50 truy vấn quét ~34.640 hồ sơ, vẫn chấp nhận được.
- Ghi thật vào CDB production: chờ nghiệm thu máy CSĐT (Checkpoint 32).
