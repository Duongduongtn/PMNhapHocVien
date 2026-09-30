# Đề bài — Hệ thống thu nhận hồ sơ học viên (mobile/web + tool nạp DB)

**Ngày:** 30/09/2026 · **Người lập:** BA (Claude) · **Nguồn:** Chủ dự án / vận hành CSDT 70004, đặt bài 30/09/2026

---

## 1. Yêu cầu gốc, nguyên văn

> "Tôi đang muốn làm 1 tool app web và dùng điện thoại để quét QR căn cước hoặc nhập các trường dữ liệu để nạp thông tin học viên, chụp hình chân dung học viên và xóa phông để có nền trắng, sau đó có 1 tool chạy ở máy tính và kết nối với app web để tải dữ liệu về rồi import vào DB. [...] tôi muốn khi nạp ảnh vào DB cũng phải ghi đường dẫn ảnh có cài đặt trong DB [...]"

> Bổ sung qua trao đổi: "app web thì dùng mobile hoặc bản desktop được nhé, ở mobile thì quét được QR và chụp được ảnh chân dung hoặc ảnh thẻ. còn bản web thì nhập được dữ liệu, thêm ảnh sau cũng được. Tool ở máy tính thì kéo dữ liệu về và cũng có thể thay ảnh. cả 2 app web và tool đều cho phép sửa dữ liệu."

> "Dữ liệu lưu ở web app (tôi có VPS và domain). [...] tool ở máy tính để kết nối với web app rất quan trọng [...] nạp vô DB rồi mở UI này lên thì hiển thị được dữ liệu học viên như thể tôi dùng UI này làm vậy."

> "địa chỉ căn cước thì cho phép nhập địa chỉ mới hoặc địa chỉ cũ rồi tự map đổi theo địa chỉ mới [...] có nhập cả hạng mô tô và ô tô."

## 2. Đào 5 Whys

| # | Câu hỏi | Trả lời |
|---|---|---|
| 1 | Vì sao cần app thu nhận + tool nạp DB? | Để không phải ngồi tại máy DB gõ tay lại toàn bộ thông tin từng học viên |
| 2 | Vì sao gõ tay tại máy DB là vấn đề? | Chậm, dễ sai (nhất là địa chỉ sau sáp nhập 2025), và bị trói tại một máy — đầu khóa nhiều HV đến cùng lúc thì nghẽn |
| 3 | Vì sao nghẽn/sai lại quan trọng? | Học viên phải chờ; nhân viên mất giờ công; dữ liệu sai phải sửa lại, ảnh hưởng hồ sơ sát hạch sau này |
| 4 | Vì sao muốn tách thu thập (điện thoại) khỏi nạp (máy DB)? | Thu thập linh hoạt mọi lúc/mọi nơi (quầy, hiện trường); dồn việc nạp về một người kiểm soát tại máy DB |
| 5 | Kết quả cuối cùng là gì? | Giảm **thời gian** lập hồ sơ + giảm **lỗi dữ liệu** + gỡ **nghẽn** đầu khóa, mà vẫn nạp vào DB production **trung thực y như app cũ** |

**Kết quả nghiệp vụ thật sự:** Rút ngắn thời gian và giảm lỗi khi lập hồ sơ học viên mới, bằng cách tách khâu thu thập (app web trên điện thoại/máy tính, quét QR) khỏi khâu nạp DB (tool tại máy DB), trong khi bản ghi tạo ra **không phân biệt được** với bản ghi do app desktop cũ nhập.

## 3. Phát biểu vấn đề

**Tình hình hiện tại:**
Nhân viên dùng app desktop cũ (màn "Thu nhận Hồ sơ cấp mới", xem `UI.png`) tại máy chứa DB `GPLX_CSDT`. Với mỗi học viên: chọn khóa học, gõ tay toàn bộ thông tin cá nhân từ CCCD, tự tra và chọn đơn vị hành chính (Tỉnh/Xã), chụp hoặc quét ảnh chân dung rời, tick giấy tờ, rồi lưu. Mỗi học viên là một lần nhập thủ công đầy đủ.

**Nỗi đau:** (chủ dự án xác nhận cả 3)
1. **Tốc độ/nghẽn** — đầu khóa nhiều học viên đến cùng lúc, gõ tay từng người không kịp.
2. **Sai sót dữ liệu** — đặc biệt địa chỉ sau sáp nhập hành chính 01/07/2025: CCCD cũ ghi địa chỉ cũ, phải tự đổi sang đơn vị mới và tra mã DVHC bằng tay, dễ sai.
3. **Bị trói tại máy DB** — chỉ nhập được tại đúng máy có DB, không thu nhận linh hoạt ở quầy/hiện trường.

**Chi phí của nỗi đau:**
| Loại chi phí | Ước tính | Nguồn số liệu |
|---|---|---|
| Giờ công lãng phí | `[GIẢ ĐỊNH]` — chưa có số HV/khóa và thời gian/HV | Chờ chủ dự án cung cấp (GĐ trong `10-assumptions.md`) |
| Tỷ lệ lỗi địa chỉ | `[GIẢ ĐỊNH]` — cao do sáp nhập 2025 | Suy luận, chưa đo |
| Rủi ro chưa thành tiền | Hồ sơ sai kéo theo sai ở khâu sát hạch/cấp GPLX | — |

