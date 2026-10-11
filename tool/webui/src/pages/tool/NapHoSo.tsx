import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { Icon } from "../../components/Icon";
import { PhanTrang } from "../../components/PhanTrang";
import AddressCombo, { type DiaChiMoi } from "../../components/AddressCombo";
import AnhModal from "../../components/AnhModal";
import { ODate } from "../../components/ODate";
import { ComboLoc } from "../../components/ComboLoc";
import { boDau, nghiSaiChinhTa, ymdToVN } from "../../lib/format";
import { tachDiaChiGoc, lamTuoiNhapDiaChi } from "../../lib/diachi";
import {
  getKhoaHoc,
  getGiayTo,
  keoHangDoi,
  getDanhSachKeoVe,
  boKhoiHangDoi,
  taiAnhKeoVe,
  napLo,
  getSoGtvt,
  nhapCo,
  nhapDoc,
  nhapLuu,
  nhapXoa,
  type KhoaHoc,
  type LoaiXe,
  type GiayTo,
  type KeoVeRow,
  type NapIn,
  type SoGtvt,
  type NhapCo,
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
// Nơi cấp căn cước mặc định (mã DM_DVHC): CCCD 12 số do Cục QLHC cấp → '00' (Cục QLHC).
// CMND 9 số / khác → '' (operator chọn tay). Đổi 06/10 (trước suy mã tỉnh — BUG-10).
function suyNoiCap(cccd: string | null | undefined): string {
  const s = (cccd || "").trim();
  return /^\d{12}$/.test(s) ? "00" : "";
}

// dd/mm/yyyy → 'yyyymmdd' (rỗng nếu chưa đủ ngày) — ô Ngày cấp CCCD (CHANGES #43).
// Dùng chung kiểu với TraCuuDB/TraCuuCDB (ngày cấp lưu yyyymmdd); cặp với ymdToVN.
function vnToYmd(v: string): string {
  const m = (v || "").trim().match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  return m ? `${m[3]}${m[2]}${m[1]}` : "";
}

interface Nhap {
  diaChi: DiaChiMoi | null; // NAP-03: operator map/chọn tay — bắt buộc mới nạp được
  chiTiet: string;
  noiCap?: string; // mã Sở GTVT (nơi cấp); operator sửa khi suy từ CCCD sai (BUG-10)
  ngayCap?: string; // CHANGES #43: ngày cấp CCCD dạng hiển thị dd/mm/yyyy (free-text khi gõ); undefined = chưa sửa, dùng gốc keo_ve.ngay_cap
  jp2: string | null;
  anhPreview: string | null; // CHANGES #23: PNG xem trước ảnh đã chỉnh (xem lại + mở lại chỉnh tiếp); .jp2 không render trực tiếp
  tick: number[] | null; // giấy tờ đã tick; null = chưa khởi tạo theo khóa
}

// Badge trạng thái nạp lô (CHANGES #6) — màu + icon + chữ (phủ mù màu).
function NapBadge({ tt, gon }: { tt: KeoVeRow["trang_thai"]; gon?: boolean }) {
  const cfg = {
    cho: { cls: "text-muted-foreground bg-muted border-border", icon: "clock", label: "Chờ nạp", ngan: "Chờ" },
    loi: { cls: "text-destructive bg-destructive/10 border-destructive/40", icon: "warn", label: "Lỗi", ngan: "Lỗi" },
    xong: { cls: "text-success bg-success/10 border-success/40", icon: "check", label: "Đã nạp", ngan: "Xong" },
  }[tt];
  return (
    <span
      title={cfg.label}
      className={`inline-flex items-center gap-1 text-[11px] font-semibold border rounded-full px-2 py-0.5 whitespace-nowrap ${cfg.cls}`}
    >
      <Icon name={cfg.icon} className="w-3 h-3" sw={2.5} /> {gon ? cfg.ngan : cfg.label}
    </span>
  );
}

// Màn đủ rộng để chia đôi (danh sách | ngăn Chuẩn bị luôn mở); hẹp hơn thì ngăn trượt phủ như trước.
function useRong(min = 1024): boolean {
  const [r, setR] = useState(() => typeof window !== "undefined" && window.matchMedia(`(min-width:${min}px)`).matches);
  useEffect(() => {
    const m = window.matchMedia(`(min-width:${min}px)`);
    const f = () => setR(m.matches);
    f();
    m.addEventListener("change", f);
    return () => m.removeEventListener("change", f);
  }, [min]);
  return r;
}

// Gói nháp gửi backend (dùng khi chuyển học viên, đóng ngăn, và khi rời trang).
function goiNhap(n: Nhap) {
  return {
    dia_chi_json: n.diaChi ? JSON.stringify(n.diaChi) : null,
    chi_tiet: n.chiTiet || null,
    noi_cap: n.noiCap || null,
    ngay_cap: vnToYmd(n.ngayCap ?? "") || null, // dd/mm/yyyy → yyyymmdd; chưa đủ/rỗng = null
    tick_json: n.tick ? JSON.stringify(n.tick) : null,
    jp2_b64: n.jp2,
    anh_preview: n.anhPreview,
  };
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
function NapLoDialog({ khoa, items, boQua, docked, onPha, onDong, onXong, onXemDB, onBoSungAnh }: {
  khoa: KhoaHoc;
  docked?: boolean; // true = vẽ trong ngăn phải (không phủ màn hình)
  onPha?: (pha: "xacnhan" | "chay" | "xong") => void;
  items: NapIn[];
  boQua: number; // số dòng đã chọn nhưng chưa sẵn sàng → bỏ qua lô này
  onDong: () => void;
  onXong: (okRows: { uuid: string; ma_dk: string }[]) => void; // làm tươi staging + ghi khóa đã nạp
  onXemDB: (maDks: string[]) => void; // nhảy sang Tra cứu DB, làm nổi HV vừa nạp
  onBoSungAnh: () => void; // CHANGES #32 — mở Tra cứu DB lọc "chưa ảnh" để bổ sung ảnh HV vừa nạp thiếu ảnh
}) {
  const [pha, setPha] = useState<"xacnhan" | "chay" | "xong">("xacnhan");
  const [dangUuid, setDangUuid] = useState<string | null>(null);
  const [daXuLy, setDaXuLy] = useState(0);
  const [tongChay, setTongChay] = useState(items.length);
  const [kq, setKq] = useState<NapDong[]>([]);

  useEffect(() => { onPha?.(pha); }, [pha]); // eslint-disable-line react-hooks/exhaustive-deps

  async function chay(ds: NapIn[]) {
    setPha("chay");
    setDaXuLy(0);
    setTongChay(ds.length);
    setKq([]);
    const ketQua: NapDong[] = [];
    for (let i = 0; i < ds.length; i++) {
      const it = ds[i];
      setDangUuid(it.uuid);
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
    setDangUuid(null);
    setDaXuLy(ds.length);
    setPha("xong");
    onXong(ketQua.filter((x) => x.ok && x.ma_dk).map((x) => ({ uuid: x.uuid, ma_dk: x.ma_dk! })));
  }

  const okList = kq.filter((x) => x.ok);
  const loiList = kq.filter((x) => !x.ok);
  const okMaDks = okList.map((x) => x.ma_dk).filter((m): m is string => !!m);
  const pct = tongChay > 0 ? Math.round((daXuLy / tongChay) * 100) : 0;
  // CHANGES #32 — thiếu ảnh: ảnh KHÔNG bắt buộc (BR-011) → vẫn nạp, chỉ cảnh báo + lối tắt bổ sung.
  const khongAnh = new Set(items.filter((i) => !i.anh_jp2_b64).map((i) => i.uuid));
  const soThieuAnh = khongAnh.size;                                    // cảnh báo trước lô
  const okThieuAnh = okList.filter((x) => khongAnh.has(x.uuid)).length; // sau lô: HV đã nạp mà thiếu ảnh

  // Nạp lại CHỈ các dòng lỗi (chọn lại đúng uuid lỗi từ items gốc).
  const napLaiLoi = () => {
    const loiUuids = new Set(loiList.map((x) => x.uuid));
    chay(items.filter((it) => loiUuids.has(it.uuid)));
  };

  // Trạng thái từng dòng: chờ → đang nạp → ✓ / ✗ (cập nhật ngay, không đợi cuối lô).
  const trangThaiDong = (it: NapIn) => {
    const r = kq.find((x) => x.uuid === it.uuid);
    if (r) return r.ok
      ? { k: "ok" as const, t: `Số HS ${r.so_ho_so ?? ""}`.trim() }
      : { k: "loi" as const, t: r.loi || "Nạp lỗi." };
    if (pha === "chay" && dangUuid === it.uuid) return { k: "dang" as const, t: "Đang nạp…" };
    return { k: "cho" as const, t: "Chờ" };
  };

  const noiDung = (
    <>
      <div className="flex items-center justify-between px-5 py-3 border-b border-border shrink-0">
        <h3 className="font-bold text-sm">Nạp học viên vào khóa</h3>
        {pha !== "chay" && (
          <button onClick={onDong} aria-label="Đóng" className="w-8 h-8 rounded-lg hover:bg-muted flex items-center justify-center transition-colors">
            <Icon name="x" className="w-5 h-5" />
          </button>
        )}
      </div>
      <div className={"p-5 overflow-y-auto " + (docked ? "flex-1 min-h-0" : "")}>
        <p className="text-[13px] text-muted-foreground">Khóa <b className="text-foreground">{khoa.ten_kh}</b> ({khoa.ma_kh})</p>

        <div className="mt-3 space-y-2">
          <p className="text-[14px]">
            {pha === "xacnhan" ? "Sẽ nạp " : "Nạp "}<b className="text-primary">{items.length}</b> học viên sẵn sàng vào khóa này.
          </p>
          {pha === "xacnhan" && boQua > 0 && (
            <p className="text-[12.5px] text-warning flex items-start gap-1.5">
              <Icon name="warn" className="w-4 h-4 shrink-0 mt-px" /> {boQua} hồ sơ chưa sẵn sàng (thiếu địa chỉ/giấy tờ) sẽ bỏ qua — chuẩn bị xong nạp sau.
            </p>
          )}
          {pha === "xacnhan" && soThieuAnh > 0 && (
            <p className="text-[12.5px] text-warning flex items-start gap-1.5">
              <Icon name="imageOff" className="w-4 h-4 shrink-0 mt-px" /> {soThieuAnh} học viên nạp <b>thiếu ảnh</b> — vẫn nạp được, bổ sung ảnh sau ở Tra cứu DB (lọc "chưa ảnh").
            </p>
          )}
          {pha === "xacnhan" && (
            <p className="text-[12px] text-muted-foreground">Lỗi 1 học viên không hỏng cả lô — cuối cùng có báo cáo từng hồ sơ.</p>
          )}
        </div>

        {/* Danh sách sẽ nạp + trạng thái từng dòng */}
        <div className={"mt-3 rounded-lg border border-border overflow-auto " + (docked ? "" : "max-h-56")}>
          <table className="w-full text-[12.5px]" aria-label="Danh sách học viên sẽ nạp">
            <thead>
              <tr className="bg-muted/60 text-muted-foreground text-left text-[12px] border-b border-border">
                <th className="px-2 py-1.5 font-semibold w-9">#</th>
                <th className="px-2 py-1.5 font-semibold">Học viên</th>
                <th className="px-2 py-1.5 font-semibold">CCCD</th>
                <th className="px-2 py-1.5 font-semibold">Trạng thái</th>
              </tr>
            </thead>
            <tbody>
              {items.map((it, idx) => {
                const t = trangThaiDong(it);
                return (
                  <tr key={it.uuid} className={"border-b border-border last:border-b-0 " + (t.k === "dang" ? "bg-accent" : "")}>
                    <td className="px-2 py-1.5 tabular-nums text-muted-foreground">{idx + 1}</td>
                    <td className="px-2 py-1.5 font-semibold">{it.ho_ten.toUpperCase() || "(chưa có tên)"}</td>
                    <td className="px-2 py-1.5 font-mono text-[12px] text-muted-foreground">{it.so_cmt}</td>
                    <td className="px-2 py-1.5">
                      {t.k === "ok" && <span className="inline-flex items-center gap-1 text-success font-medium"><Icon name="check" className="w-3.5 h-3.5" sw={3} /> {t.t}</span>}
                      {t.k === "loi" && <span className="inline-flex items-start gap-1 text-destructive font-medium"><Icon name="warn" className="w-3.5 h-3.5 mt-0.5 shrink-0" /> {t.t}</span>}
                      {t.k === "dang" && <span className="inline-flex items-center gap-1 text-primary font-medium"><Icon name="refresh" className="w-3.5 h-3.5 animate-spin" /> {t.t}</span>}
                      {t.k === "cho" && <span className="text-muted-foreground">{t.t}</span>}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Tiến độ */}
        {pha !== "xacnhan" && (
          <div className="mt-3 space-y-2">
            <div className="h-2.5 rounded-full bg-muted overflow-hidden">
              <div className="h-full bg-primary transition-all" style={{ width: `${pct}%` }} />
            </div>
            <div className="flex items-center justify-between text-[13px]">
              <span className="text-muted-foreground tabular-nums" data-testid="tien-do-nap">{Math.min(daXuLy, tongChay)}/{tongChay} · {pct}%</span>
              {pha === "chay" && <span className="inline-flex items-center gap-1 text-primary font-medium"><Icon name="refresh" className="w-3.5 h-3.5 animate-spin" /> đang nạp…</span>}
              {pha === "xong" && <span className="inline-flex items-center gap-1 text-success font-medium"><Icon name="check" className="w-3.5 h-3.5" sw={3} /> xong</span>}
            </div>
            {pha === "xong" && (
              <div className="flex gap-3 text-[12.5px]">
                <span className="text-success">Vào DB: <b className="tabular-nums">{okList.length}</b></span>
                <span className={loiList.length > 0 ? "text-destructive" : "text-muted-foreground"}>Lỗi: <b className="tabular-nums">{loiList.length}</b></span>
              </div>
            )}
          </div>
        )}
      </div>
      <div className="p-3 border-t border-border flex gap-2 flex-wrap shrink-0">
        {pha === "xacnhan" && (
          <>
            <button onClick={onDong} className="btn btn-secondary">Hủy</button>
            <button onClick={() => void chay(items)} className="ml-auto btn btn-primary">
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
              <button onClick={() => void napLaiLoi()} className="btn btn-secondary">
                <Icon name="refresh" className="w-4 h-4" /> Nạp lại {loiList.length} lỗi
              </button>
            )}
            {okMaDks.length > 0 && (
              <button onClick={() => onXemDB(okMaDks)} className="btn btn-secondary">
                <Icon name="db" className="w-4 h-4" /> Xem trong DB
              </button>
            )}
            {okThieuAnh > 0 && (
              <button onClick={onBoSungAnh} className="btn border border-warning/50 bg-white text-warning hover:bg-warning/10">
                <Icon name="imageOff" className="w-4 h-4" /> Bổ sung ảnh ({okThieuAnh})
              </button>
            )}
            <button onClick={onDong} className="ml-auto btn btn-primary">Xong</button>
          </>
        )}
      </div>
    </>
  );

  if (docked) return <div className="h-full flex flex-col min-h-0 bg-card">{noiDung}</div>;
  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={(e) => { if (e.target === e.currentTarget && pha !== "chay") onDong(); }}>
      <div className="bg-card w-full max-w-lg rounded-xl shadow-2xl max-h-[90vh] flex flex-col overflow-hidden">{noiDung}</div>
    </div>
  );
}

// NAP-01: Tool kéo hàng đợi VPS → staging + nạp lô (chế độ Nạp). Tra cứu DB = QLY-01 (task 22, stub).
export default function NapHoSo() {
  const navigate = useNavigate();

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
  // Cờ NHẸ cho 2 chip cả lưới (co_dia_chi/co_anh/co_tick) — nháp bền task 51 (không tải ảnh).
  const [nhapCoMap, setNhapCoMap] = useState<Record<string, NhapCo>>({});
  const [xacNhanXoaNhap, setXacNhanXoaNhap] = useState(false); // nút "Xóa nháp" — xác nhận 2 bước inline
  // NAP-01 #51 — "Bỏ khỏi hàng đợi" 1 hay nhiều dòng: panel xác nhận 2 bước + thông báo kết quả
  const [boXn, setBoXn] = useState<{ uuids: string[]; nhan: string } | null>(null);
  const [boTb, setBoTb] = useState("");

  // Danh sách Sở GTVT cho combobox "Nơi cấp" (BUG-10) — tải 1 lần
  const [soGtvt, setSoGtvt] = useState<SoGtvt[]>([]);
  useEffect(() => { getSoGtvt().then(setSoGtvt).catch(() => {}); }, []);

  // Giấy tờ mặc định theo khóa + ảnh + modal
  const [giayTo, setGiayTo] = useState<GiayTo[]>([]);
  const [anhUrl, setAnhUrl] = useState<string | null>(null);
  const [anhOpen, setAnhOpen] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false); // task 46 — ngăn "Chuẩn bị" trượt từ phải (chỉ màn hẹp)
  const rong = useRong(1024); // màn rộng: ngăn Chuẩn bị luôn mở bên phải (≈60%)
  const [loDangChay, setLoDangChay] = useState(false); // đang nạp lô: khóa các nút thay đổi hàng đợi

  // Nạp lô
  const [napBusy, setNapBusy] = useState(false);
  const [napErr, setNapErr] = useState("");

  // Task 47 — dialog nạp 3 pha + "Xem trong DB"
  const [napDialog, setNapDialog] = useState<{ items: NapIn[]; boQua: number } | null>(null);
  const [napKhoa, setNapKhoa] = useState<Record<string, string>>({}); // uuid → mã khóa đã nạp (cho "Xem trong DB" dòng đã nạp)

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

  // ── Tải danh sách chờ nạp mỗi khi mở màn Nạp ──
  // BUG-03: "Gỡ về chờ nạp" nằm ở Tra cứu DB (route khác) → đưa dòng về 'cho' ở kho cục bộ.
  // Nạp & Tra cứu nay là 2 route riêng → chuyển tab là unmount/mount lại màn Nạp, effect này
  // chạy lại mỗi lần quay về → HV vừa gỡ hiện NGAY (PRD QLY-08). Chỉ đọc SQLite cục bộ, KHÔNG gọi VPS.
  useEffect(() => {
    getDanhSachKeoVe().then((ds) => { setKeoVe(ds); taiCoNhap(ds); }).catch(() => setKeoVe([]));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Tải cờ nháp NHẸ cho các dòng chưa nạp (vẽ 2 chip) — không kèm ảnh (TDD §10.5, task 51).
  const taiCoNhap = (ds: KeoVeRow[]) => {
    const ids = ds.filter((r) => r.trang_thai !== "xong").map((r) => r.uuid);
    nhapCo(ids)
      .then((cs) => setNhapCoMap((m) => { const n = { ...m }; for (const c of cs) n[c.uuid] = c; return n; }))
      .catch(() => {});
  };

  // Task 46 polish — khóa cuộn trang nền khi mở ngăn "Chuẩn bị" dạng phủ (màn hẹp).
  useEffect(() => {
    if (!drawerOpen || rong) return;
    const cu = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = cu; };
  }, [drawerOpen, rong]);

  // Cảnh báo khi rời/đóng tab giữa lúc đang nạp lô.
  useEffect(() => {
    if (!loDangChay) return;
    const f = (e: BeforeUnloadEvent) => { e.preventDefault(); e.returnValue = ""; };
    window.addEventListener("beforeunload", f);
    return () => window.removeEventListener("beforeunload", f);
  }, [loDangChay]);

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
      const moi = await getDanhSachKeoVe();
      // BUG-04: collector sửa địa chỉ trên app → raw đổi khi kéo lại → reset nháp địa chỉ đã map cũ
      // (map lại từ raw mới), giữ giấy tờ/ảnh. So raw cũ (keoVe hiện tại) ↔ raw mới (moi).
      const rawCu = new Map(keoVe.map((r) => [r.uuid, r.noi_tt_raw]));
      setNhap((prev) => lamTuoiNhapDiaChi(prev, rawCu, moi));
      setKeoVe(moi);
      taiCoNhap(moi); // backend đã reset địa chỉ nháp (BUG-04) → tải lại cờ cho chip đúng
      const phan = [`${kq.keo_ve} hồ sơ mới`];
      if (kq.lam_tuoi > 0) phan.push(`làm tươi ${kq.lam_tuoi} hồ sơ chờ nạp`);
      if (kq.bo_da_xoa > 0) phan.push(`bỏ ${kq.bo_da_xoa} hồ sơ đã xóa ở app`);
      if (kq.dia_chi_reset > 0) phan.push(`⚠ ${kq.dia_chi_reset} hồ sơ đổi địa chỉ — cần map lại`);
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

  // Cờ 2 chip (Địa chỉ/Ảnh) của 1 dòng: ưu tiên nháp RAM (nếu đã mở/sửa phiên này), else cờ nhẹ từ backend.
  const coChip = (uuid: string) => {
    const n = nhap[uuid];
    const f = nhapCoMap[uuid];
    return {
      diaChi: n ? n.diaChi != null : !!f?.co_dia_chi,
      anh: n ? !!(n.jp2 || n.anhPreview) : !!f?.co_anh,
    };
  };

  // Mở ngăn Chuẩn bị cho 1 HV: chọn dòng + trượt ngăn phải + NẠP NHÁP BỀN đầy đủ (kèm ảnh) từ backend.
  const moChuanBi = async (uuid: string) => {
    setSelUuid(uuid);
    if (!rong) setDrawerOpen(true);
    setXacNhanXoaNhap(false);
    try {
      const d = await nhapDoc(uuid);
      const co = d.dia_chi_json || d.chi_tiet || d.jp2_b64 || d.anh_preview || d.tick_json || d.noi_cap || d.ngay_cap;
      if (!co) return; // chưa có nháp bền → để prefill client (NAP-03) lo ô chi tiết
      setNhap((prev) => {
        const cu = prev[uuid];
        let diaChi = cu?.diaChi ?? null;
        let tick = cu?.tick ?? null;
        try { if (d.dia_chi_json) diaChi = JSON.parse(d.dia_chi_json); } catch { /* giữ cũ */ }
        try { if (d.tick_json) tick = JSON.parse(d.tick_json); } catch { /* giữ cũ */ }
        return { ...prev, [uuid]: {
          diaChi,
          chiTiet: d.chi_tiet ?? cu?.chiTiet ?? "",
          noiCap: d.noi_cap ?? cu?.noiCap,
          // ngay_cap nháp lưu yyyymmdd → đổi sang dd/mm/yyyy để hiện; chưa đặt thì để undefined (drawer prefill từ gốc).
          ngayCap: d.ngay_cap ? ymdToVN(d.ngay_cap) : cu?.ngayCap,
          jp2: d.jp2_b64 ?? cu?.jp2 ?? null,
          anhPreview: d.anh_preview ?? cu?.anhPreview ?? null,
          tick,
        } };
      });
    } catch { /* chưa có nháp / lỗi mạng → dùng prefill client */ }
  };

  // Lưu nháp bền (upsert) của 1 HV — dùng khi chuyển HV khác, đóng ngăn phủ, hoặc rời trang.
  // Lưu lỗi mạng thì giữ bản RAM, thử lại lần sau.
  const luuNhapHv = async (uuid: string | null) => {
    const n = uuid ? nhap[uuid] : undefined;
    if (!uuid || !n) return;
    try {
      await nhapLuu(uuid, goiNhap(n));
      setNhapCoMap((m) => ({ ...m, [uuid]: {
        uuid, co_dia_chi: n.diaChi != null, co_anh: !!(n.jp2 || n.anhPreview),
        co_tick: n.tick != null ? n.tick.length > 0 : true,
      } }));
    } catch { /* giữ RAM, lần lưu sau thử lại */ }
  };

  // Đóng ngăn phủ (màn hẹp) → LƯU nháp bền rồi đóng.
  const luuVaDong = async () => {
    await luuNhapHv(selUuid);
    setXacNhanXoaNhap(false);
    setDrawerOpen(false);
  };

  // Chọn 1 HV ở danh sách: lưu nháp của HV đang xem (không chờ mạng) rồi hiện dữ liệu HV mới.
  const chonHv = async (uuid: string) => {
    if (uuid === selUuid) { if (!rong) setDrawerOpen(true); return; }
    void luuNhapHv(selUuid);
    const r = keoVe.find((x) => x.uuid === uuid);
    if (r && r.trang_thai === "xong") { setSelUuid(uuid); setXacNhanXoaNhap(false); return; }
    await moChuanBi(uuid);
  };

  // Rời trang (đổi tab/phân hệ): lưu nháp HV đang xem — ngăn không còn nút "Đóng" để lưu như trước.
  const moiNhat = useRef({ selUuid, nhap });
  moiNhat.current = { selUuid, nhap };
  useEffect(() => () => {
    const { selUuid: u, nhap: ns } = moiNhat.current;
    const n = u ? ns[u] : undefined;
    if (u && n) void nhapLuu(u, goiNhap(n)).catch(() => {});
  }, []);

  // Nút "Xóa nháp" — dọn nháp (gồm ảnh PII) của HV đang mở, cả backend lẫn RAM (TDD-decisions §11).
  const xoaNhap = async () => {
    const uuid = selUuid;
    if (!uuid) return;
    try { await nhapXoa(uuid); } catch { /* lỗi mạng — vẫn dọn RAM */ }
    setNhap((prev) => { const n = { ...prev }; delete n[uuid]; return n; });
    setNhapCoMap((m) => { const x = { ...m }; delete x[uuid]; return x; });
    setXacNhanXoaNhap(false);
    setDrawerOpen(false);
  };

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
      // Ngày cấp (#43): ưu tiên bản operator sửa (dd/mm/yyyy→yyyymmdd); ô rỗng → quay về gốc keo_ve.ngay_cap.
      ngay_cap_cmt: vnToYmd(n.ngayCap ?? "") || r.ngay_cap || undefined,
      // nơi cấp: operator chọn tay > suy từ CCCD ('00' Cục QLHC); rỗng thì backend tự suy.
      // (Bỏ r.noi_cap_cccd: là TEXT "Cục QLHC…" không phải mã → nhét vào cột mã sẽ sai.)
      noi_cap_cmt: n.noiCap || suyNoiCap(r.so_cccd) || undefined,
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

  // Task 47 — nhảy sang route Tra cứu DB, mở khóa đích + làm nổi HV vừa nạp.
  // Gộp 3 tab 1 hàng: Tra cứu là route riêng → truyền tham số qua router state (TraCuuDBPage đọc lại).
  // CHANGES #32: locAnh="chua" → mở sẵn bộ lọc "chưa ảnh" để bổ sung ảnh HV vừa nạp thiếu ảnh.
  const xemTrongDB = (maKh: string, maDks: string[], locAnh?: "all" | "chua" | "roi") => {
    navigate("/tool/tra-cuu", { state: { maKh, maDks, nonce: Date.now(), locAnh } });
  };

  // NAP-01 task 38 — nạp lại nhanh dòng lỗi (tái dùng nạp lô 1 uuid).
  const napLaiNhanh = (r: KeoVeRow) => { void chayNapLo([r]); };

  // NAP-01 #51 — "Bỏ khỏi hàng đợi" áp MỌI trạng thái qua 1 đường POST /bo-qua (dòng chờ/lỗi ghi
  // "bỏ qua" tombstone nên kéo lại không về). Mở panel xác nhận 2 bước TRƯỚC khi gọi API.
  const xinBoDong = (r: KeoVeRow) => {
    setBoTb("");
    setBoXn({ uuids: [r.uuid], nhan: (r.ho_ten || "").toUpperCase() || r.so_cccd || "1 hồ sơ" });
  };
  const xinBoNhieu = () => {
    if (chon.size === 0) return;
    setBoTb("");
    setBoXn({ uuids: [...chon], nhan: `${chon.size} hồ sơ` });
  };
  const boDong = async () => {
    if (!boXn) return;
    const uuids = boXn.uuids;
    setNapErr("");
    try {
      const kq = await boKhoiHangDoi(uuids);
      setKeoVe(await getDanhSachKeoVe());
      setChon((prev) => { const n = new Set(prev); for (const u of uuids) n.delete(u); return n; });
      if (selUuid && uuids.includes(selUuid)) { setSelUuid(null); setDrawerOpen(false); }
      setBoXn(null);
      setBoTb(
        `Đã bỏ ${kq.bo} hồ sơ khỏi hàng đợi` +
          (kq.tombstone > 0 ? ` · nhớ "bỏ qua" ${kq.tombstone} hồ sơ (kéo lại không mang về)` : "") + ".",
      );
    } catch (e) {
      setNapErr(e instanceof Error ? e.message : "Không bỏ được khỏi hàng đợi.");
      setBoXn(null);
    }
  };

  const chonSanSang = daLoc.canXuly.filter((r) => chon.has(r.uuid) && rowSanSang(r));
  const selRow = keoVe.find((r) => r.uuid === selUuid) ?? null;
  const tongCanXuly = daLoc.canXuly.length;
  const soChon = daLoc.canXuly.filter((r) => chon.has(r.uuid)).length;
  const soThieuChon = soChon - chonSanSang.length;
  const soSanSangTat = daLoc.canXuly.filter(rowSanSang).length;
  const chonTatCa = () =>
    setChon((prev) => {
      if (tongCanXuly > 0 && soChon === tongCanXuly) {
        const n = new Set(prev);
        for (const r of daLoc.canXuly) n.delete(r.uuid);
        return n;
      }
      return new Set([...prev, ...daLoc.canXuly.map((r) => r.uuid)]);
    });

  // Màn rộng: ngăn phải luôn có dữ liệu — tự chọn HV đầu tiên của nhóm đang xem khi chưa có HV nào được chọn
  // (hoặc HV đang xem đã rời nhóm: nạp xong, bỏ khỏi hàng đợi, đổi tab).
  useEffect(() => {
    if (!rong || loDangChay) return;
    if (rows.length === 0) { if (selUuid) setSelUuid(null); return; }
    if (!selUuid || !rows.some((r) => r.uuid === selUuid)) void chonHv(rows[0].uuid);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rong, rows, selUuid, loDangChay]);

  // ↑/↓ chuyển nhanh giữa các học viên của trang đang xem.
  const phimDanhSach = (e: React.KeyboardEvent) => {
    if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
    const t = e.target as HTMLElement;
    if (t.tagName === "INPUT" && (t as HTMLInputElement).type !== "checkbox") return;
    const i = rowsTrang.findIndex((r) => r.uuid === selUuid);
    const k = e.key === "ArrowDown" ? Math.min(rowsTrang.length - 1, i + 1) : Math.max(0, i - 1);
    if (rowsTrang[k] && rowsTrang[k].uuid !== selUuid) { e.preventDefault(); void chonHv(rowsTrang[k].uuid); }
  };

  // Ngăn Chuẩn bị (dùng cả khi ghim bên phải lẫn khi phủ ở màn hẹp).
  const nganChuanBi = selRow ? (
    <div className="h-full flex flex-col min-h-0">
                <div className="px-4 py-3 border-b border-border flex items-center justify-between shrink-0">
                  <h3 className="text-sm font-bold">Chuẩn bị hồ sơ</h3>
                  <div className="flex items-center gap-2">
                    <NapBadge tt={selRow.trang_thai} />
                    {!rong && (
                      <button onClick={() => void luuVaDong()} aria-label="Đóng (lưu nháp)" className="text-muted-foreground hover:text-foreground">
                        <Icon name="x" className="w-5 h-5" />
                      </button>
                    )}
                  </div>
                </div>
                <>
                  <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-0">
                    <div className="grid grid-cols-[148px_minmax(0,1fr)] gap-3 items-start">
                    {/* Ảnh chân dung — LÊN ĐẦU, thu gọn, căn giữa (task 46 polish); NAP-04 + ảnh gốc (task 45) */}
                    <div className="rounded-lg border border-border bg-card p-3">
                      <div className="aspect-[3/4] w-[104px] mx-auto rounded-lg bg-white border border-input flex items-center justify-center relative overflow-hidden shadow-sm">
                        {layNhap(selRow.uuid).anhPreview ? (
                          <>
                            <img src={layNhap(selRow.uuid).anhPreview!} alt="Ảnh đã chỉnh (nền trắng)" className="w-full h-full object-cover" />
                            <span className="absolute top-1 left-1 text-[9px] bg-success text-white px-1 py-0.5 rounded">.jp2</span>
                          </>
                        ) : layNhap(selRow.uuid).jp2 ? (
                          <>
                            <Icon name="check" className="w-10 h-10 text-success/50" />
                            <span className="absolute top-1 left-1 text-[9px] bg-success text-white px-1 py-0.5 rounded">.jp2</span>
                          </>
                        ) : anhUrl ? (
                          <img src={anhUrl} alt="Ảnh thô từ VPS" className="w-full h-full object-cover" />
                        ) : (
                          <Icon name="user" className="w-10 h-10 text-muted-foreground/40" sw={1.5} />
                        )}
                      </div>
                      <p className="text-[11px] text-muted-foreground text-center mt-2">
                        {selRow.co_anh
                          ? "Ảnh thô — chỉnh crop 3:4 + nền trắng để xuất .jp2"
                          : "Không ảnh — vẫn nạp được (BR-011)"}
                      </p>
                      <div className="flex justify-center mt-2">
                        <button
                          onClick={() => setAnhOpen(true)}
                          title="Mở trình chỉnh ảnh chân dung (crop 3:4, nền trắng, xuất .jp2)"
                          className="btn btn-primary btn-row h-auto min-h-8 py-1.5 whitespace-normal text-center leading-tight"
                        >
                          <Icon name="camera" className="w-4 h-4 shrink-0" /> Sửa ảnh chân dung
                        </button>
                      </div>
                    </div>

                    {/* Tóm tắt học viên */}
                    <div className="rounded-md bg-secondary/70 border border-border px-2.5 py-2 text-[12px] leading-relaxed">
                      <div className="font-bold text-[14px]">{(selRow.ho_ten || "").toUpperCase() || "(chưa có tên)"}</div>
                      <div className="text-muted-foreground mt-0.5">
                        {selRow.gioi_tinh === "F" ? "Nữ" : "Nam"} · CCCD {selRow.so_cccd || selRow.so_cmnd_cu || "—"}
                        {selRow.ngay_sinh && <> · NS {ymdToVN(selRow.ngay_sinh)}</>}
                      </div>
                      <div className="text-muted-foreground">Địa chỉ gốc: {selRow.noi_tt_raw || "—"}</div>
                      {nghiSaiChinhTa(selRow.ho_ten || "") && (
                        <div className="mt-1 text-warning font-medium flex items-center gap-1">
                          <Icon name="warn" className="w-3.5 h-3.5" /> Tên nghi sai chính tả ({nghiSaiChinhTa(selRow.ho_ten || "")}) — sửa trên VPS nếu cần.
                        </div>
                      )}
                    </div>

                    {/* NAP-03: map địa chỉ nơi thường trú — chiếm cả bề ngang để nút đủ chữ */}
                    <div className="col-span-2">
                      <label className="field-label mb-1 block">
                        Nơi thường trú <span className="text-destructive">*</span>{" "}
                        <span className="text-muted-foreground font-normal">(map/chọn tay để lấy đúng mã DVHC)</span>
                      </label>
                      <AddressCombo key={selRow.uuid} diaChiGoc={selRow.noi_tt_raw ?? ""} onChon={(dc) => capNhatNhap(selRow.uuid, { diaChi: dc })} />
                      {layNhap(selRow.uuid).diaChi && (
                        <div className="mt-1.5 text-[11px] text-success font-medium flex items-center gap-1">
                          <Icon name="check" className="w-3.5 h-3.5" sw={3} /> Đã map:{" "}
                          {[layNhap(selRow.uuid).chiTiet.trim(), layNhap(selRow.uuid).diaChi!.ten_xa, layNhap(selRow.uuid).diaChi!.ten_tinh]
                            .filter(Boolean)
                            .join(", ")}{" "}
                          (mã {layNhap(selRow.uuid).diaChi!.ma_dvhc})
                        </div>
                      )}
                      <input
                        className="field-input mt-2"
                        value={layNhap(selRow.uuid).chiTiet}
                        onChange={(e) => capNhatNhap(selRow.uuid, { chiTiet: e.target.value })}
                        placeholder="Chi tiết (số nhà/thôn) — không bắt buộc"
                      />
                    </div>

                    </div>

                    {/* Ngày cấp + Nơi cấp căn cước — điền sẵn từ hồ sơ VPS, operator sửa được (CHANGES #43) */}
                    <div className="rounded-lg border border-border bg-card p-4 space-y-3">
                      {/* Ngày cấp CCCD — ô ODate dd/mm/yyyy, điền sẵn keo_ve.ngay_cap, sửa được; rỗng → nạp dùng ngày gốc */}
                      <ODate
                        label={<>Ngày cấp căn cước <span className="text-[11px] font-normal text-muted-foreground">(điền sẵn từ hồ sơ — sửa nếu cần)</span></>}
                        value={layNhap(selRow.uuid).ngayCap ?? ymdToVN(selRow.ngay_cap)}
                        onChange={(v) => capNhatNhap(selRow.uuid, { ngayCap: v })}
                        max={new Date().toISOString().slice(0, 10)}
                      />
                      {/* Nơi cấp — mã DM_DVHC, tự suy từ CCCD ('00' Cục QLHC), sửa được (BUG-10/#40) */}
                      <div>
                        <label className="field-label">
                          Nơi cấp căn cước{" "}
                          <span className="text-[11px] font-normal text-muted-foreground">(tự suy từ số CCCD — sửa nếu sai)</span>
                        </label>
                        {(() => {
                          // Combobox gõ-để-tìm (ComboLoc) — dùng chung với ô Nơi cấp ở Tra cứu DB (TraCuuDB).
                          // Bền hóa #43: suy ra '00' Cục QLHC mà danh mục nguồn thiếu mã '00' (máy chưa chạy
                          // script đồng bộ DM_DVHC #40) → tự chèn '00' vào đầu options để luôn hiển thị + tìm được.
                          const noiCapVal = layNhap(selRow.uuid).noiCap ?? suyNoiCap(selRow.so_cccd);
                          const thieu00 = noiCapVal === "00" && !soGtvt.some((s) => s.ma === "00");
                          const opts = (thieu00 ? [{ ma: "00", ten: "Cục QLHC" }] : []).concat(
                            soGtvt.map((s) => ({ ma: s.ma, ten: s.ten })),
                          );
                          return (
                            <ComboLoc
                              className="mt-1"
                              value={noiCapVal}
                              options={opts}
                              onChon={(ma) => capNhatNhap(selRow.uuid, { noiCap: ma })}
                              placeholder="Gõ Cục QLHC hoặc tên tỉnh…"
                            />
                          );
                        })()}
                      </div>
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

                  <div className="p-3 border-t border-border shrink-0 space-y-2">
                    {/* Task 51 — "Xóa nháp": dọn chuẩn bị (gồm ảnh PII) của HV này (TDD-decisions §11) */}
                    {selRow.trang_thai !== "xong" && (
                      xacNhanXoaNhap ? (
                        <div className="flex items-center gap-2 text-[12px]">
                          <span className="text-muted-foreground flex-1">Xóa nháp đã chuẩn bị (địa chỉ, ảnh, giấy tờ)?</span>
                          <button
                            onClick={() => void xoaNhap()}
                            className="h-8 px-3 rounded-lg bg-destructive text-white font-semibold hover:brightness-110 transition-colors"
                          >
                            Xóa nháp
                          </button>
                          <button
                            onClick={() => setXacNhanXoaNhap(false)}
                            className="h-8 px-3 rounded-lg border border-border font-semibold hover:bg-muted transition-colors"
                          >
                            Hủy
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => setXacNhanXoaNhap(true)}
                          title="Xóa nháp đã chuẩn bị (địa chỉ, ảnh, giấy tờ) của học viên này"
                          className="w-full h-9 rounded-lg border border-border text-muted-foreground text-[13px] font-semibold whitespace-nowrap inline-flex items-center justify-center gap-1.5 hover:text-destructive hover:border-destructive/40 hover:bg-destructive/5 transition-colors"
                        >
                          <Icon name="x" className="w-3.5 h-3.5" /> Xóa nháp
                        </button>
                      )
                    )}
                    <button
                      onClick={() => { void chayNapLo([selRow]); }}
                      disabled={napBusy || !rowSanSang(selRow) || !khoa}
                      title="Nạp riêng học viên này vào khóa đích"
                      className="w-full btn btn-primary h-auto min-h-9 py-2 whitespace-normal text-center leading-tight"
                    >
                      <Icon name={napBusy ? "refresh" : "plus"} className={"w-4 h-4" + (napBusy ? " animate-spin" : "")} />
                      {selRow.trang_thai === "xong"
                        ? "Đã nạp"
                        : !layNhap(selRow.uuid).diaChi
                          ? "Map địa chỉ để nạp"
                          : khoa
                            ? `Nạp học viên này vào khóa ${khoa.ma_kh} — ${khoa.ten_kh}`
                            : "Chọn khóa để nạp"}
                    </button>
                  </div>
                </>
    </div>
  ) : null;

  // Nạp lô xong (dùng cho cả ngăn phải lẫn hộp thoại ở màn hẹp): làm tươi staging + dọn nháp đã nạp.
  const xongNapLo = async (okRows: { uuid: string; ma_dk: string }[]) => {
    if (!khoa) return;
            const fresh = await getDanhSachKeoVe();
            setKeoVe(fresh);
            setChon(new Set());
            ghiNapKhoa(okRows.map((o) => o.uuid), khoa.ma_kh);
            // Nạp xong → backend đã xóa nháp bền (task 50). Dọn RAM cho khớp + tải lại cờ.
            const ids = new Set(okRows.map((o) => o.uuid));
            setNhap((prev) => { const n = { ...prev }; for (const id of ids) delete n[id]; return n; });
            taiCoNhap(fresh);
            setDrawerOpen(false);
  };

  return (
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
              disabled={keoBusy || loDangChay}
              className="ml-auto btn btn-secondary"
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

          {/* Chia đôi: DANH SÁCH gọn (≈40%) | NGĂN CHUẨN BỊ luôn mở (≈60%). Màn hẹp: chỉ danh sách + ngăn phủ. */}
          <div className="p-4 flex flex-col gap-3 h-[calc(100svh-9.5rem)] min-h-0">
            <div className={"flex-1 min-h-0 grid gap-4 grid-rows-[minmax(0,1fr)] " + (rong ? "grid-cols-[1fr_1fr]" : "grid-cols-1")}>
              {/* ── Trái: danh sách ── */}
              <div className="list-frame flex flex-col min-h-0 min-w-0">
                <div className="px-3 py-2.5 flex items-center gap-2 border-b border-border shrink-0">
                  <div className="inline-flex rounded-lg border border-border overflow-hidden" role="group" aria-label="Lọc hàng đợi">
                    <button
                      onClick={() => setNapFilter("canxuly")}
                      aria-pressed={napFilter === "canxuly"}
                      className={"inline-flex items-center gap-1.5 h-8 px-3 text-[12.5px] font-semibold transition-colors " + (napFilter === "canxuly" ? "bg-accent text-primary" : "bg-white text-muted-foreground hover:bg-muted")}
                    >
                      <Icon name="clock" className="w-4 h-4" /> Cần xử lý <span className="text-[11px] bg-primary/10 rounded-full px-1.5">{daLoc.canXuly.length}</span>
                    </button>
                    <button
                      onClick={() => setNapFilter("danap")}
                      aria-pressed={napFilter === "danap"}
                      className={"inline-flex items-center gap-1.5 h-8 px-3 text-[12.5px] font-semibold transition-colors " + (napFilter === "danap" ? "bg-success/10 text-success" : "bg-white text-muted-foreground hover:bg-muted")}
                    >
                      <Icon name="check" className="w-4 h-4" /> Đã nạp <span className="text-[11px] bg-success/15 text-success rounded-full px-1.5">{daLoc.daNap.length}</span>
                    </button>
                  </div>

                  {/* Ô tìm — màn hẹp thu gọn nút kính lúp (CHANGES #10) */}
                  <div className="flex items-center gap-2 ml-auto min-w-0 flex-1 justify-end">
                    <button
                      onClick={() => setQOpen((v) => !v)}
                      aria-label="Tìm kiếm"
                      className="sm:hidden w-9 h-9 rounded-lg border border-border flex items-center justify-center text-muted-foreground hover:text-foreground"
                    >
                      <Icon name="search" className="w-4 h-4" />
                    </button>
                    <div className={(qOpen ? "flex" : "hidden") + " sm:flex relative min-w-0 flex-1 max-w-[220px]"}>
                      <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground">
                        <Icon name="search" className="w-4 h-4" />
                      </span>
                      <input
                        className="field-input pl-8"
                        value={q}
                        onChange={(e) => setQ(e.target.value)}
                        placeholder="Tìm tên (không dấu) / CCCD"
                      />
                    </div>
                  </div>
                </div>


                {/* Chọn tất cả + số lượng (chỉ nhóm Cần xử lý) */}
                {napFilter === "canxuly" && (
                  <div className="px-3 py-2 border-b border-border bg-muted/30 shrink-0 flex items-center gap-x-3 gap-y-1 flex-wrap text-[12.5px]">
                    <label className="inline-flex items-center gap-2 font-semibold cursor-pointer whitespace-nowrap">
                      <input
                        type="checkbox"
                        aria-label="Chọn tất cả học viên trong danh sách"
                        ref={(el) => { if (el) el.indeterminate = soChon > 0 && soChon < tongCanXuly; }}
                        checked={tongCanXuly > 0 && soChon === tongCanXuly}
                        disabled={tongCanXuly === 0 || loDangChay}
                        onChange={chonTatCa}
                        className="accent-primary w-4 h-4"
                      />
                      Chọn tất cả ({tongCanXuly})
                    </label>
                    <span className="text-muted-foreground tabular-nums whitespace-nowrap" data-testid="dem-chon">
                      Chọn <b className="text-primary">{soChon}</b>/{tongCanXuly} · Sẵn sàng <b className="text-success">{chonSanSang.length}</b>
                      {soThieuChon > 0 && <> · Thiếu <b className="text-warning">{soThieuChon}</b></>}
                    </span>
                    <button
                      type="button"
                      onClick={chonTatCaSanSang}
                      disabled={soSanSangTat === 0 || loDangChay}
                      title={`Chỉ tích ${soSanSangTat} học viên đủ địa chỉ + giấy tờ`}
                      className="ml-auto btn btn-secondary btn-row"
                    >
                      Chỉ sẵn sàng
                    </button>
                  </div>
                )}

              {/* Banners lỗi/chính tả (chỉ nhóm Cần xử lý) */}
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

                {/* NAP-01 #51 — thông báo kết quả "Bỏ khỏi hàng đợi" (có thể bỏ ở cả 2 nhóm) */}
                {boTb && (
                  <div className="mx-4 mt-3 flex items-center gap-2 text-[13px] font-medium text-success bg-success/10 border border-success/30 rounded-lg px-3 py-2 shrink-0">
                    <Icon name="check" className="w-4 h-4 shrink-0" /> {boTb}
                    <button type="button" onClick={() => setBoTb("")} className="ml-auto text-muted-foreground hover:text-foreground">
                      <Icon name="x" className="w-4 h-4" />
                    </button>
                  </div>
                )}

                {/* rows — chỉ cột này cuộn; ↑/↓ chuyển học viên */}
                <div className="flex-1 overflow-y-auto min-h-0" tabIndex={0} onKeyDown={phimDanhSach} role="list" aria-label="Danh sách hồ sơ kéo về">
                  {rowsTrang.map((r) => {
                    const chinhTa = nghiSaiChinhTa(r.ho_ten || "");
                    const tenIn = (r.ho_ten || "").toUpperCase(); // IN HOA giữ dấu
                    const c = coChip(r.uuid);
                    const thieuGiayTo = tinhSanSang(r).thieu.includes("giấy tờ");
                    const mk = napKhoa[r.uuid] ?? khoa?.ma_kh;
                    return (
                      <div
                        key={r.uuid}
                        role="listitem"
                        data-testid={`hv-${r.uuid}`}
                        onClick={() => void chonHv(r.uuid)}
                        className={"lrow flex items-center gap-2 px-3 h-[54px] cursor-pointer whitespace-nowrap " + (selUuid === r.uuid ? "sel bg-accent" : "hover:bg-accent/50")}
                      >
                        {r.trang_thai !== "xong" ? (
                          <input
                            type="checkbox"
                            aria-label={`Chọn ${tenIn || r.uuid}`}
                            checked={chon.has(r.uuid)}
                            disabled={loDangChay}
                            onChange={() => toggleChon(r.uuid)}
                            onClick={(e) => e.stopPropagation()}
                            className="accent-primary w-4 h-4 shrink-0"
                          />
                        ) : (
                          <span className="w-4 shrink-0" />
                        )}
                        <div className="min-w-0 flex-1">
                          <div className="font-semibold text-[13px] truncate flex items-center gap-1">
                            <span className="truncate">{tenIn || <span className="text-muted-foreground font-normal">(chưa có tên)</span>}</span>
                            {chinhTa && <span title={`Nghi sai chính tả: ${chinhTa}`} className="shrink-0 text-warning"><Icon name="warn" className="w-3.5 h-3.5" /></span>}
                          </div>
                          <div className="text-[11.5px] text-muted-foreground truncate">
                            {r.trang_thai === "loi" && r.loi ? (
                              <span className="text-destructive font-medium" title={r.loi}>{r.loi}</span>
                            ) : r.trang_thai === "xong" && r.so_ho_so ? (
                              <span className="text-success font-medium">HS {r.so_ho_so} · {r.ma_dk}</span>
                            ) : (
                              <>{r.so_cccd || r.so_cmnd_cu || "—"} · {r.noi_tt_raw || "—"}</>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-1 shrink-0">
                          {r.trang_thai !== "xong" && (
                            <>
                              <span
                                title={c.diaChi ? "Đã map địa chỉ 2 cấp" : "Chưa map địa chỉ"}
                                className={"inline-grid place-items-center h-5 px-1 rounded text-[10px] font-bold " + (c.diaChi ? "text-success bg-success/10" : "text-muted-foreground bg-muted")}
                              >
                                ĐC
                              </span>
                              <span
                                title={c.anh ? "Có hình" : "Chưa có hình"}
                                className={"inline-grid place-items-center w-5 h-5 rounded " + (c.anh ? "text-success bg-success/10" : "text-muted-foreground bg-muted")}
                              >
                                <Icon name={c.anh ? "image" : "imageOff"} className="w-3 h-3" />
                              </span>
                              {thieuGiayTo && (
                                <span title="Chưa chọn giấy tờ" className="inline-grid place-items-center w-5 h-5 rounded text-warning bg-warning/10">
                                  <Icon name="warn" className="w-3 h-3" />
                                </span>
                              )}
                            </>
                          )}
                          <NapBadge tt={r.trang_thai} gon />
                          {r.trang_thai === "loi" && (
                            <button
                              type="button"
                              title="Nạp lại nhanh"
                              aria-label={`Nạp lại ${tenIn}`}
                              disabled={napBusy || loDangChay || !rowSanSang(r)}
                              onClick={(e) => { e.stopPropagation(); napLaiNhanh(r); }}
                              className="w-7 h-7 rounded-lg inline-flex items-center justify-center text-primary hover:bg-accent transition-colors disabled:opacity-45 disabled:cursor-not-allowed"
                            >
                              <Icon name="refresh" className={"w-4 h-4" + (napBusy ? " animate-spin" : "")} />
                            </button>
                          )}
                          {r.trang_thai === "xong" && r.ma_dk && (
                            <button
                              type="button"
                              title="Xem học viên này trong DB"
                              aria-label={`Xem ${tenIn} trong DB`}
                              disabled={!mk}
                              onClick={(e) => { e.stopPropagation(); if (mk) xemTrongDB(mk, [r.ma_dk!]); }}
                              className="w-7 h-7 rounded-lg inline-flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted transition-colors disabled:opacity-45"
                            >
                              <Icon name="db" className="w-4 h-4" />
                            </button>
                          )}
                          <button
                            type="button"
                            title="Bỏ khỏi hàng đợi (không xóa khỏi DB)"
                            aria-label={`Bỏ ${tenIn} khỏi hàng đợi`}
                            disabled={loDangChay}
                            onClick={(e) => { e.stopPropagation(); xinBoDong(r); }}
                            className="w-7 h-7 rounded-lg inline-flex items-center justify-center text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors disabled:opacity-45"
                          >
                            <Icon name="x" className="w-4 h-4" />
                          </button>
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
              </div>

              {/* ── Phải: ngăn Chuẩn bị luôn mở / Nạp lô / Đã nạp (chỉ xem) ── */}
              {rong && (
                <aside className="list-frame flex flex-col min-h-0 min-w-0" aria-label="Ngăn chuẩn bị hồ sơ">
                  {napDialog && khoa ? (
                    <NapLoDialog
                      docked
                      khoa={khoa}
                      items={napDialog.items}
                      boQua={napDialog.boQua}
                      onPha={(p) => setLoDangChay(p === "chay")}
                      onDong={() => setNapDialog(null)}
                      onXong={xongNapLo}
                      onXemDB={(maDks) => { setNapDialog(null); xemTrongDB(khoa.ma_kh, maDks); }}
                      onBoSungAnh={() => { setNapDialog(null); xemTrongDB(khoa.ma_kh, [], "chua"); }}
                    />
                  ) : selRow && selRow.trang_thai === "xong" ? (
                    <div className="p-4 space-y-3">
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-bold flex-1 truncate">{(selRow.ho_ten || "").toUpperCase()}</h3>
                        <NapBadge tt={selRow.trang_thai} />
                      </div>
                      <div className="rounded-lg border border-border p-3 text-[13px] space-y-1">
                        <div>Số hồ sơ <b>{selRow.so_ho_so ?? "—"}</b> · MaDK <b className="font-mono">{selRow.ma_dk ?? "—"}</b></div>
                        <div className="text-muted-foreground">Khóa {napKhoa[selRow.uuid] ?? khoa?.ma_kh ?? "—"} · CCCD {selRow.so_cccd || selRow.so_cmnd_cu || "—"}</div>
                        <div className="text-[12px] text-muted-foreground">Hồ sơ đã nạp — dữ liệu chỉ đọc. Sửa ở Tra cứu DB.</div>
                      </div>
                      {selRow.ma_dk && (napKhoa[selRow.uuid] ?? khoa?.ma_kh) && (
                        <button type="button" className="btn btn-secondary"
                          onClick={() => xemTrongDB((napKhoa[selRow.uuid] ?? khoa?.ma_kh)!, [selRow.ma_dk!])}>
                          <Icon name="db" className="w-4 h-4" /> Xem trong DB
                        </button>
                      )}
                    </div>
                  ) : selRow ? (
                    nganChuanBi
                  ) : (
                    <div className="flex-1 grid place-items-center p-6 text-center text-[13px] text-muted-foreground">
                      <div>
                        <Icon name="user" className="w-10 h-10 mx-auto text-muted-foreground/40" sw={1.5} />
                        <p className="mt-2">Chọn một học viên ở danh sách bên trái để chuẩn bị hồ sơ.</p>
                        <p className="text-[12px] mt-1">Dùng ↑/↓ để chuyển nhanh.</p>
                      </div>
                    </div>
                  )}
                </aside>
              )}
            </div>

            {/* Thanh đáy: số đã chọn + bỏ khỏi hàng đợi + nạp lô */}
            {napFilter === "canxuly" && (
              <div className="shrink-0 flex items-center gap-3 flex-wrap rounded-xl border border-border bg-card px-4 py-2.5">
                <span className="text-[13px] tabular-nums">
                  Đã chọn <b>{soChon}</b> · sẵn sàng <b className="text-success">{chonSanSang.length}</b>
                  {soThieuChon > 0 && <span className="text-warning"> · {soThieuChon} chưa sẵn sàng (bỏ qua khi nạp)</span>}
                </span>
                <button
                  type="button"
                  onClick={xinBoNhieu}
                  disabled={chon.size === 0 || loDangChay}
                  title="Bỏ các hồ sơ đã chọn khỏi hàng đợi (không xóa khỏi DB)"
                  className="ml-auto btn btn-danger"
                >
                  <Icon name="x" className="w-4 h-4" /> Bỏ khỏi hàng đợi ({chon.size})
                </button>
                <button
                  onClick={() => moNapDialog(chonSanSang)}
                  disabled={napBusy || loDangChay || chonSanSang.length === 0 || !khoa}
                  className="btn btn-primary"
                >
                  <Icon name="plus" className="w-4 h-4" />
                  {`Nạp ${chonSanSang.length} học viên${khoa ? ` vào ${khoa.ten_kh} (${khoa.ma_kh})` : ""}`}
                </button>
              </div>
            )}
          </div>

          {/* NGĂN "CHUẨN BỊ" dạng phủ — chỉ màn hẹp (<1024px); màn rộng dùng ngăn cố định bên phải */}
          {!rong && drawerOpen && selRow && selRow.trang_thai !== "xong" && (
            <div className="fixed inset-0 z-40 flex justify-end">
              <div className="absolute inset-0 bg-black/40" onClick={() => void luuVaDong()} />
              <div className="relative w-full max-w-[460px] h-full bg-card shadow-xl flex flex-col min-h-0">
                {nganChuanBi}
              </div>
            </div>
          )}

      {/* Task 47 — dialog nạp lô 3 pha (màn hẹp; màn rộng vẽ trong ngăn phải) */}
      {!rong && napDialog && khoa && (
        <NapLoDialog
          khoa={khoa}
          items={napDialog.items}
          boQua={napDialog.boQua}
          onPha={(p) => setLoDangChay(p === "chay")}
          onDong={() => setNapDialog(null)}
          onXong={xongNapLo}
          onXemDB={(maDks) => { setNapDialog(null); xemTrongDB(khoa.ma_kh, maDks); }}
          onBoSungAnh={() => { setNapDialog(null); xemTrongDB(khoa.ma_kh, [], "chua"); }}
        />
      )}

      {/* NAP-01 #51 — panel xác nhận 2 bước "Bỏ khỏi hàng đợi" (1 hay nhiều dòng) */}
      {boXn && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={() => setBoXn(null)}>
          <div
            className="w-full max-w-md rounded-xl bg-card border border-border shadow-xl p-5"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-2 text-destructive font-semibold text-[15px]">
              <Icon name="warn" className="w-5 h-5" /> Bỏ {boXn.nhan} khỏi hàng đợi?
            </div>
            <div className="mt-3 text-[13px] text-muted-foreground space-y-2">
              <p>
                Chỉ dọn hàng đợi của tool — <b className="text-foreground">KHÔNG</b> xóa khỏi cơ sở dữ liệu,
                KHÔNG đụng máy chủ.
              </p>
              <p>
                Hồ sơ đang <b className="text-foreground">chờ / lỗi</b> sẽ được ghi nhớ "bỏ qua": lần "Kéo về từ VPS"
                sau <b className="text-foreground">không mang về lại</b>. Không lấy lại được qua giao diện — người gửi
                gửi lại trên app web sẽ là hồ sơ mới.
              </p>
            </div>
            <div className="mt-5 flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={() => setBoXn(null)}
                className="h-9 px-4 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors"
              >
                Hủy
              </button>
              <button
                type="button"
                onClick={() => void boDong()}
                className="h-9 px-4 rounded-lg bg-destructive text-white text-sm font-semibold inline-flex items-center gap-1.5 hover:brightness-110 transition-all"
              >
                <Icon name="x" className="w-4 h-4" /> Bỏ khỏi hàng đợi
              </button>
            </div>
          </div>
        </div>
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
