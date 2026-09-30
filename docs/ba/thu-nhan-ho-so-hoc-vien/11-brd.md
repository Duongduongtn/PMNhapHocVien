# BRD — Thu nhận hồ sơ học viên (mobile/web + tool nạp DB)

**Phiên bản:** 0.1 · **Ngày:** 30/09/2026 · **Người lập:** BA (Claude) · **Trạng thái:** Nháp

> Bản tóm tắt + liên kết. Chi tiết ở file chủ (xem `00-INDEX.md`). Không sửa nội dung nghiệp vụ ở đây.

---

## 1. Tóm tắt điều hành

Cơ sở đào tạo lái xe (CSDT 70004) đang nhập từng học viên bằng tay tại máy chứa DB — chậm, dễ sai địa chỉ sau sáp nhập 2025, và bị trói tại một máy. Đề xuất: **app web** (điện thoại/máy tính) quét QR căn cước + thu thập thông tin & ảnh, đẩy lên **VPS**; **tool tại máy DB** kéo về, tự map địa chỉ cũ→mới, căn ảnh + xóa phông + xuất `.jp2`, và nạp vào DB **qua stored procedure có sẵn** để bản ghi hiển thị y như app cũ. Tool đồng thời là app quản lý học viên (tra cứu/sửa/đổi khóa/xóa) và tạo khóa học. Không làm gì → tiếp tục chậm, sai, nghẽn đầu khóa. Xin duyệt phạm vi + kiến trúc để sang PRD/xây dựng.

## 2. Bối cảnh và vấn đề

**Hiện tại:** gõ tay đầy đủ từng HV tại máy DB (màn "Thu nhận Hồ sơ cấp mới").
**Điểm đau:** chậm/nghẽn đầu khóa; sai địa chỉ/DVHC sau sáp nhập; bị trói tại máy DB.
**Chi phí:** `[GIẢ ĐỊNH]` chưa định lượng (AS-010).
**Ai chịu:** nhân viên thu nhận, gián tiếp học viên.

📄 [`01-problem-statement.md`](./01-problem-statement.md)

## 3. Phạm vi

**Trong phạm vi:** app web thu thập (QR + nhập + ảnh); backend VPS hàng đợi; tool nạp DB + quản lý hồ sơ + tạo khóa; map DVHC cũ→mới; mô tô + ô tô cấp mới.

**Ngoài phạm vi:** sát hạch, Báo cáo 1/2, cấp/in GPLX, báo cáo Sở/Cục; nâng hạng đầy đủ (loại 3); sửa/xóa khóa học; kết xuất báo cáo (giai đoạn sau).

📄 [`01-problem-statement.md`](./01-problem-statement.md)

## 4. Các bên liên quan

| Vai trò | Mối quan tâm | Quyết định |
|---|---|---|
| Chủ dự án / vận hành CSDT | Nhanh, đúng, trung thực với app cũ | Phạm vi, nghiệp vụ |
| Nhân viên thu nhận | Thu thập dễ, nhanh | — |
| Nhân viên nạp DB | Nạp an toàn, quản lý được | — |

📄 [`07-roles-permissions.md`](./07-roles-permissions.md)

## 5. Quy trình hiện tại (as-is)

Nhân viên tại máy DB: chọn khóa → gõ tay thông tin từ CCCD → tra/chọn DVHC → chụp/quét ảnh → tick giấy tờ → Lưu (app sinh Số hồ sơ + MaDK, ghi DB + file ảnh). Hỏng ở: tra sai địa chỉ, nghẽn khi đông, thiếu ảnh.

| # | Điểm đau | Ở bước | Chi phí |
|---|---|---|---|
| 1 | Gõ tay lại từ CCCD | C | `[GIẢ ĐỊNH]` giờ công |
| 2 | Tra/đổi địa chỉ cũ→mới tay | D/F | Lỗi + thời gian |
| 3 | Bị trói tại máy DB | toàn luồng | Không thu từ xa |
| 4 | Nghẽn đầu khóa | C | HV chờ |

📄 [`04-flow-as-is.md`](./04-flow-as-is.md)

## 6. Quy trình đề xuất (to-be)

Tách thu thập (app web) khỏi nạp (tool). QR điền sẵn, tool tự suy trường theo khóa + config, map địa chỉ tự động, xử lý ảnh tập trung. Nạp qua SP có sẵn → hiển thị y app cũ.

