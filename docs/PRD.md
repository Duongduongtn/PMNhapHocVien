# PRD — Hệ thống Thu nhận hồ sơ học viên (mobile/web + tool nạp DB)

> Mô tả ngắn: App web (điện thoại/máy tính) thu thập thông tin học viên bằng quét QR căn cước + chụp ảnh, đẩy lên VPS; tool tại máy DB kéo về, map địa chỉ, xử lý ảnh và nạp vào DB `GPLX_CSDT` qua stored procedure có sẵn — hiển thị y như app cũ. Cho CSDT đào tạo lái xe (CSDT 70004).

---

## ① Overview

- **App name:** Thu nhận hồ sơ học viên (3 thành phần: App web · Backend VPS · Tool máy DB)
- **Tagline:** Quét căn cước — thu thập mọi nơi, nạp DB một chạm, đúng y app cũ.
- **Problem:** Nhân viên phải ngồi tại máy DB gõ tay từng học viên từ CCCD, tự tra/đổi địa chỉ sau sáp nhập 2025, chụp ảnh rời — chậm, dễ sai địa chỉ, nghẽn đầu khóa, bị trói tại một máy.
- **Solution:** Tách thu thập (app web quét QR + chụp ảnh, gửi VPS) khỏi nạp (tool tại máy DB map địa chỉ tự động, căn ảnh + xóa phông + xuất `.jp2`, nạp qua SP có sẵn). Bản ghi tạo ra không phân biệt được với bản do app cũ nhập.
- **Platform:** Both — App web responsive (mobile + desktop) + Tool desktop (UI localhost).

---

## ② Target User

**Persona chính — Nhân viên thu nhận hồ sơ (tuyển sinh):**
- Nghề: nhân viên CSDT (~3–10 người), dùng điện thoại tại quầy/hiện trường.
- Hàng ngày: tiếp học viên, thu CCCD, lập hồ sơ nhập học.
- Nỗi đau: gõ tay lặp lại, tra địa chỉ thủ công, nghẽn đầu khóa.
- Tool hiện tại: app desktop cũ (màn "Thu nhận Hồ sơ cấp mới") tại máy DB.

**Persona phụ — Nhân viên nạp DB:** 1–2 người, ngồi tại máy DB, kéo dữ liệu về, kiểm và nạp vào DB, quản lý hồ sơ, tạo khóa.
**Persona quản trị:** quản tài khoản, cấu hình, xóa PII.

📄 Vai trò đầy đủ: `docs/ba/thu-nhan-ho-so-hoc-vien/07-roles-permissions.md`

---

## ③ Features & User Stories

### 🟢 MUST (bắt buộc có trong MVP)

#### [HTG-01] Đăng nhập & phân quyền + cấu hình kết nối

**Trạng thái:** ✅ Done — 01/10/2026, đủ 3 task: ① cấu hình (task 4) · ② auth JWT 3 vai trò (task 14) · ③ login UI webapp + cổng đăng nhập tool (task 17). Tool xác thực qua VPS rồi phát session cục bộ (option A); /local/config miễn token (A1). review-nghiepvu đủ 4/4. E2E đăng nhập 3 vai trò live để ở Checkpoint 3 (/kiemthu).
**Story:** Là người dùng, tôi muốn đăng nhập bằng tài khoản riêng, để hệ thống truy vết được ai gửi/ai nạp (dữ liệu căn cước).

