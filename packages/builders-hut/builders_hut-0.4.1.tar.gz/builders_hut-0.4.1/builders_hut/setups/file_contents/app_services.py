"""app/models/*"""

from textwrap import dedent

APP_SERVICE_INIT_CONTENT = dedent(
    """
from .hero import HeroServiceDeps

__all__ = ["HeroServiceDeps"]
"""
)

APP_SERVICE_HERO_CONTENT = dedent(
    """
from app.repositories import HeroRepository, HeroRepoDeps
from typing import Annotated
from fastapi import Depends


class HeroService:
    def __init__(self, repo: HeroRepository):
        self.repo = repo

    async def get_hero(self, hero_id):
        return await self.repo.get_hero_by_id(hero_id)

    async def create_hero(self, name: str):
        if not name or not name.strip():
            raise ValueError("Hero name cannot be empty")

        return await self.repo.create_hero(name=name.strip())

    async def update_hero(self, hero_id, name: str | None = None):
        if name is not None and not name.strip():
            raise ValueError("Hero name cannot be empty")

        hero = await self.repo.update_hero(hero_id, name=name)
        if not hero:
            raise LookupError("Hero not found")

        return hero

    async def delete_hero(self, hero_id):
        hero = await self.repo.delete_hero(hero_id)
        if not hero:
            raise LookupError("Hero not found")

        return hero


def get_hero_service(
    repo: HeroRepoDeps,
):
    return HeroService(repo)


HeroServiceDeps = Annotated[HeroService, Depends(get_hero_service)]
"""
)
