import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Icon } from "../components/Icon";
import { NHAN_VAI_TRO, useAuth } from "../auth/AuthContext";
import { ApiError, doiMatKhau, layToolKey } from "../lib/api";

export default function TaiKhoan() {
  const { user, dangXuat } = useAuth();
  const nav = useNavigate();
  const laAdmin = user?.vai_tro === "admin";
  const [dangThoat, setDangThoat] = useState(false);

  async function thoat() {
    setDangThoat(true);
    await dangXuat();
    nav("/dang-nhap", { replace: true });
  }

  return (
    <div className="p-4 lg:p-6 max-w-lg space-y-4">
      <h1 className="text-lg font-bold">Tài khoản</h1>

      {/* Thông tin */}
      <div className="bg-card border border-border rounded-xl p-5">
        <div className="flex items-center gap-3">
          <span className="w-12 h-12 rounded-full bg-secondary flex items-center justify-center shrink-0">
            <Icon name="user" className="w-6 h-6 text-muted-foreground" />
          </span>
          <div className="min-w-0">
            <div className="text-base font-semibold truncate">{user?.ho_ten || user?.username}</div>
            <div className="text-[13px] text-muted-foreground truncate">
              @{user?.username} · {user ? (NHAN_VAI_TRO[user.vai_tro] ?? user.vai_tro) : "—"}
            </div>
          </div>
        </div>
      </div>

      <DoiMatKhau />

      {laAdmin && <KhoaKetNoiTool />}

      {laAdmin && (
        <Link
          to="/quan-ly-tai-khoan"
          className="bg-card border border-border rounded-xl p-4 flex items-center gap-3 hover:bg-muted/50 transition-colors"
        >
          <Icon name="user" className="w-5 h-5 text-muted-foreground" />
          <span className="font-medium text-sm flex-1">Quản lý tài khoản nhân viên</span>
          <Icon name="chevronRight" className="w-4 h-4 text-muted-foreground" />
        </Link>
      )}

      <button
        onClick={thoat}
        disabled={dangThoat}
        className="w-full h-11 rounded-lg bg-destructive/10 text-destructive font-semibold text-sm flex items-center justify-center gap-2 hover:bg-destructive/20 transition-colors disabled:opacity-60"
      >
        <Icon name="logout" className="w-4 h-4" /> {dangThoat ? "Đang đăng xuất…" : "Đăng xuất"}
      </button>
    </div>
  );
}

// HTG-06 — tự đổi mật khẩu
function DoiMatKhau() {
  const [htai, setHtai] = useState("");
  const [moi, setMoi] = useState("");
  const [lai, setLai] = useState("");
  const [dang, setDang] = useState(false);
  const [loi, setLoi] = useState("");
  const [ok, setOk] = useState(false);

  async function luu(e: React.FormEvent) {
    e.preventDefault();
    setLoi("");
    setOk(false);
    if (moi.length < 4) return setLoi("Mật khẩu mới phải từ 4 ký tự.");
    if (moi !== lai) return setLoi("Nhập lại mật khẩu không khớp.");
    setDang(true);
    try {
      await doiMatKhau(htai, moi);
      setOk(true);
      setHtai("");
      setMoi("");
      setLai("");
      setTimeout(() => setOk(false), 3000);
    } catch (err) {
      setLoi(err instanceof ApiError ? err.message : "Đổi mật khẩu không thành công.");
    } finally {
      setDang(false);
    }
  }

  return (
    <form onSubmit={luu} className="bg-card border border-border rounded-xl p-5 space-y-3">
      <h2 className="text-sm font-bold">Đổi mật khẩu</h2>
      <div>
        <label className="field-label">Mật khẩu hiện tại</label>
        <input type="password" autoComplete="current-password" className="field-input mt-1" value={htai} onChange={(e) => setHtai(e.target.value)} />
      </div>
      <div>
        <label className="field-label">Mật khẩu mới</label>
        <input type="password" autoComplete="new-password" className="field-input mt-1" value={moi} onChange={(e) => setMoi(e.target.value)} />
      </div>
      <div>
        <label className="field-label">Nhập lại mật khẩu mới</label>
        <input type="password" autoComplete="new-password" className="field-input mt-1" value={lai} onChange={(e) => setLai(e.target.value)} />
      </div>
      {loi && (
        <p className="text-[12px] text-destructive flex items-center gap-1"><Icon name="warn" className="w-3.5 h-3.5" /> {loi}</p>
      )}
      {ok && (
        <p className="text-[12px] text-success flex items-center gap-1"><Icon name="check" className="w-3.5 h-3.5" sw={3} /> Đã đổi mật khẩu.</p>
      )}
      <button
        type="submit"
        disabled={dang || !htai || !moi || !lai}
        className="h-10 px-5 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:brightness-110 transition-all disabled:opacity-60"
      >
        {dang ? "Đang đổi…" : "Đổi mật khẩu"}
      </button>
    </form>
  );
}

