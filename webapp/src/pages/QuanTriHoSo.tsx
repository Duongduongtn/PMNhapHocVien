import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Icon } from "../components/Icon";
import { ApiError, dsHoSoAdmin, xoaHoSoAdmin, type HoSoAdmin } from "../lib/api";

// HTG-03 — admin lọc & xóa thủ công hồ sơ PII trong hàng đợi VPS.
// Bám prototype ui-demo/src/pages/admin/HoSo.tsx: bảng + checkbox chọn nhiều + lọc
// trạng thái/khoảng ngày + dialog xác nhận xóa. Xóa là hard-delete, không khôi phục (BR-016).
// Chỉ admin (RequireAdmin + server require_role("admin")).

const LOC_TT = [
  { v: "", nhan: "Tất cả" },
  { v: "pending", nhan: "Chờ nạp" },
  { v: "importing", nhan: "Đang nạp" },
  { v: "imported", nhan: "Đã nạp" },
] as const;

const NGAY_VN = new Intl.DateTimeFormat("vi-VN", {
  day: "2-digit", month: "2-digit", year: "numeric", timeZone: "Asia/Ho_Chi_Minh",
});
const NGAY_GIO_VN = new Intl.DateTimeFormat("vi-VN", {
  day: "2-digit", month: "2-digit", year: "numeric",
  hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "Asia/Ho_Chi_Minh",
});

function ngayVN(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? "—" : NGAY_VN.format(d);
}
function ngayGioVN(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? "—" : NGAY_GIO_VN.format(d);
}

function ChipTrangThai({ tt }: { tt: string }) {
  if (tt === "imported")
    return <span className="inline-flex items-center gap-1 text-[11px] font-medium text-success bg-success/10 border border-success/30 rounded-full px-2 py-0.5 whitespace-nowrap"><Icon name="check" className="w-3 h-3" sw={3} /> Đã nạp</span>;
  if (tt === "importing")
    return <span className="inline-flex items-center gap-1 text-[11px] font-medium text-primary bg-primary/10 border border-primary/30 rounded-full px-2 py-0.5 whitespace-nowrap"><Icon name="refresh" className="w-3 h-3" /> Đang nạp</span>;
  return <span className="inline-flex items-center gap-1 text-[11px] font-medium text-warning bg-warning/10 border border-warning/30 rounded-full px-2 py-0.5 whitespace-nowrap"><Icon name="clock" className="w-3 h-3" /> Chờ nạp</span>;
}

