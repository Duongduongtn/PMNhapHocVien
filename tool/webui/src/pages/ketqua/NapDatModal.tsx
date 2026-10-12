import { useMemo, useRef, useState } from "react";
import { Icon } from "../../components/Icon";
import {
  luuDatKQD, xemTruocDatKQD,
  type DatDong, type DatLuuKetQua, type DatXemTruoc, type TinhTrangDat,
} from "../../lib/api";
import { bangNhau, chuanHoaGio, fmtVn, parseGio, parseKm, soHien } from "./gioThucHanh";
import { nhanCanhBao } from "./kiemTruoc";

// KQD-08 — nạp giờ/km thực hành đường từ PDF báo cáo DAT, theo từng khóa.
// Bước 1 chọn file → bước 2 bảng xác nhận (giờ/km cũ → mới) → Lưu hàng loạt (chỉ 2 cột giờ/km,
// không đụng điểm/kết luận/trạng thái). Xem trước KHÔNG ghi gì.
// Số "mới" sửa được ngay trong bảng (nhận cả hh:mm); dòng sửa khác số PDF được tô để soát lại.

type Sua = { gio: string; km: string };
const GIO_TOI_DA = 999, KM_TOI_DA = 99999; // khớp ràng buộc của endpoint /dat/luu

/** Đọc ô đã sửa → số hợp lệ, hoặc null nếu trống/sai/ngoài khung. */
function giaTri(v: Sua | undefined): { gio: number | null; km: number | null; sai: boolean } {
  if (!v) return { gio: null, km: null, sai: false };
  const g = parseGio(v.gio), k = parseKm(v.km);
  const gioOk = typeof g === "number" && g >= 0 && g <= GIO_TOI_DA;
  const kmOk = typeof k === "number" && k >= 0 && k <= KM_TOI_DA;
  return { gio: gioOk ? (g as number) : null, km: kmOk ? (k as number) : null, sai: !gioOk || !kmOk };
}

const TT: Record<TinhTrangDat, { nhan: string; cls: string }> = {
  khop: { nhan: "✔ Khớp", cls: "text-success" },
  chua_chay_dat: { nhan: "⚠ Chưa chạy DAT", cls: "text-warning" },
  khong_co_trong_khoa: { nhan: "✖ Không có trong khóa", cls: "text-destructive" },
  da_ket_xuat: { nhan: "🔒 Đã kết xuất", cls: "text-muted-foreground" },
  loi_dong: { nhan: "✖ Sai dạng", cls: "text-destructive" },
  trung_dong: { nhan: "✖ Trùng dòng", cls: "text-destructive" },
};
const TOI_DA = 5 * 1024 * 1024;

