# Quyết định kỹ thuật — Thu nhận hồ sơ học viên

> Nguồn của mục 1 và mục "Risks & Trade-offs" trong `docs/TDD.md`.
> Cập nhật lần cuối: 04/10/2026

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

### 4a. Cách tool xác thực người dùng cho `/local/*` (chốt 01/10/2026, task 17 — option A)

- **Đã chốt:** Tool **KHÔNG tự verify JWT** của VPS. Khi đăng nhập, backend tool gọi VPS `POST /api/auth/login` **thay mặt** → xác thực tài khoản + vai trò → rồi **tự phát một session token cục bộ** (in-memory) cho các endpoint `/local/*`. Chỉ `operator`/`admin` dùng được tool; `collector` đăng nhập tool → **403** (không nạp DB).
- **Vì sao:** JWT do VPS ký bằng `jwt_secret` + user nằm ở PostgreSQL trên VPS; tool chạy localhost chỉ nối SQL Server, không có cách xác thực JWT đó theo `get_current_user` của server. Phát session cục bộ giúp tool **vẫn nạp được khi VPS chập chờn** (chỉ cần VPS online lúc đăng nhập) — đúng tinh thần "nạp DB chạy local".
- **Đánh đổi:** session cục bộ không đồng bộ vòng đời với JWT VPS; tool khởi động lại thì đăng nhập lại (in-memory). Chấp nhận — tool 1 máy, 1 người.
- **A1 — miễn token cho `/local/config*` và `/local/auth/*`:** màn Cấu hình là **bước mồi** đặt URL VPS; nếu gác token thì không đăng nhập được (phải đọc config để biết URL VPS, mà đọc config lại cần token → vòng lặp). Config chỉ là thiết lập kết nối cục bộ, chưa chạm dữ liệu học viên. Mọi `/local/*` nghiệp vụ khác vẫn buộc session.
- **Đã cân nhắc & loại:** (B) tool chia sẻ `jwt_secret` verify offline — loại vì không thu hồi/khóa tài khoản tức thì (không đọc được `is_active`/blocklist) + phải bê secret sang máy tool; (C) mỗi request `/local/*` gọi VPS `/api/auth/me` — loại vì buộc VPS online suốt, VPS sập là tool nạp cũng chết.
- **Còn mở (chưa chốt):** tool cho **1 hay nhiều phiên** đăng nhập đồng thời? Hiện code cho **n phiên** (dict session không giới hạn). Chưa có yêu cầu nghiệp vụ → để mở; khi cần siết (vd 1 máy chỉ 1 phiên) thì `/capnhat` chốt sau.
- Nguồn: PRD HTG-01 Done khi (app web + tool đều bắt đăng nhập), TDD §5.3 (ma trận quyền), task 17.

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

## 11. Lưu nháp chuẩn bị BỀN ở máy tool, gồm cả ảnh (04/10/2026)

