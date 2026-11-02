# Sổ bug

> File do `/suabug` ghi. Khác `CHANGES.md`: file kia ghi **thay đổi yêu cầu**, file này ghi **code không làm đúng yêu cầu đã có**.

| # | Ngày | Mức | Story | Bug | Trạng thái | Deploy |
|---|---|---|---|---|---|---|
| 19 | 02/11/2026 | 🔴 Chặn | `NAP-07` · `NAP-03` · `SYNC-01` | **Tool: Enter ở ô gõ để lọc chọn sai không báo**, cùng gốc BUG-17. Sửa ở `ComboLoc` dùng chung: Enter chỉ chọn khi còn đúng một khả năng. Đã đóng gói exe, chưa commit. | ✅ Đã sửa | ⬜ |
| 18 | 02/11/2026 | 🔴 Chặn | `THU-01` · `THU-07` | **Ngày không có thật vẫn hiện ✓ và gửi được** (`45/13/1990`, `31/02/2021`, năm `9999`). Chỉ kiểm dạng số. Sửa: kiểm ngày có thật ở form nhập và form sửa. | ✅ Đã sửa | ✅ |
| 17 | 02/11/2026 | 🔴 Chặn | `THU-07` | **Enter ở ô Hạng, Nơi cấp chọn sai không báo.** Gõ `B1` ra "B1 số tự động", `A` ra A1, `C` ra C1, `Ha` ra Hà Nội. Sửa: Enter chỉ chọn khi còn đúng một khả năng. Tool cùng lỗi, xem BUG-19. | ✅ Đã sửa app web | ✅ |
| 16 | 02/11/2026 | 🟠 Nặng | `THU-01` · `THU-07` | **Dòng "Đã đủ thông tin bắt buộc" hiện xanh khi khối GPLX còn lỗi.** Danh sách thiếu chỉ tính 4 ô căn cước, trong khi nút gửi có kiểm GPLX nên báo đủ mà bấm vẫn bị chặn. Sửa: thêm "GPLX đã có" vào danh sách thiếu. | ✅ Đã sửa | ✅ |
| 15 | 02/11/2026 | 🟠 Nặng | `THU-01` | **Nút chính màn nhập hồ sơ không dính đáy trên điện thoại, lệch PRD.** Cụm nút nằm cuối form, cuộn theo nội dung; mở 2 bằng GPLX thì nút "Tiếp tục" nằm dưới mép màn. Sửa: nút chính dính đáy, nút phụ ở cuối form, máy tính giữ nguyên. | ✅ Đã sửa | ✅ |
| 14 | 07/10/2026 | 🟠 Nặng | `THU-01` | **iPhone (iOS Safari) không quét được QR CCCD — Android quét được.** Camera mở, thấy hình, nhưng rê mã QR ở góc trên phải thẻ mãi không nhận (treo màn quét). Gốc: `decodeTuCanvas` ưu tiên `BarcodeDetector` của máy (Android có → bắt mã nhỏ ở góc khỏe) rồi fallback `qr-scanner.scanImage` 1-lần-1-khung; **iOS Safari KHÔNG có BarcodeDetector** → luôn rơi xuống fallback yếu, quét nguyên khung 1080p nên bỏ sót mã QR nhỏ lệch góc. Sửa (phương án A): tách nhánh — máy có BarcodeDetector giữ vòng quét gốc (khung bám); **iPhone dùng lớp `QrScanner` của thư viện qr-scanner** (worker + dò lặp) **ÉP quét TOÀN khung** (`tinhVungQuet`, downscale ≤1024 giữ độ nét) thay vì vùng giữa mặc định. +4 unit test (28 vitest) + build/tsc sạch. **CHƯA verify iPhone thật** — lỗi chỉ hiện trên iOS. **CẬP NHẬT 07/10: fix A đã deploy (`c7d350a`) nhưng KHÔNG hiệu quả** — probe offline ảnh thẻ thật (zxing-cpp+pyzbar+OpenCV, kèm xoay/cắt sát/Otsu/phóng 3×) không engine nào đọc nổi QR → gốc là QR thẻ nhỏ/mờ + engine web yếu (jsQR còn yếu hơn), KHÔNG phải vùng quét. **Chốt A: giao lối iPhone cho OCR (THU-06)**, không đầu tư thêm QR iPhone. | ⏳ Vá bằng THU-06 | ⬜ (fix A đã deploy; QR iPhone không còn là lối dựa) |
| 13 | 07/10/2026 | 🟠 Nặng | `KQD-01` · `KQD-02` | **Lưới Cập nhật KQĐT không hiện điểm + kết luận ĐÃ LƯU cho HV đã cập nhật (09/10/14/90).** Dòng các trạng thái này là dòng NHẬP: ô input lấy `value={nr[m]}` (state nhập RAM, trống) + cột Kết luận tính từ `nhap` (`!t.full`→"đang nhập…"), KHÔNG đọc `h.diem`/`h.ket_luan` đã lưu. Chỉ dòng khóa cứng 12/13 mới render điểm lưu. Hậu quả: nhân viên tưởng điểm chưa lưu (ca TRẦN THỊ VÂN ANH, điểm thực đã ghi TT=09 Đạt). Vi phạm PRD KQD-01 "lưới hiện điểm (nếu có)". Sửa: `diemHint.ts` (`hintDiem` hiện "đã lưu X,X" dưới ô khi chưa gõ + có điểm) + cột Kết luận hiện "Đạt/Không đạt · đã lưu". **Verify live CDB thật** (Vân Anh hiện đủ điểm + "Đạt · đã lưu"). | ✅ Đã sửa | ⬜ (chờ chạy lại tool) |
| 12 | 03/10/2026 | 🟡 Nên sửa | `QLY-03` | **Xóa hẳn HV ở DB nhưng tab "Đã nạp" vẫn hiện.** `/xoa` (QLY-03) gỡ khỏi CSDT nhưng KHÔNG dọn dòng staging `'xong'` → "Đã nạp" (lọc keo_ve 'xong') còn hiện HV đã xóa. Sửa: sau `_xoa_hv_csdt` → `keo_ve_xoa(lay_uuid_theo_ma_dk(ma_dk))` (bỏ hẳn dòng staging, chỉ SQLite local; xóa hẳn ≠ gỡ nên KHÔNG về 'cho'). Frontend đã tự tải lại keoVe khi về tab Nạp (effect BUG-03). | ✅ Đã sửa | ⬜ (chờ chạy lại tool) |
| 11 | 03/10/2026 | 🔴 Chặn | `QLY-01` | **Lưới học viên lặp dòng nhiều lần** (regression từ BUG-10): query chi tiết lưới thêm 3 `LEFT JOIN` (DM_DonViGTVT + DM_DVHC cho TT/CT) để lấy tên; nhưng `DM_DVHC.MaDvhc` KHÔNG duy nhất → join **nhân dòng** HV (khóa 6 HV hiện 12+). Sửa: đổi 3 JOIN → **scalar subquery `TOP 1`** (lấy đúng 1 tên, không nhân dòng). Verify khóa 6 HV: 12→6. | ✅ Đã sửa | ⬜ (chờ chạy lại tool) |
| 10 | 03/10/2026 | 🟠 Nặng | `NAP-05` · `QLY-01` | **Nơi cấp căn cước rỗng + popup thiếu trường.** QR không mang nơi cấp → nạp để `NoiCapCMT` RỖNG (Lê Thị Hồng rỗng). Sửa: nạp **tự suy mã Sở GTVT từ số CCCD** (`cccd[2:3]`, vd `070…`→`70` Bình Phước; `NoiCapCMT`=mã đơn vị GTVT `DM_DonViGTVT` LoaiDV='SO', khớp 63/63) + **vá 6 bản ghi cũ** rỗng (chỉ CCCD 12 số hợp lệ). Popup "Chi tiết học viên" (tool) thêm **Ngày cấp · Nơi cấp (tên tỉnh) · Địa chỉ cư trú** + địa chỉ đầy đủ (join DM_DVHC). **Combobox "Nơi cấp" ở form nạp** (danh sách Sở GTVT, mặc định suy từ CCCD, operator sửa khi lệch) — endpoint `/local/dvhc/so-gtvt`. +2 test. **⚠️ THAY THẾ bởi CHANGES #40 (06/10): nơi cấp đổi sang `DM_DVHC.MaDvhc` (có '00' Cục QLHC), CCCD 12 số mặc định '00' — không còn là mã tỉnh/Sở GTVT.** | ✅ Đã sửa | ⬜ (chờ chạy lại tool) |
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

