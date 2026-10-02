// NAP-03 (CHANGES #19): tách địa chỉ gốc kéo về từ VPS (noi_tt_raw) thành Tỉnh/Huyện/Xã + phần
// chi tiết, để ĐIỀN SẴN ô map — best-effort phía client, luôn cho operator sửa trước khi map.
// Không gọi DB, không tự map cứng (địa chỉ QR hay viết tắt/thiếu dấu).

export interface DiaChiTach {
  tinh: string;
  huyen: string;
  xa: string;
  chiTiet: string; // số nhà / thôn / ấp... (phần không phải tỉnh/huyện/xã)
}

const RE_TINH = /^(tỉnh|thành phố|tp)\.?\s+/i;
const RE_HUYEN = /^(huyện|quận|thị xã|tx)\.?\s+/i;
const RE_XA = /^(xã|phường|thị trấn|tt)\.?\s+/i;

function boTienTo(s: string, re: RegExp): string | null {
  return re.test(s) ? s.replace(re, "").trim() : null;
}

/** Tách "…, Xã X, Huyện Y, Tỉnh Z" → {tinh,huyen,xa,chiTiet}. Chuỗi rỗng/không rõ → trường trống. */
export function tachDiaChiGoc(raw: string | null | undefined): DiaChiTach {
  const rong: DiaChiTach = { tinh: "", huyen: "", xa: "", chiTiet: "" };
  const segs = (raw || "").split(",").map((s) => s.trim()).filter(Boolean);
  if (segs.length === 0) return rong;

  let tinh = "";
  let huyen = "";
  let xa = "";
  const du: string[] = [];

  // Lượt 1: nhận theo tiền tố (Tỉnh/Huyện/Xã…)
  for (const s of segs) {
    const t = boTienTo(s, RE_TINH);
    const h = boTienTo(s, RE_HUYEN);
    const x = boTienTo(s, RE_XA);
    if (t !== null && !tinh) tinh = t;
    else if (h !== null && !huyen) huyen = h;
    else if (x !== null && !xa) xa = x;
    else du.push(s);
  }

  // Không có tiền tố nào khớp → suy theo vị trí: [chi tiết…], Xã, Huyện, Tỉnh (tỉnh ở cuối)
  if (!tinh && !huyen && !xa) {
    const n = segs.length;
    if (n === 1) {
      return { tinh: "", huyen: "", xa: "", chiTiet: segs[0] };
    }
    tinh = segs[n - 1];
    if (n >= 3) {
      huyen = segs[n - 2];
      xa = segs[n - 3];
      return { tinh, huyen, xa, chiTiet: segs.slice(0, n - 3).join(", ") };
    }
    // n === 2 → Xã + Tỉnh
    xa = segs[n - 2];
    return { tinh, huyen: "", xa, chiTiet: "" };
  }

  // Lượt 3 (CHANGES #19): đã có tỉnh/huyện theo tiền tố nhưng XÃ không ghi tiền tố (dữ liệu GPLX
  // hay thiếu "Xã/Phường") → đoạn không-rõ CUỐI cùng (sát huyện/tỉnh) chính là xã; phần trước là
  // chi tiết. Vẫn best-effort, operator sửa được.
  if (!xa && du.length > 0 && (tinh || huyen)) {
    xa = du[du.length - 1];
    du.pop();
  }

  return { tinh, huyen, xa, chiTiet: du.join(", ") };
}
