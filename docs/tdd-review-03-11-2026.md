# Biên bản review TDD — PMCSĐTLX

- **File review:** docs/TDD.md, phạm vi §10.7 (CHANGES #89, v6.32) + dòng mới §4.3, §4.4, §7.5
- **Ngày:** 03/11/2026
- **Người soát:** subagent review-tdd (context độc lập)
- **Số phát hiện:** 13 (Chặn: 1 · Nên sửa: 8 · Ghi nhận: 4)

## Đã sửa

| # | Điểm | Mức | Phát hiện | Đã sửa thế nào |
|---|---|---|---|---|
| F1 | 2 | Chặn | Báo nhầm hồ sơ không được bổ sung | User chốt: nhận diện bằng `audit_log` `bo_sung_gplx`, không dùng mốc thời gian lúc cài như agent đề xuất |
| F2 | 2 | Nên sửa | Phân trang chưa rõ, có thể sót | Sắp `(updated_at, uuid)`, cursor cặp, `limit` 1..500, `co_tiep` |
| F3 | 2 | Nên sửa | Danh sách rỗng biến mất khỏi cảnh báo | Rỗng → 422; thêm câu vào `THU-07` |
| F4 | 3 | Nên sửa | Ghi đua với gỡ về chờ nạp, xóa | Một `UPDATE` có điều kiện, kiểm `rowcount` |
| F5 | 3 | Nên sửa | `ma_dk` không còn hoặc trùng | Hiện "Không tìm thấy", không tính số cảnh báo; trùng lấy bản mới nhất |
| F6 | 3 | Nên sửa | Dữ liệu cũ lệch số phần không lưu được | Trả chuỗi thô về giao diện, gửi lại làm điều kiện; không giữ phiên ở server như agent đề xuất |
| F7 | 3 | Ghi nhận | Lỗi giữa lưu DB và ghi dấu vân | Ghi DB trước, dấu vân lỗi chỉ log |
| F8 | 4 | Nên sửa | Khẳng định hash che được số | Thêm `uuid` vào hash, ghi rõ không che giấu, dọn 30 ngày |
| F9 | 4 | Nên sửa | Quyền endpoint danh sách chưa ghi | Tool key + operator, `limit` tối đa 500, không log |
| F10 | 4 | Ghi nhận | Quá 30 ngày mất dữ liệu không báo | Ghi rõ hệ quả; không thêm hạn còn lại trên app web vì ngoài PRD |
| F11 | 5 | Nên sửa | Cỡ lô chưa rõ | Lô 500 `MaDK`; không thêm bộ nhớ đệm như agent đề xuất |
| F12 | 6 | Ghi nhận | Thiếu sơ đồ vòng đời cảnh báo | Đã thêm vào §10.7 |
| F13 | 2 | Ghi nhận | Phần đóng băng chưa rõ | Ghi chỉ đổi `gplx_da_co`, `updated_at` |

## Cố tình bỏ qua

Không có.

## Hoãn lại

| # | Phát hiện | Chờ gì |
|---|---|---|
| F5 | `QLY-02` có đổi `MaDK` không | Đọc lại code lúc làm |
| F11 | `MaDK` có là khóa của `NguoiLX_HoSo` không | Kiểm lúc làm |
