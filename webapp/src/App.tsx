import { Navigate, Outlet, Route, Routes } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import CapNhatApp from "./components/CapNhatApp";
import DangNhap from "./pages/DangNhap";
import Quet from "./pages/Quet";
import DaGui from "./pages/DaGui";
import TaiKhoan from "./pages/TaiKhoan";
import QuanLyTaiKhoan from "./pages/QuanLyTaiKhoan";
import { AuthProvider, useAuth } from "./auth/AuthContext";

// Chưa đăng nhập → đẩy về /dang-nhap (không đăng nhập không dùng được — HTG-01).
function RequireAuth() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/dang-nhap" replace />;
  return <Outlet />;
}

// Chỉ admin (HTG-05) — không phải admin thì đẩy về Tài khoản (server cũng chặn 403).
function RequireAdmin() {
  const { user } = useAuth();
  if (user && user.vai_tro !== "admin") return <Navigate to="/tai-khoan" replace />;
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
            <Route element={<RequireAdmin />}>
              <Route path="/quan-ly-tai-khoan" element={<QuanLyTaiKhoan />} />
            </Route>
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/quet" replace />} />
      </Routes>
    </AuthProvider>
  );
}
