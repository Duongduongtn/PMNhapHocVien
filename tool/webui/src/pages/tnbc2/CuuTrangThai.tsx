import { useCallback, useEffect, useRef, useState } from "react";
import ChuGiaiTrangThai from "../../components/ChuGiaiTrangThai";
import PanelCuuTrangThai from "../../components/tnbc2/PanelCuuTrangThai";
import { soVN } from "../../lib/format";
import { LoiTnbc2, timHvCuu, type HvCuu, type LoaiHang, type TimCuuResp } from "../../lib/tnbc2Api";

// TNB-06 (2/2) — tab "Học viên không tìm thấy": tìm HV trên toàn DB, nói rõ vì sao không có trong danh sách BC2,
// và chuyển về đúng trạng thái chờ lập BC2 (có lý do, hoàn tác một lần). Bám ui-mock/tnbc2.html `viewCuu`.

export default function CuuTrangThai() {
  const [q, setQ] = useState("");
  const [loai, setLoai] = useState<LoaiHang | "">("");
  const [kq, setKq] = useState<TimCuuResp | null>(null);
  const [loi, setLoi] = useState<string | null>(null);
  const [dang, setDang] = useState(false);
  const [chon, setChon] = useState<HvCuu | null>(null);
  const daTim = useRef({ q: "", loai: "" as LoaiHang | "" });

  const tim = useCallback(async (tu: string, lo: LoaiHang | "") => {
    const t = tu.trim();
    if (t.length < 2) {
      setLoi("Nhập ít nhất 2 ký tự để tìm");
      return;
    }
    daTim.current = { q: t, loai: lo };
    setDang(true);
    setLoi(null);
    try {
      setKq(await timHvCuu(t, lo));
    } catch (e) {
      setKq(null);
      setLoi(e instanceof LoiTnbc2 ? e.message : e instanceof Error ? e.message : "Không tìm được");
    } finally {
      setDang(false);
    }
  }, []);

  // Đổi loại khi đã có kết quả → tìm lại với loại mới
  useEffect(() => {
    if (daTim.current.q && daTim.current.loai !== loai) {
      setChon(null);
      void tim(daTim.current.q, loai);
    }
  }, [loai, tim]);

  const lamTuoi = () => {
    if (daTim.current.q) void tim(daTim.current.q, daTim.current.loai);
  };

  return (
    <div className="h-full flex flex-col min-h-0">
      <div className="shrink-0 bg-card border-b border-border px-4 py-3 flex flex-wrap items-end gap-3">
        <div className="w-[420px] max-w-full">
          <label className="field-label" htmlFor="cuu-tim">Tìm học viên không thấy khi lập BC2 (tên / số CMT / mã đăng ký)</label>
          <input id="cuu-tim" className="field-input" value={q} placeholder="vd: nguyen van an"
            onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") void tim(q, loai); }} />
        </div>
        <div>
          <label className="field-label" htmlFor="cuu-loai">Loại hạng</label>
          <select id="cuu-loai" className="field-input" value={loai} onChange={(e) => setLoai(e.target.value as LoaiHang | "")}>
            <option value="">Cả hai</option>
            <option value="oto">Ô tô</option>
            <option value="moto">Mô tô</option>
          </select>
        </div>
        <button type="button" onClick={() => void tim(q, loai)} disabled={dang}
          className="h-9 px-4 rounded-lg bg-tn text-white text-[13px] font-semibold disabled:opacity-45">
          Tìm
        </button>
        <div className="text-[12px] text-muted-foreground max-w-[540px] leading-snug">
          Dùng khi một học viên đã tốt nghiệp hoặc vắng/rớt sát hạch mà không có trong danh sách. Chỉ đưa được về nhóm
          chờ lập BC2; không sửa kết quả sát hạch.
        </div>
        <ChuGiaiTrangThai />
      </div>

      {loi && <div className="shrink-0 px-4 py-2 text-[13px] bg-destructive/10 text-destructive border-b border-destructive/30">{loi}</div>}

      <div className="flex-1 min-h-0 flex">
        <div className="flex-1 min-w-0 overflow-auto">
          {!kq && !dang && (
            <div className="text-center text-muted-foreground py-14 text-[13.5px]">
              Gõ tên hoặc số CMT để tìm. Tool sẽ nói rõ vì sao học viên không có trong danh sách.
            </div>
          )}
          {dang && <div className="p-4 text-[13px] text-muted-foreground">Đang tìm…</div>}
          {kq && (
            <>
              {kq.tong_khop > kq.hoc_vien.length && (
                <div className="m-3 rounded-lg bg-muted px-3 py-2 text-[12.5px] text-muted-foreground">
                  Có {soVN(kq.tong_khop)} học viên khớp, chỉ hiện {soVN(kq.hoc_vien.length)} — gõ rõ hơn để thu hẹp.
                </div>
              )}
              <table className="w-full text-[13px]">
                <thead className="sticky top-0 bg-card border-b border-border z-10">
                  <tr className="text-left text-[12px] text-muted-foreground">
                    <th className="px-3 py-2 font-semibold">Tên học viên</th>
                    <th className="py-2 pr-3 font-semibold">Số CMT</th>
                    <th className="py-2 pr-3 font-semibold">Loại</th>
                    <th className="py-2 pr-3 font-semibold hidden min-[1400px]:table-cell">Khóa</th>
                    <th className="py-2 pr-3 font-semibold">Trạng thái hiện tại</th>
                    <th className="py-2 pr-3 font-semibold">Vì sao không thấy trong danh sách BC2?</th>
                    <th className="py-2 pr-3" />
                  </tr>
                </thead>
                <tbody>
                  {kq.hoc_vien.length === 0 && (
                    <tr><td colSpan={7} className="text-center text-muted-foreground py-10">Không tìm thấy học viên nào.</td></tr>
                  )}
                  {kq.hoc_vien.map((h) => {
                    const du = h.khong_hien.ma === "dang_hien";
                    const mau = du ? "text-success" : h.cuu_duoc ? "text-warning" : "text-destructive";
                    return (
                      <tr key={h.ma_dk} className={`border-b border-border ${chon?.ma_dk === h.ma_dk ? "bg-tn-soft" : ""}`}>
                        <td className="px-3 py-2 font-medium whitespace-nowrap">{h.ten}</td>
                        <td className="py-2 pr-3 font-mono text-[12px]">{h.cmt}</td>
                        <td className="py-2 pr-3 whitespace-nowrap">{h.loai === "oto" ? "Ô tô" : "Mô tô"}</td>
                        <td className="py-2 pr-3 hidden min-[1400px]:table-cell">{h.ten_kh || h.ma_kh}</td>
                        <td className="py-2 pr-3">
                          {h.ten_trang_thai} <span className="text-[10px] opacity-70">{h.tt}</span>
                        </td>
                        <td className={`py-2 pr-3 text-[12.5px] ${mau}`}>
                          {h.khac_loai ? "Khác loại hạng với loại đang chọn — không đổi trạng thái" : h.khong_hien.noi_dung}
                        </td>
                        <td className="py-2 pr-3 text-right whitespace-nowrap">
                          {h.cuu_duoc && !du && (
                            <button type="button" onClick={() => setChon(h)} aria-label={`Chuyển trạng thái ${h.ten}`}
                              className="h-8 px-3 rounded-lg border border-input text-[12.5px] font-semibold hover:bg-muted">
                              Chuyển…
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </>
          )}
        </div>
        {chon && (
          <PanelCuuTrangThai key={chon.ma_dk} hv={chon} loai={loai} onDong={() => setChon(null)} onDaDoi={lamTuoi} />
        )}
      </div>
    </div>
  );
}
