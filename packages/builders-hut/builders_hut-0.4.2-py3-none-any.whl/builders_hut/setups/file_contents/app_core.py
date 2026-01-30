"""app/core/*"""

from textwrap import dedent

APP_CORE_INIT_CONTENT = dedent(
    """
from .config import settings
from .lifespan import lifespan
from .response_helper import success_response, error_response

__all__ = ["settings", "lifespan", "success_response", "error_response"]
"""
)

APP_CORE_CONFIG_CONTENT = dedent("""
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
from pydantic import Field
from functools import lru_cache
from typing import Literal

load_dotenv()


class Settings(BaseSettings):
    '''
    Settings for the application
    '''

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    TITLE: str = Field(
        description="The title of the application", validation_alias="TITLE"
    )

    DESCRIPTION: str = Field(
        description="The description of the application",
        validation_alias="DESCRIPTION",
    )

    VERSION: str = Field(
        description="The version of the application", validation_alias="VERSION"
    )

    DEBUG: bool = Field(
        description="Whether the application is in debug mode",
        validation_alias="DEBUG",
    )

    PORT: int = Field(
        description="The port to run the application on", validation_alias="PORT"
    )

    HOST: str = Field(
        description="The host to run the application on", validation_alias="HOST"
    )

    DB_USER: str = Field(..., description="Database user name", validation_alias="DB_USER")

    DB_PASS: str = Field(..., description="Database password", validation_alias="DB_PASS")

    DB_HOST: str = Field(..., description="Database Host", validation_alias="DB_HOST")

    DB_PORT: str = Field(..., description="Database port", validation_alias="DB_PORT")

    DB_NAME: str = Field(..., description="Database Name", validation_alias="DB_NAME")

    DB_TYPE: Literal["postgres", "mysql", "sqlite", "mongodb"] = Field(
        "postgres", description="Which database to use for the project", validation_alias="DB_TYPE"
    )

    @property
    def db_url(self) -> str:
        if self.DB_TYPE == "postgres":
            return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    '''
    Get the settings
    '''
    return Settings()


settings = get_settings()
""")

APP_CORE_LIFESPAN_CONTENT = dedent("""
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.database.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()
""")

APP_CORE_API_RESPONSE_HELPER_CONTENT = dedent(
    """
from fastapi import status
from fastapi.responses import JSONResponse
from typing import Any
from app.schemas.common import APIResponse


def api_response(
    *,
    success: bool,
    message: str | None,
    data: Any = None,
    status_code: int = status.HTTP_200_OK,
    error_code: str | None = None,
    stack_trace: str | None = None,
) -> JSONResponse:
    payload = APIResponse(
        success=success,
        message=message,
        data=data,
        error_code=error_code,
        stack_trace=stack_trace,
    )

    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(exclude_none=True),
    )


def success_response(
    message: str | None = None,
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
    stack_trace: str | None = None,
):
    return api_response(
        success=False,
        message=message,
        status_code=status_code,
        error_code=error_code,
        data=data,
        stack_trace=stack_trace,
    )
"""
)

