# Rủi ro và giả định — Thu nhận hồ sơ học viên

**Ngày:** 30/09/2026 · **Người lập:** BA (Claude)

## 1. Pre-mortem

`[CHƯA LÀM]` — cỡ dự án **Vừa** chỉ chạy kiểm lỗ hổng vận hành (`09b`). Chạy pre-mortem khi nâng lên cỡ Lớn hoặc trước go-live chính thức.

## 2. Risk register

`[CHƯA LÀM]` — như trên. Rủi ro dự án lớn nhất đã nhận diện sơ bộ: (a) QR CCCD thực tế khác chuẩn giả định; (b) ghi nhầm DB production; (c) lộ PII trên VPS. Đã có biện pháp ở `09b`.

## 3. Sổ giả định

Phân loại theo **chi phí nếu sai**.

### Nền móng — sai thì phải làm lại kiến trúc / mô hình dữ liệu

```
AS-001  Giả định: Chuỗi QR CCCD gắn chip của học viên tại cơ sở đúng 7 trường
        phân tách bằng "|" (CCCD, CMND cũ, họ tên, ngày sinh ddMMyyyy, giới tính, nơi TT, ngày cấp).
        Nếu sai: khâu quét QR (BR-018) parse sai → phải chỉnh parser / thiết kế lại màn thu thập.
        Mức độ tin: CAO (định dạng đã xác nhận từ code chạy thật dự án webThanhdat, cùng ngành lái xe): 6 hoặc 7 trường tách "|" = CCCD(12) | [CMND cũ(9)] | Họ tên | Ngày sinh(ddMMyyyy) | Giới tính(Nam/Nữ) | Địa chỉ | Ngày cấp(ddMMyyyy). QR ở MẶT TRƯỚC CCCD gắn chip 2021+.
        Cách kiểm chứng: quét vài thẻ HV thật của cơ sở (xác nhận trên thiết bị thật) — không còn chặn thiết kế.
        Ai kiểm: NV thu nhận.
        Hạn: khi test app web.
        Trạng thái: ĐÃ XÁC NHẬN định dạng 30/09/2026 (tham khảo webThanhdat: lib qr-cccd/parse.ts). Chỉ còn test thẻ thật của cơ sở khi có app.

AS-002  Giả định: Ghép (tên tỉnh mới, tên xã mới) từ dataset vietnamadminunits về mã DB
        (DM_DVHC TrangThai=1) phủ 100% và ổn định.
        Nếu sai: map địa chỉ cũ→mới (BR-006) trật → sai NoiTT_MaDVHC/MaDVQL hàng loạt.
        Mức độ tin: Cao (đã verify 3321/3321 xã, 34/34 tỉnh ngày 30/09/2026).
        Cách kiểm chứng: chạy lại script đối soát mỗi khi DM_DVHC của DB thay đổi.
        Ai kiểm: dev.
        Hạn: trước khi dựng DM_DVHC_MAP + mỗi lần DB cập nhật DVHC.
        Trạng thái: Đã xác nhận (tại thời điểm 30/09/2026).

AS-003  Giả định: DB đích là GPLX_CSDT (DESKTOP-UBV2GQI), dùng đúng SP hiện có; nạp qua SP
        cho ra bản ghi app cũ hiển thị được.
        Nếu sai: toàn bộ khâu nạp phải thiết kế lại.
        Mức độ tin: Cao (đã xem DB thật + SP).
        Cách kiểm chứng: nạp thử 1 HV → mở app cũ kiểm.
        Ai kiểm: dev + chủ dự án.
        Hạn: Phase 1 build.
        Trạng thái: Đang kiểm (chờ nạp thử thật).
```

### Cấu trúc — sai thì phải sửa nhiều màn hình / luồng

