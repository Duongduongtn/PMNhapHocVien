import { useEffect, useMemo, useRef, useState, type KeyboardEvent as RKbd } from "react";
import { Icon } from "../../components/Icon";
import { PhanTrang } from "../../components/PhanTrang";
import { useConfigDrawer } from "../../lib/configDrawer";
import { boDau } from "../../lib/format";
import MoKhoaModal, { type MoKhoaKetQuaUI } from "./MoKhoaModal";
import SuaSauGuiModal from "./SuaSauGuiModal";
import { hintDiem } from "./diemHint";
import {
  getSyncTargets,
  dsKhoaKQD,
  dsHocVienKQD,
  getChuongTrinhKQD,
  setChuongTrinhKQD,
  getGiaiTrinhKQD,
  capNhatKQD,
  xoaDiemKQD,
  moKhoaTrangThai,
  dsSuaSauGui,
  type MoKhoaTrangThai,
  type SuaSauGuiMuc,
  type SuaSauGuiKetQua,
  type KhoaKQD,
  type HocVienKQD,
  type TrangThaiKQD,
  type ChuongTrinh,
  type DiemGocKQD,
  luatKQD,
  luuDatKQD,
  xuatExcelKQD,
  xuatSoTheoDoiKQD,
  moThuMucXuat,
  type XuatExcelKetQua,
  type DatLuuKetQua,
} from "../../lib/api";
import KiemTruocKetXuat from "./KiemTruocKetXuat";
import NapDatModal from "./NapDatModal";
import { bangNhau, chuanHoaGio, parseGio, soHien } from "./gioThucHanh";

// KQD-01 (lưới + lọc) + KQD-02 (nhập điểm gốc → quy đổi → ghi CDB). Ghi CSDL ĐÍCH qua
// /local/ketqua/*. Bám mockup ui-mock/ketqua.html: nhập điểm THẲNG trên lưới, quy đổi &
// kết luận Đạt hiện ngay; giờ/km đường trên lưới; giờ sân/km sân/số giấy/ngày trong drawer.

const TT_LABEL: Record<string, [string, string]> = {
  "03": ["Đã đăng ký", "text-muted-foreground bg-muted border-border"],
  "04": ["Đã đăng ký", "text-muted-foreground bg-muted border-border"],
  "09": ["Đã cập nhật · Đạt", "text-success bg-success/10 border-success/40"],
  "10": ["Đã cập nhật · Không đạt", "text-destructive bg-destructive/10 border-destructive/40"],
  "12": ["Đã kết xuất gửi Sở", "text-primary bg-primary/10 border-primary/40"],
  "13": ["Hoàn thành", "text-primary bg-primary/10 border-primary/40"],
  "14": ["Sở từ chối", "text-destructive bg-destructive/10 border-destructive/40"],
  "90": ["Đang giải trình", "text-warning bg-warning/10 border-warning/40"],
};
const BO_LOC: { key: TrangThaiKQD; label: string }[] = [
  { key: "all", label: "Tất cả" },
  { key: "dangky", label: "Đã đăng ký (03/04)" },
  { key: "capnhat", label: "Đã cập nhật (09/10)" },
  { key: "tuchoi", label: "Sở từ chối (14)" },
  { key: "giaitrinh", label: "Đang giải trình (90)" },
];

// ── Quy đổi phía client (mirror app/ketqua_quydoi.py) — chỉ để xem trước; server tính lại khi ghi ──
const LT: Record<string, [number, number]> = {
  "B|cu": [27, 30], "B|moi": [45, 50], "C1|cu": [32, 35], "C1|moi": [54, 60],
};
const NG_MAX: Record<string, [number, number]> = {
  mo_phong: [5, 10], hinh: [80, 100], tien_lui: [5, 10], duong: [80, 100],
};
const GIO_KM: Record<string, { gioSan: number; kmSan: number; gyGio: number; gyKm: number }> = {
  B01: { gioSan: 34, kmSan: 240, gyGio: 12, gyKm: 710 },
  B: { gioSan: 34, kmSan: 240, gyGio: 20, gyKm: 810 },
  C1: { gioSan: 35, kmSan: 225, gyGio: 24, gyKm: 825 },
};
type HangCat = "B01" | "B" | "C1" | null;
function phanLoaiHang(mm: string | null, mh: string | null): HangCat {
  const m = (mm || "").trim().toUpperCase();
  const h = (mh || "").trim().toUpperCase();
  if (m === "B.01" || h === "B11") return "B01";
  if (m === "C1" || h === "C1") return "C1";
  if (m === "B" || h === "B1" || h === "B2") return "B";
  return null;
}
function ltParam(cat: HangCat, ct: ChuongTrinh): [number, number] | null {
  const nhom = cat === "B01" || cat === "B" ? "B" : cat === "C1" ? "C1" : null;
  return nhom ? LT[`${nhom}|${ct}`] : null;
}
function ngMax(mon: string, cat: HangCat, ct: ChuongTrinh): [number, number] | null {
  if (mon === "ly_thuyet") return ltParam(cat, ct);
  return NG_MAX[mon];
}
function quyDoi(goc: number, ng: number, mx: number): number {
  return goc >= ng ? 5 + ((goc - ng) / (mx - ng)) * 5 : (goc / ng) * 5;
}
const d1 = (x: number | null): string => (x == null ? "—" : x.toFixed(1).replace(".", ","));

const MON5 = ["ly_thuyet", "mo_phong", "hinh", "tien_lui", "duong"] as const;
const MON_NHAN: Record<string, string> = {
  ly_thuyet: "số câu", mo_phong: "/10", hinh: "/100", tien_lui: "/10", duong: "/100",
};
type NhapRow = { ly_thuyet: string; mo_phong: string; hinh: string; tien_lui: string; duong: string; gio_duong: string; km_duong: string };
const NHAP_RONG: NhapRow = { ly_thuyet: "", mo_phong: "", hinh: "", tien_lui: "", duong: "", gio_duong: "", km_duong: "" };
// KQD-02: HV đã có giờ/km ở DB đích → ô nạp sẵn đúng giá trị đó (không để trống rồi ghi NULL đè khi lưu).
const gocNhap = (h: HocVienKQD): NhapRow => ({ ...NHAP_RONG, gio_duong: soHien(h.gio_duong), km_duong: soHien(h.km_duong) });

function parseNum(v: string): number | null {
  const t = (v || "").trim().replace(",", ".");
  if (t === "") return null;
  const n = Number(t);
  return Number.isFinite(n) ? n : null;
}

// Điều hướng ô nhập điểm bằng phím mũi tên trên lưới: ↑/↓ đổi hàng (cùng cột);
// ←/→ đổi cột khi con trỏ ở đầu/cuối ô (để vẫn di chuyển con trỏ trong ô như thường).
// Dò ô đích theo data-kqd-r (hàng) + data-kqd-c (cột). Ô bị khóa (12/13) không có input → bỏ qua.
function navGrid(e: RKbd<HTMLInputElement>, r: number, c: number) {
  const el = e.currentTarget;
  let tr = r, tc = c;
  if (e.key === "ArrowUp") tr = r - 1;
  else if (e.key === "ArrowDown") tr = r + 1;
  else if (e.key === "ArrowLeft") { if (el.selectionStart !== 0) return; tc = c - 1; }
  else if (e.key === "ArrowRight") { if (el.selectionStart !== el.value.length) return; tc = c + 1; }
  else return;
  const next = document.querySelector<HTMLInputElement>(`input[data-kqd-r="${tr}"][data-kqd-c="${tc}"]`);
  if (next) { e.preventDefault(); next.focus(); next.select(); }
}

