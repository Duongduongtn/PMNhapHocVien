# Edge case — Thu nhận hồ sơ học viên

**Ngày:** 30/09/2026 · **Người lập:** BA (Claude)

Luồng: **F1 = Thu thập (app web)** · **F2 = Nạp DB + quản lý (tool)**.

## Bảng đối chiếu 8 trục

| Luồng | T1 Vòng đời | T2 Đồng thời | T3 Hoàn tác | T4 Dữ liệu | T5 Thời gian | T6 Phân quyền | T7 Hệ thống ngoài | T8 Quy mô |
|---|---|---|---|---|---|---|---|---|
| F1 Thu thập | EC-001 | EC-012 | EC-020 | EC-030, EC-031, EC-033 | EC-041 | EC-050 | EC-060 | EC-070 |
| F2 Nạp DB | EC-002, EC-003 | EC-010, EC-011 | EC-021, EC-022 | EC-032 | EC-040 | EC-051 | EC-061, EC-062 | EC-071 |

Mỗi luồng đều có ≥1 ca ở T2, T3, T4, T7. ✅

## Danh sách edge case

### Trục 1 — Vòng đời

```
EC-001  App web điền 80% rồi đóng tab / mất pin trước khi gửi VPS.
        Trục: T1 · Luồng/bước: F1, bước C-F
        Mong đợi: Giữ nháp cục bộ (localStorage) trạng thái draft; mở lại app tiếp tục được.
        Nghiệm thu: Điền dở, đóng tab, mở lại → dữ liệu còn.
        Mức: Trung bình
        Nguồn: suy luận T1
        Đường vòng: Nhập lại từ đầu nếu chưa làm.

EC-002  Bản ghi kẹt importing khi tool tắt/đơ giữa lúc nạp.
        Trục: T1 · Luồng/bước: F2, bước importing
        Mong đợi: Có timeout/cờ mở khóa; bản ghi tự trả về pending sau X phút hoặc admin mở khóa.
        Nghiệm thu: Tắt tool khi đang nạp → sau timeout bản ghi về pending, nạp lại được.
        Mức: Cao
        Nguồn: suy luận T1/T7
        Đường vòng: Admin sửa trạng thái tay.

EC-003  Bản ghi imported bị kéo/nạp lại lần 2.
        Trục: T1 · Luồng/bước: F2
        Mong đợi: Chặn — bản ghi da_nap không xuất hiện trong hàng đợi; nếu ép nạp, kiểm MaDK đã có → từ chối.
        Nghiệm thu: Nạp 1 bản ghi 2 lần → chỉ 1 HV trong DB.
        Mức: Chặn
        Nguồn: BR-015
        Đường vòng: —
```

### Trục 2 — Đồng thời

```
EC-010  Hai tool (2 máy) cùng kéo & nạp một bản ghi pending.
        Trục: T2 · Luồng/bước: F2, importing
        Mong đợi: Khóa bản ghi khi chuyển importing (optimistic/lock trên VPS); tool thứ 2 báo "đang được nạp".
        Nghiệm thu: 2 tool cùng nạp 1 bản ghi → chỉ 1 HV tạo ra.
        Mức: Chặn
        Nguồn: suy luận T2
        Đường vòng: Quy ước chỉ 1 máy nạp (nếu chưa làm khóa).

EC-011  Hai HV nạp gần như đồng thời cùng khóa → tranh Số hồ sơ (SoHoSo).
        Trục: T2 · Luồng/bước: F2, bước S (sinh SoHoSo)
        Mong đợi: Sinh SoHoSo trong transaction có khóa; nếu trùng PK → retry MAX+1. Không tạo 2 SoHoSo giống nhau.
        Nghiệm thu: Nạp lô 10 HV cùng khóa → SoHoSo liên tục, không trùng.
        Mức: Chặn
        Nguồn: BR-002 + suy luận T2
        Đường vòng: Nạp tuần tự từng HV.

EC-012  Hai NV thu nhận gửi cùng một CCCD cho cùng khóa.
        Trục: T2 · Luồng/bước: F1→F2
        Mong đợi: Bước nạp phát hiện trùng CCCD trong khóa (BR-005) → cảnh báo, chỉ nạp 1.
        Nghiệm thu: Gửi 2 bản ghi cùng CCCD cùng khóa → khi nạp cái thứ 2 bị cảnh báo trùng.
        Mức: Cao
        Nguồn: BR-005
        Đường vòng: NV nạp DB kiểm mắt.
```

### Trục 3 — Hoàn tác / bù trừ

