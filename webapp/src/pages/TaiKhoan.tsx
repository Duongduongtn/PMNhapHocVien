import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Icon } from "../components/Icon";
import { NHAN_VAI_TRO, useAuth } from "../auth/AuthContext";

export default function TaiKhoan() {
  const { user, dangXuat } = useAuth();
  const nav = useNavigate();
  const [dangThoat, setDangThoat] = useState(false);

  async function thoat() {
    setDangThoat(true);
    await dangXuat();
    nav("/dang-nhap", { replace: true });
  }

  return (
    <div className="p-4 lg:p-6 max-w-lg">
      <h1 className="text-lg font-bold mb-4">Tài khoản</h1>

      <div className="bg-card border border-border rounded-xl p-5 space-y-4">
        <div className="flex items-center gap-3">
          <span className="w-12 h-12 rounded-full bg-secondary flex items-center justify-center shrink-0">
            <Icon name="user" className="w-6 h-6 text-muted-foreground" />
          </span>
          <div className="min-w-0">
            <div className="text-base font-semibold truncate">{user?.ho_ten || user?.username}</div>
            <div className="text-[13px] text-muted-foreground truncate">@{user?.username}</div>
          </div>
        </div>

        <div className="flex items-center justify-between border-t border-border pt-3 text-sm">
          <span className="text-muted-foreground">Vai trò</span>
          <span className="font-medium">{user ? (NHAN_VAI_TRO[user.vai_tro] ?? user.vai_tro) : "—"}</span>
        </div>

        <button
          onClick={thoat}
          disabled={dangThoat}
          className="w-full h-11 rounded-lg bg-destructive/10 text-destructive font-semibold text-sm flex items-center justify-center gap-2 hover:bg-destructive/20 transition-colors disabled:opacity-60"
        >
          <Icon name="logout" className="w-4 h-4" /> {dangThoat ? "Đang đăng xuất…" : "Đăng xuất"}
        </button>
      </div>
    </div>
  );
}
