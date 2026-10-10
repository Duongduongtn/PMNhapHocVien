import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import BuocGiaoVien from "./BuocGiaoVien";
import BuocPhanCong from "./BuocPhanCong";
import BuocXe from "./BuocXe";
import GhiBanNhap from "./GhiBanNhap";
import { Icon } from "../../components/Icon";
import { useConfigDrawer } from "../../lib/configDrawer";
import { ymdToVN } from "../../lib/format";
import {
  getSyncTargets,
  dsKhoaPC,
  hienTrangPC,
  dsGiaoVienPC,
  dsMonPC,
  dsXePC,
  kiemTraPC,
  type BanNhapPC,
  type GiaoVienPC,
  type MonPC,
  type XePC,
  type GhiPCKetQua,
  type HienTrangPC,
  type KhoaPC,
  type KiemTraPC,
  type MucVanDe,
  type VanDePC,
} from "../../lib/api";

// PCG — Phân công GV – xe theo khóa. Khung phân hệ (task 88): chọn khóa, thanh 3 bước,
// bản nháp ở phía trình duyệt, cột "Kiểm tra khóa" gọi /local/phancong/kiem-tra (server là
// nguồn luật duy nhất). Nội dung từng bước dựng ở task 89–94. Bám ui-mock/phancong.html.

const BUOC: { so: 1 | 2 | 3; ten: string; huongDan: string }[] = [
  { so: 1, ten: "Giáo viên của khóa", huongDan: "Chọn những giáo viên sẽ tham gia dạy khóa này. Chưa chọn ở đây thì bước 2 không phân công được cho họ." },
  { so: 2, ten: "Phân công dạy", huongDan: "Với mỗi giáo viên: chọn môn và khoảng ngày dạy. Môn Thực hành lái xe cần nhập ngày bắt đầu thực hành của khóa trước." },
  { so: 3, ten: "Xe và ghép xe", huongDan: "Chọn xe vào khóa, rồi ghép từng giáo viên thực hành với một xe theo khoảng ngày." },
];

const MUC: Record<MucVanDe, { nhan: string; lop: string }> = {
  chan: { nhan: "Chặn — phải sửa mới ghi được", lop: "border-l-destructive bg-destructive/5" },
  canh_bao: { nhan: "Cảnh báo — xem lại rồi xác nhận", lop: "border-l-warning bg-warning/5" },
  thong_tin: { nhan: "Thông tin", lop: "border-l-primary bg-primary/5" },
};

// Bản nháp tự giữ trên MÁY NÀY (localStorage) theo (CSDL đích, khóa) — chỉ để khỏi mất khi F5/đóng tab.
// KHÔNG ghi gì vào CDB. Chỉ khôi phục khi mốc "goc" còn khớp CDB hiện tại (CDB chưa bị đổi).
interface BanNhapLuu { goc: BanNhapPC; ban: BanNhapPC; luc: string }
const khoaLuu = (targetKey: string, maKh: string) => `pcg.nhap.${targetKey}.${maKh}`;
function docNhapLuu(targetKey: string, maKh: string): BanNhapLuu | null {
  try {
    const t = localStorage.getItem(khoaLuu(targetKey, maKh));
    return t ? (JSON.parse(t) as BanNhapLuu) : null;
  } catch { return null; }
}
function ghiNhapLuu(targetKey: string, maKh: string, v: BanNhapLuu | null) {
  try {
    if (v) localStorage.setItem(khoaLuu(targetKey, maKh), JSON.stringify(v));
    else localStorage.removeItem(khoaLuu(targetKey, maKh));
  } catch { /* trình duyệt chặn lưu → bỏ qua, vẫn dùng bình thường */ }
}

function banTuHienTrang(h: Omit<HienTrangPC, "khoa">): BanNhapPC {
  return {
    gv_khoa: h.gv_khoa.map((g) => g.ma),
    pc: h.pc.map((p) => ({ ...p })),
    xe_khoa: h.xe_khoa.map((x) => x.bs),
    ghep: h.ghep.map((g) => ({ ...g })),
  };
}

