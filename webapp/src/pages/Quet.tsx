import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Icon } from "../components/Icon";
import { ODate } from "../components/ODate";
import { ApiError, kiemTrungCccd, type KiemTrungKq } from "../lib/api";
import { kiemDoDaiTen, parseCccdQr, tinhVungQuet, type CccdFields, type GioiTinh } from "../lib/qr";
import { capNhatNhap, dsNhap, luuNhap, taoUuid, tuCccd } from "../lib/draft";
import { dangKyGuiLai, guiMot } from "../lib/gui";

// THU-01 quét QR + preview sửa; THU-02 chụp ảnh chân dung + gửi VPS.
// Luồng: quét/nhập → preview (sửa) → giữ nháp → chụp ảnh → gửi (POST /api/ho-so + /anh).
// Bám bố cục ui-demo/src/pages/app/Quet.tsx. Mất mạng → giữ nháp, tự gửi lại khi online (lib/gui).
// Cách quét (BarcodeDetector→qr-scanner, auto-capture 2 frame) tham khảo webThanhdat — memory ref-quet-qr-cccd.

// ---- Decoder cascade: BarcodeDetector native → qr-scanner (ZXing) ----
// Hộp (box) = vị trí mã QR trong khung hình (px canvas) để vẽ khung bám (THU-01, CHANGES #12).
// BarcodeDetector trả boundingBox; qr-scanner không có → box = null (dùng khung ngắm tĩnh).
interface DetectedBarcode {
  rawValue: string;
  boundingBox?: { x: number; y: number; width: number; height: number };
}
interface BarcodeDetectorLike {
  detect(src: CanvasImageSource): Promise<DetectedBarcode[]>;
}
type BarcodeDetectorCtor = new (opts: { formats: string[] }) => BarcodeDetectorLike;

type Box = { x: number; y: number; w: number; h: number };
type KetQuaGiaiMa = { raw: string; box: Box | null };

async function decodeTuCanvas(
  canvas: HTMLCanvasElement,
  detector: { cur: BarcodeDetectorLike | null },
): Promise<KetQuaGiaiMa | null> {
  const Ctor = (globalThis as { BarcodeDetector?: BarcodeDetectorCtor }).BarcodeDetector;
  if (Ctor) {
    try {
      if (!detector.cur) detector.cur = new Ctor({ formats: ["qr_code"] });
      const res = await detector.cur.detect(canvas);
      if (res.length === 0) return null;
      const b = res[0].boundingBox;
      return { raw: res[0].rawValue, box: b ? { x: b.x, y: b.y, w: b.width, h: b.height } : null };
    } catch {
      // trình duyệt báo lỗi → rơi xuống qr-scanner
    }
  }
  try {
    const QrScanner = (await import("qr-scanner")).default;
    const r = await QrScanner.scanImage(canvas, { returnDetailedScanResult: true });
    return { raw: r.data, box: null };
  } catch {
    return null;
  }
}

async function decodeTuFile(file: File): Promise<string | null> {
  try {
    const QrScanner = (await import("qr-scanner")).default;
    const r = await QrScanner.scanImage(file, { returnDetailedScanResult: true });
    return r.data;
  } catch {
    return null;
  }
}

function giaiThichLoiCamera(err: unknown): string {
  if (typeof window !== "undefined" && !window.isSecureContext)
    return "Trình duyệt chặn camera vì trang không chạy trên HTTPS. Hãy tải ảnh CCCD hoặc nhập tay.";
  const name = (err as { name?: string })?.name ?? "";
  switch (name) {
    case "NotAllowedError":
    case "SecurityError":
      return "Bạn chưa cho phép dùng camera. Mở lại quyền camera trong trình duyệt, hoặc tải ảnh CCCD / nhập tay.";
    case "NotFoundError":
    case "OverconstrainedError":
      return "Không tìm thấy camera phù hợp trên thiết bị. Hãy tải ảnh CCCD hoặc nhập tay.";
    case "NotReadableError":
      return "Camera đang bị ứng dụng khác chiếm. Đóng app đang dùng camera rồi thử lại, hoặc tải ảnh CCCD.";
    default:
      return "Không mở được camera. Hãy tải ảnh CCCD hoặc nhập tay.";
  }
}

const FIELDS_RONG: CccdFields = {
  soCccd: "",
  soCmndCu: "",
  hoTen: "",
  ngaySinh: "",
  gioiTinh: "Nam",
  noiThuongTru: "",
  ngayCap: "",
};

