from __future__ import annotations

from typing import Any, TypeVar

from .models import ErrorFrame,ErrorInfo, Frame, PageMeta

T = TypeVar("T")


def ok(data: T | None = None, *, meta: dict[str, Any] | None = None) -> Frame[T]:
    return Frame[T](data=data, meta=meta)

def ok_paged(
    data: list[T],
    *,
    total: int,
    limit: int,
    offset: int,
    meta: dict[str, Any] | None = None,
) -> Frame[list[T]]:
    page = PageMeta(total=total, limit=limit, offset=offset).model_dump(exclude_none=True)
    merged_meta = {**(meta or {}), "page": page}
    return ok(data, meta=merged_meta)

def error(
    *,
    code: str,
    message: str,
    context: Any | None = None,
    meta: dict[str, Any] | None = None,
    trace_id: str | None = None,
) -> ErrorInfo:
    return ErrorFrame(
        error=ErrorInfo(code=code, message=message, context=context, trace_id=trace_id),
        meta=meta,
    )
