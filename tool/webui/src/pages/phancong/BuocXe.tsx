import { useMemo, useRef, useState, type ReactNode } from "react";
import { Icon } from "../../components/Icon";
import { ymdToVN } from "../../lib/format";
import type { BanNhapPC, GhepDong, GiaoVienPC, KhoaPC, VanDePC, XePC } from "../../lib/api";
import { HuyHieu } from "./BuocGiaoVien";

// PCG-03 (1/2) — Bước ③ chọn xe vào khóa + ghép 1 GV – 1 xe theo khoảng ngày. Bám ui-mock/phancong.html.
// Luật do server quyết (lỗi lấy từ cột Kiểm tra khóa qua `vande`); trang chỉ sửa BẢN NHÁP.
// Địa điểm để trống thì server tự điền mặc định khi ghi (địa điểm phổ biến nhất của cơ sở).

const MON_TH = 6;
const DIA_DIEM_GOI_Y = "tại trung tâm Thành Đạt và trên đường";
const dP = (s: string) => s.slice(0, 10);
const mk = (d: string) => `${d}T00:00`;

function homNay(): string {
  const d = new Date();
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

function thongTinXe(x: XePC | undefined, khoa: KhoaPC): ReactNode {
  if (!x) return null;
  const nay = homNay();
  const dang = (x.ban as { khoa?: string; bg?: string }[]).filter((b) => b.khoa && b.bg && b.bg >= nay);
  const hetHan = !!x.gp_het && x.gp_het.slice(0, 10) < khoa.bg;
  return (
    <>
      Hạng {x.hang || "—"} ·{" "}
      {x.gp_het ? (
        hetHan
          ? <b className="text-destructive">giấy phép hết {ymdToVN(x.gp_het.slice(0, 10))}</b>
          : <>giấy phép đến {ymdToVN(x.gp_het.slice(0, 10))}</>
      ) : "chưa có hạn giấy phép"}
      {!x.active && <> · <b className="text-destructive">đã ngừng</b></>}
      {dang.map((b, i) => <span key={i}> · đang ở {b.khoa} → {ymdToVN(b.bg as string)}</span>)}
    </>
  );
}

function Hop({ tieuDe, children, chan, dong, rong = "max-w-[640px]" }: { tieuDe: string; children: ReactNode; chan: ReactNode; dong: () => void; rong?: string }) {
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center p-4 bg-black/40" role="dialog" aria-modal="true" aria-label={tieuDe}>
      <div className={`w-full ${rong} max-h-[88vh] flex flex-col rounded-lg bg-card border border-border shadow-xl`}>
        <div className="px-5 py-3 border-b border-border flex items-center">
          <h3 className="text-[15px] font-semibold">{tieuDe}</h3>
          <button onClick={dong} aria-label="Đóng" className="ml-auto w-8 h-8 rounded-md hover:bg-muted inline-flex items-center justify-center">
            <Icon name="x" className="w-4 h-4" />
          </button>
        </div>
        <div className="px-5 py-4 overflow-auto space-y-3 text-[13.5px]">{children}</div>
        <div className="px-5 py-3 border-t border-border flex justify-end gap-2">{chan}</div>
      </div>
    </div>
  );
}

const lopMuc = (m: string) =>
  m === "chan" ? "border-destructive bg-destructive/5" : m === "canh_bao" ? "border-warning bg-warning/10" : "border-primary bg-primary/5";

