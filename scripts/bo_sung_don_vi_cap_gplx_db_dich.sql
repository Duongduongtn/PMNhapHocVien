/* =====================================================================================================
   Bổ sung mã Sở GTVT cũ để phần mềm cũ hiện TÊN nơi cấp GPLX đã có — chạy trên DB đích (GPLX_CDB_CSDT)
   11/11/2026

   Vì sao:
   - Phần mềm cũ hiện nơi cấp GPLX đã có bằng hàm usf_QuangLA_PM4_ThuNhanHS_getTenDVCap: tra mã trong
     DM_DonViGTVT rồi thay bằng TenDV; mã không có trong danh mục thì in nguyên số (vd "70").
   - DB đích đã đổi danh mục theo 34 tỉnh sau sáp nhập 2025, bỏ 29 mã Sở cũ (70, 74, 67, 72...). GPLX cấp
     trước đây vẫn mang mã cũ (2 số đầu số GPLX) → hồ sơ đồng bộ sang hiện "70" thay cho tên tỉnh.
   - Dữ liệu hồ sơ đồng bộ ĐÚNG (tool chép nguyên 7 cột GPLX đã có), chỉ thiếu danh mục → không sửa tool/schema.

   Script làm gì:
   - Thêm 29 mã cũ còn thiếu vào DM_DonViGTVT, tên = TÊN TỈNH MỚI sau sáp nhập, lấy đúng TenDV của mã mới
     tương ứng ngay trong DB này (vd 70 lấy tên của 75 "Đồng Nai").
   - TrangThai = 0 (ngưng dùng) để không chen vào ô chọn của phần mềm; hàm hiện tên không lọc TrangThai nên vẫn tra ra.
   - CHỈ THÊM mã chưa có; không sửa/xóa 36 mã đang có. Chạy lại nhiều lần an toàn (lần sau thêm 0 dòng).
   - Dòng thêm mang GhiChu riêng để script hoàn tác (hoan_tac_don_vi_cap_gplx_db_dich.sql) xóa đúng chúng.

   CÁCH CHẠY: 0) Trong SSMS chọn ĐÚNG DB đích ở ô "Available Databases" (dòng đầu tab Messages in tên DB).
              1) SAO LƯU DB.  2) Chạy với @ChayThat = 0 → đọc số dòng in ra (tự hoàn tác).
              3) Hợp lý thì đổi @ChayThat = 1 rồi chạy lại.  4) Mở hồ sơ có GPLX đã có trong phần mềm cũ kiểm.
   ===================================================================================================== */
SET NOCOUNT ON;
PRINT N'Đang chạy trên DB: ' + DB_NAME();
IF OBJECT_ID('dbo.DM_DonViGTVT') IS NULL OR OBJECT_ID('dbo.NguoiLX_HoSo') IS NULL
   OR OBJECT_ID('dbo.usf_QuangLA_PM4_ThuNhanHS_getTenDVCap') IS NULL
BEGIN
    RAISERROR(N'DB đang chọn không phải DB GPLX (thiếu DM_DonViGTVT / NguoiLX_HoSo / hàm hiện tên nơi cấp) — chọn lại DB rồi chạy.', 16, 1);
    RETURN;
END
SET XACT_ABORT ON;

DECLARE @ChayThat bit = 0;   -- 0 = chạy thử (hoàn tác) · 1 = ghi thật
DECLARE @GhiChu nvarchar(255) = N'Bổ sung mã cũ cho nơi cấp GPLX đã có (11/11/2026)';
DECLARE @n int, @truoc int, @sau int;

-- Mã Sở cũ → mã tỉnh mới sau sáp nhập 2025 (đang có trong DB đích)
DECLARE @map TABLE (MaCu varchar(6) COLLATE DATABASE_DEFAULT PRIMARY KEY, MaMoi varchar(6) COLLATE DATABASE_DEFAULT);
INSERT INTO @map (MaCu, MaMoi) VALUES
 ('02','08'),('06','19'),('10','15'),('17','25'),('26','25'),('27','24'),('30','31'),('34','33'),
 ('35','37'),('36','37'),('45','44'),('49','48'),('54','66'),('58','56'),('60','68'),('62','51'),
 ('64','52'),('67','68'),('70','75'),('72','80'),('74','79'),('77','79'),('83','86'),('84','86'),
 ('87','82'),('89','91'),('93','92'),('94','92'),('95','96');

-- Hồ sơ có GPLX đã có mà phần mềm cũ vẫn hiện số trần (trước khi thêm)
SELECT @truoc = COUNT(*) FROM NguoiLX_HoSo
WHERE DonViCapGPLXDaCo LIKE '%[0-9]%'
  AND dbo.usf_QuangLA_PM4_ThuNhanHS_getTenDVCap(DonViCapGPLXDaCo) LIKE '%[0-9]%';
PRINT N'Hồ sơ đang hiện nơi cấp GPLX bằng số trần: ' + CAST(@truoc AS varchar(10));

-- Mã cũ mà mã mới tương ứng không có trong DB này → không thêm, báo ra
SELECT @n = COUNT(*) FROM @map m
WHERE NOT EXISTS (SELECT 1 FROM DM_DonViGTVT d WHERE d.MaDV = m.MaCu)
  AND NOT EXISTS (SELECT 1 FROM DM_DonViGTVT d WHERE d.MaDV = m.MaMoi);
IF @n > 0 PRINT N'Bỏ qua ' + CAST(@n AS varchar(10)) + N' mã cũ vì DB không có mã tỉnh mới tương ứng.';

BEGIN TRAN;

INSERT INTO DM_DonViGTVT (MaDV, MaDVQL, LoaiDV, TenDV, CoQuanQL, CacHangGPLX, DienThoai, Fax, DiaChi, LuuLuongDT,
                          SoGP, NgayGP, LanhDao, GhiChu, TrangThai, NguoiTao, NguoiSua, NgayTao, NgaySua,
                          Website, DienTichSanTap, NgayHHGP, DiaDiemDaoTao, MaDvOld)
SELECT m.MaCu, m.MaCu, 'SO', moi.TenDV, moi.CoQuanQL, '', '', '', '', 0,
       '', moi.NgayGP, '', @GhiChu, 0, N'ADMIN', N'ADMIN', GETDATE(), GETDATE(),
       '', 0, moi.NgayHHGP, '', ''
FROM @map m
JOIN DM_DonViGTVT moi ON moi.MaDV = m.MaMoi
WHERE NOT EXISTS (SELECT 1 FROM DM_DonViGTVT d WHERE d.MaDV = m.MaCu);
SET @n = @@ROWCOUNT;
PRINT N'Thêm mã Sở cũ vào danh mục: ' + CAST(@n AS varchar(10)) + N' dòng';

SELECT @sau = COUNT(*) FROM NguoiLX_HoSo
WHERE DonViCapGPLXDaCo LIKE '%[0-9]%'
  AND dbo.usf_QuangLA_PM4_ThuNhanHS_getTenDVCap(DonViCapGPLXDaCo) LIKE '%[0-9]%';
PRINT N'Sau khi thêm, hồ sơ còn hiện số trần: ' + CAST(@sau AS varchar(10)) + N' (kỳ vọng 0)';

IF @ChayThat = 1
BEGIN
    COMMIT TRAN;
    PRINT N'ĐÃ GHI THẬT.';
END
ELSE
BEGIN
    ROLLBACK TRAN;
    PRINT N'CHẠY THỬ — đã hoàn tác, DB không đổi. Đổi @ChayThat = 1 để ghi thật.';
END
