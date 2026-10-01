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
