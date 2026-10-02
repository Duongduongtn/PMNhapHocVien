# Tiến độ màn hình — ui-demo

> File do `/prototype` sinh, `/prototype-next` cập nhật mỗi lượt.

- **PRD nguồn:** docs/PRD.md
- **Bản HTML chuẩn:** ui-demo-options/detailed.html
- **Stack:** Vite + React + TypeScript + Tailwind v3 (token shadcn) + react-router-dom · font Be Vietnam Pro
- **Cổng dev:** 3021 (sổ `~/.claude/local-ports.md`)
- **Cập nhật lần cuối:** 02/10/2026 (CHANGES #22 — mở rộng quản lý ảnh Tra cứu DB: avatar lưới + xem ảnh/đường dẫn + click sửa ảnh + thống kê + QLY-07 đổi nền cả khóa. **Chỉ chốt thiết kế/wireframe, chưa dựng prototype** — `/prototype-next` dựng sau. Lượt 12 trước đó: ảnh app web CHANGES #15)

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
| 4 | Cấu hình kết nối | HTG-01 | `/tool/cau-hinh` | ✅ Xong | 2 |
| 5 | Tạo khóa học | KHO-01 | `/tool/tao-khoa` | ✅ Xong | 2 |
| 6 | Hồ sơ tôi đã gửi | THU-02 | `/app/da-gui` | ✅ Xong | 3 |
| 7 | Tài khoản (app web) | HTG-01 | `/app/tai-khoan` | ✅ Xong | 3 |
| 8 | Lọc & xóa PII (quản trị VPS) | HTG-03 | `/admin/ho-so` | ✅ Xong | 3 |
| 9 | Tra cứu & sửa hồ sơ đã có | QLY-01 | `/tool/nap` (tab DB → drawer Xem/Sửa) | ✅ Xong | 4 |
| 10 | Đổi khóa + di chuyển ảnh | QLY-02 | `/tool/nap` (drawer → dialog Đổi khóa) | ✅ Xong | 4 |
| 11 | Xóa học viên + xóa mềm ảnh | QLY-03 | `/tool/nap` (drawer → dialog Xóa) | ✅ Xong | 4 |
| 12 | Nạp/thay ảnh cho HV đã có (+ click avatar/ảnh ở Tra cứu DB mở trình chỉnh — CHANGES #22) | QLY-05 | `/tool/nap` (lọc tình trạng ảnh + drawer → dialog Nạp/thay ảnh) | ⬜ Chưa có route | — |
| 13 | Nạp lô + IA 2 chế độ (hàng chờ VPS badge ⚪🔴🟢) | NAP-01 | `/tool/nap` (chế độ Nạp hồ sơ / Tra cứu DB) | ✅ Xong (+⬜ "Bỏ khỏi hàng đợi" & "Nạp lại nhanh" CHANGES #22) | 5 |
| 14 | Tra cứu DB: avatar lưới + xem ảnh/đường dẫn + thống kê đầu khóa + thao tác nhanh | QLY-01 | `/tool/nap` (tab DB) | ⬜ Chưa dựng (CHANGES #22) | — |
| 15 | Đổi nền trắng cả khóa (phạm vi + sao lưu + thanh tiến độ) | QLY-07 | `/tool/nap` (tab DB → dialog) | ⬜ Chưa dựng (CHANGES #22) | — |
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
| /tool/tao-khoa, /tool/cau-hinh | Form layout | Một trang; tái dùng pattern "Tự điền chip + nhóm BẮT BUỘC (viền đỏ, *) + accordion Thông tin thêm" như /tool/nap | 2 |
| /tool/cau-hinh | Kiểm tra kết nối | Nút "Kiểm tra kết nối" → badge kết quả inline (thành công/lỗi), không popup | 2 |
| /dang-nhap | Bố cục | Card giữa màn (username + password + nút); 3 vai trò theo tài khoản, không SSO | 2 |
| App web (AppLayout, Quét) | Responsive desktop (PRD ⑥) | Mobile-first giữ nguyên; desktop ≥lg: sidebar trái + nội dung nhiều cột (Quét = camera trái/form phải); Đã gửi desktop = table | 2 |
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

## Component dùng chung

| Component | File | Dùng ở màn |
|---|---|---|
| Icon (SVG inline) | src/components/Icon.tsx | Tất cả |
| ToolLayout (title bar + nav) | src/components/ToolLayout.tsx | /tool/* |
| AppLayout (mobile shell + bottom nav) | src/components/AppLayout.tsx | /app/* |
| Placeholder | src/components/Placeholder.tsx | Các màn placeholder |
| AddressCombo (combobox DVHC) | trong src/pages/tool/NapHoSo.tsx | /tool/nap |
| NapBadge / Banner / KhoaCombo (helper nội bộ) | trong src/pages/tool/NapHoSo.tsx | /tool/nap (màn #13) |
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
