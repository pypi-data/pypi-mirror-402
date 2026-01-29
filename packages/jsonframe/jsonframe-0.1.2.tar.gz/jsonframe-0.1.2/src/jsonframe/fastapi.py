from __future__ import annotations

from typing import Any, TYPE_CHECKING

# Re-export helpers for FastAPI usage
from .helpers import ok, ok_paged
from .builders import build_error
from .models import ErrorDetail

if TYPE_CHECKING:
    # Optional dependency: allows type checking without requiring FastAPI installed at runtime
    from fastapi import HTTPException

__all__ = ["ok", "ok_paged", "http_error"]


def http_error(
    status_code: int,
    *,
    message: str,
    code: str | None = None,
    context: Any | None = None,
    meta: dict[str, Any] | None = None,
) -> "HTTPException":
    """
    Raises a FastAPI HTTPException where `detail` is either a string or structured error payload.

    FastAPI will return: {"detail": <string or error payload>}.
    """
    from fastapi import HTTPException  # local import: optional dependency

    payload = build_error(
        code=code,
        message=message,
        context=context,
        meta=meta,
    )
    detail = payload.detail
    if isinstance(detail, ErrorDetail):
        detail = detail.model_dump(exclude_none=True)
    return HTTPException(
        status_code=status_code,
        detail=detail,
    )
