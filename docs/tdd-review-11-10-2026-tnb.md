# Biên bản review TDD — PMCSĐTLX · §11F Tốt nghiệp & Báo cáo 2 (TNB)

- **File review:** `docs/TDD.md` §11F.0–11F.8 (đối chiếu PRD `TNB-01..07`, CHANGES #60/#61, TDD-decisions §23, định nghĩa SP + dữ liệu DB Nạp `GPLX_CSDT`)
- **Ngày:** 11/10/2026
- **Lưu ý:** §11F được viết ở phiên khác; phiên này đọc như người lạ. Đã bù bằng đọc định nghĩa SP thật và đo dữ liệu (chỉ SELECT).
- **Số phát hiện:** 25 (Chặn: 5 · Nên sửa: 17 · Ghi nhận: 3) — **tất cả chọn "Sửa"** (mục #1 user chọn phương án A)

## Đã sửa

| # | Điểm | Mức | Phát hiện | Đã sửa thế nào |
|---|---|---|---|---|
| 1 | 1 PRD | **Chặn** | "HV đang ở BC2 khác sẽ bị chuyển" mâu thuẫn với `khong_duoc ∋ 11`; SP không trả HV `11`; chuyển bằng `ThemHSBC2` đặt `TT_XuLy_Old='11'` → HV kẹt `11` không BC2 | §11F.4: bỏ chuyển; HV ở BC2 mở khác → `khong_duoc`; decisions §23 |
| 2 | 1 PRD | **Chặn** | Không đọc lại `BaoCaoII.TrangThai` trước khi thêm/gỡ (PRD TNB-04 edge) | §11F.4 bước ②, §11F.7 ⛔ |
| 3 | 1 PRD | Nên sửa | TNB-01: kiểm trùng ngay khi gõ, "Xem lại", điền sẵn sổ, đánh số liên tiếp không có chỗ trong TDD | §11F.2 + `POST /tot-nghiep/xem-lai` |
| 4 | 1 PRD | Nên sửa | Bước ① "khóa chưa có BC2" chưa định nghĩa | §11F.4 luồng ① |
| 5 | 1 PRD | Ghi nhận | Ghi số giấy lần đầu cho HV ≥ 11 vs "chặn hủy/sửa ≥ 11" | §11F.2 |
| 6 | 2 Mơ hồ | **Chặn** | HV `14/17/18` cùng khóa không thuộc nhóm nào | §11F.4 `thi_lai` bất kể khóa |
| 7 | 2 Mơ hồ | Nên sửa | `san_sang` "ô tô 09" chồng `can_xem` "09 thiếu số giấy" | §11F.4 thêm `SoGiayCNTN<>''` + thứ tự xét |
| 8 | 2 Mơ hồ | Nên sửa | `thi_lai_thang` lọc hay chỉ quyết định tích | §11F.4: trả đủ + `tuoi_thang` |
| 9 | 2 Mơ hồ | Nên sửa | Luồng 3 bước không nói lấy BC1 ở đâu | §11F.3: suy từ khóa; khóa chưa có BC1 hiện mờ |
| 10 | 2 Mơ hồ | Nên sửa | `TongSoThiSinh` ô tô trong `/lap` | §11F.3: tính trước Insert, sau đọc lại |
| 11 | 2 Mơ hồ | Nên sửa | Hoàn tác "lô gần nhất" của cái gì | §11F.4: của BC2 đang xem, một lần |
| 12 | 2 Mơ hồ | Nên sửa | Hoàn tác cứu tự chặn bởi luật đích | §11F.5: miễn luật đích |
| 13 | 3 Edge | Nên sửa | Khóa theo BC2 không loại trừ hai BC2 ghi cùng HV | §11F.0 khóa chung `tnbc2_ghi` + §16.1 |
| 14 | 3 Edge | Nên sửa | Đứt giữa chừng: nhật ký ghi sau cùng; "Làm tiếp" gọi lại SP | §11F.4 ghi nhật ký từng HV, không gọi lại SP |
| 15 | 3 Edge | Nên sửa | Bấm hai lần / F5; trùng số giấy với chính mình | §11F.4 `lo_id` idempotent; §11F.2 loại trừ chính HV |
| 16 | 3 Edge | Nên sửa | 91 HV `MaBC2` trỏ BC2 không tồn tại | §11F.4 `san_sang` coi như rỗng |
| 17 | 3 Edge | Ghi nhận | 2 HV `11` trong BC2 đã đóng | §11F.7 ℹ "mở lại ở PM cũ" |
| 18 | 3 Edge | Ghi nhận | Tích 0 HV / khóa 0 ứng viên | Ghi trong giao diện (nút khóa; `giai_thich_khong_hien`) |
| 19 | 4 Bảo mật | **Chặn** | Xóa BC2 "chỉ 0 HV" không nói đếm thế nào; SP không kiểm HV, không FK | §11F.6 đếm `MaBC2` mọi `TT_XuLy` trong khóa |
| 20 | 4 Bảo mật | Nên sửa | Luật ⛔ chỉ nêu, không nói thi hành ở máy chủ | §11F.7 đầu mục |
| 21 | 4 Bảo mật | Nên sửa | Giới hạn đầu vào, độ dài cột thật | §11F.1 bảng độ dài, §11F.7 giới hạn |
| 22 | 4 Bảo mật | Nên sửa | Nhật ký/lỗi có thể chứa CMT/họ tên | §11F.0 |
| 23 | 5 Hiệu năng | **Chặn** | `@MaKH=<khóa>` không trả thi lại khóa khác; SP thiếu cột trạng thái | §11F.4: gọi một lần `@MaKH=''` + `SELECT` bổ sung |
| 24 | 5 Hiệu năng | Nên sửa | Đếm theo khóa / theo BC2 dễ thành 460 / 455 lần quét 40.000 dòng | §11F.4 ①, §11F.6 `GROUP BY MaBC2` |
| 25 | 5 Hiệu năng | Nên sửa | `/lap` đồng bộ hàng nghìn lượt gọi DB | §11F.4 chạy nền + `GET /bc2/lo/{lo_id}`; chỉ tiêu §11F.8 |

Điểm 6: chèn 3 sơ đồ ASCII (vòng đời trạng thái §11F.2 thay sơ đồ cũ; thứ tự xét nhóm và luồng ghi §11F.4).

## Cố tình bỏ qua

| # | Phát hiện | Mức | Vì sao chấp nhận |
|---|---|---|---|
| 13b | Khe còn lại: PM cũ không dùng khóa `tnbc2_ghi`, giữa đọc lại và gọi SP vẫn có khe nhỏ | Thấp | Tool một máy, ghi ngắn; SP không có điều kiện trạng thái và không được ghi trực tiếp. Giảm nhẹ bằng khóa chung + đọc lại sát trước SP + kiểm `TT_XuLy_Old='11'` sau ghi. Ghi ở §16.1 (11/10/2026) |

## Hoãn lại

| # | Phát hiện | Chờ gì |
|---|---|---|
| H1 | PRD TNB-04 ("Cần xem … sẽ bị chuyển", edge) và TNB-03 ("chọn BC1 (bắt buộc)") đang nói khác TDD sau review | User chạy `/capnhat`; kiểm lại mockup `ui-mock/tnbc2.html` |
| H2 | Quy tắc số giấy CNTN liên tiếp (`N1|7282` → ?), số sổ/quyết định theo khóa; chụp trước/sau PM cũ (`NgaySua`, `NguoiSua`, `Transfer_flag`) | Nghiệm thu máy CSDT (decisions §23 "Còn mở") |

## Kết luận

TDD §11F **đủ để bắt đầu lập kế hoạch** sau khi PRD được `/capnhat` theo H1. Số phát hiện **Chặn chưa đóng ở TDD: 0**; còn 1 việc PRD (H1) và 1 việc nghiệm thu (H2).
