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
│   ├── webui/         React (build → static nhúng)
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
POST /api/admin/users           (admin) tạo tài khoản
PUT  /api/admin/users/:id       (admin) sửa vai trò/khóa
```

### 4.3 Hồ sơ thu thập (app web — collector)
```
POST /api/ho-so                 Gửi hồ sơ mới (uuid client-gen, idempotent)
GET  /api/ho-so/cua-toi         DS mình đã gửi
PUT  /api/ho-so/:uuid           Sửa (khi pending)
POST /api/ho-so/:uuid/anh       Upload ảnh thô (multipart)
```

### 4.4 Nạp (tool — operator, kèm X-Tool-Key)
```
GET  /api/nap/keo?limit=200     Kéo DS pending (không lấy imported/deleted); limit mặc định 200, có cursor
POST /api/nap/:uuid/lock        Khóa bản ghi (→ importing) trước khi nạp
POST /api/nap/:uuid/da-nap      Đánh dấu da_nap (kèm ma_dk) + mở khóa
POST /api/nap/:uuid/unlock      Mở khóa khi nạp lỗi (→ pending)
```

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
DELETE /local/ho-so/:madk            Xóa HV + xóa mềm ảnh
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

### 5.0 Màn Cấu hình tool (HTG-01)
Tool có màn **Cấu hình** (gọi `/local/config`): nhập kết nối SQL Server (server/database/user/password), URL VPS, API key; nút **"Kiểm tra kết nối"** (`POST /local/config/test`) thử nối SQL Server + ping VPS trước khi lưu; lưu vào config cục bộ **mã hóa** (§15). Chưa cấu hình xong → chặn mọi chức năng nạp.

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
- **Session store:** in-memory trong tiến trình tool (1 máy, 1 người). Tool khởi động lại → đăng nhập lại. `logout` xóa token khỏi store.
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
    ▲                                          │                            │
    │  unlock: nạp lỗi/mất DB → compensation ──┘                            │
    │  job mở khóa nếu importing > 15' (EC-002) ─────▶ pending              │
    │                                                                       │
    └─ pending/imported > 30 ngày ──┐   importing: job PII BỎ QUA (EC-040)  │
                                     ▼                    admin xóa tay ─────┤
                                  deleted  ◀──────────────────────────────── ┘
```
> NAP-06 trùng CCCD trong khóa → **GIỮ `pending`** + cảnh báo (operator tự xử: bỏ qua / đổi khóa / xóa). KHÔNG có trạng thái `duplicate`.

### 7.2 Khóa & chống trùng (EC-003, EC-010, EC-011)
- Kéo: chỉ trả `pending` chưa bị khóa (`locked_by IS NULL`).
- Trước nạp: `POST /nap/:uuid/lock` set `importing` + `locked_by` (compare-and-set nguyên tử trong 1 UPDATE có WHERE `trang_thai='pending'`). Tool khác thua → báo "đang được nạp".
- Nạp xong: `da_nap` + lưu `ma_dk`; `imported` không kéo lại → không tạo HV thứ 2.
- Lỗi: `unlock` → `pending`; timeout khóa **15 phút** (env `IMPORT_LOCK_TIMEOUT_MIN=15`) → job tự mở khóa (EC-002).

### 7.3 Xóa PII (BR-016)
APScheduler quét mỗi giờ: `pending`/`imported` quá 30 ngày → xóa dòng + file ảnh thô; **bỏ qua** `importing` (EC-040). Ghi `audit_log(hanh_dong='xoa_pii')`.

### 7.4 Validate ảnh thô khi nhận (bảo mật)
`POST /api/ho-so/:uuid/anh` phải kiểm trước khi lưu: kích thước **≤ 8 MB**; **magic-byte** đúng JPEG/PNG (không tin đuôi/Content-Type); giới hạn số điểm ảnh (`Image.MAX_IMAGE_PIXELS`) để chặn ảnh "bung nén" (decompression bomb) làm treo/sập tool khi `rembg`/`Pillow` xử lý. Không hợp lệ → 4xx, báo lỗi rõ (PRD ⑦).

