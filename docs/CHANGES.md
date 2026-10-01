# Sổ thay đổi

> File do `/capnhat` ghi. Các lệnh khác đọc file này để biết tính năng nào đã bỏ / quyết định nào đã đổi.

| # | Ngày | Loại | Mã | Thay đổi | PRD | TDD | Màn hình | Code |
|---|---|---|---|---|---|---|---|---|
| 8 | 01/10/2026 | ✏️ Sửa | `HTG-01` | Chốt cách tool xác thực `/local/*` (task 17): option A (tool gọi VPS thay mặt → session cục bộ; collector 403) + A1 miễn token `/local/config*`+`/local/auth/*`. Còn mở: 1 hay n phiên | — | ✅ | — | ✅ task 17 |
| 7 | 01/10/2026 | ✏️ Sửa | `HTG-01` | TDD §3.2 ghi sót bảng `token_blocklist` (logout thu hồi phiên §5.1) — đồng bộ khi làm task 14 | — | ✅ | — | ✅ task 14 |
| 6 | 01/10/2026 | ✏️ Sửa | `NAP-01`, `QLY-01`, `NAP-06`, NFR⑥ | UX màn nạp: IA 2 chế độ (Nạp/Tra cứu); tên IN HOA khi kéo; check chính tả mức A; nạp lô badge đỏ/xanh; chuẩn cảnh báo inline nổi bật; tìm khóa mọi khóa (kể cả BC1) | ✅ | ✅ | ⬜ NAP-01 (P2) | ✅ C1 · ⬜ NAP-01 (P2) |
| 5 | 01/10/2026 | ✏️ Sửa + ➕ Thêm | `NAP-05`, `QLY-05` | Sau review TDD §10: nới ❌ NAP-05 cho UPDATE 5 cột ảnh (hướng A) + sửa tiêu đề "3 SP"→"1 SP gộp"; thêm story `QLY-05` Nạp/thay ảnh cho HV đã có | ✅ | ✅ | ⬜ QLY-05 | ⬜ |
| 4 | 01/10/2026 | ✏️ Sửa | `NAP-05` | Đổi đường nạp HV: 3 SP rời → **1 SP gộp app cũ** `usp_QuangLA_PM4_ThuNhanHS_ThemMoiCapNhat` (AS-003 phát hiện 3 SP rời lệch app cũ 5 field) | ✅ | ✅ | — | ⬜ làm lại |
| 3 | 01/10/2026 | ✏️ Sửa | `NAP-04`/`NAP-05` | Tên file ảnh: `70004-<timestamp>.jp2` → `<MaDK>.jp2` (khớp TDD §9.2 + verify thật) | ✅ | — | — | — (áp ở NAP-05) |
| 2 | 01/10/2026 | ✏️ Sửa | `NAP-03` | Dropdown Tỉnh (chọn tay) lấy trực tiếp từ `DM_DVHC` thay vì SP `usp_DM_DVHC_SelectAll_Tinh` | ✅ | — | — | ✅ (task 7) |
| 1 | 01/10/2026 | ✏️ Sửa | — | Đổi nơi lưu bảng ánh xạ `DM_DVHC_MAP`: GPLX_CSDT → SQLite cục bộ của tool | — | ✅ | — | ✅ (task 5) |

Chú thích: ✅ Xong · 🟡 Còn dở · ⬜ Chưa làm · — Không liên quan

---

## #8 — Chốt cách tool xác thực `/local/*` (option A + A1) · 01/10/2026

