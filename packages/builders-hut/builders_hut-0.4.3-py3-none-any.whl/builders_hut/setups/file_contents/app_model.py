"""app/models/*"""

from textwrap import dedent

APP_MODELS_INIT_CONTENT = dedent(
    """
from .hero import Hero

__all__ = ["Hero"]
"""
)

APP_MODELS_HERO_CONTENT = dedent(
    """
from .common import BaseModel
from sqlmodel import Field


class Hero(BaseModel, table=True):
    name: str = Field(index=True, default="", description="The name of the hero", unique=True)

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "created_at": self.created_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "updated_at": self.updated_at.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        }
"""
)

APP_MODELS_COMMON_CONTENT = dedent("""
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, DateTime
from datetime import datetime, timezone
import uuid


class BaseModel(SQLModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    created_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
        ),
        default_factory=lambda: datetime.now(timezone.utc),
    )

    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True),
            nullable=False,
        ),
        default_factory=lambda: datetime.now(timezone.utc),
    )
""")
