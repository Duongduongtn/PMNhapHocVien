# Biên bản soát deploy — 02/11/2026

- **Phạm vi:** https://nhaphocvien.trungtamthanhdat.com · VPS `vps`, `/opt/nhaphocvien` · bản `74f2178`
- **Cách soát:** chỉ đọc, không in giá trị bí mật. Biên bản đầu tiên.

| Mục | Mức | Kết quả |
|---|---|---|
| ① Ứng dụng | ⚠️ | `api`, `postgres` healthy; `web` Up nhưng không có healthcheck; chỉ `web` mở cổng, bind `127.0.0.1:3012`; 30 dòng log cuối không có lỗi |
| ② HTTPS | ⚠️ | Chứng chỉ còn 58 ngày, `certbot.timer` bật, `nginx -t` sạch, HTTP chuyển HTTPS; `www` không truy cập được |
| ③ Database | ⚠️ | API truy vấn được; đủ biến môi trường theo TDD; đĩa dùng 34%; lúc soát không có sao lưu tự động (❌), đã cài cùng ngày, chưa thử khôi phục |
| ④ Migration | ✅ | Không có công cụ migration; cột `gplx_da_co` đã có, API đọc được |
| ⑤ Trang chính | ✅ | `/`, `/dang-nhap`, `/api/health` trả 200, đều dưới 0,2 giây |

## Mục chưa đạt

### ③ Không có sao lưu tự động — đã xử 02/11/2026
- **Thấy gì:** cron chỉ có sao lưu của dự án khác (CEMACOSG); không có thư mục, container hay cron sao lưu cho dự án này. DB có 471 hồ sơ (357 đã nạp, 111 chờ nạp, 3 đã xóa mềm).
- **Đã xử (user chọn sao lưu trong VPS, giữ 7 ngày):** `deploy/backup-db.sh` cài ở `/usr/local/bin/pmnhap-backup.sh`; `/etc/cron.d/pmnhap-backup` chạy 3:30 hằng đêm; file ở `/var/backups/nhaphocvien/`, chỉ root đọc. Đã chạy thử một lần.
- **Còn lại:** hỏng cả VPS thì mất luôn bản sao lưu · chưa thử khôi phục từ file · sao lưu lỗi chỉ ghi vào `/var/log/pmnhap-backup.log`, không báo ai · ảnh thô chưa có sao lưu.

### ① `web` không có healthcheck — chưa xử
- `Up` chỉ nói tiến trình còn sống. Workflow đã gọi web và API sau mỗi lần deploy nên rủi ro nhỏ.

### ② `www` không truy cập được — chưa xử
- Chứng chỉ không có tên `www`. Có thể là chủ ý vì đây là tên miền phụ; user quyết có cần không.
