import { useEffect, useMemo, useRef, useState } from "react";
import {
  ghiTotNghiep,
  LoiTnbc2,
  taoLoId,
  tienDoLo,
  xemLaiTotNghiep,
  type ChungTn,
  type DongTn,
  type LoTn,
  type XemLaiTnResp,
} from "../../lib/tnbc2Api";
import { soVN } from "../../lib/format";

// TNB-01 — hộp "Xem lại & ghi": chạy thử (không ghi) → xác nhận CSDL thật → ghi nền theo lô → kết quả đã/chưa ghi.
// Cùng `lo_id` cho mọi lần gửi trong một lượt mở hộp: gửi lại (mất mạng, "Làm tiếp") không ghi đôi.

const NHAN_KET_QUA: Record<string, string> = {
  se_len_09: "sẽ chuyển sang \"Đã tốt nghiệp, chờ lập BC2\"",
  luu_so_truoc: "chỉ lưu sổ/quyết định, chưa cấp giấy (vẫn \"Đã học xong\")",
  giu_09_sua_thong_tin: "sửa thông tin, giữ nguyên \"Đã tốt nghiệp\"",
  khong_doi_trang_thai_da_vao_bc2: "ghi số giấy, không đổi trạng thái (đã vào BC2)",
  khong_doi: "không đổi (nhập y hệt hiện trạng)",
  bo_qua: "bỏ qua",
  chan: "bị chặn",
};

const LY_DO_GHI: Record<string, string> = {
  doi_giua_chung: "Phần mềm cũ vừa đổi học viên này — không ghi đè",
  trung_db: "Số giấy vừa được dùng cho học viên khác",
};

const cho = (ms: number) => new Promise((r) => setTimeout(r, ms));

interface Props {
  maKh: string;
  dong: DongTn[];
  chung: ChungTn;
  /** mã đăng ký → họ tên, để hiện tên người đọc được thay vì mã. */
  tenHv: Record<string, string>;
  onDong: () => void;
  /** Gọi khi đã có kết quả ghi (hoặc lỗi giữa chừng) và người dùng đóng hộp — để làm tươi danh sách. */
  onXong: () => void;
}