export default function BuocXe({
  khoa, danhMuc, xeDm, ban, setBan, vande,
}: {
  khoa: KhoaPC;
  danhMuc: GiaoVienPC[];
  xeDm: XePC[];
  ban: BanNhapPC;
  setBan: (f: (b: BanNhapPC) => BanNhapPC) => void;
  vande: VanDePC[];
}) {
  const theoXe = useMemo(() => new Map(xeDm.map((x) => [x.bs, x])), [xeDm]);
  const theoGv = useMemo(() => new Map(danhMuc.map((g) => [g.ma, g])), [danhMuc]);
  const [poolMo, setPoolMo] = useState(false);
  const [q, setQ] = useState("");
  const [doiXe, setDoiXe] = useState<{ ma: string; xe: string } | null>(null);
  const [goXe, setGoXe] = useState<string | null>(null);
  const dem = useRef(0);

  const ghepCua = (ma: string) => ban.ghep.find((m) => m.ma === ma);
  const dungBoi = (bs: string) => ban.ghep.find((m) => m.xe === bs && m.xe)?.ma;
  const loiRef = (ref: string) => vande.filter((v) => v.ref === ref && v.buoc === 3 && v.muc !== "thong_tin");

  // GV hiện ở bảng ghép: có phân công Thực hành lái xe, hoặc đang có ghép xe (dữ liệu cũ).
  const dsGv = useMemo(() => {
    const th = ban.gv_khoa.filter((ma) => ban.pc.some((p) => p.ma === ma && p.mon.includes(MON_TH)));
    const coGhep = ban.ghep.map((m) => m.ma).filter((ma) => !th.includes(ma));
    return [...th, ...[...new Set(coGhep)]];
  }, [ban.gv_khoa, ban.pc, ban.ghep]);

  function datXe(ma: string, bs: string) {
    const cur = ghepCua(ma);
    if (!bs) { setBan((b) => ({ ...b, ghep: b.ghep.filter((m) => m.ma !== ma) })); return; }
    if (cur && cur.xe && cur.xe !== bs) { setDoiXe({ ma, xe: bs }); return; }
    ghiXe(ma, bs);
  }
  function ghiXe(ma: string, bs: string) {
    const pcTH = ban.pc.filter((p) => p.ma === ma && p.mon.includes(MON_TH));
    const tu = pcTH.length ? pcTH.map((p) => p.tu).sort()[0] : mk(khoa.kg);
    const den = pcTH.length ? pcTH.map((p) => p.den).sort().pop() as string : mk(khoa.bg);
    setBan((b) => {
      const cur = b.ghep.find((m) => m.ma === ma);
      if (cur) return { ...b, ghep: b.ghep.map((m) => (m.ma === ma ? { ...m, xe: bs } : m)) };
      const moi: GhepDong = { id: `n${Date.now().toString(36)}${++dem.current}`, ma, xe: bs, tu, den, dia_diem: "" };
      return { ...b, ghep: [...b.ghep, moi] };
    });
  }
  function datNgay(ma: string, f: "tu" | "den", v: string) {
    if (!v) return;
    setBan((b) => ({ ...b, ghep: b.ghep.map((m) => (m.ma === ma ? { ...m, [f]: mk(v) } : m)) }));
  }
  function themXe(bs: string) {
    setBan((b) => ({ ...b, xe_khoa: b.xe_khoa.includes(bs) ? b.xe_khoa : [...b.xe_khoa, bs] }));
  }
  function boXe(bs: string, kemGhep: boolean) {
    setBan((b) => ({
      ...b,
      xe_khoa: b.xe_khoa.filter((x) => x !== bs),
      ghep: kemGhep ? b.ghep.filter((m) => m.xe !== bs) : b.ghep,
    }));
  }

  const pool = xeDm.filter(
    (x) => !ban.xe_khoa.includes(x.bs) && (x.bs.toLowerCase().includes(q.toLowerCase()) || x.hang.toLowerCase().includes(q.toLowerCase())),
  );

  return (
    <div>
      {/* Xe của khóa — dải chip gọn */}
      <div className="mb-3 rounded-lg border border-pc-border bg-card px-3 py-2.5">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-[13px] font-bold text-pc">Xe của khóa ({ban.xe_khoa.length})</span>
          <button
            onClick={() => { setQ(""); setPoolMo(true); }}
            className="ml-auto h-8 px-2.5 rounded-md border border-pc-border text-pc text-[12.5px] font-semibold hover:bg-pc-soft inline-flex items-center gap-1"
          >
            <Icon name="plus" className="w-3.5 h-3.5" /> Thêm xe
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {ban.xe_khoa.length === 0 && <span className="text-[13px] text-muted-foreground">Chưa chọn xe nào cho khóa.</span>}
          {ban.xe_khoa.map((bs) => {
            const u = dungBoi(bs);
            const xau = loiRef(`xe-${bs}`).some((v) => v.muc === "chan") || (theoXe.get(bs) ? !theoXe.get(bs)!.active : false);
            const tenGv = u ? theoGv.get(u)?.ten ?? u : "";
            return (
              <span
                key={bs}
                id={`xe-${bs}`}
                className={"inline-flex items-center gap-2 rounded-lg border-2 px-2.5 py-1 text-[13px] " + (xau ? "border-destructive bg-destructive/5" : u ? "border-border" : "border-warning bg-warning/10")}
                title={`Hạng ${theoXe.get(bs)?.hang ?? "—"}`}
              >
                <b className="font-mono">{bs}</b>
                <span className="text-[12px] text-muted-foreground">{u ? `→ ${tenGv}` : "chưa ghép"}</span>
                <button
                  title="Gỡ xe khỏi khóa"
                  aria-label={`Gỡ xe ${bs} khỏi khóa`}
                  onClick={() => (u ? setGoXe(bs) : boXe(bs, false))}
                  className="p-0.5 rounded hover:bg-muted"
                >
                  <Icon name="x" className="w-4 h-4" />
                </button>
              </span>
            );
          })}
        </div>
        {ban.xe_khoa.flatMap((bs) => loiRef(`xe-${bs}`)).map((v, i) => (
          <div key={i} className={`mt-2 rounded-md border-l-4 px-2.5 py-1.5 text-[13px] ${lopMuc(v.muc)}`}>{v.noi_dung}</div>
        ))}
      </div>

      <div className="mb-2 text-[13.5px] text-muted-foreground">
        Mỗi <b className="text-foreground">giáo viên thực hành</b> ghép <b className="text-foreground">1 xe</b>. Địa điểm mặc định: <i>{DIA_DIEM_GOI_Y}</i>.
      </div>

      <div className="rounded-lg border border-border bg-card divide-y divide-border/60">
        {dsGv.length === 0 && (
          <div className="px-3 py-12 text-center text-[13.5px] text-muted-foreground">
            Chưa có giáo viên nào có phân công “Thực hành lái xe”. Làm bước ② trước.
          </div>
        )}
        {dsGv.map((ma) => {
          const g = theoGv.get(ma);
          const m = ghepCua(ma);
          const loi = loiRef(`gh-${ma}`);
          const xau = loi.some((v) => v.muc === "chan");
          const pcTH = ban.pc.filter((p) => p.ma === ma && p.mon.includes(MON_TH));
          return (
            <div key={ma} id={`gh-${ma}`} className="px-3 py-3 grid grid-cols-1 sm:grid-cols-[190px_1fr] gap-3">
              <div>
                <div className="text-[14px] font-semibold">{g?.ten ?? ma}</div>
                <div className="font-mono text-[12px] text-muted-foreground">{ma}</div>
                {g && <div className="mt-1 flex gap-1 flex-wrap"><HuyHieu g={g} khoa={khoa} /></div>}
                <div className="text-[12px] text-muted-foreground mt-1">
                  TH:{" "}
                  {pcTH.length
                    ? pcTH.map((p) => `${ymdToVN(dP(p.tu))} → ${ymdToVN(dP(p.den))}`).join("; ")
                    : <span className="text-warning font-semibold">chưa có phân công TH</span>}
                </div>
              </div>
              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <select
                    aria-label={`Xe của ${g?.ten ?? ma}`}
                    value={m?.xe ?? ""}
                    onChange={(e) => datXe(ma, e.target.value)}
                    className={`h-10 w-[220px] rounded-md border bg-background px-2 text-sm ${xau ? "border-destructive" : "border-border"}`}
                  >
                    <option value="">— chưa ghép xe —</option>
                    {ban.xe_khoa.map((bs) => {
                      const u = dungBoi(bs);
                      const khac = !!u && u !== ma;
                      return (
                        <option key={bs} value={bs} disabled={khac}>
                          {bs}{khac ? ` — đã ghép ${theoGv.get(u as string)?.ten ?? u}` : ""}
                        </option>
                      );
                    })}
                  </select>
                  {m?.xe
                    ? <button onClick={() => datXe(ma, "")} className="h-10 px-3 rounded-lg border border-border text-[13px] hover:bg-muted">Bỏ ghép</button>
                    : <span className="text-[13px] text-muted-foreground">{ban.xe_khoa.length ? "Chọn xe để ghép." : "Thêm xe vào khóa trước."}</span>}
                </div>
                {m?.xe && (
                  <>
                    <div className="mt-2 flex items-center gap-1.5 tabular-nums flex-wrap">
                      <input type="date" aria-label="Ghép từ ngày" value={dP(m.tu)} min={khoa.kg} max={khoa.bg}
                        onChange={(e) => datNgay(ma, "tu", e.target.value)}
                        className="h-10 w-[150px] rounded-md border border-border bg-background px-2 text-sm" />
                      <span>→</span>
                      <input type="date" aria-label="Ghép đến ngày" value={dP(m.den)} min={khoa.kg} max={khoa.bg}
                        onChange={(e) => datNgay(ma, "den", e.target.value)}
                        className="h-10 w-[150px] rounded-md border border-border bg-background px-2 text-sm" />
                      <span className="text-[12px] text-muted-foreground ml-1">Theo ngày</span>
                    </div>
                    <div className="mt-1 text-[12px] text-muted-foreground">{thongTinXe(theoXe.get(m.xe), khoa)}</div>
                  </>
                )}
                {loi.map((v, i) => (
                  <div key={i} className={`mt-2 rounded-md border-l-4 px-2.5 py-1.5 text-[13px] ${lopMuc(v.muc)}`}>{v.noi_dung}</div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {poolMo && (
        <Hop
          tieuDe="Thêm xe tập lái vào khóa"
          dong={() => setPoolMo(false)}
          chan={<button onClick={() => setPoolMo(false)} className="h-9 px-4 rounded-md border border-border text-[13px]">Đóng</button>}
        >
          <input
            autoFocus
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Biển số / hạng"
            className="w-full h-9 px-3 rounded-md border border-border bg-background text-[13px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pc"
          />
          <ul className="rounded-lg border border-border divide-y divide-border/60 max-h-80 overflow-auto">
            {pool.length === 0 && <li className="px-3 py-6 text-center text-[13px] text-muted-foreground">Không có xe nào để thêm.</li>}
            {pool.map((x) => (
              <li key={x.bs} className="px-3 py-2 flex items-center gap-2">
                <div className="min-w-0">
                  <div className="font-mono font-semibold text-[13px]">{x.bs}</div>
                  <div className="text-[12px] text-muted-foreground">{thongTinXe(x, khoa)}</div>
                </div>
                <button
                  disabled={!x.active}
                  onClick={() => themXe(x.bs)}
                  className="ml-auto h-8 px-3 rounded-md border border-pc-border text-pc text-[12.5px] font-semibold hover:bg-pc-soft disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  Thêm
                </button>
              </li>
            ))}
          </ul>
          <p className="text-[12px] text-muted-foreground">
            Xe hết hạn giấy phép vẫn thêm được vào danh sách, nhưng bị <b>chặn khi ghép</b> cho GV. Xe đã ngừng không thêm được.
          </p>
        </Hop>
      )}

      {doiXe && (
        <Hop
          tieuDe="Đổi xe cho giáo viên?"
          rong="max-w-[460px]"
          dong={() => setDoiXe(null)}
          chan={<>
            <button onClick={() => setDoiXe(null)} className="h-9 px-4 rounded-md border border-border text-[13px]">Giữ xe cũ</button>
            <button onClick={() => { ghiXe(doiXe.ma, doiXe.xe); setDoiXe(null); }} className="h-9 px-4 rounded-md bg-pc text-white text-[13px] font-semibold">Đổi xe</button>
          </>}
        >
          <p>
            GV <b>{theoGv.get(doiXe.ma)?.ten ?? doiXe.ma}</b> đang dùng xe <b className="font-mono">{ghepCua(doiXe.ma)?.xe}</b>. Đổi sang{" "}
            <b className="font-mono">{doiXe.xe}</b>? Xe cũ sẽ không còn ghép cho GV nào.
          </p>
        </Hop>
      )}

      {goXe && (() => {
        const m = ban.ghep.find((x) => x.xe === goXe);
        return (
          <Hop
            tieuDe={`Gỡ xe ${goXe} khỏi khóa?`}
            rong="max-w-[500px]"
            dong={() => setGoXe(null)}
            chan={<>
              <button onClick={() => setGoXe(null)} className="h-9 px-4 rounded-md border border-border text-[13px]">Giữ lại</button>
              <button onClick={() => { boXe(goXe, true); setGoXe(null); }} className="h-9 px-4 rounded-md bg-destructive text-white text-[13px] font-semibold">Gỡ xe + xóa ghép</button>
            </>}
          >
            {m && (
              <div className="rounded-md border-l-4 border-destructive bg-destructive/5 px-3 py-2 text-[13px]">
                Xe đang ghép cho GV {theoGv.get(m.ma)?.ten ?? m.ma} ({ymdToVN(dP(m.tu))} → {ymdToVN(dP(m.den))}). Gỡ xe sẽ xóa ghép xe này; GV sẽ về “chưa có xe”.
              </div>
            )}
            <div className="text-[12.5px] text-muted-foreground">Chưa ghi vào CDB cho tới khi bấm “Ghi vào CDB”.</div>
          </Hop>
        );
      })()}
    </div>
  );
}
