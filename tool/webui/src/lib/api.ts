// Gọi API tool chạy localhost. Dev: webui 3011 ↔ backend 8000 (khác origin).
// Khi đóng gói .exe, webui static do chính FastAPI phục vụ → cùng origin (BASE rỗng).
const BASE = import.meta.env.DEV ? "http://localhost:8000" : "";

// Session token cục bộ (HTG-01③) — giữ trong bộ nhớ; tải lại trang phải đăng nhập lại.
let _token: string | null = null;
export const datToken = (t: string | null) => {
  _token = t;
};
// Header kèm Bearer cho endpoint /local/* nghiệp vụ (config/auth được miễn — A1).
function authHeaders(extra?: Record<string, string>): Record<string, string> {
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
}

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

async function json<T>(r: Response): Promise<T> {
  if (!r.ok) {
    const d = await r.json().catch(() => null);
    throw new Error(d?.detail || `${r.status} ${r.statusText}`);
  }
  return r.json() as Promise<T>;
}

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

export const getKhoaHoc = (loai: LoaiXe) =>
  fetch(`${BASE}/local/khoa-hoc?loai=${loai}`, { headers: authHeaders() }).then(json<KhoaHoc[]>);

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

export const getGiayTo = (maLoaiHs: number, hangDt: string) =>
  fetch(`${BASE}/local/giay-to?ma_loai_hs=${maLoaiHs}&hang_dt=${encodeURIComponent(hangDt)}`, {
    headers: authHeaders(),
  }).then(json<GiayTo[]>);

export interface NapIn {
  uuid: string;
  ma_khoa_hoc: string;
  ho_ten: string;
  ngay_sinh: string; // yyyymmdd
  gioi_tinh: string; // 'M' | 'F'
  so_cmt: string;
  chi_tiet_tt?: string; // số nhà/thôn — mặc định trống (NoiTT); KHÔNG nhét tên xã
  noi_tt_ma_dvhc: string;
  noi_tt_ma_dvql: string;
  chi_tiet_ct?: string;
  giay_to_tick: number[];
  anh_jp2_b64?: string | null;
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
