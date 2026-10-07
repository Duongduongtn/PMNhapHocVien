# Phiếu nghiệm thu tại máy CSDT — PMCSĐTLX

> Gộp các hạng mục **đã code xong nhưng chờ verify ở máy thật** (máy dev không ghi được vào CDB thật + ổ ảnh `D:\GPLXCSDT\ANHCDUNG`). Chi tiết từng bullet nằm ở **Checkpoint tương ứng trong `docs/BUILD-PLAN.md`** — phiếu này chỉ xếp thứ tự chạy + nhắc đối chiếu, KHÔNG chép lại (tránh lệch; BUILD-PLAN là nguồn).
> Lập 07/10/2026. Đánh ✅/❌ vào đây khi chạy; mục nào pass thì lên PRD đổi story ⚠️ → ✅ (hoặc hỏi user chốt Feature).

## Chuẩn bị (đầu buổi)

- [ ] Mang **exe tool mới nhất** (`tool/dist/pmcsdtlx-tool/`) sang máy CSDT, hoặc build lại ở đó. Máy CSDT phải thấy ổ ảnh `D:\GPLXCSDT\ANHCDUNG` + DB `GPLX_CSDT`/`GPLX_CDB_CSDT`.
- [ ] So giờ máy CSDT ↔ VPS (Asia/Saigon) — MaDK/tên file `.jp2` theo timestamp máy (Checkpoint 5).
- [ ] Mở sẵn **phần mềm CDB cũ** để đối chiếu từng bản ghi.

## Nhóm 1 — Tool nạp & quản lý HV (Checkpoint 6, 7)

> Stories: QLY-01/02/03/05/07 · NAP-03/04. Ghi vào `GPLX_CSDT`.

- [ ] **QLY-05/NAP-04** — nạp/thay ảnh 1 HV → mở **app cũ**: ảnh `.jp2` 353×471 nền trắng mở được, 5 cột ảnh đúng, `TT_XuLy` KHÔNG tụt (bug BUG-13 đã vá) → Checkpoint 6.
- [ ] **QLY-01** — Tra cứu DB: avatar lazy, modal ảnh + đường dẫn, file mất → cảnh báo không vỡ lưới → Checkpoint 6.
- [ ] **QLY-02** — đổi khóa cùng hạng → file `.jp2` di chuyển đúng + `DuongDanAnh` cập nhật.
- [ ] **QLY-03** — xóa HV: khóa chưa BC1 xóa được; khóa **BC1 → chặn 409** → Checkpoint 6.
- [ ] **QLY-07** — đổi nền cả khóa: tiến độ chạy, `_BACKUP` giữ bản gốc, chạy lần 2 KHÔNG đè backup, khóa BC2 giữ HV trong Báo cáo → Checkpoint 7.
- [ ] **QLY-06** — "Tạo thêm hồ sơ khóa khác hạng": điền sẵn từ HV cũ → nạp MỚI (MaDK mới, chung SoCMT), đăng ký cũ giữ nguyên.

## Nhóm 2 — Gỡ/đồng bộ VPS↔CSDT (Checkpoint 8) — ⚠ cần VPS

> Stories: THU-05 · QLY-08 · QLY-09 · NAP-01 (đồng bộ xóa). Server đã deploy.

- [ ] **QLY-08** — gỡ HV khóa chưa BC1 → biến khỏi CSDT + về hàng chờ nạp; khóa BC1 → chặn; VPS lỗi sau khi xóa CSDT → báo + "Thử lại" → Checkpoint 8.
- [ ] **QLY-09** — đối soát VPS↔CSDT: tạo lệch thử (phantom/CSDT-có-VPS-chưa/importing treo) → panel chỉ hiện dòng lệch + nút sửa 1 chạm chạy đúng → Checkpoint 10.
- [ ] **NAP-01** — "Kéo về": HV đã xóa ở app biến khỏi hàng chờ; dòng đang khóa KHÔNG bị xóa nhầm.

