import { useEffect, useState } from "react";
import { Icon } from "./Icon";
import {
  getConfig, putConfig, testConfig, type ToolConfig, type TestResult,
  getSyncTargets, saveSyncTargets, testSyncTarget,
  type SyncTarget, type SyncOptions, type TtXuLyOption, type SyncTestKetQua,
} from "../lib/api";

// Form cấu hình kết nối dùng chung (HTG-07 + DGT-03). Gộp 2 khối TÁCH BẠCH:
//   ① CSDL để NẠP hồ sơ (nguồn khi đồng bộ) — tông primary
//   ② Các CSDL ĐÍCH để đồng bộ sang           — tông sync (teal)
// Dùng ở 2 nơi: CauHinhDrawer (⚙ header) và Wizard thiết lập lần đầu (DGT-03).
// Backend không đổi: /local/config* (khối ①) + /local/sync/targets (khối ②).

const EMPTY_CFG: ToolConfig = {
  sqlserver_host: "", sqlserver_database: "", sqlserver_user: "",
  sqlserver_password: "", vps_url: "", vps_api_key: "",
};

interface Hang extends SyncTarget {
  _rid: number; // id tạm để render khi key chưa sinh
}
let _seq = 1;
const moiRid = () => _seq++;

interface Props {
  /** Tải/làm tươi dữ liệu khi true (drawer: lúc mở; wizard: lúc vào bước cấu hình). */
  active: boolean;
  /** DGT-03 test-before-next: báo kết quả test khối ① (SQL + VPS đều xanh). */
  onBlock1Test?: (ok: boolean) => void;
  /** DGT-03: báo đã lưu kết nối khối ① (để wizard cho qua bước). */
  onBlock1Saved?: () => void;
}

