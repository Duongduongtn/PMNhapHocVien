import { useEffect, useMemo, useRef, useState } from "react";
import { dsBc2, goiYSoBc2, type GoiYSoResp } from "../../lib/tnbc2Api";
import { DO_DAI_MA_BCII, kiemSoBc2 } from "../../lib/tnbcBc2";

// TNB-03 — form BC2: số gợi ý (sửa được, kiểm trùng ngay khi gõ), ngày báo cáo, ghi chú, BC1 của khóa (chỉ đọc).
// Dùng cho "Tạo BC2 rỗng" (task 111) và bước ③ "Lập BC2 và thêm học viên" (task 112).

export interface GiaTriFormBc2 {
  so_bao_cao: string;
  ngay_bao_cao: string; // YYYY-MM-DD
  ghi_chu: string;
  /** Có BC1, số hợp lệ và không trùng. */
  hop_le: boolean;
  /** Mô tô mà khóa đã có BC2: cần người dùng xác nhận đã xem (server trả 409 nếu không). */
  canh_bao: string;
  bc1: GoiYSoResp["bc1"];
}

const homNayIso = () => {
  const d = new Date();
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
};

export default function FormBc2({
  maKh,
  tenKh,
  onChange,
}: {
  maKh: string;
  tenKh: string;
  onChange: (v: GiaTriFormBc2) => void;
}) {
  const [goiY, setGoiY] = useState<GoiYSoResp | null>(null);
  const [daCo, setDaCo] = useState<string[]>([]);
  const [loi, setLoi] = useState<string | null>(null);
  const [so, setSo] = useState("");
  const [ngay, setNgay] = useState(homNayIso());
  const [ghiChu, setGhiChu] = useState("");
  const cb = useRef(onChange);
  cb.current = onChange;

  useEffect(() => {
    let huy = false;
    setLoi(null);
    Promise.all([goiYSoBc2(maKh), dsBc2()])
      .then(([g, d]) => {
        if (huy) return;
        setGoiY(g);
        setSo(g.so);
        setDaCo(d.bc2.map((b) => b.ma_bc2));
      })
      .catch((e: unknown) => { if (!huy) setLoi(e instanceof Error ? e.message : "Không tải được gợi ý số BC2"); });
    return () => { huy = true; };
  }, [maKh]);

  const loiSo = useMemo(() => (goiY ? kiemSoBc2(so, daCo) : []), [goiY, so, daCo]);
  const chuaBc1 = !!goiY && !goiY.co_bc1;
  const canhBao = goiY && goiY.loai === "moto" && goiY.bc2_cua_khoa.length > 0
    ? `Khóa này đã có BC2 số ${goiY.bc2_cua_khoa.map((b) => b.ma).join(", ")}`
    : "";
  const hopLe = !!goiY && !chuaBc1 && loiSo.length === 0 && !!ngay;

  useEffect(() => {
    if (!goiY) return;
    cb.current({ so_bao_cao: so.trim(), ngay_bao_cao: ngay, ghi_chu: ghiChu, hop_le: hopLe, canh_bao: canhBao, bc1: goiY.bc1 });
  }, [goiY, so, ngay, ghiChu, hopLe, canhBao]);

  if (loi) return <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-[13px] text-destructive">{loi}</div>;
  if (!goiY) return <div className="text-[13px] text-muted-foreground">Đang tải gợi ý số BC2…</div>;

  return (
    <div className="rounded-xl border border-border bg-card p-4 space-y-3">
      <div className="text-[12.5px] text-muted-foreground">Khóa <b className="text-foreground">{tenKh}</b> · {goiY.loai === "oto" ? "ô tô" : "mô tô"}</div>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div>
          <label className="field-label" htmlFor="bc2-so">Số BC2 (= mã báo cáo)</label>
          <input id="bc2-so" className={`field-input font-mono ${loiSo.length ? "!border-destructive !bg-destructive/5" : ""}`}
            value={so} maxLength={DO_DAI_MA_BCII + 10} onChange={(e) => setSo(e.target.value)} />
        </div>
        <div>
          <label className="field-label" htmlFor="bc2-ngay">Ngày báo cáo</label>
          <input id="bc2-ngay" type="date" className="field-input" value={ngay} onChange={(e) => setNgay(e.target.value)} />
        </div>
        <div>
          <label className="field-label" htmlFor="bc2-bc1">BC1 của khóa</label>
          <input id="bc2-bc1" className="field-input font-mono" disabled
            value={goiY.bc1 ? goiY.bc1.so_bao_cao : "(chưa có BC1)"} readOnly />
          {goiY.bc1 && (
            <div className="text-[11.5px] text-muted-foreground mt-0.5">{goiY.bc1.so_hoc_sinh ?? 0} học sinh ghi trong BC1</div>
          )}
        </div>
      </div>
      <div>
        <label className="field-label" htmlFor="bc2-ghichu">Ghi chú (tùy chọn)</label>
        <input id="bc2-ghichu" className="field-input" value={ghiChu} maxLength={255} onChange={(e) => setGhiChu(e.target.value)} />
      </div>
      {!ngay && (
        <div className="rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-[13px] text-destructive">⛔ Cần nhập ngày báo cáo.</div>
      )}
      {loiSo.map((m) => (
        <div key={m} className="rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-[13px] text-destructive">⛔ {m}</div>
      ))}
      {chuaBc1 && (
        <div className="rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-[13px] text-destructive">
          ⛔ Khóa này chưa có BC1 — phải có BC1 mới lập được BC2.
        </div>
      )}
      {canhBao && (
        <div className="rounded-lg border border-warning/40 bg-warning/10 px-3 py-2 text-[13px] text-warning">⚠ {canhBao}</div>
      )}
      <div className="text-[12.5px] text-muted-foreground">
        {goiY.loai === "moto"
          ? "Mô tô: mỗi khóa một BC1 và một BC2; số BC2 = số BC1 bỏ tiền tố A1A2. Tổng thí sinh ghi bằng số học sinh của BC1."
          : "Ô tô: số BC2 kế tiếp theo năm; một BC1 có thể có nhiều BC2. Tổng thí sinh ghi bằng số học viên lúc lập (0 khi tạo rỗng)."}
      </div>
    </div>
  );
}
