import { useEffect, useRef, useState } from "react";
import { Icon } from "./Icon";
import type { KetQuaAnh } from "../lib/api";

// Avatar mỗi dòng lưới HV, lazy-load (IntersectionObserver): chỉ tải thumbnail khi dòng lọt
// viewport, không request cả khóa. 3 ca (TDD §11.1):
//   coAnh=false → icon người (chưa ảnh) · thumb OK → ảnh · 404/422 → icon ảnh-vỡ (khác icon người).
//
// Tách từ TraCuuDB (QLY-01) để màn Tra cứu CDB đích (TCB-01) dùng lại mà KHÔNG đụng TraCuuDB.
// `tai(ver)` tùy nguồn: Nạp = taiAnhThumb(maDk, ver) · CDB = taiAnhThumbCDB(maDk, target, ver).
export default function AnhAvatar({ coAnh, ver = 0, tai }: {
  coAnh: boolean;
  ver?: number;
  tai: (ver: number) => Promise<KetQuaAnh>;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [url, setUrl] = useState<string | null>(null);
  const [loi, setLoi] = useState(false);     // file mất/hỏng
  const [hien, setHien] = useState(false);   // đã lọt viewport

  useEffect(() => {
    if (!coAnh || hien) return;
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      (ents) => { if (ents.some((e) => e.isIntersecting)) { setHien(true); io.disconnect(); } },
      { rootMargin: "120px" },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [coAnh, hien]);

  useEffect(() => {
    if (!hien || !coAnh) return;
    let huy = false;
    let obj: string | null = null;
    setLoi(false);
    void tai(ver).then((kq) => {
      if (huy) return;
      if ("url" in kq) { obj = kq.url; setUrl(kq.url); } else setLoi(true);
    });
    return () => { huy = true; if (obj) URL.revokeObjectURL(obj); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hien, coAnh, ver]);

  const box = "w-9 h-9 rounded-md border flex items-center justify-center overflow-hidden shrink-0";
  if (!coAnh)
    return <div className={box + " border-border bg-muted"} title="Chưa có ảnh"><Icon name="user" className="w-5 h-5 text-muted-foreground" /></div>;
  if (loi)
    return <div className={box + " border-destructive/40 bg-destructive/10"} title="DB có đường dẫn nhưng mất/hỏng file ảnh"><Icon name="imageOff" className="w-5 h-5 text-destructive" /></div>;
  if (url)
    return <div className={box + " border-border bg-muted"}><img src={url} alt="" className="w-full h-full object-cover" /></div>;
  return <div ref={ref} className={box + " border-border bg-muted"}><Icon name="image" className="w-4 h-4 text-muted-foreground/40" /></div>;
}
