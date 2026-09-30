# Vai trò và phân quyền — Thu nhận hồ sơ học viên

**Ngày:** 30/09/2026 · **Người lập:** BA (Claude)

> Nguồn: Câu 2=A (nhiều NV thu nhận + ít NV nạp DB, đăng nhập riêng) + Câu 3=B (tool là app quản lý). Cơ sở nhỏ (single CSDT) nên số vai trò ít.

## 1. Danh sách vai trò

| Vai trò | Ai giữ thực tế | Số người ước tính | Xuất hiện ở bước | Mục tiêu chính |
|---|---|---:|---|---|
| **Nhân viên thu nhận** (`collector`) | Nhân viên tuyển sinh dùng app web (mobile/desktop) | nhiều (≥2) | B–G (app web) | Quét QR/nhập liệu + chụp ảnh, gửi lên VPS |
| **Nhân viên nạp DB** (`operator`) | Người phụ trách tại máy DB dùng tool | ít (1–2) | K–W + quản lý/tạo khóa | Kéo về, map địa chỉ, xử lý ảnh, nạp DB, quản lý hồ sơ, tạo khóa |
| **Quản trị** (`admin`) | Người quản lý hệ thống | 1 | ngoài luồng | Quản tài khoản, cấu hình, xóa PII, xem log |

> `[GIẢ ĐỊNH]` vai trò `admin` — chủ dự án chưa nêu rõ, nhưng cần cho quản tài khoản + xóa PII. Đưa vào `10-assumptions.md`.

## 2. Ma trận quyền

Ký hiệu: ✅ được · ❌ không · ⚠️ có điều kiện. Scope: `own` (bản ghi mình tạo) · `all` (toàn bộ trong phạm vi CSDT).

| Đối tượng | Hành động | Nhân viên thu nhận | Nhân viên nạp DB | Quản trị |
|---|---|---|---|---|
| **Bản ghi thu thập (VPS)** | Tạo | ✅ (own) | ❌ | ✅ |
| | Xem | ✅ (all pending) | ✅ (all pending) | ✅ (all) |
| | Sửa | ✅ (khi `draft`/`pending`) | ✅ (khi `pending`) | ✅ |
| | Xóa | ⚠️ (own, khi chưa nạp) | ⚠️ (khi chưa nạp) | ✅ |
| | Nạp vào DB | ❌ | ✅ | ⚠️ (ghi log) |
| | Xuất dữ liệu | ❌ | ❌ | ⚠️ (có log) |
| **Hồ sơ HV trong DB** | Tạo (=nạp) | ❌ | ✅ | ✅ |
| | Xem/tra cứu | ❌ | ✅ (all) | ✅ (all) |
| | Sửa thông tin/ảnh/địa chỉ | ❌ | ⚠️ (chưa lập BC1) | ✅ |
| | Đổi khóa | ❌ | ⚠️ (cùng hạng; chưa BC1) | ✅ |
| | Xóa | ❌ | ⚠️ (chưa có GPLX, chưa BC1) | ⚠️ (ghi log) |
| **Khóa học** | Tạo | ❌ | ✅ | ✅ |
| | Xem | ✅ (chọn khóa) | ✅ | ✅ |
| | Sửa/Xóa | ❌ | ❌ (ngoài MVP) | ⚠️ (app cũ) |
| **Ảnh chân dung** | Chụp/thêm | ✅ (own) | ✅ (thay ảnh) | ✅ |
| | Căn/xóa phông/.jp2 | ❌ | ✅ | ✅ |
| **Tài khoản người dùng** | Quản lý | ❌ | ❌ | ✅ |
| **Cấu hình hệ thống** | Sửa | ❌ | ❌ | ✅ |

### Giải thích các ô ⚠️

| Ô | Điều kiện chính xác |
|---|---|
| Bản ghi thu thập.Xóa — thu nhận/nạp | Chỉ khi trạng thái ≠ `imported` (chưa vào DB) |
| Bản ghi thu thập.Nạp/Xuất — admin | Được nhưng ghi log |
| Hồ sơ DB.Sửa/Đổi khóa/Xóa — nạp DB | Chỉ khi khóa **chưa lập BC1** (BR-012) và (với xóa) HV **chưa có GPLX** (FK NO_ACTION) |
| Hồ sơ DB.Xóa — admin | Ghi log; vẫn bị FK chặn nếu đã có GPLX |
| Khóa học.Sửa/Xóa — admin | Ngoài MVP; tạm dùng app cũ |

