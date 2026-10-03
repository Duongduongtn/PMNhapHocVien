# Sổ bug

> File do `/suabug` ghi. Khác `CHANGES.md`: file kia ghi **thay đổi yêu cầu**, file này ghi **code không làm đúng yêu cầu đã có**.

| # | Ngày | Mức | Story | Bug | Trạng thái | Deploy |
|---|---|---|---|---|---|---|
| 3 | 03/10/2026 | 🟠 Nặng | `QLY-08` · `NAP-01` | Gỡ HV về chờ nạp xong, màn Nạp không tự hiện lại ở "chờ nạp" — phải bấm "Kéo từ VPS" | ✅ Đã sửa | ⬜ (tool chưa lên VPS — có hiệu lực khi chạy lại tool) |
| 2 | 03/10/2026 | 🟠 Nặng | `QLY-01` · `NAP-01` | Tra cứu DB ẩn mọi HV chưa ảnh (TT_XuLy='01') → "Xem trong DB" không thấy HV nạp không ảnh; bộ lọc "Chưa ảnh" luôn rỗng | ✅ Đã sửa | ⬜ (tool chưa lên VPS — có hiệu lực khi chạy lại tool) |
| 1 | 03/10/2026 | 🔴 Chặn | `QLY-08` | Gỡ về chờ nạp rồi nạp lại cùng uuid → HV KHÔNG vào DB nhưng tool báo thành công | ✅ Đã sửa | ⬜ (tool chưa lên VPS — có hiệu lực khi chạy lại tool) |

Chú thích trạng thái: ✅ Đã sửa · 🔄 Đang sửa · ⏳ Đã xếp task · ⬜ Chưa xử

---

## BUG-03 — Màn Nạp không tự làm tươi "chờ nạp" sau khi gỡ HV · 03/10/2026

- **Mức:** 🟠 Nặng (có đường vòng: bấm "Kéo từ VPS"; nhưng sai luồng hằng ngày + dễ tưởng gỡ hỏng)
- **Story:** `QLY-08` (gỡ về chờ nạp) · `NAP-01` (danh sách chờ nạp)
- **Ai báo:** chủ dự án, khi gỡ HV ở Tra cứu DB rồi sang tab Nạp không thấy HV ở hàng chờ
- **Tái hiện:** Tra cứu DB → "Gỡ về chờ nạp" 1 HV (dòng còn trong hàng đợi) → sang tab "Nạp hồ sơ" → HV KHÔNG hiện ở "chờ nạp" cho tới khi bấm "Kéo từ VPS".
- **Nguyên nhân gốc:** `NapHoSo.tsx` tải danh sách chờ nạp (`getDanhSachKeoVe`) **chỉ 1 lần lúc mount** (`useEffect([])`). Thao tác "Gỡ về chờ nạp" nằm ở component `TraCuuDB` (tab Tra cứu) — gọi backend `keo_ve_ve_cho` đưa dòng staging về `'cho'` ĐÚNG, nhưng không chạm state `keoVe` của `NapHoSo`. Chuyển tab chỉ `setMode("nap")`, không tải lại → danh sách cũ. Dữ liệu đúng, chỉ UI không làm tươi.
- **Đã sửa:** `tool/webui/src/pages/tool/NapHoSo.tsx` — đổi effect tải danh sách sang phụ thuộc `[mode]`: khi `mode==='nap'` thì `getDanhSachKeoVe()` (gồm cả lần mở màn). Chỉ đọc SQLite cục bộ, không gọi VPS.
- **Test hồi quy:** KHÔNG viết được test tự động — dự án chưa có hạ tầng test React component (`@testing-library/react`/jsdom chưa cài; vitest chạy node env, chỉ test hàm thuần). Dựng cả bộ cho 1 effect là quá mức. **Bước kiểm tay:** mở tool → Tra cứu DB → "Gỡ về chờ nạp" 1 HV còn trong hàng đợi → bấm tab "Nạp hồ sơ" → HV phải hiện ngay ở nhóm "Cần xử lý" (badge chờ nạp) mà KHÔNG cần bấm "Kéo từ VPS". (Ngoại lệ: HV đã "Bỏ khỏi hàng đợi" trước đó vẫn cần Kéo — đúng thiết kế.)
- **Deploy:** tool chạy cục bộ máy CSDT (chưa lên VPS) → hiệu lực khi chạy lại tool (dev server đã nạp qua HMR).

---

## BUG-02 — Tra cứu DB ẩn học viên chưa có ảnh · 03/10/2026

