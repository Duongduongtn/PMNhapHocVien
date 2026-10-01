import { createContext, useCallback, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { datToken, toolDangNhap, toolDangXuat } from "../lib/api";

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
  dangNhap: (username: string, password: string) => Promise<void>;
  dangXuat: () => Promise<void>;
}

const Ctx = createContext<ToolAuthCtx | null>(null);

export function ToolAuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<ToolNguoiDung | null>(null);

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

  const value = useMemo(() => ({ user, dangNhap, dangXuat }), [user, dangNhap, dangXuat]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useToolAuth(): ToolAuthCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useToolAuth phải nằm trong ToolAuthProvider");
  return ctx;
}
