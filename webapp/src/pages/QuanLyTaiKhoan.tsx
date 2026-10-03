import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Icon } from "../components/Icon";
import { NHAN_VAI_TRO, useAuth } from "../auth/AuthContext";
import {
  ApiError,
  dsTaiKhoan,
  taoTaiKhoan,
  suaTaiKhoan,
  resetMatKhauTaiKhoan,
  type TaiKhoan,
} from "../lib/api";

// HTG-05 — admin quản lý tài khoản nhân viên: danh sách (phân trang) + tạo + reset mật khẩu
// + khóa/mở. Không xóa cứng (giữ dấu vết PII). Chỉ admin (RequireAuth + server require_role).
const VAI_TRO_CHON = [
  { v: "collector", nhan: "Thu nhận hồ sơ" },
  { v: "operator", nhan: "Nạp DB (dùng tool)" },
  { v: "admin", nhan: "Quản trị" },
];

function matKhauNgauNhien(): string {
  const bang = "ABCDEFGHJKMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789";
  return Array.from({ length: 10 }, () => bang[Math.floor(Math.random() * bang.length)]).join("");
}

export default function QuanLyTaiKhoan() {
  const { user } = useAuth();
  const nav = useNavigate();
  const [rows, setRows] = useState<TaiKhoan[]>([]);
  const [total, setTotal] = useState(0);
  const [coTrang, setCoTrang] = useState(20);
  const [trang, setTrang] = useState(0); // 0-based
  const [dang, setDang] = useState(false);
  const [loi, setLoi] = useState("");
  const [moTao, setMoTao] = useState(false);
  const [reset, setReset] = useState<TaiKhoan | null>(null);
  const [okMsg, setOkMsg] = useState("");

  const tai = useCallback(async () => {
    setDang(true);
    setLoi("");
    try {
      const kq = await dsTaiKhoan(coTrang, trang * coTrang);
      setRows(kq.items);
      setTotal(kq.total);
    } catch (err) {
      setLoi(err instanceof ApiError ? err.message : "Không tải được danh sách.");
    } finally {
      setDang(false);
    }
  }, [coTrang, trang]);

  useEffect(() => {
    void tai();
  }, [tai]);

  function bao(msg: string) {
    setOkMsg(msg);
    setTimeout(() => setOkMsg(""), 2500);
  }

  async function doiKhoa(tk: TaiKhoan) {
    try {
      await suaTaiKhoan(tk.id, { is_active: !tk.is_active });
      bao(tk.is_active ? "Đã khóa tài khoản." : "Đã mở tài khoản.");
      void tai();
    } catch (err) {
      setLoi(err instanceof ApiError ? err.message : "Không đổi được trạng thái.");
    }
  }

  const soTrang = Math.max(1, Math.ceil(total / coTrang));
  const tu = total === 0 ? 0 : trang * coTrang + 1;
  const den = Math.min(total, (trang + 1) * coTrang);

  return (
    <div className="p-4 lg:p-6 max-w-3xl space-y-4">
      <div className="flex items-center gap-2 flex-wrap">
        <button onClick={() => nav("/tai-khoan")} className="inline-flex items-center gap-1 text-[13px] text-primary font-medium hover:underline">
          <Icon name="chevronLeft" className="w-4 h-4" /> Tài khoản
        </button>
        <h1 className="text-lg font-bold flex-1">Quản lý tài khoản</h1>
        <button
          onClick={() => setMoTao(true)}
          className="h-10 px-4 rounded-lg bg-primary text-primary-foreground font-semibold text-sm inline-flex items-center gap-1.5 hover:brightness-110 transition shadow-sm"
        >
          <Icon name="plus" className="w-4 h-4" sw={2.5} /> Tạo nhân viên
        </button>
      </div>

      {okMsg && (
        <div className="flex items-center gap-2 text-[13px] text-success bg-success/10 border border-success/30 rounded-lg px-3 py-2">
          <Icon name="check" className="w-4 h-4 shrink-0" sw={3} /> {okMsg}
        </div>
      )}
      {loi && (
        <div className="flex items-center gap-2 text-[13px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2">
          <Icon name="warn" className="w-4 h-4 shrink-0" /> {loi}
        </div>
      )}

      <div className="border border-border rounded-xl overflow-hidden">
        <table className="w-full text-[13px]">
          <thead>
            <tr className="bg-muted text-muted-foreground text-left">
              <th className="px-3 py-2 font-semibold">Tên</th>
              <th className="px-3 py-2 font-semibold">Tài khoản</th>
              <th className="px-3 py-2 font-semibold">Vai trò</th>
              <th className="px-3 py-2 font-semibold">Trạng thái</th>
              <th className="px-3 py-2 font-semibold text-right">Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((tk) => {
              const laMinh = tk.username === user?.username;
              return (
                <tr key={tk.id} className="border-t border-border">
                  <td className="px-3 py-2 font-medium">{tk.ho_ten || "—"}</td>
                  <td className="px-3 py-2">@{tk.username}</td>
                  <td className="px-3 py-2">{NHAN_VAI_TRO[tk.vai_tro] ?? tk.vai_tro}</td>
                  <td className="px-3 py-2">
                    {tk.is_active ? (
                      <span className="text-success font-medium">● Hoạt động</span>
                    ) : (
                      <span className="text-muted-foreground">● Đã khóa</span>
                    )}
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex items-center justify-end gap-1">
                      <button
                        onClick={() => setReset(tk)}
                        className="h-8 px-2.5 rounded-md border border-border text-[12px] font-medium hover:bg-muted transition-colors inline-flex items-center gap-1"
                      >
                        <Icon name="key" className="w-3.5 h-3.5" /> Đổi MK
                      </button>
                      <button
                        onClick={() => void doiKhoa(tk)}
                        disabled={laMinh}
                        title={laMinh ? "Không thể khóa tài khoản đang đăng nhập" : ""}
                        className="h-8 px-2.5 rounded-md border border-border text-[12px] font-medium hover:bg-muted transition-colors inline-flex items-center gap-1 disabled:opacity-40"
                      >
                        <Icon name={tk.is_active ? "lock" : "unlock"} className="w-3.5 h-3.5" /> {tk.is_active ? "Khóa" : "Mở"}
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {dang && <div className="px-4 py-6 text-center text-sm text-muted-foreground"><Icon name="refresh" className="w-4 h-4 animate-spin inline mr-1" /> Đang tải…</div>}
        {!dang && !rows.length && <div className="px-4 py-6 text-center text-sm text-muted-foreground">Chưa có tài khoản.</div>}
      </div>

      {/* Phân trang */}
      <div className="flex items-center justify-between gap-2 flex-wrap text-[13px]">
        <span className="text-muted-foreground tabular-nums">{tu}–{den} / {total}</span>
        <div className="flex items-center gap-2">
          <button onClick={() => setTrang((t) => Math.max(0, t - 1))} disabled={trang === 0}
            className="h-8 w-8 rounded-md border border-border inline-flex items-center justify-center hover:bg-muted transition-colors disabled:opacity-40">
            <Icon name="chevronLeft" className="w-4 h-4" />
          </button>
          <span className="tabular-nums">Trang {trang + 1}/{soTrang}</span>
          <button onClick={() => setTrang((t) => (t + 1 < soTrang ? t + 1 : t))} disabled={trang + 1 >= soTrang}
            className="h-8 w-8 rounded-md border border-border inline-flex items-center justify-center hover:bg-muted transition-colors disabled:opacity-40">
            <Icon name="chevronRight" className="w-4 h-4" />
          </button>
          <select value={coTrang} onChange={(e) => { setCoTrang(Number(e.target.value)); setTrang(0); }}
            className="h-8 rounded-md border border-border bg-card px-2 text-[13px]">
            {[20, 50, 100].map((n) => <option key={n} value={n}>{n}/trang</option>)}
          </select>
        </div>
      </div>

      {moTao && <TaoNhanVien onDong={() => setMoTao(false)} onXong={(msg) => { setMoTao(false); bao(msg); setTrang(0); void tai(); }} />}
      {reset && <ResetMatKhau tk={reset} onDong={() => setReset(null)} onXong={(msg) => { setReset(null); bao(msg); }} />}
    </div>
  );
}

function TaoNhanVien({ onDong, onXong }: { onDong: () => void; onXong: (msg: string) => void }) {
  const [hoTen, setHoTen] = useState("");
  const [username, setUsername] = useState("");
  const [vaiTro, setVaiTro] = useState("collector");
  const [matKhau, setMatKhau] = useState("");
  const [dang, setDang] = useState(false);
  const [loi, setLoi] = useState("");

  async function tao(e: React.FormEvent) {
    e.preventDefault();
    setLoi("");
    if (!username.trim()) return setLoi("Chưa nhập tài khoản.");
    if (matKhau.length < 4) return setLoi("Mật khẩu phải từ 4 ký tự.");
    setDang(true);
    try {
      await taoTaiKhoan({ username: username.trim(), password: matKhau, ho_ten: hoTen.trim() || null, vai_tro: vaiTro });
      onXong("Đã tạo tài khoản.");
    } catch (err) {
      setLoi(err instanceof ApiError ? err.message : "Tạo không thành công.");
    } finally {
      setDang(false);
    }
  }

  return (
    <Modal tieuDe="Tạo nhân viên" onDong={onDong}>
      <form onSubmit={tao} className="p-5 space-y-3">
        <div>
          <label className="field-label">Họ và tên</label>
          <input autoFocus className="field-input mt-1" value={hoTen} onChange={(e) => setHoTen(e.target.value)} />
        </div>
        <div>
          <label className="field-label">Tài khoản (username)</label>
          <input className="field-input mt-1" value={username} onChange={(e) => setUsername(e.target.value.replace(/\s/g, ""))} autoComplete="off" />
        </div>
        <div>
          <label className="field-label">Vai trò</label>
          <select className="field-input mt-1" value={vaiTro} onChange={(e) => setVaiTro(e.target.value)}>
            {VAI_TRO_CHON.map((r) => <option key={r.v} value={r.v}>{r.nhan}</option>)}
          </select>
        </div>
        <div>
          <label className="field-label">Mật khẩu ban đầu</label>
          <div className="flex gap-2 mt-1">
            <input className="field-input" value={matKhau} onChange={(e) => setMatKhau(e.target.value)} autoComplete="off" />
            <button type="button" onClick={() => setMatKhau(matKhauNgauNhien())} className="h-[38px] px-3 rounded-lg border border-border text-[13px] font-medium hover:bg-muted transition-colors whitespace-nowrap">
              Ngẫu nhiên
            </button>
          </div>
        </div>
        {loi && <p className="text-[12px] text-destructive flex items-center gap-1"><Icon name="warn" className="w-3.5 h-3.5" /> {loi}</p>}
        <div className="flex gap-2 pt-1">
          <button type="button" onClick={onDong} className="h-10 px-4 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors">Hủy</button>
          <button type="submit" disabled={dang} className="ml-auto h-10 px-5 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:brightness-110 transition disabled:opacity-60">
            {dang ? "Đang tạo…" : "Tạo"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function ResetMatKhau({ tk, onDong, onXong }: { tk: TaiKhoan; onDong: () => void; onXong: (msg: string) => void }) {
  const [matKhau, setMatKhau] = useState("");
  const [dang, setDang] = useState(false);
  const [loi, setLoi] = useState("");

  async function luu(e: React.FormEvent) {
    e.preventDefault();
    setLoi("");
    if (matKhau.length < 4) return setLoi("Mật khẩu phải từ 4 ký tự.");
    setDang(true);
    try {
      await resetMatKhauTaiKhoan(tk.id, matKhau);
      onXong("Đã đặt mật khẩu mới.");
    } catch (err) {
      setLoi(err instanceof ApiError ? err.message : "Đặt mật khẩu không thành công.");
    } finally {
      setDang(false);
    }
  }

  return (
    <Modal tieuDe={`Đổi mật khẩu — @${tk.username}`} onDong={onDong}>
      <form onSubmit={luu} className="p-5 space-y-3">
        <div>
          <label className="field-label">Mật khẩu mới</label>
          <div className="flex gap-2 mt-1">
            <input autoFocus className="field-input" value={matKhau} onChange={(e) => setMatKhau(e.target.value)} autoComplete="off" />
            <button type="button" onClick={() => setMatKhau(matKhauNgauNhien())} className="h-[38px] px-3 rounded-lg border border-border text-[13px] font-medium hover:bg-muted transition-colors whitespace-nowrap">
              Ngẫu nhiên
            </button>
          </div>
          <p className="text-[11px] text-muted-foreground mt-1">Báo mật khẩu mới cho nhân viên; họ tự đổi lại sau.</p>
        </div>
        {loi && <p className="text-[12px] text-destructive flex items-center gap-1"><Icon name="warn" className="w-3.5 h-3.5" /> {loi}</p>}
        <div className="flex gap-2 pt-1">
          <button type="button" onClick={onDong} className="h-10 px-4 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors">Hủy</button>
          <button type="submit" disabled={dang} className="ml-auto h-10 px-5 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:brightness-110 transition disabled:opacity-60">
            {dang ? "Đang lưu…" : "Đặt mật khẩu"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function Modal({ tieuDe, onDong, children }: { tieuDe: string; onDong: () => void; children: React.ReactNode }) {
  return (
    <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={(e) => { if (e.target === e.currentTarget) onDong(); }}>
      <div className="bg-card w-full max-w-md rounded-xl shadow-2xl max-h-[90vh] flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-5 py-3 border-b border-border">
          <h3 className="font-bold text-sm">{tieuDe}</h3>
          <button onClick={onDong} aria-label="Đóng" className="w-8 h-8 rounded-lg hover:bg-muted flex items-center justify-center transition-colors">
            <Icon name="x" className="w-5 h-5" />
          </button>
        </div>
        <div className="overflow-y-auto">{children}</div>
      </div>
    </div>
  );
}
