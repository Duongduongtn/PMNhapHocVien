import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Icon } from "../../components/Icon";
import AnhAvatar from "../../components/AnhAvatar";
import AnhModal from "../../components/AnhModal";
import { PhanTrang } from "../../components/PhanTrang";
import { useConfigDrawer } from "../../lib/configDrawer";
import { boDau, ymdToVN } from "../../lib/format";
import {
  getSyncTargets,
  traCuuKhoaCDB,
  dsHoSoCDB,
  khoaCuaMaDkCDB,
  taiAnhCDB,
  taiAnhThumbCDB,
  napAnhCDB,
  type KhoaCDB,
  type HoSoRowCDB,
  type KetQuaAnh,
} from "../../lib/api";

// TCB-01 — Tra cứu CDB đích. Song song QLY-01 (Tra cứu DB bên Nạp) nhưng mọi truy vấn trỏ CSDL
// ĐÍCH (GPLX_CDB_CSDT) qua các endpoint /local/sync/tra-cuu/*. CHỈ ĐỌC ở task này — thay ảnh /
// sửa nhân thân / xóa-đổi khóa là TCB-02/03/04 (task 64-66). KHÔNG đụng TraCuuDB.tsx (tránh vỡ QLY-01).
function gioiTinhVN(g: string | null): string {
  return g === "M" ? "Nam" : g === "F" ? "Nữ" : "—";
}

function Bc1Chip() {
  return (
    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-warning bg-warning/10 border border-warning/30 rounded-full px-2 py-0.5 whitespace-nowrap">
      <Icon name="warn" className="w-3 h-3" /> Đã BC1
    </span>
  );
}
function DkkhChip() {
  return (
    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-sync bg-sync-soft border border-sync-border rounded-full px-2 py-0.5 whitespace-nowrap">
      <Icon name="check" className="w-3 h-3" sw={3} /> Đã kết xuất DKKH
    </span>
  );
}

