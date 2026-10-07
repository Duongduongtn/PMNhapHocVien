// Định dạng điểm 1 chữ số kiểu VN (8.3 → "8,3").
const fmt1 = (x: number): string => x.toFixed(1).replace(".", ",");

// Gợi ý dưới ô nhập điểm ở lưới Cập nhật KQĐT.
// BUG (07/10/2026): HV đã cập nhật (TT_XuLy 09/10/14/90) có điểm đã lưu nhưng dòng là
// ô NHẬP (trống) → nhân viên tưởng điểm chưa lưu. PRD KQD-01 yêu cầu "lưới hiện điểm (nếu có)".
// Quy tắc: đang gõ hợp lệ → preview quy đổi "→ X,X"; vượt khung → "sai";
//          chưa gõ mà đã có điểm lưu → "đã lưu X,X"; chưa có gì → "—".
export function hintDiem(over: boolean, qd: number | null, saved: number | null | undefined): string {
  if (over) return "sai";
  if (qd != null) return "→ " + fmt1(qd);
  if (saved != null) return "đã lưu " + fmt1(saved);
  return "—";
}
