# Kế hoạch build — PMCSĐTLX Thu nhận hồ sơ học viên

> File do `/kehoach` sinh. `/tieptheo` đọc file này để biết làm gì tiếp theo.
> **Thứ tự code** nằm ở đây. **Yêu cầu và trạng thái story** nằm ở `docs/PRD.md`.
> Cập nhật lần cuối: 02/11/2026 (v31 — +Phase 12 task 149-154 GPLX đã có, CHANGES #81-#82; trước đó v30 — +Phase 11 task 146-148 "Chọn in GPLX", CHANGES #79; trước đó v29 — mô tả task 137/139/140/141 theo `/reviewtdd` §11D.13, CHANGES #78; trước đó v28 — thêm task 136-145 + Checkpoint 34/35 cho `KQD-04` đổi (14→90 + giải trình hàng loạt), CHANGES #77). Trước đó 12/10/2026 (v27 — thêm task 127-135 + Checkpoint 33 cho `KQD-09` xuất Excel kết quả học tập và `KQD-10` xuất Sổ theo dõi (mẫu Phụ lục VI) (CHANGES #72-#76); trước đó v26 — thêm task 123-126 (126 đã đóng gói exe, selftest đạt) + Checkpoint 32 cho `KQD-08` nạp giờ/km đường từ PDF DAT + phần đổi của `KQD-02` (CHANGES #69-#70); trước đó v25 — thêm task 118-122 + Checkpoint 29-31 cho QLY-07 sửa ghi ảnh, KQD-07, PCG-06; trước đó v24 — thêm task 116-117 (110b) + Checkpoint 28; trước đó v23 — Phase 10 Tốt nghiệp & Báo cáo 2 TNB-01..07, task 96-115, CHANGES #60-#62, TDD §11F v6.8. Trước đó v22 — Phase 9 Phân công GV – xe PCG-01..05, task 85-95, CHANGES #54. Trước đó v21 — KQD-05 mở rộng "Sửa sau gửi" #53, task 83-84. Trước đó v20 — Phase 8 NAP-01 #51 "Bỏ khỏi hàng đợi" dòng chờ/lỗi + tombstone, task 81-82. Trước đó v19 — THU-06 chỉ OCR 5 trường (CHANGES #50); v18 — Phase 7 THU-06 task 79-80)

## Quyết định về thứ tự

- **Risk-first (theo TDD §17):** làm **Tool nạp DB trước** vì đây là mắt xích khó & rủi ro cao nhất — sinh `SoHoSo` qua `sp_getapplock`, gọi **1 SP gộp app cũ** `usp_QuangLA_...ThemMoiCapNhat`, ghi ảnh hướng A riêng (UPDATE 5 cột), xuất `.jp2` khớp app cũ. Hỏng chỗ này ở cuối dự án = làm lại từ đầu; nên chứng minh sớm bằng **nạp tay 1 HV** (AS-003) rồi mới dựng đường thu thập. *(01/10 — đổi 3 SP rời → 1 SP gộp, bỏ compensation vì SP atomic; xem CHANGES #4/#5.)*
- **Đảo ưu tiên có chủ đích (Luật 2 > Luật 3):** vài story **MUST** (`KHO-01`, `HTG-03`) nằm ở Phase 3 vì độc lập, rủi ro thấp, không nằm trên đường chứng minh lõi (DB đã có khóa thật + hồ sơ thật để test NAP). SHOULD `QLY-*` cũng Phase 3 vì phụ thuộc `NAP-05`.
- **`HTG-01` cắt 3 task theo nơi chạy:** ① cấu hình kết nối tool (local, Phase 1) · ② auth JWT trên VPS (Phase 2) · ③ login UI + tool gate (Phase 2). PRD chỉ chuyển ✅ khi xong cả 3.
- **`NAP-05` và `HTG-02` cắt đôi** để không còn task cỡ L.
- **1 người build → tuần tự một luồng**, không tách nhánh song song (quyết định chủ dự án 01/10/2026).
- **Phase 4 Đồng bộ CDB (task 54-60) — module mới tách khỏi Nạp:** SHOULD, xếp cuối sau mọi task Nạp/thu thập (không đảo lên MUST). Đổi `ToolLayout`→sidebar (task 54) đụng chrome dùng chung → chạy một mình, nhưng **hành vi màn Nạp không đổi** (không hạ story Nạp). Ghi vào CSDL đích GPLX_CDB_CSDT (≠ CSDL Nạp) → module backend tách (`sync_*`), không import Nạp. Tạo HV **qua 3 SP chuẩn CDB** + MaCSDT từ `QTHT.MA_CSDT`/khóa đích (đã phân tích DB: `docs/DB-GPLX_CDB_CSDT.md`). Khóa đích đã BC1: **cảnh báo, vẫn cho sync** (user chốt B 04/10) — khác NAP-02 chặn cứng, vì sync là thao tác bù dữ liệu chủ động.
- **KQD (task 71-78, Phase 6) — module #3 "Cập nhật kết quả đào tạo":** xếp sau DGT vì là module mới hoàn toàn, tái dùng hạ tầng CDB đã ổn định (sidebar task 54 + `conn_dich`/config đích task 55). Cắt KQD-02 làm 2 task (72 backend quy đổi/Đạt/ghi · 73 UI form) và KQD-05 làm 2 task (76 backend mở-khóa · 77 UI) tránh cỡ L (nhiều tiêu chí Done); KQD-06 (task 78) sửa lẻ/xóa điểm gộp 1 task. KQD-05 "Mở khóa để sửa sau kết xuất" thao tác **mức CƠ SỞ** (DB không nối HV↔gói). Chỉ ghi KQĐT (`TT_XuLy` 03→09/10, riêng KQD-05 lùi 12→09/10, KQD-06 lùi 09/10→03 khi xóa điểm), KHÔNG kết xuất XML. Mọi ghi thật đối chiếu phần mềm CDB → nghiệm thu máy CSDT (như TCB/QLY).
- **Phase 10 TNB (task 96-115) — phân hệ #5 "Tốt nghiệp & Báo cáo 2", ghi DB Nạp `GPLX_CSDT` dùng chung với PM cũ:** risk-first như Phase 9 — luật thuần (96) rồi backend (97-105) **trước** UI (106-115), vì ghi thẳng DB thật mà PM cũ đang dùng, hỏng sau khi dựng UI là làm lại cả hai. Chỉ gọi SP có sẵn, không INSERT/UPDATE/DELETE trực tiếp. TNB-04 cắt 6 task (luật · đọc ứng viên · ghi lô · UI ① · UI ② · UI ③), TNB-01 cắt 3, TNB-02/03/05/06/07 cắt 2 — không task nào cỡ L. Cả 7 story cùng nhóm, không có đảo MUST/SHOULD. Ghi thật → nghiệm thu máy CSDT (Checkpoint 27).
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
- **SQL login của tool ở DB Nạp có `EXECUTE` trên 7 SP của TDD §11F.1** (`usp_NguoiLX_HoSo_Update_CNTN`, `usp_BaoCaoII_Insert`, `usp_BaoCaoII_Delete`, `usp_NguoiLX_HoSo_ThemHS_BC2`, `usp_NguoiLX_Update_ThemHSBC2`, `usp_NguoiLXHoSo_Update_DanhSachHocSinhBC2`, `usp_NguoiLX_HoSo_UpdateTTXLy`) và `sp_getapplock` — cần trước **task 98**.
- **Chụp trước/sau PM cũ** (1 HV + 1 BC2 thử: `NgaySua`, `NguoiSua`, `Transfer_flag` và cột khác PM cũ chạm) — cần trước **task 99/102** để biết SP + cột chính xác (TDD-decisions §23 "Còn mở").
- **Quy tắc số giấy CNTN liên tiếp** (`N1|7282` → ?) và số sổ/quyết định theo khóa — cần trước **task 107**; chưa rõ thì mặc định nhập tay từng ô (nhân viên luôn sửa được).
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
| 118 | **Sửa ghi ảnh đổi nền cả khóa (QLY-07, CHANGES #67):** `tool/app/doinen.py` (`xu_ly_mot`, `_backup_neu_chua`) ghi đè atomic **tại `DuongDanAnh` hiện có** (rút chung hàm ghi đè của `thay_anh_ghi_de` — `routers/sync_tracuu.py` — ra module dùng chung, KHÔNG import router), bỏ `ghi_anh_update` + bỏ UPDATE `DuongDanAnh`; sao lưu `<tên>_BACKUP.jp2` cùng thư mục, chỉ-nếu-chưa-có (bỏ thư mục `<khóa>\_BACKUP\`); chỉ UPDATE `ChatLuongAnh`/`NgayThuNhanAnh`/`NguoiThuNhanAnh`, giữ `TT_XuLy`; cập nhật `tests/test_doinen.py` (ảnh ở gốc khác vẫn ghi đúng chỗ, `DuongDanAnh` không đổi, backup chỉ-nếu-chưa-có, `TT_XuLy` giữ). `nap.py` `ghi_anh_update` giữ nguyên (chạy `impact` trước) | `QLY-07` | M | 40, 64 | 1+2 | [x] 12/10 — `anh_file.ghi_de_tai_cho` dùng chung (cả `thay_anh_ghi_de`) · `doinen.py` bỏ `ghi_anh_update`/IMG_PATH_CSDT · tool 668 pytest · chờ nghiệm thu máy CSĐT (Checkpoint 29) |

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

### ✅ Checkpoint 29 — sau task 118 (QLY-07 ghi đè tại `DuongDanAnh`, CHANGES #67)
- [ ] **Mức 2:** ảnh ở gốc khác `IMG_PATH_CSDT` (UNC / `Capmoi`) ghi đè TẠI CHỖ, `DuongDanAnh` **không đổi**; backup `<tên>_BACKUP.jp2` chỉ-nếu-chưa-có (chạy lần 2 không đè); `TT_XuLy` giữ nguyên (kể cả khóa đã BC2); HV không file → bỏ qua.
- [ ] `pytest` toàn bộ pass; nạp/thay ảnh HV mới (QLY-05) vẫn dùng `ghi_anh_update` như cũ.
- [ ] **Nghiệm thu máy CSĐT:** chạy 1 khóa thật → mở ảnh ở **cả 2 DB** thấy cùng ảnh nền trắng; kiểm máy CSĐT xem bản cũ đã sinh file/thư mục `_BACKUP` theo khóa chưa (không tự xóa).

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
| 83 | **KQD-05 mở rộng (1/2) backend "sửa sau gửi"** (CHANGES #53): `POST /local/ketqua/mo-sua-sau-gui` (body `ma_dk[]` ≤200 + `ly_do` ≤1000) — còn gói chưa gửi → **409** `con_goi_chua_gui`; ghi nhật ký sqlite `sua_sau_gui` (điểm trước · lý do · người · giờ) **TRƯỚC**; rồi UPDATE tham số hóa từng `MaDK` lùi `12`→09/10 theo `KetLuanCSDT`, guard `TT_XuLy='12' AND KetLuanCSDT IS NOT NULL`, `13`→409, ghi `GiaiTrinh`, **không xóa gói**; `GET /local/ketqua/sua-sau-gui` (nhật ký ∩ HV chưa về `12`, tự đánh đã-kết-xuất-lại). Tái dùng `_SQL_GOI_KQDT` (task 76) + mẫu `xoa_diem` (SELECT trước, không tin `rowcount`); +unit test guard/409/nhật-ký-trước. `routers/ketqua.py` + module sqlite nhật ký | `KQD-05 (+1/2)` | M | 76,78 | 1+2 | [x] |
| 84 | **KQD-05 mở rộng (2/2) UI "sửa sau gửi"**: lưới KQD-02 — ô tích HV `12` + chip xám "Đã gửi Sở" + thanh "Mở sửa điểm" + hộp xác nhận (danh sách HV+điểm, cảnh báo, lý do bắt buộc, tích "sẽ kết xuất lại ngay") + chip cam "Sửa sau gửi — chưa kết xuất lại" + băng cam đầu khóa; tab KQD-03 — khối đỏ "chờ kết xuất lại" (HV·khóa·người·lúc mở·lý do·điểm trước→sau); sửa `MoKhoaModal` ca "gói đã gửi hết" dẫn sang lối này thay khóa cứng M1. Chạy `impeccable`+`ui-ux-pro-max`. `CapNhatKQDT.tsx`, `TheoDoiKetXuat.tsx`, `MoKhoaModal.tsx`, `lib/api.ts` | `KQD-05 (+2/2)` | M | 83,77,73,74 | 1 | [x] |
| 119 | **KQD-07 backend (CHANGES #65, TDD §11D.9):** luật thuần `hv_chua_du` cạnh `ketqua_quydoi.py` (chưa có điểm · thiếu môn bắt buộc theo hạng · thiếu giờ/km thực hành · thiếu kết luận; giờ/km đường dưới ngưỡng gợi ý KHÔNG vào lý do) + **nguồn chung "môn bắt buộc theo hạng" ở backend** + `GET /local/ketqua/kiem-truoc?ma_kh` (chỉ đọc, dùng lại hàm đọc HV của `/hoc-vien`, chỉ HV `TT_XuLy` 03/04/09/10) + unit test | `KQD-07 (1/2)` | M | 73 | 1+2 | [x] 12/10 — `hv_chua_du` + `la_mo_to` (`ketqua_quydoi.py`) · `GET /kiem-truoc` dùng chung `_doc_hv_khoa` · +4 cột giờ/km ở `_SQL_HV` · user chốt: chỉ hạng ô tô, 5 môn bắt buộc, chỉ cảnh báo · tool 681 pytest |
| 120 | **KQD-07 UI (cần mock `/prototype-next` trước):** nút "Kiểm trước kết xuất" ở màn Cập nhật KQĐT sau khi chọn khóa + khung kết quả (tóm tắt đủ/thiếu, chip lý do, bấm dòng mở HV ở lưới nhập điểm, "Kiểm lại") bám mock; **KQD-02 chuyển sang dùng chung nguồn luật ở backend** thay bản đang ở `CapNhatKQDT.tsx` (ô đỏ vẫn đúng như cũ) | `KQD-07 (2/2)` | M | 119, mock | 1 | [x] 12/10 — `KiemTruocKetXuat.tsx` + `kiemTruoc.ts` (ẩn chip giờ/km khi chưa có điểm) · nút ở `CapNhatKQDT.tsx` · `GET /luat` (danh sách môn bắt buộc một nguồn, KQD-02 đọc về một lần) · `canh_bao` vàng giờ/km đường ở `/kiem-truoc` · pytest 693 · vitest 65 · Playwright 5 ca (API giả); chưa chạy UI với DB thật |
| 123 | **KQD-08 backend (CHANGES #69, TDD §11D.10):** `ketqua_dat.py` — `doc_gio`/`doc_km`/`doc_pdf_dat` (pdfplumber, mã khóa chữ+số) + `doi_chieu` + `gan_ly_do_khong_co`; `POST /local/ketqua/dat/xem-truoc` (≤5 MB, kiểm mã khóa, chỉ SELECT, lý do "không có trong khóa" tra DB đích) + `POST /dat/luu` (một transaction, UPDATE 2 cột `TGThucHanhDuong`/`TongQDThucHanh` + `NgaySua`, `TrangThai=1`, 12/13 bỏ qua, không gọi SP); `/hoc-vien` trả thêm giờ/km đã lưu làm tròn 2 chữ số. Đã đối chiếu DB dev: mã học viên trong PDF = `MaDK` (62/62) | `KQD-08 (1/3)` | M | 72, 119 | 1+2 | [x] 12/10 — `d2073ea`, `923695b`, `85ecef0` |
| 124 | **KQD-08 UI + KQD-02 giờ/km (CHANGES #69):** `NapDatModal.tsx` (chọn PDF → bảng xác nhận cũ → mới, tình trạng ✔⚠✖🔒, lý do không có trong khóa, **sửa số ngay trong bảng**, tô "đã sửa so với PDF", tick tay dòng chưa chạy DAT điền sẵn 0) · `gioThucHanh.ts` (`parseGio`/`parseKm`/`chuanHoaGio`) · `CapNhatKQDT.tsx`: nút nạp, ô giờ/km nạp sẵn giá trị đã lưu, ô giờ nhận `hh:mm`, chỉ sửa giờ/km thì ghi riêng 2 cột (sửa lỗi lưu điểm ghi NULL đè giờ cũ) | `KQD-08 (2/3)` · `KQD-02` | M | 123 | 1+3 | [x] 12/10 — `d2073ea`, `247c3ec`; chưa có mock riêng (bố cục theo kế hoạch đã duyệt) |
| 125 | **Test + chốt 6 điểm sau `/kiemthu` (CHANGES #70):** pytest S1–S12 (nhánh doi_chieu, pdfplumber giả, biên 5 MB, mất kết nối, `/dat/luu` biên + 401/422 + tham số hóa) · vitest + pytest dùng chung vector giờ/km (`tool/tests/fixtures/gio_km_vectors.json`) · Playwright E1–E12 (lưới + hộp thoại) · sửa regex mã khóa, thêm `TrangThai=1`, điền sẵn 0, giờ nhận `hh:mm:ss` | `KQD-08` · `KQD-02` | S | 123, 124 | 2+3 | [x] 12/10 — `9a06009`, `85ecef0` (805 pytest · 102 vitest · Playwright pass) |
| 126 | **KQD-08 đóng gói exe:** build webui TRƯỚC rồi PyInstaller (`tool.spec` đã có `collect_all` cho `pdfplumber`/`pdfminer`/`pypdfium2`); kiểm trong bản đóng gói đọc được PDF DAT mẫu (đúng 30 dòng K40), máy sạch không có Python. Lưu ý `tool.spec` đang có thay đổi chưa commit của phiên khác (dập số bản build) — build theo bản working copy | `KQD-08 (3/3)` | S | 125 | 1 | [x] 12/10 — build webui + PyInstaller (buildinfo `3ff1e8e`); bản đóng gói có `pdfminer`/`pdfplumber`/`pypdfium2` + `pdfium.dll`; thêm phép kiểm PDF vào `--selftest` (`run_tool.py`) → chạy trên exe: pymssql ✔ · rembg ✔ · **pdfplumber đọc được PDF ✔ "KET QUA: DAT"**. Chưa nạp PDF K40 thật qua giao diện exe (cần phiên đăng nhập VPS + DB đích) → làm ở nghiệm thu máy CSĐT |
| 127 | **KQD-09 backend (CHANGES #72, TDD §11D.11):** `ketqua_xuat.py` dựng workbook 1 sheet (khối đầu + 22 cột; điểm Lý thuyết/Thực hành = TB; kết quả theo `KetLuanCSDT`; ghi chú thiếu môn + cảnh báo giờ/km) · endpoint `xuat-excel` (chỉ SELECT, 404 khi khóa rỗng) · `PUT /local/config/co-so` + `co_quan_chu_quan`/`ten_co_so_dao_tao` trong `ConfigIn` · `openpyxl` vào requirements/`tool.spec`/`--selftest` | `KQD-09 (1/3)` | M | 123 | 1+2 | [x] 12/10 — `551fb38` |
| 128 | **KQD-09 UI + lưu vào thư mục `output` (CHANGES #72, #74):** nút "Xuất Excel" ở màn Cập nhật KQĐT · khối ③ "Thông tin cơ sở" ở Cấu hình · `paths.output_dir()` (cạnh exe, lùi về `%APPDATA%\\pmcsdtlx-tool\\output`, dev `tool/output`) · `luu_file` không ghi đè (`_2`…) · `POST /mo-thu-muc-xuat` + nút "Mở thư mục" · giờ/km số nguyên hết dấu chấm thừa (`34.` → `34`) | `KQD-09 (2/3)` | M | 127 | 1+3 | [x] 12/10 — `551fb38`, `9d67c19` |
| 129 | **KQD-09 chốt sau `/reviewtdd` §11D.11 (CHANGES #73):** chống formula injection (ô bắt đầu `= + - @` ép kiểu chữ) + bỏ ký tự điều khiển + cắt 32.000 ký tự · `PUT /co-so` gác phiên · hạng khối đầu ổn định khi hòa · nhãn "Chưa có kết luận" · `Ngày lập` chỉ `dd/mm/yyyy` | `KQD-09 (3/3)` | S | 128 | 2 | [x] 12/10 — `ce6b407` |
| 130 | **KQD-10 backend (CHANGES #75, TDD §11D.12):** `ketqua_so.py` — 1 sheet `SO_PHU_LUC_VI` bám file mẫu (A4 dọc, 13 ô gộp, lặp `$10:$11`, chân trang `Trang &P/&N`, Times New Roman 12), xếp theo TÊN tiếng Việt tự dựng, kết quả chỉ khi đủ 5 điểm, `Người lập` để trống · `POST /xuat-so-theo-doi` · tách `_doc_khoa_va_hv` / `_luu_file_xuat` dùng chung với `xuat-excel` | `KQD-10 (1/3)` | M | 128 | 1+2 | [x] 12/10 — `03fae74` |
| 131 | **KQD-10 UI (CHANGES #75-#76):** nút "Xuất Sổ theo dõi" cạnh "Xuất Excel" (dùng chung thanh thông báo + "Mở thư mục") · `so_hv_trong_ket_qua` + dòng lưu ý "N học viên có kết luận nhưng thiếu điểm nên để trống kết quả" | `KQD-10 (2/3)` | S | 130 | 1+3 | [x] 12/10 — `03fae74`, `b768ae7` |
| 132 | **KQD-10 chốt sau `/reviewtdd` §11D.12 (CHANGES #76):** thanh điệu theo âm tiết (`Hòa`=`Hoà`) · viền xám `A6A6A6`, chân trang cỡ 10, hàng 5/9 cao 15,75 đúng mẫu · `footer` 0,3 inch · độ rộng cột Họ tên theo chữ hoa/thường · chiều cao khối cơ sở tự tăng | `KQD-10 (3/3)` | S | 131 | 2 | [x] 12/10 — `b768ae7` |
| 133 | **Sửa lỗi có sẵn: `PUT /local/config` ghi đè cả cấu hình** (làm rơi `kqd_chuong_trinh`, cấu hình Sync khi lưu khối ①) → gộp `{**đã lưu, **mới}`, secret che giữ nguyên + test hồi quy (phát hiện khi làm task 127) | — | XS | 127 | 2 | [x] 12/10 — `08c8f78` |
| 134 | **Đóng gói exe bản có KQD-09/10:** build webui + PyInstaller; `collect_all` `openpyxl`/`pdfplumber` đặt đúng chỗ trong `tool.spec` (`8eb043f` sửa vị trí chèn nhầm); `--selftest` đạt. Lưu ý: tiến trình `chrome-native-host` có thể giữ `VCRUNTIME140.dll` trong `dist` → build ra thư mục tạm rồi sao chép (`robocopy`) | — | S | 129, 132 | 1 | [x] 12/10 — `b768ae7` |
| 135 | **Nghiệm thu máy CSĐT (KQD-09 + KQD-10 + KQD-08 + KQD-02 giờ/km):** mở file Excel chi tiết bằng Excel thật; **in thử Sổ theo dõi A4**; chọn lại luật kết quả của sổ (A như mẫu / B theo kết luận) sau khi xem khóa thật; thư mục `output` cạnh exe ghi được; rồi đổi 4 story sang ✅ trong PRD | `KQD-09`, `KQD-10` | S | 134 | 1 | [ ] |
| 136 | **KQD-04 đổi (1/3) — backend `cap_nhat` 14→90 (CHANGES #77, TDD §11D.13):** sau SP `_CapNhat`, khi HV đọc ra đang `TT_XuLy='14'` và kết luận Đạt → `UPDATE ... SET TT_XuLy='90' WHERE MaDK=%s AND MaKhoaHoc=%s AND TT_XuLy='14' AND KetLuanCSDT=1 AND ISNULL(GiaiTrinh,'')<>''` (guard trong SQL, không tin client); tham số mới `giai_trinh_chung` (dùng khi ô riêng trống); response `tt_moi` đọc lại từ DB + `thieu_giai_trinh`; pytest bảng quy tắc (Đạt+GT→90 · Đạt thiếu GT→14 · Không đạt→14 · đang 90→90 · 12/13→409). **Chạy `impact` trước** (hàm dùng chung KQD-02/04/05/06). | `KQD-04` (1/3) | M | 135 | 1+2 | [x] |
| 137 | **KQD-04 đổi (2/3) — backend hàng loạt + mẫu + lý do trên lưới:** `POST /local/ketqua/giai-trinh-lo` (≤200 HV, một giao dịch, guard `TT_XuLy='14' AND KetLuanCSDT=1`, trả `da_chuyen` + `bo_qua[{ma_dk, ly_do}]`, lỗi giữa lô rollback) · `GET`/`PUT /local/ketqua/mau-giai-trinh` qua `config_store` (**theo `target_key`**, ≤20 mẫu × 1000 ký tự, loại rỗng/trùng, `phien_ban` lệch → 409; **ghi cấu hình có khóa** `threading.Lock` + ghi tạm rồi `os.replace`) · SELECT lưới đọc thêm `LyDoTuChoiKQDT` + `GiaiTrinh`; lô: kiểm đủ điều kiện bằng `hv_chua_du`, giải trình riêng được giữ (`ghi_de_rieng`), `MaCSDT`, biên lô, 502 `lo_loi`/`khong_ro` (TDD §11D.13 v6.23). | `KQD-04` (2/3) | M | 136 | 1+2 | [x] |
| 138 | **KQD-03 backend:** nhóm "còn sót kết xuất" = `09`/`10` + `90` có `KetLuanCSDT=1` (`_NHOM_TT["capnhat"]`, đếm theo khóa ở `/khoa`); HV `90` không kết luận không tính. | `KQD-03` | XS | 136 | 1+2 | [x] |
| 139 | **KQD-07 backend:** `/kiem-truoc` xét thêm HV `90` (lọc `TT_XuLy IN ('03','04','09','10','90')`, `hv_chua_du` giữ nguyên luật); test HV 90 đủ/thiếu điểm; **+3 lý do mới** `thieu_giai_trinh` (14 Đạt) · `khong_dat_o_90` · `giai_trinh_trong`. | `KQD-07` | XS | 136 | 1+2 | [x] |
| 140 | **KQD-01 UI (đã duyệt mock `ui-mock/ketqua.html` 16/10):** cột **Trạng thái** (chip tên nghiệp vụ + dòng "việc cần làm", mã chỉ ở tooltip — bảng nhãn thay `TT_LABEL`) · **dải tab có đếm** thay `BO_LOC` (Tất cả · Chưa nhập · Chờ kết xuất · Không đạt · Sở từ chối nổi đỏ · Đã gửi/Hoàn thành) · "Chú giải trạng thái" gập · lý do Sở từ chối một dòng dưới tên HV `14` · giữ `whitespace-nowrap` các chip · **header gọn 2 hàng** (khóa + chương trình + Kiểm trước + tìm / tab + chú giải + nút "Giải trình chung ▾" thu gọn) · tab **"Cần xử lý"** = `14` + `90` Không đạt/trống kết luận · chip đỏ "Đang giải trình nhưng không đạt" + chip cam "Thiếu giải trình — chưa kết xuất được". | `KQD-01` | M | 137, 138 | 1 | → PRD |
| 141 | **KQD-04 đổi (3/3) — UI giải trình hàng loạt:** khung "Giải trình chung của khóa" (ô + chọn/lưu mẫu + đếm 1000) hiện khi khóa có HV 14/90 · cột tích chọn ở tab "Sở từ chối" + chọn tất cả · thanh "Giải trình & chuyển chờ kết xuất lại (N)" + hộp xác nhận (đủ điều kiện X · bỏ qua Y kèm lý do từng người) · Lưu 1 HV `14` báo đúng 3 ca (→90 / thiếu giải trình / Không đạt) — **thiếu giải trình = thông báo vàng đứng lâu** · **ô tích "Ghi đè giải trình riêng"** (mặc định tắt) · nút hàng loạt khóa khi nội dung rỗng · **hộp "Quản lý mẫu"** (sửa/xóa/thêm, một `PUT`) · "không rõ kết quả" khi mất kết nối. | `KQD-04` (3/3) | M | 137, 140 | 1 | → PRD |
| 142 | **KQD-03 UI:** màn Theo dõi kết xuất — "còn sót kết xuất" hiện HV `90` Đạt, nhãn trạng thái dùng chung bảng nhãn task 140. | `KQD-03` | XS | 138, 140 | 1 | → PRD |
| 143 | **Test KQD-04/KQD-01:** vitest bảng nhãn + tab đếm · Playwright API giả (14 Đạt+GT→90 · Đạt thiếu GT giữ 14 · Không đạt giữ 14 · lô lẫn 14/09/13 chỉ chuyển người đủ điều kiện · giải trình chung điền sẵn hộp) · ảnh 4 viewport lưới ở `anh-kiem/`. | `KQD-04` · `KQD-01` | S | 141, 142 | 2+3 | [x] |
| 144 | **Đóng gói exe bản có KQD-04 đổi:** build webui TRƯỚC rồi PyInstaller; `--selftest`. Chạy một mình (sửa `tool.spec`/dist dùng chung). | — | S | 143 | 1 | [x] |
| 145 | **Nghiệm thu máy CSĐT (KQD-04 đổi + KQD-01 + KQD-03 + KQD-07):** HV `14` thật → sửa điểm + giải trình → thấy `90`; mở phần mềm CDB thấy HV trong danh sách kết xuất và kết xuất lại được; **phần mềm CDB có tự đặt `90` ở màn giải trình riêng không** (so trước/sau); giải trình hàng loạt 1 lô nhỏ. | `KQD-04` | — | 144 | 1 | [ ] |

> KQD-02 cắt 2 task (72/73) cùng trỏ 1 story → PRD `KQD-02` chỉ ✅ khi xong cả 2. Tái dùng SP đã verify 07/10 trên `GPLX_CDB_CSDT` (biên bản `tdd-review-07-10-2026.md`): SP ghi 18 tham số, SP không bảo vệ `12`, cột `GiaiTrinh nvarchar(1000)` ghi ngoài SP.
> KQD-05 cắt 2 task (76/77) cùng trỏ 1 story → PRD `KQD-05` chỉ ✅ khi xong cả 2. Thao tác **mức CƠ SỞ** (user chốt phương án A sau /reviewtdd 07/10 — DB không nối HV↔gói nên xóa gói buộc quét cả CSĐT; biên bản `tdd-review-07-10-2026-kqd05.md`, TDD §11D.7, decisions §19). Ghi/xóa thật ở CDB → **nghiệm thu máy CSDT**.
> KQD-06 (task 78) **đã code trước khi ghi sổ** (user chốt phương án A gộp 1 story 07/10): sửa lẻ **giữ quy-đổi môn cũ** + xóa điểm reset `03` bằng **UPDATE trực tiếp** (SP không lùi 03 được) — chỉ áp HV `09/10`. TDD §11D.8, CHANGES #48. Ghi/xóa thật ở CDB → **nghiệm thu máy CSDT**.
> KQD-05 mở rộng #53 (task 83/84): **"Sửa sau gửi" chọn từng HV** thay khóa cứng M1 khi cơ sở hết gói chưa gửi; PRD `KQD-05` chỉ ✅ khi xong **cả 4 task (76, 77, 83, 84)**. Không sinh/ký XML (file KQĐT ký số bằng khóa phần mềm CDB). TDD §11D.7b, decisions §21. Ghi thật → **nghiệm thu máy CSDT**.
> KQD-04 đổi #77 (task 136-145): HV Sở từ chối sửa xong **tự sang `90`** khi Đạt + có giải trình (vì phần mềm CDB chỉ kết xuất `09`/`90` và không thủ tục nào đặt `90`); giải trình hàng loạt = giải trình chung của khóa + mẫu + tích nhiều HV một giao dịch. KQD-04 cắt 3 task cùng trỏ 1 story → PRD `KQD-04` chỉ ✅ khi xong cả 3. KQD-01 (140), KQD-03 (138/142), KQD-07 (139) bị hạ ⏳ ở PRD (yêu cầu đổi). **Khuyến nghị `/reviewtdd` §11D.13 trước task 136** (sửa hàm dùng chung).

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

### ✅ Checkpoint 19 — sau task 83-84 (KQD-05 sửa sau gửi, CHANGES #53)
- [ ] Còn gói chưa gửi → "Mở sửa điểm" **tắt**, chỉ dùng "Mở khóa" cũ (409 `con_goi_chua_gui` nếu gọi thẳng API).
- [ ] Hết gói chưa gửi → tích 2 HV `12` → xác nhận (lý do + tích) → **chỉ 2 HV đó** về 09/10, **gói không bị xóa**, `GiaiTrinh` có lý do, nhật ký ghi điểm trước.
- [ ] Sau mở: sửa 1 môn → Lưu (ô trống giữ quy đổi cũ); chip cam + băng cam hiện; khối đỏ KQD-03 đủ cột.
- [ ] HV `13` → không có ô tích / 409; HV `12` `KetLuanCSDT` NULL → bỏ qua, không ép '10'; HV đã về `12` (kết xuất lại) → dòng biến khỏi khối đỏ.
- [ ] **Mức 2** unit test: guard `12`/`KetLuanCSDT`, 409 còn gói chưa gửi, nhật ký ghi trước UPDATE.
- [ ] Playwright 1280/1440 lưới + hộp xác nhận + khối đỏ — 0 tràn.
- [ ] **Ghi thật → nghiệm thu máy CSDT** (HV `12` khóa B01-K40); hỏi hỗ trợ CDB/Sở việc nhận 2 bản KQĐT cùng HV.

### ✅ Checkpoint 30 — sau task 119-120 (KQD-07 Kiểm trước kết xuất, CHANGES #65)
- [ ] **Mức 2:** đủ 5 môn → đủ · thiếu 1 môn (nêu đúng môn) · chưa có điểm · thiếu giờ/km · thiếu kết luận (09/10 mà `KetLuanCSDT` NULL) · giờ/km đường dưới ngưỡng gợi ý **không** vào lý do · HV `12/13/14/90` không vào danh sách · hạng mô tô ẩn thực hành.
- [ ] KQD-02 và KQD-07 dùng **cùng một nguồn luật** (đổi môn bắt buộc của một hạng thì cả hai đổi theo); test KQD-02 hiện có vẫn xanh.
- [ ] Bấm một dòng → mở đúng HV ở lưới nhập điểm; khóa đủ hết → thông báo "đủ điều kiện kết xuất".
- [ ] Playwright 1280/1440 khung kết quả — 0 tràn.

### ✅ Checkpoint 32 — sau task 123-126 (KQD-08 nạp giờ/km từ PDF DAT + KQD-02 giờ/km, CHANGES #69-#70)
- [x] **Mức 2:** pytest 805 · vitest 102 (`doc_gio`/`doc_km`/vector chung, `doi_chieu` mọi nhánh, 2 endpoint với cursor giả, giờ/km ngoài khung 422).
- [x] **Mức 3:** Playwright backend giả — lưới (nạp sẵn, `hh:mm`, chỉ sửa giờ/km, sửa điểm không gửi null) + hộp thoại (sai khóa, .xlsx/>5 MB, lưu xong, lỗi 502, biên ô sửa, tick, điền sẵn 0).
- [ ] **`/reviewtdd` ở phiên mới** cho §11D.10 (TDD đổi API + luồng ghi).
- [x] **Exe đóng gói** (task 126): `--selftest` trên exe báo `pdfplumber/pdfminer/pypdfium2 đọc được PDF`, không thiếu cmap/DLL (12/10/2026).
- [ ] **Exe + PDF thật:** trong exe, nạp PDF K40 qua giao diện ra đúng 30 dòng như bản dev (làm cùng nghiệm thu máy CSĐT bên dưới).
- [ ] **Nghiệm thu máy CSĐT:** xem trước 1 khóa thật · ghi 1–2 HV · mở lại bằng phần mềm CDB cũ thấy đúng giờ/km · HV `12`/`13` không bị đụng · soát **cột phụ** PM cũ có đặt mà UPDATE trực tiếp bỏ sót (chụp trước/sau).

### ✅ Checkpoint 33 — sau task 127-135 (KQD-09 Excel chi tiết + KQD-10 Sổ theo dõi, CHANGES #72-#76)
- [x] **Mức 2:** pytest 871 — dựng workbook rồi đọc lại bằng `openpyxl`: khối đầu, 22 cột, ngày/CCCD đúng kiểu, luật kết quả, formula injection, ký tự điều khiển; Sổ: **so trực tiếp với file mẫu** (khổ giấy, ô gộp, tiêu đề lặp, chân trang, font, nền, viền, chiều cao hàng), xếp tên tiếng Việt (thanh điệu, `a<ă<â`, `d<đ`, `Hòa=Hoà`).
- [x] **Mức 3:** Playwright `xuat-excel` 8 ca — bấm nút → POST đúng khóa, báo đường dẫn + "Mở thư mục", 404, nút khóa khi đang xuất, lưu tên cơ sở, dòng lưu ý thiếu điểm.
- [x] Dựng thử từ DB dev thật (B.01-K40, 30 HV): Excel chi tiết 30 dòng; Sổ 30 dòng xếp đúng tên.
- [ ] **Mở file Excel chi tiết bằng Excel thật:** 22 cột, lọc/đóng băng tiêu đề, ngày dd/mm/yyyy, CCCD không thành `1.2E+11`.
- [ ] **In thử Sổ theo dõi A4:** tên không xuống dòng và đều cỡ chữ · `Trang x/y` không đè dòng cuối · 2 hàng tiêu đề lặp ở trang 2 · số dòng mỗi trang (ước lượng ~22 / ~31).
- [ ] **Quyết luật kết quả của sổ** (A: trống khi thiếu điểm như mẫu / B: theo kết luận đã lưu) sau khi xem khóa thật — K40 dev: 25 Đạt nhưng chỉ 1 người đủ 5 điểm.
- [ ] Máy CSĐT: thư mục `output` cạnh exe ghi được; "Mở thư mục" mở đúng; tên cơ quan/cơ sở đã nhập ở Cấu hình.
- [ ] **`/subagent` bổ sung** — mảng xuất Excel chưa có người soát (agents hiện dựng theo PRD cũ).

### ✅ Checkpoint 34 — sau task 136-139 (backend KQD-04 đổi + KQD-03/07 xét `90`, CHANGES #77)
- [ ] `pytest` sạch; **bảng quy tắc §11D.13** có test đủ 5 ca (Đạt+GT→90 · Đạt thiếu GT→14 · Không đạt→14 · đang 90→90 · 12/13→409).
- [ ] `giai-trinh-lo`: lô lẫn 14 Đạt / 14 Không đạt / 09 / 13 chỉ chuyển người đủ điều kiện, `bo_qua` có lý do; lỗi giữa lô rollback cả lô.
- [ ] `detect_changes` — chỉ chạm `routers/ketqua.py`, `config_store.py`, test; KQD-02/05/06 không đổi hành vi.
- [ ] `/kiem-truoc` và "còn sót kết xuất" tính đúng HV `90`.

### ✅ Checkpoint 35 — sau task 140-145 (UI + đóng gói + nghiệm thu, CHANGES #77) — **nghiệm thu máy CSĐT**
- [ ] `pnpm build` + `pnpm vitest run` + Playwright sạch; ảnh 4 viewport lưới (Tất cả · Sở từ chối đã chọn · hộp xác nhận) bám mock, chip không ngắt dòng.
- [ ] Luồng đầu–cuối trên dev (API giả): HV `14` Đạt + giải trình → chip "Đã giải trình"; thiếu giải trình → còn "Sở từ chối" + nhắc.
- [ ] **Máy CSĐT:** HV `14` thật sửa + giải trình → `90` → phần mềm CDB thấy trong danh sách kết xuất → kết xuất lại; ghi nhận phần mềm CDB có đặt `90` riêng không.
- [ ] Giải trình hàng loạt một lô nhỏ trên khóa thật; kiểm `GiaiTrinh` ghi đúng và HV khác không bị đổi.
- [ ] PRD: KQD-01/03/04/07 chuyển ✅ khi pass (KQD-03 đã ⏳ từ ⚠️ — nâng sau khi kiểm live).

## Phase 7 — Lối nhập OCR dự phòng (THU-06)

> Feature MUST thêm ở CHANGES #49 (sau BUG-14 — iPhone/iOS quét QR CCCD yếu; probe fail mọi engine web → QR iPhone là ngõ cụt, OCR thay hẳn). Thiết kế: TDD §6.7 (v5.8 — engine chốt) · TDD-decisions §20 · biên bản `tdd-review-07-10-2026-thu06.md`. **Thuần app web (webapp)** — KHÔNG đụng tool/VPS luồng ghi; tái dùng màn xác nhận + luồng gửi (idempotent UUID, nháp offline) của THU-01/02. **Engine chốt:** Tesseract.js client-side (ảnh KHÔNG rời máy — rào cứng PII), tách trường = OCR toàn ảnh + regex theo nhãn.

| # | Task | Story | Quy mô | Phụ thuộc | Kiểm | Xong |
|---|---|---|---|---|---|---|
| 79 | **Nền OCR (lib)**: tích hợp Tesseract.js + dữ liệu `vie` vào webapp; `lib/ocr.ts` — downscale ảnh ≤~1600px → chạy Tesseract (client/worker) → trả text; **tách 5 trường mặt trước bằng regex theo nhãn** in trên thẻ ("Số/No.", "Họ và tên", "Ngày sinh", "Giới tính", "Nơi thường trú"; **ngày cấp ở mặt sau → không đọc, nhân viên nhập tay** — chốt A); chuẩn hóa hạ nguồn qua helper `lib/qr.ts` (ddMMyyyy→yyyymmdd, độ dài tên, parse địa chỉ 2 cấp); **mốc fail = CCCD 12 số hợp lệ** (không có → fail không điền gì); **hủy ảnh thẻ khỏi bộ nhớ sau khi đọc** (trừ khi tái dùng cắt chân dung). +unit test tách trường | `THU-06 (1/2)` | M | 13,18 | 1+2 | [x] 07/10 — `lib/ocr.ts` (Tesseract.js client + downscale ≤1600 + regex theo nhãn + mốc fail CCCD 12 số + ngày cấp rỗng theo chốt A) + 6 unit test (34 vitest) + build sạch. OCR thẻ thật = mức 1, chờ Checkpoint 17 |
| 80 | **Lối vào "Chụp ảnh thẻ (tự đọc)" + luồng UI**: thêm lựa chọn thứ 3 ở màn vào `/app/quet` (mọi thiết bị, không khóa theo máy) → chụp/tải ảnh mặt trước CCCD → gọi `ocr.ts` (spinner tiến trình + **hủy → Nhập tay**) → điền **màn xác nhận dùng chung** (THU-01/02), trường thiếu/không-chắc **đánh dấu để soát**, **không auto-submit** → lưu qua luồng gửi sẵn có; ảnh fail → báo rõ, không điền bừa, về Nhập tay/Quét QR. Chạy `impeccable` | `THU-06 (2/2)` | M | 79,17,19 | 1 | [x] 07/10 — lối "Chụp ảnh thẻ" (mobile ChonCach) + "Đọc thẻ OCR" (desktop Preview) = mọi thiết bị; spinner + Hủy→Nhập tay; dynamic-import ocr.ts; banner đánh dấu trường soát + ngày cấp nhập tay; lưu qua luồng gửi sẵn. build+34 vitest. review-nghiepvu 5/6 (6b "ô đỏ" = banner chung như THU-01/02). **THU-06 ⚠️ — OCR thẻ thật chờ Checkpoint 17** |

> THU-06 cắt 2 task (79/80) cùng trỏ 1 story → PRD `THU-06` chỉ ✅ khi xong cả 2 **và** kiểm tay trên thẻ+điện thoại thật (Checkpoint 17). Engine OCR + tách trường đã chốt ở `/tdd` (TDD §6.7 v5.8). **Mở kiểm:** độ chính xác tiếng Việt có dấu của Tesseract.js trên thẻ thật — quá thấp thì tăng sửa tay hoặc xin phê duyệt pháp lý cho eKYC ngoài (qua `/capnhat`).

### ✅ Checkpoint 17 — sau task 79-80 (THU-06 OCR)
- [ ] Màn vào có lối **"Chụp ảnh thẻ (tự đọc)"** trên **mọi thiết bị** (iPhone/Android/desktop), không khóa theo máy.
- [ ] **Mức 2** (unit tách trường regex): ảnh đủ nhãn → **5 trường mặt trước** đúng (ngày sinh ddMMyyyy→dd/mm/yyyy); không đọc được CCCD 12 số → **fail, không điền trường nào**; nơi thường trú 2 cấp / xuống dòng → ghép dòng, giữ dấu tiếng Việt; **ngày cấp luôn trống + đánh dấu** (nhập tay). ✅ đã có 6 unit test task 79.
- [ ] **Mức 1 (BẮT BUỘC thẻ thật + điện thoại thật — như AS-001/BUG-14):** chụp CCCD rõ → điền sẵn đúng trường; ảnh mờ/OCR fail → báo rõ, không điền bừa; CCCD sai chữ số → ô đỏ validate 12 số; nhân viên **sửa được từng trường** trước khi lưu (màn xác nhận không auto-submit).
- [ ] Ảnh CCCD **không rời máy** (OCR client-side); ảnh **hủy khỏi bộ nhớ sau khi đọc** (trừ khi tái dùng cắt chân dung); không log đầu ra OCR.
- [ ] Playwright webapp 375/800/1440 màn vào + luồng OCR (dùng ảnh mẫu) — 0 tràn.

## Phase 8 — NAP-01: Bỏ khỏi hàng đợi cho dòng chờ/lỗi (tombstone)

> Mở rộng NAP-01, CHANGES #51 (sau /reviewtdd → TDD v6.1, biên bản `tdd-review-08-10-2026.md`). Chỉ đụng `staging.sqlite` máy tool — KHÔNG đụng VPS/DB đích. Gộp **1 đường** `POST /local/nap/bo-qua` (gỡ endpoint `DELETE /local/keo-ve/:uuid` của task 38). Sau khi code → **đóng gói lại exe** (công thức memory `project_pmcsdtlx_tool_exe_build`).

| # | Task | Story | Quy mô | Phụ thuộc | Kiểm | Xong |
|---|---|---|---|---|---|---|
| 81 | **NAP-01 #51 (1/2) backend**: bảng tombstone `keo_ve_bo_qua(uuid PK, ly_do, created_at)` + migrate `IF NOT EXISTS` (TDD §9.3b) · `keo_ve_upsert` **lọc bỏ uuid ∈ tombstone TRƯỚC upsert** (đặt TRONG hàm — kéo theo trang cursor) · endpoint `POST /local/nap/bo-qua {uuids}` idempotent/1-transaction (tra `keo_ve_trang_thai` từng uuid → tombstone cho `cho`/`loi`/`None`, KHÔNG `xong` vì QLY-08; `keo_ve_xoa`+`nhap_xoa` mọi dòng) + lô rỗng no-op + trần ≤1000 + tham số hóa · **GỠ endpoint `DELETE /local/keo-ve/:uuid`** (`bo_khoi_hang_doi`, task 38 — thay bởi POST). `tool/app/nap.py` + `tool/app/routers/nap.py`. ⚠ `impact` GitNexus TRƯỚC khi sửa `keo_ve_upsert` | `NAP-01` | M | 20,50,38 | 1+2 | [x] 08/10 — tombstone `keo_ve_bo_qua` + `_bo_qua_uuids`/lọc trong `keo_ve_upsert` + `bo_qua_nhieu` + `POST /local/nap/bo-qua` (gỡ DELETE cũ, trần 1000); impact nhiễu→grep xác nhận caller duy nhất `keo_hang_doi`; +11 test (50 test_nap_keo, 346 full suite); review-nghiepvu 6/6 |
| 82 | **NAP-01 #51 (2/2) UI**: chọn nhiều dòng (checkbox) ở lưới hàng đợi + nút "Bỏ khỏi hàng đợi" cho dòng ⚪ chờ / 🔴 lỗi (trước chỉ 🟢) + panel xác nhận 2 bước (nêu số dòng, không lấy lại qua giao diện — tái dùng mẫu panel đỏ) + **chuyển mọi chỗ gọi `DELETE /keo-ve/:uuid` sang `POST /bo-qua` `{uuids:[1]}`**. `tool/webui/src/pages/tool/NapHoSo.tsx` + `api.ts`. Chạy `impeccable` | `NAP-01` | S | 81,51 | 1 | [x] 08/10 — `boKhoiHangDoi(uuids[])`→POST /bo-qua; checkbox sẵn có tái dùng cho nút "Bỏ khỏi hàng đợi (N)" ở thanh đáy + nút bỏ trên MỌI dòng + panel xác nhận 2 bước (modal đỏ) + thông báo kết quả (số nhớ bỏ-qua). build+tsc+38 vitest. Playwright/visual hoãn (màn cần login+dữ liệu, như 46/47/51) → Checkpoint 18 lúc chạy tool |

> Task 81 **gỡ một phần task 38** (endpoint `DELETE /local/keo-ve/:uuid`) — task 38 đã [x], giữ nguyên dòng để lưu dấu vết; nút "Nạp lại nhanh" dòng lỗi của task 38 KHÔNG đụng. NAP-01 vẫn 🔄 tới khi mọi task con xong.

### ✅ Checkpoint 18 — sau task 81-82 (NAP-01 #51 bỏ hàng đợi + tombstone)
- [ ] Bỏ 1 dòng ⚪ chờ → bấm "Kéo về từ VPS" lại → **không hiện lại** (tombstone chặn); nháp (gồm ảnh) của dòng đó **đã dọn**.
- [ ] Bỏ nhiều dòng một lượt + xác nhận 2 bước; dòng 🟢 lẫn trong lô vẫn bỏ được (không ghi tombstone).
- [ ] **Mức 2:** `keo_ve_upsert` lọc bỏ uuid ∈ `keo_ve_bo_qua` (kéo lại không về); **`xong` KHÔNG bị ghi tombstone** (QLY-08 "Gỡ về chờ nạp" sau đó kéo lại được); hồ sơ gửi lại (uuid mới) hiện lại bình thường.
- [ ] Không còn endpoint `DELETE /local/keo-ve/:uuid`; UI gọi `POST /bo-qua` cho cả 1 dòng.
- [ ] Đóng gói lại exe (pnpm build webui TRƯỚC + PyInstaller) chạy được bản mới.

## Phase 9 — Phân công giáo viên – xe (phân hệ #4, PCG-01..05)

> Feature mới (CHANGES #54, PRD v4.3, TDD v6.4 §11E, decisions §22, mock `ui-mock/phancong.html`). Ghi `GPLX_CDB_CSDT` (`KhoaHoc_GiaoVien`, `KhoaHoc_XeTap`). **Rủi ro cao lên sớm:** luật + `/ghi` (ghi thẳng CDB thật) làm TRƯỚC UI. Không đụng task cũ. Ghi thật → **nghiệm thu máy CSDT**.

| # | Task | Story | Quy mô | Phụ thuộc | Kiểm | Xong |
|---|---|---|---|---|---|---|
| 85 | **Luật thuần** `tool/app/phancong_rules.py` (không DB): trùng = `NOT(kt<=bd_cũ OR bd>=kt_cũ)` datetime nửa mở · phạm vi khóa (`bd>KG 00:00`, `kt<BG 23:59:59`, `bd<kt`) · GV/xe thuộc khóa, còn hoạt động · 1 GV–1 xe · hạn `GPXTL/GCNKD` · 3 mức Chặn/Cảnh báo/Thông tin (bảng TDD §11E.7) + unit test (chạm đầu mút, sáng/chiều cùng ngày, lịch 00:00 chiếm mọi giờ, cùng khóa chặn) | `PCG-04 (1/4)` | M | — | 1+2 | [x] |
| 86 | **Backend đọc + kiểm:** `routers/phancong.py` (mount `require_session`) `GET /khoa`, `GET /khoa/{ma}` (hiện trạng GV/phân công/xe/ghép kèm `MaLichLV/MaLichSD`), `GET /giao-vien?ma_kh`, `GET /xe?ma_kh` (kèm "bận" ở khóa khác) + `POST /kiem-tra` (bản nháp → vấn đề, **không ghi**) + `phancong_service.py` (đọc CDB, đọc lại môn theo 3 định dạng) | `PCG-04 (2/4)` | M | 85 | 1+2 | [x] |
| 87 | **Backend ghi:** `POST /ghi` — kiểm lại toàn bộ luật trên CDB hiện tại, 409 khi còn chặn / thiếu xác nhận cảnh báo / thiếu `xac_nhan_csdl_that`; thứ tự xóa→thêm→sửa từng dòng bằng SP (`usp_KhoaHoc_GiaoVien_Insert`, `usp_LichLV_KhoaHoc_GiaoVien_Insert/_Update`, `usp_KhoaHoc_XeTap_Insert`, `LichSD_KhoaHoc_XeTap_Insert`, `usp_LichSD_KhoaHoc_XeTap_Update`; xóa `usp_LLV_…_Delete`/`usp_LSD_…_Delete`; **KHÔNG** SP xóa lan); `TenMonHoc="1,8"`, `MaMonHoc` NULL, `GhiChu=''`, `NguoiTao`=người đăng nhập; lỗi giữa chừng trả đã/chưa ghi; nhật ký sqlite `phancong_nhat_ky` + `GET /nhat-ky`. Test cursor giả (không bao giờ gọi SP xóa lan) | `PCG-04 (3/4)` | M | 85,86 | 1+2 | [x] |
| 88 | **Khung phân hệ #4:** thêm `phancong` vào `lib/modules.ts` (route `/phan-cong/*`, accent `pc`, `db: GPLX_CDB_CSDT`, sub-nav 2 mục) + token `pc` trong `tailwind.config.js` + route `App.tsx` + trang `PhanCongTheoKhoa.tsx` (chọn khóa gõ-tìm, chip hạng/ngày/DKKH, stepper 3 bước, cột phải "Kiểm tra khóa" gọi `/kiem-tra`, khung hướng dẫn từng bước) bám mock | — | M | 86 | 1 | [x] |
| 89 | **Bước ① GV của khóa:** 2 danh sách gọn (tìm, lọc LT/TH/AL), thêm từng GV (hộp cảnh báo), tích chọn → "Thêm N GV" (xem trước từng GV), "Chọn GV TH hợp hạng", gỡ GV (hộp liệt kê hậu quả xóa theo phân công + ghép xe); trạng thái bản nháp phía client | `PCG-01` | M | 88 | 1 | → PRD |
| 90 | **Bản nháp + Ghi vào CDB:** thanh dưới đếm thay đổi (thêm/sửa/xóa) + "Hủy thay đổi"; hộp xem lại (tóm tắt + SP) + tích "CSDL thật" + tích "đã xem N cảnh báo"; nút Ghi khóa khi còn chặn; kết quả đã/chưa ghi; làm tươi hiện trạng + nhắc kết xuất lại nếu đã DKKH | `PCG-04 (4/4)` | M | 87,89 | 1 | → PRD |
| 91 | **Bước ② phân công từng GV:** ô "Ngày bắt đầu thực hành của khóa" (tự nhập, để trống) · khung nhập: ô lớn ★ Thực hành lái xe (1 bấm), 8 môn khác, từ/đến ngày, ô tích "Chỉnh giờ" (danh sách bước 30 phút + nút tắt sáng/chiều/cả ngày, giờ lẻ cũ giữ nguyên), "nối tiếp"/"+1 tuần", ô "Kiểm tra ngay" sát nút Lưu · chip phân công (TH tô màu) + lỗi chữ lớn dưới ô sai · sửa/xóa (xóa TH cuối → xóa theo ghép xe) | `PCG-02 (1/2)` | M | 90 | 1 | [x] |
| 92 | **Bước ② hàng loạt:** tích nhiều GV → "Phân công cho N GV" (cùng môn + thời gian, xem trước từng GV, GV lỗi bỏ qua kèm lý do), "Dời ngày kết thúc thực hành cho N GV", "Áp Thực hành lái xe cho N GV TH chưa có" | `PCG-02 (2/2)` | M | 91 | 1 | → PRD |
| 93 | **Bước ③ xe + ghép:** dải chip "Xe của khóa" + hộp "Thêm xe" (hạng, hạn giấy phép, xe ở khóa khác; xe ngừng không thêm được) · bảng ghép 1 GV–1 xe (chọn xe, từ–đến theo ngày, địa điểm điền sẵn, lỗi dưới ô) · đổi xe/gỡ xe/bỏ ghép có xác nhận | `PCG-03 (1/2)` | M | 91 | 1 | [x] |
| 94 | **Gợi ý ghép xe:** `POST /goi-y-ghep-xe` (xe còn trống, thuộc khóa, không bị chặn, ưu tiên đúng hạng; **không ghi**) + hộp xem trước/sửa/tích từng dòng → "Áp" vào bản nháp | `PCG-03 (2/2)` | S | 93 | 1+2 | → PRD |
| 95 | **Rà soát khóa:** `GET /ra-soat` (`phancong_rasoat.py`) + tab 2 `RaSoat.tsx` (bảng mọi khóa, bấm dòng mở khóa đó) | `PCG-05` | S | 88 | 1 | → PRD |
| 121 | **PCG-06 backend (CHANGES #66, TDD §11E.10):** `phan_loai_han` (đỏ/vàng/chưa khai) trong `phancong_rules.py` + `GET /local/phancong/han-giay-to?ngay=30` (3 nhóm: xe `NgayHHGPXTL`/`NgayHHGCNKD` · GV `NgayHHGPLX` · GV/xe `TrangThai=0` còn dòng ở khóa `NgayBG >= hôm nay`; lọc `MaCSDT`; kèm khóa chưa bế giảng đang dùng) + unit test (ngày biên, NULL, ngưỡng); tái dùng `gp_het_som_nhat` lấy ngày sớm nhất | `PCG-06 (1/2)` | M | 85, 86 | 1+2 | [x] 12/10 — `phan_loai_han` (`phancong_rules.py`) · module riêng `phancong_hangiayto.py` theo tiền lệ `phancong_rasoat.py` (không dùng `gp_het_som_nhat` vì cần tách từng loại giấy) · tool 690 pytest |
| 122 | **PCG-06 UI (cần mock `/prototype-next` trước):** tab thứ 3 "Hạn giấy tờ" — `modules.ts` sub-nav + route `App.tsx` + `HanGiayTo.tsx` (3 nhóm, đếm đỏ/vàng, dòng kèm khóa, bấm khóa mở màn Phân công theo khóa) | `PCG-06 (2/2)` | M | 121, mock | 1 | [x] 12/10 — `HanGiayTo.tsx` + `hanGiayToHelper.ts` (tab thứ 3, `modules.ts` + `App.tsx`, bấm khóa → `?khoa=`) · vitest 69 · Playwright 4 ca (API giả) · chưa chạy UI với DB thật |

> PCG-04 cắt 4 task (85→86→87→90) cùng trỏ 1 story → PRD `PCG-04` chỉ ✅ khi xong cả 4. PCG-02 cắt 2 (91/92), PCG-03 cắt 2 (93/94). Mô tả chi tiết từng story ở PRD; thiết kế ở TDD §11E; **ghi thật chỉ nghiệm thu ở máy CSDT** (dev không ghi happy-path vào CDB thật).

### ✅ Checkpoint 20 — sau task 85-87 (backend luật + đọc + ghi)
- [ ] **Mức 2** unit `phancong_rules`: chạm đầu mút không trùng · sáng 07:30–11:30 và chiều 13:30–17:30 cùng ngày không trùng · chồng 07:30–11:30 với 09:30–13:30 chặn · lịch 00:00→00:00 chiếm mọi giờ → lịch có giờ nằm trong khoảng bị chặn · trùng **cùng khóa** chặn · `bd<=KG 00:00` chặn, `kt>=BG 23:59:59` chặn · 1 xe 2 GV / 1 GV 2 xe chặn · xe hết hạn trước bế giảng chặn.
- [ ] `POST /ghi`: 409 khi còn lỗi chặn; 409 khi có cảnh báo mà thiếu xác nhận; thứ tự xóa→thêm→sửa; lỗi giữa chừng trả đã/chưa ghi; **không bao giờ gọi** `usp_KhoaHoc_*_Delete`/`usp_VoHieuLuc*`.
- [ ] `GET` đọc đúng cả 3 định dạng môn (`MaMonHoc`+tên · danh sách mã · tên thuần).
- [ ] `pytest` toàn bộ pass; không đụng module cũ.

### ✅ Checkpoint 21 — sau task 88-90 (khung + bước ① + ghi)
- [ ] Phân hệ #4 hiện ở sidebar (màu hồng), băng cam "CSDL đích", chọn khóa gõ-tìm, stepper 3 bước.
- [ ] Bước ①: thêm 3 GV → bản nháp đếm 3 → "Ghi vào CDB" → hộp xem lại → tích → ghi → làm tươi; gỡ 1 GV có phân công → hộp liệt kê đúng hậu quả.
- [ ] Nút Ghi **khóa** khi còn lỗi chặn; "Hủy thay đổi" về đúng hiện trạng.
- [ ] Playwright 1280/1440: không tràn, đủ dấu, cảnh báo chữ ≥13px.

### ✅ Checkpoint 22 — sau task 91-95 (bước ②③ + gợi ý + rà soát)
- [ ] Luồng đầu–cuối trên 1 khóa test: GV → phân công (Thực hành 1 bấm + 1 GV lý thuyết có giờ sáng/chiều) → chọn xe → ghép → Ghi → mở lại thấy đúng.
- [ ] Hàng loạt: phân công cho 5 GV (1 GV trùng khóa khác bị bỏ qua kèm lý do, 4 GV tạo); dời ngày kết thúc cho N GV.
- [ ] "Gợi ý ghép xe": không gán xe hết hạn/đã ngừng/trùng; xem trước mới áp.
- [ ] Rà soát khóa khớp số liệu rà soát DB 10/10/2026 (vd B-K149 11 xe chưa ghép).
- [ ] Ngày bắt đầu thực hành **trống** → nút Thực hành khóa; không có gợi ý ngầm.
- [ ] **Ghi thật CDB production + đối chiếu phần mềm CDB (GV/xe/lịch hiện đúng) → nghiệm thu máy CSDT**; hỏi hỗ trợ CDB việc gói DKKH có chứa GV/xe.

### ✅ Checkpoint 31 — sau task 121-122 (PCG-06 Hạn giấy tờ, CHANGES #66)
- [ ] **Mức 2:** hết hạn (đỏ) · đúng hôm nay · đúng +30 ngày (vàng) · +31 không hiện · NULL → "chưa khai" · ngưỡng đổi được · xe/GV `TrangThai=0` chỉ vào nhóm ngưng khi còn dòng ở khóa `NgayBG >= hôm nay`.
- [ ] Đối chiếu số liệu DB đích 12/10/2026: **5 xe ≤ 30 ngày**, **3 GV hết hạn GPLX**, 1 GV ≤ 30 ngày, nhóm ngưng = 0.
- [ ] Bấm khóa trong dòng → mở đúng khóa ở Phân công theo khóa; sub-nav có đủ 3 tab, các màn cũ không đổi.
- [ ] Playwright 1280/1440 — 0 tràn.

## Phase 10 — Tốt nghiệp & Báo cáo 2 (phân hệ #5, TNB-01..07)

> Feature mới (CHANGES #60-#62, PRD v4.6, TDD §11F v6.8, decisions §23, mock `ui-mock/tnbc2.html`, biên bản `tdd-review-11-10-2026-tnb.md`). Ghi **DB Nạp `GPLX_CSDT`** (`NguoiLX_HoSo`, `BaoCaoII`) **chỉ qua SP có sẵn**; PM cũ mở lên thấy y chang. **Rủi ro cao lên sớm:** luật + backend ghi làm TRƯỚC UI. Không đụng task cũ. Mô tả chi tiết ở PRD; thiết kế ở TDD §11F. Ghi thật → **nghiệm thu máy CSDT**.

| # | Task | Story | Quy mô | Phụ thuộc | Kiểm | Xong |
|---|---|---|---|---|---|---|
| 96 | **Luật thuần** `tool/app/tn_bc2_rules.py` (không DB): `phan_nhom` 4 nhóm + thứ tự xét `khong_duoc`→`can_xem`→`thi_lai`→`san_sang` · phân loại ô tô/mô tô · chuyển `TT_XuLy` được phép + hoàn tác miễn luật đích · đánh số BC2 ô tô/mô tô · `giai_thich_khong_hien` · độ dài cột + giới hạn đầu vào (TDD §11F.1/.7) + unit test | `TNB-04 (1/6)` | M | — | 1+2 | [x] |
| 97 | **Backend đọc ứng viên:** `routers/tn_bc2.py` (mount `require_session`) + `tn_bc2_service.py` (`sqlserver_conn`); `GET /bc2/khoa-san-sang`, `GET /bc2/ung-vien`, `POST /bc2/khop-danh-sach`; gọi `ThemHS_BC2` **một lần `@MaKH=''`** + một `SELECT` bổ sung `TT_XuLy, MaBC2, HangGPLX, NgayBG, BaoCaoII.TrangThai`; phân nhóm trong Python; cache ~30 giây (bỏ khi làm tươi/sau ghi) | `TNB-04 (2/6)` | M | 96 | 1+2 | [x] |
| 98 | **Backend tạo BC2:** `GET /bc2/goi-y-so`, `POST /bc2` (Insert `TrangThai=0`, kiểm trùng số, BC1 suy từ khóa, `TongSoThiSinh` đúng PM cũ) + nhật ký sqlite `tnbc2_nhat_ky` (mẫu `phancong_nhat_ky.py`; **không lưu CMT/họ tên**) + helper khóa ghi chung `tnbc2_ghi` + cổng `xac_nhan_csdl_that` | `TNB-03 (1/2)` | M | 96,97 | 1+2 | [x] |
| 99 | **Backend lập + thêm HV:** `POST /bc2/lap` chạy nền (`lo_id` client sinh, idempotent) — đọc lại cả lô, đọc `BaoCaoII.TrangThai`, Insert nếu chưa có, từng HV `Update_ThemHSBC2` (HV đã `11` đúng BC2 = "đã thêm", không gọi lại SP), kiểm `TT_XuLy_Old='11'`, nhật ký từng HV · `GET /bc2/lo/{lo_id}` · `POST /bc2/{ma}/hoan-tac` (lô gần nhất của BC2, một lần) | `TNB-04 (3/6)` | M | 98 | 1+2 | [x] |
| 100 | **Backend xem/gỡ/xóa BC2:** `GET /bc2/{ma}` (chi tiết + HV), `POST /bc2/{ma}/go` (chỉ HV còn `11` + BC2 còn mở, `DanhSachHocSinhBC2` 101), `DELETE /bc2/{ma}` (**đếm `MaBC2` mọi `TT_XuLy` = 0** trong khóa, rồi `BaoCaoII_Delete`) | `TNB-05 (1/2)` | M | 98 | 1+2 | [x] |
| 101 | **Backend tốt nghiệp đọc:** `GET /khoa?loai=&cu=`, `GET /tot-nghiep/hv`, `POST /tot-nghiep/xem-lai` (chạy thử: trùng số giấy trong lô/DB, khoảng số, cảnh báo; không ghi); tìm không dấu trong Python | `TNB-01 (1/3)` | M | 96 | 1+2 | [x] |
| 102 | **Backend ghi tốt nghiệp:** `POST /tot-nghiep/ghi` — `Update_CNTN` từng HV; lưu sổ trước (số giấy rỗng, ở lại `03`); kiểm trùng loại trừ chính HV; chặn khóa chưa bế giảng; HV ≥ 11 ghi số giấy lần đầu = cảnh báo; khóa `tnbc2_ghi`; lỗi giữa chừng trả đã/chưa ghi | `TNB-01 (2/3)` | M | 101,98 | 1+2 | [x] |
| 103 | **Backend hủy/sửa tốt nghiệp:** `POST /tot-nghiep/huy` — HV `09` → `03`, giữ sổ/quyết định (đọc lại rồi truyền), chặn `≥11`/có `MaBC2`, không dùng `Update_HSTotNghiep` | `TNB-02 (1/2)` | S | 102 | 1+2 | [x] |
| 104 | **Backend cứu trạng thái:** `GET /cuu/tim?q=` (kèm `giai_thich_khong_hien`), `POST /cuu/chuyen` (nguồn `01/02/03/04/10/12/13` → đích `09/14/17/18`, `ly_do` bắt buộc ≤ 255) + hoàn tác (miễn luật đích, chỉ khi HV chưa đổi tiếp) | `TNB-06 (1/2)` | S | 98 | 1+2 | [x] |
| 105 | **Backend danh sách:** `GET /bc1?loai=`, `GET /bc2?loai=&dong=` ("HV thực tế" bằng **một** `GROUP BY MaBC2`), `GET /nhat-ky` | `TNB-07 (1/2)` | S | 98 | 1+2 | [x] |
| 106 | **Khung phân hệ #5:** thêm `tnbc2` vào `lib/modules.ts` (route `/tot-nghiep-bc2/*`, `db: "GPLX_CSDT"`, băng cam "CSDL: DB Nạp") + token màu + route `App.tsx` + 4 tab (Tốt nghiệp · Báo cáo 2 · Cứu trạng thái · Nhật ký) + `api.ts` + chú giải trạng thái nghiệp vụ (nút "?", tên + mã nhỏ) bám mock | — | M | 97 | 1 | [x] |
| 107 | **UI Tốt nghiệp:** chọn khóa (mặc định khóa 13 tháng + công tắc "Hiện khóa cũ"), danh sách HV, điền chung sổ/quyết định/ngày, số giấy liên tiếp + dán từ Excel + kiểm trùng ngay khi gõ, "Xem lại" → "Ghi N HV", kết quả đã/chưa ghi | `TNB-01 (3/3)` | M | 102,106 | 1 | → PRD |
| 108 | **UI sửa/hủy tốt nghiệp:** sửa nhầm số giấy, "Hủy tốt nghiệp" (hộp nêu tên + số giấy sẽ xóa), khóa nút kèm lý do khi HV đã vào BC2 | `TNB-02 (2/2)` | S | 103,107 | 1 | → PRD |
| 109 | **Lập BC2 bước ①:** chọn khóa — mỗi dòng đếm Sẵn sàng · Thi lại · Cần xem, khóa chưa có BC1 hiện mờ + khóa nút, vào từ "Lập BC2 mới" hoặc từ dòng BC2 đang mở (vào thẳng ②) | `TNB-04 (4/6)` | S | 97,106 | 1 | [x] |
| 110 | **Bước ②:** 4 nhóm HV (Sẵn sàng tích sẵn · Thi lại không tích + nút "Thêm HV thi lại trong N tháng" + gom theo khóa gốc · Cần xem với hướng xử lý 1 chạm · Không đưa được ẩn mặc định), dải "Sẽ đưa vào BC2: A + B = N", tìm/dán danh sách CMT, xử lý ngoại lệ tại chỗ (mini-form số giấy / Cứu trạng thái), danh sách ảo ~3.450 dòng | `TNB-04 (5/6)` | M | 109,104 | 1 | [ ] |
| 111 | **Form BC2:** số gợi ý (sửa được, kiểm trùng), ngày báo cáo, ghi chú, BC1 của khóa (chỉ đọc), "Xem lại" → "Tạo BC2"; dùng cho cả BC2 rỗng từ danh sách và bước ③ | `TNB-03 (2/2)` | S | 98,106 | 1 | → PRD |
| 112 | **Bước ③:** hộp xác nhận "Lập BC2 và thêm N học viên" (tích "CSDL thật"), thanh tiến độ từ 200 HV (poll `/bc2/lo/{lo_id}`), đã/chưa ghi + lý do bỏ qua, "Làm tiếp", "Hoàn tác lần vừa rồi", làm tươi khi quay lại cửa sổ | `TNB-04 (6/6)` | M | 99,110,111 | 1 | → PRD |
| 113 | **UI xem/gỡ/xóa BC2:** danh sách HV trong BC2 (tìm, chọn nhiều, "Gỡ N học viên"), khóa HV có kết quả kèm lý do, cảnh báo `TT_XuLy_Old` rỗng, xóa BC2 rỗng có xác nhận, hoàn tác lô | `TNB-05 (2/2)` | M | 100,106 | 1 | → PRD |
| 114 | **UI Cứu trạng thái:** tìm HV, lý do không hiện, chọn đích (tên nghiệp vụ + mã), lý do bắt buộc, hộp xem lại "cũ → mới", hoàn tác một lần | `TNB-06 (2/2)` | M | 104,106 | 1 | → PRD |
| 115 | **UI danh sách BC2 + nhật ký:** tab Ô tô/Mô tô, lọc đang mở/đã đóng, "Tổng ghi" ≠ "HV thực tế" đánh dấu lệch, bấm dòng → chi tiết; tab Nhật ký (ai · lúc nào · loại · số HV · kết quả) | `TNB-07 (2/2)` | M | 105,106 | 1 | → PRD |
| 116 | **Dán danh sách ở bước ② (110b-1):** hộp dán cột CMT/mã đăng ký (≤ 5.000 dòng) → `POST /bc2/khop-danh-sach` → tích đúng người khớp (Sẵn sàng/Thi lại); báo **số dòng không khớp** và HV khớp nhưng không đưa được kèm lý do; không tích HV ngoài nhóm được phép | `TNB-04 (5/6, phần dán)` | S | 97,110 | 1 | → PRD |
| 117 | **Xử lý ngoại lệ tại chỗ ở bước ② (110b-2):** nhóm Cần xem — "Cập nhật tốt nghiệp" (mini-form số giấy → `POST /tot-nghiep/ghi`, làm tươi, HV tự sang Sẵn sàng); "Cứu trạng thái" mở `PanelCuuTrangThai` ngay trong màn (dùng lại task 114) rồi làm tươi; nhóm Không đưa được — nút nhảy sang xem BC2 đang giữ HV ("gỡ khỏi BC2 đó trước") | `TNB-04 (5/6, phần ngoại lệ)` | M | 107,110,113,114 | 1+3 | → PRD |

> TNB-04 cắt 6 task (96→97→99→109→110→112) cùng trỏ 1 story → PRD `TNB-04` chỉ ✅ khi xong cả 6. TNB-01 cắt 3 (101/102/107), TNB-02 cắt 2 (103/108), TNB-03 cắt 2 (98/111), TNB-05 cắt 2 (100/113), TNB-06 cắt 2 (104/114), TNB-07 cắt 2 (105/115). **Ghi thật chỉ nghiệm thu ở máy CSDT** (dev không ghi happy-path vào DB Nạp thật).

### ✅ Checkpoint 23 — sau task 96-100 (backend BC2)
- [x] **Mức 2** `tn_bc2_rules`: thứ tự xét 4 nhóm (HV ở BC2 mở khác → `khong_duoc`; ô tô `14/17/18` cùng khóa → `thi_lai`; `09` thiếu số giấy → `can_xem`) · `MaBC2` không tồn tại xử như rỗng · đánh số ô tô/mô tô · hoàn tác cứu miễn luật đích · giới hạn đầu vào/độ dài cột.
- [x] **Mức 2** service (cursor giả): `lo_id` gửi hai lần → một lần chạy · "Làm tiếp" **không gọi lại** SP với HV đã `11` đúng BC2 · BC2 đóng giữa chừng → không ghi · xóa BC2 còn HV (đếm theo `MaBC2`) → chặn · `TT_XuLy_Old='11'` sau ghi → cảnh báo · nhật ký không chứa CMT/họ tên · **không bao giờ** có `INSERT/UPDATE/DELETE` trực tiếp.
- [x] `ung-vien` đo trên DB Nạp thật ≤ 2 giây; `pytest` toàn bộ pass; không đụng module cũ.

### ✅ Checkpoint 24 — sau task 101-105 (backend tốt nghiệp + cứu + danh sách)
- [x] **Mức 2:** `Update_CNTN` đúng 8 tham số + lưu sổ trước giữ `03` · hủy giữ sổ/quyết định, chặn `≥11` · kiểm trùng loại trừ chính HV, trong lô và trong DB · khóa chưa bế giảng bị chặn · `xem-lai` không ghi.
- [x] `GET /bc2` "HV thực tế" bằng một truy vấn (không N+1); khớp số liệu DB (455 BC2).
- [x] `pytest` toàn bộ pass.

### ✅ Checkpoint 25 — sau task 106-108 (tab Tốt nghiệp)
- [ ] Phân hệ #5 hiện ở sidebar, băng cam "CSDL: DB Nạp", 4 tab, chú giải trạng thái dùng tên nghiệp vụ (không lộ `TT_XuLy`/SP ở giao diện chính).
- [ ] Tab Tốt nghiệp trên 1 khóa test: điền chung → số giấy liên tiếp → kiểm trùng → Xem lại → Ghi → hủy một HV; nút khóa khi HV đã vào BC2.
- [ ] Playwright 1280/1440: không tràn, đủ dấu, chữ cảnh báo ≥ 13px.

### ✅ Checkpoint 26 — sau task 109-113 (lập BC2 + xem/gỡ đầu–cuối)
- [x] Luồng ô tô và mô tô: ① chọn khóa → ② 4 nhóm (Sẵn sàng tích sẵn, Thi lại không tích, dán 10 CMT khớp đúng) → ③ "Lập BC2 và thêm N" → thấy tiến độ → mở BC2 thấy đúng N HV.
- [x] HV ở BC2 mở khác nằm "Không đưa được" kèm "gỡ khỏi BC2 … trước"; khóa chưa có BC1 mờ không chọn được.
- [x] "Hoàn tác lần vừa rồi" gỡ đúng lô; gỡ HV có kết quả bị khóa; xóa BC2 còn HV bị chặn.
- [x] Bấm "Lập" hai lần/F5 giữa chừng không tạo đôi.

### ✅ Checkpoint 27 — sau task 114-115 (cứu + danh sách + nhật ký) — **nghiệm thu máy CSDT**
- [ ] Cứu trạng thái: nguồn `11/16/19` bị chặn; đích `09` thiếu số giấy bị chặn; hoàn tác về `03` được.
- [ ] Danh sách BC2 + nhật ký khớp thao tác vừa làm; `pnpm build` webui sạch; đóng gói lại exe nếu giao máy.
- [ ] **Ghi thật DB Nạp production + mở PM cũ đối chiếu** (HV, BC2, số giấy hiện đúng; chụp trước/sau cột `NgaySua`/`NguoiSua`/`Transfer_flag`) → nghiệm thu máy CSDT.
- [ ] Chỉ tiêu §11F.8: danh sách ứng viên ≤ 2 giây · thêm 100 HV ≤ 5 giây · từ 200 HV có thanh tiến độ.
- [ ] Login SQL của tool có `EXECUTE` đủ 7 SP + `sp_getapplock` (Prerequisite).

### ✅ Checkpoint 5 — cuối dự án
- [ ] Mọi tiêu chí MUST + SHOULD trong PRD đạt.
- [ ] Đối chiếu bảo mật OG đóng trước go-live (chặn go-live nếu chưa đạt).
- [ ] So giờ máy DB ↔ VPS (Asia/Saigon) trước go-live — MaDK/tên file `.jp2` theo timestamp máy DB.

### ✅ Checkpoint 28 — sau task 116-117 (đóng nốt TNB-04 ở bước ②)
- [x] **Mức 3:** dán 10 CMT → đúng 10 người được tích; dòng không khớp được báo; HV ở nhóm khác nêu lý do (mục còn lại của Checkpoint 26).
- [x] **Mức 3:** HV "Cần xem" thiếu số giấy → mini-form → ghi → tự sang Sẵn sàng; "Cứu trạng thái" tại chỗ rồi quay lại thấy HV đã đổi nhóm.
- [x] `pnpm build` + vitest + E2E sạch; ảnh 1280/1440 vào `anh-kiem/`.
- [ ] TNB-04 đủ "Done khi" (trừ ghi thật → Checkpoint 27 nghiệm thu máy CSDT).

## Phase 11 — NAP-05/NAP-01: Chọn in GPLX theo hạng khóa

> CHANGES #79 (PRD v4.22, TDD v6.25 §10.2, decisions §10). Mô tô (hạng `A*`) mặc định 3 "không thời hạn", ô tô mặc định 2 "có thời hạn"; ô chọn ở ngăn Chuẩn bị; Sync CDB chép nguyên giá trị. **Task 146 đã code + test xong trước khi ghi kế hoạch** (commit `b152bbd` backend · `514d7a4` frontend · `d2834fc` docs; pytest 978 · vitest 147 · Playwright 162; `review-nghiepvu` soát đủ). Còn nghiệm thu thật + đóng gói exe.

| # | Task | Story | Quy mô | Phụ thuộc | Kiểm | Xong |
|---|---|---|---|---|---|---|
| 146 | **Chọn in GPLX (1/1) backend + UI + test:** `nap.chon_in_gplx_mac_dinh` + `build_params_sp_gop` · `NapIn`/`NhapChuanBiIn.chon_in_gplx` (422 ngoài {1,2,3}) · nháp `nhap_chuan_bi.chon_in_gplx` + ALTER · Sync `_HV_SELECT`/`_INSERT_HOSO` chép nguyên (NULL→0) · ô "Chọn in GPLX" ở ngăn Chuẩn bị (`inGplx.ts`, `NapHoSo.tsx`) · `test_in_gplx.py`, `inGplx.test.ts`, `e2e/in-gplx.e2e.ts`. | `NAP-05` | M | 9 | 1+2+3 | [x] |
| 147 | **Đóng gói exe bản có Chọn in GPLX:** build webui TRƯỚC rồi PyInstaller (không chạy `--selftest`). Chạy một mình (sửa dist dùng chung). | — | S | 146 | 1 | [x] |
| 148 | **Nghiệm thu máy CSĐT (NAP-05 + NAP-01):** nạp thử 1 HV khóa mô tô + 1 HV khóa ô tô → `SELECT CHON_IN_GPLX` ra 3 và 2; đổi tay 1 HV sang "ghép" → ra 1; **mở phần mềm cũ đối chiếu thứ tự 3 dòng trên ô `cboInGplx`** với 1/2/3 (khác thì chỉ sửa bảng nhãn `IN_GPLX_NHAN`); đồng bộ CDB 1 HV mô tô → DB đích mang 3. | `NAP-05` | — | 147 | 1 | [ ] |

### ✅ Checkpoint 36 — sau task 146-148 (Chọn in GPLX, CHANGES #79) — **nghiệm thu máy CSĐT**
- [x] `pytest` (978) + `pnpm vitest run` (147) + Playwright (162) sạch; ảnh kiểm ô ở `anh-kiem/2026-10-16-in-gplx/`.
- [ ] Exe mới chạy được trên máy CSĐT, ô "Chọn in GPLX" hiện đúng khóa mô tô/ô tô.
- [ ] **Máy CSĐT:** nạp thật mô tô = 3, ô tô = 2, đổi tay giữ đúng; Sync sang DB đích mang nguyên giá trị.
- [ ] Đối chiếu thứ tự 1/2/3 với ô `cboInGplx` phần mềm cũ.
- [ ] PRD: NAP-05 ⚠️→✅ khi pass (NAP-01 giữ 🔄 theo việc khác của story).
- Ghi nợ ngoài phạm vi (CHANGES #79): HV mô tô đã nạp trước đây mang 2; ~739 HV DB đích đang 0 (25 HV đã vào BC2) — cần script riêng nếu muốn; chưa xác minh Sở dùng trường này trong BC1/BC2.

## Phase 12 — NAP-07/THU-07: GPLX đã có

> CHANGES #81, #82 (PRD v4.24, TDD v6.28 §10.6, decisions §28, mock `ui-mock/gplxdaco.html` đã duyệt). Không đổi schema DB Nạp, không sửa Sync. Làm Tool trước, App web sau.

| # | Task | Story | Quy mô | Phụ thuộc | Kiểm | Xong |
|---|---|---|---|---|---|---|
| 149 | **NAP-07 (1/2) backend tool:** `dung_chuoi_gplx_da_co` + 6 tham số SP · cột `gplx_da_co_json` ở `keo_ve`, `nhap_chuan_bi` + ALTER · `nhap_co`, `keo_ve_cap_nhat` · `NapIn`, `NhapChuanBiIn` · `ds_noi_cap_gplx` + endpoint. | `NAP-07 (1/2)` | M | 146 | 1+2 | [x] |
| 150 | **NAP-07 (2/2) UI tool:** khối GPLX đã có ở ngăn Chuẩn bị (`ComboLoc`, `ODate`), chip, bộ lọc + đếm, thông báo miễn lý thuyết/trùng hạng, cờ "App web có bản mới". | `NAP-07 (2/2)` | M | 149 | 1+3 | [x] |
| 151 | **THU-07 (1/2) VPS:** cột `gplx_da_co` + tự ALTER · kiểm dữ liệu · `POST/PUT`, `/cua-toi`, `/nap/keo` · dọn PII, xóa mềm · tool nhận khi kéo. | `THU-07 (1/2)` | M | 149 | 1+2 | [x] |
| 152 | **THU-07 (2/2) app web:** ô tích + khối nhập một cột ở `Quet.tsx` và form sửa. | `THU-07 (2/2)` | M | 151 | 1+3 | [x] |
| 153 | **Đóng gói exe + deploy VPS bản có GPLX đã có.** Chạy một mình. | — | S | 150, 152 | 1 | [ ] |
| 154 | **Nghiệm thu máy CSĐT:** nạp thật một bằng + hai bằng; mở phần mềm cũ; miễn lý thuyết; Sync giữ chuỗi; đối chiếu bảng nhãn ↔ mã và Cục QLHC. | `NAP-07` | — | 153 | 1 | [ ] |

### ✅ Checkpoint 37 — sau task 149-150 (tool)
- [ ] pytest + vitest + Playwright sạch; ảnh màn Nạp có khối GPLX.
- [ ] Nhập 2 bằng → body nạp đúng; lọc đếm đúng; nháp giữ lại.

### ✅ Checkpoint 38 — sau task 151-154 (app web + nghiệm thu)
- [ ] App web nhập → tool kéo về tự điền → sửa → cờ "App web có bản mới" đúng.
- [ ] Hồ sơ quá hạn dọn cả GPLX.
- [ ] Máy CSĐT đạt task 154; PRD `NAP-07`, `THU-07` chuyển ✅.

## Nhóm chạy song song được

> Chủ dự án chốt **1 người build tuần tự** → không dùng song song. Mục này để tham chiếu nếu về sau mở phiên thứ hai.

**Phải chạy một mình (nếu có parallel):**
- Task 116 → 117 (Phase 10, bước ② lập BC2): cùng sửa `BuocChonHocVien.tsx`, làm tuần tự
- Task 1, 3, 12, 13 — dựng khung, chạm cấu trúc nền của cả app.
- Task 5 — bảng phụ trên DB đích.
- Task 9, 14, 15 — cơ chế lõi (SP import / auth / hàng đợi), nhiều task dựa vào.
- Task 83 → 84 — tuần tự, cùng đụng `routers/ketqua.py` + `CapNhatKQDT.tsx`/`MoKhoaModal.tsx`.
- Task 85 → 94 (Phase 9) — tuần tự, cùng đụng `routers/phancong.py` / `phancong_rules.py` / `PhanCongTheoKhoa.tsx`; task 88 sửa `modules.ts` + `App.tsx` (shell dùng chung).
- Task 96 → 105 (Phase 10 backend) — tuần tự, cùng đụng `routers/tn_bc2.py` / `tn_bc2_service.py` / `tn_bc2_rules.py`; task 106 sửa `modules.ts` + `App.tsx` (shell dùng chung) → chạy một mình.
- **Nhóm song song duy nhất Phase 10 (nếu mở phiên thứ hai):** task 113, 114, 115 — khác file (`XemBc2.tsx`, `CuuTrangThai.tsx`, `DanhSachBc2.tsx`), chỉ an toàn sau 106 và backend tương ứng (100/104/105) xong; chốt hợp đồng endpoint trước.
- Task 118 (QLY-07 sửa ghi ảnh) — chạy một mình: đụng ghi ảnh ra đĩa dùng chung 2 DB, tách hàm dùng chung với `sync_tracuu.py`.
- Task 119 → 120 (KQD-07) — tuần tự, cùng đụng `routers/ketqua.py` + `CapNhatKQDT.tsx`; 120 sửa luật KQD-02 đang chạy.
- Task 127 → 135 (KQD-09 + KQD-10) — tuần tự, cùng đụng `routers/ketqua.py`, `ketqua_xuat.py`, `CapNhatKQDT.tsx`, `CauHinhForm.tsx`, `tool.spec`; **134 chạy một mình** (đóng gói); 133 sửa `routers/config.py` dùng chung toàn app → một mình.
- Task 136 → 145 (KQD-04 đổi #77) — **tuần tự**, cùng đụng `routers/ketqua.py` + `CapNhatKQDT.tsx`; **136 chạy một mình** (sửa `cap_nhat` dùng chung KQD-02/05/06); 140 → 141 cùng sửa `CapNhatKQDT.tsx`; **144 chạy một mình** (đóng gói, `tool.spec`).
- Task 123 → 126 (KQD-08 + KQD-02 giờ/km) — tuần tự, cùng đụng `routers/ketqua.py` + `CapNhatKQDT.tsx`; **126 chạy một mình** (đóng gói, sửa `tool.spec` dùng chung).
- Task 121 → 122 (PCG-06) — tuần tự; 122 sửa `modules.ts` + `App.tsx` (shell dùng chung) → chạy một mình.
- **Nhóm song song (nếu mở phiên thứ hai):** nhánh 119–120 và nhánh 121–122 khác file hoàn toàn (`ketqua*` so với `phancong*`) — an toàn sau khi chốt hợp đồng endpoint; 118 luôn một mình.
- **Nhóm song song duy nhất Phase 9:** task 95 với 91–94 — an toàn nếu tách file riêng (`phancong_rasoat.py`, `RaSoat.tsx`); chốt hợp đồng `GET /ra-soat` trước.

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
| Ghi nhầm vào CDB thật khi phân công GV/xe (Phase 9, task 87/90) | Cao | Server kiểm lại toàn bộ luật + 2 lớp xác nhận (CSDL thật + cảnh báo) + bản nháp; ghi từng dòng báo đã/chưa ghi; nghiệm thu máy CSDT |
| Luật tool nghiêm hơn dữ liệu cũ → chặn oan cặp chồng thời gian cùng khóa đã có (task 85/86) | Trung bình | Hiện 0 trường hợp (rà soát 10/10); hiển thị lý do + cho sửa từng dòng |
| Chưa xác minh gói DKKH/BC1 có chứa GV/xe (task 90) | Thấp–TB | Đang để ⚠ "khóa đã gửi DKKH"; xác minh với hỗ trợ CDB trước khi nâng mức |
| HV đang mở "sửa sau gửi" mà Sở trả 13/14 → SP tiếp nhận chỉ nhận HV `12` nên HV kẹt (task 83/84) | Cao | Cảnh báo + tích cam kết + khối đỏ nhắc; kết xuất lại ngay bằng phần mềm CDB |
| Sở nhận 2 bản KQĐT cho cùng HV (bản đã gửi + kết xuất lại) — chưa rõ Sở xử lý (task 83/84) | Trung bình | Hỏi hỗ trợ CDB/Sở trước khi dùng thật; nghiệm thu máy CSDT |
| Ghi nhầm vào DB Nạp thật khi thêm/gỡ HV hoặc ghi tốt nghiệp (Phase 10, task 99/102) | Cao | Server kiểm lại toàn bộ luật ⛔ trên dữ liệu đọc lại + khóa `tnbc2_ghi` + cổng `xac_nhan_csdl_that`; ghi từng HV báo đã/chưa ghi; chụp trước/sau PM cũ; nghiệm thu máy CSDT (Checkpoint 27) |
| `usp_NguoiLX_Update_ThemHSBC2` không có điều kiện trạng thái → gọi lại cho HV đã `11` đặt `TT_XuLy_Old='11'`, gỡ ra HV kẹt `11` không BC2 (task 99) | Cao | "Làm tiếp" không gọi lại SP với HV đã `11` đúng BC2; bỏ "chuyển giữa BC2"; kiểm `TT_XuLy_Old` sau ghi → cảnh báo |
| PM cũ ghi cột/SP mà ta chưa biết (`NgaySua`, `NguoiSua`, `Transfer_flag`) → dữ liệu tool ghi lệch PM cũ (task 99/102) | Trung bình | Chụp trước/sau PM cũ trước task 99/102 (Prerequisite); nghiệm thu so snapshot cột |
| PM cũ không dùng khóa `tnbc2_ghi` → khe nhỏ ghi chồng giữa lúc tool đọc lại và gọi SP (task 99) | Thấp | Chấp nhận (TDD §16.1): tool một máy, ghi ngắn; đọc lại sát trước SP + kiểm sau ghi |
| `usp_BaoCaoII_Delete` không kiểm HV, `MaBC2` không có FK → xóa nhầm để HV mồ côi (task 100) | Cao | Đếm `MaBC2` mọi `TT_XuLy` = 0 trong khóa, ngay trước SP; thi hành ở máy chủ |
| Sửa server VPS đang chạy prod (task 41/42/44) làm gãy luồng thu thập đang live | Cao | Deploy giờ thấp điểm + verify login/gửi/kéo ngay sau deploy (Checkpoint 8); đổi thêm endpoint, không đổi endpoint cũ |
| Đổi nền cả khóa cũ (task 39/40) từng tạo file mới ở `<IMG_PATH_CSDT>\<MaKH>\` + `_BACKUP` theo khóa và đổi `DuongDanAnh` ở Nạp, DB đích còn trỏ file cũ (task 118) | Trung bình | Chưa biết đã chạy trên khóa thật chưa — kiểm ở máy CSĐT khi nghiệm thu Checkpoint 29; không tự xóa file |
| Task 120 chuyển luật "môn bắt buộc theo hạng" từ UI lên backend, có thể làm lệch ô đỏ của KQD-02 đang chạy (task 119/120) | Trung bình | Unit test đối chiếu luật cũ/mới theo từng hạng + chạy lại test KQD-02 trước khi đóng (Checkpoint 30) |
| Exe thiếu cmap/DLL của `pdfminer`/`pypdfium2` nên nạp PDF không chạy ở máy sạch (task 126) | Trung bình | `tool.spec` đã `collect_all`; kiểm nạp PDF mẫu trong bản đóng gói ở Checkpoint 32 trước khi giao |
| Giờ/km DAT khác số gõ tay cũ ở hầu hết HV (K40: 30/30 khác) → Lưu ghi đè giờ đang có (task 123/124) | Trung bình | Bảng xem trước hiện cũ → mới + tô dòng đã sửa; bỏ tick được từng dòng; không ghi gì trước khi bấm Lưu |
| DAT đổi mẫu báo cáo PDF → bộ đọc báo "không phải báo cáo DAT" (task 123) | Thấp | Báo rõ, không ghi gì; sửa `ketqua_dat.py` theo mẫu mới (4 PDF mẫu trong `thamkhao/` làm smoke) |
| UPDATE trực tiếp 2 cột (không qua SP) bỏ sót cột phụ mà PM cũ đặt — vd cờ chuyển dữ liệu (task 123) | Thấp–TB | SP `_CapNhat` chỉ thêm `NgaySua` (đã đặt); chụp trước/sau PM cũ khi nghiệm thu Checkpoint 32 |
| Excel/Sổ lọt công thức hoặc ký tự điều khiển từ họ tên/tên cơ sở (task 127/130) | Cao nếu bỏ sót | `_sach` + `_ghi_chu` ép kiểu chữ ô bắt đầu `= + - @`, bỏ ký tự điều khiển (task 129); test riêng |
| Sổ in ra lệch bản mẫu thật (tên bị thu chữ, `Trang x/y` đè dòng cuối, số dòng/trang khác ước lượng) vì chưa in thử trên Excel (task 130/132/135) | Trung bình | Thông số bám file mẫu + test so trực tiếp; **in thử ở Checkpoint 33**, mỗi chỗ chỉnh một hằng số |
| Sổ trống cột "Kết quả" với dữ liệu PM cũ lưu kết luận nhưng thiếu điểm (K40: 25 Đạt, 1 người đủ điểm) (task 130/131) | Trung bình | Theo luật sổ mẫu đã chốt; dòng lưu ý giải thích sau khi xuất; chờ user chọn A/B ở task 135 |
| Thư mục `output` cạnh exe không ghi được (cài vào thư mục hệ thống) (task 128) | Thấp | Tự lùi về `%APPDATA%\\pmcsdtlx-tool\\output`; báo đường dẫn đầy đủ + nút "Mở thư mục" |
| `PUT /local/config` từng ghi đè cấu hình → máy CSĐT đã lưu khối ① có thể đã mất chương trình Cũ/Mới từng khóa (task 133) | Trung bình | Đã sửa ngăn mất về sau; khóa nào bị mất phải chọn lại chương trình Cũ/Mới một lần |
| Tiến trình lạ giữ DLL trong `dist` làm PyInstaller lỗi `PermissionError` (task 134) | Thấp | Build ra thư mục tạm rồi `robocopy` sang `dist`; so hash DLL bị giữ |
| Phần mềm CDB cũng đặt `TT_XuLy='90'` ở màn giải trình riêng → hai nơi cùng đặt (task 136/145) | Thấp (cùng giá trị) | Nghiệm thu so trước/sau ở máy CSĐT; guard SQL `TT_XuLy='14'` nên không ghi đè khi đã 90 |
| `usp_CSDT_PheDuyetKQDT_TiepNhan` xóa trắng `GiaiTrinh` ở lần Sở phản hồi kế tiếp; HV `90` mà Sở trả lời bản kết xuất cũ → SP yêu cầu `12` có thể báo lỗi (task 136/137) | Trung bình | Ghi rõ ở TDD §11D.13; nghiệm thu máy CSĐT; không chặn, chỉ báo |
| Sửa `cap_nhat` (hàm dùng chung KQD-02/04/05/06) làm hỏng luồng nhập điểm thường (task 136) | Cao nếu sót | `impact` trước khi sửa + test hồi quy 03→09/10 + `detect_changes` ở Checkpoint 34 |

## Nguồn đối chiếu

> `/tieptheo` so mục này với PRD mỗi buổi để biết kế hoạch còn khớp không. Lệch thì báo user chạy lại `/kehoach` chế độ bổ sung. **Không tự sửa kế hoạch.**

- **Số story trong PRD khi cập nhật:** 63 (thêm `NAP-07`, `THU-07` từ CHANGES #81; giữ nguyên ở CHANGES #77 — KQD-04 đổi, không thêm/bớt mã; thêm `KQD-09`, `KQD-10` từ CHANGES #72, #75; trước đó 59 — thêm `KQD-08` từ CHANGES #69; trước đó 58 — thêm `KQD-07` từ CHANGES #65 + `PCG-06` từ CHANGES #66; `TNB-01..07` từ CHANGES #60; `PCG-01..05` từ CHANGES #54; thêm `THU-06` từ CHANGES #49; `KQD-06` #48; `KQD-05` #45; trước đó `KQD-01/02/03/04` #42; `DGT-01/02/03/04` #38/#39; `TCB-01/02/03/04` #35; `HTG-07` #34; `SYNC-01/02/03` #33; chưa tính NICE `QLY-04`, `THU-03`)
- **Mã story đã đưa vào kế hoạch:** `HTG-01`, `HTG-02`, `HTG-03`, `HTG-07`, `THU-01`, `THU-02`, `THU-04`, `THU-05`, `THU-06`, `THU-07`, `NAP-01`…`NAP-07`, `KHO-01`, `QLY-01`, `QLY-02`, `QLY-03`, `QLY-05`, `QLY-06`, `QLY-07`, `QLY-08`, `QLY-09`, `SYNC-01`, `SYNC-02`, `SYNC-03`, `TCB-01`, `TCB-02`, `TCB-03`, `TCB-04`, `DGT-01`, `DGT-02`, `DGT-03`, `DGT-04`, `KQD-01`, `KQD-02`, `KQD-03`, `KQD-04`, `KQD-05`, `KQD-06`, `KQD-07`, `KQD-08`, `KQD-09`, `KQD-10`, `PCG-01`, `PCG-02`, `PCG-03`, `PCG-04`, `PCG-05`, `PCG-06`, `TNB-01`, `TNB-02`, `TNB-03`, `TNB-04`, `TNB-05`, `TNB-06`, `TNB-07`
- **Mã story chưa đưa vào:** `QLY-04`, `THU-03` (NICE, chưa đủ chi tiết) · **`HTG-04/05/06`** (thêm ở CHANGES #18, đã code thẳng — chưa có task trong plan; cần `/kehoach` bổ sung riêng nếu muốn khớp sổ)
- **Đã đọc `docs/CHANGES.md` tới dòng ngày:** 02/11/2026 (#82)

## Changelog

| Ngày | Thay đổi |
|---|---|
| 02/11/2026 | v31 — bổ sung (CHANGES #81-#82; PRD v4.24, TDD v6.28): thêm **Phase 12** `NAP-07`, `THU-07` — task **149-154** + **Checkpoint 37, 38**. Không đánh số lại task cũ; số story 63. |
| 16/10/2026 | v30 — bổ sung (CHANGES #79; PRD v4.22, TDD v6.25): thêm **Phase 11** `NAP-05`/`NAP-01` ô "Chọn in GPLX" theo hạng khóa — task **146** (đã xong, M) · **147** đóng gói exe · **148** nghiệm thu máy CSĐT + **Checkpoint 36**. Không đánh số lại task cũ; số story giữ 61. |
| 16/10/2026 | v29 — bổ sung nhẹ (CHANGES #78; PRD v4.21, TDD v6.24): **không thêm task, không đánh số lại** — cập nhật mô tả task **137** (mẫu theo `target_key` + khóa ghi cấu hình + lô kiểm đủ điều kiện/giữ riêng), **139** (+3 lý do KQD-07), **140** (header gọn, tab "Cần xử lý", 2 chip), **141** (cảnh báo vàng đứng lâu, ô ghi đè, Quản lý mẫu, "không rõ kết quả") theo `/reviewtdd` §11D.13 + mock đã chỉnh. Số story giữ 61. |
| 16/10/2026 | v28 — bổ sung (CHANGES #77; PRD v4.19, TDD v6.22 §11D.13, decisions §27, mock `ui-mock/ketqua.html` đã duyệt): thêm **task 136-145** + **Checkpoint 34, 35** cho `KQD-04` đổi — HV Sở từ chối sửa xong tự sang `90` khi Đạt + có giải trình, giải trình hàng loạt (136 backend `cap_nhat` · 137 `giai-trinh-lo` + mẫu + lý do trên lưới · 141 UI hàng loạt), `KQD-01` cột Trạng thái + tab đếm (140), `KQD-03` (138/142) và `KQD-07` (139) xét `90`; 143 test, 144 đóng gói, 145 nghiệm thu máy CSĐT. KQD-01/03/04/07 hạ ⏳ ở PRD. Số story giữ 61. |
| 12/10/2026 | v27 — bổ sung (CHANGES #72-#76; PRD v4.12-v4.18, TDD v6.17-v6.21 §11D.11-§11D.12): thêm **task 127-135** + **Checkpoint 33** cho `KQD-09` Xuất Excel kết quả học tập theo khóa (127 backend · 128 UI + lưu `output` · 129 chốt sau `/reviewtdd`) và `KQD-10` Xuất Sổ theo dõi mẫu Phụ lục VI (130 backend · 131 UI · 132 chốt sau `/reviewtdd`), 133 sửa `PUT /local/config` làm rơi cấu hình, 134 đóng gói exe — **127-134 đã code xong, ghi `[x]` kèm commit**, 135 nghiệm thu máy CSĐT còn mở. +6 rủi ro. Không đổi số thứ tự task cũ. |
| 12/10/2026 | v26 — bổ sung (CHANGES #69-#70; PRD v4.12-v4.13, TDD v6.14-v6.15 §11D.10): thêm **task 123-126** + **Checkpoint 32** cho `KQD-08` nạp giờ/km thực hành đường từ PDF DAT (123 backend đọc PDF + xem trước + lưu · 124 UI hộp thoại + lưới `KQD-02` giờ `hh:mm`/nạp sẵn · 125 test + chốt 6 điểm sau `/kiemthu` · 126 đóng gói exe) — **123-125 đã code xong, ghi `[x]` kèm commit**, 126 còn mở. `KQD-08` và `KQD-02` còn ⚠️ Partial tới khi đóng gói exe + nghiệm thu máy CSĐT. +4 rủi ro. Không đổi số thứ tự task cũ. |
| 12/10/2026 | v25 — bổ sung (CHANGES #65, #66, #67; PRD v4.9–v4.10, TDD v6.11–v6.12): thêm **task 118** sửa ghi ảnh đổi nền cả khóa `QLY-07` (ghi đè tại `DuongDanAnh`, sao lưu `<tên>_BACKUP.jp2` cùng thư mục; cuối Phase 3) · **119-120** `KQD-07` Kiểm trước kết xuất (backend luật thuần + endpoint chỉ đọc / UI + KQD-02 dùng chung luật; cuối Phase 6) · **121-122** `PCG-06` Hạn giấy tờ (backend + tab thứ 3; cuối Phase 9) + **Checkpoint 29-31** + 2 rủi ro. Giao diện của 120 và 122 chờ mock `/prototype-next`. +2 story (56→58). 122 task. |
| 11/10/2026 | v24 — bổ sung (không đổi PRD/TDD): thêm **task 116** dán danh sách CMT/mã đăng ký ở bước ② + **task 117** xử lý ngoại lệ tại chỗ ở bước ② (nốt phần "110b" của `TNB-04`; 116 S, 117 M, tuần tự vì cùng sửa `BuocChonHocVien.tsx`) + **Checkpoint 28** |
| 11/10/2026 | v23 — bổ sung (CHANGES #60-#62, PRD v4.6, TDD §11F v6.8 sau /reviewtdd 25 phát hiện): thêm **Phase 10 Tốt nghiệp & Báo cáo 2** (feature mới, prefix `TNB`, 7 story, phân hệ #5, DB Nạp) — task **96** luật thuần + test · **97** backend đọc ứng viên (SP `@MaKH=''` + SELECT bổ sung) · **98** tạo BC2 + nhật ký + khóa `tnbc2_ghi` · **99** `/bc2/lap` chạy nền + `lo_id` + hoàn tác · **100** xem/gỡ/xóa BC2 · **101-103** tốt nghiệp đọc/ghi/hủy · **104** cứu trạng thái · **105** danh sách BC1/BC2 + nhật ký · **106** khung phân hệ #5 · **107-108** UI tốt nghiệp · **109-112** UI lập BC2 3 bước (+ form BC2) · **113** UI xem/gỡ · **114** UI cứu · **115** UI danh sách + nhật ký, + Checkpoint 23-27 + 3 Prerequisite + 5 rủi ro. Chỉ gọi SP có sẵn, không bảng/cột mới. +7 story (49→56). 115 task. |
| 10/10/2026 | v22 — bổ sung (CHANGES #54, PRD v4.3, TDD v6.4 §11E): thêm **Phase 9 Phân công giáo viên – xe** (feature mới, prefix `PCG`, 5 story) — task **85** luật thuần + test · **86** backend đọc + `/kiem-tra` · **87** backend `/ghi` + nhật ký (rủi ro cao làm trước UI) · **88** khung phân hệ #4 · **89** PCG-01 bước ① · **90** bản nháp + Ghi vào CDB · **91-92** PCG-02 bước ② (từng GV + hàng loạt) · **93-94** PCG-03 bước ③ (xe + ghép, gợi ý) · **95** PCG-05 rà soát + Checkpoint 20/21/22. Chỉ ghi `KhoaHoc_GiaoVien`/`KhoaHoc_XeTap`, không bảng mới; không dùng SP xóa lan. +5 story (44→49). 95 task. |
| 10/10/2026 | v21 — bổ sung (CHANGES #53, PRD v4.2, TDD v6.3): thêm **KQD-05 mở rộng "Sửa sau gửi" chọn từng HV** vào cuối Phase 6 — task **83** backend (`POST /mo-sua-sau-gui` + `GET /sua-sau-gui` + nhật ký sqlite `sua_sau_gui`, lùi đúng HV chọn, không xóa gói, `13` 409) + task **84** UI (ô tích + hộp xác nhận + chip/băng cam + khối đỏ KQD-03 + sửa MoKhoaModal) + Checkpoint 19. Thay khóa cứng M1 (decisions §21). Không story mới, giữ 44. 84 task. |
| 08/10/2026 | v20 — bổ sung (CHANGES #51, sau /reviewtdd → TDD v6.1): thêm **Phase 8 NAP-01 "Bỏ khỏi hàng đợi" dòng chờ/lỗi + tombstone** — task **81** backend (bảng `keo_ve_bo_qua` + migrate + lọc trong `keo_ve_upsert` + endpoint `POST /local/nap/bo-qua` xử mọi trạng thái/idempotent/trần 1000 + **GỠ `DELETE /local/keo-ve/:uuid`** của task 38) + task **82** UI (chọn nhiều + nút bỏ cho dòng ⚪/🔴 + xác nhận 2 bước + chuyển DELETE→POST) + Checkpoint 18. Chỉ đụng `staging.sqlite`, KHÔNG đụng VPS/DB. Mở rộng NAP-01, **không story mới, giữ 44**. Sau code → đóng gói lại exe. 82 task. |
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
