import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Icon } from "../../components/Icon";
import { ymdToVN } from "../../lib/format";
import { getSyncTargets, hanGiayToPC, type GiayHanPC, type HanGiayToPC, type KhoaGanPC } from "../../lib/api";
import { nhanHan, sapXepTheoHan, TEN_GIAY, tongHop } from "./hanGiayToHelper";

// PCG-06 — tab "Hạn giấy tờ": toàn cơ sở, CHỈ ĐỌC. Xe/GV sắp hết hạn giấy tờ + GV/xe đã ngưng mà còn trong khóa.
// Bấm một khóa → mở khóa đó ở "Phân công theo khóa" (?khoa=<mã>). Bám ui-mock/phancong.html (tab "Hạn giấy tờ").

function Badge({ children, mau }: { children: React.ReactNode; mau: "do" | "vang" | "xam" | "pc" }) {
  const cls = {
    do: "text-destructive bg-destructive/10 border-destructive/40",
    vang: "text-warning bg-warning/10 border-warning/40",
    xam: "text-muted-foreground bg-muted border-border",
    pc: "text-pc bg-pc-soft border-pc-border",
  }[mau];
  return <span className={"inline-block text-[11px] font-semibold border rounded-full px-2 py-px whitespace-nowrap " + cls}>{children}</span>;
}

function Khoa({ ds, onMo }: { ds: KhoaGanPC[]; onMo: (ma: string) => void }) {
  if (!ds.length) return <span className="text-[12px] text-muted-foreground italic">Chưa dùng ở khóa nào</span>;
  return (
    <div className="flex flex-wrap gap-1">
      {ds.map((k) => (
        <button key={k.ma_kh} onClick={() => onMo(k.ma_kh)} title={`Mở khóa ${k.ten_kh}`}
          className="text-[11px] font-semibold border rounded-full px-2 py-px text-pc bg-pc-soft border-pc-border hover:brightness-95">
          {k.ten_kh || k.ma_kh}
        </button>
      ))}
    </div>
  );
}

function Giay({ ds }: { ds: GiayHanPC[] }) {
  return (
    <div>
      {ds.map((g) => (
        <div key={g.giay} className="flex items-center gap-2 py-0.5">
          <span>{TEN_GIAY[g.giay] ?? g.giay}</span>
          <span className="tabular-nums">{ymdToVN(g.ngay)}</span>
          <Badge mau={g.con_ngay < 0 ? "do" : "vang"}>{nhanHan(g.con_ngay)}</Badge>
        </div>
      ))}
    </div>
  );
}

function Bang({ tieuDe, icon, cot, children }: { tieuDe: string; icon: string; cot: string[]; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-border bg-card overflow-hidden mb-4">
      <div className="px-3 py-2 border-b border-border bg-pc-soft text-[13px] font-bold text-pc flex items-center gap-2">
        <Icon name={icon} className="w-4 h-4" /> {tieuDe}
      </div>
      <div className="overflow-auto">
        <table className="w-full text-[13px]">
          <thead className="bg-muted text-left">
            <tr>{cot.map((c) => <th key={c} className="px-3 py-1.5 text-[12px] font-semibold text-muted-foreground">{c}</th>)}</tr>
          </thead>
          <tbody>{children}</tbody>
        </table>
      </div>
    </div>
  );
}

function O({ tieuDe, a, b }: { tieuDe: string; a: [number, string, "do" | "vang" | "xam"]; b?: [number, string, "do" | "vang" | "xam"] }) {
  const hien = (x: [number, string, "do" | "vang" | "xam"]) => <Badge mau={x[0] ? x[2] : "xam"}>{x[0]} {x[1]}</Badge>;
  return (
    <div className="rounded-lg border border-border bg-card px-3 py-2.5 flex-1">
      <div className="text-[12px] text-muted-foreground font-semibold">{tieuDe}</div>
      <div className="flex items-center gap-2 mt-1">{hien(a)}{b && hien(b)}</div>
    </div>
  );
}