```
EC-020  Mất mạng/hủy giữa lúc app web đang gửi bản ghi lên VPS.
        Trục: T3 · Luồng/bước: F1, bước G
        Mong đợi: Gửi idempotent theo UUID; gửi lại không tạo 2 bản ghi trên VPS.
        Nghiệm thu: Ngắt mạng giữa lúc gửi, gửi lại → VPS chỉ có 1 bản ghi UUID đó.
        Mức: Cao
        Nguồn: BR-015 + suy luận T3
        Đường vòng: Kiểm hàng đợi VPS thủ công.

EC-021  Xóa HV vừa nạp nhầm (cùng ảnh .jp2).
        Trục: T3 · Luồng/bước: F2, xóa HV
        Mong đợi: usp_NguoiLX_Delete (cascade) + chuyển file .jp2 sang _DELETED (xóa mềm, BR-014).
        Nghiệm thu: Xóa HV → 3 bảng sạch, file ở _DELETED, còn khôi phục được.
        Mức: Cao
        Nguồn: BR-014
        Đường vòng: —

EC-022  File .jp2 đã ghi ổ D nhưng SP nạp DB lỗi → file mồ côi.
        Trục: T3 · Luồng/bước: F2, bước S-T
        Mong đợi: Ghi file sau khi SP thành công (hoặc dọn file nếu transaction fail). Không để file trỏ tới HV không tồn tại.
        Nghiệm thu: Ép SP lỗi sau khi ghi file → file bị dọn, không còn mồ côi.
        Mức: Cao
        Nguồn: suy luận T3
        Đường vòng: Dọn file rác định kỳ.
```

### Trục 4 — Dữ liệu biên / bẩn

```
EC-030  Họ tên quá dài hoặc ký tự lạ vượt giới hạn cột.
        Trục: T4 · Luồng/bước: F1/F2
        Mong đợi: Validate độ dài theo cột: HoVaTen ≤50, HoDemNLX ≤30, TenNLX ≤20, HoVaTenIn ≤25 (nvarchar). Cắt/cảnh báo trước khi nạp, giữ dấu tiếng Việt (UTF-8/Unicode).
        Nghiệm thu: Nhập tên 60 ký tự → chặn/cảnh báo, không lỗi SP; tên có dấu lưu đúng.
        Mức: Cao
        Nguồn: DB thật (độ dài cột)
        Đường vòng: —

EC-031  Ngày sinh mờ trên CCCD (chỉ có năm) hoặc QR trả sai định dạng.
        Trục: T4 · Luồng/bước: F1
        Mong đợi: NgaySinh lưu varchar(8) yyyymmdd; cho phép yyyy0000 nếu chỉ có năm; QR ddMMyyyy → đổi đúng.
        Nghiệm thu: CCCD chỉ ghi năm 1985 → lưu 19850000, app cũ hiển thị được.
        Mức: Trung bình
        Nguồn: DB thật (NgaySinh varchar8) + memory
        Đường vòng: Nhập tay.

EC-032  Địa chỉ cũ không có trong DM_DVHC_MAP hoặc xã bị chia.
        Trục: T4 · Luồng/bước: F2, bước N
        Mong đợi: Cho người dùng chọn tay Tỉnh/Xã mới từ DM_DVHC (TrangThai=1); không tự đoán bừa.
        Nghiệm thu: Nhập địa chỉ không map được → hiện popup chọn tay, chọn xong lưu đúng mã.
        Mức: Cao
        Nguồn: BR-006 + verify (isDividedWard)
        Đường vòng: Chọn tay.

EC-033  Số CCCD sai độ dài / trùng số CMND cũ / để trống.
        Trục: T4 · Luồng/bước: F1
        Mong đợi: Cảnh báo nếu CCCD ≠ 12 số; SoCMT bắt buộc (NOT NULL), CMND cũ cho trống.
        Nghiệm thu: Nhập CCCD 10 số → cảnh báo; bỏ trống SoCMT → chặn nạp.
        Mức: Trung bình
        Nguồn: DB thật (SoCMT NOT NULL)
        Đường vòng: Nhập tay đúng.
```

### Trục 5 — Thời gian

```
EC-040  Bản ghi pending quá 30 ngày đúng lúc đang nạp (importing).
        Trục: T5 · Luồng/bước: F2 + job VPS
        Mong đợi: Job xóa PII bỏ qua bản ghi importing/imported chưa quá hạn; không xóa giữa lúc nạp.
        Nghiệm thu: Đặt bản ghi 30 ngày + importing → job không xóa.
        Mức: Cao
        Nguồn: BR-016 + suy luận T5
        Đường vòng: Tạm dừng job khi nạp.

EC-041  Học viên chưa đủ tuổi tối thiểu / ngày sinh tương lai.
        Trục: T5 · Luồng/bước: F1/F2
        Mong đợi: Cảnh báo mềm (BR-011) khi tuổi < TuoiHV của hạng; vẫn cho nạp (app cũ cho).
        Nghiệm thu: HV 17 tuổi hạng B (yêu cầu 18) → cảnh báo, vẫn nạp được.
        Mức: Trung bình
        Nguồn: BR-011 + DM_HangDT.TuoiHV
        Đường vòng: NV tự kiểm.
```

