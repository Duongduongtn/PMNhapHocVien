import { useMemo, useState, type ReactNode } from "react";
import { Icon } from "../../components/Icon";
import {
  hoSoChoNap, hocVienTrongKhoa, dmDvhc, khoaOto, khoaMoto, khoaTraCuu,
  type TrangThaiMap, type TrangThaiAnh, type NapTrangThai, type HocVienDB, type KhoaTraCuu,
} from "../../lib/mock-data";

function Chip({ kind }: { kind: TrangThaiMap | TrangThaiAnh }) {
  const map: Record<string, string> = {
    map: "text-success bg-success/10 border-success/30",
    photo: "text-success bg-success/10 border-success/30",
    manual: "text-warning bg-warning/10 border-warning/30",
    no: "text-muted-foreground bg-muted border-border",
  };
  const label: Record<string, string> = { map: "Đã map", photo: "Ảnh ✓", manual: "Chọn tay", no: "Chưa ảnh" };
  return <span className={`text-[11px] font-medium border rounded-full px-2 py-0.5 whitespace-nowrap ${map[kind]}`}>{label[kind]}</span>;
}

// Badge trạng thái nạp lô (CHANGES #6) — màu + icon + chữ để phủ mù màu (⚪ chờ · 🔴 lỗi · 🟢 đã nạp)
function NapBadge({ tt }: { tt: NapTrangThai }) {
  const cfg = {
    cho: { cls: "text-muted-foreground bg-muted border-border", icon: "clock", label: "Chờ nạp" },
    loi: { cls: "text-destructive bg-destructive/10 border-destructive/40", icon: "warn", label: "Lỗi" },
    nap: { cls: "text-success bg-success/10 border-success/40", icon: "check", label: "Đã nạp" },
  }[tt];
  return (
    <span className={`inline-flex items-center gap-1 text-[11px] font-semibold border rounded-full px-2 py-0.5 whitespace-nowrap ${cfg.cls}`}>
      <Icon name={cfg.icon} className="w-3 h-3" sw={2.5} /> {cfg.label}
    </span>
  );
}

// Banner cảnh báo inline nổi bật (NFR⑥) — nền + viền trái dày + icon + nêu rõ nguyên nhân
function Banner({ tone = "warning", children }: { tone?: "warning" | "error"; children: ReactNode }) {
  const cls = tone === "error"
    ? "border-destructive/40 border-l-destructive bg-destructive/10 text-destructive"
    : "border-warning/40 border-l-warning bg-warning/10 text-warning";
  return (
    <div role="alert" className={`flex items-start gap-2.5 rounded-lg border border-l-4 px-3 py-2.5 ${cls}`}>
      <Icon name="warn" className="w-5 h-5 shrink-0 mt-px" />
      <div className="text-[12.5px] font-medium leading-relaxed">{children}</div>
    </div>
  );
}

function Avatar({ mau }: { mau: string }) {
  return (
    <span className={`inline-flex w-9 h-9 rounded-full items-center justify-center shrink-0 ${mau}`}>
      <Icon name="user" className="w-5 h-5 text-white/90" />
    </span>
  );
}

// Combobox địa chỉ tra DM_DVHC (mock — thật nối usp_DM_DVHC_*)
function AddressCombo({ value, onPick }: { value: string; onPick: (ten: string, code: string, dvql: string) => void }) {
  const [q, setQ] = useState(value);
  const [open, setOpen] = useState(false);
  const rows = dmDvhc.filter(([c, d, t]) => !q || t.toLowerCase().includes(q.toLowerCase()) || `${c}/${d}`.includes(q));
  return (
    <div className="relative">
      <input
        className="field-input" value={q} autoComplete="off" placeholder="Gõ tên xã/tỉnh hoặc mã DVHC…"
        onChange={(e) => { setQ(e.target.value); setOpen(true); }} onFocus={() => setOpen(true)} onBlur={() => setTimeout(() => setOpen(false), 150)}
      />
      {open && (
        <div className="absolute z-30 left-0 right-0 mt-1 bg-card border border-border rounded-lg shadow-lg max-h-52 overflow-y-auto">
          {rows.length ? rows.map(([c, d, t]) => (
            <button key={c} type="button" onMouseDown={(e) => e.preventDefault()} onClick={() => { setQ(t); setOpen(false); onPick(t, c, d); }}
              className="w-full text-left px-3 py-2 hover:bg-accent transition-colors flex items-center gap-2 border-b border-border last:border-0">
              <span className="font-mono text-[11px] bg-secondary rounded px-1.5 py-0.5 shrink-0">{c}/{d}</span>
              <span className="text-[13px] truncate">{t}</span>
            </button>
          )) : <div className="px-3 py-2 text-[12px] text-muted-foreground">Không khớp mã/tên — kiểm lại</div>}
        </div>
      )}
    </div>
  );
}

