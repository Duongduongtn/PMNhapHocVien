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

**Trạng thái:** ⚠️ Partial — redesign desktop (CHANGES #30, 03/10/2026) code XONG: `Quet.tsx` thêm hook `useIsDesktop`, desktop vào thẳng form nhập tay (bỏ cổng ChonCach), nút Quét QR/Tải ảnh phụ góc phải, popover camera (`QuetPopover`) đè form tự điền, "Lưu & nhập tiếp" về form trống; mobile guard `!isDesktop` giữ nguyên. Kiểm mức 1: webapp build + typecheck sạch · 24 vitest pass · review-nghiepvu **8/8 đủ**. **CHƯA chụp Playwright 3vp (375/800/1440)** — màn sau đăng nhập + cần backend stack, chưa dựng được phiên này. Mobile vẫn ✅ như trước (task 30, deploy live `029026c`). Trước đó ✅ Done 01/10/2026: Nhập liên tiếp ("Lưu & nhập hồ sơ tiếp") + redesign UX nhập liệu (task 30, CHANGES #13/#14: ẩn ô CMND cũ, ô ngày auto-mask "/" + nút lịch giữ năm-only, desktop 2 cột + 2 nút tách hai đầu + phím tắt + nới khung). Kiểm: webapp 24 test · build · 4 review (nghiệp vụ/kỹ thuật/bảo mật/giao diện) đã vá · Playwright 1440/375 · deploy live `029026c`. Nền quét QR (task 18/28) — khung bám QR cần thẻ thật AS-001.
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
- ❌ Không OCR chữ trên thẻ; ảnh thẻ chỉ dùng cắt ảnh chân dung.

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

**Trạng thái:** ✅ Done — 01/10/2026. Gửi nhanh không ảnh (toast) + badge "Thiếu ảnh" + bộ lọc thiếu ảnh ở "Hồ sơ đã gửi" (task 30, CHANGES #13) + form nhập tay thân thiện (ô ngày auto-mask/lịch, CHANGES #14) + ảnh 2 nút chụp/chọn-từ-máy & phóng to popup (CHANGES #15). Kiểm: server 67 test · webapp 24 · 4 review đã vá · Playwright 1440/375 · deploy live.
**Story:** Là nhân viên thu nhận, tôi muốn nhập tay và chụp ảnh chân dung rồi gửi lên VPS, để thu thập được cả khi không quét được QR.

**Steps to Complete:**
1. Nhập/sửa các trường cá nhân (khi không quét QR hoặc cần bổ sung).
2. Chụp ảnh chân dung thô (người thật) hoặc ảnh thẻ; bản desktop có thể thêm ảnh sau/upload.
3. Bấm gửi → bản ghi + ảnh thô lên VPS, trạng thái `cho_nap`.

**Done khi:**
- ✅ Gửi thành công → bản ghi có UUID, trạng thái `pending` trên VPS.
- ✅ Xem lại được danh sách bản ghi mình đã gửi.
- ✅ **Hiện ảnh chân dung thật** (thumbnail) ở danh sách + chi tiết hồ sơ đã gửi (không còn icon xám) — nhân viên tải lại ảnh của **chính mình** qua endpoint mới (TDD §4.3). (CHANGES #12)
- ✅ **Bấm hồ sơ đã gửi → xem chi tiết**; khi còn **Chờ nạp** cho **Sửa thông tin** + **Chụp/đổi ảnh** (server cho sửa lúc `pending`); khi **Đang nạp/Đã nạp** thì **chỉ xem**. (CHANGES #12)
- ✅ **Tìm trong danh sách đã gửi** theo **tên (khớp cả có dấu lẫn không dấu)** hoặc **số CCCD**; ô tìm đặt trên đầu danh sách, màn hẹp thu gọn thành **nút kính lúp** (bấm mới bung ô nhập). (CHANGES #10)
- ✅ Nơi thường trú lấy từ QR (hoặc nhập tay), cho sửa trước khi gửi. Nơi cư trú (tạm trú) **không nhập ở app** — tool mặc định = nơi thường trú khi nạp (BR-004 / TDD §8.1; xem CHANGES #9).
- ✅ **Gửi nhanh không ảnh để nhập liên tiếp** (CHANGES #13): ở màn xác nhận bấm "Lưu & nhập hồ sơ tiếp" → gửi hồ sơ **không kèm ảnh** → hiện **toast "Đã gửi ✓"** (không qua màn kết quả) → về màn chọn cách nhập. Mất mạng vẫn giữ nháp, tự gửi lại khi có mạng (như cũ).
- ✅ **Badge "Thiếu ảnh" + bộ lọc** (CHANGES #13): ở "Hồ sơ đã gửi", hồ sơ chưa có ảnh chân dung hiện **badge "Thiếu ảnh"** (list + chi tiết) và có **bộ lọc riêng gom hồ sơ thiếu ảnh** để chụp bổ sung sau (nút "Thêm ảnh" cho hồ sơ Chờ nạp đã có). Badge thông báo cho mọi trạng thái; chụp bù chỉ áp hồ sơ còn **Chờ nạp** (đã nạp phải bổ sung ảnh ở tool — QLY-05).
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

#### [NAP-01] Tool kéo hàng đợi + chống trùng

**Trạng thái:** 🔄 In Progress — **thêm yêu cầu 04/10/2026 (CHANGES #32, chưa code):** lưu nháp BỀN (địa chỉ+chi tiết+nơi cấp+tick+ảnh) xuống máy tool + tự xóa sau nạp/bỏ hàng đợi/xóa VPS · 2 chip Địa chỉ/Ảnh mỗi dòng · nút "Xử lý" to + cả dòng bấm · nạp chặn khi thiếu địa chỉ, cảnh báo khi thiếu ảnh + lối tắt bổ sung ảnh; phần đã code vẫn đúng, story ở lại hàng đợi. — task 44 (03/10) XONG: đồng bộ bỏ hồ sơ đã xóa khi "Kéo về" — server `GET /api/nap/da-xoa?since=` (đọc `audit_log` hành động `'xoa'` THU-05; KHÔNG suy từ vắng mặt trong `/keo`) + tool bỏ dòng staging `'cho'` trùng uuid (mốc incremental, dòng đã nạp/lỗi giữ nguyên) + toast "bỏ N hồ sơ đã xóa ở app". Kiểm mức 1: server 116 pytest (+6) · tool 165 pytest (+4) · webui build + 29 vitest · review-nghiepvu đủ. **Còn task 46/47 (redesign Nạp lô) + verify live Checkpoint 8** (gửi→xóa→kéo biến mất). Yêu cầu thêm 02/10/2026 (CHANGES #24: "Kéo về từ VPS" đồng bộ bỏ hồ sơ collector đã xóa ở app web — THU-05); phần đã code vẫn đúng, story quay lại hàng đợi để thêm đồng bộ xóa. task 38 (CHANGES #22) xong 02/10/2026: "Bỏ khỏi hàng đợi" (`DELETE /local/keo-ve/:uuid`, guard chỉ dòng đã nạp `'xong'`, tool-local — KHÔNG đụng prod) + "Nạp lại nhanh" dòng lỗi (tái dùng nạp lô 1 uuid). Kiểm: +5 test (132 pytest, gồm endpoint 401/404/409/200) · build · 29 vitest · review-nghiepvu 2/2. 2 nút UI là reuse mỏng của luồng đã live-verify — xác nhận thao tác khi chạy tool. Phần đã xong trước đó: ✅ Done 01/10/2026 — ① backend (kéo→staging, nạp lô lock→nạp→da-nap, +2 vá server) + ② UI 2 chế độ (ô tìm/IN HOA/chính tả/badge) + AC "kéo lại làm tươi bản chờ nạp" (CHANGES #11). Kiểm: tool 72 + server 56 test · Playwright 3vp · review-nghiepvu 9/9. (Tra cứu DB = QLY-01 task 22)
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
- ⬜ **"Bỏ khỏi hàng đợi"** (CHANGES #22): xóa dòng 🟢 Đã nạp khỏi hàng đợi staging của tool (SQLite cục bộ) — KHÔNG đụng DB prod; VPS đã đánh dấu đã nạp nên kéo lại không mang về. Tên nhẹ, TÁCH BẠCH với "Xóa khỏi DB" của Tra cứu DB (tránh xóa nhầm prod).
- ⬜ **"Nạp lại nhanh"** dòng 🔴 lỗi (CHANGES #22): nút nạp lại ngay trên dòng lỗi (không phải chọn lại thủ công).
- ⬜ **Kéo về đồng bộ bỏ hồ sơ đã xóa** (CHANGES #24): bấm "Kéo về từ VPS", hồ sơ collector đã **xóa ở app web** (đánh dấu đã xóa trên VPS — THU-05) → **biến mất khỏi hàng chờ nạp** của tool (bỏ dòng staging `pending` tương ứng). Chỉ áp dòng **chưa nạp**; dòng đã nạp/đã lỗi giữ nguyên.
- ⬜ **Redesign UX màn Nạp lô — trạng thái sẵn sàng mỗi dòng** (CHANGES #26): mỗi hồ sơ chờ nạp hiện rõ `✔ Sẵn sàng` hoặc thiếu gì (`⚠ Thiếu địa chỉ` / `⚠ Thiếu ảnh` / `⚠ Chưa chọn giấy tờ`) — nhìn là biết nạp được hàng nào, không phải mở từng cái.
- ⬜ **Hai chip trạng thái chuẩn bị trên mỗi dòng** (CHANGES #32): mỗi dòng HV hiện **2 chip riêng** — `✓ Địa chỉ 2 cấp` / `✗ Chưa map địa chỉ` và `✓ Có hình` / `✗ Chưa có hình`; **mặc định ✗ (xám)** khi chưa làm. Nhìn là biết từng HV đã map địa chỉ / đã chuẩn bị ảnh chưa, không phải mở drawer. (Cụ thể hóa dòng "trạng thái sẵn sàng" #26.)
- ⬜ **Nạp lô — chặn/cảnh báo theo mức bắt buộc** (CHANGES #32): **thiếu địa chỉ 2 cấp → CHẶN nạp** dòng đó (địa chỉ bắt buộc); **thiếu ảnh → vẫn cho nạp nhưng CẢNH BÁO rõ** "N học viên nạp thiếu ảnh — bổ sung sau ở Tra cứu DB" (ảnh không bắt buộc, bổ sung qua QLY-05). Sau nạp, nếu có HV thiếu ảnh → hiện **lối tắt mở Tra cứu DB lọc "chưa ảnh"** để bổ sung ngay.
- ⬜ **Chọn nhiều HV để nạp vào khóa chưa BC1 thuận tiện** (CHANGES #26): nút **"Chọn tất cả sẵn sàng"** tick mọi dòng đủ điều kiện (bỏ qua dòng còn thiếu); thanh hành động dính đáy một nút chính **"Nạp N học viên"**.
- ⬜ **Ngăn "Chuẩn bị" trượt ra khi cần** (CHANGES #26): bấm "Chuẩn bị" ở một dòng → ngăn trượt từ phải (map địa chỉ + giấy tờ + ảnh); lưu xong dòng chuyển `✔ Sẵn sàng`. Bỏ cột chuẩn bị cố định để màn gọn, bớt rối.
- ⬜ **Mở hồ sơ dễ thao tác** (CHANGES #32): **cả dòng HV bấm được** để mở ngăn Chuẩn bị + thêm **nút "Xử lý" to, rõ bên phải** mỗi dòng — thay nút/icon nhỏ, tránh bấm nhầm, nhìn thấy ngay chỗ bấm.
- ⬜ **Lưu nháp BỀN khi chuẩn bị hồ sơ** (CHANGES #32): mọi chỉnh sửa khi chuẩn bị (địa chỉ 2 cấp đã map, chi tiết, nơi cấp, tick giấy tờ, **và ảnh đã đổi nền**) được **lưu xuống máy tool**, không mất khi tải lại trang / đóng mở tool. Nháp **tự xóa** khi: nạp xong · "Bỏ khỏi hàng đợi" · hồ sơ bị xóa trên app web (đồng bộ xóa). Nhờ đó 2 chip trạng thái phản ánh đúng kể cả sau khi mở lại tool.
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

> Nguồn: CAP-004 · BR-015 · EC-062 · EC-071 · CHANGES #6 · CHANGES #11 · CHANGES #32

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

**Trạng thái:** ⏳ Todo — yêu cầu bổ sung UI ảnh 02/10/2026 (CHANGES #23: hiện ảnh đã chỉnh + mở lại chỉnh tiếp + nhãn nút lưu rõ); code cũ (CHANGES #19+#20) vẫn đúng, story quay lại hàng đợi để làm phần UI mới. Trình chỉnh ảnh: nạp sẵn ảnh VPS + grab 2 trục + xoay (−90/+90 + nghiêng) + khung chân dung mẫu + warm-up rembg (u2net); xử lý qua canvas (WYSIWYG). Kiểm: webui build + 29 test + Playwright. **Còn kiểm tay 'mở .jp2 bằng app cũ' (1c) + verify trên tool thật.**
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

**Trạng thái:** ⚠️ Partial — chờ verify máy CSDT. Toàn bộ 6 task code XONG: task 22 (tra cứu + sửa nhân thân) · 34 (backend `/anh`+`/anh-thumb` `.jp2`→PNG) · 35 (UI: avatar lưới lazy 3-ca · modal ảnh lớn + đường dẫn `DuongDanAnh` + cảnh báo 404/422 · click ảnh→AnhModal) · 36 (thống kê Tổng·Thiếu ảnh + badge BC1 cấp khóa [phương án A] + nút đổi-khóa/xóa nhanh ra lưới, ẩn khi BC1). Kiểm mức 1: 125 pytest · 29 vitest · build sạch · review-nghiepvu task 35 3/3 + task 36 2/2. **Chờ verify máy CSDT (SQL Server GPLX_CSDT live):** render ảnh thật + 3 ca avatar + cảnh báo 404/422 + click→chỉnh→lưu đè + đổi-khóa/xóa nhanh trên HV thật (ghi prod + chặn BC1). Đã verify live trước đó: tra cứu khóa + lưới HV (khóa B-K149, 55 HV). Mở rộng yêu cầu 02/10/2026 (CHANGES #22: hiện ảnh chân dung + avatar lưới + đường dẫn ảnh + cảnh báo file thiếu + thống kê đầu khóa + nút đổi-khóa/xóa nhanh ra list). Phần đã code trước đó (chờ verify prod): **Lát 1 (đọc, task 22) xong + verify live:** Tra cứu DB — tìm khóa mọi khóa kể cả BC1 + lưới HV theo khóa (`usp_NguoiLX_Select_By_MaKH`) + tìm trong lưới + xem chi tiết (verify live: khóa B-K149, 55 HV đúng). **Lát 2 (sửa, task 22) code xong — CHỜ VERIFY PROD:** sửa **thông tin nhân thân** (họ tên/ngày sinh/giới tính/CCCD/địa chỉ TT) qua `usp_NguoiLX_Update`, đọc lại full bản ghi để giữ cột không sửa; chặn sửa khi khóa đã BC1 (BR-012). **Thu hẹp phạm vi:** bỏ `usp_NguoiLX_HoSo_Update` khỏi QLY-01 (SP ghi đè 65 cột gồm kết quả thi/báo cáo → rủi ro) — ảnh để QLY-05, đổi khóa QLY-02 (CHANGES #17). Kiểm: tool **101 test** + webui **19 test** + build. Chờ bạn verify ghi prod thật + chặn BC1 live. **BUG-02 (03/10, đã sửa):** lưới Tra cứu DB (`ds_ho_so`) trước dùng SP app cũ lọc cứng `TT_XuLy IN ('03','04')` → ẩn HV chưa ảnh (bộ lọc "Chưa ảnh" luôn rỗng); nay thay SELECT riêng bỏ lọc TT_XuLy (không sửa SP cũ). +1 test hồi quy. Xem `docs/BUGS.md`. (Ghi chú: con số "55 HV" verify trước đây là số đã BỊ SP lọc — thực tế khóa có 57.)
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

**Trạng thái:** ⏳ Todo — **thêm yêu cầu 04/10/2026 (CHANGES #32, chưa code):** bổ sung ảnh cho HV thiếu ảnh lấy từ file máy tính HOẶC kéo ảnh thô VPS, qua cùng AnhModal + đổi nền. — yêu cầu bổ sung UI ảnh 02/10/2026 (CHANGES #23: sau khi lưu/chỉnh hiện ảnh đã chỉnh + mở lại chỉnh tiếp + nút lưu rõ); code task 33 (vá `TT_XuLy`) vẫn đúng, story quay lại hàng đợi để làm phần UI mới. task 33 (🐛 vá `TT_XuLy` + ghi ảnh atomic) XONG + 123 test (2 hồi quy); còn task 34-35 (xem ảnh/click từ Tra cứu DB). Nền (CHANGES #22: 🐛 sửa bug `TT_XuLy='03'` làm rơi HV khỏi Báo cáo 2 + cho click ảnh từ Tra cứu DB mở trình chỉnh). Phần đã code trước đó (task 27): màn Tra cứu DB thêm lọc tình trạng ảnh (Tất cả/Chưa ảnh/Đã có ảnh) + nút Nạp/Thay ảnh → tái dùng `AnhModal` (NAP-04: crop 3:4 + nền trắng + .jp2 353×471) → `POST /local/ho-so/nap-anh` ghi `.jp2` (ghi đè khi thay) + UPDATE 5 cột ảnh hướng A (`ghi_anh_update` dùng chung NAP-05); cảnh báo trước khi ghi đè; retry UPDATE 1 lần theo MaDK khi lỗi (EC §11.5), file bị khóa app cũ → báo đóng (409). Nạp/thay ảnh dùng được cả khóa đã BC1 (chỉ cập nhật ảnh). Kiểm: tool 119 test (11 QLY-05) · webui build · Playwright 3vp (0 tràn) · review-nghiepvu Done khi 5/5 + edge case retry đã vá. **Chờ verify ghi ảnh thật trên SQL Server.**
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
- ⬜ **Bổ sung ảnh cho HV thiếu ảnh — 2 nguồn** (CHANGES #32): với HV đã nạp nhưng **chưa có ảnh** (lọc "chưa ảnh"), mở AnhModal và lấy ảnh gốc từ: **(a) chọn từ file máy tính** · **(b) kéo ảnh thô học viên gửi trên VPS** (tra theo HV, nếu ảnh còn trên VPS — bản gửi giữ ~30 ngày). Qua **cùng trình chỉnh + đổi nền** như NAP-04 rồi nạp vào DB (dùng luồng QLY-05 sẵn có). Ảnh thô VPS đã hết hạn → chỉ còn nguồn (a).
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

**Trạng thái:** ⏳ Todo — đổi nhãn nút 02/10/2026 (CHANGES #23: "Mở khóa khác" → **"Tạo thêm hồ sơ ở khóa học khác hạng"** cho đúng bản chất tạo hồ sơ MỚI, giữ hồ sơ cũ; GIỮ hiển thị cả ở khóa đã BC1 vì học thêm hạng không đụng báo cáo cũ); code task 32 vẫn đúng, chỉ sửa nhãn. Code xong: nút "Mở khóa khác" ở Tra cứu DB → `MoKhoaKhacDialog` điền sẵn thông tin cá nhân (`GET /local/ho-so/day-du` đọc NguoiLX) → chọn loại + khóa đích chưa BC1 (khác hạng) → tick giấy tờ + ảnh tùy chọn → nạp MỚI qua SP gộp `@p_MaDK=NULL` (MaDK mới, chung SoCMT, đăng ký cũ giữ nguyên); chặn trùng cùng khóa đích (kiemTrung disable nút + server `@p_out=-2`). KHÔNG nâng hạng. Kiểm: tool 121 test (2 gate day-du) · webui build · Playwright 1440/375 (0 tràn) · review-nghiepvu 3/3 Done khi. **Chờ verify nạp thật trên SQL Server.**
**Story:** Là nhân viên nạp DB, tôi muốn mở hồ sơ ở một khóa khác (khác hạng) cho học viên đã có trong DB, để học viên học thêm hạng mà không phải nhập lại thông tin từ đầu.

**Căn cứ DB (kiểm thật 01/10, CHANGES #16):** SP `ThemMoiCapNhat` khi nạp mới (`@p_MaDK` rỗng) **luôn tạo `NguoiLX` mới** (MaDK mới) — không dò người cũ. Dữ liệu thật: nhiều HV có 2–8 khóa, mỗi khóa 1 hồ sơ, **chung SoCMT** → nhiều dòng cùng SoCMT là đúng thiết kế, KHÔNG phải trùng. Nên nạp khác khóa = **nạp mới bình thường**, không cần nối người cũ.

**Done khi:**
- ⬜ Từ màn Tra cứu DB (QLY-01), chọn HV đã có → **nút "Tạo thêm hồ sơ ở khóa học khác hạng"** (CHANGES #23: nhãn cũ "Mở khóa khác"/"Mở hồ sơ khóa khác" gây hiểu nhầm là *chuyển* khóa) → điền sẵn thông tin cá nhân từ bản ghi cũ (đọc theo SoCMT/MaDK) để đỡ gõ lại. Nút **hiển thị cả khi khóa đã BC1** (tạo hồ sơ mới ở khóa khác hạng, KHÔNG đụng hồ sơ/báo cáo cũ) — khác nút "Đổi khóa" (QLY-02, chuyển cùng hạng) vốn đã ẩn khi BC1.
- ⬜ Chọn khóa đích (khác hạng, vẫn là cấp mới — `MaLoaiHs` 1/2 theo khóa NAP-02) → nạp mới qua SP gộp (`@p_MaDK=NULL`) → tạo MaDK mới + hồ sơ ở khóa đích; đăng ký cũ giữ nguyên.
- ⬜ Chặn trùng trong **cùng khóa đích** (NAP-06 theo khóa): HV đã có trong khóa đó → báo trùng, không tạo thêm.
- ❌ Không làm nâng hạng (B→C/D/E) — ngoài MVP (SP có tham số thâm niên/km nhưng chưa thu thập).

> Nguồn: user 01/10/2026 (CHANGES #13/#16) · kiểm DB thật · NAP-06 "cùng CCCD khác khóa thì cho phép" · liên quan QLY-01/QLY-02

#### [QLY-07] Đổi nền trắng ảnh cho cả khóa

**Trạng thái:** ⚠️ Partial — chờ verify máy CSDT. task 39 (backend) + task 40 (UI) XONG. Backend: job đổi nền cả khóa chạy thread + tiến độ (`POST`/`GET /local/khoa/:ma_kh/doi-nen`) · applock `sp_getapplock` · `_BACKUP` chỉ-nếu-chưa-có (`<khóa>/_BACKUP/`) · heuristic 4 góc · giữ `TT_XuLy` · HV không ảnh bỏ qua · 1 HV lỗi không hỏng lô. UI: `DoiNenDialog` (chọn phạm vi chỉ-chưa-trắng/tất cả + sao lưu + thanh tiến độ polling 1.5s + ds lỗi + chặn đóng khi đang chạy + làm tươi lưới). Kiểm: 146 pytest (+14 doinen) · build · 29 vitest · review-nghiepvu task 39+40 đủ. **Chờ verify máy CSDT:** chạy rembg đổi nền 1 khóa thật (ảnh trắng · tiến độ · `_BACKUP` không đè lần 2 · `TT_XuLy` giữ cho khóa đã BC2). Thêm mới 02/10/2026 (CHANGES #22).
**Story:** Là nhân viên nạp DB, tôi muốn đổi nền trắng hàng loạt cho ảnh của cả một khóa, để chuẩn hóa ảnh cũ (nạp từ app cũ, nền chưa trắng) mà không phải xử lý từng học viên.

**Done khi:**
- ⬜ Từ màn Tra cứu DB, chọn 1 khóa → "Đổi nền trắng cả khóa" → chạy xử lý rembg (crop 3:4 + nền trắng như NAP-04) cho ảnh từng HV.
- ⬜ **Chạy nền + thanh tiến độ** (N/tổng, số lỗi), không treo giao diện (ước ~1-3 giây/ảnh × ~100 HV ≈ vài phút).
- ⬜ **Sao lưu ảnh gốc vào `_BACKUP` trước khi ghi đè** (tùy chọn, mặc định bật) — ghi đè `.jp2` không khôi phục được nếu không sao lưu.
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

> Nguồn: user 02/10/2026 (CHANGES #22) · dùng lại NAP-04 · liên quan QLY-05 · bảo toàn Báo cáo 1/2 (schema DBcu: `NguoiLX_HoSo.MaBC1/MaBC2`, `usp_BaoCao2_DSHS` lọc `TT_XuLy`)

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

**Trạng thái:** 🔄 In Progress — task 48 (backend đối soát + phòng tuyến 2) đang code 04/10/2026. Yêu cầu mới 03/10/2026 (CHANGES #28, từ ca Lê Thị Hồng / BUG-01). Phạm vi chốt: đối soát **theo khóa / theo yêu cầu** (không quét toàn bộ).
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
**Trạng thái:** 🔄 In Progress — 3 story SYNC-01/02/03 đã ✅ (task 56-62, 04/10/2026). **Chưa chốt Feature** — chờ user duyệt + E2E sync thật 1 khóa nhỏ (Checkpoint 12, `/kiemthu`). Còn task 26 (đóng gói .exe) ngoài phạm vi Feature.

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
- ⬜ **(CHANGES #37) Thêm trường sửa:** **địa chỉ thường trú 2 cấp** (chọn Tỉnh + Xã chuẩn → ghi `NoiTT_MaDVHC`/`NoiTT_MaDVQL`, không chỉ dòng chữ) · **ngày cấp CCCD** (`NgayCapCMT`) · **nơi cấp CCCD** (`NoiCapCMT`, Sở GTVT). `usp_NguoiLX_Update` đã nhận sẵn các tham số này. (Nơi cư trú 2 cấp để sau; KHÔNG làm số CMND cũ vì SP update không nhận.)
- ⬜ **Bộ chọn Tỉnh/Xã + danh mục Sở GTVT đọc từ DB ĐÍCH** (`target_key`), không phải DB Nạp — nếu đọc nhầm DB Nạp thì danh mục Xã/Sở hiện sai. Tái dùng `ComboLoc`/`AddressCombo` nhưng cho nhận nguồn danh mục đích.
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
| 05/10/2026 | v3.3 — **+Nhóm "Đóng gói & khởi chạy tool độc lập"** (CHANGES #38): 4 story mới `DGT-01` (đóng gói exe PyInstaller + FastAPI phục vụ UI cùng cổng) · `DGT-02` (tự mở trình duyệt + khay hệ thống + chống chạy 2 bản + tùy chọn tự chạy khi bật máy) · `DGT-03` (wizard thiết lập lần đầu, tái dùng test-before-save) · `DGT-04` (phiên đăng nhập **vĩnh viễn** lưu đĩa + thu hồi từ xa, chỉ Đăng xuất mới thoát). HTG-01 +dòng trỏ DGT-04 (chỉ tool; web giữ phiên thường, vẫn ✅). | PM |
