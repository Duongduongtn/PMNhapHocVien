import { useLocation } from "react-router-dom";
import TraCuuDB from "./TraCuuDB";

// Bọc TraCuuDB thành route riêng /tool/tra-cuu (gộp 3 tab 1 hàng).
// Tham số "Xem trong DB" (từ màn Nạp hồ sơ: mở sẵn khóa đích + tô sáng HV vừa nạp)
// đi qua router state thay cho state nội bộ cũ. Vào tab trực tiếp → state null → tra cứu trống.
interface XemDBState {
  maKh?: string;
  maDks?: string[];
  nonce?: number;
  locAnh?: "all" | "chua" | "roi";
}

export default function TraCuuDBPage() {
  const { state } = useLocation() as { state: XemDBState | null };
  return (
    <TraCuuDB
      khoaMa={state?.maKh}
      noiBat={state?.maDks}
      moNonce={state?.nonce}
      locAnhBanDau={state?.locAnh}
    />
  );
}
