import { useRef, useState } from "react";
import FormBc2, { type GiaTriFormBc2 } from "./FormBc2";
import type { TrangThaiWizard } from "./WizardBc2";
import { soVN } from "../../lib/format";
import { hoanTacLoThem, lapBc2, LoiTnbc2, taoLoId, tienDoLo, type LoTn } from "../../lib/tnbc2Api";

// TNB-04 — bước ③: xác nhận "Lập BC2 và thêm N học viên" (tạo BC2 nếu chưa có rồi thêm HV; BC2 đã có thì chỉ thêm).
// Ghi nền theo `lo_id` (idempotent): mất kết nối / "Làm tiếp" gửi lại CÙNG `lo_id` ⇒ HV đã thêm không bị ghi lại.

const cho = (ms: number) => new Promise((r) => setTimeout(r, ms));
const TU_BAO_TIEN_DO = 200;   // từ 200 HV trở lên mới hiện thanh tiến độ (TDD §11F.8)

const LY_DO: Record<string, string> = {
  doi_giua_chung: "Phần mềm cũ vừa đổi học viên này — không ghi đè",
  khong_con_o_bc2: "Học viên không còn ở BC2 này hoặc đã có kết quả — không gỡ",
};

export default function BuocXacNhan({
  tt,
  onQuayLai,
  onXong,
}: {
  tt: TrangThaiWizard;
  onQuayLai: () => void;
  onXong: () => void;
}) {
  const loId = useRef(taoLoId());
  // Nội dung ĐÃ XÁC NHẬN ở lần gửi đầu: "Làm tiếp" luôn gửi lại đúng nội dung này (form có thể mount lại và đổi số gợi ý).
  const daXacNhan = useRef<{ so_bao_cao: string; ngay_bao_cao: string; ghi_chu: string } | null>(null);
  const coBc2 = tt.maBc2 !== "";
  const [form, setForm] = useState<GiaTriFormBc2 | null>(null);
  const [hop, setHop] = useState(false);
  const [daXemCanhBao, setDaXemCanhBao] = useState(false);
  const [xacNhanThat, setXacNhanThat] = useState(false);
  const [dang, setDang] = useState<"" | "lap" | "hoan_tac">("");
  const [lo, setLo] = useState<LoTn | null>(null);
  const [loHoanTac, setLoHoanTac] = useState<LoTn | null>(null);
  const [loi, setLoi] = useState<string | null>(null);
  const [matKetNoi, setMatKetNoi] = useState(false);
  const [canhBaoServer, setCanhBaoServer] = useState("");

  const ten = (ma: string) => tt.tenHv[ma] || ma;
  const n = tt.dsMaDk.length;
  const canhBao = form?.canh_bao || canhBaoServer;
  const duocLap = n > 0 && (coBc2 || !!form?.hop_le);

  async function theoDoi(id: string, dat: (t: LoTn) => void): Promise<LoTn> {
    let t = await tienDoLo(id);
    dat(t);
    let loiMang = 0;
    while (!t.xong) {
      await cho(800);
      try {
        t = await tienDoLo(id);
        if (t.bi_gian_doan) throw new Error("bi_gian_doan");
        dat(t);
        loiMang = 0;
      } catch (e) {
        if (e instanceof Error && e.message === "bi_gian_doan") throw e;
        if (++loiMang >= 5) throw e;
      }
    }
    return t;
  }

  async function lap() {
    setLoi(null);
    setMatKetNoi(false);
    setDang("lap");
    let dangTheoDoi = false;   // đã gửi lệnh ghi: từ đây mọi lỗi đều là "chưa biết ghi tới đâu" → Làm tiếp
    try {
      daXacNhan.current ??= {
        so_bao_cao: form?.so_bao_cao ?? "",
        ngay_bao_cao: form?.ngay_bao_cao ?? "",
        ghi_chu: form?.ghi_chu ?? "",
      };
      const t0 = await lapBc2({
        lo_id: loId.current,
        ma_kh: tt.maKh,
        ma_bc2: tt.maBc2,
        ...daXacNhan.current,
        ds_ma_dk: tt.dsMaDk,
        da_xem_canh_bao: daXemCanhBao,
      });
      setLo(t0);
      setHop(false);
      dangTheoDoi = true;
      const t = t0.xong ? t0 : await theoDoi(loId.current, setLo);
      setLo(t);
    } catch (e) {
      if (e instanceof LoiTnbc2 && !dangTheoDoi) {
        setLoi(e.message);
        if (e.ma === "can_xac_nhan_canh_bao") {
          const cb = (e.duLieu.canh_bao as { noi_dung: string }[] | undefined)?.[0]?.noi_dung ?? e.message;
          setCanhBaoServer(cb);
        }
      } else {
        setHop(false);
        setMatKetNoi(true);
        setLoi(
          e instanceof Error && e.message === "bi_gian_doan"
            ? "Tool bị tắt giữa chừng khi đang ghi — bấm \"Làm tiếp\"; học viên đã thêm không bị ghi lại."
            : "Mất kết nối khi ghi — bấm \"Làm tiếp\" để kiểm tra và ghi nốt phần còn lại.",
        );
      }
    } finally {
      setDang("");
    }
  }

  async function hoanTac() {
    if (!lo) return;
    setLoi(null);
    setDang("hoan_tac");
    const id = taoLoId();
    try {
      const t0 = await hoanTacLoThem(lo.ma_bc2 ?? "", id);
      setLoHoanTac(t0);
      const t = t0.xong ? t0 : await theoDoi(id, setLoHoanTac);
      setLoHoanTac(t);
    } catch (e) {
      setLoi(e instanceof Error ? e.message : "Không hoàn tác được");
    } finally {
      setDang("");
    }
  }

  const xong = !!lo?.xong && dang === "";
  const maBc2Kq = lo?.ma_bc2 ?? "";
  const soDaThem = (lo?.da_them?.length ?? 0) + (lo?.da_co_tu_truoc?.length ?? 0);
  const conDo = xong && (lo?.trang_thai === "loi_giua_chung" || (lo?.chua_ghi?.length ?? 0) > 0);
  const thatBai = xong && lo?.trang_thai === "that_bai";
  const daHoanTac = (loHoanTac?.da_go?.length ?? 0) > 0 || loHoanTac?.trang_thai === "xong";

  return (
    <div className="flex-1 min-h-0 flex flex-col">
      <div className="flex-1 min-h-0 overflow-auto p-4">
        <div className="max-w-[760px] mx-auto space-y-4">
          <div className="text-[15px] font-semibold">
            {xong ? "Kết quả" : coBc2 ? "Xác nhận thêm học viên vào BC2" : "Xác nhận lập BC2 và thêm học viên"}
          </div>

          {!lo && !dang && (
            <>
              {coBc2 ? (
                <div className="rounded-xl border border-border bg-card p-4 text-[13px]">
                  Thêm vào BC2 số <b className="font-mono">{tt.maBc2}</b> (đang mở) · khóa <b>{tt.tenKh}</b>
                </div>
              ) : (
                <FormBc2 maKh={tt.maKh} tenKh={tt.tenKh} onChange={setForm} />
              )}
              <div className="rounded-xl border border-border bg-card p-4 grid grid-cols-3 gap-3 text-center">
                <div>
                  <div className="text-2xl font-bold tabular-nums text-tn">{soVN(n)}</div>
                  <div className="text-[12px] text-muted-foreground">học viên sẽ thêm</div>
                </div>
                <div>
                  <div className="text-2xl font-bold tabular-nums text-success">{soVN(tt.nSan)}</div>
                  <div className="text-[12px] text-muted-foreground">của khóa</div>
                </div>
                <div>
                  <div className="text-2xl font-bold tabular-nums text-primary">{soVN(tt.nThi)}</div>
                  <div className="text-[12px] text-muted-foreground">thi lại</div>
                </div>
              </div>
              <div className="rounded-lg bg-muted px-3 py-2 text-[12.5px] text-muted-foreground">
                Tool đọc lại từng học viên ngay trước khi ghi: ai phần mềm cũ vừa đổi thì được bỏ qua và nêu lý do, không
                ghi đè. Sau khi ghi có nút <b>Hoàn tác lần vừa rồi</b>.
              </div>
            </>
          )}

          {dang === "lap" && (
            <div className="rounded-xl border border-border bg-card p-4">
              {n >= TU_BAO_TIEN_DO ? (
                <>
                  <div className="mb-1 text-[13px]">Đang ghi {soVN(lo?.xu_ly ?? 0)}/{soVN(lo?.tong ?? n)} học viên…</div>
                  <div className="h-2 rounded bg-muted overflow-hidden">
                    <div className="h-full bg-tn transition-all"
                      style={{ width: `${lo?.tong ? Math.min(100, Math.round(((lo.xu_ly ?? 0) / lo.tong) * 100)) : 0}%` }} />
                  </div>
                </>
              ) : (
                <div className="text-[13px]">Đang ghi {soVN(n)} học viên…</div>
              )}
            </div>
          )}

          {loi && <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-[13px] text-destructive">{loi}</div>}

          {xong && lo && !thatBai && (
            <>
              <div className="rounded-xl border border-success/40 bg-success/10 p-4 text-[13px]">
                {lo.da_tao_bc2 && <>Đã tạo BC2 số <b className="font-mono">{maBc2Kq}</b>. </>}
                Đã thêm <b>{soVN(soDaThem)}</b> học viên vào BC2 số <b className="font-mono">{maBc2Kq}</b>
                {(lo.da_co_tu_truoc?.length ?? 0) > 0 && <> (trong đó {soVN(lo.da_co_tu_truoc!.length)} đã có từ lần trước)</>}.
              </div>
              {(lo.bo_qua?.length ?? 0) > 0 && (
                <div className="rounded-lg border border-warning/40 bg-warning/10 p-3 text-[13px]">
                  <div className="font-semibold text-warning mb-1">{soVN(lo.bo_qua!.length)} học viên bị bỏ qua</div>
                  <ul className="max-h-48 overflow-auto space-y-0.5">
                    {lo.bo_qua!.map((b) => (
                      <li key={b.ma_dk}><b>{ten(b.ma_dk)}</b> — {LY_DO[b.ma_ly_do] ?? b.ly_do}</li>
                    ))}
                  </ul>
                </div>
              )}
              {(lo.chua_ghi?.length ?? 0) > 0 && (
                <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-[13px] text-destructive">
                  <div className="font-semibold">
                    CHƯA ghi {soVN(lo.chua_ghi!.length)} học viên{lo.loi ? ` — lỗi ở ${ten(lo.loi.ma_dk)}: ${lo.loi.noi_dung}` : ""}
                  </div>
                  <div>Bấm "Làm tiếp" để ghi nốt; học viên đã thêm không bị ghi lại.</div>
                </div>
              )}
              {(lo.canh_bao?.length ?? 0) > 0 && (
                <ul className="text-[13px] text-warning space-y-0.5">
                  {lo.canh_bao!.map((c, i) => (
                    <li key={i}>{c.ma_dk ? <b>{ten(c.ma_dk)}: </b> : null}{c.noi_dung}</li>
                  ))}
                </ul>
              )}
            </>
          )}

          {thatBai && lo && (
            <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-[13px] text-destructive">
              {lo.loi_nghiep_vu?.noi_dung ?? lo.loi?.noi_dung ?? "Không lập được BC2 — chưa có học viên nào được thêm."}
            </div>
          )}

          {loHoanTac?.xong && (
            <div className="rounded-lg border border-border bg-card p-3 text-[13px]">
              <b>Hoàn tác:</b> đã gỡ {soVN(loHoanTac.da_go?.length ?? 0)} học viên khỏi BC2 {maBc2Kq}.
              {(loHoanTac.bo_qua?.length ?? 0) > 0 && (
                <ul className="mt-1 space-y-0.5 text-warning">
                  {loHoanTac.bo_qua!.map((b) => (
                    <li key={b.ma_dk}><b>{ten(b.ma_dk)}</b> — {LY_DO[b.ma_ly_do] ?? b.ly_do}</li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="shrink-0 h-14 bg-card border-t border-border px-4 flex items-center gap-3">
        {!xong && !lo && (
          <button type="button" disabled={dang !== ""} onClick={onQuayLai}
            className="h-9 px-4 rounded-lg border border-input text-[13px] font-semibold hover:bg-muted">
            ← Quay lại chọn học viên
          </button>
        )}
        {thatBai && (
          <button type="button" onClick={onQuayLai}
            className="h-9 px-4 rounded-lg border border-input text-[13px] font-semibold hover:bg-muted">
            ← Quay lại chọn học viên
          </button>
        )}
        {xong && (
          <button type="button" onClick={onXong}
            className="h-9 px-4 rounded-lg border border-input text-[13px] font-semibold hover:bg-muted">
            Xong
          </button>
        )}
        <div className="ml-auto flex gap-2">
          {xong && !thatBai && !conDo && soDaThem > 0 && !daHoanTac && (
            <button type="button" disabled={dang !== ""} onClick={hoanTac}
              className="h-9 px-4 rounded-lg border border-destructive/50 text-destructive text-[13px] font-semibold hover:bg-destructive/10">
              Hoàn tác lần vừa rồi
            </button>
          )}
          {(conDo || matKetNoi) && dang === "" && (
            <button type="button" onClick={lap}
              className="h-9 px-4 rounded-lg bg-tn text-white text-[13px] font-semibold">
              Làm tiếp
            </button>
          )}
          {!lo && !matKetNoi && (
            <button type="button" disabled={!duocLap || dang !== ""} onClick={() => setHop(true)}
              className="h-9 px-4 rounded-lg bg-tn text-white text-[13px] font-semibold disabled:opacity-45 disabled:cursor-not-allowed">
              {coBc2 ? `Thêm ${soVN(n)} học viên` : `Lập BC2 và thêm ${soVN(n)} học viên`}
            </button>
          )}
        </div>
      </div>

      {hop && (
        <div className="fixed inset-0 z-50 bg-black/40 grid place-items-center p-4">
          <div role="dialog" aria-modal="true" aria-label="Xác nhận ghi"
            className="bg-white rounded-xl shadow-2xl w-[560px] max-w-full flex flex-col">
            <div className="p-4 border-b border-border font-semibold">
              {coBc2 ? "Thêm học viên vào BC2" : "Lập BC2 và thêm học viên"}
            </div>
            <div className="p-4 space-y-2 text-[13px]">
              <div>
                {coBc2 ? <>Thêm <b>{soVN(n)}</b> học viên vào BC2 số <b className="font-mono">{tt.maBc2}</b>.</> : (
                  <>Tạo BC2 số <b className="font-mono">{form?.so_bao_cao}</b> (ngày {form?.ngay_bao_cao.split("-").reverse().join("/")})
                    rồi thêm <b>{soVN(n)}</b> học viên.</>
                )}
              </div>
              {canhBao && (
                <label className="flex items-start gap-2 rounded-lg border border-warning/40 bg-warning/10 p-3 text-warning">
                  <input type="checkbox" className="mt-1" checked={daXemCanhBao} onChange={(e) => setDaXemCanhBao(e.target.checked)} />
                  <span>{canhBao}. Tôi đã xem và vẫn muốn tiếp tục.</span>
                </label>
              )}
              <label className="inline-flex items-center gap-2">
                <input type="checkbox" checked={xacNhanThat} onChange={(e) => setXacNhanThat(e.target.checked)} />
                Tôi xác nhận đây là CSDL thật (DB Nạp) — ghi thẳng vào hồ sơ
              </label>
              {loi && <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-destructive">{loi}</div>}
            </div>
            <div className="p-3 border-t border-border flex justify-end gap-2">
              <button type="button" disabled={dang !== ""} onClick={() => setHop(false)}
                className="h-9 px-4 rounded-lg border border-input text-[13px] font-semibold hover:bg-muted">
                Quay lại
              </button>
              <button type="button" onClick={lap}
                disabled={dang !== "" || !xacNhanThat || (!!canhBao && !daXemCanhBao)}
                className="h-9 px-4 rounded-lg bg-tn text-white text-[13px] font-semibold disabled:opacity-45 disabled:cursor-not-allowed">
                {coBc2 ? "Thêm học viên" : "Lập BC2 và thêm"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
