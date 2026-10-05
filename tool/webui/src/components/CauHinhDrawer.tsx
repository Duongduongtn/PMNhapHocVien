import { useEffect } from "react";
import { Icon } from "./Icon";
import CauHinhForm from "./CauHinhForm";

// Drawer ⚙ trên header (HTG-07, CHANGES #34) — vỏ trượt phải bọc <CauHinhForm/>.
// Nội dung form (2 khối config) tách ra CauHinhForm để dùng chung với Wizard (DGT-03).

export default function CauHinhDrawer({ open, onClose }: { open: boolean; onClose: () => void }) {
  // Đóng bằng phím Esc.
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  return (
    <div
      className={
        "fixed inset-0 z-50 transition-opacity duration-200 " +
        (open ? "opacity-100" : "opacity-0 pointer-events-none")
      }
      aria-hidden={!open}
    >
      {/* Nền mờ */}
      <div className="absolute inset-0 bg-foreground/30" onClick={onClose} />

      {/* Drawer trượt phải */}
      <aside
        role="dialog"
        aria-modal="true"
        aria-label="Cấu hình kết nối"
        className={
          "absolute right-0 top-0 h-full w-[580px] max-w-[94vw] bg-background border-l border-border " +
          "shadow-[-8px_0_28px_-12px_hsl(222_47%_11%/0.25)] flex flex-col " +
          "transition-transform duration-200 ease-out " +
          (open ? "translate-x-0" : "translate-x-full")
        }
      >
        {/* Tiêu đề drawer */}
        <header className="shrink-0 h-14 px-5 flex items-center gap-2.5 border-b border-border bg-card">
          <Icon name="settings" className="w-[18px] h-[18px] text-foreground" />
          <div className="min-w-0">
            <h2 className="text-[15px] font-bold leading-tight">Cấu hình kết nối</h2>
            <p className="text-[11.5px] text-muted-foreground leading-tight">Dùng chung cho cả tool · lưu mã hóa cục bộ</p>
          </div>
          <button
            onClick={onClose}
            aria-label="Đóng"
            className="ml-auto w-8 h-8 grid place-items-center rounded-lg text-muted-foreground hover:bg-muted hover:text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <Icon name="x" className="w-[18px] h-[18px]" />
          </button>
        </header>

        {/* Nội dung cuộn — form dùng chung */}
        <div className="flex-1 min-h-0 overflow-y-auto px-5 py-4">
          <CauHinhForm active={open} />
        </div>
      </aside>
    </div>
  );
}