## BUG-19 — Tool: Enter ở ô gõ để lọc chọn sai không báo · 02/11/2026

- **Mức:** 🔴 Chặn · **Story:** `NAP-07` · `NAP-03` · `SYNC-01` · **File:** `tool/webui/src/lib/locLuaChon.ts` (mới), `components/ComboLoc.tsx`, `components/AddressCombo.tsx` (bỏ bản sao, dùng ô chung), `pages/tool/gplxDaCo.ts`
- **Ai báo:** rà nhập nhầm 02/11/2026; user yêu cầu sửa và đóng gói lại.
- **Tái hiện:** màn Nạp → ngăn Chuẩn bị → tích "Đã có GPLX" → ô Hạng gõ `B1` rồi Enter → ra "B1 số tự động".
- **Nguyên nhân gốc:** như BUG-17: Enter lấy dòng đầu của danh sách lọc "chứa chuỗi". Ô này dùng chung cho chọn khóa, tra cứu, nơi cấp; `AddressCombo` có bản sao riêng nên ô Tỉnh, Xã cùng rủi ro.
- **Đã sửa:** ô Hạng chỉ tìm theo tên hạng; dòng trùng khớp xếp đầu; Enter chỉ chọn khi còn đúng một khả năng, nên ở mọi màn dùng ô này, gõ dở còn nhiều khả năng thì phải bấm chọn.
- **Test hồi quy:** `tool/webui/e2e/gplx-da-co.e2e.ts` — `BUG-19` (FAIL trên code cũ, PASS trên code mới) · `tool/webui/src/lib/locLuaChon.test.ts`.
- **Deploy:** tool chạy ở máy CSĐT, đã đóng gói exe 02/11/2026, chưa mang sang máy CSĐT.

