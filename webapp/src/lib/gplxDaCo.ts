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

export const DS_HANG_GPLX = [
  ...LUAT_MOI.map(([ma, ten]) => ({ ma: `moi:${ma}`, ten: `${ten} — luật mới` })),
  ...LUAT_CU.map(([ma, ten]) => ({ ma: `cu:${ma}`, ten: `${ten} — luật cũ` })),
];

// Bản chụp DM_DVHC mã 2 ký tự (DB Nạp, 02/11/2026) vì app web không đọc được SQL Server. Tool đọc trực tiếp từ DB.
// Cờ 1 = tỉnh trước sáp nhập; bằng cũ cấp từ các tỉnh này nên vẫn phải chọn được. Tên trùng khác mã nên hiện kèm mã.
const NOI_CAP: [string, string, 1?][] = [
  ["00", "Cục QLHC"], ["99", "Cục ĐBVN"], ["01", "Hà Nội"], ["02", "Hà Giang", 1], ["04", "Cao Bằng"], ["06", "Bắc Kạn", 1],
  ["08", "Tuyên Quang"], ["10", "Lào Cai", 1], ["11", "Điện Biên"], ["12", "Lai Châu"], ["14", "Sơn La"], ["15", "Lào Cai"],
  ["17", "Hòa Bình", 1], ["19", "Thái Nguyên"], ["20", "Lạng Sơn"], ["22", "Quảng Ninh"], ["24", "Bắc Ninh"], ["25", "Phú Thọ"],
  ["26", "Vĩnh Phúc", 1], ["27", "Bắc Ninh", 1], ["30", "Hải Dương", 1], ["31", "Hải Phòng"], ["33", "Hưng Yên"], ["34", "Thái Bình", 1],
  ["35", "Hà Nam", 1], ["36", "Nam Định", 1], ["37", "Ninh Bình"], ["38", "Thanh Hóa"], ["40", "Nghệ An"], ["42", "Hà Tĩnh"],
  ["44", "Quảng Trị"], ["45", "Quảng Trị", 1], ["46", "Thừa Thiên Huế"], ["48", "Đà Nẵng"], ["49", "Quảng Nam", 1], ["51", "Quảng Ngãi"],
  ["52", "Gia Lai"], ["54", "Phú Yên", 1], ["56", "Khánh Hòa"], ["58", "Ninh Thuận", 1], ["60", "Bình Thuận", 1], ["62", "Kon Tum", 1],
  ["64", "Gia Lai", 1], ["66", "Đắk Lắk"], ["67", "Đắk Nông", 1], ["68", "Lâm Đồng"], ["70", "Bình Phước", 1], ["72", "Tây Ninh", 1],
  ["74", "Bình Dương", 1], ["75", "Đồng Nai"], ["77", "Bà Rịa - Vũng Tàu", 1], ["79", "Hồ Chí Minh"], ["80", "Tây Ninh"], ["82", "Đồng Tháp"],
  ["83", "Bến Tre", 1], ["84", "Trà Vinh", 1], ["86", "Vĩnh Long"], ["87", "Đồng Tháp", 1], ["89", "An Giang", 1], ["91", "An Giang"],
  ["92", "Cần Thơ"], ["93", "Hậu Giang", 1], ["94", "Sóc Trăng", 1], ["95", "Bạc Liêu", 1], ["96", "Cà Mau"],
];
export const DS_NOI_CAP_GPLX = NOI_CAP.map(([ma, ten, cu]) => ({ ma, ten: `${ma} — ${ten}${cu ? " (trước sáp nhập)" : ""}` }));

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
  return m ? `${m[3]}${m[2]}${m[1]}` : "";
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

/** Lỗi chặn gửi của 1 bằng; rỗng = hợp lệ. */
export function loiBang(b: BangGplx): string[] {
  const loi: string[] = [];
  if (!b.hang) loi.push("Chưa chọn hạng");
  if (!b.so.trim()) loi.push("Chưa nhập số GPLX");
  const ten = { ngay_tt: "Ngày trúng tuyển", ngay_cap: "Ngày cấp", ngay_hh: "Ngày hết hạn" } as const;
  for (const f of NGAY) {
    if (f === "ngay_hh" && laBangMoTo(b.hang)) continue;
    if (b[f].trim() && !vnToYmd(b[f])) loi.push(`${ten[f]} chưa đúng dd/mm/yyyy`);
  }
  return loi;
}

/** Lỗi của cả danh sách, dùng khi bấm gửi/lưu; null = hợp lệ. */
export function loiDanhSach(ds: BangGplx[]): string | null {
  for (let i = 0; i < ds.length; i++) {
    const l = loiBang(ds[i]);
    if (l.length) return `GPLX đã có, bằng ${i + 1}: ${l.join(", ")}.`;
  }
  return null;
}
