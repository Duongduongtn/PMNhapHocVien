// Gọi API tool chạy localhost. Dev: webui 3011 ↔ backend 8000 (khác origin).
// Khi đóng gói .exe, webui static do chính FastAPI phục vụ → cùng origin (BASE rỗng).
const BASE = import.meta.env.DEV ? "http://localhost:8000" : "";

// Session token cục bộ (HTG-01③) — giữ trong bộ nhớ; tải lại trang phải đăng nhập lại.
let _token: string | null = null;
export const datToken = (t: string | null) => {
  _token = t;
};
// Header kèm Bearer cho endpoint /local/* nghiệp vụ (config/auth được miễn — A1).
function authHeaders(extra?: Record<string, string>): Record<string, string> {
  const h: Record<string, string> = { ...(extra || {}) };
  if (_token) h.Authorization = `Bearer ${_token}`;
  return h;
}

export interface ToolConfig {
  sqlserver_host: string;
  sqlserver_database: string;
  sqlserver_user: string;
  sqlserver_password: string;
  vps_url: string;
  vps_api_key: string;
}

export interface TestResult {
  sqlserver: { ok: boolean; message: string };
  vps: { ok: boolean; message: string };
}

export type LoaiXe = "moto" | "oto";

export interface KhoaHoc {
  ma_kh: string;
  ten_kh: string;
  hang_gplx: string;
  hang_dt: string | null;
  ma_so_gtvt: string;
  ma_loai_hs: number; // 1 = mô tô, 2 = ô tô
}

async function json<T>(r: Response): Promise<T> {
  if (!r.ok) {
    const d = await r.json().catch(() => null);
    throw new Error(d?.detail || `${r.status} ${r.statusText}`);
  }
  return r.json() as Promise<T>;
}

// ── Đăng nhập cục bộ của tool (HTG-01③) ──
export interface ToolNguoiDung {
  session_token: string;
  username: string;
  ho_ten: string | null;
  vai_tro: string;
}

