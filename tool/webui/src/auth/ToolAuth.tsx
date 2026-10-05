import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { coToken, datToken, kiemMoiTruong, toolDangNhap, toolDangXuat, toolMe } from "../lib/api";

export const NHAN_VAI_TRO: Record<string, string> = {
  operator: "Nhân viên nạp DB",
  admin: "Quản trị",
};

interface ToolNguoiDung {
  username: string;
  ho_ten: string | null;
  vai_tro: string;
}

interface ToolAuthCtx {
  user: ToolNguoiDung | null;
  dangKhoiTao: boolean; // đang khôi phục phiên từ token đã lưu (F5) → chưa biết login hay chưa
  daCauHinh: boolean | null; // null = đang hỏi backend; false = máy sạch → wizard (DGT-03)
  dangNhap: (username: string, password: string) => Promise<void>;
  dangXuat: () => Promise<void>;
}

const Ctx = createContext<ToolAuthCtx | null>(null);

export function ToolAuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<ToolNguoiDung | null>(null);
  const [dangKhoiTao, setDangKhoiTao] = useState(coToken()); // có token lưu → thử khôi phục trước
  const [daCauHinh, setDaCauHinh] = useState<boolean | null>(null);

  // Khôi phục phiên khi tải lại trang: có token lưu thì hỏi /me; token hết hạn thì xóa.
  useEffect(() => {
    if (!coToken()) return;
    let huy = false;
    toolMe()
      .then((me) => { if (!huy) setUser({ username: me.username, ho_ten: me.ho_ten, vai_tro: me.vai_tro }); })
      .catch(() => { if (!huy) datToken(null); })
      .finally(() => { if (!huy) setDangKhoiTao(false); });
    return () => { huy = true; };
  }, []);

  // DGT-03 — hỏi backend đã đủ cấu hình chưa (nhận 'máy sạch' → wizard).
  // Lỗi đọc (blip) → coi như đã cấu hình để KHÔNG đẩy nhầm vào wizard.
  useEffect(() => {
    let huy = false;
    kiemMoiTruong()
      .then((m) => { if (!huy) setDaCauHinh(m.da_cau_hinh); })
      .catch(() => { if (!huy) setDaCauHinh(true); });
    return () => { huy = true; };
  }, []);

  const dangNhap = useCallback(async (username: string, password: string) => {
    const kq = await toolDangNhap(username, password);
    datToken(kq.session_token);
    setUser({ username: kq.username, ho_ten: kq.ho_ten, vai_tro: kq.vai_tro });
    setDaCauHinh(true); // đăng nhập được nghĩa là đã có cấu hình
  }, []);

  const dangXuat = useCallback(async () => {
    try {
      await toolDangXuat();
    } finally {
      datToken(null);
      setUser(null);
      kiemMoiTruong().then((m) => setDaCauHinh(m.da_cau_hinh)).catch(() => setDaCauHinh(true));
    }
  }, []);

  const value = useMemo(
    () => ({ user, dangKhoiTao, daCauHinh, dangNhap, dangXuat }),
    [user, dangKhoiTao, daCauHinh, dangNhap, dangXuat],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useToolAuth(): ToolAuthCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useToolAuth phải nằm trong ToolAuthProvider");
  return ctx;
}
