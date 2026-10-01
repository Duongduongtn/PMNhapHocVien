import { NavLink, Outlet, Link } from "react-router-dom";
import { Icon } from "./Icon";
import { NHAN_VAI_TRO, useToolAuth } from "../auth/ToolAuth";

const navCls = ({ isActive }: { isActive: boolean }) =>
  "inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-[12px] transition-colors " +
  (isActive ? "bg-white/25 text-white font-semibold" : "bg-white/10 text-white/90 hover:bg-white/20");

// Shell cho tool. Nav Nạp / Tạo khóa + badge "Đã kết nối SQL Server" thêm khi các màn đó
// được dựng (task 6, 21) — tham chiếu bố cục đầy đủ ở ui-demo/src/components/ToolLayout.tsx.
export default function ToolLayout() {
  const { user, dangXuat } = useToolAuth();
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-[1500px] mx-auto p-4 sm:p-6">
        <div className="bg-card border border-border rounded-xl shadow-sm overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2.5 bg-primary text-primary-foreground flex-wrap gap-2">
            <Link to="/" className="flex items-center gap-2 text-sm font-semibold">
              <Icon name="file" className="w-4 h-4" /> Thu nhận hồ sơ cấp mới — Tool nạp DB
            </Link>
            <div className="flex items-center gap-2">
              <NavLink to="/tool/nap" className={navCls}>
                <Icon name="file" className="w-3.5 h-3.5" /> Nạp hồ sơ
              </NavLink>
              <NavLink to="/tool/cau-hinh" className={navCls}>
                <Icon name="settings" className="w-3.5 h-3.5" /> Cấu hình
              </NavLink>
              {user && (
                <span className="inline-flex items-center gap-2 pl-2 ml-1 border-l border-white/25">
                  <span className="text-[12px] text-white/90 max-w-[180px] truncate">
                    {user.ho_ten || user.username}
                    <span className="text-white/60"> · {NHAN_VAI_TRO[user.vai_tro] ?? user.vai_tro}</span>
                  </span>
                  <button
                    onClick={() => void dangXuat()}
                    className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-[12px] bg-white/10 text-white/90 hover:bg-white/20 transition-colors"
                  >
                    <Icon name="logout" className="w-3.5 h-3.5" /> Đăng xuất
                  </button>
                </span>
              )}
            </div>
          </div>
          <Outlet />
        </div>
      </div>
    </div>
  );
}
