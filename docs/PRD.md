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
- ✅ Tool có màn **Cấu hình**: nhập kết nối SQL Server (server/database/user/password) + URL VPS + API key, có nút "Kiểm tra kết nối", lưu vào config cục bộ (mã hóa).
- ✅ Nhân viên thu nhận không gọi được chức năng nạp DB (chặn 403).
- ❌ Không làm SSO/đăng nhập bằng Google/Zalo lần này.

> Nguồn: CAP-014 · BR-020 · OG-001, OG-002, OG-004 · EC-050

#### [THU-01] Quét QR căn cước + xác nhận/sửa (app web, mobile)

**Trạng thái:** ✅ Done — 01/10/2026. Nhập liên tiếp ("Lưu & nhập hồ sơ tiếp") + redesign UX nhập liệu (task 30, CHANGES #13/#14: ẩn ô CMND cũ, ô ngày auto-mask "/" + nút lịch giữ năm-only, desktop 2 cột + 2 nút tách hai đầu + phím tắt + nới khung). Kiểm: webapp 24 test · build · 4 review (nghiệp vụ/kỹ thuật/bảo mật/giao diện) đã vá · Playwright 1440/375 · deploy live `029026c`. Nền quét QR (task 18/28) — khung bám QR cần thẻ thật AS-001.
**Story:** Là nhân viên thu nhận, tôi muốn quét QR căn cước để điền sẵn hồ sơ, để giảm gõ tay.

**Steps to Complete:**
1. Mở app web → **màn vào** cho chọn: **Quét QR CCCD** / **Nhập tay** / **Tải ảnh CCCD**. Camera **chỉ bật khi bấm "Quét QR"** (không tự mở sau đăng nhập — CHANGES #12).
2. Bấm Quét → bật **camera sau** (`facingMode: {ideal:'environment'}`, ~1080p); best-effort `focusMode: continuous` + zoom 2x + nút đèn flash (torch). Tự giải mã liên tục, không cần bấm chụp.
3. Giải mã bằng **BarcodeDetector API** (native, nhanh) → fallback **qr-scanner (ZXing)** khi trình duyệt không hỗ trợ; **auto-capture** khi kết quả ổn định ~2 frame (~500ms).
4. Quét được → **hiệu ứng quét OK** (app tự thiết kế riêng: rung + đổi màu + tick ✓) rồi hiện màn preview.
5. Parse chuỗi QR (chuẩn Bộ Công an 2021) → hiện các trường **cho sửa** trước khi giữ.

**Done khi:**
- ✅ **Màn vào không tự mở camera** — cho chọn Quét QR / Nhập tay / Tải ảnh; camera bật khi bấm Quét (CHANGES #12).
- ✅ Quét mặt trước CCCD gắn chip hợp lệ → điền đúng: CCCD (12 số), [CMND cũ 9 số nếu có], họ tên, ngày sinh (ddMMyyyy → lưu yyyymmdd), giới tính (Nam/Nữ), nơi thường trú, ngày cấp.
- ✅ Chuỗi QR **6 hoặc 7 trường** (tách `|`, CMND cũ tùy có) đều parse được; sai định dạng → báo lỗi rõ (số trường / CCCD ≠ 12 số...).
- ✅ **Khung quét bám theo mã** khi bắt trúng (dùng 4 góc `cornerPoints` của BarcodeDetector) — không phải khung xanh tĩnh; vẫn auto-capture khi ổn định; hiệu ứng báo thành công; mọi trường sửa được. (CHANGES #12)
- ✅ Trên điện thoại (NFR Responsive): layout **vừa một màn** (`100dvh`), khung camera co giãn, **thanh điều hướng + nút hành động chính dính đáy**, không phải cuộn để thấy nút. **Logo header không phải nút** (bỏ dáng camera bấm được). (CHANGES #12)
- ✅ Decoder: BarcodeDetector native + fallback qr-scanner (ZXing) — tham khảo cách quét từ dự án webThanhdat; hiệu ứng thiết kế riêng.
- ✅ **Lưu & nhập hồ sơ tiếp** (CHANGES #13): màn xác nhận có thêm nút **"Lưu & nhập hồ sơ tiếp"** bên cạnh "Tiếp tục — chụp ảnh chân dung" → gửi ngay **không kèm ảnh** (chi tiết gửi + toast ở THU-02) rồi về **màn chọn cách nhập** (Quét QR / Nhập tay / Tải ảnh) để làm hồ sơ kế tiếp. Áp cho cả quét QR lẫn nhập tay (cùng đi qua màn xác nhận).
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

**Trạng thái:** ✅ Done — 01/10/2026. ① backend (kéo→staging, nạp lô lock→nạp→da-nap, +2 vá server) + ② UI 2 chế độ (ô tìm/IN HOA/chính tả/badge) + AC "kéo lại làm tươi bản chờ nạp" (CHANGES #11). Kiểm: tool 72 + server 56 test · Playwright 3vp · review-nghiepvu 9/9. (Tra cứu DB = QLY-01 task 22)
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
- ❌ Không kéo bản ghi đã nạp/đã xóa.

**Edge cases:**
| Tình huống | Hành vi mong muốn |
|---|---|
| VPS/tunnel down khi kéo | Tool vẫn xử lý bản ghi đã kéo (staging); báo lỗi, cho thử lại |
| Nạp lô, vài HV lỗi | Dòng lỗi 🔴 + lý do, dòng xong 🟢; lô vẫn chạy hết (EC-071) |
| Tên thiếu dấu / ký tự lạ (từ QR hỏng hoặc gõ tay) | Cảnh báo mức A, cho sửa; không chặn cứng |
| Kéo xong, người thu nhận sửa thông tin/ảnh trên app web | Kéo lại làm tươi bản 'chờ nạp'; bản đã nạp/đã lỗi giữ nguyên (CHANGES #11) |

> Nguồn: CAP-004 · BR-015 · EC-062 · EC-071 · CHANGES #6 · CHANGES #11

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
- ✅ Dropdown chọn tay Tỉnh→Xã: Tỉnh lấy từ `DM_DVHC` (DISTINCT `MaDVQL`, `TrangThai=1`); Xã qua `usp_DM_DVHC_SelectDanhSachXaPhuongTheoTinh` + lọc `TrangThai=1`. (SP `usp_DM_DVHC_SelectAll_Tinh` chỉ trả đơn vị cũ TW/TI — không dùng được cho model 2 cấp mới; xem CHANGES #2.)
- ❌ Không tự đoán khi xã bị chia — cho chọn tay.

**Edge cases:**
| Tình huống | Hành vi mong muốn |
|---|---|
| Xã bị chia (isDividedWard) / không khớp map | Popup chọn tay Tỉnh/Xã mới |

> Nguồn: CAP-006 · BR-006 · EC-032 · verify phủ 3321/3321 xã (30/09/2026)

#### [NAP-04] Căn ảnh + xóa phông trắng + xuất .jp2

**Trạng thái:** ⚠️ Partial — 02/10/2026 (CHANGES #19+#20). Trình chỉnh ảnh: nạp sẵn ảnh VPS + grab 2 trục + xoay (−90/+90 + nghiêng) + khung chân dung mẫu + warm-up rembg (u2net); xử lý qua canvas (WYSIWYG). Kiểm: webui build + 29 test + Playwright. **Còn kiểm tay 'mở .jp2 bằng app cũ' (1c) + verify trên tool thật.**
**Story:** Là nhân viên nạp DB, tôi muốn căn khung chân dung, xoay cho thẳng, xóa phông thành nền trắng và xuất `.jp2`, để ảnh đúng chuẩn app cũ.

**Steps to Complete:**
1. Hiện ảnh thô; **khung crop cố định tỷ lệ 3:4** + **khung chân dung mẫu mờ chồng lên** (ô-van đầu + đường căn mắt/cằm) để biết đặt mặt vào đâu; tự nhận diện mặt gợi ý vị trí; **grab di chuyển + phóng to/thu nhỏ + xoay** (kéo chuột/chạm) để canh mặt vào giữa; chỉnh tay hoặc thay ảnh khác.
2. Xóa phông → **nền trắng** (`rembg`); xem trước.
3. Khi bấm Nạp mới xuất `.jp2` (`Pillow`) và ghi file.

**Done khi:**
- ✅ **Ảnh thô đã kéo về từ VPS được nạp sẵn vào trình chỉnh** (có ngay trong khung crop 3:4 để căn + đổi nền), không bắt operator chọn lại file; vẫn cho chọn file khác nếu muốn thay. (CHANGES #19)
- ✅ **Grab tự do 4 hướng:** kéo ảnh trái/phải **và** lên/xuống để căn mặt (không bị ghim một trục ở mức zoom gốc); vùng lộ ra khi kéo → nền trắng. (CHANGES #20)
- ✅ **Xoay ảnh:** nút xoay nhanh **−90°/+90°** + thanh **tinh chỉnh độ nghiêng** (vài độ) để làm thẳng mặt; ảnh xoay rồi mới crop + xuất. (CHANGES #20)
- ✅ **Khung chân dung mẫu** mờ chồng lên khung crop (ô-van đầu + đường căn) để operator biết căn; **chỉ là hướng dẫn, KHÔNG dính vào ảnh `.jp2` xuất ra**. (CHANGES #20)
- ✅ **Xóa phông nhanh:** bật **warm-up rembg lúc khởi động tool** (bỏ `TOOL_SKIP_WARMUP=1` ở `tool-start.bat`) → ảnh đầu chỉ chờ 1 lần lúc mở tool, ảnh sau <5s (TDD §9.2); GIỮ model u2net (không đổi chất lượng). (CHANGES #20)
- ✅ File `.jp2` (JPEG 2000) **tỷ lệ 3:4, nền trắng, RGB**; kích thước **353×471 (~48 KB, khớp cụm phổ biến nhất của app cũ)** — hoặc 480×640 nếu chọn nét hơn; mở được bằng app cũ.
- ✅ Ghi file tại `<IMG_PATH_CSDT>\<MaKhoaHoc>\<MaDK>.jp2` (**dùng lại `MaDK` do SP trả về**, không sinh timestamp mới — verify 39.648 HV khớp 100%, TDD §9.2); DB lưu `DuongDanAnh`, `ChatLuongAnh=1`.
- ✅ `IMG_PATH_CSDT` đọc từ `QTHT_ThamSoHT`, không hard-code.
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

#### [QLY-01] Tra cứu & sửa hồ sơ đã có

**Trạng thái:** ⚠️ Partial — 02/10/2026. **Lát 1 (đọc, task 22) xong + verify live:** Tra cứu DB — tìm khóa mọi khóa kể cả BC1 + lưới HV theo khóa (`usp_NguoiLX_Select_By_MaKH`) + tìm trong lưới + xem chi tiết (verify live: khóa B-K149, 55 HV đúng). **Lát 2 (sửa, task 22) code xong — CHỜ VERIFY PROD:** sửa **thông tin nhân thân** (họ tên/ngày sinh/giới tính/CCCD/địa chỉ TT) qua `usp_NguoiLX_Update`, đọc lại full bản ghi để giữ cột không sửa; chặn sửa khi khóa đã BC1 (BR-012). **Thu hẹp phạm vi:** bỏ `usp_NguoiLX_HoSo_Update` khỏi QLY-01 (SP ghi đè 65 cột gồm kết quả thi/báo cáo → rủi ro) — ảnh để QLY-05, đổi khóa QLY-02 (CHANGES #17). Kiểm: tool **101 test** + webui **19 test** + build. Chờ bạn verify ghi prod thật + chặn BC1 live.
**Story:** Là nhân viên nạp DB, tôi muốn tra cứu và sửa hồ sơ học viên đã có trong DB, để thay phần lớn thao tác của app cũ.

**Done khi:**
- ✅ **Chế độ "Tra cứu DB"** (CHANGES #6): **tìm khóa theo tên khóa hoặc mã khóa — MỌI khóa, kể cả đã lập BC1** (khác dropdown nạp của NAP-02 vốn ẩn khóa BC1). Chọn khóa → lưới học viên theo khóa (`usp_NguoiLX_Select_By_MaKH`) + tìm theo **tên (khớp cả có dấu lẫn không dấu)**/CCCD/số hồ sơ (`usp_NguoiLX_HoSo_Search`); ô tìm đặt trên đầu lưới, màn hẹp thu gọn thành **nút kính lúp**. (CHANGES #10)
- ✅ Mở hồ sơ để sửa **thông tin nhân thân** (họ tên, ngày sinh, giới tính, số căn cước, địa chỉ thường trú) qua `usp_NguoiLX_Update`; đọc lại bản ghi hiện tại để giữ nguyên cột không sửa. Ảnh → QLY-05, đổi khóa → QLY-02 (KHÔNG dùng `usp_NguoiLX_HoSo_Update` ở đây — SP ghi đè 65 cột, CHANGES #17).
- ✅ Chặn sửa khi khóa đã lập BC1 (badge "Đã BC1 — chỉ xem"); khóa chưa BC1 sửa được.
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

**Trạng thái:** ⚠️ Partial — 02/10/2026 (task 24). Code xong: `POST /local/ho-so/xoa` → `usp_NguoiLX_Delete` (cascade HoSo+GiayTo); chặn HV đã có GPLX (pre-check `NguoiLX_GPLX` + verify sau xóa vì SP không raiserror); ảnh **xóa mềm** chuyển sang folder `_DELETED` (giữ tên MaDK, không xóa cứng) + ghi log staging. UI: nút "Xóa" xác nhận 2 bước ở Tra cứu DB. Kiểm: tool **111 test** + webui build · review-nghiệp-vụ **6/6 Done**. **Chờ verify xóa thật.** (Ghi chú: UI ẩn nút Xóa khi khóa BC1 — ngoài AC, backend chưa chặn tương ứng; cần `/capnhat` nếu muốn cấm xóa HV khóa BC1.)
**Story:** Là nhân viên nạp DB, tôi muốn xóa học viên nhập nhầm, để dọn hồ sơ sai mà không mất ảnh vĩnh viễn.

**Done khi:**
- ✅ `usp_NguoiLX_Delete` (cascade HoSo + GiayTo); file `.jp2` chuyển sang folder `_DELETED` (xóa mềm) + log.
- ✅ HV đã có GPLX không xóa được (FK chặn) → báo rõ.
- ❌ Không xóa cứng file ảnh.

> Nguồn: CAP-012 · BR-014 · EC-021

#### [QLY-05] Nạp/thay ảnh cho học viên đã có

**Trạng thái:** ⚠️ Partial — 02/10/2026 (task 27). Code xong: màn Tra cứu DB thêm lọc tình trạng ảnh (Tất cả/Chưa ảnh/Đã có ảnh) + nút Nạp/Thay ảnh → tái dùng `AnhModal` (NAP-04: crop 3:4 + nền trắng + .jp2 353×471) → `POST /local/ho-so/nap-anh` ghi `.jp2` (ghi đè khi thay) + UPDATE 5 cột ảnh hướng A (`ghi_anh_update` dùng chung NAP-05); cảnh báo trước khi ghi đè; retry UPDATE 1 lần theo MaDK khi lỗi (EC §11.5), file bị khóa app cũ → báo đóng (409). Nạp/thay ảnh dùng được cả khóa đã BC1 (chỉ cập nhật ảnh). Kiểm: tool 119 test (11 QLY-05) · webui build · Playwright 3vp (0 tràn) · review-nghiepvu Done khi 5/5 + edge case retry đã vá. **Chờ verify ghi ảnh thật trên SQL Server.**
**Story:** Là nhân viên nạp DB, tôi muốn bổ sung ảnh cho học viên đã nạp hồ sơ nhưng chưa có ảnh, hoặc thay ảnh mới cho học viên đã có ảnh, để hoàn tất/chuẩn hóa hồ sơ mà không phải nhập lại từ đầu.

**Steps to Complete:**
1. Trên màn tra cứu/quản lý HV, lọc học viên theo tình trạng ảnh (chưa có ảnh `TT_XuLy='01'` / đã có ảnh `'03'`).
2. Chọn HV → căn ảnh + xóa phông + xuất `.jp2` (dùng lại luồng NAP-04).
3. Ghi `.jp2` theo `MaDK` (ghi đè nếu đã có) + UPDATE 5 cột ảnh `NguoiLX_HoSo`, nâng/giữ `TT_XuLy='03'` (hướng A, TDD §10.3).

**Done khi:**
- ✅ Màn tra cứu có bộ lọc theo tình trạng ảnh; hiện đúng danh sách HV chưa ảnh / đã có ảnh.
- ✅ Bổ sung ảnh (HV `'01'`): `.jp2` ghi tại `<IMG_PATH_CSDT>\<MaKhoaHoc>\<MaDK>.jp2`; `DuongDanAnh`/`ChatLuongAnh=1`/`TT_XuLy='03'`/`NgayThuNhanAnh` cập nhật; mở app cũ thấy ảnh.
- ✅ Thay ảnh (HV `'03'`): ghi đè đúng file `.jp2` cùng tên; cập nhật lại `DuongDanAnh`/`ChatLuongAnh`/`NgayThuNhanAnh`; có cảnh báo trước khi ghi đè ảnh cũ.
- ✅ Dùng lại đúng luồng xử lý ảnh NAP-04 (crop 3:4 + nền trắng + 353×471).
- ❌ Không tạo bản ghi HV mới (chỉ cập nhật HV đã có).

**Edge cases:**
| Tình huống | Hành vi mong muốn |
|---|---|
| App cũ đang mở/khóa file `.jp2` của HV đó | Báo không ghi được file đang bị khóa, yêu cầu đóng app cũ rồi thử lại |
| Ghi `.jp2` lỗi | Giữ nguyên trạng thái ảnh cũ (`'01'` hoặc file cũ), báo lỗi, cho thử lại |
| UPDATE cột ảnh lỗi sau khi đã ghi file | Retry UPDATE theo `MaDK`; không tạo HV mới |

> Nguồn: review TDD §10 (01/10/2026, CHANGES #5) · dùng lại NAP-04 · BR-010, BR-011 · TDD §10.3 hướng A

#### [QLY-06] Mở hồ sơ khóa khác cho học viên đã có (cấp mới khác hạng, song song)

**Trạng thái:** ⚠️ Partial — 02/10/2026 (task 32). Code xong: nút "Mở khóa khác" ở Tra cứu DB → `MoKhoaKhacDialog` điền sẵn thông tin cá nhân (`GET /local/ho-so/day-du` đọc NguoiLX) → chọn loại + khóa đích chưa BC1 (khác hạng) → tick giấy tờ + ảnh tùy chọn → nạp MỚI qua SP gộp `@p_MaDK=NULL` (MaDK mới, chung SoCMT, đăng ký cũ giữ nguyên); chặn trùng cùng khóa đích (kiemTrung disable nút + server `@p_out=-2`). KHÔNG nâng hạng. Kiểm: tool 121 test (2 gate day-du) · webui build · Playwright 1440/375 (0 tràn) · review-nghiepvu 3/3 Done khi. **Chờ verify nạp thật trên SQL Server.**
**Story:** Là nhân viên nạp DB, tôi muốn mở hồ sơ ở một khóa khác (khác hạng) cho học viên đã có trong DB, để học viên học thêm hạng mà không phải nhập lại thông tin từ đầu.

**Căn cứ DB (kiểm thật 01/10, CHANGES #16):** SP `ThemMoiCapNhat` khi nạp mới (`@p_MaDK` rỗng) **luôn tạo `NguoiLX` mới** (MaDK mới) — không dò người cũ. Dữ liệu thật: nhiều HV có 2–8 khóa, mỗi khóa 1 hồ sơ, **chung SoCMT** → nhiều dòng cùng SoCMT là đúng thiết kế, KHÔNG phải trùng. Nên nạp khác khóa = **nạp mới bình thường**, không cần nối người cũ.

**Done khi:**
- ⬜ Từ màn Tra cứu DB (QLY-01), chọn HV đã có → "Mở hồ sơ khóa khác" → điền sẵn thông tin cá nhân từ bản ghi cũ (đọc theo SoCMT/MaDK) để đỡ gõ lại.
- ⬜ Chọn khóa đích (khác hạng, vẫn là cấp mới — `MaLoaiHs` 1/2 theo khóa NAP-02) → nạp mới qua SP gộp (`@p_MaDK=NULL`) → tạo MaDK mới + hồ sơ ở khóa đích; đăng ký cũ giữ nguyên.
- ⬜ Chặn trùng trong **cùng khóa đích** (NAP-06 theo khóa): HV đã có trong khóa đó → báo trùng, không tạo thêm.
- ❌ Không làm nâng hạng (B→C/D/E) — ngoài MVP (SP có tham số thâm niên/km nhưng chưa thu thập).

> Nguồn: user 01/10/2026 (CHANGES #13/#16) · kiểm DB thật · NAP-06 "cùng CCCD khác khóa thì cho phép" · liên quan QLY-01/QLY-02

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
- **Responsive:** Both. App web **mobile-first, giao diện như app mobile thật** khi dùng trên điện thoại: điều hướng dạng bottom nav/tab, thao tác chạm (nút to, vuốt), **ẩn hoặc thu gọn** các thành phần không cần trên mobile — KHÔNG phải giao diện desktop bị co nhỏ. Bản desktop của app web mới hiển thị đầy đủ dạng bảng/nhiều cột. Tool UI desktop (localhost).
- **Chuẩn hiển thị cảnh báo (CHANGES #6):** mọi cảnh báo/lỗi khi nạp (trùng CCCD, sai chính tả tên, thiếu ảnh, lỗi nạp lô) phải **inline (không hộp thoại modal), NỔI BẬT** (banner có nền + viền + icon, không chỉ dòng chữ nhỏ) và **nêu rõ NGUYÊN NHÂN cụ thể** (vd "CCCD 070… đã có ở Số hồ sơ 014 trong khóa này"). Trạng thái nạp lô dùng màu + icon + chữ (⚪ chờ / 🔴 lỗi / 🟢 xong) — **không chỉ dựa màu** (phủ người mù màu).
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
| SQL Server lỗi giữa lúc nạp | Rollback transaction, giữ `pending`, cho thử lại |
| VPS/tunnel lỗi | Tool báo lỗi, làm việc trên staging; thử lại |
| Nạp lại bản ghi đã nạp | Chặn (không tạo HV thứ 2) |
| Hai người/hai tool cùng nạp một bản ghi | Khóa bản ghi khi `importing`; chỉ tạo 1 HV |
| Bấm nút thao tác hai lần (nạp/gửi) | Disable + idempotent theo UUID; không tạo bản ghi trùng |
| Bản ghi PII quá 30 ngày đang nạp | Job xóa bỏ qua bản `importing` |

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
