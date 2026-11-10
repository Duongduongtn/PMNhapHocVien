// A6 (10/11/2026) — thông tin bắt buộc của hồ sơ kéo về trước khi nạp: họ tên, ngày sinh, giới tính.
// Thiếu thì dòng "chưa sẵn sàng" + lý do, không lặng lẽ loại khỏi lô hay ghi mặc định "Nam".

/** Giới tính để nạp: lấy giá trị app web gửi ('M'/'F'); trống mà có CCCD 12 số thì suy từ chữ số thứ 4
 *  (chẵn = Nam, lẻ = Nữ — mã thế kỷ/giới tính của căn cước). Không suy được → null (chưa sẵn sàng). */
export function gioiTinhNap(gioiTinh: string | null | undefined, soCccd: string | null | undefined): "M" | "F" | null {
  if (gioiTinh === "M" || gioiTinh === "F") return gioiTinh;
  const so = (soCccd || "").trim();
  if (!/^\d{12}$/.test(so)) return null;
  return Number(so[3]) % 2 === 0 ? "M" : "F";
}

/** Các mục thông tin còn thiếu (sửa trên app web): "họ tên", "ngày sinh", "giới tính". */
export function thieuThongTin(r: { ho_ten?: string | null; ngay_sinh?: string | null; gioi_tinh?: string | null; so_cccd?: string | null }): string[] {
  const t: string[] = [];
  if (!(r.ho_ten || "").trim()) t.push("họ tên");
  if (!(r.ngay_sinh || "").trim()) t.push("ngày sinh");
  if (!gioiTinhNap(r.gioi_tinh, r.so_cccd)) t.push("giới tính");
  return t;
}
