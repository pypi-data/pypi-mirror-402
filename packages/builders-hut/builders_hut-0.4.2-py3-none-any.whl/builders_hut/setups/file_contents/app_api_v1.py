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
from app.core import success_response
from app.services import HeroServiceDeps
from app.schemas.hero import CreateHeroSchema, HeroResponse, UpdateHeroSchema
from app.core.responses import (
    SUCCESS_201_RESPONSE,
    CONFLICT_RESPONSES,
    VALIDATION_ERROR_RESPONSES,
    SERVER_ERROR_RESPONSES,
    SUCCESS_200_RESPONSE,
    NOT_FOUND_RESPONSES,
    SUCCESS_204_RESPONSE,
)

route = APIRouter(prefix="/heroes", tags=["Heroes"])


@route.post(
    "/",
    summary="Create A Hero",
    description="Create a new hero with the given name.",
    status_code=status.HTTP_201_CREATED,
    response_model=HeroResponse,
    responses={
        **SUCCESS_201_RESPONSE,
        **CONFLICT_RESPONSES,
        **VALIDATION_ERROR_RESPONSES,
        **SERVER_ERROR_RESPONSES,
    },
)
async def create_hero(payload: CreateHeroSchema, service: HeroServiceDeps):
    hero = await service.create_hero(name=payload.name)
    return success_response(
        message="Hero created successfully",
        data=hero,
        status_code=status.HTTP_201_CREATED,
    )


@route.get(
    "/{hero_id}",
    summary="Get A Hero Details",
    description="Get a Hero By ID.",
    status_code=status.HTTP_200_OK,
    response_model=HeroResponse,
    responses={
        **SUCCESS_200_RESPONSE,
        **VALIDATION_ERROR_RESPONSES,
        **NOT_FOUND_RESPONSES,
        **SERVER_ERROR_RESPONSES,
    },
)
async def get_hero(hero_id: uuid, service: HeroServiceDeps):
    hero = await service.get_hero(hero_id)
    return success_response(
        message="Hero retrieved successfully",
        data=hero,
        status_code=status.HTTP_200_OK,
    )


@route.put(
    "/{hero_id}",
    summary="Update A Hero Details",
    description="Update hero name by hero ID",
    status_code=status.HTTP_200_OK,
    response_model=HeroResponse,
    responses={
        **SUCCESS_200_RESPONSE,
        **VALIDATION_ERROR_RESPONSES,
        **NOT_FOUND_RESPONSES,
        **CONFLICT_RESPONSES,
        **SERVER_ERROR_RESPONSES,
    },
)
async def update_hero(payload: UpdateHeroSchema, service: HeroServiceDeps):
    hero = await service.update_hero(hero_id=payload.id, name=payload.name)
    return success_response(
        message="Hero updated successfully",
        data=hero,
        status_code=status.HTTP_200_OK,
    )


@route.delete(
    "/{hero_id}",
    summary="Delete A Hero",
    description="Delete hero by hero ID",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    responses={
        **SUCCESS_204_RESPONSE,
        **VALIDATION_ERROR_RESPONSES,
        **NOT_FOUND_RESPONSES,
        **SERVER_ERROR_RESPONSES,
    },
)
async def delete_hero(hero_id: uuid, service: HeroServiceDeps):
    await service.delete_hero(hero_id)
    return
""")
