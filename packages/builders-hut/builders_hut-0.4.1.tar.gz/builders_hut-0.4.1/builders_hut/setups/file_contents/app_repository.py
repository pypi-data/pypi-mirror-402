"app/database/*"

from textwrap import dedent

APP_REPO_INIT_CONTENT_FOR_SQL = dedent("""
from .hero import HeroRepoDeps, HeroRepository

__all__ = ["HeroRepoDeps", "HeroRepository"]
""")

APP_REPO_HERO_CONTENT_FOR_SQL = dedent('''
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Hero
from app.database import SessionDeps
from typing import Annotated
from fastapi import Depends


class HeroRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_hero_by_id(self, hero_id):
        result = await self.session.execute(select(Hero).where(Hero.id == hero_id))
        return result.scalar_one_or_none()

    async def create_hero(self, name: str):
        hero = Hero(name=name)
        self.session.add(hero)
        await self.session.commit()
        await self.session.refresh(hero)
        return hero

    async def update_hero(self, hero_id, name: str | None = None):
        hero = await self.get_hero_by_id(hero_id)
        if not hero:
            return None

        if name is not None:
            hero.name = name

        await self.session.commit()
        await self.session.refresh(hero)
        return hero

    async def delete_hero(self, hero_id):
        hero = await self.get_hero_by_id(hero_id)
        if not hero:
            return None

        await self.session.delete(hero)
        await self.session.commit()
        return hero


def get_hero_repo(
    session: SessionDeps,
):
    return HeroRepository(session)


HeroRepoDeps = Annotated[HeroRepository, Depends(get_hero_repo)]
''')