// Combobox chọn khóa cho chế độ Tra cứu — hiện MỌI khóa kể cả 🔒 đã BC1
function KhoaCombo({ value, onPick }: { value: KhoaTraCuu; onPick: (k: KhoaTraCuu) => void }) {
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const rows = khoaTraCuu.filter((k) => !q || k.ten.toLowerCase().includes(q.toLowerCase()) || k.ma.includes(q));
  return (
    <div className="relative" style={{ minWidth: 320 }}>
      <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground"><Icon name="search" className="w-4 h-4" /></span>
      <input
        className="field-input pl-8" autoComplete="off"
        value={open ? q : `${value.ma} — ${value.ten}${value.bc1 ? " · 🔒 đã BC1" : ""}`}
        placeholder="Tìm khóa theo tên hoặc mã (mọi khóa, kể cả đã BC1)…"
        onChange={(e) => { setQ(e.target.value); setOpen(true); }} onFocus={() => { setQ(""); setOpen(true); }} onBlur={() => setTimeout(() => setOpen(false), 150)}
      />
      {open && (
        <div className="absolute z-30 left-0 right-0 mt-1 bg-card border border-border rounded-lg shadow-lg max-h-64 overflow-y-auto">
          {rows.length ? rows.map((k) => (
            <button key={k.ma} type="button" onMouseDown={(e) => e.preventDefault()} onClick={() => { onPick(k); setOpen(false); }}
              className="w-full text-left px-3 py-2 hover:bg-accent transition-colors flex items-center gap-2 border-b border-border last:border-0">
              <span className="font-mono text-[11px] bg-secondary rounded px-1.5 py-0.5 shrink-0">{k.ma}</span>
              <span className="text-[13px] font-semibold">{k.ten}</span>
              <span className="text-[11px] text-muted-foreground">KG {k.kg} · {k.siSo} HV</span>
              {k.bc1
                ? <span className="ml-auto inline-flex items-center gap-1 text-[11px] font-semibold text-warning"><Icon name="lock" className="w-3 h-3" /> đã BC1</span>
                : <span className="ml-auto text-[11px] text-success font-medium">chưa BC1</span>}
            </button>
          )) : <div className="px-3 py-2 text-[12px] text-muted-foreground">Không khớp tên/mã khóa</div>}
        </div>
      )}
    </div>
  );
}