**Ai chịu nỗi đau này:**
| Vai trò | Chịu như thế nào | Mức độ |
|---|---|---|
| Nhân viên thu nhận hồ sơ | Gõ tay lặp lại, tra địa chỉ thủ công, nghẽn đầu khóa | Cao |
| Nhân viên nạp DB (tại máy DB) | Dồn việc nhập, kiểm | Trung bình |
| Học viên | Chờ lâu khi đông | Trung bình |

## 4. Nếu không làm gì thì sao

Giữ nguyên: mỗi học viên vẫn gõ tay đầy đủ tại máy DB; lỗi địa chỉ sau sáp nhập tiếp diễn và tích lũy; đầu khóa vẫn nghẽn. Không có cách thu nhận từ xa/hiện trường.

## 5. Thành công trông như thế nào

| Chỉ số | Hiện tại | Mục tiêu | Đo bằng cách nào | Khi nào đo |
|---|---|---|---|---|
| Thời gian nạp 1 HV vào DB | `[GIẢ ĐỊNH]` gõ tay đầy đủ | Giảm còn thao tác xác nhận (chọn khóa + xác nhận địa chỉ + ảnh) | Bấm giờ mẫu | Sau khi chạy thật |
| Số trường phải gõ tay/HV | ~toàn bộ | Còn tối đa 2-3 việc (khóa, xác nhận địa chỉ, xác nhận ảnh) | Đếm trường | Nghiệm thu |
| Lỗi địa chỉ/DVHC | `[GIẢ ĐỊNH]` | ~0 với địa chỉ map được tự động (phủ 100% xã theo verify) | Đối chiếu DB | Sau 1 khóa |
| Bản ghi khớp app cũ | — | 100% hiển thị đúng trên `UI.png` | Mở app cũ kiểm | Mỗi lần nạp |

## 6. Phạm vi

**Trong phạm vi:**
| # | Nội dung |
|---|---|
| 1 | App web responsive (mobile + desktop): quét QR CCCD (mobile), nhập/sửa dữ liệu, chụp/thêm ảnh chân dung hoặc ảnh thẻ |
| 2 | Backend + lưu trữ trên VPS (hàng đợi học viên chờ nạp) |
| 3 | Tool tại máy DB: kéo dữ liệu về, chọn khóa học có sẵn (lọc chưa lập BC1), map địa chỉ cũ→mới, căn khung + xóa phông + xuất `.jp2`, thay ảnh, sửa dữ liệu, nạp DB qua SP có sẵn |
| 4 | Nạp trung thực: sinh Số hồ sơ, ghi đường dẫn ảnh, giấy tờ mặc định — hiển thị y app cũ |
| 5 | Hỗ trợ cả hạng mô tô (A*) và ô tô (B/C/D/E/F) — cấp mới |

**Ngoài phạm vi:**
| # | Nội dung | Vì sao loại |
|---|---|---|
| 1 | Tạo/sửa khóa học | Khóa vẫn tạo bằng app cũ; tool chỉ gán HV vào khóa có sẵn |
| 2 | Sát hạch, Báo cáo 1/2, cấp/in GPLX, báo cáo Sở/Cục | Ngoài luồng thu nhận hồ sơ |
| 3 | Nâng hạng (loại hồ sơ 3) đầy đủ | Giai đoạn sau; MVP tập trung cấp mới |
| 4 | Đồng bộ ngược từ DB ra app web | Luồng một chiều: thu thập → nạp |

## 7. Ràng buộc đã biết

| Loại | Nội dung |
|---|---|
| Thời gian | Chưa chốt |
| Ngân sách | Chưa chốt |
| Con người | Vận hành single-user tại CSDT; ít nhân sự IT |
| Kỹ thuật (phải tích hợp) | DB `GPLX_CSDT` SQL Server (DESKTOP-UBV2GQI), phải dùng schema/SP có sẵn; ảnh `.jp2` (JPEG 2000) ghi ra `D:\GPLXCSDT\ANHCDUNG\<MaKhoaHoc>\`; máy DB có internet; VPS + domain có sẵn; stack Python cả 3 phần |
| Pháp lý / tuân thủ | Dữ liệu căn cước (PII) — bảo mật khi lưu tạm trên VPS, xóa sau khi nạp |

## 8. Chưa biết

| Câu hỏi | Ai trả lời được | Chặn cái gì |
|---|---|---|
| Số HV/khóa và thời gian gõ tay/HV | Chủ dự án | Định lượng cái giá (mục 3, 5) |
| Định dạng chuỗi QR CCCD thực tế của cơ sở | Test thẻ thật | Parse QR (Pha 3) |
| Có bao nhiêu người dùng app web / tool, phân quyền | Chủ dự án | Pha 4 vai trò |

---

⛔ **Cổng chốt:** Mục 3 (phát biểu vấn đề) và mục 5 (chỉ số thành công) — chờ chủ dự án xác nhận trước khi sang Pha 2.
