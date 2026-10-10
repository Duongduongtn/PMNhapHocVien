import { useState, type ReactNode } from "react";
import { Icon } from "../../components/Icon";
import { ghiPC, type BanNhapPC, type GhiPCKetQua, type KhoaPC, type VanDePC } from "../../lib/api";

// PCG-04 — thanh bản nháp + hộp "Ghi vào CDB". Bám ui-mock/phancong.html (openGhi/doGhi).
// Diff ở đây CHỈ để đếm/hiển thị; server tự suy thay đổi từ bản nháp và kiểm lại toàn bộ luật.

export interface DiffPC {
  gvThem: number; gvGo: number;
  pcThem: number; pcSua: number; pcXoa: number;
  xeThem: number; xeGo: number;
  ghThem: number; ghSua: number; ghXoa: number;
  tong: number;
}

const idCdb = (v: number | string | null | undefined): number | null =>
  typeof v === "number" ? v : typeof v === "string" && /^\d+$/.test(v) ? Number(v) : null;

/** So bản nháp với `goc` (đúng như CDB lúc tải). Dòng cũ khớp theo id CDB, dòng mới có id tạm. */
export function tinhDiff(goc: BanNhapPC, ban: BanNhapPC): DiffPC {
  const gvG = new Set(goc.gv_khoa), gvB = new Set(ban.gv_khoa);
  const xeG = new Set(goc.xe_khoa), xeB = new Set(ban.xe_khoa);
  const pcG = new Map(goc.pc.map((p) => [idCdb(p.id), p]));
  const ghG = new Map(goc.ghep.map((m) => [idCdb(m.id), m]));
  const d: DiffPC = { gvThem: 0, gvGo: 0, pcThem: 0, pcSua: 0, pcXoa: 0, xeThem: 0, xeGo: 0, ghThem: 0, ghSua: 0, ghXoa: 0, tong: 0 };
  d.gvThem = [...gvB].filter((m) => !gvG.has(m)).length;
  d.gvGo = [...gvG].filter((m) => !gvB.has(m)).length;
  d.xeThem = [...xeB].filter((m) => !xeG.has(m)).length;
  d.xeGo = [...xeG].filter((m) => !xeB.has(m)).length;
  const pcDaThay = new Set<number>();
  for (const p of ban.pc) {
    const i = idCdb(p.id);
    const o = i !== null ? pcG.get(i) : undefined;
    if (!o) d.pcThem++;
    else {
      pcDaThay.add(i as number);
      if (o.ma !== p.ma || o.tu !== p.tu || o.den !== p.den || [...o.mon].sort().join() !== [...p.mon].sort().join()) d.pcSua++;
    }
  }
  d.pcXoa = goc.pc.filter((p) => !pcDaThay.has(idCdb(p.id) as number)).length;
  const ghDaThay = new Set<number>();
  for (const m of ban.ghep) {
    if (!m.xe) continue;
    const i = idCdb(m.id);
    const o = i !== null ? ghG.get(i) : undefined;
    if (!o) d.ghThem++;
    else {
      ghDaThay.add(i as number);
      if (o.ma !== m.ma || o.xe !== m.xe || o.tu !== m.tu || o.den !== m.den) d.ghSua++;
    }
  }
  d.ghXoa = goc.ghep.filter((m) => !ghDaThay.has(idCdb(m.id) as number)).length;
  d.tong = d.gvThem + d.gvGo + d.pcThem + d.pcSua + d.pcXoa + d.xeThem + d.xeGo + d.ghThem + d.ghSua + d.ghXoa;
  return d;
}

export interface DongThayDoi {
  dau: "+" | "~" | "−";
  nhom: string;
  noiDung: string;
}