## BUG-18 — Ngày không có thật vẫn gửi được · 02/11/2026

- **Mức:** 🔴 Chặn · **Story:** `THU-01` · `THU-07` · **File:** `webapp/src/lib/qr.ts` (`laNgayCoThat`, `laNgaySinh`), `lib/gplxDaCo.ts`, `pages/Quet.tsx`, `pages/DaGui.tsx`
- **Ai báo:** rà nhập nhầm 02/11/2026 khi user hỏi nhập nhiều có nhầm không; user chọn sửa.
- **Tái hiện:** Nhập tay → Ngày sinh `45131990` → ô hiện ✓ xanh, dòng trạng thái báo đủ; Ngày cấp `31022021` → bấm gửi vẫn đi tiếp.
- **Nguyên nhân gốc:** form chỉ so mẫu `dd/mm/yyyy`, không xét ngày có tồn tại; hàm đọc QR `docNgay` có kiểm nhưng form không dùng. Ngày cấp sai cũng không vào dòng "còn thiếu".
- **Đã sửa:** dùng lại `docNgay` qua `laNgayCoThat`, `laNgaySinh` ở form nhập, form sửa và khối GPLX; năm-only chỉ nhận 1900-2100. API chưa kiểm ngày sinh, cố ý không thêm để nháp cũ đang chờ gửi không bị từ chối.
- **Test hồi quy:** `webapp/src/lib/gplxDaCo.test.ts` — `BUG-18: ngày không có thật bị chặn`. Script Playwright: FAIL trên code cũ, PASS trên code mới; chưa có trong repo. Kiểm tay: 4 ca nêu ở Tái hiện, thêm `02/03/1990` và `1990` vẫn được.
- **Deploy:** 02/11/2026, commit `210c5e1`.

## BUG-17 — Enter ở ô Hạng, Nơi cấp chọn sai không báo · 02/11/2026