export default function QuanTriHoSo() {
  const nav = useNavigate();
  const [rows, setRows] = useState<HoSoAdmin[]>([]);
  const [total, setTotal] = useState(0);
  const [loc, setLoc] = useState<string>("");
  const [tuNgay, setTuNgay] = useState("");
  const [denNgay, setDenNgay] = useState("");
  const [coTrang, setCoTrang] = useState(100);
  const [trang, setTrang] = useState(0); // 0-based
  const [chon, setChon] = useState<Set<string>>(new Set());
  const [dang, setDang] = useState(false);
  const [loi, setLoi] = useState("");
  const [okMsg, setOkMsg] = useState("");
  const [xacNhan, setXacNhan] = useState(false);
  const [dangXoa, setDangXoa] = useState(false);

  const tai = useCallback(async () => {
    setDang(true);
    setLoi("");
    try {
      const kq = await dsHoSoAdmin({
        trang_thai: loc || undefined,
        tu_ngay: tuNgay || undefined,
        den_ngay: denNgay || undefined,
        limit: coTrang,
        offset: trang * coTrang,
      });
      setRows(kq.items);
      setTotal(kq.total);
      setChon(new Set());
    } catch (err) {
      setLoi(err instanceof ApiError ? err.message : "Không tải được danh sách.");
    } finally {
      setDang(false);
    }
  }, [loc, tuNgay, denNgay, coTrang, trang]);

  useEffect(() => {
    void tai();
  }, [tai]);

  function bao(msg: string) {
    setOkMsg(msg);
    setTimeout(() => setOkMsg(""), 2500);
  }

  function toggle(uuid: string) {
    setChon((cu) => {
      const s = new Set(cu);
      if (s.has(uuid)) s.delete(uuid);
      else s.add(uuid);
      return s;
    });
  }
  function toggleAll() {
    setChon((cu) => (cu.size === rows.length ? new Set() : new Set(rows.map((h) => h.uuid))));
  }

  async function xoaDaChon() {
    setDangXoa(true);
    setLoi("");
    let loiCt = 0;
    for (const uuid of chon) {
      try {
        await xoaHoSoAdmin(uuid);
      } catch {
        loiCt += 1;
      }
    }
    setDangXoa(false);
    setXacNhan(false);
    if (loiCt > 0) setLoi(`Có ${loiCt} hồ sơ không xóa được, hãy thử lại.`);
    else bao(`Đã xóa ${chon.size} hồ sơ.`);
    void tai();
  }

  const soTrang = Math.max(1, Math.ceil(total / coTrang));
  const tu = total === 0 ? 0 : trang * coTrang + 1;
  const den = Math.min(total, (trang + 1) * coTrang);

  return (
    <div className="p-4 lg:p-6 max-w-6xl space-y-4">
      <div className="flex items-center gap-2 flex-wrap">
        <button onClick={() => nav("/tai-khoan")} className="inline-flex items-center gap-1 text-[13px] text-primary font-medium hover:underline">
          <Icon name="chevronLeft" className="w-4 h-4" /> Tài khoản
        </button>
        <h1 className="text-lg font-bold flex-1">Lọc &amp; xóa dữ liệu căn cước</h1>
      </div>

      <p className="text-[13px] text-muted-foreground">
        Hồ sơ căn cước lưu tạm trên máy chủ, hệ thống tự xóa sau <b className="text-foreground">30 ngày</b>.
        Xóa thủ công <b className="text-destructive">không khôi phục được</b> (cả hồ sơ lẫn ảnh gốc).
      </p>

      {okMsg && (
        <div className="flex items-center gap-2 text-[13px] text-success bg-success/10 border border-success/30 rounded-lg px-3 py-2">
          <Icon name="check" className="w-4 h-4 shrink-0" sw={3} /> {okMsg}
        </div>
      )}
      {loi && (
        <div className="flex items-center gap-2 text-[13px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2">
          <Icon name="warn" className="w-4 h-4 shrink-0" /> {loi}
        </div>
      )}

      {/* Thanh lọc + hành động */}
      <div className="bg-card border border-border rounded-xl p-3 flex items-center gap-3 flex-wrap">
        <div className="inline-flex rounded-lg bg-muted p-1">
          {LOC_TT.map((o) => (
            <button
              key={o.v}
              onClick={() => { setLoc(o.v); setTrang(0); }}
              className={"px-3.5 py-1.5 text-[13px] rounded-md transition-colors " + (loc === o.v ? "bg-primary text-primary-foreground font-semibold" : "text-muted-foreground font-medium hover:text-foreground")}
            >
              {o.nhan}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2 flex-wrap text-[13px]">
          <label className="field-label whitespace-nowrap">Từ ngày</label>
          <input type="date" className="field-input" style={{ width: 150 }} value={tuNgay} onChange={(e) => { setTuNgay(e.target.value); setTrang(0); }} />
          <label className="field-label whitespace-nowrap">Đến</label>
          <input type="date" className="field-input" style={{ width: 150 }} value={denNgay} onChange={(e) => { setDenNgay(e.target.value); setTrang(0); }} />
          {(tuNgay || denNgay) && (
            <button onClick={() => { setTuNgay(""); setDenNgay(""); setTrang(0); }} className="text-[12px] text-muted-foreground hover:text-foreground underline">Bỏ lọc ngày</button>
          )}
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
              <th className="px-3 py-2.5 w-10">
                <input type="checkbox" className="accent-primary" checked={chon.size === rows.length && rows.length > 0} onChange={toggleAll} aria-label="Chọn tất cả" />
              </th>
              <th className="px-3 py-2.5 font-semibold">Họ và tên</th>
              <th className="px-3 py-2.5 font-semibold">Số CCCD</th>
              <th className="px-3 py-2.5 font-semibold">Nơi thường trú</th>
              <th className="px-3 py-2.5 font-semibold">Ngày gửi</th>
              <th className="px-3 py-2.5 font-semibold text-center">Trạng thái</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((h) => (
              <tr key={h.uuid} className={"border-t border-border transition-colors " + (chon.has(h.uuid) ? "bg-accent/50" : "hover:bg-accent/30")}>
                <td className="px-3 py-2"><input type="checkbox" className="accent-primary" checked={chon.has(h.uuid)} onChange={() => toggle(h.uuid)} aria-label={`Chọn ${h.ho_ten ?? ""}`} /></td>
                <td className="px-3 py-2 font-semibold">
                  <span className="inline-flex items-center gap-1.5">
                    {h.co_anh && <Icon name="image" className="w-3.5 h-3.5 text-muted-foreground shrink-0" />}
                    {h.ho_ten || "—"}
                  </span>
                </td>
                <td className="px-3 py-2 tabular-nums">{h.so_cccd || "—"}</td>
                <td className="px-3 py-2 max-w-[200px] truncate" title={h.noi_tt_raw ?? undefined}>{h.noi_tt_raw || "—"}</td>
                <td className="px-3 py-2 tabular-nums" title={ngayGioVN(h.created_at)}>{ngayVN(h.created_at)}</td>
                <td className="px-3 py-2 text-center"><ChipTrangThai tt={h.trang_thai} /></td>
              </tr>
            ))}
          </tbody>
        </table>
        {dang && <div className="px-4 py-6 text-center text-sm text-muted-foreground"><Icon name="refresh" className="w-4 h-4 animate-spin inline mr-1" /> Đang tải…</div>}
        {!dang && !rows.length && <div className="px-4 py-6 text-center text-sm text-muted-foreground">Không có hồ sơ nào khớp bộ lọc.</div>}
      </div>

      {/* Phân trang */}
      <div className="flex items-center justify-between gap-2 flex-wrap text-[13px]">
        <span className="text-muted-foreground tabular-nums">{tu}–{den} / {total} · đã chọn {chon.size}</span>
        <div className="flex items-center gap-2">
          <button onClick={() => setTrang((t) => Math.max(0, t - 1))} disabled={trang === 0}
            className="h-8 w-8 rounded-md border border-border inline-flex items-center justify-center hover:bg-muted transition-colors disabled:opacity-40">
            <Icon name="chevronLeft" className="w-4 h-4" />
          </button>
          <span className="tabular-nums">Trang {trang + 1}/{soTrang}</span>
          <button onClick={() => setTrang((t) => (t + 1 < soTrang ? t + 1 : t))} disabled={trang + 1 >= soTrang}
            className="h-8 w-8 rounded-md border border-border inline-flex items-center justify-center hover:bg-muted transition-colors disabled:opacity-40">
            <Icon name="chevronRight" className="w-4 h-4" />
          </button>
          <select value={coTrang} onChange={(e) => { setCoTrang(Number(e.target.value)); setTrang(0); }}
            className="h-8 rounded-md border border-border bg-card px-2 text-[13px]">
            {[50, 100, 200].map((n) => <option key={n} value={n}>{n}/trang</option>)}
          </select>
        </div>
      </div>

      {/* Dialog xác nhận xóa */}
      {xacNhan && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4" onClick={(e) => { if (e.target === e.currentTarget && !dangXoa) setXacNhan(false); }}>
          <div className="bg-card rounded-xl shadow-2xl w-full max-w-sm p-5">
            <div className="flex items-start gap-3">
              <span className="w-11 h-11 rounded-full bg-destructive/10 text-destructive flex items-center justify-center shrink-0"><Icon name="warn" className="w-6 h-6" /></span>
              <div>
                <h3 className="font-bold text-sm">Xóa {chon.size} hồ sơ?</h3>
                <p className="text-[13px] text-muted-foreground mt-1">Xóa cả bản ghi và ảnh gốc trên máy chủ. Thao tác <b className="text-destructive">không khôi phục được</b>.</p>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-5">
              <button onClick={() => setXacNhan(false)} disabled={dangXoa} className="h-10 px-4 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors disabled:opacity-60">Hủy</button>
              <button onClick={() => void xoaDaChon()} disabled={dangXoa} className="h-10 px-5 rounded-lg bg-destructive text-white text-sm font-semibold hover:brightness-110 transition-all disabled:opacity-60">
                {dangXoa ? "Đang xóa…" : "Xóa"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
