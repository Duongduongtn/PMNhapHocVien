/*
  Bật mã 00 "Cục QLHC" làm đơn vị cấp GPLX ở DB Nạp (NAP-07, CHANGES #84).
  Chạy trên DB GPLX_CSDT. Chạy lại nhiều lần vẫn an toàn.

  Vì sao: tờ khai đọc tên đơn vị cấp từ DM_DonViGTVT (usf_QuangLA_PM4_ThuNhanHS_getTenDVCap).
  Mã 00 của Cục QLHC khớp DM_DVHC ở cả DB Nạp và DB đích, nhưng DM_DonViGTVT ở DB Nạp đang ghi 00 là
  "Tổng cục đường bộ Việt Nam" và tắt. Dữ liệu cũ chưa có GPLX đã có nào mang mã 00 nên đổi tên không làm sai hồ sơ cũ.

  Chỉ đụng đúng 1 dòng DM_DonViGTVT mã 00. Không đổi DM_DVHC, không đổi DB đích.
*/
USE GPLX_CSDT;
GO
SET XACT_ABORT ON;
BEGIN TRANSACTION;

IF EXISTS (SELECT 1 FROM dbo.DM_DonViGTVT WHERE MaDV = '00')
    UPDATE dbo.DM_DonViGTVT
    SET TenDV = N'Cục QLHC',
        CoQuanQL = N'Cục Cảnh sát quản lý hành chính',
        TrangThai = 1
    WHERE MaDV = '00';
ELSE
    INSERT INTO dbo.DM_DonViGTVT (MaDV, MaDVQL, LoaiDV, TenDV, CoQuanQL, TrangThai)
    VALUES ('00', '00', 'SO', N'Cục QLHC', N'Cục Cảnh sát quản lý hành chính', 1);

COMMIT TRANSACTION;

SELECT MaDV, MaDVQL, LoaiDV, TenDV, CoQuanQL, TrangThai,
       dbo.usf_QuangLA_PM4_ThuNhanHS_getTenDVCap('00') AS TenTrenToKhai
FROM dbo.DM_DonViGTVT
WHERE MaDV = '00';
GO
