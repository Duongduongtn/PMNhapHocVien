// Gọi API VPS. Dev: webapp 3022 ↔ VPS khác origin (đặt VITE_API_BASE).
// Prod: static do nginx VPS phục vụ cùng origin với /api → BASE rỗng.
const BASE = import.meta.env.DEV ? (import.meta.env.VITE_API_BASE ?? "http://localhost:8000") : "";

// Token giữ trong bộ nhớ (TDD §5.1 "memory/secure") — KHÔNG lưu localStorage (tránh mất token qua XSS).
// Đổi lại: tải lại trang phải đăng nhập lại.
let _token: string | null = null;
export const datToken = (t: string | null) => {
  _token = t;
};

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function authHeaders(extra?: HeadersInit): HeadersInit {
  const h: Record<string, string> = { ...(extra as Record<string, string>) };
  if (_token) h.Authorization = `Bearer ${_token}`;
  return h;
}

async function json<T>(r: Response): Promise<T> {
  if (!r.ok) {
    const d = await r.json().catch(() => null);
    throw new ApiError(r.status, d?.detail || `${r.status} ${r.statusText}`);
  }
  return r.json() as Promise<T>;
}

export interface NguoiDung {
  id: string;
  username: string;
  ho_ten: string | null;
  vai_tro: string;
}

export interface DangNhapKetQua {
  access_token: string;
  username: string;
  ho_ten: string | null;
  vai_tro: string;
}

export const dangNhap = (username: string, password: string) =>
  fetch(`${BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  }).then(json<DangNhapKetQua>);

export const layMe = () => fetch(`${BASE}/api/auth/me`, { headers: authHeaders() }).then(json<NguoiDung>);

export const dangXuat = () =>
  fetch(`${BASE}/api/auth/logout`, { method: "POST", headers: authHeaders() });

// ---- Hồ sơ thu thập (THU-02) ----
// Khớp HoSoIn của server (server/app/routers/ho_so.py). uuid do client sinh (idempotent).
export interface HoSoGui {
  uuid: string;
  so_cccd: string | null;
  so_cmnd_cu: string | null;
  ho_ten: string | null;
  ngay_sinh: string | null; // yyyymmdd
  gioi_tinh: string | null; // M/F
  noi_tt_raw: string | null;
  ngay_cap_cccd: string | null; // yyyy-mm-dd
  noi_cap_cccd: string | null;
}

export interface HoSoOut {
  uuid: string;
  trang_thai: string; // pending | importing | imported | deleted
  so_cccd: string | null;
  so_cmnd_cu: string | null;
  ho_ten: string | null;
  ngay_sinh: string | null;
  gioi_tinh: string | null;
  noi_tt_raw: string | null;
  noi_cap_cccd: string | null;
  co_anh: boolean;
  ma_dk: string | null;
  created_at: string;
}

export const guiHoSo = (body: HoSoGui) =>
  fetch(`${BASE}/api/ho-so`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  }).then(json<HoSoOut>);

// Ảnh thô JPEG — upload riêng (TDD §6.3). KHÔNG tự đặt Content-Type để trình duyệt tự gắn boundary.
export const guiAnh = (uuid: string, blob: Blob) => {
  const fd = new FormData();
  fd.append("file", blob, "anh.jpg");
  return fetch(`${BASE}/api/ho-so/${uuid}/anh`, { method: "POST", headers: authHeaders(), body: fd }).then(json<HoSoOut>);
};

export const dsDaGui = () => fetch(`${BASE}/api/ho-so/cua-toi`, { headers: authHeaders() }).then(json<HoSoOut[]>);

// THU-04 (CHANGES #13): soi hàng đợi CSDT xem CCCD đã có hồ sơ CHƯA NẠP chưa — cảnh báo mềm.
export interface KiemTrungKq {
  trung: boolean;
  so_luong: number;
  nguoi_gui: string | null;
  luc: string | null; // ISO
  trang_thai: string | null;
}
export const kiemTrungCccd = (cccd: string, uuid?: string) =>
  fetch(`${BASE}/api/ho-so/kiem-trung?cccd=${encodeURIComponent(cccd)}${uuid ? `&uuid=${encodeURIComponent(uuid)}` : ""}`, {
    headers: authHeaders(),
  }).then(json<KiemTrungKq>);

// THU-02 (CHANGES #12): sửa hồ sơ đã gửi khi còn chờ nạp. Đã nạp/đang nạp → server trả 409.
export type HoSoSua = Partial<Omit<HoSoGui, "uuid">>;
export const suaHoSo = (uuid: string, body: HoSoSua) =>
  fetch(`${BASE}/api/ho-so/${uuid}`, {
    method: "PUT",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  }).then(json<HoSoOut>);

// Tải lại ảnh chân dung CỦA MÌNH để hiện thumbnail. Cần Bearer → fetch blob → objectURL.
// Chưa có ảnh / không phải của mình (404) → null (UI hiện placeholder).
export const taiAnhCuaToi = async (uuid: string): Promise<string | null> => {
  const r = await fetch(`${BASE}/api/ho-so/${uuid}/anh`, { headers: authHeaders() });
  if (r.status === 404) return null;
  if (!r.ok) throw new ApiError(r.status, `${r.status} ${r.statusText}`);
  return URL.createObjectURL(await r.blob());
};
