import { useState } from "react";
import { Icon } from "./Icon";
import { getTinh, getXa, mapDiaChi, type Tinh, type Xa } from "../lib/api";
import { tachDiaChiGoc } from "../lib/diachi";
import { boDau } from "../lib/format";

// Ô gõ-để-lọc (NAP-03, CHANGES #29): thay dropdown chọn tay — gõ tên (không dấu cũng khớp nhờ
// boDau) → danh sách gợi ý lọc dần → bấm/Enter chọn. Danh sách xã có thể dài nên gõ-lọc nhanh hơn.
function ComboLoc({
  value,
  options,
  onChon,
  placeholder,
  disabled,
}: {
  value: string;
  options: { ma: string; ten: string }[];
  onChon: (ma: string) => void;
  placeholder?: string;
  disabled?: boolean;
}) {
  const [q, setQ] = useState("");
  const [mo, setMo] = useState(false);
  const tenDaChon = options.find((o) => o.ma === value)?.ten ?? "";
  const loc = q.trim() ? options.filter((o) => boDau(o.ten).includes(boDau(q))) : options;
  const chon = (o: { ma: string; ten: string }) => {
    onChon(o.ma);
    setQ("");
    setMo(false);
  };
  return (
    <div className="relative">
      <input
        className="field-input mt-1"
        value={mo ? q : tenDaChon}
        placeholder={placeholder}
        disabled={disabled}
        onFocus={() => { setMo(true); setQ(""); }}
        onChange={(e) => { setQ(e.target.value); setMo(true); }}
        onBlur={() => window.setTimeout(() => setMo(false), 120)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && loc.length) { e.preventDefault(); chon(loc[0]); }
          else if (e.key === "Escape") setMo(false);
        }}
      />
      {mo && !disabled && (
        <ul className="absolute z-20 left-0 right-0 mt-1 max-h-56 overflow-y-auto rounded-lg border border-border bg-card shadow-lg">
          {loc.length === 0 ? (
            <li className="px-3 py-2 text-[13px] text-muted-foreground">Không tìm thấy</li>
          ) : (
            loc.slice(0, 60).map((o) => (
              <li key={o.ma}>
                <button
                  type="button"
                  onMouseDown={(e) => { e.preventDefault(); chon(o); }}
                  className={"w-full text-left px-3 py-2 text-[13px] hover:bg-muted transition-colors " + (o.ma === value ? "bg-primary/5 font-semibold" : "")}
                >
                  {o.ten}
                </button>
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  );
}

export interface DiaChiMoi {
  ma_dvhc: string;
  ma_dvql: string;
  ten_xa: string;
  ten_tinh: string;
}

// NAP-03: nhập địa chỉ CŨ (tỉnh/huyện/xã) → tự map sang xã mới 2025.
// Không khớp hoặc xã bị chia → chuyển sang chọn tay Tỉnh→Xã (không tự đoán).
// diaChiGoc (CHANGES #19): địa chỉ thô kéo về từ VPS → tự tách ĐIỀN SẴN 3 ô (operator sửa được).
// Component remount theo key={uuid} ở NapHoSo nên init theo từng hồ sơ.
export default function AddressCombo({ diaChiGoc, onChon }: { diaChiGoc?: string; onChon?: (dc: DiaChiMoi) => void }) {
  const g = tachDiaChiGoc(diaChiGoc);
  const [cuTinh, setCuTinh] = useState(g.tinh);
  const [cuHuyen, setCuHuyen] = useState(g.huyen);
  const [cuXa, setCuXa] = useState(g.xa);
  const [ketQua, setKetQua] = useState<DiaChiMoi | null>(null);
  const [tay, setTay] = useState(false);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  const [tinhList, setTinhList] = useState<Tinh[]>([]);
  const [xaList, setXaList] = useState<Xa[]>([]);
  const [mTinh, setMTinh] = useState("");

  const chon = (dc: DiaChiMoi) => {
    setKetQua(dc);
    onChon?.(dc);
  };

  const moChonTay = async () => {
    setTay(true);
    setErr("");
    if (tinhList.length === 0) {
      try {
        setTinhList(await getTinh());
      } catch {
        setErr("Không tải được danh sách tỉnh — kiểm kết nối.");
      }
    }
  };

  const chuyenDoi = async () => {
    setBusy(true);
    setErr("");
    setMsg("");
    setKetQua(null);
    try {
      const r = await mapDiaChi({ tinh: cuTinh, huyen: cuHuyen, xa: cuXa });
      if (r.matched && !r.divided && r.ma_dvhc) {
        chon({ ma_dvhc: r.ma_dvhc, ma_dvql: r.ma_dvql!, ten_xa: r.ten_xa!, ten_tinh: r.ten_tinh! });
        setMsg(`Đã map tự động: ${r.ten_xa}, ${r.ten_tinh}`);
        setTay(false);
      } else if (r.matched && r.divided) {
        setMsg("Xã cũ bị chia nhiều xã mới — chọn tay xã đúng.");
        await moChonTay();
      } else {
        setMsg("Không khớp bảng ánh xạ — chọn tay Tỉnh/Xã mới.");
        await moChonTay();
      }
    } catch {
      setErr("Gọi map địa chỉ thất bại — kiểm tool backend/kết nối.");
    } finally {
      setBusy(false);
    }
  };

  const chonTinh = async (ma: string) => {
    setMTinh(ma);
    setXaList([]);
    if (!ma) return;
    try {
      setXaList(await getXa(ma));
    } catch {
      setErr("Không tải được danh sách xã.");
    }
  };

  const chonXa = (ma: string) => {
    const xa = xaList.find((x) => x.ma_dvhc === ma);
    const tinh = tinhList.find((t) => t.ma_dvql === mTinh);
    if (xa && tinh) {
      chon({ ma_dvhc: xa.ma_dvhc, ma_dvql: xa.ma_dvql, ten_xa: xa.ten_xa, ten_tinh: tinh.ten_tinh });
      setMsg("");
    }
  };

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <h3 className="text-sm font-bold mb-3 flex items-center gap-2">
        <Icon name="file" className="w-4 h-4 text-primary" /> Nơi thường trú — map địa chỉ
        <span className="text-[11px] font-semibold text-primary bg-primary/10 rounded-full px-2 py-0.5">NAP-03</span>
      </h3>

      {/* Địa chỉ cũ (text) */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label className="field-label">Tỉnh/TP cũ <span className="text-destructive">*</span></label>
          <input className="field-input mt-1" placeholder="VD: Đồng Nai" value={cuTinh} onChange={(e) => setCuTinh(e.target.value)} />
        </div>
        <div>
          <label className="field-label">Quận/Huyện cũ</label>
          <input className="field-input mt-1" placeholder="VD: Long Thành" value={cuHuyen} onChange={(e) => setCuHuyen(e.target.value)} />
        </div>
        <div>
          <label className="field-label">Phường/Xã cũ <span className="text-destructive">*</span></label>
          <input className="field-input mt-1" placeholder="VD: An Phước" value={cuXa} onChange={(e) => setCuXa(e.target.value)} />
        </div>
      </div>

      <div className="flex items-center gap-3 mt-3 flex-wrap">
        <button
          onClick={chuyenDoi}
          disabled={busy || !cuTinh || !cuXa}
          className="inline-flex items-center gap-2 h-9 px-4 rounded-lg bg-primary text-primary-foreground font-semibold text-sm hover:brightness-110 transition-all disabled:opacity-60"
        >
          <Icon name="refresh" className={"w-4 h-4" + (busy ? " animate-spin" : "")} /> Chuyển đổi sang xã mới
        </button>
        <button
          onClick={moChonTay}
          className="inline-flex items-center gap-2 h-9 px-3 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors"
        >
          Chọn tay
        </button>
      </div>

      {msg && (
        <div className="mt-3 flex items-center gap-2 text-[13px] text-muted-foreground">
          <Icon name="warn" className="w-4 h-4" /> {msg}
        </div>
      )}

      {/* Chọn tay Tỉnh → Xã mới */}
      {tay && (
        <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="field-label">Tỉnh/TP mới</label>
            <ComboLoc
              value={mTinh}
              options={tinhList.map((t) => ({ ma: t.ma_dvql, ten: t.ten_tinh }))}
              onChon={chonTinh}
              placeholder="Gõ tên tỉnh/TP…"
            />
          </div>
          <div>
            <label className="field-label">Phường/Xã mới</label>
            <ComboLoc
              value={ketQua?.ma_dvhc ?? ""}
              options={xaList.map((x) => ({ ma: x.ma_dvhc, ten: x.ten_xa }))}
              onChon={chonXa}
              placeholder={mTinh ? "Gõ tên phường/xã…" : "Chọn tỉnh trước"}
              disabled={!mTinh}
            />
          </div>
        </div>
      )}

      {/* Kết quả đã chốt */}
      {ketQua && (
        <div className="mt-3 flex items-center gap-2 text-[13px] font-semibold text-success bg-success/10 border border-success/30 rounded-lg px-3 py-2">
          <Icon name="check" className="w-4 h-4" sw={3} />
          {ketQua.ten_xa}, {ketQua.ten_tinh} · Mã {ketQua.ma_dvhc}/{ketQua.ma_dvql}
        </div>
      )}

      {err && (
        <div className="mt-3 flex items-center gap-2 text-[13px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2">
          <Icon name="warn" className="w-4 h-4" /> {err}
        </div>
      )}
    </div>
  );
}
