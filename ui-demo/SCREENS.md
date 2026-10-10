# Tiến độ màn hình — ui-demo

> File do `/prototype` sinh, `/prototype-next` cập nhật mỗi lượt.

- **PRD nguồn:** docs/PRD.md
- **Bản HTML chuẩn:** ui-demo-options/detailed.html
- **Stack:** Vite + React + TypeScript + Tailwind v3 (token shadcn) + react-router-dom · font Be Vietnam Pro
- **Cổng dev:** 3021 (sổ `~/.claude/local-ports.md`)
- **Cập nhật lần cuối:** 07/10/2026 (**lượt 22** CHANGES #49: +màn **#23 Chụp ảnh thẻ tự đọc OCR** (THU-06) — lối nhập thứ 3 ở `/app/quet`, ⬜ chưa dựng → `/prototype-next`; lối thoát cho iPhone quét QR yếu, BUG-14). Trước: 04/10/2026 (**lượt 21** CHANGES #35: +màn **Tra cứu CDB đích** (#19) — tra khóa/xem HV/chi tiết+ảnh/thay ảnh/sửa nhân thân/xóa+đổi khóa trên `GPLX_CDB_CSDT`, luật khóa DKKH/BC1 đọc ở đích, +nút Xem chi tiết từ Bàn đồng bộ; dựng thẳng `tool/webui`, tái dùng AnhModal). Trước: **lượt 20** CHANGES #34: cấu hình kết nối **dời lên panel ⚙ header dùng chung**, gộp DB nguồn Nạp + nhiều DB đích Sync (tách bạch rõ), bỏ màn `/tool/cau-hinh` + `/sync/db-dich`; làm đẹp combobox + danh sách HV màn Bàn đồng bộ — impeccable/ui-ux-pro-max, dựng thẳng `tool/webui`. Trước: **lượt 19** CHANGES #32: 2 chip Địa chỉ/Ảnh + nút "Xử lý" to + nháp bền ở màn Nạp lô; bổ sung ảnh HV thiếu ảnh từ file/VPS — ghi UX, chưa dựng. Trước: 03/10/2026 (gộp 2 phiên song song: **lượt 17** panel "Đối soát VPS↔CSDT" QLY-09 (CHANGES #28) · **lượt 18** redesign DESKTOP app web THU-01/05 — Quét vào thẳng form + popover quét, "Hồ sơ đã gửi" chọn-nhiều-để-xóa (CHANGES #30) + tool dời nút nạp lên header & combobox gõ-lọc địa chỉ NAP-01/03 (CHANGES #29). Lượt 16: CHANGES #26)

## ⚠️ Prototype gộp 1 project — KIẾN TRÚC THẬT là 2 app riêng (TDD §2.4)

Project `ui-demo` gộp cả 2 app vào 1 router **chỉ để xem/bấm demo**. Khi code thật (`/tieptheo`) phải tách theo TDD §2.4, KHÔNG bê nguyên cấu trúc gộp:

| Folder prototype | → App thật (TDD §2.4) | Deploy |
|---|---|---|
| `src/pages/app/*` + `components/AppLayout.tsx` | **`webapp/`** (app web PWA) | VPS |
| `src/pages/tool/*` + `components/ToolLayout.tsx` | **`tool/webui/`** (React static nhúng .exe) | Máy DB |
| `src/lib/*`, `src/components/Icon.tsx`, `Placeholder.tsx` | dùng chung — copy cho cả hai | — |
| `src/pages/DangNhap.tsx`, `admin/HoSo.tsx` | app tương ứng (đăng nhập: cả hai; admin PII: `webapp/` phía VPS) | — |

Prototype là tham chiếu **style/layout**, không phải scaffold thật.

## Bảng màn hình

| # | Màn hình (PRD) | Mã story | Route | Trạng thái | Lượt |
|---|---|---|---|---|---|
| 0 | Trang chọn app (Tool / App web) | — | `/` | ✅ Xong | 1 |
| 1 | Quét QR căn cước + preview + gửi | THU-01, THU-02 | `/app/quet` | ✅ Xong | 1 |
| 2 | Nạp hồ sơ vào DB (list · thông tin · ảnh) | NAP-01, NAP-02, NAP-03, NAP-04, NAP-05, NAP-06, QLY-01 | `/tool/nap` | ✅ Xong | 1 |
| 3 | Đăng nhập & phân quyền | HTG-01 | `/dang-nhap` | ✅ Xong | 2 |
| 4 | Cấu hình kết nối (DB nguồn Nạp + nhiều DB đích Sync) — **panel mở từ icon ⚙ header** | HTG-01, HTG-07, SYNC-02 | header ⚙ (bỏ route `/tool/cau-hinh`) | ⬜ Làm lại (CHANGES #34 — dời lên header, gộp quản lý DB đích; dựng thẳng `tool/webui`) | 2 |
| 5 | Tạo khóa học | KHO-01 | `/tool/tao-khoa` | ✅ Xong | 2 |
| 6 | Hồ sơ tôi đã gửi | THU-02 | `/app/da-gui` | ✅ Xong | 3 |
| 7 | Tài khoản (app web) | HTG-01 | `/app/tai-khoan` | ✅ Xong | 3 |
| 8 | Lọc & xóa PII (quản trị VPS) | HTG-03 | `/admin/ho-so` | ✅ Xong | 3 |
| 9 | Tra cứu & sửa hồ sơ đã có | QLY-01 | `/tool/nap` (tab DB → drawer Xem/Sửa) | ✅ Xong | 4 |
| 10 | Đổi khóa + di chuyển ảnh | QLY-02 | `/tool/nap` (drawer → dialog Đổi khóa) | ✅ Xong | 4 |
| 11 | Xóa học viên + xóa mềm ảnh | QLY-03 | `/tool/nap` (drawer → dialog Xóa) | ✅ Xong | 4 |
| 12 | Nạp/thay ảnh cho HV đã có (+ click avatar/ảnh ở Tra cứu DB mở trình chỉnh — CHANGES #22) | QLY-05 | `/tool/nap` (lọc tình trạng ảnh + drawer → dialog Nạp/thay ảnh) | ⬜ Chưa có route | — |
| 13 | Nạp lô + IA 2 chế độ (hàng chờ VPS badge ⚪🔴🟢) | NAP-01 | `/tool/nap` (chế độ Nạp hồ sơ / Tra cứu DB) | ✅ Xong (+⬜ "Bỏ khỏi hàng đợi" & "Nạp lại nhanh" CHANGES #22) | 5 |
| 14 | Tra cứu DB: avatar lưới (3 ca: có ảnh/chưa ảnh/mất file) + xem ảnh lớn+đường dẫn + thống kê đầu khóa + thao tác nhanh | QLY-01 | `/tool/nap` (tab DB) | ✅ Xong | 13 |
| 15 | Đổi nền trắng cả khóa (phạm vi + sao lưu _BACKUP + thanh tiến độ) | QLY-07 | `/tool/nap` (tab DB → dialog) | ✅ Xong | 13 |
| 16 | Sync · Bàn đồng bộ (chọn khóa nguồn/đích · ngày nhập HS · bảng HV đối chiếu đích · SYNC + tiến trình SSE) | SYNC-01 | `/sync/ban-dong-bo` | ⬜ Đã dựng (task 57-59) — **làm đẹp lại** combobox + danh sách HV (CHANGES #34, impeccable/ui-ux-pro-max) | — |
| 17 | Sync · Quản lý DB đích → **dời vào khối ② của panel ⚙ header** (xem màn #4/HTG-07) | SYNC-02, HTG-07 | header ⚙ (bỏ route `/sync/db-dich`) | ⬜ Làm lại (CHANGES #34) | — |
| 18 | Sync · Lịch sử & Hủy sync khóa (log JSON + rollback dual-mode) | SYNC-03 | `/sync/lich-su` | ⬜ Chưa có route (dựng thẳng `tool/webui`) | — |
| 19 | Sync · **Tra cứu CDB đích** (tra khóa `GPLX_CDB_CSDT` → lưới HV + chi tiết + ảnh · thay ảnh · sửa nhân thân — form thêm **địa chỉ 2 cấp + ngày/nơi cấp CCCD** từ CHANGES #37 · xóa/đổi khóa · +nút Xem chi tiết từ Bàn đồng bộ) | TCB-01, TCB-02, TCB-03, TCB-04 | `/sync/tra-cuu` (dự kiến) | ⬜ Chưa có route (dựng thẳng `tool/webui`, tái dùng AnhModal/AnhAvatar; KHÔNG đụng Tra cứu DB Nạp) | — |
| 20 | **Wizard thiết lập lần đầu** (máy sạch): 3 bước — kiểm môi trường (thư mục ghi được; mạng VPS kiểm ở bước cấu hình) → cấu hình SQL nguồn/đích + VPS (test-before-next) → đăng nhập; có cấu hình rồi thì bỏ qua | DGT-03 | `/tool/thiet-lap` | ✅ Dựng thật `tool/webui/src/pages/tool/Wizard.tsx` (task 68) — tái dùng `CauHinhForm` tách từ `CauHinhDrawer`; verify visual 05/10 | — |
| 21 | **Kết quả đào tạo · Cập nhật KQĐT** (băng cam DB đích · combobox gõ-tìm khóa đã BC1 · lọc HV 4 trạng thái · lưới nhập điểm GỐC→quy đổi /10 hiện kế bên · giờ/km sân auto, đường trống-gợi-ý · Kết luận tự tính · sửa lại HV Sở từ chối/giải trình · **dòng 🔒 TT=12 có nút "Mở khóa để sửa" KQD-05** · **khi gói đã gửi hết: ô tích HV 12 + thanh "Mở sửa điểm" → hộp xác nhận (lý do + tích cam kết) → chip cam "Sửa sau gửi — chưa kết xuất lại" + băng cam đầu khóa, #53**) | KQD-01, KQD-02, KQD-04, KQD-05 | `/ket-qua/cap-nhat` (dự kiến) | ⬜ Chưa có route (dựng thẳng `tool/webui`; băng DB đích = component dùng chung với Sync) | — |
| 22 | **Kết quả đào tạo · Theo dõi kết xuất** (khóa-first master–detail: trái list khóa + tiến độ "đã KX/còn sót"; phải tiến độ theo trạng thái + panel gói hàng đợi Chưa/Đã gửi + lưới HV lọc Đã KX/Còn sót + nút "Mở khóa để sửa" KQD-05 + **khối đỏ "Sửa sau gửi — chờ kết xuất lại" (HV · khóa · người mở · lúc mở · lý do · điểm trước→sau), #53**; KHÔNG có nút kết xuất) | KQD-03, KQD-05 | `/ket-qua/ket-xuat` (dự kiến) | ⬜ Chưa có route (dựng thẳng `tool/webui`; **mock đã dựng `ui-mock/theodoiketxuat.html`** — bám theo) | — |
| 23 | **Thu nhận · Chụp ảnh thẻ (tự đọc OCR)** — lối nhập thứ 3 ở màn vào `/app/quet` cạnh Quét QR / Nhập tay / Tải ảnh: chụp/tải ảnh mặt trước CCCD → OCR điền sẵn 6 trường → **màn xác nhận dùng chung** (THU-01/02) để nhân viên soát/sửa trước khi lưu. Mọi thiết bị (lối thoát cho iPhone quét QR yếu — BUG-14) | THU-06 | `/app/quet` (bổ sung lối vào) | ⬜ Chưa dựng — **chạy `/prototype-next`** (bám màn vào + màn xác nhận đã có; engine OCR chờ `/tdd`) | — |
| 24 | **Phân công GV – xe · Phân công theo khóa** (phân hệ #4 màu hồng sẫm · băng cam DB đích · chọn khóa + hạng/ngày KG→BG/DKKH · stepper 3 bước ✓/⚠/✗ · ① GV của khóa: 2 danh sách gọn, tích chọn hàng loạt · ② Phân công dạy: ô "Ngày bắt đầu thực hành" tự nhập, nút lớn ★ Thực hành lái xe, chip môn TH tô màu, ô tích "Chỉnh giờ" bước 30 phút · ③ Ghép xe: dải chip xe gọn + bảng ghép 1 GV–1 xe + "Gợi ý ghép xe" · cột phải "Kiểm tra khóa" 3 mức bấm nhảy tới dòng · thanh bản nháp + "Ghi vào CDB" · ngăn "Mô tả nghiệp vụ" · khung hướng dẫn từng bước) | PCG-01, PCG-02, PCG-03, PCG-04 | `/phan-cong/theo-khoa` (dự kiến) | ⬜ Chưa có route (dựng thẳng `tool/webui`; **mock đã duyệt `ui-mock/phancong.html`** — bám theo) | — |
| 25 | **Phân công GV – xe · Rà soát khóa** (bảng mọi khóa: GV chưa phân công · phân công ngoài danh sách · xe chưa ghép · ghép xe ngoài danh sách · Ổn/Cần xử lý; bấm dòng mở khóa) | PCG-05 | `/phan-cong/ra-soat` (dự kiến) | ⬜ Chưa có route (bám mock `ui-mock/phancong.html` tab 2) | — |
| — | Hàng đợi VPS + xóa PII 30 ngày | HTG-02 | (backend, không có UI) | ⬜ Không dựng | — |
| — | Kết xuất Excel (NICE) | QLY-04 | (mới có nút, chưa luồng) | ⬜ NICE — sau | — |
| — | Offline app web (NICE) | THU-03 | — | ⬜ NICE — sau | — |

Chú thích: ✅ Xong · 🟡 Placeholder · ⬜ Chưa có route

## Quyết định UX đã chốt

| Màn | Vấn đề | Đã chốt | Lượt |
|---|---|---|---|
| /tool/nap | Bố trí 2 app | 2 app riêng (tool + app web), gom 1 project router: `/tool/*` và `/app/*` + trang chọn app | 1 |
| /tool/nap | List vs form | List-first 3 cột (List · Thông tin · Ảnh); chỉ cột list cuộn, thông tin+ảnh xem trọn | 1 |
| /tool/nap | Chờ nạp vs DB | Card lọc (segmented) "Chờ nạp (VPS) / Trong khóa (DB, lọc theo khóa)" — không tách tab đẩy list xuống | 1 |
| /tool/nap | Trường bắt buộc vs optional | Nhóm BẮT BUỘC (viền đỏ + dấu *) theo cột NOT NULL; optional gom accordion đóng sẵn | 1 |
| /tool/nap | Tên in | Bỏ ô — tự sinh = Họ tên cắt ≤25 giữ dấu (verify DB 99,93%) | 1 |
| /tool/nap | Địa chỉ | Combobox tra DM_DVHC: gõ tên/mã → chọn "mã — địa chỉ", lấy đúng MaDvhc/MaDVQL | 1 |
| /tool/nap | Ảnh | Modal chỉnh riêng (crop 3:4 kéo/zoom + xóa phông + kết quả nền trắng) | 1 |
| /tool/nap | TT_XuLy/TrangThai theo ảnh | Có ảnh→TT_XuLy 03, thiếu ảnh→01; TrangThai=1 không đổi (verify DB) — hiện ở dòng "Tự điền" | 1 |
| /tool/tao-khoa | Form layout | Một trang; tái dùng pattern "Tự điền chip + nhóm BẮT BUỘC (viền đỏ, *) + accordion Thông tin thêm" như /tool/nap | 2 |
| Cấu hình (⚙ header, HTG-07) | Kiểm tra kết nối | Nút "Kiểm tra kết nối" → badge kết quả inline (thành công/lỗi), không popup | 2 |
| Cấu hình (⚙ header, HTG-07) | Dùng chung cả tool + phân biệt DB | **Panel mở từ icon ⚙ góc phải header** (mọi màn), KHÔNG là route riêng, KHÔNG nằm trong sub-nav. Chia **hai khối tách bạch có nhãn rõ**: ① *Kết nối chung + CSDL NGUỒN để Nạp* (Server/User/Pass + `GPLX_CSDT` + VPS + API key) · ② *Các CSDL ĐÍCH để Sync* (danh sách nhiều DB, chọn mặc định, test, tùy chọn). Người dùng nhìn là biết đâu là DB nạp, đâu là các DB đẩy sang — không trộn một danh sách phẳng. Bỏ màn `/tool/cau-hinh` + `/sync/db-dich`. Dựng impeccable/ui-ux-pro-max | (#34) |
| /sync/ban-dong-bo | Làm đẹp combobox + danh sách HV (CHANGES #34) | Combobox năm/khóa + ô chọn DB đích gọn, nhãn rõ (năm · khóa · hạng); **danh sách HV để sync: tên hiển thị hài hòa, đủ dấu, căn cột, mật độ dòng vừa phải, không tràn/cắt chữ**; bám token `tool/webui`; impeccable/ui-ux-pro-max; Playwright 1280/1440/1920 | (#34) |
| /sync/tra-cuu (Tra cứu CDB, TCB) | Màn riêng cho DB đích (CHANGES #35) | **Bản riêng** cho CDB đích — KHÔNG tái dùng màn Tra cứu DB Nạp (tránh vỡ QLY-01); tái dùng component con AnhModal/AnhAvatar/bố cục chi tiết. Lưới avatar + tìm bỏ dấu/CCCD + cờ BC1/DKKH. Dựng thẳng `tool/webui`, impeccable | (#35) |
| /sync/tra-cuu — luật khóa sửa/xóa | Đọc trạng thái Ở ĐÍCH (CHANGES #35) | **Thay ảnh:** cho + cảnh báo (ghi đè file `.jp2` dùng chung 2 DB). **Sửa nhân thân:** chặn nếu khóa đích **đã kết xuất DKKH** (`SoQD_KhaiGiang`). **Xóa/Đổi khóa:** chặn nếu HV **đã BC1** (FK ép); DKKH chưa BC1 → cho + cảnh báo. Mốc đọc độc lập DB Nạp | (#35) |
| /dang-nhap | Bố cục | Card giữa màn (username + password + nút); 3 vai trò theo tài khoản, không SSO | 2 |
| Tool (ToolLayout) | Điều hướng nhiều module | **Sidebar trái** = danh sách module (Nạp hồ sơ · Đồng bộ CDB · dự kiến Kết quả học tập) → bấm module hiện sub-nav + màn của module; mỗi module màu nhấn + banner DB riêng; sidebar thu gọn được (icon ↔ nhãn); đăng ký mảng MODULES (mở rộng N). Nav Nạp cũ → sub-nav module Nạp (hành vi màn không đổi) | (SYNC) |
| Tool (toàn bộ) | Bề rộng · thiết bị | **CHỈ desktop** (không responsive/mobile); nội dung ≥1280px, canh giữa ~1500px; sidebar nhường bề ngang; **bảng nhiều cột cuộn ngang trong vùng bảng**, không co cột cắt chữ/MaDK. Kiểm Playwright 1280/1440/1920 bắt tràn ngang trước khi xong | (SYNC) |
| /sync/ban-dong-bo | Dựng UI | Bám **design system tool thật** (`tool/webui` token/shadcn hiện tại — KHÔNG theo prototype cũ đã lệch); dùng **skill UI** (ui-ux-pro-max/impeccable) khi dựng. Bảng 11 cột: ☑·STT·Họ tên·CCCD·Hạng·MaDK nguồn·NgàyHS nguồn·MaDK đích·NgàyHS đích·Số HS·Trạng thái; HV đã có ở đích nền vàng + khóa tick | (SYNC) |
| /sync/* | Màu nhấn | Module Đồng bộ CDB dùng tông **hổ phách/teal** phân biệt với Nạp (xanh primary), trong khuôn khổ token hiện có; banner cố định nhắc DB đích đang ghi | (SYNC) |
| App web (AppLayout, Quét) | Responsive desktop (PRD ⑥) | Mobile-first giữ nguyên; desktop ≥lg: sidebar trái + nội dung nhiều cột; Đã gửi desktop = table. ⚠️ "Quét = camera trái/form phải" **đã bỏ** — thay bằng desktop vào thẳng form + popover quét (lượt 18, CHANGES #30) | 2 |
| /app/da-gui | Danh sách + chi tiết | Lọc Tất cả/Chờ nạp/Đã nạp; mobile = card list, desktop = table; bấm dòng → modal chi tiết (ảnh thô + thông tin) | 3 |
| /admin/ho-so | Xóa PII | Bảng + checkbox chọn nhiều + lọc trạng thái/khoảng ngày; xóa tay → dialog xác nhận (không khôi phục, BR-016) | 3 |
| /app/tai-khoan | Bố cục | Thẻ người dùng + thông tin tài khoản + Đổi mật khẩu + Đăng xuất | 3 |
| /tool/nap (tab DB) | QLY-01/02/03 | Bấm dòng HV → drawer Xem/Sửa bên phải (chặn sửa nếu BC1, BR-012); trong drawer: Đổi khóa (dialog chọn khóa cùng hạng, BR-013) + Xóa (dialog xác nhận, xóa mềm ảnh, BR-014) | 4 |
| /tool/nap | IA 2 chế độ (CHANGES #6) | Thanh chế độ **Nạp hồ sơ** (dropdown khóa **chỉ chưa BC1**) / **Tra cứu DB** (tìm khóa theo tên/mã **mọi khóa, kể cả BC1** — khóa 🔒 BC1 chỉ xem). Tách vì luật BC1 ngược nhau | 6 |
| /tool/nap (chế độ Nạp) | Trạng thái nạp lô (CHANGES #6) | 1 danh sách hàng chờ, lọc **Cần xử lý** (⚪ chờ + 🔴 lỗi, lỗi lên đầu) / **Đã nạp** (🟢). Nạp lô → dòng đổi realtime; "Đã nạp" là xác nhận tạm, chỗ ở thật là tab Tra cứu DB | 6 |
| /tool/nap | Chuẩn cảnh báo (CHANGES #6) | Inline **nổi bật** (banner nền/viền/icon) + **nêu rõ nguyên nhân**, KHÔNG modal. Trạng thái dùng màu + icon + chữ (phủ mù màu) | 6 |
| /tool/nap · /app/da-gui | Ô tìm kiếm (CHANGES #10) | Tìm theo **tên (khớp cả không dấu)** hoặc **CCCD**. Đặt **đầu danh sách/lưới**: tool list tải về (chế độ Nạp), tool lưới khóa (Tra cứu DB), app web Hồ sơ đã gửi. **Màn hẹp thu gọn thành nút kính lúp** (bấm mới bung ô nhập). App web KHÔNG nằm trong B cũ — chốt lại A (cả 3 chỗ) | 7 |
| /tool/nap (chế độ Nạp) | Kéo lại làm tươi (CHANGES #11) | Bấm "Kéo về từ VPS" lần nữa **cập nhật** hồ sơ còn **chờ nạp** (collector sửa ở app web sau khi đã kéo → nhận bản mới); giữ nguyên bản đã nạp/đã lỗi. Báo số hồ sơ vừa làm tươi | 8 |
| /app/quet | Màn vào + camera (CHANGES #12) | **Không tự mở camera** sau đăng nhập — màn vào cho chọn **Quét QR / Nhập tay / Tải ảnh**; camera chỉ bật khi bấm Quét. **Khung bám theo QR** khi bắt trúng (4 góc `cornerPoints`), không phải khung tĩnh | 9 |
| App web (AppLayout) | Layout mobile dính đáy + header (CHANGES #12) | `100dvh` + khung camera co giãn → **bottom-nav 3 nút + nút hành động chính dính đáy**, không cuộn mới thấy. **Logo header là trang trí** (bỏ dáng nút, tránh nhầm là camera) | 9 |
| /app/da-gui | Ảnh thật + xem/sửa/chụp lại (CHANGES #12) | List & chi tiết hiện **ảnh chân dung thật** (`GET /api/ho-so/:uuid/anh` của mình). Modal chi tiết: hồ sơ **Chờ nạp** → **Sửa thông tin + Chụp/đổi ảnh**; **Đang/Đã nạp** → chỉ xem | 9 |
| /app/quet | Nhập liên tiếp (CHANGES #13) | Màn preview thêm nút **"Lưu & nhập hồ sơ tiếp"** cạnh "Tiếp tục — chụp ảnh" → gửi **không ảnh** → **toast "Đã gửi ✓"** (bỏ màn kết quả) → về màn chọn cách nhập. Áp cho cả quét QR lẫn nhập tay | 10 |
| /app/da-gui | Badge + lọc thiếu ảnh (CHANGES #13) | Hồ sơ chưa ảnh có **badge "Thiếu ảnh"** (list + chi tiết) + **bộ lọc "Thiếu ảnh"** cạnh tab trạng thái để gom chụp bù. Chụp bù qua nút "Thêm ảnh" (Chờ nạp) đã có | 10 |
| /app/quet | Cảnh báo trùng CCCD (CHANGES #13, THU-04) | Khi gửi, nếu CCCD đã có hồ sơ **chưa nạp trong hàng đợi** → **banner cảnh báo mềm** (nêu ai gửi/lúc nào), **vẫn cho gửi**. Soi hàng đợi VPS, không soi DB thật | 10 |
| /app/quet · /app/da-gui | Redesign UX nhập liệu (CHANGES #14, impeccable) | Màn xác nhận: **ẩn ô CMND cũ** (vẫn lưu từ QR); ô ngày **gõ tay dd/mm/yyyy + nút lịch** (giữ năm-only) — component dùng chung; **desktop** tách vị trí 2 nút tránh bấm nhầm + bố cục gọn + **phím tắt** (autofocus, Enter/Ctrl+Enter, tab order) | 11 |
| /app/quet · /app/da-gui | Ảnh: nguồn + phóng to (CHANGES #15) | Màn chụp ảnh & đổi ảnh (Chờ nạp): **2 nút "Chụp ảnh" (camera) / "Chọn từ máy" (file·thư viện)**. Chi tiết hồ sơ: **bấm ảnh → popup phóng to** (AnhLightbox, bấm ngoài đóng) | 12 |
| /tool/nap (tab DB) | Avatar + xem ảnh (CHANGES #22) | Lưới HV thêm **cột avatar** (ảnh thu nhỏ từ DB qua endpoint thumbnail; chưa ảnh → icon người). Modal chi tiết hiện **ảnh lớn + dòng đường dẫn `.jp2`**; **click ảnh → mở trình chỉnh** (đổi nền, QLY-05). File DB có path mà mất file → **cảnh báo "không tìm thấy file ảnh"**. Ảnh `.jp2` phải transcode→PNG (trình duyệt không mở `.jp2`). Wireframe ở Ghi chú | 13 |
| /tool/nap (tab DB) | Thống kê + thao tác nhanh (CHANGES #22) | Đầu khóa hiện **tổng HV · thiếu ảnh · đã BC1**. Nút **đổi khóa/xóa nhanh** ra lưới (xác nhận 2 bước, **chặn BC1**). Tab Nạp (staging): nút **"Bỏ khỏi hàng đợi"** dòng 🟢 (nhẹ, TÁCH BẠCH "Xóa khỏi DB") + **"Nạp lại nhanh"** dòng 🔴 | 13 |
| /tool/nap (tab DB) | Đổi nền cả khóa QLY-07 (CHANGES #22) | Dialog: **phạm vi** (chỉ ảnh chưa trắng [mặc định] / tất cả HV có ảnh) · tùy chọn **sao lưu `_BACKUP`** (mặc định bật) · nút Bắt đầu → **thanh tiến độ N/tổng + số lỗi** (chạy nền, không treo). Giữ `TT_XuLy`. Wireframe ở Ghi chú | 13 |
| /tool/nap (cả 2 tab) | Xem lại/chỉnh tiếp ảnh đã chỉnh (CHANGES #23) | Sau "Dùng ảnh này": khung ảnh hiện **đúng ảnh vừa chỉnh** (bản xem trước PNG, KHÔNG chỉ icon check — vì `.jp2` không render được). Mở trình chỉnh lần sau **nạp sẵn ảnh đã chỉnh gần nhất** để chỉnh tiếp. Nút áp dụng **nổi bật + nhãn rõ** (badge ghi "đã xử lý — bấm để áp dụng") tránh dừng ở bước "Xử lý ảnh" tưởng đã lưu. Lưu ý: ở tab Nạp vẫn là **nháp** cho tới khi bấm "Nạp HV vào khóa" | 14 |
| /tool/nap (tab DB) | Nhãn nút "khóa khác" (CHANGES #23) | Đổi **"Mở khóa khác"** → **"Tạo thêm hồ sơ ở khóa học khác hạng"** (QLY-06, tạo hồ sơ MỚI khác hạng, GIỮ hồ sơ cũ) cho khỏi nhầm là *chuyển* khóa. **Giữ hiển thị cả ở khóa đã BC1** (không đụng báo cáo cũ) — khác nút "Đổi khóa" (QLY-02) đã ẩn khi BC1 | 14 |
| /tool/nap (tab DB) | Gỡ HV về chờ nạp QLY-08 (CHANGES #24) | Nút **RIÊNG "Gỡ về chờ nạp"** cạnh "Xóa" (chỉ khóa chưa BC1, xác nhận 2 bước) — gỡ HV khỏi CSDT **rồi trả về hàng chờ** để nạp lại đúng khóa. TÁCH BẠCH với "Xóa" (bỏ hẳn). Bản ghi VPS đã dọn PII → báo không gỡ được | 15 |
| /app/da-gui | Xóa hồ sơ đã gửi THU-05 (CHANGES #24) | Hồ sơ **Chờ nạp** có nút **Xóa** (xác nhận 2 bước) → soft-delete trên VPS; hồ sơ **đã/đang nạp** ẩn/khóa nút. Collector chỉ xóa của mình, admin bất kỳ. Xóa xong tool kéo về sẽ **đồng bộ bỏ** khỏi hàng chờ | 15 |
| /tool/nap (tab DB) | Avatar 3 trạng thái (lượt 13 dựng) | Có ảnh → vòng tròn màu + user · chưa ảnh → xám + user · **mất file (DB có path, ổ không có) → đỏ + icon ảnh-vỡ + badge "mất ảnh"**. Bấm avatar/ảnh → trình chỉnh (được cả khóa BC1 — chỉ đụng ảnh, giữ TT_XuLy). Thao tác nhanh đổi-khóa/xóa chỉ hiện khi khóa chưa BC1 | 13 |
| /app/da-gui · /tool/nap (tab DB) | Popup cảnh báo bàn giao (CHANGES #26) | Nguyên tắc: **trước nạp app web làm chủ, sau nạp tool làm chủ** (TDD §7.5). THU-05 xóa chờ nạp: panel 2 bước ("chưa nạp nên xóa được, kéo về sẽ mất, không lấy lại"); đã/đang nạp → chú thích "báo người nạp". QLY-08 "Gỡ về chờ nạp": panel cam **tách** "Xóa hẳn" + banner "đồng bộ máy chủ lỗi — Thử lại". QLY-03 "Xóa hẳn": copy tách bạch (bỏ hẳn, nạp lại phải nhập lại ở app) | 16 |
| /app/quet | Desktop ưu tiên nhập tay (CHANGES #30, THU-01) | **Desktop (≥lg) vào thẳng form nhập tay** (con trỏ ở ô Số CCCD), bỏ cổng chọn. **Quét QR / Tải ảnh** thu nhỏ thành nút phụ góc phải tiêu đề; bấm Quét QR mở **popover camera nổi** đè form → quét xong tự điền. "Lưu & nhập tiếp" desktop → form trống. **Mobile giữ camera-first** (cổng chọn + camera toàn màn). Thuần client nhánh `lg:`, không đổi API | 18 |
| /app/da-gui | Desktop chọn-nhiều-để-xóa (CHANGES #30, THU-05) | Bảng desktop thêm **cột ô tích chỉ ở dòng Chờ nạp** (đã/đang nạp không chọn được); ô tích đầu cột = chọn tất cả Chờ nạp trên trang. **Thanh nổi "Đã chọn N · Bỏ chọn · Xóa N"** khi chọn ≥1 → dialog xác nhận (không khôi phục). Tái dùng mẫu xóa-hàng-loạt /admin/ho-so (QuanTriHoSo). **Mobile giữ** xóa lẻ trong modal | 18 |
| /tool/nap (chế độ Nạp) | Nút nạp lên header NAP-01 (CHANGES #29) | Dời **"Chọn tất cả sẵn sàng" + "Nạp N học viên vào khóa"** từ thanh dính đáy **lên header** (hàng shrink-0 ngay dưới tab lọc, trong `h-[calc]` → list tự co, nút luôn thấy). Chỉ hiện ở tab "Cần xử lý" | 18 |
| /tool/nap (Chọn tay địa chỉ) | Combobox gõ-lọc NAP-03 (CHANGES #29) | "Chọn tay" địa chỉ 2 cấp mới: 2 dropdown Tỉnh/Xã → **ô gõ-để-lọc** `ComboLoc` (gõ không dấu cũng khớp nhờ `boDau`, danh sách gợi ý lọc dần, bấm/Enter chọn). Thuần client, `getTinh`/`getXa` sẵn | 18 |
| /tool/nap (AnhModal) | "Dùng lại ảnh gốc" (CHANGES #26) | Nút trong trình chỉnh quay về **ảnh nguyên bản** (bỏ chỉnh sửa, xác nhận nhanh): NAP-04 = ảnh thô VPS, QLY-05 = ảnh `.jp2` DB. Ẩn khi không có nguồn. Đi xa hơn "mở lại nạp ảnh đã chỉnh gần nhất" (CHANGES #23) | 16 |
| /tool/nap (chế độ Nạp) | Redesign Nạp lô (CHANGES #26) | Mỗi dòng badge **sẵn sàng/thiếu gì**; **"Chọn tất cả sẵn sàng"** + thanh **"Nạp N học viên"** dính đáy; **drawer "Chuẩn bị"** thay cột cố định (gọn); **dialog nạp 3 pha** (xác nhận → tiến độ → báo cáo + "Nạp lại lỗi"); nút **"Xem trong DB"**. Wireframe ở Ghi chú | 16 |
| /tool/nap (chế độ Nạp) | 2 chip + nút Xử lý + nháp bền (CHANGES #32) | Mỗi dòng **2 chip riêng** `✓/✗ Địa chỉ 2 cấp` + `✓/✗ Có hình` (mặc định ✗ xám); **cả dòng bấm được** + **nút "Xử lý" to** bên phải (thay icon nhỏ). Nháp chuẩn bị (địa chỉ+ảnh+tick) **lưu bền** nên chip đúng cả sau khi tải lại trang. Nạp **chặn thiếu địa chỉ** / **cảnh báo thiếu ảnh** + lối tắt "Bổ sung ảnh ở Tra cứu DB" | — |
| /tool/nap (AnhModal, QLY-05) | Bổ sung ảnh HV thiếu ảnh (CHANGES #32) | HV chưa ảnh → AnhModal lấy ảnh gốc từ **Chọn file** hoặc **Kéo ảnh VPS** (nếu còn), cùng khung crop + đổi nền rồi nạp. Ảnh VPS hết hạn → chỉ còn Chọn file | — |
| /tool/nap (Tra cứu DB) | Đối soát VPS↔CSDT QLY-09 (CHANGES #28) | **Panel admin/operator** (không collector): chọn **1 khóa** → liệt kê **chỉ dòng lệch** VPS↔CSDT, mỗi dòng nêu loại lệch + **1 nút sửa** tương ứng: ① phantom (VPS đã nạp, DB không có) → "Trả về chờ nạp" · ② DB có, VPS chưa → "Đánh dấu đã nạp" · ③ treo khóa quá lâu → "Mở khóa". Sửa xong làm tươi, dòng khớp biến mất. **Dựng trực tiếp ở tool webui khi code** (màn tool, không qua ui-demo/prototype) | 17 |

## Component dùng chung

| Component | File | Dùng ở màn |
|---|---|---|
| Icon (SVG inline) | src/components/Icon.tsx | Tất cả |
| ToolLayout (title bar + nav) | src/components/ToolLayout.tsx | /tool/* |
| AppLayout (mobile shell + bottom nav) | src/components/AppLayout.tsx | /app/* |
| Placeholder | src/components/Placeholder.tsx | Các màn placeholder |
| AddressCombo (combobox DVHC) | trong src/pages/tool/NapHoSo.tsx | /tool/nap |
| NapBadge / Banner / KhoaCombo (helper nội bộ) | trong src/pages/tool/NapHoSo.tsx | /tool/nap (màn #13) |
| Avatar / AvatarDB (helper nội bộ) | trong src/pages/tool/NapHoSo.tsx | /tool/nap — AvatarDB 3 ca ảnh (màn #14) |
| mock-data / format | src/lib/mock-data.ts, src/lib/format.ts | Nhiều màn |

## Ghi chú

- ✅ **Lượt 5 (01/10/2026) — màn #13 overlay lên `/tool/nap` theo CHANGES #6:** thanh **IA 2 chế độ** (Nạp hồ sơ / Tra cứu DB) thay cho segmented "Chờ nạp/Trong khóa" cũ; chế độ Nạp có filter nạp lô **Cần xử lý (⚪ chờ + 🔴 lỗi, lỗi lên đầu) / Đã nạp (🟢)**, badge trạng thái màu+icon+chữ (phủ mù màu), banner cảnh báo **nổi bật** (viền trái dày + nền + icon) cho lỗi & chính tả mức A; chế độ Tra cứu tìm **mọi khóa kể cả 🔒 BC1** (BC1 → chỉ xem, drawer khóa sửa). Tên hiển thị IN HOA. Không tạo component mới ở file chung — chỉ helper nội bộ NapHoSo (NapBadge/Banner/KhoaCombo) + thêm icon `lock` vào Icon.tsx. Mock thêm `tt/loiLyDo/chinhTa` + `khoaTraCuu`.
- ✅ **App web đã có bản desktop (PRD ⑥) — làm 30/09/2026:** `AppLayout` responsive — mobile (< lg) giữ nguyên app điện thoại (header + bottom-nav, max-w-440); desktop (≥ lg) hiện **sidebar trái** (nav dọc + user) + nội dung rộng. `Quét` desktop thành **2 cột** (camera trái · form phải). Màn `Đã gửi` khi build sẽ làm **table** trên desktop (card list trên mobile).
- **Component mới lượt 2:** không tạo component mới — tái dùng `Icon`, `ToolLayout`, `.field-input`, pattern "Tự điền + BẮT BUỘC + accordion". Thêm `dmHangDT` vào `mock-data.ts`.
- **Chưa logic thật:** không API/DB/auth/validation. Nút bấm được, chuyển route được. Dữ liệu ở `src/lib/mock-data.ts` (tên/khóa/địa chỉ lấy từ PRD + DB thật).
- **Dữ liệu địa chỉ combobox** là mẫu; thật sẽ nối `usp_DM_DVHC_SelectAll_Tinh` / `usp_DM_DVHC_SelectDanhSachXaPhuongTheoTinh`.
- **QLY-02/03** (đổi khóa, xóa HV) là thao tác trong tab "Trong khóa (DB)" của /tool/nap — chưa dựng tương tác, sẽ thêm ở lượt sau.
- **HTG-02** là backend VPS (hàng đợi + job xóa PII) — không có UI, không dựng màn.
- PRD chưa gắn mã bằng `/ganma`? — PRD đã có mã story (THU/NAP/QLY/KHO/HTG), dùng luôn ở cột Mã story.

## Wireframe CHANGES #22 (cách làm — `/prototype-next` bám theo)

**① Lưới HV có avatar (tab Tra cứu DB) + thống kê + thao tác nhanh**
```
Khóa B-K149 · hạng B · 98 HV · thiếu ảnh 12 · 🔒 đã BC1   [Tìm] [Tất cả][Chưa ảnh][Đã có ảnh]
[Đổi nền trắng cả khóa ⚙]
┌─────┬────────────────────┬──────┬───────────┬─────────────┬───────┐
│ Ảnh │ Họ và tên          │ G.T  │ Ngày sinh │ Số CCCD     │ Số HS │
├─────┼────────────────────┼──────┼───────────┼─────────────┼───────┤
│ [▣] │ NGUYỄN VĂN AN      │ Nam  │ 01/02/1990│ 0360…1234   │ 010   │  ▣=ảnh thu nhỏ (click→chỉnh)
│ [☺] │ TRẦN THỊ BÌNH      │ Nữ   │ 03/04/1992│ 0360…5678   │ 011   │  ☺=icon người (chưa ảnh)
└─────┴────────────────────┴──────┴───────────┴─────────────┴───────┘
  click dòng → modal chi tiết ② · click avatar [▣] → trình chỉnh ảnh
```

**② Modal chi tiết có ảnh + đường dẫn (click ảnh để sửa)**
```
┌─ Chi tiết học viên ─────────────────────── [x] ┐
│ ┌────────┐  NGUYỄN VĂN AN                      │
│ │ ẢNH    │  Số hồ sơ 010 · Nam                 │
│ │ 3:4    │  Số CCCD   0360…1234                │
│ │(click  │  Ngày sinh 01/02/1990               │
│ │ để sửa)│  Ảnh       Đã có                     │
│ └────────┘                                     │
│ Đường dẫn: D:\GPLXCSDT\…\70004K26B010.jp2 [⎘]  │
│ ⚠ File ảnh không có trên ổ (khi path có, file mất) │
│ [Đóng] [Thay ảnh] [Mở khóa khác]  [Xóa*][Đổi khóa*][Sửa*] │  *ẩn/chặn khi khóa BC1
└──────────────────────────────────────────────────┘
```

**③ Đổi nền trắng cả khóa (chạy nền + tiến độ)**
```
┌─ Đổi nền trắng — khóa B-K149 ─────────────── [x] ┐
│ Phạm vi: (•) Chỉ ảnh CHƯA nền trắng  ( ) Tất cả (98) │
│ Sao lưu: [✓] Lưu ảnh gốc vào _BACKUP trước khi ghi   │
│ ⚠ ~1-3 giây/ảnh · ghi đè ảnh · giữ TT_XuLy (BC an toàn) │
│ [Hủy]                    [Bắt đầu đổi nền 98 ảnh]    │
│ ───────────────────────────────────────────────    │
│ Đang xử lý ▓▓▓▓▓▓▓░░░░░ 42/98 (✓39 ✎1 ✗3)  [xem lỗi]│
└──────────────────────────────────────────────────────┘
```

## Wireframe CHANGES #26 (redesign Nạp lô — `/prototype-next` / code bám theo)

**① Màn Nạp lô — trạng thái sẵn sàng + chọn nhiều + thanh hành động dính đáy**
```
Nạp vào khóa: ▸ B-K150 · Mô tô A1 · chưa Báo cáo 1 ▼    [↻ Kéo về từ VPS]
┌ Cần xử lý (14) ┐  Đã nạp (8)                       🔍 Tìm tên / CCCD
☑ Chọn tất cả sẵn sàng (9)              Lọc ▾ Tất cả · Còn thiếu
┌────────────────────────────────────────────────────────────────┐
│ ☑  NGUYỄN VĂN A   079…   ✔ Sẵn sàng            [ Chuẩn bị ▸ ]   │
│ ☐  LÊ VĂN C       080…   ⚠ Thiếu địa chỉ        [ Chuẩn bị ▸ ]   │ ← chưa đủ: không tick được
│ ☐  🔴 PHẠM VĂN D  081…   Lỗi: trùng CCCD khóa    [ Nạp lại ]     │
└────────────────────────────────────────────────────────────────┘
┌ Đã chọn 9 học viên sẵn sàng ───────────── [ Nạp 9 học viên → ] ┐ ← dính đáy, 1 nút chính
```

**② Ngăn "Chuẩn bị 1 HV" (drawer trượt từ phải, thay cột cố định)**
```
                       ┌─ Chuẩn bị: LÊ VĂN C ───────────── [x] ┐
                       │ 080… · Mô tô A1                        │
                       │ Địa chỉ thường trú      ⚠ cần chọn     │ (AddressCombo)
                       │ [ Tỉnh / Xã … ▼ ]  [ Chi tiết … ]     │
                       │ Giấy tờ   ☑ CCCD  ☑ Giấy KSK  ☐ …     │
                       │ Ảnh   [ khung ] [Chỉnh ảnh][Dùng lại ảnh gốc]│ (AnhModal)
                       │              [ Lưu & đánh dấu sẵn sàng ]│ → dòng thành ✔ + tự tick
                       └────────────────────────────────────────┘
```

**③ Dialog nạp 3 pha (reuse pattern DoiNenDialog)**
```
Pha 1 · Xác nhận          Pha 2 · Đang nạp           Pha 3 · Báo cáo
┌ Nạp 9 học viên ─────┐  ┌ Đang nạp… ──────────┐  ┌ Nạp xong ──────────────┐
│ Vào khóa B-K150      │  │ ▓▓▓▓▓▓░░  6/9        │  │ ✔ 7 vào DB              │
│ (Mô tô A1, chưa BC1) │  │ Đang nạp: TRẦN THỊ B │  │ 🔴 2 chưa nạp được      │
│ 9 sẵn sàng, 5 thiếu  │  │ (lỗi 1 HV không hỏng │  │  · PHẠM D — trùng CCCD  │
│ sẽ bỏ qua.           │  │  cả lô)              │  │  · VÕ E — thiếu giấy tờ │
│ [Hủy] [Bắt đầu nạp]  │  │ (không đóng khi chạy)│  │ [Nạp lại lỗi]           │
└──────────────────────┘  └──────────────────────┘  │ [Xem trong DB] [Xong]   │
                                                     └─────────────────────────┘
```
"Xem trong DB" → sang chế độ Tra cứu DB, mở đúng khóa đích + làm nổi HV vừa nạp.

## Quyết định UX — Phân công GV – xe (10/10/2026, user chốt qua mock `ui-mock/phancong.html`)
- **Khung chọn nhỏ, khung phân giờ to:** danh sách GV/xe gọn (hàng 1–2 dòng, xe dạng chip); vùng làm việc chính là chỗ nhập thời gian; cảnh báo chữ ≥13px, dải màu bên trái, ngay dưới ô sai, kèm băng tóm tắt đầu bước và cột "Kiểm tra khóa" bấm nhảy tới dòng.
- **Môn "Thực hành lái xe" nổi bật** (nhiều GV dạy): ô lớn hồng ở đầu khung nhập, 1 bấm chọn môn + điền ngày; chip môn này tô màu riêng.
- **Thời gian:** "Theo ngày" (00:00→00:00) mặc định; ô tích "Chỉnh giờ" mới hiện giờ (danh sách chọn bước 30 phút + 3 nút tắt sáng/chiều/cả ngày); ngày bắt đầu thực hành của khóa để trống, tự nhập.
- **Hàng loạt:** tích chọn nhiều GV → thêm / phân công / dời ngày kết thúc / gỡ, luôn xem trước từng GV, GV lỗi bị bỏ qua kèm lý do; ghép xe chỉ "Gợi ý" duyệt từng dòng.
- **An toàn:** bản nháp, "Ghi vào CDB" khóa khi còn lỗi chặn, hộp xem lại + tích CSDL thật + tích cảnh báo; thao tác phá (gỡ GV/xe, xóa phân công TH cuối) liệt kê hậu quả cụ thể.
- **Hướng dẫn từng bước** ngay trên giao diện (mở khi bước chưa có dữ liệu, tự thu gọn khi đã có).