- **Mức:** 🔴 Chặn · **Story:** `THU-07` · **File:** `webapp/src/lib/gplxDaCo.ts` (`locLuaChon`, `chonKhiEnter`), `components/GplxDaCoKhoi.tsx`
- **Ai báo:** rà nhập nhầm 02/11/2026; user chọn sửa.
- **Tái hiện:** tích "Đã có GPLX" → ô Hạng gõ `B1` rồi Enter → ra "B1 số tự động" (mã `B11`). Gõ `A` ra A1, `C` ra C1, `D` ra D1; ô Nơi cấp gõ `Ha` ra Hà Nội.
- **Nguyên nhân gốc:** Enter lấy dòng đầu của danh sách lọc theo "chứa chuỗi", và chuỗi tìm gồm cả chữ "luật mới/cũ". Thứ tự danh sách quyết định kết quả, không phải chữ đã gõ.
- **Đã sửa:** Hạng chỉ tìm theo tên hạng; dòng trùng khớp xếp đầu; Enter chỉ chọn khi còn đúng một khả năng. `A1`, `C`, `D` có ở cả hai luật nên Enter giữ danh sách mở để tự chọn.
- **Test hồi quy:** `webapp/src/lib/gplxDaCo.test.ts` — 2 test `BUG-17`. Script Playwright: FAIL trên code cũ, PASS trên code mới; chưa có trong repo.
- **Còn lại:** tool cùng lỗi, xem BUG-19.
- **Deploy:** 02/11/2026, commit `210c5e1`.

## BUG-16 — Dòng "đã đủ" báo sai khi GPLX còn lỗi · 02/11/2026

- **Mức:** 🟠 Nặng · **Story:** `THU-01` · `THU-07` · **File:** `webapp/src/pages/Quet.tsx` (`Preview`)
- **Ai báo:** critique Impeccable 02/11/2026; user chọn sửa.
- **Tái hiện:** điền đủ căn cước → tích "Đã có GPLX", để trống bằng → dòng xanh "Đã đủ thông tin bắt buộc, sẵn sàng lưu" vẫn hiện.
- **Nguyên nhân gốc:** `THU-07` thêm kiểm GPLX vào `giu`/`giuVaTiep` qua `loiDanhSach`, nhưng mảng `thieu` của dòng trạng thái không được nối thêm, nên hai nơi kết luận khác nhau.
- **Đã sửa:** thêm `loiDanhSach(gplx) && "GPLX đã có"` vào `thieu`; chuyển `useState` của `gplx` lên trước chỗ dùng.
- **Kiểm tay (webapp chưa có bộ test DOM/Playwright):** điền đủ căn cước → báo đủ; tích GPLX, bằng trống → "Còn thiếu: GPLX đã có"; điền đủ bằng → báo đủ lại; bỏ tích → vẫn báo đủ. Đã chạy bằng script Playwright một lần: 2 mục FAIL trên code cũ, PASS trên code mới.
- **Deploy:** 02/11/2026, commit `f8f3fb7`.

## BUG-15 — Nút chính không dính đáy trên điện thoại · 02/11/2026

- **Mức:** 🟠 Nặng · **Story:** `THU-01` (PRD dòng 69; story đang ⚠️ Partial nên không hạ thêm) · **File:** `webapp/src/pages/Quet.tsx` (`Preview`, vùng cuộn)
- **Ai báo:** critique Impeccable 02/11/2026; user chốt chỉ nút chính dính đáy, nút phụ cuối form.
- **Tái hiện:** 375×812 → Nhập tay → tích "Đã có GPLX" → "+ Thêm GPLX" → nút "Tiếp tục" nằm ngoài màn (Y đáy 1.675 khi ở đầu form, thanh điều hướng ở Y 751).
- **Nguyên nhân gốc:** cụm nút là khối thường cuối form, không có `sticky`. Form ngắn thì vẫn thấy nút nên lỗi ẩn; khối GPLX làm form dài mới lộ.
- **Đã sửa:** nút chính bọc trong thanh `sticky -bottom-4` (bù đệm vùng cuộn, nếu để `bottom-0` chữ form lọt qua khe dưới thanh); hai lớp `contents` để form là cha của thanh; vùng cuộn thêm `scroll-pb-20` để ô đang focus không bị che. Thứ tự Tab trên máy tính đổi thành nút phụ trước nút chính, bố cục máy tính giữ nguyên.
- **Kiểm tay (webapp chưa có bộ test DOM/Playwright):** ở 375 và 800, form trống và 2 bằng, cuộn đầu/giữa/cuối: nút chính luôn thấy trọn, thanh sát thanh điều hướng, nút phụ và dòng gợi ý không bị che, ô đang focus không bị che, danh sách Nơi cấp nổi trên thanh. Ở 1440: hai nút cùng hàng, nút chính bên phải, không dính. Đã chạy bằng script Playwright: FAIL trên code cũ, PASS trên code mới. Chưa thử trên điện thoại thật có bàn phím ảo. Ảnh: `anh-kiem/02-11-2026-BUG-15/`.
- **Deploy:** 02/11/2026, commit `f8f3fb7`.

