import { Outlet, Link } from "react-router-dom";
import { Icon } from "./Icon";

// Shell khung cho tool. Nav đầy đủ (Nạp / Tạo khóa / Cấu hình) + badge "Đã kết nối SQL Server"
// sẽ được thêm khi các màn tương ứng được dựng ở task 4, 6, 21 — tham chiếu bố cục đầy đủ ở
// ui-demo/src/components/ToolLayout.tsx.
export default function ToolLayout() {
  return (
    <div className="min-h-screen bg-[hsl(210_40%_96%)]">
      <div className="max-w-[1500px] mx-auto p-4 sm:p-6">
        <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2.5 bg-primary text-primary-foreground flex-wrap gap-2">
            <Link to="/" className="flex items-center gap-2 text-sm font-semibold">
              <Icon name="file" className="w-4 h-4" /> Thu nhận hồ sơ cấp mới — Tool nạp DB
            </Link>
            <span className="inline-flex items-center gap-1.5 bg-white/15 rounded-full px-2.5 py-1 text-[12px]">
              <span className="w-2 h-2 rounded-full bg-amber-300" /> Chưa cấu hình kết nối
            </span>
          </div>
          <Outlet />
        </div>
      </div>
    </div>
  );
}
