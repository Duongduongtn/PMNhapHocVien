# Biên bản review TDD — PMCSĐTLX (THU-06 OCR, §6.7)

- **File review:** docs/TDD.md §6.7 (THU-06 — Chụp ảnh thẻ → tự đọc chữ OCR)
- **Ngày:** 07/10/2026
- **Nguồn đối chiếu:** PRD [THU-06] · TDD-decisions §20 · CHANGES #49 · BUG-14
- **Số phát hiện:** 12 (Chặn: 0 · Nên sửa: 7 · Ghi nhận: 5) — 0 tồn

> Phạm vi: §6.7 là **khung nghiệp vụ**, cố ý để *engine OCR* + *cách tách trường* cho `/tdd`. Review không tính các "chưa chốt" đó là lỗi; soi phần đã chốt (luồng, ràng buộc, PII) + đối chiếu PRD.

## Đã sửa

| # | Điểm | Mức | Phát hiện | Đã sửa thế nào |
|---|---|---|---|---|
| 1a | 1 (PRD) | Nên sửa | §6.7 thiếu dòng truy vết `Phục vụ` chuẩn như các mục khác | Thêm `> **Phục vụ:** THU-06` dưới tiêu đề |
| 1b | 1 (PRD) | Nên sửa | TDD-decisions §20 dòng 202 ("song song vẫn cải thiện QR iPhone — không thay nhau") mâu thuẫn quyết định BUG-14 A vừa chốt | Sửa §20: QR iPhone là ngõ cụt (probe fail), giao hẳn cho OCR, không đầu tư thêm QR |
| 2a | 2 (mơ hồ) | Nên sửa | Ranh giới "fail" vs "điền một phần" không rõ (đọc 3/6 trường thì sao) | Quy tắc mốc = **CCCD 12 số hợp lệ**: không có → fail không điền gì; có → điền phần đọc được + đánh dấu |
| 2b | 2 (mơ hồ) | Ghi nhận | "bám parse dùng chung `lib/qr.ts`" dễ hiểu nhầm là qr.ts đọc luôn text OCR | Làm rõ: tách trường từ OCR là bước mới; qr.ts chỉ chuẩn hóa hạ nguồn |
| 3a | 3 (edge) | Nên sửa | Ảnh thẻ 12MP làm Tesseract.js treo/sập tab điện thoại (OCR client không qua §7.4) | Thêm ràng buộc **downscale ≤~1600px cạnh dài TRƯỚC khi OCR** |
| 3b | 3 (edge) | Ghi nhận | CMND 9 số / CCCD cũ → layout lệch | Ghi rõ phạm vi = CCCD 12 số gắn chip; mẫu khác rơi về Nhập tay (validate bắt) |
| 3c | 3 (edge) | Ghi nhận | OCR đọc CCCD đủ 12 số nhưng sai chữ số → validate pass, dễ lướt | Nhấn màn xác nhận **không auto-submit**, buộc soát từng trường |
| 4a | 4 (bảo mật) | Nên sửa | Để ngỏ gửi ảnh CCCD ra dịch vụ OCR/eKYC ngoài = lộ PII căn cước (HTTPS chỉ bảo vệ đường truyền) | Siết: **OCR client-side = rào cứng**; dịch vụ ngoài chỉ mở khi có phê duyệt pháp lý/dữ liệu |
| 4b | 4 (bảo mật) | Nên sửa | Vòng đời ảnh thẻ dùng cho OCR không nói (hủy? hay thành ảnh thô giữ 30 ngày?) | Đọc xong hủy khỏi client, chỉ giữ nếu tái dùng cắt chân dung; không tạo đường lưu ảnh CCCD mới |
| 4c | 4 (bảo mật) | Ghi nhận | §12 "không log CCCD" chưa phủ đầu ra OCR | §12 +không log đầu ra OCR (console client / dịch vụ theo dõi lỗi) |
| 5a | 5 (hiệu năng) | Ghi nhận | NFR "thao tác <2s" không thực tế cho bước OCR trên điện thoại | Ghi rõ <2s không áp bước OCR; +spinner + hủy → Nhập tay |
| 6a | 6 (sơ đồ) | Nên sửa | Quyết định 2a thêm nhánh rẽ nhưng không có sơ đồ | Chèn sơ đồ luồng OCR ASCII (cùng kiểu §7.1) |

## Cố tình bỏ qua

Không có — mọi phát hiện đều sửa hoặc ghi nhận vào §6.7; 0 Chặn.

## Hoãn lại

| # | Phát hiện | Chờ gì |
|---|---|---|
| — | **Engine OCR cụ thể** (Tesseract.js vs engine client khác) + **cách tách trường** (layout thẻ vs OCR toàn ảnh + regex) | `/tdd` — chốt công nghệ (nơi chạy đã chốt client-side ở review này) |

---

**Kết luận:** §6.7 (khung nghiệp vụ THU-06) **đã đủ để sang `/tdd` chốt engine** — 0 phát hiện Chặn tồn. Ràng buộc nghiệp vụ, quy tắc fail và rào PII (client-side) đã rõ; chỉ còn chọn engine OCR + cách tách trường là việc kỹ thuật thuần.
