import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Icon } from "../../components/Icon";
import { PhanTrang } from "../../components/PhanTrang";
import { ComboLoc } from "../../components/ComboLoc";
import { ODate } from "../../components/ODate";
import { boDau } from "../../lib/format";
import {
  getSyncTargets, getSyncNam, getSyncKhoa, postSyncHocVien, postSyncRun, openSyncStream, testSyncTarget,
  type SyncTarget, type SyncKhoa, type SyncHV, type SyncHocVienData, type SyncTestKetQua,
} from "../../lib/api";

const hom_nay = () => new Date();
const vnHienTai = () => {
  const d = hom_nay();
  return `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}/${d.getFullYear()}`;
};
// ISO (yyyy-mm-dd...) → dd/mm/yyyy; rỗng → "–"
const isoVN = (s: string | null) => {
  if (!s) return "–";
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(s);
  return m ? `${m[3]}/${m[2]}/${m[1]}` : s.slice(0, 10);
};
// dd/mm/yyyy → Date | null
const parseVN = (s: string): Date | null => {
  const m = /^(\d{2})\/(\d{2})\/(\d{4})$/.exec(s.trim());
  if (!m) return null;
  const d = new Date(+m[3], +m[2] - 1, +m[1]);
  return d.getDate() === +m[1] ? d : null;
};
const toISO = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;

interface RowTT { trang_thai: string; mau: string }

