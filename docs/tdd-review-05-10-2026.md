# Biên bản review TDD — PMCSĐTLX

- **File review:** docs/TDD.md
- **Ngày:** 05/10/2026
- **Phạm vi:** chỉ phần SỬA HÔM NAY (CHANGES #36) — §11B.7 (định nghĩa DKKH + ma trận TCB-03/04), §11B.2 (filter khóa đích + sort + cờ dkkh), §5.5 (giữ token qua F5). Các phần khác đã review ở `tdd-review-03-10-2026.md` + `tdd-review-04-10-2026-tcb.md`.
- **Số phát hiện:** 7 (Chặn: 0 · Nên sửa: 4 · Ghi nhận: 3)
- **Lưu ý:** review cùng phiên viết (#36) → có thiên vị, nhẹ tay hơn người lạ đọc; nên chạy lại `/reviewtdd` phiên mới nếu muốn soát sâu toàn TDD.

## Đã sửa

| # | Điểm | Mức | Phát hiện | Đã sửa thế nào |
|---|---|---|---|---|
| 2a | Logic mơ hồ | Nên sửa | §11B.2 filter không nói rõ khi CHƯA chọn khóa nguồn (hạng chưa xác định) | Thêm: chưa chọn nguồn → bỏ điều kiện hạng, chỉ lọc `!dkkh` |
| 2b | Logic mơ hồ | Nên sửa | TDD chưa ghi hành vi "tự kiểm kết nối đích khi vào màn" (thay cổng bấm-tay) | Thêm bullet §11B.2 mô tả auto-test + giữ nút thử lại tay |
| 3a | Edge | Nên sửa | §5.5 chưa nêu edge `localStorage` bị chặn | Thêm: try/catch → fallback bộ nhớ, không vỡ app |
| 6a | Sơ đồ | Nên sửa | §5.5 có sơ đồ đăng nhập nhưng thiếu luồng khôi phục phiên F5 | Thêm sơ đồ ASCII F5 (token→/me→200/401) |

## Cố tình bỏ qua (Ghi nhận — chấp nhận, không sửa)

| # | Phát hiện | Mức | Vì sao chấp nhận |
|---|---|---|---|
| 3b | `/me` lỗi MẠNG (≠401) khi F5 → xóa token về đăng nhập (dù token có thể còn hợp lệ) | Ghi nhận | Tool localhost; backend chết thì không thao tác được gì → đăng xuất vô hại |
| 4a | Token lưu `localStorage` → tăng bề mặt lộ (XSS) so với bộ nhớ | Ghi nhận | Tool localhost 1 người, chỉ phục vụ webui của chính nó → gần như không có đường XSS; đã ghi §5.5 |
| 5a | `CHARINDEX` trên `DuongDan` không dùng index → quét TRANS_CLI per khóa | Ghi nhận | Quy mô hiện tại ~68 gói × ~20 khóa/năm = không đáng kể; theo dõi nếu TRANS_CLI lên hàng chục nghìn |

## Hoãn lại

(không có)

---

**Kết luận:** TDD ĐỦ để code — thực tế code đã viết + verify trước review này. **0 phát hiện Chặn.** 4 `Nên sửa` đều là bổ sung/làm rõ tài liệu (code đã đúng), đã sửa xong. 3 `Ghi nhận` chấp nhận được, ghi lại ở trên.
