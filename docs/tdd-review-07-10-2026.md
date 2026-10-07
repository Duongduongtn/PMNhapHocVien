# Biên bản review TDD — PMCSĐTLX (module KQD)

- **File review:** docs/TDD.md — §11D "Cập nhật kết quả đào tạo" (KQD-01..04, CHANGES #42)
- **Ngày:** 07/10/2026
- **Đối chiếu:** PRD chương 🟣 KQD-01..04 · TDD-decisions §17 · CHANGES #42 · DB-GPLX_CDB_CSDT §5 · **verify trực tiếp DB đích `GPLX_CDB_CSDT`** (thân + tham số 3 SP, cột bảng `NguoiLX_HoSo`)
- **Số phát hiện:** 9 (Chặn: 1 · Nên sửa: 5 · Ghi nhận: 3) — **tất cả đã xử lý, không mục nào bỏ qua hay hoãn**

## Đã sửa

| # | Điểm | Mức | Phát hiện | Đã sửa thế nào |
|---|---|---|---|---|
| ① | 1 (PRD) | Chặn | KQD-04 yêu cầu "ô nhập giải trình" nhưng SP `_CapNhat` không có tham số ghi `GiaiTrinh`; §11D không chỉ ra chỗ lưu | Verify DB: cột `GiaiTrinh nvarchar(1000)` có sẵn nhưng không SP nhập-liệu nào ghi. §11D.0 chốt KQD-04 ghi `GiaiTrinh` bằng `UPDATE` tham số hóa riêng (phương án A) |
| ② | 2 (logic) | Nên sửa | §11D mô tả SP "giữ nguyên 90/13/14" nhưng SP **không bảo vệ `12`** — gọi vào HV 12 kéo lùi 12→09, desync Sở | §11D.0 thêm cảnh báo ⚠️ app BẮT BUỘC chặn gọi SP cho 12/13; sơ đồ §11D.1 vẽ rõ |
| ③ | 2 (logic) | Nên sửa | §11D.4 "cả 5 môn quy đổi ≥5" không rõ dùng điểm thô hay đã làm tròn → gốc dưới ngưỡng làm tròn 5,0 đỗ nhầm | §11D.2 chốt xét Đạt trên giá trị **thô chưa làm tròn**, chỉ làm tròn khi hiển thị/ghi `DiemKQ*` (phương án A) |
| ④ | 3 (edge) | Nên sửa | KQD-04 ghi điểm (SP) + giải trình (UPDATE riêng) không nguyên tử — đứt giữa chừng mất giải trình | §11D.0 chốt ghi `GiaiTrinh` **TRƯỚC** `_CapNhat` cùng connection; nêu rõ hệ quả từng nhánh lỗi (phương án A) |
| ⑤ | 3 (edge) | Ghi nhận | Hạng `MaHangMoi` NULL/rỗng (dữ liệu cũ) → §11D.3 không có mặc định giờ/km | §11D.3 thêm: hạng không xác định → không khóa-cứng giờ/km, nhân viên tự nhập + cảnh báo |
| ⑥ | 4 (bảo mật) | Nên sửa | `UPDATE GiaiTrinh` (từ ①-A) là chỗ duy nhất ghi SQL ngoài SP — nguy cơ injection + cắt cụt | §11D.0 ràng buộc tham số hóa (`%s`) + validate `len ≤ 1000` phía app |
| ⑦ | 5 (hiệu năng) | Ghi nhận | Combobox khóa đếm HV-theo-trạng-thái mỗi phím gõ có thể nặng | §11D.6 thêm debounce ~300ms + giới hạn ~20 gợi ý, chỉ đếm khóa hiển thị |
| ⑧ | 6 (sơ đồ) | Nên sửa | §11D.1 mô tả máy trạng thái bằng chữ, thiếu sơ đồ | §11D.1 chèn sơ đồ ASCII ranh giới tool/ngoài-tool + cảnh báo 12 |
| ⑨ | 1 (PRD) | Ghi nhận | TDD chọn SP đọc `usp_NguoiLX_KetQuaDaoTao_CSDT` trong khi `_CNKQDT` trả đủ cột lưới hơn | §11D.0 ưu tiên `_CNKQDT`, dặn so cột trả về khi code |

## Cố tình bỏ qua

(không có — mọi phát hiện Chặn/Nên-sửa đều đã đưa vào §11D)

## Hoãn lại

(không có)

## Dữ kiện verify DB (tham chiếu khi code)

- SP ghi `usp_NguoiLX_KetQuaDaoTao_CSDT_CapNhat`: **18 tham số** (@MaDK,@MaKH,@KQLyThuyet,@KQThucHanh,@TGBatDau,@TGKetThuc,@KetLuanCSDT,@DiemKQLyThuyet,@DiemKQThucHanh,@DiemKQMoPhong,@DiemKQHinh,@DiemKQTienLui,@TGThucHanhDuong,@TGThucHanhHinh,@TongQDThucHanh,@QDThucHanhHinh,@SoGiayCNTN,@NgayRaQDTN). WHERE `MaDK AND MaKhoaHoc`. Chuyển trạng thái: giữ 90/13/14; KetLuan='1'→09, '0'→10; **12 không được bảo vệ**.
- SP đọc `_CNKQDT` (10 tham số, phân trang) và `_GetHocVien` (@MaKhoaHoc,@MaDK) đều trả `GiaiTrinh`, `DiemKQ*`, giờ/km, `SoGiayCNTN`, `HangDaoTao` (=`MaHangMoi`), ngày khóa → prefill form sửa được. **Cả hai KHÔNG trả `LyDoTuChoiKQDT`.**
- Cột liên quan trong `NguoiLX_HoSo`: `GiaiTrinh nvarchar(1000)`, `LyDoTuChoiKQDT nvarchar(1000)`, `GhiChuKQDSTW nvarchar(510)`.

---

# Biên bản review TDD — PMCSĐTLX (#43 §9.3a) — cùng ngày, phạm vi khác

- **File review:** docs/TDD.md — §9.3a "Lưu nháp chuẩn bị BỀN", **chỉ phần CHANGES #43** (cột `ngay_cap` + ô Ngày cấp/Nơi cấp ở drawer Nạp lô). KHÔNG soi lại module KQD #42 (biên bản §11D ở trên).
- **Ngày:** 07/10/2026
- **Đối chiếu:** PRD story NAP-01 (3 "Done khi" mới) · CHANGES #43 · **code thật** `tool/app/nap.py` (`nhap_chuan_bi` DDL + `keo_ve`), `tool/webui/src/pages/tool/NapHoSo.tsx`, `TraCuuDB.tsx`/`sync/TraCuuCDB.tsx`
- **Số phát hiện:** 6 (Chặn: 1 · Nên sửa: 2 · Ghi nhận: 3) — tất cả đã xử lý, không mục nào bỏ qua hay hoãn

## Đã sửa

| # | Điểm | Mức | Phát hiện | Đã sửa thế nào |
|---|---|---|---|---|
| 3.1 | 3 (edge/dữ liệu cũ) | **Chặn** | `nhap_chuan_bi` DDL là `CREATE TABLE IF NOT EXISTS` (nap.py:464) → thêm cột `ngay_cap` không migrate bảng đã có; `tool/app` không có cơ chế migrate nào → `INSERT (… ngay_cap …)` ném `OperationalError` trên máy đã tạo bảng (#32), lưu nháp vỡ | §9.3a (bullet schema) +đoạn **Migrate bắt buộc**: guard `PRAGMA table_info` + `ALTER TABLE nhap_chuan_bi ADD COLUMN ngay_cap TEXT` trong `_nhap_conn()` sau DDL |
| 2.1 | 2 (logic/nhất quán) | Nên sửa | §9.3a ghi ô Ngày cấp = `<input type="date">` — lệch pattern `ODate` dd/mm/yyyy đã dùng ở TraCuuDB.tsx:1222 & TraCuuCDB.tsx:833; `<input type="date">` hiển thị theo locale, không chắc dd/mm/yyyy (lệch chuẩn ngày VN + PRD dòng 163 ghi "chọn ngày dd/mm/yyyy") | §9.3a đổi sang **`ODate`** (`ymdToVN`/`vnToYmd`, `max`=hôm nay), tái dùng control sẵn có |
| 2.2 | 2 (logic mơ hồ) | Nên sửa | "payload ưu tiên `nhap.ngayCap` rồi tới gốc" không rõ ô rỗng = giữ gốc hay nạp rỗng → 2 người code 2 kết quả | User chốt **A**: ô rỗng → quay về ngày gốc; §9.3a chốt **một quy tắc `nhap.ngayCap \|\| keo_ve.ngay_cap`** cho cả hiển thị lẫn nạp (khớp hành vi ô Nơi cấp hiện có) |
| 2.3 | 2 (logic) | Ghi nhận | Đọc nháp nên nhất quán với quyết định 2.2 | Tan nhờ chọn 2.2-A (một quy tắc `\|\|`, không cần phân biệt null/'') — không sửa |
| 3.2 | 3 (edge) | Ghi nhận | Reset địa chỉ BUG-04 (nap.py:566) chỉ null `dia_chi_json`/`chi_tiet` → cột `ngay_cap` tự được GIỮ, đúng sơ đồ vòng đời (TDD giữ GIỮ ngay_cap) | Không sửa — xác nhận đã nhất quán |
| 4/5/6 | 4·5·6 | Ghi nhận | Bảo mật (`ngay_cap` nhạy-cảm-thấp, không route/auth mới, PII ảnh đã ghi nhận §9.3a/decisions §11), hiệu năng (query cờ nhẹ không kéo `ngay_cap`/ảnh), sơ đồ (vòng đời nháp đã có + đã gồm `ngay_cap`) | Không sửa — các điểm này ổn |

## Cố tình bỏ qua

(không có)

## Hoãn lại

(không có)

## Dữ kiện code (tham chiếu khi code #43)

- `keo_ve` **đã có** cột `ngay_cap TEXT` (nap.py:318) lưu dạng `yyyymmdd` (`iso_to_yyyymmdd` lúc upsert) → nguồn điền sẵn hợp lệ.
- `nhap_chuan_bi` DDL hiện **8 cột, CHƯA có `ngay_cap`** (nap.py:465-467); các hàm `nhap_doc`/`nhap_luu`/`nhap_co` cũng chưa đụng `ngay_cap` → khi code #43 phải +cột ở cả DDL (kèm migrate 3.1) lẫn 3 hàm này.
- `NapHoSo.tsx:583` payload nạp hiện `ngay_cap_cmt: r.ngay_cap || undefined` (lấy thẳng gốc) → #43 đổi thành `n.ngayCap || r.ngay_cap || undefined`.
- `NapHoSo.tsx:1043` ngày cấp hiện là chữ read-only inline (`· cấp {ymdToVN(selRow.ngay_cap)}`) → #43 thay bằng ô `ODate` sửa được.
- Ô Nơi cấp ở drawer **đã** điền-sẵn-sửa-được (NapHoSo.tsx:1085 `layNhap(uuid).noiCap ?? suyNoiCap(so_cccd)`); #43 chỉ bền hóa (chèn option '00' khi combo thiếu).

---

# Mục #44 — App web chụp bù ảnh kể cả HV đã nạp (Phương án B)

- **Phạm vi review:** TDD §4.3 (nới chặn `POST /api/ho-so/:uuid/anh`) · §6.2/§6.3 (app web chụp bù `imported`) · §11.5(b) (tool kéo ảnh VPS) · TDD-decisions §18.
- **Đối chiếu:** PRD THU-02 (Done-khi ⬜ "chụp bù imported") + QLY-05 (nguồn b) · CHANGES #44 · TDD-decisions §18 · **code server thật** `server/app/routers/ho_so.py:237-251` (xác nhận còn hành vi Phương án A — `!= 'pending'` chặn, #44 chưa code).
- **Số phát hiện:** 6 (Chặn: 1 · Nên sửa: 3 · Ghi nhận: 2) — **tất cả đã xử lý, không mục nào bỏ qua hay hoãn**.
- **Ghi chú:** phần TDD #44 viết ở phiên trước (không phải phiên review) → đọc như người lạ, không giảm độ bắt lỗi.

## Đã sửa

| # | Điểm | Mức | Phát hiện | Đã sửa thế nào |
|---|---|---|---|---|
| F1 | 1 (PRD) | Nên sửa | Changelog v4.9 nói "§4.3 nới chặn `POST .../anh`" nhưng bảng API §4.3 (dòng endpoint) im lặng về luật trạng thái — luật thật nằm ở §6.3; người code mở §4.3 dễ bỏ sót | §4.3 ghi luật inline vào dòng `POST .../anh` (như dòng `DELETE`): chỉ `pending`/`imported`, `importing`/`deleted`→409, kiểm `created_by`, trỏ §6.3 |
| F2 | 2 (logic) | **Chặn** | §6.3 "cho `pending`/`imported`, vẫn chặn `importing`" bỏ sót `deleted`; phát biểu kiểu blocklist dễ dẫn tới code `if ==importing: 409` → ghi ảnh lọt vào hồ sơ đã xóa mềm | §6.3 đổi sang **allowlist** `trang_thai ∈ {pending,imported}` mới cho; mọi trạng thái khác (gồm `importing` **và `deleted`**) → 409; ghi snippet `not in (...)` + cảnh báo không viết `==importing` |
| F3 | 2 (logic) | Nên sửa | §7.5 (dòng 538 + bảng 546) vẫn tuyên bố "đóng băng sau nạp — không sửa/xóa", mâu thuẫn §6.3 vừa mở khe cho ảnh; decisions §18 thừa nhận §7.5 bị đụng nhưng chưa sửa vào §7.5 | §7.5 +ngoại lệ #44: cho bổ sung **ẢNH** HV `imported` thiếu ảnh (chỉ ảnh thô, vẫn khóa sửa thông tin/xóa); sửa cả câu dòng 538 lẫn ô bảng 546 |
| F4 | 3 (edge) | Nên sửa | Ảnh chụp bù cho HV `imported` nạp gần 30 ngày có thể bị job PII xóa (cả bản ghi + ảnh) trước khi operator kéo ở QLY-05 → hụt đúng ca #44 phục vụ | **Phương án A (user chọn):** `upload_anh` set `updated_at=now` khi ghi ảnh cho `imported`; job PII §9.3 tính tuổi 30 ngày theo `updated_at` → mỗi lần chụp bù gia hạn chờ operator kéo |
| F5 | 3 (edge/đồng thời) | Ghi nhận | Đua collector-ghi-đè-ảnh vs operator-kéo (QLY-05 b) — không hỏng dữ liệu, chỉ last-write-wins trên file | §11.5(b) +1 câu: kéo đọc bản tại thời điểm bấm, ghi đè sau → kéo lại lấy bản mới; không cần khóa |
| + | 6 (sơ đồ) | — | §11.5 mô tả luồng 3 hệ thống bằng chữ, chưa có sơ đồ — chỗ dễ hiểu sai "ai ghi đè cái gì, khi nào" | +sơ đồ ASCII luồng collector→VPS→tool vào cuối §11.5 (nêu rõ: không đổi trạng thái; operator chủ động kéo; ảnh vào DB sau bước duyệt AnhModal) |

## Cố tình bỏ qua

(không có)

## Hoãn lại

(không có)

## Điểm đã soi, kết luận ổn (không sửa)

| Điểm | Kết luận |
|---|---|
| 4 (bảo mật) | Ổn — giữ `created_by` (collector chỉ ảnh của mình kể cả `imported`); tái dùng `validate_anh` (≤8MB, magic-byte, chặn decompression bomb — §9.2); `require_role("collector")` đúng luồng; không secret trong TDD. **F6 ghi nhận:** collector ghi đè ảnh HV đã nạp — chấp nhận vì operator duyệt ở AnhModal trước khi ghi `.jp2` (có người kiểm giữa). |
| 5 (hiệu năng) | Ổn — nới điều kiện 1 endpoint đã có + wiring tool tái dùng; không query nặng, không N+1, không tải lô vào RAM, `rembg` chạy ở tool không trên request upload. |

## Dữ kiện code (tham chiếu khi code #44)

- `server/app/routers/ho_so.py:241-242` hiện chặn `if hs.trang_thai != "pending": 409` (Phương án A cũ) → #44 đổi thành `if hs.trang_thai not in ("pending","imported"): 409` (**allowlist**, F2).
- `upload_anh` (ho_so.py:248-249) hiện chỉ set `anh_tho_path` + commit, **chưa set `updated_at`** → #44 thêm `updated_at=now` (F4).
- Job PII (TDD §9.3) phải đổi mốc tuổi `created_at`→`updated_at` cho nhánh `imported` (F4) — kiểm cột thật trong `ho_so_thu_thap` khi code.
- Client: §6.6 `DaGui.tsx` + `lib/gui.ts` bỏ điều kiện chỉ-gửi-ảnh-khi-`pending` (nút "Thêm ảnh" hiện cả `imported`).
- Tool QLY-05 nguồn (b) trùng #32 đang code riêng — chỉ wiring `vps.tra_uuid`/`vps.tai_anh`→`AnhModal.napTuUrl`.