## Nhóm 3 — Tra cứu CDB đích (Checkpoint 14) — ghi vào GPLX_CDB_CSDT

> Stories: TCB-01/02/03/04. Máy dev chỉ verify ĐỌC + các mốc CHẶN; luồng GHI happy-path hoãn sang đây.

- [ ] **TCB-02** thay ảnh CDB: ghi đè `.jp2` + `_BACKUP.jp2` (chỉ nếu chưa có) + UPDATE `ChatLuongAnh`/`NgayThuNhanAnh`; cho cả DKKH/BC1 (cảnh báo).
- [ ] **TCB-03** sửa nhân thân CDB: nhánh **chưa DKKH → sửa được** (nhánh DKKH→409 đã verify máy dev).
- [ ] **TCB-04** xóa/đổi khóa CDB: HV chưa BC1 → chạy; BC1 → chặn (cần HV test chưa BC1).

## Nhóm 4 — Cập nhật kết quả đào tạo (Checkpoint 16) — ghi vào GPLX_CDB_CSDT

> Stories: KQD-01..06. Ghi điểm `TT_XuLy` 03→09/10, KHÔNG kết xuất XML.

- [ ] **KQD-02** — nhập điểm 1 HV đạt → mở **phần mềm CDB** đối chiếu điểm/`TT_XuLy=09`/`SoGiayCNTN` khớp; HV `12`/`13` → nút Lưu mờ, không gọi SP.
- [ ] **KQD-04** — HV `14`/`90` sửa điểm + giải trình → `GiaiTrinh` ghi được.
- [ ] **KQD-05** — mở khóa: còn gói chưa gửi → mở + lùi mọi HV `12` cơ sở về 09/10; gói gửi hết → 409/M1; `13` không mở.
- [ ] **KQD-06** — sửa lẻ 1 môn (giữ quy đổi môn cũ) + xóa điểm (về `03`, sạch 5 điểm/3 cờ); HV ngoài 09/10 → 409.

## Nhóm 5 — App web OCR trên iPhone (Checkpoint 17) — KHÔNG ở máy CSDT

> Story: THU-06. Đã deploy production `nhaphocvien.trungtamthanhdat.com`.

- [ ] **Nạp bản mới trên iPhone:** đóng hẳn Safari/xóa dữ liệu site (PWA cache SW) rồi mở lại → `/app/quet` thấy nút "Chụp ảnh thẻ (tự đọc)".
- [ ] Chụp CCCD thật rõ → OCR điền đúng **5 trường** (CCCD/họ tên/ngày sinh/giới tính/nơi TT); **ngày cấp để trống** (nhập tay).
- [ ] Ảnh mờ/OCR fail → báo rõ, không điền bừa; CCCD sai → chặn lưu.
- [ ] **Đánh giá độ chính xác tiếng Việt có dấu** của Tesseract.js — nếu quá kém: tăng sửa tay hoặc xin duyệt eKYC (TDD §6.7 "mở kiểm").

## Nhóm 6 — Đóng gói & phiên tool (Checkpoint 15) — máy sạch

> Stories: DGT-01..04.

- [ ] **DGT-03** máy sạch → wizard 3 bước; đã có cấu hình → vào thẳng; key.bin hỏng → wizard + cảnh báo.
- [ ] **DGT-04** đăng nhập 1 lần → tắt/mở exe vào thẳng; qua 8h vẫn kéo VPS được (refresh ngầm); admin khóa TK → bị đá khi refresh.

## Sau khi nghiệm thu

- [ ] Mục nào pass → PRD đổi story ⚠️ → ✅; Feature đủ story + user duyệt → "✅ Đã chốt — dd/mm/yyyy".
- [ ] Trước go-live: chạy **`/baomatdeploy`** (soát bảo mật toàn diện) + **`/soatdeploy`** nếu có đổi cấu hình/DB.