## BUG-14 — iPhone (iOS Safari) không quét được QR CCCD · 07/10/2026

- **Mức:** 🟠 Nặng · **Story:** `THU-01` (đang ⚠️ Partial) · **File:** `webapp/src/pages/Quet.tsx` + `webapp/src/lib/qr.ts` (`tinhVungQuet` mới)
- **Ai báo:** user 07/10/2026 (đã ghi nhận ở CHANGES #43 dòng 124 "xử lý riêng", nay mới xử). Triệu chứng user chốt phương án A.
- **Tái hiện:** mở app web trên **iPhone (Safari)** → bấm "Quét QR CCCD" → camera mở, thấy hình → rê mặt trước CCCD (mã QR ở **góc trên phải**) vào khung → **mãi không nhận, treo màn quét**. Cùng thao tác trên **Android quét ra ngay**. *(Lỗi chỉ hiện trên iOS thật — máy dev không chạy được iOS Safari nên root-cause bằng đọc code; bản sửa chờ kiểm iPhone.)*
- **Nguyên nhân gốc:** `decodeTuCanvas` giải mã theo thứ tự ①`BarcodeDetector` native → ②`qr-scanner.scanImage` (fallback). **iOS Safari tới 2026 vẫn KHÔNG hỗ trợ `BarcodeDetector`** → mọi khung hình rơi xuống nhánh ②; code chụp nguyên khung ~1080p rồi quét 1-lần-1-khung, mã QR CCCD nhỏ lại nằm lệch góc nên nhánh ② (yếu hơn hẳn detector native) không khóa được mã. Android có BarcodeDetector native → bắt mã nhỏ/góc khỏe nên quét ra. Tức: nhánh dự phòng đủ cho ảnh tĩnh nhưng quá yếu cho camera trực tiếp iPhone.
- **Đã sửa (phương án A — user chốt 07/10):** tách 2 nhánh trong `KhungQuet`:
  - Máy **có** `BarcodeDetector` (Android/Chrome) → giữ nguyên vòng quét cũ (`getUserMedia` + `setInterval` tick + khung bám QR). **Không đụng** → không regression.
  - Máy **không có** (iPhone/iOS) → dùng lớp `QrScanner` của thư viện `qr-scanner` (worker + dò lặp, viết riêng cho camera trực tiếp iOS), **ép quét TOÀN khung** qua `tinhVungQuet(w,h)` (vùng `0,0→w,h`, downscale ≤1024 giữ độ nét) thay cho vùng-giữa-2/3 mặc định của thư viện — chính chỗ bỏ sót mã ở góc. Đèn flash chuyển sang `QrScanner.turnFlashOn/Off`; `dungCamera` dừng+`destroy` QrScanner. Đánh đổi (PRD cho phép ở edge case): iPhone mất "khung bám theo mã" (cornerPoints), dùng khung ngắm tĩnh.
- **Test hồi quy:** `webapp/src/lib/qr.test.ts` — nhóm `tinhVungQuet — BUG-14` (4 ca: quét từ gốc phủ toàn khung · downscale ≤1024 · khung nhỏ giữ nguyên · video chưa sẵn mặc định 1280×720). Guard chống việc lỡ quay lại quét vùng giữa (bỏ sót mã góc). **28 vitest pass · `tsc -b` + `vite build` sạch.**
- **Kiểm tay còn lại (BẮT BUỘC trên iPhone thật, chưa làm được ở máy dev):**
  1. iPhone Safari → Quét QR CCCD → đưa mặt trước CCCD (mã góc phải) vào khung → **nhận trong ~1-2 giây**, tự điền đủ trường.
  2. Android → quét vẫn ra như cũ (không regression).
  3. Nút đèn flash trên iPhone (nếu máy có) bật/tắt được.
  4. Đóng màn quét → camera tắt hẳn (không còn chấm xanh camera trên iPhone).
- **CẬP NHẬT 07/10/2026 (sau deploy + probe) — fix A KHÔNG hiệu quả:** đã deploy `c7d350a` nhưng iPhone vẫn không quét được. Verify bằng **probe offline** trên ảnh thẻ CCCD thật: giải mã bằng **zxing-cpp + pyzbar + OpenCV QRCodeDetector**, kèm xoay, downscale, cắt sát khung QR, nhị phân Otsu, phóng 3× → **KHÔNG engine nào đọc được**. Kết luận gốc chính xác hơn: **QR trên thẻ CCCD nhỏ + in mờ, cộng engine giải mã trên web yếu** — `qr-scanner` (jsQR) ở fix A còn yếu hơn cả 3 engine vừa thử, nên đổi vùng quét/engine kiểu này không thể cứu. **Không phải lỗi vùng quét.** → **Đừng tinh chỉnh vùng quét QR nữa.**
- **Hướng xử lý (user chốt A, 07/10):** lối nhập trên iPhone chuyển sang **OCR đọc chữ trên thẻ (THU-06)** — đọc trực tiếp text in trên CCCD thay vì giải mã QR. BUG-14 **không đóng độc lập**, coi như **vá bằng THU-06**. Fix A (`c7d350a`) giữ nguyên (vô hại, iPhone vẫn thử QR toàn khung nếu muốn), nhưng QR **không còn là lối dựa** cho iPhone.
- **Trạng thái:** ⏳ Vá bằng THU-06 — QR iPhone xác định không khả thi bằng engine web; chờ THU-06 (OCR) phủ. `THU-01` giữ ⚠️ Partial; lối iPhone đã trỏ sang THU-06 (PRD §MUST, /capnhat #49).
- **Deploy:** fix A đã lên production (`c7d350a`); không có deploy thêm cho hướng QR. Lối iPhone thật sự có khi THU-06 xong + deploy.

---

## BUG-13 — Lưới KQĐT không hiện điểm + kết luận đã lưu cho HV đã cập nhật · 07/10/2026

- **Mức:** 🟠 Nặng · **Story:** `KQD-01` (lưới hiện "điểm nếu có") · `KQD-02` · **File:** `tool/webui/src/pages/ketqua/CapNhatKQDT.tsx` + `diemHint.ts` (mới)
- **Ai báo:** người quản CDB (nghiệm thu máy CSDT), ca HV **TRẦN THỊ VÂN ANH** (CCCD 075185005104, khóa 75032K260009).
- **Tái hiện:** cập nhật điểm 1 HV → vào lọc "Đã cập nhật" xem lại → ô nhập trống + cột Kết luận "đang nhập…" → tưởng điểm chưa lưu. Verify DB đích: điểm ĐÃ ghi đủ (LT 8,3·MP 5,0·SH 6,3·CC 5,0·ĐT 7,3), TT_XuLy=09 Đạt.
- **Nguyên nhân gốc:** lưới gộp KQD-01 (xem) + KQD-02 (nhập) — dòng HV 09/10/14/90 render **dạng NHẬP**: ô input `value={nr[m]}` lấy state nhập RAM (trống khi chưa gõ lại), gợi ý dưới ô + cột Kết luận tính từ `nhap` (`t.qd`/`t.full`), **không bao giờ đọc `h.diem`/`h.ket_luan` đã lưu**. Chỉ nhánh khóa cứng (12/13) mới hiện `d1(h.diem)`. → HV đã có điểm nhưng chưa kết xuất nhìn như trống.
- **Đã sửa:** tách `hintDiem(over, qd, saved)` ra `diemHint.ts` — chưa gõ mà có điểm lưu → "đã lưu X,X" (thay "—"); đang gõ → preview "→ X,X"; vượt khung → "sai". Cột Kết luận: `!t.full` mà có `h.ket_luan` → "Đạt · đã lưu" / "Không đạt · đã lưu".
- **Test hồi quy:** `tool/webui/src/pages/ketqua/diemHint.test.ts` (4 test) — case `hintDiem(false,null,8.3)` phải ra "đã lưu 8,3"; logic cũ (`qd==null?"—"`) ra "—" → FAIL trên code cũ, PASS trên code mới.
- **Kiểm tay (đã chạy live):** CDB thật, khóa B01-K42 → HV Vân Anh hiện đủ "đã lưu …" 5 môn + Kết luận "Đạt · đã lưu".
- **Deploy:** chưa commit (phần KQĐT chưa commit); hiệu lực sau khi chạy lại tool.

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
