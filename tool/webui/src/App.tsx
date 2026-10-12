import { Routes, Route, Navigate } from "react-router-dom";
import ToolLayout from "./components/ToolLayout";
import NapHoSo from "./pages/tool/NapHoSo";
import TraCuuDBPage from "./pages/tool/TraCuuDBPage";
import TaoKhoa from "./pages/tool/TaoKhoa";
import DangNhap from "./pages/tool/DangNhap";
import Wizard from "./pages/tool/Wizard";
import BanDongBo from "./pages/sync/BanDongBo";
import TraCuuCDB from "./pages/sync/TraCuuCDB";
import LichSu from "./pages/sync/LichSu";
import CapNhatKQDT from "./pages/ketqua/CapNhatKQDT";
import TheoDoiKetXuat from "./pages/ketqua/TheoDoiKetXuat";
import PhanCongTheoKhoa from "./pages/phancong/PhanCongTheoKhoa";
import RaSoatKhoa from "./pages/phancong/RaSoatKhoa";
import HanGiayTo from "./pages/phancong/HanGiayTo";
import TotNghiep from "./pages/tnbc2/TotNghiep";
import BaoCao2 from "./pages/tnbc2/BaoCao2";
import CuuTrangThai from "./pages/tnbc2/CuuTrangThai";
import NhatKy from "./pages/tnbc2/NhatKy";
import { ToolAuthProvider, useToolAuth } from "./auth/ToolAuth";
import type { ReactNode } from "react";

// Nghiệp vụ ghi DB cần đăng nhập; chưa đăng nhập → màn đăng nhập.
// Máy sạch (chưa đủ cấu hình, DGT-03) → wizard thiết lập lần đầu thay vì màn đăng nhập.
// (Cấu hình vẫn vào được — A1).
function CoBaoVe({ children }: { children: ReactNode }) {
  const { user, dangKhoiTao, daCauHinh } = useToolAuth();
  if (dangKhoiTao || daCauHinh === null)
    return <div className="p-8 text-center text-sm text-muted-foreground">Đang khôi phục phiên…</div>;
  if (!user) return daCauHinh === false ? <Navigate to="/tool/thiet-lap" replace /> : <DangNhap />;
  return <>{children}</>;
}

export default function App() {
  return (
    <ToolAuthProvider>
      <Routes>
        {/* Wizard thiết lập lần đầu (DGT-03) — toàn màn, ngoài ToolLayout */}
        <Route path="/tool/thiet-lap" element={<Wizard />} />
        <Route path="/" element={<ToolLayout />}>
          <Route index element={<Navigate to="/tool/nap" replace />} />
          {/* Phân hệ Nạp hồ sơ */}
          <Route path="tool/nap" element={<CoBaoVe><NapHoSo /></CoBaoVe>} />
          <Route path="tool/tra-cuu" element={<CoBaoVe><TraCuuDBPage /></CoBaoVe>} />
          <Route path="tool/tao-khoa" element={<CoBaoVe><TaoKhoa /></CoBaoVe>} />
          {/* Cấu hình kết nối: panel ⚙ trên header (HTG-07) — không còn route riêng */}
          {/* Phân hệ Đồng bộ CDB (màn thật dựng ở các bước sau) */}
          <Route path="sync/ban-dong-bo" element={<CoBaoVe><BanDongBo /></CoBaoVe>} />
          <Route path="sync/tra-cuu" element={<CoBaoVe><TraCuuCDB /></CoBaoVe>} />
          <Route path="sync/lich-su" element={<CoBaoVe><LichSu /></CoBaoVe>} />
          {/* Phân hệ Kết quả đào tạo (KQD) — module #3 */}
          <Route path="ket-qua/cap-nhat" element={<CoBaoVe><CapNhatKQDT /></CoBaoVe>} />
          <Route path="ket-qua/ket-xuat" element={<CoBaoVe><TheoDoiKetXuat /></CoBaoVe>} />

          <Route path="phan-cong" element={<Navigate to="/phan-cong/theo-khoa" replace />} />
          <Route path="phan-cong/theo-khoa" element={<CoBaoVe><PhanCongTheoKhoa /></CoBaoVe>} />
          <Route path="phan-cong/ra-soat" element={<CoBaoVe><RaSoatKhoa /></CoBaoVe>} />
          <Route path="phan-cong/han-giay-to" element={<CoBaoVe><HanGiayTo /></CoBaoVe>} />

          {/* Phân hệ Tốt nghiệp & Báo cáo 2 (TNB) — phân hệ #5, ghi DB Nạp */}
          <Route path="tot-nghiep-bc2" element={<Navigate to="/tot-nghiep-bc2/tot-nghiep" replace />} />
          <Route path="tot-nghiep-bc2/tot-nghiep" element={<CoBaoVe><TotNghiep /></CoBaoVe>} />
          <Route path="tot-nghiep-bc2/bao-cao-2" element={<CoBaoVe><BaoCao2 /></CoBaoVe>} />
          <Route path="tot-nghiep-bc2/cuu-trang-thai" element={<CoBaoVe><CuuTrangThai /></CoBaoVe>} />
          <Route path="tot-nghiep-bc2/nhat-ky" element={<CoBaoVe><NhatKy /></CoBaoVe>} />
        </Route>
      </Routes>
    </ToolAuthProvider>
  );
}
