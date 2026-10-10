# Tham chiếu DB đích GPLX_CDB_CSDT (cho module Sync + Cập nhật kết quả đào tạo)

> Tài liệu phân tích DB đích để **code đúng cách tạo học viên / cập nhật kết quả** ở `GPLX_CDB_CSDT`.
> Đọc file này trước khi code bất cứ phần nào ghi vào `GPLX_CDB_CSDT` (SYNC-01/02/03 và module #3 "Cập nhật kết quả đào tạo" sau này).
> Nguồn: probe trực tiếp DB ngày **04/10/2026** (schema thật, không phải suy đoán). Legacy GPLX chuẩn Cục ĐBVN.

## 0. Kết nối & cơ sở đào tạo

- Server `DESKTOP-UBV2GQI` · DB `GPLX_CDB_CSDT` · dùng chung host/user/pass với `GPLX_CSDT` (chỉ khác tên DB) — xem `DBcu/env.txt`.
- **Mã CSĐT của DB này = `75032`** (DB đang chứa dữ liệu CSĐT 75032, dùng chung máy với dự án). 729 `NguoiLX`, 729 `NguoiLX_HoSo`, 2187 `NguoiLXHS_GiayTo`, 15 `KhoaHoc`.
- **Cách lấy mã CSĐT ĐÚNG** (KHÔNG bê `MaCSDT` từ bản ghi nguồn `GPLX_CSDT`):
  - Nguồn chuẩn: `SELECT GiaTriTS FROM QTHT_ThamSoHT WHERE TenTS='MA_CSDT'` → `75032`. (Cùng chỗ: `MA_DONVI=75032`, `IMG_PATH_CSDT=D:\GPLXCSDT\ANHCDUNG`.)
  - Khi tạo HV: mã CSĐT lấy từ **khóa ĐÍCH** (`KhoaHoc.MaCSDT` của khóa người dùng chọn ở CDB) — giá trị này = `QTHT.MA_CSDT`. `usp_NguoiLX_Insert` dùng nó qua `@DonViNhanHSo`.

## 1. Cách tạo 1 học viên MỚI đúng chuẩn CDB (dùng cho Sync)

Thứ tự: `usp_NguoiLX_Insert` → `usp_NguoiLX_HoSo_Insert` → `usp_NguoiLXHS_GiayTo_Insert` (mỗi SP tự `BEGIN/COMMIT TRANSACTION`).

**Khuyến nghị:** gọi **đúng 3 SP này** thay vì INSERT thô như sync_tool cũ → MaDK + SoHoSo sinh theo chuẩn DB, hết nợ kỹ thuật #1 (SoHoSo) và #3 (giấy tờ).

### 1.1 `usp_NguoiLX_Insert` (24 tham số, `@MaDK` OUT)
```
@MaDK OUT, @DonViNhanHSo, @HoDemNLX, @TenNLX, @HoVaTen, @MaQuocTich, @NgaySinh,
@NoiTT, @NoiTT_MaDVHC, @NoiTT_MaDVQL, @NoiCT, @NoiCT_MaDVHC, @NoiCT_MaDVQL,
@SoCMT, @NgayCapCMT, @NoiCapCMT, @GhiChu, @TrangThai, @NguoiTao, @NguoiSua,
@NgayTao, @NgaySua, @GioiTinh, @HoVaTenIn
```
- **Sinh MaDK:** `IF @MaDK IS NULL OR LEN=0 → @MaDK = dbo.CreateNewMaDK(@DonViNhanHSo)`. Truyền `@MaDK=NULL` để DB sinh (ngày hôm nay); truyền sẵn MaDK nếu **backdate** (xem §2).
- ⚠️ **`@NgayTao`/`@NgaySua` BỊ BỎ QUA** — thân SP hardcode `getdate()`. Muốn backdate phải `UPDATE NguoiLX SET NgayTao=?,NgaySua=? WHERE MaDK=?` SAU khi insert.
- `@NgaySinh` là **varchar(8)** `yyyyMMdd` (không phải datetime). `@NgayCapCMT` là datetime.
- `@DonViNhanHSo` = mã CSĐT khóa đích (75032).

### 1.2 `usp_NguoiLX_HoSo_Insert` (76 tham số, `@SoHoSo` OUT)
- **Sinh SoHoSo:** `IF @SoHoSo IS NULL OR LEN=0 → @SoHoSo = dbo.CreateNewSoHoso(@MaDK, @HangGPLX, 'I')` → dạng **`<Hạng><2 số>`** (`B01`). ⚠️ **ĐÍNH CHÍNH 04/10:** dữ liệu thật CSDL đích **100% SoHoSo là số thuần `001/002`** (kể cả 502 bản `NguoiTao=ADMIN` của phần mềm CDB; 0 bản `Bxx`) → **KHÔNG truyền `@SoHoSo=NULL`** (sẽ ra `B01` lệch dữ liệu). **Port sát sync_tool**: tự sinh **SoHoSo số** (MAX(CAST(SoHoSo AS INT))+1 theo khóa, zero-pad 3) rồi INSERT thô `NguoiLX_HoSo` (sync_tool dùng INSERT thô, không dùng SP này). PK `NguoiLX_HoSo = MaDK` nên SoHoSo trùng giữa các khóa KHÔNG vi phạm PK — "nợ #1" không áp dụng.
- ⚠️ `@NgayTao/@NgaySua` cũng hardcode `getdate()` → backdate phải UPDATE sau. `@NgayNhanHSo` thì nhận đúng tham số (OK để đặt ngày nhập HS).
- Cột `Transfer_flag` (NOT NULL, def 0) + `IDs` (identity) KHÔNG nằm trong SP → tự nhận default.
- Nhóm tham số kết quả (`@KetQua_LyThuyet`, `@KetQuaSH`, `@MaBC1`, `@MaBC2`…) khi tạo mới để mặc định/NULL.

### 1.3 `usp_NguoiLXHS_GiayTo_Insert`
```
@MaGT int, @MaDK, @SoHoSo, @TenGT, @TrangThai
```
- Insert `@MaGT` tường minh. ✅ **Đã kiểm 04/10: `MaGT` KHÔNG phải IDENTITY** (`IsIdentity=0`). `MaGT` là **mã loại giấy tờ** (từ `DM_GiayTo`, vd 3=Giấy KSK), lặp qua nhiều hồ sơ → PK `NguoiLXHS_GiayTo = (MaDK, SoHoSo, MaGT)`. **Sync copy `MaGT` từ nguồn** truyền vào SP (đúng như sync_tool). Hàm `GetMaGiaytoByHosoForSync` chỉ **đọc** (nối chuỗi MaGT bằng `|`), KHÔNG sinh mã — không dùng cho insert.

## 2. Các hàm sinh mã (format + cạm bẫy)

| Hàm | Format | Ghi chú |
|---|---|---|
| `CreateNewMaDK(@MaVPDK)` | `MaCSDT-yyyyMMdd-nnnnnn` (21 ký tự) | **Hardcode GETDATE** (ngày hôm nay). Đếm `MAX(SUBSTRING(MaDK,16,6))+1` theo `LEFT(MaDK,14)=MaVPDK-yyyyMMdd`, `LEN=21`. **Giả định MaCSDT đúng 5 ký tự** (75032 đạt). Backdate → phải tự sinh phía app. |
| `CreateNewSoHoso(@MaDK,@HangGPLX,'I'/'U')` | `<Hạng><2 số>` vd `B01` | Đếm theo **từng MaDK** (không theo khóa). PK `NguoiLX_HoSo = MaDK` nên SoHoSo không thuộc PK → không gây trùng PK. |
| `CreateNewMaKhoaHoc(@MaSoGTVT,@MaCSDT,@HangGPLX)` | `MaCSDT + K + YY + 4 số` vd `75032K260001` | Dùng GETDATE year. Bỏ qua mã cũ đuôi ≥1000 (vá bug cũ). Chỉ dùng khi tạo khóa, không dùng cho sync. |

**Backdate MaDK (ngày nhập HS ≠ hôm nay):** tự query `MAX(SUBSTRING(MaDK,16,6))` theo prefix `MaCSDT-yyyyMMdd` của ngày chọn rồi cấp dải `[MAX+1..MAX+N]` (đúng logic `sinh_madk_batch` của sync_tool), truyền MaDK đó vào `usp_NguoiLX_Insert` + `UPDATE` 4 cột ngày.

## 3. Khóa chính & FK cascade (ảnh hưởng SKIP + ROLLBACK)

- **PK:** `NguoiLX = PK(MaDK)` · `NguoiLX_HoSo = PK(MaDK)` → **1 người = 1 hồ sơ = 1 MaDK** (xác nhận bằng schema, không chỉ nghiệp vụ). HV đã có `MaDK` ở đích → **skip** (không thêm hồ sơ 2).
- **ON DELETE CASCADE:** `NguoiLX→NguoiLX_HoSo`, `NguoiLX_HoSo→NguoiLXHS_GiayTo`, **`KhoaHoc→NguoiLX_HoSo`** (xóa khóa kéo xóa hồ sơ!). → Rollback: `DELETE NguoiLX WHERE MaDK=?` tự dọn HoSo + GiayTo.
- **CHẶN xóa:** `FK_NguoiLX_HoSo_BaoCaoI` = **NO_ACTION** → HV đã có dòng trong `BaoCaoI` (đã Báo cáo 1) thì **DELETE sẽ lỗi**. Rollback chỉ an toàn cho HV chưa BC1 (sync đặt `TT_XuLy=03`, chưa BC1 nên thường OK; vẫn phải bắt lỗi).

## 4. Cột bảng trọng tâm (khi tạo HV phải đủ NOT NULL)

- **NguoiLX NOT NULL:** MaDK, DonViNhanHSo, HoDemNLX, TenNLX, HoVaTen, MaQuocTich, NgaySinh(varchar8), NoiTT, NoiTT_MaDVHC, NoiTT_MaDVQL, NoiCT, NoiCT_MaDVHC, NoiCT_MaDVQL, SoCMT, TrangThai(def 1), NgayTao/NgaySua(def getdate), GioiTinh(char1), HoVaTenIn. Nullable: NgayCapCMT, NoiCapCMT, GhiChu, NguoiTao/NguoiSua, SO_CMND_CU.
- **NguoiLX_HoSo NOT NULL:** MaDK, SoHoSo, MaCSDT, MaSoGTVT, MaDVNhanHSo, NgayNhanHSo, MaLoaiHs(int), TT_XuLy(varchar2), HangGPLX, TrangThai(def 0), NgayTao/NgaySua, IDs(identity), Transfer_flag(def 0).
- **NguoiTao thực tế trong DB:** `ADMIN`(502) + `SYNC`(226, công cụ cũ) + 10 bản mới nhất `admin`. → Ghi `NguoiTao=NguoiSua='admin'` cho bản sync (giống phần mềm CDB; TDD-decisions §15).

## 5. Module #3 — Cập nhật kết quả đào tạo (dự kiến)

Dữ liệu kết quả đào tạo **nằm sẵn trong `NguoiLX_HoSo`** (không cần bảng mới) — các cột đáng chú ý:
- Lý thuyết/thực hành: `KetQua_LyThuyet`, `KetQua_Hinh`, `KetQua_Duong`, `KetQuaSH`, `KetQuaSHM`, `DiemKQLyThuyet`, `DiemKQThucHanh`, `KQLyThuyet`, `KQThucHanh`, `TongQDThucHanh`, `TGThucHanhHinh/Duong`.
- Tốt nghiệp/CCN: `KetLuanCSDT`, `XepLoaiTotNghiep`, `SoGiayCNTN`, `SoCCN`, `NgayCapCCN`, `SoQuyetDinhTN`, `NgayRaQDTN`, `VaoSoCNNSo`, `NgayVaoSoCNN`.
- Báo cáo: `MaBC1`, `KQ_BC1`, `MaBC2`, `KetQuaBC2`, `MaLyDoTCBC2` + bảng `BaoCaoI`/`BaoCaoII`.
- SP liên quan: `usp_BaoCaoII_Insert/Update`, `usp_BaoCaoII_Update_PheDuyetKQDT`, `usp_CSDT_PheDuyetKQDT_TiepNhan`, `usp_BaoCao1_KetQua_update`, hàm `usf_GetTrangThaiHocVien`.
- Bảng phụ: `KhoaHoc_GiaoVien`, `KhoaHoc_XeTap`, `LichHoc`, `DM_MonHoc`, `GiaoVien`, `XeTap`, `KySH`.

> Khi làm module #3: cập nhật kết quả = UPDATE các cột trên trong `NguoiLX_HoSo` (ưu tiên qua SP nếu có SP update phù hợp — kiểm `usp_NguoiLX_HoSo_Update` / `usp_BaoCaoII_*`), KHÔNG tự chế UPDATE thô nếu DB có SP chuẩn.

## 6. Việc cần KIỂM khi code (chưa chốt từ probe)

1. ✅ ĐÃ KIỂM 04/10: `NguoiLXHS_GiayTo.MaGT` **không IDENTITY**, là mã loại giấy tờ (DM_GiayTo), PK composite `(MaDK,SoHoSo,MaGT)` → copy từ nguồn, truyền `@MaGT` vào SP.
2. Đọc thân `usp_NguoiLX_HoSo_Update` (nếu dùng cho module #3) + `usp_BaoCaoII_Update_PheDuyetKQDT` để biết tham số.
3. Xác nhận `KhoaHoc.MaCSDT` của mọi khóa đích = `QTHT.MA_CSDT` (75032) — nếu lệch, ưu tiên `KhoaHoc.MaCSDT` của khóa đang chọn.
4. Dữ liệu dev hiện là CSĐT 75032; nếu production là CSĐT khác thì mã CSĐT tự đổi theo khóa/QTHT (code không hardcode).

## 7. "Đã kết xuất DKKH" — định nghĩa đúng (verify 05/10/2026)

**DKKH = Đăng ký khóa học đã kết xuất/gửi lên Sở (TW).** Dùng để: (a) chặn sửa nhân thân HV ở Tra cứu CDB (TCB-03); (b) lọc khóa đích ở Bàn đồng bộ (chỉ nạp vào khóa **chưa** gửi Sở — thêm HV sau khi đã gửi sẽ lệch danh sách đã đăng ký).

**Tín hiệu ĐÚNG:** khóa đã kết xuất DKKH ⇔ tồn tại gói trong **`TRANS_CLI_HangDoiGui`** có **`KieuDuLieu = 'DANG_KY_KHOA_HOC'`** mà **`DuongDan` (tên file) chứa MaKH của khóa**, neo giữa 2 dấu `_`:
```
C:\DKKH_<MaCSDT>_<MaSoGTVT>_<MaKH>_<yyyyMMdd>_<HHmmss>.zip
      vd: DKKH_75032_75_75032K260009_20261002_092630.zip  ← khóa 75032K260009
```
SQL (dùng CHARINDEX để tránh `%`/`%%` của pymssql) — định nghĩa CHUNG ở `tool/app/sync_helpers.py: dkkh_exists_sql(alias)`:
```sql
EXISTS (SELECT 1 FROM dbo.TRANS_CLI_HangDoiGui g
        WHERE g.KieuDuLieu = 'DANG_KY_KHOA_HOC'
          AND CHARINDEX('_' + <alias>.MaKH + '_', g.DuongDan) > 0)
```
Mốc tính "đã kết xuất" = **có BẤT KỲ gói nào** (bất kể `TrangThai` 0/1/2 — nghĩa 0/1/2 chưa xác minh; một khi đã sinh file đăng ký là đã kết xuất).

**KHÔNG dùng các tín hiệu sau (đã loại sau khi tra dữ liệu thật):**
- ❌ `KhoaHoc.SoQD_KhaiGiang` có giá trị — **mọi khóa đều có** số QĐ khai giảng nội bộ (16/16 khóa), không phân biệt đã/chưa gửi Sở. *(Đây là định nghĩa SAI dùng ở TCB-02/03/04 trước 05/10 — đã sửa sang tín hiệu TRANS_CLI.)*
- ❌ `KhoaHoc.TT_Xuly` — **luôn NULL** ở CSĐT này.
- ❌ `NguoiLX_HoSo.TT_XuLy` per-HV — khóa đã gửi DKKH nhưng HV vẫn ở `03` ("Đã nhận ảnh chân dung" = CDB "Đã đăng ký khóa học"), không đổi theo việc gửi Sở.

**Bảng `TRANS_CLI_HangDoiGui`** (hàng đợi gửi TW): `Id, NoiGui, NoiNhan, DuongDan, KickThuocFile, TrangThai, NguoiTao, NgayTao, KieuDuLieu`. `KieuDuLieu` ∈ {`DANG_KY_KHOA_HOC`, `BAO_CAO1`, `BAO_CAO2`, `KET_QUA_DAO_TAO`}. **Chỉ có ở CSDL ĐÍCH** → `dkkh_exists_sql` chỉ dùng cho truy vấn đích (nguồn GPLX_CSDT không chắc có bảng này).

> Kiểm chứng 05/10: 16 khóa đích 2026 → 14 đã DKKH, **2 chưa** (`75032K26C1003` C1-K09 — có SoQD nhưng chưa gửi Sở; `75032K260010` B01-KTEST — khóa test). Dùng SoQD thì cả 16 "đã DKKH" → filter rỗng và TCB-03 chặn nhầm C1-K09.

---
*Ghi bởi phân tích 04/10/2026 phục vụ SYNC-01/02/03 + module Cập nhật kết quả đào tạo. §7 thêm 05/10/2026 (định nghĩa DKKH đúng). Cập nhật lại nếu schema CDB đổi.*

## 8. Phân GV / xe / lịch cho khóa (rà soát 10/10/2026 — phục vụ PCG-01..05)

**Bảng:** `GiaoVien` (87) · `XeTap` (89, 7 đã tắt) · `KhoaHoc_GiaoVien` (373) · `KhoaHoc_XeTap` (214) · `LichHoc` (13, chỉ 1 khóa) · `DM_MonHoc` (9) · `DM_HangDT_MonHoc` (320; cấu hình giờ của B/B.01/C1 đang NULL). `KySH` rỗng.

**Một bảng hai tầng, phân biệt bằng cờ:** `KhoaHoc_GiaoVien.IsKhoaHocGiaoVien` `1`=GV thuộc khóa (175 dòng, không ngày) · `0`=phân công (198 dòng: `NgayBD/NgayKT` datetime, `TenMonHoc`). `KhoaHoc_XeTap.IsKhoaHocXeTap` `1`=xe thuộc khóa (95 dòng, `MaGV` NULL) · `0`=ghép xe (119 dòng: `MaGV` + `BienSoXe` + `NgayBD/NgayKT` + `DiaDiem`). Không FK/UNIQUE giữa hai tầng; không CHECK, không trigger. `GhiChu` **NOT NULL** ở cả hai bảng. `KhoaHoc_GiaoVien.BienSoXe` và `SoHV` không bao giờ được điền; `KhoaHoc_XeTap.MaHV` trống 100%.

**Luật thời gian nằm ở SP, không ở schema:** `usp_CheckWarningLichLVGiaoVien` / `usp_CheckWarningLichLSDXeTap` (UI CDB gọi trước khi ghi): `bd < kt`; `bd > NgayKG(00:00)`; `kt < NgayBG + 23:59:59`; trùng = `NOT (kt <= bd_cũ OR bd >= kt_cũ)` trên datetime so với **mọi khóa kể cả cùng khóa** (dòng cờ=0, `TrangThai=1`, bỏ dòng đang sửa). `usp_CheckWarningGiaoVien/XeTap` chỉ cảnh báo GV/xe đang ở khóa chưa bế giảng. **SP Insert/Update không tự gọi các SP kiểm.**
- Dữ liệu thật: lịch GV 126/198 dòng `00:00→00:00` ("cả giai đoạn", 122 dòng kết thúc đúng 00:00 ngày bế giảng), 72 dòng có giờ (07:30–11:30, 13:30–17:30, 07:30–17:30; vài dòng phút lẻ do gõ tay); lịch xe 118/119 dòng `00:00`.
- Định dạng môn: trước 07/2026 `MaMonHoc`+tên (54 dòng); từ 29/07/2026 `MaMonHoc`=NULL, `TenMonHoc`=danh sách mã `"1,8"` (144 dòng).
- Loại GV (`LoaiHinh_DaoTao`, nhãn trong phần mềm CDB): `LT` Lý thuyết (1) · `TH` Thực hành (81) · `AL` Lý thuyết + Thực hành (5).

**SP an toàn để ghi:** `usp_KhoaHoc_GiaoVien_Insert` (cờ=1) · `usp_LichLV_KhoaHoc_GiaoVien_Insert/_Update` (cờ=0, tự lấy `TenGV`/`LoaiGV` từ `GiaoVien`, ghi `BienSoXe=''`) · `usp_KhoaHoc_XeTap_Insert` (cờ=1) · `LichSD_KhoaHoc_XeTap_Insert` / `usp_LichSD_KhoaHoc_XeTap_Update` (cờ=0) · xóa theo `MaLichLV`/`MaLichSD`: `usp_LLV_KhoaHoc_GiaoVien_Delete`, `usp_LSD_KhoaHoc_Xetap_Delete`.
**SP KHÔNG dùng (xóa lan):** `usp_KhoaHoc_GiaoVien_Delete`, `usp_KhoaHoc_XeTap_Delete` (xóa mọi dòng của (khóa, GV|xe) gồm lịch) · `usp_VoHieuLucKhoaHocGiaoVien/XeTap` (+`_TrongKhoaHoc`) (xóa danh sách ở **mọi khóa kể cả đã bế giảng**) · `usp_KhoaHoc_GiaoVien_Update` (đè mọi dòng của (khóa, GV), đè `NguoiTao/NgayTao`).

