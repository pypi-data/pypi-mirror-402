"""app/api/*"""

from textwrap import dedent


APP_API_V1_INIT_CONTENT = dedent("""
from .hero import route as hero_router
from fastapi import APIRouter

router = APIRouter(prefix="/v1")


router.include_router(hero_router)

__all__ = ["router"]
""")


APP_API_V1_HERO_CONTENT = dedent("""
from fastapi import APIRouter, status
from uuid import UUID as uuid
from app.utils import success_response, error_response
from app.services import HeroServiceDeps

route = APIRouter(prefix="/heroes", tags=["Heroes"])


@route.post("/")
async def create_hero(name: str, service: HeroServiceDeps):
    try:
        hero = await service.create_hero(name)
        return success_response(
            message="Hero created successfully",
            data=hero.to_dict(),
            status_code=status.HTTP_201_CREATED,
        )
    except Exception as e:
        return error_response(
            message="Failed to create hero",
            data=str(e),
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="hero_creation_failed",
        )


@route.get("/{hero_id}")
async def get_hero(hero_id: uuid, service: HeroServiceDeps):
    try:
        hero = await service.get_hero(hero_id)
        if not hero:
            return error_response(
                message="Hero not found",
                data=None,
                status_code=status.HTTP_404_NOT_FOUND,
                error_code="hero_not_found",
            )
        return success_response(
            message="Hero retrieved successfully",
            data=hero.to_dict() if hero else None,
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve hero",
            data=str(e),
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="hero_retrieval_failed",
        )


@route.put("/{hero_id}")
async def update_hero(service: HeroServiceDeps, hero_id: uuid, name: str | None = None):
    try:
        hero = await service.update_hero(hero_id, name)
        return success_response(
            message="Hero updated successfully",
            data=hero.to_dict(),
            status_code=status.HTTP_200_OK,
        )
    except LookupError:
        return error_response(
            message="Hero not found",
            data=None,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="hero_not_found",
        )


@route.delete("/{hero_id}")
async def delete_hero(hero_id: uuid, service: HeroServiceDeps):
    try:
        await service.delete_hero(hero_id)
        return success_response(
            message="Hero deleted successfully",
            status_code=status.HTTP_200_OK,
        )
    except Exception as e:
        return error_response(
            message="Hero not found",
            data=str(e),
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="hero_not_found",
        )
""")
