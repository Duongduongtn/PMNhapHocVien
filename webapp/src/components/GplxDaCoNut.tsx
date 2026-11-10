import { useEffect, useRef, useState } from "react";
import { Icon } from "./Icon";
import { GplxDaCoKhoi } from "./GplxDaCoKhoi";
import { DS_NOI_CAP_GPLX, bangMoi, bangTrong, loiDanhSach, oSaiDau, tomTatGplx, type BangGplx } from "../lib/gplxDaCo";

// "GPLX đã có" gọn trong form: một dòng tóm tắt + nút mở popup nhập (CHANGES #99). Form không dài ra khi có bằng.
// Popup sửa trên bản nháp tạm: Hủy = bỏ; Xong = kiểm lỗi, còn lỗi thì không đóng. Form bấm gửi bị chặn vì GPLX
// (lanGui tăng) → tự mở popup, hiện đủ lỗi, con trỏ vào ô sai đầu tiên.
export function GplxDaCoNut({ ds, onDoi, lanGui = 0 }: { ds: BangGplx[]; onDoi: (ds: BangGplx[]) => void; lanGui?: number }) {
  const [mo, setMo] = useState(false);
  const [nhap, setNhap] = useState<BangGplx[]>([]);
  const [lanTam, setLanTam] = useState(0);
  const [daBamXong, setDaBamXong] = useState(false);
  const lanDau = useRef(lanGui);

  const moPopup = (baoLoi = false) => {
    setNhap(ds.length ? ds : [bangMoi()]);
    setDaBamXong(false);
    setLanTam((n) => (baoLoi ? n + 1 : 0));
    setMo(true);
  };

  // Bấm gửi bị chặn vì GPLX → mở popup với đủ lỗi (bỏ qua giá trị lúc mới dựng).
  useEffect(() => {
    if (lanGui === lanDau.current) return;
    lanDau.current = lanGui;
    if (loiDanhSach(ds.filter((b) => !bangTrong(b)))) moPopup(true);
  }, [lanGui]); // eslint-disable-line react-hooks/exhaustive-deps

  // Có lỗi → đưa con trỏ tới ô sai đầu tiên trong popup.
  useEffect(() => {
    if (!mo || !lanTam) return;
    const o = oSaiDau(nhap.filter((b) => !bangTrong(b)));
    if (!o) return;
    requestAnimationFrame(() => {
      const el = document.querySelector<HTMLInputElement>(`[data-popup-gplx] [data-o="${o}"] input`);
      el?.scrollIntoView({ block: "center" });
      el?.focus({ preventScroll: true });
    });
  }, [mo, lanTam]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!mo) return;
    const f = (e: KeyboardEvent) => { if (e.key === "Escape" && !e.defaultPrevented) setMo(false); };
    window.addEventListener("keydown", f);
    return () => window.removeEventListener("keydown", f);
  }, [mo]);

  const xong = () => {
    const sach = nhap.filter((b) => !bangTrong(b));
    const l = loiDanhSach(sach);
    if (l) { setNhap(sach.length ? sach : nhap); setLanTam((n) => n + 1); setDaBamXong(true); return; }
    onDoi(sach);
    setMo(false);
  };

  const tomTat = tomTatGplx(ds, DS_NOI_CAP_GPLX);
  const loiNgoai = loiDanhSach(ds.filter((b) => !bangTrong(b))); // cùng cách tính với Xong
  return (
    <div className="rounded-lg border border-border bg-card px-3 py-2.5" data-testid="gplx-tom-tat">
      <div className="flex items-center gap-2">
        <span className="text-[13px] font-semibold shrink-0">GPLX đã có</span>
        {tomTat.length === 0 && <span className="flex-1 text-[12.5px] text-muted-foreground">Không có</span>}
        {tomTat.length > 0 && <span className="flex-1" />}
        <button
          type="button"
          onClick={() => moPopup(!!loiNgoai)}
          className="shrink-0 inline-flex items-center gap-1 h-9 px-3 rounded-lg border border-border text-[13px] font-medium hover:bg-muted"
        >
          <Icon name={tomTat.length ? "edit" : "plus"} className="w-4 h-4" />
          {tomTat.length ? "Sửa" : "Nhập GPLX"}
        </button>
      </div>
      {tomTat.length > 0 && (
        <div className="mt-1.5 flex flex-wrap gap-1.5">
          {tomTat.map((t, i) => (
            <span key={i} className="inline-flex max-w-full items-center rounded-md bg-primary/10 px-2 py-0.5 text-[12px] font-medium text-primary">
              <span className="truncate">{t}</span>
            </span>
          ))}
        </div>
      )}
      {loiNgoai && <p role="alert" className="mt-1.5 text-[12px] text-destructive">{loiNgoai}</p>}

      {mo && (
        <div
          className="fixed inset-0 z-[60] bg-black/60 flex items-end sm:items-center justify-center p-0 sm:p-4"
          onClick={(e) => { if (e.target === e.currentTarget) setMo(false); }}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-label="GPLX đã có"
            data-popup-gplx
            className="bg-card w-full sm:max-w-2xl rounded-t-2xl sm:rounded-xl shadow-2xl max-h-[90vh] flex flex-col overflow-hidden"
          >
            <div className="flex items-center justify-between px-4 py-3 border-b border-border shrink-0">
              <h3 className="font-bold text-sm">GPLX học viên đang có</h3>
              <button type="button" autoFocus onClick={() => setMo(false)} aria-label="Đóng" className="w-8 h-8 rounded-lg hover:bg-muted flex items-center justify-center">
                <Icon name="x" className="w-5 h-5" />
              </button>
            </div>
            <div className="p-4 overflow-y-auto">
              <GplxDaCoKhoi ds={nhap} onDoi={setNhap} lanGui={lanTam} trongPopup />
            </div>
            <div className="shrink-0 border-t border-border px-4 py-3">
              {daBamXong && <p role="alert" className="mb-2 text-[12px] text-destructive">Còn lỗi ở trên — sửa xong mới bấm Xong được.</p>}
              <div className="flex gap-2">
                <button type="button" onClick={() => setMo(false)} className="flex-1 h-11 rounded-lg border border-border text-sm font-medium hover:bg-muted">Hủy</button>
                <button type="button" onClick={xong} className="flex-1 h-11 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:opacity-90">Xong</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
