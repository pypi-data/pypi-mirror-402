"app/database/*"

from textwrap import dedent

APP_REPO_INIT_CONTENT_FOR_SQL = dedent("""
from .hero import HeroRepoDeps, HeroRepository

__all__ = ["HeroRepoDeps", "HeroRepository"]
""")

APP_REPO_HERO_CONTENT_FOR_SQL = dedent("""
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError as SAIntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import (
    DatabaseError,
    DuplicateKeyError,
    NotFoundError,
)
from app.database import SessionDeps
from app.models import Hero


class HeroRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_hero_by_id(self, hero_id) -> Hero:
        result = await self.session.execute(select(Hero).where(Hero.id == hero_id))
        hero = result.scalar_one_or_none()

        if not hero:
            raise NotFoundError("Hero not found")

        return hero

    async def create_hero(self, name: str) -> Hero:
        hero = Hero(name=name)
        self.session.add(hero)

        try:
            await self.session.commit()
            await self.session.refresh(hero)
            return hero

        except SAIntegrityError as e:
            await self.session.rollback()
            raise DuplicateKeyError("Hero with this name already exists") from e

        except Exception as e:
            await self.session.rollback()
            raise DatabaseError("Failed to create hero") from e

    async def update_hero(self, hero_id, name: str | None = None) -> Hero:
        hero = await self.get_hero_by_id(hero_id)

        if name is not None:
            hero.name = name

        try:
            await self.session.commit()
            await self.session.refresh(hero)
            return hero

        except SAIntegrityError as e:
            await self.session.rollback()
            raise DuplicateKeyError("Hero with this name already exists") from e

        except Exception as e:
            await self.session.rollback()
            raise DatabaseError("Failed to update hero") from e

    async def delete_hero(self, hero_id) -> Hero:
        hero = await self.get_hero_by_id(hero_id)

        try:
            await self.session.delete(hero)
            await self.session.commit()
            return hero

        except Exception as e:
            await self.session.rollback()
            raise DatabaseError("Failed to delete hero") from e


def get_hero_repo(
    session: SessionDeps,
):
    return HeroRepository(session)


HeroRepoDeps = Annotated[HeroRepository, Depends(get_hero_repo)]
""")