---

## 8. Map địa chỉ hành chính (DVHC)

> **Phục vụ:** `NAP-03`
*Vì sao nối theo tên chứ không theo mã: mã của dataset ngoài khác mã DB; (tỉnh mới, xã mới) là duy nhất 100% trong DB nên nối tên an toàn.*

### 8.1 Luồng
```
Địa chỉ text (cũ/mới) → chuẩn hóa (NFC, lower, bỏ tiền tố Tỉnh/Thành phố/Quận/Huyện/Thị xã/Phường/Xã/Thị trấn, chuẩn dấu nháy)
  → tra DM_DVHC_MAP theo (TenTinhCu,TenHuyenCu,TenXaCu)
     ├─ khớp & không chia → lấy MaDvhcMoi + MaDVQLMoi
     ├─ IsDividedWard=1 hoặc không khớp → popup chọn tay (Tỉnh→Xã từ DM_DVHC TrangThai=1)
  → điền NoiTT_MaDVHC + NoiTT_MaDVQL (+ NoiCT_* = NoiTT_* mặc định, BR-004)
```

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
Ảnh thô (từ VPS) → hiển thị + khung crop CỐ ĐỊNH 3:4
  → auto gợi ý theo nhận diện mặt → grab di chuyển + zoom (chỉnh tay) / thay ảnh
  → rembg xóa phông → nền TRẮNG → preview
  → (khi bấm Nạp) Pillow xuất .jp2
```

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
- **Hiệu năng rembg:** nạp `rembg` session (model u2net ~170 MB) **một lần lúc khởi động tool** (warm-up), giữ trong bộ nhớ. Mốc <5s/ảnh (§13) tính từ ảnh **thứ 2**; ảnh đầu (cold-start) đo riêng, chấp nhận cao hơn.

### 9.3 Lưu tạm & dọn (staging tool)
- Ảnh kéo về (thô) + ảnh đang chỉnh lưu trong **staging cục bộ máy DB** (`%LOCALAPPDATA%\pmcsdtlx-tool\staging\anh\<uuid>.*`), cạnh `staging.sqlite`. Đây là bản tạm.
- **Nạp thành công:** bản `.jp2` chính thức đã ở `ANHCDUNG\<MaKhoaHoc>\` (GIỮ) → **xóa ngay ảnh thô + ảnh làm việc trong staging** (dọn PII trên máy DB + tiết kiệm ổ).
- **Nạp lỗi:** giữ staging để thử lại.
- Trên VPS: bản thô giữ tới 30 ngày rồi job tự xóa (BR-016) — để đối chiếu/nạp lại.

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

---

## 11. Quản lý hồ sơ đã có & tạo khóa (tool)

> **Phục vụ:** `QLY-01`, `QLY-02`, `QLY-03`, `KHO-01`
*Vì sao gộp: đều là thao tác của operator trên DB đích qua SP, cùng ràng buộc BC1/GPLX.*

### 11.1 Tra cứu/sửa (QLY-01)
**Chế độ "Tra cứu DB" (CHANGES #6):** tìm khóa theo **tên/mã, MỌI khóa kể cả đã BC1** (SELECT `KhoaHoc` lọc theo tên/mã, **KHÔNG** lọc `BaoCaoI` — khác dropdown nạp của NAP-02). Chọn khóa → lưới theo khóa (`usp_NguoiLX_Select_By_MaKH`) + tìm (`usp_NguoiLX_HoSo_Search`) → mở sửa (`usp_NguoiLX_HoSo_Get_Sua_HS`) → `usp_NguoiLX_Update`/`usp_NguoiLX_HoSo_Update`. Khóa đã BC1 → badge 🔒, chặn sửa (BR-012), chỉ xem.

**Tìm trong lưới học viên (CHANGES #10):** khớp theo **tên hoặc số CCCD**; tên **chuẩn hóa bỏ dấu cả hai vế** (NFD + xóa dấu kết hợp) để gõ không dấu vẫn ra. QLY-01 tìm qua SP `usp_NguoiLX_HoSo_Search` (collation không phân biệt dấu, hoặc chuẩn hóa tương tự); NAP-01 (list tải về, hàng chờ VPS) lọc phía client trên staging SQLite đã kéo. UI chung: ô tìm đặt **đầu danh sách/lưới**; màn hẹp thu gọn thành **nút kính lúp** (bấm mới bung ô nhập).

### 11.2 Đổi khóa (QLY-02) — vòng đời file ảnh
```
Cùng hạng: usp_NguoiLX_HoSo_Update (MaKhoaHoc mới) + sinh lại SoHoSo theo khóa mới
  → di chuyển file .jp2 sang folder khóa mới (giữ tên) → cập nhật DuongDanAnh
