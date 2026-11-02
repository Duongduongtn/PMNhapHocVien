import { boDau } from "./text";
import { laNgayCoThat } from "./qr";

export interface LuaChon { ma: string; ten: string; khop: string[] }

// "GPLX đã có" ở app web (THU-07, TDD §10.6). Phản chiếu tool/webui/src/pages/tool/gplxDaCo.ts.
// `hang` luôn là MÃ DM_HangGPLX; `nhom` chỉ để hiện lại đúng nhãn (mã trùng giữa hai nhóm luật).

export type NhomLuat = "moi" | "cu";

// Ngày trong state form là dd/mm/yyyy (ô ODate); gửi server là yyyymmdd.
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

// khop: chữ người dùng gõ để tìm. Ô Hạng không tìm trong "luật mới/cũ", nếu không gõ A khớp mọi dòng.
export const DS_HANG_GPLX: LuaChon[] = [
  ...LUAT_MOI.map(([ma, ten]) => ({ ma: `moi:${ma}`, ten: `${ten} — luật mới`, khop: [ten] })),
  ...LUAT_CU.map(([ma, ten]) => ({ ma: `cu:${ma}`, ten: `${ten} — luật cũ`, khop: [ten] })),
];

// Bản chụp DM_DonViGTVT cấp Sở (DB Nạp, 02/11/2026), nguồn phần mềm cũ dùng in tờ khai; app web không đọc được SQL Server.
// Mã 00 đặt tên Cục QLHC theo scripts/them_cuc_qlhc_dm_donvigtvt.sql.
const NOI_CAP: [string, string][] = [
  ["00", "Cục QLHC"], ["01", "Hà Nội"], ["02", "Hà Giang"], ["04", "Cao Bằng"], ["06", "Bắc Kạn"], ["08", "Tuyên Quang"],
  ["10", "Lào Cai"], ["11", "Điện Biên"], ["12", "Lai Châu"], ["14", "Sơn La"], ["15", "Yên Bái"], ["17", "Hoà Bình"], ["19", "Thái Nguyên"],
  ["20", "Lạng Sơn"], ["22", "Quảng Ninh"], ["24", "Bắc Giang"], ["25", "Phú Thọ"], ["26", "Vĩnh Phúc"], ["27", "Bắc Ninh"], ["30", "Hải Dương"],
  ["31", "Hải Phòng"], ["33", "Hưng Yên"], ["34", "Thái Bình"], ["35", "Hà Nam"], ["36", "Nam Định"], ["37", "Ninh Bình"], ["38", "Thanh Hóa"],
  ["40", "Nghệ An"], ["42", "Hà Tĩnh"], ["44", "Quảng Bình"], ["45", "Quảng Trị"], ["46", "Thừa Thiên Huế"], ["48", "Đà Nẵng"], ["49", "Quảng Nam"],
  ["51", "Quảng Ngãi"], ["52", "Bình Định"], ["54", "Phú Yên"], ["56", "Khánh Hoà"], ["58", "Ninh Thuận"], ["60", "Bình Thuận"], ["62", "Kon Tum"],
  ["64", "Gia Lai"], ["66", "Đắk Lắk"], ["67", "Đắk Nông"], ["68", "Lâm Đồng"], ["70", "Bình Phước"], ["72", "Tây Ninh"], ["74", "Bình Dương"],
  ["75", "Đồng Nai"], ["77", "Bà Rịa - Vũng Tàu"], ["79", "Hồ Chí Minh"], ["80", "Long An"], ["82", "Tiền Giang"], ["83", "Bến Tre"], ["84", "Trà Vinh"],
  ["86", "Vĩnh Long"], ["87", "Đồng Tháp"], ["89", "An Giang"], ["91", "Kiên Giang"], ["92", "Cần Thơ"], ["93", "Hậu Giang"], ["94", "Sóc Trăng"],
  ["95", "Bạc Liêu"], ["96", "Cà Mau"], ["99", "Tổng cục đường bộ Việt Nam"],
];
export const DS_NOI_CAP_GPLX: LuaChon[] = NOI_CAP.map(([ma, ten]) => ({ ma, ten: `${ma} — ${ten}`, khop: [ma, ten] }));

const trungKhop = (o: LuaChon, t: string) => o.khop.some((k) => boDau(k) === t);

/** Danh sách theo chữ đang gõ, dòng trùng khớp đứng đầu. */
export function locLuaChon(ds: LuaChon[], q: string): LuaChon[] {
  const t = boDau(q);
  if (!t) return ds;
  return [
    ...ds.filter((o) => trungKhop(o, t)),
    ...ds.filter((o) => !trungKhop(o, t) && o.khop.some((k) => boDau(k).includes(t))),
  ];
}

/** Enter chỉ chọn khi chỉ còn đúng một khả năng; còn lại trả null để người nhập tự chọn (BUG-17). */
export function chonKhiEnter(ds: LuaChon[], q: string): string | null {
  const t = boDau(q);
  if (!t) return null;
  const trung = ds.filter((o) => trungKhop(o, t));
  if (trung.length) return trung.length === 1 ? trung[0].ma : null;
  const loc = locLuaChon(ds, q);
  return loc.length === 1 ? loc[0].ma : null;
}

