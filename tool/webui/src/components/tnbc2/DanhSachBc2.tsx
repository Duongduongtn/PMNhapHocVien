import { useEffect, useMemo, useState } from "react";
import { soVN } from "../../lib/format";
import { dsBc2, type Bc2Dong, type DsBc2Resp, type LoaiHang } from "../../lib/tnbc2Api";
import TrangThaiBc2 from "./TrangThaiBc2";

// TNB-07 (+ lối vào TNB-04/05) — bảng BC2 theo loại hạng, lọc đang mở / đã có kết quả hoặc đã đóng: số báo cáo · ngày · BC1 · khóa ·
// Tổng ghi · HV thực tế (đánh dấu lệch) · trạng thái · người tạo. Bấm một dòng → chi tiết. Chỉ đọc: không sửa/xóa ở đây.

const dmy = (iso: string) => (iso ? iso.slice(0, 10).split("-").reverse().join("/") : "");
const dm = (iso: string) => (iso ? iso.slice(0, 10).split("-").reverse().slice(0, 2).join("/") : "");
const chuan = (s: string) => s.toLowerCase().replace(/ð/g, "đ");
const nutHang = "h-8 px-3 rounded-lg border border-input bg-white text-[12.5px] font-semibold hover:bg-muted inline-flex items-center justify-center gap-1.5 whitespace-nowrap";

// TNB-08 — cột "Bản in": đọc từ SQLite của tool (chưa in / đang chọn · cần chọn / đã in dd/mm · N chọn lại).
function BanIn({ b }: { b: Bc2Dong }) {
  const x = b.ban_in;
  if (!x) return <span className="text-muted-foreground text-[12px]">Chưa in từ tool</span>;
  if (x.so_can_chon > 0)
    return <span className="text-[11px] font-semibold px-2 rounded-full border text-destructive bg-destructive/10 border-destructive/30">Đang chọn · {x.so_can_chon} cần chọn</span>;
  const chonLai = x.so_chon_lai > 0 ? ` · ${x.so_chon_lai} chọn lại` : "";
  if (x.da_in_luc)
    return <span className="text-[11px] font-semibold px-2 rounded-full border text-muted-foreground bg-muted border-border">Đã in {dm(x.da_in_luc)}{chonLai}</span>;
  return <span className="text-[11px] font-semibold px-2 rounded-full border text-tn bg-tn-soft border-tn-border">Đang chọn{chonLai}</span>;
}

