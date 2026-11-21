/* =====================================================================================================
   Bổ sung giấy tờ kèm theo + sửa cột GPLX đã có — chạy được cho DB Nạp (GPLX_CSDT) VÀ DB đích (GPLX_CDB_CSDT)
   10/11/2026, sửa 11/11/2026: bỏ USE cố định để dùng chung cho cả hai DB.

   Vì sao:
   - Màn "Giấy tờ kèm theo" của phần mềm cũ lấy danh sách bằng usp_QuangLA_PM4_ThuNhanHS_DSGiayTo: tra
     DM_LoaiHSo_GiayTo theo DM_HangGPLX.MaHangMoi bỏ dấu chấm. DB thiếu dòng cho mã hạng mới 'Am' (khóa A2),
     'Cm' (khóa C)... nên khóa đó hiện danh sách trống, và hồ sơ nạp vào không có giấy tờ nào.
   - Tool nạp từng ghi NULL vào các cột *GPLXDaCo; phần mềm cũ luôn ghi chuỗi rỗng ('' hoặc '|' theo số bằng)
     → hồ sơ do tool nạp không hiện nơi cấp GPLX trong phần mềm cũ.

   Script CHỈ THÊM / ĐIỀN Ô ĐANG TRỐNG, không sửa hay xóa dòng có sẵn:
     Phần 1  thêm danh mục giấy tờ còn thiếu cho mã hạng mới (chép từ dòng của hạng cũ tương ứng).
     Phần 2  hồ sơ CHƯA có giấy tờ nào → thêm đúng danh sách phần mềm cũ hiện cho khóa đó + bật GiayCNSK
             khi có giấy tờ số 3 (giấy khám sức khỏe), giống hồ sơ nạp đúng.
     Phần 3  hồ sơ do tool nạp có cột GPLX đã có = NULL → chuỗi rỗng như phần mềm cũ (NoiCapGPLXDaCo theo số bằng).

   Không sửa được bằng dữ liệu: khóa hạng B2 cũ (phần mềm cũ gộp B1/B2 chung mã mới 'B', luôn lấy B1).

   DB đích (CDB): phần mềm CDB hiện danh sách bằng cùng SP nên thiếu 'Am'/'Cm' như DB Nạp. Đồng bộ (tool) chép
   nguyên giấy tờ của hồ sơ ở DB Nạp, KHÔNG chép danh mục → chạy script ở CẢ HAI DB; chạy DB Nạp trước rồi mới đồng bộ.

   CÁCH CHẠY: 0) Trong SSMS chọn ĐÚNG DB ở ô "Available Databases" (dòng đầu tab Messages in tên DB đang chạy).
              1) SAO LƯU DB.  2) Chạy với @ChayThat = 0 → đọc số dòng in ra (tự hoàn tác).
              3) Hợp lý thì đổi @ChayThat = 1 rồi chạy lại.  4) Mở hồ sơ trong phần mềm cũ kiểm.
   ===================================================================================================== */
SET NOCOUNT ON;
PRINT N'Đang chạy trên DB: ' + DB_NAME();
IF OBJECT_ID('dbo.DM_LoaiHSo_GiayTo') IS NULL OR OBJECT_ID('dbo.NguoiLXHS_GiayTo') IS NULL
BEGIN
    RAISERROR(N'DB đang chọn không phải DB Nạp/DB đích GPLX — chọn lại DB rồi chạy.', 16, 1);
    RETURN;
END
SET XACT_ABORT ON;

DECLARE @ChayThat bit = 0;           -- 0 = chạy thử (hoàn tác) · 1 = ghi thật
DECLARE @MaKH varchar(13) = NULL;    -- NULL = mọi khóa; điền mã khóa để chỉ sửa phần 2 cho 1 khóa
DECLARE @n int;

BEGIN TRAN;

/* ---------- PHẦN 1: danh mục giấy tờ cho mã hạng mới ---------- */
;WITH hg AS (
    SELECT MaHang, REPLACE(MaHangMoi, '.', '') AS X,
           CASE WHEN CHARINDEX('A', MaHang) > 0 THEN 1 ELSE 2 END AS Loai
    FROM DM_HangGPLX h
    WHERE MaHang = (SELECT MIN(MaHang) FROM DM_HangGPLX h2
                    WHERE REPLACE(h2.MaHangMoi, '.', '') = REPLACE(h.MaHangMoi, '.', ''))
)
INSERT INTO DM_LoaiHSo_GiayTo (MaGT, MaLoaiHS, MaHangGPLX, TenGT, GhiChu, TrangThai, NguoiTao, NgayTao, NgaySua)
SELECT g.MaGT, hg.Loai, hg.X, g.TenGT, N'Bổ sung cho mã hạng mới (10/11/2026)', g.TrangThai, N'script', GETDATE(), GETDATE()
FROM hg
JOIN DM_LoaiHSo_GiayTo g ON g.MaLoaiHS = hg.Loai AND g.MaHangGPLX = hg.MaHang
WHERE hg.X <> hg.MaHang
  AND NOT EXISTS (SELECT 1 FROM DM_LoaiHSo_GiayTo d WHERE d.MaLoaiHS = hg.Loai AND d.MaHangGPLX = hg.X);
