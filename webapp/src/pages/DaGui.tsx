import { useEffect, useState } from "react";
import { Icon } from "../components/Icon";
import { ApiError, dsDaGui, type HoSoOut } from "../lib/api";
import { dsNhap } from "../lib/draft";
import { dangKyGuiLai, guiLaiTatCa } from "../lib/gui";
import { khopTim } from "../lib/text";

// THU-02 — Hồ sơ nhân viên đã gửi lên VPS (GET /api/ho-so/cua-toi) + nháp còn chờ gửi (offline).
// Bám bố cục ui-demo/src/pages/app/DaGui.tsx: lọc tab, mobile card / desktop table, modal chi tiết.

type Loc = "all" | "pending" | "imported";

// yyyymmdd → hiển thị. Năm-only (….0000) → "yyyy". Rỗng → "—".
function nsHienThi(s: string | null): string {
  if (!s) return "—";
  if (/^\d{4}0000$/.test(s)) return s.slice(0, 4);
  if (/^\d{8}$/.test(s)) return `${s.slice(6, 8)}/${s.slice(4, 6)}/${s.slice(0, 4)}`;
  return s;
}

function guiHienThi(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const p = (n: number) => String(n).padStart(2, "0");
  return `${p(d.getDate())}/${p(d.getMonth() + 1)}/${d.getFullYear()} ${p(d.getHours())}:${p(d.getMinutes())}`;
}

function gioiTinhHienThi(g: string | null): string {
  return g === "M" ? "Nam" : g === "F" ? "Nữ" : "—";
}

function TrangThaiChip({ tt }: { tt: string }) {
  if (tt === "imported")
    return (
      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-success bg-success/10 border border-success/30 rounded-full px-2 py-0.5 whitespace-nowrap">
        <Icon name="check" className="w-3 h-3" sw={3} /> Đã nạp
      </span>
    );
  if (tt === "importing")
    return (
      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-primary bg-primary/10 border border-primary/30 rounded-full px-2 py-0.5 whitespace-nowrap">
        <Icon name="refresh" className="w-3 h-3" /> Đang nạp
      </span>
    );
  return (
    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-warning bg-warning/10 border border-warning/30 rounded-full px-2 py-0.5 whitespace-nowrap">
      <Icon name="clock" className="w-3 h-3" /> Chờ nạp
    </span>
  );
}

