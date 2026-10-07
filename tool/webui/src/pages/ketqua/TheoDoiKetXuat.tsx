import { useEffect, useMemo, useState } from "react";
import { Icon } from "../../components/Icon";
import { useConfigDrawer } from "../../lib/configDrawer";
import MoKhoaModal, { type MoKhoaKetQuaUI } from "./MoKhoaModal";
import {
  getSyncTargets,
  dsKhoaKQD,
  dsHocVienKQD,
  moKhoaTrangThai,
  type KhoaKQD,
  type HocVienKQD,
  type MoKhoaTrangThai,
} from "../../lib/api";

// KQD-03 (task 74) — Theo dõi kết xuất, CHỈ XEM, master–detail theo KHÓA (bám ui-mock/theodoiketxuat.html).
// Trái: danh sách khóa (đã BC1) + tiến độ "đã kết xuất / còn sót" + lọc "Còn sót kết xuất".
// Phải: tiến độ theo trạng thái + panel gói hàng đợi của CƠ SỞ + lưới HV lọc Đã kết xuất / Còn sót.
// KHÔNG nút kết xuất (việc đó thuộc phần mềm CDB cũ). Nút "Mở khóa để sửa" (KQD-05) thêm ở task 77.
// Gói lọc theo NoiGui=<mã CSĐT>, KHÔNG nối được HV↔gói (DB không lưu) — chỉ đối chiếu bằng trạng thái.

// "Còn sót kết xuất" (đã cập nhật chưa kết xuất) = số HV 09/10 của khóa.
const conSot = (k: KhoaKQD) => k.dem.capnhat;
const coKetQua = (k: KhoaKQD) => k.dem.ketxuat + k.dem.capnhat + k.dem.tuchoi + k.dem.giaitrinh > 0;

const TT_BADGE: Record<string, [string, string]> = {
  "09": ["Đã cập nhật · Đạt", "text-success bg-success/10 border-success/40"],
  "10": ["Đã cập nhật · Không đạt", "text-destructive bg-destructive/10 border-destructive/40"],
  "12": ["Đã kết xuất gửi Sở", "text-kq bg-kq-soft border-kq-border"],
};
function ttBadge(tt: string | null) {
  const [lbl, cls] = TT_BADGE[tt ?? ""] ?? [tt ?? "—", "text-muted-foreground bg-muted border-border"];
  return <span className={"inline-block text-[11px] font-semibold border rounded-full px-2 py-0.5 whitespace-nowrap " + cls}>{lbl}</span>;
}

type HvLoc = "ketxuat" | "capnhat";