export const toolDangNhap = (username: string, password: string) =>
  fetch(`${BASE}/local/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  }).then(json<ToolNguoiDung>);

export const toolDangXuat = () =>
  fetch(`${BASE}/local/auth/logout`, { method: "POST", headers: authHeaders() });

export const getConfig = () =>
  fetch(`${BASE}/local/config`).then(json<Partial<ToolConfig>>);

export const putConfig = (cfg: ToolConfig) =>
  fetch(`${BASE}/local/config`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cfg),
  }).then(json<Partial<ToolConfig>>);

export const testConfig = (cfg: ToolConfig) =>
  fetch(`${BASE}/local/config/test`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(cfg),
  }).then(json<TestResult>);

export const getKhoaHoc = (loai: LoaiXe) =>
  fetch(`${BASE}/local/khoa-hoc?loai=${loai}`, { headers: authHeaders() }).then(json<KhoaHoc[]>);

// KHO-01 — tạo khóa học
export interface HangDT {
  ma_hang_dt: string;
  ten: string;
  tuoi_hv: number | null;
  thoi_gian_dt: number | null;
  hang_gplx: string;
}
export const getHangDT = () =>
  fetch(`${BASE}/local/khoa-hoc/hang-dt`, { headers: authHeaders() }).then(json<HangDT[]>);

export interface KhoaHocTaoIn {
  hang_dt: string;
  ten_kh: string;
  ngay_kg: string; // yyyy-mm-dd
  ngay_bg: string; // yyyy-mm-dd
  tong_so_hv: number;
  so_qd?: string | null;
  ngay_qd?: string | null;
  ngay_thi?: string | null;
  ghi_chu?: string | null;
}
export interface KhoaHocTaoKq {
  ma_kh: string;
  ten_kh: string;
  hang_gplx: string;
  hang_dt: string;
}
export const taoKhoa = (body: KhoaHocTaoIn) =>
  fetch(`${BASE}/local/khoa-hoc/tao`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  }).then(json<KhoaHocTaoKq>);

// QLY-01 — Tra cứu DB
export interface KhoaTraCuu {
  ma_kh: string;
  ten_kh: string;
  hang_gplx: string;
  hang_dt: string | null;
  bc1: boolean; // đã lập Báo cáo I → chỉ xem
}
export const traCuuKhoa = (q: string) =>
  fetch(`${BASE}/local/khoa-hoc/tra-cuu?q=${encodeURIComponent(q)}`, { headers: authHeaders() }).then(json<KhoaTraCuu[]>);

export interface HoSoRow {
  ma_dk: string;
  ho_ten: string | null;
  ngay_sinh: string | null; // yyyymmdd
  gioi_tinh: string | null; // M/F
  so_cccd: string | null;
  so_cmnd_cu: string | null;
  so_ho_so: string | null;
  noi_tt: string | null; // chi tiết thường trú (số nhà/thôn)
  hktt: string | null; // thường trú đầy đủ (xã/tỉnh từ DM_DVHC)
  noi_ct: string | null; // chi tiết cư trú
  hkct: string | null; // cư trú đầy đủ
  ngay_cap: string | null; // ngày cấp CCCD (yyyymmdd)
  noi_cap_ma: string | null; // mã Sở GTVT (nơi cấp)
  noi_cap_ten: string | null; // tên Sở GTVT (tỉnh cấp CCCD)
  co_anh: boolean;
  duong_dan_anh: string | null; // đường dẫn .jp2 trong DB (QLY-01 task 35 — hiện ở modal)
  ma_loai_hs: number;
}
export const dsHoSoTheoKhoa = (makh: string) =>
  fetch(`${BASE}/local/ho-so?makh=${encodeURIComponent(makh)}`, { headers: authHeaders() }).then(json<HoSoRow[]>);

// QLY-01 task 35 — tải ảnh chân dung HV đã lưu (.jp2 → PNG qua backend). Phải fetch kèm session
// header rồi createObjectURL (KHÔNG <img src=url> trực tiếp: header không gửi kèm). Phân biệt
// file mất (404) / ảnh hỏng (422) để avatar hiện icon ảnh-vỡ và modal báo đúng nguyên nhân.
export type KetQuaAnh = { url: string } | { loi: "mat" | "hong" | "khac" };
async function taiAnhPNG(path: string): Promise<KetQuaAnh> {
  const r = await fetch(`${BASE}${path}`, { headers: authHeaders() });
  if (r.ok) return { url: URL.createObjectURL(await r.blob()) };
  if (r.status === 404) return { loi: "mat" };
  if (r.status === 422) return { loi: "hong" };
  return { loi: "khac" };
}
// v: cache-bust (CHANGES #23) — tăng sau khi lưu/thay ảnh để trình duyệt lấy ảnh MỚI, không trả bản cũ từ bộ đệm. v=0 → URL ổn định (cache bình thường).
export const taiAnhHoSo = (maDk: string, v = 0) => taiAnhPNG(`/local/ho-so/anh?ma_dk=${encodeURIComponent(maDk)}${v ? `&v=${v}` : ""}`);
export const taiAnhThumb = (maDk: string, v = 0) => taiAnhPNG(`/local/ho-so/anh-thumb?ma_dk=${encodeURIComponent(maDk)}${v ? `&v=${v}` : ""}`);

// QLY-07 task 40 — đổi nền trắng cả khóa (job nền + polling tiến độ).
export interface DoiNenTienDo {
  tong: number;
  xong: number;
  bo_qua: number;
  loi: number;
  ds_loi: { ma_dk: string; ly_do: string }[];
  dang_chay: boolean;
  xong_het: boolean;
  thong_bao: string;
}
export const batDauDoiNen = (maKh: string, pham_vi: "chua_trang" | "tat_ca", sao_luu: boolean) =>
  fetch(`${BASE}/local/khoa/${encodeURIComponent(maKh)}/doi-nen`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ pham_vi, sao_luu }),
  }).then(json<{ ok: boolean; ma_kh: string }>);
export const tienDoDoiNen = (maKh: string) =>
  fetch(`${BASE}/local/khoa/${encodeURIComponent(maKh)}/doi-nen`, { headers: authHeaders() }).then(
    json<DoiNenTienDo>,
  );

// QLY-01 lát 2 — sửa nhân thân HV. Đọc chi tiết để mở form + cờ BC1 (chặn sửa).
export interface HoSoChiTiet {
  ma_dk: string;
  ho_ten: string;
  ngay_sinh: string; // dd/mm/yyyy (hoặc yyyy) để hiển thị trên ô
  gioi_tinh: string; // M/F/U
  gioi_tinh_ten: string;
  so_cccd: string;
  noi_tt: string;
  hktt: string | null; // tên xã HKTT (chỉ để tham chiếu, không sửa ở đây)
  ma_kh: string;
  bc1: boolean;
}
export const chiTietHoSo = (maDk: string) =>
  fetch(`${BASE}/local/ho-so/chi-tiet?ma_dk=${encodeURIComponent(maDk)}`, { headers: authHeaders() }).then(
    json<HoSoChiTiet>,
  );

export interface HoSoSuaIn {
  ho_ten: string;
  ngay_sinh: string; // dd/mm/yyyy hoặc yyyy
  gioi_tinh: string; // M/F/U
  so_cccd: string;
  noi_tt: string;
}
export const suaHoSo = (maDk: string, body: HoSoSuaIn) =>
  fetch(`${BASE}/local/ho-so/sua?ma_dk=${encodeURIComponent(maDk)}`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  }).then(json<{ ok: boolean; ma_dk: string }>);

// QLY-02 — đổi khóa (cùng hạng). Danh sách khóa đích + thực hiện đổi.
export interface KhoaDich {
  ma_kh: string;
  ten_kh: string;
  hang_gplx: string;
  hang_dt: string | null;
}
export const khoaCungHang = (maKh: string) =>
  fetch(`${BASE}/local/khoa-hoc/cung-hang?ma_kh=${encodeURIComponent(maKh)}`, { headers: authHeaders() }).then(
    json<KhoaDich[]>,
  );
export const doiKhoa = (maDk: string, maKhDich: string) =>
  fetch(`${BASE}/local/ho-so/doi-khoa?ma_dk=${encodeURIComponent(maDk)}`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ ma_kh_dich: maKhDich }),
  }).then(json<{ ok: boolean; ma_dk: string; ma_kh: string; so_ho_so: string }>);

// QLY-03 — xóa học viên (xóa mềm ảnh sang _DELETED). anh_loi: đã xóa DB nhưng chuyển ảnh lỗi.
export const xoaHoSo = (maDk: string) =>
  fetch(`${BASE}/local/ho-so/xoa?ma_dk=${encodeURIComponent(maDk)}`, {
    method: "POST",
    headers: authHeaders(),
  }).then(json<{ ok: boolean; ma_dk: string; anh_loi?: string }>);

// QLY-08 — gỡ HV đã nạp (nhầm khóa) về chờ nạp: xóa khỏi CSDT rồi trả bản ghi gốc VPS về pending.
// ve_cho_nap=true: trọn vẹn. VPS lỗi SAU khi đã xóa CSDT: ok vẫn true + dong_bo_loi + co_the_thu_lai
// (UI hiện banner "Thử lại đồng bộ"). trong_hang_doi=false: dòng đã "Bỏ khỏi hàng đợi" → bấm Kéo về.
export interface GoVeKetQua {
  ok: boolean;
  ma_dk: string;
  uuid?: string;
  ve_cho_nap?: boolean;
  trong_hang_doi?: boolean;
  da_xoa_csdt?: boolean;
  dong_bo_loi?: string;
  co_the_thu_lai?: boolean;
  anh_loi?: string;
}
export const goVeChoNap = (maDk: string) =>
  fetch(`${BASE}/local/ho-so/go-ve-cho-nap?ma_dk=${encodeURIComponent(maDk)}`, {
    method: "POST",
    headers: authHeaders(),
  }).then(json<GoVeKetQua>);

// QLY-08 "Thử lại đồng bộ" — chạy lại RIÊNG bước gọi VPS (KHÔNG xóa lại CSDT). Idempotent.
export const dongBoTraVe = (uuid: string) =>
  fetch(`${BASE}/local/ho-so/dong-bo-tra-ve?uuid=${encodeURIComponent(uuid)}`, {
    method: "POST",
    headers: authHeaders(),
  }).then(json<{ ok: boolean; uuid: string; ve_cho_nap: boolean; trong_hang_doi: boolean }>);

// QLY-05 — nạp/thay ảnh cho HV đã có. Ảnh đã xử lý qua xuLyAnh (NAP-04) → gửi jp2_b64.
export const napAnh = (maDk: string, jp2B64: string) =>
  fetch(`${BASE}/local/ho-so/nap-anh?ma_dk=${encodeURIComponent(maDk)}`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ jp2_b64: jp2B64 }),
  }).then(json<{ ok: boolean; ma_dk: string; duong_dan_anh: string; co_anh: boolean }>);

// QLY-06 — đọc đủ dữ liệu cá nhân HV để điền sẵn khi mở hồ sơ khóa khác (nạp mới khóa đích).
export interface HoSoDayDu {
  ho_ten: string;
  ngay_sinh: string; // yyyymmdd (hoặc yyyy)
  gioi_tinh: string; // M/F/U
  so_cmt: string;
  ngay_cap_cmt: string | null; // yyyymmdd
  noi_cap_cmt: string | null;
  noi_tt: string | null;
  noi_tt_ma_dvhc: string;
  noi_tt_ma_dvql: string;
}
export const hoSoDayDu = (maDk: string) =>
  fetch(`${BASE}/local/ho-so/day-du?ma_dk=${encodeURIComponent(maDk)}`, { headers: authHeaders() }).then(
    json<HoSoDayDu>,
  );

export interface Tinh {
  ma_dvql: string;
  ten_tinh: string;
}

export interface Xa {
  ma_dvhc: string;
  ma_dvql: string;
  ten_xa: string;
}

export interface MapKetQua {
  matched: boolean;
  divided: boolean;
  ma_dvhc?: string;
  ma_dvql?: string;
  ten_xa?: string;
  ten_tinh?: string;
}

export const getTinh = () =>
  fetch(`${BASE}/local/dvhc/tinh`, { headers: authHeaders() }).then(json<Tinh[]>);

export const getXa = (tinh: string) =>
  fetch(`${BASE}/local/dvhc/xa?tinh=${encodeURIComponent(tinh)}`, { headers: authHeaders() }).then(json<Xa[]>);

export interface SoGtvt { ma: string; ten: string } // nơi cấp: mã Sở GTVT (MaDVQL) + tên tỉnh
export const getSoGtvt = () =>
  fetch(`${BASE}/local/dvhc/so-gtvt`, { headers: authHeaders() }).then(json<SoGtvt[]>);

export const mapDiaChi = (dc: { tinh: string; huyen: string; xa: string }) =>
  fetch(`${BASE}/local/dvhc/map`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(dc),
  }).then(json<MapKetQua>);

export interface AnhKetQua {
  preview: string; // data URL PNG (xem trước)
  jp2_b64: string; // .jp2 base64 — NAP-05 dùng để ghi file
  w: number;
  h: number;
}

export const xuLyAnh = (file: File, box: string, xoaPhong: boolean) => {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("box", box);
  fd.append("xoa_phong", String(xoaPhong));
  return fetch(`${BASE}/local/anh/xu-ly`, { method: "POST", headers: authHeaders(), body: fd }).then(
    json<AnhKetQua>,
  );
};

// NAP-05: giấy tờ bắt buộc theo khóa + nạp 1 HV.
export interface GiayTo {
  ma_gt: number;
  ten_gt: string;
}

export const getGiayTo = (maLoaiHs: number, hangDt: string) =>
  fetch(`${BASE}/local/giay-to?ma_loai_hs=${maLoaiHs}&hang_dt=${encodeURIComponent(hangDt)}`, {
    headers: authHeaders(),
  }).then(json<GiayTo[]>);

export interface NapIn {
  uuid: string;
  ma_khoa_hoc: string;
  ho_ten: string;
  ngay_sinh: string; // yyyymmdd
  gioi_tinh: string; // 'M' | 'F'
  so_cmt: string;
  ngay_cap_cmt?: string; // yyyymmdd (SP convert style 112); từ hàng kéo về
  noi_cap_cmt?: string;
  chi_tiet_tt?: string; // số nhà/thôn — mặc định trống (NoiTT); KHÔNG nhét tên xã
  noi_tt_ma_dvhc: string;
  noi_tt_ma_dvql: string;
  chi_tiet_ct?: string;
  giay_to_tick: number[];
  anh_jp2_b64?: string | null;
}

export interface NapKetQua {
  ma_dk: string;
  so_ho_so: string;
  so_giay_to: number;
}

// Trả lỗi kèm nội dung detail (FastAPI) để UI báo đúng dòng.
export const napHoSo = async (body: NapIn): Promise<NapKetQua> => {
  const r = await fetch(`${BASE}/local/nap`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    const d = await r.json().catch(() => null);
    throw new Error(d?.detail || `${r.status} ${r.statusText}`);
  }
  return r.json() as Promise<NapKetQua>;
};

// NAP-06: kiểm CCCD đã có trong cùng khóa chưa (cảnh báo sớm). Lỗi kiểm → coi như không trùng
// (SP gộp vẫn chặn khi nạp qua @p_out=-2).
export const kiemTrungCccd = async (
  maKh: string,
  soCmt: string,
): Promise<{ trung: boolean; so_ho_so: string | null }> => {
  try {
    const q = `ma_kh=${encodeURIComponent(maKh)}&so_cmt=${encodeURIComponent(soCmt)}`;
    const r = await fetch(`${BASE}/local/kiem-trung-cccd?${q}`, { headers: authHeaders() });
    if (!r.ok) return { trung: false, so_ho_so: null };
    return (await r.json()) as { trung: boolean; so_ho_so: string | null };
  } catch {
    return { trung: false, so_ho_so: null };
  }
};

// ── NAP-01: kéo hàng đợi VPS → staging + nạp lô ──
export interface KeoVeRow {
  uuid: string;
  so_cccd: string | null;
  so_cmnd_cu: string | null;
  ho_ten: string | null;
  ngay_sinh: string | null; // yyyymmdd
  gioi_tinh: string | null;
  noi_tt_raw: string | null;
  ngay_cap: string | null; // yyyymmdd (đã đổi từ ISO)
  noi_cap_cccd: string | null;
  co_anh: number; // 0/1
  created_at: string | null;
  trang_thai: "cho" | "loi" | "xong";
  loi: string | null;
  ma_dk: string | null;
  so_ho_so: string | null;
}

// Kéo trọn bản ghi pending từ VPS về staging. Trả số mới thêm + làm tươi + bỏ-đã-xóa + reset-địa-chỉ + tổng.
export const keoHangDoi = () =>
  fetch(`${BASE}/local/nap/keo`, { method: "POST", headers: authHeaders() }).then(
    json<{ keo_ve: number; lam_tuoi: number; bo_da_xoa: number; dia_chi_reset: number; tong: number }>,
  );

export const getDanhSachKeoVe = () =>
  fetch(`${BASE}/local/nap/danh-sach`, { headers: authHeaders() }).then(json<KeoVeRow[]>);

// NAP-01 task 38 — "Bỏ khỏi hàng đợi": xóa 1 dòng đã nạp khỏi staging cục bộ (không đụng prod).
export const boKhoiHangDoi = (uuid: string) =>
  fetch(`${BASE}/local/keo-ve/${encodeURIComponent(uuid)}`, { method: "DELETE", headers: authHeaders() }).then(
    json<{ ok: boolean; uuid: string }>,
  );

// ── Nháp chuẩn bị BỀN (NAP-01 task 50/51, CHANGES #32, TDD §9.3a) ────────────
export interface NhapCo {
  uuid: string;
  co_dia_chi: boolean;
  co_anh: boolean;
  co_tick: boolean;
}

export interface NhapChuanBi {
  uuid: string;
  dia_chi_json: string | null;
  chi_tiet: string | null;
  noi_cap: string | null;
  tick_json: string | null;
  jp2_b64: string | null;
  anh_preview: string | null;
  updated_at: string | null;
}

// Cờ NHẸ (không kèm ảnh) để vẽ 2 chip cả lưới. Danh sách rỗng → không gọi mạng.
export const nhapCo = (uuids: string[]): Promise<NhapCo[]> =>
  uuids.length === 0
    ? Promise.resolve([])
    : fetch(`${BASE}/local/nap/nhap?uuids=${encodeURIComponent(uuids.join(","))}`, {
        headers: authHeaders(),
      }).then(json<NhapCo[]>);

// Đọc đầy đủ 1 nháp (kèm ảnh) — gọi khi mở drawer Chuẩn bị.
export const nhapDoc = (uuid: string) =>
  fetch(`${BASE}/local/nap/nhap/${encodeURIComponent(uuid)}`, { headers: authHeaders() }).then(
    json<NhapChuanBi>,
  );

// Lưu (upsert) nháp — gọi khi đóng drawer / debounce.
export const nhapLuu = (
  uuid: string,
  body: Partial<Omit<NhapChuanBi, "uuid" | "updated_at">>,
) =>
  fetch(`${BASE}/local/nap/nhap/${encodeURIComponent(uuid)}`, {
    method: "PUT",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  }).then(json<{ ok: boolean; uuid: string }>);

// Nút "Xóa nháp" — dọn 1 nháp (gồm ảnh PII) chủ động.
export const nhapXoa = (uuid: string) =>
  fetch(`${BASE}/local/nap/nhap/${encodeURIComponent(uuid)}`, {
    method: "DELETE",
    headers: authHeaders(),
  }).then(json<{ ok: boolean; uuid: string }>);

// ── QLY-09: Đối soát VPS↔CSDT (CHANGES #28, task 48/49) ──────────────────────
export interface DoiSoatDong {
  loai: string;              // "①" | "②" | "③"
  uuid?: string;
  ma_dk?: string;
  ho_ten?: string | null;
  trang_thai_vps?: string;   // ca ②
  locked_at?: string;        // ca ③
  hanh_dong: string;         // "da_nap" | "tra_ve_cho_nap" | "unlock"
}
export interface KhongTraDuoc { ma_dk: string; ho_ten?: string | null; ly_do?: string }

export const doiSoatKhoa = (maKh: string) =>
  fetch(`${BASE}/local/doi-soat/khoa?ma_kh=${encodeURIComponent(maKh)}`, { headers: authHeaders() })
    .then(json<{ ca2: DoiSoatDong[]; khong_tra_duoc: KhongTraDuoc[] }>);

export const quetLac = () =>
  fetch(`${BASE}/local/doi-soat/lac`, { headers: authHeaders() })
    .then(json<{ phantom: DoiSoatDong[]; treo: DoiSoatDong[] }>);

const _dsPost = (path: string) =>
  fetch(`${BASE}${path}`, { method: "POST", headers: authHeaders() }).then(json<{ ok: boolean }>);

export const doiSoatDaNap = (uuid: string, maDk: string) =>
  _dsPost(`/local/doi-soat/da-nap?uuid=${encodeURIComponent(uuid)}&ma_dk=${encodeURIComponent(maDk)}`);
export const doiSoatTraVe = (uuid: string) =>
  _dsPost(`/local/doi-soat/tra-ve?uuid=${encodeURIComponent(uuid)}`);
export const doiSoatMoKhoa = (uuid: string) =>
  _dsPost(`/local/doi-soat/mo-khoa?uuid=${encodeURIComponent(uuid)}`);

// Ảnh thô cần Bearer → tải bằng fetch rồi tạo object URL (thẻ <img> không gửi header được).
// Chưa có ảnh (404) → null.
export const taiAnhKeoVe = async (uuid: string): Promise<string | null> => {
  const r = await fetch(`${BASE}/local/nap/keo/${uuid}/anh`, { headers: authHeaders() });
  if (r.status === 404) return null;
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return URL.createObjectURL(await r.blob());
};

// QLY-05 (CHANGES #32) — ảnh THÔ học viên gửi còn trên VPS, tra theo ma_dk (nguồn bổ sung ảnh cho
// HV thiếu ảnh). Hết hạn/không tra được (404) → null → UI ẩn nguồn này, chỉ còn chọn-file.
export const taiAnhVps = async (maDk: string): Promise<string | null> => {
  const r = await fetch(`${BASE}/local/ho-so/anh-vps?ma_dk=${encodeURIComponent(maDk)}`, { headers: authHeaders() });
  if (r.status === 404) return null;
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return URL.createObjectURL(await r.blob());
};

export interface NapLoDong {
  uuid: string;
  ok: boolean;
  ma_dk?: string;
  so_ho_so?: string;
  so_giay_to?: number;
  loi?: string;
}

export interface NapLoKetQua {
  tong: number;
  thanh_cong: number;
  that_bai: number;
  ket_qua: NapLoDong[];
}

// Nạp lô các HV đã chuẩn bị đủ (khóa + địa chỉ + giấy tờ + ảnh). 1 lỗi không hỏng cả lô.
export const napLo = (items: NapIn[]) =>
  fetch(`${BASE}/local/nap/nap-lo`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ items }),
  }).then(json<NapLoKetQua>);

// ── Phân hệ Đồng bộ CDB — Quản lý CSDL đích (SYNC-02) ──
export interface SyncTarget {
  key: string;
  name: string;
  database: string;
}
export interface SyncOptions {
  tt_xuly_force: string;
  update_tong_so_hv: boolean;
}
export interface TtXuLyOption {
  ma: string;
  ten: string;
  ghi_chu: string;
}
export interface SyncTargetsData {
  targets: SyncTarget[];
  selected: string;
  options: SyncOptions;
  tt_xuly_options: TtXuLyOption[];
}
export interface SyncTestKetQua {
  ok: boolean;
  count: number;
  message: string;
}

export const getSyncTargets = () =>
  fetch(`${BASE}/local/sync/targets`, { headers: authHeaders() }).then(json<SyncTargetsData>);

export const saveSyncTargets = (
  targets: SyncTarget[],
  selected: string,
  options: SyncOptions,
) =>
  fetch(`${BASE}/local/sync/targets`, {
    method: "PUT",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ targets, selected, options }),
  }).then(json<SyncTargetsData>);

export const testSyncTarget = (database: string) =>
  fetch(`${BASE}/local/sync/targets/test`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ database }),
  }).then(json<SyncTestKetQua>);

// ── Phân hệ Đồng bộ CDB — Bàn đồng bộ (SYNC-01) ──
export interface SyncKhoa {
  ma_kh: string;
  ten_kh: string;
  hang_gplx: string;
  ngay_kg: string | null;
  so_hv: number;
  bc1?: boolean;
}
export interface SyncHV {
  ho_ten: string | null;
  so_cmt: string;
  hang_gplx: string | null;
  ma_dk_nguon: string | null;
  ngay_hs_nguon: string | null;
  da_co_dich: boolean;
  ma_dk_dich: string | null;
  ngay_hs_dich: string | null;
  so_hs_dich: number | null;
  thieu_cccd: boolean;
  trung_cccd_nguon: boolean;
}
export interface SyncHocVienData {
  hoc_vien: SyncHV[];
  tong: number;
  da_co_dich: number;
  se_tao_moi: number;
  thieu_cccd: number;
  trung_cccd_nguon: number;
}

const qs = (o: Record<string, string | number | undefined>) =>
  Object.entries(o)
    .filter(([, v]) => v !== undefined && v !== "")
    .map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`)
    .join("&");

