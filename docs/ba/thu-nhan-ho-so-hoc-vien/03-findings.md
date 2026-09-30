# Phát hiện từ phỏng vấn — Thu nhận hồ sơ học viên

**Ngày:** 30/09/2026 · **Người lập:** BA (Claude)

## Nguồn tin

| Người | Vai trò | Ngày | Thời lượng | Chế độ |
|---|---|---|---|---|
| Chủ dự án | Vận hành CSDT 70004 (chủ + người dùng) | 30/09/2026 | phiên chat | **1 nguồn tin** |
| DB `GPLX_CSDT` | Hệ thống thật | 30/09/2026 | truy vấn chỉ đọc | Quan sát trực tiếp |
| `UI.png` | Tài liệu (màn app cũ) | 30/09/2026 | — | Quan sát trực tiếp |

> Điều **chủ dự án nói** về quy trình → độ tin cậy **Thấp** (1 nguồn). Điều **quan sát từ DB/UI/script** → độ tin cậy **Cao**.

---

## Chủ đề

### CĐ-01 — Nạp phải trung thực với app cũ
| | |
|---|---|
| **Bằng chứng** | > "nạp vô DB rồi mở UI này lên thì hiển thị được dữ liệu học viên như thể tôi dùng UI này làm vậy" |
| **Tần suất** | chỉ 1 nguồn |
| **Mâu thuẫn** | chưa đối chiếu được |
| **Hệ quả** | Toàn bộ trường + Số hồ sơ + giấy tờ + ảnh phải sinh y app cũ. Gọi SP có sẵn, không INSERT tay → BR-nhóm nạp |
| **Độ tin cậy** | Cao (đã đối chiếu cấu trúc DB thật) |

### CĐ-02 — Số hồ sơ là số thứ tự 3 chữ số theo khóa
| | |
|---|---|
| **Bằng chứng** | DB: `SoHoSo` trong khóa `70004K26B010` = `001..055`, ô mới trên UI = `056` |
| **Tần suất** | quan sát trực tiếp |
| **Mâu thuẫn** | Khác hàm `CreateNewSoHoso` trong script (sinh `B01`) → app override |
| **Hệ quả** | Tool sinh `SoHoSo = RIGHT('000'+MAX+1,3)` theo khóa → BR-002 |
| **Độ tin cậy** | Cao |

### CĐ-03 — Địa chỉ: nhập cũ/mới, tự đổi sang mới
| | |
|---|---|
| **Bằng chứng** | > "cho phép nhập địa chỉ mới hoặc địa chỉ cũ rồi tự map đổi theo địa chỉ mới"; > "Tỉnh Đồng Nai đã đổi thành Thành Phố Đồng Nai" (DB là chuẩn tên) |
| **Tần suất** | chỉ 1 nguồn (yêu cầu) + quan sát DB (cơ chế) |
| **Mâu thuẫn** | chưa đối chiếu được |
| **Hệ quả** | Bảng phụ `DM_DVHC_MAP` (nguồn `vietnamadminunits`, phủ 100%); nối theo tên về mã DB; xã bị chia → chọn tay → BR + EC |
| **Độ tin cậy** | Cao (đã verify phủ 3321/3321) |

### CĐ-04 — Nơi cư trú mặc định = Nơi thường trú
| | |
|---|---|
| **Bằng chứng** | > "Nơi thường trú và Nơi cư trú mặc định như nhau nha" |
| **Tần suất** | chỉ 1 nguồn |
| **Hệ quả** | Tool tự sao `NoiCT*` = `NoiTT*`, cho bỏ tick nếu khác → BR-004 |
| **Độ tin cậy** | Thấp (lời user, nhưng rõ ràng) |