export default function BanDongBo() {
  const navigate = useNavigate();
  const [targets, setTargets] = useState<SyncTarget[]>([]);
  const [targetKey, setTargetKey] = useState("");
  const [namNguon, setNamNguon] = useState<number[]>([]);
  const [namDich, setNamDich] = useState<number[]>([]);
  const [khoaNguon, setKhoaNguon] = useState<SyncKhoa[]>([]);
  const [khoaDich, setKhoaDich] = useState<SyncKhoa[]>([]);
  const [selNamNguon, setSelNamNguon] = useState<number>();
  const [selNamDich, setSelNamDich] = useState<number>();
  const [maKhNguon, setMaKhNguon] = useState("");
  const [maKhDich, setMaKhDich] = useState("");
  const [ngay, setNgay] = useState(vnHienTai());
  const [data, setData] = useState<SyncHocVienData | null>(null);
  const [chon, setChon] = useState<Set<string>>(new Set());
  const [rowTT, setRowTT] = useState<Record<string, RowTT>>({});
  const [onlyNew, setOnlyNew] = useState(false);
  const [tim, setTim] = useState("");
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(50);
  const [selCollapsed, setSelCollapsed] = useState(false);
  const [dangTai, setDangTai] = useState(false);
  const [chayPct, setChayPct] = useState<number | null>(null); // null = chưa chạy
  const [chayTxt, setChayTxt] = useState("");
  const [running, setRunning] = useState(false);
  const [err, setErr] = useState("");
  const [tongKet, setTongKet] = useState("");
  const [daTest, setDaTest] = useState(false); // 2b: bắt test kết nối đích trước khi Tải
  const [testKq, setTestKq] = useState<(SyncTestKetQua & { dang?: boolean }) | null>(null);
  const streamRef = useRef<AbortController | null>(null);

  const dichTarget = targets.find((t) => t.key === targetKey);
  const khoaDichSel = khoaDich.find((k) => k.ma_kh === maKhDich);
  const khoaNguonSel = khoaNguon.find((k) => k.ma_kh === maKhNguon);
  // Lịch chọn ngày giới hạn tối đa = min(hôm nay, NgàyKG khóa đích)
  const maxNgayISO = (() => {
    const t0 = new Date(); t0.setHours(0, 0, 0, 0);
    const kgm = khoaDichSel?.ngay_kg ? /^(\d{4})-(\d{2})-(\d{2})/.exec(khoaDichSel.ngay_kg) : null;
    const kg = kgm ? new Date(+kgm[1], +kgm[2] - 1, +kgm[3]) : null;
    return toISO(kg && kg < t0 ? kg : t0);
  })();

  // Nạp cấu hình + năm 2 bên
  useEffect(() => {
    getSyncTargets()
      .then((d) => {
        setTargets(d.targets);
        setTargetKey(d.selected);
      })
      .catch(() => setErr("Không đọc được cấu hình (tool backend chưa chạy?)"));
    getSyncNam("nguon").then((ns) => { setNamNguon(ns); setSelNamNguon(ns.find((n) => n === hom_nay().getFullYear()) ?? ns[0]); })
      .catch(() => setErr("Không đọc được danh sách năm/khóa nguồn (GPLX_CSDT) — kiểm cấu hình kết nối hoặc đăng nhập lại."));
  }, []);

  useEffect(() => {
    if (!targetKey) return;
    setDaTest(false); setTestKq(null); // đổi CSDL đích → bắt kiểm tra kết nối lại (2b)
    getSyncNam("dich", targetKey)
      .then((ns) => { setNamDich(ns); setSelNamDich(ns.find((n) => n === hom_nay().getFullYear()) ?? ns[0]); })
      .catch(() => setErr("Không đọc được danh sách năm/khóa CSDL đích — kiểm cấu hình kết nối đích."));
  }, [targetKey]);

  const kiemTraDich = async () => {
    if (!dichTarget) return;
    setTestKq({ ok: false, count: 0, message: "", dang: true });
    try {
      const kq = await testSyncTarget(dichTarget.database);
      setTestKq({ ...kq, dang: false });
      setDaTest(kq.ok);
    } catch {
      setTestKq({ ok: false, count: 0, message: "Gọi kiểm tra thất bại", dang: false });
      setDaTest(false);
    }
  };

  useEffect(() => {
    if (!selNamNguon) return;
    getSyncKhoa("nguon", selNamNguon).then((ks) => { setKhoaNguon(ks); setMaKhNguon(ks[0]?.ma_kh ?? ""); }).catch(() => setKhoaNguon([]));
  }, [selNamNguon]);

  useEffect(() => {
    if (!selNamDich || !targetKey) return;
    getSyncKhoa("dich", selNamDich, targetKey).then((ks) => { setKhoaDich(ks); setMaKhDich(ks[0]?.ma_kh ?? ""); }).catch(() => setKhoaDich([]));
  }, [selNamDich, targetKey]);

  const taiDanhSach = async () => {
    if (!maKhNguon) { setErr("Chưa chọn khóa nguồn."); return; }
    if (!daTest) { setErr("Hãy Kiểm tra kết nối CSDL đích trước khi tải danh sách."); return; }
    setErr(""); setTongKet(""); setRowTT({}); setChayPct(null); setDangTai(true);
    try {
      const d = await postSyncHocVien(maKhNguon, targetKey);
      setData(d);
      // Mặc định chọn tất cả HV sẽ tạo mới (chưa có đích, có CCCD)
      setChon(new Set(d.hoc_vien.filter((h) => !h.da_co_dich && !h.thieu_cccd).map((h) => h.so_cmt)));
      setPage(0);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Lỗi tải danh sách.");
      setData(null);
    } finally {
      setDangTai(false);
    }
  };

  // Lọc + phân trang (client)
  const loc = useMemo(() => {
    const list = data?.hoc_vien ?? [];
    const t = boDau(tim.trim().toLowerCase());
    return list.filter((h) => {
      if (onlyNew && (h.da_co_dich || h.thieu_cccd)) return false;
      if (!t) return true;
      return boDau((h.ho_ten || "").toLowerCase()).includes(t) || (h.so_cmt || "").includes(tim.trim());
    });
  }, [data, onlyNew, tim]);
  const trang = loc.slice(page * pageSize, page * pageSize + pageSize);
  const soChon = chon.size;

  const tickAll = (v: boolean) => {
    if (!data) return;
    setChon(v ? new Set(data.hoc_vien.filter((h) => !h.da_co_dich && !h.thieu_cccd).map((h) => h.so_cmt)) : new Set());
  };
  const tickRow = (cc: string, v: boolean) =>
    setChon((s) => { const n = new Set(s); if (v) n.add(cc); else n.delete(cc); return n; });

  const bdSync = async () => {
    setErr(""); setTongKet("");
    if (!maKhDich) { setErr("Chưa chọn khóa đích."); return; }
    if (soChon === 0) { setErr("Chưa chọn học viên nào để đồng bộ."); return; }
    if (khoaNguonSel && khoaDichSel && khoaNguonSel.hang_gplx !== khoaDichSel.hang_gplx) {
      setErr(`Hạng xe không khớp: nguồn ${khoaNguonSel.hang_gplx} ≠ đích ${khoaDichSel.hang_gplx}.`);
      return;
    }
    const d = parseVN(ngay);
    if (!d) { setErr("Ngày nhập HS phải dạng dd/mm/yyyy."); return; }
    const t0 = new Date(); t0.setHours(0, 0, 0, 0);
    if (d > t0) { setErr("Ngày nhập HS không được sau hôm nay."); return; }
    const cach = Math.floor((hom_nay().getTime() - d.getTime()) / 86400000);
    if (cach > 90 && !window.confirm(`Ngày nhập HS cách hôm nay ${cach} ngày (~${Math.floor(cach / 30)} tháng). Backdate xa vậy chắc chứ?`)) return;

    setRunning(true); setChayPct(0); setChayTxt("Đang mở phiên…"); setRowTT({});
    try {
      const { job_id } = await postSyncRun({
        ma_kh_nguon: maKhNguon, ma_kh_dich: maKhDich, ngay_nhap_hs: toISO(d),
        target_key: targetKey, so_cmt_chon: [...chon],
      });
      const total = soChon;
      let xong = 0;
      streamRef.current = openSyncStream(job_id, (ev) => {
        if (ev.loai === "hv") {
          const cc = String(ev.so_cmt ?? "");
          setRowTT((m) => ({ ...m, [cc]: { trang_thai: String(ev.trang_thai), mau: String(ev.mau) } }));
          xong += 1;
          setChayPct(Math.min(100, Math.round((xong / Math.max(total, 1)) * 100)));
          setChayTxt(`Đang đồng bộ… ${xong}/${total} — ${ev.ho_ten ?? ""}`);
        } else if (ev.loai === "xong") {
          setChayPct(100);
          setChayTxt(`Xong · ${ev.ok} tạo mới · ${ev.skip} bỏ qua · ${ev.loi} lỗi`);
          setTongKet(`Hoàn tất: ${ev.ok} tạo mới, ${ev.skip} bỏ qua, ${ev.loi} lỗi${ev.tong_so_hv != null ? ` · TongSoHV khóa đích: ${ev.tong_so_hv}` : ""}.`);
          setRunning(false);
          void taiDanhSach(); // làm tươi lưới (HV mới chuyển sang "đã có")
        } else if (ev.loai === "loi_he_thong") {
          setErr(`Lỗi hệ thống khi sync: ${ev.message}`);
          setRunning(false);
        }
      });
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Không mở được phiên đồng bộ.");
      setRunning(false); setChayPct(null);
    }
  };

  useEffect(() => () => streamRef.current?.abort(), []);

  const fmtKhoaNguon = (k: SyncKhoa) => `${k.ten_kh} — ${k.hang_gplx} (${k.so_hv} HV)`;
  const fmtKhoaDich = (k: SyncKhoa) => `${k.ten_kh} — ${k.hang_gplx} (KG ${isoVN(k.ngay_kg)}, ${k.so_hv} HV)`;

  return (
    <section className="h-full flex flex-col min-h-0">
      {/* KHUNG CHỌN KHÓA — cố định */}
      <div className="shrink-0 bg-card border-b border-border">
        <div className="px-4 py-2 flex items-center gap-2 flex-wrap">
          <span className="text-[13px] font-bold">Bàn đồng bộ</span>
          <span className="inline-flex items-center gap-1.5 text-[12px] text-muted-foreground">
            <span className="w-1.5 h-1.5 rounded-full bg-success" />Nguồn <b className="text-foreground">GPLX_CSDT</b>
            {dichTarget && <>· <span className="w-1.5 h-1.5 rounded-full bg-success" />Đích <b className="text-foreground">{dichTarget.database}</b></>}
          </span>
          <button onClick={() => setSelCollapsed((v) => !v)} className="ml-auto inline-flex items-center gap-1 text-[12px] text-muted-foreground hover:text-foreground">
            <Icon name="chevronDown" className={"w-4 h-4 transition-transform " + (selCollapsed ? "-rotate-90" : "")} />
            {selCollapsed ? "mở khung chọn" : "thu gọn khung chọn"}
          </button>
        </div>

        {!selCollapsed && (
          <div className="px-4 pb-2.5 space-y-2">
            {/* Hàng 1: chọn khóa nguồn + đích — hai khối cùng chiều cao, nhãn + combo thẳng hàng */}
            <div className="grid grid-cols-2 gap-x-6">
              <div>
                <label className="field-label">① Khóa nguồn (GPLX_CSDT)</label>
                <div className="flex gap-1.5 mt-1">
                  <select className="field-input !w-[80px] shrink-0" value={selNamNguon ?? ""} disabled={running} onChange={(e) => setSelNamNguon(+e.target.value)}>
                    {namNguon.map((n) => <option key={n} value={n}>{n}</option>)}
                  </select>
                  <ComboLoc className="flex-1 min-w-0" value={maKhNguon} disabled={running}
                    placeholder="Gõ tên/mã khóa nguồn…"
                    options={khoaNguon.map((k) => ({ ma: k.ma_kh, ten: fmtKhoaNguon(k) }))}
                    onChon={setMaKhNguon} />
                </div>
              </div>
              <div>
                <label className="field-label">② Khóa đích {dichTarget ? `(${dichTarget.name})` : ""} — cùng hạng</label>
                <div className="flex gap-1.5 mt-1">
                  {targets.length > 1 && (
                    <select className="field-input !w-[120px] shrink-0" value={targetKey} disabled={running} onChange={(e) => setTargetKey(e.target.value)}>
                      {targets.map((t) => <option key={t.key} value={t.key}>{t.name}</option>)}
                    </select>
                  )}
                  <select className="field-input !w-[80px] shrink-0" value={selNamDich ?? ""} disabled={running} onChange={(e) => setSelNamDich(+e.target.value)}>
                    {namDich.map((n) => <option key={n} value={n}>{n}</option>)}
                  </select>
                  <ComboLoc className="flex-1 min-w-0" value={maKhDich} disabled={running}
                    placeholder="Gõ tên/mã khóa đích…"
                    options={khoaDich.map((k) => ({ ma: k.ma_kh, ten: fmtKhoaDich(k) }))}
                    onChon={setMaKhDich} />
                </div>
              </div>
            </div>

            {/* Hàng 2: ngày + kiểm tra đích + người tạo + Tải — một dòng, căn đáy (wrap khi hẹp) */}
            <div className="flex items-end gap-x-5 gap-y-2 flex-wrap">
              <ODate
                className="w-44 shrink-0"
                label={<>③ Ngày nhập hồ sơ {khoaDichSel?.ngay_kg ? <span className="text-muted-foreground font-normal">(≤ KG {isoVN(khoaDichSel.ngay_kg)})</span> : null}</>}
                value={ngay}
                onChange={setNgay}
                disabled={running}
                max={maxNgayISO}
              />
              <div className="flex items-center gap-2 h-[34px]">
                <button type="button" onClick={kiemTraDich} disabled={!dichTarget || testKq?.dang || running}
                  className="inline-flex items-center gap-1 h-[30px] px-2.5 rounded-md border border-border text-[12.5px] hover:bg-muted disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sync whitespace-nowrap">
                  <Icon name="refresh" className={"w-3.5 h-3.5 " + (testKq?.dang ? "animate-spin" : "")} /> Kiểm tra kết nối đích
                </button>
                {testKq && !testKq.dang ? (
                  <span className={"inline-flex items-center gap-1 text-[12px] whitespace-nowrap " + (testKq.ok ? "text-success" : "text-destructive")}>
                    <Icon name={testKq.ok ? "check" : "warn"} className="w-3.5 h-3.5" sw={testKq.ok ? 3 : 2} /> {testKq.message}
                  </span>
                ) : (!daTest && <span className="text-[11.5px] text-muted-foreground whitespace-nowrap">Kiểm tra trước khi Tải</span>)}
              </div>
              <div className="ml-auto flex items-center gap-4 h-[34px]">
                <span className="text-[11.5px] text-muted-foreground whitespace-nowrap">
                  Người tạo: <b className="text-foreground" style={{ fontFamily: "ui-monospace,Consolas,monospace" }}>admin</b>
                </span>
                <button onClick={taiDanhSach} disabled={dangTai || running || !daTest} title={!daTest ? "Kiểm tra kết nối CSDL đích trước" : undefined}
                  className="inline-flex items-center gap-1.5 h-[34px] px-4 rounded-md bg-sync text-white font-semibold text-[13px] whitespace-nowrap hover:brightness-110 transition-all disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sync">
                  <Icon name="download" className={"w-4 h-4 " + (dangTai ? "animate-pulse" : "")} /> Tải danh sách
                </button>
              </div>
            </div>
          </div>
        )}

        {khoaDichSel?.bc1 && (
          <div className="px-4 py-1.5 flex items-center gap-2 text-[12px] bg-warning/10 border-t border-warning/30 text-warning">
            <Icon name="warn" className="w-4 h-4 shrink-0" />
            Khóa đích đã lập Báo cáo 1 — học viên thêm sẽ KHÔNG nằm trong BC1 đã nộp. Vẫn đồng bộ được nếu bạn chủ ý bù dữ liệu.
          </div>
        )}

        <div className="px-4 py-1.5 border-t border-border/70 flex items-center gap-3 bg-muted/30 flex-wrap">
          {data ? (
            <span className="text-[12.5px] text-muted-foreground">
              <b className="text-foreground">{data.tong}</b> HV · Đã có ở đích <b className="text-warning">{data.da_co_dich}</b> · Sẽ tạo mới <b className="text-success">{data.se_tao_moi}</b>
              {data.thieu_cccd > 0 && <> · <b className="text-destructive">{data.thieu_cccd}</b> thiếu CCCD</>}
              {data.trung_cccd_nguon > 0 && <> · <b className="text-destructive">{data.trung_cccd_nguon}</b> trùng CCCD</>}
            </span>
          ) : <span className="text-[12.5px] text-muted-foreground">Chọn khóa rồi bấm “Tải danh sách”.</span>}
          <label className="ml-auto inline-flex items-center gap-1.5 text-[12px] text-muted-foreground cursor-pointer whitespace-nowrap">
            <input type="checkbox" checked={onlyNew} onChange={(e) => { setOnlyNew(e.target.checked); setPage(0); }} /> Chỉ hiện HV sẽ tạo mới
          </label>
          <div className="relative">
            <Icon name="search" className="w-4 h-4 absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input className="field-input !w-56 !pl-8" placeholder="Tìm tên / CCCD" value={tim} onChange={(e) => { setTim(e.target.value); setPage(0); }} />
          </div>
        </div>
      </div>

      {/* BẢNG */}
      <div className="flex-1 min-h-0 overflow-auto bg-card">
        <table className="w-full text-[13px] border-collapse min-w-[1120px]">
          <thead className="sticky top-0 z-10">
            <tr className="bg-sync text-white text-left [&>th]:bg-sync [&>th]:sticky [&>th]:top-0">
              <th className="font-semibold px-2 py-1.5 w-9 text-center">
                <input type="checkbox" checked={!!data && soChon > 0 && soChon === data.se_tao_moi} onChange={(e) => tickAll(e.target.checked)} />
              </th>
              <th className="font-semibold px-2 py-1.5 w-10 text-center">STT</th>
              <th className="font-semibold px-2 py-1.5">Họ và tên</th>
              <th className="font-semibold px-2 py-1.5">Số CCCD</th>
              <th className="font-semibold px-2 py-1.5 w-12 text-center">Hạng</th>
              <th className="font-semibold px-2 py-1.5">MaDK nguồn</th>
              <th className="font-semibold px-2 py-1.5 w-[86px]">NgàyHS nguồn</th>
              <th className="font-semibold px-2 py-1.5">MaDK đích</th>
              <th className="font-semibold px-2 py-1.5 w-[86px]">NgàyHS đích</th>
              <th className="font-semibold px-2 py-1.5 w-12 text-center">Số HS</th>
              <th className="font-semibold px-2 py-1.5 w-44">Trạng thái</th>
            </tr>
          </thead>
          <tbody>
            {trang.length === 0 && (
              <tr><td colSpan={11} className="px-3 py-8 text-center text-muted-foreground">{data ? "Không có dòng khớp." : "Chưa tải danh sách."}</td></tr>
            )}
            {trang.map((h, i) => <Dong key={h.so_cmt || `r${i}`} h={h} stt={page * pageSize + i + 1} ticked={chon.has(h.so_cmt)} onTick={tickRow} tt={rowTT[h.so_cmt]} onXem={(maDk) => navigate(`/sync/tra-cuu?ma_dk=${encodeURIComponent(maDk)}`)} />)}
          </tbody>
        </table>
      </div>

      {/* CHÂN cố định */}
      <div className="shrink-0 border-t border-border bg-card px-4 py-2 flex items-center gap-3 flex-wrap">
        <label className="inline-flex items-center gap-2 text-[13px] font-medium cursor-pointer">
          <input type="checkbox" checked={!!data && soChon > 0 && soChon === data.se_tao_moi} onChange={(e) => tickAll(e.target.checked)} /> Chọn tất cả sẵn sàng
        </label>
        <button onClick={bdSync} disabled={running || soChon === 0} className="inline-flex items-center gap-2 h-9 px-5 rounded-lg bg-sync text-white font-semibold text-[13px] hover:brightness-110 disabled:opacity-50">
          <Icon name="refresh" className={"w-4 h-4 " + (running ? "animate-spin" : "")} /> SYNC {soChon} học viên
        </button>
        <span className="text-[12px] text-muted-foreground tabular-nums">đã chọn {soChon}</span>
        {chayPct !== null && (
          <div className="flex items-center gap-2 min-w-[240px]">
            <div className="flex-1 h-2 rounded-full bg-muted overflow-hidden"><div className="h-full bg-sync transition-all" style={{ width: `${chayPct}%` }} /></div>
            <span className="text-[12px] text-muted-foreground tabular-nums whitespace-nowrap max-w-[220px] truncate">{chayTxt}</span>
          </div>
        )}
        {data && (
          <div className="ml-auto">
            <PhanTrang total={loc.length} trang={page} coTrang={pageSize} onTrang={setPage} onCoTrang={(c) => { setPageSize(c); setPage(0); }} />
          </div>
        )}
      </div>

      {(err || tongKet) && (
        <div className="shrink-0 px-4 pb-2">
          {err && <div className="flex items-center gap-2 text-[13px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2"><Icon name="warn" className="w-4 h-4" /> {err}</div>}
          {tongKet && !err && <div className="flex items-center gap-2 text-[13px] text-success bg-success/10 border border-success/30 rounded-lg px-3 py-2"><Icon name="check" className="w-4 h-4" sw={3} /> {tongKet}</div>}
        </div>
      )}
    </section>
  );
}