**Done khi:**
- ✅ App web và tool đều bắt đăng nhập; không đăng nhập không dùng được.
- ✅ 3 vai trò: nhân viên thu nhận · nhân viên nạp DB · quản trị; mỗi người một tài khoản (không dùng chung).
- ✅ Tool có **bảng Cấu hình**: nhập kết nối SQL Server (server/database/user/password) + URL VPS + API key, có nút "Kiểm tra kết nối", lưu vào config cục bộ (mã hóa). *(04/10/2026 — CHANGES #34: bảng này **dời lên icon ⚙ ở header** dùng chung cả tool, gộp với quản lý CSDL đích; chi tiết + UI mới ở **HTG-07**. Cơ chế config-store + kiểm kết nối giữ nguyên, nên HTG-01 vẫn ✅.)*
- ✅ Nhân viên thu nhận không gọi được chức năng nạp DB (chặn 403).
- ❌ Không làm SSO/đăng nhập bằng Google/Zalo lần này.
- *(05/10/2026 — CHANGES #38) **Phiên đăng nhập của TOOL** chuyển sang vĩnh viễn (lưu đĩa, chỉ Đăng xuất mới thoát) — chi tiết ở **DGT-04**. Chỉ áp cho tool; đăng nhập app web giữ nguyên phiên thường → HTG-01 vẫn ✅.*

> Nguồn: CAP-014 · BR-020 · OG-001, OG-002, OG-004 · EC-050

#### [THU-01] Quét QR căn cước + xác nhận/sửa (app web, mobile)

**Trạng thái:** ⚠️ Partial — redesign desktop (CHANGES #30, 03/10/2026) code XONG: `Quet.tsx` thêm hook `useIsDesktop`, desktop vào thẳng form nhập tay (bỏ cổng ChonCach), nút Quét QR/Tải ảnh phụ góc phải, popover camera (`QuetPopover`) đè form tự điền, "Lưu & nhập tiếp" về form trống; mobile guard `!isDesktop` giữ nguyên. Kiểm mức 1: webapp build + typecheck sạch · 24 vitest pass · review-nghiepvu **8/8 đủ**. **CHƯA chụp Playwright 3vp (375/800/1440)** — màn sau đăng nhập + cần backend stack, chưa dựng được phiên này. Mobile vẫn ✅ như trước (task 30, deploy live `029026c`). Trước đó ✅ Done 01/10/2026: Nhập liên tiếp ("Lưu & nhập hồ sơ tiếp") + redesign UX nhập liệu (task 30, CHANGES #13/#14: ẩn ô CMND cũ, ô ngày auto-mask "/" + nút lịch giữ năm-only, desktop 2 cột + 2 nút tách hai đầu + phím tắt + nới khung). Kiểm: webapp 24 test · build · 4 review (nghiệp vụ/kỹ thuật/bảo mật/giao diện) đã vá · Playwright 1440/375 · deploy live `029026c`. Nền quét QR (task 18/28) — khung bám QR cần thẻ thật AS-001. — 08/10/2026 (CHANGES #52): thêm loạt UX desktop cho form xác nhận (nút gạt Nam/Nữ, gợi ý địa chỉ 2025, chặn+đếm CCCD 12 số, in hoa tên, phím mũi tên, icon nhãn, trạng thái ✓/đỏ từng ô, tự suy giới tính/năm sinh từ CCCD) — code+build+34 test pass, commit `5087ceb`; **vẫn chờ chụp Playwright 3vp** để chốt ✅.
**Story:** Là nhân viên thu nhận, tôi muốn quét QR căn cước để điền sẵn hồ sơ, để giảm gõ tay.

**Steps to Complete:**
1. Mở app web → **mobile: màn vào** cho chọn **Quét QR CCCD / Nhập tay / Tải ảnh CCCD** (camera **chỉ bật khi bấm "Quét QR"** — CHANGES #12). **Desktop (≥lg): vào thẳng form nhập tay** (con trỏ tự vào ô Số CCCD); **Quét QR / Tải ảnh CCCD** là 2 nút phụ nhỏ ở góc phải tiêu đề — bấm Quét QR mở **popover camera nổi** đè form, quét xong tự điền vào form đang mở (CHANGES #30).
2. Bấm Quét → bật **camera sau** (`facingMode: {ideal:'environment'}`, ~1080p); best-effort `focusMode: continuous` + zoom 2x + nút đèn flash (torch). Tự giải mã liên tục, không cần bấm chụp.
3. Giải mã bằng **BarcodeDetector API** (native, nhanh) → fallback **qr-scanner (ZXing)** khi trình duyệt không hỗ trợ; **auto-capture** khi kết quả ổn định ~2 frame (~500ms).
4. Quét được → **hiệu ứng quét OK** (app tự thiết kế riêng: rung + đổi màu + tick ✓) rồi hiện màn preview.
5. Parse chuỗi QR (chuẩn Bộ Công an 2021) → hiện các trường **cho sửa** trước khi giữ.

**Done khi:**
- ✅ **Mobile — màn vào không tự mở camera**: cho chọn Quét QR / Nhập tay / Tải ảnh; camera bật khi bấm Quét (CHANGES #12).
- ✅ **Desktop (≥lg) — vào thẳng form nhập tay** (CHANGES #30, code xong — chờ chụp Playwright): bỏ cổng chọn cách nhập; **Quét QR / Tải ảnh CCCD** thu nhỏ thành nút phụ ở góc phải tiêu đề; **Quét QR mở popover camera nổi** đè form (form vẫn hiện), quét xong tự điền vào form đang mở; con trỏ tự vào ô Số CCCD. Mobile KHÔNG đổi.
- ✅ Quét mặt trước CCCD gắn chip hợp lệ → điền đúng: CCCD (12 số), [CMND cũ 9 số nếu có], họ tên, ngày sinh (ddMMyyyy → lưu yyyymmdd), giới tính (Nam/Nữ), nơi thường trú, ngày cấp.
- ✅ Chuỗi QR **6 hoặc 7 trường** (tách `|`, CMND cũ tùy có) đều parse được; sai định dạng → báo lỗi rõ (số trường / CCCD ≠ 12 số...).
- ✅ **Khung quét bám theo mã** khi bắt trúng (dùng 4 góc `cornerPoints` của BarcodeDetector) — không phải khung xanh tĩnh; vẫn auto-capture khi ổn định; hiệu ứng báo thành công; mọi trường sửa được. (CHANGES #12)
- ✅ Trên điện thoại (NFR Responsive): layout **vừa một màn** (`100dvh`), khung camera co giãn, **thanh điều hướng + nút hành động chính dính đáy**, không phải cuộn để thấy nút. **Logo header không phải nút** (bỏ dáng camera bấm được). (CHANGES #12)
- ✅ Decoder: BarcodeDetector native + fallback qr-scanner (ZXing) — tham khảo cách quét từ dự án webThanhdat; hiệu ứng thiết kế riêng.
- ✅ **Lưu & nhập hồ sơ tiếp** (CHANGES #13): màn xác nhận có thêm nút **"Lưu & nhập hồ sơ tiếp"** bên cạnh "Tiếp tục — chụp ảnh chân dung" → gửi ngay **không kèm ảnh** (chi tiết gửi + toast ở THU-02) rồi về **màn chọn cách nhập** (Quét QR / Nhập tay / Tải ảnh) để làm hồ sơ kế tiếp. Áp cho cả quét QR lẫn nhập tay (cùng đi qua màn xác nhận). **Desktop không có cổng chọn → quay về form nhập tay TRỐNG cho hồ sơ kế tiếp** (CHANGES #30).
- ✅ **Màn xác nhận thân thiện nhập tay** (CHANGES #14): **ẩn ô "Số CMND cũ"** khỏi form (vẫn lưu/gửi giá trị từ QR nếu có); ô **ngày sinh/ngày cấp** gõ tay dd/mm/yyyy **+ nút lịch** bấm chọn, vẫn nhập được **năm-only**; **desktop**: tách vị trí 2 nút tránh bấm nhầm, bố cục gọn, **phím tắt** (autofocus ô đầu, Enter → nút chính, tab order hợp lý).
- ✅ **Form desktop gọn + nhập nhanh hơn** (CHANGES #52): nới khung desktop (2xl→3xl); sắp lại ô (**Số CCCD + Ngày cấp cùng hàng**, Họ tên và Nơi thường trú trọn bề ngang); **Số CCCD chặn quá 12 số + bộ đếm `n/12`** (xanh khi đủ); **Họ và tên tự in hoa** khi gõ; **Giới tính dùng nút gạt Nam/Nữ** thay dropdown; **Nơi thường trú gợi ý Tỉnh/Xã 2 cấp 2025** (nhập tự do, khớp không dấu, **không ép chọn** — hợp cả địa chỉ cũ 3 cấp); **phím mũi tên nhảy giữa các ô**; **icon ở nhãn từng ô**; **trạng thái ✓/đỏ từng ô + dòng "còn thiếu/đã đủ"**; **tự suy Giới tính + Năm sinh từ số CCCD** (gợi ý mặc định, sửa đè được). Áp cho form xác nhận dùng chung (QR/nhập tay/OCR). Thuần giao diện+nhập liệu, không đổi dữ liệu gửi.
- ❌ THU-01 không tự OCR — đọc chữ trên thẻ bằng OCR **tách sang `THU-06`** (lối dự phòng khi QR không quét được, CHANGES #49); ảnh thẻ ở THU-01 chỉ dùng cắt ảnh chân dung.

**Edge cases:**
| Tình huống | Hành vi mong muốn |
|---|---|
| QR mờ/không đọc được | Fallback: đọc QR từ **ảnh CCCD tải lên/chụp sẵn**, hoặc **nhập tay** (THU-02) |
| Trình duyệt không trả `cornerPoints` (qr-scanner fallback) | Dùng khung ngắm tĩnh + hiệu ứng vạch quét; không chặn |
| Camera bị chặn quyền / đang bận / thiếu HTTPS | Báo lỗi cụ thể theo từng ca + gợi ý nhập tay |
| Chuỗi QR sai số trường / CCCD ≠ 12 số | Báo lỗi rõ, không tự điền bừa |
| CCCD ghi ngày sinh chỉ có năm | Lưu yyyy0000, cho nạp |

> Nguồn: CAP-001 · BR-018 · EC-031, EC-033

#### [THU-02] Nhập tay + chụp ảnh + gửi VPS (app web)

**Trạng thái:** ⚠️ Partial — **nhánh #44 (chụp-bù-imported) đã CODE + unit test 07/10/2026; CHƯA chạy E2E 3 hệ thống ở máy CSDT (app→VPS→tool kéo ảnh→nạp DB).** Đã làm: server nới `POST /api/ho-so/:uuid/anh` sang allowlist `{pending,imported}` + job PII tính tuổi theo `updated_at` (server 44 test pass); app web `DaGui.tsx` hiện nút chụp bù cho HV `imported` thiếu ảnh (webapp 24 test + tsc pass); tool `keoAnhVps`/lọc "Chưa ảnh" dùng lại QLY-05 nguồn b (có sẵn #32). **Lật Phương án A** (chốt 01/10) → B. Chờ nghiệm thu ở máy CSDT để chốt ✅. — ✅ Done trước đó 01/10/2026: Gửi nhanh không ảnh (toast) + badge "Thiếu ảnh" + bộ lọc thiếu ảnh ở "Hồ sơ đã gửi" (task 30, CHANGES #13) + form nhập tay thân thiện (ô ngày auto-mask/lịch, CHANGES #14) + ảnh 2 nút chụp/chọn-từ-máy & phóng to popup (CHANGES #15). Kiểm: server 67 test · webapp 24 · 4 review đã vá · Playwright 1440/375 · deploy live.
**Story:** Là nhân viên thu nhận, tôi muốn nhập tay và chụp ảnh chân dung rồi gửi lên VPS, để thu thập được cả khi không quét được QR.

**Steps to Complete:**
1. Nhập/sửa các trường cá nhân (khi không quét QR hoặc cần bổ sung).
2. Chụp ảnh chân dung thô (người thật) hoặc ảnh thẻ; bản desktop có thể thêm ảnh sau/upload.
3. Bấm gửi → bản ghi + ảnh thô lên VPS, trạng thái `cho_nap`.

**Done khi:**
- ✅ Gửi thành công → bản ghi có UUID, trạng thái `pending` trên VPS.
- ✅ Xem lại được danh sách bản ghi mình đã gửi.
- ✅ **Hiện ảnh chân dung thật** (thumbnail) ở danh sách + chi tiết hồ sơ đã gửi (không còn icon xám) — nhân viên tải lại ảnh của **chính mình** qua endpoint mới (TDD §4.3). (CHANGES #12)
- ✅ **Bấm hồ sơ đã gửi → xem chi tiết**; khi còn **Chờ nạp** cho **Sửa thông tin** + **Chụp/đổi ảnh** (server cho sửa lúc `pending`); khi **Đang nạp/Đã nạp** thì **chỉ xem** — **trừ bổ sung ảnh cho HV thiếu ảnh** (xem Done khi "chụp bù ảnh cho HV đã nạp", CHANGES #44). (CHANGES #12)
- ✅ **Tìm trong danh sách đã gửi** theo **tên (khớp cả có dấu lẫn không dấu)** hoặc **số CCCD**; ô tìm đặt trên đầu danh sách, màn hẹp thu gọn thành **nút kính lúp** (bấm mới bung ô nhập). (CHANGES #10)
- ✅ Nơi thường trú lấy từ QR (hoặc nhập tay), cho sửa trước khi gửi. Nơi cư trú (tạm trú) **không nhập ở app** — tool mặc định = nơi thường trú khi nạp (BR-004 / TDD §8.1; xem CHANGES #9).
- ✅ **Gửi nhanh không ảnh để nhập liên tiếp** (CHANGES #13): ở màn xác nhận bấm "Lưu & nhập hồ sơ tiếp" → gửi hồ sơ **không kèm ảnh** → hiện **toast "Đã gửi ✓"** (không qua màn kết quả) → về màn chọn cách nhập. Mất mạng vẫn giữ nháp, tự gửi lại khi có mạng (như cũ).
- ✅ **Badge "Thiếu ảnh" + bộ lọc** (CHANGES #13): ở "Hồ sơ đã gửi", hồ sơ chưa có ảnh chân dung hiện **badge "Thiếu ảnh"** (list + chi tiết) và có **bộ lọc riêng gom hồ sơ thiếu ảnh** để chụp bổ sung sau (nút "Thêm ảnh"). Badge thông báo cho mọi trạng thái.
- ⚠️ **Chụp bù ảnh cho HV thiếu ảnh — kể cả ĐÃ NẠP** (CHANGES #44, lật Phương án A) — *code + unit test xong, chờ E2E máy CSDT*: với hồ sơ **thiếu ảnh**, nút "Thêm ảnh"/"Chụp ảnh" hiện **cả khi Chờ nạp lẫn Đã nạp** (trước đây chỉ Chờ nạp). Collector chụp/chọn ảnh → gửi lên VPS (ghi đè ảnh thô của hồ sơ đó) kể cả hồ sơ đã `imported`. Nhờ đó người nạp kéo ảnh về ở Tra cứu DB (QLY-05) để bổ sung vào DB. **Chỉ mở cho bổ sung ẢNH** — hồ sơ đã nạp vẫn **không sửa thông tin, không xóa** ở app web. (Vẫn chỉ ảnh của chính mình — kiểm `created_by`.)
- ✅ **Form nhập tay thân thiện** (CHANGES #14): dùng chung màn xác nhận với THU-01 — ẩn ô CMND cũ, ô ngày có nút lịch (giữ năm-only), desktop bố cục gọn + phím tắt; ô sửa ngày sinh trong "Hồ sơ đã gửi" cũng có nút lịch.
- ✅ **Ảnh: chụp trực tiếp hoặc chọn từ máy + xem phóng to** (CHANGES #15): màn chụp ảnh & đổi ảnh (hồ sơ Chờ nạp) có **2 nút "Chụp ảnh" / "Chọn từ máy"** (bỏ ép camera, chọn được ảnh có sẵn); bấm ảnh chân dung ở chi tiết → **phóng to popup**.
- ❌ Không xóa phông/căn ảnh ở điện thoại (để tool làm).

**Edge cases:**
| Tình huống | Hành vi mong muốn |
|---|---|
| Mất mạng khi gửi | Giữ nháp, gửi lại tự động khi có mạng; idempotent theo UUID (không tạo 2 bản ghi) |
| Sửa/chụp lại hồ sơ vừa bị tool khóa (`importing`) | Server trả 409 → báo "hồ sơ đã vào nạp, không sửa được", chuyển về chỉ xem |
| Nhập thiếu trường bắt buộc (SoCMT) | Cảnh báo, chưa cho gửi |
| Họ tên/địa chỉ vượt độ dài cột DB (HoVaTen ≤50, HoDemNLX ≤30, TenNLX ≤20, HoVaTenIn ≤25) | Cảnh báo + cho sửa/cắt trước khi nạp, giữ dấu tiếng Việt; không để SP lỗi |

> Nguồn: CAP-002 · BR-004, BR-015, BR-020 · EC-020, EC-060

#### [HTG-02] Hàng đợi VPS + tự xóa PII 30 ngày

**Trạng thái:** ✅ Done — 01/10/2026, hàng đợi + lock CAS + upload/validate ảnh (task 15) + job APScheduler xóa PII 30 ngày bỏ qua importing (task 16); 50/50 test pass (SQLite in-memory), review-nghiepvu đủ cả 2 phần. HTTPS là cấu hình nginx lúc deploy.
**Story:** Là hệ thống, tôi muốn lưu bản ghi thu thập vào hàng đợi và tự xóa sau 30 ngày, để tool kéo về và bảo vệ dữ liệu căn cước.

**Done khi:**
- ✅ Bản ghi lưu trên VPS (PostgreSQL) + ảnh thô, có trạng thái `pending`/`importing`/`imported`.
- ✅ Bản ghi tự xóa (kèm ảnh thô) sau 30 ngày; job không đụng bản đang `importing`.
- ✅ Mọi API qua HTTPS + xác thực token.
- ❌ VPS không kết nối SQL Server.

> Nguồn: CAP-003 · BR-016 · EC-040 · OG-001, OG-007

#### [THU-06] Chụp ảnh thẻ → tự đọc chữ (OCR) điền sẵn hồ sơ (app web)

**Trạng thái:** ⚠️ Partial — code xong task 79+80 (build+34 test pass, review-nghiepvu 5/6 — "ô đỏ" chốt dùng banner lỗi chung như THU-01/02); **chỉ còn chờ kiểm mức 1 trên thẻ + điện thoại thật (Checkpoint 17)**: độ chính xác OCR tiếng Việt có dấu + luồng mobile. — thêm 07/10/2026 (CHANGES #49). Lối nhập **thứ 3** khi QR không quét được (đặc biệt iPhone/iOS — engine QR trên web yếu hơn Android, xem BUG-14). Mở cho **mọi thiết bị**. Engine OCR + nơi chạy (client / dịch vụ) **chốt ở `/tdd`**.
**Story:** Là nhân viên thu nhận, khi QR trên thẻ không quét được (mờ/lóa/nhỏ), tôi muốn chụp ảnh mặt trước CCCD để hệ thống tự đọc chữ điền sẵn hồ sơ, để khỏi gõ tay toàn bộ.

**Steps to Complete:**
1. Màn vào (mobile) thêm lối thứ 3 **"Chụp ảnh thẻ (tự đọc)"** cạnh Quét QR / Nhập tay / Tải ảnh CCCD — **mọi thiết bị**, không khóa theo máy.
2. Chụp hoặc tải ảnh mặt trước CCCD → hệ thống **OCR** đọc các trường in trên thẻ.
3. Điền sẵn vào **màn xác nhận dùng chung** (THU-01/02) **5 trường in ở mặt trước**: Số CCCD, họ tên, ngày sinh, giới tính, nơi thường trú. (**Ngày cấp ở mặt sau thẻ → không đọc; nhân viên nhập tay** — xem Done khi.)
4. **Nhân viên xác nhận/sửa** từng trường trước khi lưu — OCR có thể đọc sai ký tự, không tin tuyệt đối.

**Done khi:**
- ⬜ Màn vào có lối **"Chụp ảnh thẻ (tự đọc)"** trên **mọi thiết bị** (iPhone/Android/desktop), không khóa theo máy.
- ⬜ Ảnh mặt trước CCCD rõ → OCR điền sẵn đúng **5 trường in ở mặt trước**: CCCD (12 số), họ tên, ngày sinh (ddMMyyyy→yyyymmdd), giới tính (Nam/Nữ), nơi thường trú.
- ⬜ **Ngày cấp KHÔNG đọc bằng OCR** (in ở mặt sau thẻ, THU-06 chỉ chụp mặt trước) → ô ngày cấp để trống + đánh dấu để **nhân viên nhập tay** (hoặc lấy từ QR nếu quét được).
- ⬜ Mọi trường OCR **sửa được** trước khi lưu; trường đọc không chắc **đánh dấu để nhân viên soát** (đi qua màn xác nhận dùng chung THU-01/02).
- ⬜ Ảnh quá mờ / OCR fail → **báo rõ, không điền bừa**, cho quay lại Nhập tay / Quét QR.
- ⬜ Số CCCD đọc ra **validate 12 số** (sai → ô đỏ, không tự lưu); các trường bám ràng buộc độ dài cột DB như THU-01/02 (HoVaTen ≤50…).
- ❌ Không đọc mặt sau thẻ; **không lưu khi nhân viên chưa xác nhận**; engine OCR chạy client hay gửi ảnh lên dịch vụ — **chốt ở `/tdd`** (cân nhắc PII vì gửi ảnh CCCD).

**Edge cases:**
| Tình huống | Hành vi mong muốn |
|---|---|
| Ảnh mờ/lóa/nghiêng → OCR sai nhiều | Nhân viên sửa tay, chụp lại, hoặc chuyển Nhập tay |
| OCR sai 1-2 ký tự số CCCD | Ô CCCD validate 12 số + cho sửa; không tự lưu |
| Chụp nhầm mặt sau / không phải CCCD | OCR không ra trường → báo, không điền bừa |
| Nơi thường trú 2 cấp mới / chữ xuống dòng | Ghép dòng, giữ dấu tiếng Việt; nhân viên soát (map địa chỉ vẫn ở tool lúc nạp) |

> Nguồn: user 07/10/2026 (sau BUG-14 — iPhone quét QR CCCD yếu hơn Android; chữ in to/rõ nên OCR đọc tốt). Lật quyết định "không OCR" của THU-01 — xem `TDD-decisions` §20. Engine + nơi chạy OCR: `/tdd`.

#### [NAP-01] Tool kéo hàng đợi + chống trùng

**Trạng thái:** 🔄 In Progress — **thêm yêu cầu 04/10/2026 (CHANGES #32, chưa code):** lưu nháp BỀN (địa chỉ+chi tiết+nơi cấp+tick+ảnh) xuống máy tool + tự xóa sau nạp/bỏ hàng đợi/xóa VPS · 2 chip Địa chỉ/Ảnh mỗi dòng · nút "Xử lý" to + cả dòng bấm · nạp chặn khi thiếu địa chỉ, cảnh báo khi thiếu ảnh + lối tắt bổ sung ảnh; phần đã code vẫn đúng, story ở lại hàng đợi. — task 44 (03/10) XONG: đồng bộ bỏ hồ sơ đã xóa khi "Kéo về" — server `GET /api/nap/da-xoa?since=` (đọc `audit_log` hành động `'xoa'` THU-05; KHÔNG suy từ vắng mặt trong `/keo`) + tool bỏ dòng staging `'cho'` trùng uuid (mốc incremental, dòng đã nạp/lỗi giữ nguyên) + toast "bỏ N hồ sơ đã xóa ở app". Kiểm mức 1: server 116 pytest (+6) · tool 165 pytest (+4) · webui build + 29 vitest · review-nghiepvu đủ. **Còn task 46/47 (redesign Nạp lô) + verify live Checkpoint 8** (gửi→xóa→kéo biến mất). Yêu cầu thêm 02/10/2026 (CHANGES #24: "Kéo về từ VPS" đồng bộ bỏ hồ sơ collector đã xóa ở app web — THU-05); phần đã code vẫn đúng, story quay lại hàng đợi để thêm đồng bộ xóa. task 38 (CHANGES #22) xong 02/10/2026: "Bỏ khỏi hàng đợi" (`DELETE /local/keo-ve/:uuid`, guard chỉ dòng đã nạp `'xong'`, tool-local — KHÔNG đụng prod) + "Nạp lại nhanh" dòng lỗi (tái dùng nạp lô 1 uuid). Kiểm: +5 test (132 pytest, gồm endpoint 401/404/409/200) · build · 29 vitest · review-nghiepvu 2/2. 2 nút UI là reuse mỏng của luồng đã live-verify — xác nhận thao tác khi chạy tool. Phần đã xong trước đó: ✅ Done 01/10/2026 — ① backend (kéo→staging, nạp lô lock→nạp→da-nap, +2 vá server) + ② UI 2 chế độ (ô tìm/IN HOA/chính tả/badge) + AC "kéo lại làm tươi bản chờ nạp" (CHANGES #11). Kiểm: tool 72 + server 56 test · Playwright 3vp · review-nghiepvu 9/9. (Tra cứu DB = QLY-01 task 22) — **thêm yêu cầu 07/10/2026 (CHANGES #43) — ĐÃ code (chờ verify máy CSDT):** drawer Chuẩn bị thêm ô **Ngày cấp CCCD** (`ODate` dd/mm/yyyy) điền sẵn + sửa được (lưu nháp bền `nhap_chuan_bi.ngay_cap`, rỗng→nạp ngày gốc, nạp vào `NgayCapCMT`) · bền hóa ô **Nơi cấp** luôn điền sẵn "Cục QLHC" cho CCCD 12 số kể cả khi danh mục nguồn chưa đồng bộ '00' (tự chèn option). Qua /reviewtdd §9.3a (1 Chặn migration + 2 Nên-sửa đã đóng, biên bản `tdd-review-07-10-2026.md`). Kiểm: tsc + 34 vitest + build + 308 pytest (+4 #43).
**Story:** Là nhân viên nạp DB, tôi muốn kéo danh sách học viên chờ nạp về tool, để xử lý và nạp vào DB.

**Steps to Complete:**
1. Đăng nhập tool, kết nối VPS bằng API key.
2. Kéo bản ghi `pending` về staging cục bộ (SQLite).
3. Hiển thị danh sách kèm đầy đủ thông tin + ảnh thô (như lưới UI.png).
4. Nạp lô vào khóa; hiển thị trạng thái từng dòng.

**Done khi:**
- ✅ Chỉ kéo bản ghi `pending`; bản `imported` không kéo lại (theo UUID).
- ✅ Kéo lại nhiều lần không nhân đôi trong staging.
- ✅ **Kéo lại làm tươi hồ sơ chưa nạp** (CHANGES #11): bấm "Kéo về từ VPS" lần nữa **cập nhật lại thông tin/ảnh mới nhất từ VPS** cho các hồ sơ đang **chờ nạp** trong tool — người thu nhận sửa trên app web sau khi tool đã kéo thì tool nhận bản mới; **giữ nguyên** hồ sơ đã nạp/đã lỗi. (Kéo KHÔNG khóa hồ sơ — app web còn sửa được tới lúc operator bấm nạp.)
- ✅ Tool hiển thị ảnh chân dung của từng học viên (như UI.png).
- ✅ **Màn nạp 2 chế độ** (CHANGES #6): **Nạp hồ sơ** (dropdown khóa chỉ chưa BC1 — NAP-02) · **Tra cứu DB** (QLY-01). Ở chế độ Nạp: hàng chờ VPS gộp **1 danh sách**, lọc **"Cần xử lý" (⚪ chờ + 🔴 lỗi, lỗi đẩy lên đầu) / "Đã nạp" (🟢)**.
- ✅ **Tìm trong list tải về** (hàng chờ VPS, chế độ Nạp hồ sơ) theo **tên (khớp cả có dấu lẫn không dấu)** hoặc **số CCCD**; ô tìm đặt trên đầu danh sách, màn hẹp thu gọn thành **nút kính lúp**. (CHANGES #10)
- ✅ **Tên học viên hiển thị IN HOA giữ dấu** ngay khi kéo về (khớp cách ghi DB).
- ✅ **Cảnh báo "sai chính tả" mức A:** tô dấu hiệu khi tên **thiếu dấu tiếng Việt / có số/ký tự lạ / khoảng trắng thừa** (không dùng từ điển tên — tránh báo nhầm); cảnh báo mềm, nhân viên tự sửa.
- ✅ **Nạp lô:** HV lỗi (trùng CCCD cùng khóa / thiếu dữ liệu…) **tô đỏ + nêu rõ lý do**; HV nạp được **tô xanh (kèm Số hồ sơ)**; HV khác trong lô vẫn nạp (EC-071).
- ⬜ **"Bỏ khỏi hàng đợi"** (CHANGES #22, #51): bỏ dòng khỏi hàng đợi staging của tool (SQLite cục bộ) — KHÔNG đụng DB prod, KHÔNG đụng máy chủ VPS. Tên nhẹ, TÁCH BẠCH với "Xóa khỏi DB" của Tra cứu DB (tránh xóa nhầm prod). Áp cho **mọi dòng**, không chỉ dòng đã nạp:
  - **Dòng 🟢 Đã nạp:** bỏ như cũ. VPS đã đánh dấu đã nạp nên kéo lại không mang về.
  - **Dòng ⚪ chờ nạp / 🔴 lỗi (CHANGES #51 — MỚI):** tool **ghi nhớ "bỏ qua"** uuid này; lần **"Kéo về từ VPS"** sau **không hiện lại nữa**. Dùng khi operator **không muốn nạp** hồ sơ đó vào DB (hồ sơ đã xóa bên app web nhưng tool kéo về từ trước nên còn sót, hoặc gửi nhầm/trùng). Vì sao cần "ghi nhớ bỏ qua": hồ sơ chờ có thể vẫn đang ở hàng chờ trên máy chủ — nếu chỉ xóa dòng cục bộ mà không nhớ, lần kéo sau nó quay lại.
- ⬜ **Bỏ nhiều dòng một lượt** (CHANGES #51): chọn nhiều hồ sơ trong danh sách rồi **"Bỏ khỏi hàng đợi"** một lần, kèm **bước xác nhận** (nêu rõ số dòng sẽ bỏ, không lấy lại được qua giao diện — gửi lại thì tạo hồ sơ mới ở app web).
- ⬜ **"Nạp lại nhanh"** dòng 🔴 lỗi (CHANGES #22): nút nạp lại ngay trên dòng lỗi (không phải chọn lại thủ công).
- ⬜ **Kéo về đồng bộ bỏ hồ sơ đã xóa** (CHANGES #24): bấm "Kéo về từ VPS", hồ sơ collector đã **xóa ở app web** (đánh dấu đã xóa trên VPS — THU-05) → **biến mất khỏi hàng chờ nạp** của tool (bỏ dòng staging `pending` tương ứng). Chỉ áp dòng **chưa nạp**; dòng đã nạp/đã lỗi giữ nguyên.
- ⬜ **Redesign UX màn Nạp lô — trạng thái sẵn sàng mỗi dòng** (CHANGES #26): mỗi hồ sơ chờ nạp hiện rõ `✔ Sẵn sàng` hoặc thiếu gì (`⚠ Thiếu địa chỉ` / `⚠ Thiếu ảnh` / `⚠ Chưa chọn giấy tờ`) — nhìn là biết nạp được hàng nào, không phải mở từng cái.
- ⬜ **Hai chip trạng thái chuẩn bị trên mỗi dòng** (CHANGES #32): mỗi dòng HV hiện **2 chip riêng** — `✓ Địa chỉ 2 cấp` / `✗ Chưa map địa chỉ` và `✓ Có hình` / `✗ Chưa có hình`; **mặc định ✗ (xám)** khi chưa làm. Nhìn là biết từng HV đã map địa chỉ / đã chuẩn bị ảnh chưa, không phải mở drawer. (Cụ thể hóa dòng "trạng thái sẵn sàng" #26.)
- ⬜ **Nạp lô — chặn/cảnh báo theo mức bắt buộc** (CHANGES #32): **thiếu địa chỉ 2 cấp → CHẶN nạp** dòng đó (địa chỉ bắt buộc); **thiếu ảnh → vẫn cho nạp nhưng CẢNH BÁO rõ** "N học viên nạp thiếu ảnh — bổ sung sau ở Tra cứu DB" (ảnh không bắt buộc, bổ sung qua QLY-05). Sau nạp, nếu có HV thiếu ảnh → hiện **lối tắt mở Tra cứu DB lọc "chưa ảnh"** để bổ sung ngay.
- ⬜ **Chọn nhiều HV để nạp vào khóa chưa BC1 thuận tiện** (CHANGES #26): nút **"Chọn tất cả sẵn sàng"** tick mọi dòng đủ điều kiện (bỏ qua dòng còn thiếu); thanh hành động dính đáy một nút chính **"Nạp N học viên"**.
- ⬜ **Ngăn "Chuẩn bị" trượt ra khi cần** (CHANGES #26): bấm "Chuẩn bị" ở một dòng → ngăn trượt từ phải (map địa chỉ + giấy tờ + ảnh); lưu xong dòng chuyển `✔ Sẵn sàng`. Bỏ cột chuẩn bị cố định để màn gọn, bớt rối.
- ⬜ **Mở hồ sơ dễ thao tác** (CHANGES #32): **cả dòng HV bấm được** để mở ngăn Chuẩn bị + thêm **nút "Xử lý" to, rõ bên phải** mỗi dòng — thay nút/icon nhỏ, tránh bấm nhầm, nhìn thấy ngay chỗ bấm.
- ⬜ **Lưu nháp BỀN khi chuẩn bị hồ sơ** (CHANGES #32, #43): mọi chỉnh sửa khi chuẩn bị (địa chỉ 2 cấp đã map, chi tiết, nơi cấp, **ngày cấp CCCD**, tick giấy tờ, **và ảnh đã đổi nền**) được **lưu xuống máy tool**, không mất khi tải lại trang / đóng mở tool. Nháp **tự xóa** khi: nạp xong · "Bỏ khỏi hàng đợi" · hồ sơ bị xóa trên app web (đồng bộ xóa). Nhờ đó 2 chip trạng thái phản ánh đúng kể cả sau khi mở lại tool.
- ⬜ **Ngày cấp CCCD — ô điền sẵn + sửa được ở drawer Chuẩn bị** (CHANGES #43): drawer Chuẩn bị có **ô "Ngày cấp"** riêng (chọn ngày `dd/mm/yyyy`), **điền sẵn** ngày cấp đã kéo về từ VPS và cho nhân viên **sửa được** trước khi nạp (giống ô Nơi cấp); giá trị đã sửa được lưu nháp bền và dùng khi nạp vào DB (`NgayCapCMT`). Trước đây ngày cấp chỉ hiện dạng chữ đọc, không sửa được.
- ⬜ **Nơi cấp luôn điền sẵn đúng cho CCCD 12 số** (CHANGES #43): ô "Nơi cấp căn cước" ở drawer **luôn hiển thị sẵn "Cục QLHC"** khi số CCCD có 12 chữ số — kể cả khi danh mục nơi cấp trên máy đó chưa được đồng bộ đủ (trước đây ô bị để trống trong trường hợp này, trông như không tự chọn). Vẫn sửa được như cũ; dữ liệu nạp không đổi.
- ⬜ **Dialog nạp 3 pha** (CHANGES #26): bấm "Nạp N học viên" → (1) xác nhận nạp vào khóa nào, bao nhiêu sẵn sàng/bỏ qua · (2) thanh tiến độ N/tổng + tên HV đang nạp · (3) **báo cáo kết thúc**: mấy HV vào DB, mấy lỗi + **lý do từng HV** + nút **"Nạp lại lỗi"** (chọn lại đúng dòng lỗi). Lỗi 1 HV không hỏng cả lô.
- ⬜ **Nút "Xem trong DB"** (CHANGES #26): ở dòng đã nạp + trong báo cáo → nhảy sang chế độ **Tra cứu DB**, mở đúng khóa đích + làm nổi HV vừa nạp, để kiểm HV đã vào DB đúng chưa.
- ❌ Không kéo bản ghi đã nạp/đã xóa.

**Edge cases:**
| Tình huống | Hành vi mong muốn |
|---|---|
| VPS/tunnel down khi kéo | Tool vẫn xử lý bản ghi đã kéo (staging); báo lỗi, cho thử lại |
| Nạp lô, vài HV lỗi | Dòng lỗi 🔴 + lý do, dòng xong 🟢; lô vẫn chạy hết (EC-071) |
| Tên thiếu dấu / ký tự lạ (từ QR hỏng hoặc gõ tay) | Cảnh báo mức A, cho sửa; không chặn cứng |
| Kéo xong, người thu nhận sửa thông tin/ảnh trên app web | Kéo lại làm tươi bản 'chờ nạp'; bản đã nạp/đã lỗi giữ nguyên (CHANGES #11) |
| Kéo lại mà **địa chỉ gốc đã đổi** trên app web, dù đã có nháp bền | Reset riêng **địa chỉ 2 cấp** đã map (cả bản nháp bền) + chip địa chỉ về `✗` + thông báo "địa chỉ của N hồ sơ đã đổi, cần map lại"; **giữ nguyên** ảnh đã đổi nền, tick giấy tờ, nơi cấp (CHANGES #32, mở rộng BUG-04) |
| Bỏ qua dòng ⚪ chờ / 🔴 lỗi rồi bấm **"Kéo về từ VPS"** lại | Dòng đã bỏ qua **không hiện lại** (tool nhớ uuid "bỏ qua"); nháp đã chuẩn bị của dòng đó (gồm ảnh) cũng bị dọn (CHANGES #51) |
| Hồ sơ đã bỏ qua được collector **gửi lại** trên app web (hồ sơ mới = uuid mới) | **Hiện lại bình thường** ở hàng chờ — "bỏ qua" chỉ gắn với uuid cũ, không chặn hồ sơ mới (CHANGES #51) |

> Nguồn: CAP-004 · BR-015 · EC-062 · EC-071 · CHANGES #6 · CHANGES #11 · CHANGES #32 · CHANGES #51

#### [NAP-02] Chọn mô tô/ô tô + khóa chưa lập BC1

**Trạng thái:** ✅ Done
**Story:** Là nhân viên nạp DB, tôi muốn lọc khóa theo mô tô/ô tô và chỉ khóa chưa báo cáo, để gán học viên vào đúng khóa còn nhận.

**Done khi:**
- ✅ Chọn Mô tô → chỉ hiện khóa hạng bắt đầu `A`; chọn Ô tô → khóa `B/C/D/E/F`.
- ✅ Dropdown chỉ hiện khóa `TrangThai=1` và chưa có dòng trong `BaoCaoI`.
- ✅ Chọn khóa → suy ra `MaLoaiHs` (A*→1, còn lại→2), `HangGPLX`, `HangDaoTao`, `MaSoGTVT` theo khóa.
- ❌ Khóa đã lập BC1 không xuất hiện.

> Nguồn: CAP-005 · BR-007, BR-012 · verify DB 30/09/2026 (moto MaLoaiHs=1)

#### [NAP-03] Map địa chỉ cũ→mới + chọn tay

**Trạng thái:** ⚠️ Partial — 02/10/2026 (CHANGES #19). Thêm tự tách địa chỉ gốc kéo về → điền sẵn Tỉnh/Huyện/Xã + Chi tiết (lượt 3 bắt cả xã không tiền tố), operator bấm Chuyển đổi; giữ map cốt lõi + chọn tay. Kiểm: webui 29 test (tách địa chỉ) + build + Playwright (tự điền đúng). **Chờ verify trên tool thật.**
**Story:** Là nhân viên nạp DB, tôi muốn nhập địa chỉ cũ hoặc mới và hệ thống tự đổi sang đơn vị hành chính mới, để không sai địa chỉ sau sáp nhập 2025.

**Steps to Complete:**
1. Nhận địa chỉ text (từ QR hoặc nhập).
2. Tra bảng phụ `DM_DVHC_MAP` (nguồn dữ liệu ánh xạ cũ→mới).
3. Nối theo tên (tỉnh mới, xã mới) về `DM_DVHC` (`TrangThai=1`) lấy `MaDvhc`+`MaDVQL` của DB.

**Done khi:**
- ✅ **Tự tách địa chỉ gốc kéo về từ VPS** (`noi_tt_raw`, dạng "…, Xã X, Huyện Y, Tỉnh Z") thành Tỉnh/Huyện/Xã **điền sẵn** vào ô map, phần dư (số nhà/thôn) điền sẵn ô Chi tiết; operator chỉ bấm "Chuyển đổi sang xã mới". (CHANGES #19)
- ✅ Tách không ra / địa chỉ viết tắt / thiếu → để ô trống cho gõ tay (không chặn); operator luôn sửa được các ô trước khi map.
- ✅ Địa chỉ mới hoặc cũ khớp map → điền đúng `NoiTT_MaDVHC`+`NoiTT_MaDVQL` (và `NoiCT_*`).
- ✅ Tên hiển thị theo DB (vd "Thành phố Đồng Nai"), không theo dataset.
- ✅ Chọn tay Tỉnh→Xã bằng **ô gõ-để-lọc** (CHANGES #29): gõ tên (khớp cả **không dấu** nhờ `boDau`) → danh sách gợi ý lọc dần → bấm/Enter chọn; thay 2 dropdown cũ (xã dài, cuộn mệt). Tỉnh lấy từ `DM_DVHC` (DISTINCT `MaDVQL`, `TrangThai=1`); Xã qua `usp_DM_DVHC_SelectDanhSachXaPhuongTheoTinh` + lọc `TrangThai=1`. (SP `usp_DM_DVHC_SelectAll_Tinh` chỉ trả đơn vị cũ TW/TI — không dùng được cho model 2 cấp mới; xem CHANGES #2.)
- ❌ Không tự đoán khi xã bị chia — cho chọn tay.

**Edge cases:**
| Tình huống | Hành vi mong muốn |
|---|---|
| Xã bị chia (isDividedWard) / không khớp map | Popup chọn tay Tỉnh/Xã mới |

> Nguồn: CAP-006 · BR-006 · EC-032 · verify phủ 3321/3321 xã (30/09/2026)

#### [NAP-04] Căn ảnh + xóa phông trắng + xuất .jp2

**Trạng thái:** ⚠️ Partial — code xong (commit `37ad996`/`ce5849f`), **chờ verify máy CSDT** (mở .jp2 bằng app cũ). yêu cầu bổ sung UI ảnh 02/10/2026 (CHANGES #23: hiện ảnh đã chỉnh + mở lại chỉnh tiếp + nhãn nút lưu rõ); code cũ (CHANGES #19+#20) vẫn đúng, story quay lại hàng đợi để làm phần UI mới. Trình chỉnh ảnh: nạp sẵn ảnh VPS + grab 2 trục + xoay (−90/+90 + nghiêng) + khung chân dung mẫu + warm-up rembg (u2net); xử lý qua canvas (WYSIWYG). Kiểm: webui build + 29 test + Playwright. **Còn kiểm tay 'mở .jp2 bằng app cũ' (1c) + verify trên tool thật.**
**Story:** Là nhân viên nạp DB, tôi muốn căn khung chân dung, xoay cho thẳng, xóa phông thành nền trắng và xuất `.jp2`, để ảnh đúng chuẩn app cũ.

**Steps to Complete:**
1. Hiện ảnh thô; **khung crop cố định tỷ lệ 3:4** + **khung chân dung mẫu mờ chồng lên** (ô-van đầu + đường căn mắt/cằm) để biết đặt mặt vào đâu; tự nhận diện mặt gợi ý vị trí; **grab di chuyển + phóng to/thu nhỏ + xoay** (kéo chuột/chạm) để canh mặt vào giữa; chỉnh tay hoặc thay ảnh khác.
2. Xóa phông → **nền trắng** (`rembg`); xem trước.
3. Khi bấm Nạp mới xuất `.jp2` (`Pillow`) và ghi file.

**Done khi:**
- ✅ **Ảnh thô đã kéo về từ VPS được nạp sẵn vào trình chỉnh** (có ngay trong khung crop 3:4 để căn + đổi nền), không bắt operator chọn lại file; vẫn cho chọn file khác nếu muốn thay. (CHANGES #19)
- ✅ **Grab tự do 4 hướng:** kéo ảnh trái/phải **và** lên/xuống để căn mặt (không bị ghim một trục ở mức zoom gốc); vùng lộ ra khi kéo → nền trắng. (CHANGES #20)
- ✅ **Phóng to/thu nhỏ linh hoạt:** thang zoom **mặc định ở GIỮA = cỡ gốc** (kéo trái = thu nhỏ **dưới cỡ ban đầu**, kéo phải = phóng to); **lăn chuột** trên khung cũng phóng/thu. (CHANGES #21)
- ✅ **Xoay ảnh:** nút xoay nhanh **−90°/+90°** + thanh **tinh chỉnh độ nghiêng** (vài độ) để làm thẳng mặt; ảnh xoay rồi mới crop + xuất. (CHANGES #20)
- ✅ **Khung chân dung mẫu** mờ chồng lên khung crop (ô-van đầu + đường căn) để operator biết căn; **chỉ là hướng dẫn, KHÔNG dính vào ảnh `.jp2` xuất ra**. (CHANGES #20)
- ✅ **Xóa phông nhanh:** bật **warm-up rembg lúc khởi động tool** (bỏ `TOOL_SKIP_WARMUP=1` ở `tool-start.bat`) → ảnh đầu chỉ chờ 1 lần lúc mở tool, ảnh sau <5s (TDD §9.2); GIỮ model u2net (không đổi chất lượng). (CHANGES #20)
- ✅ File `.jp2` (JPEG 2000) **tỷ lệ 3:4, nền trắng, RGB**; kích thước **353×471 (~48 KB, khớp cụm phổ biến nhất của app cũ)** — hoặc 480×640 nếu chọn nét hơn; mở được bằng app cũ.
- ✅ Ghi file tại `<IMG_PATH_CSDT>\<MaKhoaHoc>\<MaDK>.jp2` (**dùng lại `MaDK` do SP trả về**, không sinh timestamp mới — verify 39.648 HV khớp 100%, TDD §9.2); DB lưu `DuongDanAnh`, `ChatLuongAnh=1`.
- ✅ `IMG_PATH_CSDT` đọc từ `QTHT_ThamSoHT`, không hard-code.
- ⬜ **Hiện ảnh đã chỉnh sau khi "Dùng ảnh này"** (CHANGES #23): bấm "Dùng ảnh này" xong, khung ảnh ở panel hiển thị **đúng ảnh vừa chỉnh** (bản xem trước PNG từ `/local/anh/xu-ly`), **không chỉ hiện icon check** — để operator xem lại ảnh mình đã chuẩn bị. (Lý do kỹ thuật: `.jp2` trình duyệt không render được nên phải dùng bản PNG.)
- ⬜ **Mở lại trình chỉnh nạp sẵn ảnh đã chỉnh mới nhất** (CHANGES #23): bấm "Mở trình chỉnh ảnh" lần sau → nạp **ảnh đã chỉnh gần nhất** (nếu đã có) để chỉnh tiếp/thay, thay vì quay về ảnh thô VPS; chưa chỉnh lần nào thì vẫn nạp ảnh thô như cũ.
- ⬜ **Nút lưu ảnh rõ + nổi bật** (CHANGES #23): trong trình chỉnh, nút áp dụng ảnh ("Dùng ảnh này") đặt **nổi bật** + badge kết quả ghi rõ ảnh **đã xử lý, bấm nút để áp dụng** — tránh operator dừng ở bước "Xử lý ảnh" rồi tưởng đã xong.
- ⬜ **"Dùng lại ảnh gốc"** (CHANGES #26): trong trình chỉnh, nút quay về **ảnh thô học viên gửi trên VPS (bản nguyên gốc, chưa xử lý lần nào)** — bỏ mọi chỉnh sửa để căn/xóa phông lại từ đầu khi đã chỉnh hỏng; xác nhận nhanh trước khi bỏ. Chỉ hiện khi còn ảnh thô VPS cho hồ sơ đó. (Khác nút "Mở lại trình chỉnh" vốn nạp ảnh đã chỉnh gần nhất — nút này đi xa hơn, về tận ảnh gốc.)
- ❌ Không xử lý ảnh ở điện thoại.

**Edge cases:**
| Tình huống | Hành vi mong muốn |
|---|---|
| Chưa có ảnh khi nạp | Cảnh báo mềm, vẫn cho nạp |
| Ghi file xong nhưng SP nạp lỗi | Dọn file, không để mồ côi |

> Nguồn: CAP-007 · BR-010, BR-019 · EC-022, EC-041

#### [NAP-05] Sinh Số hồ sơ + nạp DB qua 1 SP gộp app cũ + giấy tờ

**Trạng thái:** ✅ Done — 01/10/2026, nạp qua 1 SP gộp app cũ hướng A (CHANGES #4/#5); AS-003 nạp thật 17/17 khớp app cũ (user đã mở app cũ đối chiếu). **EC-010 hoãn Phase 2:** khóa bản ghi VPS khi 2 máy cùng nạp cần `pending→importing` trên VPS (HTG-02/NAP-01, chưa dựng); chống trùng cùng máy đã có (idempotent UUID).
**Story:** Là nhân viên nạp DB, tôi muốn nạp học viên vào khóa qua stored procedure có sẵn, để hồ sơ hiện đúng trên app cũ.

**Steps to Complete:**
1. Sinh `SoHoSo` = MAX+1 (3 chữ số) trong khóa (nếu SP không tự sinh).
2. Gọi **1 SP gộp `usp_QuangLA_PM4_ThuNhanHS_ThemMoiCapNhat`** — chính SP màn "Thu nhận Hồ sơ cấp mới" của app cũ dùng (32 tham số khớp 1:1 form) — ghi NguoiLX + NguoiLX_HoSo + giấy tờ + `CHON_IN_GPLX` trong một lần, atomic (SP tự lo transaction).
3. Ghi file ảnh; đánh dấu bản ghi VPS = `da_nap` (kèm MaDK).

**Done khi:**
- ✅ Mở app cũ (màn Thu nhận HS) tại đúng khóa: dòng học viên hiện đúng Số hồ sơ, Họ tên, Giới tính, Ngày sinh, CMT/HC, Nơi ĐK thường trú, Đường dẫn ảnh, Ngày nhận HS **khớp giá trị đã nhập**; mở ảnh chân dung xem được; tab Giấy tờ có đủ dòng đã tick.
- ✅ `SoHoSo` đúng thứ tự khóa (khóa 55 HV → HV mới 056); `MaHTCap=CM_VN`, `TT_XuLy=03`, `GiayCNSK=1`.
- ✅ **Giá trị khớp app cũ (verify AS-003 01/10/2026):** `HoVaTen`/`HoVaTenIn` **IN HOA giữ dấu**; `MaQuocTich=VNM` (không "VN" — vỡ FK); `NoiTT`/`NoiCT` **trống**, địa chỉ hành chính lấy từ mã DVHC, ô Chi tiết riêng (không nhét tên xã vào NoiTT gây lặp); `DonViHocLX=NULL`; `CHON_IN_GPLX=2`.
- ✅ Giấy tờ mặc định nộp đủ theo `DM_LoaiHSo_GiayTo` (hạng B/A → 3 giấy tờ), `TenGT` lấy đầy đủ từ `DM_GiayTo`; **ghi theo trạng thái tick cuối của người dùng** (bỏ tick được và được tôn trọng khi nạp, không auto ghi đè về "đủ").
- ✅ Nạp trong transaction; lỗi giữa chừng → rollback, giữ `pending`.
- ❌ Không INSERT/UPDATE bảng trực tiếp cho dữ liệu hồ sơ (chỉ qua SP gộp). **Ngoại lệ (01/10/2026, CHANGES #5):** được UPDATE thẳng 5 cột ảnh `NguoiLX_HoSo` (`DuongDanAnh`, `ChatLuongAnh`, `TT_XuLy`, `NgayThuNhanAnh`, `NguoiThuNhanAnh`) sau khi ghi `.jp2` — vì SP gộp không ghi ảnh (hướng A, TDD §10.3).

**Edge cases:**
| Tình huống | Hành vi mong muốn |
|---|---|
| Mất kết nối SQL Server giữa lúc nạp | Rollback, bản ghi giữ `pending`, cho thử lại |
| Nạp lô nhiều HV, 1 HV lỗi | Các HV còn lại vẫn nạp; HV lỗi giữ pending + báo dòng lỗi |
| Nạp đồng thời tranh Số hồ sơ | Sinh SoHoSo trong khóa/transaction, retry nếu trùng |
| Hai tool (2 máy) cùng nạp một bản ghi | Khóa bản ghi khi chuyển `importing`; tool thứ 2 báo "đang được nạp", không tạo HV thứ 2 |
| Bấm nút "Nạp" hai lần (double-click) | Disable nút sau lần đầu + idempotent theo UUID; chỉ tạo 1 HV |

> Nguồn: CAP-008 · BR-001, BR-002, BR-003, BR-008, BR-009 · EC-011, EC-061, EC-071

#### [NAP-06] Kiểm trùng CCCD trong khóa

**Trạng thái:** ✅ Done — 01/10/2026: kiểm sớm `GET /local/kiem-trung-cccd` + chốt chặn server-side trong `nap_mot_hv`/applock (SP không bắt trùng khi nạp mới); test live 5/5. Cảnh báo trùng đã nâng thành **banner nổi bật (nền/viền/icon) nêu rõ nguyên nhân** (CCCD + Số hồ sơ) theo chuẩn UX ⑥ — verify Playwright 375/1440.
**Story:** Là nhân viên nạp DB, tôi muốn được cảnh báo khi CCCD đã có trong khóa, để không tạo hồ sơ trùng.

**Done khi:**
- ✅ Trước nạp, nếu `SoCMT` đã có trong cùng `MaKhoaHoc` → cảnh báo, không nạp.
- ✅ Cùng CCCD ở khóa khác thì cho phép.
- ❌ Không chặn trùng toàn hệ thống.

> Nguồn: CAP-009 · BR-005 · EC-012

#### [KHO-01] Tạo khóa học

**Trạng thái:** ✅ Done — 02/10/2026. Code (task 21) + **user tạo khóa thật trên prod, verify OK**. API tool `GET /local/khoa-hoc/hang-dt` + `POST /local/khoa-hoc/tao` (gọi `usp_KhoaHoc_Insert` — mã tự sinh; `HangGPLX` suy từ `DM_HangGPLX.MaHang WHERE MaHangMoi=hạng ĐT`; hằng MaCSDT=70004/MaSoGTVT=70/TrangThai=1; đếm HV=0; đọc lại MaKH vì SP không trả) + màn "Tạo khóa" webui (5 bắt buộc + 4 tùy chọn, tự điền HangGPLX/tuổi/thời gian ĐT). Kiểm: tool **81 test** · webui build + 15 test · typecheck · verify live end-to-end (dropdown DB thật, tạo khóa + app cũ đối chiếu).
**Story:** Là nhân viên nạp DB, tôi muốn tạo khóa học mới trong tool, để có khóa gán học viên mà không cần mở app cũ.

**Steps to Complete:**
1. Chọn Hạng đào tạo từ `DM_HangDT` (mô tô/ô tô/nâng hạng).
2. Nhập Tên khóa, Ngày KG, Ngày BG, Tổng số HV; (tùy chọn) Số QĐ, Ngày QĐ, Ngày thi, Ghi chú.
3. Gọi `usp_KhoaHoc_Insert` (mã khóa tự sinh).

**Done khi:**
- ✅ Tạo khóa qua `usp_KhoaHoc_Insert`; mã `MaKH` tự sinh (mã hóa hạng), hiển thị trong app cũ.
- ✅ 5 trường bắt buộc; `HangGPLX` suy từ hạng ĐT qua `DM_HangGPLX.MaHangMoi`; `MaCSDT=70004`, `MaSoGTVT=70`, `TrangThai=1`.
- ✅ Tuổi tối thiểu + thời gian ĐT auto từ `DM_HangDT`.
- ❌ Không sửa/xóa khóa (dùng app cũ nếu cần).

> Nguồn: CAP-013 · BR-017

---

### 🔵 SHOULD (nên có, không gấp)

#### [THU-04] Cảnh báo trùng CCCD khi thu nhận (app web)

**Trạng thái:** ✅ Done — 01/10/2026. Cảnh báo trùng CCCD app web (task 31): `GET /api/ho-so/kiem-trung` soi hàng đợi pending/importing + banner mềm ở màn xác nhận, vẫn cho gửi. Kiểm: server 67 test (+5 kiểm-trùng, +validate cccd) · review-baomat không lỗ CHẶN (giữ hiển thị tên đầy đủ người gửi theo chủ dự án chốt) · deploy live. Đối chiếu DB thật vẫn ở NAP-06.
**Story:** Là nhân viên thu nhận, tôi muốn được cảnh báo khi căn cước vừa nhập đã có hồ sơ chưa nạp trong hàng đợi, để tránh gửi trùng một học viên lên hệ thống.

**Done khi:**
- ✅ Khi gửi (hoặc ngay sau khi có đủ số CCCD), app hỏi VPS xem CCCD này **đã có hồ sơ `pending`/`importing` trong hàng đợi CSDT 70004** chưa (mọi nhân viên, không chỉ của mình).
- ✅ Có trùng → **cảnh báo mềm, NỔI BẬT** (banner nền/viền/icon theo chuẩn UX ⑥) nêu rõ **ai gửi + lúc nào**; **vẫn cho gửi** (nhân viên tự quyết — có thể là cố ý bổ sung/gửi lại).
- ✅ Không chặn cứng; chốt chặn trùng thật vẫn ở bước nạp (NAP-06, đối chiếu DB thật).
- ❌ App web **không** đối chiếu DB thật (không kết nối SQL Server) — chỉ soi hàng đợi chưa nạp của CSDT.

**Edge cases:**
| Tình huống | Hành vi mong muốn |
|---|---|
| Mất mạng lúc hỏi trùng | Bỏ qua cảnh báo, vẫn cho gửi (giữ nháp như luồng offline); không chặn |
| Gửi lại chính hồ sơ của mình (sửa/bổ sung, cùng uuid) | Không coi là trùng |

> Nguồn: user 01/10/2026 (CHANGES #13) · liên quan NAP-06 · chuẩn cảnh báo ⑥

#### [THU-05] Xóa hồ sơ đã gửi (app web)

**Trạng thái:** ⚠️ Partial — desktop chọn-nhiều-để-xóa (CHANGES #30, 03/10/2026) code XONG: `DaGui.tsx` cột ô tích chỉ ở dòng pending + "chọn tất cả Chờ nạp trên trang" + thanh thao tác `hidden lg:flex` (Đã chọn N · Bỏ chọn · Xóa N) + dialog xác nhận, lặp `xoaHoSo` (DELETE /api/ho-so/:uuid) phía client, phân biệt lỗi 409 (vừa bị nạp) ≠ lỗi mạng (EC1). Mobile giữ xóa lẻ trong modal. Kiểm mức 1: build + typecheck sạch · 24 vitest · review-nghiepvu đủ (2 ❔ đã tự xác minh: endpoint `xoaHoSo` + EC1 409). **CHƯA chụp Playwright.** task 41 (03/10/2026) XONG: server `DELETE /api/ho-so/:uuid` soft-delete CAS + phân quyền IDOR + audit · webapp nút Xóa + panel xác nhận 2 bước + chú thích khi đã nạp. Kiểm: server 100 pytest (7 test xóa) · webapp build + 24 vitest · review-nghiepvu đủ. **CÒN:** Done khi #5 "đồng bộ tool kéo về bỏ dòng đã xóa" = task 44 (NAP-01); chưa deploy VPS + verify Playwright/live (Checkpoint 8). Yêu cầu mới 02/10/2026 (CHANGES #24) + popup/copy (CHANGES #26). Chữ PRD đã khớp code (CHANGES #27: edge 404 chống IDOR, copy "máy tính" thay "DB"). **Thêm 03/10/2026 (CHANGES #30): desktop chọn-nhiều-để-xóa** — cột ô tích (chỉ dòng Chờ nạp) + thanh "Đã chọn N · Xóa N" + dialog xác nhận, lặp `DELETE` client, tái dùng mẫu xóa-hàng-loạt của QuanTriHoSo (HTG-03); mobile giữ xóa lẻ trong modal. Phần xóa lẻ đã code (task 41) vẫn đúng, chỉ thêm nhánh desktop chọn-nhiều.
**Story:** Là nhân viên thu nhận, tôi muốn xóa hồ sơ mình đã gửi nhầm/không dùng trong danh sách "Hồ sơ đã gửi", để nó biến mất khỏi hàng chờ nạp của tool khi nạp DB kéo về.

**Done khi:**
- ⬜ Màn **"Hồ sơ đã gửi"** (`/app/da-gui`) có nút **Xóa** cho mỗi hồ sơ **chưa nạp** (⚪ Chờ nạp); xác nhận 2 bước trước khi xóa.
- ✅ **Desktop: chọn nhiều để xóa** (CHANGES #30, code xong — chờ chụp Playwright): bảng có **cột ô tích chỉ ở dòng Chờ nạp** (đã/đang nạp không chọn được — khớp luật server chặn xóa); ô tích đầu cột = **chọn tất cả hồ sơ Chờ nạp trên trang**; **thanh thao tác nổi "Đã chọn N · Bỏ chọn · Xóa N hồ sơ"** chỉ hiện khi chọn ≥1 → dialog xác nhận (không khôi phục), xóa bằng lặp `DELETE /api/ho-so/:uuid` phía client. Tái dùng mẫu xóa-hàng-loạt của màn admin (QuanTriHoSo/HTG-03). **Mobile giữ nguyên** xóa lẻ trong modal chi tiết, KHÔNG thêm chọn nhiều (chốt phương án A, 03/10/2026). Nút Xóa lẻ trong modal vẫn giữ.
- ⬜ **Chỉ xóa hồ sơ CHƯA NẠP** (`pending`); hồ sơ **đã nạp/đang nạp** (`importing`/`imported`) **không xóa được** ở app web (phải xử lý ở tool — QLY-03/QLY-08), ẩn/khóa nút + báo lý do.
- ⬜ **Phân quyền:** nhân viên thu nhận chỉ xóa **hồ sơ của chính mình**; **admin** xóa được bất kỳ hồ sơ nào.
- ⬜ **Xóa mềm trên VPS** (đánh dấu "đã xóa" + ai xóa/lúc nào), KHÔNG xóa cứng → giữ vết truy; hồ sơ đã xóa không còn trả về khi tool kéo.
- ⬜ **Đồng bộ sang tool:** khi tool bấm **"Kéo về từ VPS"**, hồ sơ đã xóa ở app web **biến mất khỏi hàng chờ nạp** của tool (xem NAP-01 — kéo về đồng bộ bỏ).
- ⬜ **Popup xác nhận + hướng dẫn khi xóa** (CHANGES #26): nút Xóa mở panel xác nhận 2 bước (tái dùng mẫu panel đỏ của tool), copy: *"Xóa hồ sơ này khỏi hàng chờ nạp? Hồ sơ chưa nạp vào máy tính nên còn xóa được. Lần tới máy nạp bấm 'Kéo về', hồ sơ biến mất khỏi danh sách chờ nạp. Xóa rồi không lấy lại được — gửi nhầm thì tạo hồ sơ mới."* Nút: **Giữ lại / Xóa hồ sơ**. (Dùng "máy tính" thay "DB" — tránh lộ từ kỹ thuật cho người thu nhận, theo luật nội dung.)
- ⬜ **Hồ sơ đã/đang nạp: khóa nút + chú thích** (CHANGES #26): thay nút Xóa bằng dòng chú thích *"Hồ sơ đã được máy nạp xử lý. Cần gỡ hay sửa thì báo người nạp thao tác trên máy tính."*
- ❌ Không cho collector xóa hồ sơ đã nạp. ❌ Không xóa cứng bản ghi VPS (giữ vết).

**Edge cases:**
| Tình huống | Hành vi mong muốn |
|---|---|
| Hồ sơ vừa được tool nạp (đổi sang `importing`/`imported`) đúng lúc collector bấm xóa | Chặn xóa, báo "hồ sơ đã/đang được nạp, không xóa được ở đây" |
| Collector xóa hồ sơ của người khác (không phải admin) | Chặn — trả **404** (chống IDOR, không lộ hồ sơ tồn tại, như `_cua_minh`), chỉ xóa của mình |

> Nguồn: user 02/10/2026 (CHANGES #24, buổi verify #22) · liên quan NAP-01 (kéo về đồng bộ xóa) · phân quyền HTG

#### [QLY-01] Tra cứu & sửa hồ sơ đã có

**Trạng thái:** ⚠️ Partial — chờ verify máy CSDT. **Mở rộng 06/10/2026 (CHANGES #40, đã code): modal sửa nhân thân +combo địa chỉ 2 cấp (Tỉnh/Xã) + nơi cấp căn cước (DM_DVHC, có '00' Cục QLHC) + ngày cấp CCCD — ngang TCB-03; bỏ-trống-giữ-cũ, guard BC1 giữ nguyên.** Toàn bộ 6 task code XONG: task 22 (tra cứu + sửa nhân thân) · 34 (backend `/anh`+`/anh-thumb` `.jp2`→PNG) · 35 (UI: avatar lưới lazy 3-ca · modal ảnh lớn + đường dẫn `DuongDanAnh` + cảnh báo 404/422 · click ảnh→AnhModal) · 36 (thống kê Tổng·Thiếu ảnh + badge BC1 cấp khóa [phương án A] + nút đổi-khóa/xóa nhanh ra lưới, ẩn khi BC1). Kiểm mức 1: 125 pytest · 29 vitest · build sạch · review-nghiepvu task 35 3/3 + task 36 2/2. **Chờ verify máy CSDT (SQL Server GPLX_CSDT live):** render ảnh thật + 3 ca avatar + cảnh báo 404/422 + click→chỉnh→lưu đè + đổi-khóa/xóa nhanh trên HV thật (ghi prod + chặn BC1). Đã verify live trước đó: tra cứu khóa + lưới HV (khóa B-K149, 55 HV). Mở rộng yêu cầu 02/10/2026 (CHANGES #22: hiện ảnh chân dung + avatar lưới + đường dẫn ảnh + cảnh báo file thiếu + thống kê đầu khóa + nút đổi-khóa/xóa nhanh ra list). Phần đã code trước đó (chờ verify prod): **Lát 1 (đọc, task 22) xong + verify live:** Tra cứu DB — tìm khóa mọi khóa kể cả BC1 + lưới HV theo khóa (`usp_NguoiLX_Select_By_MaKH`) + tìm trong lưới + xem chi tiết (verify live: khóa B-K149, 55 HV đúng). **Lát 2 (sửa, task 22) code xong — CHỜ VERIFY PROD:** sửa **thông tin nhân thân** (họ tên/ngày sinh/giới tính/CCCD/địa chỉ TT) qua `usp_NguoiLX_Update`, đọc lại full bản ghi để giữ cột không sửa; chặn sửa khi khóa đã BC1 (BR-012). **Thu hẹp phạm vi:** bỏ `usp_NguoiLX_HoSo_Update` khỏi QLY-01 (SP ghi đè 65 cột gồm kết quả thi/báo cáo → rủi ro) — ảnh để QLY-05, đổi khóa QLY-02 (CHANGES #17). Kiểm: tool **101 test** + webui **19 test** + build. Chờ bạn verify ghi prod thật + chặn BC1 live. **BUG-02 (03/10, đã sửa):** lưới Tra cứu DB (`ds_ho_so`) trước dùng SP app cũ lọc cứng `TT_XuLy IN ('03','04')` → ẩn HV chưa ảnh (bộ lọc "Chưa ảnh" luôn rỗng); nay thay SELECT riêng bỏ lọc TT_XuLy (không sửa SP cũ). +1 test hồi quy. Xem `docs/BUGS.md`. (Ghi chú: con số "55 HV" verify trước đây là số đã BỊ SP lọc — thực tế khóa có 57.)
**Story:** Là nhân viên nạp DB, tôi muốn tra cứu và sửa hồ sơ học viên đã có trong DB, để thay phần lớn thao tác của app cũ.

**Done khi:**
- ✅ **Chế độ "Tra cứu DB"** (CHANGES #6): **tìm khóa theo tên khóa hoặc mã khóa — MỌI khóa, kể cả đã lập BC1** (khác dropdown nạp của NAP-02 vốn ẩn khóa BC1). Chọn khóa → lưới học viên theo khóa (`usp_NguoiLX_Select_By_MaKH`) + tìm theo **tên (khớp cả có dấu lẫn không dấu)**/CCCD/số hồ sơ (`usp_NguoiLX_HoSo_Search`); ô tìm đặt trên đầu lưới, màn hẹp thu gọn thành **nút kính lúp**. (CHANGES #10)
- ✅ Mở hồ sơ để sửa **thông tin nhân thân** (họ tên, ngày sinh, giới tính, số căn cước, địa chỉ thường trú) qua `usp_NguoiLX_Update`; đọc lại bản ghi hiện tại để giữ nguyên cột không sửa. Ảnh → QLY-05, đổi khóa → QLY-02 (KHÔNG dùng `usp_NguoiLX_HoSo_Update` ở đây — SP ghi đè 65 cột, CHANGES #17).
- ✅ Chặn sửa khi khóa đã lập BC1 (badge "Đã BC1 — chỉ xem"); khóa chưa BC1 sửa được.
- ⚠️ **Hiện ảnh chân dung + đường dẫn ảnh khi xem HV** (CHANGES #22): click HV → modal chi tiết hiện ảnh thật (backend chuyển `.jp2`→PNG để trình duyệt xem được) + dòng đường dẫn `DuongDanAnh`. **DB có đường dẫn nhưng file không tồn tại trên ổ → cảnh báo "không tìm thấy file ảnh"** (hiện `co_anh` chỉ xét cột rỗng, không kiểm file thật). *(task 34: backend endpoint `/anh` + `/anh-thumb` XONG; UI task 35)*
- ⬜ **Avatar mỗi dòng lưới HV** (CHANGES #22): ảnh thu nhỏ lấy từ DB (endpoint thumbnail + cache); HV chưa ảnh → icon hình người.
- ⬜ **Click ảnh → mở trình chỉnh ảnh** (sang QLY-05): chỉnh/đổi nền ảnh đã có.
- ⬜ **Thống kê nhanh đầu khóa** (CHANGES #22): tổng HV · số thiếu ảnh · đã BC1.
- ⬜ **Nút đổi khóa / xóa nhanh ra lưới** (CHANGES #22): gọi QLY-02/QLY-03, vẫn xác nhận 2 bước, tôn trọng chặn BC1.
- ❌ Không kết xuất báo cáo (NICE).

**Edge cases:**
| Tình huống | Hành vi mong muốn |
|---|---|
| Sửa hồ sơ khóa đã lập BC1 | Chặn, báo lý do, hướng dùng app cũ |

> Nguồn: CAP-010 · BR-012 · EC-051

#### [QLY-02] Đổi khóa + di chuyển ảnh

**Trạng thái:** ⚠️ Partial — 02/10/2026 (task 23). Code xong: đổi khóa **cùng hạng** qua **UPDATE nhắm 3 cột** (`MaKhoaHoc`/`SoHoSo`/`DuongDanAnh`, KHÔNG dùng `usp_NguoiLX_HoSo_Update` — CHANGES #17/#18); `SoHoSo` sinh lại trong applock khóa đích; di chuyển `.jp2` sang folder khóa mới (hoàn tác nếu UPDATE lỗi). Chặn: khác hạng · khóa cũ/đích đã BC1 · HV đã có GPLX (`NguoiLX_GPLX`) · file ảnh bị khóa. UI: nút "Đổi khóa" ở Tra cứu DB + `GET /local/khoa-hoc/cung-hang`. Kiểm: tool **109 test** + webui build · review-nghiệp-vụ **6/6 Done**. **Chờ verify đổi khóa thật.** (PRD Steps bước 2 còn ghi SP cũ — cập nhật qua `/capnhat`.)
**Story:** Là nhân viên nạp DB, tôi muốn chuyển học viên sang khóa khác, để sửa khi gán nhầm khóa.

**Steps to Complete:**
1. Chọn học viên + khóa đích (cùng hạng).
2. `usp_NguoiLX_HoSo_Update` đổi `MaKhoaHoc`, sinh lại Số hồ sơ theo khóa mới.
3. Di chuyển file `.jp2` sang folder khóa mới, cập nhật `DuongDanAnh` (giữ tên file).

**Done khi:**
- ✅ Đổi khóa cùng hạng → `MaKhoaHoc` mới, file ảnh nằm folder mới, `DuongDanAnh` khớp, `MaDK` giữ nguyên.
- ✅ Đổi sang khác hạng → hướng xóa tạo lại (không đổi trực tiếp).
- ❌ Không đổi khóa cho HV đã lập BC1/đã có GPLX.

> Nguồn: CAP-011 · BR-013

#### [QLY-03] Xóa học viên + xóa mềm ảnh

**Trạng thái:** ⚠️ Partial — chờ verify xóa thật prod. task 37 XONG (chặn xóa HV khóa BC1 ở BACKEND: cờ `bc1` = `EXISTS(BaoCaoI theo MaKH)` gộp vào query step 1 → 409 trước `usp_NguoiLX_Delete`; +2 test mock, 127 pytest; review-nghiepvu đủ). Nút xóa nhanh ra lưới đã xong ở task 36 (QLY-01). Phần đã code trước đó (task 24): `POST /local/ho-so/xoa` → `usp_NguoiLX_Delete` (cascade HoSo+GiayTo); chặn HV đã có GPLX (pre-check `NguoiLX_GPLX` + verify sau xóa vì SP không raiserror); ảnh **xóa mềm** chuyển sang folder `_DELETED` (giữ tên MaDK, không xóa cứng) + ghi log staging. UI: nút "Xóa" xác nhận 2 bước ở Tra cứu DB. Kiểm: tool **111 test** + webui build · review-nghiệp-vụ **6/6 Done**. **Chờ verify xóa thật.** (CHANGES #22: ĐÃ CHỐT cấm xóa HV khóa BC1 — chặn ở BACKEND, không chỉ ẩn nút UI; lý do: bảo toàn liên kết `NguoiLX_HoSo.MaBC1/MaBC2` với Báo cáo 1/2.)
**Story:** Là nhân viên nạp DB, tôi muốn xóa học viên nhập nhầm, để dọn hồ sơ sai mà không mất ảnh vĩnh viễn.

**Done khi:**
- ✅ `usp_NguoiLX_Delete` (cascade HoSo + GiayTo); file `.jp2` chuyển sang folder `_DELETED` (xóa mềm) + log.
- ✅ HV đã có GPLX không xóa được (FK chặn) → báo rõ.
- ⬜ **Chặn xóa HV ở khóa đã lập BC1 — ở BACKEND** (CHANGES #22): xóa HV đã vào Báo cáo (`NguoiLX_HoSo.MaBC1/MaBC2`) sẽ làm HV biến mất khỏi Báo cáo 1/2 → cấm xóa ở tầng backend (`usp_NguoiLX_Delete`), không chỉ ẩn nút UI.
- ⬜ **Popup "Xóa hẳn" tách bạch với "Gỡ về chờ nạp"** (CHANGES #26): copy nói rõ khác QLY-08: *"Xóa hẳn học viên khỏi DB? Dùng khi bỏ hẳn học viên này. Muốn nạp lại phải nhập lại hồ sơ ở app. Ảnh chuyển sang thư mục _DELETED (còn khôi phục được). Học viên đã có giấy phép lái xe thì không xóa được."* Hai nút "Xóa hẳn" và "Gỡ về chờ nạp" đặt cạnh nhau, copy nêu rõ hậu quả khác nhau (bỏ hẳn ≠ gỡ để nạp lại) — chống bấm nhầm.
- ⬜ **Bản ghi app web sau "Xóa hẳn"** (CHANGES #26, nguyên tắc bàn giao TDD §7.5): QLY-03 **không** đồng bộ ngược VPS — bản ghi trên app web giữ nguyên "đã nạp" (lịch sử). Muốn nạp lại học viên = **tạo hồ sơ MỚI ở app web** (uuid mới).
- ❌ Không xóa cứng file ảnh.

> Nguồn: CAP-012 · BR-014 · EC-021

#### [QLY-05] Nạp/thay ảnh cho học viên đã có

**Trạng thái:** ⚠️ Partial — code xong (CHANGES #32 **ĐÃ code task 53**, commit `51e133e`+`b6c7317`), **chờ verify máy CSDT** (ghi ảnh thật trên SQL Server). Phần #32: bổ sung ảnh cho HV thiếu ảnh lấy từ file máy tính HOẶC kéo ảnh thô VPS, qua cùng AnhModal + đổi nền. — yêu cầu bổ sung UI ảnh 02/10/2026 (CHANGES #23: sau khi lưu/chỉnh hiện ảnh đã chỉnh + mở lại chỉnh tiếp + nút lưu rõ); code task 33 (vá `TT_XuLy`) vẫn đúng, story quay lại hàng đợi để làm phần UI mới. task 33 (🐛 vá `TT_XuLy` + ghi ảnh atomic) XONG + 123 test (2 hồi quy); còn task 34-35 (xem ảnh/click từ Tra cứu DB). Nền (CHANGES #22: 🐛 sửa bug `TT_XuLy='03'` làm rơi HV khỏi Báo cáo 2 + cho click ảnh từ Tra cứu DB mở trình chỉnh). Phần đã code trước đó (task 27): màn Tra cứu DB thêm lọc tình trạng ảnh (Tất cả/Chưa ảnh/Đã có ảnh) + nút Nạp/Thay ảnh → tái dùng `AnhModal` (NAP-04: crop 3:4 + nền trắng + .jp2 353×471) → `POST /local/ho-so/nap-anh` ghi `.jp2` (ghi đè khi thay) + UPDATE 5 cột ảnh hướng A (`ghi_anh_update` dùng chung NAP-05); cảnh báo trước khi ghi đè; retry UPDATE 1 lần theo MaDK khi lỗi (EC §11.5), file bị khóa app cũ → báo đóng (409). Nạp/thay ảnh dùng được cả khóa đã BC1 (chỉ cập nhật ảnh). Kiểm: tool 119 test (11 QLY-05) · webui build · Playwright 3vp (0 tràn) · review-nghiepvu Done khi 5/5 + edge case retry đã vá. **Chờ verify ghi ảnh thật trên SQL Server.**
**Story:** Là nhân viên nạp DB, tôi muốn bổ sung ảnh cho học viên đã nạp hồ sơ nhưng chưa có ảnh, hoặc thay ảnh mới cho học viên đã có ảnh, để hoàn tất/chuẩn hóa hồ sơ mà không phải nhập lại từ đầu.

**Steps to Complete:**
1. Trên màn tra cứu/quản lý HV, lọc học viên theo tình trạng ảnh (chưa có ảnh `TT_XuLy='01'` / đã có ảnh `'03'`).
2. Chọn HV → căn ảnh + xóa phông + xuất `.jp2` (dùng lại luồng NAP-04).
3. Ghi `.jp2` theo `MaDK` (ghi đè nếu đã có) + UPDATE cột ảnh `NguoiLX_HoSo` (hướng A, TDD §10.3). **`TT_XuLy` — nguyên tắc "KHÔNG BAO GIỜ HẠ": chỉ set `'03'` khi HV CHƯA có ảnh (`TT_XuLy` hiện tại là `'01'`/`'02'`); mọi giá trị khác (`'03'` và mọi mã Báo cáo) → GIỮ NGUYÊN, chỉ thay file + đường dẫn ảnh** — tránh đá HV khỏi `usp_BaoCao2_DSHS` (lọc `TT_XuLy in '11'..'19'`).

**Done khi:**
- ✅ Màn tra cứu có bộ lọc theo tình trạng ảnh; hiện đúng danh sách HV chưa ảnh / đã có ảnh.
- ✅ Bổ sung ảnh (HV `'01'`): `.jp2` ghi tại `<IMG_PATH_CSDT>\<MaKhoaHoc>\<MaDK>.jp2`; `DuongDanAnh`/`ChatLuongAnh=1`/`TT_XuLy='03'`/`NgayThuNhanAnh` cập nhật; mở app cũ thấy ảnh.
- ✅ Thay ảnh (HV `'03'`): ghi đè đúng file `.jp2` cùng tên; cập nhật lại `DuongDanAnh`/`ChatLuongAnh`/`NgayThuNhanAnh`; có cảnh báo trước khi ghi đè ảnh cũ.
- ✅ Dùng lại đúng luồng xử lý ảnh NAP-04 (crop 3:4 + nền trắng + 353×471).
- ⬜ **Giữ `TT_XuLy` khi HV đã ở Báo cáo 1/2** (CHANGES #22, 🐛): thay ảnh cho HV `'11'`–`'19'` KHÔNG hạ về `'03'` (sẽ làm HV biến mất khỏi Báo cáo 2) — chỉ thay file + `DuongDanAnh`/`NgayThuNhanAnh`.
- ⬜ **Mở trình chỉnh ảnh từ màn Tra cứu DB** (CHANGES #22): click avatar/ảnh HV đã có → AnhModal (ảnh `.jp2` đã transcode→PNG làm ảnh gốc) → đổi nền/chỉnh → lưu đè.
- ⬜ **Bổ sung ảnh cho HV thiếu ảnh — 2 nguồn** (CHANGES #32, #44): với HV đã nạp nhưng **chưa có ảnh** (lọc "chưa ảnh"), mở AnhModal và lấy ảnh gốc từ: **(a) chọn từ file máy tính** · **(b) kéo ảnh thô học viên gửi trên VPS** (tra theo HV, nếu ảnh còn trên VPS — bản gửi giữ ~30 ngày) — **gồm cả ảnh collector CHỤP BÙ sau khi đã nạp** (THU-02/#44: app web cho chụp bù HV thiếu ảnh kể cả imported). Qua **cùng trình chỉnh + đổi nền** như NAP-04 rồi nạp vào DB (dùng luồng QLY-05 sẵn có). Ảnh thô VPS đã hết hạn / chưa chụp → chỉ còn nguồn (a). Operator **tự lọc "Chưa ảnh" → mở HV → bấm kéo** (không có cờ "ảnh mới" — chốt A, CHANGES #44).
- ⬜ **Sau khi lưu ảnh, hiện ngay ảnh mới + mở lại chỉnh tiếp** (CHANGES #23): lưu đè xong (`/nap-anh` thành công), khung ảnh HV hiện **ảnh mới** (làm tươi, không trả bản cũ từ bộ đệm); bấm chỉnh lần sau nạp sẵn **ảnh mới nhất** để chỉnh tiếp. Nút áp dụng trong trình chỉnh **nổi bật + nhãn rõ** (như NAP-04) — tránh dừng ở bước "Xử lý ảnh" tưởng đã lưu.
- ⬜ **"Dùng lại ảnh gốc"** (CHANGES #26): khi thay ảnh HV đã có, nút quay về **ảnh `.jp2` đang lưu trong DB** (bản trước khi chỉnh ở phiên này, transcode PNG) để sửa lại từ đầu; xác nhận nhanh trước khi bỏ chỉnh sửa. Dùng chung nút với NAP-04 (ảnh gốc = nguồn tùy màn: NAP-04 là ảnh thô VPS, QLY-05 là ảnh DB).
- ❌ Không tạo bản ghi HV mới (chỉ cập nhật HV đã có).

**Edge cases:**
| Tình huống | Hành vi mong muốn |
|---|---|
| App cũ đang mở/khóa file `.jp2` của HV đó | Báo không ghi được file đang bị khóa, yêu cầu đóng app cũ rồi thử lại |
| Ghi `.jp2` lỗi | Giữ nguyên trạng thái ảnh cũ (`'01'` hoặc file cũ), báo lỗi, cho thử lại |
| UPDATE cột ảnh lỗi sau khi đã ghi file | Retry UPDATE theo `MaDK`; không tạo HV mới |

> Nguồn: review TDD §10 (01/10/2026, CHANGES #5) · dùng lại NAP-04 · BR-010, BR-011 · TDD §10.3 hướng A

#### [QLY-06] Mở hồ sơ khóa khác cho học viên đã có (cấp mới khác hạng, song song)

**Trạng thái:** ⚠️ Partial — code xong (commit `92bba21` task 32), **chờ verify máy CSDT** (nạp thật trên SQL Server). đổi nhãn nút 02/10/2026 (CHANGES #23: "Mở khóa khác" → **"Tạo thêm hồ sơ ở khóa học khác hạng"** cho đúng bản chất tạo hồ sơ MỚI, giữ hồ sơ cũ; GIỮ hiển thị cả ở khóa đã BC1 vì học thêm hạng không đụng báo cáo cũ); code task 32 vẫn đúng, chỉ sửa nhãn. Code xong: nút "Mở khóa khác" ở Tra cứu DB → `MoKhoaKhacDialog` điền sẵn thông tin cá nhân (`GET /local/ho-so/day-du` đọc NguoiLX) → chọn loại + khóa đích chưa BC1 (khác hạng) → tick giấy tờ + ảnh tùy chọn → nạp MỚI qua SP gộp `@p_MaDK=NULL` (MaDK mới, chung SoCMT, đăng ký cũ giữ nguyên); chặn trùng cùng khóa đích (kiemTrung disable nút + server `@p_out=-2`). KHÔNG nâng hạng. Kiểm: tool 121 test (2 gate day-du) · webui build · Playwright 1440/375 (0 tràn) · review-nghiepvu 3/3 Done khi. **Chờ verify nạp thật trên SQL Server.**
**Story:** Là nhân viên nạp DB, tôi muốn mở hồ sơ ở một khóa khác (khác hạng) cho học viên đã có trong DB, để học viên học thêm hạng mà không phải nhập lại thông tin từ đầu.

**Căn cứ DB (kiểm thật 01/10, CHANGES #16):** SP `ThemMoiCapNhat` khi nạp mới (`@p_MaDK` rỗng) **luôn tạo `NguoiLX` mới** (MaDK mới) — không dò người cũ. Dữ liệu thật: nhiều HV có 2–8 khóa, mỗi khóa 1 hồ sơ, **chung SoCMT** → nhiều dòng cùng SoCMT là đúng thiết kế, KHÔNG phải trùng. Nên nạp khác khóa = **nạp mới bình thường**, không cần nối người cũ.

**Done khi:**
- ⬜ Từ màn Tra cứu DB (QLY-01), chọn HV đã có → **nút "Tạo thêm hồ sơ ở khóa học khác hạng"** (CHANGES #23: nhãn cũ "Mở khóa khác"/"Mở hồ sơ khóa khác" gây hiểu nhầm là *chuyển* khóa) → điền sẵn thông tin cá nhân từ bản ghi cũ (đọc theo SoCMT/MaDK) để đỡ gõ lại. Nút **hiển thị cả khi khóa đã BC1** (tạo hồ sơ mới ở khóa khác hạng, KHÔNG đụng hồ sơ/báo cáo cũ) — khác nút "Đổi khóa" (QLY-02, chuyển cùng hạng) vốn đã ẩn khi BC1.
- ⬜ Chọn khóa đích (khác hạng, vẫn là cấp mới — `MaLoaiHs` 1/2 theo khóa NAP-02) → nạp mới qua SP gộp (`@p_MaDK=NULL`) → tạo MaDK mới + hồ sơ ở khóa đích; đăng ký cũ giữ nguyên.
- ⬜ Chặn trùng trong **cùng khóa đích** (NAP-06 theo khóa): HV đã có trong khóa đó → báo trùng, không tạo thêm.
- ❌ Không làm nâng hạng (B→C/D/E) — ngoài MVP (SP có tham số thâm niên/km nhưng chưa thu thập).

> Nguồn: user 01/10/2026 (CHANGES #13/#16) · kiểm DB thật · NAP-06 "cùng CCCD khác khóa thì cho phép" · liên quan QLY-01/QLY-02

#### [QLY-07] Đổi nền trắng ảnh cho cả khóa

**Trạng thái:** ⚠️ Partial — chưa nghiệm thu ghi thật ở máy CSĐT (ổ ảnh `D:\GPLXCSDT` + UNC/`Capmoi` chỉ có ở đó; file khóa app cũ, ghi đè file dùng chung 2 DB, bản cũ đã sinh `_BACKUP` theo khóa chưa). Code xong 12/10/2026 (task 118, CHANGES #67): `doinen.py` ghi đè TẠI `DuongDanAnh` (module chung `anh_file.py`), sao lưu `<tên>_BACKUP.jp2` cùng thư mục chỉ-nếu-chưa-có, chỉ UPDATE `ChatLuongAnh/NgayThuNhanAnh/NguoiThuNhanAnh`; tool 668 pytest · review-nghiepvu đủ tiêu chí 3-8 + 4 edge. Trước đó: task 39 (backend) + 40 (UI) — chạy nền + tiến độ polling, heuristic 4 góc, giữ `TT_XuLy`, HV không ảnh bỏ qua.
**Story:** Là nhân viên nạp DB, tôi muốn đổi nền trắng hàng loạt cho ảnh của cả một khóa, để chuẩn hóa ảnh cũ (nạp từ app cũ, nền chưa trắng) mà không phải xử lý từng học viên.

**Done khi:**
- ⬜ Từ màn Tra cứu DB, chọn 1 khóa → "Đổi nền trắng cả khóa" → chạy xử lý rembg (crop 3:4 + nền trắng như NAP-04) cho ảnh từng HV.
- ⬜ **Chạy nền + thanh tiến độ** (N/tổng, số lỗi), không treo giao diện (ước ~1-3 giây/ảnh × ~100 HV ≈ vài phút).
- ⬜ **Ghi đè ĐÚNG file ở `DuongDanAnh` hiện có** (user chốt 12/10/2026): ảnh là một file vật lý **dùng chung** giữa DB Nạp và DB đích (sync sao chép `DuongDanAnh` nguyên văn), nên đổi nền **không tạo file ở thư mục khác và không đổi `DuongDanAnh`**; chỉ cập nhật `ChatLuongAnh`/`NgayThuNhanAnh`/`NguoiThuNhanAnh` của bản ghi.
- ⬜ **Sao lưu ảnh gốc `<tên>_BACKUP.jp2` CÙNG thư mục với file ảnh, chỉ tạo nếu chưa có** (tùy chọn, mặc định bật; cùng kiểu với thay ảnh ở TCB-02) — ghi đè `.jp2` không khôi phục được nếu không sao lưu; chạy lần 2 không đè bản gốc thật.
- ⬜ **Phạm vi mặc định "chỉ ảnh chưa nền trắng"** (ảnh nạp qua tool đã trắng sẵn) — phát hiện bằng heuristic lấy mẫu pixel 4 góc (DB không có cờ); sai sót nhỏ bù bằng tùy chọn "tất cả HV có ảnh".
- ⬜ **Giữ `TT_XuLy`** như QLY-05 (không hạ về `'03'` cho HV đã Báo cáo) — nếu không, cả khóa đã BC2 biến mất khỏi báo cáo cùng lúc.
- ⬜ HV không có ảnh → bỏ qua, không báo lỗi.
- ❌ Không đổi thông tin nhân thân, không xóa, không đụng khóa/đăng ký.

**Edge cases:**
| Tình huống | Hành vi mong muốn |
|---|---|
| File ảnh bị app cũ khóa | Bỏ qua HV đó, ghi vào danh sách lỗi, chạy tiếp các HV khác |
| Khóa đã BC1/BC2 | Vẫn chạy (ảnh không nằm trong nội dung báo cáo), nhưng BẮT BUỘC giữ `TT_XuLy` |
| Tắt tool/mất điện giữa chừng | Ảnh đã xử lý giữ nguyên; chạy lại bỏ qua ảnh đã trắng |
| Ảnh của HV nằm ở gốc khác `IMG_PATH_CSDT` (vd `\\192.168.1.15\GPLXCSDT\ANHCDUNG`, `...\Capmoi\70004`) | Vẫn ghi đè **tại chỗ**, giữ nguyên `DuongDanAnh`; thư mục không ghi được → ghi vào danh sách lỗi, chạy tiếp HV khác |

> Nguồn: user 02/10/2026 (CHANGES #22) · dùng lại NAP-04 · liên quan QLY-05 · bảo toàn Báo cáo 1/2 (schema DBcu: `NguoiLX_HoSo.MaBC1/MaBC2`, `usp_BaoCao2_DSHS` lọc `TT_XuLy`)
> **Sửa 12/10/2026 (CHANGES #67):** user xác nhận ảnh dùng chung 1 đường dẫn của DB Nạp cho cả 2 DB · đọc DB 12/10/2026: DB đích 741 ảnh, 668 đường dẫn trùng đường dẫn ở Nạp; DB Nạp 39.927 ảnh, trong đó 154 ảnh ở `\\192.168.1.15\GPLXCSDT\ANHCDUNG` và 87 ảnh ở `\\192.168.0.10\...\Capmoi\70004` (khác gốc `D:\GPLXCSDT\ANHCDUNG`) · TDD §11.6.

#### [QLY-08] Gỡ học viên về chờ nạp (nạp nhầm khóa)

**Trạng thái:** ⚠️ Partial — chờ verify live (Checkpoint 8). Code XONG cả 2 task: task 42 (03/10) server VPS `tra-ve-cho-nap` + `tra-uuid`; task 43 (03/10) tool+webui — endpoint `go-ve-cho-nap` (tra uuid TRƯỚC → xóa CSDT `usp_NguoiLX_Delete` + ảnh `_DELETED`, reuse QLY-03 → gọi VPS trả về `pending`) + `dong-bo-tra-ve` ("Thử lại đồng bộ" riêng bước VPS khi đã xóa CSDT mà VPS lỗi) + webui nút "Gỡ về chờ nạp" viền cam cạnh "Xóa hẳn" (chỉ khóa chưa BC1, panel 2 bước copy #26) + banner đồng bộ lỗi + refine copy "Xóa hẳn". Kiểm mức 1: tool **161 pytest** (+15 QLY-08) · webui **build + 29 vitest** · review-nghiepvu 8/10 Done đủ (1 ❔ tiêu chí 9 phụ thuộc server, 1 edge "Bỏ khỏi hàng đợi" → chủ dự án chốt 03/10: nhắc bấm "Kéo về" thủ công, không tự kéo). **Chờ verify máy CSDT + deploy VPS (Checkpoint 8):** gỡ HV khóa chưa BC1 → biến mất CSDT + ảnh `_DELETED` + VPS về `pending`; khóa BC1/GPLX → chặn; VPS lỗi sau khi xóa → "Thử lại đồng bộ". Yêu cầu mới 02/10/2026 (CHANGES #24) + nghiệp vụ/popup (CHANGES #26). **BUG-01 (03/10, đã sửa):** gỡ về chờ nạp rồi nạp lại CÙNG uuid từng không vào DB (tool báo thành công) — `keo_ve_ve_cho` nay xóa luôn vé `nap_xong`; +2 test hồi quy (tool 167 pytest). Xem `docs/BUGS.md`. **BUG-03 (03/10, đã sửa):** gỡ xong màn Nạp không tự hiện lại HV ở "chờ nạp" (phải bấm Kéo) — `NapHoSo` nay tải lại danh sách khi vào tab Nạp (`useEffect[mode]`). Kiểm tay (chưa có hạ tầng test React component). Xem `docs/BUGS.md`.
**Story:** Là nhân viên nạp DB, tôi muốn gỡ một học viên đã nạp nhầm khóa ra khỏi DB và trả về danh sách chờ nạp, để nạp lại đúng khóa mà không phải nhập lại từ app web.

**Steps to Complete:**
1. Ở Tra cứu DB, chọn HV (khóa **chưa BC1**) → nút **"Gỡ về chờ nạp"** (TÁCH BẠCH với "Xóa" bỏ hẳn — QLY-03) → xác nhận 2 bước.
2. Tool gỡ HV khỏi CSDT (`usp_NguoiLX_Delete`, cascade HoSo+GiayTo như QLY-03; ảnh `.jp2` xóa mềm → `_DELETED`).
3. Tool gọi VPS **"trả về chờ nạp"** (bản ghi gốc `imported`→`pending`, gỡ liên kết `ma_dk`) theo `uuid` suy từ liên kết nạp (`nap_xong`/VPS).
4. Hàng chờ của tool đưa dòng HV về **"chờ nạp" (⚪)** ngay; nếu dòng đã bị "Bỏ khỏi hàng đợi" trước đó → kéo lại từ VPS.

**Done khi:**
- ⬜ Nút **"Gỡ về chờ nạp"** chỉ hiện/chạy được ở **khóa chưa BC1** (khóa đã BC1 cấm — gỡ sẽ phá liên kết Báo cáo 1/2, như QLY-03).
- ⬜ Gỡ xong: HV **biến mất khỏi khóa trong CSDT** và **hiện lại ở danh sách chờ nạp** của tool với badge **"chờ nạp"** như HV mới kéo về.
- ⬜ **VPS cập nhật theo:** bản ghi gốc về `pending` (gỡ `ma_dk`) → mọi máy nạp kéo về đều thấy HV ở hàng chờ (cần **đường mới ở server VPS** "trả về chờ nạp").
- ⬜ **Ảnh:** HV về chờ nạp hiển thị lại **ảnh thô còn trên VPS** (như lúc mới kéo); KHÔNG chuyển ngược ảnh `.jp2` đã xử lý.
- ⬜ **Bản ghi gốc VPS đã bị dọn PII** (HTG-03) → không còn để trả về → **báo rõ "không còn bản gốc trên VPS, chỉ có thể Xóa hẳn"**, không gỡ.
- ⬜ HV **đã có GPLX** → FK chặn xóa (như QLY-03) → không gỡ được, báo rõ.
- ⬜ **Popup xác nhận "Gỡ về chờ nạp"** (CHANGES #26): panel 2 bước (viền cam, TÁCH khỏi "Xóa hẳn" QLY-03), copy: *"Gỡ học viên về hàng chờ nạp? Dùng khi nạp nhầm khóa và muốn nạp lại. Học viên bị gỡ khỏi khóa này trong DB và quay lại danh sách chờ nạp để nạp vào đúng khóa, không phải nhập lại ở app. Ảnh đã xử lý sẽ bỏ; nạp lại dùng ảnh gốc học viên gửi. Chỉ làm được khi khóa chưa lập Báo cáo 1."* Nút: **Hủy / Gỡ về chờ nạp**.
- ⬜ **Banner khi đồng bộ máy chủ lỗi** (CHANGES #26, edge): *"Đã gỡ học viên khỏi khóa trong DB, nhưng chưa đưa về được hàng chờ nạp (mất kết nối máy chủ). Học viên hiện không còn trong khóa. Bấm 'Thử lại' để đồng bộ."* + nút **"Thử lại đồng bộ"** (chỉ chạy lại bước gọi VPS, không xóa lại CSDT).
- ⬜ **Về chờ nạp → người thu nhận chỉnh được tiếp** (CHANGES #26): sau khi gỡ, hồ sơ về `pending` trên app web → người thu nhận lại sửa/xóa được như hồ sơ chờ nạp bình thường (nhất quán "trước nạp, app web làm chủ" — TDD §7.5).
- ❌ Không áp cho khóa đã BC1. ❌ Không xóa cứng ảnh (xóa mềm `_DELETED` như QLY-03).

**Edge cases:**
| Tình huống | Hành vi mong muốn |
|---|---|
| Gỡ khỏi CSDT xong nhưng gọi VPS "trả về" lỗi | Báo lỗi rõ; HV đã xóa khỏi CSDT nhưng chưa về hàng chờ — cho thử lại bước đồng bộ VPS |
| Dòng staging đã bị "Bỏ khỏi hàng đợi" | Sau khi VPS về `pending`, kéo lại dòng đó từ VPS về hàng chờ |
| Bản ghi gốc VPS đã dọn PII | Không gỡ được về chờ nạp (báo rõ); muốn bỏ hẳn thì dùng "Xóa" |

> Nguồn: user 02/10/2026 (CHANGES #24, buổi verify #22) · tách bạch QLY-03 · liên quan NAP-01 (hàng chờ) · HTG-02/NAP-05 (trạng thái VPS) · HTG-03 (dọn PII)

#### [QLY-09] Đối soát & đồng bộ trạng thái VPS↔CSDT

**Trạng thái:** ✅ Done — 04/10/2026, đủ 2 task: 48 backend đối soát VPS↔CSDT + phòng tuyến 2 (`82684ea`) · 49 webui panel "Đối soát VPS↔CSDT" + nút sửa 1 chạm (`a8b3274`); review-nghiepvu 15/16 + chốt edge BC1 (`e3a34c3`). Kiểm mức 1+2: server 128 pytest · tool 193 pytest · webui build+34 vitest. Yêu cầu từ CHANGES #28 (ca BUG-01). Phạm vi: đối soát **theo khóa / theo yêu cầu** (không quét toàn bộ). Playwright + verify lệch thật ở Checkpoint 10 (máy có dữ liệu).
**Story:** Là nhân viên nạp DB (hoặc quản trị), tôi muốn tự phát hiện và sửa các bản ghi bị **lệch trạng thái giữa máy chủ (VPS) và CSDT**, để không phải nhờ kỹ thuật sửa tay cơ sở dữ liệu khi có sự cố.

**Steps to Complete:**
1. Mở panel **"Đối soát VPS↔CSDT"** (ở Tra cứu DB, chỉ operator/admin) → chọn **một khóa** (hoặc phạm vi) cần kiểm.
2. Tool so trạng thái từng hồ sơ: bản ghi VPS (`ho_so_thu_thap`) ↔ bản ghi CSDT (`NguoiLX_HoSo` theo `MaDK`) ↔ staging.
3. Liệt kê **chỉ các dòng lệch**, mỗi dòng nêu rõ loại lệch + nút sửa 1 chạm tương ứng.
4. Bấm nút sửa → tool gọi đúng đường đồng bộ có sẵn (không tạo endpoint/SP nạp mới), rồi làm tươi lại danh sách đối soát.

**Done khi:**
- ⬜ **Hai chế độ đối soát** (chốt A sau review TDD — bản ghi VPS không có cột khóa nên phantom/importing không quy được về khóa):
  - **Đối soát theo khóa** (operator/admin): chọn khóa → bắt **ca ②** (hồ sơ của khóa còn ở CSDT nhưng VPS chưa `imported`).
  - **Quét bản ghi lạc toàn hệ** (admin): bắt **ca ① + ③** (neo ở trạng thái VPS, dùng lại `GET /api/admin/ho-so` lọc trạng thái — check một chiều, không so 2 chiều toàn tập).
- ⬜ **Phát hiện 3 ca lệch:**
  - **① VPS `imported` nhưng CSDT KHÔNG có `MaDK`** ("phantom import" — như BUG-01) → nút **"Trả về chờ nạp"** (lật VPS `imported→pending`, gỡ `ma_dk`; tái dùng `tra_ve_cho_nap` — KHÔNG đụng CSDT vì vốn đã không có).
  - **② CSDT có HV nhưng VPS chưa `imported`** (nạp vào CSDT xong nhưng bước báo VPS lỗi) → nút **"Đánh dấu đã nạp"** (tái dùng `da_nap(uuid, ma_dk)`).
  - **③ VPS `importing` treo** (lock kẹt quá lâu, không ai đang nạp) → nút **"Mở khóa"** (tái dùng `unlock`, đưa về `pending`).
- ⬜ Mỗi dòng lệch **nêu rõ loại + hậu quả** bằng chữ nghiệp vụ (không để operator đoán).
- ⬜ Sửa xong **làm tươi lại** danh sách đối soát; dòng đã khớp biến mất.
- ⬜ **Không tạo endpoint/SP nạp mới** — chỉ tái dùng `tra_ve_cho_nap` · `da_nap` · `unlock` (VPS) + truy vấn đọc CSDT.
- ⬜ **Phòng tuyến 2 (chặn tái phát phantom):** trong luồng nạp lô, nếu `_nap_mot` trả **kết quả cũ từ vé idempotency** (không INSERT mới) thì **KHÔNG gọi `da_nap`** — tránh đánh dấu VPS `imported` cho bản ghi không thực sự vào CSDT (gốc BUG-01).
- ❌ KHÔNG so khớp **2 chiều toàn tập** mỗi lần (ca ② theo khóa; ca ①③ quét một chiều theo trạng thái VPS — nhẹ).
- ❌ KHÔNG tự động sửa hàng loạt không hỏi — mỗi dòng operator tự bấm (tránh sửa nhầm diện rộng).

**Edge cases:**
| Tình huống | Hành vi mong muốn |
|---|---|
| VPS/tunnel down khi đối soát | Báo lỗi rõ, không coi là "lệch"; cho thử lại |
| Khóa đã BC1 | Chỉ ĐỐI SOÁT/đọc được; nút sửa đụng xóa/gỡ phải tôn trọng chặn BC1 như QLY-03/QLY-08 |
| Bản ghi gốc VPS đã dọn PII (HTG-03) | Ca ② không "Đánh dấu đã nạp" được nếu VPS không còn bản ghi → báo rõ |
| Lệch do đang nạp thật ở máy khác (`importing` mới) | KHÔNG coi là treo; chỉ ca `importing` **quá ngưỡng thời gian** mới gợi "Mở khóa" |

> Nguồn: user 03/10/2026 (sau ca Lê Thị Hồng / BUG-01) · tái dùng §11.7 (tra-ve/da-nap/unlock) · liên quan QLY-08, NAP-01

#### [HTG-03] Bộ lọc & xóa PII thủ công trên VPS

**Trạng thái:** ⚠️ Partial — 02/10/2026. Code xong: `GET /api/admin/ho-so` (lọc trạng thái + khoảng ngày giờ VN + phân trang) + `DELETE /api/admin/ho-so/:uuid` (hard-delete bản ghi + ảnh thô + audit `xoa_pii_tay`) + màn `/admin/ho-so` (chỉ admin, vào từ màn Tài khoản). Tách helper `xoa_mot_ho_so` dùng chung với job 30 ngày. Kiểm: server 93 test (11 mới, có biên múi giờ VN) · webapp build + 24 test · Playwright 3vp (0 tràn, 0 lỗi) · review-nghiepvu 7/7. **Chờ deploy VPS + verify thao tác lọc/xóa thật.** (Admin xóa được mọi trạng thái kể cả `importing` — có chủ đích, khác job tự động bỏ qua importing EC-040.)
**Story:** Là quản trị, tôi muốn lọc và xóa thủ công bản ghi trên VPS, để chủ động dọn dữ liệu căn cước.

**Done khi:**
- ✅ Trang quản trị lọc bản ghi theo trạng thái/ngày; chọn và xóa thủ công (kèm ảnh thô).
- ❌ Không khôi phục bản ghi đã xóa.

> Nguồn: CAP-015 · BR-016

#### [HTG-04] Admin xem khóa kết nối tool (API key VPS)

**Trạng thái:** ⚠️ Partial — 02/10/2026. Code xong: endpoint `GET /api/admin/tool-key` (chỉ admin) + khối API key ở màn Tài khoản (che/Hiện/Sao chép, chỉ tải key khi bấm). Kiểm: server 82 test + webapp build. **Chờ deploy VPS + verify** (admin đăng nhập app web thấy key, dán vào tool).
**Story:** Là quản trị, tôi muốn xem khóa kết nối tool (API key VPS) ngay trên app web, để cấu hình tool mà không phải SSH vào máy chủ.

**Done khi:**
- ✅ Màn Tài khoản có khối "Khóa kết nối tool" **chỉ admin thấy**; key che sẵn (••••), nút **Hiện** + **Sao chép**; kèm dòng hướng dẫn dán vào tool → Cấu hình → API key.
- ✅ Endpoint `GET /api/admin/tool-key` chỉ admin (`require_role("admin")`) trả `TOOL_API_KEY` từ cấu hình server; **không ghi log** giá trị key.
- ❌ Không xoay/đổi key tự động (chỉ hiển thị cái đang có); không hiện cho collector/operator.

**Đánh đổi (bảo mật — chủ dự án đã duyệt):** key là khóa máy dùng chung; ai chiếm được tài khoản admin hoặc nhìn lén màn hình là lấy được, lộ thì phải xoay lại thủ công (`.env` + cấu hình tool). Chấp nhận để đổi lấy tiện lợi cấu hình.

> Nguồn: user 02/10/2026 (CHANGES #18) · thay việc SSH lấy TOOL_API_KEY

#### [HTG-05] Admin quản lý tài khoản nhân viên

**Trạng thái:** ⚠️ Partial — 02/10/2026. Code xong + **đã deploy** (chờ user verify): màn "Quản lý tài khoản" (danh sách + phân trang 20/50/100) · tạo (họ tên/username/vai trò/mật khẩu + nút ngẫu nhiên) · reset mật khẩu · khóa/mở (`is_active`, chặn tự khóa). Server `GET|POST|PUT /api/admin/users*` + reset endpoint + 13 test. ("Buộc đổi mật khẩu lần đầu" — **bỏ khỏi phạm vi** theo chủ dự án 02/10, CHANGES #18.)
**Story:** Là quản trị, tôi muốn tạo và quản lý tài khoản nhân viên (thu nhận / nạp DB), để cấp quyền dùng hệ thống mà không phải đụng cơ sở dữ liệu.

**Done khi:**
- ✅ Màn "Quản lý tài khoản" (chỉ admin): danh sách tài khoản (tên, tài khoản, vai trò, trạng thái) có **phân trang**.
- ✅ Tạo nhân viên: họ tên · tài khoản (username) · vai trò (thu nhận / nạp DB / quản trị) · mật khẩu ban đầu (có nút tạo ngẫu nhiên).
- ✅ Reset mật khẩu nhân viên: admin đặt mật khẩu mới trực tiếp (hệ thống không có email).
- ✅ Khóa/mở tài khoản (`is_active`) thay cho xóa — giữ dấu vết ai gửi/nạp hồ sơ (PII).
- ✅ Mọi endpoint chỉ admin (`require_role("admin")`); mật khẩu **băm** trước khi lưu; tài khoản trùng → báo lỗi.
- ❌ Không xóa cứng tài khoản.

**Edge cases:**
| Tình huống | Hành vi mong muốn |
|---|---|
| Admin tự khóa chính mình | Chặn — không cho khóa/vô hiệu tài khoản đang đăng nhập |
| Username đã tồn tại | Báo lỗi, không tạo |

> Nguồn: user 02/10/2026 (CHANGES #18) · HTG-01 ba vai trò collector/operator/admin

#### [HTG-06] Tự đổi mật khẩu

**Trạng thái:** ⚠️ Partial — 02/10/2026. Code xong: khối "Đổi mật khẩu" ở màn Tài khoản (mọi vai trò) + endpoint `POST /api/auth/doi-mat-khau` (kiểm mật khẩu hiện tại, chỉ đổi của chính mình). Kiểm: server 82 test + webapp build. **Chờ deploy VPS + verify.**
**Story:** Là người dùng bất kỳ (gồm admin), tôi muốn tự đổi mật khẩu của mình ở màn Tài khoản, để giữ an toàn đăng nhập.

**Done khi:**
- ✅ Màn Tài khoản có khối "Đổi mật khẩu": mật khẩu hiện tại · mật khẩu mới · nhập lại.
- ✅ Endpoint đổi mật khẩu của chính mình: kiểm mật khẩu hiện tại đúng mới cho đổi; mật khẩu mới **băm** trước khi lưu.
- ✅ Sai mật khẩu hiện tại → báo rõ; "nhập lại" không khớp → chặn phía UI trước khi gửi.
- ❌ Không đổi mật khẩu người khác (đó là HTG-05 của admin).

> Nguồn: user 02/10/2026 (CHANGES #18)

#### [HTG-07] Bảng cấu hình kết nối dùng chung ở header

**Trạng thái:** ✅ Done — task 61 (04/10/2026, CHANGES #34). drawer ⚙ ở header mọi màn (kể cả trước đăng nhập — A1), 2 khối tách bạch màu (① NẠP xanh primary · ② SYNC teal) gộp `CauHinhDrawer.tsx` từ CauHinh+DbDich; bỏ route `/tool/cau-hinh`+`/sync/db-dich` + sub-nav; đăng nhập/lối tắt mở drawer qua `useConfigDrawer()`. Kiểm: typecheck + build · Playwright 1280/1440/1920 0 tràn/0 lỗi console · impeccable detect `[]` · **review-nghiepvu 7/7 Done-khi** · **review-giaodien đạt** (sửa `rounded-xl`→`rounded-lg` theo token). Chưa commit.
**Story:** Là người dùng tool, tôi muốn xem/sửa cấu hình kết nối DB từ bất kỳ màn nào qua một nút ⚙ trên thanh header, với DB để **Nạp** và các DB để **Sync sang** tách bạch rõ ràng, để khỏi lạc không biết cài kết nối ở đâu và khỏi nhầm hai loại DB.

**Done khi:**
- ✅ Thanh header (góc phải, mọi màn) có **icon ⚙ Cấu hình**; bấm mở **một bảng cấu hình chung** (dạng panel/drawer), đóng lại về đúng màn đang xem.
- ✅ Bảng chia **hai khối tách bạch, có nhãn rõ**:
  - **① Kết nối chung + CSDL NGUỒN để Nạp:** Server / User / Mật khẩu (dùng chung cả tool) + tên **DB nguồn** `GPLX_CSDT` + URL VPS + API key + nút "Kiểm tra kết nối". *(nội dung HTG-01)*
  - **② CSDL ĐÍCH để Sync sang:** danh sách **nhiều DB đích** (thêm/sửa/xóa, chỉ khác tên database — dùng chung Server/User/Pass ở khối ①), chọn **1 mặc định**, **Kiểm tra kết nối** từng cái, + tùy chọn đồng bộ (`TT_XuLy`, cập nhật `TongSoHV`). *(nội dung SYNC-02, dời vào đây)*
- ✅ Người dùng **phân biệt được** đâu là DB để nạp, đâu là các DB để đẩy dữ liệu sang (nhãn + bố cục, không lẫn vào một danh sách phẳng).
- ✅ **Bỏ** route màn Cấu hình riêng (`/tool/cau-hinh`) và mục "Quản lý CSDL đích" khỏi sidebar/sub-nav — chỉ vào từ header. Mọi lối cũ trỏ tới hai màn này chuyển sang mở bảng header.
- ✅ Lưu **mã hóa cục bộ**; khối ① và khối ② vẫn là hai khối config riêng như cũ (không trộn chung một bản ghi).
- ❌ Không khai Server/User/Pass riêng cho từng DB đích (vẫn dùng chung khối ①).
- ❌ Không đụng cơ chế config-store/kiểm-kết-nối đã có (chỉ dời + gộp lớp UI).

> Nguồn: user 04/10/2026 (CHANGES #34) · gộp HTG-01 ③ + SYNC-02 · dựng UI bằng `impeccable` + `ui-ux-pro-max`

---

### 🟣 Đồng bộ CDB (workspace riêng — tool máy CSDT)
**Trạng thái:** ✅ Đã chốt — 07/10/2026 (user duyệt). 3 story SYNC-01/02/03 ✅ (task 56-62) · TDD §11B khớp · dấu vết commit đủ (SYNC-01 11·02 2·03 2) · review-nghiepvu từng story + review-giaodien đạt (Checkpoint 13) · **E2E live Checkpoint 12 PASS 04/10** (sync thật khóa A1m→3 HV khớp phần mềm CDB, hủy sync→CDB về 0/0/0, HV đã có skip, HV BC1 chặn 409; 265 pytest). Task 26 đóng gói .exe ngoài phạm vi Feature (thuộc DGT).

> Nghiệp vụ **TÁCH HOÀN TOÀN** khỏi Nạp hồ sơ: workspace riêng trong tool (công tắc đổi màu nhấn, banner nhắc DB đích), module backend riêng (`routers/sync.py` + `sync_service.py` + `sync_helpers.py` — **không import** module nạp). Port nghiệp vụ từ công cụ đồng bộ GPLX v2.0 (`D:\Du_An\GPLX\sync_tool`). Chuyển học viên đã có trong DB nguồn `GPLX_CSDT` sang DB đích CDB `GPLX_CDB_CSDT` (cùng Server/User/Pass, **chỉ khác tên DB**). Nghiệp vụ DB đích: **1 người = 1 hồ sơ = 1 MaDK**.

#### [SYNC-01] Bàn đồng bộ — chọn khóa, đối chiếu, đẩy HV sang CDB

**Trạng thái:** ✅ Done — task 57-59 + **task 62 làm đẹp UI** (04/10/2026, CHANGES #34): danh sách HV thêm avatar chữ-cái-đầu (theo tên gọi) + tên đậm đủ dấu không cắt + giãn dòng vừa (py-1.5) + CCCD mono; header bảng + nút Tải/SYNC đồng màu teal; +thông báo lỗi khi tải năm/khóa thất bại (bỏ catch câm). Kiểm: typecheck+build · Playwright 1280/1440 (150 HV thật, 0 tràn, 0 lỗi console) · detect `[]` · review-nghiepvu đủ · review-giaodien đạt. Nghiệp vụ sync KHÔNG đổi (bám sync_tool v2.0). Chưa commit. *(Đã làm trước đó — task 57-59, 04/10/2026, pass kiểm: Port sync_tool v2.0 tạo HV qua usp_NguoiLX_Insert + INSERT thô (SoHoSo SỐ, verify DB) + copy GiấyTờ, NguoiTao='admin'; năm/khóa nguồn+đích (đích cờ BC1 cảnh báo B); đối chiếu skip + E1/E2; backdate MaDK batch; tiến trình SSE (fetch-reader); UI bàn đồng bộ combo gõ-để-lọc + bảng 11 cột header dính + phân trang + SYNC cố định + test kết nối đích gate Tải + chặn ngày tương lai/sau-KG + khóa thao tác khi đang sync. Kiểm: tool 258 pytest · webui build+34 vitest · Playwright 1280/1440/1920 · impeccable detect sạch · review-nghiepvu đủ.)*
**Story:** Là nhân viên nạp DB, tôi muốn chọn một khóa nguồn và một khóa đích rồi đẩy các học viên chưa có sang DB CDB, để khỏi gõ lại từng người ở phần mềm CDB.

**Steps to Complete:**
1. Chọn **khóa nguồn** (Năm + Khóa ở `GPLX_CSDT`) và **khóa đích** (DB đích + Năm + Khóa ở CDB) — hai khóa phải cùng hạng xe.
2. Chọn **Ngày nhập HS** (≤ NgàyKG khóa đích). *(Không hỏi cán bộ — xem Done khi.)*
3. Bấm **Tải danh sách**: hiện HV khóa nguồn, đối chiếu CCCD với DB đích (cột MaDK đích / NgàyHS đích / Số HS).
4. Tick chọn HV cần đồng bộ (HV đã có ở đích bị khóa tick).
5. Bấm **SYNC** → xác nhận → tiến trình chạy trực tiếp từng HV → tổng kết.

**Done khi:**
- ✅ Chỉ sync khi **hạng khóa nguồn = hạng khóa đích** (lệch → chặn, báo rõ hai hạng).
- ✅ **Lọc khóa đích hợp lệ** (CHANGES #36): checkbox *"Chỉ khóa cùng hạng & chưa kết xuất DKKH"* (**mặc định bật**) → combo khóa đích chỉ hiện khóa **cùng hạng** với khóa nguồn **và chưa kết xuất DKKH** (chưa gửi đăng ký khóa học lên Sở — xem định nghĩa ở TCB-03); **bỏ tích** → hiện mọi khóa. Lọc ra rỗng → gợi ý "bỏ tích để xem tất cả". *(Thêm HV vào khóa đã gửi Sở sẽ lệch danh sách đã đăng ký → ngăn chọn nhầm từ đầu.)*
- ✅ **Khóa xếp mới-nhất-trước** (CHANGES #36): combo nguồn + đích xếp theo **NgàyKG giảm dần, MaKH DESC** (sort phụ cho ổn định khi trùng ngày); combo **nguồn hiện thêm ngày KG** để thấy rõ thứ tự (đích vốn đã có).
- ✅ **Ngày nhập HS ≤ NgàyKG** khóa đích (bằng ngày KG vẫn được); quá hôm nay/sau KG → chặn; backdate > 90 ngày → hỏi xác nhận.
- ✅ Khóa đích **đã lập Báo cáo 1 (BC1)** → **vẫn cho chọn/sync nhưng hiện cảnh báo** (HV mới không nằm trong BC1 đã nộp; khác NAP-02 chặn cứng — vì sync là thao tác bù dữ liệu chủ động). *(user chốt B, 04/10/2026)*
- ✅ HV **chưa có** ở đích → tạo mới `NguoiLX` + `NguoiLX_HoSo` (+ copy `NguoiLXHS_GiayTo` nếu có); `NguoiTao/NguoiSua` = **`admin`** (giống bản ghi phần mềm CDB tạo — **verify DB 04/10/2026**: CDB chỉ dùng tài khoản hệ thống `admin`/`ADMIN`, không có cán bộ riêng từng người → **bỏ ô "Cán bộ nạp"**, không phải 'SYNC' như công cụ cũ).
- ✅ HV **đã có** ở đích (đối chiếu theo SoCMT) → **tự bỏ qua** (1 người = 1 hồ sơ = 1 MaDK), ghi "Bỏ qua" vào kết quả.
- ✅ **MaDK** đúng `MaCSDT-yyyyMMdd-nnnnnn` (21 ký tự): ngày = hôm nay → SP tự sinh; backdate → tự sinh batch `MAX+1…MAX+N` theo prefix + backdate `NgayNhanHSo/NgayTao/NgaySua`.
- ✅ `TT_XuLy` gán theo tùy chọn (mặc định `03`); gán `SoHoSo` theo quy ước DB đích.
- ✅ Tiến trình hiển thị **trực tiếp** (thanh % + trạng thái từng HV); lỗi 1 HV không dừng cả lô, ghi lý do; tổng kết cuối (tạo mới / bỏ qua / lỗi).
- ✅ Mọi thao tác ghi vào **DB đích** đang chọn; banner cố định nhắc tên DB đích; đang sync thì chặn đổi khóa/DB/đóng tool.
- ❌ Không đổi/thêm hồ sơ thứ 2 cho HV đã có; không sync sang khóa khác hạng.

**Tiện ích UI (thêm 04/10, ngoài v2.0):** (a) combo khóa **gõ-để-lọc** (như màn Nạp) · (b) toggle **"Chỉ hiện HV sẽ tạo mới"** (ẩn dòng đã skip) · (c) **đếm dòng đang tick** cạnh nút SYNC.

**Chuẩn giao diện (CHANGES #34, 04/10/2026 — làm lại bằng `impeccable` + `ui-ux-pro-max`):** combobox năm/khóa và ô chọn DB đích trình bày gọn, nhãn rõ (năm · khóa · hạng); **danh sách HV để sync hiển thị tên hài hòa, dễ đọc** (họ tên đủ dấu, căn cột, mật độ dòng vừa phải), không để tràn/cắt chữ; bám design-system token của `tool/webui`, kiểm Playwright 1280/1440/1920.

**Ghi chú (CHANGES #35):** màn này sẽ thêm **nút "Xem chi tiết HV"** cho HV đã có ở đích → mở tab Tra cứu CDB + tô sáng (tiêu chí thuộc **TCB-01**). Thuần thêm nút điều hướng, **không đổi hành vi sync** nên SYNC-01 giữ ✅.

**Ghi chú (CHANGES #36, 05/10/2026):** 3 cải tiến, **không đổi nghiệp vụ sync lõi** nên SYNC-01 giữ ✅ — (a) filter khóa đích "cùng hạng & chưa DKKH" (mặc định bật) + (b) khóa xếp mới-nhất-trước (2 bullet Done khi trên) + (c) **giữ phiên đăng nhập qua F5** (xem HTG-01 / bảng edge "Session"). Định nghĩa "đã kết xuất DKKH" đổi sang tín hiệu đúng — xem **TCB-03**.

**Edge cases:** HV đã có ở đích → skip · race trùng MaDK (2 phiên cùng khóa cùng ngày) → kiểm tồn tại + sinh lại, tối đa 3 lần rồi báo lỗi HV đó · copy giấy tờ lỗi → vẫn tính HV thành công (best-effort) · **E1 HV nguồn thiếu CCCD** (`SoCMT` rỗng) → chặn + báo riêng (không để lỗi giữa lô, vì `NguoiLX.SoCMT` NOT NULL) · **E2 trùng CCCD trong chính danh sách nguồn** → cảnh báo (PK là MaDK nên vẫn tạo được 2, để người dùng quyết) · **E3 mất kết nối CSDL đích giữa lô** → dừng, HV đã tạo giữ nguyên + đã ghi log → sync lại tự skip HV đã tạo · E4 HV nguồn chưa có ảnh → vẫn ép `TT_XuLy` theo tùy chọn (mặc định 03, giữ v2.0).

> Nguồn: user 04/10/2026 · port sync_tool GPLX v2.0 · Phụ lục XXVII TT 17/2026/TT-BXD (format mã)

#### [SYNC-02] Quản lý DB đích + tùy chọn đồng bộ

**Trạng thái:** ✅ Done — task 61 (04/10/2026, CHANGES #34): quản lý nhiều DB đích dời vào **khối ② bảng cấu hình header** (`CauHinhDrawer.tsx`: bảng target teal + radio mặc định + Kiểm tra báo số NguoiLX + Thêm + tùy chọn TT_XuLy/TongSoHV), bỏ màn `/sync/db-dich` riêng; API `/local/sync/targets` + config-store **giữ nguyên**. Kiểm: typecheck+build+Playwright 3vp+detect `[]` · review-nghiepvu đủ · review-giaodien đạt. Chưa commit. *(Đã làm trước đó — task 56, 04/10/2026, pass kiểm: API `/local/sync/targets` GET/PUT+/test + màn Quản lý CSDL đích bảng inline-edit + radio mặc định + Kiểm tra kết nối báo số NguoiLX + tùy chọn TT_XuLy/TongSoHV, dùng chung host/user/pass với Nạp. Kiểm: tool 244 pytest · webui build+34 vitest · Playwright · impeccable sạch · review-nghiepvu đủ.)*
**Story:** Là nhân viên nạp DB, tôi muốn khai báo các DB đích CDB và chọn DB mặc định, để đổi nơi đồng bộ mà không phải sửa file cấu hình.

**Done khi:**
- ✅ Thêm/sửa/xóa **nhiều DB đích** (tên hiển thị + tên database); dùng chung Server/User/Pass với cấu hình nạp. *(04/10 — UI này nằm ở khối ② bảng cấu hình header HTG-07, không còn màn riêng.)*
- ✅ Chọn 1 DB đích **mặc định** cho Bàn đồng bộ; đổi DB đích → bắt kiểm tra kết nối lại.
- ✅ **Test kết nối** từng DB đích (báo số `NguoiLX`).
- ✅ Tùy chọn áp cho mọi DB đích: `TT_XuLy` gán sau sync (mặc định `03`), bật/tắt cập nhật `KhoaHoc.TongSoHV`.
- ✅ Cấu hình lưu **mã hóa cục bộ**, khối riêng (không trộn cấu hình nạp); xóa khỏi danh sách **không** xóa database thật.
- ❌ Không khai Server/User/Pass riêng cho đích (dùng chung với nạp).

> Nguồn: user 04/10/2026 · port cơ chế `[targets]` của sync_tool v1.06+

#### [SYNC-03] Lịch sử & Hủy sync khóa

**Trạng thái:** ✅ Done — task 60 (04/10/2026). Backend `sync.py`: `GET /lich-su` (đọc nhật ký JSON, mới nhất trước) + `GET /rollback/preview` (đếm số sẽ xóa) + `POST /rollback` (atomic autocommit=False; xóa nhóm MaDK log + nhóm `NguoiTao='SYNC'`, cascade NguoiLX→HoSo→GiayTo; cập nhật TongSoHV; **bắt lỗi BC1 FK NO_ACTION → 409** "chưa xóa HV nào"; nhật ký giữ nguyên) + `sync_history.list_all_batches()`. UI `LichSu.tsx` (bảng lần sync teal + nút Hủy + modal preview số thật). Kiểm: **7 unit test mới** (lich-su/preview/rollback+commit/BC1→409-không-commit/422) · **265 pytest** 0 hồi quy · live lich-su+preview (chỉ đọc) · Playwright 1440 0 lỗi console · detect `[]` · **review-nghiepvu 5/5 Done-khi**. Chưa commit.
**Story:** Là nhân viên nạp DB, tôi muốn xem các lần đã sync và hủy một khóa sync nhầm, để dọn sạch học viên do tool tạo mà không đụng dữ liệu khác.

**Done khi:**
- ✅ Mỗi lần SYNC ghi 1 **bản log JSON** ở máy tool (`%APPDATA%\GPLX_Sync\history`): khóa đích/nguồn, ngày sync, cán bộ, danh sách `MaDK` đã tạo (ghi sau mỗi HV để không mất khi tool tắt đột ngột).
- ✅ Xem danh sách lần sync theo khóa đích; bấm **Hủy sync khóa** → xác nhận → xóa `NguoiLX` + `NguoiLX_HoSo` + `NguoiLXHS_GiayTo` của các `MaDK` trong log.
- ✅ **Tương thích ngược**: hủy được cả HV sync bằng công cụ cũ (đánh dấu `NguoiTao='SYNC'`).
- ✅ Cập nhật lại `KhoaHoc.TongSoHV` sau khi hủy (nếu bật tùy chọn); **không hoàn tác được** → xác nhận rõ số bản ghi sẽ xóa.
- ✅ File log giữ lại sau khi hủy (xóa tay khi không cần trace); file log hỏng → bỏ qua file đó, vẫn hủy được lần khác.
- ❌ Không tự xóa học viên do phần mềm khác tạo (chỉ theo log + nhóm `NguoiTao='SYNC'`).

> Nguồn: user 04/10/2026 · port rollback dual-mode sync_tool v2.0

#### [TCB-01] Tra cứu CDB đích — tra khóa, lưới HV, xem chi tiết + ảnh

**Trạng thái:** ✅ Done — 04/10/2026 (task 63; kiểm mức 1: pytest 265 pass, build sạch, Playwright 1280/1440/1920 render đúng, review-nghiepvu 4/4).
**Story:** Là nhân viên nạp DB, tôi muốn tra một khóa học ở CSDL đích CDB rồi xem danh sách học viên và chi tiết + ảnh từng người, để kiểm lại dữ liệu đã đồng bộ sang đích mà không phải mở phần mềm CDB.

**Done khi:**
- ✅ Tab **"Tra cứu CDB đích"** trong phân hệ Đồng bộ CDB (đọc **`GPLX_CDB_CSDT`** — DB đích đang chọn); tìm khóa (mọi khóa, kể cả đã BC1) theo mã/tên.
- ✅ Chọn khóa → **lưới HV** của khóa (avatar chân dung lazy-load, tìm trong lưới theo tên bỏ dấu / CCCD); hiện thống kê đầu khóa (tổng · thiếu ảnh) + cờ khóa đã BC1 / đã kết xuất DKKH.
- ✅ Mở 1 HV → **chi tiết** (họ tên, ngày sinh, giới tính, CCCD, ngày/nơi cấp, địa chỉ TT đầy đủ, hạng, MaDK, SoHoSo, TT_XuLy) + **ảnh chân dung lớn** + đường dẫn ảnh.
- ✅ **Nút "Xem chi tiết HV"** ở Bàn đồng bộ (SYNC-01) cho HV **đã có ở đích** → mở tab Tra cứu CDB, mở đúng **khóa chứa `MaDK` đích** + **tô sáng** HV đó (dùng cơ chế `khoaMa`/`noiBat`).
- ❌ Không đụng màn Tra cứu DB bên Nạp (QLY-01, đọc `GPLX_CSDT`) — màn này là bản riêng cho CDB đích.

**Edge cases:** chưa chọn CSDL đích → báo + lối tắt mở ⚙ Cấu hình · ảnh thiếu file (404) → báo rõ, không vỡ lưới · khóa rỗng → empty state.

> Nguồn: user 04/10/2026 (CHANGES #35) · tham chiếu QLY-01 (Tra cứu DB) nhưng trỏ DB đích · trạng thái đọc ở đích qua `DM_TrangThai`

#### [TCB-02] Thay ảnh chân dung HV ở CDB đích

**Trạng thái:** ✅ Done — 04/10/2026 (task 64; kiểm mức 1+2: 269 pytest pass (4 test backup/atomic), build sạch, Playwright AnhModal + cảnh báo BC1, review-nghiepvu đủ). Ghi đè thật kiểm live ở Checkpoint 14.
**Story:** Là nhân viên nạp DB, tôi muốn thay ảnh chân dung của một HV trong CDB đích ngay trên màn tra cứu, để sửa ảnh hỏng/sai mà không phải nhập lại.

**Done khi:**
- ✅ Từ chi tiết HV → mở **AnhModal** (tái dùng Y NGUYÊN của Nạp: căn 3:4 + zoom/xoay + **đổi nền** qua `/local/anh/xu-ly` rembg); nguồn ảnh để chỉnh: **file máy** hoặc **ảnh hiện có** (nạp lại .jp2 cũ để chỉnh tiếp).
- ✅ Lưu → **ghi đè đúng file `.jp2` cũ, GIỮ NGUYÊN tên file + `DuongDanAnh`** (ảnh là 1 file vật lý **dùng chung** giữa DB Nạp và DB đích → thay ảnh thì **cả 2 DB cùng đổi**); **trước khi ghi đè, sao lưu ảnh cũ sang `<tên>_BACKUP.jp2` cùng thư mục (chỉ nếu chưa có)** để khôi phục khi thay nhầm; cập nhật `ChatLuongAnh`/`NgayThuNhanAnh` ở bản ghi CDB.
- ✅ **Cho phép thay ảnh kể cả khi khóa đã kết xuất DKKH / đã BC1** — chỉ **cảnh báo** (ảnh là sửa chất lượng, cùng một người; bám tiền lệ QLY-05 Nạp cho đổi ảnh khi BC1).
- ❌ Không đổi đường dẫn/tên file ảnh (giữ chung với bản nguồn); không tạo file ảnh thứ 2.

**Edge cases:** file ảnh đang bị phần mềm CDB khóa → báo đóng app (409) · ghi .jp2 lỗi → báo, không cập nhật DB cột ảnh.

> Nguồn: user 04/10/2026 (CHANGES #35) · tái dùng AnhModal + đổi nền (QLY-05/NAP-04) · user chốt ghi đè file dùng chung

#### [TCB-03] Sửa nhân thân HV ở CDB đích

**Trạng thái:** 🔄 In Progress — bản mở rộng #37 **đã code xong (API+UI) 05/10/2026**, unit 287 pass + build + TS sạch; **chờ nghiệm thu ghi-thật tại máy CSDT** (user lái UI). Thêm **địa chỉ thường trú 2 cấp + ngày cấp CCCD + nơi cấp CCCD**; danh mục đọc từ DB đích (đã probe `GPLX_CDB_CSDT`: 34 tỉnh + xã mới + 36 Sở — đủ). Bản 5 trường (task 65, ✅ 04/10) đã **nghiệm thu ghi-thật PASS 05/10**. Chỉ mở rộng ở TCB-03 (user chốt 05/10); form Nạp QLY-01 giữ nguyên 5 trường.
**Story:** Là nhân viên nạp DB, tôi muốn sửa thông tin nhân thân của một HV trong CDB đích (họ tên, ngày sinh, giới tính, CCCD, địa chỉ thường trú 2 cấp, ngày cấp CCCD, nơi cấp CCCD), để vá sai sót dữ liệu trước khi khóa được báo cáo.

**Done khi:**
- ✅ Từ chi tiết HV → sửa **nhân thân** 5 trường có sẵn: họ tên, ngày sinh, giới tính, CCCD, nơi thường trú (dòng chữ tự do) — ghi qua SP update của CDB; đọc lại full bản ghi để giữ cột không sửa. *(task 65, đã nghiệm thu ghi-thật 05/10)*
- ⬜ **(CHANGES #37) Thêm trường sửa:** **địa chỉ thường trú 2 cấp** (chọn Tỉnh + Xã chuẩn → ghi `NoiTT_MaDVHC`/`NoiTT_MaDVQL`, không chỉ dòng chữ) · **ngày cấp CCCD** (`NgayCapCMT`) · **nơi cấp căn cước** (`NoiCapCMT` = mã `DM_DVHC`: `'00'` Cục QLHC / mã tỉnh — **đổi 06/10 CHANGES #40**, trước ghi "Sở GTVT"/`DM_DonViGTVT`). `usp_NguoiLX_Update` đã nhận sẵn các tham số này. (Nơi cư trú 2 cấp để sau; KHÔNG làm số CMND cũ vì SP update không nhận.)
- ⬜ **Bộ chọn Tỉnh/Xã + danh mục nơi cấp đọc từ DB ĐÍCH** (`target_key`), không phải DB Nạp — nếu đọc nhầm DB Nạp thì danh mục Xã/nơi cấp hiện sai. Tái dùng `ComboLoc`/`AddressCombo` nhưng cho nhận nguồn danh mục đích.
- ✅ **CHẶN sửa nếu khóa đích ĐÃ KẾT XUẤT DKKH** → báo rõ "khóa đã đăng ký khai giảng với Sở, không sửa nhân thân qua tool". **Định nghĩa "đã kết xuất DKKH" (sửa CHANGES #36, 05/10/2026):** khóa có gói **`DANG_KY_KHOA_HOC` đã gửi lên Sở/TW** (bản ghi `TRANS_CLI_HangDoiGui` tên file chứa MaKH). **KHÔNG** dùng `KhoaHoc.SoQD_KhaiGiang` — mọi khóa đều có số QĐ khai giảng nội bộ nên không phân biệt được đã/chưa gửi Sở (verify DB 05/10: 16 khóa đều có SoQD nhưng chỉ 14 đã gửi). Chi tiết: `docs/DB-GPLX_CDB_CSDT.md` §7.
- ✅ Chỉ sửa nhân thân (`usp_NguoiLX_Update`), **KHÔNG đụng** cột kết quả thi / BC1 / BC2 của hồ sơ (như thu hẹp phạm vi QLY-01).
- ❌ Không sửa ảnh ở đây (ảnh là TCB-02); không đổi khóa/xóa ở đây (TCB-04).

**Edge cases:** SP `usp_NguoiLX_Update` không có trong CDB → báo không hỗ trợ, tắt nút sửa (kiểm khi code) · CCCD trùng người khác trong khóa → cảnh báo · ngày cấp CCCD sau hôm nay → báo không hợp lệ · danh mục Xã/Sở theo DB đích (34 tỉnh + xã mới 2025 như bên Nạp).

> Nguồn: user 04/10/2026 (CHANGES #35) · mở rộng trường 05/10/2026 (CHANGES #37, chỉ TCB-03) · mốc chặn = đã kết xuất DKKH (đọc ở đích = có gói DANG_KY_KHOA_HOC gửi Sở, sửa #36) · tham chiếu QLY-01 lát 2

#### [TCB-04] Xóa HV / Đổi khóa HV ở CDB đích

**Trạng thái:** ✅ Done — 04/10/2026 (task 66; kiểm mức 1+2: 280 pytest (7 test: chặn MaBC1 xóa/đổi · khác hạng · khóa đích BC1 · giữ DuongDanAnh · không động file ảnh), build sạch, Playwright nút render; review-nghiepvu 5/5). Ghi thật (xóa/đổi khóa) kiểm Checkpoint 14 có giám sát.
**Story:** Là nhân viên nạp DB, tôi muốn xóa một HV hoặc chuyển HV sang khóa khác trong CDB đích, để dọn HV nhầm hoặc xếp lại đúng khóa.

**Done khi:**
- ✅ Xóa 1 HV (NguoiLX + NguoiLX_HoSo + GiayTo, cascade) / Đổi khóa HV sang khóa đích khác **cùng hạng** (chưa BC1).
- ✅ **CHẶN nếu HV ĐÃ BC1** — nhận biết bằng **`NguoiLX_HoSo.MaBC1` có giá trị** (đúng cái FK NO_ACTION chặn xóa; KHÔNG dùng `TT_XuLy ≥ 05` hay dòng `BaoCaoI` cấp khóa — chốt /reviewtdd 04/10) → báo rõ "HV đã lập Báo cáo 1, không xóa/đổi khóa được"; vẫn bắt lỗi FK làm lưới an toàn.
- ✅ **CHẶN nếu khóa ĐÃ KẾT XUẤT DKKH** (gửi danh sách đăng ký lên Sở — xem định nghĩa TCB-03) → **không xóa HV, không đổi khóa** (sửa CHANGES #36, 05/10/2026 — user: thêm/bớt HV ở khóa đã gửi Sở là lệch danh sách đã nộp). Áp cả **khóa đi lẫn khóa đến** khi đổi khóa. DKKH luôn trước BC1 trong quy trình nên là mốc chặn sớm hơn (bao trùm BC1); vẫn giữ chặn BC1 + bắt lỗi FK làm lưới. UI **vô hiệu nút Đổi khóa/Xóa** + ghi lý do; danh sách khóa để đổi **chỉ hiện khóa cùng hạng chưa DKKH + chưa BC1**.
- ✅ Xác nhận rõ trước khi xóa (không hoàn tác được).
- ❌ Không xóa/đổi khóa HV ở khóa đã DKKH hoặc đã BC1; không đổi sang khóa khác hạng; không đổi sang khóa đích đã DKKH/BC1.

**Edge cases:** đổi khóa mà khóa đích đã DKKH/BC1 → chặn · khóa hiện tại của HV đã DKKH → chặn (nút mờ) · không còn khóa cùng hạng chưa DKKH & chưa BC1 để chuyển → báo.

> Nguồn: user 04/10/2026 (CHANGES #35) + 05/10/2026 (CHANGES #36, nâng ngưỡng chặn lên DKKH) · đọc ở đích · tham chiếu QLY-02 (đổi khóa) + QLY-03 (xóa)

---

### 🟣 Cập nhật kết quả đào tạo (workspace riêng — tool máy CSDT)

**Trạng thái:** ⏳ Todo — nhóm mới (CHANGES #42, 07/10/2026). Nhập kết quả học tập/kiểm tra của học viên vào CSDL đích CDB `GPLX_CDB_CSDT` (bảng `NguoiLX_HoSo`) để chuyển trạng thái "Đã đăng ký khóa học" → "Đã cập nhật kết quả", thay cho việc gõ từng người trong phần mềm CDB cũ.

> Nghiệp vụ **ghi CDB đích** như SYNC/TCB (cùng Server/User/Pass, khác tên DB). **Phạm vi: CHỈ cập nhật KQĐT** (`TT_XuLy` `03`→`09` Đạt / `03`→`10` Không đạt). **KHÔNG làm kết xuất XML gửi Sở** — để phần mềm CDB cũ lo (giữ phần mã hóa truyền tin). Tool dừng ở `09`/`10`; phần mềm cũ đọc chung CDB rồi kết xuất (`09`→`12`). Ghi qua SP có sẵn `usp_NguoiLX_KetQuaDaoTao_CSDT_CapNhat`; đọc danh sách qua `usp_NguoiLX_KetQuaDaoTao_CSDT` / `_GetHocVien`. Quy đổi điểm + giờ/km theo **TT 17/2026/TT-BXD** + "Sổ theo dõi KQ học tập TT17" (tham khảo `thamkhao/`). Chi tiết schema: `docs/DB-GPLX_CDB_CSDT.md` §5. Quyết định kỹ thuật: TDD-decisions §17. **Ngoại lệ KQD-05 (CHANGES #45):** HV đã kết xuất (`12`) vẫn mở khóa sửa được **khi khóa còn gói chưa gửi** — xóa gói chưa gửi + lùi cả lô 12→09/10; **khi gói đã gửi hết** thì "sửa sau gửi" chọn từng HV có xác nhận (CHANGES #53, TDD-decisions §21); vẫn **không** kết xuất XML (TDD-decisions §19/§21).

#### [KQD-01] Chọn khóa + lọc HV theo trạng thái + lưới danh sách (băng DB đích)

**Trạng thái:** ✅ Done — chọn khóa đã BC1 (combobox gõ-tìm + đếm HV theo trạng thái) + lọc 4 nhóm + lưới xem (đọc CDB đích qua SELECT tự viết, TDD §11D.0); băng DB đích dùng chung Sync + chip "Đã kết nối DB đích" (máy·CSĐT). Backend import OK + 304 pytest; webui build + 34 vitest; **verify UI live trên CDB thật** (CSĐT 75032, 14 khóa BC1, HV thật) bám mockup `ui-mock/ketqua.html` — review-nghiepvu đủ 4 Done + 2 ❌ + 3 edge.
**Story:** Là nhân viên nạp DB, tôi muốn chọn một khóa học rồi xem danh sách học viên của khóa đó theo trạng thái cập nhật, để biết ai đã/chưa nhập kết quả mà không lẫn với học viên khóa khác.

**Done khi:**
- ⬜ **Băng nhắc CSDL đích** nổi bật trên đầu workspace (nền cam): "CSDL đích: `GPLX_CDB_CSDT` · <máy> · CSĐT <mã>". Dùng **component header dùng chung** cho cả màn Sync (nhắc nhân viên đang ghi vào máy/DB nào).
- ⬜ **Chọn khóa bằng combobox gõ-tìm** theo **tên khóa** (vd "B-K148") hoặc **MaKH**; mỗi gợi ý kèm ngày khai giảng + đếm HV theo trạng thái. **Chỉ hiện khóa đã có Báo cáo 1** (`EXISTS BaoCaoI` — khớp SP `usp_NguoiLX_KetQuaDaoTao_CSDT`).
- ⬜ **Lọc HV theo 4 trạng thái** (map `DM_TrangThai` qua `TT_XuLy`): Đã đăng ký (`03`/`04`) · Đã cập nhật KQ (`09`/`10`) · Sở từ chối (`14`) · Đang giải trình (`90`) · (Tất cả). + ô tìm nhanh theo tên/CCCD.
- ⬜ Lưới HV đọc qua `usp_NguoiLX_KetQuaDaoTao_CSDT` (phân trang) / `_GetHocVien` (1 HV): STT, họ tên, ngày sinh, CCCD, hạng, điểm (nếu có), trạng thái.
- ❌ Không dồn phẳng toàn bộ HV mọi khóa vào 1 danh sách (phải chọn khóa trước); không hiện khóa chưa BC1.

**Edge cases:** khóa không có HV ở trạng thái lọc → lưới rỗng có thông báo · mất kết nối DB đích → báo, không treo · khóa chưa BC1 không xuất hiện trong gợi ý.

> Nguồn: user 06-07/10/2026 (trao đổi module KQĐT) · đọc CDB đích như SYNC/TCB · băng DB đích = yêu cầu #2 (áp cả Sync)

#### [KQD-02] Nhập điểm gốc → quy đổi thang 10 → ghi kết quả vào CDB

**Trạng thái:** ⚠️ Partial — yêu cầu đổi 12/10/2026 (CHANGES #69): ô Giờ đường/Km đường nạp sẵn giá trị đã lưu + giờ nhận `hh:mm`. **Phần mới đã code + test (vitest `gioThucHanh`, pytest `/hoc-vien` trả giờ/km); chưa chạy giao diện trên trình duyệt và chưa ghi thật.** *Phần đã code trước đó:* **ghi thật qua SP `_CapNhat` vào CDB production chờ nghiệm thu máy CSDT** (máy dev không ghi happy-path vào CDB thật, như TCB/QLY). Đã xong + verify trên dev: nhập 5 điểm gốc inline → quy đổi /10 + 3 cờ Đạt per-môn (trên điểm thô) · tham số LT theo hạng×cờ CŨ/MỚI (lưu phía tool/khóa) · giờ sân khóa cứng + km sân điền sẵn + giờ/km đường gợi ý (cảnh báo vàng không chặn) · SoGiayCNTN tự sinh khi Đạt · chặn HV 12/13 (SP không bảo vệ 12) · ô đỏ khi thiếu điểm. **24 unit test quy đổi** + 332 pytest + webui build/34 vitest; **UI live trên CDB thật** bám mockup; review-nghiepvu đủ (đã vá edge ô-đỏ).
**Story:** Là nhân viên nạp DB, tôi muốn nhập điểm gốc các môn của học viên, hệ thống tự quy đổi về thang 10 và kết luận Đạt/Không đạt rồi ghi vào CDB, để khỏi tự tính tay và tránh ghi sai.

**Done khi:**
- ⬜ **Nhập điểm GỐC 5 môn**, app tự quy đổi về /10 (hiện ngay bên cạnh), GHI 5 điểm quy đổi vào `NguoiLX_HoSo`: Lý thuyết→`DiemKQLyThuyet` · Mô phỏng→`DiemKQMoPhong` · Sa hình (liên hoàn)→`DiemKQHinh` · Tiến lùi chữ chi→`DiemKQTienLui` · Đường trường→`DiemKQThucHanh`. **KHÔNG ghi điểm trung bình.**
- ⬜ **Công thức quy đổi** (2 đoạn tuyến tính, ngưỡng đạt = 5,0): `gốc ≥ ngưỡng` → `5+(gốc−ngưỡng)/(tối đa−ngưỡng)×5` ; `gốc < ngưỡng` → `gốc/ngưỡng×5` (làm tròn 1 chữ số). Lý thuyết nhập **số câu đúng** (ngưỡng/tổng theo hạng) · Sa hình & Đường nhập **/100** (ngưỡng 80, tối đa 100) · Mô phỏng & Chữ chi nhập thẳng **/10**.
- ⬜ **Tham số Lý thuyết theo hạng + cờ chương trình**: CŨ (TT12/2025/TT-BCA) B 30 câu/ngưỡng 27, C1 35/32 · MỚI (TT108/2026/TT-BCA) B 50/45, C1 60/54. Cờ CŨ/MỚI **tích chọn theo TỪNG KHÓA** (không nhảy theo ngày), lưu phía tool (không đụng schema CDB) — xem TDD-decisions §17.
- ⬜ **Giờ/quãng đường thực hành** (TT17/2026/TT-BXD): **Giờ sân** `TGThucHanhHinh` khóa cứng auto (B & B.01: 34 · C1: 35) · **km sân** `QDThucHanhHinh` điền sẵn sửa được (B & B.01: 240 · C1: 225) · **Giờ đường** `TGThucHanhDuong` + **km đường** `TongQDThucHanh` **để trống khi HV chưa có giá trị, chỉ gợi ý tối thiểu** (giờ ≥ ½ quy định: B.01 12 / B 20 / C1 24 · km ≥ quy định: B.01 710 / B 810 / C1 825). **HV đã có giờ/km ở DB đích → mở ra là hiện sẵn đúng giá trị đó** (sửa và lưu lại được, không bị ghi NULL đè khi chỉ sửa điểm). **Ô giờ đường nhận 2 dạng:** số thập phân (`20,5` / `20.5`) giữ nguyên như đã nhập · `hh:mm` (`20:30`) → rời ô tự đổi sang thập phân làm tròn 2 chữ số (`20,5`; `20:20` → `20,33`). Số đang lưu ở DB **là giờ thập phân**, hiển thị nguyên, không đoán lại là phút. Phân biệt B số tự động (`MaHangMoi='B.01'`, `MaHang='B11'`) vs B số sàn (`MaHangMoi='B'`, `MaHang='B1/B2'`).
- ⬜ **Kết luận Đạt do app tự tính** (không cho gõ tay), quy tắc TỪNG MÔN ≥5: `KetLuanCSDT`=Đạt ⇔ cả 5 môn ≥5 · `KQLyThuyet`=1 ⇔ LT≥5 **và** Mô phỏng≥5 · `KQThucHanh`=1 ⇔ Sa hình≥5 **và** Chữ chi≥5 **và** Đường≥5. **Bỏ điểm liệt, bỏ loại trực tiếp.** 3 cờ app tự tính rồi truyền vào SP (DB không có trigger/computed/constraint tính hộ — verify 06/10).
- ⬜ **Số giấy HTKH** `SoGiayCNTN` = `MaDK` + `'-'` + hạng mới, **tự sinh khi Đạt**. Ngày cấp HTKH `NgayRaQDTN` + TG bắt đầu/kết thúc thực tế `TGBatDau`/`TGKetThuc` điền sẵn từ ngày khóa, cho sửa.
- ⬜ Ghi qua **`usp_NguoiLX_KetQuaDaoTao_CSDT_CapNhat`** (SP tự đổi `TT_XuLy` 03→09 nếu Đạt / →10 nếu không; giữ nguyên nếu đang 90/13/14). Lưu theo **từng HV**.
- ⬜ **Khóa sửa** HV đã `TT_XuLy=12/13` (đã gửi Sở) — dòng chỉ-đọc; riêng **TT=12 có nút "Mở khóa để sửa" (KQD-05)** khi cơ sở còn gói chưa gửi, hoặc **ô tích + "Mở sửa điểm" (sửa sau gửi, KQD-05 #53)** khi gói đã gửi hết (TT=13 khóa tuyệt đối).
- ❌ Không tự quy đổi theo chương trình mới khi chưa bật cờ; không ghi điểm trung bình; không làm kết xuất XML gửi Sở.

**Edge cases:** điểm gốc vượt khung (câu > tổng, /100 > 100) → chặn nhập · giờ/km đường dưới ngưỡng gợi ý → cảnh báo vàng, không chặn · giờ gõ `hh:mm` có phút ≥ 60 (vd `20:75`) → viền đỏ, chặn Lưu · thiếu điểm bắt buộc của hạng → không cho Lưu (ô đỏ) · HV đã `12`/`13` → nút Lưu mờ (12 có lối "Mở khóa để sửa" qua KQD-05) · hạng mô tô (A) ẩn bớt ô thực hành (dữ liệu hiện chưa có HV hạng A).

> Nguồn: user 06-07/10/2026 · quy đổi từ "Sổ theo dõi KQ học tập TT17" + giờ/km TT17/2026/TT-BXD · quy tắc Đạt per-môn (user chốt A)

#### [KQD-03] Tab "Theo dõi kết xuất" (khóa-first, chỉ xem)

**Trạng thái:** ⚠️ Partial — **chưa chạy end-to-end live, chờ restart backend dev** (task 74, CHANGES #45, 07/10/2026). Đã xong + verify: master–detail khóa-first (`TheoDoiKetXuat.tsx` dựng lại từ stub) + tiến độ 5 nhóm trạng thái + panel gói cơ sở (tái dùng `GET /mo-khoa`, note "không tra được HV nằm gói nào") + lưới HV lọc Đã kết xuất (12) / Còn sót (09/10); backend thêm đếm `ketxuat` ở `/khoa` + nhóm `ketxuat` ở `/hoc-vien`. **Backend logic verify qua Python** (ds_khoa trả ketxuat, lọc ketxuat→25 HV khóa K260003) + **layout verify qua ảnh Playwright desktop 1280** (`anh-kiem/07-10-2026-KQD-03/`, đủ dấu/không tràn) + webui build pass + 336 pytest. Còn: backend dev 8000 chạy code cũ (`--reload` không bắt + không restart sạch được) → **restart tool để xác nhận live rồi nâng ✅**. Read-only (không ghi CDB) nên verify được hẳn trên dev, không cần máy CSDT.
**Story:** Là nhân viên nạp DB, tôi muốn theo dõi tiến độ kết xuất theo từng khóa — ai đã/chưa kết xuất, đợt đã gửi Sở chưa — để biết khóa nào nhập xong cần sang phần mềm cũ bấm kết xuất, mà không phải dò trong danh sách phẳng khó tìm.

**Done khi:**
- ⬜ Bố cục **master–detail theo KHÓA**: cột trái danh sách khóa (đã BC1) + thanh tiến độ "đã kết xuất X / còn sót Y" + lọc "Còn sót kết xuất"; cột phải là chi tiết khóa đang chọn.
- ⬜ Chi tiết khóa gồm: **tiến độ theo trạng thái** (đã kết xuất 12 · đã cập nhật chưa kết xuất 09/10 · chưa có điểm 03 · Sở từ chối 14 · giải trình 90) · **panel gói hàng đợi gửi** (liệt kê gói `KET_QUA_DAO_TAO` của CSĐT: tên + giờ + trạng thái Chưa gửi/Đã gửi) · **lưới HV** lọc Đã kết xuất / Còn sót.
- ⬜ Panel gói ghi rõ **không tra được HV nằm trong từng gói** (danh sách HV ở trong file nén, không có trong CSDL) — chỉ đối chiếu HV bằng cột trạng thái.
- ⬜ **Không có nút kết xuất** (kết xuất/gửi Sở thuộc phần mềm CDB cũ) — tab chỉ theo dõi + chứa lối "Mở khóa để sửa" (KQD-05) + khối đỏ **"Sửa sau gửi — chờ kết xuất lại"** (KQD-05 #53).
- ❌ Không sinh file XML, không đẩy thêm `TRANS_CLI_HangDoiGui`, không dồn phẳng toàn bộ HV của CSĐT vào 1 danh sách (phải chọn khóa).

**Edge cases:** khóa chưa có HV cập nhật → chi tiết rỗng có chú thích · khóa chưa có gói → panel gói trống · mất kết nối đích → báo, không treo.

> Nguồn: user 07/10/2026 (dựng lại khóa-first thay list phẳng) · gói lọc theo `NoiGui=CSĐT`, không nối được HV↔gói (verify DB) · mock `ui-mock/theodoiketxuat.html`

#### [KQD-04] Sửa lại kết quả HV Sở từ chối / đang giải trình

**Trạng thái:** ⚠️ Partial — **ghi thật + luồng 14/90 chờ nghiệm thu máy CSDT** (dev không có HV TT_XuLy 14/90 để chạy live; ghi CDB production). Đã xong + verify code: HV 14/90 mở lại nhập điểm (như KQD-02) + nút "Giải trình" → drawer hiện **lý do Sở từ chối (đọc `LyDoTuChoiKQDT`, SELECT riêng)** + ô giải trình; ghi `GiaiTrinh` bằng UPDATE tham số hóa ≤1000 **TRƯỚC** SP (quyết định ④-A); SP giữ nguyên TT_XuLy 14/90 (verify DB 07/10); không áp HV 12/13; sửa `tt_moi` phản ánh đúng SP. webui build + 34 vitest + 332 pytest; review-nghiepvu 9/9 đủ.
**Story:** Là nhân viên nạp DB, tôi muốn sửa lại kết quả cho học viên bị Sở từ chối hoặc đang giải trình, để nộp lại cho đúng.

**Done khi:**
- ⬜ HV ở `TT_XuLy=14` (Sở từ chối) / `90` (đang giải trình) → **mở lại cho sửa điểm** (như KQD-02) + ô nhập **giải trình**.
- ⬜ Lưu lại qua SP cập nhật (SP giữ nguyên `TT_XuLy` khi đang 90/13/14 — không tự nhảy về 09).
- ❌ Không áp cho HV đã `13` (hoàn thành). HV `12` (đã gửi Sở) sửa qua **KQD-05** (mở khóa khi còn gói chưa gửi, hoặc "sửa sau gửi" chọn từng HV khi gói đã gửi hết), không qua luồng 14/90 này.

**Edge cases:** HV không ở 14/90 → không hiện ở tab này.

> Nguồn: user 06/10/2026 (chốt làm 4 story)

#### [KQD-05] Mở khóa để sửa điểm sau kết xuất (TT_XuLy=12)

**Trạng thái:** ⚠️ Partial — task 83 (backend `POST /mo-sua-sau-gui` + `GET /sua-sau-gui` + nhật ký sqlite) và task 84 (UI lưới/hộp xác nhận/chip+băng cam/khối đỏ KQD-03) **code xong 10/10/2026**: 11 unit test + 358 pytest, tsc/38 vitest/build pass, Playwright 1280/1440/800 không tràn (`anh-kiem/10-10-2026-KQD-05-sua-sau-gui/`, API mock), review-nghiepvu đủ. **Còn:** ghi thật vào CDB production (lùi 12→09/10 + nhật ký + sửa điểm + kết xuất lại bằng phần mềm CDB) **chờ nghiệm thu máy CSDT**; backend dev 8000 đang chạy code cũ → restart tool để chạy UI live. Yêu cầu đổi (CHANGES #53): thêm lối **"Sửa sau khi đã gửi Sở" chọn từng HV** thay khóa cứng M1; phần đã code bên dưới (cổng B-1 + mở khóa mức cơ sở) vẫn giữ, chờ nghiệm thu máy CSDT. *Trước #53 là ⚠️ Partial —* code xong cả 2 task, **chờ restart backend dev + nghiệm thu máy CSDT** (CHANGES #45, 07/10/2026). Task 76 backend (`GET/POST /local/ketqua/mo-khoa`, cổng B-1 + lùi mức cơ sở + guard KetLuanCSDT NULL + 409/M1) — verify qua Python/DB dev: cổng B-1 + 409 không ghi đúng. Task 77 UI: `MoKhoaModal.tsx` (2 ca mở được/khóa cứng bám mock) + nút "Mở khóa" ở **cả 2 tab** (dòng 🔒 HV 12 ở KQD-02 + header lưới "Đã kết xuất" ở KQD-03) + làm tươi sau mở; webui build pass + 336 pytest. **Còn:** (a) backend dev 8000 chạy code cũ → **restart tool** để chạy UI live; (b) happy-path xóa gói+lùi HV cần **máy CSDT** (dev hiện 2 gói đều đã gửi → chỉ test được ca khóa cứng M1).
**Story:** Là nhân viên nạp DB, khi lỡ nhập sai điểm cho học viên đã kết xuất nhưng đợt chưa gửi đi Sở, tôi muốn mở khóa để sửa lại rồi kết xuất lại, mà không phải chờ Sở từ chối.

**Done khi:**
- ⬜ **Cổng mở khóa (B-1):** nút "Mở khóa để sửa" trên HV `TT_XuLy=12` **chỉ bật khi CSĐT còn gói KQĐT chưa gửi** — `EXISTS TRANS_CLI_HangDoiGui WHERE KieuDuLieu='KET_QUA_DAO_TAO' AND NoiGui=<mã CSĐT> AND TrangThai='0'`. Lọc theo `NoiGui` (không parse tên file) để không đụng gói CSĐT khác.
- ⬜ **Hành vi mở khóa (B-1a, mức CƠ SỞ):** xóa (các) gói chưa gửi của CSĐT qua `usp_TRANS_CLI_HangDoiGui_Delete` + lùi **MỌI HV đang `TT_XuLy=12` của cơ sở (mọi khóa)** về 09/10 → khớp phạm vi xóa gói (buộc quét cả CSĐT), tránh HV khóa khác treo "12 không gói". HV `12` mà chưa có kết luận (bất thường) → bỏ qua + cảnh báo, không ép Không-đạt oan. Sau đó nhân viên sửa điểm (KQD-02) rồi **kết xuất lại ở phần mềm CDB cũ**.
- ⬜ **Cảnh báo trước khi mở:** modal nêu rõ "mở khóa **toàn bộ HV đã kết xuất chưa gửi của cơ sở (N người · M khóa)**" + các bước + ô lý do (ghi vào `GiaiTrinh`).
- ⬜ **Hết gói chưa gửi → KHÔNG khóa cứng nữa; chuyển sang lối "Sửa sau khi đã gửi Sở" (CHANGES #53, thay M1).** Lối "Mở khóa" cũ ở trên chỉ dùng khi còn gói chưa gửi. Thông báo vẫn nói **mức đợt** — liệt kê gói đã gửi + **"hệ thống không xác định được HV nằm gói nào"** (danh sách HV ở trong file nén).
- ⬜ **Sửa sau gửi — chọn từng HV (chỉ bật khi cơ sở KHÔNG còn gói chưa gửi):** *Lưới KQD-02:* HV `12` hiện chip xám "Đã gửi Sở", ô điểm khóa, **có ô tích chọn** (HV `13` không có); chọn ≥1 → thanh dưới "Đã chọn N HV đã gửi Sở · [Mở sửa điểm]". *Hộp xác nhận:* danh sách HV + điểm hiện tại; cảnh báo (Sở đã nhận bản cũ · phải kết xuất lại ngay bằng phần mềm CDB · Sở trả kết quả lúc chưa kết xuất lại thì HV bị kẹt vì phản hồi Sở chỉ nhận HV đang `12`); **ô Lý do bắt buộc ≤1.000 ký tự** (ghi `GiaiTrinh`); tích **"Tôi sẽ kết xuất lại ngay bằng phần mềm CDB"**; nút "Mở sửa" chỉ bật khi đủ lý do + đã tích.
- ⬜ **Hành vi mở sửa sau gửi:** chỉ lùi **các HV được chọn** `12`→09/10 (theo `KetLuanCSDT`: Đạt→09, Không đạt→10), **KHÔNG xóa gói đã gửi**, HV `KetLuanCSDT` NULL → bỏ qua + cảnh báo, `13` từ chối. Tool **lưu nhật ký** (điểm trước · lý do · người · giờ) phía tool. Sau đó sửa/bổ sung điểm như KQD-02 (ô trống giữ nguyên, không bị xóa — dùng sửa lẻ KQD-06).
- ⬜ **Nhắc kết xuất lại:** HV đã mở sửa mang chip cam **"Sửa sau gửi — chưa kết xuất lại"** + băng cam đầu khóa; tab KQD-03 có khối đỏ **"Sửa sau gửi — chờ kết xuất lại"** (HV · khóa · người mở · lúc mở `dd/mm/yyyy HH:mm` · lý do · điểm trước→sau); dòng **tự biến mất khi HV về lại `12`** (phần mềm CDB kết xuất lại).
- ⬜ **Nút ở CẢ 2 tab:** trên dòng 🔒 ở "Cập nhật KQĐT" (KQD-02) + ở "Theo dõi kết xuất" (KQD-03).
- ⬜ **Nới chặn 409 có kiểm soát:** endpoint mở-khóa là ngoại lệ duy nhất cho `TT=12`; mọi đường ghi khác vẫn chặn 12/13. **TT=13 khóa tuyệt đối** (Sở đã duyệt).
- ❌ Không mở TT=13; không tự kết xuất lại / không sinh XML (file KQĐT có chữ ký số của phần mềm CDB — PM cũ lo); không đoán HV nằm gói nào; **không xóa gói đã gửi**; "Mở sửa sau gửi" không dùng khi còn gói chưa gửi (dùng "Mở khóa" cũ để gói chưa gửi không mang điểm cũ).

**Edge cases (sửa sau gửi):** Sở trả kết quả (13/14) lúc HV đang mở-sửa chưa kết xuất lại → phản hồi không khớp (SP chỉ nhận `12`) → HV kẹt: cảnh báo trước ở hộp xác nhận + khối đỏ nhắc · HV đã mở sửa nhưng chưa sửa gì rồi kết xuất lại → vẫn gửi bản cũ lần 2 (chấp nhận, hỏi Sở/hỗ trợ CDB cách Sở xử lý 2 bản) · 2 người mở cùng HV → lần sau HV không còn `12` → bỏ qua · mất kết nối giữa chừng → HV nào đã lùi vẫn sửa được, chưa lùi giữ `12`.

**Edge cases:** còn gói chưa gửi nhưng của CSĐT khác (dữ liệu test lẫn máy) → lọc `NoiGui` loại ra → coi như không có gói → khóa cứng · xóa gói xong SP lỗi giữa chừng → báo lỗi, HV đã lùi 09/10 vẫn sửa được · 2 nhân viên mở cùng lúc → thao tác mức cơ sở, lần sau không còn gói → tự khóa · HV khóa khác đang xem cũng bị lùi 12→09/10 (hệ quả cố ý của mức cơ sở — modal báo trước "mọi khóa").

> Nguồn: user 07/10/2026 (chốt B-1 + B-1a mức cơ sở + M1, nút 2 tab) · DB không nối HV↔gói nên thao tác ở mức cơ sở (verify live 07/10) · TDD §11D.7 · decisions §19 · mock `ui-mock/theodoiketxuat.html`
> **Bổ sung 10/10/2026 (CHANGES #53):** user chốt sửa sau gửi chọn-từng-HV (thay M1 khóa cứng) + UI 4 phần · verify DB 10/10: `usp_CSDT_PheDuyetKQDT_TiepNhan` chỉ nhận HV `TT_XuLy='12'`; file KQĐT ký số RSA nên không tự kết xuất · TDD §11D.7b · decisions §21.

#### [KQD-06] Sửa lẻ / xóa điểm đã lưu (HV chưa kết xuất)

**Trạng thái:** ⚠️ Partial — code xong, **chờ restart backend + nghiệm thu máy CSDT** (CHANGES #48, 07/10/2026). Backend: `ket_qua_hon_hop` (sửa lẻ giữ quy-đổi môn cũ) + `POST /local/ketqua/xoa-diem` (reset về 03, chỉ 09/10, 409 nếu khác) — verify qua **4 unit test** (340 pytest). Frontend `CapNhatKQDT.tsx`: Lưu nhận sửa lẻ (1 môn, giữ điểm cũ) + nút "Xóa điểm" trong drawer có xác nhận — **verify render live** (Lưu bật khi gõ 1 môn; nút Xóa hiện cho HV 09/10). **Còn:** write thật (sửa lẻ ghi đè + xóa reset) cần restart backend (đang chạy code cũ) + máy CSDT.
**Story:** Là nhân viên nạp DB, khi lỡ nhập sai điểm cho học viên **đã cập nhật nhưng chưa kết xuất**, tôi muốn sửa lại chỉ môn sai hoặc xóa điểm để nhập lại, mà không phải gõ lại cả 5 môn.

**Done khi:**
- ⬜ **Sửa lẻ:** HV đã cập nhật (`TT_XuLy` 09/10) → sửa 1 hoặc vài môn, **các môn không sửa GIỮ điểm đã lưu** (truyền lại điểm quy đổi đã lưu, KHÔNG tính ngược ra điểm gốc để tránh lệch làm tròn); bấm Lưu **không bắt điền đủ 5 ô**.
- ⬜ **Xóa điểm:** nút "Xóa điểm" trên dòng HV 09/10 → **xác nhận** → đưa HV **về chưa có điểm**: `TT_XuLy='03'`, NULL 5 điểm (`DiemKQ*`) + 3 cờ (`KQLyThuyet`/`KQThucHanh`/`KetLuanCSDT`) + `SoGiayCNTN`. Qua **UPDATE trực tiếp** (SP `_CapNhat` chỉ đặt 09/10, không lùi được 03 — verify 07/10).
- ⬜ **Chỉ áp HV chưa kết xuất (09/10).** HV `12` phải "Mở khóa" (KQD-05) trước; `13` khóa tuyệt đối; `14`/`90` sửa qua luồng giải trình (KQD-04) — không áp xóa/sửa-lẻ ở đây.
- ⬜ **Xác nhận trước khi xóa** (đổi dữ liệu đã ghi vào CDB thật).
- ❌ Không xóa/reset HV `12`/`13`/`14`/`90`; không "xóa" khi HV chưa có điểm (nút mờ); không sinh XML.

**Edge cases:** HV đã có `SoGiayCNTN` (Đạt) → xóa điểm xóa luôn số giấy · sửa lẻ mà HV chưa có điểm cũ nào → coi như nhập mới (phải đủ 5) · xóa xong HV về 03 → biến khỏi lọc "Đã cập nhật", quay lại "Đã đăng ký".

> Nguồn: user 07/10/2026 (sau khi dùng thử KQD-02) · SP không reset được → UPDATE trực tiếp (verify DB 07/10) · điểm lưu là quy đổi /10 → giữ môn cũ bằng truyền lại quy đổi · TDD §11D.8

#### [KQD-07] Kiểm trước kết xuất (theo từng khóa, chỉ đọc)

**Trạng thái:** ✅ Done — task 119 (backend) + task 120 (UI) xong 12/10/2026: luật `hv_chua_du` + `GET /local/ketqua/kiem-truoc` + `GET /local/ketqua/luat`, khung "Kiểm trước kết xuất" ở màn Cập nhật KQĐT; tool 693 pytest · webui 65 vitest · Playwright 5 ca với API giả (chưa chạy UI với DB thật).
**Story:** Là nhân viên nạp DB, trước khi sang phần mềm CDB cũ bấm kết xuất, tôi muốn một danh sách các học viên của khóa còn thiếu điểm, thiếu giờ thực hành hoặc thiếu kết luận, để sửa hết một lượt rồi mới kết xuất, không phải gửi Sở xong mới phát hiện thiếu rồi mở khóa sửa lại.

**Done khi:**
- ⬜ Ở màn Cập nhật KQĐT, sau khi chọn khóa có nút **"Kiểm trước kết xuất"**; bấm ra khung kết quả của **đúng khóa đang chọn** (không quét cả cơ sở).
- ⬜ Đầu khung hiện tóm tắt: **N học viên đủ điều kiện kết xuất · M học viên còn thiếu**, kèm đếm theo từng loại thiếu.
- ⬜ Mỗi học viên còn thiếu hiện một dòng (họ tên · CCCD · trạng thái) kèm **chip lý do**, một học viên có thể có nhiều chip: **Chưa có điểm** (chưa nhập môn nào) · **Thiếu môn** (có điểm nhưng thiếu môn bắt buộc của hạng, nêu rõ môn nào) · **Thiếu giờ/km thực hành** (giờ sân/km sân/giờ đường/km đường còn trống) · **Thiếu kết luận** (đã có trạng thái cập nhật mà chưa có kết luận Đạt/Không đạt — bất thường).
- ⬜ "Môn bắt buộc" lấy **đúng luật ô đỏ của KQD-02** — **cả 5 môn** với mọi hạng ô tô — không tạo luật thứ hai. **Hạng mô tô (mã hạng bắt đầu `A`) không xét** (không nhập kết quả đào tạo ở tool này): không vào danh sách, chỉ đếm riêng.
- ⬜ Học viên **Chưa có điểm** thì **không hiện thêm** chip "Thiếu giờ/km thực hành" (chưa có điểm thì chắc chắn chưa có giờ/km, hiện thêm chỉ làm rối).
- ⬜ Màn nhập điểm KQD-02 **giữ nguyên** (vẫn chặn lưu khi còn môn trống); "chỉ nhắc, không chặn" áp cho khung kiểm trước kết xuất.
- ⬜ Giờ/km đường **thấp hơn mức gợi ý tối thiểu** (KQD-02) chỉ hiện **cảnh báo vàng**, không tính là "thiếu".
- ⬜ Bấm một dòng → mở đúng học viên đó ở lưới nhập điểm (KQD-02) để sửa.
- ⬜ Chỉ xét học viên `TT_XuLy` 03/04 (chưa có điểm) và 09/10 (đã cập nhật, chưa kết xuất). HV đã `12`/`13`/`14`/`90` không đưa vào danh sách.
- ⬜ Khung có ghi chú: *"Kiểm tra này chỉ nhắc, không chặn. Kết xuất do phần mềm CDB cũ làm."*
- ❌ Không ghi DB; không chặn kết xuất; không tự sửa điểm; không sinh XML; không quét nhiều khóa một lượt.

**Edge cases:** khóa không có học viên → "Khóa chưa có học viên" · khóa toàn học viên mô tô → "Khóa mô tô — không xét kết quả đào tạo" kèm số học viên (không báo "chưa có học viên") · mọi học viên đều đủ → "Khóa đủ điều kiện kết xuất" (không hiện danh sách rỗng) · mất kết nối DB đích → báo, không treo · học viên vừa được sửa ở lưới → bấm "Kiểm lại" làm tươi.

> Nguồn: user 12/10/2026 (tư vấn bổ sung theo schema DB đích, chốt "theo từng khóa"; sau đó chốt "nhập kết quả học tập chỉ nhập cho hạng ô tô thôi, chưa nhập thì chỉ cảnh báo vẫn cho lưu các ô đã nhập" → cả 5 môn, bỏ mô tô; chốt qua mock: ẩn chip giờ/km khi chưa có điểm, thông điệp khóa mô tô) · luật ô bắt buộc/giờ-km: KQD-02 · mock `ui-mock/ketqua.html` (nút + khung kiểm trước) · TDD §11D.9

#### [KQD-08] Nạp giờ/km thực hành đường từ file PDF DAT (theo từng khóa)

**Trạng thái:** ⚠️ Partial — CHANGES #69 (12/10/2026). **Đã xong + verify trên dev:** đọc 4 PDF mẫu (60/30/64/32 dòng) · kiểm mã khóa · khớp theo `MaDK` trên **DB dev thật** (2 khóa có sẵn: 30/30 và 31/32 dòng khớp, 1 dòng chưa chạy DAT bỏ tick) · bảng xác nhận · lưu một transaction chỉ 2 cột (+`NgaySua`) · tool 747 pytest · webui 79 vitest + build · Playwright 98 ca (có 2 ca hộp thoại nạp PDF: sửa hh:mm → thập phân, tô "đã sửa", sai dạng chặn Lưu, Lưu gửi số đã sửa; backend giả). **Chưa kiểm:** ghi thật vào CDB production (chờ nghiệm thu máy CSDT).
**Story:** Là nhân viên nạp DB, tôi muốn nạp file PDF "Báo cáo kết quả đào tạo thực hành lái xe trên đường" tải từ hệ thống DAT, xem bảng đối chiếu rồi lưu giờ/km đường cho cả khóa một lượt, để khỏi gõ tay từng học viên.

**Done khi:**
- ⬜ Ở màn Cập nhật KQĐT, sau khi chọn khóa có nút **"Nạp giờ/km từ PDF DAT"**; chọn file `.pdf` (≤ 5 MB) → hệ thống đọc **mã khóa + bảng** trong file (cột: Mã học viên · Họ và tên · Ngày sinh · Tổng thời gian `hh:mm` · Tổng quãng đường `1.008,19` · Ghi chú).
- ⬜ **Mã khóa trong file khác khóa đang chọn** → báo lỗi đỏ, **không cho đi tiếp** (chống nạp nhầm khóa). File không phải báo cáo DAT / không đọc được bảng → báo rõ, không ghi gì.
- ⬜ Khớp học viên theo **"Mã học viên" trong file ↔ mã đăng ký (`MaDK`) ở DB đích**, chỉ trong khóa đang chọn. *(Đã kiểm trên DB dev 12/10/2026: 62/62 dòng của 2 khóa có trong DB trùng `MaDK`, mã khóa trong file trùng `MaKhoaHoc`.)*
- ⬜ **Bảng xác nhận** (chưa ghi gì): STT · Họ tên · Mã HV · **Giờ đường (cũ → mới)** · **Km đường (cũ → mới)** · Tình trạng. Giờ `hh:mm` đổi thập phân làm tròn 2 chữ số (`16:19` → `16,32`), km chuẩn số VN. Tình trạng: ✔ Khớp (tick sẵn nếu có thay đổi) · ⚠ Dưới mức gợi ý của hạng (cảnh báo vàng, vẫn tick sẵn — dùng đúng ngưỡng KQD-02) · ⚠ **Chưa chạy DAT** (giờ trống / km `0,00`) **bỏ tick sẵn**, ai cần ghi 0 thì tự tick · ✖ Không có trong khóa (không tick được) · 🔒 Đã kết xuất `12`/`13` (không tick được).
- ⬜ **Số "mới" sửa được ngay trong bảng** (giờ nhận số thập phân hoặc `hh:mm`, km nhận `725,63` / `1.008,19`): ô sửa khác số PDF được tô vàng + nhãn "đã sửa so với PDF"; ô trống/sai dạng/ngoài khung (giờ > 999, km > 99.999) thì **chặn Lưu** (không ghi số đoán). Lưu gửi đúng số đang hiện trong ô.
- ⬜ Dòng **"Không có trong khóa"** kèm **lý do** tra từ DB đích: mã đang thuộc khóa khác (đã đổi khóa) · hồ sơ không còn hoạt động · cùng họ tên + ngày sinh nhưng **lệch mã** giữa DAT và CDB · không tìm thấy (chưa nạp/đồng bộ). Tra lỗi thì hiện lý do chung, không làm hỏng xem trước.
- ⬜ Cuối bảng liệt kê riêng **học viên có trong khóa nhưng không có trong file** (chỉ để biết, không ghi).
- ⬜ Bấm **"Lưu N học viên"** → ghi `TGThucHanhDuong` + `TongQDThucHanh` của các dòng đang tick, **trong một lần ghi** (hỏng thì không dở dang) → báo "đã lưu X · bỏ qua Y" → lưới tự làm tươi.
- ⬜ Chỉ ghi **2 cột giờ/km đường**; **không đụng điểm, kết luận, trạng thái** (`TT_XuLy`) của học viên.
- ❌ Không nhận Excel; không tự suy giờ/km cho dòng thiếu; không ghi HV `12`/`13`; không kết xuất XML; không nạp nhiều khóa một lượt.

**Edge cases:** PDF nhiều trang (bảng ngắt trang) · giờ ≥ 24 (`28:26`) và km có dấu nghìn (`1.008,19`) · dòng "KHÔNG ĐẠT" giờ trống + km `0,00` · phút trong giờ ≥ 60 hoặc ô rác → dòng đó báo lỗi, các dòng khác vẫn nạp · HV có trong file nhiều lần → cảnh báo, lấy dòng đầu · mất kết nối DB đích → báo, không treo · HV bị chuyển sang `12`/`13` giữa lúc xem bảng và lúc lưu → bỏ qua dòng đó, tính vào "bỏ qua Y".

> Nguồn: user 12/10/2026 ("cho nạp file ở khóa học … ra bảng để xác nhận … lưu cho nhanh thay vì gõ tay"; chốt nhận thẳng PDF DAT, không qua Excel) · 4 file mẫu `thamkhao/DAT *.pdf` (B.01-K39/K40, C1-K10/K11, 186 dòng) · ngưỡng gợi ý: KQD-02 · TDD §11D.10

---

### 🟣 Phân công giáo viên – xe cho khóa (workspace riêng — tool máy CSDT)

**Trạng thái:** ✅ Đã chốt — 12/10/2026 (6/6 story ✅; user duyệt chốt dù chưa nghiệm thu ghi thật CDB ở máy CSĐT — Checkpoint 22/31 còn mở). Phân hệ #4 của tool: gán **giáo viên** và **xe tập lái** vào khóa, ghi **ai dạy môn gì, từ lúc nào đến lúc nào**, **xe nào đi với giáo viên nào** vào CSDL đích CDB `GPLX_CDB_CSDT` (bảng `KhoaHoc_GiaoVien`, `KhoaHoc_XeTap`), thay cho việc nhập từng dòng trong phần mềm CDB cũ.

> Nghiệp vụ **ghi CDB đích** như SYNC/TCB/KQD. **Phạm vi:** danh sách GV/xe của khóa + phân công dạy + ghép xe 1 GV–1 xe. **KHÔNG làm:** lịch học theo tuần (`LichHoc` — chỉ 1/16 khóa dùng), phân xe cho từng học viên (`MaHV` luôn trống), thêm/sửa/xóa GV hoặc xe trong danh mục (do Sở tiếp nhận), kết xuất XML. Mock đã duyệt: `ui-mock/phancong.html` (ngăn "Mô tả nghiệp vụ" trong mock là bản mô tả chi tiết). Thiết kế: TDD §11E · quyết định: TDD-decisions §22 · schema/SP đã rà soát 10/10/2026 (trao đổi CHANGES #54).
>
> **Mô hình dữ liệu CDB (một bảng hai tầng, phân biệt bằng cờ):** `KhoaHoc_GiaoVien.IsKhoaHocGiaoVien=1` = GV thuộc khóa; `=0` = dòng phân công (`NgayBD/NgayKT` datetime, `TenMonHoc`). `KhoaHoc_XeTap.IsKhoaHocXeTap=1` = xe thuộc khóa; `=0` = ghép xe (`MaGV` + `BienSoXe` + `NgayBD/NgayKT` + `DiaDiem`).
> **Luật thời gian (đúng công thức CDB, verify 10/10/2026):** `datetime`, trùng = hai khoảng **giao nhau có xét giờ**, **nửa mở** (kết thúc đúng lúc bắt đầu kế tiếp **không** trùng; cùng ngày khác giờ **không** trùng); so với **mọi khóa kể cả cùng khóa**; bắt đầu < kết thúc; bắt đầu > 00:00 ngày khai giảng; kết thúc < hết ngày bế giảng. **CDB không tự cưỡng chế** (schema không ràng buộc; chỉ SP `usp_CheckWarning*` do UI CDB gọi) → tool tự kiểm trước khi ghi. Không chỉnh giờ = ghi `00:00 → 00:00` ("Theo ngày") như dữ liệu CDB đang có.

#### [PCG-01] Chọn giáo viên của khóa (bước ①, kèm thao tác hàng loạt)

**Trạng thái:** ✅ Done — bản nháp ở trình duyệt; ghi CDB thuộc PCG-04. Kiểm với API giả (chưa chạy trên CDB thật); /kiemthu 11/10/2026 đã sửa lỗi gỡ GV mà giữ dòng phụ thuộc
**Story:** Là nhân viên cơ sở, tôi muốn chọn nhanh các giáo viên sẽ dạy một khóa từ danh mục giáo viên đang hoạt động, để khóa có danh sách GV đúng mà không nhập từng dòng.

**Done khi:**
- ⬜ Chọn **khóa** bằng combobox (chỉ khóa của CSĐT hiện tại) + hiện hạng, ngày khai giảng → bế giảng, trạng thái DKKH; băng cam "ghi CSDL đích" dùng chung với KQĐT/Sync.
- ⬜ Danh sách trái = GV **đang hoạt động** chưa thuộc khóa (tìm tên/mã, lọc loại **TH** Thực hành · **LT** Lý thuyết · **AL** Lý thuyết + Thực hành); danh sách phải = GV của khóa. Mỗi GV có huy hiệu: loại, "Đã ngừng", "Chỉ dạy hạng X" khi lệch hạng khóa **và GV dạy thực hành** (loại TH/AL; GV lý thuyết không cảnh báo hạng; khóa B/C1: hạng được đào tạo B, C1, C, D… đều hợp — user 10/10/2026), "Đang ở khóa Y đến dd/mm" khi khóa kia chưa bế giảng.
- ⬜ **Thêm từng GV**: GV có cảnh báo (lệch hạng/đang dạy khóa khác) → hộp nêu lý do, vẫn thêm được; GV đã ngừng → không thêm được.
- ⬜ **Hàng loạt:** tích nhiều GV → "Thêm N GV" (hộp xem trước từng GV: hợp lệ / cảnh báo / không thêm được + lý do); nút "Chọn GV TH hợp hạng" (loại **TH và AL**, đang hoạt động, đúng hạng, không chạy khóa khác — CHANGES #58); "Gỡ N GV".
- ⬜ **Gỡ GV khỏi khóa** → hộp xác nhận liệt kê **đúng các phân công + ghép xe sẽ bị xóa theo** (chỉ trong khóa này).
- ❌ Không thêm/sửa/xóa giáo viên trong danh mục; không đổi `TrangThai` GV.

**Edge cases:** GV đã có phân công trong khóa nhưng chưa thuộc danh sách (dữ liệu cũ) → hiện đỏ "Ngoài danh sách khóa" kèm nút "Thêm GV vào khóa" · danh sách GV rỗng → báo "chưa đồng bộ danh mục GV" · khóa đã gửi DKKH → băng cảnh báo (vẫn sửa được).

> Nguồn: user 10/10/2026 (mock `phancong.html` bước ①) · luật badge dựa `usp_CheckWarningGiaoVien` · TDD §11E.3

#### [PCG-02] Phân công dạy: môn + thời gian (bước ②, kèm hàng loạt)

**Trạng thái:** ✅ Done — từng GV + hàng loạt, bản nháp ở trình duyệt; ghi CDB thuộc PCG-04. Kiểm với API giả (chưa chạy trên CDB thật)
**Story:** Là nhân viên cơ sở, tôi muốn ghi mỗi giáo viên dạy môn nào từ lúc nào đến lúc nào, để khóa có lịch phân công đúng và không bị trùng với khóa khác.

**Done khi:**
- ⬜ Ô **"Ngày bắt đầu thực hành của khóa"** đầu bước ②: **để trống, nhân viên tự nhập, không gợi ý/không tự tính** (bắt buộc trước khi dùng nút Thực hành); nhãn ghi rõ "không phải thời gian dạy lý thuyết"; khóa đã có phân công TH trong CDB thì hiện ngày thật; đổi ngày → hỏi có cập nhật cho N phân công TH chưa chỉnh riêng.
- ⬜ Khung nhập phân công: ô lớn nổi bật **★ Thực hành lái xe** (1 bấm = chọn môn + điền từ ngày bắt đầu thực hành → đến ngày bế giảng, sửa được) + 8 môn khác (chọn 1 hoặc nhiều; khi code lọc theo hạng khóa từ `DM_HangDT_MonHoc` nếu có cấu hình). Chip phân công môn Thực hành tô màu riêng để nhìn nhanh.
- ⬜ **Từ ngày / Đến ngày** là bộ chọn lịch, giới hạn trong khóa; **ô tích "Chỉnh giờ"** (mặc định tắt = ghi `00:00 → 00:00`, nhãn "Theo ngày"); bật → chọn **giờ bắt đầu/kết thúc bước 30 phút** (tròn giờ hoặc :30, danh sách chọn, không gõ tự do) + nút tắt "Sáng 07:30–11:30", "Chiều 13:30–17:30", "Cả ngày 07:30–17:30"; nhiều ngày + có giờ → ghi chú "tính liên tục, chiếm cả đêm". Dòng cũ có giờ lẻ (vd 11:34) giữ nguyên nếu không đụng, sửa giờ thì chọn lại theo bước 30 phút.
- ⬜ Điền nhanh cho GV lý thuyết: "nối tiếp sau phân công trước", "+1 tuần" (không có giá trị mặc định cho độ dài).
- ⬜ **Kiểm tra ngay trong khung nhập** (ô "Kiểm tra ngay" đặt sát nút Lưu, chữ lớn): nêu lỗi chặn/cảnh báo theo luật PCG-04; chặn → không lưu được.
- ⬜ **Hàng loạt:** tích nhiều GV → "Phân công cho N GV" (cùng môn + cùng khoảng thời gian; xem trước từng GV, **GV có lỗi chặn bị bỏ qua kèm lý do, không chặn cả lô**) · "Dời ngày kết thúc thực hành cho N GV" (khi bế giảng dời; xem trước từng GV) · nút "Áp Thực hành lái xe cho N GV TH chưa có".
- ⬜ Sửa/xóa từng phân công; xóa phân công Thực hành **cuối cùng** của GV → báo sẽ xóa theo ghép xe của GV đó.
- ⬜ Ghi `TenMonHoc` = danh sách **mã môn** ngăn dấu phẩy (vd `"1,8"`), `MaMonHoc` = NULL (định dạng phần mềm CDB từ 29/07/2026).
- ❌ Không gợi ý/tự tính ngày bắt đầu thực hành; không tạo lịch tuần `LichHoc`; không batch phân công lý thuyết khác môn/khác ngày giữa các GV.

**Edge cases:** phân công kết thúc đúng lúc phân công kế bắt đầu (cùng ngày biên) → hợp lệ (nối tiếp) · sáng và chiều cùng ngày → hợp lệ · lịch "cả giai đoạn" 00:00 của GV chiếm mọi giờ → thêm lịch có giờ nằm trong khoảng đó cho cùng GV bị chặn · "1 ngày" ở chế độ Theo ngày (từ = đến) → chặn "bắt đầu phải trước kết thúc, hãy chỉnh giờ" · GV loại AL dạy được cả hai nhóm môn (không chặn theo loại).

> Nguồn: user 10/10/2026 (mock + các quyết định: môn Thực hành nổi bật, ngày bắt đầu thực hành để trống, giờ bước 30 phút, batch) · luật datetime verify DB 10/10/2026 · TDD §11E.4

#### [PCG-03] Chọn xe vào khóa và ghép xe cho giáo viên thực hành (bước ③)

**Trạng thái:** ✅ Done — chọn xe + ghép xe + gợi ý ghép xe, bản nháp ở trình duyệt; ghi CDB thuộc PCG-04. Kiểm với API giả (chưa chạy trên CDB thật)
**Story:** Là nhân viên cơ sở, tôi muốn chọn xe tập lái dùng cho khóa và ghép mỗi giáo viên thực hành với một xe theo khoảng ngày, để khóa có xe–GV rõ ràng và không dùng nhầm xe hết hạn hoặc đang chạy khóa khác.

**Done khi:**
- ⬜ "**Xe của khóa**" hiển thị gọn (dải chip: biển số · trạng thái · gỡ); "Thêm xe" mở danh sách xe đang hoạt động (hạng xe, hạn giấy phép, xe đang ở khóa khác); xe đã ngừng không thêm được; xe hết hạn vẫn thêm được vào danh sách nhưng **bị chặn khi ghép**.
- ⬜ **Ghép xe:** mỗi GV có phân công "Thực hành lái xe" chọn **1 xe** từ danh sách xe của khóa, kèm từ ngày–đến ngày (mặc định theo phân công thực hành, ghi `00:00`, "Theo ngày") và địa điểm điền sẵn = **giá trị cơ sở hay dùng nhất** trong các ghép xe cũ, chưa có thì *"tại trung tâm Thành Đạt và trên đường"* (CHANGES #58); GV có nhiều đợt thực hành cách quãng → điền sẵn từ đợt đầu đến đợt cuối; mỗi xe chỉ 1 GV, mỗi GV chỉ 1 xe trong cùng khoảng thời gian.
- ⬜ **"Gợi ý ghép xe":** đề xuất xe còn trống, đã thuộc khóa, giấy phép còn hạn, ưu tiên đúng hạng cho các GV chưa có xe; **xem trước, sửa xe từng dòng, tích dòng muốn dùng rồi "Áp"** — không tự ghi.
- ⬜ Đổi xe của GV → hỏi xác nhận; gỡ xe khỏi khóa → liệt kê ghép xe sẽ bị xóa theo; "Bỏ ghép".
- ❌ Không ghép xe hàng loạt tự động; không gán xe cho học viên; không sửa danh mục xe.

**Edge cases:** xe lệch hạng khóa (vd xe B số sàn vào khóa B01) → cảnh báo, không chặn · xe đang chạy khóa khác chưa bế giảng → chỉ hiện ghi chú ở chỗ chọn xe (không phải cảnh báo ở cột kiểm tra); **trùng thời gian (chồng giờ) → cảnh báo, vẫn ghép bình thường** (user 10/10/2026) · GV thực hành chưa có xe → cảnh báo (không chặn ghi) · xe thuộc khóa nhưng chưa ghép → thông tin.

> Nguồn: user 10/10/2026 (mock bước ③) · luật theo `usp_CheckWarningLichLSDXeTap`/`usp_CheckWarningXeTap` · TDD §11E.5

#### [PCG-04] Kiểm tra 3 mức, bản nháp và ghi vào CDB

**Trạng thái:** ✅ Done — luật + bản nháp + ghi + hiển thị lỗi; kiểm với API giả/test cursor giả, ghi thật chưa nghiệm thu ở máy CSDT; /kiemthu 11/10/2026 đã sửa luật "dữ liệu cũ" hạ nhầm dòng mới/dòng mồ côi (`tool/tests/test_phancong_kiemthu.py`)
**Story:** Là nhân viên cơ sở, tôi muốn mọi thay đổi nằm trong bản nháp, được kiểm chặt theo luật và chỉ ghi vào CDB sau khi tôi xem lại, để không ghi nhầm vào dữ liệu thật.

**Done khi:**
- ⬜ **Kiểm tra 3 mức, chạy lại mỗi thay đổi:** ⛔ **Chặn** (không lưu/ghi được): ngoài phạm vi khóa · bắt đầu ≥ kết thúc · chưa chọn môn · GV chưa trong khóa · GV/xe đã ngừng · xe chưa thuộc khóa · xe hết hạn giấy phép trước bế giảng · ghép xe cho GV không dạy thực hành. ⚠ **Cảnh báo** (ghi được sau xác nhận): GV/xe **trùng thời gian có xét giờ** (khóa khác hoặc cùng khóa; cùng ngày khác giờ không tính là trùng) · 1 xe 2 GV / 1 GV 2 xe chồng giờ · lệch hạng xe · lệch hạng GV (**chỉ khi GV có phân công Thực hành lái xe**; khóa B/C1 xem bảng hợp hạng TDD §11E.7) · thực hành chưa tới bế giảng (**tính theo cả GV**: đợt thực hành kết thúc xa nhất vẫn trước bế giảng; 1 cảnh báo/GV) · GV lý thuyết (LT) được phân công môn Thực hành · GV chưa phân công · GV thực hành chưa có xe · khóa đã gửi DKKH. ℹ **Thông tin**: xe chưa ghép. **Bản nháp không đổi gì → "Không có thay đổi để ghi", không hỏi xác nhận cảnh báo** (CHANGES #58).
- ⬜ **Hiển thị lỗi rõ:** thông báo ngay dưới ô/dòng sai (chữ lớn, dải màu bên trái), băng tóm tắt đầu mỗi bước ("N lỗi chặn — Tới lỗi đầu tiên"), cột "Kiểm tra khóa" bấm một lỗi → cuộn + nháy đúng dòng.
- ⬜ **Bản nháp:** thanh dưới "Chưa ghi vào CDB: N thay đổi" + "Xem các thay đổi" (liệt kê từng dòng: thêm/sửa/xóa kèm tên GV, môn, ngày, xe) + "Hủy thay đổi" (xác nhận); không ghi gì vào CDB trước khi bấm "Ghi vào CDB". Bản nháp tự giữ trên máy theo từng khóa (không mất khi F5/đóng tab; chỉ khôi phục khi CDB chưa đổi, hỏi Làm tiếp / Bỏ).
- ⬜ **"Ghi vào CDB":** bị khóa khi còn lỗi chặn; hộp xem lại tóm tắt thêm/sửa/xóa (kèm SP sẽ gọi) + **tích "đây là CSDL thật"** + (nếu có) **tích "đã xem N cảnh báo"**; server **kiểm lại toàn bộ luật** trên trạng thái CDB hiện tại trước khi ghi (không tin client).
- ⬜ Ghi từng dòng bằng SP có sẵn (TDD §11E.6); `GhiChu=''`, `NguoiTao/NguoiSua` = người đăng nhập tool; lỗi giữa chừng → báo dòng đã ghi / chưa ghi để làm tiếp; ghi xong → làm tươi dữ liệu + nhắc kết xuất lại nếu khóa đã gửi DKKH.
- ⬜ Nhật ký thao tác phía tool (ai · lúc nào · khóa · thay đổi gì) để truy vết (CDB `NguoiTao` hiện trống).
- ❌ Không dùng `usp_KhoaHoc_GiaoVien_Delete`, `usp_KhoaHoc_XeTap_Delete`, `usp_VoHieuLuc*` (xóa lan nhiều dòng/nhiều khóa) — xóa theo `MaLichLV`/`MaLichSD` từng dòng.

**Edge cases:** hai nhân viên cùng sửa một khóa → **không áp dụng** (user chốt 10/10/2026: tại một thời điểm chỉ có một người thao tác tool) · xe/GV bị ngừng giữa lúc đang soạn → lỗi chặn khi ghi · **CDB bị sửa từ lúc mở khóa (vd phần mềm CDB cũ vừa thêm phân công) → không ghi được, báo "Khóa đã bị sửa… tải lại rồi làm tiếp", bản nháp trên máy vẫn giữ (CHANGES #59)** · bấm Ghi hai lần/hai tab cùng lúc → lần thứ hai báo "đang được ghi" · mất kết nối giữa chừng → danh sách dòng đã ghi.

> Nguồn: user 10/10/2026 · schema không cưỡng chế luật (verify) · TDD §11E.6, decisions §22

#### [PCG-05] Rà soát khóa (tab thứ 2)

**Trạng thái:** ✅ Done — chỉ đọc; kiểm với dữ liệu giả (chưa chạy trên CDB thật)
**Story:** Là nhân viên cơ sở, tôi muốn thấy khóa nào đang làm dở hoặc lệch giữa danh sách và phân công, để xử lý đúng khóa cần.

**Done khi:**
- ⬜ Bảng mọi khóa của CSĐT: GV trong danh sách · GV chưa phân công · phân công ngoài danh sách · xe trong danh sách · xe chưa ghép (chỉ là thông tin, **không** làm kết luận thành "Cần xử lý") · ghép xe ngoài danh sách · kết luận Ổn / Cần xử lý (CHANGES #58).
- ⬜ Bấm một dòng → mở khóa đó ở màn Phân công theo khóa.
- ❌ Chỉ đọc; không sửa hàng loạt nhiều khóa.

**Edge cases:** khóa chưa có GV nào → "Cần xử lý" · khóa cũ chỉ có lịch xe không có danh sách xe (dữ liệu trước khi dùng danh sách) → hiện ở cột "Ghép xe ngoài danh sách".

> Nguồn: user 10/10/2026 · số liệu mẫu từ rà soát DB 10/10/2026 · TDD §11E.7

#### [PCG-06] Hạn giấy tờ xe, hạn GPLX giáo viên và GV/xe ngưng còn phân công (tab thứ 3, chỉ đọc)

**Trạng thái:** ✅ Done — task 121 (backend) + task 122 (UI) xong 12/10/2026: `phan_loai_han` + `phancong_hangiayto.py` + `GET /local/phancong/han-giay-to?ngay=30`, tab thứ 3 "Hạn giấy tờ"; tool 693 pytest · webui 69 vitest · Playwright 4 ca với API giả (chưa chạy UI với DB thật).
**Story:** Là nhân viên cơ sở, tôi muốn một bảng cho thấy xe nào sắp hết hạn giấy phép, giáo viên nào sắp hết hạn GPLX và GV/xe nào đã ngưng mà vẫn còn trong khóa chưa bế giảng, để xử lý trước khi ảnh hưởng khóa học, thay vì chỉ thấy cảnh báo khi mở từng khóa.

**Done khi:**
- ⬜ Tab mới **"Hạn giấy tờ"** ở màn Phân công GV–xe (cạnh "Phân công theo khóa" và "Rà soát khóa"), phạm vi **toàn bộ cơ sở**, chỉ đọc.
- ⬜ **Nhóm Xe:** liệt kê xe **đang hoạt động** có giấy phép xe tập lái (`NgayHHGPXTL`) hoặc giấy chứng nhận kiểm định (`NgayHHGCNKD`) **đã hết hạn (đỏ)** hoặc **còn ≤ 30 ngày (vàng)**; mỗi dòng: biển số · hạng xe · loại giấy · ngày hết hạn · số ngày còn/quá · **các khóa chưa bế giảng đang dùng xe đó**.
- ⬜ **Nhóm Giáo viên:** liệt kê GV **đang hoạt động** có GPLX (`NgayHHGPLX`) **đã hết hạn (đỏ)** hoặc **còn ≤ 30 ngày (vàng)**; mỗi dòng: mã · họ tên · hạng · ngày hết hạn · số ngày còn/quá · **các khóa chưa bế giảng đang có GV đó**.
- ⬜ **Nhóm "Đã ngưng nhưng còn phân công":** GV/xe `TrangThai=0` mà vẫn còn dòng thuộc khóa chưa bế giảng — nêu khóa nào.
- ⬜ Đầu tab hiện đếm theo nhóm và theo mức đỏ/vàng; bấm một khóa trong dòng → mở khóa đó ở màn Phân công theo khóa.
- ⬜ Ngày hết hạn trống → xếp thành mục thông tin **"Chưa khai ngày hết hạn"**, không tính đỏ/vàng.
- ❌ Không ghi DB; không đổi `TrangThai` GV/xe; không thay luật chặn "xe hết hạn trước bế giảng" của PCG-04 (luật đó vẫn xét theo từng khóa lúc ghi); không gửi thông báo ra ngoài.

**Edge cases:** không có GV/xe nào sắp hết hạn → "Không có giấy tờ nào sắp hết hạn trong 30 ngày" · xe/GV hết hạn nhưng không ở khóa nào → vẫn hiện, ô khóa ghi "Chưa dùng ở khóa nào" · giấy phép và kiểm định cùng ngày → gộp một dòng nêu cả hai loại.

> Nguồn: user 12/10/2026 (tư vấn bổ sung theo schema DB đích; chốt ngưỡng 30 ngày, đặt trong Phân công, gộp nhóm ngưng-còn-phân-công, thêm hạn GPLX giáo viên) · số liệu thật đọc DB đích 12/10/2026: 5 xe còn ≤ 30 ngày, 3 GV đã hết hạn GPLX, 1 GV còn ≤ 30 ngày, chưa có GV/xe ngưng còn phân công · mock `ui-mock/phancong.html` (tab "Hạn giấy tờ") · TDD §11E.10

---

### 🟣 Đóng gói & khởi chạy tool độc lập (chỉ tool máy CSDT)

**Trạng thái:** ⏳ Todo — nhóm mới (CHANGES #38, 05/10/2026). Mục tiêu: mang tool sang máy CSDT khác **không cần cài Python/Node**, mở như một phần mềm bình thường, lần sau dùng không phải thiết lập lại.

#### [DGT-01] Đóng gói tool thành file .exe chạy độc lập

**Trạng thái:** ⚠️ Partial — đã đóng gói (PyInstaller one-folder, `tool/tool.spec`): gói sẵn Python + pymssql/rembg/onnxruntime + model u2net + webui/dist (FastAPI phục vụ cùng cổng) + dvhc_map.sqlite; ghi dữ liệu vào `%APPDATA%\pmcsdtlx-tool` khi `sys.frozen`. **Tự kiểm trên máy dev PASS** (`pmcsdtlx-tool.exe --selftest`: pymssql/FreeTDS nạp được + rembg xóa phông ra .jp2; server sẵn sàng ~1,2s; 299 unit test pass). **Còn chờ nghiệm thu "máy sạch thật" ở CSDT** (không Python/Node → nối SQL Server + nạp/tra cứu) mới chốt ✅
**Story:** Là người triển khai, tôi muốn đóng gói tool thành **một file `.exe`** mang sang máy CSDT khác chạy được ngay, để không phải cài Python, Node hay thư viện gì trên máy đó.

**Done khi:**
- ⬜ Build ra exe (PyInstaller) **gói sẵn Python + mọi thư viện backend** (FastAPI, uvicorn, pymssql, Pillow/rembg, cryptography…) → máy đích **không cài gì thêm**.
- ⬜ Giao diện build tĩnh (`vite build`) được **FastAPI phục vụ ngay trên cùng cổng** với API → không cần Node/cổng dev 3011 riêng; đường dẫn tương đối (`BASE=""` ở bản production — đã có sẵn).
- ⬜ Dữ liệu kèm theo (`dvhc_map.sqlite`, file SQL/mẫu) được nhét vào gói; tool ghi cấu hình/nháp/ảnh tạm vào thư mục **ghi được** (`%APPDATA%` hoặc cạnh exe), không vào `Program Files`.
- ⬜ **Test trên 1 máy sạch** (không có Python/Node) → chạy được, nối SQL Server, nạp/tra cứu bình thường.

**Edge cases:** pymssql có phần biên dịch C (FreeTDS) — phải verify gói kèm chạy trên máy sạch · Windows SmartScreen cảnh báo exe chưa ký số → kèm hướng dẫn "Vẫn chạy" hoặc ký số sau · máy đích phải **tới được SQL Server + VPS qua mạng** (như hiện tại).

> Nguồn: user 05/10/2026 (CHANGES #38). Tech Stack ④ đã nêu "Tool đóng gói PyInstaller".

#### [DGT-02] Khởi chạy thuận tiện — tự mở trình duyệt, khay hệ thống, chống chạy 2 bản

**Trạng thái:** ⚠️ Partial — code xong (`app/launcher.py` + `run_tool.py` orchestration + `tool.spec` windowed/pystray). **Verify trên exe thật PASS**: windowed không console; tự mở trình duyệt nạp UI; chống chạy 2 bản (mở lần 2 → vẫn 1 tiến trình, chỉ thêm tab); dò cổng (8000 bận → nhảy 8001); khay hệ thống chạy; 5 unit test launcher + 304 test toàn bộ pass. **Còn chờ nghiệm thu thao tác khay tận tay ở máy CSDT** (bấm "Mở giao diện"/"Thoát"/"Tự chạy khi bật máy") mới chốt ✅
**Story:** Là người dùng tool, tôi muốn **nháy đúp exe là trình duyệt tự mở đúng trang**, không phải gõ địa chỉ, và lần sau dùng cũng nhanh như mở một phần mềm.

**Done khi:**
- ⬜ Mỗi lần chạy exe **tự mở trình duyệt vào đúng trang** (localhost cổng của tool); trình duyệt không bật được thì hiện sẵn địa chỉ để gõ tay.
- ⬜ Có **biểu tượng khay hệ thống** (system tray) với "Mở giao diện" + "Thoát" — thay cho cửa sổ console đen; thoát tool gọn bằng nút này.
- ⬜ **Chặn chạy 2 bản**: đang chạy rồi mà mở lại exe → **đưa tab/giao diện cũ lên trước**, không bật bản thứ hai.
- ⬜ Cổng mặc định bận → tự nhảy cổng trống và mở đúng cổng đó.
- ⬜ **Tùy chọn tự chạy khi bật máy** (bật/tắt được) — máy CSDT cố định thì bật để lúc nào cũng sẵn.

**Edge cases:** cổng 8000 bị phần mềm khác chiếm → nhảy cổng · người dùng đóng tab nhưng tool vẫn chạy khay → nhấp khay hiện lại · nhiều trình duyệt mặc định → mở trình duyệt hệ thống đang đặt.

> Nguồn: user 05/10/2026 (CHANGES #38).

#### [DGT-03] Wizard thiết lập lần đầu trên máy sạch

**Trạng thái:** ✅ Done — wizard 3 bước (tách CauHinhForm dùng chung + redirect máy sạch + endpoint kiểm môi trường) + mở token sync-targets (bước mồi) cho khối CSDL đích; build/tsc/vitest + backend mức-2 + **verify visual chrome-devtools (bước 1+2, 1280/1440, console sạch)**; review-nghiepvu OK (sửa EC1 + ca key.bin hỏng + lỗi khối ② 401). review-giaodien để Bước 7b khi chốt Feature DGT
**Story:** Là người dùng, lần đầu chạy tool trên máy mới tôi muốn được **dẫn từng bước** để khai báo kết nối, thay vì bị thả vào app trống rồi gặp lỗi khó hiểu.

**Done khi:**
- ⬜ Máy chưa có cấu hình → vào **wizard thiết lập**, KHÔNG vào thẳng màn đăng nhập (vì chưa có URL VPS thì không đăng nhập được).
- ⬜ **Bước kiểm tra môi trường:** thư mục ghi được · mạng tới VPS — đỏ mục nào thì báo cách sửa, chưa cho qua.
- ⬜ **Bước cấu hình kết nối:** SQL Server nguồn + DB đích Sync + VPS; **tái dùng nút "Kiểm tra kết nối" sẵn có** (`/local/config/test`) — **test xanh mới cho sang bước sau**.
- ⬜ **Bước đăng nhập** (qua VPS); VPS lỗi → báo rõ "không nối được máy chủ trung tâm" + nút quay lại sửa địa chỉ VPS (không bắt làm lại cả wizard).
- ⬜ **Lần sau đã có cấu hình → bỏ qua wizard**, vào thẳng (đăng nhập hoặc vào luôn nếu còn phiên — xem DGT-04).

**Edge cases:** SQL sai mật khẩu/không thấy máy/sai tên DB → báo lỗi **cụ thể**, không nói chung chung · đặt exe trong `Program Files` không ghi được → bắt lỗi sớm ở bước kiểm môi trường.

> Nguồn: user 05/10/2026 (CHANGES #38). Tái dùng `CauHinhDrawer` + `/local/config/test` + `/local/auth/login` sẵn có, chỉ xếp lại thành wizard.

#### [DGT-04] Phiên đăng nhập vĩnh viễn (đăng nhập 1 lần, chỉ Đăng xuất mới thoát)

**Trạng thái:** ⚠️ Partial — code đủ 2/2 task (69 server refresh-token + 70 tool phiên đĩa DPAPI/heartbeat) + unit test (mức 2) pass. **Task 69 đã deploy VPS + verify live 06/10/2026** (bảng `refresh_token` tạo tay trên Postgres prod; login 3 đường 200/200/401, cap_refresh cấp token, /refresh xoay cặp mới, khóa TK → refresh 401, web không gãy — Checkpoint 15 phần "Deploy VPS" ✅). **Còn chờ verify tool-side ở máy CSDT** (phiên DPAPI sống qua tắt/mở exe + heartbeat đổi refresh sau 8h) mới chốt ✅
**Story:** Là người dùng tool hằng ngày, tôi muốn **đăng nhập một lần rồi dùng mãi** — mở lại tool không phải gõ tài khoản lại — chỉ khi bấm "Đăng xuất" mới thoát.

**Done khi:**
- ⬜ Sau khi đăng nhập, **phiên lưu ra đĩa** (mã hóa an toàn, **ràng vào đúng máy + tài khoản Windows** — copy sang máy khác không mở được), **không hết hạn**.
- ⬜ **Giữ được quyền máy chủ (VPS) lâu dài:** máy chủ cấp một "vé gia hạn" khi đăng nhập, tool giữ an toàn và **định kỳ tự đổi lấy quyền mới ngầm** → thao tác kéo hồ sơ / đối soát với máy chủ **không chết sau vài giờ** dù người dùng không đăng nhập lại. Đổi thất bại / tài khoản bị khóa → tự đăng xuất.
- ⬜ Mở exe lần sau → **tự nạp phiên → vào thẳng, không hỏi đăng nhập** (token trình duyệt đã sống qua F5/đóng-mở trình duyệt; mảnh đĩa này cho sống qua cả tắt/mở exe).
- ⬜ Nút **"Đăng xuất" (đã có sẵn)** là lối ra duy nhất → xóa phiên ở đĩa + trình duyệt → lần sau mới hỏi đăng nhập lại.
- ⬜ **Thu hồi từ xa:** khi có mạng, định kỳ ngầm hỏi VPS tài khoản còn hiệu lực — VPS khóa tài khoản thì tự đá ra (không bắt người dùng bình thường đăng nhập lại).

**Edge cases:** mất khóa máy (đổi máy, dọn máy, đổi tài khoản Windows) → phiên cũ không giải mã được → đăng nhập lại (chấp nhận) · VPS không có mạng lúc khởi động → vẫn vào bằng phiên đĩa, kiểm hiệu lực + gia hạn quyền khi có mạng lại · quyền máy chủ hết hạn giữa ca → **tự gia hạn ngầm, không bắt đăng nhập lại**; vé gia hạn cũng bị thu hồi khi bấm Đăng xuất.

**Rủi ro đã nêu & chấp nhận (user 05/10):** phiên vĩnh viễn = **ai ngồi vào máy cũng vào thẳng** tool sửa/xóa hồ sơ GPLX + xem căn cước, kể cả máy bỏ không lâu ngày. Chấp nhận vì **máy nội bộ CSDT, một người dùng**. Nếu sau này máy dùng chung → cân nhắc "hỏi mật khẩu khi xóa/đổi khóa" (để sau).

> Nguồn: user 05/10/2026 (CHANGES #38). Chỉ áp cho **tool**; đăng nhập app web (HTG-01) giữ nguyên hành vi phiên thường.

---

### 🟣 Tốt nghiệp & Báo cáo 2 (workspace riêng — tool máy CSDT, DB Nạp `GPLX_CSDT`)

**Trạng thái:** ⏳ Todo — nhóm mới (CHANGES #60, 11/10/2026, prefix **TNB**). Phân hệ #5 của tool: **cập nhật tốt nghiệp** cho học viên **ô tô**, **tạo Báo cáo 2 (BC2)** và **thêm/bỏ học viên khỏi BC2** (ô tô và mô tô riêng), kèm chức năng **cứu trạng thái** học viên không tìm thấy khi lập BC2. Làm việc trên **DB Nạp** (`GPLX_CSDT`) để **phần mềm cũ (PM cũ) mở lên thấy y chang**.

> **Phạm vi:** tool làm — cập nhật/hủy tốt nghiệp ô tô · tạo số + tạo BC2 · thêm/bỏ HV khỏi BC2 · chuyển `TT_XuLy` cứu HV. **PM cũ vẫn làm:** kết xuất BC2, cập nhật kết quả BC2, đổi trạng thái HV sau khi gửi BC2, **đóng BC2** (`TrangThai=1`). **KHÔNG làm:** gửi BC2, nhập kết quả sát hạch, lập/sửa BC1.
>
> **Ràng buộc cứng:** chỉ dùng **SP có sẵn** trong DB Nạp (`usp_NguoiLX_HoSo_Update_CNTN`, `usp_BaoCaoII_Insert`, `usp_NguoiLX_HoSo_ThemHS_BC2`, `usp_NguoiLX_Update_ThemHSBC2`, `usp_NguoiLXHoSo_Update_DanhSachHocSinhBC2`, `usp_NguoiLX_HoSo_UpdateTTXLy`); **không** `INSERT/UPDATE/DELETE` trực tiếp, **không** sửa schema, **không** tạo SP mới. Tool và PM cũ **dùng chung một DB** (không staging) → mọi thứ PM cũ làm tool thấy ngay sau khi làm tươi.
>
> **Sự thật đã verify trên DB 11/10/2026:** `TT_XuLy` Nạp: 01 Nhận hồ sơ · 03 Đã nhận ảnh · **09 Đạt tốt nghiệp** · **11 Đã lập BC2** · 12 Đã gửi BC2 · 13/14 Đạt/Chưa đạt BC2 · 16/17/18 Đạt/Chưa đạt/Vắng SH · 19 Đã nhận GPLX (khác nghĩa CDB: ở CDB `12` = đã kết xuất). Ô tô: `03 → 09 → 11 → 13/14 → 16/17/18 → 19`; **mô tô không có bước tốt nghiệp**: `03 → 11 → …`. `BaoCaoII.TrangThai`: **0 = đang mở** (toàn HV ở 11), **1 = đã đóng**. 455 BC2: 329 chỉ ô tô · 130 chỉ mô tô · 0 trộn. PM cũ ghi tốt nghiệp bằng `usp_NguoiLX_HoSo_Update_CNTN` (cả 90 HV ô tô ở 09 có đủ 6 trường sổ tốt nghiệp).

> **Ngôn ngữ và cách làm giao diện (CHANGES #61):** màn hình **không** hiện mã story, tên SP hay `TT_XuLy`. Trạng thái học viên hiện bằng **tên nghiệp vụ** kèm mã nhỏ của PM cũ và một **bảng chú giải** (nút "?"): "Đã học xong, chưa tốt nghiệp" (03 ô tô) · "Đã học xong, chờ lập BC2" (03 mô tô) · "Đã tốt nghiệp, chờ lập BC2" (09) · "Đã vào BC2, chờ kết quả" (11) · "Chưa đạt BC2 — cần lập lại" (14) · "Thi sát hạch chưa đạt" (17) · "Vắng sát hạch" (18) · "Đã có kết quả cuối" (13/16/19). Chi tiết kỹ thuật gom vào mục thu gọn "dành cho IT". **Ưu tiên tự động hóa:** tích sẵn nhóm sẵn sàng, chọn hàng loạt theo khóa gốc, dán danh sách CMT, xử lý ngoại lệ tại chỗ, một nút làm xong, hoàn tác lần thêm vừa rồi.

#### [TNB-01] Cập nhật tốt nghiệp ô tô theo lô

**Trạng thái:** ⚠️ Partial — 3/3 task xong (101 đọc + xem lại, 102 ghi, 107 UI); mức 1 pass bằng kết nối giả + Playwright giả backend, **chưa ghi thật DB Nạp** (nghiệm thu máy CSDT, Checkpoint 27); sửa/hủy HV đã tốt nghiệp thuộc TNB-02
**Story:** Là nhân viên cơ sở, tôi muốn nhập sổ tốt nghiệp, quyết định và số giấy chứng nhận tốt nghiệp (CNTN) cho cả một khóa ô tô trong một lượt, để học viên được ghi nhận "Đạt tốt nghiệp" và đủ điều kiện vào BC2.

**Done khi:**
- ⬜ **Chọn theo khóa học** (không theo BC1). Danh sách HV có cột **Tên học viên · Ngày sinh · Số CMT · Tên khóa học**, cột phụ **Trạng thái** (Chưa tốt nghiệp / Đã tốt nghiệp) và **Số giấy CNTN**.
- ⬜ **Phạm vi mặc định:** HV ô tô (hạng không chứa `A`, khác `B1m`) của khóa **đã bế giảng từ "hôm nay − 1 tháng − 1 năm" đến hôm nay** (vd hôm nay 11/10/2026 → từ 11/09/2025), tức khóa năm nay và năm trước. Công tắc **"Hiện khóa cũ"** mở rộng sang mọi khóa đã bế giảng, HV khóa cũ có huy hiệu "khóa cũ". Khóa **chưa bế giảng** chỉ xem, không ghi được.
- ⬜ **Tìm** theo họ tên (gõ không dấu cũng ra), số CMT/CCCD, mã đăng ký; lọc theo khóa và trạng thái.
- ⬜ **Điền chung một lượt cho các HV đã tích:** số sổ tốt nghiệp (vd `01/XNĐT/2026`), ngày vào sổ, số quyết định (vd `100/TTTĐ`), ngày ra quyết định, ngày in giấy; khóa đã có sổ thì điền sẵn từ HV cùng khóa. Tool **không tự bịa** số/ngày quyết định.
- ⬜ **Số giấy CNTN** (dạng `N1|7282`): nhập số bắt đầu → tool đánh liên tiếp theo thứ tự tên; sửa tay từng ô; dán cột số từ Excel; **kiểm trùng ngay khi gõ** (trong lô và trong DB): chỉ chặn khi **đổi sang số đang thuộc học viên khác** — HV đang giữ đúng số đó (dù PM cũ từng cấp trùng) vẫn lưu được, hiện ghi chú "vốn đã trùng từ trước". Số sổ/quyết định/ngày là **một bộ chung** cho cả lượt ghi (cần sổ khác thì ghi theo nhóm).
- ⬜ **Lưu sổ trước, cấp số giấy sau:** HV chưa có số giấy → ghi thông tin sổ/quyết định nhưng ở lại `03`; có số giấy → sang **`09`**.
- ⬜ "Xem lại" (số HV, khoảng số giấy, cảnh báo) → "Ghi N HV": gọi `usp_NguoiLX_HoSo_Update_CNTN` từng HV (applock theo khóa); lỗi giữa chừng báo **đã/chưa ghi**, làm tiếp được.
- ❌ Không nhập kết quả thi, không gửi báo cáo, không đụng hạng mô tô.

**Edge cases:** HV đã ở 11–18 mà thiếu số giấy (~41 người) → ghi được số giấy nhưng **không đổi trạng thái**, kèm cảnh báo "báo cáo đã lập không đổi theo" · HV đã `09` → hiện "Đã tốt nghiệp", chỉ sửa được qua TNB-02 · trùng số giấy → chặn dòng đó · khóa cũ trước 2018 chưa từng có sổ (461 HV) → vẫn làm được, nhân viên nhập số quyết định thật · số chứng chỉ nghề (`SoCCN`) là tùy chọn riêng, không bắt buộc.

> Nguồn: user 11/10/2026 · `usp_NguoiLX_HoSo_Update_CNTN` (6 trường sổ) · dữ liệu 90 HV ô tô ở 09 · TDD §11F.2

#### [TNB-02] Sửa / hủy kết quả tốt nghiệp

**Trạng thái:** ⚠️ Partial — 2/2 task xong (103 backend hủy, 108 UI; sửa nhầm số giấy ở 102); mức 1 pass bằng kết nối giả + Playwright giả backend, **chưa ghi thật DB Nạp** (nghiệm thu máy CSDT, Checkpoint 27)
**Story:** Là nhân viên cơ sở, tôi muốn sửa số giấy hoặc hủy tốt nghiệp khi chọn nhầm, để dữ liệu đúng trước khi lập BC2.

**Done khi:**
- ⬜ **Sửa nhầm số giấy/sổ/quyết định:** nhập lại cho HV đang `09`; SP chỉ cập nhật thông tin, giữ `09`.
- ⬜ **Hủy tốt nghiệp:** chọn HV đang `09` → "Hủy tốt nghiệp" (hộp xác nhận nêu tên + số giấy sẽ bị xóa) → SP với số giấy rỗng đưa **`09 → 03`**; giữ nguyên thông tin sổ/quyết định để nhập lại.
- ⬜ **CHẶN** hủy/sửa khi HV **đã vào BC2** (`TT_XuLy ≥ 11` hoặc `MaBC2` có giá trị): nút khóa kèm lý do "phải gỡ khỏi BC2 trước" (TNB-05).
- ❌ Không dùng `usp_NguoiLX_HoSo_Update_HSTotNghiep` để hủy (dựa vào `TT_XuLy_Old`, 32/90 HV ở 09 đang trống).

**Edge cases:** HV bị PM cũ đưa vào BC2 giữa lúc đang mở hộp → đọc lại trước khi ghi, bỏ qua kèm lý do · hủy mà `TT_XuLy` đã khác `09` → SP không đổi trạng thái, tool báo "HV không còn ở 09".

> **Ghi nhận khi dựng UI (v4.8, CHANGES #64 — tài liệu đi theo code, không đổi yêu cầu):** cho **tích lẫn** HV chưa tốt nghiệp và đã tốt nghiệp trong cùng lượt Xem lại → Ghi (user chốt; hộp xem lại nêu rõ từng nhóm). Nút "Hủy tốt nghiệp" chỉ bật khi **mọi** HV đã chọn đều "Đã tốt nghiệp" và chưa vào BC2. "Chọn tất cả" chỉ chọn nhóm chưa tốt nghiệp (đang lọc "Đã tốt nghiệp" thì chọn nhóm đó) để bộ sổ điền chung không đè nhầm sổ của HV đã tốt nghiệp. Hộp Hủy báo lỗi đỏ (không báo "Đã hủy 0") khi lô thất bại hoặc đứt giữa chừng, có "Làm tiếp".

> Nguồn: user 11/10/2026 · định nghĩa SP verify DB · TDD §11F.2

#### [TNB-03] Tạo BC2 (ô tô / mô tô)

**Trạng thái:** ⚠️ Partial — 2/2 task xong (98 backend, 111 UI form + tạo BC2 rỗng); mức 1 pass bằng kết nối giả + Playwright giả backend, **chưa ghi thật DB Nạp** (nghiệm thu máy CSDT, Checkpoint 27); UI hiện đủ số BC1, ngày, số học sinh
**Story:** Là nhân viên cơ sở, tôi muốn tạo phiếu BC2 đúng số và đúng BC1 của khóa, để thêm học viên vào báo cáo.

**Done khi:**
- ⬜ Chọn **loại** (ô tô / mô tô — hai danh sách riêng) → chọn **khóa** (BC1 do tool **tự suy từ khóa** — mỗi khóa có tối đa một BC1; hiện số BC1, ngày, số HV; khóa đã bế giảng mà **chưa có BC1** hiện mờ "chưa có BC1 — chưa lập BC2 được" và không chọn được) → nhập **số báo cáo**, **ngày báo cáo**, ghi chú.
- ⬜ **Gợi ý số, nhân viên sửa được, kiểm trùng trước khi ghi:** ô tô = số kế tiếp trong chuỗi `n/năm` (vd `81/2026`); mô tô = **số BC1 bỏ tiền tố `A1A2`** (BC1 `A1A2870/26-TTTĐ` → BC2 `870/26-TTTĐ`). `MaBCII` = `SoBaoCao`.
- ⬜ **`TongSoThiSinh` đúng như PM cũ, không tự đếm lại:** mô tô = `BaoCaoI.SoHocSinh` của BC1; ô tô = số HV tại lúc lập (0 khi tạo rỗng). Danh sách hiện song song "Tổng ghi" và "HV thực tế".
- ⬜ "Xem lại" → "Tạo BC2": `usp_BaoCaoII_Insert`, **`TrangThai=0` (đang mở)**, người tạo = tên đăng nhập tool. **Trong luồng 3 bước của TNB-04 việc tạo BC2 và thêm HV gộp một lần xác nhận** ("Lập BC2 và thêm N học viên"); vẫn cho tạo BC2 rỗng từ danh sách BC2.
- ⬜ Mỗi BC2 mô tô gắn BC1 của chính khóa đó (1 khóa = 1 BC1 = 1 BC2); ô tô có thể nhiều BC2 cho một BC1.
- ❌ Không tạo BC2 không có BC1; không tạo BC1; không nút "Đóng BC2".

**Edge cases:** số BC2 trùng → chặn · BC1 đã có BC2 mô tô → cảnh báo "khóa này đã có BC2 số …" · mất kết nối giữa chừng → kiểm lại BC2 đã tạo chưa trước khi thử lại (tránh tạo đôi).

> **Ghi nhận khi dựng UI (v4.8, CHANGES #64 — tài liệu đi theo code, không đổi yêu cầu):** form hiện **số BC1 · ngày BC1 · số học sinh** của khóa (backend đọc thêm `BaoCaoI.NgayBaoCao`); **ngày báo cáo là bắt buộc**; mất kết nối hoặc lỗi máy chủ khi tạo → "Gửi lại" mang `thu_lai` để không tạo đôi BC2; số gợi ý của mô tô trùng chính BC2 đã có của khóa nên nhân viên phải đổi số mới tạo được (kèm cảnh báo "khóa này đã có BC2 số …").

> Nguồn: user 11/10/2026 · 7 BC2 mô tô gần nhất (tổng = `SoHocSinh` BC1) · TDD §11F.3

#### [TNB-04] Thêm học viên vào BC2

**Trạng thái:** ⚠️ Partial — code + kiểm mức 1/3 xong (96 luật, 97 đọc ứng viên, 99 lập + thêm + hoàn tác, 109 UI bước ①, 110 UI bước ② mới xong lõi, 112 UI bước ③ lập + thêm + làm tiếp + hoàn tác; kiểm bằng kết nối giả + Playwright giả backend, chưa ghi thật). Lối vào "+ Thêm học viên" từ dòng BC2 đang mở và lọc đang mở/đã đóng đã có (task 113). "Dán danh sách CMT/mã đăng ký" đã có (task 116); xử lý ngoại lệ tại chỗ (mini-form số giấy / Cứu trạng thái / Xem BC2) đã có (task 117). **Còn:** nghiệm thu ghi thật ghi thật ở máy CSDT (Checkpoint 27)
**Story:** Là nhân viên cơ sở, tôi muốn đưa đúng các học viên đủ điều kiện (kể cả HV rớt/vắng từ khóa cũ) vào một BC2 đang mở.

**Done khi:**
- ⬜ Chọn **BC2 đang mở** (`TrangThai=0`) của đúng loại; BC2 đã đóng chỉ xem (công tắc "Hiện BC2 đã đóng").
- ⬜ **Luồng 3 bước, một nút làm xong:** ① **Chọn khóa** (khóa đã bế giảng chưa có BC2; mỗi dòng ghi "Sẵn sàng · Thi lại · Cần xem") → ② **Chọn học viên** (một màn, không tab) → ③ **Xác nhận** ("Lập BC2 và thêm N học viên": tạo BC2 nếu chưa có rồi thêm HV; BC2 đã có thì chỉ thêm). Vào từ "Lập BC2 mới" (đủ 3 bước) hoặc từ dòng BC2 đang mở → "Thêm học viên" (vào thẳng bước ②).
- ⬜ **Bốn nhóm học viên (thay cho tab + mã):** ✅ **Sẵn sàng** (HV của khóa đủ điều kiện, chưa ở báo cáo nào — **tích sẵn**) · 🔁 **Thi lại** (rớt/vắng sát hạch hoặc chưa đạt BC2, từ khóa trước hoặc chính khóa này — **KHÔNG tích sẵn**; có nút **"Thêm HV thi lại trong [12] tháng"** đổi được số tháng; gom theo khóa gốc, "chọn cả khóa") · ⚠️ **Cần xem** (chưa tốt nghiệp (ô tô) · thiếu số giấy; mỗi dòng có hướng xử lý 1 chạm) · ⛔ **Không đưa được** (khóa chưa bế giảng · đã có kết quả cuối · sai loại · **đang ở BC2 đang mở khác — phải gỡ khỏi BC2 đó trước (TNB-05)**; ẩn mặc định, mở ra để biết lý do).
- ⬜ **Dải tóm tắt luôn hiện:** "Sẽ đưa vào BC2: 150 + 74 = 224 học viên" cập nhật khi tích, kèm số cảnh báo.
- ⬜ **Chọn nhanh:** tìm tên/CMT (Enter để tích) · **"Dán danh sách"** (dán cột CMT/mã đăng ký từ Excel để tích đúng người, báo số không khớp) · chọn cả khóa gốc · bỏ chọn tất cả.
- ⬜ **Xử lý ngoại lệ ngay trên dòng, không rời màn:** HV chưa tốt nghiệp (ô tô) → "Cập nhật tốt nghiệp" (mini-form số giấy, xong tự sang Sẵn sàng); trạng thái lạ → "Cứu trạng thái" (TNB-06) rồi quay lại.
- ⬜ **Điều kiện:** ô tô — `09` (đã tốt nghiệp, **có số giấy**) cộng `14/17/18`; mô tô — `03` cộng `14/17/18`; khóa đã bế giảng; đúng loại hạng. Danh sách lấy bằng `usp_NguoiLX_HoSo_ThemHS_BC2` rồi **lọc lại phía tool** theo đúng điều kiện (SP nhánh mô tô có lỗi `OR 'B1m'`).
- ⬜ **Ô tô và mô tô không trộn** trong cùng BC2 (tool tự chặn vì DB không có cột hạng ở `BaoCaoII`).
- ⬜ "Thêm N HV": `usp_NguoiLX_Update_ThemHSBC2` từng HV (applock theo BC2) → `MaBC2` mới, `TT_XuLy='11'`, lưu `TT_XuLy_Old`. HV đang ở một BC2 **đang mở** khác thì **không thêm được** (nằm nhóm "Không đưa được", ghi rõ "đang ở BC2 số …, gỡ khỏi BC2 đó trước"); HV thi lại mang số BC2 cũ **đã đóng** thì thêm được và sang BC2 mới.
- ⬜ **Đọc lại từng HV trước khi ghi:** HV PM cũ đã thêm/đổi từ lúc tải danh sách → **bỏ qua kèm lý do**, không ghi đè. Có nút **Làm tươi**; tự tải lại khi quay lại cửa sổ.
- ⬜ Kết quả hiện **đã/chưa ghi** kèm lý do bỏ qua; **"Làm tiếp"** khi đứt giữa chừng; **"Hoàn tác lần vừa rồi"** gỡ đúng các HV vừa thêm (còn ở "Đã vào BC2, chờ kết quả").
- ❌ Không đếm lại `TongSoThiSinh`, không đóng BC2, không nhập kết quả sát hạch.

**Edge cases:** HV khóa chưa bế giảng → không hiện, kèm giải thích (xem TNB-06) · BC2 do PM cũ tạo → thấy ngay như BC2 tạo ở tool · BC2 đã đóng giữa lúc đang thêm → báo, không ghi · HV đang ở BC2 đang mở khác → không đưa được, kèm "gỡ khỏi BC2 số … trước" (không tự chuyển giữa hai BC2) · mô tô: HV tồn là luồng chính (BC2 `861/26-TTTĐ` có 74 HV tồn của 11 khóa).

> **Ghi nhận khi dựng UI (v4.8, CHANGES #64 — tài liệu đi theo code, không đổi yêu cầu):** bước ③ **chốt số/ngày/ghi chú ở lần gửi đầu** — "Làm tiếp" luôn gửi đúng nội dung đã xác nhận dù số gợi ý nhảy (lỗi do kiểm thử Checkpoint 26 phát hiện); bước ② **tự làm tươi khi quay lại cửa sổ** (bỏ qua nếu vừa tải < 15 giây); thanh tiến độ từ 200 HV; lối vào "+ Thêm học viên" ở dòng BC2 đang mở trong danh sách BC2; Enter ở ô tìm rỗng không tích gì. **Hạn chế đã biết:** F5 giữa lúc ghi mất mã lô nên không "Làm tiếp" được (lô vẫn chạy nền; xem kết quả ở danh sách BC2 / Nhật ký). **Chưa quyết (ghi nhận, không phải yêu cầu):** nhóm riêng "đã ở BC2 này" cho HV vừa thêm vào chính BC2 đang xem (hiện xếp "Không đưa được"); (đã chốt khi làm task 117: HV vừa xử lý xong tại chỗ — Cập nhật tốt nghiệp / Cứu trạng thái — **được tích sẵn** nếu sau làm tươi đã vào Sẵn sàng hoặc Thi lại, vì đó là hành động tường minh của người dùng; HV khác không đổi).

> Nguồn: user 11/10/2026 · `usp_NguoiLX_HoSo_ThemHS_BC2` + `usp_NguoiLX_Update_ThemHSBC2` · TDD §11F.4

#### [TNB-05] Bỏ học viên khỏi BC2

**Trạng thái:** ⚠️ Partial — 2/2 task xong (100 backend, 113 UI xem/gỡ/xóa/hoàn tác); mức 1 pass bằng kết nối giả + Playwright giả backend, **chưa ghi thật DB Nạp** (nghiệm thu máy CSDT, Checkpoint 27)
**Story:** Là nhân viên cơ sở, tôi muốn gỡ học viên thêm nhầm khỏi BC2 đang mở.

**Done khi:**
- ⬜ Chọn HV trong BC2 → "Gỡ khỏi BC2" (hộp xác nhận): `usp_NguoiLXHoSo_Update_DanhSachHocSinhBC2` với `@TrangThaiXuLy=101` → `TT_XuLy` về `TT_XuLy_Old`, `MaBC2=''`.
- ⬜ **Chỉ gỡ HV còn `TT_XuLy='11'`** (chưa có kết quả). HV `13/14/16–19` khóa nút kèm lý do (SP sẽ trả về trạng thái cũ làm mất kết quả).
- ⬜ **Xóa BC2** chỉ khi còn 0 HV và BC2 **còn mở** (`usp_BaoCaoII_Delete`), có xác nhận; BC2 đã đóng chỉ xem.
- ⬜ HV thi lại từng ở BC2 cũ đã đóng rồi được thêm vào BC2 này: gỡ ra về trạng thái trước đó (`14/17/18`), **không** tự quay về BC2 cũ (hộp xác nhận nêu rõ).
- ⬜ **Màn xem/gỡ riêng** (ít dùng hơn thêm): danh sách HV trong BC2 có tìm kiếm, chọn nhiều, "Gỡ N học viên"; HV đã có kết quả bị khóa kèm lý do.
- ⬜ **Hoàn tác lần thêm vừa rồi** (gỡ theo lô thêm gần nhất, chỉ HV còn "Đã vào BC2, chờ kết quả").
- ❌ Không nút "Đóng BC2".

**Edge cases:** HV bị PM cũ đổi trạng thái giữa lúc chọn → đọc lại, bỏ qua kèm lý do · `TT_XuLy_Old` rỗng → cảnh báo trước khi gỡ (sẽ về giá trị rỗng) · `TT_XuLy_Old` cũng là "Đã vào BC2" → **không gỡ được** (xử lý ở phần mềm cũ).

> **Ghi nhận khi dựng UI (v4.8, CHANGES #64 — tài liệu đi theo code, không đổi yêu cầu):** hộp Gỡ và Hoàn tác báo **lỗi đỏ** khi lô thất bại hoặc đứt giữa chừng (không báo "Đã gỡ 0"), Hoàn tác có "Làm tiếp"; cảnh báo `TT_XuLy_Old` rỗng xuất hiện sau lúc mở màn (409) vẫn có ô tích để xác nhận; nút Hoàn tác luôn bật khi BC2 đang mở (chỉ nhật ký phía máy chủ biết còn lô nào) — nếu không có lô thì hộp báo lý do.

> Nguồn: user 11/10/2026 · SP gỡ verify DB · TDD §11F.4

#### [TNB-06] Chuyển trạng thái học viên (cứu HV không tìm thấy)

**Trạng thái:** ⚠️ Partial — 2/2 task xong (104 backend, 114 UI tab "Học viên không tìm thấy"); mức 1 pass bằng kết nối giả + Playwright giả backend, **chưa ghi thật DB Nạp** (nghiệm thu máy CSDT, Checkpoint 27); gửi lại sau mất kết nối khi lần trước đã chuyển xong được hoàn tất từ nhật ký (vẫn Hoàn tác được)
**Story:** Là nhân viên cơ sở, khi một học viên đã tốt nghiệp hoặc vắng/rớt sát hạch không hiện trong danh sách để thêm vào BC2, tôi muốn đưa trạng thái của họ về đúng nhóm chờ lập BC2.

**Done khi:**
- ⬜ **Tìm HV** theo tên/CMT/mã đăng ký; tool hiện **lý do HV không có trong danh sách ứng viên** (trạng thái ngoài tập cho phép / khóa chưa bế giảng / khác hạng / đang ở BC2 …).
- ⬜ **Đích cho phép:** `09` (ô tô, bắt buộc đã có số giấy CNTN) hoặc `14/17/18`. **Nguồn cho phép:** HV chưa có kết quả cuối `01, 02, 03, 04, 10, 12, 13`. **CHẶN** nguồn `11` (phải gỡ BC2 trước), `16` (đạt SH), `19` (đã nhận GPLX).
- ⬜ Bắt buộc **nhập lý do**; hộp xem lại "trạng thái cũ → mới" + SP sẽ gọi; ghi **nhật ký**.
- ⬜ Ghi bằng `usp_NguoiLX_HoSo_UpdateTTXLy`; sau khi ghi có nút **hoàn tác về trạng thái cũ** (một lần, ngay sau đó, dựa vào nhật ký của tool; chỉ khi học viên chưa bị phần mềm cũ đổi tiếp). Giao diện hiện **tên trạng thái nghiệp vụ kèm mã** (xem chú giải đầu chương).
- ❌ Không cho gõ mã trạng thái tự do; không sửa kết quả sát hạch; không giải quyết được ca "khóa chưa bế giảng" (điều kiện nằm ở ngày bế giảng của khóa).

**Edge cases:** SP đặt `Transfer_flag=0` (hiện toàn bộ HV đã bằng 0) · HV khác hạng với loại đang chọn → không đổi, báo lý do · HV `09` mà không có số giấy → chặn đích 09.

> **Ghi nhận khi dựng UI (v4.8, CHANGES #64 — tài liệu đi theo code, không đổi yêu cầu):** hộp xem lại "cũ → mới" có mục thu gọn **"dành cho IT"** nêu `usp_NguoiLX_HoSo_UpdateTTXLy`; HV của khóa chưa bế giảng vẫn chuyển được nhưng có ghi chú "không làm học viên hiện vào danh sách BC2"; **gửi lại sau khi tool bị ngắt giữa lúc cứu** (SP đã chạy, lô chưa đóng) được hoàn tất từ nhật ký thay vì bị từ chối — vẫn Hoàn tác được.

> Nguồn: user 11/10/2026 · `usp_NguoiLX_HoSo_UpdateTTXLy` · TDD §11F.5

#### [TNB-07] Danh sách BC2 và nhật ký thao tác

**Trạng thái:** ✅ Done — 2/2 task xong (105 backend danh sách BC1/BC2 + nhật ký, 115 UI); chỉ đọc nên không cần ghi thật; kiểm bằng Playwright giả backend + đọc DB Nạp thật ở task 105 (455 BC2)
**Story:** Là nhân viên cơ sở, tôi muốn xem các BC2 hiện có và biết ai đã làm gì trong tool.

**Done khi:**
- ⬜ Bảng BC2 theo **loại hạng (Ô tô / Mô tô — nút chọn chung ở đầu màn Báo cáo 2)**, lọc **đang mở / đã đóng**: số báo cáo · ngày · BC1 · khóa · **Tổng ghi** · **HV thực tế** (đánh dấu lệch) · người tạo. Bấm một dòng → chi tiết (TNB-04/05).
- ⬜ **Nhật ký thao tác phía tool:** ai · lúc nào · loại (tốt nghiệp / tạo BC2 / thêm / gỡ / cứu trạng thái) · số HV · kết quả đã/chưa ghi.
- ❌ Chỉ đọc; không sửa/xóa BC2 ở màn này.

> **Ghi nhận khi dựng UI (v4.8, CHANGES #64 — tài liệu đi theo code, không đổi yêu cầu):** tab Nhật ký lưu và hiển thị **số lượng + mã thao tác, không có họ tên/CMT học viên** (ghi chú ở cuối màn); danh sách BC2 đánh dấu "lệch" chỉ là thông tin (PM cũ không đếm lại; HV thi lại chuyển sang BC2 khác).

> Nguồn: user 11/10/2026 · `usp_BaoCaoII_Search`, `usp_BaoCaoI_SelectAll` · TDD §11F.6

---

### 🟠 NICE TO HAVE (sau này thêm)

- [ ] [QLY-04] Kết xuất/báo cáo danh sách học viên (Excel) — có log, giới hạn, chỉ quản trị.
- [ ] [THU-03] Chế độ offline app web (nhập không mạng, đồng bộ sau) — nếu nhân viên thu nhận cần. Lưu ý: khi làm offline, kiểm trùng CCCD + map DVHC dời hẳn về bước nạp ở tool (app web offline không có DB).

---

## ④ Tech Stack

| Layer | Tech | Lý do chọn |
|---|---|---|
| Frontend (app web + tool) | React + Vite (PWA) + TailwindCSS + shadcn/ui | Đẹp, hiện đại, mobile-friendly; build sẵn ở máy dev → tool không cần Node ở máy CSDT |
| Backend (VPS) | Python FastAPI | Nhẹ, hợp API + phục vụ static PWA |
| Backend (tool máy DB) | Python FastAPI (localhost) + pymssql + Pillow (.jp2) + rembg (xóa phông) | Python xuất `.jp2` + xóa phông sạch nhất; nối SQL Server |
| Database (VPS) | PostgreSQL | Đa người dùng đồng thời, ổn cho hàng đợi + PII tạm |
| Database (tool staging) | SQLite | 1 máy, 1 người, không cần cài server |
| Hệ đích | SQL Server `GPLX_CSDT` (SP có sẵn) | DB production; nạp qua stored procedure |
| Auth | Token/JWT (tài khoản riêng hệ thống này) + API key cho tool | Truy vết ai gửi/ai nạp (PII) |
| Hosting | App web + Backend trên VPS (domain, HTTPS); Tool đóng gói PyInstaller chạy tại máy DB | Máy DB sau NAT vẫn chạy (tool pull ra VPS) |

---

## ⑤ Integration Points

### SQL Server `GPLX_CSDT` (chỉ tool kết nối)
1. Tool nối SQL Server qua LAN bằng SQL login riêng (không dùng `sa`).
2. Nạp/sửa/xóa chỉ qua stored procedure: `usp_NguoiLX_*`, `usp_NguoiLX_HoSo_*`, `usp_NguoiLXHS_GiayTo_*`, `usp_KhoaHoc_Insert`; danh mục qua `usp_DM_DVHC_*`, bảng `DM_*`, `QTHT_ThamSoHT`, `BaoCaoI`.
3. Đọc cấu hình động từ `QTHT_ThamSoHT` (IMG_PATH_CSDT, MA_CSDT).
❌ Không xử lý: sát hạch, Báo cáo 1/2, cấp/in GPLX; không INSERT bảng trực tiếp.

### App web ↔ VPS ↔ Tool (qua domain, gián tiếp)
1. App web gọi API VPS qua HTTPS domain + token người dùng.
2. Tool gọi API VPS qua HTTPS + API key (pull); đánh dấu `da_nap`.
3. App web và tool không nối trực tiếp — VPS là điểm hẹn.
❌ Không xử lý: mở cổng/ IP tĩnh ở máy DB.

### Bảng ánh xạ DVHC (`DM_DVHC_MAP`)
1. Nạp từ nguồn dữ liệu ánh xạ cũ→mới (`vietnamadminunits`), đối soát về mã DB.
2. Cập nhật lại khi `DM_DVHC` của DB thay đổi.
❌ Không xử lý: tự cập nhật online.

---

## ⑥ Non-Functional Requirements

- **Performance:** app web thao tác < 2s; API VPS < 500 ms (p95); xóa phông + xuất `.jp2` < 5s/ảnh; nạp 1 HV < 2s.
- **Security:** HTTPS toàn bộ; token/JWT + API key; SQL login riêng (không `sa`); PII căn cước giữ tối đa 30 ngày rồi tự xóa; không log nội dung CCCD; chặn IDOR; nạp DB chỉ ở tool (app web không có endpoint nạp).
- **Responsive:** App web **mobile-first, giao diện như app mobile thật** khi dùng trên điện thoại: điều hướng dạng bottom nav/tab, thao tác chạm (nút to, vuốt), **ẩn hoặc thu gọn** các thành phần không cần trên mobile — KHÔNG phải giao diện desktop bị co nhỏ. Bản desktop của app web mới hiển thị đầy đủ dạng bảng/nhiều cột. **Tool máy tính CHỈ desktop** (localhost, không mobile/responsive): thiết kế cho cửa sổ rộng, nội dung giữ bề rộng tối thiểu dễ đọc (ngắm ≥1280px, canh giữa ~1500px); sidebar module thu gọn được để nhường bề ngang; bảng nhiều cột cho cuộn ngang trong vùng bảng — **không để khung quá hẹp làm vỡ/chật giao diện**. Dựng UI tool phải **dùng skill UI** (ui-ux-pro-max/impeccable) bám design system đang có.
- **Chuẩn hiển thị cảnh báo (CHANGES #6):** mọi cảnh báo/lỗi khi nạp (trùng CCCD, sai chính tả tên, thiếu ảnh, lỗi nạp lô) phải **inline (không hộp thoại modal), NỔI BẬT** (banner có nền + viền + icon, không chỉ dòng chữ nhỏ) và **nêu rõ NGUYÊN NHÂN cụ thể** (vd "CCCD 070… đã có ở Số hồ sơ 014 trong khóa này"). Trạng thái nạp lô dùng màu + icon + chữ (⚪ chờ / 🔴 lỗi / 🟢 xong) — **không chỉ dựa màu** (phủ người mù màu).
- **Kiến trúc module + sidebar (tách nghiệp vụ trong tool):** tool máy CSDT chia thành **nhiều module độc lập**, điều hướng **2 cấp**: **sidebar bên trái** liệt kê các module — bấm module nào thì vùng nội dung bên phải hiện **các màn/cửa sổ phiên làm việc** của module đó (mỗi module có **sub-nav riêng** + **màu nhấn** + **banner nhắc DB** đang ghi vào). Hiện có **Thu nhận hồ sơ** (sub-nav: Nạp hồ sơ · Tạo khóa · Cấu hình — ghi `GPLX_CSDT`) và **Đồng bộ CDB** (sub-nav: Bàn đồng bộ · Quản lý DB đích · Lịch sử & Hủy — ghi `GPLX_CDB_CSDT`); **dự kiến thêm "Cập nhật kết quả học tập"** (module #3, chưa đặc tả). Sidebar + router + module backend phải **mở rộng được cho N module** (đăng ký thêm một dòng, không hardcode); các module **không import chéo** nhau để tránh xung đột và nhầm lẫn UX. (Việc đổi điều hướng Nạp từ thanh nav trên cùng → sub-nav trong module chỉ là đổi vị trí điều hướng, **hành vi màn Nạp không đổi**.)
- **Concurrency:** ~10 nhân viên thu nhận đồng thời; 1–2 tool; đầu khóa ~60 bản ghi/đợt; sinh Số hồ sơ có khóa tuần tự.
- **Uptime:** VPS ~99% (nội bộ, không SLA gắt); tool phụ thuộc máy DB.

---

## ⑦ Edge Cases & Error States

| Tình huống | Hành vi mong muốn |
|---|---|
| User nhập sai form | Cảnh báo trường sai, không cho gửi/nạp trường bắt buộc thiếu |
| Mất mạng giữa chừng | App web giữ nháp, gửi lại theo UUID (không trùng); tool xử lý staging đã kéo |
| File ảnh quá lớn/không hợp lệ | Nén/chuẩn hóa; báo lỗi nếu không phải ảnh |
| Session hết hạn | Yêu cầu đăng nhập lại; không mất dữ liệu đang nhập (nháp local) |
| Tải lại trang (F5) khi đang đăng nhập | **Giữ phiên, không văng ra đăng nhập** (token lưu localStorage, khôi phục qua `/local/auth/me`); token đã hết hiệu lực → tự xóa, về đăng nhập (CHANGES #36) |
| SQL Server lỗi giữa lúc nạp | Rollback transaction, giữ `pending`, cho thử lại |
| VPS/tunnel lỗi | Tool báo lỗi, làm việc trên staging; thử lại |
| Nạp lại bản ghi đã nạp | Chặn (không tạo HV thứ 2) |
| Hai người/hai tool cùng nạp một bản ghi | Khóa bản ghi khi `importing`; chỉ tạo 1 HV |
| Bấm nút thao tác hai lần (nạp/gửi) | Disable + idempotent theo UUID; không tạo bản ghi trùng |
| Bản ghi PII quá 30 ngày đang nạp | Job xóa bỏ qua bản `importing` |
| Sync: HV đã có trong DB đích | Tự bỏ qua (1 người=1 hồ sơ=1 MaDK), không tạo trùng |
| Sync: hai phiên cùng khóa cùng ngày sinh trùng MaDK | Kiểm tồn tại trước INSERT + sinh lại (tối đa 3 lần) rồi báo lỗi riêng HV đó |
| Sync: lỗi 1 HV giữa lô | Ghi lý do, sync tiếp HV khác; vào tổng kết cuối |
| Sync: HV nguồn thiếu CCCD (SoCMT rỗng) | Chặn + báo riêng trước sync (NguoiLX.SoCMT NOT NULL) |
| Sync: trùng CCCD trong danh sách nguồn | Cảnh báo, để người dùng quyết (PK=MaDK, vẫn tạo được) |
| Sync: mất kết nối CSDL đích giữa lô | Dừng; HV đã tạo giữ nguyên + đã ghi log → sync lại tự skip |

---

## ⑧ Success Metrics

- **Tuần 1:** nạp thử ≥ 1 khóa thật đầu-cuối; bản ghi mở app cũ hiển thị đúng 100%.
- **Tháng 1:** thời gian nạp 1 HV giảm còn ≤ 2–3 thao tác xác nhận (chọn khóa + địa chỉ + ảnh); lỗi địa chỉ/DVHC ~0 với địa chỉ map được.
- **Tháng 3:** **≥ 80% học viên mới của các khóa chưa lập BC1 được nhập qua hệ thống này** (đếm trên DB theo `NgayTao`); nhân viên thu nhận không cần ngồi tại máy DB.

*(Baseline hiện tại — chủ dự án cung cấp 01/10/2026: trung bình **~100 HV/khóa**; gõ tay nhập 1 HV vào app cũ **~3 phút/HV** (≈300 phút/khóa). Dùng để ước lượng % thời gian tiết kiệm khi nhập qua hệ thống mới.)*

---

## ⑨ Constraints & Assumptions

**Giới hạn:** *(chủ dự án chốt 01/10/2026)*
- Budget: **VPS + domain có sẵn, không phát sinh chi phí** → chỉ dùng thư viện/mã nguồn mở miễn phí, không thuê dịch vụ trả phí.
- Timeline: **không có deadline cứng** → giao tăng dần theo lát cắt dọc, xong phần nào dùng phần đó.
- Team size: **1 người** → build tuần tự một luồng, không tách nhánh song song.
- Tech constraints: DB `GPLX_CSDT` SQL Server (DESKTOP-UBV2GQI); ảnh `.jp2` ghi ra `D:\GPLXCSDT\ANHCDUNG\<MaKhoaHoc>\`; máy DB có internet; VPS + domain có sẵn; stack Python + React.

**Assumptions (giả định Nền móng — chưa kiểm chứng, chặn code phần liên quan):**
- AS-001: Chuỗi QR CCCD **6 hoặc 7 trường** phân tách `|` (đã xác nhận định dạng từ dự án webThanhdat 30/09/2026) — chỉ cần test thẻ thật của cơ sở khi có app.
- AS-003: Nạp qua SP ra bản ghi hiển thị y app cũ — cần nạp thử 1 HV thật.
- (AS-002 map DVHC phủ 100%, AS-004 mô tô MaLoaiHs=1 — đã xác nhận 30/09/2026.)
- GĐ: nhân viên thu nhận có điện thoại chụp ảnh + quét QR; máy không hỗ trợ → dùng bản desktop web nhập tay + upload ảnh (kiểm: hỏi thiết bị thực tế).
- GĐ: đồng hồ máy DB và VPS đúng giờ Asia/Saigon — MaDK + tên file `.jp2` sinh theo timestamp máy DB (kiểm: so giờ trước go-live).
- GĐ: `rembg` xóa phông đạt yêu cầu cho ảnh chân dung thường; ca lỗi (tóc/viền) cho giữ ảnh gốc/chỉnh tay (kiểm: thử ~10 ảnh thật).
- GĐ: máy DB đủ tài nguyên chạy rembg + Pillow/OpenCV trong <5s/ảnh (kiểm: đo trên máy CSDT).

📄 Chi tiết: `docs/ba/thu-nhan-ho-so-hoc-vien/10-assumptions.md`

---

## Changelog

| Ngày | Thay đổi | Người cập nhật |
|---|---|---|
| 30/09/2026 | v1 — draft đầu tiên (từ tài liệu BA, chế độ B) | BA/PM |
| 30/09/2026 | v2 — sửa sau review: số lượng user; khung ảnh 3:4 grab + nền trắng + xuất 353×471; Done NAP-05 khớp trường cụ thể; giấy tờ theo tick cuối; edge đồng thời (2 tool/double-click) + tên dài; metric ≥80%; +4 giả định; QR 6/7 trường | PM |
| 01/10/2026 | v2.1 — chốt 4 ô [CHƯA CHỐT]: ⑧ baseline ~100 HV/khóa & ~3 phút/HV; ⑨ budget (VPS/domain có sẵn, không phát sinh) · timeline (không deadline, giao tăng dần) · team size (1 người, tuần tự) | PM |
| 01/10/2026 | v2.2 — sau review TDD §10 (CHANGES #5): NAP-05 đổi tiêu đề "3 SP"→"1 SP gộp app cũ" + nới ❌ cho UPDATE 5 cột ảnh (hướng A); thêm story **QLY-05** Nạp/thay ảnh cho HV đã có (làm sau NAP-05) | PM |
| 01/10/2026 | v2.3 — UX màn nạp (CHANGES #6): NAP-01 thêm IA 2 chế độ (Nạp/Tra cứu), tên IN HOA khi kéo, check chính tả mức A, nạp lô badge đỏ/xanh; QLY-01 tìm khóa mọi khóa (kể cả BC1); NFR ⑥ chuẩn cảnh báo inline nổi bật; NAP-06 hạ ⏳ (làm banner nổi bật) | PM |
| 01/10/2026 | v2.4 — NAP-01 thêm AC "kéo lại làm tươi hồ sơ chưa nạp" + edge case (CHANGES #11); hạ NAP-01 ✅→⏳ Todo (yêu cầu thêm, code ①/② cũ vẫn đúng) | PM |
| 01/10/2026 | v2.5 — sửa UX app web sau test điện thoại (CHANGES #12): THU-01 (màn vào không tự mở camera, header logo không phải nút, layout mobile dính đáy, khung bám QR) + THU-02 (ảnh thật ở list/chi tiết, xem/sửa/chụp lại hồ sơ chờ nạp); hạ THU-01 & THU-02 ✅→⏳ Todo | PM |
| 01/10/2026 | v2.6 — app web nhập liên tiếp (CHANGES #13): THU-01/THU-02 +AC "Lưu & nhập hồ sơ tiếp" (gửi không ảnh + toast) + badge/bộ lọc "Thiếu ảnh" → hạ THU-01 & THU-02 ✅→⏳; +story **THU-04** (SHOULD) cảnh báo trùng CCCD app web (cảnh báo mềm, soi hàng đợi); +story **QLY-06** (📝 Draft) mở hồ sơ khóa khác cho HV đã có — còn nợ kiểm DB | PM |
| 01/10/2026 | v2.7 — redesign UX nhập liệu (CHANGES #14): THU-01/THU-02 +AC ẩn ô CMND cũ (vẫn lưu từ QR) + ô ngày gõ tay/nút lịch (giữ năm-only) + desktop tách nút/bố cục/phím tắt. Giữ THU-01/02 ⏳ | PM |
| 04/10/2026 | v2.8 — +Feature **Đồng bộ CDB** (CHANGES #33, SHOULD): 3 story `SYNC-01`/`SYNC-02`/`SYNC-03` port từ sync_tool GPLX v2.0, workspace riêng tách khỏi Nạp; +NFR kiến trúc workspace (mở rộng N module, dự kiến workspace #3 "Cập nhật kết quả học tập"); +3 edge case Sync | PM |
| 04/10/2026 | v2.9 — cấu hình kết nối lên header (CHANGES #34): +story **HTG-07** (bảng cấu hình chung mở từ icon ⚙ header, gộp HTG-01 ③ + SYNC-02, tách rõ DB nguồn Nạp / nhiều DB đích Sync); sửa bullet Cấu hình HTG-01 trỏ sang HTG-07 (giữ ✅); hạ **SYNC-02 ✅→⏳** (quản lý đích dời vào bảng header) + **SYNC-01 ✅→⏳** (làm đẹp combobox + danh sách HV bằng impeccable/ui-ux-pro-max) | PM |
| 04/10/2026 | v3.0 — +Feature **Tra cứu CDB đích** (CHANGES #35, mở rộng phân hệ Đồng bộ CDB): 4 story **TCB-01** (tra khóa+lưới HV+chi tiết+ảnh, +nút Xem chi tiết từ Bàn đồng bộ) · **TCB-02** (thay ảnh — tái dùng AnhModal+đổi nền, ghi đè file dùng chung 2 DB) · **TCB-03** (sửa nhân thân — chặn nếu đã kết xuất DKKH) · **TCB-04** (xóa HV/đổi khóa — chặn nếu đã BC1). Trạng thái khóa đọc Ở ĐÍCH (DKKH=SoQD_KhaiGiang, BC1=TT_XuLy≥05/BaoCaoI). SYNC-01 thêm nút điều hướng (giữ ✅) | PM |
| 05/10/2026 | v3.1 — **sửa định nghĩa DKKH** (CHANGES #36): "đã kết xuất DKKH" = có gói `DANG_KY_KHOA_HOC` gửi Sở (`TRANS_CLI_HangDoiGui`), **KHÔNG** phải `SoQD_KhaiGiang` (sai — mọi khóa đều có) → áp TCB-01/02/03/04 (chip + chặn sửa nhân thân TCB-03). +SYNC-01: filter khóa đích "cùng hạng & chưa DKKH" (mặc định bật) + khóa xếp mới-nhất-trước (hiện ngày KG combo nguồn + sort phụ MaKH DESC) + giữ phiên đăng nhập qua F5. Giữ ✅ (code đã viết+verify live 05/10) | PM |
| 05/10/2026 | v3.2 — **mở rộng trường sửa nhân thân TCB-03** (CHANGES #37): thêm địa chỉ thường trú 2 cấp (Tỉnh+Xã) + ngày cấp CCCD + nơi cấp CCCD; danh mục Xã/Sở đọc từ DB đích. Chỉ TCB-03 (user chốt); Nạp QLY-01 giữ 5 trường. TCB-03 hạ ✅→⏳ (bản 5 trường đã nghiệm thu ghi-thật tại máy CSDT 05/10). | PM |
| 05/10/2026 | v3.4 — **DGT-04 +refresh-token VPS** (CHANGES #39, gỡ Chặn vps_token 8h từ /reviewtdd #38): thêm "Done khi" giữ quyền máy chủ lâu dài (vé gia hạn + tự đổi ngầm); sửa mô tả mã hóa phiên "key.bin" → "ràng vào máy + tài khoản Windows". Gộp vào DGT-04, không thêm story. | PM |
| 06/10/2026 | v3.5 — **Nơi cấp căn cước = Cục QLHC '00' từ `DM_DVHC`** (CHANGES #40, đảo #31/BUG-10 + #37): nơi cấp đọc/lưu theo `DM_DVHC.MaDvhc` (có '00' Cục QLHC) thay `DM_DonViGTVT`; CCCD 12 số mặc định '00'. **Mở rộng modal sửa QLY-01 Nạp** +combo địa chỉ 2 cấp + nơi cấp + ngày cấp CCCD (ngang TCB-03), guard BC1 giữ nguyên. Tiền đề: đã đồng bộ `DM_DVHC` đích→nguồn. NAP-05 giữ ✅, QLY-01 ⚠️ Partial, TCB-03 🔄. | PM |
| 05/10/2026 | v3.3 — **+Nhóm "Đóng gói & khởi chạy tool độc lập"** (CHANGES #38): 4 story mới `DGT-01` (đóng gói exe PyInstaller + FastAPI phục vụ UI cùng cổng) · `DGT-02` (tự mở trình duyệt + khay hệ thống + chống chạy 2 bản + tùy chọn tự chạy khi bật máy) · `DGT-03` (wizard thiết lập lần đầu, tái dùng test-before-save) · `DGT-04` (phiên đăng nhập **vĩnh viễn** lưu đĩa + thu hồi từ xa, chỉ Đăng xuất mới thoát). HTG-01 +dòng trỏ DGT-04 (chỉ tool; web giữ phiên thường, vẫn ✅). | PM |
| 07/10/2026 | v3.6 — **+Nhóm "Cập nhật kết quả đào tạo"** (CHANGES #42, prefix mới KQD): 4 story `KQD-01` (chọn khóa combobox gõ-tìm + lọc HV 4 trạng thái + lưới + băng DB đích) · `KQD-02` (nhập điểm GỐC → quy đổi /10 theo Sổ TT17 → ghi 5 điểm per-môn; giờ/km TT17/2026; cờ CŨ/MỚI theo khóa; Đạt từng-môn-≥5 app tự tính) · `KQD-03` (tab Theo dõi kết xuất chỉ xem) · `KQD-04` (sửa lại HV Sở từ chối/giải trình). Module tool ghi CDB đích qua `usp_NguoiLX_KetQuaDaoTao_CSDT_CapNhat`; chỉ cập nhật, KHÔNG kết xuất XML. | PM |
| 07/10/2026 | v3.8 — **App web chụp bù ảnh kể cả HV ĐÃ NẠP — Phương án B** (CHANGES #44, lật quyết định A 01/10): `THU-02` +Done khi "chụp bù ảnh HV thiếu ảnh kể cả imported" (chỉ ảnh, không sửa/xóa), hạ ✅→⏳; `QLY-05` nguồn (b) kéo ảnh VPS nay gồm bản collector chụp-bù, operator tự lọc "Chưa ảnh"→kéo (chốt A không cờ). | PM |
| 07/10/2026 | v3.7 — **Ngày cấp + Nơi cấp điền sẵn ở drawer Nạp lô** (CHANGES #43, `NAP-01`): +Done khi ô **Ngày cấp CCCD** điền sẵn + sửa được (lưu nháp bền, nạp vào `NgayCapCMT`) · ô **Nơi cấp** luôn điền sẵn "Cục QLHC" cho CCCD 12 số kể cả khi máy chưa đồng bộ '00' (bền hóa #40). Không thêm mã, NAP-01 giữ 🔄, NAP-05 giữ ✅. | PM |
| 07/10/2026 | v3.9 — **Sửa điểm sau kết xuất + dựng lại tab Theo dõi kết xuất** (CHANGES #45): +story mới `KQD-05` "Mở khóa để sửa điểm" (cổng B-1: chỉ mở khi còn gói chưa gửi `NoiGui=CSĐT`/`TrangThai=0`; hành vi B-1a mức lô: xóa gói + lùi mọi HV 12 của khóa về 09/10; M1: gói đã gửi hết → khóa cứng + thông báo mức đợt, không truy được HV nằm gói nào; nút ở cả 2 tab; nới chặn 409 cho TT=12). `KQD-03` viết lại khóa-first master–detail (thay list phẳng). `KQD-02`/`KQD-04` +ghi chú ngoại lệ TT=12 qua KQD-05 (giữ ⚠️ Partial — yêu cầu lõi không đổi). Số story 41→42. | PM |
| 07/10/2026 | v4.0 — **+story mới `THU-06` "Chụp ảnh thẻ → tự đọc chữ (OCR)"** (CHANGES #49): lối nhập thứ 3 khi QR không quét được, **mọi thiết bị** (iPhone/iOS engine QR web yếu hơn Android — BUG-14); OCR điền sẵn 6 trường → nhân viên xác nhận/sửa trước khi lưu. Lật quyết định "không OCR" của THU-01 (dòng ❌ nay trỏ THU-06; THU-01 giữ ⚠️, hành vi QR không đổi). Engine OCR + nơi chạy để `/tdd`. Số story 43→44. | PM |
| 07/10/2026 | v4.1 — **THU-06 OCR chỉ đọc 5 trường mặt trước — bỏ ngày cấp** (CHANGES #50, phát hiện khi build task 79): ngày cấp in ở MẶT SAU thẻ → OCR mặt trước không đọc được; Steps bước 3 + Done-khi sửa 6→5 trường (CCCD/họ tên/ngày sinh/giới tính/nơi TT), +dòng "ngày cấp nhân viên nhập tay". User chốt A. Số story giữ 44, THU-06 giữ 🔄. | PM |
| 10/10/2026 | v4.2 — **KQD-05 mở rộng: "Sửa sau khi đã gửi Sở" chọn từng HV** (CHANGES #53): thay khóa cứng M1 bằng lối sửa có xác nhận khi cơ sở hết gói chưa gửi — ô tích HV `12` trên lưới KQD-02 + hộp xác nhận (cảnh báo, lý do bắt buộc ≤1.000 ký tự, tích cam kết kết xuất lại) + chip cam "Sửa sau gửi — chưa kết xuất lại" + khối đỏ "chờ kết xuất lại" ở KQD-03; chỉ lùi HV được chọn, không xóa gói đã gửi, `13` từ chối. Lối "Mở khóa" cũ (còn gói chưa gửi) giữ nguyên. **KQD-05 hạ ⚠️ Partial → ⏳ Todo** (yêu cầu đổi). KQD-02/03/04 chỉ thêm ghi chú, giữ trạng thái. Số story giữ 44. Không làm kết xuất XML (file ký số). | PM |
| 10/10/2026 | v4.3 — **+Feature "Phân công giáo viên – xe" (prefix mới `PCG`, 5 story `PCG-01..05`)** (CHANGES #54): phân hệ #4 của tool máy CSDT ghi `KhoaHoc_GiaoVien`/`KhoaHoc_XeTap` ở CDB đích — ① chọn GV của khóa (+hàng loạt) · ② phân công môn + từ→đến (môn Thực hành nổi bật, ngày bắt đầu thực hành tự nhập, giờ bước 30 phút, "Theo ngày"=00:00) · ③ chọn xe + ghép 1 GV–1 xe + "Gợi ý ghép xe" · kiểm 3 mức theo luật datetime nửa mở của CDB, bản nháp + "Ghi vào CDB" có xác nhận · tab "Rà soát khóa". Không làm lịch tuần `LichHoc`, phân xe theo HV, sửa danh mục GV/xe. **Số story 44→49.** | PM |
| 11/10/2026 | v4.4 — **+Feature "Tốt nghiệp & Báo cáo 2" (prefix mới `TNB`, 7 story `TNB-01..07`)** (CHANGES #60): phân hệ #5 của tool, DB Nạp `GPLX_CSDT`, chỉ dùng SP có sẵn; cập nhật/hủy tốt nghiệp ô tô, tạo BC2 + thêm/bỏ HV (ô tô, mô tô riêng), cứu `TT_XuLy`. PM cũ vẫn kết xuất/đóng BC2. +TDD §11F (v6.6) + decisions §23 + SCREENS #26–#32; **số story 49→56**. | BA/PM |
| 11/10/2026 | v4.5 — **TNB: thiết kế lại luồng thêm HV vào BC2** (CHANGES #61, phản hồi mockup v1): 3 bước một nút làm xong, 4 nhóm HV (Sẵn sàng/Thi lại/Cần xem/Không đưa được), HV thi lại không tích sẵn + nút "Thêm HV thi lại 12 tháng", dán danh sách CMT, xử lý ngoại lệ tại chỗ, hoàn tác lần thêm vừa rồi; giao diện dùng tên trạng thái nghiệp vụ + chú giải, không lộ mã/SP. Số story giữ 56. | BA/PM |
| 11/10/2026 | v4.6 — **TNB đồng bộ PRD với TDD §11F v6.8 sau /reviewtdd** (CHANGES #62): TNB-04 bỏ "HV đang ở BC2 khác sẽ bị chuyển" → nhóm "Không đưa được" kèm "gỡ khỏi BC2 đó trước" (SP không trả HV đang `11`; chuyển làm HV kẹt `11` không BC2); Thi lại tính cả cùng khóa; ô tô `09` cần có số giấy; TNB-03 BC1 suy từ khóa, khóa chưa có BC1 hiện mờ; TNB-05 sửa dòng "từng ở BC2 cũ". Số story giữ 56. | BA/PM |
| 11/10/2026 | v4.7 — **TNB ghi lại hành vi thực tế sau backend task 96–105** (CHANGES #63, không đổi yêu cầu, không đổi mã/trạng thái): TNB-01 trùng số giấy chỉ chặn khi đổi sang số của HV khác + bộ sổ/QĐ/ngày chung cho cả lượt; TNB-05 xóa BC2 chỉ khi còn mở, gỡ tay HV `Old='11'` bị chặn; TNB-06 hoàn tác dựa nhật ký tool. Số story giữ 56. | BA/PM |
| 11/10/2026 | v4.8 — **TNB ghi lại hành vi thực tế khi dựng UI task 106-115** (CHANGES #64, không đổi yêu cầu, trạng thái story giữ nguyên vì code đã chạy đúng điều được ghi): TNB-02 tích lẫn + luật nút Hủy/Chọn tất cả · TNB-03 hiện ngày BC1, ngày bắt buộc, Gửi lại `thu_lai` · TNB-04 chốt payload bước ③, tự làm tươi, hạn chế F5 + 2 điểm chưa quyết · TNB-05 lỗi lô · TNB-06 mục IT, khóa chưa bế giảng, hoàn tất lô dở · TNB-07 "chọn loại hạng" thay "tab", nhật ký không PII. Số story giữ 56. | BA/PM |
| 12/10/2026 | v4.9 — **+2 story chỉ đọc theo tư vấn bổ sung từ schema DB đích** (CHANGES #65, #66): `KQD-07` Kiểm trước kết xuất (theo từng khóa; chip Chưa có điểm / Thiếu môn / Thiếu giờ-km thực hành / Thiếu kết luận; dùng luật ô bắt buộc của KQD-02) · `PCG-06` Hạn giấy tờ (tab thứ 3 màn Phân công, toàn cơ sở: xe hết hạn/≤30 ngày, GPLX giáo viên hết hạn/≤30 ngày, GV/xe ngưng còn phân công ở khóa chưa bế giảng). Cả hai ⏳ Todo, không ghi DB, không đổi schema. **Số story 56→58.** | BA/PM |
| 12/10/2026 | v4.10 — **QLY-07 sửa nguyên tắc ghi ảnh** (CHANGES #67): đổi nền cả khóa ghi đè đúng file ở `DuongDanAnh` (2 DB dùng chung 1 file), không tạo file/không đổi đường dẫn; sao lưu thống nhất `<tên>_BACKUP.jp2` cùng thư mục, chỉ-nếu-chưa-có. QLY-07 hạ ⚠️ → ⏳ Todo. Số story giữ 58. | BA/PM |
| 12/10/2026 | v4.11 — **KQD-07 ghi quyết định đã chốt** (CHANGES #68): môn bắt buộc = cả 5 môn mọi hạng ô tô, hạng mô tô không xét (thay câu "mô tô ẩn bớt ô thực hành"); chỉ nhắc không chặn, KQD-02 giữ nguyên; chốt UX qua mock: ẩn chip giờ/km khi chưa có điểm, thông điệp khóa mô tô. Mock `ui-mock/ketqua.html` + `ui-mock/phancong.html` ghi vào nguồn KQD-07/PCG-06. Số story giữ 58. |
| 12/10/2026 | v4.12 — **+`KQD-08` Nạp giờ/km đường từ PDF DAT theo khóa** (CHANGES #69): đọc PDF báo cáo DAT, khớp theo Mã học viên, bảng xác nhận cũ→mới, chặn nạp nhầm khóa, dòng chưa chạy DAT bỏ tick, ghi riêng 2 cột giờ/km (không qua SP). **Sửa `KQD-02`:** ô Giờ đường nhận `hh:mm` tự đổi thập phân; mở lại hiện sẵn giờ/km đã lưu; hạ ⚠️ Partial → ⏳ Todo. Số story 58 → 59. | BA/PM |
