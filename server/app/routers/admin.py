"""Quản trị khác — chỉ admin (HTG-04).

Hiện `TOOL_API_KEY` để admin cấu hình tool mà không phải SSH vào máy chủ.
Đánh đổi bảo mật đã chốt ở PRD HTG-04: chỉ admin thấy, KHÔNG ghi log giá trị key.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.deps import require_role
from app.config import get_settings
from app.models.user import User

router = APIRouter(prefix="/api/admin", tags=["admin"])


class ToolKeyOut(BaseModel):
    tool_key: str


@router.get("/tool-key", response_model=ToolKeyOut)
def xem_tool_key(_admin: User = Depends(require_role("admin"))) -> ToolKeyOut:
    """Trả X-Tool-Key (khóa kết nối tool) cho admin. Không log giá trị."""
    return ToolKeyOut(tool_key=get_settings().tool_api_key)