SET @n = @@ROWCOUNT;
PRINT N'Phần 1 - thêm danh mục giấy tờ: ' + CAST(@n AS varchar(10)) + N' dòng';

/* ---------- PHẦN 2: hồ sơ chưa có giấy tờ nào ---------- */
IF OBJECT_ID('tempdb..#hs') IS NOT NULL DROP TABLE #hs;
SELECT DISTINCT hs.MaDK, hs.SoHoSo, d.MaGT, dg.TenGT
INTO #hs
FROM NguoiLX_HoSo hs
JOIN KhoaHoc kh ON kh.MaKH = hs.MaKhoaHoc
JOIN DM_HangGPLX hg ON hg.MaHang = kh.HangGPLX
JOIN DM_LoaiHSo_GiayTo d
  ON d.MaHangGPLX = REPLACE(hg.MaHangMoi, '.', '') AND d.TrangThai = 1
 AND d.MaLoaiHS = CASE WHEN CHARINDEX('-', kh.HangDT) > 0 THEN 3
                       WHEN CHARINDEX('A', kh.HangGPLX) > 0 THEN 1 ELSE 2 END
JOIN DM_GiayTo dg ON dg.MaGT = d.MaGT
WHERE NOT EXISTS (SELECT 1 FROM NguoiLXHS_GiayTo x WHERE x.MaDK = hs.MaDK)
  AND hg.MaHang = (SELECT MIN(MaHang) FROM DM_HangGPLX h2
                   WHERE REPLACE(h2.MaHangMoi, '.', '') = REPLACE(hg.MaHangMoi, '.', ''))
  AND CHARINDEX('DB', kh.MaKH) <= 0
  AND (@MaKH IS NULL OR hs.MaKhoaHoc = @MaKH);

INSERT INTO NguoiLXHS_GiayTo (MaGT, MaDK, SoHoSo, TenGT, TrangThai)
SELECT MaGT, MaDK, SoHoSo, TenGT, 1 FROM #hs;
SET @n = @@ROWCOUNT;
DECLARE @soHS int = (SELECT COUNT(DISTINCT MaDK) FROM #hs);
PRINT N'Phần 2 - thêm giấy tờ: ' + CAST(@n AS varchar(10)) + N' dòng cho ' + CAST(@soHS AS varchar(10)) + N' hồ sơ';

UPDATE hs SET GiayCNSK = 1
FROM NguoiLX_HoSo hs
WHERE hs.MaDK IN (SELECT MaDK FROM #hs WHERE MaGT = 3) AND ISNULL(hs.GiayCNSK, 0) = 0;
SET @n = @@ROWCOUNT;
PRINT N'Phần 2 - bật dấu giấy khám sức khỏe: ' + CAST(@n AS varchar(10)) + N' hồ sơ';

/* ---------- PHẦN 3: cột GPLX đã có NULL → chuỗi rỗng như phần mềm cũ ---------- */
UPDATE NguoiLX_HoSo SET
    SoGPLXDaCo       = ISNULL(SoGPLXDaCo, ''),
    HangGPLXDaCo     = ISNULL(HangGPLXDaCo, ''),
    NgayTTGPLXDaCo   = ISNULL(NgayTTGPLXDaCo, ''),
    NgayCapGPLXDaCo  = ISNULL(NgayCapGPLXDaCo, ''),
    NgayHHGPLXDaCo   = ISNULL(NgayHHGPLXDaCo, ''),
    DonViCapGPLXDaCo = ISNULL(DonViCapGPLXDaCo, ''),
    -- quốc gia cấp: rỗng theo số bằng (đếm dấu | trong số GPLX), như phần mềm cũ ghi '' / '|'
    NoiCapGPLXDaCo   = ISNULL(NoiCapGPLXDaCo,
                              REPLICATE('|', LEN(ISNULL(SoGPLXDaCo, '')) - LEN(REPLACE(ISNULL(SoGPLXDaCo, ''), '|', ''))))
-- Chỉ hồ sơ tool nạp (quốc gia cấp NULL). Không đụng dữ liệu cũ 2019 do phần mềm cũ để NULL lẻ tẻ ở cột khác.
WHERE NoiCapGPLXDaCo IS NULL;
SET @n = @@ROWCOUNT;
PRINT N'Phần 3 - sửa cột GPLX đã có đang NULL: ' + CAST(@n AS varchar(10)) + N' hồ sơ';

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
