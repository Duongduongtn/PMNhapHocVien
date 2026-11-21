import { useEffect, useState } from "react";
import { Icon } from "../../components/Icon";
import { moKhoaTrangThai, moKhoa, type MoKhoaTrangThai, type GoiHangDoi } from "../../lib/api";

// KQD-05 (task 77) — modal "Mở khóa để sửa điểm sau kết xuất", MỨC CƠ SỞ. Bám ui-mock/theodoiketxuat.html.
// Dùng chung cho cả tab Cập nhật KQĐT (KQD-02) và Theo dõi kết xuất (KQD-03).
// 2 ca theo cổng B-1: mở được (còn gói chưa gửi) / gói đã gửi hết → KHÔNG khóa cứng nữa (CHANGES #53):
// dẫn sang lối "Sửa sau gửi" chọn từng HV ở tab Cập nhật KQĐT (SuaSauGuiModal).
// Thao tác CSĐT-wide: xóa mọi gói chưa gửi + lùi MỌI HV 12 của cơ sở về 09/10.

export interface MoKhoaKetQuaUI {
  so_hv_mo: number;
  so_khoa: number;
  so_goi_xoa: number;
  so_hv_bo_qua: number;
}

function GoiRow({ g, da }: { g: GoiHangDoi; da: boolean }) {
  return (
    <div className={"flex items-center gap-2 text-[12px] rounded-md border px-2.5 py-1.5 " + (da ? "border-border bg-muted/40" : "border-warning/40 bg-warning/10")}>
      <Icon name="file" className={"w-4 h-4 shrink-0 " + (da ? "text-success" : "text-warning")} />
      <span className="truncate" title={g.ten_file}>{g.ten_file}</span>
      <span className="ml-auto shrink-0 text-muted-foreground tabular-nums">{g.ngay_tao ?? "—"}</span>
      <span className={"shrink-0 text-[11px] font-semibold border rounded-full px-2 py-0.5 " + (da ? "text-success border-success/40" : "text-warning border-warning/40")}>{da ? "Đã gửi" : "Chưa gửi"}</span>
    </div>
  );
}

