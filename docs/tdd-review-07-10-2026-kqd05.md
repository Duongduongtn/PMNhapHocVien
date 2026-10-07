# Biên bản review TDD — PMCSĐTLX (KQD-05 "Mở khóa để sửa sau kết xuất")

- **File review:** docs/TDD.md — §11D.7 "Mở khóa để sửa sau kết xuất (KQD-05)" + §11D.1 (sơ đồ máy trạng thái), phạm vi hẹp CHANGES #45
- **Ngày:** 07/10/2026
- **Đối chiếu:** PRD `[KQD-05]` (chương 🟣 Cập nhật kết quả đào tạo) · TDD-decisions §19 · CHANGES #45 · DB-GPLX_CDB_CSDT §5/§7 · **verify trực tiếp DB đích `GPLX_CDB_CSDT`** (bảng `TRANS_CLI_HangDoiGui`, `NguoiLX_HoSo`, SP `usp_TRANS_CLI_HangDoiGui_Delete`) · memory `project_pmcsdtlx_huy_ketxuat_kqdt`
- **Số phát hiện:** 3 (Chặn: 1 · Nên sửa: 2) — **tất cả đã xử lý, không mục nào bỏ qua hay hoãn**

## Đã sửa

| # | Điểm | Mức | Phát hiện | Đã sửa thế nào |
|---|---|---|---|---|
| ① | 1 (đối chiếu PRD) | **Chặn** | §11D.7 **xóa gói ở mức CƠ SỞ** (gói `KET_QUA_DAO_TAO` lọc theo `NoiGui=@MaCSDT`, không nối khóa) nhưng **lùi HV chỉ ở mức KHÓA** → HV `12` ở khóa khác (gói của họ cũng vừa bị xóa) treo "12 không còn gói", không bao giờ gửi, PM cũ cũng không kết xuất lại | **User chốt phương án A (lùi mức CƠ SỞ):** §11D.7 đổi bước lùi thành 1 `UPDATE WHERE MaCSDT=@MaCSDT AND TT_XuLy='12' AND KetLuanCSDT IS NOT NULL` (quét cả CSĐT, mọi khóa) cho khớp phạm vi xóa gói. Đồng bộ PRD `[KQD-05]` B-1a + decisions §19 (B/C) + mock modal (báo "cơ sở N người · M khóa") |
| ② | 3 (edge) | Nên sửa | `UPDATE` lùi 12→09/10 bằng `CASE KetLuanCSDT` không xử HV `12` mà `KetLuanCSDT` NULL (bất thường: đã kết xuất ắt có kết luận) → `CASE` rơi vào ELSE/NULL hoặc bị ép '10' oan | Thêm guard **`AND KetLuanCSDT IS NOT NULL`** vào `WHERE` → HV `12` không kết luận bị **bỏ qua + ghi cảnh báo**, không ép Không-đạt. (Gộp thẳng vào §11D.7, không tách bước riêng) |
| ③ | 6 (sơ đồ) | Nên sửa | §11D.1 sơ đồ máy trạng thái chưa vẽ **ngoại lệ `12 → 09/10`** của KQD-05 → đọc sơ đồ tưởng 12 luôn là ngõ cụt phía tool | §11D.1 thêm nhánh/ghi chú trong khung TOOL: `⟳ 12 → 09/10 (KQD-05, §11D.7)` khi cơ sở còn gói chưa gửi, kèm 1 dòng chú thích dưới sơ đồ "chỉ mở qua `POST /local/ketqua/mo-khoa`, mức CƠ SỞ" |

## Cố tình bỏ qua

(không có — cả 3 phát hiện đều đưa vào §11D.7 / §11D.1)

## Hoãn lại

(không có)

## Kết luận

**TDD §11D.7 đủ để code KQD-05 — 0 Chặn tồn sau khi áp phương án A.**

Hợp đồng kỹ thuật đã rõ cho cả 3 lớp: cổng B-1 (`EXISTS ... NoiGui=@MaCSDT AND TrangThai='0'`), hành vi mở khóa mức cơ sở (xóa gói qua `usp_TRANS_CLI_HangDoiGui_Delete` + `UPDATE` lùi 12→09/10 có guard NULL), và ca khóa cứng M1 (409 + thông báo mức đợt). `13` khóa tuyệt đối. Code bám mock `ui-mock/theodoiketxuat.html`, nối vào khung `routers/ketqua.py` của phần KQĐT chưa commit.

## Dữ kiện verify DB (tham chiếu khi code)

- `TRANS_CLI_HangDoiGui`: cột `NoiGui` = mã CSĐT chuẩn (gói 75032 có `NoiGui='75032'`), `TrangThai` `0`=chưa gửi/`1`=đã gửi, `KieuDuLieu='KET_QUA_DAO_TAO'`. Tên gói chỉ chứa timestamp (`KQDT_<CSDT>_<MaSoGTVT>_K<timestamp>.zip`), **không** nối MaKH/MaDK; không bảng junction; `Transfer_flag=0` toàn bộ → không truy được HV↔gói.
- `usp_TRANS_CLI_HangDoiGui_Delete(@Id)` = `DELETE WHERE Id=@Id` (xóa 1 gói/lần).
- `NguoiLX_HoSo`: `TT_XuLy` `12`=đã kết xuất gửi Sở, `KetLuanCSDT` (`1`/`0`/NULL), `NgaySua`. SP `_CapNhat` **không bảo vệ `12`** → luồng mở khóa dùng `UPDATE` tham số hóa trực tiếp (không gọi `_CapNhat`), guard `KetLuanCSDT IS NOT NULL`.
- Dữ liệu lẫn máy: hiện 61 gói `TrangThai='0'` của CSĐT 24005 (`NguoiTao='ADMIN'`) → **bắt buộc lọc `NoiGui=@MaCSDT`**, không parse tên file.
