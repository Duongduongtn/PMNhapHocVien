# Quyết định kỹ thuật — Thu nhận hồ sơ học viên

> Nguồn của mục 1 và mục "Risks & Trade-offs" trong `docs/TDD.md`.
> Cập nhật lần cuối: 30/09/2026

## 1. Kiến trúc 3 thành phần

- **Đã chốt:** App web (thu thập) · Backend VPS (hàng đợi) · Tool tại máy DB (nạp). Tách rời; tool là client **pull** ra VPS.
- **Vì sao:** chỉ tool nối được SQL Server + ghi ổ D + chạy xử lý ảnh; máy DB sau NAT nên phải gọi ra.
- **Đánh đổi:** 3 codebase/deploy thay vì 1; bù lại mỗi phần đơn giản, máy DB không cần mở cổng.
- **Phương án đã cân nhắc:** gộp 1 app (không được — browser không nối SQL Server/ghi .jp2).
- Nguồn: PRD ①④⑤.

## 2. Stack

- **Đã chốt:** FE **React + Vite (PWA) + TailwindCSS + shadcn/ui** (dùng chung app web + tool). BE **Python FastAPI**. DB: **PostgreSQL** (VPS) + **SQLite** (staging tool) + **SQL Server GPLX_CSDT** (đích, qua SP). Xử lý ảnh: **Pillow** (.jp2) + **rembg** (xóa phông). Nối SQL Server: **pymssql**.
- **Vì sao:** đẹp + nhất quán FE; Python xuất .jp2 + xóa phông sạch nhất; FE build sẵn ở máy dev nên tool đóng gói không cần Node ở máy CSDT.
- **Đánh đổi:** 2 ngôn ngữ (Python + JS/TS FE) — chấp nhận, không tránh được vì FE là JS.
- Nguồn: PRD ④ (chốt cùng chủ dự án).

## 3. Nơi chạy

- **Đã chốt:** App web + Backend chạy trên **VPS** (domain trỏ IP VPS, HTTPS). Tool đóng gói **PyInstaller (.exe)** chạy tại **máy DB**, mở UI localhost, **pull ra VPS** (outbound HTTPS).
- **Vì sao:** máy DB sau NAT vẫn chạy chỉ cần internet ra; không mở cổng, không cần IP tĩnh.
- **Đánh đổi:** cập nhật tool = phát hành lại .exe.
- Nguồn: PRD ④⑤.

## 4. Đăng nhập & phân quyền

- **Đã chốt:** **JWT** cho người dùng (app web + tool) + **API key riêng** cho tool khi gọi VPS. 3 vai trò: `collector` (thu nhận), `operator` (nạp DB), `admin`.
- **Vì sao:** truy vết ai gửi/ai nạp (PII căn cước); tách token người dùng và khóa máy.
- **Đánh đổi:** tự quản token thay vì dùng dịch vụ auth ngoài — chấp nhận, quy mô nhỏ.
- Nguồn: PRD F1 (HTG-01), BR-020, OG-001/002.

## 5. Nơi lưu bảng ánh xạ DM_DVHC_MAP (đổi 01/10/2026)

- **Đã chốt (01/10/2026):** Bảng ánh xạ nằm ở **SQLite cục bộ của tool** (`staging.sqlite`), **không** trong `GPLX_CSDT`. Tool đóng gói sẵn dataset `vietnamadminunits` (CSV tĩnh); lần chạy đầu / thao tác **"Đồng bộ danh mục"** → đọc `DM_DVHC (TrangThai=1)` của máy đích (chỉ đọc) + dataset → tự dựng bảng tra cứu, nối theo TÊN.
- **Vì sao:** mang `.exe` cài máy/cơ sở khác được, **không phụ thuộc máy hiện tại**; production (`GPLX_CSDT`) chỉ bị ĐỌC, không thêm bảng nào. Nối theo tên với `DM_DVHC` của chính máy đích → luôn ra đúng mã của máy đó.
- **Đánh đổi:** mỗi máy phải "Đồng bộ danh mục" lần đầu (tự động, vài giây); khi đơn vị hành chính đổi phải đồng bộ lại trên từng máy — nhẹ ở quy mô nhỏ.
- **Điều kiện DB đích:** `DM_DVHC` đã có đơn vị mới 2025 (`TrangThai=1`) — ngoài phạm vi tool.
- **Đã từng chốt (tới 30/09/2026):** bảng phụ `DM_DVHC_MAP` trong `GPLX_CSDT`, lý do "cập nhật danh mục một chỗ dùng chung, khỏi build lại tool". Đổi vì yêu cầu **không ghi production** + **tool mang đi máy khác** (01/10/2026).