// Desktop ≥ lg (1024px, khớp breakpoint Tailwind). Dùng để quyết điểm vào màn Quét:
// desktop → vào thẳng form nhập tay + popover quét; mobile → cổng chọn + camera toàn màn (CHANGES #30).
const MQ_DESKTOP = "(min-width: 1024px)";
function docDesktop(): boolean {
  return typeof window !== "undefined" && window.matchMedia(MQ_DESKTOP).matches;
}
function useIsDesktop(): boolean {
  const [v, setV] = useState(docDesktop);
  useEffect(() => {
    const mq = window.matchMedia(MQ_DESKTOP);
    const on = () => setV(mq.matches);
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);
  return v;
}

type GiaiDoan = "chon" | "quet" | "preview" | "anh" | "ketqua";

export default function Quet() {
  const isDesktop = useIsDesktop();
  // Điểm vào: mobile = "chon" (cổng chọn, KHÔNG tự mở camera — CHANGES #12);
  // desktop = "preview" (vào thẳng form nhập tay, quét là phụ qua popover — CHANGES #30).
  const [giaiDoan, setGiaiDoan] = useState<GiaiDoan>(() => (docDesktop() ? "preview" : "chon"));
  const [fields, setFields] = useState<CccdFields>(FIELDS_RONG);
  const [formKey, setFormKey] = useState(0); // bump → remount form (reseed sau quét / nhập tiếp)
  const [quetPopover, setQuetPopover] = useState(false); // desktop: popover camera đè form
  const [loiQuet, setLoiQuet] = useState<string | null>(null);
  const [loiChon, setLoiChon] = useState<string | null>(null);
  const [uuid, setUuid] = useState<string>("");
  const [offline, setOffline] = useState(false);
  const [toast, setToast] = useState<{ msg: string; ok: boolean } | null>(null);
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  // THU-06: OCR đọc chữ mặt trước CCCD làm lối nhập dự phòng (chạy client, ảnh không rời máy).
  const [dangOcr, setDangOcr] = useState(false); // spinner trong lúc OCR (có thể vài giây)
  const [canhBaoOcr, setCanhBaoOcr] = useState<string[] | null>(null); // trường cần soát sau OCR
  const ocrHuy = useRef(false); // user bấm Hủy giữa chừng → bỏ kết quả OCR

  // Có mạng trở lại → tự gửi lại nháp còn tồn.
  useEffect(() => {
    dangKyGuiLai();
    return () => { if (toastTimer.current) clearTimeout(toastTimer.current); };
  }, []);

  // Co màn hình từ mobile → desktop trong lúc đang ở cổng chọn: desktop không có cổng,
  // chuyển sang form nhập tay cho khỏi kẹt ở màn trống.
  useEffect(() => {
    if (isDesktop && giaiDoan === "chon") setGiaiDoan("preview");
  }, [isDesktop, giaiDoan]);

  function baoToast(msg: string, ok: boolean) {
    setToast({ msg, ok });
    if (toastTimer.current) clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(null), 2800);
  }

  // "Lưu & nhập hồ sơ tiếp" (CHANGES #13): gửi KHÔNG ảnh → toast → về màn chọn cách nhập.
  // Về màn chọn ngay cho mượt; gửi chạy nền, báo kết quả bằng toast (mất mạng vẫn giữ nháp).
  async function luuVaTiep(id: string) {
    const hs = dsNhap().find((x) => x.uuid === id);
    quetTiep();
    if (!hs) return;
    try {
      await guiMot(hs);
      baoToast("Đã gửi ✓", true);
    } catch (err) {
      if (err instanceof ApiError) baoToast(err.message, false);
      else baoToast("Đã lưu — sẽ tự gửi khi có mạng", false);
    }
  }

  // Có dữ liệu (quét QR / tải ảnh / OCR) → điền vào form. Desktop: đóng popover + reseed form đang mở.
  // canhBao: danh sách trường cần soát (OCR điền một phần); QR thì bỏ trống.
  const batDau = useCallback((f: CccdFields, canhBao?: string[]) => {
    setFields(f);
    setCanhBaoOcr(canhBao ?? null);
    setLoiQuet(null);
    setFormKey((k) => k + 1);
    setQuetPopover(false);
    setGiaiDoan("preview");
  }, []);

  function nhapTay() {
    setFields(FIELDS_RONG);
    setCanhBaoOcr(null);
    setLoiQuet(null);
    setFormKey((k) => k + 1);
    setGiaiDoan("preview");
  }

  // Làm hồ sơ kế tiếp: desktop về form trống (không có cổng chọn), mobile về cổng chọn.
  function quetTiep() {
    setFields(FIELDS_RONG);
    setCanhBaoOcr(null);
    setUuid("");
    setOffline(false);
    setLoiQuet(null);
    setLoiChon(null);
    setQuetPopover(false);
    setFormKey((k) => k + 1);
    setGiaiDoan(isDesktop ? "preview" : "chon");
  }

  // Tải ảnh CCCD từ máy → đọc QR. onErr nhận chỗ hiện lỗi (mobile: banner cổng; desktop: toast).
  async function docAnh(file: File, onErr: (m: string) => void) {
    const raw = await decodeTuFile(file);
    if (!raw) {
      onErr("Không đọc được mã QR trong ảnh. Thử ảnh rõ nét hơn hoặc nhập tay.");
      return;
    }
    const r = parseCccdQr(raw);
    if (!r.ok) {
      onErr(r.message);
      return;
    }
    batDau(r.data);
  }

  // THU-06: chụp/tải ảnh MẶT TRƯỚC thẻ → OCR (client) điền sẵn 5 trường. Ngày cấp ở mặt sau
  // → để trống, nhân viên nhập tay. Không đọc được CCCD 12 số → báo lỗi, không điền bừa.
  const NHAN_OCR: Record<string, string> = {
    soCccd: "Số CCCD",
    hoTen: "Họ và tên",
    ngaySinh: "Ngày sinh",
    gioiTinh: "Giới tính",
    noiThuongTru: "Nơi thường trú",
    ngayCap: "Ngày cấp (ở mặt sau thẻ — nhập tay)",
  };
  async function docOcr(file: File, onErr: (m: string) => void) {
    ocrHuy.current = false;
    setDangOcr(true);
    try {
      const { docTheCccd } = await import("../lib/ocr"); // tải Tesseract.js chỉ khi dùng
      const r = await docTheCccd(file);
      if (ocrHuy.current) return; // user đã bấm Hủy → bỏ kết quả
      if (!r.ok) {
        onErr(r.message);
        return;
      }
      const d = r.ket.data;
      batDau(
        {
          soCccd: d.soCccd,
          soCmndCu: "",
          hoTen: d.hoTen,
          ngaySinh: d.ngaySinh,
          gioiTinh: (d.gioiTinh || FIELDS_RONG.gioiTinh) as GioiTinh,
          noiThuongTru: d.noiThuongTru,
          ngayCap: "",
        },
        r.ket.danhDau.map((k) => NHAN_OCR[k] ?? k),
      );
    } catch {
      if (!ocrHuy.current) onErr("Không đọc được thẻ — thử lại hoặc chuyển Nhập tay.");
    } finally {
      if (!ocrHuy.current) setDangOcr(false);
    }
  }
  function huyOcr() {
    ocrHuy.current = true;
    setDangOcr(false);
    nhapTay(); // chuyển thẳng sang Nhập tay cho mượt
  }

  return (
    <div className="h-full flex flex-col lg:h-auto lg:p-6 lg:max-w-2xl lg:mx-auto">
      {/* Cổng chọn + camera toàn màn: CHỈ mobile. Desktop vào thẳng form (CHANGES #30). */}
      {giaiDoan === "chon" && !isDesktop && (
        <ChonCach onQuet={() => { setLoiChon(null); setGiaiDoan("quet"); }} onNhapTay={nhapTay} onAnhFile={(f) => void docAnh(f, setLoiChon)} onOcrFile={(f) => void docOcr(f, setLoiChon)} loi={loiChon} />
      )}
      {giaiDoan === "quet" && !isDesktop && (
        <KhungQuet onQuet={batDau} onNhapTay={nhapTay} onQuayLai={() => setGiaiDoan("chon")} loi={loiQuet} setLoi={setLoiQuet} />
      )}
      {(giaiDoan === "preview" || giaiDoan === "anh" || giaiDoan === "ketqua") && (
        <div className="flex-1 min-h-0 overflow-y-auto p-4 lg:p-0">
          {giaiDoan === "preview" && (
            <Preview
              key={formKey}
              fields={fields}
              isDesktop={isDesktop}
              canhBaoOcr={canhBaoOcr}
              onMoQuet={() => { setLoiQuet(null); setQuetPopover(true); }}
              onAnhFile={(f) => void docAnh(f, (m) => baoToast(m, false))}
              onOcrFile={(f) => void docOcr(f, (m) => baoToast(m, false))}
              onLuu={(id) => { setUuid(id); setGiaiDoan("anh"); }}
              onLuuVaTiep={luuVaTiep}
              onQuetLai={quetTiep}
            />
          )}
          {giaiDoan === "anh" && (
            <ChupAnhGui uuid={uuid} onXong={(mangYeu) => { setOffline(mangYeu); setGiaiDoan("ketqua"); }} />
          )}
          {giaiDoan === "ketqua" && <KetQua offline={offline} onQuetTiep={quetTiep} />}
        </div>
      )}

      {/* Desktop: popover camera nổi đè form — quét xong tự điền, form vẫn còn (CHANGES #30). */}
      {quetPopover && isDesktop && (
        <QuetPopover onQuet={batDau} onDong={() => setQuetPopover(false)} loi={loiQuet} setLoi={setLoiQuet} />
      )}

      {/* Toast gửi nhanh (CHANGES #13) — luồng "Lưu & nhập hồ sơ tiếp" */}
      {toast && (
        <div className="fixed left-1/2 -translate-x-1/2 bottom-20 lg:bottom-6 z-50 pointer-events-none">
          <div
            className={
              "flex items-center gap-2 px-4 py-2.5 rounded-full shadow-lg text-sm font-semibold text-white " +
              (toast.ok ? "bg-success" : "bg-warning")
            }
          >
            <Icon name={toast.ok ? "check" : "wifiOff"} className="w-4 h-4" sw={toast.ok ? 3 : 2} /> {toast.msg}
          </div>
        </div>
      )}

      {/* THU-06: spinner lúc OCR đọc thẻ (có thể vài giây, lần đầu còn tải bộ đọc) + Hủy */}
      {dangOcr && (
        <div className="fixed inset-0 z-50 bg-background/85 backdrop-blur-sm flex flex-col items-center justify-center gap-3 p-6 text-center">
          <Icon name="refresh" className="w-8 h-8 text-primary animate-spin" />
          <p className="text-[15px] font-semibold">Đang đọc chữ trên thẻ…</p>
          <p className="text-[12px] text-muted-foreground max-w-xs">Lần đầu có thể mất vài giây để tải bộ đọc. Ảnh thẻ chỉ xử lý trên máy bạn, không gửi đi.</p>
          <button
            type="button"
            onClick={huyOcr}
            className="mt-2 h-10 px-4 rounded-lg border border-border bg-card text-foreground text-[13px] font-medium hover:bg-muted transition-colors"
          >
            Hủy → Nhập tay
          </button>
        </div>
      )}
    </div>
  );
}

