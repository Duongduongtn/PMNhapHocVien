// Gọi API tool chạy localhost. Dev: webui 3011 ↔ backend 8000 (khác origin).
// Khi đóng gói .exe, webui static do chính FastAPI phục vụ → cùng origin (BASE rỗng).
export const BASE = import.meta.env.DEV ? "http://localhost:8000" : "";

// Session token cục bộ (HTG-01③) — lưu localStorage để F5/tải lại trang không văng
// ra đăng nhập (server session không có TTL, sống tới khi backend restart).
const _TOKEN_KEY = "tool_session_token";
let _token: string | null = (() => {
  try {
    return localStorage.getItem(_TOKEN_KEY);
  } catch {
    return null; // chế độ riêng tư / storage bị chặn → chỉ giữ trong bộ nhớ
  }
})();
export const datToken = (t: string | null) => {
  _token = t;
  try {
    if (t) localStorage.setItem(_TOKEN_KEY, t);
    else localStorage.removeItem(_TOKEN_KEY);
  } catch {
    /* không ghi được storage → vẫn chạy với token trong bộ nhớ */
  }
};
export const coToken = () => _token !== null;
// Header kèm Bearer cho endpoint /local/* nghiệp vụ (config/auth được miễn — A1).
export function authHeaders(extra?: Record<string, string>): Record<string, string> {
  const h: Record<string, string> = { ...(extra || {}) };
  if (_token) h.Authorization = `Bearer ${_token}`;
  return h;
}

export interface ToolConfig {
  sqlserver_host: string;
  sqlserver_database: string;
  sqlserver_user: string;
  sqlserver_password: string;
  vps_url: string;
  vps_api_key: string;
  co_quan_chu_quan?: string;     // KQD-09 — đầu file Excel kết quả học tập
  ten_co_so_dao_tao?: string;
}

// KQD-09: chỉ lưu 2 ô tên cơ quan/cơ sở (không đụng khóa kết nối).
export const putCoSo = (b: { co_quan_chu_quan: string; ten_co_so_dao_tao: string }) =>
  fetch(`${BASE}/local/config/co-so`, {
    method: "PUT", headers: authHeaders({ "Content-Type": "application/json" }), body: JSON.stringify(b),
  }).then(json<ToolConfig>);

export interface TestResult {
  sqlserver: { ok: boolean; message: string };
  vps: { ok: boolean; message: string };
}

export type LoaiXe = "moto" | "oto";

export interface KhoaHoc {
  ma_kh: string;
  ten_kh: string;
  hang_gplx: string;
  hang_dt: string | null;
  ma_so_gtvt: string;
  ma_loai_hs: number; // 1 = mô tô, 2 = ô tô
}

// Lỗi API: `.chiTiet` giữ nguyên `detail` của server (có thể là object {loi|ketqua, thong_bao,…}) để UI phân loại.
export class ApiLoi extends Error {
  chiTiet: unknown;
  constructor(msg: string, chiTiet?: unknown) {
    super(msg);
    this.chiTiet = chiTiet;
  }
}

async function json<T>(r: Response): Promise<T> {
  if (!r.ok) {
    const d = await r.json().catch(() => null);
    const dt = d?.detail;
    const msg = typeof dt === "string" ? dt : (dt && typeof dt === "object" && typeof dt.thong_bao === "string" ? dt.thong_bao : "");
    throw new ApiLoi(msg || `${r.status} ${r.statusText}`, dt);
  }
  return r.json() as Promise<T>;
}

// Số hiệu bản build (hiện trên thanh tiêu đề để nhận ra đang chạy bản mới nhất).
// Bản đóng gói trả thời điểm build + commit; chạy dev trả "dev".
export interface VersionInfo {
  version: string;
  build: string;
  commit: string;
}
export const getVersion = () => fetch(`${BASE}/version`).then(json<VersionInfo>);

// ── Đăng nhập cục bộ của tool (HTG-01③) ──
export interface ToolNguoiDung {
  session_token: string;
  username: string;
  ho_ten: string | null;
  vai_tro: string;
}

