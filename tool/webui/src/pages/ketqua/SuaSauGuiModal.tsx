import { useState } from "react";
import { Icon } from "../../components/Icon";
import { moSuaSauGui, SuaSauGuiLoi, type HocVienKQD, type SuaSauGuiKetQua } from "../../lib/api";
import { d1, MON_SSG, nhanKetLuan } from "./diemFmt";

// KQD-05 mở rộng (task 84) — hộp xác nhận "Sửa sau khi đã gửi Sở", chọn TỪNG HV.
// Chỉ mở khi cơ sở hết gói chưa gửi (lưới KQD-02 kiểm). KHÔNG xóa gói; HV chọn về 09/10 để sửa
// điểm, rồi PHẢI kết xuất lại ở phần mềm CDB (phản hồi Sở chỉ nhận HV đang 12 — SP tiếp nhận).

const LY_DO_TOI_DA = 1000;

export default function SuaSauGuiModal({
  targetKey, hv, onClose, onDone, onGoiDoi,
}: {
  targetKey?: string;
  hv: HocVienKQD[];
  onClose: () => void;
  onDone: (r: SuaSauGuiKetQua) => void;
  onGoiDoi: () => void; // server báo cơ sở lại còn gói chưa gửi → UI chuyển lối "Mở khóa"
}) {
  const [lyDo, setLyDo] = useState("");
  const [camKet, setCamKet] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const lyDoOk = lyDo.trim().length > 0;
  const duDieuKien = lyDoOk && camKet && hv.length > 0 && !busy;

  async function xacNhan() {
    setBusy(true); setErr("");
    try {
      const r = await moSuaSauGui({ ma_dk: hv.map((h) => h.ma_dk), ly_do: lyDo.trim() }, targetKey);
      onDone(r);
    } catch (e) {
      if (e instanceof SuaSauGuiLoi && e.loi === "con_goi_chua_gui") {
        setErr(e.message);
        onGoiDoi();
      } else {
        setErr(e instanceof Error ? e.message : "Không mở sửa được — kiểm kết nối rồi thử lại.");
      }
    } finally { setBusy(false); }
  }

  return (
    <div className="fixed inset-0 z-50">
      <div className="absolute inset-0 bg-black/40" onClick={busy ? undefined : onClose} />
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[640px] max-w-[94vw] bg-card rounded-xl shadow-2xl flex flex-col max-h-[90vh]">
        <div className="shrink-0 px-5 py-3.5 border-b border-border flex items-center gap-2">
          <Icon name="clock" className="w-5 h-5 text-kq" />
          <div className="font-bold text-[15px]">Mở sửa điểm cho {hv.length} học viên đã gửi Sở</div>
          <button onClick={onClose} disabled={busy} className="ml-auto text-muted-foreground hover:text-foreground disabled:opacity-50"><Icon name="x" className="w-5 h-5" /></button>
        </div>

        <div className="flex-1 overflow-auto px-5 py-4 space-y-3.5 text-[13px]">
          {err && <div className="rounded-md border border-destructive/40 bg-destructive/5 px-3 py-2 text-[12.5px] text-destructive">{err}</div>}

          {/* Danh sách HV + điểm hiện tại */}
          <div className="rounded-lg border border-border overflow-hidden">
            <div className="max-h-44 overflow-auto">
              <table className="w-full text-[12.5px]">
                <thead className="bg-muted/50 text-muted-foreground sticky top-0">
                  <tr className="text-left">
                    <th className="font-semibold px-3 py-1.5">Học viên</th>
                    {MON_SSG.map((m) => <th key={m.key} className="font-semibold px-1.5 py-1.5 text-center">{m.nhan}</th>)}
                    <th className="font-semibold px-2 py-1.5 text-center">Kết luận</th>
                  </tr>
                </thead>
                <tbody>
                  {hv.map((h) => (
                    <tr key={h.ma_dk} className="border-t border-border/60">
                      <td className="px-3 py-1.5 font-medium truncate max-w-[200px]" title={h.ho_ten}>{h.ho_ten}<div className="text-[11px] font-normal text-muted-foreground tabular-nums">{h.so_cccd}</div></td>
                      {MON_SSG.map((m) => <td key={m.key} className="px-1.5 py-1.5 text-center tabular-nums">{d1(h.diem[m.key])}</td>)}
                      <td className="px-2 py-1.5 text-center text-[12px]">{nhanKetLuan(h.ket_luan)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="rounded-lg border border-warning/40 bg-warning/10 px-3 py-2.5 text-[12.5px]">
            <div className="flex items-center gap-1.5 font-semibold text-warning mb-1"><Icon name="warn" className="w-4 h-4" /> Cần biết trước khi mở</div>
            <ul className="list-disc pl-5 space-y-0.5 text-foreground">
              <li><b>Sở đã nhận kết quả cũ</b> của các học viên này — gói đã gửi không thu hồi được từ máy cơ sở.</li>
              <li>Sửa xong <b>phải kết xuất lại ngay</b> bằng phần mềm CDB để gửi bản mới.</li>
              <li>Nếu Sở trả kết quả (duyệt/từ chối) <b>trong lúc chưa kết xuất lại</b>, học viên đó sẽ <b>bị kẹt</b> — phần mềm không nhận được phản hồi cho người đang ở trạng thái "đã cập nhật".</li>
              <li>Chỉ <b>{hv.length} học viên đã chọn</b> được mở; học viên khác giữ nguyên.</li>
            </ul>
          </div>

          <div>
            <label className="text-[11px] font-semibold text-muted-foreground">Lý do sửa <span className="text-destructive">*</span> <span className="font-normal">(ghi vào cột Giải trình của hồ sơ)</span></label>
            <textarea
              value={lyDo}
              onChange={(e) => setLyDo(e.target.value)}
              maxLength={LY_DO_TOI_DA}
              disabled={busy}
              placeholder="Ví dụ: nhập nhầm điểm sa hình của 2 học viên, cần sửa và gửi lại Sở…"
              className={"w-full h-20 mt-1 text-[13px] px-2.5 py-1.5 rounded-lg border bg-card focus:outline-none focus:border-kq focus:ring-2 focus:ring-kq/20 " + (lyDoOk ? "border-input" : "border-destructive/60")}
            />
            <div className="text-[11px] text-muted-foreground text-right tabular-nums">{lyDo.length.toLocaleString("vi-VN")}/{LY_DO_TOI_DA.toLocaleString("vi-VN")}</div>
          </div>

          <label className="flex items-start gap-2 cursor-pointer rounded-lg border border-border px-3 py-2 hover:bg-muted/40">
            <input type="checkbox" checked={camKet} onChange={(e) => setCamKet(e.target.checked)} disabled={busy} className="mt-0.5" />
            <span className="text-[12.5px]">Tôi sẽ <b>kết xuất lại ngay</b> bằng phần mềm CDB sau khi sửa xong.</span>
          </label>
        </div>

        <div className="shrink-0 px-5 py-3.5 border-t border-border flex items-center gap-2 justify-end">
          <button onClick={onClose} disabled={busy} className="h-9 px-4 rounded-lg border border-border text-[13px] hover:bg-muted disabled:opacity-50">Hủy bỏ</button>
          <button onClick={xacNhan} disabled={!duDieuKien} className="h-9 px-5 rounded-lg bg-kq text-white font-semibold text-[13px] hover:brightness-110 disabled:opacity-40 disabled:cursor-not-allowed inline-flex items-center gap-1.5">
            {busy && <Icon name="refresh" className="w-4 h-4 animate-spin" />} Mở sửa điểm
          </button>
        </div>
      </div>
    </div>
  );
}
