# Sổ bug

> File do `/suabug` ghi. Khác `CHANGES.md`: file kia ghi **thay đổi yêu cầu**, file này ghi **code không làm đúng yêu cầu đã có**.

| # | Ngày | Mức | Story | Bug | Trạng thái | Deploy |
|---|---|---|---|---|---|---|
| 12 | 03/10/2026 | 🟡 Nên sửa | `QLY-03` | **Xóa hẳn HV ở DB nhưng tab "Đã nạp" vẫn hiện.** `/xoa` (QLY-03) gỡ khỏi CSDT nhưng KHÔNG dọn dòng staging `'xong'` → "Đã nạp" (lọc keo_ve 'xong') còn hiện HV đã xóa. Sửa: sau `_xoa_hv_csdt` → `keo_ve_xoa(lay_uuid_theo_ma_dk(ma_dk))` (bỏ hẳn dòng staging, chỉ SQLite local; xóa hẳn ≠ gỡ nên KHÔNG về 'cho'). Frontend đã tự tải lại keoVe khi về tab Nạp (effect BUG-03). | ✅ Đã sửa | ⬜ (chờ chạy lại tool) |
| 11 | 03/10/2026 | 🔴 Chặn | `QLY-01` | **Lưới học viên lặp dòng nhiều lần** (regression từ BUG-10): query chi tiết lưới thêm 3 `LEFT JOIN` (DM_DonViGTVT + DM_DVHC cho TT/CT) để lấy tên; nhưng `DM_DVHC.MaDvhc` KHÔNG duy nhất → join **nhân dòng** HV (khóa 6 HV hiện 12+). Sửa: đổi 3 JOIN → **scalar subquery `TOP 1`** (lấy đúng 1 tên, không nhân dòng). Verify khóa 6 HV: 12→6. | ✅ Đã sửa | ⬜ (chờ chạy lại tool) |
| 10 | 03/10/2026 | 🟠 Nặng | `NAP-05` · `QLY-01` | **Nơi cấp căn cước rỗng + popup thiếu trường.** QR không mang nơi cấp → nạp để `NoiCapCMT` RỖNG (Lê Thị Hồng rỗng). Sửa: nạp **tự suy mã Sở GTVT từ số CCCD** (`cccd[2:3]`, vd `070…`→`70` Bình Phước; `NoiCapCMT`=mã đơn vị GTVT `DM_DonViGTVT` LoaiDV='SO', khớp 63/63) + **vá 6 bản ghi cũ** rỗng (chỉ CCCD 12 số hợp lệ). Popup "Chi tiết học viên" (tool) thêm **Ngày cấp · Nơi cấp (tên tỉnh) · Địa chỉ cư trú** + địa chỉ đầy đủ (join DM_DVHC). **Combobox "Nơi cấp" ở form nạp** (danh sách Sở GTVT, mặc định suy từ CCCD, operator sửa khi lệch) — endpoint `/local/dvhc/so-gtvt`. +2 test | ✅ Đã sửa | ⬜ (chờ chạy lại tool) |
| 9 | 03/10/2026 | 🟠 Nặng | `NAP-05` · `QLY-02` | **Số hồ sơ lệch** (ca Lê Thị Hồng): nạp→gỡ→nạp lại → khóa 57 HV mà SoHoSo = 58. Gốc: sinh SoHoSo = **MAX(SoHoSo)+1**; lúc "gỡ về chờ nạp" `usp_NguoiLX_Delete` xóa cứng số nhưng MAX+1 KHÔNG thu hồi → nếu có HV khác chen/phantom thì MAX trèo quá số HV thực. Sửa: đổi sang **số nhỏ nhất CHƯA dùng** (lấp khe, khớp số lượng, tái dùng số đã gỡ) ở cả nạp mới (`nap.py`) + đổi khóa (`hoso.py`); +2 test | ✅ Đã sửa | ⬜ (chờ chạy lại tool) |
| 8 | 03/10/2026 | 🟡 Nên sửa | `THU-05` | Màn "Hồ sơ đã gửi" desktop: sau khi fix cuộn ngang (BUG-05, `table-fixed`), cột **Họ tên** chỉ còn phần dư ~136px (các cột phụ ăn hết 756px) → **tên dài bị cắt "…"** — cột định danh quan trọng nhất lại hẹp nhất (nghịch đảo ưu tiên). Sửa (plan A): Họ tên width rộng cố định `w-[220px]`, **Nơi thường trú** thành cột nhường (bỏ width → co giãn + truncate, chi tiết ở modal), thu Giới tính/Ngày sinh. Build + 24 vitest | ✅ Đã sửa | ⬜ (chờ deploy webapp) |
| 7 | 03/10/2026 | 🟠 Nặng | `NAP-03` | **Ca Lê Thị Hồng:** địa chỉ 2 cấp KHÔNG tiền tố + chi tiết đầu "Thôn 2, Trấn Biên, Đồng Nai" → `tachDiaChiGoc` tưởng 3 cấp cũ (xã=**Thôn 2**, huyện=**Trấn Biên**) → map trượt, vì "Trấn Biên" thực ra là **xã mới** (mã 26041) còn "Thôn 2" là thôn. Sửa: tách chi tiết đầu chuỗi (số nhà/thôn/ấp…) TRƯỚC khi suy vị trí → còn 2 phần "Trấn Biên, Đồng Nai" = xã mới + tỉnh → khớp. Xác nhận bằng dvhc_map.sqlite thật + sim pipeline; +5 test (34 vitest). (BUG-06 lo ca CÓ tiền tố; BUG-07 lo ca KHÔNG tiền tố) | ✅ Đã sửa | ⬜ (chờ chạy lại tool) |
| 6 | 03/10/2026 | 🟠 Nặng | `NAP-03` | Địa chỉ 2 cấp mới "Phường X, <Tỉnh không tiền tố>" (vd "Phường Hồng Hà, Hà Nội") → `tachDiaChiGoc` nuốt tỉnh vào chiTiet (tinh="") → tool map KHÔNG RA. "Hồng Hà, Hà Nội" (không tiền tố) lại OK. Sửa: thêm cứu TỈNH từ phần dư (đoạn cuối = tỉnh) khi xã/huyện đã khớp tiền tố mà tinh rỗng; +4 test (33 vitest) | ✅ Đã sửa | ⬜ (chờ chạy lại tool) |
| 5 | 03/10/2026 | 🟠 Nặng | `THU-05` | Màn "Hồ sơ đã gửi" (app web desktop): cột ô tích chọn-nhiều (CHANGES #30) làm bảng vượt khung → che cột phải. Sửa (chốt cuối, user: KHÔNG cuộn ngang): `table-fixed` + cột định width + `truncate` → bảng luôn vừa khung, chữ dài hiện "…", chi tiết xem ở modal (bỏ `overflow-x-auto`) | ✅ Đã sửa | ⬜ (chờ deploy webapp) |
| 4 | 03/10/2026 | 🟠 Nặng | `NAP-01` · `NAP-03` | Collector sửa địa chỉ (2 cấp mới) trên app; kéo về tool lại nạp địa chỉ CŨ đã map — nháp địa chỉ không làm tươi theo raw mới | ✅ Đã sửa | ⬜ (tool chưa lên VPS — có hiệu lực khi chạy lại tool) |
| 3 | 03/10/2026 | 🟠 Nặng | `QLY-08` · `NAP-01` | Gỡ HV về chờ nạp xong, màn Nạp không tự hiện lại ở "chờ nạp" — phải bấm "Kéo từ VPS" | ✅ Đã sửa | ⬜ (tool chưa lên VPS — có hiệu lực khi chạy lại tool) |
| 2 | 03/10/2026 | 🟠 Nặng | `QLY-01` · `NAP-01` | Tra cứu DB ẩn mọi HV chưa ảnh (TT_XuLy='01') → "Xem trong DB" không thấy HV nạp không ảnh; bộ lọc "Chưa ảnh" luôn rỗng | ✅ Đã sửa | ⬜ (tool chưa lên VPS — có hiệu lực khi chạy lại tool) |
| 1 | 03/10/2026 | 🔴 Chặn | `QLY-08` | Gỡ về chờ nạp rồi nạp lại cùng uuid → HV KHÔNG vào DB nhưng tool báo thành công | ✅ Đã sửa | ⬜ (tool chưa lên VPS — có hiệu lực khi chạy lại tool) |

Chú thích trạng thái: ✅ Đã sửa · 🔄 Đang sửa · ⏳ Đã xếp task · ⬜ Chưa xử

---

## BUG-07 — Địa chỉ 2 cấp KHÔNG tiền tố + chi tiết đầu không auto-map (ca Lê Thị Hồng) · 03/10/2026

- **Mức:** 🟠 Nặng · **Story:** `NAP-03` · **File:** `tool/webui/src/lib/diachi.ts`
- **Tái hiện (ca thật Lê Thị Hồng, xác nhận bằng dvhc_map.sqlite + sim pipeline):** `noi_tt_raw = "Thôn 2, Trấn Biên, Đồng Nai"` → `tachDiaChiGoc` cho `xa="Thôn 2", huyện="Trấn Biên", tỉnh="Đồng Nai"` → "Chuyển đổi sang xã mới" báo **"Không khớp bảng ánh xạ"**.
- **Nguyên nhân:** chuỗi 3 phần KHÔNG tiền tố bị suy mặc định là **3 cấp cũ (xã-huyện-tỉnh)**, nhét "Thôn 2" (vốn là thôn/chi tiết) vào ô XÃ. Thực tế đây là **2 cấp + chi tiết**: "Thôn 2" = chi tiết, **"Trấn Biên" = xã mới** (DB: mã `26041`, Thành phố Đồng Nai), "Đồng Nai" = tỉnh. DB xác nhận "Thôn 2" không phải xã nào (0 dòng) nên map bằng "Thôn 2" luôn trượt.
- **Khác BUG-06:** BUG-06 lo ca có tiền tố ("Phường X, <tỉnh trần>"); ca này KHÔNG tiền tố nên đi nhánh suy-vị-trí, BUG-06 không chạm tới.
- **Cách sửa:** trong nhánh không-tiền-tố của `tachDiaChiGoc`, **tách "chi tiết" đầu chuỗi** (regex số nhà/thôn/ấp/khu/tổ/xóm/lô/kp hoặc bắt đầu bằng số) TRƯỚC khi suy vị trí trên phần địa danh còn lại. "Thôn 2" tách ra chi tiết → còn "Trấn Biên, Đồng Nai" (2 phần) = xã mới + tỉnh → khớp `26041`. Không gồm "đường/ngõ" trong từ khoá (tránh nhầm xã thật như "Đường Lâm"); địa chỉ phố thường có số nhà đầu nên đã bắt bằng `^\d`.
- **Kiểm:** tool webui build + typecheck · **34 vitest** (+5 ca BUG-07: Thôn/Số/số-nhà đầu + 2 ca giữ hành vi 3 cấp cũ không hồi quy). Sim tách+map trên DB thật: trước "không khớp", sau "khớp 26041".

## BUG-06 — Địa chỉ 2 cấp mới không auto-map ở tool (tỉnh không tiền tố) · 03/10/2026

- **Mức:** 🟠 Nặng (địa chỉ 2 cấp đúng vẫn báo "không khớp" → operator phải chọn tay) · **Story:** `NAP-03` · **File:** `tool/webui/src/lib/diachi.ts`
- **Tái hiện (xác nhận bằng data thật dvhc_map.sqlite):** địa chỉ dạng **"Phường Hồng Hà, Hà Nội"** (xã CÓ tiền tố "Phường", tỉnh KHÔNG tiền tố) → `tachDiaChiGoc` cho `tinh="", xa="Hồng Hà", chiTiet="Hà Nội"` → `tra_map` nhận tinh rỗng → **không khớp**. Nghịch lý: "Hồng Hà, Hà Nội" (không tiền tố) lại map OK.
- **Nguyên nhân:** khối cứu-theo-vị-trí trong `tachDiaChiGoc` **chỉ chạy khi KHÔNG field nào khớp tiền tố**. Khi xã đã khớp "Phường" nhưng tỉnh không tiền tố → tỉnh không được cứu, rơi vào `chiTiet`. Loại trừ nghi ngờ "bảng map thiếu data" (bảng đủ 34 tỉnh/10.602 dòng, map đúng khi tỉnh được tách đúng).
- **Ảnh hưởng:** tool máy Nạp, bước map địa chỉ (NAP-03) — mọi địa chỉ 2 cấp viết "Phường/Xã X, <Tỉnh trần>". Bước nạp/CSDL không sai; chỉ tốn công chọn tay.
- **Cách sửa:** thêm "Lượt 3a" trong `tachDiaChiGoc` — khi `tinh` rỗng mà xã/huyện đã khớp tiền tố, lấy **đoạn dư CUỐI cùng** làm tỉnh (thứ tự địa chỉ VN: tỉnh ở cuối), chạy TRƯỚC bước cứu xã. Đối xứng với "Lượt 3b" (cứu xã) sẵn có. Thuần client.
- **Kiểm:** tool webui build + typecheck · **33 vitest** (+4 ca BUG-06: "Phường X, <tỉnh trần>", có số nhà, giữ hành vi cũ khi cả 2 có tiền tố). Mô phỏng pipeline tách+map trên `dvhc_map.sqlite` thật: trước sửa "không khớp", sau sửa khớp.

## BUG-05 — Màn "Hồ sơ đã gửi" app web desktop che mất cột phải · 03/10/2026

- **Mức:** 🟠 Nặng (nội dung bị che, không xem được) · **Story:** `THU-05` · **File:** `webapp/src/pages/DaGui.tsx`
- **Tái hiện:** mở "Hồ sơ đã gửi" trên desktop (≥lg) — bảng bị cắt bên phải, không thấy đủ cột (Nơi thường trú / Ngày gửi / Trạng thái).
- **Nguyên nhân:** THU-05 (CHANGES #30) thêm **cột ô tích chọn-nhiều** → bảng thành 8 cột, tổng bề rộng vượt khung nội dung AppLayout (~940px, shell `max-w-[1180px]` trừ sidebar). Card bảng để `overflow-hidden` (có sẵn) → phần vượt bị **cắt cứng** thay vì cuộn.
- **Ảnh hưởng:** chỉ app web **desktop**, màn "Hồ sơ đã gửi". Mobile (card list) không ảnh hưởng.
- **Cách sửa (chốt cuối — user yêu cầu KHÔNG cuộn ngang):** `table` chuyển **`table-fixed`** + mỗi cột định width (Giới tính 90 · CCCD 128 · Ngày sinh 96 · Nơi TT 150 · Ngày gửi 140 · Trạng thái 112; Họ tên co giãn phần còn lại) + **`truncate`** ô dài (Họ tên/CCCD/Nơi TT/Ngày gửi, kèm `title` hover) + header `whitespace-nowrap`. Bảng **luôn bằng bề rộng khung** → card giữ `overflow-hidden`, **không cuộn ngang, không che**; chữ dài hiện "…", chi tiết đầy đủ ở modal khi bấm dòng. (Bản đầu dùng `overflow-x-auto` đã bỏ.)
- **Kiểm:** webapp build + typecheck sạch · 24 vitest. **Chưa chụp Playwright** (màn sau đăng nhập) — verify trực quan trên live sau deploy; width cột có thể nhích nếu nhìn thấy chật.

## BUG-04 — Kéo lại sau khi collector sửa địa chỉ vẫn nạp địa chỉ cũ · 03/10/2026

- **Mức:** 🟠 Nặng (nạp sai địa chỉ vào CSDT; đường vòng: operator map tay lại — nhưng không biết để làm)
- **Story:** `NAP-01` (kéo lại làm tươi) · `NAP-03` (map địa chỉ)
- **Ai báo:** chủ dự án (qua phiên pmcs-tlx-b7), ca Lê Thị Hồng
- **Tái hiện:** operator mở 1 HV ở màn Nạp (tạo nháp + map địa chỉ) → collector sửa địa chỉ sang 2 cấp mới trên app web → operator **"Kéo từ VPS"** → nạp HV đó → CSDT nhận **địa chỉ CŨ** (đã map), không phải địa chỉ mới.
- **Nguyên nhân gốc:** `noi_tt_raw` được làm tươi đúng ở staging + `keoVe` state, NHƯNG **nháp** (`nhap[uuid]` trong `NapHoSo.tsx`, giữ `diaChi` đã map + `chiTiet`) không bị đụng khi kéo lại: effect tự điền chặn bởi `if (nhap[selUuid]) return`, và `keoVeFromVps` chỉ `setKeoVe`, không reset nháp. Nháp map theo raw CŨ thành stale; `dungNapIn` nạp theo `nhap[uuid].diaChi` cũ.
- **Đã sửa:** `tool/webui/src/lib/diachi.ts` +hàm thuần `lamTuoiNhapDiaChi(nhap, rawCu, rowsMoi)` — raw của uuid đổi → reset `diaChi=null` (map lại) + điền lại `chiTiet` từ raw mới, GIỮ giấy tờ/ảnh. `tool/webui/src/pages/tool/NapHoSo.tsx` `keoVeFromVps` so raw cũ↔mới rồi gọi hàm trước `setKeoVe`.
- **Test hồi quy:** `tool/webui/src/lib/diachi.test.ts` — `lamTuoiNhapDiaChi (BUG-04)` 3 ca (raw đổi → reset + giữ giấy tờ · raw không đổi → giữ nguyên reference · chưa có nháp → bỏ qua). 32 vitest. *Fail nếu helper bị đưa về no-op (hành vi bug).*
- **Kiểm tay (frontend, chưa có hạ tầng test component):** mở HV map địa chỉ → sửa địa chỉ trên app web → "Kéo từ VPS" → mở lại HV: ô "Đã map" phải trống/đòi map lại theo địa chỉ mới, không giữ xã cũ.
- **Deploy:** tool cục bộ máy CSDT (chưa lên VPS) → hiệu lực khi chạy lại tool (dev server HMR đã nạp).

- **Mức:** 🟠 Nặng (có đường vòng: bấm "Kéo từ VPS"; nhưng sai luồng hằng ngày + dễ tưởng gỡ hỏng)
- **Story:** `QLY-08` (gỡ về chờ nạp) · `NAP-01` (danh sách chờ nạp)
- **Ai báo:** chủ dự án, khi gỡ HV ở Tra cứu DB rồi sang tab Nạp không thấy HV ở hàng chờ
- **Tái hiện:** Tra cứu DB → "Gỡ về chờ nạp" 1 HV (dòng còn trong hàng đợi) → sang tab "Nạp hồ sơ" → HV KHÔNG hiện ở "chờ nạp" cho tới khi bấm "Kéo từ VPS".
- **Nguyên nhân gốc:** `NapHoSo.tsx` tải danh sách chờ nạp (`getDanhSachKeoVe`) **chỉ 1 lần lúc mount** (`useEffect([])`). Thao tác "Gỡ về chờ nạp" nằm ở component `TraCuuDB` (tab Tra cứu) — gọi backend `keo_ve_ve_cho` đưa dòng staging về `'cho'` ĐÚNG, nhưng không chạm state `keoVe` của `NapHoSo`. Chuyển tab chỉ `setMode("nap")`, không tải lại → danh sách cũ. Dữ liệu đúng, chỉ UI không làm tươi.
- **Đã sửa:** `tool/webui/src/pages/tool/NapHoSo.tsx` — đổi effect tải danh sách sang phụ thuộc `[mode]`: khi `mode==='nap'` thì `getDanhSachKeoVe()` (gồm cả lần mở màn). Chỉ đọc SQLite cục bộ, không gọi VPS.
- **Test hồi quy:** KHÔNG viết được test tự động — dự án chưa có hạ tầng test React component (`@testing-library/react`/jsdom chưa cài; vitest chạy node env, chỉ test hàm thuần). Dựng cả bộ cho 1 effect là quá mức. **Bước kiểm tay:** mở tool → Tra cứu DB → "Gỡ về chờ nạp" 1 HV còn trong hàng đợi → bấm tab "Nạp hồ sơ" → HV phải hiện ngay ở nhóm "Cần xử lý" (badge chờ nạp) mà KHÔNG cần bấm "Kéo từ VPS". (Ngoại lệ: HV đã "Bỏ khỏi hàng đợi" trước đó vẫn cần Kéo — đúng thiết kế.)
- **Deploy:** tool chạy cục bộ máy CSDT (chưa lên VPS) → hiệu lực khi chạy lại tool (dev server đã nạp qua HMR).

---

## BUG-02 — Tra cứu DB ẩn học viên chưa có ảnh · 03/10/2026

- **Mức:** 🟠 Nặng (không mất dữ liệu, nhưng HV nạp-không-ảnh vô hình ở Tra cứu DB → không quản lý/thêm ảnh được; "Xem trong DB" không thấy HV vừa nạp)
- **Story:** `QLY-01` (lưới tra cứu) · `NAP-01` (nút "Xem trong DB", dòng 158) · liên quan `QLY-05` (lọc "Chưa ảnh")
- **Ai báo:** chủ dự án, khi nạp Lê Thị Hồng (không ảnh) rồi bấm "Xem trong DB" không thấy tên
- **Tái hiện:** nạp 1 HV KHÔNG ảnh vào khóa (BR-011, TT_XuLy='01') → Tra cứu DB mở khóa đó → HV không xuất hiện trong lưới. Thực chứng: khóa 70004K26B010 có 2 HV '01' + 55 HV '03'; endpoint cũ trả 55, bỏ 2.
- **Nguyên nhân gốc:** `ds_ho_so` (`tool/app/routers/hoso.py`, `GET /local/ho-so`) dùng SP app cũ `usp_NguoiLX_Select_By_MaKH`, SP lọc cứng `AND B.TT_XuLy IN ('03','04')` (`--BaBT them`, "phải nhận ảnh rồi"). HV chưa ảnh (TT_XuLy '01'/'02') bị loại ở nguồn → không thể hiện, và bộ lọc "Chưa ảnh" (QLY-05) không bao giờ có dữ liệu.
- **Đã sửa:** `ds_ho_so` thay EXEC SP bằng SELECT riêng (JOIN `NguoiLX`+`NguoiLX_HoSo`, `WHERE MaKhoaHoc=@ AND TrangThai=1`, **bỏ** điều kiện `TT_XuLy`, giữ nguyên shape trả về). **KHÔNG sửa SP cũ** (dùng chung app cũ → sửa là vỡ báo cáo cũ).
- **Test hồi quy:** `tool/tests/test_hoso.py` — `test_ds_ho_so_liet_ke_ca_hv_chua_anh` (HV DuongDanAnh rỗng vẫn trả về + endpoint KHÔNG gọi SP lọc ảnh + KHÔNG lọc TT_XuLy). Fail trên code cũ, pass trên code mới (168 pytest).
- **Kiểm thật (máy CSDT):** query mới trả 57 HV cho khóa 70004K26B010 (trước 55), có Lê Thị Hồng (MaDK `70004-20261003153838977`). Backend tool đã restart code mới.
- **Deploy:** tool chạy cục bộ máy CSDT (chưa lên VPS) → hiệu lực khi chạy lại tool (đã restart lúc sửa).

---

## BUG-01 — Gỡ về chờ nạp rồi nạp lại → học viên không vào DB · 03/10/2026

- **Mức:** 🔴 Chặn (mất dữ liệu: tool báo nạp thành công nhưng HV không có trong CSDT)
- **Story:** `QLY-08` (liên quan `NAP-01` nạp lô)
- **Ai báo:** chủ dự án, khi test tool trên máy CSDT (nạp Lê Thị Hồng vào khóa 70004K26B010, không thấy trong DB)
- **Tái hiện:** Nạp 1 HV → "Gỡ về chờ nạp" (QLY-08) → "Kéo về từ VPS" → chuẩn bị → "Nạp" lại cùng HV. Tool báo "đã nạp" với số hồ sơ cũ, nhưng tra DB theo CCCD/MaDK → **rỗng**.
- **Nguyên nhân gốc:** `nap.keo_ve_ve_cho()` (QLY-08 bước 5) reset dòng `keo_ve` về `'cho'` nhưng **không xóa vé idempotency trong bảng `nap_xong`** (uuid→MaDK). Vé này do lần nạp đầu tạo ra để chống bấm nạp 2 lần. Khi gỡ về chờ nạp, HV đã bị xóa khỏi CSDT nên vé cũ trỏ tới MaDK đã chết. Lần nạp lại, `nap.nap_mot_hv()` gọi `_done_get(uuid)` thấy vé còn → **trả kết quả cũ, bỏ qua INSERT thật** (short-circuit idempotency bắn nhầm). Hệ quả: không bản ghi mới trong DB, staging bị set lại `'xong'` với MaDK đã xóa.
- **Đã sửa:** `tool/app/nap.py` — `keo_ve_ve_cho()` xóa luôn `DELETE FROM nap_xong WHERE uuid=?` trước khi reset dòng (không phụ thuộc dòng keo_ve còn hay không).
- **Dọn dữ liệu kẹt:** vé `nap_xong` của Lê Thị Hồng (uuid `3e162f1e-…`, MaDK chết `70004-20261002214215390`) đã được gỡ; dòng về `'cho'` để nạp lại.
- **Test hồi quy:** `tool/tests/test_nap_keo.py` — `test_keo_ve_ve_cho_go_ve_khoi_nap_xong` + `test_keo_ve_ve_cho_go_ve_nap_xong_du_da_bo_khoi_hang_doi` (fail trên code cũ, pass trên code mới).
- **Deploy:** tool chạy cục bộ máy CSDT (chưa đóng gói/lên VPS) → có hiệu lực ngay khi chạy lại tool; backend dev đã restart code mới lúc sửa.
