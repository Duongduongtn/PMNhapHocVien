import { useState } from "react";
import { NavLink, Outlet, Link, useLocation } from "react-router-dom";
import { Icon } from "./Icon";
import CauHinhDrawer from "./CauHinhDrawer";
import { ConfigDrawerContext } from "../lib/configDrawer";
import { NHAN_VAI_TRO, useToolAuth } from "../auth/ToolAuth";
import { MODULES, moduleForPath, type ModuleDef } from "../lib/modules";

const SB_KEY = "tool.sidebar.collapsed";

// Lớp màu nhấn theo phân hệ — phải là class literal để Tailwind giữ lại.
const ACCENT = {
  primary: {
    activeItem: "bg-accent text-primary",
    rail: "bg-primary",
    subActive: "bg-accent text-primary",
    ring: "focus-visible:ring-ring",
    chip: "text-primary bg-accent",
  },
  sync: {
    activeItem: "bg-sync-soft text-sync",
    rail: "bg-sync",
    subActive: "bg-sync-soft text-sync",
    ring: "focus-visible:ring-sync",
    chip: "text-sync bg-sync-soft",
  },
} as const;

export default function ToolLayout() {
  const { user, dangXuat } = useToolAuth();
  const { pathname } = useLocation();
  const active: ModuleDef = moduleForPath(pathname);
  const acc = ACCENT[active.accent];

  const [cfgOpen, setCfgOpen] = useState(false);

  const [collapsed, setCollapsed] = useState<boolean>(() => {
    try {
      return localStorage.getItem(SB_KEY) === "1";
    } catch {
      return false;
    }
  });
  const toggle = () => {
    setCollapsed((v) => {
      const nv = !v;
      try {
        localStorage.setItem(SB_KEY, nv ? "1" : "0");
      } catch {
        /* chế độ riêng tư / chặn storage — bỏ qua, chỉ là tiện ích */
      }
      return nv;
    });
  };

  // UI-1/2: khóa khung = 100svh, chỉ vùng nội dung cuộn → giống app Windows.
  return (
    <ConfigDrawerContext.Provider value={{ open: () => setCfgOpen(true) }}>
    <div className="h-[100svh] overflow-hidden bg-background flex flex-col">
      {/* Thanh tiêu đề */}
      <header className="shrink-0 h-12 bg-card border-b border-border flex items-center gap-3 px-4">
        <Link to="/" className="flex items-center gap-2 text-sm font-semibold text-foreground">
          <span className="inline-grid place-items-center w-6 h-6 rounded-md bg-primary text-primary-foreground">
            <Icon name="file" className="w-4 h-4" />
          </span>
          Thu nhận &amp; đồng bộ hồ sơ — Tool máy CSDT
        </Link>
        <div className="ml-auto flex items-center gap-2">
          {user && (
            <span className="text-[12px] text-muted-foreground max-w-[220px] truncate">
              {user.ho_ten || user.username}
              <span className="text-muted-foreground/60"> · {NHAN_VAI_TRO[user.vai_tro] ?? user.vai_tro}</span>
            </span>
          )}
          <button
            onClick={() => setCfgOpen(true)}
            title="Cấu hình kết nối (dùng chung cả tool)"
            className="inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-[12px] font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <Icon name="settings" className="w-4 h-4" /> Cấu hình
          </button>
          {user && (
            <button
              onClick={() => void dangXuat()}
              className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-[12px] text-muted-foreground hover:bg-muted hover:text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <Icon name="logout" className="w-3.5 h-3.5" /> Đăng xuất
            </button>
          )}
        </div>
      </header>

      <div className="flex-1 min-h-0 flex">
        {/* Sidebar phân hệ */}
        <aside
          className={
            "shrink-0 bg-card border-r border-border flex flex-col transition-[width] duration-150 " +
            (collapsed ? "w-[56px]" : "w-[220px]")
          }
        >
          <div className="px-3 pt-3 pb-1.5 flex items-center justify-between">
            {!collapsed && (
              <span className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">Phân hệ</span>
            )}
            <button
              onClick={toggle}
              title={collapsed ? "Mở rộng" : "Thu gọn"}
              aria-label={collapsed ? "Mở rộng thanh phân hệ" : "Thu gọn thanh phân hệ"}
              className="w-6 h-6 grid place-items-center rounded-md text-muted-foreground hover:bg-muted hover:text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <Icon name={collapsed ? "chevronRight" : "chevronLeft"} className="w-4 h-4" />
            </button>
          </div>

          <nav className="px-2 space-y-1">
            {MODULES.map((m) => {
              const on = m.id === active.id && !m.comingSoon;
              const a = ACCENT[m.accent];
              if (m.comingSoon) {
                return (
                  <div
                    key={m.id}
                    title="Phân hệ dự kiến"
                    className="flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-[13px] text-muted-foreground/60 cursor-default select-none"
                  >
                    <Icon name={m.icon} className="w-[18px] h-[18px] shrink-0" />
                    {!collapsed && (
                      <span className="inline-flex items-center gap-1.5 truncate">
                        {m.label}
                        <span className="text-[9px] border border-border rounded px-1 py-px">dự kiến</span>
                      </span>
                    )}
                  </div>
                );
              }
              return (
                <NavLink
                  key={m.id}
                  to={m.subnav[0]?.to ?? m.base}
                  title={collapsed ? m.label : undefined}
                  className={
                    "relative flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-[13px] font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 " +
                    a.ring + " " +
                    (on ? a.activeItem + " font-semibold" : "text-foreground hover:bg-muted")
                  }
                >
                  {on && <span className={"absolute left-0 top-1.5 bottom-1.5 w-[3px] rounded-full " + a.rail} />}
                  <Icon name={m.icon} className="w-[18px] h-[18px] shrink-0" />
                  {!collapsed && <span className="truncate">{m.label}</span>}
                </NavLink>
              );
            })}
          </nav>

          {!collapsed && (
            <div className="mt-auto px-3 py-3 border-t border-border">
              <p className="text-[11px] text-muted-foreground leading-relaxed">
                Mỗi phân hệ ghi vào một CSDL riêng. Bấm để chuyển — thanh công cụ &amp; màu đổi theo phân hệ.
              </p>
            </div>
          )}
        </aside>

        {/* Vùng nội dung: sub-nav + banner + màn */}
        <main className="flex-1 min-w-0 flex flex-col overflow-hidden">
          <div className="shrink-0 h-11 bg-card border-b border-border px-4 flex items-center gap-1">
            {active.subnav.map((s) => (
              <NavLink
                key={s.to}
                to={s.to}
                className={({ isActive }) =>
                  "inline-flex items-center gap-1.5 h-8 px-3 rounded-md text-[13px] transition-colors focus-visible:outline-none focus-visible:ring-2 " +
                  acc.ring + " " +
                  (isActive ? acc.subActive + " font-semibold" : "text-muted-foreground hover:bg-muted hover:text-foreground")
                }
              >
                <Icon name={s.icon} className="w-3.5 h-3.5" /> {s.label}
              </NavLink>
            ))}
          </div>

          {active.db && (
            <div className="shrink-0 flex items-center gap-2 px-4 py-1.5 text-[12.5px] bg-warning/10 border-b border-warning/30 text-warning">
              <Icon name="warn" className="w-4 h-4 shrink-0" />
              <span>
                Phân hệ <b>{active.label}</b> ghi vào <b>CSDL đích: {active.db}</b> — khác CSDL nguồn của phần Nạp.
              </span>
            </div>
          )}

          <div className="flex-1 min-h-0 overflow-y-auto">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
    <CauHinhDrawer open={cfgOpen} onClose={() => setCfgOpen(false)} />
    </ConfigDrawerContext.Provider>
  );
}
