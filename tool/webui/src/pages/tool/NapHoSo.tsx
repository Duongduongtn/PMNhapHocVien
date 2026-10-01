import { useEffect, useState } from "react";
import { Icon } from "../../components/Icon";
import AddressCombo from "../../components/AddressCombo";
import AnhModal from "../../components/AnhModal";
import { getKhoaHoc, type KhoaHoc, type LoaiXe } from "../../lib/api";

// NAP-02: chọn Mô tô/Ô tô + khóa chưa lập BC1, suy hạng/MaLoaiHs theo khóa.
// Các cột Danh sách HV / Thông tin / Ảnh (NAP-01, 03, 04, 05, 06) dựng ở task sau.
export default function NapHoSo() {
  const [loai, setLoai] = useState<LoaiXe>("oto");
  const [list, setList] = useState<KhoaHoc[]>([]);
  const [maKh, setMaKh] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string>("");
  const [anhOpen, setAnhOpen] = useState(false);

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

  return (
    <div>
      <div className="flex items-center gap-2 px-4 pt-4">
        <h2 className="text-base font-bold">Nạp hồ sơ vào DB</h2>
        <span className="text-[11px] font-semibold text-primary bg-primary/10 rounded-full px-2 py-0.5">NAP-02</span>
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

      {/* NAP-03: map địa chỉ nơi thường trú */}
      <div className="m-4">
        <AddressCombo />
      </div>

      {/* NAP-04: ảnh chân dung */}
      <div className="mx-4 mb-4 rounded-lg border border-border bg-card p-4 flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <Icon name="file" className="w-4 h-4 text-primary" />
          <span className="text-sm font-bold">Ảnh chân dung</span>
          <span className="text-[11px] font-semibold text-primary bg-primary/10 rounded-full px-2 py-0.5">NAP-04</span>
        </div>
        <span className="text-[12px] text-muted-foreground">Căn 3:4, xóa phông nền trắng, xuất .jp2 353×471.</span>
        <button
          onClick={() => setAnhOpen(true)}
          className="ml-auto inline-flex items-center gap-2 h-9 px-4 rounded-lg border border-primary text-primary font-semibold text-sm hover:bg-primary/5 transition-colors"
        >
          <Icon name="file" className="w-4 h-4" /> Mở trình chỉnh ảnh
        </button>
      </div>

      {/* Phần còn lại của màn Nạp dựng ở task sau (NAP-01/05/06) */}
      <div className="mx-4 mb-4 rounded-lg border border-dashed border-border bg-muted/30 px-4 py-8 text-center text-[13px] text-muted-foreground">
        Danh sách học viên · Thông tin cá nhân · ghép Nạp — dựng ở các bước tiếp theo (NAP-01, NAP-05, NAP-06).
      </div>

      {anhOpen && <AnhModal onDong={() => setAnhOpen(false)} />}
    </div>
  );
}