### CĐ-05 — Chặn trùng CCCD trong cùng khóa
| | |
|---|---|
| **Bằng chứng** | Câu 1 = A |
| **Tần suất** | chỉ 1 nguồn |
| **Hệ quả** | Trước nạp: cảnh báo nếu CCCD đã có trong khóa đang chọn; cho phép ở khóa khác → BR-005 + EC |
| **Độ tin cậy** | Thấp |

### CĐ-06 — Vai trò & phân quyền
| | |
|---|---|
| **Bằng chứng** | Câu 2 = A |
| **Hệ quả** | Vai trò: Nhân viên thu nhận (app web) · Nhân viên nạp DB (tool) · (Quản trị). Đăng nhập riêng, tài khoản của hệ thống này → Pha 4 |
| **Độ tin cậy** | Thấp |

### CĐ-07 — Tool là app quản lý học viên đầy đủ (scope B)
| | |
|---|---|
| **Bằng chứng** | > "B nhưng bạn đề xuất chức năng và phải nghiên cứu các schema procedure usp" |
| **Hệ quả** | Tool tra cứu + sửa hồ sơ có sẵn trong DB, tái dùng SP: `usp_NguoiLX_Select_By_MaKH`, `_HoSo_Search`, `_Get_Sua_HS`, `_Update`, `_Delete`... → CAP nhiều |
| **Độ tin cậy** | Cao (SP đã kiểm kê) |

### CĐ-08 — Tạo khóa học trong tool
| | |
|---|---|
| **Bằng chứng** | > "có thêm chức năng tạo khóa học và tuyệt đối tuân thủ hàm đang có ở DB" |
| **Hệ quả** | UI tạo khóa 5 trường bắt buộc + 4 tùy chọn; gọi `usp_KhoaHoc_Insert`; hạng từ `DM_HangDT` → CAP + BR |
| **Độ tin cậy** | Cao (SP + DM_HangDT đã kiểm) |

### CĐ-09 — Ảnh: điện thoại chụp thô, tool xử lý
| | |
|---|---|
| **Bằng chứng** | > "điện thoại chỉ chụp ảnh chân dung chưa cần xóa phông"; ảnh thẻ chỉ cắt chân dung, không OCR (Câu 8=A) |
| **Hệ quả** | Tool: căn khung + xóa phông trắng + xuất `.jp2` (480×640); file `<IMG_PATH>\<MaKhoaHoc>\70004-<timestamp>.jp2`; DB lưu `DuongDanAnh` → BR + CAP |
| **Độ tin cậy** | Cao (chuẩn ảnh verify từ file thật) |

### CĐ-10 — Quét QR có phản hồi + màn xác nhận
| | |
|---|---|
| **Bằng chứng** | > "lúc quét QR căn cước phải có hiệu ứng là quét được và hiển thị các trường dữ liệu đã lấy được để người dùng xác nhận" |
| **Hệ quả** | App web: hiệu ứng quét thành công + màn preview 7 trường QR để xác nhận/sửa trước khi lưu → CAP + BR |
| **Độ tin cậy** | Thấp (yêu cầu UX của user) |

### CĐ-11 — Điều kiện nạp mềm + giữ PII 30 ngày
| | |
|---|---|
| **Bằng chứng** | Câu 5=B (chỉ cảnh báo, cho nạp tất); Câu 6=B (VPS giữ 30 ngày + bộ lọc xóa thủ công/tự động) |
| **Hệ quả** | Không chặn cứng (trừ NOT NULL); VPS auto-xóa sau 30 ngày + màn lọc để xóa tay → BR + EC (PII) |
| **Độ tin cậy** | Thấp |

### CĐ-12 — Đổi khóa & vòng đời ảnh
| | |
|---|---|
| **Bằng chứng** | Câu về đổi khóa = "Di chuyển file sang folder khóa mới"; DB không tự đụng file |
| **Hệ quả** | Đổi khóa cùng hạng: `usp_NguoiLX_HoSo_Update` đổi MaKhoaHoc + di chuyển `.jp2` + đổi `DuongDanAnh` + giữ tên file + sinh lại SoHoSo. Khác hạng: xóa tạo lại. Xóa HV: xóa mềm ảnh vào `_DELETED` → BR + EC |
| **Độ tin cậy** | Cao (FK + SP đã kiểm) |

