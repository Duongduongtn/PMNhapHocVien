// Gọi API Tốt nghiệp & Báo cáo 2 (TNB) — /local/tnbc2/*, TDD §11F.6. Ghi DB Nạp GPLX_CSDT.
// Mọi lệnh GHI cần `xac_nhan_csdl_that: true` (cổng chống bấm nhầm). Số BC2 có dấu `/`
// nên luôn `encodeURIComponent` khi ghép vào đường dẫn.
import { BASE, authHeaders } from "./api";

export type LoaiHang = "oto" | "moto";
/** Dữ liệu trả về: kiểu cụ thể được tinh chỉnh ở từng màn dùng nó (task 107–115). */
export type DuLieu = Record<string, unknown>;

/** Lỗi nghiệp vụ của server: `detail = {ma, noi_dung, ...}` (409 kèm `canh_bao[]`, `bo_qua[]`, `chan[]`…). */
export class LoiTnbc2 extends Error {
  ma: string;
  http: number;
  duLieu: DuLieu;
  constructor(ma: string, noiDung: string, http: number, duLieu: DuLieu = {}) {
    super(noiDung);
    this.ma = ma;
    this.http = http;
    this.duLieu = duLieu;
  }
}

type Query = Record<string, string | number | boolean | undefined>;

function qs(q?: Query): string {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(q ?? {})) if (v !== undefined && v !== "") p.set(k, String(v));
  const s = p.toString();
  return s ? `?${s}` : "";
}

async function goi<T = DuLieu>(
  method: string,
  duongDan: string,
  tuyChon: { query?: Query; body?: unknown } = {},
): Promise<T> {
  const coBody = tuyChon.body !== undefined;
  const r = await fetch(`${BASE}/local/tnbc2${duongDan}${qs(tuyChon.query)}`, {
    method,
    headers: authHeaders(coBody ? { "Content-Type": "application/json" } : undefined),
    body: coBody ? JSON.stringify(tuyChon.body) : undefined,
  });
  if (!r.ok) {
    const d = await r.json().catch(() => null);
    const detail = d?.detail;
    if (detail && typeof detail === "object" && !Array.isArray(detail)) {
      const { ma, noi_dung, ...conLai } = detail as DuLieu & { ma?: string; noi_dung?: string };
      throw new LoiTnbc2(String(ma ?? "loi"), String(noi_dung ?? `${r.status} ${r.statusText}`), r.status, conLai);
    }
    // 422 của pydantic: detail là mảng; hoặc lỗi 5xx không có JSON
    throw new LoiTnbc2("loi_he_thong", typeof detail === "string" ? detail : `${r.status} ${r.statusText}`, r.status);
  }
  return r.json() as Promise<T>;
}

/** Mã lô do client sinh mỗi lần xác nhận (8–64 ký tự chữ/số/gạch) — cùng `lo_id` gửi lại = không chạy đôi. */
export function taoLoId(): string {
  const u =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
  return u.replace(/[^A-Za-z0-9_-]/g, "").slice(0, 64);
}

// ── Tốt nghiệp (ô tô) ──
export interface DongTn { ma_dk: string; so_giay: string }
export interface ChungTn {
  so_so_tn: string;
  ngay_vao_so: string;
  so_quyet_dinh: string;
  ngay_ra_qd: string;
  ngay_in: string;
}

export interface KhoaTn {
  ma_kh: string;
  ten_kh: string;
  hang: string;
  ngay_kg: string | null;
  ngay_bg: string;
  ghi_duoc: boolean;
  khoa_cu: boolean;
  tong: number;
  chua_tot_nghiep: number;
  da_tot_nghiep: number;
  da_vao_bc2: number;
}
export interface KhoaTnResp {
  loai: string;
  hom_nay: string;
  moc_cua_so: string;
  khoa: KhoaTn[];
  so_giay_ke_tiep: string;
}

