import { useState } from "react";
import ChuGiaiTrangThai from "../../components/ChuGiaiTrangThai";
import BuocChonHocVien from "../../components/tnbc2/BuocChonHocVien";
import BuocXacNhan from "../../components/tnbc2/BuocXacNhan";
import DanhSachBc2 from "../../components/tnbc2/DanhSachBc2";
import TaoBc2Rong from "../../components/tnbc2/TaoBc2Rong";
import XemBc2 from "../../components/tnbc2/XemBc2";
import { BuocChonKhoa, DauWizard, type TrangThaiWizard } from "../../components/tnbc2/WizardBc2";
import type { LoaiHang } from "../../lib/tnbc2Api";

// TNB-03/04/05/07 — tab Báo cáo 2. Task 109: lối vào "Lập BC2 mới" + khung wizard + bước ①.
// Danh sách BC2 đầy đủ (task 115) sẽ thay phần "danh sách" bên dưới; bước ② (110) và ③ (112) gắn vào khung wizard.

export default function BaoCao2() {
  const [loai, setLoai] = useState<LoaiHang>("oto");
  const [wiz, setWiz] = useState<TrangThaiWizard | null>(null);
  const [thongBao, setThongBao] = useState("");
  const [rong, setRong] = useState(false);
  const [xem, setXem] = useState<string | null>(null);
  // Từ bước ② nhảy sang xem một BC2 (để gỡ học viên): giữ wizard để "Quay lại" trở về đúng bước.
  const [veWiz, setVeWiz] = useState<TrangThaiWizard | null>(null);

  if (xem) {
    return (
      <XemBc2
        maBc2={xem}
        onVe={() => {
          setXem(null);
          if (veWiz) { setWiz(veWiz); setVeWiz(null); }
        }}
        onThem={(ct) => {
          setXem(null);
          setVeWiz(null);
          setThongBao(`Thêm học viên vào BC2 ${ct.ma_bc2}.`);
          setWiz({ loai: ct.loai === "moto" ? "moto" : "oto", buoc: 2, maKh: ct.ma_kh, tenKh: ct.ten_kh, maBc2: ct.ma_bc2,
            dsMaDk: [], nSan: 0, nThi: 0, tenHv: {} });
        }}
      />
    );
  }

  if (rong) {
    return (
      <TaoBc2Rong
        loai={loai}
        onVe={() => setRong(false)}
        onThemHocVien={(maKh, tenKh, maBc2) => {
          setRong(false);
          setThongBao(`Đã tạo BC2 ${maBc2} — chọn học viên để thêm vào BC2 này.`);
          setWiz({ loai, buoc: 2, maKh, tenKh, maBc2, dsMaDk: [], nSan: 0, nThi: 0, tenHv: {} });
        }}
      />
    );
  }

  if (wiz) {
    return (
      <div className="h-full flex flex-col min-h-0">
        <DauWizard tt={wiz} onVe={() => { setWiz(null); setThongBao(""); }} />
        {thongBao && (
          <div className="shrink-0 px-4 py-2 text-[13px] bg-tn-soft text-tn border-b border-tn-border">{thongBao}</div>
        )}
        {wiz.buoc === 1 && (
          <BuocChonKhoa
            loai={wiz.loai}
            onChon={(k, maBc2) => {
              setThongBao(maBc2 ? `Khóa này đã có BC2 ${maBc2} — chuyển sang thêm học viên vào BC2 đó.` : "");
              setWiz({ ...wiz, buoc: 2, maKh: k.ma_kh, tenKh: k.ten_kh, maBc2, dsMaDk: [], nSan: 0, nThi: 0, tenHv: {} });
            }}
          />
        )}
        {wiz.buoc === 2 && (
          <BuocChonHocVien
            maKh={wiz.maKh}
            tenKh={wiz.tenKh}
            maBc2={wiz.maBc2}
            loai={wiz.loai}
            onDoiKhoa={() => { setThongBao(""); setWiz({ ...wiz, buoc: 1 }); }}
            onTiep={(chon) => setWiz({ ...wiz, buoc: 3, ...chon })}
            onXemBc2={(ma) => { setVeWiz(wiz); setWiz(null); setXem(ma); }}
          />
        )}
        {wiz.buoc === 3 && (
          <BuocXacNhan
            tt={wiz}
            onQuayLai={() => setWiz({ ...wiz, buoc: 2 })}
            onXong={() => { setWiz(null); setThongBao(""); }}
          />
        )}
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-5 max-w-[1200px]">
      <div className="flex items-start gap-3">
        <div className="min-w-0">
          <h1 className="text-lg font-bold">Báo cáo 2</h1>
          <p className="text-[13px] text-muted-foreground mt-0.5">
            Lập BC2 mới, thêm học viên vào BC2 đang mở, xem/gỡ học viên và theo dõi các BC2 đã lập.
          </p>
        </div>
        <div className="ml-auto shrink-0"><ChuGiaiTrangThai /></div>
      </div>
      <div className="mt-4 flex items-center gap-3">
        <div className="inline-flex rounded-lg border border-border overflow-hidden" role="group" aria-label="Loại hạng">
          {([["oto", "Ô tô"], ["moto", "Mô tô"]] as const).map(([v, t]) => (
            <button key={v} type="button" onClick={() => setLoai(v)} aria-pressed={loai === v}
              className={`h-9 px-4 text-[13px] font-semibold ${loai === v ? "bg-tn text-white" : "bg-white hover:bg-muted"}`}>
              {t}
            </button>
          ))}
        </div>
        <button type="button"
          onClick={() => setWiz({ loai, buoc: 1, maKh: "", tenKh: "", maBc2: "", dsMaDk: [], nSan: 0, nThi: 0, tenHv: {} })}
          className="h-9 px-4 rounded-lg bg-tn text-white text-[13px] font-semibold">
          Lập BC2 mới
        </button>
        <button type="button" onClick={() => setRong(true)}
          className="h-9 px-4 rounded-lg border border-input text-[13px] font-semibold hover:bg-muted">
          Tạo BC2 rỗng
        </button>
      </div>
      <DanhSachBc2
        loai={loai}
        onXem={(b) => setXem(b.ma_bc2)}
        onThem={(b) => {
          setThongBao(`Thêm học viên vào BC2 ${b.ma_bc2}.`);
          setWiz({ loai: b.loai === "moto" ? "moto" : "oto", buoc: 2, maKh: b.ma_kh, tenKh: b.ten_kh, maBc2: b.ma_bc2,
            dsMaDk: [], nSan: 0, nThi: 0, tenHv: {} });
        }}
      />
    </div>
  );
}
