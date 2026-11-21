import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import ChuGiaiTrangThai from "../ChuGiaiTrangThai";
import HopGoHocVien from "./HopGoHocVien";
import { soVN } from "../../lib/format";
import {
  chiTietBc2,
  hoanTacLoThem,
  LoiTnbc2,
  taoLoId,
  tienDoLo,
  xoaBc2,
  type ChiTietBc2,
  type HvTrongBc2,
  type LoTn,
} from "../../lib/tnbc2Api";
import { khopTim } from "../../lib/tnbcUngVien";
import MaTT from "../MaTT";
import TrangThaiBc2 from "./TrangThaiBc2";

// TNB-05 — màn xem / gỡ / xóa BC2 (ít dùng hơn thêm). Bám ui-mock/tnbc2.html `viewXem`, `xacNhanGo`.

const cho = (ms: number) => new Promise((r) => setTimeout(r, ms));
const dmy = (iso: string) => (iso ? iso.slice(0, 10).split("-").reverse().join("/") : "");
const nutNho = "h-9 px-3 rounded-lg border border-input bg-white text-[13px] font-semibold hover:bg-muted disabled:opacity-45 disabled:cursor-not-allowed";

type Hop = "" | "go" | "xoa" | "hoan_tac";

export default function XemBc2({
  maBc2,
  onVe,
  onThem,
  onIn,
}: {
  maBc2: string;
  onVe: () => void;
  onThem: (ct: ChiTietBc2) => void;
  onIn: (ma: string) => void;
}) {
  const [ct, setCt] = useState<ChiTietBc2 | null>(null);
  const [loi, setLoi] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [sel, setSel] = useState<Set<string>>(new Set());
  const [hop, setHop] = useState<Hop>("");
  const [tai, setTai] = useState(0);

  useEffect(() => {
    let huy = false;
    setLoi(null);
    chiTietBc2(maBc2)
      .then((d) => {
        if (huy) return;
        setCt(d);
        const goDuoc = new Set(d.hoc_vien.filter((h) => h.go_duoc).map((h) => h.ma_dk));
        setSel((s) => new Set([...s].filter((m) => goDuoc.has(m))));
      })
      .catch((e: unknown) => { if (!huy) { setCt(null); setLoi(e instanceof Error ? e.message : "Không tải được BC2"); } });
    return () => { huy = true; };
  }, [maBc2, tai]);

  const ds = useMemo(() => (ct?.hoc_vien ?? []).filter((h) => khopTim(h, q)), [ct, q]);
  const hvChon = useMemo(() => (ct?.hoc_vien ?? []).filter((h) => sel.has(h.ma_dk)), [ct, sel]);
  const lamTuoi = useCallback(() => setTai((n) => n + 1), []);

  const doi = (h: HvTrongBc2, bat: boolean) =>
    setSel((s) => { const n = new Set(s); if (bat) n.add(h.ma_dk); else n.delete(h.ma_dk); return n; });

  return (
    <div className="h-full flex flex-col min-h-0">
      <div className="shrink-0 bg-card border-b border-border px-4 py-2.5 flex flex-wrap items-center gap-3">
        <button type="button" onClick={onVe} className={nutNho}>← Danh sách BC2</button>
        {ct && (
          <>
            <div>
              <div className="text-[11px] text-muted-foreground">BC2 {ct.loai === "oto" ? "ô tô" : ct.loai === "moto" ? "mô tô" : ""}</div>
              <div className="font-semibold font-mono text-[15px]">{ct.ma_bc2}</div>
            </div>
            <div className="text-[12.5px] leading-snug border-l border-border pl-3">
              Ngày <b>{dmy(ct.ngay_bao_cao)}</b><br /><b>{ct.ten_kh || "—"}</b>
            </div>
            <div className="text-[12.5px] leading-snug border-l border-border pl-3">
              Tổng ghi <b>{ct.tong_ghi ?? "—"}</b> · Học viên thực tế <b>{soVN(ct.hv_thuc_te)}</b>
              {ct.lech && <span className="ml-1 text-muted-foreground">(lệch là bình thường)</span>}
            </div>
            <TrangThaiBc2 tt={ct.trang_thai ?? (ct.dang_mo ? 0 : 1)} hvKetQua={ct.hv_ket_qua} chiXem />
          </>
        )}
        <input aria-label="Tìm học viên trong BC2" className="field-input ml-auto" style={{ width: 240 }} value={q}
          placeholder="Tìm tên / số CMT" onChange={(e) => setQ(e.target.value)} />
        <button type="button" className={nutNho} onClick={lamTuoi}>Làm tươi</button>
        <button type="button" className={nutNho} onClick={() => onIn(maBc2)} disabled={!ct || ct.hv_thuc_te === 0}
          data-testid="in-bc2-tu-xem">In BC2</button>
        <ChuGiaiTrangThai />
        <button type="button" disabled={!ct?.xoa_duoc} onClick={() => setHop("xoa")}
          title="Chỉ xóa được BC2 đang mở và không còn học viên"
          className="h-9 px-3 rounded-lg border border-destructive/50 text-destructive text-[13px] font-semibold hover:bg-destructive/10 disabled:opacity-45 disabled:cursor-not-allowed">
          Xóa BC2 rỗng
        </button>
      </div>

      <div className="flex-1 min-h-0 overflow-auto">
        {loi && <div className="m-3 rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-[13px] text-destructive">{loi}</div>}
        {!ct && !loi && <div className="p-4 text-[13px] text-muted-foreground">Đang tải…</div>}
        {ct && (
          <>
            <div className="m-3 rounded-lg bg-muted px-3 py-2 text-[12.5px] text-muted-foreground">
              Chỉ gỡ được học viên còn ở "Đã vào BC2, chờ kết quả". Học viên đã có kết quả bị khóa vì gỡ sẽ làm mất kết quả.
            </div>
            <table className="w-full text-[13px]">
              <thead className="sticky top-0 bg-card border-b border-border z-10">
                <tr className="text-left text-[12px] text-muted-foreground">
                  <th className="w-8 px-3 py-2" />
                  <th className="py-2 pr-3 font-semibold">Tên học viên</th>
                  <th className="py-2 pr-3 font-semibold">Ngày sinh</th>
                  <th className="py-2 pr-3 font-semibold">Số CMT</th>
                  <th className="py-2 pr-3 font-semibold">Khóa gốc</th>
                  <th className="py-2 pr-3 font-semibold">Trạng thái</th>
                </tr>
              </thead>
              <tbody>
                {ds.length === 0 && (
                  <tr><td colSpan={6} className="text-center text-muted-foreground py-10">
                    {ct.hoc_vien.length ? "Không có học viên phù hợp." : "Chưa có học viên trong BC2 này."}
                  </td></tr>
                )}
                {ds.map((h) => (
                  <tr key={h.ma_dk} className={`border-b border-border ${sel.has(h.ma_dk) ? "bg-tn-soft" : ""} ${h.go_duoc ? "" : "text-muted-foreground bg-muted/40"}`}>
                    <td className="px-3 py-1.5">
                      <input type="checkbox" aria-label={`Chọn ${h.ten}`} checked={sel.has(h.ma_dk)} disabled={!h.go_duoc}
                        onChange={(e) => doi(h, e.target.checked)} />
                    </td>
                    <td className="py-1.5 pr-3 font-medium whitespace-nowrap">{h.ten}</td>
                    <td className="py-1.5 pr-3 tabular-nums whitespace-nowrap">{h.ngay_sinh}</td>
                    <td className="py-1.5 pr-3 font-mono text-[12px]">{h.cmt}</td>
                    <td className="py-1.5 pr-3">{h.ten_kh}</td>
                    <td className="py-1.5 pr-3">
                      <span className="text-[12px]">{h.ten_trang_thai}</span>
                      <MaTT ma={h.tt} />
                      {h.ly_do_khoa && <div className="text-[11px] text-warning mt-0.5">{h.ly_do_khoa}</div>}
                      {h.go_duoc && h.canh_bao_tt_cu && (
                        <div className="text-[11px] text-warning mt-0.5">Không có trạng thái trước đó — gỡ ra sẽ về giá trị rỗng</div>
                      )}
                      {h.khac_khoa_bc1 && <div className="text-[11px] text-muted-foreground mt-0.5">Thi lại từ khóa khác</div>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
      </div>

      <div className="shrink-0 h-14 bg-card border-t border-border px-4 flex items-center gap-3">
        <span className="text-[13px]"><b>{soVN(hvChon.length)}</b> học viên đã chọn</span>
        <button type="button" className={nutNho} disabled={!ct?.dang_mo} onClick={() => setHop("hoan_tac")}>
          Hoàn tác lần thêm vừa rồi
        </button>
        <button type="button" className={nutNho} disabled={!ct?.dang_mo} onClick={() => ct && onThem(ct)}>
          + Thêm học viên
        </button>
        <button type="button" disabled={hvChon.length === 0 || !ct?.dang_mo} onClick={() => setHop("go")}
          className="ml-auto h-9 px-4 rounded-lg bg-destructive text-white text-[13px] font-semibold disabled:opacity-45 disabled:cursor-not-allowed">
          Gỡ {soVN(hvChon.length)} học viên khỏi BC2
        </button>
      </div>

      {hop === "go" && ct && (
        <HopGoHocVien maBc2={ct.ma_bc2} hocVien={hvChon} onDong={() => setHop("")}
          onXong={() => { setHop(""); setSel(new Set()); lamTuoi(); }} />
      )}
      {hop === "xoa" && ct && (
        <HopXoaBc2 maBc2={ct.ma_bc2} onDong={() => setHop("")} onXong={onVe} />
      )}
      {hop === "hoan_tac" && ct && (
        <HopHoanTac maBc2={ct.ma_bc2} tenHv={Object.fromEntries(ct.hoc_vien.map((h) => [h.ma_dk, h.ten]))}
          onDong={() => setHop("")}
          onXong={() => { setHop(""); setSel(new Set()); lamTuoi(); }} />
      )}
    </div>
  );
}

function Khung({ nhan, tieuDe, children, chan }: { nhan: string; tieuDe: string; children: React.ReactNode; chan: React.ReactNode }) {
  return (
    <div className="fixed inset-0 z-50 bg-black/40 grid place-items-center p-4">
      <div role="dialog" aria-modal="true" aria-label={nhan}
        className="bg-white rounded-xl shadow-2xl w-[560px] max-w-full max-h-[90vh] flex flex-col">
        <div className="p-4 border-b border-border font-semibold">{tieuDe}</div>
        <div className="p-4 overflow-auto space-y-3 text-[13px]">{children}</div>
        <div className="p-3 border-t border-border flex items-center gap-3">{chan}</div>
      </div>
    </div>
  );
}

function HopXoaBc2({ maBc2, onDong, onXong }: { maBc2: string; onDong: () => void; onXong: () => void }) {
  const [xacNhan, setXacNhan] = useState(false);
  const [dang, setDang] = useState(false);
  const [loi, setLoi] = useState<string | null>(null);
  const [xong, setXong] = useState(false);
  async function xoa() {
    setDang(true);
    setLoi(null);
    try {
      await xoaBc2(maBc2);
      setXong(true);
    } catch (e) {
      setLoi(e instanceof LoiTnbc2 ? e.message : "Mất kết nối khi xóa — mở lại danh sách để kiểm BC2 đã xóa chưa rồi thử lại.");
    } finally {
      setDang(false);
    }
  }
  return (
    <Khung nhan="Xóa BC2 rỗng" tieuDe={xong ? "Đã xóa BC2" : `Xóa BC2 ${maBc2}?`}
      chan={
        <>
          {!xong && (
            <label className="inline-flex items-center gap-2">
              <input type="checkbox" checked={xacNhan} onChange={(e) => setXacNhan(e.target.checked)} />
              Tôi xác nhận đây là CSDL thật (DB Nạp)
            </label>
          )}
          <div className="ml-auto flex gap-2">
            <button type="button" disabled={dang} onClick={xong ? onXong : onDong} className={nutNho}>{xong ? "Về danh sách" : "Giữ nguyên"}</button>
            {!xong && (
              <button type="button" disabled={dang || !xacNhan} onClick={xoa}
                className="h-9 px-4 rounded-lg bg-destructive text-white text-[13px] font-semibold disabled:opacity-45 disabled:cursor-not-allowed">
                Xóa BC2
              </button>
            )}
          </div>
        </>
      }>
      {xong ? (
        <div className="rounded-lg border border-success/40 bg-success/10 p-3">Đã xóa BC2 số <b className="font-mono">{maBc2}</b>.</div>
      ) : (
        <>
          <div className="rounded-lg border border-warning/40 bg-warning/10 p-3 text-warning">
            BC2 này không còn học viên nào. Xóa sẽ bỏ hẳn phiếu BC2 khỏi cơ sở dữ liệu, không hoàn tác được.
          </div>
          {loi && <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-destructive">{loi}</div>}
        </>
      )}
    </Khung>
  );
}

function HopHoanTac({ maBc2, tenHv, onDong, onXong }: { maBc2: string; tenHv: Record<string, string>; onDong: () => void; onXong: () => void }) {
  const [xacNhan, setXacNhan] = useState(false);
  const [dang, setDang] = useState(false);
  const [lo, setLo] = useState<LoTn | null>(null);
  const [loi, setLoi] = useState<string | null>(null);
  const loId = useRef(taoLoId());
  async function chay() {
    // "Làm tiếp" sau lỗi giữa chừng: lô gốc chưa bị đánh dấu đã hoàn tác nên làm lại được bằng lô hoàn tác mới;
    // học viên đã gỡ ở lần trước sẽ được bỏ qua (không còn ở BC2).
    if (lo) loId.current = taoLoId();
    setLo(null);
    setDang(true);
    setLoi(null);
    try {
      let t = await hoanTacLoThem(maBc2, loId.current);
      setLo(t);
      let loiMang = 0;
      while (!t.xong) {
        await cho(800);
        try {
          t = await tienDoLo(loId.current);
          setLo(t);
          loiMang = 0;
        } catch (e) {
          if (++loiMang >= 5) throw e;
        }
      }
    } catch (e) {
      setLoi(e instanceof LoiTnbc2 ? e.message : "Mất kết nối khi hoàn tác — mở lại BC2 để kiểm tra.");
    } finally {
      setDang(false);
    }
  }
  const xong = !!lo?.xong && !dang;
  const thatBai = xong && lo?.trang_thai === "that_bai";
  const dangDo = xong && lo?.trang_thai === "loi_giua_chung";
  return (
    <Khung nhan="Hoàn tác lần thêm vừa rồi" tieuDe={xong ? "Kết quả hoàn tác" : "Hoàn tác lần thêm vừa rồi?"}
      chan={
        <>
          {!lo && !dang && (
            <label className="inline-flex items-center gap-2">
              <input type="checkbox" checked={xacNhan} onChange={(e) => setXacNhan(e.target.checked)} />
              Tôi xác nhận đây là CSDL thật (DB Nạp)
            </label>
          )}
          <div className="ml-auto flex gap-2">
            {!dang && <button type="button" onClick={xong || loi ? onXong : onDong} className={nutNho}>{xong || loi ? "Đóng" : "Giữ nguyên"}</button>}
            {dangDo && !dang && (
              <button type="button" onClick={chay} className="h-9 px-4 rounded-lg bg-tn text-white text-[13px] font-semibold">Làm tiếp</button>
            )}
            {!lo && !dang && !loi && (
              <button type="button" disabled={!xacNhan} onClick={chay}
                className="h-9 px-4 rounded-lg bg-destructive text-white text-[13px] font-semibold disabled:opacity-45 disabled:cursor-not-allowed">
                Hoàn tác
              </button>
            )}
          </div>
        </>
      }>
      {!lo && !dang && !loi && (
        <div className="rounded-lg border border-warning/40 bg-warning/10 p-3 text-warning">
          Gỡ đúng các học viên của lần thêm gần nhất vào BC2 này (chỉ người còn ở "Đã vào BC2, chờ kết quả"). Mỗi lần thêm
          chỉ hoàn tác được một lần.
        </div>
      )}
      {dang && <div className="text-muted-foreground">Đang hoàn tác…</div>}
      {loi && <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-destructive">{loi}</div>}
      {thatBai && lo && (
        <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-destructive">
          {lo.loi_nghiep_vu?.noi_dung ?? lo.loi?.noi_dung ?? "Không hoàn tác được — chưa có học viên nào được gỡ."}
        </div>
      )}
      {xong && lo && !thatBai && (
        <>
          <div className="rounded-lg border border-success/40 bg-success/10 p-3">
            Đã gỡ <b>{soVN(lo.da_go?.length ?? 0)}</b> học viên khỏi BC2 {maBc2}.
          </div>
          {dangDo && (
            <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-destructive">
              CHƯA hoàn tác xong{lo.loi ? ` — lỗi ở ${tenHv[lo.loi.ma_dk] ?? lo.loi.ma_dk}: ${lo.loi.noi_dung}` : ""}. Bấm "Làm tiếp"
              để gỡ nốt; học viên đã gỡ không bị gỡ lại.
            </div>
          )}
          {(lo.bo_qua?.length ?? 0) > 0 && (
            <ul className="text-warning space-y-0.5">
              {lo.bo_qua!.map((b) => <li key={b.ma_dk}><b>{tenHv[b.ma_dk] ?? b.ma_dk}</b> — {b.ly_do}</li>)}
            </ul>
          )}
        </>
      )}
    </Khung>
  );
}
