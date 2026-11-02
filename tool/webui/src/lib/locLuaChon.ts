import { boDau } from "./format";

export interface LuaChon {
  ma: string;
  ten: string;
  khop?: string[]; // chữ dùng để tìm; bỏ trống thì lấy cả tên và từng phần, vd "79 — Hồ Chí Minh" tìm theo mã, tên, hoặc cả cụm
}

const khopCua = (o: LuaChon) => (o.khop ?? [o.ten, ...o.ten.split(" — ")]).map(boDau);

/** Danh sách theo chữ đang gõ, dòng trùng khớp đứng đầu. */
export function locLuaChon<T extends LuaChon>(ds: T[], q: string): T[] {
  const t = boDau(q);
  if (!t) return ds;
  const trung = (o: T) => khopCua(o).includes(t);
  return [...ds.filter(trung), ...ds.filter((o) => !trung(o) && khopCua(o).some((k) => k.includes(t)))];
}

/** Enter chỉ chọn khi chỉ còn đúng một khả năng; còn lại trả null để người nhập tự chọn (BUG-19). */
export function chonKhiEnter<T extends LuaChon>(ds: T[], q: string): T | null {
  const t = boDau(q);
  if (!t) return null;
  const trung = ds.filter((o) => khopCua(o).includes(t));
  if (trung.length) return trung.length === 1 ? trung[0] : null;
  const loc = locLuaChon(ds, q);
  return loc.length === 1 ? loc[0] : null;
}