export default function HopGhiTotNghiep({ maKh, dong, chung, tenHv, onDong, onXong }: Props) {
  const loId = useRef(taoLoId());
  const [xem, setXem] = useState<XemLaiTnResp | null>(null);
  const [loiXem, setLoiXem] = useState<string | null>(null);
  const [daXemCanhBao, setDaXemCanhBao] = useState(false);
  const [xacNhanThat, setXacNhanThat] = useState(false);
  const [dangGhi, setDangGhi] = useState(false);
  const [lo, setLo] = useState<LoTn | null>(null);
  const [loiGhi, setLoiGhi] = useState<string | null>(null);
  const [matKetNoi, setMatKetNoi] = useState(false);
  const daGhi = useRef(false);

  useEffect(() => {
    let huy = false;
    xemLaiTotNghiep(maKh, dong, chung)
      .then((r) => { if (!huy) setXem(r); })
      .catch((e: unknown) => { if (!huy) setLoiXem(e instanceof Error ? e.message : "Không xem lại được"); });
    return () => { huy = true; };
  }, [maKh, dong, chung]);

  const ten = (ma: string) => tenHv[ma] || ma;
  const soGhiDuoc = useMemo(() => (xem ? xem.dong.filter((d) => d.ghi_duoc).length : 0), [xem]);
  const dongKhongGhi = useMemo(() => (xem ? xem.dong.filter((d) => !d.ghi_duoc) : []), [xem]);
  const canXacNhanCanhBao = !!xem && xem.canh_bao.length > 0;

  async function ghi() {
    setLoiGhi(null);
    setMatKetNoi(false);
    setLo(null);
    setDangGhi(true);
    daGhi.current = true;
    try {
      let t = await ghiTotNghiep(loId.current, maKh, dong, chung, daXemCanhBao);
      setLo(t);
      let loiMang = 0;
      while (!t.xong) {
        await cho(800);
        try {
          t = await tienDoLo(loId.current);
          if (t.bi_gian_doan) {   // tool đã tắt giữa chừng: lô không còn chạy — "Làm tiếp" bằng cùng lo_id
            setLo(null);
            setMatKetNoi(true);
            setLoiGhi(`Tool bị tắt giữa chừng khi đang ghi (đã ghi ${t.da_ghi?.length ?? 0}/${t.tong} học viên) — bấm "Làm tiếp" để ghi nốt, học viên đã ghi không bị ghi lại.`);
            return;
          }
          setLo(t);
          loiMang = 0;
        } catch (e) {
          // mất kết nối thoáng qua: thử lại vài lần rồi báo (lô vẫn chạy nền, "Làm tiếp" an toàn)
          if (++loiMang >= 5) throw e;
        }
      }
    } catch (e) {
      if (e instanceof LoiTnbc2) setLoiGhi(e.message);
      else {
        setMatKetNoi(true);
        setLoiGhi("Mất kết nối khi ghi — bấm \"Làm tiếp\" để kiểm tra và ghi nốt phần còn lại.");
      }
    } finally {
      setDangGhi(false);
    }
  }

  const xong = !!lo?.xong && !dangGhi;
  const conDo = xong && (lo?.trang_thai === "loi_giua_chung" || (lo?.chua_ghi?.length ?? 0) > 0);
  const dong_ = () => (daGhi.current ? onXong() : onDong());

  return (
    <div className="fixed inset-0 z-50 bg-black/40 grid place-items-center p-4">
      <div role="dialog" aria-modal="true" aria-label="Xem lại và ghi tốt nghiệp"
        className="bg-white rounded-xl shadow-2xl w-[760px] max-w-full max-h-[90vh] flex flex-col">
        <div className="p-4 border-b border-border font-semibold">
          {lo ? "Kết quả ghi tốt nghiệp" : `Xem lại trước khi ghi ${soVN(dong.length)} học viên`}
        </div>

        <div className="p-4 overflow-auto space-y-3 text-[13px]">
          {loiXem && <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-destructive">{loiXem}</div>}
          {!xem && !loiXem && <div className="text-muted-foreground">Đang kiểm tra…</div>}

          {xem && !lo && !dangGhi && (
            <>
              <ul className="space-y-1">
                {Object.entries(xem.dem).map(([k, n]) => (
                  <li key={k} className="flex gap-2">
                    <span className="font-semibold tabular-nums w-14 text-right">{soVN(n)}</span>
                    <span>học viên {NHAN_KET_QUA[k] ?? k}</span>
                  </li>
                ))}
              </ul>
              {xem.khoang_so && (
                <div className="rounded-lg bg-muted px-3 py-2">
                  Số giấy từ <b className="font-mono">{xem.khoang_so.tien_to}{xem.khoang_so.tu}</b> đến{" "}
                  <b className="font-mono">{xem.khoang_so.tien_to}{xem.khoang_so.den}</b> ({soVN(xem.khoang_so.so_luong)} số)
                </div>
              )}
              {xem.canh_bao.length > 0 && (
                <div className="rounded-lg border border-warning/40 bg-warning/10 p-3 space-y-1">
                  <div className="font-semibold text-warning">Cảnh báo</div>
                  {xem.canh_bao.map((c) => (
                    <div key={c.ma}>
                      {c.noi_dung} <span className="text-muted-foreground">({soVN(c.so_dong)} học viên)</span>
                    </div>
                  ))}
                </div>
              )}
              {dongKhongGhi.length > 0 && (
                <div className="rounded-lg border border-destructive/30 p-3">
                  <div className="font-semibold text-destructive mb-1">
                    {soVN(dongKhongGhi.length)} học viên sẽ KHÔNG được ghi
                  </div>
                  <ul className="max-h-40 overflow-auto space-y-0.5">
                    {dongKhongGhi.map((d) => (
                      <li key={d.ma_dk}>
                        <b>{ten(d.ma_dk)}</b> — {(d.chan[0] ?? d.thong_tin[0])?.noi_dung ?? NHAN_KET_QUA[d.ket_qua] ?? d.ket_qua}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {soGhiDuoc === 0 && <div className="text-destructive font-medium">Không có học viên nào ghi được — sửa lại danh sách.</div>}
            </>
          )}

          {dangGhi && lo && !lo.xong && (
            <div>
              <div className="mb-1">Đang ghi {soVN(lo.xu_ly ?? 0)}/{soVN(lo.tong)} học viên…</div>
              <div className="h-2 rounded bg-muted overflow-hidden">
                <div className="h-full bg-tn transition-all"
                  style={{ width: `${lo.tong ? Math.min(100, Math.round(((lo.xu_ly ?? 0) / lo.tong) * 100)) : 0}%` }} />
              </div>
            </div>
          )}
          {dangGhi && !lo && <div className="text-muted-foreground">Đang gửi…</div>}

          {loiGhi && <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-destructive">{loiGhi}</div>}

          {xong && lo && (
            <>
              <div className="rounded-lg border border-success/40 bg-success/10 p-3">
                Đã ghi <b>{soVN((lo.da_ghi?.length ?? 0) + (lo.da_ghi_truoc?.length ?? 0))}</b> học viên
                {(lo.da_ghi_truoc?.length ?? 0) > 0 && <> (trong đó {soVN(lo.da_ghi_truoc!.length)} đã ghi từ lần trước)</>}.
              </div>
              {lo.dem && Object.keys(lo.dem).length > 0 && (
                <ul className="space-y-0.5">
                  {Object.entries(lo.dem).map(([k, n]) => (
                    <li key={k}><b className="tabular-nums">{soVN(n)}</b> học viên {NHAN_KET_QUA[k] ?? k}</li>
                  ))}
                </ul>
              )}
              {(lo.bo_qua?.length ?? 0) > 0 && (
                <div className="rounded-lg border border-warning/40 bg-warning/10 p-3">
                  <div className="font-semibold text-warning mb-1">{soVN(lo.bo_qua!.length)} học viên bị bỏ qua</div>
                  <ul className="max-h-40 overflow-auto space-y-0.5">
                    {lo.bo_qua!.map((b) => (
                      <li key={b.ma_dk}><b>{ten(b.ma_dk)}</b> — {LY_DO_GHI[b.ma_ly_do] ?? b.ly_do}</li>
                    ))}
                  </ul>
                </div>
              )}
              {(lo.chua_ghi?.length ?? 0) > 0 && (
                <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-destructive">
                  <div className="font-semibold">
                    CHƯA ghi {soVN(lo.chua_ghi!.length)} học viên{lo.loi ? ` — lỗi ở ${ten(lo.loi.ma_dk)}: ${lo.loi.noi_dung}` : ""}
                  </div>
                  <div>Bấm "Làm tiếp" để ghi nốt; học viên đã ghi không bị ghi lại.</div>
                </div>
              )}
              {(lo.canh_bao?.length ?? 0) > 0 && (
                <ul className="text-warning space-y-0.5">
                  {lo.canh_bao!.map((c, i) => (
                    <li key={i}>{c.ma_dk ? <b>{ten(c.ma_dk)}: </b> : null}{c.noi_dung}</li>
                  ))}
                </ul>
              )}
              {lo.loi_nghiep_vu && <div className="text-destructive">{lo.loi_nghiep_vu.noi_dung}</div>}
            </>
          )}
        </div>

        <div className="p-3 border-t border-border flex items-center gap-3">
          {xem && !lo && !dangGhi && (
            <div className="flex flex-col gap-1 text-[13px]">
              {canXacNhanCanhBao && (
                <label className="inline-flex items-center gap-2">
                  <input type="checkbox" checked={daXemCanhBao} onChange={(e) => setDaXemCanhBao(e.target.checked)} />
                  Tôi đã xem các cảnh báo trên
                </label>
              )}
              <label className="inline-flex items-center gap-2">
                <input type="checkbox" checked={xacNhanThat} onChange={(e) => setXacNhanThat(e.target.checked)} />
                Tôi xác nhận đây là CSDL thật (DB Nạp) — ghi thẳng vào hồ sơ
              </label>
            </div>
          )}
          <div className="ml-auto flex gap-2">
            {!dangGhi && (
              <button type="button" onClick={dong_}
                className="h-9 px-4 rounded-lg border border-input text-[13px] font-semibold hover:bg-muted">
                {xong || loiGhi ? "Đóng" : "Quay lại"}
              </button>
            )}
            {xem && !lo && !dangGhi && !matKetNoi && (
              <button type="button" onClick={ghi}
                disabled={soGhiDuoc === 0 || !xacNhanThat || (canXacNhanCanhBao && !daXemCanhBao)}
                className="h-9 px-4 rounded-lg bg-tn text-white text-[13px] font-semibold disabled:opacity-45 disabled:cursor-not-allowed">
                Ghi {soVN(soGhiDuoc)} học viên
              </button>
            )}
            {(conDo || matKetNoi) && !dangGhi && (
              <button type="button" onClick={ghi}
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