// ---------- Màn vào: chọn cách nhập (không tự mở camera) ----------
function ChonCach({
  onQuet,
  onNhapTay,
  onAnhFile,
  onOcrFile,
  loi,
}: {
  onQuet: () => void;
  onNhapTay: () => void;
  onAnhFile: (f: File) => void | Promise<void>;
  onOcrFile: (f: File) => void | Promise<void>;
  loi: string | null;
}) {
  return (
    <div className="flex-1 min-h-0 flex flex-col p-4">
      <div className="text-center mt-3">
        <h2 className="text-lg font-bold">Thu nhận hồ sơ học viên</h2>
        <p className="text-[13px] text-muted-foreground mt-1">Chọn cách nhập hồ sơ căn cước</p>
      </div>

      {loi && (
        <div className="mt-4 flex items-start gap-2 text-[12px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2">
          <Icon name="warn" className="w-4 h-4 shrink-0 mt-0.5" /> {loi}
        </div>
      )}

      <div className="flex-1" />

      <div className="space-y-2.5 lg:max-w-md lg:mx-auto lg:w-full">
        <button
          type="button"
          onClick={onQuet}
          className="w-full h-14 rounded-xl bg-primary text-primary-foreground font-bold text-[15px] flex items-center justify-center gap-2.5 hover:brightness-110 transition shadow-sm"
        >
          <Icon name="scan" className="w-5 h-5" /> Quét QR CCCD
        </button>
        {/* THU-06: lối dự phòng khi QR không quét được (iPhone yếu) — chụp mặt trước, OCR tự đọc */}
        <label className="w-full h-14 rounded-xl border border-border bg-card text-foreground font-semibold text-[15px] flex items-center justify-center gap-2.5 hover:bg-muted transition-colors cursor-pointer">
          <Icon name="image" className="w-5 h-5" /> Chụp ảnh thẻ (tự đọc)
          <input
            type="file"
            accept="image/*"
            capture="environment"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              e.target.value = "";
              if (f) void onOcrFile(f);
            }}
          />
        </label>
        <button
          type="button"
          onClick={onNhapTay}
          className="w-full h-14 rounded-xl border border-border bg-card text-foreground font-semibold text-[15px] flex items-center justify-center gap-2.5 hover:bg-muted transition-colors"
        >
          <Icon name="edit" className="w-5 h-5" /> Nhập tay
        </button>
        <label className="w-full py-2 text-[13px] text-primary font-medium flex items-center justify-center gap-1.5 cursor-pointer hover:underline">
          <Icon name="image" className="w-4 h-4" /> Tải ảnh CCCD (đọc QR từ ảnh)
          <input
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              e.target.value = "";
              if (f) void onAnhFile(f);
            }}
          />
        </label>
      </div>

      <div className="flex-1" />
    </div>
  );
}

