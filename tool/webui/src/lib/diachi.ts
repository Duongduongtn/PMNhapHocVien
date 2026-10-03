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

// BUG-07: đoạn "chi tiết" (số nhà / thôn / ấp / khu…) KHÔNG phải địa danh cấp xã/huyện/tỉnh.
// Dùng để tách chi tiết đầu chuỗi trước khi suy vị trí, tránh nhầm địa chỉ 2 cấp
// "Thôn 2, Trấn Biên, Đồng Nai" (chi tiết + xã mới + tỉnh) thành 3 cấp cũ (xã=Thôn 2 — sai).
// Từ khoá chi tiết + khoảng trắng (KHÔNG dùng \b — ký tự có dấu như "ố" không phải word-char ASCII
// nên \b sau "Số" không khớp), hoặc chuỗi bắt đầu bằng số nhà. Không gồm "đường/ngõ" để tránh nhầm
// xã thật (vd "Đường Lâm"); địa chỉ phố thường có số nhà đầu → đã bắt bằng ^\d.
const RE_CHITIET = /^(số|thôn|ấp|khu phố|khu|tổ|xóm|lô|kp)\s|^\d/i;
function laChiTiet(s: string): boolean {
  return RE_CHITIET.test(s.trim());
}

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

  // Không có tiền tố nào khớp → suy theo vị trí. TRƯỚC tiên tách "chi tiết" đầu chuỗi (số nhà/thôn/
  // ấp…) ra, rồi mới suy vị trí trên phần ĐỊA DANH còn lại — nếu không, địa chỉ 2 cấp
  // "Thôn 2, Trấn Biên, Đồng Nai" bị hiểu là 3 cấp cũ (xã=Thôn 2 sai) → map trượt (BUG-07).
  if (!tinh && !huyen && !xa) {
    let i = 0;
    while (i < segs.length - 1 && laChiTiet(segs[i])) i++; // chừa ≥1 đoạn địa danh ở cuối
    const ct = segs.slice(0, i); // chi tiết đầu (số nhà/thôn…)
    const dd = segs.slice(i); // phần địa danh (xã/huyện/tỉnh)
    const m = dd.length;
    if (m === 1) {
      // chỉ còn 1 đoạn, không đủ để suy cấp → dồn tất cả vào chi tiết (giữ hành vi cũ n===1)
      return { tinh: "", huyen: "", xa: "", chiTiet: segs.join(", ") };
    }
    tinh = dd[m - 1];
    if (m >= 3) {
      // 3 cấp cũ: …, Xã, Huyện, Tỉnh
      huyen = dd[m - 2];
      xa = dd[m - 3];
      return { tinh, huyen, xa, chiTiet: [...ct, ...dd.slice(0, m - 3)].join(", ") };
    }
    // m === 2 → 2 cấp mới: Xã (mới) + Tỉnh
    xa = dd[m - 2];
    return { tinh, huyen: "", xa, chiTiet: ct.join(", ") };
  }

  // Lượt 3a (BUG-06): xã/huyện đã khớp tiền tố nhưng TỈNH không ghi tiền tố (địa chỉ 2 cấp mới hay
  // viết "Phường X, Đồng Nai") → đoạn dư CUỐI cùng (thứ tự địa chỉ VN: tỉnh ở cuối) chính là tỉnh.
  // Phải cứu TỈNH TRƯỚC (đoạn cuối), rồi mới tới xã. Nếu không, tỉnh rơi vào chiTiet → map trượt.
  if (!tinh && du.length > 0 && (xa || huyen)) {
    tinh = du[du.length - 1];
    du.pop();
  }

  // Lượt 3b (CHANGES #19): đã có tỉnh/huyện theo tiền tố nhưng XÃ không ghi tiền tố (dữ liệu GPLX
  // hay thiếu "Xã/Phường") → đoạn không-rõ CUỐI cùng (sát huyện/tỉnh) chính là xã; phần trước là
  // chi tiết. Vẫn best-effort, operator sửa được.
  if (!xa && du.length > 0 && (tinh || huyen)) {
    xa = du[du.length - 1];
    du.pop();
  }

  return { tinh, huyen, xa, chiTiet: du.join(", ") };
}

// BUG-04 (NAP-01/NAP-03): collector sửa địa chỉ trên app web rồi tool "Kéo về từ VPS" làm tươi
// `noi_tt_raw`. Nháp địa chỉ đã map theo raw CŨ trở thành STALE — nếu giữ, nạp ra địa chỉ cũ
// (ca Lê Thị Hồng). Hàm thuần: với mỗi HV có nháp mà raw ĐỔI so với lúc kéo trước → **reset địa
// chỉ** (diaChi về null để map lại) + điền lại chiTiet từ raw MỚI. GIỮ nguyên giấy tờ/ảnh của nháp
// (chỉ địa chỉ mới stale). Không đổi nháp của HV raw không đổi (trả nguyên object cũ — ổn định
// tham chiếu cho React). rawCu: map uuid→noi_tt_raw ở lần kéo trước.
export function lamTuoiNhapDiaChi<T extends { diaChi: unknown; chiTiet: string }>(
  nhap: Record<string, T>,
  rawCu: Map<string, string | null>,
  rowsMoi: { uuid: string; noi_tt_raw: string | null }[],
): Record<string, T> {
  let next = nhap;
  let doi = false;
  for (const r of rowsMoi) {
    const n = nhap[r.uuid];
    if (!n) continue; // chưa có nháp → effect tự điền lo khi operator mở
    const rawDoi = rawCu.has(r.uuid) && rawCu.get(r.uuid) !== r.noi_tt_raw;
    if (rawDoi && (n.diaChi || n.chiTiet)) {
      if (!doi) { next = { ...nhap }; doi = true; }
      next[r.uuid] = { ...n, diaChi: null, chiTiet: tachDiaChiGoc(r.noi_tt_raw).chiTiet };
    }
  }
  return next;
}
