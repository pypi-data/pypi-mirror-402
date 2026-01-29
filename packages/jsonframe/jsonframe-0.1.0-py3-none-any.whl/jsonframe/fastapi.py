from __future__ import annotations

from typing import Any, TYPE_CHECKING

from .builders import error as build_error
from .models import ErrorInfo, Frame

if TYPE_CHECKING:
    # Optional dependency: allows type checking without requiring FastAPI installed at runtime
    from fastapi import HTTPException
    from fastapi.responses import JSONResponse



def json_frame(
    frame: Frame[Any],
    *,
    status_code: int = 200,
    headers: dict[str, str] | None = None,
) -> "JSONResponse":
    """
    Returns a FastAPI JSONResponse with consistent framing and status_code control.

    Note: FastAPI is imported lazily so jsonframe can be used without FastAPI installed.
    """
    from fastapi.responses import JSONResponse  # local import: optional dependency

    return JSONResponse(
        status_code=status_code,
        content=frame.model_dump(exclude_none=True),
        headers=headers,
    )


def http_error(
    status_code: int,
    *,
    code: str,
    message: str,
    context: Any | None = None,
    meta: dict[str, Any] | None = None,
    trace_id: str | None = None,
) -> "HTTPException":
    """
    Raises a FastAPI HTTPException where `detail` is a flat error object.

    FastAPI will return: {"detail": <your ErrorInfo dict>}.
    """
    from fastapi import HTTPException  # local import: optional dependency

    payload: ErrorInfo = build_error(
        code=code,
        message=message,
        details=context,
        meta=meta,
        trace_id=trace_id,
    )
    return HTTPException(
        status_code=status_code,
        detail=payload.model_dump(exclude_none=True),
    )
