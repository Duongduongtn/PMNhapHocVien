import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import ChuGiaiTrangThai from "../../components/ChuGiaiTrangThai";
import DanSoGiayDialog from "../../components/tnbc2/DanSoGiayDialog";
import HopGhiTotNghiep from "../../components/tnbc2/HopGhiTotNghiep";
import { soVN } from "../../lib/format";
import { danhLienTiep, khoaSoGiay } from "../../lib/tnbcSoGiay";
import {
  dsHvTotNghiep,
  dsKhoaTotNghiep,
  xemLaiTotNghiep,
  type ChungTn,
  type DongTn,
  type DongXemLaiTn,
  type HvTn,
  type HvTnResp,
  type KhoaTnResp,
} from "../../lib/tnbc2Api";

// TNB-01 (3/3) — màn Tốt nghiệp (ô tô): chọn khóa → điền chung sổ/quyết định → số giấy liên tiếp / dán Excel /
// sửa tay (kiểm trùng ngay khi gõ) → Xem lại → Ghi. Bám ui-mock/tnbc2.html. Hủy/sửa tốt nghiệp: TNB-02 (task 108).

const CHUNG_TRONG: ChungTn = { so_so_tn: "", ngay_vao_so: "", so_quyet_dinh: "", ngay_ra_qd: "", ngay_in: "" };
const NHAN_TRANG_THAI = [
  ["", "Tất cả"],
  ["chua_tot_nghiep", "Chưa tốt nghiệp"],
  ["da_tot_nghiep", "Đã tốt nghiệp"],
  ["da_vao_bc2", "Đã vào BC2"],
] as const;

const isoSangVN = (iso: string | null | undefined) => (iso ? iso.slice(0, 10).split("-").reverse().join("/") : "");
const ngayVN = (iso: string | null | undefined) => isoSangVN(iso);
const chonDuoc = (h: HvTn) => h.sua_duoc && (h.trang_thai_tn === "chua_tot_nghiep" || (h.trang_thai_tn === "da_vao_bc2" && !h.so_giay));

function Huy({ children, kieu }: { children: string; kieu: "warn" | "ok" | "gray" | "red" }) {
  const lop = {
    warn: "text-warning bg-warning/10 border-warning/40",
    ok: "text-success bg-success/10 border-success/40",
    gray: "text-muted-foreground bg-muted border-border",
    red: "text-destructive bg-destructive/10 border-destructive/40",
  }[kieu];
  return <span className={`inline-block text-[11px] font-semibold px-2 rounded-full border whitespace-nowrap ${lop}`}>{children}</span>;
}

