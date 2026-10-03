import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Icon } from "../components/Icon";
import { useAuth } from "../auth/AuthContext";
import { ApiError } from "../lib/api";

// Bám bố cục ui-demo/src/pages/DangNhap.tsx: card giữa màn (tài khoản + mật khẩu + nút).
export default function DangNhap() {
  const nav = useNavigate();
  const { dangNhap } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loi, setLoi] = useState<string | null>(null);
  const [dangGui, setDangGui] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoi(null);
    setDangGui(true);
    try {
      await dangNhap(username.trim(), password);
      nav("/quet", { replace: true });
    } catch (err) {
      setLoi(err instanceof ApiError ? err.message : "Không kết nối được máy chủ");
    } finally {
      setDangGui(false);
    }
  }

  return (
    <div className="min-h-screen bg-[hsl(210_40%_96%)] flex items-center justify-center p-4">
      <div className="w-full max-w-sm bg-card border border-border rounded-xl shadow-sm p-6">
        <div className="text-center mb-5">
          <div className="w-14 h-14 rounded-2xl bg-primary text-primary-foreground flex items-center justify-center mx-auto mb-3">
            <Icon name="scan" className="w-7 h-7" />
          </div>
          <h1 className="text-lg font-bold">Đăng nhập hệ thống</h1>
          <p className="text-[12px] text-muted-foreground mt-1">Thu nhận hồ sơ học viên · CSDT 70004</p>
        </div>

        <form className="space-y-3" onSubmit={submit}>
          <div>
            <label className="field-label">
              Tài khoản <span className="text-destructive">*</span>
            </label>
            <input
              className="field-input mt-1"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Tên đăng nhập"
              autoComplete="username"
              required
            />
          </div>
          <div>
            <label className="field-label">
              Mật khẩu <span className="text-destructive">*</span>
            </label>
            <input
              type="password"
              className="field-input mt-1"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Mật khẩu"
              autoComplete="current-password"
              required
            />
          </div>

          {loi && (
            <div className="rounded-lg bg-destructive/10 border border-destructive/30 px-3 py-2 text-[13px] text-destructive">
              {loi}
            </div>
          )}

          <button
            type="submit"
            disabled={dangGui}
            className="w-full h-11 rounded-lg bg-primary text-primary-foreground font-semibold text-sm flex items-center justify-center gap-2 hover:brightness-110 transition shadow-sm disabled:opacity-60"
          >
            <Icon name="logout" className="w-4 h-4" /> {dangGui ? "Đang đăng nhập…" : "Đăng nhập"}
          </button>
        </form>

        <div className="mt-4 rounded-lg bg-secondary/60 border border-border p-3 text-[12px] text-muted-foreground leading-relaxed">
          <b className="text-foreground">3 vai trò</b> (theo tài khoản, mỗi người một tài khoản): nhân viên thu nhận · nhân viên nạp DB · quản trị. Không đăng nhập Google/Zalo.
        </div>
      </div>
    </div>
  );
}
