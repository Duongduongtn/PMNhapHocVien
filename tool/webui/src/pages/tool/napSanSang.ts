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

// NAP-09 (CHANGES #102) — tuổi học viên so với tuổi tối thiểu của hạng đào tạo, tính tại ngày nạp (hôm nay).
export interface KetQuaTuoi {
  du: boolean;
  tuoi: number;          // tuổi tròn tại ngày tính
  ngayDuTuoi: string;    // yyyymmdd — ngày bắt đầu đủ tuổi tối thiểu
  conThieuNgay: number;  // 0 nếu đã đủ
}

const ymd = (d: Date) => `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}${String(d.getDate()).padStart(2, "0")}`;

/** Ngày sinh yyyymmdd hỏng → null (không kiểm được — thiếu ngày sinh đã có luật riêng BUG-24).
 *  Ngày đủ tuổi = cùng ngày/tháng sinh của (năm sinh + tuổi); sinh 29/02 mà năm đó không nhuận → 01/03. */
export function kiemTuoi(ngaySinh: string | null | undefined, tuoiToiThieu: number, homNay: Date): KetQuaTuoi | null {
  const m = (ngaySinh || "").match(/^(\d{4})(\d{2})(\d{2})$/);
  if (!m) return null;
  const [y, mo, d] = [Number(m[1]), Number(m[2]), Number(m[3])];
  const sinh = new Date(y, mo - 1, d);
  if (sinh.getFullYear() !== y || sinh.getMonth() !== mo - 1 || sinh.getDate() !== d) return null;
  const duTuoi = new Date(y + tuoiToiThieu, mo - 1, d); // 29/02 năm không nhuận → JS tự lăn sang 01/03
  const hom = new Date(homNay.getFullYear(), homNay.getMonth(), homNay.getDate());
  let tuoi = hom.getFullYear() - y;
  if (hom.getMonth() < mo - 1 || (hom.getMonth() === mo - 1 && hom.getDate() < d)) tuoi -= 1;
  const conThieuNgay = Math.max(0, Math.round((duTuoi.getTime() - hom.getTime()) / 86_400_000));
  return { du: hom >= duTuoi, tuoi, ngayDuTuoi: ymd(duTuoi), conThieuNgay };
}

/** "45 ngày" dưới 3 tháng; từ 3 tháng: "1 năm 3 tháng" / "5 tháng". */
export function chuConThieu(ngay: number): string {
  if (ngay < 90) return `${ngay} ngày`;
  const thang = Math.max(3, Math.floor(ngay / 30.44)); // từ 90 ngày trở lên luôn ≥ "3 tháng", khớp ngưỡng màu
  const nam = Math.floor(thang / 12);
  const du = thang % 12;
  return nam ? `${nam} năm${du ? ` ${du} tháng` : ""}` : `${thang} tháng`;
}
