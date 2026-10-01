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
