import { useEffect, useState } from "react";
import { Icon } from "../../components/Icon";
import { PhanTrang } from "../../components/PhanTrang";
import { boDau, ymdToVN, maskNgay, nghiSaiChinhTa } from "../../lib/format";
import {
  traCuuKhoa,
  dsHoSoTheoKhoa,
  chiTietHoSo,
  suaHoSo,
  khoaCungHang,
  doiKhoa,
  type KhoaTraCuu,
  type KhoaDich,
  type HoSoRow,
  type HoSoSuaIn,
} from "../../lib/api";

// QLY-01 — Tra cứu DB. Tìm khóa (mọi khóa, kể cả BC1) → lưới HV theo khóa (tìm phía client:
// tên bỏ dấu / CCCD) → xem chi tiết → SỬA nhân thân (lát 2, chỉ khóa chưa BC1 — BR-012).
function gioiTinhVN(g: string | null): string {
  return g === "M" ? "Nam" : g === "F" ? "Nữ" : "—";
}

function Bc1Chip() {
  return (
    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-warning bg-warning/10 border border-warning/30 rounded-full px-2 py-0.5 whitespace-nowrap">
      <Icon name="warn" className="w-3 h-3" /> Đã BC1 — chỉ xem
    </span>
  );
}

const FORM_RONG: HoSoSuaIn = { ho_ten: "", ngay_sinh: "", gioi_tinh: "U", so_cccd: "", noi_tt: "" };

