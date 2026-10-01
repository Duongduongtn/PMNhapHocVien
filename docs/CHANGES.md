# Sổ thay đổi

> File do `/capnhat` ghi. Các lệnh khác đọc file này để biết tính năng nào đã bỏ / quyết định nào đã đổi.

| # | Ngày | Loại | Mã | Thay đổi | PRD | TDD | Màn hình | Code |
|---|---|---|---|---|---|---|---|---|
| 4 | 01/10/2026 | ✏️ Sửa | `NAP-05` | Đổi đường nạp HV: 3 SP rời → **1 SP gộp app cũ** `usp_QuangLA_PM4_ThuNhanHS_ThemMoiCapNhat` (AS-003 phát hiện 3 SP rời lệch app cũ 5 field) | ✅ | ✅ | — | ⬜ làm lại |
| 3 | 01/10/2026 | ✏️ Sửa | `NAP-04`/`NAP-05` | Tên file ảnh: `70004-<timestamp>.jp2` → `<MaDK>.jp2` (khớp TDD §9.2 + verify thật) | ✅ | — | — | — (áp ở NAP-05) |
| 2 | 01/10/2026 | ✏️ Sửa | `NAP-03` | Dropdown Tỉnh (chọn tay) lấy trực tiếp từ `DM_DVHC` thay vì SP `usp_DM_DVHC_SelectAll_Tinh` | ✅ | — | — | ✅ (task 7) |
| 1 | 01/10/2026 | ✏️ Sửa | — | Đổi nơi lưu bảng ánh xạ `DM_DVHC_MAP`: GPLX_CSDT → SQLite cục bộ của tool | — | ✅ | — | ✅ (task 5) |

Chú thích: ✅ Xong · 🟡 Còn dở · ⬜ Chưa làm · — Không liên quan

---

## #4 — Đổi đường nạp HV: 3 SP rời → 1 SP gộp app cũ · 01/10/2026

- **Mã:** `NAP-05` (và nền cho `NAP-01`, `QLY-01/02/03` dùng SP tương tự).
- **Vì sao:** Mục tiêu NAP-05 là **bản ghi khớp app cũ 100%**. Khi chạy **AS-003** (nạp thử 1 HV thật vào khóa B-K149), bản ghi tạo bằng 3 SP rời (`usp_NguoiLX_Insert` → `usp_NguoiLX_HoSo_Insert` → `usp_NguoiLXHS_GiayTo_Insert`) **lệch app cũ 5 field**: họ tên không IN HOA · `NoiTT`/`NoiCT` nhét tên xã gây app hiển thị lặp địa chỉ (phải để trống, địa chỉ lấy từ mã DVHC 2 cấp) · `DonViHocLX`='70004' (phải NULL) · `CHON_IN_GPLX`=0 (phải 2 — **3 SP rời không có tham số để set**) · `MaQuocTich`='VN' vỡ `FK_NguoiLX_DM_QuocTich` (đúng là 'VNM'). Gốc rễ: app cũ màn "Thu nhận Hồ sơ cấp mới" nạp qua **1 SP gộp** `usp_QuangLA_PM4_ThuNhanHS_ThemMoiCapNhat` (32 tham số khớp 1:1 form), không phải 3 SP rời.
- **Mới:** nạp qua `usp_QuangLA_PM4_ThuNhanHS_ThemMoiCapNhat` — ghi NguoiLX + NguoiLX_HoSo + giấy tờ + `CHON_IN_GPLX` atomic trong một SP; bỏ compensation bù trừ 3 bước thủ công.
- **Đã sửa:** TDD §10.1 (luồng), §10.1b (sequence), §10.2 (field map khớp app cũ), §10.3 (bỏ compensation, SP atomic), Changelog v1.4 · TDD-decisions §10 (giữ "Đã từng chốt" = 3 SP rời) · PRD `NAP-05` (Steps + Done khi giá trị khớp app cũ; **hạ ⏳ Todo** — code làm lại).
- **Còn nợ:** làm lại code `tool/app/nap.py` + `tool/app/routers/nap.py` + `tool/webui/.../NapHoSo.tsx` (gửi Chi tiết địa chỉ riêng, không nhét tên xã vào NoiTT) + tests. Đọc thân SP để chốt: SP tự sinh `MaDK`/`SoHoSo` hay caller truyền; cách SP ghi `DuongDanAnh`. Phần tái dùng được từ task 9+10 cũ (commit `843819a`): form nhập tay, checklist giấy tờ, route skeleton, `sinh_so_ho_so`/`tach_ho_ten`. BUILD-PLAN task 9+10 cần `/kehoach` bổ sung xác định lại.

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

## #3 — Tên file ảnh .jp2 = MaDK (không phải timestamp rời) · 01/10/2026

- **Mã:** `NAP-04` / `NAP-05`
- **Vì sao:** PRD `NAP-04` Done khi ghi `70004-<yyyyMMddHHmmssfff>.jp2`, nhưng TDD §9.2 + bộ nhớ dự án §6 (verify 39.648 HV thật, khớp 100%) xác định tên file = `<MaDK>.jp2`, với `MaDK` do `usp_NguoiLX_Insert` trả về. Sinh timestamp mới ở bước ghi ảnh sẽ lệch `MaDK` → đường dẫn ảnh sai, app cũ không tìm thấy ảnh.
- **Đã sửa:** PRD `NAP-04` Done khi (dòng ghi file). Áp dụng thực tế khi code NAP-05 (dùng lại `MaDK` từ SP).
- **TDD:** không đổi (§9.2 vốn đã đúng).

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
