import { useNavigate } from "react-router-dom";
import { Icon } from "../../components/Icon";

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex justify-between gap-3 text-[13px] border-b border-border py-2.5 last:border-0">
      <span className="text-muted-foreground shrink-0">{k}</span>
      <span className="font-medium text-right">{v}</span>
    </div>
  );
}

export default function TaiKhoan() {
  const nav = useNavigate();
  return (
    <div className="lg:p-6 lg:max-w-lg lg:mx-auto">
      <div className="p-4 lg:p-0">
        <div className="flex items-center gap-2 mb-4">
          <h2 className="text-base font-bold">Tài khoản</h2>
          <span className="text-[11px] font-semibold text-primary bg-primary/10 rounded-full px-2 py-0.5">HTG-01</span>
        </div>

        {/* Thẻ người dùng */}
        <div className="rounded-xl border border-border bg-card p-5 flex items-center gap-4">
          <span className="w-16 h-16 rounded-2xl bg-primary text-primary-foreground flex items-center justify-center shrink-0">
            <Icon name="user" className="w-8 h-8" />
          </span>
          <div className="min-w-0">
            <div className="text-lg font-bold truncate">Trần Thị Hoa</div>
            <span className="inline-flex items-center gap-1 text-[12px] font-semibold text-primary bg-primary/10 rounded-full px-2 py-0.5 mt-1">Nhân viên thu nhận</span>
          </div>
        </div>

        {/* Thông tin */}
        <div className="rounded-xl border border-border bg-card p-4 mt-4">
          <h3 className="text-[13px] font-bold mb-1">Thông tin tài khoản</h3>
          <Row k="Tên đăng nhập" v="nvthu01" />
          <Row k="Vai trò" v="Nhân viên thu nhận (collector)" />
          <Row k="Cơ sở đào tạo" v="CSDT 70004" />
          <Row k="Đăng nhập lần cuối" v="30/09/2026 08:05" />
        </div>

        {/* Hành động */}
        <div className="mt-4 space-y-2">
          <button className="w-full h-11 rounded-lg border border-border bg-card text-foreground font-semibold text-sm flex items-center justify-center gap-2 hover:bg-muted transition-colors">
            <Icon name="settings" className="w-4 h-4" /> Đổi mật khẩu
          </button>
          <button onClick={() => nav("/")} className="w-full h-11 rounded-lg bg-destructive/10 text-destructive border border-destructive/30 font-semibold text-sm flex items-center justify-center gap-2 hover:bg-destructive/15 transition-colors">
            <Icon name="logout" className="w-4 h-4" /> Đăng xuất
          </button>
        </div>

        <p className="text-[11px] text-muted-foreground text-center mt-4">Mỗi người một tài khoản (không dùng chung) để truy vết ai gửi/ai nạp — HTG-01, BR-020.</p>
      </div>
    </div>
  );
}
