import { useEffect, useState } from "react";
import { Icon } from "../../components/Icon";
import { getConfig, putConfig, testConfig, type ToolConfig, type TestResult } from "../../lib/api";

const EMPTY: ToolConfig = {
  sqlserver_host: "",
  sqlserver_database: "",
  sqlserver_user: "",
  sqlserver_password: "",
  vps_url: "",
  vps_api_key: "",
};

export default function CauHinh() {
  const [cfg, setCfg] = useState<ToolConfig>(EMPTY);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState(false);
  const [result, setResult] = useState<TestResult | null>(null);
  const [saveMsg, setSaveMsg] = useState<string>("");
  const [err, setErr] = useState<string>("");

  // Nạp cấu hình đã lưu (mật khẩu/API key hiện dạng che ********).
  // Khóa form tới khi data về để không gõ nhầm vào field trống rồi bị ghi đè.
  useEffect(() => {
    getConfig()
      .then((c) => setCfg({ ...EMPTY, ...c }))
      .catch(() => setErr("Không đọc được cấu hình (tool backend chưa chạy?)"))
      .finally(() => setLoading(false));
  }, []);

  const set = (k: keyof ToolConfig) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setCfg({ ...cfg, [k]: e.target.value });
    setResult(null);
    setSaveMsg("");
  };

  const onTest = async () => {
    setTesting(true);
    setErr("");
    setResult(null);
    try {
      setResult(await testConfig(cfg));
    } catch {
      setErr("Gọi kiểm tra thất bại — kiểm tool backend.");
    } finally {
      setTesting(false);
    }
  };

  const onSave = async () => {
    setErr("");
    try {
      setCfg({ ...EMPTY, ...(await putConfig(cfg)) });
      setSaveMsg("Đã lưu cấu hình (mã hóa cục bộ).");
    } catch {
      setErr("Lưu cấu hình thất bại.");
    }
  };

  return (
    <div className="p-4 max-w-2xl">
      <div className="flex items-center gap-2 mb-1">
        <h2 className="text-base font-bold">Cấu hình kết nối</h2>
        <span className="text-[11px] font-semibold text-primary bg-primary/10 rounded-full px-2 py-0.5">HTG-01</span>
      </div>
      <p className="text-[12px] text-muted-foreground mb-4">
        Khai báo kết nối tới SQL Server và VPS. Lưu vào cấu hình cục bộ (mã hóa), không commit.
      </p>

      {loading && (
        <div className="mb-4 flex items-center gap-2 text-[13px] text-muted-foreground">
          <Icon name="refresh" className="w-4 h-4 animate-spin" /> Đang tải cấu hình…
        </div>
      )}

      {/* Khóa toàn bộ input/nút tới khi tải xong */}
      <fieldset disabled={loading} className="contents">
      {/* SQL Server */}
      <div className="rounded-lg border border-border bg-card p-4 mb-4">
        <h3 className="text-sm font-bold mb-3 flex items-center gap-2">
          <Icon name="db" className="w-4 h-4 text-primary" /> SQL Server (DB đích)
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-3">
          <div>
            <label className="field-label">Server <span className="text-destructive">*</span></label>
            <input className="field-input mt-1" placeholder="VD: MAY-DB" value={cfg.sqlserver_host} onChange={set("sqlserver_host")} />
          </div>
          <div>
            <label className="field-label">Database <span className="text-destructive">*</span></label>
            <input className="field-input mt-1" placeholder="GPLX_CSDT" value={cfg.sqlserver_database} onChange={set("sqlserver_database")} />
          </div>
          <div>
            <label className="field-label">User (login riêng, không sa) <span className="text-destructive">*</span></label>
            <input className="field-input mt-1" placeholder="gplx_tool" value={cfg.sqlserver_user} onChange={set("sqlserver_user")} />
          </div>
          <div>
            <label className="field-label">Password <span className="text-destructive">*</span></label>
            <input type="password" className="field-input mt-1" placeholder="••••••" value={cfg.sqlserver_password} onChange={set("sqlserver_password")} />
          </div>
        </div>
      </div>

      {/* VPS */}
      <div className="rounded-lg border border-border bg-card p-4 mb-4">
        <h3 className="text-sm font-bold mb-3 flex items-center gap-2">
          <Icon name="refresh" className="w-4 h-4 text-primary" /> Kết nối VPS (kéo hồ sơ)
        </h3>
        <div className="space-y-3">
          <div>
            <label className="field-label">URL VPS <span className="text-destructive">*</span></label>
            <input className="field-input mt-1" placeholder="https://ten-mien/api" value={cfg.vps_url} onChange={set("vps_url")} />
          </div>
          <div>
            <label className="field-label">API key (khóa máy) <span className="text-destructive">*</span></label>
            <input type="password" className="field-input mt-1" placeholder="••••••" value={cfg.vps_api_key} onChange={set("vps_api_key")} />
          </div>
        </div>
      </div>

      {/* Kiểm tra + lưu */}
      <div className="flex items-center gap-3 flex-wrap">
        <button
          onClick={onTest}
          disabled={testing}
          className="inline-flex items-center gap-2 h-10 px-4 rounded-lg border border-primary text-primary font-semibold text-sm hover:bg-primary/5 transition-colors disabled:opacity-60"
        >
          <Icon name="refresh" className="w-4 h-4" /> {testing ? "Đang kiểm tra…" : "Kiểm tra kết nối"}
        </button>
        <button
          onClick={onSave}
          className="inline-flex items-center gap-2 h-10 px-5 rounded-lg bg-primary text-primary-foreground font-semibold text-sm hover:brightness-110 transition-all shadow-sm"
        >
          <Icon name="check" className="w-4 h-4" sw={3} /> Lưu cấu hình
        </button>
        {saveMsg && (
          <span className="inline-flex items-center gap-1.5 text-[13px] font-semibold text-success bg-success/10 border border-success/30 rounded-full px-3 py-1.5">
            <Icon name="check" className="w-4 h-4" sw={3} /> {saveMsg}
          </span>
        )}
      </div>
      </fieldset>

      {/* Kết quả kiểm tra từng kênh */}
      {result && (
        <div className="mt-4 space-y-2">
          {([["SQL Server", result.sqlserver], ["VPS", result.vps]] as const).map(([ten, r]) => (
            <div
              key={ten}
              className={
                "flex items-center gap-2 text-[13px] rounded-lg px-3 py-2 border " +
                (r.ok ? "text-success bg-success/10 border-success/30" : "text-destructive bg-destructive/10 border-destructive/30")
              }
            >
              <Icon name={r.ok ? "check" : "warn"} className="w-4 h-4" sw={r.ok ? 3 : 2} />
              <span className="font-semibold">{ten}:</span> {r.message}
            </div>
          ))}
        </div>
      )}

      {err && (
        <div className="mt-4 flex items-center gap-2 text-[13px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2">
          <Icon name="warn" className="w-4 h-4" /> {err}
        </div>
      )}
    </div>
  );
}
