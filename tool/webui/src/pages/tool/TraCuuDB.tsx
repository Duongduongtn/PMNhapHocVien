import { useEffect, useState } from "react";
import { Icon } from "../../components/Icon";
import AnhModal from "../../components/AnhModal";
import AnhAvatar from "../../components/AnhAvatar";
import MoKhoaKhacDialog from "../../components/MoKhoaKhacDialog";
import DoiSoatDialog from "../../components/DoiSoatDialog";
import { PhanTrang } from "../../components/PhanTrang";
import { boDau, ymdToVN, maskNgay, nghiSaiChinhTa } from "../../lib/format";
import {
  traCuuKhoa,
  dsHoSoTheoKhoa,
  chiTietHoSo,
  suaHoSo,
  khoaCungHang,
  doiKhoa,
  xoaHoSo,
  goVeChoNap,
  dongBoTraVe,
  napAnh,
  taiAnhHoSo,
  taiAnhThumb,
  taiAnhVps,
  batDauDoiNen,
  tienDoDoiNen,
  type KetQuaAnh,
  type DoiNenTienDo,
  type KhoaTraCuu,
  type KhoaDich,
  type HoSoRow,
  type HoSoSuaIn,
} from "../../lib/api";

// QLY-01 — Tra cứu DB. Tìm khóa (mọi khóa, kể cả BC1) → lưới HV theo khóa (tìm phía client:
// tên bỏ dấu / CCCD) → xem chi tiết → SỬA nhân thân (lát 2, chỉ khóa chưa BC1 — BR-012).
function gioiTinhVN(g: string | null): string {
  return g === "M" ? "Nam" : g === "F" ? "Nữ" : "—";
}

function Bc1Chip() {
  return (
    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-warning bg-warning/10 border border-warning/30 rounded-full px-2 py-0.5 whitespace-nowrap">
      <Icon name="warn" className="w-3 h-3" /> Đã BC1 — chỉ xem
    </span>
  );
}

const FORM_RONG: HoSoSuaIn = { ho_ten: "", ngay_sinh: "", gioi_tinh: "U", so_cccd: "", noi_tt: "" };