export default function TheoDoiKetXuat() {
  const { open: moCauHinh } = useConfigDrawer();
  const [targetKey, setTargetKey] = useState<string | null>(null);
  const [chuaChonDich, setChuaChonDich] = useState(false);

  const [khoaList, setKhoaList] = useState<KhoaKQD[] | null>(null);
  const [loadingKhoa, setLoadingKhoa] = useState(false);
  const [khoaFilter, setKhoaFilter] = useState<"all" | "sot">("all");
  const [khoa, setKhoa] = useState<KhoaKQD | null>(null);

  const [goi, setGoi] = useState<MoKhoaTrangThai | null>(null); // gói CSĐT-wide, tải 1 lần
  const [goiErr, setGoiErr] = useState(false); // lỗi riêng khi tải panel gói (không chặn tab, nhưng phải báo)
  const [hvLoc, setHvLoc] = useState<HvLoc>("ketxuat");
  const [hoSo, setHoSo] = useState<HocVienKQD[] | null>(null);
  const [loadingHv, setLoadingHv] = useState(false);
  const [err, setErr] = useState("");
  const [moKhoaMo, setMoKhoaMo] = useState(false); // KQD-05: modal mở khóa (lối từ tab này)
  const [toast, setToast] = useState("");

  // Chọn CSDL đích (như CapNhatKQDT)
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

  // Tải danh sách khóa + gói hàng đợi của cơ sở khi có đích
  useEffect(() => {
    if (!targetKey) return;
    let huy = false;
    setLoadingKhoa(true);
    dsKhoaKQD("", targetKey)
      .then((ks) => { if (!huy) setKhoaList(ks); })
      .catch((e) => { if (!huy) setErr(e instanceof Error ? e.message : "Không tải được danh sách khóa."); })
      .finally(() => { if (!huy) setLoadingKhoa(false); });
    setGoiErr(false);
    moKhoaTrangThai(targetKey)
      .then((g) => { if (!huy) setGoi(g); })
      .catch(() => { if (!huy) setGoiErr(true); }); // không chặn tab, nhưng báo ở panel gói
    return () => { huy = true; };
  }, [targetKey]);

  function chonKhoa(k: KhoaKQD) {
    setKhoa(k); setHvLoc("ketxuat"); setHoSo(null); setErr("");
    void taiHv(k, "ketxuat");
  }
  function chonHvLoc(l: HvLoc) { setHvLoc(l); if (khoa) void taiHv(khoa, l); }

  async function taiHv(k: KhoaKQD, l: HvLoc) {
    setLoadingHv(true); setHoSo(null);
    try {
      setHoSo(await dsHocVienKQD(k.ma_kh, l, targetKey ?? undefined));
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Không tải được danh sách học viên.");
    } finally { setLoadingHv(false); }
  }

  // KQD-05: sau khi mở khóa (CSĐT-wide) → làm tươi đếm khóa + gói + lưới HV đang xem.
  function sauMoKhoa(r: MoKhoaKetQuaUI) {
    setMoKhoaMo(false);
    setToast(`Đã mở khóa ${r.so_hv_mo} học viên (${r.so_khoa} khóa) + xóa ${r.so_goi_xoa} gói chưa gửi${r.so_hv_bo_qua > 0 ? ` · bỏ qua ${r.so_hv_bo_qua} HV chưa có kết luận` : ""}. Sửa điểm ở tab "Cập nhật KQĐT" rồi kết xuất lại ở phần mềm CDB.`);
    if (targetKey) {
      dsKhoaKQD("", targetKey).then(setKhoaList).catch(() => {});
      setGoiErr(false);
      moKhoaTrangThai(targetKey).then(setGoi).catch(() => setGoiErr(true));
    }
    if (khoa) void taiHv(khoa, hvLoc);
  }

  const dsHienThi = useMemo(() => {
    if (!khoaList) return [];
    return khoaFilter === "sot" ? khoaList.filter((k) => conSot(k) > 0) : khoaList;
  }, [khoaList, khoaFilter]);

  const soKhoaCoKetQua = useMemo(() => (khoaList ?? []).filter(coKetQua).length, [khoaList]);

  if (chuaChonDich) {
    return (
      <div className="p-6">
        <div className="max-w-xl rounded-lg border border-warning/40 bg-warning/5 p-4 text-[13px]">
          <div className="font-semibold mb-1 flex items-center gap-2 text-warning"><Icon name="warn" className="w-4 h-4" /> Chưa chọn CSDL đích</div>
          <p className="text-muted-foreground mb-3">Chọn CSDL đích trong Cấu hình để theo dõi kết xuất.</p>
          <button onClick={moCauHinh} className="inline-flex items-center gap-1.5 h-8 px-3 rounded-md bg-kq text-white text-[13px] font-medium hover:brightness-110"><Icon name="settings" className="w-4 h-4" /> Mở Cấu hình</button>
        </div>
      </div>
    );
  }

  const goiChua = goi?.goi_chua_gui ?? [];
  const goiDa = goi?.goi_da_gui ?? [];

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="shrink-0 bg-card border-b border-border px-4 pt-3 pb-2.5 flex items-center gap-2 flex-wrap">
        <h1 className="text-[14px] font-bold">Theo dõi kết xuất</h1>
        <span className="text-[10px] font-semibold text-kq bg-kq-soft border border-kq-border rounded-full px-1.5 py-px">KQD-03 · chỉ xem</span>
        <span className="text-[12px] text-muted-foreground">Kết xuất/gửi Sở do phần mềm CDB cũ lo — tab này chỉ theo dõi.</span>
        <div className="ml-auto flex items-center gap-3 text-[12px] text-muted-foreground tabular-nums">
          <span>Khóa có kết quả: <b className="text-foreground">{soKhoaCoKetQua}</b></span>
          <span>Gói chờ gửi: <b className={goiChua.length > 0 ? "text-warning" : "text-foreground"}>{goiChua.length}</b></span>
        </div>
      </div>

      {toast && (
        <div className="shrink-0 px-4 py-1.5 bg-kq-soft border-b border-kq-border text-[12.5px] text-kq flex items-start gap-2">
          <Icon name="check" className="w-4 h-4 mt-0.5 shrink-0" sw={3} /> <span>{toast}</span>
          <button onClick={() => setToast("")} className="ml-auto shrink-0 text-muted-foreground hover:text-foreground"><Icon name="x" className="w-3.5 h-3.5" /></button>
        </div>
      )}

      <div className="flex-1 min-h-0 flex">
        {/* Trái: danh sách khóa */}
        <div className="w-72 shrink-0 border-r border-border flex flex-col bg-muted/20">
          <div className="shrink-0 px-3 py-2 border-b border-border flex items-center gap-1.5 flex-wrap">
            <button onClick={() => setKhoaFilter("all")} className={"px-2 py-0.5 rounded-full text-[12px] border " + (khoaFilter === "all" ? "bg-kq text-white border-kq" : "border-border hover:bg-muted")}>Tất cả khóa</button>
            <button onClick={() => setKhoaFilter("sot")} className={"px-2 py-0.5 rounded-full text-[12px] border " + (khoaFilter === "sot" ? "bg-kq text-white border-kq" : "border-border hover:bg-muted")}>Còn sót kết xuất</button>
          </div>
          <div className="flex-1 overflow-auto p-2 space-y-1.5">
            {loadingKhoa && <div className="px-2 py-4 text-[13px] text-muted-foreground inline-flex items-center gap-2"><Icon name="refresh" className="w-4 h-4 animate-spin" /> Đang tải khóa…</div>}
            {!loadingKhoa && dsHienThi.length === 0 && (
              <div className="px-2 py-6 text-center text-[12.5px] text-muted-foreground">{khoaFilter === "sot" ? "Không khóa nào còn sót kết xuất." : "Chưa có khóa (chỉ hiện khóa đã BC1)."}</div>
            )}
            {dsHienThi.map((k) => {
              const chon = khoa?.ma_kh === k.ma_kh;
              return (
                <button key={k.ma_kh} onClick={() => chonKhoa(k)} className={"w-full text-left rounded-lg border px-2.5 py-2 transition-colors " + (chon ? "border-kq bg-kq-soft" : "border-border bg-card hover:bg-muted/60")}>
                  <div className="text-[12.5px] font-medium truncate" title={k.ten_kh}>{k.ten_kh}</div>
                  <div className="text-[11px] text-muted-foreground tabular-nums">{k.ma_kh} · hạng {k.hang_gplx} · KG {k.ngay_kg ?? "—"}</div>
                  <div className="mt-1 flex items-center gap-2 text-[11px] tabular-nums">
                    <span className="text-kq">Đã kết xuất {k.dem.ketxuat}</span>
                    <span className={conSot(k) > 0 ? "text-warning" : "text-muted-foreground"}>Còn sót {conSot(k)}</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Phải: chi tiết khóa */}
        <div className="flex-1 min-w-0 overflow-auto p-4">
          {err && <div className="mb-3 text-[13px] text-destructive">{err}</div>}
          {!khoa ? (
            <div className="text-[13px] text-muted-foreground max-w-xl rounded-lg border border-dashed border-border bg-card p-8 text-center">Chọn một khóa bên trái để xem tiến độ kết xuất.</div>
          ) : (
            <div className="space-y-4">
              <div>
                <div className="text-[14px] font-bold">{khoa.ten_kh}</div>
                <div className="text-[12px] text-muted-foreground tabular-nums">{khoa.ma_kh} · hạng {khoa.hang_gplx} · khai giảng {khoa.ngay_kg ?? "—"}</div>
              </div>

              {/* Tiến độ theo trạng thái */}
              <div className="rounded-lg border border-border bg-card p-3">
                <div className="text-[12px] font-bold text-kq mb-2">Tiến độ kết xuất KQĐT</div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1 text-[12.5px]">
                  <div className="flex items-center justify-between"><span>Đã kết xuất <span className="text-muted-foreground">(chờ Sở · 12)</span></span><b className="tabular-nums text-kq">{khoa.dem.ketxuat}</b></div>
                  <div className="flex items-center justify-between"><span>Còn sót <span className="text-muted-foreground">(đã cập nhật · 09/10)</span></span><b className={"tabular-nums " + (conSot(khoa) > 0 ? "text-warning" : "")}>{conSot(khoa)}</b></div>
                  <div className="flex items-center justify-between"><span>Chưa có điểm <span className="text-muted-foreground">(03/04)</span></span><b className="tabular-nums text-muted-foreground">{khoa.dem.dangky}</b></div>
                  <div className="flex items-center justify-between"><span>Sở từ chối <span className="text-muted-foreground">(14)</span></span><b className="tabular-nums">{khoa.dem.tuchoi}</b></div>
                  <div className="flex items-center justify-between"><span>Đang giải trình <span className="text-muted-foreground">(90)</span></span><b className="tabular-nums">{khoa.dem.giaitrinh}</b></div>
                </div>
              </div>

              {/* Panel gói hàng đợi của CƠ SỞ */}
              <div className="rounded-lg border border-border bg-card p-3">
                <div className="flex items-center gap-1.5 text-[12px] font-bold text-kq mb-1"><Icon name="send" className="w-4 h-4" /> Gói kết xuất của cơ sở (hàng đợi gửi Sở)</div>
                <p className="text-[11.5px] text-muted-foreground mb-2">Gói chung của <b>cả cơ sở</b> (không tách theo khóa) — hệ thống <b>không tra được học viên nào nằm trong từng gói</b> (danh sách HV ở trong file nén, không lưu trong CSDL). Chỉ đối chiếu HV bằng cột trạng thái.</p>
                {goiErr ? (
                  <div className="px-3 py-5 text-center text-[12.5px] text-warning">Không tải được danh sách gói — kiểm kết nối CSDL đích rồi chọn lại khóa.</div>
                ) : goiChua.length === 0 && goiDa.length === 0 ? (
                  <div className="px-3 py-5 text-center text-[12.5px] text-muted-foreground">Cơ sở chưa có gói kết xuất KQĐT.</div>
                ) : (
                  <div className="space-y-1.5">
                    {goiChua.map((g) => (
                      <div key={g.id} className="flex items-center gap-2 text-[12px] rounded-md border border-warning/40 bg-warning/10 px-2.5 py-1.5">
                        <Icon name="file" className="w-4 h-4 text-warning shrink-0" />
                        <span className="truncate" title={g.ten_file}>{g.ten_file}</span>
                        <span className="ml-auto shrink-0 text-muted-foreground tabular-nums">{g.ngay_tao ?? "—"}</span>
                        <span className="shrink-0 text-[11px] font-semibold text-warning border border-warning/40 rounded-full px-2 py-0.5">Chưa gửi</span>
                      </div>
                    ))}
                    {goiDa.map((g) => (
                      <div key={g.id} className="flex items-center gap-2 text-[12px] rounded-md border border-border bg-muted/40 px-2.5 py-1.5">
                        <Icon name="file" className="w-4 h-4 text-success shrink-0" />
                        <span className="truncate" title={g.ten_file}>{g.ten_file}</span>
                        <span className="ml-auto shrink-0 text-muted-foreground tabular-nums">{g.ngay_tao ?? "—"}</span>
                        <span className="shrink-0 text-[11px] font-semibold text-success border border-success/40 rounded-full px-2 py-0.5">Đã gửi</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Lưới HV */}
              <div className="rounded-lg border border-border bg-card">
                <div className="flex items-center gap-1.5 px-3 py-2 border-b border-border flex-wrap">
                  <span className="text-[12px] text-muted-foreground mr-1">Học viên:</span>
                  <button onClick={() => chonHvLoc("ketxuat")} className={"px-2.5 py-0.5 rounded-full text-[12px] border " + (hvLoc === "ketxuat" ? "bg-kq text-white border-kq" : "border-border hover:bg-muted")}>Đã kết xuất ({khoa.dem.ketxuat})</button>
                  <button onClick={() => chonHvLoc("capnhat")} className={"px-2.5 py-0.5 rounded-full text-[12px] border " + (hvLoc === "capnhat" ? "bg-kq text-white border-kq" : "border-border hover:bg-muted")}>Còn sót ({conSot(khoa)})</button>
                  {khoa.dem.ketxuat > 0 && (
                    <button onClick={() => setMoKhoaMo(true)} className="ml-auto inline-flex items-center gap-1.5 h-7 px-2.5 rounded-md border border-kq/50 text-kq text-[12px] font-medium hover:bg-kq-soft" title="Mở khóa để sửa điểm HV đã kết xuất (thao tác toàn cơ sở)">
                      <Icon name="clock" className="w-3.5 h-3.5" /> Mở khóa để sửa
                    </button>
                  )}
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-[12.5px]">
                    <thead className="text-muted-foreground border-b border-border">
                      <tr className="text-left">
                        <th className="font-semibold px-3 py-1.5">Số HS</th>
                        <th className="font-semibold px-2 py-1.5">Họ tên</th>
                        <th className="font-semibold px-2 py-1.5">CCCD</th>
                        <th className="font-semibold px-2 py-1.5">Hạng</th>
                        <th className="font-semibold px-2 py-1.5 text-center">Trạng thái</th>
                      </tr>
                    </thead>
                    <tbody>
                      {loadingHv && (
                        <tr><td colSpan={5} className="px-3 py-8 text-center text-muted-foreground"><Icon name="refresh" className="w-4 h-4 animate-spin inline" /> Đang tải…</td></tr>
                      )}
                      {!loadingHv && hoSo && hoSo.length === 0 && (
                        <tr><td colSpan={5} className="px-3 py-8 text-center text-muted-foreground text-[13px]">{hvLoc === "ketxuat" ? "Khóa này chưa có học viên đã kết xuất." : "Khóa này không còn học viên nào chờ kết xuất."}</td></tr>
                      )}
                      {!loadingHv && hoSo?.map((h) => (
                        <tr key={h.ma_dk} className="border-b border-border/60 last:border-0">
                          <td className="px-3 py-2 tabular-nums">{h.so_ho_so}</td>
                          <td className="px-2 py-2 font-medium truncate max-w-[220px]" title={h.ho_ten}>{h.ho_ten}<div className="text-[11px] text-muted-foreground tabular-nums font-normal">{h.ngay_sinh}</div></td>
                          <td className="px-2 py-2 tabular-nums">{h.so_cccd}</td>
                          <td className="px-2 py-2">{h.hang ?? "—"}</td>
                          <td className="px-2 py-2 text-center">{ttBadge(h.tt_xuly)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {moKhoaMo && (
        <MoKhoaModal targetKey={targetKey ?? undefined} maKh={khoa?.ma_kh ?? null} onClose={() => setMoKhoaMo(false)} onDone={sauMoKhoa} />
      )}
    </div>
  );
}
