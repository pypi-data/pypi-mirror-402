from __future__ import annotations

from typing import Any, TypeVar

from .builders import build_ok, build_ok_paged, build_error

T = TypeVar("T")


def ok(data: T | None = None, *, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Build a successful JSON response.

    Returns a plain dict ready to be returned from an API handler.
    """
    frame = build_ok(data=data, meta=meta)
    payload = frame.model_dump(exclude_none=True)
    if "data" not in payload:
        payload["data"] = None
    return payload


def ok_paged(
    data: list[T],
    *,
    total: int,
    limit: int,
    offset: int,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build a paginated successful JSON response.
    """
    return build_ok_paged(
        data=data,
        total=total,
        limit=limit,
        offset=offset,
        meta=meta,
    ).model_dump(exclude_none=True)


def error(
    *,
    message: str,
    code: str | None = None,
    context: Any | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build an error JSON response.

    - Returns {"detail": "..."} for simple errors
    - Returns structured {"detail": {"error": {...}, "meta": {...}}} otherwise
    """
    return build_error(
        message=message,
        code=code,
        context=context,
        meta=meta,
    ).model_dump(exclude_none=True)
