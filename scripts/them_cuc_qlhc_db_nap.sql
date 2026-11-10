/* =====================================================================================================
   Thêm "Cục QLHC" (mã 00) làm NƠI CẤP CĂN CƯỚC vào DB Nạp (GPLX_CSDT) cũ — chạy 1 lần · 10/11/2026

   Tool tự điền nơi cấp căn cước '00' cho CCCD 12 số (NguoiLX.NoiCapCMT). Phần mềm cũ ghép tên theo DM_DVHC
   (form: TenNganGon "Cục QLHC", tờ khai: TenDayDu). DB thiếu dòng này thì nạp vẫn thành công (cột không có
   khóa ngoại) nhưng nơi cấp hiện TRỐNG.
   (Nơi cấp GPLX đã có KHÔNG cần Cục QLHC: suy từ 2 số đầu số GPLX — CHANGES #98.)

   Không cần DB đích. Không có khóa ngoại nào trỏ vào DM_DVHC. Chỉ đụng đúng dòng mã 00:
   - chưa có → thêm (giống hệt dòng đang chạy ở DB Nạp máy dev, đã kiểm hiển thị đúng);
   - đã có   → chỉ sửa tên cho đúng "Cục QLHC"; giữ nguyên TrangThai (phần mềm cũ tra tên không lọc
     TrangThai; để tắt thì ô chọn địa chỉ không lẫn "Cục" vào danh sách xã/tỉnh).
   Chạy lại nhiều lần vẫn an toàn.

   CÁCH CHẠY: 1) SAO LƯU DB.  2) Chạy với @ChayThat = 0 → đọc kết quả in ra (tự hoàn tác).
              3) Đúng thì đổi @ChayThat = 1 rồi chạy lại.  4) Dòng "Kiểm —" phải ra "Cục QLHC".
   ===================================================================================================== */
USE GPLX_CSDT;
SET NOCOUNT ON;
SET XACT_ABORT ON;

DECLARE @ChayThat bit = 0;           -- 0 = chạy thử (hoàn tác) · 1 = ghi thật
DECLARE @n int;

BEGIN TRAN;

/* ---------- DM_DVHC 00 — nơi cấp căn cước ---------- */
IF EXISTS (SELECT 1 FROM dbo.DM_DVHC WHERE MaDvhc = '00')
BEGIN
    UPDATE dbo.DM_DVHC
    SET TenDvhc = N'Cục Cảnh sát quản lý hành chính',
        TenNganGon = N'Cục QLHC',
        TenDayDu = N'Cục Cảnh sát quản lý hành chính',
        NgaySua = GETDATE()
    WHERE MaDvhc = '00'
      AND (TenNganGon <> N'Cục QLHC' OR ISNULL(TenDayDu, N'') <> N'Cục Cảnh sát quản lý hành chính');
    SET @n = @@ROWCOUNT;
    PRINT N'DM_DVHC: đã có mã 00 — sửa tên ' + CAST(@n AS varchar(10)) + N' dòng (0 = đã đúng sẵn).';
END
ELSE
BEGIN
    INSERT INTO dbo.DM_DVHC (MaDvhc, MaDVQL, MaDV, TenDvhc, TenNganGon, TenDayDu, LoaiDvhc, GhiChu, TrangThai, NguoiTao, NguoiSua, NgayTao, NgaySua)
    VALUES ('00', '00', '00', N'Cục Cảnh sát quản lý hành chính', N'Cục QLHC', N'Cục Cảnh sát quản lý hành chính', 'C', N'', 0, N'script', N'script', GETDATE(), GETDATE());
    PRINT N'DM_DVHC: THÊM mã 00 "Cục QLHC".';
END

/* ---------- Kiểm: đúng như phần mềm cũ sẽ hiển thị ---------- */
DECLARE @noiCapCccd nvarchar(100) = (SELECT TOP 1 TenNganGon FROM dbo.DM_DVHC WHERE MaDvhc = '00');
DECLARE @toKhaiCccd nvarchar(200) = (SELECT TOP 1 TenDayDu FROM dbo.DM_DVHC WHERE MaDvhc = '00');
PRINT N'Kiểm — nơi cấp căn cước (form): ' + ISNULL(@noiCapCccd, N'(TRỐNG)')
    + N' · (tờ khai): ' + ISNULL(@toKhaiCccd, N'(TRỐNG)');

IF @ChayThat = 1
BEGIN
    COMMIT TRAN;
    PRINT N'ĐÃ GHI THẬT.';
END
ELSE
BEGIN
    ROLLBACK TRAN;
    PRINT N'Chạy thử xong — đã hoàn tác, DB không đổi. Đổi @ChayThat = 1 để ghi thật.';
END
