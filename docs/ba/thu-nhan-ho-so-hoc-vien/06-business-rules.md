# Quy tắc nghiệp vụ — Thu nhận hồ sơ học viên

**Ngày:** 30/09/2026 · **Người lập:** BA (Claude)

> Nguồn "DB thật" / "UI.png" = quan sát trực tiếp (tin cậy cao). Nguồn "chủ dự án" = 1 nguồn tin. `[GIẢ ĐỊNH]` → `10-assumptions.md`.

---

## Danh sách

### BR-001 — Nạp trung thực qua SP có sẵn
| | |
|---|---|
| **Quy tắc** | Mọi thao tác ghi DB phải gọi stored procedure có sẵn (`usp_NguoiLX_Insert`, `usp_NguoiLX_HoSo_Insert`, `usp_NguoiLXHS_GiayTo_Insert`, `usp_KhoaHoc_Insert`, `usp_*_Update`, `usp_*_Delete`). TUYỆT ĐỐI không INSERT/UPDATE/DELETE bảng trực tiếp. |
| **Nguồn** | Chủ dự án ("tuyệt đối tuân thủ hàm đang có ở DB") + DB thật |
| **Loại** | Chính sách nội bộ |
| **Áp dụng tại** | Mọi bước ghi DB ở luồng to-be |
| **Đối tượng** | NguoiLX, NguoiLX_HoSo, NguoiLXHS_GiayTo, KhoaHoc |
| **Cách kiểm chứng** | Nạp 1 HV → mở app cũ (`UI.png`) → hiển thị đầy đủ y như tự nhập |
| **Ngoại lệ** | Không |

### BR-002 — Số hồ sơ = số thứ tự 3 chữ số theo khóa
| | |
|---|---|
| **Quy tắc** | `SoHoSo` sinh = `RIGHT('000' + CAST(MAX(SoHoSo trong cùng MaKhoaHoc)+1 AS varchar), 3)`. KHÔNG dùng UDF `CreateNewSoHoso`. |
| **Nguồn** | DB thật (khóa `70004K26B010`: 001..055; ô mới UI=056) |
| **Loại** | Ràng buộc vận hành |
| **Áp dụng tại** | Bước nạp HV (T-NAP) |
| **Đối tượng** | NguoiLX_HoSo |
| **Cách kiểm chứng** | Khóa đang có 55 HV → nạp thêm → SoHoSo = 056 |
| **Ngoại lệ** | Khi nạp nhiều HV cùng lúc phải khóa tuần tự (xem EC concurrency) |

### BR-003 — Mã đăng ký MaDK do DB sinh theo timestamp
| | |
|---|---|
| **Quy tắc** | `MaDK` = `70004-<yyyyMMddHHmmssfff>`, để `usp_NguoiLX_Insert` tự sinh (`CreateNewMaDK`) khi truyền NULL. MaDK là định danh, không mang nghĩa ngày nhận. |
| **Nguồn** | DB thật + script |
| **Loại** | Ràng buộc vận hành |
| **Áp dụng tại** | T-NAP |
| **Đối tượng** | NguoiLX |
| **Cách kiểm chứng** | Nạp 2 HV liên tiếp → 2 MaDK khác nhau theo mili-giây |
| **Ngoại lệ** | Không |

### BR-004 — Nơi cư trú mặc định bằng nơi thường trú
| | |
|---|---|
| **Quy tắc** | `NoiCT`, `NoiCT_MaDVHC`, `NoiCT_MaDVQL` mặc định sao chép từ `NoiTT`, `NoiTT_MaDVHC`, `NoiTT_MaDVQL`. Cho phép người dùng bỏ tick "giống thường trú" để nhập khác. |
| **Nguồn** | Chủ dự án |
| **Loại** | Chính sách nội bộ |
| **Áp dụng tại** | App web + tool (form địa chỉ) |
| **Đối tượng** | NguoiLX |
| **Cách kiểm chứng** | Nhập thường trú, để trống cư trú → cư trú = thường trú |
| **Ngoại lệ** | Người dùng nhập cư trú khác |

### BR-005 — Chặn trùng CCCD trong cùng khóa
| | |
|---|---|
| **Quy tắc** | Trước khi nạp, nếu `SoCMT` đã tồn tại trong CÙNG `MaKhoaHoc` → cảnh báo và không cho nạp trùng. Cho phép cùng CCCD ở khóa khác. |
| **Nguồn** | Chủ dự án (Câu 1=A) |
| **Loại** | Chính sách nội bộ |
| **Áp dụng tại** | T-NAP (kiểm trước insert) |
| **Đối tượng** | NguoiLX × KhoaHoc |
| **Cách kiểm chứng** | Nạp 1 CCCD vào khóa X 2 lần → lần 2 bị cảnh báo chặn; nạp CCCD đó vào khóa Y → cho phép |
| **Ngoại lệ** | Học viên học lại/khóa khác |

