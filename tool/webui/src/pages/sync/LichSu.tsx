import { useEffect, useState } from "react";
import { Icon } from "../../components/Icon";
import {
  getSyncLichSu, getSyncRollbackPreview, postSyncRollback, getSyncTargets,
  type SyncLichSuRow, type SyncRollbackPreview, type SyncTarget,
} from "../../lib/api";

// ISO (yyyy-mm-ddTHH:MM:SS) → dd/mm/yyyy HH:mm
const fmtLuc = (s: string) => {
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(s);
  return m ? `${m[3]}/${m[2]}/${m[1]} ${m[4]}:${m[5]}` : s;
};

interface HuyState {
  row: SyncLichSuRow;
  preview: SyncRollbackPreview | null;
  dangXem: boolean;   // đang tải preview
  dangXoa: boolean;   // đang thực hiện hủy
  loi: string;
}

export default function LichSu() {
  const [rows, setRows] = useState<SyncLichSuRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [targets, setTargets] = useState<SyncTarget[]>([]);
  const [targetKey, setTargetKey] = useState("");
  const [huy, setHuy] = useState<HuyState | null>(null);
  const [toast, setToast] = useState("");

  const dichTarget = targets.find((t) => t.key === targetKey);

  const taiDS = () => {
    setLoading(true);
    getSyncLichSu()
      .then(setRows)
      .catch(() => setErr("Không đọc được nhật ký sync (tool backend chưa chạy?)"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    taiDS();
    getSyncTargets()
      .then((d) => { setTargets(d.targets); setTargetKey(d.selected); })
      .catch(() => {});
  }, []);

  const moHuy = (row: SyncLichSuRow) => {
    setHuy({ row, preview: null, dangXem: true, dangXoa: false, loi: "" });
    getSyncRollbackPreview(row.khoa_moi, targetKey)
      .then((p) => setHuy((h) => (h && h.row === row ? { ...h, preview: p, dangXem: false } : h)))
      .catch((e) => setHuy((h) => (h && h.row === row
        ? { ...h, dangXem: false, loi: e instanceof Error ? e.message : "Không đếm được số bản ghi." }
        : h)));
  };

  const xacNhanHuy = async () => {
    if (!huy) return;
    setHuy({ ...huy, dangXoa: true, loi: "" });
    try {
      const kq = await postSyncRollback(huy.row.khoa_moi, targetKey);
      setHuy(null);
      setToast(`Đã hủy sync khóa ${huy.row.khoa_moi}: xóa ${kq.hs_del} hồ sơ · ${kq.nlx_del} người lái`
        + (kq.tong_so_hv != null ? ` · TổngSoHV còn ${kq.tong_so_hv}` : ""));
      taiDS();
    } catch (e) {
      setHuy((h) => (h ? { ...h, dangXoa: false, loi: e instanceof Error ? e.message : "Hủy sync thất bại." } : h));
    }
  };

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
                  <th className="font-semibold px-3 py-2">Khóa đích</th>
                  <th className="font-semibold px-3 py-2 w-40">Lúc sync</th>
                  <th className="font-semibold px-3 py-2 w-28">Cán bộ</th>
                  <th className="font-semibold px-3 py-2 w-20 text-center">Tạo</th>
                  <th className="font-semibold px-3 py-2">Khóa nguồn</th>
                  <th className="font-semibold px-3 py-2 w-28"></th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr key={`${r.khoa_moi}-${r.sync_at}-${i}`} className="border-t border-border hover:bg-muted/40">
                    <td className="px-3 py-2 font-semibold" style={{ fontFamily: "ui-monospace,Consolas,monospace", fontSize: "12.5px" }}>{r.khoa_moi}</td>
                    <td className="px-3 py-2 tabular-nums text-muted-foreground">{fmtLuc(r.sync_at)}</td>
                    <td className="px-3 py-2">{r.can_bo}</td>
                    <td className="px-3 py-2 text-center tabular-nums font-semibold">{r.so_tao}</td>
                    <td className="px-3 py-2 text-muted-foreground" style={{ fontFamily: "ui-monospace,Consolas,monospace", fontSize: "12.5px" }}>{r.khoa_cu ?? "–"}</td>
                    <td className="px-3 py-2 text-right">
                      <button
                        onClick={() => moHuy(r)}
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

      {/* Modal xác nhận hủy */}
      {huy && (
        <div className="fixed inset-0 z-50 grid place-items-center">
          <div className="absolute inset-0 bg-foreground/30" onClick={() => !huy.dangXoa && setHuy(null)} />
          <div role="dialog" aria-modal="true" className="relative bg-card rounded-xl border border-border shadow-xl w-[480px] max-w-[94vw] p-5">
            <h3 className="font-bold text-[15px] mb-2 flex items-center gap-2 text-destructive">
              <Icon name="warn" className="w-5 h-5 shrink-0" />
              Hủy sync khóa {huy.row.khoa_moi}?
            </h3>

            {huy.dangXem ? (
              <div className="flex items-center gap-2 text-[13px] text-muted-foreground py-3">
                <Icon name="refresh" className="w-4 h-4 animate-spin" /> Đang đếm số bản ghi sẽ xóa…
              </div>
            ) : huy.preview ? (
              <>
                <ul className="text-[13px] text-foreground space-y-1 mb-3 list-disc pl-5">
                  <li>Nhóm nhật ký máy tool còn ở đích: <b className="tabular-nums">{huy.preview.log_con_dich}</b> học viên{huy.preview.log_count > huy.preview.log_con_dich && <span className="text-muted-foreground"> (nhật ký {huy.preview.log_count}, số còn lại đã bị xóa trước đó)</span>}</li>
                  <li>Nhóm công cụ cũ (NguoiTao=SYNC): <b className="tabular-nums">{huy.preview.sync_group}</b> học viên</li>
                </ul>
                <p className="text-[12.5px] text-muted-foreground mb-4">
                  Xóa Người lái + Hồ sơ + Giấy tờ của <b className="text-destructive tabular-nums">{huy.preview.tong}</b> học viên khỏi
                  CSDL đích <b>{dichTarget?.database}</b>. Nhật ký máy tool vẫn giữ lại. <b>Không hoàn tác được.</b>
                </p>
              </>
            ) : null}

            {huy.loi && (
              <div className="mb-3 flex items-start gap-2 text-[12.5px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2">
                <Icon name="warn" className="w-4 h-4 shrink-0 mt-0.5" /> {huy.loi}
              </div>
            )}

            <div className="flex justify-end gap-2">
              <button
                onClick={() => setHuy(null)}
                disabled={huy.dangXoa}
                className="h-9 px-4 rounded-lg border border-border text-[13px] hover:bg-muted disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                Đóng
              </button>
              <button
                onClick={xacNhanHuy}
                disabled={huy.dangXem || huy.dangXoa || !huy.preview || huy.preview.tong === 0}
                title={huy.preview && huy.preview.tong === 0 ? "Khóa này không còn học viên nào do tool tạo" : undefined}
                className="inline-flex items-center gap-1.5 h-9 px-4 rounded-lg bg-destructive text-white font-semibold text-[13px] hover:brightness-110 transition-all disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-destructive"
              >
                <Icon name={huy.dangXoa ? "refresh" : "warn"} className={"w-4 h-4 " + (huy.dangXoa ? "animate-spin" : "")} />
                {huy.dangXoa ? "Đang hủy…" : huy.preview ? `Xóa ${huy.preview.tong} hồ sơ` : "Xóa"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
