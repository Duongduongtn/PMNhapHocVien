import { NavLink, Outlet, Link } from "react-router-dom";
import { Icon } from "./Icon";

const navCls = ({ isActive }: { isActive: boolean }) =>
  "inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-[12px] transition-colors " +
  (isActive ? "bg-white/25 text-white font-semibold" : "bg-white/10 text-white/90 hover:bg-white/20");

export default function ToolLayout() {
  return (
    <div className="min-h-screen bg-[hsl(210_40%_96%)]">
      <div className="max-w-[1500px] mx-auto p-4 sm:p-6">
        <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden">
          {/* Title bar */}
          <div className="flex items-center justify-between px-4 py-2.5 bg-primary text-primary-foreground flex-wrap gap-2">
            <Link to="/tool/nap" className="flex items-center gap-2 text-sm font-semibold">
              <Icon name="file" className="w-4 h-4" /> Thu nhận hồ sơ cấp mới — Tool nạp DB
            </Link>
            <div className="flex items-center gap-2 text-[12px]">
              <span className="inline-flex items-center gap-1.5 bg-white/15 rounded-full px-2.5 py-1">
                <span className="w-2 h-2 rounded-full bg-emerald-300" /> Đã kết nối SQL Server
              </span>
              <NavLink to="/tool/nap" className={navCls} end>
                <Icon name="plus" className="w-3.5 h-3.5" /> Nạp
              </NavLink>
              <NavLink to="/tool/tao-khoa" className={navCls}>
                <Icon name="calendar" className="w-3.5 h-3.5" /> Tạo khóa
              </NavLink>
              <NavLink to="/tool/cau-hinh" className={navCls}>
                <Icon name="settings" className="w-3.5 h-3.5" /> Cấu hình
              </NavLink>
              <span className="text-white/80 ml-1">NV nạp: Lê Văn Bình</span>
              <Link to="/" title="Về trang chọn app" className="text-white/80 hover:text-white transition-colors">
                <Icon name="logout" className="w-4 h-4" />
              </Link>
            </div>
          </div>
          <Outlet />
        </div>
      </div>
    </div>
  );
}
