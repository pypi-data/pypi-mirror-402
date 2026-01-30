"""app/models/*"""

from textwrap import dedent

APP_UTILS_INIT_CONTENT = dedent(
    """
from .common import success_response, error_response

__all__ = ["success_response", "error_response"]

"""
)

APP_UTILS_COMMON_CONTENT = dedent(
    """
from typing import Generic, TypeVar, Optional
from pydantic import BaseModel
from fastapi import status
from fastapi.responses import JSONResponse
from typing import Any

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: Optional[T] = None
    error_code: Optional[str] = None


def api_response(
    *,
    success: bool,
    message: str,
    data: Any = None,
    status_code: int = status.HTTP_200_OK,
    error_code: str | None = None,
) -> JSONResponse:
    payload = APIResponse(
        success=success,
        message=message,
        data=data,
        error_code=error_code,
    )

    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(exclude_none=True),
    )


def success_response(
    message: str = "Success",
    data: Any = None,
    status_code: int = status.HTTP_200_OK,
):
    return api_response(
        success=True,
        message=message,
        data=data,
        status_code=status_code,
    )


def error_response(
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    error_code: str | None = None,
    data: Any = None,
):
    return api_response(
        success=False,
        message=message,
        status_code=status_code,
        error_code=error_code,
        data=data,
    )
"""
)
