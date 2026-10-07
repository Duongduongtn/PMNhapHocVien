# Kế hoạch build — PMCSĐTLX Thu nhận hồ sơ học viên

> File do `/kehoach` sinh. `/tieptheo` đọc file này để biết làm gì tiếp theo.
> **Thứ tự code** nằm ở đây. **Yêu cầu và trạng thái story** nằm ở `docs/PRD.md`.
> Cập nhật lần cuối: 07/10/2026 (v19 — sửa THU-06 chỉ OCR 5 trường mặt trước, bỏ ngày cấp (CHANGES #50). Trước đó v18 — Phase 7 THU-06 task 79-80; v17 — KQD-06 task 78)

## Quyết định về thứ tự

- **Risk-first (theo TDD §17):** làm **Tool nạp DB trước** vì đây là mắt xích khó & rủi ro cao nhất — sinh `SoHoSo` qua `sp_getapplock`, gọi **1 SP gộp app cũ** `usp_QuangLA_...ThemMoiCapNhat`, ghi ảnh hướng A riêng (UPDATE 5 cột), xuất `.jp2` khớp app cũ. Hỏng chỗ này ở cuối dự án = làm lại từ đầu; nên chứng minh sớm bằng **nạp tay 1 HV** (AS-003) rồi mới dựng đường thu thập. *(01/10 — đổi 3 SP rời → 1 SP gộp, bỏ compensation vì SP atomic; xem CHANGES #4/#5.)*
- **Đảo ưu tiên có chủ đích (Luật 2 > Luật 3):** vài story **MUST** (`KHO-01`, `HTG-03`) nằm ở Phase 3 vì độc lập, rủi ro thấp, không nằm trên đường chứng minh lõi (DB đã có khóa thật + hồ sơ thật để test NAP). SHOULD `QLY-*` cũng Phase 3 vì phụ thuộc `NAP-05`.
- **`HTG-01` cắt 3 task theo nơi chạy:** ① cấu hình kết nối tool (local, Phase 1) · ② auth JWT trên VPS (Phase 2) · ③ login UI + tool gate (Phase 2). PRD chỉ chuyển ✅ khi xong cả 3.
- **`NAP-05` và `HTG-02` cắt đôi** để không còn task cỡ L.
- **1 người build → tuần tự một luồng**, không tách nhánh song song (quyết định chủ dự án 01/10/2026).
- **Phase 4 Đồng bộ CDB (task 54-60) — module mới tách khỏi Nạp:** SHOULD, xếp cuối sau mọi task Nạp/thu thập (không đảo lên MUST). Đổi `ToolLayout`→sidebar (task 54) đụng chrome dùng chung → chạy một mình, nhưng **hành vi màn Nạp không đổi** (không hạ story Nạp). Ghi vào CSDL đích GPLX_CDB_CSDT (≠ CSDL Nạp) → module backend tách (`sync_*`), không import Nạp. Tạo HV **qua 3 SP chuẩn CDB** + MaCSDT từ `QTHT.MA_CSDT`/khóa đích (đã phân tích DB: `docs/DB-GPLX_CDB_CSDT.md`). Khóa đích đã BC1: **cảnh báo, vẫn cho sync** (user chốt B 04/10) — khác NAP-02 chặn cứng, vì sync là thao tác bù dữ liệu chủ động.
- **KQD (task 71-78, Phase 6) — module #3 "Cập nhật kết quả đào tạo":** xếp sau DGT vì là module mới hoàn toàn, tái dùng hạ tầng CDB đã ổn định (sidebar task 54 + `conn_dich`/config đích task 55). Cắt KQD-02 làm 2 task (72 backend quy đổi/Đạt/ghi · 73 UI form) và KQD-05 làm 2 task (76 backend mở-khóa · 77 UI) tránh cỡ L (nhiều tiêu chí Done); KQD-06 (task 78) sửa lẻ/xóa điểm gộp 1 task. KQD-05 "Mở khóa để sửa sau kết xuất" thao tác **mức CƠ SỞ** (DB không nối HV↔gói). Chỉ ghi KQĐT (`TT_XuLy` 03→09/10, riêng KQD-05 lùi 12→09/10, KQD-06 lùi 09/10→03 khi xóa điểm), KHÔNG kết xuất XML. Mọi ghi thật đối chiếu phần mềm CDB → nghiệm thu máy CSDT (như TCB/QLY).
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

[Phase 4 — Module Đồng bộ CDB]  (ghi vào GPLX_CDB_CSDT, tách khỏi Nạp)
    Sidebar workspace shell (54, đổi ToolLayout) ─┐
    Sync nền backend (55: config đích + conn_dich + sync_helpers + sync_history)
          ├── SYNC-02 Quản lý CSDL đích (56)
          ├── SYNC-01 backend tạo HV qua 3 SP + MaCSDT từ QTHT/khóa đích (57)
          │     ├── SYNC-01 SSE + chạy (58)
          │     └── SYNC-01 UI Bàn đồng bộ (59, bám mock + sidebar 54)
          └── SYNC-03 Lịch sử & Hủy sync (60)
                 └── (26) Đóng gói .exe — sau Phase 4
```

## Prerequisite (chủ dự án/ops làm trước khi tới task liên quan)

- **Tạo SQL login riêng cho tool** (không dùng `sa`) trên máy DB `DESKTOP-UBV2GQI` — cần trước **task 4**. Hiện mới có `sa` (chỉ dùng đọc-kiểm READ ONLY).
- **AS-001** quét thẻ CCCD thật của cơ sở — kiểm ở Checkpoint 4.
- **AS-003** nạp thử 1 HV → mở app cũ đối chiếu — kiểm ở Checkpoint 2.
- **MaGT identity?** — kiểm `NguoiLXHS_GiayTo.MaGT` ở `GPLX_CDB_CSDT` có IDENTITY không (quyết truyền tay hay dùng hàm `GetMaGiaytoByHosoForSync`) — cần trước **task 57**.
- **SP sửa/đổi khóa/xóa trong CDB?** — kiểm `GPLX_CDB_CSDT` có `usp_NguoiLX_Update` / SP đổi khóa / SP xóa (như `GPLX_CSDT`) không — cần trước **task 65-66**; thiếu thì tắt nút tương ứng + báo (đã ghi trong TDD §11B.7 + CHANGES #35).

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
| 48 | **QLY-09 (1/2)** backend đối soát (2 chế độ, TDD §11.8): **theo khóa** (ca ② — `NguoiLX_HoSo` theo `MaKhoaHoc` ↔ trạng thái VPS qua `nap_xong`/`tra-uuid`) + **quét lạc toàn hệ** (ca ①③ — tái dùng `GET /api/admin/ho-so` lọc trạng thái, check ma_dk∉CSDT = phantom / importing quá ngưỡng) + 3 action tái dùng `vps.tra_ve_cho_nap`/`da_nap`/`unlock` · **phòng tuyến 2**: `nap_fn` bỏ `da_nap` khi `_nap_mot` trả vé cũ (chặn tái phát phantom BUG-01) | `QLY-09` | M | 42,43,20,22 | 1+2 | [x] 04/10 — ⚠ĐỔI SCOPE (user chọn A): +server read `GET /api/nap/trang-thai?uuids=` (operator, ca ②) + admin ho-so +ma_dk/locked_at (ca ①③) → **cần deploy VPS**. Tool `doisoat.py` (khoa/lac + 3 action) + vps.py wrapper + phòng tuyến 2 `nap_fn` bỏ da_nap khi `trung_uuid` (KHÔNG đụng nap_mot_hv — né impact HIGH). server 128 pytest (+5) · tool 193 pytest (+12). UI → task 49 |
| 49 | **QLY-09 (2/2)** webui panel **"Đối soát VPS↔CSDT"** trong Tra cứu DB: **theo khóa** (operator/admin) + **"Quét bản ghi lạc"** toàn hệ (admin) → liệt kê **chỉ dòng lệch** + loại + **nút sửa 1 chạm** (Trả về chờ nạp / Đánh dấu đã nạp / Mở khóa) → làm tươi. TDD §11.8 | `QLY-09` | M | 48,22 | 1 | [x] 04/10 — `DoiSoatDialog.tsx` (2 chế độ: theo khóa operator/admin + Quét lạc admin qua `useToolAuth`) + nút "Đối soát máy chủ" ở toolbar Tra cứu DB; mỗi dòng lệch mô tả nghiệp vụ + nút sửa 1 chạm → làm tươi; api.ts +5 client fn. build+tsc+34 vitest. Playwright chờ chạy tool. **review-nghiepvu 15/16 đủ; edge "Khóa BC1" → chốt (user 04/10) KHÔNG cần guard: 3 action không xóa/gỡ CSDT (① phantom không có CSDT · ② da_nap chỉ đồng bộ VPS · ③ unlock chỉ VPS) — PRD:541 guard chỉ áp hành động xóa/gỡ; thêm guard còn hại ca ②. Đối soát là read-only (đạt phần 'chỉ đọc').** |
| 50 | **NAP-01 nháp bền (1/3) — backend** (CHANGES #32, TDD §9.3a): bảng `nhap_chuan_bi` trong `staging.sqlite` + helper `nhap_xoa(uuid)` gọi ở 3 điểm kết thúc (nạp xong / bỏ hàng đợi / đồng bộ xóa VPS) + 3 endpoint `GET /local/nap/nhap?uuids=` (cờ nhẹ `co_dia_chi`/`co_anh`/`co_tick`) · `GET /local/nap/nhap/{uuid}` (full `jp2_b64`+preview) · `PUT /local/nap/nhap/{uuid}` + **BUG-04 reset địa chỉ nháp trong `keo_ve_upsert`** khi `noi_tt_raw` đổi (giữ ảnh/tick/nơi cấp). ⚠ **`impact` GitNexus TRƯỚC khi sửa `keo_ve_upsert`** (nhiều caller) | `NAP-01` | M | 20,46 | 1+2 | [x] 04/10 — bảng `nhap_chuan_bi` + CRUD + `nhap_xoa`/`nhap_reset_dia_chi` + BUG-04 trong `keo_ve_upsert` + 4 endpoint (list nhẹ/full/PUT/DELETE); impact xác nhận 1 caller LOW; +14 pytest (test_nap_keo 41 pass). UI (chip/nút) → task 51 |
| 51 | **NAP-01 nháp bền (2/3) — UI + 2 chip + nút** (CHANGES #32, TDD §10.5): NapHoSo chuyển `nhap[uuid]` RAM→API (list dùng cờ nhẹ, full khi mở drawer, `PUT` khi đóng/debounce) · 2 chip Địa chỉ/Ảnh (mặc định ✗) · nút "Xử lý" to + cả dòng bấm · nút "Xóa nháp" trong drawer · preview địa chỉ ghép `[chi_tiet, TenDayDu].join(", ")`. Chạy skill `impeccable` | `NAP-01` | M | 50,47 | 1 | [x] 04/10 — `nhap[uuid]` RAM→API (cờ nhẹ vẽ chip, full khi mở drawer, PUT khi đóng) + 2 chip `ChipCo` Địa chỉ/Ảnh + nút "Xử lý" to + cả dòng bấm + "Xóa nháp" (xác nhận 2 bước) + toast BUG-04 + ghép địa chỉ `join(", ")`. api.ts +nhapCo/Doc/Luu/Xoa. build+tsc+34 vitest. Playwright chờ chạy tool (cổng login+DB) |
| 52 | **NAP-01 nháp bền (3/3) — nạp chặn/cảnh báo** (CHANGES #32): thiếu địa chỉ → CHẶN dòng (loại khỏi lô, chip ✗) · thiếu ảnh → vẫn nạp + cảnh báo "N học viên nạp thiếu ảnh" trước lô · sau lô lối tắt mở Tra cứu DB lọc "chưa ảnh" (reuse "Xem trong DB") | `NAP-01` | S | 51,47 | 1 | [x] 04/10 — chặn địa chỉ sẵn có (dòng thiếu → boQua); NapLoDialog +cảnh báo "N thiếu ảnh" pha xác nhận + nút "Bổ sung ảnh (N)" pha báo cáo → `xemTrongDB(ma_kh, [], "chua")`; TraCuuDB +prop `locAnhBanDau` (áp bộ lọc chưa-ảnh, reset theo moNonce). build+tsc+34 vitest |
| 53 | **QLY-05 bổ sung ảnh HV thiếu ảnh — 2 nguồn** (CHANGES #32, TDD §11.5): AnhModal mở với (a) `chonFile` / (b) kéo ảnh thô VPS (`vps.tra_uuid`→`vps.tai_anh`→`AnhModal.napTuUrl`), ẩn (b) khi ảnh thô hết ~30 ngày → cùng luồng QLY-05 (đổi nền→`.jp2`→`nap_anh`, nâng `TT_XuLy '01'→'03'`). Thuần wiring | `QLY-05` | M | 27,35,43 | 1 | [x] 04/10 — nguồn (a) chọn-file sẵn có; +nguồn (b) `GET /local/ho-so/anh-vps?ma_dk=` (resolve uuid staging→VPS tra-uuid → tai_anh, 404 khi hết hạn) + client `taiAnhVps` + nút "Kéo ảnh máy chủ" trong panel (chỉ HV chưa ảnh), seed AnhModal qua `anhBanDau`. tool 181 pytest (+6 /anh-vps) · webui build+34 vitest. Playwright chờ chạy tool |
| 26 | **DGT-01** Đóng gói tool PyInstaller (.exe): one-folder + `--add-data` (webui/dist, dvhc_map.sqlite, SQL/mẫu) + **FastAPI mount StaticFiles phục vụ `webui/dist` cùng cổng** (SPA fallback, giữ `/local/*`) + **chuyển gốc dữ liệu → `%APPDATA%` khi `sys.frozen`** (config/key.bin, staging.sqlite, ảnh tạm) + test **máy sạch** (pymssql/FreeTDS); cân nhắc bỏ rembg (exe to). + đối chiếu bảo mật OG (không `sa`, không log CCCD, HTTPS). Thuộc **Phase 5 (DGT)** — xem dưới | `DGT-01` | M | tất cả | 1 | → PRD |

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

## Phase 4 — Đồng bộ CDB (workspace mới, tách khỏi Nạp)

> Feature SHOULD thêm ở CHANGES #33. Port nghiệp vụ `D:\Du_An\GPLX\sync_tool` v2.0 vào `tool/`, tách module bằng **sidebar workspace** (mở rộng N — đón module #3 "Kết quả đào tạo"). Ghi vào **CSDL đích GPLX_CDB_CSDT** — đọc `docs/DB-GPLX_CDB_CSDT.md` trước khi code. UI dựng thẳng `tool/webui` bám mock `ui-mock/sync.html` + skill UI (KHÔNG qua ui-demo). Tool CHỈ desktop (≥1280px, bảng cuộn ngang).

| # | Task | Story | Quy mô | Phụ thuộc | Kiểm | Xong |
|---|---|---|---|---|---|---|
| 54 | **Sidebar workspace shell**: `ToolLayout` top-nav→**sidebar module** (registry `MODULES` mở rộng N + màu nhấn + banner CSDL); nav Nạp (Nạp/Tạo khóa/Cấu hình)→sub-nav trong module Nạp — **hành vi màn Nạp KHÔNG đổi** (chỉ đổi vị trí điều hướng) | — | M | 3 | 1 | [x] |
| 55 | **Sync nền backend**: config `sync_targets/sync_selected/sync_options` (mã hóa, khối riêng) + `db.py sqlserver_conn_dich(db)` + `sync_helpers.py` (port `db_helpers`: `sinh_madk_batch`, `kiem_tra_madk_ton_tai`, `enrich_from_db_dich`, load năm/khóa theo year, **MaCSDT từ `QTHT_ThamSoHT.MA_CSDT`/khóa đích**, copy/snapshot) + `sync_history.py` (port HistoryStore/SyncBatch) — `pyodbc ?`→`pymssql %s` | — | M | 4 | 1+2 | [x] |
| 56 | **SYNC-02 Quản lý CSDL đích**: router `/local/sync/targets` GET/POST (CRUD + chọn mặc định + test kết nối báo số NguoiLX) + options TT_XuLy(mặc định 03)/TongSoHV; webui màn DB đích (bảng target + radio + Thêm/Sửa/Xóa + tùy chọn) | `SYNC-02` | M | 54,55 | 1+2 | → PRD |
| 57 | **SYNC-01 (1/3) backend tạo HV**: `sync_service.sync_one_hv` qua **3 SP** `usp_NguoiLX_Insert`(`@MaDK=NULL`/precomputed)+`usp_NguoiLX_HoSo_Insert`(`@SoHoSo=NULL`→`CreateNewSoHoso`)+`usp_NguoiLXHS_GiayTo_Insert` (kiểm MaGT identity — prerequisite); **MaCSDT từ khóa đích**; `NguoiTao=admin`; backdate MaDK batch + UPDATE 4 cột ngày; guard MaDK trùng; endpoints năm/khóa (nguồn+đích, **khóa đích trả cờ `bc1`** cho cảnh báo B) + hoc-vien+enrich (skip HV đã có); **E1** chặn HV thiếu CCCD + **E2** đánh dấu trùng CCCD trong DS nguồn + **E3** sync-lại-an-toàn (idempotent qua skip) | `SYNC-01 (1/3)` | M | 55 | 1+2 | [x] |
| 58 | **SYNC-01 (2/3) SSE + chạy**: `POST /local/sync/run` (job nền thread + `asyncio.Queue`, ngắt SSE job vẫn chạy hết) + `GET /local/sync/stream` (SSE từng HV `{stt,trang_thai}` + tổng kết) + validate hạng khớp / ngày ≤ NgàyKG / backdate >90 hỏi | `SYNC-01 (2/3)` | M | 57 | 1+2 | [x] |
| 59 | **SYNC-01 (3/3) UI Bàn đồng bộ**: màn React bám `ui-mock/sync.html` + skill UI — khung chọn khóa **cố định/thu gọn**, bảng 11 cột **header dính** + **phân trang** (mẫu `PhanTrang`), **SYNC cố định chân**, tiến trình SSE, HV đã có nền vàng + khóa tick; **cảnh báo khi khóa đích đã BC1 (vẫn cho sync — B)**; **(a)** combo khóa gõ-để-lọc · **(b)** toggle "Chỉ hiện HV sẽ tạo mới" · **(c)** đếm dòng đang tick cạnh SYNC; chặn/cảnh báo E1/E2; bỏ ô cán bộ + bỏ CSV | `SYNC-01 (3/3)` | M | 54,57,58 | 1 | [x] |
| 60 | **SYNC-03 Lịch sử & Hủy sync**: router `/local/sync/lich-su` (đọc JSON `%APPDATA%`) + rollback (xóa theo MaDK log + `NguoiTao='SYNC'`, cascade `NguoiLX→HoSo→GiayTo`, **bắt lỗi HV đã BC1** FK NO_ACTION, cập nhật TongSoHV) + webui màn Lịch sử + modal hủy | `SYNC-03` | M | 55,57 | 1+2 | → PRD |
| 61 | **HTG-07 Bảng cấu hình chung ở header** (CHANGES #34): `ToolLayout` +icon ⚙ góc phải header → panel/drawer **2 khối tách bạch**: ① *kết nối chung + DB NGUỒN Nạp* (gộp `CauHinh.tsx`) · ② *nhiều DB ĐÍCH Sync* (gộp `DbDich.tsx` — CRUD/mặc định/test/tùy chọn); gỡ route `/tool/cau-hinh` + `/sync/db-dich` khỏi `App.tsx` + subnav `lib/modules.ts`; mọi lối cũ trỏ 2 màn → mở panel. **Thuần UI** — backend `/local/config*`+`/local/sync/targets`+config-store KHÔNG đổi. `impeccable`+`ui-ux-pro-max` | `HTG-07`, `SYNC-02` | M | 54,56 | 1 | → PRD |
| 62 | **SYNC-01 làm đẹp UI** (CHANGES #34): combobox năm/khóa + ô chọn DB đích gọn, nhãn rõ (năm·khóa·hạng); **danh sách HV để sync tên hài hòa, đủ dấu, căn cột, mật độ dòng vừa, không tràn/cắt chữ** (`BanDongBo.tsx`, `ComboLoc.tsx`); bám token `tool/webui`; `impeccable`+`ui-ux-pro-max`. Nghiệp vụ sync KHÔNG đổi (bám sync_tool v2.0) | `SYNC-01` | S | 59,61 | 1 | → PRD |
| 63 | **Màn Tra cứu CDB + đọc** (TCB, CHANGES #35, TDD §11B.7): `pages/sync/TraCuuCDB.tsx` (mới, **tái dùng** `AnhModal`/`AnhAvatar`, **KHÔNG sửa** `TraCuuDB.tsx` của QLY-01) + endpoint đọc CDB qua `sqlserver_conn_dich` (tra khóa mọi khóa kể cả BC1, lưới HV avatar lazy-load + tìm tên bỏ dấu/CCCD, chi tiết + ảnh lớn + đường dẫn, thống kê đầu khóa + cờ DKKH/BC1) + nút **"Xem chi tiết HV"** ở `BanDongBo.tsx` (mở khóa chứa MaDK đích + tô sáng, reuse `khoaMa`/`noiBat`). *Nếu khi code thấy phình → cắt đôi (khóa+lưới / chi tiết+ảnh+nút).* | `TCB-01` | M | 54,55,59 | 1 | → PRD |
| 64 | **Thay ảnh HV ở CDB** (TCB): từ chi tiết → `AnhModal` + đổi nền (`/local/anh/xu-ly` rembg, nguồn file máy / ảnh `.jp2` hiện có) → **sao lưu `<tên>_BACKUP.jp2` CÙNG thư mục (chỉ nếu chưa có)** → ghi đè đúng file, giữ tên + `DuongDanAnh` → UPDATE `ChatLuongAnh`/`NgayThuNhanAnh` ở bản ghi CDB; cho phép kể cả DKKH/BC1 (chỉ **cảnh báo**); **endpoint ghi buộc token operator** (collector 403). Ảnh dùng chung 2 DB → thay đổi cả ở Nạp | `TCB-02` | M | 63,8 | 1+2 | → PRD |
| 65 | **Sửa nhân thân HV ở CDB** (TCB): `usp_NguoiLX_Update` của CDB (đọc lại full giữ cột không sửa, KHÔNG đụng kết quả/BC1/BC2) — **CHẶN nếu `KhoaHoc.SoQD_KhaiGiang` có giá trị** (đã kết xuất DKKH) → báo rõ; **kiểm SP tồn tại trong CDB, thiếu → tắt nút + báo**; endpoint ghi buộc token operator | `TCB-03` | M | 63 | 1+2 | → PRD |
| 66 | **Xóa HV / Đổi khóa HV ở CDB** (TCB): xóa cascade (NguoiLX+NguoiLX_HoSo+GiayTo) / đổi khóa đích cùng hạng chưa BC1 — **CHẶN nếu `NguoiLX_HoSo.MaBC1` có giá trị** (đã BC1; vẫn **bắt lỗi FK NO_ACTION** làm lưới an toàn) · **cảnh báo** nếu DKKH chưa BC1 · xác nhận 2 bước (không hoàn tác) · **kiểm SP đổi khóa/xóa tồn tại, thiếu → tắt nút**; endpoint ghi buộc token operator | `TCB-04` | M | 63,65 | 1+2 | → PRD |

> SYNC-01 cắt 3 task (57/58/59) cùng trỏ 1 story → PRD `SYNC-01` chỉ ✅ khi xong cả 3 **và** task 62 (làm đẹp UI, CHANGES #34). Task **26** (đóng gói .exe) nay là **`DGT-01` thuộc Phase 5**, chạy **sau task 66** + 67-70.
> **Feature "Tra cứu CDB đích" (TCB-01..04, task 63-66, CHANGES #35):** mở rộng phân hệ Đồng bộ CDB — xem/sửa/xóa HV **trên DB đích** `GPLX_CDB_CSDT` ngay trong tool. Lát dọc: 63 màn+đọc → 64 thay ảnh → 65 sửa nhân thân → 66 xóa/đổi khóa. **Mốc khóa đọc Ở ĐÍCH** (độc lập DB Nạp): sửa nhân thân chặn khi DKKH (`SoQD_KhaiGiang`); xóa/đổi khóa chặn khi BC1 (`MaBC1`). Đã qua /reviewtdd (biên bản `tdd-review-04-10-2026-tcb.md`): mốc BC1=`MaBC1`, thay ảnh backup trước ghi đè, endpoint ghi buộc token operator.
> **Thứ tự build khuyến nghị (user chốt 04/10):** làm **61 → 62 TRƯỚC task 60** — HTG-07 tái cấu trúc header/sidebar (bỏ route `db-dich`), làm trước thì SYNC-03 (task 60, thêm màn Lịch sử) ráp vào shell đã ổn định, khỏi đụng route hai lượt.

### ✅ Checkpoint 12 — sau task 54-60 (module Đồng bộ CDB)
> **Kiểm 04/10/2026:** 265 pytest · E2E live tự-dọn trên CDB thật (tạo khóa test A1m → sync 3 HV A1K129 → verify → Hủy sync → xóa khóa; CDB về nguyên trạng 0/0/0, nhật ký test đã dọn). Ảnh/log E2E: happy-path + hủy sync xanh.
- [x] Sync thật 1 khóa nhỏ → HV vào CDB **khớp phần mềm**: MaDK `75032-20261004-000001..003` (21 ký tự), **SoHoSo SỐ THUẦN `001/002/003`** (zero-pad 3 — **đính chính: KHÔNG phải `B01`/CreateNewSoHoso**, verify DB thật), `NguoiTao=admin`. (E2E live 04/10)
- [x] HV đã có ở đích (theo SoCMT) → **skip** (không tạo hồ sơ 2); đúng PK(MaDK). (live: A1K129 vs CDB da_co_dich=2/150; C1-K14 da_co_dich=32/32)
- [~] **Backdate**: MaDK + 4 cột ngày đúng ngày quá khứ — **unit test phủ** (`test_sync_service`); E2E live dùng hôm nay, chưa chạy backdate live.
- [~] Khóa đích **đã BC1** → cảnh báo vẫn sync (B) — cờ `bc1` ở `dich/khoa` đã có; chưa dựng khóa BC1 test để E2E live.
- [x] **Hủy sync khóa** → xóa sạch HV tool tạo (E2E: hs_del=3, nlx_del=3, HV còn=0); TongSoHV về 0; nhật ký giữ. HV đã BC1 → **chặn 409** (unit `test_sync_rollback`).
- [~] Tiến trình **SSE** chạy (E2E: 3 sự kiện HV realtime) ✓; ngắt-trang-job-vẫn-xong: design/unit, chưa ngắt live.
- [x] **Regression Nạp**: sau đổi sidebar + bỏ route cau-hinh/db-dich — build+typecheck sạch, Playwright điều hướng OK (hành vi màn Nạp không đổi).
- [x] Playwright: cấu hình 1280/1440/1920 · Bàn đồng bộ 1280/1440 · Lịch sử 1440 — 0 tràn, header bảng dính (teal), 0 lỗi console.

### ✅ Checkpoint 13 — sau task 61-62 (cấu hình header + làm đẹp UI sync, CHANGES #34)
- [x] Icon ⚙ hiện trên header ở **mọi màn**; bấm mở panel cấu hình; đóng về đúng màn. (Playwright: mở từ Bàn đồng bộ/Lịch sử)
- [x] Panel chia **2 khối rõ**: ① kết nối + DB nguồn Nạp `GPLX_CSDT` · ② nhiều DB đích Sync — phân biệt được (review-giaodien + ảnh xác nhận).
- [x] "Kiểm tra kết nối": khối ② báo số NguoiLX (live "729 người lái"). (khối ① ping SQL+VPS — logic cũ HTG-01 không đổi)
- [x] Route cũ `/tool/cau-hinh` + `/sync/db-dich` **đã bỏ** khỏi sidebar/sub-nav (modules.ts + App.tsx); không còn link chết.
- [x] **Regression:** backend `/local/config*`+`/local/sync/targets` không đổi; 265 pytest + nạp/bàn đồng bộ chạy như cũ.

### ✅ Checkpoint 14 — sau task 63-66 (Feature Tra cứu CDB đích, TCB-01..04)
> **Kiểm live 04/10/2026 (máy dev, backend sạch 1 worker không --reload):** phần ĐỌC + các mốc CHẶN chạy đúng trên CDB thật qua `sqlserver_conn_dich`. **Luồng GHI happy-path hoãn nghiệm thu sang máy CSDT** (user chọn A): máy dev không truy cập được ổ ảnh `D:\GPLXCSDT\ANHCDUNG` (thay ảnh 404) và CDB thật **toàn khóa đã DKKH + BC1** nên không có target an toàn chạy sửa/xóa/đổi nhánh happy. **Feature GIỮ 🔄 — chưa chốt.** Nhất quán cách QLY-01/02/03/05 "⚠️ chờ verify máy CSDT".
- [~] Tra 1 khóa CDB thật → lưới HV + chi tiết + ảnh. Live: `/khoa` 15 khóa, `/ho-so` 32 HV (tên đủ dấu, SoHoSo sort đúng), `/chi-tiet-sua` nhân thân+ngày dd/mm/yyyy+HKTT đủ dấu đúng; **ảnh thiếu file → 404 "DB có đường dẫn nhưng file đã mất", không vỡ lưới** ✓. Còn: render ảnh thật + avatar lazy + đối chiếu "khớp phần mềm CDB" → **máy CSDT** (file ảnh không có ở máy dev).
- [~] Nút "Xem chi tiết HV": API `/khoa-cua-madk` trả **đúng khóa** chứa MaDK ✓. Còn phần tô sáng UI → cần webui/Playwright (ô dưới).
- [ ] **Thay ảnh (TCB-02)** → **HOÃN máy CSDT**: máy dev không có ổ `D:\GPLXCSDT` nên không ghi đè/`_BACKUP`/đối chiếu 2 DB được. (Code backup atomic chỉ-nếu-chưa-có đã đọc xác nhận.)
- [~] Sửa nhân thân (TCB-03): **CHẶN khi DKKH — live 409 đã chứng kiến** ("Khóa đã kết xuất DKKH … không sửa nhân thân qua tool", chặn trước UPDATE) ✓. Nhánh **chưa DKKH → sửa được: HOÃN máy CSDT** (CDB không có khóa nào chưa DKKH).
- [ ] **Xóa/đổi khóa (TCB-04)** → **HOÃN máy CSDT**: guard per-HV `MaBC1` không đọc được qua API nên không bắn thử an toàn ở máy dev; cần user chỉ HV chưa BC1 (hoặc tạo HV test tự dọn) trên máy CSDT.
- [~] **Mức 2:** đọc code xác nhận chặn đúng tín hiệu (`SoQD_KhaiGiang` cho sửa, `MaBC1` cho xóa/đổi — KHÔNG đọc `TT_XuLy`; backup ảnh chỉ-nếu-chưa-có) ✓; nhánh sửa-DKKH đã thấy live. Nhánh xóa/đổi live → cùng HOÃN.
- [~] Collector gọi endpoint TCB ghi → **403**: theo thiết kế, collector bị chặn ngay ở đăng nhập (`VAI_TRO_DUNG_TOOL`=operator/admin → mọi /local/* 401 vì không có phiên) — đọc code xác nhận; chưa có tài khoản collector để bắn live.
- [ ] Playwright 1280/1440/1920 màn Tra cứu CDB + modal chi tiết — 0 tràn. (Chưa chạy — thuần đọc, an toàn, chạy khi bật webui.)
- [x] Màn Bàn đồng bộ: combobox + danh sách HV **đẹp, tên đủ dấu, không tràn/cắt** (avatar + teal); Playwright 1280/1440 (150 HV) 0 tràn + review-giaodien đạt.

## Phase 5 — Đóng gói & khởi chạy tool độc lập (DGT-01..04)

> Feature DGT thêm ở CHANGES #38/#39 (sau /reviewtdd + /capnhat). Thiết kế: TDD §11C (+§11C.5 sơ đồ khởi động/vòng đời phiên) · §12 (refresh-token) · TDD-decisions §16. Mục tiêu: mang tool sang máy CSDT khác **không cần Python/Node**, mở như phần mềm thường, **đăng nhập 1 lần dùng mãi**.
> **DGT-01 = task 26** (ở bảng Phase 3, giữ số — dep "tất cả" nên luôn chạy cuối). Các task 67-70 thực thi SAU toàn bộ Phase 1-4 + TCB.

| # | Task | Story | Quy mô | Phụ thuộc | Kiểm | Xong |
|---|---|---|---|---|---|---|
| 67 | **DGT-02 Khởi chạy**: tự mở trình duyệt (uvicorn **bind `127.0.0.1`**) + khay `pystray` (Mở giao diện/Thoát, ẩn console `--windowed`) + **single-instance named mutex/lock-file** (mở lại → đưa về bản đang chạy, không bật bản 2) + dò cổng trống nếu bận + tùy chọn **tự chạy khi bật máy (mặc định TẮT)** | `DGT-02` | M | 26 | 1 | → PRD |
| 68 | **DGT-03 Wizard lần đầu**: nhận **3 trạng thái khởi động** ((a) chưa key.bin/config · (b) đủ → vào thẳng · (c) key.bin hỏng → wizard+cảnh báo) → stepper 3 bước (kiểm môi trường thư-mục-ghi-được + ping VPS → cấu hình SQL nguồn/đích + VPS **test-before-next** `/local/config/test` → đăng nhập), **tái dùng `CauHinhDrawer`** xếp thành stepper toàn màn; màn #20 SCREENS | `DGT-03` | M | 61,26 | 1 | → PRD ✅ 05/10 — tách `CauHinhForm` + `Wizard` 3 bước + redirect máy sạch + `/config/moi-truong` + **mở token sync-targets (bước mồi)**; build+tsc+34 vitest + 5 test backend; review-nghiepvu OK; **verify visual chrome-devtools 1280/1440 (console sạch)**. review-giaodien để Bước 7b |
| 69 | **DGT-04 (1/2) ⚠VPS server refresh-token**: `POST /api/auth/refresh` + bảng `refresh_token(user_id, token_hash, created_at, last_used_at, revoked)` **lưu HASH** + **xoay một-lần-dùng** (trả access+refresh mới, vô hiệu cũ, không TTL lịch) + **cửa sổ ân hạn** chống đá nhầm khi mạng chập chờn + `logout` xóa refresh token của phiên + `doi-mat-khau` **thu hồi toàn bộ** + kiểm `is_active`. **Deploy lại VPS** | `DGT-04 (1/2)` | M | 14 | 1+2 | [x] 05/10 — bảng `refresh_token` (hash) + `POST /api/auth/refresh` xoay 1-lần + ân hạn + thu hồi khi logout/đổi-mk/khóa-TK; 138 pytest (+11); review-nghiepvu 8/8. **Chờ deploy VPS (CP15)** |
| 70 | **DGT-04 (2/2) tool phiên vĩnh viễn**: lưu phiên + refresh token ra đĩa **mã hóa DPAPI (CurrentUser)** (ràng máy + tài khoản Windows) + nạp lại khi khởi động **bọc try/except** (hỏng → về màn đăng nhập) + **heartbeat** đổi refresh token định kỳ (khởi động + mỗi N giờ) + Đăng xuất xóa phiên đĩa+client. Vòng đời: TDD §11C.5 | `DGT-04 (2/2)` | M | 69,17 | 1+2 | [x] 05/10 — phiên đĩa DPAPI + nạp-lại-khi-khởi-động + heartbeat đổi refresh (3h) + đăng xuất xóa đĩa/thu hồi VPS; 296 pytest tool (+10); review-nghiepvu 9/9. **Verify live heartbeat chờ deploy VPS (CP15)** |

### ✅ Checkpoint 15 — sau task 26, 67-70 (Feature DGT) — **⚠ Deploy lại VPS (task 69)**
- [~] **DGT-01:** đóng gói exe → chạy trên **máy sạch** (không Python/Node) → nối SQL Server + VPS, nạp/tra cứu bình thường; dữ liệu ghi `%APPDATA%` (không `Program Files`). *(06/10/2026: ĐÃ build PyInstaller one-folder (`tool/tool.spec`) + tự kiểm trên máy dev PASS — `--selftest` OK pymssql/FreeTDS + rembg; server ~1,2s; data vào `%APPDATA%\pmcsdtlx-tool`; 299 test pass. CÒN chờ chạy trên máy sạch thật ở CSDT để tick xong.)*
- [~] **DGT-02:** nháy đúp exe → trình duyệt tự mở đúng trang + khay hiện; mở lại exe → **không bật bản 2**; cổng mặc định bận → nhảy cổng trống. *(06/10/2026: verify trên exe thật — windowed không console; trình duyệt tự mở nạp UI; mở lần 2 vẫn 1 tiến trình; 8000 bận→8001; 5 unit test launcher pass. CÒN chờ bấm khay tận tay ở máy CSDT.)*
- [ ] **DGT-03:** máy sạch → vào **wizard** 3 bước (test xanh mới qua); đã có cấu hình → vào thẳng; **key.bin hỏng → vào wizard** + cảnh báo.
- [ ] **DGT-04:** đăng nhập 1 lần → tắt/mở exe **vào thẳng**; **qua 8h vẫn kéo VPS được** (refresh ngầm); Đăng xuất → lần sau hỏi lại; admin khóa TK → **bị đá** khi refresh.
- [ ] **Mức 2:** refresh **xoay một-lần-dùng** + lưu **HASH** + `doi-mat-khau` thu hồi toàn bộ + **ân hạn** không đá nhầm khi retry refresh cũ (mạng chập chờn).
- [x] **Deploy VPS** (task 69 đổi `/api/auth`) → verify 3 vai trò + đăng nhập web không gãy ngay sau deploy. *(06/10/2026: CD đã đẩy sha HEAD; tạo tay bảng `refresh_token` trên Postgres prod (init.sql không chạy lại); login admin/thu1=200, sai MK=401, cap_refresh cấp token, /refresh xoay cặp mới, refresh bịa=401, khóa TK→refresh 401+thu hồi chuỗi, web /=200; prod dọn sạch token test. Chỉ có 2 vai trò trên prod (admin+collector) — login không rẽ theo vai trò nên đủ.)*

## Phase 6 — Cập nhật kết quả đào tạo (module KQD, module #3 sidebar)

> Feature SHOULD thêm ở CHANGES #42 (sau /capnhat + /reviewtdd §11D). Thiết kế: TDD §11D · TDD-decisions §17 · biên bản `tdd-review-07-10-2026.md` (verify SP/cột trên CDB thật). Ghi vào **CSDL đích GPLX_CDB_CSDT** (bảng `NguoiLX_HoSo`) qua SP có sẵn — **đọc `docs/DB-GPLX_CDB_CSDT.md` §5 + TDD §11D trước khi code**. Là **module #3** trong sidebar đã dựng ở task 54 (registry `MODULES` mở rộng N). Tái dùng hạ tầng CDB: băng DB đích + `sqlserver_conn_dich` (task 55). Tool CHỈ desktop. **Phạm vi: chỉ cập nhật KQĐT (`TT_XuLy` 03→09/10), KHÔNG kết xuất XML/gửi Sở.**

| # | Task | Story | Quy mô | Phụ thuộc | Kiểm | Xong |
|---|---|---|---|---|---|---|
| 71 | Workspace KQĐT vào sidebar (module #3) + **băng DB đích** dùng chung Sync + backend đọc qua `conn_dich` (SP `usp_NguoiLX_KetQuaDaoTao_CSDT_CNKQDT` lưới / `_GetHocVien` 1 HV — cả 2 trả `GiaiTrinh`/`DiemKQ*`, verify 07/10) + combobox khóa **chỉ đã BC1** + lọc 4 trạng thái (`03/04`·`09/10`·`14`·`90`) + ô tìm tên/CCCD. `routers/ketqua.py` + `ketqua_service.py` | `KQD-01` | M | 54,55 | 1 | → PRD |
| 72 | **KQD-02 (1/2) backend**: `ketqua_quydoi.py` (quy đổi 2 đoạn ngưỡng 5,0 + tham số LT theo hạng × cờ CŨ/MỚI: B CŨ 30/27·C1 35/32·B MỚI 50/45·C1 60/54) + tính 3 cờ Đạt **per-môn ≥5 trên điểm quy đổi THÔ chưa làm tròn** (làm tròn 1 chữ số chỉ khi hiển thị/ghi `DiemKQ*`) + giờ/km TT17 (giờ sân khóa cứng · km sân điền sẵn · đường gợi ý) + `SoGiayCNTN=MaDK+'-'+MaHangMoi` + **cờ CŨ/MỚI map `MaKH→cũ/mới` lưu phía tool** (SQLite/JSON như `dvhc_map`, mặc định CŨ) + `POST /local/ketqua/cap-nhat` ghi `usp_NguoiLX_KetQuaDaoTao_CSDT_CapNhat` (**18 tham số**) + **chặn gọi SP cho HV `12`/`13`** (SP không bảo vệ 12 → kéo lùi 12→09) | `KQD-02 (1/2)` | M | 71 | 1+2 | → PRD |
| 73 | **KQD-02 (2/2) UI**: form nhập điểm gốc 5 môn → hiện /10 bên cạnh + ô giờ/km (khóa cứng/điền sẵn/trống + cảnh báo vàng dưới ngưỡng) + tích cờ CŨ/MỚI theo khóa + **kết luận Đạt app tự tính (không gõ tay)** + validate vượt khung/thiếu điểm bắt buộc (ô đỏ) + dòng `12`/`13` chỉ-đọc nút Lưu mờ. Chạy `impeccable`+`ui-ux-pro-max` | `KQD-02 (2/2)` | M | 72 | 1 | → PRD |
| 74 | **KQD-03** tab "Theo dõi kết xuất" chỉ-đọc: Đã kết xuất XML (`TT_XuLy='12'`) / Chưa (đã `09` chưa `12`) map `@TTKetXuat` của SP lưới; **không nút kết xuất**, không sinh XML, không đổi `TT_XuLy` | `KQD-03` | S | 71 | 1 | → PRD |
| 75 | **KQD-04** sửa lại HV `14`/`90`: mở lại form sửa điểm (reuse KQD-02) + ô nhập **giải trình** → ghi `GiaiTrinh` bằng `UPDATE` tham số hóa riêng (pymssql `%s`, validate ≤1000) **chạy TRƯỚC `_CapNhat`** cùng `conn_dich` + hiển thị `LyDoTuChoiKQDT` (read SP không trả → `SELECT` riêng); SP giữ nguyên `14`/`90`. KHÔNG áp cho `12`/`13` | `KQD-04` | M | 73,72 | 1+2 | → PRD |
| 76 | **KQD-05 (1/2) backend**: `POST /local/ketqua/mo-khoa` — cổng B-1 (`EXISTS TRANS_CLI_HangDoiGui WHERE KieuDuLieu='KET_QUA_DAO_TAO' AND NoiGui=@MaCSDT AND TrangThai='0'`, lọc `NoiGui` không parse tên file) → còn gói chưa gửi thì xóa từng gói qua `usp_TRANS_CLI_HangDoiGui_Delete` + **lùi MỌI HV `12` của CƠ SỞ (mọi khóa)** 1 `UPDATE` tham số hóa `WHERE MaCSDT=@MaCSDT AND TT_XuLy='12' AND KetLuanCSDT IS NOT NULL` (CASE 1→'09'/0→'10', `NgaySua=GETDATE()`; HV 12 kết luận NULL → bỏ qua + cảnh báo) + ghi `GiaiTrinh` nếu UI gửi; hết gói chưa gửi → **409** kèm danh sách gói đã gửi (M1). Ngoại lệ DUY NHẤT gỡ chặn `12`; `13` tuyệt đối không. +`GET /mo-khoa` cổng B-1 cho UI. `routers/ketqua.py` | `KQD-05 (1/2)` | M | 71 | 1 | [x] |
| 77 | **KQD-05 (2/2) UI**: nút "Mở khóa để sửa" ở **CẢ 2 tab** (dòng 🔒 HV `12` ở KQD-02 + tab KQD-03) + modal 2 ca bám mock `ui-mock/theodoiketxuat.html` — ca mở được (xóa gói + báo "toàn bộ HV của cơ sở N người · M khóa") / ca khóa cứng M1 (liệt kê gói đã gửi + "không xác định HV nằm gói nào") + ô lý do → `GiaiTrinh`. Chạy `impeccable`+`ui-ux-pro-max` | `KQD-05 (2/2)` | M | 76,73,74 | 1 | [x] |
| 78 | **KQD-06** sửa lẻ / xóa điểm đã lưu (HV chưa kết xuất 09/10): **sửa lẻ** — `ket_qua_hon_hop` ghi lại 1/vài môn, các môn không sửa **GIỮ điểm quy đổi đã lưu** (truyền lại quy đổi /10, KHÔNG tính ngược ra gốc để tránh lệch làm tròn); Lưu không bắt đủ 5 ô + **xóa điểm** `POST /local/ketqua/xoa-diem` đưa HV về `TT_XuLy='03'` + NULL 5 `DiemKQ*` + 3 cờ (`KQLyThuyet`/`KQThucHanh`/`KetLuanCSDT`) + `SoGiayCNTN` bằng **UPDATE trực tiếp tham số hóa** (SP `_CapNhat` chỉ đặt 09/10, không lùi 03 — verify 07/10); chỉ 09/10 (**409** nếu 12/13/14/90). UI `CapNhatKQDT.tsx`: Lưu nhận sửa lẻ + nút "Xóa điểm" có xác nhận. +4 unit test (340 pytest). `routers/ketqua.py` + `ketqua_quydoi.py` | `KQD-06` | M | 72,73 | 1 | [x] |

> KQD-02 cắt 2 task (72/73) cùng trỏ 1 story → PRD `KQD-02` chỉ ✅ khi xong cả 2. Tái dùng SP đã verify 07/10 trên `GPLX_CDB_CSDT` (biên bản `tdd-review-07-10-2026.md`): SP ghi 18 tham số, SP không bảo vệ `12`, cột `GiaiTrinh nvarchar(1000)` ghi ngoài SP.
> KQD-05 cắt 2 task (76/77) cùng trỏ 1 story → PRD `KQD-05` chỉ ✅ khi xong cả 2. Thao tác **mức CƠ SỞ** (user chốt phương án A sau /reviewtdd 07/10 — DB không nối HV↔gói nên xóa gói buộc quét cả CSĐT; biên bản `tdd-review-07-10-2026-kqd05.md`, TDD §11D.7, decisions §19). Ghi/xóa thật ở CDB → **nghiệm thu máy CSDT**.
> KQD-06 (task 78) **đã code trước khi ghi sổ** (user chốt phương án A gộp 1 story 07/10): sửa lẻ **giữ quy-đổi môn cũ** + xóa điểm reset `03` bằng **UPDATE trực tiếp** (SP không lùi 03 được) — chỉ áp HV `09/10`. TDD §11D.8, CHANGES #48. Ghi/xóa thật ở CDB → **nghiệm thu máy CSDT**.

### ✅ Checkpoint 16 — sau task 71-78 (module KQD)
- [ ] Chọn 1 khóa đã BC1 → lưới HV đúng 4 trạng thái; khóa chưa BC1 không hiện trong gợi ý; khóa rỗng → lưới rỗng có thông báo.
- [ ] **Mức 2** (unit quy đổi): khớp "Sổ theo dõi KQ TT17" (LT 28/30(ng.27)→6,7 · liên hoàn 84→6,0 · đường 85→6,3); **ranh giới làm tròn** (sa hình gốc 79,2→quy đổi 4,95 = **Trượt**, không làm tròn thành 5,0 rồi tính Đạt); 3 cờ Đạt per-môn đúng; tham số LT đổi theo cờ CŨ/MỚI của khóa.
- [ ] Ghi 1 HV đạt → mở phần mềm CDB đối chiếu điểm/`TT_XuLy`=09/`SoGiayCNTN` khớp.
- [ ] HV `12`/`13` → nút Lưu mờ, **không gọi SP** (không kéo lùi 12→09).
- [ ] KQD-04: HV `14`/`90` → sửa điểm + nhập giải trình → `GiaiTrinh` ghi được, mở lại thấy; lỗi bước GiaiTrinh thì điểm/trạng thái **chưa đổi** (HV vẫn 14/90).
- [ ] **KQD-05 cổng B-1:** cơ sở còn gói `NoiGui=@MaCSDT TrangThai='0'` → nút "Mở khóa" bật ở cả 2 tab; chỉ còn gói CSĐT khác (lẫn máy) → nút tắt (khóa cứng, không đụng gói lạ).
- [ ] **KQD-05 mở khóa (mức cơ sở):** bấm mở → mọi gói chưa gửi của cơ sở bị xóa + **mọi HV `12` của cơ sở (nhiều khóa) về 09/10**; HV `12` mà `KetLuanCSDT` NULL → bỏ qua, không bị ép '10'. Gói đã gửi hết → 409 + thông báo mức đợt M1, **không đổi gì**. `13` không mở được.
- [ ] **KQD-06 sửa lẻ:** HV `09/10` sửa 1 môn → Lưu (không bắt đủ 5 ô) → mở lại thấy môn sửa đổi, **các môn khác giữ nguyên điểm quy đổi cũ** (không lệch làm tròn).
- [ ] **KQD-06 xóa điểm:** nút "Xóa điểm" dòng HV `09/10` → xác nhận → HV về `03` + sạch 5 điểm/3 cờ/`SoGiayCNTN`, rời lọc "Đã cập nhật"; HV `12/13/14/90` → **không có nút / 409** (không đụng).
- [ ] Playwright desktop (1280/1440) workspace KQĐT + form sửa + **modal mở khóa 2 ca** — 0 tràn.
- [ ] **Ghi thật/đối chiếu phần mềm CDB → nghiệm thu ở máy CSDT** (máy dev CDB toàn khóa đã BC1/DKKH; nhất quán cách TCB/QLY "⚠️ chờ verify máy CSDT").

## Phase 7 — Lối nhập OCR dự phòng (THU-06)

> Feature MUST thêm ở CHANGES #49 (sau BUG-14 — iPhone/iOS quét QR CCCD yếu; probe fail mọi engine web → QR iPhone là ngõ cụt, OCR thay hẳn). Thiết kế: TDD §6.7 (v5.8 — engine chốt) · TDD-decisions §20 · biên bản `tdd-review-07-10-2026-thu06.md`. **Thuần app web (webapp)** — KHÔNG đụng tool/VPS luồng ghi; tái dùng màn xác nhận + luồng gửi (idempotent UUID, nháp offline) của THU-01/02. **Engine chốt:** Tesseract.js client-side (ảnh KHÔNG rời máy — rào cứng PII), tách trường = OCR toàn ảnh + regex theo nhãn.

| # | Task | Story | Quy mô | Phụ thuộc | Kiểm | Xong |
|---|---|---|---|---|---|---|
| 79 | **Nền OCR (lib)**: tích hợp Tesseract.js + dữ liệu `vie` vào webapp; `lib/ocr.ts` — downscale ảnh ≤~1600px → chạy Tesseract (client/worker) → trả text; **tách 5 trường mặt trước bằng regex theo nhãn** in trên thẻ ("Số/No.", "Họ và tên", "Ngày sinh", "Giới tính", "Nơi thường trú"; **ngày cấp ở mặt sau → không đọc, nhân viên nhập tay** — chốt A); chuẩn hóa hạ nguồn qua helper `lib/qr.ts` (ddMMyyyy→yyyymmdd, độ dài tên, parse địa chỉ 2 cấp); **mốc fail = CCCD 12 số hợp lệ** (không có → fail không điền gì); **hủy ảnh thẻ khỏi bộ nhớ sau khi đọc** (trừ khi tái dùng cắt chân dung). +unit test tách trường | `THU-06 (1/2)` | M | 13,18 | 1+2 | [x] 07/10 — `lib/ocr.ts` (Tesseract.js client + downscale ≤1600 + regex theo nhãn + mốc fail CCCD 12 số + ngày cấp rỗng theo chốt A) + 6 unit test (34 vitest) + build sạch. OCR thẻ thật = mức 1, chờ Checkpoint 17 |
| 80 | **Lối vào "Chụp ảnh thẻ (tự đọc)" + luồng UI**: thêm lựa chọn thứ 3 ở màn vào `/app/quet` (mọi thiết bị, không khóa theo máy) → chụp/tải ảnh mặt trước CCCD → gọi `ocr.ts` (spinner tiến trình + **hủy → Nhập tay**) → điền **màn xác nhận dùng chung** (THU-01/02), trường thiếu/không-chắc **đánh dấu để soát**, **không auto-submit** → lưu qua luồng gửi sẵn có; ảnh fail → báo rõ, không điền bừa, về Nhập tay/Quét QR. Chạy `impeccable` | `THU-06 (2/2)` | M | 79,17,19 | 1 | [ ] |

> THU-06 cắt 2 task (79/80) cùng trỏ 1 story → PRD `THU-06` chỉ ✅ khi xong cả 2 **và** kiểm tay trên thẻ+điện thoại thật (Checkpoint 17). Engine OCR + tách trường đã chốt ở `/tdd` (TDD §6.7 v5.8). **Mở kiểm:** độ chính xác tiếng Việt có dấu của Tesseract.js trên thẻ thật — quá thấp thì tăng sửa tay hoặc xin phê duyệt pháp lý cho eKYC ngoài (qua `/capnhat`).

### ✅ Checkpoint 17 — sau task 79-80 (THU-06 OCR)
- [ ] Màn vào có lối **"Chụp ảnh thẻ (tự đọc)"** trên **mọi thiết bị** (iPhone/Android/desktop), không khóa theo máy.
- [ ] **Mức 2** (unit tách trường regex): ảnh đủ nhãn → **5 trường mặt trước** đúng (ngày sinh ddMMyyyy→dd/mm/yyyy); không đọc được CCCD 12 số → **fail, không điền trường nào**; nơi thường trú 2 cấp / xuống dòng → ghép dòng, giữ dấu tiếng Việt; **ngày cấp luôn trống + đánh dấu** (nhập tay). ✅ đã có 6 unit test task 79.
- [ ] **Mức 1 (BẮT BUỘC thẻ thật + điện thoại thật — như AS-001/BUG-14):** chụp CCCD rõ → điền sẵn đúng trường; ảnh mờ/OCR fail → báo rõ, không điền bừa; CCCD sai chữ số → ô đỏ validate 12 số; nhân viên **sửa được từng trường** trước khi lưu (màn xác nhận không auto-submit).
- [ ] Ảnh CCCD **không rời máy** (OCR client-side); ảnh **hủy khỏi bộ nhớ sau khi đọc** (trừ khi tái dùng cắt chân dung); không log đầu ra OCR.
- [ ] Playwright webapp 375/800/1440 màn vào + luồng OCR (dùng ảnh mẫu) — 0 tràn.

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

- **Số story trong PRD khi cập nhật:** 44 (thêm `THU-06` từ CHANGES #49; `KQD-06` #48; `KQD-05` #45; trước đó `KQD-01/02/03/04` #42; `DGT-01/02/03/04` #38/#39; `TCB-01/02/03/04` #35; `HTG-07` #34; `SYNC-01/02/03` #33; chưa tính NICE `QLY-04`, `THU-03`)
- **Mã story đã đưa vào kế hoạch:** `HTG-01`, `HTG-02`, `HTG-03`, `HTG-07`, `THU-01`, `THU-02`, `THU-04`, `THU-05`, `THU-06`, `NAP-01`…`NAP-06`, `KHO-01`, `QLY-01`, `QLY-02`, `QLY-03`, `QLY-05`, `QLY-06`, `QLY-07`, `QLY-08`, `QLY-09`, `SYNC-01`, `SYNC-02`, `SYNC-03`, `TCB-01`, `TCB-02`, `TCB-03`, `TCB-04`, `DGT-01`, `DGT-02`, `DGT-03`, `DGT-04`, `KQD-01`, `KQD-02`, `KQD-03`, `KQD-04`, `KQD-05`, `KQD-06`
- **Mã story chưa đưa vào:** `QLY-04`, `THU-03` (NICE, chưa đủ chi tiết) · **`HTG-04/05/06`** (thêm ở CHANGES #18, đã code thẳng — chưa có task trong plan; cần `/kehoach` bổ sung riêng nếu muốn khớp sổ)
- **Đã đọc `docs/CHANGES.md` tới dòng ngày:** 07/10/2026 (#49)

## Changelog

| Ngày | Thay đổi |
|---|---|
| 07/10/2026 | v19 — sửa (CHANGES #50, /capnhat — phát hiện khi build task 79): THU-06 OCR **chỉ đọc 5 trường mặt trước** (bỏ *ngày cấp* — in ở mặt sau, không chụp; nhân viên nhập tay, user chốt A). Sửa mô tả task 79 + Checkpoint 17 (mức 2: 5 trường + ngày cấp luôn trống). Task 79 đã code đúng (5 trường). Không đổi số task. 80 task. |
| 07/10/2026 | v18 — bổ sung (CHANGES #49, sau /reviewtdd §6.7 + /tdd): thêm **Phase 7 Lối nhập OCR dự phòng (THU-06)** — task **79** nền OCR `lib/ocr.ts` (Tesseract.js client + dữ liệu `vie`, downscale ≤~1600px, tách 6 trường regex theo nhãn, mốc fail CCCD 12 số, hủy ảnh sau đọc, +unit test) + task **80** lối vào "Chụp ảnh thẻ (tự đọc)" + luồng UI (spinner/hủy, màn xác nhận dùng chung không auto-submit, lưu qua luồng gửi sẵn có) + Checkpoint 17. **Thuần webapp**, không đụng tool/VPS; engine chốt Tesseract.js client-side (rào PII, TDD §6.7 v5.8). +1 story THU-06. 80 task. |
| 07/10/2026 | v17 — bổ sung (CHANGES #48, **đã code trước khi ghi sổ**): thêm **KQD-06 "Sửa lẻ / xóa điểm đã lưu"** vào cuối Phase 6 — task **78** (backend `ket_qua_hon_hop` giữ quy-đổi môn cũ + `POST /local/ketqua/xoa-diem` reset `03` bằng UPDATE trực tiếp, chỉ 09/10, 409 khác + UI nút Xóa điểm có xác nhận; +4 unit test, 340 pytest). Checkpoint 16 mở rộng 71→78 + 2 mục kiểm KQD-06 (sửa lẻ giữ môn cũ · xóa về 03). User chốt phương án A gộp 1 story; TDD §11D.8. +1 story. 78 task. |
| 07/10/2026 | v16 — bổ sung (CHANGES #45, sau /reviewtdd KQD-05): thêm **KQD-05 "Mở khóa để sửa điểm sau kết xuất"** vào cuối Phase 6 — task **76** backend (`POST /local/ketqua/mo-khoa`: cổng B-1 `EXISTS NoiGui=@MaCSDT TrangThai='0'` + xóa gói chưa gửi + `UPDATE` lùi **mọi HV 12 của CƠ SỞ** guard `KetLuanCSDT IS NOT NULL` + 409/M1) + task **77** UI (nút 2 tab + modal 2 ca bám mock). Checkpoint 16 mở rộng 71→77 + 2 mục kiểm KQD-05. Thao tác **mức cơ sở** (phương án A — DB không nối HV↔gói; biên bản tdd-review-07-10-2026-kqd05). +1 story. 77 task. |
| 07/10/2026 | v15 — bổ sung (CHANGES #42, sau /reviewtdd §11D): thêm **Phase 6 Cập nhật kết quả đào tạo (KQD)** task **71-75** — workspace KQĐT module #3 sidebar + đọc CDB (71, KQD-01) · KQD-02 cắt 2: backend quy đổi/Đạt per-môn điểm thô/giờ-km TT17/cờ CŨ-MỚI phía tool/ghi _CapNhat 18 th.số chặn 12-13 (72) + UI form (73) · tab Theo dõi kết xuất chỉ-đọc (74, KQD-03) · sửa HV 14/90 + ghi GiaiTrinh UPDATE riêng trước SP (75, KQD-04) + Checkpoint 16. Verify SP/cột trên CDB thật (biên bản tdd-review-07-10-2026). +4 story KQD. 75 task. |
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
| 04/10/2026 | v12 — bổ sung (CHANGES #34): thêm task **61** (HTG-07 bảng cấu hình chung ở header, gộp DB nguồn Nạp + nhiều DB đích Sync, bỏ route cau-hinh/db-dich — đóng HTG-07 + SYNC-02) + task **62** (SYNC-01 làm đẹp combobox + danh sách HV) + Checkpoint 13. Thuần UI/IA, backend không đổi; dựng impeccable/ui-ux-pro-max. Khuyến nghị build 61→62 trước task 60. +1 story HTG-07. 62 task. |
| 05/10/2026 | v14 — bổ sung (CHANGES #38/#39, sau /reviewtdd + /capnhat): thêm **Phase 5 Đóng gói & khởi chạy tool (DGT)** — gán **task 26 → `DGT-01`** (đóng gói exe + serve dist + %APPDATA%, giữ số) + task **67** DGT-02 khởi chạy (tự mở trình duyệt+khay+single-instance mutex+dò cổng+tự-chạy mặc định TẮT) · **68** DGT-03 wizard 3-trạng-thái tái dùng CauHinhDrawer · **69** ⚠VPS DGT-04(1/2) server refresh-token (lưu HASH, xoay 1-lần-dùng, ân hạn, thu hồi khi logout/đổi-mk) · **70** DGT-04(2/2) tool phiên đĩa DPAPI+heartbeat + Checkpoint 15. +4 story DGT-01..04. 70 task. |
| 04/10/2026 | v13 — bổ sung (CHANGES #35, sau /reviewtdd): thêm Feature **Tra cứu CDB đích** task **63-66** (cuối Phase 4, trước task 26) — màn Tra cứu CDB + đọc qua `sqlserver_conn_dich` + nút Xem chi tiết (63, TCB-01) · thay ảnh backup `_BACKUP.jp2` trước ghi đè (64, TCB-02) · sửa nhân thân chặn DKKH (65, TCB-03) · xóa/đổi khóa chặn BC1=`MaBC1` (66, TCB-04) + Checkpoint 14 + Prerequisite kiểm SP CDB. Mốc chặn đọc Ở ĐÍCH, đã nhúng kết quả review (biên bản `tdd-review-04-10-2026-tcb.md`). Task 26 nay sau task 66. +4 story TCB. 66 task. |
| 04/10/2026 | v11 — bổ sung (CHANGES #33): thêm **Phase 4 Đồng bộ CDB** task **54-60** — sidebar workspace shell (54), Sync nền backend config/conn_dich/sync_helpers/sync_history (55), SYNC-02 Quản lý CSDL đích (56), SYNC-01 cắt 3: backend tạo HV qua 3 SP + MaCSDT từ QTHT/khóa đích (57) · SSE+chạy (58) · UI Bàn đồng bộ bám mock (59), SYNC-03 Lịch sử & Hủy sync (60) + Checkpoint 12 + prerequisite MaGT identity. Khóa đích BC1: cảnh báo-vẫn-cho (user chốt B). Task 26 đóng gói nay sau task 60. +3 story SYNC. 60 task. |