export const getSyncNam = (ben: "nguon" | "dich", targetKey?: string) =>
  fetch(`${BASE}/local/sync/${ben}/nam?${qs({ target_key: ben === "dich" ? targetKey : undefined })}`, {
    headers: authHeaders(),
  }).then(json<number[]>);

export const getSyncKhoa = (ben: "nguon" | "dich", nam: number, targetKey?: string) =>
  fetch(`${BASE}/local/sync/${ben}/khoa?${qs({ nam, target_key: ben === "dich" ? targetKey : undefined })}`, {
    headers: authHeaders(),
  }).then(json<SyncKhoa[]>);

export const postSyncHocVien = (maKhNguon: string, targetKey?: string) =>
  fetch(`${BASE}/local/sync/hoc-vien`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ ma_kh_nguon: maKhNguon, target_key: targetKey }),
  }).then(json<SyncHocVienData>);

// ── TCB-01: Tra cứu CDB đích (đọc GPLX_CDB_CSDT) ──
export interface KhoaCDB {
  ma_kh: string;
  ten_kh: string;
  hang_gplx: string;
  hang_dt: string | null;
  bc1: boolean;   // khóa đã lập Báo cáo 1 (cấp khóa) — cờ cảnh báo
  dkkh: boolean;  // đã kết xuất DKKH (SoQD_KhaiGiang có giá trị)
}
// Dòng HV đích = HoSoRow + tt_xuly (hiện thêm ở chi tiết CDB).
export type HoSoRowCDB = HoSoRow & { tt_xuly: string | null };

