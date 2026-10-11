import { useState } from "react";
import { soVN } from "../../lib/format";
import { khopDanhSach, LoiTnbc2, type KhopDanhSachResp } from "../../lib/tnbc2Api";
import { TOI_DA_DONG_DAN, TOI_DA_KY_TU_DONG, trichMaTuVanBan } from "../../lib/tnbcUngVien";

// TNB-04 — "Dán danh sách CMT / mã đăng ký" ở bước ②: tích đúng người, báo số dòng không khớp và người khớp nhưng
// không đưa được kèm lý do. Chỉ tích HV thuộc nhóm Sẵn sàng/Thi lại (do server quyết, không tự tích ngoài nhóm).

export default function DanDanhSachBuoc2({
  maKh,
  maBc2,
  onDong,
  onTich,
}: {
  maKh: string;
  maBc2: string;
  onDong: () => void;
  onTich: (dsMaDk: string[]) => void;
}) {
  const [text, setText] = useState("");
  const [dang, setDang] = useState(false);
  const [kq, setKq] = useState<KhopDanhSachResp | null>(null);
  const [loi, setLoi] = useState<string | null>(null);

  const ma = trichMaTuVanBan(text);
  const quaDai = ma.filter((x) => x.length > TOI_DA_KY_TU_DONG);
  const qua = ma.length > TOI_DA_DONG_DAN;

  async function khop() {
    setDang(true);
    setLoi(null);
    setKq(null);
    try {
      setKq(await khopDanhSach(maKh, maBc2, ma));
    } catch (e) {
      setLoi(e instanceof LoiTnbc2 ? e.message : "Mất kết nối khi đối chiếu danh sách — thử lại.");
    } finally {
      setDang(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/40 grid place-items-center p-4">
      <div role="dialog" aria-modal="true" aria-label="Dán danh sách CMT"
        className="bg-white rounded-xl shadow-2xl w-[680px] max-w-full max-h-[90vh] flex flex-col">
        <div className="p-4 border-b border-border font-semibold">Dán danh sách CMT / mã đăng ký</div>
        <div className="p-4 overflow-auto space-y-3 text-[13px]">
          <p className="text-muted-foreground">
            Dán một cột số CMT/CCCD (hoặc mã đăng ký) từ Excel, mỗi dòng một người. Dòng nhiều cột thì lấy ô trông như số
            CMT. Chỉ học viên thuộc nhóm <b>Sẵn sàng</b> hoặc <b>Thi lại</b> mới được tích.
          </p>
          <textarea autoFocus rows={8} className="field-input font-mono" value={text}
            placeholder={"079203012345\n079203012346\n…"}
            onChange={(e) => { setText(e.target.value); setKq(null); }} />
          <div className={qua || quaDai.length ? "text-destructive" : "text-muted-foreground"}>
            {ma.length === 0
              ? "Chưa có dòng nào."
              : qua
                ? `Có ${soVN(ma.length)} dòng, tối đa ${soVN(TOI_DA_DONG_DAN)} — chia nhỏ rồi dán lần lượt.`
                : quaDai.length
                  ? `${quaDai.length} dòng dài quá ${TOI_DA_KY_TU_DONG} ký tự (có thể dán nhầm cả hàng) — kiểm lại.`
                  : `${soVN(ma.length)} dòng (đã bỏ dòng trống và dòng trùng).`}
          </div>

          {loi && <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-destructive">{loi}</div>}

          {kq && (
            <div className="space-y-2">
              <div className="rounded-lg border border-success/40 bg-success/10 p-3">
                Khớp <b>{soVN(kq.so_khop)}</b> / {soVN(kq.tong_dong)} dòng — sẽ tích {soVN(kq.so_khop)} học viên.
              </div>
              {kq.khong_khop.length > 0 && (
                <div className="rounded-lg border border-warning/40 bg-warning/10 p-3">
                  <div className="font-semibold text-warning mb-1">{soVN(kq.khong_khop.length)} dòng không khớp ai</div>
                  <ul className="max-h-28 overflow-auto font-mono text-[12px] space-y-0.5">
                    {kq.khong_khop.map((d) => <li key={d}>{d}</li>)}
                  </ul>
                </div>
              )}
              {kq.khong_dua_duoc.length > 0 && (
                <div className="rounded-lg border border-border p-3">
                  <div className="font-semibold mb-1">{soVN(kq.khong_dua_duoc.length)} người khớp nhưng chưa đưa vào được</div>
                  <ul className="max-h-36 overflow-auto space-y-0.5">
                    {kq.khong_dua_duoc.map((x) => (
                      <li key={x.ma_dk}><b>{x.ten}</b> <span className="font-mono text-[12px] text-muted-foreground">{x.cmt}</span> — {x.ly_do}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
        <div className="p-3 border-t border-border flex justify-end gap-2">
          <button type="button" onClick={onDong}
            className="h-9 px-4 rounded-lg border border-input text-[13px] font-semibold hover:bg-muted">
            Đóng
          </button>
          {!kq && (
            <button type="button" disabled={dang || ma.length === 0 || qua || quaDai.length > 0} onClick={khop}
              className="h-9 px-4 rounded-lg bg-tn text-white text-[13px] font-semibold disabled:opacity-45 disabled:cursor-not-allowed">
              {dang ? "Đang đối chiếu…" : "Đối chiếu"}
            </button>
          )}
          {kq && (
            <button type="button" disabled={kq.so_khop === 0} onClick={() => onTich(kq.khop.map((h) => h.ma_dk))}
              className="h-9 px-4 rounded-lg bg-tn text-white text-[13px] font-semibold disabled:opacity-45 disabled:cursor-not-allowed">
              Tích {soVN(kq.so_khop)} học viên
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
