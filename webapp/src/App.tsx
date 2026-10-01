import { Navigate, Outlet, Route, Routes } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import CapNhatApp from "./components/CapNhatApp";
import DangNhap from "./pages/DangNhap";
import Quet from "./pages/Quet";
import DaGui from "./pages/DaGui";
import TaiKhoan from "./pages/TaiKhoan";
import { AuthProvider, useAuth } from "./auth/AuthContext";

// Chưa đăng nhập → đẩy về /dang-nhap (không đăng nhập không dùng được — HTG-01).
function RequireAuth() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/dang-nhap" replace />;
  return <Outlet />;
}

export default function App() {
  return (
    <AuthProvider>
      <CapNhatApp />
      <Routes>
        <Route path="/dang-nhap" element={<DangNhap />} />
        <Route element={<RequireAuth />}>
          <Route element={<AppLayout />}>
            <Route index element={<Navigate to="/quet" replace />} />
            <Route path="/quet" element={<Quet />} />
            <Route path="/da-gui" element={<DaGui />} />
            <Route path="/tai-khoan" element={<TaiKhoan />} />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/quet" replace />} />
      </Routes>
    </AuthProvider>
  );
}
