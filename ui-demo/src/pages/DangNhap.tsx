import { useNavigate } from "react-router-dom";
import { Icon } from "../components/Icon";

export default function DangNhap() {
  const nav = useNavigate();
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

        <form
          className="space-y-3"
          onSubmit={(e) => {
            e.preventDefault();
            nav("/");
          }}
        >
          <div>
            <label className="field-label">Tài khoản <span className="text-destructive">*</span></label>
            <input className="field-input mt-1" defaultValue="nvnap01" placeholder="Tên đăng nhập" />
          </div>
          <div>
            <label className="field-label">Mật khẩu <span className="text-destructive">*</span></label>
            <input type="password" className="field-input mt-1" defaultValue="matkhau" placeholder="Mật khẩu" />
          </div>
          <button type="submit" className="w-full h-11 rounded-lg bg-primary text-primary-foreground font-semibold text-sm flex items-center justify-center gap-2 hover:brightness-110 transition-all shadow-sm">
            <Icon name="logout" className="w-4 h-4" /> Đăng nhập
          </button>
        </form>

        <div className="mt-4 rounded-lg bg-secondary/60 border border-border p-3 text-[12px] text-muted-foreground leading-relaxed">
          <b className="text-foreground">3 vai trò</b> (theo tài khoản, mỗi người một tài khoản): nhân viên thu nhận · nhân viên nạp DB · quản trị. Không đăng nhập Google/Zalo (HTG-01).
        </div>

        <button onClick={() => nav("/")} className="mt-4 w-full text-center text-[12px] text-muted-foreground hover:text-primary transition-colors">
          ← Về trang chọn app
        </button>
      </div>
    </div>
  );
}