- **Đã chốt (04/10/2026):** Nháp chuẩn bị nạp (địa chỉ 2 cấp, chi tiết, nơi cấp, tick giấy tờ, **ảnh đã đổi nền** `jp2_b64`+preview) **lưu bền** xuống `staging.sqlite` bảng `nhap_chuan_bi` (TDD §9.3a) — sống qua F5/đóng-mở tool. **Tự xóa** khi nạp xong / "Bỏ khỏi hàng đợi" / hồ sơ bị xóa trên app web.
- **Vì sao:** operator chuẩn bị nhiều HV trước khi nạp lô; mất nháp khi lỡ tải lại trang = làm lại từ đầu, dễ tưởng mất dữ liệu. 2 chip trạng thái (Địa chỉ/Ảnh) chỉ đúng nếu nháp bền.
- **Đánh đổi (quan trọng — PII):** lưu `jp2_b64` bền **để ảnh căn cước nằm lại máy tool** giữa lúc chờ nạp — **đi ngược nguyên tắc cũ** "không để ảnh căn cước ở máy tool" (TDD §9.3 dọn ngay, §7.4). **Chấp nhận có điều kiện:** (1) máy tool là máy nội bộ tại CSDT, không phơi ra ngoài; (2) **tự xóa nháp (gồm ảnh)** ở 3 điểm dòng `keo_ve` kết thúc — nạp xong / "Bỏ khỏi hàng đợi" / đồng bộ xóa VPS; (3) ảnh nằm trong `staging.sqlite`, không commit/không backup ra ngoài (`.gitignore`).
- **Giới hạn đã biết (thu hẹp sau review TDD #32, Điểm 4):** điều kiện (2) **KHÔNG phủ nháp bỏ dở** — một dòng `cho` operator chuẩn bị rồi không nạp mà collector cũng không xóa trên app web thì nháp (gồm ảnh) **tồn tại tới khi operator chủ động bấm nút "Xóa nháp"** (thêm ở drawer Chuẩn bị). Job dọn PII 30 ngày trên VPS (§9) xóa ảnh thô bên VPS nhưng **không** kéo theo xóa nháp bên tool. Chấp nhận giới hạn này vì máy nội bộ; không làm job tự quét-tuổi để tránh phức tạp.
- **Phương án đã cân nhắc:** (B) chỉ lưu bền địa chỉ+tick, KHÔNG lưu ảnh — giữ nguyên tắc PII nhưng chip "đã có hình" không bền, F5 phải chọn ảnh lại (user bác, 03/10 hỏi-đáp). (C) mã hóa ảnh nháp trong SQLite — phức tạp, lợi ích thấp vì máy nội bộ.
- **Nguồn:** user 03/10/2026 (hỏi-đáp chốt B "lưu bền + tự xóa"); PRD NAP-01/QLY-05; CHANGES #32.

## 12. Tool chia module + sidebar trái (04/10/2026)

- **Đã chốt (04/10/2026):** Tool máy tính chia thành **nhiều module độc lập**, điều hướng 2 cấp bằng **sidebar bên trái** (danh sách module) → vùng nội dung hiện sub-nav + màn của module. Module đăng ký trong mảng `MODULES` (mở rộng N). Hiện: Thu nhận hồ sơ, Đồng bộ CDB; dự kiến Cập nhật kết quả học tập.
- **Vì sao:** thêm nghiệp vụ Sync (và sắp tới "kết quả học tập") vào chung thanh nav trên cùng sẽ chật và dễ cho operator thao tác nhầm DB (Nạp ghi `GPLX_CSDT`, Sync ghi `GPLX_CDB_CSDT`). Sidebar tách bạch từng module + màu nhấn + banner DB, và nới được cho nhiều module hơn top-nav.
- **Phương án đã cân nhắc:** (B) công tắc 2 workspace ở thanh tiêu đề — user bác vì sắp có module #3, top-bar không nới tốt. (C) giữ 1 thanh nav phẳng gộp hết màn — rối, dễ nhầm DB.
- **Đánh đổi:** đổi khung `ToolLayout` (đang là top-nav) → sidebar; hành vi các màn Nạp không đổi, chỉ chuyển vị trí điều hướng.
- **Nguồn:** user 04/10/2026 (hỏi-đáp trong buổi thiết kế SYNC); PRD ⑥ NFR; TDD §11B.0.

## 13. Kết nối DB đích CDB dùng chung host/user/pass, nhiều đích (04/10/2026)

- **Đã chốt (04/10/2026):** DB đích đồng bộ (`GPLX_CDB_CSDT`) **dùng chung Server/User/Pass** với cấu hình Nạp, **chỉ khác tên database** (`sqlserver_conn_dich(db_name)`). Hỗ trợ **nhiều DB đích** (khối `sync_targets[]` + `sync_selected` trong `config.enc`), chọn 1 mặc định, test kết nối từng cái.
- **Vì sao:** user xác nhận thông số kết nối đích giống hệt file `env.txt`, chỉ khác tên DB. Nhiều đích để sync sang CDB ô tô / mô tô khác nhau mà không sửa file.
- **Phương án đã cân nhắc:** (B) 1 trường tên DB đích đơn — gọn nhưng không đổi nhanh nhiều đích. (C) khối kết nối đích riêng đầy đủ server/user/pass — thừa vì cùng server.
- **Nguồn:** user 04/10/2026; `D:\Du_An\PMCSĐTLX\DBcu\env.txt`; port `[targets]` sync_tool; TDD §11B.1.

## 14. Tiến trình sync đẩy trực tiếp bằng SSE (04/10/2026)

- **Đã chốt (04/10/2026):** `POST /local/sync/run` chạy vòng sync ở thread nền + `GET /local/sync/stream` (Server-Sent Events) đẩy tiến trình từng HV về UI (thanh %, trạng thái từng dòng), như trải nghiệm realtime của sync_tool. Job lưu dict theo `job_id`; ngắt SSE giữa chừng thì job vẫn chạy hết (an toàn dữ liệu).
- **Vì sao:** sync vài chục–vài trăm HV cần thấy tiến trình, không để màn "đứng hình". SSE một chiều đủ dùng, nhẹ hơn WebSocket, hợp localhost 1 người.
- **Phương án đã cân nhắc:** (B) chạy xong trả kết quả 1 lần (spinner) — đơn giản nhưng mất cảm giác tiến trình với lô lớn. (C) polling — tốn request, trễ.
- **Nguồn:** user 04/10/2026 (chọn SSE); TDD §11B.3.

## 15. Bỏ ô "Cán bộ nạp", ghi NguoiTao='admin' (04/10/2026, verify DB)

- **Đã chốt (04/10/2026):** Bàn đồng bộ **không hỏi cán bộ**; ghi `NguoiTao=NguoiSua='admin'` cho mọi bản ghi sync. (Có thể nâng thành tùy chọn trong SYNC-02 sau, mặc định `admin`.)
- **Vì sao:** kết nối thật `GPLX_CDB_CSDT` (04/10) cho thấy `NguoiTao` chỉ có `ADMIN` (502) + `SYNC` (226, công cụ cũ) + 1 trống; 10 bản ghi mới nhất đều `admin`. CDB **không có khái niệm cán bộ riêng** — phần mềm ghi một tài khoản hệ thống. Ghi `admin` để bản sync **trùng khít** bản ghi phần mềm tạo, không để dấu vết lạ (khác công cụ cũ ghi 'SYNC').
- **Khác sync_tool v2.0:** bản gốc thêm ô "Cán bộ nạp" thay 'SYNC' — nay bỏ vì DB không dùng giá trị đó.
- **Đánh đổi:** mất truy vết "ai sync" trong DB; chấp nhận vì nhật ký JSON máy tool vẫn ghi batch, và CDB vốn chỉ dùng `admin`.
- **Nguồn:** user 04/10/2026 ("bỏ ô cán bộ, mặc định giống DB"); probe DB `GPLX_CDB_CSDT`; TDD §11B.2.

## 16. Đóng gói tool bằng PyInstaller + phiên đăng nhập vĩnh viễn (05/10/2026)

- **Đã chốt (05/10/2026):**
  - **Đóng gói:** tool thành **một exe PyInstaller** (one-folder), FastAPI phục vụ luôn `webui/dist` trên cùng cổng; máy đích không cần Python/Node. Dữ liệu ghi vào `%APPDATA%` khi chạy dạng đóng gói (`sys.frozen`).
  - **Phiên đăng nhập tool: VĨNH VIỄN** — lưu phiên ra đĩa (mã hóa `key.bin`), mở exe lần sau vào thẳng, **chỉ "Đăng xuất" mới thoát**; thêm thu hồi từ xa (ngầm hỏi VPS khi có mạng).
- **Vì sao:**
  - Máy CSDT không được cài thêm công cụ dev; cần mang đi như một phần mềm. PyInstaller gói sẵn mọi thư viện → không cài gì. Kiến trúc đã sẵn (`BASE=""` ở bản production → cùng origin).
  - Ca làm hằng ngày của một nhân viên nạp tại máy nội bộ: đăng nhập lại mỗi lần mở là phiền vô ích. User chọn **vĩnh viễn** (không chọn mốc 30 ngày / hết ca).
- **Phương án đã cân nhắc (độ dài phiên):** (A) trượt 30 ngày theo sử dụng · (B) **vĩnh viễn** ← chọn · (C) hết ca 8-12h. User chốt B.
- **Đánh đổi:** phiên vĩnh viễn = ai ngồi vào máy cũng vào thẳng (sửa/xóa GPLX + xem căn cước). **Chấp nhận** vì máy nội bộ CSDT 1 người dùng; lưới an toàn = nút Đăng xuất + thu hồi từ xa. Máy thành dùng chung sau này → thêm "hỏi mật khẩu khi xóa/đổi khóa" (để sau). pymssql/FreeTDS phải test trên máy sạch.
- **Phạm vi:** chỉ **tool**; đăng nhập app web (VPS, đa người) giữ phiên thường, KHÔNG đổi.
- **Nguồn:** user 05/10/2026; TDD §11C; CHANGES #38; PRD DGT-01..04.
