import { useEffect, useRef, useState } from "react";
import HopGhiTotNghiep from "./HopGhiTotNghiep";
import PanelCuuTrangThai from "./PanelCuuTrangThai";
import {
  dsHvTotNghiep,
  timHvCuu,
  type ChungTn,
  type HvCuu,
  type HvTnResp,
  type HvUngVien,
  type LoaiHang,
} from "../../lib/tnbc2Api";
import MaTT from "../MaTT";

// TNB-04 — xử lý ngoại lệ ngay ở bước ②, khỏi rời wizard: (a) "Cập nhật tốt nghiệp" = mini-form số giấy + bộ sổ chung →
// dùng lại hộp Xem lại & ghi của TNB-01; (b) "Cứu trạng thái" = dùng lại panel của TNB-06. Xong thì báo `onXong` để
// bước ② làm tươi danh sách và tích sẵn học viên vừa xử lý.

const CHUNG_TRONG: ChungTn = { so_so_tn: "", ngay_vao_so: "", so_quyet_dinh: "", ngay_ra_qd: "", ngay_in: "" };
const NUT_PHU = "h-9 px-4 rounded-lg border border-input text-[13px] font-semibold hover:bg-muted";

export function CapNhatTotNghiepTaiCho({
  maKh,
  hv,
  onDong,
  onXong,
}: {
  maKh: string;
  hv: HvUngVien;
  onDong: () => void;
  onXong: (maDk: string) => void;
}) {
  const [data, setData] = useState<HvTnResp | null>(null);
  const [loi, setLoi] = useState<string | null>(null);
  const [soGiay, setSoGiay] = useState("");
  const [chung, setChung] = useState<ChungTn>(CHUNG_TRONG);
  const [ghi, setGhi] = useState(false);
  const [coSoRieng, setCoSoRieng] = useState(false);
  const daDien = useRef(false);

  useEffect(() => {
    let huy = false;
    dsHvTotNghiep(maKh, hv.cmt || hv.ten)
      .then((d) => {
        if (huy || daDien.current) return;
        daDien.current = true;
        setData(d);
        setSoGiay(hv.so_giay || d.so_giay_ke_tiep);
        // Ưu tiên sổ/quyết định riêng của học viên (đã lưu trước); thiếu ô nào mới lấy bộ phổ biến của khóa — tránh đè sổ riêng.
        const rieng = d.hoc_vien.find((x) => x.ma_dk === hv.ma_dk);
        const k = d.so_chung;
        const lay = (r: string | undefined, c: string | undefined) => r || c || "";
        const moi: ChungTn = {
          so_so_tn: lay(rieng?.so_so_tn, k?.so_so_tn),
          ngay_vao_so: lay(rieng?.ngay_vao_so?.slice(0, 10), k?.ngay_vao_so),
          so_quyet_dinh: lay(rieng?.so_quyet_dinh, k?.so_quyet_dinh),
          ngay_ra_qd: lay(rieng?.ngay_ra_qd?.slice(0, 10), k?.ngay_ra_qd),
          ngay_in: lay(rieng?.ngay_in?.slice(0, 10), k?.ngay_in),
        };
        setChung(moi);
        setCoSoRieng(!!(rieng && (rieng.so_so_tn || rieng.so_quyet_dinh)));
      })
      .catch((e: unknown) => { if (!huy) setLoi(e instanceof Error ? e.message : "Không tải được thông tin sổ của khóa"); });
    return () => { huy = true; };
  }, [maKh, hv.cmt, hv.ten, hv.so_giay]);

  const setC = (k: keyof ChungTn, v: string) => setChung((c) => ({ ...c, [k]: v }));
  const du = soGiay.trim() !== "" && chung.so_so_tn.trim() !== "" && chung.so_quyet_dinh.trim() !== "";

  if (ghi) {
    return (
      <HopGhiTotNghiep
        maKh={maKh}
        dong={[{ ma_dk: hv.ma_dk, so_giay: soGiay.trim() }]}
        chung={chung}
        tenHv={{ [hv.ma_dk]: hv.ten }}
        onDong={() => setGhi(false)}
        onXong={() => onXong(hv.ma_dk)}
      />
    );
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/40 grid place-items-center p-4">
      <div role="dialog" aria-modal="true" aria-label="Cập nhật tốt nghiệp tại chỗ"
        className="bg-white rounded-xl shadow-2xl w-[560px] max-w-full max-h-[90vh] flex flex-col">
        <div className="p-4 border-b border-border font-semibold">Cập nhật tốt nghiệp — {hv.ten}</div>
        <div className="p-4 overflow-auto space-y-3 text-[13px]">
          <div className="rounded-lg border border-border p-3">
            <b>{hv.ten}</b>
            <div className="font-mono text-[12px] text-muted-foreground">{hv.cmt} · {hv.ten_kh}</div>
            <div className="mt-1">Hiện tại: {hv.ten_trang_thai} <MaTT ma={hv.tt} /></div>
          </div>
          {loi && <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-destructive">{loi}</div>}
          {!data && !loi && <div className="text-muted-foreground">Đang tải số giấy gợi ý và bộ sổ của khóa…</div>}
          {data && (
            <>
              <div>
                <label className="field-label" htmlFor="nl-so-giay">Số giấy chứng nhận</label>
                <input id="nl-so-giay" className="field-input font-mono" value={soGiay} onChange={(e) => setSoGiay(e.target.value)} />
                <div className="text-[11.5px] text-muted-foreground mt-0.5">Gợi ý: số kế tiếp của khóa. Hộp xem lại sẽ kiểm trùng trước khi ghi.</div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="field-label" htmlFor="nl-so-so">Số sổ</label>
                  <input id="nl-so-so" className="field-input" value={chung.so_so_tn} onChange={(e) => setC("so_so_tn", e.target.value)} />
                </div>
                <div>
                  <label className="field-label" htmlFor="nl-ngay-so">Ngày vào sổ</label>
                  <input id="nl-ngay-so" type="date" className="field-input" value={chung.ngay_vao_so} onChange={(e) => setC("ngay_vao_so", e.target.value)} />
                </div>
                <div>
                  <label className="field-label" htmlFor="nl-qd">Số quyết định</label>
                  <input id="nl-qd" className="field-input" value={chung.so_quyet_dinh} onChange={(e) => setC("so_quyet_dinh", e.target.value)} />
                </div>
                <div>
                  <label className="field-label" htmlFor="nl-ngay-qd">Ngày ra quyết định</label>
                  <input id="nl-ngay-qd" type="date" className="field-input" value={chung.ngay_ra_qd} onChange={(e) => setC("ngay_ra_qd", e.target.value)} />
                </div>
                <div>
                  <label className="field-label" htmlFor="nl-ngay-in">Ngày in</label>
                  <input id="nl-ngay-in" type="date" className="field-input" value={chung.ngay_in} onChange={(e) => setC("ngay_in", e.target.value)} />
                </div>
              </div>
              {coSoRieng && (
                <div className="rounded-lg border border-warning/40 bg-warning/10 px-3 py-2 text-[12.5px] text-warning">
                  Học viên này đã có sổ/quyết định riêng — đang điền sẵn đúng giá trị đó, không lấy bộ phổ biến của khóa.
                  Sửa chỉ khi chắc chắn.
                </div>
              )}
              <div className="text-[12px] text-muted-foreground">
                {data.so_chung
                  ? `Bộ sổ điền sẵn từ ${data.so_chung.so_hv} học viên cùng khóa đã có sổ — sửa được.`
                  : "Khóa này chưa có học viên nào có sổ — nhập số sổ và số quyết định."}
              </div>
            </>
          )}
        </div>
        <div className="p-3 border-t border-border flex justify-end gap-2">
          <button type="button" onClick={onDong} className={NUT_PHU}>Hủy</button>
          <button type="button" disabled={!data || !du} onClick={() => setGhi(true)}
            className="h-9 px-4 rounded-lg bg-tn text-white text-[13px] font-semibold disabled:opacity-45 disabled:cursor-not-allowed">
            Xem lại & ghi
          </button>
        </div>
      </div>
    </div>
  );
}

export function CuuTrangThaiTaiCho({
  hv,
  loai,
  onDong,
  onXong,
}: {
  hv: HvUngVien;
  loai: LoaiHang;
  onDong: () => void;
  /** Đã chuyển hoặc hoàn tác ít nhất một lần khi đóng panel. */
  onXong: (maDk: string) => void;
}) {
  const [cuu, setCuu] = useState<HvCuu | null>(null);
  const [loi, setLoi] = useState<string | null>(null);
  const daDoi = useRef(false);

  useEffect(() => {
    let huy = false;
    timHvCuu(hv.cmt || hv.ma_dk, loai)
      .then((r) => {
        if (huy) return;
        const x = r.hoc_vien.find((c) => c.ma_dk === hv.ma_dk);
        if (x) setCuu(x);
        else setLoi("Không tìm thấy học viên này ở chức năng cứu trạng thái — mở tab \"Học viên không tìm thấy\" để tra.");
      })
      .catch((e: unknown) => { if (!huy) setLoi(e instanceof Error ? e.message : "Không tải được thông tin học viên"); });
    return () => { huy = true; };
  }, [hv.cmt, hv.ma_dk, loai]);

  const dong = () => (daDoi.current ? onXong(hv.ma_dk) : onDong());

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex justify-end">
      {cuu ? (
        <PanelCuuTrangThai hv={cuu} loai={loai} onDong={dong} onDaDoi={() => { daDoi.current = true; }} />
      ) : (
        <aside className="w-[380px] bg-card p-4 space-y-3 text-[13px]" aria-label="Chuyển trạng thái học viên">
          {loi ? (
            <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-destructive">{loi}</div>
          ) : (
            <div className="text-muted-foreground">Đang tải…</div>
          )}
          <button type="button" onClick={onDong} className={NUT_PHU}>Đóng</button>
        </aside>
      )}
    </div>
  );
}
