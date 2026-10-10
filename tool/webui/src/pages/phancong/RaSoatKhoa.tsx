import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Icon } from "../../components/Icon";
import { ymdToVN } from "../../lib/format";
import { getSyncTargets, raSoatPC, type RaSoatKhoaPC } from "../../lib/api";

// PCG-05 — tab "Rà soát khóa": mọi khóa của CSĐT, khóa nào làm dở / lệch giữa danh sách và phân công.
// Chỉ đọc. Bấm một dòng → mở khóa đó ở "Phân công theo khóa" (?khoa=<mã>).

function So({ n, xau }: { n: number; xau?: boolean }) {
  if (!n) return <span className="text-muted-foreground">0</span>;
  return (
    <span className={"px-1.5 rounded text-[12px] font-semibold " + (xau ? "bg-destructive/10 text-destructive" : "bg-warning/10 text-warning")}>{n}</span>
  );
}

export default function RaSoatKhoa() {
  const nav = useNavigate();
  const [ds, setDs] = useState<RaSoatKhoaPC[] | null>(null);
  const [loi, setLoi] = useState<string | null>(null);

  useEffect(() => {
    let huy = false;
    getSyncTargets()
      .then((d) => {
        const t = d.targets.find((x) => x.key === d.selected) ?? d.targets[0];
        if (!t) throw new Error("Chưa cấu hình CSDL đích. Mở Cấu hình để khai báo.");
        return raSoatPC(t.key);
      })
      .then((r) => { if (!huy) setDs(r); })
      .catch((e: Error) => { if (!huy) setLoi(e.message); });
    return () => { huy = true; };
  }, []);

  const canXuLy = (ds ?? []).filter((k) => k.can_xu_ly).length;

  return (
    <div className="p-5">
      <div className="flex items-center gap-2 mb-3 flex-wrap">
        <h1 className="text-[15px] font-bold flex items-center gap-2">
          <Icon name="search" className="w-5 h-5 text-pc" /> Rà soát khóa
        </h1>
        <span className="text-[12.5px] text-muted-foreground">
          Phát hiện khóa làm dở / lệch giữa danh sách GV–xe và phân công. Bấm một dòng để mở khóa đó.
        </span>
        {ds && <span className="ml-auto text-[13px]"><b>{canXuLy}</b>/{ds.length} khóa cần xử lý</span>}
      </div>

      {loi && <div className="rounded-md border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">{loi}</div>}
      {!ds && !loi && (
        <div className="text-sm text-muted-foreground flex items-center gap-2">
          <Icon name="refresh" className="w-4 h-4 animate-spin" /> Đang rà soát…
        </div>
      )}
      {ds && ds.length >= 200 && (
        <div className="mb-2 text-[12.5px] text-muted-foreground">Chỉ hiện 200 khóa mới nhất của cơ sở.</div>
      )}
      {ds && ds.length === 0 && <div className="text-sm text-muted-foreground">Cơ sở chưa có khóa học nào.</div>}

      {ds && ds.length > 0 && (
        <div className="rounded-lg border border-border bg-card overflow-auto">
          <table className="w-full text-[13px]">
            <thead className="bg-pc text-white">
              <tr className="text-left">
                <th className="px-3 py-2">Khóa</th>
                <th className="px-2">Hạng</th>
                <th className="px-2">Khai giảng → bế giảng</th>
                <th className="px-2 text-center">GV trong DS</th>
                <th className="px-2 text-center">GV chưa phân công</th>
                <th className="px-2 text-center">Phân công ngoài DS</th>
                <th className="px-2 text-center">Xe trong DS</th>
                <th className="px-2 text-center">Xe chưa ghép</th>
                <th className="px-2 text-center">Ghép xe ngoài DS</th>
                <th className="px-2 text-center">Kết luận</th>
              </tr>
            </thead>
            <tbody>
              {ds.map((k) => (
                <tr
                  key={k.ma_kh}
                  tabIndex={0}
                  onClick={() => nav(`/phan-cong/theo-khoa?khoa=${encodeURIComponent(k.ma_kh)}`)}
                  onKeyDown={(e) => { if (e.key === "Enter") nav(`/phan-cong/theo-khoa?khoa=${encodeURIComponent(k.ma_kh)}`); }}
                  className="border-t border-border/60 cursor-pointer hover:bg-pc-soft focus-visible:outline-none focus-visible:bg-pc-soft"
                >
                  <td className="px-3 py-2 font-semibold">{k.ten_kh}</td>
                  <td className="px-2">{k.hang_dt || "—"}</td>
                  <td className="px-2 tabular-nums whitespace-nowrap">{ymdToVN(k.kg)} → {ymdToVN(k.bg)}</td>
                  <td className="px-2 text-center tabular-nums">{k.gv_ds}</td>
                  <td className="px-2 text-center"><So n={k.gv_chua_pc} /></td>
                  <td className="px-2 text-center"><So n={k.pc_ngoai_ds} xau /></td>
                  <td className="px-2 text-center tabular-nums">{k.xe_ds}</td>
                  <td className="px-2 text-center"><So n={k.xe_chua_ghep} /></td>
                  <td className="px-2 text-center"><So n={k.ghep_ngoai_ds} xau /></td>
                  <td className="px-2 text-center">
                    {k.can_xu_ly
                      ? <span className="px-2 py-0.5 rounded-full bg-warning/10 text-warning text-[12px] font-semibold">Cần xử lý</span>
                      : <span className="px-2 py-0.5 rounded-full bg-success/10 text-success text-[12px] font-semibold">Ổn</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