export default function PhanCongTheoKhoa() {
  const { open: openConfig } = useConfigDrawer();
  const [params, setParams] = useSearchParams();
  const [targetKey, setTargetKey] = useState<string | null>(null);
  const [targetLoi, setTargetLoi] = useState<string | null>(null);

  const [q, setQ] = useState("");
  const [dsKhoa, setDsKhoa] = useState<KhoaPC[]>([]);
  const [dsLoi, setDsLoi] = useState<string | null>(null);
  const [mo, setMo] = useState(false);

  const [maKh, setMaKh] = useState<string | null>(null);
  const [hien, setHien] = useState<HienTrangPC | null>(null);
  const [ban, setBan] = useState<BanNhapPC | null>(null);
  const [thStart, setThStart] = useState(""); // ngày bắt đầu thực hành của khóa — tự nhập, không gợi ý
  const [goc, setGoc] = useState<BanNhapPC | null>(null); // đúng như CDB lúc tải/ghi gần nhất
  const [khoiPhuc, setKhoiPhuc] = useState<BanNhapLuu | null>(null); // bản nháp cũ trên máy, chờ user chọn
  const [danhMuc, setDanhMuc] = useState<GiaoVienPC[]>([]);
  const [mon, setMon] = useState<MonPC[]>([]);
  const [xeDm, setXeDm] = useState<XePC[]>([]);
  const [loiTai, setLoiTai] = useState<string | null>(null);
  const [dangTai, setDangTai] = useState(false);

  const [buoc, setBuoc] = useState<1 | 2 | 3>(1);
  const [kt, setKt] = useState<KiemTraPC | null>(null);
  const [ktBusy, setKtBusy] = useState(false);
  const [ktLoi, setKtLoi] = useState<string | null>(null);
  const ktSeq = useRef(0);

  // Đích ghi = CSDL đích đã chọn ở ngăn Cấu hình (cùng cách các phân hệ Sync / KQĐT).
  useEffect(() => {
    getSyncTargets()
      .then((d) => {
        const t = d.targets.find((x) => x.key === d.selected) ?? d.targets[0];
        if (t) setTargetKey(t.key);
        else setTargetLoi("Chưa cấu hình CSDL đích. Mở Cấu hình để khai báo.");
      })
      .catch((e: Error) => setTargetLoi(e.message));
  }, []);

  // Gõ để tìm khóa (trễ 250ms).
  useEffect(() => {
    if (!targetKey) return;
    const h = setTimeout(() => {
      dsKhoaPC(q, targetKey)
        .then((d) => { setDsKhoa(d); setDsLoi(null); })
        .catch((e: Error) => setDsLoi(e.message));
    }, 250);
    return () => clearTimeout(h);
  }, [q, targetKey]);

  async function chonKhoa(k: KhoaPC) {
    if (!targetKey) return;
    setMo(false);
    setMaKh(k.ma_kh);
    setHien(null);
    setBan(null);
    setGoc(null);
    setKhoiPhuc(null);
    setThStart("");
    setKt(null);
    setBuoc(1);
    setLoiTai(null);
    setDangTai(true);
    try {
      const [h, gv, mh, xe] = await Promise.all([
        hienTrangPC(k.ma_kh, targetKey),
        dsGiaoVienPC(k.ma_kh, targetKey),
        dsMonPC(targetKey),
        dsXePC(k.ma_kh, targetKey),
      ]);
      setXeDm(xe.xe);
      setDanhMuc(gv.giao_vien);
      setMon(mh);
      setHien(h);
      const g0 = banTuHienTrang(h);
      setBan(banTuHienTrang(h));
      setGoc(g0);
      // Có bản nháp cũ trên máy và CDB chưa đổi kể từ lúc đó → hỏi khôi phục; CDB đã đổi → bỏ.
      const luu = docNhapLuu(targetKey, k.ma_kh);
      if (luu && JSON.stringify(luu.goc) === JSON.stringify(g0) && JSON.stringify(luu.ban) !== JSON.stringify(g0)) {
        setKhoiPhuc(luu);
      } else if (luu) {
        ghiNhapLuu(targetKey, k.ma_kh, null);
      }
      // Khóa đã có phân công Thực hành trong CDB → hiện ngày thật (sớm nhất); chưa có thì để trống.
      const dauTh = h.pc.filter((x) => x.mon.includes(6)).map((x) => x.tu.slice(0, 10)).sort()[0];
      setThStart(dauTh ?? "");
    } catch (e) {
      setLoiTai((e as Error).message);
    } finally {
      setDangTai(false);
    }
  }

  // Mở sẵn khóa từ liên kết (?khoa=<mã>) — dùng khi bấm một dòng ở tab "Rà soát khóa".
  const khoaTuLienKet = params.get("khoa");
  useEffect(() => {
    if (!targetKey || !khoaTuLienKet) return;
    let huy = false;
    dsKhoaPC(khoaTuLienKet, targetKey)
      .then((d) => {
        const k = d.find((x) => x.ma_kh === khoaTuLienKet);
        if (k && !huy) void chonKhoa(k);
      })
      .catch(() => {})
      .finally(() => { if (!huy) setParams({}, { replace: true }); });
    return () => { huy = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [targetKey, khoaTuLienKet]);

  // Tự giữ bản nháp trên máy mỗi khi khác CDB (chờ user chọn khôi phục/bỏ thì chưa ghi đè bản cũ).
  useEffect(() => {
    if (!targetKey || !maKh || !ban || !goc || khoiPhuc) return;
    if (JSON.stringify(ban) === JSON.stringify(goc)) ghiNhapLuu(targetKey, maKh, null);
    else ghiNhapLuu(targetKey, maKh, { goc, ban, luc: new Date().toISOString() });
  }, [ban, goc, maKh, targetKey, khoiPhuc]);

  // Kiểm tra sống: mỗi lần bản nháp đổi → hỏi server sau 250ms; bỏ kết quả trả về muộn.
  useEffect(() => {
    if (!targetKey || !maKh || !ban) return;
    const seq = ++ktSeq.current;
    setKtBusy(true);
    const h = setTimeout(() => {
      kiemTraPC(maKh, ban, targetKey)
        .then((r) => { if (seq === ktSeq.current) { setKt(r); setKtLoi(null); } })
        .catch((e: Error) => { if (seq === ktSeq.current) setKtLoi(e.message); })
        .finally(() => { if (seq === ktSeq.current) setKtBusy(false); });
    }, 250);
    return () => clearTimeout(h);
  }, [ban, maKh, targetKey]);

  const khoa = hien?.khoa ?? null;

  // Bấm một lỗi → sang đúng bước, cuộn tới dòng sai và nháy khung (ref: pc-<id> | gv-<ma> | gh-<ma> | xe-<bs>).
  function toiLoi(v: VanDePC) {
    if (v.buoc >= 1 && v.buoc <= 3) setBuoc(v.buoc as 1 | 2 | 3);
    if (!v.ref) return;
    setTimeout(() => {
      const el = document.getElementById(v.ref);
      if (!el) return;
      el.scrollIntoView({ block: "center", behavior: "smooth" });
      const cu = el.style.outline;
      el.style.outline = "3px solid hsl(330 62% 44%)";
      el.style.outlineOffset = "2px";
      setTimeout(() => { el.style.outline = cu; }, 1600);
    }, 80);
  }
  const loiBuoc = (kt?.vande ?? []).filter((v) => v.buoc === buoc);
  const nChanBuoc = loiBuoc.filter((v) => v.muc === "chan").length;
  const nCanhBaoBuoc = loiBuoc.filter((v) => v.muc === "canh_bao").length;
  const dauTien = loiBuoc.find((v) => v.muc === "chan") ?? loiBuoc.find((v) => v.muc === "canh_bao");

  function sauKhiGhi(r: GhiPCKetQua) {
    // Làm tươi bản nháp + mốc theo CDB sau khi ghi (cả khi lỗi giữa chừng — tránh ghi trùng dòng đã ghi).
    if (r.hien_trang) {
      setBan(banTuHienTrang(r.hien_trang));
      setGoc(banTuHienTrang(r.hien_trang));
    }
  }
  const nhom = useMemo(() => {
    const r: Record<MucVanDe, VanDePC[]> = { chan: [], canh_bao: [], thong_tin: [] };
    for (const v of kt?.vande ?? []) (r[v.muc] ?? r.thong_tin).push(v);
    return r;
  }, [kt]);

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* Thanh chọn khóa */}
      <div className="border-b border-border bg-card px-5 py-3 flex flex-wrap items-center gap-3">
        <div className="relative w-[340px] max-w-full">
          <label className="block text-[11px] font-medium text-muted-foreground mb-1">Khóa học</label>
          <button
            type="button"
            onClick={() => setMo((v) => !v)}
            disabled={!targetKey}
            className="w-full h-10 px-3 rounded-md border border-border bg-background text-left text-sm flex items-center justify-between gap-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pc disabled:opacity-50"
          >
            <span className={khoa ? "font-medium truncate" : "text-muted-foreground"}>
              {khoa ? `${khoa.ma_kh} · ${khoa.ten_kh}` : "Chọn khóa để phân công…"}
            </span>
            <Icon name="chevronDown" className="w-4 h-4 text-muted-foreground shrink-0" />
          </button>
          {mo && (
            <div className="absolute z-20 mt-1 w-full rounded-md border border-border bg-card shadow-lg">
              <div className="p-2 border-b border-border">
                <input
                  autoFocus
                  value={q}
                  onChange={(e) => setQ(e.target.value)}
                  placeholder="Gõ mã hoặc tên khóa…"
                  className="w-full h-9 px-3 rounded-md border border-border bg-background text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pc"
                />
              </div>
              <ul className="max-h-72 overflow-auto py-1">
                {dsLoi && <li className="px-3 py-2 text-[13px] text-destructive">{dsLoi}</li>}
                {!dsLoi && dsKhoa.length === 0 && <li className="px-3 py-2 text-[13px] text-muted-foreground">Không có khóa nào khớp.</li>}
                {dsKhoa.map((k) => (
                  <li key={k.ma_kh}>
                    <button type="button" onClick={() => chonKhoa(k)} className="w-full text-left px-3 py-2 hover:bg-pc-soft">
                      <div className="text-sm font-medium">{k.ma_kh} · {k.ten_kh}</div>
                      <div className="text-[12px] text-muted-foreground">
                        Hạng {k.hang_dt || k.hang_gplx || "—"} · {ymdToVN(k.kg)} → {ymdToVN(k.bg)} · {k.so_hv} học viên
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {khoa && (
          <div className="flex flex-wrap items-center gap-2 text-[12.5px] pt-5">
            <span className="px-2 py-1 rounded-md bg-pc-soft text-pc font-medium">Hạng {khoa.hang_dt || khoa.hang_gplx || "—"}</span>
            <span className="px-2 py-1 rounded-md bg-muted">Khai giảng {ymdToVN(khoa.kg)}</span>
            <span className="px-2 py-1 rounded-md bg-muted">Bế giảng {ymdToVN(khoa.bg)}</span>
            <span className="px-2 py-1 rounded-md bg-muted">{khoa.so_hv} học viên</span>
            {khoa.da_dkkh && (
              <span className="px-2 py-1 rounded-md bg-warning/10 text-warning font-medium" title="Khóa đã có gói đăng ký khóa học gửi Sở">
                Đã gửi đăng ký khóa học
              </span>
            )}
          </div>
        )}
      </div>

      {targetLoi && (
        <div className="m-5 rounded-md border border-warning/40 bg-warning/10 px-4 py-3 text-sm flex items-center justify-between gap-3">
          <span>{targetLoi}</span>
          <button onClick={() => openConfig()} className="h-8 px-3 rounded-md border border-border bg-card text-[13px] font-medium">Mở Cấu hình</button>
        </div>
      )}

      {!khoa && !dangTai && !loiTai && !targetLoi && (
        <div className="m-5 rounded-lg border border-dashed border-border bg-card px-6 py-10 text-center">
          <Icon name="calendar" className="w-8 h-8 mx-auto text-pc" />
          <p className="mt-3 text-sm font-medium">Chọn một khóa để bắt đầu phân công giáo viên và xe</p>
          <p className="mt-1 text-[13px] text-muted-foreground">
            Làm lần lượt 3 bước: giáo viên của khóa → phân công dạy → xe và ghép xe. Chỉ khi bấm “Ghi vào CDB” thì dữ liệu mới được lưu.
          </p>
        </div>
      )}

      {dangTai && (
        <div className="m-5 text-sm text-muted-foreground flex items-center gap-2">
          <Icon name="refresh" className="w-4 h-4 animate-spin" /> Đang đọc hiện trạng khóa…
        </div>
      )}
      {loiTai && <div className="m-5 rounded-md border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">{loiTai}</div>}

      {khoa && ban && (
        <div className="flex-1 min-h-0 flex">
          {/* Cột làm việc */}
          <div className="flex-1 min-w-0 overflow-auto p-5">
            {khoiPhuc && (
              <div className="mb-4 rounded-lg border-2 border-pc bg-pc-soft px-4 py-3 flex items-center gap-3 flex-wrap">
                <div className="text-[13.5px]">
                  <b>Có thay đổi chưa ghi vào CDB</b> được giữ lại trên máy này lúc{" "}
                  {new Date(khoiPhuc.luc).toLocaleString("vi-VN", { hour: "2-digit", minute: "2-digit", day: "2-digit", month: "2-digit", year: "numeric" })}.
                  Bạn muốn làm tiếp hay bỏ?
                </div>
                <div className="ml-auto flex gap-2">
                  <button
                    onClick={() => { setBan(khoiPhuc.ban); setKhoiPhuc(null); }}
                    className="h-9 px-3 rounded-lg bg-pc text-white text-[13px] font-semibold"
                  >
                    Làm tiếp
                  </button>
                  <button
                    onClick={() => { if (targetKey && maKh) ghiNhapLuu(targetKey, maKh, null); setKhoiPhuc(null); }}
                    className="h-9 px-3 rounded-lg border border-border bg-white text-[13px]"
                  >
                    Bỏ, dùng dữ liệu CDB
                  </button>
                </div>
              </div>
            )}
            <ol className="flex flex-wrap gap-2 mb-4">
              {BUOC.map((b) => {
                const dang = b.so === buoc;
                const soLoi = (kt?.vande ?? []).filter((v) => v.buoc === b.so && v.muc === "chan").length;
                return (
                  <li key={b.so}>
                    <button
                      type="button"
                      onClick={() => setBuoc(b.so)}
                      aria-current={dang ? "step" : undefined}
                      className={`h-10 pl-2 pr-3 rounded-full border text-sm font-medium inline-flex items-center gap-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-pc ${
                        dang ? "bg-pc text-white border-pc" : "bg-card border-border hover:bg-pc-soft"
                      }`}
                    >
                      <span className={`w-6 h-6 rounded-full inline-flex items-center justify-center text-[12px] ${dang ? "bg-white/20" : "bg-muted"}`}>{b.so}</span>
                      {b.ten}
                      {soLoi > 0 && <span className="ml-1 px-1.5 rounded-full bg-destructive text-white text-[11px]">{soLoi}</span>}
                    </button>
                  </li>
                );
              })}
            </ol>

            <div className="rounded-md border border-pc-border bg-pc-soft px-4 py-3 text-[13.5px] mb-4">
              <b>Bước {buoc}.</b> {BUOC[buoc - 1].huongDan}
              <div className="mt-1.5 text-[12.5px] text-muted-foreground">
                Cách làm: ① Chọn GV → ② Phân công → ③ Xe &amp; ghép xe → <b>Xem các thay đổi</b> → <b>Ghi vào CDB</b>.
                Mọi thao tác chỉ nằm trên màn hình, <b>CDB chỉ đổi khi bạn bấm “Ghi vào CDB”</b> và xác nhận.
              </div>
            </div>

            {dauTien && (
              <div
                role="status"
                className={
                  "mb-3 rounded-lg border-2 px-3.5 py-2.5 flex items-center gap-3 " +
                  (nChanBuoc ? "border-destructive bg-destructive/5" : "border-warning bg-warning/10")
                }
              >
                <span className={"text-[14px] font-bold " + (nChanBuoc ? "text-destructive" : "text-warning")}>
                  {nChanBuoc
                    ? `${nChanBuoc} lỗi chặn ở bước này — phải sửa mới ghi được`
                    : `${nCanhBaoBuoc} cảnh báo ở bước này — cần xem trước khi ghi`}
                </span>
                <button
                  onClick={() => toiLoi(dauTien)}
                  className={
                    "ml-auto h-9 px-3 rounded-lg border bg-white text-[13px] font-semibold " +
                    (nChanBuoc ? "border-destructive text-destructive" : "border-warning text-warning")
                  }
                >
                  Tới lỗi đầu tiên →
                </button>
              </div>
            )}

            {buoc === 1 ? (
              <BuocGiaoVien
                khoa={khoa}
                danhMuc={danhMuc}
                mon={mon}
                ban={ban}
                setBan={(f) => setBan((b) => (b ? f(b) : b))}
                vande={kt?.vande ?? []}
              />
            ) : buoc === 2 && targetKey ? (
              <BuocPhanCong
                khoa={khoa}
                danhMuc={danhMuc}
                mon={mon}
                ban={ban}
                setBan={(f) => setBan((b) => (b ? f(b) : b))}
                vande={kt?.vande ?? []}
                targetKey={targetKey}
                thStart={thStart}
                setThStart={setThStart}
              />
            ) : buoc === 3 && targetKey ? (
              <BuocXe
                khoa={khoa}
                danhMuc={danhMuc}
                xeDm={xeDm}
                ban={ban}
                setBan={(f) => setBan((b) => (b ? f(b) : b))}
                vande={kt?.vande ?? []}
                targetKey={targetKey}
              />
            ) : (
              <div className="rounded-lg border border-border bg-card p-5">
                <h2 className="text-base font-semibold">{BUOC[buoc - 1].ten}</h2>
                <dl className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                  <div><dt className="text-[12px] text-muted-foreground">Giáo viên của khóa</dt><dd className="text-lg font-semibold">{ban.gv_khoa.length}</dd></div>
                  <div><dt className="text-[12px] text-muted-foreground">Dòng phân công</dt><dd className="text-lg font-semibold">{ban.pc.length}</dd></div>
                  <div><dt className="text-[12px] text-muted-foreground">Xe của khóa</dt><dd className="text-lg font-semibold">{ban.xe_khoa.length}</dd></div>
                  <div><dt className="text-[12px] text-muted-foreground">Dòng ghép xe</dt><dd className="text-lg font-semibold">{ban.ghep.length}</dd></div>
                </dl>
                <p className="mt-4 text-[13px] text-muted-foreground">
                  Thao tác nhập của bước này được dựng ở các task kế tiếp; hiện trang chỉ đọc hiện trạng khóa và kiểm tra theo luật CDB.
                </p>
              </div>
            )}
          </div>

          {/* Cột Kiểm tra khóa */}
          <aside className="w-[340px] shrink-0 border-l border-border bg-card overflow-auto p-4" aria-label="Kiểm tra khóa">
            <div className="flex items-center justify-between">
              <h2 className="text-[15px] font-semibold">Kiểm tra khóa</h2>
              {ktBusy && <Icon name="refresh" className="w-4 h-4 animate-spin text-muted-foreground" />}
            </div>
            {ktLoi && <p className="mt-2 text-[13px] text-destructive">{ktLoi}</p>}
            {kt && kt.vande.length === 0 && (
              <p className="mt-2 text-[13px] text-success flex items-center gap-1.5">
                <Icon name="check" className="w-4 h-4" /> Không có lỗi hay cảnh báo.
              </p>
            )}
            {(["chan", "canh_bao", "thong_tin"] as MucVanDe[]).map((m) =>
              nhom[m].length === 0 ? null : (
                <section key={m} className="mt-4">
                  <h3 className="text-[12.5px] font-semibold uppercase tracking-wide text-muted-foreground">
                    {MUC[m].nhan} ({nhom[m].length})
                  </h3>
                  <ul className="mt-2 space-y-2">
                    {nhom[m].map((v, i) => (
                      <li key={`${v.ma}-${v.ref}-${i}`}>
                        <button
                          type="button"
                          onClick={() => toiLoi(v)}
                          className={`w-full text-left rounded-md border-l-4 px-3 py-2 text-[13px] leading-snug ${MUC[m].lop}`}
                        >
                          <span className="text-foreground">{v.noi_dung}</span>
                          {v.ai && <span className="block text-[12px] text-muted-foreground mt-0.5">{v.ai} · bước {v.buoc}</span>}
                        </button>
                      </li>
                    ))}
                  </ul>
                </section>
              ),
            )}
          </aside>
        </div>
      )}

      {khoa && ban && goc && targetKey && (
        <GhiBanNhap
          khoa={khoa}
          goc={goc}
          ban={ban}
          canhBao={nhom.canh_bao}
          coChan={!kt || kt.co_chan}
          dangKiem={ktBusy}
          targetKey={targetKey}
          onHuy={() => { setBan({ ...goc, pc: goc.pc.map((p) => ({ ...p })), ghep: goc.ghep.map((g) => ({ ...g })) }); }}
          onDaGhi={sauKhiGhi}
          tenGv={(ma) => danhMuc.find((g) => g.ma === ma)?.ten ?? ma}
          tenMon={(ids) => ids.map((i) => mon.find((m) => m.id === i)?.ten ?? `môn ${i}`).join(" + ") || "chưa chọn môn"}
        />
      )}
    </div>
  );
}
