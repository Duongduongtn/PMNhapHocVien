import { useCallback, useEffect, useRef, useState } from "react";
import { Icon } from "../components/Icon";
import { kiemDoDaiTen, parseCccdQr, type CccdFields, type GioiTinh } from "../lib/qr";
import { luuNhap, taoUuid, tuCccd } from "../lib/draft";

// THU-01 — Quét QR mặt trước CCCD gắn chip → preview 7 trường cho sửa → giữ nháp.
// Bám bố cục ui-demo/src/pages/app/Quet.tsx (khung ngắm góc xanh + hiệu ứng + form).
// Chụp ảnh chân dung + gửi VPS là THU-02 (đọc lại nháp qua lib/draft).
// Cách quét (BarcodeDetector→qr-scanner, auto-capture 2 frame) tham khảo webThanhdat — memory ref-quet-qr-cccd.

// ---- Decoder cascade: BarcodeDetector native → qr-scanner (ZXing) ----
interface DetectedBarcode {
  rawValue: string;
}
interface BarcodeDetectorLike {
  detect(src: CanvasImageSource): Promise<DetectedBarcode[]>;
}
type BarcodeDetectorCtor = new (opts: { formats: string[] }) => BarcodeDetectorLike;

async function decodeTuCanvas(canvas: HTMLCanvasElement, detector: { cur: BarcodeDetectorLike | null }): Promise<string | null> {
  const Ctor = (globalThis as { BarcodeDetector?: BarcodeDetectorCtor }).BarcodeDetector;
  if (Ctor) {
    try {
      if (!detector.cur) detector.cur = new Ctor({ formats: ["qr_code"] });
      const res = await detector.cur.detect(canvas);
      return res.length > 0 ? res[0].rawValue : null;
    } catch {
      // trình duyệt báo lỗi → rơi xuống qr-scanner
    }
  }
  try {
    const QrScanner = (await import("qr-scanner")).default;
    const r = await QrScanner.scanImage(canvas, { returnDetailedScanResult: true });
    return r.data;
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

type GiaiDoan = "quet" | "preview" | "xong";

export default function Quet() {
  const [giaiDoan, setGiaiDoan] = useState<GiaiDoan>("quet");
  const [fields, setFields] = useState<CccdFields>(FIELDS_RONG);
  const [loiQuet, setLoiQuet] = useState<string | null>(null);

  const batDau = useCallback((f: CccdFields) => {
    setFields(f);
    setLoiQuet(null);
    setGiaiDoan("preview");
  }, []);

  function nhapTay() {
    setFields(FIELDS_RONG);
    setLoiQuet(null);
    setGiaiDoan("preview");
  }

  function quetTiep() {
    setFields(FIELDS_RONG);
    setLoiQuet(null);
    setGiaiDoan("quet");
  }

  return (
    <div className="p-4 lg:p-6 lg:max-w-md lg:mx-auto">
      {giaiDoan === "quet" && <KhungQuet onQuet={batDau} onNhapTay={nhapTay} loi={loiQuet} setLoi={setLoiQuet} />}
      {giaiDoan === "preview" && (
        <Preview
          fields={fields}
          onLuu={() => setGiaiDoan("xong")}
          onQuetLai={quetTiep}
        />
      )}
      {giaiDoan === "xong" && <Xong onQuetTiep={quetTiep} />}
    </div>
  );
}

// ---------- Khung quét (camera + auto-capture + hiệu ứng + tải ảnh) ----------
function KhungQuet({
  onQuet,
  onNhapTay,
  loi,
  setLoi,
}: {
  onQuet: (f: CccdFields) => void;
  onNhapTay: () => void;
  loi: string | null;
  setLoi: (s: string | null) => void;
}) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const loopRef = useRef<number | null>(null);
  const detectorRef = useRef<{ cur: BarcodeDetectorLike | null }>({ cur: null });
  const daBatRef = useRef(false); // đã bắt được QR hợp lệ → dừng hẳn, không bắt lần 2
  const dangTickRef = useRef(false); // đang xử lý 1 frame → chặn tick chồng
  const stableRef = useRef<{ raw: string | null; dem: number }>({ raw: null, dem: 0 });

  const [loiCamera, setLoiCamera] = useState<string | null>(null);
  const [coTorch, setCoTorch] = useState(false);
  const [torchBat, setTorchBat] = useState(false);
  const [thanhCong, setThanhCong] = useState(false);

  const dungCamera = useCallback(() => {
    if (loopRef.current !== null) {
      window.clearInterval(loopRef.current);
      loopRef.current = null;
    }
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
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
        const raw = await decodeTuCanvas(c, detectorRef.current);
        if (!raw) {
          stableRef.current = { raw: null, dem: 0 };
          return;
        }
        const st = stableRef.current;
        if (raw === st.raw) st.dem += 1;
        else {
          st.raw = raw;
          st.dem = 1;
        }
        if (st.dem < 2) return; // chờ ổn định ~2 frame (~500ms) mới nhận
        const r = parseCccdQr(raw);
        if (!r.ok) {
          // QR đọc được nhưng không đúng chuẩn CCCD → báo, tiếp tục quét.
          stableRef.current = { raw: null, dem: 0 };
          setLoi(r.message);
          return;
        }
        batDuoc(r.data);
      } finally {
        dangTickRef.current = false;
      }
    }

    async function batCamera() {
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

    void batCamera();
    return () => {
      huy = true;
      dungCamera();
    };
  }, [batDuoc, dungCamera, setLoi]);

  async function toggleTorch() {
    const track = streamRef.current?.getVideoTracks()[0];
    if (!track) return;
    const moi = !torchBat;
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
    <div className="space-y-4">
      <div className="text-center">
        <h2 className="text-base font-bold">Quét căn cước</h2>
        <p className="text-[12px] text-muted-foreground mt-0.5">Đưa mặt trước CCCD gắn chip vào khung — tự nhận, không cần bấm</p>
      </div>

      <div className="relative bg-slate-950 aspect-[3/4] rounded-xl overflow-hidden flex items-center justify-center">
        {loiCamera ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 p-6 text-center">
            <Icon name="warn" className="w-8 h-8 text-warning" />
            <p className="text-[13px] text-white/90 leading-relaxed">{loiCamera}</p>
          </div>
        ) : (
          <>
            <video ref={videoRef} className="absolute inset-0 w-full h-full object-cover" muted playsInline />
            {/* khung ngắm góc xanh */}
            <div className="relative w-[70%] aspect-square pointer-events-none">
              <span className="absolute -top-0.5 -left-0.5 w-8 h-8 border-t-4 border-l-4 border-success rounded-tl-lg" />
              <span className="absolute -top-0.5 -right-0.5 w-8 h-8 border-t-4 border-r-4 border-success rounded-tr-lg" />
              <span className="absolute -bottom-0.5 -left-0.5 w-8 h-8 border-b-4 border-l-4 border-success rounded-bl-lg" />
              <span className="absolute -bottom-0.5 -right-0.5 w-8 h-8 border-b-4 border-r-4 border-success rounded-br-lg" />
              {!thanhCong && (
                <div className="absolute left-2 right-2 h-0.5 bg-success/80 shadow-[0_0_12px_2px] shadow-success animate-pulse" style={{ top: "60%" }} />
              )}
            </div>
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
            <div className="absolute bottom-3 left-3 text-[11px] text-white/70">Đưa mặt trước CCCD vào khung</div>
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
        <div className="flex items-start gap-2 text-[12px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2">
          <Icon name="warn" className="w-4 h-4 shrink-0 mt-0.5" /> {loi}
        </div>
      )}

      <div className="space-y-2">
        <label className="w-full h-11 rounded-lg border border-border bg-secondary text-foreground font-semibold text-sm flex items-center justify-center gap-2 hover:bg-muted transition-colors cursor-pointer">
          <Icon name="image" className="w-4 h-4" /> Tải ảnh CCCD (đọc QR từ ảnh)
          <input type="file" accept="image/*" className="hidden" onChange={chonAnh} />
        </label>
        <button
          type="button"
          onClick={onNhapTay}
          className="w-full text-[13px] text-primary font-medium hover:underline text-center py-1"
        >
          QR mờ, không quét được? Nhập tay
        </button>
      </div>
    </div>
  );
}

