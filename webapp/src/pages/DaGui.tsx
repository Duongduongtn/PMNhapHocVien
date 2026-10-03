import { useEffect, useState } from "react";
import { Icon } from "../components/Icon";
import { ODate } from "../components/ODate";
import { PhanTrang } from "../components/PhanTrang";
import { ApiError, dsDaGui, guiAnh, suaHoSo, taiAnhCuaToi, xoaHoSo, type HoSoOut, type HoSoSua } from "../lib/api";
import { dsNhap } from "../lib/draft";
import { dangKyGuiLai, guiLaiTatCa } from "../lib/gui";
import { khopTim } from "../lib/text";

// Thumbnail ảnh chân dung thật (tải của mình). Chưa có ảnh/không tải được → placeholder.
function AnhThumb({ uuid, coAnh, size = "sm" }: { uuid: string; coAnh: boolean; size?: "xs" | "sm" | "lg" }) {
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => {
    if (!coAnh) {
      setUrl(null);
      return;
    }
    let huy = false;
    let u: string | null = null;
    taiAnhCuaToi(uuid)
      .then((x) => {
        if (huy) {
          if (x) URL.revokeObjectURL(x);
          return;
        }
        u = x;
        setUrl(x);
      })
      .catch(() => {});
    return () => {
      huy = true;
      if (u) URL.revokeObjectURL(u);
    };
  }, [uuid, coAnh]);
  const khung = size === "lg" ? "w-20 aspect-[3/4] rounded-lg" : size === "xs" ? "w-8 h-8 rounded-md" : "w-11 h-11 rounded-lg";
  const ico = size === "lg" ? "w-10 h-10" : size === "xs" ? "w-4 h-4" : "w-6 h-6";
  if (url) return <img src={url} alt="Ảnh chân dung" className={`${khung} object-cover shrink-0 border border-border`} />;
  return (
    <span className={`${khung} inline-flex items-center justify-center shrink-0 bg-slate-200 text-slate-400`}>
      <Icon name="user" className={ico} sw={size === "lg" ? 1.5 : 2} />
    </span>
  );
}

// Popup phóng to ảnh chân dung (CHANGES #15) — bấm ảnh ở chi tiết để xem lớn, bấm ngoài để đóng.
function AnhLightbox({ uuid, onDong }: { uuid: string; onDong: () => void }) {
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => {
    let huy = false;
    let u: string | null = null;
    taiAnhCuaToi(uuid)
      .then((x) => {
        if (huy) {
          if (x) URL.revokeObjectURL(x);
          return;
        }
        u = x;
        setUrl(x);
      })
      .catch(() => {});
    return () => {
      huy = true;
      if (u) URL.revokeObjectURL(u);
    };
  }, [uuid]);
  return (
    <div className="fixed inset-0 z-[60] bg-black/80 flex items-center justify-center p-4" onClick={onDong}>
      {url ? (
        <img src={url} alt="Ảnh chân dung" className="max-h-full max-w-full rounded-lg object-contain" />
      ) : (
        <div className="text-white/80 text-sm">Đang tải ảnh…</div>
      )}
      <button onClick={onDong} aria-label="Đóng" className="absolute top-4 right-4 w-10 h-10 rounded-full bg-white/15 text-white flex items-center justify-center hover:bg-white/25 transition-colors">
        <Icon name="x" className="w-6 h-6" />
      </button>
    </div>
  );
}

// Nén ảnh chụp lại về JPEG (cạnh dài ≤ maxCanh) — nhẹ cho upload, server giới hạn 8 MB.
function nenAnh(file: File, maxCanh: number, chatLuong: number): Promise<Blob> {
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
      if (!ctx) return reject(new Error("Không dựng được canvas"));
      ctx.drawImage(img, 0, 0, w, h);
      c.toBlob((b) => (b ? resolve(b) : reject(new Error("Không nén được ảnh"))), "image/jpeg", chatLuong);
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("Không đọc được ảnh"));
    };
    img.src = url;
  });
}

// dd/mm/yyyy | yyyy → yyyymmdd | yyyy0000 (lưu DB). Rỗng/sai → giữ nguyên chuỗi (server validate).
function vnToYmd(s: string): string {
  const t = s.trim();
  if (/^\d{4}$/.test(t)) return `${t}0000`;
  const m = t.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  return m ? `${m[3]}${m[2]}${m[1]}` : t;
}

