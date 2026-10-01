import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Icon } from "../../components/Icon";
import AddressCombo, { type DiaChiMoi } from "../../components/AddressCombo";
import AnhModal from "../../components/AnhModal";
import { boDau, nghiSaiChinhTa, ymdToVN } from "../../lib/format";
import {
  getKhoaHoc,
  getGiayTo,
  keoHangDoi,
  getDanhSachKeoVe,
  taiAnhKeoVe,
  napLo,
  type KhoaHoc,
  type LoaiXe,
  type GiayTo,
  type KeoVeRow,
  type NapIn,
} from "../../lib/api";

// Bản nháp chuẩn bị 1 HV trước khi nạp (địa chỉ + giấy tờ + ảnh do operator bổ sung).
interface Nhap {
  diaChi: DiaChiMoi | null; // NAP-03: operator map/chọn tay — bắt buộc mới nạp được
  chiTiet: string;
  jp2: string | null;
  tick: number[] | null; // giấy tờ đã tick; null = chưa khởi tạo theo khóa
}

// Badge trạng thái nạp lô (CHANGES #6) — màu + icon + chữ (phủ mù màu).
function NapBadge({ tt }: { tt: KeoVeRow["trang_thai"] }) {
  const cfg = {
    cho: { cls: "text-muted-foreground bg-muted border-border", icon: "clock", label: "Chờ nạp" },
    loi: { cls: "text-destructive bg-destructive/10 border-destructive/40", icon: "warn", label: "Lỗi" },
    xong: { cls: "text-success bg-success/10 border-success/40", icon: "check", label: "Đã nạp" },
  }[tt];
  return (
    <span className={`inline-flex items-center gap-1 text-[11px] font-semibold border rounded-full px-2 py-0.5 whitespace-nowrap ${cfg.cls}`}>
      <Icon name={cfg.icon} className="w-3 h-3" sw={2.5} /> {cfg.label}
    </span>
  );
}

// Banner cảnh báo inline nổi bật (NFR⑥) — nền + viền trái dày + icon + nêu rõ nguyên nhân.
function Banner({ tone = "warning", children }: { tone?: "warning" | "error"; children: ReactNode }) {
  const cls =
    tone === "error"
      ? "border-destructive/40 border-l-destructive bg-destructive/10 text-destructive"
      : "border-warning/40 border-l-warning bg-warning/10 text-warning";
  return (
    <div role="alert" className={`flex items-start gap-2.5 rounded-lg border border-l-4 px-3 py-2.5 ${cls}`}>
      <Icon name="warn" className="w-5 h-5 shrink-0 mt-px" />
      <div className="text-[12.5px] font-medium leading-relaxed">{children}</div>
    </div>
  );
}

