# Technical Design Document — Thu nhận hồ sơ học viên

> **Version:** 1.2 · **Ngày:** 30/09/2026 · **Status:** Draft (đã qua review)
> **PRD reference:** `docs/PRD.md` (v2) · **Quyết định:** `docs/TDD-decisions.md`

---

## 1. Overview

### Bài toán
Nhân viên phải ngồi tại máy chứa DB gõ tay từng học viên từ CCCD, tự tra/đổi địa chỉ sau sáp nhập 2025, chụp ảnh rời — chậm, dễ sai, nghẽn đầu khóa, bị trói tại một máy.

### Giải pháp
Tách **thu thập** (app web quét QR + chụp ảnh, đẩy lên VPS) khỏi **nạp** (tool tại máy DB map địa chỉ, xử lý ảnh, nạp vào DB `GPLX_CSDT` qua stored procedure có sẵn). Bản ghi tạo ra hiển thị y như app cũ.

### Scope của TDD này
Bao gồm: app web thu thập, backend VPS (hàng đợi + PII), tool nạp DB (map địa chỉ, xử lý ảnh, nạp qua SP, quản lý hồ sơ, tạo khóa). **Không bao gồm:** sát hạch, Báo cáo 1/2, cấp/in GPLX, báo cáo Sở/Cục, nâng hạng đầy đủ, kết xuất báo cáo (giai đoạn sau).

### Quyết định kiến trúc quan trọng
- **3 thành phần tách rời** (app web · VPS · tool) — vì chỉ tool nối được SQL Server + ghi ổ D + xử lý ảnh, máy DB sau NAT nên phải pull ra.
- **Ghi DB đích chỉ qua Stored Procedure** (`pymssql`, không ORM) — vì bản ghi phải khớp 100% app cũ và an toàn DB production.
- **Tool pull ra VPS (outbound HTTPS)** — vì máy DB sau NAT, không mở cổng, không cần IP tĩnh.
- **`DM_DVHC_MAP` là bảng phụ trong `GPLX_CSDT`** — vì cập nhật danh mục một chỗ, không phải build lại tool.
- **Ảnh thô lưu filesystem VPS + path trong PostgreSQL** — vì đơn giản, rẻ cho quy mô nhỏ.
- **FE React build sẵn ở máy dev** — vì máy CSDT không cần cài Node, chỉ chạy 1 `.exe`.

---

## 2. System Architecture

*Vì sao tách 3 phần: trình duyệt không nối được SQL Server/ghi .jp2, nên phần "chạm DB" phải là tiến trình riêng tại máy DB.*

### 2.1 High-level diagram

```
┌────────────────────────┐        ┌─────────────────────────────┐        ┌──────────────────────────────┐
│  APP WEB (PWA)         │        │      BACKEND VPS            │        │   TOOL tại MÁY DB (.exe)     │
│  React+Vite+shadcn     │        │   FastAPI + PostgreSQL     │        │  FastAPI(local) + React      │
│  điện thoại / desktop  │ HTTPS  │  - Auth (JWT)              │ HTTPS  │  - UI localhost              │
│  - Quét QR CCCD        │──────► │  - Hàng đợi hồ sơ chờ nạp  │◄────── │  - Kéo về (pull, API key)    │
│  - Chụp ảnh thô        │  token │  - Ảnh thô (filesystem)    │  pull  │  - Map DVHC, xử lý ảnh       │
│  - Nhập/sửa, gửi       │        │  - Job xóa PII 30 ngày     │        │  - rembg + Pillow (.jp2)     │
└────────────────────────┘        └─────────────────────────────┘        └───────────────┬──────────────┘
                                                                                          │ LAN (pymssql)
                                                                          ┌───────────────▼──────────────┐
                                                                          │  SQL SERVER GPLX_CSDT        │
                                                                          │  - usp_* (Insert/Update/Del) │
                                                                          │  - DM_* , QTHT_ThamSoHT      │
                                                                          │  (CHỈ ĐỌC — tool không ghi)  │
                                                                          └──────────────┬───────────────┘
                                                                          ┌──────────────▼───────────────┐
                                                                          │  Ổ D: \GPLXCSDT\ANHCDUNG\    │
                                                                          │  <MaKhoaHoc>\70004-*.jp2     │
                                                                          └──────────────────────────────┘
```

### 2.2 Các thành phần chính

| Component | Vai trò | Tech |
|---|---|---|
| **App web** | Quét QR CCCD, nhập, chụp ảnh thô, gửi VPS | React + Vite (PWA) + Tailwind + shadcn/ui |
| **Backend VPS** | Auth, hàng đợi hồ sơ chờ nạp, lưu ảnh thô, job xóa PII | Python FastAPI + PostgreSQL |
| **Tool máy DB** | Kéo về, map địa chỉ, xử lý ảnh, nạp qua SP, quản lý hồ sơ, tạo khóa | Python FastAPI (localhost) + React (static) + pymssql + Pillow + rembg |
| **Staging tool** | Lưu tạm hồ sơ đã kéo + bảng tra cứu `DM_DVHC_MAP` (ánh xạ địa chỉ) | SQLite (cục bộ máy DB) |
| **DB đích** | Nguồn sự thật hồ sơ học viên | SQL Server `GPLX_CSDT` (SP có sẵn) |
| **Kho ảnh đích** | File `.jp2` chân dung | Filesystem ổ D máy DB |

### 2.3 Deployment topology

```
VPS (domain HTTPS)
├── FastAPI (uvicorn/gunicorn)   ← API + phục vụ static PWA + APScheduler (job PII)
├── PostgreSQL                    ← users, ho_so_thu_thap, audit_log
├── Filesystem /data/anh-tho/     ← ảnh thô (xóa cùng bản ghi 30 ngày)
└── Nginx (443)                   ← reverse proxy + SSL (Let's Encrypt)

Máy DB (Windows, sau NAT)
├── tool.exe (PyInstaller)        ← FastAPI localhost + UI, pull ra VPS, nối SQL Server LAN
│   └── staging.sqlite            ← hồ sơ đã kéo
├── SQL Server GPLX_CSDT
└── D:\GPLXCSDT\ANHCDUNG\         ← .jp2 đích
```

### 2.4 Cây thư mục nguồn trong repo

```
pmcsdtlx-thunhan/
├── webapp/            React+Vite (PWA)          → app web thu thập (build → static, VPS phục vụ)
│   └── src/
├── server/            Python FastAPI            → dịch vụ `api` (VPS)
│   ├── app/           routers, models, jobs
│   └── tests/         pytest (auth, queue, pii-job)
├── tool/              Python FastAPI + React     → tool máy DB (đóng gói PyInstaller)
│   ├── app/           pull, dvhc-map, image, import(SP), khoahoc
│   │                  + sync: routers/sync.py, sync_service.py, sync_helpers.py, sync_history.py (§11B — không import nạp)
│   ├── webui/         React (build → static nhúng) — ToolLayout = sidebar module + sub-nav; pages/sync/*
│   ├── db/            builder nạp DM_DVHC_MAP → SQLite cục bộ + dataset vietnamadminunits đóng kèm
│   └── tests/         pytest (sohoso, import-sp, image-jp2)
├── docker-compose.yml (VPS: api + postgres + nginx)
└── docs/              PRD · TDD · TDD-decisions · prd-review · (BUILD-PLAN sau)
```
*(Tên thư mục trùng tên dịch vụ để `docker-compose` khỏi dịch qua lại. `tool/` không lên docker — đóng gói .exe.)*

---

## 3. Data Model

*Vì sao 3 kho tách: DB đích là hệ cũ (chỉ ghi qua SP), nên dữ liệu trung chuyển + tài khoản của hệ thống mới phải nằm ở PostgreSQL riêng, không đụng schema production.*

### 3.1 Quan hệ tổng thể

```
[PostgreSQL - VPS]                         [SQL Server GPLX_CSDT - máy DB]
users ──< ho_so_thu_thap                   (hiện có) NguoiLX ──1:1── NguoiLX_HoSo ──< NguoiLXHS_GiayTo
             │  (trang_thai, anh_tho_path,            KhoaHoc, DM_*, QTHT_ThamSoHT, BaoCaoI
             │   ma_dk sau khi nạp)                   (mới)  DM_DVHC_MAP
             └──< audit_log

[SQLite - tool] staging: bản sao ho_so_thu_thap đã kéo (theo uuid)
```

### 3.2 PostgreSQL (VPS) — schema mới

```sql
-- ────────────────────────────────────────────
-- USERS & AUTH
-- ────────────────────────────────────────────
CREATE TABLE users (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  username      VARCHAR(50) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,          -- bcrypt
  ho_ten        VARCHAR(100),
  vai_tro       VARCHAR(20) NOT NULL DEFAULT 'collector'
                CHECK (vai_tro IN ('collector','operator','admin')),
  is_active     BOOLEAN NOT NULL DEFAULT TRUE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_login_at TIMESTAMPTZ
);

-- ────────────────────────────────────────────
-- HỒ SƠ THU THẬP (hàng đợi chờ nạp)
-- ────────────────────────────────────────────
CREATE TABLE ho_so_thu_thap (
  uuid          UUID PRIMARY KEY DEFAULT gen_random_uuid(),  -- idempotency key
  trang_thai    VARCHAR(20) NOT NULL DEFAULT 'pending'
                CHECK (trang_thai IN ('pending','importing','imported','deleted')),
                -- Bỏ 'duplicate': trùng CCCD trong khóa (NAP-06) chỉ CẢNH BÁO, giữ 'pending' (review §7.2)
  -- Dữ liệu cá nhân (từ QR/nhập tay)
  so_cccd       VARCHAR(12),
  so_cmnd_cu    VARCHAR(9),
  ho_ten        VARCHAR(70),
  ngay_sinh     VARCHAR(8),                       -- yyyymmdd (khớp DB đích)
  gioi_tinh     CHAR(1) CHECK (gioi_tinh IN ('M','F','U')),
  noi_tt_raw    TEXT,                             -- địa chỉ text thô từ QR
  ngay_cap_cccd DATE,
  noi_cap_cccd  VARCHAR(100),
  -- Ảnh thô
  anh_tho_path  TEXT,                             -- đường dẫn file trên VPS
  -- Chống trùng & truy vết
  ma_dk         VARCHAR(25),                      -- điền sau khi nạp thành công
  imported_at   TIMESTAMPTZ,
  imported_by   UUID REFERENCES users(id),        -- operator nạp
  locked_by     UUID,                             -- tool đang importing (khóa)
  locked_at     TIMESTAMPTZ,
  created_by    UUID REFERENCES users(id),        -- collector gửi
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ────────────────────────────────────────────
-- AUDIT LOG (ai gửi/ai nạp/ai xóa — PII)
-- ────────────────────────────────────────────
CREATE TABLE audit_log (
  id         BIGSERIAL PRIMARY KEY,
  actor_id   UUID REFERENCES users(id),
  hanh_dong  VARCHAR(30) NOT NULL,               -- 'gui','keo','nap','xoa_pii','dang_nhap'
  uuid_hs    UUID,
  chi_tiet   JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ────────────────────────────────────────────
-- TOKEN BLOCKLIST (logout thu hồi phiên — xem §5.1)
-- jti token đã đăng xuất, giữ tới khi token hết hạn (exp) rồi dọn.
-- ────────────────────────────────────────────
CREATE TABLE token_blocklist (
  jti        UUID PRIMARY KEY,
  exp        TIMESTAMPTZ NOT NULL,                 -- hết hạn gốc của token → tới đây dọn được
  revoked_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ────────────────────────────────────────────
-- INDEXES
-- ────────────────────────────────────────────
CREATE INDEX idx_hstt_trangthai ON ho_so_thu_thap(trang_thai);
CREATE INDEX idx_hstt_pending_time ON ho_so_thu_thap(created_at) WHERE trang_thai = 'pending';
CREATE INDEX idx_hstt_cccd ON ho_so_thu_thap(so_cccd);
CREATE INDEX idx_hstt_creator ON ho_so_thu_thap(created_by);   -- lọc /api/ho-so/cua-toi theo collector
CREATE INDEX idx_audit_created ON audit_log(created_at);
CREATE INDEX idx_blocklist_exp ON token_blocklist(exp);         -- job dọn token hết hạn
```

### 3.3 Bảng tra cứu DVHC — SQLite CỤC BỘ của tool (KHÔNG trong GPLX_CSDT)

> Bảng ánh xạ địa chỉ cũ → xã mới nằm trong SQLite cục bộ của tool (cùng file `staging.sqlite`),
> **không** tạo trong `GPLX_CSDT`. Production chỉ bị ĐỌC (`DM_DVHC`). Tool **tự dựng** bảng này:
> đọc `DM_DVHC (TrangThai=1)` của máy đích + dataset `vietnamadminunits` (CSV tĩnh) đóng kèm tool,
> nối theo TÊN (tỉnh mới + xã mới ngắn) để lấy đúng mã của **chính máy đích** → mang `.exe` sang
> máy/cơ sở khác vẫn chạy, không phụ thuộc máy hiện tại. Thao tác "Đồng bộ danh mục" dựng lại bảng.

```sql
-- SQLite cục bộ (staging.sqlite). Tool tự dựng, không ghi vào GPLX_CSDT.
CREATE TABLE IF NOT EXISTS dm_dvhc_map (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  ten_tinh_cu   TEXT NOT NULL,   -- chuẩn hóa: lower, bỏ tiền tố (khi tra khớp y hệt)
  ten_huyen_cu  TEXT NOT NULL,
  ten_xa_cu     TEXT NOT NULL,
  ma_dvhc_moi   TEXT NOT NULL,   -- = DM_DVHC.MaDvhc (TrangThai=1) của máy đích
  ma_dvql_moi   TEXT NOT NULL,   -- = DM_DVHC.MaDVQL
  ten_xa_moi    TEXT NOT NULL,   -- tên hiển thị (giữ nguyên dấu/hoa thường)
  ten_tinh_moi  TEXT NOT NULL,
  is_divided    INTEGER NOT NULL DEFAULT 0  -- 1 = xã cũ chia nhiều xã mới → cần chọn tay
);
CREATE INDEX IF NOT EXISTS ix_dvhcmap_cu ON dm_dvhc_map(ten_tinh_cu, ten_huyen_cu, ten_xa_cu);
```

### 3.4 Bảng hiện có của DB đích (CHỈ ĐỌC/ghi qua SP — không redesign)

| Bảng | Dùng để |
|---|---|
| `NguoiLX` (PK MaDK) | thông tin cá nhân — ghi qua `usp_NguoiLX_Insert` |
| `NguoiLX_HoSo` (PK MaDK) | hồ sơ + `DuongDanAnh`,`ChatLuongAnh` — `usp_NguoiLX_HoSo_Insert/Update` |
| `NguoiLXHS_GiayTo` | giấy tờ — `usp_NguoiLXHS_GiayTo_Insert` |
| `KhoaHoc` | khóa học — `usp_KhoaHoc_Insert`; lọc chưa BC1 qua `BaoCaoI` |
| `DM_DVHC` | tỉnh/xã (`TrangThai=1` = mới) — `usp_DM_DVHC_SelectAll_Tinh`, `usp_DM_DVHC_SelectDanhSachXaPhuongTheoTinh` |
| `DM_LoaiHSo_GiayTo`, `DM_GiayTo` | giấy tờ bắt buộc theo (loại, hạng) |
| `DM_HangDT`, `DM_HangGPLX` | hạng đào tạo (tạo khóa) |
| `QTHT_ThamSoHT` | config `IMG_PATH_CSDT`, `MA_CSDT` |

### 3.5 Bảo vệ PII
Ảnh thô + số CCCD trên VPS là PII: HTTPS toàn bộ; `password_hash` bcrypt; job tự xóa bản ghi + ảnh sau 30 ngày; không log nội dung CCCD (audit_log chỉ ghi hành động + uuid).

---

## 4. API Design

*Vì sao REST + token: đơn giản, hợp FastAPI; tool và app web dùng chung kiểu xác thực, phân biệt bằng vai trò + API key.*

### 4.1 Base & Auth
```
Base VPS:  https://<domain>/api
Auth:      Bearer JWT (app web + tool đăng nhập người dùng)
           X-Tool-Key: <api_key>  (tool gọi endpoint pull/mark — khóa máy)
```

### 4.2 Auth
```
POST /api/auth/login            Đăng nhập → JWT
POST /api/auth/logout           Thu hồi phiên
GET  /api/auth/me               Thông tin user hiện tại
POST /api/auth/doi-mat-khau     Tự đổi mật khẩu (kiểm mật khẩu hiện tại)        [HTG-06]
GET  /api/admin/users           (admin) DS tài khoản, phân trang                [HTG-05]
POST /api/admin/users           (admin) tạo tài khoản                           [HTG-05]
PUT  /api/admin/users/:id       (admin) sửa vai trò / khóa-mở (is_active)       [HTG-05]
POST /api/admin/users/:id/reset-mat-khau  (admin) đặt mật khẩu mới              [HTG-05]
GET  /api/admin/tool-key        (admin) xem TOOL_API_KEY để cấu hình tool       [HTG-04]
```

> **HTG-04/05/06 — bảo mật (§5.3):** `GET /api/admin/tool-key`, `GET|POST|PUT /api/admin/users*`, reset mật khẩu → `require_role("admin")`. `POST /api/auth/doi-mat-khau` cho mọi vai trò nhưng **chỉ đổi của chính mình** (theo `sub` trong JWT, không nhận user_id ngoài). Mật khẩu **băm bcrypt** trước khi lưu; **không log** giá trị `TOOL_API_KEY` lẫn mật khẩu. Khóa/mở bằng `is_active` (KHÔNG xóa cứng — giữ dấu vết PII); chặn admin tự khóa chính mình (so `id` với user hiện tại). `tool-key` đọc `get_settings().tool_api_key`; endpoint này **mở rộng bề mặt lộ secret** — đánh đổi đã chốt ở PRD `HTG-04`, bù lại chỉ admin + không cache/không log.