// ---------- Khung quét (camera + auto-capture + hiệu ứng + tải ảnh) ----------
function KhungQuet({
  onQuet,
  onNhapTay,
  onQuayLai,
  loi,
  setLoi,
  inPopover = false,
}: {
  onQuet: (f: CccdFields) => void;
  onNhapTay: () => void;
  onQuayLai: () => void;
  loi: string | null;
  setLoi: (s: string | null) => void;
  inPopover?: boolean; // dùng trong popover desktop: ẩn header riêng, đổi link đáy (CHANGES #30)
}) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const camRef = useRef<HTMLDivElement | null>(null); // khung hiển thị camera — để quy đổi vị trí QR
  const streamRef = useRef<MediaStream | null>(null);
  const loopRef = useRef<number | null>(null);
  const detectorRef = useRef<{ cur: BarcodeDetectorLike | null }>({ cur: null });
  const qrScannerRef = useRef<import("qr-scanner").default | null>(null); // nhánh iPhone (BUG-14)
  const daBatRef = useRef(false); // đã bắt được QR hợp lệ → dừng hẳn, không bắt lần 2
  const dangTickRef = useRef(false); // đang xử lý 1 frame → chặn tick chồng
  const stableRef = useRef<{ raw: string | null; dem: number }>({ raw: null, dem: 0 });

  const [loiCamera, setLoiCamera] = useState<string | null>(null);
  const [coTorch, setCoTorch] = useState(false);
  const [torchBat, setTorchBat] = useState(false);
  const [thanhCong, setThanhCong] = useState(false);
  const [box, setBox] = useState<Box | null>(null); // khung bám theo QR (px trong khung camera)

  const dungCamera = useCallback(() => {
    if (loopRef.current !== null) {
      window.clearInterval(loopRef.current);
      loopRef.current = null;
    }
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    const qs = qrScannerRef.current;
    if (qs) {
      try { qs.stop(); qs.destroy(); } catch { /* đã dừng */ }
      qrScannerRef.current = null;
    }
  }, []);

  const batDuoc = useCallback(
    (f: CccdFields) => {
      daBatRef.current = true;
      dungCamera();
      setThanhCong(true);
      if (typeof navigator !== "undefined" && navigator.vibrate) navigator.vibrate(60);
      window.setTimeout(() => onQuet(f), 450);
    },
    [dungCamera, onQuet],
  );

  useEffect(() => {
    let huy = false;
    // iOS Safari KHÔNG có BarcodeDetector → nhánh QrScanner; máy có thì giữ vòng quét gốc (khung bám). BUG-14
    const coBarcodeDetector =
      typeof (globalThis as { BarcodeDetector?: BarcodeDetectorCtor }).BarcodeDetector === "function";

    // raw QR → đếm ổn định ~2 frame → parse → nhận. Dùng chung cả 2 nhánh.
    function nhanRaw(raw: string) {
      const st = stableRef.current;
      if (raw === st.raw) st.dem += 1;
      else {
        st.raw = raw;
        st.dem = 1;
      }
      if (st.dem < 2) return; // chờ ổn định ~2 frame mới nhận
      const r = parseCccdQr(raw);
      if (!r.ok) {
        // QR đọc được nhưng không đúng chuẩn CCCD → báo, tiếp tục quét.
        stableRef.current = { raw: null, dem: 0 };
        setLoi(r.message);
        return;
      }
      batDuoc(r.data);
    }

    async function tick() {
      if (daBatRef.current || dangTickRef.current) return;
      const v = videoRef.current;
      const c = canvasRef.current;
      if (!v || !c || v.readyState < 2) return;
      dangTickRef.current = true;
      try {
        c.width = v.videoWidth;
        c.height = v.videoHeight;
        const ctx = c.getContext("2d");
        if (!ctx) return;
        ctx.drawImage(v, 0, 0, c.width, c.height);
        const d = await decodeTuCanvas(c, detectorRef.current);
        if (!d) {
          stableRef.current = { raw: null, dem: 0 };
          setBox(null);
          return;
        }
        // Khung bám: quy đổi vị trí QR (px canvas) → px khung hiển thị (video object-cover).
        const cont = camRef.current;
        if (cont && d.box) {
          const cw = cont.clientWidth, ch = cont.clientHeight, vw = c.width, vh = c.height;
          const scale = Math.max(cw / vw, ch / vh);
          const ox = (cw - vw * scale) / 2, oy = (ch - vh * scale) / 2;
          setBox({ x: d.box.x * scale + ox, y: d.box.y * scale + oy, w: d.box.w * scale, h: d.box.h * scale });
        } else {
          setBox(null);
        }
        nhanRaw(d.raw);
      } finally {
        dangTickRef.current = false;
      }
    }

    // Nhánh 1 — máy có BarcodeDetector (Android/Chrome): tự quản camera + vòng quét, giữ khung bám QR.
    async function batCameraNative() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: "environment" }, width: { ideal: 1920 }, height: { ideal: 1080 } },
          audio: false,
        });
        if (huy) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        const v = videoRef.current;
        if (v) {
          v.srcObject = stream;
          await v.play().catch(() => undefined);
        }
        const track = stream.getVideoTracks()[0];
        const caps = (track.getCapabilities?.() ?? {}) as { focusMode?: string[]; zoom?: { max?: number }; torch?: boolean };
        const adv: MediaTrackConstraintSet[] = [];
        if (caps.focusMode?.includes("continuous")) adv.push({ focusMode: "continuous" } as MediaTrackConstraintSet);
        if (caps.zoom?.max && caps.zoom.max >= 2) adv.push({ zoom: 2 } as unknown as MediaTrackConstraintSet);
        if (adv.length) await track.applyConstraints({ advanced: adv }).catch(() => undefined);
        setCoTorch(!!caps.torch);
        daBatRef.current = false;
        dangTickRef.current = false;
        stableRef.current = { raw: null, dem: 0 };
        loopRef.current = window.setInterval(() => void tick(), 250);
      } catch (e) {
        if (!huy) setLoiCamera(giaiThichLoiCamera(e));
      }
    }

    // Nhánh 2 — iPhone/iOS Safari (không có BarcodeDetector): bộ quét camera của thư viện qr-scanner
    // (worker + dò lặp), ÉP quét TOÀN khung (tinhVungQuet) để bắt QR CCCD nằm lệch góc. BUG-14
    async function batCameraQrScanner() {
      try {
        const QrScanner = (await import("qr-scanner")).default;
        const v = videoRef.current;
        if (!v || huy) return;
        daBatRef.current = false;
        stableRef.current = { raw: null, dem: 0 };
        const qs = new QrScanner(
          v,
          (res) => {
            if (!daBatRef.current) nhanRaw(res.data);
          },
          {
            preferredCamera: "environment",
            returnDetailedScanResult: true,
            maxScansPerSecond: 5,
            highlightScanRegion: false,
            highlightCodeOutline: false,
            calculateScanRegion: (vid) => tinhVungQuet(vid.videoWidth, vid.videoHeight),
          },
        );
        qrScannerRef.current = qs;
        await qs.start();
        if (huy) {
          dungCamera();
          return;
        }
        const coFlash = await qs.hasFlash().catch(() => false);
        setCoTorch(coFlash);
      } catch (e) {
        if (!huy) setLoiCamera(giaiThichLoiCamera(e));
      }
    }

    if (coBarcodeDetector) void batCameraNative();
    else void batCameraQrScanner();
    return () => {
      huy = true;
      dungCamera();
    };
  }, [batDuoc, dungCamera, setLoi]);

  async function toggleTorch() {
    const moi = !torchBat;
    const qs = qrScannerRef.current;
    if (qs) {
      // nhánh iPhone: đèn do QrScanner quản (BUG-14)
      try {
        if (moi) await qs.turnFlashOn();
        else await qs.turnFlashOff();
        setTorchBat(moi);
      } catch {
        // thiết bị không bật được đèn — bỏ qua
      }
      return;
    }
    const track = streamRef.current?.getVideoTracks()[0];
    if (!track) return;
    try {
      await track.applyConstraints({ advanced: [{ torch: moi } as unknown as MediaTrackConstraintSet] });
      setTorchBat(moi);
    } catch {
      // thiết bị không bật được đèn — bỏ qua
    }
  }

  function chonAnh(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setLoi(null);
    void (async () => {
      const raw = await decodeTuFile(file);
      if (!raw) {
        setLoi("Không đọc được mã QR trong ảnh. Thử ảnh rõ nét hơn hoặc nhập tay.");
        return;
      }
      const r = parseCccdQr(raw);
      if (!r.ok) {
        setLoi(r.message);
        return;
      }
      dungCamera();
      onQuet(r.data);
    })();
  }

  return (
    <div className="flex-1 min-h-0 flex flex-col p-4 gap-3">
      {/* Header riêng: chỉ mobile. Trong popover desktop đã có tiêu đề + nút đóng. */}
      {!inPopover && (
        <div className="flex items-center gap-2 shrink-0">
          <button type="button" onClick={onQuayLai} aria-label="Quay lại" className="w-9 h-9 -ml-1 rounded-lg flex items-center justify-center text-muted-foreground hover:bg-muted transition-colors">
            <Icon name="chevronLeft" className="w-5 h-5" />
          </button>
          <div>
            <h2 className="text-base font-bold leading-tight">Quét căn cước</h2>
            <p className="text-[11px] text-muted-foreground leading-tight">Đưa mặt trước CCCD vào khung — tự nhận</p>
          </div>
        </div>
      )}

      <div ref={camRef} className="relative flex-1 min-h-0 bg-slate-950 rounded-xl overflow-hidden flex items-center justify-center">
        {loiCamera ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 p-6 text-center">
            <Icon name="warn" className="w-8 h-8 text-warning" />
            <p className="text-[13px] text-white/90 leading-relaxed">{loiCamera}</p>
          </div>
        ) : (
          <>
            <video ref={videoRef} className="absolute inset-0 w-full h-full object-cover" muted playsInline />
            {/* khung ngắm góc xanh (hướng dẫn) */}
            <div className="relative w-[64%] aspect-square pointer-events-none">
              <span className="absolute -top-0.5 -left-0.5 w-8 h-8 border-t-4 border-l-4 border-white/70 rounded-tl-lg" />
              <span className="absolute -top-0.5 -right-0.5 w-8 h-8 border-t-4 border-r-4 border-white/70 rounded-tr-lg" />
              <span className="absolute -bottom-0.5 -left-0.5 w-8 h-8 border-b-4 border-l-4 border-white/70 rounded-bl-lg" />
              <span className="absolute -bottom-0.5 -right-0.5 w-8 h-8 border-b-4 border-r-4 border-white/70 rounded-br-lg" />
              {!thanhCong && !box && (
                <div className="absolute left-2 right-2 h-0.5 bg-white/80 shadow-[0_0_12px_2px] shadow-white/50 animate-pulse" style={{ top: "60%" }} />
              )}
            </div>
            {/* khung BÁM theo QR khi phát hiện (CHANGES #12) */}
            {box && !thanhCong && (
              <div
                className="absolute pointer-events-none border-[3px] border-amber-400 rounded-md transition duration-100"
                style={{ left: box.x, top: box.y, width: box.w, height: box.h, boxShadow: "0 0 0 3px rgba(251,191,36,.28)" }}
              >
                <span className="absolute -top-1 -left-1 w-3.5 h-3.5 border-t-[3px] border-l-[3px] border-amber-400" />
                <span className="absolute -top-1 -right-1 w-3.5 h-3.5 border-t-[3px] border-r-[3px] border-amber-400" />
                <span className="absolute -bottom-1 -left-1 w-3.5 h-3.5 border-b-[3px] border-l-[3px] border-amber-400" />
                <span className="absolute -bottom-1 -right-1 w-3.5 h-3.5 border-b-[3px] border-r-[3px] border-amber-400" />
              </div>
            )}
            {coTorch && (
              <button
                type="button"
                aria-label="Bật đèn"
                onClick={toggleTorch}
                className={`absolute bottom-3 right-3 w-10 h-10 rounded-full backdrop-blur flex items-center justify-center text-white transition-colors ${torchBat ? "bg-warning" : "bg-white/15 hover:bg-white/25"}`}
              >
                <Icon name="torch" className="w-5 h-5" />
              </button>
            )}
            {/* hiệu ứng quét thành công */}
            {thanhCong && (
              <>
                <div className="absolute inset-0 bg-success/40 animate-pulse" />
                <div className="absolute top-3 left-1/2 -translate-x-1/2 flex items-center gap-1.5 bg-success text-white text-xs font-semibold px-3 py-1.5 rounded-full shadow-lg">
                  <Icon name="check" className="w-4 h-4" sw={3} /> Quét thành công
                </div>
              </>
            )}
          </>
        )}
      </div>
      <canvas ref={canvasRef} className="hidden" />

      {loi && (
        <div className="shrink-0 flex items-start gap-2 text-[12px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2">
          <Icon name="warn" className="w-4 h-4 shrink-0 mt-0.5" /> {loi}
        </div>
      )}

      <div className="shrink-0 space-y-2">
        <label className="w-full h-11 rounded-lg border border-border bg-secondary text-foreground font-semibold text-sm flex items-center justify-center gap-2 hover:bg-muted transition-colors cursor-pointer">
          <Icon name="image" className="w-4 h-4" /> Tải ảnh CCCD (đọc QR từ ảnh)
          <input type="file" accept="image/*" className="hidden" onChange={chonAnh} />
        </label>
        <button
          type="button"
          onClick={onNhapTay}
          className="w-full text-[13px] text-primary font-medium hover:underline text-center py-1"
        >
          {inPopover ? "QR mờ? Đóng để nhập tay" : "QR mờ, không quét được? Nhập tay"}
        </button>
      </div>
    </div>
  );
}

