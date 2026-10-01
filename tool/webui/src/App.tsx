import { Routes, Route, Navigate } from "react-router-dom";
import ToolLayout from "./components/ToolLayout";
import CauHinh from "./pages/tool/CauHinh";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<ToolLayout />}>
        {/* Màn mặc định hiện tại là Cấu hình; Nạp/Tạo khóa thêm ở task sau */}
        <Route index element={<Navigate to="/tool/cau-hinh" replace />} />
        <Route path="tool/cau-hinh" element={<CauHinh />} />
      </Route>
    </Routes>
  );
}
