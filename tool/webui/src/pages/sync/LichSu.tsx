import { useEffect, useState } from "react";
import { Icon } from "../../components/Icon";
import HuyncSyncDialog from "../../components/HuyncSyncDialog";
import {
  getSyncLichSu, getSyncTargets,
  type SyncLichSuRow, type SyncTarget,
} from "../../lib/api";

// ISO (yyyy-mm-ddTHH:MM:SS) → dd/mm/yyyy HH:mm
const fmtLuc = (s: string) => {
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(s);
  return m ? `${m[3]}/${m[2]}/${m[1]} ${m[4]}:${m[5]}` : s;
};

export default function LichSu() {
  const [rows, setRows] = useState<SyncLichSuRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [targets, setTargets] = useState<SyncTarget[]>([]);
  const [targetKey, setTargetKey] = useState("");
  const [huyRow, setHuyRow] = useState<SyncLichSuRow | null>(null);
  const [toast, setToast] = useState("");

  const dichTarget = targets.find((t) => t.key === targetKey);

  const taiDS = (tk?: string) => {
    setLoading(true);
    getSyncLichSu(tk)
      .then(setRows)
      .catch(() => setErr("Không đọc được nhật ký sync (tool backend chưa chạy?)"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    getSyncTargets()
      .then((d) => { setTargets(d.targets); setTargetKey(d.selected); taiDS(d.selected); })
      .catch(() => taiDS());
  }, []);

  return (
    <div className="h-full overflow-auto p-4">
      <div className="max-w-4xl">
        <h1 className="text-base font-bold mb-1">Lịch sử &amp; Hủy sync</h1>
        <p className="text-[12.5px] text-muted-foreground mb-4 max-w-3xl">
          Các lần đồng bộ đã ghi nhật ký trên máy tool. Hủy một khóa sẽ xóa học viên do tool tạo
          (Người lái + Hồ sơ + Giấy tờ) khỏi CSDL đích — <b>không hoàn tác được</b>.
          Hủy sync ghi vào CSDL đích đang chọn: <b className="text-sync">{dichTarget ? `${dichTarget.name} (${dichTarget.database})` : "chưa chọn — vào ⚙ Cấu hình"}</b>.
        </p>

        {toast && (
          <div className="mb-3 flex items-center gap-2 text-[13px] text-success bg-success/10 border border-success/30 rounded-lg px-3 py-2">
            <Icon name="check" className="w-4 h-4 shrink-0" sw={3} /> {toast}
            <button onClick={() => setToast("")} className="ml-auto text-muted-foreground hover:text-foreground"><Icon name="x" className="w-4 h-4" /></button>
          </div>
        )}
        {err && (
          <div className="mb-3 flex items-center gap-2 text-[13px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2">
            <Icon name="warn" className="w-4 h-4 shrink-0" /> {err}
          </div>
        )}

        {loading ? (
          <div className="flex items-center gap-2 text-[13px] text-muted-foreground">
            <Icon name="refresh" className="w-4 h-4 animate-spin" /> Đang tải nhật ký…
          </div>
        ) : rows.length === 0 ? (
          <div className="rounded-lg border border-dashed border-border bg-card p-10 text-center">
            <span className="inline-grid place-items-center w-12 h-12 rounded-full bg-sync-soft border border-sync-border text-sync mb-3 mx-auto">
              <Icon name="clock" className="w-6 h-6" />
            </span>
            <div className="font-semibold text-foreground mb-1">Chưa có lần sync nào</div>
            <p className="text-[13px] text-muted-foreground max-w-sm mx-auto">
              Mỗi lần bấm <b>SYNC</b> ở Bàn đồng bộ sẽ ghi một bản nhật ký ở máy tool và hiện tại đây.
            </p>
          </div>
        ) : (
          <div className="rounded-lg border border-border bg-card overflow-hidden">
            <table className="w-full text-[13px]">
              <thead>
                <tr className="bg-sync text-white text-left">
                  <th className="font-semibold px-3 py-2">Khóa nguồn (CSDT)</th>
                  <th className="font-semibold px-3 py-2">Khóa đích (CDB)</th>
                  <th className="font-semibold px-3 py-2 w-40">Lúc sync</th>
                  <th className="font-semibold px-3 py-2 w-28">Cán bộ</th>
                  <th className="font-semibold px-3 py-2 w-20 text-center">Tạo</th>
                  <th className="font-semibold px-3 py-2 w-28"></th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr key={`${r.khoa_moi}-${r.sync_at}-${i}`} className="border-t border-border hover:bg-muted/40">
                    <td className="px-3 py-2">
                      {r.ten_khoa_cu && <div className="font-semibold">{r.ten_khoa_cu}</div>}
                      <div className={r.ten_khoa_cu ? "text-muted-foreground" : "font-semibold"} style={{ fontFamily: "ui-monospace,Consolas,monospace", fontSize: "12px" }}>{r.khoa_cu ?? "–"}</div>
                    </td>
                    <td className="px-3 py-2">
                      {r.ten_khoa_moi && <div className="font-semibold">{r.ten_khoa_moi}</div>}
                      <div className={r.ten_khoa_moi ? "text-muted-foreground" : "font-semibold"} style={{ fontFamily: "ui-monospace,Consolas,monospace", fontSize: "12px" }}>{r.khoa_moi}</div>
                    </td>
                    <td className="px-3 py-2 tabular-nums text-muted-foreground">{fmtLuc(r.sync_at)}</td>
                    <td className="px-3 py-2">{r.can_bo}</td>
                    <td className="px-3 py-2 text-center tabular-nums font-semibold">{r.so_tao}</td>
                    <td className="px-3 py-2 text-right">
                      <button
                        onClick={() => setHuyRow(r)}
                        className="inline-flex items-center gap-1 h-7 px-2.5 rounded-md border border-destructive/40 text-destructive text-[12px] font-medium hover:bg-destructive/10 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-destructive"
                      >
                        <Icon name="warn" className="w-3.5 h-3.5" /> Hủy sync
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Hộp thoại xác nhận hủy (dùng chung với Bàn đồng bộ) */}
      {huyRow && (
        <HuyncSyncDialog
          maKhoaMoi={huyRow.khoa_moi}
          nhan={huyRow.ten_khoa_moi || huyRow.khoa_moi}
          targetKey={targetKey}
          dichDbName={dichTarget?.database}
          onClose={() => setHuyRow(null)}
          onDone={(kq) => {
            const nhan = huyRow.ten_khoa_moi || huyRow.khoa_moi;
            setHuyRow(null);
            setToast(`Đã hủy sync khóa ${nhan}: xóa ${kq.hs_del} hồ sơ · ${kq.nlx_del} người lái`
              + (kq.tong_so_hv != null ? ` · TổngSoHV còn ${kq.tong_so_hv}` : ""));
            taiDS(targetKey);
          }}
        />
      )}
    </div>
  );
}