| Bước as-is | Số phận | Quy tắc đi đâu |
|---|---|---|
| Gõ tay tại máy DB | Tự động hóa | Điền từ QR + suy theo khóa |
| Tra/đổi địa chỉ tay | Tự động hóa | DM_DVHC_MAP (BR-006) |
| Chụp ảnh rời tại máy DB | Tách + tự động | Điện thoại chụp thô, tool xử lý (BR-010) |
| Bị trói tại máy DB | Bỏ | App web thu thập mọi nơi |
| Chọn mọi khóa | Thu hẹp | Chỉ khóa chưa BC1 (BR-012) |

📄 [`05-flow-to-be.md`](./05-flow-to-be.md) · vòng đời: [`04b-state-ho-so-thu-thap.md`](./04b-state-ho-so-thu-thap.md)

## 7. Quy tắc nghiệp vụ

**Tổng: 20 quy tắc** — 1 pháp lý · 0 hợp đồng · 7 chính sách nội bộ · 12 ràng buộc vận hành · 0 thói quen.

| Mã | Quy tắc (tóm tắt) | Loại |
|---|---|---|
| BR-001 | Nạp qua SP có sẵn, không INSERT tay | Chính sách |
| BR-002 | Số hồ sơ 3 số MAX+1/khóa | Vận hành |
| BR-006 | Map địa chỉ cũ→mới, tên/mã theo DB | Vận hành |
| BR-012 | Chỉ nạp khóa chưa lập BC1 | Vận hành |
| BR-016 | PII giữ 30 ngày, HTTPS, xóa | Pháp lý |

📄 Nguồn sự thật: [`06-business-rules.md`](./06-business-rules.md)

## 8. Vai trò và phân quyền

**3 vai trò** (Nhân viên thu nhận · Nhân viên nạp DB · Quản trị) · **2 SOD**. Phân quyền theo phạm vi CSDT (`all` trong CSDT) + theo trạng thái (khóa chưa/đã BC1, HV chưa/đã GPLX). Đăng nhập riêng, không dùng chung tài khoản (PII).

📄 [`07-roles-permissions.md`](./07-roles-permissions.md)

## 9. Năng lực hệ thống

**15 năng lực** — 13 bắt buộc (MVP) · 2 có thì tốt.

| Mã | Năng lực | Ưu tiên | BR/EC liên quan |
|---|---|---|---|
| CAP-001 | App web: quét QR + hiệu ứng + preview sửa | Bắt buộc | BR-018 |
| CAP-002 | App web: nhập tay + chụp ảnh thô + gửi VPS | Bắt buộc | BR-015,020 |
| CAP-003 | VPS: hàng đợi chờ nạp, giữ 30 ngày + xóa | Bắt buộc | BR-016 |
| CAP-004 | Tool: kéo hàng đợi, chống trùng UUID | Bắt buộc | BR-015, EC-020 |
| CAP-005 | Tool: chọn mô tô/ô tô → khóa chưa BC1 | Bắt buộc | BR-007,012 |
| CAP-006 | Tool: map địa chỉ cũ→mới + chọn tay | Bắt buộc | BR-006, EC-032 |
| CAP-007 | Tool: căn ảnh + xóa phông + .jp2 + ghi path | Bắt buộc | BR-010,019 |
| CAP-008 | Tool: sinh Số hồ sơ + nạp 3 SP + giấy tờ | Bắt buộc | BR-001,002,008,009 |
| CAP-009 | Tool: kiểm trùng CCCD trong khóa | Bắt buộc | BR-005, EC-012 |
| CAP-010 | Tool: tra cứu/sửa hồ sơ đã có (lưới, tìm, sửa) | Bắt buộc | scope B |
| CAP-011 | Tool: đổi khóa + di chuyển ảnh | Bắt buộc | BR-013 |
| CAP-012 | Tool: xóa HV + xóa mềm ảnh | Bắt buộc | BR-014, EC-021 |
| CAP-013 | Tool: tạo khóa học qua usp_KhoaHoc_Insert | Bắt buộc | BR-017 |
| CAP-014 | Đăng nhập/phân quyền app web + tool | Bắt buộc | BR-020, OG-001/002 |
| CAP-015 | Bộ lọc + xóa PII thủ công trên VPS | Có thì tốt | BR-016 |

> Cỡ Vừa: chưa tách `12-capabilities.md`. User story Given/When/Then chi tiết sẽ lập ở bước `/prd`.