export default function TotNghiep() {
  const [cu, setCu] = useState(false);
  const [khoa, setKhoa] = useState<KhoaTnResp | null>(null);
  const [maKh, setMaKh] = useState("");
  const [q, setQ] = useState("");
  const [qTre, setQTre] = useState("");
  const [trangThai, setTrangThai] = useState("");
  const [data, setData] = useState<HvTnResp | null>(null);
  const [loi, setLoi] = useState<string | null>(null);
  const [dangTai, setDangTai] = useState(false);
  const [lamTuoi, setLamTuoi] = useState(0);

  const [sel, setSel] = useState<Set<string>>(new Set());
  const [giay, setGiay] = useState<Record<string, string>>({});
  const [chung, setChung] = useState<ChungTn>(CHUNG_TRONG);
  const [batDau, setBatDau] = useState("");
  const [loiDanh, setLoiDanh] = useState("");
  const [dan, setDan] = useState(false);
  const [hop, setHop] = useState<{ dong: DongTn[]; chung: ChungTn } | null>(null);
  const [kiem, setKiem] = useState<Record<string, DongXemLaiTn>>({});

  const hvDaThay = useRef<Map<string, HvTn>>(new Map());
  const khoaDaNap = useRef("");
  const napLaiBatDau = useRef(false);   // sau khi ghi: số bắt đầu gợi ý phải tính lại từ DB

  // Danh sách khóa
  useEffect(() => {
    let huy = false;
    dsKhoaTotNghiep(cu)
      .then((k) => {
        if (huy) return;
        setKhoa(k);
        setBatDau((b) => b || k.so_giay_ke_tiep);
        setMaKh((cur) => (k.khoa.some((x) => x.ma_kh === cur) ? cur : (k.khoa.find((x) => x.ghi_duoc) ?? k.khoa[0])?.ma_kh ?? ""));
      })
      .catch((e: unknown) => { if (!huy) setLoi(e instanceof Error ? e.message : "Không tải được danh sách khóa"); });
    return () => { huy = true; };
  }, [cu]);

  // Ô tìm: chờ ngừng gõ rồi mới hỏi server
  useEffect(() => {
    const t = setTimeout(() => setQTre(q), 300);
    return () => clearTimeout(t);
  }, [q]);

  // Học viên của khóa
  useEffect(() => {
    if (!maKh) { setData(null); return; }
    let huy = false;
    setDangTai(true);
    setLoi(null);
    dsHvTotNghiep(maKh, qTre, trangThai)
      .then((d) => {
        if (huy) return;
        setData(d);
        d.hoc_vien.forEach((h) => hvDaThay.current.set(h.ma_dk, h));
        if (napLaiBatDau.current) {
          napLaiBatDau.current = false;
          setBatDau(d.so_giay_ke_tiep);
        }
        if (khoaDaNap.current !== maKh) {   // đổi khóa: nạp lại bộ chung + bỏ chọn
          khoaDaNap.current = maKh;
          hvDaThay.current = new Map(d.hoc_vien.map((h) => [h.ma_dk, h]));
          setSel(new Set());
          setGiay({});
          setKiem({});
          setBatDau(d.so_giay_ke_tiep);
          setChung(d.so_chung ? { ...CHUNG_TRONG, ...pick(d.so_chung) } : CHUNG_TRONG);
        }
      })
      .catch((e: unknown) => { if (!huy) { setData(null); setLoi(e instanceof Error ? e.message : "Không tải được học viên"); } })
      .finally(() => { if (!huy) setDangTai(false); });
    return () => { huy = true; };
  }, [maKh, qTre, trangThai, lamTuoi]);

  const ds = useMemo(
    () => [...(data?.hoc_vien ?? [])].sort((a, b) => a.ten.localeCompare(b.ten, "vi")),
    [data],
  );
  const giayHieuLuc = useCallback((h: HvTn) => giay[h.ma_dk] ?? h.so_giay, [giay]);

  // Trùng ngay khi gõ — trong danh sách đang nhập (tức thì) + trong DB (xem-lai, debounce)
  const demKhoa = useMemo(() => {
    const m = new Map<string, number>();
    for (const h of hvDaThay.current.values()) {
      const k = khoaSoGiay(giayHieuLuc(h));
      if (k) m.set(k, (m.get(k) ?? 0) + 1);
    }
    return m;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, giay, giayHieuLuc]);
  const trungCucBo = (h: HvTn) => {
    if (giay[h.ma_dk] === undefined) return false;
    const k = khoaSoGiay(giay[h.ma_dk]);
    return !!k && (demKhoa.get(k) ?? 0) > 1;
  };

  const hvChon = useMemo(
    () => [...sel].map((ma) => hvDaThay.current.get(ma)).filter((h): h is HvTn => !!h),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [sel, data],
  );
  const dongGhi = useCallback(
    (): DongTn[] => hvChon.map((h) => ({ ma_dk: h.ma_dk, so_giay: (giay[h.ma_dk] ?? h.so_giay).trim() })),
    [hvChon, giay],
  );

  useEffect(() => {
    if (!maKh || hvChon.length === 0) { setKiem({}); return; }
    let huy = false;
    const t = setTimeout(() => {
      xemLaiTotNghiep(maKh, dongGhi(), chung)
        .then((r) => { if (!huy) setKiem(Object.fromEntries(r.dong.map((d) => [d.ma_dk, d]))); })
        .catch(() => { if (!huy) setKiem({}); });
    }, 600);
    return () => { huy = true; clearTimeout(t); };
  }, [maKh, hvChon, giay, chung, dongGhi]);

  function chonMot(h: HvTn, bat: boolean) {
    setSel((s) => { const n = new Set(s); if (bat) n.add(h.ma_dk); else n.delete(h.ma_dk); return n; });
  }
  function chonTatCa(bat: boolean) {
    setSel((s) => { const n = new Set(s); ds.filter(chonDuoc).forEach((h) => (bat ? n.add(h.ma_dk) : n.delete(h.ma_dk))); return n; });
  }
  function chonChuaGiay() {
    // chỉ nhóm "Đã học xong, chưa tốt nghiệp" (03); HV đã vào BC2 thiếu giấy là ca đặc biệt — tích tay
    setSel(new Set(ds.filter((h) => h.trang_thai_tn === "chua_tot_nghiep" && chonDuoc(h) && !h.so_giay).map((h) => h.ma_dk)));
  }
  function danhSo() {
    const can = ds.filter((h) => sel.has(h.ma_dk) && chonDuoc(h) && !h.so_giay);
    const kq = danhLienTiep(batDau.trim(), can.map((h) => h.ma_dk));
    if (!kq) { setLoiDanh("Số bắt đầu phải kết thúc bằng chữ số, vd N1|7329"); return; }
    setLoiDanh("");
    setGiay((g) => ({ ...g, ...kq }));
  }
  function apDan(cacSo: string[]) {
    const can = ds.filter((h) => sel.has(h.ma_dk) && chonDuoc(h));
    setGiay((g) => { const n = { ...g }; can.forEach((h, i) => { n[h.ma_dk] = cacSo[i]; }); return n; });
    setDan(false);
  }

  const tenHv = useMemo(() => Object.fromEntries([...hvDaThay.current.values()].map((h) => [h.ma_dk, h.ten])),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [data]);
  const ghiDuocKhoa = !!data?.ghi_duoc;
  const khoaChon = khoa?.khoa.find((k) => k.ma_kh === maKh);
  const soDanDuoc = ds.filter((h) => sel.has(h.ma_dk) && chonDuoc(h)).length;
  const tatCaDaChon = ds.filter(chonDuoc).length > 0 && ds.filter(chonDuoc).every((h) => sel.has(h.ma_dk));
  const khongTrungCucBo = hvChon.every((h) => !trungCucBo(h));
  const setC = (k: keyof ChungTn, v: string) => setChung((c) => ({ ...c, [k]: v }));

  return (
    <div className="h-full flex flex-col min-h-0">
      {/* Bộ lọc */}
      <div className="shrink-0 bg-card border-b border-border px-4 py-2.5 flex flex-wrap items-end gap-3">
        <div className="w-[340px] max-w-full">
          <label className="field-label" htmlFor="tn-khoa">Khóa học</label>
          <select id="tn-khoa" className="field-input" value={maKh} onChange={(e) => setMaKh(e.target.value)}>
            {!khoa?.khoa.length && <option value="">{khoa ? "Không có khóa trong phạm vi" : "Đang tải…"}</option>}
            {khoa?.khoa.map((k) => (
              <option key={k.ma_kh} value={k.ma_kh}>
                {k.ten_kh} · bế giảng {ngayVN(k.ngay_bg)}{k.ghi_duoc ? "" : " (chưa)"}
              </option>
            ))}
          </select>
        </div>
        <div className="w-[280px] max-w-full">
          <label className="field-label" htmlFor="tn-tim">Tìm theo tên / số CMT / mã đăng ký</label>
          <input id="tn-tim" className="field-input" value={q} onChange={(e) => setQ(e.target.value)} placeholder="gõ không dấu cũng được, vd: nguyen thi hoa" />
        </div>
        <div className="w-[170px]">
          <label className="field-label" htmlFor="tn-tt">Trạng thái</label>
          <select id="tn-tt" className="field-input" value={trangThai} onChange={(e) => setTrangThai(e.target.value)}>
            {NHAN_TRANG_THAI.map(([v, t]) => <option key={v} value={v}>{t}</option>)}
          </select>
        </div>
        <label className="inline-flex items-center gap-2 h-9 px-3 rounded-lg border border-border bg-white text-[13px] cursor-pointer">
          <input type="checkbox" checked={cu} onChange={(e) => { setCu(e.target.checked); setMaKh(""); khoaDaNap.current = ""; }} />
          Hiện khóa cũ
        </label>
        <ChuGiaiTrangThai />
        <div className="ml-auto text-[12px] text-muted-foreground text-right leading-snug">
          {khoa && <>Mặc định: khóa bế giảng từ <b>{ngayVN(khoa.moc_cua_so)}</b> đến hôm nay<br /></>}
          {data ? `${soVN(ds.length)} / ${soVN(data.tong)} học viên` : ""}
        </div>
      </div>

      {loi && <div className="shrink-0 px-4 py-2 text-[13px] bg-destructive/10 text-destructive border-b border-destructive/30">{loi}</div>}
      {data && !ghiDuocKhoa && (
        <div className="shrink-0 px-4 py-2 text-[13px] bg-warning/10 text-warning border-b border-warning/30">
          Khóa này chưa bế giảng ({ngayVN(data.ngay_bg)}) — chỉ xem, không ghi được.
        </div>
      )}

      <div className="flex-1 min-h-0 flex">
        {/* Bảng học viên */}
        <div className="flex-1 min-w-0 overflow-auto">
          <table className="w-full text-[13px]">
            <thead className="sticky top-0 bg-card border-b border-border z-10">
              <tr className="text-left text-[12px] text-muted-foreground">
                <th className="w-8 px-3 py-2">
                  <input type="checkbox" aria-label="Chọn tất cả" checked={tatCaDaChon} onChange={(e) => chonTatCa(e.target.checked)} />
                </th>
                <th className="py-2 pr-3 font-semibold">Tên học viên</th>
                <th className="py-2 pr-3 font-semibold">Ngày sinh</th>
                <th className="py-2 pr-3 font-semibold">Số CMT</th>
                <th className="py-2 pr-3 font-semibold">Tên khóa học</th>
                <th className="py-2 pr-3 font-semibold">Trạng thái</th>
                <th className="py-2 pr-3 font-semibold w-[170px]">Số giấy CNTN</th>
              </tr>
            </thead>
            <tbody>
              {ds.length === 0 && (
                <tr>
                  <td colSpan={7} className="text-center text-muted-foreground py-10">
                    {dangTai ? "Đang tải…" : "Không có học viên phù hợp. Bật \"Hiện khóa cũ\" để xem khóa bế giảng trước " + ngayVN(khoa?.moc_cua_so) + "."}
                  </td>
                </tr>
              )}
              {ds.map((h) => {
                const duoc = chonDuoc(h);
                const k = kiem[h.ma_dk];
                const chanServer = k && !k.ghi_duoc && k.chan.length > 0 ? k.chan[0].noi_dung : "";
                const trung = trungCucBo(h);
                const sai = trung || !!chanServer;
                const ghiChu = trung ? "Số giấy bị trùng trong danh sách đang nhập" : chanServer;
                const trungCoSan = k?.thong_tin.find((t) => t.ma === "trung_co_san");
                return (
                  <tr key={h.ma_dk} className={`border-b border-border hover:bg-tn-soft/40 ${sel.has(h.ma_dk) ? "bg-tn-soft" : ""} ${duoc ? "" : "text-muted-foreground"}`}>
                    <td className="px-3 py-1.5">
                      <input type="checkbox" aria-label={`Chọn ${h.ten}`} checked={sel.has(h.ma_dk)} disabled={!duoc}
                        onChange={(e) => chonMot(h, e.target.checked)} />
                    </td>
                    <td className="py-1.5 pr-3 font-medium whitespace-nowrap">
                      {h.ten} {h.khoa_cu && <Huy kieu="warn">khóa cũ</Huy>}
                    </td>
                    <td className="py-1.5 pr-3 tabular-nums whitespace-nowrap">{h.ngay_sinh}</td>
                    <td className="py-1.5 pr-3 font-mono text-[12px] whitespace-nowrap">{h.cmt}</td>
                    <td className="py-1.5 pr-3 max-w-[130px] truncate" title={khoa?.khoa.find((x) => x.ma_kh === h.ma_kh)?.ten_kh ?? data?.ten_kh}>
                      {khoa?.khoa.find((x) => x.ma_kh === h.ma_kh)?.ten_kh ?? data?.ten_kh}
                    </td>
                    <td className="py-1.5 pr-3">
                      <Huy kieu={h.trang_thai_tn === "da_tot_nghiep" ? "ok" : h.trang_thai_tn === "khac" ? "red" : h.trang_thai_tn === "da_vao_bc2" ? "gray" : "warn"}>
                        {h.ten_trang_thai}
                      </Huy>
                      {h.ly_do_khoa && <div className="text-[11px] text-warning mt-0.5">{h.ly_do_khoa}</div>}
                      {!h.ly_do_khoa && h.trang_thai_tn === "da_tot_nghiep" && (
                        <div className="text-[11px] text-muted-foreground mt-0.5">Sửa / hủy ở bước riêng</div>
                      )}
                    </td>
                    <td className="py-1.5 pr-3">
                      {duoc ? (
                        <>
                          <input aria-label={`Số giấy của ${h.ten}`} placeholder="N1|…"
                            className={`field-input font-mono !py-1 !text-[12.5px] ${sai ? "!border-destructive !bg-destructive/5" : ""}`}
                            value={giay[h.ma_dk] ?? h.so_giay}
                            onChange={(e) => setGiay((g) => ({ ...g, [h.ma_dk]: e.target.value }))} />
                          {ghiChu && <div className="text-[11px] text-destructive mt-0.5">{ghiChu}</div>}
                          {!ghiChu && trungCoSan && <div className="text-[11px] text-muted-foreground mt-0.5">Vốn đã trùng từ trước</div>}
                        </>
                      ) : (
                        <span className="font-mono text-[12px]">{h.so_giay || "—"}</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Điền chung */}
        <aside className="shrink-0 w-[330px] border-l border-border bg-card p-3 overflow-auto space-y-3">
          <div className="text-[13px] font-semibold">Điền chung cho {soVN(sel.size)} học viên đã tích</div>
          {data?.so_chung && (
            <div className="text-[11.5px] text-muted-foreground">
              Điền sẵn từ {soVN(data.so_chung.so_hv)} học viên cùng khóa đã có sổ.
            </div>
          )}
          <div>
            <label className="field-label" htmlFor="tn-so">Số sổ tốt nghiệp</label>
            <input id="tn-so" className="field-input" placeholder="01/XNĐT/2026" value={chung.so_so_tn} onChange={(e) => setC("so_so_tn", e.target.value)} />
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="field-label" htmlFor="tn-ngayso">Ngày vào sổ</label>
              <input id="tn-ngayso" type="date" className="field-input" value={chung.ngay_vao_so} onChange={(e) => setC("ngay_vao_so", e.target.value)} />
            </div>
            <div>
              <label className="field-label" htmlFor="tn-ngayin">Ngày in giấy</label>
              <input id="tn-ngayin" type="date" className="field-input" value={chung.ngay_in} onChange={(e) => setC("ngay_in", e.target.value)} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="field-label" htmlFor="tn-qd">Số quyết định</label>
              <input id="tn-qd" className="field-input" placeholder="100/TTTĐ" value={chung.so_quyet_dinh} onChange={(e) => setC("so_quyet_dinh", e.target.value)} />
            </div>
            <div>
              <label className="field-label" htmlFor="tn-ngayqd">Ngày ra quyết định</label>
              <input id="tn-ngayqd" type="date" className="field-input" value={chung.ngay_ra_qd} onChange={(e) => setC("ngay_ra_qd", e.target.value)} />
            </div>
          </div>
          <div className="rounded-lg bg-muted px-3 py-2 text-[12px] text-muted-foreground">
            Nhập đúng số/ngày quyết định theo giấy tờ thật; tool không tự bịa. Một bộ này dùng chung cho cả lượt ghi
            — cần sổ khác thì ghi theo nhóm.
          </div>
          <div className="border-t border-border pt-3">
            <label className="field-label" htmlFor="tn-batdau">Số giấy chứng nhận tốt nghiệp bắt đầu từ</label>
            <div className="flex gap-2">
              <input id="tn-batdau" className="field-input font-mono" value={batDau} onChange={(e) => setBatDau(e.target.value)} />
              <button type="button" onClick={danhSo}
                className="h-[34px] px-3 rounded-lg border border-input text-[13px] font-semibold hover:bg-muted whitespace-nowrap">
                Đánh liên tiếp
              </button>
            </div>
            {loiDanh && <div className="text-[12px] text-destructive mt-1">{loiDanh}</div>}
            <div className="text-[11.5px] text-muted-foreground mt-1">
              Đánh theo thứ tự tên cho học viên đã tích chưa có số giấy. Sửa tay từng ô được; kiểm trùng ngay khi gõ.
            </div>
            <button type="button" disabled={soDanDuoc === 0} onClick={() => setDan(true)}
              className="mt-2 h-8 px-3 rounded-lg border border-input text-[12.5px] font-semibold hover:bg-muted disabled:opacity-45 disabled:cursor-not-allowed">
              Dán từ Excel…
            </button>
          </div>
          <div className="text-[12px] text-muted-foreground border-t border-border pt-2 leading-relaxed">
            <b>Lưu sổ trước, cấp giấy sau:</b> chưa có số giấy → ghi sổ/quyết định, học viên vẫn là "chưa tốt nghiệp".
            Có số giấy → "Đã tốt nghiệp".<br />
            <b>Khóa chưa bế giảng</b> chỉ xem, không ghi được.
          </div>
        </aside>
      </div>

      {/* Thanh đáy */}
      <div className="shrink-0 h-14 bg-card border-t border-border px-4 flex items-center gap-3">
        <span className="text-[13px]"><b>{soVN(sel.size)}</b> học viên đã chọn{khoaChon && !khoaChon.ghi_duoc ? " (khóa chưa bế giảng)" : ""}</span>
        <button type="button" onClick={chonChuaGiay} disabled={!ghiDuocKhoa}
          className="h-9 px-3 rounded-lg border border-input text-[13px] font-semibold hover:bg-muted disabled:opacity-45 disabled:cursor-not-allowed">
          Chọn học viên chưa có số giấy
        </button>
        <button type="button" onClick={() => setLamTuoi((n) => n + 1)}
          className="h-9 px-3 rounded-lg border border-transparent text-[13px] font-semibold text-primary hover:bg-accent">
          Làm tươi
        </button>
        <button type="button"
          disabled={sel.size === 0 || !ghiDuocKhoa || !khongTrungCucBo}
          title={!khongTrungCucBo ? "Có số giấy trùng trong danh sách — sửa trước" : undefined}
          onClick={() => setHop({ dong: dongGhi(), chung: { ...chung } })}
          className="ml-auto h-9 px-4 rounded-lg bg-tn text-white text-[13px] font-semibold disabled:opacity-45 disabled:cursor-not-allowed">
          Xem lại &amp; ghi {soVN(sel.size)} học viên
        </button>
      </div>

      {dan && <DanSoGiayDialog soHocVien={soDanDuoc} onAp={apDan} onDong={() => setDan(false)} />}
      {hop && (
        <HopGhiTotNghiep
          maKh={maKh}
          dong={hop.dong}
          chung={hop.chung}
          tenHv={tenHv}
          onDong={() => setHop(null)}
          onXong={() => {
            setHop(null);
            setSel(new Set());
            setGiay({});
            setKiem({});
            napLaiBatDau.current = true;
            setLamTuoi((n) => n + 1);
          }}
        />
      )}
    </div>
  );
}

function pick(c: { so_so_tn: string; ngay_vao_so: string; so_quyet_dinh: string; ngay_ra_qd: string; ngay_in: string }): ChungTn {
  return {
    so_so_tn: c.so_so_tn,
    ngay_vao_so: c.ngay_vao_so,
    so_quyet_dinh: c.so_quyet_dinh,
    ngay_ra_qd: c.ngay_ra_qd,
    ngay_in: c.ngay_in,
  };
}
