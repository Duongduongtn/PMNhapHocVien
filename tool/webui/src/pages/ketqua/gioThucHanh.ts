// KQD-02/KQD-08 — ô Giờ đường nhận 2 dạng: số thập phân (giữ nguyên) hoặc hh:mm (đổi sang thập phân).
// Cùng luật với backend `ketqua_dat.doc_gio`. Số đã lưu ở DB đích LÀ giờ thập phân → hiển thị nguyên,
// không đoán lại phần lẻ là phút.

export type GioDoc = number | null | "sai";

const HH_MM = /^(\d{1,3}):(\d{1,2})(?::(\d{1,2}))?$/;
const lamTron2 = (x: number) => Math.round(x * 100) / 100;

/** "20:30" → 20.5 · "20,5"/"20.5" → 20.5 · "" → null · rác / phút ≥ 60 → "sai". */
export function parseGio(v: string): GioDoc {
  const t = (v || "").trim();
  if (t === "") return null;
  const m = HH_MM.exec(t);
  if (m) {
    const h = Number(m[1]), ph = Number(m[2]), gi = Number(m[3] ?? 0);
    if (ph >= 60 || gi >= 60) return "sai";
    return lamTron2(h + ph / 60 + gi / 3600);
  }
  if (/^\d+([.,]\d+)?$/.test(t)) return Number(t.replace(",", "."));
  return "sai";
}

/** Rời ô: hh:mm hợp lệ → thập phân VN ("20:30" → "20,5"); dạng khác giữ NGUYÊN như đã gõ. */
export function chuanHoaGio(v: string): string {
  const t = (v || "").trim();
  if (!HH_MM.test(t)) return v;
  const g = parseGio(t);
  return typeof g === "number" ? soHien(g) : v;
}

/** Số từ DB → chuỗi trong ô nhập: tối đa 2 chữ số thập phân, dấu phẩy, không dấu nghìn (để parse lại được). */
export function soHien(x: number | null | undefined): string {
  if (x == null || !Number.isFinite(x)) return "";
  return String(lamTron2(x)).replace(".", ",");
}

/** Hiển thị trong bảng (có dấu nghìn): 1008.19 → "1.008,19". */
export function fmtVn(x: number | null | undefined): string {
  return x == null ? "—" : x.toLocaleString("vi-VN", { maximumFractionDigits: 2 });
}

/** Hai giá trị coi là bằng nhau khi lệch < 0,005 (cột real của CDB lưu 18.4 thành 18.399999…). */
export function bangNhau(a: number | null | undefined, b: number | null | undefined): boolean {
  if (a == null || b == null) return a == null && b == null;
  return Math.abs(lamTron2(a) - lamTron2(b)) < 0.005;
}

/** Km nhập tay: "725,63" / "725.63" / "1.008,19" → số · trống → null · rác → "sai". */
export function parseKm(v: string): GioDoc {
  const t = (v || "").trim();
  if (t === "") return null;
  if (/^\d{1,3}(\.\d{3})+(,\d+)?$/.test(t)) return lamTron2(Number(t.replace(/\./g, "").replace(",", ".")));
  if (/^\d+([.,]\d+)?$/.test(t)) return lamTron2(Number(t.replace(",", ".")));
  return "sai";
}
