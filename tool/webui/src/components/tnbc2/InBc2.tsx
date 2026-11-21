import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import OPhanThi, { OMau } from "./OPhanThi";
import XemTruocBc2 from "./XemTruocBc2";
import { banInBc2, luuNoiDungThi, type BanInResp, type HvBanIn } from "../../lib/tnbc2Api";
import {
  chuGiaiO, demTheoMuc, doiPhan, doiPhanLoat, locHocVien, ngayNguon, TEN_PHAN, trangThaiChung, type LocNoiDung,
} from "../../lib/phanThi";

// TNB-08 — màn "In Báo cáo 2": mỗi dòng hiện sẵn các ô phần thi (điền sẵn theo dữ liệu), bấm ô để đổi, cột
// "Ghi chú khi in" ra tên mục tương ứng (do server tính). Tự lưu trong tool; không ghi DB Nạp. Bám ui-mock/inbc2.html.

const nutNho = "h-9 px-3 rounded-lg border border-input bg-white text-[13px] font-semibold hover:bg-muted disabled:opacity-45 disabled:cursor-not-allowed inline-flex items-center justify-center gap-1.5 whitespace-nowrap";
const gio = () => new Date().toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" });
const coM = (s: string) => /(^|[ +(])M([ +)]|$)/.test(s);   // phần mềm cũ còn tính phần mô phỏng (bỏ từ 01/07/2025)

const icMat = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"
    strokeLinejoin="round" aria-hidden="true"><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" /><circle cx="12" cy="12" r="3" /></svg>
);
const icCanh = (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"
    strokeLinejoin="round" aria-hidden="true"><path d="M12 9v4m0 4h.01" /><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z" /></svg>
);
const icVe = (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"
    strokeLinejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 3-6.7L3 8" /><path d="M3 3v5h5" /></svg>
);

function KyHieu({ phan, phaiThi }: { phan: string[]; phaiThi: string[] }) {
  return (
    <span className="inline-flex gap-0.5" aria-hidden="true">
      {phan.map((p) => (
        <i key={p} className={`not-italic min-w-[20px] h-5 px-1 rounded text-[10.5px] font-bold inline-grid place-items-center ${
          phaiThi.includes(p) ? "bg-tn text-white" : "text-muted-foreground/60 ring-1 ring-inset ring-border"}`}>{p}</i>
      ))}
    </span>
  );
}

