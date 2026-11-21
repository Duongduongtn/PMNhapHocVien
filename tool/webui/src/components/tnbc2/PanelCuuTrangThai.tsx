import { useRef, useState } from "react";
import { cuuChuyen, cuuHoanTac, LoiTnbc2, taoLoId, type HvCuu, type KetQuaCuu, type LoaiHang } from "../../lib/tnbc2Api";
import MaTT from "../MaTT";

// TNB-06 — panel "Chuyển trạng thái học viên": chọn đích (không gõ mã tự do) + lý do bắt buộc → hộp xem lại
// "cũ → mới" → chuyển → hoàn tác một lần. Bám ui-mock/tnbc2.html `viewCuuPanel`, `cuuXemLai`.

const GIOI_HAN_LY_DO = 255;

export default function PanelCuuTrangThai({
  hv,
  loai,
  onDong,
  onDaDoi,
}: {
  hv: HvCuu;
  loai: LoaiHang | "";
  onDong: () => void;
  /** Đã chuyển hoặc hoàn tác xong — để làm tươi kết quả tìm kiếm. */
  onDaDoi: () => void;
}) {
  const dichDuoc = hv.dich.filter((d) => d.cho_phep);
  const [dich, setDich] = useState(dichDuoc[0]?.ma ?? "");
  const [lyDo, setLyDo] = useState("");
  const [xemLai, setXemLai] = useState(false);
  const [xacNhanThat, setXacNhanThat] = useState(false);
  const [dang, setDang] = useState(false);
  const [loi, setLoi] = useState<string | null>(null);
  const [matKetNoi, setMatKetNoi] = useState(false);
  const [kq, setKq] = useState<KetQuaCuu | null>(null);
  const [hoanTac, setHoanTac] = useState<KetQuaCuu | null>(null);
  const [loiHoanTac, setLoiHoanTac] = useState<string | null>(null);
  const loId = useRef(taoLoId());
  const loIdHoanTac = useRef(taoLoId());   // giữ nguyên khi gửi lại sau mất kết nối

  const d = hv.dich.find((x) => x.ma === dich);
  const lyDoCat = lyDo.trim();
  const duXemLai = !!d && d.cho_phep && lyDoCat.length > 0 && lyDoCat.length <= GIOI_HAN_LY_DO;

  async function chuyen() {
    setDang(true);
    setLoi(null);
    try {
      const r = await cuuChuyen(loId.current, hv.ma_dk, dich, lyDoCat, loai);
      setKq(r);
      setXemLai(false);
      setMatKetNoi(false);
      onDaDoi();
    } catch (e) {
      if (e instanceof LoiTnbc2 && e.http < 500 && e.ma !== "loi_he_thong") {
        if (matKetNoi) {
          // đã gửi lại sau khi mất kết nối mà bị từ chối: có thể lần trước ĐÃ chuyển xong → kiểm tra thay vì báo lỗi lạ
          setLoi(`${e.message} — nếu lần gửi trước đã chuyển xong thì học viên đã ở trạng thái mới; danh sách đang được làm tươi để kiểm tra.`);
          onDaDoi();
        } else {
          setMatKetNoi(false);
          setLoi(e.message);
        }
      } else {
        // chưa biết đã chuyển chưa: gửi lại CÙNG lo_id — máy chủ không chuyển hai lần
        setMatKetNoi(true);
        setLoi("Chưa biết đã chuyển được hay chưa (mất kết nối hoặc lỗi máy chủ) — bấm \"Gửi lại\"; tool kiểm tra, không chuyển hai lần.");
      }
    } finally {
      setDang(false);
    }
  }

  async function hoan() {
    if (!kq) return;
    setDang(true);
    setLoiHoanTac(null);
    try {
      const r = await cuuHoanTac(kq.lo_id, loIdHoanTac.current);
      setHoanTac(r);
      onDaDoi();
    } catch (e) {
      setLoiHoanTac(e instanceof LoiTnbc2 ? e.message : "Mất kết nối khi hoàn tác — làm tươi rồi kiểm tra trạng thái học viên.");
    } finally {
      setDang(false);
    }
  }

  return (
    <aside className="shrink-0 w-[380px] border-l border-border bg-card p-3 overflow-auto space-y-3" aria-label="Chuyển trạng thái học viên">
      <div className="flex items-center">
        <div className="text-[13px] font-semibold">Chuyển trạng thái học viên</div>
        <button type="button" onClick={onDong} className="ml-auto text-[12px] text-muted-foreground hover:text-foreground">Đóng</button>
      </div>

      <div className="rounded-lg border border-border p-3 text-[13px]">
        <b>{hv.ten}</b>
        <div className="font-mono text-[12px] text-muted-foreground">{hv.cmt} · {hv.ten_kh || hv.ma_kh}</div>
        <div className="mt-1">
          Hiện tại: {hv.ten_trang_thai} <MaTT ma={hv.tt} />
        </div>
      </div>

      {!kq && hv.khong_hien.ma === "khoa_chua_be_giang" && (
        <div className="rounded-lg border border-warning/40 bg-warning/10 px-3 py-2 text-[12.5px] text-warning">
          Khóa của học viên này chưa bế giảng. Chuyển trạng thái <b>không</b> làm học viên hiện vào danh sách BC2 — điều kiện
          nằm ở ngày bế giảng của khóa.
        </div>
      )}

      {!kq && (
        <>
          <fieldset className="space-y-1.5">
            <legend className="field-label">Chuyển sang</legend>
            {hv.dich.map((x) => (
              <label key={x.ma}
                className={`flex items-start gap-2 rounded-lg border px-3 py-2 text-[13px] ${
                  x.cho_phep ? "border-border cursor-pointer hover:bg-muted" : "border-border opacity-55 cursor-not-allowed"} ${dich === x.ma && x.cho_phep ? "bg-tn-soft border-tn-border" : ""}`}>
                <input type="radio" name="dich-cuu" className="mt-1" value={x.ma} disabled={!x.cho_phep}
                  checked={dich === x.ma} onChange={() => setDich(x.ma)} />
                <span>
                  {x.ten} <MaTT ma={x.ma} />
                  {!x.cho_phep && x.ly_do && <span className="block text-[11.5px] text-destructive">{x.ly_do}</span>}
                </span>
              </label>
            ))}
          </fieldset>

          <div>
            <label className="field-label" htmlFor="cuu-ly-do">Lý do (bắt buộc, ghi vào nhật ký)</label>
            <textarea id="cuu-ly-do" className="field-input" style={{ height: 72, padding: 8 }} value={lyDo}
              maxLength={GIOI_HAN_LY_DO + 20} placeholder="vd: nhập nhầm trạng thái vắng, học viên thực tế đã thi"
              onChange={(e) => setLyDo(e.target.value)} />
            <div className={`text-[11px] text-right ${lyDoCat.length > GIOI_HAN_LY_DO ? "text-destructive" : "text-muted-foreground"}`}>
              {lyDoCat.length}/{GIOI_HAN_LY_DO}
            </div>
          </div>

          <div className="rounded-lg bg-muted px-3 py-2 text-[12px] text-muted-foreground">
            Chỉ đổi trạng thái, không đụng số BC2, kết quả hay số giấy. Có nút <b>Hoàn tác</b> ngay sau khi chuyển (chỉ khi
            học viên chưa bị phần mềm cũ đổi tiếp).
          </div>

          {dichDuoc.length === 0 && (
            <div className="rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-[13px] text-destructive">
              Học viên này không chuyển được sang đích nào — xem lý do ở từng đích.
            </div>
          )}

          <div className="flex gap-2">
            <button type="button" onClick={onDong} className="h-9 px-4 rounded-lg border border-input text-[13px] font-semibold hover:bg-muted">Hủy</button>
            <button type="button" disabled={!duXemLai} onClick={() => setXemLai(true)}
              className="h-9 px-4 rounded-lg bg-tn text-white text-[13px] font-semibold disabled:opacity-45 disabled:cursor-not-allowed">
              Xem lại
            </button>
          </div>
        </>
      )}

      {kq && (
        <div className="space-y-2">
          <div className="rounded-lg border border-success/40 bg-success/10 p-3 text-[13px]">
            Đã chuyển <b>{hv.ten}</b> từ "{kq.ten_trang_thai_cu ?? hv.ten_trang_thai}" sang "{kq.ten_trang_thai_moi}"{" "}
            <MaTT ma={kq.tt_moi} />.
            {kq.da_ton_tai && <div className="text-muted-foreground mt-1">(Lệnh này đã được thực hiện từ trước.)</div>}
          </div>
          {kq.canh_bao.length > 0 && (
            <ul className="text-[13px] text-warning space-y-0.5">{kq.canh_bao.map((c) => <li key={c.ma}>{c.noi_dung}</li>)}</ul>
          )}
          {hoanTac && (
            <div className="rounded-lg border border-border bg-card p-3 text-[13px]">
              Đã hoàn tác về "{hoanTac.ten_trang_thai_moi}" <MaTT ma={hoanTac.tt_moi} />.
            </div>
          )}
          {loiHoanTac && (
            <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-[13px] text-destructive">{loiHoanTac}</div>
          )}
          <div className="flex gap-2">
            {!hoanTac && (
              <button type="button" disabled={dang} onClick={hoan}
                className="h-9 px-4 rounded-lg border border-destructive/50 text-destructive text-[13px] font-semibold hover:bg-destructive/10">
                Hoàn tác
              </button>
            )}
            <button type="button" onClick={onDong} className="h-9 px-4 rounded-lg border border-input text-[13px] font-semibold hover:bg-muted">Xong</button>
          </div>
        </div>
      )}

      {xemLai && d && (
        <div className="fixed inset-0 z-50 bg-black/40 grid place-items-center p-4">
          <div role="dialog" aria-modal="true" aria-label="Xác nhận chuyển trạng thái"
            className="bg-white rounded-xl shadow-2xl w-[560px] max-w-full flex flex-col">
            <div className="p-4 border-b border-border font-semibold">Xác nhận chuyển trạng thái</div>
            <div className="p-4 space-y-3 text-[13px]">
              <div className="flex items-center justify-center gap-3 flex-wrap py-2">
                <span className="rounded-lg border border-border px-3 py-1.5">
                  {hv.ten_trang_thai} <MaTT ma={hv.tt} />
                </span>
                <span className="text-2xl" aria-hidden>→</span>
                <span className="rounded-lg border border-tn-border bg-tn-soft px-3 py-1.5 font-medium">
                  {d.ten} <MaTT ma={d.ma} />
                </span>
              </div>
              <div><b>{hv.ten}</b> · {hv.ten_kh || hv.ma_kh}<br />Lý do: <i>{lyDoCat}</i></div>
              <div className="rounded-lg border border-warning/40 bg-warning/10 p-3 text-warning">
                Ghi thẳng vào dữ liệu thật, phần mềm cũ thấy ngay. Sau khi chuyển có thể hoàn tác.
              </div>
              <details className="text-[12px] text-muted-foreground">
                <summary className="cursor-pointer underline decoration-dotted">Chi tiết kỹ thuật (dành cho IT)</summary>
                <div className="mt-1 leading-relaxed">
                  Gọi <span className="font-mono">usp_NguoiLX_HoSo_UpdateTTXLy</span> cho mã đăng ký{" "}
                  <span className="font-mono">{hv.ma_dk}</span>, đích <span className="font-mono">{d.ma}</span>. SP ghi đè{" "}
                  <span className="font-mono">TT_XuLy_Old</span> nên việc hoàn tác dùng trạng thái cũ lưu trong nhật ký của tool.
                </div>
              </details>
              <label className="inline-flex items-center gap-2">
                <input type="checkbox" checked={xacNhanThat} onChange={(e) => setXacNhanThat(e.target.checked)} />
                Tôi xác nhận đây là CSDL thật (DB Nạp)
              </label>
              {loi && <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-destructive">{loi}</div>}
            </div>
            <div className="p-3 border-t border-border flex justify-end gap-2">
              <button type="button" disabled={dang} onClick={() => setXemLai(false)}
                className="h-9 px-4 rounded-lg border border-input text-[13px] font-semibold hover:bg-muted">Quay lại</button>
              <button type="button" disabled={dang || !xacNhanThat} onClick={chuyen}
                className="h-9 px-4 rounded-lg bg-tn text-white text-[13px] font-semibold disabled:opacity-45 disabled:cursor-not-allowed">
                {matKetNoi ? "Gửi lại" : "Chuyển"}
              </button>
            </div>
          </div>
        </div>
      )}
    </aside>
  );
}
