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
  ma_bc2?: string;
  da_tao_bc2?: boolean;
  da_them?: string[];
  da_co_tu_truoc?: string[];
  da_go?: string[];
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
  /** 0 = đang mở, 1 = đã đóng, 2 = chưa đóng nhưng đã gửi / có kết quả (khóa như đã đóng). */
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
  bc1: { ma_bci: string; so_bao_cao: string; so_hoc_sinh: number; ngay_bao_cao: string } | null;
  bc2_cua_khoa: Bc2CuaKhoa[];
  nhom: Record<NhomUngVien, HvUngVien[]>;
  dem: { san_sang: number; thi_lai: number; thi_lai_trong_nguong: number; can_xem: number; khong_duoc: number };
}
export const ungVienBc2 = (maKh: string, maBc2 = "", thiLaiThang?: number, lamTuoi = false) =>
  goi<UngVienResp>("GET", "/bc2/ung-vien", {
    query: { ma_kh: maKh, ma_bc2: maBc2, thi_lai_thang: thiLaiThang, lam_tuoi: lamTuoi },
  });
export interface KhopDanhSachResp {
  ma_kh: string;
  tong_dong: number;
  so_khop: number;
  /** HV khớp VÀ thuộc nhóm Sẵn sàng/Thi lại — được tích. */
  khop: (HvUngVien & { dong: string })[];
  /** Khớp người nhưng không đưa được (nhóm khác / đang ở BC2 mở khác…) kèm lý do. */
  khong_dua_duoc: { dong: string; ma_dk: string; ten: string; cmt: string; ma_ly_do: string; ly_do: string; goi_y_xu_ly?: string | null }[];
  /** Dòng không khớp ai (sai số / không có trong cơ sở). */
  khong_khop: string[];
}
export const khopDanhSach = (maKh: string, maBc2: string, dong: string[]) =>
  goi<KhopDanhSachResp>("POST", "/bc2/khop-danh-sach", { body: { ma_kh: maKh, ma_bc2: maBc2, dong } });
export interface GoiYSoResp {
  ma_kh: string;
  ten_kh: string;
  loai: LoaiHang;
  nam: number;
  so: string;
  co_bc1: boolean;
  bc1: { ma_bci: string; so_bao_cao: string; so_hoc_sinh: number; ngay_bao_cao: string } | null;
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
  /** `false` khi đã đóng HOẶC đã có kết quả (khóa). */
  dang_mo: boolean;
  /** 0 đang mở · 1 đã đóng · 2 đã gửi / có kết quả (chưa đóng). */
  trang_thai?: number;
  hv_ket_qua?: number;
  nguoi_tao: string;
  ngay_tao: string;
  /** TNB-08: từ SQLite của tool; `null` = chưa mở In BC2 lần nào. */
  ban_in?: { da_in_luc: string | null; so_chon_lai: number; so_can_chon: number } | null;
}
export interface DsBc2Resp {
  loai: string;
  dong: string;
  tong: number;
  dang_mo: number;
  da_dong: number;
  co_ket_qua?: number;
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
}) => goi<LoTn>("POST", "/bc2/lap", { body: { ...b, xac_nhan_csdl_that: true } });
/** Tiến độ DÙNG CHUNG cho mọi lô chạy nền (lập, gỡ, hoàn tác, ghi/hủy tốt nghiệp). */
export const tienDoLo = (loId: string) => goi<LoTn>("GET", `/bc2/lo/${encodeURIComponent(loId)}`);

// ── Báo cáo 2: xem / gỡ / xóa / hoàn tác ──
const duongBc2 = (ma: string) => `/bc2/${encodeURIComponent(ma)}`;
export interface HvTrongBc2 {
  ma_dk: string;
  so_ho_so: string;
  ten: string;
  ngay_sinh: string; // dd/mm/yyyy
  cmt: string;
  hang: string;
  ma_kh: string;
  ten_kh: string;
  tt: string;
  ten_trang_thai: string;
  tt_cu: string;
  ten_trang_thai_cu: string;
  go_duoc: boolean;
  ly_do_khoa: string;
  /** `TT_XuLy_Old` rỗng: gỡ ra sẽ về giá trị rỗng — cần xác nhận đã xem. */
  canh_bao_tt_cu: boolean;
  khac_khoa_bc1: boolean;
}
export interface ChiTietBc2 {
  ma_bc2: string;
  so_bao_cao: string;
  ngay_bao_cao: string;
  trang_thai: number;
  hv_ket_qua?: number;
  dang_mo: boolean;
  nguoi_tao: string;
  ngay_tao: string;
  ma_bci: string;
  ma_kh: string;
  ten_kh: string;
  loai: LoaiHang | "";
  tong_ghi: number | null;
  hv_thuc_te: number;
  lech: boolean;
  hoc_vien: HvTrongBc2[];
  xoa_duoc: boolean;
}
export const chiTietBc2 = (ma: string) => goi<ChiTietBc2>("GET", duongBc2(ma));
export const goHvKhoiBc2 = (ma: string, loId: string, dsMaDk: string[], daXemCanhBao: boolean) =>
  goi<LoTn>("POST", `${duongBc2(ma)}/go`, {
    body: { lo_id: loId, ds_ma_dk: dsMaDk, da_xem_canh_bao: daXemCanhBao, xac_nhan_csdl_that: true },
  });
