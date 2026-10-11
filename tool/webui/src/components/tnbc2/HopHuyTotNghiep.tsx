import { useRef, useState } from "react";
import { huyTotNghiep, LoiTnbc2, taoLoId, tienDoLo, type LoTn } from "../../lib/tnbc2Api";
import { soVN } from "../../lib/format";

// TNB-02 — hộp "Hủy kết quả tốt nghiệp": nêu tên + số giấy sẽ bị xóa → xác nhận CSDL thật → hủy nền theo lô
// → đã/chưa hủy → "Làm tiếp". Giữ nguyên sổ/quyết định/ngày (server chỉ xóa số giấy, đưa 09 → 03).

const cho = (ms: number) => new Promise((r) => setTimeout(r, ms));

const LY_DO: Record<string, string> = {
  doi_giua_chung: "Phần mềm cũ vừa đổi học viên này — không hủy",
};

interface Props {
  maKh: string;
  hocVien: { ma_dk: string; ten: string; so_giay: string }[];
  onDong: () => void;
  /** Gọi khi đã gửi lệnh hủy và người dùng đóng hộp — để làm tươi danh sách. */
  onXong: () => void;
}

export default function HopHuyTotNghiep({ maKh, hocVien, onDong, onXong }: Props) {
  const loId = useRef(taoLoId());
  const [xacNhan, setXacNhan] = useState(false);
  const [dang, setDang] = useState(false);
  const [lo, setLo] = useState<LoTn | null>(null);
  const [loi, setLoi] = useState<string | null>(null);
  const [boQuaTruoc, setBoQuaTruoc] = useState<{ ma_dk: string; ly_do: string }[]>([]);
  const [matKetNoi, setMatKetNoi] = useState(false);
  const daGui = useRef(false);

  const ten = (ma: string) => hocVien.find((h) => h.ma_dk === ma)?.ten ?? ma;
  const dsMaDk = hocVien.map((h) => h.ma_dk);

  async function huy() {
    setLoi(null);
    setBoQuaTruoc([]);
    setMatKetNoi(false);
    setLo(null);
    setDang(true);
    daGui.current = true;
    try {
      let t = await huyTotNghiep(loId.current, maKh, dsMaDk);
      setLo(t);
      let loiMang = 0;
      while (!t.xong) {
        await cho(800);
        try {
          t = await tienDoLo(loId.current);
          if (t.bi_gian_doan) {
            setLo(null);
            setMatKetNoi(true);
            setLoi(`Tool bị tắt giữa chừng khi đang hủy (đã hủy ${t.da_huy?.length ?? 0}/${t.tong} học viên) — bấm "Làm tiếp" để hủy nốt, học viên đã hủy không bị hủy lại.`);
            return;
          }
          setLo(t);
          loiMang = 0;
        } catch (e) {
          if (++loiMang >= 5) throw e;
        }
      }
    } catch (e) {
      if (e instanceof LoiTnbc2) {
        setLoi(e.message);
        const bq = (e.duLieu.bo_qua as { ma_dk: string; ly_do: string }[] | undefined) ?? [];
        setBoQuaTruoc(bq);
      } else {
        setMatKetNoi(true);
        setLoi("Mất kết nối khi hủy — bấm \"Làm tiếp\" để kiểm tra và hủy nốt phần còn lại.");
      }
    } finally {
      setDang(false);
    }
  }

  const xong = !!lo?.xong && !dang;
  const conDo = xong && (lo?.trang_thai === "loi_giua_chung" || (lo?.chua_ghi?.length ?? 0) > 0);
  const soDaHuy = (lo?.da_huy?.length ?? 0) + (lo?.da_huy_truoc?.length ?? 0);

  return (
    <div className="fixed inset-0 z-50 bg-black/40 grid place-items-center p-4">
      <div role="dialog" aria-modal="true" aria-label="Hủy kết quả tốt nghiệp"
        className="bg-white rounded-xl shadow-2xl w-[620px] max-w-full max-h-[90vh] flex flex-col">
        <div className="p-4 border-b border-border font-semibold">
          {xong ? "Kết quả hủy tốt nghiệp" : "Hủy kết quả tốt nghiệp?"}
        </div>

        <div className="p-4 overflow-auto space-y-3 text-[13px]">
          {!dang && !lo && (
            <>
              <div className="rounded-lg border border-warning/40 bg-warning/10 p-3 text-warning">
                Sẽ xóa số giấy của <b>{soVN(hocVien.length)}</b> học viên và đưa về{" "}
                <b>"Đã học xong, chưa tốt nghiệp"</b>. Thông tin sổ/quyết định giữ nguyên để nhập lại.
              </div>
              <ul className="list-disc pl-5 max-h-56 overflow-auto space-y-0.5">
                {hocVien.map((h) => (
                  <li key={h.ma_dk}>
                    {h.ten} — <span className="font-mono">{h.so_giay || "(chưa có số giấy)"}</span>
                  </li>
                ))}
              </ul>
              <div className="text-[12px] text-muted-foreground">
                Học viên đã vào BC2 không hủy được — phải gỡ khỏi BC2 trước (tab Báo cáo 2).
              </div>
            </>
          )}

          {dang && !lo && <div className="text-muted-foreground">Đang gửi…</div>}
          {dang && lo && !lo.xong && (
            <div>
              <div className="mb-1">Đang hủy {soVN(lo.xu_ly ?? 0)}/{soVN(lo.tong)} học viên…</div>
              <div className="h-2 rounded bg-muted overflow-hidden">
                <div className="h-full bg-tn transition-all"
                  style={{ width: `${lo.tong ? Math.min(100, Math.round(((lo.xu_ly ?? 0) / lo.tong) * 100)) : 0}%` }} />
              </div>
            </div>
          )}

          {loi && <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-destructive">{loi}</div>}
          {boQuaTruoc.length > 0 && (
            <ul className="space-y-0.5">
              {boQuaTruoc.map((b) => (
                <li key={b.ma_dk}><b>{ten(b.ma_dk)}</b> — {b.ly_do}</li>
              ))}
            </ul>
          )}

          {xong && lo && (
            <>
              <div className="rounded-lg border border-success/40 bg-success/10 p-3">
                Đã hủy tốt nghiệp <b>{soVN(soDaHuy)}</b> học viên
                {(lo.da_huy_truoc?.length ?? 0) > 0 && <> (trong đó {soVN(lo.da_huy_truoc!.length)} đã hủy từ lần trước)</>}.
                {soDaHuy > 0 && <div className="text-muted-foreground mt-1">Họ trở lại "Đã học xong, chưa tốt nghiệp"; số sổ/quyết định giữ nguyên.</div>}
              </div>
              {(lo.bo_qua?.length ?? 0) > 0 && (
                <div className="rounded-lg border border-warning/40 bg-warning/10 p-3">
                  <div className="font-semibold text-warning mb-1">{soVN(lo.bo_qua!.length)} học viên không hủy</div>
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
                    CHƯA hủy {soVN(lo.chua_ghi!.length)} học viên{lo.loi ? ` — lỗi ở ${ten(lo.loi.ma_dk)}: ${lo.loi.noi_dung}` : ""}
                  </div>
                  <div>Bấm "Làm tiếp" để hủy nốt; học viên đã hủy không bị hủy lại.</div>
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
          {!dang && !lo && !matKetNoi && (
            <label className="inline-flex items-center gap-2 text-[13px]">
              <input type="checkbox" checked={xacNhan} onChange={(e) => setXacNhan(e.target.checked)} />
              Tôi xác nhận đây là CSDL thật (DB Nạp)
            </label>
          )}
          <div className="ml-auto flex gap-2">
            {!dang && (
              <button type="button" onClick={() => (daGui.current ? onXong() : onDong())}
                className="h-9 px-4 rounded-lg border border-input text-[13px] font-semibold hover:bg-muted">
                {xong || loi ? "Đóng" : "Giữ nguyên"}
              </button>
            )}
            {!dang && !lo && !matKetNoi && !xong && boQuaTruoc.length === 0 && (
              <button type="button" onClick={huy} disabled={!xacNhan}
                className="h-9 px-4 rounded-lg bg-destructive text-white text-[13px] font-semibold disabled:opacity-45 disabled:cursor-not-allowed">
                Hủy tốt nghiệp
              </button>
            )}
            {(conDo || matKetNoi) && !dang && (
              <button type="button" onClick={huy}
                className="h-9 px-4 rounded-lg bg-tn text-white text-[13px] font-semibold">
                Làm tiếp
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
