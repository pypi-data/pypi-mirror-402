"""app/models/*"""

from textwrap import dedent

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