export const toolDangNhap = (username: string, password: string) =>
  fetch(`${BASE}/local/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  }).then(json<ToolNguoiDung>);

export const toolDangXuat = () =>
  fetch(`${BASE}/local/auth/logout`, { method: "POST", headers: authHeaders() });

// Khôi phục phiên từ token đã lưu (F5): trả thông tin người dùng, 401 nếu token hết hạn.
export const toolMe = () =>
  fetch(`${BASE}/local/auth/me`, { headers: authHeaders() }).then(
    json<{ username: string; ho_ten: string | null; vai_tro: string }>,
  );

export const getConfig = () =>
  fetch(`${BASE}/local/config`).then(json<Partial<ToolConfig>>);

export const putConfig = (cfg: ToolConfig) =>
  fetch(`${BASE}/local/config`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cfg),
  }).then(json<Partial<ToolConfig>>);

export const testConfig = (cfg: ToolConfig) =>
  fetch(`${BASE}/local/config/test`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cfg),
  }).then(json<TestResult>);

// DGT-03 — kiểm môi trường + trạng thái cấu hình cho wizard lần đầu.
export interface MoiTruong {
  thu_muc_ghi_duoc: boolean;
  duong_dan: string;
  da_cau_hinh: boolean;
}
export const kiemMoiTruong = () =>
  fetch(`${BASE}/local/config/moi-truong`).then(json<MoiTruong>);

export const getKhoaHoc = (loai: LoaiXe) =>
  fetch(`${BASE}/local/khoa-hoc?loai=${loai}`, { headers: authHeaders() }).then(json<KhoaHoc[]>);

// KHO-01 — tạo khóa học
export interface HangDT {
  ma_hang_dt: string;
  ten: string;
  tuoi_hv: number | null;
  thoi_gian_dt: number | null;
  hang_gplx: string;
}
export const getHangDT = () =>
  fetch(`${BASE}/local/khoa-hoc/hang-dt`, { headers: authHeaders() }).then(json<HangDT[]>);

export interface KhoaHocTaoIn {
  hang_dt: string;
  ten_kh: string;
  ngay_kg: string; // yyyy-mm-dd
  ngay_bg: string; // yyyy-mm-dd
  tong_so_hv: number;
  so_qd?: string | null;
  ngay_qd?: string | null;
  ngay_thi?: string | null;
  ghi_chu?: string | null;
}
export interface KhoaHocTaoKq {
  ma_kh: string;
  ten_kh: string;
  hang_gplx: string;
  hang_dt: string;
}
export const taoKhoa = (body: KhoaHocTaoIn) =>
  fetch(`${BASE}/local/khoa-hoc/tao`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  }).then(json<KhoaHocTaoKq>);

// QLY-01 — Tra cứu DB
export interface KhoaTraCuu {
  ma_kh: string;
  ten_kh: string;
  hang_gplx: string;
  hang_dt: string | null;
  bc1: boolean; // đã lập Báo cáo I → chỉ xem
}
export const traCuuKhoa = (q: string) =>
  fetch(`${BASE}/local/khoa-hoc/tra-cuu?q=${encodeURIComponent(q)}`, { headers: authHeaders() }).then(json<KhoaTraCuu[]>);

export interface HoSoRow {
  ma_dk: string;
  ho_ten: string | null;
  ngay_sinh: string | null; // yyyymmdd
  gioi_tinh: string | null; // M/F
  so_cccd: string | null;
  so_cmnd_cu: string | null;
  so_ho_so: string | null;
  noi_tt: string | null; // chi tiết thường trú (số nhà/thôn)
  hktt: string | null; // thường trú đầy đủ (xã/tỉnh từ DM_DVHC)
  noi_ct: string | null; // chi tiết cư trú
  hkct: string | null; // cư trú đầy đủ
  ngay_cap: string | null; // ngày cấp CCCD (yyyymmdd)
  noi_cap_ma: string | null; // mã Sở GTVT (nơi cấp)
  noi_cap_ten: string | null; // tên Sở GTVT (tỉnh cấp CCCD)
  co_anh: boolean;
  duong_dan_anh: string | null; // đường dẫn .jp2 trong DB (QLY-01 task 35 — hiện ở modal)
  ma_loai_hs: number;
}
export const dsHoSoTheoKhoa = (makh: string) =>
  fetch(`${BASE}/local/ho-so?makh=${encodeURIComponent(makh)}`, { headers: authHeaders() }).then(json<HoSoRow[]>);

// QLY-01 task 35 — tải ảnh chân dung HV đã lưu (.jp2 → PNG qua backend). Phải fetch kèm session
// header rồi createObjectURL (KHÔNG <img src=url> trực tiếp: header không gửi kèm). Phân biệt
// file mất (404) / ảnh hỏng (422) để avatar hiện icon ảnh-vỡ và modal báo đúng nguyên nhân.
export type KetQuaAnh = { url: string } | { loi: "mat" | "hong" | "khac" };
async function taiAnhPNG(path: string): Promise<KetQuaAnh> {
  const r = await fetch(`${BASE}${path}`, { headers: authHeaders() });
  if (r.ok) return { url: URL.createObjectURL(await r.blob()) };
  if (r.status === 404) return { loi: "mat" };
  if (r.status === 422) return { loi: "hong" };
  return { loi: "khac" };
}
// v: cache-bust (CHANGES #23) — tăng sau khi lưu/thay ảnh để trình duyệt lấy ảnh MỚI, không trả bản cũ từ bộ đệm. v=0 → URL ổn định (cache bình thường).
export const taiAnhHoSo = (maDk: string, v = 0) => taiAnhPNG(`/local/ho-so/anh?ma_dk=${encodeURIComponent(maDk)}${v ? `&v=${v}` : ""}`);
export const taiAnhThumb = (maDk: string, v = 0) => taiAnhPNG(`/local/ho-so/anh-thumb?ma_dk=${encodeURIComponent(maDk)}${v ? `&v=${v}` : ""}`);

// QLY-07 task 40 — đổi nền trắng cả khóa (job nền + polling tiến độ).
export interface DoiNenTienDo {
  tong: number;
  xong: number;
  bo_qua: number;
  loi: number;
  ds_loi: { ma_dk: string; ly_do: string }[];
  dang_chay: boolean;
  xong_het: boolean;
  thong_bao: string;
}
export const batDauDoiNen = (maKh: string, pham_vi: "chua_trang" | "tat_ca", sao_luu: boolean) =>
  fetch(`${BASE}/local/khoa/${encodeURIComponent(maKh)}/doi-nen`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ pham_vi, sao_luu }),
  }).then(json<{ ok: boolean; ma_kh: string }>);
export const tienDoDoiNen = (maKh: string) =>
  fetch(`${BASE}/local/khoa/${encodeURIComponent(maKh)}/doi-nen`, { headers: authHeaders() }).then(
    json<DoiNenTienDo>,
  );

// QLY-01 lát 2 — sửa nhân thân HV. Đọc chi tiết để mở form + cờ BC1 (chặn sửa).
export interface HoSoChiTiet {
  ma_dk: string;
  ho_ten: string;
  ngay_sinh: string; // dd/mm/yyyy (hoặc yyyy) để hiển thị trên ô
  gioi_tinh: string; // M/F/U
  gioi_tinh_ten: string;
  so_cccd: string;
  noi_tt: string;
  hktt: string | null; // tên xã HKTT (chỉ để tham chiếu)
  // Mở rộng 06/10 — preselect combo địa chỉ 2 cấp + ngày/nơi cấp CCCD
  noi_tt_ma_dvhc: string;
  noi_tt_ma_dvql: string;
  ngay_cap_cmt: string; // 'yyyymmdd' hoặc ''
  noi_cap_ma: string;   // mã DM_DVHC ('00' Cục QLHC / mã tỉnh)
  noi_cap_ten: string | null;
  ma_kh: string;
  bc1: boolean;
}
export const chiTietHoSo = (maDk: string) =>
  fetch(`${BASE}/local/ho-so/chi-tiet?ma_dk=${encodeURIComponent(maDk)}`, { headers: authHeaders() }).then(
    json<HoSoChiTiet>,
  );

export interface HoSoSuaIn {
  ho_ten: string;
  ngay_sinh: string; // dd/mm/yyyy hoặc yyyy
  gioi_tinh: string; // M/F/U
  so_cccd: string;
  noi_tt: string;
  // Mở rộng 06/10 — rỗng = giữ giá trị cũ ở DB
  noi_tt_ma_dvhc?: string; // mã xã (DM_DVHC)
  noi_tt_ma_dvql?: string; // mã tỉnh (MaDVQL)
  ngay_cap_cmt?: string;   // 'yyyymmdd'
  noi_cap_cmt?: string;    // nơi cấp căn cước (mã DM_DVHC)
}
export const suaHoSo = (maDk: string, body: HoSoSuaIn) =>
  fetch(`${BASE}/local/ho-so/sua?ma_dk=${encodeURIComponent(maDk)}`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  }).then(json<{ ok: boolean; ma_dk: string }>);

// QLY-10, TCB-05 — GPLX đã có của học viên đã nạp. `tho` gửi lại nguyên văn khi lưu để đối chiếu dữ liệu cũ.
export interface GplxHoSo {
  ma_dk: string;
  ho_ten: string | null;
  ma_kh: string;
  hang_khoa: string;
  chan: string | null; // lý do không được lưu; null = lưu được
  gplx: Record<string, string>[];
  lech: boolean;
  tho: Record<string, string>;
}

export interface BanWebRef { uuid: string; dau_van: string }

const luuGplx = (url: string, gplx: unknown[], tho: Record<string, string>, banWeb?: BanWebRef) =>
  fetch(url, {
    method: "PUT",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ gplx, tho, ban_web: banWeb ?? null }),
  }).then(json<{ ok: boolean; ma_dk: string; co_o_dich?: boolean }>);

// QLY-10 — bản app web chờ duyệt. kiem_duoc=false: chưa hỏi được VPS, KHÔNG có nghĩa là 0 hồ sơ.
export interface GplxCanhBao extends BanWebRef {
  ma_dk: string;
  nguoi_gui: string | null;
  updated_at: string;
  ho_ten: string | null;
  ma_kh: string | null;
  ten_kh: string | null;
  hang_db: { hang: string; nhom: string }[];
  hang_web: { hang: string; nhom: string }[];
  khong_thay: boolean;
}
export interface GplxBanWeb extends BanWebRef {
  gplx: Record<string, string>[];
  nguoi_gui: string | null;
  updated_at: string;
}

export const dsGplxBoSung = () =>
  fetch(`${BASE}/local/ho-so/gplx-bo-sung`, { headers: authHeaders() }).then(json<{ kiem_duoc: boolean; items: GplxCanhBao[] }>);

export const gplxBanWeb = (maDk: string) =>
  fetch(`${BASE}/local/ho-so/gplx-ban-web?ma_dk=${encodeURIComponent(maDk)}`, { headers: authHeaders() }).then(json<GplxBanWeb>);

export const boQuaGplx = (ref: BanWebRef) =>
  fetch(`${BASE}/local/ho-so/gplx/bo-qua`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ uuid: ref.uuid, dau_van: ref.dau_van }),
  }).then(json<{ ok: boolean }>);

export const gplxHoSo = (maDk: string) =>
  fetch(`${BASE}/local/ho-so/gplx?ma_dk=${encodeURIComponent(maDk)}`, { headers: authHeaders() }).then(json<GplxHoSo>);

export const luuGplxHoSo = (maDk: string, gplx: unknown[], tho: Record<string, string>, banWeb?: BanWebRef) =>
  luuGplx(`${BASE}/local/ho-so/gplx?ma_dk=${encodeURIComponent(maDk)}`, gplx, tho, banWeb);

// QLY-02 — đổi khóa (cùng hạng). Danh sách khóa đích + thực hiện đổi.
export interface KhoaDich {
  ma_kh: string;
  ten_kh: string;
  hang_gplx: string;
  hang_dt: string | null;
}
export const khoaCungHang = (maKh: string) =>
  fetch(`${BASE}/local/khoa-hoc/cung-hang?ma_kh=${encodeURIComponent(maKh)}`, { headers: authHeaders() }).then(
    json<KhoaDich[]>,
  );
export const doiKhoa = (maDk: string, maKhDich: string) =>
  fetch(`${BASE}/local/ho-so/doi-khoa?ma_dk=${encodeURIComponent(maDk)}`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ ma_kh_dich: maKhDich }),
  }).then(json<{ ok: boolean; ma_dk: string; ma_kh: string; so_ho_so: string }>);

// QLY-03 — xóa học viên (xóa mềm ảnh sang _DELETED). anh_loi: đã xóa DB nhưng chuyển ảnh lỗi.
export const xoaHoSo = (maDk: string) =>
  fetch(`${BASE}/local/ho-so/xoa?ma_dk=${encodeURIComponent(maDk)}`, {
    method: "POST",
    headers: authHeaders(),
  }).then(json<{ ok: boolean; ma_dk: string; anh_loi?: string }>);

// QLY-08 — gỡ HV đã nạp (nhầm khóa) về chờ nạp: xóa khỏi CSDT rồi trả bản ghi gốc VPS về pending.
// ve_cho_nap=true: trọn vẹn. VPS lỗi SAU khi đã xóa CSDT: ok vẫn true + dong_bo_loi + co_the_thu_lai
// (UI hiện banner "Thử lại đồng bộ"). trong_hang_doi=false: dòng đã "Bỏ khỏi hàng đợi" → bấm Kéo về.
export interface GoVeKetQua {
  ok: boolean;
  ma_dk: string;
  uuid?: string;
  ve_cho_nap?: boolean;
  trong_hang_doi?: boolean;
  da_xoa_csdt?: boolean;
  dong_bo_loi?: string;
  co_the_thu_lai?: boolean;
  anh_loi?: string;
}
export const goVeChoNap = (maDk: string) =>
  fetch(`${BASE}/local/ho-so/go-ve-cho-nap?ma_dk=${encodeURIComponent(maDk)}`, {
    method: "POST",
    headers: authHeaders(),
  }).then(json<GoVeKetQua>);

// QLY-08 "Thử lại đồng bộ" — chạy lại RIÊNG bước gọi VPS (KHÔNG xóa lại CSDT). Idempotent.
export const dongBoTraVe = (uuid: string) =>
  fetch(`${BASE}/local/ho-so/dong-bo-tra-ve?uuid=${encodeURIComponent(uuid)}`, {
    method: "POST",
    headers: authHeaders(),
  }).then(json<{ ok: boolean; uuid: string; ve_cho_nap: boolean; trong_hang_doi: boolean }>);

// QLY-05 — nạp/thay ảnh cho HV đã có. Ảnh đã xử lý qua xuLyAnh (NAP-04) → gửi jp2_b64.
export const napAnh = (maDk: string, jp2B64: string) =>
  fetch(`${BASE}/local/ho-so/nap-anh?ma_dk=${encodeURIComponent(maDk)}`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ jp2_b64: jp2B64 }),
  }).then(json<{ ok: boolean; ma_dk: string; duong_dan_anh: string; co_anh: boolean }>);

// QLY-06 — đọc đủ dữ liệu cá nhân HV để điền sẵn khi mở hồ sơ khóa khác (nạp mới khóa đích).
export interface HoSoDayDu {
  ho_ten: string;
  ngay_sinh: string; // yyyymmdd (hoặc yyyy)
  gioi_tinh: string; // M/F/U
  so_cmt: string;
  ngay_cap_cmt: string | null; // yyyymmdd
  noi_cap_cmt: string | null;
  noi_tt: string | null;
  noi_tt_ma_dvhc: string;
  noi_tt_ma_dvql: string;
}
export const hoSoDayDu = (maDk: string) =>
  fetch(`${BASE}/local/ho-so/day-du?ma_dk=${encodeURIComponent(maDk)}`, { headers: authHeaders() }).then(
    json<HoSoDayDu>,
  );

export interface Tinh {
  ma_dvql: string;
  ten_tinh: string;
}

export interface Xa {
  ma_dvhc: string;
  ma_dvql: string;
  ten_xa: string;
}

export interface MapKetQua {
  matched: boolean;
  divided: boolean;
  ma_dvhc?: string;
  ma_dvql?: string;
  ten_xa?: string;
  ten_tinh?: string;
}

export const getTinh = () =>
  fetch(`${BASE}/local/dvhc/tinh`, { headers: authHeaders() }).then(json<Tinh[]>);

export const getXa = (tinh: string) =>
  fetch(`${BASE}/local/dvhc/xa?tinh=${encodeURIComponent(tinh)}`, { headers: authHeaders() }).then(json<Xa[]>);

export interface SoGtvt { ma: string; ten: string } // nơi cấp căn cước: mã DM_DVHC ('00' Cục QLHC / tỉnh) + tên
export const getSoGtvt = () =>
  fetch(`${BASE}/local/dvhc/so-gtvt`, { headers: authHeaders() }).then(json<SoGtvt[]>);

export const getNoiCapGplx = () =>
  fetch(`${BASE}/local/dvhc/noi-cap-gplx`, { headers: authHeaders() }).then(json<SoGtvt[]>);

export const mapDiaChi = (dc: { tinh: string; huyen: string; xa: string }) =>
  fetch(`${BASE}/local/dvhc/map`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(dc),
  }).then(json<MapKetQua>);

export interface AnhKetQua {
  preview: string; // data URL PNG (xem trước)
  jp2_b64: string; // .jp2 base64 — NAP-05 dùng để ghi file
  w: number;
  h: number;
}

export const xuLyAnh = (file: File, box: string, xoaPhong: boolean) => {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("box", box);
  fd.append("xoa_phong", String(xoaPhong));
  return fetch(`${BASE}/local/anh/xu-ly`, { method: "POST", headers: authHeaders(), body: fd }).then(
    json<AnhKetQua>,
  );
};

// NAP-05: giấy tờ bắt buộc theo khóa + nạp 1 HV.
export interface GiayTo {
  ma_gt: number;
  ten_gt: string;
}

// hangGplx: backend dò thêm theo hạng GPLX khi danh mục không có mã HangDT (vd khóa A2 HangDT 'Am').
export const getGiayTo = (maLoaiHs: number, hangDt: string, hangGplx?: string | null) =>
  fetch(`${BASE}/local/giay-to?ma_loai_hs=${maLoaiHs}&hang_dt=${encodeURIComponent(hangDt)}${hangGplx ? `&hang_gplx=${encodeURIComponent(hangGplx)}` : ""}`, {
    headers: authHeaders(),
  }).then(json<GiayTo[]>);

export interface NapIn {
  uuid: string;
  ma_khoa_hoc: string;
  ho_ten: string;
  ngay_sinh: string; // yyyymmdd
  gioi_tinh: string; // 'M' | 'F'
  so_cmt: string;
  ngay_cap_cmt?: string; // yyyymmdd (SP convert style 112); từ hàng kéo về
  noi_cap_cmt?: string;
  chi_tiet_tt?: string; // số nhà/thôn — mặc định trống (NoiTT); KHÔNG nhét tên xã
  noi_tt_ma_dvhc: string;
  noi_tt_ma_dvql: string;
  chi_tiet_ct?: string;
  giay_to_tick: number[];
  anh_jp2_b64?: string | null;
  // "Chọn in GPLX": 1 ghép · 2 có thời hạn · 3 không thời hạn. Bỏ trống → server mặc định theo hạng khóa (mô tô 3 / ô tô 2).
  chon_in_gplx?: 1 | 2 | 3;
  // GPLX đã có (NAP-07): danh sách bằng, ngày yyyymmdd, `hang` là mã DM_HangGPLX. Bỏ trống = không ghi.
  gplx_da_co?: Record<string, unknown>[];
}

export interface NapKetQua {
  ma_dk: string;
  so_ho_so: string;
  so_giay_to: number;
}

// Trả lỗi kèm nội dung detail (FastAPI) để UI báo đúng dòng.
export const napHoSo = async (body: NapIn): Promise<NapKetQua> => {
  const r = await fetch(`${BASE}/local/nap`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    const d = await r.json().catch(() => null);
    throw new Error(d?.detail || `${r.status} ${r.statusText}`);
  }
  return r.json() as Promise<NapKetQua>;
};

// NAP-06: kiểm CCCD đã có trong cùng khóa chưa (cảnh báo sớm). Lỗi kiểm → coi như không trùng
// (SP gộp vẫn chặn khi nạp qua @p_out=-2).
export const kiemTrungCccd = async (
  maKh: string,
  soCmt: string,
): Promise<{ trung: boolean; so_ho_so: string | null }> => {
  try {
    const q = `ma_kh=${encodeURIComponent(maKh)}&so_cmt=${encodeURIComponent(soCmt)}`;
    const r = await fetch(`${BASE}/local/kiem-trung-cccd?${q}`, { headers: authHeaders() });
    if (!r.ok) return { trung: false, so_ho_so: null };
    return (await r.json()) as { trung: boolean; so_ho_so: string | null };
  } catch {
    return { trung: false, so_ho_so: null };
  }
};

// ── NAP-01: kéo hàng đợi VPS → staging + nạp lô ──
export interface KeoVeRow {
  uuid: string;
  so_cccd: string | null;
  so_cmnd_cu: string | null;
  ho_ten: string | null;
  ngay_sinh: string | null; // yyyymmdd
  gioi_tinh: string | null;
  noi_tt_raw: string | null;
  ngay_cap: string | null; // yyyymmdd (đã đổi từ ISO)
  noi_cap_cccd: string | null;
  co_anh: number; // 0/1
  created_at: string | null;
  trang_thai: "cho" | "loi" | "xong";
  loi: string | null;
  ma_dk: string | null;
  so_ho_so: string | null;
  gplx_da_co_json?: string | null; // GPLX đã có từ VPS / đã nạp (NAP-07)
}

// Kéo trọn bản ghi pending từ VPS về staging. Trả số mới thêm + làm tươi + bỏ-đã-xóa + reset-địa-chỉ + tổng.
export const keoHangDoi = () =>
  fetch(`${BASE}/local/nap/keo`, { method: "POST", headers: authHeaders() }).then(
    json<{ keo_ve: number; lam_tuoi: number; bo_da_xoa: number; dia_chi_reset: number; thay_doi: number; tong: number }>,
  );

// NAP-08 — hồ sơ CHƯA NẠP mà app web vừa đổi sau lần kéo trước (chỉ mã trường, không có giá trị cá nhân).
export interface ThayDoiHoSo {
  uuid: string;
  ho_ten: string | null;
  truong: string[]; // "tt:<cột>" · "gplx" · "anh" · "dc_reset"
  luc: string; // ISO, giờ máy tool
  nhap_giu_anh_cu: boolean; // ảnh đổi mà nháp Chuẩn bị đang giữ ảnh đã xử lý
}
export const getThayDoi = () => fetch(`${BASE}/local/nap/thay-doi`, { headers: authHeaders() }).then(json<ThayDoiHoSo[]>);
export const thayDoiDaXem = (b: { uuids?: string[]; tat_ca?: boolean; loai?: string }) =>
  fetch(`${BASE}/local/nap/thay-doi/da-xem`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify(b),
  }).then(json<{ ok: boolean }>);
// "Dùng ảnh mới": bỏ riêng ảnh trong nháp, giữ địa chỉ và giấy tờ.
export const nhapBoAnh = (uuid: string) =>
  fetch(`${BASE}/local/nap/nhap/${encodeURIComponent(uuid)}/bo-anh`, { method: "POST", headers: authHeaders() }).then(
    json<{ ok: boolean; uuid: string; da_bo: boolean }>,
  );

export const getDanhSachKeoVe = () =>
  fetch(`${BASE}/local/nap/danh-sach`, { headers: authHeaders() }).then(json<KeoVeRow[]>);

// NAP-01 #51 — "Bỏ khỏi hàng đợi" 1 hay nhiều dòng (MỌI trạng thái) qua 1 đường POST.
// Dòng chờ/lỗi → tool nhớ "bỏ qua" (tombstone) nên kéo lại không mang về; 'xong' bỏ như cũ.
// TOOL-LOCAL, không đụng prod/VPS. Thay endpoint DELETE /keo-ve/{uuid} cũ (task 38).
export const boKhoiHangDoi = (uuids: string[]) =>
  fetch(`${BASE}/local/nap/bo-qua`, {
    method: "POST",
    headers: { ...authHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ uuids }),
  }).then(json<{ bo: number; tombstone: number }>);

// ── Nháp chuẩn bị BỀN (NAP-01 task 50/51, CHANGES #32, TDD §9.3a) ────────────
export interface NhapCo {
  uuid: string;
  co_dia_chi: boolean;
  co_anh: boolean;
  co_tick: boolean;
  gplx_da_co_json?: string | null; // nháp GPLX đã có: null = chưa sửa, '[]' = đã xóa hết
  gplx_goc_json?: string | null;
}

export interface NhapChuanBi {
  uuid: string;
  dia_chi_json: string | null;
  chi_tiet: string | null;
  noi_cap: string | null;
  ngay_cap: string | null; // ngày cấp CCCD 'yyyymmdd' (CHANGES #43); null/'' = chưa đặt
  tick_json: string | null;
  jp2_b64: string | null;
  anh_preview: string | null;
  updated_at: string | null;
  chon_in_gplx?: number | null; // "Chọn in GPLX" đã chọn (1/2/3); null = theo mặc định của hạng
  gplx_da_co_json?: string | null;
  gplx_goc_json?: string | null;
}

// Cờ NHẸ (không kèm ảnh) để vẽ 2 chip cả lưới. Danh sách rỗng → không gọi mạng.
export const nhapCo = (uuids: string[]): Promise<NhapCo[]> =>
  uuids.length === 0
    ? Promise.resolve([])
    : fetch(`${BASE}/local/nap/nhap?uuids=${encodeURIComponent(uuids.join(","))}`, {
        headers: authHeaders(),
      }).then(json<NhapCo[]>);

// Đọc đầy đủ 1 nháp (kèm ảnh) — gọi khi mở drawer Chuẩn bị.
export const nhapDoc = (uuid: string) =>
  fetch(`${BASE}/local/nap/nhap/${encodeURIComponent(uuid)}`, { headers: authHeaders() }).then(
    json<NhapChuanBi>,
  );

// Lưu (upsert) nháp — gọi khi đóng drawer / debounce.
export const nhapLuu = (
  uuid: string,
  body: Partial<Omit<NhapChuanBi, "uuid" | "updated_at">>,
) =>
  fetch(`${BASE}/local/nap/nhap/${encodeURIComponent(uuid)}`, {
    method: "PUT",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  }).then(json<{ ok: boolean; uuid: string }>);

// Nút "Xóa nháp" — dọn 1 nháp (gồm ảnh PII) chủ động.
export const nhapXoa = (uuid: string) =>
  fetch(`${BASE}/local/nap/nhap/${encodeURIComponent(uuid)}`, {
    method: "DELETE",
    headers: authHeaders(),
  }).then(json<{ ok: boolean; uuid: string }>);

// ── QLY-09: Đối soát VPS↔CSDT (CHANGES #28, task 48/49) ──────────────────────
export interface DoiSoatDong {
  loai: string;              // "①" | "②" | "③"
  uuid?: string;
  ma_dk?: string;
  ho_ten?: string | null;
  trang_thai_vps?: string;   // ca ②
  locked_at?: string;        // ca ③
  hanh_dong: string;         // "da_nap" | "tra_ve_cho_nap" | "unlock"
}
export interface KhongTraDuoc { ma_dk: string; ho_ten?: string | null; ly_do?: string }

export const doiSoatKhoa = (maKh: string) =>
  fetch(`${BASE}/local/doi-soat/khoa?ma_kh=${encodeURIComponent(maKh)}`, { headers: authHeaders() })
    .then(json<{ ca2: DoiSoatDong[]; khong_tra_duoc: KhongTraDuoc[] }>);

export const quetLac = () =>
  fetch(`${BASE}/local/doi-soat/lac`, { headers: authHeaders() })
    .then(json<{ phantom: DoiSoatDong[]; treo: DoiSoatDong[] }>);

const _dsPost = (path: string) =>
  fetch(`${BASE}${path}`, { method: "POST", headers: authHeaders() }).then(json<{ ok: boolean }>);

export const doiSoatDaNap = (uuid: string, maDk: string) =>
  _dsPost(`/local/doi-soat/da-nap?uuid=${encodeURIComponent(uuid)}&ma_dk=${encodeURIComponent(maDk)}`);
export const doiSoatTraVe = (uuid: string) =>
  _dsPost(`/local/doi-soat/tra-ve?uuid=${encodeURIComponent(uuid)}`);
export const doiSoatMoKhoa = (uuid: string) =>
  _dsPost(`/local/doi-soat/mo-khoa?uuid=${encodeURIComponent(uuid)}`);

// Ảnh thô cần Bearer → tải bằng fetch rồi tạo object URL (thẻ <img> không gửi header được).
// Chưa có ảnh (404) → null.
export const taiAnhKeoVe = async (uuid: string): Promise<string | null> => {
  const r = await fetch(`${BASE}/local/nap/keo/${uuid}/anh`, { headers: authHeaders() });
  if (r.status === 404) return null;
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return URL.createObjectURL(await r.blob());
};

// QLY-05 (CHANGES #32) — ảnh THÔ học viên gửi còn trên VPS, tra theo ma_dk (nguồn bổ sung ảnh cho
// HV thiếu ảnh). Hết hạn/không tra được (404) → null → UI ẩn nguồn này, chỉ còn chọn-file.
export const taiAnhVps = async (maDk: string): Promise<string | null> => {
  const r = await fetch(`${BASE}/local/ho-so/anh-vps?ma_dk=${encodeURIComponent(maDk)}`, { headers: authHeaders() });
  if (r.status === 404) return null;
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return URL.createObjectURL(await r.blob());
};

export interface NapLoDong {
  uuid: string;
  ok: boolean;
  ma_dk?: string;
  so_ho_so?: string;
  so_giay_to?: number;
  loi?: string;
}

export interface NapLoKetQua {
  tong: number;
  thanh_cong: number;
  that_bai: number;
  ket_qua: NapLoDong[];
}

// Nạp lô các HV đã chuẩn bị đủ (khóa + địa chỉ + giấy tờ + ảnh). 1 lỗi không hỏng cả lô.
export const napLo = (items: NapIn[]) =>
  fetch(`${BASE}/local/nap/nap-lo`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ items }),
  }).then(json<NapLoKetQua>);

// ── Phân hệ Đồng bộ CDB — Quản lý CSDL đích (SYNC-02) ──
export interface SyncTarget {
  key: string;
  name: string;
  database: string;
}
export interface SyncOptions {
  tt_xuly_force: string;
  update_tong_so_hv: boolean;
}
export interface TtXuLyOption {
  ma: string;
  ten: string;
  ghi_chu: string;
}
export interface SyncTargetsData {
  targets: SyncTarget[];
  selected: string;
  options: SyncOptions;
  tt_xuly_options: TtXuLyOption[];
}
export interface SyncTestKetQua {
  ok: boolean;
  count: number;
  message: string;
}

export const getSyncTargets = () =>
  fetch(`${BASE}/local/sync/targets`, { headers: authHeaders() }).then(json<SyncTargetsData>);

export const saveSyncTargets = (
  targets: SyncTarget[],
  selected: string,
  options: SyncOptions,
) =>
  fetch(`${BASE}/local/sync/targets`, {
    method: "PUT",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ targets, selected, options }),
  }).then(json<SyncTargetsData>);

export const testSyncTarget = (database: string) =>
  fetch(`${BASE}/local/sync/targets/test`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ database }),
  }).then(json<SyncTestKetQua>);

// ── Phân hệ Đồng bộ CDB — Bàn đồng bộ (SYNC-01) ──
export interface SyncKhoa {
  ma_kh: string;
  ten_kh: string;
  hang_gplx: string;
  ngay_kg: string | null;
  so_hv: number;
  bc1?: boolean;
  dkkh?: boolean; // khóa đích đã kết xuất đăng ký khóa học lên Sở (lọc ở Bàn đồng bộ)
}
export interface SyncHV {
  ho_ten: string | null;
  so_cmt: string;
  hang_gplx: string | null;
  ma_dk_nguon: string | null;
  ngay_hs_nguon: string | null;
  da_co_dich: boolean;
  ma_dk_dich: string | null;
  ngay_hs_dich: string | null;
  so_hs_dich: number | null;
  thieu_cccd: boolean;
  trung_cccd_nguon: boolean;
}
export interface SyncHocVienData {
  hoc_vien: SyncHV[];
  tong: number;
  da_co_dich: number;
  se_tao_moi: number;
  thieu_cccd: number;
  trung_cccd_nguon: number;
}

const qs = (o: Record<string, string | number | undefined>) =>
  Object.entries(o)
    .filter(([, v]) => v !== undefined && v !== "")
    .map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`)
    .join("&");