export default function HanGiayTo() {
  const nav = useNavigate();
  const [kq, setKq] = useState<HanGiayToPC | null>(null);
  const [loi, setLoi] = useState<string | null>(null);
  const moKhoa = (ma: string) => nav(`/phan-cong/theo-khoa?khoa=${encodeURIComponent(ma)}`);

  useEffect(() => {
    let huy = false;
    getSyncTargets()
      .then((d) => {
        const t = d.targets.find((x) => x.key === d.selected) ?? d.targets[0];
        if (!t) throw new Error("Chưa cấu hình CSDL đích. Mở Cấu hình để khai báo.");
        return hanGiayToPC(30, t.key);
      })
      .then((r) => { if (!huy) setKq(r); })
      .catch((e: Error) => { if (!huy) setLoi(e.message); });
    return () => { huy = true; };
  }, []);

  const th = kq ? tongHop(kq) : null;
  const xe = kq ? sapXepTheoHan([...kq.xe.het_han, ...kq.xe.sap_het]) : [];
  const gv = kq ? sapXepTheoHan([...kq.gv.het_han, ...kq.gv.sap_het]) : [];

  return (
    <div className="p-5">
      <div className="flex items-center gap-2 mb-3 flex-wrap">
        <h1 className="text-[15px] font-bold flex items-center gap-2">
          <Icon name="clock" className="w-5 h-5 text-pc" /> Hạn giấy tờ
        </h1>
        <span className="text-[10px] font-semibold text-pc bg-pc-soft border border-pc-border rounded-full px-1.5 py-px">PCG-06</span>
        <span className="text-[12.5px] text-muted-foreground">
          Toàn bộ cơ sở · chỉ đọc{kq ? <> · ngưỡng {kq.nguong} ngày · tính đến <b className="text-foreground">{ymdToVN(kq.hom_nay)}</b></> : null}. Bấm một khóa để mở khóa đó ở “Phân công theo khóa”.
        </span>
      </div>

      {loi && <div className="rounded-md border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">{loi}</div>}
      {!kq && !loi && (
        <div className="text-sm text-muted-foreground flex items-center gap-2">
          <Icon name="refresh" className="w-4 h-4 animate-spin" /> Đang đọc hạn giấy tờ…
        </div>
      )}

      {kq && th && (
        <>
          <div className="flex gap-3 mb-4">
            <O tieuDe="Xe tập lái" a={[th.xe.het, "đã hết hạn", "do"]} b={[th.xe.sap, `còn ≤ ${kq.nguong} ngày`, "vang"]} />
            <O tieuDe="Giáo viên (GPLX)" a={[th.gv.het, "đã hết hạn", "do"]} b={[th.gv.sap, `còn ≤ ${kq.nguong} ngày`, "vang"]} />
            <O tieuDe="Đã ngưng nhưng còn phân công" a={[th.ngung, "GV/xe", "do"]} />
            <O tieuDe="Chưa khai ngày hết hạn" a={[th.chuaKhai, "mục thông tin", "xam"]} />
          </div>

          {th.tong === 0 && (
            <div className="rounded-lg border border-success/40 bg-success/5 px-4 py-8 text-center">
              <Icon name="check" className="w-6 h-6 mx-auto mb-1 text-success" />
              <div className="text-[14px] font-semibold text-success">Không có giấy tờ nào sắp hết hạn trong {kq.nguong} ngày</div>
            </div>
          )}

          {xe.length > 0 && (
            <Bang tieuDe={`Xe tập lái đang hoạt động — giấy tờ hết hạn hoặc còn ≤ ${kq.nguong} ngày`} icon="warn"
              cot={["Biển số", "Hạng xe", "Giấy tờ · ngày hết hạn", "Khóa chưa bế giảng đang dùng"]}>
              {xe.map((d) => (
                <tr key={d.bien_so} className="border-t border-border/60 align-top">
                  <td className="px-3 py-2 font-semibold tabular-nums">{d.bien_so}</td>
                  <td className="px-3 py-2">{d.hang || "—"}</td>
                  <td className="px-3 py-2"><Giay ds={d.giay} /></td>
                  <td className="px-3 py-2"><Khoa ds={d.khoa} onMo={moKhoa} /></td>
                </tr>
              ))}
            </Bang>
          )}

          {gv.length > 0 && (
            <Bang tieuDe={`Giáo viên đang hoạt động — GPLX hết hạn hoặc còn ≤ ${kq.nguong} ngày`} icon="warn"
              cot={["Mã", "Họ tên", "Hạng", "GPLX · ngày hết hạn", "Khóa chưa bế giảng đang có GV"]}>
              {gv.map((d) => (
                <tr key={d.ma_gv} className="border-t border-border/60 align-top">
                  <td className="px-3 py-2 font-mono text-[12px]">{d.ma_gv}</td>
                  <td className="px-3 py-2 font-semibold">{d.ho_ten}</td>
                  <td className="px-3 py-2">{d.hang || "—"}</td>
                  <td className="px-3 py-2"><Giay ds={d.giay} /></td>
                  <td className="px-3 py-2"><Khoa ds={d.khoa} onMo={moKhoa} /></td>
                </tr>
              ))}
            </Bang>
          )}

          {th.ngung > 0 && (
            <Bang tieuDe="Đã ngưng nhưng còn phân công trong khóa chưa bế giảng" icon="warn"
              cot={["Loại", "Mã / biển số", "Họ tên", "Hạng", "Khóa còn phân công"]}>
              {[
                ...kq.ngung.gv.map((d) => ({ loai: "Giáo viên", ma: d.ma_gv, ten: d.ho_ten, hang: d.hang, khoa: d.khoa })),
                ...kq.ngung.xe.map((d) => ({ loai: "Xe", ma: d.bien_so, ten: "—", hang: d.hang, khoa: d.khoa })),
              ].map((d) => (
                <tr key={d.loai + d.ma} className="border-t border-border/60 align-top">
                  <td className="px-3 py-2"><Badge mau="xam">{d.loai}</Badge></td>
                  <td className="px-3 py-2 font-mono text-[12px]">{d.ma}</td>
                  <td className="px-3 py-2">{d.ten}</td>
                  <td className="px-3 py-2">{d.hang || "—"}</td>
                  <td className="px-3 py-2"><Khoa ds={d.khoa} onMo={moKhoa} /></td>
                </tr>
              ))}
            </Bang>
          )}

          {th.chuaKhai > 0 && (
            <div className="rounded-lg border border-border bg-card px-3 py-2.5 text-[13px]">
              <div className="font-semibold text-[12.5px] text-muted-foreground mb-1.5 flex items-center gap-1.5">
                <Icon name="info" className="w-4 h-4" /> Chưa khai ngày hết hạn — không tính đỏ/vàng ({th.chuaKhai})
              </div>
              <div className="flex flex-wrap gap-x-5 gap-y-1">
                {kq.xe.chua_khai.map((d) => (
                  <span key={d.bien_so}><Badge mau="xam">Xe</Badge> <span className="font-medium tabular-nums">{d.bien_so}</span> · {d.hang || "—"}</span>
                ))}
                {kq.gv.chua_khai.map((d) => (
                  <span key={d.ma_gv}><Badge mau="xam">GV</Badge> <span className="font-medium">{d.ho_ten}</span> <span className="font-mono text-[12px] text-muted-foreground">{d.ma_gv}</span> · {d.hang || "—"}</span>
                ))}
              </div>
            </div>
          )}

          <div className="mt-3 text-[12px] text-muted-foreground">
            Màn này <b>không ghi gì</b> và không đổi trạng thái GV/xe. Luật chặn “xe hết hạn trước bế giảng” vẫn xét theo từng khóa lúc ghi ở bước ③.
          </div>
        </>
      )}
    </div>
  );
}
