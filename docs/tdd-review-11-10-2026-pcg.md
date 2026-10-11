# Biên bản review TDD — PMCSĐTLX · §11E Phân công GV – xe (PCG)

- **File review:** `docs/TDD.md` §11E.0–11E.9 (đối chiếu PRD `PCG-01..05`, CHANGES #54–#58, TDD-decisions §22, code `routers/phancong.py`, `phancong_service.py`, `phancong_rules.py`)
- **Ngày:** 11/10/2026
- **Lưu ý:** phần lớn §11E vừa được sửa trong chính phiên này (CHANGES #58) nên review nhẹ tay hơn đọc ở phiên mới; đã bù bằng đo thật (12 ms) và đọc code.
- **Số phát hiện:** 14 (Chặn: 0 · Nên sửa: 11 · Ghi nhận: 3) — **tất cả chọn "Sửa"**

## Đã sửa

| # | Điểm | Mức | Phát hiện | Đã sửa thế nào |
|---|---|---|---|---|
| 1.1 | 1 PRD | Nên sửa | TDD ghi "server nhận danh sách GV + phân công mẫu" cho hàng loạt, code không có endpoint đó (UI lặp `/kiem-tra`) | §11E.4 viết lại: hàng loạt chạy ở UI, gồm dời ngày + áp Thực hành |
| 1.2 | 1 PRD | Nên sửa | Bản nháp tự giữ trên máy (#57) không có trong TDD | §11E.0 + sơ đồ vòng đời bản nháp |
| 1.3 | 1 PRD | Nên sửa | §11E.3 `NgayBG+1` và câu hạng GV lệch §11E.7/#56/#58 | §11E.3 khớp |
| 1.4 | 1 PRD | Nên sửa | §11E.6 bước 2 lẫn câu, chưa phản ánh luật dữ liệu cũ mới; "không đổi → 200" nằm sai chỗ | Viết lại bước 2, gỡ bullet trùng §11E.7 |
| 1.5 | 1 PRD | Ghi nhận | Thiếu công thức kết luận rà soát, thiếu `GET /mon`, decisions còn "hai người cùng sửa" | §11E.8, §11E.2, decisions §22 |
| 2.1 | 2 Mơ hồ | Nên sửa | "GV TH" hai nghĩa (loại TH vs có phân công môn 6) | §11E.7 đầu mục: định nghĩa "GV loại TH/AL" và "GV dạy thực hành"; §11E.5/§11E.7 dùng đúng |
| 2.2 | 2 Mơ hồ | Nên sửa | Ghép xe mặc định với GV nhiều đợt cách quãng | §11E.5: `MIN(NgayBD)`→`MAX(NgayKT)` |
| 2.3 | 2 Mơ hồ | Nên sửa | Hợp đồng ngầm `xe` rỗng = Bỏ ghép | §11E.6 bước 1 |
| 2.4 | 2 Mơ hồ | Nên sửa | "Giữ nguyên" chưa định nghĩa so cột nào | §11E.6 bước 2 |
| 2.5 | 2 Mơ hồ | Ghi nhận | Không nói không rollback / cách làm tiếp | §11E.6 bước 4 |
| 3.1 | 3 Edge case | Nên sửa (sát Chặn) | Bản nháp cũ xóa lặng lẽ dòng người khác (phần mềm CDB) vừa ghi giữa chừng | Code + TDD: `dau_van_tay`, 409 `khoa_da_doi`; UI gửi và làm tươi |
| 3.2 | 3 Edge case | Nên sửa | Ghi chồng (bấm đúp, hai tab) nhân đôi dòng vì CDB không UNIQUE | Code + TDD: khóa ghi theo `ma_kh`, 409 `dang_ghi` |
| 3.3 | 3 Edge case | Ghi nhận | Bản ghi nhật ký `dang_ghi` treo mãi khi tool chết | §11E.6 bước 5: quá 1 giờ = gián đoạn (chỉ quy ước hiển thị) |
| 4.1 | 4 Bảo mật | Nên sửa | `dia_diem`/`mon`/mã không giới hạn, môn không tồn tại lọt tới `/ghi` rồi lỗi giữa chừng | Code + TDD: giới hạn đầu vào + luật ⛔ `mon_khong_ton_tai` |
| 4.2 | 4 Bảo mật | Ghi nhận | `xac_nhan_csdl_that` dễ bị hiểu là kiểm soát an ninh | §11E.7 ghi rõ là cổng thao tác |

Điểm 5 (hiệu năng) và 6 (sơ đồ) không có phát hiện Chặn: đo `/kiem-tra` 12 ms ở khóa 54 dòng, hàng loạt 30 GV ≈ 0,4 giây; đã chèn 3 sơ đồ ASCII (vòng đời bản nháp §11E.0, hai tầng cờ §11E.1, luồng ghi §11E.6).

## Cố tình bỏ qua

Không có.

## Hoãn lại

| # | Phát hiện | Chờ gì |
|---|---|---|
| — | Test frontend (vitest) cho logic trong TSX: khôi phục bản nháp, dời ngày thực hành, chọn GV hợp hạng | Tách hàm khỏi `PhanCongTheoKhoa.tsx`/`BuocPhanCong.tsx` (sửa code, chưa duyệt) |
| — | E2E Playwright | Cài Playwright + API giả |
| — | Ghi thật + đối chiếu phần mềm CDB; gói DKKH/BC1 có chứa GV/xe không | Nghiệm thu máy CSDT (Checkpoint 22), hỏi hỗ trợ CDB |

## Kết luận

**TDD §11E đủ để dùng**, không còn phát hiện Chặn chưa đóng. Hai chỗ đáng kể nhất đã đóng bằng code + test: 3.1 (xóa nhầm dòng người khác) và 2.1 (hai nghĩa của "GV TH").