export type TrangThaiTn = "chua_tot_nghiep" | "da_tot_nghiep" | "da_vao_bc2" | "khac";
export interface HvTn {
  ma_dk: string;
  ten: string;
  ngay_sinh: string; // dd/mm/yyyy
  cmt: string;
  hang: string;
  tt: string;
  ma_bc2: string;
  ma_kh: string;
  so_giay: string;
  so_so_tn: string;
  ngay_vao_so: string;
  so_quyet_dinh: string;
  ngay_ra_qd: string;
  ngay_in: string;
  trang_thai_tn: TrangThaiTn;
  ten_trang_thai: string;
  khoa_cu: boolean;
  sua_duoc: boolean;
  ly_do_khoa: string;
}
export interface SoChungTn extends ChungTn {
  so_hv: number;
}
export interface HvTnResp {
  ma_kh: string;
  ten_kh: string;
  ngay_bg: string;
  ghi_duoc: boolean;
  khoa_cu: boolean;
  so_chung: SoChungTn | null;
  so_giay_ke_tiep: string;
  tong: number;
  dem: { chua_tot_nghiep: number; da_tot_nghiep: number; da_vao_bc2: number };
  hoc_vien: HvTn[];
}

export interface VanDeTn {
  muc: string;
  ma: string;
  noi_dung: string;
}
export type KetQuaDongTn =
  | "se_len_09"
  | "luu_so_truoc"
  | "giu_09_sua_thong_tin"
  | "khong_doi_trang_thai_da_vao_bc2"
  | "khong_doi"
  | "bo_qua"
  | "chan";
export interface DongXemLaiTn {
  ma_dk: string;
  ket_qua: KetQuaDongTn | string;
  ghi_duoc: boolean;
  chan: VanDeTn[];
  canh_bao: VanDeTn[];
  thong_tin: VanDeTn[];
}
export interface XemLaiTnResp {
  ma_kh: string;
  ghi_duoc_khoa: boolean;
  tong: number;
  dem: Record<string, number>;
  khoang_so: { tien_to: string; tu: number; den: number; so_luong: number } | null;
  co_chan: boolean;
  canh_bao: { ma: string; noi_dung: string; so_dong: number }[];
  dong: DongXemLaiTn[];
}

/** Tiến độ / kết quả của một lô (dùng chung `GET /bc2/lo/{lo_id}`). Trường kết quả chỉ có khi `xong`. */
export interface LoTn {
  lo_id: string;
  trang_thai: "dang_chay" | "xong" | "loi_giua_chung" | "that_bai" | string;
  xu_ly?: number;
  tong: number;
  xong: boolean;
  bi_gian_doan?: boolean;
  da_ghi?: { ma_dk: string; ket_qua: string }[];
  da_ghi_truoc?: string[];
  da_huy?: { ma_dk: string; so_giay_cu: string }[];
  da_huy_truoc?: { ma_dk: string; so_giay_cu: string }[];
  bo_qua?: { ma_dk: string; ma_ly_do: string; ly_do: string }[];
  chua_ghi?: string[];
  canh_bao?: { ma_dk?: string; ma: string; noi_dung: string }[];
  dem?: Record<string, number>;
  loi?: { ma_dk: string; noi_dung: string } | null;
  loi_nghiep_vu?: { ma: string; noi_dung: string };
}

export const dsKhoaTotNghiep = (cu = false) => goi<KhoaTnResp>("GET", "/khoa", { query: { loai: "oto", cu } });
export const dsHvTotNghiep = (maKh: string, q = "", trangThai = "") =>
  goi<HvTnResp>("GET", "/tot-nghiep/hv", { query: { ma_kh: maKh, q, trang_thai: trangThai } });
export const xemLaiTotNghiep = (maKh: string, dong: DongTn[], chung: ChungTn) =>
  goi<XemLaiTnResp>("POST", "/tot-nghiep/xem-lai", { body: { ma_kh: maKh, dong, chung } });
export const ghiTotNghiep = (loId: string, maKh: string, dong: DongTn[], chung: ChungTn, daXemCanhBao: boolean) =>
  goi<LoTn>("POST", "/tot-nghiep/ghi", {
    body: { lo_id: loId, ma_kh: maKh, dong, chung, da_xem_canh_bao: daXemCanhBao, xac_nhan_csdl_that: true },
  });
export const huyTotNghiep = (loId: string, maKh: string, dsMaDk: string[]) =>
  goi<LoTn>("POST", "/tot-nghiep/huy", { body: { lo_id: loId, ma_kh: maKh, ds_ma_dk: dsMaDk, xac_nhan_csdl_that: true } });