export const getSyncNam = (ben: "nguon" | "dich", targetKey?: string) =>
  fetch(`${BASE}/local/sync/${ben}/nam?${qs({ target_key: ben === "dich" ? targetKey : undefined })}`, {
    headers: authHeaders(),
  }).then(json<number[]>);

export const getSyncKhoa = (ben: "nguon" | "dich", nam: number, targetKey?: string) =>
  fetch(`${BASE}/local/sync/${ben}/khoa?${qs({ nam, target_key: ben === "dich" ? targetKey : undefined })}`, {
    headers: authHeaders(),
  }).then(json<SyncKhoa[]>);

export const postSyncHocVien = (maKhNguon: string, targetKey?: string) =>
  fetch(`${BASE}/local/sync/hoc-vien`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ ma_kh_nguon: maKhNguon, target_key: targetKey }),
  }).then(json<SyncHocVienData>);

// ── TCB-01: Tra cứu CDB đích (đọc GPLX_CDB_CSDT) ──
export interface KhoaCDB {
  ma_kh: string;
  ten_kh: string;
  hang_gplx: string;
  hang_dt: string | null;
  bc1: boolean;   // khóa đã lập Báo cáo 1 (cấp khóa) — cờ cảnh báo
  dkkh: boolean;  // đã kết xuất DKKH (SoQD_KhaiGiang có giá trị)
}
// Dòng HV đích = HoSoRow + tt_xuly (hiện thêm ở chi tiết CDB).
export type HoSoRowCDB = HoSoRow & { tt_xuly: string | null };