export const bangMoi = (): BangGplx => ({ nhom: "cu", hang: "", so: "", ngay_tt: "", ngay_cap: "", ngay_hh: "", don_vi: "" });
export const khoaHang = (b: BangGplx) => (b.hang ? `${b.nhom}:${b.hang}` : "");

export function tachKhoaHang(khoa: string): Pick<BangGplx, "nhom" | "hang"> {
  const [nhom, hang] = khoa.split(":");
  return { nhom: nhom === "moi" ? "moi" : "cu", hang: hang ?? "" };
}

export function tenHang(b: Pick<BangGplx, "nhom" | "hang">): string {
  return (b.nhom === "moi" ? LUAT_MOI : LUAT_CU).find(([ma]) => ma === b.hang)?.[1] ?? b.hang;
}

export const laBangMoTo = (hang: string) => /^A/.test(hang);

const NGAY = ["ngay_tt", "ngay_cap", "ngay_hh"] as const;

function vnToYmd(v: string): string {
  const m = (v || "").trim().match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  return m && laNgayCoThat(v) ? `${m[3]}${m[2]}${m[1]}` : "";
}

/** Dữ liệu server (ngày yyyymmdd) → state form. */
export function tuServer(ds: Partial<BangGplx>[] | null | undefined): BangGplx[] {
  return (ds ?? []).map((x) => {
    const b = { ...bangMoi(), ...x };
    for (const f of NGAY) b[f] = /^\d{8}$/.test(b[f]) ? `${b[f].slice(6, 8)}/${b[f].slice(4, 6)}/${b[f].slice(0, 4)}` : "";
    return b;
  });
}

/** State form → dữ liệu gửi server. Bằng mô tô không có thời hạn nên không gửi ngày hết hạn. */
export function sangServer(ds: BangGplx[]): BangGplx[] {
  return ds.map((b) => {
    const r = { ...b, so: b.so.trim(), don_vi: b.don_vi.trim() };
    for (const f of NGAY) r[f] = vnToYmd(b[f]);
    if (laBangMoTo(b.hang)) r.ngay_hh = "";
    return r;
  });
}

export const soGplxLa = (so: string) => so.trim() !== "" && !/^\d{12}$/.test(so.trim());

export type OGplx = "hang" | "so" | "ngay_tt" | "ngay_cap" | "ngay_hh";

/** Lỗi chặn gửi của 1 bằng kèm ô gây lỗi, để form chỉ báo ô đã rời và đưa con trỏ tới đúng ô. */
export function loiTungO(b: BangGplx): { o: OGplx; loi: string }[] {
  const ds: { o: OGplx; loi: string }[] = [];
  if (!b.hang) ds.push({ o: "hang", loi: "Chưa chọn hạng" });
  if (!b.so.trim()) ds.push({ o: "so", loi: "Chưa nhập số GPLX" });
  if (!b.ngay_tt.trim()) ds.push({ o: "ngay_tt", loi: "Chưa nhập ngày trúng tuyển" });
  if (!b.ngay_cap.trim()) ds.push({ o: "ngay_cap", loi: "Chưa nhập ngày cấp" });
  const ten = { ngay_tt: "Ngày trúng tuyển", ngay_cap: "Ngày cấp", ngay_hh: "Ngày hết hạn" } as const;
  for (const f of NGAY) {
    if (f === "ngay_hh" && laBangMoTo(b.hang)) continue;
    if (b[f].trim() && !vnToYmd(b[f])) ds.push({ o: f, loi: `${ten[f]} chưa đúng dd/mm/yyyy` });
  }
  const [tt, cap, hh] = [vnToYmd(b.ngay_tt), vnToYmd(b.ngay_cap), laBangMoTo(b.hang) ? "" : vnToYmd(b.ngay_hh)];
  if (tt && cap && cap < tt) ds.push({ o: "ngay_cap", loi: "Ngày cấp phải sau ngày trúng tuyển" });
  if (cap && hh && hh <= cap) ds.push({ o: "ngay_hh", loi: "Ngày hết hạn phải sau ngày cấp" });
  return ds;
}

/** Lỗi chặn gửi của 1 bằng; rỗng = hợp lệ. */
export function loiBang(b: BangGplx): string[] {
  return loiTungO(b).map((x) => x.loi);
}

/** Tên `data-o` của ô sai đầu tiên trong khối GPLX; null = hợp lệ. */
export function oSaiDau(ds: BangGplx[]): string | null {
  for (let i = 0; i < ds.length; i++) {
    const l = loiTungO(ds[i]);
    if (l.length) return `gplx-${i}-${l[0].o}`;
  }
  return null;
}

/** Lỗi của cả danh sách, dùng khi bấm gửi/lưu; null = hợp lệ. */
export function loiDanhSach(ds: BangGplx[]): string | null {
  for (let i = 0; i < ds.length; i++) {
    const l = loiBang(ds[i]);
    if (l.length) return `GPLX đã có, bằng ${i + 1}: ${l.join(", ")}.`;
  }
  return null;
}