### BR-006 — Địa chỉ: map cũ→mới, mã và tên lấy từ DB
| | |
|---|---|
| **Quy tắc** | Cho nhập địa chỉ cũ hoặc mới. Dùng bảng phụ `DM_DVHC_MAP` (nguồn `vietnamadminunits`) để đổi địa chỉ cũ → xã mới; nối theo `(tên tỉnh mới, tên xã mới)` về `DM_DVHC` (`TrangThai=1`) lấy `MaDvhc`+`MaDVQL`. Tên hiển thị luôn theo DB. Xã bị chia (`isDividedWard`) hoặc không khớp → người dùng chọn tay từ `DM_DVHC` (2 cấp Tỉnh→Xã). |
| **Nguồn** | Chủ dự án (Option B) + DB thật (verify phủ 3321/3321) |
| **Loại** | Ràng buộc vận hành |
| **Áp dụng tại** | Form địa chỉ (app web + tool) |
| **Đối tượng** | NguoiLX (NoiTT/NoiCT) |
| **Cách kiểm chứng** | Nhập "Xã Phú Nghĩa, Đồng Nai" → ra MaDvhc=25267, MaDVQL=75 |
| **Ngoại lệ** | Xã chia → chọn tay |

### BR-007 — Loại hồ sơ suy theo hạng khóa
| | |
|---|---|
| **Quy tắc** | `MaLoaiHs` = 1 nếu hạng khóa bắt đầu `A` (mô tô), = 2 nếu `B/C/D/E/F` (ô tô, cấp mới). Nâng hạng = 3 (luồng riêng, ngoài MVP). |
| **Nguồn** | DB thật (khóa B → MaLoaiHs=2) + suy luận cho mô tô `[GIẢ ĐỊNH]` |
| **Loại** | Ràng buộc vận hành |
| **Áp dụng tại** | T-NAP |
| **Đối tượng** | NguoiLX_HoSo |
| **Cách kiểm chứng** | Chọn khóa hạng A1m → MaLoaiHs=1; khóa B → MaLoaiHs=2 |
| **Ngoại lệ** | Nâng hạng (3) |

### BR-008 — Hình thức cấp mặc định CM_VN
| | |
|---|---|
| **Quy tắc** | `MaHTCap` = `CM_VN` (Cấp cho người Việt Nam thi mới) cho hồ sơ cấp mới người VN — tương ứng ô "Chọn in GPLX" trên `UI.png`. |
| **Nguồn** | DB thật (HV khóa B đều CM_VN) |
| **Loại** | Ràng buộc vận hành |
| **Áp dụng tại** | T-NAP |
| **Đối tượng** | NguoiLX_HoSo |
| **Cách kiểm chứng** | Nạp HV cấp mới VN → MaHTCap=CM_VN |
| **Ngoại lệ** | Người nước ngoài (CM_EN) — ngoài MVP |

### BR-009 — Giấy tờ mặc định nộp đủ
| | |
|---|---|
| **Quy tắc** | Giấy tờ = `SELECT MaGT FROM DM_LoaiHSo_GiayTo WHERE MaLoaiHS=<loại> AND MaHangGPLX=<HangDT khóa>`. Insert từng giấy tờ với `TenGT` = tên đầy đủ từ `DM_GiayTo`, `TrangThai=1` (nộp đủ). |
| **Nguồn** | DB thật (hạng B → MaGT 1,2,3) + chủ dự án ("mặc định nộp đủ") |
| **Loại** | Ràng buộc vận hành |
| **Áp dụng tại** | T-NAP (sau HoSo_Insert) |
| **Đối tượng** | NguoiLXHS_GiayTo |
| **Cách kiểm chứng** | Nạp HV hạng B → 3 dòng giấy tờ MaGT 1,2,3, TrangThai=1 |
| **Ngoại lệ** | Người dùng bỏ tick giấy tờ nào đó |