const dP = (s: string) => (s || "").slice(0, 10);
const tP = (s: string) => (s || "").slice(11, 16) || "00:00";
const ngayVN = (ymd: string) => (ymd ? `${ymd.slice(8, 10)}/${ymd.slice(5, 7)}/${ymd.slice(0, 4)}` : "?");
function khoangVN(tu: string, den: string): string {
  const coGio = tP(tu) !== "00:00" || tP(den) !== "00:00";
  if (!coGio) return `${ngayVN(dP(tu))} → ${ngayVN(dP(den))}`;
  if (dP(tu) === dP(den)) return `${ngayVN(dP(tu))} ${tP(tu)} → ${tP(den)}`;
  return `${ngayVN(dP(tu))} ${tP(tu)} → ${ngayVN(dP(den))} ${tP(den)}`;
}

/** Liệt kê TỪNG thay đổi của bản nháp so với CDB (để người dùng xem lại trước khi ghi). */
export function moTaThayDoi(
  goc: BanNhapPC, ban: BanNhapPC, tenGv: (ma: string) => string, tenMon: (ids: number[]) => string,
): DongThayDoi[] {
  const out: DongThayDoi[] = [];
  const gvG = new Set(goc.gv_khoa), gvB = new Set(ban.gv_khoa);
  for (const m of ban.gv_khoa) if (!gvG.has(m)) out.push({ dau: "+", nhom: "Giáo viên của khóa", noiDung: `Thêm ${tenGv(m)}` });
  for (const m of goc.gv_khoa) if (!gvB.has(m)) out.push({ dau: "−", nhom: "Giáo viên của khóa", noiDung: `Gỡ ${tenGv(m)}` });
  const pcG = new Map(goc.pc.map((p) => [idCdb(p.id), p]));
  const thay = new Set<number>();
  for (const p of ban.pc) {
    const i = idCdb(p.id);
    const o = i !== null ? pcG.get(i) : undefined;
    const mo_ta = `${tenGv(p.ma)} — ${tenMon(p.mon)}, ${khoangVN(p.tu, p.den)}`;
    if (!o) out.push({ dau: "+", nhom: "Phân công dạy", noiDung: mo_ta });
    else {
      thay.add(i as number);
      if (o.ma !== p.ma || o.tu !== p.tu || o.den !== p.den || [...o.mon].sort().join() !== [...p.mon].sort().join()) {
        out.push({ dau: "~", nhom: "Phân công dạy", noiDung: `${tenGv(p.ma)}: ${tenMon(o.mon)}, ${khoangVN(o.tu, o.den)} → ${tenMon(p.mon)}, ${khoangVN(p.tu, p.den)}` });
      }
    }
  }
  for (const o of goc.pc) if (!thay.has(idCdb(o.id) as number)) out.push({ dau: "−", nhom: "Phân công dạy", noiDung: `Xóa ${tenGv(o.ma)} — ${tenMon(o.mon)}, ${khoangVN(o.tu, o.den)}` });
  const xG = new Set(goc.xe_khoa), xB = new Set(ban.xe_khoa);
  for (const b of ban.xe_khoa) if (!xG.has(b)) out.push({ dau: "+", nhom: "Xe của khóa", noiDung: `Thêm xe ${b}` });
  for (const b of goc.xe_khoa) if (!xB.has(b)) out.push({ dau: "−", nhom: "Xe của khóa", noiDung: `Gỡ xe ${b}` });
  const ghG = new Map(goc.ghep.map((m) => [idCdb(m.id), m]));
  const daGh = new Set<number>();
  for (const m of ban.ghep) {
    if (!m.xe) continue;
    const i = idCdb(m.id);
    const o = i !== null ? ghG.get(i) : undefined;
    if (!o) out.push({ dau: "+", nhom: "Ghép xe", noiDung: `Xe ${m.xe} → ${tenGv(m.ma)}, ${khoangVN(m.tu, m.den)}` });
    else {
      daGh.add(i as number);
      if (o.ma !== m.ma || o.xe !== m.xe || o.tu !== m.tu || o.den !== m.den) {
        out.push({ dau: "~", nhom: "Ghép xe", noiDung: `${tenGv(m.ma)}: xe ${o.xe}, ${khoangVN(o.tu, o.den)} → xe ${m.xe}, ${khoangVN(m.tu, m.den)}` });
      }
    }
  }
  for (const o of goc.ghep) if (!daGh.has(idCdb(o.id) as number)) out.push({ dau: "−", nhom: "Ghép xe", noiDung: `Bỏ ghép xe ${o.xe} → ${tenGv(o.ma)}` });
  return out;
}