export default function TraCuuCDB() {
  const { open: moCauHinh } = useConfigDrawer();
  const [sp, setSp] = useSearchParams();

  const [targetKey, setTargetKey] = useState<string | null>(null);
  const [targetName, setTargetName] = useState("");
  const [chuaChonDich, setChuaChonDich] = useState(false);

  const [q, setQ] = useState("");
  const [khoaList, setKhoaList] = useState<KhoaCDB[] | null>(null);
  const [khoa, setKhoa] = useState<KhoaCDB | null>(null);
  const [hoSo, setHoSo] = useState<HoSoRowCDB[] | null>(null);
  const [qHv, setQHv] = useState("");
  const [sel, setSel] = useState<HoSoRowCDB | null>(null);
  const [loadingKhoa, setLoadingKhoa] = useState(false);
  const [loadingHv, setLoadingHv] = useState(false);
  const [err, setErr] = useState("");

  // HV cần tô sáng khi mở từ "Xem chi tiết HV" (Bàn đồng bộ) — theo MaDK đích.
  const [noiBat, setNoiBat] = useState<string[]>([]);
  const noiBatSet = new Set(noiBat);

  // Ảnh lớn ở modal chi tiết (fetch kèm session header → object URL; revoke khi đổi/đóng).
  const [anhXem, setAnhXem] = useState<KetQuaAnh | null>(null);
  const [anhXemBusy, setAnhXemBusy] = useState(false);

  // TCB-02 — thay ảnh. anhVer: cache-bust sau khi ghi đè (ảnh dùng chung URL theo MaDK).
  const [anhModal, setAnhModal] = useState(false);
  const [anhSeed, setAnhSeed] = useState<string | null>(null);
  const [anhBusy, setAnhBusy] = useState(false);
  const [anhErr, setAnhErr] = useState("");
  const [anhVer, setAnhVer] = useState(0);
  const [okMsg, setOkMsg] = useState("");

  const [trang, setTrang] = useState(0);
  const [coTrang, setCoTrang] = useState(20);

  // CSDL đích đang chọn (cấu hình ⚙ header). Chưa có → báo + lối tắt mở Cấu hình.
  useEffect(() => {
    let huy = false;
    getSyncTargets()
      .then((d) => {
        if (huy) return;
        const t = d.targets.find((x) => x.key === d.selected) ?? d.targets[0];
        if (!t) { setChuaChonDich(true); return; }
        setTargetKey(t.key);
        setTargetName(t.name);
      })
      .catch(() => { if (!huy) setChuaChonDich(true); });
    return () => { huy = true; };
  }, []);

  async function chonKhoa(k: KhoaCDB, tk = targetKey) {
    setKhoa(k);
    setErr("");
    setHoSo(null);
    setQHv("");
    setLoadingHv(true);
    try {
      setHoSo(await dsHoSoCDB(k.ma_kh, tk ?? undefined));
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Không tải được danh sách học viên.");
    } finally {
      setLoadingHv(false);
    }
  }

  async function timKhoa() {
    if (!targetKey) return;
    setErr("");
    setLoadingKhoa(true);
    setKhoa(null);
    setHoSo(null);
    setNoiBat([]);
    try {
      setKhoaList(await traCuuKhoaCDB(q, targetKey));
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Không tìm được khóa.");
    } finally {
      setLoadingKhoa(false);
    }
  }

  // "Xem chi tiết HV" từ Bàn đồng bộ: ?ma_dk=<MaDK đích> → tra khóa chứa HV → mở + tô sáng.
  const maDkParam = sp.get("ma_dk");
  useEffect(() => {
    if (!targetKey || !maDkParam) return;
    let huy = false;
    (async () => {
      setErr("");
      setLoadingKhoa(true);
      try {
        const k = await khoaCuaMaDkCDB(maDkParam, targetKey);
        if (huy) return;
        setQ(k.ma_kh);
        setNoiBat([maDkParam]);
        await chonKhoa(k, targetKey);
      } catch (e) {
        if (!huy) setErr(e instanceof Error ? e.message : "Không mở được học viên từ Bàn đồng bộ.");
      } finally {
        if (!huy) setLoadingKhoa(false);
      }
    })();
    return () => { huy = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [targetKey, maDkParam]);

  // Tải ảnh lớn khi mở chi tiết. anhVer đổi → refetch ảnh mới sau khi thay (tránh bộ đệm).
  useEffect(() => {
    setAnhXem(null);
    if (!sel || !sel.co_anh) return;
    let huy = false;
    let obj: string | null = null;
    setAnhXemBusy(true);
    void taiAnhCDB(sel.ma_dk, targetKey ?? undefined, anhVer)
      .then((kq) => {
        if (huy) return;
        if ("url" in kq) obj = kq.url;
        setAnhXem(kq);
      })
      .finally(() => { if (!huy) setAnhXemBusy(false); });
    return () => { huy = true; if (obj) URL.revokeObjectURL(obj); };
  }, [sel, targetKey, anhVer]);

  // Mở AnhModal để thay ảnh (TCB-02). Ảnh cũ còn → nạp sẵn làm ảnh gốc để chỉnh tiếp;
  // mất/hỏng → mở chế độ chọn-file. Khi mở từ danh sách, reset lỗi.
  function moThayAnh() {
    if (!sel) return;
    setAnhErr("");
    setAnhSeed(anhXem && "url" in anhXem ? anhXem.url : null);
    setAnhModal(true);
  }

  async function thayAnh(jp2B64: string) {
    if (!sel) return;
    const maDk = sel.ma_dk;
    setAnhModal(false);
    setAnhErr("");
    setAnhBusy(true);
    try {
      await napAnhCDB(maDk, jp2B64, targetKey ?? undefined);
      setSel((prev) => (prev && prev.ma_dk === maDk ? { ...prev, co_anh: true } : prev));
      setAnhVer((v) => v + 1); // refetch ảnh mới (chi tiết + avatar lưới)
      if (khoa) setHoSo(await dsHoSoCDB(khoa.ma_kh, targetKey ?? undefined));
      setOkMsg("Đã thay ảnh — ảnh đổi ở cả bản Nạp và CDB (dùng chung file). Bản gốc lưu _BACKUP.");
      setTimeout(() => setOkMsg(""), 4000);
    } catch (e) {
      setAnhErr(e instanceof Error ? e.message : "Thay ảnh không thành công.");
    } finally {
      setAnhBusy(false);
    }
  }

  const rows = (hoSo ?? []).filter((h) => {
    const t = qHv.trim();
    if (!t) return true;
    return boDau(h.ho_ten ?? "").includes(boDau(t)) || (h.so_cccd ?? "").includes(t);
  });
  const rowsSapXep = noiBatSet.size > 0
    ? [...rows].sort((a, b) => (noiBatSet.has(b.ma_dk) ? 1 : 0) - (noiBatSet.has(a.ma_dk) ? 1 : 0))
    : rows;
  const soNoiBat = noiBatSet.size > 0 ? (hoSo ?? []).filter((h) => noiBatSet.has(h.ma_dk)).length : 0;
  useEffect(() => { setTrang(0); }, [khoa, qHv, coTrang]);
  const rowsTrang = rowsSapXep.slice(trang * coTrang, (trang + 1) * coTrang);

  function quayLaiDsKhoa() {
    setKhoa(null);
    setNoiBat([]);
    if (maDkParam) setSp({}, { replace: true }); // bỏ ?ma_dk để không mở lại tự động
  }

  if (chuaChonDich) {
    return (
      <div className="p-4">
        <div className="max-w-md mx-auto mt-10 text-center rounded-xl border border-border bg-card p-6">
          <div className="w-12 h-12 mx-auto rounded-full bg-sync-soft text-sync flex items-center justify-center mb-3">
            <Icon name="db" className="w-6 h-6" />
          </div>
          <h3 className="font-bold text-sm">Chưa chọn CSDL đích</h3>
          <p className="text-[13px] text-muted-foreground mt-1.5">
            Tra cứu CDB đọc dữ liệu học viên trên CSDL đích. Hãy chọn (hoặc thêm) một CSDL đích trong phần Cấu hình.
          </p>
          <button
            type="button"
            onClick={moCauHinh}
            className="mt-4 h-10 px-5 rounded-lg bg-sync text-white text-sm font-semibold inline-flex items-center gap-2 hover:brightness-110 transition-all shadow-sm"
          >
            <Icon name="settings" className="w-4 h-4" /> Mở Cấu hình
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4">
      {targetName && (
        <div className="mb-3 inline-flex items-center gap-1.5 text-[12px] text-sync bg-sync-soft border border-sync-border rounded-lg px-2.5 py-1">
          <Icon name="db" className="w-3.5 h-3.5" /> CSDL đích: <b>{targetName}</b>
        </div>
      )}

      {/* Tìm khóa */}
      <div className="flex items-end gap-2 flex-wrap">
        <div className="flex-1 min-w-[220px]">
          <label className="field-label">Tìm khóa ở CDB đích (tên hoặc mã — mọi khóa, kể cả đã BC1)</label>
          <div className="relative mt-1">
            <Icon name="search" className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              className="field-input pl-9"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") void timKhoa(); }}
              placeholder="VD: B-K149 hoặc 75032K26B010"
            />
          </div>
        </div>
        <button
          type="button"
          onClick={() => void timKhoa()}
          disabled={loadingKhoa || !targetKey}
          className="h-10 px-4 rounded-lg bg-sync text-white font-semibold text-sm inline-flex items-center gap-2 hover:brightness-110 transition-all shadow-sm disabled:opacity-60"
        >
          <Icon name={loadingKhoa ? "refresh" : "search"} className={"w-4 h-4" + (loadingKhoa ? " animate-spin" : "")} /> Tìm khóa
        </button>
      </div>

      {okMsg && (
        <div className="mt-3 flex items-center gap-2 text-[13px] text-success bg-success/10 border border-success/30 rounded-lg px-3 py-2">
          <Icon name="check" className="w-4 h-4 shrink-0" sw={3} /> {okMsg}
        </div>
      )}
      {err && (
        <div className="mt-3 flex items-center gap-2 text-[13px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2">
          <Icon name="warn" className="w-4 h-4 shrink-0" /> {err}
        </div>
      )}

      {/* Kết quả khóa */}
      {khoaList && !khoa && (
        <div className="mt-4">
          {khoaList.length === 0 ? (
            <p className="text-[13px] text-muted-foreground px-1">Không tìm thấy khóa khớp ở CSDL đích.</p>
          ) : (
            <div className="border border-border rounded-xl divide-y divide-border overflow-hidden">
              {khoaList.map((k) => (
                <button
                  key={k.ma_kh}
                  type="button"
                  onClick={() => void chonKhoa(k)}
                  className="w-full text-left flex items-center gap-3 px-4 py-2.5 hover:bg-muted/60 transition-colors"
                >
                  <div className="min-w-0 flex-1">
                    <div className="font-semibold text-[14px] truncate">{k.ten_kh || "(không tên)"}</div>
                    <div className="text-[12px] text-muted-foreground tabular-nums">{k.ma_kh} · hạng {k.hang_gplx}</div>
                  </div>
                  {k.dkkh && <DkkhChip />}
                  {k.bc1 && <Bc1Chip />}
                  <Icon name="chevronRight" className="w-4 h-4 text-muted-foreground shrink-0" />
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Lưới học viên trong khóa đã chọn */}
      {khoa && (
        <div className="mt-4">
          <div className="flex items-center gap-2 flex-wrap mb-3">
            <button type="button" onClick={quayLaiDsKhoa} className="inline-flex items-center gap-1 text-[13px] text-sync font-medium hover:underline">
              <Icon name="chevronLeft" className="w-4 h-4" /> Danh sách khóa
            </button>
            <span className="text-[13px] font-bold">{khoa.ten_kh}</span>
            <span className="text-[12px] text-muted-foreground tabular-nums">{khoa.ma_kh} · hạng {khoa.hang_gplx}</span>
            {khoa.dkkh && <DkkhChip />}
            {khoa.bc1 && <Bc1Chip />}
          </div>

          {soNoiBat > 0 && (
            <div className="mb-3 flex items-center gap-2 text-[13px] text-sync bg-sync-soft border border-sync-border rounded-lg px-3 py-2">
              <Icon name="check" className="w-4 h-4 shrink-0" sw={3} /> Đang xem <b className="mx-1">{soNoiBat}</b> học viên mở từ Bàn đồng bộ — tô sáng ở đầu danh sách.
            </div>
          )}

          {/* Thống kê đầu khóa (client, trên lưới đã tải) */}
          {hoSo && (
            <div className="flex items-center gap-2 flex-wrap mb-3 text-[12px]">
              <span className="inline-flex items-center gap-1.5 rounded-lg bg-muted px-2.5 py-1 font-medium">
                <Icon name="user" className="w-3.5 h-3.5 text-muted-foreground" /> Tổng <b className="tabular-nums">{hoSo.length}</b> HV
              </span>
              <span className="inline-flex items-center gap-1.5 rounded-lg bg-warning/10 text-warning px-2.5 py-1 font-medium">
                <Icon name="imageOff" className="w-3.5 h-3.5" /> Thiếu ảnh <b className="tabular-nums">{hoSo.filter((h) => !h.co_anh).length}</b>
              </span>
            </div>
          )}

          <div className="flex items-center gap-2 flex-wrap mb-2">
            <div className="relative max-w-sm flex-1 min-w-[220px]">
              <Icon name="search" className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <input
                className="field-input pl-9"
                value={qHv}
                onChange={(e) => setQHv(e.target.value)}
                placeholder="Tìm trong khóa: tên (không dấu được) hoặc CCCD"
              />
            </div>
          </div>

          {loadingHv ? (
            <div className="px-4 py-8 text-center text-sm text-muted-foreground">
              <Icon name="refresh" className="w-4 h-4 animate-spin inline mr-1" /> Đang tải học viên…
            </div>
          ) : (
            <div className="border border-border rounded-xl overflow-hidden">
              <table className="w-full text-[13px]">
                <thead>
                  <tr className="bg-muted text-muted-foreground text-left">
                    <th className="px-2 py-2 font-semibold w-12">Ảnh</th>
                    <th className="px-3 py-2 font-semibold">Số HS</th>
                    <th className="px-3 py-2 font-semibold">Họ và tên</th>
                    <th className="px-3 py-2 font-semibold">Giới tính</th>
                    <th className="px-3 py-2 font-semibold">Ngày sinh</th>
                    <th className="px-3 py-2 font-semibold">Số CCCD</th>
                  </tr>
                </thead>
                <tbody>
                  {rowsTrang.map((h) => (
                    <tr key={h.ma_dk} onClick={() => setSel(h)} className={"border-t border-border cursor-pointer transition-colors " + (noiBatSet.has(h.ma_dk) ? "bg-sync-soft hover:brightness-95" : "hover:bg-muted/60")}>
                      <td className="px-2 py-1.5"><AnhAvatar coAnh={h.co_anh} ver={anhVer} tai={(v) => taiAnhThumbCDB(h.ma_dk, targetKey ?? undefined, v)} /></td>
                      <td className="px-3 py-2 tabular-nums">{h.so_ho_so || "—"}</td>
                      <td className="px-3 py-2 font-semibold">{h.ho_ten || "(chưa có tên)"}</td>
                      <td className="px-3 py-2">{gioiTinhVN(h.gioi_tinh)}</td>
                      <td className="px-3 py-2 tabular-nums">{ymdToVN(h.ngay_sinh)}</td>
                      <td className="px-3 py-2 tabular-nums">{h.so_cccd || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!rows.length && (
                <div className="px-4 py-8 text-center text-sm text-muted-foreground">
                  {qHv.trim() ? "Không tìm thấy học viên khớp." : "Khóa chưa có học viên."}
                </div>
              )}
            </div>
          )}
          {hoSo && (
            <>
              <PhanTrang total={rows.length} trang={trang} coTrang={coTrang} onTrang={setTrang} onCoTrang={setCoTrang} />
              <p className="text-[12px] text-muted-foreground mt-1">{rows.length}/{hoSo.length} học viên trong khóa</p>
            </>
          )}
        </div>
      )}

      {/* Chi tiết (chỉ xem) */}
      {sel && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={(e) => { if (e.target === e.currentTarget) setSel(null); }}>
          <div className="bg-card w-full max-w-md rounded-xl shadow-2xl max-h-[90vh] flex flex-col overflow-hidden">
            <div className="flex items-center justify-between px-5 py-3 border-b border-border">
              <h3 className="font-bold text-sm">Chi tiết học viên (CDB đích)</h3>
              <button onClick={() => setSel(null)} aria-label="Đóng" className="w-8 h-8 rounded-lg hover:bg-muted flex items-center justify-center transition-colors">
                <Icon name="x" className="w-5 h-5" />
              </button>
            </div>
            <div className="p-5 overflow-y-auto">
              <div className="mb-4 flex flex-col items-center">
                <button
                  type="button"
                  onClick={moThayAnh}
                  disabled={!sel.co_anh || anhBusy}
                  title={sel.co_anh ? "Bấm để thay ảnh" : "Học viên chưa có ảnh ở CDB — không thay được"}
                  className="group relative w-32 h-[170px] rounded-lg border border-border overflow-hidden bg-muted flex items-center justify-center disabled:cursor-not-allowed"
                >
                  {!sel.co_anh ? (
                    <div className="flex flex-col items-center gap-1 text-muted-foreground">
                      <Icon name="user" className="w-10 h-10" />
                      <span className="text-[11px]">Thiếu ảnh</span>
                    </div>
                  ) : anhBusy ? (
                    <Icon name="refresh" className="w-6 h-6 text-primary animate-spin" />
                  ) : anhXemBusy ? (
                    <Icon name="refresh" className="w-6 h-6 text-muted-foreground animate-spin" />
                  ) : anhXem && "url" in anhXem ? (
                    <img src={anhXem.url} alt="Ảnh chân dung" className="w-full h-full object-cover" />
                  ) : (
                    <div className="flex flex-col items-center gap-1 text-destructive px-2 text-center">
                      <Icon name="imageOff" className="w-10 h-10" />
                      <span className="text-[11px]">{anhXem && "loi" in anhXem && anhXem.loi === "hong" ? "Ảnh hỏng" : "Mất file"}</span>
                    </div>
                  )}
                  {sel.co_anh && (
                    <span className="absolute inset-x-0 bottom-0 bg-black/55 text-white text-[10px] py-0.5 flex items-center justify-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Icon name="edit" className="w-3 h-3" /> Thay ảnh
                    </span>
                  )}
                </button>
                {sel.co_anh && anhXem && "loi" in anhXem && (
                  <p className="mt-2 text-[12px] text-destructive flex items-start gap-1 text-center max-w-[260px]">
                    <Icon name="warn" className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                    {anhXem.loi === "hong"
                      ? "Ảnh trong hồ sơ bị hỏng, không đọc được."
                      : "DB có đường dẫn nhưng không tìm thấy file ảnh trên ổ."}
                  </p>
                )}
                {sel.duong_dan_anh && (
                  <p className="mt-1.5 text-[11px] text-muted-foreground break-all text-center max-w-[300px]" title={sel.duong_dan_anh}>
                    {sel.duong_dan_anh}
                  </p>
                )}
                {/* Thay ảnh được phép kể cả khi DKKH/BC1 — chỉ cảnh báo (ảnh là sửa chất lượng) */}
                {sel.co_anh && (khoa?.dkkh || khoa?.bc1) && (
                  <p className="mt-2 text-[11px] text-warning flex items-start gap-1 text-center max-w-[280px]">
                    <Icon name="warn" className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                    Khóa đã {khoa?.bc1 ? "lập Báo cáo 1" : "kết xuất DKKH"} — vẫn thay được ảnh. Ảnh dùng chung nên đổi cả ở bản Nạp.
                  </p>
                )}
                {anhErr && (
                  <p className="mt-2 text-[12px] text-destructive flex items-start gap-1 text-center max-w-[280px]">
                    <Icon name="warn" className="w-3.5 h-3.5 shrink-0 mt-0.5" /> {anhErr}
                  </p>
                )}
              </div>
              <div className="font-bold text-[15px]">{sel.ho_ten || "(chưa có tên)"}</div>
              <div className="text-[12px] text-muted-foreground mt-0.5">Số hồ sơ {sel.so_ho_so || "—"} · {gioiTinhVN(sel.gioi_tinh)}</div>
              <div className="mt-3 space-y-2">
                {(
                  [
                    ["Số CMND cũ", sel.so_cmnd_cu || "—"],
                    ["Số căn cước", sel.so_cccd || "—"],
                    ["Ngày sinh", ymdToVN(sel.ngay_sinh)],
                    ["Ngày cấp", ymdToVN(sel.ngay_cap)],
                    ["Nơi cấp", sel.noi_cap_ten || sel.noi_cap_ma || "—"],
                    ["Địa chỉ thường trú", [sel.noi_tt, sel.hktt].filter(Boolean).join(", ") || "—"],
                    ["Địa chỉ cư trú", [sel.noi_ct, sel.hkct].filter(Boolean).join(", ") || "(theo thường trú)"],
                    ["Hạng", sel.ma_loai_hs === 1 ? "Mô tô" : sel.ma_loai_hs === 2 ? "Ô tô" : "—"],
                    ["Mã đăng ký (MaDK)", sel.ma_dk],
                    ["Trạng thái xử lý", sel.tt_xuly || "—"],
                  ] as [string, string][]
                ).map(([k, v]) => (
                  <div key={k} className="flex justify-between gap-3 text-[13px] border-b border-border pb-2 last:border-0">
                    <span className="text-muted-foreground shrink-0">{k}</span>
                    <span className="font-medium text-right break-words">{v}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TCB-02 — AnhModal thay ảnh (tái dùng Y NGUYÊN của Nạp: 3:4 + zoom/xoay + đổi nền) */}
      {anhModal && (
        <AnhModal
          anhBanDau={anhSeed}
          anhGoc={anhSeed}
          onDong={() => { setAnhModal(false); setAnhSeed(null); }}
          onXong={(b64) => void thayAnh(b64)}
        />
      )}
    </div>
  );
}
