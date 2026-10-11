// Logic thuần cho bước ② lập BC2 (TNB-04): lọc tìm, gom thi lại theo khóa gốc. Không gọi mạng.
import { boDau } from "./format";
import type { HvUngVien } from "./tnbc2Api";

/** Khớp tên không dấu / CMT / mã đăng ký; rỗng = giữ tất cả. */
export function khopTim(h: Pick<HvUngVien, "ten" | "cmt" | "ma_dk">, q: string): boolean {
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

/** Giới hạn đầu vào của `khop-danh-sach` (khớp backend `kiem_danh_sach_dan`). */
export const TOI_DA_DONG_DAN = 5000;
export const TOI_DA_KY_TU_DONG = 40;

/**
 * Trích mã tra cứu từ văn bản dán từ Excel: mỗi dòng một mã. Dòng nhiều cột (tab) → lấy ô trông như CMT/CCCD
 * (9–12 chữ số), không có thì lấy ô đầu tiên khác rỗng. Bỏ dòng trống và dòng trùng (giữ thứ tự xuất hiện).
 */
export function trichMaTuVanBan(text: string): string[] {
  const thay = new Set<string>();
  const kq: string[] = [];
  for (const dong of text.split(/\r?\n/)) {
    const o = dong.split("\t").map((x) => x.trim()).filter((x) => x !== "");
    if (o.length === 0) continue;
    const ma = o.find((x) => /^\d{9,12}$/.test(x)) ?? o[0];
    const k = ma.toLowerCase();
    if (thay.has(k)) continue;
    thay.add(k);
    kq.push(ma);
  }
  return kq;
}

export function demDaChon(ds: HvUngVien[], sel: ReadonlySet<string>): number {
  let n = 0;
  for (const h of ds) if (sel.has(h.ma_dk)) n++;
  return n;
}