// ---------- Popover quét (desktop) — camera nổi đè form, quét xong tự điền (CHANGES #30) ----------
function QuetPopover({
  onQuet,
  onDong,
  loi,
  setLoi,
}: {
  onQuet: (f: CccdFields) => void;
  onDong: () => void;
  loi: string | null;
  setLoi: (s: string | null) => void;
}) {
  return (
    <div
      className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4"
      onClick={(e) => { if (e.target === e.currentTarget) onDong(); }}
    >
      <div className="bg-card w-full max-w-md h-[560px] max-h-[90vh] rounded-xl shadow-2xl flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-border shrink-0">
          <div>
            <h3 className="font-bold text-sm leading-tight">Quét QR căn cước</h3>
            <p className="text-[11px] text-muted-foreground leading-tight">Đưa mặt trước CCCD vào khung — tự điền vào form</p>
          </div>
          <button onClick={onDong} aria-label="Đóng" className="w-8 h-8 rounded-lg hover:bg-muted flex items-center justify-center transition-colors shrink-0">
            <Icon name="x" className="w-5 h-5" />
          </button>
        </div>
        <KhungQuet onQuet={onQuet} onNhapTay={onDong} onQuayLai={onDong} loi={loi} setLoi={setLoi} inPopover />
      </div>
    </div>
  );
}

