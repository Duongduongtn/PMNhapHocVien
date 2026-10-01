# Sổ thay đổi

> File do `/capnhat` ghi. Các lệnh khác đọc file này để biết tính năng nào đã bỏ / quyết định nào đã đổi.

| # | Ngày | Loại | Mã | Thay đổi | PRD | TDD | Màn hình | Code |
|---|---|---|---|---|---|---|---|---|
| 2 | 01/10/2026 | ✏️ Sửa | `NAP-03` | Dropdown Tỉnh (chọn tay) lấy trực tiếp từ `DM_DVHC` thay vì SP `usp_DM_DVHC_SelectAll_Tinh` | ✅ | — | — | ✅ (task 7) |
| 1 | 01/10/2026 | ✏️ Sửa | — | Đổi nơi lưu bảng ánh xạ `DM_DVHC_MAP`: GPLX_CSDT → SQLite cục bộ của tool | — | ✅ | — | ✅ (task 5) |

Chú thích: ✅ Xong · 🟡 Còn dở · ⬜ Chưa làm · — Không liên quan

---

## #1 — Đổi nơi lưu bảng ánh xạ DM_DVHC_MAP · 01/10/2026

- **Loại:** đổi quyết định kỹ thuật đã chốt (TDD-decisions §5). Không phải story — là task nền (BUILD-PLAN task 5) + phục vụ `NAP-03`.
- **Vì sao:** tool desktop `.exe` phải **mang đi cài máy/cơ sở khác, không phụ thuộc máy hiện tại**, và **không được ghi/sửa gì vào DB production** (`GPLX_CSDT` chỉ được ĐỌC). Để bảng trong production nghĩa là mỗi máy mới phải tạo + nạp bảng vào production của máy đó (cần quyền tạo bảng) — ngược cả hai yêu cầu.
- **Cũ (tới 30/09/2026):** `DM_DVHC_MAP` là bảng phụ MỚI trong `GPLX_CSDT`, lý do "cập nhật danh mục một chỗ dùng chung".
- **Mới:** bảng tra cứu nằm ở **SQLite cục bộ của tool** (`staging.sqlite`). Tool đóng gói sẵn dataset `vietnamadminunits` (CSV tĩnh); lần chạy đầu / thao tác "Đồng bộ danh mục" → đọc `DM_DVHC (TrangThai=1)` của máy đích (chỉ đọc) + dataset → tự dựng bảng, nối theo TÊN nên luôn ra đúng mã của máy đích. Production không bao giờ bị ghi.
- **Đã sửa:** TDD §3.3 (SQLite thay SQL Server), §8.2 (cơ chế tự dựng), sơ đồ §2.1 (gỡ `DM_DVHC_MAP` khỏi hộp SQL Server), bảng thành phần §2.2, cây thư mục §2.4, Changelog v1.3 · TDD-decisions §5 (giữ "Đã từng chốt"). PRD `NAP-03` **không đổi** (hành vi với user y nguyên; nơi lưu là chuyện kỹ thuật).
- **Còn dấu vết (cần dọn):**
  - Bảng `dbo.DM_DVHC_MAP` **đã được tạo + nạp 10.602 dòng vào production** `DESKTOP-UBV2GQI` ở phiên trước (task 5 cũ, commit `74d211b`/`41ccb1c`) → **phải DROP** để trả máy về nguyên trạng.
  - Code `tool/db/01_create_dm_dvhc_map.sql` + `02_seed_dm_dvhc_map.sql` (nhắm SQL Server) → thay bằng builder nạp **SQLite**. `seed_dvhc_map.py` tái dùng phần đối soát theo tên, đổi đích ghi.
- **Còn nợ:** rework code task 5 (builder SQLite) + bước "Đồng bộ danh mục" trong tool. BUILD-PLAN task 5 cần cập nhật mô tả qua `/kehoach` bổ sung.

---

## #2 — Dropdown Tỉnh (NAP-03 chọn tay) lấy trực tiếp từ DM_DVHC · 01/10/2026

- **Mã:** `NAP-03`
- **Vì sao:** SP `usp_DM_DVHC_SelectAll_Tinh` chỉ trả đơn vị `LoaiDvhc` TW/TI, toàn `TrangThai=0` (tỉnh cũ) — DB xác nhận `TrangThai=1` chỉ có PH/XA, không có bản ghi cấp tỉnh mới. Dùng SP này thì dropdown Tỉnh hiện tỉnh cũ → nhân viên chọn ra mã sai.
- **Mới:** dropdown Tỉnh lấy 34 tỉnh mới từ `DM_DVHC` (DISTINCT `MaDVQL`, tên tách từ `TenDayDu`, `TrangThai=1`). Xã vẫn qua `usp_DM_DVHC_SelectDanhSachXaPhuongTheoTinh` + lọc `TrangThai=1` ở app (SP không lọc `TrangThai`).
- **Đã sửa:** PRD `NAP-03` (dòng Done khi dropdown chọn tay). TDD §API giữ nguyên (mô tả endpoint không đổi).

---

## Mốc đối chiếu

> `/capnhat` đọc mục này ở Bước 0b để biết có thay đổi nào chưa ghi sổ không.
> So bằng **danh sách mã**, không so bằng thời gian sửa file.

- **Cập nhật:** 01/10/2026
- **Số story trong PRD:** 15
- **Mã story hiện có:** `HTG-01`, `HTG-02`, `HTG-03`, `THU-01`, `THU-02`, `NAP-01`…`NAP-06`, `KHO-01`, `QLY-01`, `QLY-02`, `QLY-03`
- **Mã đã nghỉ hưu:** (chưa có)
