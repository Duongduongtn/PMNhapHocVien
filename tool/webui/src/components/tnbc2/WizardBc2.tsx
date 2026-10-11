import { useEffect, useState } from "react";
import { khoaSanSang, type KhoaSanSang, type KhoaSanSangResp, type LoaiHang } from "../../lib/tnbc2Api";
import { soVN } from "../../lib/format";

// TNB-04 — luồng 3 bước "một nút làm xong": ① Chọn khóa → ② Chọn học viên → ③ Xác nhận. Bám ui-mock/tnbc2.html.
// Task 109 dựng khung + bước ①; bước ② (task 110) và ③ (task 112) gắn vào `NoiDungBuoc`.

export interface TrangThaiWizard {
  loai: LoaiHang;
  buoc: 1 | 2 | 3;
  maKh: string;
  tenKh: string;
  /** Rỗng = chưa có BC2 (sẽ lập ở bước ③); khác rỗng = thêm học viên vào BC2 đang mở này. */
  maBc2: string;
}

const ngayVN = (iso: string) => (iso ? iso.slice(0, 10).split("-").reverse().join("/") : "");

function Vien({ n, ten, buoc }: { n: 1 | 2 | 3; ten: string; buoc: number }) {
  const xong = buoc > n;
  const dang = buoc === n;
  return (
    <div className={`inline-flex items-center gap-2 h-8 px-3 rounded-full border text-[13px] font-semibold ${
      dang ? "bg-tn-soft border-tn text-tn" : xong ? "bg-success/10 border-success/40 text-success" : "border-border text-muted-foreground"}`}>
      <span className={`grid place-items-center w-5 h-5 rounded-full text-[11px] ${dang ? "bg-tn text-white" : xong ? "bg-success text-white" : "bg-muted"}`}>
        {xong ? "✓" : n}
      </span>
      {ten}
    </div>
  );
}

export function DauWizard({ tt, onVe }: { tt: TrangThaiWizard; onVe: () => void }) {
  return (
    <div className="shrink-0 bg-card border-b border-border px-4 py-2.5 flex flex-wrap items-center gap-3">
      <button type="button" onClick={onVe}
        className="h-9 px-3 rounded-lg border border-input text-[13px] font-semibold hover:bg-muted">
        ← Danh sách BC2
      </button>
      <Vien n={1} ten="Chọn khóa" buoc={tt.buoc} />
      <span className="text-muted-foreground">›</span>
      <Vien n={2} ten="Chọn học viên" buoc={tt.buoc} />
      <span className="text-muted-foreground">›</span>
      <Vien n={3} ten="Xác nhận" buoc={tt.buoc} />
      <div className="ml-auto text-[12px] text-muted-foreground">
        {tt.loai === "oto" ? "Ô tô" : "Mô tô"}
        {tt.maBc2 ? <> · Thêm vào BC2 số <b>{tt.maBc2}</b></> : " · Lập BC2 mới"}
        {tt.maKh && <> · {tt.tenKh}</>}
      </div>
    </div>
  );
}