// Tính quy đổi + Đạt cho 1 dòng nhập. over: môn vượt khung.
function tinhDong(nhap: NhapRow, cat: HangCat, ct: ChuongTrinh, monBatBuoc: readonly string[] = MON5) {
  const qd: Record<string, number | null> = {};
  const over: Record<string, boolean> = {};
  const thieu: Record<string, boolean> = {};
  // "đã bắt đầu nhập" = có ít nhất 1 môn điền → tô đỏ ô bắt buộc còn trống (PRD edge "ô đỏ").
  const batDau = MON5.some((m) => parseNum(nhap[m]) != null);
  for (const mon of MON5) {
    const raw = parseNum(nhap[mon]);
    thieu[mon] = batDau && raw == null && monBatBuoc.includes(mon);
    const nm = ngMax(mon, cat, ct);
    if (raw == null || !nm) { qd[mon] = null; over[mon] = false; continue; }
    const [ng, mx] = nm;
    over[mon] = raw < 0 || raw > mx;
    qd[mon] = over[mon] ? null : quyDoi(raw, ng, mx);
  }
  const full = MON5.every((m) => qd[m] != null && !over[m]);
  const dat = full && MON5.every((m) => (qd[m] as number) >= 5);
  return { qd, over, thieu, full, dat };
}

function ttBadge(tt: string | null) {
  const [lbl, cls] = TT_LABEL[tt ?? ""] ?? [tt ?? "—", "text-muted-foreground bg-muted border-border"];
  return <span className={"inline-block text-[11px] font-semibold border rounded-full px-2 py-0.5 whitespace-nowrap " + cls}>{lbl}</span>;
}