export default function DanhSachBc2({
  loai,
  onXem,
  onThem,
  onIn,
}: {
  loai: LoaiHang;
  onXem: (b: Bc2Dong) => void;
  onThem: (b: Bc2Dong) => void;
  onIn: (b: Bc2Dong) => void;
}) {
  const [q, setQ] = useState("");
  const [dong, setDong] = useState<"mo" | "dong">("mo");
  const [kq, setKq] = useState<DsBc2Resp | null>(null);
  const [loi, setLoi] = useState<string | null>(null);
  const [tai, setTai] = useState(0);

  useEffect(() => {
    let huy = false;
    setLoi(null);
    setKq(null);
    dsBc2(loai, dong)
      .then((d) => { if (!huy) setKq(d); })
      .catch((e: unknown) => { if (!huy) setLoi(e instanceof Error ? e.message : "Không tải được danh sách BC2"); });
    return () => { huy = true; };
  }, [loai, dong, tai]);

  const tatCa = kq?.bc2 ?? [];
  const ds = useMemo(() => {
    const t = chuan(q.trim());
    return t ? tatCa.filter((b) => chuan(`${b.so_bao_cao} ${b.so_bc1} ${b.ten_kh} ${b.ma_kh}`).includes(t)) : tatCa;
  }, [tatCa, q]);

  return (
    <div className="mt-4">
      <div className="flex flex-wrap items-center gap-3">
        <div className="inline-flex rounded-lg border border-border overflow-hidden" role="group" aria-label="Lọc BC2">
          {([["mo", "Đang mở"], ["dong", "Đã đóng / đã có kết quả (chỉ xem)"]] as const).map(([v, t]) => (
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
        <input aria-label="Tìm BC2" className="field-input" style={{ width: 240, height: 32 }} value={q}
          placeholder="Tìm số BC2, BC1, tên khóa" onChange={(e) => setQ(e.target.value)} />
        <div className="text-[12px] text-muted-foreground">
          BC2 <b>đang mở</b> = còn thêm/gỡ học viên được. BC2 đã <b>gửi hoặc có kết quả</b> bị khóa (chỉ xem, in) — việc đóng BC2 do phần mềm cũ làm.
        </div>
        {kq && (
          <div className="ml-auto text-[12px] text-muted-foreground" data-testid="tom-tat-ds-bc2">
            {soVN(kq.tong)} BC2{kq.lech > 0 ? ` · ${soVN(kq.lech)} có "Tổng ghi" khác "HV thực tế"` : ""}
          </div>
        )}
      </div>

      {loi && <div className="mt-3 rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-[13px] text-destructive">{loi}</div>}
      {!kq && !loi && <div className="mt-3 text-[13px] text-muted-foreground">Đang tải…</div>}
      {kq && (
        <div className="mt-3 rounded-xl border border-border bg-card overflow-auto">
          <table className="w-full text-[13px]">
            <thead>
              <tr className="text-left text-[12px] text-muted-foreground border-b border-border">
                <th className="px-3 py-2 font-semibold">Số BC2</th>
                <th className="py-2 pr-3 font-semibold">Ngày báo cáo</th>
                <th className="py-2 pr-3 font-semibold">BC1</th>
                <th className="py-2 pr-3 font-semibold">Khóa</th>
                <th className="py-2 pr-3 font-semibold text-right">Tổng ghi</th>
                <th className="py-2 pr-3 font-semibold text-right">HV thực tế</th>
                <th className="py-2 pr-3 font-semibold">Trạng thái</th>
                <th className="py-2 pr-3 font-semibold">Bản in</th>
                <th className="py-2 pr-3 font-semibold">Người tạo</th>
                <th className="py-2 pr-3" />
              </tr>
            </thead>
            <tbody>
              {ds.length === 0 && (
                <tr><td colSpan={10} className="text-center text-muted-foreground py-8">
                  {q.trim() ? "Không có BC2 khớp." : dong === "mo" ? "Chưa có BC2 đang mở." : "Chưa có BC2 đã đóng hoặc đã có kết quả."}
                </td></tr>
              )}
              {ds.map((b) => (
                <tr key={b.ma_bc2} onClick={() => onXem(b)} data-testid={`bc2-${b.ma_bc2}`}
                  className="border-b border-border last:border-b-0 hover:bg-tn-soft/40 cursor-pointer">
                  <td className="px-3 py-2 font-mono font-medium whitespace-nowrap">{b.ma_bc2}</td>
                  <td className="py-2 pr-3 tabular-nums whitespace-nowrap">{dmy(b.ngay_bao_cao)}</td>
                  <td className="py-2 pr-3 font-mono text-[12px] whitespace-nowrap">{b.so_bc1 || "—"}</td>
                  <td className="py-2 pr-3">{b.ten_kh || b.ma_kh || "—"}</td>
                  <td className="py-2 pr-3 text-right tabular-nums">{b.tong_ghi ?? "—"}</td>
                  <td className="py-2 pr-3 text-right tabular-nums">
                    {soVN(b.hv_thuc_te)}
                    {b.lech && (
                      <span title="Tổng ghi khác HV thực tế — bình thường (phần mềm cũ không đếm lại; HV thi lại chuyển sang BC2 khác)"
                        className="ml-1 text-[10.5px] font-semibold px-1.5 rounded border border-warning/40 bg-warning/10 text-warning">
                        lệch
                      </span>
                    )}
                  </td>
                  <td className="py-2 pr-3 whitespace-nowrap">
                    <TrangThaiBc2 tt={b.trang_thai ?? (b.dang_mo ? 0 : 1)} hvKetQua={b.hv_ket_qua} />
                  </td>
                  <td className="py-2 pr-3 whitespace-nowrap" data-testid={`ban-in-${b.ma_bc2}`}><BanIn b={b} /></td>
                  <td className="py-2 pr-3 whitespace-nowrap">{b.nguoi_tao || "—"}</td>
                  <td className="py-2 pr-3 text-right whitespace-nowrap">
                    {/* Các nút cùng một hàng căn giữa, cùng cao: tránh lệch dòng khi có/không có nút "+ Thêm" */}
                    <div className="inline-flex items-center justify-end gap-1.5 align-middle">
                      <button type="button" onClick={(e) => { e.stopPropagation(); onXem(b); }} aria-label={`Xem BC2 ${b.ma_bc2}`}
                        className={nutHang}>
                        Xem
                      </button>
                      <button type="button" onClick={(e) => { e.stopPropagation(); onIn(b); }} aria-label={`In BC2 ${b.ma_bc2}`}
                        className={nutHang} data-testid={`in-bc2-${b.ma_bc2}`}>
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"
                          strokeLinejoin="round" aria-hidden="true"><path d="M6 9V3h12v6" /><rect x="4" y="9" width="16" height="8" rx="2" /><path d="M7 14h10v7H7z" /></svg>
                        In BC2
                      </button>
                      {b.dang_mo && (
                        <button type="button" onClick={(e) => { e.stopPropagation(); onThem(b); }}
                          aria-label={`Thêm học viên vào BC2 ${b.ma_bc2}`}
                          className="h-8 px-3 rounded-lg bg-tn text-white text-[12.5px] font-semibold inline-flex items-center justify-center whitespace-nowrap">
                          + Thêm học viên
                        </button>
                      )}
                    </div>
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