- **Mã:** `HTG-01` (phần ③). Không đổi yêu cầu nghiệp vụ — chỉ ghi lại quyết định kỹ thuật đã triển khai ở task 17.
- **Vì sao:** TDD §4.6 bắt mọi `/local/*` kèm token operator, nhưng chưa nói tool **xác thực token kiểu gì** — JWT do VPS ký + user ở PostgreSQL, tool localhost chỉ nối SQL Server nên không verify JWT đó được. Khoảng trống này lộ ra khi code task 17.
- **Chốt (option A):** backend tool gọi VPS `POST /api/auth/login` **thay mặt** → xác thực tài khoản + vai trò → tự phát **session token cục bộ** (in-memory) cho `/local/*`. Chỉ `operator`/`admin` dùng tool; `collector` → 403. Tool vẫn nạp được khi VPS chập chờn (chỉ cần VPS online lúc đăng nhập).
- **Chốt (A1):** `/local/config*` và `/local/auth/*` **miễn token** — config là bước mồi đặt URL VPS (gác token thì không đăng nhập được: đọc config cần token, mà token cần URL VPS trong config → vòng lặp). Mọi `/local/*` nghiệp vụ khác vẫn buộc session.
- **Đã loại:** (B) chia sẻ `jwt_secret` verify offline — không thu hồi tức thì + bê secret sang máy tool; (C) mỗi request gọi VPS `/api/auth/me` — buộc VPS online suốt.
- **Đã sửa:** TDD §5.5 (mới), §4.2 + §4.6 (thêm endpoint `/local/auth/*` + ghi ngoại lệ A1), TDD-decisions §4a (mới), Changelog TDD v1.9. Code đã có (task 17, commit `1a38af2`): `tool/app/session.py`, `routers/auth.py`, gác ở `main.py`; webapp + webui login.
- **Còn mở (chưa chốt):** tool cho **1 hay nhiều phiên** đăng nhập đồng thời — hiện code cho n phiên. Chưa có yêu cầu nghiệp vụ → để mở, `/capnhat` chốt sau khi cần siết.
- **Không đụng:** PRD (HTG-01 Done khi "tool bắt đăng nhập" đã có, không đổi) · màn hình demo · BUILD-PLAN.

---

## #7 — Bổ sung bảng token_blocklist vào TDD §3.2 · 01/10/2026

- **Mã:** `HTG-01` (phần ② auth). Không đổi yêu cầu nghiệp vụ — chỉ đồng bộ nội bộ TDD.
- **Vì sao:** TDD §5.1 mô tả logout ghi `jti` vào blocklist trong PostgreSQL để thu hồi phiên, nhưng schema §3.2 **ghi sót bảng này**. Phát hiện khi code task 14 (HTG-01②): để làm đúng logout thu hồi phiên phải có bảng.
- **Chốt:** thêm bảng `token_blocklist` (`jti` PK, `exp`, `revoked_at`) + index `idx_blocklist_exp` vào schema §3.2, khớp với `server/db/init.sql` đã tạo ở task 14.
- **Đã sửa:** TDD §3.2 (thêm bảng + index) + Changelog v1.8. Code `server/db/init.sql` + model `TokenBlocklist` + logout blocklist đã có (task 14, commit `b637f0a`).
- **Không đụng:** PRD (hành vi "thu hồi phiên" đã có trong Done HTG-01 + §5.1, không đổi) · màn hình · BUILD-PLAN.

---

## #6 — UX màn nạp: IA 2 chế độ + hiển thị/cảnh báo khi kéo VPS · 01/10/2026

- **Mã:** `NAP-01`, `QLY-01`, `NAP-06` (hạ ⏳), NFR ⑥. Phần lớn là UI/UX cho luồng kéo-nạp (Phase 2) + chuẩn cảnh báo áp ngay Phase 1.
- **Vì sao:** chủ dự án yêu cầu màn nạp trực quan: phân biệt rõ HV **kéo-chưa-nạp / đã-nạp / nạp-lỗi / xem-trong-DB**; và tách bạch **"khóa để nạp" (ẩn khóa đã BC1) vs "khóa để tra cứu" (hiện mọi khóa, kể cả BC1)** — hai luật BC1 ngược nhau, nhồi chung một dropdown thì không tìm được khóa đã BC1 để xem HV.
- **Chốt (hỏi từng câu, user duyệt A/A/A):**
  - **IA 2 chế độ** `Nạp hồ sơ` / `Tra cứu DB` trên màn `/tool/nap`. Chế độ Nạp: dropdown khóa **chỉ chưa BC1** (NAP-02). Chế độ Tra cứu: tìm khóa theo **tên/mã, mọi khóa kể cả 🔒 BC1** (chỉ xem).
  - **Hàng chờ nạp lô** gộp 1 danh sách, lọc **"Cần xử lý" (⚪ chờ + 🔴 lỗi, lỗi lên đầu) / "Đã nạp" (🟢)**. "Đã nạp" là xác nhận tạm trong phiên; chỗ ở thật của HV là chế độ Tra cứu DB.
  - **Tên IN HOA** khi kéo về hiển thị; **check chính tả mức A** (thiếu dấu / số-ký tự lạ / khoảng trắng thừa — không từ điển tên).
  - **Nạp lô:** dòng lỗi **đỏ + lý do**, dòng xong **xanh**; lô vẫn chạy hết.
  - **Chuẩn UX cảnh báo (NFR ⑥):** inline, **nổi bật (banner nền/viền/icon)**, **nêu rõ nguyên nhân**; màu + icon + chữ (phủ mù màu). Áp cả cảnh báo trùng CCCD hiện có.
