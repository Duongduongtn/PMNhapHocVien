import { useState } from "react";
import { Icon } from "./Icon";
import { getTinh, getXa, mapDiaChi, type Tinh, type Xa } from "../lib/api";

export interface DiaChiMoi {
  ma_dvhc: string;
  ma_dvql: string;
  ten_xa: string;
  ten_tinh: string;
}

// NAP-03: nhập địa chỉ CŨ (tỉnh/huyện/xã) → tự map sang xã mới 2025.
// Không khớp hoặc xã bị chia → chuyển sang chọn tay Tỉnh→Xã (không tự đoán).
export default function AddressCombo({ onChon }: { onChon?: (dc: DiaChiMoi) => void }) {
  const [cuTinh, setCuTinh] = useState("");
  const [cuHuyen, setCuHuyen] = useState("");
  const [cuXa, setCuXa] = useState("");
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
            <select className="field-input mt-1" value={mTinh} onChange={(e) => chonTinh(e.target.value)}>
              <option value="">— Chọn tỉnh —</option>
              {tinhList.map((t) => (
                <option key={t.ma_dvql} value={t.ma_dvql}>{t.ten_tinh}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="field-label">Phường/Xã mới</label>
            <select className="field-input mt-1" disabled={!mTinh} value={ketQua?.ma_dvhc ?? ""} onChange={(e) => chonXa(e.target.value)}>
              <option value="">— Chọn xã —</option>
              {xaList.map((x) => (
                <option key={x.ma_dvhc} value={x.ma_dvhc}>{x.ten_xa}</option>
              ))}
            </select>
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