### Trục 6 — Phân quyền

```
EC-050  NV thu nhận cố gọi chức năng nạp DB.
        Trục: T6 · Luồng/bước: F1
        Mong đợi: Backend chặn theo vai trò (collector không có quyền nạp); không lộ API nạp cho app web.
        Nghiệm thu: Đăng nhập collector gọi API nạp → 403.
        Mức: Cao
        Nguồn: BR-020 + ma trận quyền
        Đường vòng: —

EC-051  Sửa/đổi khóa hồ sơ thuộc khóa đã lập BC1.
        Trục: T6 · Luồng/bước: F2
        Mong đợi: Chặn sửa qua tool (BR-012); hướng dùng app cũ; báo rõ lý do "khóa đã báo cáo".
        Nghiệm thu: Mở sửa HV khóa đã BC1 → tool chặn, báo lý do.
        Mức: Cao
        Nguồn: BR-012
        Đường vòng: Dùng app cũ.
```

### Trục 7 — Hệ thống ngoài thất bại

```
EC-060  Mất mạng khi app web gửi VPS.
        Trục: T7 · Luồng/bước: F1, bước G
        Mong đợi: Giữ nháp, hàng đợi gửi lại tự động khi có mạng; idempotent theo UUID (EC-020).
        Nghiệm thu: Tắt mạng khi gửi → app báo "sẽ gửi lại"; có mạng → tự gửi, không trùng.
        Mức: Cao
        Nguồn: suy luận T7 (câu hỏi offline còn treo — Pha 2)
        Đường vòng: Gửi lại tay.

EC-061  Tool mất kết nối SQL Server giữa lúc nạp.
        Trục: T7 · Luồng/bước: F2, bước S
        Mong đợi: Transaction trong SP rollback; bản ghi giữ pending; tool báo lỗi rõ, cho thử lại.
        Nghiệm thu: Ngắt DB khi nạp → không có HV nửa vời, bản ghi vẫn pending.
        Mức: Chặn
        Nguồn: suy luận T7 + BR-001
        Đường vòng: Thử lại khi có DB.

EC-062  VPS/tunnel down khi tool kéo dữ liệu.
        Trục: T7 · Luồng/bước: F2, bước K
        Mong đợi: Tool làm việc trên staging đã kéo (SQLite cục bộ); báo VPS lỗi, thử lại; không mất dữ liệu đã kéo.
        Nghiệm thu: Tắt VPS → tool vẫn mở, xử lý bản ghi đã kéo; kéo mới thì báo lỗi.
        Mức: Cao
        Nguồn: suy luận T7
        Đường vòng: Chờ VPS lên.
```

### Trục 8 — Quy mô

```
EC-070  Đầu khóa 50+ học viên gửi dồn lên VPS trong thời gian ngắn.
        Trục: T8 · Luồng/bước: F1
        Mong đợi: Backend chịu tải hàng đợi; ảnh thô nén hợp lý; không mất bản ghi.
        Nghiệm thu: Gửi 60 bản ghi liên tục → VPS nhận đủ.
        Mức: Trung bình
        Nguồn: suy luận T8 (điểm đau nghẽn đầu khóa)
        Đường vòng: Gửi rải.

EC-071  Nạp hàng loạt (tick 50 HV) một lần.
        Trục: T8 · Luồng/bước: F2, bước R-W
        Mong đợi: Nạp tuần tự, hiện tiến độ; lỗi 1 HV không làm hỏng cả lô, HV lỗi giữ pending + báo dòng lỗi.
        Nghiệm thu: Nạp 50 HV, ép 1 HV lỗi → 49 vào DB, 1 giữ pending có thông báo.
        Mức: Cao
        Nguồn: suy luận T8
        Đường vòng: Nạp từng HV.
```

## Thống kê

| Mức | Số ca | Đã có AC | Chưa có AC |
|---|---:|---:|---:|
| Chặn | 4 (EC-003, 010, 011, 061) | 4 | 0 |
| Cao | 13 | 13 | 0 |
| Trung bình | 5 | 5 | 0 |
| Thấp | 0 | 0 | 0 |

Cột "Chưa có AC" của mức Chặn & Cao = 0. ✅

## Trục không áp dụng

| Luồng | Trục | Lý do |
|---|---|---|
| F1/F2 | — | Tất cả 8 trục đều có ít nhất 1 ca; không trục nào bỏ trống |