### BR-010 — Ảnh chân dung: chuẩn và đường dẫn
| | |
|---|---|
| **Quy tắc** | Ảnh xuất `.jp2` (JPEG 2000), 480×640, RGB, ~60-85 KB. Ghi file `<IMG_PATH_CSDT>\<MaKhoaHoc>\70004-<yyyyMMddHHmmssfff>.jp2`. DB lưu đường dẫn ở `NguoiLX_HoSo.DuongDanAnh`, `ChatLuongAnh=1`, `NgayThuNhanAnh`=lúc thu, `NguoiThuNhanAnh`=nhân viên. |
| **Nguồn** | DB thật + file ảnh mẫu (471×628, RGB, 86,6 KB) + config `IMG_PATH_CSDT` |
| **Loại** | Ràng buộc vận hành |
| **Áp dụng tại** | T-ANH, T-NAP |
| **Đối tượng** | Filesystem + NguoiLX_HoSo |
| **Cách kiểm chứng** | Nạp HV có ảnh → file .jp2 mở được, DuongDanAnh đúng, app cũ hiện ảnh |
| **Ngoại lệ** | HV chưa có ảnh (cảnh báo, vẫn nạp — BR-011) |

### BR-011 — Điều kiện nạp mềm
| | |
|---|---|
| **Quy tắc** | Không chặn cứng khi thiếu ảnh, chưa đủ tuổi tối thiểu, hoặc vượt sĩ số khóa — chỉ **cảnh báo**, vẫn cho nạp. Chỉ ràng buộc NOT NULL của DB mới chặn (SP báo lỗi). |
| **Nguồn** | Chủ dự án (Câu 5=B) + DB thật (khóa cho 55/50) |
| **Loại** | Chính sách nội bộ |
| **Áp dụng tại** | T-NAP |
| **Đối tượng** | NguoiLX_HoSo |
| **Cách kiểm chứng** | Nạp HV thiếu ảnh → có cảnh báo, vẫn tạo được bản ghi |
| **Ngoại lệ** | Thiếu trường NOT NULL → chặn (lỗi SP) |

### BR-012 — Chỉ nạp vào khóa chưa lập Báo cáo 1
| | |
|---|---|
| **Quy tắc** | Dropdown chọn khóa chỉ hiện khóa `TrangThai=1` và **chưa có dòng trong `BaoCaoI`** (`KhoaHoc LEFT JOIN BaoCaoI ON MaKH` → NULL). Khóa đã lập BC1 không cho thêm HV. |
| **Nguồn** | DB thật (FK NguoiLX_HoSo.MaBC1 → BaoCaoI) + nghiệp vụ |
| **Loại** | Ràng buộc vận hành |
| **Áp dụng tại** | Chọn khóa (T-CHONKHOA) |
| **Đối tượng** | KhoaHoc |
| **Cách kiểm chứng** | Khóa đã lập BC1 → không xuất hiện trong danh sách chọn |
| **Ngoại lệ** | Không |

### BR-013 — Đổi khóa & vòng đời ảnh
| | |
|---|---|
| **Quy tắc** | Đổi HV sang khóa **cùng hạng**: `usp_NguoiLX_HoSo_Update` đổi `MaKhoaHoc`, giữ `MaDK`, sinh lại `SoHoSo` theo khóa mới, di chuyển file `.jp2` sang folder khóa mới, cập nhật `DuongDanAnh`, giữ nguyên tên file. Đổi sang **khác hạng** → xóa tạo lại (vì đổi cả hạng/giấy tờ/loại). |
| **Nguồn** | Chủ dự án + DB thật (FK MaKhoaHoc NO_ACTION) |
| **Loại** | Ràng buộc vận hành |
| **Áp dụng tại** | Chức năng đổi khóa |
| **Đối tượng** | NguoiLX_HoSo + filesystem |
| **Cách kiểm chứng** | Đổi khóa cùng hạng → MaKhoaHoc mới, file ảnh nằm folder mới, DuongDanAnh khớp |
| **Ngoại lệ** | Khác hạng → xóa tạo lại |

### BR-014 — Xóa học viên: cascade DB + xóa mềm ảnh
| | |
|---|---|
| **Quy tắc** | Xóa HV = `usp_NguoiLX_Delete` (cascade `NguoiLX_HoSo` → `NguoiLXHS_GiayTo`). File `.jp2` KHÔNG bị DB xóa → tool chuyển file sang folder `_DELETED` (xóa mềm) + ghi log. Không xóa cứng. |
| **Nguồn** | DB thật (FK CASCADE) + đề xuất an toàn |
| **Loại** | Ràng buộc vận hành |
| **Áp dụng tại** | Chức năng xóa HV |
| **Đối tượng** | NguoiLX + filesystem |
| **Cách kiểm chứng** | Xóa HV → 3 bảng sạch, file .jp2 nằm ở `_DELETED` |
| **Ngoại lệ** | HV đã có GPLX → không xóa được hồ sơ (FK NO_ACTION chặn) |

