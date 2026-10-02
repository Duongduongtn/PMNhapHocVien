import { useEffect, useRef, useState } from "react";
import { Icon } from "./Icon";
import { xuLyAnh, type AnhKetQua } from "../lib/api";

// NAP-04: chọn ảnh thô → khung crop CỐ ĐỊNH 3:4 (kéo + zoom) → xóa phông nền trắng → .jp2.
// Khung hiển thị 288×384 (3:4). Box crop tính theo pixel ảnh GỐC rồi gửi backend.
// anhBanDau (CHANGES #19): URL ảnh thô đã kéo về từ VPS → nạp SẴN vào khung (không bắt chọn
// lại file). TÙY CHỌN để QLY-05/QLY-06 mở không-ảnh-sẵn vẫn chạy như cũ.
const FW = 288;
const FH = 384;

export default function AnhModal({
  onDong,
  onXong,
  anhBanDau,
}: {
  onDong: () => void;
  onXong?: (jp2_b64: string, preview: string) => void; // preview: PNG data-URL để xem lại/chỉnh tiếp (CHANGES #23)
  anhBanDau?: string | null;
}) {
  const [src, setSrc] = useState("");
  const [nat, setNat] = useState({ w: 0, h: 0 });
  const [mucZoom, setMucZoom] = useState(0); // thang −1..1, 0 = GIỮA = cỡ ban đầu (1×); trái thu nhỏ, phải phóng to
  const [pos, setPos] = useState({ x: 0, y: 0 });
  const [xoay, setXoay] = useState(0);      // bước 90° (nút ⟲ ⟳)
  const [nghieng, setNghieng] = useState(0); // tinh chỉnh độ nghiêng (−15..15°)
  const [xoaPhong, setXoaPhong] = useState(true);
  const [kq, setKq] = useState<AnhKetQua | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const fileRef = useRef<File | null>(null);
  const drag = useRef<{ x: number; y: number } | null>(null);

  const baseScale = nat.w ? Math.max(FW / nat.w, FH / nat.h) : 1;
  const zoom = Math.pow(3, mucZoom); // 0→1× (cỡ ban đầu) · −1→1/3 (thu nhỏ) · +1→3× (phóng to)
  const scale = baseScale * zoom;
  const rW = nat.w * scale;
  const rH = nat.h * scale;

  // Grab tự do CẢ 4 HƯỚNG (CHANGES #20): chỉ giữ tối thiểu KEEP phần ảnh trong khung để không
  // kéo mất hẳn ảnh; vùng lộ ra → nền trắng ở canvas. Trước đây ghim 1 trục ở zoom gốc (rW=FW
  // hoặc rH=FH) nên chỉ kéo được 1 chiều.
  const KEEP = 0.25;
  const clamp = (x: number, y: number) => ({
    x: Math.max(rW * KEEP - rW, Math.min(FW - rW * KEEP, x)),
    y: Math.max(rH * KEEP - rH, Math.min(FH - rH * KEEP, y)),
  });

  const chonFile = (f: File) => {
    fileRef.current = f;
    setKq(null);
    setErr("");
    const url = URL.createObjectURL(f);
    const im = new Image();
    im.onload = () => {
      const bs = Math.max(FW / im.naturalWidth, FH / im.naturalHeight);
      setNat({ w: im.naturalWidth, h: im.naturalHeight });
      setMucZoom(0);
      setXoay(0);
      setNghieng(0);
      setPos({ x: (FW - im.naturalWidth * bs) / 2, y: (FH - im.naturalHeight * bs) / 2 });
      setSrc(url);
    };
    im.src = url;
  };

  // Nạp sẵn ảnh thô kéo về từ VPS (CHANGES #19): tải URL → Blob → File → đưa vào khung crop.
  // Lỗi tải (ảnh mất/đổi) chỉ bỏ qua — operator vẫn chọn file tay được.
  useEffect(() => {
    if (!anhBanDau) return;
    let huy = false;
    fetch(anhBanDau)
      .then((r) => (r.ok ? r.blob() : Promise.reject()))
      .then((b) => {
        if (huy) return;
        chonFile(new File([b], "anh-vps.jpg", { type: b.type || "image/jpeg" }));
      })
      .catch(() => {});
    return () => { huy = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [anhBanDau]);

  const datZoom = (m: number) => {
    const mm = Math.max(-1, Math.min(1, m)); // thang −1..1
    setMucZoom(mm);
    // giữ vị trí hợp lệ sau khi đổi zoom (cùng ràng buộc KEEP với clamp)
    const s = baseScale * Math.pow(3, mm);
    const w = nat.w * s;
    const h = nat.h * s;
    setPos((p) => ({
      x: Math.max(w * KEEP - w, Math.min(FW - w * KEEP, p.x)),
      y: Math.max(h * KEEP - h, Math.min(FH - h * KEEP, p.y)),
    }));
  };

  // Lăn chuột trên khung → phóng to/thu nhỏ (CHANGES #21). deltaY>0 (lăn xuống) = thu nhỏ.
  const onWheel = (e: React.WheelEvent) => {
    if (!src) return;
    datZoom(mucZoom - e.deltaY * 0.0015);
  };

  const onMove = (e: React.MouseEvent) => {
    if (!drag.current) return;
    const nx = pos.x + (e.clientX - drag.current.x);
    const ny = pos.y + (e.clientY - drag.current.y);
    drag.current = { x: e.clientX, y: e.clientY };
    setPos(clamp(nx, ny));
  };

  // Dựng đúng khung 3:4 đang thấy (pan + zoom + XOAY) ra canvas → gửi backend (đã crop sẵn 3:4,
  // backend chỉ xóa phông + resize 353×471). WYSIWYG: ảnh xuất = đúng ảnh trong khung. CHANGES #20.
  const dungCanvasBlob = (): Promise<Blob> =>
    new Promise((resolve, reject) => {
      if (!src) return reject(new Error("chưa có ảnh"));
      const im = new Image();
      im.onload = () => {
        const c = document.createElement("canvas");
        c.width = FW;
        c.height = FH;
        const ctx = c.getContext("2d");
        if (!ctx) return reject(new Error("no ctx"));
        ctx.fillStyle = "#ffffff"; // vùng lộ ra khi xoay → nền trắng (khớp chuẩn ảnh thẻ)
        ctx.fillRect(0, 0, FW, FH);
        // khớp CSS: img đặt tại (pos), kích thước rW×rH, xoay quanh TÂM img (transform-origin mặc định)
        ctx.save();
        ctx.translate(pos.x + rW / 2, pos.y + rH / 2);
        ctx.rotate(((xoay + nghieng) * Math.PI) / 180);
        ctx.drawImage(im, -rW / 2, -rH / 2, rW, rH);
        ctx.restore();
        c.toBlob((b) => (b ? resolve(b) : reject(new Error("toBlob null"))), "image/jpeg", 0.95);
      };
      im.onerror = () => reject(new Error("load ảnh lỗi"));
      im.src = src;
    });

  const xuLy = async () => {
    if (!src) return;
    setBusy(true);
    setErr("");
    try {
      const blob = await dungCanvasBlob();
      const file = new File([blob], "anh.jpg", { type: "image/jpeg" });
      const r = await xuLyAnh(file, "", xoaPhong); // box rỗng — canvas đã là 3:4, backend không cắt thêm
      setKq(r);
    } catch {
      setErr("Xử lý ảnh thất bại — thử ảnh khác hoặc kiểm backend.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4" onClick={onDong}>
      <div className="bg-card rounded-xl shadow-xl w-full max-w-2xl p-5" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center gap-2 mb-1">
          <h3 className="text-sm font-bold">Ảnh chân dung</h3>
          <span className="text-[11px] font-semibold text-primary bg-primary/10 rounded-full px-2 py-0.5">NAP-04</span>
          <button onClick={onDong} className="ml-auto text-muted-foreground hover:text-foreground">
            <Icon name="x" className="w-5 h-5" />
          </button>
        </div>
        <p className="text-[12px] text-muted-foreground mb-4">
          Ảnh thô kéo về từ VPS được nạp sẵn (nếu có) — hoặc bấm "Chọn ảnh" để tải file khác. Kéo và phóng to canh mặt vào khung 3:4, rồi xóa phông → nền trắng.
        </p>

        <div className="flex flex-col sm:flex-row gap-5">
          {/* Khung crop 3:4 */}
          <div className="flex flex-col items-center gap-3">
            <div
              className="relative overflow-hidden rounded-lg border-2 border-primary bg-muted select-none"
              style={{ width: FW, height: FH, cursor: src ? "grab" : "default" }}
              onMouseDown={(e) => (drag.current = { x: e.clientX, y: e.clientY })}
              onMouseUp={() => (drag.current = null)}
              onMouseLeave={() => (drag.current = null)}
              onMouseMove={onMove}
              onWheel={onWheel}
            >
              {src ? (
                <img
                  src={src}
                  alt="crop"
                  draggable={false}
                  style={{ position: "absolute", left: pos.x, top: pos.y, width: rW, height: rH, maxWidth: "none", transform: `rotate(${xoay + nghieng}deg)` }}
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-[12px] text-muted-foreground px-4 text-center">
                  Chưa chọn ảnh
                </div>
              )}
              {/* Khung chân dung mẫu (CHANGES #20) — chỉ để căn, KHÔNG dính vào ảnh xuất */}
              {src && (
                <svg viewBox={`0 0 ${FW} ${FH}`} className="absolute inset-0 w-full h-full pointer-events-none" aria-hidden="true">
                  <ellipse cx={FW / 2} cy={FH * 0.46} rx={FW * 0.30} ry={FH * 0.30} fill="none" stroke="#ffffff" strokeOpacity="0.85" strokeWidth="2" strokeDasharray="6 5" />
                  <line x1={FW * 0.5} y1="4" x2={FW * 0.5} y2={FH - 4} stroke="#ffffff" strokeOpacity="0.35" strokeWidth="1" strokeDasharray="4 6" />
                  <line x1="8" y1={FH * 0.40} x2={FW - 8} y2={FH * 0.40} stroke="#ffffff" strokeOpacity="0.45" strokeWidth="1" strokeDasharray="4 6" />
                  <line x1="8" y1={FH * 0.72} x2={FW - 8} y2={FH * 0.72} stroke="#ffffff" strokeOpacity="0.45" strokeWidth="1" strokeDasharray="4 6" />
                </svg>
              )}
            </div>
            {src && (
              <div className="w-full">
                <div className="flex items-center gap-2">
                  <span className="text-[11px] text-muted-foreground shrink-0">Thu nhỏ</span>
                  <input type="range" min={-1} max={1} step={0.02} value={mucZoom} onChange={(e) => datZoom(Number(e.target.value))} className="flex-1" />
                  <span className="text-[11px] text-muted-foreground shrink-0">Phóng to</span>
                </div>
                <p className="text-[10px] text-muted-foreground text-center mt-0.5">Giữa = cỡ gốc · lăn chuột trên khung để phóng/thu</p>
              </div>
            )}
            {src && (
              <div className="w-full space-y-2">
                <div className="flex items-center gap-2">
                  <button type="button" onClick={() => setXoay((x) => x - 90)} className="h-8 px-2.5 rounded-lg border border-border text-[12px] font-medium hover:bg-muted transition-colors inline-flex items-center gap-1">
                    <Icon name="refresh" className="w-3.5 h-3.5 -scale-x-100" /> Xoay trái
                  </button>
                  <button type="button" onClick={() => setXoay((x) => x + 90)} className="h-8 px-2.5 rounded-lg border border-border text-[12px] font-medium hover:bg-muted transition-colors inline-flex items-center gap-1">
                    Xoay phải <Icon name="refresh" className="w-3.5 h-3.5" />
                  </button>
                  {(xoay !== 0 || nghieng !== 0) && (
                    <button type="button" onClick={() => { setXoay(0); setNghieng(0); }} className="ml-auto h-8 px-2 rounded-lg text-[12px] text-muted-foreground hover:text-foreground">
                      Đặt lại
                    </button>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] text-muted-foreground w-14 shrink-0">Nghiêng</span>
                  <input type="range" min={-15} max={15} step={0.5} value={nghieng} onChange={(e) => setNghieng(Number(e.target.value))} className="flex-1" />
                  <span className="text-[11px] tabular-nums w-9 text-right shrink-0">{nghieng}°</span>
                </div>
              </div>
            )}
            <label className="inline-flex items-center gap-2 h-9 px-3 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors cursor-pointer">
              <Icon name="file" className="w-4 h-4" /> {src ? "Thay ảnh khác" : "Chọn ảnh"}
              <input type="file" accept="image/jpeg,image/png" className="hidden" onChange={(e) => e.target.files?.[0] && chonFile(e.target.files[0])} />
            </label>
          </div>

          {/* Kết quả */}
          <div className="flex-1 min-w-0">
            <label className="inline-flex items-center gap-2 text-[13px] mb-3 cursor-pointer">
              <input type="checkbox" checked={xoaPhong} onChange={(e) => setXoaPhong(e.target.checked)} /> Xóa phông → nền trắng
            </label>
            <button
              onClick={xuLy}
              disabled={!src || busy}
              className="w-full inline-flex items-center justify-center gap-2 h-10 rounded-lg bg-primary text-primary-foreground font-semibold text-sm hover:brightness-110 transition-all disabled:opacity-60 mb-3"
            >
              <Icon name="refresh" className={"w-4 h-4" + (busy ? " animate-spin" : "")} /> {busy ? "Đang xử lý…" : "Xử lý ảnh"}
            </button>
            <div className="rounded-lg border border-border bg-muted/40 p-3 flex items-center justify-center" style={{ minHeight: FH / 1.4 }}>
              {kq ? (
                <div className="text-center">
                  <img src={kq.preview} alt="kết quả" className="mx-auto rounded border border-border" style={{ width: 177, height: 236 }} />
                  <p className="text-[12px] text-success font-semibold mt-2">
                    <Icon name="check" className="w-4 h-4 inline" sw={3} /> {kq.w}×{kq.h} · nền trắng · .jp2
                  </p>
                  {onXong && (
                    <p className="text-[11px] text-warning font-medium mt-1">Ảnh đã xử lý — bấm <b>"Dùng ảnh này"</b> bên dưới để áp dụng.</p>
                  )}
                </div>
              ) : (
                <span className="text-[12px] text-muted-foreground">Kết quả xem trước hiện ở đây</span>
              )}
            </div>
            {err && (
              <div className="mt-3 flex items-center gap-2 text-[13px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2">
                <Icon name="warn" className="w-4 h-4" /> {err}
              </div>
            )}
            {kq && onXong && (
              <button
                onClick={() => { onXong(kq.jp2_b64, kq.preview); onDong(); }}
                className="mt-3 w-full inline-flex items-center justify-center gap-2 h-11 rounded-lg bg-primary text-primary-foreground font-semibold text-sm hover:brightness-110 transition-all shadow-sm"
              >
                <Icon name="check" className="w-4 h-4" sw={3} /> Dùng ảnh này
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
