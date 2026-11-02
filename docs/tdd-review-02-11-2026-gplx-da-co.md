# Biên bản review TDD — GPLX đã có (NAP-07, THU-07)

- **File review:** docs/TDD.md §10.6 (v6.27), §3, §4
- **Ngày:** 02/11/2026
- **Người soát:** subagent review-tdd (context độc lập)
- **Số phát hiện:** 15 (Chặn: 2 · Nên sửa: 11 · Ghi nhận: 2)

## Đã sửa

| # | Điểm | Mức | Phát hiện | Đã sửa thế nào |
|---|---|---|---|---|
| 1 | 2 | Chặn | `/cua-toi` không trả GPLX, mở lại lưu là mất bằng | Trả kèm; app web chỉ gửi trường khi có sửa |
| 2 | 2 | Chặn | Câu mô tả nháp tự mâu thuẫn, có nguy cơ mất bản sửa | NULL / `[]` / JSON rõ nghĩa; `goiNhap` gửi đủ trường |
| 3, 4 | 2 | Nên sửa | `hang` mơ hồ nhãn hay mã; mã trùng giữa hai nhóm | Lưu mã; `ComboLoc` dùng khóa `moi:B1` |
| 5 | 2 | Nên sửa | Chip, lọc chưa có nguồn dữ liệu | `nhap_co` + `_KEO_COLS`; UI ghép một chỗ |
| 6 | 2 | Nên sửa | Chưa rõ lúc ghi danh sách cuối | `keo_ve_cap_nhat` trước `nhap_xoa` |
| 7 | 3 | Nên sửa | Hai bên cùng sửa, bản app web bị bỏ qua âm thầm | **User chốt A:** cờ "App web có bản mới" + nút dùng bản đó |
| 8 | 3 | Nên sửa | Không có trần số bằng, VPS không kiểm | Tối đa 8 bằng, VPS kiểm ngay lúc gửi |
| 9 | 3 | Nên sửa | Một dòng sai làm hỏng cả lô | `NapIn` chỉ kiểm hình dạng, lỗi thành dòng `loi` |
| 10 | 3 | Ghi nhận | Gỡ về chờ nạp rồi kéo lại mất bản sửa | Ghi nhận, chấp nhận |
| 11 | 4 | Nên sửa | Xóa mềm vẫn giữ GPLX | Xóa mềm đặt NULL (phần job xem Hoãn lại) |
| 12 | 4 | Nên sửa | Bản ở tool và nội dung lỗi 422 | Ghi nhận nhóm PII staging; không log giá trị |
| 13 | 5 | Nên sửa | Deploy thiếu cột làm app web lỗi | API tự ALTER lúc khởi động + checklist |
| 14 | 5 | Nên sửa | Nguồn danh sách Nơi cấp không rõ | `ds_noi_cap_gplx` + endpoint riêng |
| 15 | 6 | Ghi nhận | Thiếu sơ đồ ưu tiên | Đã thêm vào §10.6 |

## Cố tình bỏ qua

Không có.

## Hoãn lại

| # | Phát hiện | Chờ gì |
|---|---|---|
| 11b | Hồ sơ xóa mềm (`deleted`) còn giữ `so_cccd` mãi vì job dọn 30 ngày bỏ qua trạng thái này; có từ trước | User quyết có mở rộng job không |

**Kết luận:** TDD đủ để code; 0 phát hiện Chặn còn mở.