// ── Báo cáo 2: lập + thêm HV ──
export interface Bc2CuaKhoa {
  ma: string;
  /** 0 = đang mở, 1 = đã đóng. */
  trang_thai: number;
  tong_ghi: number | null;
}
export interface KhoaSanSang {
  ma_kh: string;
  ten_kh: string;
  ngay_bg: string;
  khoa_cu: boolean;
  co_bc1: boolean;
  so_bc1: string;
  bc2_cua_khoa: Bc2CuaKhoa[];
  san_sang: number;
  can_xem: number;
  /** HV thi lại trong ngưỡng tháng (như nhau cho mọi khóa — thi lại tính bất kể khóa). */
  thi_lai: number;
  thi_lai_cua_khoa: number;
}
export interface KhoaSanSangResp {
  loai: LoaiHang;
  hom_nay: string;
  thi_lai_thang: number;
  thi_lai_tat_ca: number;
  khoa: KhoaSanSang[];
}
export const khoaSanSang = (loai: LoaiHang, cu = false, thiLaiThang?: number, lamTuoi = false) =>
  goi<KhoaSanSangResp>("GET", "/bc2/khoa-san-sang", {
    query: { loai, cu, thi_lai_thang: thiLaiThang, lam_tuoi: lamTuoi },
  });
export type NhomUngVien = "san_sang" | "thi_lai" | "can_xem" | "khong_duoc";
export interface HvUngVien {
  ma_dk: string;
  so_ho_so: string;
  ten: string;
  ngay_sinh: string; // dd/mm/yyyy
  cmt: string;
  so_giay: string;
  hang: string;
  ma_kh: string;
  ten_kh: string;
  tt: string;
  ten_trang_thai: string;
  ma_bc2: string;
  bg: string; // ISO ngày bế giảng khóa gốc
  nhom: NhomUngVien;
  ma_ly_do: string;
  ly_do: string;
  /** `cap_nhat_tot_nghiep` | `cuu_trang_thai` | `go_khoi_bc2` | null */
  goi_y_xu_ly: string | null;
  tich_san: boolean;
  tuoi_thang: number | null;
  trong_nguong: boolean;
}
export interface UngVienResp {
  ma_kh: string;
  ten_kh: string;
  loai: LoaiHang;
  hom_nay: string;
  thi_lai_thang: number;
  ma_bc2: string;
  bc1: { ma_bci: string; so_bao_cao: string; so_hoc_sinh: number } | null;
  bc2_cua_khoa: Bc2CuaKhoa[];
  nhom: Record<NhomUngVien, HvUngVien[]>;
  dem: { san_sang: number; thi_lai: number; thi_lai_trong_nguong: number; can_xem: number; khong_duoc: number };
}
export const ungVienBc2 = (maKh: string, maBc2 = "", thiLaiThang?: number, lamTuoi = false) =>
  goi<UngVienResp>("GET", "/bc2/ung-vien", {
    query: { ma_kh: maKh, ma_bc2: maBc2, thi_lai_thang: thiLaiThang, lam_tuoi: lamTuoi },
  });
export const khopDanhSach = (maKh: string, maBc2: string, dong: string[]) =>
  goi("POST", "/bc2/khop-danh-sach", { body: { ma_kh: maKh, ma_bc2: maBc2, dong } });
