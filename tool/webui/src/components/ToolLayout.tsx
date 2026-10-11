import { useEffect, useState } from "react";
import { NavLink, Outlet, Link, useLocation } from "react-router-dom";
import { Icon } from "./Icon";
import CauHinhDrawer from "./CauHinhDrawer";
import { ConfigDrawerContext } from "../lib/configDrawer";
import { NHAN_VAI_TRO, useToolAuth } from "../auth/ToolAuth";
import { MODULES, NHOM_INFO, moduleForPath, type ModuleDef } from "../lib/modules";
import { getDbDichInfo, coToken, type DbDichInfo } from "../lib/api";

const SB_KEY = "tool.sidebar.collapsed";

// Lớp màu nhấn theo phân hệ — phải là class literal để Tailwind giữ lại.
const ACCENT = {
  primary: {
    activeItem: "bg-accent text-primary",
    rail: "bg-primary",
    subActive: "bg-accent text-primary",
    ring: "focus-visible:ring-ring",
    chip: "text-primary bg-accent",
    hover: "hover:bg-accent/70 hover:text-primary",
  },
  sync: {
    activeItem: "bg-sync-soft text-sync",
    rail: "bg-sync",
    subActive: "bg-sync-soft text-sync",
    ring: "focus-visible:ring-sync",
    chip: "text-sync bg-sync-soft",
    hover: "hover:bg-sync-soft/70 hover:text-sync",
  },
  kq: {
    activeItem: "bg-kq-soft text-kq",
    rail: "bg-kq",
    subActive: "bg-kq-soft text-kq",
    ring: "focus-visible:ring-kq",
    chip: "text-kq bg-kq-soft",
    hover: "hover:bg-kq-soft/70 hover:text-kq",
  },
  pc: {
    activeItem: "bg-pc-soft text-pc",
    rail: "bg-pc",
    subActive: "bg-pc-soft text-pc",
    ring: "focus-visible:ring-pc",
    chip: "text-pc bg-pc-soft",
    hover: "hover:bg-pc-soft/70 hover:text-pc",
  },
  tn: {
    activeItem: "bg-tn-soft text-tn",
    rail: "bg-tn",
    subActive: "bg-tn-soft text-tn",
    ring: "focus-visible:ring-tn",
    chip: "text-tn bg-tn-soft",
    hover: "hover:bg-tn-soft/70 hover:text-tn",
  },
} as const;

