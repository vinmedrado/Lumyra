from __future__ import annotations
from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel
T = TypeVar('T')
class ApiResponse(BaseModel, Generic[T]):
    ok: bool = True
    data: Optional[T] = None
    message: str = ''
class ErrorResponse(BaseModel):
    ok: bool = False
    message: str
    detail: Any | None = None