// ---------- Preview 7 trường cho sửa + giữ ----------
function kiemFields(f: CccdFields): string | null {
  if (!/^\d{12}$/.test(f.soCccd.trim())) return "Số CCCD phải có đúng 12 chữ số.";
  if (f.soCmndCu.trim() && !/^\d{9}$/.test(f.soCmndCu.trim())) return "Số CMND cũ phải có đúng 9 chữ số (hoặc bỏ trống).";
  if (!f.hoTen.trim()) return "Chưa có họ và tên.";
  const ns = f.ngaySinh.trim();
  if (!/^\d{4}$/.test(ns) && !/^\d{2}\/\d{2}\/\d{4}$/.test(ns)) return "Ngày sinh phải là dd/mm/yyyy (hoặc chỉ năm yyyy).";
  if (!f.noiThuongTru.trim()) return "Chưa có nơi thường trú.";
  if (f.ngayCap.trim() && !/^\d{2}\/\d{2}\/\d{4}$/.test(f.ngayCap.trim())) return "Ngày cấp phải là dd/mm/yyyy (hoặc bỏ trống).";
  return null;
}

function Preview({ fields, onLuu, onQuetLai }: { fields: CccdFields; onLuu: () => void; onQuetLai: () => void }) {
  const [f, setF] = useState<CccdFields>(fields);
  const [loi, setLoi] = useState<string | null>(null);

  const set = <K extends keyof CccdFields>(k: K, v: CccdFields[K]) => setF((p) => ({ ...p, [k]: v }));
  const canhBaoTen = kiemDoDaiTen(f.hoTen);

  function giu() {
    const e = kiemFields(f);
    if (e) {
      setLoi(e);
      return;
    }
    luuNhap(tuCccd(taoUuid(), f));
    onLuu();
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-bold">Thông tin từ căn cước</h2>
        <button type="button" onClick={onQuetLai} className="text-[12px] text-primary font-medium hover:underline flex items-center gap-1">
          <Icon name="refresh" className="w-3.5 h-3.5" /> Quét lại
        </button>
      </div>
      <p className="text-[12px] text-muted-foreground -mt-1">Kiểm tra và sửa nếu sai trước khi giữ</p>

      <Field label="Số CCCD" req value={f.soCccd} onChange={(v) => set("soCccd", v)} inputMode="numeric" />
      <Field label="Số CMND cũ (nếu có)" value={f.soCmndCu} onChange={(v) => set("soCmndCu", v)} placeholder="9 số — bỏ trống nếu không có" inputMode="numeric" />
      <Field label="Họ và tên" req value={f.hoTen} onChange={(v) => set("hoTen", v)} />
      <div className="grid grid-cols-2 gap-3">
        <Field label="Ngày sinh" req value={f.ngaySinh} onChange={(v) => set("ngaySinh", v)} placeholder="dd/mm/yyyy" />
        <div>
          <label className="field-label">
            Giới tính <span className="text-destructive">*</span>
          </label>
          <select className="field-input mt-1" value={f.gioiTinh} onChange={(e) => set("gioiTinh", e.target.value as GioiTinh)}>
            <option value="Nam">Nam</option>
            <option value="Nữ">Nữ</option>
          </select>
        </div>
      </div>
      <Field label="Nơi thường trú" req value={f.noiThuongTru} onChange={(v) => set("noiThuongTru", v)} />
      <Field label="Ngày cấp" value={f.ngayCap} onChange={(v) => set("ngayCap", v)} placeholder="dd/mm/yyyy" />

      {canhBaoTen.length > 0 && (
        <div className="flex items-start gap-2 text-[12px] text-warning bg-warning/10 border border-warning/30 rounded-lg px-3 py-2">
          <Icon name="warn" className="w-4 h-4 shrink-0 mt-0.5" />
          <span>
            Tên dài hơn giới hạn cột lưu trữ, cần rút gọn trước khi nạp:{" "}
            {canhBaoTen.map((c) => `${c.ten} ${c.dai}/${c.max}`).join(" · ")}
          </span>
        </div>
      )}

      {loi && (
        <div className="flex items-start gap-2 text-[12px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2">
          <Icon name="warn" className="w-4 h-4 shrink-0 mt-0.5" /> {loi}
        </div>
      )}

      <button
        type="button"
        onClick={giu}
        className="w-full h-11 rounded-lg bg-primary text-primary-foreground font-semibold text-sm flex items-center justify-center gap-2 hover:brightness-110 transition-all shadow-sm"
      >
        <Icon name="check" className="w-4 h-4" sw={3} /> Giữ thông tin
      </button>
    </div>
  );
}