// HTG-04 — admin xem khóa kết nối tool (API key VPS). Chỉ tải key khi bấm Hiện/Sao chép.
function KhoaKetNoiTool() {
  const [key, setKey] = useState<string | null>(null);
  const [hien, setHien] = useState(false);
  const [dang, setDang] = useState(false);
  const [loi, setLoi] = useState("");
  const [daChep, setDaChep] = useState(false);

  async function tai(): Promise<string | null> {
    if (key !== null) return key;
    setDang(true);
    setLoi("");
    try {
      const k = (await layToolKey()).tool_key;
      setKey(k);
      return k;
    } catch (err) {
      setLoi(err instanceof ApiError ? err.message : "Không lấy được khóa.");
      return null;
    } finally {
      setDang(false);
    }
  }

  async function toggleHien() {
    if (!hien) {
      const k = await tai();
      if (k === null) return;
    }
    setHien((v) => !v);
  }

  async function saoChep() {
    const k = await tai();
    if (!k) return;
    try {
      await navigator.clipboard.writeText(k);
      setDaChep(true);
      setTimeout(() => setDaChep(false), 2000);
    } catch {
      setHien(true); // không copy được → hiện để chép tay
    }
  }

  return (
    <div className="bg-card border border-border rounded-xl p-5 space-y-2">
      <h2 className="text-sm font-bold flex items-center gap-2"><Icon name="key" className="w-4 h-4" /> Khóa kết nối tool (API key VPS)</h2>
      <div className="flex items-center gap-2">
        <code className="flex-1 min-w-0 truncate bg-muted rounded-lg px-3 py-2 text-[13px] tabular-nums">
          {hien ? (key ?? "…") : "••••••••••••••••"}
        </code>
        <button
          type="button"
          onClick={() => void toggleHien()}
          disabled={dang}
          className="h-9 px-3 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors inline-flex items-center gap-1.5 disabled:opacity-60"
        >
          <Icon name={hien ? "eyeOff" : "eye"} className="w-4 h-4" /> {hien ? "Ẩn" : "Hiện"}
        </button>
        <button
          type="button"
          onClick={() => void saoChep()}
          disabled={dang}
          className="h-9 px-3 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:brightness-110 transition-all inline-flex items-center gap-1.5 disabled:opacity-60"
        >
          <Icon name="copy" className="w-4 h-4" /> {daChep ? "Đã chép" : "Sao chép"}
        </button>
      </div>
      {loi ? (
        <p className="text-[12px] text-destructive flex items-center gap-1"><Icon name="warn" className="w-3.5 h-3.5" /> {loi}</p>
      ) : (
        <p className="text-[11px] text-muted-foreground">Dán vào tool nạp DB → Cấu hình → ô API key VPS. Giữ kín, không gửi cho người ngoài.</p>
      )}
    </div>
  );
}
