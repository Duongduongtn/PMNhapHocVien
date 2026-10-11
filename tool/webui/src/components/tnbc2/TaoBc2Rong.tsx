import { useRef, useState } from "react";
import FormBc2, { type GiaTriFormBc2 } from "./FormBc2";
import { BuocChonKhoa } from "./WizardBc2";
import { LoiTnbc2, taoBc2, type LoaiHang, type TaoBc2Resp } from "../../lib/tnbc2Api";

// TNB-03 — "Tạo BC2 rỗng" (không kèm học viên): chọn khóa → form → Xem lại → Tạo BC2 → (thêm học viên vào BC2 này).
// Trong luồng 3 bước của TNB-04 việc tạo + thêm HV gộp một lần xác nhận (task 112).

type Pha = "khoa" | "form" | "xong";

export default function TaoBc2Rong({
  loai,
  onVe,
  onThemHocVien,
}: {
  loai: LoaiHang;
  onVe: () => void;
  onThemHocVien: (maKh: string, tenKh: string, maBc2: string) => void;
}) {
  const [pha, setPha] = useState<Pha>("khoa");
  const [khoa, setKhoa] = useState<{ ma_kh: string; ten_kh: string } | null>(null);
  const [gt, setGt] = useState<GiaTriFormBc2 | null>(null);
  const [xemLai, setXemLai] = useState(false);
  const [daXemCanhBao, setDaXemCanhBao] = useState(false);
  const [xacNhanThat, setXacNhanThat] = useState(false);
  const [dang, setDang] = useState(false);
  const [loi, setLoi] = useState<string | null>(null);
  const [matKetNoi, setMatKetNoi] = useState(false);
  const [kq, setKq] = useState<TaoBc2Resp | null>(null);
  const [canhBaoServer, setCanhBaoServer] = useState("");
  // Khóa của lần "chưa biết đã tạo chưa" — `thu_lai` chỉ áp cho ĐÚNG khóa + số đó, đổi số/khóa thì reset.
  const daThu = useRef("");

  async function tao() {
    if (!khoa || !gt) return;
    const khoaThu = `${khoa.ma_kh}|${gt.so_bao_cao}`;
    setDang(true);
    setLoi(null);
    try {
      const r = await taoBc2({
        ma_kh: khoa.ma_kh,
        so_bao_cao: gt.so_bao_cao,
        ngay_bao_cao: gt.ngay_bao_cao,
        ghi_chu: gt.ghi_chu,
        da_xem_canh_bao: daXemCanhBao,
        thu_lai: daThu.current === khoaThu,
      });
      setKq(r);
      setXemLai(false);
      setPha("xong");
    } catch (e) {
      const khongBiet = !(e instanceof LoiTnbc2) || e.http >= 500 || e.ma === "loi_he_thong";
      if (khongBiet) {
        // không biết lần trước đã tạo chưa (mất kết nối / lỗi máy chủ): lần gửi lại mang `thu_lai` để không tạo đôi
        daThu.current = khoaThu;
        setMatKetNoi(true);
        setLoi("Chưa biết BC2 đã được tạo hay chưa (mất kết nối hoặc lỗi giữa chừng) — bấm \"Gửi lại\"; tool sẽ kiểm tra BC2 đã có chưa, không tạo đôi.");
      } else {
        setMatKetNoi(false);
        setLoi(e.message);
        if (e.ma === "can_xac_nhan_canh_bao") {
          const cb = (e.duLieu.canh_bao as { noi_dung: string }[] | undefined)?.[0]?.noi_dung ?? e.message;
          setCanhBaoServer(cb);
        }
      }
    } finally {
      setDang(false);
    }
  }

  return (
    <div className="h-full flex flex-col min-h-0">
      <div className="shrink-0 bg-card border-b border-border px-4 py-2.5 flex items-center gap-3">
        <button type="button" onClick={onVe} className="h-9 px-3 rounded-lg border border-input text-[13px] font-semibold hover:bg-muted">
          ← Danh sách BC2
        </button>
        <div className="font-semibold text-[14px]">Tạo BC2 rỗng</div>
        <div className="ml-auto text-[12px] text-muted-foreground">
          {loai === "oto" ? "Ô tô" : "Mô tô"}{khoa ? ` · ${khoa.ten_kh}` : ""}
        </div>
      </div>

      {pha === "khoa" && (
        <BuocChonKhoa loai={loai} onChon={(k) => { setKhoa({ ma_kh: k.ma_kh, ten_kh: k.ten_kh }); setPha("form"); }} />
      )}

      {pha === "form" && khoa && (
        <>
          <div className="flex-1 min-h-0 overflow-auto p-4">
            <div className="max-w-[760px] mx-auto space-y-4">
              <div className="text-[15px] font-semibold">Thông tin BC2</div>
              <FormBc2 maKh={khoa.ma_kh} tenKh={khoa.ten_kh} onChange={setGt} />
            </div>
          </div>
          <div className="shrink-0 h-14 bg-card border-t border-border px-4 flex items-center gap-3">
            <button type="button" onClick={() => { setPha("khoa"); setGt(null); }}
              className="h-9 px-4 rounded-lg border border-input text-[13px] font-semibold hover:bg-muted">
              ← Đổi khóa
            </button>
            <button type="button" disabled={!gt?.hop_le} onClick={() => setXemLai(true)}
              className="ml-auto h-9 px-4 rounded-lg bg-tn text-white text-[13px] font-semibold disabled:opacity-45 disabled:cursor-not-allowed">
              Xem lại
            </button>
          </div>
        </>
      )}

      {pha === "xong" && kq && khoa && (
        <div className="p-4">
          <div className="max-w-[760px] mx-auto space-y-4">
            <div className="rounded-xl border border-success/40 bg-success/10 p-4">
              <div className="font-semibold">
                {kq.da_ton_tai ? "BC2 này đã được tạo từ trước" : "Đã tạo BC2"} số <span className="font-mono">{kq.ma_bc2}</span>
              </div>
              <div className="text-[13px] mt-1">
                Đang mở · ngày {(kq.ngay_bao_cao ?? gt?.ngay_bao_cao ?? "").split("-").reverse().join("/")}
                {kq.tong_so_thi_sinh != null && <> · tổng thí sinh ghi {kq.tong_so_thi_sinh}</>}.
              </div>
            </div>
            <div className="flex gap-2">
              <button type="button" onClick={() => onThemHocVien(khoa.ma_kh, khoa.ten_kh, kq.ma_bc2)}
                className="h-9 px-4 rounded-lg bg-tn text-white text-[13px] font-semibold">
                Thêm học viên vào BC2 này
              </button>
              <button type="button" onClick={onVe}
                className="h-9 px-4 rounded-lg border border-input text-[13px] font-semibold hover:bg-muted">
                Xong
              </button>
            </div>
          </div>
        </div>
      )}

      {xemLai && gt && khoa && (
        <div className="fixed inset-0 z-50 bg-black/40 grid place-items-center p-4">
          <div role="dialog" aria-modal="true" aria-label="Xem lại trước khi tạo BC2"
            className="bg-white rounded-xl shadow-2xl w-[560px] max-w-full flex flex-col">
            <div className="p-4 border-b border-border font-semibold">Xem lại trước khi tạo BC2</div>
            <div className="p-4 space-y-2 text-[13px]">
              <dl className="grid grid-cols-[130px_1fr] gap-y-1">
                <dt className="text-muted-foreground">Khóa</dt><dd>{khoa.ten_kh}</dd>
                <dt className="text-muted-foreground">Số BC2</dt><dd className="font-mono">{gt.so_bao_cao}</dd>
                <dt className="text-muted-foreground">Ngày báo cáo</dt><dd>{gt.ngay_bao_cao.split("-").reverse().join("/")}</dd>
                <dt className="text-muted-foreground">BC1 của khóa</dt><dd className="font-mono">{gt.bc1?.so_bao_cao}</dd>
                {gt.ghi_chu && (<><dt className="text-muted-foreground">Ghi chú</dt><dd>{gt.ghi_chu}</dd></>)}
              </dl>
              {(gt.canh_bao || canhBaoServer) && (
                <label className="flex items-start gap-2 rounded-lg border border-warning/40 bg-warning/10 p-3 text-warning">
                  <input type="checkbox" className="mt-1" checked={daXemCanhBao} onChange={(e) => setDaXemCanhBao(e.target.checked)} />
                  <span>{gt.canh_bao || canhBaoServer}. Tôi đã xem và vẫn muốn tạo thêm BC2.</span>
                </label>
              )}
              <label className="inline-flex items-center gap-2">
                <input type="checkbox" checked={xacNhanThat} onChange={(e) => setXacNhanThat(e.target.checked)} />
                Tôi xác nhận đây là CSDL thật (DB Nạp) — ghi thẳng vào hồ sơ
              </label>
              {loi && <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-destructive">{loi}</div>}
            </div>
            <div className="p-3 border-t border-border flex justify-end gap-2">
              <button type="button" disabled={dang} onClick={() => setXemLai(false)}
                className="h-9 px-4 rounded-lg border border-input text-[13px] font-semibold hover:bg-muted">
                Quay lại
              </button>
              <button type="button" onClick={tao}
                disabled={dang || !xacNhanThat || (!!(gt.canh_bao || canhBaoServer) && !daXemCanhBao)}
                className="h-9 px-4 rounded-lg bg-tn text-white text-[13px] font-semibold disabled:opacity-45 disabled:cursor-not-allowed">
                {matKetNoi ? "Gửi lại" : "Tạo BC2"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
