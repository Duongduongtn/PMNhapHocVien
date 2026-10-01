// Gọi API tool chạy localhost. Dev: webui 3011 ↔ backend 8000 (khác origin).
// Khi đóng gói .exe, webui static do chính FastAPI phục vụ → cùng origin (BASE rỗng).
const BASE = import.meta.env.DEV ? "http://localhost:8000" : "";

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
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json() as Promise<T>;
}

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
  fetch(`${BASE}/local/khoa-hoc?loai=${loai}`).then(json<KhoaHoc[]>);

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

export const getTinh = () => fetch(`${BASE}/local/dvhc/tinh`).then(json<Tinh[]>);

export const getXa = (tinh: string) =>
  fetch(`${BASE}/local/dvhc/xa?tinh=${encodeURIComponent(tinh)}`).then(json<Xa[]>);

export const mapDiaChi = (dc: { tinh: string; huyen: string; xa: string }) =>
  fetch(`${BASE}/local/dvhc/map`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(dc),
  }).then(json<MapKetQua>);
