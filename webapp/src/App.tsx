import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import Placeholder from "./pages/Placeholder";

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Navigate to="/quet" replace />} />
        <Route path="/quet" element={<Placeholder ten="Quét căn cước" icon="scan" />} />
        <Route path="/da-gui" element={<Placeholder ten="Hồ sơ đã gửi" icon="send" />} />
        <Route path="/tai-khoan" element={<Placeholder ten="Tài khoản" icon="user" />} />
      </Route>
      <Route path="*" element={<Navigate to="/quet" replace />} />
    </Routes>
  );
}