export const xoaBc2 = (ma: string) =>
  goi<{ ma_bc2: string; da_xoa: boolean }>("DELETE", duongBc2(ma), { query: { xac_nhan_csdl_that: true } });
export const hoanTacLoThem = (ma: string, loId: string) =>
  goi<LoTn>("POST", `${duongBc2(ma)}/hoan-tac`, { body: { lo_id: loId, xac_nhan_csdl_that: true } });

// ── Cứu trạng thái ──
export interface DichCuu {
  /** `09` | `14` | `17` | `18` */
  ma: string;
  ten: string;
  cho_phep: boolean;
  ly_do: string;
}
export interface HvCuu {
  ma_dk: string;
  so_ho_so: string;
  ten: string;
  ngay_sinh: string; // dd/mm/yyyy
  cmt: string;
  hang: string;
  tt: string;
  ma_bc2: string;
  ma_kh: string;
  so_giay: string;
  ten_kh: string;
  bg: string;
  loai: LoaiHang;
  khac_loai: boolean;
  ten_trang_thai: string;
  /** Vì sao HV không có trong danh sách ứng viên. `ma === "dang_hien"` = thực ra đang có trong danh sách. */
  khong_hien: { ma: string; noi_dung: string; goi_y_xu_ly?: string | null; nhom?: string };
  dich: DichCuu[];
  cuu_duoc: boolean;
}
export interface TimCuuResp {
  q: string;
  loai: string;
  tong_khop: number;
  hien_toi_da: number;
  hoc_vien: HvCuu[];
}
export interface KetQuaCuu {
  lo_id: string;
  ma_dk: string;
  tt_cu: string;
  tt_moi: string;
  ten_trang_thai_cu?: string;
  ten_trang_thai_moi: string;
  ly_do?: string;
  canh_bao: { ma: string; noi_dung: string }[];
  trang_thai: string;
  da_ton_tai?: boolean;
  lo_goc?: string;
}
export const timHvCuu = (q: string, loai: LoaiHang | "" = "") =>
  goi<TimCuuResp>("GET", "/cuu/tim", { query: { q, loai } });
export const cuuChuyen = (loId: string, maDk: string, dich: string, lyDo: string, loai: LoaiHang | "" = "") =>
  goi<KetQuaCuu>("POST", "/cuu/chuyen", {
    body: { lo_id: loId, ma_dk: maDk, dich, ly_do: lyDo, loai, xac_nhan_csdl_that: true },
  });
export const cuuHoanTac = (loIdCuu: string, loId: string) =>
  goi<KetQuaCuu>("POST", "/cuu/hoan-tac", { body: { lo_id_cuu: loIdCuu, lo_id: loId, xac_nhan_csdl_that: true } });

// ── Danh sách + nhật ký (chỉ đọc) ──
export const dsBc1 = (loai: LoaiHang | "" = "") => goi("GET", "/bc1", { query: { loai } });
export const dsBc2 = (loai: LoaiHang | "" = "", dong: "mo" | "dong" | "" = "") =>
  goi<DsBc2Resp>("GET", "/bc2", { query: { loai, dong } });
export interface DongNhatKy {
  id: number;
  /** ISO `YYYY-MM-DDTHH:mm:ss`, giờ máy CSĐT. */
  luc: string;
  nguoi: string;
  /** `tao_bc2` | `them_hv` | `go_hv` | `xoa_bc2` | `tot_nghiep` | `huy_tot_nghiep` | `cuu_trang_thai` */
  loai: string;
  ten_loai: string;
  ma_kh: string;
  ma_bc2: string;
  lo_id: string;
  so_hv: number;
  tom_tat_thao_tac: string;
  /** `xong` | `loi_giua_chung` | `that_bai` | `bat_dau` | `da_ton_tai` */
  trang_thai: string;
  ten_trang_thai: string;
  ket_qua: { da_ghi: number; chua_ghi: number; bo_qua: number; tom_tat: string };
}
export interface NhatKyResp {
  loai: string;
  ma_bc2: string;
  tong: number;
  nhat_ky: DongNhatKy[];
}
export const dsNhatKy = (loai = "", maBc2 = "", gioiHan = 100) =>
  goi<NhatKyResp>("GET", "/nhat-ky", { query: { loai, ma_bc2: maBc2, gioi_han: gioiHan } });

