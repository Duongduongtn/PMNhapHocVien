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
- **Bổ sung (08/10/2026, CHANGES #51):** điểm xóa nháp thứ **4** — **"Bỏ khỏi hàng đợi" dòng `cho`/`loi`** (nhớ "bỏ qua", TDD §9.3b) — nay cũng gọi `nhap_xoa(uuid)`, nên nháp (gồm ảnh PII) của dòng bỏ dở được dọn khi operator chủ động bỏ nó khỏi hàng đợi, không chỉ nút "Xóa nháp". Thu hẹp bớt giới hạn trên: operator giờ có 2 lối chủ động dọn PII của dòng không nạp.
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
- **Cập nhật 05/10 (/reviewtdd #38 + /capnhat #39):** hai tinh chỉnh cho phần phiên, **không đảo quyết định "vĩnh viễn"**:
  - **Mã hóa phiên đĩa: DPAPI (CurrentUser)** thay `key.bin`. *Đã từng chốt `key.bin`* → đổi vì `key.bin` nằm cùng thư mục, copy cả thư mục sang máy/user khác là giải mã được; DPAPI ràng vào máy + tài khoản Windows. (`key.bin` vẫn dùng cho config.)
  - **Thêm refresh-token VPS:** phiên local vĩnh viễn nhưng `vps_token` (JWT VPS) hết 8h → nạp từ VPS chết lặng sau 8h. Fix: VPS cấp refresh token (`POST /api/auth/refresh`), heartbeat đổi lấy access_token mới. Đụng server VPS nên đã qua `/capnhat` #39 (gộp vào DGT-04).
- **Nguồn:** user 05/10/2026; TDD §11C + §12; CHANGES #38, #39; PRD DGT-01..04; biên bản tdd-review-05-10-2026.

## 17. Module Cập nhật kết quả đào tạo — quy đổi điểm & nơi lưu cờ chương trình (07/10/2026, verify DB)

- **Đã chốt (07/10/2026):**
  - **Phạm vi:** CHỈ nhập KQĐT (`TT_XuLy` 03→09/10) qua `usp_NguoiLX_KetQuaDaoTao_CSDT_CapNhat`. **KHÔNG** kết xuất XML/gửi Sở (để PM CDB cũ lo — giữ phần mã hóa truyền tin).
  - **Quy đổi điểm:** nhân viên nhập **điểm gốc**, app quy đổi /10 theo "Sổ theo dõi KQ học tập TT17" (2 đoạn tuyến tính, ngưỡng 5,0), **ghi 5 điểm per-môn** vào `DiemKQ*`, **KHÔNG ghi điểm trung bình** vào DB.
  - **Quy tắc Đạt = từng môn ≥5** (`KetLuanCSDT`/`KQLyThuyet`/`KQThucHanh` do **app tự tính** rồi truyền SP). Bỏ điểm liệt, bỏ loại trực tiếp.
  - **Cờ chương trình CŨ/MỚI (TT12/2025 vs TT108/2026) tích chọn theo TỪNG KHÓA**, lưu **phía tool** (map `MaKH→cũ/mới` trong SQLite/JSON cấu hình), mặc định CŨ — **không** nhảy tự động theo ngày, **không** đụng schema CDB.
  - **Giờ/km thực hành (TT17/2026/TT-BXD):** giờ sân khóa cứng · km sân điền sẵn · giờ+km đường để trống, chỉ gợi ý tối thiểu.
- **Vì sao:**
  - **DB không định nghĩa "đạt"** — verify 06/10: `NguoiLX_HoSo` 0 trigger, 3 cột bit (`KQLyThuyet/KQThucHanh/KetLuanCSDT`) rỗng không computed/constraint, 2 SP CapNhat chỉ lưu nguyên tham số. HV đạt thật (`...000001`) có `KetLuanCSDT=1` nhưng mô phỏng/sa hình/chữ chi NULL → PM cũ set đạt tùy ý, **dữ liệu cũ không đáng tin để bắt chước** → tool tự đặt quy tắc theo TT17.
  - **Cờ CŨ/MỚI theo khóa + lưu phía tool:** sau 01/03/2027 khóa cũ (khai giảng trước) + khóa mới chạy song song; cắt theo ngày kiểm tra sẽ quy đổi LT sai hàng loạt (vd B 28 câu: /30→6,7 vs /50→3,1). DB đích không có cột cho cờ này nên lưu phía tool như `dvhc_map`.
  - **Per-môn ≥5 thay vì trung bình nhóm:** chặt hơn — HV mô phỏng 4,0 nhưng LT 6,7 theo TB vẫn đạt (5,35), theo per-môn là trượt. User chốt per-môn (A).
- **Phương án đã cân nhắc:**
  - *Xét đạt:* (A) **từng môn ≥5** ← chọn · (B) trung bình nhóm ≥5 (như cột Q của sổ).
  - *Nơi lưu cờ CŨ/MỚI:* (A) **theo từng khóa, lưu phía tool** ← chọn · (B) công tắc toàn cục màn Cấu hình (dễ quên gạt → sai hàng loạt).
  - *`TongQDThucHanh`:* chốt = **quãng đường trên đường** (nhân viên nhập), khớp dữ liệu cũ (~719 ≈ km đường), KHÔNG phải tổng sân+đường.
- **Đánh đổi:** per-môn ≥5 + bắt nhập đủ 5 điểm chặt hơn PM cũ (cũ cho để trống) — đúng tinh thần TT17 nhưng nhân viên gõ nhiều ô hơn. Cờ theo khóa thêm 1 thao tác tích chọn/khóa, đổi lại không sai quy đổi khi giao thời.
- **Phạm vi:** chỉ **tool máy CSDT** (ghi CDB đích). Không đụng app web/VPS, không đụng Nạp/Sync/TCB (module riêng `routers/ketqua.py`).
- **Nguồn:** user 06-07/10/2026; TDD §11D; CHANGES #42; PRD KQD-01..04; probe DB 06/10; `thamkhao/` (TT17/2026/TT-BXD + Sổ theo dõi KQ học tập TT17); `docs/DB-GPLX_CDB_CSDT.md` §5.

## 18. App web cho chụp bù ảnh kể cả hồ sơ ĐÃ NẠP — Phương án B (07/10/2026)

- **Đã chốt (07/10/2026):** cho collector **chụp/bổ sung ảnh trên app web cho HV THIẾU ảnh kể cả khi hồ sơ đã `imported`** (không chỉ `pending`). Ảnh ghi đè lên ảnh thô VPS; người nạp **kéo về ở Tra cứu DB** (QLY-05 nguồn b) để bổ sung vào DB Nạp. **Chỉ mở cho ẢNH** — sửa thông tin & xóa hồ sơ đã nạp vẫn khóa ở app web.
- **Cách operator biết HV nào có ảnh mới:** chốt **A — không cờ "ảnh mới"**. Operator tự lọc "Chưa ảnh" ở Tra cứu DB → mở HV → bấm kéo ảnh VPS; có thì hiện để chỉnh, không thì báo chưa có. KHÔNG thêm cột/tín hiệu đồng bộ trên VPS.
- **Đã từng chốt (01/10/2026) — Phương án A:** *"thay/bổ sung ảnh cho HV đã nạp CHỈ dùng ảnh từ máy tool (chọn file/chụp tại máy), KHÔNG mở đường app web chụp lại rồi tool kéo về"* (phản ánh ở TDD §11.5 + chặn `pending` ở `POST .../anh`). **Lý do đổi:** HV nạp lúc chưa có ảnh (collector chưa kịp chụp / gửi nhanh không ảnh) thì ảnh **thật của học viên** nằm ở điện thoại collector; Phương án A chỉ cho ảnh-từ-máy-tool nên **không lấy được ảnh collector chụp tại chỗ** cho HV đã nạp. Thực tế vận hành cần đúng ca này (user 07/10).
- **Vì sao đổi được an toàn:** endpoint `POST /api/ho-so/:uuid/anh` chỉ ghi `anh_tho_path`, không đổi `trang_thai`/thông tin → mở cho `imported` không ảnh hưởng vòng đời nạp; vẫn chặn `importing` (đang nạp) tránh đua; giữ kiểm `created_by` (chỉ ảnh của mình).
- **Phương án đã cân nhắc (cờ ảnh mới):** (A) **không cờ, operator tự kéo** ← chọn (đơn giản, không đụng schema VPS) · (B) thêm cờ "có ảnh mới" + tool chủ động hiện danh sách (tiện hơn nhưng phải đồng bộ 3 hệ thống — để dành, thêm sau không phá gì).
- **Đánh đổi:** app web không còn "đóng băng hoàn toàn sau nạp" (trước là ranh giới sạch §7.5) — nay có một khe hẹp cho ảnh. Chấp nhận vì chỉ ghi ảnh thô, không đổi dữ liệu nạp; bù lại lấy được ảnh collector cho HV đã nạp mà không phải gỡ về chờ nạp (QLY-08).
- **Phạm vi 3 hệ thống:** app web (`DaGui.tsx` + `lib/gui.ts` cho chụp/gửi khi imported) · VPS (`server .../anh` nới chặn) · tool (TraCuuDB/AnhModal nguồn b — QLY-05 #32 đã specced).
- **Nguồn:** user 07/10/2026; THU-02, QLY-05; TDD §6.2/§6.3/§11.5; CHANGES #44. Thay thế Phương án A chốt 01/10 (ở trên).

## 19. Mở khóa để sửa điểm sau kết xuất — cổng theo gói chưa gửi (07/10/2026, verify DB)

- **Đã chốt (07/10/2026):**
  - **B-1 (cổng):** cho mở khóa HV `TT_XuLy=12` để sửa điểm **chỉ khi CSĐT còn gói `KET_QUA_DAO_TAO` chưa gửi** (`NoiGui=<mã CSĐT>` + `TrangThai='0'`). Gói đã gửi hết → **khóa cứng**.
  - **B-1a (hành vi, mức CƠ SỞ — chốt phương án A sau /reviewtdd 07/10):** mở khóa = xóa (các) gói chưa gửi qua `usp_TRANS_CLI_HangDoiGui_Delete` + lùi **MỌI HV `12` của CƠ SỞ (mọi khóa)** về 09/10 (`UPDATE` tham số hóa, guard `KetLuanCSDT IS NOT NULL` — HV `12` không kết luận thì bỏ qua + cảnh báo, không ép '10' oan). Không mổ xẻ 1 HV. Sửa xong **kết xuất lại ở PM CDB cũ**.
  - **Đã từng chốt — "gói đã gửi hết → khóa cứng": bị thay ngày 10/10/2026 bởi §21** (sửa sau gửi chọn từng HV có xác nhận). B-1/B-1a bên dưới vẫn hiệu lực khi còn gói chưa gửi.
  - **M1 (thông báo khi khóa cứng):** chỉ nói **mức đợt** — liệt kê gói đã gửi + "không xác định được HV nằm gói nào". KHÔNG đoán gói cụ thể.
  - **Nút ở CẢ 2 tab** (Cập nhật KQĐT dòng 🔒 + Theo dõi kết xuất). `13` khóa tuyệt đối.
- **Vì sao:**
  - **DB không nối HV↔gói:** tên gói chỉ có dấu thời gian (`KQDT_<CSDT>_<MaSoGTVT>_K<timestamp>.zip`), không chứa MaKH/MaDK; không bảng junction; `Transfer_flag=0` cho mọi HV kể cả `12` (verify 07/10). Danh sách HV nằm trong file nén. → không thể "hủy kết xuất 1 HV" hay "biết HV nằm gói nào" — chỉ biết ở mức CSĐT "còn gói chưa gửi không".
  - **Vì sao phải lùi cả CƠ SỞ (B-1a — sửa sau review):** xóa gói chưa gửi buộc **quét cả CSĐT** (gói không nối khóa, không lọc được theo khóa) → nếu chỉ lùi HV `12` **của khóa đang xem**, HV `12` ở khóa khác (gói của họ cũng vừa bị xóa) treo "12 nhưng không còn gói" → không bao giờ gửi, PM cũ cũng không kết xuất lại (đang 12, ngoài nhóm 09/10 đủ điều kiện). Vì vậy lùi **mọi HV 12 của cơ sở** về 09/10 cho khớp phạm vi xóa — mọi HV vừa mất gói đều quay lại nhóm kết xuất.
  - **Vì sao chặn khi gói đã gửi:** `_CapNhat` không bảo vệ 12 nên DB cho ghi đè, nhưng bản đã gửi vẫn ở Sở → sửa cục bộ sẽ lệch. Chờ Sở từ chối (14)→giải trình (90) là nhánh chính thức.
  - **Lọc `NoiGui` không parse tên file:** cột `NoiGui`=mã CSĐT chuẩn (verify gói 75032 có `NoiGui='75032'`); tránh đụng 61 gói `TrangThai=0` của CSĐT 24005 lẫn trên máy dev dùng chung.
- **Phương án đã cân nhắc:**
  - *Cổng:* (A) cho mở mọi HV 12 kể cả gói đã gửi (linh hoạt, dễ lệch Sở) · (B-1) **chỉ khi còn gói chưa gửi** ← chọn · (B-3) chỉ thao tác cả đợt, không mở lẻ (an toàn nhưng cứng).
  - *Phạm vi lùi:* (A) chỉ HV được chọn (→ HV khác treo) · (B) cả 12 của **khóa** (→ HV 12 khóa khác vẫn treo vì gói đã xóa cả CSĐT) · (C) **cả CƠ SỞ, mọi khóa** ← chọn (07/10, sau /reviewtdd phát hiện B còn rò treo).
  - *Thông báo khi khóa cứng:* (M1) **mức đợt, trung thực** ← chọn · (M2) đoán gói theo thời gian (có thể sai → loại).
- **Đánh đổi:** "mở khóa 1 người = mở cả CƠ SỞ" (mọi HV 12 chưa gửi của cơ sở cùng về 09/10, phải kết xuất lại). Cổng B-1 khiến tính năng hiếm khi khả dụng (gói thường đã gửi) — chấp nhận, vì đó chính là ranh an toàn; phần còn lại là thông báo khóa-cứng rõ ràng + chỉ đường qua 14/90.
- **Phạm vi:** chỉ **tool máy CSDT** (ghi/xóa ở CDB đích). Endpoint `POST /local/ketqua/mo-khoa` là ngoại lệ duy nhất gỡ chặn 409 cho `12`; không đụng app web/VPS; module `routers/ketqua.py`.
- **Nguồn:** user 07/10/2026 (chốt B-1 + B-1a + M1 + nút 2 tab, qua nhiều lượt); PRD KQD-05; TDD §11D.7; CHANGES #45; probe DB live 07/10 (`GPLX_CDB_CSDT`); memory `project_pmcsdtlx_huy_ketxuat_kqdt`; mock `ui-mock/theodoiketxuat.html`.

## 20. Thêm OCR đọc chữ trên thẻ CCCD làm lối nhập dự phòng (07/10/2026)

- **Đã chốt (07/10/2026):** thêm lối nhập **thứ 3** "Chụp ảnh thẻ → tự đọc chữ (OCR)" (`THU-06`), mở cho **mọi thiết bị**. OCR điền sẵn 6 trường → **nhân viên xác nhận/sửa** trước khi lưu (không tin OCR tuyệt đối).
- **Đã từng chốt (lúc viết PRD) — "KHÔNG OCR":** THU-01 ghi *"❌ Không OCR chữ trên thẻ; ảnh thẻ chỉ dùng cắt ảnh chân dung"*. **Lý do đổi:** iPhone/iOS Safari quét QR CCCD yếu hơn Android hẳn (không có `BarcodeDetector`; engine QR web đọc không nổi QR nhỏ/mờ/lóa — verify BUG-14: zxing-cpp + zbar + OpenCV + tiền xử lý mạnh đều fail trên ảnh thẻ thật). Chữ IN trên thẻ to/rõ → OCR là lối thoát chắc hơn QR trong đúng ca này. User chốt 07/10 (sau khi test iPhone + xem kết quả giải mã thử).
- **Đã chốt (`/tdd` 07/10):** **engine = Tesseract.js** (WASM client-side, offline, dữ liệu `vie`); **nơi chạy = client thuần** (ảnh KHÔNG rời máy — rào cứng PII, xem /reviewtdd §6.7 điểm 4a); **tách trường = OCR toàn ảnh + regex theo nhãn in trên thẻ** (bền với ảnh chụp tay nghiêng/cắt lệch hơn cắt-vùng-theo-tọa-độ). Gửi ảnh CCCD ra dịch vụ eKYC ngoài bị **loại** vì lộ dữ liệu căn cước — chỉ mở lại khi có phê duyệt pháp lý. **Mở kiểm:** Tesseract.js độ chính xác tiếng Việt có dấu trên thẻ thật cần thử nghiệm; quá thấp → tăng sửa tay hoặc xin duyệt eKYC (qua `/capnhat`).
- **Phạm vi:** app web (THU-06); không đụng tool/VPS luồng ghi. Vẫn qua màn xác nhận + luồng gửi dùng chung (idempotent UUID, nháp offline).
- **Quan hệ BUG-14 (cập nhật 07/10 sau probe):** QR iPhone xác định **không khả thi bằng engine web** — probe offline ảnh thẻ thật (zxing-cpp + pyzbar + OpenCV + xoay/cắt/Otsu/phóng 3×) fail mọi engine; fix "quét toàn khung" (`c7d350a`) không cứu được. → **Giao hẳn lối iPhone cho OCR (THU-06), KHÔNG đầu tư thêm QR iPhone** (BUGS.md #14 → ⏳ vá bằng THU-06). User chốt A, 07/10. *(Đảo câu cũ "song song vẫn cải thiện QR iPhone — không thay nhau": bằng chứng probe cho thấy QR iPhone là ngõ cụt, OCR thay hẳn.)*
- **Nguồn:** user 07/10/2026; PRD THU-06; CHANGES #49; BUG-14 (probe giải mã QR ảnh thật).

## 21. Sửa điểm sau khi gói đã gửi Sở — chọn từng HV, có xác nhận (10/10/2026, verify DB)

- **Đã chốt (10/10/2026, user):** khi cơ sở **hết gói chưa gửi** (HV `12` đã nằm trong gói đã gửi Sở), **vẫn cho sửa/bổ sung điểm** — chỉ cần hộp xác nhận. **Mở theo từng HV được chọn** (không cả cơ sở). Hộp xác nhận bắt buộc: lý do ≤1.000 ký tự + tích "sẽ kết xuất lại ngay bằng phần mềm CDB". HV mở sửa mang chip cam + khối đỏ "chờ kết xuất lại" ở tab Theo dõi kết xuất đến khi HV về lại `12`.
- **Đã từng chốt — thay thế:** §19 "gói đã gửi hết → khóa cứng, chờ Sở từ chối (14) rồi giải trình (90)" và phương án (A) §19 "cho mở mọi HV 12 kể cả gói đã gửi (linh hoạt, dễ lệch Sở)" từng bị loại. User chọn lại (A) sau khi nghe hậu quả bên dưới.
- **Lối nào dùng khi nào:** còn gói chưa gửi → **"Mở khóa" §19** (xóa gói chưa gửi để không gửi điểm cũ); hết gói chưa gửi → **"Sửa sau gửi" §21**. Hai lối loại trừ nhau theo cùng một điều kiện (có/không gói `TrangThai='0'`).
- **Vì sao chọn từng HV (không cả cơ sở):** lùi cả cơ sở buộc kết xuất lại hàng loạt HV không liên quan; ở lối này không xóa gói nên không còn lý do phải lùi hàng loạt (lý do của B-1a §19 chỉ do việc xóa gói).
- **Hậu quả đã chấp nhận (verify DB 10/10):**
  - `usp_CSDT_PheDuyetKQDT_TiepNhan` chỉ nhận HV `TT_XuLy='12'` (`RAISERROR` nếu không) → Sở trả 13/14 lúc HV đang mở-sửa → HV kẹt. Giảm nhẹ: cảnh báo trước + khối đỏ nhắc + tích cam kết.
  - Sở có thể nhận 2 bản KQĐT cho 1 HV (bản đã gửi + bản kết xuất lại) — chưa xác minh Sở xử lý ra sao → hỏi hỗ trợ CDB/Sở.
  - DB không nối HV↔gói nên không biết HV nằm gói nào; vì thế không chặn theo gói.
- **Không làm — tự kết xuất XML:** file KQĐT (`FPT.GPLX.XML.dll`) là XML có chữ ký số RSA bằng khóa của phần mềm CDB. Tự ký = dùng lại khóa/giả mạo phần mềm chính thức; khóa nằm lộ trong DLL là lỗ hổng của nhà cung cấp, dự án không dùng và không chép. Muốn làm cần Cục/FPT cấp chứng thư riêng hoặc tài liệu nộp file chính thức. Kết xuất giữ ở phần mềm CDB.
- **Phạm vi:** chỉ tool máy CSDT (ghi CDB đích + sqlite nhật ký phía tool). Không đụng app web/VPS. `13` khóa tuyệt đối.
- **Nguồn:** user 10/10/2026 (qua trao đổi + chốt UI 4 phần); PRD KQD-05; TDD §11D.7b; CHANGES #53; probe DB live 10/10.

## 22. Phân công giáo viên – xe cho khóa (10/10/2026, rà soát schema + dữ liệu CDB)

- **Đã chốt (user, 10/10/2026):**
  - **Phân hệ riêng #4** "Phân công GV – xe", prefix story `PCG`; ghi `GPLX_CDB_CSDT`; phạm vi **A**: danh sách GV/xe của khóa + phân công dạy (môn + từ→đến) + ghép xe 1 GV–1 xe. Bỏ lịch tuần `LichHoc`, bỏ phân xe theo HV.
  - **Luật trùng thời gian = đúng công thức CDB (có xét giờ, khoảng nửa mở).** Cùng ngày khác giờ được; chạm đầu mút không trùng; so với mọi khóa kể cả cùng khóa.
  - **Giờ mặc định "Theo ngày" = `00:00 → 00:00`** (như 126/198 dòng GV, 118/119 dòng xe hiện có), KHÔNG 23:59; ô "Chỉnh giờ" bước **30 phút** (tròn giờ hoặc :30).
  - **Ngày bắt đầu thực hành của khóa: để trống, nhân viên tự nhập** — không gợi ý, không tự tính.
  - **Môn Thực hành lái xe** nổi bật (1 bấm = chọn môn + điền ngày); GV lý thuyết không có mặc định độ dài.
  - **Thao tác hàng loạt:** thêm/gỡ GV, phân công cùng môn+thời gian cho N GV, dời ngày kết thúc thực hành; xem trước từng GV, GV lỗi bị bỏ qua không chặn cả lô. **Ghép xe không tự ghi hàng loạt** — chỉ "Gợi ý" duyệt từng dòng.
  - Loại GV: **LT** = Lý thuyết · **TH** = Thực hành · **AL** = Lý thuyết + Thực hành (nhãn trong phần mềm CDB).
- **Vì sao:**
  - **Schema không ràng buộc gì:** không UNIQUE, CHECK hay trigger; chỉ SP `usp_CheckWarningLichLVGiaoVien`/`…LichLSDXeTap`/`…GiaoVien`/`…XeTap` (UI CDB gọi) kiểm → tool phải tự áp luật, nếu không ghi thẳng sẽ lọt GV trùng giờ.
  - **Công thức datetime nửa mở** suy ra từ SP và khớp dữ liệu thật: GV `75032004` có 09/08→20/08 rồi 20/08→22/08; GV `75032060` có 04/09 11:30 rồi 13:30 — đang lưu bình thường.
  - **`00:00→00:00` thay vì 23:59:** 23:59 sẽ chặn oan ca nối tiếp cùng ngày biên đã có trong dữ liệu.
  - **Ngày bắt đầu thực hành để trống:** dữ liệu 14 khóa cho thấy khoảng khai giảng→bắt đầu thực hành lệch theo hạng và theo khóa (B01 17, C1 20, B 20–22 ngày, có khóa lệch 1–2 ngày) → không có quy tắc cố định; ghi sai sẽ lan xuống mọi GV thực hành và ngày ghép xe.
  - **Lưu môn kiểu danh sách mã** (`TenMonHoc="1,8"`, `MaMonHoc` NULL): định dạng phần mềm CDB hiện hành ghi từ 29/07/2026 (144 dòng/10 khóa; trước đó 54 dòng/5 khóa ghi mã+tên).
  - **Không dùng SP xóa lan:** `usp_KhoaHoc_GiaoVien_Delete`/`usp_KhoaHoc_XeTap_Delete` xóa mọi dòng (khóa,GV|xe) gồm cả lịch; `usp_VoHieuLuc*` xóa danh sách ở **mọi khóa kể cả đã bế giảng** → xóa theo `MaLichLV`/`MaLichSD` từng dòng.
  - **Luật chạy ở server, một nguồn:** UI gọi `POST /kiem-tra`; `POST /ghi` kiểm lại lần cuối (không tin client).
  - **Cập nhật 11/10/2026 (/reviewtdd §11E, CHANGES #59):** `/ghi` nhận `dau_van_tay` (băm hiện trạng lúc mở khóa) và khóa ghi theo `ma_kh`. Vì sao: phần mềm CDB cũ cùng ghi một CDB và CDB không có UNIQUE — bản nháp cũ sẽ xóa lặng lẽ dòng người khác vừa thêm, hoặc bấm đúp nhân đôi dòng. Đã cân nhắc: (A) băm + khóa ← chọn · (B) chỉ băm · (C) ghi vào Risks, chờ sự cố. Ca "hai người cùng sửa trong tool" vẫn không áp dụng (một người thao tác).
- **Phương án đã cân nhắc:**
  - *Giờ mặc định:* (A) 00:00→00:00 như CDB ← chọn · (B) 00:00→23:59 trực quan nhưng lệch CDB, chặn oan ca nối tiếp.
  - *Trùng thời gian:* (A) có xét giờ như CDB ← chọn · (B) chặn cùng ngày (chặn oan ca sáng/chiều) · (C) theo loại GV (phức tạp, lệch CDB).
  - *Ngày bắt đầu thực hành:* (A) gợi ý + xác nhận · (B) tự tính · (C) **để trống tự nhập ← chọn** (user).
- **Đánh đổi:** tool ghi luật nghiêm hơn CDB ở một chỗ — trùng với **chính khóa đang sửa** bị chặn (CDB cũng chặn qua SP so mọi khóa nhưng UI cũ hay bị bỏ qua) → dữ liệu cũ có thể có cặp chồng cùng khóa; hiện 0 trường hợp. Ngày kết thúc `00:00` nghĩa là ngày đó chưa bị chiếm (như CDB) — nhãn "Theo ngày" nhắc điều này.
- **Cập nhật 10/10/2026 (CHANGES #55):** **trùng thời gian GV/xe chỉ là ⚠ cảnh báo, không chặn** (user: "phân xe, phân giáo viên vẫn bình thường, chỉ hiện cảnh báo ở chỗ lựa và ở từng dòng"); bỏ cảnh báo "đang dạy/chạy khóa khác chưa kết thúc" khỏi cột Kiểm tra. Vì sao: probe CDB thật — **0 cặp GV/xe trùng giờ giữa các khóa**, 133 cảnh báo loại đó đều nhiễu (92 ở khóa đã bế giảng); schema không trigger/CHECK/UNIQUE và 4 SP `usp_CheckWarning*` chỉ **trả câu thông báo**, không ghi/không chặn. Đánh đổi: bỏ cảnh báo trên làm bước ② mất 'nhắc GV còn ở khóa kia' khi chưa có phân công — vẫn còn huy hiệu ở bước ①. *Lật phần "ghi luật nghiêm hơn CDB" ở đánh đổi phía trên.*
- **Cập nhật 10/10/2026 (CHANGES #56) — hạng GV:** cột nguồn là `GiaoVien.CacHangGPLXDuocDT` (hạng được đào tạo, 1 giá trị/GV: B 60 · C 12 · C1 9 · D 5 · D2 1; `HangGPLX` là bằng lái của GV, không dùng). Cảnh báo lệch hạng GV là **tool tự thêm** (4 SP `usp_CheckWarning*` và `usp_GiaoVien_*` không kiểm hạng). Dữ liệu thật phân GV dạy TH: khóa C1 ← B 22 · C 9 · C1 3; khóa B ← B 20 · C1 8 · C 6 · D 2 · D2 1 → hạng khác B/C1 hoặc 'B' dạy C1 đều thực tế. Quyết (user): chỉ xét hạng khi GV dạy **thực hành**; khóa B/C1 dùng bảng hợp hạng rộng; hạng khóa khác giữ luật cũ. Quét lại 16 khóa thật: `gv_lech_hang` 92 → 0.
- **Còn mở (xác minh ở /reviewtdd hoặc khi code):** gói DKKH/BC1 có chứa GV/xe không (đang ⚠); lọc môn theo hạng từ `DM_HangDT_MonHoc` (cấu hình giờ 3 hạng B/B.01/C1 hiện NULL); đối chiếu `CacHangGPLXDuocDT` với hạng khóa; mã `LoaiGV` AL có hạn chế môn không.
- **Phạm vi:** chỉ tool máy CSDT; router mới `phancong.py`; không đụng app web/VPS/Nạp/Sync/KQĐT.
- **Nguồn:** user 10/10/2026 (nhiều lượt trao đổi + mock `ui-mock/phancong.html`); PRD PCG-01..05; TDD §11E; CHANGES #54; probe DB live 10/10/2026 (`GPLX_CDB_CSDT`); `docs/DB-GPLX_CDB_CSDT.md` (bổ sung §8).


## 23. Tốt nghiệp & Báo cáo 2 trên DB Nạp (11/10/2026, rà soát schema + dữ liệu `GPLX_CSDT`)

- **Đã chốt (user, 11/10/2026):**
  - **Phân hệ riêng #5**, prefix `TNB`; làm việc trên **DB Nạp**, **chỉ gọi SP có sẵn**, PM cũ mở lên thấy y chang; không tạo SP/bảng/cột.
  - **Tool làm:** cập nhật/hủy tốt nghiệp ô tô · tạo BC2 · thêm/bỏ HV (ô tô, mô tô riêng) · chuyển `TT_XuLy` cứu HV. **PM cũ làm:** kết xuất BC2, kết quả BC2, đổi trạng thái sau gửi, **đóng BC2** (tool không có nút Đóng).
  - Tốt nghiệp chọn theo **khóa**; mặc định khóa bế giảng trong "hôm nay − 1 tháng − 1 năm → hôm nay", công tắc "khóa cũ".
  - Cứu trạng thái: nguồn `01/02/03/04/10/12/13` → đích `09/14/17/18`, chặn `11/16/19`.
  - Đánh số BC2 theo quy tắc từng loại, nhân viên sửa được, kiểm trùng.
- **Vì sao:**
  - **Dùng `usp_NguoiLX_HoSo_Update_CNTN` (không phải `Update_HSTotNghiep`):** 90/90 HV ô tô ở `09` có đủ 6 trường sổ tốt nghiệp — dấu vết PM cũ dùng SP này; `HSTotNghiep` chỉ ghi số giấy + `SoCCN` và hủy dựa `TT_XuLy_Old` (32/90 HV trống).
  - **BC2 `TrangThai` 0 = đang mở / 1 = đã đóng:** 11/11 BC2 `TrangThai=0` toàn HV ở `11`; 439/440 BC2 `TrangThai=1` không còn HV ở `11`; khớp ghi chú trong `ThemHS_BC2`.
  - **`TongSoThiSinh` không đếm lại:** mô tô = `BaoCaoI.SoHocSinh` (7/7 BC2 gần nhất), ô tô = số HV lúc lập; PM cũ không cập nhật sau → làm khác sẽ lệch báo cáo.
  - **Lọc lại ứng viên ở tool:** nhánh mô tô của `ThemHS_BC2` viết `... AND hạng like '%A%' OR hạng='B1m'` (HV `B1m` bỏ qua mọi điều kiện); DB hiện 0 HV `B1m` nên chưa hại, vẫn lọc phòng.
  - **BC1 bắt buộc ở phiếu BC2, không ở HV:** 455/455 BC2 có `MaBCI`; `NguoiLX_HoSo.MaBC1` gần như trống (37.117 HV có BC2 mà trống).
  - **Ô tô/mô tô không trộn:** 329 BC2 chỉ ô tô, 130 chỉ mô tô, 0 trộn — DB không có cột hạng nên tool tự chặn.
  - **Đọc lại trước khi ghi:** tool và PM cũ cùng một DB; `ThemHSBC2` ghi đè `MaBC2` của HV đang ở BC2 khác.
- **Phương án đã cân nhắc:**
  - *Nút "Đóng BC2":* (A) không làm, PM cũ đóng ← chọn · (B) đóng khi không còn HV ở 11 · (C) đóng tự do.
  - *Cứu trạng thái:* (A) nguồn/đích hẹp ← chọn · (B) cho cả 16/19 với xác nhận mạnh · (C) gõ mã tự do.
  - *Mặc định khóa:* (A) cửa sổ 13 tháng theo `NgayBG` ← chọn · (B) cả năm nay + năm trước · (C) 12 tháng bỏ tháng cuối.
  - *Đánh số BC2:* (A) theo quy tắc từng loại ← chọn · (B) tự gõ · (C) một chuỗi chung.
- **Đánh đổi:** tool phụ thuộc đúng SP của PM cũ (đổi PM cũ có thể lệch); `TongSoThiSinh` hiển thị lệch thật nhưng đúng PM cũ.
- **Còn mở (xác minh khi code/nghiệm thu):** chụp trước/sau PM cũ để biết chính xác SP + cột nó chạm (`NgaySua`, `NguoiSua`, `Transfer_flag`); quy tắc số giấy CNTN kế tiếp (`N1|7282` → ?) và số sổ/quyết định theo khóa; PM cũ có ép "đã 09 mới vào BC2" ở giao diện không.
- **Phạm vi:** chỉ tool máy CSDT; router mới `tn_bc2.py`; không đụng app web/VPS/CDB/Sync/KQĐT/Phân công.
- **Nguồn:** user 11/10/2026 (nhiều lượt trao đổi); probe DB Nạp 11/10/2026; PRD TNB-01..07; TDD §11F; CHANGES #60.
- **Cập nhật 11/10/2026 (CHANGES #61, phản hồi mockup v1):** luồng thêm HV **3 bước một nút làm xong** (chọn khóa → chọn học viên → xác nhận "Lập BC2 và thêm N học viên"), bốn nhóm HV thay cho tab + mã. **Vì sao:** v1 bắt duyệt từng HV qua 3 tab và lộ mã kỹ thuật; nhân viên chỉ quyết "khóa nào, đưa ai"; phần còn lại tool tự suy. **HV thi lại KHÔNG tích sẵn** (user chốt) — số liệu: mô tô ≈ 196 người trong 12 tháng nhưng 2.767 quá 24 tháng; ô tô ≈ 437 / 1.268; tích sẵn tất cả sẽ kéo nghìn HV rất cũ vào BC2. Thay bằng nút "Thêm HV thi lại 12 tháng" (đổi được) + dán danh sách CMT + chọn theo khóa gốc. Đã cân nhắc: (A) tích sẵn thi lại ≤ 12 tháng · (B) không tích sẵn, một nút ← chọn · (C) tích sẵn tất cả. Thêm: hoàn tác theo `lo_id`, ngoại lệ xử lý tại chỗ (tốt nghiệp / cứu trạng thái).
- **Cập nhật 11/10/2026 (sau `/reviewtdd` §11F, biên bản `tdd-review-11-10-2026-tnb.md`):**
  - **Bỏ "chuyển HV từ BC2 mở khác sang BC2 này"** (user chọn A). **Vì sao:** `usp_NguoiLX_HoSo_ThemHS_BC2` không bao giờ trả HV đang `11`; ép chuyển bằng `usp_NguoiLX_Update_ThemHSBC2` đặt `TT_XuLy_Old='11'` → gỡ ra thì HV kẹt `11` không BC2, không hiện ở danh sách thêm và cứu cũng chặn nguồn `11`. HV ở BC2 mở khác giờ nằm nhóm "Không đưa được" kèm "gỡ khỏi BC2 … trước". Đã cân nhắc: (A) bỏ chuyển ← chọn · (B) tool tự gỡ BC2 cũ rồi thêm (2 SP, tự truy vấn ngoài SP, BC2 cũ hụt HV).
  - **Gọi `ThemHS_BC2` một lần với `@MaKH=''`** rồi `SELECT` bổ sung `TT_XuLy, MaBC2, hạng, NgayBG`: SP lọc khóa bằng `LIKE` nên truyền khóa cụ thể không trả HV thi lại khóa khác, và SP không trả các cột trạng thái. Đo 0,07–0,12 giây cho cả CSĐT (~3.450 HV).
  - **Một khóa ghi chung `tnbc2_ghi`** thay khóa theo BC2/khóa học: hai BC2 cùng ghi một HV không loại trừ nhau, mà SP thêm HV không có điều kiện trạng thái. **Khe còn lại** (PM cũ không dùng khóa) chấp nhận — ghi ở §16.1.
  - **`/bc2/lap` chạy nền + `lo_id` do client sinh:** chống bấm đôi/F5, "Làm tiếp" không gọi lại SP với HV đã `11` (gọi lại đặt `TT_XuLy_Old='11'`).
  - **Xóa BC2 đếm theo `MaBC2` (mọi `TT_XuLy`):** `usp_BaoCaoII_Delete` chỉ xóa đúng dòng BC2, không kiểm HV, không có FK từ HV — đây là cơ chế sinh 91 HV `MaBC2` mồ côi đang có.
  - **BC1 suy từ khóa:** 454 khóa có BC1, 0 khóa có hơn 1 BC1 → luồng 3 bước không cần bước chọn BC1.
  - **Cần `/capnhat` PRD:** TNB-04 (nhóm "Cần xem" còn ghi "đang ở BC2 khác sẽ bị chuyển") và TNB-03 ("chọn BC1 (bắt buộc)"); kiểm lại mockup `ui-mock/tnbc2.html`.
- **Cập nhật 11/10/2026 (backend task 96–105, CHANGES #63 — ghi lại thiết kế thực tế):**
  - **Số sổ/QĐ/ngày một bộ chung cho cả lượt ghi** (user chốt): vì sao — một khóa hầu như dùng một sổ; ô riêng từng HV làm bảng rộng và dễ nhập lệch; cần sổ khác thì ghi theo nhóm. Đã cân nhắc: (A) chung cả lô ← chọn · (B) sửa riêng từng HV.
  - **Trùng số giấy chỉ chặn khi ĐỔI sang số đang thuộc HV khác:** DB có 463 số trùng của PM cũ (chỉ 2 thuộc 2026); chặn mọi số trùng sẽ khóa oan các HV cũ. Hai luật đi kèm không có trong tài liệu gốc: (B) HV chưa tới bước tốt nghiệp bị chặn, (C) cấp số giấy cần cả số sổ và số QĐ (PM cũ có đủ 6 trường ở 90/90 HV `09`).
  - **Gỡ tay HV `TT_XuLy_Old='11'` bị chặn** (user chốt, khớp hoàn tác): gỡ ra HV kẹt `11` không BC2, Cứu trạng thái cũng chặn nguồn `11`. Đã cân nhắc: (A) chặn ← chọn · (B) cảnh báo + xác nhận.
  - **Hoàn tác cứu dùng trạng thái cũ trong nhật ký tool** thay vì `TT_XuLy_Old` của DB: SP `UpdateTTXLy` ghi đè cột đó mỗi lần chuyển. Đánh đổi: mất sqlite thì mất hoàn tác.
  - **BC2 đã đóng không xóa ở tool** (kể cả khi 0 HV): PRD "BC2 đã đóng chỉ xem"; 440/455 BC2 đã đóng đều còn HV.
  - **Cứu HV khóa chưa bế giảng vẫn cho:** PRD chỉ nói tool không "giải quyết" ca đó; giao diện phải nói rõ HV chưa hiện.
  - **Route `{ma:path}`:** số BC2 có dấu `/`; `%2F` bị giải mã trước khi khớp route. Các route cố định phải đứng trước.
- **Cập nhật 11/10/2026 (UI task 106-115, CHANGES #64):**
  - **Tích lẫn chưa/đã tốt nghiệp** trong một lượt ghi (user chốt A): một luồng "Xem lại → Ghi", server đã xử từng dòng; đổi lại "Chọn tất cả" chỉ chọn nhóm chưa tốt nghiệp. Đã cân nhắc: (A) tích lẫn ← chọn · (B) tách hai chế độ.
  - **"Làm tiếp" gửi đúng nội dung đã xác nhận** (payload chốt ở lần gửi đầu): vì form mount lại có thể đổi số gợi ý → tạo BC2 thứ hai. Phát hiện bởi E2E Checkpoint 26.
  - **Hoàn tất lô cứu dở từ nhật ký** (user chốt A): tool ngắt giữa lúc cứu không để HV mất nút Hoàn tác. Đã cân nhắc: (A) sửa backend ← chọn · (B) để nhân viên tự làm tươi/kiểm tra.
  - **Chưa chốt (để ngỏ):** nhóm "đã ở BC2 này"; khôi phục lô sau F5; giữ/tích sẵn lựa chọn sau Làm tươi.

## 24. Nạp giờ/km đường từ PDF DAT theo khóa (12/10/2026)

- **Đã chốt (user, 12/10/2026):**
  - Nạp giờ đường + km đường **cho cả khóa từ file DAT**, ra bảng xác nhận rồi lưu, thay cho gõ tay từng HV.
  - **Nhận thẳng PDF DAT**, không qua Excel (file DAT user có là PDF).
  - Ô Giờ đường trên lưới nhận `hh:mm` → đổi thập phân; số đã có ở DB **là giờ thập phân**, hiển thị nguyên.
- **Vì sao:**
  - **PDF đọc được bằng `pdfplumber`:** 4/4 file mẫu ra bảng sạch, 186 dòng, đủ cột; không cần OCR.
  - **UPDATE thẳng 2 cột, không qua SP `_CapNhat`:** SP ghi đè điểm, kết luận và `TT_XuLy` (kéo HV 12 lùi về 09). Nạp giờ/km không được đụng những thứ đó.
  - **Kiểm mã khóa trong file:** chống nạp nhầm file khóa khác — nhầm là ghi sai giờ/km cả khóa.
  - **Dòng chưa chạy DAT (giờ trống, km 0,00) bỏ tick sẵn:** ghi `0` đè giá trị đã có là mất dữ liệu.
  - **Giữ nguyên số đã lưu khi mở:** đoán "20,3 = 20 giờ 3 phút" sẽ đổi nhầm dữ liệu cũ đã là thập phân.
- **Phương án đã cân nhắc:**
  - *Loại file:* (A) PDF DAT ← chọn · (B) PDF + Excel · (C) chỉ Excel (người dùng tự chuyển).
  - *Số cũ ở DB:* (A) đã là giờ thập phân, giữ nguyên ← chọn · (B) phần lẻ là phút, đổi lại khi mở.
  - *Cách ghi:* (A) UPDATE 2 cột ← chọn · (B) gọi SP `_CapNhat` từng HV.
- **Đánh đổi:** thêm phụ thuộc `pdfplumber` (+ `pdfminer.six`) vào tool/exe; phụ thuộc bố cục PDF của DAT (đổi mẫu báo cáo là phải sửa bộ đọc).
- **Còn mở (xác minh khi code):** "Mã học viên" trong PDF có là `MaDK` không; UPDATE trực tiếp 2 cột có bỏ sót cột phụ nào của SP không.
- **Phạm vi:** chỉ tool máy CSDT, nhóm KQD; không đụng app web/VPS/Sync/Phân công/TNB.
- **Nguồn:** user 12/10/2026; 4 file `thamkhao/DAT *.pdf`; PRD KQD-08 + KQD-02; TDD §11D.10; CHANGES #69.
- **Cập nhật 12/10/2026 (sau `/reviewtdd` §11D.10, CHANGES #71):**
  - **"Chọn tất cả" chỉ tick dòng `khop`** (user chốt): ghi `0/0` cho người chưa chạy DAT có thể đè giá trị đang có; muốn ghi 0 thì tick tay từng dòng. Đã cân nhắc: (A) chỉ tick `khop` ← chọn · (B) tick cả chưa chạy DAT rồi điền 0.
  - **Dòng vượt trần tra lý do hiện "Chưa tra được lý do"**, không báo "không tìm thấy": khóa lớn có nhiều dòng không khớp thì dòng cuối chưa hề được tra.
  - **Chấp nhận:** đếm `da_luu` bằng `rowcount`; hai phiên nạp cùng khóa ghi sau thắng (không nhật ký); PDF không giới hạn số trang. Lý do và điều kiện xem lại: TDD §11D.10 mục "Rủi ro đã biết".

## 25. Xuất Excel kết quả học tập theo khóa (12/10/2026)

- **Đã chốt (user, 12/10/2026):**
  - **Một sheet bảng chi tiết** (không dựng sổ Phụ lục VI in mẫu): lọc/sắp xếp được trong Excel.
  - **Mọi học viên đang hoạt động** của khóa; người chưa đủ điểm để ô trống.
  - **Tên cơ quan chủ quản + cơ sở đào tạo nhập một lần ở màn Cấu hình tool**.
  - **Ngày xét hoàn thành = ngày thi của khóa**, chỉ hiện với học viên Hoàn thành.
- **Vì sao:**
  - **Lấy thẳng 5 điểm quy đổi đã lưu** (`DiemKQ*`): DB không lưu điểm gốc nên không cần và không thể tính ngược.
  - **Kết quả theo `KetLuanCSDT`**, không tính lại từ điểm đã làm tròn: kết luận lúc lưu xét trên điểm thô (KQD-02), tính lại từ điểm tròn có thể lệch ca 4,95 → 5,0.
  - **Chỉ đọc, không ghi DB:** xuất file không đổi trạng thái học viên.
  - **Tên cơ sở ở Cấu hình:** CDB không có cột tên cơ sở rõ ràng; hard-code thì đổi cơ sở phải sửa code.
- **Phương án đã cân nhắc:**
  - *Form:* (A) 1 sheet chi tiết ← chọn · (B) 2 sheet: sổ Phụ lục VI + chi tiết · (C) chỉ sổ Phụ lục VI.
  - *Học viên:* (A) mọi HV hoạt động ← chọn · (B) chỉ HV đủ 5 điểm.
  - *Tên cơ sở:* (A) nhập ở Cấu hình ← chọn · (B) hard-code · (C) để trống gõ tay.
  - *Thư viện:* `openpyxl` (đọc lại được trong test, dựng được định dạng in) so với `xlsxwriter` (chỉ ghi).
- **Đánh đổi:** thêm phụ thuộc `openpyxl` vào exe; không có sổ in đúng mẫu Phụ lục VI (nếu cần sau này thêm sheet thứ hai).
- **Phạm vi:** chỉ tool máy CSĐT, nhóm KQD; không đụng app web/VPS/Sync/Phân công/TNB.
- **Nguồn:** user 12/10/2026; `thamkhao/So_theo_doi_ket_qua_hoc_tap_DTLX_TT17.xlsx`; PRD KQD-09; TDD §11D.11; CHANGES #72.
- **Cập nhật 12/10/2026 (sau `/reviewtdd` §11D.11, CHANGES #73):**
  - **Nhãn tóm tắt "Chưa có kết luận"** (user chốt A, thay "Chưa đủ điểm"): số đếm là HV chưa có `KetLuanCSDT`, không phải HV thiếu môn; giữ đúng quyết định kết quả theo kết luận đã lưu. Đã cân nhắc: (A) đổi nhãn ← chọn · (B) giữ nhãn, đếm theo HV thiếu môn.
  - **Hệ quả §25 ghi rõ:** "Hoàn thành" có thể nằm cạnh ô điểm trống khi PM cũ lưu kết luận mà thiếu môn; Ghi chú nêu môn thiếu.
  - **Chống formula injection + làm sạch ký tự điều khiển:** file đi nộp ra ngoài, họ tên có thể do học viên khai; chuỗi bắt đầu `= + - @` ép kiểu chữ, ký tự điều khiển bị bỏ.
  - **`PUT /local/config/co-so` gác phiên:** khác `PUT /local/config` (bước mồi lần đầu); tên này đi vào file nộp ra ngoài.
  - **Hạng khối đầu hòa phiếu → theo chữ cái:** xuất hai lần ra cùng hạng.
- **Cập nhật 12/10/2026 (user dùng thử, CHANGES #74):**
  - **File lưu mặc định vào thư mục `output` của phần mềm**, không tải qua trình duyệt: người dùng cần biết file nằm đâu và lấy lại được. Bản đóng gói = `output` cạnh exe (lùi về `%APPDATA%\pmcsdtlx-tool\output` nếu không ghi được). Đã cân nhắc: (A) lưu `output` + báo đường dẫn + nút Mở thư mục ← chọn · (B) vẫn tải qua trình duyệt (vào thư mục Downloads) · (C) hộp thoại chọn nơi lưu.
  - **Không ghi đè file cũ** (`_2`, `_3`): xuất lại trong ngày không mất bản trước và không lỗi khi file cũ đang mở.
  - **Ô giờ/km sân số nguyên dùng định dạng `0`** (không `0.##`) để không hiện dấu chấm thừa.

## 26. Xuất Sổ theo dõi kết quả học tập — mẫu Phụ lục VI (12/10/2026)

- **Đã chốt (user, 12/10/2026):**
  - **Nút riêng, file riêng** `SoTheoDoiKetQuaHocTap_…xlsx`, tách khỏi Excel chi tiết KQD-09 (bảng chi tiết để lọc/đối chiếu; sổ để in nộp).
  - **Giữ nguyên bố cục file mẫu**, 1 sheet; **không bìa, không chữ ký, không trang điểm quy đổi/chi tiết**.
  - **Xếp theo TÊN rồi họ đệm**; **kết quả theo kết luận đã lưu + luật sổ mẫu** (đủ 5 điểm mới có kết quả); **mọi HV hoạt động**; **cột Khóa = tên khóa**; **Người lập để trống**.
  - **Lề trái 2 · phải 1 · trên/dưới 1,5 cm**; **cột Họ tên không xuống dòng**; **font Times New Roman 12**; **ngày chỉ `dd/mm/yyyy`** (cả KQD-09).
- **Vì sao:**
  - **Xếp tên bằng khóa tự dựng, không `locale`:** thứ tự collation tiếng Việt của Windows/Python không ổn định giữa máy; bảng chữ cái + thanh điệu là quy ước cố định.
  - **Kết quả chỉ khi đủ 5 điểm:** đúng luật sổ mẫu và không "Hoàn thành" cho học viên chưa có điểm.
  - **Ngày xét = ngày thi khóa:** mẫu lấy một ngày cho cả khóa từ ô nhập tay; CDB có ngày thi khóa.
  - **`Người lập` để trống:** mẫu lấy từ ô nhập tay; người in ký tên sau.
- **Phương án đã cân nhắc:**
  - *Kết quả:* (A) kết luận đã lưu + luật đủ 5 điểm ← chọn · (B) tính lại từ 5 điểm làm tròn như công thức mẫu (lệch ca thô 4,95).
  - *Xếp:* (A) tên → họ → đệm ← chọn · (B) từ chữ đầu (theo họ).
  - *Lề:* (A) 2/1/1,5/1,5 ← chọn · (B) 1 cm cả bốn · (C) giữ mẫu 3/2/2/2.
- **Đánh đổi / lưu ý:** dữ liệu PM cũ có nhiều HV đã lưu kết luận Đạt nhưng thiếu điểm môn → sổ để trống kết quả của họ (khác Excel chi tiết). Dev B.01-K40: 25 HV Đạt, chỉ 1 HV đủ 5 điểm. Nếu muốn sổ hiện theo kết luận thì đổi luật (phương án khác, cần user quyết).
- **Phạm vi:** chỉ tool máy CSĐT, nhóm KQD; không thêm phụ thuộc.
- **Nguồn:** user 12/10/2026; mẫu `thamkhao/So_theo_doi_ket_qua_hoc_tap_DTLX_TT17.xlsx`; PRD KQD-10; TDD §11D.12; CHANGES #75.

