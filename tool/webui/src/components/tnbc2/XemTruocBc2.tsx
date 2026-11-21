import { useCallback, useEffect, useRef, useState } from "react";
import {
  daInBc2, datThuMucPmCu, LoiTnbc2, tenTepBc2, thuMucPmCu, xemTruocBc2, type ThuMucPmCu,
} from "../../lib/tnbc2Api";

// TNB-08 — xem trước bản in BC2: PDF dựng bằng chính mẫu của phần mềm cũ, rồi In… hoặc Lưu PDF (nút của tool;
// cả hai ghi một lần in để cột "Bản in" ở danh sách BC2 biết). Bám ui-mock/inbc2.html màn ② và màn lỗi.

const nutNho = "h-9 px-3 rounded-lg border border-input bg-white text-[13px] font-semibold hover:bg-muted disabled:opacity-45 disabled:cursor-not-allowed inline-flex items-center justify-center gap-1.5 whitespace-nowrap";
const nutChinh = "h-9 px-3 rounded-lg bg-tn text-white text-[13px] font-semibold hover:bg-[hsl(222_76%_34%)] disabled:opacity-45 disabled:cursor-not-allowed inline-flex items-center justify-center gap-1.5 whitespace-nowrap";

const icIn = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"
    strokeLinejoin="round" aria-hidden="true"><path d="M6 9V3h12v6" /><rect x="4" y="9" width="16" height="8" rx="2" /><path d="M7 14h10v7H7z" /></svg>
);
const icTai = (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"
    strokeLinejoin="round" aria-hidden="true"><path d="M12 3v12m0 0 4-4m-4 4-4-4" /><path d="M4 17v3h16v-3" /></svg>
);

export default function XemTruocBc2({
  maBc2, maKh, soHv, soChonLai, onVe,
}: { maBc2: string; maKh: string; soHv: number; soChonLai: number; onVe: () => void }) {
  const [url, setUrl] = useState<string | null>(null);
  const [loi, setLoi] = useState<LoiTnbc2 | null>(null);
  const [dang, setDang] = useState(true);
  const [lan, setLan] = useState(0);
  const [canhBao, setCanhBao] = useState("");
  const khung = useRef<HTMLIFrameElement>(null);
  // Một lần dựng (~3 giây, chiếm bộ Crystal) cho mỗi (BC2, lần thử): hiệu ứng gắn–gỡ–gắn lại của React ở chế độ dev
  // không được gọi trùng lần hai.
  const dangDung = useRef<{ khoa: string; p: Promise<Blob> } | null>(null);

  useEffect(() => {
    let huy = false;
    let moi: string | null = null;
    setDang(true);
    setLoi(null);
    setUrl(null);
    const khoa = `${maBc2}|${lan}`;
    if (dangDung.current?.khoa !== khoa) dangDung.current = { khoa, p: xemTruocBc2(maBc2) };
    dangDung.current.p
      .then((b) => { if (!huy) { moi = URL.createObjectURL(b); setUrl(moi); } })
      .catch((e: unknown) => { if (!huy) setLoi(e instanceof LoiTnbc2 ? e : new LoiTnbc2("loi_he_thong", e instanceof Error ? e.message : "Không dựng được bản in", 0)); })
      .finally(() => { if (!huy) setDang(false); });
    return () => { huy = true; if (moi) URL.revokeObjectURL(moi); };
  }, [maBc2, lan]);

  // Ghi sổ phần thi + cột "Bản in". Lỗi không chặn việc in nhưng phải báo: sổ không cập nhật thì BC2 sau điền thiếu phần đã đạt.
  const ghiDaIn = () => {
    setCanhBao("");
    void daInBc2(maBc2).catch(() => setCanhBao("Chưa ghi nhận được lần in này vào sổ phần thi — bản in vẫn dùng được; lần lập BC2 sau hãy kiểm lại cột Phần thi."));
  };

  const inRa = () => {
    const w = khung.current?.contentWindow;
    if (!w) return;
    w.focus();
    w.print();
    ghiDaIn();
  };

  const luuPdf = () => {
    if (!url) return;
    const a = document.createElement("a");
    a.href = url;
    a.download = tenTepBc2(maBc2, maKh);
    document.body.appendChild(a);
    a.click();
    a.remove();
    ghiDaIn();
  };

  return (
    <div className="h-full flex flex-col min-h-0">
      <div className="shrink-0 bg-card border-b border-border px-4 py-2.5 flex flex-wrap items-center gap-3">
        <button type="button" onClick={onVe} className={nutNho}>← Sửa nội dung thi</button>
        <div className="min-w-0">
          <div className="text-[11px] text-muted-foreground">Xem trước bản in</div>
          <div className="font-semibold text-[15px] tabular-nums">
            {maBc2}<span className="font-normal text-muted-foreground text-[13px]"> · {soHv} học viên{soChonLai > 0 ? ` · ${soChonLai} dòng đã sửa` : ""}</span>
          </div>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <span className="text-[12px] text-muted-foreground mr-1">Đúng mẫu in của phần mềm cũ</span>
          <button type="button" className={nutNho} onClick={inRa} disabled={!url} data-testid="nut-in">{icIn}In…</button>
          <button type="button" className={nutChinh} onClick={luuPdf} disabled={!url} data-testid="nut-luu-pdf">{icTai}Lưu PDF</button>
        </div>
      </div>

      <div className="flex-1 min-h-0 bg-muted">
        {dang && (
          <div role="status" className="h-full grid place-items-center text-[13px] text-muted-foreground">
            <div className="flex items-center gap-3">
              <svg className="animate-spin" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="hsl(222 76% 40%)" strokeWidth="2.5" aria-hidden="true">
                <path d="M21 12a9 9 0 1 1-6.2-8.6" strokeLinecap="round" />
              </svg>
              Đang dựng bản in bằng mẫu phần mềm cũ…
            </div>
          </div>
        )}
        {canhBao && <div role="status" className="m-3 rounded-lg border border-warning/40 bg-warning/10 px-3 py-2 text-[12.5px] text-warning">{canhBao}</div>}
        {loi && <LoiDung loi={loi} onThuLai={() => setLan((n) => n + 1)} onVe={onVe} />}
        {url && !dang && (
          <iframe ref={khung} src={url} title="Bản in Báo cáo 2" data-testid="khung-pdf" className="w-full h-full border-0 bg-white" />
        )}
      </div>
    </div>
  );
}

