import { useCallback, useEffect, useState } from "react";
import { Icon } from "../../components/Icon";
import { kiemTruocKQD, type KiemTruocKQD, type KhoaKQD } from "../../lib/api";
import { soVN } from "../../lib/format";
import { hienThiKiemTruoc, LY_DO_NHAN, LY_DO_THU_TU, MON_NHAN, nhanCanhBao } from "./kiemTruoc";

// KQD-07 (task 120) — khung "Kiểm trước kết xuất", CHỈ ĐỌC, đúng 1 khóa. Bám ui-mock/ketqua.html (drawer phải).
// Kiểm tra này chỉ nhắc, không chặn: kết xuất do phần mềm CDB cũ làm.

const TT_NHAN: Record<string, [string, string]> = {
  "03": ["Đã đăng ký", "text-muted-foreground bg-muted border-border"],
  "04": ["Đã đăng ký", "text-muted-foreground bg-muted border-border"],
  "09": ["Đã cập nhật · Đạt", "text-success bg-success/10 border-success/40"],
  "10": ["Đã cập nhật · Không đạt", "text-destructive bg-destructive/10 border-destructive/40"],
};
const CHIP_MAU: Record<string, string> = {
  chua_co_diem: "text-muted-foreground bg-muted border-border",
  thieu_mon: "text-destructive bg-destructive/5 border-destructive/40",
  thieu_gio_km: "text-destructive bg-destructive/5 border-destructive/40",
  thieu_ket_luan: "text-destructive bg-destructive/5 border-destructive/40",
};

function Hop({ icon, tieuDe, phu, mau = "border-border bg-muted/40" }: { icon: string; tieuDe: string; phu?: string; mau?: string }) {
  return (
    <div className={"m-4 rounded-lg border px-4 py-6 text-center " + mau}>
      <Icon name={icon} className="w-6 h-6 mx-auto mb-1" />
      <div className="text-[14px] font-semibold">{tieuDe}</div>
      {phu && <div className="text-[12.5px] text-muted-foreground mt-1">{phu}</div>}
    </div>
  );
}

