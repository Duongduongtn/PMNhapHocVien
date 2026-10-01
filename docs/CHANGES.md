# Sổ thay đổi

> File do `/capnhat` ghi. Các lệnh khác đọc file này để biết tính năng nào đã bỏ / quyết định nào đã đổi.

| # | Ngày | Loại | Mã | Thay đổi | PRD | TDD | Màn hình | Code |
|---|---|---|---|---|---|---|---|---|
| 14 | 01/10/2026 | ✏️ Sửa | `THU-01`, `THU-02` | Redesign UX nhập liệu (impeccable): ẩn ô "Số CMND cũ" (vẫn lưu từ QR nếu có) · ô ngày gõ tay dd/mm/yyyy + nút lịch (giữ năm-only) · desktop tách vị trí 2 nút tránh bấm nhầm + bố cục nhập tay thân thiện + phím tắt · rà content tránh lộ story/AI slop | ✅ | ✅ | ⬜ | 🔄 đang dựng |
| 13 | 01/10/2026 | ✏️ Sửa + ➕ Thêm | `THU-01`, `THU-02`, `THU-04`, `QLY-06` | App web nhập liên tiếp: nút "Lưu & nhập hồ sơ tiếp" (gửi không ảnh + toast) + badge/lọc "Thiếu ảnh" (THU-01/02 hạ ⏳); +THU-04 cảnh báo trùng CCCD app web (SHOULD, cảnh báo mềm soi hàng đợi); +QLY-06 mở hồ sơ khóa khác cho HV đã có (📝 Draft, còn nợ kiểm DB) | ✅ | ✅ | ⬜ | 🟡 THU-01/02/04 code+test xong, chưa deploy · QLY-06 ⬜ |
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

- **Cập nhật:** 01/10/2026 (CHANGES #13)
- **Số story trong PRD:** 18 (17 MUST/SHOULD gồm `THU-04` + `QLY-06` 📝 Draft; chưa tính NICE `QLY-04`, `THU-03`)
- **Mã story hiện có:** `HTG-01`, `HTG-02`, `HTG-03`, `THU-01`, `THU-02`, `THU-04`, `NAP-01`…`NAP-06`, `KHO-01`, `QLY-01`, `QLY-02`, `QLY-03`, `QLY-05`, `QLY-06` (NICE: `QLY-04`, `THU-03`)
- **Mã đã nghỉ hưu:** (chưa có)