// QLY-07 task 40 — dialog đổi nền trắng cả khóa: chọn phạm vi + sao lưu → chạy nền → polling tiến độ.
function DoiNenDialog({ maKh, tenKh, onDong, onXong }: {
  maKh: string; tenKh: string; onDong: () => void; onXong: () => void;
}) {
  const [pha, setPha] = useState<"form" | "chay" | "xong">("form");
  const [phamVi, setPhamVi] = useState<"chua_trang" | "tat_ca">("chua_trang");
  const [saoLuu, setSaoLuu] = useState(true);
  const [td, setTd] = useState<DoiNenTienDo | null>(null);
  const [err, setErr] = useState("");

  // Polling tiến độ khi đang chạy; dừng khi job báo xong_het.
  useEffect(() => {
    if (pha !== "chay") return;
    let huy = false;
    const timer = setInterval(async () => {
      try {
        const t = await tienDoDoiNen(maKh);
        if (huy) return;
        setTd(t);
        if (t.xong_het) { clearInterval(timer); setPha("xong"); }
      } catch { /* tạm thời lỗi mạng → thử lại nhịp sau */ }
    }, 1500);
    return () => { huy = true; clearInterval(timer); };
  }, [pha, maKh]);

  async function batDau() {
    setErr("");
    try {
      await batDauDoiNen(maKh, phamVi, saoLuu);
      setTd(null);
      setPha("chay");
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Không bắt đầu được.");
    }
  }

  const daXuLy = td ? td.xong + td.bo_qua + td.loi : 0;
  const pct = td && td.tong > 0 ? Math.round((daXuLy / td.tong) * 100) : 0;

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={(e) => { if (e.target === e.currentTarget && pha !== "chay") onDong(); }}>
      <div className="bg-card w-full max-w-md rounded-xl shadow-2xl max-h-[90vh] flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3 border-b border-border">
          <h3 className="font-bold text-sm">Đổi nền trắng cả khóa</h3>
          {pha !== "chay" && (
            <button onClick={onDong} aria-label="Đóng" className="w-8 h-8 rounded-lg hover:bg-muted flex items-center justify-center transition-colors">
              <Icon name="x" className="w-5 h-5" />
            </button>
          )}
        </div>
        <div className="p-5 overflow-y-auto">
          <p className="text-[13px] text-muted-foreground">Khóa <b className="text-foreground">{tenKh}</b> ({maKh})</p>

          {pha === "form" && (
            <div className="mt-4 space-y-4">
              <div>
                <label className="field-label">Phạm vi</label>
                <div className="mt-1 space-y-1.5">
                  {([["chua_trang", "Chỉ ảnh chưa nền trắng (khuyên dùng)"], ["tat_ca", "Tất cả học viên có ảnh"]] as const).map(([v, label]) => (
                    <label key={v} className="flex items-center gap-2 text-[13px] cursor-pointer">
                      <input type="radio" name="pv" checked={phamVi === v} onChange={() => setPhamVi(v)} className="accent-primary w-4 h-4" />
                      {label}
                    </label>
                  ))}
                </div>
              </div>
              <label className="flex items-center gap-2 text-[13px] cursor-pointer">
                <input type="checkbox" checked={saoLuu} onChange={(e) => setSaoLuu(e.target.checked)} className="accent-primary w-4 h-4" />
                Sao lưu ảnh gốc vào <b>_BACKUP</b> trước khi ghi đè
              </label>
              <p className="text-[12px] text-muted-foreground">Chạy nền, mỗi ảnh ~1-3 giây. Giữ trạng thái báo cáo của học viên (không ảnh hưởng Báo cáo 1/2).</p>
              {err && (
                <p className="text-[12px] text-destructive flex items-center gap-1"><Icon name="warn" className="w-3.5 h-3.5" /> {err}</p>
              )}
            </div>
          )}

          {pha !== "form" && (
            <div className="mt-4 space-y-3">
              <div className="h-2.5 rounded-full bg-muted overflow-hidden">
                <div className="h-full bg-primary transition-all" style={{ width: `${pct}%` }} />
              </div>
              <div className="flex items-center justify-between text-[13px]">
                <span className="text-muted-foreground tabular-nums">{daXuLy}/{td?.tong ?? 0} ảnh · {pct}%</span>
                {pha === "chay" && <span className="inline-flex items-center gap-1 text-primary font-medium"><Icon name="refresh" className="w-3.5 h-3.5 animate-spin" /> đang chạy…</span>}
                {pha === "xong" && <span className="inline-flex items-center gap-1 text-success font-medium"><Icon name="check" className="w-3.5 h-3.5" sw={3} /> xong</span>}
              </div>
              <div className="flex gap-3 text-[12px]">
                <span className="text-success">Đã đổi: <b className="tabular-nums">{td?.xong ?? 0}</b></span>
                <span className="text-muted-foreground">Bỏ qua: <b className="tabular-nums">{td?.bo_qua ?? 0}</b></span>
                <span className={td && td.loi > 0 ? "text-destructive" : "text-muted-foreground"}>Lỗi: <b className="tabular-nums">{td?.loi ?? 0}</b></span>
              </div>
              {td?.thong_bao && (
                <p className="text-[12px] text-warning flex items-start gap-1"><Icon name="warn" className="w-3.5 h-3.5 shrink-0 mt-0.5" /> {td.thong_bao}</p>
              )}
              {td && td.ds_loi.length > 0 && (
                <div className="max-h-28 overflow-y-auto rounded-lg border border-destructive/30 bg-destructive/5 p-2 text-[11px] space-y-1">
                  {td.ds_loi.map((l, i) => (
                    <div key={i} className="text-destructive"><b className="tabular-nums">{l.ma_dk}</b>: {l.ly_do}</div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
        <div className="p-3 border-t border-border flex gap-2">
          {pha === "form" && (
            <>
              <button onClick={onDong} className="h-10 px-4 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors">Hủy</button>
              <button onClick={() => void batDau()} className="ml-auto h-10 px-5 rounded-lg bg-primary text-primary-foreground text-sm font-semibold inline-flex items-center gap-2 hover:brightness-110 transition-all shadow-sm">
                <Icon name="image" className="w-4 h-4" /> Bắt đầu
              </button>
            </>
          )}
          {pha === "chay" && (
            <p className="text-[12px] text-muted-foreground px-1 py-2">Đang xử lý — có thể đóng khi chạy xong.</p>
          )}
          {pha === "xong" && (
            <button onClick={onXong} className="ml-auto h-10 px-5 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:brightness-110 transition-all shadow-sm">Xong</button>
          )}
        </div>
      </div>
    </div>
  );
}

// Props task 47 (NAP-01): "Xem trong DB" từ màn Nạp — tự mở khóa đích + làm nổi HV vừa nạp.
export default function TraCuuDB({ khoaMa, noiBat, moNonce, locAnhBanDau }: {
  khoaMa?: string;      // mã khóa đích cần mở sẵn
  noiBat?: string[];    // MaDK các HV vừa nạp cần tô sáng
  moNonce?: number;     // đổi mỗi lần bấm "Xem trong DB" → ép mở lại dù cùng khóa
  locAnhBanDau?: "all" | "chua" | "roi"; // CHANGES #32 — mở sẵn bộ lọc ảnh (lối tắt "bổ sung ảnh" từ Nạp lô)
} = {}) {
  const [q, setQ] = useState("");
  const [khoaList, setKhoaList] = useState<KhoaTraCuu[] | null>(null);
  const [khoa, setKhoa] = useState<KhoaTraCuu | null>(null);
  const [hoSo, setHoSo] = useState<HoSoRow[] | null>(null);
  const [qHv, setQHv] = useState("");
  const [sel, setSel] = useState<HoSoRow | null>(null);
  const [loadingKhoa, setLoadingKhoa] = useState(false);
  const [loadingHv, setLoadingHv] = useState(false);
  const [err, setErr] = useState("");

  // Sửa nhân thân (lát 2)
  const [sua, setSua] = useState(false);
  const [form, setForm] = useState<HoSoSuaIn>(FORM_RONG);
  const [hktt, setHktt] = useState<string | null>(null);
  const [loadingCt, setLoadingCt] = useState(false);
  const [saving, setSaving] = useState(false);
  const [suaErr, setSuaErr] = useState("");
  const [okMsg, setOkMsg] = useState("");

  // Đổi khóa (QLY-02)
  const [doiMo, setDoiMo] = useState(false);
  const [khoaDich, setKhoaDich] = useState<KhoaDich[] | null>(null);
  const [maKhDich, setMaKhDich] = useState("");
  const [doiBusy, setDoiBusy] = useState(false);
  const [doiErr, setDoiErr] = useState("");

  // Xóa HV (QLY-03)
  const [xoaMo, setXoaMo] = useState(false);
  const [xoaBusy, setXoaBusy] = useState(false);
  const [xoaErr, setXoaErr] = useState("");

  // Gỡ về chờ nạp (QLY-08) — tách bạch "Xóa hẳn": gỡ khỏi CSDT rồi trả bản ghi gốc về hàng chờ nạp
  const [goMo, setGoMo] = useState(false);
  const [goBusy, setGoBusy] = useState(false);
  const [goErr, setGoErr] = useState("");
  // Banner khi đã xóa CSDT nhưng đồng bộ VPS lỗi (cho "Thử lại đồng bộ" RIÊNG bước VPS)
  const [goSync, setGoSync] = useState<{ uuid: string; msg: string; coTheThuLai: boolean } | null>(null);
  const [goSyncBusy, setGoSyncBusy] = useState(false);

  // Nạp/thay ảnh (QLY-05)
  const [locAnh, setLocAnh] = useState<"all" | "chua" | "roi">(locAnhBanDau ?? "all"); // lọc tình trạng ảnh
  const [anhMo, setAnhMo] = useState(false);   // panel xác nhận nạp/thay ảnh
  const [anhModal, setAnhModal] = useState(false); // AnhModal (căn + xóa phông)
  const [anhSeed, setAnhSeed] = useState<string | null>(null); // ảnh nạp sẵn vào AnhModal (chỉnh ảnh cũ / kéo VPS)
  const [anhVpsBusy, setAnhVpsBusy] = useState(false); // CHANGES #32 — đang kéo ảnh thô VPS (nguồn b)
  const [vpsKhongCo, setVpsKhongCo] = useState(false);  // CHANGES #32 — ảnh thô VPS hết hạn/404 → ẩn nguồn (b), chỉ còn (a)
  const [anhBusy, setAnhBusy] = useState(false);
  const [anhErr, setAnhErr] = useState("");

  // Xem ảnh lớn ở modal chi tiết (QLY-01 task 35)
  const [anhXem, setAnhXem] = useState<KetQuaAnh | null>(null);
  const [anhXemBusy, setAnhXemBusy] = useState(false);

  // Mở hồ sơ khóa khác (QLY-06)
  const [moKhoaKhac, setMoKhoaKhac] = useState(false);

  // Đổi nền trắng cả khóa (QLY-07 task 40)
  const [doiNenMo, setDoiNenMo] = useState(false);
  const [doiSoatMo, setDoiSoatMo] = useState(false); // QLY-09 task 49 — panel đối soát VPS↔CSDT

  async function timKhoa() {
    setErr("");
    setLoadingKhoa(true);
    setKhoa(null);
    setHoSo(null);
    try {
      setKhoaList(await traCuuKhoa(q));
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Không tìm được khóa.");
    } finally {
      setLoadingKhoa(false);
    }
  }

  async function chonKhoa(k: KhoaTraCuu) {
    setKhoa(k);
    setErr("");
    setHoSo(null);
    setQHv("");
    setLoadingHv(true);
    try {
      setHoSo(await dsHoSoTheoKhoa(k.ma_kh));
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Không tải được danh sách học viên.");
    } finally {
      setLoadingHv(false);
    }
  }

  function dong() {
    setSel(null);
    setSua(false);
    setSuaErr("");
    setDoiMo(false);
    setDoiErr("");
    setKhoaDich(null);
    setMaKhDich("");
    setXoaMo(false);
    setXoaErr("");
    setGoMo(false);
    setGoErr("");
    setGoSync(null);
    setAnhMo(false);
    setAnhModal(false);
    setAnhSeed(null);
    setAnhErr("");
    setMoKhoaKhac(false);
  }

  // CHANGES #23 — tăng sau khi lưu/thay ảnh để ép tải lại ảnh MỚI (ảnh lớn + avatar), tránh
  // trình duyệt trả bản cũ từ bộ đệm (URL ảnh cố định theo MaDK).
  const [anhVer, setAnhVer] = useState(0);

  // Tải ảnh lớn khi mở modal chi tiết (QLY-01 task 35). Fetch kèm session header → object URL;
  // revoke khi đổi HV/đóng. File mất (404) / hỏng (422) → giữ trong anhXem để báo cảnh báo.
  // Phụ thuộc anhVer: thay ảnh xong → refetch ảnh mới ngay trong modal (CHANGES #23).
  useEffect(() => {
    setAnhXem(null);
    if (!sel || !sel.co_anh) return;
    let huy = false;
    let obj: string | null = null;
    setAnhXemBusy(true);
    void taiAnhHoSo(sel.ma_dk, anhVer)
      .then((kq) => {
        if (huy) return;
        if ("url" in kq) obj = kq.url;
        setAnhXem(kq);
      })
      .finally(() => { if (!huy) setAnhXemBusy(false); });
    return () => { huy = true; if (obj) URL.revokeObjectURL(obj); };
  }, [sel, anhVer]);

  // Task 47 — "Xem trong DB": tự tìm + mở khóa đích. Đổi khóaMa/moNonce → mở lại. HV cần tô sáng
  // đưa theo prop noiBat (khớp theo MaDK trong lưới đã tải — không cần gọi server riêng).
  const noiBatSet = new Set(noiBat ?? []);
  useEffect(() => {
    if (!khoaMa) return;
    setLocAnh(locAnhBanDau ?? "all"); // CHANGES #32 — mở qua lối tắt "bổ sung ảnh" → áp bộ lọc chưa ảnh
    let huy = false;
    (async () => {
      setErr("");
      setLoadingKhoa(true);
      try {
        const ds = await traCuuKhoa(khoaMa);
        if (huy) return;
        const k = ds.find((x) => x.ma_kh === khoaMa) ?? ds[0];
        if (!k) { setErr("Không mở được khóa đích để xem."); return; }
        setQ(khoaMa);
        await chonKhoa(k);
      } catch (e) {
        if (!huy) setErr(e instanceof Error ? e.message : "Không mở được khóa đích để xem.");
      } finally {
        if (!huy) setLoadingKhoa(false);
      }
    })();
    return () => { huy = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [khoaMa, moNonce]);

  // Click ảnh → mở trình chỉnh (QLY-05). Ảnh cũ còn → nạp sẵn vào khung; mất/hỏng (404/422) →
  // mở chế độ chọn-file mới (TDD §11.5). Ảnh đã nạp sẽ ghi đè qua napAnhHv.
  function moChinhAnh() {
    if (!sel) return;
    setAnhErr("");
    setAnhSeed(anhXem && "url" in anhXem ? anhXem.url : null);
    setAnhModal(true);
  }

  // QLY-05 (CHANGES #32) — nguồn (b): kéo ảnh THÔ học viên gửi còn trên VPS (tra theo ma_dk) → nạp
  // vào AnhModal làm ảnh gốc. Hết hạn/không tra được (404→null) → báo, operator chuyển nguồn (a) file.
  async function keoAnhVps() {
    if (!sel) return;
    setAnhErr("");
    setAnhVpsBusy(true);
    try {
      const url = await taiAnhVps(sel.ma_dk);
      if (!url) {
        setVpsKhongCo(true); // ẩn nút nguồn (b) — chỉ còn chọn-file (TDD §11.5)
        setAnhErr("Ảnh gốc trên máy chủ đã hết hạn hoặc không có — chọn ảnh từ máy.");
        return;
      }
      setAnhSeed(url);
      setAnhModal(true);
    } catch (e) {
      setAnhErr(e instanceof Error ? e.message : "Không kéo được ảnh từ máy chủ.");
    } finally {
      setAnhVpsBusy(false);
    }
  }

  // Đổi HV đang chọn → reset cờ "VPS không có ảnh" (nút nguồn b hiện lại cho HV mới).
  useEffect(() => { setVpsKhongCo(false); }, [sel?.ma_dk]);

  async function napAnhHv(jp2B64: string) {
    if (!sel) return;
    const coAnhTruoc = sel.co_anh;
    const maDk = sel.ma_dk;
    setAnhModal(false);
    setAnhErr("");
    setAnhBusy(true);
    try {
      await napAnh(maDk, jp2B64);
      // CHANGES #23: KHÔNG đóng modal — hiện ảnh MỚI trong modal + cho chỉnh tiếp. HV giờ có ảnh;
      // tăng anhVer để refetch ảnh mới (tránh bộ đệm); đóng panel "thay ảnh" để quay về xem.
      setSel((prev) => (prev && prev.ma_dk === maDk ? { ...prev, co_anh: true } : prev));
      setAnhVer((v) => v + 1);
      setAnhMo(false);
      if (khoa) setHoSo(await dsHoSoTheoKhoa(khoa.ma_kh)); // lưới đổi "đã có" + avatar refetch (ver mới)
      setOkMsg(coAnhTruoc
        ? "Đã thay ảnh — xem ảnh mới bên dưới; bấm \"Thay ảnh\" để chỉnh tiếp."
        : "Đã nạp ảnh — xem bên dưới; bấm \"Thay ảnh\" để chỉnh tiếp.");
      setTimeout(() => setOkMsg(""), 3500);
    } catch (e) {
      setAnhErr(e instanceof Error ? e.message : "Nạp ảnh không thành công.");
    } finally {
      setAnhBusy(false);
    }
  }

  async function xoaHv() {
    if (!sel) return;
    setXoaErr("");
    setXoaBusy(true);
    try {
      const kq = await xoaHoSo(sel.ma_dk);
      if (khoa) setHoSo(await dsHoSoTheoKhoa(khoa.ma_kh)); // HV biến mất khỏi lưới
      setOkMsg(kq.anh_loi ? "Đã xóa học viên (ảnh chưa chuyển được — xem log)." : "Đã xóa học viên.");
      setTimeout(() => setOkMsg(""), 2800);
      dong();
    } catch (e) {
      setXoaErr(e instanceof Error ? e.message : "Xóa không thành công.");
    } finally {
      setXoaBusy(false);
    }
  }

  // QLY-08 — gỡ HV về chờ nạp. Xóa khỏi CSDT rồi trả bản ghi gốc VPS về pending. Khác "Xóa hẳn":
  // về chờ nạp để nạp lại đúng khóa, không nhập lại ở app. VPS lỗi SAU khi xóa CSDT → banner thử lại.
  async function goVeHv() {
    if (!sel) return;
    setGoErr("");
    setGoSync(null);
    setGoBusy(true);
    try {
      const kq = await goVeChoNap(sel.ma_dk);
      if (khoa) setHoSo(await dsHoSoTheoKhoa(khoa.ma_kh)); // HV rời khóa → làm tươi lưới
      if (kq.dong_bo_loi && kq.uuid) {
        // Đã xóa CSDT nhưng chưa đưa về được hàng chờ → giữ modal, hiện banner thử lại (edge #26)
        setGoSync({ uuid: kq.uuid, msg: kq.dong_bo_loi, coTheThuLai: !!kq.co_the_thu_lai });
      } else {
        const them = kq.trong_hang_doi ? "" : " Bấm “Kéo về” để thấy lại trong hàng chờ.";
        setOkMsg("Đã gỡ học viên về chờ nạp." + them);
        setTimeout(() => setOkMsg(""), 3200);
        dong();
      }
    } catch (e) {
      setGoErr(e instanceof Error ? e.message : "Gỡ về chờ nạp không thành công.");
    } finally {
      setGoBusy(false);
    }
  }

  // "Thử lại đồng bộ" — chỉ chạy lại bước gọi VPS (không xóa lại CSDT). HV đã rời khóa rồi.
  async function thuLaiDongBo() {
    if (!goSync) return;
    setGoSyncBusy(true);
    try {
      const kq = await dongBoTraVe(goSync.uuid);
      const them = kq.trong_hang_doi ? "" : " Bấm “Kéo về” để thấy lại trong hàng chờ.";
      setOkMsg("Đã đưa học viên về chờ nạp." + them);
      setTimeout(() => setOkMsg(""), 3200);
      dong();
    } catch (e) {
      setGoSync({ ...goSync, msg: e instanceof Error ? e.message : "Vẫn chưa đồng bộ được — thử lại sau." });
    } finally {
      setGoSyncBusy(false);
    }
  }

  // QLY-01 task 36 — nút nhanh ra lưới: chọn HV rồi mở đúng luồng confirm 2 bước trong modal
  // (tái dùng moDoiKhoa/xoaHv, vẫn tôn trọng chặn BC1 — chỉ hiện khi khóa chưa BC1).
  function nhanhXoa(h: HoSoRow) {
    setSel(h);
    setXoaErr("");
    setXoaMo(true);
  }
  function nhanhDoiKhoa(h: HoSoRow) {
    setSel(h);
    void moDoiKhoa();
  }

  async function moDoiKhoa() {
    if (!khoa) return;
    setDoiErr("");
    setDoiMo(true);
    setKhoaDich(null);
    setMaKhDich("");
    try {
      const ds = await khoaCungHang(khoa.ma_kh);
      setKhoaDich(ds);
      setMaKhDich(ds[0]?.ma_kh ?? "");
    } catch (e) {
      setDoiErr(e instanceof Error ? e.message : "Không tải được khóa đích.");
    }
  }

  async function chuyenKhoa() {
    if (!sel || !maKhDich) return;
    setDoiErr("");
    setDoiBusy(true);
    try {
      await doiKhoa(sel.ma_dk, maKhDich);
      if (khoa) setHoSo(await dsHoSoTheoKhoa(khoa.ma_kh)); // HV rời khóa → làm tươi lưới
      setOkMsg("Đã đổi khóa học viên.");
      setTimeout(() => setOkMsg(""), 2500);
      dong();
    } catch (e) {
      setDoiErr(e instanceof Error ? e.message : "Đổi khóa không thành công.");
    } finally {
      setDoiBusy(false);
    }
  }

  async function moSua() {
    if (!sel) return;
    setSuaErr("");
    setLoadingCt(true);
    try {
      const ct = await chiTietHoSo(sel.ma_dk);
      if (ct.bc1) {
        setSuaErr("Khóa đã lập Báo cáo 1 — chỉ xem, không sửa được.");
        return;
      }
      setForm({
        ho_ten: ct.ho_ten,
        ngay_sinh: ct.ngay_sinh,
        gioi_tinh: ct.gioi_tinh,
        so_cccd: ct.so_cccd,
        noi_tt: ct.noi_tt ?? "",
      });
      setHktt(ct.hktt);
      setSua(true);
    } catch (e) {
      setSuaErr(e instanceof Error ? e.message : "Không mở được hồ sơ để sửa.");
    } finally {
      setLoadingCt(false);
    }
  }

  async function luu() {
    if (!sel) return;
    if (!form.ho_ten.trim()) return setSuaErr("Chưa nhập họ và tên.");
    if (!/^\d{1,20}$/.test(form.so_cccd.trim())) return setSuaErr("Số căn cước phải là chữ số (tối đa 20).");
    setSuaErr("");
    setSaving(true);
    try {
      await suaHoSo(sel.ma_dk, { ...form, ho_ten: form.ho_ten.trim(), so_cccd: form.so_cccd.trim() });
      if (khoa) setHoSo(await dsHoSoTheoKhoa(khoa.ma_kh)); // làm tươi lưới đúng dữ liệu DB
      setOkMsg("Đã lưu thay đổi.");
      setTimeout(() => setOkMsg(""), 2500);
      dong();
    } catch (e) {
      setSuaErr(e instanceof Error ? e.message : "Lưu không thành công.");
    } finally {
      setSaving(false);
    }
  }

  const rows = (hoSo ?? []).filter((h) => {
    if (locAnh === "chua" && h.co_anh) return false;   // QLY-05: lọc theo tình trạng ảnh
    if (locAnh === "roi" && !h.co_anh) return false;
    const t = qHv.trim();
    if (!t) return true;
    return boDau(h.ho_ten ?? "").includes(boDau(t)) || (h.so_cccd ?? "").includes(t);
  });
  // Task 47 — HV vừa nạp (noiBat) đưa lên đầu để thấy ngay khi "Xem trong DB".
  const rowsSapXep = noiBatSet.size > 0
    ? [...rows].sort((a, b) => (noiBatSet.has(b.ma_dk) ? 1 : 0) - (noiBatSet.has(a.ma_dk) ? 1 : 0))
    : rows;
  const soNoiBat = noiBatSet.size > 0 ? (hoSo ?? []).filter((h) => noiBatSet.has(h.ma_dk)).length : 0;
  // UI-3: phân trang lưới HV (client). Đổi khóa/ô tìm/lọc ảnh/cỡ trang → về trang 1.
  const [trang, setTrang] = useState(0);
  const [coTrang, setCoTrang] = useState(20);
  useEffect(() => { setTrang(0); }, [khoa, qHv, locAnh, coTrang]);
  const rowsTrang = rowsSapXep.slice(trang * coTrang, (trang + 1) * coTrang);
  const canhBaoTen = sua ? nghiSaiChinhTa(form.ho_ten) : "";

  return (
    <div className="p-4">
      {/* Tìm khóa */}
      <div className="flex items-end gap-2 flex-wrap">
        <div className="flex-1 min-w-[220px]">
          <label className="field-label">Tìm khóa (tên hoặc mã — mọi khóa, kể cả đã BC1)</label>
          <div className="relative mt-1">
            <Icon name="search" className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              className="field-input pl-9"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") void timKhoa(); }}
              placeholder="VD: B-K149 hoặc 70004K26B010"
            />
          </div>
        </div>
        <button
          type="button"
          onClick={() => void timKhoa()}
          disabled={loadingKhoa}
          className="h-10 px-4 rounded-lg bg-primary text-primary-foreground font-semibold text-sm inline-flex items-center gap-2 hover:brightness-110 transition-all shadow-sm disabled:opacity-60"
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
            <p className="text-[13px] text-muted-foreground px-1">Không tìm thấy khóa khớp.</p>
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
                    <div className="text-[12px] text-muted-foreground tabular-nums">
                      {k.ma_kh} · hạng {k.hang_gplx}
                    </div>
                  </div>
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
            <button type="button" onClick={() => setKhoa(null)} className="inline-flex items-center gap-1 text-[13px] text-primary font-medium hover:underline">
              <Icon name="chevronLeft" className="w-4 h-4" /> Danh sách khóa
            </button>
            <span className="text-[13px] font-bold">{khoa.ten_kh}</span>
            <span className="text-[12px] text-muted-foreground tabular-nums">{khoa.ma_kh} · hạng {khoa.hang_gplx}</span>
            {khoa.bc1 && <Bc1Chip />}
            {/* QLY-09 task 49 — đối soát máy chủ ↔ CSDT (theo khóa này + quét lạc toàn hệ nếu admin) */}
            <button
              type="button"
              onClick={() => setDoiSoatMo(true)}
              className="ml-auto inline-flex items-center gap-1.5 h-8 px-3 rounded-lg border border-border text-[13px] font-medium hover:bg-muted transition-colors"
            >
              <Icon name="refresh" className="w-4 h-4" /> Đối soát máy chủ
            </button>
            {/* QLY-07 task 40 — đổi nền trắng cả khóa (được phép cả khi BC1: ảnh không nằm trong báo cáo) */}
            <button
              type="button"
              onClick={() => setDoiNenMo(true)}
              className="inline-flex items-center gap-1.5 h-8 px-3 rounded-lg border border-border text-[13px] font-medium hover:bg-muted transition-colors"
            >
              <Icon name="image" className="w-4 h-4" /> Đổi nền cả khóa
            </button>
          </div>

          {/* Task 47 — báo HV vừa nạp khi mở từ "Xem trong DB" */}
          {soNoiBat > 0 && (
            <div className="mb-3 flex items-center gap-2 text-[13px] text-success bg-success/10 border border-success/30 rounded-lg px-3 py-2">
              <Icon name="check" className="w-4 h-4 shrink-0" sw={3} /> Vừa nạp <b className="mx-1">{soNoiBat}</b> học viên vào khóa này — các dòng tô sáng ở đầu danh sách.
            </div>
          )}

          {/* QLY-01 task 36 — thống kê nhanh đầu khóa (client, trên lưới đã tải; BC1 ở cấp khóa) */}
          {hoSo && (
            <div className="flex items-center gap-2 flex-wrap mb-3 text-[12px]">
              <span className="inline-flex items-center gap-1.5 rounded-lg bg-muted px-2.5 py-1 font-medium">
                <Icon name="user" className="w-3.5 h-3.5 text-muted-foreground" /> Tổng <b className="tabular-nums">{hoSo.length}</b> HV
              </span>
              <span className="inline-flex items-center gap-1.5 rounded-lg bg-warning/10 text-warning px-2.5 py-1 font-medium">
                <Icon name="imageOff" className="w-3.5 h-3.5" /> Thiếu ảnh <b className="tabular-nums">{hoSo.filter((h) => !h.co_anh).length}</b>
              </span>
              {khoa.bc1 && (
                <span className="inline-flex items-center gap-1.5 rounded-lg bg-warning/10 text-warning px-2.5 py-1 font-medium">
                  <Icon name="warn" className="w-3.5 h-3.5" /> Khóa đã lập Báo cáo 1
                </span>
              )}
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
            {/* QLY-05: lọc tình trạng ảnh */}
            <div className="inline-flex rounded-lg bg-muted p-1">
              {([["all", "Tất cả"], ["chua", "Chưa ảnh"], ["roi", "Đã có ảnh"]] as const).map(([k, label]) => (
                <button
                  key={k}
                  type="button"
                  onClick={() => setLocAnh(k)}
                  className={"px-3 py-1.5 text-[13px] rounded-md transition-colors " + (locAnh === k ? "bg-primary text-primary-foreground font-semibold" : "text-muted-foreground font-medium hover:text-foreground")}
                >
                  {label}
                </button>
              ))}
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
                    {!khoa.bc1 && <th className="px-2 py-2 font-semibold text-center w-20">Thao tác</th>}
                  </tr>
                </thead>
                <tbody>
                  {rowsTrang.map((h) => (
                    <tr key={h.ma_dk} onClick={() => setSel(h)} className={"border-t border-border cursor-pointer transition-colors " + (noiBatSet.has(h.ma_dk) ? "bg-success/10 hover:bg-success/15" : "hover:bg-muted/60")}>
                      <td className="px-2 py-1.5"><AnhAvatar coAnh={h.co_anh} ver={anhVer} tai={(v) => taiAnhThumb(h.ma_dk, v)} /></td>
                      <td className="px-3 py-2 tabular-nums">{h.so_ho_so || "—"}</td>
                      <td className="px-3 py-2 font-semibold">{h.ho_ten || "(chưa có tên)"}</td>
                      <td className="px-3 py-2">{gioiTinhVN(h.gioi_tinh)}</td>
                      <td className="px-3 py-2 tabular-nums">{ymdToVN(h.ngay_sinh)}</td>
                      <td className="px-3 py-2 tabular-nums">{h.so_cccd || "—"}</td>
                      {!khoa.bc1 && (
                        <td className="px-2 py-1.5 text-center whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                          <button
                            type="button"
                            title="Đổi khóa"
                            onClick={() => nhanhDoiKhoa(h)}
                            className="w-7 h-7 rounded-md hover:bg-muted inline-flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors"
                          >
                            <Icon name="send" className="w-4 h-4" />
                          </button>
                          <button
                            type="button"
                            title="Xóa học viên"
                            onClick={() => nhanhXoa(h)}
                            className="w-7 h-7 rounded-md hover:bg-destructive/10 inline-flex items-center justify-center text-destructive transition-colors"
                          >
                            <Icon name="x" className="w-4 h-4" />
                          </button>
                        </td>
                      )}
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

      {/* Chi tiết (xem) + Sửa nhân thân */}
      {sel && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={(e) => { if (e.target === e.currentTarget) dong(); }}>
          <div className="bg-card w-full max-w-md rounded-xl shadow-2xl max-h-[90vh] flex flex-col overflow-hidden">
            <div className="flex items-center justify-between px-5 py-3 border-b border-border">
              <h3 className="font-bold text-sm">{sua ? "Sửa thông tin nhân thân" : "Chi tiết học viên"}</h3>
              <button onClick={dong} aria-label="Đóng" className="w-8 h-8 rounded-lg hover:bg-muted flex items-center justify-center transition-colors">
                <Icon name="x" className="w-5 h-5" />
              </button>
            </div>

            {!sua ? (
              <>
                <div className="p-5 overflow-y-auto">
                  {/* Ảnh chân dung (QLY-01 task 35): ảnh lớn + đường dẫn + cảnh báo mất file; bấm → trình chỉnh */}
                  <div className="mb-4 flex flex-col items-center">
                    <button
                      type="button"
                      onClick={moChinhAnh}
                      title={sel.co_anh ? "Bấm để chỉnh / thay ảnh" : "Bấm để nạp ảnh"}
                      className="group relative w-32 h-[170px] rounded-lg border border-border overflow-hidden bg-muted flex items-center justify-center"
                    >
                      {!sel.co_anh ? (
                        <div className="flex flex-col items-center gap-1 text-muted-foreground">
                          <Icon name="user" className="w-10 h-10" />
                          <span className="text-[11px]">Thiếu ảnh</span>
                        </div>
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
                      <span className="absolute inset-x-0 bottom-0 bg-black/55 text-white text-[10px] py-0.5 flex items-center justify-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <Icon name="edit" className="w-3 h-3" /> {sel.co_anh ? "Chỉnh / thay" : "Nạp ảnh"}
                      </span>
                    </button>
                    {sel.co_anh && anhXem && "loi" in anhXem && (
                      <p className="mt-2 text-[12px] text-destructive flex items-start gap-1 text-center max-w-[260px]">
                        <Icon name="warn" className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                        {anhXem.loi === "hong"
                          ? "Ảnh trong hồ sơ bị hỏng, không đọc được — cần nạp lại."
                          : "DB có đường dẫn nhưng không tìm thấy file ảnh trên ổ — cần nạp lại."}
                      </p>
                    )}
                    {sel.duong_dan_anh && (
                      <p className="mt-1.5 text-[11px] text-muted-foreground break-all text-center max-w-[300px]" title={sel.duong_dan_anh}>
                        {sel.duong_dan_anh}
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
                      ] as [string, string][]
                    ).map(([k, v]) => (
                      <div key={k} className="flex justify-between gap-3 text-[13px] border-b border-border pb-2 last:border-0">
                        <span className="text-muted-foreground shrink-0">{k}</span>
                        <span className="font-medium text-right break-words">{v}</span>
                      </div>
                    ))}
                  </div>
                  {suaErr && (
                    <div className="mt-3 flex items-center gap-2 text-[12px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2">
                      <Icon name="warn" className="w-4 h-4 shrink-0" /> {suaErr}
                    </div>
                  )}

                  {/* Đổi khóa (QLY-02) — cùng hạng, chưa BC1 */}
                  {doiMo && (
                    <div className="mt-3 rounded-lg border border-border bg-muted/40 p-3 space-y-2">
                      <div className="text-[13px] font-semibold flex items-center gap-1.5">
                        <Icon name="send" className="w-4 h-4" /> Đổi sang khóa khác (cùng hạng)
                      </div>
                      {khoaDich === null ? (
                        <p className="text-[12px] text-muted-foreground flex items-center gap-1">
                          <Icon name="refresh" className="w-3.5 h-3.5 animate-spin" /> Đang tải khóa…
                        </p>
                      ) : khoaDich.length === 0 ? (
                        <p className="text-[12px] text-muted-foreground">Không có khóa cùng hạng (chưa BC1) để chuyển.</p>
                      ) : (
                        <>
                          <select className="field-input" value={maKhDich} onChange={(e) => setMaKhDich(e.target.value)}>
                            {khoaDich.map((k) => (
                              <option key={k.ma_kh} value={k.ma_kh}>{k.ma_kh} — {k.ten_kh}</option>
                            ))}
                          </select>
                          <p className="text-[11px] text-muted-foreground">Số hồ sơ cấp lại theo khóa mới; ảnh di chuyển sang thư mục khóa mới.</p>
                          <div className="flex gap-2">
                            <button onClick={() => { setDoiMo(false); setDoiErr(""); }} className="h-9 px-3 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors">Hủy</button>
                            <button
                              onClick={() => void chuyenKhoa()}
                              disabled={doiBusy || !maKhDich}
                              className="ml-auto h-9 px-4 rounded-lg bg-primary text-primary-foreground text-sm font-semibold inline-flex items-center gap-2 hover:brightness-110 transition-all disabled:opacity-60"
                            >
                              <Icon name={doiBusy ? "refresh" : "send"} className={"w-4 h-4" + (doiBusy ? " animate-spin" : "")} /> Chuyển sang khóa này
                            </button>
                          </div>
                        </>
                      )}
                      {doiErr && (
                        <p className="text-[12px] text-destructive flex items-center gap-1"><Icon name="warn" className="w-3.5 h-3.5" /> {doiErr}</p>
                      )}
                    </div>
                  )}

                  {/* Xóa HV (QLY-03) — xác nhận 2 bước, không dùng dialog chặn. Copy TÁCH BẠCH với
                      "Gỡ về chờ nạp" (CHANGES #26): nêu rõ đây là BỎ HẲN, nạp lại phải nhập lại ở app. */}
                  {xoaMo && (
                    <div className="mt-3 rounded-lg border border-destructive/40 bg-destructive/10 p-3 space-y-2">
                      <div className="text-[13px] font-semibold text-destructive flex items-center gap-1.5">
                        <Icon name="warn" className="w-4 h-4" /> Xóa hẳn học viên khỏi DB?
                      </div>
                      <p className="text-[12px] text-muted-foreground">Dùng khi <b>bỏ hẳn</b> học viên này. Muốn nạp lại phải <b>nhập lại hồ sơ ở app</b> (khác &ldquo;Gỡ về chờ nạp&rdquo;). Ảnh chuyển sang thư mục <b>_DELETED</b> (còn khôi phục được). Học viên đã có giấy phép lái xe thì không xóa được.</p>
                      {xoaErr && (
                        <p className="text-[12px] text-destructive flex items-center gap-1"><Icon name="warn" className="w-3.5 h-3.5" /> {xoaErr}</p>
                      )}
                      <div className="flex gap-2">
                        <button onClick={() => { setXoaMo(false); setXoaErr(""); }} className="h-9 px-3 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors">Hủy</button>
                        <button
                          onClick={() => void xoaHv()}
                          disabled={xoaBusy}
                          className="ml-auto h-9 px-4 rounded-lg bg-destructive text-white text-sm font-semibold inline-flex items-center gap-2 hover:brightness-110 transition-all disabled:opacity-60"
                        >
                          <Icon name={xoaBusy ? "refresh" : "x"} className={"w-4 h-4" + (xoaBusy ? " animate-spin" : "")} /> Xóa hẳn
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Gỡ về chờ nạp (QLY-08) — panel VIỀN CAM, tách khỏi "Xóa hẳn". Copy #26. */}
                  {goMo && (
                    <div className="mt-3 rounded-lg border border-warning/50 bg-warning/10 p-3 space-y-2">
                      <div className="text-[13px] font-semibold text-warning flex items-center gap-1.5">
                        <Icon name="warn" className="w-4 h-4" /> Gỡ học viên về hàng chờ nạp?
                      </div>
                      {goSync ? (
                        // Edge #26: đã xóa CSDT nhưng đồng bộ VPS lỗi → banner + "Thử lại đồng bộ"
                        <>
                          <p className="text-[12px] text-destructive flex items-start gap-1">
                            <Icon name="warn" className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                            Đã gỡ học viên khỏi khóa trong DB, nhưng chưa đưa về được hàng chờ nạp{goSync.coTheThuLai ? " (mất kết nối máy chủ)" : ""}. Học viên hiện không còn trong khóa.
                          </p>
                          <p className="text-[11px] text-muted-foreground">{goSync.msg}</p>
                          <div className="flex gap-2">
                            <button onClick={dong} className="h-9 px-3 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors">Đóng</button>
                            {goSync.coTheThuLai && (
                              <button
                                onClick={() => void thuLaiDongBo()}
                                disabled={goSyncBusy}
                                className="ml-auto h-9 px-4 rounded-lg bg-warning text-white text-sm font-semibold inline-flex items-center gap-2 hover:brightness-110 transition-all disabled:opacity-60"
                              >
                                <Icon name="refresh" className={"w-4 h-4" + (goSyncBusy ? " animate-spin" : "")} /> Thử lại đồng bộ
                              </button>
                            )}
                          </div>
                        </>
                      ) : (
                        <>
                          <p className="text-[12px] text-muted-foreground">Dùng khi <b>nạp nhầm khóa</b> và muốn nạp lại. Học viên bị gỡ khỏi khóa này trong DB và quay lại <b>danh sách chờ nạp</b> để nạp vào đúng khóa, <b>không phải nhập lại ở app</b>. Ảnh đã xử lý sẽ bỏ; nạp lại dùng ảnh gốc học viên gửi. Chỉ làm được khi khóa chưa lập Báo cáo 1.</p>
                          {goErr && (
                            <p className="text-[12px] text-destructive flex items-center gap-1"><Icon name="warn" className="w-3.5 h-3.5" /> {goErr}</p>
                          )}
                          <div className="flex gap-2">
                            <button onClick={() => { setGoMo(false); setGoErr(""); }} className="h-9 px-3 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors">Hủy</button>
                            <button
                              onClick={() => void goVeHv()}
                              disabled={goBusy}
                              className="ml-auto h-9 px-4 rounded-lg bg-warning text-white text-sm font-semibold inline-flex items-center gap-2 hover:brightness-110 transition-all disabled:opacity-60"
                            >
                              <Icon name={goBusy ? "refresh" : "send"} className={"w-4 h-4" + (goBusy ? " animate-spin" : "")} /> Gỡ về chờ nạp
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  )}

                  {/* Nạp/thay ảnh (QLY-05) — dùng được cả khi khóa đã BC1 (chỉ cập nhật ảnh) */}
                  {anhMo && (
                    <div className="mt-3 rounded-lg border border-border bg-muted/40 p-3 space-y-2">
                      <div className="text-[13px] font-semibold flex items-center gap-1.5">
                        <Icon name="image" className="w-4 h-4" /> {sel.co_anh ? "Thay ảnh chân dung" : "Nạp ảnh chân dung"}
                      </div>
                      {sel.co_anh ? (
                        <p className="text-[12px] text-warning flex items-start gap-1">
                          <Icon name="warn" className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                          Học viên đã có ảnh — nạp ảnh mới sẽ <b>ghi đè ảnh cũ</b>, không khôi phục được.
                        </p>
                      ) : (
                        <p className="text-[12px] text-muted-foreground">
                          Lấy ảnh gốc từ <b>máy tính</b> hoặc <b>kéo ảnh học viên gửi trên máy chủ</b> → căn khung 3:4 + xóa phông → lưu vào hồ sơ.
                        </p>
                      )}
                      {anhErr && (
                        <p className="text-[12px] text-destructive flex items-center gap-1"><Icon name="warn" className="w-3.5 h-3.5" /> {anhErr}</p>
                      )}
                      <div className="flex gap-2 flex-wrap">
                        <button onClick={() => { setAnhMo(false); setAnhErr(""); }} className="h-9 px-3 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors">Hủy</button>
                        {/* CHANGES #32 — nguồn (b): kéo ảnh thô VPS (chỉ khi HV chưa có ảnh + VPS còn ảnh; ẩn sau 404) */}
                        {!sel.co_anh && !vpsKhongCo && (
                          <button
                            onClick={() => void keoAnhVps()}
                            disabled={anhBusy || anhVpsBusy}
                            className="ml-auto h-9 px-4 rounded-lg border border-primary/40 text-primary text-sm font-semibold inline-flex items-center gap-2 hover:bg-primary/5 transition-all disabled:opacity-60"
                          >
                            <Icon name={anhVpsBusy ? "refresh" : "download"} className={"w-4 h-4" + (anhVpsBusy ? " animate-spin" : "")} /> {anhVpsBusy ? "Đang kéo…" : "Kéo ảnh máy chủ"}
                          </button>
                        )}
                        <button
                          onClick={() => { setAnhErr(""); setAnhSeed(null); setAnhModal(true); }}
                          disabled={anhBusy || anhVpsBusy}
                          className={(sel.co_anh || vpsKhongCo ? "ml-auto " : "") + "h-9 px-4 rounded-lg bg-primary text-primary-foreground text-sm font-semibold inline-flex items-center gap-2 hover:brightness-110 transition-all disabled:opacity-60"}
                        >
                          <Icon name={anhBusy ? "refresh" : "image"} className={"w-4 h-4" + (anhBusy ? " animate-spin" : "")} /> {anhBusy ? "Đang lưu…" : sel.co_anh ? "Chọn & xử lý ảnh" : "Chọn ảnh từ máy"}
                        </button>
                      </div>
                    </div>
                  )}

                  {khoa?.bc1 && (
                    <p className="text-[11px] text-warning mt-3 flex items-center gap-1">
                      <Icon name="warn" className="w-3.5 h-3.5" /> Khóa đã lập Báo cáo 1 — chỉ xem, không sửa/đổi được (vẫn nạp/thay ảnh được).
                    </p>
                  )}
                </div>
                <div className="p-3 border-t border-border flex gap-2 flex-wrap">
                  <button onClick={dong} className="h-10 px-4 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors">Đóng</button>
                  {!doiMo && !xoaMo && !goMo && !anhMo && (
                    <button
                      onClick={() => { setAnhMo(true); setAnhErr(""); }}
                      className="h-10 px-4 rounded-lg border border-border text-sm font-medium inline-flex items-center gap-1.5 hover:bg-muted transition-colors"
                    >
                      <Icon name="image" className="w-4 h-4" /> {sel.co_anh ? "Thay ảnh" : "Nạp ảnh"}
                    </button>
                  )}
                  {!doiMo && !xoaMo && !goMo && !anhMo && (
                    <button
                      onClick={() => setMoKhoaKhac(true)}
                      className="h-10 px-4 rounded-lg border border-border text-sm font-medium inline-flex items-center gap-1.5 hover:bg-muted transition-colors"
                    >
                      <Icon name="plus" className="w-4 h-4" /> Tạo thêm hồ sơ ở khóa học khác hạng
                    </button>
                  )}
                  {!khoa?.bc1 && !doiMo && !xoaMo && !goMo && !anhMo && (
                    <>
                      <button
                        onClick={() => { setXoaMo(true); setXoaErr(""); }}
                        className="h-10 px-4 rounded-lg border border-destructive/40 text-destructive text-sm font-medium inline-flex items-center gap-1.5 hover:bg-destructive/10 transition-colors"
                      >
                        <Icon name="x" className="w-4 h-4" /> Xóa hẳn
                      </button>
                      <button
                        onClick={() => { setGoMo(true); setGoErr(""); setGoSync(null); }}
                        className="h-10 px-4 rounded-lg border border-warning/50 text-warning text-sm font-medium inline-flex items-center gap-1.5 hover:bg-warning/10 transition-colors"
                      >
                        <Icon name="send" className="w-4 h-4" /> Gỡ về chờ nạp
                      </button>
                      <button
                        onClick={() => void moDoiKhoa()}
                        className="ml-auto h-10 px-4 rounded-lg border border-border text-sm font-medium inline-flex items-center gap-1.5 hover:bg-muted transition-colors"
                      >
                        <Icon name="send" className="w-4 h-4" /> Đổi khóa
                      </button>
                      <button
                        onClick={() => void moSua()}
                        disabled={loadingCt}
                        className="h-10 px-5 rounded-lg bg-primary text-primary-foreground text-sm font-semibold inline-flex items-center gap-2 hover:brightness-110 transition-all shadow-sm disabled:opacity-60"
                      >
                        <Icon name={loadingCt ? "refresh" : "edit"} className={"w-4 h-4" + (loadingCt ? " animate-spin" : "")} /> Sửa
                      </button>
                    </>
                  )}
                </div>
              </>
            ) : (
              <>
                <div className="p-5 overflow-y-auto space-y-3">
                  <div>
                    <label className="field-label">Họ và tên</label>
                    <input
                      autoFocus
                      className="field-input mt-1"
                      value={form.ho_ten}
                      onChange={(e) => setForm({ ...form, ho_ten: e.target.value })}
                    />
                    {canhBaoTen && (
                      <p className="text-[11px] text-warning mt-1 flex items-center gap-1">
                        <Icon name="warn" className="w-3 h-3" /> {canhBaoTen}
                      </p>
                    )}
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="field-label">Ngày sinh</label>
                      <input
                        className="field-input mt-1 tabular-nums"
                        value={form.ngay_sinh}
                        onChange={(e) => setForm({ ...form, ngay_sinh: maskNgay(e.target.value) })}
                        placeholder="dd/mm/yyyy hoặc yyyy"
                        inputMode="numeric"
                      />
                    </div>
                    <div>
                      <label className="field-label">Giới tính</label>
                      <select
                        className="field-input mt-1"
                        value={form.gioi_tinh}
                        onChange={(e) => setForm({ ...form, gioi_tinh: e.target.value })}
                      >
                        <option value="M">Nam</option>
                        <option value="F">Nữ</option>
                        <option value="U">Không xác định</option>
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="field-label">Số căn cước</label>
                    <input
                      className="field-input mt-1 tabular-nums"
                      value={form.so_cccd}
                      onChange={(e) => setForm({ ...form, so_cccd: e.target.value.replace(/\D/g, "").slice(0, 20) })}
                      inputMode="numeric"
                    />
                  </div>
                  <div>
                    <label className="field-label">Nơi thường trú (chi tiết: số nhà / thôn)</label>
                    <input
                      className="field-input mt-1"
                      value={form.noi_tt}
                      maxLength={50}
                      onChange={(e) => setForm({ ...form, noi_tt: e.target.value })}
                    />
                    {hktt && <p className="text-[11px] text-muted-foreground mt-1">Thuộc: {hktt}</p>}
                  </div>
                  <p className="text-[11px] text-muted-foreground">Chỉ sửa thông tin nhân thân. Ảnh, khóa học không đổi ở đây.</p>
                  {suaErr && (
                    <div className="flex items-center gap-2 text-[12px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2">
                      <Icon name="warn" className="w-4 h-4 shrink-0" /> {suaErr}
                    </div>
                  )}
                </div>
                <div className="p-3 border-t border-border flex gap-2">
                  <button onClick={() => { setSua(false); setSuaErr(""); }} className="h-10 px-4 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors">Hủy</button>
                  <button
                    onClick={() => void luu()}
                    disabled={saving}
                    className="ml-auto h-10 px-5 rounded-lg bg-primary text-primary-foreground text-sm font-semibold inline-flex items-center gap-2 hover:brightness-110 transition-all shadow-sm disabled:opacity-60"
                  >
                    <Icon name={saving ? "refresh" : "check"} className={"w-4 h-4" + (saving ? " animate-spin" : "")} sw={3} /> Lưu
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* AnhModal (QLY-05) — căn khung 3:4 + xóa phông; onXong trả jp2_b64 → nạp vào hồ sơ.
          anhSeed: ảnh cũ nạp sẵn khi bấm chỉnh từ modal chi tiết (null = chọn file mới). */}
      {anhModal && sel && (
        <AnhModal
          anhBanDau={anhSeed}
          anhGoc={anhSeed}
          onDong={() => { setAnhModal(false); setAnhSeed(null); }}
          onXong={(b64) => void napAnhHv(b64)}
        />
      )}

      {/* Mở hồ sơ khóa khác (QLY-06) */}
      {moKhoaKhac && sel && (
        <MoKhoaKhacDialog
          maDk={sel.ma_dk}
          hoTen={sel.ho_ten || "(chưa có tên)"}
          onDong={() => setMoKhoaKhac(false)}
          onXong={(msg) => { setOkMsg(msg); setTimeout(() => setOkMsg(""), 3500); dong(); }}
        />
      )}

      {/* Đổi nền trắng cả khóa (QLY-07 task 40) */}
      {doiNenMo && khoa && (
        <DoiNenDialog
          maKh={khoa.ma_kh}
          tenKh={khoa.ten_kh || "(không tên)"}
          onDong={() => setDoiNenMo(false)}
          onXong={async () => {
            setDoiNenMo(false);
            setOkMsg("Đã đổi nền trắng cho khóa.");
            setTimeout(() => setOkMsg(""), 3500);
            if (khoa) setHoSo(await dsHoSoTheoKhoa(khoa.ma_kh)); // làm tươi avatar lưới
          }}
        />
      )}

      {/* Đối soát VPS↔CSDT (QLY-09 task 49) */}
      {doiSoatMo && (
        <DoiSoatDialog
          khoaMa={khoa?.ma_kh}
          tenKhoa={khoa?.ten_kh || undefined}
          onDong={() => setDoiSoatMo(false)}
        />
      )}
    </div>
  );
}
