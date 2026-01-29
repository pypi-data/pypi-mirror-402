"app/database/*"

from textwrap import dedent

APP_DATABASE_SESSION_CONTENT_FOR_SQL = dedent('''
"""
Database Connections Management
"""

from typing import AsyncGenerator, Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)

from app.core import settings


""" database engine """
engine: AsyncEngine = create_async_engine(
    settings.db_url,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

""" databse session """
asyncsession = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """get the session as needed"""
    async with asyncsession() as session:
        yield session


""" session dependency to use when needed """
SessionDeps = Annotated[AsyncSession, Depends(get_session)]
''')
