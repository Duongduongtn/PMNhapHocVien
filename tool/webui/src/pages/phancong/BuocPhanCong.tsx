import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Icon } from "../../components/Icon";
import { ymdToVN } from "../../lib/format";
import { kiemTraPC, type BanNhapPC, type GiaoVienPC, type KhoaPC, type MonPC, type PcDong, type VanDePC } from "../../lib/api";
import { HuyHieu } from "./BuocGiaoVien";

// PCG-02 — Bước ② phân công dạy: từng giáo viên + hàng loạt. Bám ui-mock/phancong.html (stepPC/renderEdit).
// Luật kiểm do SERVER quyết (POST /kiem-tra); khung nhập chỉ hỏi server về dòng đang soạn.
// Thời gian lưu dạng "YYYY-MM-DDTHH:mm"; không chỉnh giờ = 00:00 → 00:00 ("Theo ngày").

const MON_TH = 6;
const GIO: string[] = Array.from({ length: 48 }, (_, i) => `${String(Math.floor(i / 2)).padStart(2, "0")}:${i % 2 ? "30" : "00"}`);

const dP = (s: string) => s.slice(0, 10);
const tP = (s: string) => s.slice(11, 16) || "00:00";
const mk = (d: string, t = "00:00") => `${d}T${t}`;
function addDays(ymd: string, n: number): string {
  const d = new Date(`${ymd}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}
const soNgay = (tu: string, den: string) => Math.round((Date.parse(`${dP(den)}T00:00:00Z`) - Date.parse(`${dP(tu)}T00:00:00Z`)) / 86400000);

function fmtKhoang(tu: string, den: string): string {
  if (!tu || !den) return "chưa chọn thời gian";
  const coGio = tP(tu) !== "00:00" || tP(den) !== "00:00";
  if (!coGio) return `${ymdToVN(dP(tu))} → ${ymdToVN(dP(den))}`;
  if (dP(tu) === dP(den)) return `${ymdToVN(dP(tu))} ${tP(tu)} → ${tP(den)}`;
  return `${ymdToVN(dP(tu))} ${tP(tu)} → ${ymdToVN(dP(den))} ${tP(den)}`;
}

function Hop({ tieuDe, children, chan, dong, rong = "max-w-[680px]" }: { tieuDe: string; children: ReactNode; chan: ReactNode; dong: () => void; rong?: string }) {
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center p-4 bg-black/40" role="dialog" aria-modal="true" aria-label={tieuDe}>
      <div className={`w-full ${rong} max-h-[90vh] flex flex-col rounded-lg bg-card border border-border shadow-xl`}>
        <div className="px-5 py-3 border-b border-border flex items-center">
          <h3 className="text-[15px] font-semibold">{tieuDe}</h3>
          <button onClick={dong} aria-label="Đóng" className="ml-auto w-8 h-8 rounded-md hover:bg-muted inline-flex items-center justify-center">
            <Icon name="x" className="w-4 h-4" />
          </button>
        </div>
        <div className="px-5 py-4 overflow-auto space-y-3.5 text-[13.5px]">{children}</div>
        <div className="px-5 py-3 border-t border-border flex items-center gap-2 justify-end">{chan}</div>
      </div>
    </div>
  );
}

const lopMuc = (m: string) =>
  m === "chan" ? "border-destructive bg-destructive/5" : m === "canh_bao" ? "border-warning bg-warning/10" : "border-primary bg-primary/5";

function ThongBao({ v }: { v: VanDePC }) {
  return <div className={`rounded-md border-l-4 px-2.5 py-1.5 text-[13px] ${lopMuc(v.muc)}`}>{v.noi_dung}</div>;
}

interface Soan {
  id: number | string | null; // null/"tam" = dòng mới
  ma: string;
  batch: string[] | null; // phân công cùng môn + thời gian cho nhiều GV
  mon: number[];
  tuD: string;
  denD: string;
  gio: boolean;
  tuT: string;
  denT: string;
}

/** Hộp xem trước hàng loạt: mỗi GV 1 dòng (hợp lệ / cảnh báo / bỏ qua kèm lý do); lỗi 1 GV không chặn cả lô. */
function HopHangLoat({
  tieuDe, mota, cands, thay, kiemFn, tenGv, nhanApDung, dong, apDung,
}: {
  tieuDe: string;
  mota: ReactNode;
  cands: PcDong[];
  thay: string[];
  kiemFn: (cands: PcDong[], thay: string[]) => Promise<VanDePC[]>;
  tenGv: (ma: string) => string;
  nhanApDung: (n: number) => string;
  dong: () => void;
  apDung: (ok: PcDong[]) => void;
}) {
  const [vd, setVd] = useState<VanDePC[] | null>(null);
  const [busy, setBusy] = useState(false);
  const khoaCands = JSON.stringify(cands);
  useEffect(() => {
    if (cands.length === 0) { setVd([]); return; }
    let huy = false;
    setBusy(true);
    const h = setTimeout(() => {
      kiemFn(cands, thay)
        .then((r) => { if (!huy) setVd(r); })
        .catch(() => { if (!huy) setVd(null); })
        .finally(() => { if (!huy) setBusy(false); });
    }, 200);
    return () => { huy = true; clearTimeout(h); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [khoaCands, thay.join()]);

  const theoGv = new Map<string, PcDong[]>();
  for (const c of cands) theoGv.set(c.ma, [...(theoGv.get(c.ma) ?? []), c]);
  const dong1 = [...theoGv].map(([ma, cs]) => {
    const ids = new Set(cs.map((c) => `pc-${c.id}`));
    const vs = (vd ?? []).filter((v) => ids.has(v.ref));
    return { ma, cs, vs, chan: vs.some((v) => v.muc === "chan"), canh: vs.some((v) => v.muc === "canh_bao") };
  });
  const ok = dong1.filter((d) => !d.chan).flatMap((d) => d.cs);
  const nGv = dong1.filter((d) => !d.chan).length;

  return (
    <Hop
      tieuDe={tieuDe}
      dong={dong}
      chan={<>
        <button onClick={dong} className="h-9 px-4 rounded-md border border-border text-[13px]">Hủy</button>
        <button disabled={busy || vd === null || nGv === 0} onClick={() => apDung(ok)}
          className="h-9 px-4 rounded-md bg-pc text-white text-[13px] font-semibold disabled:opacity-40">
          {nhanApDung(nGv)}
        </button>
      </>}
    >
      <div>{mota}</div>
      {cands.length === 0 ? (
        <div className="text-[13px] text-muted-foreground">Chưa có gì để áp dụng — kiểm tra lại lựa chọn.</div>
      ) : (
        <ul className="rounded-lg border border-border divide-y divide-border/60 max-h-64 overflow-auto">
          {dong1.map((d) => (
            <li key={d.ma} className="px-3 py-2">
              <div className="flex items-center gap-2 text-[13.5px]">
                <Icon name={d.chan ? "x" : d.canh ? "warn" : "check"} className={"w-[18px] h-[18px] " + (d.chan ? "text-destructive" : d.canh ? "text-warning" : "text-success")} />
                <b>{tenGv(d.ma)}</b>
                <span className={"ml-auto text-[12.5px] " + (d.chan ? "text-destructive" : d.canh ? "text-warning" : "text-success")}>
                  {busy ? "Đang kiểm…" : d.chan ? "Bỏ qua" : d.canh ? "Có cảnh báo" : "Hợp lệ"}
                </span>
              </div>
              {d.vs.map((v, i) => <div key={i} className="mt-1 ml-6"><ThongBao v={v} /></div>)}
            </li>
          ))}
        </ul>
      )}
      <div className="text-[12.5px] text-muted-foreground">GV có lỗi chặn bị bỏ qua (làm riêng sau); không chặn cả lô.</div>
    </Hop>
  );
}

export default function BuocPhanCong({
  khoa, danhMuc, mon, ban, setBan, vande, targetKey, thStart, setThStart,
}: {
  khoa: KhoaPC;
  danhMuc: GiaoVienPC[];
  mon: MonPC[];
  ban: BanNhapPC;
  setBan: (f: (b: BanNhapPC) => BanNhapPC) => void;
  vande: VanDePC[];
  targetKey: string;
  thStart: string;
  setThStart: (v: string) => void;
}) {
  const theoMa = useMemo(() => new Map(danhMuc.map((g) => [g.ma, g])), [danhMuc]);
  const tenMon = useMemo(() => new Map(mon.map((m) => [m.id, m.ten])), [mon]);
  const monTen = (ids: number[]) => ids.map((i) => tenMon.get(i) ?? `môn ${i}`).join(" + ") || "chưa chọn môn";
  const [soan, setSoan] = useState<Soan | null>(null);
  const [xoa, setXoa] = useState<PcDong | null>(null);
  const [doiNgay, setDoiNgay] = useState<{ cu: string; moi: string; n: number } | null>(null);
  const [chon, setChon] = useState<string[]>([]);
  const [hl, setHl] = useState<"th" | "doi" | null>(null);
  const [ngayDoi, setNgayDoi] = useState("");
  const [kiem, setKiem] = useState<VanDePC[] | null>(null);
  const [dangKiem, setDangKiem] = useState(false);
  const seq = useRef(0);
  const dem = useRef(0);

  const trongKhoa = useMemo(() => new Set(ban.gv_khoa), [ban.gv_khoa]);
  const mo = ban.pc;
  const ngoaiDs = useMemo(() => [...new Set(mo.map((p) => p.ma))].filter((m) => !trongKhoa.has(m)), [mo, trongKhoa]);
  const hang = [...ngoaiDs, ...ban.gv_khoa];
  const thieuNgayTh = !thStart;
  const chuaTH = ban.gv_khoa.filter((ma) => theoMa.get(ma)?.loai === "TH" && !ban.pc.some((p) => p.ma === ma));
  const thCuaChon = ban.pc.filter((p) => chon.includes(p.ma) && p.mon.includes(MON_TH));

  // Dòng đang soạn (hoặc cả lô) → bản nháp giả định gửi /kiem-tra để lấy lỗi riêng từng dòng đó.
  const idSoan = soan ? String(soan.id ?? "tam") : "";
  const tu = soan && soan.tuD ? mk(soan.tuD, soan.gio ? soan.tuT : "00:00") : "";
  const den = soan && soan.denD ? mk(soan.denD, soan.gio ? soan.denT : "00:00") : "";
  const idLo = (ma: string) => `b-${ma}`;
  useEffect(() => {
    if (!soan) { setKiem(null); return; }
    if (soan.batch && (!tu || !den)) { setKiem([]); return; }
    const s = ++seq.current;
    setDangKiem(true);
    const h = setTimeout(() => {
      const cands: PcDong[] = soan.batch
        ? soan.batch.map((ma) => ({ id: idLo(ma), ma, mon: soan.mon, tu, den }))
        : [{ id: idSoan, ma: soan.ma, mon: soan.mon, tu, den }];
      const thay = new Set(soan.batch ? [] : [idSoan]);
      const pc = [...ban.pc.filter((p) => !thay.has(String(p.id))), ...cands];
      const gv_khoa = soan.batch || ban.gv_khoa.includes(soan.ma) ? ban.gv_khoa : [...ban.gv_khoa, soan.ma];
      const refs = new Set(cands.map((c) => `pc-${c.id}`));
      kiemTraPC(khoa.ma_kh, { ...ban, gv_khoa, pc }, targetKey)
        .then((r) => { if (s === seq.current) setKiem(r.vande.filter((v) => refs.has(v.ref))); })
        .catch(() => { if (s === seq.current) setKiem(null); })
        .finally(() => { if (s === seq.current) setDangKiem(false); });
    }, 250);
    return () => clearTimeout(h);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [soan, tu, den, idSoan]);

  const gvLoOk = (ma: string) => !(kiem ?? []).some((v) => v.ref === `pc-${idLo(ma)}` && v.muc === "chan");
  const okLo = soan?.batch ? soan.batch.filter(gvLoOk) : [];
  const coChan = soan?.batch
    ? !!tu && !!den && soan.mon.length > 0 && okLo.length === 0
    : (kiem ?? []).some((v) => v.muc === "chan");

  function moSoan(p?: PcDong, ma?: string) {
    if (p) {
      setSoan({
        id: p.id, ma: p.ma, batch: null, mon: [...p.mon], tuD: dP(p.tu), denD: dP(p.den),
        gio: tP(p.tu) !== "00:00" || tP(p.den) !== "00:00",
        tuT: tP(p.tu) === "00:00" ? "07:30" : tP(p.tu), denT: tP(p.den) === "00:00" ? "17:30" : tP(p.den),
      });
    } else {
      setSoan({ id: null, ma: ma ?? "", batch: null, mon: [], tuD: "", denD: "", gio: false, tuT: "07:30", denT: "11:30" });
    }
  }
  function moHangLoat() {
    setSoan({ id: null, ma: "", batch: [...chon], mon: [], tuD: "", denD: "", gio: false, tuT: "07:30", denT: "11:30" });
  }

  function luu() {
    if (!soan || coChan || !tu || !den) return;
    if (soan.batch) {
      const moi = okLo.map((ma) => ({ id: `n${Date.now().toString(36)}${++dem.current}`, ma, mon: soan.mon, tu, den }));
      setBan((b) => ({ ...b, pc: [...b.pc, ...moi] }));
      setChon([]);
      setSoan(null);
      return;
    }
    const dong: PcDong = { id: soan.id ?? `n${Date.now().toString(36)}${++dem.current}`, ma: soan.ma, mon: soan.mon, tu, den };
    setBan((b) => ({
      ...b,
      pc: soan.id !== null ? b.pc.map((p) => (String(p.id) === String(soan.id) ? dong : p)) : [...b.pc, dong],
    }));
    setSoan(null);
  }

  function pickTH() {
    if (!soan || !thStart) return;
    if (soan.mon.includes(MON_TH)) setSoan({ ...soan, mon: soan.mon.filter((m) => m !== MON_TH) });
    else setSoan({ ...soan, mon: [MON_TH], tuD: thStart, denD: khoa.bg, gio: false });
  }
  function togMon(id: number) {
    if (!soan) return;
    setSoan({ ...soan, mon: soan.mon.includes(id) ? soan.mon.filter((m) => m !== id) : [...soan.mon.filter((m) => m !== MON_TH), id] });
  }
  function noiTiep() {
    if (!soan) return;
    const truoc = ban.pc.filter((p) => p.ma === soan.ma && String(p.id) !== String(soan.id)).map((p) => p.den).sort().pop();
    if (!truoc) return;
    const tuD = dP(truoc);
    setSoan({ ...soan, tuD, gio: false, denD: !soan.denD || soan.denD <= tuD ? addDays(tuD, 2) : soan.denD });
  }
  const coTruoc = !!soan && ban.pc.some((p) => p.ma === soan.ma && String(p.id) !== String(soan.id));

  function doiThStart(v: string) {
    const cu = thStart;
    const n = cu && v && v !== cu
      ? ban.pc.filter((p) => p.mon.length === 1 && p.mon[0] === MON_TH && dP(p.tu) === cu && tP(p.tu) === "00:00").length
      : 0;
    if (n > 0) setDoiNgay({ cu, moi: v, n });
    else setThStart(v);
  }
  function apDungDoiNgay() {
    if (!doiNgay) return;
    setBan((b) => ({
      ...b,
      pc: b.pc.map((p) =>
        p.mon.length === 1 && p.mon[0] === MON_TH && dP(p.tu) === doiNgay.cu && tP(p.tu) === "00:00" ? { ...p, tu: mk(doiNgay.moi) } : p),
    }));
    setThStart(doiNgay.moi);
    setDoiNgay(null);
  }

  function xoaPc(p: PcDong) {
    const lastTH = p.mon.includes(MON_TH) && ban.pc.filter((q) => q.ma === p.ma && q.mon.includes(MON_TH)).length === 1;
    setBan((b) => ({
      ...b,
      pc: b.pc.filter((q) => String(q.id) !== String(p.id)),
      ghep: lastTH ? b.ghep.filter((m) => m.ma !== p.ma) : b.ghep,
    }));
    setXoa(null);
  }
  const xoaLaThCuoi = (p: PcDong) =>
    p.mon.includes(MON_TH) && ban.pc.filter((q) => q.ma === p.ma && q.mon.includes(MON_TH)).length === 1 && ban.ghep.some((m) => m.ma === p.ma);

  // Kiểm cả lô: dòng ứng viên thay thế/bổ sung vào bản nháp, trả lỗi theo ref pc-<id> của ứng viên.
  const kiemHL = (cands: PcDong[], thay: string[]) =>
    kiemTraPC(
      khoa.ma_kh,
      { ...ban, pc: [...ban.pc.filter((p) => !thay.includes(String(p.id))), ...cands] },
      targetKey,
    ).then((r) => r.vande);

  const loiCuaPc = (id: number | string | null) => vande.filter((v) => v.ref === `pc-${id}`);
  const gioLe = soan && soan.gio && (!GIO.includes(soan.tuT) || !GIO.includes(soan.denT));
  const nhieuNgayCoGio = !!soan && soan.gio && soan.tuD && soan.denD && soan.tuD !== soan.denD;

  return (
    <div>
      {/* Ngày bắt đầu thực hành của khóa */}
      <div className={`mb-3 rounded-lg border px-3.5 py-3 flex items-center gap-3 flex-wrap ${thieuNgayTh ? "border-pc bg-pc-soft" : "border-border bg-card"}`}>
        <div>
          <div className={`text-[13.5px] font-bold ${thieuNgayTh ? "text-pc" : ""}`}>
            Ngày bắt đầu thực hành của khóa {thieuNgayTh && <span className="text-destructive">*</span>}
          </div>
          <div className="text-[12px] text-muted-foreground">
            Là ngày GV thực hành bắt đầu ra sân — <b>không phải</b> thời gian dạy lý thuyết. Nhập 1 lần, dùng cho nút “Thực hành lái xe”.
          </div>
        </div>
        <input
          type="date"
          aria-label="Ngày bắt đầu thực hành của khóa"
          value={thStart}
          min={addDays(khoa.kg, 1)}
          max={addDays(khoa.bg, -1)}
          onChange={(e) => doiThStart(e.target.value)}
          className={`ml-auto h-10 w-[170px] rounded-md border bg-background px-2 text-sm ${thieuNgayTh ? "border-pc" : "border-border"}`}
        />
        {chuaTH.length > 0 && (
          <button
            disabled={thieuNgayTh}
            onClick={() => setHl("th")}
            title={thieuNgayTh ? "Nhập ngày bắt đầu thực hành trước" : ""}
            className="h-10 px-3.5 rounded-lg bg-pc text-white text-[13px] font-semibold disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Áp “Thực hành lái xe” cho {chuaTH.length} GV TH chưa có
          </button>
        )}
      </div>

      {chon.length > 0 && (
        <div className="mb-3 rounded-lg border border-pc-border bg-pc-soft px-3 py-2.5 flex items-center gap-2 flex-wrap text-[13.5px]">
          <b>Đã chọn {chon.length} GV:</b>
          <button onClick={moHangLoat} className="h-9 px-3 rounded-lg bg-pc text-white font-semibold text-[13px]">Phân công cho {chon.length} GV</button>
          <button
            onClick={() => { setNgayDoi(addDays(khoa.bg, -1)); setHl("doi"); }}
            className="h-9 px-3 rounded-lg border border-pc-border text-pc font-semibold text-[13px] bg-white"
          >
            Dời ngày kết thúc thực hành
          </button>
          <button onClick={() => setChon([])} className="ml-auto text-[12.5px] text-muted-foreground underline">Bỏ chọn</button>
        </div>
      )}

      <p className="mb-2 text-[12.5px] text-muted-foreground">
        Mỗi giáo viên có thể có <b>nhiều phân công</b> (khác môn hoặc khác ngày): bấm <b>+</b> để thêm một phân công nữa, bấm biểu tượng bút trên phân công để sửa. Mọi thay đổi chỉ nằm trên màn hình cho tới khi bạn bấm <b>Ghi vào CDB</b>.
      </p>
      <div className="flex items-center gap-3 mb-2 text-[12.5px] text-muted-foreground flex-wrap">
        <span className="inline-flex items-center gap-1.5"><span className="inline-block w-3.5 h-3.5 rounded border-2 border-pc bg-pc-soft" /> Thực hành lái xe</span>
        <span className="inline-flex items-center gap-1.5"><span className="inline-block w-3.5 h-3.5 rounded border-2 border-border" /> Môn lý thuyết khác</span>
        <span>· Hợp lệ: sau 00:00 <b className="text-foreground">{ymdToVN(khoa.kg)}</b> → trước hết <b className="text-foreground">{ymdToVN(khoa.bg)}</b></span>
      </div>

      <div className="rounded-lg border border-border bg-card divide-y divide-border/60">
        {hang.length === 0 && (
          <div className="px-3 py-12 text-center text-[13.5px] text-muted-foreground">Chưa có giáo viên trong khóa. Quay lại bước ① để chọn giáo viên.</div>
        )}
        {hang.map((ma) => {
          const g = theoMa.get(ma);
          const ps = mo.filter((p) => p.ma === ma);
          const trong = trongKhoa.has(ma);
          return (
            <div key={ma} id={`gv-${ma}`} className={`px-3 py-3 grid grid-cols-1 sm:grid-cols-[190px_1fr] gap-3 ${trong ? (chon.includes(ma) ? "bg-pc-soft" : "") : "bg-destructive/5"}`}>
              <div>
                {trong && (
                  <label className="mb-1 inline-flex items-center gap-1.5 text-[12px] text-muted-foreground cursor-pointer">
                    <input type="checkbox" checked={chon.includes(ma)} onChange={() => setChon((c) => (c.includes(ma) ? c.filter((x) => x !== ma) : [...c, ma]))} aria-label={`Chọn ${g?.ten ?? ma}`} />
                    Chọn
                  </label>
                )}
                <div className="text-[14px] font-semibold">{g?.ten ?? ma}</div>
                <div className="font-mono text-[12px] text-muted-foreground">{ma}</div>
                <div className="mt-1 flex gap-1 flex-wrap">
                  {g && <HuyHieu g={g} khoa={khoa} />}
                  {!trong && <span className="px-1.5 rounded text-[11px] font-semibold bg-destructive/10 text-destructive">Ngoài danh sách khóa</span>}
                </div>
                {trong && (
                  <button
                    onClick={() => moSoan(undefined, ma)}
                    title={ps.length ? "Mỗi giáo viên có thể có nhiều phân công (khác môn / khác ngày). Muốn sửa phân công cũ: bấm biểu tượng bút trên phân công đó." : ""}
                    className={
                      "mt-2 h-9 px-3 rounded-lg border text-[13px] font-semibold " +
                      (ps.length
                        ? "border-border text-muted-foreground hover:bg-muted"
                        : "border-pc-border text-pc hover:bg-pc-soft")
                    }
                  >
                    {ps.length ? "+ Thêm phân công khác" : "+ Phân công"}
                  </button>
                )}
              </div>
              <div className="space-y-2">
                {ps.length === 0 && <span className="text-[13.5px] text-muted-foreground">Chưa có phân công.</span>}
                {ps.map((p) => {
                  const loi = loiCuaPc(p.id);
                  const xau = loi.some((v) => v.muc === "chan");
                  const th = p.mon.includes(MON_TH);
                  return (
                    <div key={String(p.id)} id={`pc-${p.id}`} className="space-y-1.5">
                      <span
                        className={
                          "inline-flex items-center gap-2 flex-wrap rounded-lg border-2 px-2.5 py-1.5 text-[13.5px] " +
                          (xau ? "border-destructive bg-destructive/5" : th ? "border-pc bg-pc-soft" : "border-border bg-card")
                        }
                      >
                        {th && <Icon name="star" className="w-4 h-4 text-pc" />}
                        <b>{monTen(p.mon)}</b>
                        <span className="text-foreground/80 tabular-nums">{fmtKhoang(p.tu, p.den)}</span>
                        <span className="text-muted-foreground text-[12px]">{soNgay(p.tu, p.den) + 1} ngày</span>
                        <button title="Sửa" aria-label="Sửa phân công" onClick={() => moSoan(p)} className="p-1 rounded hover:bg-muted"><Icon name="edit" className="w-4 h-4" /></button>
                        <button title="Xóa" aria-label="Xóa phân công" onClick={() => setXoa(p)} className="p-1 rounded hover:bg-muted"><Icon name="trash" className="w-4 h-4" /></button>
                      </span>
                      {loi.map((v, i) => <ThongBao key={i} v={v} />)}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* Khung nhập 1 phân công */}
      {soan && (() => {
        const g = theoMa.get(soan.ma);
        const thBat = soan.mon.includes(MON_TH);
        const khongLuu = coChan || !tu || !den || soan.mon.length === 0 || dangKiem || kiem === null || (!!soan.batch && okLo.length === 0);
        return (
          <Hop
            tieuDe={soan.batch ? `Phân công cho ${soan.batch.length} giáo viên` : `${soan.id !== null ? "Sửa" : "Thêm"} phân công — ${g?.ten ?? soan.ma}`}
            dong={() => setSoan(null)}
            chan={<>
              <span className="mr-auto text-[12.5px] text-muted-foreground">
                {soan.batch
                  ? `Sẽ tạo ${okLo.length}/${soan.batch.length} phân công, bỏ qua ${soan.batch.length - okLo.length}`
                  : coChan ? "Còn lỗi chặn — chưa lưu được" : (kiem ?? []).length ? "Có cảnh báo — vẫn lưu được" : ""}
              </span>
              <button onClick={() => setSoan(null)} className="h-9 px-4 rounded-md border border-border text-[13px]">Hủy</button>
              <button disabled={khongLuu} onClick={luu} className="h-9 px-4 rounded-md bg-pc text-white text-[13px] font-semibold disabled:opacity-40">
                {soan.batch ? `Tạo ${okLo.length} phân công` : "Áp dụng (chưa ghi vào CDB)"}
              </button>
            </>}
          >
            <button
              type="button"
              disabled={thieuNgayTh}
              onClick={pickTH}
              className={
                "w-full text-left rounded-xl px-4 py-3 border-2 flex items-center gap-3 " +
                (thBat ? "bg-pc text-white border-pc" : "bg-pc-soft text-pc border-pc") +
                (thieuNgayTh ? " opacity-50 cursor-not-allowed" : " hover:brightness-95")
              }
            >
              <Icon name="star" className="w-7 h-7 shrink-0" />
              <span>
                <span className="block text-[16px] font-bold">Thực hành lái xe</span>
                <span className={`block text-[12.5px] ${thBat ? "text-white/90" : "text-pc/80"}`}>
                  {thieuNgayTh
                    ? "Nhập “Ngày bắt đầu thực hành của khóa” ở đầu bước ② trước"
                    : `Môn nhiều GV dạy — một bấm: chọn môn + từ ${ymdToVN(thStart)} đến bế giảng ${ymdToVN(khoa.bg)}`}
                </span>
              </span>
              {thBat && <Icon name="check" className="w-6 h-6 ml-auto shrink-0" />}
            </button>

            <div>
              <div className="text-[12.5px] font-semibold mb-1.5">Môn lý thuyết khác <span className="font-normal text-muted-foreground">(chọn 1 hoặc nhiều)</span></div>
              <div className="grid grid-cols-2 gap-x-3 gap-y-1.5">
                {mon.filter((m) => m.id !== MON_TH).map((m) => (
                  <label key={m.id} className={`flex items-center gap-2 rounded-md border px-2 py-1.5 cursor-pointer ${soan.mon.includes(m.id) ? "border-foreground/40 bg-muted" : "border-border"}`}>
                    <input type="checkbox" checked={soan.mon.includes(m.id)} onChange={() => togMon(m.id)} />
                    <span className="text-[13px]">{m.ten}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <label className="block">
                <span className="block text-[12.5px] font-semibold mb-1">Từ ngày</span>
                <input type="date" value={soan.tuD} min={khoa.kg} max={khoa.bg}
                  onChange={(e) => setSoan({ ...soan, tuD: e.target.value })}
                  className="h-10 w-full rounded-md border border-border bg-background px-2 text-sm" />
              </label>
              <label className="block">
                <span className="block text-[12.5px] font-semibold mb-1">Đến ngày</span>
                <input type="date" value={soan.denD} min={khoa.kg} max={khoa.bg}
                  onChange={(e) => setSoan({ ...soan, denD: e.target.value })}
                  className="h-10 w-full rounded-md border border-border bg-background px-2 text-sm" />
              </label>
            </div>

            <div className="rounded-lg border border-border px-3 py-2.5">
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={soan.gio} onChange={(e) => setSoan({ ...soan, gio: e.target.checked })} />
                <span className="text-[13.5px] font-semibold">Chỉnh giờ</span>
                <span className="text-[12.5px] text-muted-foreground">
                  {soan.gio ? "· giờ tròn hoặc :30" : "· đang ghi “Theo ngày” (00:00)"}
                </span>
              </label>
              {soan.gio && (
                <>
                  <div className="mt-2.5 grid grid-cols-2 gap-3">
                    {([["Giờ bắt đầu", "tuT"], ["Giờ kết thúc", "denT"]] as const).map(([nhan, k]) => {
                      const cur = soan[k];
                      const opts = GIO.includes(cur) ? GIO : [...GIO, cur].sort();
                      return (
                        <label key={k} className="block">
                          <span className="block text-[12.5px] font-semibold mb-1">{nhan}</span>
                          <select value={cur} onChange={(e) => setSoan({ ...soan, [k]: e.target.value })}
                            className="h-10 w-full rounded-md border border-border bg-background px-2 text-sm">
                            {opts.map((t) => <option key={t} value={t}>{t}{GIO.includes(t) ? "" : " (lẻ phút)"}</option>)}
                          </select>
                        </label>
                      );
                    })}
                  </div>
                  <div className="mt-2 flex gap-2 flex-wrap">
                    {([["Sáng 07:30–11:30", "07:30", "11:30"], ["Chiều 13:30–17:30", "13:30", "17:30"], ["Cả ngày 07:30–17:30", "07:30", "17:30"]] as const).map(([nhan, a, b]) => (
                      <button key={nhan} type="button"
                        onClick={() => setSoan({ ...soan, gio: true, tuT: a, denT: b, denD: soan.tuD || soan.denD })}
                        className="h-8 px-2.5 rounded-md border border-border text-[12.5px] hover:bg-muted">{nhan}</button>
                    ))}
                  </div>
                  {nhieuNgayCoGio && (
                    <div className="mt-2 rounded-md border-l-4 border-warning bg-warning/10 px-2.5 py-1.5 text-[13px]">
                      Nhiều ngày + có giờ: tính LIÊN TỤC từ giờ bắt đầu ngày đầu đến giờ kết thúc ngày cuối (chiếm cả đêm). Muốn sáng/chiều từng ngày thì tạo từng dòng.
                    </div>
                  )}
                  {gioLe && <div className="mt-2 text-[12px] text-muted-foreground">Giờ lẻ phút giữ nguyên từ dữ liệu cũ; đổi giờ thì chọn lại theo bước 30 phút.</div>}
                </>
              )}
            </div>

            <div className="flex gap-2 flex-wrap items-center">
              <span className="text-[12px] text-muted-foreground">Điền nhanh (lý thuyết):</span>
              {!soan.batch && <button type="button" disabled={!coTruoc} onClick={noiTiep}
                title={coTruoc ? "" : "GV này chưa có phân công trước để nối tiếp"}
                className="h-8 px-2.5 rounded-md border border-border text-[12.5px] hover:bg-muted disabled:opacity-40">Nối tiếp sau phân công trước</button>}
              <button type="button" disabled={!soan.tuD}
                onClick={() => setSoan({ ...soan, denD: addDays(soan.tuD, 6) })}
                title={soan.tuD ? "" : "Chọn “Từ ngày” trước"}
                className="h-8 px-2.5 rounded-md border border-border text-[12.5px] hover:bg-muted disabled:opacity-40">+1 tuần</button>
            </div>

            {/* Kiểm tra ngay — sát nút Lưu */}
            <div className={`rounded-lg border-2 px-3 py-2.5 ${coChan && !soan.batch ? "border-destructive/50 bg-destructive/5" : (kiem ?? []).length ? "border-warning/50 bg-warning/5" : "border-success/50 bg-success/5"}`}>
              <div className={`text-[15px] font-bold mb-1 ${coChan ? "text-destructive" : "text-success"}`}>
                {soan.batch ? "Xem trước từng giáo viên" : "Kiểm tra ngay"} {dangKiem && <Icon name="refresh" className="w-3.5 h-3.5 inline animate-spin text-muted-foreground" />}
              </div>
              {soan.batch ? (
                !tu || !den || soan.mon.length === 0
                  ? <div className="text-[13.5px] text-muted-foreground">Chọn môn và khoảng ngày để xem trước từng giáo viên.</div>
                  : <ul className="divide-y divide-border/50">
                      {soan.batch.map((ma) => {
                        const vs = (kiem ?? []).filter((v) => v.ref === `pc-${idLo(ma)}`);
                        const b = vs.some((v) => v.muc === "chan");
                        const w = vs.some((v) => v.muc === "canh_bao");
                        return (
                          <li key={ma} className="py-1.5">
                            <div className="flex items-center gap-2 text-[13.5px]">
                              <Icon name={b ? "x" : w ? "warn" : "check"} className={"w-[18px] h-[18px] " + (b ? "text-destructive" : w ? "text-warning" : "text-success")} />
                              <b>{theoMa.get(ma)?.ten ?? ma}</b>
                              <span className={"ml-auto text-[12.5px] " + (b ? "text-destructive" : w ? "text-warning" : "text-success")}>
                                {b ? "Bỏ qua" : w ? "Có cảnh báo" : "Hợp lệ"}
                              </span>
                            </div>
                            {vs.map((v, i) => <div key={i} className="mt-1 ml-6"><ThongBao v={v} /></div>)}
                          </li>
                        );
                      })}
                    </ul>
              ) : (kiem ?? []).length === 0
                ? <div className="text-[13.5px] text-success">{dangKiem ? "Đang kiểm tra…" : "✓ Hợp lệ."}</div>
                : <div className="space-y-1.5">{(kiem ?? []).map((v, i) => <ThongBao key={i} v={v} />)}</div>}
            </div>
          </Hop>
        );
      })()}

      {/* Hàng loạt: áp Thực hành cho GV TH chưa có */}
      {hl === "th" && (
        <HopHangLoat
          tieuDe="Áp “Thực hành lái xe” hàng loạt"
          mota={<>Tạo phân công <b>Thực hành lái xe</b>, <b className="tabular-nums">{fmtKhoang(mk(thStart), mk(khoa.bg))}</b> cho các GV thực hành chưa có phân công:</>}
          cands={chuaTH.map((ma) => ({ id: `h-${ma}`, ma, mon: [MON_TH], tu: mk(thStart), den: mk(khoa.bg) }))}
          thay={[]}
          kiemFn={(cands, thay) => kiemHL(cands, thay)}
          tenGv={(ma) => theoMa.get(ma)?.ten ?? ma}
          nhanApDung={(n) => `Áp cho ${n} GV`}
          dong={() => setHl(null)}
          apDung={(ok) => {
            const moi = ok.map((c) => ({ ...c, id: `n${Date.now().toString(36)}${++dem.current}` }));
            setBan((b) => ({ ...b, pc: [...b.pc, ...moi] }));
            setHl(null);
          }}
        />
      )}
      {/* Hàng loạt: dời ngày kết thúc thực hành */}
      {hl === "doi" && (
        <HopHangLoat
          tieuDe={`Dời ngày kết thúc thực hành — ${[...new Set(thCuaChon.map((p) => p.ma))].length} GV`}
          mota={
            <div className="grid grid-cols-2 gap-3 items-end">
              <label className="block">
                <span className="block text-[12.5px] font-semibold mb-1">Ngày kết thúc mới</span>
                <input type="date" value={ngayDoi} min={addDays(khoa.kg, 1)} max={khoa.bg}
                  onChange={(e) => setNgayDoi(e.target.value)}
                  className="h-10 w-full rounded-md border border-border bg-background px-2 text-sm" />
              </label>
              <div className="text-[12.5px] text-muted-foreground">Áp cho phân công <b>Thực hành</b> của các GV đã chọn. Ngày kết thúc để 00:00 (Theo ngày).</div>
            </div>
          }
          cands={ngayDoi ? thCuaChon.map((p) => ({ ...p, den: mk(ngayDoi) })) : []}
          thay={thCuaChon.map((p) => String(p.id))}
          kiemFn={(cands, thay) => kiemHL(cands, thay)}
          tenGv={(ma) => theoMa.get(ma)?.ten ?? ma}
          nhanApDung={(n) => `Dời cho ${n} GV`}
          dong={() => setHl(null)}
          apDung={(ok) => {
            const theoId = new Map(ok.map((c) => [String(c.id), c]));
            setBan((b) => ({ ...b, pc: b.pc.map((p) => theoId.get(String(p.id)) ?? p) }));
            setChon([]);
            setHl(null);
          }}
        />
      )}

      {/* Đổi ngày bắt đầu thực hành */}
      {doiNgay && (
        <Hop
          tieuDe="Đổi ngày bắt đầu thực hành?"
          rong="max-w-[500px]"
          dong={() => setDoiNgay(null)}
          chan={<>
            <button onClick={() => { setThStart(doiNgay.moi); setDoiNgay(null); }} className="h-9 px-4 rounded-md border border-border text-[13px]">Chỉ đổi ô này</button>
            <button onClick={apDungDoiNgay} className="h-9 px-4 rounded-md bg-pc text-white text-[13px] font-semibold">Cập nhật {doiNgay.n} phân công</button>
          </>}
        >
          <div className="rounded-md border-l-4 border-warning bg-warning/10 px-3 py-2 text-[13px]">
            Có <b>{doiNgay.n}</b> phân công Thực hành đang bắt đầu {ymdToVN(doiNgay.cu)}. Cập nhật luôn sang {ymdToVN(doiNgay.moi)}?
          </div>
          <div className="text-[12.5px] text-muted-foreground">Phân công đã chỉnh riêng (ngày khác) giữ nguyên.</div>
        </Hop>
      )}

      {/* Xóa phân công */}
      {xoa && (
        <Hop
          tieuDe="Xóa phân công này?"
          rong="max-w-[520px]"
          dong={() => setXoa(null)}
          chan={<>
            <button onClick={() => setXoa(null)} className="h-9 px-4 rounded-md border border-border text-[13px]">Giữ lại</button>
            <button onClick={() => xoaPc(xoa)} className="h-9 px-4 rounded-md bg-destructive text-white text-[13px] font-semibold">
              Xóa{xoaLaThCuoi(xoa) ? " phân công + ghép xe" : ""}
            </button>
          </>}
        >
          <div className="rounded-lg border border-border px-3 py-2">
            <b>{theoMa.get(xoa.ma)?.ten ?? xoa.ma}</b> · {monTen(xoa.mon)} · {fmtKhoang(xoa.tu, xoa.den)}
          </div>
          {xoaLaThCuoi(xoa) && (
            <div className="rounded-md border-l-4 border-warning bg-warning/10 px-3 py-2 text-[13px]">
              Đây là phân công Thực hành cuối của GV — ghép xe {ban.ghep.filter((m) => m.ma === xoa.ma).map((m) => m.xe).join(", ")} của GV sẽ bị xóa theo.
            </div>
          )}
          <div className="text-[12.5px] text-muted-foreground">Chưa ghi vào CDB cho tới khi bấm “Ghi vào CDB”.</div>
        </Hop>
      )}
    </div>
  );
}
