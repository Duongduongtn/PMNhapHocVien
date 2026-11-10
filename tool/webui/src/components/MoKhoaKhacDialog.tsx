import { useEffect, useMemo, useState } from "react";
import { Icon } from "./Icon";
import AnhModal from "./AnhModal";
import {
  hoSoDayDu,
  getKhoaHoc,
  getGiayTo,
  kiemTrungCccd,
  napHoSo,
  type HoSoDayDu,
  type KhoaHoc,
  type GiayTo,
  type LoaiXe,
  type NapIn,
} from "../lib/api";

// QLY-06 — mở hồ sơ ở khóa khác (khác hạng) cho HV đã có: điền sẵn thông tin cá nhân từ bản
// ghi cũ → chọn khóa đích (cấp mới, chưa BC1) → nạp MỚI qua SP gộp (@p_MaDK=NULL → MaDK mới),
// đăng ký cũ giữ nguyên. Chặn trùng trong cùng khóa đích (NAP-06). KHÔNG nâng hạng.
export default function MoKhoaKhacDialog({
  maDk,
  hoTen,
  onDong,
  onXong,
}: {
  maDk: string;
  hoTen: string;
  onDong: () => void;
  onXong: (msg: string) => void;
}) {
  const [dayDu, setDayDu] = useState<HoSoDayDu | null>(null);
  const [loadErr, setLoadErr] = useState("");
  const [loai, setLoai] = useState<LoaiXe>("oto");
  const [dsKhoa, setDsKhoa] = useState<KhoaHoc[]>([]);
  const [maKh, setMaKh] = useState("");
  const [giayTo, setGiayTo] = useState<GiayTo[]>([]);
  const [tick, setTick] = useState<Set<number>>(new Set());
  const [anhJp2, setAnhJp2] = useState<string | null>(null);
  const [anhModal, setAnhModal] = useState(false);
  const [trung, setTrung] = useState<{ trung: boolean; so_ho_so: string | null }>({ trung: false, so_ho_so: null });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const khoa = useMemo(() => dsKhoa.find((k) => k.ma_kh === maKh) ?? null, [dsKhoa, maKh]);

  // Đọc đủ dữ liệu cá nhân để điền sẵn
  useEffect(() => {
    let huy = false;
    hoSoDayDu(maDk)
      .then((d) => !huy && setDayDu(d))
      .catch((e) => !huy && setLoadErr(e instanceof Error ? e.message : "Không đọc được dữ liệu học viên."));
    return () => { huy = true; };
  }, [maDk]);

  // Danh sách khóa đích (cấp mới, chưa BC1) theo loại xe
  useEffect(() => {
    let huy = false;
    setMaKh("");
    getKhoaHoc(loai)
      .then((ds) => !huy && setDsKhoa(ds))
      .catch(() => !huy && setDsKhoa([]));
    return () => { huy = true; };
  }, [loai]);

  // Giấy tờ bắt buộc theo khóa đích → mặc định tick hết
  useEffect(() => {
    if (!khoa) { setGiayTo([]); setTick(new Set()); return; }
    let huy = false;
    getGiayTo(khoa.ma_loai_hs, khoa.hang_dt || khoa.hang_gplx, khoa.hang_gplx)
      .then((gs) => { if (!huy) { setGiayTo(gs); setTick(new Set(gs.map((g) => g.ma_gt))); } })
      .catch(() => { if (!huy) { setGiayTo([]); setTick(new Set()); } });
    return () => { huy = true; };
  }, [maKh, khoa?.ma_loai_hs, khoa?.hang_dt]);

  // Cảnh báo trùng trong cùng khóa đích (NAP-06)
  useEffect(() => {
    if (!khoa || !dayDu?.so_cmt) { setTrung({ trung: false, so_ho_so: null }); return; }
    let huy = false;
    kiemTrungCccd(khoa.ma_kh, dayDu.so_cmt).then((kq) => !huy && setTrung(kq));
    return () => { huy = true; };
  }, [maKh, dayDu?.so_cmt]);

  function toggleTick(ma: number) {
    setTick((cu) => {
      const s = new Set(cu);
      if (s.has(ma)) s.delete(ma); else s.add(ma);
      return s;
    });
  }

  async function nap() {
    if (!dayDu || !khoa) return;
    if (trung.trung) { setErr(`Học viên đã có hồ sơ trong khóa này (Số hồ sơ ${trung.so_ho_so ?? "—"}) — không tạo thêm.`); return; }
    setErr("");
    setBusy(true);
    const body: NapIn = {
      uuid: crypto.randomUUID(),
      ma_khoa_hoc: khoa.ma_kh,
      ho_ten: dayDu.ho_ten,
      ngay_sinh: dayDu.ngay_sinh,
      gioi_tinh: dayDu.gioi_tinh,
      so_cmt: dayDu.so_cmt,
      ngay_cap_cmt: dayDu.ngay_cap_cmt || undefined,
      noi_cap_cmt: dayDu.noi_cap_cmt || undefined,
      chi_tiet_tt: dayDu.noi_tt || undefined,
      noi_tt_ma_dvhc: dayDu.noi_tt_ma_dvhc,
      noi_tt_ma_dvql: dayDu.noi_tt_ma_dvql,
      giay_to_tick: [...tick],
      anh_jp2_b64: anhJp2,
    };
    try {
      const kq = await napHoSo(body);
      onXong(`Đã mở hồ sơ ở khóa ${khoa.ten_kh} — Số hồ sơ ${kq.so_ho_so}.`);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Nạp không thành công.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={(e) => { if (e.target === e.currentTarget && !busy) onDong(); }}>
      <div className="bg-card w-full max-w-lg rounded-xl shadow-2xl max-h-[90vh] flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3 border-b border-border">
          <h3 className="font-bold text-sm">Mở hồ sơ khóa khác — {hoTen}</h3>
          <button onClick={onDong} aria-label="Đóng" className="w-8 h-8 rounded-lg hover:bg-muted flex items-center justify-center transition-colors">
            <Icon name="x" className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5 overflow-y-auto space-y-4">
          {loadErr && (
            <div className="flex items-center gap-2 text-[13px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2">
              <Icon name="warn" className="w-4 h-4 shrink-0" /> {loadErr}
            </div>
          )}
          {!dayDu && !loadErr && (
            <p className="text-[13px] text-muted-foreground flex items-center gap-1"><Icon name="refresh" className="w-4 h-4 animate-spin" /> Đang đọc dữ liệu học viên…</p>
          )}

          {dayDu && (
            <>
              {/* Thông tin cá nhân điền sẵn (chỉ xem) */}
              <div className="rounded-lg border border-border bg-muted/40 p-3 text-[13px] space-y-1">
                <div className="font-semibold text-[14px]">{dayDu.ho_ten}</div>
                <div className="text-muted-foreground">
                  CCCD {dayDu.so_cmt || "—"} · {dayDu.gioi_tinh === "M" ? "Nam" : dayDu.gioi_tinh === "F" ? "Nữ" : "—"}
                </div>
                <div className="text-muted-foreground">Thường trú: {dayDu.noi_tt || "—"}</div>
                <p className="text-[11px] text-muted-foreground pt-1">Thông tin cá nhân lấy từ hồ sơ cũ (chung số căn cước). Nạp mới tạo hồ sơ riêng ở khóa đích, không đụng hồ sơ cũ.</p>
              </div>

              {/* Chọn loại xe + khóa đích */}
              <div>
                <label className="field-label">Loại khóa đích</label>
                <div className="inline-flex rounded-lg bg-muted p-1 mt-1">
                  {([["oto", "Ô tô"], ["moto", "Mô tô"]] as const).map(([k, label]) => (
                    <button key={k} type="button" onClick={() => setLoai(k)}
                      className={"px-4 py-1.5 text-sm rounded-md transition-colors " + (loai === k ? "bg-primary text-primary-foreground font-semibold" : "text-muted-foreground font-medium hover:text-foreground")}>
                      {label}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="field-label">Khóa đích (chưa lập Báo cáo 1)</label>
                <select className="field-input mt-1" value={maKh} onChange={(e) => setMaKh(e.target.value)}>
                  <option value="">— Chọn khóa —</option>
                  {dsKhoa.map((k) => (
                    <option key={k.ma_kh} value={k.ma_kh}>{k.ma_kh} — {k.ten_kh} (hạng {k.hang_gplx})</option>
                  ))}
                </select>
                {dsKhoa.length === 0 && <p className="text-[12px] text-muted-foreground mt-1">Không có khóa {loai === "oto" ? "ô tô" : "mô tô"} nào chưa BC1.</p>}
              </div>

              {/* Cảnh báo trùng trong khóa đích */}
              {trung.trung && (
                <div className="flex items-start gap-2 text-[13px] text-warning bg-warning/10 border border-warning/30 rounded-lg px-3 py-2">
                  <Icon name="warn" className="w-4 h-4 shrink-0 mt-0.5" />
                  Học viên <b>đã có hồ sơ</b> trong khóa này (Số hồ sơ {trung.so_ho_so ?? "—"}) — không tạo thêm được.
                </div>
              )}

              {/* Giấy tờ nộp */}
              {khoa && giayTo.length > 0 && (
                <div>
                  <label className="field-label">Giấy tờ nộp</label>
                  <div className="mt-1 rounded-lg border border-border divide-y divide-border">
                    {giayTo.map((g) => (
                      <label key={g.ma_gt} className="flex items-center gap-2 px-3 py-2 text-[13px] cursor-pointer hover:bg-muted/50">
                        <input type="checkbox" className="accent-primary" checked={tick.has(g.ma_gt)} onChange={() => toggleTick(g.ma_gt)} />
                        {g.ten_gt}
                      </label>
                    ))}
                  </div>
                </div>
              )}

              {/* Ảnh (tùy chọn) */}
              {khoa && (
                <div className="flex items-center gap-2">
                  <button type="button" onClick={() => setAnhModal(true)}
                    className="h-9 px-3 rounded-lg border border-border text-sm font-medium inline-flex items-center gap-1.5 hover:bg-muted transition-colors">
                    <Icon name="image" className="w-4 h-4" /> {anhJp2 ? "Đổi ảnh" : "Thêm ảnh (tùy chọn)"}
                  </button>
                  {anhJp2 && <span className="text-[12px] text-success inline-flex items-center gap-1"><Icon name="check" className="w-3.5 h-3.5" sw={3} /> Đã có ảnh</span>}
                </div>
              )}

              {err && (
                <div className="flex items-center gap-2 text-[13px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2">
                  <Icon name="warn" className="w-4 h-4 shrink-0" /> {err}
                </div>
              )}
            </>
          )}
        </div>

        <div className="p-3 border-t border-border flex gap-2">
          <button onClick={onDong} disabled={busy} className="h-10 px-4 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors disabled:opacity-60">Hủy</button>
          <button
            onClick={() => void nap()}
            disabled={busy || !dayDu || !khoa || trung.trung}
            className="ml-auto h-10 px-5 rounded-lg bg-primary text-primary-foreground text-sm font-semibold inline-flex items-center gap-2 hover:brightness-110 transition-all shadow-sm disabled:opacity-60"
          >
            <Icon name={busy ? "refresh" : "plus"} className={"w-4 h-4" + (busy ? " animate-spin" : "")} /> {busy ? "Đang nạp…" : "Mở hồ sơ ở khóa đích"}
          </button>
        </div>
      </div>

      {anhModal && <AnhModal onDong={() => setAnhModal(false)} onXong={(b64) => { setAnhJp2(b64); setAnhModal(false); }} />}
    </div>
  );
}