export interface GoiYSoResp {
  ma_kh: string;
  ten_kh: string;
  loai: LoaiHang;
  nam: number;
  so: string;
  co_bc1: boolean;
  bc1: { ma_bci: string; so_bao_cao: string; so_hoc_sinh: number } | null;
  bc2_cua_khoa: Bc2CuaKhoa[];
  trung: boolean;
}
export interface TaoBc2Resp {
  ma_bc2: string;
  da_ton_tai: boolean;
  ma_kh: string;
  loai: LoaiHang;
  ma_bci: string;
  /** Vắng khi `da_ton_tai` (BC2 đã được tạo từ trước, server chỉ trả mã) — màn hình phải tự lấy từ giá trị đã nhập. */
  so_bao_cao?: string;
  ngay_bao_cao?: string;
  tong_so_thi_sinh?: number;
  trang_thai?: number;
  canh_bao: { ma: string; noi_dung: string }[];
}
export interface Bc2Dong {
  ma_bc2: string;
  so_bao_cao: string;
  ngay_bao_cao: string;
  ma_bci: string;
  so_bc1: string;
  ma_kh: string;
  ten_kh: string;
  loai: LoaiHang | "";
  tong_ghi: number | null;
  hv_thuc_te: number;
  lech: boolean;
  dong: boolean;
  dang_mo: boolean;
  nguoi_tao: string;
  ngay_tao: string;
}
export interface DsBc2Resp {
  loai: string;
  dong: string;
  tong: number;
  dang_mo: number;
  da_dong: number;
  lech: number;
  bc2: Bc2Dong[];
}
export const goiYSoBc2 = (maKh: string) => goi<GoiYSoResp>("GET", "/bc2/goi-y-so", { query: { ma_kh: maKh } });
export const taoBc2 = (b: {
  ma_kh: string;
  so_bao_cao: string;
  ngay_bao_cao: string;
  ghi_chu: string;
  da_xem_canh_bao: boolean;
  thu_lai?: boolean;
}) => goi<TaoBc2Resp>("POST", "/bc2", { body: { ...b, xac_nhan_csdl_that: true } });
export const lapBc2 = (b: {
  lo_id: string;
  ma_kh: string;
  ma_bc2: string;
  so_bao_cao: string;
  ngay_bao_cao: string;
  ghi_chu: string;
  ds_ma_dk: string[];
  da_xem_canh_bao: boolean;
}) => goi("POST", "/bc2/lap", { body: { ...b, xac_nhan_csdl_that: true } });
/** Tiến độ DÙNG CHUNG cho mọi lô chạy nền (lập, gỡ, hoàn tác, ghi/hủy tốt nghiệp). */
export const tienDoLo = (loId: string) => goi<LoTn>("GET", `/bc2/lo/${encodeURIComponent(loId)}`);

// ── Báo cáo 2: xem / gỡ / xóa / hoàn tác ──
const duongBc2 = (ma: string) => `/bc2/${encodeURIComponent(ma)}`;
export const chiTietBc2 = (ma: string) => goi("GET", duongBc2(ma));
export const goHvKhoiBc2 = (ma: string, loId: string, dsMaDk: string[], daXemCanhBao: boolean) =>
  goi("POST", `${duongBc2(ma)}/go`, {
    body: { lo_id: loId, ds_ma_dk: dsMaDk, da_xem_canh_bao: daXemCanhBao, xac_nhan_csdl_that: true },
  });
export const xoaBc2 = (ma: string) => goi("DELETE", duongBc2(ma), { query: { xac_nhan_csdl_that: true } });
export const hoanTacLoThem = (ma: string, loId: string) =>
  goi("POST", `${duongBc2(ma)}/hoan-tac`, { body: { lo_id: loId, xac_nhan_csdl_that: true } });

// ── Cứu trạng thái ──
export const timHvCuu = (q: string, loai: LoaiHang | "" = "") => goi("GET", "/cuu/tim", { query: { q, loai } });
export const cuuChuyen = (loId: string, maDk: string, dich: string, lyDo: string, loai: LoaiHang | "" = "") =>
  goi("POST", "/cuu/chuyen", { body: { lo_id: loId, ma_dk: maDk, dich, ly_do: lyDo, loai, xac_nhan_csdl_that: true } });
export const cuuHoanTac = (loIdCuu: string, loId: string) =>
  goi("POST", "/cuu/hoan-tac", { body: { lo_id_cuu: loIdCuu, lo_id: loId, xac_nhan_csdl_that: true } });

// ── Danh sách + nhật ký (chỉ đọc) ──
export const dsBc1 = (loai: LoaiHang | "" = "") => goi("GET", "/bc1", { query: { loai } });
export const dsBc2 = (loai: LoaiHang | "" = "", dong: "mo" | "dong" | "" = "") =>
  goi<DsBc2Resp>("GET", "/bc2", { query: { loai, dong } });
export const dsNhatKy = (loai = "", maBc2 = "", gioiHan = 100) =>
  goi("GET", "/nhat-ky", { query: { loai, ma_bc2: maBc2, gioi_han: gioiHan } });