### BR-015 — Chống nạp trùng bằng UUID
| | |
|---|---|
| **Quy tắc** | Mỗi bản ghi thu thập trên VPS có UUID + trạng thái `cho_nap`/`da_nap`. Tool chỉ kéo `cho_nap`; nạp DB xong ghi `MaDK` + set `da_nap`. Bản ghi đã `da_nap` không nạp lại. |
| **Nguồn** | Đề xuất kỹ thuật (chống trùng do MaDK sinh mới mỗi lần) |
| **Loại** | Ràng buộc vận hành |
| **Áp dụng tại** | T-KEO, T-NAP |
| **Đối tượng** | Bản ghi thu thập (VPS) |
| **Cách kiểm chứng** | Nạp 1 bản ghi 2 lần → lần 2 bị chặn, không tạo HV thứ 2 |
| **Ngoại lệ** | Không |

### BR-016 — Bảo mật & lưu giữ PII trên VPS
| | |
|---|---|
| **Quy tắc** | Dữ liệu căn cước lưu tạm trên VPS: HTTPS + đăng nhập bắt buộc; giữ tối đa **30 ngày** rồi tự xóa; kèm bộ lọc cho người dùng xóa thủ công. |
| **Nguồn** | Chủ dự án (Câu 6=B) |
| **Loại** | Pháp lý (bảo vệ dữ liệu cá nhân) |
| **Áp dụng tại** | Backend VPS |
| **Đối tượng** | Bản ghi thu thập |
| **Cách kiểm chứng** | Bản ghi quá 30 ngày → tự biến mất; bộ lọc xóa tay hoạt động |
| **Ngoại lệ** | Không |

### BR-017 — Tạo khóa học qua SP, mã tự sinh
| | |
|---|---|
| **Quy tắc** | Tạo khóa = `usp_KhoaHoc_Insert` (mã `MaKH` tự sinh qua `CreateNewMaKhoaHoc`). 5 trường bắt buộc: Hạng đào tạo (`HangDT`, từ `DM_HangDT`), Tên khóa, Ngày KG, Ngày BG, Tổng số HV. `HangGPLX` suy từ hạng ĐT qua `DM_HangGPLX.MaHangMoi`. `MaCSDT`=70004, `MaSoGTVT`=70, `TrangThai`=1. |
| **Nguồn** | DB thật + chủ dự án (Câu 7=A) |
| **Loại** | Ràng buộc vận hành |
| **Áp dụng tại** | Chức năng tạo khóa |
| **Đối tượng** | KhoaHoc |
| **Cách kiểm chứng** | Tạo khóa hạng B → mã dạng `70004K26B0nn`, hiển thị trong app cũ |
| **Ngoại lệ** | Không |

### BR-018 — Quét QR CCCD: phản hồi + xác nhận sửa được
| | |
|---|---|
| **Quy tắc** | Quét QR CCCD (7 trường phân tách `\|`) phải có hiệu ứng "quét thành công" và hiện màn preview các trường lấy được **cho người dùng sửa** trước khi lưu. Ảnh thẻ chỉ dùng cắt ảnh chân dung, KHÔNG OCR. |
| **Nguồn** | Chủ dự án (yêu cầu UX) |
| **Loại** | Chính sách nội bộ |
| **Áp dụng tại** | App web (mobile) |
| **Đối tượng** | Bản ghi thu thập |
| **Cách kiểm chứng** | Quét thẻ → thấy hiệu ứng + 7 trường điền sẵn, sửa được |
| **Ngoại lệ** | QR lỗi → nhập tay |

### BR-019 — Đọc cấu hình từ QTHT_ThamSoHT, không hard-code
| | |
|---|---|
| **Quy tắc** | Đường dẫn ảnh gốc lấy từ `QTHT_ThamSoHT` (TenTS=`IMG_PATH_CSDT`), mã CSDT từ `MA_CSDT`. Không hard-code trong tool. |
| **Nguồn** | DB thật |
| **Loại** | Ràng buộc vận hành |
| **Áp dụng tại** | T-ANH, khởi tạo tool |
| **Đối tượng** | Cấu hình |
| **Cách kiểm chứng** | Đổi IMG_PATH_CSDT trong DB → tool ghi ảnh theo path mới |
| **Ngoại lệ** | Không |

