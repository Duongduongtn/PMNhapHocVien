// Dữ liệu mẫu — tên/chữ lấy đúng theo PRD & DB thật GPLX_CSDT. KHÔNG dùng Lorem/John Doe.

export type TrangThaiMap = "map" | "manual";
export type TrangThaiAnh = "photo" | "no";
// Trạng thái nạp lô (CHANGES #6): chờ nạp ⚪ · nạp lỗi 🔴 · đã nạp 🟢
export type NapTrangThai = "cho" | "loi" | "nap";

export interface HoSoChoNap {
  hoTen: string;
  gioiTinh: "Nam" | "Nữ";
  cccd: string;
  noiTT: string;
  ttMap: TrangThaiMap;
  ttAnh: TrangThaiAnh;
  mau: string; // màu avatar
  tick: boolean;
  trung?: boolean; // trùng CCCD trong khóa
  tt: NapTrangThai; // trạng thái nạp lô
  loiLyDo?: string; // lý do khi tt = "loi"
  chinhTa?: string; // cảnh báo chính tả mức A (thiếu dấu / ký tự lạ / khoảng trắng thừa)
}

export interface HocVienDB {
  soHS: string;
  hoTen: string;
  gioiTinh: "Nam" | "Nữ";
  cccd: string;
  noiTT: string;
}

// Hồ sơ chờ nạp (kéo từ VPS về staging) — chưa vào DB
export const hoSoChoNap: HoSoChoNap[] = [
  { hoTen: "NGUYỄN THANH TÂM", gioiTinh: "Nam", cccd: "070202008455", noiTT: "Xã Phú Nghĩa, Tỉnh Đồng Nai", ttMap: "map", ttAnh: "photo", mau: "bg-blue-500", tick: true, tt: "cho" },
  { hoTen: "LÊ THỊ MỸ DUYÊN", gioiTinh: "Nữ", cccd: "075301004821", noiTT: "Xã Nghĩa Trung, TP Đồng Nai", ttMap: "map", ttAnh: "photo", mau: "bg-rose-500", tick: true, tt: "cho" },
  { hoTen: "PHẠM QUỐC HUY", gioiTinh: "Nam", cccd: "070204006712", noiTT: "Xã Thọ Sơn, TP Đồng Nai", ttMap: "map", ttAnh: "no", mau: "bg-emerald-500", tick: true, tt: "cho" },
  { hoTen: "TRAN VAN HUNG", gioiTinh: "Nam", cccd: "070203007781", noiTT: "Xã Thọ Sơn, TP Đồng Nai", ttMap: "map", ttAnh: "photo", mau: "bg-teal-500", tick: false, tt: "cho", chinhTa: "Tên có thể thiếu dấu tiếng Việt — kiểm lại trước khi nạp (mức A)" },
  { hoTen: "ĐỖ VŨ BẢO ANH", gioiTinh: "Nam", cccd: "074207005570", noiTT: "P. Chánh Phú Hòa, TP Hồ Chí Minh", ttMap: "manual", ttAnh: "no", mau: "bg-amber-500", tick: false, trung: true, tt: "loi", loiLyDo: "Trùng CCCD với học viên đã có trong khóa (BR-005) — không nạp được" },
  { hoTen: "VÕ XUÂN LỘC", gioiTinh: "Nam", cccd: "070094000283", noiTT: "Xã Đông Phú, TP Đồng Nai", ttMap: "map", ttAnh: "photo", mau: "bg-violet-500", tick: false, tt: "nap" },
  { hoTen: "NGUYỄN NGỌC MAI", gioiTinh: "Nữ", cccd: "075301009912", noiTT: "Xã Phú Nghĩa, Tỉnh Đồng Nai", ttMap: "map", ttAnh: "photo", mau: "bg-sky-500", tick: false, tt: "nap" },
];

