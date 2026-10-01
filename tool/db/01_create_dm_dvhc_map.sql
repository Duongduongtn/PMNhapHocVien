-- ============================================================================
-- 01_create_dm_dvhc_map.sql
-- Tạo bảng phụ ánh xạ địa chỉ hành chính cũ -> xã mới (sáp nhập 2025) trong GPLX_CSDT.
-- Schema theo TDD §3.3. Bảng phục vụ NAP-03 (map địa chỉ) — tool CHỈ ĐỌC bảng này.
--
-- Chạy MỘT LẦN trên SSMS bằng tài khoản có quyền tạo bảng (DDL).
-- Sau khi tạo xong, chạy tiếp 02_seed_dm_dvhc_map.sql để nạp dữ liệu.
-- ============================================================================

USE GPLX_CSDT;
GO

IF OBJECT_ID('dbo.DM_DVHC_MAP', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.DM_DVHC_MAP (
        Id             INT IDENTITY(1,1) PRIMARY KEY,
        TenTinhCu      NVARCHAR(100) NOT NULL,   -- đã chuẩn hóa: lower, bỏ tiền tố, khi tra khớp y hệt
        TenHuyenCu     NVARCHAR(100) NOT NULL,
        TenXaCu        NVARCHAR(100) NOT NULL,
        MaDvhcMoi      VARCHAR(5)  NOT NULL,      -- = DM_DVHC.MaDvhc (TrangThai=1)
        MaDVQLMoi      VARCHAR(5)  NOT NULL,      -- = DM_DVHC.MaDVQL
        TenXaMoi       NVARCHAR(100) NOT NULL,    -- tên hiển thị (giữ nguyên dấu/hoa thường)
        TenTinhMoi     NVARCHAR(100) NOT NULL,
        IsDividedWard  BIT NOT NULL DEFAULT 0,    -- 1 = xã cũ chia nhiều xã mới -> cần chọn tay
        NgayTao        DATETIME NOT NULL DEFAULT GETDATE()
    );
    CREATE INDEX IX_DVHCMAP_cu ON dbo.DM_DVHC_MAP(TenTinhCu, TenHuyenCu, TenXaCu);
    PRINT N'Đã tạo bảng dbo.DM_DVHC_MAP + index IX_DVHCMAP_cu.';
END
ELSE
    PRINT N'Bảng dbo.DM_DVHC_MAP đã tồn tại — bỏ qua CREATE.';
GO
