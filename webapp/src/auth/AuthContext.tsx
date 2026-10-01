import { createContext, useCallback, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { datToken, dangNhap as apiDangNhap, dangXuat as apiDangXuat } from "../lib/api";
import type { NguoiDung } from "../lib/api";

// Nhãn vai trò hiển thị cho người dùng (TDD §5.3, 3 vai trò).
export const NHAN_VAI_TRO: Record<string, string> = {
  collector: "Nhân viên thu nhận",
  operator: "Nhân viên nạp DB",
  admin: "Quản trị",
};

interface AuthCtx {
  user: NguoiDung | null;
  dangNhap: (username: string, password: string) => Promise<void>;
  dangXuat: () => Promise<void>;
}

const Ctx = createContext<AuthCtx | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<NguoiDung | null>(null);

  const dangNhap = useCallback(async (username: string, password: string) => {
    const kq = await apiDangNhap(username, password);
    datToken(kq.access_token);
    setUser({ id: "", username: kq.username, ho_ten: kq.ho_ten, vai_tro: kq.vai_tro });
  }, []);

  const dangXuat = useCallback(async () => {
    try {
      await apiDangXuat(); // thu hồi phiên phía VPS (blocklist)
    } finally {
      datToken(null);
      setUser(null);
    }
  }, []);

  const value = useMemo(() => ({ user, dangNhap, dangXuat }), [user, dangNhap, dangXuat]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth(): AuthCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useAuth phải nằm trong AuthProvider");
  return ctx;
}
