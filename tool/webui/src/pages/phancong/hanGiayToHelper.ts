// PCG-06 (task 122) — hàm thuần cho tab "Hạn giấy tờ" (nhãn + tổng hợp). Dữ liệu từ GET /local/phancong/han-giay-to.
import type { HanGiayToPC } from "../../lib/api";

export const TEN_GIAY: Record<string, string> = {
  gpxtl: "Giấy phép xe tập lái",
  gcnkd: "Giấy chứng nhận kiểm định",
  gplx: "GPLX giáo viên",
};

// "Quá hạn 14 ngày" / "Hết hạn hôm nay" / "Còn 8 ngày"  (con_ngay âm = đã quá hạn)
export function nhanHan(conNgay: number): string {
  if (conNgay < 0) return `Quá hạn ${-conNgay} ngày`;
  if (conNgay === 0) return "Hết hạn hôm nay";
  return `Còn ${conNgay} ngày`;
}

export interface TongHopHan {
  xe: { het: number; sap: number };
  gv: { het: number; sap: number };
  ngung: number;
  chuaKhai: number;
  tong: number; // số mục đỏ/vàng/ngưng — 0 và chuaKhai=0 thì không có gì để hiện
}

export function tongHop(r: HanGiayToPC): TongHopHan {
  const xe = { het: r.xe.het_han.length, sap: r.xe.sap_het.length };
  const gv = { het: r.gv.het_han.length, sap: r.gv.sap_het.length };
  const ngung = r.ngung.xe.length + r.ngung.gv.length;
  const chuaKhai = r.xe.chua_khai.length + r.gv.chua_khai.length;
  return { xe, gv, ngung, chuaKhai, tong: xe.het + xe.sap + gv.het + gv.sap + ngung };
}

// Xếp theo ngày hết hạn sớm nhất của dòng (quá hạn lâu nhất lên trên).
export function sapXepTheoHan<T extends { giay: { ngay: string }[] }>(ds: T[]): T[] {
  const sớm = (d: T) => d.giay.reduce((m, g) => (g.ngay < m ? g.ngay : m), "9999-12-31");
  return [...ds].sort((a, b) => sớm(a).localeCompare(sớm(b)));
}
