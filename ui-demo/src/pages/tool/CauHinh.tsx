import { useState } from "react";
import { Icon } from "../../components/Icon";

export default function CauHinh() {
  const [testResult, setTestResult] = useState<"idle" | "ok">("idle");

  return (
    <div className="p-4 max-w-2xl">
      <div className="flex items-center gap-2 mb-1">
        <h2 className="text-base font-bold">Cấu hình kết nối</h2>
        <span className="text-[11px] font-semibold text-primary bg-primary/10 rounded-full px-2 py-0.5">HTG-01</span>
      </div>
      <p className="text-[12px] text-muted-foreground mb-4">Khai báo kết nối tới SQL Server và VPS. Lưu vào cấu hình cục bộ (mã hóa), không commit.</p>

      {/* SQL Server */}
      <div className="rounded-lg border border-border bg-card p-4 mb-4">
        <h3 className="text-sm font-bold mb-3 flex items-center gap-2"><Icon name="db" className="w-4 h-4 text-primary" /> SQL Server (DB đích)</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-3">
          <div><label className="field-label">Server <span className="text-destructive">*</span></label><input className="field-input mt-1" defaultValue="DESKTOP-UBV2GQI" /></div>
          <div><label className="field-label">Database <span className="text-destructive">*</span></label><input className="field-input mt-1" defaultValue="GPLX_CSDT" /></div>
          <div><label className="field-label">User (login riêng, không sa) <span className="text-destructive">*</span></label><input className="field-input mt-1" defaultValue="gplx_tool" /></div>
          <div><label className="field-label">Password <span className="text-destructive">*</span></label><input type="password" className="field-input mt-1" defaultValue="password" /></div>
        </div>
      </div>

      {/* VPS */}
      <div className="rounded-lg border border-border bg-card p-4 mb-4">
        <h3 className="text-sm font-bold mb-3 flex items-center gap-2"><Icon name="refresh" className="w-4 h-4 text-primary" /> Kết nối VPS (kéo hồ sơ)</h3>
        <div className="space-y-3">
          <div><label className="field-label">URL VPS <span className="text-destructive">*</span></label><input className="field-input mt-1" defaultValue="https://thunhan.example.vn/api" /></div>
          <div><label className="field-label">API key (khóa máy) <span className="text-destructive">*</span></label><input type="password" className="field-input mt-1" defaultValue="tool-api-key" /></div>
        </div>
      </div>

      {/* Kiểm tra + lưu */}
      <div className="flex items-center gap-3 flex-wrap">
        <button
          onClick={() => setTestResult("ok")}
          className="inline-flex items-center gap-2 h-10 px-4 rounded-lg border border-primary text-primary font-semibold text-sm hover:bg-primary/5 transition-colors"
        >
          <Icon name="refresh" className="w-4 h-4" /> Kiểm tra kết nối
        </button>
        <button className="inline-flex items-center gap-2 h-10 px-5 rounded-lg bg-primary text-primary-foreground font-semibold text-sm hover:brightness-110 transition-all shadow-sm">
          <Icon name="check" className="w-4 h-4" sw={3} /> Lưu cấu hình
        </button>
        {testResult === "ok" && (
          <span className="inline-flex items-center gap-1.5 text-[13px] font-semibold text-success bg-success/10 border border-success/30 rounded-full px-3 py-1.5">
            <Icon name="check" className="w-4 h-4" sw={3} /> Kết nối SQL Server + VPS thành công
          </span>
        )}
      </div>
    </div>
  );
}