export const traCuuKhoaCDB = (q: string, targetKey?: string) =>
  fetch(`${BASE}/local/sync/tra-cuu/khoa?${qs({ q, target_key: targetKey })}`, { headers: authHeaders() }).then(
    json<KhoaCDB[]>,
  );
export const dsHoSoCDB = (makh: string, targetKey?: string) =>
  fetch(`${BASE}/local/sync/tra-cuu/ho-so?${qs({ makh, target_key: targetKey })}`, { headers: authHeaders() }).then(
    json<HoSoRowCDB[]>,
  );
export const khoaCuaMaDkCDB = (maDk: string, targetKey?: string) =>
  fetch(`${BASE}/local/sync/tra-cuu/khoa-cua-madk?${qs({ ma_dk: maDk, target_key: targetKey })}`, {
    headers: authHeaders(),
  }).then(json<KhoaCDB>);
export const taiAnhCDB = (maDk: string, targetKey?: string, v = 0) =>
  taiAnhPNG(`/local/sync/tra-cuu/anh?${qs({ ma_dk: maDk, target_key: targetKey, v: v || undefined })}`);
export const taiAnhThumbCDB = (maDk: string, targetKey?: string, v = 0) =>
  taiAnhPNG(`/local/sync/tra-cuu/anh-thumb?${qs({ ma_dk: maDk, target_key: targetKey, v: v || undefined })}`);