// NAP-01: Tool kéo hàng đợi VPS → staging + nạp lô (chế độ Nạp). Tra cứu DB = QLY-01 (task 22, stub).
export default function NapHoSo() {
  const [mode, setMode] = useState<"nap" | "tracuu">("nap");

  // Khóa đích (chỉ chưa BC1 — NAP-02)
  const [loai, setLoai] = useState<LoaiXe>("oto");
  const [list, setList] = useState<KhoaHoc[]>([]);
  const [maKh, setMaKh] = useState("");
  const [loadingKhoa, setLoadingKhoa] = useState(true);
  const [errKhoa, setErrKhoa] = useState("");

  // Hàng kéo về (staging)
  const [keoVe, setKeoVe] = useState<KeoVeRow[]>([]);
  const [keoErr, setKeoErr] = useState("");
  const [keoMsg, setKeoMsg] = useState("");
  const [keoBusy, setKeoBusy] = useState(false);
  const [napFilter, setNapFilter] = useState<"canxuly" | "danap">("canxuly");
  const [q, setQ] = useState("");
  const [qOpen, setQOpen] = useState(false);

  // Chọn để nạp lô + nháp chuẩn bị theo uuid
  const [chon, setChon] = useState<Set<string>>(new Set());
  const [selUuid, setSelUuid] = useState<string | null>(null);
  const [nhap, setNhap] = useState<Record<string, Nhap>>({});

  // Giấy tờ mặc định theo khóa + ảnh + modal
  const [giayTo, setGiayTo] = useState<GiayTo[]>([]);
  const [anhUrl, setAnhUrl] = useState<string | null>(null);
  const [anhOpen, setAnhOpen] = useState(false);

  // Nạp lô
  const [napBusy, setNapBusy] = useState(false);
  const [napErr, setNapErr] = useState("");

  // ── Tải khóa đích ──
  useEffect(() => {
    let huy = false;
    setLoadingKhoa(true);
    setErrKhoa("");
    getKhoaHoc(loai)
      .then((ks) => {
        if (huy) return;
        setList(ks);
        setMaKh(ks[0]?.ma_kh ?? "");
      })
      .catch(() => !huy && setErrKhoa("Không tải được danh sách khóa — kiểm cấu hình kết nối."))
      .finally(() => !huy && setLoadingKhoa(false));
    return () => {
      huy = true;
    };
  }, [loai]);

  const khoa = list.find((k) => k.ma_kh === maKh) ?? null;

  // ── Giấy tờ bắt buộc theo khóa ──
  useEffect(() => {
    if (!khoa) {
      setGiayTo([]);
      return;
    }
    let huy = false;
    getGiayTo(khoa.ma_loai_hs, khoa.hang_dt || khoa.hang_gplx)
      .then((gs) => !huy && setGiayTo(gs))
      .catch(() => !huy && setGiayTo([]));
    return () => {
      huy = true;
    };
  }, [maKh, khoa?.ma_loai_hs, khoa?.hang_dt]);

  // ── Tải staging lúc mở màn ──
  useEffect(() => {
    getDanhSachKeoVe().then(setKeoVe).catch(() => setKeoVe([]));
  }, []);

  // ── Ảnh của HV đang chọn (tải từ VPS) ──
  useEffect(() => {
    setAnhUrl(null);
    const row = keoVe.find((r) => r.uuid === selUuid);
    if (!row || !row.co_anh) return;
    let huy = false;
    let url: string | null = null;
    taiAnhKeoVe(row.uuid)
      .then((u) => {
        if (huy) {
          if (u) URL.revokeObjectURL(u);
          return;
        }
        url = u;
        setAnhUrl(u);
      })
      .catch(() => {});
    return () => {
      huy = true;
      if (url) URL.revokeObjectURL(url);
    };
  }, [selUuid, keoVe]);

  const keoVeFromVps = async () => {
    setKeoErr("");
    setKeoMsg("");
    setKeoBusy(true);
    try {
      const kq = await keoHangDoi();
      setKeoVe(await getDanhSachKeoVe());
      const phan = [`${kq.keo_ve} hồ sơ mới`];
      if (kq.lam_tuoi > 0) phan.push(`làm tươi ${kq.lam_tuoi} hồ sơ chờ nạp`);
      setKeoMsg(`Đã kéo: ${phan.join(" · ")}. Tổng ${kq.tong} trong danh sách.`);
    } catch (e) {
      setKeoErr(e instanceof Error ? e.message : "Không kéo được hàng đợi từ VPS.");
    } finally {
      setKeoBusy(false);
    }
  };

  // Lọc + sắp xếp: Cần xử lý = chờ + lỗi (lỗi lên đầu) · Đã nạp = xong. Áp ô tìm (tên không dấu / CCCD).
  const daLoc = useMemo(() => {
    const qn = boDau(q.trim());
    const khopTim = (r: KeoVeRow) =>
      !qn ||
      boDau(r.ho_ten || "").includes(qn) ||
      (r.so_cccd || "").includes(q.trim()) ||
      (r.so_cmnd_cu || "").includes(q.trim());
    const canXuly = keoVe
      .filter((r) => r.trang_thai !== "xong")
      .filter(khopTim)
      .sort((a, b) => (b.trang_thai === "loi" ? 1 : 0) - (a.trang_thai === "loi" ? 1 : 0));
    const daNap = keoVe.filter((r) => r.trang_thai === "xong").filter(khopTim);
    return { canXuly, daNap };
  }, [keoVe, q]);

  const rows = napFilter === "canxuly" ? daLoc.canXuly : daLoc.daNap;
  const tongXong = keoVe.filter((r) => r.trang_thai === "xong").length;
  const soLoi = keoVe.filter((r) => r.trang_thai === "loi").length;
  const soChinhTa = daLoc.canXuly.filter((r) => nghiSaiChinhTa(r.ho_ten || "")).length;

  // Nháp của 1 HV (khởi tạo giấy tờ theo khóa nếu chưa có).
  const layNhap = (uuid: string): Nhap =>
    nhap[uuid] ?? { diaChi: null, chiTiet: "", jp2: null, tick: null };

  const capNhatNhap = (uuid: string, patch: Partial<Nhap>) =>
    setNhap((prev) => ({ ...prev, [uuid]: { ...layNhap(uuid), ...patch } }));

  const toggleChon = (uuid: string) =>
    setChon((prev) => {
      const next = new Set(prev);
      next.has(uuid) ? next.delete(uuid) : next.add(uuid);
      return next;
    });

  // 'cho' và 'loi' đều nạp được (lỗi đã unlock về pending trên VPS → sửa rồi nạp lại); 'xong' thì thôi.
  const rowSanSang = (r: KeoVeRow) => r.trang_thai !== "xong" && !!nhap[r.uuid]?.diaChi;

  // Dựng NapIn từ 1 hàng kéo về + nháp.
  const dungNapIn = (r: KeoVeRow): NapIn | null => {
    const n = layNhap(r.uuid);
    if (!khoa || !n.diaChi || !r.ho_ten || !r.ngay_sinh) return null;
    const tick = n.tick ?? giayTo.map((g) => g.ma_gt);
    return {
      uuid: r.uuid,
      ma_khoa_hoc: khoa.ma_kh,
      ho_ten: r.ho_ten.trim(),
      ngay_sinh: r.ngay_sinh,
      gioi_tinh: r.gioi_tinh || "M",
      so_cmt: (r.so_cccd || r.so_cmnd_cu || "").trim(),
      ngay_cap_cmt: r.ngay_cap || undefined,
      noi_cap_cmt: r.noi_cap_cccd || undefined,
      chi_tiet_tt: n.chiTiet.trim() || undefined,
      noi_tt_ma_dvhc: n.diaChi.ma_dvhc,
      noi_tt_ma_dvql: n.diaChi.ma_dvql,
      giay_to_tick: tick,
      anh_jp2_b64: n.jp2,
    };
  };

  const chayNapLo = async (dsRow: KeoVeRow[]) => {
    setNapErr("");
    const items: NapIn[] = [];
    for (const r of dsRow) {
      const it = dungNapIn(r);
      if (it) items.push(it);
    }
    if (items.length === 0) {
      setNapErr("Chưa hồ sơ nào sẵn sàng — mỗi hồ sơ cần map Nơi thường trú trước khi nạp.");
      return;
    }
    setNapBusy(true);
    try {
      await napLo(items);
      setKeoVe(await getDanhSachKeoVe()); // trạng thái mỗi dòng cập nhật ở staging
      setChon(new Set());
    } catch (e) {
      setNapErr(e instanceof Error ? e.message : "Nạp lô thất bại.");
    } finally {
      setNapBusy(false);
    }
  };

  const chonSanSang = daLoc.canXuly.filter((r) => chon.has(r.uuid) && rowSanSang(r));
  const selRow = keoVe.find((r) => r.uuid === selUuid) ?? null;

  return (
    <>
      {/* Thanh IA 2 chế độ (CHANGES #6) */}
      <div className="px-4 py-3 border-b border-border flex items-center gap-3 flex-wrap">
        <div className="inline-flex rounded-lg border border-border bg-muted p-1">
          <button
            onClick={() => setMode("nap")}
            className={
              "inline-flex items-center gap-2 px-4 py-2 text-sm rounded-md transition-colors " +
              (mode === "nap" ? "bg-primary text-primary-foreground font-semibold shadow-sm" : "text-muted-foreground font-medium hover:text-foreground")
            }
          >
            <Icon name="plus" className="w-4 h-4" /> Nạp hồ sơ
          </button>
          <button
            onClick={() => setMode("tracuu")}
            className={
              "inline-flex items-center gap-2 px-4 py-2 text-sm rounded-md transition-colors " +
              (mode === "tracuu" ? "bg-primary text-primary-foreground font-semibold shadow-sm" : "text-muted-foreground font-medium hover:text-foreground")
            }
          >
            <Icon name="search" className="w-4 h-4" /> Tra cứu DB
          </button>
        </div>
        <p className="text-[12px] text-muted-foreground">
          {mode === "nap"
            ? "Kéo hồ sơ từ VPS và nạp vào khóa chưa lập BC1."
            : "Tìm mọi khóa (kể cả 🔒 đã BC1) để xem/sửa hồ sơ đã có trong DB."}
        </p>
      </div>

      {/* ============ CHẾ ĐỘ NẠP ============ */}
      {mode === "nap" && (
        <>
          {/* Toolbar chọn khóa + kéo về */}
          <div className="px-4 py-3 border-b border-border bg-muted/40 flex items-center gap-4 flex-wrap">
            <div className="inline-flex rounded-lg border border-border bg-card p-0.5">
              {(["moto", "oto"] as const).map((l) => (
                <button
                  key={l}
                  onClick={() => setLoai(l)}
                  className={"px-4 py-1.5 text-sm rounded-md transition-colors " + (loai === l ? "bg-primary text-primary-foreground font-semibold" : "text-muted-foreground font-medium hover:text-foreground")}
                >
                  {l === "moto" ? "Mô tô" : "Ô tô"}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <label className="field-label whitespace-nowrap">Khóa đích</label>
              {loadingKhoa ? (
                <span className="inline-flex items-center gap-2 text-[13px] text-muted-foreground">
                  <Icon name="refresh" className="w-4 h-4 animate-spin" /> Đang tải…
                </span>
              ) : list.length === 0 ? (
                <span className="inline-flex items-center gap-1.5 text-[13px] text-warning bg-warning/10 border border-warning/30 rounded-lg px-3 py-1.5">
                  <Icon name="warn" className="w-4 h-4" /> Không có khóa nhận học viên (chưa lập BC1)
                </span>
              ) : (
                <select className="field-input" style={{ minWidth: 300 }} value={maKh} onChange={(e) => setMaKh(e.target.value)}>
                  {list.map((k) => (
                    <option key={k.ma_kh} value={k.ma_kh}>
                      {k.ma_kh} — {k.ten_kh}
                    </option>
                  ))}
                </select>
              )}
              <span className="text-[11px] text-muted-foreground">(chỉ khóa chưa BC1)</span>
            </div>
            <button
              onClick={keoVeFromVps}
              disabled={keoBusy}
              className="ml-auto inline-flex items-center gap-2 h-9 px-4 rounded-lg border border-primary text-primary font-semibold text-sm hover:bg-primary/5 transition-colors disabled:opacity-60"
            >
              <Icon name="refresh" className={"w-4 h-4" + (keoBusy ? " animate-spin" : "")} /> {keoBusy ? "Đang kéo…" : "Kéo về từ VPS"}
            </button>
          </div>

          {(errKhoa || keoErr) && (
            <div className="mx-4 mt-3">
              <Banner tone="error">{errKhoa || keoErr}</Banner>
            </div>
          )}
          {keoMsg && !keoErr && (
            <div className="mx-4 mt-3 flex items-center gap-2 text-[13px] font-medium text-success bg-success/10 border border-success/30 rounded-lg px-3 py-2">
              <Icon name="check" className="w-4 h-4 shrink-0" sw={3} /> {keoMsg}
            </div>
          )}

          <div className="flex flex-col xl:flex-row xl:h-[720px]">
            {/* CỘT 1: hàng chờ nạp lô */}
            <div className="flex-1 min-w-0 border-b xl:border-b-0 xl:border-r border-border flex flex-col min-h-0">
              <div className="px-4 py-3 flex items-center gap-3 flex-wrap border-b border-border shrink-0">
                <div className="inline-flex rounded-lg bg-muted p-1">
                  <button
                    onClick={() => setNapFilter("canxuly")}
                    className={"inline-flex items-center gap-2 px-3.5 py-1.5 text-sm rounded-md transition-colors " + (napFilter === "canxuly" ? "bg-card shadow-sm text-primary font-semibold" : "text-muted-foreground font-medium hover:text-foreground")}
                  >
                    <Icon name="clock" className="w-4 h-4" /> Cần xử lý <span className="text-[11px] bg-primary/10 rounded-full px-1.5">{daLoc.canXuly.length}</span>
                  </button>
                  <button
                    onClick={() => setNapFilter("danap")}
                    className={"inline-flex items-center gap-2 px-3.5 py-1.5 text-sm rounded-md transition-colors " + (napFilter === "danap" ? "bg-card shadow-sm text-success font-semibold" : "text-muted-foreground font-medium hover:text-foreground")}
                  >
                    <Icon name="check" className="w-4 h-4" /> Đã nạp <span className="text-[11px] bg-success/15 text-success rounded-full px-1.5">{daLoc.daNap.length}</span>
                  </button>
                </div>

                {/* Ô tìm — màn hẹp thu gọn nút kính lúp (CHANGES #10) */}
                <div className="flex items-center gap-2 ml-auto">
                  <button
                    onClick={() => setQOpen((v) => !v)}
                    aria-label="Tìm kiếm"
                    className="sm:hidden w-9 h-9 rounded-lg border border-border flex items-center justify-center text-muted-foreground hover:text-foreground"
                  >
                    <Icon name="search" className="w-4 h-4" />
                  </button>
                  <div className={(qOpen ? "flex" : "hidden") + " sm:flex relative"}>
                    <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground">
                      <Icon name="search" className="w-4 h-4" />
                    </span>
                    <input
                      className="field-input pl-8"
                      style={{ width: 200 }}
                      value={q}
                      onChange={(e) => setQ(e.target.value)}
                      placeholder="Tìm tên (không dấu) / CCCD"
                    />
                  </div>
                </div>
              </div>

              {/* Batch bar + banners (chỉ nhóm Cần xử lý) */}
              {napFilter === "canxuly" && (
                <>
                  <div className="px-4 py-2.5 flex items-center gap-3 flex-wrap border-b border-border shrink-0">
                    <span className="text-[12px] text-muted-foreground">
                      Đã chọn <b className="text-primary">{chonSanSang.length}</b>/{daLoc.canXuly.length}
                      {chon.size > chonSanSang.length && (
                        <span className="text-warning"> · {chon.size - chonSanSang.length} chưa sẵn sàng (thiếu địa chỉ)</span>
                      )}
                    </span>
                    <button
                      onClick={() => chayNapLo(chonSanSang)}
                      disabled={napBusy || chonSanSang.length === 0 || !khoa}
                      className="ml-auto h-9 px-4 rounded-lg bg-primary text-primary-foreground font-semibold text-sm flex items-center gap-2 hover:brightness-110 transition-all shadow-sm disabled:opacity-60"
                    >
                      <Icon name={napBusy ? "refresh" : "plus"} className={"w-4 h-4" + (napBusy ? " animate-spin" : "")} />
                      {napBusy ? "Đang nạp lô…" : `Nạp ${chonSanSang.length} HV${khoa ? ` vào ${khoa.ma_kh}` : ""}`}
                    </button>
                  </div>

                  {(soLoi > 0 || soChinhTa > 0 || napErr) && (
                    <div className="px-4 py-3 space-y-2 border-b border-border shrink-0">
                      {napErr && <Banner tone="error">{napErr}</Banner>}
                      {soLoi > 0 && (
                        <Banner tone="error">
                          <b>{soLoi} hồ sơ nạp lỗi</b> (🔴 bên dưới) — lý do ghi ngay trên từng dòng. Lô vẫn chạy hết; sửa xong nạp lại riêng dòng lỗi.
                        </Banner>
                      )}
                      {soChinhTa > 0 && (
                        <Banner tone="warning">
                          <b>{soChinhTa} hồ sơ tên nghi sai chính tả</b> (mức A: thiếu dấu / ký tự lạ / khoảng trắng thừa) — kiểm lại họ tên trước khi nạp, hệ thống không chặn.
                        </Banner>
                      )}
                    </div>
                  )}
                </>
              )}

              {/* rows — chỉ cột này cuộn */}
              <div className="flex-1 overflow-y-auto min-h-0">
                {rows.map((r) => {
                  const chinhTa = nghiSaiChinhTa(r.ho_ten || "");
                  const tenIn = (r.ho_ten || "").toUpperCase(); // IN HOA giữ dấu
                  return (
                    <div
                      key={r.uuid}
                      onClick={() => setSelUuid(r.uuid)}
                      className={"lrow flex items-center gap-3 px-4 py-3 cursor-pointer " + (selUuid === r.uuid ? "sel bg-accent" : "hover:bg-accent/50")}
                    >
                      {r.trang_thai !== "xong" ? (
                        <input
                          type="checkbox"
                          checked={chon.has(r.uuid)}
                          onChange={() => toggleChon(r.uuid)}
                          onClick={(e) => e.stopPropagation()}
                          className="accent-primary w-4 h-4 shrink-0"
                        />
                      ) : (
                        <span className="w-4 shrink-0" />
                      )}
                      <div className="min-w-0 flex-1">
                        <div className="font-semibold text-[14px] truncate flex items-center gap-1.5">
                          {tenIn || <span className="text-muted-foreground font-normal">(chưa có tên)</span>}
                          {chinhTa && (
                            <span className="inline-flex items-center gap-0.5 text-[10px] text-warning font-medium whitespace-nowrap" title={chinhTa}>
                              <Icon name="warn" className="w-3 h-3" /> nghi sai chính tả
                            </span>
                          )}
                        </div>
                        <div className="text-[12px] text-muted-foreground truncate">
                          {r.gioi_tinh === "F" ? "Nữ" : "Nam"} · {r.so_cccd || r.so_cmnd_cu || "—"} · {r.noi_tt_raw || "—"}
                        </div>
                        {r.trang_thai === "loi" && r.loi && (
                          <div className="text-[11px] text-destructive font-medium truncate mt-0.5 flex items-center gap-1">
                            <Icon name="warn" className="w-3 h-3 shrink-0" /> {r.loi}
                          </div>
                        )}
                        {r.trang_thai === "xong" && r.so_ho_so && (
                          <div className="text-[11px] text-success font-medium truncate mt-0.5">Số hồ sơ {r.so_ho_so} · MaDK {r.ma_dk}</div>
                        )}
                      </div>
                      <div className="flex items-center gap-1.5 shrink-0">
                        {rowSanSang(r) && (
                          <span className="hidden sm:inline-flex items-center gap-1 text-[10px] text-success font-medium">
                            <Icon name="check" className="w-3 h-3" sw={3} /> sẵn sàng
                          </span>
                        )}
                        <NapBadge tt={r.trang_thai} />
                      </div>
                    </div>
                  );
                })}
                {rows.length === 0 && (
                  <div className="px-4 py-10 text-center text-[13px] text-muted-foreground">
                    {keoVe.length === 0 ? 'Chưa kéo hồ sơ nào — bấm "Kéo về từ VPS".' : "Không có hồ sơ trong nhóm này."}
                  </div>
                )}
              </div>

              {/* footer tiến độ */}
              {keoVe.length > 0 && (
                <div className="px-4 py-2.5 border-t border-border shrink-0">
                  <div className="flex justify-between text-[11px] text-muted-foreground mb-1">
                    <span>Đã nạp (lỗi 1 HV không hỏng cả lô)</span>
                    <span>{tongXong}/{keoVe.length}</span>
                  </div>
                  <div className="h-2 rounded-full bg-muted overflow-hidden">
                    <div className="h-full bg-success rounded-full" style={{ width: `${Math.round((tongXong / keoVe.length) * 100)}%` }} />
                  </div>
                </div>
              )}
            </div>

            {/* CỘT 2: chuẩn bị HV đang chọn */}
            <div className="w-full xl:w-[460px] shrink-0 border-b xl:border-b-0 xl:border-r border-border bg-muted/15 flex flex-col min-h-0">
              <div className="px-4 py-3 border-b border-border flex items-center justify-between shrink-0">
                <h3 className="text-sm font-bold">Chuẩn bị hồ sơ</h3>
                {selRow && <NapBadge tt={selRow.trang_thai} />}
              </div>
              {!selRow ? (
                <div className="flex-1 flex items-center justify-center p-6 text-center text-[13px] text-muted-foreground">
                  Chọn một hồ sơ bên trái để map địa chỉ, chọn giấy tờ và ảnh trước khi nạp.
                </div>
              ) : (
                <>
                  <div className="flex-1 xl:overflow-y-auto p-4 space-y-3 min-h-0">
                    <div className="rounded-md bg-secondary/70 border border-border px-2.5 py-2 text-[12px] leading-relaxed">
                      <div className="font-bold text-[14px]">{(selRow.ho_ten || "").toUpperCase() || "(chưa có tên)"}</div>
                      <div className="text-muted-foreground mt-0.5">
                        {selRow.gioi_tinh === "F" ? "Nữ" : "Nam"} · CCCD {selRow.so_cccd || selRow.so_cmnd_cu || "—"}
                        {selRow.ngay_sinh && <> · NS {ymdToVN(selRow.ngay_sinh)}</>}
                        {selRow.ngay_cap && <> · cấp {ymdToVN(selRow.ngay_cap)}</>}
                      </div>
                      <div className="text-muted-foreground">Địa chỉ gốc: {selRow.noi_tt_raw || "—"}</div>
                      {nghiSaiChinhTa(selRow.ho_ten || "") && (
                        <div className="mt-1 text-warning font-medium flex items-center gap-1">
                          <Icon name="warn" className="w-3.5 h-3.5" /> Tên nghi sai chính tả ({nghiSaiChinhTa(selRow.ho_ten || "")}) — sửa trên VPS nếu cần.
                        </div>
                      )}
                    </div>

                    {/* NAP-03: map địa chỉ nơi thường trú */}
                    <div>
                      <label className="field-label mb-1 block">
                        Nơi thường trú <span className="text-destructive">*</span>{" "}
                        <span className="text-muted-foreground font-normal">(map/chọn tay để lấy đúng mã DVHC)</span>
                      </label>
                      <AddressCombo key={selRow.uuid} onChon={(dc) => capNhatNhap(selRow.uuid, { diaChi: dc })} />
                      {layNhap(selRow.uuid).diaChi && (
                        <div className="mt-1.5 text-[11px] text-success font-medium flex items-center gap-1">
                          <Icon name="check" className="w-3.5 h-3.5" sw={3} /> Đã map: {layNhap(selRow.uuid).diaChi!.ten_xa}, {layNhap(selRow.uuid).diaChi!.ten_tinh} (mã {layNhap(selRow.uuid).diaChi!.ma_dvhc})
                        </div>
                      )}
                      <input
                        className="field-input mt-2"
                        value={layNhap(selRow.uuid).chiTiet}
                        onChange={(e) => capNhatNhap(selRow.uuid, { chiTiet: e.target.value })}
                        placeholder="Chi tiết (số nhà/thôn) — không bắt buộc"
                      />
                    </div>

                    {/* Giấy tờ */}
                    <div className="rounded-lg border border-border bg-card p-3">
                      <h4 className="text-[13px] font-bold mb-2">
                        Giấy tờ kèm theo <span className="font-normal text-muted-foreground text-[11px]">(tick sẵn — bỏ tick được)</span>
                      </h4>
                      {giayTo.length === 0 ? (
                        <p className="text-[12px] text-muted-foreground">Chọn khóa đích để hiện giấy tờ.</p>
                      ) : (
                        <div className="space-y-1.5 text-[13px]">
                          {giayTo.map((g) => {
                            const tick = layNhap(selRow.uuid).tick ?? giayTo.map((x) => x.ma_gt);
                            return (
                              <label key={g.ma_gt} className="flex items-center gap-2 cursor-pointer">
                                <input
                                  type="checkbox"
                                  checked={tick.includes(g.ma_gt)}
                                  onChange={() =>
                                    capNhatNhap(selRow.uuid, {
                                      tick: tick.includes(g.ma_gt) ? tick.filter((m) => m !== g.ma_gt) : [...tick, g.ma_gt],
                                    })
                                  }
                                  className="w-4 h-4 accent-primary"
                                />
                                {g.ten_gt}
                              </label>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="p-3 border-t border-border shrink-0">
                    <button
                      onClick={() => chayNapLo([selRow])}
                      disabled={napBusy || !rowSanSang(selRow) || !khoa}
                      className="w-full h-10 rounded-lg bg-primary text-primary-foreground font-semibold text-sm flex items-center justify-center gap-2 hover:brightness-110 transition-all shadow-sm disabled:opacity-60"
                    >
                      <Icon name={napBusy ? "refresh" : "plus"} className={"w-4 h-4" + (napBusy ? " animate-spin" : "")} />
                      {selRow.trang_thai === "xong"
                        ? "Đã nạp"
                        : !layNhap(selRow.uuid).diaChi
                          ? "Map địa chỉ để nạp"
                          : khoa
                            ? `Nạp hồ sơ này vào ${khoa.ma_kh}`
                            : "Chọn khóa để nạp"}
                    </button>
                  </div>
                </>
              )}
            </div>

            {/* CỘT 3: ảnh */}
            <div className="w-full xl:w-[300px] shrink-0 bg-muted/5 p-4 flex flex-col">
              <h3 className="text-sm font-bold mb-1">Ảnh chân dung</h3>
              <p className="text-[11px] text-muted-foreground mb-3">3:4 · 353×471 · nền trắng (NAP-04)</p>
              <div className="aspect-[3/4] w-full max-w-[240px] mx-auto xl:mx-0 rounded-lg bg-white border border-input flex items-center justify-center relative overflow-hidden mb-3 shadow-sm">
                {selRow && layNhap(selRow.uuid).jp2 ? (
                  <>
                    <Icon name="check" className="w-16 h-16 text-success/50" />
                    <span className="absolute top-2 left-2 text-[10px] bg-success text-white px-1.5 py-0.5 rounded">Đã xử lý .jp2</span>
                  </>
                ) : anhUrl ? (
                  <img src={anhUrl} alt="Ảnh thô từ VPS" className="w-full h-full object-cover" />
                ) : (
                  <Icon name="user" className="w-16 h-16 text-muted-foreground/40" sw={1.5} />
                )}
              </div>
              {selRow ? (
                <>
                  {selRow.co_anh ? (
                    <p className="text-[11px] text-muted-foreground mb-2">Ảnh thô do người thu nhận chụp. Chỉnh (crop 3:4, nền trắng) để xuất .jp2.</p>
                  ) : (
                    <p className="text-[11px] text-muted-foreground mb-2">Hồ sơ không có ảnh — vẫn nạp được (TT_XuLy 01, BR-011).</p>
                  )}
                  <button
                    onClick={() => setAnhOpen(true)}
                    className="w-full h-10 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:brightness-110 transition-all shadow-sm flex items-center justify-center gap-2"
                  >
                    <Icon name="camera" className="w-4 h-4" /> Mở trình chỉnh ảnh
                  </button>
                  <p className="text-[11px] text-muted-foreground mt-2">Tên file = MaDK, lưu vào thư mục ảnh của khóa.</p>
                </>
              ) : (
                <p className="text-[12px] text-muted-foreground">Chọn hồ sơ để xem/chỉnh ảnh.</p>
              )}
            </div>
          </div>
        </>
      )}

      {/* ============ CHẾ ĐỘ TRA CỨU DB (QLY-01 — task 22) ============ */}
      {mode === "tracuu" && (
        <div className="p-8 flex flex-col items-center justify-center text-center gap-3 text-muted-foreground">
          <Icon name="search" className="w-10 h-10 opacity-40" />
          <p className="text-sm font-medium text-foreground">Tra cứu & sửa hồ sơ đã có</p>
          <p className="text-[13px] max-w-md">
            Tìm mọi khóa (kể cả 🔒 đã BC1), xem/sửa học viên trong DB. Phần này thuộc <b>QLY-01</b> — sẽ dựng ở bước sau.
          </p>
        </div>
      )}

      {anhOpen && selRow && (
        <AnhModal onDong={() => setAnhOpen(false)} onXong={(b64) => capNhatNhap(selRow.uuid, { jp2: b64 })} />
      )}
    </>
  );
}
