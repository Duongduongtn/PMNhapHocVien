// Logic thuần cho bước ② lập BC2 (TNB-04): lọc tìm, gom thi lại theo khóa gốc. Không gọi mạng.
import { boDau } from "./format";
import type { HvUngVien } from "./tnbc2Api";

/** Khớp tên không dấu / CMT / mã đăng ký; rỗng = giữ tất cả. */
export function khopTim(h: HvUngVien, q: string): boolean {
  const t = q.trim();
  if (!t) return true;
  const k = boDau(t);
  return boDau(h.ten).includes(k) || h.cmt.includes(t) || h.ma_dk.toLowerCase().includes(t.toLowerCase());
}

export interface KhoaGoc {
  ma_kh: string;
  ten_kh: string;
  bg: string;
  tuoi_thang: number | null;
  hocVien: HvUngVien[];
}

/** Gom HV theo khóa gốc, khóa bế giảng gần nhất lên đầu. */
export function gomTheoKhoaGoc(ds: HvUngVien[]): KhoaGoc[] {
  const m = new Map<string, KhoaGoc>();
  for (const h of ds) {
    let k = m.get(h.ma_kh);
    if (!k) {
      k = { ma_kh: h.ma_kh, ten_kh: h.ten_kh || h.ma_kh, bg: h.bg, tuoi_thang: h.tuoi_thang, hocVien: [] };
      m.set(h.ma_kh, k);
    }
    k.hocVien.push(h);
  }
  return [...m.values()].sort((a, b) => b.bg.localeCompare(a.bg));
}

export function demDaChon(ds: HvUngVien[], sel: ReadonlySet<string>): number {
  let n = 0;
  for (const h of ds) if (sel.has(h.ma_dk)) n++;
  return n;
}
