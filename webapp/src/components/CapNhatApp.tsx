import { useRegisterSW } from "virtual:pwa-register/react";
import { Icon } from "./Icon";

// Banner "Có bản mới — Tải lại" (CHANGES #12). Mỗi lần deploy, service worker tải bản mới ở nền;
// báo cho nhân viên bấm Tải lại thay vì phải xóa cache tay. Kiểm bản mới mỗi 60 giây.
export default function CapNhatApp() {
  const {
    needRefresh: [canTaiLai, boQua],
    updateServiceWorker,
  } = useRegisterSW({
    onRegisteredSW(_url, reg) {
      if (reg) setInterval(() => void reg.update(), 60_000);
    },
  });

  if (!canTaiLai) return null;

  return (
    <div
      className="fixed inset-x-0 top-0 z-[60] bg-primary text-primary-foreground text-[13px] px-4 py-2.5 flex items-center justify-center gap-3 shadow-lg"
      style={{ paddingTop: "calc(0.625rem + env(safe-area-inset-top, 0px))" }}
      role="alert"
    >
      <Icon name="refresh" className="w-4 h-4 shrink-0" />
      <span className="font-medium">Có bản cập nhật mới</span>
      <button onClick={() => void updateServiceWorker(true)} className="font-bold underline underline-offset-2">
        Tải lại
      </button>
      <button onClick={() => boQua(false)} aria-label="Bỏ qua" className="ml-1 opacity-80 hover:opacity-100">
        <Icon name="x" className="w-4 h-4" />
      </button>
    </div>
  );
}
