// Đăng ký phân hệ của tool. Thêm phân hệ mới = thêm 1 phần tử vào MODULES
// (không sửa khung ToolLayout). Mỗi phân hệ có sub-nav riêng, màu nhấn, và
// CSDL mà nó ghi vào (banner nhắc để tránh thao tác nhầm giữa các phân hệ).

export type Accent = "primary" | "sync";

export interface SubNav {
  to: string;
  label: string;
  icon: string; // tên trong bộ Icon
}

export interface ModuleDef {
  id: string;
  label: string;
  icon: string;
  accent: Accent;
  /** Tiền tố route để xác định phân hệ đang mở. */
  base: string;
  /** Tên CSDL phân hệ ghi vào — hiện ở banner nhắc. Bỏ trống nếu không ghi DB. */
  db?: string;
  subnav: SubNav[];
  /** Phân hệ dự kiến, chưa dựng — hiện mờ, không bấm được. */
  comingSoon?: boolean;
}

export const MODULES: ModuleDef[] = [
  {
    id: "nap",
    label: "Nạp hồ sơ",
    icon: "file",
    accent: "primary",
    base: "/tool",
    subnav: [
      { to: "/tool/nap", label: "Nạp hồ sơ", icon: "file" },
      { to: "/tool/tao-khoa", label: "Tạo khóa", icon: "plus" },
    ],
  },
  {
    id: "sync",
    label: "Đồng bộ CDB",
    icon: "refresh",
    accent: "sync",
    base: "/sync",
    db: "GPLX_CDB_CSDT",
    subnav: [
      { to: "/sync/ban-dong-bo", label: "Bàn đồng bộ", icon: "refresh" },
      { to: "/sync/lich-su", label: "Lịch sử & Hủy sync", icon: "clock" },
    ],
  },
  {
    id: "ketqua",
    label: "Kết quả học tập",
    icon: "check",
    accent: "primary",
    base: "/ket-qua",
    subnav: [],
    comingSoon: true,
  },
];

/** Phân hệ ứng với đường dẫn hiện tại (so khớp tiền tố `base` dài nhất). */
export function moduleForPath(pathname: string): ModuleDef {
  const match = [...MODULES]
    .filter((m) => !m.comingSoon)
    .sort((a, b) => b.base.length - a.base.length)
    .find((m) => pathname === m.base || pathname.startsWith(m.base + "/"));
  return match ?? MODULES[0];
}
