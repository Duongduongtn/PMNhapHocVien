# Lỗ hổng vận hành phải chặn trước go-live — Thu nhận hồ sơ học viên

**Ngày:** 30/09/2026 · **Người lập:** BA (Claude)

> Trọng tâm: ghi vào **DB production** + xử lý **dữ liệu căn cước (PII)** trên VPS. Đây là 2 mặt rủi ro chính.

---

## 1. Danh sách lỗ hổng

```
OG-001  Lộ PII căn cước qua truy cập ngang trên VPS (IDOR)
        Loại: Rò rỉ / Phân quyền
        Kịch bản: NV thu nhận đổi id/UUID trên URL/API để xem bản ghi (CCCD, ảnh) của HV do người khác gửi.
        Hậu quả: Lộ dữ liệu cá nhân.
        Chặn bằng: API kiểm quyền theo phiên + scope; không trả bản ghi ngoài quyền; id dạng UUID khó đoán.
        Cách kiểm chứng: Đăng nhập collector A, gọi API bản ghi của B → 403.
        Mức: Chặn go-live
        Edge case gốc: EC-050
        Năng lực: CAP (auth/scope)

OG-002  App web gọi thẳng API nạp DB (vượt vai trò)
        Loại: Phân quyền
        Kịch bản: Collector gọi endpoint nạp DB (vốn của operator) để ghi thẳng vào DB thật.
        Hậu quả: Ghi DB sai quyền, khó truy vết.
        Chặn bằng: Chức năng nạp DB CHỈ ở tool (không expose qua API public); tool xác thực token máy/operator.
        Cách kiểm chứng: Không có endpoint nạp DB nào gọi được từ app web.
        Mức: Chặn go-live
        Edge case gốc: EC-050
        Năng lực: CAP (auth)

OG-003  Xuất/tải PII hàng loạt không kiểm soát
        Loại: Rò rỉ
        Kịch bản: Người dùng xuất toàn bộ danh sách HV (CCCD, địa chỉ) ra Excel trước khi nghỉ việc.
        Hậu quả: Lộ PII quy mô lớn.
        Chặn bằng: MVP không có xuất hàng loạt (Câu 4=A); khi thêm sau → chỉ admin, có log + giới hạn.
        Cách kiểm chứng: MVP: không có nút xuất; sau: log mọi lần xuất.
        Mức: Cao
        Edge case gốc: —
        Năng lực: CAP (sau)

OG-004  Tool kết nối DB bằng tài khoản sa toàn quyền
        Loại: Vận hành / An ninh
        Kịch bản: Tool dùng tài khoản sa với mật khẩu mặc định yếu → nếu tool bị chiếm hoặc lỗi, toàn DB bị rủi ro.
        Hậu quả: Rủi ro toàn DB.
        Chặn bằng: Tạo SQL login riêng cho tool, chỉ EXECUTE các SP cần + SELECT danh mục; đổi mật khẩu mạnh; lưu chuỗi kết nối an toàn (không hard-code plaintext trong repo).
        Cách kiểm chứng: Tool chạy được với login hạn chế; sa không nhúng trong mã nguồn.
        Mức: Chặn go-live
        Edge case gốc: —
        Năng lực: CAP (config bảo mật)

OG-005  Nạp trùng do đồng thời / bấm nút hai lần
        Loại: Đồng thời / Toàn vẹn
        Kịch bản: 2 tool cùng nạp 1 bản ghi, hoặc bấm "Nạp" 2 lần → 2 HV (2 MaDK).
        Hậu quả: Hồ sơ ma, sai sĩ số.
        Chặn bằng: Khóa bản ghi khi importing (EC-010); chống double-submit (disable nút + idempotent theo UUID, BR-015).
        Cách kiểm chứng: Bấm Nạp 2 lần / 2 tool → 1 HV.
        Mức: Chặn go-live
        Edge case gốc: EC-010, EC-011, EC-003
        Năng lực: CAP (nạp an toàn)

OG-006  Ảnh .jp2 mồ côi / rác trên ổ đĩa
        Loại: Toàn vẹn dữ liệu
        Kịch bản: Ghi file rồi SP lỗi; hoặc xóa/đổi khóa HV để lại file cũ.
        Hậu quả: Rác ổ đĩa, ảnh trỏ sai.
        Chặn bằng: Ghi file sau khi SP OK / dọn nếu fail (EC-022); đổi khóa di chuyển file (BR-013); xóa mềm vào _DELETED (BR-014).
        Cách kiểm chứng: Ép SP fail → không còn file mồ côi.
        Mức: Cao
        Edge case gốc: EC-021, EC-022
        Năng lực: CAP (quản lý ảnh)

OG-007  PII nằm trong log / staging / backup không kiểm soát
        Loại: Rò rỉ
        Kịch bản: CCCD + ảnh lưu trong log tool, SQLite staging, hoặc backup VPS mà không xóa/mã hóa.
        Hậu quả: Lộ PII qua kênh phụ.
        Chặn bằng: Không log nội dung CCCD; staging SQLite xóa sau nạp; VPS xóa 30 ngày (BR-016); HTTPS.
        Cách kiểm chứng: Kiểm log/staging không chứa số CCCD sau khi nạp.
        Mức: Cao
        Edge case gốc: EC-040
        Năng lực: CAP (PII)

OG-008  Sửa hồ sơ khóa đã báo cáo (BC1) / đã có GPLX
        Loại: Toàn vẹn dữ liệu
        Kịch bản: Tool sửa/xóa HV thuộc khóa đã lập BC1 hoặc đã có GPLX → lệch dữ liệu đã báo Sở.
        Hậu quả: Sai số liệu báo cáo.
        Chặn bằng: Tool chặn sửa/xóa khi khóa đã BC1 (BR-012) / FK chặn khi có GPLX (BR-014).
        Cách kiểm chứng: Thử sửa HV khóa đã BC1 → bị chặn.
        Mức: Cao
        Edge case gốc: EC-051
        Năng lực: CAP (quản lý)
```