// ---------- Preview 7 trường cho sửa + giữ ----------
function kiemFields(f: CccdFields): string | null {
  if (!/^\d{12}$/.test(f.soCccd.trim())) return "Số CCCD phải có đúng 12 chữ số.";
  // CMND cũ không hiện ô nhập (CHANGES #14) — giá trị lấy từ QR, không chặn định dạng ở đây.
  if (!f.hoTen.trim()) return "Chưa có họ và tên.";
  const ns = f.ngaySinh.trim();
  if (!/^\d{4}$/.test(ns) && !/^\d{2}\/\d{2}\/\d{4}$/.test(ns)) return "Ngày sinh phải là dd/mm/yyyy (hoặc chỉ năm yyyy).";
  if (!f.noiThuongTru.trim()) return "Chưa có nơi thường trú.";
  if (f.ngayCap.trim() && !/^\d{2}\/\d{2}\/\d{4}$/.test(f.ngayCap.trim())) return "Ngày cấp phải là dd/mm/yyyy (hoặc bỏ trống).";
  return null;
}

// ISO → "dd/mm HH:mm" (giờ máy) cho banner cảnh báo trùng.
function lucHienThi(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const p = (n: number) => String(n).padStart(2, "0");
  return `${p(d.getDate())}/${p(d.getMonth() + 1)} ${p(d.getHours())}:${p(d.getMinutes())}`;
}