// TCB-02 — thay ảnh HV ở CDB (ghi đè file dùng chung + backup _BACKUP + UPDATE cột ảnh CDB).
export const napAnhCDB = (maDk: string, jp2B64: string, targetKey?: string) =>
  fetch(`${BASE}/local/sync/tra-cuu/nap-anh?${qs({ ma_dk: maDk, target_key: targetKey })}`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ jp2_b64: jp2B64 }),
  }).then(json<{ ok: boolean; ma_dk: string; duong_dan_anh: string; co_anh: boolean }>);

// TCB-03 — sửa nhân thân HV ở CDB. chi-tiet-sua trả cờ dkkh (chặn sửa nếu đã kết xuất DKKH).
export interface HoSoChiTietCDB {
  ma_dk: string;
  ho_ten: string;
  ngay_sinh: string; // dd/mm/yyyy hoặc yyyy
  gioi_tinh: string; // M/F/U
  gioi_tinh_ten: string;
  so_cccd: string;
  noi_tt: string;
  hktt: string | null;
  ma_kh: string;
  dkkh: boolean;
  // #37 — mã hiện tại để form preselect (bỏ trống khi lưu = giữ cũ)
  noi_tt_ma_dvhc: string;
  noi_tt_ma_dvql: string;
  ngay_cap_cmt: string; // 'yyyymmdd' | ''
  noi_cap_cmt: string;  // mã Sở GTVT (MaDVQL)
  noi_cap_ten: string;
}
// #37 — body sửa CDB (RIÊNG với HoSoSuaIn của Nạp): +địa chỉ 2 cấp + ngày/nơi cấp CCCD.
export interface HoSoSuaCDBIn {
  ho_ten: string;
  ngay_sinh: string;
  gioi_tinh: string;
  so_cccd: string;
  noi_tt: string;
  noi_tt_ma_dvhc: string; // '' = giữ cũ
  noi_tt_ma_dvql: string;
  ngay_cap_cmt: string;   // 'yyyymmdd' | '' (giữ cũ)
  noi_cap_cmt: string;
}
export const chiTietSuaCDB = (maDk: string, targetKey?: string) =>
  fetch(`${BASE}/local/sync/tra-cuu/chi-tiet-sua?${qs({ ma_dk: maDk, target_key: targetKey })}`, {
    headers: authHeaders(),
  }).then(json<HoSoChiTietCDB>);
// #37 — danh mục Tỉnh/Xã/Sở ĐỌC TỪ DB ĐÍCH (theo target_key), không dùng /local/dvhc/* (DB Nạp).
export const getTinhCDB = (targetKey?: string) =>
  fetch(`${BASE}/local/sync/tra-cuu/dvhc/tinh?${qs({ target_key: targetKey })}`, { headers: authHeaders() }).then(
    json<Tinh[]>,
  );
export const getXaCDB = (tinh: string, targetKey?: string) =>
  fetch(`${BASE}/local/sync/tra-cuu/dvhc/xa?${qs({ tinh, target_key: targetKey })}`, { headers: authHeaders() }).then(
    json<Xa[]>,
  );
export const getSoGtvtCDB = (targetKey?: string) =>
  fetch(`${BASE}/local/sync/tra-cuu/dvhc/so-gtvt?${qs({ target_key: targetKey })}`, { headers: authHeaders() }).then(
    json<SoGtvt[]>,
  );
export const suaHoSoCDB = (maDk: string, body: HoSoSuaCDBIn, targetKey?: string) =>
  fetch(`${BASE}/local/sync/tra-cuu/sua?${qs({ ma_dk: maDk, target_key: targetKey })}`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  }).then(json<{ ok: boolean; ma_dk: string; canh_bao: string }>);

// TCB-05 — GPLX đã có ở DB đích.
export const gplxHoSoCDB = (maDk: string, targetKey?: string) =>
  fetch(`${BASE}/local/sync/tra-cuu/gplx?${qs({ ma_dk: maDk, target_key: targetKey })}`, { headers: authHeaders() }).then(json<GplxHoSo>);

export const luuGplxHoSoCDB = (maDk: string, gplx: unknown[], tho: Record<string, string>, targetKey?: string) =>
  luuGplx(`${BASE}/local/sync/tra-cuu/gplx?${qs({ ma_dk: maDk, target_key: targetKey })}`, gplx, tho);

export const noiCapGplxCDB = (targetKey?: string) =>
  fetch(`${BASE}/local/sync/tra-cuu/noi-cap-gplx?${qs({ target_key: targetKey })}`, { headers: authHeaders() }).then(json<SoGtvt[]>);

// TCB-04 — xóa HV / đổi khóa ở CDB (chặn theo MaBC1; đổi khóa cùng hạng chưa BC1, giữ DuongDanAnh).
export const khoaCungHangCDB = (maDk: string, targetKey?: string) =>
  fetch(`${BASE}/local/sync/tra-cuu/khoa-cung-hang?${qs({ ma_dk: maDk, target_key: targetKey })}`, {
    headers: authHeaders(),
  }).then(json<KhoaDich[]>);
export const xoaHoSoCDB = (maDk: string, targetKey?: string) =>
  fetch(`${BASE}/local/sync/tra-cuu/xoa?${qs({ ma_dk: maDk, target_key: targetKey })}`, {
    method: "POST",
    headers: authHeaders(),
  }).then(json<{ ok: boolean; ma_dk: string }>);
export const doiKhoaCDB = (maDk: string, maKhDich: string, targetKey?: string) =>
  fetch(`${BASE}/local/sync/tra-cuu/doi-khoa?${qs({ ma_dk: maDk, target_key: targetKey })}`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ ma_kh_dich: maKhDich }),
  }).then(json<{ ok: boolean; ma_dk: string; ma_kh_moi: string }>);

export interface SyncRunIn {
  ma_kh_nguon: string;
  ma_kh_dich: string;
  ngay_nhap_hs: string; // ISO yyyy-mm-dd
  target_key?: string;
  so_cmt_chon: string[];
  ten_kh_nguon?: string; // tên khóa để ghi nhật ký Lịch sử (CHANGES #41)
  ten_kh_dich?: string;
}
export const postSyncRun = (body: SyncRunIn) =>
  fetch(`${BASE}/local/sync/run`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  }).then(json<{ job_id: string }>);