export default function InBc2({ maBc2, onVe }: { maBc2: string; onVe: () => void }) {
  const [dl, setDl] = useState<BanInResp | null>(null);
  const [loi, setLoi] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [loc, setLoc] = useState<LocNoiDung>("tat");
  const [chon, setChon] = useState<Set<string>>(new Set());
  const [luu, setLuu] = useState("");
  const [buoc, setBuoc] = useState<"chon" | "xem">("chon");
  const seq = useRef(0);
  const hang = useRef<Promise<unknown>>(Promise.resolve());   // PUT chạy lần lượt theo thứ tự bấm (server xử lý song song)
  const [dangLuu, setDangLuu] = useState(0);

  const tai = useCallback(() => {
    banInBc2(maBc2)
      .then((d) => { setDl(d); setLoi(null); })
      .catch((e: unknown) => setLoi(e instanceof Error ? e.message : "Không tải được dữ liệu in BC2"));
  }, [maBc2]);
  useEffect(() => { tai(); }, [tai]);

  const ap = useCallback(async (ds: { ma_dk: string; phai_thi: string[] | null }[]) => {
    if (ds.length === 0) return;
    // Cập nhật ngay ô đã bấm; tên mục (Ghi chú) lấy từ phản hồi của server — nguồn duy nhất của bảng mục.
    setDl((d) => d && {
      ...d,
      hoc_vien: d.hoc_vien.map((h) => {
        const x = ds.find((y) => y.ma_dk === h.ma_dk);
        if (!x) return h;
        const phai = x.phai_thi ?? h.mac_dinh.phai_thi;
        return { ...h, phai_thi: phai, dat: h.phan.filter((p) => !phai.includes(p)) };
      }),
    });
    const toi = ++seq.current;
    setDangLuu((n) => n + 1);
    // Mỗi lần gửi chờ lần gửi trước xong: DB luôn giữ đúng thứ tự bấm, và phản hồi cuối cùng phản ánh mọi lần bấm.
    const luot = hang.current.then(async () => {
      try {
        const r = await luuNoiDungThi(maBc2, ds);
        if (toi === seq.current) { setDl(r); setLuu(gio()); setLoi(null); }
      } catch (e) {
        if (toi === seq.current) { setLoi(e instanceof Error ? e.message : "Không lưu được lựa chọn"); tai(); }
      } finally {
        setDangLuu((n) => n - 1);
      }
    });
    hang.current = luot;
    await luot;
  }, [maBc2, tai]);

  const hocVien = dl?.hoc_vien ?? [];
  const dem = useMemo(() => demTheoMuc(hocVien), [hocVien]);
  const ds = useMemo(() => locHocVien(hocVien, loc, q), [hocVien, loc, q]);
  const hvChon = useMemo(() => hocVien.filter((h) => chon.has(h.ma_dk)), [hocVien, chon]);
  const phanChung = hvChon.length > 0 && hvChon.every((h) => h.phan.join() === hvChon[0].phan.join()) ? hvChon[0].phan : [];
  const loai = dl?.loai === "moto" ? "mô tô" : "ô tô";
  const tatCaChon = ds.length > 0 && ds.every((h) => chon.has(h.ma_dk));

  if (buoc === "xem" && dl) {
    return <XemTruocBc2 maBc2={maBc2} maKh={dl.ma_kh} soHv={dl.hoc_vien.length} soChonLai={dl.so_chon_lai} onVe={() => setBuoc("chon")} />;
  }

  const doiChon = (ma: string, bat: boolean) => setChon((s) => { const n = new Set(s); if (bat) n.add(ma); else n.delete(ma); return n; });
  const chonHet = () => setChon((s) => { const n = new Set(s); for (const h of ds) { if (tatCaChon) n.delete(h.ma_dk); else n.add(h.ma_dk); } return n; });

  return (
    <div className="h-full flex flex-col min-h-0">
      <div className="shrink-0 bg-card border-b border-border px-4 py-2.5 flex flex-wrap items-center gap-3">
        <button type="button" onClick={onVe} className={nutNho}>← Danh sách BC2</button>
        <div className="min-w-0">
          <div className="text-[11px] text-muted-foreground">In Báo cáo 2 · BC2 {loai}</div>
          <div className="font-semibold text-[15px] tabular-nums">
            {dl?.so_bao_cao || maBc2}
            {dl && <span className="font-normal text-muted-foreground text-[13px]"> · Khóa {dl.ma_kh || "—"} · {hocVien.length} học viên</span>}
          </div>
        </div>
        <input aria-label="Tìm học viên" className="field-input ml-auto" style={{ width: 220 }} value={q}
          placeholder="Tìm tên / số CMT" onChange={(e) => setQ(e.target.value)} />
        <button type="button" onClick={() => setBuoc("xem")} data-testid="nut-xem-truoc"
          disabled={!dl || hocVien.length === 0 || dl.so_can_chon > 0 || dangLuu > 0}
          title={dl && dl.so_can_chon > 0 ? "Còn học viên chưa bật phần thi nào" : dangLuu > 0 ? "Đang lưu lựa chọn…" : undefined}
          className="h-9 px-4 rounded-lg bg-tn text-white text-[13px] font-semibold inline-flex items-center gap-1.5 hover:bg-[hsl(222_76%_34%)] disabled:opacity-45 disabled:cursor-not-allowed">
          {icMat}Xem trước
        </button>
      </div>

      {loi && <div role="alert" className="shrink-0 mx-4 mt-3 rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-[13px] text-destructive">{loi}</div>}
      {!dl && !loi && <div className="p-4 text-[13px] text-muted-foreground">Đang tải…</div>}

      {dl && (
        <>
          <div className="shrink-0 px-4 py-2.5 border-b border-border flex flex-wrap items-center gap-2">
            <span className="text-[12px] text-muted-foreground mr-1">Nội dung thi</span>
            <button type="button" aria-pressed={loc === "tat"} onClick={() => setLoc("tat")}
              className={`h-[30px] px-2.5 rounded-full border text-[12.5px] ${loc === "tat" ? "border-tn bg-tn-soft text-tn font-semibold" : "border-border bg-white"}`}>
              Tất cả <b className="tabular-nums">{hocVien.length}</b>
            </button>
            {dem.nhom.map((n) => (
              <button key={n.khoa} type="button" aria-pressed={loc === n.khoa} onClick={() => setLoc(n.khoa)} data-testid={`dem-${n.khoa}`}
                className={`h-[30px] px-2.5 rounded-full border text-[12.5px] inline-flex items-center gap-1.5 ${loc === n.khoa ? "border-tn bg-tn-soft text-tn font-semibold" : "border-border bg-white"}`}>
                <KyHieu phan={n.phan} phaiThi={n.phaiThi} />{n.ten} <b className="tabular-nums">{n.n}</b>
              </button>
            ))}
            {dem.can > 0 && (
              <button type="button" aria-pressed={loc === "can"} onClick={() => setLoc("can")} data-testid="dem-can"
                className="h-[30px] px-2.5 rounded-full border border-destructive/50 bg-white text-destructive text-[12.5px] inline-flex items-center gap-1.5">
                {icCanh}Chưa có phần thi <b className="tabular-nums">{dem.can}</b>
              </button>
            )}
            {dem.sua > 0 && (
              <button type="button" aria-pressed={loc === "sua"} onClick={() => setLoc("sua")}
                className={`h-[30px] px-2.5 rounded-full border text-[12.5px] ${loc === "sua" ? "border-tn bg-tn-soft text-tn font-semibold" : "border-border bg-white"}`}>
                Đã sửa <b className="tabular-nums">{dem.sua}</b>
              </button>
            )}
            <span className="ml-auto text-[12px] text-muted-foreground" data-testid="trang-thai-luu">
              {dangLuu > 0 ? "Đang lưu… · " : luu ? `Đã lưu ${luu} · ` : ""}Chỉ đổi bản in — DB Nạp và gói gửi Sở không đổi
            </span>
          </div>

          <div className="shrink-0 px-4 py-2 text-[12px] text-muted-foreground flex flex-wrap items-center gap-3 border-b border-border bg-muted/50">
            <span className="inline-flex items-center gap-1.5"><OMau phan={dl.loai === "moto" ? "LT" : "L"} phaiThi /> phải thi</span>
            <span className="inline-flex items-center gap-1.5"><OMau phan={dl.loai === "moto" ? "LT" : "L"} phaiThi={false} /> đã đạt, không thi</span>
            <span>· Bấm một ô để đổi; cột Ghi chú tự đổi theo. {dl.loai === "moto" ? "Mô tô: Lý thuyết · Thực hành." : "Ô tô: Lý thuyết · Sa hình · Đường (không còn mô phỏng từ 01/07/2025)."}</span>
          </div>

          <div className="flex-1 min-h-0 overflow-auto [scrollbar-gutter:stable]">
            {/* Bố cục cố định: bề rộng cột và chiều cao dòng không phụ thuộc nội dung → bật/tắt ô không làm bảng co giãn */}
            <table className="w-full min-w-[1020px] table-fixed text-[13px]">
              <colgroup>
                <col style={{ width: 44 }} /><col style={{ width: 48 }} /><col style={{ width: 230 }} /><col style={{ width: 104 }} />
                <col style={{ width: 130 }} /><col style={{ width: 240 }} /><col />
              </colgroup>
              <thead className="sticky top-0 bg-card border-b border-border z-10">
                <tr className="text-left text-[12px] text-muted-foreground">
                  <th className="w-10 px-3 py-2"><input type="checkbox" className="w-4 h-4 accent-[hsl(222_76%_40%)]" aria-label="Chọn tất cả" checked={tatCaChon} onChange={chonHet} /></th>
                  <th className="py-2 pr-3 w-10 font-semibold">STT</th>
                  <th className="py-2 pr-3 font-semibold">Họ và tên</th>
                  <th className="py-2 pr-3 font-semibold">Ngày sinh</th>
                  <th className="py-2 pr-3 font-semibold">Số CMND</th>
                  <th className="py-2 pr-3 font-semibold">Phần thi <span className="font-normal">(bấm bật/tắt)</span></th>
                  <th className="py-2 pr-3 font-semibold">Ghi chú khi in</th>
                </tr>
              </thead>
              <tbody>
                {ds.length === 0 && <tr><td colSpan={7} className="py-10 text-center text-muted-foreground">Không có học viên khớp bộ lọc.</td></tr>}
                {ds.map((h) => <Dong key={h.ma_dk} h={h} chon={chon.has(h.ma_dk)} onChon={(b) => doiChon(h.ma_dk, b)} ap={ap} />)}
              </tbody>
            </table>
          </div>

          {hvChon.length > 0 && (
            <div className="shrink-0 border-t border-border bg-card px-4 py-2.5 flex flex-wrap items-center gap-3 shadow-[0_-4px_12px_hsl(222_30%_20%/.06)]" data-testid="thanh-chon-nhieu">
              <span className="text-[13px]">Đã chọn <b className="tabular-nums">{hvChon.length}</b> học viên{phanChung.length > 0 ? " — đặt phần thi chung:" : ""}</span>
              {phanChung.length > 0 ? (
                <span className="inline-flex gap-1">
                  {phanChung.map((p) => {
                    const tt = trangThaiChung(hvChon, p);
                    return (
                      <OPhanThi key={p} phan={p} phaiThi={tt !== "dat"} testId={`chung-${p}`}
                        tieuDe={`${TEN_PHAN[p] ?? p}: bấm để ${tt === "dat" ? "bắt thi" : "đánh dấu đã đạt"} cho ${hvChon.length} học viên`}
                        onBam={() => void ap(doiPhanLoat(hvChon, p))} />
                    );
                  })}
                </span>
              ) : <span className="text-[12px] text-muted-foreground">Chọn học viên cùng nhóm hạng để đặt phần thi chung.</span>}
              <button type="button" className={nutNho} onClick={() => { void ap(hvChon.map((h) => ({ ma_dk: h.ma_dk, phai_thi: null }))); setChon(new Set()); }}>
                {icVe}Về mặc định
              </button>
              <button type="button" className={nutNho} onClick={() => setChon(new Set())}>Bỏ chọn</button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function Dong({ h, chon, onChon, ap }: {
  h: HvBanIn; chon: boolean; onChon: (b: boolean) => void;
  ap: (ds: { ma_dk: string; phai_thi: string[] | null }[]) => Promise<void>;
}) {
  const can = h.ma_nd === null;
  const phu = h.da_sua ? "" : h.pm_cu_khac && h.pm_cu
    ? `PM cũ: ${h.pm_cu}${coM(h.pm_cu) && h.nhom !== "moto" ? " — đã bỏ M" : ""}${can ? " — không còn phần nào để thi" : ""}` : "";
  const datTxt = h.dat.length > 0 && !can ? `${h.dat.join(", ")} đạt · ` : "";
  return (
    <tr data-testid={`hv-${h.ma_dk}`} className={`h-[68px] border-b border-border ${chon ? "bg-tn-soft" : ""} ${can ? "bg-destructive/5" : "hover:bg-tn-soft/40"}`}>
      <td className="px-3 py-0"><input type="checkbox" className="w-4 h-4 accent-[hsl(222_76%_40%)]" checked={chon} onChange={(e) => onChon(e.target.checked)} aria-label={`Chọn ${h.ho_ten}`} /></td>
      <td className="py-0 pr-3 tabular-nums text-muted-foreground">{h.stt}</td>
      <td className="py-0 pr-3 font-semibold truncate" title={h.ho_ten}>{h.ho_ten}</td>
      <td className="py-0 pr-3 tabular-nums">{h.ngay_sinh}</td>
      <td className="py-0 pr-3 tabular-nums truncate">{h.so_cmt}</td>
      <td className="py-0 pr-3">
        <div className="flex gap-1 h-7">
          {h.phan.map((p) => (
            <OPhanThi key={p} phan={p} phaiThi={h.phai_thi.includes(p)} testId={`phan-${h.ma_dk}-${p}`}
              tieuDe={chuGiaiO(h, p, TEN_PHAN)} onBam={() => void ap([{ ma_dk: h.ma_dk, phai_thi: doiPhan(h, p) }])} />
          ))}
        </div>
        <div className="text-[11px] text-muted-foreground mt-1 h-4 leading-4 truncate" title={`${datTxt}${h.ten_nguon}`}>{datTxt}{h.ten_nguon}{ngayNguon(h) ? ` · ${ngayNguon(h)}` : ""}</div>
      </td>
      <td className="py-0 pr-3">
        <div className="flex items-center gap-2 h-7 min-w-0">
          {can ? (
            <span className="inline-flex items-center gap-1.5 text-destructive font-semibold truncate" data-testid={`ghi-chu-${h.ma_dk}`}>{icCanh}Phải bật ít nhất 1 phần</span>
          ) : (
            <span className="font-semibold truncate" title={h.ghi_chu} data-testid={`ghi-chu-${h.ma_dk}`}>{h.ghi_chu}</span>
          )}
          {h.da_sua && (
            <button type="button" aria-label={`Về mặc định ${h.ho_ten}`} title="Về như tool điền sẵn"
              onClick={() => void ap([{ ma_dk: h.ma_dk, phai_thi: null }])}
              className="shrink-0 text-[12px] text-tn font-semibold inline-flex items-center gap-1 hover:underline">{icVe}Mặc định</button>
          )}
        </div>
        <div className="text-[11px] text-muted-foreground mt-1 h-4 leading-4 truncate" title={phu}>{phu}</div>
      </td>
    </tr>
  );
}
