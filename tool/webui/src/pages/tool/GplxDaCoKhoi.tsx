import { ComboLoc } from "../../components/ComboLoc";
import { ODate } from "../../components/ODate";
import {
  DS_HANG_GPLX, bangMoi, duocMienLyThuyet, khoaHang, laBangMoTo, loiBang, soGplxLa, tachKhoaHang, trungHangDangKy,
  type BangGplx,
} from "./gplxDaCo";

// Khối "GPLX đã có" ở ngăn Chuẩn bị (NAP-07): thu gọn mặc định, mỗi bằng 6 ô, thêm/xóa được nhiều bằng.
export function GplxDaCoKhoi({
  ds,
  onDoi,
  noiCap,
  hangKhoa,
  tuAppWeb,
  coBanMoi,
  onDungBanWeb,
}: {
  ds: BangGplx[];
  onDoi: (ds: BangGplx[]) => void;
  noiCap: { ma: string; ten: string }[];
  hangKhoa?: string | null;
  tuAppWeb: boolean;
  coBanMoi: boolean;
  onDungBanWeb: () => void;
}) {
  const sua = (i: number, p: Partial<BangGplx>) => onDoi(ds.map((b, j) => (j === i ? { ...b, ...p } : b)));

  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <label className="flex items-center gap-2 text-[13px] font-semibold cursor-pointer">
        <input
          type="checkbox"
          className="accent-primary w-4 h-4"
          checked={ds.length > 0}
          onChange={(e) => onDoi(e.target.checked ? [bangMoi()] : [])}
        />
        Học viên đã có GPLX
      </label>

      {coBanMoi && (
        <div className="mt-2 flex flex-wrap items-center gap-2 rounded-md bg-warning/10 px-2 py-1.5 text-[12px] text-warning">
          <span className="flex-1 min-w-[160px]">App web có bản mới, đang giữ bản đã sửa ở đây.</span>
          <button type="button" className="btn btn-secondary btn-row" onClick={onDungBanWeb}>Dùng bản app web</button>
        </div>
      )}

      {ds.length > 0 && (
        <>
          {tuAppWeb && !coBanMoi && (
            <p className="mt-2 rounded-md bg-primary/5 px-2 py-1.5 text-[12px] text-primary">Từ app web — kiểm lại với bằng thật, sửa nếu cần.</p>
          )}
          {ds.map((b, i) => (
            <div key={i} className="mt-3 border-t border-border pt-3 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[12.5px] font-semibold">Bằng {i + 1}</span>
                <button type="button" className="text-[12px] text-destructive" onClick={() => onDoi(ds.filter((_, j) => j !== i))}>Xóa</button>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="field-label">Hạng</label>
                  <ComboLoc
                    className="mt-1"
                    value={khoaHang(b)}
                    options={DS_HANG_GPLX}
                    onChon={(k) => sua(i, tachKhoaHang(k))}
                    placeholder="Gõ hạng, ví dụ B2"
                  />
                </div>
                <div>
                  <label className="field-label" htmlFor={`gplx-so-${i}`}>Số GPLX</label>
                  <input
                    id={`gplx-so-${i}`}
                    className="field-input mt-1"
                    inputMode="numeric"
                    maxLength={20}
                    value={b.so}
                    placeholder="12 chữ số"
                    onChange={(e) => sua(i, { so: e.target.value.replace(/\|/g, "") })}
                  />
                </div>
                <ODate label="Ngày trúng tuyển" value={b.ngay_tt} onChange={(v) => sua(i, { ngay_tt: v })} />
                <ODate label="Ngày cấp" value={b.ngay_cap} onChange={(v) => sua(i, { ngay_cap: v })} />
                {!laBangMoTo(b.hang) && <ODate label="Ngày hết hạn" value={b.ngay_hh} onChange={(v) => sua(i, { ngay_hh: v })} />}
                <div>
                  <label className="field-label">Nơi cấp</label>
                  <ComboLoc
                    className="mt-1"
                    value={b.don_vi}
                    options={noiCap}
                    onChon={(ma) => sua(i, { don_vi: ma })}
                    placeholder="Gõ mã hoặc tên tỉnh"
                  />
                </div>
              </div>
              {soGplxLa(b.so) && <p className="text-[12px] text-warning">Số GPLX thường có 12 chữ số — kiểm lại, vẫn lưu được.</p>}
              {loiBang(b).length > 0 && <p className="text-[12px] text-destructive">{loiBang(b).join(" · ")}</p>}
            </div>
          ))}
          <button type="button" className="btn btn-secondary btn-row mt-3" onClick={() => onDoi([...ds, bangMoi()])}>+ Thêm GPLX</button>
          {trungHangDangKy(hangKhoa, ds) && (
            <p className="mt-2 rounded-md bg-warning/10 px-2 py-1.5 text-[12px] text-warning">GPLX đã có trùng hạng đăng ký của khóa — kiểm lại, vẫn nạp được.</p>
          )}
          {duocMienLyThuyet(hangKhoa, ds) && (
            <p className="mt-2 rounded-md bg-success/10 px-2 py-1.5 text-[12px] text-success">Khóa mô tô, đã có bằng ô tô: miễn thi lý thuyết.</p>
          )}
        </>
      )}
    </div>
  );
}