// Đọc SSE bằng fetch (EventSource không đặt được header Bearer). Gọi onEvent cho
// mỗi sự kiện {loai,...}. Trả AbortController để hủy (job nền vẫn chạy tới hết).
export function openSyncStream(jobId: string, onEvent: (ev: Record<string, unknown>) => void) {
  const ctrl = new AbortController();
  void (async () => {
    const r = await fetch(`${BASE}/local/sync/stream?job=${encodeURIComponent(jobId)}`, {
      headers: authHeaders(),
      signal: ctrl.signal,
    });
    if (!r.ok || !r.body) throw new Error(String(r.status));
    const reader = r.body.getReader();
    const dec = new TextDecoder();
    let buf = "";
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      let i: number;
      while ((i = buf.indexOf("\n\n")) >= 0) {
        const chunk = buf.slice(0, i);
        buf = buf.slice(i + 2);
        const line = chunk.split("\n").find((l) => l.startsWith("data:"));
        if (line) {
          try {
            onEvent(JSON.parse(line.slice(5).trim()));
          } catch {
            /* bỏ qua dòng không phải JSON (keepalive) */
          }
        }
      }
    }
  })().catch(() => {
    /* abort/ngắt mạng — bỏ qua, UI đã có nút chạy lại */
  });
  return ctrl;
}

// ── Phân hệ Đồng bộ CDB — Lịch sử & Hủy sync (SYNC-03) ──
export interface SyncLichSuRow {
  khoa_moi: string;          // mã khóa ĐÍCH (CDB)
  khoa_cu: string | null;    // mã khóa NGUỒN (CSDT)
  ten_khoa_moi: string;      // tên khóa đích (rỗng nếu bản cũ + DB không tra được)
  ten_khoa_cu: string;       // tên khóa nguồn
  sync_at: string; // ISO
  can_bo: string;
  so_tao: number;
}
export const getSyncLichSu = (targetKey?: string) =>
  fetch(`${BASE}/local/sync/lich-su?${qs({ target_key: targetKey })}`, { headers: authHeaders() }).then(
    json<SyncLichSuRow[]>,
  );

export interface SyncRollbackPreview {
  log_count: number;
  log_con_dich: number;
  sync_group: number;
  tong: number;
}
export const getSyncRollbackPreview = (maKh: string, targetKey?: string) =>
  fetch(`${BASE}/local/sync/rollback/preview?${qs({ ma_kh: maKh, target_key: targetKey })}`, {
    headers: authHeaders(),
  }).then(json<SyncRollbackPreview>);

export interface SyncRollbackKetQua {
  hs_del: number;
  nlx_del: number;
  tong_so_hv: number | null;
}
export const postSyncRollback = (maKh: string, targetKey?: string) =>
  fetch(`${BASE}/local/sync/rollback`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ ma_kh: maKh, target_key: targetKey }),
  }).then(json<SyncRollbackKetQua>);

// ── KQD-01: Cập nhật kết quả đào tạo (đọc GPLX_CDB_CSDT) ──

// Băng nhắc CSDL đích ở header (dùng chung mọi phân hệ ghi DB đích).
export interface DbDichInfo {
  database: string | null;
  host: string | null;
  ma_csdt: string | null;
  connected: boolean;
}
export const getDbDichInfo = (targetKey?: string) =>
  fetch(`${BASE}/local/ketqua/db-dich-info?${qs({ target_key: targetKey })}`, {
    headers: authHeaders(),
  }).then(json<DbDichInfo>);

export interface KhoaKQD {
  ma_kh: string;
  ten_kh: string;
  hang_gplx: string;
  ngay_kg: string | null;
  ngay_bg: string | null;
  ngay_thi: string | null;
  dem: {
    dangky: number; capnhat: number; tuchoi: number; giaitrinh: number; ketxuat: number;
    // KQD-04 đổi #77: nhóm có điều kiện cho dải tab (chokx = 09 + 90 Đạt; canxuly = 14 + 90 không đạt/trống)
    chokx?: number; khongdat?: number; canxuly?: number; dagui?: number;
  };
}
export const dsKhoaKQD = (q: string, targetKey?: string) =>
  fetch(`${BASE}/local/ketqua/khoa?${qs({ q, target_key: targetKey })}`, { headers: authHeaders() }).then(
    json<KhoaKQD[]>,
  );

export interface DiemKQD {
  ly_thuyet: number | null;
  mo_phong: number | null;
  hinh: number | null;
  tien_lui: number | null;
  duong: number | null;
}
export interface HocVienKQD {
  ma_dk: string;
  ho_ten: string;
  ngay_sinh: string;
  so_cccd: string;
  so_ho_so: string;
  hang: string | null;
  ma_hang_moi: string | null;
  ma_hang: string | null;
  tt_xuly: string | null;
  ket_luan: "dat" | "khong_dat" | null;
  diem: DiemKQD;
  gio_duong: number | null; // giờ đường đã lưu ở DB đích (thập phân, làm tròn 2 chữ số)
  km_duong: number | null;
  ly_do_tu_choi?: string | null; // KQD-04 #77: lý do Sở từ chối (LyDoTuChoiKQDT) — hiện trên dòng HV 14
  giai_trinh?: string | null; // giải trình đã lưu (GiaiTrinh)
}
// Nhóm lọc trạng thái (khớp _NHOM_TT backend) + 'all'. ketxuat=12 (KQD-03 "đã kết xuất").
export type TrangThaiKQD =
  | "all" | "dangky" | "capnhat" | "tuchoi" | "giaitrinh" | "ketxuat"
  | "chokx" | "khongdat" | "canxuly" | "dagui";   // task 138: nhóm có điều kiện
export const dsHocVienKQD = (maKh: string, trangThai: TrangThaiKQD, targetKey?: string) =>
  fetch(`${BASE}/local/ketqua/hoc-vien?${qs({ ma_kh: maKh, trang_thai: trangThai, target_key: targetKey })}`, {
    headers: authHeaders(),
  }).then(json<HocVienKQD[]>);

// ── KQD-07: kiểm trước kết xuất (chỉ đọc, đúng 1 khóa) + luật môn bắt buộc dùng chung với KQD-02 ──
export interface KiemTruocKQD {
  ma_kh: string;
  tong: number;
  du: number;
  mo_to_bo_qua: number;
  dem: {
    chua_co_diem?: number; thieu_mon?: number; thieu_gio_km?: number; thieu_ket_luan?: number;
    thieu_giai_trinh?: number; khong_dat_o_90?: number; giai_trinh_trong?: number;   // task 139
  };
  thieu: {
    ma_dk: string;
    ho_ten: string;
    so_cccd: string;
    tt_xuly: string | null;
    ly_do: string[];
    mon_thieu: string[];
    canh_bao: { loai: string; gia_tri: number; goi_y: number }[];
  }[];
}
export const kiemTruocKQD = (maKh: string, targetKey?: string) =>
  fetch(`${BASE}/local/ketqua/kiem-truoc?${qs({ ma_kh: maKh, target_key: targetKey })}`, {
    headers: authHeaders(),
  }).then(json<KiemTruocKQD>);
// ── KQD-09: xuất Excel kết quả học tập theo khóa — server LƯU file vào thư mục `output` của phần mềm ──
export interface XuatExcelKetQua {
  ok: boolean;
  ten_file: string;
  duong_dan: string;
  thu_muc: string;
  so_hoc_vien: number;
  so_hv_trong_ket_qua?: number; // KQD-10: HV có kết luận nhưng thiếu điểm nên ô kết quả trong sổ để trống
}
export const xuatExcelKQD = (maKh: string, targetKey?: string) =>
  fetch(`${BASE}/local/ketqua/xuat-excel?${qs({ ma_kh: maKh, target_key: targetKey })}`, {
    method: "POST", headers: authHeaders(),
  }).then(json<XuatExcelKetQua>);
// KQD-10: "Sổ theo dõi kết quả học tập" (mẫu Phụ lục VI) — cùng khuôn lưu vào `output`.
export const xuatSoTheoDoiKQD = (maKh: string, targetKey?: string) =>
  fetch(`${BASE}/local/ketqua/xuat-so-theo-doi?${qs({ ma_kh: maKh, target_key: targetKey })}`, {
    method: "POST", headers: authHeaders(),
  }).then(json<XuatExcelKetQua>);
export const moThuMucXuat = () =>
  fetch(`${BASE}/local/ketqua/mo-thu-muc-xuat`, { method: "POST", headers: authHeaders() }).then(json<{ ok: boolean; thu_muc: string }>);

// ── KQD-08: nạp giờ/km đường từ PDF DAT (xem trước → lưu hàng loạt, chỉ 2 cột giờ/km) ──
export type TinhTrangDat =
  | "khop" | "chua_chay_dat" | "khong_co_trong_khoa" | "da_ket_xuat" | "loi_dong" | "trung_dong";
