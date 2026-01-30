"""app/models/*"""

from textwrap import dedent

APP_SCHEMA_COMMON_CONTENT = dedent(
    """
from typing import Generic, TypeVar, Optional, Any
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    success: bool
    message: str | None
    data: Optional[T] = None
    error_code: Optional[str] = None
    stack_trace: Optional[str] = None


class SuccessResponseSchema(BaseModel, Generic[T]):
    success: bool = True
    message: str
    data: Optional[T] = None


class ErrorResponseSchema(BaseModel):
    success: bool = False
    message: str
    data: Optional[Any] = None
    error_code: Optional[str] = None
"""
)

APP_SCHEMA_HERO_CONTENT = dedent(
    """
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from app.schemas.common import SuccessResponseSchema


# ---------- REQUEST SCHEMAS ----------


class CreateHeroSchema(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=100, description="The name of the hero."
    )


class UpdateHeroSchema(BaseModel):
    id: UUID = Field(..., description="The unique identifier of the hero.")
    name: str | None = Field(
        None, min_length=1, max_length=100, description="The new name of the hero."
    )


# ---------- RESPONSE SCHEMAS ----------
class HeroSchema(BaseModel):
    id: UUID = Field(..., description="The unique identifier of the hero.")
    name: str = Field(..., description="The name of the hero.")
    created_at: datetime = Field(..., description="The creation timestamp of the hero.")
    updated_at: datetime = Field(
        ..., description="The last update timestamp of the hero."
    )


class HeroResponse(SuccessResponseSchema):
    data: HeroSchema
"""
)
