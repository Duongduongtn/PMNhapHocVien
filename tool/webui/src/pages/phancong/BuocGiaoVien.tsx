import { useMemo, useState, type ReactNode } from "react";
import { Icon } from "../../components/Icon";
import { boDau, ymdToVN } from "../../lib/format";
import type { BanNhapPC, GiaoVienPC, KhoaPC, MonPC, VanDePC } from "../../lib/api";

// PCG-01 — Bước ① chọn giáo viên của khóa (kèm thao tác hàng loạt). Bám ui-mock/phancong.html.
// Chỉ sửa BẢN NHÁP ở trình duyệt; ghi CDB làm ở task 90. Luật cảnh báo mirror phancong_rules.py
// (lệch hạng, đang dạy khóa khác) để hiện huy hiệu/hộp xem trước; server vẫn kiểm lại khi ghi.

const LOAI_NHAN: Record<string, string> = { LT: "Lý thuyết", TH: "Thực hành", AL: "Lý thuyết + Thực hành" };

function homNay(): string {
  const d = new Date();
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

/** Các khóa khác GV còn đang dạy (chưa bế giảng) — gộp theo khóa. */
function khoaDangDay(g: GiaoVienPC): { khoa: string; bg: string }[] {
  const nay = homNay();
  const m = new Map<string, string>();
  for (const b of g.ban as { khoa?: string; bg?: string }[]) {
    if (b.khoa && b.bg && b.bg >= nay && !m.has(b.khoa)) m.set(b.khoa, b.bg);
  }
  return [...m].map(([khoa, bg]) => ({ khoa, bg }));
}

// Lệch hạng chỉ có nghĩa khi GV dạy THỰC HÀNH (loại TH/AL); GV lý thuyết không cần cảnh báo hạng.
// Server quyết hợp hạng (`hop_hang`, bảng B/C1 theo dữ liệu thật) — UI không tự tính.
function lechHang(g: GiaoVienPC, _khoa: KhoaPC): boolean {
  return g.hop_hang === false && (g.loai === "TH" || g.loai === "AL");
}

function canhBao(g: GiaoVienPC, khoa: KhoaPC): string[] {
  const w: string[] = [];
  if (lechHang(g, khoa)) w.push(`Chỉ được dạy hạng ${g.hang_duoc_day.join(", ")}, khóa này là hạng ${khoa.hang_nhom}.`);
  for (const k of khoaDangDay(g)) w.push(`Đang dạy khóa ${k.khoa}, bế giảng ${ymdToVN(k.bg)}.`);
  return w;
}

const ddmm = (ymd: string) => `${ymd.slice(8, 10)}/${ymd.slice(5, 7)}`;

export function HuyHieu({ g, khoa }: { g: GiaoVienPC; khoa: KhoaPC }) {
  const dang = khoaDangDay(g);
  return (
    <>
      <span
        title={LOAI_NHAN[g.loai] ?? g.loai}
        className={"px-1.5 rounded text-[11px] font-semibold shrink-0 " + (g.loai === "TH" ? "bg-pc-soft text-pc" : "bg-muted text-muted-foreground")}
      >
        {g.loai}
      </span>
      {!g.active && <span className="px-1.5 rounded text-[11px] font-semibold bg-destructive/10 text-destructive whitespace-nowrap">Đã ngừng</span>}
      {lechHang(g, khoa) && (
        <span title={`Chỉ được dạy hạng ${g.hang_duoc_day.join(", ")}`} className="px-1.5 rounded text-[11px] font-semibold bg-warning/10 text-warning whitespace-nowrap">
          Hạng {g.hang_duoc_day.join("/")}
        </span>
      )}
      {dang.length > 0 && (
        <span
          title={dang.map((k) => `Đang dạy khóa ${k.khoa} đến ${ymdToVN(k.bg)}`).join("; ")}
          className="px-1.5 rounded text-[11px] font-semibold bg-warning/10 text-warning whitespace-nowrap truncate max-w-[170px]"
        >
          Đang ở {dang[0].khoa} đến {ddmm(dang[0].bg)}
        </span>
      )}
    </>
  );
}

function Hop({ tieuDe, children, chan, dong, rong = "max-w-[620px]" }: { tieuDe: string; children: ReactNode; chan?: ReactNode; dong: () => void; rong?: string }) {
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center p-4 bg-black/40" role="dialog" aria-modal="true" aria-label={tieuDe}>
      <div className={`w-full ${rong} max-h-[85vh] flex flex-col rounded-lg bg-card border border-border shadow-xl`}>
        <div className="px-5 py-3 border-b border-border flex items-center">
          <h3 className="text-[15px] font-semibold">{tieuDe}</h3>
          <button onClick={dong} aria-label="Đóng" className="ml-auto w-8 h-8 rounded-md hover:bg-muted inline-flex items-center justify-center">
            <Icon name="x" className="w-4 h-4" />
          </button>
        </div>
        <div className="px-5 py-4 overflow-auto space-y-2">{children}</div>
        <div className="px-5 py-3 border-t border-border flex justify-end gap-2">{chan}</div>
      </div>
    </div>
  );
}