function DanhSachThayDoi({ ds }: { ds: DongThayDoi[] }) {
  if (ds.length === 0) return <div className="text-[13px] text-muted-foreground">Chưa có thay đổi nào.</div>;
  const nhom = [...new Set(ds.map((d) => d.nhom))];
  return (
    <div className="space-y-2.5">
      {nhom.map((n) => (
        <div key={n}>
          <div className="text-[12px] font-bold uppercase tracking-wide text-muted-foreground mb-1">{n}</div>
          <ul className="space-y-1">
            {ds.filter((d) => d.nhom === n).map((d, i) => (
              <li key={i} className="flex gap-2 text-[13.5px]">
                <span className={"w-5 shrink-0 text-center font-bold " + (d.dau === "+" ? "text-success" : d.dau === "−" ? "text-destructive" : "text-warning")}>{d.dau}</span>
                <span>{d.noiDung}</span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

function Hop({ tieuDe, children, chan, dong, rong = "max-w-[660px]" }: { tieuDe: string; children: ReactNode; chan: ReactNode; dong?: () => void; rong?: string }) {
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center p-4 bg-black/40" role="dialog" aria-modal="true" aria-label={tieuDe}>
      <div className={`w-full ${rong} max-h-[88vh] flex flex-col rounded-lg bg-card border border-border shadow-xl`}>
        <div className="px-5 py-3 border-b border-border flex items-center">
          <h3 className="text-[15px] font-semibold">{tieuDe}</h3>
          {dong && (
            <button onClick={dong} aria-label="Đóng" className="ml-auto w-8 h-8 rounded-md hover:bg-muted inline-flex items-center justify-center">
              <Icon name="x" className="w-4 h-4" />
            </button>
          )}
        </div>
        <div className="px-5 py-4 overflow-auto space-y-3 text-[13.5px]">{children}</div>
        <div className="px-5 py-3 border-t border-border flex justify-end gap-2">{chan}</div>
      </div>
    </div>
  );
}

function Dong({ dau, nhan, n, sp }: { dau: "+" | "~" | "−"; nhan: string; n: number; sp: string }) {
  if (!n) return null;
  const mau = dau === "+" ? "text-success" : dau === "−" ? "text-destructive" : "text-warning";
  return (
    <div className="flex items-center gap-2 py-1">
      <span className={`w-5 text-center font-bold ${mau}`}>{dau}</span>
      <span>{nhan}</span>
      <span className="px-1.5 rounded bg-muted text-[12px] font-semibold">{n}</span>
      <span className="ml-auto text-[11.5px] text-muted-foreground font-mono truncate">{sp}</span>
    </div>
  );
}

export default function GhiBanNhap({
  khoa, goc, ban, canhBao, coChan, dangKiem, targetKey, onHuy, onDaGhi, tenGv, tenMon,
}: {
  khoa: KhoaPC;
  goc: BanNhapPC;
  ban: BanNhapPC;
  canhBao: VanDePC[];
  coChan: boolean;
  dangKiem: boolean;
  targetKey: string;
  onHuy: () => void;
  onDaGhi: (kq: GhiPCKetQua) => void;
  tenGv: (ma: string) => string;
  tenMon: (ids: number[]) => string;
}) {
  const d = tinhDiff(goc, ban);
  const [hop, setHop] = useState<"huy" | "ghi" | "ketqua" | "chitiet" | null>(null);
  const chiTiet = moTaThayDoi(goc, ban, tenGv, tenMon);
  const [tichThat, setTichThat] = useState(false);
  const [tichCanhBao, setTichCanhBao] = useState(false);
  const [dangGhi, setDangGhi] = useState(false);
  const [loi, setLoi] = useState<string | null>(null);
  const [kq, setKq] = useState<GhiPCKetQua | null>(null);

  const khoaNut = d.tong === 0 || coChan || dangKiem;
  const lyDoKhoa = coChan ? "Còn lỗi chặn — sửa hết mới ghi được" : d.tong === 0 ? "Chưa có thay đổi" : dangKiem ? "Đang kiểm tra…" : "";

  function mo() {
    setTichThat(false);
    setTichCanhBao(false);
    setLoi(null);
    setHop("ghi");
  }

  async function ghi() {
    setDangGhi(true);
    setLoi(null);
    try {
      const r = await ghiPC(khoa.ma_kh, ban, { da_xem_canh_bao: tichCanhBao || canhBao.length === 0, xac_nhan_csdl_that: tichThat }, targetKey);
      setKq(r);
      setHop("ketqua");
      onDaGhi(r);
    } catch (e) {
      setLoi((e as Error).message);
    } finally {
      setDangGhi(false);
    }
  }

  const duDieuKien = tichThat && (canhBao.length === 0 || tichCanhBao) && !dangGhi;

  return (
    <>
      <div className="shrink-0 bg-card border-t border-border px-4 h-14 flex items-center gap-3">
        {d.tong > 0 ? (
          <>
            <span className="w-2.5 h-2.5 rounded-full bg-pc" />
            <div className="text-[13.5px]">
              <b>Chưa ghi vào CDB:</b> {d.tong} thay đổi
              <span className="text-muted-foreground">
                {" "}· thêm {d.gvThem + d.pcThem + d.xeThem + d.ghThem} · sửa {d.pcSua + d.ghSua} · xóa {d.gvGo + d.pcXoa + d.xeGo + d.ghXoa}
              </span>
            </div>
          </>
        ) : (
          <div className="text-[13.5px] text-muted-foreground">
            Chưa có thay đổi nào chưa ghi.
            {kq?.ok && kq.da_ghi.length > 0 && <span className="text-success"> Đã ghi {kq.da_ghi.length} thay đổi gần nhất.</span>}
          </div>
        )}
        <div className="ml-auto flex items-center gap-2">
          <button
            disabled={d.tong === 0}
            onClick={() => setHop("chitiet")}
            className="h-10 px-4 rounded-lg border border-pc-border text-pc text-[13px] font-semibold hover:bg-pc-soft disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Xem các thay đổi
          </button>
          <button
            disabled={d.tong === 0}
            onClick={() => setHop("huy")}
            className="h-10 px-4 rounded-lg border border-border text-[13px] hover:bg-muted disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Hủy thay đổi
          </button>
          <button
            disabled={khoaNut}
            onClick={mo}
            title={lyDoKhoa}
            className="h-10 px-5 rounded-lg bg-pc text-white text-[13px] font-semibold hover:brightness-110 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {coChan ? "🔒 " : ""}Ghi vào CDB{d.tong ? ` (${d.tong})` : ""}
          </button>
        </div>
      </div>

      {hop === "chitiet" && (
        <Hop
          tieuDe={`Các thay đổi chưa ghi vào CDB (${d.tong})`}
          dong={() => setHop(null)}
          chan={<>
            <button onClick={() => setHop(null)} className="h-9 px-4 rounded-md border border-border text-[13px]">Đóng</button>
            <button
              disabled={khoaNut}
              onClick={mo}
              title={lyDoKhoa}
              className="h-9 px-4 rounded-md bg-pc text-white text-[13px] font-semibold disabled:opacity-40"
            >
              Ghi vào CDB…
            </button>
          </>}
        >
          <p className="text-[12.5px] text-muted-foreground">
            Đây là các thay đổi bạn đã làm trên màn hình nhưng <b>chưa nằm trong CDB</b>. Chỉ khi bấm “Ghi vào CDB” và xác nhận thì CDB mới đổi.
          </p>
          <DanhSachThayDoi ds={chiTiet} />
        </Hop>
      )}

      {hop === "huy" && (
        <Hop
          tieuDe="Hủy toàn bộ thay đổi chưa ghi?"
          rong="max-w-[460px]"
          dong={() => setHop(null)}
          chan={<>
            <button onClick={() => setHop(null)} className="h-9 px-4 rounded-md border border-border text-[13px]">Giữ các thay đổi</button>
            <button onClick={() => { onHuy(); setHop(null); }} className="h-9 px-4 rounded-md bg-destructive text-white text-[13px] font-semibold">Hủy thay đổi</button>
          </>}
        >
          <p>Có <b>{d.tong}</b> thay đổi chưa ghi. Hủy sẽ đưa khóa về đúng như đang có trong CDB (CDB không bị ảnh hưởng). Không thể hoàn tác.</p>
        </Hop>
      )}

      {hop === "ghi" && (
        <Hop
          tieuDe="Ghi vào CSDL đích — xem lại trước khi ghi"
          dong={dangGhi ? undefined : () => setHop(null)}
          chan={<>
            <button disabled={dangGhi} onClick={() => setHop(null)} className="h-9 px-4 rounded-md border border-border text-[13px] disabled:opacity-40">Quay lại</button>
            <button
              disabled={!duDieuKien}
              onClick={ghi}
              className="h-9 px-4 rounded-md bg-pc text-white text-[13px] font-semibold disabled:opacity-40 inline-flex items-center gap-1.5"
            >
              {dangGhi && <Icon name="refresh" className="w-4 h-4 animate-spin" />}
              {dangGhi ? "Đang ghi…" : `Ghi ${d.tong} thay đổi vào CDB`}
            </button>
          </>}
        >
          <div className="rounded-lg border border-border px-3 py-2">
            <div className="text-[12.5px] font-bold text-pc mb-1">Khóa {khoa.ten_kh} · {d.tong} thay đổi</div>
            <Dong dau="+" nhan="Thêm GV vào khóa" n={d.gvThem} sp="usp_KhoaHoc_GiaoVien_Insert · cờ=1" />
            <Dong dau="+" nhan="Thêm phân công dạy" n={d.pcThem} sp="usp_LichLV_KhoaHoc_GiaoVien_Insert · cờ=0" />
            <Dong dau="~" nhan="Sửa phân công dạy" n={d.pcSua} sp="usp_LichLV_KhoaHoc_GiaoVien_Update" />
            <Dong dau="+" nhan="Thêm xe vào khóa" n={d.xeThem} sp="usp_KhoaHoc_XeTap_Insert · cờ=1" />
            <Dong dau="+" nhan="Ghép xe (thêm)" n={d.ghThem} sp="LichSD_KhoaHoc_XeTap_Insert · cờ=0" />
            <Dong dau="~" nhan="Ghép xe (sửa)" n={d.ghSua} sp="usp_LichSD_KhoaHoc_XeTap_Update" />
            <Dong dau="−" nhan="Gỡ GV khỏi khóa" n={d.gvGo} sp="usp_LLV_KhoaHoc_GiaoVien_Delete (theo MaLichLV)" />
            <Dong dau="−" nhan="Xóa phân công dạy" n={d.pcXoa} sp="usp_LLV_KhoaHoc_GiaoVien_Delete" />
            <Dong dau="−" nhan="Gỡ xe khỏi khóa" n={d.xeGo} sp="usp_LSD_KhoaHoc_Xetap_Delete (theo MaLichSD)" />
            <Dong dau="−" nhan="Xóa ghép xe" n={d.ghXoa} sp="usp_LSD_KhoaHoc_Xetap_Delete" />
          </div>

          <details className="rounded-lg border border-border px-3 py-2">
            <summary className="cursor-pointer text-[13px] font-semibold">Xem chi tiết từng thay đổi ({chiTiet.length})</summary>
            <div className="mt-2 max-h-48 overflow-auto"><DanhSachThayDoi ds={chiTiet} /></div>
          </details>

          {canhBao.length > 0 && (
            <div className="rounded-lg border-2 border-warning/60 bg-warning/10 px-3 py-2.5">
              <div className="font-bold text-warning mb-1">{canhBao.length} cảnh báo chưa xử lý</div>
              <ul className="list-disc pl-5 text-[13px] space-y-0.5 max-h-28 overflow-auto">
                {canhBao.map((w, i) => (
                  <li key={i}><b>{w.ai}</b>: {w.noi_dung}</li>
                ))}
              </ul>
            </div>
          )}

          <label className="flex items-start gap-2 cursor-pointer">
            <input type="checkbox" className="mt-1" checked={tichThat} onChange={(e) => setTichThat(e.target.checked)} />
            <span>Tôi hiểu đây là <b>CSDL thật</b> của cơ sở — các thay đổi trên sẽ được ghi ngay và không có nút hoàn tác.</span>
          </label>
          {canhBao.length > 0 && (
            <label className="flex items-start gap-2 cursor-pointer">
              <input type="checkbox" className="mt-1" checked={tichCanhBao} onChange={(e) => setTichCanhBao(e.target.checked)} />
              <span>Tôi đã xem <b>{canhBao.length} cảnh báo</b> ở trên và vẫn muốn ghi.</span>
            </label>
          )}
          {khoa.da_dkkh && (
            <div className="rounded-md border-l-4 border-warning bg-warning/10 px-3 py-2 text-[13px]">
              Khóa đã gửi DKKH — thay đổi có thể không có trong bản Sở đang giữ.
            </div>
          )}
          {loi && <div className="rounded-md border-l-4 border-destructive bg-destructive/5 px-3 py-2 text-[13px] text-destructive">{loi}</div>}
          <p className="text-[12px] text-muted-foreground">
            Mỗi dòng ghi là một lệnh riêng; nếu lỗi giữa chừng, hệ thống liệt kê dòng đã ghi / chưa ghi để làm tiếp.
          </p>
        </Hop>
      )}

      {hop === "ketqua" && kq && (
        <Hop
          tieuDe={kq.ok ? "Đã ghi xong" : "Ghi chưa xong"}
          dong={() => setHop(null)}
          chan={<button onClick={() => setHop(null)} className="h-9 px-4 rounded-md bg-pc text-white text-[13px] font-semibold">Đóng</button>}
        >
          {kq.ok ? (
            <>
              <div className="rounded-lg border border-success/40 bg-success/5 px-3 py-2.5 text-success font-semibold text-[14px]">
                ✓ {kq.da_ghi.length}/{kq.da_ghi.length} thay đổi đã ghi vào CDB.
              </div>
              <p className="text-muted-foreground text-[13px]">
                {khoa.da_dkkh
                  ? "Khóa đã gửi DKKH: nếu Sở yêu cầu cập nhật GV/xe, cần kết xuất lại ở phần mềm CDB."
                  : "Nếu khóa chưa kết xuất DKKH, danh sách GV/xe này sẽ đi cùng gói khi kết xuất."}
              </p>
            </>
          ) : (
            <>
              <div className="rounded-md border-l-4 border-destructive bg-destructive/5 px-3 py-2 text-[13px]">
                {kq.thong_bao || kq.loi || "Lỗi giữa chừng."} Đã ghi {kq.da_ghi.length}, chưa ghi {kq.chua_ghi.length}.
              </div>
              {kq.da_ghi.length > 0 && (
                <div>
                  <div className="font-semibold text-success mb-1">Đã ghi ({kq.da_ghi.length})</div>
                  <ul className="list-disc pl-5 text-[13px] max-h-32 overflow-auto">{kq.da_ghi.map((x, i) => <li key={i}>{x.mo_ta}</li>)}</ul>
                </div>
              )}
              <div>
                <div className="font-semibold text-destructive mb-1">Chưa ghi ({kq.chua_ghi.length})</div>
                <ul className="list-disc pl-5 text-[13px] max-h-32 overflow-auto">{kq.chua_ghi.map((x, i) => <li key={i}>{x.mo_ta}</li>)}</ul>
              </div>
              <p className="text-[13px] text-muted-foreground">Màn hình đã được làm tươi theo đúng CDB hiện tại (để không ghi trùng dòng đã ghi). Hãy làm lại các thay đổi chưa ghi ở trên.</p>
            </>
          )}
        </Hop>
      )}
    </>
  );
}