### 4.3 Hồ sơ thu thập (app web — collector)
```
POST /api/ho-so                 Gửi hồ sơ mới (uuid client-gen, idempotent)
GET  /api/ho-so/cua-toi         DS mình đã gửi
PUT  /api/ho-so/:uuid           Sửa (khi pending)
POST /api/ho-so/:uuid/anh       Upload ảnh thô (multipart)
GET  /api/ho-so/:uuid/anh       Tải lại ảnh thô CỦA MÌNH (hiện thumbnail list/chi tiết — THU-02, CHANGES #12)
GET  /api/ho-so/kiem-trung?cccd=<>  Kiểm CCCD đã có hồ sơ pending/importing trong hàng đợi CSDT — cảnh báo mềm (THU-04, CHANGES #13)
DELETE /api/ho-so/:uuid         Xóa hồ sơ đã gửi — SOFT-DELETE (trang_thai→'deleted'), CHỈ khi 'pending'; collector CHỈ của mình (kiểm created_by, chống IDOR), admin bất kỳ; 'importing'/'imported'→409. Ghi audit_log (THU-05, CHANGES #24)
```
> **CAS (review #24):** chuyển trạng thái bằng UPDATE có điều kiện nguyên tử, KHÔNG đọc-rồi-ghi: `UPDATE … SET trang_thai='deleted' WHERE uuid=:u AND trang_thai='pending'` (như `lock` §7.1); 0 dòng bị sửa → **409** (hồ sơ vừa bị tool `lock` sang `importing` đúng lúc collector bấm xóa — EC đồng thời THU-05). Soft-delete ghi **mốc thời điểm vào `audit_log`** (đã có `created_at` + `idx_audit_created`) → endpoint `GET /api/nap/da-xoa?since=` (§4.4) lọc theo mốc này, KHÔNG cần thêm cột `deleted_at`.

### 4.4 Nạp (tool — operator, kèm X-Tool-Key)
```
GET  /api/nap/keo?limit=200     Kéo DS pending (không lấy imported/deleted); limit mặc định 200, có cursor
POST /api/nap/:uuid/lock        Khóa bản ghi (→ importing) trước khi nạp
POST /api/nap/:uuid/da-nap      Đánh dấu da_nap (kèm ma_dk) + mở khóa
POST /api/nap/:uuid/unlock      Mở khóa khi nạp lỗi (→ pending)
POST /api/nap/:uuid/tra-ve-cho-nap  Trả hồ sơ ĐÃ NẠP về chờ nạp (imported→pending, gỡ ma_dk) — tool gọi sau khi gỡ HV khỏi CSDT (QLY-08, CHANGES #24). Bản ghi đã 'deleted' → 409 (không còn để trả về)
GET  /api/nap/da-xoa?since=<ts>  DS uuid đã chuyển 'deleted' từ mốc <ts> (đọc audit_log) — tool dùng khi "Kéo về" để BỎ dòng staging collector đã xóa ở app web (NAP-01/THU-05, CHANGES #24)
GET  /api/nap/tra-uuid?ma_dk=<>  Tra uuid gốc theo ma_dk (VPS lưu ma_dk khi da-nap) — fallback cho QLY-08 bước 2 khi staging nap_xong local không còn
```
> **CAS (review #24):** `tra-ve-cho-nap` chuyển nguyên tử `UPDATE … SET trang_thai='pending', ma_dk=NULL WHERE uuid=:u AND trang_thai='imported'`; 0 dòng bị sửa → **409**. Gọi lại khi đã `pending` → 0 dòng → coi như **idempotent** (báo "đã về chờ nạp", không lỗi) để nhánh retry QLY-08 bước 4 an toàn.

### 4.5 Quản trị PII (admin)

> **Phục vụ:** `HTG-03`

```
GET    /api/admin/ho-so?limit=100  Lọc bản ghi (trạng thái/ngày); limit mặc định 100, có phân trang
DELETE /api/admin/ho-so/:uuid      Xóa thủ công (bản ghi + ảnh thô)
```

### 4.6 Tool local (localhost — không ra internet)

> Mọi endpoint `/local/*` nghiệp vụ **buộc kèm session token cục bộ của tool** (xem §5.5) — không mở trống dù chạy localhost (máy DB có thể nhiều tài khoản Windows / tiến trình khác).
> **Ngoại lệ (A1, task 17):** `/local/config*` và `/local/auth/*` **KHÔNG** gác token — config là bước mồi đặt URL VPS (chưa có URL thì không đăng nhập được), auth là cửa đăng nhập.

```
POST /local/auth/login               Đăng nhập (tool gọi VPS thay mặt) → session token cục bộ   [HTG-01③]
GET  /local/auth/me                  Thông tin phiên hiện tại                                  [HTG-01③]
POST /local/auth/logout              Thu hồi session cục bộ                                    [HTG-01③]
GET  /local/config                   Đọc cấu hình hiện tại (che password)                     [HTG-01]
PUT  /local/config                   Lưu cấu hình (SQL Server + URL VPS + API key), mã hóa cục bộ [HTG-01]
POST /local/config/test              Kiểm tra kết nối: thử nối SQL Server + ping VPS           [HTG-01]
GET  /local/khoa-hoc?loai=moto|oto   Khóa chưa BC1 theo loại (query SQL Server)
GET  /local/dvhc/tinh                DS tỉnh (usp_DM_DVHC_SelectAll_Tinh)
GET  /local/dvhc/xa?tinh=<MaDVQL>    DS xã theo tỉnh
POST /local/dvhc/map                 Map địa chỉ text → mã (DM_DVHC_MAP)
POST /local/anh/xu-ly                Căn 3:4 + xóa phông + preview
POST /local/nap                      Nạp 1 HV (SoHoSo + 3 SP + ghi .jp2)
POST /local/khoa-hoc/tao             Tạo khóa (usp_KhoaHoc_Insert)
GET  /local/ho-so?makh=<>            Tra cứu HV theo khóa (usp_NguoiLX_Select_By_MaKH)
PUT  /local/ho-so/:madk              Sửa (usp_NguoiLX_*_Update)
POST /local/ho-so/:madk/doi-khoa     Đổi khóa + di chuyển ảnh
DELETE /local/ho-so/:madk            Xóa HV + xóa mềm ảnh (chặn khi khóa đã BC1 — §11.3)
GET  /local/ho-so/anh?ma_dk=<>       Ảnh chân dung .jp2→PNG (xem); file mất→404, hỏng→422     [QLY-01]
GET  /local/ho-so/anh-thumb?ma_dk=<> Thumbnail PNG avatar lưới (cache cục bộ, lazy)            [QLY-01]
DELETE /local/keo-ve/:uuid           Bỏ dòng đã-nạp khỏi hàng đợi staging (tool-local)        [NAP-01]
POST /local/khoa/:ma_kh/doi-nen      Đổi nền trắng cả khóa (job nền + tiến độ)                 [QLY-07]
```

### 4.7 Ví dụ

**POST /api/ho-so** (app web gửi)
```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "so_cccd": "070202008455",
  "so_cmnd_cu": null,
  "ho_ten": "NGUYỄN THANH TÂM",
  "ngay_sinh": "20021121",
  "gioi_tinh": "M",
  "noi_tt_raw": "Xã Phú Nghĩa, Huyện Bù Gia Mập, Tỉnh Bình Phước",
  "ngay_cap_cccd": "2021-03-10"
}
// 201 → { "uuid": "...", "trang_thai": "pending" }   (gửi lại cùng uuid → trả 200, không tạo trùng)
```

**POST /local/nap** (tool → sau khi map địa chỉ + xử lý ảnh)
```json
{
  "uuid": "550e8400-...",
  "ma_khoa_hoc": "70004K26B010",
  "noi_tt_madvhc": "25267", "noi_tt_madvql": "75",
  "anh_da_xu_ly": "<base64/tạm>",
  "giay_to_tick": [1,2,3]
}
// 200 → { "ma_dk": "70004-20260930xxxxxxx", "so_ho_so": "056" }
```

---

## 5. Authentication & Authorization

> **Phục vụ:** `HTG-01`
*Vì sao JWT + API key: token người dùng để truy vết ai thao tác; API key riêng cho máy tool để phân biệt kênh pull, thu hồi độc lập.*

### 5.0 Cấu hình tool (HTG-01 → bảng header HTG-07)
Tool có **bảng Cấu hình** (gọi `/local/config`): nhập kết nối SQL Server (server/database/user/password), URL VPS, API key; nút **"Kiểm tra kết nối"** (`POST /local/config/test`) thử nối SQL Server + ping VPS trước khi lưu; lưu vào config cục bộ **mã hóa** (§15). Chưa cấu hình xong → chặn mọi chức năng nạp.

> **04/10/2026 (CHANGES #34, HTG-07):** bảng này **không còn là màn route riêng** `/tool/cau-hinh` — dời lên **panel mở từ icon ⚙ trên header**, dùng chung mọi màn, và **gộp** khối quản lý nhiều DB đích Sync (SYNC-02, §11B.1) vào cùng panel, chia **hai khối tách bạch**: ① Kết nối chung + **DB NGUỒN để Nạp** `GPLX_CSDT` · ② **các DB ĐÍCH để Sync** (nhiều, chọn mặc định). Backend `/local/config*` + `/local/sync/targets` + config-store **giữ nguyên** — chỉ dời/gộp lớp UI. Dựng bằng `impeccable` + `ui-ux-pro-max`.

### 5.1 Luồng đăng nhập
```
POST /api/auth/login → verify bcrypt → JWT (HS256, expire 8h) → trả token
App web lưu token (memory/secure); tool lưu trong config cục bộ (mã hóa).
```
- **Kiểm tra mỗi request bảo vệ:** đọc `is_active` + `vai_tro` **từ DB** theo `sub`, KHÔNG tin claim trong token — để admin khóa tài khoản / đổi vai trò có hiệu lực ngay, không chờ hết 8h (trục "quyền đổi giữa chừng").
- **logout:** ghi `jti` của token vào blocklist ngắn hạn (tới `exp`) trong PostgreSQL; request mang token đã blocklist → 401. (Không có blocklist thì logout chỉ xóa token phía client, token vẫn hợp lệ tới hạn — nêu rõ để không hiểu nhầm.)

### 5.2 JWT payload
```json
{ "sub": "user-uuid", "username": "nvthu01", "vai_tro": "collector", "exp": 1730000000 }
```

### 5.3 Chặn quyền
- `collector`: chỉ `/api/ho-so*` (tạo/sửa của mình). KHÔNG gọi được `/api/nap/*` → 403 (OG-002).
- `operator`: `/api/nap/*` + `/local/*`.
- `admin`: `/api/admin/*` + tất cả.
- **IDOR (OG-001):** collector chỉ đọc/sửa bản ghi có `created_by = <user hiện tại>` — kiểm quyền **sở hữu** ở server. UUID chỉ là định danh khó đoán, **KHÔNG** phải cơ chế chặn (không dựa vào sự mù mờ của UUID).

**Ma trận phân quyền:**
```
Nhóm endpoint                         collector        operator   admin
──────────────────────────────────────────────────────────────────────────
/api/auth/*     (login/me/logout)         ✓               ✓         ✓
/api/ho-so/*    (gửi/sửa của mình)     ✓ CHỈ bản ghi       —         ✓
                                        created_by=mình
/api/nap/*      (lock/da-nap/unlock)     ✗ 403             ✓         ✓   + X-Tool-Key
/local/*        (tool: nạp/ảnh/khóa)     ✗                 ✓         ✓   (buộc token)
/api/admin/*    (users, lọc/xóa PII)     ✗                 ✗         ✓
──────────────────────────────────────────────────────────────────────────
```

### 5.4 Khởi tạo tài khoản đầu tiên
Admin đầu tiên tạo bằng script seed (CLI trên VPS), không mở API self-register.

### 5.5 Xác thực tool cho `/local/*` — session cục bộ (HTG-01③, option A)

> **Phục vụ:** `HTG-01③`. Quyết định & lý do loại B/C: `TDD-decisions.md §4a`.

*Vì sao không verify JWT ở tool: JWT do VPS ký (`jwt_secret` + user ở PostgreSQL); tool localhost chỉ nối SQL Server, không xác thực JWT đó được. Nên tool đăng nhập THAY MẶT rồi phát session riêng.*

```
Đăng nhập tool:
  UI tool → POST /local/auth/login (username, password)
    → backend tool đọc vps_url từ config → POST {vps_url}/api/auth/login
       ├─ VPS 200 + vai_tro ∈ {operator, admin} → phát session_token cục bộ (in-memory) → trả UI
       ├─ VPS 200 + vai_tro = collector         → 403 (không nạp DB)
       ├─ VPS 401                                → 401 (sai tài khoản)
       ├─ vps_url rỗng (chưa cấu hình)           → 400
       └─ VPS lỗi mạng / status ngoài {200,401}  → 502
  UI giữ session_token → gửi `Authorization: Bearer <token>` cho /local/* nghiệp vụ.
```

- **Gác quyền:** mọi `/local/*` nghiệp vụ (khóa học, DVHC, ảnh, nạp, tra cứu) qua `require_session`. **Miễn** `/local/config*` (bước mồi đặt URL VPS — A1) và `/local/auth/*` (cửa đăng nhập).
- **Session store (server):** in-memory trong tiến trình tool (1 máy, 1 người, không TTL). Tool khởi động lại → mất phiên, đăng nhập lại. `logout` xóa token khỏi store.
- **Giữ token phía client qua F5 (CHANGES #36, 05/10/2026):** UI lưu `session_token` vào `localStorage` (không chỉ bộ nhớ); tải lại trang → khôi phục phiên bằng `GET /local/auth/me`. Trước đây token chỉ ở bộ nhớ → F5 là văng ra đăng nhập. *(Tool là app localhost 1 người dùng tại máy CSDT → lưu token localStorage chấp nhận được.)*
  ```
  Tải lại trang (F5):
    UI đọc token từ localStorage
      ├─ không có token              → màn đăng nhập
      └─ có token → GET /local/auth/me
           ├─ 200 (token còn hiệu lực) → khôi phục user, vào thẳng app
           └─ 401 (token hết/sai)      → xóa token → màn đăng nhập
    (chờ /me: hiện "Đang khôi phục phiên…", không chớp màn đăng nhập)
  ```
  - **Edge `localStorage` bị chặn** (chế độ riêng tư / trình duyệt chặn storage): đọc/ghi token bọc `try/catch` → fallback giữ token **trong bộ nhớ** như trước (F5 vẫn phải đăng nhập lại), **không vỡ app**.
  - *(Edge: `/me` lỗi MẠNG — không phải 401 — khi F5 cũng xóa token về đăng nhập; chấp nhận vì backend localhost chết thì cũng không thao tác được.)*
- **Còn mở:** 1 hay nhiều phiên đồng thời — hiện cho n phiên; chốt sau khi có yêu cầu (xem `TDD-decisions.md §4a`).

---

## 6. Thu thập & quét QR CCCD (app web)

> **Phục vụ:** `THU-01`, `THU-02`
*Vì sao tách khỏi tool: thu thập cần chạy mọi nơi trên điện thoại, không cần DB.*

### 6.1 Luồng
```
Đăng nhập → camera sau (facingMode environment) → khung ngắm 3:4
  → BarcodeDetector API (native) ─ fallback ─► qr-scanner (ZXing)
  → auto-capture khi QR ổn định ~2 frame (500ms) → hiệu ứng (rung+đổi màu+tick)
  → parse chuỗi CCCD → màn preview 7 trường (sửa được) → chụp ảnh thô → POST /api/ho-so
QR hỏng → nhập tay / upload ảnh CCCD đọc QR.
Màn preview 2 lối (THU-01/THU-02, CHANGES #13):
  [Tiếp tục → chụp ảnh → gửi → màn kết quả]
  HOẶC [Lưu & nhập hồ sơ tiếp → gửi KHÔNG ảnh → toast "Đã gửi ✓" → về màn chọn cách nhập] (nhập liên tiếp).
```

### 6.2 Parse chuỗi QR CCCD (chuẩn Bộ Công an 2021)
Tách `|`, **6 hoặc 7 trường**: `CCCD(12) | [CMND cũ(9)] | Họ tên | Ngày sinh(ddMMyyyy) | Giới tính(Nam/Nữ) | Địa chỉ | Ngày cấp(ddMMyyyy)`.
- Ngày sinh ddMMyyyy → lưu `yyyymmdd`; chỉ có năm → `yyyy0000`.
- Giới tính Nam→`M`, Nữ→`F`.
- Validate: CCCD 12 số, CMND cũ 9 số (nếu có). Sai → báo lỗi rõ, không tự điền.
- **Độ dài tên (EC-030):** cảnh báo sớm nếu vượt giới hạn cột DB đích — `HoVaTen ≤50`, `HoDemNLX ≤30`, `TenNLX ≤20`, `HoVaTenIn ≤25` (nvarchar). Cho sửa/cắt trước khi gửi, **giữ dấu tiếng Việt**; không để tràn cột làm SP lỗi lúc nạp.

### 6.3 Gửi & chống mất/trùng
- `uuid` sinh ở client; POST gửi kèm. Mất mạng → giữ nháp (IndexedDB/localStorage), gửi lại cùng uuid (idempotent) khi có mạng.
- Ảnh thô: JPEG, upload riêng `POST /api/ho-so/:uuid/anh`.

### 6.4 Tìm trong "Hồ sơ đã gửi" (THU-02, CHANGES #10)
Lọc **phía client** trên danh sách `/api/ho-so/cua-toi` đã tải (không thêm endpoint). Khớp theo **tên hoặc số CCCD**; tên **chuẩn hóa bỏ dấu cả hai vế** (NFD + xóa dấu kết hợp) để gõ không dấu vẫn ra. Ô tìm đặt **đầu danh sách**; màn hẹp thu gọn thành **nút kính lúp**.

### 6.5 UX app web sau test điện thoại (THU-01/THU-02, CHANGES #12)
*Vì sao: test thật trên điện thoại lộ ra camera tự mở gây giật, nút tụt khỏi tầm nhìn, không xem lại được hồ sơ đã gửi.*
- **Màn vào không tự mở camera** (THU-01): **mobile** landing cho chọn Quét QR / Nhập tay / Tải ảnh; `getUserMedia` chỉ gọi khi bấm Quét (đỡ xin quyền đột ngột + hao pin). **Desktop (≥lg) vào thẳng form nhập tay** (THU-01, CHANGES #30): bỏ cổng chọn (`giaiDoan` khởi tạo thẳng `preview`/form trống trên desktop); nút **Quét QR / Tải ảnh** thu nhỏ ra góc phải tiêu đề form; bấm Quét QR mở **popover camera nổi** đè form (tái dùng logic `KhungQuet`/decode cascade, không full-screen), bắt được QR → `batDau(fields)` điền vào form đang mở rồi đóng popover. "Lưu & nhập hồ sơ tiếp" trên desktop quay về **form trống** (không về cổng chọn). Mobile giữ nguyên luồng `chon → quet/preview`. *Vì sao: desktop gõ bàn phím là chính, quét webcam phụ — đưa form lên trước, quét thành thao tác điền-nhanh, không bắt qua cổng chọn.* Thuần client `Quet.tsx` (nhánh `lg:`), KHÔNG đổi endpoint/schema.
- **Khung bám QR** (THU-01): BarcodeDetector trả `cornerPoints` (4 góc QR trong khung hình) → vẽ khung khóa theo mã khi bắt trúng. Fallback qr-scanner không có tọa độ → giữ khung ngắm tĩnh.
- **Layout mobile 1 màn** (THU-01, AppLayout): dùng `height:100%`/`100dvh` thay `100vh` (thanh URL mobile), khung camera `flex` co giãn, **bottom-nav + nút hành động chính dính đáy** (`position:sticky`/flex shrink-0), không cuộn mới thấy. Logo header là trang trí — bỏ nền/bo dáng nút.
- **Xem lại + ảnh thật + sửa/chụp lại** (THU-02): danh sách & chi tiết "đã gửi" hiện ảnh thật qua `GET /api/ho-so/:uuid/anh` (của mình, kiểm `created_by` — chống IDOR như `_cua_minh`); modal chi tiết khi `pending` cho **Sửa** (`PUT /api/ho-so/:uuid`) + **Chụp/đổi ảnh** (`POST .../anh`); `importing`/`imported` → chỉ xem (server trả 409 nếu cố sửa).

### 6.6 Nhập liên tiếp + badge/lọc thiếu ảnh + cảnh báo trùng (THU-01/THU-02/THU-04, CHANGES #13)
*Vì sao: nhân viên nhập hàng loạt muốn gửi nhanh không bắt chụp ảnh từng hồ sơ, rồi gom các hồ sơ thiếu ảnh để chụp bù; và tránh gửi trùng một người lên hàng đợi.*
- **Lưu & nhập hồ sơ tiếp** (THU-01/THU-02): nút thứ hai ở màn preview → gửi `POST /api/ho-so` **không kèm ảnh** (cơ chế gửi-không-ảnh + giữ nháp offline đã có) → **toast** thay màn kết quả → `setGiaiDoan("chon")` về màn chọn cách nhập. Không thêm endpoint. Thuần client `Quet.tsx`.
- **Badge "Thiếu ảnh" + bộ lọc** (THU-02): lọc **phía client** trên `co_anh` của `/api/ho-so/cua-toi` (đã có field). Badge ở list card/table + chi tiết; thêm một lựa chọn lọc "Thiếu ảnh" cạnh tab trạng thái. Chụp bù vẫn qua nút "Thêm ảnh" khi `pending` (đã có). Không thêm endpoint. Thuần client `DaGui.tsx`.
- **Cảnh báo trùng CCCD** (THU-04): thêm `GET /api/ho-so/kiem-trung?cccd=` (collector) → đếm hồ sơ `pending`/`importing` cùng CSDT có `so_cccd` khớp (loại trừ chính `uuid` đang gửi). >0 → trả thông tin (ai gửi, lúc nào) để app hiện **banner cảnh báo mềm** (chuẩn ⑥), **vẫn cho gửi**. Mất mạng/khi gọi lỗi → bỏ qua, không chặn. KHÔNG đối chiếu SQL Server (app web không nối DB) — chốt trùng thật ở NAP-06. Server validate `cccd` (12 số) từ chối sớm; client hủy request cũ bằng `AbortController`.
- **UX nhập liệu** (THU-01/THU-02, CHANGES #14): **ẩn ô CMND cũ** khỏi form (giá trị từ QR vẫn giữ trong nháp + gửi như cũ — không đổi payload/schema); ô ngày là **component gõ tay dd/mm/yyyy + nút lịch** (native date popover ghi ngược vào ô text; vẫn nhập năm-only → `yyyy0000`); **desktop** tách vị trí 2 nút + phím tắt (autofocus, Enter→nút chính). Thuần client.
- **Xóa hồ sơ đã gửi** (THU-05, CHANGES #24): ở `/app/da-gui`, hồ sơ **`pending`** có nút **Xóa** (xác nhận 2 bước) → `DELETE /api/ho-so/:uuid` (soft-delete). Hồ sơ `importing`/`imported` **ẩn/khóa nút** (server cũng chặn 409). Phân quyền: collector chỉ xóa `created_by` = mình (chống IDOR như `_cua_minh`); admin bất kỳ. Sau xóa, bỏ dòng khỏi danh sách (client `DaGui.tsx`). Đồng bộ sang tool ở bước kéo (NAP-01, §11.7).
- **Desktop chọn-nhiều-để-xóa** (THU-05, CHANGES #30): bảng desktop thêm **cột ô tích chỉ render ở dòng `pending`** (dòng `importing`/`imported` không có ô tích — khớp luật server chặn xóa); ô tích đầu cột = chọn tất cả `pending` **trên trang hiện tại**. Thanh thao tác nổi "Đã chọn N · Bỏ chọn · Xóa N" hiện khi `chon.size > 0` → dialog xác nhận → **lặp `DELETE /api/ho-so/:uuid` phía client** (for-of, đếm lỗi như `xoaDaChon` của `QuanTriHoSo.tsx`), KHÔNG thêm endpoint batch. Mobile giữ card+modal (xóa lẻ), không thêm chế độ chọn. *Vì sao lặp client: endpoint xóa lẻ đã có quyền + CAS + audit đầy đủ; thêm batch endpoint là nhân đôi logic phân quyền/soft-delete.* Thuần client `DaGui.tsx`.

---

## 7. Hàng đợi thu thập & vòng đời bản ghi (VPS)

> **Phục vụ:** `HTG-02`, `NAP-01`
*Vì sao có khóa `importing`: nhiều tool/thao tác có thể chạm cùng bản ghi, phải chặn tạo học viên trùng.*

### 7.1 State machine `trang_thai`
```
 draft (client, localStorage)
    │ gửi — POST /api/ho-so (idempotent theo uuid)
    ▼
 pending ──lock (CAS: pending→importing)──▶ importing ──da_nap(+MaDK)──▶ imported
    ▲   ▲                                      │                            │
    │   │  unlock: nạp lỗi/mất DB ─────────────┘                            │
    │   │  job mở khóa nếu importing > 15' (EC-002) ─────▶ pending           │
    │   └─ tra-ve-cho-nap: tool gỡ HV khỏi CSDT (QLY-08) imported→pending ───┘
    │      (gỡ ma_dk; bản ghi 'deleted' → 409, không trả về được)
    │                                                                        
    └─ pending/imported > 30 ngày ──┐   importing: job PII BỎ QUA (EC-040)   
                                     ▼         admin xóa tay / collector xóa (THU-05, chỉ pending của mình)
                                  deleted  ◀───────────────────────────────── 
```
> NAP-06 trùng CCCD trong khóa → **GIỮ `pending`** + cảnh báo (operator tự xử: bỏ qua / đổi khóa / xóa). KHÔNG có trạng thái `duplicate`.
> **QLY-08 (CHANGES #24):** `imported→pending` chỉ dùng khi operator GỠ HV đã nạp nhầm khỏi CSDT — khác `unlock` (chỉ `importing→pending` khi nạp lỗi). **THU-05 (CHANGES #24):** collector xóa hồ sơ `pending` của mình → `deleted` (soft-delete, giữ vết audit_log); `importing`/`imported` collector KHÔNG xóa được (409). Kéo về (NAP-01) bỏ qua `deleted` + **đồng bộ bỏ** dòng staging `pending` đã thành `deleted` trên VPS.

### 7.2 Khóa & chống trùng (EC-003, EC-010, EC-011)
- Kéo: chỉ trả `pending` chưa bị khóa (`locked_by IS NULL`).
- **Kéo KHÔNG khóa** (lock chỉ ở bước nạp) → bản ghi còn sửa được ở app web (`PUT /api/ho-so/:uuid`, `POST .../anh`) tới khi operator nạp. Hệ quả: tool kéo xong, collector sửa tiếp → bản trong staging tool thành cũ. Xử lý (NAP-01, CHANGES #11): tool **kéo lại làm tươi** các bản `keo_ve` còn trạng thái cục bộ `cho` (ghi đè thông tin/ảnh mới nhất từ VPS), **giữ nguyên** bản `xong`/`loi`. Không khóa-khi-kéo (tránh kẹt hàng loạt + job 15' lật ngược khi kéo mà chưa nạp).
- Trước nạp: `POST /nap/:uuid/lock` set `importing` + `locked_by` (compare-and-set nguyên tử trong 1 UPDATE có WHERE `trang_thai='pending'`). Tool khác thua → báo "đang được nạp". Lock **trả về bản ghi tươi** (thông tin + ảnh mới nhất) → tool nạp đúng bản collector vừa sửa, không nạp bản staging cũ (§7.5).
- Nạp xong: `da_nap` + lưu `ma_dk`; `imported` không kéo lại → không tạo HV thứ 2.
- Lỗi: `unlock` → `pending`; timeout khóa **15 phút** (env `IMPORT_LOCK_TIMEOUT_MIN=15`) → job tự mở khóa (EC-002).
- **"Bỏ khỏi hàng đợi" (NAP-01, CHANGES #22):** xóa dòng trạng thái cục bộ `xong` khỏi `staging.sqlite` bảng `keo_ve` (endpoint tool-local `DELETE /local/keo-ve/:uuid`) — chỉ dọn hàng đợi tool, **KHÔNG đụng VPS/DB đích** (HV đã nạp, VPS đã `da_nap` nên kéo lại không mang về). Khác hẳn "Xóa khỏi DB" (QLY-03 `usp_NguoiLX_Delete`) — đặt tên/nút tách bạch để tránh xóa nhầm prod.

### 7.3 Xóa PII (BR-016)
APScheduler quét mỗi giờ: `pending`/`imported` quá 30 ngày → xóa dòng + file ảnh thô; **bỏ qua** `importing` (EC-040). Ghi `audit_log(hanh_dong='xoa_pii')`.

### 7.4 Validate ảnh thô khi nhận (bảo mật)
`POST /api/ho-so/:uuid/anh` phải kiểm trước khi lưu: kích thước **≤ 8 MB**; **magic-byte** đúng JPEG/PNG (không tin đuôi/Content-Type); giới hạn số điểm ảnh (`Image.MAX_IMAGE_PIXELS`) để chặn ảnh "bung nén" (decompression bomb) làm treo/sập tool khi `rembg`/`Pillow` xử lý. Không hợp lệ → 4xx, báo lỗi rõ (PRD ⑦).

### 7.5 Quyền sở hữu bản ghi: mốc "Nạp" là điểm bàn giao (CHANGES #26)

Một hồ sơ sống ở **2 nơi**: VPS (app web — nơi collector tạo) và CSDT (qua tool — DB thật). Để không mâu thuẫn khi sửa/xóa từ 2 phía, quyền làm chủ **chuyển theo mốc nạp**:

- **Trước nạp** (`pending`): **app web làm chủ.** Collector thêm/sửa/xóa (THU-05); tool chỉ kéo-mirror (NAP-01), chưa đụng DB.
- **Sau nạp** (`imported`): **tool/CSDT làm chủ.** Operator sửa nhân thân/ảnh/đổi khóa/xóa (QLY-01/02/03/05/08); bản ghi app web **đóng băng** — chỉ xem, không sửa/xóa (`PUT`/`DELETE /api/ho-so/:uuid` chỉ khi `pending`). Bản VPS thành lịch sử, KHÔNG đẩy ngược từ CSDT.

**Edge (khóa chưa BC1):**

| Chặng | Tình huống | Xử lý |
|---|---|---|
| Cửa sổ bàn giao | Collector sửa lúc tool vừa kéo bản cũ | Tool đọc bản mới nhất ở bước `lock` (lock trả record tươi) — không nạp bản staging cũ |
| Cửa sổ bàn giao | Collector xóa đúng lúc operator bấm nạp | Ai tới trước: tool `lock` trước → app web `DELETE` 409; app web xóa trước → `lock` CAS 0 dòng → tool báo "hồ sơ đã bị người gửi xóa" |
| Sau nạp | Collector muốn sửa/xóa trên app web | Không cho (đóng băng). Sửa làm ở tool (QLY-01/05) |
| Sau nạp | Nạp nhầm khóa | Cùng hạng → QLY-02 (đổi khóa, trong DB); khác hạng / muốn sửa lại từ app → QLY-08 (gỡ về chờ nạp) |
| Thêm | Collector tạo HV đã có trong DB (đã nạp) | App web không soi được DB → chốt trùng ở tool lúc nạp (NAP-06) |

**Hai hành vi xóa HV đã nạp — hậu quả khác nhau (chống bấm nhầm):**
- **QLY-03 "Xóa hẳn":** xóa khỏi CSDT, VPS vẫn `imported` (lịch sử). Nạp lại = nhập lại hồ sơ MỚI ở app web (quyết định Q1).
- **QLY-08 "Gỡ về chờ nạp":** xóa khỏi CSDT **+** VPS `imported→pending`. Về hàng chờ, nạp lại không nhập lại; ảnh dùng ảnh thô VPS (Q2); về `pending` thì collector lại sửa/xóa được (Q3).

---

## 8. Map địa chỉ hành chính (DVHC)

> **Phục vụ:** `NAP-03`
*Vì sao nối theo tên chứ không theo mã: mã của dataset ngoài khác mã DB; (tỉnh mới, xã mới) là duy nhất 100% trong DB nên nối tên an toàn.*

### 8.1 Luồng
```
[Kéo-về] noi_tt_raw ("…, Xã X, Huyện Y, Tỉnh Z") → TỰ TÁCH theo dấu phẩy + từ khóa
   (Tỉnh/Thành phố→tỉnh · Quận/Huyện/Thị xã→huyện · Phường/Xã/Thị trấn→xã · phần dư→Chi tiết)
   → ĐIỀN SẴN 3 ô Tỉnh/Huyện/Xã cũ (operator sửa được) → operator bấm "Chuyển đổi"
   (tách rỗng/không rõ → để trống, gõ tay — không chặn)
Địa chỉ text (cũ/mới) → chuẩn hóa (NFC, lower, bỏ tiền tố Tỉnh/Thành phố/Quận/Huyện/Thị xã/Phường/Xã/Thị trấn, chuẩn dấu nháy)
  → tra DM_DVHC_MAP theo (TenTinhCu,TenHuyenCu,TenXaCu)
     ├─ khớp & không chia → lấy MaDvhcMoi + MaDVQLMoi
     ├─ IsDividedWard=1 hoặc không khớp → popup chọn tay (Tỉnh→Xã từ DM_DVHC TrangThai=1)
  → điền NoiTT_MaDVHC + NoiTT_MaDVQL (+ NoiCT_* = NoiTT_* mặc định, BR-004)
```
*Tách là best-effort phía client (không gọi DB), chỉ để đỡ gõ — luôn cho sửa trước khi map, không tự map cứng (địa chỉ QR hay viết tắt/thiếu dấu). Phục vụ NAP-03 luồng kéo-về (CHANGES #19).*

### 8.2 Nguồn & đối soát
- Bảng `dm_dvhc_map` (SQLite cục bộ) do tool **tự dựng**: đọc `DM_DVHC (TrangThai=1)` của máy đích (chỉ đọc) + dataset `vietnamadminunits` (`convert_legacy_2025_simple.csv`) **đóng kèm tool**, nối theo TÊN (tỉnh mới + xã mới ngắn) để lấy đúng mã của **chính máy đích** (đã verify phủ 3321/3321 xã trên DB mẫu DESKTOP-UBV2GQI).
- Thao tác **"Đồng bộ danh mục"** (lần chạy đầu, hoặc khi `DM_DVHC` đổi) dựng lại bảng SQLite. **Không ghi gì vào `GPLX_CSDT`.**
- Điều kiện phía DB đích: `DM_DVHC` đã có đơn vị mới 2025 (`TrangThai=1`) — việc của quản trị DB, ngoài phạm vi tool.

---

## 9. Xử lý ảnh chân dung & xuất .jp2 (tool)

> **Phục vụ:** `NAP-04`
*Vì sao xuất .jp2 ở tool: chỉ Python/Pillow tạo được JPEG 2000; khung 3:4 + nền trắng khớp chuẩn app cũ.*

### 9.1 Luồng
```
Ảnh thô (từ VPS, đã kéo về) → NẠP SẴN vào trình chỉnh (AnhModal) làm ảnh crop ban đầu
  → hiển thị + khung crop CỐ ĐỊNH 3:4 + KHUNG CHÂN DUNG MẪU mờ chồng lên (ô-van đầu + đường căn mắt/cằm)
  → auto gợi ý theo nhận diện mặt → grab di chuyển (4 hướng) + ZOOM (thang mũ 3^t, t∈[−1,1], giữa=cỡ gốc, cho thu nhỏ <1× + lăn chuột) + XOAY (−90°/+90° + tinh chỉnh độ nghiêng) / thay ảnh
  → rembg xóa phông → nền TRẮNG → preview
  → (khi bấm Nạp) Pillow xuất .jp2 (ảnh đã xoay rồi mới crop; khung mẫu KHÔNG dính vào ảnh xuất)
```
*Ảnh thô kéo về nạp thẳng vào trình chỉnh (AnhModal nhận ảnh khởi tạo tùy chọn) — luồng kéo-về NAP-04 (CHANGES #19). Prop ảnh khởi tạo là TÙY CHỌN để QLY-05/QLY-06 mở không-ảnh-sẵn vẫn chạy như cũ.*
*Xoay + khung chân dung mẫu (CHANGES #20): xoay client-side (canvas) trước khi gửi backend crop, box tính trong hệ ảnh đã xoay; khung mẫu chỉ là overlay CSS/SVG để căn, không đưa vào ảnh `.jp2`.*
*Giữ bản preview PNG để xem lại/chỉnh tiếp (CHANGES #23): `/local/anh/xu-ly` đã trả cả `preview` (PNG data-URL, trình duyệt render được) lẫn `jp2_b64` (để ghi file). Khi "Dùng ảnh này", client lưu **cả `preview`** cạnh `jp2` trong nháp (`nhap[uuid]` ở NapHoSo; state ảnh ở TraCuuDB) để: (1) khung ảnh hiển thị ảnh đã chỉnh — KHÔNG dùng `jp2` vì `.jp2` không render trực tiếp trên trình duyệt; (2) mở lại trình chỉnh thì `anhBanDau` ưu tiên preview đã chỉnh gần nhất (có) thay vì ảnh thô. Nút áp dụng ("Dùng ảnh này") để **nổi bật** (nút đặc màu chính), badge kết quả ghi rõ cần bấm để áp dụng — chống dừng ở bước "Xử lý ảnh". Không đổi endpoint; thuần client.*
*"Dùng lại ảnh gốc" (CHANGES #26): AnhModal thêm prop ảnh gốc `anhGoc` (ảnh nguyên bản, TÁCH khỏi `anhBanDau` = seed/ảnh-đã-chỉnh-gần-nhất). Có `anhGoc` → hiện nút **"Dùng lại ảnh gốc"** (xác nhận nhanh) → nạp lại `anhGoc` vào canvas, bỏ mọi chỉnh sửa + reset grab/zoom/xoay. Vì sao cần `anhGoc` riêng: CHANGES #23 đã cho `anhBanDau` ưu tiên preview-đã-chỉnh → không còn đường về ảnh nguyên bản; nút này đi xa hơn preview. Nguồn `anhGoc` tùy màn: **NAP-04** = ảnh thô VPS nguyên bản (còn trong phiên kéo-về); **QLY-05** = ảnh `.jp2` đang lưu transcode PNG (bản trước khi chỉnh phiên này). Không có nguồn → không truyền `anhGoc` → ẩn nút. Thuần client.*

### 9.2 Chuẩn xuất (đo 300 ảnh thật)
- Tỷ lệ **3:4**, RGB, **nền trắng**; kích thước **mặc định 353×471 (~48 KB, khớp cụm phổ biến nhất của app cũ)**. (480×640 chỉ dùng khi có yêu cầu nét hơn — không phải mặc định, không cần nút chọn ở MVP.)
- **Công thức đường dẫn (verify 100% dữ liệu thật):**
  `DuongDanAnh = <IMG_PATH_CSDT> \ <MaKhoaHoc> \ <MaDK>.jp2`
  - `IMG_PATH_CSDT`: **đọc từ DB** `QTHT_ThamSoHT` (TenTS='IMG_PATH_CSDT') mỗi lần — **KHÔNG hard-code** (có thể đổi) (BR-019).
  - Folder = **`MaKhoaHoc`** (thư mục ảnh của khóa; 98,6% khớp trên dữ liệu).
  - Tên file = **`<MaDK>.jp2`** (100% khớp 39.648 HV) → tool **dùng lại `MaDK` do SP trả về**, KHÔNG sinh timestamp mới.
- **Tạo folder nếu chưa có** (`makedirs(exist_ok=True)`) trước khi ghi — khóa mới chưa có ảnh thì folder chưa tồn tại; tool tự tạo (giống app cũ tạo khi lưu ảnh đầu tiên).
- Ghi DB: `DuongDanAnh` = đường dẫn đầy đủ vừa ghi (cột này là **nguồn sự thật** của đường dẫn ảnh), `ChatLuongAnh=1`, `NgayThuNhanAnh`=now, `NguoiThuNhanAnh`=operator.
- **Đọc/hiển thị ảnh** (tra cứu, đổi khóa): luôn lấy đường dẫn từ `NguoiLX_HoSo.DuongDanAnh`, KHÔNG dò theo tên folder/tên file.
- **Hiệu năng rembg:** nạp `rembg` session (model u2net ~170 MB) **một lần lúc khởi động tool** (warm-up), giữ trong bộ nhớ. Mốc <5s/ảnh (§13) tính từ ảnh **thứ 2**; ảnh đầu (cold-start) đo riêng, chấp nhận cao hơn. **Script chạy tool (`tool-start.bat`) KHÔNG đặt `TOOL_SKIP_WARMUP=1`** — cờ đó chỉ dành cho test (conftest) để khỏi tải model; đặt nó lúc chạy thật khiến ảnh đầu mỗi phiên đều cold-start chậm (CHANGES #20, phương án A). Giữ model `u2net` (chất lượng), không đổi sang model nhẹ.

### 9.3 Lưu tạm & dọn (staging tool)
- Ảnh kéo về (thô) + ảnh đang chỉnh lưu trong **staging cục bộ máy DB** (`%LOCALAPPDATA%\pmcsdtlx-tool\staging\anh\<uuid>.*`), cạnh `staging.sqlite`. Đây là bản tạm.
- **Nạp thành công:** bản `.jp2` chính thức đã ở `ANHCDUNG\<MaKhoaHoc>\` (GIỮ) → **xóa ngay ảnh thô + ảnh làm việc trong staging** (dọn PII trên máy DB + tiết kiệm ổ).
- **Nạp lỗi:** giữ staging để thử lại.
- Trên VPS: bản thô giữ tới 30 ngày rồi job tự xóa (BR-016) — để đối chiếu/nạp lại.

### 9.3a Lưu nháp chuẩn bị BỀN (CHANGES #32)

Trước #32, mọi chỉnh sửa khi chuẩn bị nạp (`nhap[uuid]`: `diaChi`, `chiTiet`, `noiCap`, `tick`, `jp2`, `anhPreview`) **chỉ sống trong RAM** của màn NapHoSo → tải lại trang/đóng tool là mất. Nay **lưu bền xuống staging** để sống qua phiên và để 2 chip trạng thái (§10.5) đúng kể cả sau khi mở lại.

- **Kho:** bảng RIÊNG trong `staging.sqlite` — **`nhap_chuan_bi(uuid PRIMARY KEY, dia_chi_json, chi_tiet, noi_cap, tick_json, jp2_b64, anh_preview, updated_at)`**. *Vì sao bảng riêng chứ không thêm cột vào `keo_ve`: tách bạch DỮ LIỆU GỐC VPS (`keo_ve`, do `keo_ve_upsert` làm tươi) khỏi NHÁP OPERATOR — upsert làm tươi dòng `cho` không vô tình đè/được đè bởi nháp; xóa nháp độc lập.*
- **Ảnh trong nháp:** `jp2_b64` (ảnh đã đổi nền, để nạp) + `anh_preview` (PNG để hiển thị) lưu **trong SQLite** cạnh nháp — là **PII ảnh căn cước nằm lại máy tool**, đi ngược nguyên tắc §9.3/§7.4 cũ; chấp nhận có điều kiện (máy nội bộ CSDT + tự xóa — xem TDD-decisions §11). Dọn như §9.3: nạp xong thì xóa.
- **API (tool-local):**
  - `GET /local/nap/nhap?uuids=<csv>` — **danh sách cờ NHẸ** cho cả lưới: mỗi dòng chỉ `{uuid, co_dia_chi, co_anh, co_tick}` (boolean), KHÔNG kèm `jp2_b64`/`anh_preview`. Dùng vẽ 2 chip §10.5 cho mọi dòng mà không tải ảnh. *Vì sao tách (review #32, Điểm 5): nếu dùng GET-theo-uuid full để lấy cờ thì phải tải toàn bộ base64 ảnh cả khóa chỉ để hiện 1 chip boolean → giật + tốn RAM tab.*
  - `GET /local/nap/nhap/{uuid}` — đọc **đầy đủ** 1 nháp (kèm `jp2_b64`+`anh_preview`), **chỉ gọi khi MỞ drawer Chuẩn bị** (nạp vào `nhap[uuid]`), không gọi hàng loạt.
  - `PUT /local/nap/nhap/{uuid}` — lưu nháp (gọi khi **đóng drawer Chuẩn bị** hoặc debounce khi đổi — không spam mỗi phím).
- **Vòng đời — tự xóa nháp** (đi kèm mọi điểm dòng `keo_ve` kết thúc): nạp xong (`keo_ve_cap_nhat(... 'xong')`), "Bỏ khỏi hàng đợi" (`keo_ve_xoa`), đồng bộ xóa VPS (`keo_ve_xoa_neu_cho`) → **xóa dòng `nhap_chuan_bi` cùng `uuid`**. Gom thành 1 helper `nhap_xoa(uuid)` gọi chung ở các chỗ này. Thêm **nút "Xóa nháp"** trên drawer Chuẩn bị gọi cùng `nhap_xoa(uuid)` để operator **chủ động dọn** một nháp.
- **Giới hạn PII nháp bỏ dở (review #32, Điểm 4):** nháp của một dòng `cho` mà operator **không nạp** và collector **không xóa trên app web** thì không rơi vào 3 lối tự-xóa trên → **tồn tại (gồm ảnh căn cước) tới khi operator bấm "Xóa nháp"**. Chấp nhận giới hạn này (máy nội bộ CSDT) — xem TDD-decisions §11.
- **Cạm bẫy `keo_ve_upsert` + BUG-04 (bắt buộc):** `keo_ve_upsert` khi làm tươi dòng `cho` hiện GHI ĐÈ `noi_tt_raw` bằng bản mới từ VPS. Khi **`noi_tt_raw` ĐỔI** so với bản đang có → **reset phần ĐỊA CHỈ của nháp bền** (`dia_chi_json=NULL`, `chi_tiet` tính lại từ raw mới) + chip địa chỉ về `✗` + toast "địa chỉ của N hồ sơ đã đổi, cần map lại"; **GIỮ** `jp2_b64`/`anh_preview`/`tick_json`/`noi_cap`. `noi_tt_raw` **không đổi** → giữ nguyên nháp. *Đặt so-sánh + reset ở BACKEND (trong/cạnh `keo_ve_upsert`, so raw cũ↔mới trước khi đè) để nguồn sự thật nhất quán, thay vì chỉ ở client `lamTuoiNhapDiaChi` như hiện tại.*
- **Luật ghép địa chỉ hiển thị (review #32 — xác minh DB thật 04/10):** DB lưu **tách** `NoiTT` (chi tiết, nvarchar 50) và địa chỉ hành chính dạng **mã** (`NoiTT_MaDVHC`/`NoiTT_MaDVQL` varchar 5) — **không có SP/view nào ghép** 2 phần, và `DM_DVHC.TenDayDu` cấp xã **đã chứa sẵn phẩy giữa các cấp** (vd `Xã Phước Hòa, Thành phố Hồ Chí Minh`). → Mọi chỗ **tool** hiển thị một dòng địa chỉ phải ghép `[chi_tiet, TenDayDu(xã)].filter(Boolean).join(", ")` (lọc rỗng, ngăn cách `", "`) — đã làm đúng ở popup Chi tiết (`TraCuuDB.tsx`), áp cùng cách cho preview địa chỉ ở drawer Nạp lô. **Lưu `NoiTT` vẫn chỉ chi tiết thuần** (không nhét tên xã/dấu phẩy — giữ §10.2). *App cũ tự render địa chỉ theo cách của nó — ngoài tầm tool.*

```
Vòng đời nháp chuẩn bị (nhap_chuan_bi, keyed theo uuid dòng keo_ve):

   mở drawer / debounce sửa
        │ PUT /local/nap/nhap/{uuid}
        ▼
   ┌─────────────┐   noi_tt_raw ĐỔI (keo_ve_upsert, BUG-04)
   │  nháp bền   │──────────────────────────────┐
   │ dia_chi,    │   reset dia_chi_json=NULL,    │
   │ chi_tiet,   │   chi_tiet tính lại từ raw,   │
   │ noi_cap,    │   chip địa chỉ → ✗ + toast;   │
   │ tick,       │   GIỮ jp2/preview/tick/noi_cap│
   │ jp2_b64,    │◀──────────────────────────────┘
   │ anh_preview │
   └─────────────┘
        │ nhap_xoa(uuid) — xóa cả ảnh
        ▼
   (xóa khi)  • nạp xong            keo_ve_cap_nhat(...'xong')
              • "Bỏ khỏi hàng đợi"  keo_ve_xoa
              • đồng bộ xóa VPS     keo_ve_xoa_neu_cho
              • nút "Xóa nháp"      operator chủ động (review #32, Điểm 4)

   ⚠ Nháp bỏ dở (dòng 'cho' không nạp, VPS không xóa) TỒN TẠI tới khi
     operator bấm "Xóa nháp" (giới hạn PII đã ghi ở TDD-decisions §11).
```

### 9.4 Ca lỗi
- rembg xấu (tóc/viền) → cho giữ ảnh gốc / chỉnh tay.
- Ghi file rồi SP lỗi → dọn file `.jp2` chính thức vừa ghi, không để mồ côi (EC-022).
- Chưa có ảnh → cảnh báo mềm, vẫn cho nạp (BR-011).

---

## 10. Nạp hồ sơ vào DB qua SP (tool)

> **Phục vụ:** `NAP-05`, `NAP-02`, `NAP-06`
*Vì sao chỉ qua SP + transaction: bản ghi phải khớp app cũ 100% và không để hồ sơ nửa vời.*

### 10.1 Luồng (đổi 01/10/2026 — CHANGES #4: 3 SP rời → 1 SP gộp app cũ)
```
Chọn loại (mô tô/ô tô) → khóa chưa BC1 → nhập/chọn HV → map địa chỉ (ra mã DVHC) → xử lý ảnh
  → kiểm trùng CCCD trong khóa (BR-005) → khóa bản ghi VPS (lock: pending→importing)
  → sp_getapplock(@Resource = MaKhoaHoc, @LockMode='Exclusive')   ◀── chặn tranh SoHoSo cả 2 máy [PH-3.1]
     → SoHoSo = RIGHT('000' + (MAX(SoHoSo theo khóa)+1), 3)        (đọc MAX trong applock)
     → EXEC usp_QuangLA_PM4_ThuNhanHS_ThemMoiCapNhat  @p_MaDK=NULL OUTPUT, @p_SoHoSo=<SoHoSo>, …
         ◀── 1 SP gộp app cũ, atomic (SP tự transaction). @p_MaDK=NULL → SP TỰ SINH MaDK
         (dạng 70004-<yyyyMMddHHmmssfff>, hàm CreateNewMaDK) trả về qua OUTPUT.
         32 tham số @p_* khớp 1:1 form "Thu nhận HS": MaKH, MaHangGPLX, HangDaoTao, SoHoSo,
         HoVaTen (IN HOA — SP TỰ TÁCH Ho/Ten), HoVaTenIn, NgaySinh, GioiTinh, MaQuocTich(=VNM),
         SoCMT, NgayCap, NoiCap, MaDVHC_TT + ChiTiet_TT, MaDVHC_CT + ChiTiet_CT, SoNamLX, SoKmLX,
         GiayTo (danh sách MaGT), GPLX đã có…, GhiChu, SO_CMND_CU, CHON_IN_GPLX(=2)
         → SP ghi NguoiLX + NguoiLX_HoSo (TT_XuLy='01', CHƯA ảnh) + giấy tờ trong MỘT lần
         → @p_out: 0=OK · -1 trùng SoHoSo · -2 trùng CMT · -3 thiếu thâm niên · -4 thiếu km
           (SP KHÔNG raiserror → tool PHẢI đọc @p_out; ≠0 → SP không insert → báo lỗi, giữ pending)
     → CÓ ảnh:  ghi file .jp2 (tên = MaDK) vào <IMG_PATH_CSDT từ QTHT_ThamSoHT>\<MaKhoaHoc>\
                → UPDATE NguoiLX_HoSo SET DuongDanAnh=<đường dẫn TUYỆT ĐỐI .jp2>, ChatLuongAnh=1,
                  TT_XuLy='03', NgayThuNhanAnh=getdate(), NguoiThuNhanAnh='' WHERE MaDK   ◀── hướng A
       CHƯA ảnh: bỏ 2 bước trên → giữ TT_XuLy='01', DuongDanAnh NULL (BR-011; bổ sung ảnh sau)
  → sp_releaseapplock(@Resource = MaKhoaHoc)
  → VPS: da_nap (ma_dk)
```
> **Vì sao 1 SP gộp thay 3 SP rời:** đây là SP app cũ dùng cho CHÍNH màn "Thu nhận Hồ sơ cấp mới",
> nên bản ghi khớp 100% (gồm `CHON_IN_GPLX=2`, họ tên IN HOA, địa chỉ mã+chi tiết tách riêng) —
> điều 3 SP rời (`usp_NguoiLX_Insert`+`HoSo_Insert`+`GiayTo_Insert`) không đạt được vì **không có
> tham số `CHON_IN_GPLX`** và ghi lệch nhiều field (AS-003 01/10/2026, xem CHANGES #4). SP atomic
> trong một lần → **bỏ compensation 3 bước thủ công** (§10.3).
> **Đã đọc thân SP (01/10/2026) — chốt:** caller truyền `@p_MaDK=NULL` → SP tự sinh `MaDK`
> (`70004-<yyyyMMddHHmmssfff>`, hàm `CreateNewMaDK`) và trả qua OUTPUT; `@p_SoHoSo` **caller truyền**
> (SP không sinh). **SP KHÔNG ghi ảnh** — không có cột `DuongDanAnh`/`ChatLuongAnh`/`TT_XuLy='03'`
> trong thân; set `TT_XuLy='01'` lúc tạo (vì `KIEM_TRA_ANH='fpt@'` ≠ `'fpt@123'`). → tool ghi `.jp2`
> rồi **UPDATE 5 cột ảnh thẳng** `NguoiLX_HoSo` nâng `'03'` (hướng A, CHANGES #5); chưa ảnh giữ `'01'`.
> SP cũng **tự tách họ tên** từ `@p_HoVaTen` (tool không truyền `HoDem`/`Ten` riêng).
> `sp_getapplock`/`sp_releaseapplock` giữ theo `MaKhoaHoc` (session-scoped) để `SoHoSo` (không UNIQUE)
> không trùng khi 2 máy nạp cùng khóa (EC-011).

### 10.1b Sequence — nạp 1 HV end-to-end
```
Collector(App web)  VPS(FastAPI/PG)   Operator(Tool)   SQL Server GPLX_CSDT   Ổ D (.jp2)
     │                   │                 │                   │                  │
1  POST /api/ho-so ─────▶│ lưu pending     │                   │                  │
     │◀── 201 pending ───│                 │                   │                  │
2  POST /:uuid/anh ─────▶│ validate+lưu ảnh thô                │                  │
3    │           GET /api/nap/keo ◀────────│ kéo pending→staging SQLite           │
4    │           POST /:uuid/lock ◀────────│ CAS pending→importing                │
     │           ── ok / "đang nạp" ──────▶│                   │                  │
5    │                   │       map DVHC + rembg→preview       │                  │
6    │                   │       kiểm trùng CCCD ──────────────▶│ (theo khóa BR-005)
     │                   │                 │◀───── ok ─────────│                  │
7    │                   │       sp_getapplock(MaKhoaHoc) ─────▶│   ◀── [PH-3.1]  │
     │                   │       SoHoSo = MAX+1 (trong applock) ▶│                 │
     │                   │       EXEC …ThemMoiCapNhat (@p_MaDK=NULL OUT) ▶│ →MaDK, @p_out │
     │                   │         (NguoiLX + HoSo[TT_XuLy='01'] + giấy tờ, atomic)│             │
     │                   │       @p_out≠0 → lỗi nghiệp vụ, KHÔNG ghi ảnh, giữ pending           │
     │                   │       [có ảnh] ghi .jp2 (tên=MaDK) ──┼────────────────▶│
     │                   │       [có ảnh] UPDATE HoSo: ảnh + TT_XuLy='03' ▶│ ◀── hướng A │
     │                   │       sp_releaseapplock ────────────▶│                 │
     │                   │       ⚠ SP lỗi → tự rollback (tool SET XACT_ABORT ON); .jp2 lỗi → giữ '01' (chưa ảnh); UPDATE lỗi → retry │
8    │           POST /:uuid/da-nap(+MaDK) ◀│                   │                  │
     │           imported ─────────────────▶│ xóa staging + ảnh thô               │
```

### 10.2 Giá trị suy ra (verify DB thật)
- `MaLoaiHs` (SP tự tính): `HangDT` chứa `'-'` (nâng hạng) → **3**; `HangGPLX` chứa `'A'` → **1** (mô tô); còn lại → **2** (ô tô).
- `MaHTCap=CM_VN`, `Transfer_flag=0`, `MaCSDT=70004`, `MaSoGTVT=70` (SP tự tính từ khóa).
- `GiayCNSK`: SP set **1 chỉ khi** `@p_GiayTo` chứa `'3,'` (giấy khám sức khỏe, MaGT=3); bỏ tick giấy 3 → **0** (không phải hằng số).
- **`TT_XuLy` (SP luôn set `'01'` lúc tạo — xác nhận thân SP + `KIEM_TRA_ANH='fpt@'`; tool nâng `'03'` ở bước UPDATE ảnh, hướng A):** có ảnh → `TT_XuLy='03'` + `ChatLuongAnh=1` (+ `NgayThuNhanAnh`,`NguoiThuNhanAnh`); **chưa có ảnh → `TT_XuLy='01'`, `ChatLuongAnh=NULL`, không ghi `DuongDanAnh`** (BR-011 cho nạp thiếu ảnh). Bằng chứng: khóa `70004K26B010` 55/55 HV đều `03`+ảnh; toàn bảng `01` chỉ xuất hiện khi không ảnh (93 bản), `03` chỉ khi có ảnh (2.256 bản). Khi bổ sung ảnh sau (đổi khóa/sửa) → nâng `01`→`03`.
- **`TrangThai=1` khi tạo — KHÔNG đổi theo ảnh** (=0 chỉ khi vô hiệu hóa về sau).
- Giấy tờ: theo **trạng thái tick cuối** của user (mặc định đủ 3, bỏ tick được — BR-009/5.1); truyền danh sách `MaGT` đã tick qua `@p_GiayTo`; `TenGT` đầy đủ từ `DM_GiayTo` (SP tự lo hoặc tra khi dựng @p_GiayTo).
- **Tách họ tên (EC-030):** app web lưu `ho_ten` một chuỗi; **SP TỰ TÁCH** khi nạp (tool chỉ truyền `@p_HoVaTen` đầy đủ + `@p_HoVaTenIn`; tool tách chỉ để KIỂM ĐỘ DÀI từng cột, KHÔNG truyền `HoDem`/`Ten` riêng — SP không có tham số đó). SP tách: `TenNLX` = **từ cuối**, `HoDemNLX` = **phần còn lại**, `HoVaTen` = tên đầy đủ. **TẤT CẢ IN HOA GIỮ DẤU** ("NGUYỄN VĂN AN") — verify AS-003: 55/55 HV khóa B-K149 `HoVaTen` in hoa. **`HoVaTenIn` = `HoVaTen` cắt ≤25, cũng IN HOA giữ dấu** (39.752/39.778 = 99,93% `HoVaTenIn` ≡ `HoVaTen`) — **KHÔNG bỏ dấu**. Trước nạp kiểm độ dài từng cột (≤50/30/20/25); vượt → cảnh báo cho cắt tay.
- **Field map khớp app cũ (verify AS-003 01/10/2026, khóa B-K149):**
  - `MaQuocTich = 'VNM'` (chuẩn ISO alpha-3 = `DM_QuocTich.Ma`; **"VN" vỡ `FK_NguoiLX_DM_QuocTich`**).
  - `NoiTT`/`NoiCT` = **chi tiết địa chỉ (số nhà/thôn), mặc định TRỐNG** — 55/55 HV thật để trống; địa chỉ hành chính nằm ở `NoiTT_MaDVHC`/`NoiTT_MaDVQL` (2 cấp: xã + tỉnh). **KHÔNG nhét tên xã vào `NoiTT`** (gây app hiển thị lặp Địa chỉ + Chi tiết). Tương ứng `@p_MaDVHC_TT`+`@p_ChiTiet_TT` (và `_CT`).
  - `DonViHocLX = NULL` (55/55 thật NULL; không hard-code `70004`).
  - `CHON_IN_GPLX = 2` (55/55 thật = 2; "Chọn in GPLX" bắt buộc; chỉ SP gộp set được — cột default 0).

### 10.3 Ca lỗi / concurrency (đổi 01/10/2026 — SP gộp atomic)
- **SP gộp tự transaction → KHÔNG cần compensation 3 bước:** `usp_QuangLA_PM4_ThuNhanHS_ThemMoiCapNhat` ghi NguoiLX + NguoiLX_HoSo + giấy tờ trong một SP; SP lỗi thì SP tự rollback → không để lại bản ghi nửa vời. (Khác hẳn 3 SP rời cũ, mỗi SP tự commit nên phải bù trừ tay — đã bỏ.) **⚠ SP dùng `IF @@error<>0 ROLLBACK` (không TRY/CATCH) → tool `SET XACT_ABORT ON` trước EXEC để lỗi runtime (vd vỡ FK) chắc chắn rollback, không treo transaction.**
- **Lỗi nghiệp vụ qua `@p_out` (SP KHÔNG raiserror):** `-1` trùng SoHoSo · `-2` trùng CMT · `-3` thiếu thâm niên · `-4` thiếu km. Tool PHẢI đọc `@p_out`; `≠0` → SP không insert → báo lỗi nghiệp vụ, giữ `pending`. **Đừng chỉ bắt exception** — SP lỗi nghiệp vụ không ném lỗi, chỉ `SELECT @p_out`.
- **⚠ `@p_out=-2` (trùng CMT) KHÔNG bắn khi nạp MỚI** (phát hiện qua test live 01/10): câu kiểm trong SP là `WHERE lx.MaDK <> @p_MaDK AND lx.SoCMT=... AND MaKhoaHoc=...`; nạp mới truyền `@p_MaDK=NULL` → `lx.MaDK <> NULL` = UNKNOWN → đếm 0 → không bao giờ `-2`. `-2` chỉ dùng được khi SỬA (có `@p_MaDK`). → **NAP-06 phải kiểm trùng CMT server-side trong `nap_mot_hv`** (`COUNT` `NguoiLX`×`NguoiLX_HoSo` theo `SoCMT`+`MaKhoaHoc`) **bên trong applock theo khóa** (chống đua 2 máy), TRƯỚC khi EXEC SP. UI `GET /local/kiem-trung-cccd` chỉ là cảnh báo sớm, không thay được chốt server-side.
- **Ghi ảnh là bước RIÊNG sau SP (SP không đụng ảnh — đã đọc thân SP):** thứ tự = gọi SP (nhận `MaDK`) → ghi `.jp2` theo `MaDK` → UPDATE 5 cột ảnh (hướng A).
  - `.jp2` ghi lỗi → KHÔNG UPDATE → HV giữ `TT_XuLy='01'`, `DuongDanAnh` NULL = **"có hồ sơ, chưa ảnh"** (hợp lệ BR-011; bổ sung ảnh sau bằng tool hoặc app cũ) — không phải rác, KHÔNG cần xóa HV.
  - UPDATE cột ảnh lỗi (ảnh đã ghi, DB chưa trỏ) → **retry UPDATE** theo `MaDK`; không cần xóa HV.
  - Nạp "chưa ảnh" chủ động (user bỏ trống ảnh) → bỏ cả 2 bước ảnh, giữ `'01'`.
- **Chống tạo trùng khi bấm lại (mạng timeout):** server lưu `uuid → MaDK` đã nạp xong vào `staging.sqlite` (bảng `nap_xong`); request lại cùng `uuid` → trả kết quả cũ, không gọi SP lần 2 (idempotent, verify AS-003). Giữ cờ `madk_dang_nap` theo uuid để dọn mồ côi nếu tool chết giữa khe.
- Mất kết nối DB giữa chừng → SP rollback, giữ `pending`, cho thử lại (EC-061).
- Nạp lô, 1 HV lỗi → các HV khác vẫn nạp, HV lỗi giữ pending + báo dòng (EC-071); nạp tuần tự trong lô, hiện tiến độ.
- Tranh SoHoSo khi nạp đồng thời → **`sp_getapplock(MaKhoaHoc)`** bọc {đọc MAX+1 → gọi SP gộp} (§10.1) — bảo đảm SoHoSo không trùng cả khi 2 máy nạp cùng khóa (EC-011); khóa `importing` (CAS) chặn 2 tool nạp cùng một bản ghi (EC-010).

### 10.4 Ca biên khác (đã có ở PRD/BR — nêu lại để không sót khi code)
- **Dropdown khóa rỗng** (không khóa nào chưa BC1) → hiện thông báo "không có khóa nhận HV", chặn nạp cho tới khi tạo/mở khóa.
- **Cảnh báo tuổi < tối thiểu** (`DM_HangDT.TuoiHV`) → cảnh báo mềm, vẫn cho nạp (BR-011, EC-041).
- **VPS/tunnel down khi kéo** → tool vẫn xử lý bản ghi đã kéo trong `staging.sqlite`; báo lỗi, cho thử lại (EC-062).
- **Token hết hạn giữa lúc nhập** → yêu cầu đăng nhập lại; nháp local (localStorage/staging) không mất.
- **Hiển thị khi kéo VPS về (NAP-01, CHANGES #6):** tên HV hiển thị **IN HOA giữ dấu** ngay trên form (khớp cách ghi DB). **Check chính tả mức A** (lớp UI, cảnh báo mềm — không chặn): cờ khi tên **thiếu dấu** (vd không có ký tự có dấu tiếng Việt), có **số/ký tự lạ** (ngoài chữ cái + khoảng trắng), hoặc **khoảng trắng thừa**. Không dùng từ điển tên (tránh báo nhầm tên hiếm/dân tộc). Nạp lô: trạng thái từng dòng ⚪/🔴(+lý do)/🟢 từ `nap_lo` (đã có, trả `{uuid, ok, loi}`).
- **"Nạp lại nhanh" dòng lỗi (NAP-01, CHANGES #22):** nút trên dòng `loi` gọi lại `nap_lo` cho **một** `uuid` (dòng đã unlock về `pending` sau lần lỗi trước) — không cơ chế mới, chỉ là lối tắt khỏi phải tick lại.

### 10.5 Redesign UX màn Nạp lô (NAP-01) — CHANGES #26

Thuần client (webui), KHÔNG đổi endpoint nạp (`nap_lo` giữ nguyên). Mục tiêu: chọn nhiều HV nạp vào khóa chưa BC1 gọn hơn, tiến độ + báo cáo rõ.

- **Trạng thái sẵn sàng mỗi dòng (client):** tính tại chỗ từ nháp **bền** của dòng (nguồn: bản lưu bền staging, nạp vào `nhap[uuid]` — §9.3a) — đủ khi `diaChi != null` (NAP-03 bắt buộc) + `tick` đã chọn giấy tờ; ảnh TÙY (thiếu ảnh vẫn nạp được, chỉ cảnh báo). Không gọi server.
- **Hai chip trạng thái mỗi dòng (CHANGES #32):** ngoài gộp `✔ Sẵn sàng`, hiện **2 chip RIÊNG** để nhìn nhanh từng mục: **Địa chỉ** (`✓ Địa chỉ 2 cấp` khi `diaChi != null`, else `✗ Chưa map` xám) · **Ảnh** (`✓ Có hình` khi có `jp2`/ảnh nháp, else `✗ Chưa có hình` xám). Mặc định `✗` khi chưa chuẩn bị. (Giấy tờ vẫn tính vào "Sẵn sàng" nhưng không ra chip riêng — tránh rối; chip chỉ cho 2 mục user quan tâm nhất.) **Nguồn chip = cờ NHẸ** `GET /local/nap/nhap?uuids=…` (`co_dia_chi`/`co_anh`/`co_tick` — §9.3a), KHÔNG tải `jp2_b64` để vẽ chip (review #32, Điểm 5).
- **Nạp — chặn/cảnh báo theo mức bắt buộc (CHANGES #32):** dòng **thiếu địa chỉ → KHÔNG cho nạp** (loại khỏi lô, chip địa chỉ `✗`); dòng **thiếu ảnh → VẪN nạp**, trước khi chạy lô hiện cảnh báo "N học viên nạp thiếu ảnh — bổ sung sau ở Tra cứu DB (lọc chưa ảnh)". Sau lô, nếu có HV thiếu ảnh → nút/lối tắt **chuyển sang Tra cứu DB, đặt bộ lọc "chưa ảnh"** (reuse nút "Xem trong DB") để bổ sung ngay qua QLY-05.
- **Chọn tất cả sẵn sàng:** nút tick mọi dòng `✔ Sẵn sàng` trong nhóm "Cần xử lý"; thanh hành động dính đáy "Nạp N học viên" (reuse batch bar sẵn có).
- **Ngăn "Chuẩn bị" (drawer):** chuyển cột-chuẩn-bị-cố-định hiện tại (AddressCombo + giấy tờ + AnhModal) thành ngăn trượt từ phải, mở theo dòng; lưu xong → dòng thành `✔ Sẵn sàng` + tự tick. Giảm tải thị giác, màn còn 1 danh sách. **Mở drawer (CHANGES #32):** **cả dòng bấm được** + **nút "Xử lý" to rõ bên phải** mỗi dòng (không dùng icon nhỏ) — dễ thao tác, khó bấm nhầm. Mở drawer mới gọi `GET /local/nap/nhap/{uuid}` lấy nháp đầy đủ (ảnh). Trong drawer có **nút "Xóa nháp"** (gọi `nhap_xoa` — review #32, Điểm 4) để dọn chủ động; preview địa chỉ ghép theo luật phẩy §9.3a (`[chi_tiet, TenDayDu(xã)].join(", ")`).
- **Dialog nạp 3 pha:** reuse pattern `DoiNenDialog` (task 40 QLY-07) — (1) xác nhận (khóa đích + số sẵn sàng/bỏ qua) → (2) chạy: gọi `nap_lo(items)`, thanh % + N/tổng + tên HV đang nạp (`nap_lo` trả `{uuid, ok, loi}` từng dòng — hiện tiến độ theo kết quả trả về, không cần endpoint polling mới nếu `nap_lo` trả dần; nếu trả 1 lần thì hiển thị tiến độ theo thứ tự xử lý) → (3) báo cáo: đếm ok/lỗi + lý do từng dòng + nút "Nạp lại lỗi" (chọn lại các `uuid` lỗi, gọi `nap_lo` tiếp).
- **Nút "Xem trong DB":** ở dòng `xong` + trong báo cáo → chuyển sang chế độ Tra cứu DB (cùng component `NapHoSo`/`TraCuuDB`), set khóa = khóa đích + làm nổi `MaDK` vừa nạp (từ kết quả `nap_lo`).

> Lưu ý khi code (CHANGES #26): nếu muốn tiến độ mượt theo từng HV mà `nap_lo` hiện trả 1 lần cho cả lô, cân nhắc nạp tuần tự từng `uuid` ở client (gọi `nap_lo` 1-uuid nhiều lần như "Nạp lại nhanh") để cập nhật thanh % — quyết lúc code, không thêm endpoint server nếu tránh được.

---

## 11. Quản lý hồ sơ đã có & tạo khóa (tool)

> **Phục vụ:** `QLY-01`, `QLY-02`, `QLY-03`, `QLY-05`, `QLY-07`, `KHO-01`
*Vì sao gộp: đều là thao tác của operator trên DB đích qua SP, cùng ràng buộc BC1/GPLX.*

### 11.1 Tra cứu/sửa (QLY-01)
**Chế độ "Tra cứu DB" (CHANGES #6):** tìm khóa theo **tên/mã, MỌI khóa kể cả đã BC1** (SELECT `KhoaHoc` lọc theo tên/mã, **KHÔNG** lọc `BaoCaoI` — khác dropdown nạp của NAP-02). Chọn khóa → lưới theo khóa (`usp_NguoiLX_Select_By_MaKH`) + tìm trong lưới (client) → xem chi tiết → **sửa NHÂN THÂN**.

**Sửa (lát 2, CHANGES #17) — chỉ bảng `NguoiLX` qua `usp_NguoiLX_Update`.** Phạm vi: họ tên, ngày sinh, giới tính, số căn cước (SoCMT), địa chỉ thường trú chi tiết (NoiTT). KHÔNG dùng `usp_NguoiLX_HoSo_Update` ở QLY-01 — SP đó ghi đè **65 cột** của `NguoiLX_HoSo` (kết quả thi, BC1/BC2, ảnh) trong khi `usp_NguoiLX_HoSo_Get_Sua_HS` chỉ trả một phần → rủi ro xóa trắng. Ảnh thuộc QLY-05, đổi khóa thuộc QLY-02. **An toàn ghi:** `usp_NguoiLX_Update` cũng ghi đè 22 cột → đọc lại full bản ghi `NguoiLX` hiện tại (SELECT), chồng 5 trường user sửa, giữ nguyên phần còn lại; đọc + ghi trong 1 kết nối. NgaySinh lưu `yyyymmdd` (hoặc `yyyy`), GioiTinh `M/F/U`, họ tên IN HOA giữ dấu (dùng chung `tach_ho_ten`). Khóa đã BC1 → UI ẩn nút Sửa, backend kiểm lại → 409 (BR-012).

**Tìm trong lưới học viên (CHANGES #10):** khớp theo **tên hoặc số CCCD**; tên **chuẩn hóa bỏ dấu cả hai vế** (NFD + xóa dấu kết hợp) để gõ không dấu vẫn ra. QLY-01 tìm qua SP `usp_NguoiLX_HoSo_Search` (collation không phân biệt dấu, hoặc chuẩn hóa tương tự); NAP-01 (list tải về, hàng chờ VPS) lọc phía client trên staging SQLite đã kéo. UI chung: ô tìm đặt **đầu danh sách/lưới**; màn hẹp thu gọn thành **nút kính lúp** (bấm mới bung ô nhập).

**Xem ảnh + avatar + thống kê (CHANGES #22).** Ảnh lưu là `.jp2` (JPEG 2000) — trình duyệt KHÔNG render được → backend phải transcode:
- `GET /local/ho-so/anh?ma_dk=` → đọc `DuongDanAnh` (`NguoiLX_HoSo`) → đọc file `.jp2` → **transcode sang PNG** (Pillow/openjpeg, dùng lại `image.py`) → trả `image/png`. **File mất** (DB có path, ổ không có) → **404**; **file hỏng/không giải mã được** → **422** (KHÔNG để 500). `ma_dk` tra DB parameterized, đường dẫn lấy từ cột DB (không ghép từ input) → không path traversal.
- `GET /local/ho-so/anh-thumb?ma_dk=` → PNG **thu nhỏ** (vd 96px) cho avatar → UI dùng `<img loading="lazy">` + **chỉ fetch dòng đang hiển thị** (IntersectionObserver), không request dòng ngoài viewport. **Cache (`MaDK`, mtime)** ở thư mục tạm cục bộ (`staging/anh-cache/`, thêm vào `.gitignore`; hoặc transcode in-memory) — ảnh là PII, không để lọt backup/commit.
- **Avatar phân biệt 3 ca:** `co_anh=false` → icon người (chưa ảnh); `co_anh=true` + thumbnail OK → ảnh; `co_anh=true` nhưng 404/422 (file mất/hỏng) → **icon ảnh-vỡ** (khác icon người, để không nhầm với chưa nạp ảnh).
- Modal chi tiết hiện **ảnh lớn + dòng `DuongDanAnh`** (cảnh báo nếu 404/422); click ảnh → trình chỉnh (QLY-05, §11.5). Thống kê đầu khóa (tổng HV · thiếu ảnh · đã BC1) tính **client** trên dữ liệu lưới đã tải (`co_anh`, cờ BC1), không thêm endpoint.
- Nút **đổi khóa / xóa nhanh** đưa ra lưới gọi lại QLY-02/QLY-03 (vẫn xác nhận 2 bước, tôn trọng chặn BC1 — §11.3).

### 11.2 Đổi khóa (QLY-02) — vòng đời file ảnh
```
Cùng hạng: usp_NguoiLX_HoSo_Update (MaKhoaHoc mới) + sinh lại SoHoSo theo khóa mới
  → di chuyển file .jp2 sang folder khóa mới (giữ tên) → cập nhật DuongDanAnh
Khác hạng: hướng xóa tạo lại.
```

### 11.3 Xóa HV (QLY-03)
`usp_NguoiLX_Delete` (cascade HoSo+GiayTo) + chuyển file `.jp2` sang `_DELETED` (xóa mềm). HV có GPLX → FK chặn.

**Chặn xóa HV ở khóa đã BC1 — BACKEND (CHANGES #22).** `usp_NguoiLX_Delete` cascade xóa `NguoiLX_HoSo` → mất cột `MaBC1`/`MaBC2` (FK `FK_NguoiLX_HoSo_BaoCaoI` + liên kết `BaoCaoII`) → HV **biến mất khỏi Báo cáo 1/2** (`usp_BaoCao1_DSHS`/`usp_BaoCao2_DSHS` chọn theo `NguoiLX_HoSo`). Hiện code chỉ **ẩn nút UI** khi khóa BC1, backend chưa chặn → phải thêm kiểm: trước `usp_NguoiLX_Delete`, `EXISTS(SELECT 1 FROM BaoCaoI b WHERE b.MaKH = <khóa của HV>)` → có → **409, không xóa** (BR-012 mở rộng cho xóa, như QLY-01/QLY-02 đã làm). *Verify schema DBcu 30/09: `NguoiLX_HoSo.MaBC1 varchar(18)` FK→`BaoCaoI.MaBCI`; `MaBC2 varchar(13)`; `BaoCaoII.MaBCI`→`BaoCaoI`.*

```
Liên kết HV ↔ Báo cáo (schema DBcu):

  NguoiLX ──1:1── NguoiLX_HoSo ──FK MaBC1──► BaoCaoI (PK MaBCI, theo khóa MaKH)
   (MaDK)          (MaDK, MaBC1,                   ▲ FK MaBCI
                    MaBC2, TT_XuLy)                │
                        └────── MaBC2 ──► BaoCaoII ┘ (PK MaBCII)

  Xóa NguoiLX → cascade NguoiLX_HoSo → mất MaBC1/MaBC2
             → HV biến mất khỏi Báo cáo 1/2
  ⇒ QLY-03 chặn xóa khi khóa đã BC1
```

### 11.4 Tạo khóa (KHO-01)
Chọn hạng ĐT từ `DM_HangDT` → `usp_KhoaHoc_Insert` (mã tự sinh). `HangGPLX` suy từ hạng ĐT qua `DM_HangGPLX.MaHangMoi`.

### 11.5 Nạp/thay ảnh cho HV đã có (QLY-05)
Làm SAU NAP-05, **dùng lại cơ chế ghi ảnh hướng A** (§10.3) — không gọi SP tạo hồ sơ. Luồng: màn tra cứu lọc HV theo tình trạng ảnh (`TT_XuLy='01'` chưa ảnh / `'03'` đã ảnh) → chọn HV → xử lý ảnh (tái dùng NAP-04: crop 3:4 + nền trắng + `.jp2` 353×471) → ghi `.jp2` tại `<IMG_PATH_CSDT>\<MaKhoaHoc>\<MaDK>.jp2` (ghi đè nếu đã có) → UPDATE cột ảnh `NguoiLX_HoSo` (`DuongDanAnh`, `ChatLuongAnh=1`, `NgayThuNhanAnh=getdate()`, `NguoiThuNhanAnh`) WHERE `MaDK`. Chỉ cập nhật HV đã có, không tạo bản ghi mới.

**🐛 `TT_XuLy` — quy tắc "KHÔNG BAO GIỜ HẠ" (CHANGES #22).** Hàm dùng chung `ghi_anh_update` (NAP-05 + QLY-05) hiện set cứng `TT_XuLy='03'`. Nhưng `usp_BaoCao2_DSHS` lọc HV theo tập `TT_XuLy in ('11','12','13','14','16','17','18','19')` (lưu ý **thiếu `'15'`**) → hạ HV đã Báo cáo về `'03'` thì **rơi khỏi Báo cáo 2** ("HV không có trong BC1"). → Sửa: **chỉ set `'03'` khi HV CHƯA có ảnh (`TT_XuLy` hiện tại là `'01'`/`'02'`); mọi giá trị khác (`'03'` và mọi mã Báo cáo) → GIỮ NGUYÊN** — nguyên tắc thay ảnh **không bao giờ HẠ** `TT_XuLy` (dùng whitelist `'01'/'02'`, không dùng ngưỡng `< '11'`). NAP-05 nạp HV mới luôn ở `'01'` → vẫn lên `'03'` đúng. **Ghi ảnh atomic:** ghi file tạm cùng thư mục → `os.replace` sang tên đích (crash giữa chừng không để lại `.jp2` cụt). **Mở từ Tra cứu DB:** click avatar/ảnh HV đã có → ảnh `.jp2` transcode→PNG (§11.1) nạp vào `AnhModal` làm ảnh gốc → đổi nền/chỉnh → lưu đè; **file gốc 404 → AnhModal mở chế độ chọn-file mới** (báo "ảnh cũ không còn, chọn ảnh mới").

**Bổ sung ảnh cho HV THIẾU ảnh — 2 nguồn (CHANGES #32).** HV đã nạp nhưng `TT_XuLy='01'` (chưa ảnh) không có `.jp2` để làm ảnh gốc. Mở `AnhModal` với nguồn ảnh gốc chọn 1 trong 2 — **tái dùng toàn bộ, không viết cơ chế nạp ảnh mới**:
- **(a) Chọn từ file máy tính:** `AnhModal.chonFile` sẵn có → crop + đổi nền như NAP-04.
- **(b) Kéo ảnh thô VPS:** tra `uuid` theo `ma_dk` (`vps.tra_uuid`, §4.4) → tải ảnh thô (`vps.tai_anh` / proxy `tai_anh_keo_ve`) → URL nạp vào `AnhModal.napTuUrl` (sẵn có) làm ảnh gốc. **Điều kiện:** ảnh thô còn trên VPS (bản gửi giữ ~30 ngày — §9.3/BR-016). Hết hạn/không tra được uuid → ẩn nguồn (b), chỉ còn (a), báo "ảnh gốc trên máy chủ đã hết hạn, chọn ảnh từ máy".

Sau khi có ảnh gốc, cả 2 nguồn đi tiếp qua **cùng luồng QLY-05** (xuất `.jp2` → `nap_anh` → `ghi_anh_update`, nâng `TT_XuLy '01'→'03'`). *Vì sao tái dùng được trọn: `AnhModal` đã có cả `chonFile` lẫn `napTuUrl`; `vps.tra_uuid`/`vps.tai_anh` đã có cho QLY-08/NAP-01 — chỉ cần wiring.*
*Ca lỗi:* app cũ đang khóa file `.jp2` → báo đóng app cũ rồi thử lại; ghi `.jp2` lỗi → giữ trạng thái ảnh cũ; UPDATE lỗi → retry theo `MaDK` (§10.3).

```
Vòng đời TT_XuLy & quy tắc thay ảnh (QLY-05/QLY-07):

  nạp HV mới (NAP-05)
        │
        ▼
     '01' / '02'  (chưa ảnh) ──(ghi .jp2)──► '03'  (có ảnh)
                                               │
                                               │ (app cũ lập Báo cáo)
                                               ▼
                             '11','12','13','14','16','17','18','19'
                             (đã vào Báo cáo 1/2) ◄── usp_BaoCao2_DSHS lọc tập này

  THAY ẢNH — "KHÔNG BAO GIỜ HẠ":
     • TT_XuLy ∈ {'01','02'}       → set '03'     (chưa ảnh → nâng)
     • mọi giá trị khác ('03'…'19') → GIỮ NGUYÊN  (chỉ thay file + DuongDanAnh)
  Vì sao: hạ HV đã Báo cáo về '03' → rơi khỏi usp_BaoCao2_DSHS
          → "HV không có trong Báo cáo 1" (bug #22)
```

### 11.6 Đổi nền trắng cả khóa (QLY-07) — CHANGES #22
Xử lý hàng loạt ảnh của 1 khóa (chủ yếu ảnh cũ từ app cũ chưa nền trắng). **Dùng lại `ghi_anh_update` với quy tắc giữ `TT_XuLy` của §11.5** — bắt buộc, vì bulk chạm MỌI HV trong khóa cùng lúc; nếu hạ `'03'` thì **cả khóa đã BC2 biến mất khỏi báo cáo** trong một lần chạy.
- **Chạy nền + tiến độ:** endpoint khởi tạo job (vd `POST /local/khoa/:ma_kh/doi-nen`) → xử lý tuần tự từng HV, UI hỏi tiến độ (N/tổng, số lỗi) qua polling hoặc SSE. ~1-3 giây/ảnh (rembg) × ~100 HV ≈ vài phút → KHÔNG làm đồng bộ (treo UI).
- **Sao lưu trước ghi đè:** tùy chọn (mặc định bật) chép `.jp2` gốc sang `<IMG_PATH_CSDT>\<MaKhoaHoc>\_BACKUP\<MaDK>.jp2` — **CHỈ chép nếu `_BACKUP\<MaDK>.jp2` CHƯA tồn tại** (giữ bản gốc đầu tiên; lần chạy sau KHÔNG ghi đè backup, tránh backup thành bản đã xử lý → mất bản gốc thật). Ghi ảnh **atomic** (file tạm → `os.replace`).
- **Phạm vi:** mặc định "chỉ ảnh chưa nền trắng" — phát hiện bằng **heuristic lấy mẫu pixel 4 góc** (gần trắng → coi đã trắng, bỏ qua; DB không có cờ đánh dấu); sai sót nhỏ bù bằng tùy chọn **"tất cả HV có ảnh"** (luôn cho đổi). HV không ảnh → bỏ qua.
- *Ca lỗi từng HV* (file bị khóa app cũ, ghi lỗi) → bỏ qua HV đó, ghi danh sách lỗi, chạy tiếp — 1 HV lỗi không hỏng cả lô.
- *Chống chạy trùng:* bọc job bằng `sp_getapplock(MaKhoaHoc)` (như nạp lô §10.3) để 2 tool không cùng xử lý một khóa (hiếm — thường 1 máy CSDT).

### 11.7 Gỡ HV về chờ nạp (QLY-08) + đồng bộ xóa khi kéo (NAP-01/THU-05) — CHANGES #24

**Gỡ HV về chờ nạp (QLY-08) — nạp nhầm khóa.** Khác "Xóa bỏ hẳn" (QLY-03): sau khi xóa khỏi CSDT thì **trả bản ghi gốc về hàng chờ** để nạp lại đúng khóa. Nút RIÊNG ở Tra cứu DB, chỉ khóa **chưa BC1**.
```
Tool: POST /local/ho-so/go-ve-cho-nap?ma_dk=<>
  1) Chặn khóa BC1 (EXISTS BaoCaoI theo MaKH) → 409 (như QLY-03).
  2) Tra uuid gốc theo ma_dk (liên kết nạp: staging nap_xong(uuid, ma_dk); fallback GET /api/nap/tra-uuid?ma_dk=<> khi staging local không còn — §4.4).
  3) usp_NguoiLX_Delete (cascade HoSo+GiayTo) + ảnh .jp2 → _DELETED (xóa mềm, dùng lại di_chuyen_anh) + log.
     HV đã có GPLX → FK chặn (như QLY-03) → 409, KHÔNG xóa.
  4) Gọi VPS tra-ve-cho-nap(uuid): imported→pending, gỡ ma_dk. VPS 'deleted'/không còn → 409
     "không còn bản gốc trên VPS" (bước 3 đã xóa CSDT rồi → báo rõ cho operator, cho thử lại bước 4).
  5) Staging local: dòng uuid về 'cho'/pending + gỡ ma_dk; nếu đã "Bỏ khỏi hàng đợi" → kéo lại từ VPS.
```
*Thứ tự xóa-CSDT-trước-rồi-VPS:* nếu VPS lỗi sau khi đã xóa CSDT thì HV đã rời khóa (đúng ý "gỡ") nhưng chưa về hàng chờ → báo rõ + cho thử lại riêng bước đồng bộ VPS (không tạo lại HV ở CSDT). Ảnh khi về chờ nạp dùng **ảnh thô còn trên VPS** (`GET /api/nap/keo` trả lại như HV mới), KHÔNG chuyển ngược `.jp2`.

```
QLY-08 "Gỡ về chờ nạp"  (operator ở Tra cứu DB, khóa chưa BC1)
───────────────────────────────────────────────────────────────
 Tool                     CSDT (SQL Server)        VPS
  │  xác nhận 2 bước
  ├─(1) chặn BC1? ─────────▶ EXISTS BaoCaoI theo MaKH
  │        ◀── có → 409 "khóa đã BC1" (DỪNG, không xóa gì)
  │
  ├─(2) tra uuid theo ma_dk (staging nap_xong │ fallback GET /api/nap/tra-uuid)
  │
  ├─(3) usp_NguoiLX_Delete ─▶ cascade HoSo+GiayTo
  │                           ảnh .jp2 → _DELETED (xóa mềm, di_chuyen_anh)
  │        ◀── FK chặn (HV có GPLX) → 409 (DỪNG, chưa xóa)
  │        ✔ CSDT đã xóa  ── điểm KHÔNG hoàn tác ───────────────┐
  │                                                              │
  ├─(4) POST /api/nap/:uuid/tra-ve-cho-nap ───────────▶ CAS imported→pending, gỡ ma_dk
  │        ◀── 'deleted'/không còn → 409 "không còn bản gốc, chỉ Xóa hẳn"
  │        ◀── lỗi mạng/5xx ─────────┐
  │                                   │  HV ĐÃ rời CSDT nhưng CHƯA về hàng chờ
  │   ┌───────────────────────────────┘  → báo rõ + cho THỬ LẠI riêng bước (4)
  │   │                                     (KHÔNG tạo lại HV ở CSDT)
  │   └─ retry (4) ──────────────────▶ (idempotent: đang pending rồi → coi như xong)
  │
  └─(5) staging local: dòng uuid → 'cho'/pending, gỡ ma_dk
         (nếu đã "Bỏ khỏi hàng đợi" → kéo lại từ VPS)
```

**Đồng bộ xóa khi kéo (NAP-01 + THU-05).** Collector xóa hồ sơ `pending` ở app web → VPS `deleted` (soft, §7.1). "Kéo về từ VPS" ngoài THÊM mới + làm tươi (CHANGES #11) nay còn **bỏ dòng staging đã xóa**: với mỗi dòng staging còn `pending` (chưa nạp), nếu VPS báo bản ghi đó **không còn `pending`** (đã `deleted`) → **xóa dòng khỏi staging**. Chỉ áp dòng chưa nạp; dòng đã nạp/đã lỗi giữ nguyên (không bị collector đụng tới).
- *Vì sao so ở bước kéo* (không webhook): tool chạy LAN sau tunnel, không nhận push từ VPS → đồng bộ theo nhịp kéo (operator chủ động). Nguồn chân lý là VPS.
- *Cách so (review #24):* tool gọi `GET /api/nap/da-xoa?since=<mốc kéo trước>` (§4.4) → VPS trả danh sách `uuid` đã chuyển `deleted` từ mốc đó → tool xóa đúng các `uuid` đó khỏi staging. **KHÔNG** suy "đã xóa" từ việc `uuid` vắng mặt trong `GET /api/nap/keo`: `keo` còn lọc `locked_by IS NULL` (§7.2) **và** `limit` → một dòng vẫn `pending` nhưng đang bị tool khác khóa / rớt ngoài limit cũng vắng mặt → suy theo vắng mặt sẽ **xóa nhầm** hồ sơ chưa hề bị xóa.

### 11.8 Đối soát & đồng bộ trạng thái VPS↔CSDT (QLY-09) — CHANGES #28

Bối cảnh: mốc "Nạp" chuyển quyền sở hữu (§7.5) đi qua **2 kho tách biệt** — VPS (`ho_so_thu_thap.trang_thai`) và CSDT (`NguoiLX_HoSo` theo `MaDK`) — nối bằng các bước gọi tuần tự (lock→nạp CSDT→da_nap). Nếu một bước lỗi hoặc có bug (BUG-01: phantom import), 2 kho **lệch nhau** mà không cơ chế nào tự dọn. §11.8 cho operator/admin **phát hiện + sửa lệch bằng tay có hướng dẫn**, KHÔNG để treo.

**Phạm vi (chốt 03/10 — phương án A, sau review TDD): 2 chế độ.** Lý do tách (review TDD 03/10): bản ghi VPS `ho_so_thu_thap` **KHÔNG có cột khóa** — khóa chỉ tồn tại ở CSDT, nối qua `ma_dk`. Ca ② còn hồ sơ ở CSDT nên quy được về khóa; **ca ① (phantom: ma_dk không có trong CSDT) và ca ③ (importing: CHƯA có ma_dk)** đều không quy được về khóa → phải quét theo **trạng thái VPS**, không theo khóa.
- **① Đối soát theo khóa (operator/admin)** → bắt **ca ②**. Neo ở CSDT, chọn 1 khóa.
- **② Quét bản ghi lạc toàn hệ (admin)** → bắt **ca ① + ③**. Neo ở VPS, không cần khóa; tái dùng `GET /api/admin/ho-so` (HTG-03, lọc trạng thái) — nhẹ vì check **một chiều** (duyệt tập VPS imported/importing, tra ma_dk sang CSDT), không so 2 chiều toàn tập.

**Cách phát hiện (đọc, không ghi):**
- **Ca ② — theo khóa:** `MaDK` của khóa từ `NguoiLX_HoSo WHERE MaKhoaHoc=@ AND TrangThai=1` (dùng lại truy vấn §11.1 đã bỏ lọc ảnh — BUG-02) → mỗi `MaDK` tra `uuid` gốc qua `nap_xong` local (`uuid↔ma_dk`, ghi lúc nạp) → hỏi trạng thái VPS của `uuid` → **chưa `imported`** = ca ②. *nap_xong là nguồn nối duy nhất; thiếu entry (máy khác / staging đã dọn) → KHÔNG khẳng định lệch, ghi "không tra được uuid" thay vì báo động giả.* **(CHANGES #32 — task 48, hướng A:)** "hỏi trạng thái VPS" = endpoint READ mới **`GET /api/nap/trang-thai?uuids=`** (operator gọi được, batch nhiều uuid 1 lượt, read thuần — không phải endpoint nạp); uuid VPS đã dọn PII → không trả → ghi "không tra được uuid".
- **Ca ① + ③ — quét lạc toàn hệ:** `GET /api/admin/ho-so?trang_thai=imported` → mỗi bản ghi có `ma_dk` → check `ma_dk` **tồn tại trong CSDT** (`NguoiLX_HoSo`) → KHÔNG có = **ca ① phantom**. `?trang_thai=importing` + `locked_at` quá ngưỡng (§7.2) = **ca ③ treo**. **(CHANGES #32 — task 48:)** `GET /api/admin/ho-so` bổ sung trả thêm `ma_dk` + `locked_at` (trước chỉ có cho HTG-03, thiếu 2 field này) — additive, không vỡ consumer cũ.

**3 ca lệch + hành động (tái dùng §11.7, KHÔNG endpoint/SP nạp mới):**
```
① VPS imported  &  CSDT KHÔNG có MaDK   (phantom — BUG-01)
      → "Trả về chờ nạp": vps.tra_ve_cho_nap(uuid) [imported→pending, gỡ ma_dk]
         KHÔNG đụng CSDT (vốn đã không có). + keo_ve_ve_cho(uuid) đưa staging về 'cho'.
② CSDT CÓ HV    &  VPS chưa imported     (nạp CSDT xong, báo VPS lỗi)
      → "Đánh dấu đã nạp": vps.da_nap(uuid, ma_dk)  [idempotent]
③ VPS importing treo (lock kẹt, quá ngưỡng, không ai đang nạp)
      → "Mở khóa": vps.unlock(uuid)  [importing→pending]
```
- *Ngưỡng ca ③:* chỉ gợi "Mở khóa" khi `importing` **quá lâu** (vd > ngưỡng job tự mở khóa §7.2, ~15') — tránh đụng dòng đang nạp thật ở máy khác.
- *Chặn BC1/PII:* nút sửa nào đụng xóa/gỡ phải tôn trọng chặn BC1 (QLY-03/08); ca ② mà VPS đã dọn PII (HTG-03) → không `da_nap` được, báo rõ.
- *Không tự động hàng loạt:* mỗi dòng operator tự bấm (tránh sửa nhầm diện rộng).

**Phòng tuyến 2 — chặn tái phát phantom (gốc BUG-01).** Trong `nap_lo` router (`nap_fn`), thứ tự hiện tại: `vps.lock` → `_nap_mot` → `vps.da_nap`. Khi `_nap_mot`→`nap_mot_hv` **trả kết quả cũ từ vé `nap_xong`** (`_done_get` trúng, KHÔNG INSERT mới) thì **BỎ gọi `vps.da_nap`** — nếu không, bản ghi không thực sự vào CSDT vẫn bị đánh dấu VPS `imported` (đúng kịch bản phantom). Cách làm: `nap_mot_hv`/`_nap_mot` trả cờ phân biệt "nạp mới" vs "trả vé cũ" (vd field `trung_uuid` đã có ở `_done_get`), `nap_fn` chỉ `da_nap` khi là nạp mới. *Vì sao vẫn giữ vé idempotency:* chống bấm nạp 2 lần tạo HV trùng (§10.3) — chỉ bỏ cái `da_nap` dư trên nhánh vé-cũ.

> Tool (webui 2 panel + tool backend đọc CSDT/gọi VPS: `doisoat.py` — `/local/doi-soat/khoa`·`/lac`·`da-nap`·`tra-ve`·`mo-khoa`). Tái dùng `tra_ve_cho_nap`/`da_nap`/`unlock` + `nap_xong` local. KHÔNG bảng VPS mới, KHÔNG SP CSDT mới, KHÔNG endpoint **nạp** mới. **Có 2 thay đổi SERVER (read, CHANGES #32 task 48, hướng A — cần deploy VPS):** thêm `GET /api/nap/trang-thai?uuids=` (ca ②) + admin `/ho-so` trả thêm `ma_dk`/`locked_at` (ca ①③). *Vì sao phải đổi server: bản ghi VPS không phơi trạng-thái-theo-uuid cho operator, và admin list thiếu `ma_dk`/`locked_at` — không có 2 field này thì ca ①③ không phát hiện được.*

---

## 11B. Đồng bộ CDB (tool — workspace riêng) — SYNC-01/02/03 (CHANGES #33)

> Port nghiệp vụ từ `D:\Du_An\GPLX\sync_tool` **v2.0** (3 file: `sync_gplx.py` + `db_helpers.py` + `sync_history.py`). Đổi driver `pyodbc` (`?`) → **`pymssql`** (`%s`) cho khớp tool. **Tách hoàn toàn** khỏi nghiệp vụ Nạp.

### 11B.0 Kiến trúc tách workspace (mở rộng N module)

Tool có **nhiều module độc lập**, điều hướng **2 cấp**: **sidebar bên trái** liệt kê module → bấm module nào thì vùng nội dung hiện **sub-nav + các màn** của module đó (mỗi module 1 bộ route + màu nhấn + banner DB). **Không hardcode** — đăng ký module qua một bảng (id, nhãn, icon, màu, route gốc, sub-nav) để thêm module #3 "Cập nhật kết quả học tập" (dự kiến) chỉ bằng một dòng, không sửa khung.

```
Sidebar          Module                 sub-nav (màn trong module)                → DB ghi
───────────────────────────────────────────────────────────────────────────────────────
◉ Nạp hồ sơ      Thu nhận hồ sơ (xanh)   /tool/{nap,tao-khoa}                      → GPLX_CSDT
○ Đồng bộ CDB    Đồng bộ CDB (hổ phách)  /sync/{ban-dong-bo,lich-su}               → GPLX_CDB_CSDT
○ Kết quả học tập (dự kiến)              /ketqua/* (chưa đặc tả)

⚙ Cấu hình (header, dùng chung — HTG-07, CHANGES #34): panel mở từ icon ⚙ trên header, KHÔNG nằm trong sub-nav module. Hai khối: ① kết nối chung + DB nguồn Nạp GPLX_CSDT · ② nhiều DB đích Sync. Thay cho route /tool/cau-hinh + /sync/db-dich (đã bỏ khỏi sub-nav).
```

- **Backend tách module:** `app/routers/sync.py` + `app/sync_service.py` (vòng sync, rollback) + `app/sync_helpers.py` (sinh MaDK, enrich, load năm/khóa, copy row, snapshot — port `db_helpers.py`) + `app/sync_history.py` (port nguyên). **Không import** `nap.py`/`anh.py`/… và ngược lại — tránh xung đột + nhầm lẫn.
- **Frontend:** đổi khung `ToolLayout` từ thanh nav trên cùng → **sidebar trái (danh sách module) + vùng nội dung có sub-nav**. Module đăng ký trong một mảng `MODULES` (mở rộng N). Màn sync: `webui/src/pages/sync/*`. Nav Nạp hiện tại chuyển thành sub-nav module Nạp — **hành vi màn Nạp không đổi**.
- **Bề rộng (tool CHỈ desktop — không mobile/responsive):** thiết kế cho cửa sổ rộng; **sidebar thu gọn được** (icon-only ~56px ↔ mở ~220px) để nhường bề ngang cho nội dung; vùng nội dung giữ bề rộng tối thiểu dễ đọc (ngắm ~1280px trở lên, canh giữa tối đa ~1500px như hiện tại). **Bảng Bàn đồng bộ nhiều cột (11 cột) → cho cuộn ngang TRONG vùng bảng**, không ép co cột tới mức chữ/`MaDK` 21 ký tự bị cắt. Kiểm bề rộng bằng Playwright ở 1280/1440/1920, bắt tràn ngang + cột chồng chữ trước khi coi là xong.

*Vì sao tách cứng: Nạp ghi vào DB nguồn (`GPLX_CSDT`), Sync ghi vào DB đích (`GPLX_CDB_CSDT`) — trộn nav/module dễ khiến nhân viên thao tác nhầm DB. Tách module backend để sửa bên này không vỡ bên kia.*

### 11B.1 Kết nối DB đích (nhiều đích)

- `app/db.py` thêm `sqlserver_conn_dich(db_name)` / `sqlserver_cursor_dich(db_name)`: **dùng chung** `sqlserver_host/user/password` của cấu hình nạp, **chỉ thay `database`**.
- Cấu hình (khối riêng trong `config.enc`, mã hóa Fernet như hiện tại):
  ```json
  "sync_targets": [{"key":"cdb_chinh","name":"CDB chính","database":"GPLX_CDB_CSDT"}],
  "sync_selected": "cdb_chinh",
  "sync_options": {"tt_xuly_force":"03","update_tong_so_hv":true}
  ```
- Bàn đồng bộ cần **2 kết nối cùng lúc**: nguồn (`sqlserver_conn`) + đích (`sqlserver_conn_dich`), cùng 1 SQL Server, khác DB.

### 11B.2 Luồng sync 1 HV (nghiệp vụ DB đích: 1 người = 1 hồ sơ = 1 MaDK)

```
Tải DS: đọc HV khóa nguồn (JOIN NguoiLX+NguoiLX_HoSo) → enrich đối chiếu đích theo SoCMT
   → phân nhánh:  đã có đích → SKIP   |   chưa có → NEW
SYNC NEW: dọn NguoiLX mồ côi → sinh/nhận MaDK → usp_NguoiLX_Insert (NguoiTao='admin')
   → [backdate] UPDATE NgayTao/NgaySua → INSERT NguoiLX_HoSo (SoHoSo, TT_XuLy, NgàyHS)
   → copy NguoiLXHS_GiayTo (best-effort) → ghi log JSON (sau mỗi HV) → emit SSE
Sau lô: cập nhật KhoaHoc.TongSoHV (nếu bật)
```

- **MaDK** `MaCSDT-yyyyMMdd-nnnnnn` (21 ký tự, MaCSDT đúng 5 số — `70004` đạt): ngày=hôm nay → để SP tự sinh; **backdate** → `sinh_madk_batch` query `MAX(SUBSTRING(MaDK,16,6))` theo prefix, cấp dải `[MAX+1..MAX+N]`, backdate `NgayNhanHSo/NgayTao/NgaySua`.
- **Guard race:** trước INSERT, `kiem_tra_madk_ton_tai` → trùng thì sinh lại, tối đa 3 lần rồi báo lỗi HV đó.
- **Validate:** hạng khóa nguồn = hạng khóa đích; `NgayNhanHSo ≤ NgayKG` khóa đích; backdate > 90 ngày → hỏi.
- **Chọn khóa (CHANGES #36, 05/10/2026):**
  - `load_khoa_hoc_by_year` **ORDER BY NgayKG DESC, MaKH DESC** (mới-nhất-trước + sort phụ ổn định khi trùng ngày); combo nguồn hiện thêm ngày KG. Endpoint `dich/khoa` trả thêm cờ **`dkkh`** (`with_dkkh=True` → `sync_helpers.dkkh_exists_sql`), chỉ bật cho đích (bảng `TRANS_CLI_HangDoiGui` chỉ có ở đích).
  - **Filter khóa đích** (client, mặc định bật): combo đích chỉ hiện khóa **`!dkkh`** (chưa gửi đăng ký lên Sở) **AND cùng hạng** — nếu **đã chọn khóa nguồn** thì thêm điều kiện `hang_gplx == hang khóa nguồn`; **chưa chọn khóa nguồn** thì **bỏ điều kiện hạng** (chỉ lọc `!dkkh`). Bỏ tích → hiện tất cả. Giữ người dùng khỏi chọn khóa khác hạng (sync sẽ chặn) hoặc khóa đã gửi Sở (thêm HV lệch danh sách đã đăng ký).
  - **Tự kiểm kết nối đích** chạy 1 lần khi **vào màn / đổi CSDL đích** (mở cổng "Tải danh sách" nếu OK) — thay cho việc bắt bấm tay mỗi lần; nút "Kiểm tra kết nối đích" vẫn giữ để thử lại thủ công khi mạng chập chờn.

### 11B.3 Tiến trình trực tiếp (SSE)

- `POST /local/sync/run` → tạo `job_id`, chạy vòng sync ở **thread nền**, đẩy sự kiện vào `asyncio.Queue`.
- `GET /local/sync/stream?job=<id>` → `text/event-stream`, emit mỗi HV `{stt, ho_ten, trang_thai, mau, ma_dk_moi}` + sự kiện tổng kết `{ok, skip, loi, tong_so_hv}`.
- Ngắt SSE giữa chừng → **job vẫn chạy tới hết** (an toàn dữ liệu); client vào lại đọc tổng kết. App 1 người dùng → job lưu dict theo `job_id`, không cần hàng đợi bền.

### 11B.4 Lịch sử & rollback (dual-mode)

- Log JSON máy tool: `%APPDATA%\GPLX_Sync\history\<MaKhoaHoc>_<timestamp>.json` (atomic write, ghi sau mỗi HV). Schema `SyncBatch`: khoa_moi/khoa_cu, ngày, cán bộ, `ma_dk_moi[]`.
- **Hủy sync khóa:** xóa `NguoiLX`+`NguoiLX_HoSo`+`NguoiLXHS_GiayTo` của các MaDK trong log **cộng** nhóm `NguoiTao='SYNC'` (tương thích công cụ cũ) → cập nhật `TongSoHV`.

### 11B.5 API

```
GET  /local/sync/targets · POST /local/sync/targets            quản lý DB đích + options
GET  /local/sync/nam?db= · GET /local/sync/khoa?db=&nam=        combo năm/khóa (nguồn & đích)
POST /local/sync/hoc-vien                                       HV khóa nguồn + enrich đích
POST /local/sync/run → {job_id}  ·  GET /local/sync/stream?job= chạy + SSE
GET  /local/sync/lich-su?db= · POST /local/sync/rollback        lịch sử + hủy sync khóa
```

Gác `Depends(require_session)` như các router local khác.

### 11B.6 Nợ kỹ thuật port từ sync_tool (quyết khi code)

**Đã xác minh DB đích 04/10/2026** (chi tiết: `docs/DB-GPLX_CDB_CSDT.md`) → hướng chốt cho 3 tồn đọng:
1. `SoHoSo` + MaDK: **PORT SÁT sync_tool v2.0** — `usp_NguoiLX_Insert` (NguoiLX, `@MaDK` OUT) + **INSERT thô `NguoiLX_HoSo`** với **SoHoSo SỐ** (MAX(CAST(SoHoSo AS INT))+1 theo khóa, zero-pad 3). ⚠️ **ĐÍNH CHÍNH 04/10 (verify dữ liệu):** CSDL đích 100% SoHoSo số thuần `001/002` (kể cả 502 bản phần mềm CDB tạo), **KHÔNG** dùng `CreateNewSoHoso` (ra `B01` lệch). PK `NguoiLX_HoSo = MaDK` → SoHoSo trùng giữa khóa không vi phạm PK ("nợ #1" không áp dụng). Backdate: tự sinh MaDK (sinh_madk_batch) + UPDATE 4 cột ngày (SP hardcode getdate).
2. `DELETE` mồ côi: **lọc theo khóa + MaDK trong log JSON**, không quét toàn DB; rollback dựa PK(MaDK) + cascade `NguoiLX→HoSo→GiayTo`. Bắt lỗi khi HV đã BC1 (FK `HoSo→BaoCaoI` NO_ACTION chặn xóa).
3. Copy giấy tờ: dùng `usp_NguoiLXHS_GiayTo_Insert` / hàm `GetMaGiaytoByHosoForSync`; không nuốt lỗi âm thầm — ghi cảnh báo.

**MaCSDT lấy từ khóa đích** (`KhoaHoc.MaCSDT` = `QTHT_ThamSoHT.MA_CSDT`, DB dev = 75032), KHÔNG bê từ bản ghi nguồn. `usp_NguoiLX_Insert` chữ ký khớp 1:1 sync_tool — port không phải sửa. Còn kiểm: `NguoiLXHS_GiayTo.MaGT` có IDENTITY không.

### 11B.7 Tra cứu CDB đích — xem/sửa/xóa HV trên DB đích (TCB-01..04, CHANGES #35)

Màn **Tra cứu CDB** (tab trong phân hệ Đồng bộ) soi dữ liệu HV **ở CSDL đích `GPLX_CDB_CSDT`** — song song màn Tra cứu DB bên Nạp (QLY-01) nhưng mọi truy vấn qua `sqlserver_conn_dich(db_đích)`, KHÔNG đụng `GPLX_CSDT`. Dựng màn mới `webui/src/pages/sync/TraCuuCDB.tsx`, **tái dùng** component con `AnhModal`/`AnhAvatar`/bố cục chi tiết — không sửa `TraCuuDB.tsx` (tránh vỡ QLY-01).

- **Đọc:** tra khóa (mọi khóa kể cả BC1) + lưới HV theo khóa + chi tiết + ảnh (đọc `.jp2` theo `DuongDanAnh` của bản ghi CDB, qua endpoint ảnh trỏ DB đích). Endpoint mới trong `routers/sync.py` (hoặc module `sync_tracuu.py`). **Các endpoint TCB GHI** (thay ảnh / sửa nhân thân / xóa / đổi khóa) buộc **token operator** như mọi `/local/*` (collector → 403).
- **Luật khóa sửa/xóa — đọc trạng thái Ở ĐÍCH (độc lập DB Nạp):**
  - **BC1** (mốc CỨNG): nhận biết bằng **`NguoiLX_HoSo.MaBC1` có giá trị** — đúng cái FK `FK_NguoiLX_HoSo_BaoCaoI` NO_ACTION chặn xóa (chốt /reviewtdd 04/10). **KHÔNG** dùng `TT_XuLy ≥ '05'` (thang chưa đối chiếu `DM_TrangThai` thật, dễ lệch) và **KHÔNG** dùng dòng `BaoCaoI` cấp khóa (`EXISTS … WHERE MaKH` — chặn rộng hơn FK, lệch cấp HV). Dùng chặn **xóa + đổi khóa** (TCB-04); vẫn **bắt lỗi FK** làm lưới an toàn phòng khi `MaBC1` NULL mà DELETE vẫn vướng FK khác.
  - **Đã kết xuất DKKH** (mốc MỀM): khóa **đã gửi đăng ký khóa học lên Sở/TW** = tồn tại gói `TRANS_CLI_HangDoiGui` có `KieuDuLieu='DANG_KY_KHOA_HOC'` mà `DuongDan` (tên file) chứa MaKH của khóa. Định nghĩa chung: `sync_helpers.dkkh_exists_sql(alias)` (CHARINDEX, tránh `%` pymssql). Dùng chặn **sửa nhân thân** (TCB-03). **KHÔNG dùng `KhoaHoc.SoQD_KhaiGiang`** (sai — mọi khóa đều có số QĐ khai giảng nội bộ nên luôn bật; verify DB 05/10: 16 khóa đều có SoQD nhưng chỉ 14 đã gửi Sở) và KHÔNG dùng `KhoaHoc.TT_Xuly` (luôn NULL). Chi tiết: `docs/DB-GPLX_CDB_CSDT.md` §7. *(Sửa CHANGES #36, 05/10/2026 — trước đây dùng SoQD, chặn nhầm khóa chưa gửi Sở.)*
  - **Thay ảnh (TCB-02):** cho phép bất kể DKKH/BC1 (chỉ cảnh báo) — ảnh là sửa chất lượng, cùng người.
  - Danh mục trạng thái: `DM_TrangThai` (MaTT→TenTT chi tiết + nhóm cấp CDB `MaTTCDB`/`TenTTCDB`; 03/04="Đã đăng ký khóa học", 05-07=đang đào tạo/BC1, 09-14=kết quả/BC2). *Thang này chỉ để HIỂN THỊ tên trạng thái, KHÔNG dùng làm mốc chặn (mốc chặn đọc `MaBC1` + gói DKKH như trên). Lưu ý `NguoiLX_HoSo.TT_XuLy` per-HV cũng không phản ánh DKKH: khóa đã gửi DKKH, HV vẫn ở `03`.*

**Ma trận quyết định (thao tác × mốc khóa đọc ở đích):**

| Thao tác | Chưa DKKH | Đã DKKH (có gói `DANG_KY_KHOA_HOC` gửi Sở) | Đã BC1 (`MaBC1` có giá trị) |
|---|---|---|---|
| Thay ảnh (TCB-02) | cho | cho (cảnh báo) | cho (cảnh báo) |
| Sửa nhân thân (TCB-03) | cho | **CHẶN** | **CHẶN** |
| Xóa / đổi khóa (TCB-04) | cho | **CHẶN** (#36) | **CHẶN** (FK NO_ACTION) |

*TCB-03 + TCB-04 chặn chủ yếu bằng **mốc DKKH** (gói `DANG_KY_KHOA_HOC` gửi Sở, `dkkh_exists_sql`/`dkkh_exists_cond`): BC1 luôn sau DKKH trong quy trình (muốn BC1 phải đã kết xuất đăng ký khai giảng) nên khóa BC1 đương nhiên đã bị DKKH chặn — BC1 (`MaBC1`) + lỗi FK giữ làm lưới an toàn. **TCB-04 (CHANGES #36, 05/10):** xóa HV → chặn nếu khóa HV đã DKKH; đổi khóa → chặn nếu **khóa đi HOẶC khóa đến** đã DKKH; endpoint `khoa-cung-hang` lọc sẵn khóa đã DKKH/BC1 (`NOT dkkh_exists_cond`). EC: CCCD trùng HV khác trong khóa (TCB-03) → **cảnh báo mềm, vẫn lưu** (không chặn).*
- **Thay ảnh (TCB-02):** AnhModal + đổi nền (`/local/anh/xu-ly` rembg) y Nạp → **ghi đè đúng file `.jp2` cũ, giữ nguyên tên + `DuongDanAnh`**. Ảnh là **1 file vật lý dùng chung** giữa Nạp và đích (sync copy path verbatim) → thay = cả 2 DB cùng đổi (user chốt). **Trước khi ghi đè, sao lưu ảnh cũ sang `<tên>_BACKUP.jp2` CÙNG thư mục** (chỉ tạo nếu chưa có) — lỡ tay thay nhầm còn khôi phục, vì ảnh dùng chung nên mất là mất ở cả 2 DB (bám tiền lệ `_BACKUP` QLY-07 §11.6). UPDATE `ChatLuongAnh`/`NgayThuNhanAnh` ở bản ghi CDB. *Vì sao giữ đường dẫn:* ảnh sinh trước theo DB Nạp, 2 DB trỏ chung — tạo file mới sẽ làm 2 DB lệch ảnh.
- **Sửa nhân thân (TCB-03):** `usp_NguoiLX_Update` của CDB (đọc lại full giữ cột không sửa; KHÔNG đụng cột kết quả/BC1/BC2). **Còn kiểm khi code:** CDB có `usp_NguoiLX_Update` / SP đổi khóa / SP xóa không (như GPLX_CSDT).
  - **Trường được sửa (CHANGES #37, mở rộng — chỉ TCB-03):** bản đầu (task 65) sửa 5 trường qua model chung `HoSoSua` (họ tên, ngày sinh, giới tính, CCCD, `NoiTT` dạng chữ tự do). Mở rộng thêm **địa chỉ thường trú 2 cấp** (`NoiTT_MaDVHC`/`NoiTT_MaDVQL` — chọn Tỉnh+Xã chuẩn, không chỉ dòng chữ), **ngày cấp CCCD** (`NgayCapCMT`), **nơi cấp CCCD** (`NoiCapCMT`, Sở GTVT). `usp_NguoiLX_Update` đã có sẵn các tham số này (xem `_EXEC_UPDATE` ở `hoso.py`) → chỉ mở rộng model + `dung_tham_so_update` (đang giữ nguyên các cột này từ bản ghi cũ).
  - **Tách model riêng cho TCB (user chốt 05/10):** KHÔNG mở rộng `HoSoSua` dùng chung (sẽ kéo theo form Nạp QLY-01, đã có hành vi riêng) — dựng model riêng cho sửa ở CDB đích (vd `HoSoSuaCDB` trong `sync_tracuu.py`) + hàm dựng tham số riêng `dung_tham_so_update_cdb`; Nạp giữ nguyên 5 trường. **Vẫn tái dùng `_EXEC_UPDATE`** (chuỗi SQL 24 tham số ở `hoso.py`) — chỉ hàm dựng tham số là riêng, KHÔNG chép lại SQL để tránh lệch.
  - **Bỏ trống thì GIỮ giá trị cũ (user chốt 05/10 /reviewtdd):** 3 trường mới (`NoiTT_MaDVHC`/`NoiTT_MaDVQL`, `NgayCapCMT`, `NoiCapCMT`) do body điều khiển, nhưng **operator bỏ trống ô nào → `dung_tham_so_update_cdb` fallback về `cur_row[...]`** (giữ nguyên giá trị đang có trong DB), KHÔNG ghi đè rỗng → không mất dữ liệu cũ. *(Khác 5 trường cũ vốn luôn giữ `cur_row`; nay các cột này body điều khiển nên phải định nghĩa rõ ngữ nghĩa rỗng.)* Địa chỉ 2 cấp đi theo cặp: operator chọn Tỉnh+Xã thì ghi cả cặp từ body; không đụng thì giữ cả cặp cũ.
  - **`chi-tiet-sua` (CDB) trả thêm mã hiện tại để preselect:** endpoint `chi_tiet_sua_dich` (`sync_tracuu.py`) hiện chỉ trả `ho_ten/ngay_sinh/gioi_tinh/so_cccd/noi_tt/hktt/ma_kh/dkkh` → bổ sung `NoiTT_MaDVHC`/`NoiTT_MaDVQL` (preselect Tỉnh+Xã), `NgayCapCMT` (yyyymmdd), `NoiCapCMT` (preselect Sở) để form mở lên hiện đúng giá trị đang lưu, không bắt operator nhập lại. *(Bản Nạp `hoso.py` chi-tiet-sua đã trả đủ các mã này; CDB bổ sung tương tự.)*
  - **Danh mục Tỉnh/Xã + Sở đọc từ DB ĐÍCH:** bộ chọn địa chỉ 2 cấp (`ComboLoc`/`AddressCombo`) + nơi cấp (`DM_DonViGTVT`) hiện lấy danh mục qua endpoint trỏ DB Nạp — cho TCB phải đọc `DM_DVHC`/`DM_DonViGTVT` ở **DB đích** (`sqlserver_conn_dich(db_đích)`, theo `target_key`), nếu không Xã/Sở hiện sai danh mục. *(Thêm endpoint danh mục trỏ đích, hoặc cho endpoint hiện có nhận `target_key`.)* **Đã kiểm khi code (05/10):** probe `GPLX_CDB_CSDT` qua `dvhc.ds_tinh/ds_xa/ds_so_gtvt(db)` → **đủ**: 34 tỉnh + xã mới 2025 (103 xã Cần Thơ) + 36 Sở GTVT; SP `usp_DM_DVHC_SelectDanhSachXaPhuongTheoTinh` chạy ở đích OK → danh mục đích không lệch. *(Endpoint vẫn bắt lỗi `_loi_db` nếu CDB khác thiếu danh mục.)*
  - **(CHANGES #40, 06/10 — đảo nguồn nơi cấp + mở rộng QLY-01):** "Nơi cấp căn cước" đọc/lưu theo **`DM_DVHC.MaDvhc`** (mã 2 ký tự: tỉnh TW/TI active + nhóm Cục 'C' gồm `'00'`='Cục QLHC'), **KHÔNG** `DM_DonViGTVT` (ở đó '00'=Cục CSGT/Tổng cục đường bộ — lệch nghĩa; app CSDT cũ tra `DM_DVHC` ra "Cục QLHC"). `ds_so_gtvt` đổi sang `DM_DVHC`; 3 chỗ hiển thị (`hoso.py`, `sync_tracuu.py` list+chi tiết) đổi join `DM_DVHC.TenNganGon` (scalar subquery, tránh BUG-11). `suy_noi_cap`/`suyNoiCap`: **CCCD 12 số → '00' Cục QLHC** (cấp tập trung), CMND 9 số → '' chọn tay. **Tiền đề đã chạy:** `DM_DVHC` DB nguồn trước đó mã tỉnh đều `TrangThai=0` + không có '00' → đồng bộ đích→nguồn `update/sync-DM_DVHC-tu-DB-dich-sang-DB-nap.sql` (MERGE cặp PK `(MaDvhc,MaDVQL)` + `COLLATE` cross-DB, UPDATE 15.744 + INSERT 11, **không DELETE** → không đụng 4 FK; backup `DM_DVHC_backup_20261006`). **Mở rộng sang Nạp QLY-01** (đảo #37 "giữ 5 trường"): `hoso.py` `HoSoSua`+4 trường + `dung_tham_so_update` overlay bỏ-trống-giữ-cũ (`_giu_cu`) + `chi-tiet` trả 4 mã preselect; `TraCuuDB.tsx` +combo (`/local/dvhc/*` trỏ DB Nạp). **Guard BC1 (409) GIỮ NGUYÊN** trên đường lưu `sua_ho_so`.
  - **Edge dữ liệu xã cũ (trước sáp nhập 2025):** HV mang `NoiTT_MaDVHC` mã xã CŨ không có trong danh mục 34 tỉnh mới → dropdown không preselect được, ô Tỉnh/Xã hiện **trống**. Đây là bình thường: luật "bỏ trống giữ cũ" ở trên bảo vệ — operator không đụng ô địa chỉ thì mã cũ giữ nguyên, không bị xóa.
  - **Validate:** ngày cấp CCCD ≤ hôm nay; CCCD trùng HV khác trong khóa → cảnh báo mềm, vẫn lưu (giữ như bản 5 trường).
- **Nút "Xem chi tiết HV" ở Bàn đồng bộ (SYNC-01):** HV đã có ở đích có sẵn `MaDK đích` → tra `NguoiLX_HoSo.MaKhoaHoc` theo MaDK đó → mở TraCuuCDB với khóa + tô sáng (reuse `khoaMa`/`noiBat`). Thuần thêm nút, không đổi hành vi sync.

> **Phục vụ:** TCB-01/02/03/04 · mở rộng phân hệ Đồng bộ CDB. Không chạm quyết định §12/§13/§14.

---

## 11C. Đóng gói & khởi chạy tool độc lập — DGT-01..04 (CHANGES #38)

Đóng gói tool (`tool/`) thành **một file `.exe`** chạy tại máy CSDT không cần cài Python/Node. Kiến trúc đã sẵn sàng cho việc này: frontend dùng `BASE = import.meta.env.DEV ? "http://localhost:8000" : ""` (bản production đường dẫn tương đối) → **FastAPI phục vụ luôn giao diện trên cùng origin**, hết CORS, hết cổng dev 3011 riêng.

### 11C.1 Đóng gói (DGT-01)
- **Build frontend tĩnh:** `cd tool/webui && pnpm build` → `tool/webui/dist/`.
- **FastAPI phục vụ `dist/`:** mount `StaticFiles` ở `app/main.py` cho mọi path không phải `/local/*` (SPA fallback về `index.html`). Giữ `/local/*` như cũ.
- **PyInstaller** gói `app/main.py` (one-folder khuyến nghị — khởi động nhanh hơn one-file) + **`--add-data`** kèm: `webui/dist/`, `db/data/dvhc_map.sqlite`, mọi file SQL/mẫu. Thư viện Python (fastapi, uvicorn, **pymssql**, Pillow, rembg, cryptography) gói sẵn trong exe → máy đích không cài gì. **Cân nhắc KHÔNG gói `rembg`** cho bản exe máy CSDT nếu máy đó không xóa phông ảnh — `rembg` kéo `onnxruntime` + model (~150–200MB) làm exe rất to + lần chạy đầu chậm.
- **pymssql** có phần biên dịch C (FreeTDS) — PyInstaller gói `.pyd` nhưng **bắt buộc test trên máy sạch** (gotcha hay gặp nhất).
- **Thư mục ghi:** config (`config/key.bin`), nháp (`staging.sqlite`), ảnh `_BACKUP`, ảnh tạm → ghi vào **`%APPDATA%\<tool>\`** (hoặc cạnh exe), KHÔNG vào `Program Files` (không ghi được). Hiện `config_store`/`nap` dùng đường dẫn tương đối theo `__file__` → **phải đổi gốc dữ liệu sang thư mục ghi được khi chạy dạng đóng gói** (phát hiện `sys.frozen`). **Chuyển từ bản chạy-dev sang exe KHÔNG di cư dữ liệu tự động** (config/nháp cũ ở chỗ cũ) — máy cài exe coi như thiết lập lại (vào wizard), không phải bug.

### 11C.2 Khởi chạy (DGT-02)
- **Tự mở trình duyệt:** uvicorn **bind `host=127.0.0.1`** (KHÔNG `0.0.0.0` — tránh máy khác trong LAN gọi được `/local/config|config/test|auth/login` vốn không gác token); khi sẵn sàng `webbrowser.open("http://127.0.0.1:<port>")`. Không mở được → in địa chỉ ra cửa sổ khởi động.
- **Khay hệ thống (tray):** `pystray` (hoặc tương đương) — menu "Mở giao diện" (mở lại trình duyệt) + "Thoát" (tắt uvicorn gọn). Ẩn console (`--windowed`).
- **Chống chạy 2 bản (single-instance):** dùng **named mutex / lock-file** (KHÔNG dựa vào cổng) — đã chạy thì **mở lại trình duyệt tới đúng URL bản đang chạy** (trình duyệt tự gộp về tab cũ nếu được, hoặc mở tab mới cùng địa chỉ), **không khởi động tiến trình tool thứ hai**.
- **Chọn cổng phục vụ (độc lập với single-instance):** thử cổng mặc định; bận (app khác chiếm) → dò cổng trống rồi mở trình duyệt đúng cổng đó.
- **Tự chạy khi bật máy (tùy chọn, mặc định TẮT):** shortcut trong `shell:startup` hoặc registry `Run`, bật/tắt từ trong tool. Bật kèm phiên vĩnh viễn = bật máy là vào thẳng → dựa khóa màn hình Windows làm lớp chặn (§16).

### 11C.3 Wizard thiết lập lần đầu (DGT-03)
- **3 trạng thái khởi động** (phân biệt rõ để không kẹt màn trắng): (a) **chưa có `key.bin` / config chưa đủ** → **wizard**; (b) **`key.bin` đọc được + config đủ** → chạy bình thường; (c) **`key.bin` CÓ nhưng giải mã config lỗi** (copy thiếu, hỏng đĩa) → **coi như máy sạch, vào wizard** kèm cảnh báo *"cấu hình cũ không đọc được, khai lại"*. Ca (a)(c) route vào **wizard**, không vào màn đăng nhập. `/local/config` + `/local/config/test` + `/local/auth/login` **không bị gác token** (đã có — "config là bước mồi", `main.py`) nên wizard chạy trước đăng nhập không vướng.
- **3 bước, test-before-next:** (1) kiểm môi trường — thư mục ghi được + ping VPS; (2) cấu hình SQL nguồn/đích + VPS, nút "Kiểm tra kết nối" (`/local/config/test` + `testSyncTarget` sẵn có) **phải xanh mới cho Tiếp**; (3) đăng nhập (`/local/auth/login` qua VPS), lỗi VPS → quay lại sửa URL. Tái dùng nội dung `CauHinhDrawer.tsx`, chỉ xếp lại thành stepper toàn màn.
- **Lần sau:** đã có cấu hình → bỏ wizard, vào thẳng (đăng nhập, hoặc vào luôn nếu còn phiên — §11C.4).

### 11C.4 Phiên đăng nhập vĩnh viễn (DGT-04)
- **Hiện trạng:** `session.py` giữ `Phien` trong RAM → tắt exe là mất; token client ở `localStorage` sống qua F5/đóng-mở trình duyệt (CHANGES #36).
- **Thêm:** **lưu phiên ra đĩa** (file trong thư mục ghi được), **không gắn hạn**. **Mã hóa bằng DPAPI Windows (`CryptProtectData`, phạm vi CurrentUser)** — KHÔNG dùng `key.bin` cho phiên: `key.bin` nằm cùng thư mục nên copy cả thư mục sang máy/user khác là giải mã được; DPAPI ràng phiên vào đúng tài khoản Windows + máy đó. Khởi động: **đọc phiên đĩa bọc try/except** — thiếu/ghi-dở/giải-mã-lỗi thì **bỏ qua phiên, về màn đăng nhập**, KHÔNG để exception nổi lên (console đã ẩn `--windowed`). Giải mã OK → `require_session` chấp nhận token cũ → vào thẳng.
- **⚠️ `vps_token` 8h vs phiên vĩnh viễn (CHẶN — fix cách A, /reviewtdd 05/10):** phiên local sống vĩnh viễn nhưng `vps_token` (JWT VPS hết hạn 8h — §12) nhét trong phiên sẽ chết → sau 8h / mở lại hôm sau, user vẫn "đã đăng nhập" dùng được tra cứu + sửa local **nhưng mọi call VPS (kéo/lock/đã-nạp/tải ảnh/đối soát QLY-08,09) đều 401**, tool câm lặng hỏng đúng việc nạp. **Fix cách A:** heartbeat thu-hồi-từ-xa **kiêm làm mới token** — VPS cấp *refresh token* lúc đăng nhập, tool lưu đĩa (DPAPI), heartbeat đổi lấy `access_token` mới; refresh thất bại / TK bị khóa → xóa phiên. **Đụng VPS `/api/auth` → đã qua `/capnhat` #39 (gộp vào DGT-04, user chốt 05/10).** Endpoint: **`POST /api/auth/refresh`** (VPS cấp + xoay refresh token; lưu DPAPI ở tool). Thu hồi từ xa dựa vào chính lần refresh thất bại (VPS trả lỗi khi `is_active=false`) — không cần endpoint kiểm riêng. Chi tiết lưu-hash / xoay một-lần-dùng / ân hạn race / thu hồi khi đổi mật khẩu: **§12** (soát /reviewtdd 05/10).
- **Đăng xuất** (`/local/auth/logout` → `session.dang_xuat`, nút UI đã có): xóa phiên ở **đĩa + client** → lối ra duy nhất.
- **Thu hồi từ xa:** khi có mạng, định kỳ (vd lúc khởi động + mỗi N giờ) ngầm hỏi VPS tài khoản còn hiệu lực (tái dùng đường xác thực VPS) — VPS khóa → xóa phiên, buộc đăng nhập lại. Không có mạng → vẫn vào bằng phiên đĩa, kiểm khi có mạng lại.
- **Rủi ro (chấp nhận, user 05/10):** phiên vĩnh viễn = ai ngồi vào máy cũng vào thẳng (sửa/xóa GPLX + xem căn cước). Chấp nhận vì máy nội bộ CSDT 1 người dùng — xem §16. **Chỉ áp cho tool**; đăng nhập app web (VPS, đa người) giữ phiên thường, không đổi.

### 11C.5 Sơ đồ khởi động & vòng đời phiên

```
Mở exe
  │
  ▼
Đọc key.bin + config + phiên đĩa
  │
  ├─ (a) chưa có key.bin / config chưa đủ ─────┐
  ├─ (c) key.bin có NHƯNG giải mã config lỗi ──┤──▶ WIZARD (DGT-03)
  │                                             │   môi trường → cấu hình(test xanh)
  │                                             │   → đăng nhập
  │                                             └────────────┬───────────────
  │                                                          │
  └─ (b) key.bin OK + config đủ                              │
        │                                                    │
        ▼                                                    │
     Có phiên đĩa hợp lệ?                                    │
        ├─ không / file hỏng / giải mã lỗi ──▶ Màn ĐĂNG NHẬP ┤
        │                                                    │
        └─ có ──────────────────▶ VÀO THẲNG                  │
                                       │                     │
                                       ▼                     ▼
                              ┌──────────────────────────────────┐
                              │      PHIÊN ĐANG HOẠT ĐỘNG         │
                              └───────────────┬──────────────────┘
                                              │
            ┌─────────────────────────────────┼────────────────────────────┐
            ▼ heartbeat (khi có mạng)          ▼ vps_token sắp hết (cách A)  ▼ Đăng xuất
     VPS báo TK bị khóa                   đổi refresh-token                (nút duy nhất)
            │                             lấy access_token mới                   │
            ▼                                    │                               ▼
     Xóa phiên đĩa + client ◀────────────────────┘ (thất bại/bị khóa)  Xóa phiên đĩa + client
            │                                                                    │
            └──────────────────────────▶ lần sau: Màn ĐĂNG NHẬP ◀────────────────┘
```

> **Phục vụ:** DGT-01/02/03/04. Không chạm nghiệp vụ Nạp/Sync/TCB — thuần đóng gói + khởi chạy + vòng đời phiên của tool. Quyết định kỹ thuật: TDD-decisions §16.

---

## 12. Security

| Nhóm | Cơ chế |
|---|---|
| Xác thực | bcrypt password; JWT HS256 expire 8h; đọc `is_active`+vai trò từ DB mỗi request; logout qua blocklist `jti`; API key tool (cân nhắc **key riêng mỗi máy** nếu cần thu hồi độc lập); đăng nhập riêng, không dùng chung (SOD-002); **refresh token cho phiên tool vĩnh viễn (DGT-04, CHANGES #39):** VPS cấp refresh token lúc login (tool lưu **DPAPI**), endpoint `POST /api/auth/refresh` đổi lấy `access_token` mới. **Lưu HASH ở DB** (bảng `refresh_token(user_id, token_hash, created_at, last_used_at, revoked)`), KHÔNG plaintext (bí mật sống vĩnh viễn — lộ DB plaintext = chiếm phiên mọi tài khoản). **Xoay một-lần-dùng:** mỗi refresh trả access_token + refresh token MỚI, vô hiệu cái cũ; **không TTL lịch** (phục vụ "vĩnh viễn") nhưng revoke được. **Chống đá nhầm khi mạng chập chờn** (máy CSDT): cửa sổ ân hạn ngắn cho refresh cũ, HOẶC chỉ coi là replay khi refresh cũ dùng lại SAU khi token mới đã dùng thành công. **Thu hồi:** `logout` xóa refresh token của phiên (ngoài blocklist access `jti`); `doi-mat-khau` thu hồi TOÀN BỘ refresh token của user; `is_active=false` → refresh fail. Chỉ cấp refresh cho đăng nhập **qua tool**; app web giữ phiên thường |
| Dữ liệu (PII) | HTTPS toàn bộ; ảnh thô + CCCD tự xóa 30 ngày; không log nội dung CCCD; SQL login riêng (không `sa`); validate ảnh upload (§7.4) |
| API | Chặn quyền theo vai trò (403); chống IDOR bằng **kiểm sở hữu `created_by`** (UUID chỉ là định danh); validate input (pydantic); nạp DB chỉ ở tool; `/local/*` buộc token operator (không mở trống localhost) |
| DB đích | Ghi nhân thân/kết quả **qua SP**; **UPDATE trực tiếp cột ảnh** (`ChatLuongAnh`/`NgayThuNhanAnh` — SP không ghi ảnh, giống bên Nạp) và **mọi SQL động (MAX SoHoSo, tra `DM_DVHC_MAP` theo text địa chỉ, tra cứu TCB) phải parameterized** — không nối chuỗi; login hạn chế EXECUTE + SELECT danh mục |

---

## 13. Non-Functional Requirements

*Vì sao ngưỡng vừa phải: nội bộ 1 CSDT, không SLA gắt.*

- **Performance:** app web thao tác <2s; API VPS <500ms p95; xóa phông + xuất .jp2 <5s/ảnh; nạp 1 HV <2s.
- **Scale:** ~10 collector đồng thời, 1–2 tool, đầu khóa ~60 bản ghi/đợt.
- **Uptime:** VPS ~99%; backup PostgreSQL `pg_dump` hằng ngày; DB đích do app cũ backup (`DUONG_DAN_SAO_LUU_CSDL`).

---

## 14. Testing Strategy

### 14.1 Unit (pytest)
```
server/tests/  auth_test, hoso_queue_test (lock/idempotent), pii_job_test
tool/tests/    sohoso_test (MAX+1 3 số), import_sp_test (mock pymssql thứ tự SP),
               image_jp2_test (3:4, nền trắng, size), dvhc_map_test (chuẩn hóa + nối tên)
webapp/        qr_parse_test (6/7 trường, ddMMyyyy→yyyymmdd)
```

### 14.2 Integration
- App web gửi → VPS pending → tool kéo → lock → nạp (SQL Server test/staging) → da_nap.
- Idempotent: gửi lại cùng uuid → 1 bản ghi.

### 14.3 Manual checklist
```
□ Quét QR thẻ thật (AS-001) → 7 trường đúng
□ Nạp 1 HV thật → mở app cũ khớp trường + ảnh + giấy tờ (AS-003)
□ Địa chỉ cũ → map ra xã mới đúng; xã chia → chọn tay
□ Ảnh: crop 3:4 grab + xóa phông trắng + .jp2 mở được app cũ
□ Hai tool cùng nạp 1 bản ghi → chỉ 1 HV
□ Bấm Nạp 2 lần → 1 HV
□ Trùng CCCD trong khóa → cảnh báo chặn
□ Tạo khóa mô tô + ô tô → hiện trong app cũ
□ collector gọi API nạp → 403
□ Bản ghi 30 ngày → job xóa (bỏ qua importing)
```

---

## 15. Environment Variables

```bash
# ── Backend VPS ──
APP_DOMAIN=https://<domain>
DATABASE_URL=postgresql://user:password@localhost:5432/thunhan_db
JWT_SECRET=<random-32-char>
ANH_THO_DIR=/data/anh-tho
PII_RETENTION_DAYS=30
TOOL_API_KEY=<random-key-cho-tool>          # tool gửi qua X-Tool-Key

# ── Tool máy DB (config cục bộ, mã hóa, KHÔNG commit) ──
SQLSERVER_HOST=DESKTOP-UBV2GQI
SQLSERVER_DB=GPLX_CSDT
SQLSERVER_USER=<login-rieng>                 # KHÔNG dùng sa
SQLSERVER_PASSWORD=<...>
VPS_API_URL=https://<domain>/api
VPS_TOOL_KEY=<random-key-cho-tool>
```
> Chỉ tên biến + giá trị mẫu. Không chép giá trị thật vào tài liệu (file này commit Git).

---

## 16. Risks & Trade-offs

### 16.1 Rủi ro
| Rủi ro | Xác suất | Impact | Mitigation |
|---|---|---|---|
| QR CCCD cơ sở khác định dạng chuẩn | Thấp | Cao | Đã xác nhận 6/7 trường (webThanhdat); test thẻ thật (AS-001) |
| Nạp ra bản ghi không khớp app cũ | Thấp | Cao | Nạp thử 1 HV đối chiếu (AS-003) trước khi mở rộng |
| Nạp trùng do đồng thời | Trung bình | Cao | Khóa `importing` (CAS) + idempotent UUID + transaction |
| Xã chia không map được | Trung bình | Trung bình | Fallback chọn tay từ DM_DVHC |
| rembg xóa phông xấu | Trung bình | Trung bình | Cho giữ ảnh gốc/chỉnh tay |
| Lộ PII trên VPS | Thấp | Cao | HTTPS + auth + xóa 30 ngày + không log CCCD |
| Tool dùng `sa` | — | Cao | Tạo SQL login riêng (OG-004) |
| Đồng hồ máy DB sai giờ | Thấp | Trung bình | So giờ trước go-live (MaDK/tên file theo timestamp) |
| **Phiên tool vĩnh viễn → ai ngồi vào máy cũng vào thẳng** (DGT-04) | Trung bình | Cao | **Chấp nhận** (user 05/10): máy nội bộ CSDT 1 người dùng. Giảm nhẹ: nút Đăng xuất + thu hồi từ xa (VPS khóa tài khoản → đá ra); **tự-chạy-khi-bật-máy mặc định TẮT** (bật = bật máy vào thẳng, dựa khóa màn hình Windows); **phiên đĩa mã hóa DPAPI** (copy sang máy/user khác không giải mã). Nếu máy thành dùng chung → thêm "hỏi mật khẩu khi xóa/đổi khóa" (để sau) |
| **DGT-04 `vps_token` 8h vs phiên vĩnh viễn** → nạp từ VPS chết lặng sau 8h | Cao | Cao | Fix cách A (đã `/capnhat` #39, gộp DGT-04): heartbeat kiêm refresh-token qua `POST /api/auth/refresh` — refresh fail/TK khóa → đăng xuất |
| **exe đóng gói chạy sai trên máy sạch** (pymssql/FreeTDS, đường dẫn ghi) | Trung bình | Cao | Test trên máy sạch trước go-live; ghi dữ liệu vào `%APPDATA%`; kèm hướng dẫn SmartScreen / ký số |

### 16.2 Trade-offs đã quyết
**Ghi DB chỉ qua SP (không ORM):** ✅ khớp app cũ, an toàn ❌ không tự sinh/migrate schema (chấp nhận — DB có sẵn).
**Phiên tool vĩnh viễn (DGT-04):** ✅ đăng nhập 1 lần dùng mãi, hợp ca làm hằng ngày ❌ mất lớp khóa đăng nhập khi máy bị người khác tiếp cận (chấp nhận — máy nội bộ 1 người; có thu hồi từ xa làm lưới).
**Đóng gói PyInstaller (DGT-01):** ✅ máy đích không cài Python/Node, mở như phần mềm thường ❌ exe to, phải test trên máy sạch, SmartScreen cảnh báo nếu chưa ký số.
**Tool pull ra VPS:** ✅ máy DB sau NAT vẫn chạy, không mở cổng ❌ không realtime (đủ cho nhịp đợt).
**DM_DVHC_MAP trong DB đích:** ✅ cập nhật một chỗ ❌ thêm 1 bảng trong production (chỉ đọc từ tool).
**Ảnh thô filesystem VPS:** ✅ đơn giản, rẻ ❌ phải xóa cả file lẫn dòng khi dọn PII.

> **Ghi chú đối chiếu PRD (review TDD 30/09/2026):** PRD ⑦/NAP-05/EC-061 dùng chữ *"transaction, rollback"*; thực tế mỗi `usp_*` tự commit nên TDD dùng **compensation (bù trừ) + `sp_getapplock`** cho tính toàn vẹn — hiệu quả cam kết tương đương (không HV nửa vời, không trùng SoHoSo, giữ pending). Nên cập nhật câu chữ PRD cho khớp qua `/capnhat` (không đổi hành vi).

---

## 17. Implementation Plan

### Phase 0 — Kiểm giả định Nền móng (trước khi code)
- [ ] Quét QR vài thẻ CCCD thật của cơ sở (AS-001)
- [ ] Tạo SQL login riêng cho tool; nạp thử 1 HV → mở app cũ đối chiếu (AS-003)
- [ ] Dựng bảng `DM_DVHC_MAP` + nạp dataset + đối soát 3321/3321

### Phase 1 — Tool nạp DB (mắt xích khó nhất)
- [ ] Kết nối SQL Server (pymssql, login riêng), đọc config QTHT_ThamSoHT
- [ ] Chọn khóa (lọc BC1) + sinh SoHoSo + gọi 3 SP + giấy tờ (nạp thủ công 1 HV)
- [ ] Xử lý ảnh: crop 3:4 grab + rembg nền trắng + xuất .jp2 + ghi path
- [ ] Map địa chỉ (DM_DVHC_MAP + chọn tay)

### Phase 2 — Backend VPS
- [ ] Auth (JWT, 3 vai trò) + seed admin
- [ ] Hàng đợi ho_so_thu_thap + lock importing + idempotent + upload ảnh thô
- [ ] API kéo/đánh dấu cho tool; APScheduler job xóa PII 30 ngày
- [ ] Tool chuyển từ nhập tay sang kéo từ VPS

### Phase 3 — App web (PWA)
- [ ] Đăng nhập + mobile-first UI (shadcn)
- [ ] Quét QR (BarcodeDetector→ZXing) + preview sửa + chụp ảnh + gửi
- [ ] Nhập tay + upload ảnh CCCD fallback

### Phase 4 — Quản lý + hoàn thiện
- [ ] Tra cứu/sửa/đổi khóa/xóa HV; tạo khóa học
- [ ] Bộ lọc + xóa PII thủ công (admin)
- [ ] Đóng gói tool PyInstaller + đối chiếu bảo mật (OG chặn go-live)

---

## Changelog

| Ngày | Version | Thay đổi |
|---|---|---|
| 06/10/2026 | 4.4 | **Nơi cấp căn cước = Cục QLHC '00' từ `DM_DVHC`** (CHANGES #40, §11B.7): đổi nguồn nơi cấp `DM_DonViGTVT`→`DM_DVHC.MaDvhc` (có '00' Cục QLHC) ở `ds_so_gtvt` + 3 hiển thị; CCCD 12 số mặc định '00'. **Tiền đề đã chạy:** đồng bộ `DM_DVHC` đích→nguồn (MERGE, backup). **Mở rộng Nạp QLY-01** +combo địa chỉ 2 cấp + nơi cấp + ngày cấp CCCD (đảo #37 "giữ 5 trường"), guard BC1 giữ nguyên. Cần /reviewtdd §11B.7. |
| 04/10/2026 | 3.4 | QLY-09 task 48 (CHANGES #28, hướng A khi code): §11.8 — "hỏi trạng thái VPS" hiện thực bằng **endpoint READ server mới** `GET /api/nap/trang-thai?uuids=` (operator, batch, ca ②) + `GET /api/admin/ho-so` trả thêm `ma_dk`/`locked_at` (ca ①③). Tool `doisoat.py` (2 panel + 3 action) + phòng tuyến 2 `nap_fn` bỏ `da_nap` khi `trung_uuid` (không sửa `nap_mot_hv`). ⚠ Đổi server → cần deploy VPS. |
| 04/10/2026 | 3.3 | Sửa sau review TDD #32 (biên bản `tdd-review-04-10-2026.md`): §9.3a +endpoint list NHẸ `GET /local/nap/nhap?uuids=` (cờ `co_dia_chi`/`co_anh`/`co_tick` vẽ chip, không tải ảnh base64 cả khóa — Điểm 5) + nút "Xóa nháp" chủ động & ghi rõ giới hạn PII nháp bỏ dở (Điểm 4) + luật ghép địa chỉ hiển thị `join(", ")` ở lớp tool (xác minh DB: không SP ghép, `TenDayDu` đã có phẩy) + sơ đồ vòng đời nháp; §10.5 chip đọc cờ nhẹ + drawer có nút Xóa nháp; TDD-decisions §11 thu hẹp cam kết tự-xóa (nháp bỏ dở tồn tại tới khi operator tự dọn). |
| 04/10/2026 | 3.2 | Lưu nháp chuẩn bị BỀN + bổ sung ảnh 2 nguồn (CHANGES #32, NAP-01/QLY-05): §9.3a mới — nháp (địa chỉ+chi tiết+nơi cấp+tick+ảnh) lưu bảng `nhap_chuan_bi` trong `staging.sqlite`, tự xóa khi nạp/bỏ hàng đợi/xóa VPS, reset địa chỉ nháp ở backend khi `keo_ve_upsert` thấy `noi_tt_raw` đổi (BUG-04); §10.5 thêm 2 chip Địa chỉ/Ảnh + nút "Xử lý" to + cả dòng bấm + nạp chặn thiếu địa chỉ/cảnh báo thiếu ảnh; §11.5 bổ sung ảnh cho HV thiếu ảnh từ file (`chonFile`) hoặc ảnh thô VPS (`tra_uuid`→`tai_anh`→`napTuUrl`). TDD-decisions §11 mới (lưu ảnh nháp bền — đánh đổi PII). |
| 03/10/2026 | 3.1 | Sửa §11.8 sau review TDD (biên bản `tdd-review-03-10-2026-qly09.md`): tách đối soát làm **2 chế độ** — ① theo khóa (ca ②, neo CSDT) · ② quét lạc toàn hệ (ca ①+③, neo VPS, tái dùng `GET /api/admin/ho-so`). Lý do: bản ghi VPS không có cột khóa nên phantom (ca ①) và importing treo (ca ③) không quy được về khóa. Làm rõ cách nối `nap_xong`/`tra-uuid` + ứng xử khi thiếu nối. |
| 03/10/2026 | 3.0 | Đối soát & đồng bộ VPS↔CSDT (CHANGES #28, QLY-09 — sau ca Lê Thị Hồng/BUG-01): §11.8 mới — panel admin/operator đối soát **theo khóa** phát hiện 3 ca lệch (① VPS imported & CSDT không có MaDK = phantom → Trả về chờ nạp; ② CSDT có HV & VPS chưa imported → Đánh dấu đã nạp; ③ importing treo quá ngưỡng → Mở khóa), tái dùng `tra_ve_cho_nap`/`da_nap`/`unlock` — KHÔNG endpoint/SP nạp mới. +Phòng tuyến 2: `nap_fn` bỏ `da_nap` khi `_nap_mot` trả vé cũ (chặn tái phát phantom). Thuần tool. |
| 03/10/2026 | 2.9 | Chốt nghiệp vụ + UX #24 (CHANGES #26): §7.5 mới — nguyên tắc "Nạp = điểm bàn giao quyền sở hữu" (trước nạp app web làm chủ, sau nạp tool/CSDT làm chủ, app web đóng băng) + bảng edge khóa chưa BC1 + phân biệt QLY-03 "Xóa hẳn" ≠ QLY-08 "Gỡ về chờ nạp"; §7.2 lock trả bản tươi; §9.1 +prop `anhGoc` + nút "Dùng lại ảnh gốc" (NAP-04 ảnh thô VPS / QLY-05 ảnh DB); §10.5 mới — redesign màn Nạp lô (trạng thái sẵn sàng mỗi dòng, chọn-tất-cả-sẵn-sàng, drawer Chuẩn bị, dialog nạp 3 pha, nút Xem trong DB). Thuần client phần UX, không endpoint mới. |
| 03/10/2026 | 2.8 | Sửa sau review TDD #24 (biên bản `tdd-review-03-10-2026.md`): §11.7 "đồng bộ xóa khi kéo" bỏ cách suy-từ-vắng-mặt-trong-`keo` (xóa nhầm khi dòng bị khóa/rớt limit) → chốt `GET /api/nap/da-xoa?since=` (thêm §4.4); §4.4 +`GET /api/nap/tra-uuid?ma_dk=` cho fallback QLY-08 bước 2; §4.3/§4.4 +quy tắc CAS nguyên tử (`DELETE … WHERE trang_thai='pending'`, `tra-ve-cho-nap … WHERE 'imported'`, idempotent khi retry); §4.3 soft-delete ghi mốc vào `audit_log.created_at` (không cột mới); §11.7 +sơ đồ ASCII luồng xóa-CSDT-trước-rồi-VPS + nhánh bù. (Ghi nhận: PRD gọi `done`, DB/TDD là `imported` → xử bằng `/capnhat`.) |
| 02/10/2026 | 2.7 | Gỡ HV về chờ nạp + đồng bộ xóa (CHANGES #24): §4.3 +`DELETE /api/ho-so/:uuid` (soft-delete, chỉ pending, phân quyền — THU-05); §4.4 +`POST /api/nap/:uuid/tra-ve-cho-nap` (imported→pending — QLY-08); §7.1 +2 chuyển trạng thái (imported→pending gỡ về; collector xóa pending→deleted); §11.7 mới (gỡ HV về chờ nạp + kéo về đồng bộ bỏ dòng đã xóa); §6 +nút Xóa app web. Dùng lại trạng thái `deleted` + `audit_log` sẵn có, không bảng mới. NAP-01 hạ ⏳; +story QLY-08, THU-05. |
| 02/10/2026 | 2.6 | UX giữ ảnh đã chỉnh để xem lại/chỉnh tiếp (CHANGES #23): §9.1 client lưu thêm bản `preview` PNG cạnh `jp2` trong nháp → khung ảnh hiện ảnh đã chỉnh (`.jp2` không render trực tiếp) + mở lại trình chỉnh nạp sẵn ảnh đã chỉnh gần nhất; nút áp dụng nổi bật. Thuần client, không đổi endpoint. NAP-04/QLY-05 hạ ⏳; QLY-06 đổi nhãn nút → ⏳. |
| 02/10/2026 | 2.5 | Sau review TDD (CHANGES #22, biên bản `tdd-review-02-10-2026.md`): §11.5 `TT_XuLy` đổi sang quy tắc **"không bao giờ HẠ"** (whitelist `'01'/'02'`, bỏ ngưỡng `< '11'`) + ghi ảnh atomic + click sửa ảnh file-mất fallback + **sơ đồ vòng đời `TT_XuLy`**; §11.3 +**sơ đồ liên kết HV↔Báo cáo**; §11.6 `_BACKUP` chỉ-nếu-chưa-có + heuristic phát hiện ảnh-trắng (4 góc) + applock bulk; §11.1 avatar file-mất→icon ảnh-vỡ + transcode lỗi→422 + cache PII cục bộ + lazy-load; §4.6 +4 endpoint; §10.4 +"nạp lại nhanh". |
| 02/10/2026 | 2.4 | Mở rộng quản lý ảnh + bảo toàn Báo cáo 1/2 (CHANGES #22): §11.1 +endpoint phục vụ ảnh `.jp2`→PNG + thumbnail/avatar + kiểm file tồn tại + thống kê đầu khóa; §11.3 chặn xóa HV khóa BC1 ở BACKEND (FK `MaBC1`/`MaBC2` → `BaoCaoI`/`BaoCaoII`); §11.5 🐛 giữ `TT_XuLy` khi HV đã Báo cáo (`'11'`–`'19'`) tránh rơi khỏi `usp_BaoCao2_DSHS` + mở trình chỉnh ảnh từ Tra cứu DB; §11.6 mới QLY-07 đổi nền cả khóa (chạy nền + `_BACKUP` + giữ `TT_XuLy`); §7.2 "Bỏ khỏi hàng đợi" staging. QLY-01/QLY-03/QLY-05 + NAP-01 hạ ⏳. |
| 01/10/2026 | 2.1 | Sửa UX app web sau test điện thoại (CHANGES #12): §4.3 thêm `GET /api/ho-so/:uuid/anh` (collector tải ảnh của mình); §6.5 mới (màn vào không tự mở camera, khung bám QR `cornerPoints`, layout `100dvh` dính đáy, xem/sửa/chụp lại hồ sơ chờ nạp). THU-01/THU-02 hạ ⏳. |
| 01/10/2026 | 2.2 | App web nhập liên tiếp (CHANGES #13): §6.1 +nhánh preview "Lưu & nhập hồ sơ tiếp" (gửi không ảnh→toast→màn chọn); §6.6 mới (badge/bộ lọc "Thiếu ảnh" + cảnh báo trùng); §4.3 +`GET /api/ho-so/kiem-trung` (THU-04 soi hàng đợi, cảnh báo mềm). THU-01/THU-02 hạ ⏳. |
| 01/10/2026 | 2.0 | §7.2 ghi rõ **kéo KHÔNG khóa** (bản ghi còn sửa ở app web tới lúc nạp) → tool **kéo lại làm tươi** bản `keo_ve` trạng thái `cho` (NAP-01, CHANGES #11); không khóa-khi-kéo để tránh kẹt + job 15' lật ngược. |
| 01/10/2026 | 1.8 | §3.2 bổ sung bảng `token_blocklist` (+ index `idx_blocklist_exp`) — §5.1 đã mô tả logout ghi jti vào blocklist nhưng schema §3.2 ghi sót; đồng bộ khi làm task 14 (HTG-01②). Xem CHANGES.md #7. |
| 30/09/2026 | 1.0 | TDD đầu tiên — thiết kế đầy đủ từ PRD v2 (chế độ phỏng vấn 3 câu + PRD) |
| 30/09/2026 | 1.2 | Verify DB thật: `TT_XuLy` phụ thuộc ảnh (có ảnh→`03`, chưa ảnh→`01`), `ChatLuongAnh`=1/NULL theo ảnh; `TrangThai`=1 không đổi theo ảnh (§10.2). |
| 30/09/2026 | 1.1 | Sửa sau review TDD: chống trùng SoHoSo bằng `sp_getapplock` (§10); dọn `NguoiLX` mồ côi; tách họ tên + validate độ dài cột; màn Cấu hình + endpoint `/local/config*`; kiểm `is_active`/vai trò mỗi request + blocklist logout; IDOR theo `created_by`; validate ảnh upload; bỏ `duplicate` khỏi enum; timeout khóa 15'; sửa chuẩn hóa tiền tố DVHC; rembg warm-up; +3 sơ đồ (sequence, ma trận quyền, state machine); +index; +ghi chú bảo mật |
| 01/10/2026 | 1.3 | Đổi nơi lưu `DM_DVHC_MAP`: GPLX_CSDT → **SQLite cục bộ tool** (tool tự dựng từ dataset đóng kèm + đọc `DM_DVHC` máy đích); production chỉ ĐỌC; tool mang đi cài máy khác không phụ thuộc máy hiện tại. §3.3, §8.2, sơ đồ §2.1, TDD-decisions §5. Xem CHANGES.md #1. |
| 01/10/2026 | 1.4 | **Đổi đường nạp HV: 3 SP rời → 1 SP gộp app cũ** `usp_QuangLA_PM4_ThuNhanHS_ThemMoiCapNhat` (§10.1, §10.1b, §10.2 field map, §10.3 bỏ compensation thủ công; TDD-decisions §10). AS-003 (nạp thử HV thật) phát hiện 3 SP rời lệch app cũ 5 field (IN HOA, địa chỉ mã+chi tiết, `DonViHocLX` NULL, `CHON_IN_GPLX`=2, `MaQuocTich`=VNM). Xem CHANGES.md #4. |
| 01/10/2026 | 1.7 | UX màn nạp (CHANGES #6): §11.1 QLY-01 thêm "tìm khóa mọi khóa kể cả BC1" (chế độ Tra cứu DB); §10.4 thêm hiển thị IN HOA khi kéo + check chính tả mức A + nạp lô badge ⚪🔴🟢. |
| 01/10/2026 | 1.6 | Thêm §11.5 Nạp/thay ảnh cho HV đã có (QLY-05) — dùng lại hướng A §10.3, làm sau NAP-05. Xem CHANGES.md #5. |
| 01/10/2026 | 1.5 | Sửa sau review TDD (đọc thân SP + verify DB thật): **SP không ghi ảnh** → thêm bước UPDATE 5 cột ảnh (hướng A) nâng `TT_XuLy` `01`→`03`, chưa ảnh giữ `01` (§10.1, §10.1b, §10.3); chốt `@p_MaDK=NULL`→SP sinh (OUTPUT), `SoHoSo` caller truyền, SP tự tách họ tên; xử lý mã lỗi `@p_out` (-1..-4, SP không raiserror) + `SET XACT_ABORT ON`; sửa `GiayCNSK` (theo giấy 3) + `MaLoaiHs` (thêm case 3) + tên tham số `IMG_PATH_CSDT`. Biên bản `docs/tdd-review-01-10-2026.md`. |
| 01/10/2026 | 1.9 | Xác thực tool cho `/local/*` (task 17, HTG-01③): thêm §5.5 + TDD-decisions §4a — option A (tool gọi VPS `/api/auth/login` thay mặt → phát session cục bộ; collector 403), A1 miễn token `/local/config*` + `/local/auth/*`; §4.2/§4.6 thêm endpoint `/local/auth/*`. Còn mở: 1 hay n phiên. Xem CHANGES.md #8. |
| 02/10/2026 | 2.0 | Quản lý tài khoản app web (HTG-04/05/06): §4.2 thêm `POST /api/auth/doi-mat-khau`, `GET|POST|PUT /api/admin/users*`, `POST /api/admin/users/:id/reset-mat-khau`, `GET /api/admin/tool-key` + ghi chú bảo mật (chỉ admin, băm bcrypt, không log secret, khóa bằng `is_active` không xóa cứng, chặn admin tự khóa). +5 sửa UI khung (header cố định, khung cao ổn định, phân trang 20/trang, tool master–detail panel ảnh ghim, fix kính lúp đè chữ bằng `@layer components`). Xem CHANGES.md #18. |
| 02/10/2026 | 2.1 | Tận dụng dữ liệu kéo-về (CHANGES #19): §8.1 thêm bước tự tách `noi_tt_raw` → điền sẵn ô map (NAP-03); §9.1 nạp thẳng ảnh thô VPS vào trình chỉnh, AnhModal nhận ảnh khởi tạo tùy chọn (NAP-04). |
| 02/10/2026 | 2.2 | Nâng cấp trình chỉnh ảnh (CHANGES #20): §9.1 thêm xoay ảnh (−90°/+90° + tinh chỉnh độ nghiêng, xoay client-side trước khi crop) + khung chân dung mẫu overlay (không dính ảnh xuất); §9.2 ghi rõ `tool-start.bat` KHÔNG đặt `TOOL_SKIP_WARMUP=1` (warm-up để ảnh sau nhanh, giữ model u2net — phương án A). |
| 02/10/2026 | 2.3 | Zoom trình chỉnh ảnh (CHANGES #21): §9.1 thang zoom mũ (3^t, t∈[−1,1], giữa=cỡ gốc) cho thu nhỏ dưới 1× + lăn chuột; grab tự do 4 hướng (nới clamp giữ ≥1/4 ảnh). |
| 03/10/2026 | 3.1 | Redesign giao diện DESKTOP (CHANGES #30; đổi từ v3.0 vì QLY-09 đã dùng 3.0 khi gộp 2 phiên): §6.5 desktop vào thẳng form nhập tay + Quét QR/Tải ảnh thu nhỏ góc phải + popover camera prefill (THU-01, mobile giữ camera-first); §6.6 desktop chọn-nhiều-để-xóa ở "Hồ sơ đã gửi" (THU-05, lặp DELETE client như QuanTriHoSo, mobile giữ xóa lẻ). Thuần client, KHÔNG đổi Data Model/API/endpoint. |
| 04/10/2026 | 3.2 | +§11B **Đồng bộ CDB** (CHANGES #33, SYNC-01/02/03): kiến trúc module + sidebar trái (mở rộng N, dự kiến module #3), `sqlserver_conn_dich()` nhiều DB đích, luồng sync 1 HV + MaDK batch + guard race, SSE tiến trình, rollback dual-mode, 3 nợ kỹ thuật port từ sync_tool. +§2.4 module sync. **Tool chỉ desktop**: sidebar thu gọn + nội dung ≥1280px + bảng sync cuộn ngang. |
| 04/10/2026 | 3.3 | Cấu hình lên header (CHANGES #34, HTG-07): §5.0 + §11B.0 — bỏ route `/tool/cau-hinh` + `/sync/db-dich` khỏi sub-nav, gộp thành **panel ⚙ trên header dùng chung** (khối ① kết nối + DB nguồn Nạp · khối ② nhiều DB đích Sync, tách bạch). Thuần UI/IA — backend `/local/config*` + `/local/sync/targets` + config-store không đổi; không chạm quyết định §12/§13/§14. |
| 05/10/2026 | 4.3 | **/reviewtdd (hẹp) refresh-token §12**: làm cứng — lưu **HASH** ở DB (bảng `refresh_token`, không plaintext — Chặn 4.1); **xoay một-lần-dùng** + không TTL lịch; **cửa sổ ân hạn** chống đá nhầm khi mạng chập chờn (edge 3.1); `logout` xóa refresh token + **`doi-mat-khau` thu hồi toàn bộ** refresh token (4.2). Biên bản: docs/tdd-review-05-10-2026.md. |
| 05/10/2026 | 4.2 | **/capnhat #39 — refresh-token VPS cho DGT-04**: §12 (Xác thực) +cơ chế refresh token (`POST /api/auth/refresh`, lưu DPAPI, thu hồi khi Đăng xuất/khóa TK); §11C.4 + §16 cập nhật "đã /capnhat" (gỡ cờ chờ). Gộp vào DGT-04, không thêm story. |
| 05/10/2026 | 4.1 | **sửa sau /reviewtdd #38 (DGT)**: §11C.4 phiên đĩa mã hóa **DPAPI** + bọc try/except + **fix Chặn `vps_token` 8h bằng refresh-token (cần /capnhat)**; §11C.3 phân biệt 3 trạng thái khởi động (key.bin hỏng→wizard); §11C.2 tách single-instance (mutex) khỏi chọn cổng + bind `127.0.0.1` + sửa câu "đưa tab cũ lên"; §11C.1 ghi chú không di cư dev→exe + cân nhắc bỏ rembg; **+§11C.5 sơ đồ khởi động/vòng đời phiên**; +2 dòng Risks §16. Biên bản: docs/tdd-review-05-10-2026.md. |
| 05/10/2026 | 4.0 | **+§11C Đóng gói & khởi chạy tool** (CHANGES #38, DGT-01..04): đóng gói exe PyInstaller + FastAPI phục vụ `webui/dist` cùng cổng (BASE="" sẵn có) + ghi dữ liệu vào `%APPDATA%` khi `sys.frozen`; tự mở trình duyệt + khay hệ thống + chống chạy 2 bản + tự chạy khi bật máy; wizard thiết lập lần đầu (tái dùng `/config/test` + `CauHinhDrawer`); **phiên vĩnh viễn** (lưu đĩa mã hóa `key.bin` + thu hồi từ xa, chỉ áp tool). +2 rủi ro §16 (phiên vĩnh viễn, exe máy sạch). Quyết định: TDD-decisions §16. |
| 05/10/2026 | 3.9 | Sửa sau /reviewtdd §11B.7 (biên bản `tdd-review-05-10-2026-tcb37.md`, phạm vi #37): +`chi-tiet-sua` (CDB) trả thêm `NoiTT_MaDVHC/MaDVQL/NgayCapCMT/NoiCapCMT` để preselect form; **luật bỏ-trống-giữ-cũ** cho 3 trường mới (fallback `cur_row`, không ghi đè rỗng) + tách `dung_tham_so_update_cdb` nhưng vẫn tái dùng `_EXEC_UPDATE`; +edge xã cũ trước sáp nhập (preselect trống là bình thường); +kiểm CDB có đủ `DM_DVHC` mới/SP xã/`DM_DonViGTVT`. 0 Chặn · 3 Nên sửa · 1 Ghi nhận. |
| 05/10/2026 | 3.8 | **Mở rộng trường sửa nhân thân TCB-03** (CHANGES #37): §11B.7 — thêm địa chỉ thường trú 2 cấp (`NoiTT_MaDVHC`/`MaDVQL`) + ngày cấp CCCD (`NgayCapCMT`) + nơi cấp CCCD (`NoiCapCMT`); **tách model riêng cho CDB** (không mở rộng `HoSoSua` dùng chung — Nạp QLY-01 giữ 5 trường, user chốt); danh mục Tỉnh/Xã + Sở phải đọc từ **DB đích** (`target_key`). `usp_NguoiLX_Update` đã nhận sẵn các tham số. |
| 05/10/2026 | 3.7 | Sửa sau review (biên bản `tdd-review-05-10-2026.md`, phạm vi vùng sửa #36): §11B.2 làm rõ filter khi **chưa chọn khóa nguồn** (bỏ lọc hạng) + ghi hành vi **tự kiểm kết nối khi vào màn**; §5.5 thêm **sơ đồ khôi phục phiên F5** + edge **localStorage bị chặn → fallback bộ nhớ**. 0 phát hiện Chặn; đều là bổ sung/làm rõ tài liệu (code đã đúng). |
| 05/10/2026 | 3.6 | **Sửa định nghĩa DKKH** (CHANGES #36): §11B.7 "đã kết xuất DKKH" = có gói `DANG_KY_KHOA_HOC` gửi Sở (`TRANS_CLI_HangDoiGui`, helper `sync_helpers.dkkh_exists_sql`), **KHÔNG** phải `SoQD_KhaiGiang` (sai — mọi khóa đều có) → sửa ma trận quyết định + ghi chú TCB-03; §11B.2 +filter khóa đích "cùng hạng & chưa DKKH" (mặc định bật) + khóa xếp mới-nhất-trước (ORDER BY NgayKG DESC, MaKH DESC + cờ `dkkh`); §5.5 +giữ token client qua F5 (localStorage + `/local/auth/me`). Chi tiết DB: `docs/DB-GPLX_CDB_CSDT.md` §7. |
| 04/10/2026 | 3.5 | Sửa §11B.7 sau /reviewtdd (biên bản `tdd-review-04-10-2026-tcb.md`): mốc "đã BC1" = **`NguoiLX_HoSo.MaBC1` có giá trị** (đúng cái FK NO_ACTION chặn — bỏ `TT_XuLy≥'05'` & dòng BaoCaoI cấp khóa, Điểm 2) + vẫn bắt lỗi FK làm lưới; thay ảnh TCB-02 **sao lưu `_BACKUP.jp2` cùng thư mục trước khi ghi đè** (Điểm 3); endpoint TCB ghi **buộc token operator** (Điểm 4); nới câu chữ §12 "DB đích" (UPDATE cột ảnh trực tiếp parameterized, không còn "chỉ gọi SP"); +**bảng ma trận quyết định** 3 thao tác × 3 mốc (Điểm 6). |
| 04/10/2026 | 3.4 | +§11B.7 **Tra cứu CDB đích** (CHANGES #35, TCB-01..04): màn tra cứu/sửa/xóa HV trên DB đích `GPLX_CDB_CSDT` (song song QLY-01 nhưng trỏ đích); luật khóa đọc ở đích — BC1 (cứng, chặn xóa/đổi khóa) + đã kết xuất DKKH `SoQD_KhaiGiang` (mềm, chặn sửa nhân thân); thay ảnh ghi đè file `.jp2` dùng chung 2 DB; danh mục `DM_TrangThai`; nút Xem chi tiết từ Bàn đồng bộ. Không chạm quyết định §12/13/14. |
