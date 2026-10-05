import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { coToken, datToken, toolDangNhap, toolDangXuat, toolMe } from "../lib/api";

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
  dangNhap: (username: string, password: string) => Promise<void>;
  dangXuat: () => Promise<void>;
}

const Ctx = createContext<ToolAuthCtx | null>(null);

export function ToolAuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<ToolNguoiDung | null>(null);
  const [dangKhoiTao, setDangKhoiTao] = useState(coToken()); // có token lưu → thử khôi phục trước

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

  const dangNhap = useCallback(async (username: string, password: string) => {
    const kq = await toolDangNhap(username, password);
    datToken(kq.session_token);
    setUser({ username: kq.username, ho_ten: kq.ho_ten, vai_tro: kq.vai_tro });
  }, []);

  const dangXuat = useCallback(async () => {
    try {
      await toolDangXuat();
    } finally {
      datToken(null);
      setUser(null);
    }
  }, []);

  const value = useMemo(() => ({ user, dangKhoiTao, dangNhap, dangXuat }), [user, dangKhoiTao, dangNhap, dangXuat]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useToolAuth(): ToolAuthCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useToolAuth phải nằm trong ToolAuthProvider");
  return ctx;
}
