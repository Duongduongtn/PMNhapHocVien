import { useCallback, useEffect, useState } from "react";
import { soVN } from "../../lib/format";
import { dsNhatKy, type DongNhatKy } from "../../lib/tnbc2Api";

// TNB-07 (2/2) — tab Nhật ký: ai · lúc nào · loại · số HV · kết quả đã/chưa ghi. Chỉ đọc; nhật ký lưu trên máy này
// và KHÔNG chứa họ tên/CMT học viên. Bám ui-mock/tnbc2.html `viewNhatKy`.

const LOAI: [string, string][] = [
  ["", "Tất cả"],
  ["tot_nghiep", "Cập nhật tốt nghiệp"],
  ["huy_tot_nghiep", "Hủy tốt nghiệp"],
  ["tao_bc2", "Tạo BC2"],
  ["them_hv", "Thêm học viên vào BC2"],
  ["go_hv", "Gỡ học viên khỏi BC2"],
  ["xoa_bc2", "Xóa BC2"],
  ["cuu_trang_thai", "Cứu trạng thái"],
];

/** `2026-10-11T10:08:05` → `11/10/2026 10:08` */
function gio(luc: string): string {
  const m = /^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})/.exec(luc);
  return m ? `${m[3]}/${m[2]}/${m[1]} ${m[4]}:${m[5]}` : luc;
}

function Nhan({ d }: { d: DongNhatKy }) {
  const lop =
    d.trang_thai === "xong" || d.trang_thai === "da_ton_tai"
      ? "text-success bg-success/10 border-success/40"
      : d.trang_thai === "loi_giua_chung"
        ? "text-warning bg-warning/10 border-warning/40"
        : "text-destructive bg-destructive/10 border-destructive/40";
  return <span className={`inline-block text-[11px] font-semibold px-2 rounded-full border whitespace-nowrap ${lop}`}>{d.ten_trang_thai}</span>;
}

export default function NhatKy() {
  const [loai, setLoai] = useState("");
  const [maBc2, setMaBc2] = useState("");
  const [ds, setDs] = useState<DongNhatKy[] | null>(null);
  const [loi, setLoi] = useState<string | null>(null);
  const [tai, setTai] = useState(0);

  useEffect(() => {
    let huy = false;
    const t = setTimeout(() => {
      setLoi(null);
      dsNhatKy(loai, maBc2.trim(), 200)
        .then((d) => { if (!huy) setDs(d.nhat_ky); })
        .catch((e: unknown) => { if (!huy) { setDs(null); setLoi(e instanceof Error ? e.message : "Không tải được nhật ký"); } });
    }, maBc2 ? 300 : 0);
    return () => { huy = true; clearTimeout(t); };
  }, [loai, maBc2, tai]);

  const lamTuoi = useCallback(() => setTai((n) => n + 1), []);

  return (
    <div className="h-full flex flex-col min-h-0">
      <div className="shrink-0 bg-card border-b border-border px-4 py-2.5 flex flex-wrap items-end gap-3">
        <div>
          <label className="field-label" htmlFor="nk-loai">Loại thao tác</label>
          <select id="nk-loai" className="field-input" value={loai} onChange={(e) => setLoai(e.target.value)}>
            {LOAI.map(([v, t]) => <option key={v} value={v}>{t}</option>)}
          </select>
        </div>
        <div className="w-[220px]">
          <label className="field-label" htmlFor="nk-bc2">Số BC2 (tùy chọn)</label>
          <input id="nk-bc2" className="field-input font-mono" value={maBc2} maxLength={13} placeholder="vd: 81/2026"
            onChange={(e) => setMaBc2(e.target.value)} />
        </div>
        <button type="button" onClick={lamTuoi}
          className="h-9 px-3 rounded-lg text-[13px] font-semibold text-primary hover:bg-accent">
          Làm tươi
        </button>
        {ds && <div className="ml-auto text-[12px] text-muted-foreground">{soVN(ds.length)} thao tác gần nhất</div>}
      </div>

      {loi && <div className="shrink-0 px-4 py-2 text-[13px] bg-destructive/10 text-destructive border-b border-destructive/30">{loi}</div>}

      <div className="flex-1 min-h-0 overflow-auto">
        {!ds && !loi && <div className="p-4 text-[13px] text-muted-foreground">Đang tải…</div>}
        {ds && (
          <table className="w-full text-[13px]">
            <thead className="sticky top-0 bg-card border-b border-border z-10">
              <tr className="text-left text-[12px] text-muted-foreground">
                <th className="px-3 py-2 font-semibold">Thời gian</th>
                <th className="py-2 pr-3 font-semibold">Người thao tác</th>
                <th className="py-2 pr-3 font-semibold">Việc</th>
                <th className="py-2 pr-3 font-semibold">Chi tiết</th>
                <th className="py-2 pr-3 font-semibold text-right">Số HV</th>
                <th className="py-2 pr-3 font-semibold">Kết quả</th>
              </tr>
            </thead>
            <tbody>
              {ds.length === 0 && (
                <tr><td colSpan={6} className="text-center text-muted-foreground py-10">Chưa có thao tác nào được ghi.</td></tr>
              )}
              {ds.map((d) => (
                <tr key={d.id} className="border-b border-border">
                  <td className="px-3 py-2 tabular-nums whitespace-nowrap">{gio(d.luc)}</td>
                  <td className="py-2 pr-3 whitespace-nowrap">{d.nguoi || "—"}</td>
                  <td className="py-2 pr-3 font-medium whitespace-nowrap">{d.ten_loai}</td>
                  <td className="py-2 pr-3">
                    {d.tom_tat_thao_tac}
                    {d.ma_bc2 && <span className="ml-1 font-mono text-[12px] text-muted-foreground">BC2 {d.ma_bc2}</span>}
                  </td>
                  <td className="py-2 pr-3 text-right tabular-nums">{soVN(d.so_hv)}</td>
                  <td className="py-2 pr-3">
                    <Nhan d={d} />
                    {d.ket_qua.tom_tat && <div className="text-[11.5px] text-muted-foreground mt-0.5">{d.ket_qua.tom_tat}</div>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <div className="m-4 rounded-lg bg-muted px-3 py-2 text-[12.5px] text-muted-foreground">
          Nhật ký lưu trên máy này để truy vết ai đã làm gì; không chứa họ tên hay số CMT của học viên. Phần mềm cũ không
          ghi lại người thao tác cho các việc này.
        </div>
      </div>
    </div>
  );
}
