# Biên bản review TDD — PMCSĐTLX (QLY-09 §11.8)

- **File review:** docs/TDD.md §11.8 "Đối soát & đồng bộ trạng thái VPS↔CSDT"
- **Phạm vi:** chỉ §11.8 (story mới QLY-09, viết qua /capnhat #28) — không soát lại toàn TDD
- **Ngày:** 03/10/2026
- **Lưu ý:** §11.8 viết trong cùng phiên → review tự-soát (nhẹ tay hơn người lạ đọc)
- **Số phát hiện:** 1 (Chặn: 1 · Nên sửa: 0 · Ghi nhận: 0)

## Đã sửa

| # | Điểm | Mức | Phát hiện | Đã sửa thế nào |
|---|---|---|---|---|
| 1 | 2 (logic) + 1 (PRD) | 🔴 Chặn | Bản ghi VPS `ho_so_thu_thap` KHÔNG có cột khóa; khóa chỉ ở CSDT (nối qua `ma_dk`). Nên **ca ① phantom** (ma_dk không có trong CSDT) và **ca ③ importing treo** (chưa có ma_dk) **không quy được về khóa** → quét "theo khóa" không bao giờ tìm ra chúng — đúng cái đẻ ra tính năng (Lê Thị Hồng) lại không hiện | **Phương án A (chủ dự án chốt):** tách 2 chế độ — **① đối soát theo khóa** (ca ②, neo CSDT) + **② quét bản ghi lạc toàn hệ** (ca ①③, neo VPS, tái dùng `GET /api/admin/ho-so` HTG-03, check một chiều). Làm rõ cách nối `nap_xong`/`tra-uuid` + ứng xử khi thiếu nối (ghi "không tra được", không báo động giả). Sửa §11.8 + PRD QLY-09 Done khi + BUILD-PLAN task 48/49 + TDD Changelog v3.1 |

## Cố tình bỏ qua

(không có)

## Hoãn lại

(không có)

## Các điểm còn lại — kết quả

- **Điểm 1 (đối chiếu PRD):** khớp PRD QLY-09 (3 ca + phòng tuyến 2 + không tự động hàng loạt). Sau sửa, PRD+TDD nhất quán 2 chế độ.
- **Điểm 3 (edge):** bảng edge đủ (VPS down · BC1 · PII đã dọn · importing đang nạp thật vs treo). Ghi nhận nhẹ: 2 operator đối soát+sửa cùng lúc — hiếm (thường 1 máy CSDT), không chặn.
- **Điểm 4 (bảo mật):** admin/operator; nút sửa tái dùng guard BC1/PII sẵn có. Không mới. Quét lạc toàn hệ = admin-only (dùng `/api/admin/ho-so`).
- **Điểm 5 (hiệu năng):** sau sửa — ca ② theo khóa (nhẹ); ca ①③ check một chiều trên tập VPS imported/importing (không so 2 chiều toàn tập).
- **Điểm 6 (sơ đồ):** có ASCII 3 ca trong §11.8. Đủ cho quy mô.

## Kết luận

TDD §11.8 **đã đủ để bắt đầu code** (task 48-49) sau khi sửa phát hiện Chặn. **0 phát hiện Chặn chưa đóng.**