type HopDangMo = { loai: "them1"; ma: string } | { loai: "themN" } | { loai: "go"; ds: string[] } | null;

export default function BuocGiaoVien({
  khoa, danhMuc, mon, ban, setBan, vande,
}: {
  khoa: KhoaPC;
  danhMuc: GiaoVienPC[];
  mon: MonPC[];
  ban: BanNhapPC;
  setBan: (f: (b: BanNhapPC) => BanNhapPC) => void;
  vande: VanDePC[];
}) {
  const [q, setQ] = useState("");
  const [loai, setLoai] = useState("");
  const [chonPool, setChonPool] = useState<string[]>([]);
  const [chonKhoa, setChonKhoa] = useState<string[]>([]);
  const [hop, setHop] = useState<HopDangMo>(null);

  const theoMa = useMemo(() => new Map(danhMuc.map((g) => [g.ma, g])), [danhMuc]);
  const tenMon = useMemo(() => new Map(mon.map((m) => [m.id, m.ten])), [mon]);
  const trongKhoa = useMemo(() => new Set(ban.gv_khoa), [ban.gv_khoa]);

  const pool = useMemo(() => {
    const k = boDau(q.toLowerCase());
    return danhMuc.filter(
      (g) => !trongKhoa.has(g.ma) && (!loai || g.loai === loai) && (boDau(g.ten.toLowerCase()).includes(k) || g.ma.toLowerCase().includes(k)),
    );
  }, [danhMuc, trongKhoa, q, loai]);

  const hopHang = useMemo(
    () => pool.filter((g) => g.active && (g.loai === "TH" || g.loai === "AL") && !lechHang(g, khoa) && khoaDangDay(g).length === 0).map((g) => g.ma),
    [pool, khoa],
  );

  const gvKhoa = ban.gv_khoa.map((ma) => theoMa.get(ma) ?? ({ ma, ten: ma, loai: "", active: true, hang_gplx: "", hang_duoc_day: [], ban: [] } as GiaoVienPC));
  // Dữ liệu cũ: có phân công/ghép xe cho GV chưa thuộc danh sách khóa → hiện đỏ, kèm nút thêm.
  const ngoaiDs = useMemo(
    () => [...new Set([...ban.pc.map((p) => p.ma), ...ban.ghep.map((m) => m.ma)])].filter((ma) => ma && !trongKhoa.has(ma)),
    [ban.pc, ban.ghep, trongKhoa],
  );

  function them(mas: string[]) {
    setBan((b) => ({ ...b, gv_khoa: [...b.gv_khoa, ...mas.filter((m) => !b.gv_khoa.includes(m))] }));
    setChonPool((c) => c.filter((m) => !mas.includes(m)));
  }
  function go(mas: string[]) {
    setBan((b) => ({
      ...b,
      gv_khoa: b.gv_khoa.filter((m) => !mas.includes(m)),
      pc: b.pc.filter((p) => !mas.includes(p.ma)),
      ghep: b.ghep.filter((m) => !mas.includes(m.ma)),
    }));
    setChonKhoa([]);
  }
  const bat = (ds: string[], ma: string) => (ds.includes(ma) ? ds.filter((x) => x !== ma) : [...ds, ma]);

  const tomPc = (ma: string) => ban.pc.filter((p) => p.ma === ma);
  const tenCuaMon = (ids: number[]) => ids.map((i) => tenMon.get(i) ?? `môn ${i}`).join(" + ") || "chưa chọn môn";

  const danhMucRong = danhMuc.length === 0;

  return (
    <div>
      {khoa.da_dkkh && (
        <div className="mb-3 rounded-md border-l-4 border-warning bg-warning/10 px-3 py-2 text-[13px]">
          <b>Khóa đã gửi đăng ký khóa học (DKKH).</b> Vẫn sửa được, nhưng thay đổi giáo viên có thể không được Sở cập nhật theo.
        </div>
      )}
      {danhMucRong && (
        <div className="mb-3 rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-[13px]">
          Cơ sở chưa có danh mục giáo viên — hãy đồng bộ danh mục giáo viên từ phần mềm CDB trước.
        </div>
      )}

      {ngoaiDs.length > 0 && (
        <div className="mb-3 rounded-md border border-destructive/40 bg-destructive/5 px-3 py-2 text-[13px] flex flex-wrap items-center gap-2">
          <Icon name="warn" className="w-4 h-4 text-destructive shrink-0" />
          <span>
            <b>Ngoài danh sách khóa:</b> {ngoaiDs.map((m) => theoMa.get(m)?.ten ?? m).join(", ")} đã có phân công nhưng chưa thuộc GV của khóa.
          </span>
          <button onClick={() => them(ngoaiDs)} className="ml-auto h-8 px-3 rounded-md bg-pc text-white text-[12.5px] font-semibold">
            Thêm GV vào khóa
          </button>
        </div>
      )}

      {chonPool.length > 0 && (
        <div className="mb-2 rounded-lg border border-pc-border bg-pc-soft px-3 py-2 flex items-center gap-3 text-[13.5px]">
          <b>Đã chọn {chonPool.length} GV</b>
          <button onClick={() => setChonPool([])} className="text-[12.5px] text-muted-foreground underline">Bỏ chọn</button>
          <button onClick={() => setHop({ loai: "themN" })} className="ml-auto h-9 px-4 rounded-lg bg-pc text-white font-semibold text-[13px]">
            Thêm {chonPool.length} GV vào khóa
          </button>
        </div>
      )}
      {chonKhoa.length > 0 && (
        <div className="mb-2 rounded-lg border border-destructive/40 bg-destructive/5 px-3 py-2 flex items-center gap-3 text-[13.5px]">
          <b>Đã chọn {chonKhoa.length} GV của khóa</b>
          <button onClick={() => setChonKhoa([])} className="text-[12.5px] text-muted-foreground underline">Bỏ chọn</button>
          <button onClick={() => setHop({ loai: "go", ds: chonKhoa })} className="ml-auto h-9 px-4 rounded-lg bg-destructive text-white font-semibold text-[13px]">
            Gỡ {chonKhoa.length} GV khỏi khóa
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-[340px_1fr] gap-3">
        {/* Danh mục GV đang hoạt động (kho để chọn — gọn) */}
        <section className="rounded-lg border border-border bg-card" aria-label="Giáo viên đang hoạt động">
          <div className="px-2.5 py-2 border-b border-border flex items-center gap-1.5 flex-wrap">
            <div className="text-[13px] font-bold">
              GV đang hoạt động <span className="text-muted-foreground font-medium">({pool.filter((g) => g.active).length})</span>
            </div>
            <select
              value={loai}
              onChange={(e) => setLoai(e.target.value)}
              aria-label="Lọc theo loại giáo viên"
              className="ml-auto h-8 w-[170px] rounded-md border border-border bg-background text-[12.5px] px-1.5"
            >
              <option value="">Mọi loại</option>
              {["TH", "LT", "AL"].map((l) => (
                <option key={l} value={l}>{l} — {LOAI_NHAN[l]}</option>
              ))}
            </select>
          </div>
          <div className="px-2.5 py-1.5 border-b border-border flex items-center gap-2">
            <div className="relative flex-1">
              <Icon name="search" className="w-3.5 h-3.5 absolute left-2 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Tên / mã GV"
                className="w-full h-8 pl-7 pr-2 rounded-md border border-border bg-background text-[13px] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pc"
              />
            </div>
            <button
              onClick={() => setChonPool((c) => [...new Set([...c, ...hopHang])])}
              disabled={hopHang.length === 0}
              title="Chọn mọi GV thực hành đang hoạt động, hợp hạng, không chạy khóa khác"
              className="h-8 px-2 rounded-md border border-pc-border text-pc text-[12px] font-semibold hover:bg-pc-soft whitespace-nowrap disabled:opacity-40"
            >
              Chọn GV TH hợp hạng ({hopHang.length})
            </button>
          </div>
          <ul className="max-h-[330px] overflow-auto">
            {pool.length === 0 && (
              <li className="px-3 py-8 text-center text-[13px] text-muted-foreground">
                {danhMucRong ? "Chưa có giáo viên nào." : "Không có giáo viên nào khớp."}
              </li>
            )}
            {pool.map((g) => (
              <li key={g.ma} className={"px-2.5 h-10 flex items-center gap-2 " + (chonPool.includes(g.ma) ? "bg-pc-soft" : "hover:bg-muted/50")}>
                <input
                  type="checkbox"
                  aria-label={`Chọn ${g.ten}`}
                  checked={chonPool.includes(g.ma)}
                  disabled={!g.active}
                  onChange={() => setChonPool((c) => bat(c, g.ma))}
                />
                <span className="text-[13px] font-medium truncate w-[104px] shrink-0" title={`${g.ten} · ${g.ma}`}>{g.ten}</span>
                <span className="flex gap-1 min-w-0 overflow-hidden"><HuyHieu g={g} khoa={khoa} /></span>
                <button
                  disabled={!g.active}
                  onClick={() => (canhBao(g, khoa).length ? setHop({ loai: "them1", ma: g.ma }) : them([g.ma]))}
                  className="ml-auto shrink-0 h-7 px-2 rounded-md border border-pc-border text-pc text-[12px] font-semibold hover:bg-pc-soft disabled:opacity-40"
                >
                  Thêm
                </button>
              </li>
            ))}
          </ul>
        </section>

        {/* GV của khóa */}
        <section className="rounded-lg border border-pc-border bg-card" aria-label="Giáo viên của khóa">
          <div className="px-3 py-2 border-b border-pc-border bg-pc-soft rounded-t-lg text-[13.5px] font-bold text-pc">
            Giáo viên của khóa <span className="font-medium">({gvKhoa.length})</span>
          </div>
          <ul className="max-h-[420px] overflow-auto">
            {gvKhoa.length === 0 && (
              <li className="px-3 py-12 text-center text-[13px] text-muted-foreground">
                Chưa chọn giáo viên nào. Tích hoặc bấm “Thêm” ở danh sách bên trái.
              </li>
            )}
            {gvKhoa.map((g) => {
              const np = tomPc(g.ma).length;
              const coXe = ban.ghep.some((m) => m.ma === g.ma);
              return (
                <li id={`gv-${g.ma}`} key={g.ma} className={"px-3 py-1.5 flex items-center gap-2.5 flex-wrap " + (chonKhoa.includes(g.ma) ? "bg-destructive/5" : "hover:bg-muted/50")}>
                  <input
                    type="checkbox"
                    aria-label={`Chọn ${g.ten}`}
                    checked={chonKhoa.includes(g.ma)}
                    onChange={() => setChonKhoa((c) => bat(c, g.ma))}
                  />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="text-[13.5px] font-medium truncate">{g.ten}</span>
                      <span className="flex gap-1 shrink-0"><HuyHieu g={g} khoa={khoa} /></span>
                    </div>
                    <div className="text-[12px] text-muted-foreground">
                      <span className="font-mono">{g.ma}</span> · {np} phân công
                      {g.loai === "TH" || g.loai === "AL" ? (coXe ? " · có xe" : <b className="text-warning"> · chưa xe</b>) : null}
                    </div>
                  </div>
                  <button onClick={() => setHop({ loai: "go", ds: [g.ma] })} className="shrink-0 h-7 px-2 rounded-md border border-border text-[12px] hover:bg-muted">
                    Gỡ
                  </button>
                  {vande
                    .filter((v) => v.ref === `gv-${g.ma}` && v.buoc === 1 && v.muc !== "thong_tin")
                    .map((v, i) => (
                      <div
                        key={i}
                        className={
                          "basis-full ml-6 rounded-md border-l-4 px-2.5 py-1.5 text-[13px] " +
                          (v.muc === "chan" ? "border-destructive bg-destructive/5" : "border-warning bg-warning/10")
                        }
                      >
                        {v.noi_dung}
                      </div>
                    ))}
                </li>
              );
            })}
          </ul>
        </section>
      </div>

      <p className="text-[12.5px] text-muted-foreground mt-3 flex items-start gap-1.5">
        <Icon name="info" className="w-4 h-4 shrink-0 mt-0.5" />
        Danh sách giáo viên lấy từ danh mục của cơ sở (do Sở tiếp nhận). Tool không thêm/sửa giáo viên — chỉ chọn vào khóa.
      </p>

      {/* Thêm từng GV có cảnh báo */}
      {hop?.loai === "them1" && (() => {
        const g = theoMa.get(hop.ma);
        if (!g) return null;
        return (
          <Hop
            tieuDe={`Thêm ${g.ten} vào khóa?`}
            dong={() => setHop(null)}
            rong="max-w-[540px]"
            chan={<>
              <button onClick={() => setHop(null)} className="h-9 px-4 rounded-md border border-border text-[13px]">Không thêm</button>
              <button onClick={() => { them([g.ma]); setHop(null); }} className="h-9 px-4 rounded-md bg-pc text-white text-[13px] font-semibold">Vẫn thêm vào khóa</button>
            </>}
          >
            {canhBao(g, khoa).map((w) => (
              <div key={w} className="rounded-md border-l-4 border-warning bg-warning/10 px-3 py-2 text-[13px]">{w}</div>
            ))}
            <p className="text-[13px] text-muted-foreground pt-1">Vẫn thêm được. Khi phân công, hệ thống sẽ chặn nếu trùng thời gian với khóa kia.</p>
          </Hop>
        );
      })()}

      {/* Thêm N GV — xem trước từng GV */}
      {hop?.loai === "themN" && (() => {
        const rows = chonPool.map((m) => theoMa.get(m)).filter((g): g is GiaoVienPC => !!g);
        const ok = rows.filter((g) => g.active);
        return (
          <Hop
            tieuDe={`Thêm ${rows.length} giáo viên vào khóa`}
            dong={() => setHop(null)}
            chan={<>
              <button onClick={() => setHop(null)} className="h-9 px-4 rounded-md border border-border text-[13px]">Hủy</button>
              <button
                disabled={ok.length === 0}
                onClick={() => { them(ok.map((g) => g.ma)); setHop(null); }}
                className="h-9 px-4 rounded-md bg-pc text-white text-[13px] font-semibold disabled:opacity-40"
              >
                Thêm {ok.length} GV
              </button>
            </>}
          >
            <ul className="rounded-lg border border-border divide-y divide-border/60 max-h-72 overflow-auto">
              {rows.map((g) => {
                const w = canhBao(g, khoa);
                const hong = !g.active;
                return (
                  <li key={g.ma} className="px-3 py-2 flex items-start gap-2">
                    <Icon name={hong ? "x" : w.length ? "warn" : "check"} className={"w-[18px] h-[18px] mt-0.5 " + (hong ? "text-destructive" : w.length ? "text-warning" : "text-success")} />
                    <div>
                      <div className="text-[13.5px] font-medium">{g.ten} <span className="font-mono text-muted-foreground">{g.ma}</span></div>
                      <div className={"text-[12.5px] " + (hong ? "text-destructive" : "text-muted-foreground")}>
                        {hong ? "Đã ngừng hoạt động — không thêm được." : w.length ? w.join(" ") : "Hợp lệ."}
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>
            <p className="text-[13px]">
              Sẽ thêm <b>{ok.length}</b> GV{rows.length - ok.length > 0 && <>, bỏ qua <b>{rows.length - ok.length}</b></>}. GV có cảnh báo vẫn được thêm; lỗi chặn nằm ở lúc phân công.
            </p>
          </Hop>
        );
      })()}

      {/* Gỡ GV — liệt kê hậu quả */}
      {hop?.loai === "go" && (() => {
        const rows = hop.ds.map((ma) => ({ g: theoMa.get(ma), ma, pc: tomPc(ma), gh: ban.ghep.filter((m) => m.ma === ma) }));
        const tong = rows.reduce((s, r) => s + r.pc.length + r.gh.length, 0);
        return (
          <Hop
            tieuDe={`Gỡ ${rows.length} giáo viên khỏi khóa?`}
            dong={() => setHop(null)}
            chan={<>
              <button onClick={() => setHop(null)} className="h-9 px-4 rounded-md border border-border text-[13px]">Giữ lại</button>
              <button
                onClick={() => { go(hop.ds); setHop(null); }}
                className="h-9 px-4 rounded-md bg-destructive text-white text-[13px] font-semibold"
              >
                Gỡ {rows.length} GV{tong > 0 ? ` và xóa ${tong} mục` : ""}
              </button>
            </>}
          >
            {tong > 0 ? (
              <div className="rounded-md border-l-4 border-destructive bg-destructive/5 px-3 py-2 text-[13px]">
                Việc này xóa luôn <b>{tong}</b> mục phân công / ghép xe của các GV dưới đây (chỉ trong khóa này).
              </div>
            ) : (
              <div className="rounded-md border-l-4 border-primary bg-primary/5 px-3 py-2 text-[13px]">
                Các GV này chưa có phân công hay ghép xe — gỡ không mất gì.
              </div>
            )}
            <ul className="rounded-lg border border-border divide-y divide-border/60 max-h-64 overflow-auto">
              {rows.map((r) => (
                <li key={r.ma} className="px-3 py-2">
                  <div className="text-[13.5px] font-medium">{r.g?.ten ?? r.ma}</div>
                  <div className="text-[12.5px] text-muted-foreground">
                    {r.pc.length
                      ? r.pc.map((p) => `${tenCuaMon(p.mon)} (${ymdToVN(p.tu.slice(0, 10))} → ${ymdToVN(p.den.slice(0, 10))})`).join("; ")
                      : "Không có phân công"}
                    {r.gh.length > 0 && ` · ghép xe ${r.gh.map((m) => m.xe).join(", ")}`}
                  </div>
                </li>
              ))}
            </ul>
            <p className="text-[12.5px] text-muted-foreground">Chưa ghi vào CDB cho tới khi bấm “Ghi vào CDB”.</p>
          </Hop>
        );
      })()}
    </div>
  );
}
