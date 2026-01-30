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
from typing import Annotated

from fastapi import Depends

from app.core.errors import ValidationError
from app.repositories import HeroRepoDeps, HeroRepository


class HeroService:
    def __init__(self, repo: HeroRepository):
        self.repo = repo

    async def get_hero(self, hero_id):
        hero = await self.repo.get_hero_by_id(hero_id)
        return hero.to_dict()

    async def create_hero(self, name: str):
        if not name or not name.strip():
            raise ValidationError(
                message="Hero name cannot be empty",
                data={"field": "name"},
            )

        hero = await self.repo.create_hero(name=name.strip())
        return hero.to_dict()

    async def update_hero(self, hero_id, name: str | None = None):
        if name is not None and not name.strip():
            raise ValidationError(
                message="Hero name cannot be empty",
                data={"field": "name"},
            )

        hero = await self.repo.update_hero(hero_id, name=name.strip() if name else None)
        return hero.to_dict()

    async def delete_hero(self, hero_id):
        return await self.repo.delete_hero(hero_id)


def get_hero_service(
    repo: HeroRepoDeps,
):
    return HeroService(repo)


HeroServiceDeps = Annotated[HeroService, Depends(get_hero_service)]
"""
)