export default function CapNhatKQDT() {
  const { open: moCauHinh } = useConfigDrawer();
  const [targetKey, setTargetKey] = useState<string | null>(null);
  const [chuaChonDich, setChuaChonDich] = useState(false);

  const [q, setQ] = useState("");
  const [khoaList, setKhoaList] = useState<KhoaKQD[] | null>(null);
  const [khoa, setKhoa] = useState<KhoaKQD | null>(null);
  const [moGoiY, setMoGoiY] = useState(false);
  const [loadingKhoa, setLoadingKhoa] = useState(false);
  const [ct, setCt] = useState<ChuongTrinh>("cu");
  // KQD-07: luật môn bắt buộc dùng chung với khung "Kiểm trước kết xuất" (đọc 1 lần; lỗi → mặc định 5 môn).
  const [monBatBuoc, setMonBatBuoc] = useState<readonly string[]>(MON5);
  const [moKiemTruoc, setMoKiemTruoc] = useState(false);
  const [moNapDat, setMoNapDat] = useState(false); // KQD-08: hộp thoại nạp giờ/km từ PDF DAT
  const [dangXuat, setDangXuat] = useState(false); // KQD-09: đang dựng + lưu file Excel
  const [fileXuat, setFileXuat] = useState<XuatExcelKetQua | null>(null); // KQD-09: file vừa lưu (hiện nút mở thư mục)

  const [loc, setLoc] = useState<TrangThaiKQD>("all");
  const [qHv, setQHv] = useState("");
  const [hoSo, setHoSo] = useState<HocVienKQD[] | null>(null);
  const [loadingHv, setLoadingHv] = useState(false);
  const [err, setErr] = useState("");
  const [trang, setTrang] = useState(0);
  const [coTrang, setCoTrang] = useState(50);

  // Nhập điểm/giờ-km theo từng HV (RAM, theo ma_dk). Drawer chi tiết: km sân + ngày.
  const [nhap, setNhap] = useState<Record<string, NhapRow>>({});
  const [luuBusy, setLuuBusy] = useState<string | null>(null);
  const [toast, setToast] = useState("");
  const [drawer, setDrawer] = useState<HocVienKQD | null>(null);
  const [ct_detail, setCtDetail] = useState<{ km_san: string; ngay_htkh: string; tg_bat_dau: string; tg_ket_thuc: string }>({ km_san: "", ngay_htkh: "", tg_bat_dau: "", tg_ket_thuc: "" });
  // KQD-04 — giải trình (sửa) + lý do Sở từ chối (đọc), theo ma_dk.
  const [giaiTrinh, setGiaiTrinh] = useState<Record<string, string>>({});
  const [lyDo, setLyDo] = useState<Record<string, string | null>>({});
  const [moKhoaMo, setMoKhoaMo] = useState(false); // KQD-05: modal mở khóa (lối từ dòng 🔒 HV 12)
  const [gonKhoa, setGonKhoa] = useState(false); // thu gọn khung chọn khóa → xem được nhiều HV hơn
  const [xacNhanXoa, setXacNhanXoa] = useState(false); // KQD-06: bước xác nhận xóa điểm trong drawer
  // KQD-05 mở rộng (#53) — "sửa sau gửi": chỉ khi cơ sở HẾT gói chưa gửi; chọn từng HV 12.
  const [goi, setGoi] = useState<MoKhoaTrangThai | null>(null);
  const [chon, setChon] = useState<Set<string>>(new Set());
  const [suaMo, setSuaMo] = useState(false);
  const [choKx, setChoKx] = useState<SuaSauGuiMuc[]>([]); // HV đã mở sửa sau gửi, chưa kết xuất lại

  useEffect(() => {
    let huy = false;
    getSyncTargets()
      .then((d) => {
        if (huy) return;
        const t = d.targets.find((x) => x.key === d.selected) ?? d.targets[0];
        if (!t) { setChuaChonDich(true); return; }
        setTargetKey(t.key);
      })
      .catch(() => { if (!huy) setChuaChonDich(true); });
    return () => { huy = true; };
  }, []);

  useEffect(() => {
    luatKQD().then((r) => { if (r.mon_bat_buoc.length) setMonBatBuoc(r.mon_bat_buoc); }).catch(() => { /* giữ mặc định 5 môn */ });
  }, []);

  const timer = useRef<number | undefined>(undefined);
  useEffect(() => {
    if (!targetKey) return;
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => {
      setLoadingKhoa(true);
      dsKhoaKQD(q, targetKey)
        .then((ks) => setKhoaList(ks))
        .catch((e) => setErr(e instanceof Error ? e.message : "Không tìm được khóa."))
        .finally(() => setLoadingKhoa(false));
    }, 300);
    return () => window.clearTimeout(timer.current);
  }, [q, targetKey]);

  async function taiHoSo(k: KhoaKQD, l: TrangThaiKQD) {
    setErr(""); setLoadingHv(true); setHoSo(null);
    try {
      setHoSo(await dsHocVienKQD(k.ma_kh, l, targetKey ?? undefined));
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Không tải được danh sách học viên.");
    } finally { setLoadingHv(false); }
  }

  // KQD-05 #53: đọc gói hàng đợi của cơ sở (cổng) + danh sách "sửa sau gửi chưa kết xuất lại".
  // Lỗi → coi như chưa biết (goi=null): lưới giữ lối "Mở khóa" cũ, không chặn nhập điểm.
  function taiGoiVaChoKx() {
    if (!targetKey) return;
    moKhoaTrangThai(targetKey).then(setGoi).catch(() => setGoi(null));
    dsSuaSauGui(targetKey).then(setChoKx).catch(() => setChoKx([]));
  }

  function chonKhoa(k: KhoaKQD) {
    setKhoa(k); setMoGoiY(false); setQ(`${k.ten_kh} · ${k.ma_kh}`);
    setLoc("all"); setQHv(""); setTrang(0); setNhap({}); setChon(new Set());
    void taiHoSo(k, "all");
    taiGoiVaChoKx();
    getChuongTrinhKQD(k.ma_kh).then((r) => setCt(r.ct)).catch(() => setCt("cu"));
  }
  function chonLoc(l: TrangThaiKQD) { setLoc(l); setTrang(0); if (khoa) void taiHoSo(khoa, l); }

  // KQD-05: sau khi mở khóa (CSĐT-wide) → HV 12 về 09/10 → làm tươi lưới đang xem.
  function sauMoKhoa(r: MoKhoaKetQuaUI) {
    setMoKhoaMo(false);
    setToast(`Đã mở khóa ${r.so_hv_mo} HV (${r.so_khoa} khóa) + xóa ${r.so_goi_xoa} gói chưa gửi${r.so_hv_bo_qua > 0 ? ` · bỏ qua ${r.so_hv_bo_qua} HV chưa có kết luận` : ""}. Giờ sửa điểm bình thường rồi kết xuất lại ở phần mềm CDB.`);
    if (khoa) void taiHoSo(khoa, loc);
    taiGoiVaChoKx();
  }

  // KQD-05 #53: sau khi mở sửa sau gửi → HV được chọn về 09/10 → làm tươi lưới + khối nhắc.
  function sauSuaSauGui(r: SuaSauGuiKetQua) {
    setSuaMo(false); setChon(new Set());
    const boQua = r.bo_qua.length;
    setToast(`Đã mở sửa ${r.so_mo} học viên${boQua > 0 ? ` · bỏ qua ${boQua} (${r.bo_qua[0].ly_do})` : ""}. Sửa điểm rồi KẾT XUẤT LẠI ở phần mềm CDB để gửi bản mới.`);
    if (khoa) void taiHoSo(khoa, loc);
    taiGoiVaChoKx();
  }
  function bangChon(ma: string, bat: boolean) {
    setChon((cur) => { const c = new Set(cur); if (bat) c.add(ma); else c.delete(ma); return c; });
  }

  async function doiCt(v: ChuongTrinh) {
    if (!khoa) return;
    setCt(v);
    try { await setChuongTrinhKQD(khoa.ma_kh, v); } catch { /* giữ UI, lần ghi sau server đọc lại */ }
  }

  function setNhapO(h: HocVienKQD, k: keyof NhapRow, v: string) {
    setNhap((cur) => ({ ...cur, [h.ma_dk]: { ...(cur[h.ma_dk] ?? gocNhap(h)), [k]: v } }));
  }

  // KQD-09 (Excel chi tiết) / KQD-10 (Sổ theo dõi): server lưu file vào thư mục `output` của phần mềm.
  async function xuatFile(loai: "excel" | "so") {
    if (!khoa || dangXuat) return;
    setDangXuat(true); setToast(""); setFileXuat(null);
    try {
      const r = loai === "so"
        ? await xuatSoTheoDoiKQD(khoa.ma_kh, targetKey ?? undefined)
        : await xuatExcelKQD(khoa.ma_kh, targetKey ?? undefined);
      setFileXuat(r);
      setToast(`Đã lưu ${loai === "so" ? "sổ theo dõi" : "kết quả"} ${r.so_hoc_vien.toLocaleString("vi-VN")} học viên → ${r.duong_dan}`);
    } catch (e) {
      setToast(e instanceof Error ? e.message : "Không xuất được file.");
    } finally { setDangXuat(false); }
  }
  async function moThuMuc() {
    try { await moThuMucXuat(); } catch (e) { setToast(e instanceof Error ? e.message : "Không mở được thư mục."); }
  }

  // KQD-08: nạp xong → làm tươi lưới; ô giờ/km đang nháp của HV vừa ghi lấy theo giá trị đã lưu.
  function sauNapDat(r: DatLuuKetQua, daGui: { ma_dk: string; gio_duong: number; km_duong: number }[]) {
    setMoNapDat(false);
    setNhap((cur) => {
      const c = { ...cur };
      for (const d of daGui) {
        if (c[d.ma_dk]) c[d.ma_dk] = { ...c[d.ma_dk], gio_duong: soHien(d.gio_duong), km_duong: soHien(d.km_duong) };
      }
      return c;
    });
    setToast(`Đã lưu giờ/km đường cho ${r.da_luu} học viên${r.bo_qua.length > 0 ? ` · bỏ qua ${r.bo_qua.length} (${r.bo_qua[0].ly_do})` : ""}.`);
    if (khoa) void taiHoSo(khoa, loc);
  }

  function moDrawer(h: HocVienKQD) {
    const cat = phanLoaiHang(h.ma_hang_moi, h.ma_hang);
    const gk = cat ? GIO_KM[cat] : null;
    setCtDetail({
      km_san: gk ? String(gk.kmSan) : "",
      ngay_htkh: khoa?.ngay_thi ?? "",
      tg_bat_dau: khoa?.ngay_bg ?? "",
      tg_ket_thuc: khoa?.ngay_thi ?? "",
    });
    setDrawer(h); setXacNhanXoa(false);
    // KQD-04: HV Sở từ chối (14) / đang giải trình (90) → lấy lý do từ chối + giải trình hiện có
    if (h.tt_xuly === "14" || h.tt_xuly === "90") {
      getGiaiTrinhKQD(h.ma_dk, targetKey ?? undefined)
        .then((r) => {
          setLyDo((c) => ({ ...c, [h.ma_dk]: r.ly_do_tu_choi }));
          setGiaiTrinh((c) => (h.ma_dk in c ? c : { ...c, [h.ma_dk]: r.giai_trinh ?? "" }));
        })
        .catch(() => { /* không chặn drawer nếu đọc lỗi */ });
    }
  }

  async function luu(h: HocVienKQD) {
    const nr = nhap[h.ma_dk] ?? gocNhap(h);
    const gio = parseGio(nr.gio_duong);
    if (gio === "sai") { setToast("Giờ đường sai dạng — gõ số (20,5) hoặc hh:mm (20:30), phút phải nhỏ hơn 60."); return; }
    const km = parseNum(nr.km_duong);
    // Không gõ điểm mới mà chỉ sửa giờ/km → ghi RIÊNG 2 cột này (không đụng điểm/kết luận/ngày), như nạp PDF DAT.
    if (!MON5.some((m) => parseNum(nr[m]) != null)) {
      if (bangNhau(gio, h.gio_duong) && bangNhau(km, h.km_duong)) { setToast("Chưa nhập điểm hay giờ/km mới nào để lưu."); return; }
      if (gio == null || km == null || !khoa) { setToast("Giờ đường và km đường phải nhập đủ cả hai để lưu."); return; }
      setLuuBusy(h.ma_dk); setToast("");
      try {
        const r = await luuDatKQD({ ma_kh: khoa.ma_kh, dong: [{ ma_dk: h.ma_dk, gio_duong: gio, km_duong: km }] }, targetKey ?? undefined);
        setToast(r.da_luu > 0 ? `Đã lưu giờ/km đường của ${h.ho_ten}.` : (r.bo_qua[0]?.ly_do ?? "Không lưu được."));
        await taiHoSo(khoa, loc);
        setNhap((cur) => { const c = { ...cur }; delete c[h.ma_dk]; return c; });
      } catch (e) {
        setToast(e instanceof Error ? e.message : "Không lưu được giờ/km.");
      } finally { setLuuBusy(null); }
      return;
    }
    const cat = phanLoaiHang(h.ma_hang_moi, h.ma_hang);
    const t = tinhDong(nr, cat, ct, monBatBuoc);
    if (MON5.some((m) => t.over[m])) { setToast("Có điểm vượt khung, sửa lại trước khi lưu."); return; }
    // KQD-06 sửa lẻ: môn vừa gõ → điểm GỐC; môn trống mà đã có điểm lưu → giữ quy-đổi cũ.
    const diem_goc: Partial<DiemGocKQD> = {};
    const giu: Partial<DiemGocKQD> = {};
    let thieu = false;
    for (const m of MON5) {
      const v = parseNum(nr[m]);
      if (v != null) diem_goc[m] = v;
      else if (h.diem[m] != null) giu[m] = h.diem[m] as number;
      else thieu = true;
    }
    if (Object.keys(diem_goc).length === 0) { setToast("Chưa nhập điểm mới nào để lưu."); return; }
    if (thieu) { setToast("Môn chưa có điểm phải nhập đủ (không có điểm cũ để giữ)."); return; }
    const coGiu = Object.keys(giu).length > 0;
    setLuuBusy(h.ma_dk); setToast("");
    try {
      const r = await capNhatKQD({
        ma_dk: h.ma_dk,
        diem_goc,
        giu_quydoi: coGiu ? giu : undefined,
        km_san: parseNum(ct_detail.km_san),
        gio_duong: gio,
        km_duong: km,
        ngay_ra_qdtn: ct_detail.ngay_htkh || undefined,
        tg_bat_dau: ct_detail.tg_bat_dau || undefined,
        tg_ket_thuc: ct_detail.tg_ket_thuc || undefined,
        // KQD-04: chỉ gửi giải trình cho HV Sở từ chối/giải trình (null = không đụng cột)
        giai_trinh: (h.tt_xuly === "14" || h.tt_xuly === "90") ? (giaiTrinh[h.ma_dk] ?? "") : null,
      }, targetKey ?? undefined);
      setToast(`Đã lưu ${h.ho_ten} — ${r.ket_luan === "dat" ? "ĐẠT" : "Không đạt"}${r.so_giay ? ` · ${r.so_giay}` : ""}`);
      if (khoa) await taiHoSo(khoa, loc);  // làm tươi trạng thái/điểm
      setNhap((cur) => { const c = { ...cur }; delete c[h.ma_dk]; return c; });
    } catch (e) {
      setToast(e instanceof Error ? e.message : "Không lưu được kết quả.");
    } finally { setLuuBusy(null); }
  }

  // KQD-06 xóa điểm: reset HV 09/10 về chưa có điểm (TT='03'). Có xác nhận ở drawer.
  async function xoaDiem(h: HocVienKQD) {
    setLuuBusy(h.ma_dk); setToast("");
    try {
      await xoaDiemKQD(h.ma_dk, targetKey ?? undefined);
      setToast(`Đã xóa điểm ${h.ho_ten} — về "Đã đăng ký", nhập lại được.`);
      setDrawer(null); setXacNhanXoa(false);
      setNhap((cur) => { const c = { ...cur }; delete c[h.ma_dk]; return c; });
      if (khoa) await taiHoSo(khoa, loc);
    } catch (e) {
      setToast(e instanceof Error ? e.message : "Không xóa được điểm.");
    } finally { setLuuBusy(null); }
  }

  const hoSoLoc = useMemo(() => {
    if (!hoSo) return null;
    const k = boDau(qHv.trim().toLowerCase());
    if (!k) return hoSo;
    return hoSo.filter((h) => boDau(h.ho_ten.toLowerCase()).includes(k) || h.so_cccd.includes(qHv.trim()));
  }, [hoSo, qHv]);
  const trenTrang = hoSoLoc ? hoSoLoc.slice(trang * coTrang, (trang + 1) * coTrang) : [];

  // KQD-05 #53 — chỉ khi cơ sở đã biết là HẾT gói chưa gửi mới cho tích chọn HV 12.
  const hetGoiChuaGui = goi != null && !goi.mo_duoc;
  const choKxTheoDk = useMemo(() => new Map(choKx.map((c) => [c.ma_dk, c])), [choKx]);
  const soChoKxKhoa = khoa ? choKx.filter((c) => c.ma_kh === khoa.ma_kh).length : 0;
  const hvChon = (hoSo ?? []).filter((h) => chon.has(h.ma_dk) && h.tt_xuly === "12");
  const chonDuoc = trenTrang.filter((h) => h.tt_xuly === "12").map((h) => h.ma_dk);
  const chonHetTrang = hetGoiChuaGui && chonDuoc.length > 0 && chonDuoc.every((m) => chon.has(m));

  if (chuaChonDich) {
    return (
      <div className="p-6">
        <div className="max-w-xl rounded-lg border border-warning/40 bg-warning/5 p-4 text-[13px]">
          <div className="font-semibold mb-1 flex items-center gap-2 text-warning"><Icon name="warn" className="w-4 h-4" /> Chưa chọn CSDL đích</div>
          <p className="text-muted-foreground mb-3">Vào Cấu hình để thêm/chọn CSDL đích (GPLX_CDB_CSDT) trước khi cập nhật kết quả đào tạo.</p>
          <button onClick={moCauHinh} className="inline-flex items-center gap-1.5 h-8 px-3 rounded-md bg-kq text-white text-[13px] font-medium hover:brightness-110"><Icon name="settings" className="w-4 h-4" /> Mở Cấu hình</button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {moKiemTruoc && khoa && (
        <KiemTruocKetXuat khoa={khoa} targetKey={targetKey} onDong={() => setMoKiemTruoc(false)}
          onMoHV={(soCccd) => { setMoKiemTruoc(false); setLoc("all"); setQHv(soCccd); setTrang(0); if (hoSo == null || loc !== "all") void taiHoSo(khoa, "all"); }} />
      )}
      {moNapDat && khoa && (
        <NapDatModal maKh={khoa.ma_kh} tenKh={khoa.ten_kh} targetKey={targetKey ?? undefined}
          onClose={() => setMoNapDat(false)} onDone={sauNapDat} />
      )}
      {/* Khung chọn khóa + chương trình + lọc */}
      <div className="shrink-0 bg-card border-b border-border">
        <div className="px-4 pt-3 pb-2 flex items-center gap-2 flex-wrap">
          <h1 className="text-[14px] font-bold">Cập nhật kết quả đào tạo</h1>
          <span className="text-[10px] font-semibold text-kq bg-kq-soft border border-kq-border rounded-full px-1.5 py-px">KQD-01 · KQD-02</span>
          <span className="text-[12px] text-muted-foreground">Gõ điểm gốc thẳng trên lưới — quy đổi &amp; kết luận hiện ngay.</span>
          {khoa && (
            <div className="ml-auto flex items-center gap-2 text-[12px] text-muted-foreground">
              <button onClick={() => setMoKiemTruoc(true)} className="inline-flex items-center gap-1.5 h-8 px-3 mr-2 rounded-lg border border-kq-border bg-kq-soft text-kq text-[12.5px] font-semibold hover:brightness-95">
                <Icon name="check" className="w-4 h-4" /> Kiểm trước kết xuất
                <span className="text-[10px] font-semibold border border-kq-border rounded-full px-1.5">KQD-07</span>
              </button>
              <button onClick={() => setMoNapDat(true)} className="inline-flex items-center gap-1.5 h-8 px-3 mr-2 rounded-lg border border-kq-border bg-kq-soft text-kq text-[12.5px] font-semibold hover:brightness-95" title="Nạp giờ/km thực hành đường của cả khóa từ file PDF báo cáo DAT">
                <Icon name="file" className="w-4 h-4" /> Nạp giờ/km từ PDF DAT
                <span className="text-[10px] font-semibold border border-kq-border rounded-full px-1.5">KQD-08</span>
              </button>
              <button onClick={() => void xuatFile("excel")} disabled={dangXuat} className="inline-flex items-center gap-1.5 h-8 px-3 mr-2 rounded-lg border border-kq-border bg-kq-soft text-kq text-[12.5px] font-semibold hover:brightness-95 disabled:opacity-60" title="Xuất file Excel kết quả học tập của cả khóa đang chọn — lưu vào thư mục output của phần mềm">
                <Icon name={dangXuat ? "refresh" : "download"} className={"w-4 h-4 " + (dangXuat ? "animate-spin" : "")} /> Xuất Excel
                <span className="text-[10px] font-semibold border border-kq-border rounded-full px-1.5">KQD-09</span>
              </button>
              <button onClick={() => void xuatFile("so")} disabled={dangXuat} className="inline-flex items-center gap-1.5 h-8 px-3 mr-2 rounded-lg border border-kq-border bg-kq-soft text-kq text-[12.5px] font-semibold hover:brightness-95 disabled:opacity-60" title="Xuất Sổ theo dõi kết quả học tập (mẫu Phụ lục VI, in A4) — lưu vào thư mục output của phần mềm">
                <Icon name={dangXuat ? "refresh" : "file"} className={"w-4 h-4 " + (dangXuat ? "animate-spin" : "")} /> Xuất Sổ theo dõi
                <span className="text-[10px] font-semibold border border-kq-border rounded-full px-1.5">KQD-10</span>
              </button>
              <span>Chương trình khóa:</span>
              <label className="inline-flex items-center gap-1 cursor-pointer"><input type="radio" name="ct" checked={ct === "cu"} onChange={() => doiCt("cu")} /> Cũ (TT12/2025)</label>
              <label className="inline-flex items-center gap-1 cursor-pointer"><input type="radio" name="ct" checked={ct === "moi"} onChange={() => doiCt("moi")} /> Mới (TT108/2026)</label>
            </div>
          )}
        </div>
        {khoa && gonKhoa ? (
          <div className="px-4 pb-2 flex items-center gap-2 flex-wrap">
            <span className="text-[11px] font-semibold text-muted-foreground">Khóa:</span>
            <span className="text-[13px] font-medium">{khoa.ten_kh} <span className="text-muted-foreground font-normal">· {khoa.ma_kh}</span></span>
            <button onClick={() => { setGonKhoa(false); setMoGoiY(true); }} className="inline-flex items-center gap-1 h-6 px-2 rounded-md border border-border text-[12px] hover:bg-muted">Đổi khóa</button>
            <button onClick={() => setGonKhoa(false)} className="ml-auto inline-flex items-center gap-1 h-6 px-2 rounded-md text-[12px] text-muted-foreground hover:bg-muted" title="Mở rộng khung chọn khóa"><Icon name="expand" className="w-3.5 h-3.5" /> Mở rộng</button>
          </div>
        ) : (
        <div className="px-4 pb-2">
          <div className="flex items-center gap-2">
            <label className="text-[11px] font-semibold text-muted-foreground">Khóa học <span className="font-normal">(chỉ khóa đã có Báo cáo 1 — gõ tên hoặc MaKH để lọc)</span></label>
            {khoa && <button onClick={() => setGonKhoa(true)} className="ml-auto inline-flex items-center gap-1 h-6 px-2 rounded-md text-[12px] text-muted-foreground hover:bg-muted" title="Thu gọn để xem nhiều học viên hơn">Thu gọn</button>}
          </div>
          <div className="relative mt-0.5 max-w-3xl">
            <Icon name="search" className="w-4 h-4 absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input value={q} onChange={(e) => { setQ(e.target.value); setMoGoiY(true); }} onFocus={() => setMoGoiY(true)} placeholder="Gõ tên khóa hoặc MaKH…" className="w-full text-[13px] pl-8 pr-8 py-1.5 rounded-lg border border-input bg-card focus:outline-none focus:border-kq focus:ring-2 focus:ring-kq/20" />
            {loadingKhoa && <Icon name="refresh" className="w-4 h-4 absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground animate-spin" />}
            {moGoiY && khoaList && (
              <div className="absolute z-20 left-0 right-0 mt-1 max-h-72 overflow-auto rounded-lg border border-border bg-card shadow-lg">
                {khoaList.length === 0 ? (
                  <div className="px-3 py-3 text-[13px] text-muted-foreground">Không có khóa khớp (chỉ hiện khóa đã BC1).</div>
                ) : (
                  khoaList.map((k) => (
                    <button key={k.ma_kh} onClick={() => chonKhoa(k)} className="w-full text-left px-3 py-2 hover:bg-kq-soft border-b border-border/70 last:border-0">
                      <div className="text-[13px] font-medium">{k.ten_kh} <span className="text-muted-foreground font-normal">· {k.ma_kh}</span></div>
                      <div className="text-[11.5px] text-muted-foreground tabular-nums">hạng {k.hang_gplx} · KG {k.ngay_kg ?? "—"} · Đã đăng ký {k.dem.dangky} · Đã cập nhật {k.dem.capnhat}{k.dem.tuchoi > 0 && <> · Sở từ chối {k.dem.tuchoi}</>}{k.dem.giaitrinh > 0 && <> · Giải trình {k.dem.giaitrinh}</>}</div>
                    </button>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
        )}
        {khoa && (
          <div className="px-4 py-1.5 border-t border-border/70 bg-muted/30 flex items-center gap-2 flex-wrap">
            <span className="text-[12px] text-muted-foreground mr-1">Lọc trạng thái:</span>
            {BO_LOC.map((b) => (
              <button key={b.key} onClick={() => chonLoc(b.key)} className={"px-2.5 py-1 rounded-full text-[12px] border transition-colors " + (loc === b.key ? "bg-kq text-white border-kq" : "border-border hover:bg-muted")}>{b.label}</button>
            ))}
            <div className="relative ml-auto">
              <Icon name="search" className="w-4 h-4 absolute left-2.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
              <input value={qHv} onChange={(e) => { setQHv(e.target.value); setTrang(0); }} placeholder="Tìm tên / CCCD" className="w-56 text-[13px] pl-8 pr-2 py-1 rounded-lg border border-input bg-card focus:outline-none focus:border-kq" />
            </div>
          </div>
        )}
      </div>

      {toast && (
        <div className="shrink-0 px-4 py-1.5 bg-kq-soft border-b border-kq-border text-[12.5px] text-kq flex items-center gap-2">
          <Icon name="check" className="w-4 h-4" sw={3} /> {toast}
          {fileXuat && (
            <button onClick={() => void moThuMuc()} className="ml-2 inline-flex items-center gap-1 h-6 px-2 rounded-md border border-kq-border bg-card text-[12px] font-semibold hover:brightness-95">
              <Icon name="file" className="w-3.5 h-3.5" /> Mở thư mục
            </button>
          )}
          <button onClick={() => { setToast(""); setFileXuat(null); }} className="ml-auto text-muted-foreground hover:text-foreground"><Icon name="x" className="w-3.5 h-3.5" /></button>
        </div>
      )}

      {khoa && soChoKxKhoa > 0 && (
        <div className="shrink-0 px-4 py-1.5 bg-warning/10 border-b border-warning/40 text-[12.5px] text-warning flex items-start gap-2">
          <Icon name="warn" className="w-4 h-4 mt-0.5 shrink-0" />
          <span><b>{soChoKxKhoa.toLocaleString("vi-VN")} học viên</b> đã sửa sau khi gửi Sở, <b>chưa kết xuất lại</b> — mở phần mềm CDB để kết xuất. Để lâu, nếu Sở trả kết quả thì học viên sẽ bị kẹt.</span>
        </div>
      )}

      <div className="flex-1 min-h-0 p-4 flex flex-col">
        {!khoa ? (
          <div className="text-[13px] text-muted-foreground max-w-xl rounded-lg border border-dashed border-border bg-card p-8 text-center">Chọn một khóa học ở trên để xem/nhập kết quả học viên.</div>
        ) : err ? (
          <div className="text-[13px] text-destructive">{err}</div>
        ) : loadingHv ? (
          <div className="text-[13px] text-muted-foreground inline-flex items-center gap-2"><Icon name="refresh" className="w-4 h-4 animate-spin" /> Đang tải danh sách…</div>
        ) : hoSoLoc && hoSoLoc.length === 0 ? (
          <div className="text-[13px] text-muted-foreground max-w-xl rounded-lg border border-dashed border-border bg-card p-8 text-center">Khóa này không có học viên ở bộ lọc đang chọn.</div>
        ) : (
          <>
            <div className="rounded-lg border border-border bg-card overflow-auto flex-1 min-h-0">
              <table className="w-full table-fixed text-[13px] border-collapse min-w-[1208px]">
                <thead className="sticky top-0 z-10">
                  <tr className="bg-kq text-white text-left">
                    <th className="font-semibold px-2 py-1.5 w-10 text-center">
                      {hetGoiChuaGui && chonDuoc.length > 0 ? (
                        <input type="checkbox" checked={chonHetTrang} aria-label="Chọn tất cả học viên đã gửi Sở ở trang này"
                          title="Chọn tất cả học viên đã gửi Sở ở trang này"
                          onChange={(e) => setChon((cur) => { const c = new Set(cur); chonDuoc.forEach((m) => (e.target.checked ? c.add(m) : c.delete(m))); return c; })} />
                      ) : "STT"}
                    </th>
                    <th className="font-semibold px-2 py-1.5 w-[200px]">Họ và tên</th>
                    <th className="font-semibold px-2 py-1.5 w-[116px]">Số CCCD</th>
                    <th className="font-semibold px-2 py-1.5 w-12 text-center">Hạng</th>
                    {["Lý thuyết", "Mô phỏng", "Sa hình", "Chữ chi", "Đường trường"].map((m, i) => (
                      <th key={m} className="font-semibold px-1 py-1.5 w-[62px] text-center">{m}<div className="text-[10px] font-normal opacity-80">{MON_NHAN[MON5[i]]}</div></th>
                    ))}
                    <th className="font-semibold px-1 py-1.5 w-[62px] text-center">Giờ đường</th>
                    <th className="font-semibold px-1 py-1.5 w-[66px] text-center">Km đường</th>
                    <th className="font-semibold px-2 py-1.5 w-[132px] text-center">Kết luận</th>
                    <th className="font-semibold px-2 py-1.5 w-[150px] text-center">Lưu · Chi tiết</th>
                    <th className="w-full" aria-hidden></th>
                  </tr>
                </thead>
                <tbody>
                  {trenTrang.map((h, i) => {
                    const khoaDong = h.tt_xuly === "12" || h.tt_xuly === "13";
                    const cat = phanLoaiHang(h.ma_hang_moi, h.ma_hang);
                    const gk = cat ? GIO_KM[cat] : null;
                    const nr = nhap[h.ma_dk] ?? gocNhap(h);
                    const t = tinhDong(nr, cat, ct, monBatBuoc);
                    const stt = trang * coTrang + i + 1;
                    if (khoaDong) {
                      // dòng chỉ-đọc (đã kết xuất/hoàn thành) — hiện điểm đã lưu
                      return (
                        <tr key={h.ma_dk} className="border-b border-border/80 bg-muted/20 text-muted-foreground align-top">
                          <td className="px-2 py-2 text-center tabular-nums">
                            {hetGoiChuaGui && h.tt_xuly === "12"
                              ? <input type="checkbox" checked={chon.has(h.ma_dk)} onChange={(e) => bangChon(h.ma_dk, e.target.checked)} aria-label={`Chọn ${h.ho_ten}`} />
                              : stt}
                          </td>
                          <td className="px-2 py-2 font-medium truncate" title={h.ho_ten}>{h.ho_ten}<div className="text-[11px] tabular-nums">{h.ngay_sinh}</div></td>
                          <td className="px-2 py-2 font-mono text-[12px]">{h.so_cccd}</td>
                          <td className="px-2 py-2 text-center">{h.hang ?? "—"}</td>
                          {MON5.map((m) => (<td key={m} className="px-1 py-2 text-center tabular-nums">{d1(h.diem[m])}</td>))}
                          <td className="px-1 py-2 text-center">—</td>
                          <td className="px-1 py-2 text-center">—</td>
                          <td className="px-2 py-2 text-center">{h.ket_luan === "dat" ? <span className="text-[11px] font-semibold text-success">Đạt</span> : h.ket_luan === "khong_dat" ? <span className="text-[11px] font-semibold text-destructive">Không đạt</span> : "—"}</td>
                          <td className="px-2 py-2 text-center"><span className="text-[12px]">🔒 chỉ xem</span><div className="mt-0.5">
                            {hetGoiChuaGui && h.tt_xuly === "12"
                              ? <span className="inline-block text-[11px] font-semibold border rounded-full px-2 py-0.5 whitespace-nowrap text-muted-foreground bg-muted border-border">Đã gửi Sở</span>
                              : ttBadge(h.tt_xuly)}
                          </div></td>
                          <td className="px-2 py-2 text-center">{h.tt_xuly === "12" && !hetGoiChuaGui && (
                            <button onClick={() => setMoKhoaMo(true)} className="inline-flex items-center gap-1 h-7 px-2 rounded-md border border-kq/50 text-kq text-[11.5px] font-medium hover:bg-kq-soft whitespace-nowrap" title="Mở khóa để sửa điểm (thao tác toàn cơ sở)">
                              <Icon name="clock" className="w-3.5 h-3.5" /> Mở khóa
                            </button>
                          )}</td>
                        </tr>
                      );
                    }
                    const suaLai = h.tt_xuly === "14" || h.tt_xuly === "90";
                    const cell = (m: typeof MON5[number]) => {
                      const qd = t.qd[m];
                      const col = t.over[m] ? "text-destructive" : qd == null ? "text-muted-foreground" : qd >= 5 ? "text-success" : "text-destructive";
                      return (
                        <td key={m} className="px-1 py-2 text-center align-top">
                          <input value={nr[m]} onChange={(e) => setNhapO(h, m, e.target.value)} inputMode="decimal"
                            data-kqd-r={i} data-kqd-c={MON5.indexOf(m)} onKeyDown={(e) => navGrid(e, i, MON5.indexOf(m))}
                            className={"w-[50px] h-7 text-center tabular-nums text-[13px] font-semibold rounded-md border bg-card focus:outline-none focus:border-kq " + (t.over[m] || (t.thieu[m] && h.diem[m] == null) ? "border-destructive" : "border-input")} />
                          <div className={"text-[11px] tabular-nums mt-0.5 leading-none " + col}>{hintDiem(t.over[m], qd, h.diem[m])}</div>
                        </td>
                      );
                    };
                    const gyGio = gk?.gyGio, gyKm = gk?.gyKm;
                    const gioP = parseGio(nr.gio_duong);
                    const gioSai = gioP === "sai";
                    const gioVal = typeof gioP === "number" ? gioP : null, kmVal = parseNum(nr.km_duong);
                    const gioKmDoi = !bangNhau(gioSai ? null : gioVal, h.gio_duong) || !bangNhau(kmVal, h.km_duong);
                    return (
                      <tr key={h.ma_dk} className="border-b border-border/80 hover:bg-kq-soft/40 align-top">
                        <td className="px-2 py-2 text-center tabular-nums text-muted-foreground">{stt}</td>
                        <td className="px-2 py-2 font-medium truncate" title={h.ho_ten}>{h.ho_ten}<div className="text-[11px] text-muted-foreground tabular-nums">{h.ngay_sinh}</div></td>
                        <td className="px-2 py-2 font-mono text-[12px]">{h.so_cccd}</td>
                        <td className="px-2 py-2 text-center">{h.hang ?? "—"}</td>
                        {MON5.map(cell)}
                        <td className="px-1 py-2 text-center align-top">
                          <input value={nr.gio_duong} onChange={(e) => setNhapO(h, "gio_duong", e.target.value)} onBlur={(e) => { const v = chuanHoaGio(e.target.value); if (v !== e.target.value) setNhapO(h, "gio_duong", v); }}
                            inputMode="decimal" placeholder={gyGio ? `≥${gyGio}` : ""} title={gioSai ? "Gõ số (20,5) hoặc hh:mm (20:30), phút < 60" : "Số thập phân hoặc hh:mm (vd 20:30 → 20,5)"}
                            data-kqd-r={i} data-kqd-c={5} onKeyDown={(e) => navGrid(e, i, 5)}
                            className={"w-[50px] h-7 text-center tabular-nums text-[12.5px] rounded-md border bg-card focus:outline-none focus:border-kq " + (gioSai ? "border-destructive" : gyGio != null && gioVal != null && gioVal < gyGio ? "border-warning bg-warning/5" : "border-input")} />
                        </td>
                        <td className="px-1 py-2 text-center align-top">
                          <input value={nr.km_duong} onChange={(e) => setNhapO(h, "km_duong", e.target.value)} inputMode="decimal" placeholder={gyKm ? `≥${gyKm}` : ""}
                            data-kqd-r={i} data-kqd-c={6} onKeyDown={(e) => navGrid(e, i, 6)}
                            className={"w-[56px] h-7 text-center tabular-nums text-[12.5px] rounded-md border bg-card focus:outline-none focus:border-kq " + (gyKm != null && kmVal != null && kmVal < gyKm ? "border-warning bg-warning/5" : "border-input")} />
                        </td>
                        <td className="px-2 py-2 text-center align-top">
                          {!t.full ? (
                            h.ket_luan === "dat" ? <span className="text-[11px] font-semibold text-success bg-success/10 border border-success/40 rounded-full px-2 py-0.5">Đạt · đã lưu</span>
                            : h.ket_luan === "khong_dat" ? <span className="text-[11px] font-semibold text-destructive bg-destructive/10 border border-destructive/40 rounded-full px-2 py-0.5">Không đạt · đã lưu</span>
                            : <span className="text-[11px] text-muted-foreground">đang nhập…</span>
                          ) : t.dat ? <span className="text-[12px] font-bold text-success bg-success/10 border border-success/50 rounded-full px-2.5 py-0.5">✓ ĐẠT</span>
                            : <span className="text-[12px] font-bold text-destructive bg-destructive/10 border border-destructive/50 rounded-full px-2.5 py-0.5">✗ Không đạt</span>}
                          {suaLai && <div className="mt-1">{ttBadge(h.tt_xuly)}</div>}
                          {choKxTheoDk.has(h.ma_dk) && (
                            <div className="mt-1"><span title={`Mở sửa ${choKxTheoDk.get(h.ma_dk)?.luc_mo ?? ""} — ${choKxTheoDk.get(h.ma_dk)?.ly_do ?? ""}`} className="inline-block text-[10.5px] leading-tight font-semibold border rounded-md px-1.5 py-0.5 text-warning bg-warning/10 border-warning/50">Sửa sau gửi — chưa kết xuất lại</span></div>
                          )}
                        </td>
                        <td className="px-2 py-2 align-top">
                          <div className="flex items-center justify-center gap-1.5">
                            <button disabled={!(MON5.some((m) => parseNum(nr[m]) != null) || gioKmDoi) || luuBusy === h.ma_dk} onClick={() => luu(h)}
                              className="h-7 px-2.5 rounded-md bg-kq text-white text-[12px] font-medium hover:brightness-110 disabled:opacity-40 disabled:cursor-not-allowed inline-flex items-center justify-center gap-1 whitespace-nowrap">
                              {luuBusy === h.ma_dk ? <Icon name="refresh" className="w-3.5 h-3.5 animate-spin" /> : null} Lưu
                            </button>
                            <button onClick={() => moDrawer(h)} className={"h-7 px-2 rounded-md border text-[11px] font-medium hover:bg-muted whitespace-nowrap " + (suaLai ? "border-destructive/40 text-destructive hover:bg-destructive/5" : "border-border text-muted-foreground")}>{suaLai ? "Giải trình" : "Chi tiết"}</button>
                          </div>
                        </td>
                        <td aria-hidden></td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            {hetGoiChuaGui && hvChon.length > 0 && (
              <div className="shrink-0 mt-2 rounded-lg border border-kq-border bg-kq-soft px-3 py-2 flex items-center gap-3 text-[13px]">
                <span>Đã chọn <b className="tabular-nums">{hvChon.length.toLocaleString("vi-VN")}</b> học viên đã gửi Sở</span>
                <button onClick={() => setChon(new Set())} className="text-[12px] text-muted-foreground hover:text-foreground underline">Bỏ chọn</button>
                <button onClick={() => setSuaMo(true)} className="ml-auto h-8 px-4 rounded-lg bg-kq text-white font-semibold text-[13px] hover:brightness-110 inline-flex items-center gap-1.5">
                  <Icon name="clock" className="w-4 h-4" /> Mở sửa điểm
                </button>
              </div>
            )}
            {hetGoiChuaGui && hvChon.length === 0 && trenTrang.some((h) => h.tt_xuly === "12") && (
              <p className="text-[12px] text-muted-foreground mt-2">Học viên <b className="text-foreground">đã gửi Sở</b>: tích chọn rồi bấm <b className="text-foreground">Mở sửa điểm</b> để sửa/bổ sung điểm (phải kết xuất lại sau đó).</p>
            )}
            {hoSoLoc && <PhanTrang total={hoSoLoc.length} trang={trang} coTrang={coTrang} onTrang={setTrang} onCoTrang={(c) => { setCoTrang(c); setTrang(0); }} cacCo={[50, 20, 100]} />}
            <p className="text-[12px] text-muted-foreground mt-2">Ngưỡng đạt từng môn = <b className="text-foreground">5,0</b> (xét trên điểm chưa làm tròn). Giờ sân · km sân · số giấy HTKH · ngày cấp → trong <b>Chi tiết</b> mỗi dòng.</p>
          </>
        )}
      </div>

      {/* Drawer Chi tiết (phần phụ, phần lớn tự điền) */}
      {drawer && (() => {
        const cat = phanLoaiHang(drawer.ma_hang_moi, drawer.ma_hang);
        const gk = cat ? GIO_KM[cat] : null;
        return (
          <div className="fixed inset-0 z-50">
            <div className="absolute inset-0 bg-black/30" onClick={() => setDrawer(null)} />
            <div className="absolute right-0 top-0 h-full w-[420px] bg-card shadow-2xl flex flex-col">
              <div className="shrink-0 px-4 py-3 border-b border-border flex items-center gap-3">
                <div><div className="font-bold text-[15px]">{drawer.ho_ten}</div><div className="text-[12px] text-muted-foreground font-mono">{drawer.ma_dk}</div></div>
                <button onClick={() => setDrawer(null)} className="ml-auto text-muted-foreground hover:text-foreground"><Icon name="x" className="w-5 h-5" /></button>
              </div>
              <div className="flex-1 overflow-auto px-4 py-3 space-y-4">
                <p className="text-[11px] text-muted-foreground -mb-1">Điểm &amp; giờ/km đường nhập ở lưới. Đây là phần phụ, phần lớn tự điền.</p>
                <div>
                  <div className="text-[12px] font-bold text-kq mb-2">Thực hành sân <span className="text-[11px] font-normal text-muted-foreground">(TT17)</span></div>
                  <div className="grid grid-cols-2 gap-3">
                    <div><label className="text-[11px] font-semibold text-muted-foreground">Giờ sân (khóa cứng)</label><input readOnly value={gk ? String(gk.gioSan) : "—"} className="w-full text-[13px] mt-0.5 px-2 py-1.5 rounded-lg border border-input bg-muted/60" /></div>
                    <div><label className="text-[11px] font-semibold text-muted-foreground">Km sân (điền sẵn)</label><input value={ct_detail.km_san} onChange={(e) => setCtDetail((c) => ({ ...c, km_san: e.target.value }))} className="w-full text-[13px] mt-0.5 px-2 py-1.5 rounded-lg border border-input bg-card focus:outline-none focus:border-kq" /></div>
                  </div>
                </div>
                <div>
                  <div className="text-[12px] font-bold text-kq mb-2">Giấy chứng nhận HTKH <span className="text-[11px] font-normal text-muted-foreground">(số tự sinh khi Đạt)</span></div>
                  <div className="grid grid-cols-2 gap-3">
                    <div><label className="text-[11px] font-semibold text-muted-foreground">Ngày cấp HTKH</label><input value={ct_detail.ngay_htkh} onChange={(e) => setCtDetail((c) => ({ ...c, ngay_htkh: e.target.value }))} placeholder="dd/mm/yyyy" className="w-full text-[13px] mt-0.5 px-2 py-1.5 rounded-lg border border-input bg-card focus:outline-none focus:border-kq" /></div>
                    <div />
                    <div><label className="text-[11px] font-semibold text-muted-foreground">TG bắt đầu</label><input value={ct_detail.tg_bat_dau} onChange={(e) => setCtDetail((c) => ({ ...c, tg_bat_dau: e.target.value }))} placeholder="dd/mm/yyyy" className="w-full text-[13px] mt-0.5 px-2 py-1.5 rounded-lg border border-input bg-card focus:outline-none focus:border-kq" /></div>
                    <div><label className="text-[11px] font-semibold text-muted-foreground">TG kết thúc</label><input value={ct_detail.tg_ket_thuc} onChange={(e) => setCtDetail((c) => ({ ...c, tg_ket_thuc: e.target.value }))} placeholder="dd/mm/yyyy" className="w-full text-[13px] mt-0.5 px-2 py-1.5 rounded-lg border border-input bg-card focus:outline-none focus:border-kq" /></div>
                  </div>
                  <p className="text-[11px] text-muted-foreground mt-1.5">Các giá trị này áp khi bấm <b>Lưu</b> ở dòng tương ứng.</p>
                </div>
                {/* KQD-04 — HV Sở từ chối (14) / đang giải trình (90): lý do từ chối + ô giải trình */}
                {(drawer.tt_xuly === "14" || drawer.tt_xuly === "90") && (
                  <div>
                    <div className="text-[12px] font-bold text-kq mb-2">Sửa lại — giải trình</div>
                    <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-2.5 mb-2">
                      <div className="text-[11px] font-semibold text-destructive mb-0.5">Lý do Sở từ chối (chỉ đọc — do Sở ghi)</div>
                      <div className="text-[13px]">{lyDo[drawer.ma_dk] ?? "— (không có / đang đọc)"}</div>
                    </div>
                    <label className="text-[11px] font-semibold text-muted-foreground">Nội dung giải trình <span className="font-normal">(ghi cột GiaiTrinh, tối đa 1000 ký tự — ghi trước khi cập nhật điểm)</span></label>
                    <textarea
                      value={giaiTrinh[drawer.ma_dk] ?? ""}
                      maxLength={1000}
                      onChange={(e) => setGiaiTrinh((c) => ({ ...c, [drawer.ma_dk]: e.target.value }))}
                      placeholder="Nhập nội dung giải trình gửi kèm khi nộp lại…"
                      className="w-full h-24 text-[13px] mt-1 px-2 py-1.5 rounded-lg border border-input bg-card focus:outline-none focus:border-kq resize-none"
                    />
                  </div>
                )}
              </div>
              <div className="shrink-0 px-4 py-3 border-t border-border flex items-center gap-2">
                {/* KQD-06: xóa điểm — chỉ HV đã cập nhật chưa kết xuất (09/10) */}
                {(drawer.tt_xuly === "09" || drawer.tt_xuly === "10") && (
                  xacNhanXoa ? (
                    <div className="mr-auto flex items-center gap-1.5">
                      <span className="text-[12px] text-destructive font-medium">Xóa hết điểm, về chưa có điểm?</span>
                      <button disabled={luuBusy === drawer.ma_dk} onClick={() => xoaDiem(drawer)} className="h-8 px-3 rounded-md bg-destructive text-white text-[12px] font-semibold hover:brightness-110 disabled:opacity-50 inline-flex items-center gap-1">{luuBusy === drawer.ma_dk && <Icon name="refresh" className="w-3.5 h-3.5 animate-spin" />} Xóa điểm</button>
                      <button onClick={() => setXacNhanXoa(false)} className="h-8 px-2 rounded-md border border-border text-[12px] hover:bg-muted">Hủy</button>
                    </div>
                  ) : (
                    <button onClick={() => setXacNhanXoa(true)} className="mr-auto h-8 px-3 rounded-md border border-destructive/50 text-destructive text-[12px] font-medium hover:bg-destructive/5">Xóa điểm</button>
                  )
                )}
                <button onClick={() => setDrawer(null)} className="h-9 px-4 rounded-lg border border-border text-[13px] hover:bg-muted">Đóng</button>
                <button onClick={() => setDrawer(null)} className="h-9 px-5 rounded-lg bg-kq text-white font-semibold text-[13px] hover:brightness-110">Xong</button>
              </div>
            </div>
          </div>
        );
      })()}

      {moKhoaMo && (
        <MoKhoaModal targetKey={targetKey ?? undefined} maKh={khoa?.ma_kh ?? null} onClose={() => setMoKhoaMo(false)} onDone={sauMoKhoa} />
      )}

      {suaMo && (
        <SuaSauGuiModal
          targetKey={targetKey ?? undefined}
          hv={hvChon}
          onClose={() => setSuaMo(false)}
          onDone={sauSuaSauGui}
          onGoiDoi={() => { taiGoiVaChoKx(); setChon(new Set()); }}
        />
      )}
    </div>
  );
}