export default function NapDatModal({
  maKh, tenKh, targetKey, onClose, onDone,
}: {
  maKh: string;
  tenKh: string;
  targetKey?: string;
  onClose: () => void;
  onDone: (r: DatLuuKetQua, daGui: { ma_dk: string; gio_duong: number; km_duong: number }[]) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [tenFile, setTenFile] = useState("");
  const [kq, setKq] = useState<DatXemTruoc | null>(null);
  const [chon, setChon] = useState<Set<string>>(new Set());
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [moVang, setMoVang] = useState(false);
  const [sua, setSua] = useState<Record<string, Sua>>({}); // ma_dk → số đang hiện trong ô (có thể đã sửa)

  async function docFile(f: File | undefined) {
    if (!f) return;
    setErr(""); setKq(null); setChon(new Set()); setSua({}); setTenFile(f.name);
    if (!f.name.toLowerCase().endsWith(".pdf")) { setErr("Chỉ nhận file PDF báo cáo DAT."); return; }
    if (f.size > TOI_DA) { setErr("File quá lớn (tối đa 5 MB)."); return; }
    setBusy(true);
    try {
      const r = await xemTruocDatKQD(maKh, f, targetKey);
      setKq(r);
      setChon(new Set(r.dong.filter((d) => d.tick_san).map((d) => d.ma_dk)));
      const init: Record<string, Sua> = {};
      for (const d of r.dong) if (d.chon_duoc) init[d.ma_dk] = { gio: soHien(d.gio_moi), km: soHien(d.km_moi) };
      setSua(init);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Không đọc được file — thử lại.");
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = ""; // cho phép chọn lại đúng file đó
    }
  }

  const dem = useMemo(() => {
    const c: Record<string, number> = {};
    for (const d of kq?.dong ?? []) c[d.tinh_trang] = (c[d.tinh_trang] ?? 0) + 1;
    return c;
  }, [kq]);
  const chonDuoc = useMemo(() => (kq?.dong ?? []).filter((d) => d.chon_duoc), [kq]);

  function doiO(ma: string, k: keyof Sua, v: string) {
    setSua((cur) => ({ ...cur, [ma]: { ...(cur[ma] ?? { gio: "", km: "" }), [k]: v } }));
  }

  // Dòng đang tick mà số trong ô trống/sai/ngoài khung → chặn Lưu (không ghi số đoán).
  const dongLoi = useMemo(
    () => (kq?.dong ?? []).filter((d) => d.chon_duoc && chon.has(d.ma_dk) && giaTri(sua[d.ma_dk]).sai),
    [kq, chon, sua],
  );

  // Dòng "chưa chạy DAT" (giờ trống, km 0): tick tay nghĩa là chủ ý ghi 0 → điền sẵn 0 giờ cho ô trống
  // để khỏi bị chặn Lưu vì ô rỗng. Anh/chị vẫn sửa được thành số khác.
  function dienSan0(ds: DatDong[]) {
    setSua((cur) => {
      const c = { ...cur };
      for (const d of ds) {
        if (d.tinh_trang === "chua_chay_dat" && (c[d.ma_dk]?.gio ?? "").trim() === "") {
          c[d.ma_dk] = { gio: "0", km: c[d.ma_dk]?.km ?? soHien(d.km_moi) };
        }
      }
      return c;
    });
  }

  function bat(ma: string, v: boolean) {
    setChon((cur) => { const c = new Set(cur); if (v) c.add(ma); else c.delete(ma); return c; });
    if (v) dienSan0((kq?.dong ?? []).filter((d) => d.ma_dk === ma));
  }

  async function luu() {
    if (!kq) return;
    if (dongLoi.length > 0) { setErr(`${dongLoi.length} dòng đã tick có giờ/km trống hoặc sai dạng — sửa lại hoặc bỏ tick.`); return; }
    const dong = kq.dong
      .filter((d) => chon.has(d.ma_dk) && d.chon_duoc)
      .map((d) => { const v = giaTri(sua[d.ma_dk]); return { ma_dk: d.ma_dk, gio_duong: v.gio as number, km_duong: v.km as number }; });
    if (dong.length === 0) return;
    setBusy(true); setErr("");
    try {
      onDone(await luuDatKQD({ ma_kh: maKh, dong }, targetKey), dong);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Không lưu được — kiểm kết nối rồi thử lại.");
    } finally { setBusy(false); }
  }

  // "Chọn tất cả" chỉ động tới dòng KHỚP. Dòng "chưa chạy DAT" (ghi 0 có thể đè giá trị đang có) luôn tick tay.
  const choTatCa = chonDuoc.filter((d) => d.tinh_trang === "khop");
  const tatCaDuocChon = choTatCa.length > 0 && choTatCa.every((d) => chon.has(d.ma_dk));

  return (
    <div className="fixed inset-0 z-50">
      <div className="absolute inset-0 bg-black/40" onClick={busy ? undefined : onClose} />
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] max-w-[96vw] bg-card rounded-xl shadow-2xl flex flex-col max-h-[92vh]">
        <div className="shrink-0 px-5 py-3.5 border-b border-border flex items-center gap-2">
          <Icon name="file" className="w-5 h-5 text-kq" />
          <div className="min-w-0">
            <div className="font-bold text-[15px]">Nạp giờ/km thực hành đường từ PDF DAT</div>
            <div className="text-[12px] text-muted-foreground truncate">Khóa {tenKh} · {maKh}</div>
          </div>
          <button onClick={onClose} disabled={busy} className="ml-auto text-muted-foreground hover:text-foreground disabled:opacity-50"><Icon name="x" className="w-5 h-5" /></button>
        </div>

        <div className="flex-1 min-h-0 overflow-auto px-5 py-4 space-y-3 text-[13px]">
          {err && <div className="rounded-md border border-destructive/40 bg-destructive/5 px-3 py-2 text-[12.5px] text-destructive">{err}</div>}

          <div className="flex items-center gap-3 flex-wrap">
            <input ref={inputRef} type="file" accept=".pdf,application/pdf" className="hidden" onChange={(e) => void docFile(e.target.files?.[0])} />
            <button onClick={() => inputRef.current?.click()} disabled={busy}
              className="h-9 px-4 rounded-lg border border-kq/60 text-kq font-semibold text-[13px] hover:bg-kq-soft disabled:opacity-50 inline-flex items-center gap-1.5">
              {busy && !kq ? <Icon name="refresh" className="w-4 h-4 animate-spin" /> : <Icon name="file" className="w-4 h-4" />}
              {kq ? "Chọn file khác" : "Chọn file PDF DAT"}
            </button>
            <span className="text-[12px] text-muted-foreground truncate">{tenFile || "Báo cáo kết quả đào tạo thực hành lái xe trên đường của khóa học (tải từ hệ thống DAT)."}</span>
          </div>

          {kq && (
            <>
              <div className="flex flex-wrap gap-x-4 gap-y-1 text-[12.5px]">
                <span><b className="tabular-nums">{kq.tong_file.toLocaleString("vi-VN")}</b> dòng trong file</span>
                <span className="text-success"><b className="tabular-nums">{chon.size.toLocaleString("vi-VN")}</b> sẽ ghi</span>
                {!!dem.chua_chay_dat && <span className="text-warning"><b className="tabular-nums">{dem.chua_chay_dat}</b> chưa chạy DAT (không tick sẵn)</span>}
                {!!dem.khong_co_trong_khoa && <span className="text-destructive"><b className="tabular-nums">{dem.khong_co_trong_khoa}</b> không có trong khóa</span>}
                {!!dem.da_ket_xuat && <span className="text-muted-foreground"><b className="tabular-nums">{dem.da_ket_xuat}</b> đã kết xuất</span>}
                {!!(dem.loi_dong || dem.trung_dong) && <span className="text-destructive"><b className="tabular-nums">{(dem.loi_dong ?? 0) + (dem.trung_dong ?? 0)}</b> dòng lỗi</span>}
              </div>

              <div className="rounded-lg border border-border overflow-hidden">
                <div className="max-h-[48vh] overflow-auto">
                  <table className="w-full text-[12.5px]">
                    <thead className="bg-muted/60 text-muted-foreground sticky top-0">
                      <tr className="text-left">
                        <th className="px-2 py-1.5 w-8">
                          <input type="checkbox" checked={tatCaDuocChon} disabled={choTatCa.length === 0 || busy}
                            title="Chọn / bỏ chọn các dòng Khớp (dòng chưa chạy DAT phải tick tay từng dòng)"
                            onChange={(e) => setChon((cur) => {
                              const c = new Set(cur);
                              for (const d of choTatCa) { if (e.target.checked) c.add(d.ma_dk); else c.delete(d.ma_dk); }
                              return c;
                            })} />
                        </th>
                        <th className="font-semibold px-2 py-1.5 w-10 text-center">STT</th>
                        <th className="font-semibold px-2 py-1.5">Học viên</th>
                        <th className="font-semibold px-2 py-1.5 text-right">Giờ đường (cũ → mới)</th>
                        <th className="font-semibold px-2 py-1.5 text-right">Km đường (cũ → mới)</th>
                        <th className="font-semibold px-2 py-1.5">Tình trạng</th>
                      </tr>
                    </thead>
                    <tbody>
                      {kq.dong.map((d) => (
                        <Dong key={d.ma_dk + "#" + d.stt} d={d} tick={d.chon_duoc && chon.has(d.ma_dk)} bat={bat} khoa={busy}
                          v={sua[d.ma_dk]} onSua={doiO} />
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {kq.vang_trong_file.length > 0 && (
                <div className="rounded-lg border border-border px-3 py-2 text-[12.5px]">
                  <button onClick={() => setMoVang((v) => !v)} className="font-semibold text-muted-foreground hover:text-foreground">
                    {moVang ? "▾" : "▸"} {kq.vang_trong_file.length.toLocaleString("vi-VN")} học viên của khóa không có trong file (không ghi)
                  </button>
                  {moVang && (
                    <ul className="mt-1.5 grid grid-cols-2 gap-x-4 gap-y-0.5 text-muted-foreground">
                      {kq.vang_trong_file.map((v) => <li key={v.ma_dk} className="truncate" title={v.ma_dk}>{v.ho_ten} <span className="tabular-nums">· {v.so_cccd ?? v.ma_dk}</span></li>)}
                    </ul>
                  )}
                </div>
              )}

              <div className="text-[12px] text-muted-foreground">
                <b>Số mới sửa được ngay trong bảng</b> (giờ nhận số thập phân hoặc hh:mm, vd 20:30 → 20,5). Ô nào sửa khác số PDF được tô vàng. Chỉ ghi <b>giờ đường</b> và <b>km đường</b> của các dòng đã tick; điểm, kết luận và trạng thái giữ nguyên. Học viên đã kết xuất (12/13) không ghi.
              </div>
            </>
          )}
        </div>

        <div className="shrink-0 px-5 py-3.5 border-t border-border flex items-center gap-2 justify-end">
          <button onClick={onClose} disabled={busy} className="h-9 px-4 rounded-lg border border-border text-[13px] hover:bg-muted disabled:opacity-50">Đóng</button>
          <button onClick={luu} disabled={!kq || chon.size === 0 || busy || dongLoi.length > 0}
            title={dongLoi.length > 0 ? `${dongLoi.length} dòng đã tick có giờ/km trống hoặc sai dạng` : undefined}
            className="h-9 px-5 rounded-lg bg-kq text-white font-semibold text-[13px] hover:brightness-110 disabled:opacity-40 disabled:cursor-not-allowed inline-flex items-center gap-1.5">
            {busy && kq && <Icon name="refresh" className="w-4 h-4 animate-spin" />} Lưu {chon.size.toLocaleString("vi-VN")} học viên
          </button>
        </div>
      </div>
    </div>
  );
}

function Dong({ d, tick, bat, khoa, v, onSua }: {
  d: DatDong; tick: boolean; bat: (ma: string, v: boolean) => void; khoa: boolean;
  v: Sua | undefined; onSua: (ma: string, k: keyof Sua, v: string) => void;
}) {
  const tt = TT[d.tinh_trang];
  const gt = giaTri(v);
  // Đã sửa khác số PDF? (so sau làm tròn 2 chữ số) — chỉ có nghĩa khi dòng sửa được.
  const gioSua = d.chon_duoc && v != null && !bangNhau(gt.gio, d.gio_moi);
  const kmSua = d.chon_duoc && v != null && !bangNhau(gt.km, d.km_moi);
  const doi = d.chon_duoc && (!bangNhau(gt.gio, d.gio_cu) || !bangNhau(gt.km, d.km_cu));
  const o = (k: keyof Sua, sua: boolean, rong: string) => {
    const txt = v?.[k] ?? "";
    const sai = txt.trim() !== "" ? (k === "gio" ? gt.gio == null : gt.km == null) : tick;
    return (
      <input value={txt} disabled={khoa} inputMode="decimal" placeholder={rong}
        onChange={(e) => onSua(d.ma_dk, k, e.target.value)}
        onBlur={(e) => { if (k === "gio") { const x = chuanHoaGio(e.target.value); if (x !== e.target.value) onSua(d.ma_dk, "gio", x); } }}
        title={k === "gio" ? "Số thập phân hoặc hh:mm (vd 20:30 → 20,5)" : "Số km (vd 725,63)"}
        className={"w-[64px] h-7 text-right tabular-nums text-[12.5px] px-1.5 rounded-md border bg-card focus:outline-none focus:border-kq " +
          (sai ? "border-destructive" : sua ? "border-warning bg-warning/10 font-semibold" : "border-input")} />
    );
  };
  const cu = (x: number | null) => <span className="text-muted-foreground">{fmtVn(x)}</span>;
  return (
    <tr className={"border-t border-border/60 " + (d.chon_duoc ? "" : "bg-muted/30 text-muted-foreground")}>
      <td className="px-2 py-1.5">
        <input type="checkbox" checked={tick} disabled={!d.chon_duoc || khoa} onChange={(e) => bat(d.ma_dk, e.target.checked)} />
      </td>
      <td className="px-2 py-1.5 text-center tabular-nums">{d.stt}</td>
      <td className="px-2 py-1.5 font-medium truncate max-w-[240px]" title={d.ho_ten}>
        {d.ho_ten}
        <div className="text-[11px] font-normal text-muted-foreground tabular-nums">{d.ma_dk}</div>
      </td>
      <td className="px-2 py-1.5 text-right tabular-nums whitespace-nowrap">
        {cu(d.gio_cu)} <span className="text-muted-foreground">→</span>{" "}
        {d.chon_duoc ? o("gio", gioSua, "giờ") : <span>{fmtVn(d.gio_moi)}</span>}
      </td>
      <td className="px-2 py-1.5 text-right tabular-nums whitespace-nowrap">
        {cu(d.km_cu)} <span className="text-muted-foreground">→</span>{" "}
        {d.chon_duoc ? o("km", kmSua, "km") : <span>{fmtVn(d.km_moi)}</span>}
      </td>
      <td className="px-2 py-1.5">
        <span className={"font-semibold " + tt.cls}>{tt.nhan}</span>
        {d.tinh_trang === "khop" && !doi && <span className="ml-1 text-[11px] text-muted-foreground">(không đổi)</span>}
        {(gioSua || kmSua) && <span className="ml-1.5 inline-block text-[11px] font-semibold text-warning bg-warning/10 border border-warning/40 rounded px-1.5 py-0.5">đã sửa so với PDF</span>}
        {!gioSua && !kmSua && d.canh_bao.map((w) => (
          <span key={w.loai} className="ml-1.5 inline-block text-[11px] font-semibold text-warning bg-warning/10 border border-warning/40 rounded px-1.5 py-0.5">{nhanCanhBao(w)}</span>
        ))}
        {d.ghi_chu && <div className="text-[11px] text-destructive">{d.ghi_chu}</div>}
      </td>
    </tr>
  );
}