function Preview({
  fields,
  isDesktop = false,
  canhBaoOcr,
  onMoQuet,
  onAnhFile,
  onOcrFile,
  onLuu,
  onLuuVaTiep,
  onQuetLai,
}: {
  fields: CccdFields;
  isDesktop?: boolean;
  canhBaoOcr?: string[] | null; // THU-06: trường điền từ OCR cần soát (gồm ngày cấp nhập tay)
  onMoQuet?: () => void; // desktop: mở popover quét
  onAnhFile?: (f: File) => void; // desktop: tải ảnh CCCD đọc QR
  onOcrFile?: (f: File) => void; // desktop: chụp/tải ảnh thẻ → OCR (THU-06)
  onLuu: (uuid: string) => void;
  onLuuVaTiep: (uuid: string) => void;
  onQuetLai: () => void;
}) {
  const [f, setF] = useState<CccdFields>(fields);
  const [loi, setLoi] = useState<string | null>(null);
  const [trung, setTrung] = useState<KiemTrungKq | null>(null); // THU-04 cảnh báo mềm
  const [dangGui, setDangGui] = useState(false);
  const guiRef = useRef(false); // chặn double-tap "Lưu & nhập hồ sơ tiếp"

  const set = <K extends keyof CccdFields>(k: K, v: CccdFields[K]) => setF((p) => ({ ...p, [k]: v }));
  const canhBaoTen = kiemDoDaiTen(f.hoTen);

  // THU-04 (CHANGES #13): CCCD đủ 12 số → soi hàng đợi, trùng thì cảnh báo mềm (không chặn).
  useEffect(() => {
    const cccd = f.soCccd.trim();
    if (!/^\d{12}$/.test(cccd)) {
      setTrung(null);
      return;
    }
    const ac = new AbortController();
    kiemTrungCccd(cccd, undefined, ac.signal)
      .then((r) => setTrung(r.trung ? r : null))
      .catch(() => {}); // lỗi mạng / abort khi đổi CCCD → bỏ qua, không chặn
    return () => ac.abort();
  }, [f.soCccd]);

  function giu() {
    const e = kiemFields(f);
    if (e) {
      setLoi(e);
      return;
    }
    const id = taoUuid();
    luuNhap(tuCccd(id, f));
    onLuu(id);
  }

  function giuVaTiep() {
    if (guiRef.current) return; // chặn double-tap → không tạo 2 bản ghi cùng CCCD
    const e = kiemFields(f);
    if (e) {
      setLoi(e);
      return;
    }
    guiRef.current = true;
    setDangGui(true);
    const id = taoUuid();
    luuNhap(tuCccd(id, f));
    onLuuVaTiep(id);
  }

  return (
    <form
      className="space-y-3"
      onSubmit={(e) => {
        e.preventDefault();
        giu();
      }}
      onKeyDown={(e) => {
        // Ctrl/Cmd + Enter = lưu nhanh & nhập hồ sơ tiếp (phím tắt nhập liệu hàng loạt).
        if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
          e.preventDefault();
          giuVaTiep();
        }
      }}
    >
      {isDesktop ? (
        <>
          {/* Desktop: form nhập tay là chủ đạo; Quét QR/Tải ảnh là nút phụ góc phải (CHANGES #30) */}
          <div className="flex items-start justify-between gap-3">
            <div>
              <h2 className="text-base font-bold">Thu nhận hồ sơ học viên</h2>
              <p className="text-[12px] text-muted-foreground mt-0.5">Nhập thông tin căn cước, hoặc quét QR để điền nhanh</p>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <button
                type="button"
                onClick={onMoQuet}
                className="h-9 px-3 rounded-lg border border-border bg-card text-foreground text-[13px] font-medium flex items-center gap-1.5 hover:bg-muted transition-colors"
              >
                <Icon name="scan" className="w-4 h-4" /> Quét QR
              </button>
              <label className="h-9 px-3 rounded-lg border border-border bg-card text-foreground text-[13px] font-medium flex items-center gap-1.5 hover:bg-muted transition-colors cursor-pointer">
                <Icon name="image" className="w-4 h-4" /> Tải ảnh
                <input
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    e.target.value = "";
                    if (f && onAnhFile) onAnhFile(f);
                  }}
                />
              </label>
              {/* THU-06: đọc chữ trên ảnh thẻ (dự phòng khi QR không đọc được) */}
              <label className="h-9 px-3 rounded-lg border border-border bg-card text-foreground text-[13px] font-medium flex items-center gap-1.5 hover:bg-muted transition-colors cursor-pointer">
                <Icon name="scan" className="w-4 h-4" /> Đọc thẻ (OCR)
                <input
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    e.target.value = "";
                    if (f && onOcrFile) onOcrFile(f);
                  }}
                />
              </label>
            </div>
          </div>
        </>
      ) : (
        <>
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold">Thông tin từ căn cước</h2>
            <button type="button" onClick={onQuetLai} className="text-[12px] text-primary font-medium hover:underline flex items-center gap-1">
              <Icon name="refresh" className="w-3.5 h-3.5" /> Quét lại
            </button>
          </div>
          <p className="text-[12px] text-muted-foreground -mt-1">Kiểm tra và sửa nếu sai trước khi giữ</p>
        </>
      )}

      {/* THU-06: điền từ OCR — nhắc nhân viên soát các trường chưa chắc + nhập ngày cấp */}
      {canhBaoOcr && canhBaoOcr.length > 0 && (
        <div className="flex items-start gap-2 text-[12px] text-warning bg-warning/10 border border-warning/30 rounded-lg px-3 py-2">
          <Icon name="warn" className="w-4 h-4 shrink-0 mt-0.5" />
          <span>
            Đã điền từ ảnh thẻ bằng OCR — có thể đọc sai. Kiểm/nhập lại: <strong>{canhBaoOcr.join(", ")}</strong>.
          </span>
        </div>
      )}

      {/* Desktop: 2 cột cho thấy hết trường, đỡ cuộn khi nhập tay (CHANGES #14) */}
      <div className="grid gap-3 lg:grid-cols-2">
        <Field label="Số CCCD" req value={f.soCccd} onChange={(v) => set("soCccd", v)} inputMode="numeric" autoFocus />
        <Field label="Họ và tên" req value={f.hoTen} onChange={(v) => set("hoTen", v)} />
        <ODate label="Ngày sinh" req value={f.ngaySinh} onChange={(v) => set("ngaySinh", v)} />
        <div>
          <label className="field-label">
            Giới tính <span className="text-destructive">*</span>
          </label>
          <select className="field-input mt-1" value={f.gioiTinh} onChange={(e) => set("gioiTinh", e.target.value as GioiTinh)}>
            <option value="Nam">Nam</option>
            <option value="Nữ">Nữ</option>
          </select>
        </div>
        <div className="lg:col-span-2">
          <Field label="Nơi thường trú" req value={f.noiThuongTru} onChange={(v) => set("noiThuongTru", v)} />
        </div>
        <ODate label="Ngày cấp" value={f.ngayCap} onChange={(v) => set("ngayCap", v)} />
      </div>

      {canhBaoTen.length > 0 && (
        <div className="flex items-start gap-2 text-[12px] text-warning bg-warning/10 border border-warning/30 rounded-lg px-3 py-2">
          <Icon name="warn" className="w-4 h-4 shrink-0 mt-0.5" />
          <span>
            Tên dài hơn giới hạn cột lưu trữ, cần rút gọn trước khi nạp:{" "}
            {canhBaoTen.map((c) => `${c.ten} ${c.dai}/${c.max}`).join(" · ")}
          </span>
        </div>
      )}

      {trung && (
        <div className="flex items-start gap-2 text-[12px] text-warning bg-warning/10 border border-warning/30 rounded-lg px-3 py-2">
          <Icon name="warn" className="w-4 h-4 shrink-0 mt-0.5" />
          <span>
            Căn cước này đã có hồ sơ <strong>chưa nạp</strong> trong hàng đợi
            {trung.nguoi_gui ? ` — ${trung.nguoi_gui}` : ""}
            {trung.luc ? ` gửi lúc ${lucHienThi(trung.luc)}` : ""}. Vẫn gửi được nếu là bổ sung/sửa.
          </span>
        </div>
      )}

      {loi && (
        <div className="flex items-start gap-2 text-[12px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2">
          <Icon name="warn" className="w-4 h-4 shrink-0 mt-0.5" /> {loi}
        </div>
      )}

      {/* Desktop: 2 nút tách hai bên (primary phải, phụ trái) tránh bấm nhầm; mobile xếp dọc (CHANGES #14) */}
      <div className="pt-1">
        <div className="flex flex-col gap-2.5 lg:flex-row-reverse lg:items-center lg:justify-between lg:gap-4">
          <button
            type="submit"
            disabled={dangGui}
            className="w-full lg:w-auto px-5 h-11 rounded-lg bg-primary text-primary-foreground font-semibold text-sm flex items-center justify-center gap-2 whitespace-nowrap hover:brightness-110 transition shadow-sm disabled:opacity-60"
          >
            <Icon name="camera" className="w-4 h-4" /> Tiếp tục — chụp ảnh chân dung
          </button>
          <button
            type="button"
            onClick={giuVaTiep}
            disabled={dangGui}
            className="w-full lg:w-auto px-5 h-11 rounded-lg border border-border bg-card text-foreground font-semibold text-sm flex items-center justify-center gap-2 whitespace-nowrap hover:bg-muted transition-colors disabled:opacity-60"
          >
            <Icon name="send" className="w-4 h-4" /> Lưu & nhập hồ sơ tiếp
          </button>
        </div>
        <p className="text-[12px] text-muted-foreground text-center mt-2 lg:text-right">
          Gửi ngay không kèm ảnh — bổ sung ảnh sau ở "Hồ sơ đã gửi".
          <span className="hidden lg:inline"> · Enter: chụp ảnh · Ctrl+Enter: lưu &amp; nhập tiếp</span>
        </p>
      </div>
    </form>
  );
}

function Field({
  label,
  req,
  value,
  onChange,
  placeholder,
  inputMode,
  autoFocus,
}: {
  label: string;
  req?: boolean;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  inputMode?: "text" | "numeric";
  autoFocus?: boolean;
}) {
  return (
    <div>
      <label className="field-label">
        {label} {req && <span className="text-destructive">*</span>}
      </label>
      <input
        className="field-input mt-1"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        inputMode={inputMode}
        autoFocus={autoFocus}
      />
    </div>
  );
}

