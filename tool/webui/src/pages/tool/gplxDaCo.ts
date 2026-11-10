// "GPLX đã có" (NAP-07, TDD §10.6). Ghi vào 6 cột *DaCo qua SP gộp; nhiều bằng nối "|" ở backend.
// `hang` luôn là MÃ DM_HangGPLX; `nhom` chỉ để hiện lại đúng nhãn (mã trùng giữa hai nhóm luật).
import { ymdToVN } from "../../lib/format";

function vnToYmd(v: string): string {
  const m = (v || "").trim().match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  return m ? `${m[3]}${m[2]}${m[1]}` : "";
}

export type NhomLuat = "moi" | "cu";

// Ngày trong state UI là dd/mm/yyyy (ô ODate); gửi backend là yyyymmdd.
export interface BangGplx {
  nhom: NhomLuat;
  hang: string;
  so: string;
  ngay_tt: string;
  ngay_cap: string;
  ngay_hh: string;
  don_vi: string;
}

const LUAT_MOI: [string, string][] = [
  ["A1m", "A1"], ["A2", "A"], ["A01", "A.01"], ["A02", "A.02"], ["B1", "B"], ["B11", "B.01"],
  ["C1", "C1"], ["C", "C"], ["D1", "D1"], ["D", "D"],
];
const LUAT_CU: [string, string][] = [
  ["A1", "A1"], ["A2", "A2"], ["A3", "A3"], ["B11", "B1 số tự động"], ["B1", "B1"], ["B2", "B2"],
  ["C", "C"], ["D", "D"], ["E", "E"], ["FB2", "FB2"], ["FC", "FC"], ["FD", "FD"], ["FE", "FE"],
];

/** Lựa chọn cho ComboLoc: khóa `moi:B1` / `cu:B1` vì mã trùng giữa hai nhóm. Chỉ tìm theo tên hạng, không tìm trong "luật mới/cũ". */
export const DS_HANG_GPLX = [
  ...LUAT_MOI.map(([ma, ten]) => ({ ma: `moi:${ma}`, ten: `${ten} — luật mới`, khop: [ten] })),
  ...LUAT_CU.map(([ma, ten]) => ({ ma: `cu:${ma}`, ten: `${ten} — luật cũ`, khop: [ten] })),
];

export const bangMoi = (): BangGplx => ({ nhom: "cu", hang: "", so: "", ngay_tt: "", ngay_cap: "", ngay_hh: "", don_vi: "" });

export const khoaHang = (b: BangGplx) => (b.hang ? `${b.nhom}:${b.hang}` : "");

export function tachKhoaHang(khoa: string): Pick<BangGplx, "nhom" | "hang"> {
  const [nhom, hang] = khoa.split(":");
  return { nhom: nhom === "moi" ? "moi" : "cu", hang: hang ?? "" };
}

export function tenHang(b: { nhom: string; hang: string }): string {
  return (b.nhom === "moi" ? LUAT_MOI : LUAT_CU).find(([ma]) => ma === b.hang)?.[1] ?? b.hang;
}

export const laBangMoTo = (hang: string) => /^A/.test(hang);

/** Nơi cấp suy từ số GPLX: số đủ 12 chữ số thì 2 số đầu là mã Sở cấp (đúng ở 94% hồ sơ DB Nạp, 10/11/2026).
 *  Mã không có trong danh mục → "" (không đoán). Chỉ dùng để điền sẵn khi ô Nơi cấp đang trống, người nhập vẫn sửa được. */
export function suyNoiCapGplx(so: string, ds: { ma: string }[]): string {
  const t = (so || "").trim();
  if (!/^\d{12}$/.test(t)) return "";
  const ma = t.slice(0, 2);
  return ds.some((o) => o.ma === ma) ? ma : "";
}

/** Nơi cấp sau khi sửa số GPLX: ô đang trống, hoặc đang đúng giá trị đã tự điền theo số cũ → theo số mới.
 *  Nơi cấp người nhập chọn khác đi thì giữ nguyên. */
export function noiCapKhiDoiSo(soCu: string, soMoi: string, donVi: string, ds: { ma: string }[]): string {
  const tuDien = !donVi.trim() || donVi === suyNoiCapGplx(soCu, ds);
  return tuDien ? suyNoiCapGplx(soMoi, ds) : donVi;
}

/** Điền sẵn nơi cấp cho mọi bằng đang trống nơi cấp mà suy được từ số. Không đổi gì → trả đúng mảng cũ. */
export function dienNoiCapTheoSo<T extends { so: string; don_vi: string }>(ds: T[], noiCap: { ma: string }[]): T[] {
  let doi = false;
  const kq = ds.map((b) => {
    if (b.don_vi.trim()) return b;
    const ma = suyNoiCapGplx(b.so, noiCap);
    if (!ma) return b;
    doi = true;
    return { ...b, don_vi: ma };
  });
  return doi ? kq : ds;
}

const NGAY_FIELDS = ["ngay_tt", "ngay_cap", "ngay_hh"] as const;

