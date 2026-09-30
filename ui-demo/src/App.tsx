import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import DangNhap from "./pages/DangNhap";
import ToolLayout from "./components/ToolLayout";
import AppLayout from "./components/AppLayout";
import NapHoSo from "./pages/tool/NapHoSo";
import TaoKhoa from "./pages/tool/TaoKhoa";
import CauHinh from "./pages/tool/CauHinh";
import Quet from "./pages/app/Quet";
import DaGui from "./pages/app/DaGui";
import TaiKhoan from "./pages/app/TaiKhoan";
import AdminHoSo from "./pages/admin/HoSo";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/dang-nhap" element={<DangNhap />} />
        <Route path="/tool" element={<ToolLayout />}>
          <Route path="nap" element={<NapHoSo />} />
          <Route path="tao-khoa" element={<TaoKhoa />} />
          <Route path="cau-hinh" element={<CauHinh />} />
        </Route>
        <Route path="/app" element={<AppLayout />}>
          <Route path="quet" element={<Quet />} />
          <Route path="da-gui" element={<DaGui />} />
          <Route path="tai-khoan" element={<TaiKhoan />} />
        </Route>
        <Route path="/admin/ho-so" element={<AdminHoSo />} />
      </Routes>
    </BrowserRouter>
  );
}
