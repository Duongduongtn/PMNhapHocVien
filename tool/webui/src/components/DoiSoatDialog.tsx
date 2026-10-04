import { useState } from "react";
import { Icon } from "./Icon";
import { useToolAuth } from "../auth/ToolAuth";
import {
  doiSoatKhoa,
  quetLac,
  doiSoatDaNap,
  doiSoatTraVe,
  doiSoatMoKhoa,
  type DoiSoatDong,
  type KhongTraDuoc,
} from "../lib/api";

// QLY-09 (task 49) — panel "Đối soát VPS↔CSDT": phát hiện + sửa 1 chạm các bản ghi lệch trạng thái
// giữa máy chủ (VPS) và CSDT. Theo khóa (ca ②, operator/admin) + Quét lạc toàn hệ (ca ①③, admin).

function loiNghiepVu(d: DoiSoatDong): string {
  if (d.loai === "①") return "Máy chủ báo ĐÃ NẠP nhưng CSDT không có hồ sơ — hồ sơ 'ma' kẹt trên máy chủ.";
  if (d.loai === "②") return "Hồ sơ đã vào CSDT nhưng máy chủ chưa ghi nhận đã nạp — kẹt ở bước báo máy chủ.";
  return "Hồ sơ đang nạp bị treo quá lâu (không ai đang nạp) — khóa kẹt trên máy chủ.";
}

const NHAN_HANH_DONG: Record<string, string> = {
  da_nap: "Đánh dấu đã nạp",
  tra_ve_cho_nap: "Trả về chờ nạp",
  unlock: "Mở khóa",
};

