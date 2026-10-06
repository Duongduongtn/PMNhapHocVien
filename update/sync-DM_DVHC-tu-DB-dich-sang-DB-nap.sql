/* ============================================================================
   ĐỒNG BỘ DANH MỤC DM_DVHC: DB ĐÍCH (GPLX_CDB_CSDT) --> DB NẠP (GPLX_CSDT)
   ----------------------------------------------------------------------------
   Mục đích: làm DM_DVHC ở DB Nạp giống DB đích để:
     - Tỉnh sáp nhập 2025 hiển thị ĐÚNG TÊN ở DB Nạp.
     - Có mã '00' = 'Cục QLHC' (nơi cấp căn cước) trong DB Nạp.

   Chạy MỘT LẦN, trong SSMS, trên CÙNG INSTANCE chứa cả 2 DB (DESKTOP-UBV2GQI).
   Chạy LẦN LƯỢT từng bước (đừng F5 cả file) để kiểm trước khi COMMIT.

   An toàn (đã khảo sát 06/10/2026):
     - 0 dòng nguồn-thừa  -> KHÔNG DELETE  -> KHÔNG đụng 4 FK trỏ (MaDvhc,MaDVQL).
     - UPDATE 15.744 dòng chung + INSERT 11 dòng mới (gồm '00' Cục QLHC).
     - Khóa MERGE = cặp PK (MaDvhc,MaDVQL) -> FK luôn hợp lệ (2 cột này không bị sửa).
     - 2 DB KHÁC collation -> mọi so chuỗi cross-DB ép COLLATE DATABASE_DEFAULT.
     - KHÔNG copy MaDV lúc UPDATE (đích có MaDV trùng, tránh vỡ unique ở nguồn).
     - Bỏ ROW_VERSION (binary tự quản).
   ============================================================================ */

USE GPLX_CSDT;   -- chạy trong ngữ cảnh DB NẠP (đích của việc ghi)
GO

/* ---------- BƯỚC 1 — SAO LƯU bảng trước khi đổi (bắt buộc) ---------- */
IF OBJECT_ID('dbo.DM_DVHC_backup_20261006') IS NOT NULL
    DROP TABLE dbo.DM_DVHC_backup_20261006;
SELECT * INTO dbo.DM_DVHC_backup_20261006 FROM dbo.DM_DVHC;
PRINT N'Đã backup -> dbo.DM_DVHC_backup_20261006 (' + CAST(@@ROWCOUNT AS varchar) + N' dòng)';
GO

/* ---------- BƯỚC 2 — Xem trước 11 dòng SẼ CHÈN (kiểm tra, chưa đổi gì) ---------- */
SELECT src.MaDvhc, src.MaDVQL, src.TenNganGon, src.LoaiDvhc, src.TrangThai
FROM GPLX_CDB_CSDT.dbo.DM_DVHC AS src
WHERE NOT EXISTS (
    SELECT 1 FROM GPLX_CSDT.dbo.DM_DVHC AS tgt
    WHERE tgt.MaDvhc = src.MaDvhc COLLATE DATABASE_DEFAULT
      AND tgt.MaDVQL = src.MaDVQL COLLATE DATABASE_DEFAULT);
GO

/* ---------- BƯỚC 3 — MERGE trong TRANSACTION (chưa commit) ---------- */
BEGIN TRANSACTION;

MERGE dbo.DM_DVHC AS tgt
USING GPLX_CDB_CSDT.dbo.DM_DVHC AS src
    ON  tgt.MaDvhc = src.MaDvhc COLLATE DATABASE_DEFAULT
    AND tgt.MaDVQL = src.MaDVQL COLLATE DATABASE_DEFAULT

/* Dòng đã có: cập nhật tên + loại + trạng thái (KHÔNG đụng MaDvhc/MaDVQL/MaDV). */
WHEN MATCHED THEN UPDATE SET
    tgt.TenDvhc    = src.TenDvhc,
    tgt.TenNganGon = src.TenNganGon,
    tgt.TenDayDu   = src.TenDayDu,
    tgt.LoaiDvhc   = src.LoaiDvhc,
    tgt.TrangThai  = src.TrangThai,
    tgt.GhiChu     = src.GhiChu,
    tgt.NgaySua    = GETDATE(),
    tgt.NguoiSua   = N'sync_dvhc'

/* Dòng mới ở đích (11 dòng, gồm '00' Cục QLHC): chèn đủ cột. */
WHEN NOT MATCHED BY TARGET THEN
    INSERT (MaDvhc, MaDVQL, MaDV, TenDvhc, TenNganGon, TenDayDu,
            LoaiDvhc, GhiChu, TrangThai, NguoiTao, NguoiSua, NgayTao, NgaySua)
    VALUES (src.MaDvhc, src.MaDVQL, src.MaDV, src.TenDvhc, src.TenNganGon, src.TenDayDu,
            src.LoaiDvhc, src.GhiChu, src.TrangThai, N'sync_dvhc', N'sync_dvhc', GETDATE(), GETDATE());
/* CỐ Ý KHÔNG có "WHEN NOT MATCHED BY SOURCE ... DELETE" -> không xóa, an toàn FK. */

PRINT N'Số dòng MERGE tác động: ' + CAST(@@ROWCOUNT AS varchar);
GO

/* ---------- BƯỚC 4 — KIỂM trước khi COMMIT ---------- */
-- Phải thấy 00 = Cục QLHC:
SELECT MaDvhc, MaDVQL, TenNganGon, TenDayDu, LoaiDvhc, TrangThai
FROM dbo.DM_DVHC WHERE MaDvhc = '00';
-- Vài tỉnh sáp nhập (đối chiếu tên đã đúng chưa):
SELECT MaDvhc, MaDVQL, TenNganGon, TrangThai
FROM dbo.DM_DVHC WHERE MaDvhc IN ('70','75','79','01') AND LEN(MaDvhc)=2;
-- Tổng dòng nguồn phải = đích (15.755):
SELECT (SELECT COUNT(*) FROM dbo.DM_DVHC) AS nguon,
       (SELECT COUNT(*) FROM GPLX_CDB_CSDT.dbo.DM_DVHC) AS dich;
GO

/* ---------- BƯỚC 5 — CHỐT ----------
   Nếu BƯỚC 4 ĐÚNG  ->  chạy:   COMMIT;
   Nếu có gì sai     ->  chạy:   ROLLBACK;
   (Transaction đang MỞ sau BƯỚC 3 — phải chạy đúng 1 trong 2.)
*/
-- COMMIT;
-- ROLLBACK;

/* ---------- Khôi phục khẩn (nếu lỡ commit mà muốn quay lại) ----------
   BEGIN TRAN;
   DELETE FROM dbo.DM_DVHC;                       -- (cẩn thận: FK; chỉ khi chắc)
   INSERT INTO dbo.DM_DVHC SELECT * FROM dbo.DM_DVHC_backup_20261006;
   -- kiểm rồi COMMIT; / ROLLBACK;
   Thực tế nên khôi phục từ backup bảng theo cách phù hợp môi trường của bạn.
*/
