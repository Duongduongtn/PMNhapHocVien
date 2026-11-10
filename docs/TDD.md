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
  gplx_da_co    JSONB,                -- GPLX đã có (§10.6, CHANGES #81); NULL = không có; dọn cùng PII
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
PUT  /api/ho-so/:uuid/gplx      Bổ sung GPLX đã có, CHỈ khi imported; khác→409, rỗng→422; UPDATE nguyên tử, kiểm created_by, ghi audit bo_sung_gplx (THU-07, §10.7, CHANGES #89)
POST /api/ho-so/:uuid/anh       Upload ảnh thô (multipart) — CHỈ khi 'pending' HOẶC 'imported' (bổ sung ảnh HV đã nạp, CHANGES #44); 'importing'/'deleted'→409; kiểm created_by (THU-02, luật đầy đủ §6.3)
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
GET  /api/nap/gplx-bo-sung?limit=&cursor=  Hồ sơ imported có audit bo_sung_gplx, tool so với DB Nạp để cảnh báo; sắp (updated_at, uuid) (QLY-10, §10.7)
GET  /api/nap/tra-uuid?ma_dk=<>  Tra uuid gốc theo ma_dk (VPS lưu ma_dk khi da-nap) — fallback cho QLY-08 bước 2 khi staging nap_xong local không còn
```
> **CAS (review #24):** `tra-ve-cho-nap` chuyển nguyên tử `UPDATE … SET trang_thai='pending', ma_dk=NULL WHERE uuid=:u AND trang_thai='imported'`; 0 dòng bị sửa → **409**. Gọi lại khi đã `pending` → 0 dòng → coi như **idempotent** (báo "đã về chờ nạp", không lỗi) để nhánh retry QLY-08 bước 4 an toàn.

> **GPLX đã có (CHANGES #81, #82, §10.6):** `POST/PUT` hồ sơ (§4.3) nhận `gplx_da_co` (danh sách bằng hoặc null), kiểm ngay trên VPS, sai → 422. `GET /api/ho-so/cua-toi` và `GET /api/nap/keo` trả kèm. App web chỉ gửi trường này trong `PUT` khi người dùng có sửa khối GPLX. Tool local: `NhapChuanBiIn`, `NapIn` nhận `gplx_da_co` (Pydantic kiểm hình dạng); kiểm nghiệp vụ ở `dung_chuoi_gplx_da_co()`; `GET /local/dvhc/noi-cap-gplx` trả danh sách Nơi cấp.

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
POST /local/nap/bo-qua               Bỏ khỏi hàng đợi (1 hay nhiều dòng, MỌI trạng thái) + nhớ "bỏ qua" cho cho/lỗi (keo_ve_bo_qua)  [NAP-01 #51]
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
  HOẶC [Lưu & nhập hồ sơ tiếp → gửi KHÔNG ảnh → toast "Đã gửi ✓" → về thẳng form trống, con trỏ ở Số CCCD] (nhập liên tiếp, CHANGES #96).
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
- **Nới chặn trạng thái cho bổ sung ảnh (CHANGES #44, lật Phương án A):** `POST /api/ho-so/:uuid/anh` trước đây chặn `trang_thai != 'pending'` → **409**. Nay **cho upload CHỈ khi `trang_thai ∈ {'pending','imported'}`** (ghi đè ảnh thô VPS cho HV thiếu ảnh — để tool kéo về bổ sung ở Tra cứu DB/QLY-05). **Dùng allowlist, KHÔNG dùng blocklist:** mọi trạng thái khác → **409**, gồm `importing` (tool đang nạp giữa chừng → tránh đua ảnh) **và `deleted`** (hồ sơ đã xóa mềm — không được ghi ảnh làm sống lại dữ liệu đã xóa). Code: `if hs.trang_thai not in ("pending", "imported"): raise 409` — **không** viết `if == "importing"` (sẽ lọt `deleted`). Giữ kiểm `created_by` (chỉ ảnh của chính mình, chống IDOR). Endpoint này chỉ ghi `anh_tho_path`, KHÔNG đổi `trang_thai`/thông tin — nên mở cho `imported` không ảnh hưởng vòng đời nạp. **Khi ghi ảnh cho `imported`: set `updated_at=now`** (mốc gia hạn PII — xem §9.3/F4). *Vì sao không đụng xóa/sửa: chỉ ảnh mới cần — xóa (THU-05) và sửa thông tin của HV đã nạp vẫn khóa.*

### 6.4 Tìm trong "Hồ sơ đã gửi" (THU-02, CHANGES #10)
Lọc **phía client** trên danh sách `/api/ho-so/cua-toi` đã tải (không thêm endpoint). Khớp theo **tên hoặc số CCCD**; tên **chuẩn hóa bỏ dấu cả hai vế** (NFD + xóa dấu kết hợp) để gõ không dấu vẫn ra. Ô tìm đặt **đầu danh sách**; màn hẹp thu gọn thành **nút kính lúp**.

### 6.5 UX app web sau test điện thoại (THU-01/THU-02, CHANGES #12)
*Vì sao: test thật trên điện thoại lộ ra camera tự mở gây giật, nút tụt khỏi tầm nhìn, không xem lại được hồ sơ đã gửi.*
- **Màn vào không tự mở camera** (THU-01): **mobile** landing cho chọn Quét QR / Nhập tay / Tải ảnh; `getUserMedia` chỉ gọi khi bấm Quét (đỡ xin quyền đột ngột + hao pin). **Desktop (≥lg) vào thẳng form nhập tay** (THU-01, CHANGES #30): bỏ cổng chọn (`giaiDoan` khởi tạo thẳng `preview`/form trống trên desktop); nút **Quét QR / Tải ảnh** thu nhỏ ra góc phải tiêu đề form; bấm Quét QR mở **popover camera nổi** đè form (tái dùng logic `KhungQuet`/decode cascade, không full-screen), bắt được QR → `batDau(fields)` điền vào form đang mở rồi đóng popover. "Lưu & nhập hồ sơ tiếp" trên desktop quay về **form trống** (không về cổng chọn). Mobile giữ nguyên luồng `chon → quet/preview`. *Vì sao: desktop gõ bàn phím là chính, quét webcam phụ — đưa form lên trước, quét thành thao tác điền-nhanh, không bắt qua cổng chọn.* Thuần client `Quet.tsx` (nhánh `lg:`), KHÔNG đổi endpoint/schema.
- **Khung bám QR** (THU-01): BarcodeDetector trả `cornerPoints` (4 góc QR trong khung hình) → vẽ khung khóa theo mã khi bắt trúng. Fallback qr-scanner không có tọa độ → giữ khung ngắm tĩnh.
- **Layout mobile 1 màn** (THU-01, AppLayout): dùng `height:100%`/`100dvh` thay `100vh` (thanh URL mobile), khung camera `flex` co giãn, **bottom-nav + nút hành động chính dính đáy** (`position:sticky`/flex shrink-0), không cuộn mới thấy. Logo header là trang trí — bỏ nền/bo dáng nút.
- **Xem lại + ảnh thật + sửa/chụp lại** (THU-02): danh sách & chi tiết "đã gửi" hiện ảnh thật qua `GET /api/ho-so/:uuid/anh` (của mình, kiểm `created_by` — chống IDOR như `_cua_minh`); modal chi tiết khi `pending` cho **Sửa** (`PUT /api/ho-so/:uuid`) + **Chụp/đổi ảnh** (`POST .../anh`); `importing`/`imported` → chỉ xem thông tin (server trả 409 nếu cố **sửa**/**xóa**) — **nhưng CHO bổ sung ảnh cho HV thiếu ảnh kể cả `imported`** (CHANGES #44, §4.3 nới chặn `POST .../anh`).

### 6.6 Nhập liên tiếp + badge/lọc thiếu ảnh + cảnh báo trùng (THU-01/THU-02/THU-04, CHANGES #13)
*Vì sao: nhân viên nhập hàng loạt muốn gửi nhanh không bắt chụp ảnh từng hồ sơ, rồi gom các hồ sơ thiếu ảnh để chụp bù; và tránh gửi trùng một người lên hàng đợi.*
- **Lưu & nhập hồ sơ tiếp** (THU-01/THU-02): nút thứ hai ở màn preview → gửi `POST /api/ho-so` **không kèm ảnh** (cơ chế gửi-không-ảnh + giữ nháp offline đã có) → **toast** thay màn kết quả → `quetTiep()` về **thẳng form trống** (CHANGES #96; trước đó mobile `setGiaiDoan("chon")` về màn chọn, mỗi hồ sơ thêm một lần chạm): form dựng lại bằng `formKey` nên `autoFocus` đưa con trỏ vào ô Số CCCD, mọi vùng cuộn bao quanh form về đầu, toast hiện ở đầu màn trên điện thoại để không đè thanh nút dính đáy. **Phím tắt (CHANGES #97):** `dieuHuongPhim` bắt Enter trong ô nhập (`HTMLInputElement`, trừ checkbox/radio, khi ô con chưa `preventDefault`) → `giuVaTiep()` chỉ khi là desktop; thiếu thông tin thì chỉ báo lỗi và đưa con trỏ tới ô sai, không gửi. Điện thoại không bắt Enter nên bàn phím ảo vẫn kích nút gửi mặc định (chụp ảnh). Không thêm endpoint. Thuần client `Quet.tsx`.
- **Badge "Thiếu ảnh" + bộ lọc** (THU-02): lọc **phía client** trên `co_anh` của `/api/ho-so/cua-toi` (đã có field). Badge ở list card/table + chi tiết; thêm một lựa chọn lọc "Thiếu ảnh" cạnh tab trạng thái. **Chụp bù ảnh cho HV thiếu ảnh qua nút "Thêm ảnh" — hiện cả khi `pending` lẫn `imported`** (CHANGES #44, lật Phương án A): nút gọi `POST /api/ho-so/:uuid/anh` (server đã nới chặn `pending`, §4.3), chỉ ghi đè ảnh thô VPS, KHÔNG đổi trạng thái/thông tin. Thuần client `DaGui.tsx` + `lib/gui.ts` (bỏ điều kiện chỉ-gửi-ảnh-khi-pending).
- **Cảnh báo trùng CCCD** (THU-04): thêm `GET /api/ho-so/kiem-trung?cccd=` (collector) → đếm hồ sơ `pending`/`importing` cùng CSDT có `so_cccd` khớp (loại trừ chính `uuid` đang gửi). >0 → trả thông tin (ai gửi, lúc nào) để app hiện **banner cảnh báo mềm** (chuẩn ⑥), **vẫn cho gửi**. Mất mạng/khi gọi lỗi → bỏ qua, không chặn. KHÔNG đối chiếu SQL Server (app web không nối DB) — chốt trùng thật ở NAP-06. Server validate `cccd` (12 số) từ chối sớm; client hủy request cũ bằng `AbortController`.
- **UX nhập liệu** (THU-01/THU-02, CHANGES #14): **ẩn ô CMND cũ** khỏi form (giá trị từ QR vẫn giữ trong nháp + gửi như cũ — không đổi payload/schema); ô ngày là **component gõ tay dd/mm/yyyy + nút lịch** (native date popover ghi ngược vào ô text; vẫn nhập năm-only → `yyyy0000`); **desktop** tách vị trí 2 nút + phím tắt (autofocus, Enter→nút chính). Thuần client.
- **Xóa hồ sơ đã gửi** (THU-05, CHANGES #24): ở `/app/da-gui`, hồ sơ **`pending`** có nút **Xóa** (xác nhận 2 bước) → `DELETE /api/ho-so/:uuid` (soft-delete). Hồ sơ `importing`/`imported` **ẩn/khóa nút** (server cũng chặn 409). Phân quyền: collector chỉ xóa `created_by` = mình (chống IDOR như `_cua_minh`); admin bất kỳ. Sau xóa, bỏ dòng khỏi danh sách (client `DaGui.tsx`). Đồng bộ sang tool ở bước kéo (NAP-01, §11.7).
- **Desktop chọn-nhiều-để-xóa** (THU-05, CHANGES #30): bảng desktop thêm **cột ô tích chỉ render ở dòng `pending`** (dòng `importing`/`imported` không có ô tích — khớp luật server chặn xóa); ô tích đầu cột = chọn tất cả `pending` **trên trang hiện tại**. Thanh thao tác nổi "Đã chọn N · Bỏ chọn · Xóa N" hiện khi `chon.size > 0` → dialog xác nhận → **lặp `DELETE /api/ho-so/:uuid` phía client** (for-of, đếm lỗi như `xoaDaChon` của `QuanTriHoSo.tsx`), KHÔNG thêm endpoint batch. Mobile giữ card+modal (xóa lẻ), không thêm chế độ chọn. *Vì sao lặp client: endpoint xóa lẻ đã có quyền + CAS + audit đầy đủ; thêm batch endpoint là nhân đôi logic phân quyền/soft-delete.* Thuần client `DaGui.tsx`.

### 6.7 Chụp ảnh thẻ → tự đọc chữ (OCR) điền sẵn hồ sơ (THU-06, CHANGES #49)
> **Phục vụ:** THU-06
> ✅ **Engine đã chốt (`/tdd` 07/10): Tesseract.js client-side + tách trường bằng regex theo nhãn in trên thẻ.** Mục này chốt *luồng*, *quy tắc fail*, *ràng buộc PII* (nơi chạy = client-side, rào cứng) và *engine*. Còn lại là chi tiết implement.

*Vì sao thêm: iPhone/iOS Safari quét QR CCCD yếu hơn Android (không có `BarcodeDetector`, engine QR web — ZXing/zbar — không đọc nổi QR nhỏ/mờ/lóa; verify BUG-14: 3 engine native + tiền xử lý mạnh đều fail trên ảnh thật). Chữ IN trên thẻ to/rõ nên OCR đọc tốt hơn QR trong đúng ca này → lối nhập dự phòng.*

- **Luồng:** màn vào (`/app/quet`) thêm lối thứ 3 **"Chụp ảnh thẻ (tự đọc)"** (mọi thiết bị) → chụp/tải ảnh mặt trước CCCD → **OCR** đọc trường → điền sẵn vào **màn xác nhận dùng chung** (THU-01/02) → **nhân viên soát/sửa** → lưu như các lối khác (`POST /api/ho-so`, giữ nháp offline, idempotent UUID — không thêm luồng gửi mới).
- **Trường OCR đọc (5 trường MẶT TRƯỚC):** Số CCCD (validate 12 số), họ tên, ngày sinh (ddMMyyyy→yyyymmdd), giới tính (Nam/Nữ), nơi thường trú. **Ngày cấp KHÔNG đọc** — in ở mặt sau thẻ, THU-06 chỉ chụp mặt trước (❌ không đọc mặt sau) → ô ngày cấp để trống + đánh dấu, nhân viên nhập tay (user chốt A, 07/10; phát hiện khi build task 79).
- **Quy tắc fail vs điền-một-phần (mốc = Số CCCD):** lấy **Số CCCD đọc ra có hợp lệ 12 số không** làm ranh giới (CCCD là trường định danh, thiếu nó hồ sơ vô nghĩa):
  - **KHÔNG** đọc được CCCD 12 số hợp lệ → coi là **fail**: báo rõ "không đọc được", **không điền trường nào**, cho quay lại Nhập tay / Quét QR.
  - **CÓ** CCCD 12 số → **điền phần đọc được**; trường thiếu/độ-tin-thấp để trống + **đánh dấu** cho nhân viên soát. Tuyệt đối không điền bừa.
- **Màn xác nhận KHÔNG auto-submit:** đi qua màn xác nhận dùng chung THU-01/02; nhân viên soát/sửa **TỪNG trường** rồi mới lưu (CCCD đọc đủ 12 số vẫn có thể sai chữ số — vd nhầm 8↔3 — mà validate không bắt được; màn xác nhận là lưới chặn duy nhất).
- **Tách trường & tái dùng helper:** tách 6 trường **TỪ text OCR là bước MỚI** (đọc theo layout thẻ / regex — để `/tdd`); `lib/qr.ts` **chỉ tái dùng cho chuẩn hóa hạ nguồn** (ngày ddMMyyyy→yyyymmdd, độ dài tên, parse địa chỉ 2 cấp), KHÔNG lo việc đọc chữ. Map DVHC vẫn ở tool lúc nạp.
- **Phạm vi:** chỉ **CCCD 12 số gắn chip** (mẫu hiện hành). CMND 9 số / CCCD mã vạch cũ → validate 12 số bắt lỗi (ô đỏ) → rơi về Nhập tay.
- **Ràng buộc PII (ảnh căn cước — hệ thống CSDT nhà nước):**
  - **OCR chạy client-side (ảnh KHÔNG rời máy) — RÀO CỨNG.** Gửi ảnh ra dịch vụ OCR/eKYC ngoài chỉ mở khi có **phê duyệt pháp lý/dữ liệu**, KHÔNG phải lựa chọn kỹ thuật thuần ở `/tdd` — HTTPS chỉ bảo vệ đường truyền, bên thứ ba vẫn nhận/giữ/huấn luyện được ảnh CCCD công dân.
  - **Downscale ảnh thẻ ≤ ~1600px cạnh dài TRƯỚC khi OCR** — tránh Tesseract.js treo/sập tab trên điện thoại yếu (ảnh OCR chạy client không qua validate §7.4).
  - **Vòng đời ảnh thẻ:** đọc xong **chỉ giữ nếu tái dùng làm nguồn cắt ảnh chân dung** (như THU-01); nếu không → **hủy khỏi bộ nhớ client, không gửi server**. Không tạo đường lưu ảnh CCCD mới ngoài luồng đã có.
  - **Không tự lưu** khi nhân viên chưa xác nhận; validate đầu ra (CCCD 12 số, độ dài cột DB HoVaTen ≤50…) y như THU-01/02; **không log đầu ra OCR** (§12).
- **Hiệu năng:** bước OCR có **spinner tiến trình + hủy được → về Nhập tay**; mốc NFR "thao tác <2s" (§13) **KHÔNG áp** cho bước đọc OCR (Tesseract.js trên điện thoại mất vài giây).
- **Engine & tách trường (chốt `/tdd` 07/10):** **Tesseract.js** (WASM client, offline, dữ liệu ngôn ngữ `vie`) — giữ ảnh trên máy đúng rào PII. Tách 6 trường = **OCR toàn ảnh rồi regex theo nhãn in trên thẻ** ("Số / No.", "Họ và tên / Full name", "Ngày sinh", "Nơi thường trú", "Ngày cấp"…) làm mốc neo — bền với ảnh chụp tay nghiêng/cắt lệch hơn cắt-vùng-theo-tọa-độ. **Mở kiểm:** nếu độ chính xác tiếng Việt có dấu của Tesseract.js trên thẻ thật quá thấp sau thử nghiệm → nhân viên sửa tay nhiều (vẫn chạy) hoặc xin phê duyệt pháp lý cho eKYC ngoài (đổi quyết định qua `/capnhat`).

**Sơ đồ luồng OCR (THU-06):**
```
Chụp / tải ảnh mặt trước CCCD
        │ downscale ≤ ~1600px cạnh dài (chống treo máy, client)
        ▼
   OCR đọc trường (client-side — ảnh không rời máy)
        │
   Đọc được Số CCCD hợp lệ 12 số?
   ┌────┴───────────────────────┐
  KHÔNG                         CÓ
   │                             │
 Báo "không đọc được",         Điền phần đọc được vào màn xác nhận;
 KHÔNG điền trường nào         trường thiếu/độ-tin-thấp → để trống + đánh dấu
 → quay lại Nhập tay / Quét QR  │
                                ▼
                      Nhân viên soát/sửa TỪNG trường (bắt buộc, không auto-submit)
                                │ validate 12 số + độ dài cột DB
                                ▼
                      Lưu: POST /api/ho-so (idempotent UUID, nháp offline) — như THU-01/02
                                │
                      Ảnh thẻ: hủy khỏi client (trừ khi tái dùng cắt chân dung)
```

---

### 6.8 Loạt UX form xác nhận trên desktop (THU-01/THU-02, CHANGES #52)

> **Phục vụ:** `THU-01`, `THU-02` (dùng chung màn xác nhận/sửa). Thuần client `Quet.tsx` (+ `ODate.tsx`, `Icon.tsx`, `lib/qr.ts`, `lib/dvhc.ts`, `data/dvhc-2025.json`). **KHÔNG đổi endpoint/schema VPS, KHÔNG đổi payload gửi.**

Mười cải tiến nhập liệu nhanh + rõ trạng thái, áp cho form dùng chung ở cả 3 lối vào (QR / nhập tay / OCR):

1. **Nới khung desktop** `max-w-2xl → max-w-3xl` (672→768px) — lưới 2 cột đỡ chật, vùng nội dung desktop (~890px sau sidebar) không còn phí.
2. **Sắp lại ô** theo cụm thông tin trên thẻ: hàng 1 **Số CCCD + Ngày cấp** (user muốn gần nhau); Họ tên và Nơi thường trú chiếm trọn bề ngang; hàng 3 Ngày sinh + Giới tính. Thứ tự DOM = thứ tự nhảy phím mũi tên.
3. **Số CCCD**: lọc còn chữ số + cắt tối đa **12**; bộ đếm `n/12` ở nhãn (xanh khi đủ) + viền xanh + ✓.
4. **Họ và tên tự in hoa** khi gõ (`.toUpperCase()`, giữ dấu) — khớp cột `HoVaTenIn` DB đích.
5. **Giới tính = nút gạt Nam/Nữ** thay `<select>` (1 bấm xong, không xổ dropdown rê chuột); ô chọn có ✓.
6. **Nơi thường trú gợi ý Tỉnh/Xã** (phương án A — nhập tự do + gợi ý, **không ép chọn**): khớp **không dấu** theo đoạn sau dấu phẩy cuối (dùng `boDau` như §6.4), danh sách hiện dưới ô, chọn thì thay đoạn cuối bằng `Phường X, Tỉnh Y`; chuẩn hóa khoảng trắng khi rời ô. **Nguồn dữ liệu: file tĩnh nhúng `webapp/src/data/dvhc-2025.json`** (34 tỉnh + 3.321 xã/phường, đơn vị hành chính 2 cấp 2025, nguồn `thanglequoc/vietnamese-provinces-database` lấy từ GSO) — **nạp lười bằng dynamic import** (chunk riêng ~59KB/gzip 16KB, không vào bundle chính). *Khác hẳn §3.3 — đó là SQLite `DM_DVHC` CỤC BỘ của tool để sinh mã nạp; đây chỉ là gợi ý gõ ở app web, không sinh mã.*
7. **Phím mũi tên nhảy giữa các ô**: Lên/Trái = ô trước, Xuống/Phải = ô sau (Trái/Phải chỉ nhảy khi con trỏ ở đầu/cuối chữ, còn lại di con trỏ như thường); ở ô Giới tính Trái/Phải đổi Nam/Nữ; ở ô địa chỉ khi danh sách gợi ý mở thì mũi tên chọn trong danh sách (chặn `stopPropagation`, không nhảy ô). Xử lý tập trung ở `onKeyDown` cấp form, các ô gắn `data-nav`.
8. **Icon nhỏ ở nhãn** từng ô (idCard/user/cake/users/mapPin/calendar) cho dễ nhận.
9. **Trạng thái ✓/đỏ từng ô** sau khi rời ô (đang gõ không báo đỏ) + **thanh tiến độ** gắn ở mép trên thanh nút dính đáy (CHANGES #100): mỗi ô bắt buộc một vạch (đủ/sai/chưa nhập), chữ "Còn N: <ô>" bấm vào thì focus ô thiếu đầu tiên (GPLX thì mở popup), đủ hết "Đủ 4/4 — sẵn sàng lưu"; tính từ cùng cờ hợp lệ đang dùng cho ✓/đỏ (`cccdOk`, `tenOk`, `nsOk`, `nttOk`, `ngayCapOk`, `loiDanhSach(gplx)`), không thêm luật mới. *Vì sao: thanh nút đáy là chỗ duy nhất luôn nhìn thấy mà không che ô nhập; dòng tóm tắt cuối form trên điện thoại phải cuộn mới thấy.* Ô không bắt buộc (Ngày cấp) im lặng khi trống.
10. **Tự suy Giới tính + Năm sinh từ số CCCD** (`suyTuCccd` trong `lib/qr.ts`): chữ số thứ 4 mã hóa thế kỷ+giới tính, 2 số kế là năm sinh. Chỉ **gợi ý mặc định** khi gõ CCCD tay (giới tính đặt theo CCCD; năm sinh chỉ điền khi ô còn trống — không đè ngày đầy đủ từ QR), **sửa đè được**.

*Vì sao thuần client: đây là lớp trình bày/nhập liệu, không đổi dữ liệu gửi lên — mọi ràng buộc lưu trữ (12 số, độ dài cột) vẫn kiểm ở `kiemFields` như cũ; validate từng ô chỉ là tín hiệu thị giác thêm.*

---

### 6.9 Chế độ sáng/tối ở app web (HTG-08 — CHANGES #94)
> *Vì sao dùng biến CSS thay vì lớp `dark:` của Tailwind: app đã đọc màu qua token (`bg-card`, `text-muted-foreground`…), đổi bộ biến một chỗ là mọi màn đổi theo, không phải thêm `dark:` vào hàng trăm chỗ.*

- Màu khai báo là biến CSS (kênh HSL) ở `webapp/src/index.css`: bộ sáng ở `:root`, bộ tối ở `html.dark`; `tailwind.config.js` đọc `hsl(var(--tên) / <alpha-value>)`. Thêm biến riêng: `--input-border`, `--label`, `--placeholder`, `--scroll`, `--ring`, `--marca-1/2` (nền thương hiệu: xanh luôn đủ đậm để chữ trắng đọc được ở cả hai chế độ).
- `webapp/src/lib/theme.ts`: chế độ hiện tại = lựa chọn đã lưu (`localStorage` khóa `giao_dien`, `sang`|`toi`) nếu có, không thì theo `prefers-color-scheme`. Chưa có lựa chọn thì nghe thay đổi của máy; bấm nút thì lưu chế độ đối diện. Áp bằng lớp `dark` trên `<html>`, `color-scheme`, và `meta theme-color`. Không đọc được `localStorage` (chế độ riêng tư): vẫn chạy, chỉ không nhớ.
- Đoạn script nhỏ trong `<head>` của `index.html` đặt lớp `dark` trước khi trang vẽ để không nháy sáng.
- Nút `NutGiaoDien` (`components/NutGiaoDien.tsx`) ở `AppLayout` (thanh trên, chân thanh bên) và `DangNhap`; có nhãn đọc cho trình đọc màn hình, đạt vùng bấm 44 px.
- Giữ nguyên ở cả hai chế độ: khung camera quét QR (nền đen sẵn), ảnh học viên, lớp phủ mờ của popup. Nút đỏ/xanh đặc đổi nền đậm hơn ở chế độ tối để chữ trắng đạt tương phản.
- Không đụng VPS, DB, tool.

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
- **"Bỏ khỏi hàng đợi" — MỘT đường duy nhất `POST /local/nap/bo-qua` (NAP-01, CHANGES #22 + #51, chốt review #51):** bỏ dòng khỏi `staging.sqlite` bảng `keo_ve` — chỉ dọn hàng đợi tool, **KHÔNG đụng VPS/DB đích**. Khác hẳn "Xóa khỏi DB" (QLY-03 `usp_NguoiLX_Delete`) — đặt tên/nút tách bạch để tránh xóa nhầm prod. Áp cho **MỌI trạng thái** (`cho`/`loi`/`xong`), **1 dòng hay nhiều dòng** đều qua endpoint này.
  - **Vì sao 1 đường (chốt review #51, phương án A):** endpoint cũ `DELETE /local/keo-ve/:uuid` (task 38, guard `409` chỉ `xong`) **bị GỠ BỎ** ở #51 — gộp hết về `POST /bo-qua`. Lý do: nếu còn 2 đường, đường `DELETE` xóa dòng `cho`/`loi` mà **không ghi tombstone** → lần kéo sau hồ sơ quay lại (đúng bug #51 muốn chặn). Một đường duy nhất, tombstone xử theo trạng thái từng uuid (§9.3b) → không thể gọi nhầm đường không-tombstone. **UI phải chuyển** mọi chỗ đang gọi `DELETE /keo-ve/:uuid` sang `POST /bo-qua` với `{uuids: [<1 uuid>]}`.
- **Vì sao dòng `cho`/`loi` cần tombstone:** dòng `cho`/`loi` có thể **vẫn đang `pending` trên VPS**, nên xóa suông thì lần `keo_ve_upsert` sau kéo lại. Giải: ghi uuid vào **tombstone cục bộ `keo_ve_bo_qua`** (§9.3b) → `keo_ve_upsert` **bỏ qua** uuid này ở mọi lượt kéo sau. Chỉ đụng `staging.sqlite`, **KHÔNG đụng VPS** (hồ sơ còn hay mất trên máy chủ là việc của app web — THU-05). Dọn kèm nháp (`nhap_xoa`). **Dùng cho ca "hồ sơ đã xóa bên app web nhưng tool kéo về từ trước nên còn sót"** mà cơ chế đồng bộ-xóa theo mốc (§11.7, chỉ bắt xóa SAU mốc) bỏ lọt. *Vì sao không nới watermark đồng bộ-xóa để tự dọn: đồng bộ-xóa chỉ bắt hồ sơ VPS báo `deleted`; hồ sơ operator chỉ "không muốn nạp" (chưa chắc đã xóa trên app) không có tín hiệu VPS → cần lối dọn tay, chủ động.*
  - **Bỏ nhiều một lượt:** `POST /local/nap/bo-qua` `{uuids: [...]}` (tombstone + xóa `keo_ve` + `nhap_xoa` theo lô, idempotent — logic chi tiết §9.3b). UI chọn nhiều dòng + xác nhận 2 bước (tái dùng mẫu panel đỏ). Dòng `xong` lẫn trong lô vẫn bỏ được nhưng **không cần** tombstone (VPS đã `da_nap`) — tombstone chỉ ghi cho `cho`/`loi` (xem lý do QLY-08 ở §9.3b).

### 7.3 Xóa PII (BR-016)
APScheduler quét mỗi giờ: `pending`/`imported` quá 30 ngày → xóa dòng + file ảnh thô; **bỏ qua** `importing` (EC-040). Ghi `audit_log(hanh_dong='xoa_pii')`.
> **Mốc tuổi tính theo `updated_at`, KHÔNG theo `created_at` (CHANGES #44, F4):** vì #44 cho collector chụp bù ảnh cho HV `imported` thiếu ảnh (set `updated_at=now` khi ghi ảnh — §6.3), nếu job tính tuổi theo lúc tạo thì ảnh chụp bù cho HV nạp gần 30 ngày sẽ bị xóa ngay trước khi operator kịp kéo ở QLY-05. Tính theo `updated_at` → mỗi lần chụp bù gia hạn thêm 30 ngày cho operator kéo. (Hồ sơ không ai đụng vẫn hết hạn đúng 30 ngày kể từ lần ghi cuối.)

### 7.4 Validate ảnh thô khi nhận (bảo mật)
`POST /api/ho-so/:uuid/anh` phải kiểm trước khi lưu: kích thước **≤ 8 MB**; **magic-byte** đúng JPEG/PNG (không tin đuôi/Content-Type); giới hạn số điểm ảnh (`Image.MAX_IMAGE_PIXELS`) để chặn ảnh "bung nén" (decompression bomb) làm treo/sập tool khi `rembg`/`Pillow` xử lý. Không hợp lệ → 4xx, báo lỗi rõ (PRD ⑦).

### 7.5 Quyền sở hữu bản ghi: mốc "Nạp" là điểm bàn giao (CHANGES #26)

Một hồ sơ sống ở **2 nơi**: VPS (app web — nơi collector tạo) và CSDT (qua tool — DB thật). Để không mâu thuẫn khi sửa/xóa từ 2 phía, quyền làm chủ **chuyển theo mốc nạp**:

- **Trước nạp** (`pending`): **app web làm chủ.** Collector thêm/sửa/xóa (THU-05); tool chỉ kéo-mirror (NAP-01), chưa đụng DB.
- **Sau nạp** (`imported`): **tool/CSDT làm chủ.** Operator sửa nhân thân/ảnh/đổi khóa/xóa (QLY-01/02/03/05/08); bản ghi app web **đóng băng** — chỉ xem, không sửa thông tin/xóa (`PUT`/`DELETE /api/ho-so/:uuid` chỉ khi `pending`). **Ngoại lệ (CHANGES #44): collector được bổ sung ẢNH cho HV `imported` thiếu ảnh** (`POST .../anh`, §6.3) — chỉ ghi ảnh thô, vẫn không sửa thông tin/xóa. **Khe thứ hai (CHANGES #89): bổ sung GPLX đã có** (`PUT .../gplx`, §10.7), người nạp duyệt mới vào DB. Chỉ ghi `gplx_da_co` và `updated_at`; mọi trường khác vẫn đóng băng. Bản VPS thành lịch sử, KHÔNG đẩy ngược từ CSDT.

**Edge (khóa chưa BC1):**

| Chặng | Tình huống | Xử lý |
|---|---|---|
| Cửa sổ bàn giao | Collector sửa lúc tool vừa kéo bản cũ | Tool đọc bản mới nhất ở bước `lock` (lock trả record tươi) — không nạp bản staging cũ |
| Cửa sổ bàn giao | Collector xóa đúng lúc operator bấm nạp | Ai tới trước: tool `lock` trước → app web `DELETE` 409; app web xóa trước → `lock` CAS 0 dòng → tool báo "hồ sơ đã bị người gửi xóa" |
| Sau nạp | Collector muốn sửa/xóa trên app web | Không cho sửa thông tin/xóa (đóng băng). **Riêng bổ sung ẢNH cho HV thiếu ảnh (§6.3/#44) và bổ sung GPLX đã có (§10.7/#89): cho.** Sửa khác làm ở tool (QLY-01/05) |
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

Trước #32, mọi chỉnh sửa khi chuẩn bị nạp (`nhap[uuid]`: `diaChi`, `chiTiet`, `noiCap`, `ngayCap`, `tick`, `jp2`, `anhPreview`) **chỉ sống trong RAM** của màn NapHoSo → tải lại trang/đóng tool là mất. Nay **lưu bền xuống staging** để sống qua phiên và để 2 chip trạng thái (§10.5) đúng kể cả sau khi mở lại.

- **Kho:** bảng RIÊNG trong `staging.sqlite` — **`nhap_chuan_bi(uuid PRIMARY KEY, dia_chi_json, chi_tiet, noi_cap, ngay_cap, tick_json, jp2_b64, anh_preview, updated_at, chon_in_gplx)`** (`chon_in_gplx INTEGER` thêm ở CHANGES #79 — xem §10.2; cùng guard `PRAGMA table_info` + `ALTER` như `ngay_cap`). *Vì sao bảng riêng chứ không thêm cột vào `keo_ve`: tách bạch DỮ LIỆU GỐC VPS (`keo_ve`, do `keo_ve_upsert` làm tươi) khỏi NHÁP OPERATOR — upsert làm tươi dòng `cho` không vô tình đè/được đè bởi nháp; xóa nháp độc lập.*
- **Migrate cột `ngay_cap` (BẮT BUỘC — DDL là `CREATE TABLE IF NOT EXISTS`):** cột `ngay_cap` là bổ sung ở #43; máy đã chạy tool (đã tạo `nhap_chuan_bi` theo #32) có bảng **thiếu** cột này, mà `IF NOT EXISTS` **không thêm cột** vào bảng đã có → `INSERT ... (… ngay_cap …)` ném `OperationalError: no column named ngay_cap`, lưu nháp vỡ. `tool/app` **không có cơ chế migrate** → phải thêm guard idempotent trong `_nhap_conn()` ngay sau `CREATE TABLE IF NOT EXISTS`:
  ```python
  cols = {r[1] for r in conn.execute("PRAGMA table_info(nhap_chuan_bi)")}
  if "ngay_cap" not in cols:
      conn.execute("ALTER TABLE nhap_chuan_bi ADD COLUMN ngay_cap TEXT")
  ```
  Áp cùng cách cho mọi lần thêm cột vào bảng staging dùng `CREATE TABLE IF NOT EXISTS` về sau.
- **Ảnh trong nháp:** `jp2_b64` (ảnh đã đổi nền, để nạp) + `anh_preview` (PNG để hiển thị) lưu **trong SQLite** cạnh nháp — là **PII ảnh căn cước nằm lại máy tool**, đi ngược nguyên tắc §9.3/§7.4 cũ; chấp nhận có điều kiện (máy nội bộ CSDT + tự xóa — xem TDD-decisions §11). Dọn như §9.3: nạp xong thì xóa.
- **API (tool-local):**
  - `GET /local/nap/nhap?uuids=<csv>` — **danh sách cờ NHẸ** cho cả lưới: mỗi dòng chỉ `{uuid, co_dia_chi, co_anh, co_tick}` (boolean), KHÔNG kèm `jp2_b64`/`anh_preview`. Dùng vẽ 2 chip §10.5 cho mọi dòng mà không tải ảnh. *Vì sao tách (review #32, Điểm 5): nếu dùng GET-theo-uuid full để lấy cờ thì phải tải toàn bộ base64 ảnh cả khóa chỉ để hiện 1 chip boolean → giật + tốn RAM tab.*
  - `GET /local/nap/nhap/{uuid}` — đọc **đầy đủ** 1 nháp (kèm `jp2_b64`+`anh_preview`), **chỉ gọi khi MỞ drawer Chuẩn bị** (nạp vào `nhap[uuid]`), không gọi hàng loạt.
  - `PUT /local/nap/nhap/{uuid}` — lưu nháp (gọi khi **đóng drawer Chuẩn bị** hoặc debounce khi đổi — không spam mỗi phím).
- **Vòng đời — tự xóa nháp** (đi kèm mọi điểm dòng `keo_ve` kết thúc): nạp xong (`keo_ve_cap_nhat(... 'xong')`), "Bỏ khỏi hàng đợi" (`keo_ve_xoa`), đồng bộ xóa VPS (`keo_ve_xoa_neu_cho`) → **xóa dòng `nhap_chuan_bi` cùng `uuid`**. Gom thành 1 helper `nhap_xoa(uuid)` gọi chung ở các chỗ này. Thêm **nút "Xóa nháp"** trên drawer Chuẩn bị gọi cùng `nhap_xoa(uuid)` để operator **chủ động dọn** một nháp.
- **Giới hạn PII nháp bỏ dở (review #32, Điểm 4):** nháp của một dòng `cho` mà operator **không nạp** và collector **không xóa trên app web** thì không rơi vào 3 lối tự-xóa trên → **tồn tại (gồm ảnh căn cước) tới khi operator bấm "Xóa nháp"**. Chấp nhận giới hạn này (máy nội bộ CSDT) — xem TDD-decisions §11.
- **Cạm bẫy `keo_ve_upsert` + BUG-04 (bắt buộc):** `keo_ve_upsert` khi làm tươi dòng `cho` hiện GHI ĐÈ `noi_tt_raw` bằng bản mới từ VPS. Khi **`noi_tt_raw` ĐỔI** so với bản đang có → **reset phần ĐỊA CHỈ của nháp bền** (`dia_chi_json=NULL`, `chi_tiet` tính lại từ raw mới) + chip địa chỉ về `✗` + toast "địa chỉ của N hồ sơ đã đổi, cần map lại"; **GIỮ** `jp2_b64`/`anh_preview`/`tick_json`/`noi_cap`/`ngay_cap`. `noi_tt_raw` **không đổi** → giữ nguyên nháp. *Đặt so-sánh + reset ở BACKEND (trong/cạnh `keo_ve_upsert`, so raw cũ↔mới trước khi đè) để nguồn sự thật nhất quán, thay vì chỉ ở client `lamTuoiNhapDiaChi` như hiện tại.*
- **Luật ghép địa chỉ hiển thị (review #32 — xác minh DB thật 04/10):** DB lưu **tách** `NoiTT` (chi tiết, nvarchar 50) và địa chỉ hành chính dạng **mã** (`NoiTT_MaDVHC`/`NoiTT_MaDVQL` varchar 5) — **không có SP/view nào ghép** 2 phần, và `DM_DVHC.TenDayDu` cấp xã **đã chứa sẵn phẩy giữa các cấp** (vd `Xã Phước Hòa, Thành phố Hồ Chí Minh`). → Mọi chỗ **tool** hiển thị một dòng địa chỉ phải ghép `[chi_tiet, TenDayDu(xã)].filter(Boolean).join(", ")` (lọc rỗng, ngăn cách `", "`) — đã làm đúng ở popup Chi tiết (`TraCuuDB.tsx`), áp cùng cách cho preview địa chỉ ở drawer Nạp lô. **Lưu `NoiTT` vẫn chỉ chi tiết thuần** (không nhét tên xã/dấu phẩy — giữ §10.2). *App cũ tự render địa chỉ theo cách của nó — ngoài tầm tool.*
- **Ngày cấp CCCD ở drawer Chuẩn bị (CHANGES #43):** ô có nhãn riêng dùng lại component **`ODate`** (nhập `dd/mm/yyyy`, kèm `max`=hôm nay) — **cùng control với ô Ngày cấp ở `TraCuuDB.tsx`/`TraCuuCDB.tsx`**, KHÔNG dùng `<input type="date">` (để đồng nhất giao diện + giữ chuẩn ngày VN dd/mm/yyyy; `<input type="date">` hiển thị theo locale máy, không chắc ra dd/mm/yyyy). **Điền sẵn** từ `keo_ve.ngay_cap` qua `ymdToVN` (yyyymmdd→dd/mm/yyyy) và **sửa được** như ô Nơi cấp; lưu vào `nhap_chuan_bi.ngay_cap` qua `vnToYmd` (dd/mm/yyyy→yyyymmdd), theo luật GIỮ khi reset địa chỉ (BUG-04). Lúc nạp, payload ưu tiên `nhap.ngayCap` rồi mới tới `keo_ve.ngay_cap` gốc (`NgayCapCMT`) — dùng **một quy tắc `nhap.ngayCap || keo_ve.ngay_cap`** cho cả hiển thị lẫn nạp, nên **ô để rỗng → quay về ngày gốc VPS** (ngày cấp gần như luôn có giá trị đúng từ CCCD; không mở ca "xóa trắng chủ động"). Trước #43 chỉ là chữ read-only, luôn lấy giá trị gốc. Nạp vẫn ghi đúng ngày cấp vào DB → **NAP-05 không đổi tiêu chí Done**.
- **Nơi cấp luôn điền sẵn dù danh mục nguồn thiếu '00' (CHANGES #43, bền hóa #40):** combo Nơi cấp lấy option từ `DM_DVHC` DB nguồn; nếu máy CSDT **chưa chạy script đồng bộ `DM_DVHC` đích→nguồn** (#40) thì danh mục nguồn không có mã `'00'` Cục QLHC → `<select value="00">` không khớp option nào, tụt về placeholder (trông như "không tự chọn"). Fix phía client: khi `suyNoiCap(cccd)` hoặc nháp ra `'00'` mà danh sách combo chưa có → **tự chèn option `00 — Cục QLHC`** để luôn hiển thị đúng. Dữ liệu nạp không đổi (payload vẫn gửi `'00'`). *Đây là lớp phòng thủ cho tiền đề #40 chưa chạy trên máy đó, không thay cho việc đồng bộ danh mục.*

```
Vòng đời nháp chuẩn bị (nhap_chuan_bi, keyed theo uuid dòng keo_ve):

   mở drawer / debounce sửa
        │ PUT /local/nap/nhap/{uuid}
        ▼
   ┌──────────────┐   noi_tt_raw ĐỔI (keo_ve_upsert, BUG-04)
   │  nháp bền    │──────────────────────────────────┐
   │ dia_chi,     │   reset dia_chi_json=NULL,        │
   │ chi_tiet,    │   chi_tiet tính lại từ raw,       │
   │ noi_cap,     │   chip địa chỉ → ✗ + toast;       │
   │ ngay_cap,    │   GIỮ jp2/preview/tick/noi_cap/   │
   │ tick,        │       ngay_cap                    │
   │ jp2_b64,     │◀──────────────────────────────────┘
   │ anh_preview  │
   └──────────────┘
        │ nhap_xoa(uuid) — xóa cả ảnh
        ▼
   (xóa khi)  • nạp xong            keo_ve_cap_nhat(...'xong')
              • "Bỏ khỏi hàng đợi"  keo_ve_xoa          (dòng 'xong')
              • bỏ qua dòng cho/lỗi keo_ve_bo_qua + keo_ve_xoa (CHANGES #51)
              • đồng bộ xóa VPS     keo_ve_xoa_neu_cho
              • nút "Xóa nháp"      operator chủ động (review #32, Điểm 4)

   ⚠ Nháp bỏ dở (dòng 'cho' không nạp, VPS không xóa) TỒN TẠI tới khi
     operator bấm "Xóa nháp" HOẶC "Bỏ khỏi hàng đợi" (CHANGES #51)
     (giới hạn PII đã ghi ở TDD-decisions §11).
```

### 9.3b Tombstone "bỏ qua" dòng chờ nạp (`keo_ve_bo_qua` — CHANGES #51, NAP-01)

Operator "Bỏ khỏi hàng đợi" một dòng `cho`/`loi` = **chủ động không nạp** hồ sơ đó. Vì hồ sơ có thể **vẫn `pending` trên VPS** (chưa chắc đã xóa ở app web), xóa suông khỏi `keo_ve` thì `keo_ve_upsert` lượt kéo sau **mang về lại**. Cần nhớ uuid đã bỏ.

```sql
-- staging.sqlite — danh sách uuid operator đã "bỏ qua" (không kéo về lại).
CREATE TABLE IF NOT EXISTS keo_ve_bo_qua (
  uuid        TEXT PRIMARY KEY,   -- = uuid dòng keo_ve đã bỏ
  ly_do       TEXT,               -- 'operator' (dọn tay) — để sau mở rộng nếu cần
  created_at  TEXT NOT NULL       -- ISO, giờ ghi (chẩn đoán)
);
```

- **Logic `POST /local/nap/bo-qua {uuids}` (idempotent, 1 transaction):**
  ```
  cho mỗi uuid trong uuids:
      tt = keo_ve_trang_thai(uuid)              # 'cho' | 'loi' | 'xong' | None
      nếu tt ∈ {'cho','loi'} HOẶC tt is None:   # None = dòng đã trôi / gọi lại lần 2
          INSERT OR IGNORE INTO keo_ve_bo_qua(uuid, 'operator', now)
      # tt == 'xong': KHÔNG ghi tombstone — xem lý do QLY-08 dưới
      keo_ve_xoa(uuid)      # idempotent: không có dòng → no-op
      nhap_xoa(uuid)        # dọn nháp bền + ảnh PII (TDD-decisions §11)
  trả {bo: <số uuid đã xử>, tombstone: <số ghi mới>}
  ```
  Endpoint nhận `{uuids}` **trần** (không kèm trạng thái) → phải **tra `keo_ve_trang_thai(uuid)` từng uuid** để quyết định có ghi tombstone không. uuid **không còn** trong `keo_ve` (`None`: kéo trôi / gọi lại) → **vẫn ghi tombstone** (operator đã chủ ý bỏ; chặn kéo lại nếu VPS còn `pending`).
- **Chặn kéo lại:** `keo_ve_upsert(rows)` **lọc bỏ** mọi row có `uuid ∈ keo_ve_bo_qua` TRƯỚC khi upsert (không thêm mới, không làm tươi). *Đặt lọc ở backend trong `keo_ve_upsert` để mọi đường kéo đều thống nhất — vì `keo_hang_doi` gọi `keo_ve_upsert` theo TỪNG trang cursor, lọc phải nằm TRONG `keo_ve_upsert`, không được lọc 1 lần ở router.*
- **Vì sao KHÔNG ghi tombstone cho dòng `xong` (quan trọng — đừng "ghi luôn cho đồng nhất"):** dòng `xong` là HV đã nạp; nếu sau này **QLY-08 "Gỡ về chờ nạp"** đẩy VPS `imported→pending`, uuid đó phải **kéo lại được**. Ghi tombstone cho `xong` sẽ **chặn vĩnh viễn** đường QLY-08 đó → tuyệt đối không ghi. (`xong` bỏ qua `keo_ve_xoa` như cũ, VPS đã `da_nap` nên cũng không kéo lại trong luồng thường.)
- **Lô rỗng `{uuids: []}`:** no-op, trả `{bo:0, tombstone:0}` 200 — không phải lỗi.
- **Trần kích thước lô:** `len(uuids) ≤ 1000` → vượt trả `4xx` (phòng payload bất thường; UI chọn-cả-khóa thực tế vài trăm dòng).
- **Tham số hóa bắt buộc:** mọi query chạm `keo_ve_bo_qua`/bỏ-qua phải dùng placeholder `?`, **tuyệt đối không ghép chuỗi `uuid` vào SQL** — dù endpoint chạy localhost, `uuid` vẫn là dữ liệu ngoài (do app web sinh). Bám đúng kiểu các query `keo_ve_*` sẵn có.
- **Tombstone không tự dọn (giới hạn đã biết):** bảng `keo_ve_bo_qua` chỉ thêm, không có đường xóa → phình dần theo thời gian. **Chấp nhận:** `uuid` là khóa chính (tra có index), mỗi dòng ~40 byte, chục nghìn dòng vẫn <1 MB + lọc vẫn nhanh. Để ngỏ job dọn theo tuổi nếu sau này phình bất thường — **KHÔNG làm ở #51**.
- **Gửi lại = uuid mới:** collector tạo hồ sơ mới trên app web sinh uuid khác → không khớp tombstone → **hiện lại bình thường** (đúng PRD edge case).
- **Vì sao bảng riêng, không thêm cột `trang_thai='bo_qua'` vào `keo_ve`:** `keo_ve` chỉ chứa hồ sơ ĐANG trong hàng; tombstone cần sống **sau khi dòng đã bị xóa** để chặn kéo lại — bản chất khác, tách bảng cho sạch (giống lẽ tách `nhap_chuan_bi`).
- **Migrate (bắt buộc — DDL `IF NOT EXISTS`):** bảng mới, máy đã chạy tool chưa có → thêm `CREATE TABLE IF NOT EXISTS keo_ve_bo_qua(...)` vào chỗ dựng schema staging (cùng nơi tạo `keo_ve`/`nhap_chuan_bi`); không cần `ALTER` vì là bảng trọn, không thêm cột vào bảng cũ.

### 9.4 Ca lỗi
- rembg xấu (tóc/viền) → cho giữ ảnh gốc / chỉnh tay.
- Ghi file rồi SP lỗi → dọn file `.jp2` chính thức vừa ghi, không để mồ côi (EC-022).
- Chưa có ảnh → cảnh báo mềm, vẫn cho nạp (BR-011).

---

## 10. Nạp hồ sơ vào DB qua SP (tool)

> **Phục vụ:** `NAP-05`, `NAP-01` (ô "Chọn in GPLX" ở ngăn Chuẩn bị), `NAP-02`, `NAP-06`
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
         GiayTo (danh sách MaGT), GPLX đã có…, GhiChu, SO_CMND_CU, CHON_IN_GPLX(1/2/3; mặc định theo hạng khóa: A*→3, còn lại→2)
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
> nên bản ghi khớp 100% (gồm `CHON_IN_GPLX` — từ 16/10/2026 theo hạng khóa/lựa chọn, không còn gán cứng 2 —, họ tên IN HOA, địa chỉ mã+chi tiết tách riêng) —
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
- `MaLoaiHs` (SP tự tính): `HangDT` chứa `'-'` (nâng hạng) → **3**; `HangGPLX` bắt đầu bằng `'A'` → **1** (mô tô); còn lại → **2** (ô tô).
- `MaHTCap=CM_VN`, `Transfer_flag=0`, `MaCSDT=70004`, `MaSoGTVT=70` (SP tự tính từ khóa).
- `GiayCNSK`: SP set **1 chỉ khi** `@p_GiayTo` chứa `'3,'` (giấy khám sức khỏe, MaGT=3); bỏ tick giấy 3 → **0** (không phải hằng số).
- **`TT_XuLy` (SP luôn set `'01'` lúc tạo — xác nhận thân SP + `KIEM_TRA_ANH='fpt@'`; tool nâng `'03'` ở bước UPDATE ảnh, hướng A):** có ảnh → `TT_XuLy='03'` + `ChatLuongAnh=1` (+ `NgayThuNhanAnh`,`NguoiThuNhanAnh`); **chưa có ảnh → `TT_XuLy='01'`, `ChatLuongAnh=NULL`, không ghi `DuongDanAnh`** (BR-011 cho nạp thiếu ảnh). Bằng chứng: khóa `70004K26B010` 55/55 HV đều `03`+ảnh; toàn bảng `01` chỉ xuất hiện khi không ảnh (93 bản), `03` chỉ khi có ảnh (2.256 bản). Khi bổ sung ảnh sau (đổi khóa/sửa) → nâng `01`→`03`.
- **`TrangThai=1` khi tạo — KHÔNG đổi theo ảnh** (=0 chỉ khi vô hiệu hóa về sau).
- Giấy tờ: theo **trạng thái tick cuối** của user (mặc định đủ 3, bỏ tick được — BR-009/5.1); truyền danh sách `MaGT` đã tick qua `@p_GiayTo`; `TenGT` đầy đủ từ `DM_GiayTo` (SP tự lo hoặc tra khi dựng @p_GiayTo).
- **Tra danh mục giấy tờ (BUG-20, 10/11/2026):** `DM_LoaiHSo_GiayTo.MaHangGPLX` ghi mã không dấu chấm và thiếu nhiều mã hạng mới (khóa B11 có `HangDT='B.01'` nhưng danh mục ghi `B01`; khóa A2 `HangDT='Am'` mà danh mục chỉ có `A2`). Tool dò lần lượt `HangDT` → `HangDT` bỏ dấu chấm → `HangGPLX`, lấy danh sách đầu tiên không rỗng (`routers/nap.py` `doc_giay_to`); vẫn rỗng → **chặn nạp**, báo bổ sung danh mục. Phần mềm cũ hiện danh sách theo `DM_HangGPLX.MaHangMoi` bỏ dấu chấm (`usp_QuangLA_PM4_ThuNhanHS_DSGiayTo`), nên DB thiếu dòng `Am`/`Cm` thì cũng hiện trống → `scripts/bo_sung_giay_to_hang_moi.sql` thêm danh mục + giấy tờ cho hồ sơ đang trống. `MaLoaiHs` tool suy cùng luật SP (có ca nâng hạng = 3).
- **Tách họ tên (EC-030):** app web lưu `ho_ten` một chuỗi; **SP TỰ TÁCH** khi nạp (tool chỉ truyền `@p_HoVaTen` đầy đủ + `@p_HoVaTenIn`; tool tách chỉ để KIỂM ĐỘ DÀI từng cột, KHÔNG truyền `HoDem`/`Ten` riêng — SP không có tham số đó). SP tách: `TenNLX` = **từ cuối**, `HoDemNLX` = **phần còn lại**, `HoVaTen` = tên đầy đủ. **TẤT CẢ IN HOA GIỮ DẤU** ("NGUYỄN VĂN AN") — verify AS-003: 55/55 HV khóa B-K149 `HoVaTen` in hoa. **`HoVaTenIn` = `HoVaTen` cắt ≤25, cũng IN HOA giữ dấu** (39.752/39.778 = 99,93% `HoVaTenIn` ≡ `HoVaTen`) — **KHÔNG bỏ dấu**. Trước nạp kiểm độ dài từng cột (≤50/30/20/25); vượt → cảnh báo cho cắt tay.
- **Field map khớp app cũ (verify AS-003 01/10/2026, khóa B-K149):**
  - `MaQuocTich = 'VNM'` (chuẩn ISO alpha-3 = `DM_QuocTich.Ma`; **"VN" vỡ `FK_NguoiLX_DM_QuocTich`**).
  - `NoiTT`/`NoiCT` = **chi tiết địa chỉ (số nhà/thôn), mặc định TRỐNG** — 55/55 HV thật để trống; địa chỉ hành chính nằm ở `NoiTT_MaDVHC`/`NoiTT_MaDVQL` (2 cấp: xã + tỉnh). **KHÔNG nhét tên xã vào `NoiTT`** (gây app hiển thị lặp Địa chỉ + Chi tiết). Tương ứng `@p_MaDVHC_TT`+`@p_ChiTiet_TT` (và `_CT`).
  - `DonViHocLX = NULL` (55/55 thật NULL; không hard-code `70004`).
  - `CHON_IN_GPLX` (**đổi 16/10/2026, CHANGES #79** — trước đó gán cứng 2): `hv["chon_in_gplx"]` nếu nhân viên chọn, ngược lại `nap.chon_in_gplx_mac_dinh(khoa.hang_gplx)` → hạng bắt đầu `A` (mô tô) = **3**, còn lại/trống = **2**. Giá trị: 1 = In 01 GPLX (ghép: có TH + không TH) · 2 = có thời hạn · 3 = không thời hạn (suy từ dữ liệu DB Nạp thật: ô tô ~15.000 HV = 2, mô tô ~17.000 HV = 3, hiếm 1; thứ tự 1/2/3 chưa đối chiếu với ô `cboInGplx` máy cũ — nếu khác chỉ sửa bảng nhãn `IN_GPLX_NHAN`). Cột `NguoiLX_HoSo.CHON_IN_GPLX int` default 0; không bảng danh mục (hard-code ở phần mềm cũ). API `NapIn.chon_in_gplx` + `NhapChuanBiIn.chon_in_gplx`: server chỉ kiểm giá trị ∈ {1,2,3} (ngoài tập → 422) và **dùng đúng giá trị client gửi** — đó là lựa chọn của nhân viên, không phải dữ liệu để tính lại. Chỉ khi client không gửi (`None`, vd gọi API trực tiếp) mới lấy mặc định theo `KhoaHoc.HangGPLX` đọc từ DB (hạng khóa thì không tin client). UI luôn gửi giá trị đang hiện nên nhánh `None` chỉ là lưới an toàn.
  - **Nháp bền:** bảng `nhap_chuan_bi` thêm cột `chon_in_gplx INTEGER` (NULL = chưa đổi → luôn theo hạng khóa), thêm bằng `ALTER TABLE` khi thiếu (cùng mẫu cột `ngay_cap`). **Quy tắc ghi (CHANGES #80, sau `/reviewtdd` 16/10/2026):** chỉ ghi số khi nhân viên chọn **khác mặc định hiện tại** của khóa; chọn lại đúng giá trị mặc định → ghi NULL. Khi đổi khóa nạp sang khóa **khác loại** (mô tô ↔ ô tô), UI xóa lựa chọn tay của mọi hồ sơ đang mở (ghi NULL xuống nháp) và ô về mặc định của khóa mới — tránh học viên ô tô mang "không thời hạn" từ lúc còn ở khóa mô tô. *Giới hạn đã biết:* hồ sơ chưa mở trong phiên này mà nháp cũ còn lựa chọn khác cả hai mặc định (thực tế chỉ giá trị 1 "ghép") vẫn giữ — ô hiện giá trị đó khi mở hồ sơ nên nhân viên thấy được.
  - **UI:** ngăn Chuẩn bị có ô "Chọn in GPLX" điền sẵn + tên loại in + dòng gợi ý khóa mô tô/ô tô (`pages/tool/inGplx.ts` phản chiếu quy tắc backend); `dungNapIn` luôn gửi giá trị đang hiện.
  - **Sync CDB:** `_HV_SELECT` đọc `B.CHON_IN_GPLX`, `_INSERT_HOSO` ghi cột này sang DB đích **nguyên giá trị** (NULL/thiếu → 0). Lý do: phần mềm CDB không hiện ô chọn nhưng 6 SP đọc/xuất (`usp_NguoiLX_Select_By_MaKH/_MaBC2/_MaBC2_2XML/_MaDK`, `usp_QuangLA_PM4_ThuNhanHS_LoadThongTin/ThemMoiCapNhat`) đều lấy cột này đưa vào file BC1/BC2 gửi Sở. *Chưa xác minh Sở có dùng trường này.*
  - **Ngoài phạm vi (ghi nợ):** HV mô tô đã nạp trước 16/10/2026 mang 2; ~739 HV ở DB đích đang 0 (25 HV đã vào BC2) — cần script cập nhật riêng nếu muốn.

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

### 10.6 GPLX đã có (NAP-07, THU-07 — CHANGES #81)
> **Phục vụ:** `NAP-07`, `THU-07` (sau nạp: §10.7). *Vì sao không đổi schema DB Nạp: 7 cột và tham số SP đã có sẵn, phần mềm cũ đang ghi đúng các cột này.*

```
App web: tích "Đã có GPLX" → nhập → gửi → VPS ho_so_thu_thap.gplx_da_co (JSONB)
                                               │ GET /api/nap/keo
Tool:    keo_ve.gplx_da_co_json ───────────────┘
           │ hiển thị = nháp nếu đã sửa, không thì giá trị VPS
         nhap_chuan_bi.gplx_da_co_json (nhân viên sửa)
           │ Nạp → dung_chuoi_gplx_da_co() → 6 tham số @p_*DaCo của SP gộp
         DB Nạp NguoiLX_HoSo → Sync chép nguyên (không đổi) → DB đích
```

**Cấu trúc 1 bằng (JSON):** `{"nhom":"cu|moi","hang":"B2","so":"…","ngay_tt":"yyyymmdd","ngay_cap":"yyyymmdd","ngay_hh":"yyyymmdd","don_vi":"70"}`. **`hang` luôn là MÃ `DM_HangGPLX`** (`A1m`, `B11`), không phải nhãn; `nhom` + mã tra ngược ra nhãn. Ô Hạng dùng khóa `moi:B1` / `cu:B1` làm `ma` của `ComboLoc` (mã trùng giữa hai nhóm), tách ra khi lưu.

**Thứ tự ưu tiên:**
```
 VPS gplx_da_co ──kéo/làm tươi──► keo_ve.gplx_da_co_json (dòng cho)
                                       │
 nhân viên sửa ──PUT nháp──► nhap_chuan_bi.gplx_da_co_json
        NULL     → dùng keo_ve
        '[]'     → không có bằng (nhân viên đã xóa hết)
        có JSON  → dùng nháp; VPS đổi thì hiện cờ "App web có bản mới" + nút "Dùng bản app web"
                                       │ hiển thị = nháp ?? keo_ve (ghép MỘT chỗ ở UI)
                 chip / lọc / số đếm / Nạp ◄─┘
 Nạp xong ok: ghi giá trị đã nạp vào keo_ve TRƯỚC nhap_xoa(uuid)
```

**Ghi xuống SP (`nap.py`, hàm thuần):**
- Một bằng: ghi thẳng. Nhiều bằng: nối `|` theo cùng thứ tự ở cả 6 cột, ô trống giữ vị trí (`20180427|` ; hết hạn `|`). Không có bằng: chuỗi rỗng `''` ở cả 6 cột. `@p_NoiCapGPLXDaCo` (quốc gia cấp) = chuỗi rỗng theo số bằng (`''` một bằng, `'|'` hai bằng). **Không bao giờ NULL** (sửa 10/11/2026, CHANGES #98): phần mềm cũ luôn ghi chuỗi rỗng (DB Nạp 6.973 + DB đích 454 hồ sơ có GPLX, 0 dòng NULL); tool từng ghi NULL nên phần mềm cũ không hiện nơi cấp. *Vì sao: phần mềm cũ tách 7 cột theo `|` rồi ghép từng bằng, cột NULL làm lệch số phần.*
- Kiểm trong `dung_chuoi_gplx_da_co()`: `hang` thuộc tập mã, ngày `yyyymmdd` hợp lệ, không chứa `|`, tối đa 8 bằng, `so` ≤ 20 ký tự, `don_vi` mã 2 số, mỗi chuỗi nối ≤ 100 ký tự (`varchar(100)`, đã kiểm DB). Nạp lô: lỗi thành dòng `loi` của đúng học viên đó, không làm hỏng cả lô (`NapIn` chỉ kiểm hình dạng). Nạp đơn: 400. VPS dùng cùng quy tắc, sai → 422 ngay lúc gửi.

**Bảng hạng (phản chiếu ở `tool/webui` và `webapp`):**

| Nhóm | Nhãn → mã `DM_HangGPLX` |
|---|---|
| Luật mới | A1 → `A1m` · A → `A2` · A.01 → `A01` · A.02 → `A02` · B → `B1` · B.01 → `B11` · C1 → `C1` · C → `C` · D1 → `D1` · D → `D` |
| Luật cũ | A1 → `A1` · A2 → `A2` · A3 → `A3` · B1 số tự động → `B11` · B1 → `B1` · B2 → `B2` · C · D · E · FB2 · FC · FD · FE (giữ mã) |

Suy từ `KhoaHoc` thật (`B`→`B1`, `B.01`→`B11`, `C1`→`C1`) + mô tả danh mục; `A`→`A2`: 2 khóa `HangDT=Am` mang `HangGPLX=A2`, và `DM_HangGPLX` mô tả `A2` là "trên 125 cm3" đúng hạng A mới. `nhom` chỉ để hiển thị lại đúng nhãn, không ghi xuống DB.

**Ô nhập (dùng lại component có sẵn):** Hạng và Nơi cấp dùng `components/ComboLoc` (lọc theo `boDau` trên chuỗi hiện, nên đưa mã vào nhãn: `70 — Bình Phước (trước sáp nhập)` là gõ được cả mã lẫn tên). Ngày dùng `components/ODate` (`maskNgay` tự chèn `/`, có nút lịch). App web dùng `ODate` của `webapp` và một ô gõ tìm tương đương.

**Nơi cấp điền sẵn (CHANGES #98):** số GPLX đủ 12 chữ số và 2 số đầu có trong danh sách Nơi cấp → điền sẵn mã đó khi ô đang trống (hoặc đang do máy điền theo số cũ); nơi cấp người nhập chọn khác thì giữ. Đúng ở 94% hồ sơ DB Nạp (6.423/6.831), phần còn lại là bằng đổi tỉnh nên vẫn cho sửa. Hàm `suyNoiCapGplx` / `noiCapKhiDoiSo` có ở cả tool và app web; tool điền cả lúc mở hồ sơ và lúc nạp lô cho bằng app web gửi về thiếu nơi cấp.

**Danh sách Nơi cấp:** `DM_DonViGTVT` với `LoaiDV='SO'` (65 đơn vị). Đây là nguồn `usf_QuangLA_PM4_ThuNhanHS_getTenDVCap` dùng in tờ khai, và mọi mã trong dữ liệu cũ đều có. **Không dùng `DM_DVHC`:** cùng mã khác tên (`80` là Long An ở đây, Tây Ninh ở kia; `15`, `24`, `44`, `52`, `82`, `91` cũng khác). `@p_NoiCapGPLXDaCo` là mã nước ngoài cấp (`DM_QuocTich`), form cũ chỉ cho nhập một trong hai.

**Cục QLHC (user chốt, CHANGES #84):** mã `00`, khớp `DM_DVHC` ở cả DB Nạp và DB đích ("Cục Cảnh sát quản lý hành chính"). `DM_DonViGTVT` DB Nạp ghi `00` là "Tổng cục đường bộ Việt Nam" và tắt → chạy `scripts/them_cuc_qlhc_dm_donvigtvt.sql` để đổi tên + bật; tool đọc danh sách từ DB nên tự hiện sau khi chạy. **Chưa khớp:** `DM_DonViGTVT` DB đích ghi `00` là "Cục CSGT", script không đụng DB đích; Sync chỉ chép mã `00`. Hàm riêng `dvhc.ds_noi_cap_gplx()` + `GET /local/dvhc/noi-cap-gplx`, **không sửa `ds_so_gtvt`**; server dựng nhãn từ `TrangThai`. App web không đọc được SQL Server nên dùng bản chụp danh sách trong code (danh mục gần như không đổi).

**Miễn lý thuyết:** `usf_BaBT_GetMaNoidungSathach` / `usf_BaBT_GetNoidungSathach` (bản đang chạy) áp cho `A1`, `Am`, `A1m` khi `HangGPLXDaCo` chứa `B1`, `B11`…`B15`, `B2`, `C`, `D`, `E`, `FB2`, `FC`, `FD`, `FE` (dò `CHARINDEX`, nên chuỗi `A1|B2` vẫn khớp). UI chỉ báo, không tự đổi gì ở DB.

**Ca khó:**
- **Kéo lại từ VPS:** `keo_ve_upsert` làm tươi `keo_ve.gplx_da_co_json` khi dòng còn `cho`. Nháp khác NULL vẫn được ưu tiên (NULL = chưa sửa, `'[]'` = đã xóa hết, JSON = bản đã sửa). UI so nháp với `keo_ve`: khác nhau và VPS vừa đổi thì hiện cờ "App web có bản mới" + nút "Dùng bản app web" (đưa nháp về NULL). `goiNhap` gửi đủ trường mỗi lần lưu nên `nhap_luu` (`INSERT OR REPLACE`) không làm mất cột này. Sửa ở app web: `GET /cua-toi` trả kèm để form hiện đúng.
- **Sau khi nạp:** `keo_ve_cap_nhat(..., gplx_da_co_json=…)` ghi danh sách đã nạp TRƯỚC `nhap_xoa`, để chip + lọc tab Đã nạp vẫn đúng. Dòng `xong` không bị `keo_ve_upsert` đè. Gỡ về chờ nạp (QLY-08) rồi kéo lại thì lấy lại giá trị VPS (chấp nhận).
- **Chip + lọc:** `nhap_co` trả thêm `gplx_da_co_json`, `_KEO_COLS` thêm cột; dữ liệu nhỏ, không phải ảnh.
- **Quy tắc khớp form cũ** (chuỗi thông báo trong `FPT.GPLX.CSDT.dll`, đối chiếu 6.973 hồ sơ): bắt buộc hạng, số, ngày cấp, ngày trúng tuyển (0 hồ sơ thiếu); "GPLX hiện có không được chứa hạng cần cấp" (0 hồ sơ trùng) → **chặn**; ngày cấp không trước trúng tuyển (0 vi phạm), không sau hôm nay; hết hạn sau ngày cấp (4 vi phạm cũ); đủ 18 tuổi khi cấp. Trùng hạng và 18 tuổi chỉ kiểm ở tool (VPS chưa biết khóa). Số GPLX 98% dài 12 chữ số; khác thì nhắc, không chặn.
- **Migrate:** SQLite `keo_ve` + `nhap_chuan_bi` dùng guard `PRAGMA table_info` + `ALTER` như `ngay_cap`. VPS: `init.sql` chỉ chạy cho DB mới, nên API tự chạy `ALTER TABLE ho_so_thu_thap ADD COLUMN IF NOT EXISTS gplx_da_co JSONB` lúc khởi động, trước khi nhận truy vấn; checklist deploy kiểm `\d ho_so_thu_thap`. Model dùng `JSON().with_variant(JSONB, "postgresql")`.
- **PII:** `gplx_da_co` là dữ liệu cá nhân: `jobs/pii.py` dọn cùng số căn cước; xóa mềm hồ sơ (THU-05) đặt NULL, job 30 ngày dọn luôn dòng `deleted` (trước đó bỏ sót, còn giữ `so_cccd` mãi); không ghi vào audit/log; lỗi 422 không log giá trị trường này. Bản ở `keo_ve` máy tool cùng nhóm PII staging như `so_cccd`.

**Cách lưu nhiều bằng đã có bằng chứng:** form cũ có lưới `dgvsDSGPLXHienCo` + `btnThemGPLXHienCo`; hàm `getTenDVCap` nhận danh sách và giữ dấu ngăn (`70|79` → `Bình Phước|Hồ Chí Minh`); hồ sơ mẫu `A1|A1` (2023) đã qua BC2 `720/23` và có kết quả sát hạch `DA`. **Còn lại:** tờ khai in nguyên dấu `|` như hồ sơ cũ; `A`→`A2` đối chiếu ở nghiệm thu máy CSĐT. Cách làm và lý do: `TDD-decisions` §28.

### 10.7 Bổ sung GPLX sau khi đã nạp (QLY-10, TCB-05, THU-07 — CHANGES #89)
> **Phục vụ:** `QLY-10`, `TCB-05`, `THU-07`. *Vì sao ghi riêng 6 cột thay vì gọi lại SP gộp: nhánh cập nhật của SP xóa rồi tạo lại giấy tờ và ghi đè nhân thân, số hồ sơ; `usp_NguoiLX_HoSo_Update` ghi đè 65 cột.*

```
 App web (Đã nạp)                 VPS                          Tool (người nạp)
 Bổ sung GPLX ──PUT .../gplx──► ho_so_thu_thap.gplx_da_co
                                updated_at = now
                                trang_thai giữ 'imported'
                                       │  GET /api/nap/gplx-bo-sung
                                       └────────────────► so với DB Nạp theo ma_dk
                                                          và gplx_da_xu_ly (SQLite)
                                                                │ khác + chưa xử lý
                                                          cảnh báo, chip, bộ lọc
                                                                │ mở khối: tự điền, sửa
                                                          Lưu → UPDATE đúng 6 cột
                                                          Lưu/Bỏ qua → ghi dấu vân
```

Vòng đời cảnh báo của một hồ sơ:
```
[không cảnh báo] ──app web bổ sung──► [CẢNH BÁO] (khác DB, chưa có dấu vân)
      ▲                                   │ Lưu / Bỏ qua
      │ app web gửi bản khác              ▼
      └───────────────────────────── [ĐÃ XỬ LÝ] (có dấu vân của bản đó)

Mọi trạng thái: gỡ về chờ nạp hoặc job 30 ngày xóa dòng ─► biến mất
Khóa đã lập Báo cáo 1: vẫn CẢNH BÁO, khối chỉ xem, chỉ Bỏ qua dùng được
```

**VPS:**
- `PUT /api/ho-so/:uuid/gplx` (collector): nhận danh sách bằng, kiểm như `POST`, sai → 422; **danh sách rỗng → 422** (muốn xóa GPLX đã có trong DB thì làm ở tool). `pending` dùng `PUT /api/ho-so/:uuid` như cũ.
- Ghi bằng một `UPDATE … SET gplx_da_co, updated_at WHERE uuid AND created_by AND trang_thai='imported'`. `rowcount=0` thì đọc lại để trả 404 (không phải của mình) hoặc 409 (không còn đã nạp). Không đọc trước rồi ghi. Chỉ ghi 2 trường này; `updated_at` là mốc job 30 ngày, như ảnh §4.3. Không thêm cột.
- Cùng giao dịch, ghi `audit_log` với `hanh_dong='bo_sung_gplx'` + `uuid_hs`, không ghi giá trị GPLX. *Vì sao: đây là dấu hiệu duy nhất phân biệt bổ sung thật với hồ sơ chỉ có GPLX từ trước khi nạp.*
- `GET /api/nap/gplx-bo-sung?limit=&cursor=`: hồ sơ `imported` có `gplx_da_co` khác NULL **và có dòng `audit_log` `bo_sung_gplx` sau lần nạp gần nhất** (`created_at >= imported_at`, để gỡ về chờ nạp rồi nạp lại không báo nhầm); trả `uuid`, `ma_dk`, `gplx_da_co`, tên người gửi, `updated_at`, `co_tiep`. Sắp theo `(updated_at, uuid)` tăng dần; `cursor` là cặp giá trị cuối lượt trước; `limit` 1..500, mặc định 200. Tool key + `require_role('operator')` như `/api/nap/keo`. Không trả hồ sơ đã xóa, không ghi `gplx_da_co` vào log.

**Tool:**
- `nap.tach_chuoi_gplx(cot)`: 6 chuỗi `|` → danh sách, số phần lệch nhau thì giữ theo vị trí, thiếu để trống. Kiểm và ghép dùng lại `dung_chuoi_gplx_da_co` với hạng khóa + ngày sinh đọc từ DB. `nhom` không có trong DB: suy nhãn từ mã, không ảnh hưởng giá trị ghi.
- So sánh: chuẩn hóa hai bên qua hàm ghép, rồi so 6 chuỗi. `NoiCapGPLXDaCo` không so; khi lưu ghi lại chuỗi rỗng theo số bằng như lúc nạp (CHANGES #98).
- SQLite `gplx_da_xu_ly(uuid PK, dau_van, luc)`: `dau_van` = SHA-256 của `uuid` + JSON bản app web đã sắp khóa, chỉ để so khớp, không coi là che giấu. Dọn sau 30 ngày kể từ `luc`, cùng nhóm dữ liệu cá nhân ở máy tool. Cảnh báo hiện khi **khác DB và dấu vân chưa có**. Ghi dấu vân khi Lưu, Bỏ qua; không cần ghi lúc nạp. *Vì sao cần: người nạp được sửa trước khi lưu, nên DB có thể vẫn khác bản app web dù đã xử lý.*
- Thứ tự khi Lưu: ghi DB trước, ghi dấu vân sau. Ghi dấu vân lỗi chỉ log, không báo lỗi lưu; cảnh báo có thể hiện lại, không sai dữ liệu.
- Endpoint: `GET /local/ho-so/gplx-bo-sung` (danh sách + khóa + tên, hạng; không trả số GPLX) · `GET /local/ho-so/gplx-ban-web?ma_dk=` (bản app web đầy đủ để tự điền) · `GET|PUT /local/ho-so/gplx?ma_dk=` (`PUT` nhận `ban_web` để ghi dấu vân) · `POST /local/ho-so/gplx/bo-qua` (body `uuid`, `dau_van`) · `GET|PUT /local/sync/tra-cuu/gplx?ma_dk=&target_key=` · `GET /local/sync/tra-cuu/noi-cap-gplx`.
- Ghi: `UPDATE NguoiLX_HoSo SET` 6 cột `WHERE MaDK=%s AND` 6 cột bằng chuỗi thô đã đọc lúc mở (so `ISNULL(cot,'')`). API đọc trả kèm chuỗi thô, giao diện gửi lại nguyên văn khi lưu; không so bằng bản đã tách/ghép. Dữ liệu cũ lệch số phần `|`: hiện cảnh báo vàng, người dùng sửa rồi lưu theo đúng bản đang thấy. 0 dòng → 409 "dữ liệu vừa đổi, tải lại". Không đổi `TT_XuLy`. Danh sách rỗng → 6 cột NULL. Lưu xong cập nhật `keo_ve.gplx_da_co_json` nếu còn dòng, để chip tab Đã nạp đúng.
- Chặn: DB Nạp theo `BaoCaoI` như `/local/ho-so/sua`; DB đích theo `dkkh_exists_sql` + BC1 như `TCB-03`, `TCB-04`. Kiểm lại ở server lúc lưu, không chỉ khóa nút.
- Nhắc DB đích: dò học viên bằng cách dò trùng sẵn có của Sync; lỗi dò thì không nhắc, không làm hỏng lần lưu.

**Ca khó:**
- VPS lỗi hoặc tool chưa đăng nhập VPS: danh sách trả trạng thái "chưa kiểm được", không phải 0 hồ sơ. Nhập tay vẫn chạy.
- Khóa đã BC1: vẫn hiện trong danh sách, khối chỉ xem. "Bỏ qua" vẫn dùng được để hết cảnh báo.
- Tải danh sách: gom `ma_dk` một lần, mỗi lô tối đa 500 `MaDK`, đọc 6 cột + `MaDK`. Chạy khi mở màn và khi bấm tải lại, không thêm bộ nhớ đệm, không tạo index mới.
- `ma_dk` không có trong DB Nạp → hiện "Không tìm thấy trong DB Nạp", không tính vào số cảnh báo, vẫn cho Bỏ qua. Hai uuid cùng `ma_dk` → lấy bản `updated_at` mới nhất.
- Gỡ về chờ nạp (QLY-08): hồ sơ về `pending` nên tự ra khỏi danh sách.
- Không lấy được bản app web khi mở khối (vừa hết hạn, VPS lỗi): vẫn mở bản DB để nhập tay. Không đọc được khóa ở DB đích: chặn lưu.
- PII: ở tool, số GPLX chỉ trả cho giao diện ở endpoint một học viên; job 30 ngày dọn theo `updated_at`. Bổ sung 30 ngày chưa ai duyệt sẽ bị dọn cùng dòng và hết cảnh báo; người nạp vẫn nhập tay được.

### 10.8 Báo hồ sơ chưa nạp vừa được app web cập nhật (NAP-08 — CHANGES #92)
> **Phục vụ:** `NAP-08` (mở rộng `NAP-01`). *Vì sao so ngay lúc kéo mà không hỏi VPS "cái gì đổi": `/api/nap/keo` đã trả mọi hồ sơ `pending` kèm toàn bộ trường mỗi lần kéo, nên tool chỉ cần giữ bản lần trước và so; VPS không phải thêm bảng lịch sử.*

```
 App web (hồ sơ pending)         VPS /api/nap/keo                 Tool: keo_ve_upsert
 sửa thông tin / chụp lại ảnh ─► trả trường + co_anh              so với dòng keo_ve 'cho' đang có
 đổi GPLX                        + anh_luc (mốc file ảnh)                │ khác
                                                                          ▼
                                                              keo_ve_thay_doi (uuid, truong, luc)
                                                                          │
                                       GET /local/nap/thay-doi ◄──────────┘
                                       dải cảnh báo · danh sách · chip · lọc
                                       nháp giữ ảnh cũ ─► cảnh báo đậm ─► "Dùng ảnh mới" / "Giữ ảnh cũ"
```

**VPS:** `KeoOut` thêm `anh_luc: datetime | None` = giờ sửa file ảnh thô (`os.stat(anh_tho_path).st_mtime`, UTC), `None` khi chưa có ảnh hoặc không đọc được file. Không thêm cột, không đổi `ho_so_thu_thap`. *Vì sao không dùng `updated_at`: cột này cũng tăng khi khóa/mở khóa hồ sơ lúc nạp (`importing` ↔ `pending`), nên dùng nó để suy "ảnh đổi" sẽ báo nhầm sau mỗi lần nạp lỗi.* Dùng `stat` tối đa 500 lần mỗi lượt kéo, không đọc nội dung file.

**Tool:**
- SQLite `staging.sqlite`: cột mới `keo_ve.anh_luc TEXT` (ALTER có kiểm `PRAGMA table_info`, như `gplx_da_co_json`) và bảng mới `keo_ve_thay_doi(uuid TEXT PRIMARY KEY, truong TEXT NOT NULL, luc TEXT NOT NULL)`; `truong` là các mã ngăn bằng dấu phẩy, ví dụ `tt:ho_ten,tt:noi_tt,anh,gplx`. Dựng cùng chỗ tạo `keo_ve` bằng `CREATE TABLE IF NOT EXISTS`.
- Trong `keo_ve_upsert`, nhánh dòng đã có và còn `cho`: đọc các cột cũ trước khi `UPDATE`, so từng trường (`so_cccd`, `so_cmnd_cu`, `ho_ten`, `ngay_sinh`, `gioi_tinh`, `noi_tt_raw`, `ngay_cap`, `noi_cap_cccd`) → `tt:<tên>`; `gplx_da_co_json` khác → `gplx`; `co_anh` đổi hoặc `anh_luc` mới hơn lúc cũ → `anh`. Dòng mới thêm, dòng `xong`/`loi` không so. `anh_luc` cũ là NULL (máy vừa nâng cấp) hoặc VPS không trả `anh_luc`: không kết luận "ảnh", chỉ ghi `anh_luc` mới làm mốc.
- Có thay đổi: `INSERT … ON CONFLICT(uuid) DO UPDATE` gộp `truong` (hợp hai tập) và đặt `luc` = lúc kéo. Cùng giao dịch với `UPDATE keo_ve`.
- Dọn: cuối mỗi lượt kéo xóa dòng `keo_ve_thay_doi` mà `uuid` không còn dòng `keo_ve` trạng thái `cho` (đã nạp, đã bỏ qua, đã xóa ở app web). Không cần móc vào từng chỗ đổi trạng thái.
- Endpoint: `GET /local/nap/thay-doi` → `[{uuid, ho_ten, truong:[…], luc, nhap_giu_anh_cu}]` (tên trường dạng nhãn tiếng Việt do giao diện dịch, không trả giá trị); `nhap_giu_anh_cu` = có `anh` trong `truong` **và** nháp bền của uuid đang giữ ảnh đã xử lý (`jp2` hoặc `anh_preview`), tính lúc đọc nên tự tắt khi nháp đã bỏ ảnh · `POST /local/nap/thay-doi/da-xem` body `{uuids:[…]}` hoặc `{tat_ca:true}` · `POST /local/nap/nhap/{uuid}/bo-anh` (xóa riêng ảnh trong nháp, giữ địa chỉ, tick, nơi cấp; idempotent; cũng xóa dòng `anh` khỏi `truong`). Kết quả `POST /local/nap/keo` thêm `thay_doi` (số hồ sơ có dòng cảnh báo).
- Giao diện (`NapHoSo.tsx`): dải cảnh báo ở tab Cần xử lý (ẩn khi 0), bấm mở danh sách; chip "App web đã sửa" trên dòng; bộ lọc cùng số lượng; trong ngăn Chuẩn bị, banner đậm khi `nhap_giu_anh_cu`. "Dùng ảnh mới" gọi `bo-anh` rồi tải lại ảnh VPS qua `GET /local/nap/keo/{uuid}/anh`.

**Ca khó:**
- Đổi rồi đổi lại về như cũ giữa hai lần kéo: không thấy, chấp nhận. *Đánh đổi: không giữ lịch sử ở VPS để đổi lại không thêm cột và không thêm bảng.*
- Máy tool nâng cấp xong, lần kéo đầu: không báo ảnh; báo thông tin/GPLX chỉ khi so được với bản đã lưu.
- Tool mới với VPS cũ (không có `anh_luc`) hoặc VPS mới với tool cũ: không lỗi, chỉ không có cảnh báo ảnh. Thứ tự deploy: VPS trước, tool sau.
- Địa chỉ đổi: dòng `tt:noi_tt` ghi kèm "cần map lại" khi `nhap_reset_dia_chi` trả có reset.
- `Đã xem` rồi app web đổi tiếp: tạo lại dòng, báo lại.
- Lỗi khi ghi `keo_ve_thay_doi`: ghi log, không làm hỏng việc kéo (cảnh báo chỉ là thông tin phụ).
- VPS tạm không trả `anh_luc` (file ảnh thiếu, VPS bản cũ): giữ mốc đã có, không ghi đè bằng rỗng, để lần ảnh đổi sau vẫn bắt được.
- Nơi thường trú đổi mà nháp địa chỉ bị reset: luôn ghi cả `tt:noi_tt_raw` lẫn `dc_reset` (reset so chuỗi thô, so sánh trường có bỏ khoảng trắng đầu cuối), để dòng cảnh báo không bao giờ rỗng.
- Khôi phục hoặc sao chép thư mục ảnh thô trên VPS làm giờ sửa file đổi hàng loạt: tool báo "Ảnh" một lần cho mọi hồ sơ chờ nạp. Chấp nhận, bấm "Đã xem tất cả"; ghi vào tài liệu vận hành VPS.
- Chỉ so và báo hồ sơ `cho`. Hồ sơ `loi` không có cảnh báo (nhân viên đang xem lỗi của nó); nạp lại thành công thì cảnh báo chưa xem của nó mất theo.
- Giao diện chỉ nhận phản hồi mới nhất của danh sách cảnh báo (bộ đếm yêu cầu); "Đã xem" lỗi thì báo lỗi và cảnh báo vẫn còn. Số `thay_doi` trong kết quả kéo là tổng cảnh báo chưa xem, không phải số hồ sơ đổi riêng lượt này.
- PII: bảng chỉ chứa uuid, mã trường, giờ; không có giá trị cá nhân. Tên học viên lấy từ `keo_ve` lúc đọc.

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
- **(b) Kéo ảnh thô VPS:** tra `uuid` theo `ma_dk` (`vps.tra_uuid`, §4.4) → tải ảnh thô (`vps.tai_anh` / proxy `tai_anh_keo_ve`) → URL nạp vào `AnhModal.napTuUrl` (sẵn có) làm ảnh gốc. **Điều kiện:** ảnh thô còn trên VPS (bản gửi giữ ~30 ngày — §9.3/BR-016). Hết hạn/không tra được uuid → ẩn nguồn (b), chỉ còn (a), báo "ảnh gốc trên máy chủ đã hết hạn, chọn ảnh từ máy". **CHANGES #44:** ảnh thô VPS nay có thể là bản **collector chụp bù sau khi đã nạp** (app web cho chụp bù HV thiếu ảnh kể cả `imported` — §6.2/§4.3). Operator **tự lọc "Chưa ảnh" → mở HV → bấm kéo** (chốt A, không có cờ "ảnh mới" chủ động — xem TDD-decisions §18). *Đua ảnh (F5, ghi nhận):* kéo đọc ảnh thô **tại thời điểm bấm**; nếu collector ghi đè ảnh sau đó → operator **kéo lại** để lấy bản mới nhất. Không khóa — không hỏng dữ liệu (last-write-wins trên file, `importing` đã bị chặn nên không đụng vòng đời nạp).

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

**Luồng chụp bù ảnh HV ĐÃ NẠP — 3 hệ thống (CHANGES #44):**
```
  [App web - collector]          [VPS]                    [Tool - operator]
         │                         │                              │
   HV imported, thiếu ảnh          │                              │
         │                         │                              │
   bấm "Thêm ảnh" ────────────────▶│                              │
   POST /api/ho-so/:uuid/anh       │                              │
   (allowlist pending|imported;    │                              │
    created_by=mình)          ghi đè anh_tho_path                 │
         │                    (KHÔNG đổi trang_thai)              │
         │                    set updated_at=now (F4, gia hạn PII)│
         ▼                         │                              │
   ảnh thô mới trên VPS            │                              │
                                   │◀── operator lọc "Chưa ảnh" ──┤
                                   │    mở HV → bấm kéo (QLY-05 b)│
                                   │    tra uuid theo ma_dk        │
                                   │─── tải ảnh thô ─────────────▶│
                                   │                     AnhModal: chỉnh/đổi nền
                                   │                              │
                                   │                     ghi .jp2 + UPDATE
                                   │                     TT_XuLy '01'→'03'
                                   │                              ▼
                                   │                        ảnh vào DB thật

  Chốt A (không cờ ảnh-mới): operator TỰ lọc "Chưa ảnh" rồi kéo — VPS không
  báo chủ động HV nào có ảnh mới (TDD-decisions §18). Ảnh chỉ vào DB thật
  SAU bước operator duyệt ở AnhModal (F6: có người kiểm giữa).
```

### 11.6 Đổi nền trắng cả khóa (QLY-07) — CHANGES #22
Xử lý hàng loạt ảnh của 1 khóa (chủ yếu ảnh cũ từ app cũ chưa nền trắng). **Giữ `TT_XuLy`** — bắt buộc, vì bulk chạm MỌI HV trong khóa cùng lúc; nếu hạ `'03'` thì **cả khóa đã BC2 biến mất khỏi báo cáo** trong một lần chạy.
- **Ghi ảnh = ghi đè ĐÚNG file ở `DuongDanAnh` hiện có (sửa 12/10/2026, CHANGES #67).** Hai DB Nạp và đích dùng chung một file vật lý (sync sao chép `DuongDanAnh` nguyên văn; đọc DB 12/10: 668/741 đường dẫn ở đích trùng đường dẫn ở Nạp), nên đổi nền **không** dùng `ghi_anh_update` (hàm đó ghi vào `<IMG_PATH_CSDT>\<MaKH>\<MaDK>.jp2` và UPDATE `DuongDanAnh` — với ảnh ở gốc khác sẽ tạo file mới + lệch đường dẫn giữa 2 DB). Đổi nền dùng cùng kiểu ghi với `thay_anh_ghi_de` (TCB-02): file tạm cùng thư mục → `os.replace` ghi đè, **giữ nguyên tên và `DuongDanAnh`**; chỉ `UPDATE ChatLuongAnh, NgayThuNhanAnh, NguoiThuNhanAnh` (không đụng `DuongDanAnh`, không đụng `TT_XuLy`). `ghi_anh_update` giữ nguyên cho nạp/thay ảnh HV mới (QLY-05).
- **Chạy nền + tiến độ:** endpoint khởi tạo job (vd `POST /local/khoa/:ma_kh/doi-nen`) → xử lý tuần tự từng HV, UI hỏi tiến độ (N/tổng, số lỗi) qua polling hoặc SSE. ~1-3 giây/ảnh (rembg) × ~100 HV ≈ vài phút → KHÔNG làm đồng bộ (treo UI).
- **Sao lưu trước ghi đè:** tùy chọn (mặc định bật) chép `.jp2` gốc sang `<tên>_BACKUP.jp2` **CÙNG thư mục với file ảnh** (cùng kiểu TCB-02) — **CHỈ chép nếu `<tên>_BACKUP.jp2` CHƯA tồn tại** (giữ bản gốc đầu tiên; lần chạy sau KHÔNG ghi đè backup, tránh backup thành bản đã xử lý → mất bản gốc thật). *Đã từng chốt (CHANGES #22):* `<IMG_PATH_CSDT>\<MaKH>\_BACKUP\<MaDK>.jp2` — bỏ 12/10/2026 vì tạo thêm thư mục ở gốc khác và lệch với TCB-02. Ghi ảnh **atomic** (file tạm → `os.replace`).
- **Phạm vi:** mặc định "chỉ ảnh chưa nền trắng" — phát hiện bằng **heuristic lấy mẫu pixel 4 góc** (gần trắng → coi đã trắng, bỏ qua; DB không có cờ đánh dấu); sai sót nhỏ bù bằng tùy chọn **"tất cả HV có ảnh"** (luôn cho đổi). HV không ảnh → bỏ qua.
- *Ca lỗi từng HV* (file bị khóa app cũ, thư mục không ghi được, ghi lỗi) → bỏ qua HV đó, ghi danh sách lỗi, chạy tiếp — 1 HV lỗi không hỏng cả lô.
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
  - **(CHANGES #40, 06/10 — đảo nguồn nơi cấp + mở rộng QLY-01):** "Nơi cấp căn cước" đọc/lưu theo **`DM_DVHC.MaDvhc`** (mã 2 ký tự: tỉnh TW/TI active + nhóm Cục 'C' gồm `'00'`='Cục QLHC'), **KHÔNG** `DM_DonViGTVT` (ở đó '00'=Cục CSGT/Tổng cục đường bộ — lệch nghĩa; app CSDT cũ tra `DM_DVHC` ra "Cục QLHC"). `ds_so_gtvt` đổi sang `DM_DVHC`; 3 chỗ hiển thị (`hoso.py`, `sync_tracuu.py` list+chi tiết) đổi join `DM_DVHC.TenNganGon` (scalar subquery, tránh BUG-11). `suy_noi_cap`/`suyNoiCap`: **CCCD 12 số → '00' Cục QLHC** (cấp tập trung), CMND 9 số → '' chọn tay. **Tiền đề đã chạy:** `DM_DVHC` DB nguồn trước đó mã tỉnh đều `TrangThai=0` + không có '00' → đồng bộ đích→nguồn `update/sync-DM_DVHC-tu-DB-dich-sang-DB-nap.sql` (MERGE cặp PK `(MaDvhc,MaDVQL)` + `COLLATE` cross-DB, UPDATE 15.744 + INSERT 11, **không DELETE** → không đụng 4 FK; backup `DM_DVHC_backup_20261006`). **Mở rộng sang Nạp QLY-01** (đảo #37 "giữ 5 trường"): `hoso.py` `HoSoSua`+4 trường + `dung_tham_so_update` overlay bỏ-trống-giữ-cũ (`_giu_cu`) + `chi-tiet` trả 4 mã preselect; `TraCuuDB.tsx` +combo (`/local/dvhc/*` trỏ DB Nạp). **Guard BC1 (409) GIỮ NGUYÊN** trên đường lưu `sua_ho_so`. **Edge xã cũ trước sáp nhập áp CẢ QLY-01 lẫn TCB-03:** HV cũ có `NoiTT_MaDVHC` là xã trước 2025 → combo Xã hiện trống; không đụng = giữ mã cũ (bỏ-trống-giữ-cũ), không bắt nhập lại. **⚠️ Rủi ro mã '00' đa nghĩa — xem §16 Risks** (NoiCapCMT='00' hiển thị đúng qua `DM_DVHC` nhưng view CDB nào tra qua `DM_DonViGTVT` ra "Cục CSGT").
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

## 11D. Cập nhật kết quả đào tạo (tool — workspace riêng) — KQD-01..10 (CHANGES #42, #45, #53, #65, #69, #72, #75, #77)

> Ghi **CSDL đích** `GPLX_CDB_CSDT` (bảng `NguoiLX_HoSo`) như SYNC/TCB. Chỉ nhập KQĐT (`TT_XuLy` 03→09/10), **không** kết xuất XML. Schema đã probe: `docs/DB-GPLX_CDB_CSDT.md` §5. Quyết định kỹ thuật: TDD-decisions §17.

### 11D.0 Kiến trúc & SP dùng
- Module tool riêng (`routers/ketqua.py` + `ketqua_service.py` + `ketqua_quydoi.py`) — **không import** module Nạp/Sync. Kết nối đích tái dùng `db.sqlserver_conn_dich(target_key)` (§11B.1).
- **Băng DB đích** (yêu cầu #2): component header dùng chung với Sync (Sync đã có "banner nhắc DB đích") — hiện `GPLX_CDB_CSDT · <host> · CSĐT <mã>`.
- SP đích (verify 06-07/10/2026 trên `GPLX_CDB_CSDT`, **không tự chế UPDATE thô khi đã có SP phù hợp**):
  - Đọc danh sách (lưới KQD-01): **SELECT tự viết trên `conn_dich`** như màn Tra cứu CDB (`sync_tracuu.py`), lọc thẳng `TT_XuLy` cho đúng 4 nhóm PRD (03/04 · 09/10 · 14 · 90 · tất cả). **KHÔNG dùng SP đọc** `_CNKQDT`/`_NguoiLX_KetQuaDaoTao_CSDT` cho lưới: tham số `@TrangThai` của SP gộp "Đã cập nhật" chỉ trả HV **Đạt (09)**, bỏ sót **Không đạt (10)** — lệch nhóm 09/10 PRD (quyết định khi code 07/10, user chốt A). SP `_CNKQDT` chỉ tham khảo danh sách cột cần hiển thị. · 1 HV (form sửa KQD-02/04): `usp_NguoiLX_KetQuaDaoTao_CSDT_GetHocVien` (verify 07/10: trả `GiaiTrinh`, `DiemKQ*`, giờ/km, `SoGiayCNTN`, ngày khóa → prefill form), hoặc SELECT tự viết nếu cần cột ngoài SP.
  - Ghi điểm: `usp_NguoiLX_KetQuaDaoTao_CSDT_CapNhat` (**18 tham số** — verify 07/10, bản cũ ghi nhầm 19; `BEGIN TRAN` + `ROLLBACK` khi `@@ERROR`; `NgaySua=GETDATE()`; `WHERE MaDK=@MaDK AND MaKhoaHoc=@MaKH`). Chuyển trạng thái trong SP: `CASE WHEN TT_XuLy IN ('90','13','14') → giữ nguyên; @KetLuanCSDT='1' → '09'; '0' → '10'; else giữ`.
  - ⚠️ **SP KHÔNG bảo vệ `TT_XuLy='12'`** (đã kết xuất gửi Sở): gọi `_CapNhat` vào HV `12` sẽ **kéo lùi 12→09**, lệch với hồ sơ Sở đã nhận. App **BẮT BUỘC** chặn gọi SP cho HV `12`/`13` — hàng chỉ-đọc, nút Lưu mờ (khớp PRD KQD-02). Chỉ `90/13/14` được SP giữ nguyên tự động. **Ngoại lệ duy nhất cho `12`:** luồng "Mở khóa để sửa" (KQD-05, §11D.7) — gỡ chặn **có kiểm soát** chỉ khi khóa còn gói chưa gửi. `13` khóa tuyệt đối, không có ngoại lệ.
  - **Ghi giải trình (KQD-04):** SP `_CapNhat` **không** có tham số ghi `GiaiTrinh`/`LyDoTuChoiKQDT`. Cột `GiaiTrinh nvarchar(1000)` có sẵn trong `NguoiLX_HoSo` nhưng không SP nhập-liệu nào ghi → KQD-04 ghi bằng **`UPDATE` tham số hóa riêng cột `GiaiTrinh`** (pymssql `%s`, `WHERE MaDK=%s AND MaKhoaHoc=%s`, validate `len ≤ 1000` phía app), **chạy TRƯỚC khi gọi `_CapNhat`** trên cùng `sqlserver_conn_dich(target_key)`: lỗi ở bước GiaiTrinh thì chưa đụng điểm/trạng thái (HV vẫn 14/90, báo lỗi sạch); giải trình ghi xong mà SP lỗi thì vô hại (trạng thái chưa đổi, lần sau ghi đè). `LyDoTuChoiKQDT` (lý do Sở từ chối) do luồng Sở ghi — read SP `_GetHocVien`/`_CNKQDT` **không** trả cột này, cần `SELECT` riêng nếu KQD-04 muốn hiển thị cho nhân viên đọc.

### 11D.1 Máy trạng thái TT_XuLy (DM_TrangThai)
`03`/`04` Đã đăng ký khóa học → `09` Đã cập nhật KQ (Đạt) / `10` (Không đạt) → `12` Đã kết xuất gửi Sở (**do PM cũ**) → `13` Hoàn thành / `14` Sở từ chối / `90` Đang giải trình. Tool đi 03→09/10 (KQD-02), sửa lại 14/90 (KQD-04) và **chuyển 14→90 khi HV đã sửa xong + Đạt + có giải trình (KQD-04, CHANGES #77)** — SP không bao giờ tự đặt `90`, nên bước này do tool UPDATE trực tiếp, có guard SQL (§11D.13). Lọc màn KQD-01 map: Đã đăng ký=03/04 · Đã cập nhật=09/10 · Sở từ chối=14 · Giải trình=90.

```
 ┌───────────────────── TOOL (máy CSDT) ─────────────────────┐   ┌──── NGOÀI TOOL (PM cũ / Sở) ────┐
 │                                                            │   │                                 │
 │   03/04 ──┬── Đạt (KetLuan=1) ──►  09 Đã cập nhật KQ ──────┼───┼─► 12 Đã kết xuất ──► 13 Hoàn thành│
 │  Đã đăng  │   [KQD-02]                                     │   │   gửi Sở            (Sở duyệt)   │
 │  ký khóa  └── Trượt (KetLuan=0) ►  10 Không đạt ───────────┼───┤      │                           │
 │                                                            │   │      ├─► 14 Sở từ chối           │
 │   14 ──► sửa điểm + giải trình ──► 90 (tool UPDATE, #77) ──┤   │      └─► ❔ 90 (ai đặt: §11D.13)  │
 │   [KQD-04]                                                 │   │                                 │
 │                                                            │   └─────────────────────────────────┘
 │   ✗ TUYỆT ĐỐI không gọi _CapNhat cho 12 / 13 (SP không     │        14/90 quay lại tool để sửa ──┐
 │     bảo vệ 12 → kéo lùi 12→09). Hàng chỉ-đọc.              │◄───────────────────────────────────┘
 │   ⟳ NGOẠI LỆ 12 → 09/10 (KQD-05, §11D.7): "Mở khóa để sửa" │
 │     khi CƠ SỞ còn gói kết xuất chưa gửi → lùi MỌI HV 12    │
 │     của cơ sở (mọi khóa) về 09/10. Ngoại lệ DUY NHẤT; 13 ✗ │
 └────────────────────────────────────────────────────────────┘
```

> Mũi tên `12 → 09/10` chỉ mở qua `POST /local/ketqua/mo-khoa` (KQD-05), **mức CƠ SỞ** — không phải đường đi thường của KQD-02/04.

**Nhánh Sở từ chối / Đang giải trình (KQD-04 đổi, CHANGES #77 — sau `/reviewtdd` §11D.13):**

```
  Đã gửi Sở(12) ─(Sở từ chối)─► Sở từ chối(14) ─┬─ sửa điểm: Đạt + có giải trình ─► Đang giải trình(90) ─(PM CDB kết xuất lại)─► Đã gửi Sở(12)
                                                │      [tool tự chuyển; guard SQL: đang 14 + KetLuanCSDT=1 + GiaiTrinh<>'']
                                                ├─ Đạt, thiếu giải trình ─► giữ 14 (nhắc ghi giải trình)
                                                └─ Không đạt ─► giữ 14 (CDB không kết xuất HV Không đạt)
  Đang giải trình(90) ─(sửa điểm tiếp)─► giữ 90   ⚠ nếu thành Không đạt/trống kết luận: vẫn 90, KHÔNG kết xuất được → chip đỏ "Cần xử lý" (§11D.13)
  ❔ "12 → 90" do phần mềm CDB đặt hay không: chưa xác minh (nghiệm thu máy CSĐT, BUILD-PLAN task 145)
```

### 11D.2 Quy đổi điểm (từ "Sổ theo dõi KQ học tập TT17")
Nhân viên nhập **điểm gốc**, app quy đổi /10, GHI 5 điểm per-môn (KHÔNG ghi trung bình):

| Môn (UI) | Nhập gốc | Cột DB | Ngưỡng | Tối đa |
|---|---|---|---|---|
| Lý thuyết | số câu đúng | `DiemKQLyThuyet` | theo hạng | tổng câu theo hạng |
| Mô phỏng | /10 | `DiemKQMoPhong` | 5 | 10 (nhập thẳng) |
| Sa hình (liên hoàn) | /100 | `DiemKQHinh` | 80 | 100 |
| Tiến lùi chữ chi | /10 | `DiemKQTienLui` | 5 | 10 (nhập thẳng) |
| Đường trường | /100 | `DiemKQThucHanh` | 80 | 100 |

Công thức (2 đoạn tuyến tính, ngưỡng=5,0): `gốc≥ngưỡng → 5+(gốc−ngưỡng)/(tối đa−ngưỡng)×5` ; `gốc<ngưỡng → gốc/ngưỡng×5`. Kiểm khớp file: LT 28/30(ng.27)→6,7 · liên hoàn 84→6,0 · đường 85→6,3.

**Xét Đạt (§11D.4) trên giá trị quy đổi THÔ chưa làm tròn** (tương đương so `gốc ≥ ngưỡng gốc`); **chỉ làm tròn 1 chữ số khi hiển thị và ghi `DiemKQ*`**. Tránh ca gốc dưới ngưỡng mà làm tròn lên 5,0 bị tính Đạt nhầm — vd sa hình gốc 79,2 (ngưỡng 80) → quy đổi 4,95 → làm tròn 5,0: xét trên 4,95 là **Trượt** (đúng), xét trên 5,0 là Đạt (sai).

Tham số Lý thuyết theo hạng + giai đoạn (cờ CŨ/MỚI tích chọn theo khóa — §11D.4):

| Hạng | Giai đoạn | Tổng câu | Ngưỡng | Căn cứ |
|---|---|---|---|---|
| B | CŨ | 30 | 27 | TT 12/2025/TT-BCA |
| C1 | CŨ | 35 | 32 | TT 12/2025/TT-BCA |
| B | MỚI | 50 | 45 | TT 108/2026/TT-BCA |
| C1 | MỚI | 60 | 54 | TT 108/2026/TT-BCA |

### 11D.3 Giờ/quãng đường thực hành (TT 17/2026/TT-BXD)
Phân biệt hạng B tự động (`MaHangMoi='B.01'`/`MaHang='B11'`) vs sàn (`B`/`B1,B2`) vs `C1`.

| Hạng | Giờ sân `TGThucHanhHinh` (khóa cứng) | km sân `QDThucHanhHinh` (điền sẵn) | Giờ đường `TGThucHanhDuong` (trống, gợi ý ≥½) | km đường `TongQDThucHanh` (trống, gợi ý ≥) |
|---|---|---|---|---|
| B.01 (tự động) | 34 | 240 | ≥12 | ≥710 |
| B (sàn) | 34 | 240 | ≥20 | ≥810 |
| C1 | 35 | 225 | ≥24 | ≥825 |

Chỉ **km sân** điền-sẵn-cho-sửa; **giờ sân** khóa cứng; **giờ/km đường** để trống + placeholder tối thiểu (dưới ngưỡng → cảnh báo vàng, không chặn).

**Hạng không xác định** (`MaHangMoi` NULL/rỗng ở dữ liệu cũ — SP lưới mặc định nhóm 3=ô tô): **không** điền-sẵn/khóa-cứng giờ-km, để nhân viên tự nhập + cảnh báo "không xác định hạng từ dữ liệu"; không đoán bừa 34h/240km.

### 11D.4 Kết luận Đạt + 3 cờ bit (app tự tính)
DB **không có** trigger/computed/constraint tính 3 cờ (verify 06/10: 0 trigger, 3 cột bit rỗng, 2 SP CapNhat chỉ lưu nguyên tham số) → **app tính rồi truyền `@KQLyThuyet/@KQThucHanh/@KetLuanCSDT`** (`'1'/'0'`). Quy tắc **từng môn ≥5** (user chốt A, bỏ điểm liệt/loại trực tiếp):
- `KetLuanCSDT`=1 ⇔ cả 5 môn quy đổi ≥5
- `KQLyThuyet`=1 ⇔ LT≥5 **và** Mô phỏng≥5
- `KQThucHanh`=1 ⇔ Sa hình≥5 **và** Chữ chi≥5 **và** Đường≥5

**Cờ CŨ/MỚI chương trình lưu phía tool** (không đụng schema CDB): map `MaKH → cũ/mới` trong SQLite/JSON cấu hình tool (như `dvhc_map`); mặc định CŨ. *Vì sao: sau 01/03/2027 khóa cũ + mới chạy song song, cắt theo ngày kiểm tra sẽ quy đổi LT sai hàng loạt; DB đích không có cột cho cờ này.*

### 11D.5 Số giấy HTKH + các trường tự điền
`SoGiayCNTN` = `MaDK + '-' + MaHangMoi` (verify 100% mẫu thật, vd `75032-20260803-000001-B`), tự sinh khi Đạt. `NgayRaQDTN`, `TGBatDau`, `TGKetThuc` điền sẵn từ ngày khóa (`KhoaHoc.NgayKG/NgayBG/NgayThi`), cho sửa.

### 11D.6 API (tool, đề xuất — chốt khi code)
`GET /local/ketqua/khoa?q=` (gợi ý khóa đã BC1, kèm đếm HV 5 nhóm trạng thái gồm **`ketxuat`=12**) · `GET /local/ketqua/hoc-vien?ma_kh&trang_thai&q` (lưới; `trang_thai` nhận cả `ketxuat` (12) cho KQD-03) · `POST /local/ketqua/cap-nhat` (1 HV: điểm gốc + hạng + cờ chương trình → app quy đổi → ghi `GiaiTrinh` trước (nếu có) → gọi SP) · **`GET /local/ketqua/mo-khoa`** (KQD-05/03 — cổng B-1 **chỉ đọc**: trả `mo_duoc` + `goi_chua_gui`/`goi_da_gui` (mỗi gói: id·ten_file·ngay_tao·kich_thuoc) + `so_hv_mo`/`so_hv_bo_qua`/`so_khoa`; panel gói KQD-03 + modal mở khóa KQD-05 dùng chung) · `POST /local/ketqua/mo-khoa` (KQD-05, §11D.7) · `POST /local/ketqua/xoa-diem` (KQD-06, §11D.8 — reset HV 09/10 về chưa có điểm; sửa lẻ dùng lại `/cap-nhat` với quy-đổi môn cũ) · **`POST /local/ketqua/mo-sua-sau-gui`** (KQD-05 #53, §11D.7b — body `ma_dk[]` + `ly_do`; lùi đúng các HV được chọn, không xóa gói) · **`GET /local/ketqua/sua-sau-gui`** (khối đỏ KQD-03: nhật ký ∩ HV chưa về `12`) · **`GET /local/ketqua/kiem-truoc?ma_kh=`** (KQD-07, §11D.9, chỉ đọc). **`POST /local/ketqua/xuat-excel?ma_kh=`** (KQD-09, §11D.11 — dựng `.xlsx` kết quả học tập của khóa và **lưu vào thư mục `output`**, chỉ SELECT DB) · **`POST /local/ketqua/mo-thu-muc-xuat`** (mở thư mục output) · **`POST /local/ketqua/xuat-so-theo-doi?ma_kh=`** (KQD-10, §11D.12 — Sổ theo dõi mẫu Phụ lục VI, lưu vào `output`) · **`POST /local/ketqua/giai-trinh-lo`** (KQD-04 #77, §11D.13 — giải trình + chuyển `14`→`90` hàng loạt, một giao dịch) · **`GET`/`PUT /local/ketqua/mau-giai-trinh`** (mẫu giải trình lưu phía tool, **theo `target_key`**, kèm `phien_ban`; §11D.13) · **`POST /local/ketqua/dat/xem-truoc`** + **`POST /local/ketqua/dat/luu`** (KQD-08, §11D.10 — nạp giờ/km đường từ PDF DAT: xem trước chỉ đọc, lưu một transaction chỉ 2 cột) · **KQD-03 "Theo dõi kết xuất" KHÔNG có endpoint `ket-xuat` riêng** (chốt khi code): tiến độ khóa ghép từ `/khoa` (đếm sẵn), panel gói từ `GET /mo-khoa` (CSĐT-wide, tải 1 lần), lưới HV từ `/hoc-vien?trang_thai=ketxuat|capnhat` — tránh thừa endpoint + khỏi nhồi danh sách gói vào mỗi lần chọn khóa. Tất cả gác session + `target_key` như §11B. **Combobox khóa:** debounce ~300ms + giới hạn ~20 gợi ý, chỉ đếm HV-theo-trạng-thái cho khóa thực sự hiển thị (tránh aggregate nặng mỗi phím gõ).

### 11D.7 Mở khóa để sửa sau kết xuất (KQD-05) — gỡ chặn `12` có kiểm soát
> Nghiệp vụ + lý do (DB không nối HV↔gói): TDD-decisions §19. Verify DB live 07/10/2026 trên `GPLX_CDB_CSDT`.

- **Cổng B-1 (chỉ đọc, quyết định bật nút):** `EXISTS (SELECT 1 FROM dbo.TRANS_CLI_HangDoiGui WHERE KieuDuLieu='KET_QUA_DAO_TAO' AND NoiGui=@MaCSDT AND TrangThai='0')`. **Lọc theo `NoiGui`=mã CSĐT** (cột chuẩn, verify: gói 75032 có `NoiGui='75032'`), **KHÔNG** parse tên file. Né dữ liệu CSĐT khác lẫn máy dùng chung (hiện 61 gói `TrangThai='0'` là `NguoiTao='ADMIN'`/CSĐT 24005). `@MaCSDT` = `QTHT_ThamSoHT.MA_CSDT` (như các module khác). `TrangThai`: `0`=chưa gửi · `1`=đã gửi (đối chiếu DKKH 05/10).
- **`POST /local/ketqua/mo-khoa` (body: `ma_kh` để ghi log/ngữ cảnh):** thao tác **mức CƠ SỞ** (review #2 — vì xóa gói buộc phải quét cả CSĐT, nên lùi HV cũng phải cả CSĐT để không rò treo sang khóa khác). Trong một `sqlserver_conn_dich` (autocommit). **Thứ tự: LÙI HV TRƯỚC, XÓA GÓI SAU** — nếu xóa gói lỗi giữa chừng thì HV đã về 09/10 (sửa được) + cổng B-1 còn mở để chạy lại, tránh kẹt "12 không gói"; khớp edge PRD KQD-05 ("xóa gói xong lỗi → HV đã lùi vẫn sửa được"). Đổi so với bản đầu (xóa trước) sau khi code:
  1. Kiểm cổng B-1; không còn gói chưa gửi → trả **409** kèm danh sách gói đã gửi (cho UI hiện thông báo M1). KHÔNG đổi gì.
  2. **Lùi MỌI HV `TT_XuLy='12'` của CƠ SỞ** (mọi khóa) về 09/10 — khớp phạm vi xóa ở bước 3, tránh HV khóa khác treo "12 không gói". 1 `UPDATE` tham số hóa: `UPDATE NguoiLX_HoSo SET TT_XuLy = CASE WHEN KetLuanCSDT=1 THEN '09' WHEN KetLuanCSDT=0 THEN '10' END, NgaySua=GETDATE()[, GiaiTrinh=@gt] WHERE MaCSDT=@MaCSDT AND TT_XuLy='12' AND KetLuanCSDT IS NOT NULL` (ghi `GiaiTrinh` cho mọi HV được lùi nếu UI gửi). **`KetLuanCSDT IS NOT NULL`** (review #3): HV `12` mà `KetLuanCSDT` NULL là bất thường (đã kết xuất ắt có kết luận) → **bỏ qua + ghi cảnh báo**, KHÔNG ép về '10' (tránh gán Không-đạt oan).
  3. **Xóa từng gói** `KET_QUA_DAO_TAO` `NoiGui=@MaCSDT` `TrangThai='0'` qua `usp_TRANS_CLI_HangDoiGui_Delete(@Id)` (SP = `DELETE WHERE Id=@Id`). Xóa quét cả CSĐT (không lọc được theo khóa — gói không nối khóa).
  4. Trả số HV đã mở + số khóa ảnh hưởng + số HV bỏ qua + số gói đã xóa.
- **Sau khi mở:** HV về 09/10 → sửa điểm bình thường qua KQD-02 → nhân viên **kết xuất lại ở PM CDB cũ** (tool không sinh XML).
- **Bất biến:** chỉ mở `12`; `13` tuyệt đối không; thao tác **mức CƠ SỞ** (không mổ xẻ 1 HV, không giới hạn 1 khóa — vì không biết HV/khóa nằm gói nào). Modal **phải nói rõ "mở khóa toàn bộ HV đã kết xuất chưa gửi của cơ sở (N người · M khóa)"**, không chỉ HV/khóa đang xem. Nút "Mở khóa" hiện ở cả màn KQD-02 (dòng 🔒) và KQD-03.

### 11D.7b Sửa sau khi đã gửi Sở — chọn từng HV (KQD-05 mở rộng, CHANGES #53)
> Lý do + phương án: TDD-decisions §21. Verify DB 10/10/2026: `usp_CSDT_PheDuyetKQDT_TiepNhan` có `SELECT … WHERE MaDK=@MaDK AND TT_XuLy='12'`, không thấy thì `RAISERROR` → phản hồi Sở chỉ khớp HV đang `12`. Gói KQĐT 75032 hiện cả 2 `TrangThai='1'`.

- **Điều kiện bật (UI + backend kiểm lại):** cơ sở **không còn** gói `KET_QUA_DAO_TAO` `NoiGui=@MaCSDT` `TrangThai='0'` (dùng lại `_SQL_GOI_KQDT`). Còn gói chưa gửi → 409 `con_goi_chua_gui`, chỉ dùng lối mở khóa §11D.7 (xóa gói chưa gửi để không mang điểm cũ).
- **`POST /local/ketqua/mo-sua-sau-gui`** body `{ ma_dk: string[] (1..200), ly_do: string (1..1000) }`:
  1. Kiểm điều kiện bật. Mỗi `ma_dk` SELECT `TT_XuLy, KetLuanCSDT, Diem*…` — không tìm thấy → bỏ qua kèm lý do; `13` → **409**; không phải `12` → bỏ qua.
  2. **Ghi nhật ký TRƯỚC** (sqlite phía tool, bảng `sua_sau_gui`: `ma_dk, ma_kh, ho_ten, diem_truoc_json, ly_do, nguoi, luc_mo, trang_thai` `cho_kx`/`da_kx`) — nếu ghi lỗi thì chưa đụng DB đích.
  3. **UPDATE tham số hóa theo từng `MaDK`:** `SET TT_XuLy = CASE WHEN KetLuanCSDT=1 THEN '09' WHEN KetLuanCSDT=0 THEN '10' END, GiaiTrinh=@ly_do, NgaySua=GETDATE() WHERE MaDK=@MaDK AND TT_XuLy='12' AND KetLuanCSDT IS NOT NULL`. KHÔNG gọi SP `_CapNhat`, KHÔNG xóa gói. Không dựa `rowcount` (SELECT lại trạng thái để báo kết quả từng HV — như `xoa_diem`).
  4. Trả `{mo: [...], bo_qua: [{ma_dk, ly_do}]}`.
- **`GET /local/ketqua/sua-sau-gui`:** đọc nhật ký `trang_thai='cho_kx'`, JOIN trạng thái hiện tại từ DB đích; HV đã về `12` → tự đánh `da_kx` (dòng biến khỏi khối đỏ). Trả kèm điểm hiện tại để UI hiện "trước→sau".
- **Sửa/bổ sung điểm:** dùng lại `/cap-nhat` (HV đã về 09/10; ô trống giữ quy đổi cũ nhờ `giu_quydoi` KQD-06). Không đổi gì ở `/cap-nhat`.
- **Bất biến:** chỉ HV được chọn; `13` không bao giờ; KHÔNG sinh/ký XML (file KQĐT ký số RSA bằng khóa phần mềm CDB — tool không có và không được dùng khóa đó); mọi SQL tham số hóa; lý do ≤1000 (như `GiaiTrinh nvarchar(1000)`).
- **Rủi ro biết trước:** Sở trả 13/14 cho HV đang mở-sửa → SP tiếp nhận báo lỗi, HV kẹt (xử lý bằng cảnh báo + khối đỏ nhắc, không chặn). HV mở sửa mà không sửa gì rồi kết xuất lại → Sở nhận 2 bản (hỏi hỗ trợ CDB).

### 11D.8 Sửa lẻ / xóa điểm đã lưu (KQD-06) — chỉ HV chưa kết xuất (09/10)
> Phát sinh sau khi dùng thử KQD-02 (CHANGES #48). Verify DB 07/10: không có SP reset KQĐT; cột `DiemKQ*` (float) + 3 cờ bit + `SoGiayCNTN` nullable; `TT_XuLy` NOT NULL (set `'03'` được).

- **Phạm vi:** chỉ HV `TT_XuLy` **09/10** (đã cập nhật, chưa gửi Sở). `12` phải mở khóa (§11D.7) trước; `13` khóa tuyệt đối; `14`/`90` sửa qua KQD-04. **Chặn backend khác nhau theo thao tác** (do dùng chung endpoint):
  - **Xóa điểm** — endpoint riêng `/xoa-diem`, mệnh đề `WHERE ... TT_XuLy IN ('09','10')`: ngoài 09/10 → 0 dòng → **409**. Chặn cứng ở backend.
  - **Sửa lẻ** — dùng **chung** `/cap-nhat` với KQD-02 (nhập điểm lần đầu, HV `TT=03`) và KQD-04 (ghi giải trình `14/90`), nên endpoint **chỉ chặn cứng `12/13`** (đã kết xuất gửi Sở / hoàn thành — SP không bảo vệ, gọi vào sẽ kéo lùi `12→09`). **Phạm vi 09/10 riêng của sửa lẻ do UI kiểm** (nút "Sửa lẻ" chỉ hiện ở dòng 09/10) — backend không chốt lại, vì cùng cửa còn phải nhận `03` và `14/90`.
- **Sửa lẻ 1 môn (giữ 4 môn cũ):** điểm lưu là **quy đổi /10** (không lưu điểm gốc) → KHÔNG tính ngược ra gốc (lệch làm tròn). Lưu gom **5 giá trị quy đổi** = {môn vừa sửa: quy đổi từ gốc nhập; môn không sửa: `DiemKQ*` đã lưu đọc từ `/hoc-vien`}; tính lại 3 cờ Đạt (per-môn ≥5 trên 5 quy đổi) → gọi SP `_CapNhat` như KQD-02 (SP nhận thẳng quy đổi). UI: cho Lưu khi chỉ 1 vài ô có giá trị, miễn **mỗi môn trống đều có điểm đã lưu** để điền chỗ trống; môn vừa trống-nhập vừa-chưa-lưu → vẫn báo thiếu (ô đỏ). *Chốt khi code:* mở rộng body `/cap-nhat` nhận cờ "giữ quy đổi cũ" theo môn, HOẶC endpoint riêng — không nối chuỗi, tham số hóa.
- **Xóa điểm (reset về chưa có điểm):** `POST /local/ketqua/xoa-diem` (body `ma_dk`). UPDATE trực tiếp tham số hóa (SP không reset được): `UPDATE NguoiLX_HoSo SET DiemKQLyThuyet=NULL, DiemKQMoPhong=NULL, DiemKQHinh=NULL, DiemKQTienLui=NULL, DiemKQThucHanh=NULL, KQLyThuyet=NULL, KQThucHanh=NULL, KetLuanCSDT=NULL, SoGiayCNTN=NULL, TT_XuLy='03', NgaySua=GETDATE() WHERE MaDK=@MaDK AND TT_XuLy IN ('09','10')`. **Kiểm `TT_XuLy` bằng SELECT TRƯỚC** (ngoài 09/10 → 409; không tìm thấy → 404) rồi mới UPDATE — KHÔNG dựa `rowcount` (pymssql có thể trả -1 khi bảng có trigger/NOCOUNT → báo nhầm thất bại dù điểm đã xóa); mệnh đề `IN ('09','10')` trong UPDATE giữ lại làm lưới chống đua (TOCTOU). UI: nút "Xóa điểm" mỗi dòng 09/10 + **hộp xác nhận** (đổi dữ liệu thật). Giờ/km thực hành (`TGThucHanh*`/`QDThucHanh*`): *chốt khi code có xóa kèm không* — mặc định giữ (không thuộc "điểm").
- **Bất biến:** chỉ 09/10; mọi SQL tham số hóa; xóa phải xác nhận; reset về `'03'` (đã đăng ký) — không đoán lại 03 vs 04.

### 11D.9 Kiểm trước kết xuất (KQD-07, CHANGES #65) — chỉ đọc
> Bổ sung 12/10/2026 từ tư vấn theo schema DB đích. Không đổi schema, không ghi DB; kết xuất vẫn thuộc PM cũ.

- **Endpoint (đề xuất, chốt khi code):** `GET /local/ketqua/kiem-truoc?ma_kh=` — gác session + `target_key` như §11D.6. Đọc HV của đúng khóa `ma_kh` có `TT_XuLy IN ('03','04','09','10','90')` (`90` thêm ở CHANGES #77 — HV đã giải trình, chờ kết xuất lại. **HV `90` mà `KetLuanCSDT` NULL → `thieu_ket_luan`; `KetLuanCSDT=0` → chip `khong_dat_o_90` ("Đang giải trình nhưng không đạt — sẽ không kết xuất"); `GiaiTrinh` rỗng → chip `giai_trinh_trong`** — §11D.13) (cùng nguồn với `/hoc-vien`, nên dùng lại hàm đọc có sẵn, không viết SELECT thứ hai). Trả `{ma_kh, tong, du, thieu:[{ma_dk, ho_ten, so_cccd, tt_xuly, ly_do:[…], mon_thieu:[…]}], dem:{chua_co_diem, thieu_mon, thieu_gio_km, thieu_ket_luan}, mo_to_bo_qua}` — `tong` **không gồm** học viên mô tô (đếm riêng ở `mo_to_bo_qua`).
- **Luật thuần (backend, không DB), hàm `hv_chua_du(hv)`** (không còn tham số `hang`; router lọc hạng mô tô — mã hạng bắt đầu `A` — trước khi gọi) đặt cạnh luật quy đổi trong `ketqua_quydoi.py`:
  - `chua_co_diem` ⇔ cả 5 `DiemKQ*` rỗng (không kèm điều kiện `TT_XuLy` — HV 09/10 mà rỗng điểm cũng là chưa có điểm);
  - `thieu_mon` ⇔ có ≥1 điểm nhưng thiếu ≥1 trong **5 môn bắt buộc** (cùng luật ô đỏ KQD-02, mọi hạng ô tô; môn thiếu trả ở `mon_thieu`);
  - `thieu_gio_km` ⇔ `TGThucHanhHinh`/`QDThucHanhHinh`/`TGThucHanhDuong`/`TongQDThucHanh` còn rỗng (giờ/km đường **dưới ngưỡng gợi ý** KQD-02 chỉ là cảnh báo, **không** vào `ly_do`; response hiện **chưa trả** cảnh báo này — ❓ chưa chốt: backend trả thêm hay UI tự tính từ lưới, quyết khi code task 120);
  - `thieu_ket_luan` ⇔ `TT_XuLy ∈ {09,10}` mà `KetLuanCSDT IS NULL` (bất thường).
- **Danh sách môn bắt buộc theo hạng hiện nằm ở phía UI** (`CapNhatKQDT.tsx`, ô đỏ KQD-02). Khi code **chuyển lên một nguồn chung ở backend rồi cho UI KQD-02 gọi lại cùng nguồn đó**, để KQD-07 và KQD-02 không có hai luật khác nhau (rủi ro đã biết nếu chép).
- **UI:** nút "Kiểm trước kết xuất" ở màn KQD-02 (sau khi chọn khóa) → khung kết quả; bấm dòng → mở HV ở lưới KQD-02. HV `12/13/14/90` không đưa vào. **Đã chốt qua mock `ui-mock/ketqua.html` (12/10/2026):** khung là drawer bên phải; HV `chua_co_diem` **không hiện** chip `thieu_gio_km` (UI lọc, response vẫn trả đủ); khóa toàn mô tô (`tong=0`, `mo_to_bo_qua>0`) hiện "Khóa mô tô — không xét kết quả đào tạo", không báo "chưa có học viên".
- **Bất biến:** chỉ đọc; không chặn kết xuất; không sinh XML.
- **Kiểm thử:** unit `hv_chua_du` (đủ 5 môn → đủ; thiếu 1 môn; chưa có điểm; thiếu giờ-km; thiếu kết luận; hạng mô tô không xét — đếm `mo_to_bo_qua`; giờ đường dưới ngưỡng không vào lý do) + API bằng cursor giả (HV 12/13 không vào danh sách).

### 11D.10 Nạp giờ/km đường từ PDF DAT (KQD-08, CHANGES #69) + giờ `hh:mm` ở lưới (KQD-02)
> Cập nhật 02/11/2026 (CHANGES #88): `doc_pdf_dat` tìm cột theo tên tiêu đề, nhận cả mẫu cũ 7 cột và mẫu mới 9 cột (giờ thập phân `24.660`). Hàng tiêu đề phải có ít nhất 2 tên cột; bảng có STT mà thiếu cột bắt buộc, hoặc hơn 7 cột mà không có tiêu đề → báo mẫu lạ. Chữ cái dính trước đúng dạng mã `ddddd-dddddddd-dddddd`, khi cột mã đứng ngay sau cột họ tên, là chữ cuối của tên tràn cột: chuyển về họ tên.
> Bổ sung 12/10/2026. Quyết định: TDD-decisions §24. **Không đổi schema CDB**; ghi 2 cột có sẵn.

```
 Nhân viên           UI (NapDatModal)        Tool (FastAPI)                  CDB đích
    │ chọn PDF ─────────► │                         │                          │
    │                     │ POST /dat/xem-truoc ──► │ kiểm .pdf / %PDF / ≤5 MB │
    │                     │                         │ doc_pdf_dat (pdfplumber) │
    │                     │                         │ mã khóa file ≠ ma_kh ─► 400
    │                     │                         │ _doc_hv_khoa ──────────► │ SELECT cả khóa
    │                     │                         │ doi_chieu                │
    │                     │                         │ _tra_cuu_khong_co ─────► │ SELECT (≤500 mã, ≤50 tên)
    │                     │ ◄── bảng cũ → mới  (CHƯA ghi gì)
    │ sửa số, tick ─────► │ chặn Lưu nếu ô trống / sai / ngoài khung
    │ bấm Lưu ──────────► │ POST /dat/luu ────────► │ BEGIN                    │
    │                     │                         │ UPDATE từng ma_dk ─────► │ chỉ 2 cột + NgaySua
    │                     │                         │ COMMIT  (lỗi → ROLLBACK cả lô, 502)
    │                     │ ◄── {da_luu, bo_qua}    làm tươi lưới
```

| `tinh_trang` | Tick được | Tick sẵn | "Chọn tất cả" | Ghi |
|---|---|---|---|---|
| `khop` | có | có, nếu khác số cũ (sau làm tròn 2 chữ số) | có | có |
| `chua_chay_dat` | có | không (tick tay thì điền sẵn `0`) | **không** | có, nếu tick tay |
| `loi_dong` | không | không | không | không |
| `trung_dong` | không | không | không | không (chỉ lấy dòng đầu) |
| `khong_co_trong_khoa` | không | không | không | không (kèm lý do) |
| `da_ket_xuat` (12/13) | không | không | không | không |

- **Nguồn:** PDF "Báo cáo kết quả đào tạo thực hành lái xe trên đường của khóa học" (DAT). Đã đọc thử 4 file mẫu `thamkhao/DAT *.pdf` (186 dòng) bằng `pdfplumber`: đầu file có `Mã khóa học:<mã> (<tên>)` + `Hạng đào tạo`; bảng 7 cột `STT · Mã học viên · Họ và tên · Ngày sinh · Tổng thời gian · Tổng quãng đường · Ghi chú`, trải nhiều trang; giờ `16:19` / `0:59` / `28:26` (có thể ≥ 24), km `725,63` / `1.008,19`; dòng chưa chạy DAT có giờ trống + km `0,00`. **Định nghĩa trong code:** `chua_chay_dat ⇔ (giờ trống hoặc 0) và (km trống hoặc 0)`; chỉ một trong hai trống → `loi_dong` "Thiếu giờ hoặc quãng đường" (không tick được).
- **Hàm thuần** (file mới `tool/app/ketqua_dat.py`, không DB): `doc_gio("16:19") → 16.32` (h + m/60 [+ s/3600], làm tròn 2 chữ số; nhận `hh:mm`, `hh:mm:ss` và số thập phân; trống → `None`; phút/giây ≥ 60 hoặc rác → lỗi dòng) · `doc_km("1.008,19") → 1008.19` · `doc_pdf_dat(bytes) → {ma_kh, hang, dong:[{stt, ma_hv, ho_ten, ngay_sinh, gio, km, ghi_chu, loi}]}`. Cùng luật `hh:mm` ở phía UI (`gioThucHanh.ts`) cho ô Giờ đường KQD-02.
- **Endpoint** (đã chốt khi code; gác session ở router + `target_key` như §11D.6):
  - `POST /local/ketqua/dat/xem-truoc` (multipart: `file` + `ma_kh`). Chỉ `.pdf` + đầu file `%PDF` (sai → 400), ≤ 5 MB (quá → 413). Mã khóa trong file ≠ `ma_kh` (không phân biệt hoa/thường) → 400. Khớp từng dòng với HV của khóa bằng `_doc_hv_khoa(ma_kh, None, …)` (không viết SELECT thứ hai). **Không ghi DB.** Cảnh báo dưới ngưỡng dùng lại `canh_bao_duong`. Trả `{ma_kh, hang, tong_file, dong:[{stt, ma_dk, ho_ten, ngay_sinh, gio_cu, gio_moi, km_cu, km_moi, tinh_trang, canh_bao[], co_thay_doi, chon_duoc, tick_san, ghi_chu, khoa_khac}], vang_trong_file:[{ma_dk, ho_ten, so_cccd}]}`. `tinh_trang` ∈ `khop | chua_chay_dat | khong_co_trong_khoa | da_ket_xuat | loi_dong | trung_dong`; `chon_duoc` = được phép tick (`khop`, `chua_chay_dat`); `tick_san` = tick sẵn (`khop` và có thay đổi).
  - `POST /local/ketqua/dat/luu` (`{ma_kh, dong:[{ma_dk, gio_duong ∈ [0,999], km_duong ∈ [0,99999]}]}`, 1..1000 dòng; ngoài khung → 422 cả lô; cần phiên). **Một transaction**, mỗi dòng: `UPDATE dbo.NguoiLX_HoSo SET TGThucHanhDuong=%s, TongQDThucHanh=%s, NgaySua=GETDATE() WHERE MaDK=%s AND MaKhoaHoc=%s AND TrangThai = 1 AND ISNULL(TT_XuLy,'') NOT IN ('12','13')`. Lỗi giữa chừng → rollback cả lô, 502. Trả `{ok, da_luu, bo_qua:[{ma_dk, ly_do}]}`. **Không gọi SP `_CapNhat`** (SP ghi đè điểm/kết luận/trạng thái — quá tay cho việc chỉ nạp giờ/km).
  - `GET /local/ketqua/hoc-vien` trả thêm `gio_duong`, `km_duong` (cột đã có sẵn trong `_SQL_HV`, làm tròn 2 chữ số) để lưới KQD-02 nạp sẵn giá trị đã lưu.
- **Sửa lỗi ngầm KQD-02:** hiện lưu sửa lẻ điểm khi ô giờ trống gửi `gio_duong=null` và SP ghi NULL đè giờ cũ. Sau thay đổi: ô nạp sẵn giá trị đã lưu → không gõ thì gửi đúng giá trị cũ.
- **Đã xác minh 12/10/2026:** (1) "Mã học viên" trong PDF **=** `NguoiLX.MaDK` — DB dev có 2/4 khóa mẫu (B.01-K40, C1-K11), 62/62 dòng khớp và `MaKhoaHoc` trùng mã khóa trong file; 2 khóa còn lại (B.01-K39, C1-K10) không có trong DB dev nên chưa đối chiếu được. (2) SP `_CapNhat` ngoài 2 cột giờ/km chỉ đặt thêm **`NgaySua = GETDATE()`** (và điểm/kết luận/`TT_XuLy`/ngày) — UPDATE của KQD-08 đặt `NgaySua` như SP, không đụng phần còn lại.
- **Số lưu ở DB là `real`** (đọc ra `18.399999618530273`): `/hoc-vien` và bảng xác nhận làm tròn 2 chữ số; so "có thay đổi" sau làm tròn.
- **Phụ thuộc mới:** `pdfplumber` (kéo `pdfminer.six`) — thêm vào requirements tool + `tool.spec`; kiểm đọc được trong exe đóng gói.
- **Lý do "không có trong khóa"** (`ketqua_dat.gan_ly_do_khong_co` + router `_tra_cuu_khong_co`, chỉ SELECT): tra `NguoiLX_HoSo` theo `MaDK` ở mọi khóa (+`KhoaHoc.TenKH`); chưa thấy thì tra `NguoiLX` theo (`HoVaTen`, `NgaySinh` yyyymmdd) — tối đa **50** dòng/lần theo tên và **500** mã/lần. **Dòng vượt trần KHÔNG được tra** và hiện *"Chưa tra được lý do (quá nhiều dòng không khớp) — kiểm lại khóa/file."* (không dùng câu "không tìm thấy"). Lỗi tra → lý do chung, không làm hỏng xem trước.
- **Sửa số trong bảng xem trước:** thuần UI (`NapDatModal.tsx`, cùng `parseGio`/`parseKm` với lưới); server `/dat/luu` nhận số đã sửa và tự kiểm khung (`0 ≤ giờ ≤ 999`, `0 ≤ km ≤ 99999`).
- **Mã khóa trong PDF** đọc bằng `khóa\s*học:\s*([A-Za-z0-9]+)` (chữ + số) để tên khóa dính liền `…260002(B01-K39)` không bị coi sai khóa.
- **Ô "chưa chạy DAT" tick tay:** UI điền sẵn `0` vào ô giờ (km đã `0`); ghi `0/0` là chủ ý của người dùng. **"Chọn tất cả" ở tiêu đề chỉ tick dòng `khop`**; dòng `chua_chay_dat` luôn tick tay từng dòng (ghi `0/0` có thể đè giá trị đang có — sửa 12/10/2026 sau `/reviewtdd`).
- **Bất biến:** chỉ ghi `TGThucHanhDuong`/`TongQDThucHanh`; không đụng điểm/kết luận/`TT_XuLy`; HV `12`/`13` không ghi; không sinh XML.
- **Rủi ro đã biết (rà soát `/reviewtdd` 12/10/2026, biên bản `tdd-review-12-10-2026-kqd08.md`):**
  - **`da_luu` đếm bằng `cursor.rowcount == 1`** (UPDATE trần, không qua SP): các phần khác của dự án dùng tương tự và chưa thấy trả `-1`; nếu có thì chỉ báo "bỏ qua" dù đã ghi, ghi lại cùng giá trị là idempotent. Chấp nhận (khác §11D.7b/§11D.8 vì các mục đó có SP/nhiều bước).
  - **Hai phiên nạp cùng một khóa: người ghi sau thắng**, không lưu giá trị cũ (cột "cũ" chỉ nằm trên màn hình đã đóng). Chấp nhận — tool một máy, file cùng nguồn DAT; cần đối chiếu thì chụp/in bảng xác nhận.
  - **PDF không giới hạn số trang:** `extract_tables()` chạy mọi trang; file ≤ 5 MB, tool localhost, một người dùng, file tự tải từ DAT (mẫu 1–3 trang). Chấp nhận; nếu về sau nhận PDF từ nguồn lạ thì thêm giới hạn (đề xuất ≤ 30 trang).
- **Kiểm thử:** unit `doc_gio`/`doc_km` (`16:19`, `0:59`, `28:26`, rỗng, `20:75`, `1.008,19`) · đọc 4 PDF mẫu (60/30/64/32 dòng; 2 dòng chưa chạy DAT) · API bằng cursor giả (sai khóa → 400; HV 12/13 bỏ qua; dòng lỗi không làm hỏng dòng khác) · vitest `gioThucHanh.ts`.

### 11D.11 Xuất Excel kết quả học tập theo khóa (KQD-09, CHANGES #72, #73) — chỉ đọc
> Bổ sung 12/10/2026, soát `/reviewtdd` cùng ngày (biên bản `tdd-review-12-10-2026-kqd09.md`). Quyết định: TDD-decisions §25. **Không đổi schema CDB, không ghi DB.**

```
 Nhân viên       Giao diện (React)            Tool (FastAPI)                       CDB đích
    │ bấm Xuất Excel │ POST /xuat-excel?ma_kh=… │ require_session ──► 401                │
    │───────────────►│────────────────────────►│ SELECT KhoaHoc ───────────────────────►│
    │                │                         │  không có ──► 404 "Không tìm thấy khóa"│
    │                │                         │ SELECT HV của khóa (_doc_hv_khoa) ────►│
    │                │                         │  rỗng ──► 404 "Khóa chưa có học viên"  │
    │                │                         │ cấu hình: cơ quan / cơ sở              │
    │                │                         │ dung_workbook(): làm sạch chuỗi,       │
    │                │                         │  ép kiểu chữ ô bắt đầu = + - @ ──► 500 │
    │                │ luu_file(): ghi vào thư mục output (không ghi đè, _2, _3…)       │
    │                │◄── 200 {duong_dan, thu_muc, so_hoc_vien}                         │
    │ thấy đường dẫn │ toast + nút "Mở thư mục" → POST /mo-thu-muc-xuat (đường dẫn cố định)│
```

| Cột | Nguồn | Luật |
|---|---|---|
| STT | thứ tự | sắp theo `CAST(SoHoSo AS INT)` |
| Mã đăng ký, Họ tên, CCCD, Ngày sinh | `NguoiLX` | CCCD ép chuỗi; `NgaySinh` yyyymmdd → ô ngày |
| Hạng | `MaHangMoi`, dự phòng `HangGPLX` | theo từng học viên |
| 5 điểm | `DiemKQ*` | 1 chữ số; < 5 chữ đỏ |
| Điểm LT / TH | tính | TB(LT, MP) / TB(Hình, Chữ chi, Đường); trống nếu thiếu môn |
| Giờ/km sân, đường | `TGThucHanh*`, `QD*` | 2 chữ số |
| Kết quả, Ngày xét | `KetLuanCSDT`, `KhoaHoc.NgayThi` | 1 → Hoàn thành, 0 → Chưa HT, NULL → trống |
| Trạng thái, Số giấy, Ghi chú | `TT_XuLy`, `SoGiayCNTN`, tính | `Thiếu: …` / `Chưa có điểm` / cảnh báo giờ-km |

- **Nguồn dữ liệu:** `NguoiLX_HoSo` + `NguoiLX` của đúng 1 khóa — dùng lại `_doc_hv_khoa(ma_kh, None, target_key)` (không viết SELECT thứ hai; thêm `B.SoGiayCNTN` vào `_SQL_HV`, đọc bằng `.get`). Thông tin khóa (`TenKH`, hạng, `NgayKG`/`NgayBG`/`NgayThi`) đọc 1 truy vấn `KhoaHoc`; chương trình Cũ/Mới từ `config_store.get_kqd_chuong_trinh(ma_kh)`.
- **Endpoint:** `POST /local/ketqua/xuat-excel?ma_kh=&target_key=` (gác phiên + `target_key` như §11D.6; **POST vì có ghi 1 file ra đĩa**, DB vẫn chỉ SELECT). Dựng workbook rồi **lưu vào thư mục `output` của phần mềm** (`paths.output_dir()`: bản đóng gói = `output` cạnh `pmcsdtlx-tool.exe`, không ghi được thì `%APPDATA%\pmcsdtlx-tool\output`; chạy dev = `tool/output`, đã `.gitignore`); `ketqua_xuat.luu_file` ghi bằng chế độ tạo mới (`xb`), **trùng tên thì thêm `_2`, `_3`…** (không ghi đè, kể cả file cũ đang mở trong Excel). Trả `{ok, ten_file, duong_dan, thu_muc, so_hoc_vien}`. **Lỗi:** khóa không tồn tại → **404** "Không tìm thấy khóa học ở CSDL đích."; khóa không có HV hoạt động → **404** "Khóa chưa có học viên — không có gì để xuất."; mất kết nối DB → lỗi chuẩn của `_loi_db`; dựng workbook lỗi → **500** thông báo chung; không ghi được thư mục output → **500** "Không ghi được file vào thư mục output của phần mềm" (không lộ chi tiết hệ thống). **Chỉ SELECT DB.**
- **`POST /local/ketqua/mo-thu-muc-xuat`:** mở thư mục output bằng File Explorer (`os.startfile`); **đường dẫn cố định do tool chọn, bỏ qua mọi đầu vào từ client**; gác phiên.
- **Hàm thuần** (`tool/app/ketqua_xuat.py`, không DB): `dung_workbook(khoa, hv_rows, co_so, nguoi_lap, ngay_lap, chuong_trinh) -> bytes` bằng `openpyxl`; `ten_file(ma_kh, ngay)` (chỉ `[A-Za-z0-9_-]`). Luật:
  - Điểm Lý thuyết = `round(TB(LT, MP), 1)`, Điểm Thực hành = `round(TB(Hinh, TienLui, ThucHanh), 1)`; **trống nếu thiếu môn** (theo sổ mẫu TT17).
  - **Kết quả** lấy từ `KetLuanCSDT` (TDD-decisions §25): 1 → "Hoàn thành", 0 → "Chưa hoàn thành", NULL → trống. **Hệ quả đã chấp nhận:** học viên PM cũ lưu "Đạt" mà thiếu môn thì thấy "Hoàn thành" cạnh ô điểm trống, cột Ghi chú nêu `Thiếu: …` (khác sổ mẫu TT17 chỉ xét khi đủ 5 điểm). Ngày xét hoàn thành = `NgayThi` khóa, chỉ khi "Hoàn thành"; khóa chưa có `NgayThi` → ô để trống, không báo lỗi.
  - **Ghi chú:** thiếu 1–4 môn → `Thiếu: <các môn>`; trống cả 5 → `Chưa có điểm`; kèm cảnh báo giờ/km đường dưới mức gợi ý (dùng chung `ketqua_quydoi.canh_bao_duong`).
  - **Dòng tóm tắt:** `Tổng N · Hoàn thành X · Chưa hoàn thành Y · Chưa có kết luận Z` (Z = HV `KetLuanCSDT` NULL).
  - **Hạng khối đầu:** `MaHangMoi` xuất hiện nhiều nhất trong các HV của khóa (**hòa → theo thứ tự chữ cái**, ổn định giữa các lần xuất); không HV nào có thì `KhoaHoc.HangGPLX` (mã cũ, vd `B11`).
  - Giờ/km làm tròn 2 chữ số (cột DB là `real`); **định dạng ô: số nguyên `0` (hiện `34`), số lẻ `0.##`** — không dùng `0.##` cho số nguyên vì Excel hiện dấu chấm thừa `34.`. Ngày sinh `yyyymmdd` → ô ngày thật; CCCD ghi dạng chuỗi.
- **An toàn dữ liệu trong file:** mọi chuỗi từ DB/cấu hình đi qua `_sach()` (bỏ ký tự điều khiển XML không hợp lệ — một học viên có ký tự lạ không được làm hỏng cả file — và cắt tối đa 32.000 ký tự) rồi `_ghi_chu()`: **chuỗi bắt đầu `= + - @` hoặc tab/CR bị ép kiểu chữ + `quotePrefix`**, không thành công thức (chống formula injection — họ tên có thể do học viên khai ở app web, file đi nộp ra ngoài).
- **Cấu hình:** `co_quan_chu_quan`, `ten_co_so_dao_tao` (không bí mật; tối đa 200 ký tự) lưu bằng `PUT /local/config/co-so` — **gác phiên** (khác `PUT /local/config` là bước mồi lần đầu), gộp vào `config.enc`, không đụng khóa khác; thêm vào `ConfigIn` để lưu khối ① không làm rơi 2 ô này. Trống thì ô đầu sổ để trống.
- **UI:** nút "Xuất Excel" ở `CapNhatKQDT.tsx` (sau khi chọn khóa); gọi POST, thanh thông báo hiện `Đã lưu N học viên → <đường dẫn đầy đủ>` kèm nút **"Mở thư mục"**; nút khóa khi đang xuất.
- **Phụ thuộc mới:** `openpyxl` (kéo `et_xmlfile`) — thêm vào requirements + `tool.spec` (`collect_all`); `--selftest` dựng workbook nhỏ.
- **Hiệu năng:** một SELECT cả khóa, dựng workbook đồng bộ trong bộ nhớ; **5.000 học viên ≈ 4 giây (đo 12/10/2026)**, CSĐT thực tế vài chục đến vài trăm nên không cần chạy nền.
- **Ghi nhận (rà soát):** hai truy vấn riêng (khóa rồi HV) có thể lệch vài mili giây nếu đang ghi — file là ảnh chụp tại lúc xuất · `ngay_lap` là giờ máy CSĐT (VN) · `ORDER BY CAST(SoHoSo AS INT)` của `_SQL_HV` (dùng chung từ trước) lỗi nếu `SoHoSo` không phải số — chưa thấy dữ liệu như vậy.
- **Bất biến:** không ghi DB; không đổi `TT_XuLy`; họ tên/CCCD/ngày sinh chỉ nằm trong file tải về máy người đã đăng nhập, không ghi log, không lọt vào thông báo lỗi.
- **Kiểm thử:** pytest dựng workbook từ hàng giả rồi đọc lại bằng `openpyxl` (khối đầu, 22 cột, STT, ngày thật, CCCD chuỗi, Hoàn thành/Chưa/trống, TB, thiếu môn, cảnh báo giờ/km, HV 12/13 vẫn có, khóa rỗng 404, tiếng Việt có dấu, tên file ASCII, hạng hòa phiếu, **công thức `=…`/`+…`/`-…`/`@…` bị ép chuỗi, ký tự điều khiển không làm hỏng file, chuỗi > 32.000 bị cắt, `PUT /co-so` cần phiên**, endpoint chỉ SELECT) · Playwright: bấm nút → tải về + tên file + API đúng khóa; 404 hiện thông báo; nút khóa khi đang xuất; lưu tên cơ sở.

### 11D.12 Xuất Sổ theo dõi kết quả học tập — mẫu Phụ lục VI (KQD-10, CHANGES #75) — chỉ đọc
> Bổ sung 12/10/2026. Quyết định: TDD-decisions §26. **Không đổi schema CDB, không ghi DB.** Bám sheet `SO_PHU_LUC_VI` của `thamkhao/So_theo_doi_ket_qua_hoc_tap_DTLX_TT17.xlsx`.

```
 Trang 1 (A4 dọc)                                     Trang 2…
 ┌──────────────────────────────────────────────┐    ┌───────────────────────────────┐
 │ CƠ QUAN / CƠ SỞ (Cấu hình ③) │ CHXHCN VIỆT NAM │    │ ┌──┬────────┬────┬───┬───┬──┬──┐│
 │                              │ Độc lập-Tự do…  │    │ │STT│ Họ tên │Khóa│ LT│ TH│KQ│… ││ ← 2 hàng
 │        SỔ THEO DÕI KẾT QUẢ HỌC TẬP (14, đậm)   │    │ ├──┼────────┼────┼───┼───┼──┼──┤│   tiêu đề
 │ Khóa học: <tên khóa>                           │    │ │ 23│ …      │    │   │   │  │  ││   lặp lại
 │ Ngày lập: dd/mm/yyyy                           │    │ │ …                              ││
 │ Người lập:                    (để trống)       │    │                  Trang 2/2     │
 │ ┌──┬────────┬────┬───┬───┬──────┬──────┬──────┐ │    └───────────────────────────────┘
 │ │STT│Họ tên │Khóa│ LT│ TH│Kết quả│Ngày xét│Xác nhận│ │
 │ ├──┼────────┼────┼───┼───┼──────┼──────┼──────┤ │   Chân trang giữa: `Trang &P/&N`
 │ │ 1 │ …  (~22 dòng ở trang 1, ~31 ở trang sau*)    │
 │                  Trang 1/2                      │
 └──────────────────────────────────────────────┘
```

- **Nguồn dữ liệu:** dùng lại `_doc_khoa_va_hv(ma_kh, target_key)` (cùng nguồn với §11D.11: khóa + HV `TrangThai=1`; chỉ SELECT).
- **Endpoint:** `POST /local/ketqua/xuat-so-theo-doi?ma_kh=&target_key=` (gác phiên; POST vì ghi 1 file ra đĩa). Dùng chung `_luu_file_xuat` với §11D.11: ghi vào `paths.output_dir()`, không ghi đè (`_2`…), trả `{ok, ten_file, duong_dan, thu_muc, so_hoc_vien}`; 404 khóa không tồn tại / khóa rỗng; 500 chung khi dựng lỗi.
- **Hàm thuần** `tool/app/ketqua_so.py` (không DB): `dung_so_theo_doi(khoa, hv_rows, co_so, ngay_lap) -> bytes`; `khoa_sap_xep(ho_ten)`. Tái dùng `ketqua_xuat` (`dong_hv`, `_ghi_chu`, `_sach`, `_ngay_vn`, `luu_file`, `ten_file`).
- **Định dạng (đối chiếu file mẫu, test so với chính file mẫu khi có `thamkhao/`):** A4 dọc `paperSize=9`; fit-to-width 1 (`fitToHeight=0`); căn giữa ngang; không lưới; `print_title_rows=$10:$11`; chân trang giữa `Trang &P/&N`; Times New Roman 12 (tiêu đề sổ 14 đậm); nền tiêu đề `FFD9EAF7`, viền mỏng; ô gộp `A1:D2`, `E1:H2`, `A4:H4`, `A6:H6`, `A7:H7`, `A8:H8`, `A10:A11`, `B10:B11`, `C10:C11`, `D10:E10`, `F10:F11`, `G10:G11`, `H10:H11`; chiều cao hàng 1: 32,1 · 2: 21,95 · 4: 26,1 · 6–8: 20,1 · 10: 38,1 · 11: 30 · dữ liệu 21,95; độ rộng A 4,4 · D–E 7,4 · G 13,4 · H 12,4 (như mẫu).
- **Khác mẫu có chủ đích (user yêu cầu):** lề trái 2 · phải 1 · trên/dưới 1,5 cm (mẫu 3/2/2/2) · cột B tự giãn theo tên dài nhất, 25–34, `wrap` tắt + `shrinkToFit` (**cột C cũng `shrinkToFit`** khi tên khóa vượt trần 14) · F ≥ 16,5 để "Chưa hoàn thành" một dòng · `Người lập` để trống · ngày chỉ `dd/mm/yyyy` · định dạng ngày tường minh `dd/mm/yyyy` (mẫu `mm-dd-yy` phụ thuộc vùng). **Giữ ĐÚNG mẫu** (đã sửa sau `/reviewtdd`): viền xám `FFA6A6A6`, chân trang giữa cỡ 10, hàng 5 và 9 cao 15,75; riêng `footer` 0,3 inch (mẫu 0,5) vì lề dưới đã hẹp còn 1,5 cm — để `Trang x/y` không đè dòng cuối bảng.
- **Độ rộng cột theo ký tự:** chữ HOA ≈ 1,6 · ký tự khác ≈ 1,05 đơn vị cột (`_rong_chu`) vì họ tên trong DB thường lưu **viết hoa**; B = max(25, tên dài nhất + 2) trần 34. Khối đầu `A1:D2` (54 pt ≈ 3 dòng): tên cơ quan + cơ sở dài quá 3 dòng thì hàng 2 tự tăng +15,5 pt mỗi dòng. **Ước lượng, cần in thử trên Excel thật** (máy dev không có để kiểm).
- **Số dòng mỗi trang (ước lượng từ chiều cao hàng và khổ A4):** ~22 dòng ở trang 1 và ~31 dòng ở các trang sau **khi cột B giữ 25**; tên dài (B tới 34) làm Excel thu tỷ lệ in còn ~89% nên chứa nhiều dòng hơn (~27/~35). Không dùng làm tiêu chí kiểm thử.
- **Xếp tên:** khóa so sánh tiếng Việt tự dựng (không dùng `locale`): bảng chữ `a ă â b c d đ e ê g h i k l m n o ô ơ p q r s t u ư v x y`; chữ cái so trước, thanh điệu sau (không dấu < huyền < sắc < hỏi < ngã < nặng) — **mỗi âm tiết một thanh** nên `Hòa`=`Hoà`, `Thúy`=`Thuý` (dấu kiểu mới/cũ) xếp cạnh nhau, hòa nhau thì ổn định theo `MaDK`; thứ tự tên (từ cuối) → họ (từ đầu) → các tên đệm; tên một từ và tên trống (cuối) so sánh được với tên nhiều từ.
- **Kết quả:** `ket_qua_so` = kết quả theo `KetLuanCSDT` (§25) **chỉ khi đủ 5 điểm**, ngược lại trống (luật sổ mẫu "chưa đủ 5 nội dung thì để trống"); ngày xét = `NgayThi` khóa, chỉ khi Hoàn thành, ghi kiểu ngày thuần. **Hệ quả:** học viên PM cũ lưu "Đạt" mà thiếu môn sẽ có ô kết quả trống trong sổ (khác file Excel chi tiết §11D.11 vẫn hiện theo kết luận) — số liệu dev B.01-K40: 25 HV có kết luận Đạt nhưng chỉ 1 HV đủ 5 điểm. **Đủ 5 điểm nhưng chưa có kết luận → trống** (sổ không tự tính kết quả từ điểm). **Khóa chưa có `NgayThi`** → dòng Hoàn thành vẫn in nhưng ô Ngày xét trống, người in tự ghi. **Giải thích cho người in:** response thêm `so_hv_trong_ket_qua` (HV có kết luận nhưng thiếu điểm) và thanh thông báo ghi "N học viên có kết luận nhưng thiếu điểm nên để trống kết quả" khi N > 0.
- **An toàn dữ liệu:** chuỗi qua `_sach`/`_ghi_chu` như §11D.11 (ép kiểu chữ ô bắt đầu `= + - @`, bỏ ký tự điều khiển, cắt 32.000).
- **UI:** nút "Xuất Sổ theo dõi" ở `CapNhatKQDT.tsx` (dùng chung state `dangXuat`/`fileXuat` và thanh thông báo + "Mở thư mục" với "Xuất Excel").
- **Không có:** bìa, mục lục, khối chữ ký, sheet điểm quy đổi/điểm chi tiết (mẫu không có phần in; user chốt không xuất).
- **Kiểm thử:** pytest dựng sổ rồi đọc lại bằng `openpyxl`: thuộc tính trang/lề/chân trang/tiêu đề lặp/ô gộp/độ rộng/chiều cao/font/nền; **so trực tiếp với file mẫu** (bỏ qua nếu máy không có `thamkhao/`); thứ tự xếp tên (thanh điệu, a<ă<â, d<đ, trùng tên); luật kết quả; tên dài không xuống dòng; công thức bị ép chữ; endpoint chỉ SELECT; Playwright: bấm nút → POST đúng khóa, báo đường dẫn.

> **Phục vụ:** KQD-01/02/03/04/05/06/07/08/09/10. Dừng ở `TT_XuLy` 09/10/12 — kết xuất XML/gửi Sở thuộc PM cũ. Quy đổi điểm/giờ/km: nguồn `thamkhao/` (TT17 + Sổ theo dõi). Quyết định: TDD-decisions §17 (quy đổi) + §19 (mở khóa).

---

### 11D.13 Sửa lại HV Sở từ chối → "Đang giải trình" + giải trình hàng loạt (KQD-04 đổi, CHANGES #77)
> **Phục vụ:** KQD-04, KQD-01, KQD-03, KQD-07. Lý do + phương án: TDD-decisions §27. Sau `/reviewtdd` 16/10/2026 (biên bản `tdd-review-16-10-2026-kqd04.md`: 20 phát hiện, 3 Chặn đã đóng).
> Verify DB 16/10/2026 trên `GPLX_CDB_CSDT` (DESKTOP-UBV2GQI): `usp_NguoiLX_KetQuaDaoTao_CSDT` (SP đọc danh sách kết xuất của phần mềm CDB) lọc `@TrangThai='47'` = `TT_XuLy IN ('09','90') AND KetLuanCSDT=1`; **không** có `14` ⇒ HV bị Sở từ chối sửa xong mà vẫn ở `14` thì **không vào danh sách kết xuất**. Không thủ tục nào trong DB đặt `TT_XuLy='90'` (quét mọi DB) ⇒ bước `14→90` do tool làm (hoặc phần mềm CDB — chưa xác minh được vì máy dev không cài).

- **Quy tắc (server quyết, không tin client):**

| Đang ở | Sau khi ghi điểm / chuyển lô | Kết quả |
|---|---|---|
| `14` | `KetLuanCSDT=1` **và** `GiaiTrinh` hiệu lực không rỗng | → `90` |
| `14` | Đạt nhưng chưa có giải trình | giữ `14`, response `tt_moi='14'` + `thieu_giai_trinh=true` |
| `14` | Không đạt | giữ `14` |
| `90` | sửa tiếp | giữ `90` (SP đã giữ) — nếu thành Không đạt/trống kết luận: **vẫn `90`** nhưng hiện chip đỏ "Cần xử lý" (xem "HV 90 không kết xuất được") |
| `12`/`13` | — | chặn 409 như cũ |

- **Cảnh báo bắt buộc "chưa giải trình thì không kết xuất được" (user chốt 16/10/2026):** học viên `14` Đạt mà thiếu giải trình **không được im lặng giữ `14`** — UI phải nói rõ ở 4 chỗ: (1) sau khi Lưu một người: thông báo vàng đứng lâu (không tự tắt như toast thường) *"Đã lưu điểm — CHƯA có giải trình nên chưa chuyển sang Đang giải trình và chưa kết xuất lại được. Nhập giải trình rồi Lưu lại."* kèm `thieu_giai_trinh=true` từ response; (2) **chip cảnh báo trên dòng** học viên `14` Đạt thiếu giải trình: "Thiếu giải trình — chưa kết xuất được" (cam, tính ở client từ điểm đang nhập + ô giải trình + giải trình chung; server vẫn quyết ở bước ghi); (3) hộp chuyển hàng loạt: nếu `noi_dung` rỗng thì nút khóa + dòng đỏ "Phải có nội dung giải trình mới chuyển được"; (4) kiểm trước kết xuất (KQD-07) liệt kê học viên `14` Đạt thiếu giải trình kèm lý do `thieu_giai_trinh`. Cùng ý với `giai_trinh_trong` của HV `90`.
- **Một hàm chuyển duy nhất** `chuyen_14_sang_90(cur, ma_dk[], giai_trinh)` — cả `/cap-nhat` (sau SP ghi điểm) lẫn `/giai-trinh-lo` (không ghi điểm, **không tính lại điểm/cờ CŨ-MỚI**) gọi đúng hàm này với **cùng guard SQL**: `TT_XuLy='14' AND KetLuanCSDT=1 AND ISNULL(GiaiTrinh,'')<>''`.
- **Giải trình hiệu lực:** `giai_trinh` riêng nếu `strip()` không rỗng; ngược lại `giai_trinh_chung` nếu có; ngược lại **giữ nguyên cột** (không xóa). Xóa giải trình chỉ khi gửi `giai_trinh=''` **và** `giai_trinh_chung=None`. Giải trình chung **không bao giờ đè** giải trình riêng đã có.
- **`POST /local/ketqua/cap-nhat` (mở rộng):** thêm `giai_trinh_chung: str | None`. Thứ tự (cùng kết nối, trạng thái tự lưu từng lệnh như `cap_nhat` hiện có): (1) đọc HV (`TT_XuLy`, `MaCSDT`…) — `MaCSDT` ≠ cơ sở của máy → 403; `12`/`13` → 409; (2) ghi `GiaiTrinh` hiệu lực với điều kiện `AND TT_XuLy NOT IN ('12','13')`; (3) **đọc lại `TT_XuLy` ngay trước SP** — khác giá trị đã đọc → 409 `trang_thai_da_doi` ("trạng thái vừa đổi, tải lại"); (4) SP `_CapNhat`; (5) nếu HV đang `14` và Đạt → `chuyen_14_sang_90`; SELECT lại `TT_XuLy` để trả `tt_moi`. **Bước (5) lỗi sau khi (4) đã ghi** → **200** kèm `canh_bao: 'chua_chuyen_90'` (điểm đã lưu; UI hiện nút "Chuyển lại"), KHÔNG trả 502 làm nhân viên tưởng chưa lưu.
- **`POST /local/ketqua/giai-trinh-lo`** body `{ ma_dk: string[], noi_dung: string, ghi_de_rieng: bool = false }`:
  0. **Biên:** `ma_dk` khử trùng, bỏ rỗng/khoảng trắng; `1..200` (vượt → 422); `noi_dung.strip()` rỗng hoặc `> 1000` → 422; `IN (...)` dựng bằng `%s` tham số hóa. Gác `require_session` + `target_key`; `timeout` 30 giây.
  1. SELECT từng HV (`TT_XuLy`, `KetLuanCSDT`, `MaCSDT`, `MaKhoaHoc`, điểm/giờ-km/`SoGiayCNTN`, `GiaiTrinh`): không thấy → bỏ qua `khong_tim_thay`; `MaCSDT` ≠ cơ sở máy → `khong_thuoc_co_so`; `12`/`13` → `da_gui_hoac_hoan_thanh`; `90` → `da_o_dang_giai_trinh` (không báo lỗi — gọi lại an toàn); không phải `14` → `khong_con_o_so_tu_choi`; `KetLuanCSDT` ≠ 1 → `khong_dat`; **Đạt nhưng `hv_chua_du(hv)` (§11D.9, một nguồn) còn thiếu điểm/giờ-km hoặc `SoGiayCNTN` rỗng → `chua_du_diem` kèm môn/mục thiếu**.
  2. **Giao dịch thật:** mở kết nối **không tự lưu** (`autocommit=False`); `BEGIN TRAN` → với người đủ điều kiện: `UPDATE ... SET GiaiTrinh = CASE WHEN %s=1 OR ISNULL(GiaiTrinh,'')='' THEN %s ELSE GiaiTrinh END, TT_XuLy='90', NgaySua=GETDATE() WHERE MaDK IN (...) AND TT_XuLy='14' AND KetLuanCSDT=1` → `COMMIT`. Lỗi → `ROLLBACK`, trả **502 `lo_loi`** + `da_chuyen=[]` (không chuyển nửa chừng). Người đã có giải trình riêng được **giữ nguyên** trừ khi `ghi_de_rieng=true`.
  3. Trả `{da_chuyen: [...], bo_qua: [{ma_dk, ly_do, chi_tiet?}], giu_rieng: N}` (SELECT lại trạng thái, không tin rowcount). **Mất kết nối khi COMMIT/đọc lại** → 502 `{ketqua: 'khong_ro'}`; UI tự `GET /hoc-vien` làm tươi và hiện "Kiểm tra lại trước khi gửi lại". Gọi lại cùng danh sách là **idempotent**.

```
  NV(UI)           Tool(server)                         DB đích
    │ tích N HV        │                                    │
    │──POST lô────────►│ SELECT từng HV ───────────────────►│ (14? Đạt? cơ sở? đủ điểm?)
    │                  │ lọc → bo_qua[ly_do]                │
    │                  │ BEGIN TRAN ───────────────────────►│
    │                  │ UPDATE ... IN(...) + guard ───────►│ (HV đổi trạng thái giữa chừng → không khớp guard)
    │                  │ COMMIT ───────────────────────────►│
    │                  │ SELECT lại TT_XuLy ───────────────►│ ← lỗi/mất kết nối ở đây = "khong_ro"
    │◄─{da_chuyen, bo_qua, giu_rieng}                       │
```
- **Mẫu giải trình:** lưu **theo `target_key`** (`config['mau_giai_trinh'][target_key] = [...]`) — máy nhiều cơ sở đích không lẫn mẫu; tối đa 20 mẫu × 1000 ký tự, vượt → 422 nêu rõ (không cắt âm thầm), mẫu rỗng/trùng bị loại. `GET` trả `{mau: [...], phien_ban}`; `PUT` gửi kèm `phien_ban`, lệch → 409 `mau_da_doi` (UI nạp lại); *ghi nhận khi code (task 137):* `PUT` **thiếu** `phien_ban` thì không kiểm (chủ ý, tương thích), UI luôn gửi; hạng mô tô chưa có luật riêng trong lô (HV mô tô `14` rơi `chua_du_diem` — chờ quyết nghiệp vụ). **Ghi cấu hình có khóa** (`threading.Lock` + ghi file tạm rồi `os.replace`) để lưu mẫu không làm mất thay đổi cấu hình khác (tích CŨ/MỚI, `sync_targets`) khi hai thao tác trùng giờ. UI cảnh báo trên màn mẫu: "Mẫu dùng chung cho cả cơ sở — không ghi tên hoặc số căn cước học viên." **UI quản lý mẫu (CHANGES #78):** hộp "Quản lý mẫu" giữ bản nháp danh sách ở client; sửa/xóa/thêm xong gửi **một `PUT` thay toàn bộ danh sách** (không thêm endpoint); server loại mẫu rỗng/trùng, `> 20` hoặc `> 1000` ký tự → 422 nêu rõ; `phien_ban` lệch (người khác vừa lưu) → 409 `mau_da_doi`, UI nạp lại danh sách và giữ nháp để người dùng gộp tay.
- **`LyDoTuChoiKQDT` lên lưới:** SELECT lưới (`_SQL_HV` ở `routers/ketqua.py`) đọc thêm `LyDoTuChoiKQDT` + `GiaiTrinh` (hai cột `nvarchar(1000)` cho một khóa — chấp nhận được, đã `WHERE MaKhoaHoc`). `LyDoTuChoiKQDT` do luồng Sở ghi, tool chỉ đọc.
- **Nhóm trạng thái:** `_NHOM_TT` đổi từ tuple mã sang **điều kiện SQL** vì "chờ kết xuất" nay có điều kiện: `TT_XuLy IN ('09','10')` **hoặc** `(TT_XuLy='90' AND KetLuanCSDT=1)`. Một nguồn dùng chung cho đếm `/khoa`, lọc `/hoc-vien` và `kiem_truoc`. Khóa nhóm `giaitrinh` giữ cho `90` mọi kết luận. Bộ lọc lưới KQD-01 đổi sang nhóm việc: **chưa nhập (03/04) · chờ kết xuất · không đạt (10) · cần xử lý (14 + 90 không đạt/trống kết luận) · đã gửi/hoàn thành (12/13) · tất cả**.
- **HV 90 không kết xuất được:** HV `90` mà `KetLuanCSDT=0` hoặc NULL (nhập lại thành Không đạt sau khi đã giải trình, hoặc dữ liệu từ PM CDB) → chip đỏ "Đang giải trình nhưng không đạt — sẽ không kết xuất", xếp tab **Cần xử lý** cùng `14`; KQD-07 đếm vào `khong_dat_o_90` / `thieu_ket_luan`. HV `90` có `GiaiTrinh` trống (do `usp_CSDT_PheDuyetKQDT_TiepNhan` xóa trắng ở phản hồi Sở) → chip `giai_trinh_trong` ở KQD-07 — vi phạm bất biến "90 phải có giải trình" nên phải thấy được.
- **Nhãn trạng thái UI (một nguồn):** `03/04` Chưa nhập điểm · `09` Đã nhập · chờ kết xuất · `10` Đã nhập · Không đạt · `12` Đã gửi Sở · chờ duyệt · `13` Sở đã duyệt · `14` Sở từ chối · `90` Đã giải trình · chờ kết xuất lại; kèm dòng "việc cần làm". Mã `TT_XuLy` chỉ ở tooltip.
- **Bất biến:** chỉ HV `14` mới được tool đẩy lên `90`; mọi SQL tham số hóa; `12`/`13` không đụng; không sinh XML; mọi đường ghi lọc theo `MaCSDT` của máy.
- **Rủi ro biết trước:** (a) phần mềm CDB cũng có thể đặt `90` ở màn giải trình riêng — vô hại (cùng giá trị, guard `14`) nhưng cần nghiệm thu máy CSĐT; (b) `usp_CSDT_PheDuyetKQDT_TiepNhan` **xóa trắng `GiaiTrinh`** ở lần phản hồi Sở kế tiếp → giải trình chỉ sống tới lúc đó (chip `giai_trinh_trong` bắt ca này); (c) HV `90` mà Sở trả `13/14` cho bản kết xuất cũ → SP tiếp nhận (yêu cầu `12`) có thể báo lỗi, HV kẹt (như §11D.7b — không chặn, chỉ cảnh báo); (d) **khe hở nhỏ còn lại giữa "đọc lại trạng thái" và SP `_CapNhat`** vì SP không nhận guard `TT_XuLy` — chấp nhận, máy một người dùng; (e) `_NHOM_TT` đổi cấu trúc chạm cả `kiem_truoc` và đếm khóa → `impact` + test hồi quy KQD-01/03/07.
- **Kiểm thử:** unit quy tắc bảng trên (Đạt+GT→90 · Đạt thiếu GT→14 · Không đạt→14 · đang 90→90 · 12/13→409) · giải trình hiệu lực (riêng/chung/giữ nguyên/xóa) · `giai-trinh-lo` (lô lẫn 14 Đạt / 14 Không đạt / 14 Đạt thiếu điểm / 90 / 09 / 13 / khác cơ sở → chỉ chuyển người đủ điều kiện; lỗi giữa lô rollback; mã trùng/rỗng/>200 → 422; gọi lại idempotent) · `cap_nhat` bước chuyển lỗi → 200 `chua_chuyen_90` · đổi trạng thái giữa chừng → 409 · mẫu (theo cơ sở, `phien_ban` lệch → 409, vượt giới hạn → 422) · vitest nhãn trạng thái · Playwright lưới + hộp hàng loạt (API giả). Ghi thật nghiệm thu ở máy CSDT.

## 11E. Phân công giáo viên – xe cho khóa (tool — workspace riêng) — PCG-01..06 (CHANGES #54, #66)

> Ghi **CSDL đích** `GPLX_CDB_CSDT` (bảng `KhoaHoc_GiaoVien`, `KhoaHoc_XeTap`) như SYNC/TCB/KQD. Không đụng học viên, không kết xuất XML. Schema + SP + dữ liệu đã probe 10/10/2026; mock: `ui-mock/phancong.html`. Quyết định: TDD-decisions §22.

### 11E.0 Kiến trúc
- **Backend:** `tool/app/routers/phancong.py` (mount `require_session` ở `main.py`, như `ketqua.py`) + `tool/app/phancong_rules.py` (**luật thuần Python, không DB** — nhận trạng thái khóa + dữ liệu "bận" rồi trả danh sách vấn đề) + `tool/app/phancong_service.py` (đọc CDB, dựng dữ liệu bận, ghi theo SP). Kết nối qua `sqlserver_conn_dich(target_key)`; KHÔNG đụng DB Nạp.
- **Frontend:** phân hệ mới `phancong` trong `tool/webui/src/lib/modules.ts` (route `/phan-cong/*`, accent `pc` hồng sẫm, `db: GPLX_CDB_CSDT`, sub-nav "Phân công theo khóa" · "Rà soát khóa") + token `pc` trong `tailwind.config.js`; trang `tool/webui/src/pages/phancong/*` bám `ui-mock/phancong.html`.
- **Luật kiểm chạy ở server** (một nguồn): UI gọi `POST /kiem-tra` (debounce ~250ms) với bản nháp để hiện lỗi sống; `POST /ghi` kiểm lại lần cuối rồi mới ghi. Không nhân đôi luật ở TS.
- **Bản nháp ở UI** (CHANGES #57, /reviewtdd 11/10/2026): mọi thao tác chỉ sửa bản nháp trong React; **tự giữ** trong `localStorage` theo (`target_key`, `ma_kh`) kèm ảnh chụp hiện trạng CDB lúc mở. Mở lại khóa: hiện trạng CDB đã khác ảnh chụp → bỏ nháp; giống → hỏi Làm tiếp / Bỏ. Server không biết bản nháp, chỉ nhận trạng thái mong muốn khi `/ghi`.
```
        mở khóa                     sửa                   bấm Ghi, qua mọi cổng
 [Không nháp] ─────> [Đang soạn] ──────> [Sẵn sàng ghi] ────────────────> [Đã ghi] ──> làm tươi, xóa nháp
                      ▲   │  F5/đóng tab     │  còn ⛔                      │ lỗi giữa chừng
                      │   ▼                  ▼                              ▼
                      │ [Nháp trên máy]  [Khóa nút Ghi]             [Ghi dở: da_ghi/chua_ghi] ──> gửi lại = làm tiếp
                      │   │ mở lại: CDB chưa đổi → hỏi Làm tiếp/Bỏ
                      └───┘ CDB đã đổi → bỏ nháp; khi ghi lệch dấu vân tay → 409 khoa_da_doi
```

### 11E.1 Dữ liệu CDB dùng (đã verify)
| Bảng | Cột chính | Ý nghĩa |
|---|---|---|
| `KhoaHoc` | `MaKH, TenKH, HangGPLX, NgayKG, NgayBG, MaCSDT, TT_Xuly` | `NgayKG/NgayBG` datetime luôn 00:00 |
| `GiaoVien` | `MaGV, HoTenDem, TenGV, LoaiHinh_DaoTao (TH/LT/AL), CacHangGPLXDuocDT, HangGPLX, TrangThai` | danh mục (do Sở tiếp nhận) — chỉ đọc |
| `XeTap` | `BienSoXe, HangGPLXXe, NgayHHGPXTL, NgayHHGCNKD, TrangThai` | danh mục — chỉ đọc |
| `KhoaHoc_GiaoVien` | PK `MaLichLV` · `MaKH, MaGV, TenGV, LoaiGV(char2), BienSoXe, SoHV, NgayHL, NgayHetHL, GhiChu(NOT NULL), TrangThai, NguoiTao/Sua, NgayBD, NgayKT, IsKhoaHocGiaoVien, MaMonHoc, TenMonHoc` | cờ `1`=GV thuộc khóa, `0`=phân công |
| `KhoaHoc_XeTap` | PK `MaLichSD` · `MaKH, BienSoXe, MaGV, MaHV, DiaDiem, GhiChu(NOT NULL), TrangThai, NgayBD, NgayKT, IsKhoaHocXeTap, TenHV, TenGV` | cờ `1`=xe thuộc khóa, `0`=ghép xe |
```
 KhoaHoc (MaKH)
    ├── KhoaHoc_GiaoVien  cờ IsKhoaHocGiaoVien=1 ─ "GV thuộc khóa"      (1 dòng/GV, NgayBD/NgayKT rỗng)
    │                     cờ =0 ─ "phân công dạy" (môn, NgayBD→NgayKT)   (n dòng/GV)
    └── KhoaHoc_XeTap     cờ IsKhoaHocXeTap=1 ─ "xe thuộc khóa"         (1 dòng/xe)
                          cờ =0 ─ "ghép xe" (MaGV + BienSoXe + NgayBD→NgayKT + DiaDiem)
 Phụ thuộc: ghép xe cần GV thuộc khóa + GV có phân công môn 6 + xe thuộc khóa
```
FK: `KhoaHoc_GiaoVien→GiaoVien/KhoaHoc`, `KhoaHoc_XeTap→XeTap/KhoaHoc` (NO ACTION). **Không UNIQUE** (khóa,GV|xe), **không CHECK, không trigger** → mọi luật nằm ở tool.
- **"Bận" của GV/xe ở khóa khác:** `SELECT … FROM KhoaHoc_GiaoVien g JOIN KhoaHoc k ON k.MaKH=g.MaKH WHERE g.IsKhoaHocGiaoVien=0 AND g.TrangThai=1 AND g.MaGV IN (…)` (tương tự xe, `IsKhoaHocXeTap=0`) — **gồm cả khóa đang sửa** (loại các dòng đang được sửa trong bản nháp theo `MaLichLV`/`MaLichSD`).

### 11E.2 API (tool, gác session + `target_key` như §11D)
`GET /local/phancong/khoa?q=` (combobox khóa CSĐT hiện tại, kèm hạng, ngày KG/BG, cờ DKKH qua `dkkh_exists_sql`) · `GET /local/phancong/mon` (danh mục môn `DM_MonHoc`) · `GET /local/phancong/khoa/{ma_kh}` (hiện trạng: danh sách GV + phân công + xe + ghép, mỗi dòng kèm khóa `MaLichLV/MaLichSD`, kèm `dau_van_tay` = băm 20 ký tự của hiện trạng) · `GET /local/phancong/giao-vien?ma_kh=` (danh mục GV đang hoạt động + "bận" các khóa khác chưa bế giảng) · `GET /local/phancong/xe?ma_kh=` (danh mục xe + hạn + bận) · `POST /local/phancong/kiem-tra` (body = bản nháp; **không ghi**) · `POST /local/phancong/goi-y-ghep-xe` (đề xuất, **không ghi**) · `POST /local/phancong/ghi` (§11E.6) · `GET /local/phancong/ra-soat` (PCG-05) · `GET /local/phancong/nhat-ky?ma_kh=` · `GET /local/phancong/han-giay-to?ngay=30` (PCG-06, §11E.10, chỉ đọc).

### 11E.3 Danh sách GV / xe của khóa (PCG-01, cờ=1)
- Thêm GV: chỉ GV `TrangThai=1`; cảnh báo lệch hạng **chỉ khi GV dạy Thực hành**, theo `gv_hop_hang` (§11E.7, CHANGES #56) hoặc GV đang có phân công ở khóa khác chưa bế giảng (`NgayBG >= hôm nay`, CHANGES #58 — không cộng thêm 1 ngày như `usp_CheckWarningGiaoVien`).
- Gỡ GV: xóa **mọi dòng của GV trong khóa này** (cờ=1 và cờ=0) **từng dòng theo `MaLichLV`**; kèm xóa ghép xe (`KhoaHoc_XeTap` cờ=0) có `MaGV` đó **theo `MaLichSD`**. Hộp xác nhận liệt kê đúng các dòng này.
- Xe: thêm = dòng cờ=1 (`MaGV` NULL, `MaHV` NULL); gỡ = xóa dòng cờ=1 và các ghép xe cờ=0 của xe trong khóa.

### 11E.4 Phân công dạy (PCG-02, cờ=0)
- **Lưu môn:** `TenMonHoc` = mã môn nối dấu phẩy sắp tăng (`"1,8"`), `MaMonHoc` = NULL. Môn Thực hành = mã `6`. Đọc lại dòng cũ: nếu `MaMonHoc` có giá trị (định dạng trước 07/2026) → hiển thị theo `MaMonHoc`; nếu `TenMonHoc` là chuỗi mã → tách theo dấu phẩy; nếu là tên → giữ nguyên.
- **Thời gian:** `NgayBD/NgayKT` datetime; "Theo ngày" = `00:00`; chọn giờ bước 30 phút. Bản ghi cũ có phút lẻ giữ nguyên khi không sửa.
- **Ngày bắt đầu thực hành của khóa** chỉ là trạng thái giao diện (không lưu CDB); khóa đã có phân công TH → suy ra từ `MIN(NgayBD)` của các dòng môn 6.
- **Hàng loạt chạy ở UI** (không có endpoint riêng): với mỗi GV được tích, UI áp phân công mẫu vào bản nháp rồi gọi `POST /kiem-tra`; hộp xem trước hiện từng GV (hợp lệ / cảnh báo / bỏ qua + lý do), GV có ⛔ bị bỏ qua, các GV còn lại vào bản nháp. Gồm "Phân công cho N GV", "Dời ngày kết thúc thực hành cho N GV", "Áp Thực hành lái xe cho N GV TH chưa có". Ghi vẫn qua một `POST /ghi`.
- Insert bằng `usp_LichLV_KhoaHoc_GiaoVien_Insert` (SP tự lấy `TenGV` và `LoaiGV` từ `GiaoVien.LoaiHinh_DaoTao`, ghi `BienSoXe=''`, cờ=0); sửa bằng `usp_LichLV_KhoaHoc_GiaoVien_Update` (theo `MaLichLV`); xóa bằng `usp_LLV_KhoaHoc_GiaoVien_Delete(@MaLichLV)`.

### 11E.5 Ghép xe (PCG-03, cờ=0)
- 1 GV thực hành – 1 xe trong khoảng thời gian; ngày ghép mặc định = từ `MIN(NgayBD)` đến `MAX(NgayKT)` của các phân công môn 6 của GV (`00:00`; GV có hai đợt cách quãng thì chiếm cả khoảng nghỉ, nhân viên chỉnh nếu muốn nhả xe — CHANGES #58); `DiaDiem` điền sẵn; `MaHV/TenHV` để trống.
- Insert `LichSD_KhoaHoc_XeTap_Insert` (SP đặt cờ=0, tự lấy `TenGV`); sửa `usp_LichSD_KhoaHoc_XeTap_Update` (theo `MaLichSD`, ghi lại cờ=0); xóa `usp_LSD_KhoaHoc_Xetap_Delete(@MaLichSD)`. Thêm xe vào khóa (cờ=1): `usp_KhoaHoc_XeTap_Insert`; thêm GV vào khóa (cờ=1): `usp_KhoaHoc_GiaoVien_Insert` (truyền `@BienSoXe=''`, `@SoHV=NULL`, `@NgayHL/@NgayHetHL=NULL`).
- **Gợi ý ghép xe:** với mỗi **GV dạy thực hành** (§11E.7) chưa có xe, chọn xe trong danh sách khóa chưa ghép, không bị chặn bởi luật §11E.7, sắp ưu tiên đúng hạng (không cảnh báo) rồi theo biển số; trả danh sách `{ma_gv, xe, tu, den, canh_bao[]}` để UI duyệt.

### 11E.6 `POST /ghi` — thứ tự và an toàn
1. Nhận **trạng thái mong muốn của cả khóa** (`gv_khoa[]`, `pc[]`, `xe_khoa[]`, `ghep[]`; dòng đã có ở CDB mang `id` = `MaLichLV`/`MaLichSD`, dòng mới mang id tạm `"n1"`…) + `da_xem_canh_bao: bool` + `xac_nhan_csdl_that: true`; thiếu `xac_nhan_csdl_that` → 400. **Server tự suy ra thay đổi** (`gv_them/gv_go`, `pc_them/pc_sua/pc_xoa`, `xe_them/xe_go`, `gh_them/gh_sua/gh_xoa`) bằng cách so với hiện trạng CDB đọc lại lúc ghi — client không phải tính diff. Body kèm `dau_van_tay` (băm hiện trạng lúc mở khóa): **CDB đã khác → 409 `khoa_da_doi`** (không có cổng này, bản nháp cũ sẽ xóa lặng lẽ dòng người khác vừa ghi ở phần mềm CDB; CHANGES #59). Khóa ghi theo `ma_kh` trong bộ nhớ: request thứ hai trong lúc đang ghi → 409 `dang_ghi` (CDB không có UNIQUE nên ghi chồng sẽ nhân đôi dòng). Ghép xe có `xe` rỗng nghĩa là **Bỏ ghép**: có `id` CDB → xóa dòng đó; id tạm → bỏ qua. *Đổi so với bản đầu (nhận thay đổi) khi code task 87, 10/10/2026.*
2. **Diff rỗng → 200 "Không có thay đổi để ghi"** (kể cả khóa đã DKKH, trước cổng cảnh báo; CHANGES #58). Ngược lại **kiểm lại toàn bộ luật** trên trạng thái CDB hiện tại (đọc lại hiện trạng + bận): ⛔ trên dòng **giữ nguyên** chỉ hạ ⚠ "dữ liệu cũ" khi chỗ phụ thuộc (GV ∈ danh sách / có thực hành / xe ∈ danh sách) **đã hỏng sẵn trong CDB** (CHANGES #59); "giữ nguyên" = phân công: cùng id + GV + tập môn + từ + đến · ghép xe: cùng GV + xe + từ + đến (địa điểm không tính) — sửa bất kỳ cột nào trong đó thì dòng thành "sửa", hết được hạ mức. Còn ⛔ → 409 kèm danh sách; có ⚠ mà `da_xem_canh_bao=false` → 409.
3. Ghi theo thứ tự phụ thuộc: **xóa** (ghép xe → phân công → GV/xe) → **thêm** (GV/xe vào khóa → phân công → ghép xe) → **sửa**. Mỗi dòng một lệnh SP (autocommit, như §11D); đọc lại `MaLichLV/MaLichSD` mới bằng `SELECT` sau insert.
4. Lỗi giữa chừng → dừng, trả `{da_ghi:[…], chua_ghi:[…], loi}`; **không rollback** phần đã ghi (mỗi SP một giao dịch). Gửi lại cùng bản nháp là làm tiếp: server tính lại diff từ CDB nên chỉ ghi phần còn thiếu. UI làm tươi hiện trạng (kể cả `dau_van_tay`) để làm tiếp.
5. Ghi **nhật ký** vào sqlite phía tool trước/sau (`phancong_nhat_ky`: id, thời gian, người, `ma_kh`, tóm tắt, JSON thay đổi, kết quả). Bản ghi `dang_ghi` quá 1 giờ coi là "gián đoạn" khi hiển thị (tool chết giữa chừng). `NguoiTao/NguoiSua` = tên đăng nhập tool; `GhiChu=''`.
- **KHÔNG** dùng `usp_KhoaHoc_GiaoVien_Delete`, `usp_KhoaHoc_XeTap_Delete`, `usp_VoHieuLucKhoaHoc*` (xóa lan nhiều dòng/nhiều khóa).
```
 Nhân viên        Giao diện (React)                 Server tool (FastAPI)             CDB đích
    │  mở khóa        │  GET /khoa/{ma_kh}                │  đọc hiện trạng ────────────>│
    │────────────────>│──────────────────────────────────>│<─────────────────────────────│
    │                 │<──────── hien_trang + dau_van_tay │                              │
    │  sửa bản nháp   │  POST /kiem-tra (debounce 250ms)  │  luật thuần, không ghi       │
    │────────────────>│──────────────────────────────────>│                              │
    │  bấm Ghi        │  POST /ghi {nháp, dau_van_tay}    │  khóa theo ma_kh ──> 409 dang_ghi
    │────────────────>│──────────────────────────────────>│  băm CDB ≠ dau_van_tay ──> 409 khoa_da_doi
    │                 │                                   │  diff rỗng ──> 200 "Không có thay đổi"
    │                 │                                   │  ⛔ ──> 409 · ⚠ chưa xác nhận ──> 409
    │                 │                                   │  xóa → thêm → sửa, mỗi dòng một SP ──>│
    │                 │<── {ok, da_ghi, chua_ghi, loi} ───│  nhật ký sqlite              │
    │  thấy kết quả   │  làm tươi hiện trạng, xóa nháp    │                              │
```

### 11E.7 Luật kiểm (`phancong_rules.py`) — công thức đúng CDB
Với khoảng `[bd, kt)` (datetime): **trùng** ⇔ `NOT (kt <= bd_cũ OR bd >= kt_cũ)`.
**Thuật ngữ:** **GV loại TH/AL** = nhãn danh mục `LoaiHinh_DaoTao`; **GV dạy thực hành** = có ≥1 phân công môn 6 trong bản nháp. Mọi luật ghép xe, "GV thực hành chưa có xe", gợi ý ghép xe xét theo **GV dạy thực hành**; nút "Chọn GV TH hợp hạng" xét theo **loại TH và AL**.
| Mức | Luật |
|---|---|
| ⛔ Chặn | thiếu môn · môn ∉ `DM_MonHoc` (`mon_khong_ton_tai`) · thiếu ngày · `bd >= kt` · `bd <= NgayKG(00:00)` · `kt >= NgayBG + 23:59:59` · GV chưa thuộc khóa · GV/xe `TrangThai=0` · ghép xe: xe ∉ danh sách xe khóa · GV không có phân công môn 6 · xe có `min(NgayHHGPXTL, NgayHHGCNKD) < NgayBG` |
| ⚠ Cảnh báo | GV/xe trùng thời gian với **mọi dòng cờ=0 `TrangThai=1`** (khóa khác **và cùng khóa**, loại chính dòng đang sửa; cùng ngày khác giờ **không** trùng) · 1 xe 2 GV / 1 GV 2 xe chồng giờ (**đổi từ ⛔ sang ⚠ ngày 10/10/2026** — CDB chỉ trả câu cảnh báo, user chốt vẫn cho phân; CHANGES #55) · hạng GV không hợp hạng khóa **khi GV có phân công môn 6** (`gv_hop_hang`: khóa B/B.01/C1 nhận mọi `CacHangGPLXDuocDT ∈ {B, C1, C, D1, D2, D, E}` — GV có chứng chỉ thực hành B dạy được khóa C1; khóa hạng khác: hạng khóa ∈ hạng được dạy; GV chỉ dạy lý thuyết không xét hạng) · hạng xe ≠ hạng xe của khóa · phân công môn 6: **tính theo cả GV** — đợt môn 6 kết thúc xa nhất vẫn trước `NgayBG` thì báo 1 lần/GV (ở dòng đó; CHANGES #58) · GV loại `LT` được phân công môn 6 (`gv_lt_day_thuc_hanh`; AL/TH không báo) · GV trong khóa chưa có phân công · GV dạy thực hành chưa có xe · khóa đã có gói `DANG_KY_KHOA_HOC` (DKKH) |
| ℹ Thông tin | xe thuộc khóa chưa ghép (**không** làm khóa thành "Cần xử lý" ở rà soát — CHANGES #58) |
- **Không còn cảnh báo "đang dạy/chạy khóa khác chưa kết thúc" ở cột Kiểm tra khóa** (10/10/2026): `usp_CheckWarningGiaoVien`/`…XeTap` của CDB chỉ báo lúc **chọn** GV/xe vào khóa, không so ngày/giờ; ở tool nó là huy hiệu "Đang ở khóa Y" + hộp xác nhận khi thêm (BuocGiaoVien) và ghi chú trong hộp "Thêm xe". Gợi ý ghép xe vẫn ưu tiên xe ít cảnh báo (xe trùng bị đẩy xuống cuối, không bị loại). Ghi chú "đang ở khóa Y" còn tới **hết ngày bế giảng** (`NgayBG >= hôm nay`, CHANGES #58 — không cộng thêm 1 ngày như CDB).
- **Giới hạn đầu vào** (422 trước khi vào luật): `ma_kh/ma/xe` ≤ 30 · `dia_diem` ≤ 255 (cột `nvarchar(255)`) · `mon` ≤ 20 phần tử · `tu/den` ≤ 25 ký tự — để lỗi độ dài không nổ giữa lúc ghi.
- **`xac_nhan_csdl_that` là cổng thao tác (chống bấm nhầm), không phải kiểm soát an ninh.** An ninh thật = phiên đăng nhập tool + `target_key` lấy từ cấu hình phía server + tool chỉ nghe `127.0.0.1`.
- **Hiệu năng** (đo 10/10/2026, CDB dev): `/kiem-tra` 12 ms ở khóa lớn nhất (54 dòng); xem lại nếu một khóa vượt ~500 dòng.
- **Mở:** gói DKKH/BC1 có chứa GV/xe hay không chưa xác minh (chuỗi XML của phần mềm CDB có `MA_GIAO_VIEN`, `BIEN_SO_XE`, `NGAY_HIEU_LUC`) → hiện đặt mức ⚠; nếu hóa ra có thì nâng lên yêu cầu kết xuất lại.

### 11E.8 Rà soát khóa (PCG-05)
Một truy vấn tổng hợp theo `MaKH`: số GV cờ=1; số GV có ≥1 dòng cờ=0 ∈ danh sách; số GV cờ=0 ngoài danh sách; số xe cờ=1; số xe cờ=1 chưa có dòng cờ=0; số xe cờ=0 ngoài danh sách. Chỉ đọc. **Kết luận `Cần xử lý`** ⇔ không có GV nào trong danh sách · hoặc có GV chưa phân công · hoặc có phân công/ghép xe ngoài danh sách. **Xe chưa ghép chỉ là thông tin** (CHANGES #58).

### 11E.9 Kiểm thử
- Unit `phancong_rules` (thuần): nửa mở (chạm đầu mút), cùng ngày khác giờ, lịch 00:00 chiếm mọi giờ, phạm vi khóa (00:00 KG, 23:59:59 BG), cùng khóa chặn, 1-1 GV–xe, hết hạn giấy phép.
- API `kiem-tra`/`ghi` bằng cursor giả (mẫu `test_ketqua_sua_sau_gui.py`): 409 khi còn lỗi chặn, 409 khi thiếu xác nhận cảnh báo, thứ tự ghi, lỗi giữa chừng trả đã/chưa ghi, không bao giờ gọi SP xóa lan.
- `tests/test_phancong_kiemthu.py` (/kiemthu 10–11/10/2026): thứ tự ghi giữa các nhóm · luật "dữ liệu cũ" không hạ nhầm dòng mới/mồ côi · cổng 400 trước 409 · `dau_van_tay` → 409 `khoa_da_doi` · khóa ghi → 409 `dang_ghi` · giới hạn đầu vào · `mon_khong_ton_tai` · bản nháp không đổi → 200.
- Ghi thật vào CDB → nghiệm thu máy CSDT (mức 1).

### 11E.10 Hạn giấy tờ + GV/xe ngưng còn phân công (PCG-06, CHANGES #66) — chỉ đọc
> Bổ sung 12/10/2026. Cột đã **verify trực tiếp trên DB đích 12/10/2026**: `XeTap.NgayHHGPXTL`, `XeTap.NgayHHGCNKD`, `XeTap.TrangThai` (bit) · `GiaoVien.NgayHHGPLX`, `GiaoVien.TrangThai` (bit) · `KhoaHoc.NgayBG`. Số liệu mẫu: 89 xe (82 hoạt động; 5 còn ≤ 30 ngày) · 87 GV (3 hết hạn GPLX, 1 còn ≤ 30 ngày) · chưa có GV/xe ngưng còn trong khóa chưa bế giảng.

- **Endpoint:** `GET /local/phancong/han-giay-to?ngay=30` — gác session + `target_key` như §11E.2. Một truy vấn cho mỗi nhóm, lọc `MaCSDT` = mã CSĐT của máy (như rà soát PCG-05), `ngay` mặc định 30, giới hạn 1..365.
- **Nhóm xe:** `XeTap` có `TrangThai=1` và (`NgayHHGPXTL` hoặc `NgayHHGCNKD`) `< hôm nay` → `het_han`; `BETWEEN hôm nay AND hôm nay+ngay` → `sap_het`; cả hai ngày NULL → mục thông tin `chua_khai`. Mỗi dòng kèm các khóa `KhoaHoc.NgayBG >= hôm nay` có dòng `KhoaHoc_XeTap` (mọi cờ) của xe đó.
- **Nhóm giáo viên:** tương tự với `GiaoVien.NgayHHGPLX`, khóa lấy từ `KhoaHoc_GiaoVien` (mọi cờ).
- **Nhóm ngưng còn phân công:** `GiaoVien`/`XeTap` `TrangThai=0` JOIN `KhoaHoc_GiaoVien`/`KhoaHoc_XeTap` JOIN `KhoaHoc` có `NgayBG >= hôm nay`. **Dòng khóa và danh mục khóa đều lọc `TrangThai=1`** (dòng đã bỏ khỏi khóa / khóa đã ngưng không tính). Mock: `ui-mock/phancong.html` (tab "Hạn giấy tờ").
- **Luật thuần:** `phan_loai_han(ngay_hh, hom_nay, nguong)` đặt trong `phancong_rules.py` (thuần, không DB). **Đọc dữ liệu ở module riêng `phancong_hangiayto.py`** (theo tiền lệ `phancong_rasoat.py`), **không** dùng `gp_het_som_nhat` — hàm đó chỉ chọn ngày sớm nhất, còn PCG-06 cần tách từng loại giấy (giấy phép / kiểm định) trên cùng một dòng. **Khác §11E.7:** luật ⛔ "hết hạn trước bế giảng" xét theo từng khóa lúc ghi; PCG-06 chỉ xét theo **hôm nay** trên toàn cơ sở.
- **Bất biến:** chỉ đọc; mọi SQL tham số hóa; không đổi `TrangThai`.
- **Kiểm thử:** unit `phan_loai_han` (đúng ngày hôm nay, ngày biên, NULL, ngưỡng) + API bằng cursor giả.

> **Phục vụ:** PCG-01/02/03/04/05/06. Quyết định: TDD-decisions §22. Liên quan: §11D (cùng DB đích, cùng cổng DKKH).

---

## 11F. Tốt nghiệp & Báo cáo 2 (tool — workspace riêng, DB Nạp) — TNB-01..07 (CHANGES #60–#63)

> Ghi **DB Nạp `GPLX_CSDT`** (bảng `NguoiLX_HoSo`, `BaoCaoII`) **chỉ qua SP có sẵn** để PM cũ thấy y chang. Không bảng/cột/SP mới. Nguồn sự thật = định nghĩa SP + dữ liệu đã probe 11/10/2026. Quyết định: TDD-decisions §23. Mock: `ui-mock/tnbc2.html`. Đã qua `/reviewtdd` 11/10/2026 (biên bản `tdd-review-11-10-2026-tnb.md`). **Cập nhật theo code đã làm ở backend task 96–105** (CHANGES #63): mục này mô tả hành vi thực tế của `tn_bc2_*`.

### 11F.0 Kiến trúc
- **Backend:** `tool/app/routers/tn_bc2.py` (mount `require_session` ở `main.py`, như `phancong.py`) + `tool/app/tn_bc2_rules.py` (**luật thuần, không DB**: phân loại hạng, tập trạng thái ứng viên, chuyển trạng thái được phép, quy tắc đánh số) + `tool/app/tn_bc2_service.py` (đọc DB Nạp, ghi bằng SP) + `tool/app/tn_bc2_nhat_ky.py` (nhật ký + lô, sqlite). Kết nối `sqlserver_conn()` (`tool/app/db.py`, autocommit giữ applock như `nap.py`). **Không** đụng CDB, **không** staging: tool và PM cũ dùng chung DB → luôn đọc lại trước khi ghi.
- **Frontend:** phân hệ mới `tnbc2` trong `tool/webui/src/lib/modules.ts` (route `/tot-nghiep-bc2/*`, `db: "GPLX_CSDT"`, băng cam "CSDL: DB Nạp"), 4 tab: **Tốt nghiệp** · **Báo cáo 2** (danh sách · **Lập BC2 / Thêm HV 3 bước** · xem/gỡ) · **Cứu trạng thái** · Nhật ký; bám `ui-mock/tnbc2.html` v2. Giao diện chỉ dùng **tên trạng thái nghiệp vụ** (kèm mã nhỏ + chú giải), không hiện tên SP/`TT_XuLy`.
- **Nhật ký + lô:** sqlite phía tool theo mẫu `phancong_nhat_ky.py`: bảng `tnbc2_nhat_ky` (từng thao tác), `tnbc2_lo` (một "lô" = một lần thêm/gỡ/ghi/hủy/cứu/hoàn tác, khóa `lo_id`) và `tnbc2_lo_hv` (từng HV của lô: `da_them`/`da_go`/`da_ghi`/`da_huy`/`da_cuu`/`bo_qua`/`chua_ghi`) — nguồn của "Làm tiếp", tiến độ sau khi tool khởi động lại và hoàn tác. **Chỉ lưu** `ma_dk`, số lượng, loại thao tác, kết quả đã/chưa ghi, tên đăng nhập, `lo_id`, `ly_do` — **không** lưu họ tên / số CMT; danh sách CMT dán vào không ghi log; thông báo lỗi trả về không kèm CMT (§12).
- **Chạy nền + tiến độ chung:** thao tác nhiều HV (`/bc2/lap`, `/bc2/{ma}/go`, `/bc2/{ma}/hoan-tac`, `/tot-nghiep/ghi`, `/tot-nghiep/huy`) kiểm nhanh ĐỒNG BỘ (4xx/409 ngay) rồi chạy ở thread nền, idempotent theo `lo_id` do client sinh mỗi lần xác nhận (cùng `lo_id` đang chạy/đã xong → trả kết quả hiện có, không chạy lần hai; dở dang vì tool chết → "Làm tiếp" chạy lại cùng danh sách). **`GET /bc2/lo/{lo_id}`** là đường theo dõi DÙNG CHUNG cho mọi loại lô: `{trang_thai: dang_chay|xong|loi_giua_chung|that_bai, xu_ly, tong, xong, …kết quả}`; tool khởi động lại thì đọc từ sqlite (`bi_gian_doan`). Lần "Làm tiếp" bị 409 vẫn GIỮ danh sách đã ghi của lần trước (`loi_lan_cuoi`). Cắt cứu trạng thái (một HV) đồng bộ, vẫn idempotent theo `lo_id`.
- **Khóa ghi chung:** mọi thao tác **ghi** của phân hệ (tốt nghiệp, lập/thêm/gỡ BC2, xóa BC2, cứu) chạy trong một `sp_getapplock` tên cố định `tnbc2_ghi` (tool một máy, mỗi lần ghi ngắn). Khóa theo BC2 / theo khóa học **không đủ**: hai BC2 cùng ghi một HV không loại trừ nhau.

### 11F.1 Dữ liệu DB Nạp dùng (đã verify)
| Bảng / SP | Dùng cho | Ghi chú |
|---|---|---|
| `NguoiLX_HoSo` | `MaDK, SoHoSo, MaKhoaHoc, HangGPLX, HangDaoTao, TT_XuLy, TT_XuLy_Old, MaBC2, SoSoTN, NgayVaoSoTN, SoQuyetDinhTN, NgayRaQDTN, SoGiayCNTN, NgayInGiayTN, SoCCN, Transfer_flag` | `MaBC1` gần như trống → **không dùng** làm liên kết BC1. Chỉ index trên `MaDK` (39.929 dòng) — không thêm được index |
| `NguoiLX` | `HoVaTen, NgaySinh (varchar8), SoCMT` | tên/ngày sinh/CMT hiển thị |
| `KhoaHoc` | `MaKH, TenKH, NgayKG, NgayBG` | điều kiện "đã bế giảng" |
| `BaoCaoI` | `MaBCI, MaKH, SoBaoCao, SoHocSinh` | BC1 của khóa (**1 khóa ≤ 1 BC1**, 0 khóa có > 1); chỉ đọc |
| `BaoCaoII` | `MaBCII (=SoBaoCao), MaBCI, TongSoThiSinh, TrangThai(0 mở/1 đóng), TT_Xuly(không dùng)` | FK `BaoCaoII→BaoCaoI` CASCADE; **không FK từ `NguoiLX_HoSo.MaBC2`** (có 91 HV `MaBC2` trỏ BC2 không còn tồn tại) |
| `usp_NguoiLX_HoSo_Update_CNTN` | ghi tốt nghiệp (6 trường); hủy | CHỈ ghi 6 cột (`SoSoTN, NgayVaoSoTN, SoQuyetDinhTN, NgayRaQDTN, SoGiayCNTN, NgayInGiayTN`) + `TT_XuLy`; **không** ghi `NgaySua/NguoiSua/Transfer_flag`; **không kiểm trạng thái** (ghi đè cả HV `≥ 11`). `LEN(@sSoCNTN)>0` và `03` → `09`; rỗng và `09` → `03` (hủy); trạng thái khác giữ nguyên. Truyền `''` (không `NULL`: `LEN(NULL)` rẽ sang nhánh hủy). `@sSoSoCNTN` nhận 150 ký tự nhưng cột 50 |
| `usp_BaoCaoII_Insert` | tạo BC2 | tự `BEGIN TRANSACTION` |
| `usp_NguoiLX_HoSo_ThemHS_BC2` | lấy ứng viên | nhánh mô tô lỗi `OR 'B1m'` → lọc lại; chỉ trả `TT_XuLy ∈ {03,09,14,17,18}`; **không trả** `TT_XuLy`, `MaBC2`, hạng, `NgayBG`; lọc khóa bằng `LIKE '%'+@MaKH+'%'` |
| `usp_NguoiLX_Update_ThemHSBC2` | thêm HV | `MaBC2`, `TT_XuLy='11'`, `TT_XuLy_Old`=cũ — **không có điều kiện trạng thái** (gọi lại cho HV đã `11` thì `TT_XuLy_Old='11'`); `@SoHoSo` là `varchar(5)` và không dùng trong `WHERE` |
| `usp_NguoiLXHoSo_Update_DanhSachHocSinhBC2` | gỡ HV (`@TrangThaiXuLy=101`) | `TT_XuLy=TT_XuLy_Old`, `MaBC2=''`; không điều kiện (HV có kết quả bị đưa về trạng thái cũ → mất kết quả); `@SoHoSo` `varchar(5)` |
| `usp_NguoiLX_HoSo_UpdateTTXLy` | cứu trạng thái | `TT_XuLy_Old`=cũ (**GHI ĐÈ** — hoàn tác không dựa vào cột này), `Transfer_flag=0` (1 nếu `04`); không kiểm điều kiện nào |
| `usp_BaoCaoII_Delete` | xóa BC2 rỗng | chỉ `DELETE` đúng dòng BC2, **không kiểm HV** → tool phải đếm trước (§11F.6) |
| `usp_BaoCaoI_SelectAll`, `usp_BaoCaoII_Search`, `usp_BaoCao2_DSHS` | đọc | |

**Collation:** DB `Latin1_General_CI_AS`. `BaoCaoII.MaBCII` / `BaoCaoI.MaBCI` là `varchar` → chữ `Đ` lưu thành byte `0xD0`, đọc ra `Ð`; `SoBaoCao` là `nvarchar` giữ `Đ`. Mọi so sánh/ghi số BC2 qua `rules.khoa_so_bc2` (gộp `Ð`/`Đ`, không phân biệt hoa/thường) và `rules.dang_luu_ma_bcii` (dạng DB).

**Độ dài cột (đã verify, kiểm trước khi gọi SP):** `SoSoTN` ≤ 50 · `SoQuyetDinhTN` ≤ 50 · `SoGiayCNTN` ≤ 20 · `SoCCN` ≤ 20 · `BaoCaoII.MaBCII` ≤ 13 · `SoBaoCao` ≤ 20 · `GhiChu` ≤ 255 · `NguoiTao/NguoiSua` ≤ 30. (SP `Update_CNTN` nhận số sổ tới 150 ký tự nhưng cột chỉ 50 → quá thì lỗi cắt chuỗi.)

### 11F.2 Tốt nghiệp ô tô (TNB-01/02)
- **Loại ô tô** = `HangGPLX` **không** chứa `A` và khác `B1m`. Phạm vi mặc định: `KhoaHoc.NgayBG` ∈ [hôm nay − 1 tháng − 1 năm, hôm nay]; công tắc "khóa cũ" bỏ cận dưới; khóa `NgayBG > hôm nay` chỉ đọc.
- Ghi: với mỗi HV `EXEC usp_NguoiLX_HoSo_Update_CNTN @MaDK, @SoHoSo, @sSoSoCNTN, @dNgayVaoSoCNTN, @sSoQuyetDinh, @dNgayQuyetDinh, @sSoCNTN, @dNgayInCNTN`. **Lưu sổ trước**: `@sSoCNTN=''` + HV đang `03` → chỉ ghi sổ, ở lại `03`. **Hủy**: HV đang `09`, gửi `@sSoCNTN=''` + giữ nguyên các giá trị sổ hiện có (đọc lại rồi truyền) → SP đưa `09→03`.
- **HV đã `≥ 11` hoặc có `MaBC2`:** **sửa/hủy số giấy đã có → chặn** (SP chỉ đổi trạng thái khi `03`/`09` nhưng vẫn xóa số giấy). **Ghi số giấy lần đầu** cho HV có số giấy rỗng → được, kèm cảnh báo "báo cáo đã lập không đổi theo" (khớp TNB-01 edge).
- **Kiểm trùng `SoGiayCNTN`** trong DB và trong lô **loại trừ chính HV đó** (bấm "Ghi" lại không tự báo trùng); mọi lần ghi nằm trong khóa `tnbc2_ghi`.
- **Xem lại (chạy thử, không ghi):** `POST /tot-nghiep/xem-lai` trả số HV, khoảng số giấy, trùng trong lô/DB, cảnh báo — dùng cho "kiểm trùng ngay khi gõ" và hộp "Xem lại" của TNB-01.
- **Số giấy liên tiếp:** dạng `N1|<n>`, **một dãy chung toàn cơ sở** (không đánh lại theo năm/khóa; lớn nhất 11/10/2026 là `N1|7328`); `so_giay_ke_tiep` = tiền tố của số in gần nhất + `MAX+1` (→ `N1|7329`). Tool chỉ gợi ý; nhân viên sửa tay từng ô, dán cột Excel.
- **Số sổ / quyết định / ngày là MỘT BỘ CHUNG cho cả lượt ghi** (user chốt 11/10/2026): `so_chung` điền sẵn từ bộ phổ biến nhất của HV cùng khóa, sửa ở ô "điền chung"; không có ô riêng từng HV — cần sổ khác thì ghi theo nhóm (hai lượt). Số giấy thì theo từng dòng.
- **Tìm không dấu:** làm trong Python trên danh sách đã tải (`rules.bo_dau`: bỏ dấu, `đ→d`); CMT khớp chuỗi con, mã đăng ký không phân biệt hoa/thường.
- **API đọc:** `GET /khoa?loai=oto&cu=` (mỗi khóa: tổng, chưa tốt nghiệp `03`, đã tốt nghiệp `09`, đã vào BC2 `≥11`/có `MaBC2`, `ghi_duoc`, `khoa_cu`; kèm `so_giay_ke_tiep`); `GET /tot-nghiep/hv?ma_kh=&q=&trang_thai=` (HV ô tô của khóa: sổ/QĐ/giấy/ngày, `trang_thai_tn`, `sua_duoc`, `ly_do_khoa`, `so_chung`); khóa mô tô → 400 `chi_o_to`; khóa chưa bế giảng hiện nhưng `ghi_duoc=false`.
- **Luật ghi (đã chốt):** (A) **trùng số giấy chỉ chặn khi ĐỔI sang số đang thuộc HV khác** (DB còn 463 số trùng cũ của PM cũ; HV đang giữ đúng số đó thì không chặn, chỉ báo `trung_co_san`; trùng trong lô → cả các dòng đó bị chặn) · (B) HV chưa tới bước tốt nghiệp (không phải `03/09/≥11`, vd `01/02/04/10`) bị chặn — phải đưa về `03` qua Cứu trạng thái trước · (C) cấp số giấy cần có cả **số sổ và số quyết định** · HV `03/09` mà đã gắn `MaBC2` (dữ liệu bất thường — SP sẽ đổi `03→09` dù báo cáo đã lập) → chặn · HV `09` để trống số giấy KHÔNG ngầm hủy (dùng "Hủy") · cảnh báo `thieu_ngay_in`, `khoa_cu`, `bao_cao_da_lap_khong_doi_theo` cần `da_xem_canh_bao`.
- **Kết quả dự kiến mỗi dòng** (`xem-lai` và `ghi` dùng CHUNG luật `phan_tich_dong_tn`): `se_len_09` · `luu_so_truoc` · `giu_09_sua_thong_tin` · `khong_doi_trang_thai_da_vao_bc2` · `khong_doi` · `bo_qua` · `chan`.
- **`POST /tot-nghiep/ghi`** `{lo_id, ma_kh, dong[{ma_dk, so_giay}], chung{so_so_tn, ngay_vao_so, so_quyet_dinh, ngay_ra_qd, ngay_in}, da_xem_canh_bao, xac_nhan_csdl_that}`: kiểm nhanh đồng bộ (khóa ô tô + đã bế giảng, ≥1 dòng ghi được, cảnh báo đã xác nhận) → chạy nền; dòng chặn BỎ QUA kèm lý do, dòng hợp lệ vẫn ghi; từng HV: đọc lại sát trước SP (đổi giữa chừng → `doi_giua_chung`; số giấy vừa bị dùng → `trung_db`), `EXEC`, nhật ký ngay sau SP, đọc lại sau SP chỉ cảnh báo.
- **`POST /tot-nghiep/huy`** `{lo_id, ma_kh, ds_ma_dk[], xac_nhan_csdl_that}`: chỉ HV còn `09` và CHƯA gắn BC2 → `03`; **giữ nguyên sổ/QĐ/ngày (kể cả ngày in), chỉ số giấy = `''`**; kết quả trả `da_huy[{ma_dk, so_giay_cu}]`; HV `≥11`/có `MaBC2` → `da_vao_bc2`; đã ở `03` → `khong_con_o_09`. Không dùng `Update_HSTotNghiep` (dựa `TT_XuLy_Old`, trống ở nhiều HV).
```
 Ô TÔ    03 ──(sổ + số giấy · TNB-01)──> 09        MÔ TÔ   03   (không có bước tốt nghiệp)
         09 ──(hủy · TNB-02)──────────> 03                  │
              chặn khi đã ≥ 11                               │
 09 ──┐                                                      │
 14 ──┼── thêm vào BC2 đang mở (TNB-04) ──> 11 <─────────────┘ (mô tô: từ 03 hoặc 14/17/18)
 17 ──┤  thi lại, không tích sẵn            │
 18 ──┘                                     ├─ gỡ (TNB-05, chỉ khi còn 11) ──> về TT_XuLy_Old
                                            └─ PM cũ: gửi ──> 12 ──> 13/14 ──> 16/17/18 ──> 19
 Cứu (TNB-06):  01/02/03/04/10/12/13 ──> 09/14/17/18      chặn nguồn 11/16/19
                hoàn tác = về trạng thái ngay trước đó, miễn luật đích, chỉ khi HV chưa bị đổi tiếp
 Tool làm:  03↔09 · →11 · 11→cũ · cứu          PM cũ làm:  11→12→13/14 · 16/17/18 · 19 · đóng BC2
```

> **Cập nhật v6.10 (UI task 106-115):** màn Tốt nghiệp cho tích lẫn HV chưa/đã tốt nghiệp trong cùng lượt `xem-lai` → `ghi` (server phân tích từng dòng: `se_len_09` / `giu_09_sua_thong_tin`); nút Hủy chỉ bật khi mọi HV đã chọn đều `09` chưa vào BC2; "Chọn tất cả" chỉ nhóm `03` (hoặc nhóm đang lọc). *Vì sao:* bộ sổ/QĐ điền chung sẽ đè sổ của HV đã tốt nghiệp nếu "chọn tất cả" lẫn cả họ.

### 11F.3 Tạo BC2 (TNB-03)
- `EXEC usp_BaoCaoII_Insert @MaBCII=<SoBaoCao>, @MaBCI, @MaCSDT, @SoBaoCao, @NgayBaoCao, @TongSoThiSinh, @GhiChu, @TrangThai=0, @NguoiTao, @NguoiSua, @NgayTao, @NgaySua`. `MaBCII` varchar(13) → kiểm độ dài; `SoBaoCao` ≤ 20, `GhiChu` ≤ 255.
- **BC1 suy từ khóa** (1 khóa ≤ 1 BC1) — luồng 3 bước không có bước chọn BC1. Khóa đã bế giảng mà chưa có BC1 → hiện mờ ở bước ① "chưa có BC1 — chưa lập BC2 được"; chặn tạo BC2 thiếu BC1.
- **Đánh số (gợi ý, sửa được, kiểm trùng):** ô tô = `MAX(n)+1` trong các `MaBCII` dạng `^\d+/<năm>$`; mô tô = `BaoCaoI.SoBaoCao` bỏ tiền tố `A1A2` (`A1A2870/26-TTTĐ` → `870/26-TTTĐ`).
- **`TongSoThiSinh`:** mô tô = `BaoCaoI.SoHocSinh`; ô tô = **số HV còn lại sau khi đọc lại và loại HV đã đổi**, tính **trước** `Insert` (trong `/bc2/lap`), 0 khi tạo rỗng. **Không** đếm lại khi thêm/gỡ (đúng PM cũ).
- Chống tạo đôi: trước khi thử lại, kiểm `BaoCaoII` đã có `MaBCII` đó chưa (kết hợp `lo_id` §11F.4).

> **Cập nhật v6.10:** `GET /bc2/goi-y-so` và `GET /bc2/ung-vien` trả thêm `bc1.ngay_bao_cao` (ISO, rỗng nếu thiếu; đọc `BaoCaoI.NgayBaoCao`) để form hiện "số BC1 · ngày · số học sinh". Form bắt buộc ngày báo cáo; `POST /bc2` lỗi 5xx / mất kết nối → UI gửi lại với `thu_lai=true` (`da_ton_tai` chỉ trả mã BC2 — UI không được giả định có `so_bao_cao`/`ngay_bao_cao`).

### 11F.4 Lập BC2 + thêm / gỡ HV (TNB-03/04/05) — luồng 3 bước (CHANGES #61)
- **Nguồn ứng viên (một lần cho cả CSĐT):** `usp_NguoiLX_HoSo_ThemHS_BC2(@MaDK='',@TenHocSinh='',@SoCMND='',@NgaySinh='',@MaKH='',@TenKH='',@HangDT=<''|'A1'>,@TrangThai=0,@maBC2='')` — `@HangDT=''` cho ô tô, `'A1'` cho mô tô; **`@MaKH=''`** vì SP lọc khóa bằng `LIKE` nên truyền khóa cụ thể sẽ **không trả HV thi lại của khóa khác**. Đo 11/10/2026: ≈ 3.450 HV ô tô / 3.240 HV mô tô, 0,07–0,12 giây. Rồi **một `SELECT` bổ sung** theo `MaDK` lấy `TT_XuLy, MaBC2, HangGPLX, NgayBG, BaoCaoII.TrangThai` (SP không trả các cột này), **phân nhóm trong Python** bằng `tn_bc2_rules.phan_nhom(hv, loai, khoa_bc1, thi_lai_thang)`. Kết quả giữ trong bộ nhớ ~30 giây, bỏ khi "Làm tươi" hoặc sau mỗi lần ghi.
- **Bốn nhóm** (xét theo thứ tự trong sơ đồ B, trúng nhóm đầu thì dừng):
  | Nhóm | Điều kiện (ô tô / mô tô) | Mặc định |
  |---|---|---|
  | `khong_duoc` | khóa chưa bế giảng · `TT_XuLy ∈ {11,13,16,19}` (gồm HV đang ở BC2 mở khác — lý do "đang ở BC2 số …, gỡ khỏi đó trước") · sai loại hạng | ẩn, kèm `ly_do` |
  | `can_xem` | **khóa đang chọn**: ô tô `03` chưa tốt nghiệp · ô tô `09` mà `SoGiayCNTN=''` | không tích, kèm `goi_y_xu_ly` |
  | `thi_lai` | `TT_XuLy ∈ {14,17,18}` **bất kể khóa** · không thuộc BC2 `TrangThai=0` | không tích; trả đủ kèm `tuoi_thang` (theo `KhoaHoc.NgayBG` của khóa gốc); `thi_lai_thang` mặc định 12 chỉ quyết định nút "Thêm HV thi lại trong N tháng" tích những người ≤ N tháng |
  | `san_sang` | **khóa đang chọn** (`MaKhoaHoc = BaoCaoI.MaKH`) · ô tô `09` có `SoGiayCNTN<>''` / mô tô `03` · `MaBC2` rỗng, hoặc không tồn tại trong `BaoCaoII`, hoặc BC2 đã đóng · khóa `NgayBG ≤ hôm nay` | tích sẵn |
  HV ô tô `09` / mô tô `03` của khóa **khác** không hiện ở khóa này — chọn đúng khóa của họ ở bước ①.
  **Nguồn của `khong_duoc` / trạng thái lạ:** SP KHÔNG trả HV `11/13/16/19` hay `01/02/04/10/12`, nên `ung-vien` đọc thêm (một truy vấn theo khóa đang chọn, không cache, cắt 500 dòng, `dem.khong_duoc` đếm đủ) các HV của khóa có `TT_XuLy ∉ {03,09,14,17,18}`: `11` ở BC2 mở khác → `khong_duoc` (`dang_o_bc2_mo`, gợi ý gỡ), `11` ở BC2 đã đóng → `da_vao_bc2_dong` ("mở lại ở PM cũ"), `13/16/19` → `co_ket_qua_cuoi`, `01/02/04/10/12` → `can_xem` kèm gợi ý Cứu trạng thái, mã khác → `trang_thai_ngoai_tap`. Nhóm `khong_duoc` chỉ gồm HV của khóa đang chọn.
- **Kiểm đầu vào (409, đồng bộ):** `kiem_dau_vao` — chưa có BC2 mà khóa chưa có BC1 → `khoa_chua_co_bc1`; BC2 không thuộc BC1 của khóa → `bc2_khac_khoa`; BC2 đã đóng → `bc2_da_dong`; không tồn tại → 404 `bc2_khong_ton_tai`.
- **`POST /bc2`** (tạo BC2 rỗng, đồng bộ): `{ma_kh, so_bao_cao, ngay_bao_cao, ghi_chu, da_xem_canh_bao, thu_lai, xac_nhan_csdl_that}`. Trùng số → 409 `trung_so`; **`thu_lai=true`** (gửi lại sau khi không biết kết quả lần trước) mà BC2 đó đã có đúng BC1 này → `da_ton_tai` (chống tạo đôi); khóa mô tô đã có BC2 → 409 `can_xac_nhan_canh_bao`; khóa ghi bận → 409 `dang_ghi`. Mô tô `TongSoThiSinh` LUÔN = `SoHocSinh` của BC1; `NguoiTao` = tên đăng nhập tool; `GhiChu`/`NguoiSua` = NULL, `NgayTao = NgaySua` (đúng PM cũ). `GET /bc2/goi-y-so?ma_kh=` trả số gợi ý + BC1 + BC2 đã có.
- **Luồng:** ① `GET /bc2/khoa-san-sang?loai=` — đếm 3 nhóm **từ chính tập đã tải** (không gọi SP theo từng khóa); khóa hiện nếu còn ≥ 1 HV ở nhóm đưa được; khóa chưa có BC1 hiện mờ · ② `GET /bc2/ung-vien?ma_kh=&ma_bc2=&thi_lai_thang=` (4 nhóm + đếm) · ③ `POST /bc2/lap`.
- **`POST /bc2/lap` — chạy nền, idempotent:** client sinh `lo_id` (uuid) mỗi lần xác nhận; server nhận cùng `lo_id` thì trả kết quả đang chạy/đã xong, **không chạy lần hai**. Trả ngay `{lo_id}`; giao diện hỏi `GET /bc2/lo/{lo_id}` → `{da_them, bo_qua, tong, xong}` (thanh tiến độ từ 200 HV). Chỉ nhận HV thuộc `san_sang` và `thi_lai`; `can_xem`/`khong_duoc` bị bỏ qua kèm lý do. `loai` suy từ khóa/BC1 phía máy chủ.
- **Thứ tự trong một lần chạy** (giữ `tnbc2_ghi`): ① đọc lại cả lô, `phan_nhom` + luật ⛔ lại trên dữ liệu mới, loại HV đã đổi · ② BC2 có sẵn: đọc `TrangThai`, `=1` (đã đóng) → dừng, không ghi; chưa có: `Insert` với `TongSoThiSinh` = số HV còn lại · ③ từng HV: còn đúng trạng thái lúc tải? → `usp_NguoiLX_Update_ThemHSBC2`; HV **đã `11` đúng BC2 này** tính là "đã thêm", **không gọi lại SP** (gọi lại sẽ đặt `TT_XuLy_Old='11'`) · ④ sau mỗi HV đọc lại: `TT_XuLy_Old='11'` → cảnh báo kèm tên HV + nhật ký · ⑤ **ghi nhật ký sqlite từng HV ngay sau khi SP thành công** (đứt giữa chừng vẫn hoàn tác được phần đã ghi). "Làm tiếp" = chạy lại cùng danh sách với `lo_id` cũ.
- **Dán danh sách:** `POST /bc2/khop-danh-sach` nhận cột CMT/`MaDK` (≤ 5.000 dòng, ≤ 40 ký tự/dòng), trả HV khớp + số dòng không khớp; chỉ tích HV nằm trong `san_sang`/`thi_lai`.
- **Hoàn tác:** `POST /bc2/{ma:path}/hoan-tac` (số BC2 có dấu `/` nên route dùng `{ma:path}`, các route cố định đặt trước) gỡ đúng các HV mà lô **THÊM** gần nhất **của BC2 đang xem** đã thêm (lô phải thêm được ít nhất 1 HV; HV `da_co_tu_truoc` không gỡ), còn `TT_XuLy='11'` và đúng `MaBC2`, BC2 còn mở (cùng SP gỡ); mỗi lô một lần (`da_hoan_tac`); HV có `TT_XuLy_Old` rỗng/`11` bị bỏ qua thay vì ghi rác; nhật ký sqlite mất thì nút ẩn (vẫn gỡ tay bằng TNB-05).
- **Gỡ tay:** `GET /bc2/{ma:path}` (chi tiết + HV: `go_duoc`, `ly_do_khoa`, `canh_bao_tt_cu`, `xoa_duoc`) → `POST /bc2/{ma:path}/go` `{lo_id, ds_ma_dk[], da_xem_canh_bao}` (chạy nền): chỉ HV `TT_XuLy='11'` và đúng BC2, BC2 còn mở: `usp_NguoiLXHoSo_Update_DanhSachHocSinhBC2(@MaDK,@SoHoSo,@MaBC2,@TrangThaiXuLy=101)`. **HV có `TT_XuLy_Old='11'` bị CHẶN** (gỡ ra sẽ kẹt `11` không BC2 — user chốt 11/10/2026, khớp hoàn tác); **`TT_XuLy_Old` rỗng → cảnh báo, cần `da_xem_canh_bao`** (gỡ ra về giá trị rỗng); HV đã có kết quả/đổi giữa chừng → bỏ qua kèm lý do.
- **Xóa BC2:** `DELETE /bc2/{ma:path}?xac_nhan_csdl_that=true` — BC2 **còn mở** và `COUNT(*) NguoiLX_HoSo WHERE MaBC2=<ma>` (mọi `TT_XuLy`; `TongSoThiSinh` không phải số đếm) = 0 ngay trước SP trong khóa ghi → `usp_BaoCaoII_Delete`, đọc lại xác nhận đã mất. BC2 **đã đóng không xóa ở tool** (409 `bc2_da_dong`).
```
 HV (SP @MaKH='' + SELECT bổ sung)
   │
   ├─ khóa chưa bế giảng · TT∈{11,13,16,19} · sai loại ──────> ⛔ khong_duoc  (kèm lý do;
   │                                                          đang ở BC2 mở: "gỡ khỏi BC2 … trước")
   ├─ [khóa đang chọn] ô tô 03 · hoặc ô tô 09 mà SoGiayCNTN='' ─> ⚠ can_xem   (hướng xử lý 1 chạm)
   ├─ TT∈{14,17,18}, bất kể khóa ────────────────────────────> 🔁 thi_lai    (không tích; gom theo
   │                                                          khóa gốc; có tuoi_thang)
   └─ [khóa đang chọn] ô tô 09 có số giấy · mô tô 03 ─────────> ✅ san_sang   (tích sẵn)
      và MaBC2 rỗng / không tồn tại / BC2 đã đóng
```
```
 Giao diện             Server tool                              DB Nạp                    sqlite nhật ký
   │ xác nhận (lo_id)   │                                         │                            │
   │──POST /bc2/lap────>│ lo_id đã có? → trả kết quả cũ            │                            │
   │<── {lo_id} ────────│ chạy nền, giữ khóa chung tnbc2_ghi       │                            │
   │                    │ 1 đọc lại cả lô ────────────────────────>│ SELECT TT_XuLy, MaBC2…     │
   │                    │ 2 phan_nhom + luật ⛔ → loại HV đã đổi    │                            │
   │                    │ 3 BC2 có sẵn: TrangThai=0? (đóng→dừng)    │                            │
   │                    │   chưa có: Insert, TongSoThiSinh = số     │                            │
   │                    │   HV còn lại ──────────────────────────>│ usp_BaoCaoII_Insert        │
   │                    │ 4 từng HV: còn đúng trạng thái? ghi ────>│ usp_NguoiLX_Update_ThemHSBC2│
   │                    │   (đã 11 đúng BC2 này = "đã thêm")        │                            │
   │                    │ 5 đọc lại; Old='11'? → cảnh báo ─────────>│ SELECT                     │
   │                    │   ghi từng HV ───────────────────────────────────────────────────────>│ ma_dk + lo_id
   │ GET /bc2/lo/{lo_id}│ {da_them, bo_qua, tong, xong}             │                            │
   │ "Hoàn tác"         │ gỡ HV của lô còn 11 đúng BC2 ───────────>│ …DanhSachHocSinhBC2 (101)  │
```

> **Cập nhật v6.10 (bước ③ + xem/gỡ):** (a) UI **chốt** `so_bao_cao`/`ngay_bao_cao`/`ghi_chu` ở lần gửi đầu của một `lo_id` và "Làm tiếp" luôn gửi lại đúng nội dung đó (form có thể mount lại và hỏi lại gợi ý số). (b) Mọi lỗi **sau khi** đã gửi lệnh ghi (kể cả lỗi theo dõi tiến độ) đều dẫn tới "Làm tiếp"; lô `that_bai` quay lại chọn học viên. (c) Hộp Gỡ / Hoàn tác không báo thành công khi `trang_thai ∈ {that_bai, loi_giua_chung}`. (d) Bước ② tự làm tươi khi cửa sổ lấy lại focus nếu lần tải trước > 15 giây; thanh tiến độ từ 200 HV. (e) Hạn chế: `lo_id` chỉ nằm trong bộ nhớ trình duyệt, F5 giữa lúc ghi không "Làm tiếp" được (lô vẫn chạy nền; thấy ở `GET /bc2` và `/nhat-ky`).

### 11F.5 Cứu trạng thái (TNB-06)
- Chuyển được: nguồn ∈ `{01,02,03,04,10,12,13}` → đích ∈ `{09,14,17,18}`; chặn nguồn `{11,16,19}`; đích `09` cần `SoGiayCNTN <> ''` và là ô tô.
- Ghi: `usp_NguoiLX_HoSo_UpdateTTXLy(@MaDK,@SoHoSo,@TT_XuLy)`. Bắt buộc `ly_do` (≤ 255), ghi nhật ký.
- **Hoàn tác** = chuyển về **trạng thái cũ đã lưu trong NHẬT KÝ tool** (không dựa `TT_XuLy_Old` của DB vì SP `UpdateTTXLy` ghi đè nó ở mỗi lần chuyển), **miễn luật đích** (về `03` là hợp lệ dù `03` không thuộc `{09,14,17,18}`); điều kiện duy nhất: HV vẫn đang ở đúng trạng thái vừa cứu (PM cũ chưa đổi tiếp), không thì 409 `da_bi_doi`. Mỗi lần cứu hoàn tác MỘT lần (`da_hoan_tac`). Mất file nhật ký thì mất khả năng hoàn tác (đánh đổi đã chấp nhận).
- **API:** `GET /cuu/tim?q=&loai=` (≥ 2 ký tự; tìm TOÀN DB theo tên không dấu/CMT/mã đăng ký; tối đa 50 kết quả, danh sách giữ trong bộ nhớ 60 giây; mỗi HV kèm `khong_hien` (lý do), `dich[]` (đủ `09/14/17/18` kèm cho/không + lý do), `cuu_duoc`, `khac_loai`) · `POST /cuu/chuyen` `{lo_id, ma_dk, dich, ly_do, loai, xac_nhan_csdl_that}` (một HV, đồng bộ, idempotent theo `lo_id`; `lo_id` đã dùng cho thao tác khác → 409 `lo_id_khong_khop`) · `POST /cuu/hoan-tac` `{lo_id_cuu, lo_id, xac_nhan_csdl_that}`. Cứu HV của khóa chưa bế giảng vẫn được nhưng HV chưa hiện ở danh sách BC2 (giao diện phải nói rõ).
- **Giải thích "vì sao không thấy":** `tn_bc2_rules.giai_thich_khong_hien(hv, loai)` trả một trong: trạng thái ngoài tập · khóa chưa bế giảng (`NgayBG`) · khác loại hạng · đang ở BC2 `<số>` · đã có kết quả cuối.

> **Cập nhật v6.10:** `cuu_chuyen` — nếu cùng `lo_id` còn lô `dang_chay` mà HV **đang đúng ở đích** và nhật ký (ghi *trước* SP: `tt_cu`, `tt_moi`, `ma_dk`) khớp thì **hoàn tất lô từ nhật ký** (`da_ton_tai: true`, cảnh báo `hoan_tat_tu_lan_truoc`) thay vì từ chối `khong_doi` — tool bị ngắt SAU SP, TRƯỚC khi đóng lô, nhân viên vẫn có nút Hoàn tác. SP chưa chạy (HV còn ở trạng thái cũ) → chạy bình thường một lần. UI: hộp xem lại có mục thu gọn "dành cho IT" nêu SP; HV khóa chưa bế giảng vẫn chuyển được kèm ghi chú "không làm HV hiện vào danh sách".

### 11F.6 API (tool, gác session như §11E)

Tiền tố `/local/tnbc2`. Mọi `POST/DELETE` ghi cần `xac_nhan_csdl_that: true` (cổng thao tác chống bấm nhầm, **không phải kiểm soát an ninh** — an ninh = phiên tool + chỉ nghe `127.0.0.1`); cảnh báo cần thêm `da_xem_canh_bao: true`. Trả về luôn kèm **tên trạng thái nghiệp vụ** (`ten_trang_thai`) cùng mã. Số BC2 có dấu `/` → route chi tiết dùng `{ma:path}`, route cố định khai báo trước.

| Nhóm | Endpoint | Ghi chú |
|---|---|---|
| Tốt nghiệp (đọc) | `GET /khoa?loai=oto&cu=` · `GET /tot-nghiep/hv?ma_kh=&q=&trang_thai=` · `POST /tot-nghiep/xem-lai` (chạy thử, không ghi, không cần cổng xác nhận) | §11F.2 |
| Tốt nghiệp (ghi) | `POST /tot-nghiep/ghi` · `POST /tot-nghiep/huy` | chạy nền theo `lo_id` |
| Ứng viên BC2 | `GET /bc2/khoa-san-sang?loai=&cu=&thi_lai_thang=` · `GET /bc2/ung-vien?ma_kh=&ma_bc2=&thi_lai_thang=&lam_tuoi=` · `POST /bc2/khop-danh-sach` | §11F.4 |
| Tạo BC2 | `GET /bc2/goi-y-so?ma_kh=` · `POST /bc2` | đồng bộ |
| Thêm / hoàn tác | `POST /bc2/lap` · `GET /bc2/lo/{lo_id}` (tiến độ CHUNG mọi lô) · `POST /bc2/{ma:path}/hoan-tac` | chạy nền |
| Xem / gỡ / xóa | `GET /bc2/{ma:path}` · `POST /bc2/{ma:path}/go` · `DELETE /bc2/{ma:path}?xac_nhan_csdl_that=true` | `go` chạy nền; xóa đồng bộ |
| Cứu trạng thái | `GET /cuu/tim` · `POST /cuu/chuyen` · `POST /cuu/hoan-tac` | §11F.5 |
| Danh sách | `GET /bc1?loai=` · `GET /bc2?loai=&dong=mo\|dong` · `GET /nhat-ky?loai=&ma_bc2=&gioi_han=` | chỉ đọc |

**Mã lỗi hay gặp** (`detail.ma`): 400 `thieu_xac_nhan_csdl_that`, `lo_id_khong_hop_le`, `khong_co_hoc_vien`, `qua_nhieu_dong`, `dong_qua_dai`, `chi_o_to`, `vuot_do_dai`, `dong_trung_hoc_vien`, `thieu_tu_khoa` · 404 `bc2_khong_ton_tai`, `khoa_khong_ton_tai`, `khong_co_lo`, `khong_co_lan_cuu`, `hv_khong_ton_tai` · 409 `dang_ghi`, `trung_so`, `can_xac_nhan_canh_bao` (kèm `canh_bao[]`), `khoa_chua_co_bc1`, `bc2_khac_khoa`, `bc2_da_dong`, `con_hoc_vien`, `khong_co_dong_hop_le` / `khong_co_hoc_vien_huy_duoc` (kèm `bo_qua[]`), `khoa_chua_be_giang`, `khong_cuu_duoc` (kèm `chan[]`), `da_hoan_tac`, `da_bi_doi`, `lo_id_khong_khop`. `GET /bc2` "HV thực tế" bằng **một** `SELECT MaBC2, COUNT(*) … GROUP BY MaBC2` cho cả danh sách; 437/455 BC2 có Tổng ghi ≠ HV thực tế là **bình thường** (PM cũ không đếm lại, HV thi lại bị chuyển sang BC2 sau) nên chỉ đánh dấu thông tin.

### 11F.7 Luật (Chặn / Cảnh báo)
**Mọi luật ⛔ do `tn_bc2_service` thi hành lúc ghi, trên dữ liệu đọc lại** — không dựa vào việc giao diện ẩn nút. `loai` suy phía máy chủ.

| Mức | Luật |
|---|---|
| ⛔ Chặn | ghi/hủy tốt nghiệp khóa chưa bế giảng hoặc khóa mô tô · **đổi sang số giấy đang thuộc HV khác** / trùng trong lô · sửa/hủy số giấy HV đã `≥11` · HV `03/09` gắn `MaBC2` · HV chưa tới bước tốt nghiệp · cấp số giấy thiếu số sổ hoặc số quyết định · hủy HV đã vào BC2 hoặc không còn `09` · thêm HV sai loại hạng vào BC2 · **thêm/gỡ HV vào BC2 đã đóng** · gỡ HV khác `11` hoặc có `TT_XuLy_Old='11'` · xóa BC2 còn HV (đếm theo `MaBC2`) hoặc đã đóng · tạo BC2 thiếu BC1 / trùng số / BC2 không thuộc khóa · cứu từ `11/16/19` hoặc nguồn ngoài tập · cứu về `09` thiếu số giấy / mô tô · thêm HV đang ở BC2 mở khác (phải gỡ trước) · vượt độ dài cột / giới hạn đầu vào · `lo_id` đã dùng cho thao tác khác |
| ⚠ Cảnh báo (cần `da_xem_canh_bao`) | HV khóa cũ (huy hiệu) · ghi số giấy lần đầu cho HV đã `11–18` (báo cáo không đổi) · thiếu ngày in giấy · BC1 đã có BC2 mô tô · `TT_XuLy_Old` rỗng khi gỡ (về giá trị rỗng) · sau ghi `TT_XuLy_Old='11'` · đọc lại sau SP không khớp / không đọc lại được / không lưu được nhật ký |
| ℹ Thông tin | "Tổng ghi" ≠ "HV thực tế" (bình thường) · số giấy vốn đã trùng từ trước (`trung_co_san`) · HV `11` trong BC2 đã đóng: "mở lại ở PM cũ để xử lý" (2 HV hiện có) · HV `09` để trống số giấy: dùng "Hủy tốt nghiệp" |

**Giới hạn đầu vào:** `khop-danh-sach` và `ds_ma_dk[]` ≤ 5.000 dòng, mỗi dòng ≤ 40 ký tự; `ly_do` bắt buộc ≤ 255; chuỗi số sổ/quyết định/số giấy/số báo cáo/ghi chú theo bảng độ dài §11F.1. Vượt → 400 báo rõ.

### 11F.8 Kiểm thử
- Cursor giả (mẫu `tests/test_phancong_ghi.py`): đúng SP + tham số, **không** câu `INSERT/UPDATE/DELETE` trực tiếp, thứ tự, lỗi giữa chừng, đọc lại trước khi ghi, khóa `tnbc2_ghi`.
- Luật thuần: tập ứng viên theo loại, thứ tự xét 4 nhóm, chuyển trạng thái được phép + hoàn tác miễn luật đích, đánh số ô tô/mô tô, `giai_thich_khong_hien`.
- Cho các mục review: `lo_id` idempotent (gửi hai lần → một lần chạy) · "Làm tiếp" không gọi lại SP với HV đã `11` · BC2 đã đóng giữa chừng → không ghi · xóa BC2 còn HV → chặn · `MaBC2` không tồn tại xử như rỗng · giới hạn đầu vào/độ dài cột · nhật ký không chứa CMT/họ tên.
- **Đã có test (kết nối giả mô phỏng đúng các SP):** `tests/test_tn_bc2_{rules,service,ghi,lap,go,tot_nghiep,ghi_tn,huy_tn,cuu,danh_sach}.py` (~200 test; backend task 96–105, Checkpoint 23/24). Chưa có: ghi thật ở máy CSDT.
- **Chỉ tiêu đo được (nghiệm thu máy CSDT; máy dev 11/10/2026: ứng viên 1,4–1,7 giây lần đầu, BC2 0,07 giây):** danh sách ứng viên một khóa ≤ 2 giây · thêm 100 HV vào BC2 ≤ 5 giây · từ 200 HV có thanh tiến độ.
- Nghiệm thu máy CSDT: login SQL của tool có `EXECUTE` trên 7 SP của §11F.1 và `sp_getapplock`; so sánh trước/sau với PM cũ trên 1 HV + 1 BC2 thử (chụp snapshot cột).

> **Phục vụ:** TNB-01/02/03/04/05/06/07. Quyết định: TDD-decisions §23. Liên quan: §11 (DB Nạp), §11E (mẫu nhật ký + đọc lại trước khi ghi).

---

## 12. Security

| Nhóm | Cơ chế |
|---|---|
| Xác thực | bcrypt password; JWT HS256 expire 8h; đọc `is_active`+vai trò từ DB mỗi request; logout qua blocklist `jti`; API key tool (cân nhắc **key riêng mỗi máy** nếu cần thu hồi độc lập); đăng nhập riêng, không dùng chung (SOD-002); **refresh token cho phiên tool vĩnh viễn (DGT-04, CHANGES #39):** VPS cấp refresh token lúc login (tool lưu **DPAPI**), endpoint `POST /api/auth/refresh` đổi lấy `access_token` mới. **Lưu HASH ở DB** (bảng `refresh_token(user_id, token_hash, created_at, last_used_at, revoked)`), KHÔNG plaintext (bí mật sống vĩnh viễn — lộ DB plaintext = chiếm phiên mọi tài khoản). **Xoay một-lần-dùng:** mỗi refresh trả access_token + refresh token MỚI, vô hiệu cái cũ; **không TTL lịch** (phục vụ "vĩnh viễn") nhưng revoke được. **Chống đá nhầm khi mạng chập chờn** (máy CSDT): cửa sổ ân hạn ngắn cho refresh cũ, HOẶC chỉ coi là replay khi refresh cũ dùng lại SAU khi token mới đã dùng thành công. **Thu hồi:** `logout` xóa refresh token của phiên (ngoài blocklist access `jti`); `doi-mat-khau` thu hồi TOÀN BỘ refresh token của user; `is_active=false` → refresh fail. Chỉ cấp refresh cho đăng nhập **qua tool**; app web giữ phiên thường |
| Dữ liệu (PII) | HTTPS toàn bộ; ảnh thô + CCCD tự xóa 30 ngày; không log nội dung CCCD **(gồm đầu ra OCR THU-06 — họ tên, số CCCD — không ghi ra console client / dịch vụ theo dõi lỗi)**; ảnh thẻ cho OCR chạy **client-side**, không gửi server (§6.7); SQL login riêng (không `sa`); validate ảnh upload (§7.4) |
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
| **Mã nơi cấp '00' đa nghĩa** (CHANGES #40): `NoiCapCMT='00'`=Cục QLHC khi tra `DM_DVHC`, nhưng =Cục CSGT khi tra `DM_DonViGTVT`. Ta hiển thị qua `DM_DVHC` (đúng), nhưng báo cáo/view CDB nào tra qua `DM_DonViGTVT` sẽ ra nhãn SAI | Trung bình | Trung bình | Hỏi người quản CDB: NoiCapCMT chính thức tra theo bảng nào. Nếu CDB dùng `DM_DonViGTVT` → cân nhắc giữ mã tỉnh thay '00', hoặc thống nhất về `DM_DVHC`. Đã verify app CSDT cũ tra `DM_DVHC` ('00'→Cục QLHC) |
| **TNB: khe ghi chồng với PM cũ** (§11F.4, review 11/10/2026 #13): PM cũ không dùng khóa `tnbc2_ghi`, nên giữa lúc tool đọc lại HV và gọi SP vẫn có một khe nhỏ; `usp_NguoiLX_Update_ThemHSBC2` không có điều kiện trạng thái và không được ghi trực tiếp | Thấp | Trung bình | **Chấp nhận** (11/10/2026): tool một máy, ghi ngắn; giảm nhẹ bằng khóa chung + đọc lại sát trước SP + kiểm `TT_XuLy_Old='11'` sau ghi (cảnh báo + nhật ký) |

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
| --- | --- | --- |
| 10/11/2026 | 6.39 | §6.6 mục 9: dòng "Còn thiếu" thay bằng thanh tiến độ ở thanh nút đáy, bấm nhảy ô thiếu (CHANGES #100). |
| 10/11/2026 | 6.38 | §10.2 tra danh mục giấy tờ dò `HangDT` → bỏ dấu chấm → `HangGPLX`, rỗng thì chặn nạp (BUG-20); §10.6/§10.7 GPLX đã có ghi chuỗi rỗng, không NULL, `NoiCapGPLXDaCo` rỗng theo số bằng; Nơi cấp điền sẵn theo 2 số đầu số GPLX (CHANGES #98). |
| 04/11/2026 | 6.37 | §6.6 "Lưu & nhập hồ sơ tiếp": thêm phím tắt Enter trên desktop (CHANGES #97). |
| 04/11/2026 | 6.36 | §6.6 dòng "Lưu & nhập hồ sơ tiếp": mobile cũng về thẳng form trống (CHANGES #96). |
| 04/11/2026 | 6.35 | **+§6.9 Chế độ sáng/tối ở app web** (CHANGES #94, `HTG-08`): biến CSS + lớp `dark`, lưu lựa chọn ở máy, script chống nháy, nút đổi chế độ. |
| 04/11/2026 | 6.34 | **+§10.8 Báo hồ sơ chưa nạp vừa được app web cập nhật** (CHANGES #92, `NAP-08`): so khi kéo, `keo_ve_thay_doi` + `keo_ve.anh_luc` ở SQLite tool, `KeoOut.anh_luc` ở VPS (không thêm cột), 3 endpoint tool, cảnh báo đậm khi nháp giữ ảnh cũ. |
| 03/11/2026 | 6.33 | Sửa sau review §10.7 (CHANGES #90, biên bản `tdd-review-03-11-2026.md`): nhận diện bổ sung bằng `audit_log`, phân trang, danh sách rỗng 422, UPDATE nguyên tử, chuỗi thô, cỡ lô 500, dọn dấu vân, sơ đồ vòng đời. |
| 03/11/2026 | 6.32 | **+§10.7 Bổ sung GPLX sau khi đã nạp** (CHANGES #89, `QLY-10`, `TCB-05`, `THU-07`): UPDATE đúng 6 cột theo `MaDK`, 2 endpoint VPS không thêm cột, SQLite `gplx_da_xu_ly`, chặn BC1/DKKH; §4.3, §4.4, §6 ghi chú. |
| 02/11/2026 | 6.31 | §11D.10 nhận hai mẫu PDF DAT (CHANGES #88). |
| 02/11/2026 | 6.30 | §10.6 Cục QLHC mã `00` + script bật ở DB Nạp (CHANGES #84). |
| 02/11/2026 | 6.29 | **§10.6 khớp form cũ** (CHANGES #83): Nơi cấp đổi sang `DM_DonViGTVT`; chặn trùng hạng, bắt buộc ngày, thứ tự ngày, 18 tuổi; ghi bằng chứng cách lưu `\|`. |
| 02/11/2026 | 6.28 | **Sửa sau `/reviewtdd` §10.6** (CHANGES #82, biên bản `tdd-review-02-11-2026-gplx-da-co.md`): `hang` lưu mã; thứ tự ưu tiên + cờ "App web có bản mới"; `/cua-toi` trả kèm; lỗi từng dòng khi nạp lô; VPS kiểm + tự ALTER; PII xóa mềm; `ds_noi_cap_gplx`. |
| 02/11/2026 | 6.27 | **+§10.6 GPLX đã có** (CHANGES #81, `NAP-07`, `THU-07`): JSONB `ho_so_thu_thap.gplx_da_co`, cột nháp SQLite, ghi 6 tham số SP nối `|`, bảng nhãn ↔ mã hạng; §3, §4.4 ghi chú; ô gõ tìm Hạng + Nơi cấp (có Cục QLHC, tỉnh trước sáp nhập), ô ngày tự chèn `/`. Không đổi schema DB Nạp, không sửa Sync. |
| 16/10/2026 | 6.26 | **Sửa sau `/reviewtdd` "Chọn in GPLX"** (CHANGES #80, biên bản `tdd-review-16-10-2026-in-gplx.md`): §9.3a +cột `chon_in_gplx` · §10 Phục vụ +`NAP-01` · §10.2 làm rõ server dùng đúng giá trị client gửi (chỉ kiểm tập) · quy tắc ghi nháp (chọn lại mặc định → NULL; đổi khóa khác loại → xóa lựa chọn tay) · dòng `MaLoaiHs` "bắt đầu bằng A". |
| 16/10/2026 | 6.25 | **"Chọn in GPLX" theo hạng khóa** (CHANGES #79): §10.1/§10.2 `CHON_IN_GPLX` hết gán cứng 2 — ô chọn 1/2/3, mặc định A*→3 / còn lại→2, 422 ngoài tập, nháp `nhap_chuan_bi.chon_in_gplx` (+ALTER), UI ngăn Chuẩn bị; Sync CDB chép nguyên giá trị (NULL→0). |
| 16/10/2026 | 6.24 | **Quản lý mẫu giải trình** (CHANGES #78): §11D.13 ghi UI hộp sửa/xóa/thêm mẫu dùng lại `PUT mau-giai-trinh` (thay toàn bộ + `phien_ban`), không thêm endpoint. |
| 16/10/2026 | 6.23 | **Sửa sau /reviewtdd §11D.13** (KQD-04 đổi, CHANGES #77, biên bản `tdd-review-16-10-2026-kqd04.md`; subagent soát độc lập: 3 Chặn · 11 Nên sửa · 6 Ghi nhận, user chọn sửa tất cả): **lô một giao dịch thật** (`autocommit=False`) + `cap_nhat` bước chuyển lỗi → 200 `chua_chuyen_90`; **lô kiểm đủ điểm** theo `hv_chua_du` §11D.9; **giải trình riêng được giữ** (chung không đè, `ghi_de_rieng`); **HV 90 Không đạt/trống kết luận** có chip đỏ + tab "Cần xử lý"; chặn đua trạng thái + `MaCSDT`; biên lô; mẫu theo `target_key` + `phien_ban` + khóa ghi cấu hình; mất kết nối `khong_ro`; sơ đồ §11D.1 + trình tự lô. |
| 16/10/2026 | 6.22 | **+§11D.13 Sửa lại HV Sở từ chối → "Đang giải trình" + giải trình hàng loạt** (KQD-04 đổi, CHANGES #77, decisions §27): quy tắc `14`→`90` khi Đạt + có giải trình (tool UPDATE có guard SQL, vì SP không đặt `90` và SP danh sách kết xuất của CDB chỉ lấy `09`/`90`); `POST /giai-trinh-lo` một giao dịch; mẫu giải trình phía tool; lưới đọc thêm `LyDoTuChoiKQDT`; nhóm "còn sót kết xuất" + KQD-07 gồm `90` Đạt; bảng nhãn trạng thái nghiệp vụ. Sửa §11D.1 (sơ đồ) + §11D.6 (API) + §11D.9. |
| 12/10/2026 | 6.21 | **Sửa sau /reviewtdd §11D.12** (KQD-10, CHANGES #76, biên bản `tdd-review-12-10-2026-kqd10.md`; subagent soát độc lập: 0 Chặn · 5 Nên sửa · 6 Ghi nhận): **xếp tên theo thanh điệu từng âm tiết (sửa code — Hòa/Hoà, Thúy/Thuý)** · viền xám, chân trang cỡ 10, hàng 5/9 = 15,75 đúng mẫu · footer 0,3 · độ rộng cột theo ký tự hoa/thường · chiều cao khối cơ sở tự tăng · `so_hv_trong_ket_qua` + dòng giải thích · §11D.6 `GET`→`POST xuat-excel` · số dòng/trang là ước lượng. |
| 12/10/2026 | 6.20 | **+§11D.12 Xuất Sổ theo dõi kết quả học tập — mẫu Phụ lục VI (KQD-10)** (CHANGES #75): endpoint `POST /xuat-so-theo-doi`, hàm thuần `ketqua_so.py`, định dạng bám file mẫu (A4 dọc, lặp 2 hàng tiêu đề, `Trang x/y`), xếp tên tiếng Việt, kết quả chỉ khi đủ 5 điểm, không bìa/chữ ký; KQD-09 `Ngày lập` chỉ `dd/mm/yyyy`; TDD-decisions §26. |
| 12/10/2026 | 6.19 | **§11D.11: lưu vào thư mục `output` + bỏ dấu chấm thừa giờ/km** (KQD-09, CHANGES #74): `GET /xuat-excel` → `POST` ghi file vào `paths.output_dir()` (không ghi đè, `_2`…), trả đường dẫn; thêm `POST /mo-thu-muc-xuat`; định dạng ô giờ/km sân số nguyên `0`. |
| 12/10/2026 | 6.18 | **Sửa sau /reviewtdd §11D.11** (KQD-09, CHANGES #73, biên bản `tdd-review-12-10-2026-kqd09.md`; subagent soát độc lập: 2 Chặn · 6 Nên sửa · 5 Ghi nhận): chốt lỗi 404/500 + Expose-Headers + tên file dự phòng · ghi chú `Thiếu`/`Chưa có điểm` · nhãn "Chưa có kết luận" · hệ quả §25 (Hoàn thành cạnh điểm trống) · hạng hòa phiếu theo chữ cái · **chống formula injection + làm sạch ký tự điều khiển (sửa code)** · `PUT /co-so` gác phiên (sửa code) · sơ đồ luồng + bảng cột→nguồn · số đo hiệu năng. |
| 12/10/2026 | 6.17 | **+§11D.11 Xuất Excel kết quả học tập theo khóa (KQD-09)** (CHANGES #72): endpoint `GET /xuat-excel` chỉ đọc, hàm thuần `ketqua_xuat.py` (openpyxl), form 1 sheet 22 cột + khối đầu, cấu hình tên cơ quan/cơ sở, thêm vào §11D.6; TDD-decisions §25. |
| 12/10/2026 | 6.16 | **Sửa sau /reviewtdd §11D.10** (KQD-08/KQD-02, CHANGES #71, biên bản `tdd-review-12-10-2026-kqd08.md`; subagent soát độc lập, 0 Chặn · 4 Nên sửa · 3 Ghi nhận): chốt endpoint `/dat/*` theo code (đủ field, 6 giá trị `tinh_trang`, 400/413/422) + thêm vào §11D.6 · chèn sơ đồ luồng + bảng tình trạng · "Chọn tất cả" chỉ tick `khop` (sửa code) · định nghĩa chưa chạy DAT khớp code · trần tra lý do 500 mã/50 tên + câu hiển thị dòng vượt trần (sửa code) · ghi nhận 3 rủi ro (rowcount, ghi sau thắng, PDF không giới hạn trang). |
| 12/10/2026 | 6.15 | **§11D.10 chốt sau /kiemthu** (CHANGES #70): `UPDATE` thêm `TrangThai = 1` (cùng điều kiện xem trước); regex mã khóa chữ+số; tick tay dòng chưa chạy DAT điền sẵn `0`; giờ nhận `hh:mm:ss`; vector giờ/km dùng chung pytest + vitest. |
| 12/10/2026 | 6.14 | **+§11D.10 Nạp giờ/km đường từ PDF DAT (KQD-08) + giờ `hh:mm` & nạp sẵn giờ/km đã lưu ở lưới (KQD-02)** (CHANGES #69): hàm thuần đọc PDF (`ketqua_dat.py`), 2 endpoint xem-trước/lưu (UPDATE thẳng 2 cột, một transaction, không qua SP), `/hoc-vien` trả thêm `gio_duong`/`km_duong`, sửa lỗi ngầm SP ghi NULL đè giờ cũ. Thêm phụ thuộc `pdfplumber`. 2 điểm còn mở ghi tại §11D.10. TDD-decisions §24. |
| 12/10/2026 | 6.13 | **Đồng bộ §11D.9 (KQD-07) và §11E.10 (PCG-06) với code + quyết định đã chốt** (CHANGES #68): `hv_chua_du(hv)` bỏ tham số `hang`, mô tô lọc ở router và đếm `mo_to_bo_qua`; môn bắt buộc = 5 môn mọi hạng ô tô; response thêm `mon_thieu`/`mo_to_bo_qua`/`ma_kh`, `cccd`→`so_cccd`; UI chốt qua mock (ẩn chip giờ/km khi chưa có điểm, thông điệp khóa mô tô). PCG-06 đọc ở `phancong_hangiayto.py`, lọc `TrangThai=1`. Không đổi schema. |
| 12/10/2026 | 6.12 | **Sửa §11.6 đổi nền cả khóa (QLY-07, CHANGES #67):** ghi đè đúng file ở `DuongDanAnh` hiện có (2 DB dùng chung 1 file), không dùng `ghi_anh_update` (không tạo file mới/không đổi `DuongDanAnh`); chỉ UPDATE `ChatLuongAnh/NgayThuNhanAnh/NguoiThuNhanAnh`; sao lưu `<tên>_BACKUP.jp2` cùng thư mục thay `<khóa>\_BACKUP\<MaDK>.jp2`. |
| 12/10/2026 | 6.11 | **+§11D.9 Kiểm trước kết xuất (KQD-07) và +§11E.10 Hạn giấy tờ + GV/xe ngưng còn phân công (PCG-06)** (CHANGES #65, #66): hai endpoint chỉ đọc `GET /local/ketqua/kiem-truoc` và `GET /local/phancong/han-giay-to`; luật thuần `hv_chua_du` / `phan_loai_han`; cột đã verify trực tiếp trên DB đích 12/10/2026 (kể cả `GiaoVien.NgayHHGPLX`). Không đổi schema, không ghi DB. |
| 11/10/2026 | 6.10 | **Ghi lại hành vi thực tế khi dựng UI TNB task 106-115 + 2 sửa backend** (CHANGES #64, không đổi yêu cầu): §11F.3 tích lẫn/Chọn tất cả/nút Hủy · §11F.4 `bc1.ngay_bao_cao`, form bắt buộc ngày, `thu_lai` · §11F.5 chốt payload bước ③, lỗi sau khi gửi → Làm tiếp, lô that_bai/loi_giua_chung, tự làm tươi, hạn chế F5 · §11F.6 `cuu_chuyen` hoàn tất lô dở từ nhật ký + mục IT. |
| 11/10/2026 | 6.9 | **Ghi lại hành vi thực tế của backend TNB task 96–105** (CHANGES #63, không đổi yêu cầu): §11F.0 +nhật ký/lô sqlite, +chạy nền & `GET /bc2/lo/{lo_id}` dùng chung · §11F.1 +hành vi thật của 4 SP, +collation `Ð`/`Đ` · §11F.2 +API tốt nghiệp, luật A/B/C, bộ sổ chung, dãy `N1\|<n>`, hủy giữ ngày in · §11F.4 +nguồn nhóm Không đưa được, `kiem_dau_vao`, `POST /bc2` (`thu_lai`), gỡ tay (Old='11' chặn), xóa BC2 (không xóa BC2 đã đóng), `{ma:path}` · §11F.5 hoàn tác cứu bằng nhật ký tool, API cứu · §11F.6 bảng API + mã lỗi · §11F.7 luật mới. |
| 11/10/2026 | 6.8 | **Sửa sau /reviewtdd §11F** (biên bản `tdd-review-11-10-2026-tnb.md`): §11F.0 +khóa ghi chung `tnbc2_ghi`, nhật ký không lưu CMT/họ tên · §11F.1 +độ dài cột, +hành vi thật của SP (`ThemHS_BC2` không trả cột trạng thái/lọc khóa bằng LIKE, `ThemHSBC2` không điều kiện, `BaoCaoII_Delete` không kiểm HV) · §11F.2 sơ đồ vòng đời đủ ô tô+mô tô+thi lại+cứu, +`xem-lai`, kiểm trùng loại trừ chính HV · §11F.3 BC1 suy từ khóa, `TongSoThiSinh` tính trước Insert · §11F.4 **bỏ "chuyển HV từ BC2 mở khác"**, `thi_lai` bất kể khóa, SP gọi một lần `@MaKH=''`, `lo_id` idempotent + chạy nền + `GET /bc2/lo/{lo_id}`, thứ tự ghi, hoàn tác theo BC2, +sơ đồ nhóm + sơ đồ luồng ghi · §11F.5 hoàn tác cứu miễn luật đích · §11F.6 xóa BC2 đếm theo `MaBC2` · §11F.7 ⛔ thi hành ở máy chủ, +BC2 đã đóng, +giới hạn đầu vào · §11F.8 +test, +chỉ tiêu đo được · §16.1 +khe ghi chồng PM cũ. |
| 11/10/2026 | 6.7 | **Sửa §11F theo phản hồi mockup v1** (CHANGES #61): §11F.4 viết lại — luồng 3 bước, 4 nhóm HV (`san_sang`/`thi_lai`/`can_xem`/`khong_duoc`) + ngưỡng `thi_lai_thang`, `lo_id` + hoàn tác, dán danh sách; §11F.6 +`khoa-san-sang`, `khop-danh-sach`, `lap`, `hoan-tac`; tên trạng thái nghiệp vụ trong API. |
| 11/10/2026 | 6.6 | **+§11F Tốt nghiệp & Báo cáo 2** (CHANGES #60, TNB-01..07): phân hệ #5 tool, **DB Nạp `GPLX_CSDT`**, chỉ gọi SP có sẵn (`Update_CNTN`, `BaoCaoII_Insert`, `ThemHS_BC2` + lọc lại, `Update_ThemHSBC2`, `Update_DanhSachHocSinhBC2`, `UpdateTTXLy`); luật ô tô/mô tô riêng, `TrangThai` BC2 0/1, đánh số theo loại, đọc lại trước khi ghi, cứu trạng thái nguồn/đích hẹp. |
| 11/10/2026 | 6.5 | **Sửa sau /reviewtdd §11E** (biên bản `tdd-review-11-10-2026-pcg.md`, CHANGES #59): §11E.0 +bản nháp ở UI + sơ đồ vòng đời · §11E.1 +sơ đồ hai tầng cờ · §11E.2 +`GET /mon`, +`dau_van_tay` · §11E.3 khớp #56/#58 · §11E.4 hàng loạt ở UI · §11E.5 ghép xe min–max + thuật ngữ · §11E.6 **+`dau_van_tay` → 409 `khoa_da_doi`, +khóa ghi → 409 `dang_ghi`**, diff rỗng → 200, định nghĩa "giữ nguyên", không rollback + sơ đồ luồng ghi · §11E.7 +thuật ngữ GV loại TH/AL ≠ GV dạy thực hành, +`mon_khong_ton_tai`, +giới hạn đầu vào, +ghi chú `xac_nhan_csdl_that` không phải an ninh · §11E.8 +công thức kết luận · §11E.9 +test. |
| 10/10/2026 | 6.4 | **+§11E Phân công giáo viên – xe cho khóa** (CHANGES #54, PCG-01..05): phân hệ #4 tool; router `phancong.py` + `phancong_rules.py` (luật thuần: datetime nửa mở, phạm vi khóa, 1 GV–1 xe, hạn giấy phép) + `phancong_service.py`; 9 endpoint (`/kiem-tra` không ghi, `/goi-y-ghep-xe`, `/ghi` kiểm lại + thứ tự xóa→thêm→sửa + trả đã/chưa ghi); dùng SP `usp_KhoaHoc_GiaoVien_Insert`, `usp_LichLV_KhoaHoc_GiaoVien_Insert/_Update`, `usp_KhoaHoc_XeTap_Insert`, `LichSD_KhoaHoc_XeTap_Insert`, `usp_LichSD_KhoaHoc_XeTap_Update`, xóa theo `MaLichLV/MaLichSD`; **KHÔNG** dùng SP xóa lan; lưu môn `TenMonHoc="1,8"`, `MaMonHoc` NULL; nhật ký sqlite `phancong_nhat_ky`. Không bảng CDB mới. decisions §22. Cần /reviewtdd (API + nghiệp vụ mới). |
| 10/10/2026 | 6.3 | **KQD-05 mở rộng "Sửa sau gửi" chọn từng HV** (CHANGES #53): §11D.7b mới — điều kiện bật (hết gói chưa gửi), `POST /mo-sua-sau-gui` (lùi đúng HV được chọn, không xóa gói, nhật ký sqlite `sua_sau_gui` ghi trước) + `GET /sua-sau-gui` (khối đỏ KQD-03); §11D.6 +2 endpoint; decisions §21 (đổi quyết định M1 khóa cứng §19). Verify DB 10/10: SP tiếp nhận phản hồi Sở chỉ nhận `TT_XuLy='12'`. Cần /reviewtdd (API + bảng sqlite mới). |
| 08/10/2026 | 6.2 | **Loạt UX form xác nhận desktop** (CHANGES #52, THU-01/THU-02): §6.8 mới — 10 cải tiến nhập liệu thuần client `Quet.tsx` (nới khung 3xl; sắp lại ô CCCD+ngày cấp cùng hàng; chặn/đếm 12 số; in hoa tên; nút gạt Nam/Nữ; **gợi ý Nơi thường trú từ file tĩnh `data/dvhc-2025.json` 34 tỉnh+3.321 xã 2 cấp 2025, nạp lười, khớp không dấu, không ép chọn**; phím mũi tên nhảy ô; icon nhãn; trạng thái ✓/đỏ + dòng "còn thiếu"; tự suy giới tính/năm sinh từ CCCD `suyTuCccd`). KHÔNG đổi endpoint/schema/payload — ràng buộc lưu trữ vẫn ở `kiemFields`. Khác §3.3 (SQLite `DM_DVHC` của tool sinh mã). Code+build+34 test pass, commit `5087ceb`. |
| 08/10/2026 | 6.1 | **Sửa sau /reviewtdd #51** (biên bản `tdd-review-08-10-2026.md`): §4+§7.2 — **GỠ endpoint `DELETE /local/keo-ve/:uuid`**, gộp mọi "Bỏ khỏi hàng đợi" (1 dòng lẫn nhiều dòng, mọi trạng thái) về **1 đường `POST /local/nap/bo-qua`** (tránh đường xóa-không-tombstone; UI phải chuyển DELETE→POST). §9.3b — thêm **pseudo-logic endpoint** (tra `keo_ve_trang_thai` từng uuid → tombstone cho `cho`/`loi`/`None`, KHÔNG cho `xong`) + **lý do QLY-08** (ghi tombstone cho `xong` sẽ chặn vĩnh viễn đường "Gỡ về chờ nạp") + lô rỗng no-op + trần ≤1000 uuid + tham số hóa `uuid` + ghi nhận tombstone không tự dọn. |
| 08/10/2026 | 6.0 | **Bỏ dòng CHỜ/LỖI khỏi hàng đợi + nhớ "bỏ qua"** (CHANGES #51, NAP-01): §7.2 mở rộng "Bỏ khỏi hàng đợi" cho dòng `cho`/`loi` (trước guard `409` chỉ `xong`); §9.3b mới — bảng tombstone `keo_ve_bo_qua(uuid PK, ly_do, created_at)` trong `staging.sqlite`, `keo_ve_upsert` lọc bỏ uuid đã bỏ qua trước khi upsert → kéo lại không mang về; §4 +endpoint `POST /local/nap/bo-qua` (bỏ nhiều một lượt, tombstone + `keo_ve_xoa` + `nhap_xoa`, idempotent); vòng đời nháp §9.3a +nhánh bỏ-qua. Chỉ đụng `staging.sqlite`, KHÔNG đụng VPS/DB đích. Dọn ca "hồ sơ đã xóa app web nhưng tool kéo về từ trước còn sót" mà đồng bộ-xóa theo mốc (§11.7) bỏ lọt. Cần /reviewtdd (API + Data Model mới). |
| 07/10/2026 | 5.4 | **+KQD-06 Sửa lẻ / xóa điểm đã lưu** (CHANGES #48): §11D.8 mới — chỉ HV `TT_XuLy` 09/10; **sửa lẻ** gom 5 quy-đổi (môn sửa từ gốc + môn giữ lấy `DiemKQ*` đã lưu, không tính ngược gốc) → `_CapNhat`; **xóa điểm** `POST /xoa-diem` UPDATE trực tiếp NULL 5 điểm+3 cờ+`SoGiayCNTN` + `TT_XuLy='03'` (SP không reset được — verify DB 07/10); §11D.6 +endpoint `xoa-diem`. Cần /reviewtdd (API + nghiệp vụ mới). |
| 07/10/2026 | 5.9 | **THU-06 OCR bỏ ngày cấp** (`/capnhat` CHANGES #50, phát hiện khi build task 79): §6.7 dòng "Trường OCR đọc" đổi 6→**5 trường mặt trước** (CCCD, họ tên, ngày sinh, giới tính, nơi thường trú); **ngày cấp in ở mặt sau → không đọc** (THU-06 chỉ chụp mặt trước), để trống + đánh dấu, nhân viên nhập tay (user chốt A). Khớp PRD + code task 79. |
| 07/10/2026 | 5.8 | **Chốt engine OCR THU-06** (`/tdd`, §6.7 + decisions §20): **engine = Tesseract.js** (WASM client-side, offline, dữ liệu `vie` — giữ ảnh trên máy đúng rào PII); **tách 6 trường = OCR toàn ảnh + regex theo nhãn in trên thẻ** (bền với ảnh chụp tay nghiêng/cắt lệch). Dịch vụ eKYC ngoài bị loại (lộ PII căn cước, chỉ mở khi có phê duyệt pháp lý). Mở kiểm: độ chính xác tiếng Việt có dấu của Tesseract.js trên thẻ thật cần thử nghiệm → quá thấp thì tăng sửa tay hoặc xin duyệt eKYC (/capnhat). §6.7 còn là chi tiết implement, hết mục "chưa chốt". |
| 07/10/2026 | 5.7 | **Sửa sau /reviewtdd §6.7** (THU-06 OCR, khung nghiệp vụ): +dòng `Phục vụ: THU-06`; **quy tắc fail** (mốc = CCCD 12 số hợp lệ: không có → fail không điền gì, có → điền phần đọc được + đánh dấu); màn xác nhận **không auto-submit**; làm rõ tách trường từ OCR là bước mới, `lib/qr.ts` chỉ chuẩn hóa hạ nguồn; phạm vi **CCCD 12 số gắn chip**; **siết PII: OCR client-side = rào cứng** (dịch vụ ngoài cần phê duyệt pháp lý), **downscale ≤~1600px trước OCR** (chống treo máy), **vòng đời ảnh thẻ** (hủy khỏi client nếu không cắt chân dung); NFR <2s không áp bước OCR + spinner/hủy; +sơ đồ luồng OCR ASCII; §12 +không log đầu ra OCR. 0 Chặn · 7 Nên sửa · 5 Ghi nhận, 0 tồn. Biên bản: docs/tdd-review-07-10-2026-thu06.md. *(+TDD-decisions §20 sửa khớp quyết định BUG-14 A.)* |
| 07/10/2026 | 5.6 | **Sửa sau /reviewtdd §11D.8** (KQD-06, hẹp — khớp tài liệu↔code): §11D.8 **tách chặn backend theo thao tác** (dùng chung endpoint): *Xóa điểm* `/xoa-diem` chặn cứng ngoài 09/10; *Sửa lẻ* dùng chung `/cap-nhat` với KQD-02 (nhập lần đầu `03`) + KQD-04 (giải trình `14/90`) nên endpoint chỉ chặn `12/13`, phạm vi 09/10 do UI kiểm (user chốt A — sửa TDD cho khớp code, không đụng guard đang chạy); *Xóa điểm* đổi sang **kiểm `TT_XuLy` bằng SELECT trước** (ngoài 09/10 → 409, không tìm thấy → 404) thay vì dựa `rowcount` pymssql (có thể trả -1 → báo nhầm thất bại), `IN ('09','10')` trong UPDATE giữ làm lưới chống đua — sửa `tool/app/routers/ketqua.py:xoa_diem`. `MaDK` lọc không kèm `MaCSDT`: xác nhận KHÔNG lỗi (`MaDK` là PK toàn CDB, nhúng sẵn `MaCSDT`). 1 điểm chốt A · 1 phi-lỗi · 1 sửa code, 0 tồn. |
| 07/10/2026 | 5.5 | **+THU-06 OCR đọc chữ trên thẻ (khung nghiệp vụ)** (CHANGES #49): §6.7 mới — lối nhập thứ 3 "Chụp ảnh thẻ → tự đọc chữ", mọi thiết bị, điền sẵn 6 trường → nhân viên xác nhận; +decisions §20 (lật "không OCR" của THU-01). **Engine OCR + nơi chạy + PII CHƯA chốt — để /tdd**. Nguồn: iPhone quét QR yếu hơn Android (BUG-14). Cần /reviewtdd + /tdd (chốt công nghệ). |
| 07/10/2026 | 5.3 | **Đồng bộ tài liệu sau code KQD-05/03** (CHANGES #46, tài liệu lag code — không đổi yêu cầu): §11D.6 +`GET /local/ketqua/mo-khoa` (cổng B-1 chỉ đọc: `mo_duoc`/`goi_chua_gui`/`goi_da_gui`/`so_hv_mo`/`so_hv_bo_qua`/`so_khoa`) + ghi rõ **KQD-03 KHÔNG dùng endpoint `ket-xuat` riêng** (ghép từ `/khoa` đếm `ketxuat`=12 + `GET /mo-khoa` panel gói + `/hoc-vien?trang_thai=ketxuat`); §11D.7 **đảo thứ tự bước: LÙI HV (bước 2) TRƯỚC, XÓA gói (bước 3) SAU** cho khớp code + khớp edge PRD ("xóa gói xong lỗi → HV đã lùi vẫn sửa được"), + ghi `GiaiTrinh` gộp vào `UPDATE` lùi. |
| 07/10/2026 | 5.2 | **Sửa sau /reviewtdd KQD-05** (phạm vi hẹp, mục #45): §11D.7 `POST /local/ketqua/mo-khoa` đổi từ "lùi HV `12` của **khóa**" → **mức CƠ SỞ** (lùi mọi HV `12` của CSĐT, mọi khóa) — **Chặn** (xóa gói buộc quét cả CSĐT, lùi theo khóa để treo HV khóa khác "12 không gói"), user chốt phương án A; `UPDATE` thêm guard **`KetLuanCSDT IS NOT NULL`** (HV `12` mà kết luận NULL → bỏ qua + cảnh báo, không ép '10' oan — Nên-sửa); §11D.1 +ghi chú/nhánh **ngoại lệ `12 → 09/10`** trong sơ đồ máy trạng thái. 1 Chặn (đã sửa) · 1 Nên-sửa · 1 Nên-sửa (sơ đồ), 0 tồn. Biên bản: docs/tdd-review-07-10-2026-kqd05.md. |
| 07/10/2026 | 5.1 | **Sửa sau /reviewtdd #44** (phạm vi app web chụp bù ảnh HV đã nạp): §4.3 ghi rõ luật trạng thái ở dòng endpoint `POST .../anh` (F1); §6.3 đổi sang **allowlist `{pending,imported}`** + chặn cả `deleted`, cảnh báo không viết blocklist `==importing` (**Chặn** F2); §7.5 +ngoại lệ "khe hẹp cho ảnh" phá tuyên bố đóng-băng-tuyệt-đối (F3); §9.3 job PII tính tuổi theo `updated_at` + `upload_anh` set `updated_at=now` cho `imported` để gia hạn ảnh chụp-bù (F4); §11.5(b) +ghi nhận đua ảnh (kéo lại lấy bản mới, F5) + **sơ đồ luồng 3 hệ thống**. 1 Chặn · 3 Nên-sửa · 2 Ghi-nhận, 0 tồn. Biên bản: docs/tdd-review-07-10-2026.md (mục #44). |
| 07/10/2026 | 5.0 | **Mở khóa để sửa điểm sau kết xuất + dựng lại tab Theo dõi kết xuất** (CHANGES #45, KQD-05/KQD-03): §11D.7 mới — luồng mở khóa `12` có kiểm soát (cổng B-1 `EXISTS ... NoiGui=@MaCSDT AND TrangThai='0'`; `POST /local/ketqua/mo-khoa` xóa gói chưa gửi qua `usp_TRANS_CLI_HangDoiGui_Delete` + lùi mọi HV 12 của khóa về 09/10; gói đã gửi hết → 409 + thông báo mức đợt M1); §11D.0 +ngoại lệ duy nhất cho `12`; §11D.6 +endpoint `mo-khoa` + `ket-xuat` trả tiến độ/gói/lưới; +decisions §19 (B-1/B-1a/M1, lý do DB không nối HV↔gói). KQD-03 viết lại khóa-first master–detail. KQD-02/04 giữ ⚠️ (yêu cầu lõi không đổi). |
| 07/10/2026 | 4.9 | **App web chụp bù ảnh kể cả HV đã nạp — Phương án B** (CHANGES #44, lật quyết định A 01/10): §6.2/§6.3 app web cho chụp bù HV thiếu ảnh cả `pending` lẫn `imported`; §4.3 **nới chặn `POST /api/ho-so/:uuid/anh`** (cho `pending`+`imported`, vẫn chặn `importing`, giữ `created_by`); §11.5(b) ảnh thô VPS nay gồm bản collector chụp-bù, operator tự lọc "Chưa ảnh"→kéo (chốt A, không cờ ảnh-mới); +decisions §18 (lật A→B). THU-02 hạ ✅→⏳. |
| 07/10/2026 | 4.8 | **Sửa sau /reviewtdd §9.3a** (hẹp, phạm vi #43): ô Ngày cấp đổi `<input type="date">`→component **`ODate`** dd/mm/yyyy (`ymdToVN`/`vnToYmd`, `max`=hôm nay) đồng nhất TraCuuDB/TraCuuCDB + giữ chuẩn ngày VN (Nên sửa 2.1); chốt **ô rỗng → quay về ngày gốc** (`nhap.ngayCap \|\| keo_ve.ngay_cap`, một quy tắc cho cả hiển thị lẫn nạp — Nên sửa 2.2); +đoạn **Migrate cột `ngay_cap`** bắt buộc (guard `PRAGMA table_info`+`ALTER TABLE ADD COLUMN`, vì DDL là `IF NOT EXISTS` không tự thêm cột → tránh nạp vỡ trên máy đã có bảng — **Chặn** 3.1). 1 Chặn · 2 Nên-sửa · 3 Ghi-nhận, 0 tồn. Biên bản: docs/tdd-review-07-10-2026.md (mục #43). |
| 07/10/2026 | 4.7 | **Ngày cấp CCCD + Nơi cấp điền sẵn ở drawer Nạp lô** (CHANGES #43, NAP-01): §9.3a — `nhap_chuan_bi` +cột `ngay_cap`; `nhap[uuid]` +`ngayCap`; ô Ngày cấp (`<input type="date">`) điền sẵn `keo_ve.ngay_cap` + sửa được + lưu nháp (GIỮ khi reset địa chỉ BUG-04); payload nạp ưu tiên `nhap.ngayCap`→gốc (`NgayCapCMT`), NAP-05 không đổi Done. +Bền hóa combo Nơi cấp: tự chèn option `00 — Cục QLHC` khi suy ra '00' mà danh mục nguồn thiếu (máy chưa chạy script đồng bộ `DM_DVHC` #40). |
| 07/10/2026 | 4.6 | **Sửa sau /reviewtdd §11D** (module KQD, verify DB `GPLX_CDB_CSDT`): §11D.0 SP ghi **18 tham số** (không phải 19) + SP đọc ưu tiên `_CNKQDT` (đủ cột lưới) + ⚠️ SP **không bảo vệ `TT_XuLy='12'`** → app chặn gọi SP cho 12/13 + KQD-04 ghi `GiaiTrinh` bằng `UPDATE` tham số hóa riêng chạy TRƯỚC `_CapNhat` (validate ≤1000; `LyDoTuChoiKQDT` read SP không trả, SELECT riêng nếu cần); §11D.1 +sơ đồ ASCII máy trạng thái (ranh giới tool/ngoài-tool); §11D.2 xét Đạt trên điểm **thô chưa làm tròn**; §11D.3 hạng `MaHangMoi` rỗng → không khóa-cứng giờ/km; §11D.6 combobox debounce+giới hạn gợi ý. 0 Chặn tồn · 5 Nên-sửa · 3 Ghi nhận. Biên bản: docs/tdd-review-07-10-2026.md. |
| 06/10/2026 | 4.5 | **Sửa sau /reviewtdd §11B.7** (hẹp, phạm vi #40): +edge "xã cũ trước sáp nhập" áp CẢ QLY-01 lẫn TCB-03 (combo Xã trống = giữ mã cũ); +Risks §16.1 **rủi ro mã '00' đa nghĩa** (DM_DVHC=Cục QLHC vs DM_DonViGTVT=Cục CSGT → hỏi người quản CDB tra bảng nào). 0 Chặn · 1 Nên-xác-nhận · 1 Ghi nhận. Biên bản: docs/tdd-review-06-10-2026.md. |
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
