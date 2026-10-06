# Biên bản review TDD — PMCSĐTLX

- **File review:** docs/TDD.md §11B.7 (sửa nhân thân Nạp QLY-01 + TCB-03)
- **Phạm vi:** hẹp — sau CHANGES #40 (nơi cấp DM_DonViGTVT→DM_DVHC + '00' Cục QLHC + mở rộng modal QLY-01)
- **Ngày:** 06/10/2026
- **Lưu ý:** §11B.7 (#40) viết trong CÙNG phiên review → bản này nhẹ tay hơn thực tế; code đã viết+test+verify live (review hồi tố tìm lỗ hổng thiết kế).
- **Số phát hiện:** 2 (Chặn: 0 · Nên xác nhận: 1 · Ghi nhận: 1)

## Đã sửa

| # | Điểm | Mức | Phát hiện | Đã sửa thế nào |
|---|---|---|---|---|
| 1 | 1+4 | Nên xác nhận | Mã `'00'` đa nghĩa: `DM_DVHC`→Cục QLHC, `DM_DonViGTVT`→Cục CSGT. Ta hiển thị qua DM_DVHC (đúng) nhưng view CDB nào tra qua DM_DonViGTVT sẽ ra nhãn sai | +Risks §16.1 (rủi ro '00' đa nghĩa) + ghi chú §11B.7 trỏ §16; cần hỏi người quản CDB tra theo bảng nào |
| 2 | 3 | Ghi nhận | Edge "xã cũ trước sáp nhập" (combo Xã trống) §11B.7 mới ghi cho TCB-03, nhưng QLY-01 mở rộng cũng gặp y hệt | +câu ở §11B.7 bullet #40: edge áp CẢ QLY-01 lẫn TCB-03 |

## Cố tình bỏ qua

(không có — 0 phát hiện Chặn)

## Hoãn lại

| # | Phát hiện | Chờ gì |
|---|---|---|
| 1 | Xác nhận NoiCapCMT chính thức tra theo `DM_DVHC` hay `DM_DonViGTVT` ở báo cáo/view CDB | Hỏi người quản CDB; nếu dùng DM_DonViGTVT thì cân nhắc đổi quy tắc nơi cấp |

## Các điểm OK (không phát hiện)

- **Điểm 2 (logic):** bỏ-trống-giữ-cũ, địa chỉ đi theo cặp, mặc định '00' — rõ ràng, có ví dụ.
- **Điểm 4 (bảo mật):** endpoint sửa gác session + chặn BC1 trên đường lưu; SQL parameterized; '00' mã cố định. Không mở bề mặt mới.
- **Điểm 5 (hiệu năng):** `/lich-su` resolve tên 2 truy vấn gộp (không N+1); chi-tiet scalar subquery TOP 1.
- **Điểm 6 (sơ đồ):** không cần sơ đồ mới (thuần field mapping).

## Kết luận

TDD §11B.7 **đủ để code** (code thực tế đã xong + verify). **0 Chặn chưa đóng.** 1 việc hoãn: xác nhận bảng tra NoiCapCMT với người quản CDB (rủi ro nhãn '00' ở báo cáo CDB).
