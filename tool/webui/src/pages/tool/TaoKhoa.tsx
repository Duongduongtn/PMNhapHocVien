import { useEffect, useState } from "react";
import { Icon } from "../../components/Icon";
import { getHangDT, taoKhoa, type HangDT } from "../../lib/api";

// KHO-01 — Tạo khóa học qua usp_KhoaHoc_Insert (mã tự sinh). 5 bắt buộc + 4 tùy chọn.
export default function TaoKhoa() {
  const [ds, setDs] = useState<HangDT[] | null>(null);
  const [loadErr, setLoadErr] = useState("");

  const [hangDt, setHangDt] = useState("");
  const [tenKh, setTenKh] = useState("");
  const [ngayKg, setNgayKg] = useState("");
  const [ngayBg, setNgayBg] = useState("");
  const [tongHv, setTongHv] = useState("");

  const [optOpen, setOptOpen] = useState(false);
  const [soQd, setSoQd] = useState("");
  const [ngayQd, setNgayQd] = useState("");
  const [ngayThi, setNgayThi] = useState("");
  const [ghiChu, setGhiChu] = useState("");

  const [dangTao, setDangTao] = useState(false);
  const [err, setErr] = useState("");
  const [kq, setKq] = useState<{ ma_kh: string } | null>(null);

  useEffect(() => {
    getHangDT()
      .then((x) => {
        setDs(x);
        setHangDt((cur) => cur || (x[0]?.ma_hang_dt ?? ""));
      })
      .catch(() => setLoadErr("Không tải được danh sách hạng đào tạo (kiểm kết nối SQL Server / đăng nhập)."));
  }, []);

  const hang = ds?.find((h) => h.ma_hang_dt === hangDt) ?? null;

  async function onTao() {
    setErr("");
    setKq(null);
    const hv = Number(tongHv);
    if (!hangDt || !tenKh.trim() || !ngayKg || !ngayBg || !hv || hv <= 0) {
      setErr("Điền đủ 5 trường bắt buộc (hạng, tên khóa, ngày KG, ngày BG, tổng số HV > 0).");
      return;
    }
    if (ngayBg < ngayKg) {
      setErr("Ngày bế giảng không được trước ngày khai giảng.");
      return;
    }
    setDangTao(true);
    try {
      const r = await taoKhoa({
        hang_dt: hangDt,
        ten_kh: tenKh.trim(),
        ngay_kg: ngayKg,
        ngay_bg: ngayBg,
        tong_so_hv: hv,
        so_qd: soQd || null,
        ngay_qd: ngayQd || null,
        ngay_thi: ngayThi || null,
        ghi_chu: ghiChu || null,
      });
      setKq(r);
      // Giữ hạng để tạo tiếp cùng hạng; xóa các trường còn lại.
      setTenKh("");
      setNgayKg("");
      setNgayBg("");
      setTongHv("");
      setSoQd("");
      setNgayQd("");
      setNgayThi("");
      setGhiChu("");
      setOptOpen(false);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Tạo khóa thất bại.");
    } finally {
      setDangTao(false);
    }
  }

  return (
    <div className="p-4 max-w-2xl">
      <h2 className="text-base font-bold mb-1">Tạo khóa học</h2>
      <p className="text-[12px] text-muted-foreground mb-4">
        Khóa tạo ra hiện ngay trong app cũ. Mã khóa tự sinh theo hạng.
      </p>

      {loadErr && (
        <div className="mb-4 flex items-center gap-2 text-[13px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2">
          <Icon name="warn" className="w-4 h-4 shrink-0" /> {loadErr}
        </div>
      )}

      {/* Tự điền theo hạng */}
      {hang && (
        <div className="rounded-md bg-secondary/70 border border-border px-3 py-2 text-[11px] text-muted-foreground leading-relaxed mb-4">
          <b className="text-foreground">Tự điền khi tạo:</b> Mã khóa tự sinh · HangGPLX{" "}
          <b className="text-foreground">{hang.hang_gplx}</b>
          {hang.tuoi_hv != null && <> · Tuổi tối thiểu <b className="text-foreground">{hang.tuoi_hv}</b></>}
          {hang.thoi_gian_dt != null && <> · Thời gian ĐT <b className="text-foreground">{hang.thoi_gian_dt}</b></>} · MaCSDT 70004 · MaSoGTVT 70 · TrangThai 1
        </div>
      )}

      <fieldset disabled={dangTao || !ds} className="contents">
        {/* Bắt buộc */}
        <div className="flex items-center gap-2 mb-2">
          <span className="inline-flex items-center gap-1.5 text-[11px] font-bold text-destructive">
            <span className="w-1.5 h-1.5 rounded-full bg-destructive" /> BẮT BUỘC
          </span>
          <div className="flex-1 h-px bg-border" />
          <span className="text-[10px] text-muted-foreground">5 trường · * phải điền</span>
        </div>
        <div className="rounded-lg border border-destructive/25 bg-destructive/[0.03] p-4 space-y-3">
          <div>
            <label className="field-label">Hạng đào tạo <span className="text-destructive">*</span></label>
            <select className="field-input mt-1" value={hangDt} onChange={(e) => setHangDt(e.target.value)}>
              {!ds && <option value="">Đang tải…</option>}
              {ds?.map((h) => (
                <option key={h.ma_hang_dt} value={h.ma_hang_dt}>
                  {h.ten} ({h.ma_hang_dt})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="field-label">Tên khóa <span className="text-destructive">*</span></label>
            <input className="field-input mt-1" value={tenKh} onChange={(e) => setTenKh(e.target.value)} placeholder="VD: B-K150" maxLength={50} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="field-label">Ngày khai giảng <span className="text-destructive">*</span></label>
              <input type="date" className="field-input mt-1" value={ngayKg} onChange={(e) => setNgayKg(e.target.value)} />
            </div>
            <div>
              <label className="field-label">Ngày bế giảng <span className="text-destructive">*</span></label>
              <input type="date" className="field-input mt-1" value={ngayBg} onChange={(e) => setNgayBg(e.target.value)} />
            </div>
          </div>
          <div>
            <label className="field-label">Tổng số học viên <span className="text-destructive">*</span></label>
            <input className="field-input mt-1" value={tongHv} onChange={(e) => setTongHv(e.target.value.replace(/\D/g, ""))} inputMode="numeric" placeholder="VD: 50" />
          </div>
        </div>

        {/* Tùy chọn */}
        <div className="rounded-lg border border-border overflow-hidden mt-4">
          <button type="button" onClick={() => setOptOpen((v) => !v)} className="w-full flex items-center justify-between px-3 py-2.5 bg-muted/40 hover:bg-muted transition-colors text-left">
            <span className="text-[13px] font-semibold flex items-center gap-2">
              <Icon name="plus" className="w-4 h-4 text-muted-foreground" /> Thông tin thêm{" "}
              <span className="font-normal text-muted-foreground text-[11px]">(không bắt buộc)</span>
            </span>
            <Icon name="chevronDown" className={"w-4 h-4 text-muted-foreground transition-transform " + (optOpen ? "rotate-180" : "")} />
          </button>
          {optOpen && (
            <div className="p-3 space-y-3 border-t border-border bg-card">
              <div className="grid grid-cols-2 gap-3">
                <div><label className="field-label">Số quyết định</label><input className="field-input mt-1" value={soQd} onChange={(e) => setSoQd(e.target.value)} placeholder="(có thể trống)" /></div>
                <div><label className="field-label">Ngày quyết định</label><input type="date" className="field-input mt-1" value={ngayQd} onChange={(e) => setNgayQd(e.target.value)} /></div>
              </div>
              <div><label className="field-label">Ngày thi</label><input type="date" className="field-input mt-1" value={ngayThi} onChange={(e) => setNgayThi(e.target.value)} /></div>
              <div><label className="field-label">Ghi chú</label><input className="field-input mt-1" value={ghiChu} onChange={(e) => setGhiChu(e.target.value)} placeholder="..." maxLength={255} /></div>
            </div>
          )}
        </div>

        <div className="mt-4">
          <button
            type="button"
            onClick={() => void onTao()}
            className="btn btn-primary"
          >
            <Icon name={dangTao ? "refresh" : "plus"} className={"w-4 h-4" + (dangTao ? " animate-spin" : "")} /> {dangTao ? "Đang tạo…" : "Tạo khóa học"}
          </button>
        </div>
      </fieldset>

      {kq && (
        <div className="mt-4 flex items-center gap-2 text-[13px] text-success bg-success/10 border border-success/30 rounded-lg px-3 py-2">
          <Icon name="check" className="w-4 h-4 shrink-0" sw={3} /> Đã tạo khóa — mã <b className="font-mono">{kq.ma_kh}</b>. Có thể tạo khóa tiếp (giữ hạng đang chọn).
        </div>
      )}
      {err && (
        <div className="mt-4 flex items-center gap-2 text-[13px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2">
          <Icon name="warn" className="w-4 h-4 shrink-0" /> {err}
        </div>
      )}
    </div>
  );
}
