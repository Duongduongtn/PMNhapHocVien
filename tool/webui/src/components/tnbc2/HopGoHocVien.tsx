import { useRef, useState } from "react";
import { goHvKhoiBc2, LoiTnbc2, taoLoId, tienDoLo, type HvTrongBc2, type LoTn } from "../../lib/tnbc2Api";
import { soVN } from "../../lib/format";

// TNB-05 — hộp "Gỡ N học viên khỏi BC2": nêu tên + khóa gốc + "không tự quay lại BC2 cũ" → cảnh báo
// `TT_XuLy_Old` rỗng (phải tích đã xem) → tích CSDL thật → gỡ nền theo lô → đã/chưa gỡ → Làm tiếp.

const cho = (ms: number) => new Promise((r) => setTimeout(r, ms));

const LY_DO: Record<string, string> = {
  khong_con_o_bc2: "Học viên không còn ở BC2 này hoặc đã có kết quả — không gỡ",
  hv_khong_ton_tai: "Không còn học viên này",
  doi_giua_chung: "Phần mềm cũ vừa đổi học viên này — không gỡ",
};

export default function HopGoHocVien({
  maBc2,
  hocVien,
  onDong,
  onXong,
}: {
  maBc2: string;
  hocVien: HvTrongBc2[];
  onDong: () => void;
  /** Đã gửi lệnh gỡ và người dùng đóng hộp — để làm tươi chi tiết BC2. */
  onXong: () => void;
}) {
  const loId = useRef(taoLoId());
  const daGui = useRef(false);
  const [daXemCanhBao, setDaXemCanhBao] = useState(false);
  const [xacNhanThat, setXacNhanThat] = useState(false);
  const [dang, setDang] = useState(false);
  const [lo, setLo] = useState<LoTn | null>(null);
  const [loi, setLoi] = useState<string | null>(null);
  const [matKetNoi, setMatKetNoi] = useState(false);
  const [canhBaoServer, setCanhBaoServer] = useState("");

  const ten = (ma: string) => hocVien.find((h) => h.ma_dk === ma)?.ten ?? ma;
  const nCanhBao = hocVien.filter((h) => h.canh_bao_tt_cu).length;
  const dsMaDk = hocVien.map((h) => h.ma_dk);

  async function go() {
    setLoi(null);
    setMatKetNoi(false);
    setLo(null);
    setDang(true);
    daGui.current = true;
    let daGuiLenh = false;
    try {
      let t = await goHvKhoiBc2(maBc2, loId.current, dsMaDk, daXemCanhBao);
      daGuiLenh = true;
      setLo(t);
      let loiMang = 0;
      while (!t.xong) {
        await cho(800);
        try {
          t = await tienDoLo(loId.current);
          if (t.bi_gian_doan) throw new Error("bi_gian_doan");
          setLo(t);
          loiMang = 0;
        } catch (e) {
          if (e instanceof Error && e.message === "bi_gian_doan") throw e;
          if (++loiMang >= 5) throw e;
        }
      }
    } catch (e) {
      if (e instanceof LoiTnbc2 && !daGuiLenh) {
        setLoi(e.message);
        if (e.ma === "can_xac_nhan_canh_bao") {   // PM cũ vừa làm TT_XuLy_Old rỗng sau khi mở màn: cho tích đã xem
          const cb = (e.duLieu.canh_bao as { noi_dung: string }[] | undefined)?.[0]?.noi_dung ?? e.message;
          setCanhBaoServer(cb);
        }
      } else {
        setLo(null);
        setMatKetNoi(true);
        setLoi(
          e instanceof Error && e.message === "bi_gian_doan"
            ? "Tool bị tắt giữa chừng khi đang gỡ — bấm \"Làm tiếp\"; học viên đã gỡ không bị gỡ lại."
            : "Mất kết nối khi gỡ — bấm \"Làm tiếp\" để kiểm tra và gỡ nốt phần còn lại.",
        );
      }
    } finally {
      setDang(false);
    }
  }

  const xong = !!lo?.xong && !dang;
  const conDo = xong && (lo?.trang_thai === "loi_giua_chung" || (lo?.chua_ghi?.length ?? 0) > 0);
  const soDaGo = lo?.da_go?.length ?? 0;
  const thatBai = xong && lo?.trang_thai === "that_bai";
  const truocKhiGui = !lo && !dang && !matKetNoi;

  return (
    <div className="fixed inset-0 z-50 bg-black/40 grid place-items-center p-4">
      <div role="dialog" aria-modal="true" aria-label="Gỡ học viên khỏi BC2"
        className="bg-white rounded-xl shadow-2xl w-[640px] max-w-full max-h-[90vh] flex flex-col">
        <div className="p-4 border-b border-border font-semibold">
          {xong ? "Kết quả gỡ học viên" : `Gỡ ${soVN(hocVien.length)} học viên khỏi BC2 ${maBc2}?`}
        </div>

        <div className="p-4 overflow-auto space-y-3 text-[13px]">
          {truocKhiGui && (
            <>
              <div className="rounded-lg border border-warning/40 bg-warning/10 p-3 text-warning">
                Mỗi học viên về trạng thái trước đó và <b>không</b> tự quay lại BC2 cũ.
              </div>
              <ul className="list-disc pl-5 max-h-56 overflow-auto space-y-0.5">
                {hocVien.map((h) => (
                  <li key={h.ma_dk}>
                    {h.ten} — {h.ten_kh}
                    {h.ten_trang_thai_cu && <span className="text-muted-foreground"> · sẽ về "{h.ten_trang_thai_cu}"</span>}
                  </li>
                ))}
              </ul>
              {(nCanhBao > 0 || canhBaoServer) && (
                <label className="flex items-start gap-2 rounded-lg border border-warning/40 bg-warning/10 p-3 text-warning">
                  <input type="checkbox" className="mt-1" checked={daXemCanhBao} onChange={(e) => setDaXemCanhBao(e.target.checked)} />
                  <span>
                    {nCanhBao > 0
                      ? <>{soVN(nCanhBao)} học viên không có trạng thái trước đó được lưu — gỡ ra sẽ về giá trị rỗng.</>
                      : <>{canhBaoServer}.</>}{" "}
                    Tôi đã xem và vẫn muốn gỡ.
                  </span>
                </label>
              )}
            </>
          )}

          {dang && !lo && <div className="text-muted-foreground">Đang gửi…</div>}
          {dang && lo && !lo.xong && (
            <div>
              <div className="mb-1">Đang gỡ {soVN(lo.xu_ly ?? 0)}/{soVN(lo.tong)} học viên…</div>
              <div className="h-2 rounded bg-muted overflow-hidden">
                <div className="h-full bg-tn transition-all"
                  style={{ width: `${lo.tong ? Math.min(100, Math.round(((lo.xu_ly ?? 0) / lo.tong) * 100)) : 0}%` }} />
              </div>
            </div>
          )}

          {loi && <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-destructive">{loi}</div>}

          {thatBai && lo && (
            <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-destructive">
              {lo.loi_nghiep_vu?.noi_dung ?? lo.loi?.noi_dung ?? "Không gỡ được — chưa có học viên nào được gỡ."}
            </div>
          )}

          {xong && lo && !thatBai && (
            <>
              <div className="rounded-lg border border-success/40 bg-success/10 p-3">
                Đã gỡ <b>{soVN(soDaGo)}</b> học viên khỏi BC2 {maBc2}.
              </div>
              {(lo.bo_qua?.length ?? 0) > 0 && (
                <div className="rounded-lg border border-warning/40 bg-warning/10 p-3">
                  <div className="font-semibold text-warning mb-1">{soVN(lo.bo_qua!.length)} học viên không gỡ</div>
                  <ul className="max-h-40 overflow-auto space-y-0.5">
                    {lo.bo_qua!.map((b) => (
                      <li key={b.ma_dk}><b>{ten(b.ma_dk)}</b> — {LY_DO[b.ma_ly_do] ?? b.ly_do}</li>
                    ))}
                  </ul>
                </div>
              )}
              {(lo.chua_ghi?.length ?? 0) > 0 && (
                <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-destructive">
                  <div className="font-semibold">
                    CHƯA gỡ {soVN(lo.chua_ghi!.length)} học viên{lo.loi ? ` — lỗi ở ${ten(lo.loi.ma_dk)}: ${lo.loi.noi_dung}` : ""}
                  </div>
                  <div>Bấm "Làm tiếp" để gỡ nốt; học viên đã gỡ không bị gỡ lại.</div>
                </div>
              )}
              {(lo.canh_bao?.length ?? 0) > 0 && (
                <ul className="text-warning space-y-0.5">
                  {lo.canh_bao!.map((c, i) => (
                    <li key={i}>{c.ma_dk ? <b>{ten(c.ma_dk)}: </b> : null}{c.noi_dung}</li>
                  ))}
                </ul>
              )}
            </>
          )}
        </div>

        <div className="p-3 border-t border-border flex items-center gap-3">
          {truocKhiGui && (
            <label className="inline-flex items-center gap-2 text-[13px]">
              <input type="checkbox" checked={xacNhanThat} onChange={(e) => setXacNhanThat(e.target.checked)} />
              Tôi xác nhận đây là CSDL thật (DB Nạp)
            </label>
          )}
          <div className="ml-auto flex gap-2">
            {!dang && (
              <button type="button" onClick={() => (daGui.current ? onXong() : onDong())}
                className="h-9 px-4 rounded-lg border border-input text-[13px] font-semibold hover:bg-muted">
                {xong || matKetNoi || loi ? "Đóng" : "Giữ nguyên"}
              </button>
            )}
            {truocKhiGui && (
              <button type="button" onClick={go}
                disabled={!xacNhanThat || ((nCanhBao > 0 || !!canhBaoServer) && !daXemCanhBao)}
                className="h-9 px-4 rounded-lg bg-destructive text-white text-[13px] font-semibold disabled:opacity-45 disabled:cursor-not-allowed">
                Gỡ {soVN(hocVien.length)} học viên
              </button>
            )}
            {(conDo || matKetNoi) && !dang && (
              <button type="button" onClick={go} className="h-9 px-4 rounded-lg bg-tn text-white text-[13px] font-semibold">
                Làm tiếp
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
