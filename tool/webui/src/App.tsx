import { Routes, Route, Navigate } from "react-router-dom";
import ToolLayout from "./components/ToolLayout";
import CauHinh from "./pages/tool/CauHinh";
import NapHoSo from "./pages/tool/NapHoSo";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<ToolLayout />}>
        {/* Mặc định vào màn Nạp hồ sơ; Tạo khóa thêm ở task sau */}
        <Route index element={<Navigate to="/tool/nap" replace />} />
        <Route path="tool/nap" element={<NapHoSo />} />
        <Route path="tool/cau-hinh" element={<CauHinh />} />
      </Route>
    </Routes>
  );
}
