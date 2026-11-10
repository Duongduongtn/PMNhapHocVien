import { useEffect, useRef, useState } from "react";
import { Icon } from "../../components/Icon";
import type { KhoaHoc, NapIn } from "../../lib/api";
import { ymdToVN } from "../../lib/format";
import { chuConThieu, type KetQuaTuoi } from "./napSanSang";

export interface HvChuaDuTuoi {
  item: NapIn;
  kq: KetQuaTuoi;
}

// NAP-09 (CHANGES #102, mock ui-mock/canhbaotuoi.html): chen trước bước nạp khi có học viên chưa đủ tuổi học hạng
// của khóa. Chỉ cảnh báo — mặc định vẫn chọn nạp hết; user bỏ chọn từng người hoặc "Bỏ hết người chưa đủ tuổi".
export function CanhBaoTuoiDialog({
  khoa, ds, tongLo, homNay, onHuy, onTiep,
}: {
  khoa: KhoaHoc;
  ds: HvChuaDuTuoi[];
  tongLo: number;            // số học viên cả lô (gồm người đã đủ tuổi)
  homNay: Date;
  onHuy: () => void;
  onTiep: (boUuid: Set<string>) => void;
}) {
  const [bo, setBo] = useState<Set<string>>(new Set());
  const tuoi = khoa.tuoi_hv ?? 0;
  const conNap = tongLo - bo.size;

  const huyRef = useRef(onHuy);
  huyRef.current = onHuy;
  useEffect(() => {
    const f = (e: KeyboardEvent) => { if (e.key === "Escape") huyRef.current(); };
    window.addEventListener("keydown", f);
    return () => window.removeEventListener("keydown", f);
  }, []);

  const doi = (uuid: string) => setBo((s) => { const n = new Set(s); if (n.has(uuid)) n.delete(uuid); else n.add(uuid); return n; });
  const ngayHom = `${String(homNay.getDate()).padStart(2, "0")}/${String(homNay.getMonth() + 1).padStart(2, "0")}/${homNay.getFullYear()}`;

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={(e) => { if (e.target === e.currentTarget) onHuy(); }}>
      <div role="dialog" aria-modal="true" aria-label="Cảnh báo tuổi học viên" data-testid="canh-bao-tuoi"
        className="bg-card w-full max-w-[920px] rounded-xl border border-border shadow-2xl max-h-[90vh] flex flex-col overflow-hidden">
        <div className="px-6 py-4 border-b border-border shrink-0">
          <div className="flex items-start gap-3">
            <div className="w-9 h-9 rounded-full bg-warning/10 text-warning grid place-items-center shrink-0">
              <Icon name="warn" className="w-5 h-5" />
            </div>
            <div className="flex-1">
              <h3 className="font-bold text-[15px]">{ds.length} học viên chưa đủ tuổi học hạng của khóa</h3>
              <p className="text-[13px] text-muted-foreground mt-0.5">Chỉ là cảnh báo — bạn quyết định nạp hay bỏ từng người.</p>
            </div>
            <button type="button" autoFocus onClick={onHuy} aria-label="Đóng" className="w-8 h-8 rounded-lg hover:bg-muted flex items-center justify-center">
              <Icon name="x" className="w-5 h-5" />
            </button>
          </div>
          <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-2 text-[12.5px]">
            <div className="rounded-lg bg-muted px-3 py-2"><div className="text-muted-foreground">Khóa</div><div className="font-semibold truncate">{khoa.ten_kh} · {khoa.ma_kh}</div></div>
            <div className="rounded-lg bg-muted px-3 py-2"><div className="text-muted-foreground">Hạng đào tạo</div><div className="font-semibold truncate">{khoa.ten_hang_dt || khoa.hang_dt || khoa.hang_gplx}</div></div>
            <div className="rounded-lg bg-muted px-3 py-2"><div className="text-muted-foreground">Tuổi tối thiểu</div><div className="font-semibold">{tuoi} tuổi</div></div>
            <div className="rounded-lg bg-muted px-3 py-2"><div className="text-muted-foreground">Tính tuổi tại</div><div className="font-semibold">Hôm nay {ngayHom}</div></div>
          </div>
        </div>

        <div className="overflow-y-auto">
          <table className="w-full text-[13px]">
            <thead className="bg-muted/60 text-[11.5px] text-muted-foreground">
              <tr>
                <th className="text-left font-semibold px-4 py-2 w-[70px]">Nạp</th>
                <th className="text-left font-semibold px-3 py-2">Học viên</th>
                <th className="text-left font-semibold px-3 py-2">Ngày sinh</th>
                <th className="text-left font-semibold px-3 py-2">Tuổi hôm nay</th>
                <th className="text-left font-semibold px-3 py-2">Ngày đủ {tuoi} tuổi</th>
                <th className="text-left font-semibold px-3 py-2">Còn thiếu</th>
              </tr>
            </thead>
            <tbody>
              {ds.map(({ item, kq }) => {
                const boRa = bo.has(item.uuid);
                const gach = boRa ? "line-through text-muted-foreground" : "";
                return (
                  <tr key={item.uuid} data-testid={`tuoi-${item.uuid}`} className="border-t border-border">
                    <td className="px-4 py-2.5">
                      <input type="checkbox" checked={!boRa} onChange={() => doi(item.uuid)} className="w-4 h-4 accent-primary" aria-label={`Nạp ${item.ho_ten}`} />
                    </td>
                    <td className={"px-3 py-2.5 " + gach}>
                      <div className="font-semibold">{item.ho_ten.toUpperCase()}</div>
                      <div className="text-[11.5px] text-muted-foreground">{item.so_cmt}</div>
                    </td>
                    <td className={"px-3 py-2.5 " + gach}>{ymdToVN(item.ngay_sinh)}</td>
                    <td className={"px-3 py-2.5 " + gach}>{kq.tuoi} tuổi</td>
                    <td className={"px-3 py-2.5 font-semibold " + gach}>{ymdToVN(kq.ngayDuTuoi)}</td>
                    <td className="px-3 py-2.5">
                      <span className={"inline-flex rounded-md px-2 py-0.5 text-[11px] font-semibold " + (kq.conThieuNgay < 90 ? "bg-warning/10 text-warning" : "bg-destructive/10 text-destructive")}>
                        {chuConThieu(kq.conThieuNgay)}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {tongLo > ds.length && (
            <p className="px-6 py-3 text-[12px] text-muted-foreground border-t border-border">
              {tongLo - ds.length} học viên còn lại trong lô đã đủ tuổi, nạp bình thường. Thiếu dưới 3 tháng hiện vàng, từ 3 tháng hiện đỏ.
            </p>
          )}
        </div>

        <div className="px-6 py-3 border-t border-border flex flex-wrap items-center gap-2 shrink-0">
          <button type="button" className="btn btn-secondary" onClick={() => setBo(new Set(ds.map((x) => x.item.uuid)))}>
            Bỏ hết người chưa đủ tuổi
          </button>
          <span className="text-[12.5px] text-muted-foreground" data-testid="tuoi-dem">Sẽ nạp {conNap}/{tongLo} học viên</span>
          <span className="flex-1" />
          <button type="button" className="btn btn-secondary" onClick={onHuy}>Hủy</button>
          <button type="button" className="btn btn-primary" disabled={conNap === 0} onClick={() => onTiep(bo)}>
            Tiếp tục nạp {conNap} học viên
          </button>
        </div>
      </div>
    </div>
  );
}
