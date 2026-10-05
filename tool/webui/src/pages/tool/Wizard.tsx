import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Icon } from "../../components/Icon";
import CauHinhForm from "../../components/CauHinhForm";
import { useToolAuth } from "../../auth/ToolAuth";
import { kiemMoiTruong, type MoiTruong } from "../../lib/api";

// DGT-03 — Wizard thiết lập lần đầu (máy sạch). 3 bước, test-before-next:
//   1) Kiểm môi trường: thư mục ghi được (mạng tới VPS kiểm ở bước 2 khi đã có URL)
//   2) Cấu hình SQL nguồn/đích + VPS — test xanh + lưu mới cho Tiếp (CauHinhForm dùng chung)
//   3) Đăng nhập (qua VPS) → vào thẳng tool
// Vào đây khi backend báo chưa đủ cấu hình (App.tsx). Có cấu hình rồi thì không vào wizard.

const BUOC = [
  { so: 1, ten: "Kiểm môi trường" },
  { so: 2, ten: "Cấu hình kết nối" },
  { so: 3, ten: "Đăng nhập" },
];

export default function Wizard() {
  const nav = useNavigate();
  const { dangNhap } = useToolAuth();
  const [buoc, setBuoc] = useState(1);

  // ── Bước 1: môi trường ──
  const [mt, setMt] = useState<MoiTruong | null>(null);
  const [dangKiemMt, setDangKiemMt] = useState(true);
  const kiemMt = () => {
    setDangKiemMt(true);
    kiemMoiTruong().then(setMt).catch(() => setMt(null)).finally(() => setDangKiemMt(false));
  };
  useEffect(kiemMt, []);

  // ── Bước 2: cấu hình (test-before-next) ──
  const [b1Test, setB1Test] = useState(false);
  const [b1Saved, setB1Saved] = useState(false);

  // ── Bước 3: đăng nhập ──
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loiDn, setLoiDn] = useState<string | null>(null);
  const [dangDn, setDangDn] = useState(false);

  async function dangNhapXong(e: React.FormEvent) {
    e.preventDefault();
    setLoiDn(null);
    setDangDn(true);
    try {
      await dangNhap(username.trim(), password);
      nav("/tool/nap", { replace: true });
    } catch (err) {
      setLoiDn(err instanceof Error ? err.message : "Không đăng nhập được");
    } finally {
      setDangDn(false);
    }
  }

  const ghiDuoc = !!mt?.thu_muc_ghi_duoc;

  return (
    <div className="min-h-screen bg-muted/30 flex flex-col items-center py-8 px-4">
      <div className="w-full max-w-2xl">
        {/* Tiêu đề */}
        <div className="text-center mb-5">
          <div className="w-14 h-14 rounded-2xl bg-primary text-primary-foreground flex items-center justify-center mx-auto mb-3">
            <Icon name="settings" className="w-7 h-7" />
          </div>
          <h1 className="text-lg font-bold">Thiết lập tool lần đầu</h1>
          <p className="text-[12.5px] text-muted-foreground mt-1">
            Khai báo kết nối một lần — lần sau mở tool vào thẳng.
          </p>
        </div>

        {/* Thanh bước */}
        <ol className="flex items-center justify-center gap-2 mb-6">
          {BUOC.map((b, i) => {
            const done = buoc > b.so;
            const active = buoc === b.so;
            return (
              <li key={b.so} className="flex items-center gap-2">
                <div className="flex items-center gap-2">
                  <span
                    className={
                      "w-7 h-7 rounded-full grid place-items-center text-[12.5px] font-bold shrink-0 " +
                      (active ? "bg-primary text-primary-foreground"
                        : done ? "bg-success text-white" : "bg-muted text-muted-foreground")
                    }
                  >
                    {done ? <Icon name="check" className="w-4 h-4" sw={3} /> : b.so}
                  </span>
                  <span className={"text-[12.5px] font-semibold " + (active ? "text-foreground" : "text-muted-foreground")}>
                    {b.ten}
                  </span>
                </div>
                {i < BUOC.length - 1 && <span className="w-8 h-px bg-border" />}
              </li>
            );
          })}
        </ol>

        <div className="rounded-xl border border-border bg-background p-5 shadow-sm">
          {/* ── Bước 1 ── */}
          {buoc === 1 && (
            <div className="space-y-4">
              <p className="text-[13px] text-muted-foreground">
                Kiểm tool có ghi được cấu hình xuống máy không. (Kết nối mạng tới máy chủ sẽ
                kiểm ở bước Cấu hình, sau khi anh nhập địa chỉ VPS.)
              </p>
              {dangKiemMt ? (
                <div className="flex items-center gap-2 text-[13px] text-muted-foreground">
                  <Icon name="refresh" className="w-4 h-4 animate-spin" /> Đang kiểm…
                </div>
              ) : (
                <div
                  className={
                    "flex items-start gap-2.5 rounded-lg px-4 py-3 border text-[13px] " +
                    (ghiDuoc ? "text-success bg-success/10 border-success/30"
                      : "text-destructive bg-destructive/10 border-destructive/30")
                  }
                >
                  <Icon name={ghiDuoc ? "check" : "warn"} className="w-5 h-5 shrink-0 mt-0.5" sw={ghiDuoc ? 3 : 2} />
                  <div className="min-w-0">
                    <div className="font-semibold">
                      {ghiDuoc ? "Thư mục lưu cấu hình ghi được" : "Không ghi được thư mục cấu hình"}
                    </div>
                    <div className="text-[11.5px] opacity-80 break-all mt-0.5 font-[ui-monospace]">
                      {mt?.duong_dan || "—"}
                    </div>
                    {!ghiDuoc && (
                      <div className="text-[11.5px] mt-1">
                        Đặt tool ngoài <b>Program Files</b> (vd Desktop hoặc ổ D) rồi bấm “Kiểm lại”.
                      </div>
                    )}
                  </div>
                </div>
              )}
              <div className="flex justify-between items-center pt-1">
                <button
                  type="button"
                  onClick={kiemMt}
                  className="inline-flex items-center gap-1.5 h-9 px-3.5 rounded-lg border border-border text-[13px] font-semibold hover:bg-muted transition-colors"
                >
                  <Icon name="refresh" className="w-4 h-4" /> Kiểm lại
                </button>
                <button
                  type="button"
                  disabled={!ghiDuoc}
                  onClick={() => setBuoc(2)}
                  className="inline-flex items-center gap-1.5 h-9 px-5 rounded-lg bg-primary text-primary-foreground font-semibold text-[13px] hover:brightness-110 transition-all shadow-sm disabled:opacity-50"
                >
                  Tiếp <Icon name="chevronRight" className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          {/* ── Bước 2 ── */}
          {buoc === 2 && (
            <div className="space-y-4">
              <p className="text-[13px] text-muted-foreground">
                Khai báo kết nối, bấm <b>Kiểm tra kết nối</b> cho xanh rồi <b>Lưu kết nối</b> để sang bước đăng nhập.
              </p>
              <CauHinhForm active={buoc === 2} onBlock1Test={setB1Test} onBlock1Saved={() => setB1Saved(true)} />
              <div className="flex justify-between items-center pt-1">
                <button
                  type="button"
                  onClick={() => setBuoc(1)}
                  className="inline-flex items-center gap-1.5 h-9 px-3.5 rounded-lg border border-border text-[13px] font-semibold hover:bg-muted transition-colors"
                >
                  <Icon name="chevronLeft" className="w-4 h-4" /> Quay lại
                </button>
                <div className="flex items-center gap-2.5">
                  {!(b1Test && b1Saved) && (
                    <span className="text-[11.5px] text-muted-foreground">
                      {b1Test ? "Lưu kết nối để tiếp" : "Kiểm tra kết nối xanh để tiếp"}
                    </span>
                  )}
                  <button
                    type="button"
                    disabled={!(b1Test && b1Saved)}
                    onClick={() => setBuoc(3)}
                    className="inline-flex items-center gap-1.5 h-9 px-5 rounded-lg bg-primary text-primary-foreground font-semibold text-[13px] hover:brightness-110 transition-all shadow-sm disabled:opacity-50"
                  >
                    Tiếp <Icon name="chevronRight" className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ── Bước 3 ── */}
          {buoc === 3 && (
            <form className="space-y-3 max-w-sm mx-auto" onSubmit={dangNhapXong}>
              <p className="text-[13px] text-muted-foreground text-center">
                Đăng nhập bằng tài khoản nạp DB hoặc quản trị (xác thực qua máy chủ).
              </p>
              <div>
                <label className="field-label">Tài khoản <span className="text-destructive">*</span></label>
                <input className="field-input mt-1" value={username} onChange={(e) => setUsername(e.target.value)}
                  placeholder="Tên đăng nhập" autoComplete="username" required />
              </div>
              <div>
                <label className="field-label">Mật khẩu <span className="text-destructive">*</span></label>
                <input type="password" className="field-input mt-1" value={password} onChange={(e) => setPassword(e.target.value)}
                  placeholder="Mật khẩu" autoComplete="current-password" required />
              </div>
              {loiDn && (
                <div className="rounded-lg bg-destructive/10 border border-destructive/30 px-3 py-2 text-[12.5px] text-destructive">
                  {loiDn} — nếu do không tới được máy chủ, bấm “Quay lại” sửa địa chỉ VPS.
                </div>
              )}
              <div className="flex justify-between items-center pt-1">
                <button
                  type="button"
                  onClick={() => setBuoc(2)}
                  className="inline-flex items-center gap-1.5 h-9 px-3.5 rounded-lg border border-border text-[13px] font-semibold hover:bg-muted transition-colors"
                >
                  <Icon name="chevronLeft" className="w-4 h-4" /> Quay lại
                </button>
                <button
                  type="submit"
                  disabled={dangDn}
                  className="inline-flex items-center gap-1.5 h-9 px-5 rounded-lg bg-primary text-primary-foreground font-semibold text-[13px] hover:brightness-110 transition-all shadow-sm disabled:opacity-60"
                >
                  <Icon name="logout" className="w-4 h-4" /> {dangDn ? "Đang đăng nhập…" : "Vào tool"}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
