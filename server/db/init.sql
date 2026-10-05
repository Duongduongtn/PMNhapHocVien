-- Schema PostgreSQL cho dịch vụ VPS (TDD §3.2).
-- File này được postgres container nạp tự động lần đầu khởi tạo
-- (mount vào /docker-entrypoint-initdb.d). Logic auth/hàng đợi/job PII
-- xây trên nền schema này ở task 14/15/16.
-- gen_random_uuid() là hàm lõi của PostgreSQL ≥ 13, không cần extension.

-- ────────────────────────────────────────────
-- USERS & AUTH
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
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
CREATE TABLE IF NOT EXISTS ho_so_thu_thap (
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
-- TOKEN BLOCKLIST (logout thu hồi phiên — TDD §5.1)
-- jti của token đã đăng xuất, giữ tới khi token hết hạn (exp) rồi dọn.
-- Ghi chú: TDD §3.2 ghi sót bảng này dù §5.1 có mô tả → thêm ở task 14 (HTG-01②);
-- cần /capnhat đồng bộ lại §3.2.
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS token_blocklist (
  jti        UUID PRIMARY KEY,
  exp        TIMESTAMPTZ NOT NULL,
  revoked_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_blocklist_exp ON token_blocklist(exp);

-- ────────────────────────────────────────────
-- REFRESH TOKEN (phiên tool vĩnh viễn — DGT-04, TDD §12)
-- Lưu HASH sha256 hex (KHÔNG plaintext). Xoay một-lần-dùng + thu hồi khi
-- Đăng xuất / đổi mật khẩu / tài khoản bị khóa. Chỉ cấp cho đăng nhập QUA TOOL.
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS refresh_token (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash   CHAR(64) UNIQUE NOT NULL,          -- sha256 hex
  created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  last_used_at TIMESTAMPTZ,
  revoked      BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX IF NOT EXISTS idx_refresh_user ON refresh_token(user_id);

-- ────────────────────────────────────────────
-- AUDIT LOG (ai gửi/ai nạp/ai xóa — PII)
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_log (
  id         BIGSERIAL PRIMARY KEY,
  actor_id   UUID REFERENCES users(id),
  hanh_dong  VARCHAR(30) NOT NULL,               -- 'gui','keo','nap','xoa_pii','dang_nhap'
  uuid_hs    UUID,
  chi_tiet   JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ────────────────────────────────────────────
-- INDEXES
-- ────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_hstt_trangthai ON ho_so_thu_thap(trang_thai);
CREATE INDEX IF NOT EXISTS idx_hstt_pending_time ON ho_so_thu_thap(created_at) WHERE trang_thai = 'pending';
CREATE INDEX IF NOT EXISTS idx_hstt_cccd ON ho_so_thu_thap(so_cccd);
CREATE INDEX IF NOT EXISTS idx_hstt_creator ON ho_so_thu_thap(created_by);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_log(created_at);
