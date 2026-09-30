# Tài liệu nghiệp vụ — Thu nhận hồ sơ học viên

**Cập nhật:** 30/09/2026 · **Quy mô đã chọn:** Vừa · **Chế độ phỏng vấn:** 1 nguồn tin (+ quan sát DB/UI trực tiếp)

> **AI đọc file này trước.** Mỗi việc chỉ cần 2-3 file. Bối cảnh kỹ thuật quan trọng: DB thật `GPLX_CSDT` (DESKTOP-UBV2GQI), màn tham chiếu `UI.png`, script `DBcu/DBcu30092026.sql`.

---

## 1. Đọc gì cho việc gì

| Việc đang làm | Đọc file |
|---|---|
| Code màn/API nạp học viên | `11-brd.md` §9 (năng lực) → `06-business-rules.md` → `05-flow-to-be.md` |
| Thiết kế nạp DB đúng SP | `06-business-rules.md` (BR-001,002,007,008,009) + memory `project-pmcsdtlx-nhap-hv-field-map` |
| Làm map địa chỉ DVHC | `06-business-rules.md` (BR-006) + memory (mục 4b nguồn dataset) |
| Đăng nhập / phân quyền | `07-roles-permissions.md` + `04b-state-ho-so-thu-thap.md` |
| Viết test | `08-edge-cases.md` (mức Chặn/Cao) |
| Rà bảo mật trước release | `09b-operational-gaps.md` + `08-edge-cases.md` trục T6/T7 |
| Trình bày cho người ngoài | `11-brd.md` |
| Hiểu vì sao có quy tắc | `06-business-rules.md` (cột Nguồn) → `03-findings.md` → `02-interview-notes.md` |

## 2. File nào là nguồn sự thật

| Loại thông tin | Mã | File chủ |
|---|---|---|
| Quy tắc nghiệp vụ | `BR-nnn` | `06-business-rules.md` |
| Edge case | `EC-nnn` | `08-edge-cases.md` |
| Lỗ hổng vận hành | `OG-nnn` | `09b-operational-gaps.md` |
| Giả định | `AS-nnn` | `10-assumptions.md` |
| Năng lực + user story | `CAP-nnn`/`US-nnn` | `11-brd.md` §9-10 (cỡ Vừa, chưa tách 12) |
| Vai trò & quyền | — | `07-roles-permissions.md` |
| Trạng thái đối tượng | — | `04b-state-ho-so-thu-thap.md` |

## 3. Danh sách file

| File | Nội dung | Còn thay đổi |
|---|---|---|
| `00-CHANGELOG.md` | Lịch sử thay đổi nghiệp vụ | Mỗi lần thay đổi |
| `01-problem-statement.md` | Đề bài, nỗi đau, chỉ số thành công | Hiếm |
| `02-interview-notes.md` | Ghi chép thô — không sửa | Thêm buổi mới |
| `03-findings.md` | Phát hiện + phải hỏi người khác | Buổi hỏi mới |
| `04-flow-as-is.md` | Luồng hiện tại (app cũ) | Hiếm |
| `04b-state-ho-so-thu-thap.md` | Vòng đời bản ghi thu thập (VPS) | Khi đổi luồng |
| `05-flow-to-be.md` | Luồng đích | Thường xuyên |
| `06-business-rules.md` | 20 quy tắc nghiệp vụ | **Thường xuyên nhất** |
| `07-roles-permissions.md` | 3 vai trò, ma trận quyền, SOD | Khi đổi luồng |
| `08-edge-cases.md` | 25 edge case (8 trục) | Thường xuyên |
| `09b-operational-gaps.md` | 8 lỗ hổng vận hành | Trước mỗi release |
| `10-assumptions.md` | 12 giả định + sẵn sàng vận hành | Khi kiểm chứng |
| `11-brd.md` | Tóm tắt + liên kết + năng lực + truy vết gọn | Sau đợt thay đổi lớn |

*(Không lập: `09-risks.md`, `12-capabilities.md`, `13-traceability.md` — thuộc cỡ Lớn; năng lực & truy vết gọn nằm trong `11-brd.md`.)*

## 4. Tình trạng hiện tại

| Phép kiểm | Số lỗ hổng | Ngày |
|---|---:|---|
| 1 — Bước to-be có năng lực | 0 | 30/09/2026 |
| 2 — Quy tắc có bước/năng lực áp | 0 | 30/09/2026 |
| 3 — EC Chặn/Cao có tiêu chí nghiệm thu | 0 | 30/09/2026 |
| 4 — OG chặn go-live có biện pháp | 0 | 30/09/2026 |

**Câu hỏi còn treo:** 5 — xem §15 của `11-brd.md`.
**Giả định Nền móng chưa kiểm chứng:** AS-001 (QR thật), AS-003 (nạp thử) — chặn bắt đầu build phần liên quan.

## 5. Muốn thay đổi nghiệp vụ

Chạy `/phantichnghiepvu` chọn **cập nhật** (vào Pha 8), đừng sửa tay rải rác. Ghi mọi thay đổi vào `00-CHANGELOG.md`.

## 6. Liên kết ngoài (không thuộc docs/ba nhưng cần khi build)

- Memory: `project-pmcsdtlx-nhap-hv-field-map` (map trường → cột DB, DVHC, nguồn dataset), `project-pmcsdtlx-db-moi-va-anh`, `project-pmcsdtlx-db-gotchas`.
- Kế hoạch kỹ thuật: `~/.claude/plans/pmcsdtlx-nhap-hv-mobile.md`.