export default function ToolLayout() {
  const { user, dangXuat } = useToolAuth();
  const { pathname } = useLocation();
  const active: ModuleDef = moduleForPath(pathname);
  const acc = ACCENT[active.accent];

  const [cfgOpen, setCfgOpen] = useState(false);

  // Băng nhắc CSDL đích (dùng chung Sync + Kết quả đào tạo): tên DB · máy · CSĐT · đã kết nối.
  // Fetch khi mở phân hệ ghi DB đích; nối lỗi → connected=false (banner tự nhắc chưa kết nối).
  const [dbInfo, setDbInfo] = useState<DbDichInfo | null>(null);
  useEffect(() => {
    if (!active.db || active.dbNap || !coToken()) {
      setDbInfo(null);
      return;
    }
    let huy = false;
    getDbDichInfo()
      .then((d) => { if (!huy) setDbInfo(d); })
      .catch(() => { if (!huy) setDbInfo({ database: active.db ?? null, host: null, ma_csdt: null, connected: false }); });
    return () => { huy = true; };
  }, [active.db, active.id]);

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

          <nav className="px-2" aria-label="Phân hệ">
            {MODULES.map((m, idx) => {
              const on = m.id === active.id && !m.comingSoon;
              const a = ACCENT[m.accent];
              const nhom = NHOM_INFO[m.nhom];
              const dauNhom = idx === 0 || MODULES[idx - 1].nhom !== m.nhom;
              const tieuDe = dauNhom && (
                <div key={m.id + "-nhom"} className={idx === 0 ? "pt-1" : "mt-2 pt-2 border-t border-border"}>
                  {collapsed ? (
                    <div className="flex justify-center py-1" title={`${nhom.ten} · ${nhom.db}`}>
                      <span className={"w-1.5 h-1.5 rounded-full " + nhom.dot} />
                    </div>
                  ) : (
                    <div className="px-1.5 pb-1 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
                      <span className={"w-1.5 h-1.5 rounded-full shrink-0 " + nhom.dot} />
                      <span>{nhom.ten}</span>
                      <span className="font-mono normal-case tracking-normal text-[10px] text-muted-foreground/70 truncate">· {nhom.db}</span>
                    </div>
                  )}
                </div>
              );
              if (m.comingSoon) {
                return (
                  <div key={m.id}>
                    {tieuDe}
                    <div
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
                  </div>
                );
              }
              return (
                <div key={m.id}>
                  {tieuDe}
                  <NavLink
                    to={m.subnav[0]?.to ?? m.base}
                    title={collapsed ? `${m.label} · ${nhom.ten}` : undefined}
                    aria-current={on ? "page" : undefined}
                    className={
                      "group relative flex items-center gap-2.5 rounded-lg px-2.5 py-2 my-0.5 text-[13px] font-medium " +
                      "transition-all duration-150 motion-reduce:transition-none active:scale-[0.98] motion-reduce:active:scale-100 " +
                      "focus-visible:outline-none focus-visible:ring-2 " +
                      a.ring + " " +
                      (on ? a.activeItem + " font-semibold" : "text-foreground " + a.hover + " hover:translate-x-0.5 motion-reduce:hover:translate-x-0")
                    }
                  >
                    <span
                      className={
                        "absolute left-0 top-1.5 bottom-1.5 w-[3px] rounded-full origin-center transition-transform duration-200 motion-reduce:transition-none " +
                        a.rail + " " + (on ? "scale-y-100" : "scale-y-0")
                      }
                    />
                    <Icon name={m.icon} className="w-[18px] h-[18px] shrink-0" />
                    {!collapsed && <span className="truncate">{m.label}</span>}
                  </NavLink>
                </div>
              );
            })}
          </nav>

          {!collapsed && (
            <div className="mt-auto px-3 py-3 border-t border-border">
              <p className="text-[11px] text-muted-foreground leading-relaxed">
                Màu = CSDL đang ghi: <b className="text-primary">xanh</b> DB Nạp · <b className="text-sync">ngọc</b> cầu nối · <b className="text-kq">tím</b> DB đích.
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
              <span className={"shrink-0 rounded-full border px-2 py-px text-[10.5px] font-semibold " + NHOM_INFO[active.nhom].chip}>
                {NHOM_INFO[active.nhom].ten} · {NHOM_INFO[active.nhom].db}
              </span>
              <span>
                {active.dbNap ? (
                  <>
                    Phân hệ <b>{active.label}</b> ghi vào <b>CSDL: DB Nạp ({active.db})</b> — dùng chung với phần mềm
                    cũ, ghi thẳng vào hồ sơ thật.
                  </>
                ) : (
                  <>
                    Phân hệ <b>{active.label}</b> ghi vào <b>CSDL đích: {active.db}</b>
                    {dbInfo?.host && <> · máy <b>{dbInfo.host}</b></>}
                    {dbInfo?.ma_csdt && <> · CSĐT <b>{dbInfo.ma_csdt}</b></>}
                    {" "}— ghi thẳng vào hồ sơ thật.
                  </>
                )}
              </span>
              {/* Chip trạng thái: đang nối DB đích nào (user yêu cầu) */}
              {dbInfo && (
                dbInfo.connected ? (
                  <span className="ml-auto inline-flex items-center gap-1.5 rounded-full border border-success/40 bg-success/10 px-2 py-0.5 text-[12px] font-medium text-success whitespace-nowrap">
                    <span className="w-1.5 h-1.5 rounded-full bg-success" /> Đã kết nối DB đích
                  </span>
                ) : (
                  <span className="ml-auto inline-flex items-center gap-1.5 rounded-full border border-destructive/40 bg-destructive/10 px-2 py-0.5 text-[12px] font-medium text-destructive whitespace-nowrap">
                    <span className="w-1.5 h-1.5 rounded-full bg-destructive" /> Chưa kết nối DB đích
                  </span>
                )
              )}
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
