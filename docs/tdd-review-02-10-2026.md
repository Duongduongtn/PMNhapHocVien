# Biên bản review TDD — PMCSĐTLX (nhập học viên)

- **File review:** docs/TDD.md (phạm vi: thay đổi CHANGES #22)
- **Ngày:** 02/10/2026
- **Số phát hiện:** 17 (Chặn: 2 · Nên sửa: 9 · Ghi nhận: 6) + 2 sơ đồ bổ sung
- **Lưu ý:** TDD #22 viết trong cùng phiên review → bản này nhẹ tay hơn thực tế; nên mở phiên mới soi lại các mục §11 nếu cần chắc.

## Đã sửa

| # | Điểm | Mức | Phát hiện | Đã sửa thế nào |
|---|---|---|---|---|
| 1 | 2 | Chặn | `TT_XuLy` dùng ngưỡng `< '11'` vẫn hạ trạng thái trung gian; tập BC2 là rời rạc (thiếu `'15'`) | §11.5 + PRD QLY-05/QLY-07: đổi sang **"không bao giờ HẠ"** — whitelist `'01'/'02'`→`'03'`, còn lại giữ nguyên |
| 2 | 3 | Chặn | Chạy đổi nền cả khóa lần 2 ghi đè `_BACKUP` → mất bản gốc thật | §11.6: **chỉ chép `_BACKUP` nếu chưa tồn tại** |
| 3 | 1 | Nên sửa | "Nạp lại nhanh" (NAP-01) có ở PRD, thiếu ở TDD | §10.4: +mô tả (gọi lại `nap_lo` cho 1 uuid) |
| 4 | 1 | Nên sửa | 4 endpoint mới chưa vào danh mục §4.6 | §4.6: +`/ho-so/anh`, `/anh-thumb`, `DELETE /keo-ve/:uuid`, `POST /khoa/:ma_kh/doi-nen` |
| 5 | 2 | Nên sửa | QLY-07 "chỉ ảnh chưa trắng" không nói phát hiện bằng gì | §11.6 + PRD: heuristic lấy mẫu 4 góc + tùy chọn "tất cả" (cách A) |
| 6 | 2 | Nên sửa | Avatar khi file mất hiển thị giống "chưa ảnh" | §11.1: `co_anh=true`+404/422 → **icon ảnh-vỡ** (khác icon người) |
| 7 | 3 | Nên sửa | Đứt giữa lúc ghi `.jp2` → file cụt | §11.5/§11.6: ghi **atomic** (file tạm → `os.replace`) |
| 8 | 3 | Nên sửa | File `.jp2` hỏng khi phục vụ ảnh → 500 | §11.1: transcode lỗi → **422**, không 500 |
| 9 | 3 | Nên sửa | Click sửa ảnh HV mà file gốc mất | §11.5: 404 → AnhModal mở chế độ chọn-file mới |
| 10 | 4 | Nên sửa | Cache thumbnail chứa PII trên đĩa | §11.1: cache ở temp cục bộ + `.gitignore` / in-memory |
| 11 | 5 | Nên sửa | Avatar: N transcode `.jp2`→PNG mỗi trang | §11.1: `loading="lazy"` + chỉ fetch dòng đang hiện + cache |
| 12 | 6 | — | Thiếu sơ đồ vòng đời `TT_XuLy` | §11.5: +sơ đồ ASCII |
| 13 | 6 | — | Thiếu sơ đồ liên kết HV↔Báo cáo | §11.3: +sơ đồ ASCII |

## Ghi nhận (biết để đó, không cần sửa)

| # | Phát hiện | Vì sao chấp nhận |
|---|---|---|
| 1 | QLY-02 Steps (PRD) còn ghi SP cũ `usp_NguoiLX_HoSo_Update` | Ngoài phạm vi #22; xử qua `/capnhat` sau |
| 2 | Operator xem mọi HV qua endpoint ảnh | Đúng vai trò tool nội bộ CSDT, không phải IDOR |
| 3 | `POST .../doi-nen` để operator (không ép admin) | Nhất quán các thao tác ghi khác; có `_BACKUP` + xác nhận UI |
| 4 | 2 tool chạy bulk cùng khóa | Hiếm (1 máy CSDT); đã ghi chú applock khi code |
| 5 | QLY-07 xử lý tuần tự + chạy nền | Đã thiết kế đúng (không block UI, không nạp hết RAM) |
| 6 | Không query mới thiếu index | Endpoint ảnh tra theo `MaDK` (PK); thống kê client-side |

## Cố tình bỏ qua

(Không có — mọi phát hiện Chặn/Nên sửa đều đã áp.)

## Hoãn lại

| # | Phát hiện | Chờ gì |
|---|---|---|
| 1 | Sửa thông tin nhân thân *trước* nạp trong tool | Chủ dự án quyết (CHANGES #22 mục ❓ treo) |

## Kết luận

**TDD đã đủ để bắt đầu code.** 0 phát hiện Chặn còn mở (2 Chặn đã sửa). Bước tiếp: `/kehoach` bổ sung (rework QLY-01/03/05 + NAP-01 + task QLY-07) → `/prototype-next` (màn #14/#15) → code. Khi code QLY-05 ưu tiên vá `ghi_anh_update` (quy tắc không-bao-giờ-hạ `TT_XuLy`) trước.