// THU-02 — Hồ sơ nhân viên đã gửi lên VPS (GET /api/ho-so/cua-toi) + nháp còn chờ gửi (offline).
// Bám bố cục ui-demo/src/pages/app/DaGui.tsx: lọc tab, mobile card / desktop table, modal chi tiết.

type Loc = "all" | "pending" | "imported" | "no_photo";

// yyyymmdd → hiển thị. Năm-only (….0000) → "yyyy". Rỗng → "—".
function nsHienThi(s: string | null): string {
  if (!s) return "—";
  if (/^\d{4}0000$/.test(s)) return s.slice(0, 4);
  if (/^\d{8}$/.test(s)) return `${s.slice(6, 8)}/${s.slice(4, 6)}/${s.slice(0, 4)}`;
  return s;
}

function guiHienThi(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const p = (n: number) => String(n).padStart(2, "0");
  return `${p(d.getDate())}/${p(d.getMonth() + 1)}/${d.getFullYear()} ${p(d.getHours())}:${p(d.getMinutes())}`;
}

function gioiTinhHienThi(g: string | null): string {
  return g === "M" ? "Nam" : g === "F" ? "Nữ" : "—";
}

function TrangThaiChip({ tt }: { tt: string }) {
  if (tt === "imported")
    return (
      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-success bg-success/10 border border-success/30 rounded-full px-2 py-0.5 whitespace-nowrap">
        <Icon name="check" className="w-3 h-3" sw={3} /> Đã nạp
      </span>
    );
  if (tt === "importing")
    return (
      <span className="inline-flex items-center gap-1 text-[11px] font-medium text-primary bg-primary/10 border border-primary/30 rounded-full px-2 py-0.5 whitespace-nowrap">
        <Icon name="refresh" className="w-3 h-3" /> Đang nạp
      </span>
    );
  return (
    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-warning bg-warning/10 border border-warning/30 rounded-full px-2 py-0.5 whitespace-nowrap">
      <Icon name="clock" className="w-3 h-3" /> Chờ nạp
    </span>
  );
}

// Badge hồ sơ thiếu ảnh chân dung (CHANGES #13) — gắn ở list + chi tiết, có bộ lọc riêng.
function ThieuAnhChip() {
  return (
    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-warning bg-warning/10 border border-warning/30 rounded-full px-2 py-0.5 whitespace-nowrap">
      <Icon name="image" className="w-3 h-3" /> Thiếu ảnh
    </span>
  );
}

