# Sổ thay đổi

> File do `/capnhat` ghi. Các lệnh khác đọc file này để biết tính năng nào đã bỏ / quyết định nào đã đổi.

| # | Ngày | Loại | Mã | Thay đổi | PRD | TDD | Màn hình | Code |
|---|---|---|---|---|---|---|---|---|
| 37 | 05/10/2026 | ✏️ Sửa | `TCB-03` | **Mở rộng trường sửa nhân thân ở Tra cứu CDB** (phát hiện khi nghiệm thu Checkpoint 14 tại máy CSDT — form 5 trường quá tối thiểu). Thêm **địa chỉ thường trú 2 cấp** (chọn Tỉnh+Xã chuẩn → `NoiTT_MaDVHC`/`MaDVQL`, không chỉ dòng chữ) + **ngày cấp CCCD** (`NgayCapCMT`) + **nơi cấp CCCD** (`NoiCapCMT`, Sở GTVT). `usp_NguoiLX_Update` đã nhận sẵn các tham số. **Chỉ TCB-03** (user chốt 05/10) — tách model riêng cho CDB, **Nạp QLY-01 giữ nguyên 5 trường**. Danh mục Tỉnh/Xã + Sở phải đọc từ **DB đích** (`target_key`). TCB-03 hạ ✅→⏳ (bản 5 trường đã nghiệm thu ghi-thật PASS tại máy CSDT 05/10). Nơi cư trú 2 cấp để sau; KHÔNG làm số CMND cũ (SP update không nhận). | ✅ v3.2 | ✅ §11B.7 (v3.8) | 🟡 ghi màn #19 (code thẳng tool/webui) | ⬜ |
| 36 | 05/10/2026 | ✏️ Sửa + ➕ Thêm | `TCB-01`, `TCB-02`, `TCB-03`, `TCB-04`, `SYNC-01`, `HTG-01` | **Sửa định nghĩa "đã kết xuất DKKH"** sang tín hiệu ĐÚNG: khóa có gói `DANG_KY_KHOA_HOC` đã gửi Sở (`TRANS_CLI_HangDoiGui` tên file chứa MaKH) — **KHÔNG** phải `KhoaHoc.SoQD_KhaiGiang` (sai: mọi khóa đều có số QĐ nội bộ → chặn nhầm khóa chưa gửi Sở; verify DB 05/10: 16 khóa đều có SoQD nhưng chỉ 14 đã gửi). Một định nghĩa chung `sync_helpers.dkkh_exists_sql`/`dkkh_exists_cond` (CHARINDEX) dùng cho TCB-01 (chip) + **TCB-03 chặn sửa nhân thân** + **TCB-04 NÂNG ngưỡng chặn: khóa đã DKKH → KHÔNG xóa HV, KHÔNG đổi khóa** (áp cả khóa đi lẫn khóa đến; `khoa-cung-hang` lọc bỏ khóa DKKH; UI vô hiệu nút + ghi lý do) — trước đây DKKH chỉ cảnh báo, chặn cứng ở BC1 (user chốt 05/10: thêm/bớt HV ở khóa đã gửi Sở là lệch danh sách). **+SYNC-01**: (a) filter khóa đích *"Chỉ khóa cùng hạng & chưa kết xuất DKKH"* (checkbox mặc định bật; đích trả thêm cờ `dkkh`) · (b) khóa xếp **mới-nhất-trước** (ORDER BY NgayKG DESC, **MaKH DESC** + hiện ngày KG ở combo nguồn) · (c) **giữ phiên đăng nhập qua F5** (token→localStorage, khôi phục `/local/auth/me`, tự kiểm kết nối đích khi vào màn). Nghiệp vụ sync lõi không đổi → SYNC-01 giữ ✅; TCB giữ ✅ (code đã sửa+verify live 05/10). +docs DB đích §7 (định nghĩa DKKH). | ✅ v3.1 | ✅ §11B.2/§11B.7/§5.5 (v3.6) | ✅ (sửa `BanDongBo.tsx`/`TraCuuCDB.tsx` qua cờ backend) | ✅ 8 file, tsc+34 vitest, verify live+DB. **Chưa commit.** |
| 35 | 04/10/2026 | ➕ Thêm | `TCB-01`, `TCB-02`, `TCB-03`, `TCB-04` | **Feature "Tra cứu CDB đích"** (mở rộng phân hệ Đồng bộ CDB) — màn tra khóa + xem/sửa HV trên **DB ĐÍCH `GPLX_CDB_CSDT`** (song song Tra cứu DB Nạp QLY-01 nhưng trỏ đích). **TCB-01** tra khóa + lưới HV (avatar, tìm) + chi tiết + ảnh lớn + **nút "Xem chi tiết HV" từ Bàn đồng bộ** (mở khóa + tô sáng). **TCB-02** thay ảnh (tái dùng AnhModal + đổi nền, **ghi đè file `.jp2` dùng chung 2 DB** → cả Nạp+đích cùng đổi; cho kể cả DKKH/BC1 + cảnh báo). **TCB-03** sửa nhân thân (`usp_NguoiLX_Update` CDB) → **chặn nếu khóa đích đã kết xuất DKKH** (`SoQD_KhaiGiang`). **TCB-04** xóa HV/đổi khóa → **chặn nếu đã BC1** (FK `BaoCaoI` NO_ACTION); DKKH chưa BC1 → cho+cảnh báo. Luật khóa đọc trạng thái **ở đích** (độc lập DB Nạp); danh mục `DM_TrangThai`. Dựng màn mới `TraCuuCDB.tsx` (tái dùng AnhModal/AnhAvatar, KHÔNG đụng QLY-01). SYNC-01 thêm nút điều hướng (giữ ✅). | ✅ | ✅ §11B.7 (v3.4) | ⬜ màn #19 (dựng thẳng tool/webui) | ⬜ |
| 34 | 04/10/2026 | ➕ Thêm + ✏️ Sửa | `HTG-07`, `HTG-01`, `SYNC-02`, `SYNC-01` | **Cấu hình kết nối DB lên header dùng chung cả tool** + tách rõ DB Nạp vs DB Sync + làm đẹp UI sync. **HTG-07 mới**: bảng cấu hình mở từ **icon ⚙ header** (mọi màn), gộp 2 khối tách bạch — ① kết nối chung + **DB NGUỒN để Nạp** `GPLX_CSDT` (từ HTG-01) · ② **nhiều DB ĐÍCH để Sync** (từ SYNC-02, chọn mặc định/test/tùy chọn). **Bỏ** route `/tool/cau-hinh` + mục "Quản lý CSDL đích" khỏi sidebar. Làm đẹp combobox năm/khóa + chọn DB đích + **danh sách HV để sync** (tên hài hòa, dễ đọc) bằng `impeccable`+`ui-ux-pro-max`. Thuần UI/IA — backend `/local/config*`+`/local/sync/targets`+config-store KHÔNG đổi; không chạm quyết định TDD §12/§13/§14. **(Nhân tiện sửa bug môi trường:** backend nền chạy không `--reload` → kẹt code cũ, combobox năm/khóa trả 404 → restart hết; không phải lỗi code.) | ✅ | ✅ §5.0 + §11B.0 (v3.3) | ✅ task 61-62: `CauHinhDrawer` + ⚙ header + làm đẹp Bàn đồng bộ | 🟡 code+kiểm mức1+2 review xong, **chưa commit** |
| 33 | 04/10/2026 | ➕ Thêm | `SYNC-01`, `SYNC-02`, `SYNC-03` | **Feature mới "Đồng bộ CDB"** (SHOULD) — port nghiệp vụ từ `D:\Du_An\GPLX\sync_tool` **v2.0** vào tool máy CSDT, **tách hoàn toàn** khỏi Nạp. **SYNC-01** Bàn đồng bộ (chọn khóa nguồn `GPLX_CSDT` + đích CDB cùng hạng · ngày nhập HS ≤ NgàyKG · `NguoiTao=admin` giống CDB, **bỏ ô cán bộ** · tải DS đối chiếu đích · skip HV đã có 1người=1HS · MaDK `MaCSDT-yyyyMMdd-nnnnnn` backdate batch · tiến trình **SSE**) · **SYNC-02** Quản lý DB đích (nhiều DB đích dùng chung host/user/pass, chọn mặc định, test, TT_XuLy mặc định 03 + cập nhật TongSoHV) · **SYNC-03** Lịch sử & Hủy sync (log JSON %APPDATA% + rollback dual-mode `NguoiTao='SYNC'`). **Kiến trúc:** tool đổi sang **sidebar trái = danh sách module** (mở rộng N — dự kiến module #3 "Cập nhật kết quả học tập"); backend tách `routers/sync.py`+`sync_service.py`+`sync_helpers.py`+`sync_history.py` không import nạp; **tool CHỈ desktop** (≥1280px, sidebar thu gọn, bảng cuộn ngang) | ✅ | ✅ §11B + §2.4 (v3.2) | ✅ 3 màn dựng thẳng tool/webui (task 56-62) | 🟡 SYNC-01/02 commit `d2b0ba1`/`765d972` (#34); SYNC-03 task 60 chưa commit |
| 32 | 04/10/2026 | ➕ Thêm + ✏️ Sửa | `NAP-01`, `QLY-05` | **Lưu nháp BỀN + 2 chip trạng thái + bổ sung ảnh 2 nguồn** (màn Nạp lô). ① **Lưu nháp bền** (NAP-01): chỉnh sửa chuẩn bị (địa chỉ 2 cấp, chi tiết, nơi cấp, tick giấy tờ, **ảnh đã đổi nền**) lưu xuống `staging.sqlite` bảng `nhap_chuan_bi` thay vì chỉ RAM → F5/đóng-mở tool không mất; **tự xóa** khi nạp xong/bỏ hàng đợi/xóa VPS; reset riêng địa chỉ nháp (backend, trong `keo_ve_upsert`) khi `noi_tt_raw` đổi (BUG-04) · ② **2 chip mỗi dòng** `✓/✗ Địa chỉ 2 cấp` + `✓/✗ Có hình` (mặc định ✗) · ③ **Mở drawer**: cả dòng bấm + nút "Xử lý" to · ④ **Nạp**: chặn thiếu địa chỉ, cảnh báo thiếu ảnh + lối tắt mở Tra cứu DB lọc "chưa ảnh" · ⑤ **Bổ sung ảnh HV thiếu ảnh** (QLY-05): lấy từ **file** (`chonFile`) hoặc **ảnh thô VPS** (`tra_uuid`→`tai_anh`→`napTuUrl`, nếu còn ≤30 ngày), cùng AnhModal + đổi nền | ✅ | ✅ §9.3a/§10.5/§11.5 (v3.2) | 🟡 ghi UX (cập nhật khi code) | ⬜ |
| 31 | 03/10/2026 | ➕ Thêm + 🐛 | `NAP-05`, `QLY-01` | **Nơi cấp căn cước + số hồ sơ + popup chi tiết** (ca Lê Thị Hồng). ① **Nơi cấp** (BUG-10): nạp tự suy **mã Sở GTVT từ số CCCD** (`cccd[2:3]`; nơi cấp = `DM_DonViGTVT` LoaiDV='SO', vd 70=Bình Phước, 75=Đồng Nai) + **combobox** chọn tay (endpoint `/local/dvhc/so-gtvt`) + **vá 6 bản ghi cũ** rỗng · ② **Số hồ sơ** (BUG-09): `MAX+1` → **số nhỏ nhất chưa dùng** (lấp khe do nạp→gỡ→nạp lại) · ③ **Popup "Chi tiết học viên"** (QLY-01): thêm Ngày cấp · Nơi cấp (tên) · Địa chỉ cư trú + địa chỉ đầy đủ (join DM_DVHC); ẩn CMND cũ ở form nạp app web giữ nguyên (đã ẩn), chi tiết vẫn hiện. Thuần tool, KHÔNG đổi SP/schema | 🟡 ghi BUGS #9/#10 | — | ✅ popup + combobox | ✅ tool build+34 vitest; vá DB xong |
| 30 | 03/10/2026 | ✏️ Sửa + ➕ Thêm | `THU-01`, `THU-05` | Redesign giao diện **DESKTOP** app web (nhánh `lg:`, mobile giữ nguyên): **① Quét (THU-01)** — desktop vào thẳng **form nhập tay** (bỏ cổng chọn), nút **Quét QR/Tải ảnh thu nhỏ** ra góc phải tiêu đề, Quét QR mở **popover camera** đè form rồi tự điền; "Lưu & nhập tiếp" → form trống · **② Hồ sơ đã gửi (THU-05)** — desktop **chọn-nhiều-để-xóa**: cột ô tích chỉ ở dòng Chờ nạp + thanh "Đã chọn N · Xóa N" + dialog xác nhận (lặp DELETE client, tái dùng QuanTriHoSo). KHÔNG đổi Data Model/API/endpoint. (Đổi số từ #28→#30 khi gộp 2 phiên song song) | ✅ | ✅ §6.5/§6.6 (v3.0) | ✅ ghi UX (sửa màn có sẵn, không dựng mới) | 🟡 client xong (build+24 test+review-nghiepvu đủ), chưa chụp Playwright/deploy |
| 29 | 03/10/2026 | ✏️ Sửa (UI) | `NAP-01`, `NAP-03` | Tool máy Nạp: **dời 2 nút "Chọn tất cả sẵn sàng" + "Nạp N học viên vào khóa" từ thanh dính đáy LÊN header** (NAP-01, hàng shrink-0 trong `h-[calc]` → list tự co, nút luôn thấy) · **"Chọn tay" địa chỉ: 2 dropdown → ô gõ-để-lọc** `ComboLoc` (gõ không dấu cũng khớp nhờ `boDau`, NAP-03). Thuần client, KHÔNG đổi API/DB | ✅ | — UI-only | ✅ ghi UX+wireframe | ✅ tool build+29 test (chờ chụp) |
| 28 | 03/10/2026 | ➕ Thêm | `QLY-09` | **Đối soát & đồng bộ trạng thái VPS↔CSDT** (sau ca Lê Thị Hồng/BUG-01): panel admin/operator ở tool, đối soát **theo khóa**, phát hiện 3 ca lệch (① VPS imported & CSDT không có MaDK = phantom → Trả về chờ nạp; ② CSDT có HV & VPS chưa imported → Đánh dấu đã nạp; ③ importing treo quá ngưỡng → Mở khóa), sửa 1 chạm **tái dùng** `tra_ve_cho_nap`/`da_nap`/`unlock` — không endpoint/SP nạp mới. +Phòng tuyến 2: `nap_fn` bỏ `da_nap` khi `_nap_mot` trả vé cũ (chặn tái phát phantom). Thuần tool | ✅ | ✅ §11.8 | ⬜ panel tool (dựng khi code) | ⬜ |
| 27 | 03/10/2026 | ✏️ Sửa (chữ) | `THU-05` | Khớp chữ PRD với code task 41 (review-nghiepvu): edge "Chặn 403" → **404** (chống IDOR, không lộ hồ sơ tồn tại — nhất quán `_cua_minh`); copy popup "chưa nạp vào **DB**" → "chưa nạp vào **máy tính**" (tránh lộ từ kỹ thuật cho người thu nhận, luật nội dung). Không đổi code (code đã đúng) | ✅ | — | — | — đã code (task 41) |
| 26 | 03/10/2026 | ✏️ Sửa + ➕ Thêm | `THU-05`, `QLY-08`, `QLY-03`, `NAP-01`, `NAP-04`, `QLY-05` | Chốt nghiệp vụ + UX trước khi code #24: **nguyên tắc bàn giao** (mốc Nạp — trước nạp app web làm chủ, sau nạp tool/CSDT làm chủ, app web đóng băng; QLY-03 "Xóa hẳn" ≠ QLY-08 "Gỡ về chờ nạp") · **popup cảnh báo + hướng dẫn** (copy impeccable) cho xóa app web (THU-05), gỡ về chờ nạp + banner đồng bộ lỗi (QLY-08), xóa hẳn tách bạch (QLY-03) · **"Dùng lại ảnh gốc"** trong trình chỉnh ảnh (NAP-04 ảnh thô VPS / QLY-05 ảnh DB) · **redesign màn Nạp lô** (NAP-01): trạng thái sẵn sàng mỗi dòng, chọn-tất-cả-sẵn-sàng, drawer Chuẩn bị, dialog nạp 3 pha (xác nhận/tiến độ/báo cáo + nạp lại lỗi), nút Xem trong DB | ✅ | ✅ §7.5/§9.1/§10.5 | ✅ ghi UX+wireframe | ⬜ |
| 25 | 03/10/2026 | ✏️ Sửa (nhãn) | `QLY-08`, `THU-05` | Sửa nhãn trạng thái VPS trong PRD: `done` → `imported` (3 chỗ ở THU-05 + QLY-08) cho khớp DB thật (`server/db/init.sql:28` chỉ có `pending/importing/imported/deleted`) + TDD. Phát hiện ở review TDD #24 (Điểm 1, biên bản `tdd-review-03-10-2026.md`). Không đổi yêu cầu, không chạm TDD (đã đúng) | ✅ | — đã đúng | — | — |
| 24 | 02/10/2026 | ➕ Thêm + ✏️ Sửa | `QLY-08`, `THU-05`, `NAP-01` | Đồng bộ gỡ/xóa hồ sơ (verify #22): **QLY-08 mới** — nút "Gỡ về chờ nạp" ở tool (gỡ HV khỏi CSDT + VPS imported→pending + về hàng chờ), tách bạch "Xóa" bỏ hẳn, chỉ khóa chưa BC1, ảnh dùng ảnh thô VPS · **THU-05 mới** — app web collector xóa hồ sơ đã gửi (chỉ pending, soft-delete VPS, của mình/admin) · **NAP-01 mở rộng** — "Kéo về từ VPS" đồng bộ bỏ hồ sơ đã xóa khỏi hàng chờ. Đụng cả tool + **server VPS** (đường mới) + app web | ✅ | ✅ | ✅ ghi UX (không dựng màn) | ⬜ |
| 23 | 02/10/2026 | ✏️ Sửa (UI) | `NAP-04`, `QLY-05`, `QLY-06` | Sửa UX quản lý ảnh + nhãn nút (phát hiện khi verify #22): sau "Dùng ảnh này" **hiện ảnh đã chỉnh** (bản PNG, không chỉ icon check) + **mở lại trình chỉnh nạp sẵn ảnh đã chỉnh** để chỉnh tiếp (NAP-04/QLY-05) · nút áp dụng ảnh **nổi bật + nhãn rõ** (tránh dừng ở "Xử lý ảnh" tưởng đã lưu) · nút **"Mở khóa khác" → "Tạo thêm hồ sơ ở khóa học khác hạng"**, giữ hiển thị cả ở khóa BC1 (QLY-06). Thuần UI, backend `/local/anh/xu-ly` đã trả `preview` sẵn | ✅ | ✅ ghi chú §9.1 | ✅ ghi UX (không dựng màn) | ⬜ |
| 22 | 02/10/2026 | ➕ Thêm + ✏️ Sửa + 🐛 | `QLY-01`, `QLY-03`, `QLY-05`, `QLY-07`, `NAP-01` | Mở rộng quản lý ảnh Tra cứu DB + bảo toàn Báo cáo 1/2: xem ảnh+đường dẫn+avatar+thống kê (QLY-01) · 🐛 giữ `TT_XuLy` khi thay ảnh HV đã Báo cáo (QLY-05, tránh rơi khỏi BC2) + click ảnh từ Tra cứu DB · chặn xóa HV khóa BC1 ở backend (QLY-03) · "Bỏ khỏi hàng đợi"+"Nạp lại nhanh" (NAP-01) · **story mới QLY-07** đổi nền cả khóa | ✅ | ✅ | ⬜ wireframe chốt | ✅ code+push, chờ verify prod |
| 21 | 02/10/2026 | ✏️ Sửa | `NAP-04` | Zoom trình chỉnh ảnh (phản hồi test): cho **thu nhỏ dưới cỡ ban đầu** (trước lấy ảnh gốc làm mốc nhỏ nhất) · thang zoom **mặc định ở GIỮA** (trái thu nhỏ, phải phóng to, mũ 3^t) · **lăn chuột** trên khung để phóng/thu | ✅ | ✅ | — tinh chỉnh AnhModal | ✅ code+build+Playwright, ⚠️ chờ verify |
| 20 | 02/10/2026 | ➕ Thêm + ⚙️ | `NAP-04` | Nâng cấp trình chỉnh ảnh (phản hồi test tool): +xoay ảnh (−90°/+90° + tinh chỉnh độ nghiêng) · +khung chân dung mẫu overlay (ô-van+đường căn, không dính ảnh xuất) · tăng tốc xóa phông = bật warm-up rembg (bỏ `TOOL_SKIP_WARMUP=1` ở `tool-start.bat`), GIỮ model u2net (phương án A). NAP-04 ⚠️→⏳ | ✅ | ✅ | — tinh chỉnh AnhModal có sẵn | ⬜ |
| 19 | 02/10/2026 | ✏️ Sửa | `NAP-03`, `NAP-04` | Tận dụng dữ liệu đã kéo từ VPS ở màn Nạp (kéo-về): NAP-03 tự tách `noi_tt_raw` → điền sẵn ô map (operator chỉ bấm Chuyển đổi; tách không chắc thì gõ tay) · NAP-04 nạp thẳng ảnh thô VPS vào trình chỉnh (không bắt chọn lại file). NAP-03 ✅→⏳, NAP-04 ⚠️→⏳ (yêu cầu đổi, code lại phần này) | ✅ | ✅ | — tinh chỉnh màn tool có sẵn | ⬜ |
| 18 | 02/10/2026 | ➕ Thêm + ✏️ Sửa | `HTG-04`, `HTG-05`, `HTG-06` | Quản lý tài khoản app web: admin xem API key VPS (HTG-04, SHOULD) · admin tạo/khóa tài khoản nhân viên + reset mật khẩu (HTG-05, MUST) · mọi người tự đổi mật khẩu (HTG-06, MUST). + **5 sửa UI (cả 2 app):** header cố định hết giật · khung cao ổn định không co theo nội dung · phân trang list (20/trang) · tool master–detail panel info+ảnh ghim · kính lúp đè chữ hint (fix `@layer components`) | ✅ | ✅ | ⬜ | 🟡 HTG-04/05/06 + UI-1/2/3/4/5 xong (code; server 82 test, build 2 app); chờ deploy VPS + verify |
| 17 | 02/10/2026 | ✏️ Sửa | `QLY-01` | Lát 2 (sửa hồ sơ) — **thu hẹp phạm vi: chỉ sửa NHÂN THÂN** (họ tên, ngày sinh, giới tính, CCCD, địa chỉ TT) qua `usp_NguoiLX_Update`; **bỏ `usp_NguoiLX_HoSo_Update` khỏi QLY-01** (SP ghi đè 65 cột gồm kết quả thi/BC1/BC2 → rủi ro xóa trắng); ảnh→QLY-05, đổi khóa→QLY-02. Ghi an toàn: đọc lại full bản ghi giữ cột không sửa. Chặn khi khóa BC1 (BR-012) | ✅ | ✅ | ⬜ | ✅ code+test, chờ verify prod |
| 16 | 01/10/2026 | ✏️ Sửa | `QLY-06` | Kiểm DB thật (chỉ đọc) chốt thiết kế QLY-06: SP `ThemMoiCapNhat` nạp mới **luôn tạo NguoiLX mới** (không dò người cũ); dữ liệu thật nhiều HV có **2–8 khóa chung SoCMT** → nạp khác khóa = nạp mới bình thường, không cần nối người. Gỡ 📝 Draft → ⏳ Todo | ✅ | — | ⬜ | ⬜ |
| 15 | 01/10/2026 | ✏️ Sửa | `THU-02` | Ảnh app web: tách **2 nút "Chụp ảnh" (camera) / "Chọn từ máy" (file·thư viện)** ở màn chụp + đổi ảnh hồ sơ Chờ nạp (trước ép camera, mobile không chọn được thư viện); bấm ảnh chân dung ở chi tiết → **phóng to popup (lightbox)** | ✅ | — | ⬜ | ✅ deploy |
| 14 | 01/10/2026 | ✏️ Sửa | `THU-01`, `THU-02` | Redesign UX nhập liệu (impeccable): ẩn ô "Số CMND cũ" (vẫn lưu từ QR nếu có) · ô ngày gõ tay dd/mm/yyyy auto-mask "/" + nút lịch (giữ năm-only) · desktop nới khung 2 cột + tách 2 nút tránh bấm nhầm + phím tắt · rà content tránh lộ story/AI slop | ✅ | ✅ | ⬜ | ✅ deploy |
| 13 | 01/10/2026 | ✏️ Sửa + ➕ Thêm | `THU-01`, `THU-02`, `THU-04`, `QLY-06` | App web nhập liên tiếp: nút "Lưu & nhập hồ sơ tiếp" (gửi không ảnh + toast) + badge/lọc "Thiếu ảnh" (THU-01/02 hạ ⏳); +THU-04 cảnh báo trùng CCCD app web (SHOULD, cảnh báo mềm soi hàng đợi); +QLY-06 mở hồ sơ khóa khác cho HV đã có (📝 Draft, còn nợ kiểm DB) | ✅ | ✅ | ⬜ | ✅ THU-01/02/04 deploy + chốt · QLY-06 ⬜ (Draft) |
| 12 | 01/10/2026 | ✏️ Sửa | `THU-01`, `THU-02` | Sửa UX app web sau test điện thoại: màn vào không tự mở camera (chọn Quét/Nhập tay), header logo không phải nút, layout mobile dính đáy, khung bám QR; ảnh thật + xem/sửa/chụp lại hồ sơ chờ nạp (+endpoint tải ảnh của mình) | ✅ | ✅ | 🟡 ghi UX | ⬜ |
| 11 | 01/10/2026 | ✏️ Sửa | `NAP-01` | "Kéo về từ VPS" làm tươi hồ sơ chưa nạp (collector sửa ở app web sau khi tool đã kéo → tool nhận bản mới); kéo không khóa | ✅ | ✅ | — nút có sẵn | ✅ |
| 10 | 01/10/2026 | ✏️ Sửa | `THU-02`, `NAP-01`, `QLY-01` | Thêm ô tìm kiếm (tên khớp cả không dấu / CCCD) ở 3 chỗ: app web Hồ sơ đã gửi · tool list tải về · tool lưới khóa. Màn hẹp thu gọn nút kính lúp | ✅ | ✅ | 🟡 prototype còn | ⬜ |
| 9 | 01/10/2026 | ✏️ Sửa | `THU-02` | Bỏ ô "nhập nơi cư trú khác" ở app thu nhận — chỉ thu nơi thường trú; cư trú để tool mặc định = thường trú (phương án A, không đổi schema) | ✅ | — đã khớp | ✅ demo | ⬜ THU-02 (P2) |
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

## #37 — Mở rộng trường sửa nhân thân ở Tra cứu CDB (TCB-03) · 05/10/2026

- **Mã:** `TCB-03` (mở rộng tiêu chí, không thêm/bớt mã). Hạ **✅→⏳ Todo**.
- **Vì sao:** nghiệm thu Checkpoint 14 tại máy CSDT (05/10), user thấy form sửa nhân thân chỉ cho sửa 5 trường (họ tên, ngày sinh, giới tính, CCCD, nơi thường trú dạng chữ) — **thiếu ô chọn địa chỉ 2 cấp** (Xã/Tỉnh chuẩn) và **ngày cấp CCCD**. Sửa CCCD mà không sửa được ngày/nơi cấp + không chỉnh được Xã/Tỉnh chuẩn là nửa vời.
- **Chốt (user 05/10):**
  - Thêm 3 trường: **địa chỉ thường trú 2 cấp** (`NoiTT_MaDVHC`/`NoiTT_MaDVQL` — chọn Tỉnh + Xã chuẩn) · **ngày cấp CCCD** (`NgayCapCMT`) · **nơi cấp CCCD** (`NoiCapCMT`, Sở GTVT). `usp_NguoiLX_Update` đã có sẵn tất cả tham số → chủ yếu mở rộng model + `dung_tham_so_update` (đang giữ nguyên các cột này từ bản ghi cũ).
  - **Phạm vi: CHỈ TCB-03.** Form sửa dùng model CHUNG `HoSoSua` (`hoso.py`) cho cả Nạp QLY-01 lẫn TCB — nhưng user chốt **chỉ mở rộng ở TCB**, Nạp giữ 5 trường → **tách model riêng cho CDB** (`HoSoSuaCDB` ở `sync_tracuu.py`), không đụng `HoSoSua`.
  - **Nơi cư trú 2 cấp** (`NoiCT*`): để sau (ít dùng). **Số CMND cũ** (`SO_CMND_CU`): KHÔNG làm — `usp_NguoiLX_Update` không nhận tham số đó (cần sửa SP → quá tầm).
- **Lưu ý kỹ thuật (ghi vào TDD):** bộ chọn Tỉnh/Xã (`ComboLoc`/`AddressCombo`) + danh mục Sở (`DM_DonViGTVT`) hiện đọc từ **DB Nạp**; cho TCB phải đọc `DM_DVHC`/`DM_DonViGTVT` ở **DB đích** (`sqlserver_conn_dich`, theo `target_key`) — nếu không Xã/Sở hiện sai danh mục.
- **Nghiệm thu đã có (Checkpoint 14, máy CSDT 05/10):** bản 5 trường **ghi-thật PASS** — sửa chị Hương (khóa test B01-KTEST chưa gửi Sở) đổi họ tên/năm sinh/CCCD/nơi TT, `POST /sua` 200 OK, verify DB khớp. 3 nhánh còn lại (thay ảnh TCB-02, xóa/đổi khóa TCB-04) **chưa nghiệm thu** vì thiếu môi trường (ổ ảnh không khớp DB + chỉ 2 khóa chưa gửi Sở khác hạng). Feature TCB giữ 🔄.
- **Đã sửa:** PRD TCB-03 (Done khi + story + edge, hạ ⏳, Changelog v3.2) · TDD §11B.7 (Changelog v3.8) · SCREENS màn #19 (ghi chú).
- **Chưa code** (⬜) — nằm trong story TCB-03 (quay lại hàng đợi), không task BUILD-PLAN mới. Cần `/reviewtdd` phần §11B.7 vừa sửa trước khi code.

## #36 — Sửa định nghĩa "đã kết xuất DKKH" + nâng ngưỡng chặn TCB-04 + cải tiến Sync · 05/10/2026

- **Vì sao:** user phát hiện mốc "đã kết xuất DKKH" ở TCB đang đọc sai (`KhoaHoc.SoQD_KhaiGiang`) và luật TCB-04 cho đổi/xóa HV ở khóa đã gửi Sở → lệch danh sách đã nộp.
- **Định nghĩa đúng (verify DB 05/10, xem `docs/DB-GPLX_CDB_CSDT.md` §7):** khóa **đã kết xuất DKKH** = có gói `TRANS_CLI_HangDoiGui` `KieuDuLieu='DANG_KY_KHOA_HOC'` mà tên file chứa MaKH (neo `_MaKH_`, CHARINDEX). **KHÔNG** dùng `SoQD_KhaiGiang` (16/16 khóa đều có số QĐ nội bộ → không phân biệt; chỉ 14/16 đã gửi Sở) · **KHÔNG** `KhoaHoc.TT_Xuly` (NULL) · **KHÔNG** `NguoiLX_HoSo.TT_XuLy` per-HV (khóa đã gửi, HV vẫn `03`). Định nghĩa CHUNG: `sync_helpers.dkkh_exists_sql` / `dkkh_exists_cond`.
- **TCB-01/03:** chip "Đã kết xuất DKKH" + chặn sửa nhân thân — nay đọc tín hiệu đúng (C1-K09 có SoQD nhưng chưa gửi Sở → không còn bị chặn nhầm).
- **TCB-04 (nâng ngưỡng chặn — user chốt 05/10):** khóa đã DKKH → **KHÔNG xóa HV, KHÔNG đổi khóa**; đổi khóa chặn nếu **khóa đi HOẶC khóa đến** đã DKKH; `khoa-cung-hang` lọc bỏ khóa DKKH; UI vô hiệu nút Đổi khóa/Xóa + ghi lý do. DKKH luôn trước BC1 → mốc chặn sớm hơn, bao trùm BC1 (BC1+FK giữ làm lưới). *(Lật quyết định cũ "ngưỡng chặn cứng là BC1".)*
- **Nguồn giữ BC1:** QLY-02 (đổi khóa) + QLY-06 (tạo thêm hồ sơ khác hạng) bên Nạp **không áp DKKH** — nguồn `GPLX_CSDT` có bảng `TRANS_CLI` nhưng **0 bản `DANG_KY_KHOA_HOC`** (chỉ BC1/BC2) → tín hiệu DKKH không tồn tại ở nguồn.
- **+SYNC-01 (3 cải tiến):** (a) filter khóa đích *"Chỉ khóa cùng hạng & chưa kết xuất DKKH"* (checkbox mặc định bật) · (b) khóa xếp **mới-nhất-trước** (ORDER BY NgayKG DESC, **MaKH DESC** + hiện ngày KG ở combo nguồn) · (c) **giữ phiên đăng nhập qua F5** (token→localStorage + khôi phục `/local/auth/me` + tự kiểm kết nối đích khi vào màn).
- **Đã sửa:** PRD TCB-03/TCB-04 + SYNC-01 + edge "Session" (v3.1) · TDD §11B.2/§11B.7/§5.5 (v3.6) · `docs/DB-GPLX_CDB_CSDT.md` +§7 · code `sync_helpers.py`/`sync.py`/`sync_tracuu.py`/`BanDongBo.tsx`/`TraCuuCDB.tsx`/`api.ts`/`ToolAuth.tsx`/`App.tsx`.
- **Trạng thái story:** TCB-01/02/03/04 + SYNC-01 **giữ ✅** (code đã sửa + verify live/DB 05/10 — khác luồng thường: code trước, /capnhat sau). Nghiệp vụ sync lõi không đổi.
- **Còn nợ:** chưa commit · ghi-thật đổi/xóa + sửa nhân thân live vẫn chờ Checkpoint 14 (máy CSDT, có giám sát) · trên dev CDB mọi khóa đã-DKKH đều đã-BC1 nên luật mới chưa đổi outcome trên data hiện tại (đúng cho ca thực tế khóa chưa BC1).

## #35 — Feature "Tra cứu CDB đích" (TCB-01..04) · 04/10/2026

- **Mã mới:** `TCB-01` (tra khóa+lưới HV+chi tiết+ảnh), `TCB-02` (thay ảnh), `TCB-03` (sửa nhân thân), `TCB-04` (xóa HV/đổi khóa) — prefix **TCB** mới ("Tra cứu CDB", user chốt), nhóm trong phân hệ Đồng bộ CDB (SHOULD).
- **Vì sao:** user cần xem lại + vá dữ liệu HV **đã đồng bộ sang CDB đích** (`GPLX_CDB_CSDT`) ngay trong tool — xem chi tiết/ảnh, thay ảnh hỏng, sửa sai nhân thân, xóa/xếp lại khóa — mà không phải mở phần mềm CDB.
- **Chốt qua trao đổi + rà soát schema CDB (04/10):**
  - **Ảnh dùng chung 1 file vật lý** giữa DB Nạp và DB đích (sync copy `DuongDanAnh` verbatim; probe: CDB 729 HV 100% có ảnh, trỏ `D:\GPLXCSDT\ANHCDUNG\<khóa nguồn 70004>\…jp2`). → **Thay ảnh ghi ĐÈ đúng file, giữ nguyên tên+đường dẫn** (user chốt) → cả 2 DB cùng đổi ảnh. Cho thay kể cả khi DKKH/BC1 (cảnh báo).
  - **Hai mốc khóa dữ liệu (đọc Ở ĐÍCH, độc lập DB Nạp):** *đã kết xuất DKKH* = `KhoaHoc.SoQD_KhaiGiang` có giá trị (mềm — chặn **sửa nhân thân**); *đã BC1* = `TT_XuLy ≥ '05'`/có dòng `BaoCaoI`, FK `FK_NguoiLX_HoSo_BaoCaoI` NO_ACTION (cứng — chặn **xóa + đổi khóa**). Ngưỡng chặn xóa là BC1 (KHÔNG phải DKKH) để không chết Hủy sync (SYNC-03 xóa HV TT_XuLy=03).
  - Danh mục trạng thái `DM_TrangThai` (MaTT→TenTT + nhóm cấp CDB MaTTCDB: 03/04 "Đã đăng ký khóa học", 05-07 đang đào tạo, 09-14 kết quả/BC2). Dữ liệu CDB dev: HV ở 03 (639)/10 (20)/12 (70); 15/15 khóa có SoQD_KhaiGiang.
  - **Phương án A** (user chốt): thay ảnh cho + cảnh báo · sửa nhân thân chặn sau DKKH · xóa/đổi khóa chặn sau BC1.
- **Đã sửa:** PRD (+4 story TCB nhóm Đồng bộ CDB; SYNC-01 +ghi chú nút Xem chi tiết, giữ ✅; Changelog v3.0) · TDD §11B.7 mới (màn CDB, luật khóa, thay ảnh ghi đè chung, SP cần kiểm; Changelog v3.4) · SCREENS màn #19 + 2 quyết định UX (lượt 21).
- **KHÔNG chạm:** màn Tra cứu DB bên Nạp (QLY-01, đọc `GPLX_CSDT`) · quyết định TDD §12/13/14.
- **Chưa code** (⬜). **Hướng dựng:** `webui/src/pages/sync/TraCuuCDB.tsx` (tái dùng AnhModal/AnhAvatar) + endpoint CDB mới (`routers/sync.py` hoặc module mới) trỏ `sqlserver_conn_dich` + sửa `BanDongBo.tsx` (nút). Vào BUILD-PLAN qua `/kehoach` bổ sung.
- **Còn kiểm khi code:** CDB có `usp_NguoiLX_Update` / SP đổi khóa / SP xóa (như GPLX_CSDT) không — nếu thiếu thì tắt nút tương ứng + báo.
- **Tinh chỉnh sau /reviewtdd (04/10, biên bản `docs/tdd-review-04-10-2026-tcb.md`, TDD v3.5):** (1) mốc "đã BC1" chốt lại = **`NguoiLX_HoSo.MaBC1` có giá trị** (đúng cái FK NO_ACTION chặn — bỏ cách hiểu `TT_XuLy≥'05'`/dòng BaoCaoI cấp khóa vì 3 tín hiệu lệch nhau) → cập nhật câu chữ PRD TCB-04; (2) thay ảnh TCB-02 **sao lưu `_BACKUP.jp2` cùng thư mục ảnh trước khi ghi đè** → cập nhật PRD TCB-02; (3) endpoint TCB ghi buộc token operator; (4) nới câu chữ §12 "DB đích"; (5) +bảng ma trận quyết định. Không đổi phạm vi/tính năng — chỉ làm chính xác lại quyết định đã chốt ở #35.

---

## #34 — Cấu hình kết nối lên header dùng chung + tách DB Nạp/Sync + làm đẹp UI sync · 04/10/2026

- **Mã mới:** `HTG-07` (Bảng cấu hình kết nối dùng chung ở header) — prefix `HTG` sẵn có, nhóm MUST.
- **Mã sửa:** `HTG-01` (bullet Cấu hình trỏ sang HTG-07, giữ ✅), `SYNC-02` (quản lý đích dời vào panel — hạ ✅→⏳), `SYNC-01` (làm đẹp UI — hạ ✅→⏳). Không mã nào nghỉ hưu.
- **Vì sao:** chủ dự án phản hồi khi test: cấu hình kết nối DB dùng chung cả tool nhưng nằm ở màn riêng → "không biết cài kết nối ở đâu"; cần đưa lên **header** để mọi màn xem/sửa được, và **phân biệt rõ** đâu là DB để **Nạp** (1 nguồn `GPLX_CSDT`) với các DB để **Sync sang** (nhiều, chọn mặc định) — tránh nhầm hai loại. Đồng thời làm đẹp combobox năm/khóa + chọn DB đích + danh sách HV để sync (tên hài hòa, dễ đọc).
- **Chốt (user 04/10, phương án A):** gộp tất cả vào **một bảng cấu hình mở từ icon ⚙ header**, chia 2 khối tách bạch (① kết nối chung + DB nguồn Nạp · ② nhiều DB đích Sync); **bỏ** màn Cấu hình riêng `/tool/cau-hinh` + mục "Quản lý CSDL đích" khỏi sidebar — chỉ vào từ header.
- **Ràng buộc:** code phần sync vẫn **bám sát sync_tool v2.0** — thay đổi này thuần UI/IA, không đụng nghiệp vụ sync.
- **Đã sửa:** PRD (+story HTG-07; sửa bullet HTG-01; hạ SYNC-01/SYNC-02 ✅→⏳ + ghi chuẩn UI; Changelog v2.9) · TDD §5.0 + §11B.0 (bỏ route cau-hinh/db-dich khỏi sub-nav, mô tả panel ⚙ header; Changelog v3.3) · SCREENS (màn #4 thành panel header, #16 làm đẹp, #17 dời vào panel; +3 quyết định UX; lượt 20).
- **KHÔNG chạm:** quyết định kỹ thuật TDD §12 (sidebar module) / §13 (nhiều đích dùng chung host/user/pass) / §14 (SSE) — đều còn đúng → **không cần `/reviewtdd`**. Backend `/local/config*`, `/local/sync/targets`, config-store giữ nguyên.
- **Bug môi trường đã sửa (không phải lỗi code):** backend nền khởi động bằng `tool-start.bat` **không có `--reload`** → kẹt bản code cũ (chạy sau SYNC-02 nhưng trước SYNC-01) → route `/local/sync/nguon/nam` + `/dich/nam` trả **404**, combobox năm/khóa ở Bàn đồng bộ trống (frontend `.catch` nuốt lỗi). **Xử lý:** restart backend → route trả 401 (đã có), đăng nhập gọi `nguon/nam` trả `[2026…2012]` ✔. **Đã thêm `--reload --reload-dir app`** vào `tool-start.bat` (user duyệt) để sửa code backend tự nạp, khỏi tái phát. Phụ: màn Bàn đồng bộ bỏ 2 `catch(()=>{})` câm khi tải năm/khóa → nay báo lỗi rõ (chính cơ chế che lỗi 404 lần này).
- **Chưa code** (⬜). **Hướng dựng:** sửa `ToolLayout.tsx` (icon ⚙ header + panel), gộp `CauHinh.tsx` + `DbDich.tsx` vào panel (2 khối), gỡ 2 route khỏi `App.tsx` + sidebar; làm đẹp `BanDongBo.tsx` + `ComboLoc.tsx`. Dùng skill `impeccable` + `ui-ux-pro-max`. Vào BUILD-PLAN qua `/kehoach` bổ sung (hoặc gộp vào task UI sync đang có).

---

## #33 — Feature "Đồng bộ CDB" (SYNC-01/02/03) + tool chuyển sang sidebar module · 04/10/2026

- **Mã mới:** `SYNC-01` (Bàn đồng bộ), `SYNC-02` (Quản lý DB đích), `SYNC-03` (Lịch sử & Hủy sync) — prefix `SYNC` mới, nhóm SHOULD.
- **Vì sao:** cần đưa nghiệp vụ đồng bộ học viên `GPLX_CSDT` → CDB `GPLX_CDB_CSDT` (đang chạy bằng công cụ rời `sync_tool` v2.0, CustomTkinter) vào chung tool máy CSDT, nhưng **tách bạch** để không lẫn với Nạp (hai bên ghi vào 2 DB khác nhau — dễ thao tác nhầm).
- **Nguồn port:** `D:\Du_An\GPLX\sync_tool` v2.0 = 3 file `sync_gplx.py` + `db_helpers.py` + `sync_history.py` (đã đọc trọn; không còn logic ngoài 3 file). Format mã theo Phụ lục XXVII TT 17/2026/TT-BXD.
- **Đã sửa/thêm:**
  - PRD: thêm nhóm 🟣 "Đồng bộ CDB" (3 story) cuối SHOULD; ⑥ NFR thêm kiến trúc module+sidebar + tool chỉ-desktop; ⑦ thêm 3 edge Sync; Changelog v2.8.
  - TDD: §11B (kiến trúc module/sidebar · kết nối đích nhiều DB · luồng sync + MaDK batch + guard race · SSE · rollback dual-mode · 3 nợ kỹ thuật) + §2.4 cây thư mục; Changelog v3.2.
  - TDD-decisions: §12 (sidebar module), §13 (kết nối đích dùng chung host/user/pass, nhiều đích), §14 (SSE).
  - SCREENS: màn #16/17/18 (⬜) + quyết định UX (sidebar, tool desktop ≥1280px bảng cuộn ngang, bám design system tool thật + dùng skill UI).
  - **Phân tích DB đích (04/10)** → `docs/DB-GPLX_CDB_CSDT.md` (mới): cách tạo HV chuẩn (3 SP `usp_NguoiLX_Insert`/`usp_NguoiLX_HoSo_Insert`/`usp_NguoiLXHS_GiayTo_Insert`) · sinh mã (`CreateNewMaDK` hardcode getdate, `CreateNewSoHoso` `B01`) · MaCSDT lấy từ khóa đích = `QTHT.MA_CSDT`=75032 · PK(MaDK) + FK cascade (xóa khóa/người kéo xóa hồ sơ; BaoCaoI chặn xóa) · cột kết quả đào tạo sẵn trong `NguoiLX_HoSo` (cho module #3). CLAUDE.md thêm trỏ đọc trước khi code CDB. TDD §11B.6 cập nhật hướng chốt 3 nợ kỹ thuật.
  - **Khóa đích đã BC1 (04/10):** cảnh báo nhưng **vẫn cho sync** (phương án B — khác NAP-02 chặn cứng; sync là bù dữ liệu chủ động). sync_tool gốc không chặn/không cảnh báo. PRD SYNC-01 +tiêu chí.
  - **Tiện ích + edge thêm (04/10, user đồng ý):** UI (a) combo khóa gõ-để-lọc · (b) toggle "chỉ hiện HV sẽ tạo mới" · (c) đếm dòng tick cạnh SYNC. Edge: E1 chặn HV thiếu CCCD · E2 cảnh báo trùng CCCD trong DS nguồn · E3 sync-lại an toàn khi mất kết nối giữa lô (idempotent qua skip). E4 (HV chưa ảnh) giữ nguyên v2.0 (ép TT_XuLy 03). Dropdown khóa nguồn+đích bám đúng v2.0: combo Năm (DISTINCT YEAR NgayKG, mặc định năm nay) + combo Khóa (TrangThai=1 + năm).
  - **Chốt qua mock `ui-mock/sync.html` (04/10):** ① **bỏ ô "Cán bộ nạp"** → `NguoiTao/NguoiSua='admin'` (probe DB `GPLX_CDB_CSDT`: NguoiTao chỉ `ADMIN`/`SYNC`, 10 bản mới nhất `admin` — CDB không có cán bộ riêng; TDD-decisions §15) · ② **bỏ Xuất CSV** (không cần) · ③ tối ưu danh sách: khung chọn khóa **cố định + thu gọn được**, **header bảng dính**, **nút SYNC cố định ở chân**, **phân trang** 20/50/100 (mẫu `PhanTrang.tsx`), dòng dày hơn để hiện nhiều HV.
- **Còn nợ:**
  - **Chưa code** (⬜). **Hướng dựng UI đã chốt (user 04/10, phương án A):** BỎ QUA `ui-demo` (prototype cũ đã lệch so với `tool/webui` thật) → dựng **1 mock HTML sidebar + 3 màn Sync bám token `tool/webui` thật** (dùng skill UI `ui-ux-pro-max`/`impeccable`) để chốt layout → **code thẳng vào `tool/webui`** (gồm đổi `ToolLayout`→sidebar). KHÔNG dùng `/prototype-next`.
  - **Xác minh trước khi code:** chữ ký `usp_NguoiLX_Insert` + hàm `CreateNewMaDK` trên DB đích CSDT **70004** có giống bản 75032 mà sync_tool giả định.
  - **3 nợ kỹ thuật port** (quyết giữ/vá khi code): `SoHoSo` sinh ở Python (nên gọi `CreateNewSoHoso`) · `DELETE` NguoiLX mồ côi quét toàn DB (nên lọc khóa) · `except: pass` khi copy giấy tờ.
  - Đổi `ToolLayout` sang sidebar đụng chrome module Nạp (hành vi màn Nạp **không đổi** → không hạ trạng thái story Nạp).
- **Chưa làm tay:** `/kehoach` bổ sung (~3-4 task: config+kết nối đích → API+SSE → UI sidebar+3 màn → rollback); `/reviewtdd` (đã sửa §11B + Data-flow); `/prototype-next` hoặc build thẳng.

---

## #32 — Lưu nháp chuẩn bị BỀN + 2 chip trạng thái + bổ sung ảnh 2 nguồn (màn Nạp lô) · 04/10/2026

- **Mã:** `NAP-01`, `QLY-05` (bổ sung tiêu chí, prefix cũ, không nghỉ hưu mã).
- **Vì sao:** chủ dự án hỏi "nháp chưa nạp có mất khi kéo lại / xóa hết trên app web không" → rà kiến trúc 3 kho tách biệt: nháp chuẩn bị (địa chỉ 2 cấp, ảnh đổi nền, tick) hiện **chỉ ở RAM** của màn, mất khi tải lại trang. Chốt nâng nháp lên **lưu bền** để người nạp chuẩn bị nhiều HV an tâm, kèm 2 chip nhìn nhanh dòng nào đã map địa chỉ / đã có ảnh, nút mở to dễ bấm, và cho bổ sung ảnh HV thiếu ảnh lấy từ file hoặc kéo lại ảnh thô VPS.
- **Lưu nháp bền (TDD §9.3a):** bảng mới `nhap_chuan_bi` trong `staging.sqlite` (tách khỏi `keo_ve` dữ-liệu-gốc-VPS); lưu địa chỉ/chi tiết/nơi cấp/tick + ảnh (`jp2_b64`+preview). API tool-local `GET/PUT /local/nap/nhap/{uuid}`. **Tự xóa** (`nhap_xoa(uuid)`) ở mọi điểm dòng `keo_ve` kết thúc: nạp xong, "Bỏ khỏi hàng đợi", đồng bộ xóa VPS. **BUG-04:** `keo_ve_upsert` khi làm tươi thấy `noi_tt_raw` đổi → reset ĐỊA CHỈ nháp (giữ ảnh/tick/nơi cấp) + chip địa chỉ về ✗ + toast.
- **UX màn Nạp lô (TDD §10.5):** 2 chip `✓/✗ Địa chỉ 2 cấp` + `✓/✗ Có hình` (mặc định ✗); nạp **chặn khi thiếu địa chỉ**, **cảnh báo khi thiếu ảnh** + lối tắt chuyển Tra cứu DB lọc "chưa ảnh"; mở drawer bằng cả dòng + nút "Xử lý" to.
- **Bổ sung ảnh HV thiếu ảnh (TDD §11.5):** AnhModal lấy ảnh gốc từ **file** (`chonFile`, sẵn có) hoặc **ảnh thô VPS** (`vps.tra_uuid`→`vps.tai_anh`→`AnhModal.napTuUrl`, sẵn có) — điều kiện ảnh còn trên VPS (~30 ngày); hết hạn thì chỉ còn nguồn file. Qua cùng luồng QLY-05 (đổi nền → `.jp2` → `nap_anh`).
- **Quyết định PII (TDD-decisions §11):** lưu ảnh nháp bền ở máy tool đi ngược nguyên tắc cũ "không để ảnh căn cước ở máy tool"; chấp nhận có điều kiện (máy nội bộ CSDT + cam kết tự xóa + không commit/backup). Phương án B (lưu bền + tự xóa) do user chốt; đã bác phương án không-lưu-ảnh.
- **Xác minh bằng GitNexus:** `keo_ve` chỉ chứa metadata (không có chỗ lưu nháp → mới hoàn toàn); `AnhModal` đã có `chonFile`+`napTuUrl`; `nap_anh` dùng chung `ghi_anh_update`; `vps.tra_uuid`/`vps.tai_anh` sẵn có → phần ảnh tái dùng gần hết, chỉ wiring.
- **Đã sửa:** PRD (NAP-01 +4 "Done khi" + 1 edge; QLY-05 +1 "Done khi"; cả 2 giữ trạng thái, ghi chú yêu cầu mới) · TDD §9.3a (mới) /§10.5/§11.5 + Changelog v3.2 · TDD-decisions §11 (mới).
- **Chưa code** — vào BUILD-PLAN (nằm trong task redesign Nạp lô #26 chưa code + thêm phần nháp bền/ảnh VPS). Code UI chạy skill `impeccable`.
- **Còn nợ:** toàn bộ phần code (⬜). Màn: cập nhật `ui-demo/SCREENS.md` ghi chú 2 chip + nút Xử lý.

---

## #30 — Redesign giao diện DESKTOP app web: Quét ưu tiên nhập tay + Hồ sơ đã gửi xóa nhiều · 03/10/2026

> Đổi số từ #28 → #30 khi gộp 2 phiên song song (số #28 đã thuộc QLY-09).

- **Mã:** `THU-01` (✏️ Sửa), `THU-05` (➕ Thêm)
- **Vì sao:** Trên máy tính, nhân viên gõ bàn phím là chính; quét QR bằng webcam khó canh. Giao diện cũ (dùng chung mobile) đặt nút Quét QR giữa màn + chặn màn "chọn cách nhập" trước form → desktop bấm thừa. Nút Xóa hồ sơ chờ nạp chôn trong modal → xóa nhiều phải mở từng cái.
- **Đã làm:** ① Quét (THU-01) desktop vào thẳng form nhập tay (bỏ cổng `ChonCach`), Quét QR/Tải ảnh thành nút phụ góc phải, popover camera đè form tự điền, "Lưu & nhập tiếp" → form trống; mobile giữ nguyên. ② Hồ sơ đã gửi (THU-05) desktop chọn-nhiều-để-xóa (ô tích chỉ dòng Chờ nạp + thanh Đã chọn N/Xóa N + dialog), lặp `DELETE /api/ho-so/:uuid` client (mẫu `QuanTriHoSo`); mobile giữ xóa lẻ.
- **Code:** `webapp/src/pages/Quet.tsx` (hook `useIsDesktop` + `QuetPopover`) + `DaGui.tsx` (chọn-nhiều + phân biệt 409). Thuần client. Kiểm: build + 24 vitest + review-nghiepvu THU-01 8/8, THU-05 đủ.
- **Còn nợ:** chụp Playwright 3vp + verify desktop sau deploy → khi đó hạ ⚠️ Partial.

---

## #29 — Tool máy Nạp: dời nút nạp lên header + combobox gõ-lọc địa chỉ · 03/10/2026

- **Mã:** `NAP-01` (dời nút), `NAP-03` (combobox) — ✏️ Sửa UI, thuần client.
- **Vì sao:** ① 2 nút "Chọn tất cả sẵn sàng" + "Nạp N học viên vào khóa" trước nằm ở **thanh dính đáy** — user muốn đưa **lên header** cho thao tác gọn, nút nạp nằm cùng vùng chọn khóa/kéo về. ② Ô "Chọn tay" địa chỉ 2 cấp mới là 2 **dropdown** — danh sách xã rất dài, cuộn mệt; user muốn **gõ để lọc**.
- **Đã làm:**
  - **NAP-01** (`tool/webui/.../NapHoSo.tsx`): gỡ thanh dính đáy, dựng lại thành **hàng hành động shrink-0 ngay dưới tab lọc** trong container `h-[calc]` → chỉ danh sách cuộn, nút Nạp luôn hiện. Chỉ hiện ở tab "Cần xử lý".
  - **NAP-03** (`tool/webui/src/components/AddressCombo.tsx`): thêm `ComboLoc` — ô gõ → danh sách gợi ý lọc dần (khớp cả **không dấu** nhờ `boDau`), bấm/Enter chọn; thay 2 `<select>` Tỉnh + Xã ở "Chọn tay". `getTinh`/`getXa` dữ liệu sẵn, **không đổi backend**.
- **Kiểm:** tool webui build + typecheck + **29 vitest** pass. **Chưa chụp Playwright** (màn tool cần backend + DB). Wireframe đã chốt với user.
- **Nhánh:** code ở `feat/nap-address-ui` (commit `03d4243`) — chưa merge main.

## #28 — Đối soát & đồng bộ trạng thái VPS↔CSDT (QLY-09) · 03/10/2026

- **Mã:** `QLY-09` (MỚI, nhóm QLY, nối tiếp QLY-08).
- **Vì sao:** ca Lê Thị Hồng (BUG-01) lộ ra khi VPS và CSDT lệch trạng thái thì không có cách sửa trong ứng dụng — phải SSH sửa tay DB production. Chủ dự án yêu cầu: "phải có cách đồng bộ lại để fix, không để treo lỗi".
- **Chốt (chủ dự án, 03/10):**
  - Phạm vi **theo khóa / theo yêu cầu** (A) — không quét toàn bộ (tránh so chéo 2 DB toàn tập, chậm khi lớn; mở rộng sau nếu cần).
  - Panel admin/operator ở tool (trong Tra cứu DB), **không collector**.
  - **3 ca lệch + nút sửa 1 chạm**, tái dùng đường có sẵn: ① VPS `imported` & CSDT không có `MaDK` (phantom) → **Trả về chờ nạp** (`tra_ve_cho_nap`) · ② CSDT có HV & VPS chưa `imported` → **Đánh dấu đã nạp** (`da_nap`) · ③ `importing` treo quá ngưỡng → **Mở khóa** (`unlock`).
  - **Phòng tuyến 2:** `nap_fn` bỏ gọi `da_nap` khi `_nap_mot` trả kết quả cũ từ vé idempotency (không INSERT mới) — chặn tận gốc "phantom import" (BUG-01).
- **Đã sửa:** PRD +story `QLY-09` (nhóm QLY, ⏳ Todo) · TDD §11.8 mới + Changelog 3.0.
- **Chưa code** — vào BUILD-PLAN task mới (`/kehoach` bổ sung). Thuần tool (webui panel + tool backend đọc CSDT/gọi VPS); KHÔNG bảng VPS mới, KHÔNG SP CSDT mới, KHÔNG endpoint nạp mới.
- **Không đụng:** schema DB CSDT · bảng VPS · app web collector.

---

## #26 — Chốt nghiệp vụ + UX trước khi code #24 (bàn giao, popup cảnh báo, ảnh gốc, redesign Nạp lô) · 03/10/2026

- **Mã:** `THU-05`, `QLY-08`, `QLY-03`, `NAP-01`, `NAP-04`, `QLY-05` (bổ sung tiêu chí, prefix cũ, không nghỉ hưu mã).
- **Vì sao:** trước khi code #24, chủ dự án + AI bàn nghiệp vụ để tránh app web và tool đá nhau khi cùng một hồ sơ bị sửa/xóa từ 2 phía; đồng thời chốt UX cho dễ dùng.
- **Nguyên tắc bàn giao (TDD §7.5 mới):** mốc "Nạp" là điểm chuyển quyền sở hữu. **Trước nạp** (`pending`) app web làm chủ (collector thêm/sửa/xóa); **sau nạp** (`imported`) tool/CSDT làm chủ, bản ghi app web **đóng băng** (chỉ xem). Phân biệt rõ 2 nút xóa HV đã nạp: **"Xóa hẳn" (QLY-03)** = bỏ luôn, nạp lại phải nhập lại ở app (bản VPS vẫn `imported` lịch sử — Q1); **"Gỡ về chờ nạp" (QLY-08)** = `imported→pending`, nạp lại không nhập lại, ảnh dùng ảnh thô VPS (Q2), về `pending` thì collector sửa/xóa được tiếp (Q3).
- **Popup cảnh báo + hướng dẫn** (copy impeccable, tái dùng panel xác nhận 2 bước + Banner sẵn có): THU-05 (xóa hồ sơ chờ nạp + chú thích khi đã nạp), QLY-08 (gỡ về chờ nạp + banner "đồng bộ máy chủ lỗi, thử lại"), QLY-03 ("Xóa hẳn" tách bạch với "Gỡ về chờ nạp").
- **"Dùng lại ảnh gốc"** (TDD §9.1): AnhModal thêm prop `anhGoc` + nút quay về ảnh nguyên bản (bỏ chỉnh sửa) — NAP-04 là ảnh thô VPS, QLY-05 là ảnh `.jp2` đang lưu; ẩn nút khi không có nguồn.
- **Redesign màn Nạp lô (NAP-01, TDD §10.5):** trạng thái sẵn sàng mỗi dòng (`✔ Sẵn sàng`/`⚠ Thiếu…`), "Chọn tất cả sẵn sàng", drawer "Chuẩn bị" (bỏ cột cố định), dialog nạp 3 pha (xác nhận → tiến độ → báo cáo + "Nạp lại lỗi"), nút "Xem trong DB". Thuần client, không endpoint nạp mới.
- **Đã sửa:** PRD (6 story thêm "Done khi") · TDD §7.2/§7.5/§9.1/§10.5 + Changelog v2.9 · `ui-demo/SCREENS.md` (wireframe Nạp lô + ghi chú AnhModal).
- **Chưa code** — vào BUILD-PLAN task mới (`/kehoach` bổ sung). Code lúc làm UI chạy skill `impeccable`.

## #25 — Sửa nhãn trạng thái VPS trong PRD: `done` → `imported` · 03/10/2026

- **Mã:** `QLY-08`, `THU-05` (sửa nhãn trong story đã có, prefix cũ, không nghỉ hưu mã).
- **Vì sao:** review TDD #24 (Điểm 1) phát hiện PRD gọi trạng thái bản ghi VPS là `done`, nhưng DB thật (`server/db/init.sql:28`) chỉ định nghĩa `pending/importing/imported/deleted` và TDD dùng `imported`. Người code đọc PRD thấy `done` sẽ đi tìm trạng thái không tồn tại, hoặc map nhầm sang staging local `nap_xong` → hỏng guard "chỉ xóa khi chưa nạp".
- **Đã sửa:** PRD `[THU-05]` Done khi + Edge case, `[QLY-08]` Steps bước 3 — 3 chỗ `done` → `imported`. Giữ nguyên `nap_xong` (staging local của tool, không phải trạng thái VPS).
- **Không chạm:** TDD (đã đúng `imported` từ v2.7/2.8), màn hình, code.
- **Hồ sơ:** biên bản `docs/tdd-review-03-10-2026.md`.

- **Mã:** `QLY-08` (MỚI), `THU-05` (MỚI), `NAP-01` (mở rộng). Prefix cũ, không nghỉ hưu mã.
- **Vì sao:** buổi verify #22, chủ dự án nêu 2 nhu cầu đồng bộ chưa có:
  - Nạp nhầm khóa → muốn **gỡ HV ra và trả về danh sách chờ nạp** (nạp lại đúng khóa), VPS cập nhật theo, ảnh vẫn hiện. Nút "Xóa" hiện tại chỉ bỏ hẳn ở CSDT, không trả về.
  - Collector gửi nhầm ở app web → muốn **xóa hồ sơ đã gửi**, và tool kéo về thì hồ sơ đó **biến mất khỏi hàng chờ**.
- **Chốt (chủ dự án, 02/10/2026):**
  - **QLY-08** là nút **RIÊNG** ("Gỡ về chờ nạp"), **giữ "Xóa"** để bỏ hẳn hồ sơ rác/trùng. Chỉ khóa **chưa BC1** (BC1 cấm như QLY-03). HV đã có GPLX → FK chặn. Bản ghi VPS đã dọn PII → báo không gỡ được.
  - **Nâng cấp server VPS**: thêm đường `tra-ve-cho-nap` (imported→pending, gỡ ma_dk). Ảnh khi về chờ nạp dùng **ảnh thô còn trên VPS** (không chuyển ngược .jp2).
  - **THU-05**: chỉ xóa hồ sơ **chưa nạp** (`pending`); **soft-delete** trên VPS (trạng thái `deleted` + audit_log, giữ vết); phân quyền **collector của mình / admin bất kỳ**.
  - **NAP-01**: "Kéo về từ VPS" đồng bộ **bỏ** dòng staging `pending` đã thành `deleted` trên VPS.
- **Đã sửa:** PRD +story `QLY-08` (nhóm QLY) · +story `THU-05` (nhóm THU) · `NAP-01` +Done khi (đồng bộ xóa, hạ ✅→⏳). TDD §4.3 +DELETE hồ sơ · §4.4 +tra-ve-cho-nap · §7.1 +2 chuyển trạng thái · §11.7 mới · §6 +nút Xóa app web · Changelog 2.7. SCREENS +2 quyết định UX (lượt 15, không dựng màn).
- **Hạ trạng thái:** `NAP-01` ✅→⏳ (thêm đồng bộ xóa — phần cũ vẫn đúng, story quay lại hàng đợi).
- **Code sẽ đụng:** **server VPS** `server/app` (endpoint `DELETE /api/ho-so/:uuid` soft-delete + `POST /api/nap/:uuid/tra-ve-cho-nap` + kéo trả tập uuid đã deleted) · **tool** `tool/app/vps.py` (hàm gọi mới) + `tool/app/routers/hoso.py` (`go-ve-cho-nap`) + `tool/app/nap.py` (staging: về pending / đồng bộ bỏ deleted) + `tool/webui/.../TraCuuDB.tsx` (nút Gỡ) · **app web** `webapp/src` (`DaGui` nút Xóa). Dùng lại trạng thái `deleted` + `audit_log` sẵn có — không bảng mới.
- **Còn nợ:** `/reviewtdd` (TDD đổi API + nghiệp vụ + state machine VPS) · `/kehoach` bổ sung (task mới đụng 3 nơi: server VPS + tool + app web) · code · verify thật.
- **Không đụng:** schema DB CSDT (chỉ đọc/xóa qua SP có sẵn) · bảng VPS mới (tái dùng trạng thái `deleted`).

---

## #23 — Sửa UX quản lý ảnh + nhãn nút (phát hiện khi verify #22) · 02/10/2026

- **Mã:** `NAP-04` (sửa), `QLY-05` (sửa), `QLY-06` (đổi nhãn). Không thêm/nghỉ hưu mã.
- **Vì sao:** buổi verify #22 trên máy CSDT, chủ dự án gặp 3 vướng ở phần ảnh:
  - **Chỉnh ảnh xong không xem lại được + mở lại phải chỉnh từ đầu:** sau "Dùng ảnh này", khung ảnh chỉ hiện **icon check** (không hiện ảnh thật), và "Mở trình chỉnh ảnh" lần sau nạp lại **ảnh thô VPS** thay vì ảnh đã chỉnh. Kỳ vọng đúng: xem lại được ảnh vừa chỉnh + mở ra chỉnh tiếp trên ảnh mới nhất.
  - **Dễ tưởng đã lưu ở bước "Xử lý ảnh":** nút áp dụng ("Dùng ảnh này") mờ (viền) + nhãn không rõ là bước lưu → operator dừng ở "Xử lý ảnh", ảnh chưa vào hồ sơ.
  - **Nhãn nút "Mở khóa khác" (QLY-06) gây hiểu nhầm** là *chuyển* HV sang khóa khác (nguy hiểm với khóa đã báo cáo) — thực chất nó **tạo hồ sơ MỚI ở khóa khác hạng, giữ hồ sơ cũ** (học thêm hạng).
- **Chốt (chủ dự án, 02/10/2026):**
  - Giữ **bản xem trước PNG** (backend `/local/anh/xu-ly` đã trả ở field `preview`) cạnh `jp2` trong nháp → khung ảnh hiện **ảnh đã chỉnh**; mở lại trình chỉnh ưu tiên **ảnh đã chỉnh gần nhất**. Lý do dùng PNG: `.jp2` trình duyệt không render trực tiếp.
  - Nút áp dụng ảnh để **nổi bật (nút đặc màu chính)** + badge kết quả ghi rõ *"đã xử lý — bấm để áp dụng"*.
  - Nút đổi nhãn **"Tạo thêm hồ sơ ở khóa học khác hạng"**, **giữ hiển thị cả ở khóa đã BC1** (không đụng báo cáo cũ) — phân biệt với "Đổi khóa" (QLY-02, chuyển cùng hạng, đã ẩn khi BC1).
  - Lưu ý nghiệp vụ: ở **tab Nạp**, "Dùng ảnh này" chỉ đưa ảnh vào **nháp trong trình duyệt**; ảnh chỉ thật sự ghi khi bấm "Nạp HV vào khóa".
- **Đã sửa:** PRD `NAP-04` (+3 Done khi, hạ ⏳) · PRD `QLY-05` (+Done khi, hạ ⏳) · PRD `QLY-06` (nhãn nút + giữ ở BC1, hạ ⏳) · TDD §9.1 ghi chú giữ `preview` + Changelog 2.6 · SCREENS +2 quyết định UX (lượt 14, không dựng màn).
- **Hạ trạng thái:** `NAP-04` ⚠️→⏳ · `QLY-05` 🔄→⏳ · `QLY-06` ⚠️→⏳ (yêu cầu UI đổi — code cũ chạy đúng nhưng phần UI phải làm lại, story quay lại hàng đợi).
- **Code sẽ đụng:** `tool/webui/src/components/AnhModal.tsx` (nút áp dụng nổi bật + nhãn; trả kèm `preview`) · `tool/webui/src/pages/tool/NapHoSo.tsx` (lưu `preview` vào `nhap[uuid]`, khung ảnh hiện preview, `anhBanDau` ưu tiên preview) · `tool/webui/src/pages/tool/TraCuuDB.tsx` (hiện ảnh mới sau lưu + mở lại chỉnh tiếp; đổi nhãn nút "khóa khác") · có thể `lib/api.ts` (kiểu trả `xuLyAnh`).
- **TÁCH riêng (KHÔNG trong đợt này):** ❓ D — gỡ HV khỏi khóa → trả về **chờ nạp** + cập nhật VPS + giữ ảnh. Tính năng mới lớn (đụng DB CSDT + VPS), bàn `/capnhat` riêng.
- **Không đụng:** backend xử lý/ghi ảnh (đã trả `preview` sẵn) · DB đích · server VPS · app web.

---

## #22 — Mở rộng quản lý ảnh Tra cứu DB + bảo toàn Báo cáo 1/2 · 02/10/2026

- **Mã:** `QLY-01` (mở rộng), `QLY-03` (sửa), `QLY-05` (sửa + 🐛), `QLY-07` (MỚI), `NAP-01` (mở rộng).
- **Vì sao:** chủ dự án muốn xem/sửa ảnh HV đã nạp ngay ở Tra cứu DB (hiện chỉ hiện chữ "Đã có/Thiếu ảnh", KHÔNG render ảnh) + đổi nền trắng hàng loạt cho ảnh cũ. Khi tra schema DB cũ (`DBcu/DBcu30092026.sql`) để kiểm tác động Báo cáo 1/2, phát hiện **bug nghiêm trọng** ở luồng thay ảnh.
- **🐛 Bug phát hiện (QLY-05, có sẵn trong code task 27):** `ghi_anh_update` (dùng chung NAP-05/QLY-05) set cứng `TT_XuLy='03'`. Mà `usp_BaoCao2_DSHS` lọc HV theo `TT_XuLy in ('11'..'19')` → **thay ảnh cho HV đã vào Báo cáo 1/2 làm HV rơi khỏi Báo cáo 2** ("HV không có trong BC1"). Liên kết HV↔báo cáo: `NguoiLX_HoSo.MaBC1`(FK→`BaoCaoI`)/`MaBC2`, `BaoCaoII.MaBCI`→`BaoCaoI`.
- **Chốt luật (khóa đã BC1):** thay ảnh/đổi nền **ĐƯỢC** (ảnh không nằm trong nội dung báo cáo) nhưng **phải giữ `TT_XuLy`**; sửa thông tin nhân thân **CHẶN** (đã chặn sẵn, BR-012); xóa HV **CHẶN ở backend** (mới).
- **Nhóm 1 (làm trước):**
  - QLY-01: hiện ảnh chân dung + đường dẫn khi xem HV (backend transcode `.jp2`→PNG) · avatar mỗi dòng lưới (thumbnail + cache; chưa ảnh → icon người) · cảnh báo khi DB có path mà mất file · thống kê đầu khóa (tổng/thiếu ảnh/BC1) · nút đổi-khóa/xóa nhanh ra lưới · click ảnh → trình chỉnh.
  - QLY-05: 🐛 giữ `TT_XuLy` khi HV đã Báo cáo (`'11'`–`'19'`), chỉ nâng `'01/02'→'03'` khi chưa BC · mở trình chỉnh ảnh từ Tra cứu DB.
  - QLY-03: chặn xóa HV khóa BC1 ở BACKEND (`usp_NguoiLX_Delete`), không chỉ ẩn nút UI.
  - NAP-01: "Bỏ khỏi hàng đợi" (xóa dòng 🟢 khỏi `staging.sqlite`, KHÔNG đụng prod — tách bạch "Xóa khỏi DB") + "Nạp lại nhanh" dòng 🔴.
- **Nhóm 2 (story mới QLY-07):** đổi nền trắng cả khóa — chạy nền + thanh tiến độ · sao lưu `_BACKUP` trước ghi đè · mặc định "chỉ ảnh chưa trắng" · giữ `TT_XuLy` (nếu không, cả khóa đã BC2 biến mất cùng lúc).
- **Đã sửa:** PRD `QLY-01`/`QLY-03`/`QLY-05` (+Done khi, hạ ⏳) · PRD `NAP-01` (hạ ⏳) · PRD +story `QLY-07` · TDD §7.2 + §11.1 + §11.3 + §11.5 + §11.6 mới + Changelog 2.4 · SCREENS màn #12/#14/#15 + 3 quyết định UX + wireframe.
- **Hạ trạng thái:** `QLY-01` ⚠️→⏳ · `QLY-03` ⚠️→⏳ · `QLY-05` ⚠️→⏳ · `NAP-01` ✅→⏳ (mở rộng yêu cầu — code cũ vẫn đúng nhưng story quay lại hàng đợi).
- **TREO (chưa quyết, KHÔNG vào PRD):** ❓ sửa thông tin nhân thân *trước* khi nạp trong tool — bẫy "Kéo lại từ VPS" đè. Nghiêng về KHÔNG làm (giữ sửa trên app web). Chờ chủ dự án quyết.
- **Code sẽ đụng:** `tool/app/nap.py` (`ghi_anh_update` giữ `TT_XuLy`; +xóa staging `keo_ve`) · `tool/app/routers/hoso.py` (`xoa_ho_so` chặn BC1; +endpoint phục vụ ảnh + thumbnail) · `tool/app/image.py` (transcode `.jp2`→PNG) · `tool/webui/src/pages/tool/TraCuuDB.tsx` + `NapHoSo.tsx` + `lib/api.ts` · màn QLY-07 mới.
- **Còn nợ:** `/reviewtdd` (TDD đổi API §11.1 + nghiệp vụ §11.3/§11.5/§11.6) · `/kehoach` bổ sung (rework QLY-01/03/05 + NAP-01 + task QLY-07) · `/prototype-next` dựng màn #14/#15 · code · chủ dự án quyết mục ❓ treo.
- **Không đụng:** schema DB đích (chỉ đọc; `_BACKUP` là thư mục file) · server VPS · app web.

---

## #21 — Zoom trình chỉnh ảnh: thu nhỏ dưới cỡ gốc + lăn chuột + thang giữa · 02/10/2026

- **Mã:** `NAP-04` — tinh chỉnh zoom AnhModal (phản hồi test), không story mới.
- **Vì sao:** user test — (1) zoom lấy ảnh ban đầu làm mốc NHỎ nhất, không thu nhỏ thêm được; (2) muốn lăn chuột để phóng/thu; (3) thang zoom nên mặc định ở giữa (trái thu nhỏ, phải phóng to).
- **Mới:** thang zoom đổi sang **mũ `3^t`, t ∈ [−1, 1]** — `t=0` (GIỮA) = cỡ gốc 1×, `t=−1` ≈ 1/3× (thu nhỏ), `t=+1` = 3× (phóng to). Slider nhãn "Thu nhỏ ← → Phóng to", mặc định giữa. Thêm **lăn chuột** (onWheel) trên khung: lăn xuống thu nhỏ, lăn lên phóng to. Vùng lộ khi thu nhỏ/kéo → nền trắng (canvas).
- **Đã sửa:** PRD `NAP-04` (Done khi) · TDD §9.1 + Changelog 2.3.
- **Code sẽ đụng:** `tool/webui/src/components/AnhModal.tsx` (state `mucZoom` thay `zoom`, `datZoom`, `onWheel`, slider −1..1).

## #20 — Nâng cấp trình chỉnh ảnh: xoay + khung mẫu + tăng tốc xóa phông · 02/10/2026

- **Mã:** `NAP-04` — nâng cấp UX trình chỉnh ảnh (AnhModal), không story mới. NAP-04 ⚠️→⏳.
- **Vì sao:** user test tool phản ánh — (1) chưa xoay ảnh linh hoạt (mới kéo di chuyển/zoom), (2) chưa có khung chân dung mẫu để biết căn mặt, (3) đổi nền trắng chạy khá lâu.
- **Mới — Grab tự do 4 hướng:** nới `clamp` (giữ tối thiểu 1/4 ảnh trong khung) để kéo được cả trái/phải lẫn lên/xuống. Trước đây `clamp` ghim ảnh phủ kín khung nên ở zoom gốc một trục (rW=FW hoặc rH=FH) bị khóa → chỉ kéo được 1 chiều (user phản ánh). Vùng lộ khi kéo → nền trắng ở canvas.
- **Mới — Xoay ảnh:** nút **−90°/+90°** + thanh **tinh chỉnh độ nghiêng** (vài độ) để làm thẳng mặt. Xoay **client-side (canvas)** trước khi gửi backend crop; box tính trong hệ ảnh đã xoay.
- **Mới — Khung chân dung mẫu:** overlay mờ chồng lên khung crop (ô-van đầu + đường căn mắt/cằm) để operator biết đặt mặt. **Chỉ là hướng dẫn, KHÔNG dính vào ảnh `.jp2` xuất ra.**
- **Tăng tốc xóa phông (phương án A — user chốt):** bật **warm-up rembg lúc khởi động tool** = **bỏ `TOOL_SKIP_WARMUP=1` khỏi `tool-start.bat`**. Ảnh đầu chỉ chờ nạp model 1 lần lúc mở tool, ảnh sau <5s (TDD §9.2). **GIỮ model u2net** (không đổi chất lượng, không dùng model nhẹ). `TOOL_SKIP_WARMUP` vẫn giữ trong test (conftest) để khỏi tải model ~170MB khi chạy test.
- **Đã sửa:** PRD `NAP-04` (Steps + Done khi + hạ ⏳) · TDD §9.1 (xoay + khung mẫu) + §9.2 (không tắt warm-up) + Changelog 2.2.
- **Còn nợ:** code (tool/webui + tool-start.bat) — `/tieptheo` nhặt NAP-04 (⏳) code lại.
- **Code sẽ đụng:** `tool/webui/src/components/AnhModal.tsx` (state xoay + transform + overlay khung mẫu + xoay canvas trước khi gửi; cân nhắc gửi ảnh đã xoay thay vì chỉ box) · `tool-start.bat` (bỏ dòng `set TOOL_SKIP_WARMUP=1`). Backend `tool/app/image.py`/`routers/anh.py` nếu chọn truyền ảnh-đã-xoay (multipart) thay vì box — quyết lúc code.

## #19 — Tận dụng dữ liệu kéo về VPS (tự điền địa chỉ + nạp ảnh sẵn) · 02/10/2026

- **Mã:** `NAP-03`, `NAP-04` — tinh chỉnh hành vi ở luồng kéo-về (chế độ Nạp), không story mới.
- **Vì sao:** user test tool phản ánh — hồ sơ kéo từ VPS về đã có địa chỉ (`noi_tt_raw`) và ảnh thô, nhưng tool vẫn bắt **gõ lại** địa chỉ vào ô map và **chọn lại file ảnh** trong trình chỉnh. Lãng phí dữ liệu đã có. TDD §8.1 (map từ "địa chỉ text") + §9.1 ("Ảnh thô từ VPS → khung crop") vốn đã định hướng tận dụng — code chưa hiện thực đủ.
- **Mới — NAP-03:** chọn hồ sơ kéo về → tự tách `noi_tt_raw` ("…, Xã X, Huyện Y, Tỉnh Z") theo dấu phẩy + từ khóa (Tỉnh/TP→tỉnh, Quận/Huyện/Thị xã→huyện, Phường/Xã/Thị trấn→xã, phần dư→Chi tiết) → **điền sẵn** 3 ô map; operator bấm "Chuyển đổi sang xã mới". Tách là best-effort client (không gọi DB), **luôn cho sửa**; rỗng/không rõ → gõ tay như cũ. Giữ nguyên nút Chọn tay + map cốt lõi (đã verify 3321/3321).
- **Mới — NAP-04:** ảnh thô đã kéo về nạp **thẳng vào trình chỉnh** (AnhModal) làm ảnh crop ban đầu — căn 3:4 + đổi nền ngay, không bắt chọn lại file; vẫn cho chọn file khác để thay. `AnhModal` nhận **prop ảnh khởi tạo TÙY CHỌN** → QLY-05/QLY-06 (cũng dùng AnhModal) mở không-ảnh-sẵn vẫn chạy như cũ.
- **Đã sửa:** PRD `NAP-03`/`NAP-04` (Done khi + hạ trạng thái ⏳) · TDD §8.1 (bước tự tách) + §9.1 (nạp ảnh sẵn) + Changelog 2.1.
- **Còn nợ:** code (tool/webui) — `/tieptheo` sẽ nhặt NAP-03/NAP-04 (đang ⏳) để code lại phần này.
- **Code sẽ đụng:** `tool/webui/src/components/AddressCombo.tsx` (nhận địa chỉ gốc + điền sẵn + hàm tách) · `tool/webui/src/components/AnhModal.tsx` (nhận ảnh khởi tạo tùy chọn) · `tool/webui/src/pages/tool/NapHoSo.tsx` (truyền `noi_tt_raw` + ảnh đã tải vào 2 component).

## #18 — Quản lý tài khoản app web + 5 sửa UI · 02/10/2026

- **Mã:** `HTG-04` (SHOULD), `HTG-05` (MUST), `HTG-06` (MUST) — thêm vào nhóm HTG.
- **Vì sao:** chủ dự án cần tự vận hành tài khoản (tạo nhân viên, đổi mật khẩu) + lấy API key tool khỏi phải SSH; đồng thời phản ánh vài lỗi khung UI.
- **HTG-04 — Admin xem API key VPS:** endpoint `GET /api/admin/tool-key` (chỉ admin) + khối ở màn Tài khoản (che/Hiện/Sao chép). **Đánh đổi bảo mật đã ghi ở PRD** (khóa dùng chung, lộ phải xoay). Không đổi `require_tool_key`, không xoay key.
- **HTG-05 — Quản lý tài khoản nhân viên:** màn admin (danh sách + phân trang) · tạo (họ tên/username/vai trò/mật khẩu ban đầu) · reset mật khẩu · khóa/mở (`is_active`, **không xóa cứng** để giữ dấu vết PII). Chặn admin tự khóa mình. ("Buộc đổi mật khẩu lần đầu" — **bỏ** theo chủ dự án 02/10.)
- **HTG-06 — Tự đổi mật khẩu:** khối ở màn Tài khoản (mọi vai trò); kiểm mật khẩu hiện tại trước khi đổi.
- **5 sửa UI (polish, không phải story):**
  - UI-1 Header cố định, hết giật — khóa khung = chiều cao màn hình, chỉ pane cuộn (nguyên nhân cũ: `h-[100dvh]` nhảy theo thanh địa chỉ; desktop thiếu header).
  - UI-2 Khung desktop cao ổn định — bỏ co theo nội dung (`lg:h-auto` → chiều cao tối thiểu đầy viewport).
  - UI-3 Phân trang list 20/trang (app web `DaGui` server-side; tool list client-side), đổi cỡ 20/50/100.
  - UI-4 Tool giống app Windows — master–detail: list trái cuộn, panel info+ảnh phải **ghim**; màn hẹp xếp dọc.
  - UI-5 Kính lúp đè chữ hint (cả 2 app) — gốc: `.field-input` đặt `padding` ngoài `@layer` nên thắng tiện ích `pl-*` của Tailwind → padding trái bị bỏ. Fix: bọc class component vào `@layer components`.
- **Chạm story đã xong:** UI-3 thêm phân trang cho `THU-02` (✅) và `QLY-01` (⚠️); UI-1/2/5 chạm khung chung (`HTG-01`). Code sửa trong cùng đợt này → cập nhật trạng thái sau khi build xong, không để ✅ sai.
- **Đã code (02/10):** server HTG-04/05/06 (`admin.py` tool-key · `admin_users.py` list/reset/chặn tự khóa · `auth.py` đổi mật khẩu) + 13 test (server 82 pass); webapp (màn Tài khoản: đổi mật khẩu + API key admin + link quản lý · màn Quản lý tài khoản: list phân trang/tạo/reset/khóa) + route admin-only; UI-5 fix kính lúp (`@layer components`, cả 2 app).
- **UI đã xong (02/10):** UI-1/2 (`AppLayout`/`ToolLayout` 100svh, header/toolbar đứng yên, khung cao ổn định) · UI-3 (`PhanTrang` mỗi app; `DaGui` + lưới HV `TraCuuDB` + list Nạp) · UI-4 (`NapHoSo` ghim detail+ảnh theo màn hình, bỏ 720px cứng) · UI-5 (`@layer components`).
- **Đã deploy (02/10):** push `main` → CD build + deploy VPS; kiểm live: `/api/admin/tool-key` + `/api/auth/doi-mat-khau` trả 403 khi chưa đăng nhập (endpoint có, gác đúng). Chờ user verify trên giao diện.
- **Bỏ khỏi phạm vi (02/10):** "buộc đổi mật khẩu lần đầu" — chủ dự án không cần; không thêm cột `must_change_password`.

---

## #17 — QLY-01 lát 2: sửa hồ sơ thu hẹp còn nhân thân · 02/10/2026

- **Mã:** `QLY-01`. Không thêm/bớt story — thu hẹp phạm vi lát 2 cho an toàn dữ liệu (chủ dự án duyệt live 02/10).
- **Vì sao:** soi 3 SP sửa của app cũ trên DB thật trước khi code: `usp_NguoiLX_HoSo_Update` **ghi đè toàn bộ 65 cột** của `NguoiLX_HoSo` (gồm kết quả thi lý thuyết/hình/đường, liên kết BC1/BC2, đường dẫn ảnh), mà SP đọc-để-sửa `usp_NguoiLX_HoSo_Get_Sua_HS` **chỉ trả một phần** → nếu tool đụng bảng hồ sơ mà truyền thiếu/sai một cột là **xóa trắng kết quả thi của HV thật** trên prod.
- **Chốt phạm vi:** QLY-01 lát 2 **chỉ sửa thông tin nhân thân** (bảng `NguoiLX`): họ tên, ngày sinh, giới tính, số căn cước, địa chỉ thường trú (chi tiết). Tất cả nằm ở `NguoiLX` → qua **1 SP `usp_NguoiLX_Update`**, KHÔNG đụng `NguoiLX_HoSo`.
  - Ảnh → `QLY-05` (nạp/thay ảnh). Đổi khóa → `QLY-02`. Kết quả thi/báo cáo → do app cũ quản, tool không sửa.
- **Ghi an toàn:** `usp_NguoiLX_Update` cũng ghi đè 22 cột → trước khi ghi, **đọc lại full bản ghi `NguoiLX` hiện tại** rồi chỉ chồng 5 trường user sửa (giữ nguyên quốc tịch, nơi cấp CCCD, ghi chú, mã DVHC, người/ngày tạo, nơi cư trú...). Đọc + ghi trong 1 kết nối.
- **BR-012:** khóa đã lập BC1 → UI chỉ cho xem (không hiện nút Sửa); backend kiểm lại khi ghi → 409.
- **Đã làm:** API `GET /local/ho-so/chi-tiet` + `POST /local/ho-so/sua` (`tool/app/routers/hoso.py`) · UI nút Sửa + form nhân thân trong modal Tra cứu DB (`TraCuuDB.tsx`) · tool **101 pytest** + webui **19 vitest** + build sạch.
- **Chờ verify prod (bạn chạy):** sửa 1 HV thật ở khóa chưa BC1 → mở app cũ đối chiếu đúng · thử khóa đã BC1 → không sửa được.
- **Không đụng:** `usp_NguoiLX_HoSo_Update`, bảng `NguoiLX_HoSo`, ảnh, schema, server/app web.

---

## #16 — Kiểm DB thật chốt thiết kế QLY-06 (nạp khác khóa/khác hạng) · 01/10/2026

- **Mã:** `QLY-06`. Không đổi phạm vi — chỉ kiểm DB thật (chỉ đọc) để gỡ ẩn số, chốt thiết kế.
- **Vì sao:** QLY-06 còn nợ: SP `usp_QuangLA_PM4_ThuNhanHS_ThemMoiCapNhat` khi nạp người đã có trong DB thì **tái dùng bản ghi người cũ** hay **tạo người trùng**? (quyết định cả giải pháp).
- **Đã chạy (qua kết nối tool, chỉ đọc):**
  - **Q1 `sp_helptext`:** nhánh `IF @p_MaDK IS NULL` → `@v_MaDK = dbo.CreateNewMaDK(...)` → **INSERT NguoiLX mới** + INSERT NguoiLX_HoSo + NguoiLXHS_GiayTo. Nhánh có `@p_MaDK` → UPDATE 3 bảng. Câu kiểm `-2` trùng CMT dùng `lx.MaDK <> @p_MaDK` nên **khi nạp mới (`@p_MaDK=NULL`) không bắt trùng** (khớp bẫy đã biết — giữ check server-side).
  - **Q2 dữ liệu:** ≥20 HV có >1 khóa (nhiều người 5–8 khóa), mỗi khóa 1 hồ sơ, **chung SoCMT**.
- **Kết luận:** mô hình = **mỗi đăng ký 1 dòng NguoiLX + NguoiLX_HoSo, MaDK riêng, chung SoCMT**; nhiều dòng cùng SoCMT là **đúng thiết kế**, không phải trùng. → Nạp khác khóa/khác hạng = **nạp mới bình thường** (tạo MaDK mới), KHÔNG cần bước nối người cũ. QLY-06 chỉ cần thao tác tool "từ HV đã có → mở hồ sơ khóa mới" (điền sẵn + nạp mới). **Gỡ 📝 Draft → ⏳ Todo.**
- **Đã sửa:** PRD `QLY-06` (căn cứ DB + Done khi + gỡ Draft) · BUILD-PLAN (thêm task, bỏ khỏi Chờ chốt).
- **Không đụng:** DB (chỉ đọc, không ghi) · server · code · schema.

---

## #15 — Ảnh app web: 2 nút chụp/chọn-từ-máy + phóng to popup · 01/10/2026

- **Mã:** `THU-02`. Sửa UX phần ảnh, không thêm story. UI thuần client.
- **Vì sao:** chủ dự án hỏi — màn ảnh đang ép `capture="user"` nên điện thoại chỉ mở camera, **không chọn được ảnh có sẵn trong máy/thư viện**; và ảnh chân dung ở chi tiết hiện nhỏ (~80px), **bấm không phóng to được**.
- **Chốt (bộ chọn):**
  1. **2 nút nguồn ảnh:** "Chụp ảnh" (giữ `capture` → camera trực tiếp) và "Chọn từ máy" (bỏ `capture` → file/thư viện). Áp ở **màn chụp ảnh (Quet/ChupAnhGui)** + **đổi ảnh hồ sơ Chờ nạp (DaGui/ChiTiet)**. Chủ dự án chọn mở cả 2 lối (không ép camera cứng).
  2. **Phóng to ảnh:** bấm ảnh chân dung ở chi tiết → **AnhLightbox** mở toàn màn, bấm ngoài đóng.
- **Kỹ thuật:** thuần client `Quet.tsx` + `DaGui.tsx` (component `AnhLightbox` tái dùng `taiAnhCuaToi`). Không thêm endpoint, không đụng server/schema. Test webapp 24 pass, typecheck + build sạch.
- **Không đụng:** server, schema, tool, luồng nạp.

---

## #14 — Redesign UX nhập liệu app web (impeccable) · 01/10/2026

- **Mã:** `THU-01`, `THU-02`. Sửa giao diện/luồng nhập, không thêm story.
- **Vì sao:** test thật, chủ dự án thấy màn nhập liệu desktop chưa thân thiện cho nhập tay: ô CMND cũ ít dùng gây rối, ô ngày khó nhập, 2 nút xếp dọc dễ bấm nhầm, thiếu phím tắt.
- **Chốt (hỏi bộ chọn):**
  1. **Ẩn ô "Số CMND cũ"** — vẫn tự lưu CMND cũ từ QR nếu có (không mất dữ liệu, tool nạp vẫn dùng). Không bỏ cột DB/field gửi.
  2. **Ô ngày** (ngày sinh, ngày cấp) — **gõ tay dd/mm/yyyy + nút lịch** bấm chọn; vẫn nhập được **năm-only** (CCCD có HV chỉ có năm sinh → yyyy0000).
  3. **Desktop:** tách vị trí 2 nút ("Tiếp tục — chụp ảnh" vs "Lưu & nhập hồ sơ tiếp") tránh bấm nhầm + bố cục form thân thiện nhập tay + **phím tắt** (Enter/Ctrl+Enter, autofocus, tab order).
  4. **Content/anti-slop:** rà chữ hiển thị tự nhiên, không lộ mã story (đã bỏ "(HTG-01)" ở màn đăng nhập).
  5. **Cảnh báo trùng (THU-04):** giữ hiển thị **tên đầy đủ** người gửi (chủ dự án chốt NV xem được của nhau).
- **Hệ quả trạng thái:** `THU-01`/`THU-02` đang ⏳ (từ #13) — giữ ⏳, gộp phần này vào cùng đợt code.
- **Kỹ thuật:** thuần client webapp (`Quet.tsx` + component ô ngày tái dùng; `DaGui.tsx` ô ngày sửa). Không đụng server/schema (CMND cũ vẫn gửi như cũ; cột DB giữ nguyên).
- **Đã sửa:** PRD THU-01/THU-02 (AC UX) + Changelog v2.7 · TDD §6.6 (ghi UX) · SCREENS lượt 11.
- **Đã code (01/10, deployed):** `ODate.tsx` (ô ngày: gõ tay + nút lịch `showPicker` + **auto-mask tự chèn "/"** khi gõ số, giữ năm-only) dùng ở `Quet.tsx` + `DaGui.tsx`; ẩn ô CMND cũ (giữ giá trị QR); desktop form 2 cột + 2 nút tách hai bên + phím tắt (autofocus/Enter/Ctrl+Enter); +icon calendar/edit/chevronLeft. Verify Playwright 1440+375. Test webapp 24 (+4 maskNgay). impeccable detect sạch (trừ góc khung ngắm camera — cố ý).
- **Không đụng:** server, schema, tool, luồng nạp.

---

## #13 — App web: nhập liên tiếp + badge thiếu ảnh + cảnh báo trùng + (Draft) nạp khác khóa · 01/10/2026

- **Mã:** `THU-01`, `THU-02` (sửa) · `THU-04` (thêm, SHOULD) · `QLY-06` (thêm, 📝 Draft — còn nợ kiểm DB).
- **Vì sao:** chủ dự án test thật nêu 4 ý — (1) nhập liên tiếp không muốn bắt chụp ảnh từng hồ sơ; (2) cần đánh dấu + gom hồ sơ thiếu ảnh để chụp bù; (3) app web nhập chưa cảnh báo trùng căn cước; (4) muốn nạp lại cùng học viên vào khóa khác, khác hạng.
- **Chốt (hỏi từng câu, user duyệt):**
  1. **Lưu & nhập hồ sơ tiếp** (THU-01/THU-02): màn preview (dùng cho cả quét QR lẫn nhập tay) thêm nút **"Lưu & nhập hồ sơ tiếp"** → gửi **không kèm ảnh** → **toast "Đã gửi ✓"** (bỏ màn kết quả) → về màn chọn cách nhập. *Phương án A* (toast) đã chọn, loại B (giữ màn kết quả).
  2. **Badge "Thiếu ảnh" + bộ lọc** (THU-02): "Hồ sơ đã gửi" hiện badge cho hồ sơ chưa ảnh + bộ lọc gom hồ sơ thiếu ảnh; chụp bù qua nút "Thêm ảnh" (Chờ nạp) đã có.
  3. **Cảnh báo trùng CCCD app web** (THU-04, SHOULD): app hỏi VPS xem CCCD đã có hồ sơ `pending`/`importing` trong hàng đợi CSDT chưa → **cảnh báo mềm, vẫn cho gửi** (*phương án A*, loại B chặn cứng / C giữ nguyên). Phạm vi: cả hàng đợi CSDT (mọi nhân viên). App web **không** soi DB thật — chốt trùng thật vẫn ở NAP-06.
  4. **Nạp khác khóa/khác hạng** (QLY-06, 📝 Draft): phạm vi **cấp mới khác hạng song song** (có B thêm A1), *loại nâng hạng* (B→C/D/E — ngoài MVP). **Còn nợ kiểm DB thật** (chưa chốt thiết kế): SP tái dùng người cũ hay tạo người trùng.
- **Hệ quả trạng thái:** `THU-01` & `THU-02` đang ✅ → **hạ ⏳ Todo** (đổi giao diện màn đã dựng). `THU-04` ⏳ Todo. `QLY-06` 📝 Draft.
- **Kỹ thuật:** #1 + #2 **thuần client webapp**, không thêm endpoint. #3 thêm **1 endpoint** `GET /api/ho-so/kiem-trung?cccd=` (collector, đếm hàng đợi, loại chính uuid). Không đụng schema/tool/luồng nạp.
- **Đã sửa:** PRD THU-01/THU-02 (Done khi + hạ ⏳) + THU-04 + QLY-06 + Changelog v2.6 · TDD §4.3 (endpoint kiểm-trùng) + §6.1 (nhánh preview) + §6.6 (mới) + Changelog v2.2.
- **Đã code (01/10, chưa deploy):** server `GET /api/ho-so/kiem-trung` (THU-04, +5 test → server 67 pass) · `webapp/api.ts` `kiemTrungCccd` · `Quet.tsx` nút "Lưu & nhập hồ sơ tiếp" + toast + banner cảnh báo trùng (Preview) · `DaGui.tsx` badge "Thiếu ảnh" + bộ lọc. Typecheck + build + webapp 20 test pass.
- **Còn nợ:** deploy (push → CD) để test trực quan trên máy thật · `/reviewtdd` (TDD §4.3 thêm endpoint) · `/kehoach` bổ sung (task rework THU-01/02 + task THU-04) · review giao diện trước khi đặt story ✅ · **QLY-06: chạy 2 query kiểm DB ở máy CSDT trước khi thiết kế chi tiết**.
- **Không đụng:** schema DB/VPS · luồng nạp · tool (trừ QLY-06 sau khi chốt).

---

## #12 — Sửa UX app web sau test điện thoại thật (THU-01/THU-02) · 01/10/2026

- **Mã:** `THU-01`, `THU-02`. Sửa giao diện/luồng, không thêm story mới.
- **Vì sao:** deploy app web lên VPS (`nhaphocvien.trungtamthanhdat.com`) test trên điện thoại thật, chủ dự án thấy 6 điểm UX chưa tốt. Wireframe đã duyệt trước khi ghi sổ.
- **Chốt (6 điểm):**
  1. **Màn vào không tự mở camera** (THU-01) — cho chọn **Quét QR / Nhập tay / Tải ảnh CCCD**; camera chỉ bật khi bấm Quét.
  2. **Header logo không phải nút** (AppLayout) — bỏ nền/bo dáng nút để không nhầm là camera.
  3. **Hiện ảnh thật** (THU-02) — thumbnail ở list + chi tiết "đã gửi" thay icon xám; cần endpoint collector tải ảnh của mình.
  4. **Xem/sửa/chụp lại** (THU-02) — bấm hồ sơ đã gửi → chi tiết; còn **Chờ nạp** cho Sửa thông tin + Chụp/đổi ảnh; **Đang/Đã nạp** chỉ xem.
  5. **Layout mobile dính đáy** (THU-01/AppLayout) — `100dvh` + khung camera co giãn + bottom-nav & nút chính dính đáy, không cuộn mới thấy.
  6. **Khung bám QR** (THU-01) — dùng 4 góc `cornerPoints` của BarcodeDetector vẽ khung khóa theo mã, thay khung xanh tĩnh.
- **Hệ quả trạng thái:** `THU-01` & `THU-02` đang ✅ → **hạ ⏳ Todo** (đổi giao diện). Code quét/parse/gửi/offline/ô tìm cũ vẫn đúng, chỉ dựng lại phần vào + xem lại + ảnh.
- **Kỹ thuật:** thêm **1 endpoint** `GET /api/ho-so/:uuid/anh` (collector, kiểm `created_by` chống IDOR). Sửa/đổi ảnh dùng `PUT /api/ho-so/:uuid` + `POST .../anh` (server đã cho khi `pending`). Khung bám QR dùng `cornerPoints` (fallback qr-scanner không có → khung tĩnh).
- **Đã sửa:** PRD `THU-01`/`THU-02` (Done + Steps + Edge + hạ ⏳) + Changelog v2.5 · TDD §4.3 (endpoint) + §6.5 (mới) + Changelog v2.1 · SCREENS.md (3 quyết định UX lượt 9).
- **Còn nợ:** code webapp (Quet.tsx, DaGui.tsx, AppLayout.tsx, api.ts) + server (`GET .../anh` collector + test) · `/kehoach` bổ sung task rework (task 18/19 đã [x]) · cập nhật prototype ui-demo nếu muốn.
- **Không đụng:** schema DB/VPS · tool · luồng nạp.

---

## #11 — "Kéo về từ VPS" làm tươi hồ sơ chưa nạp (NAP-01) · 01/10/2026

- **Mã:** `NAP-01`. Thêm 1 tiêu chí "Done khi" + 1 edge case trong story có sẵn, không thêm story mới.
- **Vì sao:** Động tác kéo **không khóa** hồ sơ (khóa chỉ ở bước nạp, 15'). Nên sau khi tool đã kéo về, người thu nhận vẫn sửa được thông tin/ảnh trên app web (hồ sơ còn `pending`) → bản trong tool thành cũ mà tool **không biết**. Trước đó tool kéo lại chống trùng theo uuid (`INSERT OR IGNORE`) → **không** làm tươi bản đã kéo.
- **Chốt (phương án A — mức nhẹ):** bấm "Kéo về từ VPS" lần nữa **cập nhật lại** thông tin/ảnh mới nhất từ VPS cho các bản `keo_ve` còn trạng thái cục bộ `cho`; **giữ nguyên** bản `xong`/`loi`. Báo số hồ sơ vừa làm tươi. KHÔNG khóa-khi-kéo (đã cân nhắc "mức chặt": khóa ngay khi kéo + app web báo "đang xử lý" — loại vì nặng, dễ kẹt lô lớn, job 15' lật ngược khi kéo mà chưa nạp).
- **Hệ quả trạng thái:** `NAP-01` đang ✅ Done (phiên này) → **hạ ⏳ Todo** (yêu cầu thêm). Code ①+② cũ vẫn đúng, chỉ bổ sung làm tươi.
- **Kỹ thuật:** đổi `tool/app/nap.py` `keo_ve_upsert` từ `INSERT OR IGNORE` → UPSERT cập nhật bản `cho` (giữ `xong`/`loi` + local status), trả số bản làm tươi; `routers/nap.py` `keo_hang_doi` báo thêm số làm tươi. Không đụng VPS/app web.
- **Đã sửa:** PRD `NAP-01` (Done khi + Edge) · TDD §7.2 + Changelog v2.0.
- **Đã code (01/10):** `keo_ve_upsert` UPSERT bản `cho` trả `(mới, làm tươi)`; `keo_hang_doi` báo `lam_tuoi`; `NapHoSo.tsx` hiện "Đã kéo N mới · làm tươi M". Test tool 72 pass (+2: làm tươi bản `cho`, không đụng `xong`). NAP-01 ✅ lại — gọn trong task 20, không cần `/kehoach` bổ sung.
- **Không đụng:** schema VPS/DB · app web · server.

---

## #10 — Thêm tìm kiếm (tên không dấu + CCCD) ở tool & app web · 01/10/2026

- **Mã:** `THU-02`, `NAP-01`, `QLY-01`. Thêm tính năng trong màn có sẵn, không thêm story mới.
- **Vì sao:** Chủ dự án muốn tra nhanh học viên bằng tên (gõ không dấu cũng ra) hoặc số CCCD, ở cả tool lẫn app web. Trước đó: app web chỉ lọc theo trạng thái (không tìm); tool list tải về chưa có ô tìm; QLY-01 có tìm tên/CCCD nhưng chưa nêu "khớp không dấu".
- **Chốt (phương án A, đổi từ B):** ô tìm ở **3 chỗ** — (1) app web `Hồ sơ đã gửi`, (2) tool `list tải về` (chế độ Nạp hồ sơ), (3) tool `lưới khóa` (Tra cứu DB). Khớp theo **tên (chuẩn hóa bỏ dấu cả hai vế) hoặc số CCCD**. UX: ô tìm **đầu danh sách/lưới**; **màn hẹp thu gọn thành nút kính lúp** (bấm mới bung).
  - *Diễn biến:* hỏi phạm vi → chủ dự án chốt **B** (chỉ tool) → đổi ý ngay sau đó sang **A** (cả app web). Theo A.
- **Hệ quả trạng thái:** `THU-02` đang ✅ → **hạ ⏳ Todo** (yêu cầu đổi, phải thêm ô tìm; code gửi cũ vẫn đúng nhưng story quay lại hàng đợi). `NAP-01`, `QLY-01` đang ⏳ → chỉ thêm AC.
- **Kỹ thuật:** app web + tool list tải về lọc **phía client** trên dữ liệu đã tải (không thêm endpoint); QLY-01 lưới khóa tìm qua SP `usp_NguoiLX_HoSo_Search` (collation không phân biệt dấu hoặc chuẩn hóa tương tự). Bỏ dấu = normalize NFD + xóa dấu kết hợp.
- **Đã sửa:** PRD `THU-02`/`NAP-01`/`QLY-01` (Done khi + hạ trạng thái THU-02) · TDD §6.4 (mới) + §11.1 (note tìm) · `SCREENS.md` (quyết định UX lượt 7).
- **Còn nợ:** code 3 ô tìm (THU-02 app web, NAP-01 tool, QLY-01 tool) · cập nhật prototype ui-demo cho 3 màn (hoặc dựng trong lúc build màn thật).
- **Không đụng:** schema DB/VPS (tìm client-side hoặc qua SP sẵn có) · BUILD-PLAN số task (THU-02 task 19, NAP-01 task 20, QLY-01 task 22 — chỉ thêm việc trong task, `/kehoach` bổ sung nếu muốn ghi rõ).

---

## #9 — Bỏ ô nhập nơi cư trú khác ở app thu nhận (THU-02) · 01/10/2026

- **Mã:** `THU-02`. Đổi quy tắc nghiệp vụ nhỏ (bớt một ô nhập), không thêm/bỏ story.
- **Vì sao:** Bảng `ho_so_thu_thap` trên VPS không có cột nơi cư trú (`HoSoIn`/model chỉ có `noi_tt_raw`), và tool khi nạp tự lấy cư trú = thường trú (BR-004 / TDD §8.1). App cho nhập cư trú khác thì dữ liệu đó không gửi đi đâu được, âm thầm mất. Nghiệp vụ học viên lái xe gần như luôn khai một địa chỉ.
- **Chốt (phương án A):** app chỉ thu **nơi thường trú** (lấy từ QR, cho sửa); không có ô cư trú. Cư trú để tool mặc định = thường trú khi nạp. Không đổi schema VPS, không sửa server, không sửa luồng tool.
- **Đã loại (B):** thêm cột `noi_cu_tru` vào bảng + `HoSoIn` + luồng tool — đúng PRD cũ nhưng phải `down -v` đổi schema + sửa server + NAP-05 cho một ô gần như không dùng.
- **Đã sửa:** PRD `THU-02` Done-khi (bỏ "nút bỏ tick để nhập khác"). Prototype `ui-demo/src/pages/app/Quet.tsx` (gỡ checkbox cư trú). **TDD không đổi** — §8.1 + field map đã ghi `NoiCT = NoiTT mặc định` sẵn.
- **Không đụng:** server (schema/endpoint giữ nguyên) · BUILD-PLAN (THU-02 vẫn task 19) · code THU-01 (đã không có ô cư trú).

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

- **Cập nhật:** 05/10/2026 (#37 mở rộng trường sửa nhân thân TCB-03: +địa chỉ 2 cấp + ngày/nơi cấp CCCD, chỉ TCB, hạ TCB-03 ✅→⏳ — **chỉ sửa tiêu chí story có sẵn, không thêm/bớt mã**. Trước đó: #36 sửa định nghĩa DKKH = gói DANG_KY_KHOA_HOC gửi Sở (không phải SoQD) + TCB-04 nâng ngưỡng chặn DKKH + SYNC-01 filter/sort/giữ phiên F5. #35 +Feature "Tra cứu CDB đích" 4 story `TCB-01..04`)
- **Cập nhật trước:** 04/10/2026 (#34 +story `HTG-07` cấu hình kết nối lên header dùng chung; hạ `SYNC-01`+`SYNC-02` ✅→⏳ làm lại UI (nay đã ✅ lại); sửa bullet `HTG-01`)
- **Trước nữa:** 04/10/2026 (#33 +Feature "Đồng bộ CDB" 3 story `SYNC-01/02/03` SHOULD, port sync_tool v2.0 + tool chuyển sidebar module)
- **Trước đó:** 04/10/2026 (#32 bổ sung tiêu chí NAP-01 + QLY-05; ⚠️ #31 có dòng bảng nhưng THIẾU mục chi tiết — cần phiên #31 bổ sung) · 03/10/2026 (gộp 2 phiên song song: #28 QLY-09 + #29 NAP-01/03 + #30 THU-01/05; THU-01 hạ ✅→⏳)
- **Số story trong PRD:** 33 (32 MUST/SHOULD gồm `HTG-07` + `THU-04` SHOULD + `THU-05` + `HTG-04` SHOULD + `QLY-06` ⏳ + `QLY-07` + `QLY-08` + `QLY-09` + `SYNC-01/02/03` + `TCB-01/02/03/04` SHOULD; chưa tính NICE `QLY-04`, `THU-03`)
- **Mã story hiện có:** `HTG-01`…`HTG-07`, `THU-01`, `THU-02`, `THU-04`, `THU-05`, `NAP-01`…`NAP-06`, `KHO-01`, `QLY-01`, `QLY-02`, `QLY-03`, `QLY-05`, `QLY-06`, `QLY-07`, `QLY-08`, `QLY-09`, `SYNC-01`, `SYNC-02`, `SYNC-03`, `TCB-01`, `TCB-02`, `TCB-03`, `TCB-04` (NICE: `QLY-04`, `THU-03`)
- **Mã đã nghỉ hưu:** (chưa có)
