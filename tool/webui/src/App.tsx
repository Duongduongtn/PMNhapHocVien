import { Routes, Route, Navigate } from "react-router-dom";
import ToolLayout from "./components/ToolLayout";
import NapHoSo from "./pages/tool/NapHoSo";
import TaoKhoa from "./pages/tool/TaoKhoa";
import DangNhap from "./pages/tool/DangNhap";
import BanDongBo from "./pages/sync/BanDongBo";
import TraCuuCDB from "./pages/sync/TraCuuCDB";
import LichSu from "./pages/sync/LichSu";
import { ToolAuthProvider, useToolAuth } from "./auth/ToolAuth";
import type { ReactNode } from "react";

// Nghiệp vụ ghi DB cần đăng nhập; chưa đăng nhập → màn đăng nhập
// (Cấu hình vẫn vào được — A1).
function CoBaoVe({ children }: { children: ReactNode }) {
  const { user, dangKhoiTao } = useToolAuth();
  if (dangKhoiTao)
    return <div className="p-8 text-center text-sm text-muted-foreground">Đang khôi phục phiên…</div>;
  return user ? <>{children}</> : <DangNhap />;
}

export default function App() {
  return (
    <ToolAuthProvider>
      <Routes>
        <Route path="/" element={<ToolLayout />}>
          <Route index element={<Navigate to="/tool/nap" replace />} />
          {/* Phân hệ Nạp hồ sơ */}
          <Route path="tool/nap" element={<CoBaoVe><NapHoSo /></CoBaoVe>} />
          <Route path="tool/tao-khoa" element={<CoBaoVe><TaoKhoa /></CoBaoVe>} />
          {/* Cấu hình kết nối: panel ⚙ trên header (HTG-07) — không còn route riêng */}
          {/* Phân hệ Đồng bộ CDB (màn thật dựng ở các bước sau) */}
          <Route path="sync/ban-dong-bo" element={<CoBaoVe><BanDongBo /></CoBaoVe>} />
          <Route path="sync/tra-cuu" element={<CoBaoVe><TraCuuCDB /></CoBaoVe>} />
          <Route path="sync/lich-su" element={<CoBaoVe><LichSu /></CoBaoVe>} />
        </Route>
      </Routes>
    </ToolAuthProvider>
  );
}
