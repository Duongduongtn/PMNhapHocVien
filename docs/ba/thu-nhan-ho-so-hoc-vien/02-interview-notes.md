# Ghi chép phỏng vấn thô — Thu nhận hồ sơ học viên

**Ngày:** 30/09/2026 · **Người lập:** BA (Claude) · **Chế độ:** 1 nguồn tin (chủ dự án/vận hành) + quan sát trực tiếp DB & UI

> Ghi chép nguyên trạng. Diễn giải nằm ở `03-findings.md`.

## Nguồn dữ kiện

- **Chủ dự án / người vận hành CSDT 70004** — trả lời trực tiếp trong hội thoại.
- **DB thật `GPLX_CSDT`** (DESKTOP-UBV2GQI/sa) — truy vấn chỉ đọc (READ UNCOMMITTED). Độ tin cậy **Cao**.
- **Ảnh `UI.png`** — màn "Thu nhận Hồ sơ cấp mới" của app desktop cũ. Độ tin cậy **Cao**.
- **Script `DBcu/DBcu30092026.sql`** — schema + SP.

## Hỏi đáp (8 câu chốt)

1. **Trùng học viên** → chặn trùng CCCD trong CÙNG khóa (cảnh báo), cho phép ở khóa khác.
2. **Người dùng/phân quyền** → Nhân viên thu nhận (app web, nhiều người) + Nhân viên nạp DB (tool, ít người), cả hai đăng nhập riêng; không có khâu duyệt riêng.
3. **Phạm vi sửa của tool** → B: tool là app quản lý đầy đủ (tra cứu + sửa hồ sơ đã có trong DB), tái dùng tối đa SP có sẵn.
4. **Phạm vi MVP** → A: Nạp mới + tra cứu/sửa cơ bản (lưới theo khóa, tìm, mở sửa thông tin/ảnh, đổi khóa, xóa). Báo cáo/kết xuất để sau.
5. **Điều kiện nạp** → B: chỉ cảnh báo mềm, cho nạp tất (như app cũ). Ràng buộc NOT NULL tự chặn ca thiếu trường lõi.
6. **Giữ PII trên VPS** → B: giữ ~30 ngày rồi tự xóa, kèm bộ lọc cho user xóa thủ công.
7. **Trường tạo khóa học** → A: 5 bắt buộc (Hạng ĐT, Tên khóa, Ngày KG, Ngày BG, Tổng số HV) + 4 tùy chọn (Số QĐ, Ngày QĐ, Ngày thi, Ghi chú). Tool tạo khóa qua `usp_KhoaHoc_Insert`.
8. **Ảnh thẻ CCCD** → A: chỉ cắt ảnh chân dung, không OCR; dữ liệu nhập tay.

## Yêu cầu bổ sung nêu rải rác trong hội thoại

- App web **responsive** (mobile + desktop): mobile quét QR + chụp ảnh; desktop nhập liệu, thêm ảnh sau.
- Tool máy tính kéo dữ liệu từ VPS về; **thay được ảnh**; căn khung + xóa phông → nền trắng; xuất `.jp2`.
- **Cả app web và tool đều cho sửa dữ liệu** (trước khi nạp).
- Nạp phải **trung thực**: mở app cũ (`UI.png`) lên thấy y như tự nhập.
- Địa chỉ: cho nhập **cũ hoặc mới**, tự đổi sang mới (Option B — nạp bảng ánh xạ chính thức).
- **Nơi cư trú mặc định = Nơi thường trú.**
- Nhập cả **mô tô (A*) và ô tô (B/C/D/E/F)**.
- **Đổi khóa**: cùng hạng → di chuyển file ảnh sang folder khóa mới, đổi `DuongDanAnh`, giữ tên file, sinh lại Số hồ sơ; khác hạng → nên xóa tạo lại.
- **Tuyệt đối dùng SP/hàm có sẵn của DB**, không INSERT/UPDATE tay.

## Quan sát trực tiếp DB (độ tin cậy Cao) — trích

- `SoHoSo` = số thứ tự 3 chữ số/khóa (`001..055`), app tự sinh MAX+1 (không dùng UDF `CreateNewSoHoso`).
- `MaDK` = `70004-<yyyyMMddHHmmssfff>` do `CreateNewMaDK` sinh.
- Khóa mẫu `70004K26B010`: MaCSDT=70004, MaSoGTVT=70, HangGPLX=B1, HangDT=B, TongSoHV=50, đang có 55 HV (VƯỢT sĩ số → app cho vượt).
- HV ô tô B: MaLoaiHs=2, MaHTCap=CM_VN, TT_XuLy=03, Transfer_flag=0, GiayCNSK=1, ChatLuongAnh=1.
- Giấy tờ hạng B (MaLoaiHs=2): MaGT 1,2,3; TenGT lấy đầy đủ từ `DM_GiayTo`; TrangThai=1.
- DVHC mới = 2 cấp: Tỉnh (`MaDVQL`, 34) → Xã (`MaDvhc`, TrangThai=1, 3.321); `(MaDVQL,TenNganGon)` duy nhất 100%.
- Config `QTHT_ThamSoHT`: IMG_PATH_CSDT=`D:\GPLXCSDT\ANHCDUNG`, MA_CSDT=70004.
- Bộ SP đầy đủ: Insert/Update/Delete/Search/Select cho NguoiLX, HoSo, GiayTo, KhoaHoc, DM_DVHC; có `usp_DM_DVHC_SelectAll_Tinh`, `usp_DM_DVHC_SelectDanhSachXaPhuongTheoTinh`, `usp_QuangLA_PM4_ThuNhanHS_*` (SP của chính màn thu nhận HS cũ).
- Tạo khóa: `usp_KhoaHoc_Insert` + `CreateNewMaKhoaHoc`; hạng đào tạo lấy từ `DM_HangDT` (32 hạng, kèm TuoiHV + ThoiGianDaoTao).
