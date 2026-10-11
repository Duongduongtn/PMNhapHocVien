import { useEffect, useState } from "react";
import { soVN } from "../../lib/format";
import { dsBc2, type Bc2Dong, type LoaiHang } from "../../lib/tnbc2Api";

// TNB-05/TNB-04 — danh sách BC2 gọn: lối vào "Xem" và "+ Thêm học viên". Task 115 sẽ bổ sung (đánh dấu lệch, nhật ký).

const dmy = (iso: string) => (iso ? iso.slice(0, 10).split("-").reverse().join("/") : "");

export default function DanhSachBc2({
  loai,
  onXem,
  onThem,
}: {
  loai: LoaiHang;
  onXem: (b: Bc2Dong) => void;
  onThem: (b: Bc2Dong) => void;
}) {
  const [dong, setDong] = useState<"mo" | "dong">("mo");
  const [ds, setDs] = useState<Bc2Dong[] | null>(null);
  const [loi, setLoi] = useState<string | null>(null);
  const [tai, setTai] = useState(0);

  useEffect(() => {
    let huy = false;
    setLoi(null);
    setDs(null);
    dsBc2(loai, dong)
      .then((d) => { if (!huy) setDs(d.bc2); })
      .catch((e: unknown) => { if (!huy) setLoi(e instanceof Error ? e.message : "Không tải được danh sách BC2"); });
    return () => { huy = true; };
  }, [loai, dong, tai]);

  return (
    <div className="mt-4">
      <div className="flex items-center gap-3">
        <div className="inline-flex rounded-lg border border-border overflow-hidden" role="group" aria-label="Lọc BC2">
          {([["mo", "Đang mở"], ["dong", "Đã đóng"]] as const).map(([v, t]) => (
            <button key={v} type="button" aria-pressed={dong === v} onClick={() => setDong(v)}
              className={`h-8 px-3 text-[12.5px] font-semibold ${dong === v ? "bg-tn-soft text-tn" : "bg-white hover:bg-muted"}`}>
              {t}
            </button>
          ))}
        </div>
        <button type="button" onClick={() => setTai((n) => n + 1)}
          className="h-8 px-3 rounded-lg text-[12.5px] font-semibold text-primary hover:bg-accent">
          Làm tươi
        </button>
      </div>

      {loi && <div className="mt-3 rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-[13px] text-destructive">{loi}</div>}
      {!ds && !loi && <div className="mt-3 text-[13px] text-muted-foreground">Đang tải…</div>}
      {ds && (
        <div className="mt-3 rounded-xl border border-border bg-card overflow-auto">
          <table className="w-full text-[13px]">
            <thead>
              <tr className="text-left text-[12px] text-muted-foreground border-b border-border">
                <th className="px-3 py-2 font-semibold">Số BC2</th>
                <th className="py-2 pr-3 font-semibold">Khóa</th>
                <th className="py-2 pr-3 font-semibold">Ngày báo cáo</th>
                <th className="py-2 pr-3 font-semibold text-right">Tổng ghi</th>
                <th className="py-2 pr-3 font-semibold text-right">HV thực tế</th>
                <th className="py-2 pr-3 font-semibold text-right"> </th>
              </tr>
            </thead>
            <tbody>
              {ds.length === 0 && (
                <tr><td colSpan={6} className="text-center text-muted-foreground py-8">
                  {dong === "mo" ? "Chưa có BC2 đang mở." : "Chưa có BC2 đã đóng."}
                </td></tr>
              )}
              {ds.map((b) => (
                <tr key={b.ma_bc2} className="border-b border-border last:border-b-0 hover:bg-tn-soft/40">
                  <td className="px-3 py-2 font-mono font-medium">{b.ma_bc2}</td>
                  <td className="py-2 pr-3">{b.ten_kh}</td>
                  <td className="py-2 pr-3 tabular-nums">{dmy(b.ngay_bao_cao)}</td>
                  <td className="py-2 pr-3 text-right tabular-nums">{b.tong_ghi ?? "—"}</td>
                  <td className="py-2 pr-3 text-right tabular-nums">{soVN(b.hv_thuc_te)}</td>
                  <td className="py-2 pr-3 text-right whitespace-nowrap">
                    <button type="button" onClick={() => onXem(b)} aria-label={`Xem BC2 ${b.ma_bc2}`}
                      className="h-8 px-3 rounded-lg border border-input text-[12.5px] font-semibold hover:bg-muted">
                      Xem
                    </button>
                    {b.dang_mo && (
                      <button type="button" onClick={() => onThem(b)} aria-label={`Thêm học viên vào BC2 ${b.ma_bc2}`}
                        className="ml-2 h-8 px-3 rounded-lg bg-tn text-white text-[12.5px] font-semibold">
                        + Thêm học viên
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