Khác hạng: hướng xóa tạo lại.
```

### 11.3 Xóa HV (QLY-03)
`usp_NguoiLX_Delete` (cascade HoSo+GiayTo) + chuyển file `.jp2` sang `_DELETED` (xóa mềm). HV có GPLX → FK chặn.

### 11.4 Tạo khóa (KHO-01)
Chọn hạng ĐT từ `DM_HangDT` → `usp_KhoaHoc_Insert` (mã tự sinh). `HangGPLX` suy từ hạng ĐT qua `DM_HangGPLX.MaHangMoi`.

### 11.5 Nạp/thay ảnh cho HV đã có (QLY-05)
Làm SAU NAP-05, **dùng lại cơ chế ghi ảnh hướng A** (§10.3) — không gọi SP tạo hồ sơ. Luồng: màn tra cứu lọc HV theo tình trạng ảnh (`TT_XuLy='01'` chưa ảnh / `'03'` đã ảnh) → chọn HV → xử lý ảnh (tái dùng NAP-04: crop 3:4 + nền trắng + `.jp2` 353×471) → ghi `.jp2` tại `<IMG_PATH_CSDT>\<MaKhoaHoc>\<MaDK>.jp2` (ghi đè nếu đã có) → UPDATE 5 cột ảnh `NguoiLX_HoSo` (`DuongDanAnh`, `ChatLuongAnh=1`, `TT_XuLy='03'`, `NgayThuNhanAnh=getdate()`, `NguoiThuNhanAnh`) WHERE `MaDK`. Chỉ cập nhật HV đã có, không tạo bản ghi mới.
*Ca lỗi:* app cũ đang khóa file `.jp2` → báo đóng app cũ rồi thử lại; ghi `.jp2` lỗi → giữ trạng thái ảnh cũ; UPDATE lỗi → retry theo `MaDK` (§10.3).

---

## 12. Security

| Nhóm | Cơ chế |
|---|---|
| Xác thực | bcrypt password; JWT HS256 expire 8h; đọc `is_active`+vai trò từ DB mỗi request; logout qua blocklist `jti`; API key tool (cân nhắc **key riêng mỗi máy** nếu cần thu hồi độc lập); đăng nhập riêng, không dùng chung (SOD-002) |
| Dữ liệu (PII) | HTTPS toàn bộ; ảnh thô + CCCD tự xóa 30 ngày; không log nội dung CCCD; SQL login riêng (không `sa`); validate ảnh upload (§7.4) |
| API | Chặn quyền theo vai trò (403); chống IDOR bằng **kiểm sở hữu `created_by`** (UUID chỉ là định danh); validate input (pydantic); nạp DB chỉ ở tool; `/local/*` buộc token operator (không mở trống localhost) |
| DB đích | Chỉ gọi SP; **mọi SQL động (MAX SoHoSo, tra `DM_DVHC_MAP` theo text địa chỉ) phải parameterized** — không nối chuỗi; login hạn chế EXECUTE + SELECT danh mục |

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

### 16.2 Trade-offs đã quyết
**Ghi DB chỉ qua SP (không ORM):** ✅ khớp app cũ, an toàn ❌ không tự sinh/migrate schema (chấp nhận — DB có sẵn).
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