export default function MoKhoaModal({
  targetKey, maKh, onClose, onDone,
}: {
  targetKey?: string;
  maKh?: string | null;
  onClose: () => void;
  onDone: (r: MoKhoaKetQuaUI) => void;
}) {
  const [tt, setTt] = useState<MoKhoaTrangThai | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [lyDo, setLyDo] = useState("");
  const [busy, setBusy] = useState(false);

  function taiTrangThai() {
    setLoading(true); setErr("");
    moKhoaTrangThai(targetKey)
      .then(setTt)
      .catch((e) => setErr(e instanceof Error ? e.message : "Không đọc được trạng thái cơ sở."))
      .finally(() => setLoading(false));
  }
  useEffect(taiTrangThai, [targetKey]);

  async function xacNhan() {
    setBusy(true); setErr("");
    try {
      const r = await moKhoa({ ma_kh: maKh, giai_trinh: lyDo.trim() || null }, targetKey);
      onDone({ so_hv_mo: r.so_hv_mo, so_khoa: r.so_khoa, so_goi_xoa: r.so_goi_xoa, so_hv_bo_qua: r.so_hv_bo_qua });
    } catch (e) {
      if (e instanceof Error && e.message === "khoa_cung") {
        setErr("Cơ sở vừa gửi hết gói đi Sở — không mở khóa được nữa.");
        taiTrangThai(); // chuyển sang ca khóa cứng M1
      } else {
        setErr(e instanceof Error ? e.message : "Không mở khóa được — kiểm kết nối rồi thử lại.");
      }
    } finally { setBusy(false); }
  }

  return (
    <div className="fixed inset-0 z-50">
      <div className="absolute inset-0 bg-black/40" onClick={onClose} />
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[560px] max-w-[94vw] bg-card rounded-xl shadow-2xl flex flex-col max-h-[90vh]">
        <div className="shrink-0 px-5 py-3.5 border-b border-border flex items-center gap-2">
          <Icon name="clock" className="w-5 h-5 text-kq" />
          <div className="font-bold text-[15px]">Mở khóa để sửa điểm</div>
          <button onClick={onClose} className="ml-auto text-muted-foreground hover:text-foreground"><Icon name="x" className="w-5 h-5" /></button>
        </div>

        <div className="flex-1 overflow-auto px-5 py-4 space-y-3.5 text-[13px]">
          {err && <div className="rounded-md border border-destructive/40 bg-destructive/5 px-3 py-2 text-[12.5px] text-destructive">{err}</div>}

          {loading ? (
            <div className="py-8 text-center text-muted-foreground inline-flex items-center gap-2 w-full justify-center"><Icon name="refresh" className="w-4 h-4 animate-spin" /> Đang kiểm gói hàng đợi của cơ sở…</div>
          ) : !tt ? null : tt.mo_duoc ? (
            // ── Ca MỞ ĐƯỢC: còn gói chưa gửi ──
            <>
              <div className="rounded-lg border border-success/40 bg-success/5 px-3 py-2.5">
                <div className="flex items-center gap-1.5 font-semibold text-success text-[12.5px] mb-1"><Icon name="check" className="w-4 h-4" sw={3} /> Còn gói CHƯA gửi — mở khóa an toàn</div>
                <div className="text-[12.5px] text-foreground">Cơ sở còn gói kết quả <b>chưa truyền đi Sở</b>. Hệ thống sẽ <b>xóa gói chưa gửi</b> để bản điểm sai không bị gửi, rồi mở khóa cho bạn sửa.</div>
                <div className="mt-2 space-y-1.5">
                  <div className="text-[11.5px] font-semibold text-warning">Gói sẽ bị xóa ({tt.goi_chua_gui.length})</div>
                  {tt.goi_chua_gui.map((g) => <GoiRow key={g.id} g={g} da={false} />)}
                </div>
              </div>
              <div className="rounded-lg border border-warning/40 bg-warning/10 px-3 py-2.5 text-[12.5px]">
                <div className="flex items-center gap-1.5 font-semibold text-warning mb-1"><Icon name="warn" className="w-4 h-4" /> Cần biết trước khi mở</div>
                <ul className="list-disc pl-5 space-y-0.5 text-foreground">
                  <li>Thao tác ở <b>mức cơ sở</b>: lùi <b>toàn bộ {tt.so_hv_mo} học viên đã kết xuất chưa gửi của cơ sở ({tt.so_khoa} khóa)</b> về "Đã cập nhật" (09/10) — <b>không chỉ khóa đang xem</b>.</li>
                  <li>Sửa xong phải <b>kết xuất lại</b> ở phần mềm CDB để gửi bản mới.</li>
                  {tt.so_hv_bo_qua > 0 && <li className="text-muted-foreground">{tt.so_hv_bo_qua} học viên "Đã kết xuất gửi Sở" (12) nhưng chưa có kết luận sẽ được <b>bỏ qua</b> (không đổi).</li>}
                </ul>
              </div>
              <div>
                <label className="text-[11px] font-semibold text-muted-foreground">Lý do mở khóa <span className="font-normal">(ghi vào cột Giải trình của hồ sơ)</span></label>
                <textarea value={lyDo} onChange={(e) => setLyDo(e.target.value)} maxLength={1000} className="w-full h-16 mt-1 text-[13px] px-2.5 py-1.5 rounded-lg border border-input bg-card focus:outline-none focus:border-kq focus:ring-2 focus:ring-kq/20" placeholder="Ví dụ: nhập nhầm điểm mô phỏng, cần sửa trước khi gửi Sở…" />
              </div>
            </>
          ) : (
            // ── Ca GÓI ĐÃ GỬI HẾT: không xóa được gói → lối "Sửa sau gửi" chọn từng HV (#53) ──
            <>
              <div className="rounded-lg border border-warning/40 bg-warning/10 px-3 py-2.5">
                <div className="flex items-center gap-1.5 font-semibold text-warning text-[12.5px] mb-1"><Icon name="warn" className="w-4 h-4" /> Kết quả đã gửi Sở — không xóa được gói</div>
                <div className="text-[12.5px] text-foreground">Mọi gói kết quả của cơ sở <b>đã truyền đi Sở</b>, không thu hồi được từ máy cơ sở. Bạn <b>vẫn sửa/bổ sung điểm được từng học viên</b>:</div>
                <ol className="list-decimal pl-5 mt-1.5 space-y-0.5 text-[12.5px] text-foreground">
                  <li>Vào tab <b>Cập nhật kết quả đào tạo</b>, chọn khóa.</li>
                  <li>Tích chọn học viên <b>đã gửi Sở</b> cần sửa rồi bấm <b>Mở sửa điểm</b> (nhập lý do + xác nhận).</li>
                  <li>Sửa điểm xong thì <b>kết xuất lại ngay</b> ở phần mềm CDB để gửi bản mới.</li>
                </ol>
                {tt.goi_da_gui.length > 0 && (
                  <div className="mt-2 space-y-1.5">
                    <div className="text-[11.5px] font-semibold text-success">Đã gửi ({tt.goi_da_gui.length})</div>
                    {tt.goi_da_gui.map((g) => <GoiRow key={g.id} g={g} da={true} />)}
                  </div>
                )}
                <div className="text-[11.5px] text-muted-foreground mt-2">Hệ thống <b>không xác định được HV nằm cụ thể gói nào</b> — danh sách HV ở trong file nén, không lưu trong CSDL. Học viên Sở đã duyệt (13) thì không sửa được.</div>
              </div>
            </>
          )}
        </div>

        <div className="shrink-0 px-5 py-3.5 border-t border-border flex items-center gap-2 justify-end">
          {!loading && tt?.mo_duoc ? (
            <>
              <button onClick={onClose} disabled={busy} className="h-9 px-4 rounded-lg border border-border text-[13px] hover:bg-muted disabled:opacity-50">Hủy bỏ</button>
              <button onClick={xacNhan} disabled={busy} className="h-9 px-5 rounded-lg bg-kq text-white font-semibold text-[13px] hover:brightness-110 disabled:opacity-60 inline-flex items-center gap-1.5">
                {busy && <Icon name="refresh" className="w-4 h-4 animate-spin" />} Xóa gói chưa gửi + mở khóa
              </button>
            </>
          ) : (
            <button onClick={onClose} className="h-9 px-5 rounded-lg border border-border text-[13px] hover:bg-muted">Đóng</button>
          )}
        </div>
      </div>
    </div>
  );
}