- **Mức:** 🟠 Nặng (không mất dữ liệu, nhưng HV nạp-không-ảnh vô hình ở Tra cứu DB → không quản lý/thêm ảnh được; "Xem trong DB" không thấy HV vừa nạp)
- **Story:** `QLY-01` (lưới tra cứu) · `NAP-01` (nút "Xem trong DB", dòng 158) · liên quan `QLY-05` (lọc "Chưa ảnh")
- **Ai báo:** chủ dự án, khi nạp Lê Thị Hồng (không ảnh) rồi bấm "Xem trong DB" không thấy tên
- **Tái hiện:** nạp 1 HV KHÔNG ảnh vào khóa (BR-011, TT_XuLy='01') → Tra cứu DB mở khóa đó → HV không xuất hiện trong lưới. Thực chứng: khóa 70004K26B010 có 2 HV '01' + 55 HV '03'; endpoint cũ trả 55, bỏ 2.
- **Nguyên nhân gốc:** `ds_ho_so` (`tool/app/routers/hoso.py`, `GET /local/ho-so`) dùng SP app cũ `usp_NguoiLX_Select_By_MaKH`, SP lọc cứng `AND B.TT_XuLy IN ('03','04')` (`--BaBT them`, "phải nhận ảnh rồi"). HV chưa ảnh (TT_XuLy '01'/'02') bị loại ở nguồn → không thể hiện, và bộ lọc "Chưa ảnh" (QLY-05) không bao giờ có dữ liệu.
- **Đã sửa:** `ds_ho_so` thay EXEC SP bằng SELECT riêng (JOIN `NguoiLX`+`NguoiLX_HoSo`, `WHERE MaKhoaHoc=@ AND TrangThai=1`, **bỏ** điều kiện `TT_XuLy`, giữ nguyên shape trả về). **KHÔNG sửa SP cũ** (dùng chung app cũ → sửa là vỡ báo cáo cũ).
- **Test hồi quy:** `tool/tests/test_hoso.py` — `test_ds_ho_so_liet_ke_ca_hv_chua_anh` (HV DuongDanAnh rỗng vẫn trả về + endpoint KHÔNG gọi SP lọc ảnh + KHÔNG lọc TT_XuLy). Fail trên code cũ, pass trên code mới (168 pytest).
- **Kiểm thật (máy CSDT):** query mới trả 57 HV cho khóa 70004K26B010 (trước 55), có Lê Thị Hồng (MaDK `70004-20261003153838977`). Backend tool đã restart code mới.
- **Deploy:** tool chạy cục bộ máy CSDT (chưa lên VPS) → hiệu lực khi chạy lại tool (đã restart lúc sửa).

---

## BUG-01 — Gỡ về chờ nạp rồi nạp lại → học viên không vào DB · 03/10/2026

- **Mức:** 🔴 Chặn (mất dữ liệu: tool báo nạp thành công nhưng HV không có trong CSDT)
- **Story:** `QLY-08` (liên quan `NAP-01` nạp lô)
- **Ai báo:** chủ dự án, khi test tool trên máy CSDT (nạp Lê Thị Hồng vào khóa 70004K26B010, không thấy trong DB)
- **Tái hiện:** Nạp 1 HV → "Gỡ về chờ nạp" (QLY-08) → "Kéo về từ VPS" → chuẩn bị → "Nạp" lại cùng HV. Tool báo "đã nạp" với số hồ sơ cũ, nhưng tra DB theo CCCD/MaDK → **rỗng**.
- **Nguyên nhân gốc:** `nap.keo_ve_ve_cho()` (QLY-08 bước 5) reset dòng `keo_ve` về `'cho'` nhưng **không xóa vé idempotency trong bảng `nap_xong`** (uuid→MaDK). Vé này do lần nạp đầu tạo ra để chống bấm nạp 2 lần. Khi gỡ về chờ nạp, HV đã bị xóa khỏi CSDT nên vé cũ trỏ tới MaDK đã chết. Lần nạp lại, `nap.nap_mot_hv()` gọi `_done_get(uuid)` thấy vé còn → **trả kết quả cũ, bỏ qua INSERT thật** (short-circuit idempotency bắn nhầm). Hệ quả: không bản ghi mới trong DB, staging bị set lại `'xong'` với MaDK đã xóa.
- **Đã sửa:** `tool/app/nap.py` — `keo_ve_ve_cho()` xóa luôn `DELETE FROM nap_xong WHERE uuid=?` trước khi reset dòng (không phụ thuộc dòng keo_ve còn hay không).
- **Dọn dữ liệu kẹt:** vé `nap_xong` của Lê Thị Hồng (uuid `3e162f1e-…`, MaDK chết `70004-20261002214215390`) đã được gỡ; dòng về `'cho'` để nạp lại.
- **Test hồi quy:** `tool/tests/test_nap_keo.py` — `test_keo_ve_ve_cho_go_ve_khoi_nap_xong` + `test_keo_ve_ve_cho_go_ve_nap_xong_du_da_bo_khoi_hang_doi` (fail trên code cũ, pass trên code mới).
- **Deploy:** tool chạy cục bộ máy CSDT (chưa đóng gói/lên VPS) → có hiệu lực ngay khi chạy lại tool; backend dev đã restart code mới lúc sửa.