export interface DatDong {
  stt: number;
  ma_dk: string;
  ho_ten: string;
  gio_cu: number | null;
  km_cu: number | null;
  gio_moi: number | null;
  km_moi: number | null;
  tinh_trang: TinhTrangDat;
  canh_bao: { loai: string; gia_tri: number; goi_y: number }[];
  co_thay_doi: boolean;
  chon_duoc: boolean;
  tick_san: boolean;
  ghi_chu: string | null;
  khoa_khac?: string | null; // "không có trong khóa": khóa khác đang chứa mã/người này (nếu tra ra)
}
export interface DatXemTruoc {
  ma_kh: string;
  hang: string | null;
  tong_file: number;
  dong: DatDong[];
  vang_trong_file: { ma_dk: string; ho_ten: string; so_cccd: string | null }[];
}
export const xemTruocDatKQD = (maKh: string, file: File, targetKey?: string) => {
  const fd = new FormData();
  fd.append("ma_kh", maKh);
  fd.append("file", file);
  return fetch(`${BASE}/local/ketqua/dat/xem-truoc?${qs({ target_key: targetKey })}`, {
    method: "POST", headers: authHeaders(), body: fd,
  }).then(json<DatXemTruoc>);
};
export interface DatLuuKetQua {
  ok: boolean;
  da_luu: number;
  bo_qua: { ma_dk: string; ly_do: string }[];
}
export const luuDatKQD = (
  body: { ma_kh: string; dong: { ma_dk: string; gio_duong: number; km_duong: number }[] },
  targetKey?: string,
) =>
  fetch(`${BASE}/local/ketqua/dat/luu?${qs({ target_key: targetKey })}`, {
    method: "POST", headers: authHeaders({ "Content-Type": "application/json" }), body: JSON.stringify(body),
  }).then(json<DatLuuKetQua>);

export const luatKQD = () =>
  fetch(`${BASE}/local/ketqua/luat`, { headers: authHeaders() }).then(json<{ mon_bat_buoc: string[] }>);

// ── KQD-02: nhập điểm → quy đổi → ghi CDB ──
export type ChuongTrinh = "cu" | "moi";
export const getChuongTrinhKQD = (maKh: string) =>
  fetch(`${BASE}/local/ketqua/chuong-trinh?${qs({ ma_kh: maKh })}`, { headers: authHeaders() }).then(
    json<{ ma_kh: string; ct: ChuongTrinh }>,
  );
export const setChuongTrinhKQD = (maKh: string, ct: ChuongTrinh) =>
  fetch(`${BASE}/local/ketqua/chuong-trinh`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ ma_kh: maKh, ct }),
  }).then(json<{ ma_kh: string; ct: ChuongTrinh }>);

export interface DiemGocKQD {
  ly_thuyet: number;
  mo_phong: number;
  hinh: number;
  tien_lui: number;
  duong: number;
}
export interface CapNhatKQDIn {
  ma_dk: string;
  diem_goc: Partial<DiemGocKQD>; // KQD-02: đủ 5; KQD-06 sửa lẻ: chỉ môn sửa lại
  giu_quydoi?: Partial<DiemGocKQD> | null; // KQD-06 sửa lẻ: {mon: quy đổi /10 đã lưu} cho môn giữ
  km_san?: number | null;
  gio_duong?: number | null;
  km_duong?: number | null;
  ngay_ra_qdtn?: string; // dd/mm/yyyy
  tg_bat_dau?: string;
  tg_ket_thuc?: string;
  giai_trinh?: string | null; // KQD-04: null = không đụng; '' = xóa; chuỗi = ghi
  giai_trinh_chung?: string | null; // KQD-04 #77: giải trình chung của khóa — chỉ ghi khi cột đang trống
}
// KQD-04: lý do Sở từ chối (chỉ đọc) + giải trình hiện có.
export const getGiaiTrinhKQD = (maDk: string, targetKey?: string) =>
  fetch(`${BASE}/local/ketqua/giai-trinh?${qs({ ma_dk: maDk, target_key: targetKey })}`, {
    headers: authHeaders(),
  }).then(json<{ ma_dk: string; ly_do_tu_choi: string | null; giai_trinh: string | null }>);
export interface CapNhatKQDOut {
  ok: boolean;
  ma_dk: string;
  ket_luan: "dat" | "khong_dat";
  tt_moi: string;
  so_giay: string | null;
  quy_doi: DiemGocKQD;
  ct: ChuongTrinh;
  thieu_giai_trinh?: boolean; // KQD-04 #77: HV 14 Đạt mà chưa có giải trình → chưa kết xuất được
  canh_bao?: string | null; // "chua_chuyen_90": đã lưu điểm nhưng bước chuyển sang 90 lỗi
}
export const capNhatKQD = (body: CapNhatKQDIn, targetKey?: string) =>
  fetch(`${BASE}/local/ketqua/cap-nhat?${qs({ target_key: targetKey })}`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  }).then(json<CapNhatKQDOut>);

// ── KQD-04 #77 (task 137): giải trình + chuyển 14→90 HÀNG LOẠT, mẫu giải trình ──
export interface GiaiTrinhLoBoQua {
  ma_dk: string;
  ly_do: string;
  chi_tiet?: { ly_do: string[]; mon_thieu: string[] };
}
export interface GiaiTrinhLoKetQua {
  ok: boolean;
  da_chuyen: string[];
  bo_qua: GiaiTrinhLoBoQua[];
  giu_rieng: number;
}
export const giaiTrinhLoKQD = (
  body: { ma_dk: string[]; noi_dung: string; ghi_de_rieng?: boolean },
  targetKey?: string,
) =>
  fetch(`${BASE}/local/ketqua/giai-trinh-lo?${qs({ target_key: targetKey })}`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  }).then(json<GiaiTrinhLoKetQua>);

export interface MauGiaiTrinh {
  mau: string[];
  phien_ban: number;
}
export const dsMauGiaiTrinhKQD = (targetKey?: string) =>
  fetch(`${BASE}/local/ketqua/mau-giai-trinh?${qs({ target_key: targetKey })}`, {
    headers: authHeaders(),
  }).then(json<MauGiaiTrinh>);
export const luuMauGiaiTrinhKQD = (body: { mau: string[]; phien_ban: number | null }, targetKey?: string) =>
  fetch(`${BASE}/local/ketqua/mau-giai-trinh?${qs({ target_key: targetKey })}`, {
    method: "PUT",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  }).then(json<MauGiaiTrinh>);

// KQD-06: xóa điểm (reset HV 09/10 về chưa có điểm, TT='03'). 409 nếu HV không ở 09/10.
export const xoaDiemKQD = (maDk: string, targetKey?: string) =>
  fetch(`${BASE}/local/ketqua/xoa-diem?${qs({ target_key: targetKey })}`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ ma_dk: maDk }),
  }).then(json<{ ok: boolean; ma_dk: string; tt_moi: string }>);

// ── KQD-03/05: cổng B-1 mở khóa (gói hàng đợi gửi của CSĐT — CHỈ ĐỌC) ──
// Gói lọc theo NoiGui=<mã CSĐT> (CSĐT-wide, không nối khóa). Panel KQD-03 dùng chung dữ liệu này.
export interface GoiHangDoi {
  id: string;
  ten_file: string;
  duong_dan: string;
  ngay_tao: string | null; // dd/mm/yyyy HH:mm
  kich_thuoc: number | null;
}
export interface MoKhoaTrangThai {
  ma_csdt: string;
  mo_duoc: boolean; // cổng B-1: còn gói chưa gửi → mở khóa được
  goi_chua_gui: GoiHangDoi[];
  goi_da_gui: GoiHangDoi[];
  so_hv_mo: number; // HV 12 sẽ lùi (có kết luận)
  so_hv_bo_qua: number; // HV 12 KetLuanCSDT NULL → bỏ qua
  so_khoa: number;
}
export const moKhoaTrangThai = (targetKey?: string) =>
  fetch(`${BASE}/local/ketqua/mo-khoa?${qs({ target_key: targetKey })}`, { headers: authHeaders() }).then(
    json<MoKhoaTrangThai>,
  );

// POST mở khóa (KQD-05 task 77): xóa gói chưa gửi + lùi mọi HV 12 của cơ sở về 09/10.
// ma_kh chỉ để log/ngữ cảnh (thao tác CSĐT-wide). giai_trinh ghi cho mọi HV được lùi.
export interface MoKhoaKetQua {
  ok: boolean;
  ma_csdt: string;
  so_hv_mo: number;
  so_goi_xoa: number;
  so_hv_bo_qua: number;
  so_khoa: number;
}
// 409 (cơ sở đã gửi hết gói) → ném Error "khoa_cung" để UI mở lại trạng thái M1.
export const moKhoa = async (
  body: { ma_kh?: string | null; giai_trinh?: string | null },
  targetKey?: string,
): Promise<MoKhoaKetQua> => {
  const r = await fetch(`${BASE}/local/ketqua/mo-khoa?${qs({ target_key: targetKey })}`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  });
  if (r.status === 409) throw new Error("khoa_cung");
  return json<MoKhoaKetQua>(r);
};

// ── KQD-05 mở rộng (task 83/84, CHANGES #53): "Sửa sau khi đã gửi Sở" — chọn từng HV ──
// Chỉ dùng khi cơ sở HẾT gói chưa gửi (còn gói chưa gửi → moKhoa ở trên). KHÔNG xóa gói.
export interface SuaSauGuiKetQua {
  ok: boolean;
  so_mo: number;
  mo: { ma_dk: string; ho_ten: string; tt_moi: string }[];
  bo_qua: { ma_dk: string; ly_do: string }[];
}
// Lỗi nghiệp vụ 409: loi = 'con_goi_chua_gui' | 'co_hv_13' (kèm thong_bao tiếng Việt).
export class SuaSauGuiLoi extends Error {
  loi: string;
  constructor(loi: string, thongBao: string) {
    super(thongBao);
    this.loi = loi;
  }
}
export const moSuaSauGui = async (
  body: { ma_dk: string[]; ly_do: string },
  targetKey?: string,
): Promise<SuaSauGuiKetQua> => {
  const r = await fetch(`${BASE}/local/ketqua/mo-sua-sau-gui?${qs({ target_key: targetKey })}`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  });
  if (r.status === 409) {
    const d = (await r.json().catch(() => null))?.detail;
    throw new SuaSauGuiLoi(d?.loi ?? "xung_dot", d?.thong_bao ?? "Không mở sửa được (trạng thái đã đổi).");
  }
  return json<SuaSauGuiKetQua>(r);
};