function LoiDung({ loi, onThuLai, onVe }: { loi: LoiTnbc2; onThuLai: () => void; onVe: () => void }) {
  const thieuPmCu = loi.ma === "chua_co_phan_mem_cu";
  return (
    <div className="h-full grid place-items-center px-6">
      <div className="max-w-[560px] text-[13.5px]" role="alert">
        <div className="flex items-center gap-2 text-destructive font-semibold text-[15px]">
          {thieuPmCu ? "Máy này chưa dựng được bản in Báo cáo 2" : "Không dựng được bản in"}
        </div>
        <p className="mt-2">{loi.message}</p>
        {thieuPmCu && <ChonThuMuc onXong={onThuLai} />}
        <div className="mt-4 flex gap-2">
          {!thieuPmCu && <button type="button" className={nutChinh} onClick={onThuLai}>Thử lại</button>}
          <button type="button" className={nutNho} onClick={onVe}>Quay lại sửa nội dung thi</button>
        </div>
        <p className="mt-3 text-[12px] text-muted-foreground">Lựa chọn nội dung thi vẫn được giữ.</p>
      </div>
    </div>
  );
}

function ChonThuMuc({ onXong }: { onXong: () => void }) {
  const [tt, setTt] = useState<ThuMucPmCu | null>(null);
  const [duong, setDuong] = useState("");
  const [loi, setLoi] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => { thuMucPmCu().then((d) => { setTt(d); setDuong(d.thu_muc || d.luu_khong_hop_le || ""); }).catch(() => undefined); }, []);

  const luu = useCallback(async (p: string) => {
    setBusy(true);
    setLoi("");
    try { await datThuMucPmCu(p); onXong(); }
    catch (e) { setLoi(e instanceof Error ? e.message : "Không lưu được thư mục"); }
    finally { setBusy(false); }
  }, [onXong]);

  return (
    <div className="mt-3">
      <p className="text-muted-foreground">Tool dùng mẫu in và bộ chạy Crystal của <b>phần mềm cũ</b> để bản in giống hệt. Nhập đúng thư mục cài phần mềm cũ (có thư mục PM1\Reports).</p>
      {tt && tt.ung_vien.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {tt.ung_vien.map((u) => (
            <button key={u} type="button" onClick={() => setDuong(u)} className="h-7 px-2 rounded-md border border-border bg-white text-[12px] tabular-nums hover:bg-muted">{u}</button>
          ))}
        </div>
      )}
      <div className="mt-2 flex gap-2">
        <input aria-label="Thư mục phần mềm cũ" className="field-input flex-1" value={duong} placeholder="D:\GPLX-…" onChange={(e) => setDuong(e.target.value)} />
        <button type="button" className={nutChinh} disabled={busy || !duong.trim()} onClick={() => void luu(duong)}>Dùng thư mục này</button>
      </div>
      {loi && <div className="mt-2 text-[12.5px] text-destructive" role="alert">{loi}</div>}
    </div>
  );
}
