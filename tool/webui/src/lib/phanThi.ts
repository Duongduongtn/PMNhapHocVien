// In BC2 (TNB-08) — phần logic thuần của màn chọn phần thi. Tên mục (Ghi chú khi in) do SERVER tính
// (`tn_bc2_phan_thi.py`) — ở đây chỉ đổi tập phần thi và gom/đếm, không nhân bản bảng mục.
import type { HvBanIn } from "./tnbc2Api";

/** Bật/tắt một phần: ô đang "phải thi" → thành "đã đạt" và ngược lại. Trả tập phải thi mới theo thứ tự của hạng. */
export function doiPhan(h: Pick<HvBanIn, "phan" | "phai_thi">, p: string): string[] {
  const co = h.phai_thi.includes(p);
  const moi = co ? h.phai_thi.filter((x) => x !== p) : [...h.phai_thi, p];
  return h.phan.filter((x) => moi.includes(x));
}

/** Bộ ô chung ở thanh đáy: mọi HV đã chọn đang "đã đạt" phần p → bắt thi; ngược lại → đánh dấu đã đạt. */
export function doiPhanLoat(ds: HvBanIn[], p: string): { ma_dk: string; phai_thi: string[] }[] {
  const tatCaDat = ds.every((h) => !h.phai_thi.includes(p));
  return ds
    .filter((h) => h.phan.includes(p))
    .map((h) => {
      const moi = tatCaDat ? [...h.phai_thi, p] : h.phai_thi.filter((x) => x !== p);
      return { ma_dk: h.ma_dk, phai_thi: h.phan.filter((x) => moi.includes(x)) };
    });
}

/** Phần p của cả nhóm đang ở trạng thái nào: `dat` (mọi HV đã đạt) · `thi` (mọi HV phải thi) · `lan` (lẫn). */
export function trangThaiChung(ds: HvBanIn[], p: string): "dat" | "thi" | "lan" {
  const co = ds.filter((h) => h.phan.includes(p));
  if (co.length > 0 && co.every((h) => !h.phai_thi.includes(p))) return "dat";
  if (co.every((h) => h.phai_thi.includes(p))) return "thi";
  return "lan";
}

export type LocNoiDung = "tat" | "can" | "sua" | string;

/** Khóa nhóm đếm: cùng mục + cùng nhóm hạng (A3/A4 và ô tô có mã mục trùng nhau nhưng khác ký hiệu). */
export const khoaMuc = (h: HvBanIn): string => `${h.nhom}|${h.ma_nd}`;

export interface NhomDem {
  khoa: string;
  ten: string;
  phan: string[];
  phaiThi: string[];
  nhom: HvBanIn["nhom"];
  n: number;
}

/** Dải đếm theo nội dung thi (bỏ HV chưa có phần nào — đếm riêng "Chưa có phần thi"). */
export function demTheoMuc(ds: HvBanIn[]): { nhom: NhomDem[]; can: number; sua: number } {
  const map = new Map<string, NhomDem>();
  let can = 0;
  let sua = 0;
  for (const h of ds) {
    if (h.da_sua) sua++;
    if (h.ma_nd === null) {
      can++;
      continue;
    }
    const k = khoaMuc(h);
    const cu = map.get(k);
    if (cu) cu.n++;
    else map.set(k, { khoa: k, ten: h.ghi_chu, phan: h.phan, phaiThi: h.phai_thi, nhom: h.nhom, n: 1 });
  }
  return { nhom: [...map.values()].sort((a, b) => b.n - a.n), can, sua };
}

export function locHocVien(ds: HvBanIn[], loc: LocNoiDung, q: string): HvBanIn[] {
  const chuan = (s: string) => s.toLowerCase().replace(/ð/g, "đ");   // DB có thể trả Ð (U+00D0) thay cho Đ
  const t = chuan(q.trim());
  return ds.filter((h) => {
    if (t && !(chuan(h.ho_ten).includes(t) || h.so_cmt.includes(t))) return false;
    if (loc === "tat") return true;
    if (loc === "can") return h.ma_nd === null;
    if (loc === "sua") return h.da_sua;
    return khoaMuc(h) === loc;
  });
}

/** Ngày ghi nhận nguồn, dd/mm/yyyy ('' nếu không có). */
export const ngayNguon = (h: Pick<HvBanIn, "nguon_luc">): string =>
  h.nguon_luc ? h.nguon_luc.slice(0, 10).split("-").reverse().join("/") : "";

/** Chữ giải thích khi rê chuột lên một ô. */
export function chuGiaiO(h: HvBanIn, p: string, tenPhan: Record<string, string>): string {
  const ten = tenPhan[p] ?? p;
  if (h.phai_thi.includes(p)) return `${ten} — phải thi. Bấm nếu học viên đã đạt phần này.`;
  const goc = h.nguon === "chua_thi" ? "" : ` (${h.ten_nguon}${ngayNguon(h) ? ` · ${ngayNguon(h)}` : ""}${h.ma_ky_sh ? ` · kỳ ${h.ma_ky_sh}` : ""})`;
  return `${ten} — đã đạt${goc}. Bấm để bắt thi lại.`;
}

export const TEN_PHAN: Record<string, string> = { L: "Lý thuyết", H: "Sa hình", "Đ": "Đường", LT: "Lý thuyết", TH: "Thực hành" };
