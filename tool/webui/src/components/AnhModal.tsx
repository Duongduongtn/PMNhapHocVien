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
  onXong?: (jp2_b64: string) => void;
  anhBanDau?: string | null;
}) {
  const [src, setSrc] = useState("");
  const [nat, setNat] = useState({ w: 0, h: 0 });
  const [zoom, setZoom] = useState(1);
  const [pos, setPos] = useState({ x: 0, y: 0 });
  const [xoaPhong, setXoaPhong] = useState(true);
  const [kq, setKq] = useState<AnhKetQua | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const fileRef = useRef<File | null>(null);
  const drag = useRef<{ x: number; y: number } | null>(null);

  const baseScale = nat.w ? Math.max(FW / nat.w, FH / nat.h) : 1;
  const scale = baseScale * zoom;
  const rW = nat.w * scale;
  const rH = nat.h * scale;

  const clamp = (x: number, y: number) => ({
    x: Math.min(0, Math.max(FW - rW, x)),
    y: Math.min(0, Math.max(FH - rH, y)),
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
      setZoom(1);
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

  const onZoom = (z: number) => {
    setZoom(z);
    // giữ ảnh phủ khung sau khi đổi zoom
    const s = baseScale * z;
    setPos((p) => ({
      x: Math.min(0, Math.max(FW - nat.w * s, p.x)),
      y: Math.min(0, Math.max(FH - nat.h * s, p.y)),
    }));
  };

  const onMove = (e: React.MouseEvent) => {
    if (!drag.current) return;
    const nx = pos.x + (e.clientX - drag.current.x);
    const ny = pos.y + (e.clientY - drag.current.y);
    drag.current = { x: e.clientX, y: e.clientY };
    setPos(clamp(nx, ny));
  };

  const xuLy = async () => {
    if (!fileRef.current) return;
    setBusy(true);
    setErr("");
    try {
      const left = Math.round(-pos.x / scale);
      const top = Math.round(-pos.y / scale);
      const w = Math.round(FW / scale);
      const h = Math.round(FH / scale);
      const r = await xuLyAnh(fileRef.current, `${left},${top},${w},${h}`, xoaPhong);
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
            >
              {src ? (
                <img
                  src={src}
                  alt="crop"
                  draggable={false}
                  style={{ position: "absolute", left: pos.x, top: pos.y, width: rW, height: rH, maxWidth: "none" }}
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-[12px] text-muted-foreground px-4 text-center">
                  Chưa chọn ảnh
                </div>
              )}
            </div>
            {src && (
              <div className="flex items-center gap-2 w-full">
                <Icon name="search" className="w-4 h-4 text-muted-foreground" />
                <input type="range" min={1} max={3} step={0.02} value={zoom} onChange={(e) => onZoom(Number(e.target.value))} className="flex-1" />
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
                onClick={() => { onXong(kq.jp2_b64); onDong(); }}
                className="mt-3 w-full inline-flex items-center justify-center gap-2 h-10 rounded-lg border border-primary text-primary font-semibold text-sm hover:bg-primary/5 transition-colors"
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
