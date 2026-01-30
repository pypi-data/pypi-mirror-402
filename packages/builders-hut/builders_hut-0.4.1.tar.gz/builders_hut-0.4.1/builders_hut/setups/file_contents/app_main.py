"app/main.py"

from textwrap import dedent

APP_MAIN_CONTENT = dedent("""
from fastapi import FastAPI
from app.core import settings, lifespan
from app.api import common_router, v1_router


def create_app() -> FastAPI:
    '''
    Create a fastapi app
    '''
    app = FastAPI(
        docs_url=None,
        redoc_url=None,
        title=settings.TITLE,
        description=settings.DESCRIPTION,
        version=settings.VERSION,
        lifespan=lifespan,
    )

    app.include_router(common_router)
    app.include_router(v1_router)

    return app


app = create_app()
""")
