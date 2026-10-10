import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Icon } from "../../components/Icon";
import { ymdToVN } from "../../lib/format";
import { goiYGhepXe, kiemTraPC, type BanNhapPC, type GhepDong, type GiaoVienPC, type GoiYGhepXe, type KhoaPC, type VanDePC, type XePC } from "../../lib/api";
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

const ddmm = (iso: string) => `${iso.slice(8, 10)}/${iso.slice(5, 7)}`;

/** Các khóa khác mà xe có lịch CHỒNG GIỜ với [tu, den) — nửa mở, chạm đầu mút / cùng ngày khác giờ không tính. */
function trungKhoaKhac(x: XePC | undefined, tu: string, den: string): string[] {
  if (!x || !tu || !den) return [];
  return (x.ban as { khoa?: string; tu?: string; den?: string }[])
    .filter((b) => b.khoa && b.tu && b.den && !(den <= b.tu || tu >= b.den))
    .map((b) => `${b.khoa} (${ddmm(b.tu as string)} → ${ddmm(b.den as string)})`);
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
  khoa, danhMuc, xeDm, ban, setBan, vande, targetKey,
}: {
  khoa: KhoaPC;
  danhMuc: GiaoVienPC[];
  xeDm: XePC[];
  ban: BanNhapPC;
  setBan: (f: (b: BanNhapPC) => BanNhapPC) => void;
  vande: VanDePC[];
  targetKey: string;
}) {
  const theoXe = useMemo(() => new Map(xeDm.map((x) => [x.bs, x])), [xeDm]);
  const theoGv = useMemo(() => new Map(danhMuc.map((g) => [g.ma, g])), [danhMuc]);
  const [poolMo, setPoolMo] = useState(false);
  const [q, setQ] = useState("");
  const [doiXe, setDoiXe] = useState<{ ma: string; xe: string } | null>(null);
  const [goXe, setGoXe] = useState<string | null>(null);
  const [goiY, setGoiY] = useState<{ dong: (GoiYGhepXe & { on: boolean })[] } | "tai" | { loi: string } | null>(null);
  const [kiemGoiY, setKiemGoiY] = useState<VanDePC[]>([]);
  const [busyGoiY, setBusyGoiY] = useState(false);
  const dem = useRef(0);

  const khoangTh = (ma: string) => {
    const th = ban.pc.filter((p) => p.ma === ma && p.mon.includes(MON_TH));
    return th.length
      ? { tu: th.map((p) => p.tu).sort()[0], den: th.map((p) => p.den).sort().pop() as string }
      : { tu: "", den: "" };
  };
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

  const chuaXe = dsGv.filter((ma) => !ghepCua(ma)?.xe && ban.pc.some((p) => p.ma === ma && p.mon.includes(MON_TH)));

  async function moGoiY() {
    setGoiY("tai");
    try {
      const r = await goiYGhepXe(khoa.ma_kh, ban, targetKey);
      setGoiY({ dong: r.goi_y.map((g) => ({ ...g, on: !!g.xe })) });
    } catch (e) {
      setGoiY({ loi: (e as Error).message });
    }
  }
  function suaGoiY(i: number, f: Partial<GoiYGhepXe & { on: boolean }>) {
    setGoiY((g) => (g && typeof g === "object" && "dong" in g ? { dong: g.dong.map((d, k) => (k === i ? { ...d, ...f } : d)) } : g));
  }
  const dongGoiY = goiY && typeof goiY === "object" && "dong" in goiY ? goiY.dong : null;
  const khoaGoiY = JSON.stringify(dongGoiY?.map((d) => [d.ma, d.xe, d.on]) ?? null);
  useEffect(() => {
    if (!dongGoiY) { setKiemGoiY([]); return; }
    const chon = dongGoiY.filter((d) => d.xe);
    if (chon.length === 0) { setKiemGoiY([]); return; }
    let huy = false;
    setBusyGoiY(true);
    const h = setTimeout(() => {
      const them: GhepDong[] = chon.map((d) => ({ id: `g-${d.ma}`, ma: d.ma, xe: d.xe, tu: d.tu, den: d.den, dia_diem: "" }));
      kiemTraPC(khoa.ma_kh, { ...ban, ghep: [...ban.ghep, ...them] }, targetKey)
        .then((r) => { if (!huy) setKiemGoiY(r.vande); })
        .catch(() => { if (!huy) setKiemGoiY([]); })
        .finally(() => { if (!huy) setBusyGoiY(false); });
    }, 250);
    return () => { huy = true; clearTimeout(h); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [khoaGoiY]);
  const xeCoDinh = new Set(ban.ghep.filter((m) => m.xe).map((m) => m.xe));

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

      <div className="mb-2 flex items-center gap-2">
        <div className="text-[13.5px] text-muted-foreground">
          Mỗi <b className="text-foreground">giáo viên thực hành</b> ghép <b className="text-foreground">1 xe</b>. Địa điểm mặc định: <i>{DIA_DIEM_GOI_Y}</i>.
        </div>
        <button
          disabled={chuaXe.length === 0 || ban.xe_khoa.length === 0}
          onClick={moGoiY}
          className="ml-auto h-9 px-3 rounded-lg border border-pc-border text-pc text-[13px] font-semibold hover:bg-pc-soft disabled:opacity-40 disabled:cursor-not-allowed whitespace-nowrap"
        >
          Gợi ý ghép xe ({chuaXe.length} GV)
        </button>
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
                      const kk = trungKhoaKhac(theoXe.get(bs), m?.tu ?? khoangTh(ma).tu, m?.den ?? khoangTh(ma).den);
                      const ghi = [
                        khac ? `đang ghép ${theoGv.get(u as string)?.ten ?? u}` : "",
                        kk.length ? `trùng giờ khóa ${kk[0]}${kk.length > 1 ? ` +${kk.length - 1}` : ""}` : "",
                      ].filter(Boolean).join("; ");
                      return (
                        <option key={bs} value={bs}>
                          {bs}{ghi ? ` — ⚠ ${ghi}` : ""}
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
                    {trungKhoaKhac(theoXe.get(m.xe), m.tu, m.den).length > 0 && (
                      <div className={`mt-1 rounded-md border-l-4 px-2.5 py-1.5 text-[13px] ${lopMuc("canh_bao")}`}>
                        Xe trùng giờ với khóa {trungKhoaKhac(theoXe.get(m.xe), m.tu, m.den).join(", ")}. Vẫn ghép được — chỉ để bạn biết.
                      </div>
                    )}
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

      {goiY && (
        <Hop
          tieuDe="Gợi ý ghép xe — xem và duyệt từng dòng"
          rong="max-w-[720px]"
          dong={() => setGoiY(null)}
          chan={<>
            <button onClick={() => setGoiY(null)} className="h-9 px-4 rounded-md border border-border text-[13px]">Hủy</button>
            {(() => {
              const ok = (dongGoiY ?? []).filter((d) => d.on && d.xe && !kiemGoiY.some((v) => v.ref === `gh-${d.ma}` && v.muc === "chan"));
              return (
                <button
                  disabled={ok.length === 0 || busyGoiY}
                  onClick={() => {
                    const moi: GhepDong[] = ok.map((d) => ({ id: `n${Date.now().toString(36)}${++dem.current}`, ma: d.ma, xe: d.xe, tu: d.tu, den: d.den, dia_diem: "" }));
                    setBan((b) => ({ ...b, ghep: [...b.ghep.filter((m) => !moi.some((x) => x.ma === m.ma)), ...moi] }));
                    setGoiY(null);
                  }}
                  className="h-9 px-4 rounded-md bg-pc text-white text-[13px] font-semibold disabled:opacity-40"
                >
                  Áp {ok.length} gợi ý vào bản nháp
                </button>
              );
            })()}
          </>}
        >
          <div className="rounded-md border-l-4 border-primary bg-primary/5 px-3 py-2 text-[13px]">
            Gợi ý theo xe còn trống, đã thuộc khóa, hợp giấy phép và ưu tiên đúng hạng. Chưa ghi gì cho tới khi bạn bấm “Áp”.
          </div>
          {goiY === "tai" && <div className="text-[13px] text-muted-foreground flex items-center gap-2"><Icon name="refresh" className="w-4 h-4 animate-spin" /> Đang tìm xe phù hợp…</div>}
          {typeof goiY === "object" && "loi" in goiY && <div className="text-[13px] text-destructive">{goiY.loi}</div>}
          {dongGoiY && (
            <ul className="rounded-lg border border-border divide-y divide-border/60 max-h-80 overflow-auto">
              {dongGoiY.length === 0 && <li className="px-3 py-6 text-center text-[13px] text-muted-foreground">Không có GV nào cần ghép.</li>}
              {dongGoiY.map((d, i) => {
                const vs = kiemGoiY.filter((v) => v.ref === `gh-${d.ma}` && v.muc !== "thong_tin");
                const chan = vs.some((v) => v.muc === "chan");
                const dungBoiDong = new Set(dongGoiY.filter((_, k) => k !== i).map((x) => x.xe).filter(Boolean));
                return (
                  <li key={d.ma} className="px-3 py-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <input
                        type="checkbox"
                        aria-label={`Dùng gợi ý cho ${d.ten}`}
                        checked={d.on && !!d.xe && !chan}
                        disabled={!d.xe || chan}
                        onChange={(e) => suaGoiY(i, { on: e.target.checked })}
                      />
                      <span className="text-[13.5px] font-medium w-[170px] truncate">{d.ten}</span>
                      <select
                        aria-label={`Xe gợi ý cho ${d.ten}`}
                        value={d.xe}
                        onChange={(e) => suaGoiY(i, { xe: e.target.value, on: !!e.target.value })}
                        className="h-9 w-[200px] rounded-md border border-border bg-background px-2 text-sm"
                      >
                        <option value="">— không gợi ý được —</option>
                        {ban.xe_khoa.filter((bs) => !xeCoDinh.has(bs) && !dungBoiDong.has(bs)).map((bs) => (
                          <option key={bs} value={bs}>{bs}</option>
                        ))}
                        {d.xe && !ban.xe_khoa.includes(d.xe) ? <option value={d.xe}>{d.xe}</option> : null}
                      </select>
                      <span className="ml-auto text-[12px] text-muted-foreground tabular-nums">
                        {ymdToVN(dP(d.tu))} → {ymdToVN(dP(d.den))}
                      </span>
                    </div>
                    {!d.xe && d.ly_do && <div className="mt-1 ml-7 text-[12.5px] text-muted-foreground">{d.ly_do}</div>}
                    {d.canh_bao.filter(() => d.xe && vs.length === 0).map((c, k) => (
                      <div key={k} className={`mt-1 ml-7 rounded-md border-l-4 px-2.5 py-1.5 text-[13px] ${lopMuc("canh_bao")}`}>{c}</div>
                    ))}
                    {vs.map((v, k) => (
                      <div key={k} className={`mt-1 ml-7 rounded-md border-l-4 px-2.5 py-1.5 text-[13px] ${lopMuc(v.muc)}`}>{v.noi_dung}</div>
                    ))}
                  </li>
                );
              })}
            </ul>
          )}
        </Hop>
      )}

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