## 2. Bảng rà bắt buộc

### Phân quyền và ranh giới dữ liệu
| # | Câu hỏi rà | Có lỗ hổng? | OG- | Ghi chú |
|---|---|---|---|---|
| 1 | Đổi id URL xem bản ghi người khác (IDOR)? | LỖ HỔNG | OG-001 | PII căn cước |
| 2 | Gọi thẳng API vượt quyền? | LỖ HỔNG | OG-002 | Nạp DB chỉ ở tool |
| 3 | Tìm kiếm lộ dữ liệu ngoài phạm vi? | Đã xử lý ở CAP | — | Tool nội bộ 1 CSDT, scope=all trong CSDT |
| 4 | Thông báo lỗi lộ thông tin nội bộ? | LỖ HỔNG nhẹ | OG-004 | Không lộ chuỗi kết nối/sa trong lỗi |
| 5 | Quyền thu hồi khi đang mở form? | Đã xử lý | — | Kiểm quyền lại khi submit |
| 6 | Job nền chạy dưới quyền gì? | Đã xử lý ở OG-007 | — | Job xóa PII = service, có log |
| 7 | Admin thao tác hộ — log tên ai? | Đã xử lý | — | Ghi vết theo BR-020 |
| 8 | Link chia sẻ báo cáo? | Không áp dụng | — | MVP không có chia sẻ báo cáo |

### Rò rỉ dữ liệu
| # | Câu hỏi rà | Có lỗ hổng? | OG- | Ghi chú |
|---|---|---|---|---|
| 9 | Ai xuất Excel/CSV, giới hạn, log? | LỖ HỔNG (tương lai) | OG-003 | MVP không xuất |
| 10 | NV nghỉ việc xuất toàn bộ? | Đã xử lý ở OG-003 | OG-003 | — |
| 11 | Dữ liệu nhạy cảm lộ qua API/báo cáo? | LỖ HỔNG | OG-001 | CCCD, ảnh |
| 12 | Backup/log chứa PII? | LỖ HỔNG | OG-007 | — |

### Đồng thời và toàn vẹn
| # | Câu hỏi rà | Có lỗ hổng? | OG- | Ghi chú |
|---|---|---|---|---|
| 13 | Tài nguyên hữu hạn có khóa? | Đã xử lý | OG-005 | SoHoSo là "tài nguyên", cần khóa sinh |
| 14 | Bấm nút 2 lần tạo 2 bản ghi? | LỖ HỔNG | OG-005 | Chống double-submit |
| 15 | Hai người sửa cùng bản ghi? | Đã xử lý | OG-005 | Khóa importing |
| 16 | Job định kỳ chạy trùng? | Đã xử lý | OG-007 | Job xóa idempotent |
| 17 | Giao dịch nhiều bước hỏng giữa chừng? | Đã xử lý | OG-006 | Transaction SP + dọn file |

### Tích hợp hệ thống ngoài
| # | Câu hỏi rà | Có lỗ hổng? | OG- | Ghi chú |
|---|---|---|---|---|
| 18 | Webhook/gửi trùng — idempotency? | Đã xử lý | OG-005 | UUID (BR-015) |
| 19 | Đối tác trả lời sau timeout? | Đã xử lý ở EC-061 | — | Transaction rollback |
| 20 | VPS/DB chết — dừng hay suy giảm? | Đã xử lý | — | EC-061/062: giữ pending, thử lại |
| 21 | Số liệu lệch giữa VPS và DB? | Đã xử lý | — | DB là chuẩn; VPS chỉ hàng đợi |

### Vận hành
| # | Câu hỏi rà | Có lỗ hổng? | OG- | Ghi chú |
|---|---|---|---|---|
| 22 | Sửa dữ liệu sai bằng công cụ nào? | Đã xử lý | — | Tool + app cũ; không sửa thẳng bảng (BR-001) |
| 23 | Ai sửa cấu hình/quy tắc, có log? | Đã xử lý | — | Chỉ admin sửa QTHT_ThamSoHT |
| 24 | Hệ thống sai không ai báo? | LỖ HỔNG nhẹ | OG-006 | Cần cảnh báo file mồ côi/nạp lỗi |
| 25 | SOD lách bằng dùng chung tài khoản? | LỖ HỔNG | OG-004 | SOD-002: cấm dùng chung |

## 3. Thống kê

| Mức | Số lỗ hổng | Có biện pháp chặn | Có cách kiểm chứng |
|---|---:|---:|---:|
| Chặn go-live | 4 (OG-001,002,004,005) | 4 | 4 (cần chạy khi build) |
| Cao | 4 (OG-003,006,007,008) | 4 | 4 |
| Trung bình | 0 | — | — |

**Điều kiện go-live:** 4 lỗ hổng "Chặn go-live" phải có biện pháp + kiểm chứng đã chạy qua trước khi cho dùng thật.

## 4. Bàn giao

Đầu vào cho bước bảo mật chi tiết (security-requirement-extraction) khi sang giai đoạn thiết kế. Trọng tâm: PII căn cước + tài khoản DB.
