from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorInfo(BaseModel):
    code: str = Field(..., description="Stable machine-readable error code")
    message: str = Field(..., description="Human-readable summary")
    context: Any | None = Field(default=None, description="Optional structured error details")
    trace_id: str | None = Field(default=None, description="Correlation/trace id if available")   


class Frame(BaseModel, Generic[T]):
    """
    Success frame.
    - data: primary payload (object/list/scalar/null)
    - meta: non-business metadata (always an object if present)
    """
    data: T | None = Field(default=None)
    meta: dict[str, Any] | None = Field(default=None)


class ErrorFrame(BaseModel):
    """
    Error frame (single error object by design).
    """
    error: ErrorInfo
    meta: dict[str, Any] | None = Field(default=None)


class PageMeta(BaseModel):
    """
    Offset pagination meta.
    Stored under meta.page by builders.paged().
    """
    total: int
    limit: int
    offset: int
