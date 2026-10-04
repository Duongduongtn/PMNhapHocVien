# Kế hoạch build — PMCSĐTLX Thu nhận hồ sơ học viên

> File do `/kehoach` sinh. `/tieptheo` đọc file này để biết làm gì tiếp theo.
> **Thứ tự code** nằm ở đây. **Yêu cầu và trạng thái story** nằm ở `docs/PRD.md`.
> Cập nhật lần cuối: 04/10/2026 (v10 — bổ sung task 50-53 theo CHANGES #32: NAP-01 lưu nháp BỀN + 2 chip + nạp chặn/cảnh báo · QLY-05 bổ sung ảnh 2 nguồn)

## Quyết định về thứ tự

- **Risk-first (theo TDD §17):** làm **Tool nạp DB trước** vì đây là mắt xích khó & rủi ro cao nhất — sinh `SoHoSo` qua `sp_getapplock`, gọi **1 SP gộp app cũ** `usp_QuangLA_...ThemMoiCapNhat`, ghi ảnh hướng A riêng (UPDATE 5 cột), xuất `.jp2` khớp app cũ. Hỏng chỗ này ở cuối dự án = làm lại từ đầu; nên chứng minh sớm bằng **nạp tay 1 HV** (AS-003) rồi mới dựng đường thu thập. *(01/10 — đổi 3 SP rời → 1 SP gộp, bỏ compensation vì SP atomic; xem CHANGES #4/#5.)*
- **Đảo ưu tiên có chủ đích (Luật 2 > Luật 3):** vài story **MUST** (`KHO-01`, `HTG-03`) nằm ở Phase 3 vì độc lập, rủi ro thấp, không nằm trên đường chứng minh lõi (DB đã có khóa thật + hồ sơ thật để test NAP). SHOULD `QLY-*` cũng Phase 3 vì phụ thuộc `NAP-05`.
- **`HTG-01` cắt 3 task theo nơi chạy:** ① cấu hình kết nối tool (local, Phase 1) · ② auth JWT trên VPS (Phase 2) · ③ login UI + tool gate (Phase 2). PRD chỉ chuyển ✅ khi xong cả 3.
- **`NAP-05` và `HTG-02` cắt đôi** để không còn task cỡ L.
- **1 người build → tuần tự một luồng**, không tách nhánh song song (quyết định chủ dự án 01/10/2026).
- **#24/#26 (task 41-47) — lần đầu sửa server VPS từ Phase 2:** task 41/42/44 đổi server đang chạy prod → phải **deploy lại VPS** + verify 3 vai trò/luồng gửi-kéo ngay sau (Checkpoint 8). Thứ tự trong cụm: 41 (THU-05, tạo `deleted` — nền cho 44) → 42 (server QLY-08) → 43 (tool QLY-08, dep 42) → 44 (đồng bộ xóa, dep 41). Task 45-47 thuần client (ảnh gốc + redesign Nạp lô), code sau, chạy skill `impeccable` lúc dựng UI.

## Cây phụ thuộc

```
[Nền móng] git init + .gitignore + quét PII
    │
    ├── Khung TOOL (FastAPI localhost + webui React + ToolLayout)
    │     └── HTG-01① Cấu hình kết nối SQL Server (/local/config + test)
    │           ├── db: DM_DVHC_MAP + seed ──── NAP-03 Map địa chỉ
    │           ├── NAP-02 Khóa mô tô/ô tô chưa BC1
    │           ├── NAP-04 Ảnh 3:4 + rembg + .jp2
    │           └── NAP-05 SoHoSo + 1 SP gộp (hướng A) + giấy tờ  ◀ mắt xích khó nhất (AS-003)
    │                 ├── NAP-06 Trùng CCCD trong khóa
    │                 ├── KHO-01 Tạo khóa
    │                 └── QLY-01/02/03 Quản lý HV
    │                       └── QLY-05 Nạp/thay ảnh HV đã có (dùng lại hàm ghi ảnh hướng A)
    │
    └── Khung SERVER VPS (FastAPI + PostgreSQL + docker-compose)
          └── HTG-01② Auth JWT + 3 vai trò + seed admin
                ├── HTG-02 Hàng đợi + lock + upload ảnh + job xóa PII 30 ngày
                │     ├── NAP-01 Tool kéo hàng đợi (thay nhập tay)
                │     └── HTG-03 Admin lọc + xóa PII
                └── Khung WEBAPP PWA (React+Vite + AppLayout)
                      ├── HTG-01③ Login UI (webapp + tool gate)
                      ├── THU-01 Quét QR + preview  ◀ AS-001
                      └── THU-02 Nhập tay + ảnh + gửi VPS
```

## Prerequisite (chủ dự án/ops làm trước khi tới task liên quan)

- **Tạo SQL login riêng cho tool** (không dùng `sa`) trên máy DB `DESKTOP-UBV2GQI` — cần trước **task 4**. Hiện mới có `sa` (chỉ dùng đọc-kiểm READ ONLY).
- **AS-001** quét thẻ CCCD thật của cơ sở — kiểm ở Checkpoint 4.
- **AS-003** nạp thử 1 HV → mở app cũ đối chiếu — kiểm ở Checkpoint 2.

## Phase 1 — Tool nạp được 1 HV khớp app cũ *(de-risk mắt xích khó nhất)*

| # | Task | Story | Quy mô | Phụ thuộc | Kiểm | Xong |
|---|---|---|---|---|---|---|
| 1 | git init + `.gitignore` (chặn `DBcu/`, `UI.png`, `anh-kiem/`) + quét PII | — | S | — | 1 | [x] |
| 2 | GitHub backup: `git remote add origin https://github.com/duongnamdata/PMNhapHocVien` + push (SAU khi `.gitignore` chặn PII) | — | S | 1 | 1 | [x] |
| 3 | Khung tool (FastAPI localhost + webui React + ToolLayout + lib + `.env.example`) | — | S | 1 | 1 | [x] |
| 4 | Cấu hình kết nối SQL Server + nút test + mã hóa config cục bộ | `HTG-01①` | M | 3 | 1 | [x] |
| 5 | Builder dựng `DM_DVHC_MAP` vào **SQLite cục bộ** (dataset đóng kèm + đọc `DM_DVHC`) + đối soát 3321/3321 xã | — | M | 4 | 1 | [x] |
| 6 | Chọn mô tô/ô tô + dropdown khóa chưa lập BC1 + suy `MaLoaiHs`/hạng | `NAP-02` | M | 4 | 1 | → PRD |
| 7 | Map địa chỉ cũ→mới (`DM_DVHC_MAP`) + popup chọn tay Tỉnh/Xã | `NAP-03` | M | 5 | 1+2 | → PRD |
| 8 | Căn ảnh 3:4 grab/zoom + rembg nền trắng + xuất `.jp2` 353×471 | `NAP-04` | M | 4 | 1+2 | → PRD |
| 9 | SoHoSo (`sp_getapplock`) + **1 SP gộp `usp_QuangLA_...ThemMoiCapNhat`** (`@p_MaDK=NULL`→SP sinh, đọc `@p_out`, `SET XACT_ABORT ON`) + ghi `.jp2` + **UPDATE 5 cột ảnh (hướng A)** + tách họ tên để kiểm độ dài. **Bỏ compensation 3 bước** (SP atomic) | `NAP-05 (1/2)` | M | 6,7,8 | 1+2 | [x] AS-003 17/17 (01/10) |
| 10 | Giấy tờ theo tick cuối qua **`@p_GiayTo`** của SP gộp (SP tự insert từ `DM_GiayTo`) + nạp lô nhiều HV + tiến độ + báo dòng lỗi + route `/local/nap` + form nhập tay 1 HV (ô Chi tiết địa chỉ riêng) + chống trùng UUID. **Tái dùng từ `843819a`:** form, checklist, `sinh_so_ho_so`, `tach_ho_ten` | `NAP-05 (2/2)` | M | 9 | 1+2 | [x] Playwright 3vp OK (01/10) |
| 11 | Kiểm trùng CCCD trong cùng khóa (BR-005) — kiểm sớm `GET /local/kiem-trung-cccd` + SP `@p_out=-2` | `NAP-06` | S | 9 | 1 | → PRD |

### ✅ Checkpoint 1 — sau task 4-5
- [ ] Tool nối được SQL Server thật bằng login riêng; đọc `IMG_PATH_CSDT`/`MA_CSDT` từ `QTHT_ThamSoHT`.
- [x] Bảng `DM_DVHC_MAP` (SQLite cục bộ) đối soát đủ 3321/3321 xã về `DM_DVHC` (TrangThai=1). ✅ 01/10/2026 — 10.602 dòng ánh xạ, 0 xã thiếu phủ. Production KHÔNG bị ghi.

### ✅ Checkpoint 2 — sau task 9-11 — **cổng AS-003** ✅ ĐÓNG 01/10/2026
- [x] `pnpm build` (webui) + tool chạy sạch.
- [x] Nạp tay 1 HV → mở **app cũ** đúng khóa: khớp (SoHoSo, họ tên IN HOA, địa chỉ, ảnh, giấy tờ) — AS-003 17/17, user đã đối chiếu.
- [x] **Kiểm mức 2** (unit): 45 test `test_nap.py` pass — SoHoSo, tách họ tên IN HOA, dựng tham số SP gộp, chuỗi giấy tờ, `@p_out` (-1/-2), ghi ảnh hướng A, trùng CMT server-side, idempotent, nạp lô.
- [x] **Kiểm mức 3** (E2E live): 5/5 `test_nap_live.py` pass — nạp có/không ảnh, bỏ tick giấy KSK, trùng CMT cùng khóa (chặn) + khác khóa (cho phép); chạy `pytest -m live`, tự dọn, production về 55 HV.

## Phase 2 — Thu thập đầu-cuối qua VPS

| # | Task | Story | Quy mô | Phụ thuộc | Kiểm | Xong |
|---|---|---|---|---|---|---|
| 12 | Khung server VPS (FastAPI + PostgreSQL + `docker-compose` api+postgres+nginx + `.env.example`) | — | M | 1 | 1 | [x] 01/10 — pytest 3/3, uvicorn health/ready OK, compose config hợp lệ |
| 13 | Khung webapp PWA (Vite + Tailwind token + font phủ tiếng Việt + AppLayout mobile+desktop) | — | S | 1 | 1 | [x] 01/10 — build OK (tsc+vite+PWA sw), Playwright 375/800/1440 shell OK |
| 14 | Auth JWT + 3 vai trò (collector/operator/admin) + seed admin + quản user + chặn 403 | `HTG-01②` | M | 12 | 1+2 | [x] 01/10 — 16/16 test pass, review-nghiepvu ② đủ (HTG-01 giữ 🔄, còn ③ task 17) |
| 15 | Hàng đợi `ho_so_thu_thap` + state machine + lock CAS (importing) + idempotent UUID + upload ảnh thô + validate ảnh | `HTG-02 (1/2)` | M | 14 | 1+2 | [x] 01/10 — 43/43 test pass (SQLite in-memory), 8 endpoint + lock CAS + validate ảnh; review-nghiepvu đủ (sửa 201/200 theo §4.7) |
| 16 | Job APScheduler xóa PII 30 ngày (bỏ qua bản `importing`) | `HTG-02 (2/2)` | S | 15 | 1+2 | [x] 01/10 — 7 test pass (mốc 30 ngày, bỏ qua importing EC-040, xóa kèm ảnh, ghi audit); scheduler mỗi giờ, bật qua enable_scheduler |
| 17 | Login UI webapp + tool login gate (wire token operator cho `/local/*`) | `HTG-01③` | M | 13,14 | 1 | [x] 01/10 — webapp guard login + tool session cục bộ (option A, VPS auth); /local/config miễn token (A1); build webapp+webui OK, tool test 47 pass, Playwright 2 màn login 4vp OK. Đóng HTG-01 ✅ |
| 18 | Quét QR CCCD (BarcodeDetector→ZXing) + auto-capture + hiệu ứng + preview sửa (parse 6/7 trường) | `THU-01` | M | 17 | 1+2 | [x] 01/10 — mức 1: build OK, parse thử 7 ca thật (năm-only→yyyy0000), Playwright 4vp 0 tràn/0 lỗi; review-nghiepvu đủ 5 Done + 4 edge. **Mức 2 (unit parse) để /kiemthu Checkpoint 4** |
| 19 | Nhập tay + chụp ảnh chân dung + gửi VPS (`POST /api/ho-so` idempotent) + DS đã gửi | `THU-02` | M | 17,15 | 1 | [x] 01/10 — build OK, luồng gửi + offline retry + DS đã gửi; Playwright 4vp 0 tràn; review-nghiepvu đủ Done + edge (cư trú bỏ theo CHANGES #9). + ô tìm tên(không dấu)/CCCD mobile kính lúp (CHANGES #10). Ngày cấp ISO→yyyymmdd đổi ở NAP-01 (task 20) |
| 20 | Tool kéo hàng đợi VPS→staging SQLite (chuyển nhập tay→kéo) + **IA 2 chế độ Nạp/Tra cứu** trên `/tool/nap` (chế độ Nạp: dropdown khóa **chỉ chưa BC1**); tên **IN HOA** + **check chính tả mức A** (thiếu dấu / ký tự lạ / khoảng trắng thừa — không từ điển tên) khi kéo về; hàng chờ nạp lô badge **Cần xử lý** (⚪ chờ + 🔴 lỗi, lỗi lên đầu) / **Đã nạp** (🟢), lô chạy hết, dòng lỗi đỏ + lý do; cảnh báo inline nổi bật (NFR⑥). Xem CHANGES #6 | `NAP-01` | M | 15,9 | 1 | [x] 01/10 — ① backend (kéo→staging+nạp lô, +2 vá server) + ② UI 2 chế độ + kéo lại làm tươi (CHANGES #11). tool 72+server 56 test · Playwright 3vp · review-nghiepvu 9/9 |
| 28 | **Rework UX app web** (sau test điện thoại, CHANGES #12): màn vào chọn Quét/Nhập tay/Tải ảnh (camera chỉ bật khi bấm Quét) + khung bám QR (`cornerPoints`) + layout mobile `100dvh` dính đáy + header logo không nút. `webapp/Quet.tsx` + `AppLayout.tsx` | `THU-01` | M | 18 | 1 | [x] 01/10 — màn vào + khung bám QR + layout dính đáy + header. Playwright 3vp (0 tràn, nav dính đáy) · review-nghiepvu 6/6 |
| 29 | **Rework UX app web** (CHANGES #12): endpoint `GET /api/ho-so/:uuid/anh` (collector, `created_by`) + ảnh thật list/chi tiết + modal Sửa/Chụp lại khi chờ nạp (chỉ xem khi importing/imported). `server/ho_so.py` + `webapp/DaGui.tsx` + `api.ts` | `THU-02` | M | 19,15 | 1+2 | [x] 01/10 — endpoint ảnh collector + ảnh thật list/table/chi tiết + modal Sửa/Đổi ảnh + nút "có bản mới". server 62 test · Playwright 3vp · review-nghiepvu 6/6 |
| 30 | **Nhập liên tiếp app web** (CHANGES #13): nút "Lưu & nhập hồ sơ tiếp" ở màn Preview (gửi không ảnh→toast→về màn chọn cách nhập, cả quét QR lẫn nhập tay) + badge "Thiếu ảnh" + tab lọc "Thiếu ảnh" ở Hồ sơ đã gửi. `webapp/Quet.tsx` + `DaGui.tsx` | `THU-01`, `THU-02` | S | 28,29 | 1 | [x] 01/10 — code + typecheck + build + webapp 20 test; deploy live 3db0146, verify trực quan (Preview 2 nút + tab lọc). Mức 1 giao diện mobile đang review |
| 31 | **Cảnh báo trùng CCCD app web** (CHANGES #13, THU-04): `GET /api/ho-so/kiem-trung` (collector, soi hàng đợi pending/importing) + banner cảnh báo mềm ở Preview, vẫn cho gửi. `server/ho_so.py` + `webapp/Quet.tsx` + `api.ts` | `THU-04` | S | 15,18 | 1+2 | [x] 01/10 — endpoint + banner; server 67 test (+5 kiem-trung). Đang review-baomat (lộ tên người gửi chéo) |

### ✅ Checkpoint 3 — sau task 14-17
- [x] Đăng nhập 3 vai trò + collector chặn 403 — **mức 2** (01/10): server `test_auth`/`test_nap` (collector 403 ở `/api/nap/*`), tool `test_auth_tool` (3 vai trò + collector 403 + session). E2E trình duyệt live để kiểm thủ công lúc go-live (plan không đánh task 1+3).
- [x] Job xóa PII >30 ngày, không đụng `importing` — **mức 2** (01/10): `test_pii` 7 case (mốc 30 ngày, bỏ qua importing EC-040, xóa kèm ảnh, ghi audit).

### ✅ Checkpoint 4 — sau task 18-20 — **cổng AS-001**
- [ ] Quét **thẻ CCCD thật** của cơ sở → parse đúng 6/7 trường. *(AS-001 — kiểm TAY, cần thẻ thật, §14.3)*
- [x] **Kiểm mức 2** (unit) 01/10: webapp `qr.test.ts` 20 test (parse 6/7 trường, năm-only→yyyy0000, EC-030 độ dài tên) + tool/webui `format.test.ts` 15 test (boDau/nghiSaiChinhTa/ymdToVN, +fix tên dân tộc). Dựng vitest cho cả 2 app.
- [⚠️] **Kiểm mức 3** 01/10: toàn tuyến VPS tự động `server/tests/test_toantuyen.py` 3 test (gửi+ảnh→kéo→sửa→kéo lại→lock→da-nap→imported; idempotent; collector 403). Nạp DB→khớp app cũ: live `test_nap_live.py` (Checkpoint 2) + **AS-003 kiểm TAY**. Browser quét thẻ thật: **AS-001 kiểm TAY**.

## Phase 3 — Quản lý hồ sơ + quản trị PII + đóng gói

| # | Task | Story | Quy mô | Phụ thuộc | Kiểm | Xong |
|---|---|---|---|---|---|---|
| 21 | Tạo khóa học (`usp_KhoaHoc_Insert`, mã tự sinh, 5 trường bắt buộc) | `KHO-01` | M | 4 | 1 | → PRD |
| 22 | Tra cứu & sửa hồ sơ đã có — **chế độ "Tra cứu DB"** (tab cùng màn `/tool/nap`): tìm khóa theo **tên/mã, mọi khóa kể cả 🔒 BC1** (khóa BC1 chỉ xem); grid theo khóa + search + edit qua SP, chặn sửa nếu BC1. Xem CHANGES #6 | `QLY-01` | M | 9 | 1 | → PRD |
| 23 | Đổi khóa cùng hạng + di chuyển file `.jp2` + cập nhật `DuongDanAnh` | `QLY-02` | M | 22 | 1+2 | → PRD |
| 24 | Xóa HV (`usp_NguoiLX_Delete` cascade) + xóa mềm ảnh sang `_DELETED` + log | `QLY-03` | S | 22 | 1 | → PRD |
| 25 | Admin lọc bản ghi (trạng thái/ngày) + xóa PII thủ công (bản ghi + ảnh thô) | `HTG-03` | M | 15 | 1 | → PRD |
| 27 | Nạp/thay ảnh cho HV đã có: lọc tình trạng ảnh (`TT_XuLy` 01/03) + **dùng lại hàm ghi ảnh hướng A** (ghi `.jp2` + UPDATE 5 cột) của NAP-05; ghi đè nếu HV đã có ảnh | `QLY-05` | M | 9,22 | 1 | → PRD |
| 32 | Mở hồ sơ khóa khác cho HV đã có (cấp mới khác hạng, song song): từ Tra cứu DB chọn HV → điền sẵn từ bản ghi cũ → nạp mới qua SP gộp vào khóa đích (MaDK mới, chung SoCMT). Đã kiểm DB chốt thiết kế (CHANGES #16). KHÔNG nâng hạng | `QLY-06` | M | 22,9 | 1 | → PRD |
| 33 | 🐛 **Vá `ghi_anh_update` giữ `TT_XuLy`** (whitelist `'01'/'02'`, KHÔNG BAO GIỜ HẠ) + ghi ảnh **atomic** (temp→`os.replace`). ƯU TIÊN — bug prod, dùng chung NAP-05 nên cẩn thận (CHANGES #22, TDD §11.5) | `QLY-05` | S | 27 | 1+2 | [x] 02/10 — giữ TT_XuLy + atomic; 123 test (2 hồi quy) |
| 34 | Backend phục vụ ảnh: `GET /local/ho-so/anh` (.jp2→PNG; file mất→404, hỏng→422) + `GET /local/ho-so/anh-thumb` (thumbnail + cache cục bộ `.gitignore`) + kiểm file tồn tại (TDD §11.1) | `QLY-01` | M | 22 | 1+2 | [x] 02/10 — image.jp2_sang_png/thumb_jp2 + 2 endpoint (404/422), 125 test |
| 35 | UI Tra cứu DB: modal chi tiết **ảnh + đường dẫn + cảnh báo file mất** · **avatar** mỗi dòng lazy-load (3 ca: người/ảnh/ảnh-vỡ) · click ảnh → `AnhModal` (fallback chọn-file khi 404) → lưu đè qua `nap-anh` | `QLY-01`,`QLY-05` | M | 33,34 | 1 | [x] 02/10 — avatar lazy 3-ca + modal ảnh lớn+đường dẫn+cảnh báo 404/422 + click→AnhModal(seed/blank); 125 pytest·29 vitest·build; review-nghiepvu 3/3; ảnh thật chờ verify máy CSDT |
| 36 | Thống kê đầu khóa (client: tổng/thiếu ảnh/BC1) + nút **đổi khóa/xóa nhanh** ra lưới (xác nhận 2 bước, tôn trọng chặn BC1) | `QLY-01` | S | 35,23,24 | 1 | [x] 02/10 — thống kê Tổng·Thiếu ảnh + badge BC1 cấp khóa (phương án A, lưới không có cờ BC1 từng HV) + cột Thao tác đổi-khóa/xóa nhanh (ẩn khi BC1, tái dùng confirm 2 bước); build·29 vitest; review-nghiepvu 2/2 |
| 37 | **Chặn xóa HV khóa BC1 ở BACKEND**: `EXISTS(BaoCaoI theo MaKH)` trước `usp_NguoiLX_Delete` → 409 (bảo toàn `MaBC1/MaBC2` ↔ Báo cáo 1/2; TDD §11.3) | `QLY-03` | S | 24 | 1+2 | [x] 02/10 — cờ bc1 gộp vào query step 1 + guard 409 trước usp_NguoiLX_Delete; +2 test mock (127 pytest); review-nghiepvu đủ; xóa thật chờ verify prod |
| 38 | NAP-01: **"Bỏ khỏi hàng đợi"** (`DELETE /local/keo-ve/:uuid` xóa staging `keo_ve`, tool-local, tách bạch "Xóa khỏi DB") + **"Nạp lại nhanh"** dòng lỗi (gọi lại `nap_lo` 1 uuid) | `NAP-01` | S | 20 | 1 | [x] 02/10 — DELETE /local/keo-ve/:uuid (guard chỉ dòng 'xong', tool-local, không đụng prod) + nút 🟢 "Bỏ khỏi hàng đợi" / 🔴 "Nạp lại nhanh" (tái dùng nạp lô); +5 test (132 pytest); review-nghiepvu 2/2 |
| 39 | **QLY-07 (1/2)** backend đổi nền cả khóa: `POST /local/khoa/:ma_kh/doi-nen` job nền + tiến độ · `_BACKUP` **chỉ-nếu-chưa-có** · heuristic 4 góc phát hiện ảnh-trắng · **giữ `TT_XuLy`** · applock theo khóa (TDD §11.6) | `QLY-07` | M | 33,8 | 1+2 | [x] 02/10 — image.doi_nen_anh + anh_da_trang(4 góc) · doinen.py job thread + tiến độ + applock sp_getapplock + _BACKUP chỉ-nếu-chưa-có (<khóa>/_BACKUP) + giữ TT_XuLy (ghi_anh_update) · POST/GET /local/khoa/:ma_kh/doi-nen; +14 test (146 pytest); review-nghiepvu đủ (đã sửa 2 lệch TDD: applock + path backup) |
| 40 | **QLY-07 (2/2)** UI: dialog phạm vi (chỉ chưa-trắng/tất cả) + sao lưu + **thanh tiến độ** (polling N/tổng + số lỗi) | `QLY-07` | S | 39 | 1 | [x] 02/10 — DoiNenDialog 3 pha (form/chạy/xong) + radio phạm vi + checkbox sao lưu + polling 1.5s thanh % + đếm xong/bỏ qua/lỗi + ds lỗi + chặn đóng khi đang chạy + làm tươi lưới; build·29 vitest; review-nghiepvu đủ |
| 41 | **THU-05** ⚠VPS: server `DELETE /api/ho-so/:uuid` (soft-delete CAS `WHERE pending`, phân quyền IDOR `created_by`, ghi mốc `audit_log`) + webapp `DaGui` nút Xóa (chỉ pending, panel xác nhận 2 bước + copy #26, ẩn/khóa + chú thích khi đã nạp, của mình/admin). **Deploy lại VPS** | `THU-05` | M | 15,29 | 1+2 | → PRD |
| 42 | **QLY-08 (1/3)** ⚠VPS server: `POST /api/nap/:uuid/tra-ve-cho-nap` (CAS `imported→pending`, idempotent khi retry) + `GET /api/nap/tra-uuid?ma_dk=` (fallback tra uuid). **Deploy lại VPS** | `QLY-08` | S | 15 | 1+2 | [x] 03/10 — 2 endpoint CAS + idempotent; +11 test (110 pytest). Chưa deploy (Checkpoint 8). QLY-08 giữ 🔄 (còn task 43) |
| 43 | **QLY-08 (2/3)** tool+webui: `POST /local/ho-so/go-ve-cho-nap` — chặn BC1 409 (reuse QLY-03) → `usp_NguoiLX_Delete` cascade + ảnh `.jp2`→`_DELETED` (reuse `di_chuyen_anh`) → tra uuid (staging `nap_xong`/fallback `tra-uuid`) → gọi VPS `tra-ve-cho-nap` → staging về `cho` + **retry riêng bước VPS** (banner #26); webui `TraCuuDB` nút **"Gỡ về chờ nạp"** (panel cam 2 bước, chỉ chưa BC1) + refine copy "Xóa hẳn" (QLY-03, tách bạch) | `QLY-08` | M | 42,24,22,36 | 1+2 | [x] 03/10 — endpoint `go-ve-cho-nap`+`dong-bo-tra-ve` (reuse `_xoa_hv_csdt` tách từ QLY-03) + webui nút/panel/banner; tool 161 pytest (+15) · webui build+29 vitest · review-nghiepvu 8/10 (edge "Bỏ khỏi hàng đợi" → chủ dự án chốt nhắc Kéo về thủ công). QLY-08 ⚠️ Partial, chờ verify live Checkpoint 8 |
| 44 | **NAP-01 (đồng bộ xóa)** ⚠VPS: server `GET /api/nap/da-xoa?since=` (đọc `audit_log`) + tool "Kéo về từ VPS" bỏ dòng staging `pending` đã `deleted` (dùng `da-xoa`, KHÔNG suy từ vắng mặt trong `keo`); chỉ dòng chưa nạp. **Deploy lại VPS** | `NAP-01` | M | 20,41 | 1+2 | [x] 03/10 — server `da-xoa` (audit `'xoa'`) + tool bỏ dòng `'cho'` trùng uuid (mốc incremental) + toast; server 116 (+6) · tool 165 (+4) · build+29 vitest · review-nghiepvu đủ. Chờ deploy + verify live Checkpoint 8 |
| 45 | **"Dùng lại ảnh gốc"** AnhModal: +prop `anhGoc` (tách `anhBanDau`) + nút quay về ảnh nguyên bản (xác nhận nhanh, reset grab/zoom/xoay). Nguồn: NAP-04 = ảnh thô VPS phiên kéo-về · QLY-05 = ảnh `.jp2` DB transcode PNG. Ẩn khi không có nguồn | `NAP-04`,`QLY-05` | S | 8,35 | 1 | [x] 03/10 — AnhModal +prop `anhGoc` + nút "Dùng lại ảnh gốc" (xác nhận nhanh inline, reset zoom/pan/xoay qua `chonFile`), ẩn khi không có nguồn; NapHoSo truyền ảnh thô VPS, TraCuuDB truyền ảnh DB. Build+tsc+29 vitest. Trực quan chờ tool chạy với ảnh thật |
| 46 | **NAP-01 redesign (1/2)** màn Nạp lô: trạng thái sẵn sàng mỗi dòng (client, từ `nhap[uuid]`: đủ địa chỉ+giấy tờ) + **"Chọn tất cả sẵn sàng"** + thanh "Nạp N học viên" dính đáy + **drawer "Chuẩn bị"** (thay cột cố định: AddressCombo+giấy tờ+AnhModal) | `NAP-01` | M | 20,10 | 1 | [x] 03/10 — 1 list + badge Sẵn sàng/Thiếu (địa chỉ+giấy tờ; thiếu ảnh cảnh báo phụ) + nút "Chuẩn bị" mở drawer phải (địa chỉ+giấy tờ+ảnh, bỏ 2 cột cố định) + thanh đáy "Chọn tất cả sẵn sàng" & "Nạp N học viên". Build+tsc+29 vitest. Trực quan chờ chạy tool (màn có cổng login+dữ liệu) |
| 47 | **NAP-01 redesign (2/2)** dialog nạp 3 pha (reuse `DoiNenDialog`: xác nhận → tiến độ N/tổng → báo cáo ok/lỗi+lý do + **"Nạp lại lỗi"**) + nút **"Xem trong DB"** (sang Tra cứu DB, mở khóa đích + làm nổi HV vừa nạp) | `NAP-01` | M | 46,22 | 1+2 | [x] 03/10 — `NapLoDialog` 3 pha trong NapHoSo.tsx (nạp tuần tự từng uuid để có tiến độ + tên HV, TDD §10.5) thay nút batch gọi thẳng; pha báo cáo liệt kê ok/lỗi từng HV + "Nạp lại lỗi" (lọc uuid lỗi) + "Xem trong DB". Nút "Xem DB" cả ở dòng đã nạp (map `napKhoa` uuid→khóa). TraCuuDB nhận props `khoaMa`/`noiBat` → tự mở khóa đích + tô sáng HV vừa nạp lên đầu. Build+tsc+29 vitest. Trực quan chờ chạy tool (màn có cổng login+dữ liệu) |
| 48 | **QLY-09 (1/2)** backend đối soát (2 chế độ, TDD §11.8): **theo khóa** (ca ② — `NguoiLX_HoSo` theo `MaKhoaHoc` ↔ trạng thái VPS qua `nap_xong`/`tra-uuid`) + **quét lạc toàn hệ** (ca ①③ — tái dùng `GET /api/admin/ho-so` lọc trạng thái, check ma_dk∉CSDT = phantom / importing quá ngưỡng) + 3 action tái dùng `vps.tra_ve_cho_nap`/`da_nap`/`unlock` · **phòng tuyến 2**: `nap_fn` bỏ `da_nap` khi `_nap_mot` trả vé cũ (chặn tái phát phantom BUG-01) | `QLY-09` | M | 42,43,20,22 | 1+2 | [ ] |
| 49 | **QLY-09 (2/2)** webui panel **"Đối soát VPS↔CSDT"** trong Tra cứu DB: **theo khóa** (operator/admin) + **"Quét bản ghi lạc"** toàn hệ (admin) → liệt kê **chỉ dòng lệch** + loại + **nút sửa 1 chạm** (Trả về chờ nạp / Đánh dấu đã nạp / Mở khóa) → làm tươi. TDD §11.8 | `QLY-09` | M | 48,22 | 1 | [ ] |
| 50 | **NAP-01 nháp bền (1/3) — backend** (CHANGES #32, TDD §9.3a): bảng `nhap_chuan_bi` trong `staging.sqlite` + helper `nhap_xoa(uuid)` gọi ở 3 điểm kết thúc (nạp xong / bỏ hàng đợi / đồng bộ xóa VPS) + 3 endpoint `GET /local/nap/nhap?uuids=` (cờ nhẹ `co_dia_chi`/`co_anh`/`co_tick`) · `GET /local/nap/nhap/{uuid}` (full `jp2_b64`+preview) · `PUT /local/nap/nhap/{uuid}` + **BUG-04 reset địa chỉ nháp trong `keo_ve_upsert`** khi `noi_tt_raw` đổi (giữ ảnh/tick/nơi cấp). ⚠ **`impact` GitNexus TRƯỚC khi sửa `keo_ve_upsert`** (nhiều caller) | `NAP-01` | M | 20,46 | 1+2 | [x] 04/10 — bảng `nhap_chuan_bi` + CRUD + `nhap_xoa`/`nhap_reset_dia_chi` + BUG-04 trong `keo_ve_upsert` + 4 endpoint (list nhẹ/full/PUT/DELETE); impact xác nhận 1 caller LOW; +14 pytest (test_nap_keo 41 pass). UI (chip/nút) → task 51 |
| 51 | **NAP-01 nháp bền (2/3) — UI + 2 chip + nút** (CHANGES #32, TDD §10.5): NapHoSo chuyển `nhap[uuid]` RAM→API (list dùng cờ nhẹ, full khi mở drawer, `PUT` khi đóng/debounce) · 2 chip Địa chỉ/Ảnh (mặc định ✗) · nút "Xử lý" to + cả dòng bấm · nút "Xóa nháp" trong drawer · preview địa chỉ ghép `[chi_tiet, TenDayDu].join(", ")`. Chạy skill `impeccable` | `NAP-01` | M | 50,47 | 1 | [x] 04/10 — `nhap[uuid]` RAM→API (cờ nhẹ vẽ chip, full khi mở drawer, PUT khi đóng) + 2 chip `ChipCo` Địa chỉ/Ảnh + nút "Xử lý" to + cả dòng bấm + "Xóa nháp" (xác nhận 2 bước) + toast BUG-04 + ghép địa chỉ `join(", ")`. api.ts +nhapCo/Doc/Luu/Xoa. build+tsc+34 vitest. Playwright chờ chạy tool (cổng login+DB) |
| 52 | **NAP-01 nháp bền (3/3) — nạp chặn/cảnh báo** (CHANGES #32): thiếu địa chỉ → CHẶN dòng (loại khỏi lô, chip ✗) · thiếu ảnh → vẫn nạp + cảnh báo "N học viên nạp thiếu ảnh" trước lô · sau lô lối tắt mở Tra cứu DB lọc "chưa ảnh" (reuse "Xem trong DB") | `NAP-01` | S | 51,47 | 1 | [ ] |
| 53 | **QLY-05 bổ sung ảnh HV thiếu ảnh — 2 nguồn** (CHANGES #32, TDD §11.5): AnhModal mở với (a) `chonFile` / (b) kéo ảnh thô VPS (`vps.tra_uuid`→`vps.tai_anh`→`AnhModal.napTuUrl`), ẩn (b) khi ảnh thô hết ~30 ngày → cùng luồng QLY-05 (đổi nền→`.jp2`→`nap_anh`, nâng `TT_XuLy '01'→'03'`). Thuần wiring | `QLY-05` | M | 27,35,43 | 1 | [ ] |
| 26 | Đóng gói tool PyInstaller (.exe) + đối chiếu bảo mật OG (không `sa`, không log CCCD, HTTPS) | — | M | tất cả | 1 | [ ] |

### ✅ Checkpoint 6 — sau task 33-38 (quản lý ảnh Tra cứu DB + bảo toàn Báo cáo)
- [ ] `pnpm build` (webui) + tool chạy sạch.
- [ ] Xem ảnh chân dung HV thật ở Tra cứu DB (modal + avatar lưới); file mất → cảnh báo/icon ảnh-vỡ.
- [ ] **Hồi quy bug (mức 2):** thay ảnh HV đang ở trạng thái Báo cáo (`TT_XuLy '11'`) → sau khi lưu `TT_XuLy` **giữ nguyên**, không về `'03'`.
- [ ] Xóa HV ở khóa đã BC1 → backend chặn **409**.
- [ ] "Bỏ khỏi hàng đợi" dòng 🟢 không đụng DB prod; "Nạp lại nhanh" dòng 🔴 chạy đúng.

### ✅ Checkpoint 7 — sau task 39-40 (đổi nền cả khóa QLY-07)
- [ ] Đổi nền 1 khóa thật → ảnh chuyển nền trắng, tiến độ chạy, lỗi từng HV không hỏng cả lô.
- [ ] `_BACKUP` giữ **bản gốc đầu tiên**; chạy lần 2 KHÔNG đè backup.
- [ ] Khóa đã BC2 → sau đổi nền HV **vẫn còn trong Báo cáo** (`TT_XuLy` giữ nguyên).

### ✅ Checkpoint 8 — sau task 41-44 (xóa/gỡ hồ sơ app web ↔ tool ↔ VPS) — **⚠ Deploy lại VPS**
- [ ] **Deploy VPS** (server đổi: `DELETE /api/ho-so`, `tra-ve-cho-nap`, `tra-uuid`, `da-xoa`) → verify **3 vai trò + luồng gửi/kéo không gãy** ngay sau deploy.
- [ ] Collector xóa hồ sơ `pending` ở app web → VPS `deleted`; `importing`/`imported` → chặn (nút ẩn + server 409); xóa hồ sơ người khác → **403**.
- [ ] Tool "Kéo về" → hồ sơ đã xóa **biến mất khỏi hàng chờ**; dòng `pending` đang bị khóa / ngoài limit **KHÔNG bị xóa nhầm** (mức 2).
- [ ] QLY-08: gỡ HV khóa **chưa BC1** → biến mất CSDT + về hàng chờ nạp; khóa **BC1** → chặn; **VPS lỗi sau khi xóa CSDT** → báo rõ + "Thử lại" được.
- [x] **Mức 2** (03/10): CAS delete/`tra-ve-cho-nap` idempotent + BC1 guard — server `test_nap` (tra-ve CAS/idempotent/409, da-xoa) + tool `test_hoso`/`test_nap_keo` (BC1 409, go-ve, keo_ve_xoa_neu_cho). server 123 · tool 165.
- [x] **Mức 3** (03/10): `test_toantuyen` +7 E2E phía VPS — A1 gửi→xóa→kéo biến mất · A2 IDOR 404 · A4 admin xóa · A5 da-xoa rỗng (chống xóa nhầm) · B1 nạp→gỡ→hàng chờ (ma_dk gỡ) · B3 gỡ khi đã xóa 409 · B4 về pending collector sửa lại. (Phần tool↔SQL Server verify live sau deploy.)

### ✅ Checkpoint 9 — sau task 45-47 (ảnh gốc + redesign Nạp lô)
- [ ] "Dùng lại ảnh gốc" ở NAP-04 (ảnh thô VPS) + QLY-05 (ảnh DB) → về đúng ảnh nguyên bản, bỏ chỉnh sửa; ẩn nút khi không có nguồn.
- [ ] Màn Nạp lô: mỗi dòng báo `✔ Sẵn sàng`/`⚠ Thiếu…`; "Chọn tất cả sẵn sàng" chỉ tick dòng đủ điều kiện.
- [ ] Dialog nạp 3 pha: tiến độ chạy, báo cáo đúng ok/lỗi + lý do; "Nạp lại lỗi" chạy đúng; "Xem trong DB" mở đúng khóa + HV vừa nạp.
- [ ] Playwright 3vp (375/800/1440) màn Nạp lô + drawer — 0 tràn.

### ✅ Checkpoint 10 — sau task 48-49 (đối soát VPS↔CSDT, QLY-09)
- [ ] Chọn 1 khóa → panel liệt kê đúng **chỉ dòng lệch** (tạo lệch thử: ca ① phantom, ② CSDT-có-VPS-chưa, ③ importing treo).
- [ ] Mỗi nút sửa 1 chạm chạy đúng (Trả về chờ nạp / Đánh dấu đã nạp / Mở khóa) → làm tươi, dòng khớp biến mất.
- [ ] **Mức 2:** phòng tuyến 2 — gỡ về chờ nạp rồi nạp lại CÙNG uuid → `nap_fn` KHÔNG gọi `da_nap` trên nhánh vé-cũ (VPS không bị đánh dấu imported sai).
- [ ] Tôn trọng chặn BC1/PII ở các nút sửa đụng xóa/gỡ.

### ✅ Checkpoint 11 — sau task 50-53 (nháp bền + 2 chip + 2 nguồn ảnh, CHANGES #32)
- [ ] Nháp (địa chỉ 2 cấp + chi tiết + nơi cấp + tick + ảnh đổi nền) **sống qua F5/đóng-mở tool**; 2 chip Địa chỉ/Ảnh phản ánh đúng sau khi mở lại.
- [ ] **Mức 2:** `keo_ve_upsert` thấy `noi_tt_raw` đổi → reset **riêng địa chỉ** nháp (giữ ảnh/tick/nơi cấp) + chip địa chỉ về ✗; `nhap_xoa` dọn **cả ảnh** ở 3 điểm kết thúc (nạp xong / bỏ hàng đợi / đồng bộ xóa VPS).
- [ ] Chip vẽ từ endpoint cờ **nhẹ** — mở màn Nạp khóa đông KHÔNG tải full ảnh base64 cả list.
- [ ] Nạp: thiếu địa chỉ bị **chặn** (loại khỏi lô); thiếu ảnh **cảnh báo + vẫn nạp**; lối tắt mở Tra cứu DB lọc "chưa ảnh".
- [ ] Bổ sung ảnh 2 nguồn (file + ảnh thô VPS); ảnh thô hết hạn → ẩn nguồn VPS, chỉ còn file.
- [ ] Nút "Xóa nháp" dọn nháp (gồm ảnh PII) chủ động.
- [ ] Playwright 3vp (375/800/1440) màn Nạp lô + drawer — 0 tràn.

### ✅ Checkpoint 5 — cuối dự án
- [ ] Mọi tiêu chí MUST + SHOULD trong PRD đạt.
- [ ] Đối chiếu bảo mật OG đóng trước go-live (chặn go-live nếu chưa đạt).
- [ ] So giờ máy DB ↔ VPS (Asia/Saigon) trước go-live — MaDK/tên file `.jp2` theo timestamp máy DB.

## Nhóm chạy song song được

> Chủ dự án chốt **1 người build tuần tự** → không dùng song song. Mục này để tham chiếu nếu về sau mở phiên thứ hai.

**Phải chạy một mình (nếu có parallel):**
- Task 1, 3, 12, 13 — dựng khung, chạm cấu trúc nền của cả app.
- Task 5 — bảng phụ trên DB đích.
- Task 9, 14, 15 — cơ chế lõi (SP import / auth / hàng đợi), nhiều task dựa vào.

## Chờ chốt (chưa lên lịch code)

| Story | Thiếu gì | Cần ai |
|---|---|---|
| `QLY-04` | Kết xuất Excel — mới 1 dòng PRD, chưa đủ chi tiết để ước lượng | Chủ dự án bổ sung story |
| `THU-03` | Offline app web — mới 1 dòng PRD; lưu ý kiểm trùng CCCD + map DVHC phải dời về bước nạp | Chủ dự án bổ sung story |

## Đã xong trước khi lập kế hoạch

- Không có code thật. `ui-demo/` là prototype tham chiếu style/layout (11 màn), **không phải scaffold thật** — khi code phải tách theo TDD §2.4 (`webapp/` + `server/` + `tool/webui/`), không bê nguyên project gộp.

## Rủi ro

| Rủi ro | Tác động | Cách xử |
|---|---|---|
| Nạp ra bản ghi không khớp app cũ | Cao | Checkpoint 2 nạp thử 1 HV đối chiếu trước khi mở rộng (AS-003) |
| Chưa có SQL login riêng cho tool | Cao | Prerequisite trước task 4; hiện mới có `sa` (chỉ đọc-kiểm) |
| QR thẻ thật khác chuẩn 6/7 trường | Cao (xác suất thấp) | Checkpoint 4 test thẻ thật (AS-001) |
| Xã chia không map được | Trung bình | Fallback popup chọn tay `DM_DVHC` (task 7) |
| rembg xóa phông xấu (tóc/viền) | Trung bình | Cho giữ ảnh gốc/chỉnh tay (task 8) |
| Đồng hồ máy DB sai giờ | Trung bình | So giờ trước go-live (Checkpoint 5) |
| Sửa server VPS đang chạy prod (task 41/42/44) làm gãy luồng thu thập đang live | Cao | Deploy giờ thấp điểm + verify login/gửi/kéo ngay sau deploy (Checkpoint 8); đổi thêm endpoint, không đổi endpoint cũ |

## Nguồn đối chiếu

> `/tieptheo` so mục này với PRD mỗi buổi để biết kế hoạch còn khớp không. Lệch thì báo user chạy lại `/kehoach` chế độ bổ sung. **Không tự sửa kế hoạch.**

- **Số story trong PRD khi cập nhật:** 25 (gồm story mới `QLY-09` từ CHANGES #28; `THU-05`, `QLY-08` từ #24; chưa tính NICE `QLY-04`, `THU-03`)
- **Mã story đã đưa vào kế hoạch:** `HTG-01`, `HTG-02`, `HTG-03`, `THU-01`, `THU-02`, `THU-04`, `THU-05`, `NAP-01`…`NAP-06`, `KHO-01`, `QLY-01`, `QLY-02`, `QLY-03`, `QLY-05`, `QLY-06`, `QLY-07`, `QLY-08`, `QLY-09`
- **Mã story chưa đưa vào:** `QLY-04`, `THU-03` (NICE, chưa đủ chi tiết) · **`HTG-04/05/06`** (thêm ở CHANGES #18, đã code thẳng — chưa có task trong plan; cần `/kehoach` bổ sung riêng nếu muốn khớp sổ)
- **Đã đọc `docs/CHANGES.md` tới dòng ngày:** 04/10/2026 (#32)

## Changelog

| Ngày | Thay đổi |
|---|---|
| 01/10/2026 | v1 — kế hoạch đầu tiên, 26 task (3 phase, risk-first theo TDD §17) |
| 01/10/2026 | v2 — bổ sung (CHANGES #4/#5): reconcile task 9+10 về `[ ]` + đổi mô tả sang 1 SP gộp hướng A (bỏ compensation); thêm task 27 `QLY-05` (nạp/thay ảnh HV đã có). 27 task. |
| 01/10/2026 | v3 — bổ sung (CHANGES #6): cập nhật mô tả task 20 `NAP-01` (IA 2 chế độ, IN HOA, check chính tả mức A, nạp lô badge ⚪🔴🟢, cảnh báo nổi bật) + task 22 `QLY-01` (chế độ Tra cứu DB, tìm mọi khóa kể cả BC1). Không thêm/xóa/đổi số task — vẫn 27 task. |
| 01/10/2026 | v4 — bổ sung (CHANGES #12): thêm task **28** (rework UX THU-01: màn vào + khung bám QR + layout dính đáy + header) + task **29** (rework UX THU-02: endpoint ảnh collector + ảnh thật + xem/sửa/chụp lại) vào cuối Phase 2. 29 task. THU-01/02 đã hạ ⏳ ở PRD. |
| 01/10/2026 | v5 — bổ sung (CHANGES #13): thêm task **30** (nhập liên tiếp: nút "Lưu & nhập hồ sơ tiếp" + badge/lọc "Thiếu ảnh", THU-01/02) + task **31** (cảnh báo trùng CCCD app web, THU-04) — cả 2 đã code+deploy. +QLY-06 (📝 Draft) vào Chờ chốt. 31 task. |
| 01/10/2026 | v6 — bổ sung (CHANGES #16): kiểm DB thật chốt thiết kế `QLY-06` → chuyển từ Chờ chốt thành **task 32** (Phase 3, nạp khác khóa/khác hạng). 32 task. |
| 02/10/2026 | v7 — bổ sung (CHANGES #22): thêm task **33-40** (Phase 3) — 🐛 vá `TT_XuLy` (33), backend ảnh (34), UI xem ảnh/avatar (35), thống kê+nút nhanh (36), chặn xóa BC1 backend (37), bỏ-hàng-đợi+nạp-lại-nhanh (38), **QLY-07** đổi nền cả khóa (39-40) + Checkpoint 6/7. QLY-01/03/05 + NAP-01 đã hạ ⏳ ở PRD. 40 task. |
| 03/10/2026 | v8 — bổ sung (CHANGES #24+#26): thêm task **41-47** (cuối Phase 3, trước task 26 đóng gói) — THU-05 xóa app web (41 ⚠VPS), QLY-08 gỡ về chờ nạp server (42 ⚠VPS) + tool/webui (43), NAP-01 đồng bộ xóa (44 ⚠VPS), "Dùng lại ảnh gốc" AnhModal (45), redesign Nạp lô drawer+sẵn sàng (46) + dialog nạp 3 pha + Xem trong DB (47) + Checkpoint 8/9. Lần đầu sửa server VPS từ Phase 2 → deploy lại. +story QLY-08, THU-05. 47 task. |
| 03/10/2026 | v9 — bổ sung (CHANGES #28): thêm task **48-49** (cuối Phase 3, trước task 26) — QLY-09 đối soát VPS↔CSDT: backend liệt kê lệch theo khóa + 3 action tái dùng + phòng tuyến 2 chặn phantom (48), webui panel đối soát + nút sửa 1 chạm (49) + Checkpoint 10. Thuần tool, không endpoint/SP nạp mới. +story QLY-09. 49 task. |
| 04/10/2026 | v10 — bổ sung (CHANGES #32, sau review TDD #32): thêm task **50-53** (cuối Phase 3, trước task 26) — NAP-01 lưu nháp BỀN backend `nhap_chuan_bi`+`nhap_xoa`+3 endpoint+BUG-04 reset trong `keo_ve_upsert` (50), UI nháp bền+2 chip+nút Xử lý/Xóa nháp (51), nạp chặn thiếu địa chỉ/cảnh báo thiếu ảnh+lối tắt (52); QLY-05 bổ sung ảnh 2 nguồn file/ảnh-thô-VPS (53) + Checkpoint 11. Endpoint list nhẹ + luật ghép địa chỉ theo biên bản `tdd-review-04-10-2026.md`. Tái dùng NAP-01/QLY-05, không story mới. 53 task. |
