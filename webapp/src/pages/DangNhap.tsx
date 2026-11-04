import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Icon } from "../components/Icon";
import { useAuth } from "../auth/AuthContext";
import { ApiError } from "../lib/api";
import { NutGiaoDien } from "../components/NutGiaoDien";

// Bám bố cục ui-demo/src/pages/DangNhap.tsx: card giữa màn (tài khoản + mật khẩu + nút).
// Giao diện: dải xanh thương hiệu phía trên, thẻ đăng nhập nổi lên chồng vào dải.
export default function DangNhap() {
  const nav = useNavigate();
  const { dangNhap } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [hienMk, setHienMk] = useState(false);
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
    <div className="min-h-[100svh] bg-page flex flex-col">
      <div className="relative overflow-hidden bg-marca text-primary-foreground px-6 pt-14 pb-24 text-center">
        <span aria-hidden className="absolute -left-12 -top-16 w-48 h-48 rounded-full bg-white/10" />
        <span aria-hidden className="absolute -right-10 top-10 w-36 h-36 rounded-full bg-white/[.07]" />
        <span aria-hidden className="absolute left-1/3 -bottom-14 w-28 h-28 rounded-full bg-white/[.06]" />
        <NutGiaoDien tren="xanh" className="absolute right-3 top-3 z-10" />
        <div className="relative rise">
          <div className="w-16 h-16 rounded-2xl bg-white/15 ring-1 ring-white/25 flex items-center justify-center mx-auto mb-4">
            <Icon name="scan" className="w-8 h-8" />
          </div>
          <h1 className="text-xl font-bold">Đăng nhập hệ thống</h1>
          <p className="text-[13px] text-white/85 mt-1">Thu nhận hồ sơ học viên · CSDT 70004</p>
        </div>
      </div>

      <div className="flex-1 px-4 pb-8 -mt-14">
        <div className="relative mx-auto w-full max-w-sm bg-card border border-border rounded-2xl shadow-pop p-5 rise rise-1">
          <form className="space-y-3.5" onSubmit={submit}>
            <div>
              <label className="field-label" htmlFor="dn-tai-khoan">
                Tài khoản <span className="text-destructive">*</span>
              </label>
              <input
                id="dn-tai-khoan"
                className="field-input mt-1"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Tên đăng nhập"
                autoComplete="username"
                required
              />
            </div>
            <div>
              <label className="field-label" htmlFor="dn-mat-khau">
                Mật khẩu <span className="text-destructive">*</span>
              </label>
              <div className="relative mt-1">
                <input
                  id="dn-mat-khau"
                  type={hienMk ? "text" : "password"}
                  className="field-input pr-11"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Mật khẩu"
                  autoComplete="current-password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setHienMk((v) => !v)}
                  aria-label={hienMk ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                  aria-pressed={hienMk}
                  className="absolute right-1 top-1/2 -translate-y-1/2 w-10 h-10 rounded-lg flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted"
                >
                  <Icon name={hienMk ? "eyeOff" : "eye"} className="w-5 h-5" />
                </button>
              </div>
            </div>

            {loi && (
              <div role="alert" className="rounded-lg bg-destructive/10 border border-destructive/30 px-3 py-2 text-[13px] text-destructive flex items-start gap-2">
                <Icon name="warn" className="w-4 h-4 shrink-0 mt-0.5" /> {loi}
              </div>
            )}

            <button
              type="submit"
              disabled={dangGui}
              className="w-full h-12 rounded-xl bg-marca text-primary-foreground font-semibold text-sm flex items-center justify-center gap-2 hover:brightness-110 shadow-pop disabled:opacity-60 disabled:shadow-none"
            >
              <Icon name={dangGui ? "refresh" : "logout"} className={"w-4 h-4" + (dangGui ? " animate-spin" : "")} /> {dangGui ? "Đang đăng nhập…" : "Đăng nhập"}
            </button>
          </form>
        </div>

        <p className="mx-auto max-w-sm mt-4 px-2 text-center text-[12px] text-muted-foreground leading-relaxed rise rise-2">
          <b className="text-foreground">3 vai trò</b> (theo tài khoản, mỗi người một tài khoản): nhân viên thu nhận · nhân viên nạp DB · quản trị. Không đăng nhập Google/Zalo.
        </p>
      </div>
    </div>
  );
}