export default function CauHinhForm({ active, onBlock1Test, onBlock1Saved }: Props) {
  // ── Khối ① — kết nối chung + CSDL Nạp ──
  const [cfg, setCfg] = useState<ToolConfig>(EMPTY_CFG);
  const [loading1, setLoading1] = useState(true);
  const [testing1, setTesting1] = useState(false);
  const [result1, setResult1] = useState<TestResult | null>(null);
  const [saveMsg1, setSaveMsg1] = useState("");
  const [err1, setErr1] = useState("");

  // ── Khối ② — CSDL đích để sync ──
  const [rows, setRows] = useState<Hang[]>([]);
  const [selected, setSelected] = useState("");
  const [opts, setOpts] = useState<SyncOptions>({ tt_xuly_force: "03", update_tong_so_hv: true });
  const [ttList, setTtList] = useState<TtXuLyOption[]>([]);
  const [loading2, setLoading2] = useState(true);
  const [dirty2, setDirty2] = useState(false);
  const [saveMsg2, setSaveMsg2] = useState("");
  const [err2, setErr2] = useState("");
  const [test2, setTest2] = useState<Record<number, SyncTestKetQua & { dang?: boolean }>>({});

  // Nạp dữ liệu khi active (gọi mỗi lần active bật; tắt rồi bật lại thì làm tươi).
  useEffect(() => {
    if (!active) return;
    setLoading1(true);
    setLoading2(true);
    setResult1(null); setSaveMsg1(""); setErr1("");
    setSaveMsg2(""); setErr2(""); setDirty2(false); setTest2({});
    getConfig()
      .then((c) => setCfg({ ...EMPTY_CFG, ...c }))
      .catch(() => setErr1("Không đọc được cấu hình (tool backend chưa chạy?)"))
      .finally(() => setLoading1(false));
    getSyncTargets()
      .then((d) => {
        setRows(d.targets.map((t) => ({ ...t, _rid: moiRid() })));
        setSelected(d.selected);
        setOpts(d.options);
        setTtList(d.tt_xuly_options);
      })
      .catch(() => setErr2("Không đọc được danh sách CSDL đích."))
      .finally(() => setLoading2(false));
  }, [active]);

  // ── Khối ① handlers ──
  const set1 = (k: keyof ToolConfig) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setCfg({ ...cfg, [k]: e.target.value });
    setResult1(null); setSaveMsg1(""); onBlock1Test?.(false); // đổi giá trị → phải test lại
  };
  const test1 = async () => {
    setTesting1(true); setErr1(""); setResult1(null);
    try {
      const res = await testConfig(cfg);
      setResult1(res);
      onBlock1Test?.(res.sqlserver.ok && res.vps.ok);
    } catch {
      setErr1("Gọi kiểm tra thất bại — kiểm tool backend.");
      onBlock1Test?.(false);
    } finally {
      setTesting1(false);
    }
  };
  const save1 = async () => {
    setErr1("");
    try {
      setCfg({ ...EMPTY_CFG, ...(await putConfig(cfg)) });
      setSaveMsg1("Đã lưu kết nối (mã hóa cục bộ).");
      onBlock1Saved?.();
    } catch {
      setErr1("Lưu kết nối thất bại.");
    }
  };

  // ── Khối ② handlers ──
  const doi2 = (fn: () => void) => { fn(); setDirty2(true); setSaveMsg2(""); };
  const suaRow = (rid: number, k: "name" | "database", v: string) =>
    doi2(() => {
      setRows((rs) => rs.map((r) => (r._rid === rid ? { ...r, [k]: v } : r)));
      if (k === "database") setTest2((t) => { const n = { ...t }; delete n[rid]; return n; });
    });
  const themRow = () => doi2(() => setRows((rs) => [...rs, { _rid: moiRid(), key: "", name: "", database: "" }]));
  const xoaRow = (rid: number) =>
    doi2(() =>
      setRows((rs) => {
        const r = rs.find((x) => x._rid === rid);
        const next = rs.filter((x) => x._rid !== rid);
        if (r && r.key === selected) setSelected(next[0]?.key ?? "");
        return next;
      }),
    );
  const thuKetNoi2 = async (rid: number, database: string) => {
    if (!database.trim()) return;
    setTest2((t) => ({ ...t, [rid]: { ok: false, count: 0, message: "", dang: true } }));
    try {
      const res = await testSyncTarget(database);
      setTest2((t) => ({ ...t, [rid]: { ...res, dang: false } }));
    } catch {
      setTest2((t) => ({ ...t, [rid]: { ok: false, count: 0, message: "Gọi kiểm tra thất bại", dang: false } }));
    }
  };
  const save2 = async () => {
    setErr2("");
    const sach = rows.filter((r) => r.name.trim() && r.database.trim());
    if (sach.length !== rows.length) {
      setErr2("Mỗi CSDL đích cần cả Tên hiển thị và Database.");
      return;
    }
    try {
      const d = await saveSyncTargets(
        sach.map(({ key, name, database }) => ({ key, name, database })),
        selected,
        opts,
      );
      setRows(d.targets.map((t) => ({ ...t, _rid: moiRid() })));
      setSelected(d.selected);
      setOpts(d.options);
      setDirty2(false);
      setTest2({});
      setSaveMsg2("Đã lưu danh sách CSDL đích (mã hóa cục bộ).");
    } catch {
      setErr2("Lưu danh sách CSDL đích thất bại.");
    }
  };

  return (
    <div className="space-y-5">
      {/* ══ Khối ① — CSDL để NẠP (primary) ══ */}
      <section className="rounded-lg border border-border bg-card overflow-hidden">
        <div className="px-4 py-3 border-b border-border bg-accent/40 flex items-start gap-2.5">
          <span className="mt-0.5 inline-grid place-items-center w-7 h-7 rounded-lg bg-primary text-primary-foreground shrink-0">
            <Icon name="db" className="w-4 h-4" />
          </span>
          <div className="min-w-0">
            <h3 className="text-[13.5px] font-bold flex items-center gap-2">
              CSDL để <span className="text-primary">NẠP hồ sơ</span>
              <span className="text-[10px] font-semibold text-primary bg-accent rounded-full px-1.5 py-0.5">nguồn</span>
            </h3>
            <p className="text-[11.5px] text-muted-foreground leading-snug mt-0.5">
              Nơi tool ghi hồ sơ thu nhận vào. Khi <b>Đồng bộ CDB</b>, đây là CSDL <b>nguồn</b> để đọc học viên.
            </p>
          </div>
        </div>

        <fieldset disabled={loading1} className="p-4 space-y-3 disabled:opacity-60">
          {loading1 && (
            <div className="flex items-center gap-2 text-[13px] text-muted-foreground">
              <Icon name="refresh" className="w-4 h-4 animate-spin" /> Đang tải…
            </div>
          )}
          <div className="grid grid-cols-2 gap-x-3 gap-y-3">
            <div>
              <label className="field-label">Server <span className="text-destructive">*</span></label>
              <input className="field-input mt-1" placeholder="VD: MAY-DB" value={cfg.sqlserver_host} onChange={set1("sqlserver_host")} />
            </div>
            <div>
              <label className="field-label">Database (nguồn) <span className="text-destructive">*</span></label>
              <input className="field-input mt-1 font-[ui-monospace] text-[12px]" placeholder="GPLX_CSDT" value={cfg.sqlserver_database} onChange={set1("sqlserver_database")} />
            </div>
            <div>
              <label className="field-label">User (login riêng, không sa) <span className="text-destructive">*</span></label>
              <input className="field-input mt-1" placeholder="gplx_tool" value={cfg.sqlserver_user} onChange={set1("sqlserver_user")} />
            </div>
            <div>
              <label className="field-label">Mật khẩu <span className="text-destructive">*</span></label>
              <input type="password" className="field-input mt-1" placeholder="••••••" value={cfg.sqlserver_password} onChange={set1("sqlserver_password")} />
            </div>
            <div>
              <label className="field-label">URL VPS <span className="text-destructive">*</span></label>
              <input className="field-input mt-1" placeholder="https://ten-mien/api" value={cfg.vps_url} onChange={set1("vps_url")} />
            </div>
            <div>
              <label className="field-label">API key (khóa máy) <span className="text-destructive">*</span></label>
              <input type="password" className="field-input mt-1" placeholder="••••••" value={cfg.vps_api_key} onChange={set1("vps_api_key")} />
            </div>
          </div>

          <p className="text-[11.5px] text-muted-foreground -mt-0.5">
            Server / User / Mật khẩu này <b>dùng chung</b> cho các CSDL đích ở khối ② bên dưới.
          </p>

          <div className="flex items-center gap-2.5 flex-wrap pt-0.5">
            <button
              onClick={test1}
              disabled={testing1}
              className="inline-flex items-center gap-1.5 h-9 px-3.5 rounded-lg border border-primary text-primary font-semibold text-[13px] hover:bg-primary/5 transition-colors disabled:opacity-60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <Icon name="refresh" className={"w-4 h-4 " + (testing1 ? "animate-spin" : "")} /> {testing1 ? "Đang kiểm tra…" : "Kiểm tra kết nối"}
            </button>
            <button
              onClick={save1}
              className="inline-flex items-center gap-1.5 h-9 px-4 rounded-lg bg-primary text-primary-foreground font-semibold text-[13px] hover:brightness-110 transition-all shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <Icon name="check" className="w-4 h-4" sw={3} /> Lưu kết nối
            </button>
            {saveMsg1 && (
              <span className="inline-flex items-center gap-1.5 text-[12.5px] font-semibold text-success bg-success/10 border border-success/30 rounded-full px-2.5 py-1">
                <Icon name="check" className="w-3.5 h-3.5" sw={3} /> {saveMsg1}
              </span>
            )}
          </div>

          {result1 && (
            <div className="space-y-1.5">
              {([["SQL Server", result1.sqlserver], ["VPS", result1.vps]] as const).map(([ten, r]) => (
                <div
                  key={ten}
                  className={
                    "flex items-center gap-2 text-[12.5px] rounded-lg px-3 py-1.5 border " +
                    (r.ok ? "text-success bg-success/10 border-success/30" : "text-destructive bg-destructive/10 border-destructive/30")
                  }
                >
                  <Icon name={r.ok ? "check" : "warn"} className="w-4 h-4 shrink-0" sw={r.ok ? 3 : 2} />
                  <span className="font-semibold">{ten}:</span> {r.message}
                </div>
              ))}
            </div>
          )}
          {err1 && (
            <div className="flex items-center gap-2 text-[12.5px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-1.5">
              <Icon name="warn" className="w-4 h-4 shrink-0" /> {err1}
            </div>
          )}
        </fieldset>
      </section>

      {/* ══ Khối ② — CSDL ĐÍCH để Sync (teal) ══ */}
      <section className="rounded-lg border border-sync-border bg-card overflow-hidden">
        <div className="px-4 py-3 border-b border-sync-border bg-sync-soft/60 flex items-start gap-2.5">
          <span className="mt-0.5 inline-grid place-items-center w-7 h-7 rounded-lg bg-sync text-white shrink-0">
            <Icon name="refresh" className="w-4 h-4" />
          </span>
          <div className="min-w-0">
            <h3 className="text-[13.5px] font-bold flex items-center gap-2">
              CSDL <span className="text-sync">ĐÍCH để đồng bộ sang</span>
              <span className="text-[10px] font-semibold text-sync bg-sync-soft rounded-full px-1.5 py-0.5">nhiều · chọn mặc định</span>
            </h3>
            <p className="text-[11.5px] text-muted-foreground leading-snug mt-0.5">
              Các DB CDB nhận học viên khi bấm <b>Đồng bộ</b>. Dùng chung Server / User / Mật khẩu ở khối ① — chỉ khác tên database.
            </p>
          </div>
        </div>

        <div className="p-4 space-y-3">
          {loading2 ? (
            <div className="flex items-center gap-2 text-[13px] text-muted-foreground">
              <Icon name="refresh" className="w-4 h-4 animate-spin" /> Đang tải…
            </div>
          ) : (
            <>
              <div className="rounded-lg border border-border overflow-hidden">
                <table className="w-full text-[12.5px]">
                  <thead>
                    <tr className="bg-sync text-white text-left">
                      <th className="font-semibold px-2.5 py-1.5 w-12 text-center" title="CSDL đích mặc định cho Bàn đồng bộ">Mặc định</th>
                      <th className="font-semibold px-2.5 py-1.5">Tên hiển thị</th>
                      <th className="font-semibold px-2.5 py-1.5">Database</th>
                      <th className="font-semibold px-2.5 py-1.5 w-9"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {rows.length === 0 && (
                      <tr>
                        <td colSpan={4} className="px-3 py-5 text-center text-[12.5px] text-muted-foreground">
                          Chưa có CSDL đích. Bấm “Thêm CSDL đích” để khai báo.
                        </td>
                      </tr>
                    )}
                    {rows.map((r) => {
                      const on = r.key !== "" && r.key === selected;
                      const tk = test2[r._rid];
                      return (
                        <tr key={r._rid} className={"border-t border-border " + (on ? "bg-sync-soft/50" : "")}>
                          <td className="px-2.5 py-1.5 text-center align-top pt-3">
                            <input
                              type="radio"
                              name="cfg-target-default"
                              className="accent-sync"
                              checked={on}
                              disabled={r.key === ""}
                              title={r.key === "" ? "Lưu trước để đặt mặc định" : "Đặt làm CSDL đích mặc định"}
                              onChange={() => doi2(() => setSelected(r.key))}
                            />
                          </td>
                          <td className="px-2.5 py-1.5">
                            <input
                              className="field-input"
                              value={r.name}
                              placeholder="VD: CDB chính"
                              onChange={(e) => suaRow(r._rid, "name", e.target.value)}
                            />
                            <div className="mt-1.5 flex items-center gap-2">
                              <button
                                type="button"
                                onClick={() => thuKetNoi2(r._rid, r.database)}
                                disabled={!r.database.trim() || tk?.dang}
                                className="inline-flex items-center gap-1 h-6 px-2 rounded-md border border-border text-[11.5px] hover:bg-muted transition-colors disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sync"
                              >
                                <Icon name="refresh" className={"w-3 h-3 " + (tk?.dang ? "animate-spin" : "")} /> Kiểm tra
                              </button>
                              {tk && !tk.dang && (
                                <span className={"inline-flex items-center gap-1 text-[11.5px] " + (tk.ok ? "text-success" : "text-destructive")}>
                                  <Icon name={tk.ok ? "check" : "warn"} className="w-3 h-3" sw={tk.ok ? 3 : 2} />
                                  {tk.message}
                                </span>
                              )}
                            </div>
                          </td>
                          <td className="px-2.5 py-1.5 align-top">
                            <input
                              className="field-input font-[ui-monospace] text-[12px]"
                              value={r.database}
                              placeholder="GPLX_CDB_CSDT"
                              onChange={(e) => suaRow(r._rid, "database", e.target.value)}
                            />
                          </td>
                          <td className="px-2.5 py-1.5 text-center align-top pt-2.5">
                            <button
                              type="button"
                              onClick={() => xoaRow(r._rid)}
                              title="Xóa khỏi danh sách (không xóa database thật)"
                              className="w-7 h-7 grid place-items-center rounded-md text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                            >
                              <Icon name="x" className="w-4 h-4" />
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              <button
                type="button"
                onClick={themRow}
                className="inline-flex items-center gap-1.5 h-8 px-3 rounded-lg border border-sync text-sync font-semibold text-[12.5px] hover:bg-sync-soft transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sync"
              >
                <Icon name="plus" className="w-4 h-4" /> Thêm CSDL đích
              </button>

              <div className="rounded-lg border border-border bg-muted/40 p-3 space-y-2.5">
                <h4 className="text-[12px] font-bold">Tùy chọn đồng bộ (áp cho mọi CSDL đích)</h4>
                <div className="flex items-center gap-2.5 flex-wrap">
                  <label className="field-label">Trạng thái xử lý gán cho hồ sơ sau sync</label>
                  <select
                    className="field-input max-w-xs"
                    value={opts.tt_xuly_force}
                    onChange={(e) => doi2(() => setOpts((o) => ({ ...o, tt_xuly_force: e.target.value })))}
                  >
                    {ttList.map((o) => (
                      <option key={o.ma} value={o.ma}>{o.ma} — {o.ten}</option>
                    ))}
                  </select>
                </div>
                <label className="inline-flex items-center gap-2 text-[12.5px] cursor-pointer">
                  <input
                    type="checkbox"
                    className="accent-sync"
                    checked={opts.update_tong_so_hv}
                    onChange={(e) => doi2(() => setOpts((o) => ({ ...o, update_tong_so_hv: e.target.checked })))}
                  />
                  Cập nhật lại tổng số học viên của khóa sau sync (đếm lại số thực tế)
                </label>
              </div>

              <div className="flex items-center gap-2.5 flex-wrap">
                <button
                  type="button"
                  onClick={save2}
                  disabled={!dirty2}
                  className="inline-flex items-center gap-1.5 h-9 px-4 rounded-lg bg-sync text-white font-semibold text-[13px] hover:brightness-110 transition-all shadow-sm disabled:opacity-50 disabled:shadow-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sync"
                >
                  <Icon name="check" className="w-4 h-4" sw={3} /> Lưu CSDL đích
                </button>
                {saveMsg2 && (
                  <span className="inline-flex items-center gap-1.5 text-[12.5px] font-semibold text-success bg-success/10 border border-success/30 rounded-full px-2.5 py-1">
                    <Icon name="check" className="w-3.5 h-3.5" sw={3} /> {saveMsg2}
                  </span>
                )}
              </div>

              {err2 && (
                <div className="flex items-center gap-2 text-[12.5px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-1.5">
                  <Icon name="warn" className="w-4 h-4 shrink-0" /> {err2}
                </div>
              )}
            </>
          )}
        </div>
      </section>
    </div>
  );
}
