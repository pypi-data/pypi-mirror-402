"""app/core/*"""

from textwrap import dedent

APP_CORE_INIT_CONTENT = dedent(
    """
from .config import settings
from .lifespan import lifespan

__all__ = [settings, lifespan]

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
