import { useEffect, useState } from "react";
import { Icon } from "../../components/Icon";
import { GplxDaCoKhoi } from "./GplxDaCoKhoi";
import { bangMoi, bangTrong, dienNoiCapTheoSo, loiBang, nhanHangGon, tenHang, tomTatGplx, trungHangDangKy, type BangGplx } from "./gplxDaCo";

// "GPLX đã có" gọn ở ngăn Chuẩn bị: dòng tóm tắt + nút mở popup nhập (CHANGES #99), ngăn không dài ra khi có bằng.
// Popup sửa trên bản nháp tạm: Hủy/Esc/bấm nền = bỏ; Xong = còn lỗi thì không đóng (lỗi đã hiện dưới từng bằng).
export function GplxDaCoNut({
  ds, onDoi, noiCap, hangKhoa, tuAppWeb, coBanMoi, onDungBanWeb, soCu,
}: {
  ds: BangGplx[];
  onDoi: (ds: BangGplx[]) => void;
  noiCap: { ma: string; ten: string }[];
  hangKhoa?: string | null;
  tuAppWeb: boolean;
  coBanMoi: boolean;
  onDungBanWeb: () => void;
  soCu?: Set<string>; // số app web gửi từ trước — giữ nguyên thì không chặn dạng (CHANGES #101)
}) {
  const [mo, setMo] = useState(false);
  const [nhap, setNhap] = useState<BangGplx[]>([]);
  const [daBamXong, setDaBamXong] = useState(false);

  // Bằng app web gửi về thiếu nơi cấp → điền sẵn theo số ngay khi mở hồ sơ (CHANGES #98).
  useEffect(() => {
    if (noiCap.length === 0) return;
    const moi = dienNoiCapTheoSo(ds, noiCap);
    if (moi !== ds) onDoi(moi);
  }, [ds, noiCap, onDoi]);

  useEffect(() => {
    if (!mo) return;
    const f = (e: KeyboardEvent) => { if (e.key === "Escape" && !e.defaultPrevented) setMo(false); };
    window.addEventListener("keydown", f);
    return () => window.removeEventListener("keydown", f);
  }, [mo]);

  const moPopup = () => { setNhap(ds.length ? ds : [bangMoi()]); setDaBamXong(false); setMo(true); };
  const xong = () => {
    const sach = nhap.filter((b) => !bangTrong(b));
    if (sach.some((b) => loiBang(b, soCu).length > 0) || trungHangDangKy(hangKhoa, sach)) { setNhap(sach.length ? sach : nhap); setDaBamXong(true); return; }
    onDoi(sach);
    setMo(false);
  };

  const tomTat = tomTatGplx(ds, noiCap);
  const coLoi = ds.some((b) => loiBang(b, soCu).length > 0) || trungHangDangKy(hangKhoa, ds);
  return (
    <div className="rounded-lg border border-border bg-card px-4 py-3" data-testid="gplx-tom-tat">
      <div className="flex items-center gap-2">
        <span className="text-[13px] font-semibold">GPLX đã có</span>
        {tomTat.length === 0 && <span className="text-[12.5px] text-muted-foreground">Không có</span>}
        <span className="flex-1" />
        <button type="button" className="btn btn-secondary btn-row inline-flex items-center gap-1" onClick={moPopup}>
          <Icon name={tomTat.length ? "edit" : "plus"} className="w-3.5 h-3.5" />
          {tomTat.length ? "Sửa" : "Nhập GPLX"}
        </button>
      </div>
      {tomTat.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {tomTat.map((t, i) => (
            <span key={i} className="inline-flex max-w-full items-center rounded-md bg-primary/10 px-2 py-0.5 text-[12px] font-medium text-primary">
              <span className="truncate">{t}</span>
            </span>
          ))}
        </div>
      )}
      {coBanMoi && (
        <div className="mt-2 flex flex-wrap items-center gap-2 rounded-md bg-warning/10 px-2 py-1.5 text-[12px] text-warning">
          <span className="flex-1 min-w-[160px]">App web có bản mới, đang giữ bản đã sửa ở đây.</span>
          <button type="button" className="btn btn-secondary btn-row" onClick={onDungBanWeb}>Dùng bản app web</button>
        </div>
      )}
      {tuAppWeb && !coBanMoi && tomTat.length > 0 && (
        <p className="mt-2 rounded-md bg-primary/5 px-2 py-1.5 text-[12px] text-primary">Từ app web — kiểm lại với bằng thật, sửa nếu cần.</p>
      )}
      {coLoi && <p role="alert" className="mt-2 text-[12px] text-destructive">GPLX đã có còn lỗi — bấm "Sửa" để xem, chưa sửa thì nạp sẽ báo lỗi.</p>}

      {mo && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={(e) => { if (e.target === e.currentTarget) setMo(false); }}>
          <div role="dialog" aria-modal="true" aria-label="GPLX đã có" className="bg-card w-full max-w-[640px] rounded-xl border border-border shadow-xl max-h-[90vh] flex flex-col overflow-hidden">
            <div className="flex items-center justify-between px-5 py-3 border-b border-border shrink-0">
              <h3 className="font-bold text-sm">GPLX học viên đang có</h3>
              <button type="button" autoFocus onClick={() => setMo(false)} aria-label="Đóng" className="w-8 h-8 rounded-lg hover:bg-muted flex items-center justify-center">
                <Icon name="x" className="w-5 h-5" />
              </button>
            </div>
            <div className="p-5 overflow-y-auto">
              <GplxDaCoKhoi ds={nhap} onDoi={setNhap} noiCap={noiCap} hangKhoa={hangKhoa} tuAppWeb={false} coBanMoi={false} onDungBanWeb={() => {}} trongPopup soCu={soCu} />
              {daBamXong && <p role="alert" className="mt-3 text-[12px] text-destructive">Còn lỗi ở trên — sửa xong mới bấm Xong được.</p>}
            </div>
            <div className="shrink-0 border-t border-border px-5 py-3 flex justify-end gap-2">
              <button type="button" className="btn btn-secondary" onClick={() => setMo(false)}>Hủy</button>
              <button type="button" className="btn btn-primary" onClick={xong}>Xong</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/** Badge "học viên đã có GPLX" ở dòng danh sách và đầu ngăn Chuẩn bị (CHANGES #99): nền xanh đậm, tối đa 2 hạng rồi +n. */
export function BadgeGplx({ ds, testId }: { ds: BangGplx[]; testId?: string }) {
  if (!ds.some((b) => !bangTrong(b))) return null;
  return (
    <span
      data-testid={testId}
      title={`Học viên đã có GPLX: ${ds.filter((b) => !bangTrong(b)).map((b) => tenHang(b) || "?").join(", ")}`}
      className="inline-flex items-center h-5 px-1.5 rounded text-[11px] font-bold text-primary-foreground bg-primary whitespace-nowrap shrink-0"
    >
      GPLX {nhanHangGon(ds)}
    </span>
  );
}
