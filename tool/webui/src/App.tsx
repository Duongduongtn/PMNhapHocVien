import { Routes, Route, Navigate } from "react-router-dom";
import ToolLayout from "./components/ToolLayout";
import CauHinh from "./pages/tool/CauHinh";
import NapHoSo from "./pages/tool/NapHoSo";
import DangNhap from "./pages/tool/DangNhap";
import { ToolAuthProvider, useToolAuth } from "./auth/ToolAuth";

// Nạp cần đăng nhập; chưa đăng nhập → hiện màn đăng nhập (Cấu hình vẫn vào được — A1).
function NapCoBaoVe() {
  const { user } = useToolAuth();
  return user ? <NapHoSo /> : <DangNhap />;
}

export default function App() {
  return (
    <ToolAuthProvider>
      <Routes>
        <Route path="/" element={<ToolLayout />}>
          <Route index element={<Navigate to="/tool/nap" replace />} />
          <Route path="tool/nap" element={<NapCoBaoVe />} />
          <Route path="tool/cau-hinh" element={<CauHinh />} />
        </Route>
      </Routes>
    </ToolAuthProvider>
  );
}