export default function KiemTruocKetXuat({
  khoa, targetKey, onDong, onMoHV,
}: {
  khoa: KhoaKQD;
  targetKey: string | null;
  onDong: () => void;
  onMoHV: (soCccd: string) => void;
}) {
  const [kq, setKq] = useState<KiemTruocKQD | null>(null);
  const [loi, setLoi] = useState("");
  const [dang, setDang] = useState(true);
  const [loc, setLoc] = useState<string | null>(null);

  const tai = useCallback(() => {
    setDang(true); setLoi(""); setLoc(null);
    kiemTruocKQD(khoa.ma_kh, targetKey ?? undefined)
      .then((r) => setKq(hienThiKiemTruoc(r)))
      .catch((e) => { setKq(null); setLoi(e instanceof Error ? e.message : "Không kiểm tra được."); })
      .finally(() => setDang(false));
  }, [khoa.ma_kh, targetKey]);
  useEffect(() => { tai(); }, [tai]);

  let noiDung;
  if (dang) {
    noiDung = <div className="px-4 py-10 text-center text-[13px] text-muted-foreground">Đang kiểm tra…</div>;
  } else if (loi || !kq) {
    noiDung = <Hop icon="warn" mau="border-destructive/40 bg-destructive/5 text-destructive" tieuDe="Không kết nối được DB đích"
      phu={(loi || "Kiểm tra máy CSDL đích") + " — bấm “Kiểm lại”. Việc nhập điểm không bị ảnh hưởng."} />;
  } else if (kq.tong === 0 && kq.mo_to_bo_qua > 0) {
    noiDung = <Hop icon="info" tieuDe="Khóa mô tô — không xét kết quả đào tạo"
      phu={`${soVN(kq.mo_to_bo_qua)} học viên hạng mô tô không nhập kết quả ở tool này nên không kiểm.`} />;
  } else if (kq.tong === 0) {
    noiDung = <Hop icon="file" tieuDe="Khóa chưa có học viên" phu="Chưa có học viên nào đang chờ kết xuất ở khóa này." />;
  } else if (kq.thieu.length === 0) {
    noiDung = <Hop icon="check" mau="border-success/40 bg-success/5 text-success" tieuDe="Khóa đủ điều kiện kết xuất"
      phu={`${soVN(kq.du)}/${soVN(kq.tong)} học viên đủ điểm, giờ/km và kết luận. Sang phần mềm CDB cũ để kết xuất.`} />;
  } else {
    const ds = kq.thieu.filter((t) => !loc || t.ly_do.includes(loc));
    noiDung = (
      <>
        <div className="px-4 py-3 border-b border-border">
          <div className="flex items-baseline gap-4">
            <span className="text-success font-bold text-[15px] tabular-nums">{soVN(kq.du)} <span className="text-[12.5px] font-medium">học viên đủ điều kiện</span></span>
            <span className="text-destructive font-bold text-[15px] tabular-nums">{soVN(kq.thieu.length)} <span className="text-[12.5px] font-medium">học viên còn thiếu</span></span>
            {kq.mo_to_bo_qua > 0 && <span className="ml-auto text-[11.5px] text-muted-foreground">{soVN(kq.mo_to_bo_qua)} HV mô tô không xét</span>}
          </div>
          <div className="flex flex-wrap gap-1.5 mt-2.5">
            {LY_DO_THU_TU.filter((k) => (kq.dem[k] ?? 0) > 0).map((k) => (
              <button key={k} onClick={() => setLoc(loc === k ? null : k)}
                className={"text-[11px] font-semibold border rounded-full px-2 py-px " + CHIP_MAU[k] + (loc === k ? " ring-2 ring-kq/50" : "")}>
                {LY_DO_NHAN[k]} · <span className="tabular-nums">{soVN(kq.dem[k] ?? 0)}</span>
              </button>
            ))}
            {loc && <button onClick={() => setLoc(null)} className="text-[11.5px] text-muted-foreground underline ml-1">bỏ lọc</button>}
          </div>
        </div>
        {ds.map((t) => {
          const [nhan, mau] = TT_NHAN[t.tt_xuly ?? ""] ?? [t.tt_xuly ?? "—", "text-muted-foreground bg-muted border-border"];
          return (
            <button key={t.ma_dk} onClick={() => onMoHV(t.so_cccd)}
              className="w-full text-left px-4 py-2.5 border-b border-border/70 hover:bg-kq-soft/40 flex items-start gap-3">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-[13px]">{t.ho_ten}</span>
                  <span className="font-mono text-[12px] text-muted-foreground">{t.so_cccd}</span>
                </div>
                <div className="flex flex-wrap gap-1.5 mt-1.5">
                  {t.ly_do.map((k) => (
                    <span key={k} className={"text-[11px] font-semibold border rounded-full px-2 py-px " + CHIP_MAU[k]}>
                      {LY_DO_NHAN[k]}{k === "thieu_mon" && t.mon_thieu.length > 0 ? ": " + t.mon_thieu.map((m) => MON_NHAN[m] ?? m).join(", ") : ""}
                    </span>
                  ))}
                  {t.canh_bao.map((w) => (
                    <span key={w.loai} title="Chỉ cảnh báo, không tính là thiếu"
                      className="text-[11px] font-semibold border rounded-full px-2 py-px text-warning bg-warning/10 border-warning/40">⚠ {nhanCanhBao(w)}</span>
                  ))}
                </div>
              </div>
              <span className={"text-[11px] font-semibold border rounded-full px-2 py-0.5 whitespace-nowrap mt-0.5 " + mau}>{nhan}</span>
              <Icon name="chevronRight" className="w-4 h-4 text-muted-foreground mt-1 shrink-0" />
            </button>
          );
        })}
        <div className="px-4 py-2 text-[11.5px] text-muted-foreground">Bấm một dòng để mở đúng học viên ở lưới nhập điểm. ⚠ vàng = dưới mức gợi ý tối thiểu, chỉ nhắc.</div>
      </>
    );
  }

  return (
    <div className="fixed inset-0 z-50">
      <div className="absolute inset-0 bg-black/30" onClick={onDong} />
      <div className="absolute right-0 top-0 h-full w-[540px] max-w-full bg-card shadow-2xl flex flex-col" role="dialog" aria-label="Kiểm trước kết xuất">
        <div className="shrink-0 px-4 py-3 border-b border-border flex items-start gap-3">
          <div>
            <div className="font-bold text-[15px] flex items-center gap-2">Kiểm trước kết xuất
              <span className="text-[10px] font-semibold text-kq bg-kq-soft border border-kq-border rounded-full px-1.5 py-px">KQD-07</span>
            </div>
            <div className="text-[12px] text-muted-foreground">Khóa <b className="text-foreground">{khoa.ten_kh}</b> · hạng {khoa.hang_gplx} · chỉ học viên chưa kết xuất</div>
          </div>
          <button onClick={tai} disabled={dang} className="ml-auto inline-flex items-center gap-1.5 h-8 px-3 rounded-lg border border-border text-[12.5px] whitespace-nowrap hover:bg-muted disabled:opacity-50">
            <Icon name="refresh" className="w-3.5 h-3.5" /> Kiểm lại
          </button>
          <button onClick={onDong} className="text-muted-foreground hover:text-foreground mt-1" aria-label="Đóng"><Icon name="x" className="w-5 h-5" /></button>
        </div>
        <div className="flex-1 overflow-auto">{noiDung}</div>
        <div className="shrink-0 px-4 py-2.5 border-t border-border bg-muted/30 text-[12px] text-muted-foreground flex items-start gap-2">
          <Icon name="info" className="w-4 h-4 shrink-0 mt-px" />
          <span><b>Kiểm tra này chỉ nhắc, không chặn.</b> Kết xuất do phần mềm CDB cũ làm.</span>
        </div>
      </div>
    </div>
  );
}
