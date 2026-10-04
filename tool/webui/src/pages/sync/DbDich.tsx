import { useEffect, useState } from "react";
import { Icon } from "../../components/Icon";
import {
  getSyncTargets,
  saveSyncTargets,
  testSyncTarget,
  type SyncTarget,
  type SyncOptions,
  type TtXuLyOption,
  type SyncTestKetQua,
} from "../../lib/api";

interface Hang extends SyncTarget {
  _rid: number; // id tạm để render khi key chưa sinh
}
let _seq = 1;
const moiRid = () => _seq++;

export default function DbDich() {
  const [rows, setRows] = useState<Hang[]>([]);
  const [selected, setSelected] = useState("");
  const [opts, setOpts] = useState<SyncOptions>({ tt_xuly_force: "03", update_tong_so_hv: true });
  const [ttList, setTtList] = useState<TtXuLyOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [dirty, setDirty] = useState(false);
  const [saveMsg, setSaveMsg] = useState("");
  const [err, setErr] = useState("");
  const [test, setTest] = useState<Record<number, SyncTestKetQua & { dang?: boolean }>>({});

  useEffect(() => {
    getSyncTargets()
      .then((d) => {
        setRows(d.targets.map((t) => ({ ...t, _rid: moiRid() })));
        setSelected(d.selected);
        setOpts(d.options);
        setTtList(d.tt_xuly_options);
      })
      .catch(() => setErr("Không đọc được cấu hình (tool backend chưa chạy?)"))
      .finally(() => setLoading(false));
  }, []);

  const doi = (fn: () => void) => {
    fn();
    setDirty(true);
    setSaveMsg("");
  };
  const suaRow = (rid: number, k: "name" | "database", v: string) =>
    doi(() => {
      setRows((rs) => rs.map((r) => (r._rid === rid ? { ...r, [k]: v } : r)));
      // Đổi tên database → kết quả Kiểm tra cũ không còn đúng → xóa, buộc test lại.
      // (Việc chặn Tải danh sách khi chưa test thuộc màn Bàn đồng bộ.)
      if (k === "database") {
        setTest((t) => {
          const n = { ...t };
          delete n[rid];
          return n;
        });
      }
    });
  const themRow = () =>
    doi(() => setRows((rs) => [...rs, { _rid: moiRid(), key: "", name: "", database: "" }]));
  const xoaRow = (rid: number) =>
    doi(() =>
      setRows((rs) => {
        const r = rs.find((x) => x._rid === rid);
        const next = rs.filter((x) => x._rid !== rid);
        if (r && r.key === selected) setSelected(next[0]?.key ?? "");
        return next;
      }),
    );

  const thuKetNoi = async (rid: number, database: string) => {
    if (!database.trim()) return;
    setTest((t) => ({ ...t, [rid]: { ok: false, count: 0, message: "", dang: true } }));
    try {
      const res = await testSyncTarget(database);
      setTest((t) => ({ ...t, [rid]: { ...res, dang: false } }));
    } catch {
      setTest((t) => ({ ...t, [rid]: { ok: false, count: 0, message: "Gọi kiểm tra thất bại", dang: false } }));
    }
  };

  const luu = async () => {
    setErr("");
    const sach = rows.filter((r) => r.name.trim() && r.database.trim());
    if (sach.length !== rows.length) {
      setErr("Mỗi CSDL đích cần cả Tên hiển thị và Database.");
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
      setDirty(false);
      setTest({});
      setSaveMsg("Đã lưu cấu hình (mã hóa cục bộ).");
    } catch {
      setErr("Lưu cấu hình thất bại.");
    }
  };

  return (
    <div className="p-4 max-w-4xl">
      <h2 className="text-base font-bold mb-1">Quản lý CSDL đích</h2>
      <p className="text-[12.5px] text-muted-foreground mb-4">
        Các CSDL đích có thể đồng bộ sang. Dùng chung Server / User / Mật khẩu với màn Cấu hình —
        chỉ khác tên CSDL. Chấm tròn là CSDL đích mặc định cho Bàn đồng bộ.
      </p>

      {loading && (
        <div className="flex items-center gap-2 text-[13px] text-muted-foreground">
          <Icon name="refresh" className="w-4 h-4 animate-spin" /> Đang tải cấu hình…
        </div>
      )}

      {!loading && (
        <>
          <div className="rounded-lg border border-border bg-card overflow-hidden mb-3">
            <table className="w-full text-[13px]">
              <thead>
                <tr className="bg-primary text-primary-foreground text-left">
                  <th className="font-semibold px-3 py-2 w-12 text-center">Mặc định</th>
                  <th className="font-semibold px-3 py-2 w-[32%]">Tên hiển thị</th>
                  <th className="font-semibold px-3 py-2 w-[32%]">Database</th>
                  <th className="font-semibold px-3 py-2">Kết nối</th>
                  <th className="font-semibold px-3 py-2 w-10"></th>
                </tr>
              </thead>
              <tbody>
                {rows.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-3 py-6 text-center text-[13px] text-muted-foreground">
                      Chưa có CSDL đích. Bấm “Thêm CSDL đích” để khai báo.
                    </td>
                  </tr>
                )}
                {rows.map((r) => {
                  const on = r.key !== "" && r.key === selected;
                  const tk = test[r._rid];
                  return (
                    <tr key={r._rid} className={"border-t border-border " + (on ? "bg-sync-soft/50" : "")}>
                      <td className="px-3 py-2 text-center">
                        <input
                          type="radio"
                          name="target-default"
                          className="accent-sync"
                          checked={on}
                          disabled={r.key === ""}
                          title={r.key === "" ? "Lưu trước để đặt mặc định" : "Đặt làm CSDL đích mặc định"}
                          onChange={() => doi(() => setSelected(r.key))}
                        />
                      </td>
                      <td className="px-3 py-2">
                        <input
                          className="field-input"
                          value={r.name}
                          placeholder="VD: CDB chính"
                          onChange={(e) => suaRow(r._rid, "name", e.target.value)}
                        />
                      </td>
                      <td className="px-3 py-2">
                        <input
                          className="field-input font-[ui-monospace] text-[12px]"
                          value={r.database}
                          placeholder="GPLX_CDB_CSDT"
                          onChange={(e) => suaRow(r._rid, "database", e.target.value)}
                        />
                      </td>
                      <td className="px-3 py-2">
                        <div className="flex items-center gap-2">
                          <button
                            type="button"
                            onClick={() => thuKetNoi(r._rid, r.database)}
                            disabled={!r.database.trim() || tk?.dang}
                            className="inline-flex items-center gap-1 h-7 px-2.5 rounded-md border border-border text-[12px] hover:bg-muted transition-colors disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sync"
                          >
                            <Icon name="refresh" className={"w-3.5 h-3.5 " + (tk?.dang ? "animate-spin" : "")} /> Kiểm tra
                          </button>
                          {tk && !tk.dang && (
                            <span
                              className={
                                "inline-flex items-center gap-1 text-[12px] " +
                                (tk.ok ? "text-success" : "text-destructive")
                              }
                            >
                              <Icon name={tk.ok ? "check" : "warn"} className="w-3.5 h-3.5" sw={tk.ok ? 3 : 2} />
                              {tk.message}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-3 py-2 text-center">
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
            className="inline-flex items-center gap-1.5 h-9 px-3 rounded-lg border border-primary text-primary font-semibold text-[13px] hover:bg-primary/5 transition-colors mb-5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <Icon name="plus" className="w-4 h-4" /> Thêm CSDL đích
          </button>

          <div className="rounded-lg border border-border bg-muted/40 p-4 mb-5 max-w-2xl">
            <h3 className="text-[13px] font-bold text-foreground mb-3">Tùy chọn đồng bộ (áp cho mọi CSDL đích)</h3>
            <div className="flex items-center gap-3 mb-3 flex-wrap">
              <label className="field-label w-56">Trạng thái xử lý gán cho hồ sơ sau sync</label>
              <select
                className="field-input max-w-md"
                value={opts.tt_xuly_force}
                onChange={(e) => doi(() => setOpts((o) => ({ ...o, tt_xuly_force: e.target.value })))}
              >
                {ttList.map((o) => (
                  <option key={o.ma} value={o.ma}>
                    {o.ma} — {o.ten}
                  </option>
                ))}
              </select>
            </div>
            <label className="inline-flex items-center gap-2 text-[13px] cursor-pointer">
              <input
                type="checkbox"
                className="accent-primary"
                checked={opts.update_tong_so_hv}
                onChange={(e) => doi(() => setOpts((o) => ({ ...o, update_tong_so_hv: e.target.checked })))}
              />
              Cập nhật lại tổng số học viên của khóa sau sync (đếm lại số thực tế)
            </label>
          </div>

          <div className="flex items-center gap-3 flex-wrap">
            <button
              type="button"
              onClick={luu}
              disabled={!dirty}
              className="inline-flex items-center gap-2 h-10 px-5 rounded-lg bg-primary text-primary-foreground font-semibold text-sm hover:brightness-110 transition-all shadow-sm disabled:opacity-50 disabled:shadow-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <Icon name="check" className="w-4 h-4" sw={3} /> Lưu cấu hình
            </button>
            {saveMsg && (
              <span className="inline-flex items-center gap-1.5 text-[13px] font-semibold text-success bg-success/10 border border-success/30 rounded-full px-3 py-1.5">
                <Icon name="check" className="w-4 h-4" sw={3} /> {saveMsg}
              </span>
            )}
          </div>

          {err && (
            <div className="mt-4 flex items-center gap-2 text-[13px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2">
              <Icon name="warn" className="w-4 h-4" /> {err}
            </div>
          )}
        </>
      )}
    </div>
  );
}