function TheKhoa({ k, thang, onChon }: { k: KhoaSanSang; thang: number; onChon: (k: KhoaSanSang) => void }) {
  const mo = k.bc2_cua_khoa.find((b) => b.trang_thai === 0);
  const duoc = k.co_bc1;
  return (
    <div className={`flex flex-wrap items-center gap-4 rounded-xl border-2 bg-card p-4 ${
      duoc ? "border-tn-border hover:border-tn cursor-pointer" : "border-border opacity-55 cursor-not-allowed"}`}
      onClick={() => duoc && onChon(k)} data-testid={`khoa-${k.ma_kh}`} aria-disabled={!duoc}>
      <div className="w-[230px] min-w-0">
        <div className="font-semibold text-[14.5px]">{k.ten_kh}</div>
        <div className="text-[12px] text-muted-foreground">
          bế giảng {ngayVN(k.ngay_bg)}
          {k.khoa_cu && <span className="ml-1 text-warning font-semibold">· khóa cũ</span>}
          {duoc ? <> · BC1 <span className="font-mono">{k.so_bc1}</span></> : <span className="text-warning"> · chưa có BC1 — lập BC1 ở phần mềm cũ trước</span>}
        </div>
      </div>
      <div className="flex gap-8 flex-1">
        <div>
          <div className="text-xl font-bold tabular-nums text-success">{soVN(k.san_sang)}</div>
          <div className="text-[11.5px] text-muted-foreground">Sẵn sàng</div>
        </div>
        <div>
          <div className="text-xl font-bold tabular-nums text-primary">{soVN(k.thi_lai)}</div>
          <div className="text-[11.5px] text-muted-foreground">Thi lại (≤ {thang} tháng)</div>
        </div>
        <div>
          <div className={`text-xl font-bold tabular-nums ${k.can_xem ? "text-warning" : ""}`}>{soVN(k.can_xem)}</div>
          <div className="text-[11.5px] text-muted-foreground">Cần xem</div>
        </div>
      </div>
      {mo && (
        <span className="inline-block text-[11px] font-semibold px-2 rounded-full border text-tn bg-tn-soft border-tn-border whitespace-nowrap">
          Đã có BC2 {mo.ma}
        </span>
      )}
      <button type="button" disabled={!duoc}
        onClick={(e) => { e.stopPropagation(); if (duoc) onChon(k); }}
        className="h-9 px-4 rounded-lg bg-tn text-white text-[13px] font-semibold disabled:opacity-45 disabled:cursor-not-allowed">
        Chọn khóa này →
      </button>
    </div>
  );
}

/** Bước ①: chọn khóa. Mô tô mà khóa đã có BC2 đang mở → chuyển sang thêm học viên vào BC2 đó (mockup `chonKhoa`). */
export function BuocChonKhoa({
  loai,
  onChon,
}: {
  loai: LoaiHang;
  onChon: (k: KhoaSanSang, maBc2: string) => void;
}) {
  const [cu, setCu] = useState(false);
  const [lamTuoi, setLamTuoi] = useState(0);
  const [data, setData] = useState<KhoaSanSangResp | null>(null);
  const [loi, setLoi] = useState<string | null>(null);

  useEffect(() => {
    let huy = false;
    setLoi(null);
    khoaSanSang(loai, cu, undefined, lamTuoi > 0)
      .then((d) => { if (!huy) setData(d); })
      .catch((e: unknown) => { if (!huy) { setData(null); setLoi(e instanceof Error ? e.message : "Không tải được danh sách khóa"); } });
    return () => { huy = true; };
  }, [loai, cu, lamTuoi]);

  function chon(k: KhoaSanSang) {
    const mo = loai === "moto" ? k.bc2_cua_khoa.find((b) => b.trang_thai === 0) : undefined;
    onChon(k, mo?.ma ?? "");
  }

  return (
    <div className="flex-1 min-h-0 overflow-auto p-4 space-y-3">
      <div className="flex items-center gap-3">
        <div className="text-[15px] font-semibold">Chọn khóa cần lập BC2</div>
        <button type="button" onClick={() => setLamTuoi((n) => n + 1)}
          className="h-8 px-3 rounded-lg text-[13px] font-semibold text-primary hover:bg-accent">
          Làm tươi
        </button>
        <label className="inline-flex items-center gap-2 h-8 px-3 rounded-lg border border-border bg-white text-[12.5px] cursor-pointer ml-auto">
          <input type="checkbox" checked={cu} onChange={(e) => setCu(e.target.checked)} /> Hiện khóa cũ
        </label>
      </div>
      {loi && <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-[13px] text-destructive">{loi}</div>}
      {!data && !loi && <div className="text-[13px] text-muted-foreground">Đang tải…</div>}
      {data && data.khoa.length === 0 && (
        <div className="text-muted-foreground py-10 text-center">Không có khóa đã bế giảng trong phạm vi.</div>
      )}
      {data?.khoa.map((k) => <TheKhoa key={k.ma_kh} k={k} thang={data.thi_lai_thang} onChon={chon} />)}
      <div className="rounded-lg bg-muted px-3 py-2 text-[12.5px] text-muted-foreground">
        Chọn khóa là đủ: tool tự tìm BC1, gợi ý số BC2 và gom học viên thành các nhóm ở bước sau.
      </div>
    </div>
  );
}
