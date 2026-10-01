# Kế hoạch build — PMCSĐTLX Thu nhận hồ sơ học viên

> File do `/kehoach` sinh. `/tieptheo` đọc file này để biết làm gì tiếp theo.
> **Thứ tự code** nằm ở đây. **Yêu cầu và trạng thái story** nằm ở `docs/PRD.md`.
> Cập nhật lần cuối: 01/10/2026 (v3 — bổ sung mô tả task 20 NAP-01 + task 22 QLY-01 theo CHANGES #6)

## Quyết định về thứ tự

- **Risk-first (theo TDD §17):** làm **Tool nạp DB trước** vì đây là mắt xích khó & rủi ro cao nhất — sinh `SoHoSo` qua `sp_getapplock`, gọi **1 SP gộp app cũ** `usp_QuangLA_...ThemMoiCapNhat`, ghi ảnh hướng A riêng (UPDATE 5 cột), xuất `.jp2` khớp app cũ. Hỏng chỗ này ở cuối dự án = làm lại từ đầu; nên chứng minh sớm bằng **nạp tay 1 HV** (AS-003) rồi mới dựng đường thu thập. *(01/10 — đổi 3 SP rời → 1 SP gộp, bỏ compensation vì SP atomic; xem CHANGES #4/#5.)*
- **Đảo ưu tiên có chủ đích (Luật 2 > Luật 3):** vài story **MUST** (`KHO-01`, `HTG-03`) nằm ở Phase 3 vì độc lập, rủi ro thấp, không nằm trên đường chứng minh lõi (DB đã có khóa thật + hồ sơ thật để test NAP). SHOULD `QLY-*` cũng Phase 3 vì phụ thuộc `NAP-05`.
- **`HTG-01` cắt 3 task theo nơi chạy:** ① cấu hình kết nối tool (local, Phase 1) · ② auth JWT trên VPS (Phase 2) · ③ login UI + tool gate (Phase 2). PRD chỉ chuyển ✅ khi xong cả 3.
- **`NAP-05` và `HTG-02` cắt đôi** để không còn task cỡ L.
- **1 người build → tuần tự một luồng**, không tách nhánh song song (quyết định chủ dự án 01/10/2026).

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
| 29 | **Rework UX app web** (CHANGES #12): endpoint `GET /api/ho-so/:uuid/anh` (collector, `created_by`) + ảnh thật list/chi tiết + modal Sửa/Chụp lại khi chờ nạp (chỉ xem khi importing/imported). `server/ho_so.py` + `webapp/DaGui.tsx` + `api.ts` | `THU-02` | M | 19,15 | 1+2 | → PRD |

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
| 26 | Đóng gói tool PyInstaller (.exe) + đối chiếu bảo mật OG (không `sa`, không log CCCD, HTTPS) | — | M | tất cả | 1 | [ ] |

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

## Nguồn đối chiếu

> `/tieptheo` so mục này với PRD mỗi buổi để biết kế hoạch còn khớp không. Lệch thì báo user chạy lại `/kehoach` chế độ bổ sung. **Không tự sửa kế hoạch.**

- **Số story trong PRD khi lập:** 16 (15 MUST/SHOULD + QLY-05; chưa tính NICE `QLY-04`, `THU-03`)
- **Mã story đã đưa vào kế hoạch:** `HTG-01`, `HTG-02`, `HTG-03`, `THU-01`, `THU-02`, `NAP-01`…`NAP-06`, `KHO-01`, `QLY-01`, `QLY-02`, `QLY-03`, `QLY-05`
- **Mã story chưa đưa vào (Chờ chốt):** `QLY-04`, `THU-03` (NICE, chưa đủ chi tiết)
- **Đã đọc `docs/CHANGES.md` tới dòng ngày:** 01/10/2026 (#12)

## Changelog

| Ngày | Thay đổi |
|---|---|
| 01/10/2026 | v1 — kế hoạch đầu tiên, 26 task (3 phase, risk-first theo TDD §17) |
| 01/10/2026 | v2 — bổ sung (CHANGES #4/#5): reconcile task 9+10 về `[ ]` + đổi mô tả sang 1 SP gộp hướng A (bỏ compensation); thêm task 27 `QLY-05` (nạp/thay ảnh HV đã có). 27 task. |
| 01/10/2026 | v3 — bổ sung (CHANGES #6): cập nhật mô tả task 20 `NAP-01` (IA 2 chế độ, IN HOA, check chính tả mức A, nạp lô badge ⚪🔴🟢, cảnh báo nổi bật) + task 22 `QLY-01` (chế độ Tra cứu DB, tìm mọi khóa kể cả BC1). Không thêm/xóa/đổi số task — vẫn 27 task. |
| 01/10/2026 | v4 — bổ sung (CHANGES #12): thêm task **28** (rework UX THU-01: màn vào + khung bám QR + layout dính đáy + header) + task **29** (rework UX THU-02: endpoint ảnh collector + ảnh thật + xem/sửa/chụp lại) vào cuối Phase 2. 29 task. THU-01/02 đã hạ ⏳ ở PRD. |