```
AS-004  Giả định: MaLoaiHs suy theo hạng khóa: bắt đầu "A" → 1 (mô tô), B/C/D/E/F → 2 (ô tô).
        Nếu sai: sai loại hồ sơ + bộ giấy tờ.
        Mức độ tin: Vừa (khóa B đã xác nhận =2; mô tô chưa gặp ca thật).
        Cách kiểm chứng: nạp thử 1 HV mô tô → MaLoaiHs=1, giấy tờ đúng.
        Ai kiểm: chủ dự án.
        Hạn: trước khi mở luồng mô tô.
        Trạng thái: ĐÃ XÁC NHẬN 30/09/2026 — DB thật: khóa A* có MaLoaiHs=1 (20.393 HV), MaHTCap=CM_VN, giấy tờ 3 chuẩn (Đơn/CMND/sức khỏe). Quy tắc A*→1 chuẩn 100%.

AS-005  Giả định: MaHTCap = CM_VN cho mọi hồ sơ cấp mới người Việt Nam.
        Nếu sai: sai "Chọn in GPLX".
        Mức độ tin: Vừa (HV khóa B đều CM_VN).
        Cách kiểm chứng: hỏi chủ dự án các ca đặc biệt (người NN).
        Ai kiểm: chủ dự án.
        Hạn: trước go-live.
        Trạng thái: Chưa kiểm chứng.

AS-006  Giả định: Cần vai trò admin (quản tài khoản, cấu hình, xóa PII).
        Nếu sai: thừa/thiếu vai trò → sửa phân quyền.
        Mức độ tin: Vừa.
        Cách kiểm chứng: xác nhận với chủ dự án.
        Ai kiểm: chủ dự án.
        Hạn: trước khi làm module tài khoản.
        Trạng thái: Chưa kiểm chứng.

AS-007  Giả định: Tool nên kết nối DB bằng SQL login riêng (không dùng sa).
        Nếu sai (vẫn dùng sa): rủi ro an ninh (OG-004).
        Mức độ tin: Cao (khuyến nghị chuẩn).
        Cách kiểm chứng: tạo login hạn chế, tool chạy được.
        Ai kiểm: chủ dự án / IT.
        Hạn: trước go-live.
        Trạng thái: Chưa kiểm chứng.
```

### Chi tiết — sai thì sửa cục bộ

```
AS-008  Giả định: App web KHÔNG bắt buộc chế độ offline (có mạng khi thu thập).
        Nếu sai: cần thêm hàng đợi offline (EC-060).
        Mức tin: Thấp. Cách kiểm: hỏi NV thu nhận. Trạng thái: Chưa kiểm.

AS-009  Giả định: Nơi cấp CCCD mặc định = "Cục Cảnh sát QLHC về TTXH (Bộ Công an)".
        Nếu sai: sửa 1 trường mặc định. Mức tin: Vừa. Cách kiểm: hỏi chủ dự án. Trạng thái: Chưa kiểm.

AS-010  Giả định: Chưa có số HV/khóa và thời gian gõ/HV để định lượng ROI.
        Nếu sai: chỉ ảnh hưởng phần đo lường thành công. Mức tin: — . Cách kiểm: đo thực tế. Trạng thái: Chưa kiểm.

AS-011  Giả định: Xã bị chia (isDividedWard) chiếm tỷ lệ thấp trên HV thật.
        Nếu sai: nhiều ca phải chọn tay. Mức tin: Thấp. Cách kiểm: theo dõi khi chạy. Trạng thái: Chưa kiểm.

AS-012  Giả định: Ngày sinh mờ (chỉ năm) lưu yyyy0000 được app cũ chấp nhận.
        Nếu sai: sửa validate ngày sinh. Mức tin: Vừa (memory ghi cho phép). Cách kiểm: nạp thử. Trạng thái: Chưa kiểm.
```

**Quy tắc chặn:** không bắt đầu xây dựng khi còn giả định **Nền móng** (AS-001, AS-003) chưa kiểm chứng. AS-002 đã xác nhận.

## 4. Sẵn sàng vận hành

| Câu hỏi | Trả lời | Ai chịu |
|---|---|---|
| DB/VPS chết 2 tiếng thì làm gì? | Tool giữ staging đã kéo, xử lý tiếp; nạp lại khi DB lên (EC-061/062) | NV nạp DB |
| Ai được gọi khi sự cố? | `[CHƯA XÁC ĐỊNH]` | Chủ dự án |
| Biết hệ thống sai mà không ai báo? | Cảnh báo file mồ côi / nạp lỗi (OG-006, OG-024) — cần làm | Dev |
| Sửa dữ liệu sai bằng cách nào? | Tool (chưa BC1) hoặc app cũ; không sửa thẳng bảng (BR-001) | NV nạp DB |
| Sao lưu DB? | DB đã có `DUONG_DAN_SAO_LUU_CSDL` (app cũ) | Chủ dự án |
| Ai theo dõi chỉ số sau chạy? | `[CHƯA XÁC ĐỊNH]` | Chủ dự án |
| Chạy song song app cũ bao lâu? | App cũ vẫn dùng cho sát hạch/cấp GPLX (ngoài phạm vi) → song song lâu dài | Chủ dự án |
| Đối soát mới/cũ? | Mở app cũ kiểm hồ sơ vừa nạp (BR-001) | NV nạp DB |