export const traCuuKhoaCDB = (q: string, targetKey?: string) =>
  fetch(`${BASE}/local/sync/tra-cuu/khoa?${qs({ q, target_key: targetKey })}`, { headers: authHeaders() }).then(
    json<KhoaCDB[]>,
  );
export const dsHoSoCDB = (makh: string, targetKey?: string) =>
  fetch(`${BASE}/local/sync/tra-cuu/ho-so?${qs({ makh, target_key: targetKey })}`, { headers: authHeaders() }).then(
    json<HoSoRowCDB[]>,
  );
export const khoaCuaMaDkCDB = (maDk: string, targetKey?: string) =>
  fetch(`${BASE}/local/sync/tra-cuu/khoa-cua-madk?${qs({ ma_dk: maDk, target_key: targetKey })}`, {
    headers: authHeaders(),
  }).then(json<KhoaCDB>);
export const taiAnhCDB = (maDk: string, targetKey?: string, v = 0) =>
  taiAnhPNG(`/local/sync/tra-cuu/anh?${qs({ ma_dk: maDk, target_key: targetKey, v: v || undefined })}`);
export const taiAnhThumbCDB = (maDk: string, targetKey?: string, v = 0) =>
  taiAnhPNG(`/local/sync/tra-cuu/anh-thumb?${qs({ ma_dk: maDk, target_key: targetKey, v: v || undefined })}`);