function Field({
  label,
  req,
  value,
  onChange,
  placeholder,
  inputMode,
}: {
  label: string;
  req?: boolean;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  inputMode?: "text" | "numeric";
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
      />
    </div>
  );
}

// ---------- Đã giữ ----------
function Xong({ onQuetTiep }: { onQuetTiep: () => void }) {
  return (
    <div className="flex flex-col items-center text-center gap-4 py-10">
      <div className="w-16 h-16 rounded-full bg-success/15 text-success flex items-center justify-center">
        <Icon name="check" className="w-8 h-8" sw={3} />
      </div>
      <div>
        <h2 className="text-base font-bold">Đã giữ thông tin căn cước</h2>
        <p className="text-[13px] text-muted-foreground mt-1 max-w-xs">
          Bước tiếp theo — chụp ảnh chân dung và gửi hồ sơ — thực hiện ở màn thu nhận.
        </p>
      </div>
      <button
        type="button"
        onClick={onQuetTiep}
        className="h-11 px-6 rounded-lg bg-primary text-primary-foreground font-semibold text-sm flex items-center justify-center gap-2 hover:brightness-110 transition-all shadow-sm"
      >
        <Icon name="scan" className="w-4 h-4" /> Quét hồ sơ khác
      </button>
    </div>
  );
}
