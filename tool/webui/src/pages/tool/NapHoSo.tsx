import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Icon } from "../../components/Icon";
import { PhanTrang } from "../../components/PhanTrang";
import AddressCombo, { type DiaChiMoi } from "../../components/AddressCombo";
import AnhModal from "../../components/AnhModal";
import TraCuuDB from "./TraCuuDB";
import { boDau, nghiSaiChinhTa, ymdToVN } from "../../lib/format";
import { tachDiaChiGoc } from "../../lib/diachi";
import {
  getKhoaHoc,
  getGiayTo,
  keoHangDoi,
  getDanhSachKeoVe,
  boKhoiHangDoi,
  taiAnhKeoVe,
  napLo,
  type KhoaHoc,
  type LoaiXe,
  type GiayTo,
  type KeoVeRow,
  type NapIn,
} from "../../lib/api";

// Kết quả nạp 1 HV để dựng báo cáo (gộp uuid + tên để hiện ở pha báo cáo).
interface NapDong {
  uuid: string;
  ho_ten: string;
  ok: boolean;
  ma_dk?: string;
  so_ho_so?: string;
  loi?: string;
}

// Bản nháp chuẩn bị 1 HV trước khi nạp (địa chỉ + giấy tờ + ảnh do operator bổ sung).
interface Nhap {
  diaChi: DiaChiMoi | null; // NAP-03: operator map/chọn tay — bắt buộc mới nạp được
  chiTiet: string;
  jp2: string | null;
  anhPreview: string | null; // CHANGES #23: PNG xem trước ảnh đã chỉnh (xem lại + mở lại chỉnh tiếp); .jp2 không render trực tiếp
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

// NAP-01 task 47 — dialog nạp lô 3 pha (reuse mẫu DoiNenDialog của QLY-07): xác nhận → tiến độ →
// báo cáo. Nạp TUẦN TỰ từng uuid ở client (gọi napLo 1-uuid, như "Nạp lại nhanh") để thanh % +
// tên HV đang nạp cập nhật mượt — không thêm endpoint server (TDD §10.5). 1 HV lỗi không hỏng cả lô.
function NapLoDialog({ khoa, items, boQua, onDong, onXong, onXemDB }: {
  khoa: KhoaHoc;
  items: NapIn[];
  boQua: number; // số dòng đã chọn nhưng chưa sẵn sàng → bỏ qua lô này
  onDong: () => void;
  onXong: (okRows: { uuid: string; ma_dk: string }[]) => void; // làm tươi staging + ghi khóa đã nạp
  onXemDB: (maDks: string[]) => void; // nhảy sang Tra cứu DB, làm nổi HV vừa nạp
}) {
  const [pha, setPha] = useState<"xacnhan" | "chay" | "xong">("xacnhan");
  const [dang, setDang] = useState<string | null>(null); // tên HV đang nạp
  const [daXuLy, setDaXuLy] = useState(0);
  const [tongChay, setTongChay] = useState(items.length);
  const [kq, setKq] = useState<NapDong[]>([]);

  async function chay(ds: NapIn[]) {
    setPha("chay");
    setDaXuLy(0);
    setTongChay(ds.length);
    setKq([]);
    const ketQua: NapDong[] = [];
    for (let i = 0; i < ds.length; i++) {
      const it = ds[i];
      setDang(it.ho_ten);
      setDaXuLy(i);
      try {
        const r = await napLo([it]);
        const d = r.ket_qua[0];
        ketQua.push({ uuid: it.uuid, ho_ten: it.ho_ten, ok: !!d?.ok, ma_dk: d?.ma_dk, so_ho_so: d?.so_ho_so, loi: d?.loi });
      } catch (e) {
        ketQua.push({ uuid: it.uuid, ho_ten: it.ho_ten, ok: false, loi: e instanceof Error ? e.message : "Nạp lỗi." });
      }
      setKq([...ketQua]);
    }
    setDang(null);
    setDaXuLy(ds.length);
    setPha("xong");
    onXong(ketQua.filter((x) => x.ok && x.ma_dk).map((x) => ({ uuid: x.uuid, ma_dk: x.ma_dk! })));
  }

  const okList = kq.filter((x) => x.ok);
  const loiList = kq.filter((x) => !x.ok);
  const okMaDks = okList.map((x) => x.ma_dk).filter((m): m is string => !!m);
  const pct = tongChay > 0 ? Math.round((daXuLy / tongChay) * 100) : 0;

  // Nạp lại CHỈ các dòng lỗi (chọn lại đúng uuid lỗi từ items gốc).
  const napLaiLoi = () => {
    const loiUuids = new Set(loiList.map((x) => x.uuid));
    chay(items.filter((it) => loiUuids.has(it.uuid)));
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={(e) => { if (e.target === e.currentTarget && pha !== "chay") onDong(); }}>
      <div className="bg-card w-full max-w-md rounded-xl shadow-2xl max-h-[90vh] flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3 border-b border-border">
          <h3 className="font-bold text-sm">Nạp học viên vào khóa</h3>
          {pha !== "chay" && (
            <button onClick={onDong} aria-label="Đóng" className="w-8 h-8 rounded-lg hover:bg-muted flex items-center justify-center transition-colors">
              <Icon name="x" className="w-5 h-5" />
            </button>
          )}
        </div>
        <div className="p-5 overflow-y-auto">
          <p className="text-[13px] text-muted-foreground">Khóa <b className="text-foreground">{khoa.ten_kh}</b> ({khoa.ma_kh})</p>

          {/* PHA 1 — xác nhận */}
          {pha === "xacnhan" && (
            <div className="mt-4 space-y-3">
              <p className="text-[14px]">
                Nạp <b className="text-primary">{items.length}</b> học viên sẵn sàng vào khóa này.
              </p>
              {boQua > 0 && (
                <p className="text-[12.5px] text-warning flex items-start gap-1.5">
                  <Icon name="warn" className="w-4 h-4 shrink-0 mt-px" /> {boQua} hồ sơ chưa sẵn sàng (thiếu địa chỉ/giấy tờ) sẽ bỏ qua — chuẩn bị xong nạp sau.
                </p>
              )}
              <p className="text-[12px] text-muted-foreground">Lỗi 1 học viên không hỏng cả lô — cuối cùng có báo cáo từng hồ sơ.</p>
            </div>
          )}

          {/* PHA 2+3 — tiến độ & báo cáo */}
          {pha !== "xacnhan" && (
            <div className="mt-4 space-y-3">
              <div className="h-2.5 rounded-full bg-muted overflow-hidden">
                <div className="h-full bg-primary transition-all" style={{ width: `${pct}%` }} />
              </div>
              <div className="flex items-center justify-between text-[13px]">
                <span className="text-muted-foreground tabular-nums">{Math.min(daXuLy, tongChay)}/{tongChay} · {pct}%</span>
                {pha === "chay" && <span className="inline-flex items-center gap-1 text-primary font-medium"><Icon name="refresh" className="w-3.5 h-3.5 animate-spin" /> đang nạp…</span>}
                {pha === "xong" && <span className="inline-flex items-center gap-1 text-success font-medium"><Icon name="check" className="w-3.5 h-3.5" sw={3} /> xong</span>}
              </div>
              {pha === "chay" && dang && (
                <p className="text-[12.5px] text-foreground truncate">Đang nạp: <b>{dang.toUpperCase()}</b></p>
              )}

              {pha === "xong" && (
                <>
                  <div className="flex gap-3 text-[12.5px]">
                    <span className="text-success">Vào DB: <b className="tabular-nums">{okList.length}</b></span>
                    <span className={loiList.length > 0 ? "text-destructive" : "text-muted-foreground"}>Lỗi: <b className="tabular-nums">{loiList.length}</b></span>
                  </div>
                  {kq.length > 0 && (
                    <div className="max-h-56 overflow-y-auto rounded-lg border border-border divide-y divide-border text-[12px]">
                      {kq.map((x) => (
                        <div key={x.uuid} className="px-2.5 py-1.5 flex items-start gap-2">
                          <Icon name={x.ok ? "check" : "warn"} className={"w-3.5 h-3.5 shrink-0 mt-0.5 " + (x.ok ? "text-success" : "text-destructive")} sw={x.ok ? 3 : 2} />
                          <div className="min-w-0 flex-1">
                            <div className="font-semibold truncate">{x.ho_ten.toUpperCase() || "(chưa có tên)"}</div>
                            {x.ok ? (
                              <div className="text-success">Số hồ sơ {x.so_ho_so} · MaDK {x.ma_dk}</div>
                            ) : (
                              <div className="text-destructive">{x.loi || "Nạp lỗi."}</div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>
        <div className="p-3 border-t border-border flex gap-2 flex-wrap">
          {pha === "xacnhan" && (
            <>
              <button onClick={onDong} className="h-10 px-4 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors">Hủy</button>
              <button onClick={() => void chay(items)} className="ml-auto h-10 px-5 rounded-lg bg-primary text-primary-foreground text-sm font-semibold inline-flex items-center gap-2 hover:brightness-110 transition-all shadow-sm">
                <Icon name="plus" className="w-4 h-4" /> Bắt đầu nạp
              </button>
            </>
          )}
          {pha === "chay" && (
            <p className="text-[12px] text-muted-foreground px-1 py-2">Đang nạp — vui lòng chờ hết lô.</p>
          )}
          {pha === "xong" && (
            <>
              {loiList.length > 0 && (
                <button onClick={() => void napLaiLoi()} className="h-10 px-4 rounded-lg border border-primary/40 text-primary text-sm font-semibold inline-flex items-center gap-2 hover:bg-primary/5 transition-colors">
                  <Icon name="refresh" className="w-4 h-4" /> Nạp lại {loiList.length} lỗi
                </button>
              )}
              {okMaDks.length > 0 && (
                <button onClick={() => onXemDB(okMaDks)} className="h-10 px-4 rounded-lg border border-border text-sm font-semibold inline-flex items-center gap-2 hover:bg-muted transition-colors">
                  <Icon name="db" className="w-4 h-4" /> Xem trong DB
                </button>
              )}
              <button onClick={onDong} className="ml-auto h-10 px-5 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:brightness-110 transition-all shadow-sm">Xong</button>
            </>
          )}
        </div>
      </div>
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
  const [drawerOpen, setDrawerOpen] = useState(false); // task 46 — ngăn "Chuẩn bị" trượt từ phải

  // Nạp lô
  const [napBusy, setNapBusy] = useState(false);
  const [napErr, setNapErr] = useState("");

  // Task 47 — dialog nạp 3 pha + "Xem trong DB"
  const [napDialog, setNapDialog] = useState<{ items: NapIn[]; boQua: number } | null>(null);
  const [napKhoa, setNapKhoa] = useState<Record<string, string>>({}); // uuid → mã khóa đã nạp (cho "Xem trong DB" dòng đã nạp)
  const [xemDB, setXemDB] = useState<{ maKh: string; maDks: string[]; nonce: number } | null>(null);

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
      if (kq.bo_da_xoa > 0) phan.push(`bỏ ${kq.bo_da_xoa} hồ sơ đã xóa ở app`);
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
  // UI-3/4: phân trang cột list (client). Đổi nhóm/ô tìm/cỡ → về trang 1.
  const [trangNap, setTrangNap] = useState(0);
  const [coTrangNap, setCoTrangNap] = useState(20);
  useEffect(() => { setTrangNap(0); }, [napFilter, q, coTrangNap]);
  const rowsTrang = rows.slice(trangNap * coTrangNap, (trangNap + 1) * coTrangNap);
  const tongXong = keoVe.filter((r) => r.trang_thai === "xong").length;
  const soLoi = keoVe.filter((r) => r.trang_thai === "loi").length;
  const soChinhTa = daLoc.canXuly.filter((r) => nghiSaiChinhTa(r.ho_ten || "")).length;

  // Nháp của 1 HV (khởi tạo giấy tờ theo khóa nếu chưa có).
  const layNhap = (uuid: string): Nhap =>
    nhap[uuid] ?? { diaChi: null, chiTiet: "", jp2: null, anhPreview: null, tick: null };

  const capNhatNhap = (uuid: string, patch: Partial<Nhap>) =>
    setNhap((prev) => ({ ...prev, [uuid]: { ...layNhap(uuid), ...patch } }));

  // NAP-03 (CHANGES #19): chọn hồ sơ → tự điền sẵn ô "Chi tiết thường trú" từ phần dư của địa
  // chỉ gốc (số nhà/thôn), chỉ khi chưa có nháp (không đè giá trị operator đã gõ).
  useEffect(() => {
    if (!selUuid || nhap[selUuid]) return;
    const row = keoVe.find((r) => r.uuid === selUuid);
    const ct = tachDiaChiGoc(row?.noi_tt_raw).chiTiet;
    if (ct) capNhatNhap(selUuid, { chiTiet: ct });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selUuid]);

  const toggleChon = (uuid: string) =>
    setChon((prev) => {
      const next = new Set(prev);
      next.has(uuid) ? next.delete(uuid) : next.add(uuid);
      return next;
    });

  // Task 46 — trạng thái sẵn sàng mỗi dòng. Sẵn sàng = đủ ĐỊA CHỈ + GIẤY TỜ (ảnh KHÔNG bắt buộc,
  // BR-011 — thiếu ảnh chỉ cảnh báo phụ, chủ dự án chốt 03/10). tick===null = mặc định tick hết =
  // đủ; tick===[] = bỏ hết = thiếu. thieuAnh = chưa có ảnh đã xử lý (nháp) lẫn ảnh thô VPS.
  const tinhSanSang = (r: KeoVeRow) => {
    const n = nhap[r.uuid];
    const thieu: string[] = [];
    if (!n?.diaChi) thieu.push("địa chỉ");
    if (n?.tick != null && n.tick.length === 0) thieu.push("giấy tờ");
    const thieuAnh = !n?.jp2 && !n?.anhPreview && !r.co_anh;
    return { ok: thieu.length === 0, thieu, thieuAnh };
  };

  // 'cho' và 'loi' đều nạp được (lỗi đã unlock về pending trên VPS → sửa rồi nạp lại); 'xong' thì thôi.
  const rowSanSang = (r: KeoVeRow) => r.trang_thai !== "xong" && tinhSanSang(r).ok;

  // Task 46 — "Chọn tất cả sẵn sàng": tick mọi dòng Cần xử lý đủ điều kiện (bỏ qua dòng còn thiếu).
  const chonTatCaSanSang = () =>
    setChon(new Set(daLoc.canXuly.filter(rowSanSang).map((r) => r.uuid)));

  // Mở ngăn Chuẩn bị cho 1 HV (chọn dòng + trượt ngăn phải).
  const moChuanBi = (uuid: string) => { setSelUuid(uuid); setDrawerOpen(true); };

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
      const kq = await napLo(items);
      setKeoVe(await getDanhSachKeoVe()); // trạng thái mỗi dòng cập nhật ở staging
      setChon(new Set());
      if (khoa) ghiNapKhoa(kq.ket_qua.filter((d) => d.ok).map((d) => d.uuid), khoa.ma_kh);
    } catch (e) {
      setNapErr(e instanceof Error ? e.message : "Nạp lô thất bại.");
    } finally {
      setNapBusy(false);
    }
  };

  // Ghi khóa đã nạp cho từng uuid (phục vụ nút "Xem trong DB" ở dòng đã nạp).
  const ghiNapKhoa = (uuids: string[], maKh: string) =>
    setNapKhoa((prev) => {
      const next = { ...prev };
      for (const u of uuids) next[u] = maKh;
      return next;
    });

  // Task 47 — mở dialog nạp 3 pha cho danh sách dòng sẵn sàng.
  const moNapDialog = (dsRow: KeoVeRow[]) => {
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
    setNapDialog({ items, boQua: Math.max(0, chon.size - items.length) });
  };

  // Task 47 — nhảy sang Tra cứu DB, mở khóa đích + làm nổi HV vừa nạp.
  const xemTrongDB = (maKh: string, maDks: string[]) => {
    setXemDB({ maKh, maDks, nonce: Date.now() });
    setMode("tracuu");
  };

  // NAP-01 task 38 — nút trên dòng: nạp lại nhanh (🔴) tái dùng nạp lô 1 uuid; bỏ khỏi hàng đợi (🟢).
  const napLaiNhanh = (r: KeoVeRow) => { void chayNapLo([r]); };
  const boDong = async (r: KeoVeRow) => {
    setNapErr("");
    try {
      await boKhoiHangDoi(r.uuid);
      setKeoVe(await getDanhSachKeoVe());
      if (selUuid === r.uuid) setSelUuid(null);
    } catch (e) {
      setNapErr(e instanceof Error ? e.message : "Không bỏ được khỏi hàng đợi.");
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
            onClick={() => { setXemDB(null); setMode("tracuu"); }}
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

          {/* UI-4: ghim theo chiều cao màn hình (thay 720px cứng) — cột detail + ảnh đứng yên,
              chỉ cột list cuộn, giống app Windows. */}
          <div className="flex flex-col h-[calc(100svh-8.5rem)] min-h-0">
            {/* Hàng chờ nạp lô — 1 danh sách, chuẩn bị qua ngăn trượt phải (task 46 redesign) */}
            <div className="flex-1 min-w-0 flex flex-col min-h-0">
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

              {/* Banners lỗi/chính tả (chỉ nhóm Cần xử lý); thanh nạp lô dời xuống ĐÁY (task 46) */}
              {napFilter === "canxuly" && (soLoi > 0 || soChinhTa > 0 || napErr) && (
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

              {/* rows — chỉ cột này cuộn */}
              <div className="flex-1 overflow-y-auto min-h-0">
                {rowsTrang.map((r) => {
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
                        {/* Task 46 — trạng thái sẵn sàng / thiếu gì ngay trên dòng */}
                        {r.trang_thai !== "xong" && (() => {
                          const ss = tinhSanSang(r);
                          return ss.ok ? (
                            <span className="hidden sm:inline-flex items-center gap-1 text-[10.5px] text-success font-semibold">
                              <Icon name="check" className="w-3 h-3" sw={3} /> Sẵn sàng
                              {ss.thieuAnh && <span className="text-warning font-medium"> · ⚠ thiếu ảnh</span>}
                            </span>
                          ) : (
                            <span className="hidden sm:inline-flex items-center gap-1 text-[10.5px] text-warning font-medium" title={"Thiếu: " + ss.thieu.join(", ")}>
                              <Icon name="warn" className="w-3 h-3" /> Thiếu {ss.thieu.join(" + ")}
                            </span>
                          );
                        })()}
                        {/* Task 46 — mở ngăn Chuẩn bị (địa chỉ + giấy tờ + ảnh) */}
                        {r.trang_thai !== "xong" && (
                          <button
                            type="button"
                            title="Chuẩn bị hồ sơ"
                            onClick={(e) => { e.stopPropagation(); moChuanBi(r.uuid); }}
                            className="h-7 px-2.5 rounded-md border border-border text-[11px] font-semibold inline-flex items-center gap-1 hover:bg-muted transition-colors"
                          >
                            <Icon name="edit" className="w-3.5 h-3.5" /> Chuẩn bị
                          </button>
                        )}
                        {/* NAP-01 task 38 — nạp lại nhanh dòng lỗi */}
                        {r.trang_thai === "loi" && (
                          <button
                            type="button"
                            title="Nạp lại nhanh"
                            disabled={napBusy || !rowSanSang(r)}
                            onClick={(e) => { e.stopPropagation(); napLaiNhanh(r); }}
                            className="h-7 px-2 rounded-md border border-primary/40 text-primary text-[11px] font-semibold inline-flex items-center gap-1 hover:bg-primary/5 transition-colors disabled:opacity-50"
                          >
                            <Icon name="refresh" className={"w-3.5 h-3.5" + (napBusy ? " animate-spin" : "")} /> Nạp lại
                          </button>
                        )}
                        {/* NAP-01 task 47 — xem HV vừa nạp trong Tra cứu DB (mở đúng khóa đích, làm nổi) */}
                        {r.trang_thai === "xong" && r.ma_dk && (() => {
                          const mk = napKhoa[r.uuid] ?? khoa?.ma_kh;
                          return (
                            <button
                              type="button"
                              title="Xem học viên này trong DB"
                              disabled={!mk}
                              onClick={(e) => { e.stopPropagation(); if (mk) xemTrongDB(mk, [r.ma_dk!]); }}
                              className="h-7 px-2 rounded-md border border-border text-[11px] font-semibold inline-flex items-center gap-1 hover:bg-muted transition-colors disabled:opacity-50"
                            >
                              <Icon name="db" className="w-3.5 h-3.5" /> Xem DB
                            </button>
                          );
                        })()}
                        {/* NAP-01 task 38 — bỏ dòng đã nạp khỏi hàng đợi (staging, không đụng prod) */}
                        {r.trang_thai === "xong" && (
                          <button
                            type="button"
                            title="Bỏ khỏi hàng đợi (không xóa khỏi DB)"
                            onClick={(e) => { e.stopPropagation(); void boDong(r); }}
                            className="w-7 h-7 rounded-md inline-flex items-center justify-center text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
                          >
                            <Icon name="x" className="w-4 h-4" />
                          </button>
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

              {rows.length > 0 && (
                <div className="px-4 shrink-0 border-t border-border">
                  <PhanTrang total={rows.length} trang={trangNap} coTrang={coTrangNap} onTrang={setTrangNap} onCoTrang={setCoTrangNap} />
                </div>
              )}

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

              {/* THANH DÍNH ĐÁY — Chọn tất cả sẵn sàng + Nạp N học viên (task 46) */}
              {napFilter === "canxuly" && (
                <div className="px-4 py-3 border-t border-border bg-card shrink-0 flex items-center gap-3 flex-wrap">
                  <button
                    type="button"
                    onClick={chonTatCaSanSang}
                    disabled={daLoc.canXuly.filter(rowSanSang).length === 0}
                    className="h-9 px-3 rounded-lg border border-border text-sm font-medium inline-flex items-center gap-1.5 hover:bg-muted transition-colors disabled:opacity-50"
                  >
                    <Icon name="check" className="w-4 h-4" /> Chọn tất cả sẵn sàng
                  </button>
                  <span className="text-[12px] text-muted-foreground">
                    Đã chọn <b className="text-primary">{chonSanSang.length}</b>/{daLoc.canXuly.length}
                    {chon.size > chonSanSang.length && (
                      <span className="text-warning"> · {chon.size - chonSanSang.length} chưa sẵn sàng</span>
                    )}
                  </span>
                  <button
                    onClick={() => moNapDialog(chonSanSang)}
                    disabled={napBusy || chonSanSang.length === 0 || !khoa}
                    className="ml-auto h-10 px-5 rounded-lg bg-primary text-primary-foreground font-semibold text-sm flex items-center gap-2 hover:brightness-110 transition-all shadow-sm disabled:opacity-60"
                  >
                    <Icon name="plus" className="w-4 h-4" />
                    {`Nạp ${chonSanSang.length} học viên${khoa ? ` vào ${khoa.ma_kh}` : ""}`}
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* NGĂN "CHUẨN BỊ" — trượt từ phải (task 46): địa chỉ + giấy tờ + ảnh, thay 2 cột cố định */}
          {drawerOpen && selRow && (
            <div className="fixed inset-0 z-40 flex justify-end">
              <div className="absolute inset-0 bg-black/40" onClick={() => setDrawerOpen(false)} />
              <div className="relative w-full max-w-[460px] h-full bg-card shadow-xl flex flex-col min-h-0">
                <div className="px-4 py-3 border-b border-border flex items-center justify-between shrink-0">
                  <h3 className="text-sm font-bold">Chuẩn bị hồ sơ</h3>
                  <div className="flex items-center gap-2">
                    <NapBadge tt={selRow.trang_thai} />
                    <button onClick={() => setDrawerOpen(false)} aria-label="Đóng" className="text-muted-foreground hover:text-foreground">
                      <Icon name="x" className="w-5 h-5" />
                    </button>
                  </div>
                </div>
                <>
                  <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-0">
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
                      <AddressCombo key={selRow.uuid} diaChiGoc={selRow.noi_tt_raw ?? ""} onChon={(dc) => capNhatNhap(selRow.uuid, { diaChi: dc })} />
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
                    {/* Ảnh chân dung — chuyển vào ngăn (task 46); NAP-04 + "Dùng lại ảnh gốc" (task 45) */}
                    <div className="rounded-lg border border-border bg-card p-3">
                      <h4 className="text-[13px] font-bold mb-0.5">Ảnh chân dung</h4>
                      <p className="text-[11px] text-muted-foreground mb-2">3:4 · 353×471 · nền trắng (NAP-04)</p>
                      <div className="aspect-[3/4] w-full max-w-[200px] rounded-lg bg-white border border-input flex items-center justify-center relative overflow-hidden mb-3 shadow-sm">
                        {layNhap(selRow.uuid).anhPreview ? (
                          <>
                            <img src={layNhap(selRow.uuid).anhPreview!} alt="Ảnh đã chỉnh (nền trắng)" className="w-full h-full object-cover" />
                            <span className="absolute top-2 left-2 text-[10px] bg-success text-white px-1.5 py-0.5 rounded">Đã xử lý .jp2</span>
                          </>
                        ) : layNhap(selRow.uuid).jp2 ? (
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
                      {selRow.co_anh ? (
                        <p className="text-[11px] text-muted-foreground mb-2">Ảnh thô do người thu nhận chụp. Chỉnh (crop 3:4, nền trắng) để xuất .jp2.</p>
                      ) : (
                        <p className="text-[11px] text-muted-foreground mb-2">Hồ sơ không có ảnh — vẫn nạp được (TT_XuLy 01, BR-011).</p>
                      )}
                      <button
                        onClick={() => setAnhOpen(true)}
                        className="w-full h-9 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:brightness-110 transition-all shadow-sm flex items-center justify-center gap-2"
                      >
                        <Icon name="camera" className="w-4 h-4" /> Mở trình chỉnh ảnh
                      </button>
                    </div>
                  </div>

                  <div className="p-3 border-t border-border shrink-0">
                    <button
                      onClick={() => { void chayNapLo([selRow]); }}
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
              </div>
            </div>
          )}
        </>
      )}

      {/* ============ CHẾ ĐỘ TRA CỨU DB (QLY-01 — task 22) ============ */}
      {mode === "tracuu" && <TraCuuDB khoaMa={xemDB?.maKh} noiBat={xemDB?.maDks} moNonce={xemDB?.nonce} />}

      {/* Task 47 — dialog nạp lô 3 pha */}
      {napDialog && khoa && (
        <NapLoDialog
          khoa={khoa}
          items={napDialog.items}
          boQua={napDialog.boQua}
          onDong={() => setNapDialog(null)}
          onXong={async (okRows) => {
            setKeoVe(await getDanhSachKeoVe());
            setChon(new Set());
            ghiNapKhoa(okRows.map((o) => o.uuid), khoa.ma_kh);
          }}
          onXemDB={(maDks) => { setNapDialog(null); xemTrongDB(khoa.ma_kh, maDks); }}
        />
      )}

      {anhOpen && selRow && (
        <AnhModal
          onDong={() => setAnhOpen(false)}
          onXong={(b64, preview) => capNhatNhap(selRow.uuid, { jp2: b64, anhPreview: preview })}
          anhBanDau={layNhap(selRow.uuid).anhPreview ?? (selRow.co_anh ? anhUrl : null)}
          anhGoc={selRow.co_anh ? anhUrl : null}
        />
      )}
    </>
  );
}
