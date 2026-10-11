import { useEffect, useMemo, useRef, useState } from "react";
import ChuGiaiTrangThai from "../ChuGiaiTrangThai";
import VirtualList from "./VirtualList";
import { soVN } from "../../lib/format";
import { ungVienBc2, type HvUngVien, type LoaiHang, type UngVienResp } from "../../lib/tnbc2Api";
import { demDaChon, gomTheoKhoaGoc, khopTim } from "../../lib/tnbcUngVien";

// TNB-04 — bước ②: chọn học viên. Bốn nhóm trong một màn: Sẵn sàng (tích sẵn) · Thi lại (không tích sẵn, gom theo
// khóa gốc, ngưỡng tháng) · Cần xem · Không đưa được. Bám ui-mock/tnbc2.html `wizChon`. Dán danh sách CMT và xử lý
// ngoại lệ ngay trên dòng thuộc lượt tiếp theo (task 110b); hiện chỉ nêu hướng xử lý bằng chữ.

const CAO_DONG = 36;
const LUOI = "grid grid-cols-[32px_minmax(150px,1.6fr)_96px_140px_minmax(160px,1.4fr)] items-center gap-2 px-3";
const dmy = (iso: string) => (iso ? iso.slice(0, 10).split("-").reverse().join("/") : "");

const GOI_Y: Record<string, string> = {
  cap_nhat_tot_nghiep: "Cập nhật tốt nghiệp ở tab \"Tốt nghiệp (ô tô)\" rồi quay lại",
  cuu_trang_thai: "Đưa về đúng trạng thái ở tab \"Học viên không tìm thấy\" rồi quay lại",
  go_khoi_bc2: "Gỡ khỏi BC2 đó trước (tab Báo cáo 2)",
};

function Dong({ h, tich, doiTich, khoa }: { h: HvUngVien; tich?: boolean; doiTich?: (b: boolean) => void; khoa?: boolean }) {
  return (
    <div className={`${LUOI} h-full border-b border-border text-[13px] ${tich ? "bg-tn-soft" : ""} ${khoa ? "text-muted-foreground bg-muted/40" : ""}`}>
      <div>
        {doiTich && (
          <input type="checkbox" aria-label={`Chọn ${h.ten}`} checked={!!tich} onChange={(e) => doiTich(e.target.checked)} />
        )}
      </div>
      <div className="font-medium truncate" title={h.ten}>{h.ten}</div>
      <div className="tabular-nums">{h.ngay_sinh}</div>
      <div className="font-mono text-[12px]">{h.cmt}</div>
      <div className="truncate" title={h.ly_do || h.ten_trang_thai}>
        {khoa || h.nhom === "can_xem" ? (
          <span className="text-warning text-[12px]">{h.ly_do || h.ten_trang_thai}</span>
        ) : (
          <>
            <span className="text-[12px]">{h.ten_trang_thai}</span>
            <span className="ml-1 text-[10px] opacity-70">{h.tt}</span>
          </>
        )}
      </div>
    </div>
  );
}

function Nhom({
  bieuTuong,
  tieuDe,
  moTa,
  children,
  phai,
}: {
  bieuTuong: string;
  tieuDe: string;
  moTa: string;
  children: React.ReactNode;
  phai?: React.ReactNode;
}) {
  return (
    <section className="rounded-xl border border-border bg-card overflow-hidden">
      <div className="flex items-center gap-3 px-4 py-2.5 border-b border-border">
        <span className="text-[16px]">{bieuTuong}</span>
        <div className="min-w-0">
          <div className="font-semibold text-[14px]">{tieuDe}</div>
          <div className="text-[12px] text-muted-foreground">{moTa}</div>
        </div>
        {phai && <div className="ml-auto flex items-center gap-2 shrink-0">{phai}</div>}
      </div>
      {children}
    </section>
  );
}

const nutNho = "h-7 px-2.5 rounded-lg border border-input bg-white text-[12px] font-semibold hover:bg-muted";

