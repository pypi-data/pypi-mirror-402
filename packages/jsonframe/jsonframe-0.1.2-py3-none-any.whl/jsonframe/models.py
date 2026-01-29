from __future__ import annotations

from typing import Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorInfo(BaseModel):
    code: str = Field(..., description="Stable machine-readable error code")
    message: str = Field(..., description="Human-readable summary")
    context: Any | None = Field(default=None, description="Optional structured error details")


class Frame(BaseModel, Generic[T]):
    """
    Success frame.
    - data: primary payload (object/list/scalar/null)
    - meta: non-business metadata (always an object if present)
    """
    data: T | None = Field(default=None)
    meta: dict[str, Any] | None = Field(default=None)


class ErrorDetail(BaseModel):
    """
    Structured error payload for `detail`.
    """
    error: ErrorInfo
    meta: dict[str, Any] | None = Field(default=None)


class ErrorFrame(BaseModel):
    """
    Error frame (string or structured detail).
    """
    detail: str | ErrorDetail


class PageMeta(BaseModel):
    """
    Offset pagination meta.
    Stored under meta.page by builders.paged().
    """
    total: int
    limit: int
    offset: int