## 10. User story tiêu biểu

```
US-001  Là nhân viên thu nhận, tôi muốn quét QR căn cước để điền sẵn hồ sơ, giảm gõ tay.
        AC-1  Given thẻ CCCD hợp lệ / When quét QR / Then hiện hiệu ứng OK + 7 trường điền sẵn, sửa được.
        AC-2  Given QR mờ không đọc / When quét thất bại / Then chuyển sang nhập tay.

US-008  Là nhân viên nạp DB, tôi muốn nạp học viên vào khóa để hồ sơ hiện đúng trên app cũ.
        AC-1  Given bản ghi chờ nạp + khóa chưa BC1 / When bấm Nạp / Then tạo HV qua SP, Số hồ sơ = MAX+1, ảnh .jp2 ghi đúng path.
        AC-2  Given CCCD đã có trong khóa / When nạp / Then cảnh báo trùng, không tạo trùng.
```

## 11. Edge case

**Tổng: 25 ca** — 4 Chặn · 13 Cao · 5 Trung bình · 0 Thấp.

| Mã | Tình huống | Trục |
|---|---|---|
| EC-003 | Nạp lại bản ghi đã nạp | T1 |
| EC-010 | Hai tool cùng nạp một bản ghi | T2 |
| EC-011 | Tranh Số hồ sơ khi nạp đồng thời | T2 |
| EC-061 | Mất kết nối DB giữa lúc nạp | T7 |

📄 [`08-edge-cases.md`](./08-edge-cases.md)

## 12. Lỗ hổng vận hành

**Tổng: 8 lỗ hổng — 4 chặn go-live.**

| Mã | Lỗ hổng | Biện pháp | Chặn go-live |
|---|---|---|---|
| OG-001 | Lộ PII qua IDOR trên VPS | Kiểm quyền theo phiên+scope | Có |
| OG-002 | App web gọi thẳng API nạp DB | Nạp chỉ ở tool | Có |
| OG-004 | Tool dùng sa toàn quyền | SQL login riêng | Có |
| OG-005 | Nạp trùng đồng thời/2 lần | Khóa importing + chống double-submit | Có |

📄 [`09b-operational-gaps.md`](./09b-operational-gaps.md)

## 13. Rủi ro và giả định

**Giả định "Nền móng" chưa kiểm chứng:**
| Mã | Giả định | Kiểm bằng | Hạn |
|---|---|---|---|
| AS-001 | QR CCCD đúng 7 trường của cơ sở | Quét thẻ thật | Trước viết parser |
| AS-003 | Nạp qua SP ra bản ghi y app cũ | Nạp thử + mở app cũ | Phase 1 build |

AS-002 (map DVHC phủ 100%) đã xác nhận 30/09/2026. Pre-mortem/risk register: `[CHƯA LÀM]` (cỡ Vừa).

📄 [`10-assumptions.md`](./10-assumptions.md)

## 14. Truy vết (kiểm gọn cỡ Vừa)

| Phép kiểm | Số lỗ | Ngày |
|---|---:|---|
| 1 — Mọi bước to-be có năng lực | 0 | 30/09/2026 |
| 2 — Mọi quy tắc có bước/năng lực áp | 0 | 30/09/2026 |
| 3 — Mọi EC Chặn/Cao có tiêu chí nghiệm thu | 0 | 30/09/2026 |
| 4 — Mọi OG chặn go-live có biện pháp | 0 | 30/09/2026 |

> Bảng truy vết đầy đủ (13-traceability.md) sẽ lập nếu nâng cỡ Lớn hoặc khi vào PRD.

## 15. Câu hỏi còn mở

| Câu hỏi | Ai quyết | Đang chặn | Hạn |
|---|---|---|---|
| Định dạng QR CCCD thật của cơ sở | Test thẻ | Parser QR (AS-001) | Trước build app web |
| Số HV/khóa + thời gian gõ/HV | Chủ dự án | Định lượng ROI | Không chặn build |
| App web có cần chế độ offline | NV thu nhận | Thiết kế gửi VPS | Trước build app web |
| Tool kết nối DB bằng sa hay login riêng | Chủ dự án/IT | An ninh (OG-004) | Trước go-live |
| Scope xem bản ghi giữa các NV thu nhận | Chủ dự án | Phân quyền VPS | Trước build backend |

## Lịch sử thay đổi

Xem [`00-CHANGELOG.md`](./00-CHANGELOG.md).