export default function NapHoSo() {
  const [mode, setMode] = useState<"nap" | "tracuu">("nap"); // IA 2 chế độ (CHANGES #6)
  const [loai, setLoai] = useState<"oto" | "moto">("oto");
  const [sel, setSel] = useState(0);
  const [optOpen, setOptOpen] = useState(false);
  const [giongTT, setGiongTT] = useState(true);
  const [modal, setModal] = useState(false);
  const [addrChip, setAddrChip] = useState("Đã map · Mã 25267/75");
  const [napFilter, setNapFilter] = useState<"canxuly" | "danap">("canxuly"); // lọc hàng chờ nạp lô
  const [khoaTC, setKhoaTC] = useState<KhoaTraCuu>(khoaTraCuu[0]); // khóa đang tra cứu
  const [selDb, setSelDb] = useState<HocVienDB | null>(null); // QLY-01 xem/sửa
  const [doiKhoa, setDoiKhoa] = useState(false); // QLY-02
  const [xoaHV, setXoaHV] = useState(false); // QLY-03
  const khoaList = loai === "oto" ? khoaOto : khoaMoto;

  // Phân loại hàng chờ nạp lô: "Cần xử lý" = ⚪ chờ + 🔴 lỗi (lỗi lên đầu) · "Đã nạp" = 🟢
  const canXuly = useMemo(
    () => hoSoChoNap.filter((r) => r.tt !== "nap").sort((a, b) => (b.tt === "loi" ? 1 : 0) - (a.tt === "loi" ? 1 : 0)),
    [],
  );
  const daNap = useMemo(() => hoSoChoNap.filter((r) => r.tt === "nap"), []);
  const rows = napFilter === "canxuly" ? canXuly : daNap;
  const soLoi = hoSoChoNap.filter((r) => r.tt === "loi").length;
  const soChinhTa = hoSoChoNap.filter((r) => r.chinhTa).length;
  const soTick = canXuly.filter((r) => r.tick && r.tt === "cho").length;

  return (
    <>
      {/* Thanh IA 2 chế độ (CHANGES #6) */}
      <div className="px-4 py-3 border-b border-border flex items-center gap-3 flex-wrap">
        <div className="inline-flex rounded-lg border border-border bg-muted p-1">
          <button onClick={() => setMode("nap")}
            className={"inline-flex items-center gap-2 px-4 py-2 text-sm rounded-md transition-colors " + (mode === "nap" ? "bg-primary text-primary-foreground font-semibold shadow-sm" : "text-muted-foreground font-medium hover:text-foreground")}>
            <Icon name="plus" className="w-4 h-4" /> Nạp hồ sơ
          </button>
          <button onClick={() => setMode("tracuu")}
            className={"inline-flex items-center gap-2 px-4 py-2 text-sm rounded-md transition-colors " + (mode === "tracuu" ? "bg-primary text-primary-foreground font-semibold shadow-sm" : "text-muted-foreground font-medium hover:text-foreground")}>
            <Icon name="search" className="w-4 h-4" /> Tra cứu DB
          </button>
        </div>
        <p className="text-[12px] text-muted-foreground">
          {mode === "nap"
            ? "Kéo hồ sơ từ VPS và nạp vào khóa chưa lập BC1."
            : "Tìm mọi khóa (kể cả 🔒 đã BC1) để xem/sửa hồ sơ đã có trong DB. Khóa đã BC1 chỉ xem."}
        </p>
      </div>

      {/* ============ CHẾ ĐỘ NẠP HỒ SƠ ============ */}
      {mode === "nap" && (
        <>
          {/* Toolbar chọn khóa (chỉ khóa chưa BC1) */}
          <div className="px-4 py-3 border-b border-border bg-muted/40 flex items-center gap-4 flex-wrap">
            <div className="inline-flex rounded-lg border border-border bg-card p-0.5">
              {(["moto", "oto"] as const).map((l) => (
                <button key={l} onClick={() => setLoai(l)}
                  className={"px-4 py-1.5 text-sm rounded-md " + (loai === l ? "bg-primary text-primary-foreground font-semibold" : "text-muted-foreground font-medium")}>
                  {l === "moto" ? "Mô tô" : "Ô tô"}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <label className="field-label whitespace-nowrap">Khóa đích</label>
              <select className="field-input" style={{ minWidth: 320 }}>
                {khoaList.map((k) => <option key={k}>{k}</option>)}
              </select>
              <span className="text-[11px] text-muted-foreground">(chỉ khóa chưa BC1)</span>
            </div>
            <div className="flex items-center gap-2 text-[12px]">
              <span className="inline-flex items-center gap-1 rounded-full bg-secondary px-2.5 py-1">Hạng ĐT <b className="text-foreground">B</b></span>
              <span className="inline-flex items-center gap-1 rounded-full bg-secondary px-2.5 py-1">Sĩ số <b className="text-foreground">55</b>/50</span>
              <span className="inline-flex items-center gap-1 rounded-full bg-primary/10 text-primary px-2.5 py-1 font-semibold">Cần xử lý {canXuly.length}</span>
            </div>
            <button className="ml-auto inline-flex items-center gap-2 h-9 px-4 rounded-lg border border-primary text-primary font-semibold text-sm hover:bg-primary/5 transition-colors">
              <Icon name="refresh" className="w-4 h-4" /> Kéo về từ VPS
            </button>
          </div>

          {/* 3 cột */}
          <div className="flex flex-col xl:flex-row xl:h-[720px]">
            {/* CỘT 1: LIST hàng chờ nạp lô */}
            <div className="flex-1 min-w-0 border-b xl:border-b-0 xl:border-r border-border flex flex-col min-h-0">
              <div className="px-4 py-3 flex items-center gap-3 flex-wrap border-b border-border shrink-0">
                <div className="inline-flex rounded-lg bg-muted p-1">
                  <button onClick={() => setNapFilter("canxuly")} className={"inline-flex items-center gap-2 px-3.5 py-1.5 text-sm rounded-md " + (napFilter === "canxuly" ? "bg-card shadow-sm text-primary font-semibold" : "text-muted-foreground font-medium hover:text-foreground transition-colors")}>
                    <Icon name="clock" className="w-4 h-4" /> Cần xử lý <span className="text-[11px] bg-primary/10 rounded-full px-1.5">{canXuly.length}</span>
                  </button>
                  <button onClick={() => setNapFilter("danap")} className={"inline-flex items-center gap-2 px-3.5 py-1.5 text-sm rounded-md " + (napFilter === "danap" ? "bg-card shadow-sm text-success font-semibold" : "text-muted-foreground font-medium hover:text-foreground transition-colors")}>
                    <Icon name="check" className="w-4 h-4" /> Đã nạp <span className="text-[11px] bg-success/15 text-success rounded-full px-1.5">{daNap.length}</span>
                  </button>
                </div>
                {napFilter === "canxuly" && (
                  <div className="ml-auto flex items-center gap-3">
                    <span className="text-[12px] text-muted-foreground">Đã chọn <b className="text-primary">{soTick}</b>/{canXuly.length}</span>
                    <button className="h-9 px-4 rounded-lg bg-primary text-primary-foreground font-semibold text-sm flex items-center gap-2 hover:brightness-110 transition-all shadow-sm">
                      <Icon name="plus" className="w-4 h-4" /> Nạp {soTick} vào B-K149
                    </button>
                  </div>
                )}
              </div>

              {/* Cảnh báo nổi bật (NFR⑥) — chỉ ở nhóm Cần xử lý */}
              {napFilter === "canxuly" && (soLoi > 0 || soChinhTa > 0) && (
                <div className="px-4 py-3 space-y-2 border-b border-border shrink-0">
                  {soLoi > 0 && (
                    <Banner tone="error">
                      <b>{soLoi} hồ sơ nạp lỗi</b> (đánh dấu 🔴 bên dưới) — nguyên nhân ghi ngay trên từng dòng. Lô vẫn chạy hết các hồ sơ còn lại; sửa xong thì nạp lại riêng dòng lỗi.
                    </Banner>
                  )}
                  {soChinhTa > 0 && (
                    <Banner tone="warning">
                      <b>{soChinhTa} hồ sơ tên nghi sai chính tả</b> (mức A: thiếu dấu / ký tự lạ / khoảng trắng thừa) — kiểm lại họ tên trước khi nạp, hệ thống không chặn.
                    </Banner>
                  )}
                </div>
              )}

              {/* rows: chỉ cột này cuộn */}
              <div className="flex-1 overflow-y-auto min-h-0">
                {rows.map((r, i) => (
                  <div key={r.cccd} onClick={() => setSel(i)} className={"lrow flex items-center gap-3 px-4 py-3 " + (sel === i ? "sel" : "")}>
                    {r.tt === "cho"
                      ? <input type="checkbox" defaultChecked={r.tick} className="accent-primary w-4 h-4 shrink-0" onClick={(e) => e.stopPropagation()} />
                      : <span className="w-4 shrink-0" />}
                    <Avatar mau={r.mau} />
                    <div className="min-w-0 flex-1">
                      <div className="font-semibold text-[14px] truncate flex items-center gap-1.5">
                        {r.hoTen}
                        {r.chinhTa && <span className="inline-flex items-center gap-0.5 text-[10px] text-warning font-medium whitespace-nowrap" title={r.chinhTa}><Icon name="warn" className="w-3 h-3" /> nghi sai chính tả</span>}
                      </div>
                      <div className="text-[12px] text-muted-foreground truncate">{r.gioiTinh} · {r.cccd} · {r.noiTT}</div>
                      {r.loiLyDo && <div className="text-[11px] text-destructive font-medium truncate mt-0.5 flex items-center gap-1"><Icon name="warn" className="w-3 h-3 shrink-0" /> {r.loiLyDo}</div>}
                    </div>
                    <div className="flex items-center gap-1.5 shrink-0">
                      <NapBadge tt={r.tt} />
                      {r.tt === "cho" && <span className="hidden sm:flex items-center gap-1.5"><Chip kind={r.ttMap} /><Chip kind={r.ttAnh} /></span>}
                    </div>
                  </div>
                ))}
                {rows.length === 0 && (
                  <div className="px-4 py-10 text-center text-[13px] text-muted-foreground">Chưa có hồ sơ trong nhóm này.</div>
                )}
              </div>

              {/* footer tiến độ nạp lô */}
              <div className="px-4 py-2.5 border-t border-border shrink-0">
                <div className="flex justify-between text-[11px] text-muted-foreground mb-1">
                  <span>Tiến độ nạp lô (tuần tự, lỗi 1 HV không hỏng cả lô)</span>
                  <span>{daNap.length}/{hoSoChoNap.length}</span>
                </div>
                <div className="h-2 rounded-full bg-muted overflow-hidden">
                  <div className="h-full bg-success rounded-full" style={{ width: `${Math.round((daNap.length / hoSoChoNap.length) * 100)}%` }} />
                </div>
              </div>
            </div>

            {/* CỘT 2: THÔNG TIN */}
            <div className="w-full xl:w-[500px] shrink-0 border-b xl:border-b-0 xl:border-r border-border bg-muted/15 flex flex-col min-h-0">
              <div className="px-4 py-3 border-b border-border flex items-center justify-between shrink-0">
                <h3 className="text-sm font-bold">Thông tin học viên</h3>
                <span className="text-[11px] font-semibold text-primary bg-primary/10 rounded-full px-2 py-0.5">Chờ nạp</span>
              </div>
              <div className="flex-1 xl:overflow-y-auto p-4 space-y-3 min-h-0">
                <div className="rounded-md bg-secondary/70 border border-border px-2.5 py-2 text-[11px] text-muted-foreground leading-relaxed">
                  <b className="text-foreground">Tự điền khi nạp:</b> Số HS <b className="text-primary">056</b> · MaDK tự sinh · Hạng B/B1 · MaLoaiHs 2 · Quốc tịch VN · Tên in = Họ tên (≤25) · CM_VN · TT_XuLy <b className="text-foreground">03</b> (có ảnh)/<b className="text-foreground">01</b> (thiếu ảnh) · TrangThai 1 · CSDT 70004
                </div>

                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center gap-1.5 text-[11px] font-bold text-destructive"><span className="w-1.5 h-1.5 rounded-full bg-destructive" /> BẮT BUỘC</span>
                  <div className="flex-1 h-px bg-border" />
                  <span className="text-[10px] text-muted-foreground">* phải điền mới nạp được</span>
                </div>
                <div className="space-y-2 rounded-lg border border-destructive/25 bg-destructive/[0.03] p-3">
                  <div><label className="field-label">Họ và tên <span className="text-destructive">*</span> <span className="text-muted-foreground font-normal">(≤50, IN HOA)</span></label><input className="field-input mt-1" defaultValue="NGUYỄN THANH TÂM" /></div>
                  <div className="grid grid-cols-2 gap-2">
                    <div><label className="field-label">Ngày sinh <span className="text-destructive">*</span></label><input className="field-input mt-1" defaultValue="21/11/2002" /></div>
                    <div><label className="field-label">Giới tính <span className="text-destructive">*</span></label><select className="field-input mt-1" defaultValue="Nam"><option>Nam</option><option>Nữ</option></select></div>
                  </div>
                  <div><label className="field-label">Số CCCD <span className="text-destructive">*</span></label><input className="field-input mt-1" defaultValue="070202008455" /></div>
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <label className="field-label">Nơi thường trú — Tỉnh/Xã <span className="text-destructive">*</span></label>
                      <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-success bg-success/10 px-1.5 py-0.5 rounded-full border border-success/30"><Icon name="check" className="w-3 h-3" sw={3} /> {addrChip}</span>
                    </div>
                    <AddressCombo value="Xã Phú Nghĩa, Tỉnh Đồng Nai" onPick={(_, c, d) => setAddrChip(`Mã ${c}/${d}`)} />
                    <p className="text-[11px] text-muted-foreground mt-1">Gõ tên hoặc mã → chọn từ DB (DM_DVHC), lấy đúng mã — không gõ tay tự do.</p>
                  </div>
                  <label className="flex items-center gap-2 text-[12px] cursor-pointer"><input type="checkbox" checked={giongTT} onChange={(e) => setGiongTT(e.target.checked)} className="w-3.5 h-3.5 accent-primary" /> Nơi cư trú giống thường trú (BR-004)</label>
                  {!giongTT && (
                    <div><label className="field-label">Nơi cư trú — Tỉnh/Xã <span className="text-destructive">*</span></label><div className="mt-1"><AddressCombo value="" onPick={() => {}} /></div></div>
                  )}
                </div>

                <div className="rounded-lg border border-border overflow-hidden">
                  <button type="button" onClick={() => setOptOpen((v) => !v)} className="w-full flex items-center justify-between px-3 py-2.5 bg-muted/40 hover:bg-muted transition-colors text-left">
                    <span className="text-[13px] font-semibold flex items-center gap-2"><Icon name="plus" className="w-4 h-4 text-muted-foreground" /> Thông tin thêm <span className="font-normal text-muted-foreground text-[11px]">(không bắt buộc — bỏ qua được)</span></span>
                    <Icon name="chevronDown" className={"w-4 h-4 text-muted-foreground transition-transform " + (optOpen ? "rotate-180" : "")} />
                  </button>
                  {optOpen && (
                    <div className="p-3 space-y-2 border-t border-border bg-card">
                      <div className="grid grid-cols-2 gap-2">
                        <div><label className="field-label">Ngày cấp CCCD</label><input className="field-input mt-1" defaultValue="10/03/2021" placeholder="dd/mm/yyyy" /></div>
                        <div><label className="field-label">Nơi cấp CCCD</label><input className="field-input mt-1" placeholder="(có thể trống)" /></div>
                      </div>
                      <div><label className="field-label">Chi tiết địa chỉ (số nhà, thôn/ấp) <span className="text-muted-foreground font-normal">(gộp NoiTT ≤50)</span></label><input className="field-input mt-1" placeholder="VD: Số 12, Thôn 3" /></div>
                      <div><label className="field-label">Ghi chú</label><input className="field-input mt-1" placeholder="..." /></div>
                    </div>
                  )}
                </div>
              </div>
              <div className="p-3 border-t border-border shrink-0">
                <button className="w-full h-10 rounded-lg bg-primary text-primary-foreground font-semibold text-sm flex items-center justify-center gap-2 hover:brightness-110 transition-all shadow-sm">
                  <Icon name="plus" className="w-4 h-4" /> Nạp hồ sơ này vào B-K149
                </button>
              </div>
            </div>

            {/* CỘT 3: ẢNH */}
            <div className="w-full xl:w-[340px] shrink-0 bg-muted/5 p-4 flex flex-col">
              <h3 className="text-sm font-bold mb-1">Ảnh chân dung</h3>
              <p className="text-[11px] text-muted-foreground mb-3">3:4 · 353×471 · nền trắng (NAP-04)</p>
              <div className="aspect-[3/4] w-full max-w-[260px] mx-auto xl:max-w-none xl:mx-0 rounded-lg bg-white border border-input flex items-center justify-center relative overflow-hidden mb-3 shadow-sm">
                <Icon name="user" className="w-20 h-20 text-muted-foreground/40" sw={1.5} />
                <span className="absolute top-2 left-2 text-[10px] bg-success text-white px-1.5 py-0.5 rounded">Đã xử lý · nền trắng</span>
                <button onClick={() => setModal(true)} aria-label="Phóng to ảnh" className="absolute top-2 right-2 w-8 h-8 rounded-lg bg-foreground/60 text-white flex items-center justify-center hover:bg-foreground/80 transition-colors"><Icon name="expand" className="w-4 h-4" /></button>
              </div>
              <div className="space-y-2">
                <button onClick={() => setModal(true)} className="w-full h-10 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:brightness-110 transition-all shadow-sm flex items-center justify-center gap-2"><Icon name="expand" className="w-4 h-4" /> Chỉnh ảnh (phóng to)</button>
                <button className="w-full h-9 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors flex items-center justify-center gap-1.5"><Icon name="camera" className="w-4 h-4" /> Chọn / chụp ảnh khác</button>
              </div>
              <p className="text-[11px] text-muted-foreground mt-3">Tên file = MaDK, lưu vào <span className="font-mono">ANHCDUNG\B-K149\</span></p>
              <div className="mt-4 rounded-lg border border-border bg-card p-3">
                <h4 className="text-[13px] font-bold mb-2">Giấy tờ kèm theo <span className="font-normal text-muted-foreground text-[11px]">(theo tick cuối)</span></h4>
                <div className="space-y-1.5 text-[13px]">
                  {["Đơn đề nghị học, sát hạch (PL XI)", "Bản sao CMND/hộ chiếu", "Giấy chứng nhận sức khỏe"].map((g) => (
                    <label key={g} className="flex items-center gap-2 cursor-pointer"><input type="checkbox" defaultChecked className="w-4 h-4 accent-primary" /> {g}</label>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      {/* ============ CHẾ ĐỘ TRA CỨU DB ============ */}
      {mode === "tracuu" && (
        <>
          {/* Toolbar chọn khóa (mọi khóa, kể cả BC1) */}
          <div className="px-4 py-3 border-b border-border bg-muted/40 flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <label className="field-label whitespace-nowrap">Khóa</label>
              <KhoaCombo value={khoaTC} onPick={setKhoaTC} />
            </div>
            <div className="flex items-center gap-2 text-[12px]">
              <span className="inline-flex items-center gap-1 rounded-full bg-secondary px-2.5 py-1">Sĩ số <b className="text-foreground">{khoaTC.siSo}</b></span>
              {khoaTC.bc1
                ? <span className="inline-flex items-center gap-1 rounded-full bg-warning/10 text-warning px-2.5 py-1 font-semibold border border-warning/30"><Icon name="lock" className="w-3.5 h-3.5" /> Đã BC1 · chỉ xem</span>
                : <span className="inline-flex items-center gap-1 rounded-full bg-success/10 text-success px-2.5 py-1 font-semibold border border-success/30"><Icon name="check" className="w-3.5 h-3.5" sw={3} /> Chưa BC1 · được sửa</span>}
            </div>
            <div className="ml-auto relative">
              <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground"><Icon name="search" className="w-4 h-4" /></span>
              <input className="field-input pl-8" style={{ width: 220 }} placeholder="Tìm học viên: tên / CCCD / số HS" />
            </div>
          </div>

          {khoaTC.bc1 && (
            <div className="px-4 pt-3">
              <Banner tone="warning">
                <b>Khóa {khoaTC.ten} đã lập BC1</b> → chỉ xem, không sửa / đổi khóa / xóa học viên (BR-012). Mở một học viên vẫn xem được đầy đủ thông tin.
              </Banner>
            </div>
          )}

          <div className="flex flex-col xl:flex-row xl:h-[680px]">
            {/* list học viên trong khóa */}
            <div className="flex-1 min-w-0 border-b xl:border-b-0 xl:border-r border-border flex flex-col min-h-0">
              <div className="px-4 py-3 flex items-center justify-between border-b border-border shrink-0">
                <h3 className="text-sm font-bold flex items-center gap-2"><Icon name="db" className="w-4 h-4 text-primary" /> Học viên trong khóa {khoaTC.ten}</h3>
                <span className="text-[12px] text-muted-foreground">{hocVienTrongKhoa.length} hiển thị · {khoaTC.siSo} tổng</span>
              </div>
              <div className="flex-1 overflow-y-auto min-h-0">
                {hocVienTrongKhoa.map((r) => (
                  <div key={r.soHS} onClick={() => setSelDb(r)} className={"lrow flex items-center gap-3 px-4 py-3 " + (selDb?.soHS === r.soHS ? "sel" : "")}>
                    <span className="inline-flex items-center justify-center min-w-[42px] h-6 rounded-md bg-secondary text-[12px] font-bold tabular-nums shrink-0">{r.soHS}</span>
                    <div className="min-w-0 flex-1">
                      <div className="font-semibold text-[14px] truncate">{r.hoTen}</div>
                      <div className="text-[12px] text-muted-foreground truncate">{r.gioiTinh} · {r.cccd} · {r.noiTT}</div>
                    </div>
                    <span className="text-[11px] text-success shrink-0" title="Đường dẫn ảnh"><Icon name="image" className="w-3.5 h-3.5" /></span>
                    <Icon name="chevronRight" className="w-4 h-4 text-muted-foreground shrink-0" />
                  </div>
                ))}
              </div>
              <div className="px-4 py-2.5 border-t border-border shrink-0 flex items-center justify-between text-[12px] text-muted-foreground">
                <span>Khóa {khoaTC.ten} · trang 1/3 · 20/trang</span>
                <div className="flex items-center gap-1">
                  <button className="w-8 h-8 rounded-md border border-border flex items-center justify-center" disabled><Icon name="chevronLeft" className="w-4 h-4" /></button>
                  <button className="w-8 h-8 rounded-md bg-primary text-primary-foreground font-semibold">1</button>
                  <button className="w-8 h-8 rounded-md border border-border hover:bg-muted transition-colors">2</button>
                  <button className="w-8 h-8 rounded-md border border-border hover:bg-muted transition-colors">3</button>
                  <button className="w-8 h-8 rounded-md border border-border hover:bg-muted flex items-center justify-center transition-colors"><Icon name="chevronRight" className="w-4 h-4" /></button>
                </div>
              </div>
            </div>

            {/* panel phụ: hướng dẫn + chú thích */}
            <div className="w-full xl:w-[380px] shrink-0 bg-muted/15 p-4 space-y-3">
              <div className="rounded-lg border border-border bg-card p-4">
                <h3 className="text-sm font-bold mb-1">Khóa {khoaTC.ten}</h3>
                <div className="text-[12px] text-muted-foreground space-y-1">
                  <div>Mã khóa: <span className="font-mono text-foreground">{khoaTC.ma}</span></div>
                  <div>Khai giảng: <b className="text-foreground">{khoaTC.kg}</b></div>
                  <div>Sĩ số: <b className="text-foreground">{khoaTC.siSo}</b> học viên</div>
                  <div>Loại: <b className="text-foreground">{khoaTC.loai === "oto" ? "Ô tô" : "Mô tô"}</b></div>
                </div>
              </div>
              <div className="rounded-lg border border-border bg-card p-4 text-[12px] text-muted-foreground leading-relaxed">
                <Icon name="edit" className="w-5 h-5 text-primary mb-1.5" />
                Bấm một học viên để mở ô <b className="text-foreground">Xem / Sửa</b> bên phải.
                {khoaTC.bc1
                  ? <> Khóa này <b className="text-warning">đã BC1</b> nên thông tin <b className="text-foreground">chỉ xem</b>.</>
                  : <> Khóa chưa BC1 nên được sửa, đổi khóa cùng hạng, hoặc xóa (BR-012/013/014).</>}
              </div>
            </div>
          </div>
        </>
      )}

      {/* MODAL chỉnh ảnh */}
      {modal && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4" onClick={(e) => { if (e.target === e.currentTarget) setModal(false); }}>
          <div className="bg-card rounded-xl shadow-2xl w-full max-w-3xl max-h-[92vh] flex flex-col overflow-hidden">
            <div className="flex items-center justify-between px-5 py-3 border-b border-border shrink-0">
              <h3 className="font-bold text-sm flex items-center gap-2"><Icon name="camera" className="w-4 h-4 text-primary" /> Chỉnh ảnh chân dung — NGUYỄN THANH TÂM</h3>
              <button onClick={() => setModal(false)} aria-label="Đóng" className="w-8 h-8 rounded-lg hover:bg-muted flex items-center justify-center transition-colors"><Icon name="x" className="w-5 h-5" /></button>
            </div>
            <div className="p-5 grid grid-cols-1 md:grid-cols-2 gap-6 overflow-y-auto">
              <div>
                <div className="field-label mb-2">Ảnh gốc — kéo để canh mặt, khung 3:4 cố định</div>
                <div className="relative aspect-[3/4] rounded-lg bg-slate-800 overflow-hidden flex items-center justify-center cursor-move select-none">
                  <div className="absolute inset-0" style={{ background: "radial-gradient(circle at 50% 42%, #334155, #0f172a)" }} />
                  <Icon name="user" className="w-40 h-40 text-white/25 relative" sw={1.2} />
                  <div className="absolute inset-x-5 inset-y-3 border-2 border-white/85 rounded pointer-events-none">
                    <span className="absolute -top-0.5 -left-0.5 w-5 h-5 border-t-4 border-l-4 border-primary rounded-tl" />
                    <span className="absolute -top-0.5 -right-0.5 w-5 h-5 border-t-4 border-r-4 border-primary rounded-tr" />
                    <span className="absolute -bottom-0.5 -left-0.5 w-5 h-5 border-b-4 border-l-4 border-primary rounded-bl" />
                    <span className="absolute -bottom-0.5 -right-0.5 w-5 h-5 border-b-4 border-r-4 border-primary rounded-br" />
                  </div>
                  <span className="absolute bottom-2 left-1/2 -translate-x-1/2 text-[11px] text-white/70 bg-black/40 px-2 py-1 rounded-full whitespace-nowrap">Kéo ảnh để di chuyển · cuộn/kéo thanh để phóng</span>
                </div>
                <div className="mt-3"><label className="field-label">Thu phóng</label><input type="range" min={100} max={260} defaultValue={135} className="w-full accent-primary mt-1" /></div>
                <button className="mt-2 w-full h-9 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors flex items-center justify-center gap-1.5"><Icon name="camera" className="w-4 h-4" /> Chọn / chụp ảnh khác</button>
              </div>
              <div>
                <div className="field-label mb-2">Kết quả (3:4 · 353×471 · nền trắng)</div>
                <div className="aspect-[3/4] rounded-lg bg-white border border-border flex items-center justify-center shadow-inner"><Icon name="user" className="w-40 h-40 text-slate-300" sw={1.2} /></div>
                <label className="flex items-center gap-2 mt-3 text-[13px] font-medium cursor-pointer"><input type="checkbox" defaultChecked className="w-4 h-4 accent-primary" /> Xóa phông → nền trắng (rembg)</label>
                <p className="text-[11px] text-muted-foreground mt-2 leading-relaxed">Nền tách bằng rembg, xuất <b>.jp2</b> (353×471) khi bấm Nạp. Tên file = MaDK, lưu vào <span className="font-mono">ANHCDUNG\B-K149\</span></p>
              </div>
            </div>
            <div className="px-5 py-3 border-t border-border flex justify-end gap-2 shrink-0">
              <button onClick={() => setModal(false)} className="h-10 px-4 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors">Hủy</button>
              <button onClick={() => setModal(false)} className="h-10 px-5 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:brightness-110 transition-all shadow-sm flex items-center gap-2"><Icon name="check" className="w-4 h-4" sw={3} /> Lưu ảnh</button>
            </div>
          </div>
        </div>
      )}

      {/* QLY-01: Drawer Xem/Sửa học viên từ DB (chế độ Tra cứu) */}
      {selDb && (
        <div className="fixed inset-0 z-50 bg-black/60 flex justify-end" onClick={(e) => { if (e.target === e.currentTarget) setSelDb(null); }}>
          <div className="bg-card w-full sm:max-w-md h-full flex flex-col shadow-2xl">
            <div className="flex items-center justify-between px-5 py-3 border-b border-border shrink-0">
              <div>
                <h3 className="font-bold text-sm flex items-center gap-2"><Icon name={khoaTC.bc1 ? "search" : "edit"} className="w-4 h-4 text-primary" /> {khoaTC.bc1 ? "Xem học viên" : "Xem / Sửa học viên"}</h3>
                <p className="text-[11px] text-muted-foreground mt-0.5">Số hồ sơ {selDb.soHS} · khóa {khoaTC.ten} · QLY-01</p>
              </div>
              <button onClick={() => setSelDb(null)} aria-label="Đóng" className="w-8 h-8 rounded-lg hover:bg-muted flex items-center justify-center transition-colors"><Icon name="x" className="w-5 h-5" /></button>
            </div>
            <div className="flex-1 overflow-y-auto p-5 space-y-3">
              {khoaTC.bc1 ? (
                <div className="flex items-center gap-2 text-[12px] text-warning bg-warning/10 border border-warning/40 border-l-4 border-l-warning rounded-lg px-3 py-2">
                  <Icon name="lock" className="w-4 h-4 shrink-0" /> Khóa {khoaTC.ten} đã lập BC1 → chỉ xem, không sửa (BR-012).
                </div>
              ) : (
                <div className="flex items-center gap-2 text-[12px] text-success bg-success/10 border border-success/30 rounded-lg px-3 py-2">
                  <Icon name="check" className="w-4 h-4 shrink-0" sw={3} /> Khóa {khoaTC.ten} chưa lập BC1 → được sửa (BR-012).
                </div>
              )}
              <div className="flex items-start gap-4">
                <div className="w-24 aspect-[3/4] rounded-lg bg-slate-100 border border-border flex items-center justify-center shrink-0 relative">
                  <Icon name="user" className="w-12 h-12 text-slate-300" sw={1.5} />
                  {!khoaTC.bc1 && <button onClick={() => setModal(true)} className="absolute bottom-1.5 left-1/2 -translate-x-1/2 text-[10px] bg-primary text-white px-2 py-0.5 rounded-full hover:brightness-110 transition-all">Chỉnh ảnh</button>}
                </div>
                <div className="min-w-0 flex-1"><div className="font-bold text-[15px]">{selDb.hoTen}</div><div className="text-[12px] text-muted-foreground mt-1">{selDb.gioiTinh} · {selDb.cccd}</div></div>
              </div>
              <div><label className="field-label">Họ và tên</label><input className="field-input mt-1" defaultValue={selDb.hoTen} readOnly={khoaTC.bc1} /></div>
              <div className="grid grid-cols-2 gap-2">
                <div><label className="field-label">Số hồ sơ</label><input className="field-input mt-1" defaultValue={selDb.soHS} readOnly /></div>
                <div><label className="field-label">Giới tính</label><select className="field-input mt-1" defaultValue={selDb.gioiTinh} disabled={khoaTC.bc1}><option>Nam</option><option>Nữ</option></select></div>
              </div>
              <div><label className="field-label">CMT/HC</label><input className="field-input mt-1" defaultValue={selDb.cccd} readOnly={khoaTC.bc1} /></div>
              <div><label className="field-label">Nơi thường trú</label><div className="mt-1"><AddressCombo value={selDb.noiTT} onPick={() => {}} /></div></div>
            </div>
            <div className="p-3 border-t border-border shrink-0 flex items-center gap-2">
              {khoaTC.bc1 ? (
                <button onClick={() => setSelDb(null)} className="ml-auto h-10 px-5 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:brightness-110 transition-all shadow-sm">Đóng</button>
              ) : (
                <>
                  <button onClick={() => setDoiKhoa(true)} className="inline-flex items-center gap-1.5 h-10 px-3 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors"><Icon name="refresh" className="w-4 h-4" /> Đổi khóa</button>
                  <button onClick={() => setXoaHV(true)} className="inline-flex items-center gap-1.5 h-10 px-3 rounded-lg border border-destructive/30 text-destructive text-sm font-medium hover:bg-destructive/10 transition-colors"><Icon name="warn" className="w-4 h-4" /> Xóa</button>
                  <button onClick={() => setSelDb(null)} className="ml-auto h-10 px-5 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:brightness-110 transition-all shadow-sm flex items-center gap-2"><Icon name="check" className="w-4 h-4" sw={3} /> Lưu</button>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* QLY-02: Đổi khóa */}
      {doiKhoa && selDb && (
        <div className="fixed inset-0 z-[60] bg-black/60 flex items-center justify-center p-4" onClick={(e) => { if (e.target === e.currentTarget) setDoiKhoa(false); }}>
          <div className="bg-card rounded-xl shadow-2xl w-full max-w-sm p-5">
            <h3 className="font-bold text-sm">Đổi khóa cho {selDb.hoTen}</h3>
            <p className="text-[12px] text-muted-foreground mt-1 mb-3">QLY-02 · chọn khóa đích <b>cùng hạng</b>.</p>
            <label className="field-label">Khóa đích</label>
            <select className="field-input mt-1">{khoaOto.map((k) => <option key={k}>{k}</option>)}</select>
            <p className="text-[11px] text-muted-foreground mt-2">Đổi khóa cùng hạng → sinh lại Số hồ sơ theo khóa mới + di chuyển file .jp2 sang folder khóa mới (giữ MaDK). Khác hạng → hướng xóa tạo lại (BR-013).</p>
            <div className="flex justify-end gap-2 mt-5">
              <button onClick={() => setDoiKhoa(false)} className="h-10 px-4 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors">Hủy</button>
              <button onClick={() => setDoiKhoa(false)} className="h-10 px-5 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:brightness-110 transition-all">Xác nhận đổi</button>
            </div>
          </div>
        </div>
      )}

      {/* QLY-03: Xóa HV */}
      {xoaHV && selDb && (
        <div className="fixed inset-0 z-[60] bg-black/60 flex items-center justify-center p-4" onClick={(e) => { if (e.target === e.currentTarget) setXoaHV(false); }}>
          <div className="bg-card rounded-xl shadow-2xl w-full max-w-sm p-5">
            <div className="flex items-start gap-3">
              <span className="w-11 h-11 rounded-full bg-destructive/10 text-destructive flex items-center justify-center shrink-0"><Icon name="warn" className="w-6 h-6" /></span>
              <div>
                <h3 className="font-bold text-sm">Xóa học viên {selDb.hoTen}?</h3>
                <p className="text-[13px] text-muted-foreground mt-1">Xóa hồ sơ + giấy tờ (cascade 3 bảng); ảnh <b>.jp2</b> chuyển sang <span className="font-mono">_DELETED</span> (xóa mềm, BR-014). Học viên đã có GPLX sẽ bị FK chặn.</p>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-5">
              <button onClick={() => setXoaHV(false)} className="h-10 px-4 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors">Hủy</button>
              <button onClick={() => { setXoaHV(false); setSelDb(null); }} className="h-10 px-5 rounded-lg bg-destructive text-white text-sm font-semibold hover:brightness-110 transition-all">Xóa</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