### BR-020 — Đăng nhập riêng, ghi vết ai gửi/ai nạp
| | |
|---|---|
| **Quy tắc** | App web và tool đều yêu cầu đăng nhập bằng tài khoản riêng của hệ thống này. Lưu vết ai thu thập (app web) và ai nạp (`NguoiThuNhanAnh`/`NguoiTao` = tài khoản nạp). |
| **Nguồn** | Chủ dự án (Câu 2=A) |
| **Loại** | Chính sách nội bộ (an ninh PII) |
| **Áp dụng tại** | App web + tool |
| **Đối tượng** | Tài khoản người dùng |
| **Cách kiểm chứng** | Không đăng nhập → không dùng được; bản ghi có dấu người gửi/nạp |
| **Ngoại lệ** | Không |

---

## Bảng tổng hợp

| Mã | Quy tắc (tóm tắt) | Loại | Nguồn | Bước |
|---|---|---|---|---|
| BR-001 | Nạp qua SP có sẵn, không INSERT tay | Chính sách | Chủ DA + DB | T-NAP |
| BR-002 | SoHoSo 3 số MAX+1/khóa | Vận hành | DB | T-NAP |
| BR-003 | MaDK timestamp do DB sinh | Vận hành | DB | T-NAP |
| BR-004 | Cư trú mặc định = thường trú | Chính sách | Chủ DA | Form |
| BR-005 | Chặn trùng CCCD cùng khóa | Chính sách | Chủ DA | T-NAP |
| BR-006 | Map DVHC cũ→mới, tên/mã theo DB | Vận hành | Chủ DA + DB | Form |
| BR-007 | MaLoaiHs theo hạng khóa | Vận hành | DB + GĐ | T-NAP |
| BR-008 | MaHTCap=CM_VN | Vận hành | DB | T-NAP |
| BR-009 | Giấy tờ nộp đủ theo DM_LoaiHSo_GiayTo | Vận hành | DB + Chủ DA | T-NAP |
| BR-010 | Ảnh .jp2 480×640, ghi DuongDanAnh | Vận hành | DB + file mẫu | T-ANH/NAP |
| BR-011 | Điều kiện nạp mềm (chỉ cảnh báo) | Chính sách | Chủ DA + DB | T-NAP |
| BR-012 | Chỉ nạp khóa chưa BC1 | Vận hành | DB | T-CHONKHOA |
| BR-013 | Đổi khóa + di chuyển ảnh | Vận hành | Chủ DA + DB | Đổi khóa |
| BR-014 | Xóa HV cascade + xóa mềm ảnh | Vận hành | DB | Xóa HV |
| BR-015 | Chống nạp trùng bằng UUID | Vận hành | Kỹ thuật | T-KEO/NAP |
| BR-016 | PII giữ 30 ngày, HTTPS, xóa | Pháp lý | Chủ DA | VPS |
| BR-017 | Tạo khóa qua usp_KhoaHoc_Insert | Vận hành | DB + Chủ DA | Tạo khóa |
| BR-018 | QR có phản hồi + preview sửa được | Chính sách | Chủ DA | App web |
| BR-019 | Config từ QTHT_ThamSoHT | Vận hành | DB | Tool init |
| BR-020 | Đăng nhập riêng + ghi vết | Chính sách | Chủ DA | App web+tool |

## Thống kê theo loại

| Loại | Số quy tắc | Đổi được không |
|---|---:|---|
| Pháp lý | 1 (BR-016) | Không |
| Hợp đồng | 0 | — |
| Chính sách nội bộ | 7 | Có, cần thẩm quyền |
| Ràng buộc vận hành | 12 | Có, tùy DB |
| Thói quen | 0 | — |

## Quy tắc "Thói quen" — đã chất vấn

Không có quy tắc loại "Thói quen". Cái gần nhất là **cho vượt sĩ số khóa** (BR-011) — đã xác nhận là chủ ý (app cũ cho phép), không phải nợ quy trình.

## Quy tắc chưa có nguồn chắc (→ `10-assumptions.md`)

| Mã | Điểm cần xác thực | Ai xác nhận |
|---|---|---|
| BR-007 | Mô tô A*→MaLoaiHs=1 (chưa gặp ca thật) | Chủ dự án / khi có ca mô tô |
| BR-008 | CM_VN áp cho mọi ca cấp mới VN | Chủ dự án |
| BR-018 | QR CCCD đúng 7 trường của cơ sở | Test thẻ thật |
