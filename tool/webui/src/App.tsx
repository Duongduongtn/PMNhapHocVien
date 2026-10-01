import { Routes, Route } from "react-router-dom";
import ToolLayout from "./components/ToolLayout";
import { Icon } from "./components/Icon";

// Trang tạm của khung — các màn thật (Cấu hình, Nạp, Tạo khóa) dựng ở task sau.
function Home() {
  return (
    <div className="p-8 text-center">
      <Icon name="db" className="w-10 h-10 mx-auto text-primary" />
      <h1 className="mt-3 text-lg font-semibold text-foreground">Khung tool đã sẵn sàng</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Màn Cấu hình, Nạp, Tạo khóa sẽ được dựng ở các task sau (xem docs/BUILD-PLAN.md).
      </p>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<ToolLayout />}>
        <Route index element={<Home />} />
      </Route>
    </Routes>
  );
}
