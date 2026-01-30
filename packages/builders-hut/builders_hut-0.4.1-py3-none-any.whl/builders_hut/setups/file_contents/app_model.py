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
    name: str = Field(index=True, default="", description="The name of the hero")

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
        }
"""
)

APP_MODELS_COMMON_CONTENT = dedent("""
from sqlmodel import Field, SQLModel
from datetime import datetime, timezone
import uuid


class BaseModel(SQLModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
""")
