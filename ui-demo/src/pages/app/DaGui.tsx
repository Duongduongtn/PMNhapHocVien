import { useState } from "react";
import { Icon } from "../../components/Icon";
import { hoSoDaGui, type HoSoDaGui } from "../../lib/mock-data";

function StatusChip({ tt }: { tt: HoSoDaGui["trangThai"] }) {
  return tt === "imported" ? (
    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-success bg-success/10 border border-success/30 rounded-full px-2 py-0.5 whitespace-nowrap">
      <Icon name="check" className="w-3 h-3" sw={3} /> Đã nạp
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-warning bg-warning/10 border border-warning/30 rounded-full px-2 py-0.5 whitespace-nowrap">
      <Icon name="clock" className="w-3 h-3" /> Chờ nạp
    </span>
  );
}

function AnhTho({ mau, size = "w-11 h-11" }: { mau: string; size?: string }) {
  return (
    <span className={`inline-flex ${size} rounded-lg items-center justify-center shrink-0 ${mau}`}>
      <Icon name="user" className="w-6 h-6 text-white/90" />
    </span>
  );
}

export default function DaGui() {
  const [loc, setLoc] = useState<"all" | "pending" | "imported">("all");
  const [sel, setSel] = useState<HoSoDaGui | null>(null);
  const ds = hoSoDaGui.filter((h) => loc === "all" || h.trangThai === loc);
  const dem = (t: "pending" | "imported") => hoSoDaGui.filter((h) => h.trangThai === t).length;

  return (
    <div className="lg:p-6 lg:max-w-5xl lg:mx-auto">
      <div className="p-4 lg:p-0 lg:mb-4">
        <div className="flex items-center gap-2 mb-1">
          <h2 className="text-base font-bold">Hồ sơ tôi đã gửi</h2>
          <span className="text-[11px] font-semibold text-primary bg-primary/10 rounded-full px-2 py-0.5">THU-02</span>
        </div>
        <p className="text-[12px] text-muted-foreground">Danh sách học viên bạn đã quét/gửi lên VPS. Bấm để xem ảnh &amp; thông tin.</p>

        {/* Bộ lọc */}
        <div className="inline-flex rounded-lg bg-muted p-1 mt-3">
          {([["all", `Tất cả (${hoSoDaGui.length})`], ["pending", `Chờ nạp (${dem("pending")})`], ["imported", `Đã nạp (${dem("imported")})`]] as const).map(([k, label]) => (
            <button key={k} onClick={() => setLoc(k)}
              className={"px-3.5 py-1.5 text-[13px] rounded-md transition-colors " + (loc === k ? "bg-card shadow-sm text-primary font-semibold" : "text-muted-foreground font-medium hover:text-foreground")}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* MOBILE: card list */}
      <div className="lg:hidden divide-y divide-border border-t border-border">
        {ds.map((h) => (
          <button key={h.cccd} onClick={() => setSel(h)} className="w-full text-left flex items-center gap-3 px-4 py-3 hover:bg-accent/40 transition-colors">
            <AnhTho mau={h.mau} />
            <div className="min-w-0 flex-1">
              <div className="font-semibold text-[14px] truncate">{h.hoTen}</div>
              <div className="text-[12px] text-muted-foreground truncate">{h.gioiTinh} · {h.cccd}</div>
              <div className="text-[11px] text-muted-foreground truncate">Gửi {h.ngayGui}</div>
            </div>
            <StatusChip tt={h.trangThai} />
          </button>
        ))}
        {!ds.length && <div className="px-4 py-10 text-center text-sm text-muted-foreground">Chưa có hồ sơ nào ở nhóm này.</div>}
      </div>

      {/* DESKTOP: table */}
      <div className="hidden lg:block bg-card border border-border rounded-xl overflow-hidden">
        <table className="w-full text-[13px]">
          <thead>
            <tr className="bg-muted text-muted-foreground text-left">
              <th className="px-4 py-2.5 font-semibold w-12">Ảnh</th>
              <th className="px-4 py-2.5 font-semibold">Họ và tên</th>
              <th className="px-4 py-2.5 font-semibold">Giới tính</th>
              <th className="px-4 py-2.5 font-semibold">Số CCCD</th>
              <th className="px-4 py-2.5 font-semibold">Ngày sinh</th>
              <th className="px-4 py-2.5 font-semibold">Nơi thường trú</th>
              <th className="px-4 py-2.5 font-semibold">Ngày gửi</th>
              <th className="px-4 py-2.5 font-semibold text-center">Trạng thái</th>
            </tr>
          </thead>
          <tbody>
            {ds.map((h) => (
              <tr key={h.cccd} onClick={() => setSel(h)} className="border-t border-border cursor-pointer hover:bg-accent/40 transition-colors">
                <td className="px-4 py-2"><AnhTho mau={h.mau} size="w-8 h-8" /></td>
                <td className="px-4 py-2 font-semibold">{h.hoTen}</td>
                <td className="px-4 py-2">{h.gioiTinh}</td>
                <td className="px-4 py-2 tabular-nums">{h.cccd}</td>
                <td className="px-4 py-2 tabular-nums">{h.ngaySinh}</td>
                <td className="px-4 py-2">{h.noiTT}</td>
                <td className="px-4 py-2 tabular-nums">{h.ngayGui}</td>
                <td className="px-4 py-2 text-center"><StatusChip tt={h.trangThai} /></td>
              </tr>
            ))}
          </tbody>
        </table>
        {!ds.length && <div className="px-4 py-10 text-center text-sm text-muted-foreground">Chưa có hồ sơ nào ở nhóm này.</div>}
      </div>

      {/* CHI TIẾT (modal): ảnh + thông tin */}
      {sel && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-end sm:items-center justify-center p-0 sm:p-4" onClick={(e) => { if (e.target === e.currentTarget) setSel(null); }}>
          <div className="bg-card w-full sm:max-w-md rounded-t-2xl sm:rounded-xl shadow-2xl max-h-[92vh] flex flex-col overflow-hidden">
            <div className="flex items-center justify-between px-5 py-3 border-b border-border shrink-0">
              <h3 className="font-bold text-sm">Chi tiết hồ sơ đã gửi</h3>
              <button onClick={() => setSel(null)} aria-label="Đóng" className="w-8 h-8 rounded-lg hover:bg-muted flex items-center justify-center transition-colors"><Icon name="x" className="w-5 h-5" /></button>
            </div>
            <div className="p-5 overflow-y-auto">
              <div className="flex items-start gap-4">
                <div className="w-24 aspect-[3/4] rounded-lg bg-slate-100 border border-border flex items-center justify-center shrink-0 relative">
                  <Icon name="user" className="w-12 h-12 text-slate-300" sw={1.5} />
                  <span className="absolute bottom-1 left-1/2 -translate-x-1/2 text-[9px] bg-foreground/70 text-white px-1.5 py-0.5 rounded whitespace-nowrap">Ảnh thô</span>
                </div>
                <div className="min-w-0 flex-1">
                  <div className="font-bold text-[15px]">{sel.hoTen}</div>
                  <div className="mt-1"><StatusChip tt={sel.trangThai} /></div>
                  <div className="text-[12px] text-muted-foreground mt-2">Gửi lúc {sel.ngayGui}</div>
                </div>
              </div>
              <div className="mt-4 space-y-2.5">
                {[["Số CCCD", sel.cccd], ["Giới tính", sel.gioiTinh], ["Ngày sinh", sel.ngaySinh], ["Nơi thường trú", sel.noiTT]].map(([k, v]) => (
                  <div key={k} className="flex justify-between gap-3 text-[13px] border-b border-border pb-2 last:border-0">
                    <span className="text-muted-foreground shrink-0">{k}</span>
                    <span className="font-medium text-right">{v}</span>
                  </div>
                ))}
              </div>
              <p className="text-[11px] text-muted-foreground mt-3">Ảnh thô do nhân viên tuyển sinh chụp; căn khung 3:4 + xóa phông + xuất .jp2 sẽ do tool nạp thực hiện (NAP-04).</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
