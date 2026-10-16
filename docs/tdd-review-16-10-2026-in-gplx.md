# Biên bản review TDD — Chọn in GPLX (NAP-05/NAP-01)

- **File review:** docs/TDD.md (phần mới §9.3a, §10, §10.2 của v6.25 / CHANGES #79)
- **Ngày:** 16/10/2026
- **Người soát:** subagent review-tdd (context độc lập)
- **Số phát hiện:** 9 (Chặn: 0 · Nên sửa: 4 · Ghi nhận: 5) — **TDD đủ để code; code task 146 đã khớp.**

## Đã sửa

| # | Điểm | Mức | Phát hiện | Đã sửa thế nào |
|---|---|---|---|---|
| 1 | 1 | Nên sửa | Dòng "Phục vụ" §10 thiếu `NAP-01` | Thêm `NAP-01` (ô ở ngăn Chuẩn bị) |
| 2 | 2 | Nên sửa | "Không tin client" mâu thuẫn với UI luôn gửi giá trị | Viết lại: server chỉ kiểm ∈ {1,2,3} và dùng giá trị client gửi; `None` mới lấy theo hạng |
| 3 | 2 | Ghi nhận | §10.2 `MaLoaiHs` ghi "chứa A" trong khi code `startswith("A")` | Sửa thành "bắt đầu bằng A" |
| 4 | 3 | Nên sửa | Chọn tay rồi đổi khóa khác loại → giá trị cũ còn dính | **User chốt A:** xóa lựa chọn tay khi đổi khóa khác loại; chọn lại mặc định = NULL. Đã code + 2 ca e2e |
| 5 | 3 | Nên sửa | §9.3a mô tả bảng `nhap_chuan_bi` chưa có cột mới | Thêm cột + guard ALTER |

## Cố tình bỏ qua

| # | Phát hiện | Mức | Vì sao chấp nhận |
|---|---|---|---|
| 6 | Nhãn 1/2/3 mới suy từ dữ liệu, chưa đối chiếu ô `cboInGplx` máy cũ | Ghi nhận | Dữ liệu ghi (2 ô tô, 3 mô tô) lấy từ DB thật nên đúng; chỉ nhãn chữ có thể đảo — đối chiếu ở task 148 |
| 8 | `test_nap_live.py:111` assert cứng 2 | Ghi nhận | Đúng với khóa B1 của test live; không đổi TDD |
| 9 | Vòng đời giá trị ô chưa có sơ đồ | Ghi nhận | Mô tả chữ đủ sau khi bổ sung #4 |

## Hoãn lại

| # | Phát hiện | Chờ gì |
|---|---|---|
| 7 | HV mô tô đã nạp mang 2, ~739 HV DB đích đang 0 (25 HV đã vào BC2); Sở có dùng trường không | User quyết có chạy script sửa không, và xác minh bằng mở một `BC2_*.zip` đã gửi — trước khi đóng NAP-05 |
