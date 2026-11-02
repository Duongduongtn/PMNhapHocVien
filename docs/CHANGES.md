# Sổ thay đổi

> File do `/capnhat` ghi. Các lệnh khác đọc file này để biết tính năng nào đã bỏ / quyết định nào đã đổi.

| # | Ngày | Loại | Mã | Thay đổi | PRD | TDD | Màn hình | Code |
|---|---|---|---|---|---|---|---|---|
| 88 | 02/11/2026 | ✏️ Sửa | `KQD-08` | Nạp giờ/km nhận cả mẫu PDF DAT cũ 7 cột và mới 9 cột, tìm cột theo tiêu đề; mẫu lạ báo rõ. | ✅ | ✅ §11D.10 | — | ✅ |
| 87 | 02/11/2026 | ✏️ Sửa (UX) | `THU-01` | Thông báo đã gửi nêu tên học viên, để làm liên tiếp biết vừa gửi hồ sơ nào. | ✅ | — | — | ✅ `210c5e1` |
| 86 | 02/11/2026 | ✏️ Sửa (UX) | `THU-01` · `THU-07` | Báo lỗi form dễ sửa trên điện thoại: tự tới ô sai đầu tiên, câu lỗi tự mất; GPLX không đỏ khi chưa nhập; chữ ô nhập 16px dưới 1024px. | ✅ | — | — | ✅ `f8f3fb7` |
| 85 | 02/11/2026 | 🐛 Sửa + ⚙️ | `THU-05` · `NAP-07` | Job dọn 30 ngày xóa cả hồ sơ xóa mềm; cài sao lưu DB đêm trên VPS; workflow gọi cả API, sửa dọn image. | — | ✅ | ✅ mock Nơi cấp | ✅ |
| 84 | 02/11/2026 | ✏️ Sửa (user chốt) | `NAP-07` · `THU-07` | **Giữ Cục QLHC mã `00`** theo DB đích; thêm script bật ở `DM_DonViGTVT` DB Nạp. | ✅ v4.26 | ✅ v6.30 | — | ✅ |
| 83 | 02/11/2026 | ✏️ Sửa (khớp form cũ) | `NAP-07` · `THU-07` | **Rà DB + DLL phần mềm cũ:** chặn trùng hạng đăng ký, bắt buộc ngày cấp + trúng tuyển, thứ tự ngày, 18 tuổi; Nơi cấp đổi sang `DM_DonViGTVT` (65 đơn vị). Cách lưu `\|` có bằng chứng. | ✅ v4.25 | ✅ v6.29 | ✅ | ✅ |
| 82 | 02/11/2026 | ✏️ Sửa (sau `/reviewtdd`) | `NAP-07` · `THU-07` | **`/reviewtdd` §10.6 (2 Chặn, 11 Nên sửa, 2 Ghi nhận):** đã sửa TDD; user chốt cờ "App web có bản mới". Hoãn: hồ sơ xóa mềm còn giữ số căn cước. | ✅ v4.24 | ✅ v6.28 | — | ✅ chưa deploy |
| 81 | 02/11/2026 | ➕ Thêm | `NAP-07` · `THU-07` | **GPLX đã có:** nhập ở app web, tool tự điền và sửa được; nhiều bằng luật cũ + luật mới (nối `\|`); chip + lọc ở màn Nạp; không đổi schema DB Nạp; Sync giữ nguyên. Số story 61→63. | ✅ v4.23 | ✅ v6.27 §10.6 + decisions §28 | ✅ mock `ui-mock/gplxdaco.html` đã duyệt + SCREENS #36 | ✅ chưa deploy |
| 80 | 16/10/2026 | ✏️ Sửa (sau `/reviewtdd`) | `NAP-05` · `NAP-01` | **`/reviewtdd` "Chọn in GPLX" (0 Chặn, 4 Nên sửa):** làm rõ server dùng đúng giá trị client gửi; bảng nháp §9.3a +cột; "Phục vụ" +NAP-01; **user chốt (A):** đổi sang khóa khác loại mô tô↔ô tô thì **xóa lựa chọn tay**, ô về mặc định khóa mới; chọn lại đúng mặc định = chưa đổi (lưu trống). NAP-05 giữ ⚠️. Số story giữ 61. | — | ✅ v6.26 | — | ✅ `NapHoSo.tsx` + 2 ca e2e |
| 79 | 16/10/2026 | ✏️ Sửa (yêu cầu đổi) | `NAP-05` · `NAP-01` | **Ô "Chọn in GPLX" thay cho `CHON_IN_GPLX=2` gán cứng:** màn Nạp hiện ô 3 giá trị (1 ghép · 2 có thời hạn · 3 không thời hạn) điền sẵn theo hạng khóa (mô tô `A*` → 3, ô tô → 2) kèm tên loại in bằng chữ, đổi được từng học viên, lưu cùng nháp; server mặc định theo hạng khi không gửi, ngoài {1,2,3} → 422; Đồng bộ CDB chép nguyên giá trị sang DB đích (NULL → 0). **Hạ NAP-05 ✅→⚠️** (chờ nghiệm thu ghi thật máy CSĐT); NAP-01 giữ 🔄. Số story giữ 61. | ✅ v4.22 | ✅ v6.25 §10 + decisions | — (màn thật đã dựng) | ✅ pytest 978 · vitest 147 · Playwright 162 (chưa commit) |
| 78 | 16/10/2026 | ✏️ Sửa (đồng bộ PRD + mock sau `/reviewtdd`) | `KQD-01` · `KQD-04` · `KQD-07` | **Đồng bộ PRD v4.20 + mock với TDD v6.23 §11D.13:** tab "Sở từ chối" → **"Cần xử lý"** (gồm `14` + `90` Không đạt/trống kết luận) + tab "Không đạt"; chip đỏ "Đang giải trình nhưng không đạt — sẽ không kết xuất" + chip cam "Thiếu giải trình — chưa kết xuất được"; **cảnh báo bắt buộc "chưa giải trình thì không kết xuất được"** (user chốt) ở 4 chỗ; giải trình riêng được giữ + ô tích ghi đè; lô kiểm đủ điều kiện; mất kết nối báo "không rõ kết quả"; mẫu theo cơ sở; KQD-07 +3 chip lý do. KQD-01/03/04/07 đã ⏳ từ #77. Số story giữ 61. | ✅ v4.20 | ✅ (đã sửa ở `/reviewtdd` v6.23) | ✅ mock `ui-mock/ketqua.html` + SCREENS #21 (chờ user duyệt) | ⬜ |
| 77 | 16/10/2026 | ✏️ Sửa (yêu cầu đổi) | `KQD-04` · `KQD-01` · `KQD-03` · `KQD-07` | **HV Sở từ chối sửa điểm xong tự sang "Đang giải trình" + giải trình hàng loạt + cột Trạng thái dễ đọc.** Lưu HV `14` → `90` khi Đạt + có giải trình (Không đạt/thiếu giải trình giữ `14`) vì phần mềm CDB chỉ kết xuất `09`/`90` và không thủ tục nào đặt `90`; giải trình chung của khóa + mẫu lưu sẵn + tích nhiều HV chuyển một lượt; lưới thêm cột Trạng thái (chip + việc cần làm) + dải tab có đếm + lý do Sở từ chối trên dòng; "còn sót kết xuất" (KQD-03) và kiểm trước kết xuất (KQD-07) gồm `90` Đạt. **Hạ KQD-04 ⚠️→⏳, KQD-01 ✅→⏳, KQD-03 ⚠️→⏳, KQD-07 ✅→⏳.** Ghi bù: ô Code #65/#68 → ✅ (PRD KQD-07 đã ✅ kể cả UI). Số story giữ 61. | ✅ v4.19 | ✅ v6.22 §11D.13 + decisions §27 | 🟡 mock `ui-mock/ketqua.html` đã cập nhật (chờ user duyệt) + SCREENS #21 | ⬜ |
| 76 | 12/10/2026 | ✏️ Sửa (đồng bộ tài liệu + 6 sửa code) | `KQD-10` | **`/reviewtdd` §11D.12 (subagent soát độc lập):** xếp tên theo thanh điệu từng âm tiết (Hòa=Hoà) · viền xám/chân trang 10/hàng 5,9 đúng mẫu · footer 0,3 · độ rộng cột theo chữ hoa · chiều cao khối cơ sở tự tăng · dòng giải thích HV thiếu điểm · §11D.6 `POST xuat-excel`. | ✅ | ✅ | — | ✅ |
| 75 | 12/10/2026 | ➕ Thêm + ✏️ Sửa | `KQD-10` · `KQD-09` | **Xuất Sổ theo dõi kết quả học tập (mẫu Phụ lục VI TT17):** nút riêng ở màn Cập nhật KQĐT, 1 sheet A4 dọc bám file mẫu, lặp 2 hàng tiêu đề + `Trang x/y`, xếp theo tên tiếng Việt, kết quả chỉ khi đủ 5 điểm, không bìa/chữ ký, lưu vào `output`. KQD-09: `Ngày lập` chỉ `dd/mm/yyyy`. | ✅ | ✅ | ✅ (SCREENS #21) | ✅ |
| 74 | 12/10/2026 | ✏️ Sửa | `KQD-09` | **Dùng thử:** (1) file Excel **lưu mặc định vào thư mục `output` của phần mềm** + báo đường dẫn + nút "Mở thư mục" (thay "tải về"); (2) bỏ **dấu chấm thừa** ở Giờ sân/Km sân (`34.` → `34`). | ✅ | ✅ | — | ✅ |
| 73 | 12/10/2026 | ✏️ Sửa (đồng bộ tài liệu + 4 sửa code) | `KQD-09` | **`/reviewtdd` §11D.11 (subagent soát độc lập):** chống formula injection + làm sạch ký tự điều khiển · `PUT /co-so` gác phiên · hạng hòa phiếu ổn định · nhãn "Chưa có kết luận" · TDD v6.18 (sơ đồ, bảng cột→nguồn, lỗi/Expose-Headers, hệ quả §25). | ✅ | ✅ | — | ✅ |
| 72 | 12/10/2026 | ➕ Thêm | `KQD-09` | **Xuất Excel kết quả học tập theo từng khóa:** nút ở màn Cập nhật KQĐT, 1 sheet bảng chi tiết 22 cột + khối đầu (cơ quan/cơ sở/khóa/ngày lập/người lập), mọi HV đang hoạt động, tên cơ sở nhập ở Cấu hình, ngày xét hoàn thành = ngày thi khóa. Chỉ đọc DB. | ✅ | ✅ | ✅ (SCREENS #21, không route mới) | ✅ |
| 71 | 12/10/2026 | ✏️ Sửa (đồng bộ tài liệu + 2 sửa code) | `KQD-08` | **`/reviewtdd` §11D.10 (subagent soát độc lập):** chốt endpoint theo code + sơ đồ/bảng tình trạng · sửa code: "Chọn tất cả" chỉ tick `khop`, dòng vượt trần tra lý do không bị báo "không tìm thấy" · ghi nhận 3 rủi ro. Không đổi yêu cầu PRD. | — | ✅ | — | ✅ |
| 70 | 12/10/2026 | ✏️ Sửa | `KQD-08` · `KQD-02` | **Chốt 6 điểm sau /kiemthu (user gật đề xuất):** ① chỉ sửa giờ/km → ghi riêng 2 cột, đủ cả giờ lẫn km, HV 03/04/09/10/14/90 · ② tick tay dòng chưa chạy DAT → điền sẵn `0` giờ · ③ làm tròn 2 chữ số khi mở lại (`18,456`→`18,46`) chấp nhận · ④ sửa code: mã khóa đọc chữ+số · ⑤ sửa code: UPDATE thêm `TrangThai = 1` · ⑥ giờ nhận `hh:mm:ss`. | ✅ | ✅ | — | ✅ |
| 69 | 12/10/2026 | ➕ Thêm + ✏️ Sửa | `KQD-08` · `KQD-02` | **Nạp giờ/km thực hành đường từ file PDF DAT theo khóa (KQD-08 mới)** — chọn PDF → kiểm mã khóa → bảng xác nhận cũ→mới → lưu hàng loạt, ghi riêng 2 cột giờ/km. **Sửa KQD-02:** ô Giờ đường nhận `hh:mm` tự đổi thập phân; mở lại hiện sẵn giờ/km đã lưu (sửa lỗi SP ghi NULL đè giờ cũ); hạ ⚠️→⏳ Todo. | ✅ | ✅ | ✅ (SCREENS #21 + #35, chưa có mock) | ✅ |
| 68 | 12/10/2026 | ✏️ Sửa | `KQD-07` · `PCG-06` | **Ghi quyết định đã chốt + đồng bộ TDD với code:** KQD-07 môn bắt buộc = cả 5 môn mọi hạng ô tô, hạng mô tô không xét (đếm riêng), chỉ nhắc không chặn, KQD-02 giữ nguyên; chốt UX qua mock (ẩn chip giờ/km khi chưa có điểm; khóa mô tô hiện "không xét kết quả đào tạo"). PCG-06 ghi lại cách đọc dữ liệu thực tế. Mock `ui-mock/ketqua.html` + `ui-mock/phancong.html` | ✅ v4.11 | ✅ §11D.9 + §11E.10 (v6.13) | ✅ 2 mock HTML (ui-demo #33/#34 giữ ⬜) | ✅ KQD-07 (UI task 120) · ⬜ PCG-06 UI task 122 |
| 67 | 12/10/2026 | ✏️ Sửa | `QLY-07` | **Đổi nền cả khóa ghi đè ĐÚNG file ở `DuongDanAnh` hiện có** (2 DB Nạp + đích dùng chung 1 file vật lý), không tạo file mới/không đổi `DuongDanAnh`; chỉ cập nhật cột ảnh; sao lưu thống nhất `<tên>_BACKUP.jp2` cùng thư mục. QLY-07 hạ ⚠️ → ⏳ Todo. | ✅ v4.10 | ✅ §11.6 (v6.12) | ✅ SCREENS #15 ghi chú | ⬜ |
| 66 | 12/10/2026 | ➕ Thêm | `PCG-06` | **Hạn giấy tờ (tab thứ 3 màn Phân công, chỉ đọc, toàn cơ sở):** xe hết hạn / còn ≤ 30 ngày (giấy phép tập lái + kiểm định), **GPLX giáo viên** hết hạn / còn ≤ 30 ngày, GV/xe ngưng còn phân công ở khóa chưa bế giảng — mỗi dòng kèm khóa đang dùng. Tư vấn từ schema DB đích + dữ liệu thật 12/10/2026. | ✅ v4.9 | ✅ §11E.10 (v6.11) | ⬜ SCREENS #34 chưa có mock | 🟡 backend xong, UI task 122 |
| 65 | 12/10/2026 | ➕ Thêm | `KQD-07` | **Kiểm trước kết xuất (theo từng khóa, chỉ đọc):** nút ở màn Cập nhật KQĐT liệt kê HV chưa đủ — Chưa có điểm / Thiếu môn bắt buộc của hạng / Thiếu giờ-km thực hành / Thiếu kết luận; dùng lại luật ô bắt buộc của KQD-02; chỉ cảnh báo, không chặn. | ✅ v4.9 | ✅ §11D.9 (v6.11) | ⬜ SCREENS #33 chưa có mock | ✅ (backend task 119 + UI task 120, PRD KQD-07 ✅ 12/10) |
| 64 | 11/10/2026 | ✏️ Sửa (đồng bộ tài liệu) | `TNB-02` · `TNB-03` · `TNB-04` · `TNB-05` · `TNB-06` · `TNB-07` | **Ghi lại hành vi thực tế khi dựng UI task 106-115 + 2 sửa backend (ngày BC1; hoàn tất lô cứu dở)**: tích lẫn + luật nút Hủy/Chọn tất cả · ngày BC1, ngày bắt buộc, `thu_lai` · chốt payload bước ③, tự làm tươi, hạn chế F5 · lỗi lô Gỡ/Hoàn tác · mục IT + khóa chưa bế giảng + hoàn tất lô dở · nhật ký không PII · "chọn loại hạng" | ✅ v4.8 | ✅ v6.10 | ✅ SCREENS #26-#32 | ✅ |
| 63 | 11/10/2026 | ✏️ Sửa (đồng bộ tài liệu) | `TNB-01` · `TNB-05` · `TNB-06` | **Ghi lại hành vi thực tế của backend TNB task 96–105 vào TDD §11F + PRD v4.7** (không đổi yêu cầu): API đầy đủ + mã lỗi; luật trùng số giấy chỉ chặn khi đổi sang số HV khác, HV chưa tới bước tốt nghiệp bị chặn, cấp giấy cần số sổ + QĐ, bộ sổ chung cả lượt; gỡ tay `Old='11'` bị chặn; không xóa BC2 đã đóng; hoàn tác cứu dùng nhật ký tool; `{ma:path}` | ✅ v4.7 | ✅ v6.9 | — | ✅ backend · ⬜ UI |
| 62 | 11/10/2026 | ✏️ Sửa | `TNB-03` · `TNB-04` · `TNB-05` | **Đồng bộ PRD + mockup với TDD §11F v6.8 sau /reviewtdd:** bỏ "HV đang ở BC2 khác sẽ bị chuyển" (→ "Không đưa được", gỡ khỏi BC2 đó trước); BC1 suy từ khóa, khóa chưa có BC1 hiện mờ ở bước ①; Thi lại tính cả cùng khóa; ô tô `09` cần có số giấy | ✅ v4.6 | ✅ v6.8 (đã sửa ở /reviewtdd) | ✅ `ui-mock/tnbc2.html` + SCREENS #29 | ✅ backend 96-105 · ✅ UI 106-115 (trừ dán danh sách + xử lý ngoại lệ tại chỗ → task 116-117) |
| 61 | 11/10/2026 | ✏️ Sửa (UX + luồng) | `TNB-03` · `TNB-04` · `TNB-05` · `TNB-06` | **Thiết kế lại luồng thêm HV vào BC2 theo phản hồi mockup v1:** 3 bước một nút làm xong; 4 nhóm HV (Sẵn sàng tích sẵn / Thi lại không tích sẵn + nút "Thêm HV thi lại 12 tháng" / Cần xem / Không đưa được); dán danh sách CMT; xử lý ngoại lệ tại chỗ; hoàn tác lần thêm vừa rồi; giao diện dùng **tên trạng thái nghiệp vụ + chú giải**, không lộ mã story/SP/`TT_XuLy`. Số story giữ 56, không thêm/bỏ mã. | ✅ v4.5 | ✅ v6.7 §11F.4/.6 | ✅ mock v2 + SCREENS #29/#30 | ✅ backend 96-105 · ✅ UI 106-115 (trừ dán danh sách + xử lý ngoại lệ tại chỗ → task 116-117) |
| 60 | 11/10/2026 | ➕ Thêm | `TNB-01` · `TNB-02` · `TNB-03` · `TNB-04` · `TNB-05` · `TNB-06` · `TNB-07` | **Feature mới "Tốt nghiệp & Báo cáo 2" — phân hệ #5 tool, DB Nạp `GPLX_CSDT` (prefix mới `TNB`, user chốt).** Cập nhật/hủy tốt nghiệp ô tô theo lô · tạo BC2 (ô tô/mô tô riêng) · thêm/bỏ HV khỏi BC2 · chuyển `TT_XuLy` cứu HV. Chỉ dùng SP có sẵn để PM cũ thấy y chang; PM cũ vẫn kết xuất/kết quả/đóng BC2. | ✅ v4.4 | ✅ v6.6 §11F | ⬜ mock `ui-mock/tnbc2.html` + SCREENS #26–#32 | ✅ backend 96-105 · ✅ UI 106-115 (trừ dán danh sách + xử lý ngoại lệ tại chỗ → task 116-117) |
| 59 | 11/10/2026 | ✏️ Sửa | `PCG-04` · `PCG-02` · `PCG-03` | **/reviewtdd §11E: chặn ghi đè dòng người khác + chống ghi chồng + giới hạn đầu vào.** `/ghi` nhận `dau_van_tay` (băm hiện trạng lúc mở khóa), CDB đã đổi → 409 `khoa_da_doi`; khóa ghi theo khóa → 409 `dang_ghi`; `dia_diem` ≤ 255 / `mon` ≤ 20 / mã ≤ 30; luật ⛔ `mon_khong_ton_tai`. Không đổi quy tắc nghiệp vụ nhân viên thấy ngoài hai thông báo mới. | ✅ | ✅ v6.5 §11E | — | ✅ pytest 444 · tsc sạch · vitest 38 |
| 58 | 11/10/2026 | ✏️ Sửa | `PCG-01` · `PCG-02` · `PCG-03` · `PCG-04` · `PCG-05` | **Chốt 9 điểm mơ hồ PCG sau /kiemthu (user chọn A hết).** E-1 luật "dữ liệu cũ" không hạ nhầm dòng mới/mồ côi (commit 2f48115) · E-2 GV lý thuyết nhận môn Thực hành → cảnh báo `gv_lt_day_thuc_hanh` · E-3 ghi chú "đang ở khóa khác" tới hết ngày bế giảng · E-4 địa điểm ghép xe = giá trị hay dùng nhất · E-5 ghép xe từ đợt đầu đến đợt cuối · E-6 bản nháp không đổi → /ghi 200 "Không có thay đổi" trước cổng cảnh báo · E-7 rà soát: xe chưa ghép không làm "Cần xử lý" · E-8 "Chọn GV TH hợp hạng" gồm TH+AL · E-9 `th_chua_toi_be_giang` theo cả GV · E-10 NguoiTao/NguoiSua 30 ký tự (đúng, không đổi). | ✅ | ✅ §11E.5/7 | — | ✅ pytest 438 · vitest 38 · tsc sạch |
| 57 | 10/10/2026 | ✏️ Sửa (UX) | `PCG-04` · `PCG-02` | **Làm rõ cơ chế "bản nháp" + nút "Phân công".** User không hiểu "Lưu vào bản nháp" lưu gì/ở đâu và vì sao GV đã có phân công vẫn còn nút "Phân công". Đổi chữ: nút khung nhập → "Áp dụng (chưa ghi vào CDB)"; thanh dưới "Chưa ghi vào CDB: N thay đổi" + nút "Xem các thay đổi" (liệt kê từng dòng); hộp Ghi có chi tiết từng thay đổi; nút per-GV "+ Thêm phân công khác" khi GV đã có phân công + dòng giải thích (1 GV nhiều phân công). Bản nháp tự giữ trên máy (localStorage theo CSDL đích + khóa; chỉ khôi phục khi CDB chưa đổi). Thuần UI, không đổi luật/endpoint. Số story giữ 49. | ✅ PCG-04 (Done khi bản nháp) | — | ✅ màn thật | ✅ code + Playwright |
| 56 | 10/10/2026 | ✏️ Sửa | `PCG-01` · `PCG-04` | **Cảnh báo lệch hạng GV: chỉ khi GV dạy Thực hành + bảng hợp hạng thực tế.** User: môn lý thuyết không cần cảnh báo hạng GPLX của GV; khóa C1 thì GV có chứng chỉ thực hành B (B2) dạy được. Điều tra: cột `GiaoVien.CacHangGPLXDuocDT` (hạng được đào tạo) là nguồn; không SP CDB nào kiểm hạng (cảnh báo do tool tự thêm); thực tế khóa C1 ← B 22 · C 9 · C1 3. Luật mới `gv_hop_hang`: khóa B/B.01/C1 nhận B, C1, C, D1, D2, D, E; hạng khác giữ luật cũ; chỉ xét khi GV có phân công môn 6; `GET /giao-vien` trả `hop_hang` (server quyết). Quét 16 khóa thật: `gv_lech_hang` 92 → 0. Số story giữ 49. | ✅ PCG-01/PCG-04 (Done khi) | ✅ §11E.7 + decisions §22 | ✅ BuocGiaoVien (huy hiệu hạng chỉ GV TH/AL) | ✅ code + test (52 pass) |
| 55 | 10/10/2026 | ✏️ Sửa | `PCG-04` · `PCG-02` · `PCG-03` | **Trùng GV/xe chỉ CẢNH BÁO, không chặn; bỏ cảnh báo "đang dạy/chạy khóa khác chưa kết thúc".** User thấy khóa đã bế giảng vẫn báo "trùng" với khóa khai giảng sau. Probe CDB thật: 0 cặp trùng giờ; loại cảnh báo đó không xét ngày/giờ (92/133 ở khóa đã bế giảng). Quy tắc mới: trùng = chồng GIỜ (nửa mở; cùng ngày khác giờ không trùng) → ⚠ ở chỗ chọn xe/GV và từng dòng, vẫn lưu/ghép/ghi bình thường; vẫn ⛔: ngoài phạm vi khóa, bd≥kt, chưa chọn môn, GV/xe ngừng, chưa thuộc khóa, xe hết hạn, ghép cho GV không dạy TH. SP `usp_CheckWarning*` của CDB chỉ trả câu thông báo (không chặn). Số story giữ 49. | ✅ PCG-03/PCG-04 (Done khi + edge) | ✅ §11E.7 + decisions §22 | ✅ BuocXe (ghi chú trùng ở ô chọn xe + dưới dòng) | ✅ code + test (51 pass) |
| 54 | 10/10/2026 | ➕ Thêm | `PCG-01` · `PCG-02` · `PCG-03` · `PCG-04` · `PCG-05` | **Feature mới "Phân công giáo viên – xe" — phân hệ #4 của tool máy CSDT (prefix mới `PCG`, user chốt).** Ghi CDB đích (`KhoaHoc_GiaoVien` cờ 1/0, `KhoaHoc_XeTap` cờ 1/0), không đụng học viên/XML. 3 bước: ① chọn GV của khóa (+hàng loạt thêm/gỡ) · ② phân công môn + từ→đến (môn **Thực hành lái xe** nổi bật 1 bấm; **ngày bắt đầu thực hành tự nhập, để trống**; ô tích "Chỉnh giờ" bước 30 phút, mặc định "Theo ngày" = 00:00→00:00; hàng loạt: phân công cùng môn cho N GV, dời ngày kết thúc) · ③ chọn xe vào khóa + ghép **1 GV–1 xe** (+ "Gợi ý ghép xe" duyệt từng dòng, không tự ghi) · tab "Rà soát khóa". Kiểm 3 mức **Chặn/Cảnh báo/Thông tin** đúng công thức CDB: `datetime`, trùng = giao nhau **có xét giờ**, nửa mở (chạm đầu mút không trùng; cùng ngày khác giờ được), so mọi khóa kể cả cùng khóa; bắt đầu > 00:00 KG, kết thúc < hết ngày BG. **Vì sao tool tự kiểm:** schema không UNIQUE/CHECK/trigger, chỉ SP `usp_CheckWarning*` (UI CDB gọi) kiểm. Bản nháp + "Ghi vào CDB" (xem lại + tích CSDL thật + tích cảnh báo; server kiểm lại). Lưu môn `TenMonHoc="1,8"`, `MaMonHoc` NULL (định dạng CDB từ 29/07/2026); xóa theo `MaLichLV/MaLichSD`, **KHÔNG** dùng SP xóa lan. Loại GV: LT Lý thuyết · TH Thực hành · AL Lý thuyết+Thực hành. Không làm: `LichHoc` (1/16 khóa dùng), phân xe theo HV (`MaHV` luôn trống), sửa danh mục GV/xe. **Số story 44→49.** Mock: `ui-mock/phancong.html`. | ✅ +chương 🟣 PCG-01..05 (v4.3) | ✅ §11E + decisions §22 (v6.4) | ✅ SCREENS #24/#25 + quyết định UX · mock `ui-mock/phancong.html` | ⬜ |
| 53 | 10/10/2026 | ✏️ Sửa (lật quyết định) | `KQD-05` | **"Sửa sau khi đã gửi Sở" — chọn từng HV, có xác nhận** (user 10/10, sau probe DB live). Thay khóa cứng M1 (#45): khi cơ sở hết gói chưa gửi, HV `12` vẫn mở sửa được theo **từng HV được tích** — hộp xác nhận (cảnh báo + lý do ≤1.000 ký tự + tích "sẽ kết xuất lại ngay bằng phần mềm CDB"); lùi `12`→09/10 đúng HV chọn, **không xóa gói đã gửi**, `13` từ chối; nhật ký (điểm trước/lý do/người/giờ) lưu sqlite phía tool; chip cam + băng cam + khối đỏ "chờ kết xuất lại" ở KQD-03, tự biến mất khi HV về lại `12`. Còn gói chưa gửi thì giữ lối "Mở khóa" #45. **Verify DB 10/10:** `usp_CSDT_PheDuyetKQDT_TiepNhan` chỉ nhận HV `12` → HV mở-sửa mà Sở trả kết quả sẽ kẹt (cảnh báo). **Không làm kết xuất XML:** file KQĐT có chữ ký số RSA của phần mềm CDB (tool không tự ký; khóa lộ trong DLL = lỗ hổng nhà cung cấp, không dùng). **KQD-05 hạ ⚠️ Partial → ⏳ Todo** (yêu cầu đổi); KQD-02/03/04 giữ trạng thái (chỉ ghi chú). Số story giữ 44, không mã mới. | ✅ KQD-05 (v4.2) | ✅ §11D.7b + §11D.6 + decisions §21 (v6.3) | ✅ màn thật dựng thẳng `tool/webui` (lưới + hộp xác nhận + khối đỏ; ảnh `anh-kiem/10-10-2026-KQD-05-sua-sau-gui/`) | 🟡 code xong task 83+84 (11 unit test, 358 pytest, tsc+38 vitest+build); chờ restart backend + nghiệm thu máy CSDT. Chưa commit. |
| 52 | 08/10/2026 | ✏️ Sửa (UX) | `THU-01` · `THU-02` | **Loạt 10 cải tiến UX form nhập HV trên desktop** (màn Quét app web, user yêu cầu qua trao đổi). Nới khung 2xl→3xl; **Số CCCD + Ngày cấp cùng hàng** + Họ tên/Nơi thường trú trọn bề ngang; **chặn CCCD >12 số + bộ đếm `n/12`**; **Họ tên tự in hoa**; **Giới tính nút gạt Nam/Nữ** (thay dropdown); **Nơi thường trú gợi ý Tỉnh/Xã 2 cấp 2025** (file tĩnh nhúng, nạp lười, khớp không dấu, **không ép chọn** — hợp cả địa chỉ cũ 3 cấp); **phím mũi tên nhảy ô** (Trái/Phải ở đầu/cuối chữ; Giới tính Trái/Phải đổi Nam/Nữ); **icon nhãn từng ô**; **trạng thái ✓/đỏ từng ô + dòng "còn thiếu/đã đủ"**; **tự suy Giới tính + Năm sinh từ số CCCD** (gợi ý mặc định, sửa được). Thuần client, KHÔNG đổi endpoint/schema/payload. Không thêm mã, số story giữ 44. | ✅ THU-01 +Done-khi #52, dòng trạng thái | ✅ §6.8 mới (v6.2) | — (sửa màn thật `Quet.tsx`, không có ui-demo) | ✅ commit `5087ceb` — tsc + 34 vitest + build pass; chờ Playwright 3vp |
| 51 | 08/10/2026 | ➕ Thêm (mở rộng) | `NAP-01` | **"Bỏ khỏi hàng đợi" cho cả dòng CHỜ/LỖI + nhớ "bỏ qua" + bỏ nhiều một lượt.** Trước chỉ bỏ được dòng 🟢 Đã nạp (guard `409`). Nay bỏ được dòng ⚪ chờ / 🔴 lỗi: tool ghi tombstone `keo_ve_bo_qua` → "Kéo về từ VPS" lần sau không mang về lại. Chỉ đụng staging máy tool, KHÔNG đụng DB Nạp/VPS. Dọn ca hồ sơ đã xóa bên app web nhưng tool kéo về từ trước còn sót (đồng bộ-xóa theo mốc §11.7 bỏ lọt). Mã cũ `NAP-01`, không nghỉ hưu, không story mới (44 giữ nguyên). | ✅ AC "Bỏ khỏi hàng đợi" + bỏ-nhiều + 2 edge case | ✅ §7.2 + §9.3b (bảng tombstone) + §4 endpoint `bo-qua` (v6.0) | — (sửa màn thật `NapHoSo.tsx`, không có ui-demo) | 🟡 code xong, commit `74b4d10` (task 81+82); chờ nghiệm thu máy CSDT (Checkpoint 18) |
| 50 | 07/10/2026 | ✏️ Sửa | `THU-06` | **OCR chỉ đọc 5 trường MẶT TRƯỚC — bỏ ngày cấp** (phát hiện khi build task 79, user chốt A). Ngày cấp in ở **mặt sau** thẻ, THU-06 chỉ chụp mặt trước (❌ không đọc mặt sau) → OCR không đọc được ngày cấp. Sửa #49 (vốn ghi "OCR điền 6 trường … ngày cấp"): OCR điền 5 trường (CCCD/họ tên/ngày sinh/giới tính/nơi TT); **ô ngày cấp để trống + đánh dấu, nhân viên nhập tay** (hoặc lấy từ QR nếu quét được). Số story giữ 44, không nghỉ hưu mã. | ✅ Steps b3 + Done-khi (v4.1) | ✅ §6.7 dòng "Trường OCR đọc" (v5.9) | — (màn #23 chưa dựng; task 80 làm ô ngày cấp nhập tay) | ✅ task 79 `ocr.ts` đã đọc 5 trường, ngày cấp rỗng |
| 49 | 07/10/2026 | ➕ Thêm (lật quyết định) | `THU-06` | **OCR đọc chữ trên thẻ CCCD làm lối nhập dự phòng** (user 07/10, sau BUG-14). Lối nhập **thứ 3** "Chụp ảnh thẻ → tự đọc chữ" ở màn vào `/app/quet`, **mọi thiết bị**: chụp/tải ảnh mặt trước CCCD → OCR điền sẵn 6 trường (CCCD/họ tên/ngày sinh/giới tính/nơi TT/ngày cấp) → **nhân viên xác nhận/sửa** trước khi lưu (OCR có thể sai ký tự) → luồng gửi dùng chung (idempotent UUID, nháp offline). **Lật quyết định "không OCR"** của THU-01 (dòng ❌ nay trỏ THU-06; THU-01 giữ ⚠️ Partial, hành vi QR không đổi). Vì sao: iPhone/iOS quét QR CCCD yếu hơn Android hẳn — engine QR web (ZXing/zbar/OpenCV) đọc không nổi QR nhỏ/mờ/lóa (verify BUG-14 trên ảnh thật), chữ in to/rõ nên OCR chắc hơn. **Engine OCR + nơi chạy + PII CHƯA chốt — để `/tdd`.** **Số story 43→44.** | ✅ +[THU-06] + sửa ❌ THU-01 (v4.0) | ✅ §6.7 + decisions §20 (v5.5) | ⬜ màn #23 → `/prototype-next` | ⬜ (chờ /tdd chốt engine) |
| 48 | 07/10/2026 | ➕ Thêm | `KQD-06` | **Sửa lẻ / xóa điểm đã lưu** (user 07/10, sau khi dùng thử KQD-02). HV đã cập nhật chưa kết xuất (09/10): **sửa lẻ 1 môn** (giữ điểm quy-đổi 4 môn cũ, KHÔNG tính ngược gốc; Lưu không bắt đủ 5) + **xóa điểm** (nút Xóa + xác nhận → UPDATE trực tiếp NULL 5 điểm/3 cờ/`SoGiayCNTN` + `TT_XuLy='03'`; SP `_CapNhat` không reset được — verify DB 07/10). Chỉ 09/10 (12 phải mở khóa KQD-05, 13 khóa tuyệt đối, 14/90 qua KQD-04). **Số story 42→43.** | ✅ +[KQD-06] | ✅ §11D.8 + §11D.6 (v5.4) | ⬜ (dựng thẳng tool/webui) | 🟡 code xong + 4 unit test; chờ restart backend + nghiệm thu máy CSDT |
| 47 | 07/10/2026 | ✏️ Sửa | `KQD-01` · `KQD-02` | **4 cải tiến UX lưới Cập nhật KQĐT** (user 07/10, thuần giao diện, không đổi nghiệp vụ/data/API): ① **ghim tiêu đề lưới** (sticky thead) khi cuộn danh sách HV · ② **thu gọn khung chọn khóa** (nút Thu gọn/Mở rộng) để xem nhiều HV hơn · ③ **phím mũi tên ↑↓←→** di chuyển giữa ô nhập điểm (←→ khi con trỏ ở đầu/cuối ô) · ④ nút **Lưu + Chi tiết ngang hàng** (Lưu trước) thay xếp dọc, dòng thấp hơn. **Không thêm mã**, số story giữ. (Bug hiện điểm/kết luận đã lưu = BUGS #13, không trùng.) | — (chỉ hiển thị) | — | ✅ `CapNhatKQDT.tsx` (verify live) | ✅ |
| 46 | 07/10/2026 | ✏️ Sửa | `KQD-05`, `KQD-03` | **Đồng bộ tài liệu TDD sau code KQD-05/03** (tài liệu lag code, KHÔNG đổi yêu cầu). ① §11D.6 +`GET /local/ketqua/mo-khoa` (cổng B-1 chỉ đọc: `mo_duoc`/`goi_chua_gui`/`goi_da_gui`/`so_hv_mo`/`so_hv_bo_qua`/`so_khoa`) — panel gói KQD-03 + modal KQD-05 dùng chung; + ghi rõ **KQD-03 KHÔNG có endpoint `ket-xuat` riêng** (ghép từ `/khoa` đếm `ketxuat`=12 + `GET /mo-khoa` + `/hoc-vien?trang_thai=ketxuat`). ② §11D.7 **đảo thứ tự bước: LÙI HV (bước 2) TRƯỚC — XÓA gói (bước 3) SAU** cho khớp code + edge PRD ("xóa gói xong lỗi → HV đã lùi vẫn sửa được", tránh kẹt "12 không gói"); `GiaiTrinh` gộp vào `UPDATE` lùi. Không đổi PRD/màn/plan, số story giữ 42. | — (hành vi đã có ở PRD KQD-05) | ✅ §11D.6 + §11D.7 (v5.3) | — (UI đã dựng task 74/77) | 🟡 code KQD-05/03 đã viết + build (task 76/74/77); chờ restart backend + máy CSDT verify |
| 45 | 07/10/2026 | ➕ Thêm + ✏️ Sửa | `KQD-05`, `KQD-03` | **Mở khóa để sửa điểm sau kết xuất + dựng lại tab Theo dõi kết xuất** (user 07/10, qua nhiều lượt + probe DB live). **KQD-05 mới**: HV đã kết xuất (`TT_XuLy=12`) vẫn sửa được điểm **khi khóa còn gói chưa gửi** — cổng **B-1** (`EXISTS TRANS_CLI_HangDoiGui WHERE KieuDuLieu='KET_QUA_DAO_TAO' AND NoiGui=<CSĐT> AND TrangThai='0'`); hành vi **B-1a mức lô** (xóa gói chưa gửi qua `usp_TRANS_CLI_HangDoiGui_Delete` + lùi **mọi HV 12 của khóa** về 09/10 để không treo → sửa → kết xuất lại cả khóa ở PM cũ); gói đã gửi hết → **khóa cứng + thông báo M1 mức đợt** ("không xác định được HV nằm gói nào" — DB không nối HV↔gói, verify: tên gói chỉ timestamp, `Transfer_flag=0` toàn bộ, không junction). Nút "Mở khóa" ở **cả 2 tab**; endpoint `POST /local/ketqua/mo-khoa` là ngoại lệ **nới chặn 409** duy nhất cho `12` (13 khóa tuyệt đối). **KQD-03 viết lại** khóa-first master–detail (trái list khóa+tiến độ; phải tiến độ+panel gói+lưới HV), thay list phẳng cũ. KQD-02/04 +ghi chú ngoại lệ 12, **giữ ⚠️ Partial** (yêu cầu lõi không đổi — 1A+2A user chốt). Lọc gói theo `NoiGui` tránh đụng 61 gói CSĐT 24005 lẫn máy. | ✅ +KQD-05, KQD-03 viết lại (v3.9) | ✅ §11D.7 + decisions §19 (v5.0) | 🟡 mock `ui-mock/theodoiketxuat.html` · màn thật ⬜ | ⬜ |
| 44 | 07/10/2026 | ✏️ Sửa (lật quyết định) | `THU-02`, `QLY-05` | **App web cho chụp bù ảnh kể cả HV ĐÃ NẠP — Phương án B** (user 07/10, lật quyết định A 01/10). App web cho collector **chụp/bổ sung ảnh cho HV THIẾU ảnh kể cả khi `imported`** (trước chỉ `pending`): server nới chặn `POST /api/ho-so/:uuid/anh` (cho `pending`+`imported`, vẫn chặn `importing`, giữ `created_by`); ảnh ghi đè ảnh thô VPS, KHÔNG đổi trạng thái/thông tin. Người nạp **kéo ảnh về ở Tra cứu DB** (QLY-05 nguồn b) để bổ sung vào DB Nạp. **Chỉ mở cho ẢNH** — sửa thông tin & xóa hồ sơ đã nạp vẫn khóa. Cách operator biết HV có ảnh mới: **chốt A — không cờ** (tự lọc "Chưa ảnh"→mở→kéo). Lật Phương án A (TDD §11.5 cũ: ảnh HV đã nạp chỉ xử lý ở tool). 3 hệ thống: app web (`DaGui.tsx`+`lib/gui.ts`) · VPS (`server .../anh`) · tool (TraCuuDB/AnhModal, QLY-05 #32). | ✅ THU-02⏳/QLY-05 (v3.8) | ✅ §6.2/§6.3/§4.3/§11.5 + decisions §18 (v4.9) | 🟡 app web `DaGui` + tool Tra cứu DB | ⬜ |
| 43 | 07/10/2026 | ✏️ Sửa + 🐛 | `NAP-01` | **Ngày cấp + Nơi cấp điền sẵn ở drawer "Chuẩn bị" (Nạp lô)** (user 07/10, phát hiện khi điều tra bug người dùng báo). ① **Ngày cấp CCCD** (yêu cầu mới): drawer thêm ô có nhãn riêng (`<input type="date">`), **điền sẵn** `keo_ve.ngay_cap` + **sửa được** như ô Nơi cấp; lưu nháp bền (`nhap_chuan_bi` +cột `ngay_cap`; `nhap[uuid]` +`ngayCap`), theo luật GIỮ khi reset địa chỉ (BUG-04); payload nạp ưu tiên `nhap.ngayCap`→gốc `keo_ve.ngay_cap` (ghi `NgayCapCMT`). Trước #43 chỉ là chữ read-only inline, luôn lấy gốc. ② **Nơi cấp** (🐛 sửa lỗi hiển thị): ô vốn đã điền sẵn+sửa được (`suyNoiCap`: CCCD 12 số→'00'), nhưng khi máy CSDT **chưa chạy script đồng bộ `DM_DVHC` đích→nguồn** (#40) thì danh mục nguồn thiếu mã '00' → `<select value="00">` không khớp option → tụt placeholder (trông như không tự chọn). Fix client: tự chèn option `00 — Cục QLHC` khi suy ra '00' mà combo chưa có. Dữ liệu nạp không đổi. Khác #40 (sửa modal QLY-01/Tra cứu DB) — đây là **drawer Nạp lô**. | ✅ NAP-01 (v3.7) | ✅ §9.3a (v4.7→v4.8 sau /reviewtdd) | — drawer code thẳng `tool/webui` | 🟡 code xong (`nap.py` +cột `ngay_cap`+migrate · `routers/nap.py` model · `NapHoSo.tsx` ô `ODate`+chèn option '00' · `api.ts`); tsc + 34 vitest + build + **308 pytest (+4 #43: round-trip/reset-giữ/migrate-bảng-cũ/default)**. **Chờ verify máy CSDT** (nạp thật ghi `NgayCapCMT` + ô hiện trên tool thật). Chưa commit. |
| 42 | 07/10/2026 | ➕ Thêm | `KQD-01`, `KQD-02`, `KQD-03`, `KQD-04` | **Nhóm "Cập nhật kết quả đào tạo"** (prefix mới **KQD**, user chốt) — nhập KQĐT vào CDB đích `GPLX_CDB_CSDT` (bảng `NguoiLX_HoSo`) qua SP có sẵn `usp_NguoiLX_KetQuaDaoTao_CSDT_CapNhat`, chuyển `TT_XuLy` 03→09/10. **Phạm vi chỉ cập nhật, KHÔNG kết xuất XML/gửi Sở** (để PM CDB cũ lo). **KQD-01** chọn khóa bằng combobox gõ-tìm (chỉ khóa đã BC1) + lọc HV 4 trạng thái (03/04·09/10·14·90) + lưới + **băng cam DB đích** (component dùng chung với Sync). **KQD-02** nhập **điểm GỐC 5 môn** → app quy đổi /10 theo "Sổ theo dõi KQ học tập TT17" (2 đoạn tuyến tính, ngưỡng 5,0) → ghi **5 điểm per-môn** (KHÔNG ghi trung bình); giờ/km thực hành theo **TT17/2026/TT-BXD** (giờ sân khóa cứng · km sân điền sẵn · giờ+km đường trống-gợi-ý-tối-thiểu); cờ chương trình **CŨ/MỚI tích chọn theo từng khóa** (lưu phía tool); **Kết luận Đạt do app tự tính từng-môn-≥5** (3 cờ bit app tính rồi truyền SP — DB không có trigger/computed/constraint, verify 06/10); Số giấy HTKH = `MaDK+'-'+hạng` tự sinh. **KQD-03** tab Theo dõi kết xuất (chỉ xem, đã/chưa = TT_XuLy 12). **KQD-04** sửa lại HV Sở từ chối (14)/giải trình (90). Sync vốn đã có "banner DB đích" → không hạ SYNC. | ✅ +chương ③🟣 (KQD-01..04) | ✅ §11D + decisions §17 | ⬜ +màn #21/#22 (dựng thẳng `tool/webui`) | ⬜ |
| 41 | 06/10/2026 | ✏️ Sửa | `SYNC-03`, `SYNC-01` | **Lịch sử sync hiện tên khóa + nút Hủy ở Bàn đồng bộ** (user 06/10). ① **Lịch sử**: đổi thứ tự cột **Khóa nguồn (CSDT) → Khóa đích (CDB)** (trước ngược), mỗi khóa hiện **tên (đậm) + mã**; `SyncBatch` +`ten_khoa_moi`/`ten_khoa_cu` lưu lúc sync, `/lich-su` tra DB bù tên cho bản ghi cũ (try/except, mất DB→mã). ② **Bàn đồng bộ**: nút **"Hủy sync khóa đích (N)"** hiện khi khóa đích đã có HV do tool tạo (dò `/rollback/preview tong>0`) → hộp thoại xác nhận (tách `HuyncSyncDialog` dùng chung) → `/rollback` về ban đầu. ③ Đổi nhãn cột đếm ở Bàn đồng bộ **"Số HS"→"SL hồ sơ"** (là `COUNT(*)` số lượng HS/người, luôn=1 — khác cột "Số HS"=SoHoSo ở Tra cứu; port từ sync_tool v2.0 nhãn "So HS"). Endpoint `/rollback` cũ không đổi. | — (thuần UI tool) | — (vòng đời sync, không chạm quyết định) | ✅ Lịch sử + Bàn đồng bộ | ✅ commit `844a031` + nhãn; 304 backend+34 vitest+tsc. **Chưa push.** |
| 40 | 06/10/2026 | ✏️ Sửa + ➕ Thêm | `NAP-05`, `QLY-01`, `TCB-03` | **Nơi cấp căn cước = Cục QLHC ('00' `DM_DVHC`) + mở rộng modal sửa Nạp** (đảo #31/BUG-10 + #37 "QLY-01 giữ 5 trường"). ① Nơi cấp lấy từ **`DM_DVHC.MaDvhc`** (có mã `'00'`=Cục QLHC, cùng danh mục với mã tỉnh) thay vì `DM_DonViGTVT` (Sở GTVT, không có Cục QLHC) — đổi 4 điểm: combo `ds_so_gtvt` + 3 hiển thị (`hoso.py`, `sync_tracuu.py` list+chi tiết). ② **Mặc định CCCD 12 số = '00' Cục QLHC** (căn cước do Cục Cảnh sát QLHC cấp tập trung; `suy_noi_cap` + `suyNoiCap`), bỏ fallback `noi_cap_cccd` (text nhét nhầm cột mã). ③ **Tiền đề đã chạy:** đồng bộ `DM_DVHC` DB đích→nguồn (`update/sync-DM_DVHC-...sql`, MERGE upsert không xóa, backup `DM_DVHC_backup_20261006`) → nguồn có '00' + 34 tỉnh sáp nhập đúng tên (trước đó tỉnh nguồn đều TrangThai=0 → combo nơi cấp/tỉnh rỗng). ④ **Mở rộng modal sửa QLY-01 Nạp** thêm combo **địa chỉ 2 cấp (Tỉnh/Xã) + nơi cấp + ngày cấp CCCD** (ngang TCB-03/#37), bỏ-trống-giữ-cũ; **guard BC1 giữ nguyên** (chặn 409 trên đường lưu). ⑤ Nhãn Sync "Nơi cấp CCCD (Sở GTVT)"→"Nơi cấp căn cước". | 🟡 QLY-01/TCB-03 ghi chú (v3.5) | 🟡 §11B.7 (chờ /reviewtdd) | ✅ combo Nạp+Sync | ✅ 3 commit `928a019`/`4acc943`/`946a56f` + 1 script sync; 304 backend+34 vitest+tsc, verify live DB nguồn+đích. **Chưa push.** |
| 39 | 05/10/2026 | ✏️ Sửa | `DGT-04` | **Refresh-token VPS cho phiên tool vĩnh viễn** (gỡ Chặn 2.1 từ /reviewtdd #38): phiên local vĩnh viễn nhưng `vps_token` (JWT VPS) hết **8h** → sau 8h mọi thao tác nạp/đối soát từ VPS **401** dù tool vẫn báo đã đăng nhập. Fix (cách A, chốt /reviewtdd): VPS cấp **refresh token** lúc đăng nhập (tool lưu **DPAPI**), heartbeat thu-hồi-từ-xa **kiêm** đổi lấy `access_token` mới qua `POST /api/auth/refresh`; refresh thất bại / TK bị khóa → tự đăng xuất. **Gộp vào DGT-04** (không tạo story mới — user chốt A). DGT-04 đang ⏳ Todo → không đụng trạng thái. | ✅ v3.4 | ✅ §12 + §11C.4 (v4.2) | — | ⬜ (code khi dựng DGT-04) |
| 38 | 05/10/2026 | ➕ Thêm | `DGT-01`, `DGT-02`, `DGT-03`, `DGT-04`, `HTG-01` | **Nhóm "Đóng gói & khởi chạy tool độc lập"** (prefix mới DGT, user chốt) — mang tool sang máy CSDT khác không cần cài Python/Node, mở như phần mềm thường, lần sau dùng không phải thiết lập lại. **DGT-01** đóng gói exe PyInstaller (gói sẵn mọi thư viện backend) + FastAPI phục vụ `webui/dist` cùng cổng (`BASE=""` sẵn có) + ghi dữ liệu vào `%APPDATA%`. **DGT-02** mỗi lần chạy **tự mở trình duyệt** đúng trang + **khay hệ thống** (Mở giao diện/Thoát) + **chống chạy 2 bản** (đưa tab cũ lên) + tùy chọn **tự chạy khi bật máy**. **DGT-03** **wizard thiết lập lần đầu** (máy sạch): kiểm môi trường → cấu hình SQL nguồn/đích + VPS (tái dùng test-before-save `/config/test`) → đăng nhập, test xanh mới qua bước; lần sau có cấu hình thì bỏ wizard. **DGT-04** **phiên đăng nhập VĨNH VIỄN** (lưu đĩa mã hóa `key.bin`, mở exe vào thẳng, chỉ Đăng xuất mới thoát) + thu hồi từ xa (ngầm hỏi VPS). HTG-01 +dòng trỏ DGT-04 (chỉ tool; web giữ phiên thường, vẫn ✅). | ✅ v3.3 | ✅ §11C (v4.0) + decisions §16 | ⬜ wizard lần đầu (dựng thẳng tool/webui) | ⬜ |
| 37 | 05/10/2026 | ✏️ Sửa | `TCB-03` | **Mở rộng trường sửa nhân thân ở Tra cứu CDB** (phát hiện khi nghiệm thu Checkpoint 14 tại máy CSDT — form 5 trường quá tối thiểu). Thêm **địa chỉ thường trú 2 cấp** (chọn Tỉnh+Xã chuẩn → `NoiTT_MaDVHC`/`MaDVQL`, không chỉ dòng chữ) + **ngày cấp CCCD** (`NgayCapCMT`) + **nơi cấp CCCD** (`NoiCapCMT`, Sở GTVT). `usp_NguoiLX_Update` đã nhận sẵn các tham số. **Chỉ TCB-03** (user chốt 05/10) — tách model riêng cho CDB, **Nạp QLY-01 giữ nguyên 5 trường**. Danh mục Tỉnh/Xã + Sở phải đọc từ **DB đích** (`target_key`). TCB-03 hạ ✅→⏳ (bản 5 trường đã nghiệm thu ghi-thật PASS tại máy CSDT 05/10). Nơi cư trú 2 cấp để sau; KHÔNG làm số CMND cũ (SP update không nhận). | ✅ v3.2 | ✅ §11B.7 (v3.8) | 🟡 ghi màn #19 (code thẳng tool/webui) | ⬜ |
| 36 | 05/10/2026 | ✏️ Sửa + ➕ Thêm | `TCB-01`, `TCB-02`, `TCB-03`, `TCB-04`, `SYNC-01`, `HTG-01` | **Sửa định nghĩa "đã kết xuất DKKH"** sang tín hiệu ĐÚNG: khóa có gói `DANG_KY_KHOA_HOC` đã gửi Sở (`TRANS_CLI_HangDoiGui` tên file chứa MaKH) — **KHÔNG** phải `KhoaHoc.SoQD_KhaiGiang` (sai: mọi khóa đều có số QĐ nội bộ → chặn nhầm khóa chưa gửi Sở; verify DB 05/10: 16 khóa đều có SoQD nhưng chỉ 14 đã gửi). Một định nghĩa chung `sync_helpers.dkkh_exists_sql`/`dkkh_exists_cond` (CHARINDEX) dùng cho TCB-01 (chip) + **TCB-03 chặn sửa nhân thân** + **TCB-04 NÂNG ngưỡng chặn: khóa đã DKKH → KHÔNG xóa HV, KHÔNG đổi khóa** (áp cả khóa đi lẫn khóa đến; `khoa-cung-hang` lọc bỏ khóa DKKH; UI vô hiệu nút + ghi lý do) — trước đây DKKH chỉ cảnh báo, chặn cứng ở BC1 (user chốt 05/10: thêm/bớt HV ở khóa đã gửi Sở là lệch danh sách). **+SYNC-01**: (a) filter khóa đích *"Chỉ khóa cùng hạng & chưa kết xuất DKKH"* (checkbox mặc định bật; đích trả thêm cờ `dkkh`) · (b) khóa xếp **mới-nhất-trước** (ORDER BY NgayKG DESC, **MaKH DESC** + hiện ngày KG ở combo nguồn) · (c) **giữ phiên đăng nhập qua F5** (token→localStorage, khôi phục `/local/auth/me`, tự kiểm kết nối đích khi vào màn). Nghiệp vụ sync lõi không đổi → SYNC-01 giữ ✅; TCB giữ ✅ (code đã sửa+verify live 05/10). +docs DB đích §7 (định nghĩa DKKH). | ✅ v3.1 | ✅ §11B.2/§11B.7/§5.5 (v3.6) | ✅ (sửa `BanDongBo.tsx`/`TraCuuCDB.tsx` qua cờ backend) | ✅ 8 file, tsc+34 vitest, verify live+DB. **Chưa commit.** |
| 35 | 04/10/2026 | ➕ Thêm | `TCB-01`, `TCB-02`, `TCB-03`, `TCB-04` | **Feature "Tra cứu CDB đích"** (mở rộng phân hệ Đồng bộ CDB) — màn tra khóa + xem/sửa HV trên **DB ĐÍCH `GPLX_CDB_CSDT`** (song song Tra cứu DB Nạp QLY-01 nhưng trỏ đích). **TCB-01** tra khóa + lưới HV (avatar, tìm) + chi tiết + ảnh lớn + **nút "Xem chi tiết HV" từ Bàn đồng bộ** (mở khóa + tô sáng). **TCB-02** thay ảnh (tái dùng AnhModal + đổi nền, **ghi đè file `.jp2` dùng chung 2 DB** → cả Nạp+đích cùng đổi; cho kể cả DKKH/BC1 + cảnh báo). **TCB-03** sửa nhân thân (`usp_NguoiLX_Update` CDB) → **chặn nếu khóa đích đã kết xuất DKKH** (`SoQD_KhaiGiang`). **TCB-04** xóa HV/đổi khóa → **chặn nếu đã BC1** (FK `BaoCaoI` NO_ACTION); DKKH chưa BC1 → cho+cảnh báo. Luật khóa đọc trạng thái **ở đích** (độc lập DB Nạp); danh mục `DM_TrangThai`. Dựng màn mới `TraCuuCDB.tsx` (tái dùng AnhModal/AnhAvatar, KHÔNG đụng QLY-01). SYNC-01 thêm nút điều hướng (giữ ✅). | ✅ | ✅ §11B.7 (v3.4) | ⬜ màn #19 (dựng thẳng tool/webui) | ⬜ |
| 34 | 04/10/2026 | ➕ Thêm + ✏️ Sửa | `HTG-07`, `HTG-01`, `SYNC-02`, `SYNC-01` | **Cấu hình kết nối DB lên header dùng chung cả tool** + tách rõ DB Nạp vs DB Sync + làm đẹp UI sync. **HTG-07 mới**: bảng cấu hình mở từ **icon ⚙ header** (mọi màn), gộp 2 khối tách bạch — ① kết nối chung + **DB NGUỒN để Nạp** `GPLX_CSDT` (từ HTG-01) · ② **nhiều DB ĐÍCH để Sync** (từ SYNC-02, chọn mặc định/test/tùy chọn). **Bỏ** route `/tool/cau-hinh` + mục "Quản lý CSDL đích" khỏi sidebar. Làm đẹp combobox năm/khóa + chọn DB đích + **danh sách HV để sync** (tên hài hòa, dễ đọc) bằng `impeccable`+`ui-ux-pro-max`. Thuần UI/IA — backend `/local/config*`+`/local/sync/targets`+config-store KHÔNG đổi; không chạm quyết định TDD §12/§13/§14. **(Nhân tiện sửa bug môi trường:** backend nền chạy không `--reload` → kẹt code cũ, combobox năm/khóa trả 404 → restart hết; không phải lỗi code.) | ✅ | ✅ §5.0 + §11B.0 (v3.3) | ✅ task 61-62: `CauHinhDrawer` + ⚙ header + làm đẹp Bàn đồng bộ | 🟡 code+kiểm mức1+2 review xong, **chưa commit** |
| 33 | 04/10/2026 | ➕ Thêm | `SYNC-01`, `SYNC-02`, `SYNC-03` | **Feature mới "Đồng bộ CDB"** (SHOULD) — port nghiệp vụ từ `D:\Du_An\GPLX\sync_tool` **v2.0** vào tool máy CSDT, **tách hoàn toàn** khỏi Nạp. **SYNC-01** Bàn đồng bộ (chọn khóa nguồn `GPLX_CSDT` + đích CDB cùng hạng · ngày nhập HS ≤ NgàyKG · `NguoiTao=admin` giống CDB, **bỏ ô cán bộ** · tải DS đối chiếu đích · skip HV đã có 1người=1HS · MaDK `MaCSDT-yyyyMMdd-nnnnnn` backdate batch · tiến trình **SSE**) · **SYNC-02** Quản lý DB đích (nhiều DB đích dùng chung host/user/pass, chọn mặc định, test, TT_XuLy mặc định 03 + cập nhật TongSoHV) · **SYNC-03** Lịch sử & Hủy sync (log JSON %APPDATA% + rollback dual-mode `NguoiTao='SYNC'`). **Kiến trúc:** tool đổi sang **sidebar trái = danh sách module** (mở rộng N — dự kiến module #3 "Cập nhật kết quả học tập"); backend tách `routers/sync.py`+`sync_service.py`+`sync_helpers.py`+`sync_history.py` không import nạp; **tool CHỈ desktop** (≥1280px, sidebar thu gọn, bảng cuộn ngang) | ✅ | ✅ §11B + §2.4 (v3.2) | ✅ 3 màn dựng thẳng tool/webui (task 56-62) | 🟡 SYNC-01/02 commit `d2b0ba1`/`765d972` (#34); SYNC-03 task 60 chưa commit |
| 32 | 04/10/2026 | ➕ Thêm + ✏️ Sửa | `NAP-01`, `QLY-05` | **Lưu nháp BỀN + 2 chip trạng thái + bổ sung ảnh 2 nguồn** (màn Nạp lô). ① **Lưu nháp bền** (NAP-01): chỉnh sửa chuẩn bị (địa chỉ 2 cấp, chi tiết, nơi cấp, tick giấy tờ, **ảnh đã đổi nền**) lưu xuống `staging.sqlite` bảng `nhap_chuan_bi` thay vì chỉ RAM → F5/đóng-mở tool không mất; **tự xóa** khi nạp xong/bỏ hàng đợi/xóa VPS; reset riêng địa chỉ nháp (backend, trong `keo_ve_upsert`) khi `noi_tt_raw` đổi (BUG-04) · ② **2 chip mỗi dòng** `✓/✗ Địa chỉ 2 cấp` + `✓/✗ Có hình` (mặc định ✗) · ③ **Mở drawer**: cả dòng bấm + nút "Xử lý" to · ④ **Nạp**: chặn thiếu địa chỉ, cảnh báo thiếu ảnh + lối tắt mở Tra cứu DB lọc "chưa ảnh" · ⑤ **Bổ sung ảnh HV thiếu ảnh** (QLY-05): lấy từ **file** (`chonFile`) hoặc **ảnh thô VPS** (`tra_uuid`→`tai_anh`→`napTuUrl`, nếu còn ≤30 ngày), cùng AnhModal + đổi nền | ✅ | ✅ §9.3a/§10.5/§11.5 (v3.2) | 🟡 ghi UX (cập nhật khi code) | ⬜ |
| 31 | 03/10/2026 | ➕ Thêm + 🐛 | `NAP-05`, `QLY-01` | **Nơi cấp căn cước + số hồ sơ + popup chi tiết** (ca Lê Thị Hồng). ① **Nơi cấp** (BUG-10): nạp tự suy **mã Sở GTVT từ số CCCD** (`cccd[2:3]`; nơi cấp = `DM_DonViGTVT` LoaiDV='SO', vd 70=Bình Phước, 75=Đồng Nai) + **combobox** chọn tay (endpoint `/local/dvhc/so-gtvt`) + **vá 6 bản ghi cũ** rỗng · ② **Số hồ sơ** (BUG-09): `MAX+1` → **số nhỏ nhất chưa dùng** (lấp khe do nạp→gỡ→nạp lại) · ③ **Popup "Chi tiết học viên"** (QLY-01): thêm Ngày cấp · Nơi cấp (tên) · Địa chỉ cư trú + địa chỉ đầy đủ (join DM_DVHC); ẩn CMND cũ ở form nạp app web giữ nguyên (đã ẩn), chi tiết vẫn hiện. Thuần tool, KHÔNG đổi SP/schema | 🟡 ghi BUGS #9/#10 | — | ✅ popup + combobox | ✅ tool build+34 vitest; vá DB xong |
| 30 | 03/10/2026 | ✏️ Sửa + ➕ Thêm | `THU-01`, `THU-05` | Redesign giao diện **DESKTOP** app web (nhánh `lg:`, mobile giữ nguyên): **① Quét (THU-01)** — desktop vào thẳng **form nhập tay** (bỏ cổng chọn), nút **Quét QR/Tải ảnh thu nhỏ** ra góc phải tiêu đề, Quét QR mở **popover camera** đè form rồi tự điền; "Lưu & nhập tiếp" → form trống · **② Hồ sơ đã gửi (THU-05)** — desktop **chọn-nhiều-để-xóa**: cột ô tích chỉ ở dòng Chờ nạp + thanh "Đã chọn N · Xóa N" + dialog xác nhận (lặp DELETE client, tái dùng QuanTriHoSo). KHÔNG đổi Data Model/API/endpoint. (Đổi số từ #28→#30 khi gộp 2 phiên song song) | ✅ | ✅ §6.5/§6.6 (v3.0) | ✅ ghi UX (sửa màn có sẵn, không dựng mới) | 🟡 client xong (build+24 test+review-nghiepvu đủ), chưa chụp Playwright/deploy |
| 29 | 03/10/2026 | ✏️ Sửa (UI) | `NAP-01`, `NAP-03` | Tool máy Nạp: **dời 2 nút "Chọn tất cả sẵn sàng" + "Nạp N học viên vào khóa" từ thanh dính đáy LÊN header** (NAP-01, hàng shrink-0 trong `h-[calc]` → list tự co, nút luôn thấy) · **"Chọn tay" địa chỉ: 2 dropdown → ô gõ-để-lọc** `ComboLoc` (gõ không dấu cũng khớp nhờ `boDau`, NAP-03). Thuần client, KHÔNG đổi API/DB | ✅ | — UI-only | ✅ ghi UX+wireframe | ✅ tool build+29 test (chờ chụp) |
| 28 | 03/10/2026 | ➕ Thêm | `QLY-09` | **Đối soát & đồng bộ trạng thái VPS↔CSDT** (sau ca Lê Thị Hồng/BUG-01): panel admin/operator ở tool, đối soát **theo khóa**, phát hiện 3 ca lệch (① VPS imported & CSDT không có MaDK = phantom → Trả về chờ nạp; ② CSDT có HV & VPS chưa imported → Đánh dấu đã nạp; ③ importing treo quá ngưỡng → Mở khóa), sửa 1 chạm **tái dùng** `tra_ve_cho_nap`/`da_nap`/`unlock` — không endpoint/SP nạp mới. +Phòng tuyến 2: `nap_fn` bỏ `da_nap` khi `_nap_mot` trả vé cũ (chặn tái phát phantom). Thuần tool | ✅ | ✅ §11.8 | ⬜ panel tool (dựng khi code) | ⬜ |
| 27 | 03/10/2026 | ✏️ Sửa (chữ) | `THU-05` | Khớp chữ PRD với code task 41 (review-nghiepvu): edge "Chặn 403" → **404** (chống IDOR, không lộ hồ sơ tồn tại — nhất quán `_cua_minh`); copy popup "chưa nạp vào **DB**" → "chưa nạp vào **máy tính**" (tránh lộ từ kỹ thuật cho người thu nhận, luật nội dung). Không đổi code (code đã đúng) | ✅ | — | — | — đã code (task 41) |
| 26 | 03/10/2026 | ✏️ Sửa + ➕ Thêm | `THU-05`, `QLY-08`, `QLY-03`, `NAP-01`, `NAP-04`, `QLY-05` | Chốt nghiệp vụ + UX trước khi code #24: **nguyên tắc bàn giao** (mốc Nạp — trước nạp app web làm chủ, sau nạp tool/CSDT làm chủ, app web đóng băng; QLY-03 "Xóa hẳn" ≠ QLY-08 "Gỡ về chờ nạp") · **popup cảnh báo + hướng dẫn** (copy impeccable) cho xóa app web (THU-05), gỡ về chờ nạp + banner đồng bộ lỗi (QLY-08), xóa hẳn tách bạch (QLY-03) · **"Dùng lại ảnh gốc"** trong trình chỉnh ảnh (NAP-04 ảnh thô VPS / QLY-05 ảnh DB) · **redesign màn Nạp lô** (NAP-01): trạng thái sẵn sàng mỗi dòng, chọn-tất-cả-sẵn-sàng, drawer Chuẩn bị, dialog nạp 3 pha (xác nhận/tiến độ/báo cáo + nạp lại lỗi), nút Xem trong DB | ✅ | ✅ §7.5/§9.1/§10.5 | ✅ ghi UX+wireframe | ⬜ |
| 25 | 03/10/2026 | ✏️ Sửa (nhãn) | `QLY-08`, `THU-05` | Sửa nhãn trạng thái VPS trong PRD: `done` → `imported` (3 chỗ ở THU-05 + QLY-08) cho khớp DB thật (`server/db/init.sql:28` chỉ có `pending/importing/imported/deleted`) + TDD. Phát hiện ở review TDD #24 (Điểm 1, biên bản `tdd-review-03-10-2026.md`). Không đổi yêu cầu, không chạm TDD (đã đúng) | ✅ | — đã đúng | — | — |
| 24 | 02/10/2026 | ➕ Thêm + ✏️ Sửa | `QLY-08`, `THU-05`, `NAP-01` | Đồng bộ gỡ/xóa hồ sơ (verify #22): **QLY-08 mới** — nút "Gỡ về chờ nạp" ở tool (gỡ HV khỏi CSDT + VPS imported→pending + về hàng chờ), tách bạch "Xóa" bỏ hẳn, chỉ khóa chưa BC1, ảnh dùng ảnh thô VPS · **THU-05 mới** — app web collector xóa hồ sơ đã gửi (chỉ pending, soft-delete VPS, của mình/admin) · **NAP-01 mở rộng** — "Kéo về từ VPS" đồng bộ bỏ hồ sơ đã xóa khỏi hàng chờ. Đụng cả tool + **server VPS** (đường mới) + app web | ✅ | ✅ | ✅ ghi UX (không dựng màn) | ⬜ |
| 23 | 02/10/2026 | ✏️ Sửa (UI) | `NAP-04`, `QLY-05`, `QLY-06` | Sửa UX quản lý ảnh + nhãn nút (phát hiện khi verify #22): sau "Dùng ảnh này" **hiện ảnh đã chỉnh** (bản PNG, không chỉ icon check) + **mở lại trình chỉnh nạp sẵn ảnh đã chỉnh** để chỉnh tiếp (NAP-04/QLY-05) · nút áp dụng ảnh **nổi bật + nhãn rõ** (tránh dừng ở "Xử lý ảnh" tưởng đã lưu) · nút **"Mở khóa khác" → "Tạo thêm hồ sơ ở khóa học khác hạng"**, giữ hiển thị cả ở khóa BC1 (QLY-06). Thuần UI, backend `/local/anh/xu-ly` đã trả `preview` sẵn | ✅ | ✅ ghi chú §9.1 | ✅ ghi UX (không dựng màn) | ⬜ |
| 22 | 02/10/2026 | ➕ Thêm + ✏️ Sửa + 🐛 | `QLY-01`, `QLY-03`, `QLY-05`, `QLY-07`, `NAP-01` | Mở rộng quản lý ảnh Tra cứu DB + bảo toàn Báo cáo 1/2: xem ảnh+đường dẫn+avatar+thống kê (QLY-01) · 🐛 giữ `TT_XuLy` khi thay ảnh HV đã Báo cáo (QLY-05, tránh rơi khỏi BC2) + click ảnh từ Tra cứu DB · chặn xóa HV khóa BC1 ở backend (QLY-03) · "Bỏ khỏi hàng đợi"+"Nạp lại nhanh" (NAP-01) · **story mới QLY-07** đổi nền cả khóa | ✅ | ✅ | ⬜ wireframe chốt | ✅ code+push, chờ verify prod |
| 21 | 02/10/2026 | ✏️ Sửa | `NAP-04` | Zoom trình chỉnh ảnh (phản hồi test): cho **thu nhỏ dưới cỡ ban đầu** (trước lấy ảnh gốc làm mốc nhỏ nhất) · thang zoom **mặc định ở GIỮA** (trái thu nhỏ, phải phóng to, mũ 3^t) · **lăn chuột** trên khung để phóng/thu | ✅ | ✅ | — tinh chỉnh AnhModal | ✅ code+build+Playwright, ⚠️ chờ verify |
| 20 | 02/10/2026 | ➕ Thêm + ⚙️ | `NAP-04` | Nâng cấp trình chỉnh ảnh (phản hồi test tool): +xoay ảnh (−90°/+90° + tinh chỉnh độ nghiêng) · +khung chân dung mẫu overlay (ô-van+đường căn, không dính ảnh xuất) · tăng tốc xóa phông = bật warm-up rembg (bỏ `TOOL_SKIP_WARMUP=1` ở `tool-start.bat`), GIỮ model u2net (phương án A). NAP-04 ⚠️→⏳ | ✅ | ✅ | — tinh chỉnh AnhModal có sẵn | ⬜ |
| 19 | 02/10/2026 | ✏️ Sửa | `NAP-03`, `NAP-04` | Tận dụng dữ liệu đã kéo từ VPS ở màn Nạp (kéo-về): NAP-03 tự tách `noi_tt_raw` → điền sẵn ô map (operator chỉ bấm Chuyển đổi; tách không chắc thì gõ tay) · NAP-04 nạp thẳng ảnh thô VPS vào trình chỉnh (không bắt chọn lại file). NAP-03 ✅→⏳, NAP-04 ⚠️→⏳ (yêu cầu đổi, code lại phần này) | ✅ | ✅ | — tinh chỉnh màn tool có sẵn | ⬜ |
| 18 | 02/10/2026 | ➕ Thêm + ✏️ Sửa | `HTG-04`, `HTG-05`, `HTG-06` | Quản lý tài khoản app web: admin xem API key VPS (HTG-04, SHOULD) · admin tạo/khóa tài khoản nhân viên + reset mật khẩu (HTG-05, MUST) · mọi người tự đổi mật khẩu (HTG-06, MUST). + **5 sửa UI (cả 2 app):** header cố định hết giật · khung cao ổn định không co theo nội dung · phân trang list (20/trang) · tool master–detail panel info+ảnh ghim · kính lúp đè chữ hint (fix `@layer components`) | ✅ | ✅ | ⬜ | 🟡 HTG-04/05/06 + UI-1/2/3/4/5 xong (code; server 82 test, build 2 app); chờ deploy VPS + verify |
| 17 | 02/10/2026 | ✏️ Sửa | `QLY-01` | Lát 2 (sửa hồ sơ) — **thu hẹp phạm vi: chỉ sửa NHÂN THÂN** (họ tên, ngày sinh, giới tính, CCCD, địa chỉ TT) qua `usp_NguoiLX_Update`; **bỏ `usp_NguoiLX_HoSo_Update` khỏi QLY-01** (SP ghi đè 65 cột gồm kết quả thi/BC1/BC2 → rủi ro xóa trắng); ảnh→QLY-05, đổi khóa→QLY-02. Ghi an toàn: đọc lại full bản ghi giữ cột không sửa. Chặn khi khóa BC1 (BR-012) | ✅ | ✅ | ⬜ | ✅ code+test, chờ verify prod |
| 16 | 01/10/2026 | ✏️ Sửa | `QLY-06` | Kiểm DB thật (chỉ đọc) chốt thiết kế QLY-06: SP `ThemMoiCapNhat` nạp mới **luôn tạo NguoiLX mới** (không dò người cũ); dữ liệu thật nhiều HV có **2–8 khóa chung SoCMT** → nạp khác khóa = nạp mới bình thường, không cần nối người. Gỡ 📝 Draft → ⏳ Todo | ✅ | — | ⬜ | ⬜ |
| 15 | 01/10/2026 | ✏️ Sửa | `THU-02` | Ảnh app web: tách **2 nút "Chụp ảnh" (camera) / "Chọn từ máy" (file·thư viện)** ở màn chụp + đổi ảnh hồ sơ Chờ nạp (trước ép camera, mobile không chọn được thư viện); bấm ảnh chân dung ở chi tiết → **phóng to popup (lightbox)** | ✅ | — | ⬜ | ✅ deploy |
| 14 | 01/10/2026 | ✏️ Sửa | `THU-01`, `THU-02` | Redesign UX nhập liệu (impeccable): ẩn ô "Số CMND cũ" (vẫn lưu từ QR nếu có) · ô ngày gõ tay dd/mm/yyyy auto-mask "/" + nút lịch (giữ năm-only) · desktop nới khung 2 cột + tách 2 nút tránh bấm nhầm + phím tắt · rà content tránh lộ story/AI slop | ✅ | ✅ | ⬜ | ✅ deploy |
| 13 | 01/10/2026 | ✏️ Sửa + ➕ Thêm | `THU-01`, `THU-02`, `THU-04`, `QLY-06` | App web nhập liên tiếp: nút "Lưu & nhập hồ sơ tiếp" (gửi không ảnh + toast) + badge/lọc "Thiếu ảnh" (THU-01/02 hạ ⏳); +THU-04 cảnh báo trùng CCCD app web (SHOULD, cảnh báo mềm soi hàng đợi); +QLY-06 mở hồ sơ khóa khác cho HV đã có (📝 Draft, còn nợ kiểm DB) | ✅ | ✅ | ⬜ | ✅ THU-01/02/04 deploy + chốt · QLY-06 ⬜ (Draft) |
| 12 | 01/10/2026 | ✏️ Sửa | `THU-01`, `THU-02` | Sửa UX app web sau test điện thoại: màn vào không tự mở camera (chọn Quét/Nhập tay), header logo không phải nút, layout mobile dính đáy, khung bám QR; ảnh thật + xem/sửa/chụp lại hồ sơ chờ nạp (+endpoint tải ảnh của mình) | ✅ | ✅ | 🟡 ghi UX | ⬜ |
| 11 | 01/10/2026 | ✏️ Sửa | `NAP-01` | "Kéo về từ VPS" làm tươi hồ sơ chưa nạp (collector sửa ở app web sau khi tool đã kéo → tool nhận bản mới); kéo không khóa | ✅ | ✅ | — nút có sẵn | ✅ |
| 10 | 01/10/2026 | ✏️ Sửa | `THU-02`, `NAP-01`, `QLY-01` | Thêm ô tìm kiếm (tên khớp cả không dấu / CCCD) ở 3 chỗ: app web Hồ sơ đã gửi · tool list tải về · tool lưới khóa. Màn hẹp thu gọn nút kính lúp | ✅ | ✅ | 🟡 prototype còn | ⬜ |
| 9 | 01/10/2026 | ✏️ Sửa | `THU-02` | Bỏ ô "nhập nơi cư trú khác" ở app thu nhận — chỉ thu nơi thường trú; cư trú để tool mặc định = thường trú (phương án A, không đổi schema) | ✅ | — đã khớp | ✅ demo | ⬜ THU-02 (P2) |
| 8 | 01/10/2026 | ✏️ Sửa | `HTG-01` | Chốt cách tool xác thực `/local/*` (task 17): option A (tool gọi VPS thay mặt → session cục bộ; collector 403) + A1 miễn token `/local/config*`+`/local/auth/*`. Còn mở: 1 hay n phiên | — | ✅ | — | ✅ task 17 |
| 7 | 01/10/2026 | ✏️ Sửa | `HTG-01` | TDD §3.2 ghi sót bảng `token_blocklist` (logout thu hồi phiên §5.1) — đồng bộ khi làm task 14 | — | ✅ | — | ✅ task 14 |
| 6 | 01/10/2026 | ✏️ Sửa | `NAP-01`, `QLY-01`, `NAP-06`, NFR⑥ | UX màn nạp: IA 2 chế độ (Nạp/Tra cứu); tên IN HOA khi kéo; check chính tả mức A; nạp lô badge đỏ/xanh; chuẩn cảnh báo inline nổi bật; tìm khóa mọi khóa (kể cả BC1) | ✅ | ✅ | ⬜ NAP-01 (P2) | ✅ C1 · ⬜ NAP-01 (P2) |
| 5 | 01/10/2026 | ✏️ Sửa + ➕ Thêm | `NAP-05`, `QLY-05` | Sau review TDD §10: nới ❌ NAP-05 cho UPDATE 5 cột ảnh (hướng A) + sửa tiêu đề "3 SP"→"1 SP gộp"; thêm story `QLY-05` Nạp/thay ảnh cho HV đã có | ✅ | ✅ | ⬜ QLY-05 | ⬜ |
| 4 | 01/10/2026 | ✏️ Sửa | `NAP-05` | Đổi đường nạp HV: 3 SP rời → **1 SP gộp app cũ** `usp_QuangLA_PM4_ThuNhanHS_ThemMoiCapNhat` (AS-003 phát hiện 3 SP rời lệch app cũ 5 field) | ✅ | ✅ | — | ⬜ làm lại |
| 3 | 01/10/2026 | ✏️ Sửa | `NAP-04`/`NAP-05` | Tên file ảnh: `70004-<timestamp>.jp2` → `<MaDK>.jp2` (khớp TDD §9.2 + verify thật) | ✅ | — | — | — (áp ở NAP-05) |
| 2 | 01/10/2026 | ✏️ Sửa | `NAP-03` | Dropdown Tỉnh (chọn tay) lấy trực tiếp từ `DM_DVHC` thay vì SP `usp_DM_DVHC_SelectAll_Tinh` | ✅ | — | — | ✅ (task 7) |
| 1 | 01/10/2026 | ✏️ Sửa | — | Đổi nơi lưu bảng ánh xạ `DM_DVHC_MAP`: GPLX_CSDT → SQLite cục bộ của tool | — | ✅ | — | ✅ (task 5) |

Chú thích: ✅ Xong · 🟡 Còn dở · ⬜ Chưa làm · — Không liên quan

---

## #88 — Nạp giờ/km nhận cả mẫu PDF DAT cũ và mới · 02/11/2026

- **Mã:** `KQD-08`. Số story giữ 63.
- **Vì sao:** file `DAT C1-K12` tải từ DAT ngày 02/11/2026 đổi mẫu: thêm cột Hạng, Mã khóa, đảo Họ tên với Mã học viên, giờ dạng `24.660`. Code đọc cột theo vị trí nên cả 72 dòng báo `Giờ 'C1' sai dạng`. User yêu cầu cả hai mẫu đều nạp được.
- **Giả định:** `24.660` là giờ thập phân (24,66 giờ). File không ghi đơn vị; user chưa đối chiếu với DAT, bảng xác nhận hiện giờ cũ → mới trước khi lưu.
- **Đã sửa:** PRD `KQD-08`, Changelog v4.29 · `tool/app/ketqua_dat.py`, `tool/tests/test_ketqua_dat.py` (5 test đọc mẫu thật trước đó bị bỏ qua do file đã chuyển vào thư mục con, nay chạy lại). TDD §11D.10 v6.31.
- **Đính chính:** commit `b89b7a1` ghi "mã có chữ G đầu, giữ chặn, nhập tay" là chẩn đoán sai. User chỉ ra và đã kiểm trên file: `G` là chữ cuối của họ tên dài tràn sang ô mã (tên thiếu `G` + mã thừa `G`, thêm vào thì khớp DB nguyên văn). Đã sửa cách đọc, không cần nhập tay hay hỏi bên DAT.
- **Còn nợ:** chưa thử lại trên màn hình với bản đã sửa tràn chữ.

## #87 — Thông báo đã gửi nêu tên học viên · 02/11/2026

- **Mã:** `THU-01`. Số story giữ 63.
- **Vì sao:** user hỏi nhập nhiều có nhầm không. "Đã gửi ✓" không cho biết vừa gửi hồ sơ nào.
- **Đã sửa:** PRD `THU-01`, Changelog v4.28 · `Quet.tsx`. Cùng đợt có BUG-17, BUG-18 ở `BUGS.md`.
- **Còn nợ:** đã deploy `210c5e1`, chưa thử điện thoại thật; hoàn tác khi xóa bằng, đậm lại chữ và viền chưa làm vì user chọn phạm vi A.

## #86 — Báo lỗi form dễ sửa trên điện thoại · 02/11/2026

- **Mã:** `THU-01`, `THU-07`. Số story giữ 63.
- **Vì sao:** critique giao diện màn nhập hồ sơ (24/40): câu lỗi cũ còn nguyên sau khi đã sửa đúng, nằm xa ô sai; mở khối GPLX là báo đỏ khi chưa nhập gì; chữ 14px làm iPhone tự phóng to. User duyệt sửa.
- **Đã sửa:** PRD `THU-01`, `THU-07`, Changelog v4.27 · `Quet.tsx`, `DaGui.tsx`, `GplxDaCoKhoi.tsx`, `gplxDaCo.ts`, `index.css`. Không đổi dữ liệu gửi nên TDD giữ nguyên.
- **Ngoài bảng duyệt, bắt buộc để chạy được:** trên điện thoại câu lỗi chuyển vào thanh nút dính đáy, vì con trỏ đã nhảy tới ô sai ở xa thì câu lỗi cuối form không nhìn thấy. Chữ 16px áp cho mọi ô `.field-input` của app web, gồm cả màn đăng nhập và quản lý.
- **Còn nợ:** đã deploy `f8f3fb7`, chưa thử điện thoại thật, bàn phím ảo. CSS build ra cú pháp `@media (width<=…)`: Safari dưới 16.4 bỏ qua, ô nhập giữ 14px. Các mục critique P2 chưa làm: vùng bấm 44px, hoàn tác khi xóa bằng, gắn nhãn cho trình đọc màn hình.

## #85 — Dọn việc treo sau deploy GPLX đã có · 02/11/2026

- **Vì sao:** user yêu cầu làm hết việc treo.
- **Đã làm:** job PII thêm `deleted` (trước đó hồ sơ xóa mềm giữ `so_cccd` mãi) · sao lưu DB đêm `deploy/backup-db.sh` (biên bản `docs/soatdeploy-02-11-2026.md`) · Sync thật hồ sơ hai bằng trong giao dịch hủy: giữ nguyên chuỗi · `A`→`A2` có căn cứ danh mục · mock Nơi cấp theo `DM_DonViGTVT`.
- **Còn nợ (cần người):** bấm nút Nạp thật + mở phần mềm cũ · gửi thật trên điện thoại · đổi mật khẩu `admin@123` · quyết script sửa `CHON_IN_GPLX` dữ liệu cũ · KQD task 145.

## #84 — Giữ Cục QLHC mã 00, script bật ở DB Nạp · 02/11/2026

- **Mã:** `NAP-07`, `THU-07`.
- **Vì sao:** user yêu cầu giữ Cục QLHC, lấy mã theo DB đích và có script bật ở DB Nạp. DB đích: `DM_DVHC` `00` = Cục QLHC; `DM_DonViGTVT` `00` = "Cục CSGT". DB Nạp: `DM_DonViGTVT` `00` = "Tổng cục đường bộ Việt Nam", tắt; chưa có GPLX đã có nào dùng `00`.
- **Đã làm:** `scripts/them_cuc_qlhc_dm_donvigtvt.sql` (đã thử trong giao dịch hủy, tờ khai ra `Cục QLHC`) · bản chụp app web · PRD v4.26 · TDD v6.30.
- **Còn nợ:** chạy script trên từng DB Nạp · tên `00` ở DB đích là "Cục CSGT", khác DB Nạp.

## #83 — GPLX đã có khớp form cũ sau khi rà DB + DLL · 02/11/2026

- **Mã:** `NAP-07`, `THU-07`. Số story giữ 63.
- **Vì sao:** user yêu cầu rà schema/procedure để suy ra và chốt. Rà ra form cũ `FPT.GPLX.CSDT.dll` có quy tắc chặn mà thiết kế #81 chưa có, và tờ khai đọc tên đơn vị từ `DM_DonViGTVT` chứ không phải `DM_DVHC`.
- **Bằng chứng cách lưu `|`:** lưới `dgvsDSGPLXHienCo`; `getTenDVCap('70|79')` ra `Bình Phước|Hồ Chí Minh`; hồ sơ `A1|A1` đã qua BC2 `720/23`, kết quả sát hạch `DA`.
- **Đã sửa:** PRD v4.25 · TDD v6.29 · decisions §28 · code tool, VPS, app web + test.
- **Còn nợ:** xem #85.

## #82 — /reviewtdd §10.6 GPLX đã có · 02/11/2026

- **Mã:** `NAP-07`, `THU-07`. Số story giữ 63.
- **Vì sao:** subagent `review-tdd` phát hiện 2 lỗi mất dữ liệu trong thiết kế: người thu hồ sơ mở lại thấy ô GPLX trống, và câu mô tả nháp tự mâu thuẫn.
- **Chốt (user 02/11/2026, phương án A):** nhân viên đã sửa mà app web đổi sau đó → giữ bản đã sửa, hiện cờ "App web có bản mới" + nút "Dùng bản app web".
- **Đã sửa:** TDD §10.6, ghi chú §4 (v6.28) · PRD `NAP-07` (v4.24) · biên bản `docs/tdd-review-02-11-2026-gplx-da-co.md`.
- **Còn nợ:** hồ sơ xóa mềm còn giữ `so_cccd` mãi vì job dọn 30 ngày bỏ qua trạng thái `deleted` (có từ trước, user quyết sau).

## #81 — GPLX đã có: nhập ở app web và tool, nhiều bằng, chip + lọc · 02/11/2026

- **Mã:** `NAP-07`, `THU-07` (mới). Không hạ `NAP-01`, `NAP-05`: tách story riêng để không trộn với việc đang chờ nghiệm thu. Số story 61→63.
- **Vì sao:** tool truyền trống 7 trường, nên học viên `A1`/`A1m` đã có bằng ô tô không được ghi nhận miễn thi lý thuyết. Phần mềm cũ có điền 6.973/39.930 hồ sơ (17,46%), năm 2026 là 934/3.537; 0 hồ sơ trùng hạng đăng ký.
- **Chốt (user 02/11/2026):** nhập được ở app web; tool tự điền và sửa được; có chip + lọc; **không thêm bớt schema DB Nạp**.
- **Vì sao vẫn giữ Sync:** user đề nghị bỏ nếu DB đích không cần. Đã kiểm: không bắt buộc nhập (cột cho phép NULL), nhưng hàm miễn lý thuyết, BC1/BC2, XML đều đọc; 454/741 hồ sơ đích đang có giá trị. Đã trình user kèm kế hoạch được duyệt.
- **Đã sửa:** PRD (+`NAP-07`, +`THU-07`, v4.23) · TDD (+§10.6, §3, §4.4, v6.27) · decisions §28 · SCREENS #36 · mock `ui-mock/gplxdaco.html`.
- **Code có thể phải đụng:** `tool/app/nap.py` (`build_params_sp_gop`, `keo_ve`, nháp, `nhap_co`) · `tool/app/routers/nap.py` · `tool/webui/src/pages/tool/NapHoSo.tsx` · `tool/webui/src/lib/api.ts` · `server/app/models/ho_so.py`, `routers/ho_so.py`, `routers/nap.py`, `jobs/pii.py`, `db/init.sql` · `webapp/src/pages/Quet.tsx`.
- **Còn nợ:** mock chờ duyệt · `/reviewtdd` · `/kehoach` bổ sung · code · nghiệm thu máy CSĐT.
- **Rủi ro cần đối chiếu:** nối `|` chỉ có 1 hồ sơ mẫu, chưa biết file gửi Sở có nhận, tờ khai in nguyên `|` · bảng nhãn ↔ mã suy từ khóa thật (`A`→`A2` mới có 2 khóa).

## #80 — /reviewtdd "Chọn in GPLX": làm rõ TDD + xóa lựa chọn tay khi đổi khóa khác loại · 16/10/2026

- **Mã:** `NAP-05` · `NAP-01` (không thêm/nghỉ hưu mã, số story giữ 61).
- **Vì sao:** subagent `review-tdd` soát độc lập phần mới của #79 — 0 Chặn, 4 Nên sửa, 5 Ghi nhận. Điểm đáng quyết: nhân viên chọn tay "không thời hạn" khi khóa đang là mô tô, rồi đổi khóa nạp sang ô tô → học viên vẫn mang "không thời hạn" mà không ai để ý.
- **Chốt (user 16/10/2026, phương án A):** đổi sang khóa khác loại → xóa lựa chọn tay của các hồ sơ đang mở, ô về mặc định theo khóa mới; chọn lại đúng giá trị mặc định coi như chưa đổi (lưu trống).
- **Đã sửa tài liệu:** TDD (§9.3a +cột `chon_in_gplx` · §10 Phục vụ +NAP-01 · §10.2 server dùng giá trị client gửi, quy tắc ghi nháp · dòng `MaLoaiHs`, Changelog v6.26) · biên bản `docs/tdd-review-16-10-2026-in-gplx.md`.
- **Đã code:** `NapHoSo.tsx` (hiệu ứng theo loại khóa + lưu trống khi chọn lại mặc định) + 2 ca e2e `in-gplx.e2e.ts`.
- **Còn nợ:** nháp cũ chưa mở trong phiên mang lựa chọn "ghép" (1) vẫn giữ qua đổi khóa (ô hiện giá trị đó khi mở) · quyết định script sửa HV mô tô đã nạp mang 2 trước khi đóng NAP-05 · nghiệm thu máy CSĐT (task 148).

## #79 — Ô "Chọn in GPLX" theo hạng khóa khi Nạp · 16/10/2026

- **Mã:** `NAP-05` · `NAP-01` (không thêm/nghỉ hưu mã, số story giữ 61).
- **Vì sao:** tool cũ gán cứng `CHON_IN_GPLX=2` (AS-003 chỉ thử học viên ô tô). DB Nạp thật: ô tô ~15.000 HV = 2, mô tô A1/A1m/A2 ~17.000 HV = 3, hiếm 1 (ghép) → khóa mô tô nạp bằng tool bị ghi sai. Phần mềm CDB đọc cột này đưa vào file BC1/BC2 gửi Sở nên DB đích cũng phải đúng.
- **Chốt (user 16/10/2026):** mô tô (hạng bắt đầu `A`) mặc định "không thời hạn" (3), ô tô mặc định "có thời hạn" (2); UI Nạp hiện ô chọn điền sẵn kèm tên loại in bằng chữ, đổi được từng học viên; Sync chép nguyên giá trị từ DB Nạp sang DB đích ("đích có cột thì cứ đồng bộ sang").
- **Đã sửa tài liệu:** PRD (NAP-05: +tiêu chí "Chọn in GPLX theo hạng khóa", sửa 3 chỗ "=2", hạ ✅→⚠️ · NAP-01: +tiêu chí ô ở ngăn Chuẩn bị · AS-003 ghi chú · Changelog v4.22) · TDD (§10.1 sơ đồ, §10.1 chú thích, §10.2 field map + nháp + UI + Sync, Changelog v6.25) · TDD-decisions (§10 ghi "Đã từng chốt =2" + lý do đổi).
- **Đã code (16/10/2026, chưa commit):** `tool/app/nap.py` (`chon_in_gplx_mac_dinh`, `build_params_sp_gop`, nháp `chon_in_gplx` + migrate) · `routers/nap.py` (`NapIn`/`NhapChuanBiIn` + validator 422) · `sync_service.py` (`_HV_SELECT`, `_INSERT_HOSO`) · webui `inGplx.ts`, `NapHoSo.tsx`, `lib/api.ts` · test `tool/tests/test_in_gplx.py` (38), `inGplx.test.ts`, `e2e/in-gplx.e2e.ts` (9).
- **Còn nợ:** (1) **nghiệm thu máy CSĐT** — nạp thử 1 HV mô tô + 1 HV ô tô, mở app cũ đối chiếu ô "Chọn in GPLX", đồng thời đối chiếu **thứ tự 3 dòng trên ô `cboInGplx`** với 1/2/3 (nếu khác chỉ sửa bảng nhãn `IN_GPLX_NHAN`); (2) HV mô tô **đã nạp trước đây** mang 2 (sai) và ~739 HV ở DB đích đang 0 (25 HV đã vào BC2) → cần script cập nhật riêng nếu muốn; (3) **chưa xác minh Sở có dùng trường này** trong XML BC1/BC2 (có thể kiểm bằng mở một `BC2_*.zip` đã gửi, chỉ đọc); (4) `/kehoach` bổ sung 1 task (đã làm xong) + đóng gói lại exe.

## #78 — Đồng bộ PRD + mock với TDD v6.23 sau /reviewtdd KQD-04 · 16/10/2026

- **Mã:** `KQD-01` · `KQD-04` · `KQD-07` (không thêm/nghỉ hưu mã, số story giữ 61; trạng thái đã ⏳ từ #77).
- **Vì sao:** `/reviewtdd` §11D.13 (20 phát hiện) đổi hành vi so với PRD v4.19 và user bổ sung giữa buổi: "phải có cảnh báo chưa giải trình thì không kết xuất được". HV `90` Không đạt/trống kết luận từng không thuộc nhóm nào (vô hình) → gom vào tab "Cần xử lý".
- **Đã sửa:** PRD KQD-01 (tab + 2 chip) · KQD-04 (cảnh báo bắt buộc, giữ giải trình riêng, lô kiểm đủ điều kiện, mất kết nối, mẫu theo cơ sở) · KQD-07 (+3 chip) · mock `ui-mock/ketqua.html` · SCREENS #21. TDD không đổi (đã ở v6.23).
- **Bổ sung cùng ngày (user: "header làm gọn lại, tối ưu hiển thị list"):** header lưới còn 2 hàng, khung giải trình chung thu gọn (nút ở hàng tab) — PRD KQD-01 + mock; bảng lên cao ~170px.
- **Bổ sung cùng ngày (user hỏi "mẫu có tạo thêm/sửa được không", chọn A):** thêm hộp **"Quản lý mẫu"** (sửa, xóa, thêm) — PRD v4.21, TDD v6.24, mock; dùng lại `PUT mau-giai-trinh`, không thêm endpoint.
- **Còn nợ:** user duyệt mock → `/kehoach` bổ sung nhẹ (task 137 khóa ghi cấu hình + mẫu theo cơ sở; task 140 + chip) → `/tieptheo` task 136.

## #77 — KQD-04: HV Sở từ chối sửa xong → "Đang giải trình" + giải trình hàng loạt + cột Trạng thái · 16/10/2026

- **Mã:** `KQD-04` (viết lại), `KQD-01` · `KQD-03` · `KQD-07` (sửa nhẹ). Không thêm/nghỉ hưu mã, số story giữ 61.
- **Vì sao:** user hỏi sửa điểm Đường trường/Sa hình cho HV Sở từ chối rồi kết xuất lại. Verify DB 16/10: SP đọc danh sách kết xuất của CDB lọc `09`/`90` + `KetLuanCSDT=1`; SP ghi điểm giữ `14`; **không thủ tục nào đặt `90`** ⇒ HV `14` sửa xong kẹt. Giải trình từng dòng quá chậm khi nhiều HV; lưới lẫn Đạt/Không đạt với nhãn Sở từ chối nên khó thấy HV đang ở đâu.
- **Đã sửa:** PRD KQD-01 (cột Trạng thái + tab đếm + lý do từ chối trên dòng) · KQD-02 (dòng trỏ KQD-04) · KQD-03 ("còn sót" gồm `90` Đạt) · KQD-04 (viết lại Done khi) · KQD-07 (xét `90`) · TDD §11D.1/.6/.9 + **§11D.13 mới** · decisions §27.
- **Hạ trạng thái:** KQD-04 ⚠️→⏳ · KQD-01 ✅→⏳ · KQD-03 ⚠️→⏳ · KQD-07 ✅→⏳ (yêu cầu đổi, code cũ lỗi thời).
- **Giả định ghi rõ:** chỉ chuyển `90` khi Đạt + có giải trình; Không đạt giữ `14`.
- **Mock:** `ui-mock/ketqua.html` đã cập nhật 16/10 (cột Trạng thái + việc cần làm, 6 tab đếm gồm tab "Không đạt", chú giải, giải trình chung + mẫu, tích chọn + hộp chuyển hàng loạt, mô phỏng quy tắc 14→90) — **chờ user duyệt**.
- **`/reviewtdd` §11D.13 (16/10/2026):** 20 phát hiện (3 Chặn · 11 Nên sửa · 6 Ghi nhận), user chọn sửa tất cả → TDD v6.23 + decisions §27 cập nhật + biên bản `tdd-review-16-10-2026-kqd04.md`; thêm yêu cầu user: **cảnh báo "chưa giải trình thì không kết xuất được"** (4 chỗ). Đổi so với PRD v4.19: tab "Sở từ chối" → "Cần xử lý", chip `giai_trinh_trong`, mẫu theo cơ sở — **cần `/capnhat` đồng bộ PRD + mock**.
- **Còn nợ:** user duyệt mock → `/kehoach` bổ sung task → code (`cap_nhat` + `giai-trinh-lo` + mẫu + webui) · SCREENS #21 ghi chú · nghiệm thu máy CSDT (phần mềm CDB có tự đặt `90` không).

## #76 — /reviewtdd §11D.12 (KQD-10): đồng bộ TDD + 6 sửa code · 12/10/2026

- **Mã:** `KQD-10` (không thêm/bớt mã, số story giữ 61). Trạng thái giữ ⏳ Todo → chờ in thử trên Excel thật + nghiệm thu.
- **Vì sao:** `/reviewtdd` bằng subagent sau khi code + test xong: **0 Chặn · 5 Nên sửa** (1.1 viền/chân trang/hàng lệch mẫu; 1.2 chân trang có thể đè dòng cuối; 1.3 §11D.6 còn ghi `GET`; **2.1 xếp sai tên có dấu kiểu cũ — Hòa/Hoà, Thúy/Thuý**; 3.1 độ rộng cột B đoán thấp với tên VIẾT HOA) · **6 Ghi nhận** (2.2, 2.3, 2.4, 3.2–3.4 + số dòng/trang). User gật tất cả theo đề xuất.
- **Đã sửa:** TDD v6.21 (§11D.6, §11D.12) · TDD-decisions §26 (cập nhật) · PRD v4.18 · biên bản `docs/tdd-review-12-10-2026-kqd10.md` · code: `ketqua_so.py` (viền, chân trang, hàng 5/9, footer, thanh điệu, độ rộng theo ký tự, chiều cao hàng 2, `dem_trong_ket_qua`), `routers/ketqua.py` (`so_hv_trong_ket_qua`), `CapNhatKQDT.tsx` (dòng lưu ý).
- **Test:** 871 pytest · Playwright `xuat-excel` 8 ca.
- **Còn nợ:** mở file bằng Excel thật + in thử A4 (xác nhận số dòng/trang, tên không bị thu nhỏ, chân trang không đè) · `/kehoach` bổ sung task `KQD-10` · nghiệm thu khóa thật.

## #75 — Xuất Sổ theo dõi kết quả học tập (KQD-10) · 12/10/2026

- **Mã:** `KQD-10` (mã mới, cùng prefix KQD) + sửa nhỏ `KQD-09` (ngày lập). **Số story 60 → 61.**
- **Vì sao:** user 12/10: *"ở module Nhập kết quả học tập tôi muốn có 1 nút xuất Sổ theo dõi kết quả học tập giữ các format như file …So_theo_doi_ket_qua_hoc_tap_DTLX_TT17.xlsx; danh sách có tiêu đề qua các trang, tên cơ sở đào tạo được cấu hình, đánh số trang, khổ A4, xếp alphabet tên"*; sau đó chốt: không in trang điểm quy đổi/chi tiết, font Times New Roman, tên không xuống dòng, lề sát mép, **không thêm bìa**, ngày chỉ dd/mm/yyyy.
- **Đã sửa:** PRD v4.17 (+KQD-10; KQD-09 ngày lập) · TDD v6.20 (+§11D.12, §11D.6) · TDD-decisions §26 · SCREENS #21 · code `ketqua_so.py` (mới), `routers/ketqua.py` (`POST /xuat-so-theo-doi`, tách `_doc_khoa_va_hv`/`_luu_file_xuat`), `CapNhatKQDT.tsx`, `api.ts`, `ketqua_xuat.py` (`ten_file` có tiền tố; ngày lập).
- **Test:** 865 pytest (có so trực tiếp với file mẫu) · 102 vitest · Playwright `xuat-excel` 6 ca.
- **Phát hiện khi dựng thử từ DB dev (B.01-K40, 30 HV):** 25 HV có kết luận Đạt nhưng **chỉ 1 HV đủ 5 điểm** (dữ liệu PM cũ lưu kết luận mà thiếu điểm môn) → theo luật sổ mẫu đã chốt, 29 dòng để trống cột Kết quả. Chờ user xem lại luật nếu muốn hiện theo kết luận.
- **Còn nợ:** mở file bằng Excel + in thử A4 (máy dev không có LibreOffice để dựng PDF kiểm số trang) · `/reviewtdd` §11D.12 · `/kehoach` bổ sung task · nghiệm thu khóa thật.

## #74 — KQD-09: lưu vào thư mục output + bỏ dấu chấm thừa giờ/km sân · 12/10/2026

- **Mã:** `KQD-09` (không thêm/bớt mã, số story giữ 60). Trạng thái giữ **⚠️ Partial**.
- **Vì sao:** user dùng thử file xuất: *"giờ sân và km sân lúc xuất ra có dấu chấm đằng sau, xóa dấu chấm đi; file excel xuất mặc định lưu ở thư mục output của phần mềm"*. Nguyên nhân dấu chấm: định dạng ô `0.##` của Excel hiện `34.` với số nguyên.
- **Đã sửa:** PRD v4.16 (Done khi lưu `output`, định dạng số) · TDD v6.19 (§11D.11: POST + `luu_file` + `mo-thu-muc-xuat`, định dạng ô) · TDD-decisions §25 (cập nhật) · code: `paths.output_dir()`, `ketqua_xuat.luu_file`, `POST /xuat-excel` + `POST /mo-thu-muc-xuat`, `CapNhatKQDT.tsx` (toast đường dẫn + nút Mở thư mục), `.gitignore` (`tool/output/`).
- **Lưu ý:** tool trước đó chưa có thư mục `output` nào; tạo mới ở cạnh exe (dev: `tool/output`).
- **Test:** 846 pytest · Playwright `xuat-excel` 4 ca.

## #73 — /reviewtdd §11D.11 (KQD-09): đồng bộ TDD + 4 sửa code · 12/10/2026

- **Mã:** `KQD-09` (không thêm/bớt mã, số story giữ 60). Trạng thái giữ **⚠️ Partial**.
- **Vì sao:** `/reviewtdd` bằng subagent sau khi code + test xong: **2 Chặn** (4.1 công thức Excel lọt vào file qua họ tên/cơ sở; 3.1 một ký tự điều khiển làm hỏng cả file) · **6 Nên sửa** (1.2, 1.3, 2.1, 2.2, 4.2, 6.1) · **5 Ghi nhận** (1.1, 2.3, 3.2–3.4). User chọn đề xuất cho tất cả.
- **Đã sửa:** TDD v6.18 (§11D.11 viết lại: sơ đồ + bảng, lỗi/header, hệ quả §25, an toàn dữ liệu, hiệu năng, ghi nhận) · TDD-decisions §25 (cập nhật) · PRD v4.15 (nhãn tóm tắt + Done khi an toàn dữ liệu) · biên bản `docs/tdd-review-12-10-2026-kqd09.md` · code: `ketqua_xuat.py` (`_sach`/`_ghi_chu`, hạng ổn định, nhãn), `routers/config.py` (`PUT /co-so` gác phiên), `CauHinhForm.tsx` (báo cần đăng nhập).
- **Test:** 840 pytest · Playwright `xuat-excel` 5 ca.
- **Còn nợ:** mở file bằng Excel thật + in thử A4 ngang · nghiệm thu khóa thật ở máy CSĐT · `/kehoach` bổ sung task · `/subagent` bổ sung.

## #72 — Xuất Excel kết quả học tập theo từng khóa (KQD-09) · 12/10/2026

- **Mã:** `KQD-09` (mã mới, cùng prefix KQD). **Số story 59 → 60.** Không đổi story nào đang có.
- **Vì sao:** user 12/10/2026: *"thêm nút xuất file excel kết quả học tập của từng khóa, đề xuất form UI excel xuất những thông tin gì"*. Form đề xuất bám sổ mẫu `thamkhao/So_theo_doi_ket_qua_hoc_tap_DTLX_TT17.xlsx`; user chốt: 1 sheet bảng chi tiết · mọi HV đang hoạt động · cơ sở nhập ở Cấu hình · ngày xét hoàn thành = ngày thi khóa.
- **Đã sửa:** PRD v4.14 (+`KQD-09`) · TDD v6.17 (+§11D.11, §11D.6, tiêu đề §11D) · TDD-decisions (+§25) · `ui-demo/SCREENS.md` (#21 ghi chú nút).
- **Đã code (12/10/2026):** `tool/app/ketqua_xuat.py` · `GET /local/ketqua/xuat-excel` · `PUT /local/config/co-so` + khối ③ ở `CauHinhForm.tsx` · nút "Xuất Excel" ở `CapNhatKQDT.tsx` (`xuatExcelKQD` ở `api.ts`) · `openpyxl` vào requirements + `tool.spec` + `--selftest`. Test: 826 pytest · 102 vitest · Playwright 5 ca. Dựng thử từ DB dev thật OK. Bản exe đóng gói thử ở `tool/build/dist/` (selftest đạt) vì exe ở `tool/dist/` đang chạy.
- **Phát hiện kèm theo — ĐÃ SỬA cùng ngày (user gật):** `PUT /local/config` từng ghi đè **toàn bộ** `config.enc` bằng 6 trường kết nối, nên lưu khối ① làm rơi các khóa khác (chương trình KQĐT theo khóa `kqd_chuong_trinh`, cấu hình Sync). Nay **gộp** vào cấu hình đã có (`{**saved, **moi}`), secret đang che vẫn giữ; có test hồi quy ở `test_config_moitruong.py`. Không đổi yêu cầu PRD (HTG-01 giữ nguyên trạng thái).
- **Còn nợ:** `/kehoach` bổ sung task · `/reviewtdd` §11D.11 · `/subagent` bổ sung (mảng xuất Excel chưa có người soát) · mở file bằng Excel thật + in thử · nghiệm thu khóa thật ở máy CSĐT.
- **Cũng ghi bù (cùng buổi):** dòng #69 cột Code ⬜ → ✅ (code đã có từ commit `d2073ea`…`5b7f8f7`).

## #71 — /reviewtdd §11D.10 (KQD-08): đồng bộ TDD + 2 sửa code · 12/10/2026

- **Mã:** `KQD-08` (không thêm/bớt mã, số story giữ 59). Trạng thái giữ **⚠️ Partial**.
- **Vì sao:** `/reviewtdd` chạy bằng subagent soát độc lập §11D.10 sau khi code + test xong: 0 Chặn · 4 Nên sửa (F1 TDD lệch code, F3 "chọn tất cả" tick cả dòng chưa chạy DAT, F5 `rowcount`, F6 lý do sai khi vượt trần tra) · 3 Ghi nhận (F4, F7, F8). User chọn: F1/F3/F4/F6 sửa, F5/F7/F8 ghi nhận.
- **Đã sửa:** TDD v6.16 (§11D.6 + §11D.10: endpoint đã chốt, sơ đồ + bảng tình trạng, luật chọn tất cả, trần tra lý do, rủi ro đã biết) · TDD-decisions §24 · biên bản `docs/tdd-review-12-10-2026-kqd08.md` · code: `NapDatModal.tsx` (chọn tất cả chỉ `khop`), `ketqua.py` + `ketqua_dat.py` (`chua_tra`, câu cho dòng vượt trần).
- **Test:** 808 pytest · Playwright `nap-dat-pdf` 9 ca (thêm F3) · 3 ca pytest mới cho trần tra cứu.
- **Còn nợ:** nghiệm thu ghi thật máy CSĐT (Checkpoint 32) · build lại exe khi mang sang máy CSĐT (UI đổi sau bản `3ff1e8e`).

## #70 — Chốt 6 điểm sau /kiemthu KQD-08/KQD-02 · 12/10/2026

- **Mã:** `KQD-08`, `KQD-02` (không thêm/bớt mã, số story giữ 59). Cả hai giữ **⚠️ Partial** (chờ nghiệm thu ghi thật ở máy CSĐT).
- **Vì sao:** `/kiemthu` (subagent `sinh-testcase` soát độc lập) nêu 6 điểm PRD mơ hồ hoặc code lệch; user chọn đề xuất của tôi cho cả 6.
- **Đã sửa:** PRD v4.13 (KQD-02: chỉ sửa giờ/km, giây, làm tròn · KQD-08: điền sẵn 0, `TrangThai=1`, mã khóa chữ+số) · TDD v6.15 (§11D.10) · code: `ketqua_dat.py` (regex mã khóa), `routers/ketqua.py` (`TrangThai = 1`), `NapDatModal.tsx` (điền sẵn 0).
- **Test:** 805 pytest · 102 vitest · Playwright 13 ca hai file (thêm E12 điền sẵn 0, ca mã khóa dính liền, ca `TrangThai = 1`, vector giây dùng chung hai bên).
- **Còn nợ:** `/kehoach` bổ sung task KQD-08 · đóng gói lại exe + kiểm `pdfplumber` trong exe · nghiệm thu ghi thật máy CSĐT.

## #69 — Nạp giờ/km đường từ PDF DAT + ô giờ nhận hh:mm (KQD-08, KQD-02) · 12/10/2026

- **Mã:** `KQD-08` (mã mới, cùng prefix KQD) · `KQD-02` (sửa). **Số story 58 → 59.** `KQD-02` hạ **⚠️ Partial → ⏳ Todo** vì yêu cầu đổi (dòng "giờ/km đường để trống" thành "nạp sẵn giá trị đã lưu" + giờ nhận `hh:mm`).
- **Vì sao:** user 12/10/2026: giờ đường phải gõ tay từng HV, không nhập được `hh:mm`, và DB đích đã có giờ thì mở ra vẫn trống; muốn *"nạp file ở khóa học … ra bảng để xác nhận … lưu cho nhanh thay vì gõ tay"*. Chốt: nhận **thẳng PDF DAT** (không qua Excel); số đã có ở DB **là giờ thập phân**, giữ nguyên. Phát hiện kèm theo: lưu sửa lẻ điểm khi ô giờ trống gửi `null` và SP `_CapNhat` **ghi NULL đè giờ cũ**.
- **Đã sửa:** PRD v4.12 (+`KQD-08`; KQD-02: trạng thái, Done khi giờ/km đường, edge `hh:mm` sai, Changelog) · TDD v6.14 (+§11D.10, tiêu đề §11D, "Phục vụ") · TDD-decisions (+§24) · `ui-demo/SCREENS.md` (#21 ghi chú, +#35 hộp thoại nạp PDF).
- **Còn nợ:** code theo kế hoạch đã duyệt: `tool/app/ketqua_dat.py` mới · 2 endpoint + `/hoc-vien` trả thêm giờ/km · `NapDatModal.tsx` + `gioThucHanh.ts` + sửa `CapNhatKQDT.tsx` · thêm `pdfplumber` vào requirements + `tool.spec` · `/kehoach` bổ sung 1–2 task · nghiệm thu ghi thật ở máy CSĐT.
- **Đã code (12/10/2026):** `tool/app/ketqua_dat.py` + 2 endpoint `/dat/xem-truoc`, `/dat/luu` + `/hoc-vien` trả giờ/km · `NapDatModal.tsx`, `gioThucHanh.ts`, sửa `CapNhatKQDT.tsx` · `pdfplumber` vào requirements + `tool.spec`. Test: 740 pytest · 77 vitest · build OK; xem trước chạy trên DB dev thật (K40 30/30 khớp, C1-K11 31/32 + 1 chưa chạy DAT). **Trạng thái KQD-08 + KQD-02: ⚠️ Partial** (UI đã chạy qua Playwright backend giả; chưa ghi thật ở máy CSĐT).
- **Bổ sung 12/10/2026 (user yêu cầu khi dùng thử):** (1) dòng "Không có trong khóa" kèm **lý do** (khóa khác / không hoạt động / lệch mã / không tìm thấy) · (2) **sửa số ngay trong bảng xem trước** (nhận hh:mm, tô "đã sửa", sai dạng chặn Lưu). Test: 747 pytest · 79 vitest · Playwright 98 ca pass.
- **Đã xác minh:** "Mã học viên" = `MaDK` (62/62 dòng) · SP `_CapNhat` ngoài giờ/km chỉ thêm `NgaySua = GETDATE()` → UPDATE của KQD-08 đặt `NgaySua` như SP.
- **Còn mở:** chưa có mock UI hộp thoại (code theo bố cục trong kế hoạch; muốn duyệt thì bổ sung `ui-mock/ketqua.html`) · 2 khóa mẫu (B.01-K39, C1-K10) không có trong DB dev nên chưa đối chiếu · `/kehoach` bổ sung task chưa chạy (code đã làm trước kế hoạch) · đóng gói lại exe và kiểm `pdfplumber` chạy được trong exe.

## #68 — Ghi quyết định KQD-07/PCG-06 + đồng bộ TDD với code · 12/10/2026

- **Mã:** `KQD-07`, `PCG-06` (không thêm/bớt mã, số story giữ 58). Cả hai đang 🔄 nên **không hạ trạng thái**.
- **Vì sao:** (1) user chốt 12/10: *"nhập kết quả học tập chỉ nhập cho hạng ô tô thôi, chưa nhập thì chỉ cảnh báo vẫn cho lưu các ô đã nhập"* — thay câu "mô tô ẩn bớt ô thực hành" trong PRD; (2) khi dựng mock user chốt A hai điểm UX (ẩn chip "Thiếu giờ/km" khi chưa có điểm; khóa toàn mô tô hiện thông điệp riêng); (3) code task 119/121 đã làm khác TDD ở vài chỗ (tài liệu lag code, không đổi yêu cầu).
- **Đã sửa:** PRD v4.11 (KQD-07: Done khi môn bắt buộc, chip chưa có điểm, KQD-02 giữ nguyên, edge khóa mô tô, nguồn; PCG-06: nguồn + mock) · TDD v6.13 (§11D.9: chữ ký `hv_chua_du(hv)`, response, luật `chua_co_diem`, UI; §11E.10: `phancong_hangiayto.py`, lọc `TrangThai=1`).
- **Còn nợ:** code UI task 120 (khung kiểm trước + KQD-02 gọi chung nguồn luật, bỏ `tinhDong` riêng ở `CapNhatKQDT.tsx`) và task 122 (tab Hạn giấy tờ) · **❓ chưa chốt:** cảnh báo vàng giờ/km đường dưới mức gợi ý — backend trả thêm trường hay UI tự tính từ lưới (quyết khi code task 120) · `/reviewtdd` phiên mới cho §11D.9 · nghiệm thu Checkpoint 29 ở máy CSĐT.

## #67 — Đổi nền cả khóa ghi đè đúng file ở DuongDanAnh (QLY-07) · 12/10/2026

- **Mã:** `QLY-07` (không thêm/bớt mã, số story giữ 58). Hạ **⚠️ Partial → ⏳ Todo** vì yêu cầu ghi ảnh đổi.
- **Vì sao:** HV vào DB Nạp rồi sync sang DB đích, `DuongDanAnh` sao chép nguyên văn nên hai DB trỏ cùng một file (đọc DB 12/10/2026: 668/741 đường dẫn ở đích trùng đường dẫn ở Nạp). Code đổi nền cũ (`doinen.py` → `ghi_anh_update`) ghi vào `<IMG_PATH_CSDT>\<MaKH>\<MaDK>.jp2` rồi UPDATE `DuongDanAnh`: với 154 ảnh ở `\\192.168.1.15\GPLXCSDT\ANHCDUNG` và 87 ảnh ở `\\192.168.0.10\...\Capmoi\70004` sẽ tạo file mới ở thư mục khác, đổi đường dẫn ở Nạp, còn DB đích vẫn trỏ file cũ chưa đổi nền. Thay ảnh ở đích (TCB-02) đã đúng nguyên tắc nên QLY-07 sửa theo TCB-02.
- **Đã sửa:** PRD v4.10 (QLY-07: trạng thái, Done khi, edge case ảnh ở gốc khác, nguồn, Changelog) · TDD v6.12 (§11.6: ghi đè tại `DuongDanAnh`, không dùng `ghi_anh_update`, sao lưu `<tên>_BACKUP.jp2` cùng thư mục, ghi "Đã từng chốt" kiểu `<khóa>\_BACKUP\<MaDK>.jp2`) · `ui-demo/SCREENS.md` #15 (ghi chú).
- **Còn nợ:** sửa code `tool/app/doinen.py` (`xu_ly_mot`, `_backup_neu_chua`) + cập nhật `tool/tests/test_doinen.py` · `/kehoach` bổ sung 1 task · nghiệm thu máy CSĐT (ổ `D:\GPLXCSDT`) · ảnh đã đổi nền bằng bản cũ (nếu có chạy trên khóa thật) cần kiểm: file ở `<IMG_PATH_CSDT>\<MaKH>\<MaDK>.jp2` và `_BACKUP` theo khóa có thể đã sinh ra ở máy CSĐT — chưa biết, cần hỏi/kiểm ở máy đó. **Chưa quyết (ghi nhận, chưa đưa vào PRD):** đổi nền cả khóa ở DB đích · tiến trình bền (sqlite) · xem trước/sau + chip "Vừa đổi nền" · khôi phục từ sao lưu.

## #66 — Hạn giấy tờ xe + GPLX giáo viên + GV/xe ngưng còn phân công · 12/10/2026

- **Mã:** `PCG-06` (mã mới của nhóm PCG, số tiếp theo chưa dùng; **số story 57→58**).
- **Vì sao:** cảnh báo hạn giấy tờ hiện chỉ xuất hiện khi mở từng khóa (luật ⛔ "hết hạn trước bế giảng" của PCG-04) nên không ai thấy xe/giáo viên sắp hết hạn của cả cơ sở. Đọc DB đích 12/10/2026: 5 xe còn ≤ 30 ngày (đều đang ở 1–2 khóa), 3 giáo viên đã hết hạn GPLX (`GiaoVien.NgayHHGPLX`) + 1 còn ≤ 30 ngày. User chốt: ngưỡng 30 ngày, đặt trong Phân công, gộp nhóm GV/xe ngưng còn phân công, thêm hạn GPLX giáo viên.
- **Đã sửa:** PRD v4.9 (+`PCG-06` + Changelog) · TDD v6.11 (§11E.10 + endpoint trong §11E.2 + Changelog) · `ui-demo/SCREENS.md` #34 (⬜).
- **Còn nợ:** mock/prototype tab "Hạn giấy tờ" (`/prototype-next`) · `/kehoach` bổ sung 1 task · code (`phan_loai_han` + endpoint + tab) · nhóm "ngưng còn phân công" hiện **chưa có dòng nào** trong dữ liệu thật — giữ làm lưới canh.

## #65 — Kiểm trước kết xuất theo từng khóa · 12/10/2026

- **Mã:** `KQD-07` (mã mới của nhóm KQD; **số story 56→57**, cộng #66 thành 58).
- **Vì sao:** nhân viên chỉ biết HV thiếu điểm/giờ/kết luận sau khi đã kết xuất hoặc gửi Sở rồi phải "Mở khóa" (KQD-05) sửa lại. Cho kiểm trước một lượt theo khóa. User chốt: theo từng khóa; "chưa đủ" tính theo môn bắt buộc của hạng (dùng luật KQD-02, không tạo luật thứ hai); chỉ cảnh báo.
- **Đã sửa:** PRD v4.9 (+`KQD-07`) · TDD v6.11 (§11D.9 + endpoint trong §11D.6) · `ui-demo/SCREENS.md` #33 (⬜).
- **Còn nợ:** luật "môn bắt buộc theo hạng" hiện nằm ở UI (`CapNhatKQDT.tsx`) — khi code phải chuyển lên một nguồn chung ở backend để KQD-02 và KQD-07 dùng chung · mock · `/kehoach` bổ sung 1 task · code.

## #64 — Ghi lại hành vi thực tế khi dựng UI TNB (task 106-115) · 11/10/2026

- **Mã:** `TNB-02` · `TNB-03` · `TNB-04` · `TNB-05` · `TNB-06` · `TNB-07` (không thêm/bớt mã, số story giữ 56; trạng thái story **giữ nguyên** vì code đã chạy đúng điều được ghi).
- **Vì sao:** khi dựng UI và chạy kiểm thử E2E phát sinh nhiều chi tiết người dùng thấy được (tích lẫn, ngày BC1, Làm tiếp chốt payload, lỗi lô, hạn chế F5…) mà PRD/TDD chưa ghi; hai thay đổi backend nhỏ (ngày BC1 ở `goi-y-so`/`ung-vien`; `cuu_chuyen` hoàn tất lô dở).
- **Đã sửa:** PRD v4.8 (khối "Ghi nhận khi dựng UI" ở TNB-02..07 + chữ "chọn loại hạng") · TDD v6.10 (§11F.3–§11F.6) · decisions §23 · `ui-demo/SCREENS.md` #26–#32 (đã dựng thật) · cột Code #60–#62.
- **Còn nợ:** task **116–117** (dán danh sách CMT + xử lý ngoại lệ tại chỗ) · 3 điểm chưa quyết (nhóm "đã ở BC2 này", khôi phục lô sau F5, tích sẵn sau Làm tươi) · `/reviewtdd` §11F ở phiên mới · nghiệm thu ghi thật ở máy CSĐT (Checkpoint 27).

## #63 — Ghi lại hành vi thực tế của backend TNB vào TDD/PRD · 11/10/2026

- **Mã:** `TNB-01` · `TNB-05` · `TNB-06` (sửa chữ; không thêm/bỏ mã, số story giữ 56; các story đang 🔄 giữ nguyên).
- **Vì sao:** backend task 96–105 đã code xong và có nhiều điều chốt khi code (luật A/B/C, bộ sổ chung, gỡ tay `Old='11'` bị chặn, hoàn tác cứu bằng nhật ký tool, `{ma:path}`, chạy nền theo `lo_id`…). Tài liệu còn lag; UI task 106+ cần bám hợp đồng API thật.
- **Đã sửa:** TDD v6.9 §11F.0–11F.8 · decisions §23 (+đoạn cập nhật) · PRD v4.7 (TNB-01, TNB-05, TNB-06).
- **Còn nợ:** `/reviewtdd` §11F ở phiên mới (TDD đổi API + luật) · mockup `ui-mock/tnbc2.html` kiểm lại khi làm UI (ô "điền chung", cứu trạng thái, nhật ký, huy hiệu "lệch" nhẹ) · chụp trước/sau PM cũ + nghiệm thu máy CSDT · UI task 106–115.

## #62 — Đồng bộ PRD/mockup TNB với TDD §11F v6.8 · 11/10/2026

- **Mã:** `TNB-03` · `TNB-04` · `TNB-05` (sửa; không thêm/bỏ mã, số story giữ 56). Các story đang ⏳ Todo nên không phải hạ trạng thái.
- **Vì sao:** `/reviewtdd` §11F (biên bản `tdd-review-11-10-2026-tnb.md`, 25 phát hiện) cho thấy: `usp_NguoiLX_HoSo_ThemHS_BC2` không bao giờ trả HV đang `11`, và chuyển HV giữa hai BC2 bằng `usp_NguoiLX_Update_ThemHSBC2` đặt `TT_XuLy_Old='11'` — gỡ ra thì HV kẹt `11` không có BC2, không hiện ở danh sách thêm và cứu trạng thái cũng chặn nguồn `11`. User chọn **bỏ "chuyển"** (phương án A). BC1 suy từ khóa vì DB có 454 khóa có BC1 và 0 khóa có hơn một.
- **Đã sửa:** PRD v4.6 TNB-03 (bỏ "chọn BC1") · TNB-04 (nhóm Cần xem/Không đưa được, điều kiện `09` có số giấy, Thi lại cả cùng khóa, bỏ "bị chuyển", Edge cases) · TNB-05 (dòng "từng ở BC2 cũ") · mockup `ui-mock/tnbc2.html` (bỏ nhóm/huy hiệu/ô đếm "chuyển", HV ở BC2 mở khác → Không đưa được, khóa chưa có BC1 mờ + nút khóa, ô tô `14/17/18` cùng khóa → Thi lại, huy hiệu "từ BC2 cũ") · SCREENS #29. TDD §11F v6.8 và decisions §23 đã sửa ở lượt `/reviewtdd` (không đụng lại).
- **Còn nợ:** `/kehoach` bổ sung (Phase 10, task cho `TNB-01..07`) · code · chụp trước/sau PM cũ · user duyệt lại mockup.

## #61 — Thiết kế lại luồng thêm HV vào BC2 (TNB-03/04/05/06) · 11/10/2026

- **Mã:** `TNB-03` · `TNB-04` · `TNB-05` · `TNB-06` (sửa; không thêm/bỏ mã, số story giữ 56). Các story đang ⏳ Todo nên không phải hạ trạng thái.
- **Vì sao:** user xem mockup v1: "giao diện thêm HV vào BC2 chưa trực quan, khó nhìn; UI lộ story, lộ tên TT_XuLy (hiện cũng được nhưng phải nói rõ nghĩa); ưu tiên tự động hóa hoặc batch chọn". Nhân viên chỉ cần quyết "khóa nào, đưa ai"; còn lại tool tự suy.
- **Đã sửa:** PRD v4.5 (ghi chú ngôn ngữ đầu chương + TNB-03/04/05/06) · TDD v6.7 §11F.0/.4/.6 · decisions §23 · mockup `ui-mock/tnbc2.html` v2 · SCREENS #29/#30.
- **Quyết định user:** HV thi lại **không tích sẵn**, có nút "Thêm HV thi lại 12 tháng".
- **Còn nợ:** `/reviewtdd` §11F (phiên mới) · `/kehoach` bổ sung · code · chụp trước/sau PM cũ.

## #60 — Feature "Tốt nghiệp & Báo cáo 2" (TNB-01..07) · 11/10/2026

- **Mã mới:** `TNB-01` Cập nhật tốt nghiệp ô tô theo lô · `TNB-02` Sửa/hủy tốt nghiệp · `TNB-03` Tạo BC2 · `TNB-04` Thêm HV vào BC2 · `TNB-05` Bỏ HV khỏi BC2 · `TNB-06` Chuyển `TT_XuLy` cứu HV · `TNB-07` Danh sách BC2 + nhật ký. Số story 49 → **56**.
- **Vì sao:** cơ sở đang làm tốt nghiệp ô tô và lập BC2 bằng PM cũ; muốn làm trong tool để nhanh hơn nhưng dữ liệu DB Nạp phải **y chang** như PM cũ ghi. Nên chỉ gọi SP có sẵn, không tự INSERT/UPDATE. Mô tô không có bước tốt nghiệp nên tách riêng với ô tô.
- **Đã ghi:** PRD chương 🟣 mới (v4.4) · TDD §11F (v6.6) · decisions §23.
- **Không làm (để PM cũ):** kết xuất BC2, cập nhật kết quả BC2, đổi trạng thái sau gửi, **đóng BC2** (`TrangThai=1`); gửi BC2; lập BC1.
- **Còn nợ:** mockup `ui-mock/tnbc2.html` (user duyệt) · SCREENS #26–#32 · `/reviewtdd` §11F · `/kehoach` bổ sung · code · **chụp trước/sau PM cũ** xác nhận SP/cột; quy tắc số giấy CNTN kế tiếp.

## #59 — /reviewtdd §11E: dấu vân tay hiện trạng, khóa ghi, giới hạn đầu vào · 11/10/2026

- **Mã:** `PCG-02` · `PCG-03` · `PCG-04` (không thêm/bớt mã; số story giữ 49; trạng thái giữ ✅ — code + test cùng lượt).
- **Vì sao:** review độc lập TDD §11E (14 phát hiện, 0 Chặn): CDB không có UNIQUE và phần mềm CDB cũ cùng ghi — bản nháp mở lâu sẽ xóa lặng lẽ dòng người khác thêm giữa chừng (3.1); ghi chồng nhân đôi dòng (3.2); địa điểm quá 255 ký tự hoặc mã môn lạ làm `/ghi` lỗi giữa chừng (4.1).
- **Đã sửa:** TDD §11E.0–11E.9 (+3 sơ đồ ASCII, v6.5) · `phancong_service.py` (`dau_van_tay`, `_khoa_ghi`) · `routers/phancong.py` (ràng buộc đầu vào) · `phancong_rules.py` (`mon_khong_ton_tai`) · UI `GhiBanNhap.tsx`/`PhanCongTheoKhoa.tsx`/`api.ts` gửi và làm tươi `dau_van_tay` · test `test_phancong_kiemthu.py` (+6) · biên bản `tdd-review-11-10-2026-pcg.md`.
- **Còn nợ:** `pnpm build` webui rồi restart backend 8010 để dist/UI mới chạy; vitest/E2E cho logic trong TSX; nghiệm thu máy CSDT (Checkpoint 22).

## #58 — Chốt 9 điểm mơ hồ PCG sau /kiemthu · 11/10/2026

- **Mã:** `PCG-01..05` (không thêm/bớt mã; số story giữ 49). Trạng thái story giữ ✅ — code đã sửa cùng lượt và có test.
- **Vì sao:** `/kiemthu` Feature PCG (agent `sinh-testcase`) nêu 10 chỗ PRD/TDD không đủ rõ để viết assertion; user chốt từng câu, chọn phương án đề xuất.
- **Đã sửa:** PRD PCG-01 (nút hợp hạng), PCG-03 (địa điểm, đợt cách quãng), PCG-04 (cảnh báo LT, theo cả GV, không đổi → không hỏi), PCG-05 (xe chưa ghép là thông tin) · TDD §11E.7 · code `phancong_rules.py`, `phancong_service.py`, `phancong_rasoat.py`, `BuocGiaoVien.tsx` · test `test_phancong_kiemthu.py`, `test_phancong_rasoat.py`.
- **Còn nợ:** vitest/E2E cho logic nằm trong TSX (cần tách hàm + cài Playwright); ghi thật nghiệm thu máy CSDT (Checkpoint 22).

## #52 — Loạt UX form nhập HV desktop (THU-01/THU-02) · 08/10/2026

- **Mã:** `THU-01` · `THU-02` (dùng chung màn xác nhận/sửa) — **không thêm mã, số story giữ 44.**
- **Vì sao:** User rà form nhập trên desktop, muốn gõ nhanh + đỡ nhầm + biết ô nào đã xong. Mười điểm đã chốt qua trao đổi:
  1. Nới khung desktop 2xl→3xl (form trước hẹp hơn vùng nội dung ~220px).
  2. Sắp lại ô theo cụm thẻ: **Số CCCD + Ngày cấp cùng hàng**; Họ tên + Nơi thường trú trọn bề ngang.
  3. Số CCCD: chặn gõ/dán quá 12 số + bộ đếm `n/12` (xanh khi đủ) + ✓.
  4. Họ và tên tự in hoa khi gõ (giữ dấu) — khớp cột `HoVaTenIn`.
  5. Giới tính: nút gạt Nam/Nữ thay `<select>` (1 bấm, không rê chuột).
  6. Nơi thường trú: **gợi ý Tỉnh/Xã, nhập tự do, không ép chọn** (phương án A); khớp không dấu + gõ một phần; hợp cả địa chỉ cũ 3 cấp lẫn mới 2 cấp.
  7. Phím mũi tên nhảy giữa các ô (Lên/Xuống; Trái/Phải khi con trỏ ở đầu/cuối chữ; Giới tính Trái/Phải đổi Nam/Nữ; đang mở gợi ý thì mũi tên chọn trong danh sách).
  8. Icon nhỏ ở nhãn từng ô cho sinh động.
  9. Trạng thái ✓ xanh / đỏ từng ô (đang gõ không báo đỏ) + dòng "Còn thiếu…/Đã đủ, sẵn sàng lưu".
  10. Tự suy Giới tính + Năm sinh từ số CCCD (chữ số thứ 4 + 2 số kế) — gợi ý mặc định, sửa đè được.
- **Nguồn dữ liệu địa chỉ:** file tĩnh `webapp/src/data/dvhc-2025.json` (34 tỉnh + 3.321 xã/phường, 2 cấp 2025, nguồn `thanglequoc/vietnamese-provinces-database` lấy từ GSO), **nạp lười** (chunk riêng ~59KB/gzip 16KB). Dùng A — nguồn công khai, user duyệt; **khác** SQLite `DM_DVHC` của tool (NAP-03, dùng để sinh mã nạp).
- **Đã sửa:** PRD `THU-01` (+Done-khi #52 + dòng trạng thái) · TDD §6.8 mới (v6.2) · code `Quet.tsx`, `ODate.tsx`, `Icon.tsx`, `lib/qr.ts` (+`suyTuCccd`), mới `lib/dvhc.ts` + `data/dvhc-2025.json`.
- **Verify:** `tsc -b` sạch · 34 vitest pass · `vite build` OK · commit `5087ceb` đã push `main` (CD auto-deploy).
- **Còn nợ:** chụp Playwright 3vp (375/800/1440) cho form desktop mới — màn sau đăng nhập, cần backend; THU-01 giữ ⚠️ Partial tới khi chụp.

---

## #51 — "Bỏ khỏi hàng đợi" cho dòng chờ/lỗi + nhớ "bỏ qua" (NAP-01) · 08/10/2026

- **Mã:** `NAP-01` (mở rộng tiêu chí, prefix cũ, không nghỉ hưu mã, không story mới).
- **Vì sao:** Operator gặp hồ sơ **đã xóa bên app web** nhưng tool đã kéo về từ trước nên còn nằm ở tab "Cần xử lý" (chờ nạp), không có cách dọn. Cơ chế đồng bộ-xóa khi kéo (§11.7) chỉ bắt hồ sơ VPS báo `deleted` **sau mốc thời gian** gần nhất → hồ sơ xóa trước mốc bị lọt. Cần lối dọn tay, chủ động, cho cả hồ sơ operator đơn giản "không muốn nạp".
- **Nội dung chốt (user 08/10/2026):**
  - "Bỏ khỏi hàng đợi" áp cho **mọi dòng**, không chỉ 🟢 Đã nạp. Dòng ⚪ chờ / 🔴 lỗi: tool **ghi nhớ "bỏ qua"** (tombstone `keo_ve_bo_qua`) → "Kéo về từ VPS" lần sau **không mang về lại**.
  - **Bỏ nhiều dòng một lượt**, kèm **xác nhận 2 bước**.
  - Chỉ đụng `staging.sqlite` của tool — **KHÔNG đụng DB Nạp (prod), KHÔNG đụng máy chủ VPS**.
  - Hồ sơ bị bỏ qua được collector **gửi lại** (uuid mới) → hiện lại bình thường.
- **Đã sửa:** PRD [NAP-01] (AC "Bỏ khỏi hàng đợi" + "Bỏ nhiều một lượt" + 2 edge case) · TDD §7.2 (mở rộng) + §9.3b mới (bảng tombstone `keo_ve_bo_qua`) + §4 endpoint `POST /local/nap/bo-qua` + vòng đời nháp §9.3a · TDD-decisions §11 (điểm xóa nháp thứ 4).
- **Chưa làm (code):** backend tombstone + nới guard + endpoint bỏ-nhiều · UI chọn nhiều + nút bỏ cho dòng chờ/lỗi + panel xác nhận. Chờ `/reviewtdd` (API + Data Model mới) rồi `/kehoach` bổ sung task.
- **Đã chốt (08/10/2026, sau /reviewtdd):** **KHÔNG làm** nút "Khôi phục dòng đã bỏ qua" (user chốt A). Lỡ bỏ nhầm → collector gửi lại trên app web (uuid mới) là hiện lại; tombstone vẫn khôi phục được ở mức dữ liệu nếu hãn hữu cần.
- **Chốt sau /reviewtdd (08/10/2026, TDD v6.1, biên bản `tdd-review-08-10-2026.md`):** gộp 1 đường — **gỡ endpoint `DELETE /local/keo-ve/:uuid`**, mọi "Bỏ khỏi hàng đợi" (1 hay nhiều dòng, mọi trạng thái) qua `POST /local/nap/bo-qua` (tránh đường xóa-không-tombstone); tombstone chỉ ghi cho `cho`/`loi`/`None`, KHÔNG cho `xong` (giữ đường QLY-08 kéo lại). Thêm việc code: **chuyển UI DELETE→POST** + gỡ endpoint DELETE cũ.

---

## #50 — OCR chỉ đọc 5 trường mặt trước, bỏ ngày cấp (THU-06) · 07/10/2026

- **Mã:** `THU-06` (sửa, không nghỉ hưu mã). **Số story giữ 44.**
- **Vì sao:** phát hiện khi build task 79 — **ngày cấp CCCD in ở MẶT SAU thẻ**, không có ở mặt trước. THU-06 chỉ chụp mặt trước (PRD ❌ không đọc mặt sau) → OCR không thể đọc ngày cấp. #49 (và Done-khi THU-06) vốn liệt kê ngày cấp trong 6 trường OCR → tiêu chí không bao giờ đạt. User chốt **phương án A** (07/10): OCR 5 trường mặt trước, ngày cấp nhân viên nhập tay.
- **Đã sửa:** PRD `[THU-06]` Steps bước 3 + Done-khi (6→5 trường + 1 dòng "ngày cấp nhập tay") · TDD §6.7 dòng "Trường OCR đọc" (v5.9) · BUILD-PLAN task 79 + Checkpoint 17 (v19).
- **Code:** task 79 (`webapp/src/lib/ocr.ts`) đã viết đúng — đọc 5 trường, ngày cấp luôn rỗng + đánh dấu. Không cần sửa code.
- **Còn nợ:** task 80 (UI) phải cho ô ngày cấp **nhập tay** (không chờ OCR); màn #23 chưa dựng.

## #49 — OCR đọc chữ trên thẻ CCCD làm lối nhập dự phòng (THU-06) · 07/10/2026

- **Mã:** `THU-06` — story mới, prefix THU có sẵn (số kế tiếp chưa dùng). **Số story 43→44.**
- **Vì sao:** user báo iPhone quét QR CCCD **không được**, test lại đúng — **iPhone/iOS Safari quét QR yếu hơn Android hẳn**. Gốc: iOS không có `BarcodeDetector`, engine QR trên web (ZXing/zbar) đọc không nổi QR nhỏ/mờ/lóa trên thẻ. **Verify (BUG-14):** giải mã thử ảnh thẻ thật bằng **zxing-cpp + pyzbar + OpenCV QRCodeDetector** + xoay + downscale + cắt sát + tăng tương phản + nhị phân Otsu + phóng 3× → **không engine nào đọc được**. Nhưng chữ IN trên thẻ **to/rõ**, đọc bằng mắt/OCR tốt → OCR là lối thoát chắc hơn QR trong đúng ca này.
- **Chốt (user 07/10):** thêm lối nhập thứ 3 "Chụp ảnh thẻ → tự đọc chữ (OCR)", **mọi thiết bị** (không khóa theo máy — Android gặp thẻ hỏng cũng dùng được). OCR điền sẵn 6 trường → **nhân viên xác nhận/sửa** trước khi lưu. Qua **màn xác nhận + luồng gửi dùng chung** (không thêm luồng gửi mới).
- **Lật quyết định:** THU-01 từng ghi *"❌ Không OCR chữ trên thẻ"* → nay OCR tách sang THU-06; THU-01 **giữ ⚠️ Partial** (hành vi quét QR của nó không đổi). Chi tiết: `TDD-decisions` §20 (giữ "Đã từng chốt").
- **Chưa chốt (để `/tdd`):** engine OCR (Tesseract.js client / dịch vụ eKYC) · nơi chạy (client thuần vs gửi server) · cách tách trường. **Chi phối bởi PII** — gửi ảnh CCCD ra dịch vụ ngoài là lộ dữ liệu căn cước, ưu tiên cân client-side trước.
- **Đã sửa tài liệu:** PRD (+[THU-06] ⏳ Todo + sửa dòng ❌ THU-01, Changelog v4.0) · TDD (§6.7 khung nghiệp vụ + Changelog v5.5) · TDD-decisions (§20) · SCREENS (+màn #23 ⬜, lượt 22).
- **Chưa code** (⬜) — chờ `/reviewtdd` §6.7 + `/tdd` chốt engine, rồi `/kehoach` bổ sung + `/prototype-next` dựng lối vào.
- **Quan hệ BUG-14:** OCR (THU-06) là lối thoát chắc ăn cho iPhone; **song song** vẫn cải thiện quét QR iPhone (engine web mạnh hơn + UX chụp gần/nét) ở BUG-14 — hai việc bổ trợ.

---

## #48 — Sửa lẻ / xóa điểm đã lưu (KQD-06) · 07/10/2026

- **Mã:** `KQD-06` (mới, chương 🟣 Cập nhật kết quả đào tạo). Số story 42→43.
- **Vì sao:** Dùng thử KQD-02 lộ 2 thiếu sót: (a) muốn sửa 1 môn sai phải gõ lại đủ 5 (nút Lưu chặn khi thiếu); (b) chưa có cách xóa điểm nhập sai để nhập lại. Đều chỉ áp HV đã cập nhật **chưa kết xuất** (09/10).
- **Đã thêm:** PRD `[KQD-06]` (⏳ Todo) · TDD §11D.8 (sửa lẻ gom 5 quy-đổi giữ môn cũ + `POST /xoa-diem` UPDATE trực tiếp reset về 03) + §11D.6 +endpoint.
- **Dữ kiện verify DB 07/10:** không có SP reset KQĐT (list `sys.procedures`); `DiemKQ*` float + 3 cờ bit + `SoGiayCNTN` **nullable**; `TT_XuLy` NOT NULL (set '03' được). Điểm lưu là **quy đổi /10** (không lưu gốc) → giữ môn cũ phải truyền lại quy đổi, không tính ngược.
- **Còn nợ:** chưa code (dựng thẳng tool/webui); cần `/reviewtdd` (API+nghiệp vụ mới) + `/kehoach` bổ sung 1 task + nghiệm thu máy CSDT (ghi/xóa thật).

## #47 — 4 cải tiến UX lưới Cập nhật KQĐT · 07/10/2026

- **Mã:** `KQD-01` · `KQD-02` (không thêm mã mới). Thuần giao diện, **không đổi nghiệp vụ/data/API**.
- **Vì sao:** nhập điểm hàng loạt trên lưới — người dùng cần thấy tiêu đề cột khi cuộn, nhiều HV trên màn hơn, di chuyển ô bằng phím, và dòng gọn.
- **Đã sửa (`tool/webui/src/pages/ketqua/CapNhatKQDT.tsx`, code ✅ + verify live):**
  - ① **Ghim tiêu đề lưới** — `thead sticky top-0`; restructure vùng cuộn (wrapper bảng thành scroll container `flex-1 min-h-0 overflow-auto`). Verify cuộn 300px thead vẫn dính mép trên.
  - ② **Thu gọn khung chọn khóa** — state `gonKhoa` + nút Thu gọn/Mở rộng; bản gọn 1 dòng (tên khóa + Đổi khóa).
  - ③ **Phím mũi tên** — `navGrid()` + `data-kqd-r/c` trên 7 ô nhập/dòng (5 môn + giờ + km đường); ↑↓ đổi hàng, ←→ đổi cột khi con trỏ ở đầu/cuối ô.
  - ④ **Lưu + Chi tiết ngang hàng** (Lưu trước) — đổi container nút `flex-col`→`flex` row; cột "Lưu" nới w-[150px].
- **Vì sao ghi ✏️ mà KHÔNG hạ trạng thái KQD-01/02:** ngược chiều /capnhat thường (ở đây code TRƯỚC, ghi sổ SAU — việc đã xong+verify, không phải việc tồn cần re-code). KQD-01 giữ ✅, KQD-02 giữ ⚠️ (lý do ⚠️ là máy CSDT, không liên quan 4 tweak này).

## #46 — Đồng bộ tài liệu TDD sau code KQD-05/03 · 07/10/2026

- **Mã:** `KQD-05`, `KQD-03` — tài liệu lag code, **KHÔNG đổi yêu cầu** (hành vi đã mô tả ở PRD #45).
- **Vì sao:** Khi code task 76/77 chốt 2 chi tiết kỹ thuật lệch với TDD §11D đã viết lúc /capnhat #45: (a) UI cần một endpoint ĐỌC để biết cổng B-1 + liệt kê gói, mà §11D.6 mới chỉ có `POST /mo-khoa`; (b) thứ tự thao tác an toàn hơn khi làm ngược số bước §11D.7 đã ghi.
- **Đã sửa (chỉ TDD):**
  - §11D.6 — thêm **`GET /local/ketqua/mo-khoa`** (cổng B-1 chỉ đọc: `mo_duoc` + `goi_chua_gui`/`goi_da_gui` + `so_hv_mo`/`so_hv_bo_qua`/`so_khoa`). Ghi rõ **KQD-03 KHÔNG có endpoint `ket-xuat` riêng** (bỏ đề xuất cũ): tiến độ ghép từ `/khoa` (thêm đếm `ketxuat`=12), panel gói từ `GET /mo-khoa` (CSĐT-wide, tải 1 lần), lưới HV từ `/hoc-vien?trang_thai=ketxuat|capnhat`.
  - §11D.7 — **đảo thứ tự: LÙI HV (bước 2) TRƯỚC, XÓA gói (bước 3) SAU**. Lý do: xóa gói lỗi giữa chừng thì HV đã về 09/10 (sửa được) + cổng còn mở để chạy lại → khớp edge PRD KQD-05, tránh kẹt "12 không gói". `GiaiTrinh` ghi gộp vào `UPDATE` lùi.
  - Changelog TDD v5.3.
- **Không đụng:** PRD (hành vi đã có ở KQD-05), màn (UI đã dựng task 74/77), BUILD-PLAN, số story giữ **42**, không thêm/nghỉ hưu mã.
- **Còn nợ:** code KQD-05/03 (task 76/74/77) đã viết + build + 336 pytest, nhưng **chờ restart backend dev** (đang chạy code cũ) + **nghiệm thu máy CSDT** (happy-path mở khóa ghi thật). Chưa commit.

## #45 — Mở khóa để sửa điểm sau kết xuất + dựng lại tab Theo dõi kết xuất · 07/10/2026

- **Mã:** `KQD-05` (mới — mở khóa sửa sau kết xuất), `KQD-03` (viết lại khóa-first). Số story 41→42.
- **Vì sao:** khi lỡ nhập sai điểm cho HV đã kết xuất nhưng **đợt chưa gửi đi Sở**, cần sửa ngay thay vì chờ Sở từ chối. Tab Theo dõi kết xuất cũ (2 panel phẳng Đã/Chưa) khó tìm, không cho biết gói nào đã gửi.
- **Chốt (qua nhiều lượt + probe DB live `GPLX_CDB_CSDT` 07/10):**
  - **Cổng B-1:** chỉ mở khi còn gói `KET_QUA_DAO_TAO` `NoiGui=<CSĐT>` `TrangThai='0'`. Gói đã gửi hết → khóa cứng.
  - **Hành vi B-1a (mức lô):** xóa gói chưa gửi (`usp_TRANS_CLI_HangDoiGui_Delete`) + lùi **mọi HV 12 của khóa** về 09/10 → sửa → kết xuất lại cả khóa ở PM cũ. Không mổ xẻ 1 HV.
  - **M1:** gói đã gửi hết → thông báo mức đợt, **không đoán gói cụ thể**.
  - Nút "Mở khóa" ở **cả 2 tab** (phương án A); KQD-02/04 giữ ⚠️ Partial (2A — yêu cầu lõi không đổi, chỉ thêm cửa thoát).
- **Ràng buộc DB (verify live):** không nối được HV↔gói — tên gói chỉ timestamp (`KQDT_<CSDT>_<MaSoGTVT>_K<ts>.zip`), không junction, `Transfer_flag=0` cho mọi HV kể cả 12; danh sách HV nằm trong file nén. SP `_CapNhat` không bảo vệ 12 (ghi đè tự lùi 12→09/10); `usp_TRANS_CLI_HangDoiGui_Delete` = DELETE theo Id. Lọc `NoiGui` để tránh 61 gói `TrangThai=0` của CSĐT 24005 lẫn trên máy dev.
- **Đã sửa:** PRD (+`[KQD-05]`, viết lại `[KQD-03]`, +ghi chú ngoại lệ 12 ở KQD-02/04, Changelog v3.9) · TDD (§11D.7 mới + §11D.0 ngoại lệ + §11D.6 endpoint, Changelog v5.0) · TDD-decisions (+§19) · SCREENS (#21/#22 + trỏ mock) · CHANGES (#45 + Mốc đối chiếu).
- **Còn nợ:** `/kehoach` bổ sung (1 task KQD-05) · `/reviewtdd` (TDD vừa thêm §11D.7 + endpoint + decisions §19) · code màn thật (mock `ui-mock/theodoiketxuat.html` đã có). Code KQĐT nền (KQD-01/02/04 từ pmcs-tlx-06) chưa commit.

---

## #44 — App web cho chụp bù ảnh kể cả HV ĐÃ NẠP (Phương án B) · 07/10/2026

- **Mã:** `THU-02` (app web chụp bù), `QLY-05` (tool kéo ảnh về bổ sung). Không thêm mã mới.
- **Nguồn:** user 07/10 — khi test thấy HV nạp lúc chưa có ảnh thì **không có đường nào lấy ảnh collector chụp tại chỗ** vào DB: app web khóa ảnh sau nạp, tool chỉ nhận ảnh-từ-file.
- **Lật quyết định:** 01/10 đã chốt **Phương án A** (ảnh HV đã nạp chỉ xử lý ở tool, không mở app web chụp lại — TDD §11.5 cũ + chặn `pending` ở `POST .../anh`). Nay chuyển **Phương án B** (TDD-decisions §18).
- **Chốt (user 07/10):**
  - App web cho chụp/bổ sung ảnh cho HV **thiếu ảnh kể cả `imported`** — **chỉ ảnh**; sửa thông tin & xóa hồ sơ đã nạp vẫn khóa.
  - Server nới `POST /api/ho-so/:uuid/anh`: cho `pending`+`imported`, **vẫn chặn `importing`** (đang nạp), giữ `created_by` (chỉ ảnh của mình).
  - Tool kéo ảnh thô VPS về ở Tra cứu DB (QLY-05 nguồn b, đã specced #32) → chỉnh + đổi nền → nạp DB.
  - **Không cờ "ảnh mới"** (chốt A): operator tự lọc "Chưa ảnh" → mở HV → bấm kéo.
- **Vì sao đổi an toàn:** endpoint ảnh chỉ ghi `anh_tho_path`, không đổi `trang_thai`/thông tin → mở cho `imported` không phá vòng đời nạp.
- **Đã sửa tài liệu:** PRD (THU-02 +Done khi + hạ ✅→⏳ · QLY-05 nguồn b, v3.8) · TDD (§6.2/§6.3/§4.3/§11.5, v4.9) · TDD-decisions §18 (lật A→B, giữ "Đã từng chốt A") · CHANGES #44.
- **Đã code (07/10/2026, sau /reviewtdd #44):** server `ho_so.py` `upload_anh` → allowlist `{pending,imported}` (chặn `importing`/`deleted`), `jobs/pii.py` lọc theo `updated_at` (gia hạn ảnh chụp-bù) — 44 test server pass; app web `DaGui.tsx` tách `anhDuoc` (hiện nút chụp bù cho `imported` thiếu ảnh) — 24 test webapp + tsc pass; tool `keoAnhVps`/lọc "Chưa ảnh" dùng lại QLY-05 nguồn (b) có sẵn (#32), không viết mới. **Còn nợ:** E2E 3 hệ thống ở máy CSDT (app→VPS→tool kéo ảnh→nạp DB) để chốt ✅ — THU-02 đang ⚠️ Partial.

---

## #43 — Ngày cấp + Nơi cấp điền sẵn ở drawer "Chuẩn bị" (Nạp lô) · 07/10/2026

- **Mã:** `NAP-01` (mở rộng drawer Chuẩn bị, không thêm mã mới). NAP-01 đang 🔄 In Progress → giữ nguyên; `NAP-05` giữ ✅ (hành vi nạp ngày cấp vào DB không đổi, chỉ đổi nguồn giá trị từ gốc sang giá trị operator chỉnh).
- **Nguồn:** user 07/10, phát hiện khi tra code 2 bug người dùng báo (quét QR iPhone/Android + chặn chụp ảnh bổ sung — xử lý riêng). Hai điểm này gói vào drawer Nạp.
- **Vì sao:**
  - *Ngày cấp:* nhân viên cần xem/sửa ngày cấp CCCD ngay trước khi nạp; trước #43 ngày cấp chỉ hiện dạng chữ đọc inline ("· cấp dd/mm/yyyy"), không sửa được, lúc nạp luôn lấy giá trị gốc kéo về.
  - *Nơi cấp:* #40 (06/10) đã làm ô Nơi cấp điền sẵn "Cục QLHC" cho CCCD 12 số, **với tiền đề đã chạy script đồng bộ `DM_DVHC` đích→nguồn**. Trên máy CSDT chưa chạy script đó, danh mục nguồn không có mã '00' → ô bị bỏ trống, trông như "không tự chọn". Cần lớp phòng thủ client cho máy chưa đồng bộ.
- **Chốt (user 07/10):**
  - Ngày cấp: ô `<input type="date">` có nhãn riêng ở drawer, điền sẵn + **sửa được** (user chốt "điền sẵn + sửa được", không phải chỉ xem). Chuyển đổi `yyyymmdd ↔ yyyy-mm-dd`. Lưu nháp bền như nơi cấp.
  - Nơi cấp: tự chèn option `00 — Cục QLHC` khi `suyNoiCap`/nháp ra '00' mà combo nguồn chưa có — bền với máy chưa đồng bộ `DM_DVHC`. Không thay cho việc đồng bộ danh mục (vẫn nên chạy script #40 để các mã tỉnh khác đúng).
- **Phân biệt với #40:** #40 sửa **modal sửa nhân thân ở Tra cứu DB (QLY-01)**; #43 sửa **drawer "Chuẩn bị" lúc nạp lô (NAP-01)** — hai màn khác nhau, cùng ý "nơi/ngày cấp điền sẵn-sửa được".
- **Đã sửa tài liệu:** PRD (`NAP-01` +2 Done khi + ghi dòng lưu nháp +ngày cấp + ghi chú trạng thái, Changelog v3.7) · TDD (§9.3a +cột `ngay_cap`/`ngayCap` + 2 bullet ô Ngày cấp/Nơi cấp + sơ đồ vòng đời, Changelog v4.7) · CHANGES (#43 + Mốc).
- **Chưa code** (⬜) — chờ `/reviewtdd` §9.3a (chạm Data Model bảng nháp) → rồi code trong story NAP-01.

---

## #42 — Nhóm "Cập nhật kết quả đào tạo" (module mới, prefix KQD) · 07/10/2026

- **Mã:** `KQD-01`, `KQD-02`, `KQD-03`, `KQD-04` — **prefix mới KQD** (Kết Quả Đào tạo), user chốt 07/10.
- **Vì sao:** Nhân viên đang phải gõ kết quả từng HV trong phần mềm CDB cũ (modal 1 người/lần, bấm mũi tên 2/70). Tool mới nhập trực tiếp trên lưới, tự quy đổi điểm theo quy định, giảm sai sót. Dữ liệu thật: 711 HV đang chờ nhập (TT_XuLy=03) trải 13 khóa — cơ chế nhập điểm→Sở phê duyệt thực sự chưa chạy ở CDB này (chỉ 1 lô test 02/10).
- **Phạm vi chốt:** CHỈ cập nhật KQĐT (`TT_XuLy` 03→09 Đạt / →10 Không đạt) qua `usp_NguoiLX_KetQuaDaoTao_CSDT_CapNhat`. **KHÔNG** kết xuất XML/gửi Sở (để PM CDB cũ lo — giữ phần mã hóa truyền tin). Tool dừng ở 09/10.
- **Quyết định nghiệp vụ (chi tiết TDD §11D + decisions §17):**
  - Nhập **điểm GỐC** → app quy đổi /10 (2 đoạn tuyến tính, ngưỡng 5,0), ghi **5 điểm per-môn** (`DiemKQLyThuyet/MoPhong/Hinh/TienLui/ThucHanh`), **KHÔNG ghi trung bình**.
  - Tham số LT theo hạng + **cờ CŨ (TT12/2025) / MỚI (TT108/2026) tích chọn theo TỪNG KHÓA**, lưu phía tool (không đụng schema CDB), không nhảy theo ngày.
  - Giờ/km thực hành **TT17/2026/TT-BXD**: giờ sân khóa cứng (B&B.01:34·C1:35) · km sân điền sẵn (B&B.01:240·C1:225) · giờ+km đường để trống + gợi ý tối thiểu (giờ ≥½: 12/20/24 · km ≥: 710/810/825).
  - **Đạt = từng môn ≥5** (user chốt A, bỏ điểm liệt/loại trực tiếp); 3 cờ `KetLuanCSDT/KQLyThuyet/KQThucHanh` **app tự tính** rồi truyền SP (verify 06/10: DB 0 trigger, cột bit rỗng không computed/constraint — HV đạt thật có cờ=1 nhưng 3 môn NULL → PM cũ set tùy ý, data cũ không bắt chước).
  - Số giấy HTKH `SoGiayCNTN`=`MaDK+'-'+hạng` tự sinh khi Đạt; `TongQDThucHanh`=km đường (nhập), không phải tổng.
- **Đã thêm vào:** PRD chương mới ③🟣 "Cập nhật kết quả đào tạo" (KQD-01..04) · TDD §11D (6 mục: kiến trúc/SP, máy trạng thái, quy đổi, giờ/km, Đạt+cờ, API) · TDD-decisions §17 · SCREENS màn #21 (Cập nhật) + #22 (Theo dõi kết xuất).
- **Còn nợ:** toàn bộ code (module `routers/ketqua.py` chưa có) · 2 màn `tool/webui` chưa dựng · cần `/reviewtdd` (chạm thiết kế/data nhiều) → `/kehoach` bổ sung → `/prototype-next` (hoặc dựng thẳng tool/webui như SYNC/TCB) → `/subagent` bổ sung (mảng mới "kết quả đào tạo" nếu dự án có bộ agent).
- **Tham khảo:** `thamkhao/2026_352_27_VBHN-BXD.docx` (TT17 giờ/km) + `thamkhao/So_theo_doi_ket_qua_hoc_tap_DTLX_TT17.xlsx` (quy đổi điểm); schema `docs/DB-GPLX_CDB_CSDT.md` §5.

---

## #41 — Lịch sử sync hiện tên khóa + nút Hủy ở Bàn đồng bộ · 06/10/2026

- **Nguồn:** user 06/10 (nhìn Lịch sử thấy chỉ có mã + thứ tự cột ngược; muốn hủy sync ngay ở Bàn đồng bộ).
- **Chốt (user 06/10 — phương án A):**
  - **Lịch sử & Hủy sync**: cột **Khóa nguồn (CSDT) trước, Khóa đích (CDB) sau**; mỗi ô khóa 2 dòng: tên (đậm) + mã. Lưu **tên lúc sync** (`SyncBatch.ten_khoa_moi/ten_khoa_cu`; FE gửi qua `RunIn.ten_kh_nguon/dich`); bản ghi CŨ rỗng → `/lich-su` tra DB bù 1 lượt (đích ở CDB theo `target_key`, nguồn ở CSDT), bọc try/except nên mất DB vẫn hiện mã.
  - **Bàn đồng bộ**: khi chọn khóa đích đã có HV do tool tạo (`/rollback/preview tong>0`) → hiện nút đỏ **"Hủy sync khóa đích (N)"** → hộp thoại xác nhận → `/rollback` (xóa HV do tool tạo khỏi CDB, về ban đầu). Tách hộp thoại rollback thành `components/HuyncSyncDialog.tsx` dùng chung Lịch sử + Bàn đồng bộ.
  - **Đổi nhãn** cột đếm ở Bàn đồng bộ: **"Số HS" → "SL hồ sơ"** (dữ liệu là `COUNT(*)` số HS/người ở đích, luôn=1 do 1 người=1 hồ sơ; ≠1 là cảnh báo bất thường). Khác cột "Số HS" ở Tra cứu DB/CDB (đó là giá trị `SoHoSo` thật). Đối chiếu **sync_tool v2.0** (`sync_gplx.py` COL_LABELS[9]="So HS", `db_helpers.py` COUNT(*)): port trung thực, không phải lỗi — chỉ đổi nhãn cho khỏi nhầm.
- **Phạm vi:** thuần UI tool + 2 field nhật ký JSON; endpoint `/rollback` cũ không đổi; không chạm quyết định TDD §12/13/14.
- **Đã sửa:** CHANGES (#41 + Mốc). PRD/TDD không đổi nghiệp vụ (chỉ trình bày + nhật ký) — không sinh story/quyết định mới; SYNC-01/03 giữ ✅.
- **Code: ✅** commit `844a031` + nhãn SL hồ sơ; 304 backend + 34 vitest + tsc. **Chưa push.**

---

## #40 — Nơi cấp căn cước = Cục QLHC (DM_DVHC) + mở rộng modal sửa Nạp · 06/10/2026

- **Đảo 2 quyết định cũ:** #31/BUG-10 (nơi cấp = `DM_DonViGTVT` Sở GTVT, suy MÃ TỈNH từ CCCD) và #37 ("Nạp QLY-01 giữ 5 trường").
- **Vì sao:** app CSDT cũ hiển thị "Nơi cấp" căn cước = **Cục QLHC**. Kiểm DB đích `GPLX_CDB_CSDT`: "Cục QLHC" là **mã `'00'` trong `DM_DVHC`** (LoaiDvhc 'C', cùng danh mục/cùng cột `NoiCapCMT` với mã tỉnh), KHÔNG có trong `DM_DonViGTVT` (ở đó '00'=Cục CSGT/Tổng cục đường bộ — lệch nghĩa). Căn cước 12 số do Cục Cảnh sát QLHC cấp tập trung → nơi cấp đúng = '00', không phải tỉnh quê quán.
- **Chốt (user 06/10, qua trao đổi + kiểm DB thật):**
  - Nơi cấp đọc/hiển thị từ **`DM_DVHC.MaDvhc`** (tỉnh TW/TI active + nhóm Cục 'C' luôn hiện gồm '00'); mã lưu = `MaDvhc`. 4 điểm: `dvhc.ds_so_gtvt` + hiển thị `hoso.py`/`sync_tracuu.py` (list+chi tiết) → scalar subquery `DM_DVHC.TenNganGon`.
  - **Mặc định CCCD 12 số = '00' Cục QLHC** (`suy_noi_cap`/`suyNoiCap`); CMND 9 số để trống chọn tay. Bỏ mắt xích `r.noi_cap_cccd` (TEXT) trong payload nạp.
  - **Mở rộng modal sửa QLY-01 Nạp** = port combo đã có ở TCB-03 (#37): Tỉnh/Xã 2 cấp + nơi cấp + ngày cấp CCCD; bỏ-trống-giữ-cũ; `chi-tiet` trả thêm 4 mã preselect. **Chốt chặn BC1 (409) giữ nguyên.** Nhãn Sync bỏ "(Sở GTVT)".
- **Tiền đề DB (ĐÃ CHẠY 06/10):** `DM_DVHC` DB nguồn `GPLX_CSDT` trước đó cũ — **toàn bộ mã tỉnh 2 ký tự TrangThai=0** (combo nơi cấp + picker Tỉnh rỗng) và **không có '00'**. Đồng bộ đích→nguồn bằng `update/sync-DM_DVHC-tu-DB-dich-sang-DB-nap.sql` (MERGE theo cặp PK `(MaDvhc,MaDVQL)` + `COLLATE` cross-DB; UPDATE 15.744 + INSERT 11; **KHÔNG DELETE** → không đụng 4 FK). Backup `dbo.DM_DVHC_backup_20261006`. Sau sync: nguồn = đích (15.755 dòng), 34 tỉnh active + '00' Cục QLHC. *(Script đồng bộ cả cấp xã → picker địa chỉ cũng đúng tên tỉnh sáp nhập.)*
- **Đã sửa tài liệu:** PRD (QLY-01 +ghi mở rộng, TCB-03 đổi nhãn nguồn nơi cấp, Changelog v3.5) · TDD (§11B.7 nơi cấp DM_DonViGTVT→DM_DVHC + tiền đề sync DM_DVHC + QLY-01 mở rộng, Changelog) · BUGS #10 (đánh dấu thay thế bởi #40) · CHANGES (#40 + Mốc).
- **Code: ✅ xong** 3 commit (`928a019`/`4acc943`/`946a56f`) + script sync; 304 backend + 34 vitest + tsc, verify live DB nguồn+đích. **Chưa push.** **NAP-05 giữ ✅** (SP nạp lõi không đổi; nơi cấp là BUG-10 tracked riêng). Cần **`/reviewtdd` §11B.7** (đã chạm thiết kế sửa nhân thân + danh mục).

---

## #39 — Refresh-token VPS cho phiên tool vĩnh viễn (DGT-04) · 05/10/2026

- **Nguồn:** phát hiện Chặn 2.1 của `/reviewtdd` #38 (biên bản `docs/tdd-review-05-10-2026.md`, mục Hoãn lại).
- **Vấn đề:** DGT-04 cho phiên **local** sống vĩnh viễn, nhưng `vps_token` nhét trong phiên là JWT do VPS phát, **hết hạn 8h** (§12). Sau 8h / mở lại hôm sau, user vẫn "đã đăng nhập" (tra cứu + sửa local chạy), **nhưng mọi call VPS — kéo hồ sơ mới / lock / đã-nạp / tải ảnh / đối soát QLY-08,09 — đều 401**, tool câm lặng hỏng đúng việc nạp.
- **Chốt (user 05/10 — cách A, `/capnhat` #39):**
  - VPS cấp **refresh token** khi đăng nhập; tool lưu ra đĩa **mã hóa DPAPI** (như phiên).
  - Heartbeat thu-hồi-từ-xa **kiêm làm mới token**: định kỳ (khởi động + mỗi N giờ) đổi refresh token lấy `access_token` mới qua **`POST /api/auth/refresh`**. Refresh token hỏng / tài khoản bị khóa → xóa phiên, buộc đăng nhập lại.
  - Đăng xuất → thu hồi cả refresh token.
  - **Gộp vào DGT-04** (user chốt A) — refresh-token chỉ phục vụ DGT-04, không tạo story server riêng; phần endpoint ghi ở TDD §12.
- **Phạm vi chạm:** server VPS (`server/app` — endpoint `/api/auth/refresh` + cấp/xoay refresh token) **và** tool (`session.py` + heartbeat). Đăng nhập app web giữ nguyên.
- **Đã sửa:** PRD (DGT-04 +Done khi refresh token + sửa "key.bin"→mã hóa ràng máy, Changelog v3.4) · TDD (§12 +refresh token, §11C.4/§16 cập nhật "đã /capnhat", Changelog v4.2) · CHANGES (#39 + Mốc đối chiếu).

---

## #38 — Nhóm "Đóng gói & khởi chạy tool độc lập" (DGT-01..04) · 05/10/2026

- **Mã mới:** `DGT-01..04` — prefix **DGT** ("Đóng gói tool") mới, user chốt. Nhóm 🟣 cuối ③ (chỉ tool máy CSDT).
- **Vì sao:** cần mang tool sang máy CSDT khác chạy được ngay **không cài Python/Node**, mở như phần mềm thường, và lần sau dùng **không phải gõ địa chỉ / thiết lập / đăng nhập lại**.
- **Chốt (user 05/10, qua trao đổi):**
  - **DGT-01 đóng gói:** PyInstaller gói Python + mọi thư viện backend vào exe; FastAPI phục vụ luôn `webui/dist` trên cùng cổng (frontend `BASE=""` ở bản production — đã sẵn); kèm data (`dvhc_map.sqlite`…); ghi config/nháp/ảnh vào `%APPDATA%` (không vào Program Files).
  - **DGT-02 khởi chạy:** mỗi lần chạy tự mở trình duyệt đúng trang; biểu tượng khay (Mở giao diện/Thoát), ẩn console; chống chạy 2 bản (đưa bản đang chạy lên); dò cổng trống nếu bận; tùy chọn tự chạy khi bật máy.
  - **DGT-03 wizard lần đầu:** máy sạch → dẫn 3 bước (kiểm môi trường → cấu hình SQL nguồn/đích + VPS, test-before-next → đăng nhập); lần sau có cấu hình thì vào thẳng. Tái dùng `CauHinhDrawer` + `/local/config/test` + `/local/auth/login` (đều không bị gác token — "config là bước mồi").
  - **DGT-04 phiên vĩnh viễn:** lưu phiên ra đĩa mã hóa bằng `key.bin`, mở exe lần sau vào thẳng **không hỏi đăng nhập**; **chỉ nút "Đăng xuất" (đã có)** mới thoát; thêm **thu hồi từ xa** (ngầm hỏi VPS tài khoản còn hiệu lực khi có mạng). Chọn "vĩnh viễn" (bác mốc 30 ngày / hết ca).
- **Rủi ro đã nêu & chấp nhận (user 05/10):** phiên vĩnh viễn = ai ngồi vào máy cũng vào thẳng (sửa/xóa GPLX + xem căn cước). Chấp nhận vì máy nội bộ CSDT 1 người dùng; lưới = Đăng xuất + thu hồi từ xa. Máy dùng chung sau này → thêm "hỏi mật khẩu khi xóa/đổi khóa" (để sau). Ghi vào TDD §16.
- **Phạm vi:** chỉ **tool**; đăng nhập app web (VPS, đa người) giữ phiên thường → HTG-01 vẫn ✅ (chỉ +1 dòng trỏ DGT-04).
- **Đã sửa:** PRD (+nhóm DGT 4 story + dòng HTG-01, Changelog v3.3) · TDD (+§11C + 2 rủi ro §16, Changelog v4.0) · TDD-decisions (+§16) · CHANGES (#38 + Mốc đối chiếu).
- **Chưa code** (⬜) — Feature mới hoàn toàn (đóng gói/khởi chạy), **chưa vào BUILD-PLAN**. Cần `/kehoach` bổ sung (task đóng gói + wizard + phiên đĩa) và `/reviewtdd` §11C trước khi code.

## #37 — Mở rộng trường sửa nhân thân ở Tra cứu CDB (TCB-03) · 05/10/2026

- **Mã:** `TCB-03` (mở rộng tiêu chí, không thêm/bớt mã). Hạ **✅→⏳ Todo**.
- **Vì sao:** nghiệm thu Checkpoint 14 tại máy CSDT (05/10), user thấy form sửa nhân thân chỉ cho sửa 5 trường (họ tên, ngày sinh, giới tính, CCCD, nơi thường trú dạng chữ) — **thiếu ô chọn địa chỉ 2 cấp** (Xã/Tỉnh chuẩn) và **ngày cấp CCCD**. Sửa CCCD mà không sửa được ngày/nơi cấp + không chỉnh được Xã/Tỉnh chuẩn là nửa vời.
- **Chốt (user 05/10):**
  - Thêm 3 trường: **địa chỉ thường trú 2 cấp** (`NoiTT_MaDVHC`/`NoiTT_MaDVQL` — chọn Tỉnh + Xã chuẩn) · **ngày cấp CCCD** (`NgayCapCMT`) · **nơi cấp CCCD** (`NoiCapCMT`, Sở GTVT). `usp_NguoiLX_Update` đã có sẵn tất cả tham số → chủ yếu mở rộng model + `dung_tham_so_update` (đang giữ nguyên các cột này từ bản ghi cũ).
  - **Phạm vi: CHỈ TCB-03.** Form sửa dùng model CHUNG `HoSoSua` (`hoso.py`) cho cả Nạp QLY-01 lẫn TCB — nhưng user chốt **chỉ mở rộng ở TCB**, Nạp giữ 5 trường → **tách model riêng cho CDB** (`HoSoSuaCDB` ở `sync_tracuu.py`), không đụng `HoSoSua`.
  - **Nơi cư trú 2 cấp** (`NoiCT*`): để sau (ít dùng). **Số CMND cũ** (`SO_CMND_CU`): KHÔNG làm — `usp_NguoiLX_Update` không nhận tham số đó (cần sửa SP → quá tầm).
- **Lưu ý kỹ thuật (ghi vào TDD):** bộ chọn Tỉnh/Xã (`ComboLoc`/`AddressCombo`) + danh mục Sở (`DM_DonViGTVT`) hiện đọc từ **DB Nạp**; cho TCB phải đọc `DM_DVHC`/`DM_DonViGTVT` ở **DB đích** (`sqlserver_conn_dich`, theo `target_key`) — nếu không Xã/Sở hiện sai danh mục.
- **Nghiệm thu đã có (Checkpoint 14, máy CSDT 05/10):** bản 5 trường **ghi-thật PASS** — sửa chị Hương (khóa test B01-KTEST chưa gửi Sở) đổi họ tên/năm sinh/CCCD/nơi TT, `POST /sua` 200 OK, verify DB khớp. 3 nhánh còn lại (thay ảnh TCB-02, xóa/đổi khóa TCB-04) **chưa nghiệm thu** vì thiếu môi trường (ổ ảnh không khớp DB + chỉ 2 khóa chưa gửi Sở khác hạng). Feature TCB giữ 🔄.
- **Đã sửa:** PRD TCB-03 (Done khi + story + edge, hạ ⏳, Changelog v3.2) · TDD §11B.7 (Changelog v3.8) · SCREENS màn #19 (ghi chú).
- **Đã `/reviewtdd` §11B.7** (05/10, biên bản `tdd-review-05-10-2026-tcb37.md`, TDD v3.9): 0 Chặn · 3 Nên sửa · 1 Ghi nhận — đều đã vào TDD.
- **Đã code** (05/10) — nằm trong story TCB-03, không task BUILD-PLAN mới. Backend: `dvhc.ds_*` nhận `db` đích; `sync_tracuu.py` +model `HoSoSuaCDB` + `dung_tham_so_update_cdb` (tái dùng `_EXEC_UPDATE`) + `chi-tiet-sua` trả 4 mã preselect + 3 endpoint danh mục đích; `/sua` dùng model mới (bỏ-trống-giữ-cũ). UI `TraCuuCDB.tsx`: +Tỉnh/Xã (ComboLoc) + ngày cấp (ODate) + nơi cấp (ComboLoc), danh mục đọc DB đích. **Kiểm:** unit 287 pass + TS + build sạch; probe CDB đủ danh mục. **Còn:** nghiệm thu ghi-thật tại máy CSDT (user lái UI) → TCB-03 ✅.

## #36 — Sửa định nghĩa "đã kết xuất DKKH" + nâng ngưỡng chặn TCB-04 + cải tiến Sync · 05/10/2026

- **Vì sao:** user phát hiện mốc "đã kết xuất DKKH" ở TCB đang đọc sai (`KhoaHoc.SoQD_KhaiGiang`) và luật TCB-04 cho đổi/xóa HV ở khóa đã gửi Sở → lệch danh sách đã nộp.
- **Định nghĩa đúng (verify DB 05/10, xem `docs/DB-GPLX_CDB_CSDT.md` §7):** khóa **đã kết xuất DKKH** = có gói `TRANS_CLI_HangDoiGui` `KieuDuLieu='DANG_KY_KHOA_HOC'` mà tên file chứa MaKH (neo `_MaKH_`, CHARINDEX). **KHÔNG** dùng `SoQD_KhaiGiang` (16/16 khóa đều có số QĐ nội bộ → không phân biệt; chỉ 14/16 đã gửi Sở) · **KHÔNG** `KhoaHoc.TT_Xuly` (NULL) · **KHÔNG** `NguoiLX_HoSo.TT_XuLy` per-HV (khóa đã gửi, HV vẫn `03`). Định nghĩa CHUNG: `sync_helpers.dkkh_exists_sql` / `dkkh_exists_cond`.
- **TCB-01/03:** chip "Đã kết xuất DKKH" + chặn sửa nhân thân — nay đọc tín hiệu đúng (C1-K09 có SoQD nhưng chưa gửi Sở → không còn bị chặn nhầm).
- **TCB-04 (nâng ngưỡng chặn — user chốt 05/10):** khóa đã DKKH → **KHÔNG xóa HV, KHÔNG đổi khóa**; đổi khóa chặn nếu **khóa đi HOẶC khóa đến** đã DKKH; `khoa-cung-hang` lọc bỏ khóa DKKH; UI vô hiệu nút Đổi khóa/Xóa + ghi lý do. DKKH luôn trước BC1 → mốc chặn sớm hơn, bao trùm BC1 (BC1+FK giữ làm lưới). *(Lật quyết định cũ "ngưỡng chặn cứng là BC1".)*
- **Nguồn giữ BC1:** QLY-02 (đổi khóa) + QLY-06 (tạo thêm hồ sơ khác hạng) bên Nạp **không áp DKKH** — nguồn `GPLX_CSDT` có bảng `TRANS_CLI` nhưng **0 bản `DANG_KY_KHOA_HOC`** (chỉ BC1/BC2) → tín hiệu DKKH không tồn tại ở nguồn.
- **+SYNC-01 (3 cải tiến):** (a) filter khóa đích *"Chỉ khóa cùng hạng & chưa kết xuất DKKH"* (checkbox mặc định bật) · (b) khóa xếp **mới-nhất-trước** (ORDER BY NgayKG DESC, **MaKH DESC** + hiện ngày KG ở combo nguồn) · (c) **giữ phiên đăng nhập qua F5** (token→localStorage + khôi phục `/local/auth/me` + tự kiểm kết nối đích khi vào màn).
- **Đã sửa:** PRD TCB-03/TCB-04 + SYNC-01 + edge "Session" (v3.1) · TDD §11B.2/§11B.7/§5.5 (v3.6) · `docs/DB-GPLX_CDB_CSDT.md` +§7 · code `sync_helpers.py`/`sync.py`/`sync_tracuu.py`/`BanDongBo.tsx`/`TraCuuCDB.tsx`/`api.ts`/`ToolAuth.tsx`/`App.tsx`.
- **Trạng thái story:** TCB-01/02/03/04 + SYNC-01 **giữ ✅** (code đã sửa + verify live/DB 05/10 — khác luồng thường: code trước, /capnhat sau). Nghiệp vụ sync lõi không đổi.
- **Còn nợ:** chưa commit · ghi-thật đổi/xóa + sửa nhân thân live vẫn chờ Checkpoint 14 (máy CSDT, có giám sát) · trên dev CDB mọi khóa đã-DKKH đều đã-BC1 nên luật mới chưa đổi outcome trên data hiện tại (đúng cho ca thực tế khóa chưa BC1).

## #35 — Feature "Tra cứu CDB đích" (TCB-01..04) · 04/10/2026

- **Mã mới:** `TCB-01` (tra khóa+lưới HV+chi tiết+ảnh), `TCB-02` (thay ảnh), `TCB-03` (sửa nhân thân), `TCB-04` (xóa HV/đổi khóa) — prefix **TCB** mới ("Tra cứu CDB", user chốt), nhóm trong phân hệ Đồng bộ CDB (SHOULD).
- **Vì sao:** user cần xem lại + vá dữ liệu HV **đã đồng bộ sang CDB đích** (`GPLX_CDB_CSDT`) ngay trong tool — xem chi tiết/ảnh, thay ảnh hỏng, sửa sai nhân thân, xóa/xếp lại khóa — mà không phải mở phần mềm CDB.
- **Chốt qua trao đổi + rà soát schema CDB (04/10):**
  - **Ảnh dùng chung 1 file vật lý** giữa DB Nạp và DB đích (sync copy `DuongDanAnh` verbatim; probe: CDB 729 HV 100% có ảnh, trỏ `D:\GPLXCSDT\ANHCDUNG\<khóa nguồn 70004>\…jp2`). → **Thay ảnh ghi ĐÈ đúng file, giữ nguyên tên+đường dẫn** (user chốt) → cả 2 DB cùng đổi ảnh. Cho thay kể cả khi DKKH/BC1 (cảnh báo).
  - **Hai mốc khóa dữ liệu (đọc Ở ĐÍCH, độc lập DB Nạp):** *đã kết xuất DKKH* = `KhoaHoc.SoQD_KhaiGiang` có giá trị (mềm — chặn **sửa nhân thân**); *đã BC1* = `TT_XuLy ≥ '05'`/có dòng `BaoCaoI`, FK `FK_NguoiLX_HoSo_BaoCaoI` NO_ACTION (cứng — chặn **xóa + đổi khóa**). Ngưỡng chặn xóa là BC1 (KHÔNG phải DKKH) để không chết Hủy sync (SYNC-03 xóa HV TT_XuLy=03).
  - Danh mục trạng thái `DM_TrangThai` (MaTT→TenTT + nhóm cấp CDB MaTTCDB: 03/04 "Đã đăng ký khóa học", 05-07 đang đào tạo, 09-14 kết quả/BC2). Dữ liệu CDB dev: HV ở 03 (639)/10 (20)/12 (70); 15/15 khóa có SoQD_KhaiGiang.
  - **Phương án A** (user chốt): thay ảnh cho + cảnh báo · sửa nhân thân chặn sau DKKH · xóa/đổi khóa chặn sau BC1.
- **Đã sửa:** PRD (+4 story TCB nhóm Đồng bộ CDB; SYNC-01 +ghi chú nút Xem chi tiết, giữ ✅; Changelog v3.0) · TDD §11B.7 mới (màn CDB, luật khóa, thay ảnh ghi đè chung, SP cần kiểm; Changelog v3.4) · SCREENS màn #19 + 2 quyết định UX (lượt 21).
- **KHÔNG chạm:** màn Tra cứu DB bên Nạp (QLY-01, đọc `GPLX_CSDT`) · quyết định TDD §12/13/14.
- **Chưa code** (⬜). **Hướng dựng:** `webui/src/pages/sync/TraCuuCDB.tsx` (tái dùng AnhModal/AnhAvatar) + endpoint CDB mới (`routers/sync.py` hoặc module mới) trỏ `sqlserver_conn_dich` + sửa `BanDongBo.tsx` (nút). Vào BUILD-PLAN qua `/kehoach` bổ sung.
- **Còn kiểm khi code:** CDB có `usp_NguoiLX_Update` / SP đổi khóa / SP xóa (như GPLX_CSDT) không — nếu thiếu thì tắt nút tương ứng + báo.
- **Tinh chỉnh sau /reviewtdd (04/10, biên bản `docs/tdd-review-04-10-2026-tcb.md`, TDD v3.5):** (1) mốc "đã BC1" chốt lại = **`NguoiLX_HoSo.MaBC1` có giá trị** (đúng cái FK NO_ACTION chặn — bỏ cách hiểu `TT_XuLy≥'05'`/dòng BaoCaoI cấp khóa vì 3 tín hiệu lệch nhau) → cập nhật câu chữ PRD TCB-04; (2) thay ảnh TCB-02 **sao lưu `_BACKUP.jp2` cùng thư mục ảnh trước khi ghi đè** → cập nhật PRD TCB-02; (3) endpoint TCB ghi buộc token operator; (4) nới câu chữ §12 "DB đích"; (5) +bảng ma trận quyết định. Không đổi phạm vi/tính năng — chỉ làm chính xác lại quyết định đã chốt ở #35.

---

## #34 — Cấu hình kết nối lên header dùng chung + tách DB Nạp/Sync + làm đẹp UI sync · 04/10/2026

- **Mã mới:** `HTG-07` (Bảng cấu hình kết nối dùng chung ở header) — prefix `HTG` sẵn có, nhóm MUST.
- **Mã sửa:** `HTG-01` (bullet Cấu hình trỏ sang HTG-07, giữ ✅), `SYNC-02` (quản lý đích dời vào panel — hạ ✅→⏳), `SYNC-01` (làm đẹp UI — hạ ✅→⏳). Không mã nào nghỉ hưu.
- **Vì sao:** chủ dự án phản hồi khi test: cấu hình kết nối DB dùng chung cả tool nhưng nằm ở màn riêng → "không biết cài kết nối ở đâu"; cần đưa lên **header** để mọi màn xem/sửa được, và **phân biệt rõ** đâu là DB để **Nạp** (1 nguồn `GPLX_CSDT`) với các DB để **Sync sang** (nhiều, chọn mặc định) — tránh nhầm hai loại. Đồng thời làm đẹp combobox năm/khóa + chọn DB đích + danh sách HV để sync (tên hài hòa, dễ đọc).
- **Chốt (user 04/10, phương án A):** gộp tất cả vào **một bảng cấu hình mở từ icon ⚙ header**, chia 2 khối tách bạch (① kết nối chung + DB nguồn Nạp · ② nhiều DB đích Sync); **bỏ** màn Cấu hình riêng `/tool/cau-hinh` + mục "Quản lý CSDL đích" khỏi sidebar — chỉ vào từ header.
- **Ràng buộc:** code phần sync vẫn **bám sát sync_tool v2.0** — thay đổi này thuần UI/IA, không đụng nghiệp vụ sync.
- **Đã sửa:** PRD (+story HTG-07; sửa bullet HTG-01; hạ SYNC-01/SYNC-02 ✅→⏳ + ghi chuẩn UI; Changelog v2.9) · TDD §5.0 + §11B.0 (bỏ route cau-hinh/db-dich khỏi sub-nav, mô tả panel ⚙ header; Changelog v3.3) · SCREENS (màn #4 thành panel header, #16 làm đẹp, #17 dời vào panel; +3 quyết định UX; lượt 20).
- **KHÔNG chạm:** quyết định kỹ thuật TDD §12 (sidebar module) / §13 (nhiều đích dùng chung host/user/pass) / §14 (SSE) — đều còn đúng → **không cần `/reviewtdd`**. Backend `/local/config*`, `/local/sync/targets`, config-store giữ nguyên.
- **Bug môi trường đã sửa (không phải lỗi code):** backend nền khởi động bằng `tool-start.bat` **không có `--reload`** → kẹt bản code cũ (chạy sau SYNC-02 nhưng trước SYNC-01) → route `/local/sync/nguon/nam` + `/dich/nam` trả **404**, combobox năm/khóa ở Bàn đồng bộ trống (frontend `.catch` nuốt lỗi). **Xử lý:** restart backend → route trả 401 (đã có), đăng nhập gọi `nguon/nam` trả `[2026…2012]` ✔. **Đã thêm `--reload --reload-dir app`** vào `tool-start.bat` (user duyệt) để sửa code backend tự nạp, khỏi tái phát. Phụ: màn Bàn đồng bộ bỏ 2 `catch(()=>{})` câm khi tải năm/khóa → nay báo lỗi rõ (chính cơ chế che lỗi 404 lần này).
- **Chưa code** (⬜). **Hướng dựng:** sửa `ToolLayout.tsx` (icon ⚙ header + panel), gộp `CauHinh.tsx` + `DbDich.tsx` vào panel (2 khối), gỡ 2 route khỏi `App.tsx` + sidebar; làm đẹp `BanDongBo.tsx` + `ComboLoc.tsx`. Dùng skill `impeccable` + `ui-ux-pro-max`. Vào BUILD-PLAN qua `/kehoach` bổ sung (hoặc gộp vào task UI sync đang có).

---

## #33 — Feature "Đồng bộ CDB" (SYNC-01/02/03) + tool chuyển sang sidebar module · 04/10/2026

- **Mã mới:** `SYNC-01` (Bàn đồng bộ), `SYNC-02` (Quản lý DB đích), `SYNC-03` (Lịch sử & Hủy sync) — prefix `SYNC` mới, nhóm SHOULD.
- **Vì sao:** cần đưa nghiệp vụ đồng bộ học viên `GPLX_CSDT` → CDB `GPLX_CDB_CSDT` (đang chạy bằng công cụ rời `sync_tool` v2.0, CustomTkinter) vào chung tool máy CSDT, nhưng **tách bạch** để không lẫn với Nạp (hai bên ghi vào 2 DB khác nhau — dễ thao tác nhầm).
- **Nguồn port:** `D:\Du_An\GPLX\sync_tool` v2.0 = 3 file `sync_gplx.py` + `db_helpers.py` + `sync_history.py` (đã đọc trọn; không còn logic ngoài 3 file). Format mã theo Phụ lục XXVII TT 17/2026/TT-BXD.
- **Đã sửa/thêm:**
  - PRD: thêm nhóm 🟣 "Đồng bộ CDB" (3 story) cuối SHOULD; ⑥ NFR thêm kiến trúc module+sidebar + tool chỉ-desktop; ⑦ thêm 3 edge Sync; Changelog v2.8.
  - TDD: §11B (kiến trúc module/sidebar · kết nối đích nhiều DB · luồng sync + MaDK batch + guard race · SSE · rollback dual-mode · 3 nợ kỹ thuật) + §2.4 cây thư mục; Changelog v3.2.
  - TDD-decisions: §12 (sidebar module), §13 (kết nối đích dùng chung host/user/pass, nhiều đích), §14 (SSE).
  - SCREENS: màn #16/17/18 (⬜) + quyết định UX (sidebar, tool desktop ≥1280px bảng cuộn ngang, bám design system tool thật + dùng skill UI).
  - **Phân tích DB đích (04/10)** → `docs/DB-GPLX_CDB_CSDT.md` (mới): cách tạo HV chuẩn (3 SP `usp_NguoiLX_Insert`/`usp_NguoiLX_HoSo_Insert`/`usp_NguoiLXHS_GiayTo_Insert`) · sinh mã (`CreateNewMaDK` hardcode getdate, `CreateNewSoHoso` `B01`) · MaCSDT lấy từ khóa đích = `QTHT.MA_CSDT`=75032 · PK(MaDK) + FK cascade (xóa khóa/người kéo xóa hồ sơ; BaoCaoI chặn xóa) · cột kết quả đào tạo sẵn trong `NguoiLX_HoSo` (cho module #3). CLAUDE.md thêm trỏ đọc trước khi code CDB. TDD §11B.6 cập nhật hướng chốt 3 nợ kỹ thuật.
  - **Khóa đích đã BC1 (04/10):** cảnh báo nhưng **vẫn cho sync** (phương án B — khác NAP-02 chặn cứng; sync là bù dữ liệu chủ động). sync_tool gốc không chặn/không cảnh báo. PRD SYNC-01 +tiêu chí.
  - **Tiện ích + edge thêm (04/10, user đồng ý):** UI (a) combo khóa gõ-để-lọc · (b) toggle "chỉ hiện HV sẽ tạo mới" · (c) đếm dòng tick cạnh SYNC. Edge: E1 chặn HV thiếu CCCD · E2 cảnh báo trùng CCCD trong DS nguồn · E3 sync-lại an toàn khi mất kết nối giữa lô (idempotent qua skip). E4 (HV chưa ảnh) giữ nguyên v2.0 (ép TT_XuLy 03). Dropdown khóa nguồn+đích bám đúng v2.0: combo Năm (DISTINCT YEAR NgayKG, mặc định năm nay) + combo Khóa (TrangThai=1 + năm).
  - **Chốt qua mock `ui-mock/sync.html` (04/10):** ① **bỏ ô "Cán bộ nạp"** → `NguoiTao/NguoiSua='admin'` (probe DB `GPLX_CDB_CSDT`: NguoiTao chỉ `ADMIN`/`SYNC`, 10 bản mới nhất `admin` — CDB không có cán bộ riêng; TDD-decisions §15) · ② **bỏ Xuất CSV** (không cần) · ③ tối ưu danh sách: khung chọn khóa **cố định + thu gọn được**, **header bảng dính**, **nút SYNC cố định ở chân**, **phân trang** 20/50/100 (mẫu `PhanTrang.tsx`), dòng dày hơn để hiện nhiều HV.
- **Còn nợ:**
  - **Chưa code** (⬜). **Hướng dựng UI đã chốt (user 04/10, phương án A):** BỎ QUA `ui-demo` (prototype cũ đã lệch so với `tool/webui` thật) → dựng **1 mock HTML sidebar + 3 màn Sync bám token `tool/webui` thật** (dùng skill UI `ui-ux-pro-max`/`impeccable`) để chốt layout → **code thẳng vào `tool/webui`** (gồm đổi `ToolLayout`→sidebar). KHÔNG dùng `/prototype-next`.
  - **Xác minh trước khi code:** chữ ký `usp_NguoiLX_Insert` + hàm `CreateNewMaDK` trên DB đích CSDT **70004** có giống bản 75032 mà sync_tool giả định.
  - **3 nợ kỹ thuật port** (quyết giữ/vá khi code): `SoHoSo` sinh ở Python (nên gọi `CreateNewSoHoso`) · `DELETE` NguoiLX mồ côi quét toàn DB (nên lọc khóa) · `except: pass` khi copy giấy tờ.
  - Đổi `ToolLayout` sang sidebar đụng chrome module Nạp (hành vi màn Nạp **không đổi** → không hạ trạng thái story Nạp).
- **Chưa làm tay:** `/kehoach` bổ sung (~3-4 task: config+kết nối đích → API+SSE → UI sidebar+3 màn → rollback); `/reviewtdd` (đã sửa §11B + Data-flow); `/prototype-next` hoặc build thẳng.

---

## #32 — Lưu nháp chuẩn bị BỀN + 2 chip trạng thái + bổ sung ảnh 2 nguồn (màn Nạp lô) · 04/10/2026

- **Mã:** `NAP-01`, `QLY-05` (bổ sung tiêu chí, prefix cũ, không nghỉ hưu mã).
- **Vì sao:** chủ dự án hỏi "nháp chưa nạp có mất khi kéo lại / xóa hết trên app web không" → rà kiến trúc 3 kho tách biệt: nháp chuẩn bị (địa chỉ 2 cấp, ảnh đổi nền, tick) hiện **chỉ ở RAM** của màn, mất khi tải lại trang. Chốt nâng nháp lên **lưu bền** để người nạp chuẩn bị nhiều HV an tâm, kèm 2 chip nhìn nhanh dòng nào đã map địa chỉ / đã có ảnh, nút mở to dễ bấm, và cho bổ sung ảnh HV thiếu ảnh lấy từ file hoặc kéo lại ảnh thô VPS.
- **Lưu nháp bền (TDD §9.3a):** bảng mới `nhap_chuan_bi` trong `staging.sqlite` (tách khỏi `keo_ve` dữ-liệu-gốc-VPS); lưu địa chỉ/chi tiết/nơi cấp/tick + ảnh (`jp2_b64`+preview). API tool-local `GET/PUT /local/nap/nhap/{uuid}`. **Tự xóa** (`nhap_xoa(uuid)`) ở mọi điểm dòng `keo_ve` kết thúc: nạp xong, "Bỏ khỏi hàng đợi", đồng bộ xóa VPS. **BUG-04:** `keo_ve_upsert` khi làm tươi thấy `noi_tt_raw` đổi → reset ĐỊA CHỈ nháp (giữ ảnh/tick/nơi cấp) + chip địa chỉ về ✗ + toast.
- **UX màn Nạp lô (TDD §10.5):** 2 chip `✓/✗ Địa chỉ 2 cấp` + `✓/✗ Có hình` (mặc định ✗); nạp **chặn khi thiếu địa chỉ**, **cảnh báo khi thiếu ảnh** + lối tắt chuyển Tra cứu DB lọc "chưa ảnh"; mở drawer bằng cả dòng + nút "Xử lý" to.
- **Bổ sung ảnh HV thiếu ảnh (TDD §11.5):** AnhModal lấy ảnh gốc từ **file** (`chonFile`, sẵn có) hoặc **ảnh thô VPS** (`vps.tra_uuid`→`vps.tai_anh`→`AnhModal.napTuUrl`, sẵn có) — điều kiện ảnh còn trên VPS (~30 ngày); hết hạn thì chỉ còn nguồn file. Qua cùng luồng QLY-05 (đổi nền → `.jp2` → `nap_anh`).
- **Quyết định PII (TDD-decisions §11):** lưu ảnh nháp bền ở máy tool đi ngược nguyên tắc cũ "không để ảnh căn cước ở máy tool"; chấp nhận có điều kiện (máy nội bộ CSDT + cam kết tự xóa + không commit/backup). Phương án B (lưu bền + tự xóa) do user chốt; đã bác phương án không-lưu-ảnh.
- **Xác minh bằng GitNexus:** `keo_ve` chỉ chứa metadata (không có chỗ lưu nháp → mới hoàn toàn); `AnhModal` đã có `chonFile`+`napTuUrl`; `nap_anh` dùng chung `ghi_anh_update`; `vps.tra_uuid`/`vps.tai_anh` sẵn có → phần ảnh tái dùng gần hết, chỉ wiring.
- **Đã sửa:** PRD (NAP-01 +4 "Done khi" + 1 edge; QLY-05 +1 "Done khi"; cả 2 giữ trạng thái, ghi chú yêu cầu mới) · TDD §9.3a (mới) /§10.5/§11.5 + Changelog v3.2 · TDD-decisions §11 (mới).
- **Chưa code** — vào BUILD-PLAN (nằm trong task redesign Nạp lô #26 chưa code + thêm phần nháp bền/ảnh VPS). Code UI chạy skill `impeccable`.
- **Còn nợ:** toàn bộ phần code (⬜). Màn: cập nhật `ui-demo/SCREENS.md` ghi chú 2 chip + nút Xử lý.

---

## #30 — Redesign giao diện DESKTOP app web: Quét ưu tiên nhập tay + Hồ sơ đã gửi xóa nhiều · 03/10/2026

> Đổi số từ #28 → #30 khi gộp 2 phiên song song (số #28 đã thuộc QLY-09).

- **Mã:** `THU-01` (✏️ Sửa), `THU-05` (➕ Thêm)
- **Vì sao:** Trên máy tính, nhân viên gõ bàn phím là chính; quét QR bằng webcam khó canh. Giao diện cũ (dùng chung mobile) đặt nút Quét QR giữa màn + chặn màn "chọn cách nhập" trước form → desktop bấm thừa. Nút Xóa hồ sơ chờ nạp chôn trong modal → xóa nhiều phải mở từng cái.
- **Đã làm:** ① Quét (THU-01) desktop vào thẳng form nhập tay (bỏ cổng `ChonCach`), Quét QR/Tải ảnh thành nút phụ góc phải, popover camera đè form tự điền, "Lưu & nhập tiếp" → form trống; mobile giữ nguyên. ② Hồ sơ đã gửi (THU-05) desktop chọn-nhiều-để-xóa (ô tích chỉ dòng Chờ nạp + thanh Đã chọn N/Xóa N + dialog), lặp `DELETE /api/ho-so/:uuid` client (mẫu `QuanTriHoSo`); mobile giữ xóa lẻ.
- **Code:** `webapp/src/pages/Quet.tsx` (hook `useIsDesktop` + `QuetPopover`) + `DaGui.tsx` (chọn-nhiều + phân biệt 409). Thuần client. Kiểm: build + 24 vitest + review-nghiepvu THU-01 8/8, THU-05 đủ.
- **Còn nợ:** chụp Playwright 3vp + verify desktop sau deploy → khi đó hạ ⚠️ Partial.

---

## #29 — Tool máy Nạp: dời nút nạp lên header + combobox gõ-lọc địa chỉ · 03/10/2026

- **Mã:** `NAP-01` (dời nút), `NAP-03` (combobox) — ✏️ Sửa UI, thuần client.
- **Vì sao:** ① 2 nút "Chọn tất cả sẵn sàng" + "Nạp N học viên vào khóa" trước nằm ở **thanh dính đáy** — user muốn đưa **lên header** cho thao tác gọn, nút nạp nằm cùng vùng chọn khóa/kéo về. ② Ô "Chọn tay" địa chỉ 2 cấp mới là 2 **dropdown** — danh sách xã rất dài, cuộn mệt; user muốn **gõ để lọc**.
- **Đã làm:**
  - **NAP-01** (`tool/webui/.../NapHoSo.tsx`): gỡ thanh dính đáy, dựng lại thành **hàng hành động shrink-0 ngay dưới tab lọc** trong container `h-[calc]` → chỉ danh sách cuộn, nút Nạp luôn hiện. Chỉ hiện ở tab "Cần xử lý".
  - **NAP-03** (`tool/webui/src/components/AddressCombo.tsx`): thêm `ComboLoc` — ô gõ → danh sách gợi ý lọc dần (khớp cả **không dấu** nhờ `boDau`), bấm/Enter chọn; thay 2 `<select>` Tỉnh + Xã ở "Chọn tay". `getTinh`/`getXa` dữ liệu sẵn, **không đổi backend**.
- **Kiểm:** tool webui build + typecheck + **29 vitest** pass. **Chưa chụp Playwright** (màn tool cần backend + DB). Wireframe đã chốt với user.
- **Nhánh:** code ở `feat/nap-address-ui` (commit `03d4243`) — chưa merge main.

## #28 — Đối soát & đồng bộ trạng thái VPS↔CSDT (QLY-09) · 03/10/2026

- **Mã:** `QLY-09` (MỚI, nhóm QLY, nối tiếp QLY-08).
- **Vì sao:** ca Lê Thị Hồng (BUG-01) lộ ra khi VPS và CSDT lệch trạng thái thì không có cách sửa trong ứng dụng — phải SSH sửa tay DB production. Chủ dự án yêu cầu: "phải có cách đồng bộ lại để fix, không để treo lỗi".
- **Chốt (chủ dự án, 03/10):**
  - Phạm vi **theo khóa / theo yêu cầu** (A) — không quét toàn bộ (tránh so chéo 2 DB toàn tập, chậm khi lớn; mở rộng sau nếu cần).
  - Panel admin/operator ở tool (trong Tra cứu DB), **không collector**.
  - **3 ca lệch + nút sửa 1 chạm**, tái dùng đường có sẵn: ① VPS `imported` & CSDT không có `MaDK` (phantom) → **Trả về chờ nạp** (`tra_ve_cho_nap`) · ② CSDT có HV & VPS chưa `imported` → **Đánh dấu đã nạp** (`da_nap`) · ③ `importing` treo quá ngưỡng → **Mở khóa** (`unlock`).
  - **Phòng tuyến 2:** `nap_fn` bỏ gọi `da_nap` khi `_nap_mot` trả kết quả cũ từ vé idempotency (không INSERT mới) — chặn tận gốc "phantom import" (BUG-01).
- **Đã sửa:** PRD +story `QLY-09` (nhóm QLY, ⏳ Todo) · TDD §11.8 mới + Changelog 3.0.
- **Chưa code** — vào BUILD-PLAN task mới (`/kehoach` bổ sung). Thuần tool (webui panel + tool backend đọc CSDT/gọi VPS); KHÔNG bảng VPS mới, KHÔNG SP CSDT mới, KHÔNG endpoint nạp mới.
- **Không đụng:** schema DB CSDT · bảng VPS · app web collector.

---

## #26 — Chốt nghiệp vụ + UX trước khi code #24 (bàn giao, popup cảnh báo, ảnh gốc, redesign Nạp lô) · 03/10/2026

- **Mã:** `THU-05`, `QLY-08`, `QLY-03`, `NAP-01`, `NAP-04`, `QLY-05` (bổ sung tiêu chí, prefix cũ, không nghỉ hưu mã).
- **Vì sao:** trước khi code #24, chủ dự án + AI bàn nghiệp vụ để tránh app web và tool đá nhau khi cùng một hồ sơ bị sửa/xóa từ 2 phía; đồng thời chốt UX cho dễ dùng.
- **Nguyên tắc bàn giao (TDD §7.5 mới):** mốc "Nạp" là điểm chuyển quyền sở hữu. **Trước nạp** (`pending`) app web làm chủ (collector thêm/sửa/xóa); **sau nạp** (`imported`) tool/CSDT làm chủ, bản ghi app web **đóng băng** (chỉ xem). Phân biệt rõ 2 nút xóa HV đã nạp: **"Xóa hẳn" (QLY-03)** = bỏ luôn, nạp lại phải nhập lại ở app (bản VPS vẫn `imported` lịch sử — Q1); **"Gỡ về chờ nạp" (QLY-08)** = `imported→pending`, nạp lại không nhập lại, ảnh dùng ảnh thô VPS (Q2), về `pending` thì collector sửa/xóa được tiếp (Q3).
- **Popup cảnh báo + hướng dẫn** (copy impeccable, tái dùng panel xác nhận 2 bước + Banner sẵn có): THU-05 (xóa hồ sơ chờ nạp + chú thích khi đã nạp), QLY-08 (gỡ về chờ nạp + banner "đồng bộ máy chủ lỗi, thử lại"), QLY-03 ("Xóa hẳn" tách bạch với "Gỡ về chờ nạp").
- **"Dùng lại ảnh gốc"** (TDD §9.1): AnhModal thêm prop `anhGoc` + nút quay về ảnh nguyên bản (bỏ chỉnh sửa) — NAP-04 là ảnh thô VPS, QLY-05 là ảnh `.jp2` đang lưu; ẩn nút khi không có nguồn.
- **Redesign màn Nạp lô (NAP-01, TDD §10.5):** trạng thái sẵn sàng mỗi dòng (`✔ Sẵn sàng`/`⚠ Thiếu…`), "Chọn tất cả sẵn sàng", drawer "Chuẩn bị" (bỏ cột cố định), dialog nạp 3 pha (xác nhận → tiến độ → báo cáo + "Nạp lại lỗi"), nút "Xem trong DB". Thuần client, không endpoint nạp mới.
- **Đã sửa:** PRD (6 story thêm "Done khi") · TDD §7.2/§7.5/§9.1/§10.5 + Changelog v2.9 · `ui-demo/SCREENS.md` (wireframe Nạp lô + ghi chú AnhModal).
- **Chưa code** — vào BUILD-PLAN task mới (`/kehoach` bổ sung). Code lúc làm UI chạy skill `impeccable`.

## #25 — Sửa nhãn trạng thái VPS trong PRD: `done` → `imported` · 03/10/2026

- **Mã:** `QLY-08`, `THU-05` (sửa nhãn trong story đã có, prefix cũ, không nghỉ hưu mã).
- **Vì sao:** review TDD #24 (Điểm 1) phát hiện PRD gọi trạng thái bản ghi VPS là `done`, nhưng DB thật (`server/db/init.sql:28`) chỉ định nghĩa `pending/importing/imported/deleted` và TDD dùng `imported`. Người code đọc PRD thấy `done` sẽ đi tìm trạng thái không tồn tại, hoặc map nhầm sang staging local `nap_xong` → hỏng guard "chỉ xóa khi chưa nạp".
- **Đã sửa:** PRD `[THU-05]` Done khi + Edge case, `[QLY-08]` Steps bước 3 — 3 chỗ `done` → `imported`. Giữ nguyên `nap_xong` (staging local của tool, không phải trạng thái VPS).
- **Không chạm:** TDD (đã đúng `imported` từ v2.7/2.8), màn hình, code.
- **Hồ sơ:** biên bản `docs/tdd-review-03-10-2026.md`.

- **Mã:** `QLY-08` (MỚI), `THU-05` (MỚI), `NAP-01` (mở rộng). Prefix cũ, không nghỉ hưu mã.
- **Vì sao:** buổi verify #22, chủ dự án nêu 2 nhu cầu đồng bộ chưa có:
  - Nạp nhầm khóa → muốn **gỡ HV ra và trả về danh sách chờ nạp** (nạp lại đúng khóa), VPS cập nhật theo, ảnh vẫn hiện. Nút "Xóa" hiện tại chỉ bỏ hẳn ở CSDT, không trả về.
  - Collector gửi nhầm ở app web → muốn **xóa hồ sơ đã gửi**, và tool kéo về thì hồ sơ đó **biến mất khỏi hàng chờ**.
- **Chốt (chủ dự án, 02/10/2026):**
  - **QLY-08** là nút **RIÊNG** ("Gỡ về chờ nạp"), **giữ "Xóa"** để bỏ hẳn hồ sơ rác/trùng. Chỉ khóa **chưa BC1** (BC1 cấm như QLY-03). HV đã có GPLX → FK chặn. Bản ghi VPS đã dọn PII → báo không gỡ được.
  - **Nâng cấp server VPS**: thêm đường `tra-ve-cho-nap` (imported→pending, gỡ ma_dk). Ảnh khi về chờ nạp dùng **ảnh thô còn trên VPS** (không chuyển ngược .jp2).
  - **THU-05**: chỉ xóa hồ sơ **chưa nạp** (`pending`); **soft-delete** trên VPS (trạng thái `deleted` + audit_log, giữ vết); phân quyền **collector của mình / admin bất kỳ**.
  - **NAP-01**: "Kéo về từ VPS" đồng bộ **bỏ** dòng staging `pending` đã thành `deleted` trên VPS.
- **Đã sửa:** PRD +story `QLY-08` (nhóm QLY) · +story `THU-05` (nhóm THU) · `NAP-01` +Done khi (đồng bộ xóa, hạ ✅→⏳). TDD §4.3 +DELETE hồ sơ · §4.4 +tra-ve-cho-nap · §7.1 +2 chuyển trạng thái · §11.7 mới · §6 +nút Xóa app web · Changelog 2.7. SCREENS +2 quyết định UX (lượt 15, không dựng màn).
- **Hạ trạng thái:** `NAP-01` ✅→⏳ (thêm đồng bộ xóa — phần cũ vẫn đúng, story quay lại hàng đợi).
- **Code sẽ đụng:** **server VPS** `server/app` (endpoint `DELETE /api/ho-so/:uuid` soft-delete + `POST /api/nap/:uuid/tra-ve-cho-nap` + kéo trả tập uuid đã deleted) · **tool** `tool/app/vps.py` (hàm gọi mới) + `tool/app/routers/hoso.py` (`go-ve-cho-nap`) + `tool/app/nap.py` (staging: về pending / đồng bộ bỏ deleted) + `tool/webui/.../TraCuuDB.tsx` (nút Gỡ) · **app web** `webapp/src` (`DaGui` nút Xóa). Dùng lại trạng thái `deleted` + `audit_log` sẵn có — không bảng mới.
- **Còn nợ:** `/reviewtdd` (TDD đổi API + nghiệp vụ + state machine VPS) · `/kehoach` bổ sung (task mới đụng 3 nơi: server VPS + tool + app web) · code · verify thật.
- **Không đụng:** schema DB CSDT (chỉ đọc/xóa qua SP có sẵn) · bảng VPS mới (tái dùng trạng thái `deleted`).

---

## #23 — Sửa UX quản lý ảnh + nhãn nút (phát hiện khi verify #22) · 02/10/2026

- **Mã:** `NAP-04` (sửa), `QLY-05` (sửa), `QLY-06` (đổi nhãn). Không thêm/nghỉ hưu mã.
- **Vì sao:** buổi verify #22 trên máy CSDT, chủ dự án gặp 3 vướng ở phần ảnh:
  - **Chỉnh ảnh xong không xem lại được + mở lại phải chỉnh từ đầu:** sau "Dùng ảnh này", khung ảnh chỉ hiện **icon check** (không hiện ảnh thật), và "Mở trình chỉnh ảnh" lần sau nạp lại **ảnh thô VPS** thay vì ảnh đã chỉnh. Kỳ vọng đúng: xem lại được ảnh vừa chỉnh + mở ra chỉnh tiếp trên ảnh mới nhất.
  - **Dễ tưởng đã lưu ở bước "Xử lý ảnh":** nút áp dụng ("Dùng ảnh này") mờ (viền) + nhãn không rõ là bước lưu → operator dừng ở "Xử lý ảnh", ảnh chưa vào hồ sơ.
  - **Nhãn nút "Mở khóa khác" (QLY-06) gây hiểu nhầm** là *chuyển* HV sang khóa khác (nguy hiểm với khóa đã báo cáo) — thực chất nó **tạo hồ sơ MỚI ở khóa khác hạng, giữ hồ sơ cũ** (học thêm hạng).
- **Chốt (chủ dự án, 02/10/2026):**
  - Giữ **bản xem trước PNG** (backend `/local/anh/xu-ly` đã trả ở field `preview`) cạnh `jp2` trong nháp → khung ảnh hiện **ảnh đã chỉnh**; mở lại trình chỉnh ưu tiên **ảnh đã chỉnh gần nhất**. Lý do dùng PNG: `.jp2` trình duyệt không render trực tiếp.
  - Nút áp dụng ảnh để **nổi bật (nút đặc màu chính)** + badge kết quả ghi rõ *"đã xử lý — bấm để áp dụng"*.
  - Nút đổi nhãn **"Tạo thêm hồ sơ ở khóa học khác hạng"**, **giữ hiển thị cả ở khóa đã BC1** (không đụng báo cáo cũ) — phân biệt với "Đổi khóa" (QLY-02, chuyển cùng hạng, đã ẩn khi BC1).
  - Lưu ý nghiệp vụ: ở **tab Nạp**, "Dùng ảnh này" chỉ đưa ảnh vào **nháp trong trình duyệt**; ảnh chỉ thật sự ghi khi bấm "Nạp HV vào khóa".
- **Đã sửa:** PRD `NAP-04` (+3 Done khi, hạ ⏳) · PRD `QLY-05` (+Done khi, hạ ⏳) · PRD `QLY-06` (nhãn nút + giữ ở BC1, hạ ⏳) · TDD §9.1 ghi chú giữ `preview` + Changelog 2.6 · SCREENS +2 quyết định UX (lượt 14, không dựng màn).
- **Hạ trạng thái:** `NAP-04` ⚠️→⏳ · `QLY-05` 🔄→⏳ · `QLY-06` ⚠️→⏳ (yêu cầu UI đổi — code cũ chạy đúng nhưng phần UI phải làm lại, story quay lại hàng đợi).
- **Code sẽ đụng:** `tool/webui/src/components/AnhModal.tsx` (nút áp dụng nổi bật + nhãn; trả kèm `preview`) · `tool/webui/src/pages/tool/NapHoSo.tsx` (lưu `preview` vào `nhap[uuid]`, khung ảnh hiện preview, `anhBanDau` ưu tiên preview) · `tool/webui/src/pages/tool/TraCuuDB.tsx` (hiện ảnh mới sau lưu + mở lại chỉnh tiếp; đổi nhãn nút "khóa khác") · có thể `lib/api.ts` (kiểu trả `xuLyAnh`).
- **TÁCH riêng (KHÔNG trong đợt này):** ❓ D — gỡ HV khỏi khóa → trả về **chờ nạp** + cập nhật VPS + giữ ảnh. Tính năng mới lớn (đụng DB CSDT + VPS), bàn `/capnhat` riêng.
- **Không đụng:** backend xử lý/ghi ảnh (đã trả `preview` sẵn) · DB đích · server VPS · app web.

---

## #22 — Mở rộng quản lý ảnh Tra cứu DB + bảo toàn Báo cáo 1/2 · 02/10/2026

- **Mã:** `QLY-01` (mở rộng), `QLY-03` (sửa), `QLY-05` (sửa + 🐛), `QLY-07` (MỚI), `NAP-01` (mở rộng).
- **Vì sao:** chủ dự án muốn xem/sửa ảnh HV đã nạp ngay ở Tra cứu DB (hiện chỉ hiện chữ "Đã có/Thiếu ảnh", KHÔNG render ảnh) + đổi nền trắng hàng loạt cho ảnh cũ. Khi tra schema DB cũ (`DBcu/DBcu30092026.sql`) để kiểm tác động Báo cáo 1/2, phát hiện **bug nghiêm trọng** ở luồng thay ảnh.
- **🐛 Bug phát hiện (QLY-05, có sẵn trong code task 27):** `ghi_anh_update` (dùng chung NAP-05/QLY-05) set cứng `TT_XuLy='03'`. Mà `usp_BaoCao2_DSHS` lọc HV theo `TT_XuLy in ('11'..'19')` → **thay ảnh cho HV đã vào Báo cáo 1/2 làm HV rơi khỏi Báo cáo 2** ("HV không có trong BC1"). Liên kết HV↔báo cáo: `NguoiLX_HoSo.MaBC1`(FK→`BaoCaoI`)/`MaBC2`, `BaoCaoII.MaBCI`→`BaoCaoI`.
- **Chốt luật (khóa đã BC1):** thay ảnh/đổi nền **ĐƯỢC** (ảnh không nằm trong nội dung báo cáo) nhưng **phải giữ `TT_XuLy`**; sửa thông tin nhân thân **CHẶN** (đã chặn sẵn, BR-012); xóa HV **CHẶN ở backend** (mới).
- **Nhóm 1 (làm trước):**
  - QLY-01: hiện ảnh chân dung + đường dẫn khi xem HV (backend transcode `.jp2`→PNG) · avatar mỗi dòng lưới (thumbnail + cache; chưa ảnh → icon người) · cảnh báo khi DB có path mà mất file · thống kê đầu khóa (tổng/thiếu ảnh/BC1) · nút đổi-khóa/xóa nhanh ra lưới · click ảnh → trình chỉnh.
  - QLY-05: 🐛 giữ `TT_XuLy` khi HV đã Báo cáo (`'11'`–`'19'`), chỉ nâng `'01/02'→'03'` khi chưa BC · mở trình chỉnh ảnh từ Tra cứu DB.
  - QLY-03: chặn xóa HV khóa BC1 ở BACKEND (`usp_NguoiLX_Delete`), không chỉ ẩn nút UI.
  - NAP-01: "Bỏ khỏi hàng đợi" (xóa dòng 🟢 khỏi `staging.sqlite`, KHÔNG đụng prod — tách bạch "Xóa khỏi DB") + "Nạp lại nhanh" dòng 🔴.
- **Nhóm 2 (story mới QLY-07):** đổi nền trắng cả khóa — chạy nền + thanh tiến độ · sao lưu `_BACKUP` trước ghi đè · mặc định "chỉ ảnh chưa trắng" · giữ `TT_XuLy` (nếu không, cả khóa đã BC2 biến mất cùng lúc).
- **Đã sửa:** PRD `QLY-01`/`QLY-03`/`QLY-05` (+Done khi, hạ ⏳) · PRD `NAP-01` (hạ ⏳) · PRD +story `QLY-07` · TDD §7.2 + §11.1 + §11.3 + §11.5 + §11.6 mới + Changelog 2.4 · SCREENS màn #12/#14/#15 + 3 quyết định UX + wireframe.
- **Hạ trạng thái:** `QLY-01` ⚠️→⏳ · `QLY-03` ⚠️→⏳ · `QLY-05` ⚠️→⏳ · `NAP-01` ✅→⏳ (mở rộng yêu cầu — code cũ vẫn đúng nhưng story quay lại hàng đợi).
- **TREO (chưa quyết, KHÔNG vào PRD):** ❓ sửa thông tin nhân thân *trước* khi nạp trong tool — bẫy "Kéo lại từ VPS" đè. Nghiêng về KHÔNG làm (giữ sửa trên app web). Chờ chủ dự án quyết.
- **Code sẽ đụng:** `tool/app/nap.py` (`ghi_anh_update` giữ `TT_XuLy`; +xóa staging `keo_ve`) · `tool/app/routers/hoso.py` (`xoa_ho_so` chặn BC1; +endpoint phục vụ ảnh + thumbnail) · `tool/app/image.py` (transcode `.jp2`→PNG) · `tool/webui/src/pages/tool/TraCuuDB.tsx` + `NapHoSo.tsx` + `lib/api.ts` · màn QLY-07 mới.
- **Còn nợ:** `/reviewtdd` (TDD đổi API §11.1 + nghiệp vụ §11.3/§11.5/§11.6) · `/kehoach` bổ sung (rework QLY-01/03/05 + NAP-01 + task QLY-07) · `/prototype-next` dựng màn #14/#15 · code · chủ dự án quyết mục ❓ treo.
- **Không đụng:** schema DB đích (chỉ đọc; `_BACKUP` là thư mục file) · server VPS · app web.

---

## #21 — Zoom trình chỉnh ảnh: thu nhỏ dưới cỡ gốc + lăn chuột + thang giữa · 02/10/2026

- **Mã:** `NAP-04` — tinh chỉnh zoom AnhModal (phản hồi test), không story mới.
- **Vì sao:** user test — (1) zoom lấy ảnh ban đầu làm mốc NHỎ nhất, không thu nhỏ thêm được; (2) muốn lăn chuột để phóng/thu; (3) thang zoom nên mặc định ở giữa (trái thu nhỏ, phải phóng to).
- **Mới:** thang zoom đổi sang **mũ `3^t`, t ∈ [−1, 1]** — `t=0` (GIỮA) = cỡ gốc 1×, `t=−1` ≈ 1/3× (thu nhỏ), `t=+1` = 3× (phóng to). Slider nhãn "Thu nhỏ ← → Phóng to", mặc định giữa. Thêm **lăn chuột** (onWheel) trên khung: lăn xuống thu nhỏ, lăn lên phóng to. Vùng lộ khi thu nhỏ/kéo → nền trắng (canvas).
- **Đã sửa:** PRD `NAP-04` (Done khi) · TDD §9.1 + Changelog 2.3.
- **Code sẽ đụng:** `tool/webui/src/components/AnhModal.tsx` (state `mucZoom` thay `zoom`, `datZoom`, `onWheel`, slider −1..1).

## #20 — Nâng cấp trình chỉnh ảnh: xoay + khung mẫu + tăng tốc xóa phông · 02/10/2026

- **Mã:** `NAP-04` — nâng cấp UX trình chỉnh ảnh (AnhModal), không story mới. NAP-04 ⚠️→⏳.
- **Vì sao:** user test tool phản ánh — (1) chưa xoay ảnh linh hoạt (mới kéo di chuyển/zoom), (2) chưa có khung chân dung mẫu để biết căn mặt, (3) đổi nền trắng chạy khá lâu.
- **Mới — Grab tự do 4 hướng:** nới `clamp` (giữ tối thiểu 1/4 ảnh trong khung) để kéo được cả trái/phải lẫn lên/xuống. Trước đây `clamp` ghim ảnh phủ kín khung nên ở zoom gốc một trục (rW=FW hoặc rH=FH) bị khóa → chỉ kéo được 1 chiều (user phản ánh). Vùng lộ khi kéo → nền trắng ở canvas.
- **Mới — Xoay ảnh:** nút **−90°/+90°** + thanh **tinh chỉnh độ nghiêng** (vài độ) để làm thẳng mặt. Xoay **client-side (canvas)** trước khi gửi backend crop; box tính trong hệ ảnh đã xoay.
- **Mới — Khung chân dung mẫu:** overlay mờ chồng lên khung crop (ô-van đầu + đường căn mắt/cằm) để operator biết đặt mặt. **Chỉ là hướng dẫn, KHÔNG dính vào ảnh `.jp2` xuất ra.**
- **Tăng tốc xóa phông (phương án A — user chốt):** bật **warm-up rembg lúc khởi động tool** = **bỏ `TOOL_SKIP_WARMUP=1` khỏi `tool-start.bat`**. Ảnh đầu chỉ chờ nạp model 1 lần lúc mở tool, ảnh sau <5s (TDD §9.2). **GIỮ model u2net** (không đổi chất lượng, không dùng model nhẹ). `TOOL_SKIP_WARMUP` vẫn giữ trong test (conftest) để khỏi tải model ~170MB khi chạy test.
- **Đã sửa:** PRD `NAP-04` (Steps + Done khi + hạ ⏳) · TDD §9.1 (xoay + khung mẫu) + §9.2 (không tắt warm-up) + Changelog 2.2.
- **Còn nợ:** code (tool/webui + tool-start.bat) — `/tieptheo` nhặt NAP-04 (⏳) code lại.
- **Code sẽ đụng:** `tool/webui/src/components/AnhModal.tsx` (state xoay + transform + overlay khung mẫu + xoay canvas trước khi gửi; cân nhắc gửi ảnh đã xoay thay vì chỉ box) · `tool-start.bat` (bỏ dòng `set TOOL_SKIP_WARMUP=1`). Backend `tool/app/image.py`/`routers/anh.py` nếu chọn truyền ảnh-đã-xoay (multipart) thay vì box — quyết lúc code.

## #19 — Tận dụng dữ liệu kéo về VPS (tự điền địa chỉ + nạp ảnh sẵn) · 02/10/2026

- **Mã:** `NAP-03`, `NAP-04` — tinh chỉnh hành vi ở luồng kéo-về (chế độ Nạp), không story mới.
- **Vì sao:** user test tool phản ánh — hồ sơ kéo từ VPS về đã có địa chỉ (`noi_tt_raw`) và ảnh thô, nhưng tool vẫn bắt **gõ lại** địa chỉ vào ô map và **chọn lại file ảnh** trong trình chỉnh. Lãng phí dữ liệu đã có. TDD §8.1 (map từ "địa chỉ text") + §9.1 ("Ảnh thô từ VPS → khung crop") vốn đã định hướng tận dụng — code chưa hiện thực đủ.
- **Mới — NAP-03:** chọn hồ sơ kéo về → tự tách `noi_tt_raw` ("…, Xã X, Huyện Y, Tỉnh Z") theo dấu phẩy + từ khóa (Tỉnh/TP→tỉnh, Quận/Huyện/Thị xã→huyện, Phường/Xã/Thị trấn→xã, phần dư→Chi tiết) → **điền sẵn** 3 ô map; operator bấm "Chuyển đổi sang xã mới". Tách là best-effort client (không gọi DB), **luôn cho sửa**; rỗng/không rõ → gõ tay như cũ. Giữ nguyên nút Chọn tay + map cốt lõi (đã verify 3321/3321).
- **Mới — NAP-04:** ảnh thô đã kéo về nạp **thẳng vào trình chỉnh** (AnhModal) làm ảnh crop ban đầu — căn 3:4 + đổi nền ngay, không bắt chọn lại file; vẫn cho chọn file khác để thay. `AnhModal` nhận **prop ảnh khởi tạo TÙY CHỌN** → QLY-05/QLY-06 (cũng dùng AnhModal) mở không-ảnh-sẵn vẫn chạy như cũ.
- **Đã sửa:** PRD `NAP-03`/`NAP-04` (Done khi + hạ trạng thái ⏳) · TDD §8.1 (bước tự tách) + §9.1 (nạp ảnh sẵn) + Changelog 2.1.
- **Còn nợ:** code (tool/webui) — `/tieptheo` sẽ nhặt NAP-03/NAP-04 (đang ⏳) để code lại phần này.
- **Code sẽ đụng:** `tool/webui/src/components/AddressCombo.tsx` (nhận địa chỉ gốc + điền sẵn + hàm tách) · `tool/webui/src/components/AnhModal.tsx` (nhận ảnh khởi tạo tùy chọn) · `tool/webui/src/pages/tool/NapHoSo.tsx` (truyền `noi_tt_raw` + ảnh đã tải vào 2 component).

## #18 — Quản lý tài khoản app web + 5 sửa UI · 02/10/2026

- **Mã:** `HTG-04` (SHOULD), `HTG-05` (MUST), `HTG-06` (MUST) — thêm vào nhóm HTG.
- **Vì sao:** chủ dự án cần tự vận hành tài khoản (tạo nhân viên, đổi mật khẩu) + lấy API key tool khỏi phải SSH; đồng thời phản ánh vài lỗi khung UI.
- **HTG-04 — Admin xem API key VPS:** endpoint `GET /api/admin/tool-key` (chỉ admin) + khối ở màn Tài khoản (che/Hiện/Sao chép). **Đánh đổi bảo mật đã ghi ở PRD** (khóa dùng chung, lộ phải xoay). Không đổi `require_tool_key`, không xoay key.
- **HTG-05 — Quản lý tài khoản nhân viên:** màn admin (danh sách + phân trang) · tạo (họ tên/username/vai trò/mật khẩu ban đầu) · reset mật khẩu · khóa/mở (`is_active`, **không xóa cứng** để giữ dấu vết PII). Chặn admin tự khóa mình. ("Buộc đổi mật khẩu lần đầu" — **bỏ** theo chủ dự án 02/10.)
- **HTG-06 — Tự đổi mật khẩu:** khối ở màn Tài khoản (mọi vai trò); kiểm mật khẩu hiện tại trước khi đổi.
- **5 sửa UI (polish, không phải story):**
  - UI-1 Header cố định, hết giật — khóa khung = chiều cao màn hình, chỉ pane cuộn (nguyên nhân cũ: `h-[100dvh]` nhảy theo thanh địa chỉ; desktop thiếu header).
  - UI-2 Khung desktop cao ổn định — bỏ co theo nội dung (`lg:h-auto` → chiều cao tối thiểu đầy viewport).
  - UI-3 Phân trang list 20/trang (app web `DaGui` server-side; tool list client-side), đổi cỡ 20/50/100.
  - UI-4 Tool giống app Windows — master–detail: list trái cuộn, panel info+ảnh phải **ghim**; màn hẹp xếp dọc.
  - UI-5 Kính lúp đè chữ hint (cả 2 app) — gốc: `.field-input` đặt `padding` ngoài `@layer` nên thắng tiện ích `pl-*` của Tailwind → padding trái bị bỏ. Fix: bọc class component vào `@layer components`.
- **Chạm story đã xong:** UI-3 thêm phân trang cho `THU-02` (✅) và `QLY-01` (⚠️); UI-1/2/5 chạm khung chung (`HTG-01`). Code sửa trong cùng đợt này → cập nhật trạng thái sau khi build xong, không để ✅ sai.
- **Đã code (02/10):** server HTG-04/05/06 (`admin.py` tool-key · `admin_users.py` list/reset/chặn tự khóa · `auth.py` đổi mật khẩu) + 13 test (server 82 pass); webapp (màn Tài khoản: đổi mật khẩu + API key admin + link quản lý · màn Quản lý tài khoản: list phân trang/tạo/reset/khóa) + route admin-only; UI-5 fix kính lúp (`@layer components`, cả 2 app).
- **UI đã xong (02/10):** UI-1/2 (`AppLayout`/`ToolLayout` 100svh, header/toolbar đứng yên, khung cao ổn định) · UI-3 (`PhanTrang` mỗi app; `DaGui` + lưới HV `TraCuuDB` + list Nạp) · UI-4 (`NapHoSo` ghim detail+ảnh theo màn hình, bỏ 720px cứng) · UI-5 (`@layer components`).
- **Đã deploy (02/10):** push `main` → CD build + deploy VPS; kiểm live: `/api/admin/tool-key` + `/api/auth/doi-mat-khau` trả 403 khi chưa đăng nhập (endpoint có, gác đúng). Chờ user verify trên giao diện.
- **Bỏ khỏi phạm vi (02/10):** "buộc đổi mật khẩu lần đầu" — chủ dự án không cần; không thêm cột `must_change_password`.

---

## #17 — QLY-01 lát 2: sửa hồ sơ thu hẹp còn nhân thân · 02/10/2026

- **Mã:** `QLY-01`. Không thêm/bớt story — thu hẹp phạm vi lát 2 cho an toàn dữ liệu (chủ dự án duyệt live 02/10).
- **Vì sao:** soi 3 SP sửa của app cũ trên DB thật trước khi code: `usp_NguoiLX_HoSo_Update` **ghi đè toàn bộ 65 cột** của `NguoiLX_HoSo` (gồm kết quả thi lý thuyết/hình/đường, liên kết BC1/BC2, đường dẫn ảnh), mà SP đọc-để-sửa `usp_NguoiLX_HoSo_Get_Sua_HS` **chỉ trả một phần** → nếu tool đụng bảng hồ sơ mà truyền thiếu/sai một cột là **xóa trắng kết quả thi của HV thật** trên prod.
- **Chốt phạm vi:** QLY-01 lát 2 **chỉ sửa thông tin nhân thân** (bảng `NguoiLX`): họ tên, ngày sinh, giới tính, số căn cước, địa chỉ thường trú (chi tiết). Tất cả nằm ở `NguoiLX` → qua **1 SP `usp_NguoiLX_Update`**, KHÔNG đụng `NguoiLX_HoSo`.
  - Ảnh → `QLY-05` (nạp/thay ảnh). Đổi khóa → `QLY-02`. Kết quả thi/báo cáo → do app cũ quản, tool không sửa.
- **Ghi an toàn:** `usp_NguoiLX_Update` cũng ghi đè 22 cột → trước khi ghi, **đọc lại full bản ghi `NguoiLX` hiện tại** rồi chỉ chồng 5 trường user sửa (giữ nguyên quốc tịch, nơi cấp CCCD, ghi chú, mã DVHC, người/ngày tạo, nơi cư trú...). Đọc + ghi trong 1 kết nối.
- **BR-012:** khóa đã lập BC1 → UI chỉ cho xem (không hiện nút Sửa); backend kiểm lại khi ghi → 409.
- **Đã làm:** API `GET /local/ho-so/chi-tiet` + `POST /local/ho-so/sua` (`tool/app/routers/hoso.py`) · UI nút Sửa + form nhân thân trong modal Tra cứu DB (`TraCuuDB.tsx`) · tool **101 pytest** + webui **19 vitest** + build sạch.
- **Chờ verify prod (bạn chạy):** sửa 1 HV thật ở khóa chưa BC1 → mở app cũ đối chiếu đúng · thử khóa đã BC1 → không sửa được.
- **Không đụng:** `usp_NguoiLX_HoSo_Update`, bảng `NguoiLX_HoSo`, ảnh, schema, server/app web.

---

## #16 — Kiểm DB thật chốt thiết kế QLY-06 (nạp khác khóa/khác hạng) · 01/10/2026

- **Mã:** `QLY-06`. Không đổi phạm vi — chỉ kiểm DB thật (chỉ đọc) để gỡ ẩn số, chốt thiết kế.
- **Vì sao:** QLY-06 còn nợ: SP `usp_QuangLA_PM4_ThuNhanHS_ThemMoiCapNhat` khi nạp người đã có trong DB thì **tái dùng bản ghi người cũ** hay **tạo người trùng**? (quyết định cả giải pháp).
- **Đã chạy (qua kết nối tool, chỉ đọc):**
  - **Q1 `sp_helptext`:** nhánh `IF @p_MaDK IS NULL` → `@v_MaDK = dbo.CreateNewMaDK(...)` → **INSERT NguoiLX mới** + INSERT NguoiLX_HoSo + NguoiLXHS_GiayTo. Nhánh có `@p_MaDK` → UPDATE 3 bảng. Câu kiểm `-2` trùng CMT dùng `lx.MaDK <> @p_MaDK` nên **khi nạp mới (`@p_MaDK=NULL`) không bắt trùng** (khớp bẫy đã biết — giữ check server-side).
  - **Q2 dữ liệu:** ≥20 HV có >1 khóa (nhiều người 5–8 khóa), mỗi khóa 1 hồ sơ, **chung SoCMT**.
- **Kết luận:** mô hình = **mỗi đăng ký 1 dòng NguoiLX + NguoiLX_HoSo, MaDK riêng, chung SoCMT**; nhiều dòng cùng SoCMT là **đúng thiết kế**, không phải trùng. → Nạp khác khóa/khác hạng = **nạp mới bình thường** (tạo MaDK mới), KHÔNG cần bước nối người cũ. QLY-06 chỉ cần thao tác tool "từ HV đã có → mở hồ sơ khóa mới" (điền sẵn + nạp mới). **Gỡ 📝 Draft → ⏳ Todo.**
- **Đã sửa:** PRD `QLY-06` (căn cứ DB + Done khi + gỡ Draft) · BUILD-PLAN (thêm task, bỏ khỏi Chờ chốt).
- **Không đụng:** DB (chỉ đọc, không ghi) · server · code · schema.

---

## #15 — Ảnh app web: 2 nút chụp/chọn-từ-máy + phóng to popup · 01/10/2026

- **Mã:** `THU-02`. Sửa UX phần ảnh, không thêm story. UI thuần client.
- **Vì sao:** chủ dự án hỏi — màn ảnh đang ép `capture="user"` nên điện thoại chỉ mở camera, **không chọn được ảnh có sẵn trong máy/thư viện**; và ảnh chân dung ở chi tiết hiện nhỏ (~80px), **bấm không phóng to được**.
- **Chốt (bộ chọn):**
  1. **2 nút nguồn ảnh:** "Chụp ảnh" (giữ `capture` → camera trực tiếp) và "Chọn từ máy" (bỏ `capture` → file/thư viện). Áp ở **màn chụp ảnh (Quet/ChupAnhGui)** + **đổi ảnh hồ sơ Chờ nạp (DaGui/ChiTiet)**. Chủ dự án chọn mở cả 2 lối (không ép camera cứng).
  2. **Phóng to ảnh:** bấm ảnh chân dung ở chi tiết → **AnhLightbox** mở toàn màn, bấm ngoài đóng.
- **Kỹ thuật:** thuần client `Quet.tsx` + `DaGui.tsx` (component `AnhLightbox` tái dùng `taiAnhCuaToi`). Không thêm endpoint, không đụng server/schema. Test webapp 24 pass, typecheck + build sạch.
- **Không đụng:** server, schema, tool, luồng nạp.

---

## #14 — Redesign UX nhập liệu app web (impeccable) · 01/10/2026

- **Mã:** `THU-01`, `THU-02`. Sửa giao diện/luồng nhập, không thêm story.
- **Vì sao:** test thật, chủ dự án thấy màn nhập liệu desktop chưa thân thiện cho nhập tay: ô CMND cũ ít dùng gây rối, ô ngày khó nhập, 2 nút xếp dọc dễ bấm nhầm, thiếu phím tắt.
- **Chốt (hỏi bộ chọn):**
  1. **Ẩn ô "Số CMND cũ"** — vẫn tự lưu CMND cũ từ QR nếu có (không mất dữ liệu, tool nạp vẫn dùng). Không bỏ cột DB/field gửi.
  2. **Ô ngày** (ngày sinh, ngày cấp) — **gõ tay dd/mm/yyyy + nút lịch** bấm chọn; vẫn nhập được **năm-only** (CCCD có HV chỉ có năm sinh → yyyy0000).
  3. **Desktop:** tách vị trí 2 nút ("Tiếp tục — chụp ảnh" vs "Lưu & nhập hồ sơ tiếp") tránh bấm nhầm + bố cục form thân thiện nhập tay + **phím tắt** (Enter/Ctrl+Enter, autofocus, tab order).
  4. **Content/anti-slop:** rà chữ hiển thị tự nhiên, không lộ mã story (đã bỏ "(HTG-01)" ở màn đăng nhập).
  5. **Cảnh báo trùng (THU-04):** giữ hiển thị **tên đầy đủ** người gửi (chủ dự án chốt NV xem được của nhau).
- **Hệ quả trạng thái:** `THU-01`/`THU-02` đang ⏳ (từ #13) — giữ ⏳, gộp phần này vào cùng đợt code.
- **Kỹ thuật:** thuần client webapp (`Quet.tsx` + component ô ngày tái dùng; `DaGui.tsx` ô ngày sửa). Không đụng server/schema (CMND cũ vẫn gửi như cũ; cột DB giữ nguyên).
- **Đã sửa:** PRD THU-01/THU-02 (AC UX) + Changelog v2.7 · TDD §6.6 (ghi UX) · SCREENS lượt 11.
- **Đã code (01/10, deployed):** `ODate.tsx` (ô ngày: gõ tay + nút lịch `showPicker` + **auto-mask tự chèn "/"** khi gõ số, giữ năm-only) dùng ở `Quet.tsx` + `DaGui.tsx`; ẩn ô CMND cũ (giữ giá trị QR); desktop form 2 cột + 2 nút tách hai bên + phím tắt (autofocus/Enter/Ctrl+Enter); +icon calendar/edit/chevronLeft. Verify Playwright 1440+375. Test webapp 24 (+4 maskNgay). impeccable detect sạch (trừ góc khung ngắm camera — cố ý).
- **Không đụng:** server, schema, tool, luồng nạp.

---

## #13 — App web: nhập liên tiếp + badge thiếu ảnh + cảnh báo trùng + (Draft) nạp khác khóa · 01/10/2026

- **Mã:** `THU-01`, `THU-02` (sửa) · `THU-04` (thêm, SHOULD) · `QLY-06` (thêm, 📝 Draft — còn nợ kiểm DB).
- **Vì sao:** chủ dự án test thật nêu 4 ý — (1) nhập liên tiếp không muốn bắt chụp ảnh từng hồ sơ; (2) cần đánh dấu + gom hồ sơ thiếu ảnh để chụp bù; (3) app web nhập chưa cảnh báo trùng căn cước; (4) muốn nạp lại cùng học viên vào khóa khác, khác hạng.
- **Chốt (hỏi từng câu, user duyệt):**
  1. **Lưu & nhập hồ sơ tiếp** (THU-01/THU-02): màn preview (dùng cho cả quét QR lẫn nhập tay) thêm nút **"Lưu & nhập hồ sơ tiếp"** → gửi **không kèm ảnh** → **toast "Đã gửi ✓"** (bỏ màn kết quả) → về màn chọn cách nhập. *Phương án A* (toast) đã chọn, loại B (giữ màn kết quả).
  2. **Badge "Thiếu ảnh" + bộ lọc** (THU-02): "Hồ sơ đã gửi" hiện badge cho hồ sơ chưa ảnh + bộ lọc gom hồ sơ thiếu ảnh; chụp bù qua nút "Thêm ảnh" (Chờ nạp) đã có.
  3. **Cảnh báo trùng CCCD app web** (THU-04, SHOULD): app hỏi VPS xem CCCD đã có hồ sơ `pending`/`importing` trong hàng đợi CSDT chưa → **cảnh báo mềm, vẫn cho gửi** (*phương án A*, loại B chặn cứng / C giữ nguyên). Phạm vi: cả hàng đợi CSDT (mọi nhân viên). App web **không** soi DB thật — chốt trùng thật vẫn ở NAP-06.
  4. **Nạp khác khóa/khác hạng** (QLY-06, 📝 Draft): phạm vi **cấp mới khác hạng song song** (có B thêm A1), *loại nâng hạng* (B→C/D/E — ngoài MVP). **Còn nợ kiểm DB thật** (chưa chốt thiết kế): SP tái dùng người cũ hay tạo người trùng.
- **Hệ quả trạng thái:** `THU-01` & `THU-02` đang ✅ → **hạ ⏳ Todo** (đổi giao diện màn đã dựng). `THU-04` ⏳ Todo. `QLY-06` 📝 Draft.
- **Kỹ thuật:** #1 + #2 **thuần client webapp**, không thêm endpoint. #3 thêm **1 endpoint** `GET /api/ho-so/kiem-trung?cccd=` (collector, đếm hàng đợi, loại chính uuid). Không đụng schema/tool/luồng nạp.
- **Đã sửa:** PRD THU-01/THU-02 (Done khi + hạ ⏳) + THU-04 + QLY-06 + Changelog v2.6 · TDD §4.3 (endpoint kiểm-trùng) + §6.1 (nhánh preview) + §6.6 (mới) + Changelog v2.2.
- **Đã code (01/10, chưa deploy):** server `GET /api/ho-so/kiem-trung` (THU-04, +5 test → server 67 pass) · `webapp/api.ts` `kiemTrungCccd` · `Quet.tsx` nút "Lưu & nhập hồ sơ tiếp" + toast + banner cảnh báo trùng (Preview) · `DaGui.tsx` badge "Thiếu ảnh" + bộ lọc. Typecheck + build + webapp 20 test pass.
- **Còn nợ:** deploy (push → CD) để test trực quan trên máy thật · `/reviewtdd` (TDD §4.3 thêm endpoint) · `/kehoach` bổ sung (task rework THU-01/02 + task THU-04) · review giao diện trước khi đặt story ✅ · **QLY-06: chạy 2 query kiểm DB ở máy CSDT trước khi thiết kế chi tiết**.
- **Không đụng:** schema DB/VPS · luồng nạp · tool (trừ QLY-06 sau khi chốt).

---

## #12 — Sửa UX app web sau test điện thoại thật (THU-01/THU-02) · 01/10/2026

- **Mã:** `THU-01`, `THU-02`. Sửa giao diện/luồng, không thêm story mới.
- **Vì sao:** deploy app web lên VPS (`nhaphocvien.trungtamthanhdat.com`) test trên điện thoại thật, chủ dự án thấy 6 điểm UX chưa tốt. Wireframe đã duyệt trước khi ghi sổ.
- **Chốt (6 điểm):**
  1. **Màn vào không tự mở camera** (THU-01) — cho chọn **Quét QR / Nhập tay / Tải ảnh CCCD**; camera chỉ bật khi bấm Quét.
  2. **Header logo không phải nút** (AppLayout) — bỏ nền/bo dáng nút để không nhầm là camera.
  3. **Hiện ảnh thật** (THU-02) — thumbnail ở list + chi tiết "đã gửi" thay icon xám; cần endpoint collector tải ảnh của mình.
  4. **Xem/sửa/chụp lại** (THU-02) — bấm hồ sơ đã gửi → chi tiết; còn **Chờ nạp** cho Sửa thông tin + Chụp/đổi ảnh; **Đang/Đã nạp** chỉ xem.
  5. **Layout mobile dính đáy** (THU-01/AppLayout) — `100dvh` + khung camera co giãn + bottom-nav & nút chính dính đáy, không cuộn mới thấy.
  6. **Khung bám QR** (THU-01) — dùng 4 góc `cornerPoints` của BarcodeDetector vẽ khung khóa theo mã, thay khung xanh tĩnh.
- **Hệ quả trạng thái:** `THU-01` & `THU-02` đang ✅ → **hạ ⏳ Todo** (đổi giao diện). Code quét/parse/gửi/offline/ô tìm cũ vẫn đúng, chỉ dựng lại phần vào + xem lại + ảnh.
- **Kỹ thuật:** thêm **1 endpoint** `GET /api/ho-so/:uuid/anh` (collector, kiểm `created_by` chống IDOR). Sửa/đổi ảnh dùng `PUT /api/ho-so/:uuid` + `POST .../anh` (server đã cho khi `pending`). Khung bám QR dùng `cornerPoints` (fallback qr-scanner không có → khung tĩnh).
- **Đã sửa:** PRD `THU-01`/`THU-02` (Done + Steps + Edge + hạ ⏳) + Changelog v2.5 · TDD §4.3 (endpoint) + §6.5 (mới) + Changelog v2.1 · SCREENS.md (3 quyết định UX lượt 9).
- **Còn nợ:** code webapp (Quet.tsx, DaGui.tsx, AppLayout.tsx, api.ts) + server (`GET .../anh` collector + test) · `/kehoach` bổ sung task rework (task 18/19 đã [x]) · cập nhật prototype ui-demo nếu muốn.
- **Không đụng:** schema DB/VPS · tool · luồng nạp.

---

## #11 — "Kéo về từ VPS" làm tươi hồ sơ chưa nạp (NAP-01) · 01/10/2026

- **Mã:** `NAP-01`. Thêm 1 tiêu chí "Done khi" + 1 edge case trong story có sẵn, không thêm story mới.
- **Vì sao:** Động tác kéo **không khóa** hồ sơ (khóa chỉ ở bước nạp, 15'). Nên sau khi tool đã kéo về, người thu nhận vẫn sửa được thông tin/ảnh trên app web (hồ sơ còn `pending`) → bản trong tool thành cũ mà tool **không biết**. Trước đó tool kéo lại chống trùng theo uuid (`INSERT OR IGNORE`) → **không** làm tươi bản đã kéo.
- **Chốt (phương án A — mức nhẹ):** bấm "Kéo về từ VPS" lần nữa **cập nhật lại** thông tin/ảnh mới nhất từ VPS cho các bản `keo_ve` còn trạng thái cục bộ `cho`; **giữ nguyên** bản `xong`/`loi`. Báo số hồ sơ vừa làm tươi. KHÔNG khóa-khi-kéo (đã cân nhắc "mức chặt": khóa ngay khi kéo + app web báo "đang xử lý" — loại vì nặng, dễ kẹt lô lớn, job 15' lật ngược khi kéo mà chưa nạp).
- **Hệ quả trạng thái:** `NAP-01` đang ✅ Done (phiên này) → **hạ ⏳ Todo** (yêu cầu thêm). Code ①+② cũ vẫn đúng, chỉ bổ sung làm tươi.
- **Kỹ thuật:** đổi `tool/app/nap.py` `keo_ve_upsert` từ `INSERT OR IGNORE` → UPSERT cập nhật bản `cho` (giữ `xong`/`loi` + local status), trả số bản làm tươi; `routers/nap.py` `keo_hang_doi` báo thêm số làm tươi. Không đụng VPS/app web.
- **Đã sửa:** PRD `NAP-01` (Done khi + Edge) · TDD §7.2 + Changelog v2.0.
- **Đã code (01/10):** `keo_ve_upsert` UPSERT bản `cho` trả `(mới, làm tươi)`; `keo_hang_doi` báo `lam_tuoi`; `NapHoSo.tsx` hiện "Đã kéo N mới · làm tươi M". Test tool 72 pass (+2: làm tươi bản `cho`, không đụng `xong`). NAP-01 ✅ lại — gọn trong task 20, không cần `/kehoach` bổ sung.
- **Không đụng:** schema VPS/DB · app web · server.

---

## #10 — Thêm tìm kiếm (tên không dấu + CCCD) ở tool & app web · 01/10/2026

- **Mã:** `THU-02`, `NAP-01`, `QLY-01`. Thêm tính năng trong màn có sẵn, không thêm story mới.
- **Vì sao:** Chủ dự án muốn tra nhanh học viên bằng tên (gõ không dấu cũng ra) hoặc số CCCD, ở cả tool lẫn app web. Trước đó: app web chỉ lọc theo trạng thái (không tìm); tool list tải về chưa có ô tìm; QLY-01 có tìm tên/CCCD nhưng chưa nêu "khớp không dấu".
- **Chốt (phương án A, đổi từ B):** ô tìm ở **3 chỗ** — (1) app web `Hồ sơ đã gửi`, (2) tool `list tải về` (chế độ Nạp hồ sơ), (3) tool `lưới khóa` (Tra cứu DB). Khớp theo **tên (chuẩn hóa bỏ dấu cả hai vế) hoặc số CCCD**. UX: ô tìm **đầu danh sách/lưới**; **màn hẹp thu gọn thành nút kính lúp** (bấm mới bung).
  - *Diễn biến:* hỏi phạm vi → chủ dự án chốt **B** (chỉ tool) → đổi ý ngay sau đó sang **A** (cả app web). Theo A.
- **Hệ quả trạng thái:** `THU-02` đang ✅ → **hạ ⏳ Todo** (yêu cầu đổi, phải thêm ô tìm; code gửi cũ vẫn đúng nhưng story quay lại hàng đợi). `NAP-01`, `QLY-01` đang ⏳ → chỉ thêm AC.
- **Kỹ thuật:** app web + tool list tải về lọc **phía client** trên dữ liệu đã tải (không thêm endpoint); QLY-01 lưới khóa tìm qua SP `usp_NguoiLX_HoSo_Search` (collation không phân biệt dấu hoặc chuẩn hóa tương tự). Bỏ dấu = normalize NFD + xóa dấu kết hợp.
- **Đã sửa:** PRD `THU-02`/`NAP-01`/`QLY-01` (Done khi + hạ trạng thái THU-02) · TDD §6.4 (mới) + §11.1 (note tìm) · `SCREENS.md` (quyết định UX lượt 7).
- **Còn nợ:** code 3 ô tìm (THU-02 app web, NAP-01 tool, QLY-01 tool) · cập nhật prototype ui-demo cho 3 màn (hoặc dựng trong lúc build màn thật).
- **Không đụng:** schema DB/VPS (tìm client-side hoặc qua SP sẵn có) · BUILD-PLAN số task (THU-02 task 19, NAP-01 task 20, QLY-01 task 22 — chỉ thêm việc trong task, `/kehoach` bổ sung nếu muốn ghi rõ).

---

## #9 — Bỏ ô nhập nơi cư trú khác ở app thu nhận (THU-02) · 01/10/2026

- **Mã:** `THU-02`. Đổi quy tắc nghiệp vụ nhỏ (bớt một ô nhập), không thêm/bỏ story.
- **Vì sao:** Bảng `ho_so_thu_thap` trên VPS không có cột nơi cư trú (`HoSoIn`/model chỉ có `noi_tt_raw`), và tool khi nạp tự lấy cư trú = thường trú (BR-004 / TDD §8.1). App cho nhập cư trú khác thì dữ liệu đó không gửi đi đâu được, âm thầm mất. Nghiệp vụ học viên lái xe gần như luôn khai một địa chỉ.
- **Chốt (phương án A):** app chỉ thu **nơi thường trú** (lấy từ QR, cho sửa); không có ô cư trú. Cư trú để tool mặc định = thường trú khi nạp. Không đổi schema VPS, không sửa server, không sửa luồng tool.
- **Đã loại (B):** thêm cột `noi_cu_tru` vào bảng + `HoSoIn` + luồng tool — đúng PRD cũ nhưng phải `down -v` đổi schema + sửa server + NAP-05 cho một ô gần như không dùng.
- **Đã sửa:** PRD `THU-02` Done-khi (bỏ "nút bỏ tick để nhập khác"). Prototype `ui-demo/src/pages/app/Quet.tsx` (gỡ checkbox cư trú). **TDD không đổi** — §8.1 + field map đã ghi `NoiCT = NoiTT mặc định` sẵn.
- **Không đụng:** server (schema/endpoint giữ nguyên) · BUILD-PLAN (THU-02 vẫn task 19) · code THU-01 (đã không có ô cư trú).

---

## #8 — Chốt cách tool xác thực `/local/*` (option A + A1) · 01/10/2026

- **Mã:** `HTG-01` (phần ③). Không đổi yêu cầu nghiệp vụ — chỉ ghi lại quyết định kỹ thuật đã triển khai ở task 17.
- **Vì sao:** TDD §4.6 bắt mọi `/local/*` kèm token operator, nhưng chưa nói tool **xác thực token kiểu gì** — JWT do VPS ký + user ở PostgreSQL, tool localhost chỉ nối SQL Server nên không verify JWT đó được. Khoảng trống này lộ ra khi code task 17.
- **Chốt (option A):** backend tool gọi VPS `POST /api/auth/login` **thay mặt** → xác thực tài khoản + vai trò → tự phát **session token cục bộ** (in-memory) cho `/local/*`. Chỉ `operator`/`admin` dùng tool; `collector` → 403. Tool vẫn nạp được khi VPS chập chờn (chỉ cần VPS online lúc đăng nhập).
- **Chốt (A1):** `/local/config*` và `/local/auth/*` **miễn token** — config là bước mồi đặt URL VPS (gác token thì không đăng nhập được: đọc config cần token, mà token cần URL VPS trong config → vòng lặp). Mọi `/local/*` nghiệp vụ khác vẫn buộc session.
- **Đã loại:** (B) chia sẻ `jwt_secret` verify offline — không thu hồi tức thì + bê secret sang máy tool; (C) mỗi request gọi VPS `/api/auth/me` — buộc VPS online suốt.
- **Đã sửa:** TDD §5.5 (mới), §4.2 + §4.6 (thêm endpoint `/local/auth/*` + ghi ngoại lệ A1), TDD-decisions §4a (mới), Changelog TDD v1.9. Code đã có (task 17, commit `1a38af2`): `tool/app/session.py`, `routers/auth.py`, gác ở `main.py`; webapp + webui login.
- **Còn mở (chưa chốt):** tool cho **1 hay nhiều phiên** đăng nhập đồng thời — hiện code cho n phiên. Chưa có yêu cầu nghiệp vụ → để mở, `/capnhat` chốt sau khi cần siết.
- **Không đụng:** PRD (HTG-01 Done khi "tool bắt đăng nhập" đã có, không đổi) · màn hình demo · BUILD-PLAN.

---

## #7 — Bổ sung bảng token_blocklist vào TDD §3.2 · 01/10/2026

- **Mã:** `HTG-01` (phần ② auth). Không đổi yêu cầu nghiệp vụ — chỉ đồng bộ nội bộ TDD.
- **Vì sao:** TDD §5.1 mô tả logout ghi `jti` vào blocklist trong PostgreSQL để thu hồi phiên, nhưng schema §3.2 **ghi sót bảng này**. Phát hiện khi code task 14 (HTG-01②): để làm đúng logout thu hồi phiên phải có bảng.
- **Chốt:** thêm bảng `token_blocklist` (`jti` PK, `exp`, `revoked_at`) + index `idx_blocklist_exp` vào schema §3.2, khớp với `server/db/init.sql` đã tạo ở task 14.
- **Đã sửa:** TDD §3.2 (thêm bảng + index) + Changelog v1.8. Code `server/db/init.sql` + model `TokenBlocklist` + logout blocklist đã có (task 14, commit `b637f0a`).
- **Không đụng:** PRD (hành vi "thu hồi phiên" đã có trong Done HTG-01 + §5.1, không đổi) · màn hình · BUILD-PLAN.

---

## #6 — UX màn nạp: IA 2 chế độ + hiển thị/cảnh báo khi kéo VPS · 01/10/2026

- **Mã:** `NAP-01`, `QLY-01`, `NAP-06` (hạ ⏳), NFR ⑥. Phần lớn là UI/UX cho luồng kéo-nạp (Phase 2) + chuẩn cảnh báo áp ngay Phase 1.
- **Vì sao:** chủ dự án yêu cầu màn nạp trực quan: phân biệt rõ HV **kéo-chưa-nạp / đã-nạp / nạp-lỗi / xem-trong-DB**; và tách bạch **"khóa để nạp" (ẩn khóa đã BC1) vs "khóa để tra cứu" (hiện mọi khóa, kể cả BC1)** — hai luật BC1 ngược nhau, nhồi chung một dropdown thì không tìm được khóa đã BC1 để xem HV.
- **Chốt (hỏi từng câu, user duyệt A/A/A):**
  - **IA 2 chế độ** `Nạp hồ sơ` / `Tra cứu DB` trên màn `/tool/nap`. Chế độ Nạp: dropdown khóa **chỉ chưa BC1** (NAP-02). Chế độ Tra cứu: tìm khóa theo **tên/mã, mọi khóa kể cả 🔒 BC1** (chỉ xem).
  - **Hàng chờ nạp lô** gộp 1 danh sách, lọc **"Cần xử lý" (⚪ chờ + 🔴 lỗi, lỗi lên đầu) / "Đã nạp" (🟢)**. "Đã nạp" là xác nhận tạm trong phiên; chỗ ở thật của HV là chế độ Tra cứu DB.
  - **Tên IN HOA** khi kéo về hiển thị; **check chính tả mức A** (thiếu dấu / số-ký tự lạ / khoảng trắng thừa — không từ điển tên).
  - **Nạp lô:** dòng lỗi **đỏ + lý do**, dòng xong **xanh**; lô vẫn chạy hết.
  - **Chuẩn UX cảnh báo (NFR ⑥):** inline, **nổi bật (banner nền/viền/icon)**, **nêu rõ nguyên nhân**; màu + icon + chữ (phủ mù màu). Áp cả cảnh báo trùng CCCD hiện có.
- **Đã sửa:** PRD `NAP-01` (Done + Edge), `QLY-01` (chế độ Tra cứu), `NAP-06` (hạ ⏳ — còn banner nổi bật), ⑥ NFR, Changelog v2.3 · TDD §11.1 + §10.4 + Changelog v1.7 · `SCREENS.md` (3 quyết định UX + màn #13 ⬜).
- **Đã làm phiên này:** C1 banner nổi bật trong `NapHoSo.tsx` (cảnh báo trùng CCCD) → NAP-06 ✅ lại (verify Playwright 375/1440).
- **Còn nợ:** IA 2 chế độ + nạp lô badge + IN HOA + check chính tả = **NAP-01 Phase 2** (chưa dựng); cập nhật task 20 + 22 qua `/kehoach` bổ sung; dựng màn #13 qua `/prototype-next`.

---

## #5 — Nới ❌ NAP-05 cho UPDATE cột ảnh + thêm QLY-05 Nạp/thay ảnh · 01/10/2026

- **Mã:** `NAP-05` (sửa), `QLY-05` (thêm mới — nhóm QLY, vì `QLY-04` đã dùng cho "Kết xuất Excel" NICE).
- **Vì sao:** Review TDD §10 (đọc thân SP + verify DB thật) xác định **SP gộp `usp_QuangLA_PM4_ThuNhanHS_ThemMoiCapNhat` KHÔNG ghi ảnh** — không có cột `DuongDanAnh`/`ChatLuongAnh`, set `TT_XuLy='01'`. Nhưng 55/55 HV thật khóa B-K149 có `TT_XuLy='03'` + đường dẫn ảnh đầy đủ → ghi ảnh là bước RIÊNG sau SP. Chốt **hướng A: UPDATE thẳng 5 cột ảnh** `NguoiLX_HoSo` (`DuongDanAnh`, `ChatLuongAnh`, `TT_XuLy`, `NgayThuNhanAnh`, `NguoiThuNhanAnh`) — việc này nghịch dòng ❌ cũ "chỉ qua SP" nên phải nới ràng buộc. Tiện thể sửa tiêu đề NAP-05 còn ghi "3 SP" (đã đổi từ CHANGES #4).
- **QLY-05:** cùng cơ chế ghi ảnh hướng A, áp cho HV **đã có trong DB** — bổ sung ảnh cho HV chưa ảnh (`TT_XuLy='01'`) hoặc thay ảnh mới cho HV đã có (`'03'`, ghi đè). Có bộ lọc tình trạng ảnh trên màn tra cứu + nút "Nạp/thay ảnh" trong drawer. **Làm SAU NAP-05** (dùng lại logic ghi ảnh NAP-04/NAP-05).
- **Đã sửa:** PRD NAP-05 (tiêu đề + dòng ❌ + Changelog v2.2) · PRD thêm story `QLY-05` · TDD §11.5 + Changelog v1.6 · `ui-demo/SCREENS.md` (màn #12 ⬜) · biên bản `docs/tdd-review-01-10-2026.md`.
- **Còn nợ:** `QLY-05` dựng màn (`/prototype-next`) + code (sau NAP-05) + task trong BUILD-PLAN (`/kehoach` bổ sung). Code NAP-05 áp hướng A khi làm lại.

---

## #4 — Đổi đường nạp HV: 3 SP rời → 1 SP gộp app cũ · 01/10/2026

- **Mã:** `NAP-05` (và nền cho `NAP-01`, `QLY-01/02/03` dùng SP tương tự).
- **Vì sao:** Mục tiêu NAP-05 là **bản ghi khớp app cũ 100%**. Khi chạy **AS-003** (nạp thử 1 HV thật vào khóa B-K149), bản ghi tạo bằng 3 SP rời (`usp_NguoiLX_Insert` → `usp_NguoiLX_HoSo_Insert` → `usp_NguoiLXHS_GiayTo_Insert`) **lệch app cũ 5 field**: họ tên không IN HOA · `NoiTT`/`NoiCT` nhét tên xã gây app hiển thị lặp địa chỉ (phải để trống, địa chỉ lấy từ mã DVHC 2 cấp) · `DonViHocLX`='70004' (phải NULL) · `CHON_IN_GPLX`=0 (phải 2 — **3 SP rời không có tham số để set**) · `MaQuocTich`='VN' vỡ `FK_NguoiLX_DM_QuocTich` (đúng là 'VNM'). Gốc rễ: app cũ màn "Thu nhận Hồ sơ cấp mới" nạp qua **1 SP gộp** `usp_QuangLA_PM4_ThuNhanHS_ThemMoiCapNhat` (32 tham số khớp 1:1 form), không phải 3 SP rời.
- **Mới:** nạp qua `usp_QuangLA_PM4_ThuNhanHS_ThemMoiCapNhat` — ghi NguoiLX + NguoiLX_HoSo + giấy tờ + `CHON_IN_GPLX` atomic trong một SP; bỏ compensation bù trừ 3 bước thủ công.
- **Đã sửa:** TDD §10.1 (luồng), §10.1b (sequence), §10.2 (field map khớp app cũ), §10.3 (bỏ compensation, SP atomic), Changelog v1.4 · TDD-decisions §10 (giữ "Đã từng chốt" = 3 SP rời) · PRD `NAP-05` (Steps + Done khi giá trị khớp app cũ; **hạ ⏳ Todo** — code làm lại).
- **Còn nợ:** làm lại code `tool/app/nap.py` + `tool/app/routers/nap.py` + `tool/webui/.../NapHoSo.tsx` (gửi Chi tiết địa chỉ riêng, không nhét tên xã vào NoiTT) + tests. Đọc thân SP để chốt: SP tự sinh `MaDK`/`SoHoSo` hay caller truyền; cách SP ghi `DuongDanAnh`. Phần tái dùng được từ task 9+10 cũ (commit `843819a`): form nhập tay, checklist giấy tờ, route skeleton, `sinh_so_ho_so`/`tach_ho_ten`. BUILD-PLAN task 9+10 cần `/kehoach` bổ sung xác định lại.

---

## #1 — Đổi nơi lưu bảng ánh xạ DM_DVHC_MAP · 01/10/2026

- **Loại:** đổi quyết định kỹ thuật đã chốt (TDD-decisions §5). Không phải story — là task nền (BUILD-PLAN task 5) + phục vụ `NAP-03`.
- **Vì sao:** tool desktop `.exe` phải **mang đi cài máy/cơ sở khác, không phụ thuộc máy hiện tại**, và **không được ghi/sửa gì vào DB production** (`GPLX_CSDT` chỉ được ĐỌC). Để bảng trong production nghĩa là mỗi máy mới phải tạo + nạp bảng vào production của máy đó (cần quyền tạo bảng) — ngược cả hai yêu cầu.
- **Cũ (tới 30/09/2026):** `DM_DVHC_MAP` là bảng phụ MỚI trong `GPLX_CSDT`, lý do "cập nhật danh mục một chỗ dùng chung".
- **Mới:** bảng tra cứu nằm ở **SQLite cục bộ của tool** (`staging.sqlite`). Tool đóng gói sẵn dataset `vietnamadminunits` (CSV tĩnh); lần chạy đầu / thao tác "Đồng bộ danh mục" → đọc `DM_DVHC (TrangThai=1)` của máy đích (chỉ đọc) + dataset → tự dựng bảng, nối theo TÊN nên luôn ra đúng mã của máy đích. Production không bao giờ bị ghi.
- **Đã sửa:** TDD §3.3 (SQLite thay SQL Server), §8.2 (cơ chế tự dựng), sơ đồ §2.1 (gỡ `DM_DVHC_MAP` khỏi hộp SQL Server), bảng thành phần §2.2, cây thư mục §2.4, Changelog v1.3 · TDD-decisions §5 (giữ "Đã từng chốt"). PRD `NAP-03` **không đổi** (hành vi với user y nguyên; nơi lưu là chuyện kỹ thuật).
- **Còn dấu vết (cần dọn):**
  - Bảng `dbo.DM_DVHC_MAP` **đã được tạo + nạp 10.602 dòng vào production** `DESKTOP-UBV2GQI` ở phiên trước (task 5 cũ, commit `74d211b`/`41ccb1c`) → **phải DROP** để trả máy về nguyên trạng.
  - Code `tool/db/01_create_dm_dvhc_map.sql` + `02_seed_dm_dvhc_map.sql` (nhắm SQL Server) → thay bằng builder nạp **SQLite**. `seed_dvhc_map.py` tái dùng phần đối soát theo tên, đổi đích ghi.
- **Còn nợ:** rework code task 5 (builder SQLite) + bước "Đồng bộ danh mục" trong tool. BUILD-PLAN task 5 cần cập nhật mô tả qua `/kehoach` bổ sung.

---

## #3 — Tên file ảnh .jp2 = MaDK (không phải timestamp rời) · 01/10/2026

- **Mã:** `NAP-04` / `NAP-05`
- **Vì sao:** PRD `NAP-04` Done khi ghi `70004-<yyyyMMddHHmmssfff>.jp2`, nhưng TDD §9.2 + bộ nhớ dự án §6 (verify 39.648 HV thật, khớp 100%) xác định tên file = `<MaDK>.jp2`, với `MaDK` do `usp_NguoiLX_Insert` trả về. Sinh timestamp mới ở bước ghi ảnh sẽ lệch `MaDK` → đường dẫn ảnh sai, app cũ không tìm thấy ảnh.
- **Đã sửa:** PRD `NAP-04` Done khi (dòng ghi file). Áp dụng thực tế khi code NAP-05 (dùng lại `MaDK` từ SP).
- **TDD:** không đổi (§9.2 vốn đã đúng).

---

## #2 — Dropdown Tỉnh (NAP-03 chọn tay) lấy trực tiếp từ DM_DVHC · 01/10/2026

- **Mã:** `NAP-03`
- **Vì sao:** SP `usp_DM_DVHC_SelectAll_Tinh` chỉ trả đơn vị `LoaiDvhc` TW/TI, toàn `TrangThai=0` (tỉnh cũ) — DB xác nhận `TrangThai=1` chỉ có PH/XA, không có bản ghi cấp tỉnh mới. Dùng SP này thì dropdown Tỉnh hiện tỉnh cũ → nhân viên chọn ra mã sai.
- **Mới:** dropdown Tỉnh lấy 34 tỉnh mới từ `DM_DVHC` (DISTINCT `MaDVQL`, tên tách từ `TenDayDu`, `TrangThai=1`). Xã vẫn qua `usp_DM_DVHC_SelectDanhSachXaPhuongTheoTinh` + lọc `TrangThai=1` ở app (SP không lọc `TrangThai`).
- **Đã sửa:** PRD `NAP-03` (dòng Done khi dropdown chọn tay). TDD §API giữ nguyên (mô tả endpoint không đổi).

---

## Mốc đối chiếu

> `/capnhat` đọc mục này ở Bước 0b để biết có thay đổi nào chưa ghi sổ không.
> So bằng **danh sách mã**, không so bằng thời gian sửa file.

- **Cập nhật:** 02/11/2026 (#88 ✏️ `KQD-08` nhận cả hai mẫu PDF DAT, số story giữ 63)
- **Cập nhật trước:** 02/11/2026 (#87 ✏️ thông báo đã gửi nêu tên học viên, số story giữ 63)
- **Cập nhật trước:** 02/11/2026 (#86 ✏️ báo lỗi form dễ sửa trên điện thoại, số story giữ 63)
- **Cập nhật trước:** 02/11/2026 (#85 dọn việc treo, số story giữ 63)
- **Cập nhật trước:** 02/11/2026 (#84 ✏️ giữ Cục QLHC mã 00, số story giữ 63)
- **Cập nhật trước:** 02/11/2026 (#83 ✏️ khớp form cũ, số story giữ 63)
- **Cập nhật trước:** 02/11/2026 (#82 ✏️ sau `/reviewtdd` §10.6, số story giữ 63)
- **Cập nhật trước:** 02/11/2026 (#81 ➕ `NAP-07`, `THU-07` GPLX đã có; số story 61→63)
- **Cập nhật trước:** 16/10/2026 (#80 ✏️ sau `/reviewtdd` Chọn in GPLX — đổi khóa khác loại xóa lựa chọn tay; không thêm/bớt mã, số story giữ 61. Trước đó #79 ✏️ NAP-05/NAP-01 ô "Chọn in GPLX" theo hạng khóa — NAP-05 ✅→⚠️ chờ nghiệm thu máy CSĐT; không thêm/bớt mã, số story giữ 61)
- **Cập nhật trước:** 16/10/2026 (#78 ✏️ đồng bộ PRD v4.20 + mock với TDD v6.23 §11D.13 — tab "Cần xử lý", cảnh báo thiếu giải trình, KQD-07 +3 chip; số story giữ 61. Trước đó cùng ngày: #77 ✏️ `KQD-04` HV Sở từ chối sửa xong → "Đang giải trình" + giải trình hàng loạt; `KQD-01` cột Trạng thái + tab đếm; `KQD-03`/`KQD-07` gồm `90` Đạt; hạ KQD-01/03/04/07 → ⏳; số story giữ 61; PRD v4.19 + TDD v6.22 §11D.13 + decisions §27. Trước đó 12/10/2026: #76 ✏️ `/reviewtdd` §11D.12 `KQD-10`: TDD v6.21 + PRD v4.18 + 6 sửa code; số story giữ 61. Trước đó cùng ngày: #75 ➕ `KQD-10` Xuất Sổ theo dõi kết quả học tập (mẫu Phụ lục VI); **số story 60→61**; PRD v4.17 + TDD v6.20 §11D.12 + decisions §26. Trước đó cùng ngày: #74 ✏️ `KQD-09` lưu file vào thư mục `output` + bỏ dấu chấm thừa giờ/km sân; PRD v4.16 + TDD v6.19; số story giữ 60. Trước đó cùng ngày: #73 ✏️ `/reviewtdd` §11D.11 `KQD-09`: TDD v6.18 + PRD v4.15 + 4 sửa code; số story giữ 60. Trước đó cùng ngày: #72 ➕ `KQD-09` Xuất Excel kết quả học tập theo khóa; **số story 59→60**; PRD v4.14 + TDD v6.17 §11D.11 + decisions §25. Trước đó cùng ngày: #71 ✏️ `/reviewtdd` §11D.10 `KQD-08`: đồng bộ TDD v6.16 + 2 sửa code; số story giữ 59. Trước đó cùng ngày: #70 ✏️ chốt 6 điểm sau /kiemthu `KQD-08`/`KQD-02`; số story giữ 59; PRD v4.13 + TDD v6.15. Trước đó cùng ngày: #69 ➕ `KQD-08` Nạp giờ/km đường từ PDF DAT theo khóa + ✏️ `KQD-02` ô giờ nhận `hh:mm` & nạp sẵn giờ/km đã lưu, KQD-02 hạ ⚠️→⏳ Todo; **số story 58→59**; PRD v4.12 + TDD v6.14 §11D.10 + decisions §24. Trước đó cùng ngày: #68 ✏️ `KQD-07`/`PCG-06` ghi quyết định đã chốt (5 môn mọi hạng ô tô, mô tô không xét, chốt UX qua mock) + đồng bộ TDD §11D.9/§11E.10 với code; số story giữ 58; PRD v4.11 + TDD v6.13. Trước đó cùng ngày: #67 ✏️ `QLY-07` đổi nền cả khóa ghi đè đúng file ở `DuongDanAnh`, hạ ⚠️→⏳ Todo; PRD v4.10 + TDD v6.12 §11.6; số story giữ 58. Trước đó cùng ngày: #65 ➕ `KQD-07` Kiểm trước kết xuất + #66 ➕ `PCG-06` Hạn giấy tờ xe/GPLX giáo viên/GV-xe ngưng còn phân công — hai story chỉ đọc, ⏳ Todo, không đổi schema; **số story 56→58**; PRD v4.9 + TDD v6.11 (§11D.9, §11E.10)). Trước đó 11/10/2026 (#64 ✏️ TNB ghi lại hành vi thực tế khi dựng UI task 106-115 vào PRD v4.8 + TDD v6.10; số story giữ 56. Trước đó cùng ngày: #63 ✏️ TNB ghi lại hành vi thực tế của backend task 96–105 vào TDD v6.9 + PRD v4.7; số story giữ 56. Trước đó cùng ngày: #62 ✏️ TNB đồng bộ PRD v4.6 + mockup với TDD §11F v6.8 sau /reviewtdd: bỏ "chuyển HV giữa BC2 mở", BC1 suy từ khóa; số story giữ 56. Trước đó cùng ngày: #61 ✏️ TNB thiết kế lại luồng thêm HV vào BC2 (3 bước, 4 nhóm HV, tên trạng thái nghiệp vụ); số story giữ 56. Trước đó cùng ngày: #60 ➕ Feature "Tốt nghiệp & Báo cáo 2" — **prefix mới `TNB`**, 7 story `TNB-01..07` ⏳ Todo, phân hệ #5 DB Nạp; +PRD v4.4 +TDD §11F v6.6 +decisions §23; **số story 49→56**. Trước đó cùng ngày: #59 ✏️ PCG /reviewtdd §11E: dấu vân tay + khóa ghi + giới hạn đầu vào; số story giữ 49. Trước đó cùng ngày: #58 ✏️ PCG chốt 9 điểm mơ hồ sau /kiemthu; số story giữ 49. Trước đó 10/10/2026: #57 ✏️ PCG UX: làm rõ bản nháp + nút Phân công, giữ bản nháp trên máy; số story giữ 49. Trước đó cùng ngày: #56 ✏️ PCG: cảnh báo lệch hạng GV chỉ khi dạy thực hành + bảng hợp hạng; số story giữ 49. Trước đó cùng ngày: #55 ✏️ PCG: trùng GV/xe chỉ cảnh báo + bỏ cảnh báo "đang ở khóa khác"; số story giữ 49, không mã mới. Trước đó cùng ngày: #54 ➕ Feature "Phân công giáo viên – xe" — **prefix mới PCG**, 5 story `PCG-01..05` ⏳ Todo, phân hệ #4; +PRD chương 🟣 (v4.3) + TDD §11E (v6.4) + decisions §22 + SCREENS #24/#25; **số story 44→49**. Trước đó cùng ngày: #53 ✏️ `KQD-05` "Sửa sau gửi" chọn từng HV thay khóa cứng M1 — KQD-05 hạ ⚠️→⏳ Todo; số story giữ 44, không thêm/nghỉ hưu mã. PRD v4.2 · TDD v6.3 §11D.7b · decisions §21.)
- **Cập nhật trước:** 08/10/2026 (#52 ✏️ UX form nhập HV desktop — `THU-01`/`THU-02`, 10 cải tiến nhập liệu thuần client: nút gạt giới tính, gợi ý địa chỉ 2 cấp 2025 (file tĩnh nạp lười), chặn+đếm CCCD 12 số, in hoa tên, phím mũi tên, icon nhãn, trạng thái ✓/đỏ từng ô, tự suy giới tính/năm sinh từ CCCD. **Không thêm mã, số story giữ 44.** TDD v6.2 §6.8; commit `5087ceb`.)
- **Cập nhật trước:** 08/10/2026 (#51 ➕ mở rộng `NAP-01` — "Bỏ khỏi hàng đợi" cho cả dòng chờ/lỗi + tombstone `keo_ve_bo_qua` (kéo lại không về) + bỏ nhiều một lượt; chỉ đụng staging tool, không đụng VPS/DB. **Không thêm mã, số story giữ 44.** TDD v6.0: §7.2 + §9.3b + endpoint `bo-qua`.)
- **Cập nhật trước:** 07/10/2026 (#50 ✏️ `THU-06` OCR chỉ đọc 5 trường mặt trước — bỏ ngày cấp (mặt sau, nhập tay; phát hiện khi build task 79, user chốt A). Số story giữ 44. Trước đó #49 ➕ `THU-06` — lối nhập OCR dự phòng, lật "không OCR" THU-01.)
- **Cập nhật trước:** 07/10/2026 (#48 ➕ `KQD-06` "Sửa lẻ / xóa điểm đã lưu" (chỉ HV 09/10; UPDATE trực tiếp reset về 03) — **số story 42→43**. #47 ✏️ 4 cải tiến UX lưới KQĐT (ghim tiêu đề · thu gọn khung khóa · phím mũi tên · 2 nút ngang hàng) — thuần UI, không thêm mã, KQD-01/02 giữ nguyên trạng thái.)
- **Cập nhật trước:** 07/10/2026 (#46 ✏️ Đồng bộ tài liệu TDD sau code KQD-05/03 — tài liệu lag code, KHÔNG đổi yêu cầu: §11D.6 +`GET /mo-khoa` + ghi rõ KQD-03 không có endpoint `ket-xuat` riêng; §11D.7 đảo thứ tự lùi-HV-trước/xóa-gói-sau. Số story giữ 42.)
- **Cập nhật trước:** 07/10/2026 (#45 ➕ Thêm `KQD-05` "Mở khóa để sửa điểm sau kết xuất" (cổng B-1 còn-gói-chưa-gửi · B-1a lùi cả lô → **sau /reviewtdd đổi mức CƠ SỞ** · M1 khóa cứng) + viết lại `KQD-03` khóa-first. KQD-02/04 giữ ⚠️ (1A+2A). **Số story 41→42.** +TDD §11D.7 + decisions §19. DB không nối HV↔gói → thao tác mức cơ sở.)
- **Cập nhật trước:** 07/10/2026 (#44 ✏️ App web cho chụp bù ảnh kể cả HV ĐÃ NẠP — Phương án B, lật quyết định A 01/10; THU-02 hạ ✅→⏳, QLY-05 nguồn b; **không thêm mã**, số story giữ 41. Chỉ mở bổ sung ẢNH cho HV đã nạp, sửa/xóa vẫn khóa.)
- **Cập nhật trước:** 07/10/2026 (#43 ✏️+🐛 Ngày cấp + Nơi cấp điền sẵn ở drawer "Chuẩn bị" Nạp lô — mở rộng `NAP-01`, **không thêm mã**, số story giữ 41; NAP-01 giữ 🔄, NAP-05 giữ ✅. Ngày cấp = ô sửa được + lưu nháp (`nhap_chuan_bi` +cột `ngay_cap`); Nơi cấp tự chèn option '00' Cục QLHC khi máy chưa đồng bộ `DM_DVHC`. Khác #40 — đây là drawer Nạp lô, không phải modal QLY-01.)
- **Cập nhật trước:** 07/10/2026 (#42 ➕ Nhóm "Cập nhật kết quả đào tạo" — **prefix mới KQD**, 4 story `KQD-01..04` ⏳ Todo, module tool ghi CDB đích; +PRD chương ③🟣, +TDD §11D, +decisions §17, +SCREENS #21/#22; số story 37→41. Phạm vi chỉ cập nhật KQĐT, không kết xuất XML; Sync vốn có banner DB đích nên không hạ SYNC.)
- **Cập nhật trước:** 06/10/2026 (#41 ✏️ Lịch sử sync +tên khóa (nguồn trước, đích sau) + nút Hủy sync ở Bàn đồng bộ + đổi nhãn "Số HS"→"SL hồ sơ" — thuần UI + 2 field nhật ký, **không thêm mã**, SYNC-01/03 giữ ✅. Trước đó cùng ngày: #40 ✏️+➕ Nơi cấp căn cước = Cục QLHC '00' từ `DM_DVHC` (đảo #31/BUG-10 + #37) + mở rộng modal sửa QLY-01 Nạp — không thêm mã, số story giữ 37; QLY-01 ⚠️ Partial, TCB-03 🔄, NAP-05 ✅. Tiền đề: đã chạy script đồng bộ `DM_DVHC` đích→nguồn.)
- **Cập nhật trước:** 05/10/2026 (#39 ✏️ DGT-04 +refresh-token VPS (gỡ Chặn vps_token 8h từ /reviewtdd #38) — gộp vào DGT-04, **không thêm mã mới**, số story giữ 37. Trước đó cùng ngày: #38 +Nhóm "Đóng gói & khởi chạy tool độc lập" — **prefix mới DGT**, 4 story `DGT-01..04`; HTG-01 +dòng trỏ DGT-04, giữ ✅. #37 mở rộng trường sửa nhân thân TCB-03, hạ TCB-03 ✅→⏳. #36 sửa định nghĩa DKKH + TCB-04 nâng ngưỡng. #35 +Feature "Tra cứu CDB đích" 4 story `TCB-01..04`)
- **Cập nhật trước:** 04/10/2026 (#34 +story `HTG-07` cấu hình kết nối lên header dùng chung; hạ `SYNC-01`+`SYNC-02` ✅→⏳ làm lại UI (nay đã ✅ lại); sửa bullet `HTG-01`)
- **Trước nữa:** 04/10/2026 (#33 +Feature "Đồng bộ CDB" 3 story `SYNC-01/02/03` SHOULD, port sync_tool v2.0 + tool chuyển sidebar module)
- **Trước đó:** 04/10/2026 (#32 bổ sung tiêu chí NAP-01 + QLY-05; ⚠️ #31 có dòng bảng nhưng THIẾU mục chi tiết — cần phiên #31 bổ sung) · 03/10/2026 (gộp 2 phiên song song: #28 QLY-09 + #29 NAP-01/03 + #30 THU-01/05; THU-01 hạ ✅→⏳)
- **Số story trong PRD:** 63 (gồm **`NAP-07`**, **`THU-07`** #81; gồm **`KQD-10`** #75 + **`KQD-09`** #72 + **`KQD-08`** #69 + **`KQD-07`** #65 + **`PCG-06`** #66 + **`TNB-01..07`** #60 + **`PCG-01..05`** #54 + **`THU-06`** #49 + `KQD-01/02/03/04` #42 + `KQD-05` #45 + `KQD-06` #48; cùng `HTG-01..07` · `THU-01/02/04/05` · `NAP-01..06` · `KHO-01` · `QLY-01/02/03/05/06/07/08/09` · `SYNC-01/02/03` · `TCB-01/02/03/04` · `DGT-01/02/03/04`; chưa tính NICE `QLY-04`, `THU-03`)
- **Mã story hiện có:** `HTG-01`…`HTG-07`, `THU-01`, `THU-02`, `THU-04`, `THU-05`, `THU-06`, `THU-07`, `NAP-01`…`NAP-07`, `KHO-01`, `QLY-01`, `QLY-02`, `QLY-03`, `QLY-05`, `QLY-06`, `QLY-07`, `QLY-08`, `QLY-09`, `SYNC-01`, `SYNC-02`, `SYNC-03`, `TCB-01`, `TCB-02`, `TCB-03`, `TCB-04`, `DGT-01`, `DGT-02`, `DGT-03`, `DGT-04`, `KQD-01`, `KQD-02`, `KQD-03`, `KQD-04`, `KQD-05`, `KQD-06`, `KQD-07`, `KQD-08`, `KQD-09`, `KQD-10`, `PCG-01`…`PCG-06` (NICE: `QLY-04`, `THU-03`), `TNB-01`…`TNB-07`
- **Mã đã nghỉ hưu:** (chưa có)