export default function DaGui() {
  const [ds, setDs] = useState<HoSoOut[] | null>(null);
  const [loi, setLoi] = useState<string | null>(null);
  const [loc, setLoc] = useState<Loc>("all");
  const [sel, setSel] = useState<HoSoOut | null>(null);
  const [soNhap, setSoNhap] = useState(0);
  const [q, setQ] = useState("");
  const [moTim, setMoTim] = useState(false);

  async function tai() {
    setLoi(null);
    try {
      setDs(await dsDaGui());
    } catch (e) {
      setLoi(e instanceof ApiError ? e.message : "Không tải được danh sách. Kiểm tra mạng rồi thử lại.");
    }
  }

  useEffect(() => {
    dangKyGuiLai();
    // Vào màn này cũng là dịp thử gửi lại nháp còn tồn, rồi mới tải danh sách từ VPS.
    void guiLaiTatCa().then(() => {
      setSoNhap(dsNhap().length);
      void tai();
    });
    setSoNhap(dsNhap().length);
    void tai();
  }, []);

  const rows = (ds ?? []).filter((h) => (loc === "all" || h.trang_thai === loc) && khopTim(q, h.ho_ten, h.so_cccd));
  const dem = (t: string) => (ds ?? []).filter((h) => h.trang_thai === t).length;
  const rong = q.trim() ? "Không tìm thấy hồ sơ khớp." : "Chưa có hồ sơ nào ở nhóm này.";

  return (
    <div className="lg:p-6 lg:max-w-5xl lg:mx-auto">
      <div className="p-4 lg:p-0 lg:mb-4">
        <div className="flex items-start gap-2">
          <h2 className="text-base font-bold">Hồ sơ tôi đã gửi</h2>
          {/* Tìm kiếm — desktop hiện ô, mobile thu gọn nút kính lúp */}
          <div className="hidden lg:block ml-auto relative w-64 shrink-0">
            <Icon name="search" className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input className="field-input pl-9" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Tìm tên hoặc số CCCD" aria-label="Tìm hồ sơ" />
          </div>
          <button
            type="button"
            onClick={() => {
              setMoTim((v) => !v);
              if (moTim) setQ("");
            }}
            aria-label={moTim ? "Đóng tìm kiếm" : "Tìm kiếm"}
            className="lg:hidden ml-auto w-10 h-10 rounded-lg border border-border flex items-center justify-center shrink-0 text-muted-foreground hover:bg-muted transition-colors"
          >
            <Icon name={moTim ? "x" : "search"} className="w-5 h-5" />
          </button>
        </div>
        <p className="text-[12px] text-muted-foreground mt-0.5">Học viên bạn đã quét/gửi lên hệ thống. Bấm để xem chi tiết.</p>

        {/* Ô tìm bung ra ở mobile */}
        {moTim && (
          <div className="lg:hidden mt-2 relative">
            <Icon name="search" className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input autoFocus className="field-input pl-9" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Tìm tên (gõ không dấu cũng được) hoặc số CCCD" aria-label="Tìm hồ sơ" />
          </div>
        )}

        {soNhap > 0 && (
          <div className="mt-3 flex items-center gap-2 text-[12px] text-warning bg-warning/10 border border-warning/30 rounded-lg px-3 py-2">
            <Icon name="wifiOff" className="w-4 h-4 shrink-0" /> {soNhap} hồ sơ chưa gửi được (chờ mạng) — sẽ tự gửi lại khi có mạng.
          </div>
        )}

        {ds && (
          <div className="inline-flex rounded-lg bg-muted p-1 mt-3">
            {(
              [
                ["all", `Tất cả (${ds.length})`],
                ["pending", `Chờ nạp (${dem("pending")})`],
                ["imported", `Đã nạp (${dem("imported")})`],
              ] as const
            ).map(([k, label]) => (
              <button
                key={k}
                onClick={() => setLoc(k)}
                className={
                  "px-3.5 py-1.5 text-[13px] rounded-md transition-colors " +
                  (loc === k ? "bg-card shadow-sm text-primary font-semibold" : "text-muted-foreground font-medium hover:text-foreground")
                }
              >
                {label}
              </button>
            ))}
          </div>
        )}
      </div>

      {loi && (
        <div className="mx-4 lg:mx-0 flex items-center justify-between gap-2 text-[13px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2">
          <span className="flex items-center gap-2">
            <Icon name="warn" className="w-4 h-4 shrink-0" /> {loi}
          </span>
          <button onClick={() => void tai()} className="font-semibold hover:underline shrink-0">
            Thử lại
          </button>
        </div>
      )}

      {!ds && !loi && <div className="px-4 py-10 text-center text-sm text-muted-foreground">Đang tải…</div>}

      {ds && (
        <>
          {/* MOBILE: card list */}
          <div className="lg:hidden divide-y divide-border border-t border-border">
            {rows.map((h) => (
              <button
                key={h.uuid}
                onClick={() => setSel(h)}
                className="w-full text-left flex items-center gap-3 px-4 py-3 hover:bg-muted/60 transition-colors"
              >
                <span className="inline-flex w-11 h-11 rounded-lg items-center justify-center shrink-0 bg-slate-200 text-slate-500">
                  <Icon name="user" className="w-6 h-6" />
                </span>
                <div className="min-w-0 flex-1">
                  <div className="font-semibold text-[14px] truncate">{h.ho_ten || "(chưa có tên)"}</div>
                  <div className="text-[12px] text-muted-foreground truncate">
                    {gioiTinhHienThi(h.gioi_tinh)} · {h.so_cccd || "—"}
                  </div>
                  <div className="text-[11px] text-muted-foreground truncate">Gửi {guiHienThi(h.created_at)}</div>
                </div>
                <TrangThaiChip tt={h.trang_thai} />
              </button>
            ))}
            {!rows.length && <div className="px-4 py-10 text-center text-sm text-muted-foreground">{rong}</div>}
          </div>

          {/* DESKTOP: table */}
          <div className="hidden lg:block bg-card border border-border rounded-xl overflow-hidden">
            <table className="w-full text-[13px]">
              <thead>
                <tr className="bg-muted text-muted-foreground text-left">
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
                {rows.map((h) => (
                  <tr key={h.uuid} onClick={() => setSel(h)} className="border-t border-border cursor-pointer hover:bg-muted/60 transition-colors">
                    <td className="px-4 py-2 font-semibold">{h.ho_ten || "(chưa có tên)"}</td>
                    <td className="px-4 py-2">{gioiTinhHienThi(h.gioi_tinh)}</td>
                    <td className="px-4 py-2 tabular-nums">{h.so_cccd || "—"}</td>
                    <td className="px-4 py-2 tabular-nums">{nsHienThi(h.ngay_sinh)}</td>
                    <td className="px-4 py-2 max-w-[260px] truncate">{h.noi_tt_raw || "—"}</td>
                    <td className="px-4 py-2 tabular-nums">{guiHienThi(h.created_at)}</td>
                    <td className="px-4 py-2 text-center">
                      <TrangThaiChip tt={h.trang_thai} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!rows.length && <div className="px-4 py-10 text-center text-sm text-muted-foreground">{rong}</div>}
          </div>
        </>
      )}

      {/* CHI TIẾT (modal) */}
      {sel && (
        <div
          className="fixed inset-0 z-50 bg-black/60 flex items-end sm:items-center justify-center p-0 sm:p-4"
          onClick={(e) => {
            if (e.target === e.currentTarget) setSel(null);
          }}
        >
          <div className="bg-card w-full sm:max-w-md rounded-t-2xl sm:rounded-xl shadow-2xl max-h-[92vh] flex flex-col overflow-hidden">
            <div className="flex items-center justify-between px-5 py-3 border-b border-border shrink-0">
              <h3 className="font-bold text-sm">Chi tiết hồ sơ đã gửi</h3>
              <button onClick={() => setSel(null)} aria-label="Đóng" className="w-8 h-8 rounded-lg hover:bg-muted flex items-center justify-center transition-colors">
                <Icon name="x" className="w-5 h-5" />
              </button>
            </div>
            <div className="p-5 overflow-y-auto">
              <div className="flex items-start gap-4">
                <div className="w-20 aspect-[3/4] rounded-lg bg-slate-100 border border-border flex items-center justify-center shrink-0 text-slate-300">
                  <Icon name="user" className="w-10 h-10" sw={1.5} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="font-bold text-[15px]">{sel.ho_ten || "(chưa có tên)"}</div>
                  <div className="mt-1">
                    <TrangThaiChip tt={sel.trang_thai} />
                  </div>
                  <div className="text-[12px] text-muted-foreground mt-2">Gửi lúc {guiHienThi(sel.created_at)}</div>
                  <div className="text-[12px] text-muted-foreground mt-0.5">{sel.co_anh ? "Có ảnh chân dung" : "Chưa có ảnh"}</div>
                </div>
              </div>
              <div className="mt-4 space-y-2.5">
                {(
                  [
                    ["Số CCCD", sel.so_cccd || "—"],
                    ["Số CMND cũ", sel.so_cmnd_cu || "—"],
                    ["Giới tính", gioiTinhHienThi(sel.gioi_tinh)],
                    ["Ngày sinh", nsHienThi(sel.ngay_sinh)],
                    ["Nơi thường trú", sel.noi_tt_raw || "—"],
                    ...(sel.ma_dk ? ([["Mã đăng ký", sel.ma_dk]] as [string, string][]) : []),
                  ] as [string, string][]
                ).map(([k, v]) => (
                  <div key={k} className="flex justify-between gap-3 text-[13px] border-b border-border pb-2 last:border-0">
                    <span className="text-muted-foreground shrink-0">{k}</span>
                    <span className="font-medium text-right break-words">{v}</span>
                  </div>
                ))}
              </div>
              <p className="text-[11px] text-muted-foreground mt-3">Căn khung 3:4, xóa phông và xuất .jp2 do tool nạp thực hiện (NAP-04).</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
