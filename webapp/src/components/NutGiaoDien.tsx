import { Icon } from "./Icon";
import { useGiaoDien } from "../lib/theme";

// Nút đổi sáng/tối (HTG-08). `tren="xanh"`: đặt trên dải xanh thương hiệu (nền trắng mờ); `tren="thuong"`: đặt trên nền thường.
// Hiện biểu tượng của chế độ SẼ chuyển sang: đang tối thì hiện mặt trời, đang sáng thì hiện mặt trăng.
export function NutGiaoDien({ tren = "thuong", className = "" }: { tren?: "xanh" | "thuong"; className?: string }) {
  const { che, doi } = useGiaoDien();
  const toi = che === "toi";
  const nhan = toi ? "Chuyển sang chế độ sáng" : "Chuyển sang chế độ tối";
  return (
    <button
      type="button"
      onClick={doi}
      aria-label={nhan}
      title={nhan}
      data-testid="nut-giao-dien"
      className={
        "w-10 h-10 rounded-full flex items-center justify-center shrink-0 " +
        (tren === "xanh" ? "bg-white/15 text-white hover:bg-white/25" : "text-muted-foreground hover:bg-muted hover:text-foreground") +
        " " + className
      }
    >
      <Icon name={toi ? "sun" : "moon"} className="w-5 h-5" />
    </button>
  );
}