APP_CORE_ERRORS_CONTENT = dedent('''
from typing import Any, Optional
from fastapi import status
import traceback


class AppError(Exception):
    status_code: int = status.HTTP_400_BAD_REQUEST
    message: str = "Application error"
    error_code: str = "APP_ERROR"
    data: Any = None
    stack_trace: Optional[str] = None

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        data: Any = None,
        error_code: Optional[str] = None,
        capture_trace: bool = True,
    ):
        if message:
            self.message = message
        if error_code:
            self.error_code = error_code
        self.data = data
        if capture_trace:
            self.stack_trace = traceback.format_exc()
        super().__init__(self.message)


"""Validation & Request errors (replaces 422)"""


class ValidationError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "VALIDATION_ERROR"
    message = "Invalid request data"


"""Authentication & Authorization"""


class UnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "UNAUTHORIZED"
    message = "Authentication required"


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "FORBIDDEN"
    message = "You do not have permission"


"""Resource errors"""


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "NOT_FOUND"
    message = "Resource not found"


"""Conflict / Integrity errors"""


class IntegrityError(AppError):
    status_code = status.HTTP_409_CONFLICT
    error_code = "INTEGRITY_ERROR"
    message = "Integrity constraint violated"


class DuplicateKeyError(IntegrityError):
    error_code = "DUPLICATE_KEY"
    message = "Duplicate key exists"


"""Mongo-specific"""


class MongoDuplicateKeyError(AppError):
    status_code = status.HTTP_409_CONFLICT
    error_code = "MONGO_DUPLICATE_KEY"
    message = "Duplicate document exists"


"""
Business rule errors
    Examples:
        - Insufficient balance
        - Invalid state transition
        - Feature disabled
"""


class BusinessRuleError(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "BUSINESS_RULE_VIOLATION"
    message = "Business rule violated"


"""External service errors"""


class ExternalServiceError(AppError):
    status_code = status.HTTP_502_BAD_GATEWAY
    error_code = "EXTERNAL_SERVICE_ERROR"
    message = "External service failed"


"""Rate limiting"""


class RateLimitExceededError(AppError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    error_code = "RATE_LIMIT_EXCEEDED"
    message = "Too many requests"


"""Infrastructure / system errors"""


class DatabaseError(AppError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "DATABASE_ERROR"
    message = "Database operation failed"


class CacheError(AppError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "CACHE_ERROR"
    message = "Cache operation failed"


"""Fallback"""


class InternalServerError(AppError):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "INTERNAL_SERVER_ERROR"
    message = "Something went wrong"
''')

APP_CORE_EXCEPTIONS_CONTENT = dedent(
    """
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .response_helper import error_response
from .errors import AppError
from .config import settings


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        stack_trace = exc.stack_trace if settings.DEBUG else None
        return error_response(
            message=exc.message,
            status_code=exc.status_code,
            error_code=exc.error_code,
            data=exc.data,
            stack_trace=stack_trace,
        )

    # Replace FastAPI 422
    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        return error_response(
            message=exc.errors()[0]["msg"],
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            error_code="VALIDATION_ERROR",
            data=exc.errors(),
        )

    # Catch raw HTTPExceptions
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return error_response(
            message=exc.detail,
            status_code=exc.status_code,
            error_code="HTTP_EXCEPTION",
        )

    # Absolute fallback
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return error_response(
            message="Internal server error",
            status_code=500,
            error_code="UNHANDLED_EXCEPTION",
        )
"""
)

APP_CORE_API_RESPONSES_CONTENT = dedent(
    """
from fastapi import status
from app.schemas.common import SuccessResponseSchema, ErrorResponseSchema


# -------- Error responses --------

VALIDATION_ERROR_RESPONSES = {
    status.HTTP_400_BAD_REQUEST: {
        "description": "Domain validation error",
        "model": ErrorResponseSchema,
    },
    status.HTTP_422_UNPROCESSABLE_ENTITY: {
        "description": "Request validation error",
        "model": ErrorResponseSchema,
    },
}

AUTH_ERROR_RESPONSES = {
    status.HTTP_401_UNAUTHORIZED: {
        "description": "Authentication required or failed",
        "model": ErrorResponseSchema,
    },
    status.HTTP_403_FORBIDDEN: {
        "description": "Permission denied",
        "model": ErrorResponseSchema,
    },
}

NOT_FOUND_RESPONSES = {
    status.HTTP_404_NOT_FOUND: {
        "description": "Resource not found",
        "model": ErrorResponseSchema,
    },
}

CONFLICT_RESPONSES = {
    status.HTTP_409_CONFLICT: {
        "description": "Resource already exists",
        "model": ErrorResponseSchema,
    },
}

SERVER_ERROR_RESPONSES = {
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "description": "Internal server error",
        "model": ErrorResponseSchema,
    },
}


# -------- Success responses --------

SUCCESS_200_RESPONSE = {
    status.HTTP_200_OK: {
        "description": "Successful operation",
        "model": SuccessResponseSchema,
    }
}

SUCCESS_201_RESPONSE = {
    status.HTTP_201_CREATED: {
        "description": "Resource created successfully",
        "model": SuccessResponseSchema,
    }
}

SUCCESS_202_RESPONSE = {
    status.HTTP_202_ACCEPTED: {
        "description": "Request accepted",
        "model": SuccessResponseSchema,
    }
}

SUCCESS_204_RESPONSE = {
    status.HTTP_204_NO_CONTENT: {
        "description": "No content",
    }
}
"""
)
