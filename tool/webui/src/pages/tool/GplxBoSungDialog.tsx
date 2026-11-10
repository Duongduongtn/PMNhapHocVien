import { useEffect, useState } from "react";
import { Icon } from "../../components/Icon";
import type { BanWebRef, GplxBanWeb, GplxHoSo, SoGtvt } from "../../lib/api";
import { GplxDaCoKhoi } from "./GplxDaCoKhoi";
import { docBang, gomBang, loiBang, tenHang, trungHangDangKy, type BangGplx } from "./gplxDaCo";

function ngayGioVN(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString("vi-VN", { dateStyle: "short", timeStyle: "short", hour12: false });
}

// Hộp "GPLX đã có" cho học viên đã nạp (QLY-10, TCB-05, TDD §10.7). Chỉ ghi DB khi bấm Lưu; đóng hộp không đổi gì.
export function GplxBoSungDialog({
  tenHv,
  nhanDb,
  tai,
  luu,
  taiNoiCap,
  taiBanWeb,
  onBoQua,
  onDong,
  onDaLuu,
}: {
  tenHv: string | null;
  nhanDb: string; // "DB Nạp" | "DB đích"
  tai: () => Promise<GplxHoSo>;
  luu: (gplx: BangGplx[], tho: Record<string, string>, banWeb?: BanWebRef) => Promise<{ co_o_dich?: boolean }>;
  taiNoiCap: () => Promise<SoGtvt[]>;
  taiBanWeb?: () => Promise<GplxBanWeb>; // có khi học viên có bản bổ sung từ app web chờ duyệt (QLY-10)
  onBoQua?: (ref: BanWebRef) => Promise<unknown>;
  onDong: () => void;
  onDaLuu: (kq: { co_o_dich?: boolean }) => void;
}) {
  const [hs, setHs] = useState<GplxHoSo | null>(null);
  const [banWeb, setBanWeb] = useState<GplxBanWeb | null>(null);
  const [hetBanWeb, setHetBanWeb] = useState(false);
  const [goc, setGoc] = useState<BangGplx[]>([]);
  const [ds, setDs] = useState<BangGplx[]>([]);
  const [noiCap, setNoiCap] = useState<SoGtvt[]>([]);
  const [loi, setLoi] = useState("");
  const [dangLuu, setDangLuu] = useState(false);
  const [xacNhanXoa, setXacNhanXoa] = useState(false);
  const [lanTai, setLanTai] = useState(0);

  useEffect(() => {
    let bo = false;
    setHs(null);
    setLoi("");
    // Bản app web vừa hết hoặc VPS lỗi: vẫn mở bản DB để nhập tay được.
    Promise.all([tai(), taiBanWeb ? taiBanWeb().catch(() => { if (!bo) setHetBanWeb(true); return null; }) : Promise.resolve(null)])
      .then(([d, web]) => {
        if (bo) return;
        const dsDb = docBang(JSON.stringify(d.gplx));
        setHs(d);
        setBanWeb(web);
        setGoc(dsDb);
        setDs(web ? docBang(JSON.stringify(web.gplx)) : dsDb); // tự điền bản app web, chưa ghi gì
      })
      .catch((e) => { if (!bo) setLoi(e instanceof Error ? e.message : "Không đọc được GPLX đã có."); });
    return () => { bo = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `tai` đổi tham chiếu mỗi lần vẽ; chỉ tải khi mở hoặc bấm tải lại
  }, [lanTai]);

  useEffect(() => { taiNoiCap().then(setNoiCap).catch(() => {}); /* eslint-disable-next-line react-hooks/exhaustive-deps */ }, []);

  // CHANGES #101: số đang có trong DB giữ nguyên thì không chặn dạng (khớp backend `ghi`).
  const soCu = new Set((hs?.tho?.SoGPLXDaCo ?? "").split("|").map((s) => s.trim()).filter(Boolean));
  const coLoi = ds.some((b) => loiBang(b, soCu).length > 0) || trungHangDangKy(hs?.hang_khoa, ds);
  const xoaHet = ds.length === 0 && goc.length > 0;

  async function bamLuu() {
    if (!hs) return;
    if (xoaHet && !xacNhanXoa) { setXacNhanXoa(true); return; }
    setLoi("");
    setDangLuu(true);
    try {
      onDaLuu(await luu(gomBang(ds), hs.tho, banWeb ?? undefined));
    } catch (e) {
      setLoi(e instanceof Error ? e.message : "Không lưu được. Kiểm tra kết nối rồi thử lại.");
    } finally {
      setDangLuu(false);
    }
  }

  async function bamBoQua() {
    if (!banWeb || !onBoQua) return;
    setLoi("");
    setDangLuu(true);
    try {
      await onBoQua(banWeb);
    } catch (e) {
      setLoi(e instanceof Error ? e.message : "Không bỏ qua được. Thử lại.");
    } finally {
      setDangLuu(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-3" role="dialog" aria-modal="true" aria-label="GPLX đã có">
      <div className="bg-card rounded-xl shadow-2xl w-full max-w-[860px] max-h-[92vh] flex flex-col">
        <div className="flex items-center gap-2 px-4 py-3 border-b border-border">
          <h3 className="font-bold text-sm min-w-0 truncate">GPLX đã có — {tenHv || "(chưa có tên)"}</h3>
          <button type="button" onClick={onDong} aria-label="Đóng" className="ml-auto w-8 h-8 rounded-lg hover:bg-muted inline-flex items-center justify-center shrink-0">
            <Icon name="x" className="w-5 h-5" />
          </button>
        </div>

        <div className="p-4 overflow-y-auto space-y-3">
          {!hs && !loi && (
            <p className="py-6 text-center text-sm text-muted-foreground"><Icon name="refresh" className="w-4 h-4 animate-spin inline mr-1" /> Đang tải…</p>
          )}
          {hs?.chan && <p className="rounded-md bg-destructive/10 px-3 py-2 text-[13px] text-destructive">{hs.chan}</p>}
          {hs?.lech && !hs.chan && (
            <p className="rounded-md bg-warning/10 px-3 py-2 text-[13px] text-warning">Dữ liệu cũ có số phần không khớp giữa các cột. Kiểm lại từng bằng trước khi lưu.</p>
          )}
          {hetBanWeb && hs && (
            <p className="rounded-md bg-warning/10 px-3 py-2 text-[13px] text-warning">Không lấy được bản bổ sung từ app web. Đang hiện bản trong {nhanDb}, vẫn nhập tay được.</p>
          )}
          {banWeb && (
            <p className="rounded-md bg-primary/5 px-3 py-2 text-[13px] text-primary">
              {banWeb.nguoi_gui || "Người thu nhận"} bổ sung từ app web lúc {ngayGioVN(banWeb.updated_at)}. Kiểm lại với bằng thật, sửa nếu cần rồi mới lưu.
            </p>
          )}
          {hs && (
            <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_minmax(0,2fr)]">
              <div className="rounded-lg border border-border p-3 text-[13px]">
                <div className="text-[12px] font-semibold text-muted-foreground mb-1.5">Đang có trong {nhanDb}</div>
                {goc.length === 0 && <span className="text-muted-foreground">Chưa có GPLX</span>}
                {goc.map((b, i) => (
                  <div key={i} className="mt-1.5 first:mt-0">
                    <div className="font-medium">{tenHang(b)} · {b.so || "—"}</div>
                    <div className="text-[12px] text-muted-foreground">Cấp {b.ngay_cap || "—"}</div>
                  </div>
                ))}
              </div>
              {hs.chan ? (
                <p className="text-[13px] text-muted-foreground self-center">
                  Chỉ xem, không sửa được ở đây.{banWeb ? ` App web gửi: ${docBang(JSON.stringify(banWeb.gplx)).map(tenHang).join(", ")}.` : ""}
                </p>
              ) : (
                <GplxDaCoKhoi ds={ds} onDoi={(d) => { setDs(d); setXacNhanXoa(false); }} noiCap={noiCap} hangKhoa={hs.hang_khoa} tuAppWeb={false} coBanMoi={false} onDungBanWeb={() => {}} chuLuu="lưu" soCu={soCu} />
              )}
            </div>
          )}
          {xoaHet && xacNhanXoa && (
            <p className="rounded-md bg-destructive/10 px-3 py-2 text-[13px] text-destructive">Xóa toàn bộ GPLX đã có của học viên này trong {nhanDb}? Bấm lưu lần nữa để xác nhận.</p>
          )}
          {loi && <p role="alert" className="rounded-md bg-destructive/10 px-3 py-2 text-[13px] text-destructive">{loi}</p>}
          {hs && !hs.chan && <p className="text-[12px] text-muted-foreground">Chưa ghi gì vào DB. Đóng hộp thì không thay đổi. Lưu chỉ ghi các cột GPLX đã có của học viên này.</p>}
        </div>

        <div className="flex flex-wrap justify-end gap-2 px-4 py-3 border-t border-border">
          {loi.includes("vừa đổi") && (
            <button type="button" className="btn btn-secondary" onClick={() => setLanTai((n) => n + 1)}>Tải lại</button>
          )}
          {banWeb && onBoQua && hs && (
            <button type="button" className="btn btn-secondary mr-auto" disabled={dangLuu} onClick={() => void bamBoQua()}>Bỏ qua bản này</button>
          )}
          <button type="button" className="btn btn-secondary" onClick={onDong}>Đóng</button>
          {hs && !hs.chan && (
            <button type="button" className="btn btn-primary" disabled={dangLuu || coLoi} onClick={() => void bamLuu()}>
              {dangLuu ? "Đang lưu…" : xoaHet && xacNhanXoa ? "Xác nhận xóa" : `Lưu vào ${nhanDb}`}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