## 3. Quyền theo trạng thái

### Đối tượng: Bản ghi thu thập (VPS) — xem `04b-state-ho-so-thu-thap.md`

| Trạng thái | Ai sửa | Ai xóa | Ai nạp | Bất biến? | Ghi chú |
|---|---|---|---|---|---|
| `draft` | Người nhập | Người nhập | — | Không | Trên app web, chưa gửi |
| `pending` | Thu nhận, Nạp DB | Thu nhận (own), Nạp DB, Admin | Nạp DB | Không | Chờ nạp |
| `importing` | ❌ (khóa) | ❌ | Nạp DB (đang) | Khóa tạm | Đang nạp |
| `imported` | ❌ (trên VPS) | Hệ thống (30 ngày), Admin | ❌ (chặn nạp lại) | **Bất biến** | Đã vào DB |
| `duplicate` | Nạp DB (đổi khóa) | Nạp DB | — | Không | CCCD trùng khóa |
| `deleted`/`discarded` | ❌ | — | — | **Bất biến** | Đã xóa |

### Đối tượng: Hồ sơ HV trong DB

| Trạng thái (theo khóa) | Ai sửa | Ai xóa | Bất biến? | Ghi chú |
|---|---|---|---|---|
| Khóa **chưa lập BC1** | Nạp DB, Admin | Nạp DB (chưa GPLX), Admin | Không | Còn chỉnh được |
| Khóa **đã lập BC1** | ❌ (dùng app cũ) | ❌ | Gần bất biến | Đã báo cáo Sở |
| HV **đã có GPLX** | Chỉ app cũ | ❌ (FK chặn) | **Bất biến** | Hồ sơ hoàn tất |

## 4. Tách biệt trách nhiệm (SOD)

```
SOD-001  Người thu nhận và người nạp DB NÊN khác nhau (không bắt buộc)
         Vì sao: kiểm tra chéo dữ liệu trước khi vào DB thật
         Xử lý khi vi phạm: cảnh báo mềm (cơ sở nhỏ, 1 người có thể kiêm)
         Ngoại lệ: cơ sở ít người → cho 1 người kiêm cả hai, nhưng KHÔNG dùng chung tài khoản

SOD-002  Không dùng chung tài khoản
         Vì sao: PII căn cước cần truy vết ai gửi/ai nạp (BR-020)
         Xử lý khi vi phạm: mỗi người một tài khoản; admin không phát tài khoản dùng chung
         Ngoại lệ: không có
```

## 5. Quyền hệ thống và job nền

| Job tự động | Chạy dưới quyền | Bỏ qua phân quyền? | Ghi log |
|---|---|---|---|
| Tự xóa bản ghi PII quá 30 ngày | Hệ thống (service VPS) | Có (job hệ thống) | Log xóa PII |
| Kết nối SQL Server nạp DB | Tài khoản DB của tool (`sa` hoặc user riêng) | — dùng SP | Log nạp (ai, MaDK) |

> `[GIẢ ĐỊNH]` nên tạo **user SQL riêng cho tool** thay vì `sa` (giảm rủi ro). Đưa vào `10-assumptions.md`.

## 6. Câu hỏi chưa trả lời

| Câu hỏi | Ai phải quyết | Chặn |
|---|---|---|
| NV thu nhận có xem được bản ghi của NV khác không (own vs all pending)? | Chủ dự án | Scope bản ghi thu thập |
| NV nghỉ việc thì bản ghi `pending` của họ về ai? | Chủ dự án | Bàn giao |
| Tool kết nối DB bằng `sa` hay user riêng? | Chủ dự án / IT | An ninh DB |
| Ai được xuất dữ liệu HV ra ngoài (Excel), có log không? | Chủ dự án | Chống rò rỉ PII |