function Dong({ h, stt, ticked, onTick, tt, onXem }: {
  h: SyncHV; stt: number; ticked: boolean; onTick: (cc: string, v: boolean) => void; tt?: RowTT;
  onXem: (maDkDich: string) => void;
}) {
  const locked = h.da_co_dich || h.thieu_cccd;
  const mono = { fontFamily: "ui-monospace,Consolas,monospace", fontSize: "12px" } as const;
  const rowbg = h.da_co_dich ? "bg-warning/10" : h.thieu_cccd ? "bg-destructive/5" : stt % 2 ? "bg-background/40" : "";
  const dim = locked ? "text-muted-foreground" : "";
  // Trạng thái: ưu tiên realtime (SSE) → tĩnh
  let st = <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-success bg-success/10 border border-success/40 rounded-full px-2 py-0.5">Sẵn sàng</span>;
  if (tt) {
    const cls = tt.mau === "ok" ? "text-sync bg-sync-soft border-sync-border" : tt.mau === "skip" ? "text-warning bg-warning/10 border-warning/40" : "text-destructive bg-destructive/10 border-destructive/40";
    st = <span className={"inline-flex items-center gap-1 text-[11px] font-semibold border rounded-full px-2 py-0.5 " + cls}>{tt.trang_thai}</span>;
  } else if (h.thieu_cccd) {
    st = <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-destructive bg-destructive/10 border border-destructive/40 rounded-full px-2 py-0.5">Thiếu CCCD</span>;
  } else if (h.da_co_dich) {
    st = <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-warning bg-warning/10 border border-warning/40 rounded-full px-2 py-0.5">Đã có ở đích</span>;
  } else if (h.trung_cccd_nguon) {
    st = <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-success bg-success/10 border border-success/40 rounded-full px-2 py-0.5">Sẵn sàng · trùng CCCD?</span>;
  }
  // Chữ cái đầu của tên gọi (từ cuối — cách gọi tên người Việt) làm avatar nhỏ,
  // giúp quét danh sách dễ hơn mà không chiếm thêm cột.
  const chuDau = ((h.ho_ten || "").trim().split(/\s+/).pop() || "?").charAt(0).toUpperCase();
  return (
    <tr className={"border-b border-border/70 " + rowbg + " " + dim}>
      <td className="px-2 py-1.5 text-center">
        <input type="checkbox" checked={ticked} disabled={locked} className="disabled:opacity-40 accent-sync" onChange={(e) => onTick(h.so_cmt, e.target.checked)} />
      </td>
      <td className="px-2 py-1.5 text-center tabular-nums text-muted-foreground">{stt}</td>
      <td className="px-2 py-1.5">
        <div className="flex items-center gap-2">
          <span className={"inline-grid place-items-center w-[22px] h-[22px] rounded-md text-[11px] font-bold shrink-0 " + (locked ? "bg-muted text-muted-foreground/70" : "bg-sync-soft text-sync")}>{chuDau}</span>
          <span className="font-semibold text-foreground/90 whitespace-nowrap">{h.ho_ten}</span>
        </div>
      </td>
      <td className="px-2 py-1.5 tracking-wide" style={mono}>{h.so_cmt || "—"}</td>
      <td className="px-2 py-1.5 text-center">{h.hang_gplx}</td>
      <td className="px-2 py-1.5 whitespace-nowrap text-muted-foreground" style={mono}>{h.ma_dk_nguon}</td>
      <td className="px-2 py-1.5 tabular-nums">{isoVN(h.ngay_hs_nguon)}</td>
      <td className="px-2 py-1.5 whitespace-nowrap text-muted-foreground" style={mono}>
        {h.da_co_dich && h.ma_dk_dich ? (
          <button
            type="button"
            onClick={() => onXem(h.ma_dk_dich!)}
            title="Xem chi tiết học viên ở Tra cứu CDB"
            className="inline-flex items-center gap-1 text-sync hover:underline"
          >
            {h.ma_dk_dich} <Icon name="search" className="w-3 h-3" />
          </button>
        ) : (h.ma_dk_dich ?? "–")}
      </td>
      <td className="px-2 py-1.5 tabular-nums">{isoVN(h.ngay_hs_dich)}</td>
      <td className="px-2 py-1.5 text-center tabular-nums">{h.so_hs_dich ?? "–"}</td>
      <td className="px-2 py-1.5">{st}</td>
    </tr>
  );
}