---

## Ba tín hiệu quy trình thật khác quy trình chính thức

| # | Tín hiệu | Bắt được ở đâu | Quy tắc ẩn phía sau | Đã truy chưa |
|---|---|---|---|---|
| 1 | "chính thức thì… nhưng thực tế thì…" | Sĩ số: TongSoHV=50 nhưng thực có 55 HV | App **cho phép vượt sĩ số khóa** — không chặn cứng | Rồi (BR-soft) |
| 2 | File/bảng sống ngoài hệ thống | Ảnh `.jp2` sống ở filesystem, DB chỉ giữ path | Vòng đời file ảnh do app quản, DB không cascade file | Rồi (CĐ-12) |
| 3 | Cùng vai trò mô tả 1 bước khác nhau | — (1 nguồn tin, chưa đối chiếu) | — | Chưa (cần nhiều người) |

## Mâu thuẫn chưa giải quyết

| # | Vấn đề | Phía A | Phía B | Ai quyết | Chặn |
|---|---|---|---|---|---|
| — | Chưa có (1 nguồn tin) | | | | |

## Phải hỏi người khác

| # | Câu hỏi | Vai trò cần hỏi | Chặn cái gì | Đã hỏi chưa |
|---|---|---|---|---|
| 1 | Định dạng chuỗi QR CCCD thực tế của cơ sở | Test thẻ thật của HV | Parse QR (Pha 3, build) | Chưa |
| 2 | Số HV/khóa + thời gian gõ tay/HV hiện tại | Nhân viên thu nhận thực tế | Định lượng ROI (mục 5 problem-statement) | Chưa |
| 3 | Nhân viên thu nhận có làm việc offline (mất mạng) không | Nhân viên thu nhận | Có cần chế độ offline PWA không | Chưa |
| 4 | Có phân biệt quyền giữa các nhân viên thu nhận không (ai xem HV của ai) | Quản lý CSDT | Chi tiết Pha 4 | Chưa |

## Quy tắc chưa xác thực (→ chuyển vào `10-assumptions.md`)

| # | Điều nghe/suy | Nguồn | Vì sao chưa chắc | Cách kiểm |
|---|---|---|---|---|
| 1 | QR CCCD chip đúng 7 trường phân tách `\|` | Chuẩn chung, chưa test thẻ cơ sở | Chưa test thẻ thật | Quét vài thẻ HV |
| 2 | MaLoaiHs suy theo hạng khóa (A*→1 mô tô, B/C/D/E/F→2 ô tô) | Suy từ dữ liệu | Chưa gặp ca nâng hạng (loại 3) | Kiểm khi có ca nâng hạng |
| 3 | Nơi cấp CCCD = "Cục CS QLHC (Bộ Công an)" mặc định | Suy luận | QR không có trường này | Xác nhận với user |
| 4 | Xã bị chia (isDividedWard) tần suất thấp | Dataset | Chưa đo trên HV thật của cơ sở | Theo dõi khi chạy |

## Điều kiện dừng phỏng vấn

- [x] 3 câu gần nhất (6,7,8) không sinh thêm **quy tắc lõi** mới (chỉ tinh chỉnh scope/UX)
- [x] 3 câu gần nhất không sinh thêm **edge case lõi** mới
- [x] Mọi bước as-is đều mô tả được (qua UI.png + DB + user)
- [x] Mọi trạng thái kết thúc (nạp thành công / trùng / thiếu ảnh / vượt sĩ số) đều được nhắc

→ **Đủ điều kiện dừng Pha 2.** Các câu còn hở là chi tiết build (QR thật) + định lượng, đã đưa vào "Phải hỏi người khác".