// TCB-02 — thay ảnh HV ở CDB (ghi đè file dùng chung + backup _BACKUP + UPDATE cột ảnh CDB).
export const napAnhCDB = (maDk: string, jp2B64: string, targetKey?: string) =>
  fetch(`${BASE}/local/sync/tra-cuu/nap-anh?${qs({ ma_dk: maDk, target_key: targetKey })}`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ jp2_b64: jp2B64 }),
  }).then(json<{ ok: boolean; ma_dk: string; duong_dan_anh: string; co_anh: boolean }>);

export interface SyncRunIn {
  ma_kh_nguon: string;
  ma_kh_dich: string;
  ngay_nhap_hs: string; // ISO yyyy-mm-dd
  target_key?: string;
  so_cmt_chon: string[];
}
export const postSyncRun = (body: SyncRunIn) =>
  fetch(`${BASE}/local/sync/run`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body),
  }).then(json<{ job_id: string }>);

// Đọc SSE bằng fetch (EventSource không đặt được header Bearer). Gọi onEvent cho
// mỗi sự kiện {loai,...}. Trả AbortController để hủy (job nền vẫn chạy tới hết).
export function openSyncStream(jobId: string, onEvent: (ev: Record<string, unknown>) => void) {
  const ctrl = new AbortController();
  void (async () => {
    const r = await fetch(`${BASE}/local/sync/stream?job=${encodeURIComponent(jobId)}`, {
      headers: authHeaders(),
      signal: ctrl.signal,
    });
    if (!r.ok || !r.body) throw new Error(String(r.status));
    const reader = r.body.getReader();
    const dec = new TextDecoder();
    let buf = "";
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      let i: number;
      while ((i = buf.indexOf("\n\n")) >= 0) {
        const chunk = buf.slice(0, i);
        buf = buf.slice(i + 2);
        const line = chunk.split("\n").find((l) => l.startsWith("data:"));
        if (line) {
          try {
            onEvent(JSON.parse(line.slice(5).trim()));
          } catch {
            /* bỏ qua dòng không phải JSON (keepalive) */
          }
        }
      }
    }
  })().catch(() => {
    /* abort/ngắt mạng — bỏ qua, UI đã có nút chạy lại */
  });
  return ctrl;
}

// ── Phân hệ Đồng bộ CDB — Lịch sử & Hủy sync (SYNC-03) ──
export interface SyncLichSuRow {
  khoa_moi: string;
  khoa_cu: string | null;
  sync_at: string; // ISO
  can_bo: string;
  so_tao: number;
}
export const getSyncLichSu = () =>
  fetch(`${BASE}/local/sync/lich-su`, { headers: authHeaders() }).then(json<SyncLichSuRow[]>);

export interface SyncRollbackPreview {
  log_count: number;
  log_con_dich: number;
  sync_group: number;
  tong: number;
}
export const getSyncRollbackPreview = (maKh: string, targetKey?: string) =>
  fetch(`${BASE}/local/sync/rollback/preview?${qs({ ma_kh: maKh, target_key: targetKey })}`, {
    headers: authHeaders(),
  }).then(json<SyncRollbackPreview>);

export interface SyncRollbackKetQua {
  hs_del: number;
  nlx_del: number;
  tong_so_hv: number | null;
}
export const postSyncRollback = (maKh: string, targetKey?: string) =>
  fetch(`${BASE}/local/sync/rollback`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ ma_kh: maKh, target_key: targetKey }),
  }).then(json<SyncRollbackKetQua>);