// ---------- Chụp ảnh chân dung + gửi VPS ----------
// Nén ảnh về JPEG (cạnh dài ≤ maxCanh) để nhẹ khi giữ nháp offline + upload. Ảnh thô để tool
// xử lý (căn 3:4 + xóa phông + .jp2 ở NAP-04), app KHÔNG cắt/xóa phông.
function nenAnhJpeg(file: File, maxCanh: number, chatLuong: number): Promise<string> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      URL.revokeObjectURL(url);
      let w = img.naturalWidth;
      let h = img.naturalHeight;
      const canh = Math.max(w, h);
      if (canh > maxCanh) {
        const r = maxCanh / canh;
        w = Math.round(w * r);
        h = Math.round(h * r);
      }
      const c = document.createElement("canvas");
      c.width = w;
      c.height = h;
      const ctx = c.getContext("2d");
      if (!ctx) {
        reject(new Error("Không dựng được canvas"));
        return;
      }
      ctx.drawImage(img, 0, 0, w, h);
      resolve(c.toDataURL("image/jpeg", chatLuong));
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("Không đọc được ảnh"));
    };
    img.src = url;
  });
}

function ChupAnhGui({ uuid, onXong }: { uuid: string; onXong: (mangYeu: boolean) => void }) {
  const [anh, setAnh] = useState<string | null>(null);
  const [dangGui, setDangGui] = useState(false);
  const [loi, setLoi] = useState<string | null>(null);

  function chonAnh(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setLoi(null);
    void nenAnhJpeg(file, 1600, 0.85)
      .then(setAnh)
      .catch(() => setLoi("Không đọc được ảnh. Thử ảnh khác."));
  }

  async function gui() {
    setDangGui(true);
    setLoi(null);
    if (anh) capNhatNhap(uuid, { anh_data_url: anh });
    const hs = dsNhap().find((x) => x.uuid === uuid);
    if (!hs) {
      setLoi("Không tìm thấy nháp hồ sơ. Hãy quét lại.");
      setDangGui(false);
      return;
    }
    try {
      await guiMot(hs);
      onXong(false);
    } catch (err) {
      // ApiError = server từ chối (4xx) → báo để sửa. Lỗi khác = mất mạng → đã giữ nháp, tự gửi lại.
      if (err instanceof ApiError) {
        setLoi(err.message);
        setDangGui(false);
      } else {
        onXong(true);
      }
    }
  }

  return (
    <div className="space-y-4 lg:max-w-md lg:mx-auto">
      <div className="text-center">
        <h2 className="text-base font-bold">Ảnh chân dung</h2>
        <p className="text-[12px] text-muted-foreground mt-0.5">Chụp ảnh người thật. Căn khung và xóa phông do tool nạp làm sau.</p>
      </div>

      <div className="relative bg-slate-100 border border-border rounded-xl aspect-[3/4] max-w-[260px] mx-auto overflow-hidden flex items-center justify-center">
        {anh ? (
          <img src={anh} alt="Ảnh chân dung" className="absolute inset-0 w-full h-full object-cover" />
        ) : (
          <div className="flex flex-col items-center gap-2 text-slate-400">
            <Icon name="user" className="w-14 h-14" sw={1.5} />
            <span className="text-[12px]">Chưa có ảnh</span>
          </div>
        )}
      </div>

      {loi && (
        <div className="flex items-start gap-2 text-[12px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2">
          <Icon name="warn" className="w-4 h-4 shrink-0 mt-0.5" /> {loi}
        </div>
      )}

      <div className="space-y-2">
        <div className="grid grid-cols-2 gap-2">
          {/* Chụp trực tiếp (camera) vs chọn ảnh có sẵn trong máy — 2 lối riêng (CHANGES #15) */}
          <label className="h-11 rounded-lg border border-border bg-secondary text-foreground font-semibold text-sm flex items-center justify-center gap-2 hover:bg-muted transition-colors cursor-pointer">
            <Icon name="camera" className="w-4 h-4" /> {anh ? "Chụp lại" : "Chụp ảnh"}
            <input type="file" accept="image/*" capture="user" className="hidden" onChange={chonAnh} disabled={dangGui} />
          </label>
          <label className="h-11 rounded-lg border border-border bg-secondary text-foreground font-semibold text-sm flex items-center justify-center gap-2 hover:bg-muted transition-colors cursor-pointer">
            <Icon name="image" className="w-4 h-4" /> Chọn từ máy
            <input type="file" accept="image/*" className="hidden" onChange={chonAnh} disabled={dangGui} />
          </label>
        </div>

        <button
          type="button"
          onClick={gui}
          disabled={dangGui}
          className="w-full h-11 rounded-lg bg-primary text-primary-foreground font-semibold text-sm flex items-center justify-center gap-2 hover:brightness-110 transition shadow-sm disabled:opacity-60"
        >
          <Icon name="send" className="w-4 h-4" /> {dangGui ? "Đang gửi…" : anh ? "Gửi hồ sơ" : "Gửi không kèm ảnh"}
        </button>
        {!anh && <p className="text-[11px] text-muted-foreground text-center">Có thể gửi trước, bổ sung ảnh sau ở máy nạp.</p>}
      </div>
    </div>
  );
}

// ---------- Kết quả gửi ----------
function KetQua({ offline, onQuetTiep }: { offline: boolean; onQuetTiep: () => void }) {
  return (
    <div className="flex flex-col items-center text-center gap-4 py-10">
      <div className={`w-16 h-16 rounded-full flex items-center justify-center ${offline ? "bg-warning/15 text-warning" : "bg-success/15 text-success"}`}>
        <Icon name={offline ? "wifiOff" : "check"} className="w-8 h-8" sw={offline ? 2 : 3} />
      </div>
      <div>
        <h2 className="text-base font-bold">{offline ? "Đã lưu — chưa gửi được" : "Đã gửi hồ sơ"}</h2>
        <p className="text-[13px] text-muted-foreground mt-1 max-w-xs">
          {offline
            ? "Chưa có mạng. Hồ sơ đã lưu ở máy và sẽ tự gửi lại khi có mạng trở lại."
            : "Hồ sơ đã lên hệ thống, chờ nhân viên nạp xử lý."}
        </p>
      </div>
      <div className="flex flex-col items-center gap-2">
        <button
          type="button"
          onClick={onQuetTiep}
          className="h-11 px-6 rounded-lg bg-primary text-primary-foreground font-semibold text-sm flex items-center justify-center gap-2 hover:brightness-110 transition shadow-sm"
        >
          <Icon name="scan" className="w-4 h-4" /> Quét hồ sơ khác
        </button>
        <Link to="/da-gui" className="text-[13px] text-primary font-medium hover:underline">
          Xem hồ sơ đã gửi
        </Link>
      </div>
    </div>
  );
}