// ── In BC2 + chọn phần thi (TNB-08, TDD §11F.9) ──
/** Một học viên ở màn In BC2. `phan` = các phần của hạng (ô tô L·H·Đ, mô tô LT·TH); `phai_thi` ⊆ `phan`. */
export interface HvBanIn {
  stt: number;
  ma_dk: string;
  ho_ten: string;
  ngay_sinh: string;
  so_cmt: string;
  hang: string;
  nhom: "oto" | "moto" | "a3a4";
  phan: string[];
  phai_thi: string[];
  dat: string[];
  da_thi: boolean;
  ma_nd: number | null;
  ghi_chu: string;
  da_sua: boolean;
  nguon: "so" | "sua" | "in" | "suy" | "pm_cu" | "chua_thi" | "qua_han";
  ten_nguon: string;
  nguon_luc: string;
  ket_qua_sh: string;
  /** Mã kỳ sát hạch ở DB Nạp lúc này (tooltip "đạt kỳ nào"). */
  ma_ky_sh?: string;
  mac_dinh: { phai_thi: string[]; dat: string[]; ma_nd: number | null; ghi_chu: string; da_thi: boolean };
  pm_cu: string;
  pm_cu_khac: boolean;
}
export interface BanInResp {
  ma_bc2: string;
  so_bao_cao: string;
  ngay_bao_cao: string;
  dang_mo: boolean;
  ma_kh: string;
  loai: LoaiHang | "";
  hoc_vien: HvBanIn[];
  so_chon_lai: number;
  so_can_chon: number;
}
export interface ThuMucPmCu {
  thu_muc: string;
  nguon: "da_luu" | "tu_do" | "khong_co";
  ung_vien: string[];
  luu_khong_hop_le?: string;
}
export const banInBc2 = (ma: string) => goi<BanInResp>("GET", `${duongBc2(ma)}/ban-in`);
/** `phaiThi = null` → về mặc định. Trả dữ liệu màn In BC2 mới (server là nguồn duy nhất của tên mục). */
export const luuNoiDungThi = (ma: string, ds: { ma_dk: string; phai_thi: string[] | null }[]) =>
  goi<BanInResp>("PUT", `${duongBc2(ma)}/noi-dung-thi`, { body: { ds } });
export const daInBc2 = (ma: string) => goi<{ ok: boolean }>("POST", `${duongBc2(ma)}/da-in`);
export const thuMucPmCu = () => goi<ThuMucPmCu>("GET", "/gplx-cu-dir");
export const datThuMucPmCu = (thuMuc: string) => goi<ThuMucPmCu>("PUT", "/gplx-cu-dir", { body: { thu_muc: thuMuc } });

/** Dựng PDF xem trước (mẫu phần mềm cũ). Lỗi giữ nguyên dạng `LoiTnbc2` như các hàm khác. */
export async function xemTruocBc2(ma: string): Promise<Blob> {
  const r = await fetch(`${BASE}/local/tnbc2${duongBc2(ma)}/xem-truoc`, { method: "POST", headers: authHeaders() });
  if (!r.ok) {
    const d = await r.json().catch(() => null);
    const detail = d?.detail;
    if (detail && typeof detail === "object" && !Array.isArray(detail)) {
      const { ma: m, noi_dung, ...conLai } = detail as DuLieu & { ma?: string; noi_dung?: string };
      throw new LoiTnbc2(String(m ?? "loi"), String(noi_dung ?? `${r.status}`), r.status, conLai);
    }
    throw new LoiTnbc2("loi_he_thong", `${r.status} ${r.statusText}`, r.status);
  }
  // Server trả JSON + base64 (không trả application/pdf để phần mềm tải file trong trình duyệt không chặn bắt).
  const d = (await r.json()) as { pdf_base64: string };
  const bin = atob(d.pdf_base64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return new Blob([bytes], { type: "application/pdf" });
}

/** Tên tệp PDF: số BC2 có `/` → `-`, kèm mã khóa đầu trang. */
export const tenTepBc2 = (maBc2: string, maKh: string) => {
  const sach = (s: string) => s.replace(/Ð/g, "Đ").replace(/ð/g, "đ").replace(/[\\/:*?"<>|\u0000-\u001f]/g, "-");
  return `BC2_${sach(maBc2)}${maKh ? `_${sach(maKh)}` : ""}.pdf`;
};