export default function BuocChonHocVien({
  maKh,
  tenKh,
  maBc2,
  loai,
  onDoiKhoa,
  onTiep,
}: {
  maKh: string;
  tenKh: string;
  maBc2: string;
  loai: LoaiHang;
  onDoiKhoa: () => void;
  onTiep: (dsMaDk: string[]) => void;
}) {
  const [data, setData] = useState<UngVienResp | null>(null);
  const [loi, setLoi] = useState<string | null>(null);
  const [thang, setThang] = useState<number | undefined>(undefined);
  const [thangNhap, setThangNhap] = useState("");
  const [lamTuoi, setLamTuoi] = useState(0);
  const [sel, setSel] = useState<Set<string>>(new Set());
  const [q, setQ] = useState("");
  const [moRong, setMoRong] = useState<Record<string, boolean>>({});
  const khoiTao = useRef("");

  useEffect(() => {
    let huy = false;
    setLoi(null);
    ungVienBc2(maKh, maBc2, thang, lamTuoi > 0)
      .then((d) => {
        if (huy) return;
        setData(d);
        setThangNhap(String(d.thi_lai_thang));
        const duoc = new Set([...d.nhom.san_sang, ...d.nhom.thi_lai].map((h) => h.ma_dk));
        const key = `${maKh}|${maBc2}`;
        if (khoiTao.current !== key) {   // lần đầu của khóa/BC2 này: tích sẵn nhóm Sẵn sàng
          khoiTao.current = key;
          setSel(new Set(d.nhom.san_sang.filter((h) => h.tich_san).map((h) => h.ma_dk)));
        } else {
          setSel((s) => new Set([...s].filter((ma) => duoc.has(ma))));   // làm tươi: bỏ người không còn đưa được
        }
      })
      .catch((e: unknown) => {
        if (!huy) { setData(null); setLoi(e instanceof Error ? e.message : "Không tải được danh sách học viên"); }
      });
    return () => { huy = true; };
  }, [maKh, maBc2, thang, lamTuoi]);

  const san = useMemo(() => (data?.nhom.san_sang ?? []).filter((h) => khopTim(h, q)), [data, q]);
  const thiLai = useMemo(() => (data?.nhom.thi_lai ?? []).filter((h) => khopTim(h, q)), [data, q]);
  const canXem = useMemo(() => (data?.nhom.can_xem ?? []).filter((h) => khopTim(h, q)), [data, q]);
  const khong = useMemo(() => (data?.nhom.khong_duoc ?? []).filter((h) => khopTim(h, q)), [data, q]);
  const khoaGoc = useMemo(() => gomTheoKhoaGoc(thiLai), [thiLai]);

  const nSan = data ? demDaChon(data.nhom.san_sang, sel) : 0;
  const nThi = data ? demDaChon(data.nhom.thi_lai, sel) : 0;
  const tong = nSan + nThi;

  const doi = (ds: HvUngVien[], bat: boolean) =>
    setSel((s) => { const n = new Set(s); ds.forEach((h) => (bat ? n.add(h.ma_dk) : n.delete(h.ma_dk))); return n; });
  const doiMot = (h: HvUngVien, bat: boolean) => doi([h], bat);

  function chotThang() {
    const v = Math.max(1, Math.min(120, Math.round(Number(thangNhap) || 0)));
    if (v && v !== (thang ?? data?.thi_lai_thang)) setThang(v);
  }

  return (
    <div className="flex-1 min-h-0 flex flex-col">
      {/* Dải tóm tắt luôn hiện */}
      <div className="shrink-0 px-4 py-2.5 bg-tn-soft border-b border-border flex flex-wrap items-center gap-4">
        <div>
          <div className="text-[11px] text-muted-foreground">Sẽ đưa vào BC2</div>
          <div className="text-[20px] font-bold tabular-nums" data-testid="dai-tom-tat">
            {soVN(nSan)} <span className="text-[13px] font-medium text-muted-foreground">của khóa</span> + {soVN(nThi)}{" "}
            <span className="text-[13px] font-medium text-muted-foreground">thi lại</span> = {soVN(tong)}{" "}
            <span className="text-[13px] font-medium text-muted-foreground">học viên</span>
          </div>
        </div>
        {data && data.dem.can_xem > 0 && (
          <div className="text-[12.5px] text-warning">⚠ {soVN(data.dem.can_xem)} học viên cần xem — chưa đưa vào được</div>
        )}
        <div className="ml-auto flex items-center gap-2">
          <input aria-label="Tìm học viên" className="field-input" style={{ width: 240 }} value={q}
            placeholder="Tìm tên / số CMT (Enter để tích)" onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") doi([...san, ...thiLai], true); }} />
          <button type="button" className={nutNho} onClick={() => setSel(new Set())}>Bỏ chọn tất cả</button>
          <button type="button" className={nutNho} onClick={() => setLamTuoi((n) => n + 1)}>Làm tươi</button>
          <ChuGiaiTrangThai />
        </div>
      </div>

      <div className="flex-1 min-h-0 overflow-auto p-4 space-y-4">
        {loi && <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-[13px] text-destructive">{loi}</div>}
        {!data && !loi && <div className="text-[13px] text-muted-foreground">Đang tải danh sách học viên…</div>}

        {data && (
          <>
            <div className="text-[12.5px] text-muted-foreground">
              Khóa <b className="text-foreground">{tenKh}</b> ·{" "}
              {maBc2 ? <>BC2 số <b className="text-foreground">{maBc2}</b></> : "BC2 mới — tool sẽ gợi ý số ở bước sau"}
              {data.bc1 && <> · BC1 <span className="font-mono">{data.bc1.so_bao_cao}</span></>}
              {" · "}{loai === "oto" ? "ô tô" : "mô tô"}
            </div>

            <Nhom bieuTuong="✅" tieuDe={`Sẵn sàng — ${soVN(data.nhom.san_sang.length)} học viên của khóa`}
              moTa={loai === "oto" ? "Đã tốt nghiệp và có số giấy, chưa vào báo cáo nào — tích sẵn." : "Đã học xong, chưa vào báo cáo nào — tích sẵn."}
              phai={<>
                <button type="button" className={nutNho} onClick={() => doi(san, true)}>Chọn tất cả</button>
                <button type="button" className={nutNho} onClick={() => doi(san, false)}>Bỏ chọn</button>
              </>}>
              {san.length === 0 ? (
                <div className="text-center text-[13px] text-muted-foreground py-6">Không có học viên sẵn sàng.</div>
              ) : (
                <VirtualList label="Sẵn sàng" items={san} rowHeight={CAO_DONG} maxHeight={360} keyOf={(h) => h.ma_dk}
                  render={(h) => <Dong h={h} tich={sel.has(h.ma_dk)} doiTich={(b) => doiMot(h, b)} />} />
              )}
            </Nhom>

            <Nhom bieuTuong="🔁" tieuDe={`Thi lại — ${soVN(data.nhom.thi_lai.length)} học viên từ các khóa trước`}
              moTa="Rớt/vắng sát hạch hoặc chưa đạt BC2 — không tích sẵn; tích tay hoặc thêm theo số tháng."
              phai={<>
                <span className="text-[12px]">trong</span>
                <input aria-label="Số tháng thi lại" type="number" min={1} max={120} className="field-input !h-7 !py-0"
                  style={{ width: 64 }} value={thangNhap} onChange={(e) => setThangNhap(e.target.value)}
                  onBlur={chotThang} onKeyDown={(e) => { if (e.key === "Enter") chotThang(); }} />
                <span className="text-[12px]">tháng</span>
                <button type="button"
                  className="h-7 px-2.5 rounded-lg bg-tn text-white text-[12px] font-semibold"
                  onClick={() => doi(data.nhom.thi_lai.filter((h) => h.trong_nguong), true)}>
                  Thêm {soVN(data.dem.thi_lai_trong_nguong)} HV thi lại ≤ {data.thi_lai_thang} tháng
                </button>
              </>}>
              {khoaGoc.length === 0 ? (
                <div className="text-center text-[13px] text-muted-foreground py-6">Không có học viên thi lại.</div>
              ) : (
                khoaGoc.map((k) => {
                  const n = demDaChon(k.hocVien, sel);
                  const mo = !!moRong[k.ma_kh];
                  const trong = k.hocVien[0]?.trong_nguong;
                  return (
                    <div key={k.ma_kh} className="border-b border-border last:border-b-0">
                      <div className="px-4 py-2 flex items-center gap-3 cursor-pointer hover:bg-muted"
                        onClick={() => setMoRong((m) => ({ ...m, [k.ma_kh]: !m[k.ma_kh] }))}>
                        <span className="text-[12px]">{mo ? "▼" : "▶"}</span>
                        <span className="font-medium">{k.ten_kh}</span>
                        <span className="text-[12px] text-muted-foreground">
                          bế giảng {dmy(k.bg)}{k.tuoi_thang != null ? ` · ${k.tuoi_thang} tháng trước` : ""}
                        </span>
                        <span className={`text-[11px] font-semibold px-2 rounded-full border ${
                          trong ? "text-success bg-success/10 border-success/40" : "text-warning bg-warning/10 border-warning/40"}`}>
                          {trong ? `trong ${data.thi_lai_thang} tháng` : `cũ hơn ${data.thi_lai_thang} tháng`}
                        </span>
                        <span className="text-[12.5px] ml-auto">{n}/{k.hocVien.length} đã chọn</span>
                        <button type="button" className={nutNho}
                          onClick={(e) => { e.stopPropagation(); doi(k.hocVien, n < k.hocVien.length); }}>
                          {n < k.hocVien.length ? "Chọn cả khóa" : "Bỏ cả khóa"}
                        </button>
                      </div>
                      {mo && (
                        <VirtualList label={`Thi lại ${k.ten_kh}`} items={k.hocVien} rowHeight={CAO_DONG} maxHeight={240}
                          keyOf={(h) => h.ma_dk}
                          render={(h) => <Dong h={h} tich={sel.has(h.ma_dk)} doiTich={(b) => doiMot(h, b)} />} />
                      )}
                    </div>
                  );
                })
              )}
            </Nhom>

            {canXem.length > 0 && (
              <Nhom bieuTuong="⚠️" tieuDe={`Cần xem — ${soVN(data.nhom.can_xem.length)} học viên`}
                moTa="Chưa đủ điều kiện vào BC2. Xử lý xong rồi bấm Làm tươi.">
                <VirtualList label="Cần xem" items={canXem} rowHeight={CAO_DONG + 14} maxHeight={260} keyOf={(h) => h.ma_dk}
                  render={(h) => (
                    <div className="h-full">
                      <Dong h={h} />
                      {h.goi_y_xu_ly && GOI_Y[h.goi_y_xu_ly] && (
                        <div className="px-3 -mt-1 text-[11.5px] text-muted-foreground pl-[44px]">→ {GOI_Y[h.goi_y_xu_ly]}</div>
                      )}
                    </div>
                  )} />
              </Nhom>
            )}

            <details className="rounded-xl border border-border bg-card overflow-hidden">
              <summary className="flex items-center gap-3 px-4 py-2.5 cursor-pointer">
                <span className="text-[16px]">⛔</span>
                <div>
                  <div className="font-semibold text-[14px]">Không đưa được — {soVN(data.dem.khong_duoc)} học viên</div>
                  <div className="text-[12px] text-muted-foreground">Mở ra để biết vì sao và cách xử lý.</div>
                </div>
              </summary>
              {khong.length === 0 ? (
                <div className="text-center text-[13px] text-muted-foreground py-6">Không có.</div>
              ) : (
                <VirtualList label="Không đưa được" items={khong} rowHeight={CAO_DONG + 14} maxHeight={280}
                  keyOf={(h) => h.ma_dk}
                  render={(h) => (
                    <div className="h-full">
                      <Dong h={h} khoa />
                      {h.goi_y_xu_ly && GOI_Y[h.goi_y_xu_ly] && (
                        <div className="px-3 -mt-1 text-[11.5px] text-muted-foreground pl-[44px]">→ {GOI_Y[h.goi_y_xu_ly]}</div>
                      )}
                    </div>
                  )} />
              )}
            </details>
          </>
        )}
      </div>

      <div className="shrink-0 h-14 bg-card border-t border-border px-4 flex items-center gap-3">
        <button type="button" onClick={onDoiKhoa}
          className="h-9 px-4 rounded-lg border border-input text-[13px] font-semibold hover:bg-muted">
          ← Đổi khóa
        </button>
        <span className="text-[13px] text-muted-foreground">{soVN(tong)} học viên sẽ được đưa vào BC2</span>
        <button type="button" disabled={tong === 0}
          onClick={() => data && onTiep([...data.nhom.san_sang, ...data.nhom.thi_lai].filter((h) => sel.has(h.ma_dk)).map((h) => h.ma_dk))}
          className="ml-auto h-9 px-4 rounded-lg bg-tn text-white text-[13px] font-semibold disabled:opacity-45 disabled:cursor-not-allowed">
          Tiếp tục → Xác nhận ({soVN(tong)} học viên)
        </button>
      </div>
    </div>
  );
}