export default function DoiSoatDialog({
  khoaMa, tenKhoa, onDong,
}: { khoaMa?: string; tenKhoa?: string; onDong: () => void }) {
  const { user } = useToolAuth();
  const laAdmin = user?.vai_tro === "admin";

  const [che, setChe] = useState<"khoa" | "lac">(khoaMa ? "khoa" : "lac");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [daQuet, setDaQuet] = useState(false);
  const [dong, setDong] = useState<DoiSoatDong[]>([]);
  const [khongTra, setKhongTra] = useState<KhongTraDuoc[]>([]);
  const [suaBusy, setSuaBusy] = useState<string | null>(null); // uuid đang sửa

  async function quet() {
    setErr(""); setBusy(true); setDaQuet(false);
    try {
      if (che === "khoa") {
        if (!khoaMa) { setErr("Chưa chọn khóa để đối soát."); return; }
        const kq = await doiSoatKhoa(khoaMa);
        setDong(kq.ca2);
        setKhongTra(kq.khong_tra_duoc);
      } else {
        const kq = await quetLac();
        setDong([...kq.phantom, ...kq.treo]);
        setKhongTra([]);
      }
      setDaQuet(true);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Không đối soát được — kiểm kết nối máy chủ.");
    } finally {
      setBusy(false);
    }
  }

  async function sua(d: DoiSoatDong) {
    if (!d.uuid) return;
    setErr(""); setSuaBusy(d.uuid);
    try {
      if (d.hanh_dong === "da_nap") await doiSoatDaNap(d.uuid, d.ma_dk ?? "");
      else if (d.hanh_dong === "tra_ve_cho_nap") await doiSoatTraVe(d.uuid);
      else await doiSoatMoKhoa(d.uuid);
      await quet(); // làm tươi — dòng đã khớp biến mất
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Sửa không thành công — thử lại.");
    } finally {
      setSuaBusy(null);
    }
  }

  const doiChe = (c: "khoa" | "lac") => { setChe(c); setDaQuet(false); setDong([]); setKhongTra([]); setErr(""); };

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4"
         onClick={(e) => { if (e.target === e.currentTarget && !busy && !suaBusy) onDong(); }}>
      <div className="bg-card w-full max-w-lg rounded-xl shadow-2xl max-h-[90vh] flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3 border-b border-border">
          <h3 className="font-bold text-sm">Đối soát máy chủ ↔ cơ sở dữ liệu</h3>
          <button onClick={onDong} aria-label="Đóng" className="w-8 h-8 rounded-lg hover:bg-muted flex items-center justify-center transition-colors">
            <Icon name="x" className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5 overflow-y-auto space-y-3">
          {/* Chọn chế độ */}
          <div className="flex gap-2">
            {khoaMa && (
              <button onClick={() => doiChe("khoa")}
                className={"h-8 px-3 rounded-md text-[13px] font-semibold transition-colors " + (che === "khoa" ? "bg-primary text-primary-foreground" : "border border-border hover:bg-muted")}>
                Theo khóa{tenKhoa ? ` · ${tenKhoa}` : ""}
              </button>
            )}
            {laAdmin && (
              <button onClick={() => doiChe("lac")}
                className={"h-8 px-3 rounded-md text-[13px] font-semibold transition-colors " + (che === "lac" ? "bg-primary text-primary-foreground" : "border border-border hover:bg-muted")}>
                Quét bản ghi lạc (toàn hệ)
              </button>
            )}
          </div>

          <p className="text-[12px] text-muted-foreground">
            {che === "khoa"
              ? "So hồ sơ của khóa này giữa máy chủ và CSDT — bắt ca hồ sơ đã vào CSDT mà máy chủ chưa ghi nhận."
              : "Quét toàn hệ các bản ghi 'ma' (máy chủ báo nạp mà CSDT không có) và khóa nạp bị treo."}
          </p>

          <button onClick={() => void quet()} disabled={busy || (che === "khoa" && !khoaMa)}
            className="h-9 px-4 rounded-lg bg-primary text-primary-foreground text-[13px] font-semibold inline-flex items-center gap-2 hover:brightness-110 transition-all shadow-sm disabled:opacity-60">
            <Icon name={busy ? "refresh" : "search"} className={"w-4 h-4" + (busy ? " animate-spin" : "")} />
            {busy ? "Đang đối soát…" : "Đối soát"}
          </button>

          {err && (
            <p className="text-[12.5px] text-destructive flex items-start gap-1.5">
              <Icon name="warn" className="w-4 h-4 shrink-0 mt-px" /> {err}
            </p>
          )}

          {daQuet && !busy && (
            dong.length === 0 && khongTra.length === 0 ? (
              <p className="text-[13px] text-success flex items-center gap-1.5 py-2">
                <Icon name="check" className="w-4 h-4" sw={3} /> Không có dòng lệch — máy chủ và CSDT khớp.
              </p>
            ) : (
              <div className="space-y-2">
                {dong.map((d) => (
                  <div key={d.uuid} className="rounded-lg border border-warning/40 bg-warning/5 p-3">
                    <div className="flex items-start gap-2">
                      <span className="text-[13px] font-bold shrink-0">{d.loai}</span>
                      <div className="min-w-0 flex-1">
                        <div className="font-semibold text-[13px] truncate">
                          {(d.ho_ten || "").toUpperCase() || "(chưa có tên)"}
                          {d.ma_dk && <span className="font-normal text-muted-foreground"> · MaDK {d.ma_dk}</span>}
                        </div>
                        <div className="text-[12px] text-muted-foreground">{loiNghiepVu(d)}</div>
                      </div>
                      <button onClick={() => void sua(d)} disabled={suaBusy !== null}
                        className="h-8 px-3 rounded-md bg-warning text-white text-[12px] font-semibold inline-flex items-center gap-1 hover:brightness-110 transition-all shrink-0 disabled:opacity-60">
                        <Icon name={suaBusy === d.uuid ? "refresh" : "check"} className={"w-3.5 h-3.5" + (suaBusy === d.uuid ? " animate-spin" : "")} sw={3} />
                        {NHAN_HANH_DONG[d.hanh_dong] ?? "Sửa"}
                      </button>
                    </div>
                  </div>
                ))}
                {khongTra.length > 0 && (
                  <div className="rounded-lg border border-border bg-muted/40 p-3 text-[12px] text-muted-foreground">
                    <div className="font-semibold text-foreground mb-1">{khongTra.length} hồ sơ không tra được bản gốc máy chủ</div>
                    {khongTra.map((k) => (
                      <div key={k.ma_dk} className="truncate">
                        · {(k.ho_ten || "").toUpperCase() || "(chưa tên)"} (MaDK {k.ma_dk}){k.ly_do ? ` — ${k.ly_do}` : " — máy khác nạp / đã dọn staging"}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )
          )}
        </div>

        <div className="p-3 border-t border-border flex">
          <button onClick={onDong} disabled={busy || suaBusy !== null}
            className="ml-auto h-10 px-5 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors disabled:opacity-60">Đóng</button>
        </div>
      </div>
    </div>
  );
}