/** Chuỗi JSON (nháp / keo_ve, ngày yyyymmdd) → state UI. Rỗng hoặc hỏng → []. */
export function docBang(json: string | null | undefined): BangGplx[] {
  if (!json) return [];
  try {
    const ds = JSON.parse(json);
    if (!Array.isArray(ds)) return [];
    return ds.map((x) => {
      const b = { ...bangMoi(), ...x } as BangGplx;
      for (const f of NGAY_FIELDS) b[f] = /^\d{8}$/.test(b[f] ?? "") ? ymdToVN(b[f]) : b[f] ?? "";
      return b;
    });
  } catch {
    return [];
  }
}

/** State UI → dữ liệu gửi backend. Ngày gõ chưa đủ giữ nguyên để nháp không mất, lúc nạp server sẽ báo lỗi. */
export function gomBang(ds: BangGplx[]): BangGplx[] {
  return ds.map((b) => {
    const r = { ...b, so: b.so.trim(), don_vi: b.don_vi.trim() };
    for (const f of NGAY_FIELDS) r[f] = vnToYmd(b[f]) || b[f].trim();
    // Bằng mô tô không có thời hạn: đổi hạng sang mô tô thì ô Hết hạn đã ẩn, không gửi giá trị cũ.
    if (laBangMoTo(b.hang)) r.ngay_hh = "";
    return r;
  });
}

// Trùng danh sách trong usf_BaBT_GetMaNoidungSathach (dò CHARINDEX): B1*, B2, C*, D*, E, F*.
const HANG_MIEN = /B1|B2|C|D|E|FB2|FC|FD|FE/;
const KHOA_MIEN = ["A1", "Am", "A1m"];

export const duocMienLyThuyet = (hangKhoa: string | null | undefined, ds: BangGplx[]) =>
  KHOA_MIEN.includes((hangKhoa ?? "").trim()) && ds.some((b) => HANG_MIEN.test(b.hang));

export const trungHangDangKy = (hangKhoa: string | null | undefined, ds: BangGplx[]) =>
  !!hangKhoa && ds.some((b) => b.hang === hangKhoa.trim());

export const soGplxLa = (so: string) => so.trim() !== "" && !/^\d{12}$/.test(so.trim());

/** Lỗi chặn nạp của 1 bằng (server kiểm lại lần nữa); rỗng = hợp lệ. */
export function loiBang(b: BangGplx): string[] {
  const loi: string[] = [];
  if (!b.hang) loi.push("Chưa chọn hạng");
  if (!b.so.trim()) loi.push("Chưa nhập số GPLX");
  if (!b.ngay_tt.trim()) loi.push("Chưa nhập ngày trúng tuyển");
  if (!b.ngay_cap.trim()) loi.push("Chưa nhập ngày cấp");
  const ten = { ngay_tt: "Ngày trúng tuyển", ngay_cap: "Ngày cấp", ngay_hh: "Ngày hết hạn" } as const;
  for (const f of NGAY_FIELDS) {
    if (f === "ngay_hh" && laBangMoTo(b.hang)) continue;
    if (b[f].trim() && !vnToYmd(b[f])) loi.push(`${ten[f]} chưa đúng dd/mm/yyyy`);
  }
  const [tt, cap, hh] = [vnToYmd(b.ngay_tt), vnToYmd(b.ngay_cap), laBangMoTo(b.hang) ? "" : vnToYmd(b.ngay_hh)];
  if (tt && cap && cap < tt) loi.push("Ngày cấp phải sau ngày trúng tuyển");
  if (cap && hh && hh <= cap) loi.push("Ngày hết hạn phải sau ngày cấp");
  return loi;
}

/** Bằng chưa nhập ô nào (mở popup rồi bấm Xong luôn) → coi như không có. */
export const bangTrong = (b: BangGplx) => !b.hang && !b.so.trim() && !b.ngay_tt && !b.ngay_cap && !b.ngay_hh && !b.don_vi.trim();

/** Một dòng tóm tắt cho mỗi bằng ở ngăn Chuẩn bị (khối nhập nằm trong popup): "B2 · 790000000123 · Hồ Chí Minh". */
export function tomTatGplx(ds: BangGplx[], noiCap: { ma: string; ten: string }[]): string[] {
  return ds.filter((b) => !bangTrong(b)).map((b) => {
    const tinh = noiCap.find((o) => o.ma === b.don_vi)?.ten.split(" — ")[1] ?? b.don_vi;
    return [b.hang ? tenHang(b) : "Chưa chọn hạng", b.so.trim(), tinh].filter(Boolean).join(" · ");
  });
}

/** Chữ trên badge dòng danh sách: tối đa 2 hạng, còn lại "+n" — "B2·A1 +1". */
export function nhanHangGon(ds: BangGplx[]): string {
  const h = ds.filter((b) => !bangTrong(b)).map((b) => tenHang(b) || "?");
  return h.slice(0, 2).join("·") + (h.length > 2 ? ` +${h.length - 2}` : "");
}
