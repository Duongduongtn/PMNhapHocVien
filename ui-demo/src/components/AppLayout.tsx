import { NavLink, Outlet, Link } from "react-router-dom";
import { Icon } from "./Icon";

// Bottom-nav (mobile) — mobile-first giữ nguyên như app điện thoại
const tabCls = ({ isActive }: { isActive: boolean }) =>
  "flex flex-col items-center gap-1 py-2.5 text-[11px] transition-colors " +
  (isActive ? "text-primary font-semibold" : "text-muted-foreground hover:text-foreground");

// Side-nav (desktop ≥ lg)
const sideCls = ({ isActive }: { isActive: boolean }) =>
  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors " +
  (isActive ? "bg-primary text-primary-foreground font-semibold" : "text-muted-foreground hover:bg-muted hover:text-foreground");

export default function AppLayout() {
  return (
    <div className="min-h-screen bg-slate-200 lg:bg-[hsl(210_40%_96%)]">
      <div className="mx-auto w-full max-w-[440px] lg:max-w-[1180px] min-h-screen lg:min-h-0 lg:py-6 flex flex-col lg:flex-row">
        {/* SIDEBAR — chỉ desktop */}
        <aside className="hidden lg:flex flex-col w-60 shrink-0 bg-card border border-border rounded-l-xl">
          <div className="px-4 py-4 flex items-center gap-2 border-b border-border">
            <div className="w-9 h-9 rounded-lg bg-primary text-primary-foreground flex items-center justify-center"><Icon name="scan" className="w-5 h-5" /></div>
            <div><div className="text-sm font-bold leading-tight">Thu nhận hồ sơ</div><div className="text-[11px] text-muted-foreground leading-tight">App web · CSDT 70004</div></div>
          </div>
          <nav className="flex-1 p-3 space-y-1">
            <NavLink to="/app/quet" className={sideCls}><Icon name="scan" className="w-5 h-5" /> Quét căn cước</NavLink>
            <NavLink to="/app/da-gui" className={sideCls}><Icon name="send" className="w-5 h-5" /> Hồ sơ đã gửi</NavLink>
            <NavLink to="/app/tai-khoan" className={sideCls}><Icon name="user" className="w-5 h-5" /> Tài khoản</NavLink>
          </nav>
          <div className="p-3 border-t border-border flex items-center justify-between">
            <div className="flex items-center gap-2 min-w-0">
              <span className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center shrink-0"><Icon name="user" className="w-4 h-4 text-muted-foreground" /></span>
              <span className="text-[13px] font-medium truncate">Trần Thị Hoa</span>
            </div>
            <Link to="/" aria-label="Đăng xuất" className="text-muted-foreground hover:text-foreground transition-colors"><Icon name="logout" className="w-4 h-4" /></Link>
          </div>
        </aside>

        {/* CỘT NỘI DUNG */}
        <div className="flex-1 min-w-0 bg-background flex flex-col shadow-xl lg:shadow-none lg:bg-card lg:border lg:border-l-0 lg:border-border lg:rounded-r-xl lg:overflow-hidden">
          {/* Header — chỉ mobile (desktop dùng sidebar) */}
          <header className="lg:hidden bg-primary text-primary-foreground px-4 pt-3 pb-3 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-white/15 flex items-center justify-center"><Icon name="scan" className="w-5 h-5" /></div>
              <div><div className="text-sm font-semibold leading-tight">Thu nhận hồ sơ</div><div className="text-[11px] text-white/70 leading-tight">Quét căn cước</div></div>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] bg-white/15 rounded-full px-2 py-1">Trần Thị Hoa</span>
              <Link to="/" aria-label="Đăng xuất" className="w-7 h-7 rounded-full bg-white/15 flex items-center justify-center hover:bg-white/25 transition-colors"><Icon name="logout" className="w-4 h-4" /></Link>
            </div>
          </header>

          <main className="flex-1 overflow-y-auto">
            <Outlet />
          </main>

          {/* Bottom-nav — chỉ mobile */}
          <nav className="lg:hidden shrink-0 border-t border-border bg-card grid grid-cols-3">
            <NavLink to="/app/quet" className={tabCls}><Icon name="scan" /> Quét</NavLink>
            <NavLink to="/app/da-gui" className={tabCls}><Icon name="send" /> Đã gửi</NavLink>
            <NavLink to="/app/tai-khoan" className={tabCls}><Icon name="user" /> Tài khoản</NavLink>
          </nav>
        </div>
      </div>
    </div>
  );
}