export interface SuaSauGuiDiem {
  ly_thuyet: number | null;
  mo_phong: number | null;
  hinh: number | null;
  tien_lui: number | null;
  duong: number | null;
  ket_luan: "dat" | "khong_dat" | null;
}
export interface SuaSauGuiMuc {
  id: number;
  ma_dk: string;
  ma_kh: string | null;
  ho_ten: string;
  nguoi: string | null;
  luc_mo: string | null; // dd/mm/yyyy HH:mm
  ly_do: string;
  tt_xuly: string | null;
  diem_truoc: Partial<SuaSauGuiDiem>;
  diem_hien: SuaSauGuiDiem;
}
// HV đã mở sửa sau gửi mà chưa kết xuất lại (server tự dọn HV đã về 12).
export const dsSuaSauGui = (targetKey?: string) =>
  fetch(`${BASE}/local/ketqua/sua-sau-gui?${qs({ target_key: targetKey })}`, { headers: authHeaders() }).then(
    json<SuaSauGuiMuc[]>,
  );

// ── Phân công GV – xe (PCG) — /local/phancong/* ──
export interface KhoaPC {
  ma_kh: string;
  ten_kh: string;
  hang_gplx: string;
  hang_dt: string;
  hang_nhom: string;
  hang_xe: string;
  kg: string; // yyyy-mm-dd
  bg: string;
  so_hv: number;
  da_dkkh: boolean;
}
export interface MonPC {
  id: number;
  ten: string;
}
export interface PcDong {
  id: number | string | null;
  ma: string;
  mon: number[];
  tu: string; // yyyy-mm-ddTHH:mm
  den: string;
}
export interface GhepDong {
  id: number | string | null;
  ma: string;
  xe: string;
  tu: string;
  den: string;
  dia_diem: string;
}
export interface BanNhapPC {
  gv_khoa: string[];
  pc: PcDong[];
  xe_khoa: string[];
  ghep: GhepDong[];
}
export interface HienTrangPC {
  khoa: KhoaPC;
  gv_khoa: { id: number; ma: string }[];
  pc: PcDong[];
  xe_khoa: { id: number; bs: string }[];
  ghep: GhepDong[];
  /** Băm hiện trạng CDB lúc đọc; gửi lại ở `/ghi` — khác thì server trả 409 `khoa_da_doi` (CHANGES #59). */
  dau_van_tay?: string;
}
export interface BanKhacPC {
  [k: string]: unknown;
}
export interface GiaoVienPC {
  ma: string;
  ten: string;
  loai: string; // LT | TH | AL
  active: boolean;
  hang_gplx: string;
  hang_duoc_day: string[];
  /** Server: hạng được đào tạo có hợp để dạy THỰC HÀNH khóa này không (chỉ để cảnh báo). */
  hop_hang?: boolean;
  ban: BanKhacPC[];
}
export interface XePC {
  bs: string;
  hang: string;
  active: boolean;
  gp_het: string;
  ban: BanKhacPC[];
}
export type MucVanDe = "chan" | "canh_bao" | "thong_tin";
export interface VanDePC {
  muc: MucVanDe;
  ma: string;
  buoc: number;
  ref: string; // pc-<id> | gh-<ma> | gv-<ma> | xe-<bs>
  ai: string;
  noi_dung: string;
}
export interface KiemTraPC {
  vande: VanDePC[];
  tom_tat: Record<string, number>;
  co_chan: boolean;
}
export interface GhiPCKetQua {
  ok: boolean;
  da_ghi: { loai: string; mo_ta: string }[];
  chua_ghi: { loai: string; mo_ta: string }[];
  loi: string | null;
  thong_bao?: string;
  hien_trang?: Omit<HienTrangPC, "khoa">;
}

export const dsKhoaPC = (q: string, targetKey?: string) =>
  fetch(`${BASE}/local/phancong/khoa?${qs({ q, target_key: targetKey })}`, { headers: authHeaders() }).then(json<KhoaPC[]>);
export const dsMonPC = (targetKey?: string) =>
  fetch(`${BASE}/local/phancong/mon?${qs({ target_key: targetKey })}`, { headers: authHeaders() }).then(json<MonPC[]>);
export const hienTrangPC = (maKh: string, targetKey?: string) =>
  fetch(`${BASE}/local/phancong/khoa/${encodeURIComponent(maKh)}?${qs({ target_key: targetKey })}`, {
    headers: authHeaders(),
  }).then(json<HienTrangPC>);
export const dsGiaoVienPC = (maKh: string, targetKey?: string) =>
  fetch(`${BASE}/local/phancong/giao-vien?${qs({ ma_kh: maKh, target_key: targetKey })}`, {
    headers: authHeaders(),
  }).then(json<{ giao_vien: GiaoVienPC[] }>);
export const dsXePC = (maKh: string, targetKey?: string) =>
  fetch(`${BASE}/local/phancong/xe?${qs({ ma_kh: maKh, target_key: targetKey })}`, {
    headers: authHeaders(),
  }).then(json<{ xe: XePC[] }>);
export const kiemTraPC = (maKh: string, ban: BanNhapPC, targetKey?: string) =>
  fetch(`${BASE}/local/phancong/kiem-tra?${qs({ target_key: targetKey })}`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ ma_kh: maKh, ...ban }),
  }).then(json<KiemTraPC>);
export const ghiPC = async (
  maKh: string,
  ban: BanNhapPC,
  xacNhan: { da_xem_canh_bao: boolean; xac_nhan_csdl_that: boolean; dau_van_tay?: string },
  targetKey?: string,
): Promise<GhiPCKetQua> => {
  const r = await fetch(`${BASE}/local/phancong/ghi?${qs({ target_key: targetKey })}`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ ma_kh: maKh, ...ban, ...xacNhan }),
  });
  if (r.status === 400 || r.status === 409) {
    const d = (await r.json().catch(() => null))?.detail;
    throw new Error(typeof d === "string" ? d : d?.thong_bao ?? "Không ghi được (trạng thái đã đổi).");
  }
  return json<GhiPCKetQua>(r);
};

export interface GoiYGhepXe {
  ma: string;
  ten: string;
  xe: string; // "" = không có xe hợp lệ
  tu: string;
  den: string;
  canh_bao: string[];
  ly_do: string;
}
export const goiYGhepXe = (maKh: string, ban: BanNhapPC, targetKey?: string) =>
  fetch(`${BASE}/local/phancong/goi-y-ghep-xe?${qs({ target_key: targetKey })}`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ ma_kh: maKh, ...ban }),
  }).then(json<{ goi_y: GoiYGhepXe[] }>);

// ── PCG-06: hạn giấy tờ xe/GPLX giáo viên + GV/xe ngưng còn phân công (chỉ đọc, toàn cơ sở) ──
export interface KhoaGanPC { ma_kh: string; ten_kh: string }
export interface GiayHanPC { giay: string; ngay: string; con_ngay: number; muc: string }
export interface XeHanPC { bien_so: string; hang: string; muc?: string; giay: GiayHanPC[]; khoa: KhoaGanPC[] }
export interface GvHanPC { ma_gv: string; ho_ten: string; hang: string; muc?: string; giay: GiayHanPC[]; khoa: KhoaGanPC[] }
export interface HanGiayToPC {
  hom_nay: string;
  nguong: number;
  xe: { het_han: XeHanPC[]; sap_het: XeHanPC[]; chua_khai: { bien_so: string; hang: string; khoa: KhoaGanPC[] }[] };
  gv: { het_han: GvHanPC[]; sap_het: GvHanPC[]; chua_khai: { ma_gv: string; ho_ten: string; hang: string; khoa: KhoaGanPC[] }[] };
  ngung: {
    xe: { bien_so: string; hang: string; khoa: KhoaGanPC[] }[];
    gv: { ma_gv: string; ho_ten: string; hang: string; khoa: KhoaGanPC[] }[];
  };
  dem: Record<string, number>;
}
export const hanGiayToPC = (ngay: number, targetKey?: string) =>
  fetch(`${BASE}/local/phancong/han-giay-to?${qs({ ngay, target_key: targetKey })}`, { headers: authHeaders() }).then(
    json<HanGiayToPC>,
  );

export interface RaSoatKhoaPC {
  ma_kh: string;
  ten_kh: string;
  hang_dt: string;
  kg: string;
  bg: string;
  da_dkkh: boolean;
  gv_ds: number;
  gv_chua_pc: number;
  pc_ngoai_ds: number;
  xe_ds: number;
  xe_chua_ghep: number;
  ghep_ngoai_ds: number;
  can_xu_ly: boolean;
}
export const raSoatPC = (targetKey?: string) =>
  fetch(`${BASE}/local/phancong/ra-soat?${qs({ target_key: targetKey })}`, { headers: authHeaders() }).then(json<RaSoatKhoaPC[]>);