export default function TraCuuDB() {
  const [q, setQ] = useState("");
  const [khoaList, setKhoaList] = useState<KhoaTraCuu[] | null>(null);
  const [khoa, setKhoa] = useState<KhoaTraCuu | null>(null);
  const [hoSo, setHoSo] = useState<HoSoRow[] | null>(null);
  const [qHv, setQHv] = useState("");
  const [sel, setSel] = useState<HoSoRow | null>(null);
  const [loadingKhoa, setLoadingKhoa] = useState(false);
  const [loadingHv, setLoadingHv] = useState(false);
  const [err, setErr] = useState("");

  // Sửa nhân thân (lát 2)
  const [sua, setSua] = useState(false);
  const [form, setForm] = useState<HoSoSuaIn>(FORM_RONG);
  const [hktt, setHktt] = useState<string | null>(null);
  const [loadingCt, setLoadingCt] = useState(false);
  const [saving, setSaving] = useState(false);
  const [suaErr, setSuaErr] = useState("");
  const [okMsg, setOkMsg] = useState("");

  // Đổi khóa (QLY-02)
  const [doiMo, setDoiMo] = useState(false);
  const [khoaDich, setKhoaDich] = useState<KhoaDich[] | null>(null);
  const [maKhDich, setMaKhDich] = useState("");
  const [doiBusy, setDoiBusy] = useState(false);
  const [doiErr, setDoiErr] = useState("");

  async function timKhoa() {
    setErr("");
    setLoadingKhoa(true);
    setKhoa(null);
    setHoSo(null);
    try {
      setKhoaList(await traCuuKhoa(q));
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Không tìm được khóa.");
    } finally {
      setLoadingKhoa(false);
    }
  }

  async function chonKhoa(k: KhoaTraCuu) {
    setKhoa(k);
    setErr("");
    setHoSo(null);
    setQHv("");
    setLoadingHv(true);
    try {
      setHoSo(await dsHoSoTheoKhoa(k.ma_kh));
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Không tải được danh sách học viên.");
    } finally {
      setLoadingHv(false);
    }
  }

  function dong() {
    setSel(null);
    setSua(false);
    setSuaErr("");
    setDoiMo(false);
    setDoiErr("");
    setKhoaDich(null);
    setMaKhDich("");
  }

  async function moDoiKhoa() {
    if (!khoa) return;
    setDoiErr("");
    setDoiMo(true);
    setKhoaDich(null);
    setMaKhDich("");
    try {
      const ds = await khoaCungHang(khoa.ma_kh);
      setKhoaDich(ds);
      setMaKhDich(ds[0]?.ma_kh ?? "");
    } catch (e) {
      setDoiErr(e instanceof Error ? e.message : "Không tải được khóa đích.");
    }
  }

  async function chuyenKhoa() {
    if (!sel || !maKhDich) return;
    setDoiErr("");
    setDoiBusy(true);
    try {
      await doiKhoa(sel.ma_dk, maKhDich);
      if (khoa) setHoSo(await dsHoSoTheoKhoa(khoa.ma_kh)); // HV rời khóa → làm tươi lưới
      setOkMsg("Đã đổi khóa học viên.");
      setTimeout(() => setOkMsg(""), 2500);
      dong();
    } catch (e) {
      setDoiErr(e instanceof Error ? e.message : "Đổi khóa không thành công.");
    } finally {
      setDoiBusy(false);
    }
  }

  async function moSua() {
    if (!sel) return;
    setSuaErr("");
    setLoadingCt(true);
    try {
      const ct = await chiTietHoSo(sel.ma_dk);
      if (ct.bc1) {
        setSuaErr("Khóa đã lập Báo cáo 1 — chỉ xem, không sửa được.");
        return;
      }
      setForm({
        ho_ten: ct.ho_ten,
        ngay_sinh: ct.ngay_sinh,
        gioi_tinh: ct.gioi_tinh,
        so_cccd: ct.so_cccd,
        noi_tt: ct.noi_tt ?? "",
      });
      setHktt(ct.hktt);
      setSua(true);
    } catch (e) {
      setSuaErr(e instanceof Error ? e.message : "Không mở được hồ sơ để sửa.");
    } finally {
      setLoadingCt(false);
    }
  }

  async function luu() {
    if (!sel) return;
    if (!form.ho_ten.trim()) return setSuaErr("Chưa nhập họ và tên.");
    if (!/^\d{1,20}$/.test(form.so_cccd.trim())) return setSuaErr("Số căn cước phải là chữ số (tối đa 20).");
    setSuaErr("");
    setSaving(true);
    try {
      await suaHoSo(sel.ma_dk, { ...form, ho_ten: form.ho_ten.trim(), so_cccd: form.so_cccd.trim() });
      if (khoa) setHoSo(await dsHoSoTheoKhoa(khoa.ma_kh)); // làm tươi lưới đúng dữ liệu DB
      setOkMsg("Đã lưu thay đổi.");
      setTimeout(() => setOkMsg(""), 2500);
      dong();
    } catch (e) {
      setSuaErr(e instanceof Error ? e.message : "Lưu không thành công.");
    } finally {
      setSaving(false);
    }
  }

  const rows = (hoSo ?? []).filter((h) => {
    const t = qHv.trim();
    if (!t) return true;
    return boDau(h.ho_ten ?? "").includes(boDau(t)) || (h.so_cccd ?? "").includes(t);
  });
  // UI-3: phân trang lưới HV (client). Đổi khóa/ô tìm/cỡ trang → về trang 1.
  const [trang, setTrang] = useState(0);
  const [coTrang, setCoTrang] = useState(20);
  useEffect(() => { setTrang(0); }, [khoa, qHv, coTrang]);
  const rowsTrang = rows.slice(trang * coTrang, (trang + 1) * coTrang);
  const canhBaoTen = sua ? nghiSaiChinhTa(form.ho_ten) : "";

  return (
    <div className="p-4">
      {/* Tìm khóa */}
      <div className="flex items-end gap-2 flex-wrap">
        <div className="flex-1 min-w-[220px]">
          <label className="field-label">Tìm khóa (tên hoặc mã — mọi khóa, kể cả đã BC1)</label>
          <div className="relative mt-1">
            <Icon name="search" className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              className="field-input pl-9"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") void timKhoa(); }}
              placeholder="VD: B-K149 hoặc 70004K26B010"
            />
          </div>
        </div>
        <button
          type="button"
          onClick={() => void timKhoa()}
          disabled={loadingKhoa}
          className="h-10 px-4 rounded-lg bg-primary text-primary-foreground font-semibold text-sm inline-flex items-center gap-2 hover:brightness-110 transition-all shadow-sm disabled:opacity-60"
        >
          <Icon name={loadingKhoa ? "refresh" : "search"} className={"w-4 h-4" + (loadingKhoa ? " animate-spin" : "")} /> Tìm khóa
        </button>
      </div>

      {okMsg && (
        <div className="mt-3 flex items-center gap-2 text-[13px] text-success bg-success/10 border border-success/30 rounded-lg px-3 py-2">
          <Icon name="check" className="w-4 h-4 shrink-0" sw={3} /> {okMsg}
        </div>
      )}
      {err && (
        <div className="mt-3 flex items-center gap-2 text-[13px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2">
          <Icon name="warn" className="w-4 h-4 shrink-0" /> {err}
        </div>
      )}

      {/* Kết quả khóa */}
      {khoaList && !khoa && (
        <div className="mt-4">
          {khoaList.length === 0 ? (
            <p className="text-[13px] text-muted-foreground px-1">Không tìm thấy khóa khớp.</p>
          ) : (
            <div className="border border-border rounded-xl divide-y divide-border overflow-hidden">
              {khoaList.map((k) => (
                <button
                  key={k.ma_kh}
                  type="button"
                  onClick={() => void chonKhoa(k)}
                  className="w-full text-left flex items-center gap-3 px-4 py-2.5 hover:bg-muted/60 transition-colors"
                >
                  <div className="min-w-0 flex-1">
                    <div className="font-semibold text-[14px] truncate">{k.ten_kh || "(không tên)"}</div>
                    <div className="text-[12px] text-muted-foreground tabular-nums">
                      {k.ma_kh} · hạng {k.hang_gplx}
                    </div>
                  </div>
                  {k.bc1 && <Bc1Chip />}
                  <Icon name="chevronRight" className="w-4 h-4 text-muted-foreground shrink-0" />
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Lưới học viên trong khóa đã chọn */}
      {khoa && (
        <div className="mt-4">
          <div className="flex items-center gap-2 flex-wrap mb-3">
            <button type="button" onClick={() => setKhoa(null)} className="inline-flex items-center gap-1 text-[13px] text-primary font-medium hover:underline">
              <Icon name="chevronLeft" className="w-4 h-4" /> Danh sách khóa
            </button>
            <span className="text-[13px] font-bold">{khoa.ten_kh}</span>
            <span className="text-[12px] text-muted-foreground tabular-nums">{khoa.ma_kh} · hạng {khoa.hang_gplx}</span>
            {khoa.bc1 && <Bc1Chip />}
          </div>

          <div className="relative mb-2 max-w-sm">
            <Icon name="search" className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              className="field-input pl-9"
              value={qHv}
              onChange={(e) => setQHv(e.target.value)}
              placeholder="Tìm trong khóa: tên (không dấu được) hoặc CCCD"
            />
          </div>

          {loadingHv ? (
            <div className="px-4 py-8 text-center text-sm text-muted-foreground">
              <Icon name="refresh" className="w-4 h-4 animate-spin inline mr-1" /> Đang tải học viên…
            </div>
          ) : (
            <div className="border border-border rounded-xl overflow-hidden">
              <table className="w-full text-[13px]">
                <thead>
                  <tr className="bg-muted text-muted-foreground text-left">
                    <th className="px-3 py-2 font-semibold">Số HS</th>
                    <th className="px-3 py-2 font-semibold">Họ và tên</th>
                    <th className="px-3 py-2 font-semibold">Giới tính</th>
                    <th className="px-3 py-2 font-semibold">Ngày sinh</th>
                    <th className="px-3 py-2 font-semibold">Số CCCD</th>
                    <th className="px-3 py-2 font-semibold text-center">Ảnh</th>
                  </tr>
                </thead>
                <tbody>
                  {rowsTrang.map((h) => (
                    <tr key={h.ma_dk} onClick={() => setSel(h)} className="border-t border-border cursor-pointer hover:bg-muted/60 transition-colors">
                      <td className="px-3 py-2 tabular-nums">{h.so_ho_so || "—"}</td>
                      <td className="px-3 py-2 font-semibold">{h.ho_ten || "(chưa có tên)"}</td>
                      <td className="px-3 py-2">{gioiTinhVN(h.gioi_tinh)}</td>
                      <td className="px-3 py-2 tabular-nums">{ymdToVN(h.ngay_sinh)}</td>
                      <td className="px-3 py-2 tabular-nums">{h.so_cccd || "—"}</td>
                      <td className="px-3 py-2 text-center">
                        {h.co_anh ? <Icon name="check" className="w-4 h-4 text-success inline" sw={3} /> : <span className="text-[11px] text-warning">thiếu</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!rows.length && (
                <div className="px-4 py-8 text-center text-sm text-muted-foreground">
                  {qHv.trim() ? "Không tìm thấy học viên khớp." : "Khóa chưa có học viên."}
                </div>
              )}
            </div>
          )}
          {hoSo && (
            <>
              <PhanTrang total={rows.length} trang={trang} coTrang={coTrang} onTrang={setTrang} onCoTrang={setCoTrang} />
              <p className="text-[12px] text-muted-foreground mt-1">{rows.length}/{hoSo.length} học viên trong khóa</p>
            </>
          )}
        </div>
      )}

      {/* Chi tiết (xem) + Sửa nhân thân */}
      {sel && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={(e) => { if (e.target === e.currentTarget) dong(); }}>
          <div className="bg-card w-full max-w-md rounded-xl shadow-2xl max-h-[90vh] flex flex-col overflow-hidden">
            <div className="flex items-center justify-between px-5 py-3 border-b border-border">
              <h3 className="font-bold text-sm">{sua ? "Sửa thông tin nhân thân" : "Chi tiết học viên"}</h3>
              <button onClick={dong} aria-label="Đóng" className="w-8 h-8 rounded-lg hover:bg-muted flex items-center justify-center transition-colors">
                <Icon name="x" className="w-5 h-5" />
              </button>
            </div>

            {!sua ? (
              <>
                <div className="p-5 overflow-y-auto">
                  <div className="font-bold text-[15px]">{sel.ho_ten || "(chưa có tên)"}</div>
                  <div className="text-[12px] text-muted-foreground mt-0.5">Số hồ sơ {sel.so_ho_so || "—"} · {gioiTinhVN(sel.gioi_tinh)}</div>
                  <div className="mt-3 space-y-2">
                    {(
                      [
                        ["Số CCCD", sel.so_cccd || "—"],
                        ["Số CMND cũ", sel.so_cmnd_cu || "—"],
                        ["Ngày sinh", ymdToVN(sel.ngay_sinh)],
                        ["Nơi thường trú", sel.noi_tt || "—"],
                        ["Ảnh chân dung", sel.co_anh ? "Đã có" : "Thiếu ảnh"],
                      ] as [string, string][]
                    ).map(([k, v]) => (
                      <div key={k} className="flex justify-between gap-3 text-[13px] border-b border-border pb-2 last:border-0">
                        <span className="text-muted-foreground shrink-0">{k}</span>
                        <span className="font-medium text-right break-words">{v}</span>
                      </div>
                    ))}
                  </div>
                  {suaErr && (
                    <div className="mt-3 flex items-center gap-2 text-[12px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2">
                      <Icon name="warn" className="w-4 h-4 shrink-0" /> {suaErr}
                    </div>
                  )}

                  {/* Đổi khóa (QLY-02) — cùng hạng, chưa BC1 */}
                  {doiMo && (
                    <div className="mt-3 rounded-lg border border-border bg-muted/40 p-3 space-y-2">
                      <div className="text-[13px] font-semibold flex items-center gap-1.5">
                        <Icon name="send" className="w-4 h-4" /> Đổi sang khóa khác (cùng hạng)
                      </div>
                      {khoaDich === null ? (
                        <p className="text-[12px] text-muted-foreground flex items-center gap-1">
                          <Icon name="refresh" className="w-3.5 h-3.5 animate-spin" /> Đang tải khóa…
                        </p>
                      ) : khoaDich.length === 0 ? (
                        <p className="text-[12px] text-muted-foreground">Không có khóa cùng hạng (chưa BC1) để chuyển.</p>
                      ) : (
                        <>
                          <select className="field-input" value={maKhDich} onChange={(e) => setMaKhDich(e.target.value)}>
                            {khoaDich.map((k) => (
                              <option key={k.ma_kh} value={k.ma_kh}>{k.ma_kh} — {k.ten_kh}</option>
                            ))}
                          </select>
                          <p className="text-[11px] text-muted-foreground">Số hồ sơ cấp lại theo khóa mới; ảnh di chuyển sang thư mục khóa mới.</p>
                          <div className="flex gap-2">
                            <button onClick={() => { setDoiMo(false); setDoiErr(""); }} className="h-9 px-3 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors">Hủy</button>
                            <button
                              onClick={() => void chuyenKhoa()}
                              disabled={doiBusy || !maKhDich}
                              className="ml-auto h-9 px-4 rounded-lg bg-primary text-primary-foreground text-sm font-semibold inline-flex items-center gap-2 hover:brightness-110 transition-all disabled:opacity-60"
                            >
                              <Icon name={doiBusy ? "refresh" : "send"} className={"w-4 h-4" + (doiBusy ? " animate-spin" : "")} /> Chuyển sang khóa này
                            </button>
                          </div>
                        </>
                      )}
                      {doiErr && (
                        <p className="text-[12px] text-destructive flex items-center gap-1"><Icon name="warn" className="w-3.5 h-3.5" /> {doiErr}</p>
                      )}
                    </div>
                  )}

                  {khoa?.bc1 && (
                    <p className="text-[11px] text-warning mt-3 flex items-center gap-1">
                      <Icon name="warn" className="w-3.5 h-3.5" /> Khóa đã lập Báo cáo 1 — chỉ xem, không sửa/đổi được.
                    </p>
                  )}
                </div>
                <div className="p-3 border-t border-border flex gap-2">
                  <button onClick={dong} className="h-10 px-4 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors">Đóng</button>
                  {!khoa?.bc1 && !doiMo && (
                    <>
                      <button
                        onClick={() => void moDoiKhoa()}
                        className="ml-auto h-10 px-4 rounded-lg border border-border text-sm font-medium inline-flex items-center gap-1.5 hover:bg-muted transition-colors"
                      >
                        <Icon name="send" className="w-4 h-4" /> Đổi khóa
                      </button>
                      <button
                        onClick={() => void moSua()}
                        disabled={loadingCt}
                        className="h-10 px-5 rounded-lg bg-primary text-primary-foreground text-sm font-semibold inline-flex items-center gap-2 hover:brightness-110 transition-all shadow-sm disabled:opacity-60"
                      >
                        <Icon name={loadingCt ? "refresh" : "edit"} className={"w-4 h-4" + (loadingCt ? " animate-spin" : "")} /> Sửa
                      </button>
                    </>
                  )}
                </div>
              </>
            ) : (
              <>
                <div className="p-5 overflow-y-auto space-y-3">
                  <div>
                    <label className="field-label">Họ và tên</label>
                    <input
                      autoFocus
                      className="field-input mt-1"
                      value={form.ho_ten}
                      onChange={(e) => setForm({ ...form, ho_ten: e.target.value })}
                    />
                    {canhBaoTen && (
                      <p className="text-[11px] text-warning mt-1 flex items-center gap-1">
                        <Icon name="warn" className="w-3 h-3" /> {canhBaoTen}
                      </p>
                    )}
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="field-label">Ngày sinh</label>
                      <input
                        className="field-input mt-1 tabular-nums"
                        value={form.ngay_sinh}
                        onChange={(e) => setForm({ ...form, ngay_sinh: maskNgay(e.target.value) })}
                        placeholder="dd/mm/yyyy hoặc yyyy"
                        inputMode="numeric"
                      />
                    </div>
                    <div>
                      <label className="field-label">Giới tính</label>
                      <select
                        className="field-input mt-1"
                        value={form.gioi_tinh}
                        onChange={(e) => setForm({ ...form, gioi_tinh: e.target.value })}
                      >
                        <option value="M">Nam</option>
                        <option value="F">Nữ</option>
                        <option value="U">Không xác định</option>
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="field-label">Số căn cước</label>
                    <input
                      className="field-input mt-1 tabular-nums"
                      value={form.so_cccd}
                      onChange={(e) => setForm({ ...form, so_cccd: e.target.value.replace(/\D/g, "").slice(0, 20) })}
                      inputMode="numeric"
                    />
                  </div>
                  <div>
                    <label className="field-label">Nơi thường trú (chi tiết: số nhà / thôn)</label>
                    <input
                      className="field-input mt-1"
                      value={form.noi_tt}
                      maxLength={50}
                      onChange={(e) => setForm({ ...form, noi_tt: e.target.value })}
                    />
                    {hktt && <p className="text-[11px] text-muted-foreground mt-1">Thuộc: {hktt}</p>}
                  </div>
                  <p className="text-[11px] text-muted-foreground">Chỉ sửa thông tin nhân thân. Ảnh, khóa học không đổi ở đây.</p>
                  {suaErr && (
                    <div className="flex items-center gap-2 text-[12px] text-destructive bg-destructive/10 border border-destructive/30 rounded-lg px-3 py-2">
                      <Icon name="warn" className="w-4 h-4 shrink-0" /> {suaErr}
                    </div>
                  )}
                </div>
                <div className="p-3 border-t border-border flex gap-2">
                  <button onClick={() => { setSua(false); setSuaErr(""); }} className="h-10 px-4 rounded-lg border border-border text-sm font-medium hover:bg-muted transition-colors">Hủy</button>
                  <button
                    onClick={() => void luu()}
                    disabled={saving}
                    className="ml-auto h-10 px-5 rounded-lg bg-primary text-primary-foreground text-sm font-semibold inline-flex items-center gap-2 hover:brightness-110 transition-all shadow-sm disabled:opacity-60"
                  >
                    <Icon name={saving ? "refresh" : "check"} className={"w-4 h-4" + (saving ? " animate-spin" : "")} sw={3} /> Lưu
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