// Học viên đã có trong khóa (đọc từ DB thật qua usp_NguoiLX_Select_By_MaKH)
export const hocVienTrongKhoa: HocVienDB[] = [
  { soHS: "034", hoTen: "NGUYỄN THỊ HUỆ AN", gioiTinh: "Nữ", cccd: "072190003564", noiTT: "Xã Hảo Đước, Tỉnh Tây Ninh" },
  { soHS: "042", hoTen: "ĐỖ VŨ BẢO ANH", gioiTinh: "Nam", cccd: "074207005570", noiTT: "P. Chánh Phú Hòa, TP Hồ Chí Minh" },
  { soHS: "008", hoTen: "NGÔ NGUYỄN HOÀNG ANH", gioiTinh: "Nữ", cccd: "066301002217", noiTT: "Xã Krông Pắc, Tỉnh Đắk Lắk" },
  { soHS: "011", hoTen: "TRẦN TUẤN ANH", gioiTinh: "Nam", cccd: "054201004151", noiTT: "P. Tuy Hòa, Tỉnh Đắk Lắk" },
  { soHS: "036", hoTen: "NINH THỊ BÌNH", gioiTinh: "Nữ", cccd: "070191001352", noiTT: "Xã Nghĩa Trung, TP Đồng Nai" },
  { soHS: "055", hoTen: "BÙI TẤN ĐẠT", gioiTinh: "Nam", cccd: "070095010655", noiTT: "P. Đông Phú, TP Đồng Nai" },
  { soHS: "040", hoTen: "MÔ TRỌNG ĐẠT", gioiTinh: "Nam", cccd: "070207002892", noiTT: "Xã Nghĩa Trung, TP Đồng Nai" },
  { soHS: "045", hoTen: "ĐIỂU THỊ DUNG", gioiTinh: "Nữ", cccd: "070192001900", noiTT: "Xã Thọ Sơn, TP Đồng Nai" },
];

// Danh mục DVHC (DM_DVHC, TrangThai=1) — combobox địa chỉ. [MaDvhc, MaDVQL, Tên đầy đủ]
export const dmDvhc: [string, string, string][] = [
  ["25267", "75", "Xã Phú Nghĩa, Tỉnh Đồng Nai"],
  ["25270", "75", "Xã Nghĩa Trung, Tỉnh Đồng Nai"],
  ["25288", "75", "Xã Thọ Sơn, Tỉnh Đồng Nai"],
  ["25291", "75", "Phường Đông Phú, Tỉnh Đồng Nai"],
  ["26134", "79", "Phường Chánh Phú Hòa, TP Hồ Chí Minh"],
  ["22045", "80", "Phường Bình Minh, Tỉnh Tây Ninh"],
  ["08910", "66", "Xã Krông Pắc, Tỉnh Đắk Lắk"],
  ["12007", "37", "Xã Nho Quan, Tỉnh Ninh Bình"],
];

export const khoaOto = [
  "70004K26B010 — B-K149 (KG 28/08/2026) · chưa BC1",
  "70004K26B012 — C-K151 (KG 05/09/2026) · chưa BC1",
];
export const khoaMoto = [
  "70004K26A011 — A1-K33 (KG 12/09/2026) · chưa BC1",
  "70004K26A012 — A-K34 (KG 20/09/2026) · chưa BC1",
];

// Khóa cho chế độ Tra cứu DB (CHANGES #6): hiện MỌI khóa kể cả đã BC1 (bc1=true → 🔒 chỉ xem)
export interface KhoaTraCuu {
  ma: string;
  ten: string;
  kg: string; // ngày khai giảng dd/mm/yyyy
  siSo: number;
  bc1: boolean; // đã lập BC1 → chỉ xem, chặn sửa (BR-012)
  loai: "oto" | "moto";
}
export const khoaTraCuu: KhoaTraCuu[] = [
  { ma: "70004K26B010", ten: "B-K149", kg: "28/08/2026", siSo: 55, bc1: false, loai: "oto" },
  { ma: "70004K26B012", ten: "C-K151", kg: "05/09/2026", siSo: 48, bc1: false, loai: "oto" },
  { ma: "70004K25B041", ten: "B-K118", kg: "10/11/2025", siSo: 60, bc1: true, loai: "oto" },
  { ma: "70004K26A011", ten: "A1-K33", kg: "12/09/2026", siSo: 40, bc1: false, loai: "moto" },
  { ma: "70004K25A007", ten: "A-K28", kg: "02/06/2025", siSo: 52, bc1: true, loai: "moto" },
];

