# Biên bản review TDD — PMCSĐTLX

- **File review:** docs/TDD.md §11B.7 (phần mở rộng CHANGES #37 — form sửa nhân thân TCB-03)
- **Ngày:** 05/10/2026
- **Đối chiếu:** PRD TCB-03 (đã gắn mã) · CHANGES #37 · code thật (`hoso.py`, `sync_tracuu.py`, `dvhc.py`)
- **Số phát hiện:** 4 (Chặn: 0 · Nên sửa: 3 · Ghi nhận: 1)
- **Kết luận:** TDD §11B.7 đủ để bắt đầu code TCB-03 bản mở rộng. 0 phát hiện Chặn chưa đóng.

## Đã sửa

| # | Điểm | Mức | Phát hiện | Đã sửa thế nào |
|---|---|---|---|---|
| 1 | 1 | Nên sửa | `chi_tiet_sua_dich` (CDB) không trả `NoiTT_MaDVHC`/`NoiTT_MaDVQL`/`NgayCapCMT`/`NoiCapCMT` → form mở rộng không preselect được giá trị đang lưu (bản Nạp đã trả, CDB thiếu) | +bullet TDD: endpoint `chi-tiet-sua` CDB trả thêm 4 mã này để preselect Tỉnh/Xã/ngày cấp/nơi cấp |
| 2 | 2 | Nên sửa | Chưa định nghĩa ngữ nghĩa "bỏ trống" 3 trường mới — model riêng mang body, body rỗng sẽ ghi đè xóa giá trị cũ (mất dữ liệu thầm lặng) | User chốt **trống = giữ cũ**: +luật TDD `dung_tham_so_update_cdb` fallback `cur_row[...]` khi body rỗng; địa chỉ đi theo cặp Tỉnh+Xã; làm rõ tách hàm riêng nhưng tái dùng `_EXEC_UPDATE` |
| 3 | 3 | Nên sửa | Dữ liệu xã trước sáp nhập 2025 không có trong danh mục mới → dropdown không preselect, dễ lưu đè rỗng | +edge TDD: preselect trống là bình thường; luật "giữ cũ" (PH#2) bảo vệ không mất dữ liệu |
| 4 | 3 | Ghi nhận | TDD nói đọc danh mục từ DB đích nhưng chưa flag kiểm CDB có đủ `DM_DVHC` mới + SP xã + `DM_DonViGTVT` | +dòng "còn kiểm khi code": thiếu thì danh mục đích lệch → báo và tắt phần chọn |

## Cố tình bỏ qua

Không có.

## Hoãn lại

Không có.

---

**Thay đổi TDD:** §11B.7 (4 bullet) + Changelog v3.9. Không chạm PRD, không đổi phạm vi story TCB-03, không chạm quyết định §12/§13/§14.
