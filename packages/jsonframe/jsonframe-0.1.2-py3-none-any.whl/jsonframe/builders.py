from __future__ import annotations

from typing import Any, TypeVar

from .models import ErrorDetail, ErrorFrame, ErrorInfo, Frame, PageMeta

T = TypeVar("T")


def build_ok(data: T | None = None, *, meta: dict[str, Any] | None = None) -> Frame[T]:
    return Frame[T](data=data, meta=meta or None)

def build_ok_paged(
    data: list[T],
    *,
    total: int,
    limit: int,
    offset: int,
    meta: dict[str, Any] | None = None,
) -> Frame[list[T]]:
    page = PageMeta(total=total, limit=limit, offset=offset).model_dump(exclude_none=True)
    merged_meta = {**(meta or {}), "page": page}
    return build_ok(data, meta=merged_meta)

def build_error(
    *,
    message: str,
    code: str | None = None,
    context: Any | None = None,
    meta: dict[str, Any] | None = None,
) -> ErrorFrame:
    if code is None and context is None and meta is None:
        return ErrorFrame(detail=message)

    if code is None:
        raise ValueError("code is required for structured error frames")

    return ErrorFrame(
        detail=ErrorDetail(
            error=ErrorInfo(code=code, message=message, context=context),
            meta=meta or None,
        ),
    )