export default function DaGui() {
  const [ds, setDs] = useState<HoSoOut[] | null>(null);
  const [loi, setLoi] = useState<string | null>(null);
  const [loc, setLoc] = useState<Loc>("all");
  const [sel, setSel] = useState<HoSoOut | null>(null);
  const [soNhap, setSoNhap] = useState(0);
  const [q, setQ] = useState("");
  const [moTim, setMoTim] = useState(false);
  const [trang, setTrang] = useState(0);
  const [coTrang, setCoTrang] = useState(20);
  // Desktop chọn-nhiều-để-xóa (CHANGES #28) — chỉ chọn được hồ sơ "Chờ nạp" (pending).
  const [chon, setChon] = useState<Set<string>>(new Set());
  const [xacNhanXoa, setXacNhanXoa] = useState(false);
  const [dangXoa, setDangXoa] = useState(false);

  async function tai() {
    setLoi(null);
    try {
      setDs(await dsDaGui());
    } catch (e) {
      setLoi(e instanceof ApiError ? e.message : "Không tải được danh sách. Kiểm tra mạng rồi thử lại.");
    }
  }

  useEffect(() => {
    dangKyGuiLai();
    // Vào màn này cũng là dịp thử gửi lại nháp còn tồn, rồi mới tải danh sách từ VPS.
    void guiLaiTatCa().then(() => {
      setSoNhap(dsNhap().length);
      void tai();
    });
    setSoNhap(dsNhap().length);
    void tai();
  }, []);

  // Lọc "no_photo" (CHANGES #13) theo co_anh — khác trục trạng thái; các lọc khác theo trang_thai.
  const khopLoc = (h: HoSoOut) => (loc === "no_photo" ? !h.co_anh : loc === "all" || h.trang_thai === loc);
  const rows = (ds ?? []).filter((h) => khopLoc(h) && khopTim(q, h.ho_ten, h.so_cccd));
  // UI-3: phân trang phía client (danh sách của chính mình, không lớn). Đổi lọc/tìm → về trang 1.
  useEffect(() => { setTrang(0); }, [loc, q, coTrang]);
  // Đổi lọc/tìm/trang → bỏ lựa chọn (tránh xóa nhầm hồ sơ ngoài tầm nhìn).
  useEffect(() => { setChon(new Set()); }, [loc, q, coTrang, trang]);
  const rowsTrang = rows.slice(trang * coTrang, (trang + 1) * coTrang);
  // Chỉ hồ sơ Chờ nạp mới chọn/xóa được (server chặn xóa đã/đang nạp).
  const pendingTrang = rowsTrang.filter((h) => h.trang_thai === "pending");
  const chonHetPending = pendingTrang.length > 0 && pendingTrang.every((h) => chon.has(h.uuid));

  function toggleChon(uuid: string) {
    setChon((cu) => {
      const s = new Set(cu);
      if (s.has(uuid)) s.delete(uuid);
      else s.add(uuid);
      return s;
    });
  }
  function toggleChonHet() {
    setChon((cu) => {
      const s = new Set(cu);
      if (chonHetPending) pendingTrang.forEach((h) => s.delete(h.uuid));
      else pendingTrang.forEach((h) => s.add(h.uuid));
      return s;
    });
  }
  async function xoaDaChon() {
    setDangXoa(true);
    setLoi(null);
    // Phân biệt 409 (hồ sơ vừa bị tool nạp giữa chừng — không xóa được nữa) với lỗi mạng (thử lại).
    let loiNap = 0;
    let loiKhac = 0;
    for (const uuid of chon) {
      try {
        await xoaHoSo(uuid);
      } catch (e) {
        if (e instanceof ApiError && e.status === 409) loiNap += 1;
        else loiKhac += 1;
      }
    }
    setDangXoa(false);
    setXacNhanXoa(false);
    setChon(new Set());
    const phan: string[] = [];
    if (loiNap > 0) phan.push(`${loiNap} hồ sơ vừa được máy nạp nên không xóa được`);
    if (loiKhac > 0) phan.push(`${loiKhac} hồ sơ lỗi mạng, thử lại sau`);
    if (phan.length) setLoi(`Không xóa được: ${phan.join("; ")}. Danh sách đã làm mới.`);
    await tai();
  }
  const dem = (t: string) => (ds ?? []).filter((h) => h.trang_thai === t).length;
  const demThieuAnh = (ds ?? []).filter((h) => !h.co_anh).length;
  const rong = q.trim()
    ? "Không tìm thấy hồ sơ khớp."
    : loc === "no_photo"
      ? "Không có hồ sơ nào thiếu ảnh."
      : "Chưa có hồ sơ nào ở nhóm này.";

  return (
    <div className="lg:p-6 lg:max-w-5xl lg:mx-auto">
      <div className="p-4 lg:p-0 lg:mb-4">
        <div className="flex items-start gap-2">
          <h2 className="text-base font-bold">Hồ sơ tôi đã gửi</h2>
          {/* Tìm kiếm — desktop hiện ô, mobile thu gọn nút kính lúp */}
          <div className="hidden lg:block ml-auto relative w-64 shrink-0">
            <Icon name="search" className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input className="field-input pl-9" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Tìm tên hoặc số CCCD" aria-label="Tìm hồ sơ" />
          </div>
          <button
            type="button"
            onClick={() => {
              setMoTim((v) => !v);
              if (moTim) setQ("");
            }}
            aria-label={moTim ? "Đóng tìm kiếm" : "Tìm kiếm"}
            className="lg:hidden ml-auto w-10 h-10 rounded-lg border border-border flex items-center justify-center shrink-0 text-muted-foreground hover:bg-muted transition-colors"
          >
            <Icon name={moTim ? "x" : "search"} className="w-5 h-5" />
          </button>
        </div>
        <p className="text-[12px] text-muted-foreground mt-0.5">Học viên bạn đã quét/gửi lên hệ thống. Bấm để xem chi tiết.</p>

        {/* Ô tìm bung ra ở mobile */}
        {moTim && (
          <div className="lg:hidden mt-2 relative">
            <Icon name="search" className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input autoFocus className="field-input pl-9" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Tìm tên (gõ không dấu cũng được) hoặc số CCCD" aria-label="Tìm hồ sơ" />
          </div>
        )}

        {soNhap > 0 && (
          <div className="mt-3 flex items-center gap-2 text-[12px] text-warning bg-warning/10 border border-warning/30 rounded-lg px-3 py-2">
            <Icon name="wifiOff" className="w-4 h-4 shrink-0" /> {soNhap} hồ sơ chưa gửi được (chờ mạng) — sẽ tự gửi lại khi có mạng.
          </div>
        )}

        {ds && (
          <div className="inline-flex rounded-lg bg-muted p-1 mt-3">
            {(
              [
                ["all", `Tất cả (${ds.length})`],
                ["pending", `Chờ nạp (${dem("pending")})`],
                ["imported", `Đã nạp (${dem("imported")})`],
                ["no_photo", `Thiếu ảnh (${demThieuAnh})`],
              ] as const
            ).map(([k, label]) => (
              <button
                key={k}
                onClick={() => setLoc(k)}
                className={
                  "px-3.5 py-1.5 text-[13px] rounded-md transition-colors " +
                  (loc === k ? "bg-card shadow-sm text-primary font-semibold" : "text-muted-foreground font-medium hover:text-foreground")
                }
              >
                {label}
              </button>
            ))}
          </div>
        )}
      </div>

      {loi && (
        <div className="mx-4 lg:mx-0 flex items-center justify-between gap-2 text-[13px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2">
          <span className="flex items-center gap-2">
            <Icon name="warn" className="w-4 h-4 shrink-0" /> {loi}
          </span>
          <button onClick={() => void tai()} className="font-semibold hover:underline shrink-0">
            Thử lại
          </button>
        </div>
      )}

      {!ds && !loi && <div className="px-4 py-10 text-center text-sm text-muted-foreground">Đang tải…</div>}

      {ds && (
        <>
          {/* DESKTOP: thanh thao tác xóa nhiều — chỉ hiện khi đã chọn ≥1 (CHANGES #28) */}
          {chon.size > 0 && (
            <div className="hidden lg:flex items-center gap-3 mb-3 px-4 py-2.5 rounded-lg bg-primary/5 border border-primary/20">
              <Icon name="check" className="w-4 h-4 text-primary shrink-0" sw={3} />
              <span className="text-[13px] font-medium">Đã chọn {chon.size} hồ sơ Chờ nạp</span>
              <button type="button" onClick={() => setChon(new Set())} className="text-[13px] text-muted-foreground hover:text-foreground underline">
                Bỏ chọn
              </button>
              <button
                type="button"
                onClick={() => setXacNhanXoa(true)}
                className="ml-auto inline-flex items-center gap-2 h-9 px-4 rounded-lg bg-destructive text-white font-semibold text-sm hover:brightness-110 transition"
              >
                <Icon name="warn" className="w-4 h-4" /> Xóa {chon.size} hồ sơ
              </button>
            </div>
          )}

          {/* MOBILE: card list */}
          <div className="lg:hidden divide-y divide-border border-t border-border">
            {rowsTrang.map((h) => (
              <button
                key={h.uuid}
                onClick={() => setSel(h)}
                className="w-full text-left flex items-center gap-3 px-4 py-3 hover:bg-muted/60 transition-colors"
              >
                <AnhThumb uuid={h.uuid} coAnh={h.co_anh} />
                <div className="min-w-0 flex-1">
                  <div className="font-semibold text-[14px] truncate">{h.ho_ten || "(chưa có tên)"}</div>
                  <div className="text-[12px] text-muted-foreground truncate">
                    {gioiTinhHienThi(h.gioi_tinh)} · {h.so_cccd || "—"}
                  </div>
                  <div className="text-[11px] text-muted-foreground truncate">Gửi {guiHienThi(h.created_at)}</div>
                </div>
                <div className="flex flex-col items-end gap-1 shrink-0">
                  <TrangThaiChip tt={h.trang_thai} />
                  {!h.co_anh && <ThieuAnhChip />}
                </div>
              </button>
            ))}
            {!rows.length && <div className="px-4 py-10 text-center text-sm text-muted-foreground">{rong}</div>}
          </div>

          {/* DESKTOP: table */}
          <div className="hidden lg:block bg-card border border-border rounded-xl overflow-hidden">
            <table className="w-full text-[13px]">
              <thead>
                <tr className="bg-muted text-muted-foreground text-left">
                  <th className="px-4 py-2.5 w-10">
                    <input
                      type="checkbox"
                      className="accent-primary align-middle"
                      checked={chonHetPending}
                      disabled={pendingTrang.length === 0}
                      onChange={toggleChonHet}
                      aria-label="Chọn tất cả hồ sơ Chờ nạp trên trang"
                    />
                  </th>
                  <th className="px-4 py-2.5 font-semibold">Họ và tên</th>
                  <th className="px-4 py-2.5 font-semibold">Giới tính</th>
                  <th className="px-4 py-2.5 font-semibold">Số CCCD</th>
                  <th className="px-4 py-2.5 font-semibold">Ngày sinh</th>
                  <th className="px-4 py-2.5 font-semibold">Nơi thường trú</th>
                  <th className="px-4 py-2.5 font-semibold">Ngày gửi</th>
                  <th className="px-4 py-2.5 font-semibold text-center">Trạng thái</th>
                </tr>
              </thead>
              <tbody>
                {rowsTrang.map((h) => (
                  <tr key={h.uuid} onClick={() => setSel(h)} className={"border-t border-border cursor-pointer transition-colors " + (chon.has(h.uuid) ? "bg-primary/5" : "hover:bg-muted/60")}>
                    <td className="px-4 py-2" onClick={(e) => e.stopPropagation()}>
                      {h.trang_thai === "pending" ? (
                        <input
                          type="checkbox"
                          className="accent-primary align-middle"
                          checked={chon.has(h.uuid)}
                          onChange={() => toggleChon(h.uuid)}
                          aria-label={`Chọn ${h.ho_ten || "hồ sơ"}`}
                        />
                      ) : null}
                    </td>
                    <td className="px-4 py-2 font-semibold">
                      <div className="flex items-center gap-2.5">
                        <AnhThumb uuid={h.uuid} coAnh={h.co_anh} size="xs" />
                        <span>{h.ho_ten || "(chưa có tên)"}</span>
                      </div>
                    </td>
                    <td className="px-4 py-2">{gioiTinhHienThi(h.gioi_tinh)}</td>
                    <td className="px-4 py-2 tabular-nums">{h.so_cccd || "—"}</td>
                    <td className="px-4 py-2 tabular-nums">{nsHienThi(h.ngay_sinh)}</td>
                    <td className="px-4 py-2 max-w-[260px] truncate">{h.noi_tt_raw || "—"}</td>
                    <td className="px-4 py-2 tabular-nums">{guiHienThi(h.created_at)}</td>
                    <td className="px-4 py-2 text-center">
                      <div className="flex flex-col items-center gap-1">
                        <TrangThaiChip tt={h.trang_thai} />
                        {!h.co_anh && <ThieuAnhChip />}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!rows.length && <div className="px-4 py-10 text-center text-sm text-muted-foreground">{rong}</div>}
          </div>

          <PhanTrang total={rows.length} trang={trang} coTrang={coTrang} onTrang={setTrang} onCoTrang={setCoTrang} />
        </>
      )}

      {/* CHI TIẾT (modal) — xem; còn Chờ nạp thì sửa/chụp lại (CHANGES #12) / xóa (THU-05) */}
      {sel && (
        <ChiTiet
          row={sel}
          onDong={() => setSel(null)}
          onCapNhat={(moi) => { setSel(moi); void tai(); }}
          onXoa={() => { setSel(null); void tai(); }}
        />
      )}

      {/* Dialog xác nhận xóa nhiều (CHANGES #28) — chỉ hồ sơ Chờ nạp */}
      {xacNhanXoa && (
        <div className="fixed inset-0 z-50 bg-black/60 flex items-center justify-center p-4" onClick={(e) => { if (e.target === e.currentTarget && !dangXoa) setXacNhanXoa(false); }}>
          <div className="bg-card rounded-xl shadow-2xl w-full max-w-sm p-5">
            <div className="flex items-start gap-3">
              <span className="w-11 h-11 rounded-full bg-destructive/10 text-destructive flex items-center justify-center shrink-0"><Icon name="warn" className="w-6 h-6" /></span>
              <div>
                <h3 className="font-bold text-sm">Xóa {chon.size} hồ sơ khỏi hàng chờ nạp?</h3>
                <p className="text-[13px] text-muted-foreground mt-1">
                  Hồ sơ chưa nạp vào máy tính nên còn xóa được. Lần tới máy nạp bấm "Kéo về", các hồ sơ này biến mất khỏi danh sách chờ nạp. <b className="text-destructive">Xóa rồi không lấy lại được</b> — gửi nhầm thì tạo hồ sơ mới.
                </p>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-5">
              <button onClick={() => setXacNhanXoa(false)} disabled={dangXoa} className="h-10 px-4 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors disabled:opacity-60">Giữ lại</button>
              <button onClick={() => void xoaDaChon()} disabled={dangXoa} className="h-10 px-5 rounded-lg bg-destructive text-white text-sm font-semibold hover:brightness-110 transition disabled:opacity-60 inline-flex items-center gap-2">
                <Icon name={dangXoa ? "refresh" : "warn"} className={"w-4 h-4" + (dangXoa ? " animate-spin" : "")} /> {dangXoa ? "Đang xóa…" : `Xóa ${chon.size} hồ sơ`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function ChiTiet({ row, onDong, onCapNhat, onXoa }: { row: HoSoOut; onDong: () => void; onCapNhat: (moi: HoSoOut) => void; onXoa: () => void }) {
  const suaDuoc = row.trang_thai === "pending"; // server chỉ cho sửa/xóa khi pending
  const [che, setChe] = useState<"xem" | "sua">("xem");
  const [f, setF] = useState<HoSoSua>({});
  const [luu, setLuu] = useState(false);
  const [loi, setLoi] = useState<string | null>(null);
  const [xemLon, setXemLon] = useState(false); // popup phóng to ảnh (CHANGES #15)
  const [xacNhanXoa, setXacNhanXoa] = useState(false); // THU-05: panel xác nhận 2 bước
  const [dangXoa, setDangXoa] = useState(false);

  async function xoa() {
    setLoi(null);
    setDangXoa(true);
    try {
      await xoaHoSo(row.uuid);
      onXoa(); // đóng modal + tải lại danh sách (hồ sơ đã xóa biến mất)
    } catch (e) {
      // 409 = tool vừa khóa/nạp hồ sơ giữa chừng → báo + chuyển về chỉ xem
      baoLoi(e, "Không xóa được. Kiểm tra mạng rồi thử lại.");
      setXacNhanXoa(false);
    } finally {
      setDangXoa(false);
    }
  }

  // 409 = tool đã khóa hồ sơ (importing) sau khi mở → báo + chuyển về chỉ xem (CHANGES #12, EC).
  function baoLoi(e: unknown, macDinh: string) {
    if (e instanceof ApiError) {
      setLoi(e.message);
      if (e.status === 409) {
        setChe("xem");
        onCapNhat({ ...row, trang_thai: "importing" });
      }
    } else {
      setLoi(macDinh);
    }
  }

  function moSua() {
    setF({
      ho_ten: row.ho_ten,
      so_cccd: row.so_cccd,
      so_cmnd_cu: row.so_cmnd_cu,
      gioi_tinh: row.gioi_tinh,
      ngay_sinh: row.ngay_sinh,
      noi_tt_raw: row.noi_tt_raw,
    });
    setLoi(null);
    setChe("sua");
  }

  async function doiAnh(file: File) {
    setLoi(null);
    setLuu(true);
    try {
      const blob = await nenAnh(file, 1600, 0.85);
      const moi = await guiAnh(row.uuid, blob);
      onCapNhat(moi);
    } catch (e) {
      baoLoi(e, "Không đổi được ảnh. Thử lại.");
    } finally {
      setLuu(false);
    }
  }

  async function luuSua() {
    setLoi(null);
    setLuu(true);
    try {
      // f.ngay_sinh đã là yyyymmdd (khởi tạo từ row + ô nhập đã vnToYmd ở onChange).
      const moi = await suaHoSo(row.uuid, f);
      onCapNhat(moi);
      setChe("xem");
    } catch (e) {
      baoLoi(e, "Không lưu được. Kiểm tra mạng rồi thử lại.");
    } finally {
      setLuu(false);
    }
  }

  const set = <K extends keyof HoSoSua>(k: K, v: HoSoSua[K]) => setF((p) => ({ ...p, [k]: v }));

  return (
    <div className="fixed inset-0 z-50 bg-black/60 flex items-end sm:items-center justify-center p-0 sm:p-4" onClick={(e) => { if (e.target === e.currentTarget) onDong(); }}>
      <div className="bg-card w-full sm:max-w-md rounded-t-2xl sm:rounded-xl shadow-2xl max-h-[92vh] flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3 border-b border-border shrink-0">
          <h3 className="font-bold text-sm">{che === "sua" ? "Sửa hồ sơ" : "Chi tiết hồ sơ đã gửi"}</h3>
          <button onClick={onDong} aria-label="Đóng" className="w-8 h-8 rounded-lg hover:bg-muted flex items-center justify-center transition-colors">
            <Icon name="x" className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5 overflow-y-auto">
          <div className="flex items-start gap-4">
            <div className="shrink-0">
              <button
                type="button"
                onClick={() => { if (row.co_anh) setXemLon(true); }}
                className={row.co_anh ? "block cursor-zoom-in" : "block cursor-default"}
                aria-label={row.co_anh ? "Phóng to ảnh chân dung" : undefined}
              >
                <AnhThumb uuid={row.uuid} coAnh={row.co_anh} size="lg" />
              </button>
            </div>
            <div className="min-w-0 flex-1">
              <div className="font-bold text-[15px]">{row.ho_ten || "(chưa có tên)"}</div>
              <div className="mt-1 flex items-center gap-1.5 flex-wrap"><TrangThaiChip tt={row.trang_thai} />{!row.co_anh && <ThieuAnhChip />}</div>
              <div className="text-[12px] text-muted-foreground mt-2">Gửi lúc {guiHienThi(row.created_at)}</div>
            </div>
          </div>

          {/* Đổi ảnh khi còn Chờ nạp: 2 lối — chụp trực tiếp / chọn ảnh có sẵn (CHANGES #15) */}
          {suaDuoc && (
            <div className="mt-3 grid grid-cols-2 gap-2">
              <label className="h-10 rounded-lg border border-border bg-secondary text-foreground text-[13px] font-medium flex items-center justify-center gap-1.5 hover:bg-muted transition-colors cursor-pointer">
                <Icon name="camera" className="w-4 h-4" /> {row.co_anh ? "Chụp lại" : "Chụp ảnh"}
                <input type="file" accept="image/*" capture="user" className="hidden" disabled={luu}
                  onChange={(e) => { const file = e.target.files?.[0]; e.target.value = ""; if (file) void doiAnh(file); }} />
              </label>
              <label className="h-10 rounded-lg border border-border bg-secondary text-foreground text-[13px] font-medium flex items-center justify-center gap-1.5 hover:bg-muted transition-colors cursor-pointer">
                <Icon name="image" className="w-4 h-4" /> Chọn từ máy
                <input type="file" accept="image/*" className="hidden" disabled={luu}
                  onChange={(e) => { const file = e.target.files?.[0]; e.target.value = ""; if (file) void doiAnh(file); }} />
              </label>
            </div>
          )}

          {xemLon && row.co_anh && <AnhLightbox uuid={row.uuid} onDong={() => setXemLon(false)} />}

          {loi && (
            <div className="mt-3 flex items-start gap-2 text-[12px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2">
              <Icon name="warn" className="w-4 h-4 shrink-0 mt-0.5" /> {loi}
            </div>
          )}

          {che === "sua" ? (
            <div className="mt-4 space-y-3">
              <OSua label="Họ và tên" value={f.ho_ten ?? ""} onChange={(v) => set("ho_ten", v)} />
              <OSua label="Số CCCD" value={f.so_cccd ?? ""} onChange={(v) => set("so_cccd", v)} inputMode="numeric" />
              <div className="grid grid-cols-2 gap-3">
                <ODate
                  label="Ngày sinh"
                  value={nsHienThi(f.ngay_sinh ?? null) === "—" ? "" : nsHienThi(f.ngay_sinh ?? null)}
                  onChange={(v) => set("ngay_sinh", vnToYmd(v))}
                />
                <div>
                  <label className="field-label">Giới tính</label>
                  <select className="field-input mt-1" value={f.gioi_tinh ?? "M"} onChange={(e) => set("gioi_tinh", e.target.value)}>
                    <option value="M">Nam</option>
                    <option value="F">Nữ</option>
                  </select>
                </div>
              </div>
              <OSua label="Nơi thường trú" value={f.noi_tt_raw ?? ""} onChange={(v) => set("noi_tt_raw", v)} />
            </div>
          ) : (
            <div className="mt-4 space-y-2.5">
              {(
                [
                  ["Số CCCD", row.so_cccd || "—"],
                  ["Số CMND cũ", row.so_cmnd_cu || "—"],
                  ["Giới tính", gioiTinhHienThi(row.gioi_tinh)],
                  ["Ngày sinh", nsHienThi(row.ngay_sinh)],
                  ["Nơi thường trú", row.noi_tt_raw || "—"],
                  ...(row.ma_dk ? ([["Mã đăng ký", row.ma_dk]] as [string, string][]) : []),
                ] as [string, string][]
              ).map(([k, v]) => (
                <div key={k} className="flex justify-between gap-3 text-[13px] border-b border-border pb-2 last:border-0">
                  <span className="text-muted-foreground shrink-0">{k}</span>
                  <span className="font-medium text-right break-words">{v}</span>
                </div>
              ))}
              {/* Hồ sơ đã/đang nạp: khóa thao tác + chú thích (THU-05, CHANGES #26) */}
              {!suaDuoc && (
                <p className="text-[12px] text-muted-foreground mt-2 flex items-start gap-1.5">
                  <Icon name="lock" className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                  Hồ sơ đã được máy nạp xử lý. Cần gỡ hay sửa thì báo người nạp thao tác trên máy tính.
                </p>
              )}
            </div>
          )}
        </div>

        {/* THU-05: xác nhận xóa 2 bước — chỉ hồ sơ Chờ nạp (CHANGES #26) */}
        {xacNhanXoa && (
          <div className="mx-5 mb-3 rounded-lg border border-destructive/40 bg-destructive/10 p-3 space-y-2 shrink-0">
            <div className="text-[13px] font-semibold text-destructive flex items-center gap-1.5">
              <Icon name="warn" className="w-4 h-4" /> Xóa hồ sơ này khỏi hàng chờ nạp?
            </div>
            <p className="text-[12px] text-muted-foreground">
              Hồ sơ chưa nạp vào máy tính nên còn xóa được. Lần tới máy nạp bấm "Kéo về", hồ sơ sẽ biến mất khỏi danh sách chờ nạp. Xóa rồi không lấy lại được — gửi nhầm thì tạo hồ sơ mới.
            </p>
            <div className="flex gap-2">
              <button onClick={() => setXacNhanXoa(false)} disabled={dangXoa} className="h-9 px-3 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors">Giữ lại</button>
              <button onClick={() => void xoa()} disabled={dangXoa} className="ml-auto h-9 px-4 rounded-lg bg-destructive text-white text-sm font-semibold inline-flex items-center gap-2 hover:brightness-110 transition disabled:opacity-60">
                <Icon name={dangXoa ? "refresh" : "warn"} className={"w-4 h-4" + (dangXoa ? " animate-spin" : "")} /> {dangXoa ? "Đang xóa…" : "Xóa hồ sơ"}
              </button>
            </div>
          </div>
        )}

        <div className="p-3 border-t border-border shrink-0 flex items-center gap-2">
          {che === "sua" ? (
            <>
              <button onClick={() => setChe("xem")} disabled={luu} className="h-10 px-4 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors">Hủy</button>
              <button onClick={() => void luuSua()} disabled={luu} className="ml-auto h-10 px-5 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:brightness-110 transition shadow-sm flex items-center gap-2 disabled:opacity-60">
                <Icon name={luu ? "refresh" : "check"} className={"w-4 h-4" + (luu ? " animate-spin" : "")} sw={3} /> {luu ? "Đang lưu…" : "Lưu"}
              </button>
            </>
          ) : suaDuoc ? (
            <>
              <button onClick={moSua} className="inline-flex items-center gap-1.5 h-10 px-3 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors"><Icon name="edit" className="w-4 h-4" /> Sửa thông tin</button>
              <button onClick={() => { setLoi(null); setXacNhanXoa(true); }} disabled={xacNhanXoa} className="inline-flex items-center gap-1.5 h-10 px-3 rounded-lg border border-destructive/40 text-destructive text-sm font-medium hover:bg-destructive/10 transition-colors disabled:opacity-60"><Icon name="warn" className="w-4 h-4" /> Xóa</button>
              <button onClick={onDong} className="ml-auto h-10 px-5 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:brightness-110 transition shadow-sm">Đóng</button>
            </>
          ) : (
            <button onClick={onDong} className="ml-auto h-10 px-5 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:brightness-110 transition shadow-sm">Đóng</button>
          )}
        </div>
      </div>
    </div>
  );
}

function OSua({ label, value, onChange, inputMode }: { label: string; value: string; onChange: (v: string) => void; inputMode?: "text" | "numeric" }) {
  return (
    <div>
      <label className="field-label">{label}</label>
      <input className="field-input mt-1" value={value} inputMode={inputMode} onChange={(e) => onChange(e.target.value)} />
    </div>
  );
}
