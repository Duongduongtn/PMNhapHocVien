import { useState } from "react";
import { Icon } from "../../components/Icon";
import { useToolAuth } from "../../auth/ToolAuth";
import { useConfigDrawer } from "../../lib/configDrawer";

// Cổng đăng nhập tool (HTG-01③). Đăng nhập xác thực qua VPS; chưa cấu hình URL VPS
// thì vào Cấu hình trước (A1 — màn Cấu hình không cần đăng nhập).
export default function DangNhap() {
  const { dangNhap } = useToolAuth();
  const { open: moCauHinh } = useConfigDrawer();
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
    } catch (err) {
      setLoi(err instanceof Error ? err.message : "Không đăng nhập được");
    } finally {
      setDangGui(false);
    }
  }

  return (
    <div className="p-8 flex justify-center">
      <div className="w-full max-w-sm">
        <div className="text-center mb-5">
          <div className="w-14 h-14 rounded-2xl bg-primary text-primary-foreground flex items-center justify-center mx-auto mb-3">
            <Icon name="file" className="w-7 h-7" />
          </div>
          <h1 className="text-lg font-bold">Đăng nhập tool nạp DB</h1>
          <p className="text-[12px] text-muted-foreground mt-1">Chỉ nhân viên nạp DB hoặc quản trị</p>
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
            className="w-full h-11 rounded-lg bg-primary text-primary-foreground font-semibold text-sm flex items-center justify-center gap-2 hover:brightness-110 transition-all shadow-sm disabled:opacity-60"
          >
            <Icon name="logout" className="w-4 h-4" /> {dangGui ? "Đang đăng nhập…" : "Đăng nhập"}
          </button>
        </form>

        <div className="mt-4 text-center text-[12px] text-muted-foreground">
          Chưa đặt kết nối VPS?{" "}
          <button type="button" onClick={moCauHinh} className="text-primary font-medium hover:underline">
            Vào Cấu hình
          </button>
        </div>
      </div>
    </div>
  );
}
