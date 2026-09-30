import { useState } from "react";
import { Link } from "react-router-dom";
import { Icon } from "../../components/Icon";
import { hoSoDaGui, type HoSoDaGui } from "../../lib/mock-data";

function StatusChip({ tt }: { tt: HoSoDaGui["trangThai"] }) {
  return tt === "imported" ? (
    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-success bg-success/10 border border-success/30 rounded-full px-2 py-0.5 whitespace-nowrap"><Icon name="check" className="w-3 h-3" sw={3} /> Đã nạp</span>
  ) : (
    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-warning bg-warning/10 border border-warning/30 rounded-full px-2 py-0.5 whitespace-nowrap"><Icon name="clock" className="w-3 h-3" /> Chờ nạp</span>
  );
}

export default function AdminHoSo() {
  const [loc, setLoc] = useState<"all" | "pending" | "imported">("all");
  const [chon, setChon] = useState<Set<string>>(new Set());
  const [xacNhan, setXacNhan] = useState(false);
  const ds = hoSoDaGui.filter((h) => loc === "all" || h.trangThai === loc);

  const toggle = (id: string) => {
    const s = new Set(chon);
    s.has(id) ? s.delete(id) : s.add(id);
    setChon(s);
  };
  const toggleAll = () => setChon(chon.size === ds.length ? new Set() : new Set(ds.map((h) => h.cccd)));

  return (
    <div className="min-h-screen bg-[hsl(210_40%_96%)]">
      {/* Header quản trị */}
      <div className="bg-primary text-primary-foreground px-4 py-3 flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2 text-sm font-semibold">
          <Icon name="db" className="w-4 h-4" /> Quản trị PII — Backend VPS
          <span className="text-[11px] font-semibold bg-white/15 rounded-full px-2 py-0.5">HTG-03</span>
        </div>
        <div className="flex items-center gap-3 text-[12px]">
          <span className="text-white/80">Quản trị: Nguyễn Văn An</span>
          <Link to="/" aria-label="Về trang chọn app" className="text-white/80 hover:text-white transition-colors"><Icon name="logout" className="w-4 h-4" /></Link>
        </div>
      </div>

      <div className="max-w-6xl mx-auto p-4 sm:p-6">
        <p className="text-[13px] text-muted-foreground mb-4">Lọc và xóa thủ công hồ sơ căn cước lưu tạm trên VPS. Hệ thống tự xóa sau <b className="text-foreground">30 ngày</b> (BR-016); xóa thủ công <b className="text-destructive">không khôi phục được</b>.</p>

        {/* Thanh lọc + hành động */}
        <div className="bg-card border border-border rounded-xl p-3 mb-4 flex items-center gap-3 flex-wrap">
          <div className="inline-flex rounded-lg bg-muted p-1">
            {([["all", "Tất cả"], ["pending", "Chờ nạp"], ["imported", "Đã nạp"]] as const).map(([k, label]) => (
              <button key={k} onClick={() => { setLoc(k); setChon(new Set()); }}
                className={"px-3.5 py-1.5 text-[13px] rounded-md transition-colors " + (loc === k ? "bg-primary text-primary-foreground font-semibold" : "text-muted-foreground font-medium hover:text-foreground")}>
                {label}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <label className="field-label whitespace-nowrap">Từ ngày</label>
            <input type="text" className="field-input" style={{ width: 120 }} placeholder="dd/mm/yyyy" defaultValue="01/09/2026" />
            <label className="field-label whitespace-nowrap">Đến</label>
            <input type="text" className="field-input" style={{ width: 120 }} placeholder="dd/mm/yyyy" defaultValue="30/09/2026" />
          </div>
          <button
            disabled={chon.size === 0}
            onClick={() => setXacNhan(true)}
            className="ml-auto inline-flex items-center gap-2 h-9 px-4 rounded-lg bg-destructive text-white font-semibold text-sm hover:brightness-110 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Icon name="warn" className="w-4 h-4" /> Xóa thủ công{chon.size > 0 ? ` (${chon.size})` : ""}
          </button>
        </div>

        {/* Bảng */}
        <div className="bg-card border border-border rounded-xl overflow-x-auto">
          <table className="w-full text-[13px] whitespace-nowrap">
            <thead>
              <tr className="bg-muted text-muted-foreground text-left">
                <th className="px-4 py-2.5 w-10"><input type="checkbox" className="accent-primary" checked={chon.size === ds.length && ds.length > 0} onChange={toggleAll} /></th>
                <th className="px-4 py-2.5 font-semibold">Họ và tên</th>
                <th className="px-4 py-2.5 font-semibold">Số CCCD</th>
                <th className="px-4 py-2.5 font-semibold">Nơi thường trú</th>
                <th className="px-4 py-2.5 font-semibold">Ngày gửi</th>
                <th className="px-4 py-2.5 font-semibold text-center">Trạng thái</th>
              </tr>
            </thead>
            <tbody>
              {ds.map((h) => (
                <tr key={h.cccd} className={"border-t border-border transition-colors " + (chon.has(h.cccd) ? "bg-accent/50" : "hover:bg-accent/30")}>
                  <td className="px-4 py-2"><input type="checkbox" className="accent-primary" checked={chon.has(h.cccd)} onChange={() => toggle(h.cccd)} /></td>
                  <td className="px-4 py-2 font-semibold">{h.hoTen}</td>
                  <td className="px-4 py-2 tabular-nums">{h.cccd}</td>
                  <td className="px-4 py-2">{h.noiTT}</td>
                  <td className="px-4 py-2 tabular-nums">{h.ngayGui}</td>
                  <td className="px-4 py-2 text-center"><StatusChip tt={h.trangThai} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-[12px] text-muted-foreground mt-2">Tổng <b className="text-foreground">{ds.length}</b> hồ sơ · đã chọn <b className="text-foreground">{chon.size}</b></p>
      </div>

      {/* Dialog xác nhận xóa */}
      {xacNhan && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4" onClick={(e) => { if (e.target === e.currentTarget) setXacNhan(false); }}>
          <div className="bg-card rounded-xl shadow-2xl w-full max-w-sm p-5">
            <div className="flex items-start gap-3">
              <span className="w-11 h-11 rounded-full bg-destructive/10 text-destructive flex items-center justify-center shrink-0"><Icon name="warn" className="w-6 h-6" /></span>
              <div>
                <h3 className="font-bold text-sm">Xóa {chon.size} hồ sơ?</h3>
                <p className="text-[13px] text-muted-foreground mt-1">Xóa cả bản ghi và ảnh thô trên VPS. Thao tác <b className="text-destructive">không khôi phục được</b>.</p>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-5">
              <button onClick={() => setXacNhan(false)} className="h-10 px-4 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors">Hủy</button>
              <button onClick={() => { setChon(new Set()); setXacNhan(false); }} className="h-10 px-5 rounded-lg bg-destructive text-white text-sm font-semibold hover:brightness-110 transition-all">Xóa</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
