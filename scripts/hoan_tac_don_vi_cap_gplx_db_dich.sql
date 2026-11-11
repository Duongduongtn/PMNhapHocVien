/* =====================================================================================================
   HOÀN TÁC script bo_sung_don_vi_cap_gplx_db_dich.sql — chạy trên DB đích (GPLX_CDB_CSDT)
   11/11/2026

   Xóa ĐÚNG các dòng script bổ sung đã thêm vào DM_DonViGTVT: nhận ra bằng GhiChu riêng của script
   + LoaiDV 'SO' + mã nằm trong danh sách 29 mã cũ. Không đụng dòng nào khác của danh mục.
   Sau khi hoàn tác, phần mềm cũ lại hiện nơi cấp GPLX đã có bằng số trần (vd "70") như trước.

   Nếu đã có dữ liệu khác trỏ khóa ngoại vào mã cũ (vd khóa học/giáo viên ghi mã Sở cũ) thì SQL Server
   không cho xóa → script hoàn tác toàn bộ, báo lỗi, DB giữ nguyên.

   CÁCH CHẠY: chọn ĐÚNG DB đích · chạy @ChayThat = 0 xem số dòng sẽ xóa · rồi @ChayThat = 1 để xóa thật.
   ===================================================================================================== */
SET NOCOUNT ON;
PRINT N'Đang chạy trên DB: ' + DB_NAME();
IF OBJECT_ID('dbo.DM_DonViGTVT') IS NULL
BEGIN
    RAISERROR(N'DB đang chọn không có DM_DonViGTVT — chọn lại DB rồi chạy.', 16, 1);
    RETURN;
END

DECLARE @ChayThat bit = 0;   -- 0 = chạy thử (hoàn tác) · 1 = xóa thật
DECLARE @GhiChu nvarchar(255) = N'Bổ sung mã cũ cho nơi cấp GPLX đã có (11/11/2026)';
DECLARE @n int;

BEGIN TRY
    BEGIN TRAN;

    DELETE FROM DM_DonViGTVT
    WHERE GhiChu = @GhiChu
      AND LoaiDV = 'SO'
      AND MaDV IN ('02','06','10','17','26','27','30','34','35','36','45','49','54','58','60','62',
                   '64','67','70','72','74','77','83','84','87','89','93','94','95');
    SET @n = @@ROWCOUNT;
    PRINT N'Xóa mã Sở cũ do script bổ sung thêm: ' + CAST(@n AS varchar(10)) + N' dòng';

    IF @ChayThat = 1
    BEGIN
        COMMIT TRAN;
        PRINT N'ĐÃ XÓA THẬT.';
    END
    ELSE
    BEGIN
        ROLLBACK TRAN;
        PRINT N'CHẠY THỬ — đã hoàn tác, DB không đổi. Đổi @ChayThat = 1 để xóa thật.';
    END
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRAN;
    PRINT N'KHÔNG XÓA ĐƯỢC — đã hoàn tác toàn bộ, DB giữ nguyên. Lỗi: ' + ERROR_MESSAGE();
END CATCH
