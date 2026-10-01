import { useEffect, useState } from "react";
import { Icon } from "../../components/Icon";
import AddressCombo, { type DiaChiMoi } from "../../components/AddressCombo";
import AnhModal from "../../components/AnhModal";
import {
  getKhoaHoc,
  getGiayTo,
  napHoSo,
  kiemTrungCccd,
  type KhoaHoc,
  type LoaiXe,
  type GiayTo,
  type NapKetQua,
} from "../../lib/api";

// dd/mm/yyyy → yyyymmdd (cột NgaySinh varchar(8)); không hợp lệ → null.
function toYmd(s: string): string | null {
  const m = s.trim().match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (!m) return null;
  const [, d, mo, y] = m;
  return `${y}${mo}${d}`;
}

// NAP-02: chọn Mô tô/Ô tô + khóa chưa BC1. NAP-03: map địa chỉ. NAP-04: ảnh.
// NAP-05 (2/2): form nhập tay 1 HV + giấy tờ theo tick + nút Nạp (POST /local/nap).
export default function NapHoSo() {
  const [loai, setLoai] = useState<LoaiXe>("oto");
  const [list, setList] = useState<KhoaHoc[]>([]);
  const [maKh, setMaKh] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string>("");
  const [anhOpen, setAnhOpen] = useState(false);

  // Form nhập tay 1 HV
  const [hoTen, setHoTen] = useState("");
  const [ngaySinh, setNgaySinh] = useState("");
  const [gioiTinh, setGioiTinh] = useState("M");
  const [soCmt, setSoCmt] = useState("");
  const [trungCccd, setTrungCccd] = useState<{ trung: boolean; so_ho_so: string | null }>({
    trung: false,
    so_ho_so: null,
  }); // NAP-06: cảnh báo sớm CCCD đã có trong khóa
  const [diaChi, setDiaChi] = useState<DiaChiMoi | null>(null);
  const [chiTiet, setChiTiet] = useState(""); // số nhà/thôn — NoiTT; mặc định trống (khớp app cũ)
  const [jp2, setJp2] = useState<string | null>(null);

  const [giayTo, setGiayTo] = useState<GiayTo[]>([]);
  const [tick, setTick] = useState<Set<number>>(new Set());

  const [uuid, setUuid] = useState(() => crypto.randomUUID());
  const [napBusy, setNapBusy] = useState(false);
  const [napErr, setNapErr] = useState("");
  const [napKq, setNapKq] = useState<NapKetQua | null>(null);

  useEffect(() => {
    let huy = false;
    setLoading(true);
    setErr("");
    getKhoaHoc(loai)
      .then((ks) => {
        if (huy) return;
        setList(ks);
        setMaKh(ks[0]?.ma_kh ?? "");
      })
      .catch(() => !huy && setErr("Không tải được danh sách khóa — kiểm cấu hình kết nối."))
      .finally(() => !huy && setLoading(false));
    return () => {
      huy = true;
    };
  }, [loai]);

  const khoa = list.find((k) => k.ma_kh === maKh) ?? null;

  // Giấy tờ bắt buộc theo khóa (loại HS + hạng ĐT) — tick sẵn tất cả, cho bỏ tick.
  useEffect(() => {
    if (!khoa) {
      setGiayTo([]);
      setTick(new Set());
      return;
    }
    let huy = false;
    getGiayTo(khoa.ma_loai_hs, khoa.hang_dt || khoa.hang_gplx)
      .then((gs) => {
        if (huy) return;
        setGiayTo(gs);
        setTick(new Set(gs.map((g) => g.ma_gt)));
      })
      .catch(() => {
        if (huy) return;
        setGiayTo([]);
        setTick(new Set());
      });
    return () => {
      huy = true;
    };
  }, [maKh, khoa?.ma_loai_hs, khoa?.hang_dt]);

  const toggleTick = (ma: number) =>
    setTick((prev) => {
      const next = new Set(prev);
      next.has(ma) ? next.delete(ma) : next.add(ma);
      return next;
    });

  const doNap = async () => {
    setNapErr("");
    setNapKq(null);
    if (!khoa) {
      setNapErr("Chưa chọn khóa đích.");
      return;
    }
    const ymd = toYmd(ngaySinh);
    if (!hoTen.trim() || !ymd || !soCmt.trim() || !diaChi) {
      setNapErr("Điền đủ Họ tên, Ngày sinh (dd/mm/yyyy), CCCD và Nơi thường trú trước khi nạp.");
      return;
    }
    if (trungCccd.trung) {
      setNapErr(`CCCD ${soCmt.trim()} đã có trong khóa này (Số hồ sơ ${trungCccd.so_ho_so}) — không nạp trùng (NAP-06).`);
      return;
    }
    setNapBusy(true);
    try {
      const kq = await napHoSo({
        uuid,
        ma_khoa_hoc: khoa.ma_kh,
        ho_ten: hoTen.trim(),
        ngay_sinh: ymd,
        gioi_tinh: gioiTinh,
        so_cmt: soCmt.trim(),
        chi_tiet_tt: chiTiet.trim() || undefined, // trống → NoiTT trống (địa chỉ từ mã DVHC)
        noi_tt_ma_dvhc: diaChi.ma_dvhc,
        noi_tt_ma_dvql: diaChi.ma_dvql,
        giay_to_tick: [...tick],
        anh_jp2_b64: jp2,
      });
      setNapKq(kq);
      setUuid(crypto.randomUUID()); // HV đã nạp → đổi uuid cho HV kế (chống nạp trùng)
      setHoTen("");
      setNgaySinh("");
      setSoCmt("");
      setTrungCccd({ trung: false, so_ho_so: null });
      setJp2(null);
      setDiaChi(null);
      setChiTiet("");
    } catch (e) {
      setNapErr(e instanceof Error ? e.message : "Nạp hồ sơ thất bại.");
    } finally {
      setNapBusy(false);
    }
  };

  return (
    <div>
      <div className="flex items-center gap-2 px-4 pt-4">
        <h2 className="text-base font-bold">Nạp hồ sơ vào DB</h2>
        <span className="text-[11px] font-semibold text-primary bg-primary/10 rounded-full px-2 py-0.5">NAP-05</span>
      </div>

      {/* Toolbar chọn loại + khóa đích */}
      <div className="px-4 py-3 mt-2 border-y border-border bg-muted/40 flex items-center gap-4 flex-wrap">
        <div className="inline-flex rounded-lg border border-border bg-card p-0.5">
          {(["moto", "oto"] as const).map((l) => (
            <button
              key={l}
              onClick={() => setLoai(l)}
              className={
                "px-4 py-1.5 text-sm rounded-md transition-colors " +
                (loai === l ? "bg-primary text-primary-foreground font-semibold" : "text-muted-foreground font-medium hover:text-foreground")
              }
            >
              {l === "moto" ? "Mô tô" : "Ô tô"}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <label className="field-label whitespace-nowrap">Khóa đích</label>
          {loading ? (
            <span className="inline-flex items-center gap-2 text-[13px] text-muted-foreground">
              <Icon name="refresh" className="w-4 h-4 animate-spin" /> Đang tải…
            </span>
          ) : list.length === 0 ? (
            <span className="inline-flex items-center gap-1.5 text-[13px] text-warning bg-warning/10 border border-warning/30 rounded-lg px-3 py-1.5">
              <Icon name="warn" className="w-4 h-4" /> Không có khóa nhận học viên (chưa lập BC1)
            </span>
          ) : (
            <select
              className="field-input"
              style={{ minWidth: 320 }}
              value={maKh}
              onChange={(e) => setMaKh(e.target.value)}
            >
              {list.map((k) => (
                <option key={k.ma_kh} value={k.ma_kh}>
                  {k.ma_kh} — {k.ten_kh}
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Giá trị suy ra theo khóa (tự điền khi nạp) */}
        {khoa && (
          <div className="flex items-center gap-2 text-[12px] flex-wrap">
            <span className="inline-flex items-center gap-1 rounded-full bg-secondary px-2.5 py-1">
              Hạng ĐT <b className="text-foreground">{khoa.hang_dt || khoa.hang_gplx}</b>
            </span>
            <span className="inline-flex items-center gap-1 rounded-full bg-secondary px-2.5 py-1">
              Hạng GPLX <b className="text-foreground">{khoa.hang_gplx}</b>
            </span>
            <span className="inline-flex items-center gap-1 rounded-full bg-secondary px-2.5 py-1">
              Loại HS <b className="text-foreground">{khoa.ma_loai_hs === 1 ? "1 · Mô tô" : "2 · Ô tô"}</b>
            </span>
            <span className="inline-flex items-center gap-1 rounded-full bg-secondary px-2.5 py-1">
              Sở GTVT <b className="text-foreground">{khoa.ma_so_gtvt}</b>
            </span>
          </div>
        )}
      </div>

      {err && (
        <div className="mx-4 mt-4 flex items-center gap-2 text-[13px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2">
          <Icon name="warn" className="w-4 h-4" /> {err}
        </div>
      )}

      {/* NAP-05: thông tin học viên (nhập tay 1 HV) */}
      <div className="mx-4 mt-4 rounded-lg border border-destructive/25 bg-destructive/[0.03] p-4">
        <div className="flex items-center gap-2 mb-3">
          <span className="inline-flex items-center gap-1.5 text-[11px] font-bold text-destructive">
            <span className="w-1.5 h-1.5 rounded-full bg-destructive" /> BẮT BUỘC
          </span>
          <div className="flex-1 h-px bg-border" />
          <span className="text-[10px] text-muted-foreground">* phải điền mới nạp được</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="sm:col-span-2">
            <label className="field-label">
              Họ và tên <span className="text-destructive">*</span>{" "}
              <span className="text-muted-foreground font-normal">(≤50, giữ dấu)</span>
            </label>
            <input className="field-input mt-1" value={hoTen} onChange={(e) => setHoTen(e.target.value)} placeholder="VD: Nguyễn Thanh Tâm" />
          </div>
          <div>
            <label className="field-label">Ngày sinh <span className="text-destructive">*</span></label>
            <input className="field-input mt-1" value={ngaySinh} onChange={(e) => setNgaySinh(e.target.value)} placeholder="dd/mm/yyyy" />
          </div>
          <div>
            <label className="field-label">Giới tính <span className="text-destructive">*</span></label>
            <select className="field-input mt-1" value={gioiTinh} onChange={(e) => setGioiTinh(e.target.value)}>
              <option value="M">Nam</option>
              <option value="F">Nữ</option>
            </select>
          </div>
          <div className="sm:col-span-2">
            <label className="field-label">Số CCCD <span className="text-destructive">*</span></label>
            <input
              className={"field-input mt-1" + (trungCccd.trung ? " border-destructive" : "")}
              value={soCmt}
              onChange={(e) => {
                setSoCmt(e.target.value);
                if (trungCccd.trung) setTrungCccd({ trung: false, so_ho_so: null });
              }}
              onBlur={async () => {
                if (!khoa || !soCmt.trim()) return;
                setTrungCccd(await kiemTrungCccd(khoa.ma_kh, soCmt.trim()));
              }}
              placeholder="VD: 070202008455"
            />
            {trungCccd.trung && (
              <div
                role="alert"
                className="mt-2 flex items-start gap-2 rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-[13px] font-medium text-destructive"
              >
                <Icon name="warn" className="mt-0.5 w-4 h-4 shrink-0" />
                <span>
                  <b>Trùng CCCD trong khóa:</b> số {soCmt.trim()} đã có học viên ở{" "}
                  <b>Số hồ sơ {trungCccd.so_ho_so}</b> của khóa này — không thể nạp trùng. Kiểm lại CCCD hoặc chọn khóa khác.
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* NAP-03: map địa chỉ nơi thường trú */}
      <div className="m-4">
        <AddressCombo onChon={setDiaChi} />
        <div className="mt-3">
          <label className="field-label">
            Chi tiết địa chỉ{" "}
            <span className="text-muted-foreground font-normal">(số nhà/thôn — không bắt buộc; để trống nếu chỉ có xã/tỉnh)</span>
          </label>
          <input
            className="field-input mt-1"
            value={chiTiet}
            onChange={(e) => setChiTiet(e.target.value)}
            placeholder="VD: Số 12, ngõ 5, thôn Đoài"
          />
        </div>
      </div>

      {/* NAP-04: ảnh chân dung */}
      <div className="mx-4 mb-4 rounded-lg border border-border bg-card p-4 flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <Icon name="file" className="w-4 h-4 text-primary" />
          <span className="text-sm font-bold">Ảnh chân dung</span>
          <span className="text-[11px] font-semibold text-primary bg-primary/10 rounded-full px-2 py-0.5">NAP-04</span>
        </div>
        <span className="text-[12px] text-muted-foreground">Căn 3:4, xóa phông nền trắng, xuất .jp2 353×471.</span>
        {jp2 ? (
          <span className="inline-flex items-center gap-1.5 text-[12px] font-semibold text-success bg-success/10 border border-success/30 rounded-full px-2.5 py-1">
            <Icon name="check" className="w-3.5 h-3.5" sw={3} /> Đã có ảnh — sẽ ghi .jp2 tên = MaDK
          </span>
        ) : (
          <span className="text-[12px] text-muted-foreground">Chưa có ảnh — vẫn nạp được (TT_XuLy 01, BR-011).</span>
        )}
        <button
          onClick={() => setAnhOpen(true)}
          className="ml-auto inline-flex items-center gap-2 h-9 px-4 rounded-lg border border-primary text-primary font-semibold text-sm hover:bg-primary/5 transition-colors"
        >
          <Icon name="file" className="w-4 h-4" /> Mở trình chỉnh ảnh
        </button>
      </div>

      {/* NAP-05: giấy tờ kèm theo (theo tick cuối) */}
      <div className="mx-4 mb-4 rounded-lg border border-border bg-card p-4">
        <h3 className="text-sm font-bold mb-1 flex items-center gap-2">
          Giấy tờ kèm theo
          <span className="font-normal text-muted-foreground text-[11px]">(tick sẵn — bỏ tick được, ghi theo tick cuối)</span>
        </h3>
        {giayTo.length === 0 ? (
          <p className="text-[13px] text-muted-foreground mt-2">
            {khoa ? "Chưa tải được danh mục giấy tờ cho khóa này — kiểm kết nối." : "Chọn khóa đích để hiện giấy tờ bắt buộc."}
          </p>
        ) : (
          <div className="space-y-1.5 text-[13px] mt-2">
            {giayTo.map((g) => (
              <label key={g.ma_gt} className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={tick.has(g.ma_gt)} onChange={() => toggleTick(g.ma_gt)} className="w-4 h-4 accent-primary" />
                {g.ten_gt}
              </label>
            ))}
          </div>
        )}
      </div>

      {/* Nút Nạp + kết quả */}
      <div className="mx-4 mb-6 rounded-lg border border-border bg-muted/20 p-4">
        {napKq && (
          <div className="mb-3 flex items-center gap-2 text-[13px] font-semibold text-success bg-success/10 border border-success/30 rounded-lg px-3 py-2">
            <Icon name="check" className="w-4 h-4" sw={3} /> Đã nạp: Số hồ sơ <b>{napKq.so_ho_so}</b> · MaDK{" "}
            <span className="font-mono">{napKq.ma_dk}</span> · {napKq.so_giay_to} giấy tờ
          </div>
        )}
        {napErr && (
          <div className="mb-3 flex items-center gap-2 text-[13px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2">
            <Icon name="warn" className="w-4 h-4" /> {napErr}
          </div>
        )}
        <button
          onClick={doNap}
          disabled={napBusy || !khoa}
          className="w-full h-11 rounded-lg bg-primary text-primary-foreground font-semibold text-sm flex items-center justify-center gap-2 hover:brightness-110 transition-all shadow-sm disabled:opacity-60"
        >
          <Icon name={napBusy ? "refresh" : "plus"} className={"w-4 h-4" + (napBusy ? " animate-spin" : "")} />
          {napBusy ? "Đang nạp…" : khoa ? `Nạp hồ sơ này vào ${khoa.ma_kh}` : "Chọn khóa để nạp"}
        </button>
      </div>

      {anhOpen && <AnhModal onDong={() => setAnhOpen(false)} onXong={(b64) => setJp2(b64)} />}
    </div>
  );
}