- **Đã sửa:** PRD `NAP-01` (Done + Edge), `QLY-01` (chế độ Tra cứu), `NAP-06` (hạ ⏳ — còn banner nổi bật), ⑥ NFR, Changelog v2.3 · TDD §11.1 + §10.4 + Changelog v1.7 · `SCREENS.md` (3 quyết định UX + màn #13 ⬜).
- **Đã làm phiên này:** C1 banner nổi bật trong `NapHoSo.tsx` (cảnh báo trùng CCCD) → NAP-06 ✅ lại (verify Playwright 375/1440).
- **Còn nợ:** IA 2 chế độ + nạp lô badge + IN HOA + check chính tả = **NAP-01 Phase 2** (chưa dựng); cập nhật task 20 + 22 qua `/kehoach` bổ sung; dựng màn #13 qua `/prototype-next`.

---

## #5 — Nới ❌ NAP-05 cho UPDATE cột ảnh + thêm QLY-05 Nạp/thay ảnh · 01/10/2026

- **Mã:** `NAP-05` (sửa), `QLY-05` (thêm mới — nhóm QLY, vì `QLY-04` đã dùng cho "Kết xuất Excel" NICE).
- **Vì sao:** Review TDD §10 (đọc thân SP + verify DB thật) xác định **SP gộp `usp_QuangLA_PM4_ThuNhanHS_ThemMoiCapNhat` KHÔNG ghi ảnh** — không có cột `DuongDanAnh`/`ChatLuongAnh`, set `TT_XuLy='01'`. Nhưng 55/55 HV thật khóa B-K149 có `TT_XuLy='03'` + đường dẫn ảnh đầy đủ → ghi ảnh là bước RIÊNG sau SP. Chốt **hướng A: UPDATE thẳng 5 cột ảnh** `NguoiLX_HoSo` (`DuongDanAnh`, `ChatLuongAnh`, `TT_XuLy`, `NgayThuNhanAnh`, `NguoiThuNhanAnh`) — việc này nghịch dòng ❌ cũ "chỉ qua SP" nên phải nới ràng buộc. Tiện thể sửa tiêu đề NAP-05 còn ghi "3 SP" (đã đổi từ CHANGES #4).
- **QLY-05:** cùng cơ chế ghi ảnh hướng A, áp cho HV **đã có trong DB** — bổ sung ảnh cho HV chưa ảnh (`TT_XuLy='01'`) hoặc thay ảnh mới cho HV đã có (`'03'`, ghi đè). Có bộ lọc tình trạng ảnh trên màn tra cứu + nút "Nạp/thay ảnh" trong drawer. **Làm SAU NAP-05** (dùng lại logic ghi ảnh NAP-04/NAP-05).
- **Đã sửa:** PRD NAP-05 (tiêu đề + dòng ❌ + Changelog v2.2) · PRD thêm story `QLY-05` · TDD §11.5 + Changelog v1.6 · `ui-demo/SCREENS.md` (màn #12 ⬜) · biên bản `docs/tdd-review-01-10-2026.md`.
- **Còn nợ:** `QLY-05` dựng màn (`/prototype-next`) + code (sau NAP-05) + task trong BUILD-PLAN (`/kehoach` bổ sung). Code NAP-05 áp hướng A khi làm lại.

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
- **Số story trong PRD:** 16 (15 MUST/SHOULD + QLY-05; chưa tính NICE `QLY-04`, `THU-03`)
- **Mã story hiện có:** `HTG-01`, `HTG-02`, `HTG-03`, `THU-01`, `THU-02`, `NAP-01`…`NAP-06`, `KHO-01`, `QLY-01`, `QLY-02`, `QLY-03`, `QLY-05` (NICE: `QLY-04`, `THU-03`)
- **Mã đã nghỉ hưu:** (chưa có)