// Danh mục hạng đào tạo (DM_HangDT) — dữ liệu mẫu; thật đọc từ DB. Tuổi + thời gian auto theo hạng.
export interface HangDaoTao {
  ma: string;
  ten: string;
  hangGPLX: string;
  tuoiToiThieu: number;
  thoiGian: string;
  loai: "moto" | "oto";
}
// Hồ sơ nhân viên tuyển sinh (Trần Thị Hoa) đã quét/gửi lên VPS — app web "Đã gửi" (THU-02)
export interface HoSoDaGui {
  hoTen: string;
  gioiTinh: "Nam" | "Nữ";
  cccd: string;
  ngaySinh: string; // dd/mm/yyyy
  noiTT: string;
  ngayGui: string; // dd/mm/yyyy HH:mm
  trangThai: "pending" | "imported"; // chờ nạp / đã nạp
  mau: string;
}
export const hoSoDaGui: HoSoDaGui[] = [
  { hoTen: "NGUYỄN THANH TÂM", gioiTinh: "Nam", cccd: "070202008455", ngaySinh: "21/11/2002", noiTT: "Xã Phú Nghĩa, Tỉnh Bình Phước", ngayGui: "30/09/2026 08:12", trangThai: "pending", mau: "bg-blue-500" },
  { hoTen: "LÊ THỊ MỸ DUYÊN", gioiTinh: "Nữ", cccd: "075301004821", ngaySinh: "03/05/2003", noiTT: "Xã Nghĩa Trung, Tỉnh Đồng Nai", ngayGui: "30/09/2026 08:20", trangThai: "pending", mau: "bg-rose-500" },
  { hoTen: "PHẠM QUỐC HUY", gioiTinh: "Nam", cccd: "070204006712", ngaySinh: "17/07/2004", noiTT: "Xã Thọ Sơn, Tỉnh Đồng Nai", ngayGui: "30/09/2026 08:31", trangThai: "pending", mau: "bg-emerald-500" },
  { hoTen: "NGÔ NGUYỄN HOÀNG ANH", gioiTinh: "Nữ", cccd: "066301002217", ngaySinh: "15/05/2001", noiTT: "Xã Krông Pắc, Tỉnh Đắk Lắk", ngayGui: "29/09/2026 16:45", trangThai: "imported", mau: "bg-violet-500" },
  { hoTen: "TRẦN TUẤN ANH", gioiTinh: "Nam", cccd: "054201004151", ngaySinh: "05/06/2001", noiTT: "Phường Tuy Hòa, Tỉnh Đắk Lắk", ngayGui: "29/09/2026 16:52", trangThai: "imported", mau: "bg-amber-500" },
  { hoTen: "NINH THỊ BÌNH", gioiTinh: "Nữ", cccd: "070191001352", ngaySinh: "20/10/1991", noiTT: "Xã Nghĩa Trung, Tỉnh Đồng Nai", ngayGui: "29/09/2026 17:03", trangThai: "imported", mau: "bg-sky-500" },
];

export const dmHangDT: HangDaoTao[] = [
  { ma: "A1", ten: "A1 — Mô tô đến 125cc", hangGPLX: "A1", tuoiToiThieu: 18, thoiGian: "12 ngày", loai: "moto" },
  { ma: "A", ten: "A — Mô tô trên 125cc", hangGPLX: "A", tuoiToiThieu: 18, thoiGian: "12 ngày", loai: "moto" },
  { ma: "B", ten: "B — Ô tô đến 8 chỗ", hangGPLX: "B1", tuoiToiThieu: 18, thoiGian: "3 tháng", loai: "oto" },
  { ma: "C", ten: "C — Ô tô tải", hangGPLX: "C", tuoiToiThieu: 21, thoiGian: "5 tháng", loai: "oto" },
];
