# -*- coding: utf-8 -*-
"""Nhật ký JSON cục bộ cho phân hệ Đồng bộ CDB (port từ sync_tool v2.0).

Thay cơ chế đánh dấu record bằng cột NguoiTao (CSDL đích sạch, không dấu vết
công cụ). Rollback (Hủy sync khóa) dựa vào các file JSON ở:

    %APPDATA%\\GPLX_Sync\\history\\<MaKhoaHoc>_<timestamp>.json

Mỗi lần bấm SYNC sinh 1 file; ghi (atomic) sau MỖI HV thành công để không mất
dữ liệu nếu tool tắt giữa chừng. Giữ tên thư mục `GPLX_Sync` để tương thích
nhật ký công cụ cũ trên cùng máy.
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "2.0"
DEFAULT_APP_FOLDER = "GPLX_Sync"
HISTORY_SUBFOLDER = "history"


def _resolve_base_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata and appdata.strip():
        return Path(appdata) / DEFAULT_APP_FOLDER
    return Path.home() / f".{DEFAULT_APP_FOLDER.lower()}"


def _json_default(obj):
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"Không serialize được {type(obj)} sang JSON")


def _atomic_write_json(path: Path, data: dict) -> None:
    """Ghi JSON atomic: tempfile cùng thư mục → fsync → os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=_json_default)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except (OSError, TypeError, ValueError):
        Path(tmp).unlink(missing_ok=True)
        raise


def _parse_date(s):
    return date.fromisoformat(s) if isinstance(s, str) else s


def _parse_datetime(s):
    return datetime.fromisoformat(s) if isinstance(s, str) else s


@dataclass
class SyncBatch:
    """Một lần bấm SYNC = một file JSON.

    ma_dk_moi: MaDK sinh mới (HV chưa có ở đích). Nghiệp vụ 1 người = 1 hồ sơ
    nên hiện chỉ dùng nhóm này; ma_dk_doi/ma_dk_giu giữ để tương thích đọc
    nhật ký công cụ cũ.
    """
    khoa_moi: str
    khoa_cu: Optional[str]
    ngay_nhap_hs_chon: date
    can_bo: str
    sync_at_start: datetime
    sync_at_last_update: datetime = field(default_factory=datetime.now)
    ma_dk_moi: list[str] = field(default_factory=list)
    ma_dk_doi: dict[str, dict] = field(default_factory=dict)
    ma_dk_giu: list[str] = field(default_factory=list)
    # Tên khóa lưu lúc sync (CHANGES #41) — bản ghi cũ rỗng, /lich-su tra DB bù.
    ten_khoa_moi: str = ""   # tên khóa ĐÍCH (CDB)
    ten_khoa_cu: str = ""    # tên khóa NGUỒN (CSDT)

    def all_ma_dk_new(self) -> set[str]:
        result: set[str] = set(self.ma_dk_moi)
        for info in self.ma_dk_doi.values():
            if info.get("ma_dk_moi"):
                result.add(info["ma_dk_moi"])
        result.update(self.ma_dk_giu)
        return result

    def to_dict(self) -> dict:
        return {
            "version": SCHEMA_VERSION,
            "khoa_moi": self.khoa_moi,
            "khoa_cu": self.khoa_cu,
            "ngay_nhap_hs_chon": self.ngay_nhap_hs_chon,
            "sync_at_start": self.sync_at_start,
            "sync_at_last_update": self.sync_at_last_update,
            "can_bo": self.can_bo,
            "ma_dk_moi": self.ma_dk_moi,
            "ma_dk_doi": self.ma_dk_doi,
            "ma_dk_giu": self.ma_dk_giu,
            "ten_khoa_moi": self.ten_khoa_moi,
            "ten_khoa_cu": self.ten_khoa_cu,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SyncBatch":
        ngay = data.get("ngay_nhap_hs_chon")
        start = data.get("sync_at_start")
        last = data.get("sync_at_last_update")
        start_dt = _parse_datetime(start) if start else datetime.now()
        return cls(
            khoa_moi=data.get("khoa_moi", ""),
            khoa_cu=data.get("khoa_cu"),
            ngay_nhap_hs_chon=_parse_date(ngay) if ngay else date.today(),
            can_bo=data.get("can_bo", ""),
            sync_at_start=start_dt,
            sync_at_last_update=_parse_datetime(last) if last else start_dt,
            ma_dk_moi=list(data.get("ma_dk_moi", []) or []),
            ma_dk_doi=dict(data.get("ma_dk_doi", {}) or {}),
            ma_dk_giu=list(data.get("ma_dk_giu", []) or []),
            ten_khoa_moi=data.get("ten_khoa_moi", "") or "",
            ten_khoa_cu=data.get("ten_khoa_cu", "") or "",
        )


class HistoryStore:
    """Quản lý thư mục nhật ký JSON. Test truyền `base_dir` riêng để cô lập."""

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        root = Path(base_dir) if base_dir else _resolve_base_dir()
        self.base_dir: Path = root
        self.history_dir: Path = root / HISTORY_SUBFOLDER
        self.history_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _safe(ma_kh: str) -> str:
        return "".join(c if c.isalnum() or c in "-_" else "_" for c in (ma_kh or "unknown"))

    def _filename_for(self, batch: SyncBatch) -> str:
        ts = batch.sync_at_start.strftime("%Y%m%d_%H%M%S")
        return f"{self._safe(batch.khoa_moi)}_{ts}.json"

    def save_batch(self, batch: SyncBatch) -> Path:
        """Ghi 1 batch ra file. Gọi nhiều lần cùng instance → overwrite đúng
        file (dựa sync_at_start → tên không đổi)."""
        batch.sync_at_last_update = datetime.now()
        path = self.history_dir / self._filename_for(batch)
        _atomic_write_json(path, batch.to_dict())
        return path

    def load_batches_for_khoa(self, ma_kh: str) -> list[SyncBatch]:
        """Load mọi file `<ma_kh>_*.json`, bỏ qua file hỏng. Sort theo thời gian."""
        if not ma_kh:
            return []
        batches: list[SyncBatch] = []
        for path in self.history_dir.glob(f"{self._safe(ma_kh)}_*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    batches.append(SyncBatch.from_dict(json.load(f)))
            except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
                logger.warning("Bỏ qua file nhật ký hỏng %s: %s", path.name, exc)
        batches.sort(key=lambda b: b.sync_at_start)
        return batches

    def get_all_ma_dk_for_khoa(self, ma_kh: str) -> set[str]:
        """Union MaDK đã tạo của khóa — dùng cho rollback WHERE MaDK IN (...)."""
        result: set[str] = set()
        for b in self.load_batches_for_khoa(ma_kh):
            result.update(b.all_ma_dk_new())
        return result

    def list_all_batches(self) -> list[SyncBatch]:
        """Mọi lần sync đã ghi nhật ký (mọi khóa) — cho màn Lịch sử. File hỏng bỏ
        qua. Sort mới nhất lên đầu."""
        batches: list[SyncBatch] = []
        for path in self.history_dir.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    batches.append(SyncBatch.from_dict(json.load(f)))
            except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
                logger.warning("Bỏ qua file nhật ký hỏng %s: %s", path.name, exc)
        batches.sort(key=lambda b: b.sync_at_start, reverse=True)
        return batches