## 6. Cách tool lấy dữ liệu (Câu 2 = A)

- **Đã chốt:** **Nút "Kéo về" thủ công** + tùy chọn tự làm mới mỗi vài phút.
- **Vì sao:** nhịp nạp theo đợt; đơn giản, ít request; nhân viên chủ động.
- **Đánh đổi:** không realtime — chấp nhận.
- **Phương án đã cân nhắc:** poll dày (hao VPS), realtime SSE/WebSocket (thừa).

## 7. Nơi lưu ảnh thô trên VPS (Câu 3 = A)

- **Đã chốt:** **Filesystem trên VPS** (thư mục riêng) + đường dẫn lưu trong PostgreSQL.
- **Vì sao:** đơn giản, rẻ, đủ cho ~60 ảnh/đợt.
- **Đánh đổi:** khi dọn PII phải xóa cả file lẫn dòng DB (job lo).
- **Phương án đã cân nhắc:** object storage (thừa dịch vụ), blob trong PostgreSQL (DB phình).

## 8. Ghi DB đích chỉ qua Stored Procedure

- **Đã chốt:** Tool nối SQL Server bằng `pymssql`, **chỉ gọi `usp_*`** (Insert/Update/Delete) + `SELECT` danh mục; KHÔNG dùng ORM sinh/migrate schema; dùng **SQL login riêng** (không `sa`).
- **Vì sao:** bản ghi khớp 100% app cũ; an toàn DB production.
- Nguồn: PRD BR-001, OG-004.

## 9. Job chạy nền xóa PII 30 ngày (đề xuất)

- **Đã chốt (đề xuất):** **APScheduler** chạy trong tiến trình FastAPI trên VPS, quét mỗi giờ, xóa bản ghi + ảnh thô quá 30 ngày (bỏ qua `importing`).
- **Vì sao:** không thêm dịch vụ; đủ cho tần suất ngày.
- **Đánh đổi:** job gắn với process API (restart API = job theo). Chấp nhận; có thể tách system cron sau.
- Nguồn: PRD BR-016, F4 (HTG-02).

## 10. SP nạp màn Thu nhận HS (đổi 01/10/2026)

> Làm rõ §8 cho riêng luồng thu nhận HV mới. §8 ("chỉ qua SP, khớp 100% app cũ") không đổi; đây là chốt DÙNG ĐÚNG SP nào.

- **Đã chốt (01/10/2026):** Nạp 1 HV qua **1 SP gộp `usp_QuangLA_PM4_ThuNhanHS_ThemMoiCapNhat`** — chính SP màn "Thu nhận Hồ sơ cấp mới" của app cũ (32 tham số `@p_*` khớp 1:1 form): ghi `NguoiLX` + `NguoiLX_HoSo` + giấy tờ (`@p_GiayTo`) + `CHON_IN_GPLX` atomic trong một lần.
- **Vì sao:** đó là SP app cũ dùng cho chính màn này → bản ghi khớp 100% (gồm `CHON_IN_GPLX=2`, họ tên IN HOA, địa chỉ mã+chi tiết tách riêng) — mục tiêu PRD NAP-05. 3 SP rời **không có tham số `CHON_IN_GPLX`** và ghi lệch nhiều field.
- **Đánh đổi:** phụ thuộc SP nội bộ app cũ ("QuangLA") — nhưng chính điều đó bảo đảm khớp; app cũ đổi SP thì tool phải theo.
- **Đã từng chốt (tới 01/10/2026):** 3 SP rời `usp_NguoiLX_Insert` → `usp_NguoiLX_HoSo_Insert` → `usp_NguoiLXHS_GiayTo_Insert` × N + compensation bù trừ tay. Đổi vì **AS-003 (nạp thử 1 HV thật 01/10/2026)** phát hiện bản ghi lệch app cũ 5 field (họ tên không IN HOA, địa chỉ lặp, `DonViHocLX`, `CHON_IN_GPLX`, `MaQuocTich`) và 3 SP rời không set được `CHON_IN_GPLX`.
- Nguồn: PRD NAP-05 ("khớp app cũ"); AS-003 01/10/2026; CHANGES #4.
